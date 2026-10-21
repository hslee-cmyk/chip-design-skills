"""IT-2a 9회로 변화표: BASE(엔진 base d3bdbd39) 대 HEAD(병합본), HEAD 대 HEAD_rep2(결정성), 그리고 IT-0 기록·IT-1 감사 기록 대비 원인 칸.

usage: python -I compare_it2a.py <run_dir> <it0_raw_dir> <it1_raw_dir> <out_json>

비교 = 회로 기록 JSON 전체의 재귀 경로 diff. 제외 칸(감사 소유 목록):
  * 시간 칸: wall_s, tag, repo, side, m_i3.perf.eval_time_median_s, m_i2.t
  * 블록 계수 칸: block_counters (따로 분석 -- 허용 변화 = keep 밖 블록 outcome reuse -> graft, calls·computes 불변)
허용 변화 규칙(card IT-2a '무동작 판정 입력'): 블록마다 calls·computes·recomputes_same_input 불변, reuses+grafts 불변,
  커널 4·봉인 항목 8 = 행 그대로, 바뀌어도 되는 행 = keep 밖 블록(ss·metric 블록, dc_seal_report)의 reuse -> graft.
"""
import json
import sys
from pathlib import Path

LIB = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
       "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]
KERNEL4 = {"dc_currents", "dc_lengths", "dc_columns", "dc_widths"}
SEAL8 = {"dc_tolerances", "dc_seal_node_conflict", "dc_seal_vgs_match", "dc_seal_kcl", "dc_seal_bulk_reverse",
         "dc_seal_saturation", "dc_seal_kvl_branch", "dc_seal_conduction"}
TIME_PATHS = {("wall_s",), ("tag",), ("repo",), ("side",), ("m_i3", "perf", "eval_time_median_s"), ("m_i2", "t")}


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def diff(a, b, path=()):
    if path in TIME_PATHS or path[:1] == ("block_counters",):
        return []
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                if path + (k,) not in TIME_PATHS and (path + (k,))[:1] != ("block_counters",):
                    out.append(("/".join(map(str, path + (k,))), "missing_in_" + ("a" if k not in a else "b")))
                continue
            out += diff(a[k], b[k], path + (k,))
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [("/".join(map(str, path)), "len %d != %d" % (len(a), len(b)))]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, path + (i,))
        return out
    return [] if a == b else [("/".join(map(str, path)), "%r != %r" % (str(a)[:120], str(b)[:120]))]


def rows(rec):
    bc = (rec or {}).get("block_counters") or {}
    return {(r[0], r[1]): dict(zip(("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input"), r[2:]))
            for r in bc.get("rows", [])}


def counter_changes(rb, rh):
    out = []
    for k in sorted(set(rb) | set(rh)):
        x, y = rb.get(k), rh.get(k)
        if x == y:
            continue
        blk = k[0]
        z = {f: 0 for f in ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")}
        x0, y0 = x or z, y or z
        same_work = all(x0[f] == y0[f] for f in ("calls", "computes", "recomputes_same_input", "replays")) \
            and x0["reuses"] + x0["grafts"] == y0["reuses"] + y0["grafts"]
        moved = x0["reuses"] - y0["reuses"]
        if blk in KERNEL4 or blk in SEAL8:
            cause = "UNEXPLAINED (커널 4·봉인 항목 8 행은 그대로여야 함)"
        elif same_work and moved > 0 and blk == "dc_seal_report":
            cause = "허용: dc_seal_report keep 밖 -> reuse->graft (O-94 (2))"
        elif same_work and moved > 0:
            cause = "허용: keep 밖 블록(ss·metric) reuse->graft (design 41 4.7-3c, 756 (i))"
        else:
            cause = "UNEXPLAINED"
        out.append({"block": blk, "part": k[1], "base": x, "head": y, "reuse_to_graft": moved, "cause": cause})
    return out


def main():
    run, it0, it1, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    res = {}
    for c in LIB:
        b, h, h2 = (load(run / "BASE" / (c + ".json")), load(run / "HEAD" / (c + ".json")), load(run / "HEAD_rep2" / (c + ".json")))
        a0, i1 = load(it0 / "AB" / (c + ".json")), load(it1 / "IT1" / (c + ".json"))
        rb, rh, rh2 = rows(b), rows(h), rows(h2)
        row = {
            "present": [b is not None, h is not None, h2 is not None],
            "base_vs_head_diffs": diff(b, h) if b and h else ["record missing"],
            "head_vs_rep2_diffs": diff(h, h2) if h and h2 else ["record missing"],
            "head_vs_rep2_counters_equal": rh == rh2,
            "counter_changes": counter_changes(rb, rh),
            "head_recomputes_same_input": sum(r["recomputes_same_input"] for r in rh.values()),
            "base_recomputes_same_input": sum(r["recomputes_same_input"] for r in rb.values()),
            "head_totals": (h or {}).get("block_counters", {}).get("totals"),
            "base_totals": (b or {}).get("block_counters", {}).get("totals"),
            "base_vs_it1_audit_diffs": diff(i1, b) if i1 and b else ["record missing"],
            "head_vs_it0_AB_n_diffs": len(diff(a0, h)) if a0 and h else None,
            "base_vs_it0_AB_n_diffs": len(diff(a0, b)) if a0 and b else None,
            "it0_diff_paths_head_minus_base": sorted(set(p for p, _ in diff(a0, h)) - set(p for p, _ in diff(a0, b))) if a0 and h and b else None,
        }
        row["n_unexplained"] = len(row["base_vs_head_diffs"]) + sum(1 for x in row["counter_changes"] if x["cause"].startswith("UNEXPLAINED")) \
            + len(row["head_vs_rep2_diffs"]) + (0 if row["head_vs_rep2_counters_equal"] else 1)
        res[c] = row
    res_all = {"circuits": res, "total_unexplained": sum(r["n_unexplained"] for r in res.values()),
               "g10_head_recomputes_same_input_total": sum(r["head_recomputes_same_input"] for r in res.values())}
    out.write_text(json.dumps(res_all, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    for c, r in res.items():
        print(c, "present", r["present"], "base/head diffs", len(r["base_vs_head_diffs"]), "rep2 diffs", len(r["head_vs_rep2_diffs"]),
              "rep2 counters eq", r["head_vs_rep2_counters_equal"], "counter changes", len(r["counter_changes"]),
              "G10 head", r["head_recomputes_same_input"], "base-vs-IT1audit", len(r["base_vs_it1_audit_diffs"]), "unexpl", r["n_unexplained"])
    print("TOTAL_UNEXPLAINED", res_all["total_unexplained"], "G10", res_all["g10_head_recomputes_same_input_total"])


if __name__ == "__main__":
    main()
