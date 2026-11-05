"""WB-1 `dc_solve` 블록 (interface card §3 D-1·D-2·D-4·D-5·D-9, §8 T-W1~4). 진입 = `size_and_seal`(공개 경로)과 conftest 보조.

oracle (손/식): 닫힌 r4 식(conftest `r4_ln_idu`, I0·B·C·LAM 상수 -- LUT 파일이 아니라 이 test 의 해석식)과 card §3 의 손 유도.
- D-1: 거울 회로. W = ID·L/IDu(IDu 는 슬라이스와 무관). M2 W ∈ (3.5, 4.5) µm -> 후보 (키 100, m = 4)·(키 200, m = 2), 곱이 400 으로
  같아 동률 -> 큰 키 200. M1 W ∈ [1, 1.5) µm -> (키 100, m = 1) 잔차 작음 vs (키 200, m = 1) 잔차 큼 -> 키 100.
- D-2: 관찰 stub (card §3 표). 미측정 회로 -- 전제가 깨지면 멈추고 보고.
- T-W: 순서 창 = 채널이 닿는 전도 MOS 의 V_DS >= 0 구간의 교집합(VDSAT·tol 읽기 0), 채널 소자 없으면 레일 범위.
"""
import importlib
import math

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, size_and_seal

from .conftest import (R4_L, R4_VDS, R4_VGS, R4_VS, build_ctx, build_ctx_u4, circuit_cs_pmos_load, circuit_mirror, free_currents,
                       kschema, mos, r4_ln_idu, theta_mirror, theta_r4c, topo, two, with_hand_ss)
from .wb1_toy import access_of, write_r4_bins_lut

GRID = 1e-8


def ops(ev):
    return dict(ev.snapshot.column("device", "dc_op"))


def fingers(ev):
    return dict(ev.snapshot.column("device", "dc_finger"))


def scc_log(ev):
    return ev.snapshot.value("graph", DC_KEY, "dc_scc_log")


@pytest.fixture(scope="module")
def two_slice_access(tmp_path_factory):
    lut, _, _ = write_r4_bins_lut(tmp_path_factory.mktemp("wb1_two"), widths=(1e-6, 2e-6))
    return access_of(lut)


def mirror_setup(tmp_path, access, w_m1=1.2e-6, w_m2=4e-6, vgs1=0.6, y=0.5, l=1e-6):
    """거울 회로 + θ. I1 은 W_M1 = w_m1 이 되게, M3 전류는 W_M2 = w_m2 가 되게 닫힌 식으로 정한다(r4 IDu, L 무관)."""
    idu_diode = math.exp(r4_ln_idu("nmos", vgs1, vgs1, 0.0))
    idu_m2 = math.exp(r4_ln_idu("nmos", vgs1, y * 1.8, 0.0))
    i1 = w_m1 * idu_diode / l
    i3 = w_m2 * idu_m2 / l
    ctx = build_ctx_u4(tmp_path, circuit_mirror(), access, element_values=(("I1", i1),))[1]
    th = theta_mirror(vgs1=vgs1, y=y, i=i3, l=(l, l, l))
    return ctx, th


# ---------------------------------------------------------------- D-1
def test_dc_solve_mirror_hand_picks_finger_slice(tmp_path, two_slice_access):
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    ev = size_and_seal(ctx, th)
    o, f = ops(ev), fingers(ev)
    w2 = o["M2"].W
    # 전제: W_M2 가 열린 구간 (3.5, 4.5) µm (손 유도의 가정)
    assert 3.5e-6 < w2 < 4.5e-6
    # op.W = I·L/IDu (닫힌 식; dc_finger 와 별개)
    want_w2 = o["M2"].current * o["M2"].L / math.exp(r4_ln_idu("nmos", o["M2"].vgs, o["M2"].vds, o["M2"].vsb))
    assert abs(w2 - want_w2) <= 1e-9 * want_w2
    # 손: 동률 -> 큰 키
    assert o["M2"].w_key == 200
    assert f["M2"].m == 2 and abs(f["M2"].w_f_m - 2e-6) <= 1e-12
    assert abs(f["M2"].residual - (4e-6 / w2 - 1.0)) <= 1e-12
    # M1: 키 100 m = 1
    w1 = o["M1"].W
    assert 1e-6 <= w1 < 1.5e-6
    assert o["M1"].w_key == 100 and f["M1"].m == 1 and abs(f["M1"].w_f_m - 1e-6) <= 1e-12
    assert abs(f["M1"].residual - (1e-6 / w1 - 1.0)) <= 1e-12
    # DeviceOp.w_key 와 dc_finger 가 같은 슬라이스를 가리킨다
    for m, fg in f.items():
        assert o[m].w_key == round(fg.w_f_m / GRID)
    assert [e.slice_rounds for e in scc_log(ev)] and all(e.slice_rounds == 1 for e in scc_log(ev))


def test_dc_solve_same_theta_bit_identical_and_parent_independent(tmp_path, two_slice_access):
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    a = size_and_seal(ctx, th)
    b = size_and_seal(ctx, th)
    assert a.snapshot.fp == b.snapshot.fp
    c = size_and_seal(ctx, th, parent=with_hand_ss(a))
    for kind, field in (("device", "dc_finger"), ("device", "dc_op"), ("node", "dc_v")):
        assert a.snapshot.column(kind, field) == c.snapshot.column(kind, field)
    assert len(a.snapshot.column("device", "dc_finger")) >= 1


# ---------------------------------------------------------------- D-5
def test_dc_solve_w_request_has_no_dc_finger_rows(tmp_path, two_slice_access):
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    free = size_and_seal(ctx, th)
    assert len(free.snapshot.column("device", "dc_finger")) >= 1                     # 탐색 평가에는 행이 있다
    req = size_and_seal(ctx, th, w_request={"M2": 1.05 * mirror_w_nat_of(ctx, th)})
    assert len(req.snapshot.column("device", "dc_finger")) == 0                      # 재봉인(geometry): 빈 열
    assert ops(req)["M2"].W == pytest.approx(1.05 * mirror_w_nat_of(ctx, th), rel=1e-12)


def mirror_w_nat_of(ctx, th):
    """W_nat(M2) = I·L/IDu(V(nb) = vgs(M1 좌표), V(out)) -- 닫힌 식, 입력은 θ."""
    ln_m1 = th[("ln_idu", "M1")]
    vgs1 = None
    # M1 좌표 ln IDu = r4_ln_idu(nmos, vgs1, vgs1, 0) 의 역: 이진 탐색(독립)
    lo, hi = 0.0, 1.8
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if r4_ln_idu("nmos", mid, mid, 0.0) > ln_m1:
            hi = mid
        else:
            lo = mid
    vgs1 = 0.5 * (lo + hi)
    y = th[("y", "out")]
    return th[("current", "M3")] * th[("L", "M2")] / math.exp(r4_ln_idu("nmos", vgs1, y * 1.8, 0.0))


# ---------------------------------------------------------------- D-4
def test_dc_solve_dependent_all_candidates_missing(tmp_path):
    # VDS 축 상한 1.0 인 LUT: 종속 소자 M2 의 VDS = V(out) = 0.9·1.8 = 1.62 가 축 밖 -> 모든 후보가 gap -> slice_missing
    grids = (R4_L, R4_VGS, R4_VDS[:5], R4_VS)
    lut, _, _ = write_r4_bins_lut(tmp_path / "lut", widths=(1e-6, 2e-6), grids=grids)
    access = access_of(lut)
    ok_ctx, ok_th = mirror_setup(tmp_path / "ok", access, y=0.5)                      # y = 0.5 -> VDS 0.9 축 안: 정상 (양성 대조)
    assert size_and_seal(ok_ctx, ok_th).snapshot is not None
    ctx, th = mirror_setup(tmp_path / "bad", access, y=0.9)
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    d = dict(ei.value.record.detail)
    assert d["reason"] == "slice_missing"                                           # lut_query_failed 로 바뀌지 않음
    assert ei.value.record.devices == ("M2",)
    assert d["kind"] == "nmos" and d["why"] == "no_candidate"
    assert tuple(d["excluded"]) == (100, 200)


# ---------------------------------------------------------------- D-2 (Rʳ ≠ ∅, 관찰 stub, 미측정)
def circuit_r_dep():
    """card §3 D-2 의 전제 '단일 순환 SCC {vin, vout} + Rʳ ≠ ∅' 를 만족하는 손 회로 (dispute 2 재유도).
    _scc_s_doc 와 같은 M1 nmos (vin, nb1, gnd), M2 nmos (vout, nb2, vin), M3 pmos (vout, pb, vdd). 옛 안은 M1 gate nb1 을 diode M0 + 이상 전류원으로 만들어 nb1 에
    1변수 순환 SCC 가 하나 더 생겼다(순환 SCC 둘). 여기서는 nb1 을 **선언 목표 전압**(spec 노드 목표 0.6 V, W3 `declared_target`)으로 둔다: nb1 은 순환에 들지 않고(고정 노드),
    M1 의 VGS 가 선언값으로 고정돼 M1 은 θ ln IDu 가 없는 종속 소자(`fixed_vgs`)이며, 순환 SCC {vin, vout}(writer 없는 W4 뿌리 둘)의 소자라 Rʳ = {M1}."""
    return topo("wb1_r_dep",
                [mos("M1", "nmos", "vin", "nb1", "gnd"), mos("M2", "nmos", "vout", "nb2", "vin"), mos("M3", "pmos", "vout", "pb", "vdd")],
                {"vin": ("input", "single_ended_input"), "vout": ("output", "single_ended_output")},
                bias=["nb1", "nb2", "pb"])


VGS_M1 = 0.6                      # nb1 선언 목표 (입력 선언, 기대값 아님)


def r_dep_setup(tmp_path, access):
    ctx = build_ctx(tmp_path, circuit_r_dep(), access, node_targets=(("nb1", VGS_M1),))[2]
    entries = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert len(entries) == 1 and set(entries[0].nodes) == {"vin", "vout"}               # 전제 1 (단일 순환 SCC)
    for n in ("vin", "vout"):
        assert ctx.base.value("node", n, "dc_writer").relation not in ("vgs_gate", "vgs_source")   # 전제 2 (writer 없는 SCC)
    assert ctx.base.value("device", "M1", "dc_coord").role != "writer"                  # 전제 3 (M1 종속 = Rʳ)
    assert "M1" in entries[0].devices
    # 손 설계점: V(vin) = 0.5, V(vout) = 1.1 -> 창 위치 y1 = V(vin)/V(vout) (vin 창 [0, V(vout)]), y2 = (V(vout) - V(vin))/(1.8 - V(vin)) (vout 창 [V(vin), 1.8])
    vin, vout = 0.5, 1.1
    y1, y2 = vin / vout, (vout - vin) / (1.8 - vin)
    assert abs(1.8 * y2 / (1.0 - y1 * (1.0 - y2)) - vout) <= 1e-12                      # 창 식 검산 (손)
    # 봉인 7 손 확인 (r4 VDSAT = c0 + c1·VGS + c2·VGS² + cs·VS + cl·(L 앵커 index), nmos (0.0625, 0.25, 0.25, 0.125, 0.0625), pmos (0.125, 0.25, 0.5, 0.0625, 0.125)):
    #   M1 (L = 2e-6, index 1): VDSAT = 0.0625 + 0.15 + 0.09 + 0 + 0.0625 = 0.365 < VDS = 0.5
    #   M2 (L = 1e-6, VGS 0.7, VSB 0.5): 0.0625 + 0.175 + 0.1225 + 0.0625 = 0.4225 < VDS = 0.6
    #   M3 (L = 1e-6, VSG 0.7): 0.125 + 0.175 + 0.245 = 0.545 < VSD = 0.7
    th = {("L", "M1"): 2e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("current", "M3"): 1e-5,
          ("ln_idu", "M2"): r4_ln_idu("nmos", 0.7, vout - vin, vin), ("ln_idu", "M3"): r4_ln_idu("pmos", 0.7, 1.8 - vout, 0.0),
          ("y", "vin"): y1, ("y", "vout"): y2}
    assert set(th) == set(kschema(ctx).components)
    return ctx, th


class Scripted:
    """M1 의 (kind, L) = (nmos, 2e-6) 호출만 스크립트 답(FingerSlice(1, key·g, key))으로 바꾼다. 나머지는 원 함수."""

    def __init__(self, orig, keys):
        self.orig, self.keys, self.m1_calls, self.other_calls = orig, list(keys), 0, 0

    def __call__(self, lut, kind, L, w_of):
        from gmid_engine.lut import FingerSlice
        if kind == "nmos" and L == 2e-6:
            key = self.keys[min(self.m1_calls, len(self.keys) - 1)]
            self.m1_calls += 1
            return FingerSlice(1, key * GRID, key)
        self.other_calls += 1
        return self.orig(lut, kind, L, w_of)


@pytest.fixture
def rdep(tmp_path, two_slice_access, monkeypatch):
    ctx, th = r_dep_setup(tmp_path, two_slice_access)
    mod = importlib.import_module("gmid_engine.sizing.block_dc")
    return ctx, th, mod, monkeypatch


@pytest.mark.parametrize("keys, rounds, final", [([200], 2, 200), ([100], 1, 100)])
def test_dc_solve_rdep_converges(rdep, keys, rounds, final):
    ctx, th, mod, mp = rdep
    stub = Scripted(mod.finger_slice, keys)
    mp.setattr(mod, "finger_slice", stub)
    ev = size_and_seal(ctx, th)
    assert stub.m1_calls >= 1
    assert ops(ev)["M1"].w_key == final
    log = scc_log(ev)
    assert log and all(e.slice_rounds == rounds for e in log)


def test_dc_solve_rdep_cycle_rejected(rdep):
    ctx, th, mod, mp = rdep
    stub = Scripted(mod.finger_slice, [200, 100])
    mp.setattr(mod, "finger_slice", stub)
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    d = dict(ei.value.record.detail)
    assert d["reason"] == "slice_cycle" and "cycle" in d
    assert "M1" in ei.value.record.devices
    assert stub.m1_calls == 2


# ---------------------------------------------------------------- T-W1~4 (순서 창)
def _window(ev, node):
    return dict(ev.snapshot.column("node", "dc_window"))[node]


def _fill_theta(ctx, kinds, y=0.5, vgs=0.6, vout=None):
    th = {}
    for (t, name) in kschema(ctx).components:
        if t == "L":
            th[(t, name)] = 1e-6
        elif t == "y":
            th[(t, name)] = y
        elif t == "ln_idu":
            kind = kinds[name]
            vds = (vout if kind == "nmos" else 1.8 - vout)
            th[(t, name)] = r4_ln_idu(kind, vgs, vds, 0.0)
        elif t == "current":
            th[(t, name)] = 1e-5
        else:
            raise AssertionError((t, name))
    return th


def test_window_w1_nmos_only_lower_is_rail(tmp_path, r4_access):
    doc = topo("wb1_w1", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
               sources=[two("I1", "current_source", "vdd", "out")])
    ctx = build_ctx(tmp_path, doc, r4_access, element_values=(("I1", 1e-5),))[2]
    ev = size_and_seal(ctx, _fill_theta(ctx, {"M1": "nmos"}, vout=0.9))
    w = _window(ev, "out")
    assert w.lo == 0.0                                                          # nmos (d = out, s = gnd): V_DS >= 0 -> lo = gnd


def test_window_w2_pmos_only_upper_is_rail(tmp_path, r4_access):
    doc = topo("wb1_w2", [mos("M2", "pmos", "out", "in", "vdd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
               sources=[two("I1", "current_source", "out", "gnd")])
    ctx = build_ctx(tmp_path, doc, r4_access, element_values=(("I1", 1e-5),))[2]
    ev = size_and_seal(ctx, _fill_theta(ctx, {"M2": "pmos"}, vout=0.9))
    assert _window(ev, "out").hi == 1.8                                         # pmos (d = out, s = vdd): V_SD >= 0 -> hi = vdd


def test_window_w3_both_is_rail_range(tmp_path, r4_access):
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), r4_access)[2]
    ev = size_and_seal(ctx, theta_r4c())
    w = _window(ev, "out")
    assert (w.lo, w.hi) == (0.0, 1.8)


def circuit_gate_only_root():
    """게이트에만 닿는 W4 뿌리 회로(회로 이름 0): M1 nmos (out, in, t, bulk t) -- 소스 t 는 이상 전류원 I1 t -> gnd 로 떠 있어 in 은 VGS 관계로 고정되지 않는
    θ y 뿌리이고(`('y','in')` 가 θ 스키마에 든다), in 에 닿는 채널 단자는 없다. M2 pmos (out, pb, vdd) 부하, pb 바이어스. """
    return topo("wb1_w4_gate_only", [mos("M1", "nmos", "out", "in", "t", "t"), mos("M2", "pmos", "out", "pb", "vdd", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "t", "gnd")], bias=["pb"])


def test_window_w4_gate_only_root_is_rail_range_without_constraints(tmp_path, r4_access):
    """T-W4: 뿌리 넷에 채널 소자가 없다(게이트에만 닿는다) -> 창 = 레일 범위 [gnd, vdd], `Window.constraints` = 0(채널 소자에서 오는 V_DS >= 0 제약 0개).
    oracle (손): 채널 단자가 닿지 않아 제약 소자 없음 -> 창 = 레일 범위. 기대 [0, 1.8] 는 SUPPLIES 선언값(입력)."""
    ctx = build_ctx(tmp_path, circuit_gate_only_root(), r4_access, element_values=(("I1", 1e-5),))[2]
    comps = set(kschema(ctx).components)
    assert ("y", "in") in comps and ("y", "out") in comps                      # 전제: in 은 θ y 뿌리 (이 회로의 통과는 미측정 -- 깨지면 멈추고 보고)
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("y", "in"): 0.5, ("y", "out"): 0.5,
          ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, 0.75, 0.0), ("ln_idu", "M2"): r4_ln_idu("pmos", 0.7, 0.75, 0.0)}
    assert set(th) == comps
    ev = size_and_seal(ctx, th)
    assert "in" in dict(ev.snapshot.column("node", "dc_window"))
    w = _window(ev, "in")
    assert (w.lo, w.hi) == (0.0, 1.8)
    assert w.constraints == 0
