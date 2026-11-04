import json, statistics as st
rows = [json.loads(l) for l in open("C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work2/mode_value_diffs.jsonl", encoding="utf-8")]
print("cells", len(rows), "bins_as_measured", sum(r["bins_as_measured"] for r in rows), "rc", sum(r["default"]["rc"] for r in rows) + sum(r["hsa"]["rc"] for r in rows))
Q = ("id", "gm", "gds", "vth", "CGG", "CGD", "CGS", "CGB", "CDD", "CSS")
out = {}
for k in ("nfet_01v8", "pfet_01v8"):
    for ax in ("L", "W"):
        s = [r for r in rows if r["kind"] == k and ax in r["axes"]]
        for q in Q:
            v = [r["rel"][q] for r in s if r["rel"][q] is not None]
            none = sum(r["rel"][q] is None for r in s)
            if not v:
                out[f"{k}|{ax}|{q}"] = {"n": 0, "null": none}; continue
            mx = max(s, key=lambda r: r["rel"][q] if r["rel"][q] is not None else -1)
            out[f"{k}|{ax}|{q}"] = {"n": len(v), "null": none, "median": st.median(v), "max": max(v), "at": (mx["l_m"], mx["w_m"])}
for k, v in out.items():
    if v["n"]:
        print(k, v["n"], "null", v["null"], f'median {v["median"]:.2e} max {v["max"]:.2e} at L={v["at"][0]:.3g} W={v["at"][1]:.3g}')
    else:
        print(k, v)
json.dump(out, open("C:/Users/HSLEE/AppData/Local/Temp/la1s_op7a_audit/work2/a2b_summary.json", "w"), indent=1)
# 절대값 예: 최대 칸
for q in ("id", "gm", "gds", "CGG", "CDD", "CGD"):
    r = max((x for x in rows if x["rel"][q] is not None), key=lambda x: x["rel"][q])
    print(q, "worst", r["kind"], r["l_m"], r["w_m"], r["axes"], r["bin_d"][-10:], r["bin_h"][-10:], r["default"][q], r["hsa"][q], f'{r["rel"][q]:.2e}')
print("LUT r2 CGG sanity:", rows[0]["default"]["CGG"], rows[0]["default"]["id"], rows[0]["default"]["gm"], rows[0]["default"]["vth"])
