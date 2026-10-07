"""넷별 단자 인덱스 -- S1 생성 때 한 번 만든다 (설계 design_mod3_s1_graph 2.2 `s1_index.py`, S6a 1.3·1.5).

진입점: `terminal_index(devices, passives, sources) -> tuple`.

반환 = 넷 이름순 ((넷, ((원소, 단자), ...)), ...), 안쪽은 (원소, 단자) 정렬. 단자 = MOS 채널 3단자 d|g|s 와 2단자 원소의
t0|t1(`TWO_TERMINAL_NAMES`). bulk 는 넣지 않는다(설계 3절: 차수 = 채널 3단자 + 수동 2 + 이상원 2, bulk 사용처는
`device.bulk` 필드). S1 의 `node.terminals` 필드와 교류접지 (2) 판정이 이 인덱스 하나를 쓴다(원소 목록을 다시 돌지 않는다).
"""
from gmid_engine.authoring import TWO_TERMINAL_NAMES
from gmid_engine.core import sorted_items

from .s1_values import MOS_TERMINAL_NAMES


def terminal_index(devices, passives, sources):
    by_net = {}
    for x in devices:
        for term, net in zip(MOS_TERMINAL_NAMES, (x.d, x.g, x.s)):
            by_net.setdefault(net, []).append((x.name, term))
    for x in passives + sources:
        for term, net in zip(TWO_TERMINAL_NAMES, x.terminals):
            by_net.setdefault(net, []).append((x.name, term))
    return tuple((net, sorted_items(pairs)) for net, pairs in sorted_items(by_net))
