"""MOD7 hub 없는 matching 쌍(branch_symmetric, 캐스코드 대칭쌍)의 행 swap common-centroid 배치 (사용자 결정 2026-10-07 Q8 (ii)).

진입점: `row_swap_layout(transistors, n_rows, matching_pairs, pair_sensitivity) -> dict`.

branch_symmetric 쌍은 gate 만 공유하고 source·drain 이 서로 달라 공유 hub 가 없다 -- hub-leaf 패턴 함수(interdigitation·
hub-leaf common-centroid)의 전제 밖이고 interdigitation 은 그래프상 불가능하다. 그래서 행 swap 분배만 쓴다:
1. 복사 함수 `apply_explicit_row_split` 로 멤버마다 finger 를 `n_rows` 행에 고르게 나눈다(나머지는 앞 행부터 +1).
2. 행마다 `row_euler`(Euler -> 거울대칭 -> 최소 crossover)로 diffusion 섬(segment)을 정한다.
3. r 번째 행은 segment 순서를 r 칸 순환 회전한다(2멤버면 한 행 걸러 swap) -- 멤버마다 행 안 위치가 행을 따라 돌아
   무게중심이 모인다. 결과는 `canonical_row` 로 정규화.
반환 dict 는 복사 패턴 함수와 같은 모양: `rows`(list of {transistor_sequence, node_sequence, segments, crossover_after}),
`method` = "row_swap", `crossover_count`(행 Euler 의 crossover 합 -- 멤버 사이 섬 경계는 이 배치의 본래 구조라 세지 않는다),
`isolated_pairs`(복사 `count_isolated_pairs`), `residual`(복사 `common_centroid_residual`).
"""
from ._helpers_hubleaf import common_centroid_residual, count_isolated_pairs
from .canonical_rows import canonical_row
from .row_euler import row_euler
from .row_fold import apply_explicit_row_split

_METHOD = "row_swap"
_BLOCK = "row_swap"


def row_swap_layout(transistors, n_rows, matching_pairs, pair_sensitivity):
    """`transistors`(같은 kind, `n_fingers` 확정)를 `n_rows` 행 swap 분배로 배치한다."""
    split = apply_explicit_row_split({_BLOCK: list(transistors)}, {_BLOCK: n_rows})
    rows = []
    crossover_count = 0
    for r, pieces in enumerate(split.values()):
        res = row_euler(sorted(pieces, key=lambda t: t.name), matching_pairs, pair_sensitivity)
        crossover_count += res["crossover_count"]
        segments = list(res["segments"])
        shift = r % len(segments)
        segments = segments[shift:] + segments[:shift]
        boundaries = []
        cursor = -1
        for seg in segments[:-1]:
            cursor += len(seg["transistor_sequence"])
            boundaries.append(cursor)
        row = {"transistor_sequence": [name for seg in segments for name in seg["transistor_sequence"]],
               "segments": segments, "crossover_after": boundaries}
        rows.append(canonical_row(row, pieces))
    names = sorted(t.name for t in transistors)
    return {"rows": rows, "method": _METHOD, "crossover_count": crossover_count,
            "isolated_pairs": count_isolated_pairs(rows, names), "residual": common_centroid_residual(rows)}
