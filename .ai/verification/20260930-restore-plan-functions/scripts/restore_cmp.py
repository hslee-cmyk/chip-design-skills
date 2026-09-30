"""복원 대조(계약 1) 보강: 삽입 위치와 복원 정의 밖 변경 0.
(1) 위치: <orig rev>와 <merged rev>에서 복원 def 바로 앞·뒤 최상위 문장(이름 또는 종류)
(2) AST: 병합본 모듈 body에서 복원 def를 빼면 base 모듈 body와 ast.dump(docstring 포함)가 같다
(3) 텍스트: git diff base merged -- <file>의 삭제 줄 0, 추가 줄 = 복원 def 원문 줄 + 빈 줄만
사용: python -P restore_cmp.py <복제본> <orig rev> <base rev> <merged rev> <out.json>"""
import ast, json, subprocess, sys
root, orig, base, merged, out = sys.argv[1:6]
TARGETS = [("skills/analog-gmid-design/assets/sizing_recipe.py", "lut_conditions_from_npz"),
           ("workspaces/run_harness.py", "derived_spec")]


def show(rev, path):
    return subprocess.run(["git", "-C", root, "show", f"{rev}:{path}"], capture_output=True, check=True).stdout


def label(n):
    if n is None:
        return None
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return f"{type(n).__name__}:{n.name}"
    if isinstance(n, ast.Assign):
        return "Assign:" + ",".join(ast.unparse(t) for t in n.targets)
    return type(n).__name__ + ":" + ast.unparse(n)[:60]


def neighbours(tree, name):
    body = tree.body
    idx = [i for i, n in enumerate(body) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(idx) == 1
    i = idx[0]
    return label(body[i - 1] if i > 0 else None), label(body[i + 1] if i + 1 < len(body) else None), i


res = {"orig": orig, "base": base, "merged": merged, "files": {}}
for path, name in TARGETS:
    to, tb, tm = (ast.parse(show(r, path)) for r in (orig, base, merged))
    po, pm = neighbours(to, name), neighbours(tm, name)
    body_m = [n for n in tm.body if not (isinstance(n, ast.FunctionDef) and n.name == name)]
    same_ast = [ast.dump(n) for n in body_m] == [ast.dump(n) for n in tb.body]
    d = subprocess.run(["git", "-C", root, "diff", "-U0", base, merged, "--", path], capture_output=True, check=True).stdout.decode("utf-8")
    hunks = [l for l in d.split("\n") if l.startswith("@@")]
    minus = [l for l in d.split("\n") if l.startswith("-") and not l.startswith("---")]
    plus = [l[1:] for l in d.split("\n") if l.startswith("+") and not l.startswith("+++")]
    src_m = show(merged, path).decode("utf-8").split("\n")
    dn = [n for n in tm.body if isinstance(n, ast.FunctionDef) and n.name == name][0]
    def_lines = src_m[dn.lineno - 1:dn.end_lineno]
    nonblank_plus = [l for l in plus if l.strip()]
    res["files"][path] = {
        "def": name,
        "orig_neighbours": {"prev": po[0], "next": po[1]},
        "merged_neighbours": {"prev": pm[0], "next": pm[1]},
        "same_neighbours": po[:2] == pm[:2],
        "module_ast_without_def_equals_base": same_ast,
        "top_level_counts": {"base": len(tb.body), "merged": len(tm.body)},
        "diff_hunks": len(hunks), "diff_minus_lines": len(minus), "diff_plus_lines": len(plus),
        "plus_nonblank_equals_def_nonblank": nonblank_plus == [l for l in def_lines if l.strip()],
        "plus_blank_lines": len(plus) - len(nonblank_plus),
    }
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
