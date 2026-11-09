"""B37a 모의 head의 V3 대상(지금 규칙 = def 전체 / N2 = 승인된 A1-b 정의)을 센다.
_drafts/v3_scripts/v3_scope_classify.py의 classify()(범위 정책 card 계약 1 구현)를 그대로 import해서 쓴다
(그 모듈이 기대하는 sim_head를 sys.modules에 대역으로 넣는다 -- mc·rch만 쓴다).
도구 함수(mutate_changed.changed_defs·mutants·inventory, reachability.build_graph·GRAPH_PREFIXES)만 읽기 전용 import.
사용: python -B v3_b37a.py <base 사본> <head 사본> <out.txt>
"""
import ast, os, sys, types, json

BASE, HEAD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, BASE + "/tools/gates")
import mutate_changed as mc  # noqa: E402
import reachability as rch  # noqa: E402
assert os.path.abspath(mc.__file__).replace("\\", "/").startswith(os.path.abspath(BASE).replace("\\", "/"))
fake = types.ModuleType("sim_head")
fake.mc, fake.rch = mc, rch
sys.modules["sim_head"] = fake
sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3_scripts")
import v3_scope_classify as V  # noqa: E402

fh = open(OUT, "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    fh.write(s + "\n")


def read(root):
    files = {}
    for pre in rch.GRAPH_PREFIXES:
        for dp, _dn, fns in os.walk(os.path.join(root, pre)):
            for fn in fns:
                if fn.endswith(".py"):
                    full = os.path.join(dp, fn)
                    rel = os.path.relpath(full, root).replace("\\", "/")
                    with open(full, encoding="utf-8", errors="replace") as f:
                        files[rel] = f.read()
    return files


bf, hf = read(BASE), read(HEAD)
nodes, edges = rch.build_graph(hf)
tests = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
         and __import__("re").search(r"::(Test[^.]*\.)?test[^.]*$", n)]
tot_all = tot_n2 = 0
summary = []
for path in sorted(p for p in hf if hf[p] != bf.get(p) and rch._is_source(p)):
    bsrc = bf.get(path)
    bdefs = dict(rch.iter_defs(ast.parse(bsrc))) if bsrc else {}
    for q, hfn in mc.changed_defs(bsrc, hf[path]):
        inv = mc.inventory(edges, "%s::%s" % (path, q), tests)
        if q in bdefs:
            rows, info = V.classify(bdefs[q], hfn, hf[path])
            sel = [t for t in rows if V.DEFS["N2b"](t)]
        else:
            rows = [dict(op=o, path=p) for o, p, _ in mc.mutants(hfn, hf[path])]
            sel, info = rows, {"new": "newdef"}
        tot_all += len(rows)
        tot_n2 += len(sel)
        log("== %s::%s  all=%d  N2=%d  inv=%d  info=%s" % (path.split("/")[-1], q, len(rows), len(sel), len(inv), json.dumps(info, ensure_ascii=False)))
        for t in sel:
            cats = [k for k in ("T1", "T2", "T3o", "T3name", "T4n", "T5n", "T6") if t.get(k)]
            log("     %-20s %-40s %s" % (t["op"], t["path"], ",".join(cats)))
        summary.append((path.split("/")[-1] + "::" + q, len(rows), len(sel), len(inv)))
log("TOTAL all=%d N2=%d" % (tot_all, tot_n2))
for s in summary:
    log("  %-60s all=%-4d N2=%-3d inv=%d" % s)
fh.close()
