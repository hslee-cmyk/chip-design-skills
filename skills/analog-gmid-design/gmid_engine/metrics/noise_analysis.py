"""입력 환산 잡음 metric -- 열잡음 평탄값·1/f corner·excess, 출력 적분으로의 분기 (설계 41 §7.1 표·§7.3 '입력 환산'·'산출', 단위 U8).

진입점: `noise_analysis(field, setup, memo) -> NoiseAnalysis`.

`field` = 레지스트리 필드 이름(`th_in_v2hz`·`fc_in_hz`·`excess_th`·`out_int_vrms`), `setup` = `NoiseSetup`, `memo` = 부르는 쪽이 한 계산 블록 안에서 넘기는 dict
(키 (계, 관측 행, 전달 뷰 열) -> 기준 계산 -- 같은 계산을 세 metric 이 공유한다). 예외를 던지지 않는다(정의 불가는 `NoiseAnalysis.undefined`).

* 입력 환산: S_in(f) = Σ_k |Z_k(jω)|²·S_k(f) / |H(jω)|², H = 선언된 전달 뷰의 전달함수(gain metric 과 같은 계·같은 열).
* `noise_th_in_v2hz` = Σ_k W_k·gm_k²·B_k = **열 성분만**(W_k = |Z_k/H|²), ω 는 f_lo(LUT 가 실측한 가장 낮은 잡음 주파수) -- 열 성분은 주파수 무관한 평탄값이라 하한 점에서
  잰다(오라클 `.noise` 가 f_lo 에서 재는 것과 같은 양).
* `noise_fc_in_hz`: 입력 환산 flicker 합 Q_fl(f) = Σ_k W_k(f)·gm_k²·A_k/f^EF_k 가 열잡음 평탄값 Q_th 와 같아지는 f. f_lo 에서 이미 Q_fl < Q_th 면 corner 가 LUT 하한 아래라
  `noise_fc_below_f_lo`. 위쪽은 f_lo·2^j 격자로 올라가며 첫 부호 변화 구간을 잡고(상한 = flicker 가 f^-EF 로 줄어드는 횟수 `k_max((Q_fl(f_lo)/Q_th)^(1/EF_min), 1)`),
  그 구간에서 ln f 의 1-D 근을 `bracket_root` 로 구한다. 격자 안에 근이 없으면 `noise_fc_not_found`.
* `noise_excess_th` = Q_th / Q_in,th, 분모 = 입력 셀 소자(`NoiseSetup.input_devices` -- S1v 전달 뷰의 첫 이득 블록 input 셀)만의 같은 열 성분 합(같은 LUT γ).
* 분해능(metrics §9와 같은 방식): LUT 파라미터 불확실성 Δp(`ParameterSet`)의 1차 최악 전파 Σ_p |∂q/∂p|·Δp(∂q/∂p = 수반 풀이 위 전달·H 미분 + S_k 의 gm 직접 의존,
  `noise_transfer`·`source_gradient`) + LUT 잡음 칸 허용오차 Σ_k tol_k·(그 성분)(열 성분은 ln B 면, flicker 는 ln S_vg(f_lo) 면의 상대 오차). corner 는 암시적 미분:
  δ ln f = (Σ|∂g/∂p|Δp + 허용오차 몫)/|∂ ln Q_fl/∂ ln f|, g = ln Q_fl − ln Q_th. 파라미터 불확실성이 미정이면 None.
* 소자별 기여 `contrib` = (이름, (flicker, share, thermal)) -- f_lo 에서 입력 환산한 V²/Hz 와 열 성분 몫.
"""
import math
import types

import numpy

from gmid_engine.sizing import bracket_root, k_max

from ._helpers_noise import source_gradient, weights
from .mna_types import Undefined
from .noise_integral import noise_integral
from .noise_transfer import noise_transfer
from .noise_types import NoiseAnalysis

FIELD_TH, FIELD_FC, FIELD_EXCESS, FIELD_OUT = "th_in_v2hz", "fc_in_hz", "excess_th", "out_int_vrms"
EPS = float(numpy.finfo(float).eps)


class _Stop(Exception):
    """계산 중단 -- ((코드, 범주, detail), ...) 를 들고 `noise_analysis` 가 받아 정의 불가로 낸다."""

    def __init__(self, reasons):
        super().__init__("noise_analysis stop")
        self.reasons = reasons


def _stop(code, category="definitional", **detail):
    raise _Stop(((code, category, tuple(detail.items())),))


def _checks(setup):
    src, noise = setup.sources, setup.noise
    out = [(code, "definitional", (("devices", names),)) for code, names in src.problems]
    if noise.f_lo is None:
        out.append(("noise_f_lo_undefined", "definitional", ()))
    if setup.column is None:
        out.append(("noise_transfer_view_missing", "definitional", ()))
    return tuple(out)


def _solve(setup, f, **options):
    src = setup.sources
    tr = noise_transfer(setup.system, setup.row, src.a, src.b, 2 * math.pi * numpy.asarray(f, dtype=float),
                        column=setup.column, **options)
    if tr.undefined:
        raise _Stop(tuple((u.code, u.category, u.detail) for u in tr.undefined))
    if (tr.h == 0).any():
        _stop("noise_transfer_zero", f_hz=float(numpy.min(f)))
    return tr


def _reference(setup, memo):
    """f_lo 의 수반 풀이 한 번 -> 열 성분 입력 환산."""
    key = (id(setup.system), setup.row, setup.column)
    if key not in memo:
        try:
            problems = _checks(setup)
            if problems:
                raise _Stop(problems)
            tr = _solve(setup, [setup.noise.f_lo], parameters=setup.parameters)
            w = weights(tr)[0]
            th = w * setup.sources.thermal
            memo[key] = {"tr": tr, "w": w, "th": th, "q": float(th.sum())}
        except _Stop as stop:
            memo[key] = stop.reasons
    hit = memo[key]
    if isinstance(hit, tuple):
        raise _Stop(hit)
    return hit


def _tolerance_sum(power, tol):
    """Σ_k power_k·tol_k -- power 가 0 인 성분은 tol 이 미정(NaN)이어도 0 을 더한다(그 성분은 값에 없다)."""
    return float(numpy.where(power > 0, power * tol, 0.0).sum())


def _lut_part(setup, gradient, tolerance):
    """Σ_p |g_p|Δp + 허용오차 몫, 불확실성이 미정이면 None."""
    if setup.parameters.undetermined or not numpy.isfinite(gradient).all() or not math.isfinite(tolerance):
        return None
    return float((numpy.abs(gradient) * setup.parameters.delta).sum() + tolerance)


def _contrib(setup, ref):
    src = setup.sources
    f_lo = setup.noise.f_lo
    flicker = ref["w"] * src.flicker / f_lo ** src.ef
    return tuple((src.labels[n], (("flicker", float(flicker[n])), ("share", float(ref["th"][n] / ref["q"])),
                                  ("thermal", float(ref["th"][n])))) for n in range(len(src.labels)) if ref["q"] > 0)


def _thermal(setup, ref):
    src = setup.sources
    gradient = source_gradient(ref["tr"], src.thermal, src)[0]
    res = _lut_part(setup, gradient, _tolerance_sum(ref["th"], src.tol_thermal))
    return NoiseAnalysis(th_in_v2hz=ref["q"], resolution=res, contrib=_contrib(setup, ref),
                         detail=(("f_lo_hz", setup.noise.f_lo),))


def _excess(setup, ref):
    src = setup.sources
    names = setup.input_devices
    if not names:
        _stop("noise_input_cell_undefined")
    mask = numpy.array([src.is_mos[n] and src.labels[n] in names for n in range(len(src.labels))])
    if not mask.any():
        _stop("noise_input_cell_not_in_circuit", devices=tuple(names))
    th_in = ref["th"] * mask
    q_in = float(th_in.sum())
    if not q_in > 0 or not ref["q"] > 0:
        _stop("noise_input_cell_noise_zero", devices=tuple(names))
    excess = ref["q"] / q_in
    grad = (source_gradient(ref["tr"], src.thermal, src)[0] / ref["q"]
            - source_gradient(ref["tr"], src.thermal * mask, src)[0] / q_in)
    share = ref["th"] / ref["q"] - th_in / q_in
    res = _lut_part(setup, grad, _tolerance_sum(numpy.abs(share), src.tol_thermal))
    return NoiseAnalysis(excess_th=excess, resolution=None if res is None else excess * res, contrib=_contrib(setup, ref),
                         detail=(("f_lo_hz", setup.noise.f_lo), ("input_cell", tuple(sorted(names)))))


def _flicker(setup, f, **options):
    """-> (NoiseTransfer, W (k, N), flicker PSD 계수 (k, N), Q_fl (k,))."""
    src = setup.sources
    f = numpy.asarray(f, dtype=float)
    tr = _solve(setup, f, **options)
    w = weights(tr)
    fl = src.flicker[None, :] / f[:, None] ** src.ef[None, :]
    return tr, w, fl, (w * fl).sum(axis=1)


def _bracket(setup, q_th, q_lo):
    src = setup.sources
    f_lo = setup.noise.f_lo
    ef_min = float(src.ef[src.flicker > 0].min())
    steps = k_max((q_lo / q_th) ** (1 / ef_min), 1.0)
    grid = f_lo * numpy.exp2(numpy.arange(1, steps + 1))
    q = _flicker(setup, grid)[3]
    g = numpy.log(q) - math.log(q_th)
    if not numpy.isfinite(g).all():
        _stop("noise_nonfinite_flicker")
    below = numpy.nonzero(g < 0)[0]
    if not below.size:
        _stop("noise_fc_not_found", f_max_hz=float(grid[-1]), ratio=float(q[-1] / q_th))
    j = int(below[0])
    return math.log(f_lo if j == 0 else grid[j - 1]), math.log(grid[j])


def _corner_resolution(setup, ref, f_c):
    src = setup.sources
    tr, w, fl, q = _flicker(setup, [f_c], parameters=setup.parameters, with_omega=True)
    q = float(q[0])
    z, h, dz, dh = tr.z[0], tr.h[0], tr.dz_dw[0], tr.dh_dw[0]
    h2 = abs(h) ** 2
    d_w = 2 * (numpy.conj(z) * dz).real / h2 - abs(z) ** 2 * 2 * (numpy.conj(h) * dh).real / (h2 * h2)
    slope = (tr.omegas[0] * float((d_w * fl[0]).sum()) - float((src.ef * w[0] * fl[0]).sum())) / q
    gradient = (source_gradient(tr, fl, src)[0] / q - source_gradient(ref["tr"], src.thermal, src)[0] / ref["q"])
    tolerance = _tolerance_sum(w[0] * fl[0], src.tol_flicker) / q + _tolerance_sum(ref["th"], src.tol_thermal) / ref["q"]
    part = _lut_part(setup, gradient, tolerance)
    if part is None or not slope:
        return None
    return float(f_c * part / abs(slope))


def _corner(setup, ref):
    src = setup.sources
    f_lo = setup.noise.f_lo
    if not ref["q"] > 0:
        _stop("noise_thermal_zero")
    fl0 = src.flicker / f_lo ** src.ef
    q_lo = float((ref["w"] * fl0).sum())
    if not q_lo > 0:
        _stop("noise_flicker_zero")
    if q_lo < ref["q"]:
        _stop("noise_fc_below_f_lo", f_lo_hz=f_lo, ratio=q_lo / ref["q"])
    f_c = f_lo
    if q_lo > ref["q"]:
        lo, hi = _bracket(setup, ref["q"], q_lo)
        x, _f_lo, _f_hi = bracket_root(lambda x: math.log(float(_flicker(setup, [math.exp(x)])[3][0])) - math.log(ref["q"]),
                                       lo, hi, EPS)
        if x is None:
            _stop("noise_fc_not_found", f_lo_hz=math.exp(lo), f_hi_hz=math.exp(hi))
        f_c = math.exp(x)
    return NoiseAnalysis(fc_in_hz=f_c, resolution=_corner_resolution(setup, ref, f_c),
                         detail=(("f_lo_hz", f_lo), ("q_flicker_f_lo", q_lo), ("q_thermal", ref["q"])))


_FLAT = types.MappingProxyType({FIELD_TH: _thermal, FIELD_EXCESS: _excess, FIELD_FC: _corner})


def noise_analysis(field, setup, memo):
    if field == FIELD_OUT:
        return noise_integral(setup)
    quantity = field
    try:
        return _FLAT[field](setup, _reference(setup, memo))
    except _Stop as stop:
        return NoiseAnalysis(undefined=tuple(Undefined(quantity, code, category, detail)
                                             for code, category, detail in stop.reasons))
