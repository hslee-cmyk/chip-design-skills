"""고른 floorplan 후보로 레이아웃 입력(design_for_layout)과 SPICE 시험대 값을 만든다.

usage: fc_build.py <design.json> <plan2.json> <part> <ws_json> <k11> <k3> <out_design_for_layout.json>
  ws_json: 예 '{"Nin":1.0e-6,"Ncm":0.84e-6,"P":0.42e-6}' -- 행별 w_s(후보 표에서 고른 것)
"""
import json, sys
import fc_design as FD
import fc_plan as FP
import fc_plan2_parts as PP

R = json.load(open(sys.argv[1], encoding="utf-8"))
part = PP.PART[sys.argv[3]]
wsr = json.loads(sys.argv[4])
k11, k3 = int(sys.argv[5]), int(sys.argv[6])
ws = {}
for rn, k, names in part:
    for n in names:
        ws[n] = wsr[rn]
dev, ws2, m, W, err = FP.plan_ws(R, ws, k11, k3)
devs = FP.topo_devices(ws, m, R["x"])
rows = FP.rows_of(devs, part)
devs, rows = FP.add_dummies(devs, rows)
devs = FP.finger_geom(devs, rows)
o = FP.outline(devs, rows, ["vdd", "gnd", "vin_n", "vin_p", "out", "vb1", "vb2", "bias3"])
I11 = 2 * R["I1"]
sim = {"vdd": FD.VDD, "CL": FD.CL, "vcm": R["vcm"], "bias3": R["nodes"]["bias3"], "iref": I11 / k11, "k11": k11, "k3": k3}
out = {"devices": {n: {k: v for k, v in d.items()} for n, d in devs.items()},
       "rows": [{"name": r["name"], "kind": r["kind"], "slots": r["slots"], "breaks": r["breaks"], "order": r["order"]} for r in rows],
       "stack": [r["name"] for r in rows], "sim": sim, "W_target": {n: dev[n]["W"] for n in dev}, "W_err": err,
       "outline_model": o, "part": sys.argv[3], "ws_row": wsr}
json.dump(out, open(sys.argv[7], "w", encoding="utf-8"), indent=1)
print("rows", [(r["name"], len(r["slots"]), r["breaks"]) for r in rows], "outline_um", round(o["w"] * 1e6, 2), round(o["h"] * 1e6, 2),
      "area_um2", round(o["area"] * 1e12, 1))
