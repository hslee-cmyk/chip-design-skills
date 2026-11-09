# O-200 Q5 측정 4·5 -- 기존 동작점 기록 b74(2026-10-22, 36소자: two_stage_ota·ngcc_3stage_ff·folded_cascode; it2c 봉인점, ngspice-46 sky130 tt)
# 원자료 wt/_drafts/evidence/2026-10-22/b74_oppoint_gap/out/{circuit}.devtb.json(소자 단위, 엔진 봉인점 VGS·VDS·VSB 를 그대로 건 SPICE 단일 소자)과
# {circuit}.circop.json(회로 단위 .op, 기하 m5 = 엔진 슬라이스 폭 5 µm × m)을 읽어,
#   엔진 띠 판정: 0 <= VDS − VDsat_eng < tol_VDsat (봉인 7 띠), 위반 VDS − VDsat_eng < 0
#   SPICE 포화: VDS − @m[vdsat] >= 0 (계획 N3.6 SPICE 대조 (ii) -- 여유 0)
# 을 소자마다 맞댄다. 정의 동일성(측정 5): 같은 op 점(소자 단위 s5·m5 기하 = LUT 생성 기하와 같은 폭)에서 VDsat_eng − @m[vdsat] 차와 tol_VDsat 비.
# 읽기만. 산출: q5_b74_band.jsonl(소자마다 1줄), q5_b74_band.txt(요약).
import json, pathlib, glob
HERE = pathlib.Path(__file__).parent
B = HERE.parent.parent / "2026-10-22/b74_oppoint_gap/out"
OUT = HERE / "q5_b74_band.jsonl"; OUT.write_text("", encoding="utf-8")
summ = []
tot = dict(n=0, band=0, viol=0, sat_dev_s5_neg=0, sat_dev_m5_neg=0, sat_circ_m5_neg=0)
dv_all = []
for f in sorted(glob.glob(str(B / "*.devtb.json"))):
    d = json.loads(pathlib.Path(f).read_text(encoding="utf-8")); c = d["circuit"]
    cop = json.loads((B / (c + ".circop.json")).read_text(encoding="utf-8"))
    cm5 = cop["modes"].get("m5", {}).get("devices", {})
    for name, rec in sorted(d["devices"].items()):
        e = rec["engine"]; sd = rec.get("spice_dev", {})
        if e.get("vdsat") is None or e.get("tol_vdsat") is None:
            continue
        s_eng = e["vds"] - e["vdsat"]; tol = e["tol_vdsat"]
        row = dict(circuit=c, device=name, w_key=e.get("w_key"), L=e["L"], vgs=e["vgs"], vds=e["vds"], vsb=e["vsb"], id=e["id"],
                   vdsat_eng=e["vdsat"], tol=tol, slack_eng=s_eng, band=0 <= s_eng < tol, viol=s_eng < 0)
        for v in ("s5", "m5", "net", "f5"):
            if v in sd and sd[v].get("vdsat") is not None:
                row[f"vdsat_{v}"] = sd[v]["vdsat"]; row[f"slack_dev_{v}"] = sd[v]["vds"] - sd[v]["vdsat"]
                row[f"dvdsat_{v}_mV"] = 1e3 * (e["vdsat"] - sd[v]["vdsat"]); row[f"dvdsat_{v}_over_tol"] = abs(e["vdsat"] - sd[v]["vdsat"]) / tol
        key = next((k for k in cm5 if k.lower() == name.lower()), None)
        if key:
            row["vds_circ_m5"] = cm5[key]["vds"]; row["vdsat_circ_m5"] = cm5[key]["vdsat"]; row["slack_circ_m5"] = cm5[key]["vds"] - cm5[key]["vdsat"]
            row["id_circ_m5"] = cm5[key]["id"]
        with open(OUT, "ab") as fh:
            fh.write((json.dumps(row) + "\n").encode("utf-8"))
        tot["n"] += 1; tot["band"] += row["band"]; tot["viol"] += row["viol"]
        tot["sat_dev_s5_neg"] += row.get("slack_dev_s5", 1) < 0; tot["sat_dev_m5_neg"] += row.get("slack_dev_m5", 1) < 0
        tot["sat_circ_m5_neg"] += row.get("slack_circ_m5", 1) < 0
        if "dvdsat_m5_mV" in row:
            dv_all.append((row["dvdsat_m5_mV"], row["dvdsat_m5_over_tol"], c, name))
        if row["band"] or row["viol"] or row.get("slack_circ_m5", 1) < 0.01:
            summ.append(f"  {c} {name}: slack_eng {1e3*s_eng:.2f} mV tol {1e3*tol:.3f} mV | dev s5 {1e3*row.get('slack_dev_s5', float('nan')):.2f} m5 {1e3*row.get('slack_dev_m5', float('nan')):.2f} | circ m5 {1e3*row.get('slack_circ_m5', float('nan')):.2f} mV")
dv = sorted(x[0] for x in dv_all); dr = sorted(x[1] for x in dv_all)
lines = [f"소자 {tot['n']}: 엔진 띠(0<=VDS-VDsat<tol) {tot['band']}, 엔진 위반(<0) {tot['viol']}, SPICE 소자 s5 비포화 {tot['sat_dev_s5_neg']}, m5 비포화 {tot['sat_dev_m5_neg']}, 회로 m5 비포화 {tot['sat_circ_m5_neg']}",
         f"정의 동일성(소자 m5, 같은 op 점): VDsat_eng − @m[vdsat] mV min {dv[0]:.4f} med {dv[len(dv)//2]:.4f} max {dv[-1]:.4f}; |차|/tol_VDsat max {dr[-1]:.3f} (n {len(dv)})",
         "회로 m5 여유 < 10 mV 또는 엔진 띠·위반 소자:"] + summ
(HERE / "q5_b74_band.txt").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
print("\n".join(lines))
