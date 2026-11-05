# -*- coding: utf-8 -*-
"""A3-8 §7 잠금 AST 부분. cwd = 복제본 루트."""
import ast, glob, json, os, sys
O = "skills/analog-gmid-design/tools/spice_oracle"
res = {"core_imports_bad": [], "core_nonpy": [], "adapter_imports_bad": [], "core_str_hits": []}
for f in sorted(glob.glob(O + "/core/*")):
    if f.endswith("__pycache__"):
        continue
    if not f.endswith(".py"):
        res["core_nonpy"].append(f)
BAD = ("adapters", "subprocess", "oracle_", "gmid_engine")
ts = [".include", ".option", ".temp", ".control", ".endc", "wrdata", "alter ", "ngspice", "@m.", "showmod", "sky130", "nfet", "pfet", "spectre", "hspice", "ac dec", "meas ", ".tran", ".op", ".ac", ".noise", ".pz", ".tf"]
for f in sorted(glob.glob(O + "/core/*.py")):
    t = ast.parse(open(f, encoding="utf-8").read())
    doc = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith(BAD):
                    res["core_imports_bad"].append((f, a.name))
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith(BAD):
            res["core_imports_bad"].append((f, n.module))
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            for k in ts:
                if k.lower() in n.value.lower():
                    res["core_str_hits"].append((os.path.basename(f), n.lineno, k, n.value[:110]))
for f in sorted(glob.glob(O + "/adapters/ngspice/*.py")):
    t = ast.parse(open(f, encoding="utf-8").read())
    for n in ast.walk(t):
        names = [a.name for a in n.names] if isinstance(n, ast.Import) else ([n.module] if isinstance(n, ast.ImportFrom) and n.module else [])
        for m in names:
            if m.startswith(("gmid_engine", "core.compare", "core.measures", "core.build")):
                res["adapter_imports_bad"].append((f, m))
print(json.dumps(res, ensure_ascii=False, indent=0))
sys.path.insert(0, O)
for m in ("oracle_simulate", "oracle_netlist", "oracle_noise", "oracle_swing", "oracle_offset_mc"):
    try:
        __import__(m)
        print(m, "import ok")
    except Exception as e:
        print(m, "import FAIL", type(e).__name__, str(e)[:100])
