import ast, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
iso, rev = sys.argv[1], sys.argv[2]
mods = {"sizing_recipe", "topology_library", "design_report"}
G = ["git", "-c", "core.quotepath=off", "-C", iso]
r = subprocess.run(G + ["grep", "-z", "-l", "-E", "sizing_recipe|topology_library|design_report", rev, "--", "*.py"],
                   capture_output=True)
if r.returncode not in (0, 1):
    sys.exit("git grep failed: " + r.stderr.decode("utf-8", "replace"))
bad = 0
for ent in r.stdout.decode("utf-8").split("\0"):
    if not ent:
        continue
    if not ent.startswith(rev + ":"):
        sys.exit("unexpected git grep entry: " + ent)
    p = ent[len(rev) + 1:]
    s = subprocess.run(G + ["show", rev + ":" + p], capture_output=True)
    if s.returncode != 0:
        print("ERROR " + p); bad += 1
        continue
    try:
        tree = ast.parse(s.stdout)
    except SyntaxError:
        print("PARSE-ERROR " + p)
        continue
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] in mods for a in n.names):
            print("stmt %s:%d" % (p, n.lineno))
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] in mods:
            print("stmt %s:%d" % (p, n.lineno))
        elif isinstance(n, ast.Call) and n.args and isinstance(n.args[0], ast.Constant) \
                and isinstance(n.args[0].value, str):
            f = n.func
            fn = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if fn in ("import_module", "_import", "__import__") and n.args[0].value.split(".")[0] in mods:
                print("call %s:%d" % (p, n.lineno))
sys.exit(3 if bad else 0)
