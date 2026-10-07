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


# ---------------------------------------------------------------------------------------------------------------
# 회로 사이징 spec 로더 test 공용 (근거: authoring/SPEC_CONTRACT.md + 공개 객체 docstring, spec_*.py 소스 미열람)
# 픽스처 = fixtures/spec/ 의 합성 회로 fx_spec_amp(주 대상)·fx_spec_ref(value_from_file 대상). test 마다 tmp 디렉터리에
# 복사하고 dict 를 바꿔 다시 쓴 뒤 load_sizing_spec 에 건다.
# ---------------------------------------------------------------------------------------------------------------
SPEC_FIXTURES = FIXTURES / "spec"
SPEC_SUFFIX = ".sizing_spec.json"
TOPO_SUFFIX = ".topology.json"


def fixture_catalog():
    """SPEC_CONTRACT 5절 '픽스처 이름표'. 어휘는 SPEC_CONTRACT 4절·core CONTRACT 0절(unit ∈ METRIC_UNITS 소문자 접미사,
    view_kind None = 뷰 없음), pm_ss_deg = loop·rout_ss_ohm = output_port 는 SPEC_CONTRACT 6절 9번(metrics CONTRACT 3.15 와 같음)."""
    from gmid_engine.core import MetricSignature as M
    return {
        "gain_ss_db": M("db", "ss", "transfer"),
        "ugf_ss_hz": M("hz", "ss", "transfer"),
        "gbw_ss_hz": M("hz", "ss", "transfer"),
        "pm_ss_deg": M("deg", "ss", "loop"),
        "parasitic_pm_ss_deg": M("deg", "ss", "transfer"),
        "rout_ss_ohm": M("ohm", "ss", "output_port"),
        "ratio_ss_db": M("db", "ss", "ratio"),
        "mismatch_sigma_mv": M("mv", "dc", None),
        "mirror_ratio_error_mv": M("mv", "dc", None),
        "power_dc_w": M("w", "dc", None),
        "area_search_m2": M("m2", "geom", None),
        "supply_current_dc": M("amp", "dc", None, "power"),
        "area_layout_m2": M("m2", "geom", None, "area"),
    }


class SpecCase:
    """tmp 디렉터리 하나에 fx_spec_amp·fx_spec_ref 의 topology·spec 을 복사해 두고 바꿔 쓴다."""

    def __init__(self, tmp_path: Path):
        self.dir = tmp_path
        for p in SPEC_FIXTURES.iterdir():
            if p.suffix == ".json":
                (tmp_path / p.name).write_bytes(p.read_bytes())
        self.spec = self.read_spec("fx_spec_amp")
        self.topo = self.read_topo("fx_spec_amp")

    # 읽기·쓰기 (test 쪽 json -- 피검 함수 아님)
    def read_spec(self, circuit):
        return json.loads((self.dir / (circuit + SPEC_SUFFIX)).read_text(encoding="utf-8"))

    def read_topo(self, circuit):
        return json.loads((self.dir / (circuit + TOPO_SUFFIX)).read_text(encoding="utf-8"))

    def write_spec(self, doc, circuit="fx_spec_amp", stem=None):
        p = self.dir / ((stem or circuit) + SPEC_SUFFIX)
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def write_topo(self, doc, circuit="fx_spec_amp"):
        p = self.dir / (circuit + TOPO_SUFFIX)
        p.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(p)

    def topology(self, circuit="fx_spec_amp"):
        from gmid_engine.authoring import load_topology
        return load_topology(str(self.dir / (circuit + TOPO_SUFFIX)))

    def resync_fp(self, circuit="fx_spec_amp", spec=None):
        """topology 를 바꾼 test 용: 입력 준비로 meta.topology_fp 를 새 topology 의 지문에 맞춘다(기대값 아님)."""
        spec = self.spec if spec is None else spec
        spec["meta"]["topology_fp"] = self.topology(circuit).connectivity_fp
        return spec

    @property
    def human(self):
        return self.spec["human"]

    def constraint(self, metric):
        return next(c for c in self.human["constraints"] if c.get("metric") == metric)

    def load(self, catalog=None, circuit="fx_spec_amp", stem=None):
        from gmid_engine.authoring import load_sizing_spec
        path = self.write_spec(self.spec, circuit, stem)
        return load_sizing_spec(path, self.topology(circuit), fixture_catalog() if catalog is None else catalog)

    def reject(self, catalog=None, circuit="fx_spec_amp", stem=None):
        """한 번의 SchemaRejectedError + 공통 형식(gate spec_load·where 경로·rejected_gates 정렬). detail dict 반환."""
        from gmid_engine.authoring import load_sizing_spec
        path = self.write_spec(self.spec, circuit, stem)
        topo = self.topology(circuit)
        cat = fixture_catalog() if catalog is None else catalog
        exc, detail = Helpers.rejected(load_sizing_spec, path, topo, cat)
        assert detail["gate"] == "spec_load"
        assert detail["where"] == path
        rg = detail["rejected_gates"]
        assert isinstance(rg, tuple) and list(rg) == sorted(set(rg))
        assert isinstance(detail["not_evaluated"], tuple)
        return detail

    @staticmethod
    def rules(detail):
        return [h.rule for h in detail["hits"]]

    @staticmethod
    def only(detail, rule, gate, not_evaluated=("references",)):
        """위반 하나: hits 가 정확히 [rule], rejected_gates == (gate,), not_evaluated 집합 일치.
        기본 not_evaluated = {references}(SPEC_CONTRACT 0절: 앞 게이트에 위반이 있으면 참조 해석 안 함)."""
        assert SpecCase.rules(detail) == [rule], [(h.rule, h.where, h.elements) for h in detail["hits"]]
        assert detail["rejected_gates"] == (gate,), detail["rejected_gates"]
        assert set(detail["not_evaluated"]) == set(not_evaluated), detail["not_evaluated"]
        return detail["hits"][0]

    def reject_only(self, rule, gate, not_evaluated=("references",), **kw):
        return self.only(self.reject(**kw), rule, gate, not_evaluated)

    def reject_has(self, rule, gate):
        """rule 이 hits 에 있고 gate 가 rejected_gates 에 있다(다른 hit 동반 여부를 계약이 정하지 않은 경우만)."""
        d = self.reject()
        assert rule in self.rules(d), self.rules(d)
        assert gate in d["rejected_gates"], d["rejected_gates"]
        return d


@pytest.fixture
def sc(tmp_path):
    return SpecCase(tmp_path)


@pytest.fixture
def catalog():
    return fixture_catalog()
