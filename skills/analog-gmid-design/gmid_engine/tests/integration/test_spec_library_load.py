"""9회로 교차 -- library 의 `<회로>.sizing_spec.json` 을 `load_sizing_spec` 에 실제로 건다 (authoring SPEC_CONTRACT 5절).

기대값: 계약 5절 표(제약 수·판정 수·pending 수, ID 별 합계)와 spec/topology JSON 직접 집계. 피검 함수로 기대값을 만들지 않는다.
이름표 = 5절 '픽스처 이름표'(단위·domain 은 이 test 가 정함).
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import pytest

from gmid_engine.authoring import BETA_DECLARED, BETA_UNITY, SenseDecl, ViewDecl, load_sizing_spec, load_topology

from gmid_engine.core import MetricSignature as M

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"

CATALOG = {  # 어휘: SPEC_CONTRACT 4절·6절 9번, core CONTRACT 0절
    "gain_ss_db": M("db", "ss", "transfer"),
    "ugf_ss_hz": M("hz", "ss", "transfer"),
    "gbw_ss_hz": M("hz", "ss", "transfer"),
    "pm_ss_deg": M("deg", "ss", "loop"),
    "pm_cm_ss_deg": M("deg", "ss", "cm_loop"),  # [CM 2026-10-08] SPEC_CONTRACT 5절 픽스처 이름표 갱신
    "parasitic_pm_ss_deg": M("deg", "ss", "transfer"),
    "rout_ss_ohm": M("ohm", "ss", "output_port"),
    "ratio_ss_db": M("db", "ss", "ratio"),
    "mismatch_sigma_mv": M("mv", "dc", None),
    "mirror_ratio_error_mv": M("mv", "dc", None),
    "power_dc_w": M("w", "dc", None),
    "area_search_m2": M("m2", "geom", None),
    "supply_current_dc": M("amp", "dc", None, "power"),
    "area_layout_m2": M("m2", "geom", None, "area"),
}

# 5절 표: 회로 -> (제약 수, 판정 수, pending 표지 수). 파일럿 pending 은 SP-10 해소(사용자 2026-10-07 "파일럿 CL1·CL2가
# 각각 1 pF", 커밋 0bc22fe) 뒤 13, CI-10 해소(사용자 2026-10-08 "5번도 네 의견에 동의해", 커밋 3a38275 -- feedback 표지 CI-10
# 1 과 pm_ss_deg 뷰 표지 MOD5 1 삭제) 뒤 11 = JSON 표지 직접 집계(MOD5 5 + SP-2·CI-15·CI-18·PA-1·PA-2·AC-3 각 1) = 5절 표 11.
TABLE = {
    "common_gate_amplifier": (0, 0, 6),
    # [CM 2026-10-08] 5절 표 그대로 9(6) / 11: pm_cm_ss_deg >= 60 user_spec 1건 추가, pending 13 -> 11 = CI-10 해소(feedback {Cf1, Cf2},
    # 사용자 2026-10-08 "5번은 네 의견에 동의해", 커밋 3a38275) + pm_ss_deg 의 view MOD5 표지 삭제(loop 뷰 유도) -- JSON 직접 집계와 같음.
    "current_reuse_telescopic_ota": (9, 6, 11),
    "folded_cascode": (0, 0, 7),
    "ngcc_3stage_ff": (3, 2, 7),
    "nmcnr_amplifier": (2, 2, 6),
    "pushpull_follower_buffer": (1, 1, 5),
    "sf_pushpull_output_opamp": (3, 3, 6),
    "two_stage_ota": (2, 1, 7),
    "two_stage_ota_sf": (3, 2, 6),
}
# 5절 ID 합계: SP-10 2 가 빠지고(65 -> 63), CI-10 해소로 CI-10 1·MOD5 1(파일럿 pm_ss_deg 뷰)이 빠진다(63 -> 61, MOD5 7 -> 6 =
# 파일럿 뷰 4·metric 1 + ngcc metric 1). 5절 문장 '남은 표지 61개' 와 JSON 직접 집계가 같음.
ID_TOTALS = {"AC-3": 9, "PA-1": 9, "PA-2": 9, "CI-15": 9, "CI-18": 9, "SP-2": 7, "MOD5": 6, "SP-3": 2,
             "CI-17": 1}
ID_TOTAL_SUM = 61  # oracle (d): SPEC_CONTRACT 5절 '남은 표지 61개'(커밋 3a38275)
PILOT = "current_reuse_telescopic_ota"
SP10_ELEMENTS = ("CL1", "CL2")
SP10_FARAD = 1e-12  # 사용자 2026-10-07 "파일럿 CL1·CL2가 각각 1 pF"


def _spec(name):
    return json.loads((LIBRARY / (name + ".sizing_spec.json")).read_text(encoding="utf-8"))


def _load(name):
    topo = load_topology(str(LIBRARY / (name + ".topology.json")))
    return load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), topo, CATALOG)


def _markers(obj):
    """JSON 직접 집계: 주석 밖 키가 pending 하나인 객체의 ID."""
    if isinstance(obj, dict):
        keys = [k for k in obj if not k.startswith("_")]
        if keys == ["pending"]:
            return [obj["pending"]]
        return [x for v in obj.values() for x in _markers(v)]
    if isinstance(obj, list):
        return [x for v in obj for x in _markers(v)]
    return []


def _judged_from_json(name, metric_or_key, seen=()):
    """JSON 직접 집계로 판정 여부: user_spec True, pending_spice False, reference 는 대상 따라감, metric 결정 대기 False."""
    raw = _spec(name)["human"]
    cons = [c for c in raw["constraints"] if c.get("metric") == metric_or_key]
    if not cons:  # 보상 목표 등 판정 없는 대상
        return True
    return _judged_of(name, cons[0], seen)


def _judged_of(name, c, seen=()):
    if not isinstance(c["metric"], str):
        return False
    kind = c["source"]["kind"]
    if kind == "user_spec":
        return True
    if kind == "pending_spice":
        return False
    if "value_from_constraint" in c:
        return _judged_from_json(name, c["value_from_constraint"], seen + (name,))
    circuit, target = c["value_from_file"].split("#")
    return _judged_from_json(circuit, target, seen + (name,))


def test_library_has_nine_specs():
    names = sorted(p.name[: -len(".sizing_spec.json")] for p in LIBRARY.glob("*.sizing_spec.json"))
    assert names == sorted(TABLE)


@pytest.mark.parametrize("name", sorted(TABLE))
def test_spec_loads_and_matches_json(name):
    doc = _load(name)
    raw = _spec(name)
    assert doc.circuit == raw["meta"]["circuit"] == name
    assert doc.supplies_v == tuple(sorted((k, float(v)) for k, v in raw["human"]["supplies_v"]["values"].items()))
    topo = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    assert {k for k, _ in doc.supplies_v} == set(topo["supply_nets"])
    assert [e.name for e in doc.element_values] == sorted(k for k in raw["human"]["element_values"] if not k.startswith("_"))
    assert {e.name for e in doc.element_values} == {e["name"] for e in topo.get("passive_elements", []) + topo.get("ideal_sources", [])}
    # 제약 수·판정 수 (JSON 집계 + 5절 표)
    n_cons, n_judged, n_pending = TABLE[name]
    assert len(doc.constraints) == len(raw["human"]["constraints"]) == n_cons
    want_judged = sum(_judged_of(name, c) for c in raw["human"]["constraints"])
    assert want_judged == n_judged
    assert [c.judged for c in doc.constraints] == [_judged_of(name, c) for c in raw["human"]["constraints"]]
    assert len(doc.judged_constraints) == n_judged


@pytest.mark.parametrize("name", sorted(TABLE))
def test_remaining_pending_equals_json_markers(name):
    doc = _load(name)
    want = sorted(_markers(_spec(name)))
    assert sorted(p.decision for p in doc.pending) == want
    assert len(want) == TABLE[name][2]


def test_pending_id_totals():
    json_total = Counter(x for name in TABLE for x in _markers(_spec(name)))
    doc_total = Counter(p.decision for name in TABLE for p in _load(name).pending)
    assert json_total == doc_total
    assert dict(json_total) == ID_TOTALS
    assert sum(ID_TOTALS.values()) == ID_TOTAL_SUM


def test_sp10_resolved_pilot_load_caps():
    """SP-10 해소: 파일럿 CL1·CL2 는 결정 대기가 아니라 각각 1e-12 F user_spec 값(SPEC_CONTRACT 1절 출처 표·2절 element_value_key
    capacitor -> value_farad). 기대값은 사용자 결정 문장 + JSON 직접 읽기."""
    raw = _spec(PILOT)["human"]["element_values"]
    for name in SP10_ELEMENTS:
        assert "pending" not in raw[name]
        assert raw[name]["value_farad"] == SP10_FARAD
        assert raw[name]["source"]["kind"] == "user_spec"
    doc = _load(PILOT)
    got = {e.name: e for e in doc.element_values}
    for name in SP10_ELEMENTS:
        assert (got[name].mode, got[name].value_key, got[name].value) == ("value", "value_farad", SP10_FARAD)
    assert "SP-10" not in {p.decision for n in TABLE for p in _load(n).pending}


@pytest.mark.parametrize("name", sorted(TABLE))
def test_spec_fp_deterministic(name):
    assert _load(name).spec_fp == _load(name).spec_fp


def test_cross_file_reference_value():
    """two_stage_ota_sf 의 value_from_file 참조가 two_stage_ota JSON 값으로 해석된다."""
    doc = _load("two_stage_ota_sf")
    base = _spec("two_stage_ota")["human"]
    gain = [c for c in doc.constraints if c.metric == "gain_ss_db"][0]
    assert gain.value == [c for c in base["constraints"] if c["metric"] == "gain_ss_db"][0]["value"]
    gbw = dict(doc.compensation_targets)["gbw_target_hz"]
    assert gbw.value == base["compensation_targets"]["gbw_target_hz"]["value"]


def test_every_spec_meta_fp_matches_topology():
    for name in TABLE:
        topo = load_topology(str(LIBRARY / (name + ".topology.json")))
        assert _spec(name)["meta"]["topology_fp"] == topo.connectivity_fp, name


# ---------------------------------------------------------------- [2026-10-08] search.theta_bounds (사용자 결정 8·9·10)
# oracle (d) 사용자 결정 문장(_drafts/user_decisions.md 2026-10-08):
#  8번 "θ 저항 범위: current_reuse R1·R2(CMFB 공통모드 감지) [10 kOhm, 10 MOhm], sf_pushpull R1a~c(자기바이어스 캐스코드) [1 kOhm, 1 MOhm]"
#  10번 "θ 커패시터 범위 [0.1 pF, 10 pF]: ... spec mode engine 인 커패시터 전부"
#  9번 "J7 영점 상쇄 규칙(R = 1/Σgm) ... 현 매칭 확정: two_stage Rz->M6, nmcnr Rm->M301, 파일럿 Rz1->M16 / Rz2->M26" -- 구조 규칙이 값을
#  정하는 저항은 θ 가 아니다(sizing CONTRACT 4.4 r5 4번) -> 상자를 받지 않는다(SPEC_CONTRACT 1절: 상자 없는 원소는 search 가 거부 --
#  θ 가 아닌 원소는 search 가 묻지 않는다).
# engine 원소 집합은 spec/topology JSON 직접 집계(피검 로더 아님).
DEC8_R = {
    "current_reuse_telescopic_ota": {"R1": (1e4, 1e7), "R2": (1e4, 1e7)},
    "sf_pushpull_output_opamp": {"R1a": (1e3, 1e6), "R1b": (1e3, 1e6), "R1c": (1e3, 1e6)},
}
DEC10_C = (1e-13, 1e-11)
DEC9_STRUCTURAL_R = {
    "two_stage_ota": {"Rz"},
    "nmcnr_amplifier": {"Rm"},
    "current_reuse_telescopic_ota": {"Rz1", "Rz2"},
}


def _engine_rc(name):
    """JSON 직접: topology 수동소자 중 kind 저항·커패시터이고 spec element_values 가 {"engine": true, ...} 인 것 -> {이름: kind}."""
    topo = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    ev = _spec(name)["human"]["element_values"]
    out = {}
    for e in topo.get("passive_elements", []):
        v = ev.get(e["name"])
        if e["kind"] in ("resistor", "capacitor") and isinstance(v, dict) and v.get("engine") is True:
            out[e["name"]] = e["kind"]
    return out


def _expected_boxes(name):
    """결정 8·10 으로 정해진 상자: 결정 8 의 저항 + 그 회로의 engine 커패시터 전부(결정 10)."""
    want = dict(DEC8_R.get(name, {}))
    for n, k in _engine_rc(name).items():
        if k == "capacitor":
            want[n] = DEC10_C
    return want


def _theta_bounds_of(doc):
    from gmid_engine.authoring import THETA_BOUNDS
    found = [s.value for s in doc.search if s.field == THETA_BOUNDS]
    return found[0] if found else ()


def test_engine_resistors_are_decision8_or_decision9_structural():
    """손 집계: library 의 engine 저항 = 결정 8 의 θ 저항 ∪ 결정 9 의 구조 규칙 저항(빠짐·겹침 없음)."""
    for name in TABLE:
        eng_r = {n for n, k in _engine_rc(name).items() if k == "resistor"}
        dec8 = set(DEC8_R.get(name, {}))
        dec9 = DEC9_STRUCTURAL_R.get(name, set())
        assert not (dec8 & dec9), name
        assert eng_r == dec8 | dec9, (name, eng_r)
    assert sum(len(_engine_rc(n)) for n in TABLE) == 18       # 손 집계: R 9(R1·R2·Rz1·Rz2·Rm·R1a~c·Rz) + C 9(Cc1·Cc2·ngcc Cm1·Cm2·nmcnr Cm1·Cm2·sf Cc·two_stage Cc·two_stage_sf Cc)


@pytest.mark.parametrize("name", sorted(TABLE))
def test_theta_bounds_follow_user_decisions(name):
    """spec 상자 = 결정 8(저항)·결정 10(engine 커패시터 전부), 결정 9 구조 규칙 저항은 상자 없음. JSON 과 로드 결과 둘 다."""
    want = _expected_boxes(name)
    raw = _spec(name)["human"]["search"].get("theta_bounds") or {}
    assert {n: (b["min"], b["max"]) for n, b in raw.items()} == want
    for n, b in raw.items():
        assert b["source"]["kind"] == "user_spec" and b["source"]["decided"] == "2026-10-08", (name, n)
    assert not set(raw) & DEC9_STRUCTURAL_R.get(name, set())
    kinds = _engine_rc(name)
    got = _theta_bounds_of(_load(name))
    assert [(t.element, t.kind, t.lo, t.hi) for t in got] == [(n, kinds[n]) + want[n] for n in sorted(want)]


def test_boxed_circuit_count():
    """상자가 있는 회로 = engine R/C 가 있는 6회로(SPEC_CONTRACT 5절 theta_bounds 측정 문장), 나머지 3회로는 칸 없음."""
    with_box = sorted(n for n in TABLE if _expected_boxes(n))
    assert with_box == ["current_reuse_telescopic_ota", "ngcc_3stage_ff", "nmcnr_amplifier", "sf_pushpull_output_opamp",
                        "two_stage_ota", "two_stage_ota_sf"]
    for n in set(TABLE) - set(with_box):
        assert "theta_bounds" not in _spec(n)["human"]["search"], n


@pytest.fixture(scope="module")
def toy_access_lib(tmp_path_factory):
    from gmid_engine.lut import load_lut_set
    from sizing.conftest import TOY_SPEC, new_access, write_toy_lut
    m, c = write_toy_lut(tmp_path_factory.mktemp("lib_toy_lut"))
    return new_access(load_lut_set(str(m), str(c), TOY_SPEC))


@pytest.mark.parametrize("name", sorted(TABLE))
def test_boxes_cover_exactly_theta_passive_components(name, toy_access_lib, tmp_path):
    """9회로: sizing θ 스키마(sizing CONTRACT 4.4 -- 의존 층 입력)의 수동소자 성분 원소 = spec 상자 원소, 그리고 search_domain 이
    재정의 없이(SearchSettings 상자 None) spec 상자만으로 변수를 만든다(거부 없음, 변수 = 상자의 ln)."""
    from gmid_engine.search import SearchSettings, search_domain
    from search.conftest import write_decls
    from sizing.conftest import library_ctx
    ctx = library_ctx(name, toy_access_lib)[5]
    kind_of = {"resistance": "resistor", "ss_resistance": "resistor", "capacitance": "capacitor"}
    theta_passive = {k: kind_of[t] for t, k in ctx.schema.components if t in kind_of}
    want = _expected_boxes(name)
    assert set(theta_passive) == set(want)
    assert theta_passive == {n: k for n, k in _engine_rc(name).items() if n in want}
    for r in DEC9_STRUCTURAL_R.get(name, set()):
        assert r not in theta_passive                            # 구조 규칙 저항은 θ 아님(결정 9)
    pdk, _ = write_decls(tmp_path / "pdk")
    dom = search_domain(ctx, SearchSettings(600.0, 40, None, (("front_budget_s", "test"),)), pdk,
                        _theta_bounds_of(_load(name)))
    got = {v.component[1]: (v.log, v.lo, v.hi) for v in dom.variables if v.component[0] in kind_of}
    assert set(got) == set(want)
    for n, (lo, hi) in want.items():
        assert got[n][0] is True
        assert got[n][1] == pytest.approx(math.log(lo), rel=1e-15) and got[n][2] == pytest.approx(math.log(hi), rel=1e-15)


# =====================================================================================================================
# CI-10 해소 (사용자 2026-10-08 "5번도 네 의견에 동의해", SPEC_CONTRACT 3절 loop 뷰 규칙 + 5절 개정, 커밋 3a38275)
# 기대값 출처: (d) 사용자 결정 문장(파일럿 되먹임 = {Cf1, Cf2}, Cs1·Cs2 는 입력 부하) + 계약 3절 문장(cuts = (소자, 입력 포트 넷
# 쪽 단자) 소자 이름순, weights = 절단 넷 (넷, 가중) 넷순, 차동 p +1/|D|, n −1/|D|) 을 topology JSON 에서 손으로 읽은 단자·role 에
# 적용한 리터럴. 피검 함수(load_sizing_spec·default_views)로 기대값을 만들지 않는다.
# =====================================================================================================================

CI10_FEEDBACK = ("Cf1", "Cf2")                             # (d) 사용자 2026-10-08 CI-10 결정
CI10_NOT_FEEDBACK = ("Cs1", "Cs2")                         # (d) 같은 결정: 입력-접지 샘플링 커패시터 = 입력 부하
# (a)+(d) 손으로 읽은 topology: Cf1 [Vom, Vip], Cf2 [Vop, Vim] -> 입력 포트 넷 쪽 단자 Vip·Vim, 소자 이름순
CI10_CUTS = (("Cf1", "Vip"), ("Cf2", "Vim"))
# 차동 입력 D = {Vip(p), Vim(n)}, |D| = 2 -> Vip +½, Vim −½, 넷순("Vim" < "Vip")
CI10_WEIGHTS = (("Vim", -0.5), ("Vip", 0.5))
PILOT_PENDING = 11                                          # (d) 5절 표 파일럿 행
PILOT_MOD5 = 5                                              # (d) 5절 '파일럿 뷰 4·metric 1'
# β = 1 루프(feedback []) 회로: (d) UD 9번 PM 정의 + 3절 'unity 면 weights·sense 가 port 와 같다'. 기대 weights·sense 는 손으로
# 읽은 ports role 에 3절 가중 규칙을 적용한 리터럴(출력 포트 1개 single_ended_output -> single_ended).
UNITY_LOOP = {
    "ngcc_3stage_ff": ((("Vinn", -0.5), ("Vinp", 0.5)), SenseDecl("Vout", None, "single_ended")),
    "nmcnr_amplifier": ((("Vin_n", -0.5), ("Vin_p", 0.5)), SenseDecl("Vout", None, "single_ended")),
}


def _topo_json(name):
    return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def _pm_views(doc):
    return [c.view for c in doc.constraints if c.metric == "pm_ss_deg"]


def test_ci10_pilot_json_preconditions():
    """입력 사실 확인(손으로 읽은 단자·role 이 기대값 리터럴의 근거임을 고정): Cf 는 출력->입력, Cs 는 입력->gnd, pm 표지 없음."""
    topo = _topo_json(PILOT)
    term = {p["name"]: p["terminals"] for p in topo["passive_elements"]}
    assert term["Cf1"] == ["Vom", "Vip"] and term["Cf2"] == ["Vop", "Vim"]
    assert term["Cs1"] == ["Vip", "gnd"] and term["Cs2"] == ["Vim", "gnd"]
    assert topo["ports"]["Vip"]["role"] == "differential_input_p"
    assert topo["ports"]["Vim"]["role"] == "differential_input_n"
    raw = _spec(PILOT)["human"]
    assert raw["feedback"]["elements"] == list(CI10_FEEDBACK)
    assert raw["feedback"]["source"]["kind"] == "user_spec"
    pm = [c for c in raw["constraints"] if c.get("metric") == "pm_ss_deg"]
    assert len(pm) == 1 and "view" not in pm[0]


def test_ci10_pilot_feedback_elements():
    doc = _load(PILOT)
    assert tuple(doc.feedback) == CI10_FEEDBACK
    assert set(doc.feedback) == set(CI10_FEEDBACK)


def test_ci10_pilot_pm_loop_view_declared():
    views = _pm_views(_load(PILOT))
    assert len(views) == 1
    v = views[0]
    assert v.mode == "loop"
    assert v.beta == BETA_DECLARED == "declared"
    assert tuple(v.cuts) == CI10_CUTS
    assert tuple(v.weights) == CI10_WEIGHTS
    assert v.sense is None


def test_ci10_beta_loop_excludes_sampling_caps():
    """거부 방향 확인: Cs1·Cs2 는 입력 포트 넷에 물려 있어(위 전제) 단자 규칙만으로는 절단 후보가 될 수 있지만, 되먹임이 아니므로
    feedback·cuts·weights 어디에도 들어가면 안 된다(사용자 2026-10-08: Cs 는 입력 부하). cuts 는 정확히 2개."""
    doc = _load(PILOT)
    v = _pm_views(doc)[0]
    cut_elements = {e for e, _ in v.cuts}
    for name in CI10_NOT_FEEDBACK:
        assert name not in doc.feedback
        assert name not in cut_elements
    assert len(v.cuts) == len(CI10_FEEDBACK) == 2
    assert {n for n, _ in v.weights} == {"Vip", "Vim"}


def test_ci10_pending_removed_pilot_counts():
    doc = _load(PILOT)
    decisions = [p.decision for p in doc.pending]
    assert "CI-10" not in decisions
    assert len(decisions) == PILOT_PENDING
    assert decisions.count("MOD5") == PILOT_MOD5
    assert all(c.view.mode != "pending" for c in doc.constraints if c.metric == "pm_ss_deg")


def test_ci10_absent_library_wide():
    assert all("CI-10" not in _markers(_spec(n)) for n in TABLE)
    assert all("CI-10" not in {p.decision for p in _load(n).pending} for n in TABLE)


@pytest.mark.parametrize("name", sorted(set(TABLE) - {PILOT}))
def test_non_pilot_feedback_empty(name):
    """파일럿 밖 8회로 feedback = [] (UD 9번, 5절)."""
    assert _spec(name)["human"]["feedback"]["elements"] == []
    assert tuple(_load(name).feedback) == ()


@pytest.mark.parametrize("name", sorted(UNITY_LOOP))
def test_non_pilot_pm_loop_beta_unity(name):
    weights, sense = UNITY_LOOP[name]
    doc = _load(name)
    views = _pm_views(doc)
    assert len(views) == 1
    v = views[0]
    assert v.mode == "loop" and v.beta == BETA_UNITY == "unity"
    assert tuple(v.weights) == weights
    assert v.sense == sense
    assert not v.cuts


@pytest.mark.parametrize("name", sorted(set(TABLE) - {PILOT} - set(UNITY_LOOP)))
def test_other_circuits_have_no_loop_view(name):
    """loop 뷰는 pm_ss_deg 기본뿐(3절) -- JSON 에 pm_ss_deg 제약이 없는 6회로는 loop 뷰가 없다."""
    assert not [c for c in _spec(name)["human"]["constraints"] if c.get("metric") == "pm_ss_deg"]
    assert all(c.view is None or c.view.mode != "loop" for c in _load(name).constraints)


def test_cm_pm_constraint_only_in_pilot():
    """[CM 2026-10-08] 사용자 결정(user_decisions.md 2026-10-08 "6번도 네 의견에 동의하고 제안한 값을 사용해" -- CMFB 루프 PM 하한
    60 deg, 완전 차동 회로에만): 파일럿에 pm_cm_ss_deg >= 60(user_spec, 판정) 한 건, 나머지 8회로에는 없다(JSON 직접 집계 + 로드)."""
    for name in TABLE:
        raw = [c for c in _spec(name)["human"]["constraints"] if c.get("metric") == "pm_cm_ss_deg"]
        got = [c for c in _load(name).constraints if c.metric == "pm_cm_ss_deg"]
        if name != PILOT:
            assert raw == [] and got == [], name
            continue
        assert len(raw) == 1 and len(got) == 1
        assert (raw[0]["op"], raw[0]["value"], raw[0]["source"]["kind"]) == (">=", 60, "user_spec")
        assert "view" not in raw[0]                                    # 3절: view 를 적지 않는다
        c = got[0]
        assert (c.op, c.value, c.judged) == (">=", 60.0, True)
        # [CM 0e487b3] SPEC_CONTRACT 3절 cm_loop: 차동 출력쌍(Vop = _p, Vom = _n, 손으로 읽은 ports) -> cm_output, 넷순 각 1/2
        assert c.view == ViewDecl("cm_output", weights=(("Vom", 0.5), ("Vop", 0.5)))
