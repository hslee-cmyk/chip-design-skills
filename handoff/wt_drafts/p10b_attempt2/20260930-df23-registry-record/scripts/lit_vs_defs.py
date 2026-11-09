"""순서 3 사전 점검: 새 test의 문자열 상수 중 엔진(_is_source: A/*.py, workspaces/run_harness.py) def 이름과 같은 것."""
import ast
import pathlib

R = pathlib.Path("C:/g88/iso2")
A = R / "skills/analog-gmid-design/assets"
TF = A / "tests/contracts/test_reg_check_df23.py"
defs = set()
for p in list(A.glob("*.py")) + [R / "workspaces/run_harness.py"]:
    for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.add(n.name)
lits = {n.value for n in ast.walk(ast.parse(TF.read_text(encoding="utf-8")))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)}
hit = sorted(lits & defs)
out = f"engine defs {len(defs)}, test str literals {len(lits)}, overlap {hit}\n"
pathlib.Path("C:/g88/out2/lit_vs_defs.txt").write_text(out, encoding="utf-8")
print(out)
