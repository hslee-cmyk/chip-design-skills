"""measure only: run fixed c3.py (and the pre-n1 c3) on every chain card's normal merged head.
    python -B c3all.py <scratch root> <old c3 path> [card,...]"""
import json
import subprocess
import sys

SCR = sys.argv[1].rstrip("/")
OLD = sys.argv[2]
WANT = sys.argv[3].split(",") if len(sys.argv) > 3 else None
PY = "C:/Python314/python.exe"
GC = SCR + "/cache/tools/gates"
out = open(SCR + "/out/c3all.jsonl", "a", encoding="utf-8")
for l in open(SCR + "/out/chain.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if WANT and r["card"] not in WANT:
        continue
    pj = "%s/out/%s/plan_base.json" % (SCR, r["card"])
    res = {"card": r["card"], "base": r["base"], "head": r["head"]}
    for tag, c3 in (("new", SCR + "/kit/c3.py"), ("old", OLD)):
        p = subprocess.run([PY, "-B", c3, SCR + "/r", r["base"], r["head"], r["card"], pj, GC], capture_output=True, text=True, encoding="utf-8")
        try:
            j = json.loads(p.stdout.strip().splitlines()[-1])
            res[tag] = {"a": j["a_corrected"], "c": j["c_future_first"], "b": {f: (v["kind"], v["match"], v["first_diff"]) for f, v in j["b"].items()}}
        except Exception:
            res[tag] = {"ERROR": p.stderr[-400:]}
    out.write(json.dumps(res, ensure_ascii=False) + "\n")
    out.flush()
    print(json.dumps(res, ensure_ascii=False), flush=True)
