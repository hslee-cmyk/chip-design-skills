"""L-5 '동작점 사본' 후보 열거 보조(M-G3). dc_op 를 읽는 함수와, DeviceOp 칸 이름(.W .L .current .gm_id .vds .vsb .vgs ...)을 그대로(또는 float/int) 생성자·dict 값에 넣는 자리.
measure_rule_l.py 의 taint(rule_l5_op)는 호출 인자 전파에서 놓침·오탐이 있어(값 복사 후보 6건 중 오탐 3, 알려진 자리 넷 놓침), 이 파일의 넓은 열거를 판정 입력으로 쓴다.
사용: python -B measure_op_sites.py <gmid_engine> <out.jsonl>"""
import ast
import json
import pathlib
import sys

ROOT, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
values = ROOT / "sizing" / "s2_values.py"
tree = ast.parse(values.read_text(encoding="utf-8"))
SLOTS = set()
for stmt in tree.body:
    if isinstance(stmt, ast.ClassDef) and stmt.name == "DeviceOp":
        SLOTS = {i.target.id for i in stmt.body if isinstance(i, ast.AnnAssign)}
rows = []
for path in sorted(ROOT.rglob("*.py")):
    rel = path.relative_to(ROOT).as_posix()
    if rel.startswith("tests/"):
        continue
    src = path.read_text(encoding="utf-8")
    if "dc_op" not in src and "DeviceOp" not in src and "ops[" not in src:
        continue
    module = ast.parse(src)
    for fn in [n for n in ast.walk(module) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        text = ast.unparse(fn)
        reads_op = "'dc_op'" in text
        names = set()
        if reads_op:
            for node in ast.walk(fn):
                if isinstance(node, (ast.Assign,)) and "'dc_op'" in ast.unparse(node.value):
                    for t in node.targets:
                        names |= {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
                if isinstance(node, ast.comprehension) and "'dc_op'" in ast.unparse(node.iter):
                    names |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
                if isinstance(node, ast.For) and "'dc_op'" in ast.unparse(node.iter):
                    names |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        names |= {a.arg for a in fn.args.args if a.arg in ("op", "ops", "o", "dc_op", "device_op")}
        for _ in range(3):
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign) and any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node.value)):
                    if isinstance(node.value, (ast.Name, ast.Subscript)):
                        for t in node.targets:
                            names |= {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
                if isinstance(node, (ast.For, ast.comprehension)):
                    if any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node.iter)):
                        names |= {n.id for n in ast.walk(node.target) if isinstance(n, ast.Name)}
        if not names:
            continue

        def direct(expr):
            if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id in ("float", "int") and expr.args:
                return direct(expr.args[0])
            if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "getattr" and expr.args:
                return direct(expr.args[0])
            if isinstance(expr, ast.Name):
                return expr.id in names
            if isinstance(expr, ast.Subscript):
                return direct(expr.value)
            if isinstance(expr, ast.Attribute):
                return expr.attr in SLOTS and direct(expr.value)
            return False

        for node in ast.walk(fn):
            kind = None
            if isinstance(node, ast.Call):
                args = list(node.args) + [k.value for k in node.keywords]
                hits = [a for a in args if direct(a)]
                callee = ast.unparse(node.func)
                if hits and callee not in ("float", "int", "dict", "tuple", "abs", "len", "getattr", "sorted", "list", "max", "min", "sum"):
                    kind = "call:" + callee
            elif isinstance(node, ast.Dict) and any(v is not None and direct(v) for v in node.values):
                kind = "dict_value"
            elif isinstance(node, (ast.Tuple,)) and any(direct(e) for e in node.elts):
                kind = "tuple"
            elif isinstance(node, ast.Return) and node.value is not None and direct(node.value):
                kind = "return"
            elif isinstance(node, ast.Assign) and direct(node.value) and any(isinstance(t, ast.Attribute) for t in node.targets):
                kind = "attr_assign"
            if kind:
                rows.append({"file": rel, "line": node.lineno, "fn": fn.name, "reads_dc_op": reads_op, "kind": kind, "src": ast.unparse(node)[:120]})
with open(OUT, "w", encoding="utf-8") as fh:
    for row in rows:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
print(len(rows), sorted(SLOTS))
for r in rows:
    print(r["file"], r["line"], r["fn"], r["reads_dc_op"], r["kind"], r["src"][:100])
