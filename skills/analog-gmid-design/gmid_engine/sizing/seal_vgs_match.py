"""봉인 2 VGS 정합 계산 블록 (계획 N3.6 항목 2, DEC-88 ID 환산 지표, 설계 3.6).

진입점: `dc_seal_vgs_match`(`@compute_block`) -- `dc_seal_vgs_match(snapshot)`.

모든 MOS(diode 포함): 노드 VGS·VDS·VSB 의 **순방향** LUT ln IDu(`dc_op.idu_forward` -- `dc_solve` 가 최종 노드값에서 순방향으로
한 번 조회한 값)와 소자 좌표 ln IDu(`dc_op.ln_idu` -- 쓰기 소자는 θ, 종속 소자는 순방향 값)의 차를 VGS 로 환산
|Δ ln IDu| / (gm/ID) ≤ tol_V(`dc_tol_v`, id_equivalent). 역산 함수를 쓰지 않는다(쓰는 쪽 = 역산, 재는 쪽 = 순방향).
"""
import math

from gmid_engine.core import compute_block

from ._helpers_seal import judge
from .s2_values import DC_KEY, DC_SEAL_VGS_MATCH_WRITER, SEAL_VGS_MATCH

READS = (("device", "dc_op"), ("device", "dc_tol_v"))
WRITES = (("graph", "dc_seal_2"),)


@compute_block(DC_SEAL_VGS_MATCH_WRITER, reads=READS, writes=WRITES)
def dc_seal_vgs_match(projection):
    tol_v = dict(projection.column("device", "dc_tol_v"))
    rows = []
    for m, op in projection.column("device", "dc_op"):
        mismatch = abs(math.log(op.idu_forward) - op.ln_idu) / op.gm_id
        rows.append((m, mismatch, tol_v[m], (m,), ()))
    return {("graph", "dc_seal_2"): {DC_KEY: judge(SEAL_VGS_MATCH, rows)}}
