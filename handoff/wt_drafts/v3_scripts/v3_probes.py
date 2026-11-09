"""검토 review_v3_cards B1·B2·S4 재현과 개정 정의 확인(도구 함수 읽기 전용 import, main 미실행).
결과: C:/g60/out/v3_probes.txt"""
import ast, hashlib, inspect, sys

sys.path.insert(0, "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/tools/gates")
import mutate_changed as mc   # noqa: E402

OUT = open("C:/g60/out/v3_probes.txt", "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.write(s + "\n")


def fn_of(src, name="f"):
    t = ast.parse(src)
    return next(n for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name == name)


def bind_hash(fn):
    """개정 card의 '묶기 해시': docstring을 지우지 않은 def 노드, 인자를 모두 명시."""
    return hashlib.sha256(ast.dump(fn, annotate_fields=True, include_attributes=False, indent=None,
                                   show_empty=False).encode("utf-8")).hexdigest()


log("python", sys.version.split()[0], "| ast.dump signature:", str(inspect.signature(ast.dump)))

# B1: docstring 한 줄이 경로를 민다
A = "def f(x):\n    y = clamp(x)\n    log(y)\n    return y\n"
B = 'def f(x):\n    """doc."""\n    y = clamp(x)\n    log(y)\n    return y\n'
fa, fb = fn_of(A), fn_of(B)
log("[B1] def_hash(①, docstring 제외) equal:", mc.def_hash(fa) == mc.def_hash(fb))
log("[B1] 묶기 해시(docstring 포함) equal:", bind_hash(fa) == bind_hash(fb))
for k in (1, 2):
    p = "body[%d]" % k
    log("[B1] stmt_delete:%s | A: %s | B: %s" % (p, ast.unparse(mc._get(fa, p)), ast.unparse(mc._get(fb, p))))
ma = {(o, p) for o, p, _ in mc.mutants(fa, A)}
mb = {(o, p) for o, p, _ in mc.mutants(fb, B)}
log("[B1] 같은 id 집합 교집합:", sorted(ma & mb))

# B2: def 머리만 바꾼 변경의 '자기 필드' 변이 수(옛 T3)
cases = {
    "bool default False->True": ("def f(x, strict=False):\n    return g(x, strict)\n", "def f(x, strict=True):\n    return g(x, strict)\n"),
    "str default": ('def f(x, mode="fast"):\n    return g(x, mode)\n', 'def f(x, mode="exact"):\n    return g(x, mode)\n'),
    "None -> []": ("def f(x, acc=None):\n    return g(x, acc)\n", "def f(x, acc=[]):\n    return g(x, acc)\n"),
    "param add": ("def f(x):\n    return g(x)\n", "def f(x, y=None):\n    return g(x)\n"),
    "param rename": ("def f(x):\n    return g(x)\n", "def f(z):\n    return g(x)\n"),
    "kw-only *": ("def f(x, y):\n    return g(x, y)\n", "def f(x, *, y):\n    return g(x, y)\n"),
    "decorator add": ("def f(x):\n    return g(x)\n", "@functools.lru_cache(maxsize=128)\ndef f(x):\n    return g(x)\n"),
}
for k, (b, h) in cases.items():
    fh = fn_of(h)
    ms = mc.mutants(fh, h)
    own = [(o, p) for o, p, _ in ms if p and p.split(".")[0].split("[")[0] not in ("body",) and o != "early_return"]
    log("[B2] %-26s 해시 다름=%s  def 자기 필드 변이(옛 T3)=%d  전체 변이=%d %s" % (
        k, mc.def_hash(fn_of(b)) != mc.def_hash(fh), len(own), len(ms), [o for o, _p, _m in ms]))

# B2: 데코레이터 변이 NOOP(_replace_def가 데코레이터 줄을 그대로 둔다)
src = "import functools\n\n\n@functools.lru_cache(maxsize=128)\ndef f(x):\n    return x + 1\n"
fn = fn_of(src)
for o, p, m in mc.mutants(fn, src):
    new = mc._replace_def(src, fn, m)
    same = ast.dump(ast.parse(new)) == ast.dump(ast.parse(src))
    log("[B2-deco] %-12s %-40s NOOP=%s" % (o, p, same))


# 개정안: 데코레이터 줄부터 바꾸는 _replace_def(제안 -- card 계약 9)
def replace_def_with_deco(src, fn, new_fn):
    import copy
    lines = src.split("\n")
    start = min([fn.lineno] + [d.lineno for d in fn.decorator_list]) - 1
    end = fn.end_lineno
    ind = len(lines[start]) - len(lines[start].lstrip())
    text = ast.unparse(ast.fix_missing_locations(copy.deepcopy(new_fn)))
    new = [(" " * ind + l) if l.strip() else l for l in text.split("\n")]
    return "\n".join(lines[:start] + new + lines[end:])


for o, p, m in mc.mutants(fn, src):
    new = replace_def_with_deco(src, fn, m)
    same = ast.dump(ast.parse(new)) == ast.dump(ast.parse(src))
    log("[B2-deco 개정] %-12s %-40s NOOP=%s" % (o, p, same))
OUT.close()
