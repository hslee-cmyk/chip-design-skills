"""[r7 2026-10-09 2차 follow-up] 기울기 열 단위 검사 -- lut CONTRACT 1.4 개정, 설계 41 §4.1 '단위 불일치 -> 로드 거부'.

규칙(계약 1.4 문장): 격자 칸 [x0, x1] 에서 ln ID 의 현 기울기 Δln ID/Δx 가 두 끝 기울기 m0·m1(저장 열, 부호 규약 GM/ID·GDS/ID +,
GMBS/ID −) 의 [min, max] 밖(허용분 eps·(|y0| + |y1|)/Δx + eps·(|m0| + |m1|) 밖)인 칸의 비율을 열마다 재고, 정의 마스크가 두 끝에서
참인 칸의 **과반**이 모순이면 `lut_unit_mismatch`(detail `path, column, cells_outside, cells`). 열 = GM(VGS 축)·GDS(VDS 축)·GMBS(VS 축).
정의 마스크 = 1.4 의 `on_mask`(ID > 0 ∧ GM > 0)·`vds_slope_ok`(ID > 0 ∧ GDS > 0)·`vs_slope_ok`(GMBS/ID 유한·양수).

oracle:
- (a) 구성: toy 슬라이스 -- 정의 칸 수·모순 칸 수가 닫힌 식으로 정해진다(각 test 의 손계산).
- (b) 독립 구현: 이 파일의 `_outside_counts`(npz 배열을 numpy 로 직접 -- 엔진 함수·엔진 배열 미사용)가 계약 문장대로 센다.
  실데이터 32 슬라이스 전수와 엔진 거부 detail 의 (cells_outside, cells) 를 이것과 대조한다.
- (d) 계약 선언: 판정선 = 과반(1/2 초과, '과반'). 정확히 절반은 과반이 아니다.
"""
import json
import math
import shutil
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutSpec, load_lut_set

from .conftest import (REAL_CAP_SUFFIX, REAL_DEVICE_KINDS, TOY_L, TOY_VDS, TOY_VS_FACTOR, _toy_dict,
                       detail_of, sha256_file, toy_slice_arrays, vs_toy_slices)

EPS = np.finfo(float).eps
COLUMN_AXIS = {"GM": (1, "VGS", 1.0), "GDS": (2, "VDS", 1.0), "GMBS": (3, "VS", -1.0)}
# 척도 오류 후보: SI 접두(10³)·rad/s↔Hz(2π)·log10↔ln(ln10)·배수 2 와 그 역수(설계 41 §4.1 '단위 불일치')
SCALE_FACTORS = (2.0, 2.0 * math.pi, math.log(10.0), 1000.0, 0.5, 1.0 / (2.0 * math.pi), 1.0 / math.log(10.0), 1e-3)
SCALE_IDS = ("x2", "x2pi", "xln10", "x1000", "x1/2", "x1/2pi", "x1/ln10", "x1/1000")


def _outside_counts(z, col, factor=1.0):
    """계약 1.4 단위 검사의 독립 구현 -> (모순 칸 수, 정의 칸 수). z = 슬라이스 배열 dict, factor = 그 열에 곱할 척도."""
    ax, gname, sign = COLUMN_AXIS[col]
    ID = np.asarray(z["ID"], dtype=float)
    C = np.asarray(z[col], dtype=float) * factor
    pos = ID > 0
    safe = np.where(pos, ID, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(pos, C / safe, np.nan)
    y = np.where(pos, np.log(safe), np.nan)
    defined = pos & np.isfinite(ratio) & (ratio > 0)
    m = sign * ratio
    n = ID.shape[ax]
    lo_i = tuple(slice(0, n - 1) if a == ax else slice(None) for a in range(4))
    hi_i = tuple(slice(1, n) if a == ax else slice(None) for a in range(4))
    dx = np.diff(np.asarray(z[gname], dtype=float)).reshape(tuple(n - 1 if a == ax else 1 for a in range(4)))
    y0, y1, m0, m1 = y[lo_i], y[hi_i], m[lo_i], m[hi_i]
    both = defined[lo_i] & defined[hi_i]
    with np.errstate(invalid="ignore"):
        chord = (y1 - y0) / dx
        tol = EPS * (np.abs(y0) + np.abs(y1)) / dx + EPS * (np.abs(m0) + np.abs(m1))
        out = both & ((chord < np.minimum(m0, m1) - tol) | (chord > np.maximum(m0, m1) + tol))
    return int(out.sum()), int(both.sum())


def _scaled(arrays, col, factor):
    a = dict(arrays)
    a[col] = np.asarray(arrays[col]) * factor
    return a


def _reject(build):
    with pytest.raises(SchemaRejectedError) as ei:
        build.load()
    return detail_of(ei.value)


# ---------------------------------------------------------------------------
# toy: 열마다 척도 오류 -> 거부 (a) + 독립 구현 대조 (b)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("factor", SCALE_FACTORS, ids=SCALE_IDS)
@pytest.mark.parametrize("col", ["GM", "GDS"])
def test_toy_scaled_gm_gds_rejected(toy_build, col, factor):
    """r5 toy(CONTRACT 7.1: ln ID = VGS 2차식 + 0.1·VDS) 의 폭 2e-6 슬라이스 한 장만 열 × factor.
    손계산(oracle (a)): GM -- VGS 칸 [0, 0.5]·[0.5, 1] 의 현 = 칸 중앙 미분 17·11, 끝 기울기 f·(20, 14)·f·(14, 8) -> f ∈ 위 8 개면 두 칸 모두
    밖 -> 정의 칸 3 L × 2 VDS × 2 VS × 2 = 24 개 전부 모순. GDS -- 현 0.1, 끝 기울기 0.1·f(상수) -> 3 × 3 VGS × 2 VS × 1 = 18 개 전부 모순.
    detail path = 바꾼 슬라이스."""
    a = toy_slice_arrays(1e-6, 1.0)
    b = _scaled(toy_slice_arrays(2e-6, 2.0), col, factor)
    n_cells = 24 if col == "GM" else 18
    assert _outside_counts(b, col) == (n_cells, n_cells)                  # (b) 독립 구현도 같은 수
    assert _outside_counts(a, col) == (0, n_cells)                        # 바꾸지 않은 슬라이스는 모순 0
    d = _reject(toy_build("sc_%s" % col, slices=[("toy_w100.npz", "toyn", a), ("toy_w200.npz", "toyn", b)]))
    assert d["reason"] == "lut_unit_mismatch" and d["column"] == col
    assert (d["cells_outside"], d["cells"]) == (n_cells, n_cells)
    assert Path(d["path"]).name == "toy_w200.npz"


@pytest.mark.parametrize("factor", SCALE_FACTORS, ids=SCALE_IDS)
def test_toy_scaled_gmbs_rejected(toy_build, factor):
    """vs toy(conftest: ln ID 의 VS 몫 −s − s², GMBS/ID = 1 + 2s) 폭 1e-6 슬라이스의 GMBS × factor.
    손계산(oracle (a)): VS 칸 [0, 0.5] 현 −1.5, 끝 기울기 −f·(1, 2) -> f ∈ 위 8 개면 밖 -> 3 L × 3 VGS × 2 VDS × 1 = 18 개 전부 모순."""
    sl = vs_toy_slices()
    sl[0] = (sl[0][0], sl[0][1], _scaled(sl[0][2], "GMBS", factor))
    assert _outside_counts(sl[0][2], "GMBS") == (18, 18)
    assert _outside_counts(sl[1][2], "GMBS") == (0, 18)
    d = _reject(toy_build("sc_gmbs", slices=sl))
    assert d["reason"] == "lut_unit_mismatch" and d["column"] == "GMBS"
    assert (d["cells_outside"], d["cells"]) == (18, 18)
    assert Path(d["path"]).name == "vs_w100.npz"


def test_toy_consistent_columns_load(toy_build):
    """음성 대조: 같은 toy 를 바꾸지 않으면 세 열 모두 모순 0(독립 구현) -- 로드된다."""
    for a in (toy_slice_arrays(1e-6, 1.0), toy_slice_arrays(2e-6, 2.0)):
        assert _outside_counts(a, "GM") == (0, 24) and _outside_counts(a, "GDS") == (0, 18)
    toy_build("plain").load()
    for _, _, a in vs_toy_slices():
        assert _outside_counts(a, "GMBS") == (0, 18)
    toy_build("vs", slices=vs_toy_slices()).load()


# ---------------------------------------------------------------------------
# 판정선 = 과반 (d): 정확히 절반은 로드, 절반 + 1 칸은 거부
# ---------------------------------------------------------------------------

HALF_ID_VGS = (1e-7, 1e-6, 1e-5)
HALF_GM_ID = (20.0, 10.0, 4.0)


def _half_slice(W, scale, gm_id_edit=None):
    """경계 toy(oracle (a) 구성): ID = (1e-6/L)·(1e-7, 1e-6, 1e-5)[VGS]·e^(0.1·VDS)·(1, 0.5)[VS], GM/ID = (20, 10, 4), GDS = 0.1·ID.
    VGS 칸 0: 현 ln10/0.5 = 4.61 ∉ [10, 20] -> 모순, 칸 1: 4.61 ∈ [4, 10] -> 일관. 정의 칸 24 개(3 L × 2 VDS × 2 VS × 2) 중 12 개 모순
    = 정확히 절반. GDS 는 ln ID 의 VDS 몫 0.1·VDS 와 같은 기울기(일관). gm_id_edit = (iL, k, s, 마디, 새 GM/ID) 로 한 곡선의 마디 하나를 바꾼다."""
    ID = np.empty((3, 3, 2, 2))
    for iL, L in enumerate(TOY_L):
        for iG in range(3):
            for k, d in enumerate(TOY_VDS):
                for s in range(2):
                    ID[iL, iG, k, s] = (1e-6 / L) * HALF_ID_VGS[iG] * math.exp(0.1 * d) * TOY_VS_FACTOR[s] * scale
    g = np.empty_like(ID)
    g[...] = np.asarray(HALF_GM_ID)[None, :, None, None]
    if gm_id_edit is not None:
        iL, k, s, node, val = gm_id_edit
        g[iL, node, k, s] = val
    return _toy_dict(W, ID, ID * g, ID * 0.1)


@pytest.mark.parametrize("edit,outside,rejected", [
    (None, 12, False),                         # 정확히 절반(12/24) -- 과반 아님 -> 로드
    ((0, 0, 0, 2, 6.0), 13, True),             # 한 곡선 칸 1 의 끝 기울기 (10, 6): 현 4.61 ∉ [6, 10] -> 13/24 과반 -> 거부
    ((0, 0, 0, 0, 4.0), 11, False),            # 한 곡선 칸 0 의 끝 기울기 (4, 10): 현 4.61 ∈ [4, 10] -> 11/24 -> 로드
], ids=["half", "half_plus_one", "half_minus_one"])
def test_majority_boundary(toy_build, edit, outside, rejected):
    a = _half_slice(1e-6, 1.0, edit)
    b = _half_slice(2e-6, 2.0)
    assert _outside_counts(a, "GM") == (outside, 24)                       # (b) 구성의 모순 수 확인
    assert _outside_counts(b, "GM") == (12, 24)
    assert _outside_counts(a, "GDS")[0] == 0 == _outside_counts(b, "GDS")[0]
    build = toy_build("half_%s" % outside, slices=[("h_w100.npz", "toyn", a), ("h_w200.npz", "toyn", b)])
    if rejected:
        d = _reject(build)
        assert d["reason"] == "lut_unit_mismatch" and d["column"] == "GM"
        assert (d["cells_outside"], d["cells"]) == (outside, 24)
        assert Path(d["path"]).name == "h_w100.npz"
    else:
        lut = build.load()
        assert set(lut.slice_map) == {("nmos", 100), ("nmos", 200)}


# ---------------------------------------------------------------------------
# 실데이터 (b): LUT v2 32 슬라이스 전수 -- 정상 열은 과반 미만, 척도 오류 열은 과반 초과
# ---------------------------------------------------------------------------

def _real_arrays(path):
    with np.load(path) as z:
        return {k: np.array(z[k]) for k in ("ID", "GM", "GDS", "GMBS", "VGS", "VDS", "VS")}


@pytest.mark.lut_realdata
def test_real_columns_below_half_and_scaled_above_half(real_lut, real_slice_files):
    """(b) 독립 구현으로 32 슬라이스 × 세 열: 저장 그대로는 모순 칸이 과반 미만(엔진도 로드했다 -- real_lut), 위 8 개 척도를 곱하면
    모든 슬라이스에서 과반 초과(이 규칙이 그 척도 오류를 놓치지 않는다). 판정선 1/2 은 계약 선언(d) -- 측정값을 기준으로 쓰지 않는다."""
    assert len(real_slice_files) == 32
    for kind, _, _, wk, path in real_slice_files:
        assert (kind, wk) in real_lut.slice_map
        z = _real_arrays(path)
        for col in COLUMN_AXIS:
            o, n = _outside_counts(z, col)
            assert n > 0 and 2 * o < n, (kind, wk, col, o, n)
            for f, fid in zip(SCALE_FACTORS, SCALE_IDS):
                o, n = _outside_counts(z, col, f)
                assert 2 * o > n, (kind, wk, col, fid, o, n)


def _real_two_slice_lut(root, real_paths, real_manifest, edit=None):
    """실데이터 폭 키 1000(W 5 µm) nmos·pmos 슬라이스 두 장으로 작은 LUT 를 tmp 에 만든다(manifest = 1.2 형식, sha256 재계산).
    edit = (device, column, factor): 그 장의 열 × factor."""
    base = Path(real_paths["manifest"]).parent
    pick = [s for s in real_manifest["slices"] if abs(float(s["w_um"]) - 5.0) <= 1e-12]
    assert sorted(s["device"] for s in pick) == ["nfet_01v8", "pfet_01v8"]
    root.mkdir(parents=True)
    ents = []
    for s in pick:
        dst = root / s["file"]
        if edit is not None and s["device"] == edit[0]:
            with np.load(base / s["file"]) as z:
                arrays = {k: np.array(z[k]) for k in z.files}
            arrays[edit[1]] = arrays[edit[1]] * edit[2]
            np.savez(dst, **arrays)
        else:
            shutil.copyfile(base / s["file"], dst)
        ents.append({"device": s["device"], "file": s["file"], "sha256": sha256_file(dst)})
    man = root / "manifest.json"
    man.write_text(json.dumps({"generator_sha256": real_manifest["generator_sha256"], "slices": ents}), encoding="utf-8")
    return man, pick


def _real_two_slice_spec(real_spec):
    return LutSpec(real_spec.manufacturing_grid_m, (("nmos", 5e-6), ("pmos", 5e-6)), REAL_DEVICE_KINDS, REAL_CAP_SUFFIX)


@pytest.mark.lut_realdata
@pytest.mark.parametrize("edit", [
    ("nfet_01v8", "GM", 2.0),
    ("pfet_01v8", "GDS", 2.0),
    ("nfet_01v8", "GMBS", math.log(10.0)),
    ("pfet_01v8", "GMBS", 1.0 / (2.0 * math.pi)),
    ("pfet_01v8", "GM", 1e-3),
], ids=["nfet_GM_x2", "pfet_GDS_x2", "nfet_GMBS_xln10", "pfet_GMBS_x1/2pi", "pfet_GM_x1/1000"])
def test_real_slice_scaled_column_rejected(tmp_path, real_paths, real_manifest, real_spec, edit):
    """실데이터 슬라이스 한 장의 열 × 척도 -> `lut_unit_mismatch`. detail 의 (cells_outside, cells) = 독립 구현(b) 의 수(같은 배열),
    column = 바꾼 열, path = 바꾼 파일."""
    man, pick = _real_two_slice_lut(tmp_path / "lut", real_paths, real_manifest, edit)
    spec = _real_two_slice_spec(real_spec)
    with pytest.raises(SchemaRejectedError) as ei:
        load_lut_set(str(man), real_paths["cap"], spec, pdk_root=real_paths["pdk_root"])
    d = detail_of(ei.value)
    fname = next(s["file"] for s in pick if s["device"] == edit[0])
    exp = _outside_counts(_real_arrays(man.parent / fname), edit[1])
    assert 2 * exp[0] > exp[1]
    assert d["reason"] == "lut_unit_mismatch" and d["column"] == edit[1]
    assert (d["cells_outside"], d["cells"]) == exp
    assert Path(d["path"]).name == fname


@pytest.mark.lut_realdata
def test_real_two_slice_control_loads(tmp_path, real_paths, real_manifest, real_spec):
    """음성 대조: 같은 두 장을 바꾸지 않고 복사하면 로드된다(위 거부가 복사·manifest 때문이 아님)."""
    man, _ = _real_two_slice_lut(tmp_path / "lut", real_paths, real_manifest)
    lut = load_lut_set(str(man), real_paths["cap"], _real_two_slice_spec(real_spec), pdk_root=real_paths["pdk_root"])
    assert set(lut.slice_map) == {("nmos", 1000), ("pmos", 1000)}
