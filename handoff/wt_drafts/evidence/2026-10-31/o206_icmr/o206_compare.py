# O-206 비교 -- o206_engine_sweep.jsonl((a) a_tb·a_hold, (c) Newton)과 o206_spice_sweep.jsonl(oracle .op + .ac)을 같은 Δx 격자에서 맞대고
# (1) 점별 이득 차 (2) 기능 기준 창 끝 위치 차 (3) 영역 행 창 끝 (4) 계산 꼴(LUT 조회·선형 풀이·반복 수)를 낸다. 결과 o206_compare.txt(덮어씀 -- 입력 jsonl 에서 결정적 재생성).
import json, pathlib, math, statistics
HERE = pathlib.Path(__file__).parent
name = "nmcnr_amplifier"
dump = [json.loads(l) for l in (HERE / "o206_seal_dump.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
d = [r for r in dump if r.get("circuit") == name and "devices" in r][-1]
E = {}
for l in (HERE / "o206_engine_sweep.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    if r["circuit"] == name:
        E[round(r["dx"], 6)] = r
S = {}
for l in (HERE / "o206_spice_sweep.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    if r["circuit"] == name:
        S[round(r["dx"], 6)] = r
grid = sorted(k for k in S if k in E)
out = []
P = out.append
x0 = d["nodes"][d["inp"]]
P(f"# O-206 비교 {name}: 봉인점 x0 = {x0:.6f} V, 격자 {len(grid)}점 (Δx {grid[0]:+.3f} ~ {grid[-1]:+.3f} V)")
P(f"spec 판정 제약: {d['spec_constraints']}")
P(f"엔진 봉인점 gain_ss_db(ss_evaluate) = {[e for e in d['metrics']['entries'] if e[0]['metric']=='gain_ss_db'][0][1]['value']:.4f} dB, 측정 스크립트 노달 = {d['gain_db_nominal']:.4f} dB")
P(f"측정 구성 T 1차: u_hold = {d['u_T']:.4f} (Δout = 0), u_tb = {d['u_tb']:.4f} (oracle 되먹임 1차, Δout/Δx = {d['u_tb']-1:.4f})")


def g(r, k):
    v = r.get(k) or {}
    return v.get("gain_db")


def dev(r, k, m, q):
    v = (r.get(k) or {}).get("dev") or {}
    return (v.get(m) or {}).get(q)


def sdev(r, m, q):
    return ((r.get("dev") or {}).get(m) or {}).get(q)


mos = sorted(d["devices"])
P("\n## 1. 점별 대조 (이득 dB, 반전 입력·출력 V, 작은 가지 M102 전류 µA, 최소 포화 여유 V(소자))")
P("x | G_spice | G_a_tb | G_a_hold | G_c | ΔG_a_tb | ΔG_c | Vinn s/a_tb/c | Vout s/a_tb/c | I102 s/a_tb/c | minslack s | minslack a_tb | minslack c")
for k in grid:
    if not (abs(k * 1000) % 20 < 1e-6 or (0.04 <= k <= 0.12)):
        continue
    s, e = S[k], E[k]
    gs = s.get("gain_db")
    ga, gh, gc = g(e, "a_tb"), g(e, "a_hold"), g(e, "c")
    def ms(src):
        best = None
        for m in mos:
            if src == "s":
                v = None if sdev(s, m, "vds") is None else sdev(s, m, "vds") - sdev(s, m, "vdsat")
            else:
                v = dev(e, src, m, "slack")
            if v is not None and (best is None or v < best[0]):
                best = (v, m)
        return "-" if best is None else f"{best[0]:+.3f}({best[1]})"
    f = lambda v, n=2: "-" if v is None else f"{v:.{n}f}"
    P(f"{x0+k:.3f} | {f(gs)} | {f(ga)} | {f(gh)} | {f(gc)} | {f(None if (ga is None or gs is None) else ga-gs)} | {f(None if (gc is None or gs is None) else gc-gs)} | "
      f"{f(s.get('v_'+d['inn'].lower()),3)}/{f((e.get('a_tb') or {}).get('Vinn'),3)}/{f((e.get('c') or {}).get('Vinn'),3)} | "
      f"{f(s.get('v_'+d['out'].lower()),3)}/{f((e.get('a_tb') or {}).get('Vout'),3)}/{f((e.get('c') or {}).get('Vout'),3)} | "
      f"{f(None if sdev(s,'M102','id') is None else sdev(s,'M102','id')*1e6,1)}/{f(None if dev(e,'a_tb','M102','ID') is None else dev(e,'a_tb','M102','ID')*1e6,1)}/{f(None if dev(e,'c','M102','ID') is None else dev(e,'c','M102','ID')*1e6,1)} | "
      f"{ms('s')} | {ms('a_tb')} | {ms('c')}")


def end_up(curve, thr):
    """공칭점(Δx=0)에서 위로 처음 curve < thr 인 x(앞 점과 선형 보간), 공칭점이 이미 미달이면 'nominal_fail', 끝까지 안 떨어지면 None."""
    ks = [k for k in grid if k >= 0]
    prev = None
    for k in ks:
        v = curve(k)
        if v is None:
            return ("undefined_at", x0 + k)
        if k == 0 and v < thr:
            return ("nominal_fail", v)
        if v < thr:
            k0, v0 = prev
            return ("end", x0 + k0 + (k - k0) * (v0 - thr) / (v0 - v))
        prev = (k, v)
    return ("none", None)


def end_dn(curve, thr):
    ks = [k for k in sorted(grid, reverse=True) if k <= 0]
    prev = None
    for k in ks:
        v = curve(k)
        if v is None:
            return ("undefined_at", x0 + k)
        if k == 0 and v < thr:
            return ("nominal_fail", v)
        if v < thr:
            k0, v0 = prev
            return ("end", x0 + k0 + (k - k0) * (v0 - thr) / (v0 - v))
        prev = (k, v)
    return ("rail", x0 + ks[-1])


curves = {"spice": lambda k: S[k].get("gain_db"), "a_tb": lambda k: g(E[k], "a_tb"), "a_hold": lambda k: g(E[k], "a_hold"), "c": lambda k: g(E[k], "c")}
P("\n## 2. 기능 기준 창 끝 (창 안 점별 gain_ss_db ≥ 기준)")
spec_thr = [c[2] for c in d["spec_constraints"] if c[0] == "gain_ss_db" and c[1] == ">="]
for thr in spec_thr:
    P(f"spec 값(value_from_constraint gain_ss_db) {thr} dB: " + ", ".join(f"{m}={end_up(cv, thr)}" for m, cv in curves.items()))
gs0 = S[0.0]["gain_db"]
P(f"공칭 이득: spice {gs0:.3f}, a_tb {g(E[0.0],'a_tb'):.3f}, c {g(E[0.0],'c'):.3f} dB")
P("측정 매개변수(설계 상수 아님) -- 기준 수준을 훑어 창 끝 오차가 기준에 따라 어떻게 달라지는지 본다:")
P("기준(dB) | 위 끝 spice | a_tb (차 mV) | a_hold (차 mV) | c (차 mV)")
for thr in [gs0 - t for t in (1, 3, 6, 10, 20, 30)] + [30.0, 20.0]:
    es = end_up(curves["spice"], thr)
    row = [f"{thr:.2f}", f"{es[1]:.4f}" if es[0] == "end" else str(es)]
    for m in ("a_tb", "a_hold", "c"):
        em = end_up(curves[m], thr)
        if em[0] == "end" and es[0] == "end":
            row.append(f"{em[1]:.4f} ({1e3*(em[1]-es[1]):+.1f})")
        else:
            row.append(str(em))
    P(" | ".join(row))
P("같은 기준을 방법마다 자기 공칭 이득에서 뺀 수준(공칭 차 상쇄)으로:")
for t in (1, 3, 6, 10, 20):
    es = end_up(curves["spice"], gs0 - t)
    row = [f"공칭−{t}", f"{es[1]:.4f}" if es[0] == "end" else str(es)]
    for m in ("a_tb", "a_hold", "c"):
        g0 = curves[m](0.0)
        em = end_up(curves[m], g0 - t)
        row.append(f"{em[1]:.4f} ({1e3*(em[1]-es[1]):+.1f})" if (em[0] == "end" and es[0] == "end") else str(em))
    P(" | ".join(row))
P("아래 끝(입력 공통모드 하강): " + ", ".join(f"{m}={end_dn(cv, gs0 - 6)}" for m, cv in curves.items()) + "  (기준 공칭−6 dB 예시)")

P("\n## 3. 영역 행 창 끝 (O-205 (3): 포화 VDS = VDSAT 행) -- 위로 처음 최소 여유 < 0")
def reg_end(src):
    for k in [k for k in grid if k >= 0]:
        if src == "spice":
            sl = [sdev(S[k], m, "vds") - sdev(S[k], m, "vdsat") for m in mos if sdev(S[k], m, "vds") is not None]
            who = min(mos, key=lambda m: sdev(S[k], m, "vds") - sdev(S[k], m, "vdsat"))
        else:
            dv = (E[k].get(src) or {}).get("dev")
            if not dv:
                return ("undefined_at", x0 + k)
            sl = [dv[m]["slack"] for m in mos if "slack" in dv.get(m, {})]
            who = min(dv, key=lambda m: dv[m].get("slack", 9))
        if min(sl) < 0:
            return (round(x0 + k, 4), who)
    return None
for src in ("spice", "a_tb", "a_hold", "c"):
    P(f"{src}: {reg_end(src)}")

P("\n## 4. 계산 꼴 (점 하나당)")
for src in ("a_tb", "a_hold"):
    lc = [E[k][src]["lut_calls"] for k in grid if E[k].get(src)]
    P(f"{src}: LUT 조회 {statistics.median(lc)} (MOS {len(mos)}개 × (op_point + gmb + vdsat 확인)), 선형 풀이 1(LU 1 + 풀이 1, n = 노드 {len(d['ss_nodes'])}), 반복 0")
it = [E[k]["c"]["iters"] for k in grid if (E[k].get("c") or {}).get("conv")]
lc = [E[k]["c"]["lut_calls"] for k in grid if (E[k].get("c") or {}).get("conv")]
nc = [x0 + k for k in grid if not (E[k].get("c") or {}).get("conv")]
P(f"c (Newton, 앞 점 연속 출발): 반복 중앙 {statistics.median(it)} 최대 {max(it)}, LUT 조회 중앙 {statistics.median(lc)} 최대 {max(lc)}, 수렴 실패 점 {len(nc)}개" +
  (f" (x {min(nc):.3f}~{max(nc):.3f})" if nc else ""))
(HERE / "o206_compare.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
print("\n".join(out))
