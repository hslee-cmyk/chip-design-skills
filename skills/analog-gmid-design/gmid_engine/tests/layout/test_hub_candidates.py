"""CONTRACT 0절·1절 `hub_candidates.find_hub_merge_candidates`(복사, SD 2635~2658, Q8 (viii)).

복사 정의 = 옛 동작과 같음: 같은 입력에서 SD(오라클)와 반환이 같다(소자는 이름·필드 직렬화로 비교). AST 해시·리터럴은
`_copy_manifest`/구조 test 소관이고 여기서는 동작 대조 + 손계산만 본다.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout import _copy_manifest as manifest
from gmid_engine.layout.hub_candidates import find_hub_merge_candidates
from gmid_engine.layout.transistor import Transistor

CASES = {
    "hub_merge_4_15": [("C", "nmos", "x", "y"), ("D", "nmos", "y", "z"), ("G", "nmos", "y", "w")],
    "shared_source_vdd": [("M3", "pmos", "vdd", "o1"), ("M4", "pmos", "vdd", "o2"), ("M6", "pmos", "vdd", "out"),
                          ("M1", "nmos", "t", "o1"), ("M2", "nmos", "t", "o2")],
    "role_collision": [("A", "nmos", "n", "a"), ("B", "nmos", "n", "b"), ("C", "nmos", "c", "n"), ("D", "nmos", "d", "n")],
    "no_sharing": [("A", "nmos", "a1", "a2"), ("B", "nmos", "b1", "b2")],
    "kind_split": [("A", "nmos", "n", "a"), ("B", "pmos", "n", "b")],
}


def _norm(res):
    return sorted((k, [(t.name, t.kind, t.source, t.drain) for t in v]) for k, v in res.items())


def test_registered_in_copy_manifest():
    rows = [r for r in manifest.COPIED_DEFINITIONS if r[:2] == ("hub_candidates.py", "find_hub_merge_candidates")]
    assert len(rows) == 1
    assert rows[0][2] == "2635~2658"


@pytest.mark.parametrize("case", sorted(CASES))
def test_same_as_old_original(sd, case):
    new = find_hub_merge_candidates([Transistor(n, k, s, d) for n, k, s, d in CASES[case]])
    old = sd.find_hub_merge_candidates([sd.Transistor(n, k, s, d) for n, k, s, d in CASES[case]])
    assert _norm(new) == _norm(old)
    assert list(new.keys()) == list(old.keys())                     # 삽입 순서까지 같다


def test_hand_values():
    res = find_hub_merge_candidates([Transistor(n, k, s, d) for n, k, s, d in CASES["hub_merge_4_15"]])
    assert _norm(res) == [(("nmos", "y"), [("D", "nmos", "y", "z"), ("G", "nmos", "y", "w")])]
    assert find_hub_merge_candidates([Transistor(n, k, s, d) for n, k, s, d in CASES["no_sharing"]]) == {}
    assert find_hub_merge_candidates([Transistor(n, k, s, d) for n, k, s, d in CASES["kind_split"]]) == {}
