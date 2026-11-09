# q8 손계산(LUT 직접, 엔진 코드 불사용) -- ngcc_3stage_ff 블록 이득을 L 지도별로 닫힌 식으로 계산해 엔진 국소 모델 값·SPICE 와 대조한다.
# 블록 식(연결에서 유도 -- icmr4 ngcc 분석 §1.2 와 같은 연결): A1 = gm2/(gds2+gds4), A2 = (gm8/gm9)*gm10/(gds10+gds11) ~ gm10/(gds10+gds11) (미러 1:1),
#   A3 = gm13/(gds13+gds12). FF 경로(M6·M7·M14)와 body 효과는 뺌(DC 주경로 곱 -- 손계산 수준).
# gm/ID = 손 사이징 시험점 값(icmr4 ngcc §3.2: pfet 입력 15, 그 밖 pfet 10, nfet 부하 10, nfet CS 12 -- 측정 매개변수), |VDS| = 0.6 V 격자, VS = 0.
# L 이 LUT 점 사이면 같은 bin 안 이웃 두 점 선형 보간(LR3), bin 경계 넘음 0. sha256 대조. 케이스마다 jsonl append.
import hashlib, json, math, pathlib
import numpy as np

HERE = pathlib.Path(__file__).parent
OUT = HERE / "q8_lut_blockgain.jsonl"
LOC = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/lut_v2_location.json").read_text(encoding="utf-8"))
NPZ = pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"]
assert hashlib.sha256(NPZ.read_bytes()).hexdigest() == LOC["files"]["cap_npz"]["sha256"]
z = np.load(NPZ, allow_pickle=True)
meta = json.loads(str(z["meta_json"]))
Ls, VGS, VDS = z["L"], z["VGS"], z["VDS"]
BINS = meta["model_bin_per_L_at_w_ref"]
JD = int(np.argmin(np.abs(VDS - 0.6)))


def app(rec):
    with open(OUT, "ab") as fh:
        fh.write((json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8"))


def at_grid(suf, iL, gmid):
    ID, GM, GDS = z["ID" + suf][iL, :, JD, 0], z["GM" + suf][iL, :, JD, 0], z["GDS" + suf][iL, :, JD, 0]
    gi = GM / np.maximum(ID, 1e-30)
    for k in range(len(VGS) - 1):
        if VGS[k] < 0.2 or ID[k] <= 1e-12:
            continue
        a, b = gi[k], gi[k + 1]
        if (a - gmid) * (b - gmid) <= 0 and a != b:
            t = (gmid - a) / (b - a)
            gm_over_id = gmid
            gds_over_id = (GDS[k] / ID[k]) + t * ((GDS[k + 1] / ID[k + 1]) - (GDS[k] / ID[k]))
            return gm_over_id, gds_over_id
    return None


def dev(kind, L, gmid):
    """(gm/ID, gds/ID) at L -- 같은 bin 안 선형 보간."""
    suf = "_n" if kind == "n" else "_p"
    name = "nfet_01v8" if kind == "n" else "pfet_01v8"
    bin_of = lambda x: BINS[name]["%g" % (x * 1e6)]["model"]
    idx = [i for i, x in enumerate(Ls) if abs(x - L) < 1e-12]
    if idx:
        return at_grid(suf, idx[0], gmid)
    lo = max(i for i, x in enumerate(Ls) if x < L)
    hi = lo + 1
    if bin_of(Ls[lo]) != bin_of(Ls[hi]):
        # 경계값 L 은 아래 bin 소속(LR3) -- 위쪽 점이 다른 bin 이면 보간 거부
        return None
    a, b = at_grid(suf, lo, gmid), at_grid(suf, hi, gmid)
    t = (L - Ls[lo]) / (Ls[hi] - Ls[lo])
    return (gmid, a[1] + t * (b[1] - a[1]))


def blocks(Lm):
    g = {"M2": ("p", 15.0), "M4": ("n", 10.0), "M10": ("p", 10.0), "M11": ("n", 10.0), "M13": ("n", 12.0), "M12": ("p", 10.0)}
    v = {n: dev(k, Lm[n], gm) for n, (k, gm) in g.items()}
    # 같은 전류 가지: gm/(gds_a + gds_b) = (gm/ID)_a / ((gds/ID)_a + (gds/ID)_b)
    A1 = v["M2"][0] / (v["M2"][1] + v["M4"][1])
    A2 = v["M10"][0] / (v["M10"][1] + v["M11"][1])
    A3 = v["M13"][0] / (v["M13"][1] + v["M12"][1])
    db = [20 * math.log10(x) for x in (A1, A2, A3)]
    return {"A1_db": db[0], "A2_db": db[1], "A3_db": db[2], "total_db": sum(db)}


member = {"M2": "M2", "M4": "M3", "M10": "M9", "M11": "M11", "M13": "M13", "M12": "M0"}
maps = {
    "uniform_0.15": {k: 0.15e-6 for k in member},
    "ga_start (engine q8 ga rung0)": {"M2": 0.4948e-6, "M4": 0.4948e-6, "M10": 0.9415e-6, "M11": 0.9415e-6, "M13": 0.4092e-6, "M12": 0.4948e-6},
    "ga_cell_top": {"M2": 0.5e-6, "M4": 0.5e-6, "M10": 1.0e-6, "M11": 1.0e-6, "M13": 0.5e-6, "M12": 0.5e-6},
    "uniform_0.5": {k: 0.5e-6 for k in member},
    "uniform_1.0": {k: 1.0e-6 for k in member},
}
app({"case": "src", "npz": str(NPZ), "vds_grid_v": float(VDS[JD])})
for name, Lm in maps.items():
    app(dict({"case": "ngcc_blocks", "map": name, "L_um": {k: v * 1e6 for k, v in Lm.items()}}, **blocks(Lm)))
    print(name, blocks(Lm))
