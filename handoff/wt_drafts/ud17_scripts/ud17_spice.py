"""UD-17 결정 자료: LUT VS 축 밖 소자의 '클램프 값 vs 실제 요청 VS 값'을 ngspice(sky130 tt, LUT 생성기와 같은 넷리스트)로 점검.

C:/g67/repo 사본의 sky130_lut_sweep.py를 모듈로 불러 _gen_netlist/_parse_output을 그대로 쓰고(수정 없이),
VGS 49점(LUT와 같은 격자) x VDS 2점(소자 vds, vds+0.0375)만 돌린다. 체크포인트는 쓰지 않는다.
입력: C:/g67/out/eval.jsonl의 F_theta_clamp / C_theta_clamp 레코드(소자 kind·L·vds·gm_id·ID·vsb).
산출: C:/g67/out/spice.jsonl -- (회로, 소자, VS)마다 gm_id 목표에서의 VGS·전류밀도(ID/W_ref)·gm/gds, 그리고 엔진 LUT(클램프) 값.
사용: python -B ud17_spice.py
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

ROOT = "C:/g67/repo"
A = os.path.join(ROOT, "skills/analog-gmid-design/assets")
sys.path.insert(0, A)
sys.path.insert(0, os.path.join(ROOT, "workspaces"))
import sky130_lut_sweep as sw  # noqa: E402

WD = "C:/g67/spice"
os.makedirs(WD, exist_ok=True)
OUT = "C:/g67/out/spice.jsonl"
W_REF = 5e-6

recs = {}
for line in open("C:/g67/out/eval.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["label"] in ("F_theta_clamp", "C_theta_clamp") and r["outcome"] == "ok":
        recs[r["circuit"]] = r

# (회로, 소자, [VS 목록]) -- 요청 vsb, 축 끝 0.8(클램프가 실제로 쓴 값), 다른 경로의 '일관된' 후보값, 추세용 점
PLAN = {
    "folded_cascode": {"M1": None, "M5": None, "M7": None},
    "current_reuse_telescopic_ota": {"M2a": None, "M9a": None, "M18a": None},
}


def vs_list(req, alt):
    s = {0.0, 0.4, 0.8, round(req, 6)}
    if alt is not None:
        s.add(round(alt, 6))
    if req > 0.8:
        s.update({1.2, 1.6} if req > 1.2 else set())
    return sorted(s)


def run(devcell, L_um, VS, vds):
    pol = 1 if devcell.startswith("nfet") else -1
    vb_sign = pol
    sw.VDS_ARR = np.array([vds, vds + 0.0375])
    sw.N_VDS = 2
    net = sw._gen_netlist(devcell, L_um, VS, vb_sign * VS * -1, pol, sw.LOD_SPICE if devcell.startswith("pfet") else "")
    tag = f"{devcell}_{L_um:.4f}_{VS:+.4f}_{vds:.4f}".replace(".", "p")
    nf, of = os.path.join(WD, tag + ".cir"), os.path.join(WD, tag + ".out")
    open(nf, "w").write(net)
    with open(of, "w") as fo:
        subprocess.run([sw.NGSPICE_EXE, "-b", nf], cwd=WD, stdout=fo, stderr=subprocess.STDOUT, timeout=600)
    ID, GM, GDS, CGG, CGD, _s = sw._parse_output(of)
    return ID[:, 0], GM[:, 0], GDS[:, 0], CGG[:, 0]


def at_gmid(vgs, ID, GM, GDS, target):
    """gm/ID 곡선의 강반전 쪽(최댓값 이후 단조감소) 가지에서 target을 지나는 VGS를 선형보간."""
    gmid = np.where(ID > 0, GM / np.maximum(ID, 1e-30), 0.0)
    k = int(np.argmax(gmid))
    for i in range(k, len(vgs) - 1):
        a, b = gmid[i], gmid[i + 1]
        if (a - target) * (b - target) <= 0 and a != b:
            t = (a - target) / (a - b)
            v = vgs[i] + t * (vgs[i + 1] - vgs[i])
            idd = math.exp(math.log(ID[i]) + t * (math.log(ID[i + 1]) - math.log(ID[i]))) / W_REF
            gg = (GM[i] / GDS[i]) + t * ((GM[i + 1] / GDS[i + 1]) - (GM[i] / GDS[i]))
            return {"vgs": v, "id_density": idd, "gm_gds": gg}
    return {"vgs": None, "id_density": None, "gm_gds": None, "gmid_max": float(gmid[k])}


def at_vgs(vgs, ID, GM, GDS, v):
    """diode-connected(VGS=VDS) 소자용: 주어진 VGS에서 gm/ID·전류밀도."""
    i = max(0, min(len(vgs) - 2, int(np.searchsorted(vgs, v)) - 1))
    t = (v - vgs[i]) / (vgs[i + 1] - vgs[i])
    idv = math.exp(math.log(max(ID[i], 1e-30)) + t * (math.log(max(ID[i + 1], 1e-30)) - math.log(max(ID[i], 1e-30))))
    gm = GM[i] + t * (GM[i + 1] - GM[i])
    return {"gm_id": gm / idv, "id_density": idv / W_REF}


import run_harness as rh  # noqa: E402

for circ, devs in PLAN.items():
    r = recs.get(circ)
    if r is None:
        print("no record", circ)
        continue
    nodes = r["nodes"]
    spec = rh.SPECS[circ]["spec_fn"]()
    vdd = spec["vdd"]
    for d in devs:
        e = r["sized"][d]
        t = r["devices"][d]
        kind = t["kind"]
        cell = "nfet_01v8" if kind == "nmos" else "pfet_01v8"
        L_um = e["L"] * 1e6
        vds = e["vds"]
        req = e["vsb"]
        # 다른 경로(충돌 상대)가 준 소스 노드 전압으로 계산한 vsb 후보
        alt = None
        for c in r["conflicts"]:
            if c["net"] == t["source"]:
                v = c["via_this"] if abs(c["existing"] - nodes[t["source"]]) < 1e-12 else c["existing"]
                alt = (vdd - v) if kind == "pmos" else v
        lut = spec["lut_by_kind"][kind]
        diode = t["gate"] == t["drain"]
        for VS in vs_list(req, alt):
            row = {"circuit": circ, "device": d, "kind": kind, "L_um": L_um, "vds": vds, "gm_id": e["gm_id"],
                   "ID": e["ID"], "W": e["W"], "vsb_req": req, "vsb_alt_other_path": alt, "VS": VS, "diode": diode}
            try:
                vg = np.array(sw.VGS_ARR)
                ID, GM, GDS, CGG = run(cell, L_um, VS, vds)
                if diode:
                    row["spice"] = at_vgs(vg, ID, GM, GDS, vds)
                else:
                    row["spice"] = at_gmid(vg, ID, GM, GDS, e["gm_id"])
                # 엔진과 같은 정규화(IDu = ID(W_ref) * L / W_ref, W = L*ID/IDu)로 맞춘다
                if row["spice"].get("id_density") is not None:
                    row["spice"]["id_density"] *= e["L"]
                # 엔진 LUT 값(이 VS를 요청했을 때 -- 0.8 초과·0 미만은 클램프)
                try:
                    if diode:
                        row["lut"] = {"gm_id": float(lut.gm_id_for_vgs(vds, e["L"], vds, VS)),
                                      "id_density": float(lut.id_density_at_vgs(vds, e["L"], vds, VS))}
                    else:
                        row["lut"] = {"vgs": float(lut.vgs_for_gm_id(e["gm_id"], e["L"], vds, VS)),
                                      "id_density": float(lut.gm_id_to_id_density(e["gm_id"], e["L"], vds, VS)),
                                      "gm_gds": float(lut.gm_gds_ratio(e["gm_id"], e["L"], vds, VS))}
                except Exception as ex:  # 측정: LUT 쪽 실패도 기록
                    row["lut_error"] = f"{type(ex).__name__}: {ex}"[:300]
            except Exception as ex:
                row["error"] = f"{type(ex).__name__}: {ex}"[:300]
            with open(OUT, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(circ, d, VS, row.get("spice"), row.get("lut"), row.get("error", ""), flush=True)
print("done")
