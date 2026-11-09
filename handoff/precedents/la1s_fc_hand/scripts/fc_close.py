"""O-255 (2) SPICE 닫기: 손잡이 = Iref(전류 크기 -> GBW), bias3(접힘 마디 X -> M3·M5 여유 균형), VCM(tail·out ->
M11·M6/M8 여유 균형). W·손가락은 고정(floorplan 기하). 멈춤 = GBW 진전이 측정 분해능(ac dec 100 의 한 칸) 이하이고
여유 균형 이동 < 1 mV, 또는 반복 상한.
usage: fc_close.py <design_for_layout.json> <tag> <gbw_target_hz> <maxit>
"""
import json, math, sys
import fc_spice as SP

des = json.load(open(sys.argv[1], encoding="utf-8"))
tag, gt, maxit = sys.argv[2], float(sys.argv[3]), int(sys.argv[4])
sim = dict(des["sim"])
res_dec = 10 ** (1 / 100) - 1  # ac dec 100 한 칸의 상대 분해능
hist = []
prev = None
log = open("../out/close_%s.txt" % tag, "a", encoding="utf-8")
extra = None
if len(sys.argv) > 5:
    # 레이아웃 뒤 닫기: 추출 기하로 바꾼 design 과 배선 기생(cnet·rser)을 그대로 쓴다
    ex = json.load(open(sys.argv[5], encoding="utf-8"))
    extra = {"cnet": {k: v * 1e-15 for k, v in ex["cnet_fF"].items()}, "rser": ex["rser_ohm"]}
for it in range(maxit):
    r = SP.run(SP.netlist(des, sim, extra), "../out/spice", "%s_%d" % (tag, it))
    mar = SP.sat_margins(r, des)
    fu = r["fu"]
    log.write("it %d iref %.6g bias3 %.5f vcm %.5f | GBW %.4f MHz PM %.2f A0 %.2f | m3 %.4f m4 %.4f m5 %.4f m11 %.4f m6 %.4f m8 %.4f | P %.2f uW\n" % (
        it, sim["iref"], sim["bias3"], sim["vcm"], fu / 1e6, r["pm"], r["a0db"], mar["M3"], mar["M4"], mar["M5"], mar["M11"], mar["M6"], mar["M8"],
        r["power_W"] * 1e6))
    log.flush()
    hist.append((sim["iref"], fu))
    # 여유 균형: X 를 올리면(bias3 내림) M5 여유 증가, M3 여유 감소
    d_b3 = 0.5 * (min(mar["M5"], mar["M6"]) - min(mar["M3"], mar["M4"]))
    d_vcm = 0.5 * (min(mar["M6"], mar["M8"]) - mar["M11"])
    # GBW secant(ln Iref -> ln fu)
    if len(hist) >= 2 and abs(math.log(hist[-1][0] / hist[-2][0])) > 1e-9:
        s = math.log(hist[-1][1] / hist[-2][1]) / math.log(hist[-1][0] / hist[-2][0])
    else:
        s = 1.0
    target = gt * (1 + res_dec)  # 측정 분해능 한 칸 위로 -- 통과 쪽
    d_ln = math.log(target / fu) / max(s, 0.2)
    done = abs(math.log(target / fu)) <= res_dec and abs(d_b3) < 1e-3 and abs(d_vcm) < 1e-3 and fu >= gt
    if done:
        break
    sim["iref"] *= math.exp(d_ln)
    sim["bias3"] -= d_b3
    sim["vcm"] += d_vcm
log.write("end it %d\n" % it)
des["sim"] = sim
json.dump(des, open("../out/dfl_%s_closed.json" % tag, "w", encoding="utf-8"), indent=1)
json.dump({"sim": sim, "spice": r, "margins": mar}, open("../out/spice/%s_closed.json" % tag, "w", encoding="utf-8"), indent=1)
