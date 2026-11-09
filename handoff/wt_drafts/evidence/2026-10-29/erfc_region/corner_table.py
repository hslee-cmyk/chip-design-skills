"""f_HP = 1/(2 pi R C) 표 -- R = 1/gds(VDS = 0, 채널만) from a_rows_g1e-18.json, L = 1 um(Table 1). 결과 corner_table.txt."""
import json, math, pathlib

HERE = pathlib.Path(__file__).resolve().parent
rows = json.loads((HERE / "a_rows_g1e-18.json").read_text(encoding="utf-8"))
GBW = 1.37e6                                   # 원문 Table 2 TT
out = ["| source V | bulk | VSG V | R_ch Ohm | f_HP @0.1 pF | f_HP @1 pF | f_HP @10 pF | f_HP(1 pF)/GBW |", "|---|---|---|---|---|---|---|---|"]
for vs, bulk, L, vsg, vth, gds, r, rd in rows:
    if L != 1.0 or vsg not in (0.20, 0.30, 0.40, 0.45, 0.50):
        continue
    f = [1 / (2 * math.pi * r * c) for c in (1e-13, 1e-12, 1e-11)]
    out.append(f"| {vs} | {bulk} | {vsg:.2f} | {r:.2e} | {f[0]:.2e} Hz | {f[1]:.2e} Hz | {f[2]:.2e} Hz | {f[1] / GBW:.1e} |")
(HERE / "corner_table.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
