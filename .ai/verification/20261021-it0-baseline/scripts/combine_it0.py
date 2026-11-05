"""IT-0 회로별 측정 결과(out/run/<side>/<circuit>.json) -> it0_table.json·report_items.json·reproduced_numbers.json·checks_raw.json.
usage: python -I combine_it0.py <run_dir> <dest_dir>
값을 새로 계산하지 않는다 -- 회로별 측정 파일의 칸을 모으고, 보고 조건(spec card '사용자 보고 항목')과 V4(두 실행 비트 동일)·래퍼 무해(front_fp 동일)만 대조한다."""
import json
import sys
from pathlib import Path

LIB = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
HO = ["cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota"]
DECLARED = ["pushpull_follower_buffer", "sf_pushpull_output_opamp"]
# O-66 승인 표(_drafts/evidence/2026-10-21/de1_output_structure_13.md §2, 15출력) -- 비교 대상(입력)
O66 = {("common_gate_amplifier", "vout"): "high_impedance", ("current_reuse_telescopic_ota", "Vom"): "kvl_fixed",
       ("current_reuse_telescopic_ota", "Vop"): "kvl_fixed", ("folded_cascode", "out"): "high_impedance",
       ("ngcc_3stage_ff", "Vout"): "high_impedance", ("nmcnr_amplifier", "Vout"): "kvl_fixed",
       ("pushpull_follower_buffer", "vout"): "kvl_fixed", ("sf_pushpull_output_opamp", "vout"): "high_impedance",
       ("two_stage_ota", "OUT"): "high_impedance", ("two_stage_ota_sf", "vout"): "high_impedance",
       ("cnr_ota", "VOP"): "kvl_fixed", ("cnr_ota", "VON"): "kvl_fixed", ("erfc_ota", "out"): "high_impedance",
       ("r2r_opamp", "Vo"): "kvl_fixed", ("rfc_ota", "out"): "high_impedance"}
CMD = "C:/Python314/python.exe -I scripts/measure_it0.py <iso-ab|iso-sim> <AB|SIM> <회로> <library|heldout> <out>"


def load(run, side, c):
    p = run / side / (c + ".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def main():
    run, dest = Path(sys.argv[1]), Path(sys.argv[2])
    dest.mkdir(parents=True, exist_ok=True)
    keys = {"m_i1": "m_i1", "m_i1_r": "m_i1_r", "m_i2": "m_i2", "m_i3": "m_i3", "m_i4": "m_i4", "m_i5": "m_i5", "m_i6": "m_i6",
            "s_p_sign": "s_p_sign", "kernel_window_status": "kernel_window_status", "front_empty": "front_empty",
            "drive_pair_nets": "drive_pair_nets", "feedback_slot": "feedback_slot", "loop_cut": "loop_cut"}
    sides_for = {"m_i1": ("AB", "SIM"), "m_i1_r": ("SIM", "AB"), "m_i2": ("AB", "SIM"), "m_i3": ("AB", "SIM"), "m_i4": ("SIM", "AB"),
                 "m_i5": ("AB", "SIM"), "m_i6": ("AB", "SIM"), "s_p_sign": ("SIM", "AB"), "kernel_window_status": ("AB", "SIM"),
                 "front_empty": ("AB", "SIM"), "drive_pair_nets": ("AB",), "feedback_slot": ("AB",), "loop_cut": ("AB", "SIM")}
    table = {}
    missing = []
    for col, k in keys.items():
        table[k] = {}
        for c in LIB:
            table[k][c] = {}
            for side in sides_for[col]:
                r = load(run, side, c)
                v = None if r is None else r.get(col)
                if v is None:
                    missing.append([col, c, side, "미측정: " + ("결과 파일 없음" if r is None else "칸 없음(실행 중단 -- 로그 log_%s_%s.txt)" % (side, c))])
                table[k][c][side] = {"value": v, "source": CMD.replace("<회로>", c) + " -- 칸 " + col}
    # m_i1_r 키 분할(spec card: multi_root·isolated_input·f_component_undeclared)
    for sub in ("multi_root", "isolated_input", "f_component_undeclared"):
        table[sub] = {c: {s: {"value": (None if v["value"] is None else v["value"].get(sub)), "source": v["source"]}
                          for s, v in table["m_i1_r"][c].items()} for c in LIB}
    # OS 13회로
    os_tab, o66_diff, sos1, sos2t, sos2e = {}, [], [], [], []
    for c in LIB + HO:
        r = load(run, "AB", c)
        v = None if r is None else r.get("output_structure")
        os_tab[c] = {"AB": {"value": v, "source": CMD.replace("<회로>", c) + " -- 칸 output_structure"}}
        if v is None:
            missing.append(["output_structure", c, "AB", "미측정"])
            continue
        for row in v.get("rows", ()):
            exp = O66.get((c, row["output"]))
            if exp != row["class"]:
                o66_diff.append([c, row["output"], row["class"], exp])
            if row.get("s_os1"):
                sos1.append([c, row["output"]])
        if v.get("s_os2_tuple"):
            sos2t.append(c)
        if v.get("s_os2_empty"):
            sos2e.append(c)
    seen = {(c, row["output"]) for c in os_tab for row in ((os_tab[c]["AB"]["value"] or {}).get("rows", ()))}
    for k in O66:
        if k not in seen:
            o66_diff.append([k[0], k[1], None, O66[k]])
    table["output_structure"] = os_tab
    # M-I7
    mi7 = {}
    for c in DECLARED:
        ab, sim = load(run, "AB", c), load(run, "SIM", c)
        if ab is None or sim is None or "m_i1" not in ab or "m_i1" not in sim:
            mi7[c] = {"value": None, "why": "미측정(결과 없음)"}
            continue
        fa, fs = ab["m_i1"]["fields_fp"], sim["m_i1"]["fields_fp"]
        mi7[c] = {"value": {f: fa[f] == fs[f] for f in fa}, "ab_fp": fa, "sim_fp": fs}
    cg_ab, cg_sim = load(run, "AB", "common_gate_amplifier"), load(run, "SIM", "common_gate_amplifier")
    if cg_ab and cg_sim and "m_i1" in cg_ab and "m_i1" in cg_sim:
        mi7["common_gate_amplifier"] = {"value": {f: cg_ab["m_i1"]["fields_fp"][f] == cg_sim["m_i1"]["fields_fp"][f] for f in cg_ab["m_i1"]["fields_fp"]},
                                        "w4_ab": cg_ab["m_i1"]["w4"], "w4_sim": cg_sim["m_i1"]["w4"]}
    table["m_i7"] = mi7
    table["col_4_7_8a"] = {"it_q2": table["m_i4"], "s_p_sign": table["s_p_sign"], "kernel_window_status": table["kernel_window_status"],
                           "multi_root": table["multi_root"], "front_empty": table["front_empty"], "output_structure": table["output_structure"]}
    (dest / "it0_table.json").write_text(json.dumps(table, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")

    def val(col, c, side):
        r = load(run, side, c)
        return None if r is None else r.get(col)
    multi = [c for c in LIB if (val("m_i1_r", c, "SIM") or {}).get("multi_root")]
    fe = [c for c in LIB for s in ("AB", "SIM") if (val("front_empty", c, s) or {}).get("empty")]
    fcu = [[c, s, (val("m_i1_r", c, s) or {}).get("f_component_undeclared"), (val("m_i1_r", c, s) or {}).get("isolated_input")]
           for c in LIB for s in ("SIM",) if (val("m_i1_r", c, s) or {}).get("f_component_undeclared") or (val("m_i1_r", c, s) or {}).get("isolated_input")]
    c2 = [[c, val("drive_pair_nets", c, "AB")] for c in LIB if (val("drive_pair_nets", c, "AB") or {}).get("failing_views")]
    lc_dyn = [[c, s, (val("loop_cut", c, s) or {}).get("input_terminal_nets_calls")] for c in LIB for s in ("AB", "SIM")
              if ((val("loop_cut", c, s) or {}).get("input_terminal_nets_calls") or {}).get("after_stage_a")]
    c3 = [c for c in LIB if (val("feedback_slot", c, "AB") or {}).get("kind") == "None"]
    rem = [[c, s] for c in LIB for s in ("AB", "SIM") if ((val("kernel_window_status", c, s) or {}).get("counts") or {}).get("remeasure_failed")]
    uncl = [[c, s, (val("kernel_window_status", c, s) or {}).get("counts")] for c in LIB for s in ("AB", "SIM")
            if any(k.endswith("unclassified") for k in ((val("kernel_window_status", c, s) or {}).get("counts") or {}))]
    itq2 = [c for c in LIB if (val("m_i4", c, "SIM") or {}).get("has_diff")]
    report = {"S-OS1": {"value": sos1, "report": bool(sos1)},
              "S-OS2": {"tuple_nonempty": sos2t, "empty_tuple": sos2e, "report": bool(sos2t or sos2e)},
              "multi_input_root_library": {"value": multi, "report": bool(multi)},
              "front_empty": {"value": fe, "report": bool(fe)},
              "f_component_or_isolated_input": {"value": fcu, "report": bool(fcu)},
              "C-2_failure": {"value": c2, "report": bool(c2)},
              "10a_dynamic": {"value": lc_dyn, "report": bool(lc_dyn)},
              "C-3_feedback_None": {"value": c3, "report": bool(c3)},
              "O-66_mismatch": {"value": o66_diff, "report": bool(o66_diff)},
              "M-I4_IT-Q2": {"circuits_with_diff": itq2, "verdict": "(다)" if itq2 else "(나)", "report": False},
              "remeasure_failed": {"value": rem, "report": bool(rem)},
              "kernel_status_unclassified": {"value": uncl, "report": bool(uncl)},
              "missing": missing}
    (dest / "report_items.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")
    # V4·래퍼 무해
    v4 = {}
    for c in LIB:
        a1, a2, nw = load(run, "AB", c), load(run, "AB_rep2", c), load(run, "AB_nowrap", c)
        s1, s2 = load(run, "SIM", c), load(run, "SIM_rep2", c)
        def same(x, y):
            if x is None or y is None:
                return None
            for r_ in (x, y):                     # 시간 칸(T 부류)은 결정성 비교에서 뺀다 -- nfr4 T_NAMES 와 같은 이름
                ((r_.get("m_i3") or {}).get("perf") or {}).pop("eval_time_median_s", None)
            cols = [k for k in x if k not in ("wall_s", "tag", "side", "wrapped", "repo", "reeval") and isinstance(x.get(k), (dict, list))]
            return all(json.dumps(x.get(k), sort_keys=True) == json.dumps(y.get(k), sort_keys=True) for k in cols if k != "m_i2" or True)
        fp = lambda r: None if r is None or "m_i3" not in r else r["m_i3"]["front_fp"]
        v4[c] = {"ab_rep_equal": same(a1, a2), "sim_rep_equal": same(s1, s2), "wrap_front_fp_equal": (None if fp(nw) is None else fp(a1) == fp(nw)),
                 "front_fp": {"AB": fp(a1), "AB_rep2": fp(a2), "AB_nowrap": fp(nw), "SIM": fp(s1), "SIM_rep2": fp(s2)}}
    (dest / "checks_raw.json").write_text(json.dumps(v4, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")
    rn = []
    for c in LIB:
        for s in ("AB", "SIM"):
            r = load(run, s, c) or {}
            for col, item, get in (("M-I6", "cycles", lambda r: (r.get("m_i6") or {}).get("cycles")),
                                   ("M-I6", "dependent", lambda r: (r.get("m_i6") or {}).get("dependent")),
                                   ("M-I3", "n_front", lambda r: (r.get("m_i3") or {}).get("n_front")),
                                   ("M-I1-r", "n_input_w4_roots", lambda r: (r.get("m_i1_r") or {}).get("n_input_w4_roots")),
                                   ("KW", "n_evals", lambda r: (r.get("kernel_window_status") or {}).get("n_evals"))):
                rn.append({"name": "%s/%s/%s/%s" % (col, c, s, item), "value": get(r),
                           "command": CMD.replace("<회로>", c).replace("<AB|SIM>", s)})
    (dest / "reproduced_numbers.json").write_text(json.dumps(rn, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v.get("report") for k, v in report.items() if isinstance(v, dict)}, ensure_ascii=False))
    print("missing", len(missing))


if __name__ == "__main__":
    main()
