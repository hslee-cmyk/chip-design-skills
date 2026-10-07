"""봉인 8 `kvl_branch` 등식 계산 블록 (계획 N3.6 항목 8, DEC-64 v2, 설계 3.6).

진입점: `dc_seal_kvl_branch`(`@compute_block`) -- `dc_seal_kvl_branch(snapshot)`.

노드전압 정본에서 루프의 Σ ±(V(g) − V(s)) = ΔV 는 항등(telescoping)이므로, 남는 잔차는 멤버마다 노드 VGS 와 좌표가 정하는
VGS 의 차다. 그 차를 순방향 LUT 값(`dc_op.idu_forward`)으로 ID 환산(|Δ ln IDu| / (gm/ID), 봉인 2 와 같은 지표)해 멤버 합
≤ 멤버 tol_V 합(= 멤버 수 × tol_V, 셀별 값). 부호를 무시한 합이라 부호 있는 잔차의 상계다(보수적). 역산 함수를 쓰지 않는다.
멤버 tol_V 가 하나라도 미정이면 그 사이클은 undefined. 사이클 목록 = S1 `graph.rel_kvl_branch`.
"""
import math

from gmid_engine.core import compute_block
from gmid_engine.graph import GRAPH_KEY

from ._helpers_seal import judge
from .s2_values import DC_KEY, DC_SEAL_KVL_WRITER, SEAL_KVL_BRANCH

READS = (("graph", "rel_kvl_branch"), ("device", "dc_op"), ("device", "dc_tol_v"))
WRITES = (("graph", "dc_seal_8"),)
_JOIN = "+"


@compute_block(DC_SEAL_KVL_WRITER, reads=READS, writes=WRITES)
def dc_seal_kvl_branch(projection):
    ops = dict(projection.column("device", "dc_op"))
    tol_v = dict(projection.column("device", "dc_tol_v"))
    rows = []
    for edge in projection.value("graph", GRAPH_KEY, "rel_kvl_branch"):
        residual = sum(abs(math.log(ops[m].idu_forward) - ops[m].ln_idu) / ops[m].gm_id for m in edge.members)
        tols = [tol_v[m] for m in edge.members]
        bound = None if any(t is None for t in tols) else sum(tols)
        rows.append((_JOIN.join(edge.members), residual, bound, tuple(edge.members), ()))
    return {("graph", "dc_seal_8"): {DC_KEY: judge(SEAL_KVL_BRANCH, rows)}}
