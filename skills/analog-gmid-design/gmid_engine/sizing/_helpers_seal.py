"""봉인 항목 판정 공용 helper (계획 N3.6 표, N3.14 margin 정규화).

공개 함수:
* `judge(item, rows, detail=())` -> SealItem. `rows` = [(대상 이름, 위반 크기, 허용오차 또는 None, 소자 tuple, 노드 tuple)].
  - 허용오차가 정의된 행 중 크기 > 허용오차 가 하나라도 있으면 fail, 대상 = 그런 행 전부, 대표 = margin(크기/허용오차) 최대 행.
  - fail 이 없고 허용오차가 None 인 행이 있으면 undefined(대상 = 그 행들) -- 판정할 수 없음을 통과로 바꾸지 않는다.
  - 그 밖 pass(대표 = margin 최대 행, 행이 없으면 magnitude None).
  - margin = 크기/허용오차, 허용오차 0 이면 크기 > 0 -> +inf, 아니면 0.0. 같은 margin 최대 행이 여럿이면 대상 이름이
    가장 큰(정렬 마지막) 행이 대표(`detail` 의 `worst`).
* `node_values(projection)` -> {넷: V} 레일(`dc_rail_v`) + 나머지(`dc_v`).
"""
import math

from gmid_engine.core import normalized_margin

from .s2_values import SEAL_FAIL, SEAL_PASS, SEAL_UNDEFINED, SealItem


def judge(item, rows, detail=()):
    defined = [r for r in rows if r[2] is not None]
    failed = [r for r in defined if r[1] > r[2]]
    undefined = [r for r in rows if r[2] is None]
    if failed:
        status, targets = SEAL_FAIL, failed
    elif undefined:
        status, targets = SEAL_UNDEFINED, undefined
    else:
        status, targets = SEAL_PASS, ()
    pool = failed or defined
    worst = max(pool, key=lambda r: (_margin(r), r[0])) if pool else None
    devices = tuple(sorted({d for r in targets for d in r[3]}))
    nodes = tuple(sorted({n for r in targets for n in r[4]}))
    detail = tuple(detail) + (("n_checked", len(rows)), ("n_undefined", len(undefined)))
    if worst is None:
        return SealItem(item, status, None, None, None, devices, nodes, tuple(sorted(detail)))
    return SealItem(item, status, float(worst[1]), float(worst[2]), _margin(worst),
                    devices, nodes, tuple(sorted(detail + (("worst", worst[0]),))))


def _margin(row):
    """크기/tol. tol 0 이면 core `normalized_margin` 은 None 을 주지만(정규화 불가) 봉인 판정에서는 '허용오차 0 을 넘은
    위반'이라 크기 > 0 이면 +inf, 크기 ≤ 0 이면 0.0 으로 둔다(계약 6절)."""
    if row[2] == 0:
        return math.inf if row[1] > 0 else 0.0
    return normalized_margin(row[1], row[2])


def node_values(projection):
    values = dict(projection.column("node", "dc_rail_v"))
    values.update(projection.column("node", "dc_v"))
    return values
