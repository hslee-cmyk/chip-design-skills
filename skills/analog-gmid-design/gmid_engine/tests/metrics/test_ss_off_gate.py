"""`off_region_gate(snapshot, lut) -> None` -- interface card 20261104-eo1r4-sf1l §4 '관문' (T-G1~T-G6, T-G3 호출 순서).

입력: 합성 회로(off 소자 하나를 harmless 하게 단 A·S·P)를 `ss_evaluate` 로 끝까지 돌려 `graph.ss_off_delta` 가 있는 스냅샷을 얻고,
그 위에서 (1) `device.dc_op` 의 M1 점을 conftest `tamper` 꼴로 정하고 (2) `graph.ss_off_delta.node_dv` 를 합성 값으로 다시 쓴다(필드 직접 주입).
관문은 그 두 입력만 읽는다. 값은 2진 분수라 s′ 가 부동소수 정확하다.
oracle (손): VDSAT 열 = sizing conftest 의 r4 해석식 VDSAT = c0 + c1·VGS + c2·VGS² + cs·VS + cl·(L 인덱스), VDS 무관 -> a2 = 0.
  nmos(c0 .0625, c1 .25, c2 .25, cs .125, cl .0625), pmos(.125, .25, .5, .0625, .125). 격자 VGS 간격 .125, VS 간격 .25 (조각 선형).
  card §4 닫힌 식 s′ = s + (1 − a2)·ΔVDS − a1·ΔVGS − a3·ΔVSB, VDS′ = VDS + ΔVDS, VDSAT′ = VDSAT + Σ_X [vdsat(X+ΔX) − vdsat(X)].
거부 = SealViolationError(reason off_gate, detail s_prime = ((소자, s′), ...), OUT_OF_DOMAIN 이면 s′ = None).
단언 금지: 블록 내부 호출 인자, magnitude·tol·margin.
"""
import dataclasses
import math

import pytest

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, SealViolationError
from gmid_engine.metrics import OffDelta, off_region_gate

from sizing.conftest import tamper                              # 필드 직접 주입 꼴

from .conftest import block_row
from .off_cases import (build_case, circuit_a, circuit_p, circuit_s, evaluate, graph_key_of, off_entry,
                        theta_from_schema, tri_entry)

IN_OFF = [("Moff", "nmos", "out", "gnd", "gnd", "gnd")]          # vgs = 0, drain 만 out: ΔI 가 작아 harmless


def _theta_a(vout_drop=9e4, i=1e-5, vgs=0.6):
    def fn(ctx):
        vout = 1.8 - i * vout_drop
        return theta_from_schema(ctx, {"M1": ("nmos", vgs, vout, 0.0)}, {"R1": i, "M1": i}, {"R1": vout_drop})
    return fn


def _case_a(tmp, triode=False):
    topo, regions = circuit_a(IN_OFF, name="gate_a" + ("t" if triode else "")), {"Moff": off_entry()}
    if triode:
        regions["M1"] = tri_entry()
        return build_case(tmp, topo, regions, _theta_a(vout_drop=1.62e5))           # V(out) = 0.18 < vdsat 0.30 -> triode
    return build_case(tmp, topo, regions, _theta_a())


def _snap(case):
    res = evaluate(case)
    return res.snapshot


def _ops(snap):
    return dict(snap.column("device", "dc_op"))


def put(snap, **m1):
    """M1 의 dc_op 점을 정해 넣는다(벌크 등 나머지는 그대로)."""
    op = _ops(snap)["M1"]
    return tamper(snap, "dc_widths", "device", "dc_op", {"M1": dataclasses.replace(op, **m1)},
                  version=snap.block_version("dc_widths"))


def dv(snap, **nets):
    """graph.ss_off_delta 의 node_dv 를 합성 값으로 다시 쓴다(소스 목록은 의미 없음 -- 관문은 node_dv 만 읽는다)."""
    key = graph_key_of(snap, "ss_off_delta")
    assert key is not None, "ss_off_delta 필드가 없다 -- off 소자가 있는 사례여야 한다"
    return snap.write("ss_off_delta", "inj:" + repr(sorted(nets.items())),
                      {("graph", "ss_off_delta"): {key: OffDelta(tuple(sorted(nets.items())), (("Moff", 0.0),))}})


def gate(case, snap):
    return off_region_gate(snap, case.ctx.lut)


def rejected(case, snap):
    with pytest.raises(SealViolationError) as ei:
        gate(case, snap)
    d = dict(ei.value.record.detail)
    assert d["reason"] == "off_gate" and type(ei.value) in CANDIDATE_FAILURE_CLASSES
    return ei.value.record.devices, dict(d["s_prime"])


def point_lookups(case):
    return sum(v.hits + v.misses for k, v in case.ctx.lut.memo.stats() if k == "point")


# ---- T-G1 선언 없는 소자: s > 0, s′ < 0 -> off_gate (nmos / pmos 부호), 닫힌 식 -------------------------------------

def test_off_gate_undeclared_s_positive_to_negative_rejected_nmos(tmp_path):
    case = _case_a(tmp_path)
    snap = dv(put(_snap(case), vgs=0.5, vds=0.5, vsb=0.0), out=-0.5)          # s = 0.5 - 0.25 = 0.25, ΔVDS = -0.5 -> s′ = -0.25
    devices, sp = rejected(case, snap)
    assert devices == ("M1",) and sp == {"M1": -0.25}


def test_off_gate_closed_form_gate_and_vds_terms_nmos(tmp_path):
    """ΔVGS = +0.0625 (칸 [0.5, 0.625] 안: VDSAT 기울기 (0.31640625 - 0.25)/0.125 = 0.53125), ΔVDS = 0. 손계산 VDSAT′ = 0.283203125,
    VDS = 0.28125 -> s′ = 0.28125 - 0.283203125 = -1/512."""
    case = _case_a(tmp_path)
    snap = dv(put(_snap(case), vgs=0.5, vds=0.28125, vsb=0.0), **{"in": 0.0625})
    devices, sp = rejected(case, snap)
    assert sp == {"M1": -0.001953125}


def test_off_gate_closed_form_crosses_one_cell(tmp_path):
    """ΔVGS = +0.25 (0.5 -> 0.75, 격자점): vdsat(0.75) - vdsat(0.5) = 0.390625 - 0.25. VDS = 0.375 -> s′ = 0.375 - 0.390625."""
    case = _case_a(tmp_path)
    snap = dv(put(_snap(case), vgs=0.5, vds=0.375, vsb=0.0), **{"in": 0.25})
    _, sp = rejected(case, snap)
    assert sp == {"M1": -0.015625}


def test_off_gate_closed_form_piecewise_linear_inside_next_cell(tmp_path):
    """ΔVGS = +0.1875 (0.5 -> 0.6875, 칸 [0.625, 0.75] 중점): vdsat(0.6875) = (0.31640625 + 0.390625)/2 = 0.353515625. VDS = 0.34375."""
    case = _case_a(tmp_path)
    snap = dv(put(_snap(case), vgs=0.5, vds=0.34375, vsb=0.0), **{"in": 0.1875})
    _, sp = rejected(case, snap)
    assert sp == {"M1": -0.009765625}


def test_off_gate_closed_form_vsb_term_with_source_degeneration(tmp_path):
    """소스 노드가 움직이는 사례: ΔV_s = +0.0625 -> ΔVSB = +0.0625, ΔVGS = -0.0625(게이트 고정), ΔVDS = ΔV_d - ΔV_s = -0.25 (ΔV_d = -0.1875).
    VDSAT′ = 0.28125 + [vdsat(0.4375) - vdsat(0.5)] + cs·ΔVSB = 0.28125 - 0.029296875 + 0.0078125 = 0.259765625, VDS′ = 0.25 -> s′ = -0.009765625.
    (VDSAT 열은 VDS 무관이라 VDS 항 보정 0.)"""
    topo = circuit_s(IN_OFF)
    i, r1, rs = 1e-5, 8e4, 1e4
    vss = i * rs

    def th(ctx):
        return theta_from_schema(ctx, {"M1": ("nmos", 0.6, (1.8 - i * r1) - vss, vss)}, {"R1": i, "M1": i, "Rs": i},
                                 {"R1": r1, "Rs": rs})
    case = build_case(tmp_path, topo, {"Moff": off_entry()}, th,
                      elements=(("R1", "resistor", None), ("Rs", "resistor", None), ("CL", "capacitor", 1e-12)))
    snap = dv(put(_snap(case), vgs=0.5, vds=0.5, vsb=0.25), ss=0.0625, out=-0.1875)
    _, sp = rejected(case, snap)
    assert sp == {"M1": -0.009765625}


def test_off_gate_pmos_sign(tmp_path):
    """pmos: ΔVDS = p(ΔV_d - ΔV_s) = -ΔV_out. s = VDS - VDSAT = 0.5 - 0.375 = 0.125 (pmos L=1µm, VGS 0.5: 0.125 + 0.125 + 0.125).
    ΔV_out = +0.25 -> s′ = -0.125 거부, +0.125 -> s′ = 0 통과, -0.25 -> s′ = +0.375 통과(부호가 반대면 반대로 나온다)."""
    pin = [("Moff", "pmos", "out", "vdd", "vdd", "vdd")]

    def th(ctx):
        i, r = 1e-5, 9e4
        return theta_from_schema(ctx, {"M1": ("pmos", 0.6, 1.8 - i * r, 0.0)}, {"R1": i, "M1": i}, {"R1": r})
    case = build_case(tmp_path, circuit_p(pin), {"Moff": off_entry()}, th)
    base = put(_snap(case), vgs=0.5, vds=0.5, vsb=0.0)
    _, sp = rejected(case, dv(base, out=0.25))
    assert sp == {"M1": -0.125}
    assert gate(case, dv(base, out=0.125)) is None
    assert gate(case, dv(base, out=-0.25)) is None


# ---- T-G2 경계 s′ = 0 --------------------------------------------------------------------------------------------

def test_off_gate_s_prime_exactly_zero_passes_and_one_ulp_below_rejects(tmp_path):
    case = _case_a(tmp_path)
    base = put(_snap(case), vgs=0.5, vds=0.5, vsb=0.0)                      # s = 0.25
    assert gate(case, dv(base, out=-0.25)) is None                          # VDS′ = 0.25 = VDSAT -> s′ = 0 정확히 -> 통과
    below = -(0.25 + math.ulp(0.25))
    _, sp = rejected(case, dv(base, out=below))
    assert sp["M1"] < 0.0
    assert gate(case, dv(base, out=-(0.25 - math.ulp(0.25)))) is None       # 경계 위쪽


# ---- T-G4 (O-222) triode: s < 0 에서 ΔV 로 s′ >= 0 이 되면 거부 -----------------------------------------------------

def test_off_gate_triode_s_prime_zero_or_positive_rejected_negative_passes(tmp_path):
    case = _case_a(tmp_path, triode=True)
    base = put(_snap(case), vgs=0.5, vds=0.125, vsb=0.0)                    # s = 0.125 - 0.25 = -0.125 (triode)
    assert gate(case, dv(base, out=0.0625)) is None                         # s′ = -0.0625 < 0 통과
    assert gate(case, dv(base, out=-0.0625)) is None                        # s′ = -0.1875 통과
    _, sp0 = rejected(case, dv(base, out=0.125))                            # s′ = 0 정확히 -> 거부
    assert sp0 == {"M1": 0.0}
    _, sp1 = rejected(case, dv(base, out=0.25))                             # s′ = +0.125 거부
    assert sp1 == {"M1": 0.125}


# ---- T-G6 VDS < 0 --------------------------------------------------------------------------------------------------

def test_off_gate_triode_reverse_vds_stays_reverse_passes_and_zero_or_positive_rejects(tmp_path):
    case = _case_a(tmp_path, triode=True)
    base = put(_snap(case), vgs=0.5, vds=-0.25, vsb=0.0)
    before = point_lookups(case)
    assert gate(case, dv(base, out=0.125)) is None                          # VDS′ = -0.125 < 0 -> 표 행 4 통과
    assert point_lookups(case) == before                                    # 그 소자 vdsat 조회 0 (기준·보정 모두)
    _, sp0 = rejected(case, dv(base, out=0.25))                             # VDS′ = 0 정확히 -> 행 5 거부
    assert sp0 == {"M1": None}
    _, sp1 = rejected(case, dv(base, out=0.5))                              # VDS′ > 0 거부
    assert sp1 == {"M1": None}


def test_off_gate_forward_vds_to_reverse_undeclared_rejected_triode_passes(tmp_path):
    undeclared = _case_a(tmp_path / "u")
    base = put(_snap(undeclared), vgs=0.5, vds=0.125, vsb=0.0)
    devices, _ = rejected(undeclared, dv(base, out=-0.25))                  # VDS′ = -0.125 < 0 : 행 3 (mismatch)
    assert devices == ("M1",)
    tri = _case_a(tmp_path / "t", triode=True)
    base_t = put(_snap(tri), vgs=0.5, vds=0.125, vsb=0.0)
    assert gate(tri, dv(base_t, out=-0.25)) is None                         # 행 4 일치


def test_off_gate_correction_lookup_outside_axis_is_out_of_domain(tmp_path):
    """vgs 2.0 (VGS 축 끝) 에서 ΔVGS = +0.25 -> 보정 조회 vdsat(2.25) 축 밖 = OUT_OF_DOMAIN -> s′ None, 거부(행 5)."""
    case = _case_a(tmp_path)
    snap = dv(put(_snap(case), vgs=2.0, vds=1.75, vsb=0.0), **{"in": 0.25})
    devices, sp = rejected(case, snap)
    assert devices == ("M1",) and sp == {"M1": None}


# ---- T-G5 보정 조회 계수 -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("nets,extra", [({}, 0), ({"out": -0.0625}, 1), ({"out": -0.0625, "in": 0.0625}, 2)],
                         ids=["no_shift", "vds_only", "vds_and_vgs"])
def test_off_gate_zero_shift_terms_cost_no_lookup(tmp_path, nets, extra):
    """기준 VDSAT 조회 1 + ΔX != 0 인 항마다 1 (ΔX = 0 이면 조회 0). 통과하는 입력으로 센다(point 영역 hits + misses 증분)."""
    case = _case_a(tmp_path)
    base = dv(put(_snap(case), vgs=0.5, vds=1.0, vsb=0.0), **nets)
    before = point_lookups(case)
    assert gate(case, base) is None
    assert point_lookups(case) - before == 1 + extra


# ---- T-G3 파이프라인 안의 자리: 거부 때 metric·icm_config 호출 0, 부분 스냅샷 -------------------------------------------

def test_off_gate_pipeline_rejection_stops_before_metrics(tmp_path):
    """off 소자의 게이트가 전원이라 ΔI 가 거대하다(합성 입력: 선언은 사용자 몫, 엔진은 판정하지 않는다). 포화 M1 의 VDS′ < 0 -> 거부."""
    pin = [("Moff", "nmos", "out", "vdd", "gnd", "gnd")]
    case = build_case(tmp_path, circuit_a(pin, name="gate_pipe"), {"Moff": off_entry()}, _theta_a())
    assert case.sealed is not None
    with pytest.raises(SealViolationError) as ei:
        evaluate(case)
    assert dict(ei.value.record.detail)["reason"] == "off_gate" and ei.value.record.devices == ("M1",)
    calls = {n: block_row(case.ctx.counters, n)[0] for n in
             ("ss_off_op", "ss_dev", "ss_off_delta", "metrics_ss", "metrics_dc", "icm_config")}
    assert all(calls[n] >= 1 for n in ("ss_off_op", "ss_dev", "ss_off_delta")), calls
    assert calls["metrics_ss"] == 0 and calls["metrics_dc"] == 0 and calls["icm_config"] == 0, calls
