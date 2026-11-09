# q5_engine_*.jsonl 집계 -> q5_engine_agg.txt (측정 1b 헤드룸 행·출발점, 2 꼬리 셀 도달, 3 봉인 7 띠).
import json, pathlib, math
from collections import defaultdict
import numpy as np
HERE = pathlib.Path(__file__).parent
rd = lambda n: [json.loads(l) for l in (HERE / n).read_text(encoding="utf-8").splitlines() if l.strip()]
C, Hh, Rw = rd("q5_engine_circuits.jsonl"), rd("q5_engine_headroom.jsonl"), rd("q5_engine_rows.jsonl")
out = []; p = out.append
p("## 회로 실행")
for r in C:
    p(f"{r['circuit']}: A {r.get('stageA')} B {r.get('stageB')} {r.get('stage')} seal7 평가 {r['seal7_evals']} 헤드룸 호출 {r['head_calls']} 대조 결정성 {r.get('ctrl_theta_equal')} err {str(r.get('error',''))[:120]}")
p("\n## 1b 헤드룸 행 (start_intervals headroom_bounds, VDS 엣지)")
errs = [h for h in Hh if "error" in h]
p(f"기록 오류 {len(errs)}")
by = defaultdict(list)
for h in Hh:
    if "error" not in h:
        by[h["circuit"]].append(h)
for c, hs in by.items():
    st = np.array([h["sum_tol"] for h in hs if h["sum_tol"] is not None]) * 1e3
    own = np.array([h["own_tol"] for h in hs]) * 1e3
    pt = np.array([h["path_tol"] for h in hs if h["path_tol"] is not None]) * 1e3
    ratio = np.array([h["sum_tol"] / h["budget_nt"] for h in hs if h["sum_tol"] is not None and h["budget_nt"]])
    act_on = sum(1 for h in hs if h["g_lo_on"] is not None and h["g_lo_on"] > h["curve_gmid_min"])
    act_nt = sum(1 for h in hs if h["g_lo_nt"] is not None and h["g_lo_nt"] > h["curve_gmid_min"])
    dg = [abs(h["g_lo_on"] - h["g_lo_nt"]) / h["g_lo_nt"] for h in hs if h["g_lo_on"] is not None and h["g_lo_nt"] is not None and h["g_lo_nt"] > 0]
    lost = sum(1 for h in hs if h["g_lo_on"] is None and h["g_lo_nt"] is not None)
    tm = sorted({(h["kind"], h["tol_min"]) for h in hs})
    p(f"{c}: 행 {len(hs)} | Σtol mV med {np.median(st):.3f} max {st.max():.3f} | 자기 tol mV med {np.median(own):.3f} max {own.max():.3f} | 경로 tol 합 mV max {pt.max() if pt.size else 0:.3f}"
      f" | Σtol/예산 med {np.median(ratio):.2e} max {ratio.max():.2e} | 하한 활성 행(tol 있음/없음) {act_on}/{act_nt} | gm/ID 하한 상대차 max {max(dg) if dg else 0:.2e} | tol 때문에 하한 없음 {lost} | 엣지 tol 최솟값 {tm}")
p("\n## 1b 출발점 칸 0 theta: tol 있음 대 tol 없음(헤드룸·정의역 행 tol_vdsat = 0)")
for r in C:
    a, n = r.get("start_on"), r.get("start_nt")
    if not a or not n:
        continue
    da = {(x[0], x[1]): x[2] for x in a["theta"]}; dn = {(x[0], x[1]): x[2] for x in n["theta"]}
    lnd = [(k[1], dn[k] - da[k]) for k in da if k[0] == "ln_idu" and k in dn and dn[k] != da[k]]
    oth = [(k, (dn[k] - da[k]) / abs(da[k]) if da[k] else None) for k in da if k[0] != "ln_idu" and k in dn and dn[k] != da[k]]
    nln = sum(1 for k in da if k[0] == "ln_idu")
    mx = max((abs(v) for _, v in lnd), default=0.0)
    big = sorted(lnd, key=lambda x: -abs(x[1]))[:4]
    p(f"{r['circuit']}: ln_idu 성분 {nln} 중 바뀜 {len(lnd)}, |Δln IDu| max {mx:.4f} (상위 {[(d, round(v, 4)) for d, v in big]}) | 그 밖 바뀐 성분 {[(k[0], k[1], None if v is None else round(v, 4)) for k, v in oth][:6]} | 키 집합 같음 {set(da) == set(dn)}")
p("\n## 3 봉인 7 띠 (find_front 평가 행)")
tot = dict(rows=0, band=0, viol=0)
for c in sorted({w["circuit"] for w in Rw}):
    ws = [w for w in Rw if w["circuit"] == c and "slack0" in w]
    nb = [w for w in ws if w["band"]]; nv = [w for w in ws if w["sat_violate"]]
    ev = len({w["ev"] for w in ws}); evb = len({w["ev"] for w in nb})
    tot["rows"] += len(ws); tot["band"] += len(nb); tot["viol"] += len(nv)
    tl = np.array([w["tol"] for w in ws if w["tol"] is not None]) * 1e3
    p(f"{c}: 행 {len(ws)} (평가 {ev}) | 띠 안 {len(nb)} (평가 {evb}, 소자 {sorted({w['device'] for w in nb})}) | 위반 {len(nv)} (소자 {sorted({w['device'] for w in nv})}) | 행 tol mV med {np.median(tl):.3f} max {tl.max():.3f}")
    for w in nb[:8]:
        p(f"    띠: ev {w['ev']} {w['device']} {w['kind']} L {w['L']*1e6:.3f}um VGS {w['vgs']:.4f} VDS {w['vds']:.4f} VSB {w['vsb']:.4f} ID {w['current']:.3e} VDsat {w['vdsat']:.5f} 여유 {1e3*w['slack0']:.3f} mV tol {1e3*w['tol']:.3f} mV")
p(f"합계: 행 {tot['rows']}, 띠 안 {tot['band']}, 위반 {tot['viol']}")
p("\n## 2 pmos w_key 1000 꼬리 셀(L 0.15/0.18 um 앵커, 높은 VDS 칸) 도달")
pm = [w for w in Rw if w.get("kind") == "pmos" and "cell_L" in w]
p(f"pmos 평가 행 {len(pm)}, w_key 집합 {sorted({w['w_key'] for w in pm})}")
hit = [w for w in pm if any(abs(l - 1.5e-7) < 1e-12 or abs(l - 1.8e-7) < 1e-12 for l in w["cell_L"])]
p(f"L 칸이 0.15/0.18 um 앵커에 닿는 pmos 행 {len(hit)} (소자 {sorted({(w['circuit'], w['device']) for w in hit})})")
if hit:
    vv = np.array([w["vds"] for w in hit]); tt = np.array([w["tol"] for w in hit]) * 1e3
    p(f"  그 행 VDS 범위 {vv.min():.3f}~{vv.max():.3f} V, tol mV min {tt.min():.3f} med {np.median(tt):.3f} max {tt.max():.3f}")
    top = sorted(hit, key=lambda w: -w["tol"])[:6]
    for w in top:
        p(f"    {w['circuit']} {w['device']} L {w['L']*1e6:.3f} VDS {w['vds']:.4f} VGS {w['vgs']:.4f} VSB {w['vsb']:.4f} 칸 L {[round(l*1e6,3) for l in w['cell_L']]} VDS {w['cell_vds']} tol {1e3*w['tol']:.3f} mV 여유 {1e3*w['slack0']:.1f} mV")
alltol = sorted(((w["tol"], w["circuit"], w["device"], w["kind"], w["L"], w["vds"]) for w in Rw if w.get("tol") is not None), reverse=True)[:5]
p(f"전체 행 tol 상위 5: {[(round(t*1e3,3), c, d, k, round(L*1e6,3), round(v,3)) for t, c, d, k, L, v in alltol]}")
(HERE / "q5_engine_agg.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
