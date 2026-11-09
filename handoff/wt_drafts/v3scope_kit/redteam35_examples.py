"""redteam 35(범위 card 계약 8 (a)~(k)) 구성 예가 계약대로 판별되는지 -- 프로세스 안 모의(참고용, 판정 근거 아님).

각 단계: base·head 모듈 소스(rt_engine), test 함수(관찰). 변이 = 복제본 도구 `mutants`(0f23786 판), 치환 = 계약 9 판(첫 데코레이터 줄부터 unparse),
'죽음' = 변이 소스를 exec하고 test가 예외. 대상 = scope_proto.select(N2w). 확인:
  * head(변이 없음)에서 test 통과(기준 실행)
  * 이 card(N2w): 대상 변이 중 생존 = 기대(attack [X] / control []), 대상 밖 id 목록
  * 규칙을 빠뜨린 구현(N2b = T6 나 없음, 또는 단계가 겨냥한 규칙을 끈 판)에서 X가 대상 밖이 되는가(판별력)
  * 지금 도구 모사(def 전체 대상 + 데코레이터 변이 NOOP): 생존 여부(red 주장 확인)
결과: <KIT>/out/redteam35_examples.txt
"""
import ast, copy, sys, textwrap

KIT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3scope_kit"
sys.path.insert(0, KIT)
sys.path.insert(0, "C:/g109/repo/tools/gates")
import mutate_changed as mc   # noqa: E402
import reachability as rch     # noqa: E402
import scope_proto as SP       # noqa: E402

OUT = KIT + "/out/redteam35_examples.txt"
PRE = '"""rt."""\nimport functools\n\nLOG = []\n\n\ndef rt_gain(gm, ro):\n    """이득."""\n    return gm * ro\n\n\n'


def M(body):
    return PRE + textwrap.dedent(body).lstrip("\n")


def replace_new(src, fn, new_fn):
    lines = src.split("\n")
    start = min([fn.lineno] + [d.lineno for d in fn.decorator_list]) - 1
    ind = len(lines[start]) - len(lines[start].lstrip())
    text = ast.unparse(ast.fix_missing_locations(copy.deepcopy(new_fn)))
    return "\n".join(lines[:start] + [(" " * ind + l) if l.strip() else l for l in text.split("\n")] + lines[fn.end_lineno:])


def passes(src, test):
    ns = {"__name__": "rt_engine"}
    try:
        exec(compile(src, "rt_engine.py", "exec"), ns)
        test(ns)
        return True
    except BaseException:
        return False


def T(cond):
    if not cond:
        raise AssertionError
    return True


STEPS = []


def step(name, kind, base, head, test, x=None, note="", no_inventory=False):
    STEPS.append((name, kind, M(base), M(head), test, x, note, no_inventory))


step("(a) unchanged-stmt-survivor", "control",
     """
     def rt_calc(x):
         LOG.append(x * 3)
         t = x + 1
         return t
     """,
     """
     def rt_calc(x):
         LOG.append(x * 3)
         t = x + 2
         return t
     """,
     lambda m: T(m["rt_calc"](1) == 3 and m["rt_calc"](-4) == -2),
     note="S = LOG.append(x * 3)(C 앞, C가 바꾸는 t를 읽지 않음) -- test는 LOG를 보지 않는다")
step("(b) changed-stmt-survivor", "attack",
     """
     def rt_b(x):
         t = x + 1
         return t
     """,
     """
     def rt_b(x):
         t = x + 1
         LOG.append(t)
         return t
     """,
     lambda m: T(m["rt_b"](1) == 2),
     x="stmt_delete:body[1]", note="X = 새 문장 LOG.append(t)의 stmt_delete(test는 LOG를 보지 않는다)")
step("(c) enclosing-guard-survivor", "attack",
     """
     def rt_c(a, b):
         r = 0
         if a < b or True:
             r = a + 1
         return r
     """,
     """
     def rt_c(a, b):
         r = 0
         if a < b or True:
             r = a + 2
         return r
     """,
     lambda m: T(m["rt_c"](1, 5) == 3 and m["rt_c"](5, 1) == 7),
     x="cmp_flip:body[1].test.values[0].ops[0]", note="X = 감싸는 if의 a < b 뒤집기(`or True`로 등가 -- 도구에 진리값 부정 연산자가 없어 이 꼴)")
step("(d) unwrapped-stmt", "attack",
     """
     def rt_d(x):
         y = x + 1
         if x > -1000:
             LOG.append(y)
         return y
     """,
     """
     def rt_d(x):
         y = x + 1
         LOG.append(y)
         return y
     """,
     lambda m: T(m["rt_d"](1) == 2),
     x="stmt_delete:body[1]", note="X = 감싸던 if를 없애 내어쓴 LOG.append(y)의 stmt_delete")
step("(e) header-only-change", "attack",
     """
     def rt_e(xs):
         out = []
         for v in [w for w in xs if w > -3]:
             out.append(v * 2)
         return out
     """,
     """
     def rt_e(xs):
         out = []
         for v in [w for w in xs if w > -1]:
             out.append(v * 2)
         return out
     """,
     lambda m: T(m["rt_e"]([0, 1, 2]) == [0, 2, 4]),
     x="const+:body[1].iter.generators[0].ifs[0].comparators[0].operand",
     note="X = for 머리 -1(UnaryOp(-, 1))의 피연산자 const+(-2 -- 0 이상 입력에서 같음). 본문 불변")
step("(f) header-default-bool", "attack",
     """
     def rt_f(x, strict=False):
         if strict:
             raise ValueError(x)
         return x
     """,
     """
     def rt_f(x, strict=True):
         if strict:
             raise ValueError(x)
         return x
     """,
     lambda m: True, no_inventory=True,
     note="test 없음(인벤토리 0) -- 대상 변이 전부 생존. 대상 = strict를 읽는 if의 몫(stmt_delete) + early_return")
step("(g) delete-then-use", "attack",
     """
     def rt_g(x):
         LOG.append(x)
         x = abs(x)
         return str(x)
     """,
     """
     def rt_g(x):
         LOG.append(x)
         return str(x)
     """,
     lambda m: T((lambda n: (m["rt_g"](3), len(m["LOG"]) == n + 1)[1])(len(m["LOG"]))),
     x="stmt_delete:body[1]", note="X = 지운 자리 바로 뒤 return의 stmt_delete(test는 반환값을 보지 않고 LOG만 본다 -- early_return은 죽는다)")
step("(h) decorator-mutant-applied", "control",
     """
     def rt_h(x):
         return x * 2
     """,
     """
     @functools.lru_cache(maxsize=128)
     def rt_h(x):
         return x * 2
     """,
     lambda m: T(m["rt_h"].cache_info().maxsize == 128 and m["rt_h"](3) == 6),
     note="데코레이터 상수 ±1(T3 자기 필드)이 계약 9 판으로 실제 적용되어 죽는다. 지금 도구는 NOOP")
step("(i) same-block-later-use", "attack",
     """
     def rt_i(x):
         mode = "fast"
         LOG.append(x)
         if mode == "exact":
             r = x * 2 + 1
         else:
             r = x * 2 + 1
         return r
     """,
     """
     def rt_i(x):
         mode = "exact"
         LOG.append(x)
         if mode == "exact":
             r = x * 2 + 1
         else:
             r = x * 2 + 1
         return r
     """,
     lambda m: T((lambda n: (m["rt_i"](3) == 7, len(m["LOG"]) == n + 1)[1])(len(m["LOG"])) and m["rt_i"](3) == 7),
     x="cmp_flip:body[2].test.ops[0]", note="X = 한 문장 건너 if mode == 'exact'의 뒤집기(두 가지가 같은 값 -- 등가). if 삭제는 r 미정의로 죽는다")
step("(j) loop-carried-use", "attack",
     """
     def rt_j(xs):
         out = []
         acc = 0
         for x in xs:
             LOG.append(acc)
             out.append(acc)
             acc = x + 1
         return out
     """,
     """
     def rt_j(xs):
         out = []
         acc = 0
         for x in xs:
             LOG.append(acc)
             out.append(acc)
             acc = x + 2
         return out
     """,
     lambda m: T(m["rt_j"]([1, 5]) == [0, 3]),
     x="stmt_delete:body[2].body[0]", note="X = 반복문 본문 앞쪽 LOG.append(acc)의 stmt_delete(다음 회차로 흐름, test는 LOG를 보지 않는다)")
step("(k) cross-block-not-targeted", "control",
     """
     def rt_k(x):
         y = 0
         if x > 0:
             y = x * 2
             LOG.append(y)
         return y + 1
     """,
     """
     def rt_k(x):
         y = 0
         if x > 0:
             y = x * 3
             LOG.append(y)
         return y + 1
     """,
     lambda m: T((lambda n: (m["rt_k"](1), m["rt_k"](-0.5), m["rt_k"](0.5), m["LOG"][n:] == [3, 1.5])[3])(len(m["LOG"]))),
     note="Y = 바깥 블록 return y + 1의 변이(test는 LOG만 본다 -- 지금 도구에서는 생존). 이 card에서는 대상 밖")


def run(name, kind, bsrc, hsrc, test, x, note, no_inv):
    log = ["== %s [%s] %s" % (name, kind, note)]
    assert passes(hsrc, test), (name, "head 기준 실행 실패")
    bdefs = dict(rch.iter_defs(ast.parse(bsrc)))
    for q, hfn in mc.changed_defs(bsrc, hsrc):
        ms = mc.mutants(hfn, hsrc)
        new = q not in bdefs
        w = [True] * len(ms) if new else SP.select(bdefs[q], hfn, ms, "N2w")
        b = [True] * len(ms) if new else SP.select(bdefs[q], hfn, ms, "N2b")
        rows = []
        for (o, p, mfn), sw, sb in zip(ms, w, b):
            if no_inv:
                killed = False
            else:
                killed = not passes(replace_new(hsrc, hfn, mfn), test)
            noop = (o.startswith("const") and p.startswith("decorator_list"))
            killed_now = False if no_inv else (killed and not noop)
            rows.append(("%s:%s" % (o, p), sw, sb, killed, killed_now))
        surv = [r[0] for r in rows if r[1] and not r[3]]
        notg = sorted(r[0] for r in rows if not r[1])
        surv_now = [r[0] for r in rows if not r[4]]
        log.append("  %s: 변이 %d, 대상 %d, 대상 밖 %d" % (q, len(rows), sum(r[1] for r in rows), len(notg)))
        log.append("  이 card 생존(대상 중): %s -> exit %d" % (surv, 1 if surv else 0))
        log.append("  대상 밖 id: %s" % notg)
        log.append("  지금 도구 모사(def 전체, 데코레이터 NOOP) 생존: %s -> exit %d" % (surv_now, 1 if surv_now else 0))
        if x:
            xr = [r for r in rows if r[0] == x]
            assert xr, (name, "X 없음", x, [r[0] for r in rows])
            log.append("  X=%s  N2w 대상=%s  N2b 대상=%s" % (x, xr[0][1], xr[0][2]))
            ok = surv == [x] if kind == "attack" else True
        else:
            ok = (surv == []) if kind == "control" else bool(surv)
        if kind == "control":
            ok = ok and surv == []
        log.append("  판정: %s" % ("기대대로" if ok else "**기대와 다름**"))
    return log


if __name__ == "__main__":
    allv = []
    for s in STEPS:
        lg = run(*s)
        allv += lg
        print("\n".join(lg), flush=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(allv) + "\n")
