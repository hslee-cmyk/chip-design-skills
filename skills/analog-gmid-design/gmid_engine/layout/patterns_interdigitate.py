"""MOD7 1D interdigitation 배치 `interdigitate_layout` -- 옛 stick_diagram.py 본문 복사(L10).

원문 대조(design_mod7_layout.md 7절, Maloberti Layout02.pdf p.15): 표 값 전부 일치(오기 0).
주석 정정(정의 밖에만 적는다 -- 정의 안 주석·docstring 은 해시 보존을 위해 원본 그대로):
  - 원문의 `*` 표시는 3x 열만이 아니라 base 열(AB*, ABC*, ABCD*, AABA*)에도 있다.
  - ABCD 3x `ABCBCADBCDA` 는 원문도 11자(A3 B3 C3 D2) -- 원문 자체의 불균형. 표 경로는 nf (3,3,3,2)
    에서만 맞는다.

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from collections import Counter

from ._helpers_hubleaf import (
    build_rows_from_shares as _build_rows_from_shares,
    build_rows_from_shares_with_crossover as _build_rows_from_shares_with_crossover,
    common_centroid_residual as _common_centroid_residual,
    count_isolated_pairs as _count_isolated_pairs,
    hubleaf_sequence_node_path as _hubleaf_sequence_node_path,
    repair_row_parity as _repair_row_parity,
)


INTERDIGITATION_PATTERNS = {
    "A":     {1: "A",     2: "AA",         3: "AAA",              4: "AAAA"},
    "AB":    {1: "AB",    2: "ABBA",       3: "ABBAAB",           4: "ABABBABA"},          # 3x '*'
    "ABC":   {1: "ABC",   2: "ABCCBA",     3: "ABCBACBCA",        4: "ABCABCCBACBA"},      # 3x '*'
    "ABCD":  {1: "ABCD",  2: "ABCDDCBA",   3: "ABCBCADBCDA",      4: "ABCDDCBAABCDDCBA"},  # 3x '*'
    "ABA":   {1: "ABA",   2: "ABAABA",     3: "ABAABAABA",        4: "ABAABAABAABA"},
    "ABABA": {1: "ABABA", 2: "ABABAABABA", 3: "ABABAABABAABABA",  4: "ABABAABABAABABAABABA"},
    "AABA":  {1: "AABA",  2: "AABAABAA",   3: "AABAAABAAABA",     4: "AABAABAAAABAABAA"},  # 3x '*'
    "AABAA": {1: "AABAA", 2: "AABAAAABAA", 3: "AABAAAABAAAABAA",  4: "AABAAAABAAAABAAAABAA"},
}


def _try_interdigitation_table_match(names: list, leaf_of: dict, hub_net, counts: dict,
                                      base: str, repeat: int | None) -> dict | None:
    """`interdigitate_layout()`가 쓰는 문헌 표(`INTERDIGITATION_PATTERNS`) 기반 경로 —
    `_try_pattern_table_match()`(common_centroid 쪽)와 대칭되는 구조다. `repeat`을
    명시하면 그 값만, 안 하면 표의 전체 repeat 중 각 소자의 실제 `n_fingers`(`counts`)와
    정확히 일치하는 것을 자동으로 찾는다. 찾은 패턴이 실제 hub-leaf 오일러 경로로 유효한지
    `_hubleaf_sequence_node_path()`로 검증하고, 실패하면(개수 불일치 또는 hub-leaf 무효)
    `None`을 반환해 호출자가 crossover-tolerant 경로로 폴백하게 한다. `base` 자체가
    없거나 소자 개수가 패턴 글자 수와 안 맞으면(호출자의 구조적 실수) `ValueError`."""
    if base not in INTERDIGITATION_PATTERNS:
        raise ValueError(f"알 수 없는 base pattern: {base} (사용 가능: {list(INTERDIGITATION_PATTERNS)})")
    table = INTERDIGITATION_PATTERNS[base]
    letters = sorted(set(next(iter(table.values()))))
    if len(letters) != len(names):
        raise ValueError(f"base={base}는 {len(letters)}개 소자 패턴인데 소자는 {len(names)}개다")
    if repeat is not None and repeat not in table:
        raise ValueError(f"{base}에 대해 {repeat}배 변형이 없다(정의된 repeat: {sorted(table)})")
    letter_to_name = dict(zip(letters, names))
    for rep in ([repeat] if repeat is not None else sorted(table)):
        seq = [letter_to_name[ch] for ch in table[rep]]
        actual = Counter(seq)
        if any(actual.get(nm, 0) != counts[nm] for nm in names):
            continue
        node_path = _hubleaf_sequence_node_path(seq, hub_net, leaf_of)
        if node_path is None:
            continue
        return {
            "transistor_sequence": seq, "node_sequence": node_path,
            "segments": [{"transistor_sequence": seq, "node_sequence": node_path}],
            "crossover_after": [],
        }
    return None


def interdigitate_layout(transistors: list, base: str | None = None, repeat: int | None = None) -> dict:
    """hub-leaf 소자들의 1행 interdigitation 배치를 찾는다 — `common_centroid_layout()`
    와 동일한 반환 형식(`rows`/`method`/`crossover_count`/`residual`/`isolated_pairs`)이고
    내부에서 직접 검증한다. `base`(+`repeat`)를 주면 `INTERDIGITATION_PATTERNS` 문헌 표에서
    각 소자의 `n_fingers`와 정확히 맞고 hub-leaf로도 유효한 repeat를 찾아 그 결과
    (`method="pattern_table"`, crossover 0)를 우선 쓴다. 표에 안 맞거나(`base` 생략 포함)
    표 경로가 hub-leaf 무효면, 소자 개수 비율에 맞춘 배치를 직접 구성해 유효성을 검증하고
    (`method="search"`) — crossover 없이 안 되면 `find_min_crossover_layout()`으로 최소
    crossover 배치로 폴백해 사실상 실패하지 않는다(`common_centroid_layout(n_rows=1)`
    과 원리가 같다 — 상세 이력은 consistency-map.md 37차/38차, gap-findings.md §18/§23 참고).
    """
    if len(transistors) < 1:
        raise ValueError("최소 1개 소자가 필요하다")
    hub_nets = {t.source for t in transistors}
    if len(hub_nets) != 1:
        raise ValueError(f"모든 소자가 같은 hub(source)를 공유해야 한다 — 실제: {sorted(hub_nets)}")
    hub_net = next(iter(hub_nets))
    names = [t.name for t in transistors]
    if len(set(names)) != len(names):
        raise ValueError(f"소자 이름에 중복이 있다: {names}")
    leafs = [t.drain for t in transistors]
    if len(set(leafs)) != len(leafs):
        raise ValueError(f"모든 소자의 drain(leaf)이 서로 달라야 한다: {leafs}")
    leaf_of = dict(zip(names, leafs))
    counts = {t.name: t.n_fingers for t in transistors}

    if base is not None:
        matched = _try_interdigitation_table_match(names, leaf_of, hub_net, counts, base, repeat)
        if matched is not None:
            return {"rows": [matched], "names": names, "residual": 0.0,
                    "isolated_pairs": 0, "crossover_count": 0, "method": "pattern_table"}

    share = Counter(counts)
    repaired = _repair_row_parity([share], leaf_of, hub_net)
    rows = _build_rows_from_shares(repaired, leaf_of, hub_net) if repaired is not None else None
    crossover_count = 0
    if rows is None:
        rows, crossover_count = _build_rows_from_shares_with_crossover([share], leaf_of, hub_net)
    return {
        "rows": rows, "names": names,
        "residual": _common_centroid_residual(rows),
        "isolated_pairs": _count_isolated_pairs(rows, names),
        "crossover_count": crossover_count, "method": "search",
    }
