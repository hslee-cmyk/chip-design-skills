"""통합 표 생성: N2w 대상(v4 head) 264(대응 있음) x {기존 test, B26-1 계약 근사, B26pre 시제품}.
기존 test 열: 이번 C:/g103 실행(out/existing.jsonl)이 있으면 그것, 없으면 이전 측정의 '죽음'(엔진 소스 동일, test 집합은 늘기만 함)을 근거로 씀.
  이전 측정: b26_scripts/out/kill_v4_N2d.jsonl(by=inventory 행만 -- 2d58fd8 base), b26pre_scripts/out/kill_v4_N2d.jsonl(a796468 base, 기존 test만).
사용: python -B combine.py ids   -> out/existing_ids.json(기존 test 재실행 대상 = 이전 '죽음' 근거가 없는 변이)
      python -B combine.py table -> b26_reconcile/out/consolidated.md, consolidated.json
"""
import json, os, sys

D = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/"
R = D + "b26_reconcile/"
G = "C:/g103/out/"


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []


def prior_existing():
    pe = {}
    for r in jl(D + "b26_scripts/out/kill_v4_N2d.jsonl"):
        if r["result"] == "killed" and r.get("by") == "inventory":
            pe[r["id"]] = "killed(prior-b26)"
        elif r["result"] == "survived":
            pe.setdefault(r["id"], "survived(prior-b26)")
    for r in jl(D + "b26pre_scripts/out/kill_v4_N2d.jsonl"):
        if r["result"] == "killed":
            pe[r["id"]] = "killed(prior-b26pre)"
        else:
            pe.setdefault(r["id"], "survived(prior-b26pre)")
    return pe


def main(what):
    proto = {r["id"]: r for r in jl(G + "proto.jsonl")}
    tg = {t["id"]: t for t in json.load(open(G + "targets_v4.json", encoding="utf-8")) if t["N2w"]}
    pe = prior_existing()
    if what == "ids":
        ids = [i for i in proto if not pe.get(i, "").startswith("killed")]
        json.dump(ids, open(G + "existing_ids.json", "w", encoding="utf-8"), indent=0)
        print("rerun existing", len(ids), "of", len(proto))
        return
    ex = {r["id"]: r for r in jl(G + "existing.jsonl")}
    rows = []
    for i, p in proto.items():
        e = ex.get(i)
        est = ("killed" if e["result"] == "killed" else "survived") + "(g103)" if e else pe.get(i, "unknown")
        t = tg[i]
        rows.append(dict(id=i, def_=t["def_"], file=t["file"].split("/")[-1], N2b=t["N2b"], existing=est,
                         con=p["con"], con_failed=p["con_failed"], pre=p["pre"], pre_failed=p["pre_failed"], unexec=t.get("unexec")))
    os.makedirs(R + "out", exist_ok=True)
    json.dump(rows, open(R + "out/consolidated.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    from collections import Counter
    c = Counter((r["existing"].split("(")[0], r["con"], r["pre"]) for r in rows)
    print(c)
    surv_ex = [r for r in rows if not r["existing"].startswith("killed")]
    print("survive existing", len(surv_ex))
    rem = [r for r in surv_ex if r["con"] == "survived" and r["pre"] == "survived"]
    print("remaining after union", len(rem))
    for r in rem:
        print("  ", r["id"])


if __name__ == "__main__":
    main(sys.argv[1])
