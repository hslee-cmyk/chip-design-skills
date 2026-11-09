# seal9_rows.jsonl 집계 -- 옛 봉인 9(I_off <= eps*ID) / P4(ID > I_off) / P5(ID > 0) 판정을 엔진 평가 점마다 비교. 결과 agg_seal9.txt.
import json, math, pathlib, collections
HERE = pathlib.Path(__file__).parent
rows = [json.loads(l) for l in (HERE / "seal9_rows.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
circ = [json.loads(l) for l in (HERE / "seal9_circuits.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
out = open(HERE / "agg_seal9.txt", "w", encoding="utf-8")


def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")


def q(v):
    v = sorted(x for x in v if x is not None and math.isfinite(x))
    if not v: return None
    f = lambda p: v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))]
    return [round(f(0), 4), round(f(.1), 4), round(f(.5), 4), round(f(.9), 4), round(f(1), 4)]


P("회로 상태:")
for c in circ:
    P(" ", c["circuit"], c.get("stage"), "seal9_evals", c.get("seal9_evals"), "front", c.get("n_front"), (c.get("error") or "")[:90])
by = collections.defaultdict(list)
for r in rows: by[r["circuit"]].append(r)
P("\n판정 비교 (행 = (평가, 전도 MOS)); 옛 = I_off <= eps*ID, P4 = ID > I_off, P5 = ID > 0 (기록 행은 모두 ID > 0)")
tot = collections.Counter()
for c, rs in sorted(by.items()):
    cnt = collections.Counter(); devs = collections.defaultdict(set); lnr = []; vg = []; lnr_old_off = []
    for r in rs:
        ID, off, eid = r.get("ID"), r["I_off"], r["epsID"]
        if ID is None: cnt["no_op"] += 1; continue
        old = None if eid is None else (off <= eid)
        p4 = ID > off
        lr = math.log(ID / off) if off > 0 else float("inf")
        lnr.append(lr); vg.append(r.get("vgs"))
        band = (eid is not None) and (0 < lr <= eid / ID)
        cnt["rows"] += 1
        cnt["old_undef"] += old is None
        cnt["old_on"] += old is True
        cnt["old_off"] += old is False
        cnt["p4_off"] += not p4
        cnt["old_off_p4_on"] += (old is False) and p4
        cnt["old_on_p4_off"] += (old is True) and (not p4)
        cnt["old_off_p5_on"] += old is False
        cnt["p4_band"] += band
        if old is False: devs["old_off"].add(r["device"]); lnr_old_off.append(lr)
        if not p4: devs["p4_off"].add(r["device"])
        devs["all"].add(r["device"])
    tot.update(cnt)
    P(f"\n[{c}] 행 {cnt['rows']}, 소자 {len(devs['all'])}, 평가 {max(r['ev'] for r in rs)}")
    P("  옛 전도/꺼짐/미정:", cnt["old_on"], cnt["old_off"], cnt["old_undef"], "| P4 꺼짐:", cnt["p4_off"], "| P5 꺼짐: 0")
    P("  옛 꺼짐 & P4 전도:", cnt["old_off_p4_on"], "| 옛 전도 & P4 꺼짐:", cnt["old_on_p4_off"], "| 옛 꺼짐 & P5 전도:", cnt["old_off_p5_on"],
      "| P4 '구별 불가' 띠:", cnt["p4_band"])
    P("  옛 꺼짐 소자:", sorted(devs["old_off"]), "| P4 꺼짐 소자:", sorted(devs["p4_off"]))
    P("  ln(ID/I_off) 분위[0,.1,.5,.9,1]:", q(lnr), "| VGS:", q(vg), "| 옛 꺼짐 행 ln(ID/I_off):", q(lnr_old_off))
P("\n합계:", dict(tot))
