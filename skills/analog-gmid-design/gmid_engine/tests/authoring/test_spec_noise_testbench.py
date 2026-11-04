"""[U5 후속 2026-10-09] spec `human.noise_testbench` -- 설계 40 §11 U5 행('noise_testbench'), 41 §7.1 폐루프 모드 '스위치'
(spec 테스트벤치 선언 `noise_testbench.sampling_caps[]` 마다 kT/C_s 항), 사용자 결정 2026-10-08 Q11 잡음 포함 범위(CMFB·바이어스·
스위치 포함), SPEC_CONTRACT 1절(형식·거부 코드)·2절 거부표·3절(결과 레코드·섹션 지문 noise_testbench_fp).

기대값 출처(oracle):
* (d) 계약 문장: `{"sampling_caps": [{"element", "source"}, ...]}`, sampling_caps 는 비어 있지 않은 list(`type`), 항목 키는 {element,
  source}(그 밖 `unknown_key`), element 는 topology 수동소자 중 kind capacitor(`noise_cap_unknown`), 같은 이름 둘 `noise_cap_duplicate`,
  출처 없음 `source_missing`, kind user_spec 만, `{"pending": ...}` 는 `unknown_key` + `type`. 결과 `NoiseTestbenchDecl` 이름순 또는 None.
* (d) 41 §7.1 '샘플링 커패시터' -- 대상은 커패시터뿐(저항·MOS·이상 전원은 kT/C 대상이 아니다).
* (a) 합성 입력: 픽스처 fx_spec_amp 의 수동소자(Cfb·Cld = capacitor, Rfb = resistor, test 쪽 JSON 직접 확인), MOS Mfx1, 이상 전원 Vcm.
* (a) metamorphic: 지문 격리(이 섹션만 바꾸면 noise_testbench_fp·spec_fp 만), 출처 record 는 지문 밖, 항목 순서 무관,
  넷 이름 전단사·소자 이름 전단사에서 결과가 사상된 이름 그대로.
"""
from __future__ import annotations

import copy
import json

import pytest

from gmid_engine.authoring import NoiseTestbenchDecl, SamplingCapDecl, SpecSource

GATE = "noise_testbench"
FP = "noise_testbench_fp"
US = {"kind": "user_spec", "record": "fixture noise testbench", "decided": "2026-10-09"}


def _cap(name, **extra):
    return dict({"element": name, "source": copy.deepcopy(US)}, **extra)


def _set(sc, *names):
    sc.human[GATE] = {"sampling_caps": [_cap(n) for n in names]}


def _fps(doc):
    return dict(doc.section_fps)


def test_fixture_passive_kinds():
    """입력 전제(합성 입력 확인 -- 기대값 아님): 픽스처에 커패시터 2개·저항 1개, MOS Mfx1, 이상 전원 Vcm."""
    from authoring.conftest import SPEC_FIXTURES
    topo = json.loads((SPEC_FIXTURES / "fx_spec_amp.topology.json").read_text(encoding="utf-8"))
    kinds = {e["name"]: e["kind"] for e in topo["passive_elements"]}
    assert kinds == {"Rfb": "resistor", "Cfb": "capacitor", "Cld": "capacitor"}
    assert "Mfx1" in {e["name"] for e in topo["netlist"]}
    assert "Vcm" in {e["name"] for e in topo["ideal_sources"]}


# ---------------------------------------------------------------- 받는 입력

def test_absent_is_none(sc):
    assert GATE not in sc.human
    assert sc.load().noise_testbench is None


def test_single_cap(sc):
    _set(sc, "Cld")
    nt = sc.load().noise_testbench
    assert isinstance(nt, NoiseTestbenchDecl)
    assert len(nt.sampling_caps) == 1
    cap = nt.sampling_caps[0]
    assert isinstance(cap, SamplingCapDecl)
    assert cap.element == "Cld"
    assert isinstance(cap.source, SpecSource) and cap.source.kind == "user_spec"


def test_result_name_order_independent_of_document_order(sc):
    _set(sc, "Cld", "Cfb")                                        # 문서 순서 = 이름 역순
    a = sc.load().noise_testbench
    assert [c.element for c in a.sampling_caps] == ["Cfb", "Cld"]   # 계약: 이름순
    _set(sc, "Cfb", "Cld")
    b = sc.load().noise_testbench
    assert a == b


def test_measurement_load_capacitor_accepted(sc):
    """측정 부하 표지(element_values.measurement_load)가 붙은 커패시터도 kind 는 capacitor -- 계약 조건은 kind 뿐."""
    sc.human["element_values"]["Cld"]["measurement_load"] = True
    _set(sc, "Cld")
    doc = sc.load()
    assert [e.name for e in doc.element_values if e.measurement_load] == ["Cld"]     # 입력 전제가 실제로 걸렸다
    assert [c.element for c in doc.noise_testbench.sampling_caps] == ["Cld"]


def test_engine_decided_capacitor_accepted(sc):
    """값이 엔진 몫(θ)인 커패시터 Cfb 도 topology kind capacitor -- 값 결정 방식은 조건이 아니다."""
    _set(sc, "Cfb")
    assert [c.element for c in sc.load().noise_testbench.sampling_caps] == ["Cfb"]


# ---------------------------------------------------------------- 거부: 각 코드가 실제로 거부한다

# null 은 넣지 않는다: 선택 섹션의 null 을 '없음'으로 볼지 '모양 밖'으로 볼지 계약이 정하지 않는다(다른 U5 섹션 test 와 같음, 보고서 이의).
@pytest.mark.parametrize("section", [[{"element": "Cld"}], "Cld", 1.0], ids=["list", "str", "num"])
def test_section_not_object_type(sc, section):
    sc.human[GATE] = section
    d = sc.reject()
    assert sc.rules(d) == ["type"]
    assert d["rejected_gates"] == (GATE,)


def test_sampling_caps_missing_type(sc):
    sc.human[GATE] = {}
    sc.reject_only("type", GATE)


def test_sampling_caps_empty_type(sc):
    sc.human[GATE] = {"sampling_caps": []}
    sc.reject_only("type", GATE)


@pytest.mark.parametrize("caps", [{"element": "Cld"}, "Cld", 3], ids=["object", "str", "num"])
def test_sampling_caps_not_list_type(sc, caps):
    sc.human[GATE] = {"sampling_caps": caps}
    sc.reject_only("type", GATE)


@pytest.mark.parametrize("item", ["Cld", 1, ["Cld"], None], ids=["str", "num", "list", "null"])
def test_item_not_object_type(sc, item):
    sc.human[GATE] = {"sampling_caps": [item]}
    sc.reject_only("type", GATE)


@pytest.mark.parametrize("element", [1, None, ["Cld"], True], ids=["num", "null", "list", "bool"])
def test_element_not_string_type(sc, element):
    sc.human[GATE] = {"sampling_caps": [{"element": element, "source": copy.deepcopy(US)}]}
    sc.reject_only("type", GATE)


def test_section_unknown_key(sc):
    _set(sc, "Cld")
    sc.human[GATE]["band_hz"] = 1e6
    sc.reject_only("unknown_key", GATE)


def test_item_unknown_key(sc):
    sc.human[GATE] = {"sampling_caps": [_cap("Cld", gain_to_out=1.0)]}
    sc.reject_only("unknown_key", GATE)


def test_pending_marker_rejected_unknown_key_and_type(sc):
    """계약 1절: `{"pending": ...}` 는 객체로 읽혀 pending 키 unknown_key + sampling_caps 없음 type (결정 대기 표지 불가)."""
    sc.human[GATE] = {"pending": "SP-2"}
    d = sc.reject()
    assert sorted(sc.rules(d)) == ["type", "unknown_key"]
    assert d["rejected_gates"] == (GATE,)


@pytest.mark.parametrize("name", ["Cxx", "cld", "Rfb", "Mfx1", "Vcm"],
                         ids=["absent", "case_mismatch", "resistor", "mos", "ideal_source"])
def test_noise_cap_unknown(sc, name):
    _set(sc, name)
    hit = sc.reject_only("noise_cap_unknown", GATE)
    assert hit.where


def test_noise_cap_unknown_does_not_hide_valid_item(sc):
    """나쁜 항목 하나만 hit -- 옳은 항목(Cfb)은 hit 를 만들지 않는다."""
    _set(sc, "Cfb", "Rfb")
    d = sc.reject()
    assert sc.rules(d) == ["noise_cap_unknown"]


def test_noise_cap_duplicate(sc):
    _set(sc, "Cld", "Cld")
    sc.reject_only("noise_cap_duplicate", GATE)


def test_noise_cap_duplicate_among_others(sc):
    _set(sc, "Cld", "Cfb", "Cld")
    sc.reject_only("noise_cap_duplicate", GATE)


def test_source_missing(sc):
    sc.human[GATE] = {"sampling_caps": [{"element": "Cld"}]}
    sc.reject_only("source_missing", GATE)


@pytest.mark.parametrize("src", [{"kind": "pending_spice", "record": "r"}, {"kind": "reference"},
                                 {"kind": "plan_rule", "plan_id": "N3.7"}], ids=["pending_spice", "reference", "plan_rule"])
def test_source_kind_not_user_spec(sc, src):
    """계약 1절 'kind user_spec 만'. 규칙 이름은 다른 U5 섹션과 같은 source_kind_not_allowed_here(계약 2절 source_* 행)."""
    sc.human[GATE] = {"sampling_caps": [{"element": "Cld", "source": src}]}
    sc.reject_only("source_kind_not_allowed_here", GATE)


def test_missing_element_rejected(sc):
    """element 없음 -- 규칙 이름은 계약이 이 경우를 따로 적지 않아 게이트만 본다."""
    sc.human[GATE] = {"sampling_caps": [{"source": copy.deepcopy(US)}]}
    d = sc.reject()
    assert d["rejected_gates"] == (GATE,)


# ---------------------------------------------------------------- 지문 격리 (a) metamorphic

def test_fingerprint_isolation_add_section(sc):
    base = sc.load()
    assert FP in _fps(base)
    _set(sc, "Cld")
    got = sc.load()
    fa, fb = _fps(base), _fps(got)
    assert {k for k in fa if fa[k] != fb[k]} == {FP}
    assert base.spec_fp != got.spec_fp


def test_fingerprint_isolation_change_caps(sc):
    _set(sc, "Cld")
    a = sc.load()
    _set(sc, "Cld", "Cfb")
    b = sc.load()
    fa, fb = _fps(a), _fps(b)
    assert {k for k in fa if fa[k] != fb[k]} == {FP}
    assert a.spec_fp != b.spec_fp


def test_fingerprint_source_record_outside(sc):
    """계약 3절: SpecSource 는 kind 만 지문에 든다 -- record·decided 만 바꾸면 section_fps·spec_fp 불변."""
    _set(sc, "Cld")
    a = sc.load()
    sc.human[GATE]["sampling_caps"][0]["source"]["record"] = "other wording"
    sc.human[GATE]["sampling_caps"][0]["source"]["decided"] = "2026-10-10"
    b = sc.load()
    assert _fps(a) == _fps(b) and a.spec_fp == b.spec_fp


def test_fingerprint_item_order_invariant(sc):
    _set(sc, "Cld", "Cfb")
    a = sc.load()
    _set(sc, "Cfb", "Cld")
    b = sc.load()
    assert _fps(a)[FP] == _fps(b)[FP] and a.spec_fp == b.spec_fp


def test_other_section_change_leaves_noise_fp(sc):
    """다른 섹션(constraints 의 값)만 바꾸면 noise_testbench_fp 는 그대로, constraints_fp 만 바뀐다."""
    _set(sc, "Cld")
    a = sc.load()
    sc.constraint("gain_ss_db")["value"] = 41
    b = sc.load()
    fa, fb = _fps(a), _fps(b)
    assert {k for k in fa if fa[k] != fb[k]} == {"constraints_fp"}
    assert fa[FP] == fb[FP]


# ---------------------------------------------------------------- 이름 전단사 (a) metamorphic -- 규칙이 이름을 읽지 않는다
NET_MAP = {"n_inn": "w9", "n_inp": "w8", "n_mid": "w7", "n_outp": "w6", "n_tail": "w5", "n_bias": "w4", "n_fbk": "w3",
           "n_vcm": "w2", "rail_hi": "w1", "rail_lo": "w0"}
ELEM_MAP = {"Cfb": "Kz", "Cld": "Ka", "Rfb": "Kr"}                  # 커패시터 두 개의 이름순을 뒤집는다


def _rename(text, mapping):
    for old, new in mapping.items():
        text = text.replace('"%s"' % old, '"%s"' % new)
    return text


def _apply(sc, mapping):
    sc.write_topo(json.loads(_rename(json.dumps(sc.topo), mapping)))
    sc.spec = json.loads(_rename(json.dumps(sc.spec), mapping))
    sc.resync_fp()


def test_net_rename_keeps_result(sc):
    _set(sc, "Cld", "Cfb")
    before = sc.load().noise_testbench
    _apply(sc, NET_MAP)
    after = sc.load().noise_testbench
    assert after == before


def test_element_rename_maps_result(sc):
    assert ("Cfb" < "Cld") and (ELEM_MAP["Cfb"] > ELEM_MAP["Cld"])   # 전단사가 이름순을 뒤집는다
    tokens = set(json.dumps(sc.topo).split('"')) | set(json.dumps(sc.spec).split('"'))
    assert not set(ELEM_MAP.values()) & tokens                        # 새 이름이 기존 토큰과 겹치지 않음
    _set(sc, "Cld", "Cfb")
    before = [c.element for c in sc.load().noise_testbench.sampling_caps]
    _apply(sc, ELEM_MAP)
    after = [c.element for c in sc.load().noise_testbench.sampling_caps]
    assert after == sorted(ELEM_MAP[n] for n in before) == ["Ka", "Kz"]


def test_element_rename_keeps_rejection(sc):
    """저항 이름을 바꿔도 kind 로 거부한다 -- 이름 'R...' 이 아니라 kind 가 규칙이다."""
    _apply(sc, ELEM_MAP)
    _set(sc, "Kr")
    sc.reject_only("noise_cap_unknown", GATE)
