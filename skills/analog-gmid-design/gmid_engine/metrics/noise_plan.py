"""폐루프 잡음 모드 구조 -- spec feedback·샘플링 커패시터 선언 -> 소신호 회로의 자유 입력 넷과 커패시터 위치 (설계 41 §7.3 '폐루프 모드', 단위 U8).

진입점: `noise_plan(ss, decl) -> NoisePlan`.

* 폐루프 모드(`noise_out_int_vrms`)는 선언된 되먹임 소자로 루프를 닫은 상태의 출력 잡음이다. 입력 포트 넷은 본래 고정 노드(전달 뷰의 구동·교류접지)인데 폐루프에서는
  증폭기 입력 노드가 되먹임 망에 달려 자유로 풀린다: spec feedback 소자마다 **입력 포트 넷 쪽 단자**(authoring `_feedback_cuts` 와 같은 규칙: 소자의 두 단자 중 정확히
  하나가 입력 포트 넷)를 자유 노드로 둔다. 되먹임이 아닌 소자(Cs 등 입력 부하)는 그대로 둔다(CI-10). 되먹임 소자가 소신호 R·C 가 아니거나 입력 포트 쪽 단자가
  정확히 하나가 아니면 정의 불가(`noise_feedback_element_unknown`·`noise_feedback_cut_ambiguous`).
* `decl.feedback` 이 빈 tuple 이면 되먹임이 없는 회로 -- `open`: 입력 고정 그대로 출력 잡음을 잰다(출력 PSD, 입력 단락). None(결정 대기·미제공)이면 정의 불가
  `noise_feedback_undeclared`.
* 샘플링 커패시터(`decl.sampling_caps`): 소신호 회로의 커패시터 순번을 적는다. 이름이 소신호 커패시터가 아니면 `cap_problems` 에 적는다(그 항을 더하지 않는다 --
  조용히 빼지 않고 호출한 쪽이 정의 불가로 낸다).
"""
from .noise_types import NoisePlan

CODE_UNDECLARED = "noise_feedback_undeclared"
CODE_ELEMENT_UNKNOWN = "noise_feedback_element_unknown"
CODE_CUT_AMBIGUOUS = "noise_feedback_cut_ambiguous"


def _element(ss, name):
    for names, elements in ((ss.resistors, ss.circuit.resistors), (ss.capacitors, ss.circuit.capacitors)):
        if name in names:
            return elements[names.index(name)]
    return None


def _input_side(ss, element):
    inputs = set(ss.input_nets)
    sides = [ss.nodes[node] for node in (element.a, element.b) if ss.nodes[node] in inputs]
    return sides[0] if len(sides) == 1 and element.a != element.b else None


def noise_plan(ss, decl):
    caps = tuple(sorted(((name, ss.capacitors.index(name)) for name in decl.sampling_caps if name in ss.capacitors),
                        key=lambda cap: cap[1]))             # 소신호 회로의 커패시터 순번(정준 순서) -- 이름 치환에 합 순서가 불변
    cap_problems = tuple(name for name in decl.sampling_caps if name not in ss.capacitors)
    if decl.feedback is None:
        return NoisePlan("undefined", reason=CODE_UNDECLARED, caps=caps, cap_problems=cap_problems)
    if not decl.feedback:
        return NoisePlan("open", caps=caps, cap_problems=cap_problems)
    free = []
    for name in decl.feedback:
        element = _element(ss, name)
        if element is None:
            return NoisePlan("undefined", reason=CODE_ELEMENT_UNKNOWN, detail=(("element", name),), caps=caps,
                             cap_problems=cap_problems)
        net = _input_side(ss, element)
        if net is None:
            return NoisePlan("undefined", reason=CODE_CUT_AMBIGUOUS, detail=(("element", name),), caps=caps,
                             cap_problems=cap_problems)
        free.append(net)
    return NoisePlan("closed", free_nets=frozenset(free), caps=caps, cap_problems=cap_problems)
