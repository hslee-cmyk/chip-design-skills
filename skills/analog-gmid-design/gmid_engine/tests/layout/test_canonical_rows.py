"""layout/canonical_rows.py -- `canonical_row(seq_result, members)`(새 코드, CONTRACT 2).

기대값: 손계산(CONTRACT 2 유도 규칙: 시작 후보 = 그 열 소자들의 source·drain 넷을 sorted() 순서로, 끝까지 가는 첫 후보) +
결정론(PYTHONHASHSEED 1~5 별도 프로세스). 복사 원본(`interdigitate_layout`)은 같은 입력에서 seed 에 따라 node_sequence 가
달라짐을 같은 실행에서 확인한다(보정 대상이 실제로 존재 -- 공허 통과 방지).
"""
from __future__ import annotations

import copy

import pytest

from gmid_engine.layout.canonical_rows import canonical_row
from gmid_engine.layout.patterns_common_centroid import common_centroid_layout
from gmid_engine.layout.patterns_interdigitate import interdigitate_layout
from gmid_engine.layout.transistor import Transistor

A = Transistor("A", "nmos", source="hub", drain="da", n_fingers=1)
B = Transistor("B", "nmos", source="hub", drain="db", n_fingers=1)
A2 = Transistor("A", "nmos", source="hub", drain="da", n_fingers=2)


def walk_ok(ts, ns, members):
    by = {m.name: m for m in members}
    if not ts:
        return ns == []
    return len(ns) == len(ts) + 1 and all({ns[i], ns[i + 1]} == {by[n].source, by[n].drain} for i, n in enumerate(ts))


# ---- 손계산 (CONTRACT 2 오라클) ----
@pytest.mark.parametrize("ts,given_ns,members,expected", [
    (["A"], ["hub", "da"], [A], ["da", "hub"]),               # 유효 시작 {da, hub} -> 정렬 최소 da
    (["A"], ["da", "hub"], [A], ["da", "hub"]),
    (["A", "A"], ["hub", "da", "hub"], [A2], ["da", "hub", "da"]),
    (["A", "B"], ["da", "hub", "db"], [A, B], ["da", "hub", "db"]),   # 유효 시작 da 하나
    ([], [], [A], []),
])
def test_hand(ts, given_ns, members, expected):
    out = canonical_row({"transistor_sequence": ts, "node_sequence": given_ns}, members)
    assert out["node_sequence"] == expected
    assert out["transistor_sequence"] == ts


def test_sorted_min_valid_start_skips_invalid_min():
    a = Transistor("A", "nmos", source="a_hub", drain="z1")
    b = Transistor("B", "nmos", source="a_hub", drain="z2")
    # 후보 정렬 [a_hub, z1, z2]: a_hub 는 B 에서 막힘 -> z1
    assert canonical_row({"transistor_sequence": ["A", "B"]}, [a, b])["node_sequence"] == ["z1", "a_hub", "z2"]
    a2 = Transistor("A", "nmos", source="a_hub", drain="z1", n_fingers=2)
    # [A,A]: a_hub·z1 둘 다 유효 -> 정렬 최소 a_hub
    assert canonical_row({"transistor_sequence": ["A", "A"]}, [a2])["node_sequence"] == ["a_hub", "z1", "a_hub"]


def test_source_equals_drain():
    s = Transistor("S", "nmos", source="n", drain="n")
    assert canonical_row({"transistor_sequence": ["S"]}, [s])["node_sequence"] == ["n", "n"]


def test_independent_of_input_node_sequence():
    base = {"transistor_sequence": ["A", "A"]}
    outs = [canonical_row(dict(base, node_sequence=ns), [A2])["node_sequence"]
            for ns in (["hub", "da", "hub"], ["da", "hub", "da"], ["junk"], [])]
    assert outs == [["da", "hub", "da"]] * 4
    assert canonical_row(base, [A2])["node_sequence"] == ["da", "hub", "da"]     # node_sequence 키 없음도 같음


def test_segments_rederived_and_concatenated():
    row = {
        "transistor_sequence": ["A", "B"],
        "node_sequence": ["hub", "da", "hub", "db"],
        "segments": [{"transistor_sequence": ["A"], "node_sequence": ["hub", "da"]},
                     {"transistor_sequence": ["B"], "node_sequence": ["hub", "db"]}],
        "crossover_after": [0],
    }
    out = canonical_row(row, [A, B])
    assert out["segments"] == [{"transistor_sequence": ["A"], "node_sequence": ["da", "hub"]},
                               {"transistor_sequence": ["B"], "node_sequence": ["db", "hub"]}]
    assert out["node_sequence"] == ["da", "hub", "db", "hub"]
    assert out["crossover_after"] == [0]
    assert out["transistor_sequence"] == ["A", "B"]


def test_empty_segments_list_uses_whole_row():
    out = canonical_row({"transistor_sequence": ["A", "B"], "segments": []}, [A, B])
    assert out["node_sequence"] == ["da", "hub", "db"]


def test_other_keys_kept_and_input_not_mutated():
    row = {"transistor_sequence": ["A", "A"], "node_sequence": ["hub", "da", "hub"],
           "segments": [{"transistor_sequence": ["A", "A"], "node_sequence": ["hub", "da", "hub"]}],
           "crossover_after": [], "extra": {"k": 1}}
    snap = copy.deepcopy(row)
    out = canonical_row(row, [A2])
    assert row == snap
    assert out is not row
    assert out["extra"] == {"k": 1} and out["crossover_after"] == []
    assert out["segments"][0]["node_sequence"] == ["da", "hub", "da"]
    assert out["node_sequence"] == ["da", "hub", "da"]


def test_unknown_name_keyerror():
    with pytest.raises(KeyError):
        canonical_row({"transistor_sequence": ["A", "Z"]}, [A])


def test_no_valid_start_valueerror():
    a = Transistor("A", "nmos", source="h", drain="x")
    b = Transistor("B", "nmos", source="k", drain="y")
    with pytest.raises(ValueError):
        canonical_row({"transistor_sequence": ["A", "B"]}, [a, b])


# ---- 복사 함수 출력에 적용 ----
def test_unique_start_rows_unchanged_table_path():
    # CONTRACT 2 불변식 4 + 오라클: 2멤버 4:2 n_rows=2 표 경로 행은 시작 하나뿐 -> 입력과 같음
    a = Transistor("A", "nmos", source="hub", drain="da", n_fingers=4)
    b = Transistor("B", "nmos", source="hub", drain="db", n_fingers=2)
    res = common_centroid_layout([a, b], n_rows=2)
    assert res["method"] == "pattern_table"
    for row in res["rows"]:
        assert canonical_row(row, [a, b])["node_sequence"] == row["node_sequence"]
    assert [r["node_sequence"] for r in res["rows"]] == [["hub", "da", "hub", "db"], ["db", "hub", "da", "hub"]]


def test_walk_property_on_crossover_rotation_rows():
    devs = [Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=3) for n in "ABC"]
    res = common_centroid_layout(devs)
    assert res["crossover_count"] == 1                         # 손: [1,1,1] 홀수 4 -> segment 2개 행
    for row in res["rows"]:
        out = canonical_row(row, devs)
        assert len(out["segments"]) == 2
        for seg in out["segments"]:
            assert walk_ok(seg["transistor_sequence"], seg["node_sequence"], devs)
        assert out["node_sequence"] == [n for seg in out["segments"] for n in seg["node_sequence"]]
        assert out["transistor_sequence"] == row["transistor_sequence"]


# ---- 결정론: PYTHONHASHSEED 1~5 ----
SEED_CODE = r"""
from gmid_engine.layout.canonical_rows import canonical_row
from gmid_engine.layout.patterns_interdigitate import interdigitate_layout
from gmid_engine.layout.patterns_common_centroid import common_centroid_layout
from gmid_engine.layout.transistor import Transistor
out = {}
for nf in (1, 2):
    a = Transistor("A", "nmos", source="hub", drain="da", n_fingers=nf)
    res = interdigitate_layout([a], base="A")
    row = res["rows"][0]
    out["nf%d" % nf] = [res["method"], row["node_sequence"], canonical_row(row, [a])["node_sequence"]]
devs = [Transistor(n, "nmos", source="hub", drain="d" + n, n_fingers=3) for n in "ABC"]
res = common_centroid_layout(devs)
out["cc3x3"] = [repr(canonical_row(r, devs)) for r in res["rows"]]
RESULT = out
"""


def test_deterministic_across_hashseeds(seed_runner):
    runs = [seed_runner(SEED_CODE, s) for s in (1, 2, 3, 4, 5)]
    for key, expected in (("nf1", ["da", "hub"]), ("nf2", ["da", "hub", "da"])):
        assert all(r[key][0] == "pattern_table" for r in runs)              # 표 경로(보정 대상 경로)를 실제로 탐
        originals = {tuple(r[key][1]) for r in runs}
        canon = {tuple(r[key][2]) for r in runs}
        assert len(originals) >= 2, "복사 원본이 seed 1~5 에서 한 가지뿐 -- 보정 대상이 재현되지 않음: %r" % originals
        assert canon == {tuple(expected)}
    assert len({tuple(r["cc3x3"]) for r in runs}) == 1
