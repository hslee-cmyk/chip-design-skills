"""출력 적분 잡음 noise_out_int_vrms (설계 41 §7.1 표·'파일럿 적분 범위'·§7.3 '폐루프 모드'·'산출', 단위 U8).

진입점: `noise_integral(setup) -> NoiseAnalysis`(필드 `out_int_vrms`).

v_out = sqrt( ∫_{f_lo}^{f_hi} S_out(f) df + Σ_s kT/C_s·|T_s|² ),  S_out(f) = Σ_k |Z_k(jω)|²·(gm_k²·B_k + gm_k²·A_k/f^EF_k  또는  4kT/R_k).

* 계 = `setup.system`: 폐루프 모드(spec feedback 선언)는 되먹임 소자의 입력 포트 쪽 넷을 자유 노드로 푼 계(`noise_plan`), 되먹임 없음이면 입력 고정 계. Z_k 는 `noise_transfer`
  (as-built MNA 수반, 격자마다 풀이 1회). 출력 = 전달 뷰의 감지(`setup.row`).
* 하한 f_lo = LUT 가 실측한 가장 낮은 잡음 주파수(`NoiseInput.f_lo`, 외삽 없음). 계의 유한 극점 중 f_lo 위의 것과 그 사이 기하 중점이 첫 격자이고, 끝은 계의 가장 높은 극점
  (f_lo 보다 낮으면 f_lo)이다.
* 상한 f_hi(유도): 가장 높은 극점에서 시작해 주파수를 두 배씩 올리며 꼬리 상계 f·S_out(f)(1극 이상 감쇠에서 ∫_f^∞ S ≤ f·S(f))가 분해능² 이하가 되는 첫 점에서 멈춘다. 두 배 확장 상한
  `k_max(f_top·S_peak, 분해능²)`(1극 포락선 S ≤ S_peak·(f_top/f)² 로 유도 -- `_extend`) -- 못 맞추면 `noise_tail_not_converged`(꼬리 상계를 같이 싣는다; 값을 내지 않는다).
* 적분은 구간마다 PSD 를 로그-로그로 보간한 멱법칙 적분이다(S = S1·(f/f1)^m, m = ln(S2/S1)/ln(f2/f1) -- 평탄 구간·극점 뒤 -2 기울기 구간에서 정확하다):
  I = S1·f1·L·exprel(ln(S2/S1) + L), L = ln(f2/f1). 구간마다 중점을 더해 두 반 구간 적분과의 차이(세분 추정의 오차 상계; 점근 오차는 이 차이의 1/3)가 그 구간 예산(분해능 × 구간
  폭/전체 폭) 이하가 될 때까지 이분한다. 이분 횟수 상한 = `k_max(최악 오차/예산, 1)`(오차는 구간 이분마다 1/4, 예산은 1/2). 분해능 전파는 이 적분 규칙의 해석 미분
  (∂I/∂S1, ∂I/∂S2)으로 PSD 의 파라미터 미분을 적분한다.
* 분해능(metrics §9와 같은 방식): LUT 파라미터 불확실성(`ParameterSet`)의 1차 최악 전파 Σ_p |∂I/∂p|·Δp(∂I/∂p = 격자 적분한 ∂S_out/∂p -- S_k 의 gm 직접 의존 포함) +
  LUT 잡음 칸 허용오차 Σ_k tol_k·(그 성분 적분)를 I 단위로 더해 v = sqrt(I) 로 옮긴다(δv = δI/2v). 수치 몫 = (이분 오차 합 + 꼬리 상계)/2v. 분해능 = max(lut, 수치) --
  LUT 몫을 정하지 못하면(`ParameterSet.undetermined`·허용오차 미정) None.
* 스위치 kT/C 항: spec `noise_testbench.sampling_caps` 커패시터마다 kT/C_s × |T_s|², T_s = 그 커패시터에 직렬로 놓인 전압원에서 출력까지의 저주파 전달
  (= jω_ref·C_s·(y[a] − y[b]) -- 노턴 등가 전류 jωC·e, ω_ref = 2π·f_lo). 이 항은 `detail` 의 `ktc_v2` 로 따로 기록한다(엔진 소자 잡음 `device_v2` 와 오라클의 스위치 포함
  구성 차이가 드러나게). 선언이 없으면 0 이고 `ktc_v2` = None.
* 소자별 기여 `contrib`: (이름, (flicker, share, thermal)) -- 적분한 V² 와 총 적분 대비 몫(구간 규칙의 선형화로 소자에 귀속), 스위치 항은 (이름, (ktc)).
"""
import math

import numpy
from scipy import special

from gmid_engine.sizing import k_max

from ._helpers_noise import source_gradient, weights
from .mna_types import Undefined
from .noise_transfer import noise_transfer
from .noise_types import NoiseAnalysis

FIELD = "out_int_vrms"
EPS = float(numpy.finfo(float).eps)
OCTAVE = math.log1p(1)                      # ln 2 -- 주파수 두 배 확장 한 걸음(ln(1 + 1))


class _Stop(Exception):
    """계산 중단 -- `Undefined` tuple 을 들고 `noise_integral` 이 받아 정의 불가로 낸다."""

    def __init__(self, undefined):
        super().__init__("noise_integral stop")
        self.undefined = undefined


def _stop(code, category="definitional", **detail):
    raise _Stop((Undefined(FIELD, code, category, tuple(detail.items())),))


def _precheck(setup):
    sources, noise, plan = setup.sources, setup.noise, setup.plan
    if sources.problems:
        raise _Stop(tuple(Undefined(FIELD, code, "definitional", (("devices", names),)) for code, names in sources.problems))
    if noise.f_lo is None:
        _stop("noise_f_lo_undefined")
    if plan.mode == "undefined":
        raise _Stop((Undefined(FIELD, plan.reason, "definitional", plan.detail),))
    if plan.cap_problems:
        _stop("noise_sampling_cap_unknown", elements=plan.cap_problems)


def _psd_rows(setup, f, tr):
    """(k, N) 잡음원별 출력 PSD 와 (k, N) 계수(열 + flicker/f^ef) -- 계수에 |Z|² 를 곱하면 PSD."""
    src = setup.sources
    coeff = src.thermal[None, :] + src.flicker[None, :] / f[:, None] ** src.ef[None, :]
    return weights(tr) * coeff, coeff


def _evaluate(setup, cache, xs):
    """x(= ln f) 점들의 S_out(f) 를 캐시에 채운다."""
    new = sorted({x for x in xs if x not in cache})
    if not new:
        return
    f = numpy.exp(numpy.array(new))
    tr = noise_transfer(setup.system, setup.row, setup.sources.a, setup.sources.b, 2 * math.pi * f)
    if tr.undefined:
        raise _Stop(tr.undefined)
    psd, _ = _psd_rows(setup, f, tr)
    for x, value in zip(new, psd.sum(axis=1)):
        if not (math.isfinite(value) and value > 0):
            _stop("noise_psd_not_positive", category="numeric", f_hz=float(math.exp(x)))
        cache[x] = float(value)


def _rule(x1, s1, x2, s2):
    """구간 [x1, x2](= ln f) 의 멱법칙 적분 I 와 ∂I/∂S1, ∂I/∂S2 (배열 가능). I = S1·f1·L·exprel(a), a = ln(S2/S1) + L."""
    f1 = numpy.exp(x1)
    span = x2 - x1
    a = numpy.log(s2 / s1) + span
    e = special.exprel(a)
    slope = numpy.divide(e - 1, a, out=numpy.full_like(a, 1 / 2), where=(a != 0))     # d exprel/da, a = 0 에서 1/2
    return s1 * f1 * span * e, f1 * span * (e - slope), (s1 / s2) * f1 * span * slope


def _base_grid(setup):
    f_lo = setup.noise.f_lo
    poles = sorted({abs(p) / (2 * math.pi) for p in setup.poles if abs(p) > 0 and math.isfinite(abs(p))})
    band = [f for f in poles if f > f_lo]
    knots = [f_lo] + band
    mids = [math.sqrt(a * b) for a, b in zip(knots, knots[1:])]
    top = max(poles) if poles else f_lo
    return sorted({math.log(f) for f in knots + mids}), max(top, f_lo)


def _caps_term(setup):
    """스위치 kT/C 항의 전달: [(이름, kT/C, T_s², dT_s²/dp)] -- ω_ref = 2π·f_lo."""
    out = []
    omega = 2 * math.pi * setup.noise.f_lo
    for name, index in setup.plan.caps:
        cap = setup.ss.circuit.capacitors[index]
        tr = noise_transfer(setup.system, setup.row, [cap.a], [cap.b], [omega], parameters=setup.parameters)
        if tr.undefined:
            raise _Stop(tr.undefined)
        scale = (omega * cap.farad) ** 2
        t2 = scale * abs(tr.z[0, 0]) ** 2
        d_t2 = scale * 2 * (numpy.conj(tr.z[0, 0]) * tr.dz[0, :, 0]).real
        out.append((name, setup.noise.kt / cap.farad, t2, d_t2))
    return out


def _final(setup, cache):
    """수렴한 격자에서의 적분·분해능 요소. -> dict."""
    x = numpy.array(sorted(cache))
    f = numpy.exp(x)
    tr = noise_transfer(setup.system, setup.row, setup.sources.a, setup.sources.b, 2 * math.pi * f,
                        parameters=setup.parameters)
    if tr.undefined:
        raise _Stop(tr.undefined)
    src = setup.sources
    power = weights(tr)                                          # 폐루프·개루프 출력 잡음에는 H 가 없다 -> |Z|²
    flick = src.flicker[None, :] / f[:, None] ** src.ef[None, :]
    psd_th, psd_fl = power * src.thermal[None, :], power * flick
    total_psd = (psd_th + psd_fl).sum(axis=1)
    integral, w1, w2 = _rule(x[:-1], total_psd[:-1], x[1:], total_psd[1:])
    i_dev = float(integral.sum())
    linear = w1 @ total_psd[:-1] + w2 @ total_psd[1:]            # 규칙의 선형화 -- 소자별 몫(귀속)의 분모

    def share(part):
        return (w1 @ part[:-1] + w2 @ part[1:]) / linear * i_dev

    i_th, i_fl = share(psd_th), share(psd_fl)
    caps = _caps_term(setup)
    i_ktc = float(sum(kt_c * t2 for _n, kt_c, t2, _d in caps))
    total = i_dev + i_ktc
    v = math.sqrt(total)
    lut_i = None
    if not setup.parameters.undetermined and not numpy.isnan(src.tol_thermal).any() and not numpy.isnan(src.tol_flicker).any():
        d_psd = source_gradient(tr, src.thermal[None, :] + flick, src)
        grad = w1 @ d_psd[:-1] + w2 @ d_psd[1:]
        for _n, kt_c, _t2, d_t2 in caps:
            grad = grad + kt_c * d_t2
        if numpy.isfinite(grad).all():
            lut_i = float((numpy.abs(grad) * setup.parameters.delta).sum() + (src.tol_thermal * i_th).sum()
                          + (src.tol_flicker * i_fl).sum())
    return {"v": v, "total": total, "i_dev": i_dev, "i_th": i_th, "i_fl": i_fl, "caps": caps, "i_ktc": i_ktc,
            "lut_v": None if lut_i is None else lut_i / (2 * v), "points": x.size}


def _extend(setup, cache, x_top, tol_sq):
    """x_top 위로 주파수를 두 배씩 올리며 꼬리 상계 f·S 가 tol_sq 이하가 되는 첫 점까지. -> (마지막 x, 마지막 f·S).
    상한: 가장 높은 극점 f_top 위의 1극 포락선 S(f) ≤ S_peak·(f_top/f)² 에서 f·S ≤ f_top·S_peak/f 이므로 `k_max(f_top·S_peak, tol_sq)` 번이면 충분하다
    (S_peak = 첫 격자에서의 최대 PSD)."""
    _evaluate(setup, cache, [x_top])
    x = x_top
    width = math.exp(x_top) * max(cache.values())
    steps = k_max(width, tol_sq) if width > tol_sq else 0
    steps = max(steps, 1 if len(cache) <= 1 else 0)               # 구간 적분에는 점이 둘 이상 있어야 한다
    for _ in range(steps):
        if len(cache) > 1 and math.exp(x) * cache[x] <= tol_sq:
            break
        x += OCTAVE
        _evaluate(setup, cache, [x])
    return x, math.exp(x) * cache[x]


def _refine(setup, cache, tol_i):
    """구간 이분(Richardson 오차 예산 비례). -> (받아들인 구간 오차 합, 이분 상한에서 예산을 못 맞추고 받은 오차 합)(I 단위)."""
    xs = sorted(cache)
    total_width = xs[-1] - xs[0]
    pending = list(zip(xs, xs[1:]))
    accepted, rounds, done, capped = 0.0, None, 0, 0.0
    while pending:
        lo = numpy.array([a for a, _b in pending])
        hi = numpy.array([b for _a, b in pending])
        mid = (lo + hi) / 2
        _evaluate(setup, cache, mid.tolist())
        s_lo, s_hi, s_mid = (numpy.array([cache[v] for v in arr.tolist()]) for arr in (lo, hi, mid))
        whole = _rule(lo, s_lo, hi, s_hi)[0]
        halves = _rule(lo, s_lo, mid, s_mid)[0] + _rule(mid, s_mid, hi, s_hi)[0]
        errors = numpy.abs(halves - whole)          # 세분(반 구간 합) 추정의 오차 ≤ 두 추정의 차이(점근적으로 차이/3 -- 추정이 낮게 잡히지 않게 상계로 쓴다)
        budgets = tol_i * (hi - lo) / total_width
        if rounds is None:                      # 이분 깊이 상한: ln f 축 폭이 그 축 값의 부동소수 해상도에 닿을 때까지
            rounds = k_max(max(total_width, 1.0), EPS * max(1.0, abs(xs[0]), abs(xs[-1])))
        pending = []
        for e, budget, a, m, b in zip(errors.tolist(), budgets.tolist(), lo.tolist(), mid.tolist(), hi.tolist()):
            if e <= budget:
                accepted += e
            elif done + 1 >= rounds:
                accepted += e
                capped += e
            else:
                pending.extend([(a, m), (m, b)])
        done += 1
    return accepted, capped


def _contrib(setup, fin):
    src = setup.sources
    total = fin["total"]
    rows = [(src.labels[n], (("flicker", float(fin["i_fl"][n])), ("share", float((fin["i_th"][n] + fin["i_fl"][n]) / total)),
                             ("thermal", float(fin["i_th"][n])))) for n in range(len(src.labels))]
    rows.extend((name, (("ktc", float(kt_c * t2)),)) for name, kt_c, t2, _d in fin["caps"])
    return tuple(rows)


def noise_integral(setup):
    cache = {}
    try:
        _precheck(setup)
        base, f_top = _base_grid(setup)
        _evaluate(setup, cache, base + [math.log(f_top)])
        if len(cache) <= 1:                     # 격자 점이 하나뿐이면 첫 분해능 추정 전에 한 걸음 올린다
            _evaluate(setup, cache, [max(cache) + OCTAVE])
        first = _final(setup, cache)
        # 분해능을 정할 수 있으면 그것이 적분 목표다. 정할 수 없으면(허용오차·불확실성 미정) 목표 없음 -- 꼬리는 기계 정밀도(sqrt(eps)·v)까지 올리고(로그 걸음이라 싸다),
        # 구간 이분은 한 번만 하며(값은 내되 분해능 None) 이분 오차는 detail 에 남는다
        known = bool(first["lut_v"])
        tol_v = first["lut_v"] if known else first["v"] * math.sqrt(EPS)
        tol_sq = tol_v * tol_v
        x_end, tail = _extend(setup, cache, max(cache), tol_sq)
        if tail > tol_sq:
            raise _Stop((Undefined(FIELD, "noise_tail_not_converged", "numeric",
                                   (("f_hi_hz", math.exp(x_end)), ("tail_bound_v2", tail), ("target_v2", tol_sq))),))
        quad, capped = _refine(setup, cache, 2 * first["v"] * tol_v)
        if capped > 0:
            raise _Stop((Undefined(FIELD, "noise_tail_not_converged", "numeric",
                                   (("quad_err_v2", float(quad)), ("unmet_err_v2", float(capped)), ("target_v", tol_v))),))
        fin = _final(setup, cache)
    except _Stop as stop:
        return NoiseAnalysis(undefined=stop.undefined)
    numeric = (quad + tail) / (2 * fin["v"])
    resolution = max(fin["lut_v"], numeric) if known else None          # 목표 없이 한 번만 이분했으면 수치 몫을 주장하지 않는다
    detail = (("device_v2", fin["i_dev"]), ("f_hi_hz", math.exp(x_end)),
              ("f_lo_hz", setup.noise.f_lo), ("ktc_v2", fin["i_ktc"] if fin["caps"] else None), ("mode", setup.mode),
              ("numeric_v", float(numeric)), ("points", fin["points"]), ("quad_err_v2", float(quad)), ("tail_v2", float(tail)))
    return NoiseAnalysis(out_int_vrms=fin["v"], resolution=resolution, contrib=_contrib(setup, fin), detail=detail)
