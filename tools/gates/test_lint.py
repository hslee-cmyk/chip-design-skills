"""V4 자기참조 lint (05-role-separation design §10, 계획 N4.2 V4 (1)~(5)).

    $PY test_lint.py --root <격리 복제본 루트> (--interface-card <파일> | --subject <모듈>:<심볼> …)
                     [--base <커밋> --head <커밋> | <test 파일> …] [--module-dir <디렉터리>]

판정은 JSON 한 줄로 표준출력, exit 0 PASS / 1 FAIL / 2 실행 오류(auditor는 FAIL로 적는다, §10 머리).

* (1) 기대값 변수가 피검 함수 호출로 만들어짐 -- 아래 DESIGN-GAP의 식
* (2) 확실한 복사(사용자 결정 (c), review30 R-05·R-06) -- `judge()`. 규칙 함수는 실측 probe
  `docs/03-analysis/gain-budget-gmid-sizing-function-audit/v4_rule_probe/v4.py`에서 글자 그대로 옮겼다(§10: 부트스트랩
  ①에서 probe의 규칙 함수를 이 파일로 옮긴다). FAIL은 확실한 복사이고 PASS는 독립의 증거가 아니다(알려진 놓침 F1~F8).
  판정 문장마다 FAIL / PASS / UNJUDGED / NO-SUBJECT.
* (3) assert가 if·try 안에만 있음 (4) assert 0개 (5) print·logging으로만 판정

DESIGN-GAP: 계획 N4.2 V4 (1) "기대값 변수가 피검 함수 호출로 만들어짐" -- 판정 문장의 두 쪽 모두에 **같은** 피검 호출
(같은 함수, 인자 정규형이 같다)이 들어 있으면(지역 대입 인라인 뒤) FAIL로 읽는다. 다른 입력의 피검 호출끼리 비교하는
불변식 test(IC2 순서 섞기 등, oracle (a))는 (1)이 아니다 -- 두 쪽에 피검 호출이 있다는 것만으로 FAIL이면 정상 흐름의
계약 test가 오거부된다. 다른 입력의 피검 호출로 만든 기대값은 auditor oracle 대조(`checks.V4.basis`)가 맡는다.
"""
import ast
import copy
import functools
import json
import os
import re
import subprocess
import sys
from fractions import Fraction


# ---------- 지역 대입 인라인 ----------
class _Sub(ast.NodeTransformer):
    def __init__(self, env):
        self.env = env

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.env:
            return copy.deepcopy(self.env[node.id])
        return node


def _inline(expr, env):
    # 소스로 되돌려 다시 파싱하지 않고 AST를 복사한다 -- 불투명 이름(`<opaque:…>`)은 소스로 쓸 수 없어
    # 다시 파싱하면 SyntaxError가 났다(review35 M4-03: `return inner(x)` 같은 중첩 def·class 호출)
    return _Sub(env).visit(copy.deepcopy(expr))


def _opaque(name):
    return ast.Name(id=f"<opaque:{name}>", ctx=ast.Load())


_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda,
           ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _assigned_names(stmts):
    """이 범위에서 대입되는 이름. 중첩 함수·클래스·lambda·comprehension의 지역 이름은 넣지 않는다
    (review34 M3-05: 바깥 이름을 가려 불투명으로 만들던 결함). 중첩 def·class의 이름 자체는 넣는다."""
    names, stack = set(), list(stmts)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
            continue
        if isinstance(n, _SCOPES):
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            names.add(n.id)
        stack.extend(ast.iter_child_nodes(n))
    return names


def _base_name(t):
    """첨자·속성 대입 대상의 밑 이름(`out[g]`, `res.v`, `a.b[c]` -> 밑 이름), 없으면 None."""
    while isinstance(t, (ast.Subscript, ast.Attribute)):
        t = t.value
    return t.id if isinstance(t, ast.Name) else None


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
    # AST 노드에 결과를 붙여 둔다(함수마다 한 번 -- 상한 = 모듈의 함수 수)
    cached = getattr(fdef, "_v4_returns", None)
    if cached is None:
        cached = []
        _walk_body(fdef.body, {}, cached)
        fdef._v4_returns = cached
    return cached


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
    """expr 안의 같은 모듈 함수 호출을 인라인한 식(목록 하나). return이 **하나인** 함수만 인라인하고,
    return이 여럿인 함수의 호출은 불투명 호출로 둔다 -- 여럿을 조합으로 펼치면 변형 수가 곱으로 늘어
    실제 엔진 함수(`stick_diagram.propose_device_roles_gap_fill`)에서 끝나지 않았다(review35 뒤 전수 실측)."""
    class _T(ast.NodeTransformer):
        def visit_Call(self, node):
            self.generic_visit(node)
            name = _callee(node)
            if name in module_funcs and name not in stack:
                fdef = module_funcs[name]
                rs = return_variants(fdef)
                if len(rs) == 1:
                    bound = _bind(fdef, node)
                    if bound is not None:
                        return expand(_inline(rs[0], bound), module_funcs, stack + (name,))[0]
            return node
    return [_T().visit(copy.deepcopy(expr))]


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
            # 블록 안에서 첨자·속성·메서드로 피검 불투명이 된 밑 이름도 블록 밖으로 올린다(review34 M3-04)
            for b in branches:
                for n, v in b.items():
                    if isinstance(v, ast.Name) and v.id.startswith("<opaque-subject:"):
                        env[n] = v
        else:
            # 피검 결과를 첨자·속성·메서드 호출로 받으면 그 밑 이름을 피검 불투명으로(review34 M3-04):
            # `out[g] = f(g)`, `res.v = f(…)`, `rs.append(f(…))`
            if isinstance(s, ast.Assign) and _has_subject(_inline(s.value, env), subjects):
                for tg in s.targets:
                    b = _base_name(tg)
                    if b:
                        env[b] = ast.Name(id=f"<opaque-subject:{b}>", ctx=ast.Load())
            if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Attribute):
                b = _base_name(s.value.func.value)
                args = s.value.args + [k.value for k in s.value.keywords]
                if b and any(_has_subject(_inline(x, env), subjects) for x in args):
                    env[b] = ast.Name(id=f"<opaque-subject:{b}>", ctx=ast.Load())
            # 중첩 def·class, 다루지 않는 문장: 안의 판정 문장은 UNJUDGED, 대입된 이름은 값에 피검이 있으면 피검 불투명
            for sub in ast.walk(s):
                if sub is not s and _is_judgement(sub):
                    out.append((sub.lineno, None, None, True))
            mark(_assigned_names([s]), getattr(s, "value", None))
    return out


def _is_leaf(c):
    return c[0] in ("num", "name", "const")


@functools.lru_cache(maxsize=8)  # 같은 모듈을 test마다 다시 파싱하지 않는다(상한 = 한 판정에 드는 모듈 수 정도)
def _module_funcs(module_src):
    mod = ast.parse(module_src)
    return {f.name: f for f in mod.body if isinstance(f, ast.FunctionDef)}


def judge(module_src, test_src, subjects, inline_test=True, inline_subject=True):
    """_judge를 감싼다: 식이 너무 깊어 어디서든(test 쪽 인라인 포함) 펼치지 못하면 판정하지 못함(review36 S3 --
    `_hits` 밖의 깊은 식은 예외로 끝났다). 판정 문장 단위를 잃으므로 줄 번호 0의 UNJUDGED 하나로 낸다."""
    try:
        return _judge(module_src, test_src, subjects, inline_test, inline_subject)
    except (RecursionError, MemoryError):
        return [(0, "UNJUDGED")]


def _judge(module_src, test_src, subjects, inline_test=True, inline_subject=True):
    """assert마다 (줄, 판정). 판정: FAIL(확실한 복사) / PASS / UNJUDGED(피검이 걸렸는데 판정 못 함 --
    auditor 대조 대상) / NO-SUBJECT(피검 호출이 없는 assert -- V4 (2) 대상 아님)."""
    funcs = _module_funcs(module_src)
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
        try:
            hit = _hits(rs, bound, funcs, fdef, cx)
        except (RecursionError, MemoryError):
            # 식이 너무 깊거나 커서 펼치지 못함 -> 판정하지 못함(UNJUDGED, auditor 대조 대상)
            results.append((lineno, "UNJUDGED"))
            continue
        results.append((lineno, "FAIL" if hit else "PASS"))
    return results


def _hits(rs, bound, funcs, fdef, cx):
    hit = []
    if True:
        for r in rs:
            used = {n.id for n in ast.walk(r) if isinstance(n, ast.Name)} & set(bound)
            passthrough = {canon(bound[p]) for p in used}
            for e in expand(_inline(r, bound), funcs, (fdef.name,)):
                c = canon(e)
                if not _is_leaf(c) and c not in passthrough and c in cx:
                    hit.append(c)
    return hit


# ================================================================ 게이트 도구 부분(§10 V4 (1)(3)(4)(5), 여러 test·모듈)
_PRIORITY = {"FAIL": 3, "UNJUDGED": 2, "PASS": 1, "NO-SUBJECT": 0}


def _fn_source(file_src, fn):
    """test 함수 한 개의 소스(`def` 줄부터, 들여쓰기 제거)와 줄 번호 보정값."""
    lines = file_src.split("\n")
    seg = lines[fn.lineno - 1:fn.end_lineno]
    ind = len(seg[0]) - len(seg[0].lstrip())
    out = [l[ind:] if l[:ind].strip() == "" else l for l in seg]
    return "\n".join(out) + "\n", fn.lineno - 1


def judge_fn(file_src, fn, module_srcs):
    """V4 (2): module_srcs = {모듈 소스: 피검 심볼 집합}. 판정 문장 줄마다 모듈별 판정의 최댓값(FAIL > UNJUDGED > PASS >
    NO-SUBJECT)."""
    src, off = _fn_source(file_src, fn)
    merged = {}
    for msrc, subj in module_srcs.items():
        for line, out in judge(msrc, src, set(subj)):
            k = line + off if line else 0
            if k not in merged or _PRIORITY[out] > _PRIORITY[merged[k]]:
                merged[k] = out
    return sorted(merged.items())


def _nested_free_walk(node):
    return _walk_no_nested(node)


def _judgements(fn):
    """(판정 문장 노드, 조상 목록) -- 중첩 def·class·lambda 안은 넣지 않는다."""
    out = []

    def rec(n, anc):
        for c in ast.iter_child_nodes(n):
            if isinstance(c, _NESTED):
                continue
            if isinstance(c, ast.Assert) or (isinstance(c, ast.Expr) and _is_assert_call(c)):
                out.append((c, anc))
            rec(c, anc + [c])
    rec(fn, [])
    return out


def _is_pytest_attr(call, names):
    f = call.func
    return isinstance(f, ast.Attribute) and f.attr in names and isinstance(f.value, ast.Name) and f.value.id == "pytest"


def _other_judgements(fn):
    n = 0
    for x in _nested_free_walk(fn):
        if isinstance(x, ast.Call) and (_is_pytest_attr(x, ("raises", "warns", "fail", "deprecated_call"))):
            n += 1
    return n


def _print_calls(fn):
    n = 0
    for x in _nested_free_walk(fn):
        if isinstance(x, ast.Call):
            f = x.func
            if isinstance(f, ast.Name) and f.id == "print":
                n += 1
            elif isinstance(f, ast.Attribute) and f.attr in ("debug", "info", "warning", "warn", "error", "critical",
                                                              "exception", "log") \
                    and isinstance(f.value, ast.Name) and (f.value.id in ("logging", "logger", "log", "LOGGER", "LOG")):
                n += 1
    return n


def _call_keys(expr, subjects):
    keys = set()
    for n in ast.walk(expr):
        if isinstance(n, ast.Call) and _callee(n) in subjects:
            try:
                keys.add((_callee(n), tuple(canon(a) for a in n.args),
                          tuple(sorted((k.arg or "**", canon(k.value)) for k in n.keywords))))
            except RecursionError:
                keys.add((_callee(n), "<deep>", id(n)))
    return keys


def rule1(fn, subjects):
    """(1): 판정 문장 두 쪽 모두에 같은 피검 호출(인자 정규형 같음)이 있다(지역 대입 인라인 뒤)."""
    hits = []
    try:
        pairs = _assert_pairs(fn.body, subjects)
    except RecursionError:
        return hits
    for lineno, a, b, _ in pairs:
        if a is None or b is None:
            continue
        if _call_keys(a, subjects) & _call_keys(b, subjects):
            hits.append(lineno)
    return hits


def lint_function(file_src, fn, module_srcs, subjects):
    """한 test 함수의 V4 판정 목록 [{rule, line, output}]."""
    res = []
    for line in rule1(fn, subjects):
        res.append({"rule": "(1)", "line": line, "output": "FAIL"})
    for line, out in judge_fn(file_src, fn, module_srcs):
        res.append({"rule": "(2)", "line": line, "output": out})
    js = _judgements(fn)
    other = _other_judgements(fn)
    if js:
        guarded = [n for n, anc in js if any(isinstance(a, (ast.If, ast.Try, ast.TryStar)) for a in anc)]
        if len(guarded) == len(js):
            res.append({"rule": "(3)", "line": js[0][0].lineno, "output": "FAIL"})
    elif not other:
        if _print_calls(fn):
            res.append({"rule": "(5)", "line": fn.lineno, "output": "FAIL"})
        else:
            res.append({"rule": "(4)", "line": fn.lineno, "output": "FAIL"})
    return res


def find_test_functions(tree):
    out = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
            out.append((n.name, n))
        elif isinstance(n, ast.ClassDef) and n.name.startswith("Test"):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and m.name.startswith("test"):
                    out.append(("%s::%s" % (n.name, m.name), m))
    return out


def lint_file(path, file_src, module_srcs, subjects):
    tree = ast.parse(file_src)
    findings = []
    for name, fn in find_test_functions(tree):
        for r in lint_function(file_src, fn, module_srcs, subjects):
            r.update({"file": path, "test": name})
            findings.append(r)
    return findings


# ---------------------------------------------------------------- 입력
_ROW = re.compile(r"^\|\s*`?([^|`]+?)`?\s*\|\s*`?([^|`]+?)`?\s*\|")


def read_card_symbols(card_text):
    """interface card의 (모듈, 심볼) 표(`| 모듈 | 심볼 | 시그니처 |` 머리의 표 전부). 심볼 `*`(신규 모듈)는 뺀다."""
    pairs = set()
    lines = card_text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        if re.match(r"^\|\s*모듈\s*\|\s*심볼\s*\|", lines[i]):
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                m = _ROW.match(lines[i])
                if m and m.group(2).strip() != "*":
                    pairs.add((m.group(1).strip(), m.group(2).strip()))
                i += 1
            continue
        i += 1
    return pairs


def _git(root, args):
    p = subprocess.run(["git", "-C", root] + args, capture_output=True, env=dict(os.environ, GIT_NO_REPLACE_OBJECTS="1"))
    if p.returncode != 0:
        raise RuntimeError("git %s 실패: %s" % (" ".join(args[:3]), p.stderr.decode("utf-8", "replace")[:300]))
    return p.stdout


TEST_PREFIX = "skills/analog-gmid-design/assets/tests/"
TEST_EXCLUDE = "skills/analog-gmid-design/assets/tests/tools/"
MODULE_DIR = "skills/analog-gmid-design/assets"


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="test_lint.py")
    ap.add_argument("--root", required=True)
    ap.add_argument("--interface-card")
    ap.add_argument("--subject", action="append", default=[], help="<모듈>:<심볼>")
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--module-dir", default=MODULE_DIR)
    ap.add_argument("files", nargs="*")
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        root = ns.root
        pairs = set()
        if ns.interface_card:
            with open(ns.interface_card, "rb") as fh:
                pairs |= read_card_symbols(fh.read().decode("utf-8"))
        for s in ns.subject:
            m, _, sym = s.partition(":")
            if not m or not sym:
                raise ValueError("--subject 형식은 <모듈>:<심볼>")
            pairs.add((m, sym))
        if not pairs:
            raise ValueError("피검 심볼이 없다(--interface-card 또는 --subject)")

        def read(rel):
            if ns.head:
                return _git(root, ["show", "%s:%s" % (ns.head, rel)]).decode("utf-8")
            with open(os.path.join(root, *rel.split("/")), "rb") as fh:
                return fh.read().decode("utf-8")
        by_mod = {}
        for m, sym in pairs:
            by_mod.setdefault(m, set()).add(sym)
        module_srcs = {}
        for m, syms in by_mod.items():
            module_srcs[read("%s/%s.py" % (ns.module_dir.rstrip("/"), m.replace(".", "/")))] = syms
        subjects = {s for _, s in pairs}
        files = list(ns.files)
        if ns.base and ns.head and not files:
            out = _git(root, ["diff", "--name-only", "--no-renames", "--diff-filter=AM", ns.base, ns.head]).decode("utf-8")
            files = [p for p in out.splitlines() if p.startswith(TEST_PREFIX) and not p.startswith(TEST_EXCLUDE)
                     and p.endswith(".py") and os.path.basename(p) != "conftest.py"]
        findings = []
        for f in files:
            rel = f.replace("\\", "/")
            findings += lint_file(rel, read(rel) if (ns.head or not os.path.isabs(rel)) else open(rel, encoding="utf-8").read(),
                                  module_srcs, subjects)
    except (OSError, ValueError, RuntimeError, SyntaxError, UnicodeDecodeError) as e:
        print(json.dumps({"tool": "V4", "verdict": "ERROR", "error": "%s: %s" % (type(e).__name__, e)}, ensure_ascii=False))
        return 2
    fail = [x for x in findings if x["output"] == "FAIL"]
    print(json.dumps({"tool": "V4", "verdict": "FAIL" if fail else "PASS", "files": files, "findings": findings,
                      "unjudged": [x for x in findings if x["output"] == "UNJUDGED"]}, ensure_ascii=False))
    return 1 if fail else 0


if __name__ == "__main__":
    # 로캘·PYTHONIOENCODING과 무관하게 출력을 UTF-8로(spec card 20260921-gate-output-utf8).
    # Python 3.14는 항상 reconfigure를 제공한다(V6, spec card 20260921-gate-flow-liveness 계약 6).
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
