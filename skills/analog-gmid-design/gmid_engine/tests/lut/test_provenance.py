"""`lut_provenance` -- CONTRACT 1.2·1.3: manifest·슬라이스 sha256 재측정, w_key = round(W / grid), 2 ulp 폭 판정,
(kind, w_key) 정렬 SliceSource, 측정 조건 쌍 tuple, 거부 사유 8종. 6절 `_lut_conditions_from_npz` 복사 해시.
"""
import dataclasses
import hashlib
import json
import math
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import LutProvenance, LutSpec, SliceSource, load_lut_set, lut_provenance

from toy_bins import write_decl

from .conftest import (BIN_MODEL_REL, LEGACY_SR, LUT_SRC, TOY_SPEC, ast_sha, detail_of, function_body,
                       mid_file, mid_meta, sha256_file, standard_toy_slices, toy_slice_arrays)

H_COND = "20513c618b94f19b50d8a4fcfc2fd0a17f934302259ed4e78d4b21163451235b"
COND_TT = (("corner", "tt"), ("recorded", True), ("temp_c", 27.0))


def test_copy_ast_hash():
    old = function_body(LEGACY_SR, "lut_conditions_from_npz")
    new = function_body(LUT_SRC / "provenance.py", "_lut_conditions_from_npz")
    assert len(old) == 3 and len(new) == 3
    assert ast_sha(old) == H_COND
    assert ast_sha(new) == H_COND


def _prov(b, spec=TOY_SPEC):
    return lut_provenance(str(b.manifest), str(b.cap), spec, bin_rule=b.bin_rule, pdk_root=b.tb.pdk_root)


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
        lut_provenance(str(tmp_path / "none.json"), str(tmp_path / "c.npz"), TOY_SPEC,
                       bin_rule=write_decl(tmp_path / "rule.json", ["0" * 64]))
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
    p = lut_provenance(real_paths["manifest"], real_paths["cap"], real_spec, bin_rule=real_paths["bin_rule"], pdk_root=real_paths["pdk_root"])
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
    p = lut_provenance(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, bin_rule=bt.bin_rule)
    for s in p.slices:
        assert len(s.model_paths) == 1
        rel, path = s.model_paths[0]
        assert rel == BIN_MODEL_REL and _same_path(path, bt.model_path)
    # [WB-1 §4] 모든 합성 LUT 가 합성 모델 파일을 가진다(기록 없는 toy 는 model_unrecorded 로 거부 -- 아래 test)
    assert all(len(s.model_paths) == 1 and s.model_paths[0][0] == "models/toy_nmos.spice" for s in _prov(toy_build()).slices)


def _reject_both(bt):
    """lut_provenance 와 load_lut_set 둘 다 같은 사유로 거부."""
    out = []
    for call in (lambda: lut_provenance(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, bin_rule=bt.bin_rule),
                 bt.load):
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
    """[WB-1 §1 적재 적용] 세트 meta 의 모델 기록이 0개면(옛: 빈 지도로 적재) `model_unrecorded` 로 거부된다. 빈 지도는 bin 블록 없는
    모델 파일로 만든다(`toy_empty`)."""
    with pytest.raises(SchemaRejectedError) as ei:
        bin_toy_build(meta_fn=lambda meta: {"model_files_sha256": {}, "ngspice": "ngspice-46"}).load()
    det = detail_of(ei.value)
    assert det["reason"] == "bin_tie_undeclared" and det["why"] == "model_unrecorded"


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
    p = lut_provenance(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(new), bin_rule=bt.bin_rule)
    for s in p.slices:
        rel, path = s.model_paths[0]
        assert rel == BIN_MODEL_REL and _same_path(path, os.path.join(str(new), BIN_MODEL_REL))
    lut1 = load_lut_set(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(new), bin_rule=bt.bin_rule)
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
    lut = load_lut_set(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(bt.pdk), bin_rule=bt.bin_rule)
    assert lut.slice_map[("nmos", 100)].l_bins.bins != ()


def test_pdk_root_override_sha_still_checked(bin_toy_build, tmp_path):
    """덮어쓴 루트의 모델 파일 내용이 다르면 sha256 불일치로 거부(폴더만 바뀌고 대조는 그대로)."""
    bt = bin_toy_build("sh")
    other = tmp_path / "pdk_other"
    shutil.copytree(bt.pdk, other)
    f = other / BIN_MODEL_REL
    f.write_text(f.read_text(encoding="utf-8") + "* other\n", encoding="utf-8")
    with pytest.raises(SchemaRejectedError) as ei:
        load_lut_set(str(bt.build.manifest), str(bt.build.cap), TOY_SPEC, pdk_root=str(other), bin_rule=bt.bin_rule)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_model_file_sha256_mismatch" and det["actual"] == sha256_file(f)


# ---------------------------------------------------------------------------
# [LM-1e §2] 중점 파일(DC 슬라이스 npz 꼴)의 provenance 관문 G0~G4c(`lut_provenance`)와 결과 칸
# oracle (d): interface §2 관문 표(사용자 승인 계획 N6.40 LM-1e 의 계약) -- 사유 이름·detail 키·순서는 그 표 그대로.
# ---------------------------------------------------------------------------

L_MID = (3.5e-6, 7.5e-6)               # interface §3 toy T 의 중점 L
SLICE_META_KEYS = ("generator_sha256", "model_files_sha256", "ngspice")


def _prov_mid(mt, paths=None):
    return lut_provenance(str(mt.build.manifest), str(mt.build.cap), TOY_SPEC, bin_rule=mt.bin_rule,
                          verify_midpoints=[str(p) for p in (mt.mid_paths if paths is None else paths)])


def _both_calls(mt):
    """같은 거부가 lut_provenance 와 load_lut_set 양쪽에서 나온다(G0~G4c = lut_provenance, load 가 먼저 부른다)."""
    return (lambda: _prov_mid(mt), lambda: mt.load())


def _expect_reject(mt, reason, **detail):
    for call in _both_calls(mt):
        with pytest.raises(SchemaRejectedError) as ei:
            call()
        det = detail_of(ei.value)
        assert det["reason"] == reason, det
        for k, v in detail.items():
            assert det[k] == v, (k, det)
    return det


def test_lm1e_midpoint_sources_recorded(mid_toy_build):
    """결과(interface §2): midpoint_sources = SliceSource(kind, device=<짝 manifest device>, w_m, w_key, path, sha256=<raw>,
    conditions, model_files_sha256, model_paths=()), (kind, w_key) 오름차순. midpoints_sha256 = property."""
    mt = mid_toy_build("pm", mid={1: L_MID, 0: L_MID})               # 선언 순서와 무관하게 w_key 오름차순
    p = _prov_mid(mt)
    assert [(s.kind, s.w_key) for s in p.midpoint_sources] == [("nmos", 100), ("nmos", 200)]
    for s, idx, wk in zip(p.midpoint_sources, (0, 1), (100, 200)):
        assert isinstance(s, SliceSource)
        assert s.device == "toyn" and s.w_m == (1e-6, 2e-6)[idx] and s.w_key == wk      # device = 짝 manifest 의 device (파일 meta 가 아니다)
        assert _same_path(s.path, mt.mid_paths[idx])
        assert s.sha256 == sha256_file(mt.mid_paths[idx])             # 파일 raw 바이트의 sha256
        assert s.conditions == COND_TT
        assert s.model_paths == ()
        assert s.model_files_sha256 == p.slices[idx].model_files_sha256   # 짝 슬라이스와 같은 기록(G4b 가 같음을 강제)
    assert p.midpoints_sha256 == tuple(sorted(sha256_file(x) for x in mt.mid_paths))
    names = {f.name for f in dataclasses.fields(LutProvenance)}
    assert "midpoint_sources" in names
    # 옛 칸 이름은 조각으로 쓴다(옛 이름 grep(G-1)에 이 파일이 걸리지 않게). midpoints_sha256 은 property 라 칸이 아니다.
    old = {"midpoints_" + "path", "midpoints_l" + "_source", "midpoints_" + "conditions", "midpoints_sha256"}
    assert not names & old


def test_lm1e_no_midpoints_provenance(mid_toy_build):
    mt = mid_toy_build("pn")
    for kw in ({}, {"verify_midpoints": []}, {"verify_midpoints": ()}):       # 빈 sequence = 없음
        q = lut_provenance(str(mt.build.manifest), str(mt.build.cap), TOY_SPEC, bin_rule=mt.bin_rule, **kw)
        assert q.midpoint_sources == () and q.midpoints_sha256 is None


def test_lm1e_verify_midpoints_string_is_type_error(mid_toy_build):
    """문자열 하나(옛 꼴) -> TypeError (두 함수 모두)."""
    mt = mid_toy_build("pt", mid={0: L_MID})
    with pytest.raises(TypeError):
        lut_provenance(str(mt.build.manifest), str(mt.build.cap), TOY_SPEC, bin_rule=mt.bin_rule,
                       verify_midpoints=str(mt.mid_path))
    with pytest.raises(TypeError):
        mt.load(verify_midpoints=str(mt.mid_path))


def test_lm1e_g0_midpoints_missing(mid_toy_build, tmp_path):
    mt = mid_toy_build("g0", mid={0: L_MID})
    missing = tmp_path / "nope_mid.npz"
    for call in (lambda: _prov_mid(mt, [missing]), lambda: mt.load(verify_midpoints=[str(missing)])):
        with pytest.raises(SchemaRejectedError) as ei:
            call()
        det = detail_of(ei.value)
        assert det["reason"] == "lut_midpoints_missing" and _same_path(det["path"], missing)


def test_lm1e_g1_width_missing_and_old_format(mid_toy_build):
    a = mid_file(1e-6, 1.0, L_MID)
    del a["W"]
    _expect_reject(mid_toy_build("g1", mid={0: a}), "lut_midpoints_width_missing")
    # 옛 형식 파일(w_ref_m·접미사 열·meta L_source, W 없음) -> G1
    old = {"L": np.asarray(L_MID), "VGS": a["VGS"], "VDS": a["VDS"], "VS": a["VS"], "ID_n": a["ID"], "GM_n": a["GM"],
           "w_ref_m": np.float64(1e-6), "corner": np.str_("tt"), "temp_c": np.float64(27.0),
           "meta_json": np.str_('{"L_source": {"kind": "json"}}')}
    _expect_reject(mid_toy_build("g1old", mid={0: old}), "lut_midpoints_width_missing")


def test_lm1e_g1b_width_off_grid(mid_toy_build):
    a = mid_file(1e-6, 1.0, L_MID)
    a["W"] = np.float64(1.005e-6)                  # 격자 1e-8 의 100.5 배
    _expect_reject(mid_toy_build("g1b", mid={0: a}), "lut_width_off_grid", w_m=1.005e-6, grid_m=1e-8)


@pytest.mark.parametrize("bad_at", [0, 1])
def test_lm1e_g1c_l_off_grid(mid_toy_build, bad_at):
    """G1c: L 원소 하나라도 제조 격자 밖(3.505e-6 / 1e-8 = 350.5 -- 비정수) -> lut_midpoints_l_off_grid(새 이름), detail L_m·grid_m."""
    L = [3.5e-6, 7.5e-6]
    L[bad_at] = 3.505e-6 if bad_at == 0 else 7.505e-6
    a = mid_file(1e-6, 1.0, L)
    _expect_reject(mid_toy_build("g1c", mid={0: a}), "lut_midpoints_l_off_grid", L_m=L[bad_at], grid_m=1e-8)


def test_lm1e_g1c_on_grid_l_accepted(mid_toy_build):
    """판별: 격자 위 L(3.5e-6 = 350 격자, 7.5e-6 = 750 격자 -- 부동소수 반올림 허용 판정)은 G1c 가 거부하지 않는다."""
    p = _prov_mid(mid_toy_build("g1ok", mid={0: L_MID}))
    assert [(s.kind, s.w_key) for s in p.midpoint_sources] == [("nmos", 100)]


def test_lm1e_g_order_g1_before_g1c_and_g2(mid_toy_build):
    """위에서 아래로 첫 맞는 행: W 없음 + L 격자 밖 + device 없음 -> G1."""
    a = mid_file(1e-6, 1.0, (3.505e-6,))
    del a["W"]
    a["meta_json"] = np.str_(json.dumps({"generator_sha256": "0" * 64}))
    _expect_reject(mid_toy_build("gord", mid={0: a}), "lut_midpoints_width_missing")


@pytest.mark.parametrize("why", ["no_device", "other_device", "no_width_pair"])
def test_lm1e_g2_slice_unmatched(mid_toy_build, why):
    """G2: meta device 없음 / 짝 device 없음 / 같은 device 인데 폭 키가 같은 슬라이스 없음(W = 1.5 µm -> 키 150)."""
    W = 1.5e-6 if why == "no_width_pair" else 1e-6
    meta = mid_meta()
    if why == "no_device":
        del meta["device"]
    if why == "other_device":
        meta["device"] = "nobody"
    a = mid_file(W, 1.0, L_MID, meta)
    det = _expect_reject(mid_toy_build("g2" + why, mid={0: a}), "lut_midpoints_slice_unmatched")
    assert det["w_key"] == (150 if why == "no_width_pair" else 100)
    if why == "other_device":
        assert det["device"] == "nobody"


def test_lm1e_g3_duplicate_pair(mid_toy_build):
    """G3: 같은 (kind, w_key) 에 중점 파일 둘 -> lut_slice_duplicate, set 'midpoints'."""
    a, b = mid_file(1e-6, 1.0, (3.5e-6,)), mid_file(1e-6, 1.0, (7.5e-6,))
    mt = mid_toy_build("g3", mid={0: a})
    p2 = mt.root / "lut" / "midpoints_dup.npz"
    np.savez(p2, **b)
    paths = [str(mt.mid_paths[0]), str(p2)]
    for call in (lambda: _prov_mid(mt, paths), lambda: mt.load(verify_midpoints=paths)):
        with pytest.raises(SchemaRejectedError) as ei:
            call()
        det = detail_of(ei.value)
        assert det["reason"] == "lut_slice_duplicate"
        assert (det["set"], det["kind"], det["w_key"]) == ("midpoints", "nmos", 100)


@pytest.mark.parametrize("key,value", [("generator_sha256", "1" * 64), ("model_files_sha256", {BIN_MODEL_REL: "2" * 64}),
                                       ("ngspice", "ngspice-45")])
def test_lm1e_g4_conditions_mismatch(mid_toy_build, key, value):
    """G4·G4b·G4c: generator_sha256 ≠ manifest 값 / model_files_sha256 ≠ 짝 슬라이스 meta / ngspice ≠ 짝 슬라이스 meta."""
    a = mid_file(1e-6, 1.0, L_MID, mid_meta(**{key: value}))
    _expect_reject(mid_toy_build("g4" + key[:3], mid={0: a}), "lut_conditions_mismatch", key=key)


def test_lm1e_g4_generator_absent_in_manifest_is_always_mismatch(mid_toy_build):
    """G4: manifest 에 generator_sha256 이 없으면 언제나 거부(중점 meta 값이 무엇이든)."""
    mt = mid_toy_build("g4none", mid={0: L_MID})
    man = json.loads(mt.build.manifest.read_text(encoding="utf-8"))
    del man["generator_sha256"]
    mt.build.manifest.write_text(json.dumps(man), encoding="utf-8")
    for call in _both_calls(mt):
        with pytest.raises(SchemaRejectedError) as ei:
            call()
        det = detail_of(ei.value)
        assert det["reason"] == "lut_conditions_mismatch" and det["key"] == "generator_sha256"


@pytest.mark.lut_realdata
def test_real_pdk_root_and_midpoints(real_lut, real_paths):
    """1.8 '쓰는 법' 로드: 모델 파일 경로 = 설정 pdk_root 기준, 중점 provenance 가 설정 파일 전부(경로·raw sha256)."""
    root = real_paths["pdk_root"]
    for s in real_lut.provenance.slices:
        assert s.model_paths and all(_same_path(path, os.path.join(root, rel)) for rel, path in s.model_paths)
    p = real_lut.provenance
    assert p.midpoints_sha256 == tuple(sorted(sha256_file(x) for x in real_paths["midpoints"]))
    assert sorted(os.path.normcase(os.path.abspath(s.path)) for s in p.midpoint_sources) == \
        sorted(os.path.normcase(os.path.abspath(x)) for x in real_paths["midpoints"])
    assert all(s.conditions == COND_TT and s.model_paths == () for s in p.midpoint_sources)
