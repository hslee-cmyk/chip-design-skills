"""`ss_off_op`(device.off_op = OffOp(vgs, vds, vsb, w_key)) 정지 사유 · 부호 식 -- interface card 20261104-eo1r4-sf1l §4 '식'·'정지'
(T-O3·T-O3b).

oracle (손): 합성 단자 전압(레일 값, 0.25 V 간격 2진 분수 h = 0.25 = r4 VS 격자 간격)으로 vgs = p(Vg - Vs), vds = p(Vd - Vs), vsb = p(Vs - Vb) 를
손으로 셈한다 (p = +1 nmos, -1 pmos). 정지 표(위에서 아래로 첫 맞는 행): off_vgs_negative(vgs < 0) -> off_bulk_forward(junction_forward > 0,
식 max(0, -vsb, -(vds+vsb)), 경계 0 V, LUT 조회 전) -> off_outside_lut(그 밖 LUT 축 밖; vds < 0 ∧ vdb >= 0 포함).
모두 SealViolationError(CANDIDATE_FAILURE_CLASSES), `dict(exc.record.detail)["reason"]`, `exc.record.devices`.
off 소자 단자는 모두 레일(고정 넷)이라 회로의 다른 점에 영향이 없다. 정지하지 않는 사례는 ΔI = IDu·w/l 을 r4 해석식으로 확인한다.
미단언: `off_cols=1` 변형(VDS = 0 열 전류 0)의 vds = 0 소자 -- card 가 미측정이라 단언하지 않는다. 부분 스냅샷 내용은 단언하지 않는다.
"""
import pytest

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, SealViolationError

from .conftest import block_row, rel_close
from .off_cases import BASE_RAILS, build_case, circuit_a, evaluate, graph_field, i_off, i_off_at_vgs0_vsb0, off_entry, theta_a


def make(tmp, pins, rails=None, w_m=1e-6, l_m=1e-6, name="oo"):
    rails = dict(rails or {})
    sup = dict(BASE_RAILS)
    sup.update(rails)
    regs = {p[0]: off_entry(w_m, l_m) for p in pins}
    return build_case(tmp, circuit_a(list(pins), name=name, rails=tuple(sorted(rails))), regs, theta_a, rails=sup)


def lookups(case):
    return sum(v.hits + v.misses for _k, v in case.ctx.lut.memo.stats())


def stop(case):
    with pytest.raises(SealViolationError) as ei:
        evaluate(case)
    assert type(ei.value) in CANDIDATE_FAILURE_CLASSES
    return dict(ei.value.record.detail)["reason"], ei.value.record.devices


# ---- off_vgs_negative -----------------------------------------------------------------------------------------------

def test_off_op_vgs_negative_records_all_devices_and_computes_no_delta(tmp_path):
    pins = [("Moffa", "nmos", "vdd", "gnd", "vh", "gnd"),          # vgs = 0 - 0.5 = -0.5
            ("Moffb", "nmos", "vdd", "gnd", "vh", "gnd"),          # 같은 단자: 둘 다 기록
            ("Moffc", "nmos", "out", "gnd", "gnd", "gnd")]         # vgs = 0 : 정상(기록 안 됨)
    case = make(tmp_path, pins, {"vh": 0.5})
    reason, devices = stop(case)
    assert reason == "off_vgs_negative" and devices == ("Moffa", "Moffb")
    assert block_row(case.ctx.counters, "ss_off_op")[0] >= 1
    assert block_row(case.ctx.counters, "ss_off_delta")[0] == 0               # ΔI 계산 호출 0
    assert block_row(case.ctx.counters, "metrics_ss")[0] == 0


def test_off_op_pmos_vgs_negative(tmp_path):
    """pmos: vgs = -(Vg - Vs) = -(0.5 - 0.25)... 게이트가 source 보다 높으면 음수: gate vh(0.5), source vb(0.25) -> vgs = -0.25."""
    pins = [("Moff", "pmos", "gnd", "vh", "vb", "vdd")]
    reason, devices = stop(make(tmp_path, pins, {"vh": 0.5, "vb": 0.25}))
    assert reason == "off_vgs_negative" and devices == ("Moff",)


def test_off_op_vgs_exactly_zero_is_not_negative(tmp_path):
    # [A-88] drain 은 gnd 와 같은 0 V 의 다른 레일 vz (drain = source 같은 넷이면 S1 의 dc_self_loop 정지)
    case = make(tmp_path, [("Moff", "nmos", "vz", "gnd", "gnd", "gnd")], {"vz": 0.0})
    res = evaluate(case)
    assert res.snapshot.value("device", "Moff", "off_op").vgs == 0.0


# ---- 표 순서 ----------------------------------------------------------------------------------------------------------

def test_off_op_vgs_negative_outranks_bulk_forward(tmp_path):
    pins = [("Mx", "nmos", "gnd", "gnd", "vh", "vdd")]             # vgs = -0.5, vds = -0.5, vsb = 0.5 - 1.8 = -1.3 (순방향 max(1.3, 1.8) = 1.8)
    reason, _ = stop(make(tmp_path, pins, {"vh": 0.5}))
    assert reason == "off_vgs_negative"


def test_off_op_bulk_forward_outranks_outside_lut_and_costs_no_lookup(tmp_path):
    pins = [("Mx", "nmos", "vh", "gnd", "gnd", "vdd")]             # vgs = 0, vds = 0.5, vsb = -1.8 (VS 축 -0.5 아래 = 축 밖이기도 함, 순방향 1.8)
    case = make(tmp_path, pins, {"vh": 0.5})
    before = lookups(case)
    reason, devices = stop(case)
    assert reason == "off_bulk_forward" and devices == ("Mx",)
    assert lookups(case) == before                                  # LUT 조회 전에 걸린다


# ---- T-O3b 벌크 접합 경계 (h = 0.25) ----------------------------------------------------------------------------------

# (이름, 핀, 레일, 손계산 vgs/vds/vsb, 설명)
BULK_STOPS = [
    ("nmos_i", ("Mx", "nmos", "vh", "gnd", "gnd", "vb"), {"vh": 0.5, "vb": 0.25}),     # vgs 0, vds 2h = 0.5, vsb -h = -0.25 -> 순방향 0.25
    ("nmos_ii", ("Mx", "nmos", "gnd", "vdd", "vb", "vb"), {"vb": 0.25}),               # vgs 1.55, vds -h, vsb 0 (vdb = -h < 0) -> 0.25
    ("pmos_i", ("Mx", "pmos", "vq", "vs3", "vs3", "vh"), {"vq": 0.25, "vs3": 0.75, "vh": 0.5}),   # vgs 0, vds 2h, vsb = Vb - Vs = -h
    ("pmos_ii", ("Mx", "pmos", "vs3", "vh", "vh", "vh"), {"vh": 0.5, "vs3": 0.75}),    # vgs 0, vds = -(0.75 - 0.5) = -h, vsb 0 (vdb < 0)
]


@pytest.mark.parametrize("pin,rails", [(b[1], b[2]) for b in BULK_STOPS], ids=[b[0] for b in BULK_STOPS])
def test_off_op_bulk_forward_both_polarities(tmp_path, pin, rails):
    case = make(tmp_path, [pin], rails)
    before = lookups(case)
    reason, devices = stop(case)
    assert reason == "off_bulk_forward" and devices == ("Mx",)
    assert lookups(case) == before                                  # 축 안이어도 LUT 조회 전에 걸린다


@pytest.mark.parametrize("kind,pin,rails", [("nmos", ("Mx", "nmos", "vz", "gnd", "gnd", "gnd"), {"vz": 0.0}),
                                            ("pmos", ("Mx", "pmos", "vy", "vs3", "vs3", "vs3"), {"vy": 0.75, "vs3": 0.75})])
def test_off_op_bulk_boundary_zero_volt_is_not_a_stop(tmp_path, kind, pin, rails):
    """vsb = 0, vds = 0 (vdb = 0): 경계 0 V 정확히 -> 정지 아님. ΔI = IDu(0, 0, 0)·w/l = I0·w/l (VDS = 0 열 켜짐)."""
    case = make(tmp_path, [pin], rails, name="oo_b_" + kind)       # [A-88] drain 은 source 와 같은 전위의 다른 레일(vz = 0 V, vy = vs3 = 0.75 V; 1.8 V 는 최상위 레일 중복이라 쓰지 않는다)
    snap = evaluate(case).snapshot
    o = snap.value("device", "Mx", "off_op")
    assert (o.vgs, o.vds, o.vsb) == (0.0, 0.0, 0.0)
    dI = dict(graph_field(snap, "ss_off_delta").sources)["Mx"]
    assert rel_close(dI, i_off_at_vgs0_vsb0(kind, 0.0, 1e-6, 1e-6), 1e-9)


# ---- off_outside_lut -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("pin,rails", [
    (("Mx", "nmos", "vb", "vdd", "vh", "gnd"), {"vb": 0.25, "vh": 0.5}),            # vds = 0.25 - 0.5 = -h, vsb = 0.5 = 2h, vdb = h >= 0
    (("Mx", "pmos", "vr", "vs3", "vs3", "vbb"), {"vr": 1.0, "vs3": 0.75, "vbb": 1.25}),   # vds = -(1 - 0.75) = -h, vsb = Vb - Vs = 2h
], ids=["nmos", "pmos"])
def test_off_op_outside_lut_vds_negative_with_nonnegative_vdb(tmp_path, pin, rails):
    case = make(tmp_path, [pin], rails)
    reason, devices = stop(case)
    assert reason == "off_outside_lut" and devices == ("Mx",)


def test_off_op_outside_lut_axis_end(tmp_path):
    """vgs 가 VGS 축 끝(2.0) 밖: 게이트 레일 2.5 V, source gnd -> vgs = 2.5 (순방향 접합 아님)."""
    case = make(tmp_path, [("Mx", "nmos", "vz", "vg", "gnd", "gnd")], {"vg": 2.5, "vz": 0.0})
    reason, devices = stop(case)
    assert reason == "off_outside_lut" and devices == ("Mx",)


# ---- 부호 식: 정지하지 않는 점의 (vgs, vds, vsb) 와 ΔI ---------------------------------------------------------------------

@pytest.mark.parametrize("pin,rails,kind,point", [
    (("Mx", "nmos", "vdd", "vh", "vb", "gnd"), {"vh": 0.5, "vb": 0.25}, "nmos", (0.25, 1.55, 0.25)),
    (("Mx", "pmos", "vb", "vh", "vs3", "vdd"), {"vh": 0.5, "vb": 0.25, "vs3": 0.75}, "pmos", (0.25, 0.5, 1.05)),
], ids=["nmos", "pmos"])
def test_off_op_sign_formulas_and_delta_current(tmp_path, pin, rails, kind, point):
    """nmos: vgs = Vg - Vs = 0.5 - 0.25, vds = Vd - Vs = 1.8 - 0.25, vsb = Vs - Vb = 0.25 - 0.
    pmos: vgs = -(Vg - Vs) = -(0.5 - 0.75), vds = -(Vd - Vs) = -(0.25 - 0.75), vsb = -(Vs - Vb) = -(0.75 - 1.8)."""
    case = make(tmp_path, [pin], rails, name="oo_sign_" + kind)
    snap = evaluate(case).snapshot
    o = snap.value("device", "Mx", "off_op")
    assert rel_close(o.vgs, point[0], 1e-12) and rel_close(o.vds, point[1], 1e-12) and rel_close(o.vsb, point[2], 1e-12)
    dI = dict(graph_field(snap, "ss_off_delta").sources)["Mx"]
    assert rel_close(dI, i_off(kind, *point, 1e-6, 1e-6), 1e-9)
