"""E-INST: harness run_harness.run(<회로>)를 격리 복제본에서 돌려 instance.json 해시와
run_matching_safety_with_finger_growth 호출마다의 relaxed_pairs interdig_ok(반환을 읽기만 하는 감싸기)를 적는다.
usage: python -P einst.py <clone_root> <circuit_key> <out.json>"""
import hashlib, io, json, os, sys, contextlib

root, key, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
ws = os.path.join(root, "workspaces")
sys.path.insert(0, ws)
import run_harness as rh  # noqa: E402
import sizing_recipe as sr  # noqa: E402

assert os.path.normcase(sr.__file__).startswith(os.path.normcase(os.path.abspath(root))), sr.__file__
calls = []
_orig = sr.run_matching_safety_with_finger_growth


def _wrapped(*a, **k):
    res = _orig(*a, **k)
    ent = []
    for e in res["relaxed_pairs"]:
        x, y = e["pair"]
        c3b = [(c.name, bool(c.ok)) for c in res["audit"].checks if c.name.startswith("3b.") and f"[{x}/{y}]" in c.name]
        ent.append({"pair": list(e["pair"]), "interdig_ok": e["interdig_ok"], "audit_3b": c3b,
                    "consistent": len(c3b) == 1 and e["interdig_ok"] is c3b[0][1]})
    calls.append({"unresolved_reason": res["unresolved_reason"], "audit_ok": bool(res["audit"].ok),
                  "rows": {r: [[t.name, t.n_fingers, t.stack_id] for t in v] for r, v in res["rows"].items()},
                  "relaxed_pairs": ent})
    return res


sr.run_matching_safety_with_finger_growth = _wrapped
cfg = rh.SPECS[key]
stem = cfg["topology_file"].removesuffix(".topology.json")
inst = os.path.join(ws, cfg["report_dir"], f"{stem}.instance.json")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rh.run(key)
log = buf.getvalue()
h = hashlib.sha256(open(inst, "rb").read()).hexdigest() if os.path.exists(inst) else None
out = {"root": root, "circuit": key, "instance_json": inst, "instance_sha256": h,
       "instance_has_interdig_ok": (b"interdig_ok" in open(inst, "rb").read()) if h else None,
       "calls": calls, "harness_fail_line": [l for l in log.splitlines() if l.startswith("[FAIL]")],
       "log_tail": log.splitlines()[-8:]}
json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(key, "sha256", h, "calls", len(calls),
      [[(e["pair"], e["interdig_ok"], e["consistent"]) for e in c["relaxed_pairs"]] for c in calls],
      out["harness_fail_line"])
