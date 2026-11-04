# -*- coding: utf-8 -*-
"""§7 잠금: OP-1 검증자 토큰 목록(g8_dialect_tokens.draft.json)을 core 문자열 리터럴(docstring 제외)에 적용. 기준선 적중 먼저(옛 oracle_netlist/simulate base blob)."""
import ast, glob, json, re, subprocess, sys
R = sys.argv[1]
O = "skills/analog-gmid-design/tools/spice_oracle"
td = json.load(open(f"{R}/.ai/verification/20261016-op1-baseline/op1_measurements/files/g8_dialect_tokens.draft.json", encoding="utf-8"))
toks = [(t["id"], re.compile(t["regex"], re.I)) for t in td["tokens"]]
extra = [("PDK", re.compile(r"sky130|nfet_|pfet_|sky_", re.I)), ("SIM", re.compile(r"ngspice|hspice|spectre", re.I))]


def lits(src):
    t = ast.parse(src)
    doc = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef)) and n.body and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            doc.add(id(n.body[0].value))
    for n in ast.walk(t):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc:
            yield n.lineno, n.value


base_hits = {}
for f in ("oracle_netlist.py", "oracle_simulate.py", "oracle_compare.py"):
    src = subprocess.run(["git", "-C", R, "show", f"c223d47d:{O}/{f}"], capture_output=True).stdout.decode("utf-8", "replace")
    for ln, s in lits(src):
        for tid, rx in toks + extra:
            if rx.search(s):
                base_hits[tid] = base_hits.get(tid, 0) + 1
hits = []
for f in sorted(glob.glob(f"{R}/{O}/core/*.py")):
    src = open(f, encoding="utf-8").read()
    for ln, s in lits(src):
        for tid, rx in toks + extra:
            if rx.search(s):
                hits.append((f.split("/")[-1].split("\\")[-1], ln, tid, s[:120]))
print(json.dumps({"n_tokens": len(toks), "base_hits_by_token": base_hits, "core_hits": hits}, ensure_ascii=False, indent=0))
tests = []
for f in sorted(glob.glob(f"{R}/{O}/tests/core/*.py")):
    src = open(f, encoding="utf-8").read()
    for ln, s in lits(src):
        for tid, rx in toks + extra:
            if rx.search(s):
                tests.append((f.split("\\")[-1], ln, tid, s[:70]))
print("tests/core hits", len(tests), tests[:8])
