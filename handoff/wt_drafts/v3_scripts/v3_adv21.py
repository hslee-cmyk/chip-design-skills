"""2차 검토(review2_v3_cards.md §2·§6) 적대적 동작 변경 21건을 다시 만들어, 지금 규칙(def 전체)·N2b(승인 당시 N2)·N2w(T6 넓힌 판)로 잰다.
(검토 scratch C:/g65는 지워져 사례 소스를 표 설명대로 다시 썼다 -- 변이 수는 검토 수치와 다를 수 있고, 판단 대상은 '분류'(weak 판정·변경 고유 변이)다.)

사례마다 base·head 모듈 소스, weak test(base·head 모두 통과 -- 변경을 관찰하지 않음), strong test(base 실패·head 통과).
변이는 도구 mutate_changed.mutants(읽기 전용 import)로 만들고, 계약 9 판(첫 데코레이터 줄부터 unparse) 치환으로 소스를 바꿔 exec, test 함수를 부른다(예외 = 죽음).
'weak 판정' = 그 정의의 대상 변이를 weak 하나가 모두 죽이면 PASS. '변경 고유' = weak은 못 죽이고 strong만 죽이는 대상 변이 수.
결과: C:/g69/out/v3_adv21.txt (사례마다 append)
"""
import ast, copy, sys, textwrap

sys.path.insert(0, "C:/g69/scripts")
import v3_scope_widen as W   # noqa: E402
V, mc, rch = W.V, W.mc, W.rch

OUT = "C:/g69/out/v3_adv21.txt"


def log(s):
    print(s)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(s + "\n")


PRE = textwrap.dedent('''
    import functools
    LOG = []
    REG = {}
    THRESH = %s
    def register(name):
        def d(fn):
            REG[name] = fn
            return fn
        return d
    def ha(x):
        return x * 2
    def hb(x):
        return x * 2 if x >= 0 else 0
    helper = %s
    def scaled(y, scale=1):
        return y * scale
    def rounded(y, exact=False):
        return y if exact else round(y)
''')


def mod(body, thresh="5", helper="ha"):
    return PRE % (thresh, helper) + textwrap.dedent(body)


def raises(fn, exc=Exception):
    try:
        fn()
    except exc:
        return
    raise AssertionError("no raise")


CASES = []


def case(cid, desc, base, head, weak, strong, bkw=None, hkw=None):
    CASES.append((cid, desc, mod(base, **(bkw or {})), mod(head, **(hkw or {})), weak, strong))


case("1a", "**kw 전달 bool 기본값 exact=False->True",
     "def f(x, exact=False, **kw):\n    y = x * 2\n    return rounded(y, exact=exact, **kw)\n",
     "def f(x, exact=True, **kw):\n    y = x * 2\n    return rounded(y, exact=exact, **kw)\n",
     lambda m: (m["f"](1.0) == 2 and m["f"](3.0) == 6) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](1.25) == 2.5 or (_ for _ in ()).throw(AssertionError()))
case("1b", "**kw 전달 int 기본값 scale=2->3",
     "def f(x, scale=2, **kw):\n    y = x + 1\n    return scaled(y, scale=scale, **kw)\n",
     "def f(x, scale=3, **kw):\n    y = x + 1\n    return scaled(y, scale=scale, **kw)\n",
     lambda m: m["f"](1, scale=5) == 10 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](1) == 6 or (_ for _ in ()).throw(AssertionError()))
case("1c", "bool 기본값 -> 별칭 s = strict -> 바뀌지 않은 if s and x < 0",
     "def f(x, strict=False):\n    s = strict\n    y = x * 2\n    if s and x < 0:\n        raise ValueError(x)\n    return y\n",
     "def f(x, strict=True):\n    s = strict\n    y = x * 2\n    if s and x < 0:\n        raise ValueError(x)\n    return y\n",
     lambda m: (m["f"](3) == 6 and m["f"](0) == 0) or (_ for _ in ()).throw(AssertionError()),
     lambda m: raises(lambda: m["f"](-1), ValueError))
case("2", "모듈 수준 상수 THRESH 5->6(바뀌지 않은 def가 읽음)",
     "def f(x):\n    return x > THRESH\n", "def f(x):\n    return x > THRESH\n",
     lambda m: (m["f"](100) is True and m["f"](0) is False) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](6) is False or (_ for _ in ()).throw(AssertionError()),
     bkw={"thresh": "5"}, hkw={"thresh": "6"})
case("3a", "문장 안 helper 이름 ha(x)->hb(x)",
     "def f(x):\n    y = ha(x)\n    return y + 1\n", "def f(x):\n    y = hb(x)\n    return y + 1\n",
     lambda m: m["f"](1) == 3 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](-1) == 1 or (_ for _ in ()).throw(AssertionError()))
case("3b", "모듈 수준 helper = ha -> hb",
     "def f(x):\n    return helper(x) + 1\n", "def f(x):\n    return helper(x) + 1\n",
     lambda m: m["f"](1) == 3 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](-1) == 1 or (_ for _ in ()).throw(AssertionError()),
     bkw={"helper": "ha"}, hkw={"helper": "hb"})
case("4a", "문장 안 lambda r[0] -> -r[0]",
     "def f(rows):\n    s = sorted(rows, key=lambda r: r[0])\n    return s[0][1]\n",
     "def f(rows):\n    s = sorted(rows, key=lambda r: -r[0])\n    return s[0][1]\n",
     lambda m: m["f"]([(1, 'a')]) == 'a' or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"]([(1, 'a'), (2, 'b')]) == 'b' or (_ for _ in ()).throw(AssertionError()))
case("4b", "기본값 lambda key=lambda r: r[0] -> -r[0]",
     "def f(rows, key=lambda r: r[0]):\n    s = sorted(rows, key=key)\n    return s[0][1]\n",
     "def f(rows, key=lambda r: -r[0]):\n    s = sorted(rows, key=key)\n    return s[0][1]\n",
     lambda m: m["f"]([(1, 'a')]) == 'a' or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"]([(1, 'a'), (2, 'b')]) == 'b' or (_ for _ in ()).throw(AssertionError()))
case("5", "컴프리헨션 필터 v > 0 -> v >= 0",
     "def f(xs):\n    vals = [v for v in xs if v > 0]\n    return sum(vals) + len(vals)\n",
     "def f(xs):\n    vals = [v for v in xs if v >= 0]\n    return sum(vals) + len(vals)\n",
     lambda m: m["f"]([1, 2]) == 5 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"]([0, 1]) == 3 or (_ for _ in ()).throw(AssertionError()))
case("6", "문장 순서 바꾸기",
     "def f(x):\n    x = x + 1\n    x = x * 2\n    return x\n", "def f(x):\n    x = x * 2\n    x = x + 1\n    return x\n",
     lambda m: isinstance(m["f"](1), int) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](0) == 1 or (_ for _ in ()).throw(AssertionError()))
case("7", "raise ValueError -> KeyError",
     "def f(x):\n    if x < 0:\n        raise ValueError(x)\n    return x\n", "def f(x):\n    if x < 0:\n        raise KeyError(x)\n    return x\n",
     lambda m: (m["f"](1) == 1 and m["f"](0) == 0 and raises(lambda: m["f"](-1)) is None) or (_ for _ in ()).throw(AssertionError()),
     lambda m: raises(lambda: m["f"](-1), KeyError))
case("8", "반환식 피연산자만 a + b -> a + c",
     "def f(a, b, c):\n    return a + b\n", "def f(a, b, c):\n    return a + c\n",
     lambda m: m["f"](1, 2, 2) == 3 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](1, 2, 5) == 6 or (_ for _ in ()).throw(AssertionError()))
case("9", "dict 리터럴 키 'gain' -> 'gm'",
     "def f(x):\n    d = {'gain': x * 2}\n    return d\n", "def f(x):\n    d = {'gm': x * 2}\n    return d\n",
     lambda m: list(m["f"](1).values()) == [2] or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](1) == {'gm': 2} or (_ for _ in ()).throw(AssertionError()))
case("10a", "데코레이터 인자 maxsize=128->1",
     "@functools.lru_cache(maxsize=128)\ndef f(x):\n    return x * 2\n", "@functools.lru_cache(maxsize=1)\ndef f(x):\n    return x * 2\n",
     lambda m: m["f"](2) == 4 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"].cache_info().maxsize == 1 or (_ for _ in ()).throw(AssertionError()))
case("10b", "데코레이터 문자열 인자 @register('a') -> ('b')",
     "@register('a')\ndef f(x):\n    return x * 2\n", "@register('b')\ndef f(x):\n    return x * 2\n",
     lambda m: m["f"](2) == 4 or (_ for _ in ()).throw(AssertionError()),
     lambda m: 'b' in m["REG"] or (_ for _ in ()).throw(AssertionError()))
case("11", "mode = 'fast'->'exact', 한 문장 건너 같은 블록의 if mode == 'exact'",
     "def f(x):\n    mode = 'fast'\n    LOG.append(x)\n    if mode == 'exact':\n        return x * 2 + 1\n    return x * 2\n",
     "def f(x):\n    mode = 'exact'\n    LOG.append(x)\n    if mode == 'exact':\n        return x * 2 + 1\n    return x * 2\n",
     lambda m: (lambda n: (m["f"](1) in (2, 3) and m["f"](2) in (4, 5) and len(m["LOG"]) == n + 2))(len(m["LOG"])) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](1) == 3 or (_ for _ in ()).throw(AssertionError()))
case("11b", "11과 같되 사용하는 if가 바로 뒤 문장",
     "def f(x):\n    mode = 'fast'\n    if mode == 'exact':\n        return x * 2 + 1\n    LOG.append(x)\n    return x * 2\n",
     "def f(x):\n    mode = 'exact'\n    if mode == 'exact':\n        return x * 2 + 1\n    LOG.append(x)\n    return x * 2\n",
     lambda m: (m["f"](1) in (2, 3) and m["f"](2) in (4, 5)) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](1) == 3 or (_ for _ in ()).throw(AssertionError()))
case("12", "문장 삽입 y = max(y, 0)",
     "def f(x):\n    y = x - 1\n    return y * 2\n", "def f(x):\n    y = x - 1\n    y = max(y, 0)\n    return y * 2\n",
     lambda m: m["f"](3) == 4 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](0) == 0 or (_ for _ in ()).throw(AssertionError()))
case("13", "elif x > 5 -> x > 6",
     "def f(x):\n    if x < 0:\n        return -1\n    elif x > 5:\n        return 2\n    return 1\n",
     "def f(x):\n    if x < 0:\n        return -1\n    elif x > 6:\n        return 2\n    return 1\n",
     lambda m: (m["f"](-3) == -1 and m["f"](10) == 2 and m["f"](1) == 1) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](6) == 1 or (_ for _ in ()).throw(AssertionError()))
case("14", "neg = False->True, 두 문장 뒤 같은 블록 if neg:",
     "def f(x):\n    neg = False\n    y = abs(x)\n    LOG.append(y)\n    if neg:\n        y = -y\n    return y\n",
     "def f(x):\n    neg = True\n    y = abs(x)\n    LOG.append(y)\n    if neg:\n        y = -y\n    return y\n",
     lambda m: (lambda n: (abs(m["f"](3)) == 3 and abs(m["f"](-2)) == 2 and len(m["LOG"]) == n + 2))(len(m["LOG"])) or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](3) == -3 or (_ for _ in ()).throw(AssertionError()))
case("15", "else 절 통째 삭제(뒤의 return y * 3이 영향)",
     "def f(x):\n    y = 0\n    if x > 0:\n        y = 1\n    else:\n        y = 2\n    return y * 3\n",
     "def f(x):\n    y = 0\n    if x > 0:\n        y = 1\n    return y * 3\n",
     lambda m: m["f"](1) == 3 or (_ for _ in ()).throw(AssertionError()),
     lambda m: m["f"](-1) == 0 or (_ for _ in ()).throw(AssertionError()))


def replace_def_with_deco(src, fn, new_fn):
    lines = src.split("\n")
    start = min([fn.lineno] + [d.lineno for d in fn.decorator_list]) - 1
    end = fn.end_lineno
    ind = len(lines[start]) - len(lines[start].lstrip())
    text = ast.unparse(ast.fix_missing_locations(copy.deepcopy(new_fn)))
    new = [(" " * ind + l) if l.strip() else l for l in text.split("\n")]
    return "\n".join(lines[:start] + new + lines[end:])


def passes(src, test):
    ns = {"__name__": "adv"}
    try:
        exec(compile(src, "<adv>", "exec"), ns)
        r = test(ns)
        return r is not False
    except BaseException:
        return False


def run_case(cid, desc, bsrc, hsrc, weak, strong):
    ok = passes(bsrc, weak) and passes(hsrc, weak) and (not passes(bsrc, strong)) and passes(hsrc, strong)
    assert ok, ("sanity", cid, passes(bsrc, weak), passes(hsrc, weak), passes(bsrc, strong), passes(hsrc, strong))
    bdefs = dict(rch.iter_defs(ast.parse(bsrc)))
    res = {k: [0, 0, 0] for k in ("now", "N2b", "N2w")}   # 대상, weak 생존, 변경 고유
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        if q in bdefs:
            rows, _info = W.classify_w(bdefs[q], hfn, hsrc)
        else:
            rows = [dict(op=o, path=p, newdef=True) for o, p, _ in mc.mutants(hfn, hsrc)]
        ms = mc.mutants(hfn, hsrc)
        assert [(o, p) for o, p, _ in ms] == [(t["op"], t["path"]) for t in rows]
        for t, (o, p, mfn) in zip(rows, ms):
            msrc = replace_def_with_deco(hsrc, hfn, mfn)
            wk = not passes(msrc, weak)
            sk = not passes(msrc, strong)
            sel = {"now": True,
                   "N2b": t.get("newdef") or V.DEFS["N2b"](t),
                   "N2w": t.get("newdef") or V.DEFS["N2w"](t)}
            for k, s in sel.items():
                if s:
                    res[k][0] += 1
                    res[k][1] += (not wk)
                    res[k][2] += (sk and not wk)
    cell = lambda k: "%d / %s / %d" % (res[k][0], "PASS" if res[k][1] == 0 else "FAIL(weak 생존 %d)" % res[k][1], res[k][2])
    log("| %s | %s | %s | %s | %s |" % (cid, desc, cell("now"), cell("N2b"), cell("N2w")))
    return res


if __name__ == "__main__":
    open(OUT, "w").close()
    log("| # | 동작 변경 | 지금(def 전체) 대상 / weak 판정 / 변경 고유 | N2b(승인 당시) | N2w(T6 넓힌 판) |")
    log("|---|---|---|---|---|")
    tot = {k: 0 for k in ("now", "N2b", "N2w")}
    for c in CASES:
        r = run_case(*c)
        for k in tot:
            tot[k] += r[k][0]
    log("합계 대상: " + ", ".join("%s=%d" % kv for kv in tot.items()))
