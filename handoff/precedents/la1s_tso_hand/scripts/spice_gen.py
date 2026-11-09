"""손설계점 + 레이아웃 기하(손가락별 ad/as/pd/ps)로 ngspice 넷리스트를 만들고 1회 돌려 결과를 파싱한다.

시험대(측정 구성, 회로 밖):
  - bias: 기준 다이오드 NMOS(M5와 같은 L·w_s, 손가락 1개)에 이상 전류원 Iref = I5/m5 -- M5·M7 게이트 넷 'bias'.
  - 입력: vin_p = VCM + AC 1, vin_n = OUT 에 큰 L(DC 단락, AC 개방) + vin_n-gnd 큰 C(AC 접지) -> beta=1 루프의
    개루프 전달 A(s) = v(OUT)/v(vin_p) (PM 정의 = 선언 되먹임 없음 -> beta=1, spec feedback 절).
  - 출력 측정: 1 Hz 이득, |A| = 1 주파수(GBW), 그 점 위상 -> PM = 180 + phase.
"""
import json, math, os, re, subprocess, sys

PDK = "C:/pdk/sky130_fd_pr"
NGSPICE = "C:/ngspice/Spice64/bin/ngspice_con.exe"
CELL = {"nmos": "nfet_01v8", "pmos": "pfet_01v8"}


def includes():
    L = []
    for k, cell in CELL.items():
        if k == "pmos":
            L.append('.include "%s/models/parameters/lod.spice"' % PDK)
        L.append('.include "%s/cells/%s/sky130_fd_pr__%s__tt.pm3.spice"' % (PDK, cell, cell))
        L.append('.include "%s/cells/%s/sky130_fd_pr__%s__mismatch.corner.spice"' % (PDK, cell, cell))
    return L


def netlist(design, geom, sim):
    dev = design["devices"]
    vdd = sim["vdd"]
    L = ["* two_stage_ota hand design + layout geometry"] + includes()
    L += ["Vdd vdd 0 dc %.6g" % vdd]  # ngspice 는 넷 이름 gnd 를 접지(0)로 읽는다
    nets_b = {"nmos": "gnd", "pmos": "vdd"}
    for n, p in dev.items():
        fg = geom["devices"][n]["finger_geom"]
        for k, f in enumerate(fg):
            L.append("X%s_%d %s %s %s %s sky130_fd_pr__%s l=%.6gu w=%.6gu ad=%.6gp as=%.6gp pd=%.6gu ps=%.6gu nf=1" % (
                n, k, p["d"], p["g"], p["s"], nets_b[p["kind"]], CELL[p["kind"]], p["L"] * 1e6, p["w_s"] * 1e6,
                f["ad"] * 1e12, f["as"] * 1e12, f["pd"] * 1e6, f["ps"] * 1e6))
    if "vbias" in sim:
        # bias 입력 = 이상 전압원(손계산 VGS5) -- 회로 밖 bias 생성기 없이 손계산 동작점 그대로
        L.append("Vbias bias 0 dc %.6g" % sim["vbias"])
    else:
        # bias 기준: M5와 같은 L, w_s, 손가락 하나(다이오드, VDS = VGS)
        m5 = dev["M5"]
        ad = m5["w_s"] * sim["ov"] * 1e12
        pdm = (m5["w_s"] + 2 * sim["ov"]) * 1e6
        L.append("Xref bias bias gnd gnd sky130_fd_pr__nfet_01v8 l=%.6gu w=%.6gu ad=%.6gp as=%.6gp pd=%.6gu ps=%.6gu nf=1" % (
            m5["L"] * 1e6, m5["w_s"] * 1e6, ad, ad, pdm, pdm))
        L.append("Iref vdd bias dc %.6g" % sim["iref"])
    L.append("Rz O1 N_cc_rz %.10g" % sim["Rz"])  # E-1 닫기 걸음이 6자리 아래라 10자리로 쓴다
    L.append("Cc N_cc_rz OUT %.10g" % sim["Cc"])
    L.append("CL OUT gnd %.6g" % sim["CL"])
    L.append("Vinp vin_p 0 dc %.6g ac 1" % sim["vcm"])
    L.append("Lfb OUT vin_n 1e9")
    L.append("Cfb vin_n gnd 1")
    L += [".control", "op", "print v(D3) v(O1) v(CS) v(OUT) v(bias) i(Vdd)"]
    for n in dev:
        L.append("print @m.x%s_0.msky130_fd_pr__%s[vds] @m.x%s_0.msky130_fd_pr__%s[vdsat] @m.x%s_0.msky130_fd_pr__%s[id] @m.x%s_0.msky130_fd_pr__%s[gm]" % (
            (n.lower(), CELL[dev[n]["kind"]]) * 4))
    L += ["ac dec 100 1 1e10",
          "let a = v(OUT)/v(vin_p)",
          "let adb = db(a)",
          "let ph = 180*cph(a)/pi",
          "meas ac a0db find adb at=1",
          "meas ac fu when adb=0 cross=1",
          "meas ac phu find ph at=fu",
          "print a0db fu phu",
          "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def run(net_text, workdir, stem):
    workdir = os.path.abspath(workdir)
    os.makedirs(workdir, exist_ok=True)
    p = os.path.join(workdir, stem + ".cir")
    open(p, "w", encoding="utf-8").write(net_text)
    r = subprocess.run([NGSPICE, "-b", p], capture_output=True, text=True, cwd=workdir)
    out = r.stdout + "\n" + r.stderr
    open(os.path.join(workdir, stem + ".log"), "w", encoding="utf-8").write(out)
    return out


def parse(out):
    res = {}
    for k in ("a0db", "fu", "phu"):
        m = re.search(r"^\s*%s\s*=\s*([-+0-9.eE]+)" % k, out, re.M)
        res[k] = float(m.group(1)) if m else None
    for nm in ("v(d3)", "v(o1)", "v(cs)", "v(out)", "v(bias)", "i(vdd)"):
        m = re.search(r"^%s\s*=\s*([-+0-9.eE]+)" % re.escape(nm), out, re.M | re.I)
        res[nm] = float(m.group(1)) if m else None
    dev = {}
    for m in re.finditer(r"^@m\.x(\w+?)_0\.msky130_fd_pr__\w+\[(\w+)\]\s*=\s*([-+0-9.eE]+)", out, re.M | re.I):
        dev.setdefault(m.group(1).upper(), {})[m.group(2)] = float(m.group(3))
    res["dev"] = dev
    if res["phu"] is not None:
        # cph 는 펼친 위상(DC 0도에서 내려감) -> PM = 180 + phase(fu)
        res["pm"] = 180.0 + res["phu"]
    return res
