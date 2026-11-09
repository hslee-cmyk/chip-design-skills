"""S1. sky130 에서 erfc_ota 전회로 바이어스 재현 -- VDD·VCP·VCN·VCM 격자에서 .op, M19~M21 밖 전 MOS 포화 여유 최소값.
결과: s1_bias_scan.txt (케이스마다 append)."""
import itertools, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from erfc_net import netlist, run, dev, ALL, PSEUDO

HERE = pathlib.Path(__file__).parent
OUT = HERE / "s1_bias_scan.txt"
OUT.write_text("# S1 bias scan (buf, mode=mos, CBAT 1 pF)\n| VDD | VCP | VCN | VCM | out | I(vdd) uA | min margin V | worst dev | linear devs |\n|---|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
devs = [d for d in ALL if d not in PSEUDO]
grid = []
for vdd in (1.8, 2.4, 3.0):
    for vcm_off in (0.9, 1.2, 1.5):          # VCM = VDD - vcm_off
        for vcp in (0.5, 0.7, 0.9, 1.1):
            for vcn in (0.7, 0.9, 1.1):
                grid.append((vdd, vcp, vcn, round(vdd - vcm_off, 3)))
best = []
for vdd, vcp, vcn, vcm in grid:
    if vcm <= 0.2:
        continue
    prints = ["print v(out) i(vvdd)"] + [f"print {dev(d)}[vds] {dev(d)}[vdsat] {dev(d)}[id]" for d in devs]
    deck = netlist(vdd, vcp, vcn, vcm, extra="\n".join([".control", "op"] + prints + [".endc", ".end"]))
    v, _ = run(HERE / "s1_tmp.cir", deck)
    if "v(out)" not in v:
        continue
    margins = {}
    for d in devs:
        vds, vdsat = v.get(f"{dev(d)}[vds]"), v.get(f"{dev(d)}[vdsat]")
        if vds is None:
            continue
        margins[d] = abs(vds) - abs(vdsat)
    worst = min(margins, key=margins.get)
    lin = [d for d, m in margins.items() if m < 0]
    row = (vdd, vcp, vcn, vcm, v["v(out)"], -v["i(vvdd)"] * 1e6, margins[worst], worst, lin)
    best.append(row)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"| {vdd} | {vcp} | {vcn} | {vcm} | {v['v(out)']:.4f} | {row[5]:.3f} | {margins[worst]:+.4f} | {worst} | {','.join(lin)} |\n")
best.sort(key=lambda r: -r[6])
with OUT.open("a", encoding="utf-8") as f:
    f.write("\n## top 8 by min margin\n")
    for r in best[:8]:
        f.write(f"{r}\n")
