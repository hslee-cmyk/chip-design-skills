"""계약 1: 새 파일의 이관 정의 밖 최상위 문장 분류, 이관 정의의 자유 전역 이름이 새 파일에서 어떻게 묶이는지,
base 엔진에서 같은 이름이 어떻게 묶였는지(import 출처 또는 모듈 내 정의)를 적는다.
사용: new_module_check.py <repo> <base> <merged> <새 파일> <base 엔진 파일> <이름>..."""
import ast, builtins, json, subprocess, sys
repo, base, mg, newp, engp = sys.argv[1:6]; names = set(sys.argv[6:])
def load(rev, p):
    return ast.parse(subprocess.run(["git", "-C", repo, "cat-file", "blob", f"{rev}:{p}"], capture_output=True, check=True).stdout.decode("utf-8"))
def bound(n):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): return {n.name}
    if isinstance(n, ast.Assign): return {t.id for t in n.targets if isinstance(t, ast.Name)}
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name): return {n.target.id}
    return set()
def binding_map(tree):
    m = {}
    for n in tree.body:
        if isinstance(n, ast.Import):
            for a in n.names: m.setdefault(a.asname or a.name.split(".")[0], ("import", a.name))
        elif isinstance(n, ast.ImportFrom):
            for a in n.names: m.setdefault(a.asname or a.name, ("from", n.module, a.name))
        else:
            for b in bound(n): m.setdefault(b, ("def", type(n).__name__))
    return m
nt, et = load(mg, newp), load(base, engp)
other = []
for n in nt.body:
    if bound(n) & names: continue
    if isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant) and isinstance(n.value.value, str):
        kind = "docstring"
    elif isinstance(n, (ast.Import, ast.ImportFrom)):
        kind = "import:" + ast.unparse(n)
    else:
        kind = "other:" + ast.unparse(n)
    other.append((n.lineno, kind))
# 자유 전역 이름(함수 지역 이름 제외: 인자·대입 대상은 대충 제외 -- Load 이름만 모아 정의 안에서 Store되지 않은 것)
free = set()
for n in nt.body:
    if not (bound(n) & names): continue
    stores = {x.id for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del))}
    args = {a.arg for x in ast.walk(n) if isinstance(x, ast.arguments) for a in x.args + x.kwonlyargs + x.posonlyargs}
    comp = set()
    for x in ast.walk(n):
        if isinstance(x, ast.ExceptHandler) and x.name: comp.add(x.name)
    loads = {x.id for x in ast.walk(n) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
    free |= loads - stores - args - comp
free -= set(dir(builtins))
nm, em = binding_map(nt), binding_map(et)
rows = {f: {"new": nm.get(f), "base_engine": em.get(f)} for f in sorted(free)}
redefined = sorted(b for n in nt.body if not (bound(n) & names) for b in bound(n))
print(json.dumps({"new_file": newp, "other_top_level": other, "free_globals": rows, "redefined_engine_names": redefined}, ensure_ascii=False, indent=1))
