"""`lut_fingerprint` -- CONTRACT 1.5: 64자 hex, 경로 무관, 어느 sha256·cap_basis 든 바뀌면 다른 지문, 결정론(10)."""
import os
import re
import subprocess
import sys

import numpy as np
import pytest

from gmid_engine.lut import load_lut_set, lut_fingerprint

from .conftest import SKILL_DIR, TOY_SPEC, copy_tree, standard_toy_slices, toy_cap_arrays


def _basis(lut):
    return tuple((k, lut.cap_map[k].w_ref_m, lut.cap_map[k].basis) for k in sorted(lut.cap_map))


def test_lutset_fp_is_fingerprint_of_provenance_and_basis(toy):
    assert re.fullmatch(r"[0-9a-f]{64}", toy.fp)
    assert toy.fp == lut_fingerprint(toy.provenance, _basis(toy))


def test_path_independent(toy_build, tmp_path):
    b = toy_build("a")
    lut1 = b.load()
    dst = copy_tree(b.root, tmp_path / "elsewhere" / "deeper")
    lut2 = load_lut_set(str(dst / "manifest.json"), str(dst / "cap_ref.npz"), TOY_SPEC)
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
print(load_lut_set({man!r}, {cap!r}, spec).fp)
"""


def test_fp_deterministic_across_hashseed(toy_build, toy):
    b = toy_build("seed")
    code = _SUB.format(skill=str(SKILL_DIR), man=str(b.manifest), cap=str(b.cap))
    outs = set()
    for seed in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr
        outs.add(r.stdout.strip())
    assert outs == {toy.fp}


@pytest.mark.lut_realdata
def test_real_fp_deterministic(real_lut, real_paths, real_spec):
    again = load_lut_set(real_paths["manifest"], real_paths["cap"], real_spec)
    assert again.fp == real_lut.fp
    assert real_lut.fp == lut_fingerprint(real_lut.provenance, _basis(real_lut))
