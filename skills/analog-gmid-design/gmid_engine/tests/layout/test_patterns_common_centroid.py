"""layout/patterns_common_centroid.py -- `common_centroid_layout`(+`COMMON_CENTROID_PATTERNS` 와 helper) 복사.

기대값:
- 표 값(CONTRACT 1.2, DM 6 T10): test 작성자가 원문 Maloberti *Layout of Analog CMOS IC* Part 2 `Layout02.pdf` p.19
  "Common Centroid Patterns" 에서 독립 전사(렌더 육안 + PyMuPDF 단어 좌표 추출 대조, 2026-10-07). 1·2열(2행 배열) = 표의
  repeat 1·2. 3열(3행 배열)·4열(4행 배열)은 표에 없다 -> xfail(reason="표 확장 미결정").
- 회전 exact: 손 정의(행 수 = 멤버 수, 다음 행 = 이름 한 칸 회전, 열마다 모든 멤버 1번씩 -> 잔차 0).
- 2멤버 표 경로(4:2, n_rows=2): 손계산(AAB/BAA, walk 시작 하나뿐).
- nf < 멤버 수(회전 경로) -> ValueError.
- 그 밖: 옛 SD 대조(같은 PYTHONHASHSEED).
"""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout.patterns_common_centroid import COMMON_CENTROID_PATTERNS, common_centroid_layout
from gmid_engine.layout.transistor import Transistor

# 원문 p.19: 가족(1열의 위/아래 행)마다 열 1~4, 열마다 행 문자열 목록
PDF_P19 = {
    ("ABBA", "BAAB"): [("ABBA", "BAAB"), ("ABBAABBA", "BAABBAAB"),
                       ("ABBAABBA", "BAABBAAB", "ABBAABBA"), ("ABBAABBA", "BAABBAAB", "BAABBAAB", "ABBAABBA")],
    ("ABA", "BAB"): [("ABA", "BAB"), ("ABAABA", "BABBAB"),
                     ("ABAABA", "BABBAB", "ABAABA"), ("ABAABAABA", "BABBABBAB", "BABBABBAB", "ABAABAABA")],
    ("ABCCBA", "CBAABC"): [("ABCCBA", "CBAABC"), ("ABCCBAABC", "CBAABCCBA"),
                           ("ABCCBAABC", "CBAABCCBA", "ABCCBAABC"),
                           ("ABCCBAABC", "CBAABCCBA", "CBAABCCBA", "ABCCBAABC")],
    ("AAB", "BAA"): [("AAB", "BAA"), ("AABBAA", "BAAAAB"),
                     ("AABBAA", "BAAAAB", "AABBAA"), ("AABBAA", "BAAAAB", "BAAAAB", "AABBAA")],
}


def test_table_two_row_columns_match_pdf_p19():
    assert list(COMMON_CENTROID_PATTERNS) == list(PDF_P19)                 # 4가족, 원문 순서
    for key, cols in PDF_P19.items():
        assert COMMON_CENTROID_PATTERNS[key] == {1: cols[0], 2: cols[1]}, key


@pytest.mark.xfail(reason="표 확장 미결정", strict=True)
@pytest.mark.parametrize("col", [2, 3], ids=["p19_col3_3rows", "p19_col4_4rows"])
def test_table_three_and_four_row_columns(col):
    for key, cols in PDF_P19.items():
        assert cols[col] in COMMON_CENTROID_PATTERNS[key].values(), (key, cols[col])


def T(name, nf, hub="hub"):
    return Transistor(name, "nmos", source=hub, drain="d" + name, n_fingers=nf)


def _walk_ok(seg, leaf_of, hub):
    ts, ns = seg["transistor_sequence"], seg["node_sequence"]
    return len(ns) == len(ts) + 1 and all({ns[i], ns[i + 1]} == {hub, leaf_of[n]} for i, n in enumerate(ts))


# 손: row_0 블록 = divmod(nf, n) 균등 분배. ABC/4 -> [2,1,1] 홀수 dB,dC = path; ABCD/8 -> [2,2,2,2] circuit;
# ABC/3 -> [1,1,1] 홀수 hub+3 leaf = 4, 홀짝 보정 불가(3 이상 홀수 없음) -> crossover 1; ABCD/4 -> [1,1,1,1] 홀수 4 -> 1.
@pytest.mark.parametrize("names,nf,xc", [("ABC", 4, 0), ("AB", 2, 0), ("ABCD", 8, 0), ("ABC", 3, 1), ("ABCD", 4, 1)])
def test_rotation_exact_hand_properties(names, nf, xc):
    out = common_centroid_layout([T(n, nf) for n in names])
    n = len(names)
    assert out["method"] == "rotation_exact"
    assert (out["residual"], out["isolated_pairs"], out["crossover_count"]) == (0.0, 0, xc)
    rows = out["rows"]
    assert len(rows) == n
    rot = {names[i]: names[(i + 1) % n] for i in range(n)}
    for k in range(n - 1):
        assert rows[k + 1]["transistor_sequence"] == [rot[x] for x in rows[k]["transistor_sequence"]]
    total = Counter(x for r in rows for x in r["transistor_sequence"])
    assert total == Counter({x: nf for x in names})
    width = len(rows[0]["transistor_sequence"])
    for j in range(width):                                        # 열마다 각 멤버 정확히 1번
        assert sorted(r["transistor_sequence"][j] for r in rows) == sorted(names)
    leaf_of = {x: "d" + x for x in names}
    for r in rows:
        assert len(r["segments"]) == xc + 1 and len(r["crossover_after"]) == xc
        for seg in r["segments"]:
            assert _walk_ok(seg, leaf_of, "hub")


def test_pattern_table_hand_4_2():
    # 손: 4:2 -> AAB/BAA(repeat 1, A 2+2, B 1+1). walk: AAB 는 hub 시작만, BAA 는 dB 시작만 성립.
    for n_rows in (2, None):
        out = common_centroid_layout([T("A", 4), T("B", 2)], n_rows=n_rows)
        assert out["method"] == "pattern_table"
        assert out["pattern"] == ("AAB", "BAA") and out["repeat"] == 1
        assert [r["transistor_sequence"] for r in out["rows"]] == [["A", "A", "B"], ["B", "A", "A"]]
        assert [r["node_sequence"] for r in out["rows"]] == [["hub", "dA", "hub", "dB"], ["dB", "hub", "dA", "hub"]]
        assert (out["residual"], out["isolated_pairs"], out["crossover_count"]) == (0.0, 0, 0)
        for r in out["rows"]:
            assert r["segments"] == [{"transistor_sequence": r["transistor_sequence"], "node_sequence": r["node_sequence"]}]
            assert r["crossover_after"] == []


def test_pattern_table_reversed_order_2_4():
    out = common_centroid_layout([T("A", 2), T("B", 4)], n_rows=2)
    assert out["method"] == "pattern_table"
    assert [r["transistor_sequence"] for r in out["rows"]] == [["B", "B", "A"], ["A", "B", "B"]]


@pytest.mark.parametrize("names,nf", [("ABC", 2), ("ABCD", 3), ("AB", 1)])
def test_fewer_fingers_than_members_rotation_rejected(names, nf):
    with pytest.raises(ValueError):
        common_centroid_layout([T(n, nf) for n in names])


def test_errors():
    with pytest.raises(ValueError):
        common_centroid_layout([T("A", 2)])                                  # 2개 미만
    with pytest.raises(ValueError):
        common_centroid_layout([T("A", 2, "h1"), T("B", 2, "h2")])           # hub 다름
    with pytest.raises(ValueError):
        common_centroid_layout([T("A", 2), T("B", 2)], n_rows=0)


def test_search_path_used_for_6_4_2_rows4():
    out = common_centroid_layout([T("A", 6), T("B", 4), T("C", 2)], n_rows=4)
    assert out["method"] == "search"
    assert len(out["rows"]) == 4
    assert Counter(x for r in out["rows"] for x in r["transistor_sequence"]) == Counter({"A": 6, "B": 4, "C": 2})


ORACLE_INPUTS = [
    ("rot_3x4", [("A", 4), ("B", 4), ("C", 4)], None, 24),
    ("rot_3x3_crossover", [("A", 3), ("B", 3), ("C", 3)], None, 24),
    ("rot_4x20_parity_fix", [("A", 20), ("B", 20), ("C", 20), ("D", 20)], None, 24),
    ("table_4_2", [("A", 4), ("B", 2)], 2, 24),
    ("search_6_4_2_rows4", [("A", 6), ("B", 4), ("C", 2)], 4, 24),
    ("search_3_1_rows2", [("A", 3), ("B", 1)], 2, 24),
    ("search_2_2_rows4_maxcand3", [("A", 2), ("B", 2)], 4, 3),
    ("search_5_3_rows1", [("A", 5), ("B", 3)], 1, 8),
]
ORACLE_METHOD = {"rot_3x4": "rotation_exact", "rot_3x3_crossover": "rotation_exact", "rot_4x20_parity_fix": "rotation_exact",
                 "table_4_2": "pattern_table", "search_6_4_2_rows4": "search", "search_3_1_rows2": "search",
                 "search_2_2_rows4_maxcand3": "search", "search_5_3_rows1": "search"}


@pytest.mark.parametrize("name,spec,n_rows,maxc", ORACLE_INPUTS, ids=[x[0] for x in ORACLE_INPUTS])
def test_same_as_oracle(name, spec, n_rows, maxc, sd, serialize):
    new = common_centroid_layout([T(n, k) for n, k in spec], n_rows, maxc)
    old = sd.common_centroid_layout([sd.Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=k) for n, k in spec],
                                    n_rows, maxc)
    assert new["method"] == ORACLE_METHOD[name]                  # 손: 의도한 경로를 실제로 탄다
    assert serialize(new) == serialize(old)


SEED_CODE = r"""
from gmid_engine.layout.patterns_common_centroid import common_centroid_layout
from gmid_engine.layout.transistor import Transistor
sd = load_sd()
out = []
for spec, n_rows in ([[("A", 4), ("B", 4), ("C", 4)], None], [[("A", 4), ("B", 2)], 2],
                     [[("A", 6), ("B", 4), ("C", 2)], 4], [[("A", 3), ("B", 3), ("C", 3)], None]):
    new = common_centroid_layout([Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=k) for n, k in spec], n_rows)
    old = sd.common_centroid_layout([sd.Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=k) for n, k in spec], n_rows)
    out.append([repr(ser(new)), repr(ser(old))])
RESULT = out
"""


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_same_as_oracle_per_hashseed(seed, seed_runner):
    for new, old in seed_runner(SEED_CODE, seed):
        assert new == old
