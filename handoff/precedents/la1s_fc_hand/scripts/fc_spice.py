"""folded_cascode 설계점 + 손가락별 기하로 ngspice 넷리스트를 만들고 돌려 파싱(O-255 (2)·(5)).

시험대(회로 밖 측정 구성):
  - Ibg: topology 의 이상 전류원(vb1 -> vb2, 구현 불가) = Iref. bias3: bias 입력 = 이상 전압원(설계 선택 값).
  - vin_p = VCM + AC 1, vin_n = out 에 큰 L(DC 단락, AC 개방) + 큰 C(AC 접지) -> beta=1 루프 개루프 A(s) = v(out)/v(vin_p)
    (spec feedback: 선언 되먹임 없음 -> beta=1, PM 정의).
  - CL = spec 측정 부하. 배선 기생(있으면): 넷별 대지 C 와 소자 단자 직렬 R 을 extra 로 받는다.
"""
import json, math, os, re, subprocess, sys

PDK = "C:/pdk/sky130_fd_pr"
NGSPICE = "C:/ngspice/Spice64/bin/ngspice_con.exe"
CELL = {"nmos": "nfet_01v8", "pmos": "pfet_01v8"}
NODES = ["vb1", "vb2", "tail", "X", "Y", "out", "Vg7", "Vg9", "Vg10"]


def includes():
    L = []
    for k, cell in CELL.items():
        if k == "pmos":
            L.append('.include "%s/models/parameters/lod.spice"' % PDK)
        L.append('.include "%s/cells/%s/sky130_fd_pr__%s__tt.pm3.spice"' % (PDK, cell, cell))
        L.append('.include "%s/cells/%s/sky130_fd_pr__%s__mismatch.corner.spice"' % (PDK, cell, cell))
    return L


def netlist(des, sim, extra=None):
    """des["devices"][n] = {kind,d,g,s,L,w_s,m,finger_geom[]}; extra = {"cnet": {net: F}, "rser": {(dev,term): ohm}}."""
    dev = des["devices"]
    bulk = {"nmos": "0", "pmos": "vdd"}
    L = ["* folded_cascode hand design"] + includes()
    L.append("Vdd vdd 0 dc %.6g" % sim["vdd"])
    ren = {"gnd": "0"}
    rser = (extra or {}).get("rser", {})
    for n, p in dev.items():
        for k, f in enumerate(p["finger_geom"]):
            t = {}
            for term in ("d", "g", "s"):
                net = ren.get(p[term], p[term])
                r = rser.get("%s.%s" % (n, term))
                if r:
                    inner = "%s_%s_%d" % (n, term, k)
                    L.append("R%s_%s_%d %s %s %.6g" % (n, term, k, net, inner, r * p["m"]))  # m 손가락 병렬 -> 손가락당 m 배
                    net = inner
                t[term] = net
            L.append("X%s_%d %s %s %s %s sky130_fd_pr__%s l=%.6gu w=%.6gu ad=%.6gp as=%.6gp pd=%.6gu ps=%.6gu nf=1" % (
                n, k, t["d"], t["g"], t["s"], bulk[p["kind"]], CELL[p["kind"]], p["L"] * 1e6, p["w_s"] * 1e6,
                f["ad"] * 1e12, f["as"] * 1e12, f["pd"] * 1e6, f["ps"] * 1e6))
    for k, d in enumerate(des.get("dummies", [])):
        L.append("XDUM%d %s %s %s %s sky130_fd_pr__%s l=%.6gu w=%.6gu nf=1" % (k, d["net"], d["net"], d["net"], bulk[d["kind"]],
                                                                            CELL[d["kind"]], d["L"] * 1e6, d["w_s"] * 1e6))
    L.append("Ibg vb1 vb2 dc %.10g" % sim["iref"])
    L.append("Vb3 bias3 0 dc %.10g" % sim["bias3"])
    L.append("CL out 0 %.6g" % sim["CL"])
    for net, c in sorted((extra or {}).get("cnet", {}).items()):
        L.append("Cw_%s %s 0 %.6g" % (net, ren.get(net, net), c))
    L.append("Vinp vin_p 0 dc %.10g ac 1" % sim["vcm"])
    L.append("Lfb out vin_n 1e9")
    L.append("Cfb vin_n 0 1")
    L += [".control", "op", "print " + " ".join("v(%s)" % n for n in NODES) + " i(Vdd)"]
    for n in dev:
        c = CELL[dev[n]["kind"]]
        L.append("print " + " ".join("@m.x%s_0.msky130_fd_pr__%s[%s]" % (n.lower(), c, q) for q in ("vds", "vdsat", "id", "gm", "gds", "vgs")))
    L += ["ac dec 100 1 1e10",
          "let a = v(out)/v(vin_p)",
          "let adb = db(a)",
          "let ph = 180*cph(a)/pi",
          "meas ac a0db find adb at=1",
          "meas ac fu when adb=0 cross=1",
          "meas ac phu find ph at=fu",
          "print a0db fu phu",
          "quit", ".endc", ".end"]
    return "\n".join(L) + "\n"


def run(text, workdir, stem):
    workdir = os.path.abspath(workdir)
    os.makedirs(workdir, exist_ok=True)
    p = os.path.join(workdir, stem + ".cir")
    open(p, "w", encoding="utf-8").write(text)
    r = subprocess.run([NGSPICE, "-b", p], capture_output=True, text=True, cwd=workdir)
    out = r.stdout + "\n" + r.stderr
    open(os.path.join(workdir, stem + ".log"), "w", encoding="utf-8").write(out)
    return parse(out)


def parse(out):
    res = {}
    for k in ("a0db", "fu", "phu"):
        m = re.search(r"^\s*%s\s*=\s*([-+0-9.eE]+)" % k, out, re.M)
        res[k] = float(m.group(1)) if m else None
    for nm in NODES + ["i(vdd)"]:
        key = nm if nm.startswith("i(") else "v(%s)" % nm.lower()
        m = re.search(r"^%s\s*=\s*([-+0-9.eE]+)" % re.escape(key), out, re.M | re.I)
        res[nm] = float(m.group(1)) if m else None
    dev = {}
    for m in re.finditer(r"^@m\.x(\w+?)_0\.msky130_fd_pr__\w+\[(\w+)\]\s*=\s*([-+0-9.eE]+)", out, re.M | re.I):
        dev.setdefault(m.group(1).upper(), {})[m.group(2)] = float(m.group(3))
    res["dev"] = dev
    if res["phu"] is not None:
        res["pm"] = 180.0 + res["phu"]
    if res.get("i(vdd)") is not None:
        res["power_W"] = -res["i(vdd)"] * 1.8
    return res


def sat_margins(res, des):
    """VDS - VDsat (ngspice 부호: pmos vds 음수) -- 손가락 0 대표."""
    out = {}
    for n, v in res["dev"].items():
        if "vds" in v and "vdsat" in v:
            out[n] = abs(v["vds"]) - abs(v["vdsat"])
    return out
