"""엔진 순수 삭제 확인: base 파일 AST에서 삭제 대상 최상위 정의를 뺀 모듈 AST가 병합본 파일 AST와 같은가(docstring 포함, 위치 속성 제외).
사용: engine_pure_delete.py <repo> <base> <merged> <path> <이름>..."""
import ast, hashlib, subprocess, sys
repo, base, mg, path = sys.argv[1:5]; names = set(sys.argv[5:])
def load(rev):
    return ast.parse(subprocess.run(["git", "-C", repo, "cat-file", "blob", f"{rev}:{path}"], capture_output=True, check=True).stdout.decode("utf-8"))
def bound(n):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): return {n.name}
    if isinstance(n, ast.Assign): return {t.id for t in n.targets if isinstance(t, ast.Name)}
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name): return {n.target.id}
    return set()
b, m = load(base), load(mg)
removed = [n for n in b.body if bound(n) & names]
kept = [n for n in b.body if not (bound(n) & names)]
db = [ast.dump(n) for n in kept]; dm = [ast.dump(n) for n in m.body]
print(path, "base_top", len(b.body), "removed", sorted(set().union(*[bound(n) for n in removed])), len(removed), "merged_top", len(m.body),
      "equal_after_removal", db == dm,
      "sha_kept", hashlib.sha256("\n".join(db).encode()).hexdigest(), "sha_merged", hashlib.sha256("\n".join(dm).encode()).hexdigest())
# 모듈 전체에서 이름이 남아 있는가(Name/Attribute/def/import alias)
left = sorted({(getattr(x, "lineno", 0), getattr(x, "id", None) or getattr(x, "attr", None) or getattr(x, "name", None))
               for x in ast.walk(m) if (getattr(x, "id", None) in names or getattr(x, "attr", None) in names or getattr(x, "name", None) in names)})
print("names_left_in_merged", left)
