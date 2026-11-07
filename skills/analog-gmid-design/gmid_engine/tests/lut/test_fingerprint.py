"""`lut_fingerprint` -- CONTRACT 1.5: 64자 hex, 경로 무관, 어느 sha256·cap_basis 든 바뀌면 다른 지문, 결정론(10)."""
import dataclasses
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.core import fp_of
from gmid_engine.lut import load_lut_set, lut_fingerprint

from .conftest import (SKILL_DIR, T_MID_L, T_WIDTHS, TOY_SPEC, build_t, copy_tree, load_real, mid_file, sha256_file,
                       standard_toy_slices, t_spec, toy_cap_arrays)


def _basis(lut):
    return tuple((k, lut.cap_map[k].w_ref_m, lut.cap_map[k].basis) for k in sorted(lut.cap_map))


def test_lutset_fp_is_fingerprint_of_provenance_and_basis(toy):
    assert re.fullmatch(r"[0-9a-f]{64}", toy.fp)
    assert toy.fp == lut_fingerprint(toy.provenance, _basis(toy))


def test_path_independent(toy_build, tmp_path):
    b = toy_build("a")
    lut1 = b.load()
    dst = copy_tree(b.root, tmp_path / "elsewhere" / "deeper")
    lut2 = load_lut_set(str(dst / "manifest.json"), str(dst / "cap_ref.npz"), TOY_SPEC, bin_rule=str(dst / "bin_rule.json"),
                        pdk_root=str(dst / "pdk"))
    assert lut1.provenance.manifest_path != lut2.provenance.manifest_path
    assert lut1.fp == lut2.fp


def test_generator_sha_changes_fp(toy_build):
    a = toy_build("a").load()
    b = toy_build("b", generator_sha256="1" * 64).load()
    assert a.fp != b.fp


def test_slice_content_changes_fp(toy_build):
    a = toy_build("a").load()
    sl = standard_toy_slices()
    sl[1][2]["VTH"] = sl[1][2]["VTH"] + 1e-3
    b = toy_build("b", slices=sl).load()
    assert a.fp != b.fp


def test_cap_content_changes_fp(toy_build):
    a = toy_build("a").load()
    cap = toy_cap_arrays()
    cap["CGD_n"] = cap["CGD_n"] * 1.01
    b = toy_build("b", cap=cap).load()
    assert a.fp != b.fp


def test_cap_basis_changes_fp(toy):
    base = _basis(toy)
    k, w, basis = base[0]
    other = ((k, w * 2.0, basis),) + base[1:]
    assert lut_fingerprint(toy.provenance, other) != toy.fp
    assert lut_fingerprint(toy.provenance, base) == toy.fp


_SUB = r"""
import sys
sys.path.insert(0, {skill!r})
from gmid_engine.lut import LutSpec, load_lut_set
spec = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
print(load_lut_set({man!r}, {cap!r}, spec, bin_rule={rule!r}, pdk_root={pdk!r}).fp)
"""


def test_fp_deterministic_across_hashseed(toy_build, toy):
    b = toy_build("seed")
    code = _SUB.format(skill=str(SKILL_DIR), man=str(b.manifest), cap=str(b.cap), rule=b.bin_rule, pdk=b.tb.pdk_root)
    outs = set()
    for seed in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr
        outs.add(r.stdout.strip())
    assert outs == {toy.fp}


@pytest.mark.lut_realdata
def test_real_fp_deterministic(real_lut, real_paths, real_spec):
    """[r6] 기본 로드(1.8 '쓰는 법' -- pdk_root·verify_midpoints)를 다시 해도 같은 지문, 지문 = lut_fingerprint(provenance, basis)."""
    again = load_real(real_paths, real_spec)
    assert again.fp == real_lut.fp
    assert real_lut.fp == lut_fingerprint(real_lut.provenance, _basis(real_lut))


@pytest.mark.lut_realdata
def test_real_fp_midpoints_item(real_lut, real_paths, real_spec):
    """[LM-1e] 1.5: 중점 파일들이 있으면 지문에 중점 sha256 항목이 더해진다. 실 LUT 는 `widths` 안 슬라이스에 중점이 없으면 적재가 거부되므로
    (D7) '중점 없이 로드한 지문'을 만들 수 없다 -- 항목 없음의 확인은 toy F-4 가 한다. 여기서는 중점을 지운 provenance 의 지문이 달라지고
    (항목이 지문에 든다) 하나만 바꿔도 달라진다."""
    stripped = dataclasses.replace(real_lut.provenance, midpoint_sources=())
    assert stripped.midpoints_sha256 is None
    assert lut_fingerprint(stripped, _basis(real_lut)) != real_lut.fp
    one_less = dataclasses.replace(real_lut.provenance, midpoint_sources=real_lut.provenance.midpoint_sources[1:])
    assert lut_fingerprint(one_less, _basis(real_lut)) != real_lut.fp


# ---------------------------------------------------------------------------
# [LM-1e §4] 지문의 중점 항목 (toy T): `("midpoints_sha256", tuple(sorted(sha)))` 항목은 중점이 있을 때만 더해진다 -- 중점 파일 하나라도 내용이
# 바뀌면 다른 지문, 순서·경로는 무관. oracle (d): interface §4 F-1~F-4 + CONTRACT 1.5(경로 무관·sha256 만). F-4 는 interface §4 항목 표로
# `core.fp_of` tuple 을 직접 만들어 대조한다(`lut_fingerprint` 로 기대를 만들지 않는다).
# ---------------------------------------------------------------------------

def _t1(mid_toy_build, sub, **kw):
    return build_t(mid_toy_build, sub, {0: T_MID_L, 1: T_MID_L}, **kw)


def test_lm1e_f1_one_midpoint_file_changes_fp(mid_toy_build, tmp_path):
    """F-1: T-1 과 키 80 중점 파일 바이트만 바꾼 LUT(ID × e^0.01) -> 지문이 다르다."""
    a = _t1(mid_toy_build, "a").load(t_spec(0.6e-6))
    arrays = mid_file(T_WIDTHS[1][0], T_WIDTHS[1][1], T_MID_L)
    arrays["ID"] = arrays["ID"] * np.exp(0.01)
    b = build_t(mid_toy_build, "b", {0: T_MID_L, 1: arrays}).load(t_spec(0.6e-6))
    assert a.fp != b.fp
    assert a.provenance.midpoints_sha256 != b.provenance.midpoints_sha256


def test_lm1e_f2_sequence_order_does_not_change_fp(mid_toy_build):
    """F-2: verify_midpoints sequence 순서만 다름 -> 같은 지문·같은 midpoints_sha256."""
    mt = _t1(mid_toy_build, "ord")
    fwd = mt.load(t_spec(0.6e-6), verify_midpoints=[str(p) for p in mt.mid_paths])
    rev = mt.load(t_spec(0.6e-6), verify_midpoints=[str(p) for p in reversed(mt.mid_paths)])
    assert fwd.fp == rev.fp
    assert fwd.provenance.midpoints_sha256 == rev.provenance.midpoints_sha256 == \
        tuple(sorted(sha256_file(p) for p in mt.mid_paths))


def test_lm1e_f3_same_content_other_folder_same_fp(mid_toy_build, tmp_path):
    """F-3: 같은 내용을 다른 폴더로 옮긴 중점 파일들 -> 같은 지문(경로는 지문에 들지 않는다)."""
    mt = _t1(mid_toy_build, "mv")
    moved = []
    for i, p in enumerate(mt.mid_paths):
        q = tmp_path / ("moved_%d" % i) / "x.npz"
        q.parent.mkdir()
        shutil.copyfile(p, q)
        moved.append(str(q))
    c1 = mt.load(t_spec(0.6e-6))
    c2 = mt.load(t_spec(0.6e-6), verify_midpoints=moved)
    assert {s.path for s in c1.provenance.midpoint_sources} != {s.path for s in c2.provenance.midpoint_sources}
    assert c1.fp == c2.fp


def _fp_items_1_to_7(lut):
    """interface §4 `lut.fp` 표 1~7(언제나 있는 항목)을 공개 칸에서 직접 모은다 -- `lut_fingerprint` 는 부르지 않는다."""
    p = lut.provenance
    return (("manifest_sha256", p.manifest_sha256), ("generator_sha256", p.generator_sha256),
            ("slices", tuple((s.kind, s.w_key, s.sha256, s.conditions, s.model_files_sha256) for s in p.slices)),
            ("cap_sha256", p.cap_sha256), ("cap_conditions", p.cap_conditions),
            ("cap_basis", tuple((k, lut.cap_map[k].w_ref_m, lut.cap_map[k].basis) for k in sorted(lut.cap_map))),
            ("bin_rule_sha256", p.bin_rule_sha256))


def test_lm1e_f4_fp_item_tuple_contract(mid_toy_build, toy_build):
    """F-4 (a): 중점 없음(T-7 꼴, 잡음·mismatch 없음) -> lut.fp == fp_of(표 1~7) 7항목, 상수 None 중점 항목을 늘 더하는 꼴과 다르다.
    (b): T-1(중점 키 60·80) -> lut.fp == fp_of(1~7 + ("midpoints_sha256", 두 파일 raw sha 정렬 tuple)); sha 는 파일에서 hashlib 으로 직접.
    oracle (d): interface §4 표. 기대는 표로 test 가 직접 만든다(lut_fingerprint 호출 0)."""
    mt = _t1(mid_toy_build, "f4")
    # [A-196] 옛 입력(T-7 꼴: mid_toy 슬라이스 0.6·0.8 µm + TOY_SPEC 최소 폭 1.5 µm -> 후보 0)은 DEC-108 (1) 로 적재 거부 -> '중점 없음' LUT 는 기본 toy(후보 있음, 중점 파일 없음; 잡음·mismatch 없음)로 만든다
    plain = toy_build("f4plain").load()
    assert dict(plain.midpoints) == {} and plain.provenance.noise_sha256 is None and plain.provenance.mismatch_sha256 is None
    items = _fp_items_1_to_7(plain)
    assert plain.fp == fp_of(items)
    assert plain.fp != fp_of(items + (("midpoints_sha256", None),))
    assert plain.fp != fp_of(items + (("midpoints_sha256", ()),))
    with_mid = mt.load(t_spec(0.6e-6))
    assert with_mid.provenance.noise_sha256 is None and with_mid.provenance.mismatch_sha256 is None
    shas = tuple(sorted(hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in mt.mid_paths))
    assert len(shas) == 2
    assert with_mid.fp == fp_of(_fp_items_1_to_7(with_mid) + (("midpoints_sha256", shas),))
    assert with_mid.fp != plain.fp
