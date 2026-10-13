"""S1v 기록 읽기 -- `graph/s1v` 필드에서 뷰 안팎 기록과 그 심각도별 묶음을 꺼낸다 (설계 40 §2.4.8 v1.9.1 D1, 41 §1, DEC-59).

진입점: `s1v_findings(source) -> (all_findings, review_needed, unsupported)`.

* `source` = S1v 필드가 있는 스냅샷 또는 `S1Graph`(`value(kind, key, field)` 질의). 필드가 곧 정본이다 -- 기록을 다른 객체에 옮겨 담지 않고 부를 때 필드에서 읽는다.
* `all_findings` = 뷰 밖 기록(`graph/s1v: findings`) + 뷰 순서대로 각 뷰의 기록, `review_needed` = severity 가 review_needed 인 것(GB4 앞 정지 대상, DEC-59 안전망),
  `unsupported` = severity 가 unsupported_rule_branch 인 것(`기록만` 분기 -- 항상 탐색 전 정지).
"""
from .s1_values import S1V_KEY
from .s1v_values import SEVERITY_REVIEW, SEVERITY_UNSUPPORTED


def s1v_findings(source):
    every = tuple(source.value("graph", S1V_KEY, "findings")) + tuple(f for v in source.value("graph", S1V_KEY, "views") for f in v.findings)
    return (every, tuple(f for f in every if f.severity == SEVERITY_REVIEW), tuple(f for f in every if f.severity == SEVERITY_UNSUPPORTED))
