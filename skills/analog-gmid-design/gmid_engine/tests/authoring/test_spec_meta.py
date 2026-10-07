"""meta 와 topology 짝 대조 (gate `spec_meta`) -- SPEC_CONTRACT 2절 circuit_name_mismatch·topology_fp_mismatch,
0절 not_evaluated `topology_cross_checks`."""
from __future__ import annotations

from gmid_engine.authoring import load_sizing_spec, load_topology

NE_META = ("topology_cross_checks", "references")


def test_fixture_meta_fp_equals_topology_fp(sc):
    """픽스처 정합(입력 확인): meta.topology_fp 가 짝 topology 의 connectivity_fp 와 같다."""
    assert sc.spec["meta"]["topology_fp"] == sc.topology().connectivity_fp
    ref = sc.read_spec("fx_spec_ref")
    assert ref["meta"]["topology_fp"] == sc.topology("fx_spec_ref").connectivity_fp


def test_circuit_differs_from_topology_name(sc):
    """meta.circuit 을 다른 이름으로, 파일도 그 이름으로 -- topology.name 과 다르다."""
    sc.spec["meta"]["circuit"] = "fx_spec_other"
    path = sc.write_spec(sc.spec, stem="fx_spec_other")
    from gmid_engine.core import SchemaRejectedError
    import pytest
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(path, sc.topology(), {})
    d = dict(ei.value.record.detail)
    assert "circuit_name_mismatch" in [h.rule for h in d["hits"]]
    assert "spec_meta" in d["rejected_gates"]
    assert set(NE_META) <= set(d["not_evaluated"])


def test_circuit_differs_from_file_stem(sc):
    """meta.circuit == topology.name 이지만 파일 이름 stem 이 다르다."""
    d = sc.reject(stem="fx_spec_copy")
    sc.only(d, "circuit_name_mismatch", "spec_meta", NE_META)


def test_topology_fp_mismatch(sc):
    sc.spec["meta"]["topology_fp"] = "f" * 64
    sc.reject_only("topology_fp_mismatch", "spec_meta", NE_META)


def test_topology_changed_breaks_spec(sc):
    """연결을 바꾼 topology 와 옛 spec -> topology_fp_mismatch."""
    t = sc.read_topo("fx_spec_amp")
    t["netlist"][4]["kind"] = "pmos"
    sc.write_topo(t)
    sc.reject_only("topology_fp_mismatch", "spec_meta", NE_META)


def test_topology_comment_change_keeps_spec_valid(sc):
    """지문은 연결 투영이라 topology 주석만 바꾸면 spec 은 그대로 통과(파일 sha256 아님)."""
    t = sc.read_topo("fx_spec_amp")
    t["_note"] = "changed comment only"
    t["device_roles"] = {"Q1": "anything"}
    sc.write_topo(t)
    sc.load()


def test_wrong_topology_object(sc):
    """다른 회로의 TopologyDoc 을 주면 이름·지문 둘 다 불일치."""
    path = sc.write_spec(sc.spec)
    other = load_topology(str(sc.dir / "fx_spec_ref.topology.json"))
    from gmid_engine.core import SchemaRejectedError
    import pytest
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(path, other, {})
    d = dict(ei.value.record.detail)
    rules = [h.rule for h in d["hits"]]
    assert "circuit_name_mismatch" in rules and "topology_fp_mismatch" in rules
    assert "topology_cross_checks" in d["not_evaluated"]
