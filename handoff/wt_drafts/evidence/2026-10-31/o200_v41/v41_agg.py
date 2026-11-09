# v41_p4_vs_p2.jsonl 집계 -> v41_agg.txt (소자 수: '다수' = 비지 않은 설정 >= 50 %, '1개 이상' = 설정 하나라도)
import json, pathlib
HERE = pathlib.Path(__file__).parent
R = [json.loads(l) for l in (HERE / "v41_p4_vs_p2.jsonl").read_text(encoding="utf-8").splitlines()]
out = open(HERE / "v41_agg.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")


keys = sorted({k for r in R for k in r["combos"]})
NS = sum(r["cls"] == "S" for r in R); NF = len(R) - NS
P(f"소자 S {NS} F {NF}; 키 = 규칙|ID|예산")
P("\n(a) P4 - P2 t* 차: 소자 수 다수/1개이상 (S,F), 전체 설정 중 차 있는 설정 수, |dln IDu| 최대, |d gm/ID|/gm/ID 최대, P2 t*=VGS0 마디 설정 수, P2만 비지 않은 설정 수")
for k in keys:
    rows = [r for r in R if k in r["combos"]]
    agg = dict(Sm=0, Fm=0, S1=0, F1=0, nd=0, n=0, dl=0.0, dg=0.0, n0=0, only=0)
    for r in rows:
        c = r["combos"][k]["P4-P2"]
        agg["n"] += c["n"]; agg["nd"] += c["n_differ"]; agg["dl"] = max(agg["dl"], c["dln_max"]); agg["dg"] = max(agg["dg"], c["dg_rel_max"])
        agg["n0"] += c["p2_at_node0"]; agg["only"] += c["only_P2"]
        if c["n"] and c["n_differ"] >= 0.5 * c["n"]:
            agg[r["cls"] + "m"] += 1
        if c["n_differ"] > 0:
            agg[r["cls"] + "1"] += 1
    P(f"{k:22s} N={len(rows):3d} 다수 S{agg['Sm']} F{agg['Fm']} | 1개↑ S{agg['S1']} F{agg['F1']} | 설정 {agg['nd']}/{agg['n']} | dln max {agg['dl']:.3f} | dg max {agg['dg']:.4f} | P2@node0 {agg['n0']} | P2만 {agg['only']}")
P("\n(a') 옛 D2+(봉인 9 행) - P4 t* 차 (참고): 차 있는 설정 / 전체, |dln| 최대")
for k in keys:
    if not k.endswith("none") and "ID1e-05" not in k:
        continue
    s = []
    for t in ("t0p1mV", "t1mV", "tLOO"):
        nd = sum(r["combos"][k]["D2P-P4@" + t]["n_differ"] for r in R if k in r["combos"])
        n = sum(r["combos"][k]["D2P-P4@" + t]["n"] for r in R if k in r["combos"])
        dl = max(r["combos"][k]["D2P-P4@" + t]["dln_max"] for r in R if k in r["combos"])
        s.append(f"{t} {nd}/{n} max {dl:.2f}")
    P(f"{k:22s} " + " | ".join(s))
P("\n(b) 정적 판정 (t* 점에서): 옛 봉인 9 꺼짐 & P4 전도 인 소자 수 다수/1개이상 (S,F) / 설정 수; 반대 방향(옛 전도 & P4 꺼짐) 설정 수")
for v in ("P4", "P2"):
    for t in ("t0p1mV", "t1mV", "tLOO"):
        P(f"-- t* 기준 {v}, tol {t}")
        for k in keys:
            agg = dict(Sm=0, Fm=0, S1=0, F1=0, x=0, n=0, rev=0)
            rows = [r for r in R if k in r["combos"]]
            for r in rows:
                c = r["combos"][k][f"judge@{v}@{t}"]
                agg["x"] += c["old_off_p4_on"]; agg["n"] += c["n"]; agg["rev"] += c["old_on_p4_off"]
                if c["n"] and c["old_off_p4_on"] >= 0.5 * c["n"]:
                    agg[r["cls"] + "m"] += 1
                if c["old_off_p4_on"] > 0:
                    agg[r["cls"] + "1"] += 1
            P(f"   {k:22s} N={len(rows):3d} 다수 S{agg['Sm']} F{agg['Fm']} | 1개↑ S{agg['S1']} F{agg['F1']} | 설정 {agg['x']}/{agg['n']} | 반대 {agg['rev']}")
out.close()
