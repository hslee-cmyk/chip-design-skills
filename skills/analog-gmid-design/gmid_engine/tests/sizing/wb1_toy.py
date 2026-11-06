"""WB-1 sizing 합성 LUT -- 슬라이스 여럿 + bin 선언 (interface card §3 D-1, §4). 기존 `write_r4_lut` 와 같은 r4 식을 쓰되
폭 슬라이스를 여러 장 쓴다: 폭 W 슬라이스의 ID·GM·GDS = 기준 폭 값 × (W / 1e-6) (IDu 는 슬라이스와 무관).
oracle (a): 기준 식은 sizing conftest 의 r4 닫힌 식(`r4_arrays`)이다. 모델 파일·선언은 `toy_bins.write_toy_bins`.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

from gmid_engine.lut import LutMemo, load_lut_set
from gmid_engine.sizing import LutAccess
from toy_bins import write_toy_bins

from .conftest import (DEVICE_OF, GRID_M, R4_GRIDS, R4_L, SUFFIX, TOY_SPEC, W_M, _sha, r4_arrays)


# [JC-1] 접합 항 입력 열(기준 폭 표 CGS·CDD·CSS) 합성 상수 -- 모든 축 같은 값. 접합 기대값 = (CDD − CGD)·r = 3e-16·r, (CSS − CGS)·r = 5e-16·r (손 계산).
JC1_CGS, JC1_CDD, JC1_CSS = 8e-16, 5e-16, 1.3e-15
JC1_CGD = 2e-16            # 이 파일 생성기가 모든 칸에 쓰는 CGD 값(아래 `np.full(shp, 2e-16)`와 같은 수)


def write_r4_bins_lut(root, widths=(1e-6, 2e-6), rule="lower", grids=R4_GRIDS, vdsat=("nmos", "pmos"), cap_vdsat=(),
                      kinds=("nmos", "pmos"), l_anchors=None, simulator="ngspice-46", idu_factor=None, jc1_cols=False):
    """-> (LutSet, 폴더, write_toy_bins 반환). 기준 폭 = W_M(1e-6, cap 의 w_ref_m). widths 에 W_M 이 있어야 한다.
    idu_factor = {폭: 배율} -- 그 폭 슬라이스의 ID·GM·GDS 에 폭 비 말고 배율을 더 곱한다(IDu 가 슬라이스마다 달라진다, interface M-5). 기본 비례.
    jc1_cols: [JC-1] 기준 폭 표에 CGS·CDD·CSS 열을 더한다(ss_dev 접합 항 입력). 기본 False = 기존 호출 불변(E-18 CDD 열 부재 시험 등)."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    l_anchors = tuple(l_anchors or grids[0])
    tb = write_toy_bins(root, kinds, l_anchors, widths, rule=rule, simulator=simulator, grid_m=GRID_M)
    entries = []
    for kind in kinds:
        for W in widths:
            a = r4_arrays(kind, kind in vdsat, 0, (), grids)
            k = W / W_M * dict(idu_factor or {}).get(W, 1.0)
            a.update(W=np.float64(W), ID=a["ID"] * k, GM=a["GM"] * k, GDS=a["GDS"] * k)
            a["meta_json"] = np.str_(json.dumps(tb.meta(kind)))
            name = "r4_%s.npz" % kind if W == widths[0] else "r4_%s_w%d.npz" % (kind, round(W / GRID_M))
            p = root / name
            np.savez(p, **a)
            entries.append({"device": DEVICE_OF[kind], "file": name, "sha256": _sha(p)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0),
           "meta_json": np.str_(json.dumps({"pdk_root": tb.pdk_root, "ngspice": tb.simulator,
                                            "model_files_sha256": {kind: tb.meta(kind)["model_files_sha256"]
                                                                   for kind in kinds}}))}
    for kind in kinds:
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
        if jc1_cols:
            cap["CGS" + SUFFIX[kind]] = np.full(shp, JC1_CGS)
            cap["CDD" + SUFFIX[kind]] = np.full(shp, JC1_CDD)
            cap["CSS" + SUFFIX[kind]] = np.full(shp, JC1_CSS)
    for kind in cap_vdsat:
        cap["VDSAT" + SUFFIX[kind]] = r4_arrays(kind, True, 0, (), grids)["VDSAT"]
    np.savez(root / "cap.npz", **cap)
    lut = load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC, bin_rule=tb.bin_rule)
    return lut, root, tb


def access_of(lut, n=4096):
    return LutAccess(LutMemo(lut, point=n, curve=n, root=n))
