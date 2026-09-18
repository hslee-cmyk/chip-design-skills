"""V4 (2) '확실한 복사' 검출기 실측 probe (05 design v3.1 §10, review30 R-05·R-06, 사용자 결정 (c)).

규칙: test의 assert 비교에서 피검 함수 호출이 든 쪽(실제값)과 다른 쪽(기대식 X)을 가른다.
양쪽 모두 test 함수 지역 대입을 끝까지 인라인한다. 피검 함수는 return마다 지역 대입을 인라인하고
호출 인자를 매개변수에 결합(기본값 포함)해 E_i를 만든다. 같은 모듈 함수 호출은 재귀 인라인한다.
정규화(덧셈·곱셈 평탄화와 정렬, 정수 거듭제곱 -> 곱, 항등원 0·1 제거, 숫자는 float) 뒤 X와 어떤 E_i가
같으면 FAIL. 상수 접기는 하지 않는다(접으면 올바른 리터럴 기대값이 전부 FAIL이 된다).
FAIL은 확실한 복사이고 PASS는 독립의 증거가 아니다(알려진 놓침은 case의 known_limit).

부트스트랩 ①에서 이 파일의 규칙 함수를 tools/gates/test_lint.py V4 (2) 구현으로 옮기고 이 probe는 지운다.
"""
import ast
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).with_name("v4.out.txt")


# ---------- 지역 대입 인라인 ----------
class _Sub(ast.NodeTransformer):
    def __init__(self, env):
        self.env = env

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.env:
            return self.env[node.id]
        return node


def _inline(expr, env):
    return _Sub(env).visit(ast.parse(ast.unparse(expr), mode="eval").body)


def _opaque(name):
    return ast.Name(id=f"<opaque:{name}>", ctx=ast.Load())


def _assigned_names(stmts):
    names = set()
    for s in stmts:
        for n in ast.walk(s):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                names.add(n.id)
    return names


def _walk_body(stmts, env, returns):
    """문장을 차례로 걸으며 env를 갱신하고 Return마다 (인라인된 식)을 returns에 넣는다."""
    env = dict(env)
    for s in stmts:
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
            env[s.targets[0].id] = _inline(s.value, env)
        elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.value is not None:
            env[s.target.id] = _inline(s.value, env)
        elif isinstance(s, ast.AugAssign) and isinstance(s.target, ast.Name):
            cur = env.get(s.target.id, ast.Name(id=s.target.id, ctx=ast.Load()))
            env[s.target.id] = ast.BinOp(left=cur, op=s.op, right=_inline(s.value, env))
        elif isinstance(s, ast.Return) and s.value is not None:
            returns.append(_inline(s.value, env))
        elif isinstance(s, ast.If):
            _walk_body(s.body, env, returns)
            _walk_body(s.orelse, env, returns)
            for n in _assigned_names(s.body + s.orelse):
                env[n] = _opaque(n)
        else:
            for n in _assigned_names([s]):
                env[n] = _opaque(n)
            for sub in ast.walk(s):
                if isinstance(sub, ast.Return) and sub.value is not None and sub is not s:
                    returns.append(_inline(sub.value, env))
    return env


def return_variants(fdef):
    returns = []
    _walk_body(fdef.body, {}, returns)
    return returns


# ---------- 인자 결합과 같은 모듈 인라인 ----------
def _bind(fdef, call):
    a = fdef.args
    params = [p.arg for p in a.posonlyargs + a.args]
    defaults = dict(zip(params[len(params) - len(a.defaults):], a.defaults))
    for p, d in zip(a.kwonlyargs, a.kw_defaults):
        params.append(p.arg)
        if d is not None:
            defaults[p.arg] = d
    if any(isinstance(v, ast.Starred) for v in call.args):
        return None
    bound = {}
    for p, v in zip(params, call.args):
        bound[p] = v
    for kw in call.keywords:
        if kw.arg is None:
            return None
        bound[kw.arg] = kw.value
    for p in params:
        if p not in bound:
            if p not in defaults:
                return None
            bound[p] = defaults[p]
    return bound


def _callee(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def expand(expr, module_funcs, stack=()):
    """expr 안의 같은 모듈 함수 호출을 return 변형으로 펼친 식들의 목록."""
    variants = [expr]
    for node in ast.walk(expr):
        if isinstance(node, ast.Call):
            name = _callee(node)
            if name in module_funcs and name not in stack:
                fdef = module_funcs[name]
                bound = _bind(fdef, node)
                if bound is None:
                    continue
                out = []
                for r in return_variants(fdef):
                    body = _inline(r, bound)
                    for b in expand(body, module_funcs, stack + (name,)):
                        for v in variants:
                            out.append(_replace(v, node, b))
                variants = out or variants
                break
    if variants != [expr] and any(v is not expr for v in variants):
        more = []
        for v in variants:
            more.extend(expand(v, module_funcs, stack) if v is not expr else [v])
        return more
    return variants


def _replace(tree, target, repl):
    tdump = ast.dump(target)

    class R(ast.NodeTransformer):
        done = False

        def visit_Call(self, node):
            if not self.done and ast.dump(node) == tdump:
                self.done = True
                return repl
            self.generic_visit(node)
            return node
    return R().visit(ast.parse(ast.unparse(tree), mode="eval").body)


# ---------- 정규화 ----------
def canon(n):
    if isinstance(n, ast.Constant):
        if isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return ("num", float(n.value))
        return ("const", repr(n.value))
    if isinstance(n, ast.Name):
        return ("name", n.id)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.UAdd):
        return canon(n.operand)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        c = canon(n.operand)
        if c[0] == "num":
            return ("num", -c[1])
        return _sum([(-1, c)])
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
        return _sum(_terms(n, 1))
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mult, ast.Div)):
        return _prod(_factors(n, 1))
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
        e = n.right
        ev = None
        if isinstance(e, ast.Constant) and isinstance(e.value, int) and not isinstance(e.value, bool):
            ev = e.value
        elif isinstance(e, ast.UnaryOp) and isinstance(e.op, ast.USub) and isinstance(e.operand, ast.Constant) \
                and isinstance(e.operand.value, int) and not isinstance(e.operand.value, bool):
            ev = -e.operand.value
        if ev:
            sgn = 1 if ev > 0 else -1
            return _prod([(sgn, canon(n.left))] * abs(ev))
        return ("pow", canon(n.left), canon(e))
    if isinstance(n, ast.Call):
        return ("call", canon(n.func), tuple(canon(a) for a in n.args),
                tuple(sorted((k.arg or "**", canon(k.value)) for k in n.keywords)))
    if isinstance(n, ast.Attribute):
        return ("attr", canon(n.value), n.attr)
    return ("dump", ast.dump(n))


def _terms(n, s):
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
        return _terms(n.left, s) + _terms(n.right, s if isinstance(n.op, ast.Add) else -s)
    c = canon(n)
    if c[0] == "sum":
        return [(s * ss, t) for ss, t in c[1]]
    return [(s, c)]


def _sum(terms):
    norm = []
    for s, t in terms:
        if t[0] == "num":
            if t[1] == 0.0:
                continue
            norm.append((1, ("num", s * t[1])))
        else:
            norm.append((s, t))
    if not norm:
        return ("num", 0.0)
    if len(norm) == 1 and norm[0][0] == 1:
        return norm[0][1]
    return ("sum", tuple(sorted(norm, key=repr)))


def _factors(n, e):
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Mult, ast.Div)):
        return _factors(n.left, e) + _factors(n.right, e if isinstance(n.op, ast.Mult) else -e)
    c = canon(n)
    if c[0] == "prod":
        return [(e * ee, f) for ee, f in c[1]]
    return [(e, c)]


def _prod(factors):
    # 부호를 밖으로: 음수 숫자 인자와 단항 마이너스 한 항짜리 합을 양수로 바꾸고 전체 부호로 모은다.
    # 숫자 인자는 곱에 이름·식 인자가 하나라도 있을 때만 계수 하나로 모은다(`x/2` -> `x*0.5`, 나눗셈 정규화).
    # 숫자만의 곱은 모으지 않는다 -- 모으면 상수 접기가 되어 재서술(`2e-3*50e3`)이 리터럴과 구별되지 않는다.
    sign, nums, norm = 1, [], []
    for e, f in factors:
        if f[0] == "sum" and len(f[1]) == 1 and f[1][0][0] == -1:
            sign, f = -sign, f[1][0][1]
        if f[0] == "num":
            v = f[1]
            if v < 0:
                sign, v = -sign, -v
            if v != 1.0:
                nums.append((e, v))
            continue
        norm.append((e, f))
    if norm:
        coef = 1.0
        for e, v in nums:
            coef = coef * v if e > 0 else coef / v
        if coef != 1.0:
            norm.append((1, ("num", coef)))
    else:
        norm = [(e, ("num", v)) for e, v in nums]
    if not norm:
        return ("num", float(sign))
    if len(norm) == 1 and norm[0][0] == 1 and norm[0][1][0] == "num":
        return ("num", sign * norm[0][1][1])
    if len(norm) == 1 and norm[0][0] == 1:
        body = norm[0][1]
    else:
        body = ("prod", tuple(sorted(norm, key=repr)))
    if sign < 0:
        return ("sum", ((-1, body),))
    return body


# ---------- test 쪽 ----------
def _pair_of(t):
    """assert 식 하나에서 비교 쌍 (a, b), 못 만들면 None.
    형태: `abs(a - b) < 또는 <= tol`, `abs((a - b) / c) < 또는 <= tol`, `a == b`(어느 쪽이든 `approx(...)`),
    `isclose(a, b)`(어느 순서든)."""
    if isinstance(t, ast.Compare) and len(t.ops) == 1:
        left, right = t.left, t.comparators[0]
        if isinstance(t.ops[0], (ast.Lt, ast.LtE)) and isinstance(left, ast.Call) and _callee(left) == "abs" and left.args:
            inner = left.args[0]
            if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Div):
                inner = inner.left
            if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Sub):
                return inner.left, inner.right
        if isinstance(t.ops[0], ast.Eq):
            if isinstance(right, ast.Call) and _callee(right) == "approx" and right.args:
                right = right.args[0]
            if isinstance(left, ast.Call) and _callee(left) == "approx" and left.args:
                left = left.args[0]
            return left, right
    if isinstance(t, ast.Call) and _callee(t) == "isclose" and len(t.args) >= 2:
        return t.args[0], t.args[1]
    return None


def _assert_pairs(test):
    """test 본문을 순서대로 걸으며 그 시점의 지역 대입 환경으로 assert마다 (줄, a, b) -- 쌍을 못 만들면 (줄, None, None)."""
    env, out = {}, []
    for s in test.body:
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
            env[s.targets[0].id] = _inline(s.value, env)
        elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.value is not None:
            env[s.target.id] = _inline(s.value, env)
        elif isinstance(s, ast.Assert):
            p = _pair_of(s.test)
            out.append((s.lineno, None, None) if p is None else (s.lineno, _inline(p[0], env), _inline(p[1], env)))
        else:
            for n in _assigned_names([s]):
                env[n] = _opaque(n)
    return out


def _is_leaf(c):
    return c[0] in ("num", "name", "const")


def judge(module_src, test_src, subjects, inline_test=True, inline_subject=True):
    mod = ast.parse(module_src)
    funcs = {f.name: f for f in mod.body if isinstance(f, ast.FunctionDef)}
    test = next(f for f in ast.parse(test_src).body if isinstance(f, ast.FunctionDef))
    if not inline_test:
        test.body = [s for s in test.body if isinstance(s, ast.Assert)]
    results = []
    for lineno, a, b in _assert_pairs(test):
        if a is None:
            results.append((lineno, "UNJUDGED"))
            continue

        def subj_call(x):
            if isinstance(x, ast.Call) and _callee(x) in subjects:
                return x
            return None
        call, x = (subj_call(a), b) if subj_call(a) else (subj_call(b), a)
        if call is None:
            results.append((lineno, "no-subject-call"))
            continue
        fdef = funcs.get(_callee(call))
        bound = _bind(fdef, call) if fdef else None
        if bound is None:
            results.append((lineno, "UNJUDGED"))
            continue
        if inline_subject:
            es = [_inline(r, bound) for r in return_variants(fdef)]
        else:
            es = [_inline(s.value, bound) for s in ast.walk(fdef) if isinstance(s, ast.Return) and s.value is not None]
        e_all = [v for e in es for v in expand(e, funcs, (fdef.name,))]
        x_all = expand(x, {k: v for k, v in funcs.items() if k not in subjects}, ())
        cx = {canon(v) for v in x_all}
        # 잎 하나(매개변수·상수)로 끝나는 return 경로는 비교하지 않는다(review31 N-03: 명세 리터럴 거짓 양성)
        hit = [i for i, e in enumerate(e_all) if not _is_leaf(canon(e)) and canon(e) in cx]
        results.append((lineno, "FAIL" if hit else "PASS"))
    return results


# ---------- 사례 ----------
def e329283_inputs():
    src = subprocess.run(["git", "show", "e329283:skills/analog-gmid-design/assets/sizing_recipe.py"],
                         capture_output=True, check=True).stdout.decode("utf-8")
    lines = src.splitlines()
    start = next(i for i, l in enumerate(lines) if "[7-4b 확장 estimate_area_budget()" in l) + 1
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == "print()")
    body = [l for l in lines[start:end]]
    indent = min(len(l) - len(l.lstrip()) for l in body if l.strip())
    test = "def test_area_budget():\n" + "\n".join("    " + l[indent:] if l.strip() else "" for l in body) + "\n"
    return src, test


def _swap(test, old, new):
    assert old in test, old
    return test.replace(old, new)


def main():
    OUT.write_text("", encoding="utf-8")
    src, test = e329283_inputs()
    subj = {"estimate_area_budget"}
    X0 = "_area_cold_expected = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected"
    cases = [
        ("e329283 실제(§13.3 변환 test)", src, test, subj, "첫 assert FAIL", None),
        ("e329283 교환 재배열", src, _swap(test, X0, "_area_cold_expected = _a1d_demo * (1 - 0.65) + _a2d_cold_expected * 0.65"), subj, "첫 assert FAIL", None),
        ("e329283 1.0* 감싸기", src, _swap(test, X0, "_area_cold_expected = 1.0 * ((1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected)"), subj, "첫 assert FAIL", None),
        ("e329283 손으로 접은 리터럴", src, _swap(test, X0, "_area_cold_expected = 135.0"), subj, "첫 assert PASS", "F1 상수 접기"),
        ("e329283 대수 정리(α 상쇄를 풀어 씀)", src, _swap(test, X0, "_area_cold_expected = (1 - 0.65) * _a1d_demo + _a1d_demo"), subj, "첫 assert PASS", "F2 분배·약분"),
        ("e329283 비교 <=", src, _swap(test, "abs(_area_cold - _area_cold_expected) < 1e-9", "abs(_area_cold - _area_cold_expected) <= 1e-9"), subj, "첫 assert FAIL", None),
        ("e329283 상대 오차", src, _swap(test, "abs(_area_cold - _area_cold_expected) < 1e-9", "abs((_area_cold - _area_cold_expected) / _area_cold_expected) < 1e-9"), subj, "첫 assert FAIL", None),
        ("e329283 approx 왼쪽", src, _swap(test, "abs(_area_cold - _area_cold_expected) < 1e-9", "pytest.approx(_area_cold_expected) == _area_cold"), subj, "첫 assert FAIL", None),
        ("e329283 주석 달린 대입", src, _swap(test, X0, "_area_cold_expected: float = (1 - 0.65) * _a1d_demo + 0.65 * _a2d_cold_expected"), subj, "첫 assert FAIL", None),
        ("e329283 합을 sum()으로", src, _swap(test, X0, "_area_cold_expected = sum([(1 - 0.65) * _a1d_demo, 0.65 * _a2d_cold_expected])"), subj, "첫 assert PASS", "F3 모듈 밖 호출·자료구조"),
    ]
    syn = [
        ("제곱 vov*vov 대 0.2**2", "def ov(vov):\n    return vov * vov\n", "def test_ov():\n    assert ov(0.2) == pytest.approx(0.2 ** 2)\n", {"ov"}, "FAIL", None),
        ("제곱 vov**2 대 0.2*0.2", "def ov(vov):\n    return vov ** 2\n", "def test_ov():\n    assert ov(0.2) == pytest.approx(0.2 * 0.2)\n", {"ov"}, "FAIL", None),
        ("gm*ro 대 2e-3*50e3(재서술)", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("gm*ro 대 리터럴 100.0", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3) == pytest.approx(100.0)\n", {"gain"}, "PASS", None),
        ("병렬 r1*r2/(r1+r2) 대 같은 식", "def par(r1, r2):\n    return r1 * r2 / (r1 + r2)\n", "def test_par():\n    assert par(1e3, 2e3) == pytest.approx(1e3 * 2e3 / (1e3 + 2e3))\n", {"par"}, "FAIL", None),
        ("병렬 대 컨덕턴스 합(다른 폐형식)", "def par(r1, r2):\n    return r1 * r2 / (r1 + r2)\n", "def test_par():\n    assert par(1e3, 2e3) == pytest.approx(1 / (1 / 1e3 + 1 / 2e3))\n", {"par"}, "PASS", None),
        ("같은 모듈 보조 함수 인라인", "def a2d(a1d, alpha):\n    return a1d / alpha\n\ndef area(n, alpha=0.65):\n    a = n * 1.0\n    return (1 - alpha) * a + alpha * a2d(a, alpha)\n", "def test_area():\n    assert area(100) == pytest.approx((1 - 0.65) * 100 + 0.65 * (100 / 0.65))\n", {"area"}, "FAIL", None),
        ("KCL 합 i1+i2 대 10e-6+20e-6", "def itot(i1, i2):\n    return i1 + i2\n", "def test_itot():\n    assert itot(10e-6, 20e-6) == pytest.approx(10e-6 + 20e-6)\n", {"itot"}, "FAIL", None),
        # review31 N-04: 부호·나눗셈 표기와 호출 형태
        ("단항 마이너스 -gm*ro 대 -(2e-3*50e3)", "def g(gm, ro):\n    return -gm * ro\n", "def test_g():\n    assert g(2e-3, 50e3) == pytest.approx(-(2e-3 * 50e3))\n", {"g"}, "FAIL", None),
        ("단항 마이너스 -gm*ro 대 2e-3*(-50e3)", "def g(gm, ro):\n    return -gm * ro\n", "def test_g():\n    assert g(2e-3, 50e3) == pytest.approx(2e-3 * (-50e3))\n", {"g"}, "FAIL", None),
        ("a - b*c 대 -b*c + a", "def h(a, b, c):\n    return a - b * c\n", "def test_h():\n    assert h(1.0, 2.0, 3.0) == pytest.approx(-2.0 * 3.0 + 1.0)\n", {"h"}, "FAIL", None),
        ("x/2 대 x*0.5", "def half(x):\n    return x / 2\n", "def test_half():\n    assert half(y) == pytest.approx(y * 0.5)\n", {"half"}, "FAIL", None),
        ("1/x 대 x**-1", "def inv(x):\n    return 1 / x\n", "def test_inv():\n    assert inv(y) == pytest.approx(y ** -1)\n", {"inv"}, "FAIL", None),
        ("키워드 전용 기본값", "def f(a, *, k=2.0):\n    return a * k\n", "def test_f():\n    assert f(y) == pytest.approx(y * 2.0)\n", {"f"}, "FAIL", None),
        ("**kw 호출(판정 없음, 예외 없음)", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    kw = {'gm': 2e-3, 'ro': 50e3}\n    assert gain(**kw) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("assert 뒤 재대입(데이터 흐름)", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    e = gm0 * ro0\n    assert gain(gm0, ro0) == pytest.approx(e)\n    e = 100.0\n", {"gain"}, "FAIL", None),
        ("튜플 반환", "def gp(a, b):\n    return a * b, a + b\n", "def test_gp():\n    p, s = gp(2.0, 3.0)\n    assert p == pytest.approx(2.0 * 3.0)\n", {"gp"}, "no-subject-call", "F3 튜플 풀기"),
        # review31 N-03: 잎 하나 return 경로의 명세 리터럴
        ("clamp 통과 경로 리터럴", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    assert clamp(5, 0, 10) == 5\n", {"clamp"}, "PASS", None),
        ("clamp 하한 리터럴", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    assert clamp(-3, 0, 10) == 0\n", {"clamp"}, "PASS", None),
        ("area(0) 상수 return", "def area(n):\n    if n == 0:\n        return 0.0\n    return n * 1.5\n", "def test_area():\n    assert area(0) == 0.0\n", {"area"}, "PASS", None),
        ("단위 이득(항등원 뒤 잎 하나)", "def vout(vin, gain=1.0):\n    return vin * gain\n", "def test_vout():\n    assert vout(0.9) == pytest.approx(0.9)\n", {"vout"}, "PASS", None),
    ]
    for name, m, t, s, expect, limit in cases + syn:
        r = judge(m, t, s)
        line = f"{name}: {r} | 기대 {expect}" + (f" | known_limit {limit}" if limit else "")
        with OUT.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line)
    # R-05 네 조합(인라인 여부) -- 실제 e329283
    for it in (False, True):
        for isub in (False, True):
            r = judge(src, test, subj, inline_test=it, inline_subject=isub)
            line = f"e329283 조합 test 인라인={it} 피검 인라인={isub}: {r}"
            with OUT.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            print(line)


if __name__ == "__main__":
    sys.exit(main())
