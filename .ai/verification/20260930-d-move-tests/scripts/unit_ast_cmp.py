"""base/T unit 파일: import·sys.path 문장 밖 최상위 문장 AST 동일 여부와 import 이름 차이."""
import ast, json, subprocess, sys
root, base, head, out = sys.argv[1:5]
A = "skills/analog-gmid-design/assets/tests/unit/"
res = {}
def load(rev, p):
    return subprocess.run(["git", "-C", root, "show", f"{rev}:{p}"], capture_output=True, check=True).stdout.decode("utf-8")
def imports(tree):
    s = set()
    for n in tree.body:
        if isinstance(n, ast.ImportFrom):
            for a in n.names: s.add((n.module, a.name, a.asname))
        elif isinstance(n, ast.Import):
            for a in n.names: s.add((None, a.name, a.asname))
    return s
for f in ["test_selftest_sizing_recipe.py", "test_selftest_stick_diagram.py"]:
    tb, th = ast.parse(load(base, A + f)), ast.parse(load(head, A + f))
    nb = [ast.dump(n) for n in tb.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    nh = [ast.dump(n) for n in th.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    # T에 더해진 비-import 문장(순서 유지 차이)
    import difflib
    added = [x for x in nh if x not in nb]
    removed = [x for x in nb if x not in nh]
    ib, ih = imports(tb), imports(th)
    tests_b = sorted(n.name for n in tb.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test"))
    tests_h = sorted(n.name for n in th.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test"))
    res[f] = {
        "non_import_stmt_count": [len(nb), len(nh)],
        "non_import_removed": removed,
        "non_import_added": added,
        "import_only_base": sorted(map(str, ib - ih)),
        "import_only_T": sorted(map(str, ih - ib)),
        "test_funcs_equal": tests_b == tests_h, "n_test_funcs": len(tests_b),
        "funcdefs_ast_equal": [ast.dump(n) for n in tb.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))] == [ast.dump(n) for n in th.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],
    }
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
