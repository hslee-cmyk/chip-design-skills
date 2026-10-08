"""`_feedback_cuts` (비공개) -- feedback 소자의 절단 단자(입력 포트 넷 쪽 단자) 판정. 공개 경로로 확인한다:
- 로더 게이트 `elements` 규칙 `feedback_element_not_on_input`·`feedback_cut_ambiguous`(SPEC_CONTRACT 2절, 7a design 2.2 L2),
- `default_views(topology, feedback)` 의 β 루프 `cuts`·`weights`(SPEC_CONTRACT 3절: cuts = (소자, 절단 넷) 소자 이름순, 절단 넷 =
  소자의 입력 포트 넷 쪽 단자 넷, weights = 절단 넷 (넷, 가중) 넷순, 가중 = 입력 포트 role -- 차동 p +1/|D|, n −1/|D|, 단일 1).
기대값은 픽스처 JSON(손으로 읽은 단자·role)과 계약 문장에서 만든다(피검 함수로 기대값을 만들지 않는다)."""
from __future__ import annotations

import copy

import pytest

from gmid_engine.authoring import BETA_DECLARED, default_views

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}


def _add_passive(sc, name, kind, terminals, value):
    """topology 에 수동소자를 더하고(spec 값 선언 포함, F4) meta 지문을 맞춘다(입력 준비)."""
    t = sc.read_topo("fx_spec_amp")
    t["passive_elements"].append({"name": name, "kind": kind, "terminals": list(terminals)})
    sc.write_topo(t)
    key = "value_farad" if kind == "capacitor" else "value_ohm"
    sc.human["element_values"][name] = {key: value, "source": copy.deepcopy(US)}
    sc.resync_fp()


def _pm(doc):
    return [c for c in doc.constraints if c.metric == "pm_ss_deg"][0]


# ---------- 절단 넷 = 입력 포트 넷 쪽 단자 ----------

def test_fixture_cfb_cut_at_n_inn(sc):
    """픽스처: Cfb terminals [n_fbk, n_inn], n_inn = differential_input_n(|D| = 2) -> cuts (Cfb, n_inn), weights (n_inn, −½)."""
    t = sc.read_topo("fx_spec_amp")
    assert next(p for p in t["passive_elements"] if p["name"] == "Cfb")["terminals"] == ["n_fbk", "n_inn"]
    assert t["ports"]["n_inn"]["role"] == "differential_input_n"
    v = _pm(sc.load()).view
    assert v.mode == "loop" and v.beta == BETA_DECLARED == "declared"
    assert tuple(v.cuts) == (("Cfb", "n_inn"),)
    assert tuple(v.weights) == (("n_inn", -0.5),)
    assert v.sense is None


def test_cut_terminal_first_position(sc):
    """입력 포트 넷이 첫 단자여도 그 단자가 절단 넷: Cq [n_inp, n_outp] -> (Cq, n_inp), 가중 +½(differential_input_p)."""
    _add_passive(sc, "Cq", "capacitor", ["n_inp", "n_outp"], 1e-13)
    sc.human["feedback"]["elements"] = ["Cq"]
    v = _pm(sc.load()).view
    assert tuple(v.cuts) == (("Cq", "n_inp"),)
    assert tuple(v.weights) == (("n_inp", 0.5),)


def test_two_elements_two_inputs_sorted(sc):
    """cuts 소자 이름순, weights 넷순: {Cfb -> n_inn, Cq -> n_inp} -> 차동 두 절단 (n_inn −½, n_inp +½)."""
    _add_passive(sc, "Cq", "capacitor", ["n_outp", "n_inp"], 1e-13)
    sc.human["feedback"]["elements"] = ["Cq", "Cfb"]
    v = _pm(sc.load()).view
    assert tuple(v.cuts) == (("Cfb", "n_inn"), ("Cq", "n_inp"))
    assert tuple(v.weights) == (("n_inn", -0.5), ("n_inp", 0.5))


def test_two_elements_same_input_one_weight(sc):
    """같은 입력 넷의 두 소자: cuts 2개, 절단 넷 가중은 넷마다 하나(n_inn −½)."""
    _add_passive(sc, "Rq", "resistor", ["n_outp", "n_inn"], 5e4)
    sc.human["feedback"]["elements"] = ["Rq", "Cfb"]
    v = _pm(sc.load()).view
    assert tuple(v.cuts) == (("Cfb", "n_inn"), ("Rq", "n_inn"))
    assert tuple(v.weights) == (("n_inn", -0.5),)


def test_single_ended_input_weight_one(sc):
    """단일 입력(role single_ended_input) 하나 -> 가중 1. n_inp 를 포트에서 빼고 n_inn 을 단일 입력으로."""
    t = sc.read_topo("fx_spec_amp")
    del t["ports"]["n_inp"]
    t["ports"]["n_inn"] = {"direction": "input", "role": "single_ended_input"}
    # 포트에서 뺀 n_inp 는 Q1 gate 에만 남아 gate 전용 넷이 된다 -> bias_inputs 선언 필요(CONTRACT 9절, Q6).
    t["bias_inputs"] = ["n_inp"]
    sc.write_topo(t)
    sc.resync_fp()
    sc.constraint("parasitic_pm_ss_deg")["view"]["ac_excite"] = {"n_inn": 1.0}
    v = _pm(sc.load()).view
    assert tuple(v.cuts) == (("Cfb", "n_inn"),)
    assert tuple(v.weights) == (("n_inn", 1.0),)


def test_default_views_direct_matches_loader(sc):
    """default_views(topology, feedback) 공개 함수가 로더와 같은 loop 유도를 낸다(로드 한 번에 한 번 쓰이는 그 함수)."""
    dv = default_views(sc.topology(), ("Cfb",))
    assert dv.loop == _pm(sc.load()).view


# ---------- 거부 규칙 ----------

@pytest.mark.parametrize("elements", [["Rfb"], ["Cld"], ["Rfb", "Cfb"]], ids=["Rfb", "Cld", "Rfb_and_Cfb"])
def test_feedback_element_not_on_input(sc, elements):
    """Rfb [n_outp, n_fbk]·Cld [n_outp, rail_lo] 은 입력 포트 넷 단자가 없다 -> 그 규칙 하나(elements 게이트).
    feedback 이 거부된 로드는 루프 뷰를 유도하지 않으므로 constraints 쪽 hit 가 따라오지 않는다(3절)."""
    sc.human["feedback"]["elements"] = elements
    sc.reject_only("feedback_element_not_on_input", "elements")


def test_feedback_cut_ambiguous(sc):
    """두 단자가 모두 입력 포트 넷(n_inp–n_inn 커패시터) -> feedback_cut_ambiguous 하나."""
    _add_passive(sc, "Cx", "capacitor", ["n_inp", "n_inn"], 1e-13)
    sc.human["feedback"]["elements"] = ["Cx"]
    sc.reject_only("feedback_cut_ambiguous", "elements")


def test_feedback_cut_ambiguous_not_a_problem_when_not_feedback(sc):
    """같은 소자가 feedback 이 아니면 거부 없음(규칙은 feedback.elements 소자에만)."""
    _add_passive(sc, "Cx", "capacitor", ["n_inp", "n_inn"], 1e-13)
    sc.load()


def test_feedback_pending_propagates_as_pending_view(sc):
    """feedback 이 결정 대기 표지면 loop view = pending(decision = 그 ID), 새 표지를 더하지 않는다(ID 는 한 번만)."""
    sc.human["feedback"] = {"pending": "CI-10"}
    doc = sc.load()
    v = _pm(doc).view
    assert v.mode == "pending" and v.decision == "CI-10"
    assert [p.decision for p in doc.pending].count("CI-10") == 1


def test_feedback_empty_is_beta_unity(sc):
    sc.human["feedback"]["elements"] = []
    v = _pm(sc.load()).view
    assert v.mode == "loop" and v.beta == "unity"
