"""소신호 회로 -> 잡음원 표 (설계 41 §7.3 '잡음원', 단위 U8).

진입점: `noise_sources(ss, noise, parameters) -> NoiseSources`.

잡음원은 소자마다 하나이고 전류원으로 스탬프한다(단위 전류의 출력 전달은 `noise_transfer` 의 수반 풀이가 한 번에 준다):
* MOS: LUT 가 준 게이트 환산 전압 잡음 S_vg(f) = A/f^EF + B(V²/Hz)를 드레인 전류 잡음 gm²·S_vg 로 바꿔 drain-source 에 둔다(게이트-소스 전압원과
  드레인-소스 전류원은 같은 양 -- 41 §7.3). gm 은 이 계에 스탬프된 값(`MosSmallSignal.gm` = 봉인 동작점의 ID·gm/ID)이다. 열 성분 `thermal` = gm²·B,
  flicker 계수 `flicker` = gm²·A(주파수 f 에서 PSD = flicker/f^ef). B 미상이면 `thermal` NaN + 문제 `noise_thermal_unknown`, LUT 질의 실패면 둘 다 NaN +
  `noise_lut_query_failed`, 이 소자의 `NoiseDevice` 가 아예 없으면 `noise_device_missing`.
* 저항: 4kT/R(Johnson-Nyquist 단측 전류 PSD, kT = `NoiseInput.kt`). flicker 없음.
* 커패시터·이상 전류원: 잡음 없음(이상 전류원은 소신호 개방).

`parameters` = `ParameterSet`(같은 회로의 `lut_parameters`) -- 각 MOS 의 gm 파라미터 번호(`gm_param`)를 적어 둔다: S_k = gm²·B 가 gm 에 직접 의존하는
항을 분해능 전파가 따로 더하기 위해서다.
"""
import numpy

from .noise_types import NoiseSources

NOT_A_NUMBER = float("nan")
GM_PARAMETER = "gm"                         # metrics.lut_parameters.LUT_PARAMETERS 원소
CODE_THERMAL_UNKNOWN = "noise_thermal_unknown"
CODE_QUERY_FAILED = "noise_lut_query_failed"
CODE_DEVICE_MISSING = "noise_device_missing"
_COLUMNS = ("labels", "is_mos", "a", "b", "thermal", "flicker", "ef", "tol_thermal", "tol_flicker", "gm", "gm_param")


def _tolerance(value):
    return NOT_A_NUMBER if value is None else float(value)


def _mos_row(mos, device):
    """(thermal, flicker, ef, tol_thermal, tol_flicker, 문제 코드 또는 None)."""
    if device is None:
        return NOT_A_NUMBER, NOT_A_NUMBER, 1.0, NOT_A_NUMBER, NOT_A_NUMBER, CODE_DEVICE_MISSING
    if device.failure is not None:
        return NOT_A_NUMBER, NOT_A_NUMBER, 1.0, NOT_A_NUMBER, NOT_A_NUMBER, CODE_QUERY_FAILED
    square = mos.gm * mos.gm
    thermal = NOT_A_NUMBER if device.b is None else square * device.b
    code = CODE_THERMAL_UNKNOWN if device.b is None else None
    return (thermal, square * device.a, float(device.ef), _tolerance(device.tol_thermal), _tolerance(device.tol_flicker),
            code)


def noise_sources(ss, noise, parameters):
    circuit = ss.circuit
    devices = {d.name: d for d in noise.devices}
    gm_at = {mos_index: p for p, (mos_index, name) in enumerate(parameters.params) if name == GM_PARAMETER}
    rows, problems = [], {}
    for index, mos in enumerate(circuit.mos):
        thermal, flicker, ef, tol_th, tol_fl, code = _mos_row(mos, devices.get(mos.label))
        if code is not None:
            problems.setdefault(code, []).append(mos.label)
        rows.append((mos.label, True, mos.d, mos.s, thermal, flicker, ef, tol_th, tol_fl, mos.gm, gm_at.get(index, -1)))
    for res in circuit.resistors:
        rows.append((res.label, False, res.a, res.b, noise.kt * (2 * 2) / res.ohm, 0.0, 1.0, 0.0, 0.0, 0.0, -1))
    columns = list(zip(*rows)) if rows else [()] * len(_COLUMNS)
    labels, is_mos, a, b, thermal, flicker, ef, tol_th, tol_fl, gm, gm_param = columns
    return NoiseSources(
        tuple(labels), numpy.array(is_mos, dtype=bool), numpy.array(a, dtype=int), numpy.array(b, dtype=int),
        numpy.array(thermal, dtype=float), numpy.array(flicker, dtype=float), numpy.array(ef, dtype=float),
        numpy.array(tol_th, dtype=float), numpy.array(tol_fl, dtype=float), numpy.array(gm, dtype=float),
        numpy.array(gm_param, dtype=int), tuple(sorted((code, tuple(names)) for code, names in problems.items())))
