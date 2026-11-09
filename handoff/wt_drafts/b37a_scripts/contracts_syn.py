"""probe_path3용 합성 topology(계약 문서의 2단 OTA·tele + 변형)."""
def _t(netlist, ports):
    return {"topology_name": "syn", "schema_version": "2.0", "supply_nets": ["vdd", "gnd"],
            "symmetry": {"matching_pairs": [], "dispositions": []}, "netlist": netlist, "ports": ports}
P = {"inp": {"role": "differential_input_p"}, "inn": {"role": "differential_input_n"}}
SYN = {
 "ota": _t([dict(name="M1", kind="nmos", gate="inp", drain="x", source="tail"),
            dict(name="M2", kind="nmos", gate="inn", drain="out", source="tail"),
            dict(name="M3", kind="pmos", gate="x", drain="x", source="vdd"),
            dict(name="M4", kind="pmos", gate="x", drain="out", source="vdd"),
            dict(name="M5", kind="nmos", gate="nb", drain="tail", source="gnd")], dict(P, out={"role": "single_ended_output"})),
 "tele": _t([dict(name="M0", kind="nmos", gate="nb", drain="t", source="gnd"),
             dict(name="M1", kind="nmos", gate="inp", drain="x", source="t"),
             dict(name="M2", kind="nmos", gate="inn", drain="y", source="t"),
             dict(name="M3", kind="nmos", gate="nc", drain="o1", source="x"),
             dict(name="M4", kind="nmos", gate="nc", drain="o2", source="y"),
             dict(name="M5", kind="pmos", gate="o1", drain="o1", source="vdd"),
             dict(name="M6", kind="pmos", gate="o1", drain="o2", source="vdd")], dict(P, o2={"role": "single_ended_output"})),
}
