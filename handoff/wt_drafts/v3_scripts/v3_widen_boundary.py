"""넓힌 T6 경계 확인: 반복문 다음 회차(앞 문장)는 대상, 다른 블록(바깥 블록)은 대상 밖, 속성·메서드 수신자 이름은 대상.
결과: C:/g69/out/v3_widen_boundary.txt"""
import ast, sys

sys.path.insert(0, "C:/g69/scripts")
import v3_scope_widen as W   # noqa: E402
V, mc = W.V, W.mc
OUT = "C:/g69/out/v3_widen_boundary.txt"
open(OUT, "w").close()


def fn_of(src):
    return next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef))


CASES = {
    "loop-carried(앞 문장, 반복문 본문)": ("def f(xs):\n    acc = 0\n    out = []\n    for x in xs:\n        out.append(acc - 1)\n        acc = x + 1\n    return out\n",
                                    "def f(xs):\n    acc = 0\n    out = []\n    for x in xs:\n        out.append(acc - 1)\n        acc = x + 2\n    return out\n"),
    "cross-block(if 안 변경 -> 바깥 return)": ("def f(x):\n    y = 0\n    if x > 0:\n        y = x * 2\n    return y + 1\n",
                                         "def f(x):\n    y = 0\n    if x > 0:\n        y = x * 3\n    return y + 1\n"),
    "attr(self.mode = ... -> 뒤 if self.mode)": ("def f(self, x):\n    self.mode = 1\n    log(x)\n    if self.mode > 1:\n        return x\n    return -x\n",
                                            "def f(self, x):\n    self.mode = 2\n    log(x)\n    if self.mode > 1:\n        return x\n    return -x\n"),
    "method(out.append 새 문장 -> 뒤 return len(out) + 1)": ("def f(x):\n    out = []\n    log(x)\n    return len(out) + 1\n",
                                                        "def f(x):\n    out = []\n    out.append(x)\n    log(x)\n    return len(out) + 1\n"),
    "two-step(a = 새 값 -> b = a -> 뒤 if b)": ("def f(x):\n    a = 1\n    b = a\n    log(x)\n    if b > 1:\n        return x\n    return -x\n",
                                          "def f(x):\n    a = 2\n    b = a\n    log(x)\n    if b > 1:\n        return x\n    return -x\n"),
}
for k, (b, h) in CASES.items():
    rows, info = W.classify_w(fn_of(b), fn_of(h), h)
    n2b = [(t["op"], t["path"]) for t in rows if V.DEFS["N2b"](t)]
    n2w = [(t["op"], t["path"]) for t in rows if V.DEFS["N2w"](t)]
    out = [(t["op"], t["path"]) for t in rows if not V.DEFS["N2w"](t)]
    line = "%s\n   all=%d N2b=%d N2w=%d\n   N2w 대상=%s\n   N2w 대상 밖=%s" % (k, len(rows), len(n2b), len(n2w), n2w, out)
    print(line)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
