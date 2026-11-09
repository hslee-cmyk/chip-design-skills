"""B33 착수 키트: run_headline.sh 출력 요약(표 숫자만 뽑는다 -- 해석은 b33_briefs.md).
    python -B summarize.py <출력 디렉터리> [<비교할 옛 m1b.jsonl>]
요약을 <출력 디렉터리>/summary.json에 쓰고 사람이 읽을 줄을 stdout에 낸다."""
import json
import os
import sys

OUT = sys.argv[1]
OLD = sys.argv[2] if len(sys.argv) > 2 else None


def rows(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def m1_summary(p):
    s = {}
    for o in rows(p):
        if o["what"] == "setup":
            s["setup"] = {k: o[k] for k in ("files", "src_defs", "test_nodes", "head_tool_build_graph_s")}
        elif o["what"] == "variant":
            v = o["variant"]
            s[v] = {k: o.get(k) for k in (
                "unreached_union", "unreached_union+R3", "unreached_before_phase3+R3", "unreached_after_phase3+R3",
                "unreached_before_phase3", "unreached_after_phase3", "nonsource_reached_union",
                "nonsource_reached_union+R3", "exempt_reached_union+R3", "v3_pairs", "v3_inventory0_n", "v3_median",
                "v3_sample", "build_graph_s", "binding_nodes")}
            s[v]["unreached_list_union+R3"] = o.get("unreached_list_union+R3")
            s[v]["v3_inventory0"] = o.get("v3_inventory0")
        elif o["what"] == "monotone":
            s["monotone_" + o["variant"]] = {k: o[k] for k in ("missing_old_edges", "missing_all_dunder_targets",
                                                              "missing_sample", "src_defs_lost_reach_noR3",
                                                              "src_defs_lost_reach_R3")}
        elif o["what"] in ("diff_unreached", "diff_inventory0"):
            s[o["what"]] = {k: v for k, v in o.items() if k != "what"}
    return s


new = m1_summary(os.path.join(OUT, "m1.jsonl"))
res = {"m1": new}
b, f = new["base"], new["fixed"]
print("setup", new["setup"])
print("unreached union+R3 base %s -> fixed %s ; union(noR3) base %s ; two sets base %s/%s fixed %s/%s" % (
    b["unreached_union+R3"], f["unreached_union+R3"], b["unreached_union"],
    b["unreached_before_phase3+R3"], b["unreached_after_phase3+R3"],
    f["unreached_before_phase3+R3"], f["unreached_after_phase3+R3"]))
print("nonsource reached (noR3) base %s fixed %s ; fixed+R3 %s ; exempt reached fixed+R3 %s" % (
    b["nonsource_reached_union"], f["nonsource_reached_union"], f["nonsource_reached_union+R3"],
    f["exempt_reached_union+R3"]))
print("V3 pairs base %s -> fixed %s (x%.3f) ; inventory0 %s -> %s ; median %s -> %s ; sample base %s fixed %s" % (
    b["v3_pairs"], f["v3_pairs"], f["v3_pairs"] / b["v3_pairs"], b["v3_inventory0_n"], f["v3_inventory0_n"],
    b["v3_median"], f["v3_median"], b["v3_sample"], f["v3_sample"]))
inv_new_zero = sorted(set(f["v3_inventory0"]) - set(b["v3_inventory0"]))
print("inventory0 in fixed but not in base (regression):", inv_new_zero)
res["inventory0_regression"] = inv_new_zero
mf = new["monotone_fixed"]
print("monotone fixed: missing old edges %s all dunder %s lost reach noR3 %s R3 %s" % (
    mf["missing_old_edges"], mf["missing_all_dunder_targets"],
    {k: len(v) for k, v in mf["src_defs_lost_reach_noR3"].items()}, {k: len(v) for k, v in mf["src_defs_lost_reach_R3"].items()}))
if OLD:
    old = m1_summary(OLD)
    ob, of = old["base"], old["fixed"]
    ub_new, ub_old = set(b["unreached_list_union+R3"]), set(ob["unreached_list_union+R3"])
    uf_new, uf_old = set(f["unreached_list_union+R3"]), set(of["unreached_list_union+R3"])
    d = {"base_new_minus_old": sorted(ub_new - ub_old), "base_old_minus_new": sorted(ub_old - ub_new),
         "fixed_new_minus_old": sorted(uf_new - uf_old), "fixed_old_minus_new": sorted(uf_old - uf_new),
         "old_setup": old["setup"], "old_base_pairs": ob["v3_pairs"], "old_fixed_pairs": of["v3_pairs"]}
    res["vs_old"] = d
    print("vs old:", json.dumps(d, ensure_ascii=False))
m4p = os.path.join(OUT, "m4.jsonl")
if os.path.exists(m4p):
    r4 = rows(m4p)
    scan = [o for o in r4 if o["what"] == "scan"]
    pairs = [o for o in r4 if o["what"] == "pair"]
    bad = [o for o in pairs if "error" in o or not o.get("same_fixed")]
    nd = [(o["records"], len(o["base"]["new_defs"] or [])) for o in pairs if "base" in o and o["base"]["new_defs"]]
    verdicts = sorted({o["base"]["verdict"] for o in pairs if "base" in o})
    cfg = sorted({o.get("config_from_head") for o in pairs})
    res["m4"] = {"scan": scan[-1] if scan else None, "pairs": len(pairs), "not_same_or_error": bad,
                 "base_verdicts": verdicts, "config_from_head": cfg, "pairs_with_new_defs": nd,
                 "records": sorted({r for o in pairs for r in o["records"]})}
    print("m4 scan", scan[-1] if scan else None, "pairs", len(pairs), "bad", len(bad), "verdicts", verdicts, "cfg_from_head", cfg)
    print("m4 new_defs pairs", nd)
m5p = os.path.join(OUT, "m5.json")
if os.path.exists(m5p):
    res["m5"] = json.load(open(m5p, encoding="utf-8"))
json.dump(res, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
