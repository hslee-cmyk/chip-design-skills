"""B41 kill 증명: 복제본 작업 트리에서 save_instance_json 변이 4개를 하나씩 넣고 지정 test만 돌린다.

사용: python -B -P b41_kill.py <복제본 루트> <도구 디렉터리(mutate_changed.py가 있는 곳)> <pytest_ini> <out.jsonl> <test nodeid...>
기준(변이 없음) 실행이 exit 0이어야 의미가 있다(아니면 exit 2). 변이마다 결과를 append하고, 끝나면 원본으로 되돌린 뒤 요약 한 줄.
"""
import ast, importlib.util, json, os, subprocess, sys

root, tooldir, ini, out = [os.path.abspath(x) for x in sys.argv[1:5]]
tests = sys.argv[5:]
sys.path.insert(0, tooldir)
spec = importlib.util.spec_from_file_location("mc", os.path.join(tooldir, "mutate_changed.py"))
mc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc)
SD = os.path.join(root, "skills", "analog-gmid-design", "assets", "stick_diagram.py")
B41 = ["stmt_delete:body[2]", "stmt_delete:body[2].body[0]",
       "const+:body[6].body[0].value.keywords[0].value", "const-:body[6].body[0].value.keywords[0].value"]
src = open(SD, encoding="utf-8", newline="").read()
fn = [n for q, n in mc.rch.iter_defs(ast.parse(src)) if q == "save_instance_json"][0]
pyc = os.path.join(os.environ.get("TEMP", root), "b41pyc")


def run():
    env = dict(os.environ, PYTHONPYCACHEPREFIX=pyc, PYTHONDONTWRITEBYTECODE="1")
    cmd = [sys.executable, "-P", "-m", "pytest", "-c", ini, "--rootdir=" + root, "--confcutdir=" + root, "-x", "-q",
           "-p", "no:cacheprovider", "--gmid-phase=%s" % os.environ.get("GMID_PHASE", "3"), "--gmid-strict="] + [os.path.join(root, t.split("::")[0]) + ("::" + t.split("::", 1)[1] if "::" in t else "")
                                       for t in tests]
    r = subprocess.run(cmd, cwd=root, capture_output=True, env=env)
    return r.returncode, (r.stdout.decode("utf-8", "replace").strip().splitlines()[-1:]
                          + r.stderr.decode("utf-8", "replace").strip().splitlines()[-3:])


def append(rec):
    with open(out, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


code, tail = run()
append({"case": "baseline", "exit": code, "tail": tail, "bind_hash": mc.bind_hash(fn)})
if code != 0:
    print(json.dumps({"verdict": "ERROR", "baseline_exit": code, "tail": tail}, ensure_ascii=False))
    sys.exit(2)
summary = {}
try:
    for op, p, mfn in mc.mutants(fn, src):
        key = "%s:%s" % (op, p)
        if key not in B41:
            continue
        with open(SD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(mc._replace_def(src.replace("\r\n", "\n"), fn, mfn))
        c, t = run()
        summary[key] = "killed" if c != 0 else "survived"
        append({"case": key, "exit": c, "tail": t, "result": summary[key]})
finally:
    with open(SD, "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
print(json.dumps({"tests": tests, "results": summary}, ensure_ascii=False))
