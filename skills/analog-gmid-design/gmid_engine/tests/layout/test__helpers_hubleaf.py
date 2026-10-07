"""layout/_helpers_hubleaf.py -- 복사 helper 7개의 공개 별칭 6개(CONTRACT 0 끝).

기대값: 손계산(hub-leaf walk 성립 조건, 잔차 = 소자별 행 내 정규화 위치 평균의 max-min, 격리 쌍 수) + 옛 SD 의 같은 이름(`_` 붙은)
함수 대조. `_` 이름은 layout 쪽에서 쓰지 않는다(CONTRACT 머리) -- 옛 SD 쪽 `_` 이름은 오라클이라 쓴다.
"""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout import _helpers_hubleaf as H

ALIASES = ["build_rows_from_shares", "build_rows_from_shares_with_crossover", "common_centroid_residual",
           "count_isolated_pairs", "hubleaf_sequence_node_path", "repair_row_parity"]
LEAF = {"A": "da", "B": "db", "C": "dc"}


@pytest.mark.parametrize("name", ALIASES)
def test_alias_exists_and_callable(name):
    assert callable(getattr(H, name))


# ---- hubleaf_sequence_node_path ----
@pytest.mark.parametrize("seq,expected", [
    (["A", "B", "B", "A"], ["da", "hub", "db", "hub", "da"]),   # 유효 시작 da 하나
    (["A", "A", "B"], ["hub", "da", "hub", "db"]),              # 유효 시작 hub 하나
    (["B", "A", "A"], ["db", "hub", "da", "hub"]),
    (["A", "B", "A"], None),                                    # ABA: hub-leaf 불가
    (["A", "B", "C", "C", "B", "A"], None),                     # ABCCBA: 불가
])
def test_hubleaf_path_hand(seq, expected):
    assert H.hubleaf_sequence_node_path(seq, "hub", LEAF) == expected


# ---- common_centroid_residual ----
@pytest.mark.parametrize("rows,expected", [
    ([["A", "B", "B", "A"]], 0.0),          # A (0+1)/2, B (1/3+2/3)/2 -> 0.5 둘 다
    ([["A", "A", "B"]], 0.75),              # A (0+0.5)/2=0.25, B 1.0
    ([["A"], ["B", "B"]], 0.0),             # 길이 1 행 = 0.5, B (0+1)/2
    ([], 0.0),
    ([[], ["A", "B"]], 1.0),                # 빈 행 건너뜀, A 0 B 1
])
def test_residual_hand(rows, expected):
    assert H.common_centroid_residual([{"transistor_sequence": r} for r in rows]) == expected


# ---- count_isolated_pairs ----
@pytest.mark.parametrize("rows,names,expected", [
    ([["A", "B"], ["C"]], ["A", "B", "C"], 2),     # (A,C),(B,C) 한 번도 같은 행에 없음
    ([["A", "B", "C"]], ["A", "B", "C"], 0),
    ([["A"], ["B"]], ["A", "B"], 1),
    ([["A", "B"]], ["A"], 0),
])
def test_isolated_pairs_hand(rows, names, expected):
    assert H.count_isolated_pairs([{"transistor_sequence": r} for r in rows], names) == expected


# ---- repair_row_parity ----
def test_repair_single_bad_row_cannot_fix():
    assert H.repair_row_parity([Counter({"A": 1, "B": 1, "C": 1})], LEAF, "hub") is None


def test_repair_moves_one_finger_to_neighbor():
    # 손: 행0 {A1,B1,C1} = 홀수 4개(hub 3, leaf 1x3) -> 불가. A 1개를 행1로: 행0 {B1,C1} 홀수 2(path), 행1 {A2} 가능.
    out = H.repair_row_parity([Counter({"A": 1, "B": 1, "C": 1}), Counter({"A": 1})], LEAF, "hub")
    assert out == [Counter({"B": 1, "C": 1}), Counter({"A": 2})]


def test_repair_already_feasible_unchanged():
    shares = [Counter({"A": 2, "B": 2}), Counter({"C": 1})]
    assert H.repair_row_parity(shares, LEAF, "hub") == shares


# ---- build_rows_from_shares(_with_crossover) ----
def _walk_ok(row, leaf_of, hub):
    ts, ns = row["transistor_sequence"], row["node_sequence"]
    return len(ns) == len(ts) + 1 and all({ns[i], ns[i + 1]} == {hub, leaf_of[n]} for i, n in enumerate(ts))


def test_build_rows_zero_crossover():
    rows = H.build_rows_from_shares([Counter({"A": 2, "B": 2}), Counter(), Counter({"C": 1})], LEAF, "hub")
    assert len(rows) == 3
    assert Counter(rows[0]["transistor_sequence"]) == Counter({"A": 2, "B": 2}) and _walk_ok(rows[0], LEAF, "hub")
    assert rows[0]["segments"] == [{"transistor_sequence": rows[0]["transistor_sequence"],
                                    "node_sequence": rows[0]["node_sequence"]}]
    assert rows[0]["crossover_after"] == []
    assert rows[1] == {"transistor_sequence": [], "node_sequence": [], "segments": [], "crossover_after": []}
    assert rows[2]["transistor_sequence"] == ["C"]


def test_build_rows_impossible_returns_none_and_crossover_variant_succeeds():
    shares = [Counter({"A": 1, "B": 1, "C": 1})]
    assert H.build_rows_from_shares(shares, LEAF, "hub") is None
    rows, xc = H.build_rows_from_shares_with_crossover(shares, LEAF, "hub")
    assert xc == 1                                                  # 손: 홀수 4개 -> 1
    row = rows[0]
    assert len(row["segments"]) == 2
    assert len(row["crossover_after"]) == 1
    assert Counter(row["transistor_sequence"]) == Counter({"A": 1, "B": 1, "C": 1})
    for seg in row["segments"]:
        assert _walk_ok(seg, LEAF, "hub")
    # crossover_after = 첫 segment 마지막 인덱스
    assert row["crossover_after"] == [len(row["segments"][0]["transistor_sequence"]) - 1]


# ---- 옛 SD 대조 ----
ORACLE_CALLS = [
    ("hubleaf_sequence_node_path", (["A", "B", "B", "A"], "hub", LEAF)),
    ("hubleaf_sequence_node_path", (["A", "A"], "hub", LEAF)),
    ("hubleaf_sequence_node_path", (["A", "B", "A"], "hub", LEAF)),
    ("common_centroid_residual", ([{"transistor_sequence": ["A", "A", "B"]}, {"transistor_sequence": ["B", "A"]}],)),
    ("count_isolated_pairs", ([{"transistor_sequence": ["A", "B"]}, {"transistor_sequence": ["C"]}], ["A", "B", "C"])),
    ("repair_row_parity", ([Counter({"A": 1, "B": 1, "C": 1}), Counter({"A": 1})], LEAF, "hub")),
    ("repair_row_parity", ([Counter({"A": 3, "B": 1, "C": 1}), Counter({"B": 2, "C": 1}), Counter({"A": 1})], LEAF, "hub")),
    ("build_rows_from_shares", ([Counter({"A": 2, "B": 2}), Counter({"A": 1, "C": 3})], LEAF, "hub")),
    ("build_rows_from_shares_with_crossover", ([Counter({"A": 1, "B": 1, "C": 1}), Counter({"A": 2, "B": 1})], LEAF, "hub")),
]


@pytest.mark.parametrize("name,args", ORACLE_CALLS, ids=[c[0] for c in ORACLE_CALLS])
def test_same_as_oracle(name, args, sd, serialize):
    import copy
    new = getattr(H, name)(*copy.deepcopy(args))
    old = getattr(sd, "_" + name)(*copy.deepcopy(args))
    assert serialize(new) == serialize(old)
