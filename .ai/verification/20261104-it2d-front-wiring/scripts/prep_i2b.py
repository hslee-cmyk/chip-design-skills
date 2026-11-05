import json
T = "C:/Users/HSLEE/AppData/Local/Temp/la1s_it2c_audit"
R = T + "/res/i2"
E = "gmid_engine/tests/"
py = "python"
cwd = T + "/i2/skills/analog-gmid-design"
base = [py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=short"]
jobs = [{"name": "i2_structure2", "cwd": cwd, "out": R + "/structure.txt", "cmd": base + ["--junitxml=" + R + "/structure.xml", E + "structure"]}]
for x in "common_gate_amplifier,current_reuse_telescopic_ota,folded_cascode,ngcc_3stage_ff,nmcnr_amplifier,pushpull_follower_buffer,r2r_opamp,rfc_ota,sf_pushpull_output_opamp,two_stage_ota,two_stage_ota_sf".split(","):
    jobs.append({"name": "rm_" + x, "cwd": T + "/m2/skills/analog-gmid-design", "out": R + "/rm/" + x + ".txt",
                 "cmd": base[:3] + [E + "integration/test_zz_remeasure.py", "-q", "-p", "no:cacheprovider", "--tb=short"], "env": {"RM_CIRCUIT": x, "RM_OUT": R + "/rm/" + x + ".json"}})
jobs.append({"name": "flow", "cwd": T + "/m2/skills/analog-gmid-design", "out": R + "/flow.txt", "cmd": base[:3] + [E + "integration/test_zz_i2flow.py", "-q", "-p", "no:cacheprovider", "--tb=short", "--run-slow"],
             "env": {"PROBE_OUT": R + "/flow.jsonl", "PROBE_FLOW": "nmcnr_amplifier,current_reuse_telescopic_ota,sf_pushpull_output_opamp,folded_cascode"}})
D = "metrics/test_icm_window.py,metrics/test_ls_swing.py,metrics/test_metrics_aux.py,metrics/test_ss_evaluate.py,metrics/test_registry.py,metrics/test_catalog.py,metrics/test_pending_metrics.py,metrics/test_aux_types.py,sizing/test_input_window.py"
K = "sizing/test_kernel_run.py,sizing/test_seal_versions.py,sizing/test_size_and_seal.py,search/test_it2e_partial_snapshot.py,search/test_kernel.py"
jobs.append({"name": "red_d", "cwd": T, "out": R + "/red_d.txt", "cmd": [py, T + "/scripts/run_red2.py", T + "/r2", "0e6449f7", R + "/red_d.jsonl", T + "/plug", D]})
jobs.append({"name": "red_e", "cwd": T, "out": R + "/red_e.txt", "cmd": [py, T + "/scripts/run_red2.py", T + "/r2", "9798e5c1", R + "/red_e.jsonl", T + "/plug", K]})
jobs.append({"name": "mutate2", "cwd": T, "out": R + "/mutate.txt", "cmd": [py, T + "/scripts/mutate2.py", T + "/m2", R + "/mutations.jsonl"]})
json.dump(jobs, open(R + "/jobs2.json", "w", encoding="utf-8"))
print(len(jobs))
