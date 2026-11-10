"""순수 Python SQP (실험용 -- 엔진에 반영하지 않는다).

목적: scipy SLSQP 는 BLAS 를 거쳐 CPU 커널(OpenBLAS DYNAMIC_ARCH)이 다르면 반복점이 갈라진다(nfr4 비교 실측). 이 모듈은 최적화기 안의 선형대수에
numpy·BLAS 를 전혀 쓰지 않고 Python float 사칙연산(IEEE 754 binary64, 정해진 순서)만 써서 커널과 무관하게 같은 반복점이 나오는지 본다.

`minimize(fun, x0, jac=, bounds=, constraints=, callback=, options={"ftol","maxiter"})` -- scipy.optimize.minimize(method="SLSQP") 의 엔진 쓰임에 맞춘 부분집합:
* 변수 상자(lo/hi, None = 무한, lo == hi 는 고정 변수), 제약 {"type": "ineq"|"eq", "fun", "jac"(없으면 전진 차분)}. ineq 는 c(x) >= 0.
* 알고리즘: QP 부문제 = Goldfarb-Idnani 듀얼 active-set (엄격 볼록, G = 감쇠 BFGS 근사), 메리트 = L1(페널티 μ 는 SLSQP 식 갱신), 선 탐색 = 반으로 줄이기(Armijo 0.1).
* 결과 .x(numpy 배열) .fun .nit .status .success .message. status: 0 성공, 4 선형화 제약 비호환, 8 선 탐색 실패(상승 방향), 9 반복 상한.
* 콜백·fun·jac·제약이 던지는 예외는 잡지 않고 그대로 올린다(엔진의 _Abort).
"""
import math

import numpy as np

_FD_EPS = 1.4901161193847656e-08      # scipy SLSQP 의 전진 차분 절대 스텝과 같은 값
_TINY = 1e-14
_ALPHA_MIN = 0.1                      # SLSQP 의 alfmin


import os
import sys


def _trace(msg):
    if os.environ.get("PURE_SQP_TRACE"):
        sys.stderr.write("[pure_sqp] " + msg + "\n")


class Result:
    def __init__(self, x, fun, nit, status, message):
        self.x = np.array(x, dtype=float)
        self.fun = fun
        self.nit = nit
        self.status = status
        self.success = status == 0
        self.message = message


# ---------------------------------------------------------------- 순수 Python 선형대수 (리스트, 정해진 합산 순서)

_FAIL = ['']


def _dot(a, b):
    s = 0.0
    for i in range(len(a)):
        s += a[i] * b[i]
    return s


def _matvec(M, v):
    return [_dot(row, v) for row in M]


def _solve(M, rhs):
    """가우스 소거(부분 피벗). 특이하면 ZeroDivisionError."""
    n = len(rhs)
    A = [list(M[i]) + [rhs[i]] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(A[r][c]))
        if abs(A[piv][c]) < _TINY:
            raise ZeroDivisionError("singular")
        if piv != c:
            A[c], A[piv] = A[piv], A[c]
        for r in range(c + 1, n):
            f = A[r][c] / A[c][c]
            if f != 0.0:
                for k in range(c, n + 1):
                    A[r][k] -= f * A[c][k]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = A[i][n]
        for k in range(i + 1, n):
            s -= A[i][k] * x[k]
        x[i] = s / A[i][i]
    return x


def _spd_inverse(B):
    """콜레스키로 B 의 역행렬. 양정치가 아니면 None."""
    n = len(B)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = B[i][j]
            for k in range(j):
                s -= L[i][k] * L[j][k]
            if i == j:
                if s <= _TINY:
                    return None
                L[i][i] = math.sqrt(s)
            else:
                L[i][j] = s / L[j][j]
    inv = [[0.0] * n for _ in range(n)]
    for col in range(n):
        y = [0.0] * n                       # L y = e_col
        for i in range(n):
            s = 1.0 if i == col else 0.0
            for k in range(i):
                s -= L[i][k] * y[k]
            y[i] = s / L[i][i]
        for i in range(n - 1, -1, -1):      # L^T x = y
            s = y[i]
            for k in range(i + 1, n):
                s -= L[k][i] * inv[k][col]
            inv[i][col] = s / L[i][i]
    return inv


# ---------------------------------------------------------------- QP: min 1/2 d'Gd + g'd  s.t. a_i'd >= b_i (eq 는 a_i'd = b_i)

def _gi_core(Ginv, g, rows):
    """Goldfarb-Idnani (행은 이미 정규화돼 있다). rows = [(a, b, is_eq)]. 반환 (d, 승수 리스트(rows 와 같은 순서; 부등식 >= 0)) 또는 None(비호환)."""
    n = len(g)
    m = len(rows)
    x = [-v for v in _matvec(Ginv, g)]
    act = []                                  # 활성 목록: (행 번호, a, b, eq, 부호)
    u = []
    pend = [i for i in range(m) if rows[i][2]]
    skip = set()                              # 반올림 오차 수준으로만 위반이고 활성 법선들과 선형종속인 행 -- 사실상 만족으로 본다

    xmax = [max([abs(v) for v in x] + [0.0])]      # 풀이 중 x 가 지난 최대 크기 -- 반올림 오차는 이 크기에 비례한다

    def tol_of(a, b):
        return 1e-12 * (1.0 + abs(b)) + 64 * 2.220446049250313e-16 * (abs(b) + xmax[0] * sum(abs(v) for v in a))
    limit = 20 * (m + n) + 200
    guard = 0
    while True:
        if pend:
            p = pend.pop(0)
        else:
            p, worst = None, 0.0
            in_act = {e[0] for e in act}
            for i in range(m):
                if i in in_act or i in skip:
                    continue
                a, b, _ = rows[i]
                s = _dot(a, x) - b
                if s < -tol_of(a, b) and s < worst:
                    p, worst = i, s
            if p is None:
                break
        a_p, b_p, eq_p = rows[p]
        sign = 1.0
        if eq_p and _dot(a_p, x) - b_p > 0.0:
            a_p, b_p, sign = [-v for v in a_p], -b_p, -1.0
        up = 0.0
        while True:
            guard += 1
            if guard > limit:
                _FAIL[0] = 'guard(limit=%d)' % limit
                return None
            q = len(act)
            Ga = _matvec(Ginv, a_p)
            if q:
                GA = [_matvec(Ginv, e[1]) for e in act]                       # G^-1 a_j
                M = [[_dot(act[i][1], GA[j]) for j in range(q)] for i in range(q)]
                rhs = [_dot(act[i][1], Ga) for i in range(q)]
                try:
                    r = _solve(M, rhs)
                except ZeroDivisionError:
                    _FAIL[0] = 'singular M q=%d' % q
                    return None
                z = list(Ga)
                for j in range(q):
                    for k in range(n):
                        z[k] -= r[j] * GA[j][k]
            else:
                r, z = [], list(Ga)
            s_p = _dot(a_p, x) - b_p
            zz = _dot(z, a_p)
            t1, k1 = math.inf, -1
            for j in range(q):
                if not act[j][3] and r[j] > _TINY:
                    ratio = u[j] / r[j]
                    if ratio < t1:
                        t1, k1 = ratio, j
            t2 = (-s_p / zz) if zz > 1e-10 * _dot(a_p, Ga) else math.inf       # z = 0(활성 법선들의 생성 공간 안)인지는 a'G^-1 a 에 상대적으로 판정
            t = min(t1, t2)
            if t == math.inf:
                if not eq_p and -s_p <= max(10.0 * tol_of(a_p, b_p), 1e-6 * (1.0 + abs(b_p))):      # 선형화에서 1e-6(정규화 단위) 안쪽 위반은 의미가 없다(SLSQP 제약 허용도 수준)
                    skip.add(p)
                    break
                _FAIL[0] = 't=inf (zz=%.3e aga=%.3e s_p=%.3e q=%d)' % (zz, _dot(a_p, Ga), s_p, q)
                return None
            if t2 != math.inf:
                for k in range(n):
                    x[k] += t * z[k]
                xmax[0] = max(xmax[0], max(abs(v) for v in x))
            u = [u[j] - t * r[j] for j in range(q)]
            up += t
            if t == t2:
                act.append((p, a_p, b_p, eq_p, sign))
                u.append(up)
                break
            del act[k1]
            del u[k1]
    mult = [0.0] * m
    for e, val in zip(act, u):
        mult[e[0]] = val * e[4]
    return x, mult


def _gi_qp(Ginv, g, rows):
    """행 정규화(a/|a|, b/|a|) 뒤 _gi_core. 승수는 원래 행 기준으로 되돌린다. 기울기 0 행: 상수 조건이라 만족이면 버리고 위반이면 비호환."""
    norm_rows, scale, keep = [], [], []
    for i, (a, b, eq) in enumerate(rows):
        nrm = math.sqrt(_dot(a, a))
        if nrm < 1e-300:
            if (eq and abs(b) > 1e-11 * (1.0 + abs(b))) or (not eq and b > 1e-11 * (1.0 + abs(b))):
                return None
            continue
        norm_rows.append(([v / nrm for v in a], b / nrm, eq))
        scale.append(nrm)
        keep.append(i)
    sol = _gi_core(Ginv, g, norm_rows)
    if sol is None:
        return None
    d, mult_n = sol
    mult = [0.0] * len(rows)
    for pos, i in enumerate(keep):
        mult[i] = mult_n[pos] / scale[pos]
    return d, mult


def _relaxed_qp(Ginv, g, rows):
    """선형화 제약이 비호환일 때(Powell 완화): 위반된 제약의 상수항에 스칼라 theta in [0,1] 을 곱한다.
    min 1/2 d'Gd + g'd + 1/2 rho (1-theta)^2   s.t.  a'd >= theta*b (위반 행), a'd = theta*b (등식 행), 0 <= theta <= 1.  d=0, theta=0 이 항상 가능하다."""
    n = len(g)
    rho = 1e3 * (1.0 + max((abs(v) for v in g), default=0.0))
    Gin = [list(Ginv[i]) + [0.0] for i in range(n)] + [[0.0] * n + [1.0 / rho]]
    g2 = list(g) + [-rho]
    rows2 = []
    for a, b, eq in rows:
        if (eq and b != 0.0) or (not eq and b > 0.0):
            rows2.append((list(a) + [-b], 0.0, eq))
        else:
            rows2.append((list(a) + [0.0], b, eq))
    rows2.append(([0.0] * n + [1.0], 0.0, False))
    rows2.append(([0.0] * n + [-1.0], -1.0, False))
    sol = _gi_qp(Gin, g2, rows2)
    if sol is None:
        return None
    d2, mult = sol
    return d2[:n], mult[:len(rows)], d2[n]


# ---------------------------------------------------------------- SQP 본체

def _fd_grad(f, x, f0):
    g = []
    for i in range(len(x)):
        xi = list(x)
        xi[i] = x[i] + _FD_EPS
        g.append((f(xi) - f0) / _FD_EPS)
    return g


def minimize(fun, x0, args=(), method=None, jac=None, bounds=None, constraints=(), tol=None, callback=None, options=None):
    opts = dict(options or {})
    ftol = float(opts.get("ftol", 1e-6))
    maxiter = int(opts.get("maxiter", 100))
    n = len(x0)
    lo = [-math.inf] * n
    hi = [math.inf] * n
    if bounds is not None:
        for i, (l, h) in enumerate(bounds):
            if l is not None:
                lo[i] = float(l)
            if h is not None:
                hi[i] = float(h)
    cons = list(constraints) if isinstance(constraints, (list, tuple)) else [constraints]
    ineq = [c for c in cons if c["type"] == "ineq"]
    eqs = [c for c in cons if c["type"] == "eq"]

    def arr(x):
        return np.array(x, dtype=float)

    def f_of(x):
        return float(fun(arr(x), *args))

    def c_of(c, x):
        return [float(v) for v in np.atleast_1d(c["fun"](arr(x)))]

    def grad_f(x, f0):
        return [float(v) for v in jac(arr(x))] if callable(jac) else _fd_grad(f_of, x, f0)

    def jac_c(c, x, c0):
        if c.get("jac") is not None:
            return [[float(v) for v in row] for row in np.atleast_2d(c["jac"](arr(x)))]
        rows = [[0.0] * n for _ in c0]
        for i in range(n):
            xi = list(x)
            xi[i] = x[i] + _FD_EPS
            ci = c_of(c, xi)
            for k in range(len(c0)):
                rows[k][i] = (ci[k] - c0[k]) / _FD_EPS
        return rows

    x = [min(max(float(x0[i]), lo[i]), hi[i]) for i in range(n)]

    def evaluate(x, with_derivs):
        f = f_of(x)
        ci = [c_of(c, x) for c in ineq]
        ce = [c_of(c, x) for c in eqs]
        if not with_derivs:
            return f, ci, ce, None, None, None
        g = grad_f(x, f)
        Ji = [jac_c(c, x, v) for c, v in zip(ineq, ci)]
        Je = [jac_c(c, x, v) for c, v in zip(eqs, ce)]
        return f, ci, ce, g, Ji, Je

    def flat(blocks):
        return [v for blk in blocks for v in blk]

    def flat_rows(blocks):
        return [row for blk in blocks for row in blk]

    f, ci, ce, g, Ji, Je = evaluate(x, True)
    cin, cen = flat(ci), flat(ce)
    n_in, n_eq = len(cin), len(cen)
    mu = [0.0] * (n_in + n_eq)
    B = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    nit = 0
    reset_done = False

    def violation(cin_, cen_):
        return sum(max(0.0, -v) for v in cin_) + sum(abs(v) for v in cen_)

    _trace("---- minimize start: n=%d n_in=%d n_eq=%d maxiter=%d ftol=%.1e f0=%.6e viol0=%.3e" % (n, n_in, n_eq, maxiter, ftol, f, violation(cin, cen)))
    while nit < maxiter:
        Ginv = _spd_inverse(B)
        if Ginv is None:
            B = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
            Ginv = _spd_inverse(B)
        rows = []
        for row, c0 in zip(flat_rows(Ji), cin):
            rows.append((row, -c0, False))
        for row, c0 in zip(flat_rows(Je), cen):
            rows.append((row, -c0, True))
        for i in range(n):
            if lo[i] == hi[i]:
                e = [0.0] * n
                e[i] = 1.0
                rows.append((e, lo[i] - x[i], True))
                continue
            if lo[i] > -math.inf:
                e = [0.0] * n
                e[i] = 1.0
                rows.append((e, lo[i] - x[i], False))
            if hi[i] < math.inf:
                e = [0.0] * n
                e[i] = -1.0
                rows.append((e, x[i] - hi[i], False))
        sol = _gi_qp(Ginv, g, rows)
        theta = 1.0
        if sol is not None:
            sol = (sol[0], sol[1], 1.0)
        else:
            sol = _relaxed_qp(Ginv, g, rows)
        if sol is None:
            if os.environ.get("PURE_SQP_DUMP"):
                import json as _j
                with open(os.environ["PURE_SQP_DUMP"], "w") as _fh:
                    _j.dump({"g": g, "rows": rows, "B": B}, _fh)
            _trace("qp_none: n=%d n_in=%d n_eq=%d max_viol=%.3e frozen=%d" % (n, n_in, n_eq, max([0.0] + [max(0.0, -v) for v in cin] + [abs(v) for v in cen]), sum(1 for i in range(n) if lo[i] == hi[i])))
            return Result(x, f, nit, 4, "Inequality constraints incompatible")
        d, lam, theta = sol
        lam_c = lam[:n_in + n_eq]
        for j in range(n_in + n_eq):
            mu[j] = max(abs(lam_c[j]), 0.5 * (mu[j] + abs(lam_c[j])))
        gd = _dot(g, d)
        vio = [max(0.0, -cin[j]) for j in range(n_in)] + [abs(cen[j]) for j in range(n_eq)]
        vtot = sum(vio)
        if theta * vtot > 0.0 and gd > 0.0:
            need = gd / (0.5 * theta * vtot)                      # 이러면 dphi <= -gd 로 확실히 내려간다
            for j in range(n_in + n_eq):
                if vio[j] > 0.0 and mu[j] < need:
                    mu[j] = need
        viol_pen = sum(mu[j] * vio[j] for j in range(n_in + n_eq))
        phi0 = f + viol_pen
        dphi = gd - theta * viol_pen
        if _dot(d, d) <= 1e-30:
            if violation(cin, cen) < 10.0 * ftol:
                return Result(x, f, nit, 0, "Optimization terminated successfully")
            _trace("d_zero_but_violated: viol=%.3e nit=%d" % (violation(cin, cen), nit))
            return Result(x, f, nit, 4, "Inequality constraints incompatible")
        if dphi >= 0.0:
            if not reset_done:
                B = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
                reset_done = True
                continue
            _trace("dphi>=0 after B reset: nit=%d dphi=%.3e gd=%.3e viol_pen=%.3e |d|=%.3e mu_max=%.3e" % (nit, dphi, _dot(g, d), viol_pen, math.sqrt(_dot(d, d)), max(mu + [0.0])))
            return Result(x, f, nit, 8, "Positive directional derivative for linesearch")
        reset_done = False
        # 선 탐색 (SLSQP 식): 2차 보간으로 줄이되 alpha 는 0.1 아래로 내려가지 않고, 10번 시도해도 메리트가 안 줄면 그 스텝을 받아들인다.
        # 엔진 목적·제약은 PDK 격자·bin 때문에 계단 함수라 작은 alpha 의 기울기가 의미 없다 -- 유한한 스텝을 받아들이고 BFGS 가 보정한다.
        alpha = 1.0
        ls_log = []
        tries = 0
        while True:
            xt = [x[i] + alpha * d[i] for i in range(n)]
            ft, cit, cet, _, _, _ = evaluate(xt, False)
            cin_t, cen_t = flat(cit), flat(cet)
            phi = ft + sum(mu[j] * max(0.0, -cin_t[j]) for j in range(n_in)) + sum(mu[n_in + j] * abs(cen_t[j]) for j in range(n_eq))
            ls_log.append((alpha, ft, violation(cin_t, cen_t), phi))
            if phi <= phi0 + 0.1 * alpha * dphi:
                break
            tries += 1
            if alpha <= _ALPHA_MIN or tries > 10:
                _trace("linesearch forced accept: nit=%d alpha=%.3g phi0=%.6e phi=%.6e" % (nit, alpha, phi0, phi))
                break
            curv = (phi - phi0 - dphi * alpha) / (alpha * alpha)
            a_star = (-dphi / (2.0 * curv)) if curv > 0.0 else 0.5 * alpha
            alpha = max(_ALPHA_MIN, min(a_star, 0.5 * alpha))
        xn = xt
        fn, cin_n, cen_n = ft, cin_t, cen_t
        _, _, _, gn, Jin, Jen = evaluate(xn, True)
        nit += 1
        if os.environ.get("PURE_SQP_ITER"):
            _trace("iter %3d  f=%.6e -> %.6e  viol=%.3e -> %.3e  alpha=%.3g |d|=%.3e theta=%.3g mu_max=%.2e" % (nit, f, fn, violation(cin, cen), violation(cin_n, cen_n), alpha, math.sqrt(_dot(d, d)), theta, max(mu + [0.0])))
        if callback is not None:
            callback(arr(xn))
        # 감쇠 BFGS (Powell)
        s = [xn[i] - x[i] for i in range(n)]
        lam_in, lam_eq = lam_c[:n_in], lam_c[n_in:]

        def lag_grad(gv, Jin_, Jen_):
            out = list(gv)
            for j, row in enumerate(flat_rows(Jin_)):
                for k in range(n):
                    out[k] -= lam_in[j] * row[k]
            for j, row in enumerate(flat_rows(Jen_)):
                for k in range(n):
                    out[k] -= lam_eq[j] * row[k]
            return out

        y = [a - b for a, b in zip(lag_grad(gn, Jin, Jen), lag_grad(g, Ji, Je))]
        Bs = _matvec(B, s)
        sBs, sy = _dot(s, Bs), _dot(s, y)
        if sBs > _TINY:
            theta = 1.0 if sy >= 0.2 * sBs else 0.8 * sBs / (sBs - sy)
            y = [theta * y[i] + (1.0 - theta) * Bs[i] for i in range(n)]
            sy = _dot(s, y)
            if sy > _TINY:
                for i in range(n):
                    for j in range(n):
                        B[i][j] += y[i] * y[j] / sy - Bs[i] * Bs[j] / sBs
        done = abs(fn - f) < ftol and violation(cin_n, cen_n) < ftol
        x, f, cin, cen, g, Ji, Je = xn, fn, cin_n, cen_n, gn, Jin, Jen
        if done:
            return Result(x, f, nit, 0, "Optimization terminated successfully")
    return Result(x, f, nit, 9, "Iteration limit reached")
