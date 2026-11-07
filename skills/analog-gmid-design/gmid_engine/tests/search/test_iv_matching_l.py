"""search/iv_matching_l.py -- matching L 하한(절대 offset, 설계 41 §6.4-2)과 offset 가드 부하 gm/ID 상한(§6.4-2a) (사용자 결정 2026-10-08 Q3; D-SId·D-SIg).

oracle (d) 설계 41 §6.4-2: '절대 offset 제약(offset_in_sigma_mv <= 값)이 있는 회로에서만 활성', 하한은 '입력 셀 소자 면적 하한 ... L ≥ √(A_min·IDu/I)';
구조 가드(offset_excess)만 있으면 L 하한이 아니라 부하 gm/ID 상한(§6.4-2a).
oracle (a):
- 구조: 입력 셀 소자 = gate 가 입력 포트에 닿는 MOS(two_stage_ota: M1·M2 -- topology 에서 읽는다).
- 단조: σ_target 이 작을수록 A_min = A_eff²/σ_share² 가 커져 L 하한은 같거나 커진다(A_eff 는 L·gm/ID 의 함수, 같은 1회차 전류·gm/ID).
실경로 = 실 LUT v2 + mismatch r1 감도 파일(데이터 위치 선언으로 명시 로드, u13_real) + library two_stage_ota(사용자 선언 offset_excess 가드 포함),
추가 제약 offset_in_sigma_mv 3.3 mV(파일럿 값, 설계 41 §6.4-2)·1.0 mV(단조 확인용 test 입력).
toy LUT(mismatch 데이터 없음): 설계 41 §6.4-2b '감도 데이터가 없는데 offset 제약이 선언되면 `SchemaRejectedError(mismatch_lut_missing)`'
(lut CONTRACT 9.5 `require_lut_data` -- 호출부는 search 시작) -> 절대 offset 제약은 탐색 문맥을 만들 때 거부된다. 그 거부를 거치지 않은 출발 입력 묶음
(u13_hand `start_ctx_with`)에서는 `matching_bounds` 가 계산하지 않고 그 사유가 남는다(CONTRACT U13 비활성 사유).
CONTRACT U13 'mismatch/잡음 질의의 폭은 W_min 이상으로 맞춘다(모델 bin 밖 폭 방지)' + (a) 설계 41 §6.4-2 σ_VGS ∝ 1/√(W·L): W < W_min 인 전류에서는
폭이 W_min 으로 고정돼 같은 σ, 폭이 커지면 σ 가 줄어든다(bin 이 바뀌면 slope 비가 바뀌므로 비례 상수는 확인하지 않는다).
"""
import ast
import math

import pytest

from gmid_engine.core.failure_errors import SchemaRejectedError
from gmid_engine.search.iv_matching_l import matching_bounds

from .u13_hand import all_inactive, bound_values, cs_chain, rows_by_name, start_ctx_with, start_view_of, toy_case
from .u13_real import input_gate_devices, real_case, real_env

SRC_L = "matching_l_6.4_2"
SRC_GUARD = "offset_guard_6.4_2a"
OFFSET = (("offset_in_sigma_mv", "<=", 3.3),)
OFFSET_TIGHT = (("offset_in_sigma_mv", "<=", 1.0),)


def _reasons(st, src):
    return {why for s, why in all_inactive(st) if s == src}


def test_no_absolute_offset_constraint_no_l_lower_bound():
    st = real_case("two_stage_ota").start
    assert not any(bound_values(r, SRC_L) for r in st.rows)
    assert _reasons(st, SRC_L) == {"constraint_not_declared"}


def test_absolute_offset_activates_l_lower_bound_on_input_cell_only():
    # (24cfecd 에서 red: σ 질의 폭이 W_min 아래라 `lut_mismatch_no_block` -- 75626c8 의 폭 보정으로 해소)
    case = real_case("two_stage_ota", OFFSET)
    st = case.start
    inputs = input_gate_devices(case.topology)
    assert inputs == {"M1", "M2"}
    assert not _reasons(st, SRC_L), _reasons(st, SRC_L)
    have = {r.device for r in st.rows if bound_values(r, SRC_L, "L", "lo")}
    assert have == inputs
    for r in st.rows:
        if r.device in inputs:
            assert r.l_lo >= max(bound_values(r, SRC_L, "L", "lo")) * (1 - 1e-12)


def test_tighter_offset_target_gives_larger_l_lower_bound():
    a = {r.device: bound_values(r, SRC_L, "L", "lo") for r in real_case("two_stage_ota", OFFSET).start.rows}
    b = {r.device: bound_values(r, SRC_L, "L", "lo") for r in real_case("two_stage_ota", OFFSET_TIGHT).start.rows}
    for dev in ("M1", "M2"):
        assert a[dev] and b[dev], (a, b)
        assert max(b[dev]) >= max(a[dev])


def test_offset_guard_gives_load_upper_bound_not_l_bound():
    # library spec 은 offset_excess 가드를 선언한다 -> 부하 gm/ID 상한(§6.4-2a), 입력 소자에는 L 하한 없음.
    # (24cfecd 에서 red: 같은 `lut_mismatch_no_block` -- 75626c8 에서 해소)
    case = real_case("two_stage_ota")
    st = case.start
    assert not _reasons(st, SRC_GUARD), _reasons(st, SRC_GUARD)
    guarded = {r.device for r in st.rows if bound_values(r, SRC_GUARD, "gm_id", "hi")}
    assert guarded and not (guarded & input_gate_devices(case.topology))


TOY_ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))
TOY_TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))


def test_toy_absolute_offset_without_mismatch_data_is_rejected():
    # 설계 41 §6.4-2b·lut CONTRACT 9.5: mismatch 감도 데이터가 없는 LUT 에 절대 offset 제약 -> SchemaRejectedError(mismatch_lut_missing)
    # [기대 red, 75626c8] search 시작 검사(search CONTRACT U8 절)는 잡음만 부른다 -- offset 제약은 거부되지 않고 출발 구간까지 간다.
    with pytest.raises(SchemaRejectedError) as ei:
        toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_TARGETS + OFFSET, fresh=True)
    assert ast.literal_eval(ei.value.args[0])["detail"]["reason"] == "mismatch_lut_missing"


def test_toy_without_mismatch_data_reports_reason_at_iv_matching():
    ctx, cur, lengths, lo = start_ctx_with(cs_chain(2), TOY_ELS, TOY_TARGETS, OFFSET)
    mb = matching_bounds(ctx, cur, lengths, lo)
    assert not [b for bs in mb.bounds.values() for b in bs if b.source == SRC_L]
    why = {w for s, w in mb.inactive if s == SRC_L}
    # 사유 이름은 입력이 없는 쪽(LUT 감도 열)을 가리킨다 -- 제약 미선언이 아니다
    assert why and "constraint_not_declared" not in why, why


@pytest.mark.parametrize("dev", ["M1", "M3"])
def test_sigma_query_width_is_at_least_w_min(dev):
    # CONTRACT U13 'mismatch 질의의 폭은 W_min 이상' -- 내부 helper `_sigma_vgs(ctx, name, g, L, current)` 를 직접 부른다.
    from gmid_engine.search.iv_matching_l import _sigma_vgs
    case = real_case("two_stage_ota", OFFSET)
    ctx = start_view_of(case, pdk=real_env().pdk)
    r = rows_by_name(case.start)[dev]
    g, L = r.gm_id_chosen, r.l_chosen
    idu = math.exp(r.ln_idu)                          # W = I·L/IDu (IDu 정의)
    w_min = float(ctx.w_min_m)
    tiny = (1e-14, 1e-13, 1e-12)
    for i in tiny:
        assert i * L / idu < w_min * 1e-2              # 입력 확인: W ≪ W_min (W_min 고정이 없으면 모델 bin 밖 폭)
    s = [_sigma_vgs(ctx, dev, g, L, i) for i in tiny]
    assert s[0] == pytest.approx(s[1], rel=1e-12) and s[1] == pytest.approx(s[2], rel=1e-12)
    wider = _sigma_vgs(ctx, dev, g, L, w_min * 4 * idu / L)    # W ≈ 4·W_min (같은 소자 kind 의 모델 bin 안 폭)
    assert wider < s[0]


# =====================================================================================================================
# [FS-1 M-1·M-2] 출발 4단계 matching L 하한 = LUT 선언 기준 폭 슬라이스의 slope bin, 6단계 가드 = 그 소자 칸 키 × 격자 (interface card 20261107-fs1 §3.4).
# oracle: (b) 엔진 밖 자료로 만든 손 값 -- LUT mismatch npz 원 열 + PDK 모델 카드·mismatch slope 원본 손 식 (`fs1_hand_sigma.py`; 엔진 함수 0),
# 손 식 입력 = 관찰 지점 `iv_matching_l.mismatch_sigma_vgs` 통과 spy 가 잡은 그 호출 인자. 앵커 고르기·전제 P1~P4: interface M-1 절차 5·6.
# 전제가 서지 않으면 회로·기대값을 고치지 말고 멈추고 보고한다 (assert 메시지에 '멈추고 보고').
# =====================================================================================================================
import inspect  # noqa: E402
import sys  # noqa: E402

from pdk_min_w import min_finger_w_m  # noqa: E402

from . import fs1_hand_sigma as H  # noqa: E402

M1_CIRCUIT = "two_stage_ota"
M1_STRICT = (("offset_in_sigma_mv", "<=", 0.001234),)        # 아주 엄격한 값 (실행 A) -- 어느 앵커도 통과하지 못해 모든 앵커를 훑는다


def _install_spies(monkeypatch):
    """관찰 지점 (§9 통과 spy -- 동작 대체 0): start_intervals.matching_bounds (호출 번호), iv_matching_l.mismatch_sigma_vgs (인자 기록)."""
    mb_mod = sys.modules["gmid_engine.search.start_intervals"]
    sg_mod = sys.modules["gmid_engine.search.iv_matching_l"]
    st = {"n": 0, "cur": None, "calls": [], "mb": []}
    orig_mb, orig_sg = mb_mod.matching_bounds, sg_mod.mismatch_sigma_vgs
    sig_sg, sig_mb = inspect.signature(orig_sg), inspect.signature(orig_mb)

    def mb(*a, **k):
        st["n"] += 1
        st["cur"] = st["n"]
        st["mb"].append(dict(sig_mb.bind(*a, **k).arguments))
        try:
            return orig_mb(*a, **k)
        finally:
            st["cur"] = None

    names = ("memo", "model", "kind", "w_key", "L", "vgs", "vds", "vsb", "w_f", "W")      # interface M-1 2: 인자 위치 그대로 (이름은 이 test 가 붙인다)

    def sg(*a, **k):
        r = orig_sg(*a, **k)                                          # 예외 없이 끝난 호출만 기록
        vals = tuple(sig_sg.bind(*a, **k).arguments.values())
        assert len(vals) == len(names), vals
        st["calls"].append((st["cur"], dict(zip(names, vals))))
        return r
    monkeypatch.setattr(mb_mod, "matching_bounds", mb)
    monkeypatch.setattr(sg_mod, "mismatch_sigma_vgs", sg)
    return st


def _first_stage_args(st, kind="nmos"):
    """4단계 = 출발 블록의 첫 matching_bounds 호출 안 spy 호출. 앵커 L 마다 예외 없이 끝난 마지막 호출의 인자."""
    by = {}
    for cur, b in st["calls"]:
        if cur == 1 and b["kind"] == kind:
            by[b["L"]] = b
    return by


@pytest.fixture(scope="module")
def m1_run_a():
    mp = pytest.MonkeyPatch()
    try:
        st = _install_spies(mp)
        case = real_case(M1_CIRCUIT, M1_STRICT)
    finally:
        mp.undo()
    return st, case


def test_m1_premise_input_devices_are_nmos(m1_run_a):
    """P0: 입력 소자 kind = nmos (helper input_gate_devices 와 그 소자 kind)."""
    st, case = m1_run_a
    inputs = input_gate_devices(case.topology)
    kinds = {d["name"]: d["kind"] for d in case.topology["netlist"]}
    assert inputs and {kinds[n] for n in inputs} == {"nmos"}, ("전제 P0 불성립 -- 멈추고 보고", inputs)


def test_m1_run_a_every_anchor_swept_and_w_f_is_reference_width(m1_run_a):
    """실행 A: 충돌 기록(입력 소자 matching L, 출처 matching_l_6.4_2)이 있고(어느 앵커도 통과 못함), 4단계 호출 w_f 가 모두 기준 폭 w_ref_m (P1, (a))."""
    st, case = m1_run_a
    sig = H.NfetSigma()
    allc = list(case.start.conflicts) + [c for r in case.start.rows for c in r.conflicts]
    conflicts = [c for c in allc if c.quantity == "L" and any(s == SRC_L for s, _ in c.bounds)]       # 출처 = 충돌 bounds 의 경계 출처
    assert {c.device for c in conflicts} >= input_gate_devices(case.topology), "실행 A 충돌 기록 없음 -- 멈추고 보고"
    by = _first_stage_args(st)
    assert len(by) >= 3, "4단계 spy 호출 없음 -- 멈추고 보고"
    assert any(math.isclose(L, 8e-6, rel_tol=1e-9) for L in by), ("L 앵커 범위가 8 µm 에 닿지 않는다 -- 멈추고 보고", sorted(by))
    for L, b in by.items():
        assert math.isclose(b["w_f"], sig.w_ref, rel_tol=1e-12), (L, b["w_f"], sig.w_ref)       # P1: 4단계 slope bin w_f = w_ref_m


def _pick(m1_run_a):
    st, case = m1_run_a
    sig = H.NfetSigma()
    H.check_bin_rule_against_evidence(sig)                              # 판정 꼴 먼저 대조 (bin 규칙 선언 evidence.points)
    by = _first_stage_args(st)
    args = {L: dict(vgs=b["vgs"], vds=b["vds"], vsb=b["vsb"], W=b["W"]) for L, b in by.items()}
    pick = H.pick_anchor(sig, args, min_finger_w_m(["nmos"])["nmos"])
    assert pick is not None, "전제 P2·P3 를 만족하는 앵커 없음 -- 멈추고 보고"
    return sig, by, pick


def test_m1_run_b_lower_bound_is_hand_picked_anchor_and_args_unchanged(m1_run_a, monkeypatch):
    """M-1: (a) 4단계 spy w_f = 모두 w_ref (b) 입력 소자 L 하한 값 == L_k (앵커 값 그대로) (c) 4단계 spy 인자 (vgs, vds, vsb, W) 가 실행 A 와 같은 L 에서 `==`.
    전제 P4: w_alt ≠ w_ref 이고 그 소자 wf_start 칸 키 × 격자 ≠ w_ref."""
    sig, by_a, pick = _pick(m1_run_a)
    assert not math.isclose(pick["w_alt"], sig.w_ref, rel_tol=1e-12)                                # P4 앞부분
    value_mv = pick["sigma_share"] * math.sqrt(2.0) / 1e-3
    st = _install_spies(monkeypatch)
    case = real_case(M1_CIRCUIT, (("offset_in_sigma_mv", "<=", value_mv),))
    by_b = _first_stage_args(st)
    assert by_b, "실행 B 4단계 spy 호출 없음 -- 멈추고 보고"
    for L, b in by_b.items():
        assert math.isclose(b["w_f"], sig.w_ref, rel_tol=1e-12), (L, b["w_f"])                      # (a)
    rows = rows_by_name(case.start)
    inputs = input_gate_devices(case.topology)
    assert inputs
    for dev in sorted(inputs):
        lo = bound_values(rows[dev], SRC_L, "L", "lo")
        assert lo and max(lo) == pick["k_L"], (dev, lo, pick["k_L"])                                # (b) 앵커 값 그대로 `==`
    for L, b in by_b.items():
        if L in by_a:
            assert (b["vgs"], b["vds"], b["vsb"], b["W"]) == (by_a[L]["vgs"], by_a[L]["vds"], by_a[L]["vsb"], by_a[L]["W"]), L   # (c)
    # P4 뒷부분: 그 소자 wf_start 칸 키 × 격자 ≠ w_ref (출발 블록 결과 스냅샷에서 읽음; 칸 키 ≠ 기준 폭 키)
    base = case.sctx.dc.base
    cells = base.value("graph", "start", "wf_start")
    grid = case.kctx.lut.spec.manufacturing_grid_m
    for dev in sorted(inputs):
        (cell,) = [c for c in cells if dev in c.members]
        assert cell.w_key is not None and not math.isclose(cell.w_key * grid, sig.w_ref, rel_tol=1e-12), ("전제 P4 불성립 -- 멈추고 보고", dev, cell)


def test_m2_guard_path_slope_bin_is_cell_key_times_grid(monkeypatch):
    """M-2 (6단계 가드 경로): 출발 블록 전체 한 번 -- 첫 이후의 matching_bounds 호출 안 spy 호출의 slope bin w_f = 그 소자 wf_start 칸 w_key × 격자 (spy 인자).
    (4단계 호출 = 기준 폭 w_ref 와 칸 키가 다른 회로에서 갈린다 -- 아래 단언은 호출 번호 2 이상만 본다.)"""
    st = _install_spies(monkeypatch)
    case = real_case(M1_CIRCUIT, (("offset_in_sigma_mv", "<=", 0.0031415),))
    sig = H.NfetSigma()
    base = case.sctx.dc.base
    cells = base.value("graph", "start", "wf_start")
    grid = case.kctx.lut.spec.manufacturing_grid_m
    keys = {m: c.w_key for c in cells for m in c.members}
    later = [b for cur, b in st["calls"] if cur is not None and cur >= 2 and b["kind"] == "nmos"]
    assert later, "6단계 가드 spy 호출 없음 -- 멈추고 보고"
    widths_seen = {round(b["w_f"] / grid) for b in later}
    inputs = input_gate_devices(case.topology)
    want = {keys[d] for d in inputs}
    assert want <= widths_seen, ("6단계 가드 w_f 가 칸 키 × 격자가 아니다", widths_seen, want)
    assert not all(math.isclose(b["w_f"], sig.w_ref, rel_tol=1e-12) for b in later), "칸 키 ≠ 기준 폭 인 toy 가 아니다 -- 멈추고 보고"
