"""행 분할(행 접기) 후보별 floorplan 모델 -- 행마다 w_s 하나를 고른다(LR8 은 물리 행 단위).

분할 후보(연결에서 읽은 묶음, 회로 이름 규칙 아님 -- 소자 집합은 이 회로의 연결로 정한 것):
  B1: kind 별 행 하나.
  B2: nmos 를 채널 연결 성분 둘(입력쌍+tail+기준 다이오드 / 캐스코드 미러)로, pmos 는 하나.
  B3: B2 + pmos 도 전류원(+기준) / 캐스코드로.
고르는 순서: Euler 끊김 -> 최대 |W 오차|(0.01 단위) -> 외곽 면적. 결과마다 행 길이 균형(빈 면적)도 적는다.
usage: fc_plan2.py <design.json> <k11> <k3> <out.txt> <out.json>
"""
import itertools, json, sys
import lutlib as lt
import fc_design as FD
import fc_plan as FP

PART = {
    "B1": [("N", "nmos", ["M1", "M2", "M11", "MN", "M7", "M8", "M9", "M10"]), ("P", "pmos", ["M3", "M4", "MP", "M5", "M6"])],
    "B2": [("Nin", "nmos", ["M1", "M2", "M11", "MN"]), ("Ncm", "nmos", ["M7", "M8", "M9", "M10"]),
           ("P", "pmos", ["M3", "M4", "MP", "M5", "M6"])],
    "B3": [("Nin", "nmos", ["M1", "M2", "M11", "MN"]), ("Ncm", "nmos", ["M7", "M8", "M9", "M10"]),
           ("Pcs", "pmos", ["M3", "M4", "MP"]), ("Pcc", "pmos", ["M5", "M6"])],
}
PINS = ["vdd", "gnd", "vin_n", "vin_p", "out", "vb1", "vb2", "bias3"]

R = json.load(open(sys.argv[1], encoding="utf-8"))
k11, k3 = int(sys.argv[2]), int(sys.argv[3])
wsl = {k: [w for w in lt.slice_widths(k) if w >= FP.WMIN - 1e-12] for k in ("nmos", "pmos")}
res = []
for pn, part in PART.items():
    for combo in itertools.product(*[wsl[k] for _, k, _ in part]):
        ws = {}
        for (rn, k, names), w in zip(part, combo):
            for n in names:
                ws[n] = w
        try:
            dev, ws2, m, W, err = FP.plan_ws(R, ws, k11, k3)
        except ValueError:
            continue
        devs = FP.topo_devices(ws, m, R["x"])
        rows = FP.rows_of(devs, part)
        devs, rows = FP.add_dummies(devs, rows)
        o = FP.outline(devs, rows, PINS)
        res.append({"part": pn, "ws": {rn: w for (rn, _, _), w in zip(part, combo)}, "m": m, "err": err,
                    "W_err_max": max(abs(v) for v in err.values()), "breaks": sum(r["breaks"] for r in rows),
                    "area": o["area"], "wh": [o["w"], o["h"]], "row_len": o["row_len"], "empty": o["row_empty_m2"]})
res.sort(key=lambda r: (r["breaks"], round(r["W_err_max"], 2), round(r["area"] * 1e12, 0)))
with open(sys.argv[4], "w", encoding="utf-8") as f:
    f.write("후보 %d (k11 %d, k3 %d)\n" % (len(res), k11, k3))
    for pn in PART:
        cand = [r for r in res if r["part"] == pn]
        f.write("== %s 상위 4\n" % pn)
        for r in cand[:4]:
            worst = max(r["err"], key=lambda n: abs(r["err"][n]))
            f.write(json.dumps({"ws_um": {k: round(v * 1e6, 3) for k, v in r["ws"].items()}, "breaks": r["breaks"],
                                "W_err_max": round(r["W_err_max"], 3), "worst": worst, "area_um2": round(r["area"] * 1e12, 1),
                                "wh_um": [round(v * 1e6, 2) for v in r["wh"]], "row_len_um": {k: round(v * 1e6, 2) for k, v in r["row_len"].items()},
                                "empty_um2": round(r["empty"] * 1e12, 1), "m": r["m"]}, ensure_ascii=False) + "\n")
json.dump(res[:40], open(sys.argv[5], "w", encoding="utf-8"))
