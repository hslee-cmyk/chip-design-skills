"""B26 backfill 결함 card 초안의 red 시제품(scratch, 커밋하지 않음). card 계약 1·2 문장 그대로."""
import importlib, json, pathlib, sys

_ASSETS_DIR = pathlib.Path(__file__).resolve().parents[2]


def _sr():
    if str(_ASSETS_DIR) not in sys.path:
        sys.path.insert(0, str(_ASSETS_DIR))
    return importlib.import_module("sizing_recipe")


def _b26bf_run(tmp_path, lut, max_rounds):
    sr = _sr()
    r = sr.size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=lut, vds=0.6)
    w = r.W
    s = {"ID": r.ID, "W": w, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0, "gds": r.gm / lut.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0),
         "kind": "nmos", "vds": 0.6, "vsb": 0.0}
    T = sr.Transistor
    row = [T("Ma", "nmos", source="n2", drain="n1", gate="ga", n_fingers=1, finger_w=w, stack_id="seg1"),
           T("Mb", "nmos", source="n4", drain="n2", gate="gb", n_fingers=1, finger_w=w, stack_id="seg1"),
           T("Mp", "nmos", source="n2", drain="n5", gate="gp", n_fingers=1, finger_w=w, stack_id="seg1")]
    p = tmp_path / "b26bf.topology.json"
    p.write_text(json.dumps({"topology_name": "b26bf", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
                             "netlist": [{"name": t.name, "kind": t.kind, "source": t.source, "drain": t.drain,
                                          "gate": t.gate} for t in row],
                             "symmetry": {"matching_pairs": [], "dispositions": []}}), encoding="utf-8")
    ctx = sr.SizingContext(sized={t.name: dict(s) for t in row}, topology_path=str(p))
    return sr.run_matching_safety_with_finger_growth({"seg1": row}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx,
                                                     {"nmos": lut}, {}, [], gm_id_bounds=(11.9, 12.1),
                                                     max_rounds=max_rounds)


def _b26bf_check(res):
    assert [e["pair"] for e in res["relaxed_pairs"]] == [("Ma", "Mb")]
    for e in res["relaxed_pairs"]:
        a, b = e["pair"]
        c3b = [c for c in res["audit"].checks if c.name.startswith("3b.") and f"[{a}/{b}]" in c.name]
        assert len(c3b) == 1
        assert e["interdig_ok"] is c3b[0].ok


def test_b26bf_interdig_ok_in_loop(tmp_path, toy_lut):
    res = _b26bf_run(tmp_path, toy_lut, 2)
    assert res["unresolved_reason"] == "relaxed_to_layout"
    _b26bf_check(res)


def test_b26bf_interdig_ok_after_loop(tmp_path, toy_lut):
    res = _b26bf_run(tmp_path, toy_lut, 1)
    assert res["unresolved_reason"] == "max_rounds_exceeded"
    _b26bf_check(res)
