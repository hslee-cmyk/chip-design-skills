"""spice_icmr.jsonl 요약 -- 설계점, 영역 행 창, 기능 기준 후보별 창 끝. 결과는 summary.jsonl에 append + 출력."""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
case = sys.argv[1] if len(sys.argv) > 1 else "base"
rows = [json.loads(l) for l in open(HERE / "spice_icmr.jsonl", encoding="utf-8")]
rows = [r for r in rows if r.get("case") == case]
for r in rows:
    if r["step"] == "tune_R":
        print("R", r["R"])
        print([(h["it"], h["R"], round(h["lo_V"], 3), round(h["hi_V"], 3)) for h in r["hist"][-3:]])
    if r["step"] == "design":
        print("k", r["k_out"], "Cc", r["Cc"], "gm1", r["gm1"])
        print({k: round(v, 4) for k, v in r["nodes"].items() if v is not None})
        for n, d in r["dev"].items():
            print(n, round(d["id"] * 1e6, 3), "uA sat", round(d["sat_margin"], 3), "vgs", round(d["vgs"], 3),
                  "gm/id", round(d["gm"] / abs(d["id"]), 1), "gm", d["gm"])
ic = [r for r in rows if r["step"] == "icmr" and r.get("A_db") is not None]
if not ic:
    sys.exit(0)
ref = min(ic, key=lambda r: abs(r["x"] - 0.9))
A0 = ref["A_db"]
print("ref x", ref["x"], "A0 dB", round(A0, 2))


def window(ok):
    """기준점에서 위·아래로 첫 실패 전까지 연속 구간."""
    xs = sorted(ic, key=lambda r: r["x"])
    i0 = xs.index(ref)
    lo = hi = None
    for r in reversed(xs[:i0 + 1]):
        if ok(r):
            lo = r["x"]
        else:
            break
    for r in xs[i0:]:
        if ok(r):
            hi = r["x"]
        else:
            break
    return lo, hi


res = {"case": case, "A0_db": A0, "x_ref": ref["x"]}
res["region_rows"] = window(lambda r: not r["neg_sat"])
for d in (1.0, 3.0, 6.0):
    res[f"rel_{d}dB"] = window(lambda r, d=d: A0 - r["A_db"] <= d)
res["abs_gain_spec_65dB"] = window(lambda r: r["A_db"] >= 65.0)
for d in (3.0,):
    res[f"region_and_rel_{d}dB"] = window(lambda r, d=d: (not r["neg_sat"]) and A0 - r["A_db"] <= d)
res["region_and_abs65"] = window(lambda r: (not r["neg_sat"]) and r["A_db"] >= 65.0)
print(json.dumps(res, ensure_ascii=False))
with open(HERE / "summary.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(res, ensure_ascii=False) + "\n")
for r in sorted(ic, key=lambda r: r["x"]):
    if round(r["x"] * 100) % 5 == 0 or r["neg_sat"][:1] != []:
        print(r["x"], round(r["A_db"], 2), "tail_I", round(r["i_tail"] * 1e6, 2), "tail_v", round(r["tail_v"], 3), "n1", round(r["n1"], 3),
              "y", round(r["y"], 3), "neg", r["neg_sat"][:4], "worst", (r["worst_sat"][0], round(r["worst_sat"][1], 3)))
