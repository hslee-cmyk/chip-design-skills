"""FU spec card '작성 전 실측' 8(V3 규모) -- 현재 gate 도구 + N2w 시제품으로 FU head의 V3 대상을 잰다.

사용: python -B fu_v3_n2w.py <gate tools/gates 사본> <base 트리> <head 트리> <out.json>
  * 현재 도구: mutate_changed.changed_defs(base 소스, head 소스) -- 엔진 파일마다(reachability._is_source) 바뀐 def.
  * N2w 시제품: _drafts/b26pre_scripts/v3_scope_widen.py(범위 정책 card 20260930-v3-changed-stmt-scope 구현 기준 분류기, 미병합)의
    classify_w + DEFS["N2w"] -- 바뀐 def마다 변이 행을 만들고 N2w 대상 수를 센다. 그 분류기의 sim_head 의존(C:/g87 경로·파일 쓰기)은
    여기서 mc·rch만 가진 빈 모듈로 바꿔 끊는다(분류기 함수만 쓰고 main·measure는 돌리지 않는다).
  * 대조(판정기가 공허하지 않은지): head DR의 `_kv_table` 반환 주석만 바꾼 합성 head에서 같은 계산 -- 바뀐 def 1이 나와야 한다.
결과는 <out.json>에 쓴다.
"""
import ast
import json
import os
import sys
import types

GATES, BASE, HEAD, OUT = sys.argv[1:5]
sys.path.insert(0, GATES)
import mutate_changed as mc  # noqa: E402
import reachability as rch   # noqa: E402

stub = types.ModuleType("sim_head")
stub.mc, stub.rch = mc, rch
sys.modules["sim_head"] = stub
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26pre_scripts")
import v3_scope_widen as W   # noqa: E402
V = W.V


def read(root):
    files = {}
    for pre in rch.GRAPH_PREFIXES:
        for dp, _dn, fns in os.walk(os.path.join(root, pre)):
            for fn in fns:
                if fn.endswith(".py"):
                    full = os.path.join(dp, fn)
                    rel = os.path.relpath(full, root).replace("\\", "/")
                    with open(full, encoding="utf-8", errors="replace") as fh:
                        files[rel] = fh.read()
    return files


def measure(bf, hf):
    res = {"changed_files": [], "defs": [], "mutants_all": 0, "n2w": 0}
    for path in sorted(p for p in hf if hf[p] != bf.get(p) and rch._is_source(p)):
        res["changed_files"].append(path)
        bsrc = bf.get(path)
        bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
        for q, hfn in mc.changed_defs(bsrc, hf[path]):
            if q in bdefs:
                rows, _info = W.classify_w(bdefs[q], hfn, hf[path])
            else:
                rows = [dict(op=o, path=p) for o, p, _ in mc.mutants(hfn, hf[path])]
            n = sum(1 for t in rows if "T1" in t and V.DEFS["N2w"](t)) if q in bdefs else len(rows)
            res["defs"].append({"path": path, "def": q, "mutants": len(rows), "n2w": n})
            res["mutants_all"] += len(rows)
            res["n2w"] += n
    return res


bf, hf = read(BASE), read(HEAD)
out = {"gates": GATES, "real": measure(bf, hf)}
DR = "skills/analog-gmid-design/assets/design_report.py"
ctl = dict(hf)
src = ctl[DR]
i = src.index("def _kv_table(")
j = src.index("->", i)
k = src.index(":", j)
ctl[DR] = src[:j] + "-> 'object'" + src[k:]
out["control_annotation_edit"] = measure(bf, ctl)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
print(json.dumps({k: {"files": v["changed_files"], "defs": len(v["defs"]), "mutants": v["mutants_all"], "n2w": v["n2w"]}
                  for k, v in out.items() if isinstance(v, dict)}, ensure_ascii=False))
