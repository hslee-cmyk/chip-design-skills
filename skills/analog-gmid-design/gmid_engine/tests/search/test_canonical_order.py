"""search CONTRACT 3.23 [r11, r12] `canonical_order(sctx, variables) -> (정렬된 변수 tuple, 변수별 차원 index list, 차원 수)`.

oracle (d) 계약 3.23 1~3 문장: 키 = (L 인가, 성분 종류, 궤도 id), 궤도 id = device.dc_orbit(원소 키) / node.dc_orbit(넷 키) / -1 -- 이 test 는 키를
스냅샷 입력 열(dc_orbit)에서 직접 만들어 (a)~(g) 를 확인한다. 이름 치환은 (a) 구성(손 회로 SYM 의 이름 전단사)과 τ(dc_colour 짝) 대응.
"""
from __future__ import annotations

import itertools
import random

import pytest

from gmid_engine.search import Variable, canonical_order

from .canon_cases import C_BOX, SYM_ELEMENTS, asym_doc, make_case, rename_doc, sym_doc, tau

BOXES = {"CL1": C_BOX, "CL2": C_BOX}


def _sym(tmp, lut, doc=None, elements=SYM_ELEMENTS, boxes=None, **kw):
    return make_case(tmp, doc or sym_doc(), lut, elements=elements, boxes=boxes or BOXES, **kw)


def _with_l(case):
    """정의역 변수 + L 변수(칸 lo < hi 인 구간 -- test 가 만든 입력: 대표 MOS 마다 [1, 2] µm)."""
    lv = [Variable(("L", m), False, 1e-6, 2e-6) for m, _ in case.sctx.domain.l_cells]
    return list(case.sctx.domain.variables) + lv


def _key(case, var):
    dv = dict(case.dc.base.column("device", "dc_orbit"))
    nv = dict(case.dc.base.column("node", "dc_orbit"))
    kind, name = var.component
    orb = dv.get(name, nv.get(name, -1))
    return (kind == "L", kind, orb)


def _check_shape(case, vars_in):
    out, dims, n = canonical_order(case.sctx, vars_in)
    assert sorted(v.component for v in out) == sorted(v.component for v in vars_in)          # (f)
    assert len(out) == len(vars_in) == len(dims)
    assert sorted(set(dims)) == list(range(n))                                             # (g)
    keys = [_key(case, v) for v in out]
    assert keys == sorted(keys)                                                            # 키 오름차순
    for (k1, d1), (k2, d2) in itertools.combinations(zip(keys, dims), 2):                  # (b) 같은 키 ⇔ 같은 차원
        assert (k1 == k2) == (d1 == d2)
    ranks = sorted(set(keys))
    assert [ranks.index(k) for k in keys] == list(dims)                                    # 차원 = 키 순위(2)
    is_l = [v.component[0] == "L" for v in out]
    assert is_l == sorted(is_l)                                                            # (d) L 은 맨 뒤
    return out, dims, n


@pytest.mark.parametrize("which", ["sym", "asym", "sym_untied"])
def test_shape_and_key_order(tmp_path, lut_sealed, which):
    if which == "asym":
        case = make_case(tmp_path, asym_doc(), lut_sealed)
    else:
        case = _sym(tmp_path, lut_sealed, untie=("M3",) if which == "sym_untied" else None)
    _check_shape(case, _with_l(case))


def test_unique_keys_when_tied(tmp_path, lut_sealed):
    """[r12] 묶음 뒤 정의역 변수는 키가 유일 -> 차원 수 = 변수 수."""
    case = _sym(tmp_path, lut_sealed)
    out, dims, n = canonical_order(case.sctx, _with_l(case))
    assert n == len(out) and sorted(dims) == list(range(n))


def test_untied_orbit_shares_dimension(tmp_path, lut_sealed):
    """spec 이 푼 궤도 {M3, M4} 의 전류 변수 둘은 같은 키 -> 같은 차원(3.23 1·2)."""
    case = _sym(tmp_path, lut_sealed, untie=("M3",))
    out, dims, n = canonical_order(case.sctx, _with_l(case))
    d = {v.component: k for v, k in zip(out, dims)}
    assert d[("current", "M3")] == d[("current", "M4")]
    assert d[("L", "M3")] == d[("L", "M4")]
    assert n < len(out)


@pytest.mark.parametrize("seed", range(4))
def test_input_order_invariance(tmp_path, lut_sealed, seed):
    """(c)(e): 입력 순서를 섞어도 같은 출력, 같은 입력은 같은 출력."""
    case = _sym(tmp_path, lut_sealed, untie=("M3",) if seed % 2 else None)
    base = _with_l(case)
    ref = canonical_order(case.sctx, base)
    shuffled = list(base)
    random.Random(seed).shuffle(shuffled)
    got = canonical_order(case.sctx, shuffled)
    assert [v.component for v in got[0]] == [v.component for v in ref[0]]
    assert list(got[1]) == list(ref[1]) and got[2] == ref[2]
    assert canonical_order(case.sctx, base) == ref


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_renaming_keeps_kind_key_dim_sequence(tmp_path, lut_sealed, seed):
    """(a): 이름 전단사 σ -> 정렬된 변수의 (종류, τ 키, 차원) 열이 같다(이름만 옮겨짐)."""
    names = ["M1", "M2", "M3", "M4", "M5", "CL1", "CL2", "inp", "inn", "o1", "o2", "t", "vb", "pb"]
    new = ["z%02d" % i for i in range(len(names))]
    random.Random(seed).shuffle(new)
    sig = dict(zip(names, new))
    a = _sym(tmp_path / "a", lut_sealed)
    b = _sym(tmp_path / "b", lut_sealed, doc=rename_doc(sym_doc(), sig, "hand_sym_ord_r%d" % seed),
             elements=tuple((sig[n], k, v) for n, k, v in SYM_ELEMENTS), boxes={sig["CL1"]: C_BOX, sig["CL2"]: C_BOX})
    oa, da, na = canonical_order(a.sctx, _with_l(a))
    ob, db, nb = canonical_order(b.sctx, _with_l(b))
    ta, tb = tau(a.dc), tau(b.dc)
    assert [ta(v.component) for v in oa] == [tb(v.component) for v in ob]
    assert list(da) == list(db) and na == nb
    assert [(v.log, v.lo.hex(), v.hi.hex()) for v in oa] == [(v.log, v.lo.hex(), v.hi.hex()) for v in ob]
