"""사이징 ↔ 손가락 계획 되먹임(J2 꼴의 손 실행): 레이아웃 규칙이 정한 tail 전류(m5·w_s)로 I1 이 바뀌면
GBW 를 지키도록 Cc 를 다시 풀고, PM 에 필요한 I6 을 다시 풀어 미러 비 n 을 다시 정한다. n 이 고정되면 멈춘다.
argv: hand_point.json  w_s(json)  out.json
"""
import json, math, sys
sys.path.insert(0, "C:/Users/HSLEE/AppData/Local/Temp/la1s_tso_hand/layout")
import design as D
import fingerplan as F

hand = json.load(open(sys.argv[1], encoding="utf-8"))
w_s = json.loads(sys.argv[2])
x = dict(hand["x"])
log = []
plan = F.plan(w_s)
I1 = plan["I1"]
I6 = plan["I6"]
for it in range(8):
    # Cc: GBW = 목표 (I1 고정)
    lo, hi = 5e-14, 2e-11
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        x["Cc"] = mid
        g = D.evaluate(x, I1, I6, w_s)["gbw"]
        if g > D.GBW_T:
            lo = mid
        else:
            hi = mid
    x["Cc"] = hi
    # I6: PM >= 목표 최소
    lo6, hi6 = 1e-7, 5e-3
    for _ in range(40):
        m6 = math.sqrt(lo6 * hi6)
        if D.evaluate(x, I1, m6, w_s)["pm"] >= D.PM_T:
            hi6 = m6
        else:
            lo6 = m6
    need6 = hi6
    m5 = plan["m"]["M5"]
    i7 = w_s["M7"] * F.idu("M7", w_s["M7"])
    n = max(1, math.ceil(need6 / (m5 * i7)))
    I6_new = n * m5 * i7
    r = D.evaluate(x, I1, I6_new, w_s)
    log.append({"it": it, "Cc": x["Cc"], "need6": need6, "n": n, "I6": I6_new, "gbw": r["gbw"], "pm": r["pm"], "gain": r["gain_db"]})
    if abs(I6_new - I6) < 1e-12:
        break
    I6 = I6_new
m = dict(plan["m"])
m["M7"] = n * m["M5"]
m["M6"] = F.even_round(I6 / (w_s["M6"] * F.idu("M6", w_s["M6"])))
choice = {"opt": "B", "w_s": w_s, "m": m, "I1": I1, "I6": I6, "x": x, "log": log,
          "gain_db": r["gain_db"], "gbw": r["gbw"], "pm": r["pm"], "power_uW": r["power_W"] * 1e6}
json.dump(choice, open(sys.argv[3], "w", encoding="utf-8"), indent=1)
