"""e_m 재분석 실측 1: LUT 보간 분해능(격자 간격이 만드는 오차)과 gmbs 생략 크기.

용도: e_m 물리 출처 분해(LUT 보간 대 손계산 근사)의 크기 비교. 엔진 코드를 읽지 않는다.
가정: 축별 선형 보간(엔진 보간 방식은 확인하지 않음 -- 보고서에 표지).
방법: 내부 격자점 k에서 이웃 k-1, k+1(간격 2h) 선형 보간값과 실제값을 비교하고,
     선형 보간 오차 ~ h^2 |f''| / 8 이므로 간격 h 중점 오차 추정 = (간격 2h 오차) / 4.
영역: 포화(VDS >= VDSAT + 2 격자), gm/ID 4~25 /V, ID > 1 nA.
결과는 케이스마다 append(원칙 30).
"""
import json
import sys
import numpy as np

LUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_fd_pr__{dev}__tt__W1p0000um_dc.npz"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-29/em_reanalysis/lut_interp_error.jsonl"


def stats(x):
    x = np.abs(x[np.isfinite(x)])
    if x.size == 0:
        return None
    return {"n": int(x.size), "p50": float(np.percentile(x, 50)), "p95": float(np.percentile(x, 95)),
            "max": float(x.max())}


def run(dev):
    d = np.load(LUT.format(dev=dev), allow_pickle=False)
    ID, GM, GDS, GMBS, VDSAT = (d[k] for k in ("ID", "GM", "GDS", "GMBS", "VDSAT"))
    VDS = d["VDS"]
    L = d["L"]
    q = {"ID": ID, "GM": GM, "GDS": GDS, "gm_id": GM / np.where(ID > 0, ID, np.nan),
         "gm_gds": GM / np.where(GDS > 0, GDS, np.nan)}
    gmid = q["gm_id"]
    vds_grid = VDS[None, None, :, None] * np.ones_like(ID)
    h_vds = VDS[1] - VDS[0]
    region = (ID > 1e-9) & (gmid >= 4) & (gmid <= 25) & (vds_grid >= VDSAT + 2 * h_vds)
    res = {"device": dev, "L_um": [float(x * 1e6) for x in L]}
    for ax, name in ((1, "VGS"), (2, "VDS"), (3, "VS")):
        res[name] = {}
        for k, f in q.items():
            fm = np.take(f, range(0, f.shape[ax] - 2), axis=ax)
            f0 = np.take(f, range(1, f.shape[ax] - 1), axis=ax)
            fp = np.take(f, range(2, f.shape[ax]), axis=ax)
            reg = np.take(region, range(1, f.shape[ax] - 1), axis=ax)
            rel2h = ((fm + fp) / 2 - f0) / f0
            res[name][k] = stats(rel2h[reg] / 4.0)  # 간격 h 중점 추정
    # gmbs/gm 크기(손계산이 gmbs를 생략할 때의 상대 크기)
    eta = GMBS / np.where(GM > 0, GM, np.nan)
    res["gmbs_over_gm"] = {}
    VS = d["VS"]
    for j, vs in enumerate(VS):
        if vs > 1.0:
            break
        sel = region[..., j]
        res["gmbs_over_gm"][f"VS={vs:.1f}"] = stats(eta[..., j][sel])
    with open(OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(res, ensure_ascii=False) + "\n")
    return res


if __name__ == "__main__":
    for dev in sys.argv[1:] or ["nfet_01v8", "pfet_01v8"]:
        r = run(dev)
        print(dev)
        for name in ("VGS", "VDS", "VS"):
            for k, v in r[name].items():
                print(f"  {name:4s} {k:7s} {v}")
        for k, v in r["gmbs_over_gm"].items():
            print("  gmbs/gm", k, v)
