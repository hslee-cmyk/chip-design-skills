"""`junction_caps` (BSIM4 접합 용량 cdb·csb, JunctionParams·DiffusionGeometry·JunctionCaps) -- metrics CONTRACT 8절.

독립 검증(작성자 ≠ 검증자): 기대값 출처는 셋뿐이다.
- 이 파일의 `ref_caps` -- 계약 8.2 의 식(온도 보정·permod·P_eff 음수 허용·역/순바이어스 가지)을 따로 구현.
- 계약 8.3 손계산 예·8.4 예 숫자·core CONTRACT 9.4 접합 파라미터 표.
- ngspice-46 `@m[capbd]`/`@m[capbs]` 실측(환경에 ngspice·sky130 이 있을 때만 -- 없으면 skip).
8.2 의 알려진 ngspice 불연속(P < Weffcj 이고 바이어스가 정확히 0)은 ngspice 대조 격자에서 빼고 따로 계약 문장대로 확인한다.
"""
import dataclasses
import hashlib
import json
import os
import random
import re
import subprocess
from pathlib import Path

import pytest

from gmid_engine.core import BoundedLRU, SchemaRejectedError, fp_of, read_pdk_decl, require_immutable
from gmid_engine.metrics import DiffusionGeometry, JunctionCaps, JunctionParams, junction_caps

from .conftest import JUNCTION_FIELDS, ref_caps

SKILL_DIR = Path(__file__).resolve().parents[3]
PDK_DECL = SKILL_DIR / "assets" / "sky130_pdk_decl.json"
LUT_RULE_DECL = SKILL_DIR / "assets" / "sky130_lut_rule_decl.json"

FIELDS = JUNCTION_FIELDS


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


_PDK = _load_json(PDK_DECL)
_SKY_PRESENT = all(os.path.isfile(_PDK["pdk_root"] + "/" + s["path"]) for s in _PDK["sources"].values())
NGSPICE = Path(r"C:\ngspice\Spice64\bin\ngspice_con.exe")
needs_ngspice = pytest.mark.skipif(not (_SKY_PRESENT and NGSPICE.is_file()), reason="ngspice-46 또는 sky130 없음")


def reason(excinfo):
    return dict(excinfo.value.record.detail)["reason"]


def rel_close(a, b, rtol):
    return abs(a - b) <= rtol * max(abs(a), abs(b))


# 독립 기준 식(계약 8.2) `ref_caps` 는 conftest 로 옮겼다 -- ss_linearize·junction_source test 도 같은 식을 쓴다.


# ---------------------------------------------------------------- 8.3 손계산 예

HAND = dict(cjs=1e-3, cjd=1e-3, cjsws=1e-10, cjswd=1e-10, cjswgs=2e-10, cjswgd=2e-10,
            mjs=0.5, mjd=0.5, mjsws=0.5, mjswd=0.5, mjswgs=0.5, mjswgd=0.5,
            pbs=1.0, pbd=1.0, pbsws=1.0, pbswd=1.0, pbswgs=1.0, pbswgd=1.0,
            tcj=0.0, tcjsw=0.0, tcjswg=0.0, tpb=0.0, tpbsw=0.0, tpbswg=0.0, tnom=27.0, permod=1.0, dwj=0.0)
HAND_GEO = (1e-6, 1e-12, 1e-12, 3e-6, 3e-6, 2.0)


def P(**over):
    d = dict(HAND)
    d.update(over)
    return JunctionParams(**d)


def G(fw=1e-6, ad=1e-12, as_=1e-12, pd=3e-6, ps=3e-6, m=2.0):
    return DiffusionGeometry(fw, ad, as_, pd, ps, m)


def test_reference_formula_matches_hand_example():
    # 검증자 도구 자체 확인: 기준 식이 8.3 손계산과 같다
    cdb, csb = ref_caps(HAND, HAND_GEO, 3.0, 0.0, 27.0)
    assert rel_close(cdb, 1.4e-15, 1e-12) and rel_close(csb, 2.8e-15, 1e-12)


@pytest.mark.parametrize("over,geo_over,v_db,v_sb,temp,cdb,csb", [
    ({}, {}, 3.0, 0.0, 27.0, 1.4e-15, 2.8e-15),
    ({}, {}, 3.0, -0.5, 27.0, 1.4e-15, 3.5e-15),
    ({"permod": 0.0}, {}, 0.0, 0.0, 27.0, 3.0e-15, 3.0e-15),
    ({"tcj": 1e-3, "tnom": 30.0}, {}, 0.0, 0.0, 27.0, 2.794e-15, 2.794e-15),
    ({}, {"ps": 0.5e-6}, 3.0, 3.0, 27.0, 1.4e-15, 1.2e-15),
    ({}, {"ps": 0.5e-6}, 3.0, 0.0, 27.0, 1.4e-15, 2.3e-15),
    ({}, {}, 3, 0, 27, 1.4e-15, 2.8e-15),   # int 바이어스·온도
], ids=["vdb3", "forward", "permod0", "tcj", "ps_short_rev", "ps_short_zero", "int_args"])
def test_hand_examples(over, geo_over, v_db, v_sb, temp, cdb, csb):
    jc = junction_caps(P(**over), G(**geo_over), v_db, v_sb, temp)
    assert isinstance(jc, JunctionCaps)
    assert isinstance(jc.cdb, float) and isinstance(jc.csb, float)
    assert rel_close(jc.cdb, cdb, 1e-12), (jc.cdb, cdb)
    assert rel_close(jc.csb, csb, 1e-12), (jc.csb, csb)


def test_temperature_factor_clamped_at_zero():
    # 1 + tcj·ΔT = 1 + 0.1·(−20) < 0 -> 바닥 항 0 (max(0, ·))
    jc = junction_caps(P(tcj=0.1), G(), 0.0, 0.0, 7.0)
    assert rel_close(jc.cdb, 2 * (1e-10 * 2e-6 + 2e-10 * 1e-6), 1e-12)
    assert rel_close(jc.csb, jc.cdb, 1e-12)


def test_built_in_potential_temperature_shift():
    # PB(T) = PB − tpb·ΔT: pb 1, tpb 0.01, ΔT 50 -> 0.5 ; v 1.5 -> (1 + 3)^(−0.5) = 0.5 (바닥 항만 있는 경우)
    p = P(cjsws=0.0, cjswd=0.0, cjswgs=0.0, cjswgd=0.0, tpb=0.01)
    jc = junction_caps(p, G(), 1.5, 1.5, 77.0)
    assert rel_close(jc.cdb, 2 * 1e-15 * 0.5, 1e-12)
    assert rel_close(jc.csb, 2 * 1e-15 * 0.5, 1e-12)


def test_negative_sidewall_term_only_dropped_in_reverse_bias():
    # P < Weffcj (permod 1): c0₂ < 0 -- 역바이어스면 0, 영·순바이어스면 그대로 더함(P_eff 를 0 으로 자르지 않는다)
    geo = G(pd=0.2e-6, ps=0.2e-6)
    rev = junction_caps(P(), geo, 1e-9, 1e-9, 27.0)
    zero = junction_caps(P(), geo, 0.0, 0.0, 27.0)
    fwd = junction_caps(P(), geo, -0.4, -0.4, 27.0)
    c1, c2, c3 = 1e-15, 1e-10 * (0.2e-6 - 1e-6), 2e-10 * 1e-6
    assert c2 < 0
    assert rel_close(rev.cdb, 2 * (c1 + c3) * (1 + 1e-9) ** -0.5, 1e-12)
    assert rel_close(zero.cdb, 2 * (c1 + c2 + c3), 1e-12)
    assert rel_close(fwd.cdb, 2 * (c1 + c2 + c3) * (1 + 0.5 * 0.4), 1e-12)
    assert (rev.csb, zero.csb, fwd.csb) == (rev.cdb, zero.cdb, fwd.cdb)


def test_zero_c0_in_reverse_bias_contributes_zero():
    jc = junction_caps(P(cjd=0.0, cjswd=0.0, cjswgd=0.0), G(), 0.7, 0.0, 27.0)
    assert jc.cdb == 0.0
    assert rel_close(jc.csb, 2.8e-15, 1e-12)


def test_dwj_shrinks_gate_sidewall_and_perimeter():
    # Weffcj = 1e-6 − 2·0.1e-6 = 0.8e-6 ; P_eff = 3e-6 − 0.8e-6 = 2.2e-6
    jc = junction_caps(P(dwj=0.1e-6), G(), 0.0, 0.0, 27.0)
    assert rel_close(jc.cdb, 2 * (1e-15 + 1e-10 * 2.2e-6 + 2e-10 * 0.8e-6), 1e-12)
    # 음수 dwj 허용(부호 제한 없음) -- Weffcj > finger_w
    jc = junction_caps(P(dwj=-0.1e-6), G(), 0.0, 0.0, 27.0)
    assert rel_close(jc.cdb, 2 * (1e-15 + 1e-10 * 1.8e-6 + 2e-10 * 1.2e-6), 1e-12)


def test_m_scales_linearly_and_may_be_fractional():
    a = junction_caps(P(), G(m=1.0), 0.3, 0.2, 27.0)
    b = junction_caps(P(), G(m=2.5), 0.3, 0.2, 27.0)
    assert rel_close(b.cdb, 2.5 * a.cdb, 1e-14) and rel_close(b.csb, 2.5 * a.csb, 1e-14)


def _random_params(rng):
    d = {}
    for s in ("s", "d"):
        d["cj" + s] = rng.uniform(1e-4, 2e-3)
        d["cjsw" + s] = rng.uniform(0.0, 2e-10)
        d["cjswg" + s] = rng.uniform(0.0, 4e-10)
        d["mj" + s] = rng.uniform(0.0, 1.0)
        d["mjsw" + s] = rng.uniform(0.0, 1.0)
        d["mjswg" + s] = rng.uniform(0.0, 1.0)
        d["pb" + s] = rng.uniform(0.5, 1.5)
        d["pbsw" + s] = rng.uniform(0.5, 1.5)
        d["pbswg" + s] = rng.uniform(0.5, 1.5)
    for k in ("tcj", "tcjsw", "tcjswg"):
        d[k] = rng.uniform(-5e-3, 5e-3)
    for k in ("tpb", "tpbsw", "tpbswg"):
        d[k] = rng.uniform(0.0, 3e-3)
    d["tnom"] = rng.uniform(20.0, 35.0)
    d["permod"] = float(rng.choice((0, 1)))
    d["dwj"] = rng.uniform(-2e-8, 5e-8)
    return d


def test_asymmetric_random_against_reference():
    # drain 쪽은 *d·ad·pd·v_db, source 쪽은 *s·as·ps·v_sb 만 쓴다 -- 쪽마다 다른 값으로 섞임을 잡는다
    rng = random.Random(910)
    for _ in range(300):
        p = _random_params(rng)
        fw = rng.uniform(0.3e-6, 5e-6)
        geo = (fw, rng.uniform(0, 3e-12), rng.uniform(0, 3e-12), rng.uniform(0, 8e-6), rng.uniform(0, 8e-6),
               rng.choice((1.0, 2.0, 3.5, 8.0)))
        v_db, v_sb = rng.uniform(-0.4, 1.8), rng.uniform(-0.4, 1.8)
        temp = rng.uniform(-40.0, 125.0)
        exp = ref_caps(p, geo, v_db, v_sb, temp)
        got = junction_caps(JunctionParams(**p), DiffusionGeometry(*geo), v_db, v_sb, temp)
        assert rel_close(got.cdb, exp[0], 1e-12) or abs(got.cdb - exp[0]) < 1e-30, (p, geo, v_db, v_sb, temp)
        assert rel_close(got.csb, exp[1], 1e-12) or abs(got.csb - exp[1]) < 1e-30, (p, geo, v_db, v_sb, temp)


# ---------------------------------------------------------------- 8.1·8.2 입력 검사

PARAM_REJECTS = [
    ({"cjs": True}, TypeError),
    ({"permod": False}, TypeError),
    ({"cjd": "1e-3"}, TypeError),
    ({"tnom": None}, TypeError),
    ({"mjs": float("nan")}, ValueError),
    ({"pbd": float("inf")}, ValueError),
    ({"tcj": -float("inf")}, ValueError),
    ({"permod": 0.5}, ValueError),
    ({"permod": 2.0}, ValueError),
    ({"pbs": 0.0}, ValueError),
    ({"pbswgd": -1.0}, ValueError),
    ({"cjs": -1e-3}, ValueError),
    ({"cjswgd": -1e-10}, ValueError),
    ({"mjsws": -0.1}, ValueError),
    ({"mjd": -1e-9}, ValueError),
]


@pytest.mark.parametrize("over,exc", PARAM_REJECTS, ids=["%s=%r" % next(iter(o.items())) for o, _ in PARAM_REJECTS])
def test_params_rejected(over, exc):
    with pytest.raises(exc):
        P(**over)


def test_params_normalised_to_float_and_frozen():
    p = P(permod=1, tnom=27, cjs=0, tcj=-2e-3, dwj=-1e-8)   # int·0·음수 tc·음수 dwj 허용
    assert all(type(getattr(p, f)) is float for f in FIELDS)
    assert p.permod == 1.0 and p.cjs == 0.0
    assert tuple(f.name for f in dataclasses.fields(JunctionParams)) == FIELDS
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.cjs = 1.0
    require_immutable(p)
    assert fp_of(p) == fp_of(P(permod=1, tnom=27, cjs=0, tcj=-2e-3, dwj=-1e-8))
    assert fp_of(p) != fp_of(P(permod=1, tnom=27, cjs=0, tcj=-2e-3, dwj=-2e-8))


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


CALL_REJECTS = [
    ("params_dict", lambda: junction_caps(HAND, G(), 0.0, 0.0, 27.0), TypeError),
    ("geo_tuple", lambda: junction_caps(P(), HAND_GEO, 0.0, 0.0, 27.0), TypeError),
    ("swapped", lambda: junction_caps(G(), P(), 0.0, 0.0, 27.0), TypeError),
    ("vdb_bool", lambda: junction_caps(P(), G(), True, 0.0, 27.0), TypeError),
    ("vsb_str", lambda: junction_caps(P(), G(), 0.0, "0", 27.0), TypeError),
    ("temp_none", lambda: junction_caps(P(), G(), 0.0, 0.0, None), TypeError),
    ("vdb_nan", lambda: junction_caps(P(), G(), float("nan"), 0.0, 27.0), ValueError),
    ("vsb_inf", lambda: junction_caps(P(), G(), 0.0, float("inf"), 27.0), ValueError),
    ("temp_ninf", lambda: junction_caps(P(), G(), 0.0, 0.0, float("-inf")), ValueError),
    # PB(T) ≤ 0: 1 − 0.1·10 = 0 (바닥·양쪽), 1 − 0.1·20 < 0, drain gate 측벽만 0.5 − 0.1·5 = 0
    ("pb_T_zero", lambda: junction_caps(P(tpb=0.1), G(), 0.0, 0.0, 37.0), ValueError),
    ("pb_T_neg", lambda: junction_caps(P(tpb=0.1), G(), 0.0, 0.0, 47.0), ValueError),
    ("pbswgd_T_zero", lambda: junction_caps(P(tpbswg=0.1, pbswgd=0.5, pbswgs=2.0), G(), 0.0, 0.0, 32.0), ValueError),
    # Weffcj = finger_w − 2·dwj ≤ 0
    ("weffcj_zero", lambda: junction_caps(P(dwj=0.5e-6), G(), 0.0, 0.0, 27.0), ValueError),
    ("weffcj_neg", lambda: junction_caps(P(dwj=0.6e-6), G(), 0.0, 0.0, 27.0), ValueError),
]


@pytest.mark.parametrize("label,call,exc", CALL_REJECTS, ids=[c[0] for c in CALL_REJECTS])
def test_call_rejected(label, call, exc):
    with pytest.raises(exc):
        call()


def test_pb_just_above_zero_accepted():
    jc = junction_caps(P(tpb=0.1), G(), 0.5, 0.5, 36.0)   # PB(T) = 0.1 > 0
    exp = ref_caps(dict(HAND, tpb=0.1), HAND_GEO, 0.5, 0.5, 36.0)
    assert rel_close(jc.cdb, exp[0], 1e-12) and rel_close(jc.csb, exp[1], 1e-12)


# ---------------------------------------------------------------- sky130 실데이터 (8.3 끝, core 9.4 표)

# core CONTRACT 9.4 표(drain 이름 = source 쪽 값)
SKY_TABLE = {
    "nmos": dict(cjs=0.001339749237, cjsws=3.67354204e-11, cjswgs=2.38232788e-10, mjs=0.44, mjsws=0.0009, mjswgs=0.8,
                 pbs=0.729, pbsws=0.2, pbswgs=0.95578, tcj=0.000792, tcjsw=1e-05, tcjswg=0.0, tpb=0.0012287, tpbsw=0.0,
                 tpbswg=0.0, tnom=30.0, permod=1.0, dwj=0.0),
    "pmos": dict(cjs=0.0007380194454, cjsws=9.888892e-11, cjswgs=2.39155046e-10, mjs=0.34629, mjsws=0.29781,
                 mjswgs=0.9274, pbs=0.6587, pbsws=0.7418, pbswgs=1.4338, tcj=0.0012407, tcjsw=0.00037357, tcjswg=2e-12,
                 tpb=0.0020386, tpbsw=0.001246, tpbswg=0.0, tnom=30.0, permod=1.0, dwj=0.0),
}
_D2S = {"cjd": "cjs", "cjswd": "cjsws", "cjswgd": "cjswgs", "mjd": "mjs", "mjswd": "mjsws", "mjswgd": "mjswgs",
        "pbd": "pbs", "pbswd": "pbsws", "pbswgd": "pbswgs"}


def sky_ref_params(kind):
    return {f: SKY_TABLE[kind][_D2S.get(f, f)] for f in FIELDS}


@pytest.fixture(scope="module")
def decls():
    if not _SKY_PRESENT:
        pytest.skip("sky130 원본 없음")
    memo = BoundedLRU(5)
    return read_pdk_decl(str(PDK_DECL), memo), read_pdk_decl(str(LUT_RULE_DECL), memo)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_from_pdk_decl_sky130(decls, kind):
    pdk, _ = decls
    p = JunctionParams.from_pdk_decl(pdk, kind)
    assert isinstance(p, JunctionParams)
    ref = sky_ref_params(kind)
    for f in FIELDS:
        assert getattr(p, f) == pdk.value("junction_%s_%s" % (kind, f)), f
        assert rel_close(getattr(p, f), ref[f], 1e-12) or getattr(p, f) == ref[f] == 0.0, (f, getattr(p, f), ref[f])
    assert p.cjd == p.cjs and p.tnom == 30.0 and p.permod == 1.0 and p.dwj == 0.0
    if kind == "nmos":
        assert p.cjs == 0.001339749237


def test_from_pdk_decl_unknown_kind_and_wrong_decl(decls):
    pdk, rule = decls
    for d, kind in ((pdk, "nfet"), (pdk, "NMOS"), (rule, "nmos")):
        with pytest.raises(SchemaRejectedError) as ei:
            JunctionParams.from_pdk_decl(d, kind)
        assert reason(ei) == "pdk_quantity_undeclared", kind


def test_from_lut_rule_sky130(decls):
    pdk, rule = decls
    g = DiffusionGeometry.from_lut_rule(rule, 2e-6, 3)
    assert isinstance(g, DiffusionGeometry)
    assert g.finger_w_m == 2e-6 and g.m == 3.0
    assert g.ad_m2 == rule.value("lut_diffusion_ad_per_w_m") * 2e-6
    assert g.as_m2 == rule.value("lut_diffusion_as_per_w_m") * 2e-6
    assert g.pd_m == 2e-6 + rule.value("lut_diffusion_pd_extra_m")
    assert g.ps_m == 2e-6 + rule.value("lut_diffusion_ps_extra_m")
    assert rel_close(g.ad_m2, 1e-12, 1e-12) and rel_close(g.as_m2, 1e-12, 1e-12)
    assert rel_close(g.pd_m, 4e-6, 1e-12) and rel_close(g.ps_m, 4e-6, 1e-12)
    with pytest.raises(SchemaRejectedError) as ei:
        DiffusionGeometry.from_lut_rule(pdk, 2e-6, 3)
    assert reason(ei) == "pdk_quantity_undeclared"
    with pytest.raises(ValueError):
        DiffusionGeometry.from_lut_rule(rule, 0.0, 3)
    with pytest.raises(ValueError):
        DiffusionGeometry.from_lut_rule(rule, 2e-6, 0)


# 8.4 예(L 0.5 µm, LUT 규칙 finger 2 µm x 3) -- 계약 숫자(11 자리)
@pytest.mark.parametrize("kind,v_db,v_sb,cdb,csb", [
    ("nmos", 0.3, 0.1, 4.8168933609e-15, 5.3305595669e-15),
    ("pmos", 0.9, 0.4, 3.0214419372e-15, 3.5374819305e-15),
])
def test_contract_84_examples(decls, kind, v_db, v_sb, cdb, csb):
    pdk, rule = decls
    jc = junction_caps(JunctionParams.from_pdk_decl(pdk, kind), DiffusionGeometry.from_lut_rule(rule, 2e-6, 3),
                       v_db, v_sb, 27.0)
    assert rel_close(jc.cdb, cdb, 1e-10), (jc.cdb, cdb)
    assert rel_close(jc.csb, csb, 1e-10), (jc.csb, csb)


def test_consumer_call_85_chain_and_memo():
    # 8.5 소비자 호출 그대로: 두 선언 같은 memo(원본 5개) -> kind 마다 params, 첫 사이징점 기하 -> junction_caps
    if not _SKY_PRESENT:
        pytest.skip("sky130 원본 없음")
    memo = BoundedLRU(5)
    w_m, W, vds, vsb = 5e-6, 17.5e-6, 0.6, 0.25   # 슬라이스 폭·소자 폭(m = W / w_m = 3.5)
    for _ in range(2):
        pdk = read_pdk_decl(str(PDK_DECL), memo)
        lut_rule = read_pdk_decl(str(LUT_RULE_DECL), memo)
        for kind in ("nmos", "pmos"):
            params = JunctionParams.from_pdk_decl(pdk, kind)
            geometry = DiffusionGeometry.from_lut_rule(lut_rule, w_m, W / w_m)
            jc = junction_caps(params, geometry, vds + vsb, vsb, 27.0)
            ad = 5e-7 * w_m
            exp = ref_caps(sky_ref_params(kind), (w_m, ad, ad, w_m + 2e-6, w_m + 2e-6, W / w_m), vds + vsb, vsb, 27.0)
            assert rel_close(jc.cdb, exp[0], 1e-12) and rel_close(jc.csb, exp[1], 1e-12)
            assert fp_of(params) == fp_of(JunctionParams.from_pdk_decl(pdk, kind))
    assert (memo.stats().misses, memo.stats().hits) == (5, 5)


# ---------------------------------------------------------------- 8.4 격자 vs 독립 기준 식 (ngspice 없이)

GEOMS = {
    "lut_2u_x3": (2e-6, 1e-12, 1e-12, 4e-6, 4e-6, 3.0),
    "lut_042u_x8": (0.42e-6, 0.21e-12, 0.21e-12, 2.42e-6, 2.42e-6, 8.0),
    "euler_1u_x4": (1e-6, 0.29e-12, 0.145e-12, 1.58e-6, 0.79e-6, 4.0),
}
BIASES = ((0.0, 0.0), (0.3, 0.1), (0.9, 0.4), (1.8, 1.0), (-0.2, -0.1))


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sky130_grid_against_reference_formula(decls, kind):
    pdk, _ = decls
    params = JunctionParams.from_pdk_decl(pdk, kind)
    ref = sky_ref_params(kind)
    for name, geo in GEOMS.items():
        for v_db, v_sb in BIASES:
            for temp in (27.0, -40.0, 85.0):
                jc = junction_caps(params, DiffusionGeometry(*geo), v_db, v_sb, temp)
                exp = ref_caps(ref, geo, v_db, v_sb, temp)
                assert rel_close(jc.cdb, exp[0], 1e-12) and rel_close(jc.csb, exp[1], 1e-12), (name, v_db, v_sb, temp)


# ---------------------------------------------------------------- 8.4 ngspice 실측 대조

def run_ngspice(tmp_dir, cell, L_um, temp_c, pts):
    """pts: [(geo, v_db, v_sb)] -> [(capbd, capbs)] -- 단일 소자 X 줄(l w ad as pd ps m), .op, 12 자리 출력."""
    pol = 1 if cell.startswith("nfet") else -1
    root = _PDK["pdk_root"].replace("/", "\\") + "\\sky130_fd_pr"
    lines = ["* junction cap check %s L=%g T=%g" % (cell, L_um, temp_c)]
    if cell.startswith("pfet"):
        lines.append('.include "%s\\models\\parameters\\lod.spice"' % root)
    lines.append('.include "%s\\cells\\%s\\sky130_fd_pr__%s__tt.pm3.spice"' % (root, cell, cell))
    lines.append('.include "%s\\cells\\%s\\sky130_fd_pr__%s__mismatch.corner.spice"' % (root, cell, cell))
    lines.append(".option temp=%.12g" % temp_c)
    for i, ((fw, ad, as_, pd, ps, m), v_db, v_sb) in enumerate(pts):
        lines += ["vd%d d%d 0 %.12g" % (i, i, pol * v_db), "vs%d s%d 0 %.12g" % (i, i, pol * v_sb),
                  "vg%d g%d 0 %.12g" % (i, i, pol * (v_sb + 0.9)),
                  "x%d d%d g%d s%d 0 sky130_fd_pr__%s l=%gu w=%.12g ad=%.12g as=%.12g pd=%.12g ps=%.12g m=%.12g"
                  % (i, i, i, i, cell, L_um, fw, ad, as_, pd, ps, m)]
    lines += [".control", "set numdgt=12", "op"]
    lines += ["print @m.x%d.msky130_fd_pr__%s[capbd] @m.x%d.msky130_fd_pr__%s[capbs]" % (i, cell, i, cell)
              for i in range(len(pts))]
    lines += ["quit", ".endc", ".end"]
    net = Path(tmp_dir) / ("jc_%s_%g_%g.cir" % (cell, L_um, temp_c))
    net.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run([str(NGSPICE), "-b", str(net)], capture_output=True, text=True, cwd=str(tmp_dir), timeout=120)
    vals = re.findall(r"\[cap(b[ds])\]\s*=\s*([-+0-9.eE]+)", r.stdout)
    assert len(vals) == 2 * len(pts), r.stdout[-2000:] + r.stderr[-2000:]
    assert [v[0] for v in vals] == ["bd", "bs"] * len(pts)
    nums = [float(v[1]) for v in vals]
    return [(nums[2 * i], nums[2 * i + 1]) for i in range(len(pts))]


def _ps_short(geo):
    return geo[4] < geo[0]


@needs_ngspice
@pytest.mark.parametrize("kind,cell", [("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")])
@pytest.mark.parametrize("L_um", [0.15, 4.0])
def test_against_ngspice_27c(tmp_path, decls, kind, cell, L_um):
    # 8.4 격자: 기하 3 x 바이어스 5, L 두 bin -- 8.2 불연속 점(ps < finger_w 이고 v_sb 정확히 0)은 뺀다
    pdk, _ = decls
    params = JunctionParams.from_pdk_decl(pdk, kind)
    pts = [(geo, v_db, v_sb) for geo in GEOMS.values() for v_db, v_sb in BIASES
           if not (_ps_short(geo) and v_sb == 0.0)]
    assert len(pts) == 14
    ng = run_ngspice(tmp_path, cell, L_um, 27.0, pts)
    for (geo, v_db, v_sb), (cbd, cbs) in zip(pts, ng):
        jc = junction_caps(params, DiffusionGeometry(*geo), v_db, v_sb, 27.0)
        assert rel_close(jc.cdb, cbd, 1e-9), (geo, v_db, v_sb, jc.cdb, cbd)
        assert rel_close(jc.csb, cbs, 1e-9), (geo, v_db, v_sb, jc.csb, cbs)


@needs_ngspice
@pytest.mark.parametrize("kind,cell", [("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")])
@pytest.mark.parametrize("temp_c", [-40.0, 85.0])
def test_against_ngspice_temperature_correction(tmp_path, decls, kind, cell, temp_c):
    # 8.2-2 온도 보정(ΔT = temp − tnom 30): 역바이어스 점만(순바이어스는 body 저항 전류가 노드 전압을 옮긴다)
    pdk, _ = decls
    params = JunctionParams.from_pdk_decl(pdk, kind)
    pts = [(geo, v_db, v_sb) for geo in GEOMS.values() for v_db, v_sb in BIASES if v_db > 0 and v_sb > 0]
    ng = run_ngspice(tmp_path, cell, 0.5, temp_c, pts)
    for (geo, v_db, v_sb), (cbd, cbs) in zip(pts, ng):
        jc = junction_caps(params, DiffusionGeometry(*geo), v_db, v_sb, temp_c)
        assert rel_close(jc.cdb, cbd, 1e-9), (geo, v_db, v_sb, temp_c, jc.cdb, cbd)
        assert rel_close(jc.csb, cbs, 1e-9), (geo, v_db, v_sb, temp_c, jc.csb, cbs)
    # 온도 보정이 실제로 값을 바꾼다(27 °C 값과 다름)
    jc27 = junction_caps(params, DiffusionGeometry(*pts[0][0]), pts[0][1], pts[0][2], 27.0)
    assert not rel_close(jc27.cdb, ng[0][0], 1e-6)


# ---------------------------------------------------------------- 8.2 알려진 불연속(계약 문장 그대로)

EULER = GEOMS["euler_1u_x4"]


def test_documented_discontinuity_engine_takes_v0_branch(decls):
    # pmos Euler 꼴(ps 0.79 µm < finger_w 1 µm, permod 1), v_sb = 0: 엔진 = v = 0 가지 1.3001046135e-15,
    # ngspice(잡음으로 역방향 가지) = 1.3830782127e-15, 차 6.0 %.
    pdk, _ = decls
    params = JunctionParams.from_pdk_decl(pdk, "pmos")
    at0 = junction_caps(params, DiffusionGeometry(*EULER), 0.0, 0.0, 27.0).csb
    assert rel_close(at0, 1.3001046135e-15, 1e-10), at0
    rev_limit = junction_caps(params, DiffusionGeometry(*EULER), 0.0, 1e-15, 27.0).csb
    assert rel_close(rev_limit, 1.3830782127e-15, 1e-10), rev_limit
    assert abs(1.0 - at0 / rev_limit - 0.060) < 0.0005
    # 기준 식도 같은 두 가지(음의 측벽 항: 역방향 0, v = 0 이면 더함)
    ref = sky_ref_params("pmos")
    assert rel_close(ref_caps(ref, EULER, 0.0, 0.0, 27.0)[1], at0, 1e-12)
    assert rel_close(ref_caps(ref, EULER, 0.0, 1e-15, 27.0)[1], rev_limit, 1e-12)


def test_no_discontinuity_when_perimeter_includes_gate_edge(decls):
    # 8.2: permod 1 에서 ps ≥ finger_w 면 v = 0 양쪽이 연속
    pdk, _ = decls
    for kind in ("nmos", "pmos"):
        params = JunctionParams.from_pdk_decl(pdk, kind)
        for geo in (GEOMS["lut_2u_x3"], GEOMS["lut_042u_x8"]):
            a = junction_caps(params, DiffusionGeometry(*geo), 0.0, 0.0, 27.0)
            b = junction_caps(params, DiffusionGeometry(*geo), 1e-12, 1e-12, 27.0)
            c = junction_caps(params, DiffusionGeometry(*geo), -1e-12, -1e-12, 27.0)
            assert rel_close(a.csb, b.csb, 1e-9) and rel_close(a.csb, c.csb, 1e-9)
            assert rel_close(a.cdb, b.cdb, 1e-9)


@needs_ngspice
def test_documented_discontinuity_ngspice_reverse_branch_matches_engine_off_zero(tmp_path, decls):
    # 불연속 점 바로 옆(v_sb = +1 nV)에서는 ngspice 와 엔진이 같은 역방향 가지 -- 차이는 정확히 0 에서만
    pdk, _ = decls
    params = JunctionParams.from_pdk_decl(pdk, "pmos")
    ((cbd, cbs),) = run_ngspice(tmp_path, "pfet_01v8", 0.5, 27.0, [(EULER, 1e-9, 1e-9)])
    jc = junction_caps(params, DiffusionGeometry(*EULER), 1e-9, 1e-9, 27.0)
    assert rel_close(jc.csb, cbs, 1e-9) and rel_close(jc.cdb, cbd, 1e-9)
    assert rel_close(cbs, 1.3830782127e-15, 1e-8)


# ---------------------------------------------------------------- 일반성: 가상 PDK 모델 카드·생성 규칙 (코드 변경 없이)

TOY_CARD_PARAMS = dict(cjs=1.1e-3, cjd=0.9e-3, cjsws=1.2e-10, cjswd=0.8e-10, cjswgs=2.5e-10, cjswgd=1.5e-10,
                       mjs=0.45, mjd=0.35, mjsws=0.2, mjswd=0.3, mjswgs=0.7, mjswgd=0.6,
                       pbs=0.8, pbd=0.7, pbsws=0.9, pbswd=0.6, pbswgs=1.1, pbswgd=1.2,
                       tcj=1e-3, tcjsw=2e-4, tcjswg=3e-4, tpb=1e-3, tpbsw=2e-3, tpbswg=5e-4,
                       tnom=25.0, permod=0.0, dwj=2e-8)


def _toy_card_text():
    # 두 bin, 접합 키는 bin 공통, 값은 SPICE 배율 글자(m·p·n) -- 단위 표가 SI 로 바꾼다; vth0 은 bin 마다 다름(쓰지 않음)
    def spice(k, v):
        if k.startswith("cjsw"):
            return "%s = %.6gp" % (k, v * 1e12)
        if k.startswith("cj"):
            return "%s = %.6gm" % (k, v * 1e3)
        if k == "dwj":
            return "%s = %.6gn" % (k, v * 1e9)
        return "%s = %.12g" % (k, v)
    body = "\n".join("+ " + spice(k, v) for k, v in TOY_CARD_PARAMS.items())
    return ("* toy card\n.model tx_n.0 nmos level = 54 vth0 = 0.3\n" + body +
            "\n.model tx_n.1 nmos level = 54 vth0 = 0.35\n" + body + "\n")


def _toy_decls(root):
    (root / "m").mkdir(parents=True)
    card = root / "m" / "tx.spice"
    card.write_bytes(_toy_card_text().encode("utf-8"))
    gen = root / "gen.py"
    gen.write_bytes(b'BASE = "xd d g s b tx w=2u ad=1p as=0.6p pd=4u ps=3u"\n')
    pdk = {"schema": "gmid_pdk_decl/1", "pdk": "toyjc", "pdk_root": root.as_posix(),
           "sources": {"card": {"path": "m/tx.spice", "sha256": _sha256(card), "format": "spice_model_card",
                                "encoding": "utf-8", "model_pattern": r"tx_n\.[0-9]+",
                                "units_m": {"": 1.0, "m": 1e-3, "p": 1e-12, "n": 1e-9}}},
           "quantities": {"junction_nmos_%s" % f: {"source": "card", "expression": f, "basis": "toy"} for f in FIELDS}}
    rule = {"schema": "gmid_pdk_decl/1", "pdk": "toyjc", "pdk_root": "unused",
            "sources": {"gen": {"path": "gen.py", "base": "decl_dir", "newline": "lf", "sha256": _sha256(gen),
                                "format": "spice_instance_line", "encoding": "utf-8",
                                "line_pattern": r'^BASE\s*=\s*"([^"]*)"', "units_m": {"u": 1e-6, "p": 1e-12}}},
           "quantities": {"lut_diffusion_ad_per_w_m": {"source": "gen", "expression": "ad / w", "basis": "t"},
                          "lut_diffusion_as_per_w_m": {"source": "gen", "expression": "as / w", "basis": "t"},
                          "lut_diffusion_pd_extra_m": {"source": "gen", "expression": "pd - w", "basis": "t"},
                          "lut_diffusion_ps_extra_m": {"source": "gen", "expression": "ps - w", "basis": "t"}}}
    pp, rp = root / "pdk.json", root / "rule.json"
    pp.write_text(json.dumps(pdk), encoding="utf-8")
    rp.write_text(json.dumps(rule), encoding="utf-8")
    return str(pp), str(rp)


def test_generality_toy_pdk_without_code_change(tmp_path):
    pp, rp = _toy_decls(tmp_path / "toy")
    memo = BoundedLRU(2)
    pdk, rule = read_pdk_decl(pp, memo), read_pdk_decl(rp, memo)
    params = JunctionParams.from_pdk_decl(pdk, "nmos")
    for f in FIELDS:
        assert rel_close(getattr(params, f), TOY_CARD_PARAMS[f], 1e-12) or getattr(params, f) == TOY_CARD_PARAMS[f], f
    with pytest.raises(SchemaRejectedError) as ei:
        JunctionParams.from_pdk_decl(pdk, "pmos")   # 선언에 없는 kind
    assert reason(ei) == "pdk_quantity_undeclared"
    geo = DiffusionGeometry.from_lut_rule(rule, 1e-6, 2.5)
    exp_geo = (1e-6, 0.5e-6 * 1e-6, 0.3e-6 * 1e-6, 1e-6 + 2e-6, 1e-6 + 1e-6, 2.5)
    for got, exp in zip((geo.finger_w_m, geo.ad_m2, geo.as_m2, geo.pd_m, geo.ps_m, geo.m), exp_geo):
        assert rel_close(got, exp, 1e-12), (got, exp)
    for v_db, v_sb, temp in ((0.6, 0.2, 60.0), (0.0, 0.0, 25.0), (-0.1, 0.4, 0.0)):
        jc = junction_caps(params, geo, v_db, v_sb, temp)
        exp = ref_caps(TOY_CARD_PARAMS, exp_geo, v_db, v_sb, temp)
        assert rel_close(jc.cdb, exp[0], 1e-11) and rel_close(jc.csb, exp[1], 1e-11), (v_db, v_sb, temp)
