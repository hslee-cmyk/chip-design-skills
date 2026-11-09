"""b26pre 도달성 실험 2: optimize_full_circuit_budget의 lut_by_kind 없는 matching-safety 분기. 결과 C:/g87/out/exp2.txt."""
import json, os, sys, tempfile, traceback
A = "C:/g87/b1/skills/analog-gmid-design/assets"
sys.path.insert(0, A)
import sizing_recipe as sr  # noqa
OUT = open("C:/g87/out/exp2.txt", "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s); OUT.write(s + "\n"); OUT.flush()


lut = sr.build_toy_lut()
L, vds = 0.5e-6, 0.6
r = sr.size_transistor(gm=200e-6, gm_id=12.0, L=L, lut=lut, vds=vds)
gds = r.gm / lut.gm_gds_ratio(12.0, L, vds, 0.0)
names = ["Ma", "Mb"]
netlist = [{"name": "Ma", "kind": "nmos", "source": "vtail", "drain": "da", "gate": "ga"},
           {"name": "Mb", "kind": "nmos", "source": "vtail", "drain": "db", "gate": "gb"}]
known = {n: {"ID": r.ID, "W": r.W, "L": L, "gm": r.gm, "gm_id": 12.0, "gds": gds, "kind": "nmos",
             "vds": vds, "vsb": 0.0} for n in names}
for with_lut in (False, True):
    d = tempfile.mkdtemp(dir="C:/g87")
    p = os.path.join(d, "pair.topology.json")
    json.dump({"topology_name": "b26pre_pair", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
               "netlist": netlist, "device_roles": {n: {"gm_id_role": "", "L_role": ""} for n in names},
               "symmetry": {"matching_pairs": [{"names": names, "matching_sensitivity": "offset", "current_forced": False}],
                            "dispositions": []},
               "sizing_roles": {"metrics": {"pair_area": {"type": "sum_area", "unit": "m^2", "devices": names}},
                                "constraints": [{"metric": "pair_area", "op": "<=", "value": 2 * r.W * L * 3}]}},
              open(p, "w", encoding="utf-8"))
    spec = {"known_sizing": known, "min_finger_w": 0.1e-6, "max_finger_w": 40e-6, "L_min": 0.1e-6,
            "gm_id_bounds": (2.0, 28.0), "stack_groups_override": {"pair_row": names}}
    if with_lut:
        spec["lut_by_kind"] = {"nmos": lut}
    try:
        res = sr.optimize_full_circuit_budget(p, spec)
        pr = res["pipeline_result"]
        log("with_lut", with_lut, "keys", sorted(pr.keys()))
        log("  audit_ok", res.get("audit_ok"), "repaired_rows" in pr,
            {k: [(t.name, t.n_fingers) for t in v] for k, v in (pr.get("repaired_rows") or {}).items()})
        a = pr["audit_row_split"]
        log("  audit", [(c.name, c.ok) for c in a.checks])
        log("  growth", pr.get("growth_rounds"), pr.get("unresolved_reason"))
        log("  transistors", [(t.name, t.n_fingers, t.stack_id) for t in pr["transistors"]])
        if pr.get("repaired_audit") is not None:
            log("  repaired_audit is audit_row_split", pr["repaired_audit"] is pr["audit_row_split"])
    except Exception:
        log("with_lut", with_lut, "EXC", traceback.format_exc()[-1500:])
