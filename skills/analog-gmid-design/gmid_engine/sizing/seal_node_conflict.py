"""봉인 1 노드 충돌 계산 블록 (계획 N3.6 항목 1, 설계 3.6).

진입점: `dc_seal_node_conflict`(`@compute_block`) -- `dc_seal_node_conflict(snapshot)`.

노드마다 {노드 값} ∪ {닿는 관계가 함의하는 값(`dc_path_values`)}의 최대 − 최소 ≤ 허용오차. 허용오차 = 그 노드에 닿는 MOS
관계 소자들의 tol_V(`dc_tol_v`) 최댓값. MOS 관계가 없는 노드(저항 강하·고정값만)는 LUT 오차원이 없어 부동소수
한계 n·eps·max|V|(n = 값 수)를 쓴다. MOS 관계는 있는데 tol_V 가 모두 미정이면 그 노드는 undefined. LUT 를 부르지 않는다
(값은 `dc_columns` 가 역산으로 만든 것을 읽기만 한다 -- 쓰는 쪽 = 역산, 재는 쪽 = 비교).
"""
import sys

from gmid_engine.core import compute_block

from ._helpers_seal import judge, node_values
from .s2_values import DC_KEY, DC_SEAL_NODE_CONFLICT_WRITER, PATH_MOS, SEAL_NODE_CONFLICT

READS = (("node", "dc_path_values"), ("node", "dc_v"), ("node", "dc_rail_v"), ("device", "dc_tol_v"))
WRITES = (("graph", "dc_seal_1"),)


@compute_block(DC_SEAL_NODE_CONFLICT_WRITER, reads=READS, writes=WRITES)
def dc_seal_node_conflict(projection):
    values = node_values(projection)
    tol_v = dict(projection.column("device", "dc_tol_v"))
    rows = []
    for net, paths in projection.column("node", "dc_path_values"):
        implied = [values[net]] + [p.value for p in paths]
        spread = max(implied) - min(implied)
        devices = tuple(sorted({p.relation[1] for p in paths if p.relation[0] == PATH_MOS}))
        if devices:
            defined = [tol_v[m] for m in devices if tol_v[m] is not None]
            tol = max(defined) if defined else None
        else:
            tol = len(implied) * sys.float_info.epsilon * max(abs(v) for v in implied)
        rows.append((net, spread, tol, devices, (net,)))
    return {("graph", "dc_seal_1"): {DC_KEY: judge(SEAL_NODE_CONFLICT, rows)}}
