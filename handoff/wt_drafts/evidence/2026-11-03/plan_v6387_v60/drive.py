"""v60 driver: run q8_run.py per circuit with a per-circuit time limit (no external timeout tool); per-circuit stderr + rc appended to drive_out.txt."""
import subprocess, sys, os
D = os.path.dirname(os.path.abspath(__file__))
CIRS = "common_gate_amplifier folded_cascode two_stage_ota two_stage_ota_sf cnr_ota erfc_ota rfc_ota r2r_opamp current_reuse_telescopic_ota sf_pushpull_output_opamp".split()
for c in CIRS:
    try:
        r = subprocess.run([sys.executable, os.path.join(D, "q8_run.py"), c, "ga"], capture_output=True, timeout=170, cwd=D)
        rc = r.returncode; tail = r.stderr.decode("utf-8", "replace")[-300:]
    except subprocess.TimeoutExpired:
        rc = "timeout"; tail = ""
    with open(os.path.join(D, "drive_out.txt"), "ab") as f:
        f.write(f"{c} rc={rc} {tail if rc != 0 else ''}\n".encode("utf-8"))
print("done")
