"""[U1b-jrules bcfee60] 제약 view `{"loop_cut": [<끊는 넷>, ...]}` -- loop metric 의 내부 루프 뷰 선언(설계 41 1.8 안정도 선언).

근거(oracle (d) 계약 문장, 피검 함수 미사용):
- SPEC_CONTRACT '내부 루프 뷰 선언 [U1b-jrules]' 단락: 비지 않은 서로 다른 넷 이름 list(위반 `type`), 넷은 topology 단자에
  있어야 한다(`view_net_unknown`), 닫힌 어휘라 다른 키 동반은 `unknown_key`(`cut_weights` 와 같이 적어도 `unknown_key`),
  결과 `ViewDecl(mode loop, beta None, cuts=(("", 넷), ...) 넷순)`.
- SPEC_CONTRACT 2절 표 `view_not_applicable`(loop metric 의 loop_cut 만 예외 -- cm_loop 는 cm_sense_elements 만 예외),
  `view_shape_not_supported`(loop 에 `{"cut_weights": ...}` 단독), `view_net_unknown`(loop_cut 원소).
- 오케스트레이터 결정(2026-10-09): loop_cut 선언 제약의 출처는 cm_sense_elements 와 같이 `user_spec` 만(3절 cm_loop 항
  'source.kind 는 user_spec 필수'와 같은 규칙). 거부 규칙 이름은 계약에 아직 없으므로 '거부된다'만 확인한다.
입력: 픽스처 fx_spec_amp(손으로 읽은 JSON) -- 넷 n_mid·n_tail·n_outp·n_fbk 는 topology 단자, n_nowhere 는 어디에도 없음.
"""
from __future__ import annotations

import copy

import pytest

from gmid_engine.authoring import ViewDecl

US = {"kind": "user_spec", "record": "U1b-jrules loop_cut test", "decided": "2026-10-09"}
CM = {"metric": "pm_cm_ss_deg", "op": ">=", "value": 60.0}


def _pm(sc, view, source=None):
    """fixture 의 pm_ss_deg 제약(유일 -- 참조 value_from_constraint 대상이라 둘이면 ref_ambiguous)에 view 를 단다."""
    c = sc.constraint("pm_ss_deg")
    c["view"] = copy.deepcopy(view)
    c["source"] = copy.deepcopy(source or US)
    return c


def _loop_views(doc):
    return [c.view for c in doc.constraints if c.metric == "pm_ss_deg"]


# ------------------------------------------------------------------ 받아들이는 모양
def test_loop_cut_single_net_view(sc):
    _pm(sc, {"loop_cut": ["n_mid"]})
    (v,) = _loop_views(sc.load())
    assert isinstance(v, ViewDecl)
    # oracle (d): 계약 결과 모양 ViewDecl(mode loop, beta None, cuts=(("", 넷),))
    assert v.mode == "loop" and v.beta is None
    assert tuple(v.cuts) == (("", "n_mid"),)


def test_loop_cut_nets_are_sorted(sc):
    # oracle (d) '넷순': 선언 순서 n_tail, n_mid -> cuts 는 넷 이름 정렬("n_mid" < "n_tail")
    _pm(sc, {"loop_cut": ["n_tail", "n_mid"]})
    (v,) = _loop_views(sc.load())
    assert tuple(v.cuts) == (("", "n_mid"), ("", "n_tail"))


# ------------------------------------------------------------------ 거부(pytest.raises 는 sc.reject 안의 SchemaRejectedError)
@pytest.mark.parametrize("extra", [{"x": 1}, {"sense_p": "n_outp"}], ids=["unknown", "sense_p"])
def test_loop_cut_with_other_key_is_unknown_key(sc, extra):
    _pm(sc, dict({"loop_cut": ["n_mid"]}, **extra))
    sc.reject_only("unknown_key", "constraints")


def test_loop_cut_with_cut_weights_is_at_least_unknown_key(sc):
    # 계약 '`cut_weights` 와 같이 적어도 `unknown_key`' -> 다른 hit 동반은 계약이 정하지 않았다
    _pm(sc, {"loop_cut": ["n_mid"], "cut_weights": {"n_mid": 1.0}})
    sc.reject_has("unknown_key", "constraints")


@pytest.mark.parametrize("value", ["n_mid", [], [3], ["n_mid", None], ["n_mid", "n_mid"], {"n_mid": 1}],
                         ids=["str", "empty", "int_elem", "none_elem", "duplicate", "dict"])
def test_loop_cut_value_type(sc, value):
    _pm(sc, {"loop_cut": value})
    sc.reject_only("type", "constraints")


def test_loop_cut_unknown_net(sc):
    _pm(sc, {"loop_cut": ["n_mid", "n_nowhere"]})
    sc.reject_only("view_net_unknown", "constraints")


def test_loop_cut_weights_alone_still_not_supported(sc):
    _pm(sc, {"cut_weights": {"n_mid": 1.0}})
    sc.reject_only("view_shape_not_supported", "constraints")


@pytest.mark.parametrize("view", [{"sense_p": "n_outp", "sense_mode": "single_ended"},
                                  {"ac_excite": {"n_inp": 0.5, "n_inn": -0.5}, "sense_p": "n_outp", "sense_n": None,
                                   "sense_mode": "single_ended"}], ids=["sense_shape", "transfer_shape"])
def test_loop_metric_other_shapes_not_applicable(sc, view):
    _pm(sc, view)
    sc.reject_only("view_not_applicable", "constraints")


def test_loop_cut_not_applicable_to_cm_loop(sc):
    # 2절 view_not_applicable: cm_loop 의 예외는 cm_sense_elements 뿐 -> loop_cut 은 cm_loop 에 적용되지 않는다
    sc.human["constraints"].append(dict(copy.deepcopy(CM), view={"loop_cut": ["n_mid"]}, source=copy.deepcopy(US)))
    sc.reject_only("view_not_applicable", "constraints")


def test_loop_cut_requires_user_spec_source(sc):
    # 오케스트레이터 결정: 출처는 user_spec 만. 대조군 -- 같은 pending_spice 출처에 view 없는 pm 제약은 받는다(거부 원인이 출처 x
    # loop_cut 조합임을 고정). 규칙 이름은 계약 미정이라 constraints 게이트 거부만 본다.
    pend = {"kind": "pending_spice", "record": "loop_cut source test"}
    c = sc.constraint("pm_ss_deg")
    c["source"] = copy.deepcopy(pend)
    sc.load()
    c["view"] = {"loop_cut": ["n_mid"]}
    d = sc.reject()
    assert "constraints" in d["rejected_gates"], d["rejected_gates"]
