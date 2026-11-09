"""손설계점 하나를 끝까지: 손가락 계획(B 최상위) → 되먹임 루프 → 레이아웃·SPICE → E-1 닫기(최대 4회, 진전 ≤ 측정 분해능이면 멈춤) → 가드.
argv: hand_point.json out_dir"""
import json, os, subprocess, sys
PY = sys.executable
S = "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/scripts/"
hp, od = sys.argv[1], sys.argv[2]
os.makedirs(od, exist_ok=True)
def run(*a):
    subprocess.run([PY] + list(a), check=True, cwd=S)
run(S + "fingerplan.py", hp, od + "/fingerplan.txt", od + "/fingerplan.json")
res = json.load(open(od + "/fingerplan.json", encoding="utf-8"))
B = [r for r in res if r["opt"] == "B"]
VDD = 1.8
B.sort(key=lambda r: (r["breaks"], not r["sym"], round(VDD * (2 * r["I1"] + r["I6"]) * 1e6, 1), round(r["box"]["row_empty_ratio"], 3), r["box"]["box_area"]))
w_s = B[0]["w_s"]
run(S + "loop.py", hp, json.dumps(w_s), od + "/choice_0.json")
log = []
prev = None
for k in range(5):
    run(S + "final.py", hp, od + "/choice_%d.json" % k, od + "/final_%d" % k)
    sp = json.load(open(od + "/final_%d/spice_vbias.json" % k, encoding="utf-8"))
    log.append({"k": k, "fu": sp["fu"], "pm": sp.get("pm"), "a0db": sp["a0db"]})
    if sp["fu"] >= 7e6 or (prev is not None and abs(sp["fu"] - prev) <= 1e-4 * 7e6):
        break
    prev = sp["fu"]
    run(S + "close_e1.py", od + "/choice_%d.json" % k, od + "/final_%d/spice_vbias.json" % k, od + "/choice_%d.json" % (k + 1))
run(S + "check_offset.py", od + "/final_%d/design_for_layout.json" % k, od + "/final_%d/spice_vbias.json" % k, od + "/final_%d/guards.json" % k)
json.dump({"w_s": w_s, "close_log": log, "final": k}, open(od + "/pipeline.json", "w", encoding="utf-8"), indent=1)
