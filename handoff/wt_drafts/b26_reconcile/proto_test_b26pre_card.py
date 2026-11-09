"""b26pre 시제품 v2(scratch) -- draft_b26pre.spec.md 계약 1~8 문장 그대로. 커밋하지 않는다."""
import importlib
import json
import pathlib
import sys

_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]


def _mods():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("sizing_recipe"), importlib.import_module("stick_diagram")


def _b26pre_r(sr, lut):
    return sr.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=lut, vds=0.6)


def _b26pre_S(sr, lut):
    r = _b26pre_r(sr, lut)
    gds = r.gm / lut.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0)
    return {"ID": r.ID, "W": r.W, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0, "gds": gds, "kind": "nmos", "vds": 0.6, "vsb": 0.0}


def _b26pre_topo(tmp_path, netlist, name="b26pre.topology.json", **extra):
    p = tmp_path / name
    data = {"topology_name": "b26pre_synthetic", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
            "netlist": netlist, "symmetry": {"matching_pairs": [], "dispositions": []}}
    data.update(extra)
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _b26pre_nl(trs):
    return [{"name": t.name, "kind": t.kind, "source": t.source, "drain": t.drain, "gate": t.gate} for t in trs]


def _b26pre_ctx(sr, lut, names, topo):
    s = _b26pre_S(sr, lut)
    return sr.SizingContext(sized={n: dict(s) for n in names}, topology_path=topo)


def _b26pre_star(sr, w):
    T = sr.Transistor
    return [T("M1", "nmos", source="na", drain="nx", gate="g1", n_fingers=1, finger_w=w, stack_id="row"),
            T("M2", "nmos", source="nx", drain="nb", gate="g2", n_fingers=1, finger_w=w, stack_id="row"),
            T("M3", "nmos", source="nx", drain="nc", gate="g3", n_fingers=1, finger_w=w, stack_id="row")]


def _b26pre_pair(sr, w):
    T = sr.Transistor
    return [T("Ma", "nmos", source="vtail", drain="nda", gate="ga", n_fingers=1, finger_w=w, stack_id="seg1"),
            T("Mb", "nmos", source="vtail", drain="ndb", gate="gb", n_fingers=1, finger_w=w, stack_id="seg1")]


def _b26pre_metrics(w):
    return ({"pair_area": {"type": "sum_area", "devices": ["Ma", "Mb"]}},
            [{"metric": "pair_area", "op": "<=", "value": 2 * w * 0.5e-6 * 3.0}])


def _b26pre_euler_ok(sd, res):
    eul = [c for c in res["audit"].checks if c.name.startswith("1. euler[")]
    built = sd.build_stick_diagram([t for v in res["rows"].values() for t in v])
    return bool(eul) and all(c.ok for c in eul) and all(r.status == "ok" for r in built.values())


# 계약 1
def test_b26pre_ofcb_lutless_repair(tmp_path, toy_lut):
    sr, _sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    s = _b26pre_S(sr, toy_lut)
    names = ["Ma", "Mb"]
    topo = _b26pre_topo(
        tmp_path, _b26pre_nl(_b26pre_pair(sr, w)),
        device_roles={n: {"gm_id_role": "", "L_role": ""} for n in names},
        symmetry={"matching_pairs": [{"names": names, "matching_sensitivity": "offset", "current_forced": False}],
                  "dispositions": []},
        sizing_roles={"metrics": {"pair_area": {"type": "sum_area", "unit": "m^2", "devices": names}},
                      "constraints": [{"metric": "pair_area", "op": "<=", "value": 2 * w * 0.5e-6 * 3}]})
    spec = {"known_sizing": {n: dict(s) for n in names}, "min_finger_w": 0.1e-6, "max_finger_w": 40e-6, "L_min": 0.1e-6,
            "gm_id_bounds": (2.0, 28.0), "stack_groups_override": {"pair_row": names}}
    res = sr.optimize_full_circuit_budget(topo, spec)
    pr = res["pipeline_result"]
    assert "repaired_rows" in pr and "repaired_audit" in pr
    assert "growth_rounds" not in pr
    assert res["audit_ok"] is False
    c3 = [c for c in pr["repaired_audit"].checks if c.name.startswith("3c.")]
    assert len(c3) == 1 and c3[0].ok is False
    rr = pr["repaired_rows"]
    assert all(k.startswith("pair_row_repair") for k in rr)
    assert sorted(t.name for v in rr.values() for t in v) == ["Ma", "Mb"]
    assert {t.stack_id for t in pr["transistors"]} == set(rr)


# 계약 2
def test_b26pre_euler_fixup_group_split(tmp_path, toy_lut):
    sr, _sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    star = _b26pre_star(sr, w)
    ctx = _b26pre_ctx(sr, toy_lut, ["M1", "M2", "M3"], _b26pre_topo(tmp_path, _b26pre_nl(star)))
    rows, _c = sr._fixup_euler_blocked_rows({"row": star}, [], {}, ctx, {"nmos": toy_lut}, {}, [])
    assert set(rows) == {"row_seg0", "row_seg1"}
    names = [t.name for v in rows.values() for t in v]
    assert sorted(names) == ["M1", "M2", "M3"] and len(set(names)) == 3
    assert all(len(v) >= 1 for v in rows.values())
    assert all(t.stack_id == k for k, v in rows.items() for t in v)


def _b26pre_both_ctx(sr, lut, tmp_path, w, names):
    topo = _b26pre_topo(tmp_path, _b26pre_nl(_b26pre_pair(sr, w) + _b26pre_star(sr, w)))
    return _b26pre_ctx(sr, lut, names, topo)


# 계약 3 (a)
def test_b26pre_growth_zero_rounds(tmp_path, toy_lut):
    sr, _sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    metrics, loose = _b26pre_metrics(w)
    res = sr.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(sr, w)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
        _b26pre_both_ctx(sr, toy_lut, tmp_path, w, ["Ma", "Mb"]), {"nmos": toy_lut}, metrics, loose,
        gm_id_bounds=(2.0, 28.0), max_rounds=0)
    assert res["growth_rounds"] == []
    assert res["unresolved_pair"] == "unknown" and res["unresolved_reason"] == "max_rounds_exceeded"
    assert res["audit"].ok is False
    assert "seg1" not in res["rows"] and all(k.startswith("seg1_repair") for k in res["rows"])
    assert sorted(t.name for v in res["rows"].values() for t in v) == ["Ma", "Mb"]


# 계약 3 (b)
def test_b26pre_growth_zero_rounds_euler(tmp_path, toy_lut):
    sr, sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    metrics, loose = _b26pre_metrics(w)
    res = sr.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(sr, w), "row": _b26pre_star(sr, w)}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"},
        _b26pre_both_ctx(sr, toy_lut, tmp_path, w, ["Ma", "Mb", "M1", "M2", "M3"]), {"nmos": toy_lut}, metrics, loose,
        gm_id_bounds=(2.0, 28.0), max_rounds=0)
    assert _b26pre_euler_ok(sd, res)


# 계약 3 (c)
def test_b26pre_growth_already_ok(tmp_path, toy_lut):
    sr, _sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    metrics, loose = _b26pre_metrics(w)
    res = sr.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(sr, w)}, [("Ma", "Mb")], {("Ma", "Mb"): "ratio"},
        _b26pre_both_ctx(sr, toy_lut, tmp_path, w, ["Ma", "Mb"]), {"nmos": toy_lut}, metrics, loose,
        gm_id_bounds=(2.0, 28.0))
    assert res["unresolved_pair"] is None and res["unresolved_reason"] is None
    assert res["growth_rounds"] == [] and res["relaxed_pairs"] == []
    assert res["audit"].ok is True
    assert {k: [(t.name, t.n_fingers, t.stack_id) for t in v] for k, v in res["rows"].items()} == \
        {"seg1": [("Ma", 1, "seg1"), ("Mb", 1, "seg1")]}


# 계약 3 (d)
def test_b26pre_growth_pair_not_found(tmp_path, toy_lut):
    sr, sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    metrics, loose = _b26pre_metrics(w)
    res = sr.run_matching_safety_with_finger_growth(
        {"seg1": _b26pre_pair(sr, w), "row": _b26pre_star(sr, w)}, [("Ma", "Mx")], {("Ma", "Mx"): "offset"},
        _b26pre_both_ctx(sr, toy_lut, tmp_path, w, ["Ma", "Mb", "M1", "M2", "M3"]), {"nmos": toy_lut}, metrics, loose,
        gm_id_bounds=(2.0, 28.0))
    assert res["unresolved_pair"] == ("Ma", "Mx") and res["unresolved_reason"] == "pair_not_found"
    assert res["growth_rounds"] == [] and res["relaxed_pairs"] == []
    assert _b26pre_euler_ok(sd, res)


# 계약 3 (e)
def test_b26pre_growth_only_3b_left(tmp_path, toy_lut):
    sr, sd = _mods()
    w = _b26pre_r(sr, toy_lut).W
    res = sr.run_matching_safety_with_finger_growth(
        {"row": _b26pre_star(sr, w)}, [], {}, _b26pre_both_ctx(sr, toy_lut, tmp_path, w, ["M1", "M2", "M3"]),
        {"nmos": toy_lut}, {}, [], gm_id_bounds=(2.0, 28.0))
    assert res["unresolved_pair"] is None and res["unresolved_reason"] == "only_3b_failures_left"
    assert res["growth_rounds"] == []
    assert res["audit"].ok is True
    assert _b26pre_euler_ok(sd, res)


# 계약 4
_B26PRE_KEYS = [("hub_merge", "nmos", "gnd"), ("hub_merge", "nmos", "ntail"),
                ("current_mirror", "nmos", "nb"), ("diff_pair", "nmos", "ntail")]


def _b26pre_audit(tmp_path, omit):
    _sr, sd = _mods()
    nl = [{"name": "M1", "kind": "nmos", "source": "gnd", "drain": "nb", "gate": "nb"},
          {"name": "M2", "kind": "nmos", "source": "gnd", "drain": "nout", "gate": "nb"},
          {"name": "Ma", "kind": "nmos", "source": "ntail", "drain": "nda", "gate": "nga"},
          {"name": "Mb", "kind": "nmos", "source": "ntail", "drain": "ndb", "gate": "ngb"}]
    disp = [{"tag": t, "kind": k, "key": n, "category": "real_match", "reason": "b26pre"}
            for (t, k, n) in _B26PRE_KEYS if (t, k, n) != omit]
    topo = _b26pre_topo(tmp_path, nl, symmetry={"matching_pairs": [], "dispositions": disp},
                        _netlist_sections_structured={"blk": {"devices": ["M1", "M2", "Ma", "Mb"]}})
    res = sd.run_full_circuit_audit_from_topology(topo)
    c3 = [c for c in res.checks if c.name.startswith("3.")]
    assert len(c3) == 1
    return c3[0]


def test_b26pre_full_audit_all_disposed(tmp_path):
    assert _b26pre_audit(tmp_path, None).ok is True


def test_b26pre_full_audit_mirror_undisposed(tmp_path):
    omit = ("current_mirror", "nmos", "nb")
    c3 = _b26pre_audit(tmp_path, omit)
    assert c3.ok is False and repr(omit) in c3.detail


def test_b26pre_full_audit_diffpair_undisposed(tmp_path):
    omit = ("diff_pair", "nmos", "ntail")
    c3 = _b26pre_audit(tmp_path, omit)
    assert c3.ok is False and repr(omit) in c3.detail


def test_b26pre_full_audit_hub_undisposed(tmp_path):
    omit = ("hub_merge", "nmos", "gnd")
    c3 = _b26pre_audit(tmp_path, omit)
    assert c3.ok is False and repr(omit) in c3.detail


# 계약 5·6
def _b26pre_cas(T):
    return [T("M1", "nmos", source="ntail", drain="nx1", gate="ninp"), T("M2", "nmos", source="ntail", drain="nx2", gate="ninn"),
            T("M1c", "nmos", source="nx1", drain="no1", gate="nvc"), T("M2c", "nmos", source="nx2", drain="no2", gate="nvc"),
            T("M3", "pmos", source="vdd", drain="no1", gate="nvp"), T("M4", "pmos", source="vdd", drain="no2", gate="nvp"),
            T("M5", "nmos", source="gnd", drain="ntail", gate="nvb")]


def test_b26pre_resolve_stack_candidates():
    sr, _sd = _mods()
    cas = _b26pre_cas(sr.Transistor)
    groups = sr.resolve_stack_layout(cas, [], {})
    members = sorted(m for g in groups.values() for m in g)
    assert members == sorted(t.name for t in cas)
    kind = {t.name: t.kind for t in cas}
    assert all(len({kind[m] for m in g}) == 1 for g in groups.values())
    assert any({"M1", "M2"} <= set(g) for g in groups.values())


def test_b26pre_vsid_gap_fill_no_ports():
    _sr, sd = _mods()
    p = sd.propose_vertical_stack_id_gap_fill(_b26pre_cas(sd.Transistor), [], {"M1": {"vertical_stack_id": "colA"}})
    assert p["proposals"] == {"M1c": "colA", "M3": "colA"}


def test_b26pre_vsid_gap_fill_ports():
    _sr, sd = _mods()
    p = sd.propose_vertical_stack_id_gap_fill(_b26pre_cas(sd.Transistor), [], {"M1": {"vertical_stack_id": "colA"}},
                                             inputs=("ninp", "ninn"), outputs=("no1", "no2"), biases=("nvb", "nvc", "nvp"))
    assert p["proposals"] == {"M1c": "colA", "M2": "colA", "M2c": "colA", "M3": "colA", "M4": "colA"}
    assert p["conflicts"] == {}
    assert sorted(sorted(c) for c in p["components_used"]) == [["M1", "M1c", "M2", "M2c", "M3", "M4"], ["M5"]]


# 계약 7
def test_b26pre_case_collisions(tmp_path):
    _sr, sd = _mods()
    N = lambda n, k, s, d, g: {"name": n, "kind": k, "source": s, "drain": d, "gate": g}  # noqa: E731
    nl = [N("M1", "nmos", "ntail", "no1", "ninp"), N("M2", "nmos", "ntail", "no2", "ninn"),
          N("M3", "pmos", "vdd", "no1", "no1"), N("M4", "pmos", "vdd", "no2", "no1"),
          N("M5", "nmos", "gnd", "ntail", "nvb"), N("M6", "nmos", "gnd", "NQ", "nvb"), N("M7", "nmos", "gnd", "nq", "nvb")]
    _t, meta = sd.load_topology(_b26pre_topo(tmp_path, nl))
    cc = [e["case_collisions"] for e in (meta["_device_roles_gap_fill_review_needed"] or []) if "case_collisions" in e]
    assert cc == [{"nq": {"NQ", "nq"}}]
