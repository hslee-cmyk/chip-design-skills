"""Base-side checks without LUT or test execution: erfc spec load, and collection of the four failing files."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:/Users/HSLEE/AppData/Local/Temp/la1s_o181_audit/iso_master")
SK = ROOT / "skills/analog-gmid-design"
sys.path.insert(0, str(SK))
from gmid_engine.authoring import load_sizing_spec, load_topology

LIB = SK / "assets/library"
topo = load_topology(str(LIB / "erfc_ota.topology.json"))
print("erfc connectivity_fp", topo.connectivity_fp)
try:
    load_sizing_spec(str(LIB / "erfc_ota.sizing_spec.json"), topo)
    print("erfc spec load ok")
except Exception as exc:
    rec = getattr(exc, "record", None)
    hits = getattr(rec, "detail", {}).get("hits", ()) if rec else ()
    print("erfc spec rejected", type(exc).__name__, [(h.rule, h.where) for h in hits][:5] or str(exc)[:300])

T = "skills/analog-gmid-design/gmid_engine/tests/integration/"
env = dict(os.environ, PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1")
for name in ("test_g10_no_recompute_9circuits", "test_layer0_boundary_rows", "test_s0_layer_9circuits", "test_stage_b_library"):
    p = subprocess.run([r"C:\Python314\python.exe", "-P", "-m", "pytest", T + name + ".py", "--collect-only", "-q", "--run-slow",
                        "-p", "no:cacheprovider", "--tb=line"],
                       cwd=ROOT, env=env, capture_output=True, encoding="utf-8", errors="replace")
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    key = [l[:170] for l in lines if "KeyError" in l or "rror" in l][:3]
    print(name, "rc", p.returncode, "|", lines[-1][:120] if lines else "", "|", key)
