"""`lut_fingerprint` -- CONTRACT 1.5: 64자 hex, 경로 무관, 어느 sha256·cap_basis 든 바뀌면 다른 지문, 결정론(10)."""
import dataclasses
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import pytest

from gmid_engine.lut import load_lut_set, lut_fingerprint

from .conftest import (MID_L_SOURCE, SKILL_DIR, TOY_SPEC, copy_tree, load_real, mid_point_arrays, sha256_file,
                       standard_toy_slices, toy_cap_arrays)


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
    """[r6] 1.5: 중점 파일을 주면 지문에 중점 sha256 항목이 더해진다 -- 중점 없이 로드한 지문과 다르고,
    provenance 에서 중점 sha256 만 None 으로 바꾼 지문은 중점 없는 로드의 지문과 같다(r5 와 같은 6항목)."""
    plain = load_real(real_paths, real_spec, verify_midpoints=None)
    assert plain.provenance.midpoints_sha256 is None
    assert plain.fp != real_lut.fp
    stripped = dataclasses.replace(real_lut.provenance, midpoints_path=None, midpoints_sha256=None,
                                   midpoints_l_source=(), midpoints_conditions=())
    assert lut_fingerprint(stripped, _basis(real_lut)) == plain.fp


# ---------------------------------------------------------------------------
# [r6] 1.5 중점 sha256 항목 (toy)
# ---------------------------------------------------------------------------

def _mid_toy(mid_toy_build, sub, L_points=(3.5e-6,), **kw):
    return mid_toy_build(sub, mid=mid_point_arrays(L_points, l_source=MID_L_SOURCE, **kw))


def test_midpoints_add_fp_item(mid_toy_build):
    mt = _mid_toy(mid_toy_build, "a")
    with_mid = mt.load()
    without = mt.load(verify_midpoints=None)
    assert with_mid.provenance.midpoints_sha256 == sha256_file(mt.mid_path)
    assert without.provenance.midpoints_sha256 is None
    assert with_mid.fp != without.fp
    assert with_mid.fp == lut_fingerprint(with_mid.provenance, _basis(with_mid))
    # 중점 sha256 만 지문을 바꾼다: 그 항목을 지운 provenance 의 지문 = 중점 없는 로드
    stripped = dataclasses.replace(with_mid.provenance, midpoints_path=None, midpoints_sha256=None,
                                   midpoints_l_source=(), midpoints_conditions=())
    assert lut_fingerprint(stripped, _basis(with_mid)) == without.fp


def test_midpoints_content_changes_fp_path_does_not(mid_toy_build, tmp_path):
    a = _mid_toy(mid_toy_build, "a").load()
    b = _mid_toy(mid_toy_build, "b", L_points=(3.25e-6,)).load()                # 다른 중점 내용
    assert a.fp != b.fp
    mt = _mid_toy(mid_toy_build, "c")
    moved = tmp_path / "moved_mid" / "x.npz"
    moved.parent.mkdir()
    shutil.copyfile(mt.mid_path, moved)
    c1 = mt.load()
    c2 = mt.load(verify_midpoints=str(moved))
    assert c1.provenance.midpoints_path != c2.provenance.midpoints_path
    assert c1.fp == c2.fp
