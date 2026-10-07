"""spec 성능 제약(ss 영역 등, 목적 축 밖) 행 -- MOD5 `ss_linearize` 연결 자리 (오케스트레이터 결정 2026-10-08 S-1, 설계 5절
'metric 선언' 행, DEC-67·74, NFR-5).

진입점: `ss_constraint_rows(evaluation, declared) -> (rows, unmeasured)`.

* `declared` = ((metric, op, value), ...) -- spec `judged_constraints` 중 목적 축(power_dc_w·area_search_m2) 밖 제약
  (`build_search_context` 가 나눈다).
* ss 값은 봉인된 스냅샷에서만 계산한다(DEC-67 -- `ss_linearize` 는 SealedSnapshot 만 받는다). 그래서:
  - `evaluation.sealed is None`(봉인 7 대기 포함) -> 행 없음, 모든 선언을 `unmeasured`(사유 `ss_requires_sealed_snapshot`).
  - 봉인됨 -> ★ 연결 자리: metrics `ss_linearize`(브랜치 ng-sslin, 아직 `gmid_engine.metrics.__all__` 밖)가 들어오면 아래
    `_UNAVAILABLE` 분기 한 곳을 'ss_linearize(evaluation.sealed, …) -> metric_value(name, …) -> 행 (값 − 목표)/s 또는
    (목표 − 값)/s, s = NFR-5 여유 바닥(그 metric 의 격자 분해능; 모델 오차 미측정이면 격자 분해능 + 여유 판정 보류)'로 바꾼다.
    그때까지 사유 `ss_linearize_unavailable` 로 `unmeasured` 에 남긴다(빠뜨리지 않는다 -- 통과로 세지 않는다).
* `unmeasured` = ((metric, op, 사유), ...) 선언 순서.
"""
_NOT_SEALED = "ss_requires_sealed_snapshot"
_UNAVAILABLE = "ss_linearize_unavailable"


def ss_constraint_rows(evaluation, declared):
    if not declared:
        return (), ()
    reason = _NOT_SEALED if evaluation.sealed is None else _UNAVAILABLE
    return (), tuple((metric, op, reason) for metric, op, _value in declared)
