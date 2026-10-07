"""authoring 공용 helper -- 되먹임 수동소자의 절단 단자 (7a design 2.2 L1~L3). `spec_elements.py`(규칙 L2 위반 거부)와
`spec_views.py`(루프 뷰 절단 유도)가 같이 쓴다 -- 같은 판정을 두 곳에서 따로 세우지 않는다.

* `input_terminal_nets(name, topology)`: 수동소자 `name` 의 두 단자 중 입력 포트 넷(포트 direction input)에 물린 단자의 넷
  tuple(단자 순서, 중복 유지). 길이 1 이면 그 넷이 절단 넷, 0 이면 `feedback_element_not_on_input`, 2 면
  `feedback_cut_ambiguous`. topology 수동소자에 없는 이름은 None(그 판정은 `feedback_element_unknown` 몫).
"""
from .ports import INPUT_DIRECTION


def input_terminal_nets(name, topology):
    inputs = frozenset(p.net for p in topology.ports if p.direction == INPUT_DIRECTION)
    for passive in topology.passives:
        if passive.name == name:
            return tuple(net for net in passive.terminals if net in inputs)
    return None
