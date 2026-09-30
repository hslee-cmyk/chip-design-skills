"""E-AST: 파일(git rev:path blob)의 최상위 정의 이름별 ast.dump(docstring 포함, 위치 속성 제외)와 sha256.
사용: e_ast.py <repo> <rev> <path> <out.json> <이름>... ; 순서 7에서 병합본 새 파일에 같은 이름으로 돌려 대조한다."""
import ast, hashlib, json, subprocess, sys
repo, rev, path, out = sys.argv[1:5]
names = sys.argv[5:]
src = subprocess.run(["git", "-C", repo, "cat-file", "blob", f"{rev}:{path}"], capture_output=True, check=True).stdout
tree = ast.parse(src.decode("utf-8"))
text = src.decode("utf-8").replace("\r\n", "\n")
lines = text.split("\n")
def bound(n):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {n.name}
    if isinstance(n, ast.Assign):
        return {t.id for t in n.targets if isinstance(t, ast.Name)}
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
        return {n.target.id}
    return set()
res = {"repo_rev": rev, "path": path, "blob_sha256": hashlib.sha256(src).hexdigest(), "defs": {}}
for name in names:
    hits = [n for n in tree.body if name in bound(n)]
    ent = {"n_top_level_bindings": len(hits)}
    if hits:
        n = hits[0]
        d = ast.dump(n, include_attributes=False)
        start = min([n.lineno] + [x.lineno for x in getattr(n, "decorator_list", [])])
        seg = "\n".join(lines[start - 1:n.end_lineno])
        ent.update({
            "kind": type(n).__name__,
            "lineno": start, "end_lineno": n.end_lineno,
            "has_docstring": isinstance(n, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(n) is not None,
            "ast_dump_sha256": hashlib.sha256(d.encode("utf-8")).hexdigest(),
            "ast_dump_len": len(d),
            "source_lines_sha256_lf": hashlib.sha256(seg.encode("utf-8")).hexdigest(),
            "ast_dump": d,
        })
    res["defs"][name] = ent
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in res["defs"].items():
    print(k, v.get("kind"), v.get("lineno"), v.get("end_lineno"), v["n_top_level_bindings"], v.get("has_docstring"), v.get("ast_dump_sha256"), v.get("source_lines_sha256_lf"))
