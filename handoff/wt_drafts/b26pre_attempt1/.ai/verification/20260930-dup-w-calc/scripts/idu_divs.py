"""참고: 범위 파일과 넓은 범위(A/**.py 중 tests 밖, workspaces/*.py)에서 분모 부분트리에 'idu' 이름이 있는 모든 Div 목록(auditor)."""
import ast, glob, json, os, sys
sys.argv.append("")
root = sys.argv[1]
def nm(n):
    if isinstance(n, ast.Name): return n.id
    if isinstance(n, ast.Attribute): return n.attr
    if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str): return n.slice.value
out = []
fs = sorted(set(glob.glob(root + "/skills/analog-gmid-design/assets/**/*.py", recursive=True) + glob.glob(root + "/workspaces/**/*.py", recursive=True)))
for f in fs:
    rel = os.path.relpath(f, root).replace("\\", "/")
    if "/tests/" in rel: continue
    src = open(f, encoding="utf-8", errors="replace").read()
    try: t = ast.parse(src)
    except SyntaxError as e: out.append({"file": rel, "syntax_error": str(e)}); continue
    for n in ast.walk(t):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            if any((nm(x) or "").lower().find("idu") >= 0 for x in ast.walk(n.right)):
                out.append({"file": rel, "line": n.lineno, "src": ast.get_source_segment(src, n)})
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for o in out: print(o)
