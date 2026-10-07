"""MOD7 box 판정 -- 행 폭 비와 길이 비 (design_mod7_layout.md 2.3, 옛 SD `check_box_shape` 의 같은 정의를 PDK·사람 선언으로).

진입점: `box_verdict(rows, max_row_ratio, folds) -> BoxVerdict`.

* 행 폭 비 = max(행 폭) / min(행 폭) -- 허용치 `max_row_ratio` 는 사람 선언(기본값 없음). 행 폭은 부르는 쪽이
  sum(nf x (L + PDK finger 여유)) 로 낸 값(옛 `pitch` 의 전역 overhead 0.0 리터럴 대신 PDK 선언).
* 길이 비 = max(전체 폭, 전체 높이) / min(...), 전체 폭 = 최대 행 폭, 전체 높이 = 행 높이(finger_w) 합 -- 보고만 한다.
"""
from .contract_output import BoxVerdict


def box_verdict(rows, max_row_ratio, folds):
    """`rows`: ((행 id, 폭 m, 높이 m), ...) 비어 있지 않음. `folds`: 적용한 행 접기 기록(그대로 결과에 옮긴다)."""
    ordered = sorted(rows, key=lambda r: (r[1], r[0]))
    narrowest, widest = ordered[0], ordered[-1]
    width_ratio = widest[1] / narrowest[1]
    total_width = widest[1]
    total_height = sum(r[2] for r in rows)
    elongation = max(total_width, total_height) / min(total_width, total_height)
    return BoxVerdict(width_ratio <= max_row_ratio, width_ratio, max_row_ratio, elongation, total_width, total_height,
                      widest[0], narrowest[0], tuple(folds))
