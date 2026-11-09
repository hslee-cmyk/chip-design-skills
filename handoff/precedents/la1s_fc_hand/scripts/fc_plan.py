"""O-255 (1)-b floorplan 모델: 행별 공유 w_s · 정수 손가락 제약 · 행 손가락 열 · 닫힌 식 외곽 면적.

엔진이라면(규칙으로 섬):
  - 기하 묶음 = kind 별 행 하나(방안 B, 13회로·two_stage_ota 실측) -> 행 w_s 하나(LR8).
  - IDu 는 그 w_s 슬라이스에서 같은 (VGS, VDS, VS) 로 다시 읽고 W = I / IDu (DEC-105 (2)).
  - 정수 제약: 짝(같은 kind·gate·source 또는 차동쌍·캐스코드 짝 -- 연결로 판정) 같은 m, 모든 m 짝수(거울 반쪽),
    미러 비 정수: m(M11) = k11·m(MN), m(M3) = m(M4) = k3·m(MP) (사용자 기준 '미러 비 최우선').
  - 행 손가락 열 = fc_rows.best_row (공통 중심 거울 + Euler 끊김 최소).
  - 외곽 면적 닫힌 식 = gen_gds_fc 의 쌓기 식과 같은 꼴(행 길이 + gate 단 + S/D 버스 + riser + tap/ring).
고르는 순서(손 판단을 규칙으로): Euler 끊김 -> 외곽 면적 -> 최대 |W 오차|.
"""
import itertools, json, math, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts")
import lutlib as lt
import fc_design as FD
import fc_rows as FR

RULES = json.load(open("C:/Users/HSLEE/AppData/Local/Temp/la1s_fc_hand/layout/sky130_layout_rules.json", encoding="utf-8"))
U = {k: v[0] * 1e-6 for k, v in RULES["um"].items()}
SD = U["licon"] + 2 * U["licon_to_gate"]
SD_END = max(U["diff_ext_beyond_poly"], U["licon"] + U["licon_to_gate"] + U["diff_encl_licon"])
STRAP_W = U["via"] + 2 * U["m1_encl_via"]
BUS_PITCH = U["via"] + 2 * U["m2_encl_via"] + U["m2_space"]
LV_PITCH = max(U["li_width"] + U["li_space"], U["licon"] + U["licon_space"])
PL_GAP = max(U["polylicon_to_diff"], U["implant_encl_diff"] + U["polylicon_to_psdm"])
RISER_PITCH = STRAP_W + U["m1_space"]
TAP_H = U["licon"] + 2 * U["tap_encl_licon_adj"]
WMIN = 0.42e-6
PAIRS = [("M1", "M2"), ("M3", "M4"), ("M5", "M6"), ("M7", "M8"), ("M9", "M10")]


def even(x, lo=2):
    return max(lo, 2 * round(x / 2))


def plan_ws(R, ws, k11, k3):
    """ws: 소자별 손가락 폭(행마다 하나)."""
    x, b = R["x"], R["bias"]
    dev = FD.devices(x, R["I1"], b, ws)
    return _round(dev, ws, k11, k3)


def plan(R, ws_n, ws_p, k11, k3):
    x, b = R["x"], R["bias"]
    ws = {n: (ws_n if FD.NET[n]["kind"] == "nmos" else ws_p) for n in b}
    dev = FD.devices(x, R["I1"], b, ws)
    return _round(dev, ws, k11, k3)


def _round(dev, ws, k11, k3):
    ws_n = ws["MN"]
    ws_p = ws["MP"]
    Wt = {n: d["W"] for n, d in dev.items()}
    m = {}
    m["MN"] = even(Wt["MN"] / ws_n)
    m["M11"] = k11 * m["MN"]
    m["MP"] = even(Wt["MP"] / ws_p)
    m["M3"] = m["M4"] = k3 * m["MP"]
    for a, c in PAIRS:
        if a in m:
            continue
        mm = even(0.5 * (Wt[a] + Wt[c]) / ws[a])
        m[a] = m[c] = mm
    W = {n: m[n] * ws[n] for n in m}
    err = {n: W[n] / Wt[n] - 1 for n in m}
    return dev, ws, m, W, err


def topo_devices(ws, m, x):
    out = {}
    for n, d in FD.NET.items():
        out[n] = {"kind": d["kind"], "d": d["drain"], "g": d["gate"], "s": d["source"], "L": x["L"][n], "w_s": ws[n], "m": m[n]}
    return out


def rows_of(devs, part=None):
    """part: [(행 이름, kind, [소자])] -- 없으면 kind 별 행 하나."""
    rows = []
    if part is None:
        part = [("N", "nmos", [n for n in devs if devs[n]["kind"] == "nmos"]),
                ("P", "pmos", [n for n in devs if devs[n]["kind"] == "pmos"])]
    for rn, kind, names in part:
        half = {n: devs[n]["m"] // 2 for n in names}
        br = FR.best_row(names, half, devs)
        slots = [s[0] for s in br["seq"]]
        rows.append({"name": rn, "kind": kind, "slots": slots, "breaks": br["breaks"], "order": br["order"], "start": br["start"],
                     "seq": br["seq"]})
    return rows


def add_dummies(devs, rows):
    """행 양 끝에 더미 손가락(gate·바깥 S/D = 행 레일, 안쪽 S/D = 끝 넷) -- 거울 대칭 유지."""
    rail = {"nmos": "gnd", "pmos": "vdd"}
    for r in rows:
        seq = r["seq"]
        lnet = seq[0][1]
        rnet = seq[-1][2]
        Lr = max(devs[s[0]]["L"] for s in seq if s[0] != "GAP")
        ws = devs[seq[0][0]]["w_s"]
        for side, net in (("L", lnet), ("R", rnet)):
            nm = "DUM%s%s" % (r["name"], side)
            devs[nm] = {"kind": r["kind"], "d": net, "g": rail[r["kind"]], "s": rail[r["kind"]], "L": Lr, "w_s": ws, "m": 1,
                        "dummy": True}
        r["slots"] = ["DUM%sL" % r["name"]] + r["slots"] + ["DUM%sR" % r["name"]]
    return devs, rows


def finger_geom(devs, rows):
    """손가락별 ad/as/pd/ps: 가운데 S/D 칸(SD) 공유 = 반씩, 끝 칸(SD_END) 혼자. 끊김(GAP) 양쪽은 끝 칸."""
    for n in devs:
        devs[n]["finger_geom"] = []
    for r in rows:
        sl = r["slots"]
        for i, n in enumerate(sl):
            if n == "GAP":
                continue
            w = devs[n]["w_s"]
            fg = {}
            for side, j in (("l", i - 1), ("r", i + 1)):
                end = j < 0 or j >= len(sl) or sl[j] == "GAP"
                area = w * SD_END if end else w * SD / 2
                per = (w + 2 * SD_END) if end else SD
                fg[side] = (area, per)
            # 어느 쪽이 drain 인지는 행 열(seq) 방향으로 -- 더미는 왼쪽 = 끝 넷
            fgd = {"ad": fg["r"][0], "pd": fg["r"][1], "as": fg["l"][0], "ps": fg["l"][1]}
            devs[n]["finger_geom"].append(fgd)
    return devs


def outline(devs, rows, pins, ring=True):
    """gen_gds_fc 쌓기 식과 같은 닫힌 식(미터)."""
    lens, h = {}, 0.0
    h += TAP_H
    nets_all = {}
    first_p = True
    for r in rows:
        segs, cur = [], []
        for s in r["slots"]:
            if s == "GAP":
                segs.append(cur); cur = []
            else:
                cur.append(s)
        segs.append(cur)
        L = sum(2 * SD_END + sum(devs[n]["L"] for n in sg) + (len(sg) - 1) * SD for sg in segs) + (len(segs) - 1) * U["difftap_space"]
        lens[r["name"]] = L
        gnets = sorted({devs[n]["g"] for n in r["slots"] if n != "GAP"})
        sdn = sorted({devs[n][t] for n in r["slots"] if n != "GAP" for t in ("d", "s")})
        for nn in gnets + sdn:
            nets_all.setdefault(nn, set()).add(r["name"])
        if ring and r["kind"] == "pmos" and first_p:
            h += U["difftap_space"] + TAP_H + U["ptap_to_nwell"] + U["nwell_encl_ntap"] + TAP_H
            first_p = False
        h += U["poly_field_to_tap"] + U["li_space"] + len(gnets) * LV_PITCH + PL_GAP + U["poly_encl_polylicon_adj"] + devs[r["slots"][0]]["w_s"] + \
            U["poly_endcap"] + U["m2_space"] + len(sdn) * BUS_PITCH
    h += U["difftap_space"] + TAP_H
    width_rows = max(lens.values())
    risers = [n for n in nets_all if len(nets_all[n]) > 1 or n in pins]
    w = width_rows + (2 * (U["difftap_space"] + TAP_H) + U["nwell_encl_ntap"] if ring else U["difftap_space"]) + U["m1_space"] + len(risers) * RISER_PITCH
    empty = sum((width_rows - l) * devs[[s for s in rr["slots"] if s != "GAP"][0]]["w_s"] for l, rr in zip(lens.values(), rows))
    return {"w": w, "h": h, "area": w * h, "row_len": lens, "risers": risers, "row_empty_m2": empty}


if __name__ == "__main__":
    R = json.load(open(sys.argv[1], encoding="utf-8"))
    k11, k3 = int(sys.argv[2]), int(sys.argv[3])
    pins = ["vdd", "gnd", "vin_n", "vin_p", "out", "vb1", "vb2", "bias3"]
    wn = [w for w in lt.slice_widths("nmos") if w >= WMIN - 1e-12]
    wp = [w for w in lt.slice_widths("pmos") if w >= WMIN - 1e-12]
    res = []
    for a, c in itertools.product(wn, wp):
        try:
            dev, ws, m, W, err = plan(R, a, c, k11, k3)
        except ValueError:
            continue
        devs = topo_devices(ws, m, R["x"])
        rows = rows_of(devs)
        devs, rows = add_dummies(devs, rows)
        o = outline(devs, rows, pins)
        res.append({"ws_n": a, "ws_p": c, "m": m, "W_err_max": max(abs(v) for v in err.values()), "err": err,
                    "breaks": sum(r["breaks"] for r in rows), "area": o["area"], "wh": [o["w"], o["h"]],
                    "row_len": o["row_len"], "fingers": sum(m.values()), "empty": o["row_empty_m2"]})
    # 물리 먼저: W 오차는 같은 전류에서 VGS(동작점)를 옮긴다 -> 끊김 다음에 W 오차, 그다음 면적
    res.sort(key=lambda r: (r["breaks"], round(r["W_err_max"], 2), round(r["area"] * 1e12, 0)))
    with open(sys.argv[4], "w", encoding="utf-8") as f:
        f.write("후보 %d (k11 %d, k3 %d), 상위 10: 끊김 -> 최대 |W 오차|(0.01) -> 외곽 면적\n" % (len(res), k11, k3))
        for r in res[:10]:
            f.write(json.dumps({"ws_um": [round(r["ws_n"] * 1e6, 3), round(r["ws_p"] * 1e6, 3)], "breaks": r["breaks"],
                                "area_um2": round(r["area"] * 1e12, 1), "wh_um": [round(v * 1e6, 2) for v in r["wh"]],
                                "row_len_um": {k: round(v * 1e6, 2) for k, v in r["row_len"].items()},
                                "W_err_max": round(r["W_err_max"], 3), "m": r["m"], "fingers": r["fingers"]}, ensure_ascii=False) + "\n")
    json.dump(res[:10], open(sys.argv[5], "w", encoding="utf-8"))
