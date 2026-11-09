"""검토 B2·S6 합성 사례에 개정 대상 정의(v3_scope_classify.classify)를 적용한 결과. 결과: C:/g60/out/v3_b2_cases.txt"""
import ast, sys

sys.path.insert(0, "C:/g60/scripts")
import v3_scope_classify as V   # noqa: E402  (import 시 sim_head가 C:/g60/base를 읽는다)

OUT = open("C:/g60/out/v3_b2_cases.txt", "w", encoding="utf-8")


def fn_of(src):
    return next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef))


CASES = {
    "bool default False->True": ("def f(x, strict=False):\n    y = h(x)\n    return g(y, strict)\n", "def f(x, strict=True):\n    y = h(x)\n    return g(y, strict)\n"),
    "str default": ('def f(x, mode="fast"):\n    y = h(x)\n    return g(y, mode)\n', 'def f(x, mode="exact"):\n    y = h(x)\n    return g(y, mode)\n'),
    "None -> []": ("def f(x, acc=None):\n    y = h(x)\n    return g(y, acc)\n", "def f(x, acc=[]):\n    y = h(x)\n    return g(y, acc)\n"),
    "param add(unused)": ("def f(x):\n    y = h(x)\n    return g(y)\n", "def f(x, z=None):\n    y = h(x)\n    return g(y)\n"),
    "param rename": ("def f(x):\n    y = h(x)\n    return g(y)\n", "def f(w):\n    y = h(x)\n    return g(y)\n"),
    "kw-only *": ("def f(x, y):\n    z = h(x)\n    return g(z, y)\n", "def f(x, *, y):\n    z = h(x)\n    return g(z, y)\n"),
    "decorator add": ("def f(x):\n    y = h(x)\n    return g(y)\n", "@functools.lru_cache(maxsize=128)\ndef f(x):\n    y = h(x)\n    return g(y)\n"),
    "delete only(S6)": ("def f(x):\n    if x > 0:\n        x = clamp(x)\n        log(x)\n    return g(x + 1)\n", "def f(x):\n    if x > 0:\n        log(x)\n    return g(x + 1)\n"),
    "delete else(S6)": ("def f(x):\n    if x > 0:\n        y = 1\n    else:\n        y = 2\n    return y * 3\n", "def f(x):\n    if x > 0:\n        y = 1\n    return y * 3\n"),
}
for k, (b, h) in CASES.items():
    rows, info = V.classify(fn_of(b), fn_of(h), h)
    res = {d: [(t["op"], t["path"]) for t in rows if f(t)] for d, f in V.DEFS.items() if d in ("old_N2", "N2a", "N2b")}
    line = "%-26s all=%d | old_N2=%d %s | N2a=%d | N2b=%d %s" % (k, len(rows), len(res["old_N2"]), res["old_N2"], len(res["N2a"]),
                                                               len(res["N2b"]), res["N2b"])
    print(line)
    OUT.write(line + "\n")
OUT.close()
