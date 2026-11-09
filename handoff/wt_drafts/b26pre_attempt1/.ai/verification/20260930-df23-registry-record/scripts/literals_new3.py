"""계약 6: 병합본 reg_check.py 새/바뀐 def(_df23_expected·_df23_rows_under·check_df23·main)와 새 모듈 상수의 문자열 리터럴 전부,
그리고 엔진 def·class 이름과의 교집합. 결과 C:/g88/o7r/literals_new.txt"""
import ast
import pathlib

R = pathlib.Path("C:/g88/m3t")
A = R / "skills/analog-gmid-design/assets"
src = (A / "tests/tools/reg_check.py").read_text(encoding="utf-8")
tree = ast.parse(src)
names = {"_df23_expected", "_df23_rows_under", "check_df23", "main"}
lits = []
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in names:
        lits += [(n.name, c.value) for c in ast.walk(n) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
    elif isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith("_DF23") for t in n.targets):
        lits += [(n.targets[0].id, c.value) for c in ast.walk(n) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
defs = set()
for p in list(A.glob("*.py")) + [R / "workspaces/run_harness.py"]:
    for x in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs.add(x.name)
out = [f"{a}\t{b!r}" for a, b in lits]
out.append(f"overlap with engine defs ({len(defs)}): {sorted({b for _, b in lits} & defs)}")
pathlib.Path("C:/g88/o7r/literals_new.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
