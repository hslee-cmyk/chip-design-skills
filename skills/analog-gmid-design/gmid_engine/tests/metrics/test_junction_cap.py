"""`junction_at_vgs_min` (접합 Cdb·Csb = LUT VGS 최소 조회 비례) + `DiffusionGeometry` -- interface card 20261106-jc1 §1 (J-1~J-12, C-0).

[JC-1] 옛 BSIM4 식 test(`junction_caps`·`JunctionParams`·`JunctionCaps`, 8.2 독립 기준 식, ngspice capbd/capbs 대조)는 모두 이 파일에서 빠졌다
-- `tests/RETIRED_TESTS_jc1.md` (covered_by = J-1~J-12). 남은 것: `DiffusionGeometry` 생성 검사·`from_lut_rule`(확산 기하 출처 -- 분류 ③ 유지).

독립 검증(작성자 ≠ 검증자): 기대값 출처는 하나 -- 정의 문장 `cdb = (CDD − CGD)·r_d`, `csb = (CSS − CGS)·r_s`, r = (면적·m)/(기준 면적·m_ref)를
기준 폭 표 격자 마디 값(jc1_toy 의 손 식 F)에 적용한 손 계산(oracle (a)/(d): 구성으로 정답이 정해진 합성 입력, 허용오차 상수 0 -- 비트 동일).
피검 함수·`DiffusionGeometry.from_lut_rule`·`lut_parameters` 로 기대값을 만들지 않는다. 공통 ε_d 식은 쓰지 않는다. SPICE 0.
"""
import dataclasses
import json
import math
import os
import sys
from pathlib import Path

import pytest

from gmid_engine.core import BoundedLRU, SchemaRejectedError, SealViolationError, read_pdk_decl, require_immutable
from gmid_engine.metrics import DiffusionGeometry, junction_at_vgs_min

from .jc1_toy import cdd, cgd, cgs, css, hand_junction, rule_values, toyc_cap_arrays, toyc_memo, node_of

SKILL_DIR = Path(__file__).resolve().parents[3]
PDK_DECL = SKILL_DIR / "assets" / "sky130_pdk_decl.json"
LUT_RULE_DECL = SKILL_DIR / "assets" / "sky130_lut_rule_decl.json"
_PDK = json.loads(PDK_DECL.read_text(encoding="utf-8"))
_SKY_PRESENT = all(os.path.isfile(_PDK["pdk_root"] + "/" + s["path"]) for s in _PDK["sources"].values())

W_EVAL = 3e-6
POINT = (2e-6, 1.0, 0.5)            # J-1 조회점 (L, vds, vsb) = 격자 마디 (1, 1, 1)
JUNCTION_MODULE = "gmid_engine.metrics.junction_cap"


def _detail(excinfo):
    return dict(excinfo.value.record.detail)


def _geo(v, W, m=1.0, ad=None, as_=None):
    return DiffusionGeometry(W, v["a"] * W if ad is None else ad, v["b"] * W if as_ is None else as_,
                             W + v["pd"], W + v["ps"], m)


def _ref(v):
    """기준 기하 손 값(생성자 직접 -- from_lut_rule 로 만들지 않는다)."""
    return DiffusionGeometry(1e-6, v["a"] * 1e-6, v["b"] * 1e-6, 1e-6 + v["pd"], 1e-6 + v["ps"], 1.0)


@pytest.fixture
def v(tmp_path):
    return rule_values(tmp_path / "rule")


@pytest.fixture
def memo(tmp_path):
    return toyc_memo(tmp_path / "lut")


def test_junction_c0_premise_node_lookup_is_table_value(memo):
    """C-0 전제: 격자 마디 조회 `caps(memo, "nmos", L, 0.25, vds, vsb, 1e-6)` 의 cdd = 표 CDD 마디 값 -- 안 서면 멈추고 보고."""
    from gmid_engine.lut import caps
    l, d, s = node_of(*POINT[:1], *POINT[1:])
    c = caps(memo, "nmos", POINT[0], 0.25, POINT[1], POINT[2], 1e-6)
    # oracle (a): 표 CDD 마디 값 = 손 식 F (jc1_toy.cdd) -- 같은 float
    assert c.cdd == cdd(l, 0, d, s)
    assert c.css == css(l, 0, d, s)


def test_junction_j1_hand_value_bit_identical(memo, v):
    """J-1: cdb = (CDD − CGD)[1,0,1,1]·((a·W·1.0)/(a·1e-6·1.0)), csb 같은 꼴 -- 비트 동일. oracle (a)."""
    l, d, s = node_of(*POINT[:1], *POINT[1:])
    cdb, csb = junction_at_vgs_min(memo, "M1", "nmos", *POINT, _geo(v, W_EVAL), _ref(v))
    exp = hand_junction(l, d, s, v["a"] * W_EVAL, v["b"] * W_EVAL, 1.0, v)
    assert (cdb, csb) == exp
    assert cdb > 0.0 and csb > 0.0


def test_junction_j2_area_and_m_scale(memo, v):
    """J-2: m = 4.0 이고 ad·as 가 규칙 값과 다른 값 -> r = (ad_m2·m)/(a·1e-6·1.0). oracle (a)."""
    l, d, s = node_of(*POINT[:1], *POINT[1:])
    ad, as_ = 0.7 * v["a"] * W_EVAL, 0.6 * v["b"] * W_EVAL
    cdb, csb = junction_at_vgs_min(memo, "M1", "nmos", *POINT, _geo(v, W_EVAL, m=4.0, ad=ad, as_=as_), _ref(v))
    assert (cdb, csb) == hand_junction(l, d, s, ad, as_, 4.0, v)
    base = junction_at_vgs_min(memo, "M1", "nmos", *POINT, _geo(v, W_EVAL), _ref(v))
    assert (cdb, csb) != base                 # 공허 방지: 규칙 기하와 다른 값


def _neg_memo(tmp_path, d=False, s=False):
    node = (1, 0, 1, 1)
    over = {}
    if d:
        over["CDD"] = {node: cgd(*node) - 1e-16}
    if s:
        over["CSS"] = {node: cgs(*node) - 1e-16}
    return toyc_memo(tmp_path / "lut", cap=toyc_cap_arrays(set_node=over))


@pytest.mark.parametrize("d,s,terminal", [(True, False, "d"), (False, True, "s"), (True, True, "d")], ids=["J-3", "J-4", "J-5"])
def test_junction_j3_j5_negative_junction_cap_stops(tmp_path, v, d, s, terminal):
    """J-3/4/5: CDD(또는 CSS) 마디만 CGD(CGS) − 1e-16 -> cdb(csb) < 0 -> SealViolationError junction_cap_negative, 단자 d 먼저. oracle (d): 수동성 관문 계약."""
    m = _neg_memo(tmp_path, d, s)
    with pytest.raises(SealViolationError) as ei:
        junction_at_vgs_min(m, "M1", "nmos", *POINT, _geo(v, W_EVAL), _ref(v))
    det = _detail(ei)
    assert ei.value.record.devices == ("M1",)
    assert det["reason"] == "junction_cap_negative" and det["terminal"] == terminal
    assert det["value"] < 0.0


def test_junction_negative_check_clean_table_does_not_stop(memo, v):
    """J-3~J-7 의 음성 대조: 같은 호출이 정상 표에서는 정지하지 않는다(정지가 음수·NaN 마디 때문임)."""
    junction_at_vgs_min(memo, "M1", "nmos", *POINT, _geo(v, W_EVAL), _ref(v))


@pytest.mark.parametrize("col,terminal", [("CDD", "d"), ("CSS", "s")], ids=["J-6", "J-7"])
def test_junction_j6_j7_nan_junction_cap_stops(tmp_path, v, col, terminal):
    """J-6/7: CDD(CSS) 마디 = NaN -> junction_cap_negative(음수·NaN 모두 `not (v >= 0)`), value NaN."""
    m = toyc_memo(tmp_path / "lut", cap=toyc_cap_arrays(set_node={col: {(1, 0, 1, 1): float("nan")}}))
    with pytest.raises(SealViolationError) as ei:
        junction_at_vgs_min(m, "M1", "nmos", *POINT, _geo(v, W_EVAL), _ref(v))
    det = _detail(ei)
    assert det["reason"] == "junction_cap_negative" and det["terminal"] == terminal and math.isnan(det["value"])
    assert ei.value.record.devices == ("M1",)


@pytest.mark.parametrize("drop,column", [(("CDD",), "CDD"), (("CSS",), "CSS"), (("CGS",), "CGS")], ids=["J-8", "J-9", "J-10"])
def test_junction_j8_j10_column_unavailable(tmp_path, v, drop, column):
    """J-8/9/10: 기준 표에 CDD(CSS, CGS) 열 없음 -> lut_column_unavailable{column, kind}, devices == () (CGB 있는데도 CGS 결손은 CGS 로 보고 --
    CGS 대신 CGG − CGD 를 쓰지 않는다)."""
    m = toyc_memo(tmp_path / "lut", cap=toyc_cap_arrays(drop=drop))
    with pytest.raises(SealViolationError) as ei:
        junction_at_vgs_min(m, "M1", "nmos", *POINT, _geo(v, W_EVAL), _ref(v))
    assert _detail(ei) == {"reason": "lut_column_unavailable", "column": column, "kind": "nmos"}
    assert ei.value.record.devices == ()


def test_vgs_min_j11_vgs_is_axis_first_value_not_zero_and_width_is_reference(tmp_path, monkeypatch, memo, v):
    """J-11 상수 0: 관찰 지점 `junction_cap.caps` 통과 spy -- 기록된 VGS 인자 == 0.25(표 VGS 축 첫 값, 0 아님), W 인자 == reference.finger_w_m.
    oracle (d): 계약(조회 좌표 = 기준 폭 표 VGS 축 첫 값)."""
    import inspect
    mod = sys.modules[JUNCTION_MODULE]
    orig = mod.caps
    sig = inspect.signature(orig)
    seen = []

    def spy(*a, **k):
        seen.append(list(sig.bind(*a, **k).arguments.values()))       # (memo, kind, L, vgs, vds, vsb, W)
        return orig(*a, **k)

    monkeypatch.setattr(mod, "caps", spy)
    ref = _ref(v)
    junction_at_vgs_min(memo, "M1", "nmos", *POINT, _geo(v, W_EVAL), ref)
    assert len(seen) == 1
    memo_a, kind, L, vgs, vds, vsb, W = seen[0]
    assert vgs == 0.25 and vgs != 0.0
    assert W == ref.finger_w_m
    assert (kind, L, vds, vsb) == ("nmos", POINT[0], POINT[1], POINT[2])


def test_vgs_min_j12_no_branch_at_axis_end_nodes(memo, v):
    """J-12 분기 0: (L, vds, vsb) = (3e-6, 0.5, 0.0) -- L 끝 마디·VDS 첫 마디·VSB 0 도 J-1 과 같은 식, 정지 없음."""
    pt = (3e-6, 0.5, 0.0)
    l, d, s = node_of(*pt[:1], *pt[1:])
    assert (l, d, s) == (2, 0, 0)
    cdb, csb = junction_at_vgs_min(memo, "M1", "nmos", *pt, _geo(v, W_EVAL), _ref(v))
    assert (cdb, csb) == hand_junction(l, d, s, v["a"] * W_EVAL, v["b"] * W_EVAL, 1.0, v)


# ---------------------------------------------------------------- DiffusionGeometry (분류 ③ 유지) -- 생성 검사·고정
GEO_REJECTS = [
    ((0.0, 1e-12, 1e-12, 3e-6, 3e-6, 2.0), ValueError),
    ((-1e-6, 1e-12, 1e-12, 3e-6, 3e-6, 2.0), ValueError),
    ((1e-6, 1e-12, 1e-12, 3e-6, 3e-6, 0.0), ValueError),
    ((1e-6, 1e-12, 1e-12, 3e-6, 3e-6, -1.0), ValueError),
    ((1e-6, -1e-15, 1e-12, 3e-6, 3e-6, 2.0), ValueError),
    ((1e-6, 1e-12, -1e-15, 3e-6, 3e-6, 2.0), ValueError),
    ((1e-6, 1e-12, 1e-12, -1e-9, 3e-6, 2.0), ValueError),
    ((1e-6, 1e-12, 1e-12, 3e-6, -1e-9, 2.0), ValueError),
    ((float("nan"), 1e-12, 1e-12, 3e-6, 3e-6, 2.0), ValueError),
    ((1e-6, 1e-12, 1e-12, 3e-6, 3e-6, float("inf")), ValueError),
    ((1e-6, True, 1e-12, 3e-6, 3e-6, 2.0), TypeError),
    ((1e-6, 1e-12, 1e-12, 3e-6, 3e-6, True), TypeError),
    (("1e-6", 1e-12, 1e-12, 3e-6, 3e-6, 2.0), TypeError),
]


@pytest.mark.parametrize("args,exc", GEO_REJECTS, ids=[str(i) for i in range(len(GEO_REJECTS))])
def test_geometry_rejected(args, exc):
    with pytest.raises(exc):
        DiffusionGeometry(*args)


def test_geometry_normalised_zero_area_allowed_and_frozen():
    g = DiffusionGeometry(1e-6, 0, 0, 0, 0, 3)
    assert tuple(f.name for f in dataclasses.fields(DiffusionGeometry)) == \
        ("finger_w_m", "ad_m2", "as_m2", "pd_m", "ps_m", "m")
    assert all(type(getattr(g, f.name)) is float for f in dataclasses.fields(DiffusionGeometry))
    with pytest.raises(dataclasses.FrozenInstanceError):
        g.m = 1.0
    require_immutable(g)


def _rel_close(a, b, rtol):
    return abs(a - b) <= rtol * max(abs(a), abs(b))


@pytest.mark.skipif(not _SKY_PRESENT, reason="sky130 원본 없음")
def test_from_lut_rule_sky130():
    memo = BoundedLRU(16)
    pdk, rule = read_pdk_decl(str(PDK_DECL), memo), read_pdk_decl(str(LUT_RULE_DECL), memo)
    g = DiffusionGeometry.from_lut_rule(rule, 2e-6, 3)
    assert isinstance(g, DiffusionGeometry)
    assert g.finger_w_m == 2e-6 and g.m == 3.0
    assert g.ad_m2 == rule.value("lut_diffusion_ad_per_w_m") * 2e-6
    assert g.as_m2 == rule.value("lut_diffusion_as_per_w_m") * 2e-6
    assert g.pd_m == 2e-6 + rule.value("lut_diffusion_pd_extra_m")
    assert g.ps_m == 2e-6 + rule.value("lut_diffusion_ps_extra_m")
    with pytest.raises(SchemaRejectedError) as ei:
        DiffusionGeometry.from_lut_rule(pdk, 2e-6, 3)
    assert dict(ei.value.record.detail)["reason"] == "pdk_quantity_undeclared"
    with pytest.raises(ValueError):
        DiffusionGeometry.from_lut_rule(rule, 0.0, 3)
    with pytest.raises(ValueError):
        DiffusionGeometry.from_lut_rule(rule, 2e-6, 0)


def test_junction_from_lut_rule_toy_decl(tmp_path, v):
    """toy 규칙 선언(core 가 읽은 값 v)에서 확산 기하: finger_w = w, ad = a·w, as = b·w, pd = w + pd_extra, ps = w + ps_extra, m. oracle (a): 선언 값 × 폭."""
    from .conftest import read_rule_decl, toy_rule_decl
    rule = read_rule_decl(toy_rule_decl(tmp_path / "r2"))
    g = DiffusionGeometry.from_lut_rule(rule, 1e-6, 2.5)
    assert (g.finger_w_m, g.ad_m2, g.as_m2, g.pd_m, g.ps_m, g.m) == (
        1e-6, v["a"] * 1e-6, v["b"] * 1e-6, 1e-6 + v["pd"], 1e-6 + v["ps"], 2.5)
