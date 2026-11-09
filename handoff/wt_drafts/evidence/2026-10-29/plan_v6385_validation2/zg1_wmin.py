"""Q-ZG1 (가) 실측: sky130 pfet_01v8 tt, bulk = source(DR-1 조건), VDS = 0 점 gds·gm·id·cgg 등.
기하: (가) 권고 W_min·L_min = 0.42 um / 0.15 um(PDK 최소 -- 아래 결과의 model bin 경고로 확인), 대조 Table 1 3 um / 1 um.
VSG 0.20~0.80 V, source 0.7 V. 결과 zg1_wmin.txt 에 append. f_HP = 1/(2 pi R C), C = 0.1/1/10 pF, GBW 대조 1.37 MHz(erfc spec)."""
import math, pathlib, re, subprocess

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "zg1_wmin.txt"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] + [
    f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"'
    for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
geoms = [(0.42, 0.15), (3.0, 1.0)]
vsgs = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
vs = 0.7
cases = [(w, l, v) for (w, l) in geoms for v in vsgs]
lines = ["* zg1", LIB, ".option gmin=1e-18"]
prints = []
for i, (w, l, vsg) in enumerate(cases):
    lines += [f"vs{i} s{i} 0 {vs}", f"vg{i} g{i} 0 {vs - vsg:.4f}",
              f"xa{i} s{i} g{i} s{i} s{i} sky130_fd_pr__pfet_01v8 w={w}u l={l}u"]
    dev = f"@m.xa{i}.msky130_fd_pr__pfet_01v8"
    prints.append(f"print {dev}[vth] {dev}[gds] {dev}[gm] {dev}[id] {dev}[cgg]")
lines += [".control", "op"] + prints + [".endc", ".end"]
deck = HERE / "zg1_wmin.cir"
deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
out = subprocess.run([NG, "-b", str(deck)], capture_output=True, text=True, cwd=HERE)
(HERE / "zg1_wmin.cir.log").write_text(out.stdout + "\n--stderr--\n" + out.stderr, encoding="utf-8")
v = {}
for line in out.stdout.splitlines():
    m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)\s*$", line)
    if m:
        v[m.group(1).lower()] = float(m.group(2))
rows = ["| W um | L um | VSG V | vth V | gds S | R=1/gds Ohm | gm S | id A | cgg F | f_HP 0.1pF | 1pF | 10pF | f_HP(0.1pF)/1.37MHz |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for i, (w, l, vsg) in enumerate(cases):
    dev = f"@m.xa{i}.msky130_fd_pr__pfet_01v8"
    vth, gds, gm, idd, cgg = (v.get(f"{dev}[{k}]") for k in ("vth", "gds", "gm", "id", "cgg"))
    if not gds:
        rows.append(f"| {w} | {l} | {vsg} | {vth} | {gds} | -- | {gm} | {idd} | {cgg} | -- | -- | -- | -- |")
        continue
    r = 1 / gds
    f = [1 / (2 * math.pi * r * c) for c in (1e-13, 1e-12, 1e-11)]
    rows.append(f"| {w} | {l} | {vsg:.2f} | {vth:.4f} | {gds:.3e} | {r:.3e} | {gm:.3e} | {idd:.3e} | {cgg:.3e} | "
                f"{f[0]:.3e} | {f[1]:.3e} | {f[2]:.3e} | {f[0] / 1.37e6:.2e} |")
RES.write_text("\n".join(rows) + "\n\nstderr tail:\n" + out.stderr[-1500:] + "\n", encoding="utf-8")
print("\n".join(rows))
