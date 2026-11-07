"""[JC-1] toy C -- 기준 폭 표 손 열 + 슬라이스 (interface card 20261106-jc1 §1 'toy C'). 접합 test(junction_cap·junction_source·junction_field·ss_dev)
공용 helper. 피검 함수를 부르지 않는다.

oracle (a)/(d): 기준 폭 표 열은 아래 손 식(F)이 정한 값이다. 인덱스 (l, g, d, s) = (L 축, VGS 축, VDS 축, VS 축) 위치.
  CGG = CGS + CGD + CGB = (6 + l + 2g + d + s)·1e-16 (전하 보존 항등식에 맞춤), CGD = (2 + g + d)·1e-16, CGS = (3 + g + s)·1e-16, CGB = (1 + l)·1e-16,
  CDD = (9 + l + 3g + 2d + s)·1e-16, CSS = (11 + 2l + g + d + 3s)·1e-16.
VGS 축은 0 에서 시작하지 않는다: (0.25, 0.5, 1.0) -- 슬라이스·기준 폭 표 모두. L = TOY_L, VDS = TOY_VDS, VS = TOY_VS, w_ref_m = 1e-6.
슬라이스 열은 기존 r5 toy 닫힌 식(lut/conftest R5_*)을 이 VGS 격자에서 계산한다.
"""
from __future__ import annotations

import math

import numpy as np

from lut.conftest import R5_A, R5_B, R5_C, TOY_L, TOY_VDS, TOY_VS, TOY_VS_FACTOR, ToyBuild, new_memo

from .conftest import read_rule_decl, toy_rule_decl

TOYC_VGS = (0.25, 0.5, 1.0)
W_REF = 1e-6
SHAPE = (len(TOY_L), len(TOYC_VGS), len(TOY_VDS), len(TOY_VS))


def cgs(l, g, d, s):
    return (3 + g + s) * 1e-16


def cgd(l, g, d, s):
    return (2 + g + d) * 1e-16


def cgb(l, g, d, s):
    return (1 + l) * 1e-16


def cgg(l, g, d, s):
    return (6 + l + 2 * g + d + s) * 1e-16


def cdd(l, g, d, s):
    return (9 + l + 3 * g + 2 * d + s) * 1e-16


def css(l, g, d, s):
    return (11 + 2 * l + g + d + 3 * s) * 1e-16


HAND = {"CGG": cgg, "CGD": cgd, "CGS": cgs, "CGB": cgb, "CDD": cdd, "CSS": css}


def hand_col(name):
    out = np.empty(SHAPE)
    for l in range(SHAPE[0]):
        for g in range(SHAPE[1]):
            for d in range(SHAPE[2]):
                for s in range(SHAPE[3]):
                    out[l, g, d, s] = HAND[name](l, g, d, s)
    return out


def toyc_cap_arrays(drop=(), set_node=None):
    """기준 폭 표 dict. drop = 뺄 열 이름(예 ("CDD",)), set_node = {열 이름: {(l, g, d, s): 값}} 마디 덮어쓰기."""
    cap = {"L": np.asarray(TOY_L), "VGS": np.asarray(TOYC_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
           "w_ref_m": np.float64(W_REF), "corner": np.str_("tt"), "temp_c": np.float64(27.0)}
    for name in HAND:
        if name in drop:
            continue
        a = hand_col(name)
        for node, v in (set_node or {}).get(name, {}).items():
            a[node] = v
        cap[name + "_n"] = a
    return cap


def toyc_slice_arrays(W, scale=1.0):
    """r5 toy 닫힌 식을 TOYC_VGS 에서: ID = (1e-6/L)·1e-7·exp(20v − 6v²)·exp(0.1·VDS)·(1, 0.5)[s], GM = ID·(20 − 12v), GDS = ID·0.1."""
    ID = np.empty(SHAPE)
    for iL, L in enumerate(TOY_L):
        for iG, v in enumerate(TOYC_VGS):
            for k, d in enumerate(TOY_VDS):
                for s in range(len(TOY_VS)):
                    ID[iL, iG, k, s] = ((1e-6 / L) * 1e-7 * math.exp(R5_A * v - R5_B * v * v) * math.exp(R5_C * d)
                                        * TOY_VS_FACTOR[s])
    ID = ID * scale
    GM = ID * (R5_A - 2 * R5_B * np.asarray(TOYC_VGS))[None, :, None, None]
    return {"W": np.float64(W), "L": np.asarray(TOY_L), "VGS": np.asarray(TOYC_VGS), "VDS": np.asarray(TOY_VDS),
            "VS": np.asarray(TOY_VS), "ID": ID, "GM": GM, "GDS": ID * R5_C, "VTH": np.full(ID.shape, 0.4),
            "meta_json": np.str_('{"model_files_sha256": {}}'), "corner": np.str_("tt"), "temp_c": np.float64(27.0)}


def toyc_slices(drop_vgs_in=()):
    """슬라이스 둘(폭 1 µm·2 µm). drop_vgs_in = "VGS" 키를 뺄 슬라이스 index(X 묶음)."""
    sl = [("toy_w100.npz", "toyn", toyc_slice_arrays(1e-6, 1.0)), ("toy_w200.npz", "toyn", toyc_slice_arrays(2e-6, 2.0))]
    for i in drop_vgs_in:
        del sl[i][2]["VGS"]
    return sl


def toyc_build(root, cap="default", slices=None, **kw):
    return ToyBuild(root, toyc_slices() if slices is None else slices, toyc_cap_arrays() if isinstance(cap, str) else cap, **kw)


def toyc_lut(root, cap="default", **kw):
    return toyc_build(root, cap, **kw).load()


def toyc_memo(root, cap="default", **kw):
    return new_memo(toyc_lut(root, cap, **kw))


def node_of(L, vds, vsb):
    """격자 마디 좌표 (l, d, s) -- 조회점이 마디라는 전제(값이 아니라 위치만 찾는다)."""
    return TOY_L.index(L), TOY_VDS.index(vds), TOY_VS.index(vsb)


def rule_values(tmp, line=None):
    """toy 규칙 선언을 core read_pdk_decl 로 읽은 값(a = ad_per_w, b = as_per_w, pd = pd_extra, ps = ps_extra) -- 판정 m5: 리터럴이 아니라 읽은 값."""
    from .conftest import TOY_RULE_LINE
    r = read_rule_decl(toy_rule_decl(tmp, TOY_RULE_LINE if line is None else line))
    return dict(a=r.value("lut_diffusion_ad_per_w_m"), b=r.value("lut_diffusion_as_per_w_m"),
                pd=r.value("lut_diffusion_pd_extra_m"), ps=r.value("lut_diffusion_ps_extra_m"))


def hand_junction(l, d, s, ad, as_, m, v, w_ref=W_REF):
    """J-1 식 그대로(연산 순서 고정, g = 0 마디): cdb = (CDD − CGD)·((ad·m)/(a·w_ref·1.0)), csb = (CSS − CGS)·((as·m)/(b·w_ref·1.0)).
    ad·as_ = 평가 기하 면적, m = 평가 기하 m, v = rule_values."""
    r_d = (ad * m) / (v["a"] * w_ref * 1.0)
    r_s = (as_ * m) / (v["b"] * w_ref * 1.0)
    return (cdd(l, 0, d, s) - cgd(l, 0, d, s)) * r_d, (css(l, 0, d, s) - cgs(l, 0, d, s)) * r_s
