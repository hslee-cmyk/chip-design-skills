"""two_stage_ota gm/ID 손계산 설계(엔진 미사용).

방법: Jespers & Murmann 2017 §6.3 (pp.267-277, 식 6.63-6.69) -- 용량 비와 gm/ID 스윕으로 설계점을 찾는다.
이 회로는 단일 출력 5T 1단 + CS 2단 + Rz-Cc 직렬 보상(topology 그대로).

설계 선택(근거는 문서 §2):
  S1 Rz = 1/gm6  -- 오른쪽 반평면 영점 제거(영점을 무한대로).
  S2 M6 L = M3 L, M6 gm/ID = M3 gm/ID -- KVL: VSG6 = VSD4 = VSD3 = VSG3 이므로 같은 IDu → 계통 offset 0.
  S3 M5·M7 같은 L -- 같은 gate·source → 같은 VGS → 전류 비 = W 비(미러 비).
  S4 입력 공통 전압 VCM = M1·M5 포화 여유가 같아지는 점(spec input_dc 미정 SP-2 → 선택으로 표지).
  S5 출력 DC = VCM(단위 이득 되먹임 DC 점, PM 정의 beta=1 루프).
DC 양(VCM·노드·포화)은 DC 풀이로, 이득·GBW·PM은 동작점 소신호 MNA로(원칙 3).
"""
import itertools, json, math, sys, time
import numpy as np
import lutlib as lt

SPEC = json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/two_stage_ota.sizing_spec.json", encoding="utf-8"))
CONS = {c["metric"]: (c["op"], c["value"]) for c in SPEC["human"]["constraints"]}
VDD = SPEC["human"]["supplies_v"]["values"]["vdd"]
CL = SPEC["human"]["element_values"]["CL"]["value_farad"]
GBW_T = CONS["gbw_ss_hz"][1]
PM_T = CONS["pm_ss_deg"][1]
GAIN_T = CONS["gain_ss_db"][1]
W_REF = 5e-6  # 손가락 폭 잠정값 = LUT 기준 폭 슬라이스(용량 표 w_ref와 같음, 나중 레이아웃에서 다시 고름)


def pmos_diode(gmid, L, ws):
    """다이오드 PMOS(VSD = VSG, VS = 0)의 VSG를 gm/ID 목표로 고정점 풀이."""
    v = 0.8
    for _ in range(40):
        v2 = lt.vgs_for_gmid("pmos", ws, L, gmid, v, 0.0)
        if abs(v2 - v) < 1e-6:
            break
        v = v2
    return v


def dc_point(x, I1, I6, ws=None):
    """설계 변수 x와 전류로 DC 점(노드 전압·소자 동작점)을 푼다."""
    wsn = ws or {}
    w = lambda d, k: wsn.get(d, W_REF)
    L1, L3, L5 = x["L1"], x["L3"], x["L5"]
    L6 = x.get("L6", L3)  # S2 일반형: VSG6 = VSG3 이면 L6 은 따로 골라도 된다(gm/ID6 은 그 VSG 에서 따라옴)
    # M3 다이오드
    vsg3 = pmos_diode(x["g3"], L3, w("M3", "pmos"))
    r3 = lt.dc("pmos", w("M3", "pmos"), L3, vsg3, vsg3, 0.0)
    d3 = VDD - vsg3
    o1 = d3  # S2: VSD4 = VSD3
    # M5: gm/ID5 목표, VDS5 = CS (아직 모름) -> VCM 선택(S4)과 함께 고정점
    cs = 0.3
    for _ in range(60):
        vgs5 = lt.vgs_for_gmid("nmos", w("M5", "nmos"), L5, x["g5"], cs, 0.0)
        r5 = lt.dc("nmos", w("M5", "nmos"), L5, vgs5, cs, 0.0)
        vgs1 = lt.vgs_for_gmid("nmos", w("M1", "nmos"), L1, x["g1"], d3 - cs, cs)
        r1 = lt.dc("nmos", w("M1", "nmos"), L1, vgs1, d3 - cs, cs)
        # S4: (VDS5 - VDSAT5) = (VDS1 - VDSAT1)  ->  cs - vdsat5 = d3 - cs - vdsat1
        cs_new = 0.5 * (d3 - r1["VDSAT"] + r5["VDSAT"])
        if abs(cs_new - cs) < 1e-6:
            cs = cs_new
            break
        cs = 0.5 * (cs + cs_new)
    vcm = cs + vgs1
    vout = vcm  # S5
    # M6: VSG6 = VSD4 = vsg3, VSD6 = VDD - vout
    r6 = lt.dc("pmos", w("M6", "pmos"), L6, vsg3, VDD - vout, 0.0)
    # M7: VGS7 = VGS5, VDS7 = vout
    r7 = lt.dc("nmos", w("M7", "nmos"), L5, vgs5, vout, 0.0)
    r4 = lt.dc("pmos", w("M4", "pmos"), L3, vsg3, VDD - o1, 0.0)
    r2 = r1
    ids = {"M1": I1, "M2": I1, "M3": I1, "M4": I1, "M5": 2 * I1, "M6": I6, "M7": I6}
    ops = {"M1": (r1, vgs1, d3 - cs, cs, L1, "nmos"), "M2": (r2, vgs1, o1 - cs, cs, L1, "nmos"),
           "M3": (r3, vsg3, vsg3, 0.0, L3, "pmos"), "M4": (r4, vsg3, VDD - o1, 0.0, L3, "pmos"),
           "M5": (r5, vgs5, cs, 0.0, L5, "nmos"), "M6": (r6, vsg3, VDD - vout, 0.0, L6, "pmos"),
           "M7": (r7, vgs5, vout, 0.0, L5, "nmos")}
    dev = {}
    for n, (r, vgs, vds, vs, L, k) in ops.items():
        W = ids[n] / r["IDu"]
        sc = W / lt._slice(k, w(n, k))["W"]  # 손가락 폭 슬라이스 값 -> 실제 W 배율
        c = lt.caps(k, L, vgs, vds, vs, W)
        dev[n] = {"kind": k, "L": L, "W": W, "ID": ids[n], "VGS": vgs, "VDS": vds, "VS": vs,
                  "gm": r["GM"] * sc, "gds": r["GDS"] * sc, "gmb": r["GMBS"] * sc, "VDSAT": r["VDSAT"], "VTH": r["VTH"],
                  "gmid": r["gmid"], "IDu": r["IDu"], "caps": c, "w_s": w(n, k)}
    nodes = {"D3": d3, "O1": o1, "CS": cs, "OUT": vout, "VCM": vcm}
    return dev, nodes


def mna(dev, Cc, Rz, f):
    """소신호 MNA: 노드 D3, O1, CS, X(=N_cc_rz), OUT. 입력 vin_p=+0.5, vin_n=-0.5. 반환 v(OUT)."""
    idx = {"D3": 0, "O1": 1, "CS": 2, "X": 3, "OUT": 4}
    n = 5
    s = 2j * math.pi * f
    Y = np.zeros((n, n), complex)
    I = np.zeros(n, complex)
    vin = {"vin_p": 0.5, "vin_n": -0.5, "vdd": 0.0, "gnd": 0.0, "bias": 0.0}

    def stamp_y(a, b, y):
        ia, ib = idx.get(a), idx.get(b)
        if ia is not None:
            Y[ia, ia] += y
        if ib is not None:
            Y[ib, ib] += y
        if ia is not None and ib is not None:
            Y[ia, ib] -= y
            Y[ib, ia] -= y
        # 고정 노드 쪽 전류
        if ia is not None and ib is None and b in vin:
            I[ia] += y * vin[b]
        if ib is not None and ia is None and a in vin:
            I[ib] += y * vin[a]

    def vccs(d, so, g, s_, gm):
        """전류 gm*(v(g)-v(s_)) 가 d 에서 so 로 흐름."""
        for node, sign in ((d, 1), (so, -1)):
            i = idx.get(node)
            if i is None:
                continue
            for ctrl, cs_ in ((g, 1), (s_, -1)):
                j = idx.get(ctrl)
                if j is not None:
                    Y[i, j] += sign * cs_ * gm
                else:
                    I[i] -= sign * cs_ * gm * vin.get(ctrl, 0.0)

    term = {"M1": ("D3", "vin_n", "CS"), "M2": ("O1", "vin_p", "CS"), "M3": ("D3", "D3", "vdd"),
            "M4": ("O1", "D3", "vdd"), "M5": ("CS", "bias", "gnd"), "M6": ("OUT", "O1", "vdd"),
            "M7": ("OUT", "bias", "gnd")}
    for nme, (d, g, so) in term.items():
        p = dev[nme]
        c = p["caps"]
        bulk = "gnd" if p["kind"] == "nmos" else "vdd"
        vccs(d, so, g, so, p["gm"])
        vccs(d, so, bulk, so, p["gmb"])
        stamp_y(d, so, p["gds"])
        stamp_y(g, so, s * c["CGS"])
        stamp_y(g, d, s * c["CGD"])
        stamp_y(d, bulk, s * max(c["CDD"] - c["CGD"], 0.0))
        stamp_y(so, bulk, s * max(c["CSS"] - c["CGS"], 0.0))
    stamp_y("O1", "X", 1.0 / Rz)
    stamp_y("X", "OUT", s * Cc)
    stamp_y("OUT", "gnd", s * CL)
    v = np.linalg.solve(Y, I)
    return v[idx["OUT"]]


def ac_metrics(dev, Cc, Rz):
    a0 = abs(mna(dev, Cc, Rz, 1.0))
    gain_db = 20 * math.log10(a0)
    # 단위 이득 주파수: 로그 이분
    lo, hi = 1e3, 1e10
    if abs(mna(dev, Cc, Rz, hi)) > 1:
        return gain_db, float("nan"), float("nan")
    for _ in range(60):
        m = math.sqrt(lo * hi)
        if abs(mna(dev, Cc, Rz, m)) > 1:
            lo = m
        else:
            hi = m
    fu = math.sqrt(lo * hi)
    # 위상은 DC 0도에서 내려간다 -- 펼쳐서 계산
    fs = np.logspace(0, math.log10(fu), 60)
    phs = np.unwrap([np.angle(mna(dev, Cc, Rz, f_)) for f_ in fs])
    pm = 180.0 + math.degrees(phs[-1])
    return gain_db, fu, pm


_unit = {}


def scaled(x, I1, I6, ws=None):
    """gm/ID 고정이면 노드 전압은 전류와 무관하고 gm·gds·C·W 는 전류에 비례 -- 단위 전류 동작점을 한 번 풀어 비례."""
    key = (json.dumps(x, sort_keys=True), json.dumps(ws or {}, sort_keys=True))
    if key not in _unit:
        _unit[key] = dc_point(x, 1.0, 1.0, ws)
    du, nodes = _unit[key]
    dev = {}
    for n, p in du.items():
        k = I6 if n in ("M6", "M7") else I1
        q = dict(p)
        for f in ("W", "ID", "gm", "gds", "gmb"):
            q[f] = p[f] * k
        q["caps"] = {c: v * k for c, v in p["caps"].items()}
        dev[n] = q
    return dev, nodes


def evaluate(x, I1, I6, ws=None):
    dev, nodes = scaled(x, I1, I6, ws)
    Rz = 1.0 / dev["M6"]["gm"]  # S1
    g, fu, pm = ac_metrics(dev, x["Cc"], Rz)
    sat = {n: dev[n]["VDS"] - dev[n]["VDSAT"] for n in dev}
    return {"dev": dev, "nodes": nodes, "Rz": Rz, "gain_db": g, "gbw": fu, "pm": pm, "sat_margin": sat,
            "power_W": VDD * (2 * I1 + I6)}


def solve_currents(x):
    """GBW >= 목표, PM >= 목표를 만족하는 최소 전류 (I1, I6) -- 손계산 순서:
    I1 은 gm1 = 2π·GBW·Cc 에서 출발, I6 은 PM 으로 이분."""
    I1 = 2 * math.pi * GBW_T * x["Cc"] / x["g1"]
    for _ in range(12):
        # I6 이분: PM >= 목표인 최소 I6
        lo, hi = 1e-7, 5e-3
        if evaluate(x, I1, hi)["pm"] < PM_T:
            return None
        for _ in range(30):
            m = math.sqrt(lo * hi)
            if evaluate(x, I1, m)["pm"] >= PM_T:
                hi = m
            else:
                lo = m
        I6 = hi
        r = evaluate(x, I1, I6)
        if not (r["gbw"] == r["gbw"]):
            return None
        ratio = GBW_T / r["gbw"]
        if 1.0 <= 1 / ratio <= 1.002:
            return I1, I6, r
        I1 *= ratio * 1.0005
    return I1, I6, r


if __name__ == "__main__":
    out = open(sys.argv[1], "a", encoding="utf-8")
    grid = {"g1": [14, 17, 20], "g3": [8, 11, 14], "g5": [8, 11], "L1": [0.5e-6, 1e-6, 1.5e-6],
            "L3": [0.5e-6, 1e-6, 1.5e-6], "L5": [0.5e-6, 1e-6], "Cc": [0.6e-12, 1e-12, 1.5e-12, 2e-12, 3e-12]}
    keys = list(grid)
    t0 = time.time()
    n = 0
    for vals in itertools.product(*[grid[k] for k in keys]):
        x = dict(zip(keys, vals))
        if x["g3"] > x["g1"]:
            continue  # 잡음 가드(부하 gm <= 입력 gm) 선행 조건
        try:
            s = solve_currents(x)
        except Exception as e:
            out.write(json.dumps({"x": x, "err": str(e)[:120]}) + "\n")
            continue
        n += 1
        if s is None:
            out.write(json.dumps({"x": x, "err": "pm_unreachable"}) + "\n")
            continue
        I1, I6, r = s
        rec = {"x": x, "I1": I1, "I6": I6, "gain_db": r["gain_db"], "gbw": r["gbw"], "pm": r["pm"],
               "power_uW": r["power_W"] * 1e6, "min_sat": min(r["sat_margin"].values()),
               "vcm": r["nodes"]["VCM"], "W": {k: v["W"] for k, v in r["dev"].items()}}
        out.write(json.dumps(rec) + "\n")
        out.flush()
    out.write(json.dumps({"done": n, "sec": time.time() - t0}) + "\n")
    out.close()
