"""모델 오차 계산 블록 -- 오라클 대조 모델 오차 ((metric, 값), ...) 을 S0 수준 필드 `graph/kernel: model_error` 에 쓴다
(설계 40 §2.4.7 'SearchContext 칸 배정'·§2.4.8, DEC-72, 체크리스트 D-GB8c).

진입점: `model_error_field`(`@compute_block`, writer `model_error`) -- `model_error_field(snapshot, pairs)`.

* extras: `pairs` = ((metric, 크기), ...) -- spec `derived.model_error_<metric>` 선언에서 `model_error_pairs` 가 만든 값(부르는 쪽 `build_search_context(model_error=)` 가 넘긴다).
  metric 이름순으로 정규화해 쓴다. 소비자: `ss_constraint_rows` 분해능 바닥(NFR-5)·`find_front` '모델 오차 미측정' 판정 보류 해제.
"""
from gmid_engine.core import compute_block
from gmid_engine.sizing import KERNEL_KEY

from .s0_fields import MODEL_ERROR_WRITER, MODEL_ERROR_WRITES


@compute_block(MODEL_ERROR_WRITER, writes=MODEL_ERROR_WRITES)
def model_error_field(projection):
    (pairs,) = projection.extras
    return {("graph", "model_error"): {KERNEL_KEY: tuple(pairs)}}
