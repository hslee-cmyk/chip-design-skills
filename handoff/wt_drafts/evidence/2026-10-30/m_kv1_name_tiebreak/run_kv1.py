# 구동: kv1_tiebreak.py 의 손계산(LUT r2)·oracle(ngspice) 로 고리별 두 선택(dep=rail / dep=stacked)을 잰다.
# 출력: results.jsonl(케이스마다 append), summary 는 run 끝에 summary.json 으로.
import json, math, sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import kv1_tiebreak as K

HERE = pathlib.Path(__file__).parent
BASE = dict(IQ=20e-6, I9a=0.6e-6, I9b=0.6e-6, I11=2.2e-6, I14=2.5e-6,
            L15=0.35e-6, L16=0.35e-6, L9a=0.15e-6, L9b=0.35e-6, Ld=0.18e-6,
            # θ 전류 밀도(A/m) = 앞 측정 classab_battery 대표점(design_out.jsonl)의 I/W -- 원문 설계점 근처
            u15=20e-6 / 200e-6, u16=20e-6 / 25e-6, u9a=0.6e-6 / 23.397e-6, u9b=0.6e-6 / 1.925e-6)
# 원문 다이오드 치수(Fig.7(a): M11 15/0.18, M14 2/0.18) 의 전류 밀도 = 독립 다이오드 θ 의 원문 근처 값
U_ORIG = dict(P=2.2e-6 / 15e-6, N=2.5e-6 / 2e-6)
OUTERS = dict(rep=1.0, hi=4.0, lo=0.25)          # 우변 소자 IDu 배율 -> 고리 합 T 를 위·아래로(상자 경계 쪽 대용)
NAME_PICK = dict(P="rail", N="stacked")          # 이름순: M11a(레일)·M14a(쌓임) [대칭: M20a(레일)·M23a(쌓임)]


def th_of(scale):
    th = dict(BASE)
    for k in ("u15", "u16", "u9a", "u9b"):
        th[k] = BASE[k] * scale
    return th


def sweep_range(kind):
    v, g, lid = K.branch(kind, BASE["Ld"], None, 0.0, True)
    return float(math.exp(lid[0]) / K.WREF), float(math.exp(lid[-1]) / K.WREF)


def main():
    summ = dict(sweep={}, spice=[], roundtrip=[])
    for oname, sc in OUTERS.items():
        th = th_of(sc)
        o = K.outer(th)
        K.append(dict(case="outer", outer=oname, th=th, o=o))
        for loop, kind, T in (("P", "p", o["Tp"]), ("N", "n", o["Tn"])):
            lo, hi = sweep_range(kind)
            us = np.exp(np.linspace(math.log(lo), math.log(hi), 61))
            feas = {"rail": [], "stacked": []}
            for u in us:
                for dep in ("rail", "stacked"):
                    r = K.close_loop(kind, th["Ld"], T, float(u), dep)
                    feas[dep].append(bool(r["ok"]))
                    K.append(dict(case="sweep", outer=oname, loop=loop, **{k: v for k, v in r.items()}))
            both = [a and b for a, b in zip(feas["rail"], feas["stacked"])]
            only_r = [a and not b for a, b in zip(feas["rail"], feas["stacked"])]
            only_s = [b and not a for a, b in zip(feas["rail"], feas["stacked"])]
            summ["sweep"][f"{oname}/{loop}"] = dict(T=T, n=len(us), ok_rail=sum(feas["rail"]), ok_stacked=sum(feas["stacked"]),
                                                    both=sum(both), only_rail=sum(only_r), only_stacked=sum(only_s),
                                                    u_range=[lo, hi],
                                                    u_ok_rail=[float(us[i]) for i in (np.where(feas["rail"])[0][[0, -1]] if any(feas["rail"]) else [])],
                                                    u_ok_stacked=[float(us[i]) for i in (np.where(feas["stacked"])[0][[0, -1]] if any(feas["stacked"]) else [])])
        # 대표 θ 점: 원문 근처 + (rep 만) 두 선택 공통 가능 구간의 양 끝 쪽
        pts = [("orig", U_ORIG["P"], U_ORIG["N"])]
        if oname == "rep":
            # 상자 경계 쪽 대용: 독립 다이오드 IDu 를 우변 배율(OUTERS)과 같은 배율로 -- run1 의 LUT 정의역 5 %/95 % 점은 W 가 비물리(>1e4 um)라 oracle 이 풀리지 않음
            pts += [("u_x%g" % f, U_ORIG["P"] * f, U_ORIG["N"] * f) for f in (OUTERS["hi"], OUTERS["lo"])]
        for pname, uP, uN in pts:
            for dP in ("rail", "stacked"):
                for dN in ("rail", "stacked"):
                    P = K.close_loop("p", th["Ld"], o["Tp"], uP, dP)
                    N = K.close_loop("n", th["Ld"], o["Tn"], uN, dN)
                    rec = dict(case="spice", outer=oname, point=pname, depP=dP, depN=dN,
                               name_combo=(dP == NAME_PICK["P"] and dN == NAME_PICK["N"]), P=P, N=N)
                    if not (P["ok"] and N["ok"]):
                        rec.update(skipped="hand infeasible")
                        K.append(rec); summ["spice"].append(rec); continue
                    S = K.size_all(th, o, P, N)
                    e0 = K.e0_hand(th, o, P, N)
                    v, dv = K.spice(f"{oname}_{pname}_{dP}_{dN}", S, th)
                    sat = {d: dict(vds=abs(dv.get(f"{d.lower()}.vds", float('nan'))), vdsat=dv.get(f"{d.lower()}.vdsat", float('nan')))
                           for d in K.DEVS}
                    for d in sat:
                        sat[d]["sat"] = bool(sat[d]["vds"] >= sat[d]["vdsat"])
                    iq = abs(dv.get("m15.id", float('nan')))
                    rec.update(sizes=S, e0_hand=e0, spice_nodes=v,
                               spice=dict(IQ=iq, IQ_err_pct=100 * (iq / th["IQ"] - 1), I16=abs(dv.get("m16.id", float('nan'))),
                                          I9a=abs(dv.get("m9a.id", float('nan'))), I9b=abs(dv.get("m9b.id", float('nan'))),
                                          all_sat=all(x["sat"] for x in sat.values()), sat=sat,
                                          n11a11b_err_mV=1e3 * (v.get("n11a11b", float('nan')) - (K.VDD - P["v_rail"])),
                                          n14a_14b_err_mV=1e3 * (v.get("n14a_14b", float('nan')) - N["v_rail"]),
                                          vg15_err_mV=1e3 * (v.get("vg15", float('nan')) - o["vg15"]),
                                          vop1_err_mV=1e3 * (v.get("vop1", float('nan')) - o["vop1"])))
                    K.append(rec); summ["spice"].append(rec)
        # 왕복: dep=rail 결과의 레일 IDu 를 dep=stacked 의 독립값으로 넣으면 같은 쌓인 IDu 가 나오는가(같은 물리점)
        for loop, kind, T, u in (("P", "p", o["Tp"], U_ORIG["P"]), ("N", "n", o["Tn"], U_ORIG["N"])):
            a = K.close_loop(kind, th["Ld"], T, u, "rail")
            if a["ok"]:
                b = K.close_loop(kind, th["Ld"], T, a["dep_margin"]["idu_dep"], "stacked")
                rt = dict(case="roundtrip", outer=oname, loop=loop, u_stk_in=u, u_rail_mid=a["dep_margin"]["idu_dep"],
                          u_stk_back=b.get("dep_margin", {}).get("idu_dep"), rel_err=(b["dep_margin"]["idu_dep"] / u - 1) if b.get("dep_margin") else None,
                          v_rail_a=a["v_rail"], v_rail_b=b.get("v_rail"))
                K.append(rt); summ["roundtrip"].append(rt)
    (HERE / "summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
