"""정규화 제약 행 -- 커널 결과 스냅샷에서 (설계 design_mod6_search_front 5절, N3.14, NFR-5).

진입점: `constraint_rows(snapshot, lut_access, w_min_m, grid_m) -> (rows, undefined)`.

* [설계 개정 S-18, 2026-10-08] W 하한: MOS 마다(tol 과 무관하게 늘) c = (W − W_min)/g. W_min = PDK 선언 `min_finger_w_m`
  (difftap.2), g = PDK `manufacturing_grid_m` -- W 판정 분해능 = 제조 격자 한 칸.

모든 행은 c ≥ 0 무차원이고 분모는 그 양의 판정 분해능이다(상수 없음). `active` = c ≤ 1(여유가 분해능 한 칸 이하).
* 봉인 6 벌크(설계 5절 표): MOS 마다 c = (min(vsb, vds + vsb) + tol_V)/tol_V -- 역바이어스 여유(양수 = 역바이어스),
  tol_V = `dc_tol_v`(id_equivalent 셀). 봉인 6 판정 max(0, −vsb, −(vds+vsb)) ≤ tol_V 와 c ≥ 0 이 같은 집합이다.
* 반전 하한(D-1 (라), 설계 4.2): 쓰기 소자(`dc_coord.role == writer`)마다 c = (r − r_peak)·(gm/ID)/tol_V. r = 좌표 ln IDu,
  r_peak = 그 소자 동작점 (L, VDS, VSB) 의 gm/ID 곡선 정점 ln IDu(lut `gm_id_curve`, memo), gm/ID = dc_op 순방향 값.
* 봉인 7 포화 여유는 VDSAT 접근자가 없어 행을 만들 수 없다(sizing O1 -- 우회 없음, `seal7_pending` 이 점을 대기로 둔다).
* tol_V 가 None 인 소자의 행은 만들지 않고 `undefined` 에 이름을 남긴다(판정 보류 -- 통과로 세지 않는다).
* spec 성능 제약(gain 등 ss 영역)은 MOD5 `ss_linearize` 가 없어 여기서 재지 않는다(`find_front` 가 판정 보류로 기록, S-1).
"""
import math

import numpy as np

from gmid_engine.lut import gm_id_curve
from gmid_engine.sizing import COORD_WRITER

from .search_values import CON_INVERSION, CON_SEAL6, CON_WMIN, ConstraintRow


def _row(name, c):
    return ConstraintRow(name, float(c), c <= 1)


def constraint_rows(snapshot, lut_access, w_min_m, grid_m):
    tols = dict(snapshot.column("device", "dc_tol_v"))
    coords = dict(snapshot.column("device", "dc_coord"))
    rows, undefined = [], []
    for m, op in snapshot.column("device", "dc_op"):
        rows.append(_row(CON_WMIN + ":" + m, (op.W - w_min_m) / grid_m))
        tol = tols.get(m)
        if tol is None or not tol > 0:
            undefined.append(m)
            continue
        rows.append(_row(CON_SEAL6 + ":" + m, (min(op.vsb, op.vds + op.vsb) + tol) / tol))
        if coords[m].role != COORD_WRITER:
            continue
        curve = gm_id_curve(lut_access.memo, op.kind, op.w_key, op.L, op.vds, op.vsb)
        peak = int(np.argmax(curve.gm_id_vals))
        w_m = lut_access.memo.lut.slice_map[(op.kind, op.w_key)].w_m
        r_peak = math.log(float(curve.id_vals[peak])) + math.log(op.L) - math.log(w_m)
        rows.append(_row(CON_INVERSION + ":" + m, (op.ln_idu - r_peak) * op.gm_id / tol))
    return tuple(rows), tuple(sorted(undefined))
