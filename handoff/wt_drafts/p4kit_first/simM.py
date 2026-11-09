"""모의 병합본 M(= 코드 변경 A + 레지스트리 + 모의 test 변경) 만들기. 측정 전용 -- 실제 card 구현이 아니다
(작성자 != 검증자: 이 산출물은 code-author·test-author·auditor에게 건네지 않는다)."""
import ast, os, re, subprocess, sys
CL = "C:/g204/sim"
A = "skills/analog-gmid-design/assets/"
REG = "docs/03-analysis/gain-budget-gmid-sizing.function-registry.md"
UT_SR = A + "tests/unit/test_selftest_sizing_recipe.py"
UT_SD = A + "tests/unit/test_selftest_stick_diagram.py"
IC5 = A + "tests/contracts/test_ic5.py"


def git(*a):
    r = subprocess.run(["git", "-C", CL] + list(a), capture_output=True)
    if r.returncode:
        raise SystemExit("git %s: %s" % (a, r.stderr.decode("utf-8", "replace")))
    return r.stdout


def rd(rev, p):
    return git("show", "%s:%s" % (rev, p)).decode("utf-8")


def drop_import_names(src, lineno, names):
    lines = src.split("\n")
    t = ast.parse(src)
    node = next(n for n in t.body if isinstance(n, ast.ImportFrom) and n.lineno == lineno)
    seg = "\n".join(lines[node.lineno - 1:node.end_lineno])
    for nm in names:
        seg2 = re.sub(r"\b%s\b,\s*" % nm, "", seg)
        if seg2 == seg:
            seg2 = re.sub(r",\s*\b%s\b" % nm, "", seg)
        assert seg2 != seg, nm
        seg = seg2
    lines[node.lineno - 1:node.end_lineno] = seg.split("\n")
    return "\n".join(lines)


def drop_funcs(src, names):
    t = ast.parse(src); lines = src.split("\n")
    spans = [(min([n.lineno] + [d.lineno for d in n.decorator_list]), n.end_lineno) for n in t.body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(spans) == len(names)
    for s, e in sorted(spans, reverse=True):
        del lines[s - 1:e]
    return "\n".join(lines)


base = git("rev-parse", "sim").decode().strip()
HA = git("rev-parse", "simA").decode().strip()
files = {}
# 레지스트리: §7 행 5개·§3 R0 행 1개 삭제, §1 D·R0 수와 소절 괄호 수 갱신
reg = rd(base, REG).split("\n")
kill = []
for i, L in enumerate(reg):
    for nm in ("solve_diode_stack_current", "estimate_area_budget", "load_derived_bounds", "derived_bounds_path",
               "MultiLeafHubParityVerdict", "check_multi_leaf_hub_parity"):
        if L.startswith("| `%s`" % nm):
            kill.append(i)
print("registry rows removed (1-based):", [k + 1 for k in kill])
reg = [L for i, L in enumerate(reg) if i not in kill]
txt = "\n".join(reg)
txt = txt.replace("| sizing_recipe.py | 86 | 77 | 20 | 9 | 11 |", "| sizing_recipe.py | 85 | 77 | 20 | 6 | 11 |")
txt = txt.replace("| stick_diagram.py | 85 | 16 | 12 | 15 | 7 |", "| stick_diagram.py | 85 | 16 | 12 | 13 | 7 |")
txt = txt.replace("### sizing_recipe.py (86)", "### sizing_recipe.py (85)").replace("### sizing_recipe.py (9)", "### sizing_recipe.py (6)")
txt = txt.replace("### stick_diagram.py (15)", "### stick_diagram.py (13)")
files[REG] = txt
# test 모의 변경(실제는 test-author 몫)
s = rd(base, UT_SR)
s = drop_import_names(s, 24, ["estimate_area_budget", "solve_diode_stack_current"])
files[UT_SR] = drop_funcs(s, ["test_s007_solve_diode_stack_current", "test_s028_estimate_area_budget"])
s = rd(base, UT_SD)
s = drop_import_names(s, 24, ["check_multi_leaf_hub_parity"])
helper = ("\n\ndef _sim_hub_parity_kind(n_fingers_by_leaf):\n"
          "    m = sum(1 for k in n_fingers_by_leaf.values() if k % 2 == 1)\n"
          "    return 'circuit' if m == 0 else ('path' if m <= 2 else 'impossible')\n")
s = s.replace("check_multi_leaf_hub_parity({f\"leaf{i}\": k for i, k in enumerate(kis)}).kind",
              "_sim_hub_parity_kind({f\"leaf{i}\": k for i, k in enumerate(kis)})")
s = s.replace("formula = check_multi_leaf_hub_parity({\"M3\": k, \"M4\": k, \"M6\": k})",
              "formula_kind = _sim_hub_parity_kind({\"M3\": k, \"M4\": k, \"M6\": k})")
s = s.replace("== formula.ok", "== (formula_kind != 'impossible')").replace("formula.kind", "formula_kind").replace("(m={formula.m_odd_leaves})", "")
s = s.rstrip("\n") + helper
assert not [n for n in ast.walk(ast.parse(s)) if isinstance(n, ast.Name) and n.id == "check_multi_leaf_hub_parity"], "s058 잔여 호출"
files[UT_SD] = s
s = rd(base, IC5)
s = s.replace('    ("stick_diagram.py", "check_multi_leaf_hub_parity"): {_NONE_LAYOUT},\n', "")
s = s.replace('    ("stick_diagram.py", "audit_vertical_stack_id_euler_feasibility"): {_NONE_LAYOUT},\n', "")
s = s.replace("assert len(_DOMAIN_TABLE) == 21", "assert len(_DOMAIN_TABLE) == 19")
files[IC5] = s
git("checkout", "--quiet", "-B", "simM", HA)
for rel, t in files.items():
    with open(os.path.join(CL, *rel.split("/")), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(t)
    git("add", "--", rel)
git("commit", "--quiet", "-m", "sim M: registry + simulated test edits")
print("simM", git("rev-parse", "HEAD").decode().strip())
git("checkout", "--quiet", "sim")
