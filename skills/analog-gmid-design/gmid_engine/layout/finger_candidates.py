"""MOD7 소자별 finger_w 후보 계산 블록 (계획 N3.17 LY1·LY2, design_mod7_layout.md 3절 2(a)·L9, 사용자 결정 2026-10-07 Q4).

진입점: `finger_candidates` -- core `@compute_block`(writer `ly_finger_candidates`, reads device `ly_point`(gm_id)·`ly_slices`·
graph `ly_pdk`, writes device `ly_fw_cand`).

보존량은 (ID, gm/ID, L)이다(Q4 (i)). 후보 finger_w = PDK 특성화 폭(LUT DC 슬라이스 폭 키)만, 그중 `ly_slices` 가 사용 가능
(`reason == ""`)인 폭. 폭마다 그 슬라이스의 `W_need` 로 nf = W_need/fw 의 내림·올림(1 이상) 두 개, 실현 W = nf x fw,
상대 오차 = |nf fw - W_need| / W_need, 허용오차 = `w_tolerance`(그 슬라이스의 id_equivalent tol_V 셀 x gm/ID, 격자 하한,
실효 = 둘 중 큰 값). `ok` = 오차 <= 실효 허용오차. 밖 후보도 기록한다(`ok=False` -- W_request 근거).
같은 (gm/ID, 슬라이스 tuple) 소자는 한 번만 계산한다(블록 안 memo).
"""
import math

from gmid_engine.core import compute_block

from ._ly_fields import DEVICE, F_FW_CAND, F_POINT, F_PDK, F_ROW_GROUPS, F_SLICES, GRAPH, GRAPH_KEY, WRITER_FW_CAND
from .contract_output import FingerCandidate
from .w_tolerance import w_tolerance


def _candidates(gm_id, slices, grid_m, excluded=()):
    out = []
    for s in slices:
        if s.reason or s.finger_w_key in excluded:     # 사용 불가 슬라이스, 그리고 MOD8 이 이 소자의 행 그룹에서 뺀 폭 키(WB-1 그룹 단위 키 제외)
            continue
        tol = w_tolerance(gm_id, s.tol_v_V, s.finger_w_m, grid_m)
        ratio = s.W_need_m / s.finger_w_m
        for n_fingers in sorted({max(1, math.floor(ratio)), max(1, math.ceil(ratio))}):
            realized = n_fingers * s.finger_w_m
            err = abs(realized - s.W_need_m) / s.W_need_m
            out.append(FingerCandidate(s.finger_w_key, s.finger_w_m, n_fingers, s.W_need_m, realized, err, tol.lower,
                                       tol.upper, tol.effective, tol.grid_dominated, err <= tol.effective))
    return tuple(out)


@compute_block(WRITER_FW_CAND, reads=((DEVICE, F_POINT), (DEVICE, F_SLICES), (GRAPH, F_PDK), (GRAPH, F_ROW_GROUPS)),
               writes=((DEVICE, F_FW_CAND),))
def finger_candidates(projection):
    """소자마다 `FingerCandidate` tuple(폭 키 오름차순, 같은 폭은 nf 오름차순). 소자가 속한 행 그룹의 `excluded_keys` 폭은 후보에서 뺀다."""
    grid = projection.value(GRAPH, GRAPH_KEY, F_PDK).manufacturing_grid_m
    slices_of = dict(projection.column(DEVICE, F_SLICES))
    excluded_of = {name: rg.excluded_keys for rg in projection.value(GRAPH, GRAPH_KEY, F_ROW_GROUPS) for name in rg.members}
    memo = {}
    out = {}
    for name, point in projection.column(DEVICE, F_POINT):
        memo_key = (point.gm_id, slices_of[name], excluded_of.get(name, ()))
        if memo_key not in memo:
            memo[memo_key] = _candidates(point.gm_id, slices_of[name], grid, memo_key[2])
        out[name] = memo[memo_key]
    return {(DEVICE, F_FW_CAND): out}
