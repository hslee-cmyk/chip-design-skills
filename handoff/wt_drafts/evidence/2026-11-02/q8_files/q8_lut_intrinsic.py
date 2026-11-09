# q8 실측 -- 물리 결정자 확인: 진성 이득 gm/gds 가 L 에 대해 어떻게 변하는가(sky130 LUT v2 r2, W_ref 5 um 표).
# 엔진 코드 불사용(LUT npz 직접 읽기, sha256 = assets/lut_v2_location.json 대조). 결과 = 케이스마다 jsonl append.
# 각 (kind, 고정 gm/ID, |VDS|, VS=0) 에서 L 격자 18점마다 gm/ID 가 목표인 VGS 를 같은 L 행 안 선형 보간으로 찾고 그 점의 gm/gds 를 낸다.
# bin 지도 = LUT meta model_bin_per_L_at_w_ref (PDK bins.csv 에서 생성기가 기록) -- 같은 bin 안 단조 여부를 함께 기록(LR3·LR4).
import hashlib, json, math, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
OUT = HERE / "q8_lut_intrinsic.jsonl"
LOC = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/lut_v2_location.json").read_text(encoding="utf-8"))
ROOT = pathlib.Path(LOC["root"]["default"])
NPZ = ROOT / LOC["files"]["cap_npz"]["path"]


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


h = hashlib.sha256(NPZ.read_bytes()).hexdigest()
ok = h == LOC["files"]["cap_npz"]["sha256"]
app({"case": "sha", "npz": str(NPZ), "sha256": h, "matches_location_json": ok})
assert ok
z = np.load(NPZ, allow_pickle=True)
meta = json.loads(str(z["meta_json"]))
Ls, VGS, VDS, VS = z["L"], z["VGS"], z["VDS"], z["VS"]
bins = meta["model_bin_per_L_at_w_ref"]


def bin_of(dev, L):
    key = ("%g" % (L * 1e6))
    e = bins[dev].get(key)
    return None if e is None else e["model"]


for dev, suf in (("nfet_01v8", "_n"), ("pfet_01v8", "_p")):
    ID, GM, GDS = z["ID" + suf], z["GM" + suf], z["GDS" + suf]
    for vds in (0.3, 0.6, 0.9):
        jd = int(np.argmin(np.abs(VDS - vds)))
        for gmid in (8.0, 12.0, 16.0, 20.0):
            rows = []
            for iL, L in enumerate(Ls):
                gi = GM[iL, :, jd, 0] / np.maximum(ID[iL, :, jd, 0], 1e-30)
                ig = GM[iL, :, jd, 0] / np.maximum(GDS[iL, :, jd, 0], 1e-30)
                val = None
                # 강반전 쪽에서 gm/ID 가 내려가는 가지(VGS 증가 방향)에서 목표와 교차하는 첫 칸
                for k in range(len(VGS) - 1):
                    if VGS[k] < 0.2:
                        continue
                    a, b = gi[k], gi[k + 1]
                    if (a - gmid) * (b - gmid) <= 0 and a != b and ID[iL, k, jd, 0] > 1e-12:
                        t = (gmid - a) / (b - a)
                        val = float(ig[k] + t * (ig[k + 1] - ig[k]))
                        vgs = float(VGS[k] + t * (VGS[k + 1] - VGS[k]))
                        break
                rows.append({"L_um": round(float(L) * 1e6, 4), "bin": bin_of(dev, float(L)),
                             "gm_gds": val, "gm_gds_db": (20 * math.log10(val) if val and val > 0 else None),
                             "vgs": (vgs if val is not None else None)})
            # 같은 bin 안 단조 / bin 경계 넘어 단조 위반 기록
            viol = []
            for a, b in zip(rows, rows[1:]):
                if a["gm_gds"] is None or b["gm_gds"] is None:
                    continue
                if b["gm_gds"] < a["gm_gds"]:
                    viol.append({"from_L": a["L_um"], "to_L": b["L_um"], "same_bin": a["bin"] == b["bin"], "drop_db": a["gm_gds_db"] - b["gm_gds_db"]})
            app({"case": "intrinsic", "device": dev, "vds_abs": float(VDS[jd]), "gm_id": gmid, "rows": rows, "nonmonotone": viol})
