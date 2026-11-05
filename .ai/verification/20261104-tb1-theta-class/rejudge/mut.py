"""Mutation check on a throwaway copy. usage: mut.py <git clone> <workdir> <out>"""
import json, os, shutil, subprocess, sys
I, W, OUT = sys.argv[1:4]
S = "skills/analog-gmid-design"
os.makedirs(W, exist_ok=True)
subprocess.run(f'git -C "{I}" archive bac4c5de {S} | tar -x -C "{W}"', shell=True, check=True)
R = W + "/" + S
TC, WP = R + "/gmid_engine/sizing/theta_class.py", R + "/gmid_engine/sizing/writer_plan.py"
MUT = [
    ("m0_control", TC, "macro = has_gbw_target or has_settling", "macro = has_gbw_target or has_settling"),
    ("m1_first_view", TC, "gain_views = views if macro else ()", "gain_views = views[:1] if macro else ()"),
    ("m2_no_w4_stop", WP, "if len(tied) > 1:", "if False:"),
    ("m3_no_root_stop", WP, "if ncolour[root] in root_colours:", "if False:"),
    ("m4_B_rank_off", WP, "if looped and theta[rep] == THETA_CLASS_B:", "if False:"),
    ("m5_downstream_off", WP, "downstream = {m: source not in fixed and any(", "downstream = {m: False and any("),
    ("m6_orbit_rep_off", WP, "orbit_rep = {m: size[orbit[m]] > 1 and colour[m] == first[orbit[m]] for m in mos}", "orbit_rep = {m: False for m in mos}"),
    ("m7_diode_rank_off", WP, "sub = (_LOOP_B, diode[rep], orbit_rep[rep]", "sub = (_LOOP_B, False, orbit_rep[rep]"),
    ("m8_strong_off", WP, "strong = {m: theta[m] == THETA_CLASS_S for m in mos}", "strong = {m: False for m in mos}"),
    ("m9_confirm_off", WP, "if cycles[subject] != rep_of.get(value, value):", "if False:"),
    ("m10_orphan_off", WP, "elif subject not in parallel:", "elif False:"),
    ("m11_macro_on", TC, "macro = has_gbw_target or has_settling", "macro = True"),
    ("m12_rout_on", TC, "if has_rout_limit:", "if True:"),
    ("m13_ff_not_B", TC, "THETA_CLASS_B if name in cells else THETA_CLASS_S if name in strong", "THETA_CLASS_S if name in strong"),
]
env = dict(os.environ, OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf8")
T = "gmid_engine/tests/"
with open(OUT, "w", encoding="utf8") as f:
    for name, path, old, new in MUT:
        src = open(path, encoding="utf8", newline="").read()
        if old not in src:
            f.write(json.dumps({"m": name, "status": "pattern_missing"}, ensure_ascii=False) + "\n"); f.flush(); continue
        open(path, "w", encoding="utf8", newline="").write(src.replace(old, new, 1))
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "--tb=no", "-rf", T + "sizing/test_theta_class.py", T + "sizing/test_writer_plan.py"], cwd=R, env=env, capture_output=True, text=True, encoding="utf8", stdin=subprocess.DEVNULL)
        open(path, "w", encoding="utf8", newline="").write(src)
        lines = [l[:170] for l in p.stdout.splitlines() if l.startswith(("FAILED", "ERROR")) or " passed" in l or " failed" in l or " error" in l] or [(p.stdout + p.stderr)[-300:]]
        f.write(json.dumps({"m": name, "killed": p.returncode != 0, "out": lines[-2:]}, ensure_ascii=False) + "\n"); f.flush()
