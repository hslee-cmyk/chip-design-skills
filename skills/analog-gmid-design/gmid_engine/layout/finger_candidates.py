"""MOD7 소자별 finger_w 후보 계산 블록 (계획 N3.17 LY1·LY2, design_mod7_layout.md 3절 2(a)·L9).

진입점: `finger_candidates` -- core `@compute_block`(writer `ly_finger_candidates`, reads device `ly_device`·graph `ly_pdk`,
writes device `ly_fw_cand`).

후보 finger_w = PDK 특성화 폭(LUT DC 슬라이스 폭 키)만. 폭마다 nf = W/fw 의 내림·올림(1 이상) 두 개, 실현 W = nf x fw,
상대 오차 = |nf fw - W| / W, 하한·상한 = `w_tolerance`. 상한 밖 후보도 기록한다(`ok=False` -- W_request 근거).
같은 (kind, W, gm/ID, tol_V) 소자는 한 번만 계산한다(블록 안 memo).
"""
import math

from gmid_engine.core import compute_block

from ._ly_fields import DEVICE, F_DEVICE, F_FW_CAND, F_PDK, GRAPH, GRAPH_KEY, WRITER_FW_CAND
from .contract_output import FingerCandidate
from .w_tolerance import w_tolerance


def _candidates(device, keys, grid_m):
    out = []
    for key in keys:
        finger_w_m = key * grid_m
        lower, upper = w_tolerance(device.gm_id, device.tol_v_V, finger_w_m, grid_m)
        ratio = device.W_m / finger_w_m
        for n_fingers in sorted({max(1, math.floor(ratio)), max(1, math.ceil(ratio))}):
            realized = n_fingers * finger_w_m
            err = abs(realized - device.W_m) / device.W_m
            out.append(FingerCandidate(key, finger_w_m, n_fingers, realized, err, lower, upper,
                                       err <= upper and lower <= upper))
    return tuple(out)


@compute_block(WRITER_FW_CAND, reads=((DEVICE, F_DEVICE), (GRAPH, F_PDK)), writes=((DEVICE, F_FW_CAND),))
def finger_candidates(projection):
    """소자마다 `FingerCandidate` tuple(폭 키 오름차순, 같은 폭은 nf 오름차순)."""
    pdk = projection.value(GRAPH, GRAPH_KEY, F_PDK)
    keys_of = dict(pdk.slice_width_keys)
    memo = {}
    out = {}
    for name, device in projection.column(DEVICE, F_DEVICE):
        memo_key = (device.kind, device.W_m, device.gm_id, device.tol_v_V)
        if memo_key not in memo:
            memo[memo_key] = _candidates(device, keys_of[device.kind], pdk.manufacturing_grid_m)
        out[name] = memo[memo_key]
    return {(DEVICE, F_FW_CAND): out}
