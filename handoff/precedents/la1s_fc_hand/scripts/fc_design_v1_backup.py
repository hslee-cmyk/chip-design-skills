"""folded_cascode gm/ID 손계산 설계(O-255 (1) -- 엔진 미사용, LUT npz 직접 읽음).

회로(연결 그대로, folded_cascode.topology.json): NMOS 입력쌍 M1/M2(tail M11), PMOS 전류원 M3/M4(gate vb1 = MP 다이오드),
PMOS 캐스코드 M5/M6(gate bias3 = 외부 bias 입력), NMOS 캐스코드 미러 M7/M8(gate Vg7, M7 다이오드) 위 M9/M10(gate Vg9,
M9 다이오드), 기준 가지 MP(vdd-vb1 다이오드) - Ibg(이상 전류원, 구현 불가) - MN(vb2-gnd 다이오드). 출력 단일 out, CL 1 pF
(측정 부하).

방법: Jespers & Murmann 2017 -- gm/ID 를 소자마다 고르고 VGS 를 LUT 에서, W = I / IDu(손가락 폭 슬라이스 값,
DEC-105 (2)). DC 양(노드·포화 여유)은 DC 풀이로, 이득·GBW·극은 동작점 소신호로(원칙 3).

설계 선택(문서 §1 에 근거; spec 미정 칸은 '선택'):
  C1 GBW 목표 30 MHz, PM >= 70 도, gain >= 60 dB -- spec SP-5/SP-3/SP-4 미정(사용자 결정), 기생 위험이 보이도록
     two_stage_ota(7 MHz) 보다 높게 고른 선택.
  C2 캐스코드 가지 전류 Icas = I1 (접힘 마디 전류 I3 = I1 + Icas = 2 I1 = I11) -- 미러 비 하나(k)로 M11·M3 를 같은
     Iref 에서 받는다(기준 가지가 하나라서).
  C3 미러 비 k = I11 / Iref (정수) -- 기준 가지 전력 대 미러 정확도 선택.
  C4 VCM(= 단위 이득 DC 점의 out) 과 접힘 마디 X 는 모든 소자 포화 여유의 최솟값이 가장 큰 점(spec input_dc SP-2,
     bias3 = bias 입력 값은 X 에서 따라옴).
"""
import json, math, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts")
import lutlib as lt
import mismatch as MM

LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/"
SPEC = json.load(open(LIB + "folded_cascode.sizing_spec.json", encoding="utf-8"))
TOPO = json.load(open(LIB + "folded_cascode.topology.json", encoding="utf-8"))
VDD = SPEC["human"]["supplies_v"]["values"]["vdd"]
CL = SPEC["human"]["element_values"]["CL"]["value_farad"]
CONS = {c["metric"]: (c["op"], c["value"]) for c in SPEC["human"]["constraints"]}
NET = {d["name"]: d for d in TOPO["netlist"]}
W_REF = 5e-6   # 노드 풀이 잠정 슬라이스(LUT 기준 폭); 행 w_s 는 (1)-b 에서 다시 고르고 IDu 를 그 슬라이스에서 다시 읽는다


def diode_vgs(kind, w, L, gmid, vs=0.0):
    """다이오드(VDS = VGS) 소자의 VGS 를 gm/ID 목표로 고정점 풀이."""
    v = 0.7
    for _ in range(60):
        v2 = lt.vgs_for_gmid(kind, w, L, gmid, v, vs)
        if abs(v2 - v) < 1e-7:
            return v2
        v = v2
    return v


def solve_nodes(x, vcm, X, w=W_REF):
    """gm/ID 고정 DC 점. 반환: 소자별 (VGS, VDS, VS) 와 노드. 크기는 pmos 도 양수(LUT 규약)."""
    o = {}
    # 기준 가지와 tail
    vgs_mn = diode_vgs("nmos", w, x["L"]["M11"], x["g"]["M11"])
    vsg_mp = diode_vgs("pmos", w, x["L"]["M3"], x["g"]["M3"])
    vb2, vb1 = vgs_mn, VDD - vsg_mp
    # 입력쌍: VS = tail (body effect), VDS = X - tail
    tail = 0.3
    for _ in range(80):
        vgs1 = lt.vgs_for_gmid("nmos", w, x["L"]["M1"], x["g"]["M1"], max(X - tail, 0.05), tail)
        t2 = vcm - vgs1
        if abs(t2 - tail) < 1e-7:
            break
        tail = 0.5 * (tail + t2)
    # PMOS 캐스코드 M6: VS(source-bulk) = VDD - X, VSD = X - out
    vsg6 = lt.vgs_for_gmid("pmos", w, x["L"]["M6"], x["g"]["M6"], max(X - vcm, 0.05), VDD - X)
    bias3 = X - vsg6
    # NMOS 캐스코드 미러
    vg9 = diode_vgs("nmos", w, x["L"]["M9"], x["g"]["M9"])
    vgs7 = diode_vgs("nmos", w, x["L"]["M7"], x["g"]["M7"], vg9)
    vg7 = vg9 + vgs7
    # M10 VGS = vg9, W10 = W9 -> 같은 전류면 VDS10 이 vg9 근처; M8 VGS = vg7 - vg10. 고정점: M8 이 M7 과 같은 IDu 를
    # 내는 vg10 (W8 = W7, 같은 전류)
    I7u = lt.dc("nmos", w, x["L"]["M7"], vgs7, vgs7, vg9)["IDu"]
    lo, hi = 0.05, vg7 - 0.05
    for _ in range(60):
        m = 0.5 * (lo + hi)
        i8 = lt.dc("nmos", w, x["L"]["M8"], vg7 - m, max(vcm - m, 0.0), m)["IDu"]
        if i8 > I7u:
            lo = m
        else:
            hi = m
    vg10 = 0.5 * (lo + hi)
    nodes = {"vb1": vb1, "vb2": vb2, "tail": tail, "X": X, "Y": X, "out": vcm, "Vg7": vg7, "Vg9": vg9,
             "Vg10": vg10, "bias3": bias3, "vin": vcm}
    # 소자 바이어스(VGS, VDS, VS) -- pmos 는 크기
    b = {"MN": (vgs_mn, vgs_mn, 0.0), "M11": (vgs_mn, tail, 0.0), "MP": (vsg_mp, vsg_mp, 0.0),
         "M3": (vsg_mp, VDD - X, 0.0), "M4": (vsg_mp, VDD - X, 0.0),
         "M1": (vgs1, X - tail, tail), "M2": (vgs1, X - tail, tail),
         "M6": (vsg6, X - vcm, VDD - X), "M5": (vsg6, X - vg7, VDD - X),
         "M9": (vg9, vg9, 0.0), "M10": (vg9, vg10, 0.0), "M7": (vgs7, vgs7, vg9), "M8": (vg7 - vg10, vcm - vg10, vg10)}
    return b, nodes


def currents(x, I1):
    Ic = x["r_cas"] * I1
    I11 = 2 * I1
    Iref = I11 / x["k"]
    return {"M1": I1, "M2": I1, "M11": I11, "MN": Iref, "M3": I1 + Ic, "M4": I1 + Ic, "MP": Iref,
            "M5": Ic, "M6": Ic, "M7": Ic, "M8": Ic, "M9": Ic, "M10": Ic}


def devices(x, I1, b, ws):
    """ws: 소자별 손가락 폭(행 w_s). IDu 는 그 슬라이스에서 같은 (VGS, VDS, VS) 로 읽는다(DEC-105 (2))."""
    I = currents(x, I1)
    dev = {}
    for n, (vgs, vds, vs) in b.items():
        k = NET[n]["kind"]
        L = x["L"][n]
        r = lt.dc(k, ws[n], L, vgs, vds, vs)
        if not r["IDu"] > 0:
            raise ValueError("%s 전류 0 (VDS %.3f) -- 이 바이어스는 실현 불가" % (n, vds))
        W = I[n] / r["IDu"]
        sc = W / lt._slice(k, ws[n])["W"]
        c = lt.caps(k, L, vgs, vds, vs, W)
        dev[n] = {"kind": k, "L": L, "w_s": ws[n], "W": W, "ID": I[n], "VGS": vgs, "VDS": vds, "VS": vs,
                  "gm": r["GM"] * sc, "gds": r["GDS"] * sc, "gmb": r["GMBS"] * sc, "VDSAT": r["VDSAT"],
                  "gmid": r["gmid"], "IDu": r["IDu"], "caps": c, "margin": vds - r["VDSAT"]}
    return dev


def ac(dev):
    """손계산 소신호: 출력 저항(캐스코드), GBW = gm1 / (2π C_out), 비우세 극들(접힘 마디·미러 마디)."""
    d = dev
    ro = {n: 1.0 / d[n]["gds"] for n in d}
    r13 = 1.0 / (d["M1"]["gds"] + d["M3"]["gds"])
    Rup = ro["M6"] + r13 * (1 + (d["M6"]["gm"] + d["M6"]["gmb"]) * ro["M6"])
    Rdn = ro["M8"] + ro["M10"] * (1 + (d["M8"]["gm"] + d["M8"]["gmb"]) * ro["M8"])
    Rout = Rup * Rdn / (Rup + Rdn)
    gm1 = d["M1"]["gm"]
    A0 = gm1 * Rout
    Cout = CL + d["M6"]["caps"]["CDD"] + d["M8"]["caps"]["CDD"]
    gbw = gm1 / (2 * math.pi * Cout)
    cX = d["M1"]["caps"]["CDD"] + d["M3"]["caps"]["CDD"] + d["M6"]["caps"]["CSS"]
    pX = (d["M6"]["gm"] + d["M6"]["gmb"]) / (2 * math.pi * cX)
    cY = d["M2"]["caps"]["CDD"] + d["M4"]["caps"]["CDD"] + d["M5"]["caps"]["CSS"]
    pY = (d["M5"]["gm"] + d["M5"]["gmb"]) / (2 * math.pi * cY)
    c7 = d["M7"]["caps"]["CGG"] + d["M8"]["caps"]["CGG"] + d["M5"]["caps"]["CDD"]
    g7 = 1.0 / (1.0 / (d["M7"]["gm"] + d["M7"]["gmb"]) + 1.0 / d["M9"]["gm"])
    p7 = g7 / (2 * math.pi * c7)
    c9 = d["M9"]["caps"]["CGG"] + d["M10"]["caps"]["CGG"] + d["M7"]["caps"]["CSS"]
    p9 = d["M9"]["gm"] / (2 * math.pi * c9)
    c10 = d["M10"]["caps"]["CDD"] + d["M8"]["caps"]["CSS"]
    p10 = (d["M8"]["gm"] + d["M8"]["gmb"]) / (2 * math.pi * c10)
    # 위상: 직접 경로(X -> out) 반 신호, 미러 경로(Y -> Vg7 -> 미러 -> out) 반 신호 -- 반 신호 경로의 극은 짝 영점(2p)과
    # 함께 doublet 이라 위상 몫 = atan(f/p) - atan(f/2p) 로 근사, 직접 경로 극은 반(1/2) 가중
    f = gbw
    ph = 0.5 * math.degrees(math.atan(f / pX)) + math.degrees(math.atan(f / pY) - math.atan(f / (2 * pY))) + \
        math.degrees(math.atan(f / p7) - math.atan(f / (2 * p7))) + math.degrees(math.atan(f / p9) - math.atan(f / (2 * p9))) + \
        0.5 * math.degrees(math.atan(f / p10))
    pm = 90.0 - ph
    return {"Rout": Rout, "A0_db": 20 * math.log10(A0), "gbw": gbw, "Cout": Cout, "pm": pm,
            "poles_hz": {"X": pX, "Y": pY, "Vg7": p7, "Vg9": p9, "Vg10": p10}}


def guards(dev):
    gm1 = dev["M1"]["gm"]
    s1, n1 = MM.sigma_vt("nmos", dev["M1"]["L"], dev["M1"]["w_s"], max(1, round(dev["M1"]["W"] / dev["M1"]["w_s"])))
    s3, n3 = MM.sigma_vt("pmos", dev["M3"]["L"], dev["M3"]["w_s"], max(1, round(dev["M3"]["W"] / dev["M3"]["w_s"])))
    s10, n10 = MM.sigma_vt("nmos", dev["M10"]["L"], dev["M10"]["w_s"], max(1, round(dev["M10"]["W"] / dev["M10"]["w_s"])))
    g3, g10 = dev["M3"]["gm"], dev["M10"]["gm"]
    oe = math.sqrt(1 + ((g3 * s3) ** 2 + (g10 * s10) ** 2) / (gm1 * s1) ** 2)
    ne = 1 + (g3 + g10) / gm1
    return {"offset_excess": oe, "noise_excess_th": ne, "sigma_mV": {"M1": s1 * 1e3, "M3": s3 * 1e3, "M10": s10 * 1e3},
            "slopes": [n1, n3, n10]}


def best_bias(x, w=W_REF):
    """C4: (VCM, X) 격자에서 포화 여유 최솟값이 가장 큰 점."""
    best = None
    for i in range(0, 21):
        vcm = 0.7 + i * 0.02
        for j in range(0, 16):
            X = 1.30 + j * 0.02
            try:
                b, nd = solve_nodes(x, vcm, X, w)
                ws = {n: w for n in b}
                dev = devices(x, 1e-6, b, ws)
            except ValueError:
                continue
            mm = min(dv["margin"] for nm, dv in dev.items())
            if best is None or mm > best[0]:
                best = (mm, vcm, X, min(dev, key=lambda n: dev[n]["margin"]))
    return best


def size(x, gbw_target):
    """I1 를 GBW 목표로(gm/ID 고정이면 노드 전압은 전류와 무관, gm·C 는 전류 비례 -- C_out 의 CL 몫만 고정이라 고정점)."""
    mm, vcm, X, crit = best_bias(x)
    b, nd = solve_nodes(x, vcm, X)
    ws = {n: W_REF for n in b}
    I1 = 1e-6
    for _ in range(40):
        dev = devices(x, I1, b, ws)
        a = ac(dev)
        I2 = I1 * gbw_target / a["gbw"]
        if abs(I2 / I1 - 1) < 1e-6:
            break
        I1 = I2
    return {"x": x, "vcm": vcm, "X": X, "min_margin": mm, "crit": crit, "bias": b, "nodes": nd, "I1": I1,
            "dev": dev, "ac": a, "guards": guards(dev)}


def dump(res, path):
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, float):
            return float("%.6g" % o)
        return o
    json.dump(clean(res), open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    x = json.load(open(sys.argv[1], encoding="utf-8"))
    res = size(x, x["gbw_target"])
    P = VDD * (2 * res["I1"] + 2 * x["r_cas"] * res["I1"] + 2 * res["I1"] / x["k"])
    res["power_W"] = P
    dump(res, sys.argv[2])
    a, g = res["ac"], res["guards"]
    with open(sys.argv[3], "a", encoding="utf-8") as f:
        f.write("%s | vcm %.3f X %.3f bias3 %.3f minmargin %.3f(%s) | I1 %.3f uA P %.1f uW | A0 %.1f dB GBW %.2f MHz PM~%.1f | "
                "oe %.3f ne %.3f | poles MHz %s\n" % (x.get("tag", ""), res["vcm"], res["X"], res["nodes"]["bias3"], res["min_margin"],
                                                    res["crit"], res["I1"] * 1e6, P * 1e6, a["A0_db"], a["gbw"] / 1e6, a["pm"],
                                                    g["offset_excess"], g["noise_excess_th"],
                                                    {k: round(v / 1e6) for k, v in a["poles_hz"].items()}))
