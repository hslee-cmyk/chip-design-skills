"""`metrics.passive_values` 계산 블록 -- GB5 수동소자 값 필드 `device.passive_value` (설계 40 v1.6 §2.4.7 '수동소자 값' 행·§2.4.8 소유표,
DEC-92, metrics CONTRACT 7.6).

호출 `passive_values(snapshot, element_values, zero_cancel, theta)` -- reads `device.element_class`·`device.dc_gm`, writes
`device.passive_value`(이름·서명은 구현 공개 API 에 맞춤 -- 값의 정의는 설계).
oracle (a)·(d): 손 S2 스냅샷(S1 -> lift_s1, `device.dc_gm` 열은 권한표 writer dc_tolerances 로 손으로)에 세 출처를 손으로 둔다 -- spec
선언 값, θ 저항·커패시터·ss 저항, 영점 상쇄 구조 규칙 저항(설계 §2.4.7 R = 1/Σ`dc_gm`). 영점 상쇄 저항 값은 회로 해석(Miller 영점을
지우는 직렬 저항 = 1/(그 단의 gm 합))에서 손으로: dc_gm 1 mS + 3 mS -> 250 Ω.
실경로(two_stage_ota Rz = 1/dc_gm(M6))는 tests/convergence/test_converge.py 에서 본다(같은 필드가 판정 축 면적 입력으로 간다).
"""
from __future__ import annotations

import pytest

import gmid_engine.metrics as metrics
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.metrics import passive_values
from gmid_engine.sizing import S2_WRITERS, ZeroCancel

from .conftest import block_row, fresh_run, hand_write, row_delta, s2_of, schema_of, topo_doc, topo_only

SUP = {"vdd": 1.8, "gnd": 0.0}
GM = {"M1": 1e-3, "M2": 3e-3}                     # 손 dc_gm(writer dc_tolerances)
PASSIVES = ("R1", "C1", "Rs", "CL", "Cx", "Rz", "Rq")


def _topo():
    """M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd); 수동소자 7개(R1·Rq 분압 vdd-x-gnd, Rz out-x, C1·CL out-gnd, Cx out-in,
    Rs in-gnd); 이상 전류원 I1 vdd -> in. 이름 집합만 의미가 있다(값은 이 test 가 준다)."""
    return topo_doc("pv_hand",
                    mos=[("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "pmos", "out", "pb", "vdd", "vdd")],
                    passives=[("R1", "resistor", "vdd", "x"), ("Rq", "resistor", "x", "gnd"), ("Rz", "resistor", "out", "x"),
                              ("C1", "capacitor", "out", "gnd"), ("CL", "capacitor", "out", "gnd"), ("Cx", "capacitor", "out", "in"),
                              ("Rs", "resistor", "in", "gnd")],
                    sources=[("I1", "current_source", "vdd", "in")], rails=("vdd", "gnd"), bias=["pb"])


@pytest.fixture(scope="module")
def snap(tmp_path_factory):
    s = s2_of(topo_only(tmp_path_factory.mktemp("pv"), _topo()), SUP)
    assert {n for n, c in s.column("device", "element_class") if c == ELEMENT_PASSIVE} == set(PASSIVES)   # 전제
    return hand_write(s, "device", "dc_gm", GM)


def zc(resistor, cells, reason=None):
    return ZeroCancel(resistor, None, (), tuple(cells), reason)


def values_of(out):
    return dict(out.column("device", "passive_value"))


def test_public():
    assert "passive_values" in metrics.__all__


def test_block_declaration():
    """§2.4.8: writer = 권한표 writer_of(device, passive_value); reads element_class·dc_gm(§2.4.7 R = 1/Σ dc_gm -- dc 단계 필드,
    ss_dev 를 읽지 않으므로 봉인 전에도 정의된다)."""
    assert passive_values.name == S2_WRITERS.writer_of("device", "passive_value")
    assert set(passive_values.reads) == {("device", "element_class"), ("device", "dc_gm")}
    assert tuple(passive_values.writes) == (("device", "passive_value"),)


def test_three_sources_merged(snap):
    ev = (("CL", 3e-12), ("Cx", None), ("I1", 0.9))
    zcs = (zc("Rz", ("M1", "M2")), zc("Rq", ("M1",), reason="pending"))
    th = ((("resistance", "R1"), 1e3), (("capacitance", "C1"), 2e-12), (("ss_resistance", "Rs"), 5e4),
          (("ln_idu", "M1"), -14.0), (("current", "M2"), 1e-5))
    got = values_of(passive_values(snap, ev, zcs, th, **fresh_run()))
    assert sorted(got) == ["C1", "CL", "R1", "Rs", "Rz"]     # 값 없는 Cx·reason 있는 Rq·비수동 I1 제외
    assert (got["C1"], got["CL"], got["R1"], got["Rs"]) == (2e-12, 3e-12, 1e3, 5e4)
    assert got["Rz"] == pytest.approx(250.0, rel=1e-15)                  # 1 / (1 mS + 3 mS)
    assert all(isinstance(v, float) for v in got.values())


def test_theta_name_not_a_passive_is_rejected(snap):
    with pytest.raises(ValueError):
        passive_values(snap, (), (), ((("resistance", "M1"), 1e3),), **fresh_run())


def test_same_passive_from_two_sources_is_rejected(snap):
    with pytest.raises(ValueError):
        passive_values(snap, (("C1", 1e-12),), (), ((("capacitance", "C1"), 2e-12),), **fresh_run())
    with pytest.raises(ValueError):
        passive_values(snap, (), (zc("R1", ("M1",)),), ((("resistance", "R1"), 1e3),), **fresh_run())


def test_structural_resistor_must_be_passive(snap):
    with pytest.raises(ValueError):
        passive_values(snap, (), (zc("I1", ("M1",)),), (), **fresh_run())


def test_no_sources_gives_empty(snap):
    assert values_of(passive_values(snap, (), (), (), **fresh_run())) == {}


def test_field_follows_dc_gm_input_version(snap):
    """DF-15·§2.4.1: dc_gm 열만 바뀌면 다시 계산(R 이 따라간다), 같은 입력이면 재사용(`is`)."""
    run = fresh_run()
    zcs = (zc("Rz", ("M1", "M2")),)
    s1 = passive_values(snap, (), zcs, (), **run)
    assert passive_values(s1, (), zcs, (), **run) is s1
    s2 = passive_values(hand_write(s1, "device", "dc_gm", {"M1": 2e-3, "M2": 6e-3}, version="gm2"), (), zcs, (), **run)
    assert s2 is not s1
    assert values_of(s2)["Rz"] == pytest.approx(125.0, rel=1e-15)

# ===========================================================================
# [U17 ①] 수동소자 값 = S2 필드 `device.passive_value` (설계 40 v1.6 §2.4.7 '수동소자 값' 행, §2.4.8 소유표, §3.7-3, 10.3a DF-15)
#
# 근거 문언:
# - §2.4.8: 수동소자 값(spec ∪ θ ∪ 영점 상쇄 R = 1/Σ`dc_gm`) -> `device: passive_value`, writer = GB5 수동소자 블록(`passive_values`를
#   블록으로). 엔진·오라클 입력·레이아웃 어댑터가 이 필드를 읽는다.
# - §2.4.7: 영점 상쇄 R = 1/Σ`dc_gm`(dc 단계 필드)이라 봉인 전에도 정의되고, `kernel.py:146-150` 사본과 '봉인 아닌 점은 값 없음'
#   분기를 지운다.
# - §10.3a DF-15: 영점 상쇄 R 은 입력 버전 있는 필드(`device.passive_value`). 설계 표의 test 이름 `test_df15_zero_cancel_is_versioned_field`
#   를 함수 이름으로 쓰고, 파일은 규칙 H(test↔원본 1:1)에 따라 원본 `metrics/passive_values.py` 의 짝인 이 파일에 둔다.
#
# 블록의 호출 서명·writer 이름은 설계에 없다(이름 미정) -- 그래서 블록을 직접 부르지 않고, 설계가 이 필드의 소비자로 적은 실제 평가
# 경로(search `evaluate`: 봉인 점 = ss 경로, 봉인 전 점 = pending_seal_7 경로)가 낸 설계점 스냅샷에서 필드를 읽는다. writer 이름은
# 권한표(`S2_WRITERS.writer_of`)에서 읽는다.
#
# 손 회로 M(Miller 영점 상쇄): 회로 C(M1 nmos (out, in, gnd) + M2 pmos 부하 (out, pb, vdd)) + Rz (out, x) + Cc (x, in), 둘 다 spec engine,
# + 값 선언 부하 CL (out, gnd). x 는 수동소자만 닿는 내부 넷이라 Rz 는 DC 전류 0(가지치기)이고, Rz–Cc 망의 경계 넷은 out·in --
# source 가 교류접지(gnd)이고 {drain, gate} = {out, in} 인 CS 셀은 M1 하나(M2 의 gate 는 pb). 그래서 회로 해석으로 S = {M1},
# Rz = 1/dc_gm(M1) (DEC-92 (3)(a), J7). 기대값 dc_gm(M1) = 자기 동작점 ID × LUT 파일 gm/ID(sizing conftest `hand_dc_gm`).
# ===========================================================================

RB_M, CB_M = (1e2, 1e6), (1e-14, 1e-10)
CC_F = 2e-12                    # θ 커패시터 값(구성 입력)
CL_F = 1e-12                    # spec 선언 부하 값(구성 입력)
M_ELEMENTS = (("Rz", "resistor", None), ("Cc", "capacitor", None), ("CL", "capacitor", CL_F))


def _circuit_m():
    from sizing.conftest import circuit_cs_pmos_load, two
    d = circuit_cs_pmos_load()
    d["topology_name"] = "u17_miller_zero_cancel"
    d["passive_elements"] = [two("Rz", "resistor", "out", "x"), two("Cc", "capacitor", "x", "in"),
                             two("CL", "capacitor", "out", "gnd")]
    return d


@pytest.fixture(scope="module")
def m_luts(tmp_path_factory):
    """r4 toy LUT 두 벌: VDSAT 열 있음(봉인 점) / 없음(봉인 7 undefined -> pending_seal_7, 봉인 전 점). -> {이름: (LutSet, 폴더)}."""
    from sizing.conftest import write_r4_lut
    a = tmp_path_factory.mktemp("u17_m_sealed")
    b = tmp_path_factory.mktemp("u17_m_pending")
    return {"sealed": (write_r4_lut(a), a), "pending": (write_r4_lut(b, vdsat=()), b)}


def _case_m(tmp, lut):
    from search.conftest import build_case
    return build_case(tmp, _circuit_m(), lut, elements=M_ELEMENTS, rbounds=RB_M, cbounds=CB_M)


def _theta_m(dc, cc=CC_F, **kw):
    """회로 M 의 θ = 회로 C 의 θ(sizing conftest theta_r4c, y 키는 스키마의 W4 뿌리 이름) + Cc 커패시턴스. Rz 는 θ 가 아니다(전제)."""
    from sizing.conftest import theta_r4c
    th = dict(theta_r4c(**kw))
    y = th.pop(("y", "out"))
    ykeys = [k for k in schema_of(dc).components if k[0] == "y"]
    assert len(ykeys) == 1
    th[ykeys[0]] = y
    th[("capacitance", "Cc")] = cc
    assert set(th) == set(schema_of(dc).components), (sorted(th), schema_of(dc).components)
    return tuple(sorted(th.items()))


def _eval_m(case, th):
    from search.conftest import CELLS_C
    from search.conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
    return evaluate(case.sctx, th, CELLS_C)


def _expected_rz(snap, root):
    from sizing.conftest import hand_dc_gm, r4_npz
    op = dict(snap.column("device", "dc_op"))["M1"]
    return 1.0 / hand_dc_gm(lambda kind: r4_npz(root, kind), op)


def test_passive_value_single_writer():
    """§2.4.8: `device.passive_value` 의 writer 는 하나다. 권한표에 writer 가 있고, 엔진 공개 API 의 계산 블록 중 그 필드를 writes 에
    선언한 블록은 정확히 하나이며 그 이름이 권한표 writer 와 같다(이름 자체는 설계에 없어 단언하지 않는다)."""
    import importlib
    from gmid_engine.core import ComputeBlock
    from gmid_engine.sizing import S2_WRITERS
    writer = S2_WRITERS.writer_of("device", "passive_value")
    assert writer is not None
    owners = set()
    for pkg in ("core", "lut", "authoring", "graph", "sizing", "metrics", "search", "layout", "convergence", "report",
                "pipeline"):
        mod = importlib.import_module("gmid_engine." + pkg)
        for name in getattr(mod, "__all__", ()):
            obj = getattr(mod, name)
            if isinstance(obj, ComputeBlock) and ("device", "passive_value") in set(obj.writes):
                owners.add(obj.name)
    assert owners == {writer}, owners


@pytest.mark.parametrize("which", ["sealed", "pending"])
def test_zero_cancel_r_is_inverse_sum_dc_gm(tmp_path, m_luts, which):
    """§2.4.7·§2.4.8·§3.7-3: 설계점 스냅샷의 `device.passive_value` -- Rz = 1/Σ_{S} dc_gm = 1/dc_gm(M1)(손계산, LUT 파일), Cc = θ 값,
    CL = spec 선언 값. 봉인 점(sealed)과 봉인 전 점(pending_seal_7)에서 모두 정의된다('봉인 아닌 점은 값 없음' 분기 삭제)."""
    from gmid_engine.search import STATUS_PENDING_SEAL7, STATUS_SEALED
    lut, root = m_luts[which]
    case = _case_m(tmp_path, lut)
    zc_rz = {z.resistor: z for z in schema_of(case.dc).zero_cancel}["Rz"]        # 전제: 구조 규칙이 Rz 를 정한다(셀 M1)
    assert zc_rz.reason is None and tuple(zc_rz.cells) == ("M1",)
    r = _eval_m(case, _theta_m(case.dc))
    assert r.status == (STATUS_SEALED if which == "sealed" else STATUS_PENDING_SEAL7)
    snap = r.evaluation.snapshot
    pv = dict(snap.column("device", "passive_value"))
    assert set(pv) == {"Rz", "Cc", "CL"}, pv
    want = _expected_rz(snap, root)
    assert pv["Rz"] == pytest.approx(want, rel=1e-9), (pv["Rz"], want)
    assert pv["Cc"] == CC_F and pv["CL"] == CL_F


def test_df15_zero_cancel_is_versioned_field(tmp_path, m_luts):
    """DF-15: 영점 상쇄 R 은 입력 버전 있는 필드다 -- 권한표 writer 의 블록 입력 버전이 설계점 스냅샷에 기록되어 있고(필드가 곧 캐시,
    §2.4.1), 값은 dc_gm 을 따라간다: 수동소자 θ(Cc)만 바꾼 점은 Rz 가 비트 동일, M1 동작점(vgs)을 바꾼 점은 Rz = 새 1/dc_gm(M1)(손계산)."""
    from gmid_engine.sizing import S2_WRITERS
    lut, root = m_luts["pending"]
    case = _case_m(tmp_path, lut)
    writer = S2_WRITERS.writer_of("device", "passive_value")
    r0 = _eval_m(case, _theta_m(case.dc))
    r1 = _eval_m(case, _theta_m(case.dc, cc=2 * CC_F))
    r2 = _eval_m(case, _theta_m(case.dc, v1=0.62))
    s0, s1, s2 = (x.evaluation.snapshot for x in (r0, r1, r2))
    assert writer is not None and s0.block_version(writer) is not None
    pv0, pv1, pv2 = (dict(s.column("device", "passive_value")) for s in (s0, s1, s2))
    assert pv1["Rz"] == pv0["Rz"] and pv1["Cc"] == 2 * CC_F
    assert pv2["Rz"] != pv0["Rz"]
    assert pv2["Rz"] == pytest.approx(_expected_rz(s2, root), rel=1e-9)


# ===========================================================================
# [회귀 9065d5f, 재검증 _audit_u17_1c_r2 §F-2] `passive_values` extras 의 θ 칸 = 수동소자 θ 성분만(`theta_passive_pairs`).
# 근거: 설계 40 §2.4.1 'FD 스텝: θ가 다르므로 입력 버전이 다르다. 그 성분을 읽는 블록만 계산한다(WP-23 (5))' -- 이 블록이 읽는 θ 성분은
# 수동소자 값의 출처인 θ 저항·커패시터·ss 저항(metrics CONTRACT 7.6 DEC-92, 42 #24 'θ capacitance, ss_resistance')뿐이다. extras 는 투영
# 지문에 들어가므로 MOS θ(L·ln_idu·current·y)까지 넘기면 MOS θ 만 다른 스텝에서도 다시 계산한다. 호출 경로 두 곳(봉인점 `ss_evaluate`,
# 비봉인점 `search.kernel`)의 관찰 test 는 각 원본의 짝 파일(tests/metrics/test_ss_evaluate.py, tests/search/test_kernel.py)에 둔다(규칙 H).
# ===========================================================================

MIXED_THETA = (
    (("L", "M1"), 1e-6),
    (("resistance", "R1"), 1e3),
    (("ln_idu", "M1"), -14.0),
    (("ss_resistance", "Rs"), 5e4),
    (("current", "M2"), 1e-5),
    (("capacitance", "C1"), 2e-12),
    (("y", "out"), 0.5),
    (("capacitance", "CL"), 1e-12),
)


def test_theta_passive_pairs_public():
    assert "theta_passive_pairs" in metrics.__all__


def test_theta_passive_pairs_selects_passive_components_in_order():
    """손 θ(MOS·수동 성분 섞임) -> resistance·capacitance·ss_resistance 성분만, 원래 순서·원래 값 그대로(손으로 고른 기대값)."""
    from gmid_engine.metrics import theta_passive_pairs
    want = ((("resistance", "R1"), 1e3), (("ss_resistance", "Rs"), 5e4), (("capacitance", "C1"), 2e-12),
            (("capacitance", "CL"), 1e-12))
    assert theta_passive_pairs(MIXED_THETA) == want
    assert theta_passive_pairs(tuple(reversed(MIXED_THETA))) == tuple(reversed(want))     # 정렬하지 않는다 -- 원래 순서
    mos_only = tuple(p for p in MIXED_THETA if p[0][0] in ("L", "ln_idu", "current", "y"))
    assert theta_passive_pairs(mos_only) == ()
    assert theta_passive_pairs(()) == ()


def test_mos_theta_change_reuses_block_through_selector(snap):
    """같은 dc_gm 스냅샷에서 MOS θ 만 바꾼 θ 를 `theta_passive_pairs` 로 고르면 extras 가 같아 재사용(`is`, computes 0),
    수동소자 θ(R1)를 바꾸면 계산 1 -- 값은 새 θ 값(손)."""
    from gmid_engine.metrics import theta_passive_pairs
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행의 구간 증분(재사용 1·계산 0, 다음 구간 계산 1)
    run = fresh_run()
    zcs = (zc("Rz", ("M1", "M2")),)
    s1 = passive_values(snap, (), zcs, theta_passive_pairs(MIXED_THETA), **run)
    mos_step = tuple(((k, v * 1.01) if k[0] in ("L", "ln_idu", "current", "y") else (k, v)) for k, v in MIXED_THETA)
    before = block_row(run["counters"], passive_values.name)
    assert passive_values(s1, (), zcs, theta_passive_pairs(mos_step), **run) is s1
    assert row_delta(block_row(run["counters"], passive_values.name), before) == (1, 1, 0, 0, 0, 0)
    r_step = tuple(((k, 2e3) if k == ("resistance", "R1") else (k, v)) for k, v in MIXED_THETA)
    s2 = passive_values(s1, (), zcs, theta_passive_pairs(r_step), **run)
    assert row_delta(block_row(run["counters"], passive_values.name), before)[4] == 1 and s2 is not s1
    assert values_of(s2)["R1"] == 2e3 and values_of(s2)["Rz"] == values_of(s1)["Rz"]
