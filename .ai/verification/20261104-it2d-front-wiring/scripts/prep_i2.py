import json
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_it2c_audit"
R = T + "/res/i2"
E = "gmid_engine/tests/"
CARD = """metrics/test_icm_window.py metrics/test_ls_swing.py metrics/test_metrics_aux.py metrics/test_ss_evaluate.py metrics/test_registry.py metrics/test_catalog.py metrics/test_pending_metrics.py metrics/test_aux_types.py authoring/test_metrics_catalog.py sizing/test_input_window.py sizing/test_kernel_run.py sizing/test_seal_versions.py sizing/test_size_and_seal.py search/test_it2e_partial_snapshot.py search/test_kernel.py metrics/test_icm_config.py""".split()
import os
root = T + "/i2/skills/analog-gmid-design/gmid_engine/tests/"
CARD = [c for c in CARD if os.path.exists(root + c)]
cwd = T + "/i2/skills/analog-gmid-design"
base = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=short"]
jobs = [
    {"name": "i2_card", "cwd": cwd, "out": R + "/card.txt", "cmd": base + ["--junitxml=" + R + "/card.xml"] + [E + c for c in CARD]},
    {"name": "i2_structure", "cwd": cwd, "out": R + "/structure.txt", "cmd": base + ["--junitxml=" + R + "/structure.xml", E + "structure"]},
    {"name": "i2_canon", "cwd": cwd, "out": R + "/canon.txt", "cmd": base + ["--junitxml=" + R + "/canon.xml", E + "search/test_canonical_order.py"]},
    {"name": "i2_smoke", "cwd": cwd, "out": R + "/smoke.txt", "cmd": base + ["--junitxml=" + R + "/smoke.xml", "--run-slow", "-k", "folded_cascode or ngcc_3stage_ff", E + "integration/test_stage_b_library.py", E + "integration/test_s0_layer_9circuits.py", E + "integration/test_g10_no_recompute_9circuits.py"]},
]
os.makedirs(R, exist_ok=True)
json.dump(jobs, open(R + "/jobs.json", "w", encoding="utf-8"))
print(CARD)
