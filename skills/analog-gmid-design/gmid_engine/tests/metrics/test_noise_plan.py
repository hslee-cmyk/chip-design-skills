"""[U8 2026-10-09] `noise_plan(ss, decl)` -- 폐루프 잡음 모드 구조 (설계 41 §7.3 '폐루프 모드'·'스위치', CI-10, metrics CONTRACT 10.1).

oracle (d) 설계 문장과 (a) 손 회로 구조:
* spec feedback 소자마다 **입력 포트 넷 쪽 단자**가 자유 노드(Cf(out, in) -> in). 되먹임이 아닌 Cs 는 그대로(CI-10).
* feedback 빈 tuple -> open(입력 고정), None -> `noise_feedback_undeclared`, 회로에 없는 소자 -> `noise_feedback_element_unknown`,
  입력 포트 단자가 정확히 하나가 아니면 -> `noise_feedback_cut_ambiguous`.
* 샘플링 커패시터: 소신호 커패시터 순번, 없는 이름은 `cap_problems`(조용히 빼지 않는다).
"""
import pytest

from gmid_engine.metrics import NoiseDecl, NoisePlan, noise_plan

from .noise_cases import Case


def sc(names=None):
    return Case(mos=(("M1", "out", "in", "gnd", "gnd", 1e-3, 1e-7),),
                res=(("Rf", "out", "in", 1e6),),
                cap=(("CL", "out", "gnd", 1e-12), ("Cf", "out", "in", 1e-12), ("Cs", "in", "gnd", 3e-12)), names=names)


def test_closed_frees_input_side_of_feedback_elements():
    ss = sc().ss()
    p = noise_plan(ss, NoiseDecl(feedback=("Cf", "Rf"), sampling_caps=("Cs",)))
    assert isinstance(p, NoisePlan)
    assert p.mode == "closed" and p.free_nets == frozenset({"in"})
    assert p.caps == (("Cs", ss.capacitors.index("Cs")),)
    assert p.cap_problems == () and p.reason is None


def test_open_when_no_feedback():
    p = noise_plan(sc().ss(), NoiseDecl(feedback=()))
    assert p.mode == "open" and p.free_nets == frozenset()


@pytest.mark.parametrize("decl, code", [
    (NoiseDecl(feedback=None), "noise_feedback_undeclared"),
    (NoiseDecl(), "noise_feedback_undeclared"),                         # 기본값 = 결정 대기·미제공
    (NoiseDecl(feedback=("Cx",)), "noise_feedback_element_unknown"),
    (NoiseDecl(feedback=("M1",)), "noise_feedback_element_unknown"),     # 되먹임 소자는 소신호 R·C 여야 한다
    (NoiseDecl(feedback=("CL",)), "noise_feedback_cut_ambiguous"),       # CL(out, gnd): 입력 포트 단자 없음
])
def test_undefined_reasons(decl, code):
    p = noise_plan(sc().ss(), decl)
    assert p.mode == "undefined" and p.reason == code


def test_unknown_sampling_cap_recorded():
    p = noise_plan(sc().ss(), NoiseDecl(feedback=("Cf",), sampling_caps=("Cs", "Cq")))
    assert p.cap_problems == ("Cq",)
    assert [name for name, _i in p.caps] == ["Cs"]


def test_name_bijection():
    names = {"in": "vin_x", "out": "q", "gnd": "zero", "Cf": "C7", "Cs": "C1", "CL": "C0", "Rf": "R5"}
    ss = sc(names).ss()
    p = noise_plan(ss, NoiseDecl(feedback=("C7", "R5"), sampling_caps=("C1",)))
    assert p.mode == "closed" and p.free_nets == frozenset({"vin_x"})
    assert p.caps == (("C1", ss.capacitors.index("C1")),)
