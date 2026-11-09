"""Sandbox only: robustness sweep of (i)+(ii) over seed windows. usage: python sweep.py <det_run.py> <gates> <mp.py> <work> <out>"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("dr", sys.argv[1]); dr = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0]] + sys.argv[2:]; spec.loader.exec_module(dr)
dr.GATES, dr.MP, dr.WORK, dr.OUT = sys.argv[1:5]
def i_ii(repo, c0, exp, v, seeds):
    outs = [dr.run(v, s, ["plan", "--root", repo, "--rev", c0] + dr.ARGS) for s in seeds]
    if len({o[1] for o in outs}) != 1: return "FAIL(i)"
    o = json.loads(outs[0][1])
    for k in ("upward", "cycles", "unassigned", "conflicts", "reg_mismatch"):
        L = o.get(k, [])
        if [dr.ek(x) for x in L] != sorted(dr.ek(x) for x in L): return "FAIL(ii)"
    return "PASS"
with open(dr.OUT, "w", encoding="utf-8") as fh:
    for n, ncyc, wins in ((2, 1, [list(range(a, a + 2)) for a in range(0, 16, 2)]),
                          (4, 2, [list(range(a, a + 8)) for a in range(0, 32, 8)])):
        repo = "%s/sw_n%d" % (dr.WORK, n)
        commits, exp = dr.build(repo, n, ncyc)
        for v in ("leak_unassigned", "leak_upward", "content", "sorted"):
            rs = [i_ii(repo, commits["C0"], exp, v, w) for w in wins]
            line = {"n": n, "ncyc": ncyc, "variant": v, "windows": [[w[0], w[-1]] for w in wins], "results": rs,
                    "missed": sum(r == "PASS" for r in rs)}
            fh.write(json.dumps(line) + "\n"); fh.flush()
            print(line)
