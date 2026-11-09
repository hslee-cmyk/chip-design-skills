"""검증 3: LUT의 R(W) 비단조(긴 L에서 W 클수록 R 증가)를 ngspice로 교차 확인. pfet tt, bulk = source, VDS = 0, source 0.7 V."""
import pathlib, re, subprocess
HERE = pathlib.Path(__file__).resolve().parent
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] + [
    f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"'
    for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
cases = [(w, l, 0.375) for l in (0.15, 0.5, 1.0) for w in (0.42, 0.55, 0.84, 1.0, 3.0, 7.0)]
lines = ["* zg1w", LIB, ".option gmin=1e-18"]; prints = []
for i, (w, l, vsg) in enumerate(cases):
    lines += [f"vs{i} s{i} 0 0.7", f"vg{i} g{i} 0 {0.7 - vsg:.4f}", f"xa{i} s{i} g{i} s{i} s{i} sky130_fd_pr__pfet_01v8 w={w}u l={l}u"]
    d = f"@m.xa{i}.msky130_fd_pr__pfet_01v8"; prints.append(f"print {d}[vth] {d}[gds]")
lines += [".control", "op"] + prints + [".endc", ".end"]
deck = HERE / "zg1_w_ngspice.cir"; deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
out = subprocess.run([NG, "-b", str(deck)], capture_output=True, text=True, cwd=HERE)
v = {}
for line in out.stdout.splitlines():
    m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)\s*$", line)
    if m: v[m.group(1).lower()] = float(m.group(2))
rows = ["| W um | L um | VSG V | vth V | gds S | R Ohm |", "|---|---|---|---|---|---|"]
for i, (w, l, vsg) in enumerate(cases):
    d = f"@m.xa{i}.msky130_fd_pr__pfet_01v8"; vth = v.get(f"{d}[vth]"); g = v.get(f"{d}[gds]")
    rows.append(f"| {w} | {l} | {vsg} | {vth} | {g:.4e} | {1/g:.4e} |" if g else f"| {w} | {l} | {vsg} | {vth} | {g} | - |")
(HERE / "zg1_w_ngspice.txt").write_text("\n".join(rows) + "\n\nstderr tail:\n" + out.stderr[-800:] + "\n", encoding="utf-8")
print("\n".join(rows)); print(out.stderr[-400:])
