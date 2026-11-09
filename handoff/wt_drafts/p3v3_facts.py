"""Phase 3 design v3 -- D0a·T0·S12 사실 재측정(읽기 전용). 결과는 p3v3_facts.json(WP-11).

    C:/Python314/python.exe -B p3v3_facts.py
"""
import ast
import json
import os
import re
import subprocess
import sys

R = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills"
G = os.path.join(R, "tools", "gates")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "p3v3_facts.json")
sys.path.insert(0, G)
import role_paths as rp        # noqa: E402
import import_layering as il   # noqa: E402
import reachability as rch     # noqa: E402
import mutate_changed as mc    # noqa: E402

AS = "skills/analog-gmid-design/assets/"
res = {"head": subprocess.run(["git", "-C", R, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()}
plan = rch._git(R, ["show", "HEAD:docs/01-plan/features/gain-budget-gmid-sizing.plan.md"]).decode("utf-8")

# S5: N3.10 표를 read_section_table로 -- 머리 열과 '대표 대상' 칸 토큰 분류(m4)
header, rows = rp.read_section_table(plan, "### N3.10 ")
res["n310_header"] = header
ci = header.index("대표 대상") if "대표 대상" in header else None
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\*)?$|^[A-Za-z_][A-Za-z0-9_]*\*[A-Za-z0-9_]*$")
tok = {}
for r in rows:
    cell = r[ci]
    ticks = re.findall(r"`([^`]+)`", cell)
    ident, dotted, pyfile, other = [], [], [], []
    for t in ticks:
        if IDENT.match(t):
            ident.append(t)
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.py", t):
            pyfile.append(t)
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", t):
            dotted.append(t)
        else:
            other.append(t)
    prose = re.sub(r"`[^`]+`", "", cell).strip(" ,")
    tok[r[0]] = {"ident": ident, "pyfile": pyfile, "dotted": dotted, "other": other, "prose_left": prose}
res["n310_rep_tokens"] = tok
res["mod_table"] = il.mod_table(plan)

# S6: 최상위 함수 몸체 _refs 대 중첩 포함 _refs -- 중첩 def만 참조하는 엔진 최상위 이름
head = rch.read_tree(R, "HEAD", rch.SOURCE_GLOBS)
eng = {p: s for p, s in head.items() if rch._is_source(p)}
tops = {}
for p, s in eng.items():
    t = ast.parse(s)
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            tops.setdefault(n.name, set()).add(p)
nested_only = {}
for p in (AS + "sizing_recipe.py", AS + "stick_diagram.py"):
    t = ast.parse(eng[p])
    cnt = 0
    ex = []
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            own = {v for k, v in rch._refs(n.body, {}, {}) if k == "name"}
            allr = set()
            for m in ast.walk(n):
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    body = m.body if isinstance(m.body, list) else [m.body]
                    allr |= {v for k, v in rch._refs(body, {}, {}) if k == "name"}
            extra = sorted((allr - own) & set(tops))
            if extra:
                cnt += 1
                ex.append((n.name, extra[:4]))
        elif isinstance(n, ast.ClassDef):
            own = {v for k, v in rch._refs([n], {}, {}) if k == "name"}
            allr = set()
            for m in ast.walk(n):
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    allr |= {v for k, v in rch._refs(m.body, {}, {}) if k == "name"}
            extra = sorted((allr - own) & set(tops))
            if extra:
                cnt += 1
                ex.append((n.name, extra[:4]))
    nested_only[p.rsplit("/", 1)[1]] = {"top_units_with_refs_only_in_nested_or_methods": cnt, "sample": ex[:6]}
res["S6_nested_refs"] = nested_only

# S7: 엔진 __future__ annotations
res["future_annotations"] = {p.rsplit("/", 1)[1]: [i + 1 for i, l in enumerate(s.split("\n")[:60]) if "from __future__ import annotations" in l]
                             for p, s in eng.items() if p.endswith(("sizing_recipe.py", "stick_diagram.py"))}

# S12: workspaces/run_harness.py::run 에 도달하는 test 수(V3 인벤토리 규칙 그대로)
graph = rch.read_tree(R, "HEAD", rch.GRAPH_PREFIXES)
nodes, edges = rch.build_graph(graph)
test_nodes = [n for n in nodes if n.startswith(mc.TESTS_PREFIX) and not n.startswith(mc.TESTS_TOOLS)
              and re.search(r"::(Test[^.]*\.)?test[^.]*$", n)]
inv = mc.inventory(edges, "workspaces/run_harness.py::run", test_nodes)
res["S12_run_inventory"] = {"count": len(inv), "sample": inv[:10]}
inv2 = mc.inventory(edges, AS + "sizing_recipe.py::optimize_full_circuit_budget", test_nodes)
res["S12_optimize_full_circuit_budget_inventory"] = {"count": len(inv2), "sample": inv2[:5]}

# m6: 전수 스캔 test의 금지 이름(삭제·이관 이름 상수)
bans = {}
for f, names in (("test_d_delete_dead.py", ("_DELETED_FUNCTIONS", "_DELETED_METHODS")),
                 ("test_d_delete_telescopic.py", ("_DELETED_NAMES", "_DELETED_CONSTANTS", "_DELETED_FIELDS")),
                 ("test_d_move_tests.py", ("_MOVES",))):
    src = head.get(AS + "tests/contracts/" + f) or rch._git(R, ["show", "HEAD:" + AS + "tests/contracts/" + f]).decode("utf-8")
    t = ast.parse(src)
    vals = {}
    for n in t.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in names:
            strs = sorted({c.value for c in ast.walk(n.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)})
            vals[n.targets[0].id] = strs
    bans[f] = vals
res["m6_scan_names"] = bans

# m7: 문자열 import
out = subprocess.run(["git", "-C", R, "grep", "-n", "-E",
                      r'import_module\("(sizing_recipe|topology_library|design_report|stick_diagram)"|_import\("(sizing_recipe|topology_library|design_report|stick_diagram)"',
                      "--", "*.py"], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
res["m7_string_imports"] = {"count": len(out), "lines": [l[:140] for l in out]}

# S13: _SIZING_RECIPE 소비자
out = subprocess.run(["git", "-C", R, "grep", "-n", "_SIZING_RECIPE", "--", "."], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
res["S13_SIZING_RECIPE"] = [l[:160] for l in out]

# S11: 엔진 모듈 속성 덮어쓰기(추적 .py 전체)
out = subprocess.run(["git", "-C", R, "grep", "-n", "-E",
                      r"^\s*(sr|sd|sizing_recipe|stick_diagram|topology_library|design_report|tl|dr)\.[A-Za-z_]+\s*=[^=]", "--", "*.py"],
                     capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
res["S11_attr_overrides"] = [l[:160] for l in out]

# B5: V3 출력 키(HEAD와 B28 code 브랜치)
for rev in ("HEAD", "role/code/20260930-v3-history-clone"):
    src = rch._git(R, ["show", "%s:tools/gates/mutate_changed.py" % rev]).decode("utf-8")
    keys = []
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "tool" for k in n.keys):
            keys.append([k.value for k in n.keys if isinstance(k, ast.Constant)])
    res.setdefault("B5_v3_output_keys", {})[rev] = keys

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("wrote", OUT)
