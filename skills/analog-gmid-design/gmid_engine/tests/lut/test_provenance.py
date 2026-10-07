"""`lut_provenance` -- CONTRACT 1.2·1.3: manifest·슬라이스 sha256 재측정, w_key = round(W / grid), 2 ulp 폭 판정,
(kind, w_key) 정렬 SliceSource, 측정 조건 쌍 tuple, 거부 사유 8종. 6절 `_lut_conditions_from_npz` 복사 해시.
"""
import hashlib
import math
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutProvenance, LutSpec, SliceSource, lut_provenance

from .conftest import (LEGACY_SR, LUT_SRC, TOY_SPEC, ast_sha, detail_of, function_body, sha256_file,
                       standard_toy_slices, toy_slice_arrays)

H_COND = "20513c618b94f19b50d8a4fcfc2fd0a17f934302259ed4e78d4b21163451235b"
COND_TT = (("corner", "tt"), ("recorded", True), ("temp_c", 27.0))


def test_copy_ast_hash():
    old = function_body(LEGACY_SR, "lut_conditions_from_npz")
    new = function_body(LUT_SRC / "provenance.py", "_lut_conditions_from_npz")
    assert len(old) == 3 and len(new) == 3
    assert ast_sha(old) == H_COND
    assert ast_sha(new) == H_COND


def _prov(b, spec=TOY_SPEC):
    return lut_provenance(str(b.manifest), str(b.cap), spec)


def test_toy_provenance(toy_build):
    # manifest 순서를 뒤집어도 (kind, w_key) 정렬
    b = toy_build(slices=list(reversed(standard_toy_slices())))
    p = _prov(b)
    assert isinstance(p, LutProvenance)
    assert p.manifest_sha256 == sha256_file(b.manifest)
    assert p.generator_sha256 == "0" * 64
    assert p.cap_sha256 == sha256_file(b.cap)
    assert p.cap_conditions == COND_TT
    assert [(s.kind, s.w_key) for s in p.slices] == [("nmos", 100), ("nmos", 200)]
    s0 = p.slices[0]
    assert isinstance(s0, SliceSource)
    assert s0.device == "toyn" and s0.w_m == 1e-6
    assert s0.sha256 == sha256_file(b.root / "toy_w100.npz")
    assert s0.conditions == COND_TT
    assert Path(s0.path).resolve() == (b.root / "toy_w100.npz").resolve()


def test_unrecorded_conditions(toy_build):
    sl = standard_toy_slices()
    for _, _, a in sl:
        del a["corner"], a["temp_c"]
    p = _prov(toy_build(slices=sl))
    c = p.slices[0].conditions
    assert [k for k, _ in c] == ["note", "recorded"]
    assert dict(c)["recorded"] is False and isinstance(dict(c)["note"], str)


def _reject(b, spec=TOY_SPEC):
    with pytest.raises(SchemaRejectedError) as ei:
        _prov(b, spec)
    return detail_of(ei.value)


def test_reject_manifest_missing(tmp_path):
    with pytest.raises(SchemaRejectedError) as ei:
        lut_provenance(str(tmp_path / "none.json"), str(tmp_path / "c.npz"), TOY_SPEC)
    assert detail_of(ei.value)["reason"] == "lut_manifest_missing"


def test_reject_device_undeclared(toy_build):
    sl = standard_toy_slices()
    sl[1] = (sl[1][0], "toyx", sl[1][2])
    assert _reject(toy_build(slices=sl))["reason"] == "lut_device_undeclared"


def test_reject_slice_missing(toy_build):
    b = toy_build()
    (b.root / "toy_w100.npz").unlink()
    assert _reject(b)["reason"] == "lut_slice_missing"


def test_reject_sha256_mismatch_by_edit(toy_build):
    b = toy_build()
    p = b.root / "toy_w200.npz"
    a = toy_slice_arrays(2e-6, 2.0)
    a["VTH"] = a["VTH"] + 1e-9
    np.savez(p, **a)                       # manifest 는 옛 sha256 그대로
    assert _reject(b)["reason"] == "lut_slice_sha256_mismatch"


def test_reject_sha256_mismatch_by_manifest(toy_build):
    b = toy_build(sha_override={0: hashlib.sha256(b"x").hexdigest()})
    assert _reject(b)["reason"] == "lut_slice_sha256_mismatch"


def test_reject_width_off_grid(toy_build):
    sl = standard_toy_slices()
    sl[1] = (sl[1][0], sl[1][1], toy_slice_arrays(2.0005e-6, 2.0))
    assert _reject(toy_build(slices=sl))["reason"] == "lut_width_off_grid"


def test_reject_slice_duplicate_same_width(toy_build):
    sl = standard_toy_slices()
    sl[1] = (sl[1][0], sl[1][1], toy_slice_arrays(1e-6, 2.0))      # 다른 파일, 같은 (kind, w_key)
    assert _reject(toy_build(slices=sl))["reason"] == "lut_slice_duplicate"


def test_reject_slice_duplicate_same_file_twice(toy_build):
    b = toy_build(manifest_slices=lambda e: e + [dict(e[0])])
    assert _reject(b)["reason"] == "lut_slice_duplicate"


def test_reject_manifest_empty(toy_build):
    assert _reject(toy_build(manifest_slices=lambda e: []))["reason"] == "lut_manifest_empty"


def test_reject_cap_missing(toy_build):
    b = toy_build(cap=None)
    assert _reject(b)["reason"] == "lut_cap_missing"


# ---------------------------------------------------------------------------
# w_key 규칙과 2 ulp 경계
# ---------------------------------------------------------------------------

def _ulps_off(W, grid):
    r = W / grid
    return abs(r - round(r)) / math.ulp(r)


def _walk(W0, grid, direction):
    """W0 에서 한 ulp 씩 걸어 (2 ulp 이내 마지막 W, 처음 2 ulp 를 넘는 W)."""
    last_ok, W = W0, W0
    for _ in range(200):
        W = math.nextafter(W, direction)
        if _ulps_off(W, grid) > 2:
            return last_ok, W
        last_ok = W
    raise AssertionError("2 ulp 경계를 못 찾음")


@pytest.mark.parametrize("direction", [math.inf, -math.inf])
@pytest.mark.parametrize("idx,W0,key", [(1, 2e-6, 200), (0, 1e-6, 100)])
def test_two_ulp_boundary(toy_build, direction, idx, W0, key):
    """[r3] 폭 키 허용 대칭: W/grid 가 키 위·아래 어느 쪽으로든 2 ulp 이내면 그 키, 넘으면 거부."""
    grid = 1e-8
    ok_W, bad_W = _walk(W0, grid, direction)
    assert ok_W != W0 and 0 < _ulps_off(ok_W, grid) <= 2 < _ulps_off(bad_W, grid)
    r = ok_W / grid
    assert (r > key) if direction > 0 else (r < key)            # 실제로 그 방향으로 벗어난 비율
    sl = standard_toy_slices()
    scale = sl[idx][2]["ID"][0, 0, 0, 0] / toy_slice_arrays(1e-6)["ID"][0, 0, 0, 0]
    sl[idx] = (sl[idx][0], sl[idx][1], toy_slice_arrays(ok_W, scale))
    p = _prov(toy_build("ok", slices=sl))
    s = [x for x in p.slices if x.w_key == key]
    assert len(s) == 1 and s[0].w_m == ok_W                     # round(W / grid) = key
    sl[idx] = (sl[idx][0], sl[idx][1], toy_slice_arrays(bad_W, scale))
    det = _reject(toy_build("bad", slices=sl))
    assert det["reason"] == "lut_width_off_grid"


def test_w_key_is_rounded_ratio_with_other_grid(toy_build):
    # grid 5e-9(sky130 MANUFACTURINGGRID 0.005 µm): 1e-6 -> 200, 2e-6 -> 400
    spec = LutSpec(5e-9, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
    p = _prov(toy_build(), spec)
    assert [s.w_key for s in p.slices] == [200, 400]
    assert all(isinstance(s.w_key, int) for s in p.slices)


@pytest.mark.lut_realdata
def test_real_provenance(real_paths, real_spec, real_manifest, real_slice_files):
    p = lut_provenance(real_paths["manifest"], real_paths["cap"], real_spec)
    assert p.manifest_sha256 == sha256_file(real_paths["manifest"])
    assert p.generator_sha256 == real_manifest["generator_sha256"]
    assert p.cap_sha256 == sha256_file(real_paths["cap"])
    assert [(s.kind, s.w_key) for s in p.slices] == [(k, wk) for k, _, _, wk, _ in real_slice_files]
    by_file = {Path(s["file"]).name: s["sha256"] for s in real_manifest["slices"]}
    for s in p.slices:
        assert s.sha256 == by_file[Path(s.path).name]
        assert s.conditions == COND_TT
    # 기준 LUT 에는 corner·temp_c 가 있다
    assert p.cap_conditions == COND_TT
    assert {s.w_key for s in p.slices if s.kind == "nmos"} >= {72, 1000, 1400}
