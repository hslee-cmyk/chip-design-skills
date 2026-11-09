"""erfc_ota 전회로 sky130 netlist 생성기 (측정 bench 전용, 저장소 파일 읽기만).

연결 = assets/heldout/erfc_ota.topology.json 그대로(M19/M20 bulk = vcn, M21 bulk = vcp, O-174 반영본).
치수 = 원문 p.9 Table 1. 공정 = sky130 tt(원문 0.18 um 대용). sky130 |Vth|가 원문 공정보다 커서
VDD·VCP·VCN·입력 CM 은 bench 인자(원문 1.8/1.1/0.7/0.8 V 는 sky130에서 바이어스 붕괴 -- erfc_region.md 5절).
pseudo-resistor 변형: mode='mos'(M19~M21 Table 1 그대로) 또는 mode='res'(M19~M21 자리에 선형 저항 R_ps).
"""
import json, pathlib, re, subprocess

NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] +
                [f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"'
                 for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
TOPO = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/erfc_ota.topology.json")
SIZE = {}
for names, wl in [(("M1A", "M1B", "M2A", "M2B", "M11", "M12"), (24, 0.6)), (("M13", "M14"), (24, 0.3)),
                  (("M17A", "M18A"), (12, 0.3)), (("M3B", "M4B"), (90, 0.3)), (("M15", "M16"), (1, 20)),
                  (("M5", "M6"), (60, 0.3)), (("M9", "M10"), (48, 0.3)), (("M3A", "M4A"), (18, 0.3)),
                  (("M3C", "M4C", "M17B", "M18B"), (30, 0.3)), (("M19", "M20", "M21"), (3, 1)), (("M7", "M8"), (24, 0.3))]:
    for n in names:
        SIZE[n] = wl
PSEUDO = ("M19", "M20", "M21")


def nm(n):
    return "0" if n == "gnd" else n.lower()


def netlist(vdd, vcp, vcn, vcm, cbat=1e-12, cbat2=None, mode="mos", r_ps=None, cfg="buf", extra="", gmin="1e-15", stim=None, cl=7e-11):
    """cfg: 'buf' = 단위이득 버퍼(vin_n = out), 'ol' = 개루프 AC(DC 만 되먹임, R 1e15 + C 1e6 F),
    'inv' = 단위이득 반전(R_in = R_f = rfb, 원문 p.13 구성; vin_p = vcm).
    stim: 입력 소스 줄(문자열) -- None 이면 DC vcm."""
    t = json.loads(TOPO.read_text(encoding="utf-8"))
    L = ["* erfc_ota bench", LIB, f".option gmin={gmin} reltol=1e-5 abstol=1e-15 vntol=1e-8 method=gear",
         f"vvdd vdd 0 {vdd}", f"vvcp vcp 0 {vcp}", f"vvcn vcn 0 {vcn}"]
    for m in t["netlist"]:
        if mode == "res" and m["name"] in PSEUDO:
            L.append(f"r{m['name'].lower()} {nm(m['drain'])} {nm(m['source'])} {r_ps}")
            continue
        w, l = SIZE[m["name"]]
        model = "sky130_fd_pr__pfet_01v8" if m["kind"] == "pmos" else "sky130_fd_pr__nfet_01v8"
        L.append(f"x{m['name'].lower()} {nm(m['drain'])} {nm(m['gate'])} {nm(m['source'])} {nm(m['bulk'])} {model} "
                 f"w={w}u l={l}u ad={w * 0.29:.4g}p as={w * 0.29:.4g}p pd={2 * (w + 0.29):.4g}u ps={2 * (w + 0.29):.4g}u")
    for p in t["passive_elements"]:
        a, b = (nm(x) for x in p["terminals"])
        if p["kind"] == "resistor":
            L.append(f"r{p['name'].lower()} {a} {b} {p['value_ohm']}")
        else:
            v = p["value_farad"]
            if p["name"] in ("CBAT1_L", "CBAT1_R"):
                v = cbat
            elif p["name"] == "CBAT2":
                v = cbat if cbat2 is None else cbat2
            elif p["name"] == "CL":
                v = cl
            L.append(f"c{p['name'].lower()} {a} {b} {v}")
    for s in t["ideal_sources"]:
        a, b = (nm(x) for x in s["terminals"])
        L.append(f"i{s['name'].lower()} {a} {b} {s['value_amp']}")
    if cfg == "buf":
        L.append("rfbk vin_n out 1e-3")
        L.append(stim or f"vinp vin_p 0 {vcm}")
    elif cfg == "ol":
        L += ["rfbk vin_n out 1e15", "cfbk vin_n 0 1e6", f"vinp vin_p 0 dc {vcm} ac 1"]
    elif cfg == "inv":
        L += [f"vinp vin_p 0 {vcm}", "rin vsig vin_n 1e6", "rf vin_n out 1e6", stim or f"vsig vsig 0 {vcm}"]
    elif cfg == "inve":   # 단위이득 반전(beta = 1/2), 이상 VCVS 저항 분압 -- 부하 0 (원문 저항값 미기재)
        L += [f"vinp vin_p 0 {vcm}", "ein vin_n 0 value={0.5*(v(vsig)+v(out))}", stim or f"vsig vsig 0 {vcm}"]
    L.append(extra)
    return "\n".join(L) + "\n"


def run(path, deck):
    path = pathlib.Path(path)
    path.write_text(deck, encoding="utf-8")
    out = subprocess.run([NG, "-b", str(path)], capture_output=True, text=True, cwd=path.parent)
    path.with_suffix(".log").write_text(out.stdout + "\n--stderr--\n" + out.stderr, encoding="utf-8")
    vals = {}
    for line in out.stdout.splitlines():
        m = re.match(r"\s*(\S+)\s*=\s*([-+0-9.eE]+)\s*$", line)
        if m:
            vals[m.group(1).lower()] = float(m.group(2))
    return vals, out.stdout


def dev(name):
    kind = "pfet" if name.upper() in PMOS else "nfet"
    return f"@m.x{name.lower()}.msky130_fd_pr__{kind}_01v8"


PMOS = {m["name"] for m in json.loads(TOPO.read_text(encoding="utf-8"))["netlist"] if m["kind"] == "pmos"}
ALL = [m["name"] for m in json.loads(TOPO.read_text(encoding="utf-8"))["netlist"]]
