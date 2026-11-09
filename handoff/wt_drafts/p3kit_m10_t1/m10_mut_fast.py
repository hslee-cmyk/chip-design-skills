"""measure only: fast survivor screen for M10 targeted mutants -- each mutant run against the prototype M10 test only
(cheap tests first, then the two real-run tests), same mutant generator and scope as gate V3 (mutate_changed.mutants + _Scope).
    python -B mut_fast.py <clone root at head> <gates dir> <base rev> <head rev> <out.jsonl>"""
import ast
import json
import os
import subprocess
import sys
import time

root, GC, base, head, out = sys.argv[1:6]
sys.path.insert(0, GC)
import mutate_changed as mc  # noqa: E402
import reachability as rch  # noqa: E402

T = "skills/analog-gmid-design/assets/tests/integration/test_m10_entry_proto.py"
env = dict(os.environ, PYTHONPATH=GC, PYTHONDONTWRITEBYTECODE="1")
hf = rch.read_tree(root, head, rch.GRAPH_PREFIXES)
bf = rch.read_tree(root, base, rch.GRAPH_PREFIXES)


def pt(k):
    cmd = [sys.executable, "-P", "-m", "pytest", "-c", GC + "/pytest_gate.ini", "--rootdir=" + root, "--confcutdir=" + root,
           "-x", "-q", "-p", "no:cacheprovider", "--gmid-phase=3", os.path.join(root, T), "-k", k]
    return subprocess.run(cmd, cwd=root, capture_output=True, env=env, timeout=900).returncode


open(out, "w").close()
for p in ("skills/analog-gmid-design/assets/gmid_design_pipeline.py", "workspaces/run_harness.py"):
    hs, bs = hf[p], bf.get(p)
    bdefs = dict(rch.iter_defs(ast.parse(bs))) if bs else {}
    fpath = os.path.join(root, *p.split("/"))
    for q, fn in mc.changed_defs(bs, hs):
        scope = mc._Scope(bdefs[q], fn) if q in bdefs else None
        for opname, npath, mfn in mc.mutants(fn, hs):
            if scope is not None and not scope.targets(opname, npath):
                continue
            mid = "%s:%s:%s:%s" % (rch.module_name(p), q, opname, npath)
            t0 = time.time()
            open(fpath, "w", encoding="utf-8", newline="\n").write(mc._replace_def(hs, fn, mfn))
            try:
                rc1 = pt("not real_run")
                rc2 = pt("real_run") if rc1 == 0 else None
            finally:
                open(fpath, "w", encoding="utf-8", newline="\n").write(hs)
            rec = {"id": mid, "fast_rc": rc1, "real_rc": rc2, "survived": rc1 == 0 and rc2 == 0, "s": round(time.time() - t0, 1)}
            with open(out, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
print("done")
