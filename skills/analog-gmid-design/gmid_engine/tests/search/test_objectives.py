"""CONTRACT r4 3.6 `objective_values(snapshot) -> Objectives`: 값은 `graph.metrics_dc` MetricBundle 에서, [U17 ①] gate_area_m2·b_P 는
같은 블록이 쓴 graph 필드 `gate_area_m2`·`power_resolution_w`(설계 40 v1.6 §2.4.7·§2.4.8)에서 읽는다. b_P = Σ_레일 |V_k|·tol_I,k
(tol_I,k = 채널 끝이 레일 k 인 MOS 의 dc_tol_v·dc_gm 최댓값, dc_gm = ID × 그 동작점 gm/ID), 합 0·행 없음 -> None.

기대값: 스냅샷 입력 열(dc_current_basis·dc_current·dc_rail_v·dc_op·dc_tol_v)로 test 가 KCL·전력·면적·b_P 를 직접 계산한다.
수동소자 값은 S2 필드 `device.passive_value`(§2.4.8) -- 손 값을 conftest `with_passive_value` 로 그 필드에 쓴 뒤 metrics_dc 를 부른다.
"""

import pytest

from gmid_engine.metrics import metrics_dc
from gmid_engine.search import Objectives, objective_values
from gmid_engine.sizing import DC_KEY, METRICS_KEY, size_and_seal

from .conftest import (PENDING, build_case, expected_objectives, circuit_c, circuit_n, circuit_p, theta_n, theta_p, theta_r4c,
                       with_passive_value)


def _run(case):
    """[XRUN-F1 card B C4·C6] 그 case 의 실행(커널 컨텍스트의 두 객체)."""
    return dict(donors=case.dc.donors, counters=case.dc.counters)


def _check(o, e, passive_area=0.0):
    assert isinstance(o, Objectives)
    assert o.power_w == pytest.approx(e["power"], rel=1e-12)
    assert [k for k, _ in o.per_rail] == [k for k, _ in e["per_rail"]]
    for (_, a), (_, b) in zip(o.per_rail, e["per_rail"]):
        assert a == pytest.approx(b, rel=1e-12, abs=1e-30)
    assert o.kcl_residual_a == pytest.approx(e["kcl"], abs=1e-18)
    assert o.gate_area_m2 == pytest.approx(e["gate_area"], rel=1e-12)
    assert o.area_m2 == pytest.approx(e["gate_area"] + passive_area, rel=1e-12)
    if e["bp"] is None:
        assert o.power_resolution_w is None
    else:
        assert o.power_resolution_w == pytest.approx(e["bp"], rel=1e-12)


def test_circuit_c_two_rails(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    ev = size_and_seal(case.dc, theta_r4c(i2=2e-5, y=0.6))
    snap = metrics_dc(with_passive_value(ev.snapshot, ()), (), **_run(case))
    e = expected_objectives(snap)
    o = objective_values(snap)
    _check(o, e)
    # 손 확인: P = 1.8 V × 20 µA (gnd 0 V), gnd 행 0 기여 -> b_P = 1.8·tol(M2)·gm(M2).
    assert o.power_w == pytest.approx(1.8 * 2e-5, rel=1e-12)
    assert o.passive_area_undeclared == () and o.passive_value_undetermined == ()


def test_resistor_circuit_bp_uses_only_mos_on_rails(tmp_path, lut_sealed):
    """회로 P: vdd 에 M1 채널, gnd 에는 R1 만 -> b_P = 1.8·tol(M1)·gm(M1)."""
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),),
                      rbounds=(1e3, 1e6))
    th = theta_p(case.dc)
    ev = size_and_seal(case.dc, th)
    snap = metrics_dc(with_passive_value(ev.snapshot, (("R1", th[("resistance", "R1")]),)), (), **_run(case))
    o = objective_values(snap)
    _check(o, expected_objectives(snap))
    assert o.power_resolution_w is not None and o.power_resolution_w > 0


def test_zero_volt_rail_only_gives_none(tmp_path, lut_sealed):
    """회로 N: 채널이 레일에 닿는 MOS 는 0 V gnd 의 M1 뿐 -> 합 0 -> b_P None."""
    case = build_case(tmp_path, circuit_n(), lut_sealed, elements=(("R1", "resistor", None),),
                      rbounds=(1e3, 1e6))
    th = theta_n(case.dc)
    ev = size_and_seal(case.dc, th)
    snap = metrics_dc(with_passive_value(ev.snapshot, (("R1", th[("resistance", "R1")]),)), (), **_run(case))
    o = objective_values(snap)
    assert o.power_resolution_w is None
    assert o.power_w == pytest.approx(expected_objectives(snap)["power"], rel=1e-12)


def test_passive_without_value_is_undetermined(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, elements=(("CL", "capacitor", PENDING),))
    ev = size_and_seal(case.dc, theta_r4c())
    o = objective_values(metrics_dc(with_passive_value(ev.snapshot, ()), (), **_run(case)))
    assert o.passive_value_undetermined == ("CL",)


def test_passive_with_value_but_no_unit_area_is_undeclared(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, elements=(("CL", "capacitor", 1e-12),))
    ev = size_and_seal(case.dc, theta_r4c())
    snap = metrics_dc(with_passive_value(ev.snapshot, (("CL", 1e-12),)), (), **_run(case))
    o = objective_values(snap)
    assert o.passive_area_undeclared == ("CL",)
    assert o.passive_value_undetermined == ()
    _check(o, expected_objectives(snap))          # 단위 면적 None -> 면적에 수동소자 0 기여


def test_requires_metrics_dc_field(tmp_path, lut_sealed):
    """r4: 값은 metrics_dc 필드에서만 읽는다(다시 계산하지 않는다) -- 필드 없는 스냅샷은 거부."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    ev = size_and_seal(case.dc, theta_r4c())
    with pytest.raises((ValueError, KeyError, LookupError)):
        objective_values(ev.snapshot)


# ===========================================================================
# [U17 ①] `gate_area_m2`·`power_resolution_w` = metrics_dc 가 쓰는 graph 필드, search 는 다시 계산하지 않는다
# (설계 40 v1.6 §2.4.7 `Objectives` 행, §2.4.8 소유표 '게이트 면적·전력 분해능 | graph/metrics: gate_area_m2, power_resolution_w |
# metrics_dc', §2.4.11, §11 U17 ① 'search/objectives.py 의 _power_resolution·gate_area_m2 계산 삭제').
#
# 필드 위치: 소유표 표기 `graph/metrics: <필드>` = (kind graph, key METRICS_KEY, field). 값의 정의:
# - gate_area_m2 = Σ dc_op W·L (§2.4.7).
# - power_resolution_w = b_P = Σ_레일 |V_k|·tol_I,k, tol_I,k = 채널 끝이 레일 k 인 MOS 의 dc_tol_v × dc_gm 최댓값(§2.4.7 이 적은
#   읽기 목록 dc_gm·dc_tol_v·dc_current_basis·dc_rail_v, §2.4.11 'b_P 가 dc_gm 필드를 읽는다', 식의 모양은 이 파일 머리의 r4 3.6 정의).
#   합 0·행 없음 -> None(r4 3.6).
# 기대값: dc_gm 은 sizing conftest `hand_dc_gm`(LUT 파일 직접 읽기), 나머지는 스냅샷 입력 열(dc_op 좌표·W·L, dc_tol_v, 기저, 레일).
# 평가는 search `evaluate`(봉인 점·봉인 전 점 두 경로 모두 metrics_dc 를 부른다)로 만든다 -- metrics_dc 의 호출 서명은 이 변경에서
# 바뀔 수 있어(수동소자 값이 필드가 됨) 직접 부르지 않는다.
# ===========================================================================

@pytest.fixture(scope="module")
def obj_luts(tmp_path_factory):
    """r4 toy LUT 두 벌(봉인 점 / 봉인 7 undefined) -> {이름: (LutSet, 폴더)}. 폴더의 npz 를 기대값 계산이 직접 연다."""
    from .conftest import write_r4_lut
    a = tmp_path_factory.mktemp("u17_obj_sealed")
    b = tmp_path_factory.mktemp("u17_obj_pending")
    return {"sealed": (write_r4_lut(a), a), "pending": (write_r4_lut(b, vdsat=()), b)}


def _hand_fields(snap, root):
    from sizing.conftest import hand_dc_gm, r4_npz
    ops = dict(snap.column("device", "dc_op"))
    tol = dict(snap.column("device", "dc_tol_v"))
    gm = {m: hand_dc_gm(lambda kind: r4_npz(root, kind), o) for m, o in ops.items()}
    basis = snap.value("graph", DC_KEY, "dc_current_basis")
    bp, rows = 0.0, False
    for rail, v in snap.column("node", "dc_rail_v"):
        cands = [tol[el] * gm[el] for el, a, b in basis.ends if el in ops and rail in (a, b) and tol.get(el) is not None]
        if cands:
            rows = True
            bp += abs(v) * max(cands)
    return sum(o.W * o.L for o in ops.values()), (bp if rows and bp != 0 else None)


@pytest.mark.parametrize("which", ["sealed", "pending"])
def test_metrics_dc_writes_gate_area_and_power_resolution_fields(tmp_path, obj_luts, which):
    """§2.4.8: 설계점 스냅샷에 graph/metrics 필드 gate_area_m2·power_resolution_w 가 있고 writer 는 metrics_dc, 값은 손계산과 같다.
    회로 C 손 확인: 레일 vdd 1.8 V 에 채널이 닿는 MOS 는 M2, gnd 0 V 는 기여 0 -> b_P = 1.8·tol_V(M2)·dc_gm(M2)."""
    from gmid_engine.search import STATUS_PENDING_SEAL7, STATUS_SEALED, evaluate
    from gmid_engine.sizing import S2_WRITERS
    from .conftest import CELLS_C
    lut, root = obj_luts[which]
    case = build_case(tmp_path, circuit_c(), lut)
    r = evaluate(case.sctx, tuple(sorted(theta_r4c(i2=2e-5, y=0.6).items())), CELLS_C)
    assert r.status == (STATUS_SEALED if which == "sealed" else STATUS_PENDING_SEAL7)
    snap = r.evaluation.snapshot
    assert S2_WRITERS.writer_of("graph", "gate_area_m2") == "metrics_dc"
    assert S2_WRITERS.writer_of("graph", "power_resolution_w") == "metrics_dc"
    gate = snap.value("graph", METRICS_KEY, "gate_area_m2")
    bp = snap.value("graph", METRICS_KEY, "power_resolution_w")
    want_gate, want_bp = _hand_fields(snap, root)
    assert gate == pytest.approx(want_gate, rel=1e-12)
    assert want_bp is not None and bp == pytest.approx(want_bp, rel=1e-9), (bp, want_bp)
    tolv = dict(snap.column("device", "dc_tol_v"))
    from sizing.conftest import hand_dc_gm, r4_npz
    m2 = dict(snap.column("device", "dc_op"))["M2"]
    assert want_bp == pytest.approx(1.8 * tolv["M2"] * hand_dc_gm(lambda kind: r4_npz(root, kind), m2), rel=1e-12)
    # 목적 값은 필드 값 그대로(비트 동일) -- search 가 같은 값을 다시 계산해 따로 들고 있지 않다
    assert r.objectives.gate_area_m2 == gate and r.objectives.power_resolution_w == bp


def test_objective_values_reads_fields_not_recomputed(tmp_path, obj_luts):
    """§2.4.7 'search 의 재계산(_power_resolution)을 지운다': 권한표 writer(metrics_dc)로 두 필드만 다른 값으로 다시 쓴 스냅샷을
    objective_values 에 주면 다시 쓴 값이 그대로 나온다(dc_op·dc_tol_v·dc_gm 은 그대로이므로 search 가 다시 계산했다면 옛 값이 나온다)."""
    from gmid_engine.search import evaluate
    from .conftest import CELLS_C
    lut, _root = obj_luts["sealed"]
    case = build_case(tmp_path, circuit_c(), lut)
    r = evaluate(case.sctx, tuple(sorted(theta_r4c().items())), CELLS_C)
    snap = r.evaluation.snapshot
    gate = snap.value("graph", METRICS_KEY, "gate_area_m2")
    bp = snap.value("graph", METRICS_KEY, "power_resolution_w")
    moved = snap.write("metrics_dc", "u17_tampered", {("graph", "gate_area_m2"): {METRICS_KEY: 3.0 * gate},
                                                      ("graph", "power_resolution_w"): {METRICS_KEY: 5.0 * bp}})
    o = objective_values(moved)
    assert o.gate_area_m2 == 3.0 * gate
    assert o.power_resolution_w == 5.0 * bp
