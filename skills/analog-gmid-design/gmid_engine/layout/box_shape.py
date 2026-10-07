"""MOD7 box 기록 -- 행 폭 비와 길이 비 (design_mod7_layout.md 2.3, 옛 SD `check_box_shape` 의 같은 정의, 사용자 결정
2026-10-07 Q8 (vi): 하드 box 게이트 없음 -- 판정 축은 floorplan 외곽 면적이고 행 폭 비는 기록만 한다).

진입점: `box_verdict(rows, folds) -> BoxVerdict`.

* 행 폭 비 = max(행 폭) / min(행 폭). 행 폭은 부르는 쪽이 sum(nf x (L + PDK finger 여유)) 로 낸 값.
* 길이 비 = max(전체 폭, 전체 높이) / min(...), 전체 폭 = 최대 행 폭, 전체 높이 = 행 높이(finger_w) 합.
"""
from .contract_output import BoxVerdict


def box_verdict(rows, folds):
    """`rows`: ((행 id, 폭 m, 높이 m), ...) 비어 있지 않음. `folds`: 적용한 행 접기 기록(그대로 결과에 옮긴다)."""
    ordered = sorted(rows, key=lambda r: (r[1], r[0]))
    narrowest, widest = ordered[0], ordered[-1]
    total_width = widest[1]
    total_height = sum(r[2] for r in rows)
    elongation = max(total_width, total_height) / min(total_width, total_height)
    return BoxVerdict(widest[1] / narrowest[1], elongation, total_width, total_height, widest[0], narrowest[0],
                      tuple(folds))
