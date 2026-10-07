"""θ 전류 상자 -- kind 마다 (꺼짐 전류, 최대 전류) LUT 유도 (오케스트레이터 결정 2026-10-08 S-3, 설계 4.1 '(0, GB4 표 행 최대 ID]').

진입점: `current_box(lut_access, kind) -> (I_off, I_max)`(A). S0 당 kind 마다 1회(`search_domain` 이 표로 든다).

* I_off(하한) = 레이아웃 전 폭 슬라이스(`lut_access.w_keys[kind]`)에서 VGS = 0 격자면의 ID 중 최솟값(on_mask 점만) --
  SPICE 오라클 `off_current_A`(엔진이 LUT VGS=0 누설 ID 로 내는 양)와 같은 열이다. 소자 기하·바이어스가 θ 로 정해지기 전이라
  격자 전체 최솟값을 쓴다: 이보다 작은 전류는 어느 동작점에서도 꺼진 소자와 구별되지 않는다.
* I_max(상한) = 그 kind 의 모든 폭 슬라이스에서 ID 최댓값(각 슬라이스는 자기 폭 w_m 의 ID) -- 특성화된 최대 단일 finger 폭의
  최대 전류(GB4 상한표의 '행 최대 ID' 자리). **잠정값**(오케스트레이터 2026-10-08): PDK 선언에 finger 수 상한이 없어 여러 finger
  합 폭은 넣지 않는다 -- 참 상한은 선언된 최대 nf 또는 면적 상한이 있어야 정해진다(열린 항목 S-3b, find_front notes `provisional`).
* VGS 격자에 0 이 없거나 유효 점이 없으면 `SchemaRejectedError`(detail reason `lut_vgs_zero_missing`·`lut_current_box_empty`).
"""
import math

import numpy as np

from gmid_engine.core import SchemaRejectedError


def current_box(lut_access, kind):
    lut = lut_access.memo.lut
    sl = lut.slice_map[(kind, dict(lut_access.w_keys)[kind])]
    vgs = [float(v) for v in sl.VGS_grid]
    zero = [i for i, v in enumerate(vgs) if abs(v) <= math.ulp(max(abs(vgs[0]), abs(vgs[-1])))]
    if not zero:
        raise SchemaRejectedError(detail={"reason": "lut_vgs_zero_missing", "kind": kind, "w_key": str(sl.w_key)})
    plane = np.asarray(sl.ID)[:, zero[0]]
    on = np.asarray(sl.on_mask, dtype=bool)[:, zero[0]] & (plane > 0)
    peaks = [float(np.max(np.where(np.asarray(s.on_mask, dtype=bool), np.asarray(s.ID), -np.inf)))
             for (k, _w), s in sorted(lut.slice_map.items()) if k == kind]
    if not on.any() or not peaks or not max(peaks) > 0:
        raise SchemaRejectedError(detail={"reason": "lut_current_box_empty", "kind": kind})
    return float(np.min(plane[on])), max(peaks)
