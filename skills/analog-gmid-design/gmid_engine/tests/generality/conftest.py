"""tests/generality 공용 fixture -- 합성 topology 를 파일로 써서 공개 API(`gmid_engine.authoring.load_topology`)에 건다.

기대값은 JSON 직접 집계와 authoring CONTRACT 문장에서 만든다(피검 함수로 기대값을 만들지 않는다). 투영(projection)은
TopologyDoc 공개 필드(CONTRACT 2절)만 읽는다.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import SchemaRejectedError, exit_code_for

HERE = Path(__file__).resolve().parent
ENGINE_ROOT = HERE.parents[1]
LIBRARY_DIR = ENGINE_ROOT.parent / "assets" / "library"
STRUCTURE_CHECKS = HERE.parent / "structure" / "structure_checks.py"
SCHEMA_REJECTED_EXIT = 7       # core CONTRACT 4.5 / authoring CONTRACT 0절
TWO_TERMINAL_VALUE_KEYS = ("value_ohm", "value_farad", "value_amp", "value_volt")   # CONTRACT 3.6·3.7


class Topo:
    """합성 doc 을 파일로 쓰고 로드·거부·투영을 돕는다."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.count = 0

    def write(self, doc) -> str:
        self.count += 1
        p = self.tmp_path / ("g%03d.topology.json" % self.count)
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def load(self, doc):
        return load_topology(self.write(doc))

    def rejected(self, doc):
        """거부돼야 한다. detail dict 반환(공통 실패 형식 확인 포함)."""
        with pytest.raises(SchemaRejectedError) as ei:
            load_topology(self.write(doc))
        assert exit_code_for(ei.value) == SCHEMA_REJECTED_EXIT
        detail = dict(ei.value.record.detail)
        assert detail["gate"] == "topology_load"
        return detail

    @staticmethod
    def projection(td):
        """TopologyDoc 공개 필드의 순서 무관 투영."""
        return {
            "devices": frozenset((d.name, d.kind, d.d, d.g, d.s, d.bulk) for d in td.devices),
            "passives": frozenset((p.name, p.kind, tuple(p.terminals), p.value_key, p.value) for p in td.passives),
            "sources": frozenset((s.name, s.kind, tuple(s.terminals), s.value_key, s.value) for s in td.sources),
            "rails": frozenset(td.rails),
            "ports": frozenset((p.net, p.direction, p.role) for p in td.ports),
        }

    @staticmethod
    def json_projection(doc):
        """같은 투영을 JSON 에서 직접 집계(test 쪽 oracle)."""
        def two(e):
            vk = next((k for k in TWO_TERMINAL_VALUE_KEYS if k in e), None)
            return (e["name"], e["kind"], tuple(e["terminals"]), vk, e[vk] if vk else None)
        return {
            "devices": frozenset((e["name"], e["kind"], e["drain"], e["gate"], e["source"], e.get("bulk"))
                                 for e in doc["netlist"]),
            "passives": frozenset(two(e) for e in doc.get("passive_elements", [])),
            "sources": frozenset(two(e) for e in doc.get("ideal_sources", [])),
            "rails": frozenset(doc["supply_nets"]),
            "ports": frozenset((k, v["direction"], v["role"]) for k, v in doc["ports"].items()
                               if not k.startswith("_")),
        }

    @staticmethod
    def map_projection(proj, mapping, kind_map=None):
        """투영의 이름(원소·넷)을 mapping 으로, MOS kind 를 kind_map 으로 바꾼 투영."""
        f = lambda x: mapping.get(x, x) if isinstance(x, str) else x   # noqa: E731
        k = (lambda x: kind_map.get(x, x)) if kind_map else (lambda x: x)  # noqa: E731
        return {
            "devices": frozenset((f(n), k(kd), f(d), f(g), f(s), f(b)) for n, kd, d, g, s, b in proj["devices"]),
            "passives": frozenset((f(n), kd, tuple(f(t) for t in ts), vk, v) for n, kd, ts, vk, v in proj["passives"]),
            "sources": frozenset((f(n), kd, tuple(f(t) for t in ts), vk, v) for n, kd, ts, vk, v in proj["sources"]),
            "rails": frozenset(f(r) for r in proj["rails"]),
            "ports": frozenset((f(n), d, r) for n, d, r in proj["ports"]),
        }

    @staticmethod
    def json_names(doc):
        """topology_name·원소 이름·넷 이름 전부(JSON 직접 집계)."""
        names = {doc["topology_name"]}
        for e in doc["netlist"]:
            names.update((e["name"], e["drain"], e["gate"], e["source"]))
            if "bulk" in e:
                names.add(e["bulk"])
        for key in ("passive_elements", "ideal_sources"):
            for e in doc.get(key, []):
                names.add(e["name"])
                names.update(e["terminals"])
        names.update(doc["supply_nets"])
        names.update(k for k in doc["ports"] if not k.startswith("_"))
        return names


@pytest.fixture
def topo(tmp_path):
    return Topo(tmp_path)


@pytest.fixture(scope="session")
def structure_checks():
    """tests/structure 의 구조 검사기(같은 이름으로 한 번만 로드 -- structure/conftest.py 와 공유)."""
    name = "gmid_structure_checks"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, STRUCTURE_CHECKS)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


@pytest.fixture(scope="session")
def library_dir():
    return LIBRARY_DIR


@pytest.fixture(scope="session")
def pipe(tmp_path_factory):
    """하류 단계(sizing·metrics·search·layout) 공용 파이프라인(pipeline.py). 실 LUT v2 가 없으면 skip 이 아니라 FAIL."""
    from .pipeline import Env, Pipe
    try:
        env = Env()
    except RuntimeError as e:
        pytest.fail("generality 하류 test 입력(실 LUT v2·PDK) 없음: %s" % e, pytrace=False)
    return Pipe(env, tmp_path_factory.mktemp("pipe"))
