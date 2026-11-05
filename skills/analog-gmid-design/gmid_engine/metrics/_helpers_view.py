"""전달 뷰 -> 노달 계 입력 공용 helper (사용처: `offset_analysis`, `offset_systematic`, `block_residual`).

공개 함수: `view_system`, `view_factor`(+ 상수 `PARAMETER_ORDER`).

* `view_system(ss, view)` -> `(고정 노드 집합, 구동 {노드: V}, 관측 벡터 (size,), 여기 ((넷, 가중), ...), 감지 (넷, 넷|None))` 또는 None(소신호 전달 뷰가 아님).
  뷰의 고정 노드 = 교류접지 ∪ 입력 포트 ∪ 뷰 구동 넷 -- `metrics_ss` `_Ledger.full` 이 같은 뷰에 세우는 계와 같은 집합(같은 뷰 = 같은 계).
  전달 뷰 = mode `transfer`(명시 ac_excite), `port`(기본 포트 전달), 되먹임 선언 없는 `loop`(β = 1, 포트 뷰와 같은 계).
* `view_factor(ss, nodal, fixed)` -> 그 고정 노드 집합의 `nodal_factor` 튜플. G 의 조립 자리는 필드 `graph.ss_nodal`(`NodalSystem`) 하나다 -- `nodal` 을 넘기면 그 G 를 읽고
  (고정 노드가 필드의 고정 집합과 같으면 필드의 인수분해를 그대로, 다르면 -- 뷰가 입력 밖 넷을 구동하는 경우 -- 같은 G 로 그 집합의 LU 를 새로 낸다),
  `nodal` 이 None 이면(필드를 거치지 않는 단위 호출) `ss_nodal.nodal_of(ss)` 로 같은 조립을 한다.
"""
import numpy

from ._helpers_nodal import capacitance_matrix, charge_seeded, nodal_factor
from .ss_nodal import nodal_of

PARAMETER_ORDER = ("gm", "gmb", "gds")          # `MosSmallSignal` 소신호 파라미터 필드 순서(스탬프 항목 단위)


def view_system(ss, view):
    mode = getattr(view, "mode", None)
    if mode == "transfer":
        pairs, decl = view.transfer.ac_excite, view.transfer
    elif mode in ("port", "loop") and getattr(view, "sense", None) is not None and not getattr(view, "cuts", ()):
        pairs, decl = view.weights, view.sense
    else:
        return None
    index = {net: i for i, net in enumerate(ss.nodes)}
    fixed = {index[n] for n in tuple(ss.ground_nets) + tuple(ss.input_nets)} | {index[n] for n, _a in pairs}
    sense = numpy.zeros(len(ss.nodes))
    sense[index[decl.sense_p]] += 1.0
    if decl.sense_n is not None:
        sense[index[decl.sense_n]] -= 1.0
    return fixed, {index[n]: a for n, a in pairs}, sense, tuple(pairs), (decl.sense_p, decl.sense_n)


def view_factor(ss, nodal, fixed):
    base = nodal_of(ss) if nodal is None else nodal
    fixed = frozenset(int(i) for i in fixed)
    return base.factor if fixed == base.fixed else nodal_factor(base.g, fixed, c=capacitance_matrix(ss.circuit, len(ss.nodes)) if charge_seeded(base.g, fixed) else numpy.zeros(base.g.shape))
