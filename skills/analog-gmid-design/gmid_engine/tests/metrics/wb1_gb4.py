"""WB-1 GB4 합성 LUT -- 슬라이스 여럿 + bin 선언 (interface card §4·§5 E-1~E-7). 입력 helper 와 독립 계산(oracle (a))만 둔다.

`gb4_hand.write_lut` 는 옛 서명(bin_rule 없음)이라 쓰지 않는다(기존 fixture 이행은 이 card 범위 밖). 슬라이스 배열은 `gb4_hand.slice_arrays` 꼴을 쓰되
슬라이스마다 (LAM, z 배율)을 바꾼다. 로더의 1.4 단위 검사(현 기울기 = GDS/ID, GMBS/ID)가 맞도록 ID 의 VDS·VS 의존성도 같이 바꾼다:
    ID = (w/L)·I0·exp(f(VGS) + lam·VDS − A·zs·VS²),  GM = ID·f'(VGS),  GDS = ID·lam,  GMBS = ID·2A·zs·VS
그래서 격자 마디에서 x = gm/ID = f'(VGS), y = gds/ID = lam, z = gmb/ID = 2A·zs·VS 가 닫힌 식이다.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from toy_bins import lf_sha, write_toy_bins

from . import gb4_hand as G


def slice_arrays_lz(kind, w, lam, zs, gmbs=True):
    a = G.slice_arrays(kind, G.GRIDS, w, 1.0, G.f_default, G.fp_default, gmbs, None, ())
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in G.GRIDS)
    Lg, Gv, D, S = gL[:, None, None, None], gG[None, :, None, None], gD[None, None, :, None], gS[None, None, None, :]
    ID = (w / Lg) * G.I0[kind] * np.exp(G.f_default(Gv) + lam * D - G.A * zs * S * S)
    a["ID"] = ID
    a["GM"] = ID * G.fp_default(Gv)
    a["GDS"] = ID * lam
    if gmbs:
        a["GMBS"] = ID * (2.0 * G.A * zs * S)
    return a


def write_slice_lut(root, slices, gmbs=True, no_bins=False, simulator="ngspice-46"):
    """slices = ((폭, lam, zs), ...) -- nmos·pmos 가 같은 슬라이스 표를 갖는다. no_bins = 모델 파일에 bin 블록이 없다(빈 bin 지도). -> LutSet."""
    from gmid_engine.lut import LutSpec, load_lut_set
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    widths = tuple(sorted({w for w, _, _ in slices}))
    tb = write_toy_bins(root, G.KINDS, G.L_GRID, widths, simulator=simulator, grid_m=G.GRID_M)
    shas = dict(tb.shas)
    if no_bins:
        for kind in G.KINDS:
            p = Path(tb.pdk_root) / tb.rels[kind]
            data = (".model %s__plain %s\n+ level = 54 vth0 = 0.4\n" % (G.DEVICE_OF[kind], kind)).encode("utf-8")
            p.write_bytes(data)
            shas[kind] = hashlib.sha256(data).hexdigest()
        decl = json.loads(Path(tb.bin_rule).read_text(encoding="utf-8"))
        decl["model_files_sha256"] = sorted({lf_sha((Path(tb.pdk_root) / r).read_bytes()) for r in tb.rels.values()})
        Path(tb.bin_rule).write_bytes(json.dumps(decl, indent=1).encode("utf-8"))

    def meta(kind):
        return {"pdk_root": tb.pdk_root, "model_files_sha256": {tb.rels[kind]: shas[kind]}, "ngspice": simulator}
    entries = []
    for i, (w, lam, zs) in enumerate(slices):
        for kind in G.KINDS:
            a = slice_arrays_lz(kind, w, lam, zs, gmbs)
            a["meta_json"] = np.str_(json.dumps(meta(kind)))
            name = "s%d_%s.npz" % (i, kind)
            p = root / name
            np.savez(p, **a)
            entries.append({"device": G.DEVICE_OF[kind], "file": name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in G.GRIDS)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(G.W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0),
           "meta_json": np.str_(json.dumps({"pdk_root": tb.pdk_root, "ngspice": simulator,
                                            "model_files_sha256": {k: meta(k)["model_files_sha256"] for k in G.KINDS}}))}
    for kind in G.KINDS:
        cap["CGG" + G.SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + G.SUFFIX[kind]] = np.full(shp, 2e-16)
        # [JC-1] 접합 항 입력 열(손 식: CGS = CGG − CGD = 8e-16, CSS − CGS = 5e-16, CDD − CGD = 3e-16 -- 모든 칸 같은 값)
        cap["CGS" + G.SUFFIX[kind]] = np.full(shp, 8e-16)
        cap["CSS" + G.SUFFIX[kind]] = np.full(shp, 1.3e-15)
        cap["CDD" + G.SUFFIX[kind]] = np.full(shp, 5e-16)
    np.savez(root / "cap.npz", **cap)
    spec = LutSpec(G.GRID_M, (("nmos", G.W_M), ("pmos", G.W_M)), (("toyn", "nmos"), ("toyp", "pmos")),
                   (("nmos", "_n"), ("pmos", "_p")))
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), spec, bin_rule=tb.bin_rule)


def all_index(grids=G.GRIDS):
    nl, ng, nd, ns = (len(g) for g in grids)
    il, iv, idd, iss = np.meshgrid(np.arange(nl), np.arange(ng), np.arange(nd), np.arange(ns), indexing="ij")
    return il.ravel(), idd.ravel(), iss.ravel(), iv.ravel()


def follower_amax(y, zfun):
    """소스 팔로워 gain x/(x + y + z) 의 격자 전수 최댓값(독립 numpy). x = f'(VGS), z = zfun(VS). -> 선형 비."""
    best = -np.inf
    for g in G.VGS_GRID:
        for s in G.VS_GRID:
            x = G.fp_default(g)
            best = max(best, x / (x + y + zfun(s)))
    return best
