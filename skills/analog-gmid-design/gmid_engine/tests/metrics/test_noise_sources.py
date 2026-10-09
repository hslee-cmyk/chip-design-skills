"""[U8 2026-10-09] `noise_sources(ss, noise, parameters)` -- 잡음원 표 (설계 41 §7.3 '잡음원', metrics CONTRACT 10.1).

oracle:
* (a) 구성: MOS 열 성분 = gm²·B, flicker 계수 = gm²·A(주파수 f 에서 gm²A/f^EF), 전류는 drain-source(a = d, b = s), 저항 = 단측 4kT/R(Johnson-Nyquist),
  커패시터는 잡음원 없음. gm 은 스탬프된 소신호 값. kT = 이 test 가 정한 NoiseInput.kt.
* (d) 계약 10.1·10.3: B 미상 -> thermal NaN + `noise_thermal_unknown`, LUT 질의 실패 -> 둘 다 NaN + `noise_lut_query_failed`, NoiseDevice 없음 ->
  `noise_device_missing`. gm_param = ParameterSet 의 (MOS 순번, "gm") 번호.
"""
import math

import numpy as np

from gmid_engine.metrics import NoiseSources, lut_parameters, noise_sources

from .noise_cases import KT, Case, dev, noise_input

GM1, GM2, R1 = 1e-3, 3e-4, 5e3
A1, B1, A2, B2 = 2e-12, 1e-16, 7e-13, 4e-16


def _case():
    return Case(mos=(("M1", "out", "in", "gnd", "gnd", GM1, 1e-6), ("M2", "out", "pb", "vdd", "vdd", GM2, 2e-6)),
                res=(("R1", "out", "gnd", R1),), cap=(("CL", "out", "gnd", 1e-12),), ground=("gnd", "vdd", "pb"))


def _run(devices, rel_tol=0.01):
    case = _case()
    ss = case.ss()
    params = lut_parameters(ss.circuit, tuple(rel_tol for _ in ss.circuit.mos))
    return case, params, noise_sources(ss, noise_input(devices), params)


def test_values_and_orientation():
    case, params, src = _run((dev("M1", a=A1, b=B1, ef=0.84, tol_flicker=0.1, tol_thermal=0.2),
                              dev("M2", a=A2, b=B2, ef=1.0)))
    assert isinstance(src, NoiseSources)
    assert src.labels == ("M1", "M2", "R1")                       # 커패시터는 잡음원이 아니다
    assert list(src.is_mos) == [True, True, False]
    ix = case.ix
    assert (int(src.a[0]), int(src.b[0])) == (ix["out"], ix["gnd"])   # MOS: drain -> source
    assert (int(src.a[1]), int(src.b[1])) == (ix["out"], ix["vdd"])
    assert {int(src.a[2]), int(src.b[2])} == {ix["out"], ix["gnd"]}
    np.testing.assert_allclose(src.thermal, [GM1 ** 2 * B1, GM2 ** 2 * B2, 4 * KT / R1], rtol=1e-14)
    np.testing.assert_allclose(src.flicker, [GM1 ** 2 * A1, GM2 ** 2 * A2, 0.0], rtol=1e-14)
    np.testing.assert_allclose(src.ef[:2], [0.84, 1.0])
    np.testing.assert_allclose(src.gm, [GM1, GM2, 0.0])
    assert src.tol_thermal[0] == 0.2 and src.tol_flicker[0] == 0.1
    assert math.isnan(src.tol_thermal[1]) and math.isnan(src.tol_flicker[1])      # 미정 = NaN(0 으로 두지 않는다)
    assert src.tol_thermal[2] == 0.0 and src.tol_flicker[2] == 0.0                 # 저항 4kT/R 은 LUT 불확실성 없음
    assert src.problems == ()
    gm_at = {m: p for p, (m, name) in enumerate(params.params) if name == "gm"}
    assert list(src.gm_param) == [gm_at[0], gm_at[1], -1]


def test_problem_codes():
    _case_, _p, src = _run((dev("M1", a=A1, b=None), dev("M2", failure="lut_l_out_of_range")))
    assert math.isnan(src.thermal[0]) and src.flicker[0] == GM1 ** 2 * A1
    assert math.isnan(src.thermal[1]) and math.isnan(src.flicker[1])
    assert dict(src.problems) == {"noise_thermal_unknown": ("M1",), "noise_lut_query_failed": ("M2",)}
    _c, _p, src = _run((dev("M1", a=A1, b=B1),))
    assert dict(src.problems) == {"noise_device_missing": ("M2",)}


def test_resistor_kt_follows_noise_input():
    """4kT/R 의 kT 는 NoiseInput.kt(LUT 측정 온도) 그대로 -- 온도를 바꾸면 비례한다. oracle (a)."""
    case = _case()
    ss = case.ss()
    params = lut_parameters(ss.circuit, (0.01, 0.01))
    devices = (dev("M1", a=A1, b=B1), dev("M2", a=A2, b=B2))
    hot = noise_sources(ss, noise_input(devices, kt=2 * KT), params)
    assert hot.thermal[2] == 4 * (2 * KT) / R1
