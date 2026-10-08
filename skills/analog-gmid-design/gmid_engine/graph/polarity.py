"""사이클 극성 (설계 41 §1.8 '극성'·§1.12.4, 계획 N3.2-7).

진입점: `loop_polarity(cycle, cells) -> int`.

**DC 사이클 극성**: 커패시터를 지나지 않는 사이클(저항은 지나도 된다)의 극성 = 셀·소자 부호의 곱이다: CS 의 gate->drain 은 반전(-1), 그 밖의 MOS 엣지
(gate->source, source->drain, pass)와 저항은 비반전(+1). 커패시터를 지나는 사이클은 저주파 경로가 없어 극성이 `ac_only` 이고 이 함수는 0 을 낸다(값은 -1, 1, 0 뿐; 0 은
'미정의'가 아니라 `ac_only` -- 그 사이클의 수동소자는 GB5 보상 후보로 올라간다). 루프 뷰의 극성은 그 뷰에 속한 DC 사이클들의 극성이며(`view_analysis`), 서로 다르면
`loop_polarity_conflict`, DC 사이클이 없으면 `loop_polarity_undefined`(review_needed)다.
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
