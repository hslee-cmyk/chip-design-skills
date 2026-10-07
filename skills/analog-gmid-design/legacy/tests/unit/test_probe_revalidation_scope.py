# -*- coding: utf-8 -*-
"""`probe_revalidation_scope`(2026-09-08) 승격본 -- 레이아웃 재검증이 어느 metric을 건너뛰는가.

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1 P3, spec card `20260923-probe-promote-clean`.

원본 probe는 표를 찍어 결함을 기록했다: `area_um2`처럼 `devices`를 선언하지 않은 metric은 계산기가
**전 소자**를 읽는데 참조 수집기(`_collect_device_refs()`)는 빈 집합을 돌려주므로 "무관"으로 분류돼
재검증에서 조용히 빠진다. probe의 '판단' 절은 *"미수정 -- 공유 엔진 변경이라 승인 대상"*으로 끝난다.

그 뒤 엔진이 고쳐졌다(`unit/test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override`의
2026-09-08 주석: 건너뛰기 최적화 자체를 폐기하고 진단 정보는 이름이 정확한 새 키로 옮겼다). 그래서 이
파일이 옮기는 것은 probe의 '★건너뜀' 표가 아니라 **그 표가 요구하던 성질**이다:

1. 참조 수집기는 **건전**하다 -- 선언에 적힌, 실재하는 소자만 돌려준다(없는 이름을 지어내지 않는다).
2. `devices`를 선언하지 않은 metric은 참조가 비지만 값은 **전 소자에 의존**한다 -- 이름이 안 적힌 소자를
   바꾸면 값이 바뀐다.
3. 그런 metric도 재검증에서 **건너뛰지 않는다**. '참조 없음'은 진단으로만 남고(`metrics_not_
   referencing_changed_devices`) 재계산은 전부 한다.

**옮기지 않은 절**(spec card 계약 4):
* probe의 '판정' 열(`affected = refs & overrides`) 자체 -- 그 식은 폐기된 최적화의 재구현이다. test에
  다시 적으면 삭제된 엔진 식을 test가 되살린다(V4 규칙 (2)).
* "전 소자를 쓰는데 건너뛰는 metric 6개", "그중 제약 3개" 같은 그 시점의 개수 -- 선언이 바뀌면 바뀌는
  진단 수치다. 개수 대신 "그런 metric이 존재한다"만 확인하고(무동작 방지) 성질로 판정한다.
* `ALL_DEVICE_METRICS` 목록 -- probe가 손으로 적은 metric type 열거다. 엔진 레지스트리가 커지면 틀리는
  목록이라(probe docstring이 지적한 것과 같은 결함 모양) 옮기지 않는다.
"""
import copy
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _library_sized_contexts as lsc  # noqa: E402
import sizing_recipe as sr  # noqa: E402

_GHOST_DEVICE = "__no_such_device__"


def assert_device_refs_are_sound(label, spec, refs, known):
    """판정: 수집된 참조는 실재 소자뿐이고, 선언에 적힌 실재 소자는 빠지지 않는다."""
    invented = sorted(set(refs) - set(known))
    assert not invented, "%s: 넷리스트에 없는 소자를 참조로 돌려줬다 %s" % (label, invented)
    declared = {name for name in (spec.get("devices") or ()) if name in known} \
        if isinstance(spec, dict) else set()
    missing = sorted(declared - set(refs))
    assert not missing, "%s: 선언된 소자 %s 가 참조에서 빠졌다" % (label, missing)


def assert_no_metric_is_skipped(label, result, metric_names):
    """판정: 재검증은 어떤 metric도 건너뛰지 않는다 -- 전부 다시 계산한 값이 있다."""
    assert list(result["unaffected_metrics_skipped"]) == [], (
        "%s: 재계산을 건너뛴 metric이 있다 %s -- '참조가 안 보이면 무관'은 안전한 방향이 반대다"
        % (label, sorted(result["unaffected_metrics_skipped"])))
    missing = sorted(set(metric_names) - set(result["metric_deltas"]))
    assert not missing, "%s: 재계산 결과가 없는 metric %s" % (label, missing)


def assert_reference_diagnostic_discriminates(label, result, changed_devices, specs, known):
    """판정: '바뀐 소자를 참조하지 않는' 진단 목록은 실제로 가려낸다 -- 참조하는 metric은 빠진다."""
    reported = set(result["metrics_not_referencing_changed_devices"])
    for name, spec in specs.items():
        refs = sr._collect_device_refs(spec, known)
        touches = bool(refs & set(changed_devices))
        assert touches != (name in reported), (
            "%s: metric %s 의 참조 %s 와 진단 목록(%s)이 어긋난다"
            % (label, name, sorted(refs), sorted(reported)))


def test_declared_metric_device_refs_are_sound_across_library():
    """library의 모든 metric 선언에서 참조 수집이 건전하고, 참조가 빈 선언이 실제로 있다.

    oracle 대조: (a)·(d) -- 기대값은 topology 선언 그 자체(넷리스트의 소자 이름 집합, metric spec의
    `devices` 항목)에서 나온다. 엔진이 돌려준 참조 집합을 기대값으로 쓰지 않는다. '참조가 빈 선언이
    있다'는 원본 probe가 기록한 상황이 아직 실재한다는 확인이다(없으면 아래 판정이 무동작이 된다).
    """
    checked, empty_refs = 0, []
    for path in lsc.library_topology_paths():
        topo = lsc.topology_json(path)
        known = lsc.declared_device_names(topo)
        for name, spec in sorted(lsc.declared_metrics(topo).items()):
            refs = sr._collect_device_refs(spec, known)
            assert_device_refs_are_sound("%s/%s" % (os.path.basename(path), name), spec, refs, known)
            checked += 1
            if not refs:
                empty_refs.append((os.path.basename(path), name))
    assert checked, "library에 metric 선언이 없다 -- 이 판정이 무동작이다"
    assert empty_refs, (
        "참조가 비는 metric 선언이 하나도 없다 -- 원본 probe가 기록한 상황이 사라졌다(판정 재검토 필요)")


def test_device_refs_never_leak_undeclared_names():
    """합성 반례: 선언에 없는 소자 이름을 넣어도 참조로 새어 나오지 않는다.

    oracle 대조: (a) 구성 -- 넷리스트에 없는 이름을 내가 넣었으므로 '실재하지 않음'이 곧 기대값이다.
    합성 선언(실재 소자 하나 + 유령 하나)을 엔진에 넣는 것과, 판정 함수에 유령이 섞인 참조 집합을
    넣는 것 둘 다 본다.
    """
    refs = sr._collect_device_refs({"type": "sum_current", "devices": ["M1", _GHOST_DEVICE]}, {"M1"})
    assert _GHOST_DEVICE not in refs, "선언에 없는 소자 이름이 참조로 새어 나왔다: %s" % sorted(refs)
    assert "M1" in refs, "선언에 적힌 실재 소자가 참조에서 빠졌다: %s" % sorted(refs)
    with pytest.raises(AssertionError):
        assert_device_refs_are_sound(
            "합성 반례(유령 참조)", {"type": "sum_current", "devices": ["M1"]},
            {"M1", _GHOST_DEVICE}, {"M1"})
    with pytest.raises(AssertionError):
        assert_device_refs_are_sound(
            "합성 반례(선언 누락)", {"type": "sum_current", "devices": ["M1", "M2"]}, {"M1"}, {"M1", "M2"})


def _two_device_context(lut):
    """구성 입력: 소자 둘(M1, M3)짜리 ctx. 값은 LUT로 정합하게 만들고 판정 대상이 아니다."""
    L, vds = 0.5e-6, 0.6
    r1 = sr.size_transistor(gm=200e-6, gm_id=12.0, L=L, lut=lut, vds=vds)
    r3 = sr.size_transistor(gm=80e-6, gm_id=10.0, L=L, lut=lut, vds=vds)
    gds1 = r1.gm / lut.gm_gds_ratio(12.0, L, vds, 0.0)
    return sr.SizingContext(sized={
        "M1": {"ID": r1.ID, "W": r1.W, "L": L, "gm": r1.gm, "gm_id": 12.0, "gds": gds1,
               "kind": "nmos", "vds": vds, "vsb": 0.0},
        "M3": {"ID": r3.ID, "W": r3.W, "L": L, "gm": r3.gm, "gm_id": 10.0, "gds": 1e-6,
               "kind": "nmos", "vds": vds, "vsb": 0.0},
    }), r1.W


def test_metric_without_declared_devices_depends_on_every_device(toy_lut):
    """`devices`를 선언하지 않은 metric은 이름이 안 적힌 소자를 바꿔도 값이 바뀐다.

    oracle 대조: (a) 구성 -- W를 두 배로 만든 소자(M1)는 그 metric 선언 어디에도 이름이 없다. 면적이
    소자 면적의 합이라는 것만으로 "값이 **커져야** 한다"가 정해진다(값 자체는 기대값이 아니다).
    비교 대상으로 M1을 이름으로 적은 metric은 참조가 비지 않는다는 것도 같이 본다.
    """
    ctx, _w1 = _two_device_context(toy_lut)
    implicit_all = {"type": "sum_area", "unit": "um^2"}
    known = set(ctx.sized)
    refs_implicit = sr._collect_device_refs(implicit_all, known)
    assert not refs_implicit, (
        "이 판정의 전제(선언에 소자 이름이 없어 참조가 빈다)가 깨졌다: %s" % sorted(refs_implicit))
    refs_named = sr._collect_device_refs({"type": "sum_current", "devices": ["M1"]}, known)
    assert "M1" in refs_named, "이름으로 적은 소자가 참조에 없다: %s" % sorted(refs_named)
    before = sr.compute_metric(implicit_all, ctx)
    grown = sr.SizingContext(sized=copy.deepcopy(ctx.sized))
    grown.sized["M1"]["W"] = grown.sized["M1"]["W"] * 2.0
    after = sr.compute_metric(implicit_all, grown)
    assert after > before, (
        "선언에 이름이 없는 소자(M1)의 W를 두 배로 했는데 값이 안 커졌다(%r -> %r) -- "
        "이 metric은 전 소자를 읽는다" % (before, after))


def test_revalidation_recomputes_metric_that_names_no_devices(toy_lut):
    """재검증은 참조가 빈 metric도 다시 계산하고, '참조 없음'은 진단으로만 남는다.

    oracle 대조: (a) 구성 -- 바꾸는 소자(M1)와 각 metric 선언의 소자 이름을 내가 정했으므로 어느 metric이
    '바뀐 소자를 참조하는가'는 입력이 정한다. (c) 건너뛰기 폐기 계약은 `test_s009_revalidate_finger_
    override`가 toy 2-metric에서 이미 판정한 것과 같은 계약이고, 여기서 더하는 것은 **소자 이름이 하나도
    없는 선언**(원본 probe가 문제 삼은 `area_um2` 모양)이 그 계약에 들어오는가다.
    """
    ctx, w1 = _two_device_context(toy_lut)
    known = set(ctx.sized)
    specs = {
        "implicit_all": {"type": "sum_area", "unit": "um^2"},          # 소자 이름 없음 = 전 소자
        "names_changed": {"type": "sum_current", "devices": ["M1"]},   # 바뀐 소자를 이름으로 적음
        "names_other": {"type": "sum_current", "devices": ["M3"]},     # 안 바뀐 소자만 적음
    }
    constraints = [{"metric": "names_other", "op": "<=", "value": 1.0}]
    result = sr.revalidate_finger_override(
        ctx, {"nmos": toy_lut}, {"M1": w1 * 0.9}, specs, constraints, gm_id_bounds=(2.0, 28.0))
    assert_no_metric_is_skipped("toy 구성", result, specs)
    delta = result["metric_deltas"]["implicit_all"]
    assert delta["new"] != delta["old"], (
        "M1의 W를 줄였는데 면적이 그대로다(%r) -- 재계산이 아니라 옛 값을 다시 적은 것이다" % delta)
    assert_reference_diagnostic_discriminates("toy 구성", result, {"M1"}, specs, known)
    assert ctx.sized["M1"]["W"] == w1, "revalidate_finger_override()가 원본 ctx를 변형했다"


def test_revalidation_judgment_rejects_skipped_and_mislabelled_metrics():
    """합성 반례: 건너뛴 metric이 있는 결과와, 진단 목록이 어긋난 결과를 판정이 거부한다.

    oracle 대조: (a) 구성 -- 재검증 결과 dict를 손으로 만든다. `M1`을 바꿨다고 해놓고 `M1`을 이름으로
    적은 metric을 '참조하지 않음'으로 보고하는 결과가 원본 probe가 기록한 결함 모양이다.
    """
    specs = {"implicit_all": {"type": "sum_area"}, "names_changed": {"type": "sum_current", "devices": ["M1"]}}
    known = {"M1", "M3"}
    good = {"unaffected_metrics_skipped": [],
            "metric_deltas": {"implicit_all": {"old": 1.0, "new": 2.0},
                              "names_changed": {"old": 1.0, "new": 2.0}},
            "metrics_not_referencing_changed_devices": ["implicit_all"]}
    assert_no_metric_is_skipped("합성 정상", good, specs)
    assert_reference_diagnostic_discriminates("합성 정상", good, {"M1"}, specs, known)
    skipped = dict(good, unaffected_metrics_skipped=["implicit_all"],
                   metric_deltas={"names_changed": {"old": 1.0, "new": 2.0}})
    with pytest.raises(AssertionError):
        assert_no_metric_is_skipped("합성 반례(건너뜀)", skipped, specs)
    mislabelled = dict(good, metrics_not_referencing_changed_devices=["implicit_all", "names_changed"])
    with pytest.raises(AssertionError):
        assert_reference_diagnostic_discriminates("합성 반례(진단 어긋남)", mislabelled, {"M1"}, specs, known)
