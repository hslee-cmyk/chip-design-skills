# -*- coding: utf-8 -*-
"""`probe_role_L_derivation`(2026-09-10) 승격본 -- `L_role` 상수를 유도로 대체한 결과, 4개 회로 전수.

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1 P3, spec card `20260923-probe-promote-clean`.

원본 probe는 표만 만들었다("**아무것도 고치지 않는다 -- 표만 만든다**"). 그 표의 세 열 중 판정이 서는 것:

1. '출처' 열 -- `_L_source`가 `L_role_derived`인가(유도), `L_role`인가(**상수 폴백**). 옛 상수
   `_L_ROLE_MULTIPLIERS`는 삭제됐으므로 폴백이 남아 있으면 안 된다.
2. '최종 L' 열 -- 유도된 L은 **선언된 L 후보 구간** 안에 있어야 한다(값을 지어내지 않는다).
3. '★ 사이징 실패' 줄 -- 실패는 **명시적 거부**여야 한다(조용한 기본값 대입 금지, 계획 §3.2 P1).

**옮기지 않은 절**(spec card 계약 4):
* '옛 상수' 열(`_OLD_MULT`로 재현한 `L_min x 1.2`) -- 비교 기준이 이미 삭제된 코드라 지켜야 할 성질이
  아니다. 그 상수를 test에 다시 적으면 삭제한 식을 test가 되살리는 것이다(V4 규칙 (2)).
* 'knee / 창 lo / 창 hi' 열과 'clamp됨' 비고 -- clamp 규칙(`L = clamp(knee, feasible_L_window)`)의
  판정은 이미 `unit/test_selftest_sizing_recipe.py::test_s024_section`이 toy LUT 위에서 양방향으로
  한다. 여기서 같은 식을 회로마다 다시 계산하면 엔진 식을 test에 재서술하는 것이 된다(V4 규칙 (2)).
  이 파일이 더하는 것은 그 규칙의 **library 전수 적용**(회로 이름을 박지 않는다)이다.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _library_sized_contexts as lsc  # noqa: E402
import sizing_recipe as sr  # noqa: E402

_DERIVED_SOURCE = "L_role_derived"


def declared_L_roles(topo_json):
    """소자 -> 선언된 `L_role`(선언이 있는 소자만)."""
    roles = (topo_json.get("device_roles") or {})
    return {name: decl["L_role"] for name, decl in roles.items()
            if isinstance(decl, dict) and decl.get("L_role")}


def assert_L_roles_are_derivable(label, roles_by_device, derivable):
    """판정: 선언된 `L_role`은 전부 엔진이 **유도 목표를 가진** 역할이다."""
    unknown = sorted({(name, role) for name, role in roles_by_device.items() if role not in derivable})
    assert not unknown, (
        "%s: 엔진이 유도하지 않는 L_role 선언 %s -- 유도 목표가 있는 역할은 %s 뿐이다(나머지는 theta 담당)"
        % (label, unknown, sorted(derivable)))


def assert_role_L_is_derived_and_declared(label, entries, L_candidates):
    """판정: `L_role`이 정한 L은 (1) 상수 폴백이 아니라 유도이고 (2) 선언된 L 후보 구간 안이다."""
    lo, hi = min(L_candidates), max(L_candidates)
    fallback = sorted(name for name, entry in entries if entry.get("_L_source") != _DERIVED_SOURCE)
    assert not fallback, (
        "%s: L_role이 유도(%s)가 아니라 다른 출처로 떨어진 소자 %s -- 옛 상수 폴백은 삭제됐다"
        % (label, _DERIVED_SOURCE, fallback))
    outside = sorted((name, entry.get("L")) for name, entry in entries
                     if not (entry.get("L") is not None and lo <= entry["L"] <= hi))
    assert not outside, (
        "%s: 유도된 L이 선언된 L 후보 구간 [%.4g, %.4g]m 밖이다: %s" % (label, lo, hi, outside))


def assert_refusals_are_explicit(refusals):
    """판정: 사이징이 안 되는 회로는 **명시적으로** 거부한다(조용한 폴백·무동작이 아니다)."""
    silent = [(key, type(exc).__name__, str(exc)) for key, exc in refusals
              if not (isinstance(exc, ValueError) and str(exc).strip())]
    assert not silent, (
        "사이징 거부가 명시적이지 않다(ValueError 계열 + 사유 문장이어야 한다): %s" % silent)


def test_every_declared_L_role_is_one_the_engine_derives():
    """library 전 회로에서 선언된 `L_role`이 엔진의 유도 목표 표에 있는 역할이다.

    oracle 대조: (a)·(d) -- 기대값은 엔진이 선언한 유도 목표 표(`_L_ROLE_TARGETS`)의 **키 집합**이고,
    입력은 topology 선언이다. 엔진을 불러 나온 L 값은 기대값으로 쓰지 않는다. 원본 probe가 표의 '목표점'
    열로 찍기만 하던 대응(role -> 목표점)을 "선언된 역할은 전부 목표점이 있어야 한다"로 판정한다.
    """
    derivable = set(sr._L_ROLE_TARGETS)
    assert derivable, "엔진이 유도 목표를 하나도 선언하지 않았다"
    declared_total = 0
    for path in lsc.library_topology_paths():
        roles_by_device = declared_L_roles(lsc.topology_json(path))
        declared_total += len(roles_by_device)
        assert_L_roles_are_derivable(os.path.basename(path), roles_by_device, derivable)
    assert declared_total, "library에 L_role 선언이 하나도 없다 -- 이 판정이 무동작이다"


def test_declared_L_role_is_rejected_when_theta_owned_or_unknown():
    """합성 반례: theta가 담당하는 역할(cascode/signal)이나 없는 역할을 선언하면 판정이 거부한다.

    oracle 대조: (a) 구성 -- 역할 이름을 유도 목표 표 **밖**에서 고르면 그 자체가 반례다.
    `cascode`·`signal`은 엔진이 `derive_role_L()`에서 거부하는 역할이고(theta 탐색 담당), 세 번째는
    아예 없는 이름이다.
    """
    derivable = set(sr._L_ROLE_TARGETS)
    for bad in ("cascode", "signal", "no_such_role"):
        assert bad not in derivable, "반례로 고른 %s 가 실제로는 유도 가능한 역할이다" % bad
        with pytest.raises(AssertionError):
            assert_L_roles_are_derivable("합성 반례", {"Mx": bad}, derivable)


def test_role_L_is_derived_for_every_harness_circuit():
    """하네스가 선언한 회로 전수에서 `L_role` 소자의 L이 유도로 정해지고 선언 구간 안에 있다.

    oracle 대조: (a)·(d) -- 판정 기준은 (i) 출처 문자열이 유도(`L_role_derived`)라는 선언과 (ii) L이
    spec의 `L_candidates` 선언 구간 안이라는 구성 사실이다. 어떤 L 값도 기대값으로 박지 않는다(회로마다
    다르고, 달라져도 이 판정은 그대로다). 사이징이 안 되는 회로는 그 자체가 판정 대상이다 -- 거부가
    명시적이어야 한다. 원본 probe의 '유도 성공 N개 / 상수 폴백 N개' 요약 줄이 이 판정이다.
    """
    circuits = lsc.sized_circuits()
    assert circuits, "run_harness.SPECS에 회로가 없다 -- 이 판정이 무동작이다"
    judged, refusals = [], []
    for key, circuit in sorted(circuits.items()):
        if circuit.sized_ok:
            judged.append((key, circuit.role_L_entries(), circuit.spec["L_candidates"]))
        else:
            refusals.append((key, circuit.refusal))
    assert any(entries for _key, entries, _cands in judged), (
        "사이징된 회로 중 L_role이 L을 정한 소자가 하나도 없다 -- 이 판정이 무동작이다(사이징 %d/%d 성공)"
        % (len(judged), len(circuits)))
    for key, entries, candidates in judged:
        assert_role_L_is_derived_and_declared(key, entries, candidates)
    assert_refusals_are_explicit(refusals)


def test_role_L_judgment_rejects_constant_fallback_and_out_of_range_L():
    """합성 반례: 상수 폴백 출처와 선언 구간 밖 L, 그리고 조용한 거부를 판정이 거부한다.

    oracle 대조: (a) 구성 -- 출처 문자열을 유도가 아닌 값으로, L을 후보 구간 밖 값으로 **만들어** 넣는다.
    (구간은 합성 입력 자체가 정한다: [1e-7, 1e-6]에 대해 2e-6은 정의상 밖이다.)
    """
    candidates = [1e-7, 5e-7, 1e-6]
    good = [("Mok", {"_L_source": "L_role_derived", "L": 5e-7})]
    assert_role_L_is_derived_and_declared("합성 정상", good, candidates)
    with pytest.raises(AssertionError):
        assert_role_L_is_derived_and_declared(
            "합성 반례(상수 폴백)", [("Mx", {"_L_source": "L_role", "L": 5e-7})], candidates)
    with pytest.raises(AssertionError):
        assert_role_L_is_derived_and_declared(
            "합성 반례(구간 밖)", [("Mx", {"_L_source": "L_role_derived", "L": 2e-6})], candidates)
    with pytest.raises(AssertionError):
        assert_role_L_is_derived_and_declared(
            "합성 반례(L 없음)", [("Mx", {"_L_source": "L_role_derived"})], candidates)
    with pytest.raises(AssertionError):
        assert_refusals_are_explicit([("합성 반례(조용한 거부)", KeyError(""))])
