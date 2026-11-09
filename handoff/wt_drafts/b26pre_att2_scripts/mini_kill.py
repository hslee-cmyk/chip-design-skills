# sandbox-only: stmt_delete (replace by pass) of listed base lines, run one test file, append result per case
import ast, json, os, shutil, subprocess, sys
I = r"C:/g344/iso"; A = I + "/skills/analog-gmid-design/assets"; C = A + "/tests/contracts"
tf, tag, outp = sys.argv[1], sys.argv[2], sys.argv[3]
shutil.copy(tf, C + "/test_b26pre_existing_paths.py")
cases = [("sizing_recipe.py", l) for l in (9403, 9405, 11695, 11697, 11699, 6572, 11800, 11876, 11878, 11879, 11880, 11827, 11834, 11835, 11836, 11802)] + \
        [("stick_diagram.py", l) for l in (4515, 4516, 3275, 3278, 3279, 6878, 6880, 2094, 2095, 2170, 2171, 3971, 3972)]
def run():
    env = dict(os.environ, PYTHONHASHSEED="1", TMP=r"C:/g344/tmp", TEMP=r"C:/g344/tmp")
    p = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-c", I + "/tools/gates/pytest_gate.ini",
                        "--rootdir=" + I, "--confcutdir=" + I, "--basetemp=C:/g344/tmp/mk", C + "/test_b26pre_existing_paths.py",
                        "--gmid-phase=3", "--gmid-strict=", "-rf"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    failed = sorted({l.split("::")[1].split(" ")[0] for l in p.stdout.splitlines() if l.startswith("FAILED")})
    return p.returncode, failed, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
with open(outp, "a", encoding="utf-8") as f:
    f.write(json.dumps({"tag": tag, "case": "baseline", "r": run()}, ensure_ascii=False) + "\n")
for fn, line in cases:
    path = A + "/" + fn
    orig = open(path, encoding="utf-8").read()
    try:
        tree = ast.parse(orig)
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.stmt) and n.lineno == line)
        lines = orig.split("\n")
        ind = lines[line - 1][:len(lines[line - 1]) - len(lines[line - 1].lstrip())]
        new = lines[:line - 1] + [ind + "pass"] + [""] * (node.end_lineno - line) + lines[node.end_lineno:]
        open(path, "w", encoding="utf-8", newline="").write("\n".join(new))
        r = run()
    finally:
        open(path, "w", encoding="utf-8", newline="").write(orig)
    with open(outp, "a", encoding="utf-8") as f:
        f.write(json.dumps({"tag": tag, "case": "%s:%d" % (fn[:2].upper().replace("SI", "SR").replace("ST", "SD"), line), "r": r}, ensure_ascii=False) + "\n")
subprocess.run(["git", "-C", I, "diff", "--quiet", "--", "skills/analog-gmid-design/assets/sizing_recipe.py", "skills/analog-gmid-design/assets/stick_diagram.py"], check=True)
