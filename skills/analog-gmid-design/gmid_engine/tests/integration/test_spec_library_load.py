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

from authoring.conftest import u5_design_signatures

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
    # [U5 2026-10-08] 옛 mismatch_sigma_mv·mirror_ratio_error_mv 는 옛 이름 표로 거부(설계 40 §3.8-8) -> 이름표에서 빼고 설계 어휘 11개
    **u5_design_signatures(),
    "power_dc_w": M("w", "dc", None),
    "area_search_m2": M("m2", "geom", None),
    "supply_current_dc": M("amp", "dc", None, "power"),
    "area_layout_m2": M("m2", "geom", None, "area"),
}

# 5절 표: 회로 -> (제약 수, 판정 수, pending 표지 수). 파일럿 pending 은 SP-10 해소(사용자 2026-10-07 "파일럿 CL1·CL2가
# 각각 1 pF", 커밋 0bc22fe) 뒤 13, CI-10 해소(사용자 2026-10-08 "5번도 네 의견에 동의해", 커밋 3a38275 -- feedback 표지 CI-10
# 1 과 pm_ss_deg 뷰 표지 MOD5 1 삭제) 뒤 11 = JSON 표지 직접 집계(MOD5 5 + SP-2·CI-15·CI-18·PA-1·PA-2·AC-3 각 1) = 5절 표 11.
# [사용자 결정 11, 2026-10-08] 회로마다 면적 예산 제약 `area_search_m2 <= v`(user_spec -> 판정) 1개씩 추가 -> 제약 수·판정 수 각 +1,
# pending 수 불변(예산은 결정 대기 표지가 아니다). 옛 표 = (0,0)·(8,5)·(0,0)·(3,2)·(2,2)·(1,1)·(3,3)·(2,1)·(3,2).
# [U5 2026-10-08] 설계 40 §9 Q5 표·§9.2 Q3·Q4 표·41 §7.1 Q11 표(oracle (d))로 U5 직전 값(옛 표)에서 손으로 더하고 뺀다:
#   common_gate (1,1)  + noise_excess_th<=2                                                      = (2,2)
#   파일럿     (10,7) - mismatch_sigma_mv(pending_spice, 판정 밖) - mirror_ratio_error_mv(그 참조, 판정 밖)
#                     + offset_in_sigma_mv<=3.3 + offset_sys_mv<=ref(offset_in_sigma_mv, 대상 판정 -> 판정)
#                     + swing_out_v>=2.4 + icm_margin_v>=0 + noise_out_int_vrms<=300e-6       = (13,12)
#   folded     (1,1)  + offset_excess 가드 + noise 가드                                         = (3,3)
#   ngcc       (4,3)  metric 표지(MOD5, 판정 밖) -> icmr_v>=0.6(이름 부여, 판정) + 가드 2         = (6,6)
#   nmcnr      (3,3)  + icmr_v>=0.5 + swing_out_v>=0.5 + 가드 2                                   = (7,7)
#   pushpull   (2,2)  변경 없음(Q11 보고만, 차동쌍 없음)                                          = (2,2)
#   sf_pushpull(4,4)  + 가드 2                                                                    = (6,6)
#   two_stage  (3,2)  - mismatch_sigma_mv(판정 밖) + gbw_ss_hz>=7e6(Q5) + 가드 2                   = (5,5)
#   two_stage_sf(4,3) - mismatch 참조(판정 밖) + gbw_ss_hz(two_stage 참조, 판정) + 가드 2          = (6,6)
# pending 표지: ngcc 의 metric 표지 MOD5 1개만 해소(7 -> 6), 나머지 불변.
# [U5 후속 2026-10-09] 설계 40 §9.2·§11 'J 추가 범위' U5 행 'sf_pushpull spec에 icm_margin_v >= 0(user_spec J-E)', 41 §4.6 '선언 입력 DC
# 유지 ... icm_margin_v >= 0 을 제약으로 둔다', 사용자 결정 J-E(_drafts/user_decisions.md 2026-10-08 "j해석은 네의견에 모두 동의해."):
#   sf_pushpull(6,6)  + icm_margin_v>=0(user_spec -> 판정)                                       = (7,7), pending 불변
TABLE = {
    "common_gate_amplifier": (2, 2, 6),
    "current_reuse_telescopic_ota": (13, 12, 11),
    "folded_cascode": (3, 3, 7),
    "ngcc_3stage_ff": (6, 6, 6),
    "nmcnr_amplifier": (7, 7, 6),
    "pushpull_follower_buffer": (2, 2, 5),
    "sf_pushpull_output_opamp": (7, 7, 6),
    "two_stage_ota": (5, 5, 7),
    "two_stage_ota_sf": (6, 6, 6),
}
# oracle (d) 사용자 결정 11 문장(_drafts/user_decisions.md 2026-10-08 "B으로 표의 값을 그대로 써. Cl을 빼는 것에 동의해")의 표 값 [mm²].
# m² 환산은 1 mm² = 1e-6 m² (단위 정의, 피검 식 아님).
DEC11_BUDGET_MM2 = {
    "common_gate_amplifier": 0.005, "pushpull_follower_buffer": 0.005, "folded_cascode": 0.01, "two_stage_ota": 0.015,
    "two_stage_ota_sf": 0.015, "sf_pushpull_output_opamp": 0.02, "ngcc_3stage_ff": 0.025, "nmcnr_amplifier": 0.025,
    "current_reuse_telescopic_ota": 0.04,
}
MM2_TO_M2 = 1e-6
# 측정 부하(measurement_load) -- oracle (d) 결정 11 "CL(측정 부하)은 면적에서 제외" + 회로 해석: 각 회로의 출력 부하 커패시터(파일럿은
# 두 출력 CL1·CL2), nmcnr 은 출력 부하 RL(25 kΩ)도 측정 부하다. common_gate 는 수동소자 없음. RL 포함은 SPEC_CONTRACT('CL·nmcnr RL')
# 의 회로 해석이고 결정 11 문장은 CL 만 명시한다(지금은 저항 면적이 미선언이라 면적 값에 영향 없음 -- Q9 저항 면적 포함 때 의미가 생긴다).
MEASUREMENT_LOADS = {
    "common_gate_amplifier": set(), "current_reuse_telescopic_ota": {"CL1", "CL2"}, "folded_cascode": {"CL"},
    "ngcc_3stage_ff": {"CL"}, "nmcnr_amplifier": {"CL", "RL"}, "pushpull_follower_buffer": {"CL"},
    "sf_pushpull_output_opamp": {"CL"}, "two_stage_ota": {"CL"}, "two_stage_ota_sf": {"CL"},
}
# 5절 ID 합계: SP-10 2 가 빠지고(65 -> 63), CI-10 해소로 CI-10 1·MOD5 1(파일럿 pm_ss_deg 뷰)이 빠진다(63 -> 61, MOD5 7 -> 6 =
# 파일럿 뷰 4·metric 1 + ngcc metric 1). 5절 문장 '남은 표지 61개' 와 JSON 직접 집계가 같음.
# [U5] ngcc metric 표지 MOD5 해소(설계 40 §9 Q5 ngcc 'icmr_v >= 0.6 V(값 유지, 이름 부여)') -> MOD5 6 -> 5, 합계 61 -> 60.
ID_TOTALS = {"AC-3": 9, "PA-1": 9, "PA-2": 9, "CI-15": 9, "CI-18": 9, "SP-2": 7, "MOD5": 5, "SP-3": 2,
             "CI-17": 1}
ID_TOTAL_SUM = 60
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


Q5_TWO_STAGE_GBW_HZ = 7e6   # oracle (d) 설계 40 §9 Q5 표 two_stage_ota 'GBW >= 7 MHz', two_stage_ota_sf 'GBW 는 두 회로 상속'


def test_cross_file_reference_value():
    """two_stage_ota_sf 의 value_from_file 참조가 two_stage_ota JSON 값으로 해석된다. [U5] GBW 는 Q5 로 제약이 되었다(7 MHz)."""
    doc = _load("two_stage_ota_sf")
    base = _spec("two_stage_ota")["human"]
    gain = [c for c in doc.constraints if c.metric == "gain_ss_db"][0]
    assert gain.value == [c for c in base["constraints"] if c["metric"] == "gain_ss_db"][0]["value"]
    gbw_c = [c for c in doc.constraints if c.metric == "gbw_ss_hz"]
    assert len(gbw_c) == 1 and gbw_c[0].value == Q5_TWO_STAGE_GBW_HZ and gbw_c[0].judged is True
    gbw = dict(doc.compensation_targets)["gbw_target_hz"]
    assert gbw.value == Q5_TWO_STAGE_GBW_HZ


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
    # [U2] search CONTRACT 3.24: 같은 자기동형 궤도의 수동소자 θ 성분은 대표 하나로 묶인다(current_reuse 의 R1/R2·Cc1/Cc2) -- 구성원은 변수에서 빠지고
    # 대표의 상자를 쓴다(상자가 같아야 받는다). 변수 ∪ 묶인 구성원 = spec 상자 원소.
    tied = {m[1] for _, ms in dom.ties for m in ms if m[0] in kind_of}
    assert set(got) | tied == set(want) and not set(got) & tied
    assert bool(tied) == (name == "current_reuse_telescopic_ota")          # 3.24 8 실측: 묶음이 서는 library 회로는 current_reuse 하나
    for n, (lo, hi) in want.items():
        if n in tied:
            continue
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
        assert c.view.mode == "cm_output" and tuple(c.view.weights) == (("Vom", 0.5), ("Vop", 0.5))
        # [6a6e4c7] 구동자 = 손 분류(M15·M16 -> Vom, M25·M26 -> Vop: 다른 channel 단자가 레일)
        assert set(c.view.cuts) == {("M15", "Vom"), ("M16", "Vom"), ("M25", "Vop"), ("M26", "Vop")}


# ---------------------------------------------------------------- [사용자 결정 11, 2026-10-08] 면적 예산·측정 부하

@pytest.mark.parametrize("name", sorted(TABLE))
def test_area_budget_constraint_follows_decision11(name):
    """회로마다 `area_search_m2 <= 결정 11 표 값(m²)` 판정 제약이 정확히 하나(JSON 과 로드 결과 둘 다), user_spec 2026-10-08."""
    raw = [c for c in _spec(name)["human"]["constraints"] if c.get("metric") == "area_search_m2"]
    assert len(raw) == 1, name
    (c,) = raw
    assert (c["op"], c["source"]["kind"], c["source"]["decided"]) == ("<=", "user_spec", "2026-10-08")
    assert "view" not in c
    want = DEC11_BUDGET_MM2[name] * MM2_TO_M2
    assert math.isclose(c["value"], want, rel_tol=1e-12), (c["value"], want)
    doc = _load(name)
    got = [x for x in doc.constraints if x.metric == "area_search_m2"]
    assert len(got) == 1 and got[0].op == "<=" and got[0].judged is True
    assert got[0].view is None or got[0].view.mode == "none"           # SPEC_CONTRACT: view 없음(판정 축)
    assert math.isclose(got[0].value, want, rel_tol=1e-12)
    assert len([x for x in doc.judged_constraints if x.metric == "area_search_m2"]) == 1


@pytest.mark.parametrize("name", sorted(TABLE))
def test_measurement_loads_declared_per_circuit(name):
    """측정 부하 표지: JSON 의 measurement_load 집합 = MEASUREMENT_LOADS(값 true), 모두 커패시터·저항(topology kind 직접),
    로드 결과 ElementValue.measurement_load 가 같은 집합(나머지 False)."""
    ev = _spec(name)["human"]["element_values"]
    topo = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
    kinds = {e["name"]: e["kind"] for e in topo.get("passive_elements", [])}
    marked = {k for k, v in ev.items() if isinstance(v, dict) and "measurement_load" in v}
    assert marked == MEASUREMENT_LOADS[name]
    for k in marked:
        assert ev[k]["measurement_load"] is True
        assert kinds[k] in ("capacitor", "resistor"), (name, k)
    doc = _load(name)
    assert {e.name for e in doc.element_values if e.measurement_load} == MEASUREMENT_LOADS[name]



# =====================================================================================================================
# [U5 2026-10-08] 설계 40 §9.2(Q3·Q4 회로별 선언)·§9 Q5 표·41 §7.1(Q11 회로별 잡음 선언) 과 library spec 대조
# oracle (d) 설계 표 값을 리터럴로 옮겼다(√2 = 가드 '<= √2', 300 µVrms = 300e-6 V, 2.4 V = ±1.2 V 차동 p-p).
# 비교 대상 = U5 어휘 12개 metric(후속 ff_gm_ratio 포함) 제약 전부(JSON 직접 + 로드 결과). 참조 제약은 ('ref', 대상) 로 적는다.
# =====================================================================================================================
SQRT2 = math.sqrt(2.0)
U5_METRICS = frozenset(u5_design_signatures())
OFFSET_GUARD = ("offset_excess", "<=", SQRT2)
NOISE_GUARD = ("noise_excess_th", "<=", 2.0)
PILOT_OFFSET_MV = 3.3
DESIGN_U5_ROWS = {
    "current_reuse_telescopic_ota": {("offset_in_sigma_mv", "<=", PILOT_OFFSET_MV),
                                     ("offset_sys_mv", "<=", ("ref", "offset_in_sigma_mv")),
                                     ("swing_out_v", ">=", 2.4), ("icm_margin_v", ">=", 0.0),
                                     ("noise_out_int_vrms", "<=", 300e-6)},
    "two_stage_ota": {OFFSET_GUARD, NOISE_GUARD},
    "two_stage_ota_sf": {OFFSET_GUARD, NOISE_GUARD},
    "folded_cascode": {OFFSET_GUARD, NOISE_GUARD},
    "ngcc_3stage_ff": {OFFSET_GUARD, NOISE_GUARD, ("icmr_v", ">=", 0.6)},
    "nmcnr_amplifier": {OFFSET_GUARD, NOISE_GUARD, ("icmr_v", ">=", 0.5), ("swing_out_v", ">=", 0.5)},
    "sf_pushpull_output_opamp": {OFFSET_GUARD, NOISE_GUARD, ("icm_margin_v", ">=", 0.0)},   # [U5 후속] J-E, 40 §9.2
    "pushpull_follower_buffer": set(),
    "common_gate_amplifier": {NOISE_GUARD},
}
OFFSET_GUARD_CIRCUITS = {"two_stage_ota", "two_stage_ota_sf", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
                         "sf_pushpull_output_opamp"}                       # §9.2 '6회로 가드'
NOISE_GUARD_CIRCUITS = OFFSET_GUARD_CIRCUITS | {"common_gate_amplifier"}   # 41 §7.1 '7회로'
LEGACY_METRICS = ("mismatch_sigma_mv", "mirror_ratio_error_mv", "mismatch_sigma_v")
# 출처 날짜: §9.2·Q11 로 새로 들어간 행은 결정일 2026-10-08. ngcc icmr_v 는 '값·출처 유지'(기존 사용자 확정)라 날짜를 보지 않는다.
KEEP_OLD_SOURCE = {("ngcc_3stage_ff", "icmr_v")}


def _row(c):
    if "value_from_constraint" in c:
        return (c["metric"], c["op"], ("ref", c["value_from_constraint"]))
    return (c["metric"], c["op"], float(c["value"]))


def _assert_rows(got, want):
    """(metric, op) 다중집합이 같고, 값은 수면 rel 1e-12(√2 의 JSON 십진 표기 반올림 허용), 참조면 그대로 같다."""
    key = lambda r: (r[0], r[1])  # noqa: E731
    g, w = sorted(got, key=key), sorted(want, key=key)
    assert [key(r) for r in g] == [key(r) for r in w], (g, w)
    for (m, _, v1), (_, _, v2) in zip(g, w):
        if isinstance(v2, tuple):
            assert v1 == v2, (m, v1, v2)
        else:
            assert math.isclose(v1, v2, rel_tol=1e-12, abs_tol=1e-15), (m, v1, v2)


@pytest.mark.parametrize("name", sorted(TABLE))
def test_u5_rows_match_design_tables_json(name):
    raw = [c for c in _spec(name)["human"]["constraints"] if isinstance(c.get("metric"), str) and c["metric"] in U5_METRICS]
    _assert_rows([_row(c) for c in raw], DESIGN_U5_ROWS[name])
    for c in raw:
        src = c["source"]
        if "value_from_constraint" in c:
            assert src["kind"] == "reference"
            continue
        assert src["kind"] == "user_spec", (name, c["metric"])
        if (name, c["metric"]) not in KEEP_OLD_SOURCE:
            assert src["decided"] == "2026-10-08", (name, c["metric"])
        assert "view" not in c                      # 설계 표가 뷰를 정하지 않는다 -- 유도(transfer)·없음(ls)


@pytest.mark.parametrize("name", sorted(TABLE))
def test_u5_rows_match_design_tables_loaded(name):
    doc = _load(name)
    got = []
    for c in doc.constraints:
        if c.metric in U5_METRICS:
            assert c.judged is True, (name, c.metric)
            got.append((c.metric, c.op, float(c.value)))
    # 참조 행(offset_sys_mv <= offset_in_sigma_mv)은 대상 값으로 해석된다
    want = [(m, o, PILOT_OFFSET_MV if isinstance(v, tuple) else v) for m, o, v in DESIGN_U5_ROWS[name]]
    _assert_rows(got, want)


def test_guard_circuit_sets():
    off = {n for n, rows in DESIGN_U5_ROWS.items() if any(r[0] == "offset_excess" for r in rows)}
    noi = {n for n, rows in DESIGN_U5_ROWS.items() if any(r[0] == "noise_excess_th" for r in rows)}
    assert off == OFFSET_GUARD_CIRCUITS and len(off) == 6
    assert noi == NOISE_GUARD_CIRCUITS and len(noi) == 7
    for name in TABLE:
        metrics = {c.metric for c in _load(name).constraints}
        assert ("offset_excess" in metrics) == (name in OFFSET_GUARD_CIRCUITS), name
        assert ("noise_excess_th" in metrics) == (name in NOISE_GUARD_CIRCUITS), name


def test_pilot_has_absolute_offset_not_guard():
    """§9.2: 파일럿만 절대값(3.3 mV)·계통 상한 참조를 두고 가드는 두지 않는다. 다른 회로에는 절대 offset 제약이 없다."""
    for name in TABLE:
        metrics = [c.metric for c in _load(name).constraints]
        if name == PILOT:
            assert metrics.count("offset_in_sigma_mv") == 1 and metrics.count("offset_sys_mv") == 1
            assert "offset_excess" not in metrics
        else:
            assert "offset_in_sigma_mv" not in metrics and "offset_sys_mv" not in metrics, name


def test_q5_two_stage_gbw_promoted():
    """§9 Q5: two_stage_ota GBW >= 7 MHz 제약(user_spec), two_stage_ota_sf 는 상속(참조), 둘 다 판정. pending_constraints 에
    gbw_ss_hz 가 남지 않는다(제약이 생겼으니 '아직 없는 값'이 아니다)."""
    raw = [c for c in _spec("two_stage_ota")["human"]["constraints"] if c.get("metric") == "gbw_ss_hz"]
    assert len(raw) == 1
    assert (raw[0]["op"], raw[0]["value"], raw[0]["source"]["kind"]) == (">=", Q5_TWO_STAGE_GBW_HZ, "user_spec")
    for name in ("two_stage_ota", "two_stage_ota_sf"):
        doc = _load(name)
        got = [c for c in doc.constraints if c.metric == "gbw_ss_hz"]
        assert len(got) == 1 and got[0].value == Q5_TWO_STAGE_GBW_HZ and got[0].judged is True
        assert "gbw_ss_hz" not in [m for m, _ in doc.pending_constraints], name


def _strings_and_keys(obj):
    """주석(`_` 키) 밖의 모든 키와 문자열 값."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            yield k
            yield from _strings_and_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings_and_keys(v)
    elif isinstance(obj, str):
        yield obj


@pytest.mark.parametrize("name", sorted(TABLE))
def test_no_legacy_matching_names_in_library(name):
    """§9.2 '옛 이름이 쓰인 library spec 3개는 U5 가 새 이름·값으로 바꾼다' -- 주석 밖 어디에도 키·metric·참조(`파일#metric`)
    토큰으로 없다(출처 record 의 서술 문장 속 언급은 이름 자리가 아니라 제외 -- 토큰 일치로만 본다)."""
    toks = list(_strings_and_keys(_spec(name)))
    assert toks
    for legacy in LEGACY_METRICS:
        assert not [t for t in toks if t == legacy or t.split("#")[-1] == legacy], (name, legacy)


# ---------------------------------------------------------------- topology 무관: 넷 이름 전단사 (9회로)
# (a) metamorphic: 한 회로의 넷 이름을 정렬 순서를 뒤집는 전단사로 바꿔(topology·spec 양쪽, 따옴표로 감싼 토큰 치환) 다시 로드해도
# 제약·판정·표지·원소 값·U5 섹션이 같고, 뷰·레일의 넷은 사상된 이름이다. 로더 규칙이 회로·넷 이름을 읽지 않는다는 근거(40 §1.2).

def _nets(topo):
    nets = set(topo["supply_nets"]) | {k for k, v in topo["ports"].items() if isinstance(v, dict)}
    for e in topo["netlist"]:
        nets |= {e[k] for k in ("drain", "gate", "source", "bulk") if k in e}
    for e in topo.get("passive_elements", []) + topo.get("ideal_sources", []):
        nets |= set(e["terminals"])
    return nets


def _summary(doc, net_map):
    def mapped_weights(v):
        if v is None or not getattr(v, "weights", None):
            return None
        return frozenset((net_map.get(n, n), w) for n, w in v.weights)
    cons = [(c.metric, c.op, c.value, c.judged, None if c.view is None else c.view.mode, mapped_weights(c.view))
            for c in doc.constraints]
    return (cons, sorted(p.decision for p in doc.pending), [(e.name, e.mode, e.value) for e in doc.element_values],
            sorted((net_map.get(n, n), v) for n, v in doc.supplies_v), doc.gain_budget_db_override, doc.driving_spec,
            doc.structure_count_budget, doc.noise_testbench)   # [U5 후속] noise_testbench 섹션도 넷 이름 무관


@pytest.mark.parametrize("name", sorted(TABLE))
def test_bijective_net_rename_keeps_library_load(name, tmp_path):
    import shutil
    for p in LIBRARY.iterdir():
        if p.name.endswith(".topology.json") or p.name.endswith(".sizing_spec.json"):
            shutil.copyfile(p, tmp_path / p.name)
    topo = json.loads((tmp_path / (name + ".topology.json")).read_text(encoding="utf-8"))
    nets = sorted(_nets(topo))
    net_map = {n: "q%03d" % (len(nets) - i) for i, n in enumerate(nets)}       # 순서를 뒤집는 전단사
    assert len(set(net_map.values())) == len(nets)
    elem_names = {e["name"] for e in topo["netlist"] + topo.get("passive_elements", []) + topo.get("ideal_sources", [])}
    assert not set(net_map.values()) & (elem_names | set(nets))

    def rename(text):
        for old, new in net_map.items():
            text = text.replace('"%s"' % old, '"%s"' % new)
        return text

    want = _summary(_load(name), net_map)
    tp = tmp_path / (name + ".topology.json")
    tp.write_text(rename(tp.read_text(encoding="utf-8")), encoding="utf-8")
    td = load_topology(str(tp))
    sp = tmp_path / (name + ".sizing_spec.json")
    spec = json.loads(rename(sp.read_text(encoding="utf-8")))
    spec["meta"]["topology_fp"] = td.connectivity_fp      # 입력 준비(바뀐 연결 지문에 맞춤) -- 기대값 아님
    sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    got = _summary(load_sizing_spec(str(sp), td, CATALOG), {})
    assert got == want
