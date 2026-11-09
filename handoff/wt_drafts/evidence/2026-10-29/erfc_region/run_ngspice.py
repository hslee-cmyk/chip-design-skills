"""erfc_ota M19~M21 영역 실측 (sky130 tt, ngspice). 결과는 케이스마다 results.txt 에 append.

A. 단일 pfet 스윕: W = 3 um, L in {0.5, 1(Table 1), 2, 4} um, VSG 0.20~0.50 V, source = 0.7 V(vcn) 또는 1.1 V(vcp),
   bulk = 1.8 V(topology 가정) 또는 source(대안). VDS = 0 점의 vth·gds·gm 과 VSD = 1 mV 점의 직접 R = 1 mV / |ID|.
B. 전체 회로 .op: topology.json 연결 그대로, Table 1 치수(sky130 대용), vin_p = 0.8 V, 단위이득(vin_n = out).
"""
import json, pathlib, re, subprocess

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "results.txt"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] + [f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"' for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])  # LUT 생성기(assets/sky130_lut_sweep.py model_includes)와 같은 include
TOPO = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/erfc_ota.topology.json")


def log(text):
    with RES.open("a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


def run(deck_name, deck):
    p = HERE / deck_name
    p.write_text(deck, encoding="utf-8")
    out = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=HERE)
    (HERE / (deck_name + ".log")).write_text(out.stdout + "\n--stderr--\n" + out.stderr, encoding="utf-8")
    vals = {}
    for line in out.stdout.splitlines():
        m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)\s*$", line)
        if m:
            vals[m.group(1).lower()] = float(m.group(2))
    return vals


def part_a(gmin="1e-12"):
    log(f"\n### A. 단일 pfet (W = 3 um, 접합 기하 0) -- VDS = 0 점, ngspice gmin = {gmin} S (bulk=vdd 행 R_direct 가 gmin x V_DB 인지 본다)")
    Ls = [0.5, 1.0, 2.0, 4.0]
    vsgs = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    cases = []
    for vs in (0.7, 1.1):
        for bulk in ("vdd", "src"):
            for L in Ls:
                for vsg in vsgs:
                    cases.append((vs, bulk, L, vsg))
    lines = ["* pfet sweep", LIB, f".option gmin={gmin}", "vdd vdd 0 1.8"]
    prints = []
    for i, (vs, bulk, L, vsg) in enumerate(cases):
        b = "vdd" if bulk == "vdd" else f"s{i}"
        lines += [f"vs{i} s{i} 0 {vs}", f"vg{i} g{i} 0 {vs - vsg:.4f}",
                  f"xa{i} s{i} g{i} s{i} {b} sky130_fd_pr__pfet_01v8 w=3u l={L}u",       # VDS = 0
                  f"vd{i} d{i} 0 {vs - 0.001:.4f}",
                  f"xb{i} d{i} g{i} s{i} {b} sky130_fd_pr__pfet_01v8 w=3u l={L}u"]       # VSD = 1 mV
        dev = f"@m.xa{i}.msky130_fd_pr__pfet_01v8"
        prints += [f"print {dev}[vth] {dev}[gds] {dev}[gm] {dev}[id]", f"print i(vd{i})"]
    lines += [".control", "op"] + prints + [".endc", ".end"]
    v = run(f"a_sweep_g{gmin}.cir", "\n".join(lines) + "\n")
    log("| source V | bulk | L um | VSG V | vth V | gds S (VDS=0) | R=1/gds Ohm | R_direct (1 mV) Ohm | gm/ID-ish note |")
    log("|---|---|---|---|---|---|---|---|---|")
    rows = []
    for i, (vs, bulk, L, vsg) in enumerate(cases):
        dev = f"@m.xa{i}.msky130_fd_pr__pfet_01v8"
        vth = v.get(f"{dev}[vth]"); gds = v.get(f"{dev}[gds]"); gm = v.get(f"{dev}[gm]")
        idd = v.get(f"i(vd{i})")
        rd = 0.001 / abs(idd) if idd else None
        r = 1 / gds if gds else None
        rows.append((vs, bulk, L, vsg, vth, gds, r, rd))
        log(f"| {vs} | {bulk} | {L} | {vsg:.2f} | {vth if vth is None else round(vth,4)} | "
            f"{gds if gds is None else f'{gds:.3e}'} | {r if r is None else f'{r:.3e}'} | {rd if rd is None else f'{rd:.3e}'} | "
            f"{'VSG<|Vth| (weak inv.)' if vth is not None and vsg < abs(vth) else 'VSG>=|Vth|'} |")
    (HERE / f"a_rows_g{gmin}.json").write_text(json.dumps(rows), encoding="utf-8")


def part_b(gmin="1e-12"):
    log(f"\n### B. 전체 회로 .op (sky130 tt, Table 1 치수, 확산 기하 ad=as=W*0.29um, 단위이득 vin_p = 0.8 V, gmin = {gmin} S)")
    t = json.loads(TOPO.read_text(encoding="utf-8"))
    size = {}
    for names, wl in [(("M1A", "M1B", "M2A", "M2B", "M11", "M12"), (24, 0.6)), (("M13", "M14"), (24, 0.3)),
                      (("M17A", "M18A"), (12, 0.3)), (("M3B", "M4B"), (90, 0.3)), (("M15", "M16"), (1, 20)),
                      (("M5", "M6"), (60, 0.3)), (("M9", "M10"), (48, 0.3)), (("M3A", "M4A"), (18, 0.3)),
                      (("M3C", "M4C", "M17B", "M18B"), (30, 0.3)), (("M19", "M20", "M21"), (3, 1)), (("M7", "M8"), (24, 0.3))]:
        for n in names:
            size[n] = wl
    nm = lambda n: "0" if n == "gnd" else n.lower()
    lines = ["* erfc_ota full op", LIB, f".option gmin={gmin}", "vvdd vdd 0 1.8", "vvcp vcp 0 1.1", "vvcn vcn 0 0.7", "vinp vin_p 0 0.8",
             "einn vin_n 0 out 0 1"]
    for m in t["netlist"]:
        w, l = size[m["name"]]
        model = "sky130_fd_pr__pfet_01v8" if m["kind"] == "pmos" else "sky130_fd_pr__nfet_01v8"
        lines.append(f"x{m['name'].lower()} {nm(m['drain'])} {nm(m['gate'])} {nm(m['source'])} {nm(m['bulk'])} {model} w={w}u l={l}u "
                     f"ad={w * 0.29:.4g}p as={w * 0.29:.4g}p pd={2 * (w + 0.29):.4g}u ps={2 * (w + 0.29):.4g}u")
    for p in t["passive_elements"]:
        a, b = (nm(x) for x in p["terminals"])
        if p["kind"] == "resistor":
            lines.append(f"r{p['name'].lower()} {a} {b} {p['value_ohm']}")
        else:
            lines.append(f"c{p['name'].lower()} {a} {b} {p['value_farad'] or 1e-12}")
    for s in t["ideal_sources"]:
        a, b = (nm(x) for x in s["terminals"])
        lines.append(f"i{s['name'].lower()} {a} {b} {s['value_amp']}")
    prints = ["print v(x) v(y) v(z) v(n_m5g) v(n_m6g) v(n_m8g) v(out) v(n_m7d) v(n_m5s)"]
    for d in ("m19", "m20", "m21", "m3a", "m5", "m7"):
        kind = "pfet" if d in ("m19", "m20", "m21", "m7") else "nfet"
        dev = f"@m.x{d}.msky130_fd_pr__{kind}_01v8"
        prints.append(f"print {dev}[id] {dev}[vgs] {dev}[vds] {dev}[vth] {dev}[gds] {dev}[gm] {dev}[vdsat]")
    lines += [".control", "op"] + prints + [".endc", ".end"]
    v = run(f"b_full_g{gmin}.cir", "\n".join(lines) + "\n")
    for k in sorted(v):
        log(f"   {k} = {v[k]:.6g}")


def part_c():
    """부유 드레인 노드(DC 원소 = 채널 하나 + 그 드레인 접합) 평형 VDS -- 접합 기하를 주고 gmin 을 바꿔 본다."""
    log("\n### C. 부유 드레인 평형 V(d) - V(s) (W=3u L=1u, ad=as=0.87p pd=ps=6.58u, 드레인 = 채널·접합·1 pF 만)")
    log("| 소자 꼴 | source V | gate V | bulk | gmin S | V(d)-V(s) V |")
    log("|---|---|---|---|---|---|")
    cases = [("M19/M20", 0.7, vz) for vz in (0.35, 0.45, 0.4957)] + [("M21", 1.1, 0.7)]
    for gmin in ("1e-12", "1e-15", "1e-18"):
        lines = ["* floating drain", LIB, f".option gmin={gmin}", "vdd vdd 0 1.8"]
        prints = []
        k = 0
        for name, vs, vg in cases:
            for bulk in ("vdd", "src"):
                b = "vdd" if bulk == "vdd" else f"s{k}"
                lines += [f"vs{k} s{k} 0 {vs}", f"vg{k} g{k} 0 {vg}",
                          f"x{k} d{k} g{k} s{k} {b} sky130_fd_pr__pfet_01v8 w=3u l=1u ad=0.87p as=0.87p pd=6.58u ps=6.58u",
                          f"c{k} d{k} 0 1p"]
                prints.append(f"print v(d{k}) v(s{k})")
                k += 1
        lines += [".control", "op"] + prints + [".endc", ".end"]
        v = run(f"c_float_g{gmin}.cir", "\n".join(lines) + "\n")
        k = 0
        for name, vs, vg in cases:
            for bulk in ("vdd", "src"):
                d, s = v.get(f"v(d{k})"), v.get(f"v(s{k})")
                log(f"| {name} | {vs} | {vg} | {bulk} | {gmin} | {None if d is None else f'{d - s:+.4e}'} |")
                k += 1


if __name__ == "__main__":
    RES.write_text("# erfc_ota M19~M21 영역 실측 (sky130 tt, ngspice-46)\n", encoding="utf-8")
    part_a("1e-12")
    part_a("1e-18")
    part_b("1e-12")
    part_b("1e-18")
    part_c()
