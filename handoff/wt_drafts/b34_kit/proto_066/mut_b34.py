"""Apply the 10 N2 mutants (ids from b34_kit/out/ids_b34_0f23786.json) to head K one at a time, run the prototype
contract-8 test, the whole prototype file and the helper-shape comparison. Results appended per mutant."""
import ast, json, os, re, subprocess, sys
sys.path.insert(0, "C:/g136/gates/tools/gates")
import mutate_changed as mc
R = "C:/g136/repo"
SD = R + "/skills/analog-gmid-design/assets/stick_diagram.py"
C = R + "/skills/analog-gmid-design/assets/tests/contracts/"
OUT = "C:/g136/out/mut_b34.txt"
ids = json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b34_kit/out/ids_b34_0f23786.json", encoding="utf-8"))["N2w"]
orig = open(SD, "rb").read().decode("utf-8").replace(chr(13) + chr(10), chr(10))
tree = ast.parse(orig)
defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
env = dict(os.environ, TMP="C:/g136/tmp", TEMP="C:/g136/tmp", PYTHONDONTWRITEBYTECODE="1",
           APPDATA="C:/Users/HSLEE/AppData/Roaming", USERPROFILE="C:/Users/HSLEE")
PT = ["C:/Python314/python.exe", "-B", "-P", "-m", "pytest", "-c", "C:/g136/gates/tools/gates/pytest_gate.ini",
      "--rootdir=" + R, "--confcutdir=" + R, "-x", "-q", "--color=no", "-p", "no:cacheprovider", "--gmid-phase=2", "--gmid-strict=", "-rf"]
def run(args):
    p = subprocess.run(PT + args, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd="C:/g136")
    o = p.stdout + p.stderr
    e = [l.strip() for l in o.splitlines() if l.startswith("E ") or l.startswith("FAILED ") or l.startswith("ERROR ")]
    first = e[0][:150] if e else ""
    return ("KILLED" if p.returncode else "survived"), first
open(OUT, "w").close()
def log(s):
    print(s, flush=True); open(OUT, "a", encoding="utf-8").write(s + "\n")
sel = sys.argv[1:] or ids
for mid in sel:
    mod, q, op, path = mid.split(":", 3)
    fn = defs[q]
    found = [f for o, pth, f in mc.mutants(fn, orig) if o == op and pth == path]
    assert len(found) == 1, (mid, len(found))
    open(SD, "w", encoding="utf-8", newline="\n").write(mc._replace_def(orig, fn, found[0]))
    try:
        r8 = run([C + "test_b34_grammar_explicit.py", "-k", "c8"])
        rall = run([C + "test_b34_grammar_explicit.py"])
        rh = run([C + "test_b34_helper_shape_cmp.py"])
    finally:
        open(SD, "w", encoding="utf-8", newline="\n").write(orig)
    log("%s\n    proto c8 (fresh process): %s  %s\n    proto all             : %s  %s\n    helper-shape c8       : %s  %s" % (mid, r8[0], r8[1], rall[0], rall[1], rh[0], rh[1]))
