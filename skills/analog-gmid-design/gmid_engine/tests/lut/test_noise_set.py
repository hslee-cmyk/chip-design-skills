"""`noise_set` (`load_noise_tables` -- `load_lut_set(noise_npz=)` 가 부른다) -- CONTRACT 9.1 [r7], 설계 41 §7.2 '저장'·'로더'.

oracle:
- (a) 구성: toy 입력을 이 파일이 만든다(conftest `NoiseToy`) -> 로드된 `NoiseTable.S` 는 [f_lo(기준 LUT SVG2_1HZ), 이분 점들(r1 파일),
  f_hi(기준 LUT SVG2_HF)] 를 그 순서로 쌓은 배열과 같아야 한다(설계 41 §7.2 '로더는 v2 의 SVG2_* 와 새 파일의 점을 합쳐 노출').
- (c) 실데이터: 저장소 설정의 r1 파일을 numpy 로 직접 열어 같은 배열을 만든다.
- 거부: 각 사유 키는 CONTRACT 9.1 '거부' 목록 그대로, 입력은 한 곳만 바꾼 toy.
"""
import json
import math
import shutil

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutSpec, NoiseTable, load_lut_set

from .conftest import (NOISE_F_HI, NOISE_F_LO, NOISE_F_MID, TOY_NOISE_SPEC, TOY_SHAPE, NoiseToy, detail_of,
                       sha256_file, toy_grid_mesh)


def _ab():
    L, v, d, s = toy_grid_mesh()
    return 1e-12 * np.exp(v), 1e-16 * np.exp(0.5 * v)


def _toy(tmp_path, sub="n", **kw):
    A, B = _ab()
    return NoiseToy(tmp_path / sub, A, B, **kw)


def test_toy_loads_and_merges_frequency_points(tmp_path):
    t = _toy(tmp_path)
    lut = t.load()
    assert set(lut.noise) == {"nmos"}
    nt = lut.noise["nmos"]
    assert isinstance(nt, NoiseTable)
    # (a) 구성: 주파수 = f_lo, 이분 점, f_hi 오름차순
    assert tuple(nt.freqs) == (NOISE_F_LO,) + NOISE_F_MID + (NOISE_F_HI,)
    with np.load(t.path) as z:
        mid = np.array(z["SVG2_F_n"])
    expect = np.concatenate([t.cap_arrays["SVG2_1HZ_n"][None], mid, t.cap_arrays["SVG2_HF_n"][None]])
    assert np.asarray(nt.S).shape == (5,) + TOY_SHAPE
    assert np.array_equal(np.asarray(nt.S), expect)
    assert nt.ef == 1.0                                     # LutSpec.noise_ef 그대로(CONTRACT 9)
    assert nt.w_key == 100                                  # 기준 폭 1e-6 / 격자 1e-8
    assert nt.cap_sha256 == sha256_file(t.build.cap)
    assert nt.sha256 == sha256_file(t.path)


def test_provenance_and_fingerprint(tmp_path):
    """CONTRACT 1.3·1.5 [r7]: 잡음 파일 경로·sha256 이 provenance 에 실리고 지문이 바뀐다. 같은 파일을 다른 폴더로 옮기면 같은 지문."""
    t = _toy(tmp_path)
    lut = t.load()
    lut0 = load_lut_set(str(t.build.manifest), str(t.build.cap), TOY_NOISE_SPEC, bin_rule=t.build.bin_rule,
                        pdk_root=t.build.tb.pdk_root)
    assert lut.provenance.noise_sha256 == sha256_file(t.path)
    assert lut0.provenance.noise_sha256 is None and lut0.provenance.noise_path is None
    assert lut0.noise == {} or len(lut0.noise) == 0
    assert lut.fp != lut0.fp
    moved = tmp_path / "moved"
    shutil.copytree(t.root, moved)
    lut2 = load_lut_set(str(moved / "manifest.json"), str(moved / "cap_ref.npz"), TOY_NOISE_SPEC,
                        noise_npz=str(moved / "noise_r1.npz"), bin_rule=str(moved / "bin_rule.json"),
                        pdk_root=str(moved / "pdk"))
    assert lut2.fp == lut.fp


def _reject(t, spec=TOY_NOISE_SPEC):
    with pytest.raises(SchemaRejectedError) as ei:
        t.load(spec)
    return detail_of(ei.value)


def test_missing_file_rejected(tmp_path):
    t = _toy(tmp_path, write_noise=False)
    d = _reject(t)
    assert d["reason"] == "lut_noise_missing"


@pytest.mark.parametrize("key", ["cap_npz_sha256", "base_frequencies_hz"])
def test_meta_key_missing_rejected(tmp_path, key):
    t = _toy(tmp_path, meta_mutate=lambda m: m.pop(key))
    d = _reject(t)
    assert d["reason"] == "lut_noise_meta_invalid"
    assert key in str(d["missing"])


def test_meta_number_unparseable_rejected(tmp_path):
    t = _toy(tmp_path, meta_mutate=lambda m: m["base_frequencies_hz"].update(F_TEST="abc"))
    assert _reject(t)["reason"] == "lut_noise_meta_invalid"


def test_bound_to_other_cap_rejected(tmp_path):
    t = _toy(tmp_path, meta_mutate=lambda m: m.update(cap_npz_sha256="0" * 64))
    d = _reject(t)
    assert d["reason"] == "lut_noise_cap_mismatch"
    assert d["bound"] == "0" * 64 and d["cap"] == sha256_file(t.build.cap)


def test_conditions_mismatch_rejected(tmp_path):
    t = _toy(tmp_path, noise_mutate=lambda a: a.update(temp_c=np.float64(85.0)))
    assert _reject(t)["reason"] == "lut_conditions_mismatch"


@pytest.mark.parametrize("f_mid", [
    (100.0, 10.0, 1000.0),          # 오름차순 아님
    (1.0, 100.0, 1000.0),           # f_lo 와 같음(안쪽이 아님 -- 1 − r_j = 0 이 되는 점, CONTRACT 9.6 경계)
    (10.0, 100.0, 1e4),             # f_hi 와 같음
    (10.0, 100.0, 2e4),             # f_hi 밖
])
def test_frequency_points_invalid_rejected(tmp_path, f_mid):
    t = _toy(tmp_path, f_mid=f_mid)
    assert _reject(t)["reason"] == "lut_noise_frequency_invalid"


@pytest.mark.parametrize("mutate", [
    lambda a: a.update(VGS=np.asarray([0.0, 0.5, 1.0 + 2 ** -50])),      # 축 float 단위로 다름
    lambda a: a.update(L=np.asarray([1e-6, 2e-6, 3.5e-6])),
    lambda a: a.update(w_ref_m=np.float64(2e-6)),                        # 기준 폭 다름
])
def test_axes_or_width_mismatch_rejected(tmp_path, mutate):
    t = _toy(tmp_path, noise_mutate=mutate)
    assert _reject(t)["reason"] == "lut_noise_axes_mismatch"


@pytest.mark.parametrize("col", ["SVG2_1HZ_n", "SVG2_HF_n", "GM_n"])
def test_base_lut_column_missing_rejected(tmp_path, col):
    t = _toy(tmp_path, cap_mutate=lambda c: c.pop(col))
    assert _reject(t)["reason"] == "lut_noise_cap_column_missing"


def test_ef_undeclared_rejected(tmp_path):
    t = _toy(tmp_path)
    spec = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
    assert _reject(t, spec)["reason"] == "lut_noise_ef_undeclared"


def test_column_missing_rejected(tmp_path):
    t = _toy(tmp_path, noise_mutate=lambda a: a.pop("SVG2_F_n"))
    assert _reject(t)["reason"] == "lut_noise_column_missing"


def test_column_shape_rejected(tmp_path):
    t = _toy(tmp_path, noise_mutate=lambda a: a.update(SVG2_F_n=a["SVG2_F_n"][:2]))
    assert _reject(t)["reason"] == "lut_noise_shape_mismatch"


# ---------------------------------------------------------------- 실데이터 (c)

@pytest.mark.lut_realdata
def test_real_noise_table_matches_raw_files(real_nm_lut, raw_noise, raw_cap):
    """(c) 실데이터: S = [기준 LUT SVG2_1HZ, r1 SVG2_F 점들, 기준 LUT SVG2_HF](numpy 로 직접 쌓음), freqs = [1, f_hz.., 1e8],
    r1 meta cap_npz_sha256 = 기준 LUT 파일 sha256(설계 41 §7.2 '기존 r2 파일은 고치지 않는다' -- 묶임)."""
    meta = json.loads(str(raw_noise["meta_json"]))
    assert meta["cap_npz_sha256"] == real_nm_lut.provenance.cap_sha256
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        nt = real_nm_lut.noise[kind]
        f_lo = meta["base_frequencies_hz"]["NOISE_F_PROBE"]
        f_hi = meta["base_frequencies_hz"]["F_TEST"]
        assert tuple(nt.freqs) == (f_lo,) + tuple(float(x) for x in raw_noise["f_hz"]) + (f_hi,)
        S = np.asarray(nt.S)
        assert np.array_equal(S[0], raw_cap["SVG2_1HZ" + suf])
        assert np.array_equal(S[-1], raw_cap["SVG2_HF" + suf])
        assert np.array_equal(S[1:-1], raw_noise["SVG2_F" + suf])


@pytest.mark.lut_realdata
def test_real_ef_from_pdk_model_card(real_nm_lut, real_pdk_decl, real_paths):
    """(a) PDK 모델 카드의 `ef` 를 독립 파싱한 값 = NoiseTable.ef (설계 41 §7.2 'EF 는 PDK 모델 카드에서 파싱')."""
    import re
    root = real_paths["pdk_root"]
    for kind, dev in (("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")):
        text = open("%s/cells/%s/sky130_fd_pr__%s__tt.pm3.spice" % (root, dev, dev), encoding="utf-8").read()
        vals = {float(x) for x in re.findall(r"(?im)\bef\s*=\s*([-+0-9.eE]+)", text)}
        assert len(vals) == 1, (dev, vals)                 # bin 공통 값
        assert real_nm_lut.noise[kind].ef == vals.pop()
    assert math.isclose(real_nm_lut.noise["nmos"].ef, 0.84) and real_nm_lut.noise["pmos"].ef == 1.0
