"""비지배 필터 (설계 design_mod6_search_front 6.3 4, DEC-77, NFR-5). MOD8 판정 축 재필터도 같은 함수를 쓴다(설계 0절 2).

진입점: `nondominated(points, ties) -> ParetoResult`.

* `points`: ((point_id, (축 값, ...), slack), ...). 축은 모두 최소화. `slack` = 활성 제약 여유 합(남기는 순서 2순위).
* `ties`: 축마다 동률 폭 -- 음 아닌 float 또는 `width(id_p, id_q) -> float`(판정 축 ΔA_tie 처럼 두 점에 따라 다른 폭).
* 축 비교: |a − b| ≤ 폭 이면 동률, a < b − 폭 이면 나음. p 가 q 를 지배 = 어느 축도 나쁘지 않고 한 축 이상 나음.
  모든 축이 동률이면 같은 점으로 접는다(먼저 남은 점이 대표).
* 남기는 순서(NFR-4): 첫 축 값 오름차순 -> slack 큰 쪽 -> point_id 이름순. 이 순서로 하나씩 넣으며 지배·접힘을 판정하고,
  새 점이 이미 남은 점을 지배하면 그 점을 뺀다(지배자 기록).
"""
from .search_values import ParetoResult


def _width(tie, p, q):
    return float(tie(p, q)) if callable(tie) else float(tie)


def _relation(p, q, ties):
    """p 대비 q 의 축 관계: (p 가 나은 축 수, q 가 나은 축 수)."""
    better = worse = 0
    for a, b, tie in zip(p[1], q[1], ties):
        width = _width(tie, p[0], q[0])
        if a < b - width:
            better += 1
        elif b < a - width:
            worse += 1
    return better, worse


def nondominated(points, ties):
    points = tuple(points)
    ties = tuple(ties)
    for pid, values, _slack in points:
        if len(values) != len(ties):
            raise ValueError("nondominated: 점 %r 의 축 수 %d 가 동률 폭 수 %d 와 다르다" % (pid, len(values), len(ties)))
    order = sorted(range(len(points)), key=lambda i: (points[i][1][0], -points[i][2], points[i][0]))
    kept, folded, dominated = [], [], []
    for i in order:
        p = points[i]
        absorbed = False
        for k in kept:
            better, worse = _relation(points[k], p, ties)
            if better == 0 and worse == 0:
                folded.append((i, k))
                absorbed = True
                break
            if worse == 0 and better > 0:
                dominated.append((i, k))
                absorbed = True
                break
        if absorbed:
            continue
        survivors = []
        for k in kept:
            better, worse = _relation(p, points[k], ties)
            if worse == 0 and better > 0:
                dominated.append((k, i))
            else:
                survivors.append(k)
        kept = survivors + [i]
    kept.sort(key=lambda i: (points[i][1][0], -points[i][2], points[i][0]))
    return ParetoResult(tuple(kept), tuple(sorted(folded)), tuple(sorted(dominated)))
