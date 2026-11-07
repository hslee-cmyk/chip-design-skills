"""WB-1 `dc_solve` 블록 (interface card §3 D-1·D-2·D-4·D-5·D-9, §8 T-W1~4). 진입 = `size_and_seal`(공개 경로)과 conftest 보조.

oracle (손/식): 닫힌 r4 식(conftest `r4_ln_idu`, I0·B·C·LAM 상수 -- LUT 파일이 아니라 이 test 의 해석식)과 card §3 의 손 유도.
- D-1: 거울 회로. W = ID·L/IDu(IDu 는 슬라이스와 무관). M2 W ∈ (3.5, 4.5) µm -> 후보 (키 100, m = 4)·(키 200, m = 2), 곱이 400 으로
  같아 동률 -> 큰 키 200. M1 W ∈ [1, 1.5) µm -> (키 100, m = 1) 잔차 작음 vs (키 200, m = 1) 잔차 큼 -> 키 100.
- D-2: 관찰 stub (card §3 표). 미측정 회로 -- 전제가 깨지면 멈추고 보고.
- T-W: 순서 창 = 채널이 닿는 전도 MOS 의 V_DS >= 0 구간의 교집합(VDSAT·tol 읽기 0), 채널 소자 없으면 레일 범위.
"""
import importlib
import inspect
import math

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, size_and_seal

from .conftest import (R4_L, R4_VDS, R4_VGS, R4_VS, build_ctx, build_ctx_u4, circuit_cs_pmos_load, circuit_mirror, free_currents,
                       hand_cells, hand_wf, kschema, mos, r4_ln_idu, theta_mirror, theta_r4c, topo, two, with_hand_ss)
from .wb1_toy import access_of, write_r4_bins_lut

GRID = 1e-8
MIRROR = ("M1", "M2")        # 손 칸 (거울 쌍) -- `mirror_setup` toy 는 graph.matching_groups 가 비어 있어(실측) 칸 입력을 손으로 묶는다


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
def _realize_spy(monkeypatch):
    """관찰 지점 `block_dc.realize_fingers`(§9 통과 spy -- 동작 대체 0): 호출 인자 기록."""
    import sys
    mod = sys.modules["gmid_engine.sizing.block_dc"]
    calls, orig = [], mod.realize_fingers

    def spy(*a, **k):
        calls.append((a, k))
        return orig(*a, **k)
    monkeypatch.setattr(mod, "realize_fingers", spy)
    return calls


def _w_closed(o):
    """oracle (식) 기존 닫힌 식: W = I·L/IDu (r4 해석식 IDu, 그 소자의 동작점 vgs·vds·vsb)."""
    return o.current * o.L / math.exp(r4_ln_idu(o.kind, o.vgs, o.vds, o.vsb))


def test_dc_solve_wf_premise_mirror_seals(tmp_path, two_slice_access):
    """D-0 (전제): `mirror_setup` ctx·θ 에 모든 칸 키 100 인 `wf` 로 `size_and_seal` -> 봉인 통과. (안 서면 멈추고 보고)"""
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    ev = size_and_seal(ctx, th, hand_wf(ctx, default=100))
    assert ev.sealed is not None


def test_dc_solve_search_eval_keeps_fractional_fingers_all_keys_100(tmp_path, two_slice_access, monkeypatch):
    """D-1: 모든 칸 키 100 -> 모든 MOS w_key == 100, dc_finger[m].m == DeviceOp.W / (100 * 1e-8) (실수, 정수화 0), residual == 0.0.
    oracle (식) interface §4.2 `dc_finger[m] = FingerGeom(DeviceOp.W / (key * grid_m), 0.0)`; 전제: W/w_f 가 정수가 아닌 소자가 하나 이상."""
    calls = _realize_spy(monkeypatch)
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    ev = size_and_seal(ctx, th, hand_wf(ctx, default=100))
    o, f = ops(ev), fingers(ev)
    assert set(o) == {"M1", "M2", "M3"}
    for m in o:
        assert o[m].w_key == 100
        assert f[m].m == o[m].W / (100 * GRID) and f[m].residual == 0.0
    assert any(abs(f[m].m - round(f[m].m)) > 1e-6 for m in f)                      # 전제: 정수가 아닌 소자 존재
    assert calls == []                                                              # D-6: 탐색 평가는 realize_fingers 호출 0


def test_dc_solve_cell_members_share_slice_and_w_is_closed_form(tmp_path, two_slice_access):
    """D-2: 정합 칸 키 200, 나머지 100 -> 칸 멤버 모두 w_key == 200, DeviceOp.W = I·L/exp(r4 ln IDu) 닫힌 식."""
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    assert ("M1", "M2") in hand_cells(ctx, join=(MIRROR,))                          # 손 칸 (이 toy 는 matching_groups 가 비어 있어 손으로 묶는다)
    ev = size_and_seal(ctx, th, hand_wf(ctx, {m: 200 for m in MIRROR}, default=100, join=(MIRROR,)))
    o = ops(ev)
    for m in MIRROR:
        assert o[m].w_key == 200
    assert o["M3"].w_key == 100
    for m, op in o.items():
        assert abs(op.W - _w_closed(op)) <= 1e-9 * _w_closed(op), m


def test_dc_solve_no_slice_rounds_and_one_node_solve_per_eval(tmp_path, two_slice_access):
    """D-3: D-1·D-2 두 평가의 dc_scc_log 항목에 slice_rounds 속성 없음, 항목 수 = 평가당 SCC 수 (노드 풀이 평가당 1회)."""
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    n_scc = len(ctx.base.value("graph", DC_KEY, "dc_scc_order"))
    evs = [size_and_seal(ctx, th, hand_wf(ctx, default=100)),
           size_and_seal(ctx, th, hand_wf(ctx, {m: 200 for m in MIRROR}, default=100, join=(MIRROR,)))]
    for ev in evs:
        log = scc_log(ev)
        assert len(log) >= 1 and len(log) == n_scc
        assert all(not hasattr(e, "slice_rounds") for e in log)


def test_dc_solve_wf_required_positional(tmp_path, two_slice_access):
    """D-4: `wf` 없이 size_and_seal(ctx, th) -> TypeError (필수 위치 인자). 양성 대조: wf 를 주면 통과."""
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    assert size_and_seal(ctx, th, hand_wf(ctx)).snapshot is not None
    with pytest.raises(TypeError):
        size_and_seal(ctx, th)


def test_dc_solve_realized_eval_uses_hand_oracle_m(tmp_path, two_slice_access, monkeypatch):
    """D-5·D-6: 실현 평가 -- 칸마다 m = interface §1 손 oracle(w_theta = 탐색 스냅샷 칸 멤버 DeviceOp.W, w_f = key × 1e-8),
    DeviceOp.W == m * (key * 1e-8), residual == m * w_f / W_θ - 1.0; realize_fingers 는 칸당 한 번(ratios = ()), 탐색 평가에서는 0회."""
    from gmid_engine.sizing import RealizeInput
    from .test_realize_fingers import hand_oracle
    calls = _realize_spy(monkeypatch)
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    wf = hand_wf(ctx, {m: 200 for m in MIRROR}, default=100, join=(MIRROR,))
    assert len(wf.cells_ref) == 2 and wf.cells_ref[0].members == MIRROR            # 전제: 2멤버 칸 하나 + M3 칸
    ev = size_and_seal(ctx, th, wf)
    assert calls == []                                                              # 탐색 평가 0회
    so = ops(ev)
    re = size_and_seal(ctx, th, wf, realized=RealizeInput(ev.snapshot))
    assert len(calls) == len(wf.cells_ref)                                          # 칸당 1회
    assert all(k == {} and a[2] == () for a, k in calls)                            # ratios = () (A-178 S-2 과도기)
    ro, rf = ops(re), fingers(re)
    for cell in wf.cells_ref:
        w_f = cell.w_key * GRID
        w_theta = tuple(so[m].W for m in cell.members)
        want = hand_oracle(w_theta, w_f, ())[4]
        for i, m in enumerate(cell.members):
            assert rf[m].m == want[i] and type(rf[m].m) is int
            assert ro[m].W == want[i] * (cell.w_key * GRID)
            assert rf[m].residual == want[i] * w_f / so[m].W - 1.0


def test_dc_solve_layout_reseal_uses_request_rows_and_base_fingers(tmp_path, two_slice_access, monkeypatch):
    """D-7: 레이아웃 뒤 -- 요청 행 소자 M2 = (nf 3, finger_w 2e-6): w_key == 200, W' = 3·2e-6; 요청 없는 소자 = 기준(실현) 스냅샷의
    dc_finger.m·DeviceOp.w_key 그대로 (W' = m·w_key·1e-8); realize_fingers 호출 0."""
    from gmid_engine.sizing import RealizeInput, RealizedGeometry
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    wf = hand_wf(ctx, default=100)
    free = size_and_seal(ctx, th, wf)
    base = size_and_seal(ctx, th, wf, realized=RealizeInput(free.snapshot))
    calls = _realize_spy(monkeypatch)
    geom = RealizedGeometry(layout_ref=None, w_request=(("M2", (3, 2e-6)),))
    req = size_and_seal(ctx, th, wf, parent=base, realized=RealizeInput(base.snapshot), layout=geom)
    assert calls == []
    bo, bf = ops(base), fingers(base)
    ro, rf = ops(req), fingers(req)
    assert ro["M2"].w_key == 200 and ro["M2"].W == pytest.approx(3 * 2e-6, rel=1e-12)
    assert rf["M2"].m == 3
    for m in ("M1", "M3"):
        assert rf[m].m == bf[m].m and ro[m].w_key == bo[m].w_key
        assert ro[m].W == bf[m].m * (bo[m].w_key * GRID)


def test_dc_solve_cell_member_lookup_failure_is_not_avoided(tmp_path, monkeypatch):
    """D-8: 칸 멤버 조회 불능 -- 폭 2e-6 슬라이스의 L 축이 소자 L(1e-6)을 품지 않게 한다. 정합 칸 키 200 이면 size_and_seal 은 후보 실패 클래스
    (SealViolationError)로 실패하고, 칸 멤버를 다른 키(100)로 바꾼 성공 스냅샷은 없다 (realize_fingers 호출 0)."""
    import json
    import numpy as np
    from gmid_engine.lut import load_lut_set
    from .conftest import TOY_SPEC, _sha
    lut, root, tb = write_r4_bins_lut(tmp_path / "lut", widths=(1e-6, 2e-6))
    access_ok = access_of(lut)
    ctx_ok, th_ok = mirror_setup(tmp_path / "ok", access_ok)
    assert size_and_seal(ctx_ok, th_ok, hand_wf(ctx_ok, default=200, join=(MIRROR,))).snapshot is not None     # 양성 대조: 원 LUT 에서는 키 200 통과
    p = root / "r4_nmos_w200.npz"
    z = dict(np.load(p, allow_pickle=False))
    z["L"] = np.asarray(z["L"], dtype=float) + 3e-6                                                # L 축에서 1e-6 이 빠진다 (3e-6, 4e-6)
    np.savez(p, **z)
    man = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for e in man["slices"]:
        if e["file"] == p.name:
            e["sha256"] = _sha(p)
    (root / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
    lut2 = load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC, bin_rule=tb.bin_rule)   # 적재 관문 통과가 전제(아니면 멈추고 보고)
    calls = _realize_spy(monkeypatch)
    ctx, th = mirror_setup(tmp_path / "bad", access_of(lut2))
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th, hand_wf(ctx, {m: 200 for m in MIRROR}, default=100, join=(MIRROR,)))
    assert dict(ei.value.record.detail).get("reason")                                              # 기존 LUT 축·L 사유가 기록됨
    assert calls == []


def test_dc_solve_same_theta_bit_identical_and_parent_independent(tmp_path, two_slice_access):
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    wf = hand_wf(ctx)
    a = size_and_seal(ctx, th, wf)
    b = size_and_seal(ctx, th, wf)
    assert a.snapshot.fp == b.snapshot.fp
    c = size_and_seal(ctx, th, wf, parent=with_hand_ss(a))
    for kind, field in (("device", "dc_finger"), ("device", "dc_op"), ("node", "dc_v")):
        assert a.snapshot.column(kind, field) == c.snapshot.column(kind, field)
    assert len(a.snapshot.column("device", "dc_finger")) >= 1


# ---------------------------------------------------------------- D-5
def layout_geometry(placed, requested):
    """레이아웃 뒤 입력 `RealizedGeometry` -- 공개 `realized_geometry(snapshot, placements)` 로 만든다(값 칸 모양에 기대지 않는다).
    placed = {소자: (nf, finger_w)} (배치), requested = {소자: (nf, finger_w)} (요청 대기: 배치 아님 + 요청 행). 접합 ad/as/pd/ps 는 DC 와 무관한 손 값."""
    from convergence.conftest import ddiff, layout, placement
    from gmid_engine.convergence import realized_geometry
    pl = [placement(m, round(fw / GRID), nf, nf * fw) for m, (nf, fw) in sorted(placed.items())]
    pl += [placement(m, round(fw / GRID), nf, nf * fw, pending=True) for m, (nf, fw) in sorted(requested.items())]
    diff = tuple(ddiff(m, fw, nf, 3e-13, 3e-13, 4e-6, 4e-6) for m, (nf, fw) in sorted(placed.items()))
    return realized_geometry(layout(diffusion=diff).snapshot, tuple(pl))


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


# [FS-1] 옛 D-4 `test_dc_solve_dependent_all_candidates_missing`·D-2 Rʳ 묶음(`circuit_r_dep`·`r_dep_setup`·`Scripted`·`rdep`·`test_dc_solve_rdep_*`)은
# 대상(선택 함수·Rʳ·slice_cycle)이 소멸해 삭제 -- 대응표 tests/RETIRED_TESTS_fs1.md.
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
    ev = size_and_seal(ctx, _fill_theta(ctx, {"M1": "nmos"}, vout=0.9), hand_wf(ctx))     # [FS-1 서명 맞춤] wf 인자
    w = _window(ev, "out")
    assert w.lo == 0.0                                                          # nmos (d = out, s = gnd): V_DS >= 0 -> lo = gnd


def test_window_w2_pmos_only_upper_is_rail(tmp_path, r4_access):
    doc = topo("wb1_w2", [mos("M2", "pmos", "out", "in", "vdd")],
               {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
               sources=[two("I1", "current_source", "out", "gnd")])
    ctx = build_ctx(tmp_path, doc, r4_access, element_values=(("I1", 1e-5),))[2]
    ev = size_and_seal(ctx, _fill_theta(ctx, {"M2": "pmos"}, vout=0.9), hand_wf(ctx))     # [FS-1 서명 맞춤] wf 인자
    assert _window(ev, "out").hi == 1.8                                         # pmos (d = out, s = vdd): V_SD >= 0 -> hi = vdd


def test_window_w3_both_is_rail_range(tmp_path, r4_access):
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), r4_access)[2]
    ev = size_and_seal(ctx, theta_r4c(), hand_wf(ctx))     # [FS-1 서명 맞춤] wf 인자
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
    ev = size_and_seal(ctx, th, hand_wf(ctx))     # [FS-1 서명 맞춤] wf 인자
    assert "in" in dict(ev.snapshot.column("node", "dc_window"))
    w = _window(ev, "in")
    assert (w.lo, w.hi) == (0.0, 1.8)
    assert w.constraints == 0


# =====================================================================================================================
# [WB-1 이동] 옛 test_block_widths.py 의 계약 -- 이 블록(dc_solve)이 노드 풀이와 W 를 한 블록으로 합쳐 같은 파일에서 본다 (rule H: 원본 module 이름 = test 파일 이름).
# `dc_solve` 의 소자 동작점 부분(옛 폭 블록 계약 5.7, WB-1 이후 한 블록): MOS 마다 DeviceOp. vgs·vds·vsb = 노드전압 차의 크기(s = +1 nmos/−1 pmos),
# op = op_point(노드 점), W = ID·L/exp(ln_idu), gm_id = op.gm_over_id, idu_forward = op.IDu, w_key = 그 소자 손가락 슬라이스 키(toy LUT 는 슬라이스 하나라 W_KEY).
#
# 기대값: toy LUT 닫힌 식(conftest Oracle) -- IDu = I0·exp(B·vgs + LAM·vds + vs항), gm/ID = B − C·vgs.
# =====================================================================================================================

import math

import pytest

from gmid_engine.sizing import DeviceOp, dc_solve

from .conftest import (W_KEY, Oracle, block_row, kfixed, kres, mos_table, node_voltages, rel_close, row_delta, run_blocks, run_of,
                       terminal_mag, theta_a, theta_c)


def check_ops(snap):
    V = node_voltages(snap)
    ops = dict(snap.column("device", "dc_op"))
    mt = mos_table(snap)
    assert set(ops) == set(mt)
    cur = dict(snap.column("device", "dc_current"))
    L = dict(snap.column("device", "dc_L"))
    ln = dict(snap.column("device", "dc_ln_idu"))
    for m, (kind, d, g, s, b) in mt.items():
        op = ops[m]
        assert isinstance(op, DeviceOp)
        vgs, vds, vsb = terminal_mag(kind, V, d, g, s, b)
        assert op.kind == kind and op.w_key == W_KEY
        assert abs(op.vgs - vgs) <= 1e-12 and abs(op.vds - vds) <= 1e-12 and abs(op.vsb - vsb) <= 1e-12
        assert op.current == cur[m] and op.L == L[m] and op.ln_idu == ln[m]
        assert rel_close(op.W, cur[m] * L[m] / math.exp(ln[m]), 1e-12)
        assert rel_close(op.idu_forward, math.exp(Oracle.ln_idu(kind, vgs, vds, vsb)), 1e-9)
        assert rel_close(op.gm_id, Oracle.gm_id(vgs), 1e-9)
        assert op.W > 0
    return ops


def test_circuit_c(ctx_c):
    th = theta_c()
    ops = check_ops(run_blocks(ctx_c[2], th))
    # 손계산: M1 vgs 0.6·vds 0.9·vsb 0, M2(pmos) vgs 0.7·vds 0.9·vsb 0; W = 1e-5·L/exp(x)
    assert abs(ops["M1"].vgs - 0.6) <= 1e-9 and abs(ops["M2"].vgs - 0.7) <= 1e-9
    assert abs(ops["M2"].vds - 0.9) <= 1e-12 and ops["M2"].vsb == 0.0
    assert rel_close(ops["M1"].W, 1e-5 * 1e-6 / math.exp(th[("ln_idu", "M1")]), 1e-12)
    assert rel_close(ops["M2"].W, 1e-5 * 2e-6 / math.exp(th[("ln_idu", "M2")]), 1e-12)
    # writer 는 forward IDu 가 좌표와 같다(toy LUT 의 VGS 축 로그선형 -> 역산 정확)
    assert rel_close(ops["M1"].idu_forward, math.exp(th[("ln_idu", "M1")]), 1e-9)


@pytest.mark.parametrize("i,r", [(1e-5, 9e4), (3e-6, 1e5)])
def test_circuit_a(ctx_a, i, r):
    ops = check_ops(run_blocks(ctx_a[2], theta_a(i=i, r=r)))
    assert abs(ops["M1"].vds - (1.8 - i * r)) <= 1e-12


def test_width_scales_with_current_only(ctx_c):
    a = dict(run_blocks(ctx_c[2], theta_c(i2=1e-5)).column("device", "dc_op"))
    b = dict(run_blocks(ctx_c[2], theta_c(i2=3e-5)).column("device", "dc_op"))
    for m in ("M1", "M2"):
        assert rel_close(b[m].W, 3 * a[m].W, 1e-12)
        assert (b[m].vgs, b[m].vds, b[m].gm_id) == (a[m].vgs, a[m].vds, a[m].gm_id)


def test_reads_no_unknown_fields(ctx_c):
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행의 이 구간 증분 = 계산 1·재사용 1
    ctx = ctx_c[2]
    th = theta_c()
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    before = block_row(ctx.counters, "dc_solve")
    out = dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run_of(ctx))
    assert dc_solve(out, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run_of(ctx)) is out
    assert row_delta(block_row(ctx.counters, "dc_solve"), before) == (2, 1, 0, 0, 1, 0)


def test_dc_solve_wf_is_required_keyword(ctx_c):
    """[FS-1 A-188, interface §4.1] `dc_solve(snapshot, theta_items, fixed_values, resistor_values, lut, *, wf, donors, counters)` -- wf 가 빠지면 TypeError.
    양성 대조: wf 를 키워드로 주면 통과."""
    ctx = ctx_c[2]
    th = theta_c()
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    assert dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run_of(ctx)) is not None
    with pytest.raises(TypeError):
        dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, **run_of(ctx))


# ===============================================================================================================
# [card 20261104-hcs] S5 -- `device.dc_sat_v` = {MOS: SatBound}, writer = dc_op 와 같은 블록 dc_solve
# oracle (손) conftest 닫힌 식 `r4_vdsat_at`·`r4_tol_vdsat`(npz 열 직접) -- 동작점 좌표(L, vgs, vsb)는 같은 블록이 낸 dc_op 의 입력 칸.
# (식) card §2: 선언 없음·triode -> sat_threshold 값, off -> SatBound(None, None, "off_declared").
# ===============================================================================================================

def test_dc_sat_v_undeclared_devices_hold_the_lut_values_at_their_operating_points(ctx_r4c):
    from gmid_engine.lut import SatBound
    from .conftest import r4_tol_vdsat, r4_vdsat_at, theta_r4c
    snap = run_blocks(ctx_r4c, theta_r4c(), upto="widths")
    ops = dict(snap.column("device", "dc_op"))
    col = dict(snap.column("device", "dc_sat_v"))
    assert set(col) == set(ops) == {"M1", "M2"}
    for m, op in ops.items():
        sb = col[m]
        assert isinstance(sb, SatBound) and sb.reason is None
        assert rel_close(sb.vdsat_v, r4_vdsat_at(op.kind, op.L, op.vgs, op.vsb), 1e-12)
        assert rel_close(sb.tol_v, r4_tol_vdsat(op.kind), 1e-9)
        assert snap.field("device", m, "dc_sat_v").writer == snap.field("device", m, "dc_op").writer == "dc_solve"


def test_dc_sat_v_writer_is_dc_widths_in_the_authority_table():
    from gmid_engine.sizing import S2_WRITERS
    assert S2_WRITERS.writer_of("device", "dc_sat_v") == "dc_solve" == S2_WRITERS.writer_of("device", "dc_op")


def test_dc_sat_v_off_declared_has_reason_and_triode_has_the_lut_value(tmp_path):
    """한 회로: Moff(off 선언) + M1(triode 선언, V(out) = 0.18 < vdsat). off 만 사유 `off_declared`, triode 는 선언 없음과 같은 LUT 값."""
    from metrics.off_cases import build_case, circuit_a, off_entry, theta_from_schema, tri_entry
    from gmid_engine.lut import SatBound
    from .conftest import r4_tol_vdsat, r4_vdsat_at
    i, r = 1e-5, 1.62e5

    def th(ctx):
        return theta_from_schema(ctx, {"M1": ("nmos", 0.6, 1.8 - i * r, 0.0)}, {"R1": i, "M1": i}, {"R1": r})
    case = build_case(tmp_path, circuit_a([("Moff", "nmos", "out", "gnd", "gnd", "gnd")], name="hcs_s5"),
                      {"Moff": off_entry(), "M1": tri_entry()}, th)
    col = dict(case.ev.snapshot.column("device", "dc_sat_v"))
    op = dict(case.ev.snapshot.column("device", "dc_op"))["M1"]
    assert set(col) == {"M1", "Moff"}
    assert col["Moff"] == SatBound(None, None, "off_declared")
    assert col["M1"].reason is None
    assert rel_close(col["M1"].vdsat_v, r4_vdsat_at("nmos", op.L, op.vgs, op.vsb), 1e-12)
    assert rel_close(col["M1"].tol_v, r4_tol_vdsat("nmos"), 1e-9)


# =====================================================================================================================
# [WB-1 이동] 옛 test_block_columns.py 의 계약 -- 이 블록(dc_solve)이 노드 풀이와 W 를 한 블록으로 합쳐 같은 파일에서 본다 (rule H: 원본 module 이름 = test 파일 이름).
# `dc_solve(snapshot, theta_items, fixed_values, resistor_values, lut)` -- CONTRACT 5.4: 노드전압 정본.
#
# 기대값: conftest `expected_columns`(writer 식·창 규칙을 독립 구현, VGS 는 toy LUT 닫힌 식 `Oracle.vgs_of`)와 손계산.
# 순환 SCC 는 [r4] VDS 정의역 하한의 반복 중/strict 규칙 test 와 [r9] 성능 항목 1·6 절(끝 두 절)에서 쓴다(수렴값은 θ 를 해에서
# 거꾸로 만들어 손으로 안다).
# =====================================================================================================================

import collections
import math

import pytest

from gmid_engine.authoring import RegionDecl

from gmid_engine.core import NonconvergentError, SealViolationError
from gmid_engine.lut import LutMemo
from gmid_engine.sizing import (DC_KEY, REASON_NO_ROOT, REASON_TOL_UNDEFINED, SCC_GAUSS_SEIDEL, LutAccess, PathValue, SccLog,
                                Window, dc_solve, size_and_seal)

from .conftest import (LAM, R4_L, Oracle, build_ctx, circuit_cs_res, circuit_empty_window, detail,
                       expected_columns, free_currents, mos, new_access, node_voltages, r4_arrays, r4_ln_idu, r4_vds_floor,
                       r4_vgs_of, rel_close, run_blocks, theta_a, theta_c, theta_r4c, topo, two, write_r4_lut)
from .conftest import run_of  # [XRUN-F1 card B C4] 블록 호출 = ctx 의 실행 두 객체
from .conftest import kfixed, kres, kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)

TOL = 1e-12


def assert_voltages(snap, ctx, theta):
    V_exp, win_exp, ln_exp = expected_columns(snap, theta, kfixed(ctx), kres(ctx))
    V = node_voltages(snap)
    assert set(V) == set(V_exp)
    for n in V_exp:
        assert abs(V[n] - V_exp[n]) <= TOL, (n, V[n], V_exp[n])
    # [IT-2b 갱신 -- 대조 대상 명시] `node.dc_window` 범위는 W4 뿌리 + 모든 입력 포트로 넓어졌다(design 41 4.7-2). `expected_columns` 는 W4 뿌리 창
    # (writer relation free_window)만 안다 -> 뿌리 항목으로 좁혀 이전과 같은 키 집합 등식·끝 값을 대조하고, 입력 포트 항목은 아래 test_it2b_k1_*·
    # test_it2b_k2_* 가 따로 본다.
    win_all = dict(snap.column("node", "dc_window"))
    roots = {n for n, w in dict(snap.column("node", "dc_writer")).items() if w.relation == "free_window"}
    win = {n: w for n, w in win_all.items() if n in roots}
    # 단언 둘로 나눈다(약화 해소): (1) 뿌리 키 집합 등식, (2) 뿌리 밖 키는 모두 입력 포트(`node.port_direction` == "input" -- 피검 출력이 아닌 입력 필드).
    # 측정 실패(A6 a)면 뿌리 아닌 포트 항목이 없으므로 '뿌리 ∪ 입력 포트' 전체 등식은 일반 불변식이 아니다(design 41 4.7-3 4).
    input_ports = {n for n, d in dict(snap.column("node", "port_direction")).items() if d == "input"}
    assert set(win_all) & roots == set(win_exp)
    assert set(win_all) - roots <= input_ports
    assert set(win) == set(win_exp)
    for n, (lo, hi) in win_exp.items():
        assert isinstance(win[n], Window)
        assert abs(win[n].lo - lo) <= TOL and abs(win[n].hi - hi) <= TOL
    ln = dict(snap.column("device", "dc_ln_idu"))
    assert set(ln) == set(ln_exp)
    for m in ln_exp:
        assert abs(ln[m] - ln_exp[m]) <= 1e-9, (m, ln[m], ln_exp[m])
    return V


# ---------------------------------------------------------------------------
# 회로 C: W4 창 + vgs_gate (nmos·pmos 부호)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("y,vgs1,vgs2", [(0.5, 0.6, 0.7), (0.3, 0.55, 0.95), (0.8, 0.43, 0.61)])
def test_circuit_c_hand(ctx_c, y, vgs1, vgs2):
    ctx = ctx_c[2]
    th = theta_c(y=y, x1=Oracle.ln_idu("nmos", vgs1, 1.8 * y, 0.0), x2=Oracle.ln_idu("pmos", vgs2, 1.8 * (1 - y), 0.0))
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    # 손계산: out = 0 + y·(1.8 − 0) (창 = 레일 범위, VDsat 항 없음), in = 0 + VGS1, pb = 1.8 − VGS2
    assert abs(V["out"] - 1.8 * y) <= TOL
    assert abs(V["in"] - vgs1) <= 1e-9
    assert abs(V["pb"] - (1.8 - vgs2)) <= 1e-9
    assert dict(snap.column("node", "dc_window"))["out"].lo == 0.0
    assert dict(snap.column("node", "dc_window"))["out"].hi == 1.8


def test_circuit_c_path_values(ctx_c):
    ctx = ctx_c[2]
    th = theta_c()
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    pv = dict(snap.column("node", "dc_path_values"))
    assert set(pv) == set(V)                       # 모든 노드
    for n, vals in pv.items():
        assert all(isinstance(p, PathValue) for p in vals)
        assert [p.relation for p in vals] == sorted(p.relation for p in vals)
    rel = {n: {p.relation: p.value for p in vals} for n, vals in pv.items()}
    vgs1 = Oracle.vgs_of("nmos", th[("ln_idu", "M1")], V["out"], 0.0)
    vgs2 = Oracle.vgs_of("pmos", th[("ln_idu", "M2")], 1.8 - V["out"], 0.0)
    assert set(rel["in"]) == {("vgs", "M1")} and abs(rel["in"][("vgs", "M1")] - (0.0 + vgs1)) <= 1e-9
    assert set(rel["gnd"]) == {("fixed", "rail"), ("vgs", "M1")}
    assert rel["gnd"][("fixed", "rail")] == 0.0 and abs(rel["gnd"][("vgs", "M1")] - (V["in"] - vgs1)) <= 1e-9
    assert set(rel["vdd"]) == {("fixed", "rail"), ("vgs", "M2")}
    assert abs(rel["vdd"][("vgs", "M2")] - (V["pb"] + vgs2)) <= 1e-9         # pmos: V(s) = V(g) − s·VGS
    assert set(rel["pb"]) == {("vgs", "M2")}
    assert rel["out"] == {("y", "out"): V["out"]}


def test_writer_ln_idu_is_theta(ctx_c):
    th = theta_c()
    snap = run_blocks(ctx_c[2], th, upto="columns")
    assert dict(snap.column("device", "dc_ln_idu")) == {"M1": th[("ln_idu", "M1")], "M2": th[("ln_idu", "M2")]}


def test_scc_log_matches_order(ctx_c):
    snap = run_blocks(ctx_c[2], theta_c(), upto="columns")
    log = snap.value("graph", DC_KEY, "dc_scc_log")
    order = snap.value("graph", DC_KEY, "dc_scc_order")
    assert all(isinstance(x, SccLog) for x in log)
    assert [(x.index, x.nodes) for x in log] == [(e.index, e.nodes) for e in order]


# ---------------------------------------------------------------------------
# 회로 A: resistor_drop 부호(t0/t1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("i,r", [(1e-5, 9e4), (2e-6, 3e5), (5e-5, 1e4)])
def test_resistor_drop_known_t0(ctx_a, i, r):
    ctx = ctx_a[2]
    th = theta_a(i=i, r=r)
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    assert abs(V["out"] - (1.8 - i * r)) <= TOL                   # known vdd = t0 -> V = V(vdd) − I·R
    rel = {p.relation: p.value for p in dict(snap.column("node", "dc_path_values"))["vdd"]}
    assert abs(rel[("resistor", "R1")] - (V["out"] + i * r)) <= TOL
    rel_out = {p.relation: p.value for p in dict(snap.column("node", "dc_path_values"))["out"]}
    assert abs(rel_out[("resistor", "R1")] - (1.8 - i * r)) <= TOL


def test_resistor_drop_known_t1(tmp_path, toy_access):
    doc = topo("hand_cs_res_rev2", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R1", "resistor", "out", "vdd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    i_r1, r = -1e-5, 9e4                                           # R1 전류(out -> vdd 방향) 음수 = M1 양수
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.0),
          ("current", "R1"): i_r1, ("resistance", "R1"): r}
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    assert abs(V["out"] - (1.8 + i_r1 * r)) <= TOL                 # known vdd = t1 -> V = V(vdd) + I·R


def test_declared_resistor_value_used(tmp_path, toy_access):
    doc = circuit_cs_res()
    doc["topology_name"] = "hand_cs_res_declared"
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("R1", 6e4),))[2]
    assert kres(ctx) == (("R1", 6e4),)
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 1.2, 0.0), ("current", "R1"): 1e-5}
    snap = run_blocks(ctx, th, upto="columns")
    assert abs(node_voltages(snap)["out"] - (1.8 - 1e-5 * 6e4)) <= TOL


def test_zero_current_drop_is_zero_and_cycle_dependent(tmp_path, toy_access):
    """R2(g3, vdd) 는 잎 가지치기 저항(전류 0) -> V(g3) = V(vdd) 정확. M2 (gate g3) 는 G_vgs 비트리 -> 종속,
    ln_idu = ln IDu(노드 vgs = 0)."""
    doc = topo("hand_zero_drop",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "g3", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R2", "resistor", "g3", "vdd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.72, 0.0),
          ("y", "out"): 0.4}
    th.update(free_currents(ctx, {"M1": 1e-6, "M2": 1e-6, "R2": 0.0}))
    assert set(dict(th)) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    assert V["g3"] == 1.8
    assert dict(snap.column("device", "dc_current"))["R2"] == 0.0
    assert snap.value("device", "M2", "dc_coord").role == "dependent"
    exp = Oracle.ln_idu("pmos", 0.0, 1.8 - 0.72, 0.0)
    assert abs(dict(snap.column("device", "dc_ln_idu"))["M2"] - exp) <= 1e-9


def test_parallel_dependent_ln_idu(tmp_path, toy_access):
    """M1·M2 같은 (gate, source), 다른 drain(VDS 다름) -> 종속 쪽 ln_idu 는 자기 VDS 의 op_point 값(writer 값과 다름)."""
    doc = topo("hand_parallel",
               [mos("M1", "nmos", "o1", "in", "gnd"), mos("M2", "nmos", "o2", "in", "gnd"),
                mos("M3", "pmos", "o1", "pb", "vdd"), mos("M4", "pmos", "o2", "pb", "vdd")],
               {"in": ("input", "x"), "o1": ("output", "y")}, bias=["pb"])                 # pb: M3·M4 gate 에만
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    comps = dict.fromkeys(kschema(ctx).components)
    th = {}
    for kind, key in comps:
        th[(kind, key)] = {"L": 1e-6, "current": 1e-5, "y": 0.3 if key == "o1" else 0.7}.get(kind)
    for m in ("M1", "M2"):
        if ("ln_idu", m) in comps:
            th[("ln_idu", m)] = Oracle.ln_idu("nmos", 0.6, 0.5, 0.0)
    for m in ("M3", "M4"):
        if ("ln_idu", m) in comps:
            th[("ln_idu", m)] = Oracle.ln_idu("pmos", 0.7, 0.9, 0.0)
    assert None not in th.values()
    snap = run_blocks(ctx, th, upto="columns")
    assert_voltages(snap, ctx, th)
    roles = {m: snap.value("device", m, "dc_coord").role for m in ("M1", "M2", "M3", "M4")}
    assert sorted(roles[m] for m in ("M1", "M2")) == ["dependent", "writer"]


def test_window_with_declared_target(tmp_path, toy_access):
    """s1 = W3 0.3 V: out 창 = [V(s1), V(vdd)] = [0.3, 1.8]; in = 0.3 + VGS(vsb 0.3)."""
    doc = topo("hand_w3",
               [mos("M1", "nmos", "out", "in", "s1"), mos("M2", "pmos", "out", "pb", "vdd"),
                mos("M5", "nmos", "s1", "vb5", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, bias=["pb", "vb5"])        # pb: M2 gate, vb5: M5 gate
    ctx = build_ctx(tmp_path, doc, toy_access, node_targets=(("s1", 0.3),))[2]
    assert kfixed(ctx) == (("s1", 0.3),)
    y = 0.4
    vout = 0.3 + y * 1.5
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M5"): 2e-6,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.5, vout - 0.3, 0.3),
          ("ln_idu", "M2"): Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0),
          ("ln_idu", "M5"): Oracle.ln_idu("nmos", 0.65, 0.3, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M5": 1e-5}))   # KCL: 세 소자 같은 전류
    assert set(th) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    w = dict(snap.column("node", "dc_window"))["out"]
    assert (w.lo, w.hi) == (0.3, 1.8)
    assert abs(V["out"] - vout) <= TOL
    assert abs(V["in"] - (0.3 + 0.5)) <= 1e-9
    assert abs(V["vb5"] - 0.65) <= 1e-9
    assert V["s1"] == 0.3
    assert {p.relation: p.value for p in dict(snap.column("node", "dc_path_values"))["s1"]}[
        ("fixed", "declared_target")] == 0.3


# ---------------------------------------------------------------------------
# 실패
# ---------------------------------------------------------------------------

def test_empty_window(tmp_path, toy_access):
    ctx = build_ctx(tmp_path, circuit_empty_window(), toy_access)[2]
    th = {}
    for kind, key in kschema(ctx).components:
        if kind != "current":
            th[(kind, key)] = {"L": 1e-6, "y": 0.5, "ln_idu": Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}[kind]
    # KCL x: MA + MC = MB (MB 는 pmos, x 로 들어옴)
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 2e-5, "MC": 1e-5}))
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run_of(ctx))
    d = detail(ei.value)
    assert d["reason"] == "empty_window" and d["item"] == 7
    assert d["node"] == "x" and d["lo"] == 1.8 and d["hi"] == 0.0
    assert "constraints" in d
    assert ei.value.record.devices == () and ei.value.record.margin is None


def _lut_fail(ctx, th):
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run_of(ctx))
    return ei.value


def test_lut_target_out_of_range(ctx_c):
    th = theta_c(x1=Oracle.ln_idu("nmos", 2.5, 0.9, 0.0))          # VGS 2.5 > 격자 최대 1.8
    e = _lut_fail(ctx_c[2], th)
    d = detail(e)
    assert d["reason"] == "lut_query_failed"
    assert d["lut_reason"] == "lut_target_out_of_range"
    assert d["device_query"] == "vgs_of_coordinate"
    assert e.record.devices == ("M1",)


def test_lut_l_not_anchor(ctx_c):
    e = _lut_fail(ctx_c[2], theta_c(l2=1.5e-6))
    d = detail(e)
    # [WB-1 §4] 합성 LUT 에 bin 지도가 생겼다: 1.5 µm 은 앵커 1 µm 의 bin 안 비앵커 점(bin 안 앵커 1개) -> 사유 어휘 변경(card 목록)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_l_bin_unbracketed"
    assert e.record.devices == ("M2",)


def test_lut_axis_out_of_range_vsb(tmp_path, toy_access):
    """bulk 를 out 에 선언: vsb = V(gnd) − V(out) = −0.6 < VS 격자 최소 −0.45 -> 축 밖(클램프 없음)."""
    ctx = build_ctx(tmp_path, circuit_cs_res(bulk_m1="out"), toy_access)[2]
    e = _lut_fail(ctx, theta_a(i=1e-5, r=1.2e5))
    d = detail(e)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_axis_out_of_range"
    assert e.record.devices == ("M1",)


# ---------------------------------------------------------------------------
# [r2] 1변수 노드 = 구간 bisection (5.4)
# ---------------------------------------------------------------------------

def _mirror_ctx(tmp_path, toy_access):
    doc = topo("bc_mirror",
               [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                mos("M3", "pmos", "out", "in", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "nb")])
    return build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5),))[2]


def _mirror_theta(ctx, v_diode):
    import math as _m
    x1 = Oracle.ln_idu("nmos", v_diode, v_diode, 0.0)       # diode: vds = vgs, vsb 0
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("ln_idu", "M1"): x1,
          ("ln_idu", "M3"): Oracle.ln_idu("pmos", 0.7, 0.9, 0.0), ("y", "out"): 0.5}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5, "I1": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


@pytest.mark.parametrize("v_star", [0.35, 0.6, 1.1])
def test_diode_one_variable_bisection(tmp_path, toy_access, v_star):
    ctx = _mirror_ctx(tmp_path, toy_access)
    snap = run_blocks(ctx, _mirror_theta(ctx, v_star), upto="columns")
    V = node_voltages(snap)
    tol = Oracle.tol_v()
    from .conftest import LAM
    # bisection 마지막 구간 폭 ≤ tol -> 가운데 오차 ≤ tol/2, 한 번 다듬기(g) 로 |g'| = LAM/(gm/ID) 배 줄어든다
    assert abs(V["nb"] - v_star) <= tol / 2 * (LAM / Oracle.gm_id(v_star)) + 1e-12
    log = {e.nodes: e for e in snap.value("graph", DC_KEY, "dc_scc_log")}[("nb",)]
    # 구간 = 레일 [0, 1.8] ∩ vds(= x) ∈ [0, 1.8] ∩ vsb(= 0) ∈ VS 격자 -> [0, 1.8]; 반복 수 = k_max(1.8, tol)
    assert log.iterations == math.ceil(math.log2(1.8 / tol))
    assert log.k_max == log.iterations and log.tol == pytest.approx(tol, rel=1e-9)
    # M2 는 종속(parallel): ln_idu = ln IDu(vgs = V(nb), vds = V(out))
    assert abs(dict(snap.column("device", "dc_ln_idu"))["M2"] - Oracle.ln_idu("nmos", V["nb"], V["out"], 0.0)) <= 1e-9


def test_source_follower_one_variable(tmp_path, toy_access):
    """M1 nmos (vdd, in, out): out 은 vgs_source 1변수(vds = 1.8 − x, vsb = x). 근은 이 test 의 독립 이분법(1e-12)으로."""
    doc = topo("bc_sf", [mos("M1", "nmos", "vdd", "in", "out"), mos("M2", "nmos", "out", "vb", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, bias=["vb"])               # vb: M2 gate 에만
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["out"].relation, w["out"].element) == ("vgs_source", "M1")
    x1 = Oracle.ln_idu("nmos", 0.6, 0.9, 0.5)
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): x1,
          ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.55, 0.6, 0.0)}
    for k, key in kschema(ctx).components:
        if k == "y":
            th[(k, key)] = 0.7
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    vin = V["in"]

    def h(x):
        return x - (vin - Oracle.vgs_of("nmos", x1, 1.8 - x, x))
    lo, hi = 0.0, 1.8
    for _ in range(200):
        m = 0.5 * (lo + hi)
        if (h(m) > 0) == (h(lo) > 0):
            lo = m
        else:
            hi = m
    root = 0.5 * (lo + hi)
    assert abs(V["out"] - root) <= Oracle.tol_v() / 2


@pytest.mark.parametrize("v_star", [2.0, -0.3])
def test_no_root_in_window(tmp_path, toy_access, v_star):
    """근이 레일 밖(2.0 V) 또는 VGS 격자 아래(−0.3 V): g 가 ±inf(목표 밖) -> 끝 부호 같음 -> no_root_in_window."""
    ctx = _mirror_ctx(tmp_path, toy_access)
    th = _mirror_theta(ctx, v_star)
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run_of(ctx))
    d = detail(ei.value)
    assert d["reason"] == "no_root_in_window"
    assert d["item"] in (6, 7)
    assert ei.value.record.devices == ("M1",)
    assert d["node"] == "nb"
    for k in ("lo", "hi", "h_lo", "h_hi", "bounds"):
        assert k in d
    assert d["lo"] == 0.0 and d["hi"] == 1.8
    assert ei.value.record.margin is None                     # 두 끝 |h| 모두 무한


def test_vdsat_not_in_window(ctx_c):
    """창은 인접 전도 소자 반대 단자 전압만으로 정해진다(VDsat 여유 없음): y = 0 -> out 이 정확히 0 V."""
    th = theta_c(y=0.0, x1=Oracle.ln_idu("nmos", 0.6, 0.0, 0.0), x2=Oracle.ln_idu("pmos", 0.7, 1.8, 0.0))
    snap = run_blocks(ctx_c[2], th, upto="columns")
    assert node_voltages(snap)["out"] == 0.0


def test_vdsat_not_in_window_even_with_column(ctx_r4c):
    """[r4] (3) VDSAT 열이 있는 LUT 에서도 W4 창에 VDsat 항이 없다: y = 0 / 1 -> out 이 정확히 레일(창 = [0, 1.8])."""
    for y in (0.0, 1.0):
        snap = run_blocks(ctx_r4c, theta_r4c(y=y), upto="columns")
        w = dict(snap.column("node", "dc_window"))["out"]
        assert (w.lo, w.hi) == (0.0, 1.8)
        assert node_voltages(snap)["out"] == 1.8 * y


# ---------------------------------------------------------------------------
# [r4] 1변수 구간의 VDS 정의역 하한(on_mask 유도) + 구간 끝 부동소수 안쪽 보정 + 반복 중/strict 의 lut_curve_undefined
# ---------------------------------------------------------------------------
# LUT F : nmos VDS 열 0 꺼짐(하한 0.25), pmos 열 0~3 꺼짐(하한 1.0) -- LUT v2 의 VDS = 0 열(ID = GM = 0) 모양.
# LUT F2: nmos 는 열 0 켜짐, 열 1 에 꺼진 점 하나(L 2e-6·VGS 0.625·VS 0.25) -> '끝 열까지 모두 켜진 첫 열' = 열 2(0.5);
#         pmos 는 열 0 꺼짐 + 마지막 열에 꺼진 점 하나(L 2e-6·VS 2.0) -> 끝까지 켜진 열이 없다 -> VDS 격자 최소(0.0).
F_OFF = {"nmos": 1, "pmos": 4}
F2_OFF_COLS = {"pmos": 1}
F2_OFF_POINTS = {"nmos": [(1, 5, 1, 3)], "pmos": [(1, 3, 8, 10)]}


def _floor(kind, which):
    if which == "F":
        return r4_vds_floor(r4_arrays(kind, off_cols=F_OFF[kind]))
    return r4_vds_floor(r4_arrays(kind, off_cols=F2_OFF_COLS.get(kind, 0), off_points=F2_OFF_POINTS[kind]))


def test_floor_oracle_values():
    """기대값 원천 확인(피검 아님): on_mask 로 유도한 하한."""
    assert _floor("nmos", "F") == 0.25 and _floor("pmos", "F") == 1.0
    assert _floor("nmos", "F2") == 0.5 and _floor("pmos", "F2") == 0.0
    # 판별력: '처음 모두 켜진 열'(끝까지 요구 없음) 규칙이면 F2 nmos 0.0, F2 pmos 0.25 가 된다
    a = r4_arrays("pmos", off_cols=1, off_points=F2_OFF_POINTS["pmos"])
    on = (a["ID"] > 0) & (a["GM"] > 0)
    assert on[:, :, 1, :].all() and not on[:, :, 8, :].all()


@pytest.fixture(scope="module")
def acc_f(tmp_path_factory):
    return new_access(write_r4_lut(tmp_path_factory.mktemp("lut_f"), off_cols=F_OFF))


@pytest.fixture(scope="module")
def acc_f2(tmp_path_factory):
    return new_access(write_r4_lut(tmp_path_factory.mktemp("lut_f2"), off_cols=F2_OFF_COLS, off_points=F2_OFF_POINTS))


def _diode_ctx(tmp_path, acc, kind, supplies=None):
    """kind 의 diode M1(1변수 노드 nb) + 거울 M2 + 반대 kind 부하 M3. bulk = source 레일(vsb 0)."""
    if kind == "nmos":
        net = [mos("M1", "nmos", "nb", "nb", "gnd", "gnd"), mos("M2", "nmos", "out", "nb", "gnd", "gnd"),
               mos("M3", "pmos", "out", "in", "vdd", "vdd")]
        src = two("I1", "current_source", "vdd", "nb")
    else:
        net = [mos("M1", "pmos", "nb", "nb", "vdd", "vdd"), mos("M2", "pmos", "out", "nb", "vdd", "vdd"),
               mos("M3", "nmos", "out", "in", "gnd", "gnd")]
        src = two("I1", "current_source", "nb", "gnd")
    doc = topo("r4_diode_%s" % kind, net, {"in": ("input", "x"), "out": ("output", "y")}, sources=[src])
    return build_ctx(tmp_path, doc, acc, supplies=supplies, element_values=(("I1", 1e-5),))[2]


def _diode_theta(ctx, kind, vgs1):
    """M1 diode 의 vgs = vds = vgs1 이 근이 되는 좌표. out 은 y = 0.25(M2·M3 VDS 가 두 LUT 하한 위)."""
    other = "pmos" if kind == "nmos" else "nmos"
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("ln_idu", "M1"): r4_ln_idu(kind, vgs1, vgs1, 0.0),
          ("ln_idu", "M3"): r4_ln_idu(other, 0.7, 1.35, 0.0), ("y", "out"): 0.25}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5, "I1": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def _no_root(ctx, th):
    with pytest.raises(SealViolationError) as ei:
        run_blocks(ctx, th, upto="columns")
    d = detail(ei.value)
    assert d["reason"] == "no_root_in_window" and ei.value.record.devices == ("M1",) and d["node"] == "nb"
    return d


@pytest.mark.parametrize("which", ["F", "F2"])
def test_floor_is_interval_lo_nmos_diode(tmp_path, acc_f, acc_f2, which):
    """nmos diode: vds = x -> 구간 lo = VDS 정의역 하한(on_mask 유도), 끝 출처 vds_axis -> item 7."""
    ctx = _diode_ctx(tmp_path, acc_f if which == "F" else acc_f2, "nmos")
    d = _no_root(ctx, _diode_theta(ctx, "nmos", 2.0))          # 근이 레일 위 -> 두 끝 h 같은 부호
    assert d["lo"] == _floor("nmos", which) and d["hi"] == 1.8
    assert "vds_axis" in d["bounds"] and d["item"] == 7


def test_floor_is_interval_hi_pmos_diode(tmp_path, acc_f):
    """pmos diode: vds = 1.8 − x ≥ 하한 1.0 -> 구간 hi = 0.8."""
    ctx = _diode_ctx(tmp_path, acc_f, "pmos")
    d = _no_root(ctx, _diode_theta(ctx, "pmos", 2.0))
    assert d["lo"] == 0.0 and d["hi"] == 1.8 - _floor("pmos", "F")
    assert "vds_axis" in d["bounds"] and d["item"] == 7


def test_root_below_floor_is_no_root(tmp_path, acc_f):
    """근(vds 0.6)이 pmos 하한 1.0 아래 -> 구간 밖 -> no_root_in_window(item 7, 유한 끝 |h| -> margin 있음)."""
    ctx = _diode_ctx(tmp_path, acc_f, "pmos")
    d = _no_root(ctx, _diode_theta(ctx, "pmos", 0.6))
    assert d["hi"] == 0.8 and d["item"] == 7


@pytest.mark.parametrize("kind,vgs1", [("nmos", 0.3), ("nmos", 0.6), ("pmos", 1.2)])
def test_root_above_floor_solved(tmp_path, acc_f, kind, vgs1):
    """하한 위의 근은 풀린다(r3 는 구간 끝 VDS = 0 의 lut_curve_undefined 로 실패하던 모양). 반복 수 = k_max(구간 폭, tol)."""
    ctx = _diode_ctx(tmp_path, acc_f, kind)
    snap = run_blocks(ctx, _diode_theta(ctx, kind, vgs1), upto="columns")
    V = node_voltages(snap)
    log = {e.nodes: e for e in snap.value("graph", DC_KEY, "dc_scc_log")}[("nb",)]
    want = vgs1 if kind == "nmos" else 1.8 - vgs1
    assert abs(V["nb"] - want) <= log.tol
    width = 1.8 - _floor(kind, "F")
    assert log.iterations == math.ceil(math.log2(width / log.tol))


def test_floor_cached_in_lut_memo(tmp_path, acc_f):
    """값은 LUT memo derived 영역 키 ("vds_floor", kind, w_key) 에 슬라이스당 1회 (card 20261104-hcs: 정본 `derived(memo, "vds_floor", ...)`)."""
    ctx = _diode_ctx(tmp_path, acc_f, "nmos")
    run_blocks(ctx, _diode_theta(ctx, "nmos", 0.6), upto="columns")
    misses = dict(acc_f.memo.stats())["derived"].misses

    def not_cached():
        raise AssertionError("하한이 derived memo 에 없다")
    assert acc_f.memo.lookup("derived", "vds_floor", ("nmos", 100), not_cached) == _floor("nmos", "F")
    run_blocks(ctx, _diode_theta(ctx, "nmos", 0.45), upto="columns")
    assert dict(acc_f.memo.stats())["derived"].misses == misses


def test_no_fully_on_suffix_falls_back_to_vds_min(tmp_path, acc_f2):
    """끝 열까지 모두 켜진 열이 없으면 하한 = VDS 격자 최소(r3 그대로): pmos diode 구간 끝 vds = 0 이 꺼진 열이라 strict 1변수
    bisection 의 끝점 평가가 lut_curve_undefined -> lut_query_failed. (잘못된 '처음 켜진 열' 규칙이면 하한 0.25 로 풀린다.)"""
    ctx = _diode_ctx(tmp_path, acc_f2, "pmos")
    with pytest.raises(SealViolationError) as ei:
        run_blocks(ctx, _diode_theta(ctx, "pmos", 0.6), upto="columns")
    d = detail(ei.value)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_curve_undefined"
    assert ei.value.record.devices == ("M1",)
    assert d["vds"] == 0.0


def test_interval_end_nextafter_inside_axis(tmp_path, acc_f):
    """gnd = 0.1 V: x_lo = (0.25 − a)/b 가 부동소수 반올림으로 vds = 0.24999999999999997(하한 밖, 꺼진 열과 보간)이 되는 구성.
    구간 끝은 축 안으로 nextafter 된다 -> 끝점 조회가 정의역 밖이 되지 않는다(근 풀림, no_root 의 lo 도 축 안)."""
    sup = {"vdd": 1.8, "gnd": 0.1}
    F = _floor("nmos", "F")
    a = 1.0 * (0.0 - 0.1)
    b = 1.0 * (1.0 - 0.1) - a
    x_naive = (F - a) / b
    assert 1.0 * (x_naive - 0.1) < F                           # 전제: 보정 없으면 축 밖
    ctx = _diode_ctx(tmp_path, acc_f, "nmos", supplies=sup)
    d = _no_root(ctx, _diode_theta(ctx, "nmos", 2.0))
    assert 1.0 * (d["lo"] - 0.1) >= F and d["lo"] > x_naive
    assert d["lo"] - x_naive <= 4 * math.ulp(x_naive)
    snap = run_blocks(ctx, _diode_theta(ctx, "nmos", 0.6), upto="columns")
    log = {e.nodes: e for e in snap.value("graph", DC_KEY, "dc_scc_log")}[("nb",)]
    assert abs(node_voltages(snap)["nb"] - 0.7) <= log.tol


@pytest.mark.parametrize("vout,ok", [(0.1, False), (0.24, False), (0.26, True), (0.5, True)])
def test_acyclic_writer_below_floor_is_strict_failure(tmp_path, acc_f, vout, ok):
    """비순환(strict) writer 의 VDS 가 하한 아래면 lut_curve_undefined 그대로 실패(일시 이탈 규칙은 반복 중에만)."""
    ctx = build_ctx(tmp_path, circuit_cs_res(bulk_m1="gnd"), acc_f)[2]
    i = 1e-5
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, max(vout, 0.25), 0.0),
          ("current", "R1"): i, ("resistance", "R1"): (1.8 - vout) / i}
    if ok:
        V = node_voltages(run_blocks(ctx, th, upto="columns"))
        assert abs(V["out"] - vout) <= 1e-12
        assert abs(V["in"] - r4_vgs_of("nmos", th[("ln_idu", "M1")], V["out"], 0.0)) <= 1e-9
    else:
        with pytest.raises(SealViolationError) as ei:
            run_blocks(ctx, th, upto="columns")
        d = detail(ei.value)
        assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_curve_undefined"
        assert d["device_query"] == "vgs_of_coordinate" and ei.value.record.devices == ("M1",)


def _cycle_ctx(tmp_path, acc, kind_a, vin):
    """다변수 순환 SCC {x, y}: MA(kind_a) 가 gate x 를 쓰고(vgs_gate, drain = y -> y 에 의존), MB nmos (d = x, g = in, s = y,
    b = y) 가 y 를 쓴다(vgs_source, 1변수 -- drain x 에 의존). 이상 전류원 IX·IY 가 KCL 을 닫는다.
    [U4 갱신] in 은 **입력 DC 선언**(`input_dc_v = vin`, writer input_dc). 옛 판은 in 을 입력 DC 미선언 W4(창 = 레일 범위,
    V(in) = y·1.8)로 두었으나, 사용자 결정 J-E(설계 41 §4.6 '입력 DC 정책' SP-2 (c), 40 §11 'J 추가 범위' U4, 확인 행 D-J5)로
    입력 DC 대기 회로의 y_icm 범위는 레일이 아니라 입력 포화 창이 되었다 -- 이 test 들이 겨냥하는 규칙(5.4 [r4] 반복 중 일시
    이탈·strict 재검증)은 V(in) 값과 무관하므로 J-E 의 '선언 입력 DC 유지'(같은 절) 경로로 V(in) 을 그대로 고정한다."""
    if kind_a == "pmos":
        net = [mos("MA", "pmos", "y", "x", "vdd", "vdd"), mos("MB", "nmos", "x", "in", "y", "y")]
        src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "y", "gnd")]
    else:
        net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
        src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    doc = topo("r4_cycle_%s" % kind_a, net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)
    ctx = build_ctx(tmp_path, doc, acc, input_dc_v=vin)[2]
    assert dict(ctx.base.column("node", "dc_writer"))["in"].relation == "input_dc"
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["x"].relation, w["x"].element) == ("vgs_gate", "MA")
    assert (w["y"].relation, w["y"].element) == ("vgs_source", "MB")
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [set(e.nodes) for e in cyc] == [{"x", "y"}]
    return ctx


def _cycle_theta(kind_a, vin, x, y, vgs_a=0.6, vgs_b=0.6):
    """해 (x, y) 가 정확히 나오는 θ: MA 는 vgs_a 를 VDS(MA) 에서, MB 는 vgs_b 를 VDS(MB) = x − y 에서 낸다."""
    vds_a = (1.8 - y) if kind_a == "pmos" else y
    return {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("current", "MA"): 1e-5, ("current", "MB"): 1e-5,
            ("ln_idu", "MA"): r4_ln_idu(kind_a, vgs_a, max(vds_a, 0.25), 0.0),
            ("ln_idu", "MB"): r4_ln_idu("nmos", vgs_b, x - y, 0.0)}           # [U4] in = 선언 입력 DC -> y 성분 없음


def test_cyclic_transient_below_floor_tolerated(tmp_path, acc_f):
    """[r4] 5.4: 반복 중(strict=False)에는 MOS writer 의 하한 아래 lut_curve_undefined 가 일시 이탈(현재 값 유지).
    MA pmos(하한 1.0)의 시작값 계산은 계약 5.4 2단계 'VDS = 레일 범위/2 = 0.9' 라 하한 아래 -> 거부하면 안 된다.
    수렴점: x = 1.8 − 0.6 = 1.2, y = vin − 0.6 = 0.5 (VDS(MA) = 1.3 ≥ 1.0, VDS(MB) = 0.7 ≥ 0.25 -> strict 검증도 통과)."""
    assert 0.9 < _floor("pmos", "F")                           # 전제: 2단계 시작 VDS 가 하한 아래
    ctx = _cycle_ctx(tmp_path, acc_f, "pmos", 1.1)
    th = _cycle_theta("pmos", 1.1, 1.2, 0.5)
    assert set(th) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    log = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if set(e.nodes) == {"x", "y"}][0]
    assert abs(V["x"] - 1.2) <= log.tol and abs(V["y"] - 0.5) <= log.tol


@pytest.mark.parametrize("vin,ok", [(0.7, False), (0.75, False), (0.9, True)])
def test_cyclic_strict_recheck_below_floor_fails(tmp_path, acc_f, vin, ok):
    """MA nmos(하한 0.25)의 수렴점 VDS = V(y) = vin − 0.6 이 하한 아래(0.1·0.15)면 반복 중 일시 이탈이어도 수렴 뒤 strict 검증에서
    거부(투영이 최종값에 남지 않는다). 0.9 -> y = 0.3 ≥ 0.25 이면 풀린다.
    [LM-1e A-159] 기대 사유: lut_query_failed(lut_curve_undefined) -> tol_v_undefined. 하한 아래 VDS 소자의 첫 칸 셀 None 이 셀 결합 규칙('하나라도
    None 이면 None', interface §5)으로 tol None 이 되고, SCC 소자 tol 조회 뒤 거부가 사유를 앞당긴다. 거부 자체는 유지(oracle (d) interface §8)."""
    ctx = _cycle_ctx(tmp_path, acc_f, "nmos", vin)
    y = vin - 0.6
    th = _cycle_theta("nmos", vin, 0.6, y)
    assert set(th) == set(kschema(ctx).components)
    if ok:
        V = node_voltages(run_blocks(ctx, th, upto="columns"))
        assert V["y"] >= _floor("nmos", "F") and abs(V["y"] - y) <= 0.01 and abs(V["x"] - 0.6) <= 0.01
    else:
        assert y < _floor("nmos", "F")                       # 전제(손 계산, detail 비의존): 수렴점 VDS = y 가 하한 아래
        with pytest.raises(SealViolationError) as ei:
            run_blocks(ctx, th, upto="columns")
        d = detail(ei.value)
        assert d["reason"] == "tol_v_undefined"
        assert ei.value.record.devices == ("MA",)


def test_gs_nonstrict_rootless_window_keeps_current_iterate_and_final_is_rejected(tmp_path, acc_f, monkeypatch):
    """[WB-1 D-7, interface SD-1 'GS 비엄격'] 다변수 순환 SCC {x, y} 의 반복 중(strict=False) 1변수 노드 y 가 근이 없으면 **현재 반복값을 그대로 유지**한다
    (구간 끝·가운데·작은 |h| 끝점으로 바꾸지 않는다); 수렴 뒤 strict 바퀴는 그대로 실패시킨다(투영이 최종값에 남지 않는다).
    손 회로: _cycle_ctx(nmos) 에서 입력 DC 0.5 V 로 선언하고 MB 의 VGS 를 0.6 V 로 두면 y* = V(in) − VGS_B = −0.1 V < 레일 하단 0 V
    -> y 의 어느 구간에도 근이 없다(h 끝 부호 같음, oracle (a) 손 계산). 반복 시작값 y = 0.75 V(레일 중앙의 시작 규칙이 아니라 호출 때 받은 현재값)가 그대로 돌아와야 하고
    반복 수 0 으로 보고된다. 호출 감시는 공개 메서드 `_Circuit.solve_self` 의 입출력만 읽는다(값 계산 아님). spy 는 서명 독립이다: `(*args, **kwargs)` 로 받아 그대로 넘기고
    `inspect.signature(...).bind` 로 이름 인자 `net`·`values`·`strict` 만 읽는다(관찰 대상 이름은 그대로, 풀이 상태 인자가 더해져도 무관).
    거부 케이스 pytest.raises 1(수렴 뒤 strict 바퀴는 근 없음 `no_root_in_window` 이거나 후속 실패라 SealViolationError 만 단언)."""
    from gmid_engine.sizing import block_dc
    real = block_dc._Circuit.solve_self
    calls = []

    sig = inspect.signature(real)

    def spy(self, *args, **kwargs):
        out = real(self, *args, **kwargs)
        bound = sig.bind(self, *args, **kwargs)
        bound.apply_defaults()
        net, values, strict = (bound.arguments[k] for k in ("net", "values", "strict"))
        calls.append((net, strict, values[net], out))
        return out

    monkeypatch.setattr(block_dc._Circuit, "solve_self", spy)
    vin = 0.5
    ctx = _cycle_ctx(tmp_path, acc_f, "nmos", vin)
    th = _cycle_theta("nmos", vin, 0.6, 0.1, vgs_b=0.6)               # y* = 0.5 − 0.6 = −0.1 (θ 의 y 인자는 MA 의 VDS 용일 뿐)
    assert set(th) == set(kschema(ctx).components)
    assert vin - 0.6 < 0.0                                             # 전제(손): 근이 레일 하단 0 V 아래
    with pytest.raises(SealViolationError):
        run_blocks(ctx, th, upto="columns")
    loose = [c for c in calls if c[0] == "y" and not c[1]]
    assert loose, "전제: 반복 중 y 의 비엄격 풀이가 불렸다"
    for _net, _strict, current, (value, iterations, _tol) in loose:
        assert value == current and iterations == 0                  # 현재 반복값 그대로, 반복 0


# ===========================================================================
# [r9] 성능 항목 1·6 (사용자 승인 2026-10-08) -- solve_self 입력 재사용, tol_V 셀 한 평가 안 재사용 (CONTRACT 5.4, 5.6c)
# ===========================================================================
# 관찰 방법(공개 주입점): lut `LutMemo.lookup(region, fn_name, key, compute)`(lut CONTRACT 2절)를 감싼 하위 클래스를 `LutAccess` 에
# 넣는다. 계약 5.6c 가 solve_self 저장 위치를 'LUT memo root 영역, 함수 이름 칸 solve_self' 로 정했으므로 그 조회의 compute 가
# 돌았는지(= 적중 아님)와 그 compute 안에서 일어난 VGS 역산 조회 수(= h 평가 수: 5.4 'VGS(좌표) = lut vgs_for_current_density'
# -- [U3] 계획 DEC-88 '쓰기 소자 VGS 는 vgs_for_current_density 로' 에 따라 옛 임시 우회 gm_id_for_target 을 대체, memo 함수 이름 칸
# `vgs_for_current_density`; h(x) = x − g(x) 한 번에 VGS 역산 한 번)를 센다. `tol_v_table` 조회 결과는 `.at` 호출을 세는 대리로 돌려준다(5.6c '한 평가 안에서
# 같은 (소자, VDS) 의 tol_v_cell 조회를 한 번만'; tol_v_cell = tol_v_table(kind, w_key).at(L, vds, "id_equivalent"), 6절 표 tol 행).

SOLVE_SELF = "solve_self"                    # CONTRACT 5.6c: memo root 영역 함수 이름 칸


class _AtCounter:
    """TolVTable 대리: `.at(...)` 인자를 (kind,) + 인자 로 기록하고 원래 표에 넘긴다."""

    def __init__(self, table, sink, kind):
        self._table, self._sink, self._kind = table, sink, kind

    def at(self, *args, **kw):
        self._sink.append((self._kind,) + tuple(args) + tuple(sorted(kw.items())))
        return self._table.at(*args, **kw)

    def __getattr__(self, name):
        return getattr(self._table, name)


class CountingMemo(LutMemo):
    """조회 기록: log = [(solve_self compute 안 깊이, region, fn_name)], at_calls = tol_v_table.at 인자."""

    def __init__(self, lut, n=4096):
        super().__init__(lut, point=n, curve=n, root=n)
        self.log, self.at_calls, self.self_computes, self._depth = [], [], 0, 0

    def lookup(self, region, fn_name, key, compute):
        self.log.append((self._depth, region, fn_name))
        if fn_name == SOLVE_SELF:
            def counted():
                self.self_computes += 1
                self._depth += 1
                try:
                    return compute()
                finally:
                    self._depth -= 1
            return super().lookup(region, fn_name, key, counted)
        value = super().lookup(region, fn_name, key, compute)
        if fn_name == "tol_v_table":
            return _AtCounter(value, self.at_calls, tuple(key)[0])
        return value

    def reset(self):
        self.log.clear()
        self.at_calls.clear()
        self.self_computes = 0

    def solve_self_lookups(self):
        return sum(1 for _, r, fn in self.log if (r, fn) == ("root", SOLVE_SELF))

    def h_evaluations(self):
        return sum(1 for d, r, fn in self.log if d > 0 and fn == "vgs_for_current_density")


def kmax_ref(width, tol):
    """CONTRACT 5.6 독립 구현."""
    return 1 if width <= tol else math.ceil(math.log2(width / tol))


def _counting_ctx(tmp_path, toy_lut, doc, **kw):
    memo = CountingMemo(toy_lut)
    return memo, build_ctx(tmp_path, doc, LutAccess(memo), **kw)[2]


def _mirror_doc():
    """_mirror_ctx 와 같은 회로: M1 diode (nb, nb, gnd) = 1변수 노드 nb(SCC 0), M2 (out, nb, gnd), M3 pmos (out, in, vdd), I1 -> nb."""
    return topo("bc_mirror_r9",
                [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                 mos("M3", "pmos", "out", "in", "vdd")],
                {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "nb")])


def _nb_log(snap):
    (log,) = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if tuple(e.nodes) == ("nb",)]
    return log


def test_solve_self_identical_inputs_reused_zero_h_evaluations(tmp_path, toy_lut):
    """5.6c: 풀이는 (종류, L, ln IDu, 관계, known, 1차식 계수, 구간, tol) 만의 함수라 memo 에 저장 -- 적중하면 h 평가 0, 같은 결과.
    nb 의 입력과 무관한 θ 성분(y(out) -- out 은 nb 뒤 비순환 W4)만 바꿔 dc_solve 를 다시 계산하게 한다(FD 형제 평가 모양).
    oracle: (a) 근 = θ 를 만든 v* = 0.6(toy 닫힌 식), 오차 상계 = 기존 diode test 와 같은 tol/2·|g'|; (c) 첫 평가 결과와 비트 동일."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), element_values=(("I1", 1e-5),))
    th = _mirror_theta(ctx, 0.6)
    tol = Oracle.tol_v()
    memo.reset()
    s1 = run_blocks(ctx, th, upto="columns")
    h1 = memo.h_evaluations()
    assert memo.solve_self_lookups() == 1 and memo.self_computes == 1          # 1변수 노드 하나, 첫 호출은 계산
    K = kmax_ref(1.8, tol)
    assert 2 <= h1 <= 2 * K + 6 + 1                                            # 끝점 2 + 상계(5.6c) + 한 번 다듬기
    th2 = dict(th)
    th2[("y", "out")] = 0.7
    memo.reset()
    s2 = run_blocks(ctx, th2, upto="columns")
    V1, V2 = node_voltages(s1), node_voltages(s2)
    assert V2["out"] != V1["out"]                                              # 전제: dc_solve 가 실제로 다시 계산됐다
    assert memo.solve_self_lookups() == 1 and memo.self_computes == 0          # 적중
    assert memo.h_evaluations() == 0                                           # h 평가 0
    assert V2["nb"] == V1["nb"]                                                # 같은 결과(비트)
    assert _nb_log(s2) == _nb_log(s1)
    assert abs(V2["nb"] - 0.6) <= tol / 2 * (LAM / Oracle.gm_id(0.6)) + 1e-12


@pytest.mark.parametrize("change", ["ln_idu", "L"])
def test_solve_self_key_sensitive(tmp_path, toy_lut, change):
    """키에 든 입력(ln IDu, L -- 5.6c 키 목록)이 바뀌면 적중하지 않고 다시 푼다(h 평가 > 0). toy 는 IDu 가 L 무관이라 L 만 바꾸면
    근이 같다 -- 그래도 키가 다르므로 다시 계산해야 한다(실 LUT 는 L 마다 곡선이 다르다). oracle (a): 근 v*."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), element_values=(("I1", 1e-5),))
    th = _mirror_theta(ctx, 0.6)
    run_blocks(ctx, th, upto="columns")
    th2 = _mirror_theta(ctx, 0.62) if change == "ln_idu" else dict(th, **{})
    v_star = 0.62 if change == "ln_idu" else 0.6
    if change == "L":
        th2[("L", "M1")] = 2e-6
        th2[("L", "M2")] = 2e-6
    memo.reset()
    s2 = run_blocks(ctx, th2, upto="columns")
    assert memo.self_computes == 1 and memo.h_evaluations() >= 2
    tol = Oracle.tol_v()
    assert abs(node_voltages(s2)["nb"] - v_star) <= tol / 2 * (LAM / Oracle.gm_id(v_star)) + 1e-12


def test_solve_self_log_fields_unchanged(tmp_path, toy_lut):
    """5.4 [r9]: SccLog.iterations·k_max 는 변함없이 k_max(hi − lo, tol)(선언 상한 -- 실제 평가 수 아님), tol = 구간 가운데 writer
    tol_v_cell, method bisection. 구간 = 레일 [0, 1.8] ∩ vds(= x) ∈ [0, 1.8](toy 는 꺼진 열이 없어 하한 = 격자 최소). 적중 평가도 같다.
    oracle (a): toy tol_V 셀(Oracle.tol_v, 모든 셀 같은 값)과 손으로 정한 구간."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), element_values=(("I1", 1e-5),))
    tol = Oracle.tol_v()
    logs = []
    for y in (0.5, 0.3):
        th = _mirror_theta(ctx, 0.45)
        th[("y", "out")] = y
        logs.append(_nb_log(run_blocks(ctx, th, upto="columns")))
    for log in logs:
        assert log.tol == pytest.approx(tol, rel=1e-9)
        assert log.iterations == log.k_max == kmax_ref(1.8 - 0.0, log.tol)
        assert log.method == "bisection" and log.fallback is None
    assert logs[0] == logs[1]


def _no_root_case(tmp_path, toy_lut):
    """vdd = 0.5: diode nb 의 구간 = 레일 [0, 0.5] ∩ vds ∈ [0, 1.8] = [0, 0.5], 근 v* = 0.6 은 구간 밖 -> 두 끝 h 가 유한하고 음수."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), supplies={"vdd": 0.5, "gnd": 0.0},
                              element_values=(("I1", 1e-5),))
    th = _mirror_theta(ctx, 0.6)
    th[("ln_idu", "M3")] = Oracle.ln_idu("pmos", 0.7, 0.25, 0.0)
    order = ctx.base.value("graph", DC_KEY, "dc_scc_order")
    assert order[0].nodes == ("nb",)                                           # 전제: nb 를 먼저 푼다
    return memo, ctx, th


def test_no_root_strict_failure_and_not_cached_as_exception(tmp_path, toy_lut):
    """5.4: 끝 부호가 같으면 SealViolationError(devices (writer,), no_root_in_window, item = 구간 끝 출처에 vds_axis 가 있으면 7
    아니면 6, margin = 유한한 끝 |h| 최솟값/tol, detail node·lo·hi·h_lo·h_hi·bounds). 5.6c: 근 없음 (None, h_lo, h_hi) 도 저장되나
    예외는 저장하지 않는다(부르는 쪽이 만든다) -- 같은 입력 두 번째 평가는 h 평가 0 이고 같은 실패를 다시 낸다.
    oracle (a): h(x) = x − VGS(T, vds = x, vsb = 0)(toy 닫힌 식 Oracle.vgs_of), tol = Oracle.tol_v()."""
    memo, ctx, th = _no_root_case(tmp_path, toy_lut)
    T = th[("ln_idu", "M1")]
    tol = Oracle.tol_v()
    h_lo = 0.0 - Oracle.vgs_of("nmos", T, 0.0, 0.0)
    h_hi = 0.5 - Oracle.vgs_of("nmos", T, 0.5, 0.0)
    assert h_lo < 0 and h_hi < 0                                               # 전제: 같은 부호, 둘 다 유한
    recs = []
    for y in (0.5, 0.7):
        th2 = dict(th)
        th2[("y", "out")] = y
        memo.reset()
        with pytest.raises(SealViolationError) as ei:
            run_blocks(ctx, th2, upto="columns")
        recs.append((ei.value.record, memo.self_computes, memo.h_evaluations()))
    (r1, c1, n1), (r2, c2, n2) = recs
    d = dict(r1.detail)
    assert d["reason"] == REASON_NO_ROOT == "no_root_in_window"
    assert r1.devices == ("M1",) and d["node"] == "nb"
    assert d["lo"] == 0.0 and d["hi"] == 0.5
    assert abs(d["h_lo"] - h_lo) <= 1e-9 and abs(d["h_hi"] - h_hi) <= 1e-9
    assert r1.margin == pytest.approx(min(abs(h_lo), abs(h_hi)) / tol, rel=1e-9)
    assert set(d["bounds"]) <= {"rail", "vds_axis", "vs_axis"}
    assert d["item"] == (7 if "vds_axis" in d["bounds"] else 6)
    assert c1 == 1 and n1 >= 2                                                 # 첫 번째: 계산(끝점 h 2회 이상)
    assert c2 == 0 and n2 == 0                                                 # 두 번째: 저장된 (None, h_lo, h_hi) 적중
    assert r2 == r1                                                            # 같은 실패를 다시 만든다


def _tolrep_doc():
    """다변수 SCC {w, g}: MA nmos (d = vdd, g = g, s = gnd, b = w) 가 g 를 쓰고(vgs_gate, VDS = 1.8 고정 -- 반복 내내 같은 (소자, VDS)),
    MC nmos (d = g, g = gc, s = w) 가 w 를 쓴다(vgs_source 1변수), gc = 입력 DC 1.2 V. MD nmos (w, nb, gnd) 는 w 의 전류 경로."""
    return topo("r9_tol_reuse", [mos("MA", "nmos", "vdd", "g", "gnd", "w"), mos("MC", "nmos", "g", "gc", "w", "gnd"),
                                 mos("MD", "nmos", "w", "nb", "gnd")],
                {"gc": ("input", "x"), "w": ("output", "y")}, sources=[two("IG", "current_source", "vdd", "g")],
                bias=["nb"])                                                     # nb: MD gate 에만


def _tolrep_theta(w_star=0.3, g_star=0.7, la=2e-6):
    """해 (w*, g*) 가 정확히 나오는 θ(toy 닫힌 식): MA vgs = g*, vds 1.8, vsb = −w*; MC vgs = 1.2 − w*, vds = g* − w*, vsb = w*."""
    return {("L", "MA"): la, ("L", "MC"): 1e-6, ("L", "MD"): 1e-6,
            ("ln_idu", "MA"): Oracle.ln_idu("nmos", g_star, 1.8, -w_star),
            ("ln_idu", "MC"): Oracle.ln_idu("nmos", 1.2 - w_star, g_star - w_star, w_star),
            ("ln_idu", "MD"): Oracle.ln_idu("nmos", 0.6, w_star, 0.0), ("current", "MA"): 1e-5, ("current", "MD"): 1e-5}


def _tolrep_ctx(tmp_path, toy_lut):
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _tolrep_doc(), input_dc_v=1.2)
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["g"].relation, w["g"].element) == ("vgs_gate", "MA")             # 전제: 계획(입력)
    assert (w["w"].relation, w["w"].element) == ("vgs_source", "MC")
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [set(e.nodes) for e in cyc] == [{"w", "g"}]
    assert set(kschema(ctx).components) == set(_tolrep_theta())
    return memo, ctx


def test_tol_v_cell_once_per_device_vds_within_one_evaluation(tmp_path, toy_lut):
    """5.6c 성능 항목 6: 한 평가(= 한 dc_solve) 안에서 같은 (소자, VDS) 의 tol_v_cell 조회는 한 번. MA 는 SCC writer MOS(5.4
    Gauss-Seidel 허용오차 = SCC writer MOS tol_v_cell 최솟값, 5.5 'tol = tolerance(current)' 반복마다)이고 VDS = 1.8 이 반복 내내
    같다 -> Gauss-Seidel 이 여러 바퀴 돌아도 (nmos, L 2 µm, 1.8) 조회는 1회. 소자마다 (kind, L) 를 달리해(MA 만 L 2 µm) .at 인자가
    소자를 가른다. oracle (a): 수렴값 = θ 를 만든 해 (0.3, 0.7), tol = toy tol_V 셀(모든 셀 같은 값)."""
    memo, ctx = _tolrep_ctx(tmp_path, toy_lut)
    memo.reset()
    snap = run_blocks(ctx, _tolrep_theta(), upto="columns")
    (log,) = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if set(e.nodes) == {"w", "g"}]
    assert log.method == SCC_GAUSS_SEIDEL and log.iterations >= 2              # 전제: 허용오차를 여러 번 물었다
    V = node_voltages(snap)
    assert abs(V["w"] - 0.3) <= log.tol and abs(V["g"] - 0.7) <= log.tol
    assert log.tol == pytest.approx(Oracle.tol_v(), rel=1e-9)
    calls = collections.Counter(memo.at_calls)
    ma_key = [k for k in calls if k[0] == "nmos" and k[1] == 2e-6 and k[2] == 1.8]
    assert len(ma_key) == 1 and calls[ma_key[0]] == 1                          # MA: (소자, VDS) 하나, 조회 1회
    assert max(calls.values()) == 1                                            # 어떤 (소자, VDS) 도 두 번 묻지 않는다


def test_tol_v_cell_values_identical_across_evaluations(tmp_path, toy_lut):
    """재사용이 값을 바꾸지 않는다: 같은 θ 의 두 평가(사이에 다른 θ 평가)에서 SccLog(tol 포함)·노드전압이 같다."""
    memo, ctx = _tolrep_ctx(tmp_path, toy_lut)
    a = run_blocks(ctx, _tolrep_theta(), upto="columns")
    run_blocks(ctx, _tolrep_theta(w_star=0.25, g_star=0.75), upto="columns")
    b = run_blocks(ctx, _tolrep_theta(), upto="columns")
    assert a.value("graph", DC_KEY, "dc_scc_log") == b.value("graph", DC_KEY, "dc_scc_log")
    assert node_voltages(a) == node_voltages(b)


# ---------------------------------------------------------------------------
# [r9 명시] Gauss-Seidel 수렴 전 SealViolationError 는 Newton 으로 넘기지 않고 그대로 (회귀: r8 까지 UnboundLocalError)
# ---------------------------------------------------------------------------
# 수렴 뒤(경우 2) Newton 인계는 test_scc_newton.py::test_case_two_seal_violation_kept_with_newton_cause 가 본다.

def _scc_s_doc():
    """W4–W4 선형 SCC {vin, vout}(1변수 노드 없음): M1 nmos (vin, nb1, gnd), M2 nmos (vout, nb2, vin), M3 pmos (vout, pb, vdd)."""
    return topo("r9_scc_s", [mos("M1", "nmos", "vin", "nb1", "gnd"), mos("M2", "nmos", "vout", "nb2", "vin"),
                             mos("M3", "pmos", "vout", "pb", "vdd")],
                {"vin": ("input", "single_ended_input"), "vout": ("output", "single_ended_output")},
                bias=["nb1", "nb2", "pb"])                                       # nb1: M1, nb2: M2, pb: M3 gate 에만


@pytest.fixture(scope="module")
def acc_two_point(tmp_path_factory):
    """CONTRACT 5.4 [r3] tol_v_undefined 최소 구성: 보간 축 VGS·VDS·VS 가 모두 2점(0, 1.8) -> 내부 격자점이 없어 모든 tol_V 셀 None."""
    return new_access(write_r4_lut(tmp_path_factory.mktemp("two_point"), grids=(R4_L, (0.0, 1.8), (0.0, 1.8), (0.0, 1.8))))


@pytest.mark.parametrize("y1,y2", [(0.6, 0.4), (0.98, 0.3)])
def test_tol_undefined_before_convergence_propagates(tmp_path, acc_two_point, y1, y2):
    """다변수 SCC 의 허용오차(5.4: SCC writer MOS 가 없으면 d·s·bulk 값이 있는 entry.devices 의 tol_v_cell 최솟값)가 모두 None ->
    Gauss-Seidel 이 수렴하기 전에 SealViolationError(tol_v_undefined, devices = SCC 소자, margin None) 그대로(Newton 인계 없음).
    y1·y2 = 빠른 수축(0.6, 0.4)·느린 수축(0.98, 0.3, Newton 경우 1 이 되는 θ). pytest.raises(SealViolationError) 라 UnboundLocalError
    는 이 test 의 실패가 된다. 공개 경로 두 개(dc_solve 직접, size_and_seal)."""
    ctx = build_ctx(tmp_path, _scc_s_doc(), acc_two_point)[2]
    (entry,) = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert set(entry.nodes) == {"vin", "vout"}
    vout = 1.8 * y2 / (1.0 - y1 * (1.0 - y2))
    vin = y1 * vout
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, vin, 0.0), ("ln_idu", "M2"): r4_ln_idu("nmos", 0.7, vout - vin, vin),
          ("ln_idu", "M3"): r4_ln_idu("pmos", 0.7, 1.8 - vout, 0.0), ("y", "vin"): y1, ("y", "vout"): y2}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    for call in (lambda: run_blocks(ctx, th, upto="columns"), lambda: size_and_seal(ctx, th, hand_wf(ctx))):     # [FS-1 서명 맞춤] wf 인자
        with pytest.raises(SealViolationError) as ei:
            call()
        e = ei.value
        assert dict(e.record.detail)["reason"] == REASON_TOL_UNDEFINED == "tol_v_undefined"
        assert e.record.devices == entry.devices and e.record.margin is None
        assert not isinstance(e.__cause__, NonconvergentError)                # Newton 으로 넘기지 않았다


def test_non_transient_lut_failure_before_convergence_propagates(tmp_path, toy_lut):
    """반복 중(strict=False)에도 일시 이탈로 보지 않는 LUT 실패(5.4: 일시 이탈 = axis/target 밖·하한 아래 curve_undefined 뿐) --
    다변수 SCC 의 MOS writer MA 의 L 이 앵커가 아님(1.5 µm, toy L 앵커 1·2 µm) -> 수렴 전 SealViolationError(lut_query_failed,
    lut_reason lut_l_not_anchor, devices (MA,)) 그대로. device_query 는 MA 를 처음 묻는 곳(VGS 역산 또는 허용오차 셀)."""
    memo, ctx = _tolrep_ctx(tmp_path, toy_lut)
    for call in (lambda: run_blocks(ctx, _tolrep_theta(la=1.5e-6), upto="columns"),
                 lambda: size_and_seal(ctx, _tolrep_theta(la=1.5e-6), hand_wf(ctx))):     # [FS-1 서명 맞춤] wf 인자
        with pytest.raises(SealViolationError) as ei:
            call()
        e = ei.value
        d = dict(e.record.detail)
        # [WB-1 §4] 합성 bin 지도 도입 -> lut_l_not_anchor 가 lut_l_bin_unbracketed 로(card 목록)
        assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_l_bin_unbracketed"
        assert d["device_query"] in ("vgs_of_coordinate", "tol_v_cell")
        assert e.record.devices == ("MA",)
        assert not isinstance(e.__cause__, NonconvergentError)


# ---------------------------------------------------------------- [U17 ①-d] d/s 반대 선언 -> 봉인 7 거부
# 사용자 결정 2026-10-13 "1은 권고"(라)(오케스트레이터 전달): "topology d/s 표기 = 물리 방향 선언 ... 사이징 결과(writer 계획·θ 스키마·ties)는 선언 방향을
# 따름. 틀린 선언은 봉인 7(VDS−VDsat ≥ tol)이 거부."
# 손 유도: 회로 C(M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd))의 두 MOS 를 모두 d/s 반대로 선언한다 -- M1 d=gnd·s=out, M2 d=vdd·s=out.
# (하나만 뒤집으면 KCL 이 I_M1 = −I_M2 < 0 을 요구해 전류 원뿔에서 먼저 거부되고, 둘 다 뒤집어야 선언 방향 전류가 양수로 맞는다.)
# 선언 방향의 VDS: M1 = V(gnd) − V(out) = −V(out), M2(pmos VSD) = V(out) − V(vdd). out 은 레일 창 [0, 1.8] V 안이므로 M1 의 VDS ≤ 0 이고
# VDS ≥ VDsat + tol > 0 을 만족하는 V(out) 이 창 안에 없다 -> 봉인 7(item 7) 거부, 소자 M1, 노드 out(M1 의 vgs_source 로 쓰는 노드), 원인 축 VDS.
# 대조: 바르게 선언한 같은 회로·같은 θ 값은 봉인 7 을 통과한다(test_seal_region 의 통과 점 (y, v1, v2) = (0.5, 0.6, 0.7) 과 같은 동작점).

def _reversed_c():
    return topo("hand_cs_pload_rev", [mos("M1", "nmos", "gnd", "in", "out"), mos("M2", "pmos", "vdd", "pb", "out")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["pb"])


def _theta_for(ctx, v1=0.6, v2=0.6, y=0.5):
    from .conftest import r4_ln_idu
    th = {}
    for t, k in kschema(ctx).components:
        if t == "L":
            th[(t, k)] = 1e-6
        elif t == "current":
            th[(t, k)] = 1e-5
        elif t == "y":
            th[(t, k)] = y
        elif t == "ln_idu":
            th[(t, k)] = r4_ln_idu("nmos" if k == "M1" else "pmos", v1 if k == "M1" else v2, 0.5, 0.0)
    return th


def test_reversed_ds_declaration_rejected_by_seal7(tmp_path, r4_access):
    from .conftest import with_tol
    ctx = build_ctx(tmp_path, _reversed_c(), r4_access)[2]
    writer = dict(ctx.base.column("node", "dc_writer"))["out"]
    assert (writer.relation, writer.element) == ("vgs_source", "M1")     # 전제: out = V(in) − VGS(M1), 선언 source 기준
    with pytest.raises(SealViolationError) as e:
        with_tol(ctx, _theta_for(ctx))
    d = detail(e.value)
    assert d["item"] == 7
    assert tuple(e.value.record.devices) == ("M1",)
    assert d["node"] == "out"
    assert "vds_axis" in d["bounds"]                                         # 원인 = 선언 방향 VDS 축(VDS ≥ 0 이 되는 V(out) ≤ 0)
    assert d["hi"] <= 0.0                                                    # 창 상한: −V(out) ≥ 0 -> V(out) ≤ 0(손 유도 VDS 부호)


def test_correct_ds_declaration_same_point_passes_seal7(tmp_path, r4_access):
    from gmid_engine.sizing import dc_seal_region
    from .conftest import circuit_cs_pmos_load, seal_item, theta_r4c, with_tol
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), r4_access)[2]
    snap, _ = with_tol(ctx, theta_r4c(y=0.5, v1=0.6, v2=0.7))
    assert seal_item(dc_seal_region(snap, ctx.lut, **run_of(ctx)), 7).status == "pass"


# ===========================================================================
# [card IT-2b] 커널 창 `node.dc_window`(모든 입력 포트 + W4 뿌리) -- design 41 v1.12.8 4.7-2·4.7-3, 4.7-7 K1·K2·P(b)·L12(b)
# 칸 `Window(lo, hi, constraints, input_status=None, tol_v=None, status_detail=())`.
# 입력 포트 항목: 입력 DC 선언 포트 = 같은 x 로 함께 움직이는 묶음의 이동량 창(4.7-3 3), 미선언 뿌리 = A6 되풀이 창, 뿌리 아닌 포트 = 뿌리 창 끝을 같은 해의
# 감도로 옮긴 [min, max] ∩ 레일(4.7-3 2), F 성분 미선언 포트 = 창 정의 불능(`f_component_undeclared`, lo·hi None).
# 기대값은 모두 toy 연결의 손계산과 이 test 안의 독립 풀이(이분법)에서 만든다. 피검 함수(`dc_solve` 출력)로 기대값을 만들지 않는다.
# ===========================================================================
from .conftest import circuit_cs_pmos_load, r4_vdsat_at, r4_tol_vdsat  # noqa: E402


def _bisect(f, lo, hi, n=200):
    flo = f(lo)
    assert (flo > 0) != (f(hi) > 0), "근을 끼지 않은 구간"
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _window_of(snap):
    return dict(snap.column("node", "dc_window"))


# [IT-1 A-39 retired_tests] 폐기: test_it2b_k1_undeclared_input_ports_both_have_windows, test_it2b_k2_non_root_port_window_is_root_ends_moved_by_the_same_
# solution_sensitivity -- 사유 = 뿌리 아닌 포트 창 전제가 DEC-106(입력 점은 항목 하나, n 포트 항목 없음)과 충돌. 새 동작은 test_it1_t1h_* 가 본다.


# ---- 입력 DC 둘 선언 toy (P(b)): 차동쌍 -------------------------------------------------------------------------------------
# M1 nmos (o1, ina, t), M2 nmos (o2, inb, t), 꼬리 M5 nmos (t, vb, gnd), 부하 저항 R1 (vdd, o1)·R2 (vdd, o2). bulk = gnd. 입력 DC 0.9 V 선언(두 입력 포트 모두).
# o1 = o2 = 1.8 − I·R(= 1.0 V, 저항 강하라 입력에 무관), t = V(in) − VGS(M_writer, vds = o − t, vsb = t) (1변수), M5 가 t 를 받친다.
def _dp_doc():
    return topo("it2b_dp", [mos("M1", "nmos", "o1", "ina", "t", "gnd"), mos("M2", "nmos", "o2", "inb", "t", "gnd"),
                            mos("M5", "nmos", "t", "vb", "gnd")],
                {"ina": ("input", "differential_input_p"), "inb": ("input", "differential_input_n"), "o1": ("output", "y")},   # [IT-1 DEC-106]
                passives=[two("R1", "resistor", "vdd", "o1"), two("R2", "resistor", "vdd", "o2")], bias=["vb"])


DP_R = 8e4
DP_I = 1e-5
DP_VO = 1.8 - DP_I * DP_R                                      # 1.0 V (저항 강하 손계산)
DP_TD = r4_ln_idu("nmos", 0.5, 0.6, 0.4)                        # 쌍 소자 writer 의 ln IDu(두 소자 같은 좌표)
DP_T5 = r4_ln_idu("nmos", 0.6, 0.4, 0.0)


def _dp_theta(ctx, y=None):
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M5"): 1e-6, ("ln_idu", "M5"): DP_T5,
          ("resistance", "R1"): DP_R, ("resistance", "R2"): DP_R}
    if y is not None:                                                  # [IT-1] 입력 DC 미선언: 입력 점 뿌리의 y 성분
        th.update({(k, key): y for k, key in kschema(ctx).components if k == "y"})
    th.update({("ln_idu", m): DP_TD for t, m in kschema(ctx).components if t == "ln_idu" and m != "M5"})
    th.update(free_currents(ctx, {"M1": DP_I, "M2": DP_I, "M5": 2 * DP_I, "R1": DP_I, "R2": DP_I}))
    assert set(th) == set(kschema(ctx).components)
    return th


def _dp_t(vin):
    """독립 풀이: t = vin − VGS(TD; vds = DP_VO − t, vsb = t)."""
    return _bisect(lambda t: vin - r4_vgs_of("nmos", DP_TD, DP_VO - t, t) - t, 1e-9, vin - 1e-9)


# ---------------------------------------------------------------------------------------------------------------------------
# P(a) 감도 음수 포트 toy (design 41 4.7-3 2·4.7-7 P (a)) -- 이름 없는 toy + VDS 의존이 가파른 LUT 픽스처(이 파일 안에서 만든다)
#
# 연결: 입력 포트 x(뿌리) -MA follower-> t, 저항 R (t -> d), t -MB follower-> u, MT (d = d, g = p, s = u) triode 선언, 둘째 입력 포트 p,
# 풀다운 MS (u, vs, gnd). 쓰기: t = x − VGS_A, u = t − VGS_B, d = t − I·R, p = u + VGS_T(vds = d − u) (p 는 vgs_gate, known u).
# 손 유도(전류 고정 writer 식): F = ∂VGS/∂VDS = −h′(VDS)/G′ (전류 고정, 이득의 역수 꼴), η = ∂VGS/∂VSB = KS/G′.
#   t -> u 엣지: s_u·(1 + |F_B| + η_B) = s_t, d: s_d = s_t (저항), u -> p 엣지(vgs_gate): s_p = s_u·(1 + |F_T| + η_T) − |F_T|·s_d.
#   s_p < 0 조건: |F_T| > (1 + η_T)/(η_B + |F_B|). r4 LUT 는 |F| ≤ 0.018 이라 이 조건이 불가능 -> VDS < 0.2 V 에서 ln ID 기울기가 가파른(deep triode) LUT 를 둔다.
# 픽스처 LUT: ln ID = ln I0 + B·VGS − CN·VGS²/2 + h(VDS) − KS·VS (+ VDSAT 열 = r4 식), h(VDS) = S1·min(VDS, D1) + S2·max(VDS − D1, 0).
# 격자 VDS 0.0125 V 간격(노드에서 기울기 GDS = ID·h′ 정확 -> 구간 선형 ln ID 가 정확). VS 항을 선형으로 두어 η 를 상수로 한다(곡률은 VGS 축 CN 이 준다).
# ---------------------------------------------------------------------------------------------------------------------------
import json as _json  # noqa: E402

import numpy as _np  # noqa: E402

from gmid_engine.lut import load_lut_set as _load_lut_set  # noqa: E402
from toy_bins import write_toy_bins as _write_toy_bins  # noqa: E402

from .conftest import (A as _A, B as _B, DEVICE_OF as _DEVICE_OF, I0 as _I0, R4_VDSAT as _R4_VDSAT, R4_VGS as _R4_VGS,  # noqa: E402
                       R4_VS as _R4_VS, SUFFIX as _SUFFIX, TOY_SPEC as _TOY_SPEC, W_M as _W_M, _sha as _file_sha)

NEG_CN, NEG_KS, NEG_S1, NEG_S2, NEG_D1 = 2.0, 2.0, 250.0, 0.1, 0.2
NEG_VDS = tuple(round(0.0125 * i, 10) for i in range(161))                 # 0 .. 2.0 V
NEG_I = 1e-5
NEG_R = 17935.0                       # t -> d 저항(Ω): VDS(MT) ≈ 0.1 V (뿌리 창 중앙에서 손으로 맞춘 입력 값, 기대값 아님)


NEG_QD = 20.0                       # 곡률 계수에 (1 + QD·VDS) 를 곱해 tol_V 셀이 VDS 에 따라 달라지게 한다(해마다 tolerance 가 다른 toy -- L12 (a) tol_v 판정)
NEG_QV, NEG_VS_KINK = 0.005, 1.6   # VS > 1.6 V 에서만 ln ID 에 −QV·(VS − 1.6)² (동작 범위 밖): LUT 허용오차 tol_V 가 극소(1e-17)가 되어
                                    # A6 되풀이가 수렴 판정을 못 하는 일을 막는 곡률(구간 선형 ln ID 의 LOO 오차가 tol_V 를 정의한다)


def _neg_h(d):
    return NEG_S1 * min(d, NEG_D1) + NEG_S2 * max(d - NEG_D1, 0.0)


def _neg_slope(d):
    return NEG_S1 if d < NEG_D1 else NEG_S2


def _neg_ln_idu(vgs, vds, vsb):
    return math.log(_I0["nmos"]) + _B * vgs - 0.5 * NEG_CN * vgs * vgs + _neg_h(vds) - NEG_KS * vsb


def _neg_vgs_of(ln_idu, vds, vsb):
    r = ln_idu - math.log(_I0["nmos"]) - _neg_h(vds) + NEG_KS * vsb
    return (_B - math.sqrt(_B * _B - 2.0 * NEG_CN * r)) / NEG_CN


def _write_neg_lut(root):
    root.mkdir(parents=True, exist_ok=True)
    g_l, g_g, g_d, g_s = (_np.asarray(g, dtype=float) for g in (R4_L, _R4_VGS, NEG_VDS, _R4_VS))
    lg, g, s = g_l[:, None, None, None], g_g[None, :, None, None], g_s[None, None, None, :]
    h_d = _np.vectorize(_neg_h)(g_d)[None, None, :, None]
    s_d = _np.vectorize(_neg_slope)(g_d)[None, None, :, None]
    tb = _write_toy_bins(root, ("nmos", "pmos"), tuple(R4_L), (_W_M,), grid_m=1e-8)
    entries = []
    for kind in ("nmos", "pmos"):
        idc = (_W_M / lg) * _I0[kind] * _np.exp(_B * g - 0.5 * NEG_CN * g * g + h_d - NEG_KS * s
                                                       - NEG_QV * (1.0 + NEG_QD * g_d[None, None, :, None])
                                                       * _np.maximum(s - NEG_VS_KINK, 0.0) ** 2)
        c0, c1, c2, cs, cl = _R4_VDSAT[kind]
        il = _np.arange(len(g_l), dtype=float)[:, None, None, None]
        arr = {"W": _np.float64(_W_M), "L": g_l, "VGS": g_g, "VDS": g_d, "VS": g_s, "ID": idc, "GM": idc * (_B - NEG_CN * g),
               "GDS": idc * s_d, "VTH": _np.full(idc.shape, 0.4), "meta_json": _np.str_(_json.dumps(tb.meta(kind))),
               "corner": _np.str_("tt"), "temp_c": _np.float64(27.0),
               "VDSAT": (c0 + c1 * g + c2 * g * g + cs * s + cl * il) + _np.zeros(idc.shape)}
        path = root / ("neg_%s.npz" % kind)
        _np.savez(path, **arr)
        entries.append({"device": _DEVICE_OF[kind], "file": path.name, "sha256": _file_sha(path)})
    (root / "manifest.json").write_text(_json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    shape = (len(g_l), len(g_g), len(g_d), len(g_s))
    cap = {"L": g_l, "VGS": g_g, "VDS": g_d, "VS": g_s, "w_ref_m": _np.float64(_W_M), "corner": _np.str_("tt"),
           "temp_c": _np.float64(27.0), "meta_json": _np.str_(_json.dumps(tb.cap_meta()))}
    for kind in ("nmos", "pmos"):
        cap["CGG" + _SUFFIX[kind]] = _np.full(shape, 1e-15)
        cap["CGD" + _SUFFIX[kind]] = _np.full(shape, 2e-16)
        # [JC-1] 접합 항 입력 열(손 식: CGS = CGG − CGD = 8e-16, CSS − CGS = 5e-16, CDD − CGD = 3e-16 -- 모든 칸 같은 값)
        cap["CGS" + _SUFFIX[kind]] = _np.full(shape, 8e-16)
        cap["CSS" + _SUFFIX[kind]] = _np.full(shape, 1.3e-15)
        cap["CDD" + _SUFFIX[kind]] = _np.full(shape, 5e-16)
    _np.savez(root / "cap.npz", **cap)
    return _load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), _TOY_SPEC, bin_rule=tb.bin_rule)


def _neg_doc():
    net = [mos("MA", "nmos", "vdd", "x", "t", "gnd"), mos("MB", "nmos", "vdd", "t", "u", "gnd"),
           mos("MT", "nmos", "d", "p", "u", "gnd"), mos("MS", "nmos", "u", "vs", "gnd")]
    return topo("it2b_neg", net, {"x": ("input", "single_ended_input"), "u": ("output", "y")},
                passives=[two("R", "resistor", "t", "d")], bias=["vs", "p"])           # [IT-1 A-39] p = MT gate 전용 바이어스(입력 포트 아님)


# θ 좌표: 소자 MA·MB 는 VGS 0.25 V, MT 는 VGS 0.8 V(VDS 0.1 V), MS 는 VGS 0.45 V 가 나오는 ln IDu(입력 값). 근사 동작점 t0 = 0.65, u0 = 0.4.
NEG_LN = {"MA": _neg_ln_idu(0.25, 1.8 - 0.65, 0.65), "MB": _neg_ln_idu(0.25, 1.8 - 0.4, 0.4),
          "MT": _neg_ln_idu(0.8, 0.1, 0.4), "MS": _neg_ln_idu(0.45, 0.4, 0.0)}


def _neg_solve(x):
    """독립 풀이(이분법): t = x − VGS_A(vds = 1.8 − t, vsb = t), u = t − VGS_B(vds = 1.8 − u, vsb = u), d = t − I·R, p = u + VGS_T(vds = d − u, vsb = u)."""
    t = _bisect(lambda v: x - _neg_vgs_of(NEG_LN["MA"], 1.8 - v, v) - v, 1e-6, x - 1e-6)
    u = _bisect(lambda v: t - _neg_vgs_of(NEG_LN["MB"], 1.8 - v, v) - v, 1e-6, t - 1e-6)
    d = t - NEG_I * NEG_R
    return t, u, d, u + _neg_vgs_of(NEG_LN["MT"], d - u, u)


def _columns_with_declared(ctx, theta):
    """`dc_solve` 를 커널과 같은 호출로 부른다: 선언 영역(triode)은 extras 가 아니라 ctx.base 의 device.region_decl 필드로 온다(A-88)."""
    from gmid_engine.sizing import dc_solve, dc_currents, dc_lengths
    run = dict(donors=ctx.donors, counters=ctx.counters)
    th = dict(theta)
    snap = dc_currents(ctx.base, tuple(sorted((k, v) for (t, k), v in th.items() if t == "current")), **run)
    snap = dc_lengths(snap, tuple(sorted((k, v) for (t, k), v in th.items() if t == "L")), **run)
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    # [EO-1 범위 4, A-88] 다섯째 extras 없음 -- triode 선언은 S0 필드 device.region_decl 로 ctx.base 에 실려 있다(dc_solve 가 READS 로 읽음).
    return dc_solve(snap, items, kfixed(ctx), kres(ctx), ctx.lut, wf=hand_wf(ctx), **run)


# [IT-1 A-39 retired_tests] 폐기: test_it2b_pa_negative_sensitivity_port_window_is_min_max_of_the_two_end_voltages -- 사유 = 뿌리 아닌 포트 창 전제가 DEC-106과 충돌.

# ---------------------------------------------------------------------------------------------------------------------------
# L12 (a) 커널 되풀이 k_max 소진 -> 뿌리 `unsettled` (design 41 4.7-7 L12 (a), A6 c) -- 주입 지점 `gmid_engine.sizing.block_columns.k_max` 하나만
# (monkeypatch 허용 지점, 상한 1). toy = 위 P(a) toy(입력 포트 x = 뿌리).
# ---------------------------------------------------------------------------------------------------------------------------
def _neg_ctx(tmp_path):
    acc = new_access(_write_neg_lut(tmp_path / "neg_lut"))
    (tmp_path / "ctx").mkdir()
    return acc, build_ctx(tmp_path / "ctx", _neg_doc(), acc, regions=(RegionDecl("MT", "triode"),))[2]


def _neg_theta(ctx, y):
    th = {("L", m): 1e-6 for m in ("MA", "MB", "MS", "MT")}
    th.update({("ln_idu", m): NEG_LN[m] for m in ("MA", "MB", "MS", "MT")})
    th.update({("resistance", "R"): NEG_R, ("y", "x"): y})
    th.update(free_currents(ctx, {"MA": NEG_I, "MB": NEG_I, "MT": NEG_I, "MS": 2 * NEG_I, "R": NEG_I}))
    return th


# ---------------------------------------------------------------------------------------------------------------------------
# D (S4-나) -- triode 행 영 교차 = 창 끝, region_rows 종류 집합·EO-1 무관 부재 단언 (정적 AST, docstring·주석 제외), 어휘 부재 (d)
# `_helpers_dc_solve` 모듈은 IT-2d 에서 생긴다(IT-2b 에는 없다) -- `region_rows` 는 block_columns 안 비공개 이름이라 공개 진입점 `dc_solve` 로 본다.
# ---------------------------------------------------------------------------------------------------------------------------
import ast as _ast  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

import gmid_engine as _gmid_engine  # noqa: E402

from gmid_engine.lut import tol_v_table  # noqa: E402

ENGINE = _Path(_gmid_engine.__file__).resolve().parent
TRI_VIN, TRI_VGS1, TRI_VGS3 = 0.8, 0.8, 0.6      # 입력 DC 선언 값, M1(triode 선언)·M3(풀다운) 의 VGS -- 손으로 정한 입력


def _tri_doc():
    """M1 nmos (d = out, g = vb, s = in, b = gnd) triode 선언 소자(source 가 입력 포트 in), M2 pmos 부하, M3 nmos (in, vc, gnd) 가 in 의 전류 경로를 닫는다.
    V(out) = lo + y·(hi − lo), lo = V(in)(M1 의 소스 쪽 이웃), hi = V(vdd)."""
    return topo("it2b_triode", [mos("M1", "nmos", "out", "vb", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"),
                                mos("M3", "nmos", "in", "vc", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")}, bias=["vb", "pb", "vc"])


def _tri_theta(ctx, y, vsg2):
    out = TRI_VIN + y * (1.8 - TRI_VIN)
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): r4_ln_idu("nmos", TRI_VGS1, out - TRI_VIN, TRI_VIN),
          ("ln_idu", "M2"): r4_ln_idu("pmos", vsg2, 1.8 - out, 0.0),
          ("ln_idu", "M3"): r4_ln_idu("nmos", TRI_VGS3, TRI_VIN, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def _docstring_ids(tree):
    ids = set()
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, _ast.Expr) and isinstance(first.value, _ast.Constant) and isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def _identifiers_and_strings(tree):
    """식별자(이름·속성·정의·인자·키워드·import 이름)와 문자열 상수(docstring 제외)만 -- 주석은 AST 에 없다."""
    skip = _docstring_ids(tree)
    names, strings = set(), set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Name):
            names.add(node.id)
        elif isinstance(node, _ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, _ast.arg):
            names.add(node.arg)
        elif isinstance(node, _ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, _ast.alias):
            names.update(part for part in ((node.asname or node.name).split(".")) if part)
        elif isinstance(node, _ast.ImportFrom) and node.module:
            names.update(node.module.split("."))
        elif isinstance(node, _ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            strings.add(node.value)
    return names, strings


def test_it2b_d_no_operating_point_mismatch_vocabulary_in_engine_sources():
    """oracle 대조: (독립) D (d), 계획 v6.33 (9)(d), 사용자 결정 O-98·O-101. (S4-나) 에서 동작점 불일치 묶음(상태 `op_mismatch`·`Window.status_detail`·metric
    code)은 EO-1 card 몫이다 -- 죽은 코드를 두지 않는다. 비test 엔진 소스(tests 폴더 제외 모든 .py)를 AST 로 읽어 식별자와 문자열 상수(docstring·주석 제외)에
    `op_mismatch`·`status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH` 가 0 이다."""
    words = ("op_mismatch", "status_detail", "input_window_operating_point_mismatch", "INPUT_STATUS_OP_MISMATCH",
             "CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH")
    hits = []
    for path in ENGINE.rglob("*.py"):
        if "tests" in path.relative_to(ENGINE).parts:
            continue
        names, strings = _identifiers_and_strings(_ast.parse(path.read_text(encoding="utf-8")))
        for word in words:
            if word in names or any(word in s for s in strings):
                hits.append((str(path.relative_to(ENGINE)), word))
    assert hits == [], hits


# ---------------------------------------------------------------------------------------------------------------------------
# L12 (a) tol 미정 -> 뿌리 `unsettled` (design 41 4.7-3 1 A6 b: '`tolerance` 가 미정이면 창을 한 번만 적용하고 되풀이 수렴 판정 없이 푼다')
# 도달 조건: 비순환 쓰기 계획(순환 SCC·자기참조 없음), 해의 모든 MOS 에서 tol_VDsat 정의(열 출처 = 기준 LUT), id_equivalent tol_V 셀은 전부 미정.
# 픽스처: 슬라이스에 VDSAT 열 없음 + 기준 LUT(cap)에 VDSAT 열, 슬라이스 VDS = 0 열 끔, 격자 VGS 2점·VDS 3점(0 포함)·VS 2점, L 앵커만.
# 회로(이름 없는 공통 게이트 꼴): M1 nmos (out, vb, in, gnd), RL (vdd, out), IS (in, gnd 전류 싱크); in = 입력 W4 뿌리, out = resistor_drop.
# ---------------------------------------------------------------------------------------------------------------------------
A6B_GRIDS = (R4_L, (0.2, 1.2), (0.0, 0.3, 1.8), (0.0, 1.8))        # 축소 격자 표현용 test 입력(엔진 상수 아님)


def _a6b_doc():
    return topo("it2b_a6b", [mos("M1", "nmos", "out", "vb", "in", "gnd")], {"in": ("input", "x"), "out": ("output", "y")},
                passives=[two("RL", "resistor", "vdd", "out")], sources=[two("IS", "current_source", "in", "gnd")], bias=["vb"])


def _a6b_access(tmp_path, slice_vdsat, cap_vdsat):
    from .conftest import write_r4_lut
    return new_access(write_r4_lut(tmp_path / "lut", vdsat=slice_vdsat, off_cols={"nmos": 1, "pmos": 1}, grids=A6B_GRIDS,
                                   cap_vdsat=cap_vdsat))


def _a6b_window(tmp_path, slice_vdsat, cap_vdsat, check_structure=False):
    acc = _a6b_access(tmp_path, slice_vdsat, cap_vdsat)
    (tmp_path / "ctx").mkdir()
    ctx = build_ctx(tmp_path / "ctx", _a6b_doc(), acc)[2]
    if check_structure:                                           # 전제: 순환 SCC 0·자기참조 0
        assert not any(e.cyclic for e in ctx.base.value("graph", DC_KEY, "dc_scc_order"))
        assert not any(v for _, v in ctx.base.column("device", "dc_self_referential"))
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): r4_ln_idu("nmos", 0.4, 0.6, 0.6), ("resistance", "RL"): 6e4}
    th.update(free_currents(ctx, {"M1": 1e-5, "RL": 1e-5, "IS": 1e-5}))
    th.update({(k, key): 0.5 for k, key in kschema(ctx).components if k == "y"})
    assert set(th) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    return acc, snap


# ===========================================================================
# [IT-1 T-1h] 입력 점의 열 -- `dc_solve`: 입력 DC 미선언 차동 toy 의 두 포트 node.dc_v 가 같고 node.dc_window 키에 n 포트가 없다
# (card 20261104-it1-input-point, 설계 41 v1.16.3 §4.7-2). oracle: (손) 두 포트는 한 점이라 같은 전압; 뿌리 전압 = 창 하한 + y·(창 폭)(회로 C 손 test
# `test_circuit_c_hand` 의 out = 0 + y·(1.8 − 0) 와 같은 규칙). `node.dc_window` 수치는 card WB-1 몫이라 단언하지 않는다(키와 포함 관계만).
# ===========================================================================

def test_it1_t1h_input_point_ports_share_voltage_and_window_key(tmp_path, r4_access):
    """T-1h (손): `_dp_doc`(입력 DC 미선언, p ina · n inb) -- 두 포트가 한 입력 점이라 node.dc_v 가 같고, 뿌리 전압은 창 [lo, hi] 와 y = 0.5 로
    lo + 0.5(hi - lo). 독립 풀이로 구한 꼬리 전압 t 는 입력이 그 전압일 때의 해(`_dp_t`). node.dc_window 키에 p 포트 ina 가 있고 n 포트 inb 는 없다."""
    ctx = build_ctx(tmp_path, _dp_doc(), r4_access)[2]
    nw = dict(ctx.base.column("node", "dc_writer"))
    assert nw["ina"].relation == nw["inb"].relation == "input_point"                          # 전제
    snap = run_blocks(ctx, _dp_theta(ctx, y=0.5), upto="columns")
    V = node_voltages(snap)
    win = _window_of(snap)
    assert "ina" in win and "inb" not in win
    assert abs(V["ina"] - V["inb"]) <= 1e-12
    assert abs(V["ina"] - (win["ina"].lo + 0.5 * (win["ina"].hi - win["ina"].lo))) <= 1e-9
    from gmid_engine.lut import tol_v_table
    ops = dict(snap.column("device", "dc_op"))
    writer = next(m for m, c in ctx.base.column("device", "dc_coord") if m in ("M1", "M2") and c.role == "writer")
    tol = tol_v_table(r4_access.memo, ops[writer].kind, ops[writer].w_key).at(ops[writer].L, ops[writer].vds, "id_equivalent")
    assert tol is not None and abs(V["t"] - _dp_t(V["ina"])) <= tol                           # 노드 풀이 수렴 정의(봉인 2 와 같은 tol_V), 숫자 상수 아님


def _it1_ftouch_doc():
    """입력쌍 source 가 레일: M1(o1, inp, gnd)·M2(o2, inn, gnd) (p inp, n inn), 부하 M3(o1, pb3, vdd)·M4(o2, pb4, vdd). G_vgs: P-F 둘 -> 입력 점이 F 에 닿는다."""
    return topo("it1_ftouch_cols",
                [mos("M1", "nmos", "o1", "inp", "gnd"), mos("M2", "nmos", "o2", "inn", "gnd"),
                 mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                 "o1": ("output", "b"), "o2": ("output", "b")}, bias=["pb3", "pb4"])


def test_it1_t1h_input_point_touching_f_ports_share_voltage(tmp_path, toy_access):
    """T-1h (손): 입력쌍 source 가 레일인 toy -- y 성분 없음, 두 포트 전압이 같고 (구성) 트리 소자의 VGS 와 같다. 출력 o1·o2 는 y = 0.5 -> 창 [0, 1.8] 의
    0.9 V, 트리 입력 소자의 좌표를 (VGS 0.6, VDS 0.9, VSB 0) 으로 잡았으므로 V(inp) = V(inn) = 0 + 0.6."""
    ctx = build_ctx(tmp_path, _it1_ftouch_doc(), toy_access)[2]
    assert not any(k == "y" and key in ("inp", "inn") for k, key in kschema(ctx).components)           # 전제: 입력 점 y 성분 0
    ln_keys = {key for k, key in kschema(ctx).components if k == "ln_idu"}
    assert len(ln_keys & {"M1", "M2"}) == 1                                                            # 전제: 입력쌍은 평행 하나 -> ln_idu 성분 하나
    th = {}
    for k, key in kschema(ctx).components:
        if k == "L":
            th[(k, key)] = 1e-6
        elif k == "y":
            th[(k, key)] = 0.5
        elif k == "current":
            th[(k, key)] = 1e-5
        elif k == "ln_idu":
            th[(k, key)] = (Oracle.ln_idu("nmos", 0.6, 0.9, 0.0) if key in ("M1", "M2") else Oracle.ln_idu("pmos", 0.7, 0.9, 0.0))
        else:
            raise AssertionError((k, key))
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    win = _window_of(snap)
    assert all(win[x].lo is None and win[x].hi is None for x in ("inp", "inn") if x in win)   # F 에 닿는 입력 점은 창 값이 없다(항목 삭제는 IT-2c)
    assert abs(V["o1"] - 0.9) <= 1e-9 and abs(V["o2"] - 0.9) <= 1e-9
    assert abs(V["inp"] - V["inn"]) <= 1e-12
    assert abs(V["inp"] - 0.6) <= 1e-9


# ---------------------------------------------------------------------------
# [LM-1e §5 J-b] 셀 결합: Gauss-Seidel 반복 중 SCC 소자 하나의 tol 이 결합 셀 일부 None 이면 -- 정의된 셀의 min 으로 값을 내지 않고 --
# 수렴 전 SealViolationError(tol_v_undefined) 그대로(Newton 인계 없음). 위 test_tol_undefined_before_convergence_propagates 는 모든 셀이 None 인 경우다.
# 입력: toy R 의 꺼진 열을 **nmos** 에 둔다(nmos 셀 0 = None; pmos 는 모두 정의) + `_scc_s_doc` + 손 θ (y1, y2) = (0.2, 0.7): 선형 SCC 닫힌 해
# vout = 1.8·y2/(1 − y1(1 − y2)) = 1.34 V, vin = y1·vout = 0.268 V(M1 의 수렴 VDS), M2 의 VDS = vout − vin = 1.072 V. 수렴 상태는 모든 소자가
# 정의역(VDS ≥ 0.25) 안이고, Gauss-Seidel 첫 걸음에서 M1 의 VDS 가 0.24 V -> 첫 칸 [0, 0.25) 안(셀 0 None 포함 결합)을 지난다. M2·M3 의 셀은 정의.
# (꺼진 열을 pmos 에 두면 수렴 상태의 |VDS| 가 0.25 아래여야 첫 칸에 닿는데, 그 점은 정의역 밖이라 `lut_query_failed`(lut_curve_undefined)로 먼저 거부된다 --
# 격자 (y1, y2) 훑기로 확인.) 확인은 관찰 지점 `block_dc.tol_v_table` 의 통과 spy(원 함수를 그대로 부르고, 돌려받은 표의 `at` 인자·결과를 기록만 한다 -- 값 주입 0).
# ---------------------------------------------------------------------------

class _AtSpy:
    def __init__(self, table, log):
        self._t = table
        self._log = log

    def __getattr__(self, name):
        return getattr(self._t, name)

    def at(self, L, vds, *a, **k):
        r = self._t.at(L, vds, *a, **k)
        self._log.append((self._t.kind, vds, r))
        return r


def _jb_inputs(tmp_path, monkeypatch):
    import sys
    from .conftest import ja_theta, r_off_access
    bd = sys.modules["gmid_engine.sizing.block_dc"]
    orig = bd.tol_v_table
    log = []
    monkeypatch.setattr(bd, "tol_v_table", lambda *a, **k: _AtSpy(orig(*a, **k), log))
    (tmp_path / "ctx").mkdir()
    ctx = build_ctx(tmp_path / "ctx", _scc_s_doc(), r_off_access(tmp_path / "lut", "nmos"))[2]
    th, vin, vout = ja_theta(ctx, 0.2, 0.7)
    assert vin >= 0.25 and vout - vin >= 0.25 and 1.8 - vout >= 0.25   # 손 계산 전제: 수렴 상태의 모든 소자 |VDS| 가 정의역(≥ 0.25 V) 안
    return ctx, th, log


def test_cell_combine_j_b_premise_spy_sees_first_cell_lookup(tmp_path, monkeypatch):
    """전제(결합 규칙과 무관): 수렴 tol 조회 중 nmos(M1) 가 첫 VDS 칸 [0, 0.25) 안에서 불렸고, 같은 SCC 의 pmos(M3) 조회는 값(정의)을 돌려받았다."""
    ctx, th, log = _jb_inputs(tmp_path, monkeypatch)
    try:
        run_blocks(ctx, th, upto="columns")
    except SealViolationError:
        pass                                                           # 새 규칙에서는 여기서 거부된다(아래 test)
    assert any(k == "nmos" and 0.0 <= v < 0.25 for k, v, _ in log), log
    assert any(k == "pmos" and r is not None for k, _, r in log), log


def test_cell_combine_j_b_partly_undefined_tol_propagates_before_convergence(tmp_path, monkeypatch):
    ctx, th, log = _jb_inputs(tmp_path, monkeypatch)
    (entry,) = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert set(entry.nodes) == {"vin", "vout"}
    for first, call in ((True, lambda: run_blocks(ctx, th, upto="columns")), (False, lambda: size_and_seal(ctx, th, hand_wf(ctx)))):     # [FS-1 서명 맞춤] wf 인자
        log.clear()
        with pytest.raises(SealViolationError) as ei:
            call()
        e = ei.value
        assert dict(e.record.detail)["reason"] == REASON_TOL_UNDEFINED == "tol_v_undefined"
        # [LM-1e A-161 (2)] devices = tol 이 None 인 원인 소자의 정렬 tuple(호출 인자 소자 전체가 아님). 원인 = spy 기록에서 결과 None 을 낸
        # 호출의 kind 와 VDS(< 0.25, 첫 칸): 이 손 회로(_scc_s_doc)에서 그 kind(nmos) 소자 중 VDS 가 그 노드 전압 하나인(소스 = gnd) 것은 M1 뿐이다
        # (M2 소스 = vin 이라 VDS = vout − vin ≈ 1.07 V 로 정의 칸; M3 는 pmos). oracle (a)+(d): spy 기록 + 손 연결.
        # [A-162] 같은 ctx 의 두 번째 호출은 첫 실패 기록을 실패 재연(graph reuse)으로 다시 던지므로 조회 0건이 맞다 -> spy 단언은 첫 호출에만,
        # 두 번째 호출은 거부 기록(reason·devices)이 같음만 본다.
        none_calls = [(k, v) for k, v, r in log if r is None]
        if first:
            assert none_calls and all(k == "nmos" and v < 0.25 for k, v in none_calls), log
        else:
            assert log == [], log
        assert e.record.devices == ("M1",)
        assert set(e.record.devices) < set(entry.devices) and e.record.margin is None
        assert not isinstance(e.__cause__, NonconvergentError)          # Newton 으로 넘기지 않았다
