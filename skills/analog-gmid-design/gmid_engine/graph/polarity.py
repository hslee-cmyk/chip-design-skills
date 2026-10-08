"""루프 극성 (설계 41 §1.8 '극성', 계획 N3.2-7).

진입점: `loop_polarity(cycle, cells) -> int`.

끊는 점에서 한 바퀴 도는 경로의 **저주파 부호**를 셀·소자 부호의 곱으로 계산한다: CS 의 gate->drain 은 반전(-1), 그 밖의 MOS 엣지
(gate->source, source->drain, pass)와 저항은 비반전(+1). 커패시터를 지나면 저주파 경로가 없어 부호가 정의되지 않는다 -> 0 (호출자가
`loop_polarity_undefined` 로 올린다). 값은 -1, 1, 0 뿐이다.
"""
from .s1v_values import CELL_CS, EDGE_CAPACITOR, EDGE_GATE_DRAIN


def loop_polarity(cycle, cells):
    kind = {c.dev: c.kind for c in cells.cells}
    sign = 1
    for edge in cycle:
        if edge.etype == EDGE_CAPACITOR:
            return 0
        if edge.etype == EDGE_GATE_DRAIN and kind[edge.element] == CELL_CS:
            sign = -sign
    return sign
