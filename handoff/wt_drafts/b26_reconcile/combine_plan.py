"""시나리오 A·B 결과 집계 + v4 통합 표(consolidated) 출력.
출력: _drafts/b26_reconcile/out/plan_summary.txt, out/survivor_table.md(통합 생존 표)
"""
import json, os
from collections import Counter

R = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_reconcile/"
G = "C:/g103/out/"
GROUPS = ("con", "pre", "trace", "bf")


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")] if os.path.exists(p) else []


def line_of(sc, mid):
    return None


out = open(R + "out/plan_summary.txt", "w", encoding="utf-8")
for sc in ("A", "B"):
    pr = {r["id"]: r for r in jl(G + "plan_%s_proto.jsonl" % sc)}
    ex = {r["id"]: r for r in jl(G + "plan_%s_existing.jsonl" % sc)}
    tg = [t for t in json.load(open(G + "targets_plan%s.json" % sc, encoding="utf-8")) if t["N2w"]]
    unm = jl(G + "plan_%s_unmapped.json" % sc) if False else json.load(open(G + "plan_%s_unmapped.json" % sc, encoding="utf-8"))
    union_surv = [i for i, r in pr.items() if all(r[g] == "survived" for g in GROUPS)]
    rem = [i for i in union_surv if ex.get(i, {}).get("result") != "killed"]
    out.write("== scenario %s: N2w targets %d, mapped %d, unmapped(new stmt) %d\n" % (sc, len(tg), len(pr), len(unm)))
    out.write("   killed by group: %s\n" % {g: sum(r[g] == "killed" for r in pr.values()) for g in GROUPS})
    out.write("   only-killer counts: %s\n" % Counter(tuple(g for g in GROUPS if r[g] == "killed") for r in pr.values()
                                                       if sum(r[x] == "killed" for x in GROUPS) == 1))
    out.write("   union survivors %d, existing measured %d, existing killed %d -> remaining %d\n" % (
        len(union_surv), len(ex), sum(1 for r in ex.values() if r["result"] == "killed"), len(rem)))
    for i in rem:
        out.write("     REMAIN %s\n" % i)
    for i in union_surv:
        if i not in rem:
            out.write("     union-survivor killed by existing: %s\n" % i)
out.close()
print(open(R + "out/plan_summary.txt", encoding="utf-8").read())
