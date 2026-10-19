"""G-8 draft support: dump every string literal (docstrings excluded) of the old oracle *.py, to find dialect grammar forms."""
import ast, json, glob, os, re
O = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/src/skills/analog-gmid-design/tools/spice_oracle"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/g8_old_literals.json"


def literals(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    doc_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            b = node.body[0]
            if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                doc_ids.add(id(b.value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_ids:
            out.append((node.lineno, node.value))
    return out


res = {}
for p in sorted(glob.glob(O + "/*.py")):
    res[os.path.basename(p)] = literals(p)
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print({k: len(v) for k, v in res.items()})
