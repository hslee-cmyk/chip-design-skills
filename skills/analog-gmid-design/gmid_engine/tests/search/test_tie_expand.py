"""search CONTRACT 3.24 [r12] 3·7 (b)(c) `expand_ties(ties, theta) -> dict` + `evaluate` 의 확장.

oracle (d) 계약 문장: 입력을 바꾸지 않는다, 묶인 성분 = 대표 값(비트), 구성원 값이 있으면 대표가 이긴다, 묶음이 없으면 입력의 사본.
(a) 구성: ties 는 test 가 손으로 쓴 값(합성 입력)과 손 회로 SYM(구성 자기동형)의 정의역.
"""
from __future__ import annotations

import copy
import math

from gmid_engine.search import expand_ties
from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼

from .conftest import schema_of  # [U17 ①-b] graph/kernel 필드 읽기
from .canon_cases import C_BOX, SYM_ELEMENTS, make_case, mid_theta, sym_doc

TIES = ((("L", "A"), (("L", "B"), ("L", "C"))), (("current", "A"), (("current", "B"),)))


def _hex(v):
    return float(v).hex()


def test_members_get_representative_value_input_untouched():
    th = {("L", "A"): 1.25e-6, ("current", "A"): 3.0000000000000004e-6, ("y", "n"): 0.5}
    before = copy.deepcopy(th)
    out = expand_ties(TIES, th)
    assert th == before                                                  # 입력 불변
    assert out is not th and isinstance(out, dict)
    assert _hex(out[("L", "B")]) == _hex(out[("L", "C")]) == _hex(1.25e-6)
    assert _hex(out[("current", "B")]) == _hex(3.0000000000000004e-6)
    assert {k: out[k] for k in before} == before                          # 대표·묶이지 않은 성분 그대로
    assert set(out) == set(before) | {("L", "B"), ("L", "C"), ("current", "B")}


def test_representative_wins_over_member_value():
    th = {("L", "A"): 1e-6, ("L", "B"): 2e-6, ("current", "A"): 1e-5, ("current", "B"): 7e-5}
    before = dict(th)
    out = expand_ties(TIES, th)
    assert out[("L", "B")] == 1e-6 and out[("L", "C")] == 1e-6 and out[("current", "B")] == 1e-5
    assert th == before


def test_no_ties_returns_copy():
    th = {("L", "A"): 1e-6}
    out = expand_ties((), th)
    assert out == th and out is not th
    out[("L", "A")] = 2e-6
    assert th[("L", "A")] == 1e-6


def test_idempotent():
    th = {("L", "A"): 1e-6, ("current", "A"): 1e-5}
    once = expand_ties(TIES, th)
    assert expand_ties(TIES, once) == once


def test_evaluate_expands_tied_members_bit_exact(tmp_path, lut_sealed):
    """3.24 7 (c): 대표 성분만 넘긴 θ 의 평가 θ 에서 구성원 성분 값 = 대표 값(비트)."""
    case = make_case(tmp_path, sym_doc(), lut_sealed, elements=SYM_ELEMENTS, boxes={"CL1": C_BOX, "CL2": C_BOX})
    d = case.sctx.domain
    assert d.ties                                                        # 묶음 있는 회로(구성)
    th, cells = mid_theta(d)
    r = evaluate(case.sctx, th, cells)
    got = dict(r.theta)
    for rep, members in d.ties:
        for m in members:
            assert _hex(got[m]) == _hex(th[rep]), (rep, m)
    assert set(got) == set(schema_of(case.dc).components)                    # 확장된 전체 θ


def test_evaluate_representative_wins_and_same_key(tmp_path, lut_sealed):
    """구성원 값을 다르게 넣어도 대표가 이긴다 -> 대표만 넘긴 평가와 같은 θ·같은 평가 키(캐시 적중)."""
    case = make_case(tmp_path, sym_doc(), lut_sealed, elements=SYM_ELEMENTS, boxes={"CL1": C_BOX, "CL2": C_BOX})
    d = case.sctx.domain
    th, cells = mid_theta(d)
    r1 = evaluate(case.sctx, th, cells)
    noisy = dict(th)
    for rep, members in d.ties:
        for m in members:
            noisy[m] = th[rep] * 1.5 if rep[0] != "y" else 0.25
    r2 = evaluate(case.sctx, noisy, cells)
    assert dict(r2.theta) == dict(r1.theta)
    assert r2.key == r1.key
    assert all(not math.isnan(v) for v in dict(r2.theta).values())
