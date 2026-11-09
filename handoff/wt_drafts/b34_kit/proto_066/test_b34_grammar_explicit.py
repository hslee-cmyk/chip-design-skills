"""B34 prototype (orchestrator decision 0.6-6) -- contracts 1~3 in pytest.raises shape, contract 8 with a fresh-process oracle.

Not the test-author's file: a shape prototype used to prove V4 (test_lint.py) PASS, base red and mutant kills.
Contracts 4~6 are omitted here (unchanged by the decision).
"""
import contextlib
import dataclasses
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_B34_HERE = Path(__file__).resolve()
_B34_ASSETS = _B34_HERE.parents[2]
if str(_B34_ASSETS) not in sys.path:
    sys.path.insert(0, str(_B34_ASSETS))
import stick_diagram  # noqa: E402
_B34_ROOT = _B34_HERE.parents[5]
_B34_PATHS = sorted(p for p in glob.glob(str(_B34_ASSETS / "library" / "*.topology.json"))
                    if not os.path.basename(p).startswith("_"))
_B34_IDS = [os.path.basename(p).split(".")[0] for p in _B34_PATHS]


def _b34_norm_path(x):
    return os.path.normcase(os.path.realpath(x))


def _b34_expected_path():
    return _b34_norm_path(_B34_ROOT / "skills" / "analog-grammar" / "assets")


def _b34_exc_problems(exc):
    """contract 3: list of violated clauses (empty list = all satisfied)."""
    problems = []
    text = os.path.normcase(str(exc))
    if "analog-grammar" not in str(exc):
        problems.append("no 'analog-grammar' in message")
    e = _b34_expected_path()
    m = os.path.normcase(os.path.normpath(os.path.join(os.path.dirname(stick_diagram.__file__), "..", "..",
                                                       "analog-grammar", "assets")))
    if not (e in text or (m in text and _b34_norm_path(m) == e)):
        problems.append("search path missing from message")
    if not isinstance(exc.__cause__, ImportError):
        problems.append("__cause__ is not ImportError")
    return problems


def _b34_overrides(ts):
    return {t.name: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_" + t.name} for t in ts}


def _b34_normalize(x):
    """card 'normalization', made JSON-exact: Match-like -> list, set -> sorted list, tuple -> list,
    dataclass/object -> dict with type name, float -> repr string (nan-safe), dict keys -> str."""
    if isinstance(x, bool) or x is None or isinstance(x, (int, str)):
        return x
    if isinstance(x, float):
        return {"__float__": repr(x)}
    if all(hasattr(x, a) for a in ("kind", "devices", "ports", "note", "priority")) and not isinstance(x, dict):
        return ["__match__", _b34_normalize(x.kind), _b34_normalize(list(x.devices)),
                _b34_normalize(sorted(x.ports.items())), _b34_normalize(x.note), _b34_normalize(x.priority)]
    if isinstance(x, dict):
        if all(isinstance(k, str) for k in x):
            return {k: _b34_normalize(v) for k, v in x.items()}
        items = [[_b34_normalize(k), _b34_normalize(v)] for k, v in x.items()]
        return {"__items__": sorted(items, key=lambda kv: json.dumps(kv, sort_keys=True))}
    if isinstance(x, (set, frozenset)):
        return {"__set__": sorted((_b34_normalize(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))}
    if isinstance(x, (list, tuple)):
        return [_b34_normalize(v) for v in x]
    if dataclasses.is_dataclass(x):
        return {"__type__": type(x).__name__,
                **{f.name: _b34_normalize(getattr(x, f.name)) for f in dataclasses.fields(x)}}
    if hasattr(x, "__dict__"):
        return {"__type__": type(x).__name__, **{k: _b34_normalize(v) for k, v in vars(x).items()}}
    return {"__repr__": repr(x)}


# The fresh interpreter computes the same 14 entry points on the same input (path p) -- calls live in a
# string so the V3 graph does not see a second caller, and nothing from the pytest process is reused.
_B34_FRESH_SCRIPT = r'''
import json, sys
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import stick_diagram
from test_b34_grammar_explicit import _b34_normalize, _b34_overrides
p = sys.argv[3]
ts, _meta = stick_diagram.load_topology(p)
out = {
    "load_topology": _b34_normalize(stick_diagram.load_topology(p)),
    "run_topology_pipeline": _b34_normalize(stick_diagram.run_topology_pipeline(p, _b34_overrides(ts))),
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
sys.stdout.write(json.dumps(out, sort_keys=True))
'''


def _b34_fresh_process(p):
    """(returncode, stdout, stderr) of a separate interpreter that never saw the absence."""
    r = subprocess.run([sys.executable, "-B", "-c", _B34_FRESH_SCRIPT, os.path.dirname(stick_diagram.__file__),
                        str(_B34_HERE.parent), p], capture_output=True, text=True, encoding="utf-8",
                       env=dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1"))
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------- contract 1 (+3)
@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c1_both_absent_raises_named_import_error(p, monkeypatch):
    ts, _meta = stick_diagram.load_topology(p)
    ov = _b34_overrides(ts)
    monkeypatch.setitem(sys.modules, "netclass", None)
    monkeypatch.setitem(sys.modules, "idioms", None)
    errs = []
    with pytest.raises(ImportError) as ei:
        stick_diagram.load_topology(p)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.run_topology_pipeline(p, ov)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_stack_edges(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_idiom_matches(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_differential_and_mirror_forks(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.suggest_vertical_stack_composites(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_differential_pair_candidates(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_verified_differential_and_mirror_relations(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.refine_differential_and_mirror_relations(ts)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.audit_theta_root_direction(ts, None)
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.propose_theta_kcl_gap_fill(ts, [])
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.propose_device_roles_gap_fill(ts, {}, [])
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.geometry_colocation_union(ts, [])
    errs.append(ei.value)
    with pytest.raises(ImportError) as ei:
        stick_diagram.propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))
    errs.append(ei.value)
    assert len(errs) == 14
    assert [_b34_exc_problems(e) for e in errs] == [[]] * 14


# ---------------------------------------------------------------- contract 2 (+3)
@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c2_idioms_only_absent_load_topology_raises(p, monkeypatch):
    monkeypatch.setitem(sys.modules, "idioms", None)
    with pytest.raises(ImportError) as ei:
        stick_diagram.load_topology(p)
    assert _b34_exc_problems(ei.value) == []


@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c2_netclass_only_absent_find_stack_edges_raises(p, monkeypatch):
    ts, _meta = stick_diagram.load_topology(p)
    monkeypatch.setitem(sys.modules, "netclass", None)
    with pytest.raises(ImportError) as ei:
        stick_diagram.find_stack_edges(ts)
    assert _b34_exc_problems(ei.value) == []


# ---------------------------------------------------------------- contract 8 (fresh-process oracle)
@pytest.mark.parametrize("p", _B34_PATHS, ids=_B34_IDS)
def test_b34_c8_restored_values_equal_fresh_process(p, monkeypatch):
    rc, out, err = _b34_fresh_process(p)
    assert rc == 0, err
    expected = json.loads(out)
    ts, _meta = stick_diagram.load_topology(p)
    ov = _b34_overrides(ts)
    with monkeypatch.context() as m:
        m.setitem(sys.modules, "netclass", None)
        m.setitem(sys.modules, "idioms", None)
        assert sys.modules["netclass"] is None and sys.modules["idioms"] is None
        for call in (lambda: stick_diagram.load_topology(p), lambda: stick_diagram.run_topology_pipeline(p, ov),
                     lambda: stick_diagram.find_stack_edges(ts), lambda: stick_diagram.find_idiom_matches(ts),
                     lambda: stick_diagram.refine_differential_and_mirror_relations(ts),
                     lambda: stick_diagram.propose_device_roles_gap_fill(ts, {}, [])):
            with contextlib.suppress(ImportError):   # base returns quietly, head raises -- both are 'absence'
                call()
    assert "netclass" not in sys.modules or sys.modules["netclass"] is not None
    got = {
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
    assert got == expected


# ---------------------------------------------------------------- self-checks of the judges
def test_b34_selfcheck_raises_rejects_quiet_fakes():
    for fake in (lambda *a: None, lambda *a: {"unavailable_reason": "x"}, lambda *a: []):
        with pytest.raises(pytest.fail.Exception):
            with pytest.raises(ImportError):
                fake()


def test_b34_selfcheck_exc_problems_rejects_bad_errors():
    e = _b34_expected_path()
    good = ImportError("analog-grammar skill (path %s)" % e)
    good.__cause__ = ModuleNotFoundError("netclass")
    no_name = ImportError("cannot import netclass")   # the search path itself contains 'analog-grammar'
    no_name.__cause__ = ModuleNotFoundError("netclass")
    no_path = ImportError("analog-grammar missing")
    no_path.__cause__ = ModuleNotFoundError("netclass")
    no_cause = ImportError("analog-grammar skill (path %s)" % e)
    assert _b34_exc_problems(good) == []
    assert "no 'analog-grammar' in message" in _b34_exc_problems(no_name)
    assert _b34_exc_problems(no_path) == ["search path missing from message"]
    assert _b34_exc_problems(no_cause) == ["__cause__ is not ImportError"]


class _B34FakeMatch:
    def __init__(self, kind):
        self.kind, self.devices, self.ports, self.note, self.priority = kind, ("M1", "M2"), {"g": "n1"}, "", 1


def test_b34_selfcheck_normalize_equal_and_different():
    assert _B34FakeMatch("dp") != _B34FakeMatch("dp")
    assert _b34_normalize([_B34FakeMatch("dp"), {1.5, 2.5}]) == _b34_normalize([_B34FakeMatch("dp"), {2.5, 1.5}])
    assert _b34_normalize([_B34FakeMatch("dp")]) != _b34_normalize([_B34FakeMatch("cm")])
    assert json.loads(json.dumps(_b34_normalize({"k": (float("nan"), {3, 1})}))) == _b34_normalize({"k": (float("nan"), {1, 3})})
