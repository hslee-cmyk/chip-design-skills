"""CONTRACT 3.19 `current_box(lut_access, kind) -> (I_off, I_max)`.

기대값은 npz 배열(test 가 쓴 toy 식 / 실 LUT v2 npz)을 numpy 로 직접 읽어 계산한다:
I_off = 레이아웃 전 슬라이스의 VGS 0 면(|v| ≤ ulp(격자 끝 크기))에서 on_mask((ID>0)&(GM>0)) 이고 ID > 0 인 점의 ID 최솟값,
I_max = 그 kind 의 모든 슬라이스 on_mask 점 ID 최댓값.
"""
import hashlib
import json

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import load_lut_set
from gmid_engine.search import current_box

from sizing.conftest import DEVICE_OF, R4_GRIDS, SUFFIX, TOY_SPEC, W_M, r4_arrays

from .conftest import expect_box, new_access


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_lut(root, grids=R4_GRIDS, extra_nmos_w=None, off_vgs0=False):
    """r4 toy 식 슬라이스(nmos·pmos, 폭 W_M) + 선택: nmos 폭 extra_nmos_w 슬라이스(ID·GM·GDS × 폭 비),
    off_vgs0: VGS index 0 면 전체 GM = 0(on_mask 거짓)."""
    root.mkdir(parents=True, exist_ok=True)
    entries, arrays = [], {}
    for kind in ("nmos", "pmos"):
        offs = ()
        if off_vgs0:
            nL, _, nD, nS = (len(g) for g in grids)
            offs = tuple((a, 0, k, s) for a in range(nL) for k in range(nD) for s in range(nS))
        a = r4_arrays(kind, True, 0, offs, grids)
        arrays[(kind, W_M)] = a
        p = root / ("%s.npz" % kind)
        np.savez(p, **a)
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": _sha(p)})
        if extra_nmos_w is not None and kind == "nmos":
            b = dict(a)
            k = extra_nmos_w / W_M
            b.update(W=np.float64(extra_nmos_w), ID=a["ID"] * k, GM=a["GM"] * k, GDS=a["GDS"] * k)
            arrays[(kind, extra_nmos_w)] = b
            p2 = root / "nmos_w2.npz"
            np.savez(p2, **b)
            entries.append({"device": DEVICE_OF[kind], "file": p2.name, "sha256": _sha(p2)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0)}
    for kind in ("nmos", "pmos"):
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    np.savez(root / "cap.npz", **cap)
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC), arrays


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_toy_box(tmp_path, kind):
    lut, arrs = write_lut(tmp_path / "l")
    got = current_box(new_access(lut), kind)
    exp = expect_box(arrs[(kind, W_M)], [arrs[(kind, W_M)]])
    assert got == pytest.approx(exp, rel=1e-12)
    # 손 확인: VGS=0 면 최소 = L 최대·VDS 최소·|VS| 최대, 최대 = L 최소·VGS 최대(B/C > 2.0)·VDS 최대·VS 0.
    assert got[0] < got[1]


def test_imax_spans_all_slices_ioff_only_pre_layout(tmp_path):
    lut, arrs = write_lut(tmp_path / "l", extra_nmos_w=2 * W_M)
    got = current_box(new_access(lut), "nmos")
    exp = expect_box(arrs[("nmos", W_M)], [arrs[("nmos", W_M)], arrs[("nmos", 2 * W_M)]])
    assert got == pytest.approx(exp, rel=1e-12)
    single = expect_box(arrs[("nmos", W_M)], [arrs[("nmos", W_M)]])
    assert got[1] == pytest.approx(2 * single[1], rel=1e-12)       # 넓은 슬라이스 ID = 2 배
    assert got[0] == pytest.approx(single[0], rel=1e-12)            # I_off 는 레이아웃 전 슬라이스만


def test_vgs_zero_within_ulp_counts(tmp_path):
    L, G, D, S = R4_GRIDS
    g2 = (L, (1e-17,) + tuple(G[1:]), D, S)              # |1e-17| ≤ ulp(2.0)
    lut, arrs = write_lut(tmp_path / "l", grids=g2)
    got = current_box(new_access(lut), "nmos")
    assert got == pytest.approx(expect_box(arrs[("nmos", W_M)], [arrs[("nmos", W_M)]]), rel=1e-12)


def test_no_vgs_zero_rejected(tmp_path):
    L, G, D, S = R4_GRIDS
    lut, _ = write_lut(tmp_path / "l", grids=(L, tuple(G[1:]), D, S))
    with pytest.raises(SchemaRejectedError) as e:
        current_box(new_access(lut), "nmos")
    assert dict(e.value.record.detail)["reason"] == "lut_vgs_zero_missing"


def test_no_valid_point_rejected(tmp_path):
    lut, _ = write_lut(tmp_path / "l", off_vgs0=True)
    with pytest.raises(SchemaRejectedError) as e:
        current_box(new_access(lut), "nmos")
    assert dict(e.value.record.detail)["reason"] == "lut_current_box_empty"


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_real_lut_v2(real_lut_v2, kind):
    """실 LUT v2: npz 를 직접 읽어 같은 정의로 계산(데이터 없으면 fixture 가 FAIL)."""
    lut, files = real_lut_v2
    acc = new_access(lut)
    wk = dict(acc.w_keys)[kind]
    arrs = {}
    for (k, w), p in files.items():
        if k == kind:
            with np.load(p) as z:
                arrs[w] = {"VGS": np.array(z["VGS"]), "ID": np.array(z["ID"]), "GM": np.array(z["GM"])}
    exp = expect_box(arrs[wk], list(arrs.values()))
    assert current_box(acc, kind) == pytest.approx(exp, rel=1e-12)
