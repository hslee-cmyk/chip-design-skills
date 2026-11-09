"""T0 card(20260930-p3-tests-location-free) '작성 전 실측' 재측정 -- 읽기 전용(측정 전용, 역할 산출물 아님).

    C:/Python314/python.exe -B t0_facts.py <복제본 루트> <rev> <출력 JSON>

git show/grep으로 <rev> 트리만 읽는다(작업 트리 무관). 결과는 출력 JSON 하나(WP-11).
"""
import ast
import json
import re
import subprocess
import sys

ROOT, REV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
A = "skills/analog-gmid-design/assets/"
T = A + "tests/"


def git(*args):
    r = subprocess.run(["git", "-c", "core.quotepath=off", "-C", ROOT] + list(args), capture_output=True)
    if r.returncode not in (0, 1):
        raise SystemExit("git %s failed: %s" % (args, r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8")


def show(p):
    return git("show", "%s:%s" % (REV, p))


def lsfiles(prefix):
    return [x for x in git("ls-tree", "-r", "--name-only", REV, "--", prefix).splitlines() if x]


res = {"rev": git("rev-parse", REV).strip()}

# 1. 파일 이름 문자열을 쓰는 test(probes 제외)
pat = r"(sizing_recipe|stick_diagram|topology_library|design_report|audit_current_forced)\.py"
out = git("grep", "-c", "-E", pat, REV, "--", A + "tests", ":!" + A + "tests/probes")
cnt = {}
for line in out.splitlines():
    path, n = line[len(REV) + 1:].rsplit(":", 1)
    cnt[path[len(T):]] = int(n)
by_dir = {}
for p in cnt:
    by_dir.setdefault(p.split("/")[0], []).append(p)
res["filename_literal_tests"] = {"per_file": cnt, "per_dir_count": {k: len(v) for k, v in by_dir.items()}}

# 2. glob 사용처(전수 스캔 test 위치)
res["glob_sites"] = [l[len(REV) + 1:] for l in git("grep", "-n", "-E", r"r?glob\(", REV, "--", A + "tests").splitlines()]

# 3. setattr·monkeypatch
res["setattr_outside_tools"] = [l[len(REV) + 1:] for l in git("grep", "-n", "setattr", REV, "--", "*.py", ":!tools").splitlines()]
res["monkeypatch_in_tests"] = [l[len(REV) + 1:] for l in git("grep", "-n", r"monkeypatch\.", REV, "--", A + "tests").splitlines()]

# 4. _SIZING_RECIPE 소비자(저장소 전체)
res["_SIZING_RECIPE_all"] = [l[len(REV) + 1:] for l in git("grep", "-n", "_SIZING_RECIPE", REV, "--", ".").splitlines()]

# 5. 전수 스캔 test 금지 이름(m6)
bans = {}
for f, names in (("test_d_delete_dead.py", ("_DELETED_FUNCTIONS", "_DELETED_METHODS")),
                 ("test_d_delete_telescopic.py", ("_DELETED_NAMES", "_DELETED_CONSTANTS", "_DELETED_FIELDS")),
                 ("test_d_move_tests.py", ("_MOVES",))):
    t = ast.parse(show(T + "contracts/" + f))
    vals = {}
    for n in t.body:
        tgt = n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1 else (n.target if isinstance(n, ast.AnnAssign) else None)
        if isinstance(tgt, ast.Name) and tgt.id in names:
            vals[tgt.id] = sorted({c.value for c in ast.walk(n.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)})
    bans[f] = vals
res["m6_scan_names"] = bans

# 6. R-DEF(엔진 소스 = A/*.py 하위 디렉터리 제외 + workspaces/run_harness.py)
eng = [p for p in lsfiles(A) if p.count("/") == A.count("/") and p.endswith(".py")] + ["workspaces/run_harness.py"]
res["engine_source_files"] = eng


def top_bindings(tree):
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(n.name)
        elif isinstance(n, ast.ClassDef):
            out.add(n.name)
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.add(n.name + "." + m.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        out.add(x.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out.add(n.target.id)
    return out


def import_bindings(tree):
    out = {}
    for n in tree.body:
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                out.setdefault(a.asname or a.name, []).append("%s.%s" % (n.module, a.name))
    return out


trees = {p: ast.parse(show(p)) for p in eng}
defs = {}
for p, t in trees.items():
    for nm in top_bindings(t):
        defs.setdefault(nm, []).append(p)
res["rdef_duplicate_names"] = {k: v for k, v in sorted(defs.items()) if len(v) > 1}
ic5 = ast.parse(show(T + "contracts/test_ic5.py"))
table_names = []
for n in ic5.body:
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "_DOMAIN_TABLE":
        table_names = [k.elts[1].value for k in n.value.keys]
res["ic5_table"] = {"rows": len(table_names), "names": table_names}
alldepth = {}
for p, t in trees.items():
    for x in ast.walk(t):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)):
            alldepth.setdefault(x.name, []).append("%s:%d" % (p, x.lineno))
res["ic5_names_alldepth"] = {nm: alldepth.get(nm, []) for nm in table_names}
probe = ["size_transistor", "width_from_id_density", "audit_vsb_consistency", "_build_theta_evaluator",
         "check_quasi_static", "load_topology", "rail_declaration", "RailDeclaration", "_L_ROLE_MULTIPLIERS"]
res["rdef_probe"] = {nm: defs.get(nm, []) for nm in probe}
res["binding_files_probe"] = {nm: sorted(set(defs.get(nm, [])) | {p for p, t in trees.items() if nm in import_bindings(t)})
                              for nm in probe}

# 7. B군 인용 줄
cites = {"test_dup_w_calc.py": (56, 72, 75, 442), "test_df35_harness_paths.py": (206,), "test_ts6_probe_relocate.py": (528,),
         "test_ts6_dead_probes.py": (60, 221, 222, 229, 261, 262), "test_dup_kcl_edges.py": (35,)}
res["cited_lines"] = {f: {str(i): show(T + "contracts/" + f).split("\n")[i - 1].strip() for i in ls} for f, ls in cites.items()}

# 8. design 10 §5.6 영역 표
d10 = show("docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md").split("\n")
rows = [(i + 1, l) for i, l in enumerate(d10) if l.startswith("| `") and "|" in l[2:]]
hdr = [(i + 1, l) for i, l in enumerate(d10) if l.startswith("| 파일 | 함수 | 영역")]
res["design10_table"] = {"header": hdr, "first_row": rows[0] if rows else None,
                         "rows_252_274": [(i, l[:60]) for i, l in rows if 250 <= i <= 276]}

# 9. contracts 목록(새 계약 test 분류 대상 -- 착수 때 이 목록의 차이를 본다)
res["contracts_files"] = sorted(p[len(T):] for p in lsfiles(T + "contracts") if p.endswith(".py"))

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)
print("wrote", OUT)
