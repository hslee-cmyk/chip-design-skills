"""묶음 III 실측 (sky130 tt, ngspice-46). 결과는 seal9_spice.txt 에 케이스마다 append.

봉인 9 (결함 고친 판, 계획 v6.38.5 N3.6 611행 문언):
  (i) 선언 없는 MOS 의 선언 방향 ID <= 0 -> 거부
  (iv) ID > 0 이고 I_off > eps*ID -> 거부,  eps = (gm/ID)*tol_V  => eps*ID = gm*tol_V
  I_off = 같은 L, W, VDS, VSB 에서 VGS = 0 채널 전류 (여기서는 복제 소자로 SPICE 가 직접 잼)
oracle 쪽 부호 ID = @id x sign(@vds) (oracle_compare.py:226-232 signed_id, 엔진 밖 사실로만 인용).
엔진(이상 KCL) 쪽 ID = 0 정확 -> (i) 로 거부.

T. 합성 toy (library/heldout 아님): 전류원 1 uA -> NMOS 다이오드 MN1 (넷 n1), PMOS pseudo-resistor MP: s = n1, b = n1(bulk = source),
   d = nfl, nfl 에는 MN2 gate + 1 pF 뿐 (KCL 항등 0, kcl_zero_audit 정의 Z2). VSG 0.1 ~ 0.9 V.
   대조 소자: MN1 (정상 전도). 복제 소자 MPoff: 같은 VD/VS/VB, VG = VS 로 I_off.
E. erfc_ota 전체 .op (현재 topology bulk = source, O-174), Table 1 치수 sky130 대용, 단위이득, M19~M21 + 대조 M5·M7.
"""
import json, pathlib, re, subprocess

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / "seal9_spice.txt"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] + [f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"' for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
TOPO = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/erfc_ota.topology.json")
TOLS = (1e-4, 1e-3, 1e-2)


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


def geo(w):  # LUT 특성화 규칙(W = 5 um: ad = 2.5p, pd = 7u)을 W 에 비례 -- 계획 T4-pre 문언
    return f"ad={0.5 * w:.4g}p as={0.5 * w:.4g}p pd={1.4 * w:.4g}u ps={1.4 * w:.4g}u"


def sgn(x):
    return 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)


def judge(idv_signed, gm, ioff):
    if idv_signed is None:
        return "판정 불능"
    if idv_signed <= 0:
        return "거부 (i) ID<=0"
    out = []
    for t in TOLS:
        out.append(f"tol{t:g}:{'통과' if ioff <= gm * t else '거부(iv)'}")
    return " ".join(out)


def dev_vals(v, dev):
    g = lambda k: v.get(f"{dev}[{k}]")
    return {k: g(k) for k in ("id", "gm", "gds", "vds", "vgs", "vth", "vdsat")}


def part_t(gmin, bulk_mode):
    log(f"\n### T. 합성 toy (MP W=3u L=1u, bulk = {bulk_mode}, gmin = {gmin} S)")
    vsgs = [0.1, 0.2, 0.3, 0.4, 0.6, 0.9]
    lines = ["* toy KCL-zero pseudo-resistor", LIB, f".option gmin={gmin}", "vvdd vdd 0 1.8"]
    prints = []
    for i, vsg in enumerate(vsgs):
        b = f"n1_{i}" if bulk_mode == "source" else "vdd"
        lines += [f"i0_{i} vdd n1_{i} 1u",
                  f"xmn1_{i} n1_{i} n1_{i} 0 0 sky130_fd_pr__nfet_01v8 w=2u l=1u {geo(2)}",
                  f"vsg_{i} n1_{i} gp_{i} {vsg}",
                  f"xmp_{i} nfa_{i} gp_{i} n1_{i} {b} sky130_fd_pr__pfet_01v8 w=3u l=1u {geo(3)}",
                  f"vam_{i} nfa_{i} nfl_{i} 0",                      # i(vam) > 0 = 선언 방향(source->drain) 전류
                  f"xmn2_{i} vdd nfl_{i} 0 0 sky130_fd_pr__nfet_01v8 w=2u l=1u {geo(2)}",
                  f"cfl_{i} nfl_{i} 0 1p",
                  # I_off 복제: 같은 VD, VS, VB, VG = VS
                  f"ers_{i} rs_{i} 0 n1_{i} 0 1",
                  f"erd_{i} rd_{i} 0 nfl_{i} 0 1",
                  f"erb_{i} rb_{i} 0 {b} 0 1",
                  f"vamo_{i} rd_{i} rdx_{i} 0",
                  f"xmpo_{i} rdx_{i} rs_{i} rs_{i} rb_{i} sky130_fd_pr__pfet_01v8 w=3u l=1u {geo(3)}"]
        for d in (f"xmp_{i}", f"xmn1_{i}"):
            kind = "pfet" if d.startswith("xmp") else "nfet"
            dev = f"@m.{d}.msky130_fd_pr__{kind}_01v8"
            prints.append(f"print {dev}[id] {dev}[gm] {dev}[gds] {dev}[vds] {dev}[vgs] {dev}[vth] {dev}[vdsat]")
        prints.append(f"print i(vam_{i}) i(vamo_{i}) v(nfl_{i}) v(n1_{i})")
    lines += [".control", "op"] + prints + [".endc", ".end"]
    v = run(f"toy_b{bulk_mode}_g{gmin}.cir", "\n".join(lines) + "\n")
    log("| 소자 | VSG V | V(d)-V(s) V | @id A | @vds V | signed ID A | i(vam) 선언방향 A | gm S | gds S | I_off A | 봉인 9 판정 (tol_V 1e-4/1e-3/1e-2 V) |")
    log("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, vsg in enumerate(vsgs):
        p = dev_vals(v, f"@m.xmp_{i}.msky130_fd_pr__pfet_01v8")
        n = dev_vals(v, f"@m.xmn1_{i}.msky130_fd_pr__nfet_01v8")
        ia, io = v.get(f"i(vam_{i})"), v.get(f"i(vamo_{i})")
        ioff = abs(io) if io is not None else None
        vd = None if v.get(f"v(nfl_{i})") is None else v[f"v(nfl_{i})"] - v[f"v(n1_{i})"]
        sid = None if p["id"] is None or p["vds"] is None else p["id"] * sgn(p["vds"])
        log(f"| MP (KCL 항등 0) | {vsg} | {vd:+.3e} | {p['id']:.3e} | {p['vds']:+.3e} | {sid:+.3e} | {ia:+.3e} | {p['gm']:.3e} | {p['gds']:.3e} | {ioff:.3e} | {judge(sid, p['gm'], ioff)} |")
        nid = n["id"] * sgn(n["vds"])
        log(f"| MN1 (대조, 1 uA) | -- | {n['vds']:+.3f} | {n['id']:.3e} | {n['vds']:+.3e} | {nid:+.3e} | -- | {n['gm']:.3e} | {n['gds']:.3e} | (생략) | {'통과 (ID>0, 정상)' if nid > 0 else '거부'} |")


def part_e(gmin):
    log(f"\n### E. erfc_ota 전체 .op (topology bulk 현재값 = M19/M20 vcn, M21 vcp; gmin = {gmin} S)")
    t = json.loads(TOPO.read_text(encoding="utf-8"))
    size = {}
    for names, wl in [(("M1A", "M1B", "M2A", "M2B", "M11", "M12"), (24, 0.6)), (("M13", "M14"), (24, 0.3)),
                      (("M17A", "M18A"), (12, 0.3)), (("M3B", "M4B"), (90, 0.3)), (("M15", "M16"), (1, 20)),
                      (("M5", "M6"), (60, 0.3)), (("M9", "M10"), (48, 0.3)), (("M3A", "M4A"), (18, 0.3)),
                      (("M3C", "M4C", "M17B", "M18B"), (30, 0.3)), (("M19", "M20", "M21"), (3, 1)), (("M7", "M8"), (24, 0.3))]:
        for n in names:
            size[n] = wl
    bulks = {m["name"]: m["bulk"] for m in t["netlist"]}
    log(f"bulk 확인: M19={bulks['M19']} M20={bulks['M20']} M21={bulks['M21']}")
    nm = lambda n: "0" if n == "gnd" else n.lower()
    lines = ["* erfc_ota full op", LIB, f".option gmin={gmin}", "vvdd vdd 0 1.8", "vvcp vcp 0 1.1", "vvcn vcn 0 0.7", "vinp vin_p 0 0.8",
             "einn vin_n 0 out 0 1"]
    target = ("M19", "M20", "M21")
    for m in t["netlist"]:
        w, l = size[m["name"]]
        model = "sky130_fd_pr__pfet_01v8" if m["kind"] == "pmos" else "sky130_fd_pr__nfet_01v8"
        d = nm(m["drain"])
        if m["name"] in target:
            lines.append(f"vam{m['name'].lower()} x{m['name'].lower()}d {d} 0")
            d = f"x{m['name'].lower()}d"
        lines.append(f"x{m['name'].lower()} {d} {nm(m['gate'])} {nm(m['source'])} {nm(m['bulk'])} {model} w={w}u l={l}u {geo(w)}")
        if m["name"] in target:  # I_off 복제
            k = m["name"].lower()
            lines += [f"e{k}rs {k}rs 0 {nm(m['source'])} 0 1", f"e{k}rd {k}rd 0 {nm(m['drain'])} 0 1", f"e{k}rb {k}rb 0 {nm(m['bulk'])} 0 1",
                      f"vamo{k} {k}rd {k}rdx 0", f"xo{k} {k}rdx {k}rs {k}rs {k}rb {model} w={w}u l={l}u {geo(w)}"]
    for p in t["passive_elements"]:
        a, b = (nm(x) for x in p["terminals"])
        if p["kind"] == "resistor":
            lines.append(f"r{p['name'].lower()} {a} {b} {p['value_ohm']}")
        else:
            lines.append(f"c{p['name'].lower()} {a} {b} {p['value_farad'] or 1e-12}")
    for s in t["ideal_sources"]:
        a, b = (nm(x) for x in s["terminals"])
        lines.append(f"i{s['name'].lower()} {a} {b} {s['value_amp']}")
    prints = []
    for dname in ("m19", "m20", "m21", "m5", "m7"):
        kind = "pfet" if dname in ("m19", "m20", "m21", "m7") else "nfet"
        dev = f"@m.x{dname}.msky130_fd_pr__{kind}_01v8"
        prints.append(f"print {dev}[id] {dev}[gm] {dev}[gds] {dev}[vds] {dev}[vgs] {dev}[vth] {dev}[vdsat]")
    prints.append("print i(vamm19) i(vamm20) i(vamm21) i(vamom19) i(vamom20) i(vamom21) v(z) v(out) v(n_m5g) v(n_m6g) v(n_m8g)")
    lines += [".control", "op"] + prints + [".endc", ".end"]
    v = run(f"erfc_full_g{gmin}.cir", "\n".join(lines) + "\n")
    log("| 소자 | @id A | @vds V | @vgs V | signed ID A | i(vam) 선언방향 A | gm S | gds S | I_off A | 봉인 9 판정 (tol_V 1e-4/1e-3/1e-2 V) |")
    log("|---|---|---|---|---|---|---|---|---|---|")
    for dname in ("m19", "m20", "m21", "m5", "m7"):
        kind = "pfet" if dname in ("m19", "m20", "m21", "m7") else "nfet"
        p = dev_vals(v, f"@m.x{dname}.msky130_fd_pr__{kind}_01v8")
        if p["id"] is None:
            log(f"| {dname} | (값 없음 -- log 확인) |")
            continue
        sid = p["id"] * sgn(p["vds"])
        ia = v.get(f"i(vam{dname})")
        io = v.get(f"i(vamo{dname})")
        ioff = abs(io) if io is not None else None
        jd = judge(sid, p["gm"], ioff) if ioff is not None else ("통과 (ID>0)" if sid > 0 else "거부 (i)")
        log(f"| {dname.upper()} | {p['id']:.3e} | {p['vds']:+.3e} | {p['vgs']:+.3f} | {sid:+.3e} | {'--' if ia is None else f'{ia:+.3e}'} | {p['gm']:.3e} | {p['gds']:.3e} | {'--' if ioff is None else f'{ioff:.3e}'} | {jd} |")
    for k in ("v(z)", "v(out)", "v(n_m5g)", "v(n_m6g)", "v(n_m8g)"):
        log(f"   {k} = {v.get(k)}")


if __name__ == "__main__":
    RES.write_text("# 묶음 III 봉인 9 SPICE 실측 (seal9_spice.py, sky130 tt, ngspice-46)\n", encoding="utf-8")
    for g in ("1e-12", "1e-18"):
        part_t(g, "source")
    part_t("1e-12", "vdd")
    for g in ("1e-12", "1e-18"):
        part_e(g)
