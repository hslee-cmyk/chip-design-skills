"""MOD7 common-centroid 배치 `common_centroid_layout` -- 옛 stick_diagram.py 본문 복사(L10).

원문 대조(design_mod7_layout.md 7절, Maloberti Layout02.pdf p.19): 1·2열 4가족 모두 일치(오기 0).
주석 정정(정의 밖에만 적는다 -- 정의 안 주석·docstring 은 해시 보존을 위해 원본 그대로):
  - 원문 p.19 3열(3행 배열)·4열(4행 배열)은 이 표에 없다. 표 경로는 n_rows = 2 에서만 쓰여 동작 영향 없음,
    3·4행 표 경로는 추가하지 않음(design 8절 3 기본안).
  - 원문에는 열 머리글이 없다. 키 1·2('반복 차수')는 해석이며 2열은 균일 2배가 아니다
    (ABCCBA -> ABCCBAABC, AAB -> AABBAA). 키는 개수 대조용이라 동작 영향 없음.
  - 결정론: 표 경로가 쓰는 `_hubleaf_sequence_node_path` 는 set 순회로 시작 노드를 고른다 --
    node_sequence 정규화는 `canonical_rows.canonical_row`.

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from collections import Counter

from .transistor import Transistor
from .euler_graph import build_graph
from .euler_condition import check_euler_condition
from .euler_trail import hierholzer
from .crossover import find_min_crossover_layout
from ._helpers_hubleaf import (
    build_rows_from_shares as _build_rows_from_shares,
    build_rows_from_shares_with_crossover as _build_rows_from_shares_with_crossover,
    common_centroid_residual as _common_centroid_residual,
    count_isolated_pairs as _count_isolated_pairs,
    hubleaf_sequence_node_path as _hubleaf_sequence_node_path,
    repair_row_parity as _repair_row_parity,
)


COMMON_CENTROID_PATTERNS = {
    ("ABBA", "BAAB"): {
        1: ("ABBA", "BAAB"),
        2: ("ABBAABBA", "BAABBAAB"),
    },
    ("ABA", "BAB"): {
        1: ("ABA", "BAB"),
        2: ("ABAABA", "BABBAB"),
    },
    ("ABCCBA", "CBAABC"): {
        1: ("ABCCBA", "CBAABC"),
        2: ("ABCCBAABC", "CBAABCCBA"),
    },
    ("AAB", "BAA"): {
        1: ("AAB", "BAA"),
        2: ("AABBAA", "BAAAAB"),
    },
}


def _common_centroid_from_pattern_table(name_a, leaf_a, name_b, leaf_b, hub_net,
                                         count_a, count_b, pattern_key) -> dict:
    """`_try_pattern_table_match()`(→ `common_centroid_layout()`)가 쓰는 표 기반
    경로 — 2-소자(A/B) 전용. `COMMON_CENTROID_PATTERNS`에서 `(count_a,count_b)`에 정확히
    맞는 repeat를 찾아 각 행을 만들고, 반환 직전 `_hubleaf_sequence_node_path()`로 1개
    metal layer 오일러 경로인지 검증(실패하면, 예: `ABA`/`BAB`는 항상 실패, `ValueError`).
    표에는 3-소자 패턴(`ABCCBA`류)도 있지만 이 함수는 2-소자 전용이라 그런 pattern_key를
    주면 명확한 `ValueError`(2026-07-28 실측 발견: letter_to_name에 A/B만 등록해놓고 이런
    pattern_key가 매치되면 예전엔 `KeyError`로 불명확하게 죽었다)."""
    if pattern_key not in COMMON_CENTROID_PATTERNS:
        raise ValueError(f"알 수 없는 pattern_key: {pattern_key}")
    letters = set(pattern_key[0]) | set(pattern_key[1])
    if letters - {"A", "B"}:
        raise ValueError(
            f"pattern_key={pattern_key}는 {sorted(letters)} 문자를 쓰는 3-소자 이상 패턴이다 -- "
            f"_common_centroid_from_pattern_table()은 2-소자(A/B) 전용이다(2026-07-28 실측 "
            f"발견: 예전 unit_cell_common_centroid_layout()은 letter_to_name에 A/B만 등록해놓고 "
            f"이런 pattern_key를 주면 KeyError로 불명확하게 죽었다)."
        )
    match = None
    for repeat, (top_pat, bot_pat) in COMMON_CENTROID_PATTERNS[pattern_key].items():
        total_a = top_pat.count("A") + bot_pat.count("A")
        total_b = top_pat.count("B") + bot_pat.count("B")
        if total_a == count_a and total_b == count_b:
            match = (repeat, top_pat, bot_pat)
            break
    if match is None:
        raise ValueError(f"{pattern_key}에 count_a={count_a}, count_b={count_b}에 맞는 repeat가 "
                          f"없다(정의된 repeat: {list(COMMON_CENTROID_PATTERNS[pattern_key])})")
    repeat, top_pat, bot_pat = match
    letter_to_name = {"A": name_a, "B": name_b}
    leaf_of = {name_a: leaf_a, name_b: leaf_b}
    rows = []
    for row_pattern in (top_pat, bot_pat):
        trs = [letter_to_name[ch] for ch in row_pattern]
        node_seq = _hubleaf_sequence_node_path(trs, hub_net, leaf_of)
        if node_seq is None:
            raise ValueError(
                f"pattern_key={pattern_key}의 행 순서 {row_pattern}은 hub-leaf 구조로는 "
                f"1개 metal layer 오일러 경로가 아니다 — 이 pattern_key는 추가 layer 없이는 "
                f"이 구조에 못 쓴다(예: 'ABA'/'BAB'는 항상 이렇게 실패한다). 다른 pattern_key를 "
                f"쓰거나 `pattern_key=None`(그래프 기반 계산)을 대신 쓸 것."
            )
        rows.append({"transistor_sequence": trs, "node_sequence": node_seq})
    return {
        "rows": rows, "pattern": pattern_key, "repeat": repeat, "hub_net": hub_net,
        "leaf_of": leaf_of,
        "total_a": sum(r["transistor_sequence"].count(name_a) for r in rows),
        "total_b": sum(r["transistor_sequence"].count(name_b) for r in rows),
    }


def _try_pattern_table_match(names: list, leafs: list, hub_net, counts: dict) -> dict | None:
    """`common_centroid_layout()`가 탐색 경로로 가기 전에, N=2이고 `COMMON_CENTROID_
    PATTERNS`의 2-소자 항목(`ABBA`/`BAAB`, `ABA`/`BAB`, `AAB`/`BAA` — 3-소자 이상인
    `ABCCBA`류는 제외, §18에서 hub-leaf 자체가 불가능함을 이미 확인) 중 주어진 개수와
    정확히 맞고 hub-leaf로 실제 유효한 repeat가 있으면 그 결과를 반환한다.

    2026-07-28 4차 신설(사용자 요청 — "표 기반 경로도 nway에 흡수해서 common_centroid_
    layout을 없앨 수 없나"). **탐색 경로가 불균등 비율에서 이 표만큼 못하는 걸 실측
    확인한 뒤 추가**: count_a=4,count_b=2(2:1 비율)를 탐색 경로에 넣으면 비례
    라운드로빈+균등분할이 회전/swap 후보를 못 만들어 residual=0.75가 나오는데, 표의
    `AAB`/`BAA`(정확히 2:1) 패턴은 검증된 residual=0을 낸다 — 있으면 항상 이걸 먼저
    쓴다. 두 소자 중 어느 쪽이 표의 'A'/'B'에 대응하는지 모르므로 양방향 다 시도한다.
    표에 맞는 게 없거나(개수가 표의 어떤 repeat와도 안 맞음) 있어도 hub-leaf로 무효
    (`ABA`/`BAB`류)면 `None`(호출자가 탐색 경로로 폴백)."""
    if len(names) != 2:
        return None
    name_a, name_b = names
    leaf_a, leaf_b = leafs
    count_a, count_b = counts[name_a], counts[name_b]
    for pattern_key in COMMON_CENTROID_PATTERNS:
        letters = set(pattern_key[0]) | set(pattern_key[1])
        if letters - {"A", "B"}:
            continue  # 3-소자 이상 패턴(ABCCBA류) — 이 경로 대상 아님
        for na, la, nb, lb, ca, cb in (
            (name_a, leaf_a, name_b, leaf_b, count_a, count_b),
            (name_b, leaf_b, name_a, leaf_a, count_b, count_a),
        ):
            try:
                return _common_centroid_from_pattern_table(na, la, nb, lb, hub_net, ca, cb, pattern_key)
            except ValueError:
                continue
    return None


def common_centroid_layout(transistors: list, n_rows: int | None = None,
                                 max_candidates: int = 24) -> dict:
    """N개(N>=2) 소자의 connectivity(`Transistor` 리스트 — 전부 같은 `source`를 hub로
    공유하고 서로 다른 `drain`을 leaf로 가짐, `n_fingers`가 각 소자의 목표 개수)를 받아
    common-centroid 배치를 자동으로 찾는다.

    2026-07-28 신설(여러 단계로 발전). 처음엔 2-소자 전용 `common_centroid_layout()`을
    3-소자로 확장해달라는 요청에서 출발했으나, `COMMON_CENTROID_PATTERNS`의 3-소자 패턴
    (`ABCCBA`/`CBAABC`)이 hub-leaf 구조로는 **애초에 실현 불가능**함을 실측 확인
    (`_hubleaf_sequence_node_path()`가 모든 repeat에서 `None`)한 뒤 — N개 leaf 회전으로
    N개 행에 배치하면 항상 정확한 common-centroid가 됨을 증명해 별도 함수로 만들었다.
    이후 사용자가 소자 개수가 달라도, row 개수를 N 위아래로 자유롭게 지정해도 최적안을
    찾도록 일반화를 요청했고, 마지막엔 `common_centroid_layout()`의 문헌 비율 패턴
    (`pattern_key=...`)까지 이 함수 하나로 흡수해달라고 요청 — **`common_centroid_
    layout()`은 이제 완전히 제거되고 이 함수 하나만 남았다**(2-소자 표 기반 경로 포함).

    **경로 1 — `n_rows=None`(또는 `target_rows==N`) + 모든 소자 개수가 같음(증명된
    최적)**: `_common_centroid_nway_exact()`로 간다 — N개 leaf가 전부 hub 하나에만
    연결되므로 이름을 순환 회전해도 그래프 automorphism이 성립하고, N개 행 전체에서
    모든 소자가 모든 열을 정확히 1번씩 방문함이 증명돼 있다(실측 확인: N=3, 열평균 완전
    일치) — **잔차가 정확히 0**이다. N=2 균등 개수를 넣으면 옛 `common_centroid_layout
    (pattern_key=None)`의 swap과 동등(회전 1회) — 실측으로 완전히 같은 결과임을 확인했었다.

    **경로 2 — N=2 + `target_rows==2` + 개수가 다름(비율)**: `_try_pattern_table_match()`
    로 간다 — `COMMON_CENTROID_PATTERNS`의 2-소자 문헌 패턴(예: `AAB`/`BAA`=2:1)이 정확히
    맞으면 그 검증된 결과(잔차 0)를 쓴다. 2026-07-28 흡수 통합 — 옛 `common_centroid_
    layout(pattern_key=...)`과 동일 알고리즘(`_common_centroid_from_pattern_table()`),
    양방향(어느 소자가 표의 'A'/'B'인지) 다 시도한다. **탐색 경로(아래)가 불균등 비율에서
    이 표만큼 못하는 걸 실측 확인한 뒤 통합**: count_a=4,count_b=2를 탐색 경로에 넣으면
    residual=0.75가 나오는데, 표의 `AAB`/`BAA`는 검증된 residual=0을 낸다 — 표에 맞는
    게 있으면 항상 먼저 쓴다. 표에 맞는 게 없으면(개수가 표의 어떤 repeat와도 안 맞음)
    경로 3(탐색)으로 넘어간다.

    **2026-07-28 3차 — crossover 폴백**: row_0을 균등 분배(+홀짝 보정)로도 단일 연속
    diffusion(0 crossover)을 못 만들면(예: N=3, count=3 -> `[1,1,1]`, 3개 leaf 전부
    홀수), 예전엔 여기서 `ValueError`로 포기했다. 그런데 회전 증명(위 문단)은 row_0가
    **어떤 방식으로 계산됐든**(그래프로 직접 계산한 것이든, crossover를 섞어 만든 것이든)
    성립한다 — 회전은 순수 relabeling(그래프 automorphism)이라 row_0 내부에 crossover가
    있어도 상관없이 "N개 행 전체에서 모든 소자가 모든 열을 정확히 1번씩 방문"이라는
    성질이 그대로 유지되기 때문이다(실측 확인: N=3/count=3을 crossover 1개로 만든 뒤
    회전해도 **잔차가 여전히 정확히 0**). 그래서 이제 0-crossover가 안 되면
    `find_min_crossover_layout()`으로 **최소 crossover** 배치를 만들어 그걸 회전한다 —
    **거의 모든 (N, count) 조합이 성공**하고(이전에 "진짜 불가능"으로 확인됐던 10개
    조합 전부 crossover 1~2개로 해결), `잔차는 여전히 0`이되 `crossover_count`가 0보다
    커질 수 있다. 우선순위는 항상 0-crossover 먼저(이 폴백은 진짜 안 될 때만 발동).

    **경로 3 — 그 외(경로 1/2 둘 다 해당 안 됨: 소자 개수가 다르고 표에도 안 맞거나,
    `n_rows`를 N과 다르게 명시)**: `_common_centroid_nway_search()`로 간다 — 이 경로는
    **증명된 최적이 아니라 candidate 생성 + objective(잔차)로 정렬하는 휴리스팁 탐색**
    이다(이 파일의 `search_stack_finger_w()`/`skyline_pack_best_width()`와 같은 철학).
    소자들을 비율에 맞게 최대한 고르게 섞은 순서(비례 라운드로빈)를 만들고, 목표 행
    개수만큼 균등 길이로 잘라 각 행의 소자별 개수를 정한 뒤, 잘린 지점(phase)을 여러 개
    시도해 그중 오일러 조건을 만족하고 objective(`(crossover_count, isolated_pairs,
    residual)` 사전식)가 가장 작은 걸 고른다. **`n_rows`가 N보다 작으면**(회전을 다
    못 채움) 잔차가 0이 아닐 수 있고, **`n_rows`가 N보다 크면**(더 잘게 쪼갬) 소자별
    finger가 여러 행에 나뉜다. 슬라이싱만으로 오일러 조건이 깨지는 조합(홀수차수 leaf
    3개 이상)이 나오면 먼저 인접 행끼리 1개씩 주고받는 보정(parity repair, 물리적 비용
    없음)을 시도하고, 그것도 안 되면 **경로 1과 같은 crossover 폴백**을 적용한다(2026-07-28
    4차 — 이제 이 경로도 사실상 실패하지 않는다). **한계(정직하게 문서화)**: 이 잔차
    지표는 각 행 내부의 x(열) 위치만 정규화해서 비교한다 — 소자 총 개수가 서로 크게
    다르면(예: 어떤 소자가 극소수 행에만 존재) y방향(어느 행에 있는지) 비대칭까지는
    잡지 못한다. 개수가 비슷할수록, `n_rows`가 N에 가까울수록 결과가 좋다 — 모든
    (n_rows, 개수) 조합에서 낮은 잔차를 보장하지 않는다.

    **입력**: `transistors`(길이 N>=2, 전부 같은 `source`=hub 공유, `drain`은 서로 달라야
    함, 이름 중복 불가), `n_rows`(선택 — 없으면 위 기본 규칙), `max_candidates`(경로 3에서
    시도할 phase 후보 수 상한).

    **반환**: `{"rows": [{"transistor_sequence":[...], "node_sequence":[...],
    "segments":[...], "crossover_after":[...]}, ...], "hub_net":..., "leaf_of":
    {name: leaf}, "names": [...], "residual": float, "isolated_pairs": int,
    "crossover_count": int, "method": "rotation_exact"|"pattern_table"|"search"}`. 각 행의
    `"crossover_after"`는 `transistor_sequence`상에서 그 인덱스 **바로 다음**에 crossover
    routing 접합이 필요하다는 뜻(빈 리스트면 crossover 없음, `"segments"`는 그 접합으로
    나뉘는 각 조각의 독립적인 `transistor_sequence`/`node_sequence`)."""
    if len(transistors) < 2:
        raise ValueError(f"최소 2개 소자가 필요하다(n={len(transistors)})")
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
    n = len(names)

    all_equal = len(set(counts.values())) == 1
    target_rows = n_rows if n_rows is not None else n
    if target_rows < 1:
        raise ValueError(f"n_rows={n_rows}는 1 이상이어야 한다")

    # target_rows==N(소자 수) + 개수 전부 같으면, n_rows를 사용자가 명시했든 기본값이든
    # 항상 회전 경로가 있고 그게 증명된 최적(잔차 0)이다 — 2026-07-28 실측으로 발견된 버그
    # 수정: 이전엔 "n_rows를 명시하면 무조건 탐색 경로"로 보내서, 명시된 n_rows가 우연히
    # N과 같은 경우(예: 2-소자를 2행에)도 탐색을 거쳤다. 그런데 탐색 경로(비례 라운드로빈+
    # 균등분할)는 **하나의 선형 시퀀스를 자르는 방식**이라 "두 행이 서로 swap된 관계"인
    # 후보를 구조적으로 만들어내지 못한다(주기적인 시퀀스를 반으로 자르면 항상 똑같은 두
    # 조각만 나온다 — 사용자가 N=2 사례로 실측 확인: n_fingers=2일 때 잔차가 0이어야
    # 하는데 탐색 경로는 1.0을 냈다). 회전 경로를 쓸 수 있는 상황이면 항상 그것부터 쓸 것.
    if target_rows == n and all_equal:
        result = _common_centroid_nway_exact(names, leafs, hub_net, counts[names[0]])
        result["residual"] = 0.0
        result["isolated_pairs"] = 0  # row_0에 항상 N개 소자 전부가 있고 회전은 relabel일 뿐이라 항상 0
        result["method"] = "rotation_exact"
        return result

    # N=2 + target_rows=2 + 개수가 다름(비율): COMMON_CENTROID_PATTERNS의 2-소자 문헌
    # 패턴(예: AAB/BAA=2:1)이 정확히 맞을 수 있다 — 2026-07-28 4차(사용자 요청: "표 기반
    # 경로도 nway에 흡수"). 탐색 경로(비례 라운드로빈+균등분할)는 불균등 비율에서 회전/swap
    # 후보를 못 만들어 문헌 패턴보다 훨씬 나쁜 잔차를 낼 수 있음을 실측 확인했다(예:
    # count_a=4,count_b=2에서 탐색 경로 residual=0.75, 표 기반 경로는 검증된 residual=0)
    # — 표에 맞는 패턴이 있으면 항상 그걸 먼저 쓴다.
    if n == 2 and target_rows == 2:
        matched = _try_pattern_table_match(names, leafs, hub_net, counts)
        if matched is not None:
            for row in matched["rows"]:
                row["segments"] = [{"transistor_sequence": row["transistor_sequence"],
                                     "node_sequence": row["node_sequence"]}]
                row["crossover_after"] = []
            matched["names"] = names
            matched["residual"] = 0.0
            matched["isolated_pairs"] = 0
            matched["crossover_count"] = 0
            matched["method"] = "pattern_table"
            return matched

    return _common_centroid_nway_search(names, leaf_of, hub_net, counts, target_rows, max_candidates)


def _fix_block_parity(block_sizes: list) -> list:
    """`_common_centroid_nway_exact()`가 "최대한 고르게" 나눈 `block_sizes`가 우연히 홀수
    항목이 3개 이상이라 오일러 조건이 깨질 때(예: n=4, count=20 -> [5,5,5,5], 전부 홀수),
    합계는 그대로 두고 홀수 항목 두 개를 짝지어 1개씩 서로 주고받는다(하나는 +1, 하나는
    -1 -> 둘 다 짝수가 됨) — row_0의 블록 배분은 무엇이든 회전이 잔차 0을 보장하므로
    (docstring 참고), 조금 덜 균등해도 홀짝만 맞으면 똑같이 최적이다. 홀수 항목 개수의
    홀짝(mod 2)은 이 연산으로 안 바뀌는 불변량이라(합계의 홀짝과 같다), 합계가 짝수면
    홀수 항목 0개까지, 홀수면 1개가 남을 때까지 줄인다. `-1`할 항목이 1(그 이상 줄이면
    0이 돼 무효)뿐이라 짝지을 수 없으면(극단적으로 작은 count) 그 지점에서 멈춘다 — 남은
    배분으로도 안 되면 호출자가 명확한 ValueError를 낸다."""
    sizes = list(block_sizes)
    target_odd = sum(sizes) % 2
    for _ in range(len(sizes) * 2):
        odd_idx = [i for i, s in enumerate(sizes) if s % 2 == 1]
        if len(odd_idx) <= max(target_odd, 0) or len(odd_idx) < 2:
            break
        # -1할 항목은 3 이상(홀수)이어야 0이 안 된다 -- 그런 항목을 우선 찾는다.
        donor = next((i for i in odd_idx if sizes[i] >= 3), None)
        if donor is None:
            break
        receiver = next(i for i in odd_idx if i != donor)
        sizes[donor] -= 1
        sizes[receiver] += 1
    return sizes


def _common_centroid_nway_exact(names: list, leafs: list, hub_net, count: int) -> dict:
    """`common_centroid_layout()`의 증명된-최적 경로(회전 대칭, 잔차 0) — 소자 개수가
    전부 같을 때만 쓴다. 원리: row_0을 계산한 뒤, 나머지 N-1개 행은 이름/leaf를 한 칸씩
    순환 회전만 해서 만든다(leaf가 전부 hub 하나에만 연결돼 회전이 항상 유효한 그래프
    automorphism — 2-소자 swap의 N-소자 일반화). N개 행 전체에서 매 열마다 회전이 정확히
    한 소자만 배정하므로(row_0의 블록 배분이 불균등해도 성립), 모든 소자의 열 평균이
    항상 정확히 일치한다(실측: N=3, 열평균 전부 일치).

    **row_0 계산 우선순위(2026-07-28 3차 — crossover 폴백 추가)**: (1) 균등 분배로 단일
    연속 diffusion(0 crossover) 시도 → (2) 안 되면 `_fix_block_parity()`로 홀짝만 보정한
    분배로 재시도(여전히 0 crossover) → (3) 그래도 안 되면 `find_min_crossover_layout()`
    으로 최소 crossover 배치로 폴백(**이 경로도 잔차 0은 그대로 유지된다** — 회전 증명은
    row_0가 어떻게 계산됐든 성립하기 때문, 실측 확인: N=3/count=3을 crossover 1개로
    만든 뒤 회전해도 잔차 정확히 0). (3)까지 왔다는 건 홀수차수 노드가 4개 이상이라는
    뜻이므로 `find_min_crossover_layout()`은 절대 실패하지 않는다(그래프 이론상 항상
    어떤 m으로든 분해 가능) — 즉 `count>=n`이기만 하면 이 함수는 이제 **항상 성공**한다."""
    n = len(names)
    if count < n:
        raise ValueError(
            f"count={count}가 소자 수 n={n}보다 작다 — row_0에서 소자마다 최소 1개 이상의 "
            f"finger가 필요한데(균등 분배 시 일부가 0개가 된다) count가 부족하다. count를 "
            f"늘리거나 n_rows를 소자 수보다 작게 지정해 탐색 경로로 갈 것"
        )
    base, extra = divmod(count, n)
    block_sizes = [base + (1 if i < extra else 0) for i in range(n)]

    row0_devices = [
        Transistor(names[i], "nmos", source=hub_net, drain=leafs[i], n_fingers=block_sizes[i])
        for i in range(n)
    ]
    g = build_graph(row0_devices)
    verdict = check_euler_condition(g)
    if verdict.kind == "impossible":
        # 2026-07-28 실측 발견: "최대한 고르게" 나눈 배분이 우연히 전부(또는 3개 이상)
        # 홀수가 되면(예: n=4, count=20 -> [5,5,5,5]) 오일러 조건이 깨지는데, 회전 자체는
        # row_0의 블록 배분이 무엇이든 항상 잔차 0을 보장하므로(docstring 참고) 조금 덜
        # 균등해도 홀짝만 맞는 배분([6,6,4,4] 등, 실측으로 유효함 확인)이 있으면 그걸 써도
        # 똑같이 최적이다 — 바로 포기하지 않고 홀수쌍을 짝지어 1개씩 주고받아(합계 불변)
        # 홀짝을 맞춰본다.
        fixed_sizes = _fix_block_parity(block_sizes)
        row0_devices = [
            Transistor(names[i], "nmos", source=hub_net, drain=leafs[i], n_fingers=fixed_sizes[i])
            for i in range(n)
        ]
        g = build_graph(row0_devices)
        verdict = check_euler_condition(g)
        block_sizes = fixed_sizes

    if verdict.kind == "impossible":
        # 2026-07-28 3차: 균등분배+홀짝보정도 안 되면 crossover를 허용해 최소 개수로
        # 폴백한다(사용자 요청 — find_min_crossover_layout()을 common_centroid에도 통합).
        mc = find_min_crossover_layout(row0_devices)
        row0_segments = mc["segments"]
        crossover_count = mc["crossover_count"]
    else:
        nodes0, row0 = hierholzer(g, verdict.start)
        row0_segments = [{"transistor_sequence": row0, "node_sequence": nodes0}]
        crossover_count = 0

    name_rotate = {names[i]: names[(i + 1) % n] for i in range(n)}
    leaf_rotate = {leafs[i]: leafs[(i + 1) % n] for i in range(n)}
    leaf_rotate[hub_net] = hub_net

    def _rotate_segments(segments):
        # 다음 행 = 직전 행을 이름/노드 둘 다 한 칸씩 회전 — leaf가 전부 hub 하나에만
        # 연결돼 구조적으로 동등하므로(자동사상), 회전된 시퀀스도 항상 유효한 walk임이
        # 이 자체로 보장된다(별도 계산 불필요, docstring 참고) — crossover가 있는 segment
        # 구성이어도 회전은 각 segment를 그대로 relabel할 뿐이라 segment 경계(=crossover
        # 위치)는 바뀌지 않는다.
        return [
            {"transistor_sequence": [name_rotate[x] for x in seg["transistor_sequence"]],
             "node_sequence": [leaf_rotate[x] for x in seg["node_sequence"]]}
            for seg in segments
        ]

    rows = []
    cur_segments = row0_segments
    for _ in range(n):
        flat_names = [nm for seg in cur_segments for nm in seg["transistor_sequence"]]
        flat_nodes = [nd for seg in cur_segments for nd in seg["node_sequence"]]
        crossover_after = []
        cursor = -1
        for seg in cur_segments[:-1]:
            cursor += len(seg["transistor_sequence"])
            crossover_after.append(cursor)
        rows.append({
            "transistor_sequence": flat_names, "node_sequence": flat_nodes,
            "segments": cur_segments, "crossover_after": crossover_after,
        })
        cur_segments = _rotate_segments(cur_segments)

    for name in names:
        actual = sum(r["transistor_sequence"].count(name) for r in rows)
        assert actual == count, f"{name}: 기대 {count}, 실제 {actual} (내부 로직 오류)"

    return {
        "rows": rows, "hub_net": hub_net, "leaf_of": dict(zip(names, leafs)), "names": names,
        "crossover_count": crossover_count,
    }


def _proportional_round_robin(counts: dict, names: list) -> list:
    """여러 소자를 비율에 맞게 최대한 고르게 섞은 순서를 만든다 — 옛 2-소자 전용
    `interdigitate_layout()` round-robin(2026-07-28 5차 재설계로 `interdigitate_layout()` 자체는 이제
    이 함수를 거치지 않고 `_build_rows_from_shares[_with_crossover]()`로 바로 검증까지
    끝내지만, 그 알고리즘을 N-소자로 처음 일반화한 게 이 함수다)의 계보. 매 단계 "지금까지
    배정된 비율(assigned/count)이 가장 작은" 소자를 고른다(가중 라운드로빈, 동률이면
    `names` 순서). `common_centroid_layout()`의 탐색 경로(`_common_centroid_nway_
    search()`)가 여러 행으로 자르기 전 기본 시퀀스를 만들 때 쓴다."""
    remaining = dict(counts)
    assigned = {nm: 0 for nm in names}
    total = sum(counts.values())
    seq = []
    for _ in range(total):
        best = min((nm for nm in names if remaining[nm] > 0),
                   key=lambda nm: (assigned[nm] / counts[nm], names.index(nm)))
        seq.append(best)
        assigned[best] += 1
        remaining[best] -= 1
    return seq


def _slice_into_rows(seq: list, target_rows: int, phase: int) -> list:
    """`seq`를 `phase`만큼 순환시킨 뒤 `target_rows`개로 길이가 최대한 균등하도록(나머지는
    앞쪽 행에 +1) 자른다 — `phase`를 바꾸면 다른 자르는 지점(=다른 소자 조합) 후보가
    나온다(`common_centroid_layout()`의 candidate 탐색용)."""
    seq2 = seq[phase:] + seq[:phase]
    total = len(seq2)
    base, extra = divmod(total, target_rows)
    chunks, idx = [], 0
    for r in range(target_rows):
        length = base + (1 if r < extra else 0)
        chunks.append(seq2[idx:idx + length])
        idx += length
    return chunks


def _common_centroid_nway_search(names: list, leaf_of: dict, hub_net, counts: dict,
                                  target_rows: int, max_candidates: int) -> dict:
    """`common_centroid_layout()`의 휴리스팁 탐색 경로 — 증명된 최적이 아니라
    candidate 생성 + objective로 정렬하는 방식(이 파일의 `search_stack_finger_w()`/
    `skyline_pack_best_width()`와 같은 철학). 비례 라운드로빈으로 만든 병합 순서를 여러
    지점(phase)에서 잘라 `target_rows`개 행 후보를 만들고, 실현 가능한 후보 중
    **`(crossover_count, isolated_pairs, residual)` 튜플이 가장 작은** 걸 고른다(사전식
    정렬 — crossover가 하나라도 더 필요한 후보는 잔차/격리가 아무리 좋아도 후순위, 그
    다음이 격리, 그 다음이 잔차).

    **행 하나를 만드는 우선순위(2026-07-28 4차 — 탐색 경로에도 crossover 폴백 추가)**:
    (1) `_repair_row_parity()`로 인접 행끼리 1개씩 주고받아(물리적 비용 없음, 순전히
    어느 행에 어느 소자를 배정하느냐의 조합 문제) 전부 0-crossover로 만들 수 있으면 그걸
    쓴다(`_build_rows_from_shares()`). (2) 그게 안 되면 `find_min_crossover_layout()`
    (`_build_rows_from_shares_with_crossover()`)으로 최소 crossover 배치로 폴백한다 —
    이 폴백은 그래프 이론상 항상 성공하므로(§19), **이 함수는 이제 실패하지 않는다**
    (이전엔 모든 phase가 (1)에서 실패하면 `ValueError`였다). crossover_count가 0인
    phase가 하나라도 있으면 그게 항상 우선(사전식 정렬 1순위)이므로, crossover는 정말
    필요한 경우에만 채택된다.

    ⚠️ 2026-07-28 실측으로 발견: `n_rows`가 총 finger 수에 비해 너무 크면(예: N=2,
    count=2씩, n_rows=4 -> 모든 행이 길이 1) 소자들이 전부 자기 혼자만의 행에 격리돼도
    (`['A'],['B'],['A'],['B']`류) 잔차가 0으로 나올 수 있다 — 각자 행 내부에서 대칭으로
    보이기 때문이다(0.5 neutral 처리 참고, `_common_centroid_residual()` docstring). 이건
    `n_rows`가 물리적으로 의미 있는 공존을 만들기엔 너무 많이 쪼갠 것이지 진짜 좋은
    배치가 아니다. `isolated_pairs`를 crossover 다음 순위로 넣어 "같은 행에 아예 못
    있었던" 후보보다는 "같이는 있었지만 완벽히 대칭은 아닌" 후보를 우선하도록 했다 —
    단, 시도한 모든 phase가 격리를 못 피하면(행 길이 자체가 구조적으로 1일 수밖에
    없으면) 최선이어도 격리가 남을 수 있다. 반환된 `"isolated_pairs"`가 0이 아니면 그
    사실 자체를 보고(호출자가 `n_rows`를 줄이는 게 나을 수 있다는 신호)."""
    seq = _proportional_round_robin(counts, names)
    total = len(seq)
    n_phases = min(max_candidates, total) if total > 0 else 1
    best = None
    for phase in range(max(1, n_phases)):
        chunks = _slice_into_rows(seq, target_rows, phase)
        shares = [Counter(chunk) for chunk in chunks]
        repaired = _repair_row_parity(shares, leaf_of, hub_net)
        if repaired is not None:
            rows = _build_rows_from_shares(repaired, leaf_of, hub_net)
            crossover_count = 0
        else:
            rows = None
        if rows is None:
            # 0-crossover 보정이 안 됐으니(또는 방어적으로, repaired 검증과 실제 build
            # 사이에 불일치가 있어도) 원본 shares에 crossover 폴백을 적용한다 — 이 경로는
            # find_min_crossover_layout()이 그래프 이론상 항상 성공하므로 절대 실패하지
            # 않는다.
            rows, crossover_count = _build_rows_from_shares_with_crossover(shares, leaf_of, hub_net)
        residual = _common_centroid_residual(rows)
        isolated = _count_isolated_pairs(rows, names)
        score = (crossover_count, isolated, residual)
        if best is None or score < best[0]:
            best = (score, rows)
    if best is None:
        raise ValueError(
            f"n_rows={target_rows}로는 휴리스틱 탐색으로 실현 가능한 배치를 하나도 찾지 "
            f"못했다(최대 {n_phases}개 phase 시도, crossover 폴백까지 시도함 — 내부 로직 "
            f"오류일 가능성이 높다) — 행 개수를 조정하거나 소자 개수를 다시 확인할 것"
        )
    (crossover_count, isolated, residual), rows = best
    return {
        "rows": rows, "hub_net": hub_net, "leaf_of": dict(leaf_of), "names": list(names),
        "residual": residual, "isolated_pairs": isolated, "crossover_count": crossover_count,
        "method": "search",
    }
