# O-206 추가 실측 -- (1) 대안 (d) 창 끝: oracle .tf(DC 증분 이득) 대 .ac(fstart) 대 엔진(ω→0 노달 = (a_tb) 같은 계산) 창 끝 위치
# (2) C4 제안 '점별 KCL 잔차 > tol_I 이면 추정 불능' 판정: (a_tb) 1차 예측 노드 전압에서 LUT 순방향 전류(sweep 기록 dev.ID)로 노드별 KCL 잔차를 다시 계산하고
#     tol_I(노드) = 그 노드에 채널(d·s)이 닿는 MOS 의 tol_V × dc_gm 최댓값(봉인 3 정의 -- seal_kcl.py 머리말, 봉인점 dc_tol_v·dc_gm; tol_V = ss.lut_rel_tol / gm_id)
#     와 비교한다. 결과 o206_d_kcl.txt(입력 jsonl 에서 결정적 재생성, 덮어씀).
import json, pathlib, math
HERE = pathlib.Path(__file__).parent
name = "nmcnr_amplifier"
d = [json.loads(l) for l in (HERE / "o206_seal_dump.jsonl").read_text(encoding="utf-8").splitlines() if l.strip() and '"devices"' in l][-1]
V0, s_tb = d["nodes"], d["s_tb"]
inp, inn, out = d["inp"], d["inn"], d["out"]
E = {round(json.loads(l)["dx"], 6): json.loads(l) for l in (HERE / "o206_engine_sweep.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
T = {round(json.loads(l)["dx"], 6): json.loads(l) for l in (HERE / "o206_d_tf.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
S = {round(json.loads(l)["dx"], 6): json.loads(l) for l in (HERE / "o206_spice_sweep.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
grid = sorted(k for k in T if k in E)
x0 = V0[inp]
O = []
P = O.append
fixed = set(d["ss_ground"]) | set(d["ss_inputs"]) | set(d["rails"])
free = [n for n in d["ss_nodes"] if n not in fixed]
devs = d["devices"]
tolI = {}
for n in free:
    c = [devs[m]["ss"]["lut_rel_tol"] / devs[m]["gm_id"] * devs[m]["ss"]["gm"] for m in devs if n in (devs[m]["pins"]["d"], devs[m]["pins"]["s"])]
    tolI[n] = max(c) if c else None
P(f"# O-206 (d)·C4 실측 {name}, x0 = {x0:.6f} V")
P("tol_I(노드, 봉인 3 정의, A): " + ", ".join(f"{n}={v:.3e}" if v else f"{n}=MOS 없음(봉인 3: 부동소수 한계)" for n, v in tolI.items()))


def resid(k):
    e = E[k].get("a_tb") or {}
    dv = e.get("dev")
    if not dv:
        return None
    V = {n: V0[n] + s_tb.get(n, 0.0) * k for n in V0}
    I = {n: 0.0 for n in V}
    for m, r in dv.items():
        sgn = 1.0 if devs[m]["kind"] == "nmos" else -1.0
        I[devs[m]["pins"]["d"]] -= sgn * r["ID"]; I[devs[m]["pins"]["s"]] += sgn * r["ID"]
    for pn, pv in d["passives"].items():
        if pv["kind"] == "resistor":
            a, b = list(pv["pins"].values())
            i = (V[a] - V[b]) / pv["value"]
            I[a] -= i; I[b] += i
    rat = {n: abs(I[n]) / tolI[n] for n in free if tolI[n]}
    w = max(rat, key=rat.get)
    return rat[w], w, I[w]


P("\n## 1. (a_tb) 1차 예측점 KCL 잔차 / tol_I (최대 노드)")
P("x | 최대 |잔차|/tol_I (노드, 잔차 A) | 판정(> 1 = 추정 불능) | ΔG a_tb − SPICE(dB)")
first_bad = None
for k in grid:
    r = resid(k)
    if r is None:
        continue
    if r[0] > 1 and first_bad is None and k >= 0:
        first_bad = k
    if abs(k * 1000) % 20 < 1e-6 or 0.03 <= k <= 0.11:
        ga = (E[k]["a_tb"] or {}).get("gain_db"); gs = S[k].get("gain_db")
        P(f"{x0+k:.3f} | {r[0]:.2f} ({r[1]}, {r[2]:+.3e}) | {'불능' if r[0] > 1 else '통과'} | {ga-gs:+.2f}")
neg_bad = [k for k in grid if k < 0 and (resid(k) or (0,))[0] > 1]
P(f"봉인점(Δx=0) 잔차비 = {resid(0.0)[0]:.3f}. 위쪽에서 처음 잔차비 > 1 인 x = {None if first_bad is None else round(x0+first_bad,4)}; 아래쪽 잔차비 > 1 점 수 {len(neg_bad)}/{sum(1 for k in grid if k<0)}")


def end_up(curve, thr):
    prev = None
    for k in [k for k in grid if k >= 0]:
        v = curve(k)
        if v is None:
            return None
        if k == 0 and v < thr:
            return "nominal_fail"
        if v < thr:
            k0, v0 = prev
            return x0 + k0 + (k - k0) * (v0 - thr) / (v0 - v)
        prev = (k, v)
    return None


P("\n## 2. (d) 점별 증분 DC 이득 기준 창 끝 -- oracle .tf 대 .ac, 엔진 (d)=(a_tb) 같은 ω→0 노달 값")
dev_db = [abs(T[k]["tf_db"] - T[k]["ac_db"]) for k in grid if T[k]["tf_db"] is not None and T[k]["ac_db"] is not None and T[k]["ac_db"] > 0]
P(f"oracle .tf − .ac(fstart) 이득 차: 최대 {max(dev_db):.3f} dB, 중앙 {sorted(dev_db)[len(dev_db)//2]:.4f} dB (이득 > 0 dB 점 {len(dev_db)}개)")
tf0 = T[0.0]["tf_db"]; ac0 = T[0.0]["ac_db"]; ga0 = E[0.0]["a_tb"]["gain_db"]
P(f"공칭: .tf {tf0:.3f}, .ac {ac0:.3f}, 엔진 {ga0:.3f} dB; spec 100 dB 기준 -> 셋 다 공칭 미달(창 공)")
P("기준 = 자기 공칭 − t | .tf 끝 | .ac 끝 (차 mV) | 엔진 (d)=(a_tb) 끝 (.tf 대비 mV) | 잔차 표지 첫 점 이후인가")
for t in (1, 3, 6, 10, 20):
    et = end_up(lambda k: T[k]["tf_db"], tf0 - t)
    ea = end_up(lambda k: T[k]["ac_db"], ac0 - t)
    ee = end_up(lambda k: (E[k].get("a_tb") or {}).get("gain_db"), ga0 - t)
    flag = None if first_bad is None or ee is None else (ee >= x0 + first_bad)
    P(f"공칭−{t} | {et:.4f} | {ea:.4f} ({1e3*(ea-et):+.1f}) | {ee:.4f} ({1e3*(ee-et):+.1f}) | {flag}")
(HERE / "o206_d_kcl.txt").write_bytes(("\n".join(O) + "\n").encode("utf-8"))
print("\n".join(O))
