"""봉인 6 벌크 역바이어스 계산 블록 (계획 N3.6 항목 6, DEC-61, 설계 3.6).

진입점: `dc_seal_bulk_reverse`(`@compute_block`) -- `dc_seal_bulk_reverse(snapshot)`.

MOS 마다 source–bulk·drain–bulk 접합이 역바이어스인지 노드전압 차로 본다(LUT 부호 규약 크기: vsb = s·(V(s) − V(b)),
vdb = vds + vsb). 순바이어스 크기 = max(0, −vsb, −vdb) ≤ tol_V(`dc_tol_v` -- VSB 는 노드전압 차이고 그 노드전압은 ln IDu
좌표 역산으로 만들어졌으므로 id_equivalent 지표, N3.6 기본안). tol_V 미정 소자는 undefined. 크기로 덮지 않는다.
"""
from gmid_engine.core import compute_block

from ._helpers_seal import judge
from .s2_values import DC_KEY, DC_SEAL_BULK_WRITER, SEAL_BULK_REVERSE

READS = (("device", "dc_op"), ("device", "dc_tol_v"))
WRITES = (("graph", "dc_seal_6"),)


@compute_block(DC_SEAL_BULK_WRITER, reads=READS, writes=WRITES)
def dc_seal_bulk_reverse(projection):
    tol_v = dict(projection.column("device", "dc_tol_v"))
    rows = []
    for m, op in projection.column("device", "dc_op"):
        forward = max(0.0, -op.vsb, -(op.vds + op.vsb))
        rows.append((m, forward, tol_v[m], (m,), ()))
    return {("graph", "dc_seal_6"): {DC_KEY: judge(SEAL_BULK_REVERSE, rows)}}
