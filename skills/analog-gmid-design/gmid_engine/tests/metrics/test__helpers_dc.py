"""`_helpers_dc.dc_limit_parts` (비공개 -- ω → 0 극한 식 행렬·우변·전하 주입 열, `dc_limit`·`sensitivity` 공용) -- metrics CONTRACT 3.3·9.2.

비공개 helper 라 공개 경로(`solve_dc_limit`·`response_sensitivity` 의 ω = 0)로 확인한다. 두 소비자가 같은 극한 식을 쓰는지(값 비트 동일),
그 식이 3.3 전하 보존 극한인지(test 쪽 독립 극한 `ref_system(omega=0)` 대조), 그리고 극한 식의 미분 규칙(9.2: 용량 전용 노드 행은
C 항목만, 나머지 행은 G 항목만)을 본다.
"""
from __future__ import annotations

import numpy as np
import pytest

from gmid_engine.metrics import (
    Excitation,
    LoopCut,
    Sense,
    build_mna,
    cut_circuit,
    lut_parameters,
    response_sensitivity,
    solve_dc_limit,
)

from .conftest import (
    EPS,
    EX2D,
    EX7_CAP,
    EX7_MOS12,
    EX7V_CAP,
    EX7V_MOS,
    FD_H,
    FD_RTOL,
    MILLER_V_MOS,
    MOS_IX,
    central_diff,
    circuit12,
    codes,
    columns_of,
    miller_v_system,
    mos_t,
    ref_system,
    senses_of,
)

VALUE_RTOL = 1e-9          # 독립 극한 식 대 엔진: 후방 안정 풀이 두 개, cond ≤ 1e6 의 작은 계 -> cond·n·eps 규모


def _cut(mos, cap):
    ck = circuit12(mos, (), cap)
    cut = cut_circuit(ck, (LoopCut("capacitor", 1, "b"),))
    sysm = build_mna(cut.circuit, cut.excitations, cut.senses)
    ref = dict(mos=mos, res=(), cap=(cap[0], (2, 4, cap[1][2]), cap[2]), ac_ground=(0,),
               columns=columns_of(cut.excitations), senses=senses_of(cut.senses))
    return ck, sysm, ref


def _ex2c():
    ck = circuit12((), (), ((2, 3, 1e-12), (3, 0, 3e-12)))
    sysm = build_mna(ck, (Excitation("vfb", voltages=((2, 1.0),)),), (Sense(3),))
    return ck, sysm, dict(mos=(), res=(), cap=((2, 3, 1e-12), (3, 0, 3e-12)), ac_ground=(0,),
                          columns=({"v": {2: 1.0}, "i": {}, "q": {}},), senses=((3, None),))


def _ex2d_gate_caps():
    """예 2d + gate(용량 전용 노드 3)의 cgs·음의 cgb·cgd -- 전하 분배가 MOS 용량에 의존한다."""
    p = EX2D
    mos = (mos_t(2, 3, 0, 0, p["gm"], 0.0, p["gds"], cgs=0.4e-12, cgd=0.1e-12, cgb=-0.05e-12),)
    cap = ((2, 3, p["cf"]), (3, 1, p["cs"]), (2, 0, p["cl"]))
    ck = circuit12(mos, (), cap)
    sysm = build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)), Excitation("iinj", currents=((3, 1.0),))), (Sense(2),))
    return ck, sysm, dict(mos=mos, res=(), cap=cap, ac_ground=(0,),
                          columns=({"v": {1: 1.0}, "i": {}, "q": {}}, {"v": {}, "i": {3: 1.0}, "q": {}}),
                          senses=((2, None),))


CASES = {"ex2c": _ex2c, "ex2d_gate_caps": _ex2d_gate_caps, "ex7_cut": lambda: _cut(EX7_MOS12, EX7_CAP),
         "ex7v_cut": lambda: _cut(EX7V_MOS, EX7V_CAP)}


@pytest.mark.parametrize("case", sorted(CASES))
def test_dc_limit_shared_by_both_consumers(case):
    """같은 극한 식: response_sensitivity(ω = 0).values == solve_dc_limit.values (비트, NaN 위치 포함), 그리고 그 값 = 독립 극한 식."""
    ck, sysm, ref = CASES[case]()
    ps = lut_parameters(ck, tuple(0.02 for _ in ck.mos))
    s = response_sensitivity(sysm, ps, 0.0)
    dl = solve_dc_limit(sysm)
    assert np.array_equal(np.asarray(s.values), np.asarray(dl.values), equal_nan=True)
    assert codes(s.undefined) == codes(dl.undefined)
    exp = ref_system(omega=0.0, **ref)
    v = np.asarray(s.values)
    fin = np.isfinite(exp)
    assert np.array_equal(fin, np.isfinite(v))
    scale = np.broadcast_to(np.nanmax(np.where(fin, np.abs(exp), 0.0), axis=0, keepdims=True), exp.shape)
    assert np.all(np.abs(v[fin] - exp[fin]) <= VALUE_RTOL * scale[fin])


def test_charge_node_row_uses_capacitive_entries_at_dc():
    """9.2 극한 식의 미분: 용량 전용 노드(gate 3) 행의 C 항목이 ω = 0 민감도에 든다 -- gate 용량(cgs·cgb·cgd)의 DC 민감도 ≠ 0 이고
    독립 극한 식의 중심 차분과 같다(vin 열; iinj 열은 dc_charge_injection 이라 NaN)."""
    ck, sysm, ref = _ex2d_gate_caps()
    ps = lut_parameters(ck, (0.02,))
    d = np.asarray(response_sensitivity(sysm, ps, 0.0).d_param)
    V = ref_system(omega=0.0, **ref)
    for i, (k, name) in enumerate(ps.params):
        p = ref["mos"][k][MOS_IX[name]]
        fd = central_diff(ref["mos"], k, name, lambda m: ref_system(**dict(ref, mos=m), omega=0.0))
        eng, exp = d[i, 0, 0] * p, fd[0, 0] * p
        floor = 3 * EPS / FD_H * abs(V[0, 0])
        assert abs(eng - exp) <= FD_RTOL * max(abs(eng), abs(exp)) + floor, (name, eng, exp)
        if name in ("cgs", "cgd", "cgb"):
            assert abs(eng) > floor, name                 # 공허하지 않은 비교
        assert np.all(np.isnan(d[i, :, 1]))


def test_conductive_rows_ignore_capacitive_entries_at_dc():
    """전용 노드가 없는 계(Miller 변형)의 ω = 0: 모든 행이 G 행 -> 용량 파라미터의 DC 민감도는 정확히 0, 컨덕턴스 몫은 ≠ 0."""
    ck, sysm = miller_v_system()
    ps = lut_parameters(ck, (0.01, 0.03))
    d = np.asarray(response_sensitivity(sysm, ps, 0.0).d_param)
    for i, (k, name) in enumerate(ps.params):
        if name in ("cgs", "cgd", "cgb"):
            assert np.all(d[i] == 0.0), (k, name)
    gm_rows = [i for i, (k, name) in enumerate(ps.params) if name in ("gm", "gds")]
    assert all(np.all(np.abs(d[i]) > 0.0) for i in gm_rows)
    assert len(MILLER_V_MOS) == 2
