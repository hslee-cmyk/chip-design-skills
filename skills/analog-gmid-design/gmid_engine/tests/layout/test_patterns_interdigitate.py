"""layout/patterns_interdigitate.py -- `interdigitate_layout`(+`INTERDIGITATION_PATTERNS`, `_try_interdigitation_table_match`) 복사.

기대값:
- 표 값(CONTRACT 1.2, DM 6 T10): test 작성자가 원문 Maloberti *Layout of Analog CMOS IC* Part 2 `Layout02.pdf` p.15
  "Interdigitiation Patterns" 표에서 독립 전사(렌더 육안 + PyMuPDF 단어 좌표 추출 대조, 2026-10-07). 원문의 `*` 표시는 값이 아니다.
- 표 경로 결과: 손계산(hub-leaf walk 성립 시작 노드가 하나뿐인 입력).
- 그 밖: 옛 SD `interdigitate_layout` 대조(같은 PYTHONHASHSEED -- 같은 프로세스 + seed 0·1·2 별도 프로세스).
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.patterns_interdigitate import INTERDIGITATION_PATTERNS, interdigitate_layout
from gmid_engine.layout.transistor import Transistor

# 원문 p.15: 행 = base(1열), 열 = 1x·2x·3x·4x
PDF_P15 = {
    "A":     ["A", "AA", "AAA", "AAAA"],
    "AB":    ["AB", "ABBA", "ABBAAB", "ABABBABA"],
    "ABC":   ["ABC", "ABCCBA", "ABCBACBCA", "ABCABCCBACBA"],
    "ABCD":  ["ABCD", "ABCDDCBA", "ABCBCADBCDA", "ABCDDCBAABCDDCBA"],
    "ABA":   ["ABA", "ABAABA", "ABAABAABA", "ABAABAABAABA"],
    "ABABA": ["ABABA", "ABABAABABA", "ABABAABABAABABA", "ABABAABABAABABAABABA"],
    "AABA":  ["AABA", "AABAABAA", "AABAAABAAABA", "AABAABAAAABAABAA"],
    "AABAA": ["AABAA", "AABAAAABAA", "AABAAAABAAAABAA", "AABAAAABAAAABAAAABAA"],
}


def test_table_matches_pdf_p15():
    assert list(INTERDIGITATION_PATTERNS) == list(PDF_P15)                  # 8 base, 원문 행 순서
    for base, cols in PDF_P15.items():
        assert INTERDIGITATION_PATTERNS[base] == {1: cols[0], 2: cols[1], 3: cols[2], 4: cols[3]}, base


def test_table_pdf_quirk_abcd_3x_is_11_letters():
    # DM 7절: 원문 ABCD 3x 는 11자(A3 B3 C3 D2) -- 원문 그대로
    s = INTERDIGITATION_PATTERNS["ABCD"][3]
    assert len(s) == 11 and (s.count("A"), s.count("B"), s.count("C"), s.count("D")) == (3, 3, 3, 2)


def T(name, nf, hub="hub"):
    return Transistor(name, "nmos", source=hub, drain="d" + name, n_fingers=nf)


def test_table_path_hand_ab_2_2():
    # 손: AB 2x = ABBA, 글자 개수 A2 B2 = nf 일치. walk: 시작 dA 만 성립 -> dA hub dB hub dA.
    out = interdigitate_layout([T("A", 2), T("B", 2)], base="AB")
    seq, nodes = ["A", "B", "B", "A"], ["dA", "hub", "dB", "hub", "dA"]
    assert out == {
        "rows": [{"transistor_sequence": seq, "node_sequence": nodes,
                  "segments": [{"transistor_sequence": seq, "node_sequence": nodes}], "crossover_after": []}],
        "names": ["A", "B"], "residual": 0.0, "isolated_pairs": 0, "crossover_count": 0, "method": "pattern_table",
    }


def test_table_path_explicit_repeat():
    out = interdigitate_layout([T("A", 2), T("B", 2)], base="AB", repeat=2)
    assert out["method"] == "pattern_table" and out["rows"][0]["transistor_sequence"] == ["A", "B", "B", "A"]
    # repeat 를 1 로 못 박으면 개수 불일치 -> 탐색 경로
    assert interdigitate_layout([T("A", 2), T("B", 2)], base="AB", repeat=1)["method"] == "search"


@pytest.mark.parametrize("nfs,base", [
    ((4, 2), "AB"),     # AB 표에 A4:B2 열 없음
    ((2, 1), "ABA"),    # ABA 1x 개수는 맞지만 hub-leaf walk 불가(손: A,B,A 어느 시작도 막힘)
    ((3, 1), "AABA"),   # AABA 1x 개수 맞음, walk 불가
])
def test_table_miss_falls_back_to_search(nfs, base):
    names = "ABCD"[:len(nfs)]
    out = interdigitate_layout([T(n, k) for n, k in zip(names, nfs)], base=base)
    assert out["method"] == "search"
    seq = out["rows"][0]["transistor_sequence"]
    assert sorted(seq) == sorted(n for n, k in zip(names, nfs) for _ in range(k))     # finger 보존


def test_errors():
    with pytest.raises(ValueError):
        interdigitate_layout([])
    with pytest.raises(ValueError):
        interdigitate_layout([T("A", 1, "h1"), T("B", 1, "h2")])                      # hub 다름
    with pytest.raises(ValueError):
        interdigitate_layout([T("A", 1), T("A", 1)])                                   # 이름 중복
    with pytest.raises(ValueError):
        interdigitate_layout([Transistor("A", "nmos", "hub", "d", 1), Transistor("B", "nmos", "hub", "d", 1)])  # leaf 중복
    with pytest.raises(ValueError):
        interdigitate_layout([T("A", 1), T("B", 1)], base="XYZ")                       # 표에 없는 base
    with pytest.raises(ValueError):
        interdigitate_layout([T("A", 1), T("B", 1), T("C", 1)], base="AB")             # 글자 2종 vs 소자 3
    with pytest.raises(ValueError):
        interdigitate_layout([T("A", 1), T("B", 1)], base="AB", repeat=7)              # 없는 repeat


ORACLE_INPUTS = [
    ("nf4_2_baseAB", [("A", 4), ("B", 2)], "AB", None),
    ("nf3_3_2_nobase", [("A", 3), ("B", 3), ("C", 2)], None, None),
    ("nf2_2_baseAB", [("A", 2), ("B", 2)], "AB", None),
    ("nf1_baseA", [("A", 1)], "A", None),
    ("nf1_1_1_nobase_crossover", [("A", 1), ("B", 1), ("C", 1)], None, None),
    ("nf2_1_baseABA", [("A", 2), ("B", 1)], "ABA", None),
]
ORACLE_METHOD = {"nf4_2_baseAB": "search", "nf3_3_2_nobase": "search", "nf2_2_baseAB": "pattern_table",
                 "nf1_baseA": "pattern_table", "nf1_1_1_nobase_crossover": "search", "nf2_1_baseABA": "search"}


@pytest.mark.parametrize("name,spec,base,repeat", ORACLE_INPUTS, ids=[x[0] for x in ORACLE_INPUTS])
def test_same_as_oracle(name, spec, base, repeat, sd, serialize):
    new = interdigitate_layout([T(n, k) for n, k in spec], base, repeat)
    old = sd.interdigitate_layout([sd.Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=k) for n, k in spec],
                                  base, repeat)
    assert new["method"] == ORACLE_METHOD[name]                 # 손: 의도한 경로를 실제로 탄다
    assert serialize(new) == serialize(old)


def test_crossover_fallback_actually_used():
    # 손: A1 B1 C1 -> 홀수 4개 -> 0-crossover 불가 -> crossover 1
    out = interdigitate_layout([T("A", 1), T("B", 1), T("C", 1)])
    assert out["crossover_count"] == 1


SEED_CODE = r"""
from gmid_engine.layout.patterns_interdigitate import interdigitate_layout
from gmid_engine.layout.transistor import Transistor
sd = load_sd()
out = []
for spec, base in ([[("A", 4), ("B", 2)], "AB"], [[("A", 3), ("B", 3), ("C", 2)], None], [[("A", 2), ("B", 2)], "AB"],
                   [[("A", 1)], "A"]):
    new = interdigitate_layout([Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=k) for n, k in spec], base)
    old = sd.interdigitate_layout([sd.Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=k) for n, k in spec], base)
    out.append([repr(ser(new)), repr(ser(old))])
RESULT = out
"""


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_same_as_oracle_per_hashseed(seed, seed_runner):
    for new, old in seed_runner(SEED_CODE, seed):
        assert new == old
