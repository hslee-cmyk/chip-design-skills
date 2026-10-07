"""tests/graph 공용 helper -- 계약 `gmid_engine/graph/CONTRACT.md` 와 `graph/__init__.py` 의 `__all__` 만 근거로 쓴다
(graph .py 소스 미열람).

- 입력: library topology 원본(`assets/library/*.topology.json`)과, test 쪽 json 으로 그것을 고친 변형(tmp 에 써서
  authoring `load_topology` 로 읽는다 -- authoring 공개 API 는 입력 생성용).
- 기대값: 이 파일의 `JsonAgg` 가 topology JSON 을 **직접** 집계한다(피검 함수로 기대값을 만들지 않는다).
  계약 7.1 표 숫자는 이 집계를 다시 교차 확인하는 데 쓴다.
- supplies_v: 사용자 확정값 `{vdd: 1.8, gnd: 0}`(two_stage_ota·current_reuse·folded·common_gate, 계약 7절) 또는
  topology `_declared_target_spec.supplies_v`(`_` 키 제외, test 쪽에서만 읽음). 둘 다 없으면 None.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parents[2]                                   # .../analog-gmid-design
LIBRARY = SKILL_DIR / "assets" / "library"

SIX = (
    "common_gate_amplifier",
    "current_reuse_telescopic_ota",
    "ngcc_3stage_ff",
    "pushpull_follower_buffer",
    "sf_pushpull_output_opamp",
    "two_stage_ota_sf",
)
# authoring 이 passives/missing_key 로 거부하는 3회로(CI-12 대기, 계약 7.2)
CI12 = ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")
NINE = tuple(sorted(SIX + CI12))

USER_CONFIRMED_SUPPLIES = {"vdd": 1.8, "gnd": 0.0}           # 사용자 확정(2026-10-07, user_decisions 1번)
USER_CONFIRMED_CIRCUITS = ("two_stage_ota", "current_reuse_telescopic_ota", "folded_cascode", "common_gate_amplifier")
TAG_KEYS = ("device_roles", "symmetry", "sizing_roles", "compensation")
MOS_KINDS = ("nmos", "pmos")
INPUT = "input"


def raw(name: str) -> dict:
    return json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def supplies_for(name: str, doc: dict | None = None):
    """test 쪽 supplies_v 출처(계약 7절). 없으면 None."""
    if name in USER_CONFIRMED_CIRCUITS:
        return dict(USER_CONFIRMED_SUPPLIES)
    doc = raw(name) if doc is None else doc
    spec = doc.get("_declared_target_spec")
    if isinstance(spec, dict) and isinstance(spec.get("supplies_v"), dict):
        return {k: v for k, v in spec["supplies_v"].items() if not str(k).startswith("_")}
    return None


def write(tmp_path: Path, doc: dict, stem: str = "variant") -> str:
    p = tmp_path / (stem + ".topology.json")
    p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(p)


def load_raw(tmp_path: Path, doc: dict, stem: str = "variant"):
    return load_topology(write(tmp_path, doc, stem))


def load_lib(name: str):
    return load_topology(str(LIBRARY / (name + ".topology.json")))


def ci12_variant(name: str) -> dict:
    """CI-12 3회로를 메모리 안에서 `passive_elements: []` 로 바꾼 변형(계약 7.2 참고값 조건, 파일은 고치지 않음)."""
    d = raw(name)
    d["passive_elements"] = []
    return d


def rename_nets(doc: dict, mapping: dict) -> dict:
    """넷 이름을 문서 전체(netlist d/g/s/bulk, 2단자 terminals, supply_nets, ports 키)에서 바꾼 사본."""
    d = copy.deepcopy(doc)
    f = lambda n: mapping.get(n, n)  # noqa: E731
    for e in d["netlist"]:
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = f(e[k])
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["terminals"] = [f(t) for t in e["terminals"]]
    d["supply_nets"] = [f(n) for n in d["supply_nets"]]
    d["ports"] = {(k if k.startswith("_") else f(k)): v for k, v in d["ports"].items()}
    return d


class JsonAgg:
    """topology JSON 직접 집계(엔진 미사용)."""

    def __init__(self, doc: dict):
        self.doc = doc
        self.mos = {e["name"]: e for e in doc["netlist"]}
        self.passives = {e["name"]: e for e in (doc.get("passive_elements") or [])}
        self.sources = {e["name"]: e for e in (doc.get("ideal_sources") or [])}
        self.rails = frozenset(doc["supply_nets"])
        self.ports = {k: v for k, v in doc["ports"].items() if not k.startswith("_")}
        term = {}
        for n, e in self.mos.items():
            for t, k in (("d", "drain"), ("g", "gate"), ("s", "source")):
                term.setdefault(e[k], []).append((n, t))
        for group in (self.passives, self.sources):
            for n, e in group.items():
                for t, net in zip(("t0", "t1"), e["terminals"]):
                    term.setdefault(net, []).append((n, t))
        self.terminals = {k: tuple(sorted(v)) for k, v in term.items()}
        self.bulk_declared = {n: e.get("bulk") for n, e in self.mos.items()}
        self.nodes = tuple(sorted(set(self.terminals) | {b for b in self.bulk_declared.values() if b} | set(self.rails)))
        self.n_kind = sum(1 for e in self.mos.values() if e["kind"] == "nmos")
        self.p_kind = sum(1 for e in self.mos.values() if e["kind"] == "pmos")
        self.diodes = tuple(sorted(n for n, e in self.mos.items() if e["gate"] == e["drain"]))
        self.input_nets = frozenset(k for k, v in self.ports.items() if v["direction"] == INPUT)
        self.gate_only = tuple(sorted(
            net for net, ts in self.terminals.items()
            if net not in self.rails and net not in self.input_nets and ts and all(t == "g" for _, t in ts)))
        self.n_in = sum(1 for v in self.ports.values() if v["direction"] == "input")
        self.n_out = sum(1 for v in self.ports.values() if v["direction"] == "output")
        self.channel_rails = frozenset(
            e[k] for e in self.mos.values() if e["kind"] in MOS_KINDS for k in ("drain", "source") if e[k] in self.rails)

    def ac_class(self, net):
        if net in self.rails:
            return "rail"
        if net in self.gate_only:
            return "gate_only_undriven"
        return None

    def expected_bulk(self, supplies):
        """계약 4.2 우선순위 표 그대로: 이름 -> (net, origin, reason)."""
        out = {}
        lo = hi = None
        if supplies is not None:
            pot = {r: float(supplies[r]) for r in self.rails}
            lo = min(pot, key=lambda r: pot[r])
            hi = max(pot, key=lambda r: pot[r])
        for n, e in self.mos.items():
            if e.get("bulk"):
                out[n] = (e["bulk"], "declared", None)
            elif e["kind"] not in MOS_KINDS:
                out[n] = (None, "undetermined", "unsupported_kind")
            elif supplies is None:
                out[n] = (None, "undetermined", "needs_supplies_v")
            else:
                out[n] = (lo if e["kind"] == "nmos" else hi, "default_rule", None)
        return out

    def extreme_rails(self, supplies):
        pot = {r: float(supplies[r]) for r in self.rails}
        vmin, vmax = min(pot.values()), max(pot.values())
        return (tuple(sorted(r for r in pot if pot[r] == vmin)), vmin,
                tuple(sorted(r for r in pot if pot[r] == vmax)), vmax)


def bulk_tuple(b):
    return (b.net, b.origin, b.reason)


class Helpers:
    SIX = SIX
    CI12 = CI12
    NINE = NINE
    TAG_KEYS = TAG_KEYS
    LIBRARY = LIBRARY
    SKILL_DIR = SKILL_DIR
    raw = staticmethod(raw)
    supplies_for = staticmethod(supplies_for)
    write = staticmethod(write)
    load_raw = staticmethod(load_raw)
    load_lib = staticmethod(load_lib)
    ci12_variant = staticmethod(ci12_variant)
    rename_nets = staticmethod(rename_nets)
    agg = staticmethod(JsonAgg)
    bulk_tuple = staticmethod(bulk_tuple)


@pytest.fixture
def gh():
    return Helpers
