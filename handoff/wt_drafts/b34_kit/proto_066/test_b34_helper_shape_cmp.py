"""Comparison only (not a candidate): contract 8 in the rejected helper-snapshot shape (expected = in-process value before absence)."""
import contextlib
import sys

import pytest

from test_b34_grammar_explicit import _B34_IDS, _B34_PATHS, _b34_normalize, _b34_overrides
import stick_diagram


def _b34h_snapshot(p, ts):
    ov = _b34_overrides(ts)
    return {
        "load_topology": _b34_normalize(stick_diagram.load_topology(p)),
        "run_topology_pipeline": _b34_normalize(stick_diagram.run_topology_pipeline(p, ov)),
        "find_stack_edges": _b34_normalize(stick_diagram.find_stack_edges(ts)),
        "find_idiom_matches": _b34_normalize(stick_diagram.find_idiom_matches(ts)),
        "find_differential_and_mirror_forks": _b34_normalize(stick_diagram.find_differential_and_mirror_forks(ts)),
        "suggest_vertical_stack_composites": _b34_normalize(stick_diagram.suggest_vertical_stack_composites(ts)),
        "find_differential_pair_candidates": _b34_normalize(stick_diagram.find_differential_pair_candidates(ts)),
        "find_verified_differential_and_mirror_relations": _b34_normalize(stick_diagram.find_verified_differential_and_mirror_relations(ts)),
        "refine_differential_and_mirror_relations": _b34_normalize(stick_diagram.refine_differential_and_mirror_relations(ts)),
        "audit_theta_root_direction": _b34_normalize(stick_diagram.audit_theta_root_direction(ts, None)),
        "propose_theta_kcl_gap_fill": _b34_normalize(stick_diagram.propose_theta_kcl_gap_fill(ts, [])),
        "propose_device_roles_gap_fill": _b34_normalize(stick_diagram.propose_device_roles_gap_fill(ts, {}, [])),
        "geometry_colocation_union": _b34_normalize(stick_diagram.geometry_colocation_union(ts, [])),
        "propose_vertical_stack_id_gap_fill": _b34_normalize(stick_diagram.propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))),
    }


@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34h_c8_helper_shape(p, monkeypatch):
    ts, _meta = stick_diagram.load_topology(p)
    before = _b34h_snapshot(p, ts)
    with monkeypatch.context() as m:
        m.setitem(sys.modules, "netclass", None)
        m.setitem(sys.modules, "idioms", None)
        with contextlib.suppress(ImportError):
            stick_diagram.load_topology(p)
    after = _b34h_snapshot(p, ts)
    assert after == before
