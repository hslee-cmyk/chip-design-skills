"""레이아웃 전 사이징의 폭 슬라이스 규칙 -- LUT 생성 규칙 폭 (계획 DEC-91 (2) '레이아웃 전 첫 사이징점은 LUT 생성 규칙의
확산 기하를 쓴다', lut CONTRACT 1.4 용량 기준 폭 `CapTable.w_ref_m`, 오케스트레이터 결정 2026-10-07).

진입점: `pre_layout_lut_access(memo) -> LutAccess`.

* kind 마다 w_key = round(`memo.lut.cap_map[kind].w_ref_m` / `memo.lut.spec.manufacturing_grid_m`) -- 기준 LUT(LUT 생성 규칙의
  폭·확산 기하로 만든 표)와 같은 폭의 DC 슬라이스. 그 (kind, w_key) 슬라이스가 없으면 `ValueError`(로드 때 w_ref_m 을 슬라이스
  대조로 정했거나 기록값이라 정상 LUT 에서는 생기지 않는다).
* 레이아웃 뒤(MOD7 결과) 실현 폭 슬라이스로 바꾸는 것은 DEC-89 재평가 몫이고 이 함수 밖이다.
"""
from .s2_values import LutAccess


def pre_layout_lut_access(memo):
    lut = memo.lut
    w_keys = []
    for kind in sorted(lut.cap_map):
        key = round(lut.cap_map[kind].w_ref_m / lut.spec.manufacturing_grid_m)
        if (kind, key) not in lut.slice_map:
            raise ValueError("pre_layout_lut_access: 용량 기준 폭의 DC 슬라이스가 없다 " + repr((kind, key)))
        w_keys.append((kind, key))
    return LutAccess(memo, tuple(w_keys))
