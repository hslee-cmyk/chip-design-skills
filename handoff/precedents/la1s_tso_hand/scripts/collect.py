"""최종 점 표 모으기(문서용). argv: point_hand.json run_dir final_k out.md"""
import json, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts")
import design as D
hp = json.load(open(sys.argv[1], encoding="utf-8"))
rd, k = sys.argv[2], sys.argv[3]
ch = json.load(open("%s/choice_%s.json" % (rd, k), encoding="utf-8"))
fd = "%s/final_%s" % (rd, k)
he = json.load(open(fd + "/hand_reeval.json", encoding="utf-8"))
sv = json.load(open(fd + "/spice_vbias.json", encoding="utf-8"))
si = json.load(open(fd + "/spice.json", encoding="utf-8"))
ge = json.load(open(fd + "/geometry.json", encoding="utf-8"))
gu = json.load(open(fd + "/guards.json", encoding="utf-8"))
des = json.load(open(fd + "/design_for_layout.json", encoding="utf-8"))
r = D.evaluate(ch["x"], ch["I1"], ch["I6"], ch["w_s"])
L = []
L.append("| 소자 | kind | L [µm] | w_s [µm] | m | W 실현 [µm] | gm/ID (손) | ID 손 [µA] | ID SPICE [µA] | VDS−VDSAT SPICE [V] |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for n in ["M1", "M2", "M3", "M4", "M5", "M6", "M7"]:
    d = des["devices"][n]
    p = r["dev"][n]
    s = sv["dev"][n]
    L.append("| %s | %s | %.3g | %.3g | %d | %.3f | %.2f | %.3f | %.3f | %.3f |" % (
        n, d["kind"], d["L"] * 1e6, d["w_s"] * 1e6, d["m"], d["m"] * d["w_s"] * 1e6, p["gm"] / p["ID"], p["ID"] * 1e6,
        s["id"] * d["m"] * 1e6, s["vds"] - s["vdsat"]))
L.append("")
L.append("| 양 | 손계산(슬라이스 반영) | SPICE (bias = 이상 전압원) | SPICE (bias = 기준 다이오드 + Iref) | spec |")
L.append("|---|---|---|---|---|")
L.append("| gain [dB] | %.2f | %.2f | %.2f | ≥ %g |" % (r["gain_db"], sv["a0db"], si["a0db"], D.GAIN_T))
L.append("| GBW [MHz] | %.4f | %.5f | %.4f | ≥ %g |" % (r["gbw"] / 1e6, sv["fu"] / 1e6, si["fu"] / 1e6, D.GBW_T / 1e6))
L.append("| PM [deg] | %.2f | %.2f | %.2f | ≥ %g |" % (r["pm"], sv["pm"], si["pm"], D.PM_T))
L.append("| 전원 전류 [µA] (전력 [µW]) | %.2f (%.1f) | %.2f (%.1f) | %.2f (%.1f, Iref 포함) | 최소화 |" % (
    2 * ch["I1"] * 1e6 + ch["I6"] * 1e6, r["power_W"] * 1e6, -sv["i(vdd)"] * 1e6, -sv["i(vdd)"] * 1.8e6, -si["i(vdd)"] * 1e6, -si["i(vdd)"] * 1.8e6))
L.append("| v(OUT) / v(CS) / v(O1) [V] | %.3f / %.3f / %.3f | %.3f / %.3f / %.3f | %.3f / %.3f / %.3f | -- |" % (
    r["nodes"]["OUT"], r["nodes"]["CS"], r["nodes"]["O1"], sv["v(out)"], sv["v(cs)"], sv["v(o1)"], si["v(out)"], si["v(cs)"], si["v(o1)"]))
L.append("| offset_excess (SPICE gm + Pelgrom) | -- | %.3f | -- | ≤ √2 = 1.414 |" % gu["offset_excess"])
L.append("| noise_excess_th (1 + gm3/gm1) | -- | %.3f | -- | ≤ 2 |" % gu["noise_excess_th"])
L.append("")
L.append("Cc = %.4f pF, Rz = %.0f Ω, VCM = %.4f V, I1 = %.3f µA, I6 = %.2f µA" % (ch["x"]["Cc"] * 1e12, r["Rz"], r["nodes"]["VCM"], ch["I1"] * 1e6, ch["I6"] * 1e6))
b = ge["box"]
L.append("box %.2f × %.2f µm = %.1f µm², 행 빈 면적 비 %.3f; 행: %s" % (b["box_w"] * 1e6, b["box_h"] * 1e6, b["box_area"] * 1e12, b["row_empty_ratio"],
         "; ".join("%s 길이 %.2f µm w_s %.2f µm 끊김 %d 대칭 %s 순서 %s" % (x["name"], x["length"] * 1e6, x["w_s"] * 1e6, x["breaks"], x["symmetric"], "".join(
             {"M1": "1", "M2": "2", "M3": "3", "M4": "4", "M5": "5", "M6": "6", "M7": "7", "DUMMY": "d"}[s] for s in x["sequence"])) for x in ge["rows"])))
L.append("MIM Cc 면적 %.0f µm² (PDK MIM 밀도 선언)" % (ch["x"]["Cc"] / 2e-3 * 1e12))
open(sys.argv[4], "w", encoding="utf-8").write("\n".join(L) + "\n")
