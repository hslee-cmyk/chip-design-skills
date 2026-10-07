"""MOD7 최소 crossover 배치 `find_min_crossover_layout` -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations


from .euler_graph import build_graph
from .euler_condition import check_euler_condition
from .euler_trail import hierholzer


def _mirror_node_map_from_pairs(matching_pairs: list, transistors: list) -> dict:
    """`matching_pairs`(2-tuple 이름 쌍 목록, N-way 그룹은 호출자가 이미
    `itertools.combinations(names, 2)`로 펼쳐서 넘긴다는 기존 관례 그대로)와 각 소자의
    connectivity로부터 **net 레벨** 거울 대응(`node_map`)을 역산한다 — `find_min_
    crossover_layout()`의 odd_nodes 짝짓기가 소자 이름이 아니라 net 이름 단위라서 필요.

    쌍 (a,b)마다: 두 소자가 **한쪽 끝(source 또는 drain)을 공유**하면 그 공유 net은
    자기대응(축 위의 노드)이고 나머지 끝끼리 대응한다(예: M1a/M1b가 source=Vx를
    공유하면 Vx는 자기대응, drain끼리인 N1a2a<->N1b2b가 대응). **공유하는 끝이
    없으면**(branch_symmetric처럼 양쪽 다 다른 net) 같은 역할(source<->source,
    drain<->drain)끼리 대응한다고 가정한다 — 매칭쌍으로 선언된 이상 같은 구조적
    역할이라는 게 유일하게 근거 있는 기본 가정이다. 체인으로 전이(propagate)할 필요
    없이 각 쌍이 그 자체로 필요한 대응을 준다(실측 확인: current_reuse_telescopic_ota
    M6 그룹에서 M2a/M2b가 서로 공유 끝이 없어도 이 규칙만으로 바로 Vom1<->Vop1이
    나온다)."""
    by_name = {t.name: t for t in transistors}
    node_map: dict = {}

    def _add(a, b):
        if a == b:
            node_map[a] = a
        else:
            node_map.setdefault(a, b)
            node_map.setdefault(b, a)

    for pair in matching_pairs:
        a_name, b_name = pair
        ta, tb = by_name.get(a_name), by_name.get(b_name)
        if ta is None or tb is None:
            continue
        if ta.source == tb.source:
            _add(ta.source, ta.source)
            _add(ta.drain, tb.drain)
        elif ta.drain == tb.drain:
            _add(ta.drain, ta.drain)
            _add(ta.source, tb.source)
        else:
            _add(ta.source, tb.source)
            _add(ta.drain, tb.drain)
    return node_map


def _pair_odd_nodes_by_mirror(odd_nodes: list, node_map: dict) -> tuple:
    """`odd_nodes`(짝수 개)를 `node_map`(net 거울 대응) 기준 우선순위로 짝짓는다 —
    세션15 M6 그룹 설계 논의에서 확정한 3단계 규칙:

    1. 진짜 거울쌍(둘 다 odd_nodes에 있고 `node_map[a]==b`)을 먼저 짝짓는다 — 대칭축
       반대편 끝이라 여기서 crossover가 생겨도 대칭 구조가 안 깨지는 가장 정당화되는
       절단점.
    2. 남은 자기대응 노드(`node_map[n]==n`, 대칭축 위의 허브)와 orphan 노드(`node_map`에
       아예 없음, 미매칭 가지의 끝)를 짝짓는다 — orphan으로 이어지는 미매칭 가지는
       원래 그 허브에서 갈라져 나온 것이므로 되짚어 잇는 게 가장 짧고 자연스럽다.
    3. 그래도 남으면(예: orphan이 허브보다 많은 경우) 근거를 지어낼 실제 사례가 아직
       없으므로 기존 방식(순서대로 2개씩)으로 폴백한다 — 각 단계 내부의 후보가 여럿일
       때도(자기대응 노드 2개 이상 등) 지금은 리스트 순서대로만 짝짓는다("더 가까운
       쪽끼리" 같은 거리 기반 규칙은 실제로 그런 다중 사례가 나올 때 근거를 갖고 추가).

    반환: `(pairs, fallback_used)` — `fallback_used`는 3단계가 실제로 발동했는지."""
    remaining = list(odd_nodes)
    used: set = set()
    pairs = []

    for a in remaining:
        if a in used:
            continue
        b = node_map.get(a)
        if b is not None and b != a and b in remaining and b not in used:
            pairs.append((a, b))
            used.add(a)
            used.add(b)

    tier2_pool = [n for n in remaining if n not in used]
    self_mapped = [n for n in tier2_pool if node_map.get(n) == n]
    orphans = [n for n in tier2_pool if n not in node_map]
    for h, o in zip(self_mapped, orphans):
        pairs.append((h, o))
        used.add(h)
        used.add(o)

    leftover = [n for n in remaining if n not in used]
    fallback_used = len(leftover) > 0
    for i in range(0, len(leftover) - 1, 2):
        pairs.append((leftover[i], leftover[i + 1]))
    return pairs, fallback_used


def _build_crossover_segments(transistors: list, pairs: list) -> list:
    """`pairs`(홀수차수 노드 완전짝짓기)로 가상 edge를 추가해 오일러 회로를 만들고
    `hierholzer()`로 계산한 뒤, 가상 edge가 나온 지점마다 끊어서 m개의 실제 trail
    (segments)로 분해한다 -- `find_min_crossover_layout()`의 핵심 계산이었는데,
    **세션17**에 pairs 후보별로 재사용할 수 있도록 뽑아냈다(`_select_crossover_pairing()`이
    후보 채점에 쓴다). `transistors`로 매번 `build_graph()`를 새로 부르므로(순수 함수라
    결정적) 호출자가 그래프를 미리 mutate해둘 필요가 없다."""
    g = build_graph(transistors)
    for k, (u, w) in enumerate(pairs):
        edge_id = f"__crossover_virtual__{k}"
        g.edges[edge_id] = ("__virtual__", u, w)
        g.adjacency[u].append((edge_id, w))
        g.adjacency[w].append((edge_id, u))
    verdict2 = check_euler_condition(g)
    assert verdict2.kind == "circuit", (
        f"가상 edge로 홀수차수 전부 짝지었는데도 circuit이 안 됐다(내부 로직 오류): {verdict2}"
    )
    node_seq, tr_seq = hierholzer(g, verdict2.start)

    # 가상 edge 중 첫 번째가 나온 바로 다음 지점부터 시작하도록 순환을 재정렬 --
    # 이러면 "마지막 가상 edge 이후 ~ 배열 끝"과 "배열 시작 ~ 첫 가상 edge 이전"처럼
    # 순환 경계에 걸쳐 갈라지는 실제 trail이 생기지 않는다.
    virtual_positions = [i for i, name in enumerate(tr_seq) if name == "__virtual__"]
    rotate_at = virtual_positions[0] + 1
    tr_seq = tr_seq[rotate_at:] + tr_seq[:rotate_at]
    node_seq = node_seq[rotate_at:] + node_seq[1:rotate_at + 1]

    segments = []
    cur_tr, cur_nodes = [], [node_seq[0]]
    for i, name in enumerate(tr_seq):
        if name == "__virtual__":
            if cur_tr:
                segments.append({"transistor_sequence": cur_tr, "node_sequence": cur_nodes})
            cur_tr, cur_nodes = [], [node_seq[i + 1]]
        else:
            cur_tr.append(name)
            cur_nodes.append(node_seq[i + 1])
    if cur_tr:
        segments.append({"transistor_sequence": cur_tr, "node_sequence": cur_nodes})

    total_real = sum(len(s["transistor_sequence"]) for s in segments)
    expected_total = sum(t.n_fingers for t in transistors)
    assert total_real == expected_total, (
        f"trail 분해 후 실제 finger 총합({total_real})이 입력 총합({expected_total})과 "
        f"다르다(내부 로직 오류)"
    )
    return segments


def _count_matching_pair_splits(segments: list, matching_pairs: list,
                                 pair_sensitivity: dict | None = None):
    """`segments`(각 `{"transistor_sequence":[...]}`)에서 선언된 `matching_pairs` 중 두
    소자가 **완전히 서로 다른** segment에만 걸쳐 있는(=crossover로 물리적으로 갈라진) 개수를
    센다(세션17) -- 세션16 D-1에서 확인된 문제("선언된 진짜 거울쌍을 최우선으로 짝짓기"가
    실제로는 매칭쌍을 갈라놓는 최악의 선택이었던 M6 그룹 사례)를 정량화한 채점 기준.
    두 소자가 최소 한 segment라도 공유하면(n_fingers>1이라 여러 segment에 걸칠 수 있음)
    "완전히 갈라진" 것으로 안 본다 -- 부분적으로라도 같이 있는 게 아예 갈라진 것보다 낫다는
    보수적 기준, 지금까지 실제로 관찰된 사례(전부 n_fingers=1)에서는 이 구분이 결과에
    영향을 주지 않는다.

    **`pair_sensitivity`(세션17 신설, 선택)**: `{pair: "ratio"|"offset"}`(다른 함수들과
    동일 계약)을 주면 반환값이 스칼라 대신 `(offset_splits, other_splits)` **튜플**이
    된다 -- Python 튜플 비교는 사전식(lexicographic)이라, 호출자(`_select_crossover_
    pairing()`)가 이 값을 그대로 비교하면 **offset 쌍이 갈라지는 걸 ratio/branch_
    symmetric 쌍이 갈라지는 것보다 항상 더 나쁘게** 채점한다 -- offset(진짜 differential
    pair)은 CMRR/PSRR 민감도 때문에 갈라지면 안 되는 우선순위가 더 높다는 게
    `audit_row_split()` §2.7과 동일한 원칙(사용자 확인, 세션17). 선언 안 된 쌍은
    `other_splits`(ratio와 동급, 보수적 기본값)로 취급한다. `pair_sensitivity=None`
    (기본값)이면 기존과 완전히 동일하게 스칼라 총합 하나만 반환(하위호환)."""
    seg_of: dict = {}
    for i, seg in enumerate(segments):
        for name in seg["transistor_sequence"]:
            seg_of.setdefault(name, set()).add(i)

    if pair_sensitivity is None:
        split = 0
        for a, b in matching_pairs:
            segs_a, segs_b = seg_of.get(a, set()), seg_of.get(b, set())
            if segs_a and segs_b and segs_a.isdisjoint(segs_b):
                split += 1
        return split

    def _sensitivity_of(a, b):
        for key in ((a, b), (b, a), frozenset({a, b})):
            if key in pair_sensitivity:
                return pair_sensitivity[key]
        return None  # 선언 안 된 쌍 -- other_splits와 동급으로 보수적 처리

    offset_splits, other_splits = 0, 0
    for a, b in matching_pairs:
        segs_a, segs_b = seg_of.get(a, set()), seg_of.get(b, set())
        if segs_a and segs_b and segs_a.isdisjoint(segs_b):
            if _sensitivity_of(a, b) == "offset":
                offset_splits += 1
            else:
                other_splits += 1
    return (offset_splits, other_splits)


def _is_perfect_crossover_score(score) -> bool:
    """`_count_matching_pair_splits()`가 스칼라(0)든 `pair_sensitivity` 튜플((0,0))이든
    "분할 없음"을 한 곳에서 판정한다(세션17) -- `_select_crossover_pairing()`의 조기
    종료/조기 채택 조건에 재사용."""
    return score == 0 or score == (0, 0)


_MAX_CROSSOVER_PAIRING_NODES = 8  # (2m-1)!! -- m=4(8노드)면 105후보, m=5(10노드)면 945로


def _enumerate_perfect_matchings(nodes: list):
    """`nodes`(짝수 개)의 가능한 모든 완전짝짓기를 생성한다(재귀, `(2m-1)!!`개) --
    `_select_crossover_pairing()`이 후보 전수 대입에 쓴다(세션17)."""
    if not nodes:
        yield []
        return
    first, rest = nodes[0], nodes[1:]
    for i in range(len(rest)):
        remaining = rest[:i] + rest[i + 1:]
        for sub in _enumerate_perfect_matchings(remaining):
            yield [(first, rest[i])] + sub


def _select_crossover_pairing(odd_nodes: list, node_map: dict, transistors: list,
                               matching_pairs: list, pair_sensitivity: dict | None = None) -> tuple:
    """**세션17** -- 세션16 D-1 발견(`_pair_odd_nodes_by_mirror()`의 tier1 "선언된 진짜
    거울쌍을 최우선으로 짝짓기"가 M6 그룹 실측에서 실제로는 matching_pairs를 갈라놓는
    최악의 선택이었음, `probe_crossover_pairing_alternatives.py`)을 일반화한다.

    "그럴듯한 절단점"을 손으로 하나 고르는 대신, 가능한 완전짝짓기 후보를 실제로
    `_build_crossover_segments()`로 구성해보고 `_count_matching_pair_splits()`로
    matching_pairs가 몇 개나 갈라지는지 직접 채점한다(세션11부터의 "탐색 대신 구성 후
    검증" 원칙 그대로) -- crossover_count(m-1) 자체는 T-join 정리로 어떤 짝짓기를
    쓰든 불변이므로(위 `find_min_crossover_layout()` docstring), 짝짓기 선택은 오직
    "어디서 갈라지는가"만 바꾼다.

    `_pair_odd_nodes_by_mirror()`(기존 3단계 휴리스틱)의 결과를 기본 후보로 채점하고,
    이미 분할 없음이면(더 나아질 여지가 없음) 그대로 채택해 전수 탐색을 생략한다(흔한
    경우를 빠르게 처리). 분할이 있고 `len(odd_nodes)<=_MAX_CROSSOVER_PAIRING_NODES`면
    가능한 완전짝짓기 전부를 전수 대입해 분할이 더 적은 후보를 찾으면 채택(분할 없음을
    찾으면 즉시 중단). 동점이면 먼저 발견된 후보를 유지한다(이 이상의 타이브레이크 근거는
    아직 없음 -- 실제 다중 사례가 나오면 근거를 갖고 추가). `len(odd_nodes)`가 캡을
    넘으면 전수 탐색을 생략하고 휴리스틱 결과만 쓴다(정직한 한계).

    **`pair_sensitivity`(세션17 신설, 선택)**: 주면 `_count_matching_pair_splits()`가
    `(offset_splits, other_splits)` 튜플을 반환하게 되고, 튜플의 사전식 비교 덕에 offset
    (진짜 differential pair, CMRR 민감도) 쌍이 갈라지는 게 ratio/branch_symmetric 쌍이
    갈라지는 것보다 항상 먼저(더 나쁘게) 채점된다 -- 두 종류를 동등하게 셌던 기존 방식과
    달리, "둘 다 완전히 안 갈라지는 배치가 없으면 offset을 먼저 보호"하는 우선순위를 준다
    (사용자 확인, 세션17). `None`(기본값)이면 기존과 완전히 동일(하위호환).

    반환: `(pairs, segments, fallback_used, search_skipped)`."""
    heuristic_pairs, fallback_used = _pair_odd_nodes_by_mirror(odd_nodes, node_map)
    heuristic_segments = _build_crossover_segments(transistors, heuristic_pairs)
    heuristic_score = _count_matching_pair_splits(heuristic_segments, matching_pairs, pair_sensitivity)

    search_skipped = len(odd_nodes) > _MAX_CROSSOVER_PAIRING_NODES
    if _is_perfect_crossover_score(heuristic_score) or search_skipped:
        return heuristic_pairs, heuristic_segments, fallback_used, search_skipped

    best_pairs, best_segments, best_score = heuristic_pairs, heuristic_segments, heuristic_score
    for candidate in _enumerate_perfect_matchings(list(odd_nodes)):
        segments = _build_crossover_segments(transistors, candidate)
        score = _count_matching_pair_splits(segments, matching_pairs, pair_sensitivity)
        if score < best_score:
            best_pairs, best_segments, best_score = candidate, segments, score
            if _is_perfect_crossover_score(best_score):
                break
    return best_pairs, best_segments, fallback_used, search_skipped


def find_min_crossover_layout(transistors: list, matching_pairs: list | None = None,
                               pair_sensitivity: dict | None = None) -> dict:
    """N개(N>=1) 소자가 전부 같은 hub_net을 공유하고 서로 다른 leaf로 가는 hub-leaf
    구조를 **최소 개수의 crossover routing**(열 사이를 metal+via로 건너뛰어 연결하는
    배선)만으로 실현하는 배치를 찾는다. 우선순위는 항상 crossover가 0인(=단일 연속
    diffusion, 진짜 오일러 trail) 배치이고, 그게 불가능할 때만 최소 crossover 배치로
    넘어간다 — `check_euler_condition()`이 "impossible"이라고 포기하던 지점을 이어받는다.

    **원리(그래프 이론 — route inspection/T-join의 표준 결과)**: 연결된 그래프에서 홀수
    차수 노드가 2m개(m>=0)면, 그 그래프의 모든 edge를 **정확히 m개의 trail**(각각은
    끊김 없는 walk)로 쪼갤 수 있고 이보다 적은 개수로는 안 된다(m=0이면 오일러 회로
    1개, m=1이면 오일러 경로 1개 — 둘 다 기존 `check_euler_condition()`이 이미 처리하는
    경우다). m개의 trail을 하나의 물리 배치로 이어붙이려면 **m-1번의 crossover**가
    필요하다(trail 사이를 이어주는 접합부).

    **구현**: 홀수차수 노드 2m개를 전부 짝지어 m개의 **가상 edge**를 그래프에 추가하면
    모든 노드가 짝수차수가 돼(항상 성립 — 짝짓기 방법과 무관하게 이 성질은 불변) 전체가
    오일러 회로가 된다. `hierholzer()`로 이 회로 전체를 계산한 뒤, 가상 edge가 나온
    지점마다 실제로 끊어서(가상 edge 자체는 버림) m개의 진짜 trail로 분해한다 — 실측
    확인(2026-07-28): ABC(3소자 1개씩, 4개 홀수차수 노드, m=2) -> `[C,A]`+`[B]` 2개
    trail, crossover=1. ABCD(4소자 1개씩, 4개 홀수, m=2) -> crossover=1. 6소자 1개씩
    (6개 홀수, m=3) -> crossover=2. **어떤 짝짓기 방법을 쓰든 trail 개수(=m)는 항상
    같다**(T-join 정리 — 짝짓기가 다르면 어느 소자가 어느 trail에 속하는지만 달라지지,
    필요한 crossover 개수 자체는 안 바뀐다) — 그래서 짝짓기 방법을 바꿔도(아래
    `matching_pairs`) crossover_count 자체(=m-1)는 안 바뀌고, 어디서 끊기는지만
    달라진다.

    **`matching_pairs`(세션15 신설, 선택)**: `None`(기본값)이면 기존과 완전히 동일하게
    hub-leaf 사전조건(모든 소자가 같은 source 공유 + drain이 서로 달라야 함)을 그대로
    강제하고, 홀수차수 노드를 순서대로 2개씩 짝짓는다(하위호환, 기존 호출부
    `_build_rows_from_shares_with_crossover()`/`_common_centroid_nway_search()`는
    전부 이 경로). `matching_pairs`를 주면(2-tuple 이름 쌍 목록) hub-leaf 제약을 풀고
    **일반 그룹**(M3a/M6류, hub-leaf가 아닌 임의의 matching_pairs 구조)을 지원한다 —
    `_mirror_node_map_from_pairs()`로 net 거울 대응을 역산해 **세션17**
    `_select_crossover_pairing()`으로 짝짓는다(아래 참고).

    **세션17 갱신 — 짝짓기가 이제 "구성 후 검증"이다**: 세션15가 도입한 3단계 휴리스틱
    (`_pair_odd_nodes_by_mirror()`, "선언된 진짜 거울쌍을 최우선으로 짝짓기")은 그래프
    대칭 관점에서는 그럴듯했지만, 세션16 D-1에서 `current_reuse_telescopic_ota`의 M6
    그룹 실측으로 **실제로는 matching_pairs를 갈라놓는 최악의 선택**이었음이 드러났다
    (물리적 무게중심 대칭(3c)이 갈라지는 것과 그래프 레벨 대칭은 다른 개념 — 세션16 D-2).
    `_select_crossover_pairing()`은 이 휴리스틱을 기본 후보로 삼되, 실제로
    `_build_crossover_segments()`로 구성해 matching_pairs가 몇 개나 갈라지는지
    (`_count_matching_pair_splits()`) 채점하고, 분할이 있으면(그리고 홀수 노드 수가
    `_MAX_CROSSOVER_PAIRING_NODES` 이하면) 가능한 다른 완전짝짓기를 전수 대입해 분할이
    더 적은(이상적으로 0인) 후보로 교체한다 — crossover_count(m-1) 자체는 T-join 정리로
    어떤 짝짓기를 쓰든 불변이므로, 이 선택은 오직 "어디서 갈라지는가"만 바꾼다.

    **`pair_sensitivity`(세션17 신설, 선택)**: 주면 offset(진짜 differential pair)
    쌍이 갈라지는 걸 ratio/branch_symmetric 쌍보다 우선 피한다(CMRR 민감도 근거,
    `_select_crossover_pairing()`/`_count_matching_pair_splits()` docstring 참고).
    `matching_pairs=None`이면 이 인자는 무시된다.

    **입력**: `matching_pairs=None`이면 `transistors`(전부 같은 `source`=hub 공유,
    `drain`은 서로 달라야 함). `matching_pairs`가 있으면 이 제약 없음.
    **반환**: `{"segments": [{"transistor_sequence":[...], "node_sequence":[...]}, ...],
    "crossover_count": int, "odd_nodes": [...], "node_pairing_fallback_used": bool|None}`
    — `crossover_count=0`이면 `segments`가 1개뿐이고 그게 곧 `build_stick_diagram()`이
    주는 것과 같은 단일 연속 diffusion 결과다. `crossover_count`가 0보다 크면
    `segments`를 순서대로 이어붙이되 각 경계마다 실제로 crossover routing(추가
    metal+via)이 필요하다는 뜻이다. `node_pairing_fallback_used`는 `matching_pairs`가
    주어졌을 때만 의미 있다(대칭 인지 짝짓기가 다 못 짝지어 순서대로 폴백했는지) —
    `None`이면 `matching_pairs`를 안 준 기존 경로."""
    if not transistors:
        raise ValueError("최소 1개 이상의 소자가 필요하다")
    if matching_pairs is None:
        hub_nets = {t.source for t in transistors}
        if len(hub_nets) != 1:
            raise ValueError(f"모든 소자가 같은 hub(source)를 공유해야 한다 — 실제: {sorted(hub_nets)}")
        drains = [t.drain for t in transistors]
        if len(set(drains)) != len(drains):
            raise ValueError(f"모든 소자의 drain(leaf)이 서로 달라야 한다: {drains}")

    g = build_graph(transistors)
    verdict = check_euler_condition(g)
    if verdict.kind != "impossible":
        nodes, trs = hierholzer(g, verdict.start)
        return {
            "segments": [{"transistor_sequence": trs, "node_sequence": nodes}],
            "crossover_count": 0, "odd_nodes": verdict.odd_nodes,
            "node_pairing_fallback_used": None,
        }

    odd = verdict.odd_nodes  # 짝수 개(그래프 이론상 항상 짝수)
    if matching_pairs is None:
        pairs = [(odd[i], odd[i + 1]) for i in range(0, len(odd), 2)]
        fallback_used = None
        segments = _build_crossover_segments(transistors, pairs)
    else:
        node_map = _mirror_node_map_from_pairs(matching_pairs, transistors)
        pairs, segments, fallback_used, _search_skipped = _select_crossover_pairing(
            odd, node_map, transistors, matching_pairs, pair_sensitivity)

    return {"segments": segments, "crossover_count": len(segments) - 1, "odd_nodes": odd,
            "node_pairing_fallback_used": fallback_used}
