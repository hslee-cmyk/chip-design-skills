"""IT-1 9회로 변화표: IT-0 AB(as-built base) 대 IT-1 HEAD 측정, 그리고 IT-0 SIM(IT-1 모의 패치) 대 HEAD.
usage: python -I compare_it1.py <it0_raw_dir> <it1_out_dir> <out_json>
원인 분류(승인 규칙, 승인 20261021-it1-o13-scope):
  R1 같은 DC 엣지 제거 / R2 input_tie 제거 / R3 y 키 = 뿌리 넷 / R4 다중 뿌리 정지
"""
import json
import sys
from pathlib import Path

LIB = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
HO = ["cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota"]


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def writers(rec):
    m = (rec or {}).get("m_i1") or {}
    out = {}
    for net, w in m.get("writers") or []:
        out[net] = (w["tier"], w["relation"], w["element"], w["known"], w["y_key"])
    return out


def coords(rec):
    m = (rec or {}).get("m_i1") or {}
    return {d: (c.get("role"), c.get("relation"), c.get("partner")) for d, c in (m.get("coords") or [])}


def theta_y(rec):
    m3 = (rec or {}).get("m_i3")
    if not isinstance(m3, dict):
        return None
    return sorted(k for _t, k in (m3.get("theta_y_components") or []))


def dof(rec):
    d = ((rec or {}).get("m_i5") or {}).get("dof")
    if not isinstance(d, dict):
        return d
    return {"status": d.get("status"), "n_variables": d.get("n_variables"), "n_equations": d.get("n_equations"),
            "structural_rank": d.get("structural_rank"), "n_free": len(d.get("free_variables") or [])}


def summary(rec):
    if rec is None:
        return None
    w = writers(rec)
    co = coords(rec)
    return {
        "stage_a": (rec.get("stage_a") or {}).get("status"),
        "plan_stop": (rec.get("output_structure") or {}).get("plan_stop"),
        "relations": sorted({v[1] for v in w.values()}),
        "n_input_tie": sum(1 for v in w.values() if v[1] == "input_tie"),
        "w4": sorted([n, v[4]] for n, v in w.items() if v[1] == "free_window"),
        "dependents": sorted([d, c[1]] for d, c in co.items() if c[0] == "dependent"),
        "tie_breaks": (rec.get("m_i1") or {}).get("tie_breaks"),
        "theta_y": theta_y(rec),
        "n_theta_y": ((rec.get("m_i3") or {}) if isinstance(rec.get("m_i3"), dict) else {}).get("n_theta_y"),
        "achievability_dof": dof(rec),
        "tie_equations": ((rec.get("m_i5") or {}).get("tie_equations")),
        "m_i6": rec.get("m_i6"),
        "input_w4_roots": ((rec.get("m_i1_r") or {}).get("input_w4_roots")),
        "n_front": ((rec.get("m_i3") or {}) if isinstance(rec.get("m_i3"), dict) else {}).get("n_front"),
    }


def classify(c, a, s, ab, it):
    """변화마다 원인. 설명 못 하면 'UNEXPLAINED'."""
    rows = []
    if a is None or it is None:
        return [{"field": "record", "cause": "UNEXPLAINED" if (a is None) != (it is None) else "n/a"}]
    wa, wi = writers(ab), writers(it)
    tie_nets = {n for n, v in wa.items() if v[1] == "input_tie"}
    for net in sorted(set(wa) | set(wi)):
        x, y = wa.get(net), wi.get(net)
        if x == y:
            continue
        if x and y and x[1] == "free_window" and y[1] == "free_window" and x[4] == "input_common_mode" and y[4] == net \
                and x[:4] == y[:4]:
            cause = "R3 y 키 = 뿌리 넷"
        elif x and x[1] == "input_tie":
            cause = "R1+R2 같은 DC 엣지·input_tie 제거(입력 포트가 MOS·저항 트리 경로로 쓰임)"
        elif tie_nets and x and y:
            cause = "R1 같은 DC 엣지 제거에 따른 Kruskal 트리 재선택(입력 성분)"
        else:
            cause = "UNEXPLAINED"
        rows.append({"field": "node.dc_writer", "net": net, "it0": x, "it1": y, "cause": cause})
    ca, ci = coords(ab), coords(it)
    for d in sorted(set(ca) | set(ci)):
        if ca.get(d) != ci.get(d):
            cause = "R1 같은 DC 엣지 제거(입력쌍 경로 나무화 -> 옛 cycle_vgs 종속이 writer)" if tie_nets else "UNEXPLAINED"
            rows.append({"field": "device.dc_coord", "device": d, "it0": ca.get(d), "it1": ci.get(d), "cause": cause})
    if a["tie_breaks"] != s_tb(it):
        old = [t for t in (a["tie_breaks"] or [])]
        rows.append({"field": "graph.dc_tie_breaks", "it0": old, "it1": it_tb(it),
                     "cause": "R2 input_tie_order 결정 제거" if all(
                         (t.get("decision") if isinstance(t, dict) else None) == "input_tie_order"
                         for t in old if t not in (it_tb(it) or [])) else "UNEXPLAINED"})
    if a["theta_y"] != c["theta_y"]:
        sa, si = set(a["theta_y"] or []), set(c["theta_y"] or [])
        ok = (sa - si) <= {"input_common_mode"} and all(k in {v[0] for v in [(n,) for n in wi]} for k in si - sa)
        rows.append({"field": "theta_schema.y", "it0": a["theta_y"], "it1": c["theta_y"],
                     "cause": "R3 y 키 = 뿌리 넷(input_common_mode -> 입력 포트 뿌리 넷)" if ok else "UNEXPLAINED"})
    if a["achievability_dof"] != c["achievability_dof"]:
        da, di = a["achievability_dof"] or {}, c["achievability_dof"] or {}
        ok = isinstance(da, dict) and isinstance(di, dict) and da.get("status") == di.get("status") \
            and da.get("n_equations", 0) - di.get("n_equations", 0) == (a["tie_equations"] or 0)
        rows.append({"field": "achievability.dof", "it0": da, "it1": di,
                     "cause": "R2 input_tie 제거 -> tie: 등식 제거(n_equations -= tie_equations)" if ok else "UNEXPLAINED"})
    if a["plan_stop"] != c["plan_stop"]:
        rows.append({"field": "plan_stop", "it0": a["plan_stop"], "it1": c["plan_stop"],
                     "cause": "R4 다중 뿌리 정지" if "input_port_multiple_roots" in json.dumps(c["plan_stop"]) else "UNEXPLAINED"})
    return rows


def s_tb(rec):
    return (rec.get("m_i1") or {}).get("tie_breaks")


it_tb = s_tb


def main():
    raw, it1, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    res = {"library": {}, "heldout": {}}
    for c in LIB + HO:
        ab, sim, it, rep2 = (load(raw / "AB" / (c + ".json")), load(raw / "SIM" / (c + ".json")),
                             load(it1 / "IT1" / (c + ".json")), load(it1 / "IT1_rep2" / (c + ".json")))
        a, s, i = summary(ab), summary(sim), summary(it)
        row = {"it0_AB": a, "it0_SIM": s, "it1_HEAD": i}
        if c in LIB:
            row["changes"] = classify(i, a, s, ab, it) if a and i and a != i else []
            plan_keys = ("relations", "w4", "dependents", "tie_breaks", "theta_y", "achievability_dof", "plan_stop", "input_w4_roots")
            row["head_equals_sim_plan"] = None if s is None or i is None else {k: s.get(k) == i.get(k) for k in plan_keys}
            if rep2 is not None and it is not None:
                drop = ("wall_s", "tag", "repo", "kernel_window_status", "m_i2")
                row["rep2_equal_excl_time"] = {k: v for k, v in it.items() if k not in drop} == {k: v for k, v in rep2.items() if k not in drop}
            row["n_unexplained"] = sum(1 for r in row["changes"] if r.get("cause") == "UNEXPLAINED")
        res["library" if c in LIB else "heldout"][c] = row
    res["total_unexplained"] = sum(r["n_unexplained"] for r in res["library"].values())
    Path(out).write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    for c, r in res["library"].items():
        print(c, "changes", len(r["changes"]), "unexplained", r["n_unexplained"], "sim_eq", r.get("head_equals_sim_plan"),
              "rep2", r.get("rep2_equal_excl_time"))
    print("TOTAL_UNEXPLAINED", res["total_unexplained"])


if __name__ == "__main__":
    main()
