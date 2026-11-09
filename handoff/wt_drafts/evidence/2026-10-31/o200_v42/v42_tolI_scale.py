# 검증 42: O-c 기준 tol_I(= tol_V x 블록 gm 최댓값, 계획 N3.6) 의 회로 전류 규모 대비 크기. 입력 = 재실행 seal9_rows.jsonl
import json, math, collections, pathlib
H = pathlib.Path(__file__).parent
rows = [json.loads(l) for l in (H/"seal9_rows.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
out = open(H/"v42_tolI_scale.txt", "a", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s+"\n"); out.flush()
by = collections.defaultdict(list)
for r in rows: by[(r["circuit"], r["ev"])].append(r)
per = collections.defaultdict(list)
for (c, ev), rs in by.items():
    gm = [r["gm_id"]*r["ID"] for r in rs]; tv = [r["tol_V"] for r in rs]; ID = [r["ID"] for r in rs]
    tolI_a = max(tv)*max(gm)                      # 최댓값 집계(현행 문언 근사: 블록 = 회로 전체로 둠)
    tolI_b = sum(t*g for t, g in zip(tv, gm))      # Q-T3 합 집계
    per[c].append((tolI_a/min(ID), tolI_a/max(ID), tolI_b/min(ID), min(tv), max(tv)))
for c, v in sorted(per.items()):
    def q(i):
        s = sorted(x[i] for x in v); return (round(s[0], 4), round(s[len(s)//2], 4), round(s[-1], 4))
    P(f"[{c}] 평가 {len(v)}: tol_I(max)/min ID (min,med,max) {q(0)} | tol_I(max)/max ID {q(1)} | tol_I(sum)/min ID {q(2)} | tol_V 범위 {q(3)[0]}~{q(4)[2]} V")
g = [r["gm_id"] for r in rows]; gs = sorted(g)
P("ln10/(gm/ID) [V] (tol_V 1십진당 O-c 경계 VGS 이동, 약반전 근사) min/med/max:", round(math.log(10)/gs[-1], 4), round(math.log(10)/gs[len(gs)//2], 4), round(math.log(10)/gs[0], 4))
for r in rows:
    if r["circuit"] == "pushpull_follower_buffer" and r["device"] == "M2" and r["vgs"] < 0.01:
        P("pushpull M2 행:", {k: r.get(k) for k in ("ev", "vgs", "vds", "ID", "I_off", "epsID", "gm_id", "tol_V", "kind", "w_key")},
          "ln(ID/Ioff)=", round(math.log(r["ID"]/r["I_off"]), 4), "eps=", round(r["epsID"]/r["ID"], 4))
