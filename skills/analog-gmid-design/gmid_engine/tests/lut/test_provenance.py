"""`lut_provenance` -- CONTRACT 1.2·1.3: manifest·슬라이스 sha256 재측정, w_key = round(W / grid), 2 ulp 폭 판정,
(kind, w_key) 정렬 SliceSource, 측정 조건 쌍 tuple, 거부 사유 8종. 6절 `_lut_conditions_from_npz` 복사 해시.
"""
import hashlib
import math
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutProvenance, LutSpec, SliceSource, load_lut_set, lut_provenance

from .conftest import (BIN_MODEL_REL, LEGACY_SR, LUT_SRC, MID_L_SOURCE, TOY_SPEC, ast_sha, detail_of, function_body,
                       mid_point_arrays, sha256_file, standard_toy_slices, toy_slice_arrays)

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


# ---------------------------------------------------------------------------
# [r4] 모델 파일 (1.3): pdk_root + 상대 경로, sha256 재측정, SliceSource.model_paths, 거부 3종
# ---------------------------------------------------------------------------

def _same_path(a, b):
    return Path(a).resolve() == Path(b).resolve()


def test_model_paths_recorded(bin_toy_build, toy_build):
    bt = bin_toy_build()
    p = lut_provenance(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC)
    for s in p.slices:
        assert len(s.model_paths) == 1
        rel, path = s.model_paths[0]
        assert rel == BIN_MODEL_REL and _same_path(path, bt.model_path)
    assert all(s.model_paths == () for s in _prov(toy_build()).slices)     # 기록 없는 toy -> ()


def _reject_both(bt):
    """lut_provenance 와 load_lut_set 둘 다 같은 사유로 거부."""
    out = []
    for call in (lambda: lut_provenance(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC), bt.load):
        with pytest.raises(SchemaRejectedError) as ei:
            call()
        out.append(detail_of(ei.value))
    assert out[0]["reason"] == out[1]["reason"]
    return out[0]


def test_reject_model_root_missing(bin_toy_build):
    def drop_root(meta):
        meta = dict(meta)
        del meta["pdk_root"]
        return meta
    bt = bin_toy_build(meta_fn=drop_root)
    det = _reject_both(bt)
    assert det["reason"] == "lut_model_root_missing"
    assert any(_same_path(det["path"], p) for p in bt.slice_paths)     # detail path = 슬라이스


def test_empty_model_record_without_root_is_fine(bin_toy_build):
    """기록이 비어 있으면 pdk_root 가 없어도 된다(빈 지도)."""
    lut = bin_toy_build(meta_fn=lambda meta: {"model_files_sha256": {}}).load()
    assert all(sl.l_bins.bins == () for sl in lut.slice_map.values())


def test_reject_model_file_missing(bin_toy_build):
    bt = bin_toy_build(model_text=False)
    det = _reject_both(bt)
    assert det["reason"] == "lut_model_file_missing"
    # path: 1.3 은 '경로 = os.path.join(pdk_root, 상대 경로)' -- detail 이 상대 표기인지 결합 경로인지는 명시 없음(둘 다 허용)
    assert det["path"] == BIN_MODEL_REL or _same_path(det["path"], bt.model_path)
    assert any(_same_path(det["slice"], p) for p in bt.slice_paths)


def test_reject_model_file_sha256_mismatch(bin_toy_build):
    bt = bin_toy_build()
    recorded = bt.meta["model_files_sha256"][BIN_MODEL_REL]
    bt.model_path.write_text(bt.model_path.read_text(encoding="utf-8") + "* edited\n", encoding="utf-8")
    det = _reject_both(bt)
    assert det["reason"] == "lut_model_file_sha256_mismatch"
    assert det["recorded"] == recorded and det["actual"] == sha256_file(bt.model_path)
    assert det["path"] == BIN_MODEL_REL or _same_path(det["path"], bt.model_path)
    assert any(_same_path(det["slice"], p) for p in bt.slice_paths)


# ---------------------------------------------------------------------------
# [r6] pdk_root 덮어쓰기 (1.3): 모델 파일 경로 = os.path.join(pdk_root, 상대 경로) (meta pdk_root 대신, root_missing 판정도),
#      sha256 대조는 그대로 -> 같은 모델 파일이면 어느 폴더든 같은 결과·같은 지문
# ---------------------------------------------------------------------------

def _moved_pdk(bt, dst):
    shutil.copytree(bt.pdk, dst)
    shutil.rmtree(bt.pdk)                                      # meta 의 pdk_root 는 이제 없다
    return dst


def test_pdk_root_override_replaces_meta_root(bin_toy_build, tmp_path):
    bt = bin_toy_build("ov")
    lut0 = bt.load()
    new = _moved_pdk(bt, tmp_path / "pdk_moved")
    with pytest.raises(SchemaRejectedError) as ei:              # 음성: 덮어쓰지 않으면 meta 경로 -> 파일 없음
        bt.load()
    assert detail_of(ei.value)["reason"] == "lut_model_file_missing"
    p = lut_provenance(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(new))
    for s in p.slices:
        rel, path = s.model_paths[0]
        assert rel == BIN_MODEL_REL and _same_path(path, os.path.join(str(new), BIN_MODEL_REL))
    lut1 = load_lut_set(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(new))
    assert lut1.fp == lut0.fp                                   # 같은 모델 파일 -> 같은 지문(경로는 지문에 없다)
    assert all(lut1.slice_map[k].l_bins == lut0.slice_map[k].l_bins for k in lut0.slice_map)


def test_pdk_root_override_used_for_root_missing(bin_toy_build):
    """meta 에 pdk_root 가 없어도(-> 기본은 lut_model_root_missing) 인자 pdk_root 가 있으면 그 루트로 로드."""
    def drop_root(meta):
        meta = dict(meta)
        del meta["pdk_root"]
        return meta
    bt = bin_toy_build("nr", meta_fn=drop_root)
    with pytest.raises(SchemaRejectedError):
        bt.load()
    lut = load_lut_set(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(bt.pdk))
    assert lut.slice_map[("nmos", 100)].l_bins.bins != ()


def test_pdk_root_override_sha_still_checked(bin_toy_build, tmp_path):
    """덮어쓴 루트의 모델 파일 내용이 다르면 sha256 불일치로 거부(폴더만 바뀌고 대조는 그대로)."""
    bt = bin_toy_build("sh")
    other = tmp_path / "pdk_other"
    shutil.copytree(bt.pdk, other)
    f = other / BIN_MODEL_REL
    f.write_text(f.read_text(encoding="utf-8") + "* other\n", encoding="utf-8")
    with pytest.raises(SchemaRejectedError) as ei:
        load_lut_set(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(other))
    det = detail_of(ei.value)
    assert det["reason"] == "lut_model_file_sha256_mismatch" and det["actual"] == sha256_file(f)


# ---------------------------------------------------------------------------
# [r6] verify_midpoints (1.3): 경로·sha256·L_source 쌍·측정 조건, 파일 없음 -> lut_midpoints_missing
# ---------------------------------------------------------------------------

def test_midpoints_recorded_in_provenance(mid_toy_build):
    mt = mid_toy_build("pm", mid=mid_point_arrays((3.5e-6,), l_source=MID_L_SOURCE))
    p = lut_provenance(str(mt.build.manifest), str(mt.build.cap), TOY_SPEC, verify_midpoints=str(mt.mid_path))
    assert _same_path(p.midpoints_path, mt.mid_path)
    assert p.midpoints_sha256 == sha256_file(mt.mid_path)
    assert tuple(p.midpoints_l_source) == tuple(sorted(MID_L_SOURCE.items()))
    assert tuple(p.midpoints_conditions) == COND_TT
    q = lut_provenance(str(mt.build.manifest), str(mt.build.cap), TOY_SPEC)
    assert (q.midpoints_path, q.midpoints_sha256, tuple(q.midpoints_l_source), tuple(q.midpoints_conditions)) == \
        (None, None, (), ())


def test_midpoints_missing(mid_toy_build, tmp_path):
    mt = mid_toy_build("pmm")
    missing = tmp_path / "nope_mid.npz"
    for call in (lambda: lut_provenance(str(mt.build.manifest), str(mt.build.cap), TOY_SPEC, verify_midpoints=str(missing)),
                 lambda: mt.load(verify_midpoints=str(missing))):
        with pytest.raises(SchemaRejectedError) as ei:
            call()
        det = detail_of(ei.value)
        assert det["reason"] == "lut_midpoints_missing" and _same_path(det["path"], missing)


@pytest.mark.lut_realdata
def test_real_pdk_root_and_midpoints(real_lut, real_paths):
    """1.8 '쓰는 법' 로드: 모델 파일 경로 = 설정 pdk_root 기준, 중점 provenance 가 설정 파일."""
    root = real_paths["pdk_root"]
    for s in real_lut.provenance.slices:
        assert s.model_paths and all(_same_path(path, os.path.join(root, rel)) for rel, path in s.model_paths)
    p = real_lut.provenance
    assert p.midpoints_sha256 == sha256_file(real_paths["midpoints"])
    assert dict(p.midpoints_l_source)["key"] == "verification_midpoints_um"
    assert tuple(p.midpoints_conditions) == COND_TT
