# -*- coding: utf-8 -*-
"""`probe_prevention_wiring`(2026-09-08) C4 승격본 -- diode 판정과 diode 동작점이 role 라벨이 아니라 물리를 따르는가.

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1 P3(대조형 -- 재구현을 oracle로 유지),
spec card `20260923-probe-promote-differential`.

## 배경(원본 probe C4에서)

계획 §3.3 C4 '물리 판정이 항상 우선'. 원본 probe는 물리적으로 같은 diode-connected 소자 16개(파일럿)의
`headroom_role`이 4종(cascode / mirror / voltage_divider / diode_reference)으로 흩어져 있다는 것을 찍고, "role
라벨을 전부 제거해도 결과가 같아야 한다"를 목표 test로 적었다.

## 독립 쪽이 엔진 코드를 옮겨 적은 것이 아닌 근거(spec card 계약 3)

* 독립 쪽: `gate == drain` -- **회로 물리의 diode 정의**(게이트와 드레인이 같은 넷)를 topology.json의 `netlist`
  원문에 직접 적용한다(`gate_equals_drain`). 엔진의 로더(`load_topology`)도, 분류 함수도 거치지 않는다.
* 엔진(피검): `load_topology`가 만든 소자에 `is_diode_connected`를 적용한 분류, 그리고 사이징 파이프라인이 낸 diode의
  동작점(`vds`, `gm_id`, `L`, `vsb`). 엔진의 이 분기들은 role 라벨(`headroom_role`)을 함께 받는 경로에 있다.
* 판정은 두 쪽의 **차이가 뜻하는 성질**이다(계약 4): (1) 라벨을 바꾸거나 지우거나 거짓 라벨을 붙여도 엔진 분류는
  물리 정의와 같다(라벨 불변). (2) 물리 diode는 라벨이 무엇이든 VGS = VDS(게이트와 드레인이 같은 노드라는 KVL)를
  만족한다 -- 사이징된 (gm_id, L, vds, vsb)에서 VGS를 LUT로 되읽어 VDS와 비교한다.

## 옮기지 않은 절(계약 5 -- 판정을 세울 수 없다)

* C4의 `_feed_vds_fallback(None, role, min_vds_by_role)` 비교(cascode 0.2 / mirror 0.3 / 라벨 없음 0.6): 그 함수는
  **role로 최소 VDS를 고르는 것이 목적**인 대체값 함수라 role에 따라 값이 다른 것은 결함이 아니다. C4의 목표(물리
  우선)가 지켜지는지는 그 대체값이 아니라 **diode의 최종 동작점**에서 보인다 -- 아래 판정 (2)가 그것이다.
* C5(게이트류 함수의 docstring에 '검사하지 않는 것'이 있는가): 정적 문서 규약 측정이다. 원본도 "위반"으로
  기록했고 이 card는 test-only라 엔진 docstring을 바꾸지 않는다 -- 지금 통과하는 판정을 세울 수 없고, 실패하는
  test를 들이는 것은 이 card의 범위(대조형 승격)가 아니다.
* C2(`["vds"] =` 원시 대입 수): 엔진 소스 문자열의 개수를 찍는 측정이고 기준값이 없다(원본도 "0곳"을 출력 문자열로
  박았을 뿐 판정하지 않았다). 순서 셔플 불변은 `--shuffle-seed` 실행이 따로 본다.
"""
import copy
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _library_sized_contexts as lsc  # noqa: E402
import numpy as np  # noqa: E402
import sizing_recipe as sr  # noqa: E402

# 부동소수 반올림 허용(상대값) -- test_probe_gm_id_monotonicity와 같은 근거: float64 엡실론의 1e3배. LUT VGS 격자 한 칸
# (37.5 mV)보다 10자리 이상 작다. 물리 허용오차가 아니라 계산 동일성의 문턱이다.
_ROUNDOFF = 1.0e3 * np.finfo(float).eps


# --------------------------------------------------------------------------------------
# 독립 쪽: diode의 물리 정의
# --------------------------------------------------------------------------------------
def gate_equals_drain(netlist):
    """`gate == drain`인 소자 이름 -- diode-connected의 정의(topology.json 원문에 직접 적용)."""
    return {dev["name"] for dev in netlist if dev["gate"] == dev["drain"]}


def _netlist_topologies():
    """`A/library/*.topology.json` 중 netlist가 소자 선언 목록인 것(이름 순).

    `_TEMPLATE.topology.json`은 netlist 자리에 설명 문자열을 담는다(`_library_sized_contexts.declared_device_names`
    주석과 같은 사실) -- 소자 선언이 있는 것만 판정 대상이다.
    """
    out = []
    for path in lsc.library_topology_paths():
        topo = lsc.topology_json(path)
        netlist = topo.get("netlist")
        if isinstance(netlist, list) and netlist and all(isinstance(d, dict) for d in netlist):
            out.append((path, topo))
    return out


def _headroom_role(topo, name):
    return ((topo.get("device_roles") or {}).get(name) or {}).get("headroom_role")


def _engine_diodes(path):
    """피검 쪽: 엔진 로더 + 엔진 분류."""
    transistors, _meta = sr.load_topology(path)
    return {t.name for t in transistors if sr.is_diode_connected(t)}


# --------------------------------------------------------------------------------------
# 판정 보조(이름이 assert로 시작한다 -- V4 (4))
# --------------------------------------------------------------------------------------
def assert_diode_set_follows_physics(label, netlist, classified):
    """판정 (1): diode로 분류된 집합이 `gate == drain` 집합과 정확히 같다(라벨만 diode인 소자도, 라벨 때문에 빠진
    물리 diode도 없다)."""
    physical = gate_equals_drain(netlist)
    classified = set(classified)
    label_only = sorted(classified - physical)
    missed = sorted(physical - classified)
    assert label_only == [], "%s: gate != drain인데 diode로 분류된 소자 %s" % (label, label_only)
    assert missed == [], "%s: gate == drain인데 diode로 분류되지 않은 소자 %s" % (label, missed)


def assert_diode_vgs_equals_vds(label, vds, vgs):
    """판정 (2): diode(gate == drain)의 VGS와 VDS가 같다(KVL -- 게이트와 드레인이 같은 노드)."""
    assert vgs is not None, "%s: 사이징된 동작점의 VGS를 LUT에서 되읽지 못했다(목표 gm/ID 거부)" % label
    tol = _ROUNDOFF * max(1.0, abs(vds))
    assert abs(vgs - vds) <= tol, "%s: diode인데 VGS %.9f != VDS %.9f" % (label, vgs, vds)


# --------------------------------------------------------------------------------------
# 판정 (1): 엔진의 diode 분류는 물리 정의를 따르고 라벨에 흔들리지 않는다
# --------------------------------------------------------------------------------------
def test_engine_diode_classification_is_gate_equals_drain_on_library():
    """oracle 대조: (b) 독립 정의 -- `gate == drain`을 topology.json netlist 원문에 직접 적용한 집합. 엔진 로더와
    분류를 거치지 않는다. 라이브러리의 물리 diode가 **서로 다른 라벨을 2종 이상** 달고 있어야 이 판정이 라벨
    다양성을 실제로 본 것이다(원본 probe의 관찰: 파일럿에서 4종) -- 그것도 센다.
    """
    labels_on_diodes, judged = set(), 0
    for path, topo in _netlist_topologies():
        assert_diode_set_follows_physics(os.path.basename(path), topo["netlist"], _engine_diodes(path))
        labels_on_diodes.update(str(_headroom_role(topo, n)) for n in gate_equals_drain(topo["netlist"]))
        judged += 1
    assert judged > 0, "소자 선언이 있는 라이브러리 topology가 없다 -- 판정이 무동작이다"
    assert len(labels_on_diodes) >= 2, (
        "물리 diode의 headroom_role이 %s뿐이다 -- 라벨이 갈리는 경우를 보지 않는다" % sorted(labels_on_diodes))


def _relabelled(topo):
    """합성 topology: 물리 diode의 headroom_role을 **지우고**, 물리 diode가 아닌 소자 하나에 diode 라벨을 **붙인다**.

    붙일 라벨은 라이브러리의 물리 diode가 실제로 쓰는 라벨 중 하나(원본 probe가 적은 'diode_reference')다.
    connectivity(netlist)는 건드리지 않는다 -- 바뀌는 것은 라벨뿐이다.
    """
    out = copy.deepcopy(topo)
    # `device_roles`가 없거나 null인 topology도 있다(라벨이 없는 회로) -- 그때는 빈 선언에서 시작한다.
    roles = out.get("device_roles") or {}
    out["device_roles"] = roles
    physical = gate_equals_drain(out["netlist"])
    for name in sorted(physical):
        (roles.get(name) or {}).pop("headroom_role", None)
    liar = sorted(lsc.declared_device_names(out) - physical)
    if liar:
        roles[liar[0]] = dict(roles.get(liar[0]) or {}, headroom_role="diode_reference")
    return out, (liar[0] if liar else None)


def test_engine_diode_classification_ignores_role_labels(tmp_path):
    """oracle 대조: (b) 같은 독립 정의(`gate == drain`) -- 라벨만 바꾼 합성 topology(물리 diode의 라벨 삭제 + 비diode
    소자에 거짓 diode 라벨)에서도 엔진 분류가 물리 집합과 같아야 한다. 라벨을 바꿨으니 차이가 생기면 그것은
    라벨이 판정을 움직였다는 뜻이다(C4 위반). 거짓 라벨을 실제로 붙인 topology가 있었는지 센다.
    """
    judged = lied = 0
    for path, topo in _netlist_topologies():
        synthetic, liar = _relabelled(topo)
        syn_path = tmp_path / ("relabelled_" + os.path.basename(path))
        syn_path.write_text(json.dumps(synthetic, ensure_ascii=False), encoding="utf-8")
        engine = _engine_diodes(str(syn_path))
        assert_diode_set_follows_physics("라벨 바꾼 " + os.path.basename(path), synthetic["netlist"], engine)
        if liar is not None:
            assert liar not in engine, "%s: 라벨만 diode인 %s를 엔진이 diode로 분류했다" % (path, liar)
            lied += 1
        judged += 1
    assert judged > 0 and lied > 0, (judged, lied)


# --------------------------------------------------------------------------------------
# 판정 (2): 사이징된 물리 diode는 라벨이 무엇이든 VGS = VDS
# --------------------------------------------------------------------------------------
def test_sized_diodes_satisfy_vgs_equals_vds_whatever_their_role():
    """oracle 대조: (b) 독립 정의 + 물리 불변식 -- 판정 대상은 `gate == drain`(netlist 원문)으로 고르고(엔진의 role
    분기가 고른 것이 아니다), 기대값은 KVL(게이트와 드레인이 같은 노드이므로 VGS = VDS)이다. VGS는 사이징된
    (gm_id, L, vds, vsb)에서 LUT로 되읽는다. 사이징이 명시적으로 거부된 회로(`InfeasibleSizingError`)는 동작점이 없어
    판정 대상이 아니다(`_library_sized_contexts` 규칙 -- 삼키지 않고 담아 둔 것). 판정한 diode의 라벨이 2종
    이상인지 센다(라벨이 달라도 같은 물리가 나오는지를 본 것이어야 한다).
    """
    labels, judged = set(), 0
    for key, circuit in sorted(lsc.sized_circuits().items()):
        if not circuit.sized_ok:
            continue
        for name in sorted(gate_equals_drain(circuit.topology["netlist"])):
            entry = dict(circuit.ctx.sized[name])
            lut = circuit.spec["lut_by_kind"][entry["kind"]]
            try:
                vgs = float(lut._solve_vgs(entry["gm_id"], entry["L"], entry["vds"], entry["vsb"]))
            except ValueError:
                vgs = None
            role = _headroom_role(circuit.topology, name)
            assert_diode_vgs_equals_vds("%s/%s(role=%s)" % (key, name, role), float(entry["vds"]), vgs)
            labels.add(str(role))
            judged += 1
    assert judged > 0, "사이징된 물리 diode가 없다 -- 판정이 무동작이다"
    assert len(labels) >= 2, "판정한 diode의 라벨이 %s뿐이다 -- 라벨이 갈리는 경우를 보지 않는다" % sorted(labels)


# --------------------------------------------------------------------------------------
# 합성 반례: 판정이 실제로 거부한다
# --------------------------------------------------------------------------------------
_SYN_NETLIST = [
    # M1: gate == drain -> 물리 diode. M2: gate != drain인데 아래 합성 라벨이 diode라고 한다.
    {"name": "M1", "kind": "nmos", "gate": "nb", "drain": "nb", "source": "gnd"},
    {"name": "M2", "kind": "nmos", "gate": "nb", "drain": "out", "source": "gnd"},
]
_SYN_ROLES = {"M1": {"headroom_role": "mirror"}, "M2": {"headroom_role": "diode_reference"}}


def test_diode_set_judgment_rejects_role_only_diode():
    """oracle 대조: (a) 합성 입력 -- M2는 gate != drain인데 라벨만 diode다(구성으로 정답이 정해진다: 물리 diode는
    M1 하나). 라벨을 믿는 분류({M2})와 라벨 때문에 물리 diode를 빠뜨린 분류({M2}에서 M1 누락), 둘 다 믿는 분류
    ({M1, M2})를 판정이 **거부**하고, 물리 분류({M1})는 통과한다.
    """
    assert gate_equals_drain(_SYN_NETLIST) == {"M1"}
    by_label = {n for n, r in _SYN_ROLES.items() if r["headroom_role"] == "diode_reference"}
    assert by_label == {"M2"}
    assert_diode_set_follows_physics("합성 물리 분류", _SYN_NETLIST, {"M1"})
    with pytest.raises(AssertionError):
        assert_diode_set_follows_physics("합성 라벨 분류", _SYN_NETLIST, by_label)
    with pytest.raises(AssertionError):
        assert_diode_set_follows_physics("합성 둘 다", _SYN_NETLIST, {"M1", "M2"})
    with pytest.raises(AssertionError):
        assert_diode_set_follows_physics("합성 누락", _SYN_NETLIST, set())


def test_diode_kvl_judgment_rejects_vgs_vds_mismatch():
    """oracle 대조: (a) 합성 입력 -- VGS와 VDS를 손으로 정했다. 라벨 대체값이 diode의 VDS를 정한 모양(VDS 0.3 V,
    물리 VGS 0.6 V -- 원본 probe C4가 적은 mirror/라벨 없음 대체값 쌍)과 VGS를 되읽지 못한 경우를 판정이 **거부**하고,
    같은 값은 통과한다.
    """
    assert_diode_vgs_equals_vds("합성 일치", 0.6, 0.6)
    with pytest.raises(AssertionError):
        assert_diode_vgs_equals_vds("합성 라벨 대체값", 0.3, 0.6)
    with pytest.raises(AssertionError):
        assert_diode_vgs_equals_vds("합성 되읽기 실패", 0.6, None)
