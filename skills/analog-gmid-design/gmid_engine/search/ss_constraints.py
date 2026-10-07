"""spec 성능 제약(ss 영역) 행 -- MOD5 `ss_evaluate` 결과 묶음에서 (설계 5절 'metric 선언' 행, DEC-67·74, NFR-5, 오케스트레이터
결정 2026-10-08 S-1 배선).

진입점: `ss_constraint_rows(bundle, declared) -> (rows, unmeasured)`.

* `declared` = spec `ConstraintDecl` tuple(`build_search_context` 가 고른 것: 판정 대상·값 있음·목적 축 밖·metric 레지스트리에서
  view_kind 가 있는 metric). `bundle` = 그 점의 `graph.metrics_ss` `MetricBundle`(`ss_evaluate(...).ss`), 봉인 안 된 점은 None.
* 봉인 안 된 점(None): 행 없음, 선언마다 (metric, op, "ss_requires_sealed_snapshot") -- ss 는 SealedSnapshot 에서만(DEC-67).
* 봉인 점: 선언 k 마다 요청 `MetricRequest(metric, view)` 의 결과. 값이 None(Undefined -- 수동소자 값 미선언·뷰 대기·교차 없음 등)
  이면 행 없이 `unmeasured` 에 (metric, op, Undefined code 들 '+' 로 이음) -- 통과로도 위반으로도 세지 않는다. 값이 있으면 행
  `ss:<k>:<metric><op>` c = (값 − 목표)/s(>=) 또는 (목표 − 값)/s(<=).
* 정규화 s: 설계 5절은 NFR-5 바닥 max(그 metric 격자 분해능, 모델 오차)인데 ss metric 의 '격자 분해능' 정의가 없고 모델 오차는
  미측정이다(열린 항목 S-19). 그래서 s = |목표값|(SLSQP 조건수용 축척 -- 상대 여유)이고 `active`(c ≤ 1)는 의미가 없어 False 로
  둔다(NFR-5 여유 판정 보류). 목표가 0 이면 s = 1(그 metric 단위 한 칸).
"""
from gmid_engine.metrics import MetricRequest

from .search_values import ConstraintRow

_NOT_SEALED = "ss_requires_sealed_snapshot"


def ss_constraint_rows(bundle, declared):
    if not declared:
        return (), ()
    if bundle is None:
        return (), tuple((d.metric, d.op, _NOT_SEALED) for d in declared)
    results = dict(bundle.entries)
    rows, unmeasured = [], []
    for k, d in enumerate(declared):
        res = results[MetricRequest(d.metric, d.view)]
        if res.value is None:
            unmeasured.append((d.metric, d.op, "+".join(sorted({u.code for u in res.undefined})) or "undefined"))
            continue
        scale = abs(d.value) or 1.0
        c = (res.value - d.value) / scale if d.op == ">=" else (d.value - res.value) / scale
        rows.append(ConstraintRow("ss:" + str(k) + ":" + d.metric + d.op, float(c), False))
    return tuple(rows), tuple(unmeasured)
