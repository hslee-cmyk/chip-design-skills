"""계약 8 정적 확인(AST) + V4 규칙 (1)·(4) 발견 줄 문장 출력. argv: <iso 루트> <base> <T> <출력 json>"""
import ast
import json
import re
import subprocess
import sys

ROOT, BASE, T, OUTP = sys.argv[1:5]
F = "skills/analog-gmid-design/assets/tests/contracts/test_b26pre_existing_paths.py"


def git(*a):
    return subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, check=True).stdout.decode("utf-8")


diff = git("diff", "--name-status", BASE, T).split("\n")
src = git("show", "%s:%s" % (T, F))
tree = ast.parse(src)
lines = src.split("\n")
top_funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
top_assign = [t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)]
tests = [f for f in top_funcs if f.startswith("test")]
helpers = [f for f in top_funcs if not f.startswith("test")]
# 엔진 밑줄 심볼 호출·참조
priv = sorted({"%s.%s" % (n.value.id, n.attr) for n in ast.walk(tree) if isinstance(n, ast.Attribute)
               and isinstance(n.value, ast.Name) and n.value.id in ("sizing_recipe", "stick_diagram") and n.attr.startswith("_")})
from_imports = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
imports = sorted({a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
# == 비교 전부(사람이 읽고 AuditResult·Transistor 객체 비교 여부 판정)
eqs = [(n.lineno, ast.unparse(n)[:160]) for n in ast.walk(tree) if isinstance(n, ast.Compare)
       and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops)]
# library 회로 이름
lib = [p.split("/")[-1].replace(".topology.json", "") for p in git("ls-tree", "--name-only", T, "skills/analog-gmid-design/assets/library/").split("\n")
       if p.endswith(".topology.json")]
strs = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
lib_hits = sorted({l for l in lib if any(l in s for s in strs)})
lib_word = [s for s in strs if "library" in s]
# 레일 표기
rail_like = sorted({s for s in strs if re.fullmatch(r"(?i)(vdd|vss|gnd|avdd|dvdd|vcc|vee|agnd|dgnd)", s)})
parametrize = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "parametrize"]
write_topo = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_b26pre_write_topology"][0]
wt_src = ast.unparse(write_topo)
topo_calls = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "_b26pre_write_topology"]
json_dump_sites = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) in ("json.dumps", "json.dump")]
layer1 = [s for s in strs if "layer1" in s]
res = {
    "diff": [d for d in diff if d], "n_tests": len(tests), "tests": tests, "helpers": helpers, "top_assign": top_assign,
    "tests_prefix_ok": all(t.startswith("test_b26pre_") for t in tests),
    "helpers_prefix_ok": all(h.startswith("_b26pre_") for h in helpers),
    "top_assign_prefix_ok": all(a.startswith("_B26PRE_") for a in top_assign),
    "engine_private_refs": priv, "from_imports": from_imports, "imports": imports,
    "eq_compares": eqs, "library_names": lib, "library_name_hits": lib_hits, "library_word_strings": lib_word,
    "rail_like_strings": rail_like, "parametrize_lines": parametrize,
    "write_topology_has_supply_nets": '"supply_nets": ["vdd", "gnd"]' in wt_src or "'supply_nets': ['vdd', 'gnd']" in wt_src,
    "write_topology_has_schema_2_0": "'schema_version': '2.0'" in wt_src,
    "write_topology_call_lines": topo_calls, "json_dump_sites": json_dump_sites,
    "layer1_strings": layer1,
    "v4_finding_lines": {k: lines[k - 1].strip() for k in (172, 196, 397, 238, 494, 505)},
}
json.dump(res, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
