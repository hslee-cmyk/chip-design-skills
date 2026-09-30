"""복원 대조 기준(계약 1): <rev>의 두 원본 정의를 git 이력에서 읽어 ast.dump(docstring 포함, 위치 속성 없음)와
원문 바이트(데코레이터 포함 첫 줄 ~ end_lineno, 줄끝 LF 그대로)를 기록한다.
사용: python -P orig_defs.py <복제본> <rev> <out.json> [dump 파일 접두사]"""
import ast, hashlib, json, subprocess, sys
root, rev, out = sys.argv[1:4]
prefix = sys.argv[4] if len(sys.argv) > 4 else None
TARGETS = [("skills/analog-gmid-design/assets/sizing_recipe.py", "lut_conditions_from_npz"),
           ("workspaces/run_harness.py", "derived_spec")]
res = {"rev": subprocess.run(["git", "-C", root, "rev-parse", rev], capture_output=True, check=True).stdout.decode().strip(),
       "defs": {}}
for path, name in TARGETS:
    blob = subprocess.run(["git", "-C", root, "rev-parse", f"{rev}:{path}"], capture_output=True, check=True).stdout.decode().strip()
    data = subprocess.run(["git", "-C", root, "cat-file", "blob", blob], capture_output=True, check=True).stdout
    tree = ast.parse(data)
    hits = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    all_hits = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(hits) == 1 and len(all_hits) == 1, (path, name, len(hits), len(all_hits))
    n = hits[0]
    first = min([n.lineno] + [d.lineno for d in n.decorator_list])
    lines = data.split(b"\n")
    src = b"\n".join(lines[first - 1:n.end_lineno]) + b"\n"
    dump = ast.dump(n)
    doc = ast.get_docstring(n, clean=False)
    ent = {"path": path, "blob": blob, "top_level": True, "lineno": n.lineno, "end_lineno": n.end_lineno,
           "decorators": len(n.decorator_list), "has_docstring": doc is not None,
           "docstring_sha256": hashlib.sha256(doc.encode("utf-8")).hexdigest() if doc is not None else None,
           "ast_dump_sha256": hashlib.sha256(dump.encode("utf-8")).hexdigest(), "ast_dump_len": len(dump),
           "source_bytes_sha256": hashlib.sha256(src).hexdigest(), "source_bytes_len": len(src),
           "source_has_cr": b"\r" in src,
           "signature": ast.unparse(n.args), "returns": ast.unparse(n.returns) if n.returns else None}
    res["defs"][name] = ent
    if prefix:
        open(f"{prefix}_{name}.ast.txt", "w", encoding="utf-8", newline="\n").write(dump + "\n")
        open(f"{prefix}_{name}.src.py", "wb").write(src)
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=1))
