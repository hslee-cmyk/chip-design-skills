# -*- coding: utf-8 -*-
"""제약 임계값을 **달성 가능 실측**에서 유도해 사이드카(`<topology>.derived.json`)에 남긴다.

사용자 지시(2026-09-10): *"1번으로 진행해. 그리고, 이것도 계산으로 유도하도록 함수로 만들고
재활용 가능하게 만들어. 마찬가지로 최초에 한번 계산해서 caching해서 쓰면 되잖아?"*

## 왜 스크립트가 따로 있나

유도는 **전체 SLSQP 탐색을 여러 번** 돌리는 일이라 수 분 걸린다. evaluator를 만들 때마다
그걸 돌리면 self-test/프로브가 못 쓴다. 그래서 여기서 **한 번 계산해 파일에 남기고**,
`resolve_constraint_references()`는 이후 **읽기만** 한다. 파일에는 `spec_fingerprint()`가
같이 들어가므로 격자/bounds를 바꾸면 그 유도는 자동으로 "안 맞는 것"이 된다(조용히 옛 값을
쓰지 않는다 -- 그때는 엔진이 이 스크립트를 다시 돌리라고 말한다).

## 무엇을 재나

`sizing_roles.constraints`에서 `value_from_achievable`를 쓰는 제약을 **선언에서 찾아**
그 metric마다 `achievable_metric_bound()`를 돌린다 -- 회로 이름도 metric 이름도 이 스크립트에
박지 않는다.

실행: assets 디렉터리에서
    python tests/derive_achievable_bounds.py                 # SPECS 전 회로
    python tests/derive_achievable_bounds.py <circuit_key>   # 하나만
"""
import sys
import os
import json
import time

ASSETS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools -> tests -> assets
sys.path.insert(0, ASSETS)
sys.path.insert(0, os.path.join(ASSETS, "..", "..", "..", "workspaces"))
import sizing_recipe as sr
import run_harness as H

_RESULT = os.path.splitext(os.path.abspath(__file__))[0] + ".result.txt"
_first = [True]


def emit(*p):
    line = " ".join(str(x) for x in p)
    print(line, flush=True)
    with open(_RESULT, "w" if _first[0] else "a", encoding="utf-8") as f:
        f.write(line + "\n")
    _first[0] = False


keys = sys.argv[1:] or sorted(H.SPECS)
emit("=" * 96)
emit("달성 가능 실측으로 제약 임계값 유도 (사이드카 갱신)")
emit("=" * 96)

for key in keys:
    if key not in H.SPECS:
        emit(f"[{key}] 등록되지 않은 circuit_key -- 건너뜀({sorted(H.SPECS)})")
        continue
    topo = os.path.join(ASSETS, "library", H.SPECS[key]["topology_file"])
    spec = H.canonical_spec(key)
    with open(topo, encoding="utf-8") as fh:
        cons = (json.load(fh).get("sizing_roles") or {}).get("constraints") or []
    targets = [(c["metric"], (c["value_from_achievable"] or {}).get("sense", "min"))
               for c in cons if "value_from_achievable" in c]
    emit("")
    emit("-" * 96)
    emit(f"[{key}] value_from_achievable 제약 {len(targets)}개: {targets or '없음'}")
    if not targets:
        continue
    fp = sr.spec_fingerprint(spec)
    book = sr.load_derived_bounds(topo)
    book.setdefault(fp, {})
    with open(topo, encoding="utf-8") as fh:
        topo_doc = json.load(fh)
    for metric, sense in targets:
        t0 = time.time()
        try:
            # 탐색 파라미터는 이 회로가 이미 선언한 것을 그대로 쓴다(임의로 줄이지 않는다 --
            # n_starts를 1로 깎았더니 파일럿이 probe 전부 실패했다, 2026-09-10 실측).
            r = sr.achievable_metric_bound(
                topo, spec, metric, sense=sense,
                slsqp_kwargs=H.SPECS[key].get("slsqp_kwargs"))
        except Exception as e:
            emit(f"  ★ {metric}({sense}) 유도 실패: {type(e).__name__}: {str(e)[:200]}")
            continue
        r["derived_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        r["elapsed_s"] = round(time.time() - t0, 1)
        book[fp][metric] = r
        emit(f"  {metric}({sense}): probe별 {[round(v, 4) for v in r['per_probe']]} "
             f"-> best={r['best']:.4f}, **conservative={r['conservative']:.4f}** "
             f"({r['n_ok']}/{len(r['per_probe']) + len(r['notes'])} 성공, {r['elapsed_s']}s)")
        for n in r["notes"]:
            emit(f"      실패 기록: {n}")
    # ★ 유도 결과를 **선언 자신에** 적어 넣는다 -- 손으로 적는 게 아니라 여기서 생성한다.
    #   엔진은 평소처럼 `value`만 읽고(모든 픽스처가 그대로 동작), `_derived`가 언제 어떤
    #   조건에서 나온 값인지 들고 있어 지문이 어긋나면 엔진이 기록으로 알린다.
    wrote = []
    for c in topo_doc["sizing_roles"]["constraints"]:
        r = book[fp].get(c.get("metric"))
        if "value_from_achievable" not in c or not r:
            continue
        c["value"] = round(float(r["conservative"]), 6)
        c["_derived"] = {"by": "achievable_metric_bound", "sense": r["sense"],
                         "spec_fingerprint": fp, "per_probe": r["per_probe"],
                         "n_ok": r["n_ok"], "constraints_dropped": r.get("constraints_dropped"),
                         "derived_at": r["derived_at"], "elapsed_s": r["elapsed_s"],
                         "notes": r.get("notes")}
        wrote.append((c["metric"], c["value"]))
    if wrote:
        with open(topo, "w", encoding="utf-8") as fh:
            json.dump(topo_doc, fh, ensure_ascii=False, indent=2)
            fh.write(chr(10))
        emit(f"  ★ topology.json 선언에 기록: {wrote}")
    path = sr.derived_bounds_path(topo)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(book, fh, ensure_ascii=False, indent=2)
    emit(f"  사이드카 저장: {path}  (지문 {fp})")

emit("")
emit("=" * 96)
