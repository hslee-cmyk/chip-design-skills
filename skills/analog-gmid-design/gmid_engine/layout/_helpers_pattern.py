"""MOD7 matching 패턴 공용 helper -- 패턴 선택(`pattern_select`)과 행 재구성(`rows`)이 같은 정의를 쓴다(개념당 정의 하나).

공개 이름(규칙 B helper 예외):
* `orient(group, devices)` -> (hub 쪽이 source 인 (이름, source, drain) tuple, "") 또는 (None, 사유) -- hub-leaf 패턴 함수 전제.
* `offsets(rows, members)` -> (dx, dy) 멤버 무게중심(finger 피치 단위, 행 가운데 기준)의 x·y 최대 차, 정확한 유리수.
* `pattern_rows(result, transistors)` -> `PatternRow` tuple(`canonical_row` 로 node_sequence 정규화).
"""
from fractions import Fraction

from .canonical_rows import canonical_row
from .contract_output import PatternRow


def orient(group, devices):
    """hub-leaf 전제: `hub_net` 이 있고 멤버마다 source 나 drain 이 hub 이며 leaf(반대쪽) 넷이 겹치지 않는다."""
    hub = group.hub_net
    if hub is None:
        return None, "no_hub_net"
    ends = []
    for name in group.members:
        d = devices[name]
        if d.source == hub:
            ends.append((name, d.source, d.drain))
        elif d.drain == hub:
            ends.append((name, d.drain, d.source))
        else:
            return None, "member_not_on_hub:" + name
    if len({leaf for _, _, leaf in ends}) != len(ends):
        return None, "leaf_net_shared"
    return tuple(ends), ""


def offsets(rows, members):
    """멤버 무게중심(finger 피치 단위, 행 가운데 기준)의 x·y 최대 차 -- 정확한 유리수로 계산.
    행 r(0부터, 행 수 R), 길이 n 인 행의 i 번째 finger: x = i - (n-1)/2, y = r - (R-1)/2."""
    sums = {m: [0, 0, 0] for m in members}
    n_rows = len(rows)
    for r, row in enumerate(rows):
        length = len(row.transistor_sequence)
        for i, name in enumerate(row.transistor_sequence):
            acc = sums[name]
            acc[0] += 2 * i - (length - 1)
            acc[1] += 2 * r - (n_rows - 1)
            acc[2] += 1
    xs = [Fraction(acc[0], 2 * acc[2]) for acc in sums.values() if acc[2]]
    ys = [Fraction(acc[1], 2 * acc[2]) for acc in sums.values() if acc[2]]
    return max(xs) - min(xs), max(ys) - min(ys)


def pattern_rows(result, transistors):
    """패턴 함수 결과 dict 의 `rows` -> 정규화된 `PatternRow` tuple."""
    out = []
    for row in result["rows"]:
        row = canonical_row(row, transistors)
        segments = tuple((tuple(s["transistor_sequence"]), tuple(s["node_sequence"])) for s in row.get("segments") or ())
        out.append(PatternRow(tuple(row["transistor_sequence"]), tuple(row["node_sequence"]), segments,
                              tuple(row.get("crossover_after") or ())))
    return tuple(out)
