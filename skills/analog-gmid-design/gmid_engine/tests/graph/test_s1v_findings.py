"""graph/s1v_findings.py -- `s1v_findings(source) -> (all_findings, review_needed, unsupported)` (U17 ①-b, 규칙 H 1:1 test).

근거: 설계 40 v1.9.1 §2.4.2 '읽기: 소비자는 S0 수준 스냅샷의 필드를 읽는다', §2.4.8 D1(graph/s1v: findings 는 뷰 밖 기록, 뷰 안 기록은 views[*].findings),
41 §1 DEC-59(review_needed 는 GB4 앞 정지 대상, unsupported_rule_branch 는 `기록만` 분기 -- 탐색 전 정지).
oracle (a): 손으로 만든 필드 값(뷰 밖 기록 + 뷰 순서 기록)에서 순서·분류를 손으로 적는다. oracle (d): 손 회로의 진단 결과는 severity 정의와 같은 분할.
"""
from __future__ import annotations

from types import SimpleNamespace

from gmid_engine.graph import Finding, s1v_findings

import s1v_hand as H


def _f(code, severity):
    return Finding(code, severity, "", (), "", ())


class _Source:
    """`value(kind, key, field)` 질의만 하는 손 스냅샷 -- graph/s1v 의 findings·views 두 필드."""

    def __init__(self, findings, views):
        self._v = {("graph", "s1v", "findings"): findings, ("graph", "s1v", "views"): views}

    def value(self, kind, key, field):
        return self._v[(kind, key, field)]


def test_order_outside_first_then_views_in_order_and_severity_split():
    a, b, c, d = _f("a", "review_needed"), _f("b", "unsupported_rule_branch"), _f("c", "info"), _f("d", "review_needed")
    src = _Source((a,), (SimpleNamespace(findings=(b, c)), SimpleNamespace(findings=(d,))))
    every, review, unsupported = s1v_findings(src)
    assert every == (a, b, c, d)
    assert review == (a, d)
    assert unsupported == (b,)


def test_empty_fields_give_empty_tuples():
    assert s1v_findings(_Source((), ())) == ((), (), ())


def test_hand_circuit_partition_matches_severity(tmp_path):
    # XCOUP 은 loop_record_only(unsupported) 를 낸다(test_s1v_build STOPPERS) -- 진단 모드 필드에서 같은 분할
    s1, s1v = H.build(tmp_path, H.XCOUP)
    every, review, unsupported = s1v_findings(s1v.graph)
    expected_all = tuple(s1v.findings) + tuple(f for v in s1v.views for f in v.findings)
    assert every == expected_all
    assert review == tuple(f for f in expected_all if f.severity == "review_needed")
    assert unsupported == tuple(f for f in expected_all if f.severity == "unsupported_rule_branch")
    assert "loop_record_only" in [f.code for f in unsupported]
