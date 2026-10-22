"""IT-2b 감사 비교: out/run/{BASE,PREFIX,HEAD,HEAD_rep2}/<회로>.json -> 변화표·결정성·G-10·(9) 표·분류표 대조.
usage: python -I compare_it2b.py <run dir> <table md (de1_output_structure_13.md)> <o103 analyst jsonl> <out json>
"""
import json
import sys
from collections import Counter
from pathlib import Path

RUN = Path(sys.argv[1])
LIB = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
HELD = ["cnr_ota", "erfc_ota", "r2r_opamp", "rfc_ota"]
# 승인된 표 §2 '새 분류'(41-57행) -- 감사가 표에서 손으로 옮긴 값(KVL/HZ), 정지 3출력은 §0 사유
TABLE = {("common_gate_amplifier", "vout"): "HZ", ("current_reuse_telescopic_ota", "Vom"): "KVL", ("current_reuse_telescopic_ota", "Vop"): "KVL",
         ("folded_cascode", "out"): "HZ", ("ngcc_3stage_ff", "Vout"): "HZ", ("nmcnr_amplifier", "Vout"): "KVL",
         ("pushpull_follower_buffer", "vout"): "KVL", ("sf_pushpull_output_opamp", "vout"): "HZ", ("two_stage_ota", "OUT"): "HZ",
         ("two_stage_ota_sf", "vout"): "HZ", ("cnr_ota", "VOP"): "KVL", ("cnr_ota", "VON"): "KVL", ("erfc_ota", "out"): "HZ",
         ("r2r_opamp", "Vo"): "KVL", ("rfc_ota", "out"): "HZ"}
TABLE_STOP = {"cnr_ota": ("dc_resistor_cycle", ["VCR", "VDD_1V8"], ["x40"]), "erfc_ota": ("mos_zero_current_structural", None, ["M19", "M20", "M21"])}
# 표 §1 선언(W3 없음, 입력 DC 선언 = pushpull·sf_pushpull·erfc·rfc)
TABLE_DECL_DC = {"pushpull_follower_buffer", "sf_pushpull_output_opamp", "erfc_ota", "rfc_ota"}
MAP = {"high_impedance": "HZ", "kvl_fixed": "KVL"}


def load(side, c):
    p = RUN / side / (c + ".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def fx(h):
    return None if h is None or not isinstance(h, str) or not h.startswith(("0x", "-0x")) else float.fromhex(h)


def root_set(d):
    return {r[0] for r in d.get("w4", {}).get("roots", []) if r[2]}


def os_check():
    rows, mism = [], 0
    for c in LIB + HELD:
        d = load("HEAD", c)
        if d is None:
            rows.append({"circuit": c, "missing": True, "match": False, "decl_same_as_table_s1": False})
            mism += 1
            continue
        o = d["os"]
        st = o.get("stop")
        decl_ok = (o.get("w3") == []) and (o.get("input_dc_declared") == (c in TABLE_DECL_DC))
        for out in o["outputs"]:
            exp = TABLE.get((c, out))
            if c in TABLE_STOP:
                rb, nets, devs = TABLE_STOP[c]
                det = dict(st.get("detail") or []) if st else {}
                got = (det.get("rule_branch"), det.get("nets"), st.get("devices") if st else None)
                ok = got[0] == rb and (nets is None or got[1] == nets) and got[2] == devs
                rows.append({"circuit": c, "output": out, "table": exp, "kind": "stop", "engine_stop": got, "table_stop": [rb, nets, devs], "match": ok,
                             "decl_same_as_table_s1": decl_ok})
            else:
                eng = (o.get("engine") or {}).get(out)
                ok = MAP.get(eng) == exp and not (st and st.get("exc"))
                rows.append({"circuit": c, "output": out, "table": exp, "engine": eng, "match": ok, "out_in_fprime": out in o.get("out_in_fprime", []),
                             "decl_same_as_table_s1": decl_ok})
            mism += 0 if rows[-1]["match"] else 1
    return {"rows": rows, "mismatch": mism, "n_outputs": len(rows),
            "out_in_fprime_total": sum(len(load("HEAD", c)["os"].get("out_in_fprime", [])) for c in LIB + HELD if load("HEAD", c)),
            "decl_changed_vs_table": [r["circuit"] for r in rows if not r["decl_same_as_table_s1"]]}


def strip(d):
    d = dict(d)
    for k in ("wall_s", "repo", "side"):
        d.pop(k, None)
    fr = dict(d.get("front", {}))
    fr["perf"] = {k: v for k, v in fr.get("perf", {}).items() if not (k.endswith("_s") or k.startswith("t_") or "time" in k)}
    d["front"] = fr
    return d


def determinism(c):
    a, b = load("HEAD", c), load("HEAD_rep2", c)
    if a is None or b is None:
        return {"missing": True}
    sa, sb = strip(a), strip(b)
    diff = sorted(k for k in set(sa) | set(sb) if json.dumps(sa.get(k), sort_keys=True) != json.dumps(sb.get(k), sort_keys=True))
    return {"equal": not diff, "diff_columns": diff}


def g10(d):
    rows = d["block_counters"]["rows"]
    rec = sum(r[7] for r in rows)
    wp = [r for r in rows if r[0] == "dc_writer_plan"]
    return {"recomputes_same_input": rec, "dc_writer_plan": wp}


def win_map(w):
    return {r[0]: r[1:] for r in (w or [])} if isinstance(w, list) else {}


def compare_evals(A, B, roots, inputs):
    """같은 θ(theta_hex) 평가 행끼리(나온 순서로 짝) 창 비교."""
    ia = {}
    for e in A["evals"]:
        ia.setdefault(tuple(e["theta_hex"]), []).append(e)
    used = Counter()
    out = Counter()
    tol_rows = []
    for e in B["evals"]:
        k = tuple(e["theta_hex"])
        lst = ia.get(k, [])
        if used[k] >= len(lst):
            out["unmatched_head"] += 1
            continue
        ea = lst[used[k]]
        used[k] += 1
        out["matched"] += 1
        if ea["status"] != e["status"]:
            out["status_diff"] += 1
        wa, wb = win_map(ea["windows"]), win_map(e["windows"])
        for n in set(wa) | set(wb):
            if n not in wa:
                out["new_entry_" + ("input_port" if n in inputs else "other")] += 1
                continue
            if n not in wb:
                out["dropped_entry"] += 1
                continue
            if wa[n][0:2] != wb[n][0:2]:
                out["lohi_diff_" + ("root_input" if n in roots else ("root_other" if wb[n][3] is None else "input_port"))] += 1
            if wa[n][3:5] != wb[n][3:5] and wa[n][3] != "<no field>":
                if wa[n][3] != wb[n][3]:
                    out["status_diff_window"] += 1
                if wa[n][4] != wb[n][4]:
                    out["tol_v_diff"] += 1
                    tol_rows.append([n, wa[n][4], wb[n][4]])
        if ea.get("input_dc_v") != e.get("input_dc_v"):
            out["input_dc_v_diff"] += 1
    out["base_only_evals"] = sum(len(v) for v in ia.values()) - sum(used.values())
    return dict(out), tol_rows[:20]


def first_div(A, B):
    ta, tb = [tuple(e["theta_hex"]) for e in A["evals"]], [tuple(e["theta_hex"]) for e in B["evals"]]
    for i, (x, y) in enumerate(zip(ta, tb)):
        if x != y:
            return i
    return None if len(ta) == len(tb) else min(len(ta), len(tb))


def kernel_9(P, H):
    """(9): PREFIX 대 HEAD 커널 기록(같은 θ 지문, 나온 순서 짝): 측정 회차·마지막 창·status·tol."""
    ip = {}
    for k in P["kernel"]:
        ip.setdefault(k["theta_fp"], []).append(k)
    used = Counter()
    out = Counter()
    ex = []
    for k in H["kernel"]:
        lst = ip.get(k["theta_fp"], [])
        if used[k["theta_fp"]] >= len(lst):
            out["unmatched"] += 1
            continue
        p = lst[used[k["theta_fp"]]]
        used[k["theta_fp"]] += 1
        if not k["roots"]:
            out["no_root"] += 1
            continue
        out["matched_with_root"] += 1
        d = []
        if p["n_measure"] != k["n_measure"]:
            out["rounds_diff"] += 1; d.append("rounds")
        if p.get("window") != k.get("window"):
            out["window_diff"] += 1; d.append("window")
        if p.get("status") != k.get("status"):
            out["status_diff"] += 1; d.append("status")
        if p.get("tol") != k.get("tol"):
            out["tol_diff"] += 1; d.append("tol")
        if d and len(ex) < 8:
            ex.append({"theta_fp": k["theta_fp"], "diff": d, "prefix": {x: p.get(x) for x in ("n_measure", "status", "tol", "window")},
                       "head": {x: k.get(x) for x in ("n_measure", "status", "tol", "window")}})
    st = Counter(k.get("status") for k in H["kernel"] if k["roots"])
    sp = Counter(k.get("status") for k in P["kernel"] if k["roots"])
    rounds_h = Counter(k["n_measure"] for k in H["kernel"] if k["roots"])
    rounds_p = Counter(k["n_measure"] for k in P["kernel"] if k["roots"])
    return {"pairs": dict(out), "status_head": dict(st), "status_prefix": dict(sp), "measures_head": dict(rounds_h), "measures_prefix": dict(rounds_p),
            "examples": ex}


def steps_cmp(A, B):
    sa, sb = A["fd_steps"], B["fd_steps"]
    n = min(len(sa), len(sb))
    diff = sum(1 for i in range(n) if sa[i] != sb[i])
    return {"n_base": len(sa), "n_head": len(sb), "compared": n, "diff": diff}


def seal_sum(d):
    s = d["seal"]
    return {k: s[k] for k in s if k != "rows"}


def probes_sum(d):
    pr = d["probes"]
    rej = [p for p in pr if not p.get("ok") and p.get("item") == 7]
    sl = [abs(fx(p.get("slack_v"))) for p in rej if fx(p.get("slack_v")) is not None]
    return {"n": len(pr), "sealed": sum(1 for p in pr if p.get("sealed")), "rejected_item7": len(rej),
            "rejected_other": sum(1 for p in pr if not p.get("ok") and p.get("item") != 7), "max_abs_slack_v": max(sl) if sl else None}


def main():
    res = {"os": os_check(), "circuits": {}}
    o103 = {}
    for line in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("kind") == "search":
            o103[(r["side"], r["circuit"])] = {k: r[k] for k in ("n_calls", "y_exact_0", "y_exact_1", "y_near_end_1e-6", "fail_item7", "fail_item7_at_end")}
    for c in LIB:
        B, P, H = load("BASE", c), load("PREFIX", c), load("HEAD", c)
        if H is None or "evals" not in H or B is None or P is None:
            res["circuits"][c] = {"missing": True}
            continue
        roots = root_set(H)
        inputs = set(H["os"]["inputs"])
        cb = {"roots_input": sorted(roots), "input_dc_declared": H["os"]["input_dc_declared"]}
        for lab, A in (("base_vs_head", B), ("prefix_vs_head", P)):
            if A is None or "evals" not in A:
                cb[lab] = "missing"
                continue
            ev, tolrows = compare_evals(A, H, roots, inputs)
            cb[lab] = {"front_fp_equal": A["front"]["front_fp"] == H["front"]["front_fp"], "n_front": [A["front"]["n_front"], H["front"]["n_front"]],
                       "n_pending": [A["front"]["n_pending"], H["front"]["n_pending"]], "n_unmeasured": [A["front"]["n_unmeasured"], H["front"]["n_unmeasured"]],
                       "n_evals": [len(A["evals"]), len(H["evals"])], "n_kernel": [len(A["kernel"]), len(H["kernel"])],
                       "eval_status": [dict(Counter(e["status"] for e in A["evals"])), dict(Counter(e["status"] for e in H["evals"]))],
                       "first_theta_divergence": first_div(A, H), "evals_matched": ev, "tol_v_diff_examples": tolrows,
                       "seal": [seal_sum(A), seal_sum(H)], "probes": [probes_sum(A), probes_sum(H)], "fd_steps": steps_cmp(A, H),
                       "g10": [g10(A), g10(H)]}
        cb["nine"] = kernel_9(P, H) if P is not None and "kernel" in P else "missing"
        cb["determinism"] = determinism(c)
        cb["o103_analyst"] = {"head_85847b49": o103.get(("head", c)), "base_53d50aea": o103.get(("base", c))}
        res["circuits"][c] = cb
    Path(sys.argv[4]).write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print("OS mismatch", res["os"]["mismatch"], "of", res["os"]["n_outputs"], "out_in_fprime", res["os"]["out_in_fprime_total"])
    for c, cb in res["circuits"].items():
        if cb.get("missing"):
            print(c, "missing")
            continue
        bh = cb["base_vs_head"]
        ph = cb["prefix_vs_head"]
        print(c, "| det", cb["determinism"].get("equal"), "| BH front_eq", bh["front_fp_equal"], bh["n_front"], "div", bh["first_theta_divergence"],
              "| ev", bh["evals_matched"], "| G10", bh["g10"][1]["recomputes_same_input"], "| PH front_eq", ph["front_fp_equal"],
              "div", ph["first_theta_divergence"], "| nine", cb["nine"]["pairs"] if isinstance(cb["nine"], dict) else cb["nine"])


if __name__ == "__main__":
    main()
