"""P8: 옛 반복이 수렴한 점에서 규칙 (B)(= (i) 열거 + (ii) bin 안 보간, 기준 w_f ≤ w_hi 최대)의 선택이 옛 결과(m, w_f)와 같은지. 출력 p8_interp_conv.out.json"""
import json, collections
from p8_compare2 import fits_interp, pickB, G
cnt = collections.Counter(); det = []
for l in open("p8_enum.out.jsonl", encoding="utf-8"):
    r = json.loads(l)
    for p in r.get("points", []):
        for dev, d in p["devices"].items():
            it, e = d["iter_rule"], d["enum"]
            if it["status"] != "converged":
                continue
            ok = [f for f in fits_interp(e) if f[1] <= e["w_hi_um"] + G / 2]
            last = it["seq"][-1]
            if not ok:
                cnt[(r["circuit"], "no_fit")] += 1; continue
            B = pickB(ok)
            same = abs(B[1] - last[3]) <= G + 1e-9
            cnt[(r["circuit"], "same" if same else "diff")] += 1
            if not same:
                det.append([r["circuit"], p["point"], dev, "iter(m,w_f)", [last[2], last[3]], "B", list(B[:3])])
json.dump({"counts": {"|".join(k): v for k, v in cnt.items()}, "detail": det}, open("p8_interp_conv.out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({"|".join(k): v for k, v in cnt.items()}); [print(x) for x in det]
