"""analysis.json 세 개 -> 판정 표(markdown 조각)를 out/summary.md 에 쓴다. 창은 모두 레일로 자른다(계획: 포트 창 ∩ 레일)."""
import json
import math
from pathlib import Path

OUT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c_spice\out")
NAMES = ["two_stage_ota", "ngcc_3stage_ff", "folded_cascode"]
L = []


def clip(d, side, x0, rails):
    lo, hi = rails
    if d is None or (isinstance(d, float) and math.isinf(d)):
        return (lo - x0) if side == 0 else (hi - x0)
    return max(d, lo - x0) if side == 0 else min(d, hi - x0)


def mv(v):
    return "--" if v is None else f"{1e3 * v:+.1f}"


for n in NAMES:
    r = json.loads((OUT / f"{n}.analysis.json").read_text(encoding="utf-8"))
    eng = json.loads((OUT / f"{n}.engine.json").read_text(encoding="utf-8"))
    rails = (min(eng["rails"].values()), max(eng["rails"].values()))
    x0 = r["x0"]
    for cfg in ("B", "A"):
        c = r["configs"][cfg]
        L.append(f"\n### {n} -- 구성 {cfg}\n")
        sp = c["tol_seal"]
        if sp.get("nominal_fail"):
            L.append(f"- SPICE: x0 = {x0:.4f} V에서 이미 여유 음수(최소 {1e3 * sp['worst']:+.1f} mV, {sp['worst_dev']}) -- SPICE 창 비어 있음. 창 비교 불가, 변화율만 비교.\n")
        else:
            L.append(f"- SPICE 창(tol 봉인점 값): [{sp['lo']:.4f}, {sp['hi']:.4f}] V = x0 {mv(sp['dlo'])} / {mv(sp['dhi'])} mV"
                     f" (묶는 소자 {sp['bind_lo'] or '레일'} / {sp['bind_hi'] or '레일'}); tol 점마다 값: {mv(c['tol_pt']['dlo'])} / {mv(c['tol_pt']['dhi'])} mV\n")
        L.append("| 틀 | 아래 끝 Δ (mV) | 위 끝 Δ (mV) | 아래 오차 (mV) | 위 오차 (mV) | 묶는 소자 |")
        L.append("|---|---|---|---|---|---|")
        for fr in ("theta", "kcl"):
            p = c["engine_pred"][fr]
            dlo, dhi = clip(p["dlo"], 0, x0, rails), clip(p["dhi"], 1, x0, rails)
            if sp.get("nominal_fail"):
                elo = ehi = None
            else:
                elo, ehi = dlo - sp["dlo"], dhi - sp["dhi"]
            L.append(f"| {'θ 고정' if fr == 'theta' else 'KCL'} | {mv(dlo)} | {mv(dhi)} | {mv(elo)} | {mv(ehi)} | {p['bind_lo']} / {p['bind_hi']} |")
        if cfg == "B" and not sp.get("nominal_fail"):
            tan = c["spice_tangent_window"]
            tfz = c["spice_tangent_window_vdsat_frozen"]
            L.append("\n오차 분해(레일 자름, 단위 mV, 합 = 엔진 끝 − SPICE 끝):\n")
            L.append("| 끝 | 틀 | 여유(모형) 차 = 엔진 − 혼합 | 틀 변화율 차 = 혼합 − SPICE 접선(VDsat 고정) | VDsat 이동 = 접선(고정) − 접선 | 곡률 = 접선 − SPICE 참값 | 합 |")
            L.append("|---|---|---|---|---|---|---|")
            for side, key in ((0, "dlo"), (1, "dhi")):
                true = sp[key]
                t_full = clip(tan[side], side, x0, rails)
                t_frz = clip(tfz[side], side, x0, rails)
                for fr in ("theta", "kcl"):
                    e = clip(c["engine_pred"][fr][key], side, x0, rails)
                    h = clip(c[f"hybrid_spice_slack_{fr}_rate"][side], side, x0, rails)
                    L.append(f"| {'아래' if side == 0 else '위'} | {'θ' if fr == 'theta' else 'KCL'} | {mv(e - h)} | {mv(h - t_frz)} | {mv(t_frz - t_full)} | {mv(t_full - true)} | {mv(e - true)} |")
        # 감도·변화율 통계 (x0)
        rr = c["row_rates"]
        for fr in ("theta", "kcl"):
            d = [abs(v[fr] - v["spice_dvds"]) for v in rr.values()]
            ds = [abs(c["sens"][k][fr] - c["sens"][k]["spice_x0"]) for k in c["sens"] if c["sens"][k][fr] is not None]
            L.append(f"\n- x0 변화율 |틀 − SPICE dVDS/dx| ({'θ' if fr == 'theta' else 'KCL'}): 최대 {max(d):.4f}, 평균 {sum(d) / len(d):.4f} V/V (소자 {len(d)}); "
                     f"노드 감도 |s − SPICE| 최대 {max(ds):.4f}, 평균 {sum(ds) / len(ds):.4f} V/V (노드 {len(ds)})")
        big = sorted(((abs(c["sens"][k]["theta"] - c["sens"][k]["spice_x0"]) if c["sens"][k]["theta"] is not None else 0, k) for k in c["sens"]), reverse=True)[:4]
        L.append("- θ 오차가 큰 노드: " + ", ".join(f"{k}(θ {c['sens'][k]['theta']:+.3f}, KCL {c['sens'][k]['kcl']:+.3f}, SPICE {c['sens'][k]['spice_x0']:+.3f})" for _, k in big))
        offs = sorted(((abs(v["diff_mV"]), k, v["diff_mV"]) for k, v in c["node_at_x0"].items() if v["diff_mV"] is not None), reverse=True)[:4]
        L.append("- x0 동작점 SPICE − 엔진(큰 넷): " + ", ".join(f"{k} {d:+.1f} mV" for _, k, d in offs))
(OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
