"""손가락·행 결정(사용자 기준 O-251~O-254) -- 방안 A(stage별 행 → 통합)와 B(전체 행)를 슬라이스 폭 후보마다 따져 본다.

순서(사용자 기준):
  1. 미러 비 우선: 같은 gate·source 넷·같은 kind 쌍(연결로 판정)의 손가락 비 = 전류 비(정수). 차동쌍(같은 source 넷,
     신호 gate)은 같은 손가락 수.
  2. Euler 기하 묶음: 방안 A = 같은 stage(채널 연결 성분) ∩ 같은 kind, 방안 B = 같은 kind 전체.
  3. 행 안 손가락 폭 하나(LR8), 행 길이 = Σ m(L + overhead) + 더미, P/N 가로 맞춤 → 빈 면적.
  4. 대칭(가운데 축 거울 같음, 차동쌍·미러쌍 1D common-centroid), Euler 끊김.
전류를 정하는 소자는 tail(M5): I5 = m5·w_s·IDu5(같은 bias VGS) -- 나머지 소자 전류는 KCL 로 따라온다.
"""
import itertools, json, math, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/layout")
import lutlib as lt
import design as D
import gen_layout as G

HAND = json.load(open(sys.argv[1], encoding="utf-8"))
TOPO = json.load(open("C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library/two_stage_ota.topology.json", encoding="utf-8"))
NET = {d["name"]: d for d in TOPO["netlist"]}
RAILS = set(TOPO["supply_nets"])
WMIN = G.pdklib.quantities(["min_finger_w_m"])["min_finger_w_m"]


def ccc():
    """채널 연결 성분(레일 제외 drain/source 넷으로 이어진 소자 묶음) -- stage 근사(기하 묶음 키 후보)."""
    parent = {n: n for n in NET}
    def f(a):
        while parent[a] != a:
            a = parent[a]
        return a
    by_net = {}
    for n, d in NET.items():
        for t in ("drain", "source"):
            if d[t] not in RAILS:
                by_net.setdefault(d[t], []).append(n)
    for ns in by_net.values():
        for a in ns[1:]:
            parent[f(a)] = f(ns[0])
    groups = {}
    for n in NET:
        groups.setdefault(f(n), []).append(n)
    return sorted(sorted(g) for g in groups.values())


def mirrors():
    """같은 kind·같은 gate 넷·같은 source 넷 쌍(연결만)."""
    out = []
    names = sorted(NET)
    for a, b in itertools.combinations(names, 2):
        da, db = NET[a], NET[b]
        if da["kind"] == db["kind"] and da["gate"] == db["gate"] and da["source"] == db["source"]:
            out.append((a, b))
    return out


_idu = {}


def idu(n, w_s):
    """설계 gm/ID 를 그 슬라이스(bin)에서 유지할 때의 IDu -- 슬라이스가 바뀌면 같은 gm/ID 의 VGS·IDu 가 바뀐다(DEC-105 (2))."""
    key = (n, round(w_s * 1e10))
    if key not in _idu:
        p = HAND["dev"][n]
        g = p["gm"] / p["ID"]
        v = lt.vgs_for_gmid(p["kind"], w_s, p["L"], g, p["VDS"], p["VS"])
        _idu[key] = lt.dc(p["kind"], w_s, p["L"], v, p["VDS"], p["VS"])["IDu"]
    return _idu[key]


def even_round(x, lo=2):
    return max(lo, 2 * round(x / 2))


def plan(w_s):
    """w_s: 소자별 손가락 폭. 반환: 손가락 수·실현 W·전류·W 오차."""
    I6_need = HAND["I6"]
    I5_t = 2 * HAND["I1"]
    # 홀짝 규칙(대칭 + Euler 연속, 손 배치에서 유도 -- 문서 §3.2):
    #   가운데 tail 은 양쪽 반(짝수), 차동쌍·미러쌍은 ABBA 두 반이 각각 짝수(4의 배수), 양 끝 큰 소자는 짝수.
    m5 = even_round(I5_t / (w_s["M5"] * idu("M5", w_s["M5"])), 2)
    I5 = m5 * w_s["M5"] * idu("M5", w_s["M5"])
    # 미러 비 우선: M7/M5 손가락 비 = 정수 n, 같은 w_s(아래 호출부가 강제). I7 은 M7 자기 VDS 의 IDu 로 -- PM 필요 전류 이상인 최소 n.
    i7_per = w_s["M7"] * idu("M7", w_s["M7"])
    n_ratio = max(1, math.ceil(I6_need / (m5 * i7_per)))
    m7 = n_ratio * m5
    I7 = m7 * i7_per
    I1 = I5 / 2
    I6 = I7
    m = {"M5": m5, "M7": m7}
    for n, I in (("M1", I1), ("M2", I1), ("M3", I1), ("M4", I1)):
        m[n] = max(4, 4 * round(I / (w_s[n] * idu(n, w_s[n])) / 4))
    m["M6"] = even_round(I6 / (w_s["M6"] * idu("M6", w_s["M6"])))
    W = {n: m[n] * w_s[n] for n in m}
    Wt = {"M1": I1 / idu("M1", w_s["M1"]), "M2": I1 / idu("M2", w_s["M2"]), "M3": I1 / idu("M3", w_s["M3"]),
          "M4": I1 / idu("M4", w_s["M4"]), "M5": I5 / idu("M5", w_s["M5"]), "M6": I6 / idu("M6", w_s["M6"]),
          "M7": I7 / idu("M7", w_s["M7"])}
    err = {n: W[n] / Wt[n] - 1 for n in W}
    return {"m": m, "W": W, "W_target": Wt, "W_err": err, "I1": I1, "I6": I6, "I5": I5, "n_ratio": n_ratio}


def half(n, k):
    return [n] * k


def rows_B(p):
    m = p["m"]
    h5 = m["M5"] // 2 if m["M5"] % 2 == 0 else None
    # N 행: M7 | M5 | M1 M2 | M2 M1 | M5 | M7   (m5 홀수면 M5 가운데 하나)
    nslots = half("M7", m["M7"] // 2)
    if h5 is None:
        mid = half("M1", m["M1"] // 2) + half("M2", m["M2"] // 2) + ["M5"] * m["M5"] + half("M2", m["M2"] // 2) + half("M1", m["M1"] // 2)
        nslots += mid
    else:
        nslots += half("M5", h5) + half("M1", m["M1"] // 2) + half("M2", m["M2"] // 2) + half("M2", m["M2"] // 2) + half("M1", m["M1"] // 2) + half("M5", h5)
    nslots += half("M7", m["M7"] - m["M7"] // 2)
    pslots = half("M6", m["M6"] // 2) + half("M3", m["M3"] // 2) + half("M4", m["M4"] // 2) + half("M4", m["M4"] // 2) + half("M3", m["M3"] // 2) + half("M6", m["M6"] - m["M6"] // 2)
    return [{"name": "N", "kind": "nmos", "slots": nslots, "pairs": {}}, {"name": "P", "kind": "pmos", "slots": pslots, "pairs": {}}], ["N", "P"]


def rows_A(p):
    m = p["m"]
    rB, _ = rows_B(p)
    n1 = [s for s in rB[0]["slots"] if s != "M7"]
    p1 = [s for s in rB[1]["slots"] if s != "M6"]
    return [{"name": "S1N", "kind": "nmos", "slots": n1, "pairs": {}}, {"name": "S1P", "kind": "pmos", "slots": p1, "pairs": {}},
            {"name": "S2N", "kind": "nmos", "slots": ["M7"] * m["M7"], "pairs": {}}, {"name": "S2P", "kind": "pmos", "slots": ["M6"] * m["M6"], "pairs": {}}]


def devices(w_s):
    out = {}
    for n, d in NET.items():
        out[n] = {"kind": d["kind"], "d": d["drain"], "g": d["gate"], "s": d["source"], "L": HAND["dev"][n]["L"], "w_s": w_s[n]}
    return out


def layout_B(w_s, p):
    rows, stack = rows_B(p)
    des = {"devices": devices(w_s), "rows": rows, "stack": stack}
    R = G.build(des)
    box = G.stack(R, des)
    return R, box, des


def layout_A(w_s, p):
    """stage 블록(각각 P 행 위 N 행)을 좌우로 놓는다: S2 반 | S1 | S2 반 이 아니라 S1 | S2 (stage 블록 단위)."""
    rows = rows_A(p)
    des = {"devices": devices(w_s), "rows": rows, "stack": []}
    R = {r["name"]: r for r in G.build(des)}
    Q = G.Q
    def block_h(nr, pr):
        return Q["tap_w_m"] + nr["w_s"] + Q["well_spacing_m"] + pr["w_s"] + Q["tap_w_m"]
    b1w = max(R["S1N"]["length"], R["S1P"]["length"])
    b2w = max(R["S2N"]["length"], R["S2P"]["length"])
    h1 = block_h(R["S1N"], R["S1P"])
    h2 = block_h(R["S2N"], R["S2P"])
    box_w = b1w + Q["well_spacing_m"] + b2w
    box_h = max(h1, h2)
    rows_area = sum(r["length"] * r["w_s"] for r in R.values())
    empty = (b1w - R["S1N"]["length"]) * R["S1N"]["w_s"] + (b1w - R["S1P"]["length"]) * R["S1P"]["w_s"] + \
            (b2w - R["S2N"]["length"]) * R["S2N"]["w_s"] + (b2w - R["S2P"]["length"]) * R["S2P"]["w_s"] + \
            abs(h1 - h2) * (b1w if h1 < h2 else b2w)
    return list(R.values()), {"box_w": box_w, "box_h": box_h, "box_area": box_w * box_h, "row_area": rows_area,
                              "row_empty_area": empty, "row_empty_ratio": empty / (box_w * box_h)}, des


def score(R, box):
    sym = all(G.symmetry(r)[0] for r in R)
    brk = sum(r["breaks"] for r in R)
    return sym, brk


if __name__ == "__main__":
    out = open(sys.argv[2], "w", encoding="utf-8")
    out.write("ccc(stage 근사) %s\nmirrors(연결) %s\nW_min %.3g\n" % (ccc(), mirrors(), WMIN))
    wn = [w for w in lt.slice_widths("nmos") if w >= WMIN - 1e-12]
    wp = [w for w in lt.slice_widths("pmos") if w >= WMIN - 1e-12]
    res = []
    # 방안 B: 행 = kind 전체 -> N 행 w_s 하나, P 행 w_s 하나
    for a, b in itertools.product(wn, wp):
        w_s = {"M1": a, "M2": a, "M5": a, "M7": a, "M3": b, "M4": b, "M6": b}
        p = plan(w_s)
        R, box, des = layout_B(w_s, p)
        sym, brk = score(R, box)
        res.append(("B", w_s, p, box, sym, brk, [(r["name"], r["length"]) for r in R]))
    # 방안 A: stage 별 행 -> S1N, S1P, S2N, S2P 각각 w_s
    # 미러 비 우선: M5·M7 미러 쌍은 stage 가 달라도 같은 w_s(사용자 기준 1이 stage 묶음보다 앞) -- S2N w_s = S1N w_s
    for a1, b1, b2 in itertools.product(wn, wp, wp):
        a2 = a1
        w_s = {"M1": a1, "M2": a1, "M5": a1, "M3": b1, "M4": b1, "M7": a2, "M6": b2}
        p = plan(w_s)
        R, box, des = layout_A(w_s, p)
        sym, brk = score(R, box)
        res.append(("A", w_s, p, box, sym, brk, [(r["name"], r["length"]) for r in R]))
    def maxerr(p):
        return max(abs(v) for v in p["W_err"].values())
    VDD = D.VDD
    for r in res:
        r[2]["power_uW"] = VDD * (2 * r[2]["I1"] + r[2]["I6"]) * 1e6
    for opt in ("A", "B"):
        cand = [r for r in res if r[0] == opt]
        # 순서: Euler 끊김 → 대칭 → 전력(회로 목적) → 빈 면적 → box 면적
        cand.sort(key=lambda r: (r[5], not r[4], round(r[2]["power_uW"], 1), round(r[3]["row_empty_ratio"], 3), r[3]["box_area"]))
        out.write("\n== 방안 %s: 후보 %d, 상위 8 (끊김, 대칭, 전력, 빈 면적, box 순)\n" % (opt, len(cand)))
        for r in cand[:8]:
            out.write(json.dumps({"w_s_um": {k: round(v * 1e6, 3) for k, v in r[1].items()}, "m": r[2]["m"],
                                  "n_ratio": r[2]["n_ratio"], "I1_uA": round(r[2]["I1"] * 1e6, 3), "I6_uA": round(r[2]["I6"] * 1e6, 2),
                                  "W_err_max": round(maxerr(r[2]), 3), "power_uW": round(r[2]["power_uW"], 1), "box_um2": round(r[3]["box_area"] * 1e12, 1),
                                  "box_wh_um": [round(r[3]["box_w"] * 1e6, 2), round(r[3]["box_h"] * 1e6, 2)],
                                  "empty_ratio": round(r[3]["row_empty_ratio"], 3), "sym": r[4], "breaks": r[5],
                                  "rows_um": [(n, round(l * 1e6, 2)) for n, l in r[6]]}, ensure_ascii=False) + "\n")
    json.dump([{"opt": r[0], "w_s": r[1], "m": r[2]["m"], "I1": r[2]["I1"], "I6": r[2]["I6"], "W_err": r[2]["W_err"],
                "box": r[3], "sym": r[4], "breaks": r[5]} for r in res], open(sys.argv[3], "w", encoding="utf-8"))
    out.close()
