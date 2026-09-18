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
from fractions import Fraction
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


_NESTED_DEF = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


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
            if not isinstance(s, _NESTED_DEF):
                for sub in _walk_no_nested(s):
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
# 숫자는 `Fraction(repr(float))`로 정확히 둔다. 곱의 숫자 인자는 곱하지 않고 정렬한 다중집합으로 두며
# 나눗셈의 숫자 인자만 역수로 바꾼다(`x/2` = `x*0.5`) -- 계수를 부동소수로 곱하면 판정이 곱하는 순서와
# 반올림에 따라 갈린다(review32 M-03). 숫자만의 식도 접지 않는다(재서술 `2e-3*50e3`가 리터럴과 구별된다).
def _num(v):
    f = float(v)
    if f != f or f in (float("inf"), float("-inf")):
        return ("const", repr(f))  # inf·nan은 유리수로 못 둔다(review33 M2-05)
    return ("num", Fraction(repr(f)))


def canon(n):
    if isinstance(n, ast.Constant):
        if isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return _num(n.value)
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
    return [(s, canon(n))]


def _sum(terms):
    norm = []
    for s, t in terms:
        if t[0] == "sum":  # 합 안의 합은 부호를 나눠 펼친다(`-(b + c)` = `-b - c`, review32 FN3)
            norm.extend((s * ss, tt) for ss, tt in t[1])
        elif t[0] == "num":
            if t[1] != 0:
                norm.append((1, ("num", s * t[1])))
        else:
            norm.append((s, t))
    if not norm:
        return ("num", Fraction(0))
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
    sign, norm = 1, []
    for e, f in factors:
        if f[0] == "sum" and len(f[1]) == 1 and f[1][0][0] == -1:
            sign, f = -sign, f[1][0][1]
        if f[0] == "num":
            v = f[1]
            if v < 0:
                sign, v = -sign, -v
            if v == 1:
                continue
            if e < 0 and v != 0:
                e, v = 1, 1 / v
            norm.append((e, ("num", v)))
            continue
        norm.append((e, f))
    if not norm:
        return ("num", Fraction(sign))
    if len(norm) == 1 and norm[0][0] == 1:
        body = norm[0][1]
    else:
        body = ("prod", tuple(sorted(norm, key=repr)))
    if sign < 0:
        return ("num", -body[1]) if body[0] == "num" else ("sum", ((-1, body),))
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


def _is_assert_call(s):
    """판정 함수 호출문: 호출 이름이 `assert`로 시작(`np.testing.assert_allclose`, `self.assertAlmostEqual` 등)."""
    return isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and (_callee(s.value) or "").startswith("assert")


def _has_subject(expr, subjects):
    for n in ast.walk(expr):
        if isinstance(n, ast.Call) and _callee(n) in subjects:
            return True
        if isinstance(n, ast.Name) and n.id.startswith("<opaque-subject:"):
            return True
    return False


_NESTED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def _walk_no_nested(node):
    """ast.walk와 같되 중첩 함수·클래스·lambda 안으로 들어가지 않는다(review33 M2-06)."""
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        for c in ast.iter_child_nodes(n):
            if not isinstance(c, _NESTED):
                stack.append(c)


def _is_judgement(s):
    return isinstance(s, ast.Assert) or _is_assert_call(s)


def _assert_pairs(stmts, subjects, env=None, out=None):
    """본문을 순서대로, 제어 흐름 안까지 재귀로 걸으며 그 시점의 지역 대입 환경으로 판정 문장마다
    (줄, a, b, 피검 걸림) -- 쌍을 못 만들면 a·b는 None. 이름 규칙(review32 M-04, review33 M2-03):
    피검 호출(또는 피검 불투명 이름)을 담은 값·반복 대상에서 나온 이름은 어디서 대입되든 피검 불투명
    (`<opaque-subject:…>`), 그 밖에 루프 변수·블록 안에서 바뀐 이름은 불투명 이름. 중첩 함수·클래스 안의
    판정 문장과 이 함수가 다루지 않는 복합 문장 안의 판정 문장은 쌍 없이 피검 걸림으로 낸다(→ UNJUDGED)."""
    env = {} if env is None else env
    out = [] if out is None else out

    def mark(names, value):
        subj = value is not None and _has_subject(_inline(value, env), subjects)
        for n in names:
            env[n] = ast.Name(id=f"<opaque-subject:{n}>", ctx=ast.Load()) if subj else _opaque(n)

    def block(stmts_, inner):
        _assert_pairs(stmts_, subjects, inner, out)
        return inner

    for s in stmts:
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
            env[s.targets[0].id] = _inline(s.value, env)
        elif isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.value is not None:
            env[s.target.id] = _inline(s.value, env)
        elif isinstance(s, ast.AugAssign) and isinstance(s.target, ast.Name):
            cur = env.get(s.target.id, ast.Name(id=s.target.id, ctx=ast.Load()))
            env[s.target.id] = ast.BinOp(left=cur, op=s.op, right=_inline(s.value, env))
        elif _is_judgement(s):
            if isinstance(s, ast.Assert):
                p, whole = _pair_of(s.test), s.test
            else:
                p = (s.value.args[0], s.value.args[1]) if len(s.value.args) >= 2 else None
                whole = s.value
            if p is None:
                out.append((s.lineno, None, None, _has_subject(_inline(whole, env), subjects)))
            else:
                out.append((s.lineno, _inline(p[0], env), _inline(p[1], env), True))
        elif isinstance(s, (ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.If,
                            ast.Try, ast.TryStar, ast.Match)):
            inner = dict(env)
            if isinstance(s, (ast.For, ast.AsyncFor)):
                subj = _has_subject(_inline(s.iter, env), subjects)
                for n in _assigned_names([s.target]):
                    inner[n] = ast.Name(id=f"<opaque-subject:{n}>", ctx=ast.Load()) if subj else _opaque(n)
            branches = []
            for attr in ("body", "orelse", "finalbody"):
                if getattr(s, attr, None):
                    branches.append(block(getattr(s, attr), dict(inner)))
            for h in getattr(s, "handlers", []) or []:
                branches.append(block(h.body, dict(inner)))
            for c in getattr(s, "cases", []) or []:
                branches.append(block(c.body, dict(inner)))
            for n in _assigned_names([s]):
                subj = any(_has_subject(b[n], subjects) for b in branches if n in b) \
                    or (n in inner and _has_subject(inner[n], subjects))
                env[n] = ast.Name(id=f"<opaque-subject:{n}>", ctx=ast.Load()) if subj else _opaque(n)
        else:
            # 중첩 def·class, 다루지 않는 문장: 안의 판정 문장은 UNJUDGED, 대입된 이름은 값에 피검이 있으면 피검 불투명
            for sub in ast.walk(s):
                if sub is not s and _is_judgement(sub):
                    out.append((sub.lineno, None, None, True))
            mark(_assigned_names([s]), getattr(s, "value", None))
    return out


def _is_leaf(c):
    return c[0] in ("num", "name", "const")


def judge(module_src, test_src, subjects, inline_test=True, inline_subject=True):
    """assert마다 (줄, 판정). 판정: FAIL(확실한 복사) / PASS / UNJUDGED(피검이 걸렸는데 판정 못 함 --
    auditor 대조 대상) / NO-SUBJECT(피검 호출이 없는 assert -- V4 (2) 대상 아님)."""
    mod = ast.parse(module_src)
    funcs = {f.name: f for f in mod.body if isinstance(f, ast.FunctionDef)}
    test = next(f for f in ast.parse(test_src).body if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)))
    body = test.body if inline_test else [s for s in test.body if isinstance(s, ast.Assert)]
    results = []
    for lineno, a, b, hooked in _assert_pairs(body, subjects):
        if a is None:
            # 쌍을 못 만든 판정: 피검이 걸렸으면 UNJUDGED, 아니면 NO-SUBJECT(review33 M2-04)
            results.append((lineno, "UNJUDGED" if hooked else "NO-SUBJECT"))
            continue

        def subj_call(x):
            if isinstance(x, ast.Call) and _callee(x) in subjects:
                return x
            return None
        call, x = (subj_call(a), b) if subj_call(a) else (subj_call(b), a)
        if call is None:
            has = _has_subject(a, subjects) or _has_subject(b, subjects)
            results.append((lineno, "UNJUDGED" if has else "NO-SUBJECT"))
            continue
        fdef = funcs.get(_callee(call))
        bound = _bind(fdef, call) if fdef else None
        if bound is None:
            results.append((lineno, "UNJUDGED"))
            continue
        if inline_subject:
            rs = return_variants(fdef)
        else:
            rs = [s.value for s in ast.walk(fdef) if isinstance(s, ast.Return) and s.value is not None]
        x_all = expand(x, {k: v for k, v in funcs.items() if k not in subjects}, ())
        cx = {canon(v) for v in x_all}
        # 입력을 그대로 돌려주는 경로는 비교하지 않는다(review31 N-03, review32 M-02): 정규형이 잎 하나이거나
        # **그 return 식에 나오는 매개변수**에 결합된 인자 식 하나의 정규형과 같은 E_i(review33 M2-06: 쓰이지
        # 않는 인자로 제외를 맞추지 못하게) -- 그 값과 같은 명세 리터럴·무발동 값을 복사로 볼 수 없다.
        hit = []
        for r in rs:
            used = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)} & set(bound)
            passthrough = {canon(bound[p]) for p in used}
            for e in expand(_inline(r, bound), funcs, (fdef.name,)):
                c = canon(e)
                if not _is_leaf(c) and c not in passthrough and c in cx:
                    hit.append(c)
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
        ("튜플 반환", "def gp(a, b):\n    return a * b, a + b\n", "def test_gp():\n    p, s = gp(2.0, 3.0)\n    assert p == pytest.approx(2.0 * 3.0)\n", {"gp"}, "UNJUDGED", "F3 튜플 풀기"),
        # review31 N-03: 잎 하나 return 경로의 명세 리터럴
        ("clamp 통과 경로 리터럴", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    assert clamp(5, 0, 10) == 5\n", {"clamp"}, "PASS", None),
        ("clamp 하한 리터럴", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    assert clamp(-3, 0, 10) == 0\n", {"clamp"}, "PASS", None),
        ("area(0) 상수 return", "def area(n):\n    if n == 0:\n        return 0.0\n    return n * 1.5\n", "def test_area():\n    assert area(0) == 0.0\n", {"area"}, "PASS", None),
        ("단위 이득(항등원 뒤 잎 하나)", "def vout(vin, gain=1.0):\n    return vin * gain\n", "def test_vout():\n    assert vout(0.9) == pytest.approx(0.9)\n", {"vout"}, "PASS", None),
        # review32 M-02: 인자가 식인 통과 경로
        ("clamp 통과 경로, 인자가 식(무발동 값)", "def clamp(x, lo, hi):\n    if x < lo:\n        return lo\n    if x > hi:\n        return hi\n    return x\n", "def test_clamp():\n    vdd = 1.8\n    vin = 0.5 * vdd\n    assert clamp(vin, 0.0, vdd) == pytest.approx(vin)\n", {"clamp"}, "PASS", None),
        ("단위 이득, 인자가 식", "def vout(vin, gain=1.0):\n    return vin * gain\n", "def test_vout():\n    vin = 0.5 * 1.8\n    assert vout(vin) == pytest.approx(vin)\n", {"vout"}, "PASS", None),
        ("항등 함수, 인자가 식", "def buf(x):\n    return x\n", "def test_buf():\n    assert buf(2.0 * 3.0) == pytest.approx(2.0 * 3.0)\n", {"buf"}, "PASS", None),
        # review32 M-03: 숫자 인자 다중집합
        ("교환 재배열 a*b*c*x 대 x*c*b*a", "def f(x, a, b, c):\n    return a * b * c * x\n", "def test_f():\n    assert f(y, 0.1, 0.2, 0.3) == pytest.approx(y * 0.3 * 0.2 * 0.1)\n", {"f"}, "FAIL", None),
        ("숫자만의 3.0/2 대 3.0*0.5", "def half(x):\n    return x / 2\n", "def test_half():\n    assert half(3.0) == pytest.approx(3.0 * 0.5)\n", {"half"}, "FAIL", None),
        ("손으로 접은 계수 6.0*y", "def f(x, k1=2.0, k2=3.0):\n    return x * k1 * k2\n", "def test_f():\n    assert f(y) == pytest.approx(6.0 * y)\n", {"f"}, "PASS", "F1 손 계산 계수"),
        ("손으로 접은 계수 4e-6*W/L", "def ids(kp, w, l, vov):\n    return 0.5 * kp * (w / l) * vov ** 2\n", "def test_ids():\n    assert ids(200e-6, W, L, 0.2) == pytest.approx(4e-6 * W / L)\n", {"ids"}, "PASS", "F1 손 계산 계수"),
        # review32 M-04와 FN3·FN7·FN8
        ("합 위 단항 마이너스 -(b+c) 대 -p-q", "def n(b, c):\n    return -(b + c)\n", "def test_n():\n    assert n(p, q) == pytest.approx(-p - q)\n", {"n"}, "FAIL", None),
        ("for 안의 재서술", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    for gm in (1e-3, 2e-3):\n        assert gain(gm, 50e3) == pytest.approx(gm * 50e3)\n", {"gain"}, "FAIL", None),
        ("with 안의 재서술", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    with ctx():\n        assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("np.testing.assert_allclose 재서술", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    np.testing.assert_allclose(gain(2e-3, 50e3), 2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("test 쪽 누적 대입 e *= 50e3", "def gain(gm, ro):\n    return gm * ro\n", "def test_gain():\n    e = 2e-3\n    e *= 50e3\n    assert gain(2e-3, 50e3) == pytest.approx(e)\n", {"gain"}, "FAIL", None),
        ("식 안의 피검 호출", "def gp(a, b):\n    return a * b\n", "def test_gp():\n    assert gp(2.0, 3.0) * 1 == pytest.approx(2.0 * 3.0)\n", {"gp"}, "UNJUDGED", None),
        ("피검 없는 assert", "def gp(a, b):\n    return a * b\n", "def test_gp():\n    assert len([1, 2]) == 2\n", {"gp"}, "NO-SUBJECT", None),
        # review33 M2-03: 블록·루프 대상으로 받은 피검 결과, match·중첩 함수·except*
        ("표 구동 zip 루프", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    rs = [gain(g, 50e3) for g in gms]\n    for r, g in zip(rs, gms):\n        assert r == pytest.approx(g * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("피검 결과 리스트를 도는 루프", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    for r in [gain(2e-3, 50e3)]:\n        assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("if 블록 안에서 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    if flag:\n        r = gain(2e-3, 50e3)\n    assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("with 블록 안에서 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    with warnings.catch_warnings():\n        r = gain(2e-3, 50e3)\n    assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("try 블록 안에서 받은 결과", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    try:\n        r = gain(2e-3, 50e3)\n    except ValueError:\n        r = 0.0\n    assert r == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "UNJUDGED", None),
        ("match 안의 재서술", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    match mode:\n        case 1:\n            assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("test 안 중첩 함수", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    def check(g):\n        assert gain(g, 50e3) == pytest.approx(g * 50e3)\n    check(2e-3)\n", {"gain"}, "UNJUDGED", None),
        ("except* 안의 재서술", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    try:\n        pass\n    except* ValueError:\n        assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        # review33 M2-04~M2-06
        ("쌍 없는 피검 없는 assert", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert len(xs) > 0\n", {"gain"}, "NO-SUBJECT", None),
        ("쌍 없는 피검 assert", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3) > 0\n", {"gain"}, "UNJUDGED", None),
        ("inf 리터럴(예외 없음)", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert gain(1e400, 2.0) == pytest.approx(1e400 * 2.0)\n", {"gain"}, "FAIL", None),
        ("async test", "def gain(gm, ro, note=None):\n    return gm * ro\n", "async def test_gain():\n    assert gain(2e-3, 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("쓰지 않는 인자로 통과 경로 흉내", "def gain(gm, ro, note=None):\n    return gm * ro\n", "def test_gain():\n    assert gain(2e-3, 50e3, note=2e-3 * 50e3) == pytest.approx(2e-3 * 50e3)\n", {"gain"}, "FAIL", None),
        ("피검 안 중첩 함수 return", "def f(x, k):\n    def inner(y):\n        return y * k\n    return x + 1.0\n", "def test_f():\n    assert f(y0, 2.0) == pytest.approx(y0 * 2.0)\n", {"f"}, "PASS", None),
    ]
    mismatch = 0
    for name, m, t, s, expect, limit in cases + syn:
        r = judge(m, t, s)
        ok = r[0][1] == expect.split()[-1]  # 첫 판정 문장의 출력과 기대(마지막 단어)를 대조
        mismatch += not ok
        line = ("" if ok else "MISMATCH ") + f"{name}: {r} | 기대 {expect}" + (f" | known_limit {limit}" if limit else "")
        with OUT.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"케이스 {len(cases) + len(syn)}개, 기대 불일치 {mismatch}개\n")
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
