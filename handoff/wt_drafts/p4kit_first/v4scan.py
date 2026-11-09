"""TS4 대상 예비 실측: V4 lint를 엔진 최상위 def 전부를 subject로 unit·contracts test 파일에 돌린다(scratch, 읽기 전용).
결과 C:/g204/out_v4scan.txt. 판정 수치가 아니라 TS4 card 작성 전 실측의 출발점이다."""
import ast, glob, json, os, subprocess, sys
ROOT = "C:/g204/base"
A = ROOT + "/skills/analog-gmid-design/assets/"
subs = []
for mod in ("sizing_recipe", "stick_diagram", "topology_library", "design_report", "audit_current_forced"):
    p = A + mod + ".py"
    if not os.path.exists(p):
        continue
    t = ast.parse(open(p, encoding="utf-8").read())
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            subs.append("%s:%s" % (mod, n.name))
files = sorted(os.path.relpath(p, ROOT).replace("\\", "/") for p in glob.glob(A + "tests/unit/*.py") + glob.glob(A + "tests/contracts/*.py"))
cmd = [sys.executable, "-B", ROOT + "/tools/gates/test_lint.py", "--root", ROOT]
for s in subs:
    cmd += ["--subject", s]
cmd += files
r = subprocess.run(cmd, capture_output=True, cwd=ROOT + "/tools/gates")
out = r.stdout.decode("utf-8", "replace")
with open("C:/g204/out_v4scan.txt", "w", encoding="utf-8") as fh:
    fh.write("exit=%d subjects=%d files=%d\n" % (r.returncode, len(subs), len(files)))
    try:
        d = json.loads(out)
    except Exception:
        fh.write(out[:4000] + "\nSTDERR:" + r.stderr.decode("utf-8", "replace")[:4000])
        raise SystemExit(1)
    import collections
    c = collections.Counter((f["rule"], f["output"]) for f in d.get("findings", []))
    fh.write("counter %s\n" % dict(c))
    for f in d.get("findings", []):
        if f["output"] not in ("NO-SUBJECT", "PASS"):
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    fh.write("unjudged %d\n" % len(d.get("unjudged", [])))
print(open("C:/g204/out_v4scan.txt", encoding="utf-8").read()[:6000])
