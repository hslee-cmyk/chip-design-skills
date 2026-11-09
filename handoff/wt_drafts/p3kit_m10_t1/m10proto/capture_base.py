"""measure-only: capture base (M9-merge) harness behaviour as golden for the M10 prototype test.
    python -B -P capture_base.py <root> <out golden.json> [real circuits comma list]"""
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import time

root, out = sys.argv[1:3]
reals = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] else []
sys.path.insert(0, os.path.join(root, "workspaces"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_harness as H  # noqa: E402
import _m10_scen as SC  # noqa: E402

gold = {"scenarios": {}, "real": {}}


def canon(p):
    return hashlib.sha256(json.dumps(json.load(open(p, encoding="utf-8")), sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def with_ws(fn):
    d = tempfile.mkdtemp(prefix="m10cap-")
    old = H.WORKSPACES_DIR
    H.WORKSPACES_DIR = d
    try:
        for c in H.SPECS.values():
            os.makedirs(os.path.join(d, c["report_dir"]), exist_ok=True)
        return fn(d)
    finally:
        H.WORKSPACES_DIR = old


for name in SC.SCEN:
    def go(d, name=name):
        od = os.path.join(d, H.SPECS["folded_cascode"]["report_dir"])
        return SC.run_scenario(H, name, lambda: H.run("folded_cascode"), od, H._REPO_ROOT)
    gold["scenarios"][name] = with_ws(go)
for c in reals:
    def go(d, c=c):
        cfg = H.SPECS[c]
        od = os.path.join(d, cfg["report_dir"])
        buf = io.StringIO()
        t = time.time()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            H.run(c)
        stem = cfg["topology_file"].removesuffix(".topology.json")
        ip, rp = os.path.join(od, stem + ".instance.json"), os.path.join(od, stem + ".report.html")
        return {"stdout": SC._s(buf.getvalue(), od, H._REPO_ROOT), "seconds": round(time.time() - t, 1),
                "instance_canon_sha256": canon(ip) if os.path.exists(ip) else None,
                "report_sha256": hashlib.sha256(open(rp, "rb").read()).hexdigest() if os.path.exists(rp) else None}
    gold["real"][c] = with_ws(go)
json.dump(gold, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"scen": len(gold["scenarios"]), "real": {k: {kk: v[kk] for kk in ("seconds", "instance_canon_sha256", "report_sha256")}
                                                           for k, v in gold["real"].items()}}))
