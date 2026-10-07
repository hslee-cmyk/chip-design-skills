"""tests/authoring 공용 helper -- 계약 `gmid_engine/authoring/CONTRACT.md` 만 근거로 쓴다(authoring 소스 미열람).

- 픽스처는 `fixtures/*.topology.json`(손으로 만든 소형 topology, library 이름과 겹치지 않음 -- test_topology_load 가 확인).
- 기대값은 계약 문장과 JSON 직접 집계에서 만든다. 피검 함수로 기대값을 만들지 않는다.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from gmid_engine.core import SchemaRejectedError, exit_code_for

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
SCHEMA_REJECTED_EXIT = 7  # core CONTRACT 4.5 / authoring CONTRACT 0절 "exit code 7"


class Helpers:
    fixtures = FIXTURES

    @staticmethod
    def path(name: str) -> Path:
        return FIXTURES / (name + ".topology.json")

    @staticmethod
    def raw(name: str):
        """픽스처 JSON 을 test 쪽 json 으로 직접 읽는다(피검 함수 아님)."""
        return json.loads(Helpers.path(name).read_text(encoding="utf-8"))

    @staticmethod
    def base():
        return copy.deepcopy(Helpers.raw("base_valid"))

    @staticmethod
    def write(tmp_path: Path, doc, name: str = "doc") -> str:
        p = tmp_path / (name + ".topology.json")
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(p)

    @staticmethod
    def rejected(fn, *args):
        """fn(*args) 가 SchemaRejectedError 를 내야 한다. (exc, detail dict) 반환 + 공통 실패 형식 확인."""
        with pytest.raises(SchemaRejectedError) as ei:
            fn(*args)
        exc = ei.value
        assert not isinstance(exc, ValueError)
        assert exit_code_for(exc) == SCHEMA_REJECTED_EXIT
        assert exc.record.devices == ()
        detail = dict(exc.record.detail)
        assert {"gate", "where", "hits"} <= set(detail)
        hits = detail["hits"]
        assert isinstance(hits, tuple) and len(hits) >= 1
        for h in hits:
            assert isinstance(h.rule, str) and isinstance(h.where, str) and isinstance(h.message, str)
            assert isinstance(h.elements, tuple)
            assert list(h.elements) == sorted(set(h.elements)), h  # 정렬·중복 제거
        return exc, detail

    @staticmethod
    def rules(hits):
        return [h.rule for h in hits]

    @staticmethod
    def dev(doc, name):
        return next(e for e in doc["netlist"] if e["name"] == name)

    @staticmethod
    def pas(doc, name):
        return next(e for e in doc["passive_elements"] if e["name"] == name)


@pytest.fixture
def ah():
    return Helpers
