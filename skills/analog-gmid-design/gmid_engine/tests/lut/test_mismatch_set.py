"""`mismatch_set` (`load_mismatch_tables` -- `load_lut_set(mismatch_npz=)`) -- CONTRACT 10.1 [r7], 설계 41 §6.4-2b '저장'·'로더'.

oracle: (a) 구성 toy(conftest `MismatchToy`) -- 로드 표의 배열·변수·slope_ref 는 이 파일이 쓴 값 그대로; (c) 실데이터 -- r1 npz 를
numpy 로 직접 읽은 배열과 meta 의 slope_ref. 거부 사유 키는 CONTRACT 10.1 목록, 입력은 한 곳만 바꾼다.
"""
import json
import shutil

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import MismatchTable, load_lut_set

from .conftest import MISMATCH_SLOPE_REF, TOY_SHAPE, TOY_SPEC, MismatchToy, detail_of, sha256_file, toy_grid_mesh


def _dv():
    L, v, d, s = toy_grid_mesh()
    return {"vth0": np.full(TOY_SHAPE, 1e-3), "toxe": 2e-3 * (1 + v), "voff": 2e-3 + 0 * v}


def test_toy_loads(tmp_path):
    dv = _dv()
    t = MismatchToy(tmp_path / "m", dv)
    lut = t.load()
    mt = lut.mismatch["nmos"]
    assert isinstance(mt, MismatchTable)
    assert tuple(mt.params) == ("toxe", "voff", "vth0")
    for p in mt.params:
        assert np.array_equal(np.asarray(mt.dvgs[p]), dv[p])
    assert mt.w_key == 100 and mt.sigma_unit == 1e-6
    assert mt.cap_sha256 == sha256_file(t.build.cap) and mt.sha256 == sha256_file(t.path)
    # slope_ref: 앵커 L 마다 (변수, slope 이름, 값) -- meta 그대로
    for row in mt.slope_ref:
        assert {(p, v) for p, _, v in row} == set(MISMATCH_SLOPE_REF.items())
    assert lut.provenance.mismatch_sha256 == sha256_file(t.path)


def test_fingerprint_includes_mismatch_and_is_path_free(tmp_path):
    t = MismatchToy(tmp_path / "m", _dv())
    lut = t.load()
    lut0 = load_lut_set(str(t.build.manifest), str(t.build.cap), TOY_SPEC)
    assert lut.fp != lut0.fp
    moved = tmp_path / "moved"
    shutil.copytree(t.root, moved)
    lut2 = load_lut_set(str(moved / "manifest.json"), str(moved / "cap_ref.npz"), TOY_SPEC,
                        mismatch_npz=str(moved / "mismatch_r1.npz"))
    assert lut2.fp == lut.fp


def _reject(t):
    with pytest.raises(SchemaRejectedError) as ei:
        t.load()
    return detail_of(ei.value)


def test_missing_file(tmp_path):
    t = MismatchToy(tmp_path / "m", _dv())
    t.path.unlink()
    assert _reject(t)["reason"] == "lut_mismatch_missing"


@pytest.mark.parametrize("key", ["cap_npz_sha256", "sigma_unit", "slope_ref", "variables"])
def test_meta_missing(tmp_path, key):
    t = MismatchToy(tmp_path / "m", _dv(), meta_mutate=lambda m: m.pop(key))
    assert _reject(t)["reason"] == "lut_mismatch_meta_invalid"


def test_slope_ref_count_must_match_anchors(tmp_path):
    def drop_one(m):
        rec = m["slope_ref"]["toyn"]
        rec.pop(sorted(rec, key=float)[-1])
    t = MismatchToy(tmp_path / "m", _dv(), meta_mutate=drop_one)
    assert _reject(t)["reason"] == "lut_mismatch_meta_invalid"


def test_bound_to_other_cap(tmp_path):
    t = MismatchToy(tmp_path / "m", _dv(), meta_mutate=lambda m: m.update(cap_npz_sha256="1" * 64))
    assert _reject(t)["reason"] == "lut_mismatch_cap_mismatch"


def test_conditions(tmp_path):
    t = MismatchToy(tmp_path / "m", _dv(), mm_mutate=lambda a: a.update(corner=np.str_("ff")))
    assert _reject(t)["reason"] == "lut_conditions_mismatch"


@pytest.mark.parametrize("mutate", [
    lambda a: a.update(VDS=np.asarray([0.5, 1.0 + 2 ** -50])),
    lambda a: a.update(VS=np.asarray([0.0, 0.6])),
    lambda a: a.update(w_ref_m=np.float64(5e-6)),
])
def test_axes_or_width(tmp_path, mutate):
    t = MismatchToy(tmp_path / "m", _dv(), mm_mutate=mutate)
    assert _reject(t)["reason"] == "lut_mismatch_axes_mismatch"


def test_declared_variable_column_missing(tmp_path):
    t = MismatchToy(tmp_path / "m", _dv(), mm_mutate=lambda a: a.pop("DVGS_voff_n"))
    assert _reject(t)["reason"] == "lut_mismatch_column_missing"


def test_column_shape(tmp_path):
    t = MismatchToy(tmp_path / "m", _dv(), mm_mutate=lambda a: a.update(DVGS_vth0_n=a["DVGS_vth0_n"][:, :2]))
    assert _reject(t)["reason"] == "lut_mismatch_shape_mismatch"


@pytest.mark.lut_realdata
def test_real_tables_match_raw(real_nm_lut, raw_mismatch, real_paths):
    """(c) 실데이터: 변수 목록 = meta variables = PDK 모델 카드의 `*_slope_spectre` 전수(설계 41 §6.4-2 'k 는 전수'), 배열 = npz 그대로."""
    import re
    meta = json.loads(str(raw_mismatch["meta_json"]))
    assert meta["cap_npz_sha256"] == real_nm_lut.provenance.cap_sha256
    for kind, dev, suf in (("nmos", "nfet_01v8", "_n"), ("pmos", "pfet_01v8", "_p")):
        card = open("%s/cells/%s/sky130_fd_pr__%s__tt.pm3.spice" % (real_paths["pdk_root"], dev, dev),
                    encoding="utf-8").read()
        spectre = sorted({m.lower() for m in re.findall(r"_01v8__(\w+?)_slope_spectre\b", card)})
        mt = real_nm_lut.mismatch[kind]
        assert sorted(mt.params) == spectre == sorted(meta["variables"][dev])
        for p in mt.params:
            assert np.array_equal(np.asarray(mt.dvgs[p]), raw_mismatch["DVGS_%s%s" % (p, suf)], equal_nan=True)
