"""손계산 꼴 '손가락 폭 = 기존 LUT 슬라이스 폭 그대로, m 정수' 의 전류 잔차 측정 (P8 (E) 대체 후보).
입력 = plan_v6384/p8_finger/p8_enum.out.jsonl (작성자 열거 자료; w_by_slice[s] = [w_s, bin, W(s)=I*L/IDu_s]).
(a) ref_only: 기준 폭 슬라이스(w_hi bin 위끝 = 계획 기준폭) 하나로 W 계산할 때, 실현 슬라이스의 W 와 비 -> 고전 gm/ID(폭 효과 무시) 오차
(b) exact_slice: w_s <= w_hi, m = round(W(s)/w_s)>=1 중 |m*w_s/W(s)-1| 최소 -> 상대 전류 잔차 r (같은 VGS 에서)
결과 = p8_exact_slice.out.json"""
import json, math, sys
src = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/plan_v6384/p8_finger/p8_enum.out.jsonl"
rows = [json.loads(l) for l in open(src, encoding="utf-8")]
out = []
for r in rows:
    for p in r.get("points", []):
        for dn, d in p["devices"].items():
            e = d.get("enum"); 
            if not e or not e.get("w_by_slice"): continue
            ws = {k: v for k, v in e["w_by_slice"].items() if v[2] is not None}
            whi = e["w_hi_um"]
            ref = [v for v in ws.values() if abs(v[0] - whi) < 1e-9]
            best = None
            for k, (w, b, W) in ws.items():
                if w > whi + 1e-12: continue
                m = max(1, round(W / w)); res = m * w / W - 1
                if best is None or abs(res) < abs(best[3]): best = (k, w, m, res, W)
            # 연속 자기정합 해(작성자 fits) 가 있으면 그 W
            fits = e.get("fits", [])
            Wfit = fits[0][3] if fits else None
            refW = ref[0][2] if ref else None
            out.append(dict(circuit=r["circuit"], point=p["point"], dev=dn, W_fit=Wfit, W_ref=refW,
                            ref_ratio=(refW / Wfit if (refW and Wfit) else None),
                            exact=dict(slice=best[0], w=best[1], m=best[2], resid=best[3], W=best[4]) if best else None,
                            Wspread=(min(v[2] for v in ws.values()), max(v[2] for v in ws.values()))))
json.dump(out, open("p8_exact_slice.out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
rs = [abs(o["exact"]["resid"]) for o in out if o["exact"]]
rr = [abs(math.log(o["ref_ratio"])) for o in out if o["ref_ratio"]]
rs.sort(); rr.sort()
def q(a, f): return a[min(len(a)-1, int(f*len(a)))]
summ = dict(n=len(out), exact_resid_med=q(rs,.5), exact_resid_p90=q(rs,.9), exact_resid_max=rs[-1],
            n_exact_le_5pct=sum(x<=0.05 for x in rs), n_exact_le_10pct=sum(x<=0.10 for x in rs),
            ref_only_abs_ln_med=q(rr,.5), ref_only_abs_ln_max=rr[-1] if rr else None, n_ref=len(rr))
json.dump(summ, open("p8_exact_slice.summary.json", "w"), indent=1); print(summ)
big=[(o["circuit"],o["dev"],round(o["exact"]["resid"],3),o["exact"]["m"],o["W_fit"]) for o in out if o["exact"] and abs(o["exact"]["resid"])>0.1]
print(big[:30])
