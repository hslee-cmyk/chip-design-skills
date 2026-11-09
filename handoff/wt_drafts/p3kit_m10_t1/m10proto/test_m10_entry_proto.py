"""measure-only prototype of the M10 entry test shape (design 30 §2.3 (ii)(iii)) -- NOT a role artifact.
Golden = base (M9-merge) harness behaviour captured by capture_base.py with the same calls."""
import ast
import contextlib
import hashlib
import inspect
import io
import json
import os
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.abspath(os.path.join(_HERE, "..", ".."))
_ROOT = os.path.abspath(os.path.join(_ASSETS, "..", "..", ".."))
sys.path.insert(0, _ASSETS)
sys.path.insert(0, os.path.join(_ROOT, "workspaces"))
sys.path.insert(0, _HERE)
import gmid_design_pipeline as G  # noqa: E402
import run_harness as H  # noqa: E402
import _m10_scen as SC  # noqa: E402

GOLD = json.load(open(os.path.join(_HERE, "m10_golden.json"), encoding="utf-8"))


def _ws(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "WORKSPACES_DIR", str(tmp_path))
    for c in H.SPECS.values():
        os.makedirs(os.path.join(str(tmp_path), c["report_dir"]), exist_ok=True)


def test_entry_signature():
    sig = inspect.signature(G.run_gmid_design_pipeline)
    ps = list(sig.parameters.values())
    assert [p.name for p in ps] == ["spec", "topology_path", "search", "output_dir"]
    assert ps[0].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY and p.default is inspect.Parameter.empty for p in ps[1:])


def test_entry_does_not_import_workspaces():
    tree = ast.parse(open(G.__file__, encoding="utf-8").read())
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module.split(".")[0])
    assert "run_harness" not in mods
    code = ("import sys; sys.path.insert(0, %r); import gmid_design_pipeline, os; "
            "bad=[m for m,o in sys.modules.items() if 'workspaces' in os.path.normcase(str(getattr(o,'__file__','') or ''))]; "
            "print(bad); sys.exit(1 if bad or 'run_harness' in sys.modules else 0)") % _ASSETS
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=_ASSETS)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("key", sorted(H.SPECS))
def test_harness_run_passes_entry_arguments(key, tmp_path, monkeypatch):
    _ws(tmp_path, monkeypatch)
    got = []
    monkeypatch.setattr(H, "run_gmid_design_pipeline", lambda *a, **k: got.append((a, k)))
    H.run(key)
    assert len(got) == 1
    a, k = got[0]
    cfg = H.SPECS[key]
    spec = cfg["spec_fn"]()
    spec.setdefault("floorplan_target", {"max_aspect_ratio": H.FLOORPLAN_MAX_ASPECT_RATIO,
                                         "min_packing_density": H.FLOORPLAN_MIN_PACKING_DENSITY})
    spec.setdefault("max_layout_retry_rounds", H.MAX_ITERS)
    assert len(a) == 1 and set(k) == {"topology_path", "search", "output_dir"}
    assert SC._norm(a[0], ("<x>", "<y>")) == SC._norm(spec, ("<x>", "<y>"))
    assert a[0]["floorplan_target"] == spec["floorplan_target"] and a[0]["max_layout_retry_rounds"] == spec["max_layout_retry_rounds"]
    assert k["topology_path"] == os.path.join(H.LIBRARY_DIR, cfg["topology_file"])
    assert k["output_dir"] == os.path.join(str(tmp_path), cfg["report_dir"])
    assert k["search"] == {"grid_points_per_theta": cfg["grid_points_per_theta"],
                           "search_method": cfg.get("search_method", "grid"), "slsqp_kwargs": cfg.get("slsqp_kwargs")}


def test_harness_rejects_unknown_key():
    with pytest.raises(ValueError):
        H.run("no_such_circuit")


@pytest.mark.parametrize("name", sorted(SC.SCEN))
def test_entry_branch_matches_base(name, tmp_path, monkeypatch):
    _ws(tmp_path, monkeypatch)
    od = os.path.join(str(tmp_path), H.SPECS["folded_cascode"]["report_dir"])
    got = SC.run_scenario([G, H], name, lambda: H.run("folded_cascode"), od, H._REPO_ROOT)
    exp = GOLD["scenarios"][name]
    assert got["stdout"] == exp["stdout"]
    assert got["calls"] == exp["calls"]


def _canon(p):
    return hashlib.sha256(json.dumps(json.load(open(p, encoding="utf-8")), sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


@pytest.mark.parametrize("key", ["folded_cascode", "two_stage_ota"])
def test_entry_real_run_matches_base(key, tmp_path, monkeypatch):
    _ws(tmp_path, monkeypatch)
    cfg = H.SPECS[key]
    od = os.path.join(str(tmp_path), cfg["report_dir"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        H.run(key)
    exp = GOLD["real"][key]
    assert SC._s(buf.getvalue(), od, H._REPO_ROOT) == exp["stdout"]
    stem = cfg["topology_file"].removesuffix(".topology.json")
    ip, rp = os.path.join(od, stem + ".instance.json"), os.path.join(od, stem + ".report.html")
    assert (_canon(ip) if os.path.exists(ip) else None) == exp["instance_canon_sha256"]
    assert (hashlib.sha256(open(rp, "rb").read()).hexdigest() if os.path.exists(rp) else None) == exp["report_sha256"]


def test_entry_propagates_exceptions(tmp_path, monkeypatch):
    """design 00-common §10.2-6: the caller (harness / Phase 4 tool) catches -- the entry does not swallow."""
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(G, "optimize_full_circuit_budget", boom)
    spec = H.SPECS["folded_cascode"]["spec_fn"]()
    spec.setdefault("floorplan_target", {"max_aspect_ratio": H.FLOORPLAN_MAX_ASPECT_RATIO,
                                         "min_packing_density": H.FLOORPLAN_MIN_PACKING_DENSITY})
    with pytest.raises(RuntimeError, match="boom"):
        G.run_gmid_design_pipeline(spec, topology_path=os.path.join(H.LIBRARY_DIR, "folded_cascode.topology.json"),
                                   search={"grid_points_per_theta": 3, "search_method": "grid", "slsqp_kwargs": None},
                                   output_dir=str(tmp_path))


def test_entry_thresholds_come_from_spec(tmp_path, monkeypatch):
    """oracle (a): the floorplan verdict printed by the entry uses spec['floorplan_target'] (single source -- design D-5 text)."""
    import types
    pr = {"layout_retry_rounds": [], "floorplan": types.SimpleNamespace(aspect_ratio=1.8, packing_density=0.25), "row_split": {},
          "box_shape": types.SimpleNamespace(ok=True, rectangular=True, width_ratio=1.0, approx=False, row_widths=[], row_heights=[]),
          "coverage": types.SimpleNamespace(ok=True, missing=[])}
    monkeypatch.setattr(G, "optimize_full_circuit_budget", lambda *a, **k: {"pipeline_result": pr, "theta_star": {}, "audit_ok": True,
                                                                             "metrics": {}, "sizing": {}})
    def no_audit(*a, **k):
        raise ValueError("x")
    monkeypatch.setattr(G, "run_full_circuit_audit_from_topology", no_audit)
    monkeypatch.setattr(G, "save_instance_json", lambda *a, **k: None)
    spec = {"floorplan_target": {"max_aspect_ratio": 2.0, "min_packing_density": 0.3}}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        G.run_gmid_design_pipeline(spec, topology_path=os.path.join(H.LIBRARY_DIR, "folded_cascode.topology.json"),
                                   search={"grid_points_per_theta": 3, "search_method": "grid", "slsqp_kwargs": None},
                                   output_dir=str(tmp_path))
    out = buf.getvalue()
    assert "(<= 2.0 ? True)" in out and "(>= 0.3 ? False)" in out
    assert "floorplan_ok=False" in out
