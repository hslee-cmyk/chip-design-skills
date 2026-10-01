"""재시도 3차 순서 3: 새 test 파일 AST 규칙 점검(card oracle 절 test 작성 규칙)."""
import ast, sys, collections
p = sys.argv[1]
src = open(p, encoding="utf-8").read(); t = ast.parse(src)
tests = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
helpers = [n for n in t.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("test_")]
print("test funcs", len(tests), "all test_p10b_", all(n.name.startswith("test_p10b_") for n in tests))
print("helpers", [n.name for n in helpers], "all _p10b_", all(n.name.startswith("_p10b_") for n in helpers))
first_rc = [(n.lineno, ast.unparse(n)) for n in t.body if isinstance(n, (ast.Import, ast.ImportFrom)) and "reg_check" in ast.unparse(n)]
print("module reg_check imports", first_rc)
inner_imp = [(f.name, n.lineno) for f in tests + helpers for n in ast.walk(f) if isinstance(n, (ast.Import, ast.ImportFrom))]
print("imports inside functions", inner_imp)
calls = collections.Counter(); where = collections.defaultdict(set)
for f in tests + helpers:
    for n in ast.walk(f):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("check_df23", "main", "getattr"):
            calls[(n.func.id, f.name.startswith("test_"))] += 1; where[n.func.id].add(f.name)
print("calls (name, in_test_body)", dict(calls))
print("helpers calling subject", sorted(x for k in ("check_df23","main") for x in where[k] if not x.startswith("test_")))
no_assert = [f.name for f in tests if not any(isinstance(n, ast.Assert) or (isinstance(n, ast.With) and "raises" in ast.unparse(n.items[0].context_expr)) for n in ast.walk(f))]
print("tests without direct assert/raises", no_assert)
eq_empty = [n.lineno for n in ast.walk(t) if isinstance(n, ast.Compare) and any(isinstance(c, ast.List) and not c.elts for c in n.comparators)]
print("`== []` lines", eq_empty)
print("tests using check_df23 or main in body", sum(1 for f in tests if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("check_df23","main") for n in ast.walk(f))), "/ subprocess-only", [f.name for f in tests if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("check_df23","main") for n in ast.walk(f))])
