# -*- coding: utf-8 -*-
"""`probe_parasitic_pm_all_circuits`(2026-09-10, §7.11) 승격본 -- `parasitic_pm_deg`의 일반성.

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1 P3, spec card `20260923-probe-promote-clean`.

원본 probe가 잰 두 가지 중 **판정이 서는 것**은 '일반성 검증' 쪽이다:

1. 신호경로가 **선언**(metric spec의 `excite`/`sense_p`/`sense_n`)에서 나오고, 그 경로는 여기점·감지점·
   레일을 뺀 **내부 노드**만 담는다(선언 원문: "신호경로(excite->sense) 위의 내부 노드만 센다").
2. 경로 노드는 **하나도 빠짐없이** 분류된다 -- pole을 셀 수 있거나, 저임피던스라 빼거나, 못 센다
   (`undetermined`). probe가 던진 질문 "`undetermined`가 다른 회로에서도 0인지"가 그대로 판정이다.
3. 그 결과인 `parasitic_pm_deg`는 **셀 수 있는 pole 수**가 정하는 구간 안에 있다. 선언된 정의
   `PM = 90 - sum_nodes atan(w_c/w_pole)`과 atan의 치역(0..90도)이 구간을 준다. probe docstring이
   적은 고장(경로 선언 없이 전 노드를 세면 -1004도)은 이 구간 밖이다.

**옮기지 않은 절**(spec card 계약 4·5):
* `folded_cascode`·`nmcnr_amplifier`의 경로 -- 이 두 회로는 경로를 **선언하지 않는다**. probe는 넷
   이름에서 경로를 '★제안'했을 뿐이고, probe docstring이 "경로 판정은 회로위상 해석이라 사용자 확인 후에
   선언으로 넣는다"고 못박았다. 선언이 없는 것을 test가 지어내면 그 test의 기대값은 내가 만든 회로해석이
   된다 -- 옮기지 않는다(사용자 결정 대기).
* `f_c`(`omega_c`)와 PM 표 자체 -- `omega_c`를 선언한 회로가 하나뿐이라 회로 간 비교표는 진단이다.
  PM은 선언한 회로에서 위 3의 구간 판정으로만 본다.
* 사이징 시간·캐시 재사용 메시지 -- 진단 출력이다.
"""
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _library_sized_contexts as lsc  # noqa: E402
import sizing_recipe as sr  # noqa: E402

_PM_DEG_AT_ZERO_LAG = 90.0   # 선언된 정의 PM = 90 - sum(...) 의 앞항(§7.11)
_MAX_LAG_PER_POLE_DEG = 90.0  # atan(x)의 치역 상한 -- pole 하나가 먹을 수 있는 위상의 상한


def declared_paths(topo_json):
    """선언에서 읽은 (metric 이름, 여기 노드, 감지 노드) -- 경로를 이 파일이 지어내지 않는다.

    * 여기 노드: `excite`에서 **0이 아닌** 단자만(0으로 여기된 단자는 AC 접지라 신호원이 아니다 --
      원본 probe docstring과 같은 규칙).
    * 감지 노드: `sense_p`/`sense_n` 중 `supply_nets` 선언에 없는 것(레일은 감지점이 아니라 기준이다).
    """
    supplies = lsc.declared_supply_nets(topo_json)
    out = []
    for name, spec in sorted(lsc.declared_metrics(topo_json).items()):
        if not (isinstance(spec, dict) and spec.get("excite") and spec.get("sense_p")):
            continue
        sources = {net for net, weight in spec["excite"].items() if weight}
        sinks = {net for net in (spec.get("sense_p"), spec.get("sense_n")) if net} - supplies
        out.append((name, sources, sinks, spec))
    return out


def assert_signal_path_is_interior(label, path, sources, sinks, supplies):
    """판정: 신호경로는 비어 있지 않고, 여기점·감지점·레일을 담지 않는다(내부 노드만)."""
    assert path, "%s: 신호경로가 비었다 -- 여기점에서 감지점에 닿지 못한다" % label
    endpoints = (set(sources) | set(sinks) | set(supplies)) & set(path)
    assert not endpoints, (
        "%s: 경로에 내부 노드가 아닌 것이 들어 있다 %s (여기점·감지점·레일은 세지 않는다)"
        % (label, sorted(endpoints)))


def assert_path_grows_with_sink_set(label, smaller, larger):
    """판정: 감지점을 더하면 경로는 줄지 않는다(도달가능성의 단조성)."""
    lost = set(smaller) - set(larger)
    assert not lost, (
        "%s: 감지점을 더했는데 경로에서 빠진 노드가 있다 %s -- 도달가능성이 단조가 아니다"
        % (label, sorted(lost)))


def assert_pole_report_partitions_path(label, report, path):
    """판정: 경로 노드는 정확히 한 번 분류된다(셈/제외/못셈), 못 센 노드는 없다, pole은 유한·양수다."""
    buckets = {"poles": set(report["poles"]),
               "skipped_low_impedance": set(report["skipped_low_impedance"]),
               "undetermined": set(report["undetermined"])}
    covered = set().union(*buckets.values())
    assert covered == set(path), (
        "%s: 분류에서 빠진 노드 %s / 경로 밖인데 분류된 노드 %s"
        % (label, sorted(set(path) - covered), sorted(covered - set(path))))
    names = sorted(buckets)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            overlap = buckets[first] & buckets[second]
            assert not overlap, "%s: %s와 %s에 같이 들어간 노드 %s" % (label, first, second, sorted(overlap))
    assert not buckets["undetermined"], (
        "%s: 고임피던스인데 용량을 못 세는 노드 %s -- 이 노드의 pole은 PM에서 조용히 빠진다"
        % (label, sorted(buckets["undetermined"])))
    bad = sorted((node, w) for node, w in report["poles"].items()
                 if not (math.isfinite(w) and w > 0.0))
    assert not bad, "%s: pole 주파수가 유한·양수가 아니다 %s" % (label, bad)


def assert_parasitic_pm_within_pole_count_bound(label, pm_deg, n_poles):
    """판정: PM은 pole 수가 정하는 구간 안이다.

    선언된 정의(§7.11) `PM = 90 - sum_nodes atan(w_c/w_pole)`에서 각 항은 0..90도 사이이므로
    PM은 `(90 - 90*n, 90)` 안이어야 한다. 이 두 끝은 정의와 atan 치역이 주는 것이지 측정값이 아니다.
    """
    assert n_poles >= 1, "%s: 셀 수 있는 pole이 없으면 PM은 기생 pole을 아무것도 말하지 않는다" % label
    assert pm_deg is not None and math.isfinite(pm_deg), "%s: PM이 유한하지 않다(%r)" % (label, pm_deg)
    assert pm_deg < _PM_DEG_AT_ZERO_LAG, (
        "%s: PM=%.3f도 -- pole이 %d개인데 위상이 하나도 안 깎였다" % (label, pm_deg, n_poles))
    floor = _PM_DEG_AT_ZERO_LAG - _MAX_LAG_PER_POLE_DEG * n_poles
    assert pm_deg > floor, (
        "%s: PM=%.3f도가 pole %d개의 하한 %.3f도보다 낮다 -- 신호경로 밖 노드까지 센 것이다"
        % (label, pm_deg, n_poles, floor))


def _declared_path_circuits():
    """선언된 경로가 있는 회로만 (key, circuit, 경로 선언 목록)."""
    out = []
    for key, circuit in sorted(lsc.sized_circuits().items()):
        paths = declared_paths(circuit.topology)
        if paths:
            out.append((key, circuit, paths))
    return out


def test_declared_signal_path_is_interior_and_monotone_in_sink_set():
    """선언된 경로마다 신호경로가 내부 노드만 담고, 감지점을 더하면 줄지 않는다.

    oracle 대조: (a) 구성·그래프 불변식 -- 여기점/감지점/레일은 입력에서 정해지므로 "경로가 그것들을
    담지 않는다"와 "감지점을 늘리면 경로가 줄지 않는다"는 엔진 출력을 보지 않고도 참이어야 하는 성질이다.
    (d) 경로의 출처는 topology의 metric 선언(`excite`/`sense_p`/`sense_n`)과 `supply_nets` 선언(DEC-60)이다.
    """
    checked = 0
    for key, circuit, paths in _declared_path_circuits():
        by_device, _passives = sr._load_full_topology_cached(circuit.topology_path)
        supplies = lsc.declared_supply_nets(circuit.topology)
        for metric_name, sources, sinks, spec in paths:
            label = "%s/%s" % (key, metric_name)
            full = sr.signal_path_nodes(by_device, sources, sinks)
            assert_signal_path_is_interior(label, full, sources, sinks, supplies)
            single = sr.signal_path_nodes(by_device, sources, {spec["sense_p"]})
            assert_path_grows_with_sink_set(label, single, full)
            checked += 1
    assert checked, "경로를 선언한 metric이 하나도 없다 -- 이 판정이 무동작이다"


def test_signal_path_judgment_rejects_unreachable_and_endpoint_nodes():
    """합성 반례: 닿을 수 없는 감지점(없는 넷)은 빈 경로를 내고, 여기점이 섞인 경로와 단조성이 깨진
    경로를 판정이 거부한다.

    oracle 대조: (a) 구성 -- 넷리스트에 없는 이름은 정의상 도달 불가이고, 여기점 집합은 내가 준 입력이다.
    판정이 '통과만' 하는 게 아니라 실제로 거부하는 것을 보인다(계획 N4.2 V7 취지).
    """
    candidates = _declared_path_circuits()
    assert candidates, "경로를 선언한 회로가 없다"
    key, circuit, paths = candidates[0]
    by_device, _passives = sr._load_full_topology_cached(circuit.topology_path)
    metric_name, sources, sinks, _spec = paths[0]
    supplies = lsc.declared_supply_nets(circuit.topology)
    ghost = sr.signal_path_nodes(by_device, sources, {"__no_such_net__"})
    assert not ghost, "%s: 없는 넷을 감지점으로 줬는데 경로가 나왔다 %s" % (key, sorted(ghost))
    with pytest.raises(AssertionError):
        assert_signal_path_is_interior("합성 반례(없는 넷)", ghost, sources, {"__no_such_net__"}, supplies)
    with pytest.raises(AssertionError):
        assert_signal_path_is_interior(
            "합성 반례(여기점이 경로에)", sorted(sources), sources, sinks, supplies)
    with pytest.raises(AssertionError):
        assert_path_grows_with_sink_set("합성 반례(단조성 깨짐)", {"A", "B"}, {"A"})


def test_node_pole_estimate_classifies_every_declared_path_node():
    """사이징된 회로에서 경로 노드가 빠짐없이 분류되고, 못 세는 노드가 없다.

    oracle 대조: (a) 구성 -- 입력으로 준 경로 노드 집합이 곧 분류 결과의 합집합이어야 한다(조용한 누락
    금지). `undetermined == 0`은 원본 probe가 일반성 질문으로 적은 성질이다. pole 주파수 값 자체는
    기대값으로 쓰지 않는다 -- 유한·양수만 본다.
    """
    judged = []
    for key, circuit, paths in _declared_path_circuits():
        if not circuit.sized_ok:
            continue
        by_device, _passives = sr._load_full_topology_cached(circuit.topology_path)
        seen = set()
        for metric_name, sources, sinks, _spec in paths:
            path = frozenset(sr.signal_path_nodes(by_device, sources, sinks))
            if path in seen:
                continue
            seen.add(path)
            report = sr.node_pole_estimate(by_device, circuit.ctx.sized, circuit.spec, only=set(path))
            judged.append(("%s/%s" % (key, metric_name), report, path))
    assert judged, "사이징되고 경로가 선언된 회로가 없다 -- 이 판정이 무동작이다"
    for label, report, path in judged:
        assert_pole_report_partitions_path(label, report, path)


def test_pole_partition_judgment_rejects_dropped_and_double_counted_nodes():
    """합성 반례: 노드를 빠뜨리거나 두 갈래에 겹쳐 넣거나 못 센 노드를 남기면 판정이 거부한다.

    oracle 대조: (a) 구성 -- 분류표를 손으로 만들어 넣는다. 세 결함 모양 전부를 하나씩 보인다.
    """
    path = {"n1", "n2", "n3"}
    good = {"poles": {"n1": 1.0e9}, "skipped_low_impedance": ["n2", "n3"], "undetermined": []}
    assert_pole_report_partitions_path("합성 정상", good, path)
    with pytest.raises(AssertionError):
        assert_pole_report_partitions_path(
            "합성 반례(누락)", {"poles": {"n1": 1.0e9}, "skipped_low_impedance": ["n2"],
                            "undetermined": []}, path)
    with pytest.raises(AssertionError):
        assert_pole_report_partitions_path(
            "합성 반례(중복)", {"poles": {"n1": 1.0e9, "n2": 2.0e9},
                            "skipped_low_impedance": ["n2", "n3"], "undetermined": []}, path)
    with pytest.raises(AssertionError):
        assert_pole_report_partitions_path(
            "합성 반례(못셈)", {"poles": {"n1": 1.0e9}, "skipped_low_impedance": ["n2"],
                            "undetermined": ["n3"]}, path)
    with pytest.raises(AssertionError):
        assert_pole_report_partitions_path(
            "합성 반례(음수 pole)", {"poles": {"n1": -1.0e9}, "skipped_low_impedance": ["n2", "n3"],
                                "undetermined": []}, path)


def test_parasitic_pm_stays_within_pole_count_bound():
    """`parasitic_pm_deg`를 선언한 회로에서 PM이 pole 수가 정하는 구간 안에 있다.

    oracle 대조: (d)·(a) -- 구간의 두 끝은 topology가 선언한 정의(`PM = 90 - sum atan(w_c/w_pole)`)와
    atan 치역에서 나온다. PM 값 자체를 기대값으로 박지 않는다(사이징이 바뀌면 값은 바뀌고 구간은 그대로다).
    """
    judged = []
    for key, circuit, paths in _declared_path_circuits():
        if not circuit.sized_ok:
            continue
        by_device, _passives = sr._load_full_topology_cached(circuit.topology_path)
        for metric_name, sources, sinks, spec in paths:
            if spec.get("type") != "parasitic_pm_deg":
                continue
            path = sr.signal_path_nodes(by_device, sources, sinks)
            report = sr.node_pole_estimate(by_device, circuit.ctx.sized, circuit.spec, only=path)
            judged.append(("%s/%s" % (key, metric_name), circuit.metrics.get(metric_name),
                           len(report["poles"])))
    assert judged, "parasitic_pm_deg를 선언하고 사이징된 회로가 없다 -- 이 판정이 무동작이다"
    for label, pm_deg, n_poles in judged:
        assert_parasitic_pm_within_pole_count_bound(label, pm_deg, n_poles)


def test_parasitic_pm_judgment_rejects_out_of_band_values():
    """합성 반례: 경로 밖 노드까지 센 PM(하한 밑)과 위상이 안 깎인 PM(상한 위)을 판정이 거부한다.

    oracle 대조: (a) 구성 -- pole 수 n에 대해 하한 `90-90n`보다 1도 낮은 값, 상한 `90`과 같은 값을
    만들어 넣는다. probe docstring이 적은 고장(경로 선언 없이 전 노드를 세면 -1004도)이 앞의 모양이다.
    """
    n_poles = 4
    floor = _PM_DEG_AT_ZERO_LAG - _MAX_LAG_PER_POLE_DEG * n_poles
    assert_parasitic_pm_within_pole_count_bound("합성 정상", (floor + _PM_DEG_AT_ZERO_LAG) / 2.0, n_poles)
    with pytest.raises(AssertionError):
        assert_parasitic_pm_within_pole_count_bound("합성 반례(하한 밑)", floor - 1.0, n_poles)
    with pytest.raises(AssertionError):
        assert_parasitic_pm_within_pole_count_bound(
            "합성 반례(안 깎임)", _PM_DEG_AT_ZERO_LAG, n_poles)
    with pytest.raises(AssertionError):
        assert_parasitic_pm_within_pole_count_bound("합성 반례(pole 0개)", 80.0, 0)
    with pytest.raises(AssertionError):
        assert_parasitic_pm_within_pole_count_bound("합성 반례(값 없음)", None, n_poles)
