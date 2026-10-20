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
import dataclasses
import json
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import GraphSnapshot
from gmid_engine.core import StructureUnresolvedError, exit_code_for
from gmid_engine.graph import GRAPH_KEY, S1_WRITERS, s1_bulk, s1_structure, supplies_declaration
from graph_u2_oracle import StopExpected, U2Oracle

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
# 예전 CI-12 3회로(2026-10-07 b9c7042 topology 정정으로 passive_elements 선언 -- 이제 load 통과)
CI12 = ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")
NINE = tuple(sorted(SIX + CI12))

USER_CONFIRMED_SUPPLIES = {"vdd": 1.8, "gnd": 0.0}           # 사용자 확정(2026-10-07, user_decisions 1번)
USER_CONFIRMED_CIRCUITS = (  # 계약 7절 + two_stage_ota_sf(7절 갱신)
    "two_stage_ota_sf", "two_stage_ota", "current_reuse_telescopic_ota", "folded_cascode", "common_gate_amplifier",
)
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


def structure_and_bulk(doc, supplies_v=None):
    """build_s1 순서(계약 1절)의 앞 두 블록만 직접 부른 스냅샷 -- U2 정지 전의 S1 기본 필드를 보려고. [XRUN-F1 card B C4] 새 실행 하나."""
    run = fresh_run()
    snap = s1_structure(GraphSnapshot.empty(S1_WRITERS), doc.devices, doc.passives, doc.sources,
                        tuple(sorted(doc.rails)), doc.ports, **run)
    return s1_bulk(snap, supplies_declaration(supplies_v, doc.rails), **run)


# ---- [XRUN-F1 card B C0·C1·C4] 실행 두 객체와 실행 계수 행(test 도구)
COUNT_FIELDS = ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")


def fresh_run():
    """새 실행 하나의 두 객체 키워드(dict) -- 블록·build_s1·build_s1v 호출 `f(..., **run)`. 부를 때마다 새 open_run() 쌍."""
    from gmid_engine.search import open_run
    donors, counters = open_run()
    return dict(donors=donors, counters=counters)


def block_row(counters, name):
    """실행 계수 (name, "*") 행의 여섯 칸 tuple(COUNT_FIELDS 순서), 기록이 없으면 0 여섯."""
    for r in counters.snapshot().blocks:
        if (r.block, r.part) == (name, "*"):
            return tuple(getattr(r, f) for f in COUNT_FIELDS)
    return (0,) * len(COUNT_FIELDS)


def row_delta(after, before):
    return tuple(a - b for a, b in zip(after, before))


def ev_plain(e):
    return (e.rule, e.nets, e.group, e.basis)


def seg_plain(s):
    return (s.nets, s.elements)


def branch_plain(b):
    return (b.id, b.ends, tuple(seg_plain(s) for s in b.segments), b.has_ideal_source)


def column_plain(c):
    return (c.id, c.rails, c.branch_order, c.parallel_expansion, c.status, ev_plain(c.evidence))


def gs_plain(g):
    return (g.kind, g.gate, g.source, g.members)


def role_plain(r):
    return (r.role, r.status, ev_plain(r.evidence))


def rel_plain(r):
    return (r.type, r.domain, r.members, r.status, ev_plain(r.evidence))


def gval(s1, field):
    """graph 필드 값(계약 5절 `value("graph", GRAPH_KEY, field)`)."""
    return s1.value("graph", GRAPH_KEY, field)


def stop(fn):
    """fn() 이 STRUCTURE_UNRESOLVED(exit 2, reason unsupported_rule_branch)로 정지 -> (detail dict, devices)."""
    import pytest as _pytest
    with _pytest.raises(StructureUnresolvedError) as ei:
        fn()
    exc = ei.value
    assert exit_code_for(exc) == 2
    d = dict(exc.record.detail)
    assert d["reason"] == "unsupported_rule_branch"
    return d, exc.record.devices


def oracle(doc_raw, merge=True, column_limit=None):
    return U2Oracle(doc_raw, merge=merge, column_limit=column_limit)


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
    rename_nets = staticmethod(rename_nets)
    agg = staticmethod(JsonAgg)
    bulk_tuple = staticmethod(bulk_tuple)
    structure_and_bulk = staticmethod(structure_and_bulk)
    fresh_run = staticmethod(fresh_run)          # [XRUN-F1 card B C0]
    block_row = staticmethod(block_row)          # [XRUN-F1 card B C1]
    ev_plain = staticmethod(ev_plain)
    seg_plain = staticmethod(seg_plain)
    branch_plain = staticmethod(branch_plain)
    column_plain = staticmethod(column_plain)
    gs_plain = staticmethod(gs_plain)
    role_plain = staticmethod(role_plain)
    rel_plain = staticmethod(rel_plain)
    gval = staticmethod(gval)
    stop = staticmethod(stop)
    oracle = staticmethod(oracle)
    StopExpected = StopExpected
    astuple = staticmethod(dataclasses.astuple)


@pytest.fixture
def gh():
    return Helpers
