"""고른 손가락 계획으로 (1) 레이아웃 생성 (2) 슬라이스 반영 손계산 재평가 (3) ngspice 1회 -- 결과를 파일에 쓴다.

argv: hand_point.json  choice.json  out_dir
choice.json = {"opt": "A"|"B", "w_s": {dev: m}, "m": {dev: int}, "I1": A, "I6": A}
"""
import json, os, subprocess, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/layout")
import design as D
import fingerplan as F
import gen_layout as G
import spice_gen as S

hand = json.load(open(sys.argv[1], encoding="utf-8"))
ch = json.load(open(sys.argv[2], encoding="utf-8"))
od = sys.argv[3]
os.makedirs(od, exist_ok=True)
w_s, m = ch["w_s"], ch["m"]
p = {"m": m}
R, box, des = (F.layout_B if ch["opt"] == "B" else F.layout_A)(w_s, p)
for n in des["devices"]:
    des["devices"][n]["m"] = m[n]
json.dump(des, open(os.path.join(od, "design_for_layout.json"), "w", encoding="utf-8"), indent=1)
if ch["opt"] == "B":
    # 생성 스크립트를 실제 경로로 다시 돌려(결정성 확인 겸) geometry·svg 를 만든다
    subprocess.run([sys.executable, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/layout/gen_layout.py",
                    os.path.join(od, "design_for_layout.json"), os.path.join(od, "geometry.json"), os.path.join(od, "layout.svg")], check=True)
    geom = json.load(open(os.path.join(od, "geometry.json"), encoding="utf-8"))
else:
    geom = {"devices": G.per_device_geom(R, des["devices"]), "box": box,
            "rows": [{"name": r["name"], "length": r["length"], "w_s": r["w_s"], "breaks": r["breaks"],
                      "symmetric": G.symmetry(r)[0], "sequence": [f["dev"] for f in r["fingers"]]} for r in R]}
    json.dump(geom, open(os.path.join(od, "geometry.json"), "w", encoding="utf-8"), indent=1)
# 손계산 재평가(슬라이스 반영, gm/ID 고정, 전류 = 손가락 계획 전류)
x = dict(ch.get("x", hand["x"]))  # 되먹임 루프가 다시 푼 Cc 포함
r = D.evaluate(x, ch["I1"], ch["I6"], w_s)
re = {"gain_db": r["gain_db"], "gbw_hz": r["gbw"], "pm_deg": r["pm"], "power_uW": r["power_W"] * 1e6, "Rz": r["Rz"],
      "nodes": r["nodes"], "sat_margin": r["sat_margin"],
      "W_hand_vs_real": {n: [r["dev"][n]["W"], m[n] * w_s[n]] for n in m}}
json.dump(re, open(os.path.join(od, "hand_reeval.json"), "w", encoding="utf-8"), indent=1)
# SPICE
for n in des["devices"]:
    des["devices"][n]["L"] = hand["dev"][n]["L"]
I5 = 2 * ch["I1"]
sim = {"vdd": D.VDD, "CL": D.CL, "Cc": x["Cc"], "Rz": r["Rz"], "vcm": r["nodes"]["VCM"], "iref": I5 / m["M5"], "ov": G.OV}
net = S.netlist(des, geom, sim)
out = S.run(net, od, "tso")
res = S.parse(out)
json.dump(res, open(os.path.join(od, "spice.json"), "w", encoding="utf-8"), indent=1)
# 둘째 시험대: bias = 손계산 VGS5 이상 전압원(기준 다이오드 VDS 차가 만든 미러 오차를 빼고 손계산만 대조)
sim2 = dict(sim, vbias=r["dev"]["M5"]["VGS"])
out2 = S.run(S.netlist(des, geom, sim2), od, "tso_vbias")
json.dump(S.parse(out2) | {"vbias": sim2["vbias"]}, open(os.path.join(od, "spice_vbias.json"), "w", encoding="utf-8"), indent=1)
