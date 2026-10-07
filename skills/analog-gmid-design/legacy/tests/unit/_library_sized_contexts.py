# -*- coding: utf-8 -*-
"""승격 test의 공용 **입력 구성기**(20260923-probe-promote-clean, design `20-dead-code-dup` v1.2 §5.1 P3).

판정 문장은 이 파일에 없다 -- test 파일이 한다(계획 N4.2 V4 (4) '판정 보조 함수'는 이름이 `assert`로
시작한다. 여기 있는 것은 판정이 아니라 입력이다). 기대값도 여기서 나오지 않는다.

원본 probe 두 개(`probe_role_L_derivation`, `probe_parasitic_pm_all_circuits`)가 똑같이 하던
"하네스가 선언한 회로마다 theta 하나를 골라 **한 번** 평가한다"를 한 곳에 모은 것이다.

* 회로 목록은 `run_harness.SPECS`다 -- 회로 이름을 코드에 박지 않는다(원본 probe의 규칙,
  `probe_role_L_derivation` docstring "회로 이름을 코드에 박지 않는다 -- run_harness.SPECS를 순회한다").
* theta는 **선언된 bounds의 중앙점**을 쓴다. 다만 `tests/canonical_theta_star.json`이 그 회로의 theta
  이름을 **전부** 담고 있으면 그 값을 쓴다(원본 probe 두 개가 쓰던 규칙). 일부만 겹치면 쓰지 않는다 --
  이름이 같은 다른 회로의 theta 값(`kcl_tail_M5`가 실제로 두 회로에 있다)이 섞이기 때문이다.
* 사이징이 **명시적으로** 거부되면(`InfeasibleSizingError`) 그 예외를 담아 돌려준다. 삼키지 않고,
  다른 예외는 그대로 올린다(조용한 실패 금지 -- 계획 §3.2 P1).
* 결과는 모듈 수준에 한 번만 계산해 캐시한다. test 순서·`--shuffle-seed`와 무관하게 같은 값이고,
  test가 이 객체를 변형하지 않도록 판정 쪽에서 복사해 쓴다.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# unit -> tests -> assets(A)
ASSETS = os.path.abspath(os.path.join(_HERE, "..", ".."))
# A -> analog-gmid-design -> skills -> 저장소 루트 -> workspaces
_WORKSPACES = os.path.abspath(os.path.join(ASSETS, "..", "..", "..", "workspaces"))
for _path in (ASSETS, _WORKSPACES):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import sizing_recipe as sr  # noqa: E402
import run_harness as H  # noqa: E402

LIBRARY_DIR = os.path.join(ASSETS, "library")
THETA_STAR_PATH = os.path.join(ASSETS, "tests", "canonical_theta_star.json")

_TOPOLOGY_CACHE = {}
_CIRCUIT_CACHE = {}


def library_topology_paths():
    """`A/library/*.topology.json` 전부(이름 순). 회로 이름을 목록으로 박지 않는다."""
    names = sorted(n for n in os.listdir(LIBRARY_DIR) if n.endswith(".topology.json"))
    return [os.path.join(LIBRARY_DIR, n) for n in names]


def topology_json(path):
    """선언 원문(topology.json)을 읽어 캐시한다."""
    key = os.path.abspath(path)
    if key not in _TOPOLOGY_CACHE:
        with open(key, encoding="utf-8") as fh:
            _TOPOLOGY_CACHE[key] = json.load(fh)
    return _TOPOLOGY_CACHE[key]


def declared_device_names(topo_json):
    # `_TEMPLATE.topology.json`은 netlist 자리에 설명 문자열을 담는다 -- 소자 선언만 센다.
    return {dev["name"] for dev in topo_json.get("netlist") or []
            if isinstance(dev, dict) and dev.get("name")}


def declared_metrics(topo_json):
    return (topo_json.get("sizing_roles") or {}).get("metrics") or {}


def declared_thetas(topo_json):
    return (topo_json.get("sizing_roles") or {}).get("theta") or []


def declared_supply_nets(topo_json):
    """레일 넷은 `supply_nets` 선언으로만 정한다(계획 DEC-60 -- 넷 이름 집합으로 판정하지 않는다)."""
    return set(topo_json.get("supply_nets") or ())


def declared_circuits():
    """`run_harness.SPECS` 회로마다 (topology 선언, 정본 spec). **사이징하지 않는다**."""
    out = {}
    for key, cfg in H.SPECS.items():
        path = os.path.join(LIBRARY_DIR, cfg["topology_file"])
        out[key] = (topology_json(path), H.canonical_spec(key))
    return out


def declared_L_search_thetas(topo_json):
    """L을 격자로 훑는 theta 선언 -- `feeds.type == "metric_stage_budget"`.

    원본 probe `probe_lut_L_interpolation`의 마지막 절이 쓰던 것과 같은 필터다(그 절의 문장:
    "`_theta_grid_points()`의 `L_grid_step` 경로"). 이 선언의 `bounds`가 L 탐색 구간(단위 m)이다.
    """
    out = []
    for decl in declared_thetas(topo_json):
        feeds = decl.get("feeds")
        if isinstance(feeds, dict) and feeds.get("type") == "metric_stage_budget" and decl.get("bounds"):
            out.append((decl, list(feeds.get("devices") or ())))
    return out


class SizedCircuit(object):
    """회로 하나의 평가 결과 -- 값만 담는다(판정 없음)."""

    __slots__ = ("key", "topology_path", "topology", "spec", "ctx", "metrics", "refusal")

    def __init__(self, key, topology_path, topology, spec, ctx, metrics, refusal):
        self.key = key
        self.topology_path = topology_path
        self.topology = topology
        self.spec = spec
        self.ctx = ctx
        self.metrics = metrics
        self.refusal = refusal

    @property
    def sized_ok(self):
        return self.refusal is None

    def role_L_entries(self):
        """`L_role` 선언이 실제로 L을 정한 소자만 (이름, sized 항목 사본)으로 돌려준다.

        theta·compensation 등 더 권위 있는 출처가 이긴 소자는 뺀다(원본 probe와 같은 기준 --
        `_L_source`가 `L_role`로 시작하는 것만 본다).
        """
        out = []
        for name in sorted((self.ctx.sized if self.ctx else {})):
            entry = self.ctx.sized[name]
            if str(entry.get("_L_source", "")).startswith("L_role"):
                out.append((name, dict(entry)))
        return out


def _midpoint(theta_decl):
    bounds = theta_decl.get("bounds")
    if not bounds:
        return 0.0
    return (float(bounds[0]) + float(bounds[1])) / 2.0


def _theta_point(thetas):
    point = {decl["name"]: _midpoint(decl) for decl in thetas}
    if not point or not os.path.exists(THETA_STAR_PATH):
        return point
    with open(THETA_STAR_PATH, encoding="utf-8") as fh:
        saved = json.load(fh)
    if set(point) <= set(saved):
        return {name: saved[name] for name in point}
    return point


def _evaluate_once(key, cfg):
    topo_path = os.path.join(LIBRARY_DIR, cfg["topology_file"])
    spec = H.canonical_spec(key)
    topo = topology_json(topo_path)
    try:
        evaluator = sr._build_theta_evaluator(topo_path, spec)
        ctx, metrics = evaluator["evaluate"](_theta_point(evaluator["thetas"]))
    except sr.InfeasibleSizingError as exc:
        return SizedCircuit(key, topo_path, topo, spec, None, None, exc)
    return SizedCircuit(key, topo_path, topo, spec, ctx, metrics, None)


def sized_circuits():
    """`run_harness.SPECS`의 회로마다 SizedCircuit 하나. 한 번 계산하고 캐시한다."""
    if not _CIRCUIT_CACHE:
        for key, cfg in H.SPECS.items():
            _CIRCUIT_CACHE[key] = _evaluate_once(key, cfg)
    return dict(_CIRCUIT_CACHE)
