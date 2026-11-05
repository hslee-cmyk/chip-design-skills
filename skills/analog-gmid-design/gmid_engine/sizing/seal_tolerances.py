"""봉인 허용오차 계산 블록 -- 소자별 tol_V 셀과 자기 동작점 gm (계획 N3.6 허용오차 식 v6.4, DEC-32·DEC-87·DEC-88, 설계 40 §3.7-3·§2.4.11).

진입점: `dc_tolerances`(`@compute_block`) -- `dc_tolerances(snapshot, lut)`.

* `device.dc_tol_v` = (kind, w_key, L 앵커, VDS) 셀의 id_equivalent tol_V(V) 또는 None(셀 미정의) -- 봉인 1·2·3·6·8 이 쓴다
  (봉인 2·3·SCC 수렴 = ID 환산 지표, DEC-88. 봉인 1·6·8 의 지표 배정은 N3.6 기본안 '그 전압을 만든 LUT 조회 종류' --
  노드전압을 만든 것이 ln IDu 좌표 역산이므로 같은 id_equivalent).
* `device.dc_gm` = 그 소자 ID × 그 동작점(L, VGS, VDS, VSB)의 LUT gm/ID(`dc_op.gm_id` × `dc_op.current`, S) -- dc 단계 gm 의 유일한
  정본(writer 이 블록 하나, 설계 40 §2.4.8). 봉인 3 tol_I(= tol_V × 노드에 닿는 소자 `dc_gm` 최댓값), `ss_dev` gm, 전력 분해능 b_P
  (`metrics_dc` 의 `power_resolution_w`), 영점 상쇄 수동소자 R = 1/Σ`dc_gm`(`passive_values`)이 이 필드를 읽는다.
  `dc_op` 하나만 읽으므로 parent(S2p)·이전 평가와 무관하다: 같은 θ 는 parent 와 상관없이 같은 봉인 결과를 낸다(사용자 결정 G-3').
  순환 없음: `dc_op` 는 ⑤ W 블록이 쓰고 tol_I 는 봉인 3 에서만 쓴다(SCC 수렴은 tol_V).
"""
from gmid_engine.core import SealViolationError, compute_block

from gmid_engine.lut import tol_v_table

from ._helpers_lut import with_device
from .s2_values import DC_TOLERANCES_WRITER

READS = (("device", "dc_op"),)
WRITES = (("device", "dc_tol_v"), ("device", "dc_gm"))


@compute_block(DC_TOLERANCES_WRITER, reads=READS, writes=WRITES)
def dc_tolerances(projection):
    (lut,) = projection.extras
    tols = {}
    gm = {}
    for m, op in projection.column("device", "dc_op"):
        try:
            tols[m] = tol_v_table(lut.memo, op.kind, op.w_key).at(op.L, op.vds, "id_equivalent")      # 그 소자 슬라이스의 셀
        except SealViolationError as exc:
            raise with_device(exc, m, "tol_v_cell") from exc
        gm[m] = op.gm_id * op.current
    return {("device", "dc_tol_v"): tols, ("device", "dc_gm"): gm}
