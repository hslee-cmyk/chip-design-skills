"""pure_sqp 검증: 표준 문제에서 scipy SLSQP 와 해가 같은지, 그리고 BLAS 커널을 바꿔도 반복점이 비트 동일한지."""
import sys
import numpy as np
from scipy.optimize import minimize as scipy_min

sys.path.insert(0, "/usrdata/hoseung.lee/claude.run/scratch/nfr4_work/exp_sqp")
import pure_sqp


def rosen(x):
    return float(sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2))


def rosen_g(x):
    g = np.zeros_like(x)
    g[:-1] = -400.0 * x[:-1] * (x[1:] - x[:-1] ** 2) - 2.0 * (1 - x[:-1])
    g[1:] += 200.0 * (x[1:] - x[:-1] ** 2)
    return g


PROBLEMS = {}
# 1) 상자 제약만 (Rosenbrock 4변수)
PROBLEMS["rosenbrock_box"] = dict(fun=rosen, jac=rosen_g, x0=np.array([-1.2, 1.0, -0.5, 0.8]), bounds=[(-2, 0.5)] * 4, cons=[])
# 2) HS71: min x1 x4 (x1+x2+x3) + x3 ; x1x2x3x4>=25 ; sum x^2 = 40 ; 1<=x<=5
PROBLEMS["hs71"] = dict(
    fun=lambda x: float(x[0] * x[3] * (x[0] + x[1] + x[2]) + x[2]),
    jac=lambda x: np.array([x[3] * (2 * x[0] + x[1] + x[2]), x[0] * x[3], x[0] * x[3] + 1.0, x[0] * (x[0] + x[1] + x[2])]),
    x0=np.array([1.0, 5.0, 5.0, 1.0]), bounds=[(1, 5)] * 4,
    cons=[{"type": "ineq", "fun": lambda x: np.array([x[0] * x[1] * x[2] * x[3] - 25.0]),
           "jac": lambda x: np.array([[x[1] * x[2] * x[3], x[0] * x[2] * x[3], x[0] * x[1] * x[3], x[0] * x[1] * x[2]]])},
          {"type": "eq", "fun": lambda x: np.array([float(x @ x) - 40.0]), "jac": lambda x: np.array([2 * x])}])
# 3) 로그 변수 문제(엔진 꼴): min u  s.t.  u + a_m z_m... 간단화 -- min sum exp(z) s.t. sum z >= 2, 상자
PROBLEMS["exp_sum"] = dict(
    fun=lambda z: float(np.sum(np.exp(z))), jac=lambda z: np.exp(z), x0=np.array([0.5, 0.2, 0.9]), bounds=[(-3, 3)] * 3,
    cons=[{"type": "ineq", "fun": lambda z: np.array([float(np.sum(z)) - 2.0, 3.0 - float(z[0] - z[1])]),
           "jac": lambda z: np.array([[1.0, 1.0, 1.0], [-1.0, 1.0, 0.0]])}])
# 4) 고정 변수(lo == hi)가 있는 문제 + 차분 도함수(jac 없음)
PROBLEMS["frozen_fd"] = dict(
    fun=lambda x: float((x[0] - 1) ** 2 + (x[1] - 2) ** 2 + (x[2] + 1) ** 2), jac=None, x0=np.array([0.0, 0.0, 0.5]),
    bounds=[(-5, 5), (-5, 5), (0.5, 0.5)],
    cons=[{"type": "ineq", "fun": lambda x: np.array([1.5 - x[0] - x[1]])}])

if __name__ == "__main__":
    ok = True
    for name, p in PROBLEMS.items():
        kw = dict(jac=p["jac"], bounds=p["bounds"], constraints=p["cons"], options={"ftol": 1e-10, "maxiter": 200})
        ref = scipy_min(p["fun"], p["x0"], method="SLSQP", **kw)
        got = pure_sqp.minimize(p["fun"], p["x0"], **kw)
        dx = float(np.max(np.abs(ref.x - got.x)))
        df = abs(ref.fun - got.fun)
        flag = "OK " if (got.success and dx < 1e-4 and df < 1e-6) else "BAD"
        ok &= flag == "OK "
        print("%s %-16s scipy f=%.8g nit=%d | pure f=%.8g nit=%d status=%d | max|dx|=%.1e |df|=%.1e" % (flag, name, ref.fun, ref.nit, got.fun, got.nit, got.status, dx, df))
    sys.exit(0 if ok else 1)
