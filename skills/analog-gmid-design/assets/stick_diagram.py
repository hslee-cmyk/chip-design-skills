#!/usr/bin/env python
"""stick_diagram.py — 회로-무관(circuit-agnostic) stack 분할 + Euler trail stick diagram 생성기.

`references/stick-diagram-euler-layout.md`(Maloberti, *Layout of Analog CMOS IC* Part 2 요약)의
그래프화 규칙을 그대로 코드화한다:
    node = net(트랜지스터가 공유하는 source/drain 전기 노드)
    edge = finger 1개(트랜지스터 1개가 n_fingers개면 같은 두 노드 사이에 병렬 edge n_fingers개)
    MOS는 source/drain이 대칭이므로 무방향 multigraph로 다룬다.

이 모듈은 **어떤 회로든** 입력으로 받는다 — 특정 토폴로지(2단 OTA, folded cascode 등)를
하드코딩하지 않는다. 입력은 트랜지스터 리스트(이름, 극성, source net, drain net, finger 수)뿐이고,
출력은 stack별 stick sequence(오일러 경로/회로) 또는 "왜 안 되는지 + 무엇을 조정하면 되는지"
진단이다.

**이 모듈이 결정하지 않는 것**: 어떤 트랜지스터들을 같은 물리적 stack(행)으로 묶을지는 대칭성/
matching/well 요구사항이 얽힌 floorplanning 판단이라 일반적으로 자동화할 수 없다 — 기본값은
(극성, finger 폭)이 같은 소자를 자동으로 묶는 것뿐이고, 실제 설계에서는 `stack_id`를 직접 지정해
회로 지식을 반영해야 한다(`split_into_stacks` docstring 참고).

Sizing과의 관계: 이 모듈이 만드는 stick diagram 판정(오일러 조건 충족 여부, stack별 finger 수,
suggest_finger_adjustments의 조정 후보)은 `stick-diagram-euler-layout.md` §5 "sizing↔layout
피드백 루프"의 입력이다 — 이 모듈이 제안하는 finger 수 조정은 **반드시 그 문서 §5의 gm/ID
검증 체크리스트로 재검증한 뒤에만** 확정해야 한다. 이 모듈 자체는 회로 스펙(gain/GBW/noise 등)을
전혀 모른다 — 순수 그래프 이론(node/edge 연결성)만 다룬다.

주의: 아래 각 블록의 "# N) 제목" 주석은 **이 파일 안에서 코드가 작성된 순서를 정리한 것**이며
`stick-diagram-euler-layout.md`의 §번호와 대응하지 않는다(예: 이 파일의 "2.5)"는 finger 폭
정합성 검사이지만, .md의 §2.5는 완전히 다른 주제인 interdigitation이다 — 우연히 같은 숫자를
쓸 뿐 같은 절이 아니다). .md의 실제 어느 절과 관련 있는지는 각 함수 docstring 안에 인용된
`§X.Y` 표기를 따를 것 — 그 표기만 .md와 정확히 대응한다.
"""
from __future__ import annotations

import itertools
import json
import math
import os
from collections import Counter, defaultdict
from dataclasses import asdict as _dc_asdict, dataclass, field, replace as _dc_replace


# ---------------------------------------------------------------------------
# 1) 입력 표현
# ---------------------------------------------------------------------------

@dataclass
class Transistor:
    """stick diagram 계산에 필요한 최소 정보만 담는다 — bulk net, VT, 공정 파라미터는 이 모듈의
    관심사가 아니다(source/drain 연결성과 finger 수만 Euler 그래프에 영향을 준다). `gate`는
    Euler 분석 자체에는 쓰이지 않지만 §2.6 `find_matching_candidates()`가 matching 그룹
    (전류거울=gate 공유, 차동쌍=source 공유+gate 상이)을 구조적으로 찾아내는 데 필요하다."""

    name: str
    kind: str                      # 'nmos' | 'pmos' — 극성이 다르면 같은 diffusion을 공유 못 함
    source: str                    # source net 이름
    drain: str                     # drain net 이름
    n_fingers: int = 1              # finger 개수(짝/홀이 §2 stick 규칙의 핵심 변수)
    finger_w: float | None = None   # finger 1개당 W(같은 stack인지 판정 + §3.5 divisibility 검사에 사용)
    w: float | None = None          # 소자 전체 W(gm/ID sizing 결과값). finger_w와 함께 주면
                                     # §3.5 check_finger_width_compatibility()가 W/finger_w의
                                     # 정수 여부를 검사한다 — n_fingers 자체는 여전히 호출자가
                                     # 직접 정해서 넣는다(이 필드는 검증용이지 자동 계산용이 아니다).
    l: float | None = None          # channel length(m, gm/ID sizing 결과값 -- sizing_recipe.py의
                                     # sizing[name]["L"]에서 옴). finger_w/w와 동일한 선택적 필드
                                     # 패턴: 있으면 compute_row_geometry()가 실제 물리 폭 계산에
                                     # 쓰고, 없으면 그 소자는 근사 계산에서 빠진다(approx 플래그로
                                     # 명시, 조용히 대체하지 않음). 이 필드는 gm/ID 지식을 요구하지
                                     # 않는 순수 치수값이라 이 모듈의 "gm/ID를 모르는 순수 그래프
                                     # 모듈" 경계(위 모듈 docstring 20-24행)를 깨지 않는다.
    gate: str | None = None          # gate net 이름(선택) — §2.6 matching 그룹 자동 탐지에만 사용
    stack_id: str | None = None     # 명시적 stack 배정(지정 시 극성/폭 자동 그룹핑보다 우선)

    def __post_init__(self):
        if self.n_fingers < 1:
            raise ValueError(f"{self.name}: n_fingers는 1 이상이어야 한다")
        if self.kind not in ("nmos", "pmos"):
            raise ValueError(f"{self.name}: kind는 'nmos' 또는 'pmos'만 허용")


# ---------------------------------------------------------------------------
# 1.5) Interdigitation(PDF p.13~16, 1D finger 교차배열) + Common-Centroid(PDF p.17~19,
#      2D 사분면 배열) — unit cell 기반 matching의 근본 원리. §3.5의 "W는 finger 폭의
#      정수배"라는 제약이 우연이 아니라 이 방법론의 필연적 귀결임을 코드로 명시한다:
#      matching이 필요한 소자는 하나의 unit cell(finger)을 정수 개 병렬 배열해서 만들고,
#      그 unit cell들을 아래 패턴표로 교차 배열해 공정 gradient를 상쇄한다. Folded Cascode
#      M3/M4의 실제 finger 순서 `433PP443`이 interdigitation 패턴 하나를 적용한 결과다
#      (stick-diagram-euler-layout.md §2.5 참고).
# ---------------------------------------------------------------------------

# PDF p.15 "Interdigitiation Patterns" 표 — 두 matching 소자를 finger 단위로 한 행(row) 안에서
# 교차배열할 때 쓴다(1D). 각 base pattern의 2×/3×/4× 반복 변형. '*' 표시는 원문이 명시한
# 주의사항("not all the patterns permit a stacked layout") 대상이므로 채택 전 반드시 재확인할 것.
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

# PDF p.19 "Common Centroid Patterns" 표 — interdigitation과는 별개로, 소자(또는 interdigitated
# 블록) 전체를 **2행(위/아래 quadrant row)**으로 나눠 배치할 때 위/아래 각 행의 순서를 이 쌍으로
# 정한다(2D 사분면 배열, p.17~18의 DA/DB 대각선 배치가 이 표로 일반화된 것). key는 (위 행,
# 아래 행) 튜플, value는 반복 차수별 (위,아래) 문자열 쌍. 이미지에서 직접 옮긴 복잡한 2D 표라
# 실사용 전 원문 재확인을 권장한다.
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
        raise ValueError(f"모든 소자가 같은 hub(source)를 공유해야 한다 — 실제: {hub_nets}")
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


def build_mirror_symmetric_pattern(half: list, pair_map: dict, center=None) -> list:
    """PDF p.14 "Axis of Symmetries"의 탄생 원리를 직접 구현: **왼쪽 절반만 설계**하면
    오른쪽 절반은 "matching되는 소자쌍을 서로 바꾼 뒤 뒤집기"로 자동 생성된다 —
    interdigitation 패턴표(§ INTERDIGITATION_PATTERNS)가 전부 이 규칙을 만족하는
    것도 우연이 아니라 이 축대칭 요구사항 자체가 패턴의 정의이기 때문이다.

    `pair_map`은 서로 matching되는 소자를 맞바꾸는 매핑이다(예: {"M3":"M4","M4":"M3"}).
    축 위에 단독으로 걸쳐 좌우 양쪽에 나타나는 소자(예: 폴디드 캐스코드의 MP)는 자기 자신에
    매핑한다({"MP":"MP"}). `center`(선택)는 전체 길이가 홀수일 때 축 정중앙에 단독으로
    놓일 원소.

    검증된 예(stick-diagram-euler-layout.md §2.5.1): folded cascode top 행의 절반
    `["M5"]*6 + ["M3","M4","M4"]`에 `{"M3":"M4","M4":"M3","MP":"MP","M6":"M6",...}`류
    매핑을 적용하면 pptx 원본이 실제로 쓴 전체 시퀀스(M5×6, M3, M4, M4, MP, MP, M3, M3, M4,
    M6×6)와 정확히 일치한다.

    `pair_map`의 값이 `None`인 원소(세션12 신규 — 홀수 self-pair "다리")는 미러링하지 않는다:
    `half`에는 그대로 한 번 남지만 `mirrored` 쪽에서는 제외된다(대칭축 위에 걸치지 않고 한쪽
    끝에만 존재하는 소자 — `mirror_symmetric_trail()`의 다리 지원이 이 동작에 의존한다)."""
    mirrored = [pair_map[x] for x in reversed(half) if pair_map[x] is not None]
    return list(half) + ([center] if center is not None else []) + mirrored


@dataclass
class MirrorSymmetryVerdict:
    ok: bool


def check_mirror_symmetry(sequence: list, pair_map: dict) -> MirrorSymmetryVerdict:
    """`sequence`(finger 순서)가 `pair_map` 기준으로 중앙 수직축에 대해 좌우 대칭인지 검증한다
    (`build_mirror_symmetric_pattern()`의 역검증). 길이가 홀수면 정중앙 원소 하나는 비교에서
    제외한다(축 위에 단독으로 걸친 소자이므로 대응 상대가 없다).

    실사용 예: `check_mirror_symmetry(list("555555344PP334666666"),
    {"5":"6","6":"5","3":"4","4":"3","P":"P"}).ok` → `True` — folded cascode top 행의 실제
    finger 순서가 이 축대칭을 정확히 만족함을 이 함수로 재확인할 수 있다."""
    n = len(sequence)
    half = n // 2
    left, right = sequence[:half], sequence[n - half:]
    mirrored_left = [pair_map[x] for x in reversed(left)]
    return MirrorSymmetryVerdict(ok=mirrored_left == right)


def find_interleaved_symmetric_splits(count_a: int, count_b: int) -> list:
    """A, B가 서로 swap 파트너(예: pair_map={"A":"B","B":"A"})이고 **개별 finger 총합이
    홀수**라 각자 단독으로는 좌우 절반씩 나눌 수 없을 때, 두 소자를 섞어 배치하면 전체 대칭을
    살릴 수 있다 — folded cascode bottom row의 실제 사례(M9=3, M10=3, 둘 다 홀수)가 정확히
    이 경우다: 원본 시퀀스 `...9xxoo99nno...`에서 M9는 좌1/우2, M10은 좌2/우1로 **불균등하게**
    나뉘어 있지만, 두 소자가 서로의 불균형을 정확히 상쇄해 전체는 대칭이 된다.

    수학적으로: A가 왼쪽에 `a_left`개, B가 왼쪽에 `b_left`개 있으면, 대칭이 성립하려면
    `a_left == count_b - b_left`(B의 오른쪽 개수)이고 `b_left == count_a - a_left`(A의
    오른쪽 개수)여야 한다 — 이 두 식을 풀면 **count_a == count_b일 때만** 정수해가 존재한다
    (다르면 잔여 불균형이 남아 다른 소자로 흡수하거나, 폴디드 캐스코드의 MP처럼 축 위에 단독
    배치해야 한다).

    **"최대한 섞는다" 원칙(우선순위 정렬)**: 대칭 조건을 만족하는 후보가 여러 개일 때 전부
    matching 효과가 같은 건 아니다 — 한쪽에 몰아넣는 분할(`(0,3,3,0)`처럼 A와 B가 사실상 안
    섞이고 각자 한쪽 절반을 통째로 차지)은 그 방향의 공정 gradient를 전혀 상쇄하지 못하고,
    양쪽에 고르게 나뉜 분할(`(1,2,2,1)`처럼 양쪽 다 A·B가 섞여 있음)일수록 gradient 상쇄
    효과가 커진다 — interdigitation의 근본 목적(§2.5) 그 자체다. 그래서 이 함수는 결과를
    **"얼마나 고르게 섞였는가"(`|a_left - a_right|` 오름차순) 순으로 정렬**해서 반환한다 —
    맨 앞이 matching 효과가 가장 좋은 후보다. 실제 folded cascode(M9=3, M10=3)에서 pptx가
    채택한 `(1,2,2,1)`이 정확히 이 정렬의 1순위 후보와 일치한다(§9 Test 9).

    반환: `count_a == count_b`이면 `[(a_left, a_right, b_left, b_right), ...]`를 매칭 효과
    내림차순(=|a_left-a_right| 오름차순)으로 정렬해 반환, 아니면 빈 리스트. 정렬은 matching
    효과 기준일 뿐 오일러 조건(§3)까지 보장하지는 않는다 — 앞쪽 후보부터 순서대로 실제 stack에
    적용해 오일러 조건도 만족하는지 확인해서 최종 채택할 것.
    """
    if count_a != count_b:
        return []
    splits = [(k, count_a - k, count_a - k, k) for k in range(count_a + 1)]
    splits.sort(key=lambda s: abs(s[0] - s[1]))
    return splits


# ---------------------------------------------------------------------------
# 1.65) 2D Common-centroid 배치(unit-cell 기반) — §2.7
#       matching이 특히 까다로운 그룹에 1D interdigitation보다 한 단계 더 정밀한 배치를
#       주는 도구. "언제 이걸 쓰는지"는 §2.7의 실측 데이터 기반 기준을 따를 것.
# ---------------------------------------------------------------------------

def _hubleaf_sequence_node_path(trs: list, hub_net, leaf_of: dict):
    """주어진 finger 순서(trs)가 hub-leaf 그래프(공유 hub_net + 소자별 leaf_of[name])에서
    실제로 인접 finger가 공유 net을 갖는 유효한 오일러 경로/회로인지 **가정하지 않고 직접
    검증**한다 — 가능한 시작 노드(hub 또는 각 leaf)로 순회를 시도해 끝까지 막힘없이
    이어지면 그 node_sequence를 반환하고, 어느 시작점으로도 안 되면 None을 반환한다.
    `common_centroid_layout()`의 그래프 기반(rotation_exact) 경로가
    `build_graph()`+`hierholzer()`로 아예 유효한 순서를 계산해내는 것과 달리, 이 함수는
    **이미 정해진(패턴표에서 온) 순서 하나가 유효한지만**
    검사한다 — 표의 pattern_key마다 실제로 1개 metal layer로 실현 가능한지가 다르기
    때문에(§2.7.2: `ABBA`/`AAB`는 가능, `ABA`는 불가능, 실측으로 확인됨) 반드시 필요한
    검증 단계다."""
    candidate_starts = {hub_net} | {leaf_of[name] for name in trs}
    for n0 in candidate_starts:
        n = n0
        path = [n0]
        ok = True
        for name in trs:
            edge = {hub_net, leaf_of[name]}
            if n not in edge:
                ok = False
                break
            n = next(iter(edge - {n})) if len(edge) == 2 else n
            path.append(n)
        if ok:
            return path
    return None


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
        raise ValueError(f"모든 소자가 같은 hub(source)를 공유해야 한다 — 실제: {hub_nets}")
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


def _row_feasible(share, leaf_of: dict, hub_net) -> bool:
    """`share`(`{name: count}`)가 한 행(1개 metal layer, hub-leaf 오일러 walk)으로 실현
    가능한지 확인한다(실제 소자가 1개 이하면 자명하게 가능)."""
    trs = [Transistor(nm, "nmos", source=hub_net, drain=leaf_of[nm], n_fingers=c)
           for nm, c in share.items() if c > 0]
    if len(trs) <= 1:
        return True
    return check_euler_condition(build_graph(trs)).kind != "impossible"


def _repair_row_parity(shares: list, leaf_of: dict, hub_net, max_iters: int = 50):
    """`_slice_into_rows()`가 만든 소자별 개수 배분 중 오일러 조건이 깨진 행이 있으면
    (홀수차수 leaf 3개 이상), 그 행의 홀수-개수 소자 하나를 골라 인접 행과 1개씩
    주고받아본다 — 양쪽 다 실현 가능해지는 조합을 찾으면 채택(실측 확인: A=6/B=4/C=2를
    4행으로 나눌 때 슬라이싱만으로는 모든 phase가 실패했지만 이 보정으로 해결됨). 못
    고치면 `None`(그 phase는 이 target_rows로 포기)."""
    shares = [Counter(s) for s in shares]
    for _ in range(max_iters):
        bad = [i for i, s in enumerate(shares) if not _row_feasible(s, leaf_of, hub_net)]
        if not bad:
            return shares
        i = bad[0]
        fixed = False
        odd_names = [nm for nm, c in shares[i].items() if c % 2 == 1]
        for nm in odd_names:
            for j in (i - 1, i + 1):
                if j < 0 or j >= len(shares) or j == i:
                    continue
                trial_i, trial_j = dict(shares[i]), dict(shares[j])
                trial_i[nm] -= 1
                trial_j[nm] = trial_j.get(nm, 0) + 1
                if trial_i[nm] == 0:
                    del trial_i[nm]
                if _row_feasible(trial_i, leaf_of, hub_net) and _row_feasible(trial_j, leaf_of, hub_net):
                    shares[i], shares[j] = Counter(trial_i), Counter(trial_j)
                    fixed = True
                    break
            if fixed:
                break
        if not fixed:
            return None
    return None


def _build_rows_from_shares(shares: list, leaf_of: dict, hub_net):
    """각 행의 소자별 개수 배분(`shares`)을 실제 `build_graph()`+`hierholzer()`로 finger
    순서까지 계산한다 — **0-crossover 전용**, 실현 불가능한 행이 남아있으면 `None`(호출자가
    `_build_rows_from_shares_with_crossover()`로 폴백할지 판단). `"segments"`는 항상 행
    전체 1개짜리, `"crossover_after"`는 항상 빈 리스트(회전 경로와 스키마를 맞추기 위함)."""
    rows = []
    for share in shares:
        trs = [Transistor(nm, "nmos", source=hub_net, drain=leaf_of[nm], n_fingers=c)
               for nm, c in share.items() if c > 0]
        if not trs:
            rows.append({"transistor_sequence": [], "node_sequence": [], "segments": [], "crossover_after": []})
            continue
        g = build_graph(trs)
        v = check_euler_condition(g)
        if v.kind == "impossible":
            return None
        nodes, seq = hierholzer(g, v.start)
        rows.append({
            "transistor_sequence": seq, "node_sequence": nodes,
            "segments": [{"transistor_sequence": seq, "node_sequence": nodes}],
            "crossover_after": [],
        })
    return rows


def _build_rows_from_shares_with_crossover(shares: list, leaf_of: dict, hub_net):
    """`_build_rows_from_shares()`의 crossover-허용판(2026-07-28 4차 신설 — 탐색 경로에도
    회전 경로와 같은 crossover 폴백을 추가해달라는 요청) — **절대 실패하지 않는다**(각 행이
    0-crossover로 안 되면 `find_min_crossover_layout()`으로 최소 crossover 배치를 대신
    쓴다, `find_min_crossover_layout()` 자체가 그래프 이론상 항상 성공하므로). 반환:
    `(rows, total_crossover_count)` — `total_crossover_count`는 이 후보의 모든 행에 걸친
    crossover 총합(탐색 경로의 사전식 정렬 1순위 기준으로 쓰임, `_common_centroid_nway_
    search()` 참고)."""
    rows = []
    total_crossover = 0
    for share in shares:
        trs = [Transistor(nm, "nmos", source=hub_net, drain=leaf_of[nm], n_fingers=c)
               for nm, c in share.items() if c > 0]
        if not trs:
            rows.append({"transistor_sequence": [], "node_sequence": [], "segments": [], "crossover_after": []})
            continue
        g = build_graph(trs)
        v = check_euler_condition(g)
        if v.kind != "impossible":
            nodes, seq = hierholzer(g, v.start)
            rows.append({
                "transistor_sequence": seq, "node_sequence": nodes,
                "segments": [{"transistor_sequence": seq, "node_sequence": nodes}],
                "crossover_after": [],
            })
            continue
        mc = find_min_crossover_layout(trs)
        flat_names = [nm for seg in mc["segments"] for nm in seg["transistor_sequence"]]
        flat_nodes = [nd for seg in mc["segments"] for nd in seg["node_sequence"]]
        crossover_after = []
        cursor = -1
        for seg in mc["segments"][:-1]:
            cursor += len(seg["transistor_sequence"])
            crossover_after.append(cursor)
        rows.append({
            "transistor_sequence": flat_names, "node_sequence": flat_nodes,
            "segments": mc["segments"], "crossover_after": crossover_after,
        })
        total_crossover += mc["crossover_count"]
    return rows, total_crossover


def _common_centroid_residual(rows: list) -> float:
    """각 소자의 "행 내 상대 위치"(0~1, 그 행 길이로 정규화 — 행 길이가 달라도 비교
    가능하도록)를 전부 모아 평균 낸 뒤, 소자 간 평균 차이(최대-최소)를 잔차로 삼는다.
    0이면 완전한 common-centroid(모든 소자 평균 위치 일치).

    ⚠️ 2026-07-28 실측으로 발견/수정된 결함: 길이 1인 행을 그냥 건너뛰면(이전 버전),
    어떤 소자가 길이 1인 행에만 등장하고 길이 2 이상인 행에는 전혀 없을 때 그 소자가
    `positions`에 아예 안 잡혀 — 즉 존재하지 않는 것처럼 완전히 빠진 채로 잔차가
    계산됐다(실측: A만 있는 길이2 행 + B만 있는 길이1 행 2개로 구성하면 잔차=0.0이
    나왔다 — B가 통째로 빠졌는데 "완벽"으로 잘못 보고된 것). 길이 1인 행은 대신
    **중립값 0.5**(어느 쪽으로도 치우치지 않은 위치)를 부여해 그 소자가 반드시
    `positions`에 기록되도록 한다 — 0이나 1(양 끝) 대신 0.5를 쓰는 이유는 왼쪽/오른쪽
    치우침을 인위적으로 만들지 않기 위해서다. 길이 0인 행(소자 없음)만 실제로 건너뛴다."""
    positions = defaultdict(list)
    for row in rows:
        seq = row["transistor_sequence"]
        length = len(seq)
        if length == 0:
            continue
        if length == 1:
            positions[seq[0]].append(0.5)
            continue
        for i, nm in enumerate(seq):
            positions[nm].append(i / (length - 1))
    if not positions:
        return 0.0
    avgs = [sum(p) / len(p) for p in positions.values()]
    return max(avgs) - min(avgs)


def _count_isolated_pairs(rows: list, names: list) -> int:
    """`names`의 모든 소자 쌍 중, 단 하나의 행에서도 함께 등장한 적이 없는(=한 번도
    같은 행에 같이 배치되지 않은) 쌍의 개수를 센다. 2026-07-28 실측으로 발견된 잔차
    지표의 개념적 한계에 대응하기 위한 보조 지표: 소자 하나가 통째로 자기 행에만
    격리되면(예: A는 항상 자기 혼자만 있는 행, B도 항상 자기 혼자만 있는 행) 각자
    행 내부에서는 대칭적으로 보여 `_common_centroid_residual()`이 0에 가깝게 나올 수
    있지만, 실제로는 서로 전혀 섞이지 않은 것이라 진짜 common-centroid가 아니다. 0이면
    모든 쌍이 적어도 한 행에서 공존했다는 뜻(잔차가 낮다고 주장하기 전에 최소한의
    타당성 조건)."""
    cooccurred = set()
    for row in rows:
        present = set(row["transistor_sequence"])
        for i, a in enumerate(names):
            if a not in present:
                continue
            for b in names[i + 1:]:
                if b in present:
                    cooccurred.add((a, b))
    total_pairs = len(names) * (len(names) - 1) // 2
    return total_pairs - len(cooccurred)


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


# ---------------------------------------------------------------------------
# 1.65b) net 이름 대소문자 자기모순 스캔 — 공용 코어 (2026-07-28 추출)
#        `run_full_circuit_audit()` 2번 체크와 `check_symmetry_dispositions()` 0단계가
#        이 검사를 각자 복붙해서 갖고 있었다(사고9 — Vbias1/vbias1이 다른 net으로 인식되는
#        문제를 두 곳에서 독립적으로 재구현). 로직 자체가 아니라 "이 로직을 두 곳에 유지해야
#        한다"는 사실을 사람이 기억해야 하는 구조였으므로, 공용 헬퍼로 뽑아 양쪽이 호출하게
#        한다 — 동작은 기존과 동일(순수 리팩터), 앞으로 이 검사를 고치면 한 곳만 고치면 된다.
# ---------------------------------------------------------------------------

def _scan_case_collisions(net_names) -> dict:
    """net 이름들(순회 가능한 문자열 iterable)을 대소문자 무시하고 그룹핑해, 표기가
    다른(대소문자만 다른) net이 있으면 `{lower: {실제 표기, ...}, ...}`로 반환한다 — 비어
    있으면 전부 단일 표기라는 뜻."""
    net_variants = defaultdict(set)
    for net in net_names:
        net_variants[net.lower()].add(net)
    return {k: v for k, v in net_variants.items() if len(v) > 1}


# ---------------------------------------------------------------------------
# 1.7) Matching이 필요한 소자 그룹 자동 탐지 — §2.5 패턴을 "어디에" 적용할지 찾는 단계.
#      전체 카탈로그(차동쌍/전류거울/캐스코드쌍/R·C 비율/DAC 단위소자/bandgap 코어/래치
#      cross-coupled 쌍 등)는 stick-diagram-euler-layout.md §2.6 참고 — 이 중 구조적으로
#      (source/gate net 연결 패턴만으로) 자동 탐지 가능한 건 전류거울과 차동쌍 두 가지뿐이다.
#      나머지(캐스코드 대칭쌍, R/C 비율 등)는 회로 지식이 필요해 `stack_id`로 직접 표시해야 한다.
# ---------------------------------------------------------------------------

def find_matching_candidates(transistors: list, idiom_matches: list | None = None) -> dict:
    """구조적 신호만으로 matching **후보**(확정 아님)를 찾는다 — AI/설계자가 소자쌍을
    일일이 수동으로 훑지 않도록 후보를 미리 좁혀주는 게 이 함수의 존재 이유다(토큰 절약).
    자동 탐지 가능한 두 유형:

    - `current_mirror`: 같은 극성(kind) + 같은 gate net을 공유하는 2개 이상의 소자.
      (`gate`를 지정하지 않은 소자는 대상에서 제외된다.)
    - `diff_pair`: 같은 극성 + 같은 source net을 공유하지만 서로 다른 gate net을 가진
      정확히 2개의 소자(차동 입력쌍의 구조적 정의 그 자체 — W는 요구하지 않는다).
      **W가 둘 다 채워져 있으면**(사이징 이후) 추가로 W까지 일치해야 후보로 잡는다 —
      대형 회로에서 우연히 같은 source에 물린 무관한 소자를 걸러내는 오탐 방지 필터다.
      **W가 없으면**(사이징 이전, topology 저작 단계) 이 필터를 건너뛰고 구조적 신호만으로
      후보를 낸다 — 이 단계에선 어차피 모든 소자가 W가 없으므로 "필수 W 일치"를 요구하면
      diff_pair 후보가 영원히 하나도 안 나온다(2026-07-28 실측 발견, 함수가 원래 의도한
      "후보를 좁혀 토큰을 아낀다"는 목적을 사이징 전 단계에서 완전히 무력화시켰다 —
      analog-topology-json-library.gap-findings.md §3 참고).

    반환: `{"current_mirror": {(kind,gate): [Transistor,...], ...},
            "diff_pair": {(kind,source): [Transistor,Transistor], ...}}`

    이 함수가 찾아준 그룹은 그 자체로 "matching이 확정됐다"는 뜻이 아니라 §2.5의
    interdigitation/common-centroid 패턴을 적용할 **후보**다 — 실제 채택 여부와 어떤 패턴을
    쓸지는 여전히 설계자의 판단이다(예: 캐스코드 전류원처럼 gate를 공유해도 matching이
    중요하지 않을 수도 있고, 반대로 이 함수가 못 찾는 R/C 비율·캐스코드 대칭쌍은 실제로는
    matching이 필수인 경우가 많다).

    `idiom_matches`가 주어지면(§1.7a `find_idiom_matches()`의 반환값) 위 net-only
    그룹핑 대신 그 Match 리스트에서 직접 후보를 뽑는다 — `analog-grammar` skill의
    `idioms.m_mirror()`/`m_diffpair()`가 이미 "그룹 안에 diode-connected 레퍼런스가
    있는가"(current_mirror)/"둘 다 role=AMPLIFYING인가"(diff_pair)를 검증해서 Match를
    내므로, 이 함수는 이름을 Transistor로 변환만 한다. `idiom_matches=None`(기본값)
    이면 이 함수는 위 net-only 동작과 완전히 동일하다(하위호환, self-test로 확인).

    이 경로로 바뀌는 것: `current_mirror` 그룹핑이 `(kind, gate)`가 아니라
    `(kind, gate, source)`로 바뀐다(2026-08-06, `analog-topology-json-library`
    세션18 K/L절 M57/M58 오탐 계기 — gate만 같고 source가 다른 소자는 VGS 동일이
    보장되지 않아 진짜 current mirror가 아닐 수 있다). 부작용으로 "캐스코드 대칭쌍"
    (같은 gate, 다른 source — 예: M2a/M2b)은 이 경로에서 더 이상 안 잡힌다 —
    이건 `find_stacked_matching_candidates()`(§1.7c)가 별도 메커니즘(복합소자/스택
    상속)으로 커버한다. 상세 설계 근거: `references/analog-grammar-integration.md`.
    """
    if idiom_matches is not None:
        by_name = {t.name: t for t in transistors}
        current_mirror, diff_pair = {}, {}
        for m in idiom_matches:
            group = [by_name[n] for n in m.devices if n in by_name]
            if m.kind == "current-mirror" and len(group) >= 2:
                current_mirror[(group[0].kind, m.ports["bias"], m.ports["rail"])] = group
            elif m.kind == "differential-pair" and len(group) == 2:
                diff_pair[(group[0].kind, m.ports["tail"])] = group
        return {"current_mirror": current_mirror, "diff_pair": diff_pair}

    by_gate = defaultdict(list)
    by_source = defaultdict(list)
    for t in transistors:
        if t.gate is not None:
            by_gate[(t.kind, t.gate)].append(t)
        by_source[(t.kind, t.source, t.w)].append(t)

    current_mirror = {k: v for k, v in by_gate.items() if len(v) >= 2}
    diff_pair = {}
    for (kind, source, w), group in by_source.items():
        # ⚠️ 2026-08-14 세션34 정정(실측으로 발견 -- 합성 fixture에서 재현, 실제 4개 라이브러리
        # 회로에는 우연히 노출된 적 없었던 잠재 버그) -- source가 레일(vdd/gnd/vss)이면 제외해야
        # 한다. 레일은 무한 전류를 공급하는 외부 전원이라 "같은 tail을 공유해 전류가 스플릿된다"는
        # diff_pair의 정의 자체가 성립하지 않는다(`find_differential_pair_candidates()`가 이미
        # 이 이유로 명시적으로 배제하고 있음, 위 그 함수 docstring 참고 -- 이 함수는 그 배제를
        # 빠뜨리고 있었다). 서로 무관한 두 소자가 우연히 같은 레일을 source로 공유하기만 해도
        # (극단적으로는 회로에 정확히 2개만 있으면) diff_pair로 오탐된다.
        if source in _RAIL_NETS:
            continue
        if len(group) != 2:
            continue
        if group[0].gate is not None and group[1].gate is not None and group[0].gate != group[1].gate:
            diff_pair[(kind, source)] = group

    return {"current_mirror": current_mirror, "diff_pair": diff_pair}


# ---------------------------------------------------------------------------
# 1.7a) analog-grammar skill 연동 -- Tier 1(topology 저작 단계, stack_id 불필요)
#       matching 후보 오탐 필터. 상세 설계: references/analog-grammar-integration.md
#       (2026-08-06, analog-topology-json-library 세션18 K/L절에서 시작된 논의).
#       analog-grammar가 sys.path에 없으면(다른 skill이라 설치 여부가 실행 환경에
#       좌우됨) 아래 어댑터(find_idiom_matches/find_stack_edges)는 조용히 None을
#       반환한다 -- 호출자는 None이면 이 보강 기능 없이 기존 동작(idiom_matches=
#       None/stack_edges=None)으로 폴백해야 한다.
#       ImportError만 잡고 다른 예외는 그대로 던진다(조용히 다른 실패까지 삼키지 않음).
# ---------------------------------------------------------------------------

def _to_analog_grammar_devs(transistors: list) -> list:
    """gate가 없는 소자는 제외한다 -- analog-grammar의 net 분류는 모든 소자가 G/D/S
    셋 다 갖고 있다고 가정한다. 이 프로젝트의 Transistor.gate는 원래 선택 필드(§1.7
    matching 탐지 전용)라 None인 소자가 흔한데, 그런 소자는 애초에 이 연동이
    강화하려는 current_mirror/diff_pair/stacked 판정 대상도 아니므로 제외해도
    손실이 없다."""
    return [{"name": t.name, "type": t.kind.upper(), "D": t.drain, "G": t.gate, "S": t.source}
            for t in transistors if t.gate is not None]


def _import_analog_grammar(*module_names):
    """`skills/analog-grammar/assets`를 sys.path에 넣고(멱등) 주어진 모듈들을 임포트해
    튜플로 반환한다. analog-grammar가 없으면(ImportError) 전부 None인 튜플을 반환한다
    -- 호출자가 언패킹 후 첫 값만 None-체크해도 되도록."""
    import sys
    _ag_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                "analog-grammar", "assets"))
    if _ag_path not in sys.path:
        sys.path.insert(0, _ag_path)
    try:
        import importlib
        return tuple(importlib.import_module(name) for name in module_names)
    except ImportError:
        return tuple(None for _ in module_names)


def find_idiom_matches(transistors: list, inputs=(), outputs=(), feedbacks=(),
                         biases=(), clocks=()) -> list | None:
    """analog-grammar skill(Stage 1 net 분류 + Stage 2 role 배정 + Stage 3 idiom
    매칭)을 한 번에 실행해 **겹침 해소 이전**의 원본 Match 리스트를 반환한다.
    resolve_overlaps()(Stage 4 계층 축약/보고용 요약)는 여기서 거치지 않는다 --
    예를 들어 current-reuse-pair(priority 9)가 그 아래 differential-pair 2개를
    흡수해도, 실제 W/L 매칭이 필요한 단위는 여전히 원래의 두 쌍이지 4소자 뭉치가
    아니다. `inputs`/`outputs`/`feedbacks`/`biases`/`clocks`는 analog-grammar의
    Stage 1 net 분류에 그대로 전달된다 -- topology.json의 `ports` 필드를 그대로
    승격해서 넘기면 이름 힌트 추정을 줄일 수 있다(references/analog-grammar-
    integration.md §5)."""
    netclass, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = netclass.classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)
    role = netclass.assign_roles(devs, cls, imp)
    return idioms_mod.match_all(devs, cls, imp, role)


def find_stack_edges(transistors: list) -> list | None:
    """analog-grammar의 `netclass.stack_edges(devs)`를 그대로 재사용한다(role/net
    분류 불필요, 순수 connectivity) -- "X.source==Y.drain이면 Y 위에 X가 얹혀
    있다"는 관계를 [(lower_name, upper_name, node), ...]로 반환한다.
    `find_stacked_matching_candidates()`(§1.7c)에 그대로 넘긴다."""
    (netclass,) = _import_analog_grammar("netclass")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    return netclass.stack_edges(devs)


# ---------------------------------------------------------------------------
# 1.7c) 복합소자(composite) 기반 매칭 후보 상속 -- 이미 확정/발견된 매칭쌍 위에 직접
#       stacked된 소자쌍을 재귀적으로 찾는다. 세션16/17의 branch composite
#       (_branch_composite_pair(), kcl_series_union() 기반, **레이아웃** crossover
#       짝짓기용)와 정확히 같은 직렬 스택 개념을, 이번엔 반대 방향(matching 후보
#       **발견**)으로 적용한 것 -- 2026-08-06, 사용자 제안. current_reuse_
#       telescopic_ota 실측: {M1a,M1b}(확정 diff_pair) 위에 {M2a,M2b}, {M4a,M4b}
#       위에 {M3a,M3b}가 정확히 이 메커니즘으로 재현됨(stick-diagram-euler-
#       layout.md §2.6이 기록해둔 "캐스코드 대칭쌍" 두 사례 전부).
# ---------------------------------------------------------------------------

def find_stacked_matching_candidates(transistors: list, base_pairs: list,
                                       stack_edges: list) -> dict:
    """이미 확정/발견된 매칭쌍(`base_pairs`: `[(name_a, name_b), ...]` -- diff_pair/
    current_mirror Match든, topology.json의 `symmetry.matching_pairs`든 호출자가
    아무거나 seed로 넘길 수 있다) 위에 직접 stacked된 소자쌍을 재귀적으로(2단 이상
    캐스코드 대비) 찾아 매칭 후보로 낸다. `stack_edges`: `find_stack_edges()`의
    반환값을 그대로 넘긴다.

    각 base pair (a, b)에 대해 a/b 위에 직접 얹힌 소자(ua/ub)를 찾고, 둘 다 있고
    같은 kind이면 (ua, ub)를 새 후보로 낸다 -- 그 (ua, ub)를 다시 base pair 삼아
    계속 위로 타고 올라간다.

    ⚠️ 한 소자의 drain(=net)을 여러 소자가 동시에 source로 쓸 수 있다(예: folded
    cascode의 folding node — PMOS/NMOS가 같은 net에서 동시에 위로 뻗음). 그래서
    "바로 위에 얹힌 소자"는 유일하지 않을 수 있다 -- **base 소자와 같은 kind인
    후보로만 좁힌다**(캐스코드 스택은 같은 극성끼리 쌓이는 게 정상 구조이므로).
    같은 kind 후보가 정확히 하나가 아니면(0개 또는 2개 이상) 모호하다고 보고 그
    갈래는 포기한다 -- 억지로 하나를 고르지 않는다(folded_cascode_example()의
    M1(pmos) 위에 M5(pmos)/M7(nmos)이 동시에 얹힌 실제 사례로 발견, 2026-08-06).

    반환: `{(kind, lower_a, lower_b): [Transistor, Transistor], ...}` -- 키의
    마지막 두 요소는 이 후보를 낳은 바로 아래 단(base) 소자 이름(추적/디버깅용).
    M57/M58처럼 확정된 쌍 위에 얹혀 있지 않은 소자는 이 경로로 전혀 끌려오지
    않는다(base_pairs에서 출발한 것만 전파되므로)."""
    by_lower = defaultdict(list)
    for lo, up, _node in stack_edges:
        by_lower[lo].append(up)
    kind_of = {t.name: t.kind for t in transistors}
    by_name = {t.name: t for t in transistors}

    def _upper_same_kind(name):
        cands = [u for u in by_lower.get(name, ()) if kind_of.get(u) == kind_of.get(name)]
        return cands[0] if len(cands) == 1 else None

    out, frontier, seen = {}, list(base_pairs), set()
    while frontier:
        a, b = frontier.pop()
        if (a, b) in seen:
            continue
        seen.add((a, b))
        ua, ub = _upper_same_kind(a), _upper_same_kind(b)
        if ua is None or ub is None or kind_of.get(ua) != kind_of.get(ub):
            continue
        out[(kind_of[ua], a, b)] = [by_name[ua], by_name[ub]]
        frontier.append((ua, ub))
    return out


# ---------------------------------------------------------------------------
# 1.7d) VDD->GND 물리 branch 추적 -- `vertical_stack_id`를 connectivity만으로 자동
#       도출할 수 있는지 세션23이 4가지 방식을 직접 실측한 결과물(.ai/context.md 세션23
#       참고). 아래 3가지는 전부 실패로 확정됨(재시도 불필요, 이유가 구조적이라 이 함수
#       자체가 그 실패를 물려받지 않도록 설계됨):
#       1) 엄격한 2단자 KCL(`kcl_series_union`, 레일 제외) -- 분기 노드에서 무조건
#          멈춰서 너무 잘게 쪼갠다(matching_pairs로 확정되는 후보 0/16).
#       2) 레일 제외 rail-to-rail 연결성분(단자 수 무관 union) -- 분기를 넘어가도록
#          허용하니 반대로 너무 뭉친다(51개 중 25개가 서로 다른 11개 declared
#          vertical_stack_id를 한 덩어리로 섞음).
#       3) 소자 단위 분기별 경로 나열(공유 net의 "다른 단자를 쓰는 이웃"을 전부 다음
#          hop 후보로 취급) -- 병렬 형제(같은 kind가 같은 종류 단자를 공유하는 관계,
#          예: M1a.source==M1b.source==Vx)까지 "다음 소자"로 오인해 조합 폭발
#          (16개 시작점 -> 446개 경로, 그나마도 분할이 아니라 소자가 여러 경로에
#          중복 등장).
#       아래 함수는 4번째 시도로, PMOS/NMOS 각각 실제 전류 방향에 맞는 "entry/exit
#       단자"를 kind로 고정해서 병렬 형제(같은 kind, 같은 타입 단자 공유)는 구조적으로
#       절대 다음 hop이 될 수 없게 막고, 대신 PMOS 출력과 NMOS 입력이 만나는
#       drain=drain 지점(예: `M2a.drain==M3a.drain==Vom1`, 텔레스코픽/폴디드 캐스코드의
#       실제 출력 노드)은 정상적으로 이어지도록 한다 -- 사용자가 직접 손으로 검증한
#       5개 실제 branch(`current_reuse_telescopic_ota`)와 전부 정확히 일치했고,
#       조합 폭발 없이 29개 완주 branch + 1개 dead-end로 수렴했다(세션23 실측).
#       ⚠️ 그럼에도 `vertical_stack_id`를 자동 확정하지는 못한다(세션23 결론) --
#       사람이 선언한 각 vertical_stack_id 그룹은 이 함수가 찾는 "하나의 물리
#       branch"와 정확히 대응하지 않고, (a) 여러 branch가 공유하는 허브 소자
#       집합(예: `stage1`={M6,M7,M5}, tail 공급/싱크 역할)이거나 (b) 하나의 branch를
#       matching_sensitivity 경계로 상/하 반씩 쪼갠 것(예: `biasgen_vom_a`/`_b`)이라서다.
#       이 함수는 그 자체로 유용한 진단/후보 도구(예: `resolve_stack_layout()`의
#       재료, box-shape 감사)로 쓰되, `vertical_stack_id` 자동판정의 최종 답은 아니다.
# ---------------------------------------------------------------------------

def trace_vdd_to_gnd_branches(transistors: list) -> dict:
    """PMOS는 source(레일쪽)->drain(부하쪽), NMOS는 drain(부하쪽)->source(레일쪽) 순으로
    "전류가 실제로 흐르는 방향"을 kind로 고정해 소자를 잇는다 -- 이렇게 하면 같은 net을
    공유하더라도 **같은 kind가 같은 타입 단자(둘 다 source 또는 둘 다 drain)를 공유하는
    관계**(예: `M1a.source==M1b.source`, 병렬 형제)는 구조적으로 절대 다음 hop이 될 수
    없고, **PMOS의 drain과 NMOS의 drain이 만나는 지점**(예: `M2a.drain==M3a.drain`,
    캐스코드 출력 노드)만 정상적으로 다음 hop이 된다.

    소자 t의 "entry_net"(전류가 들어오는 쪽) = `t.source`(pmos) 또는 `t.drain`(nmos).
    "exit_net"(전류가 나가는 쪽) = `t.drain`(pmos) 또는 `t.source`(nmos). `entry_net(t)
    == "vdd"`인 소자에서 시작해, 각 소자의 exit_net을 다음 소자의 entry_net과 매칭하며
    재귀적으로 이어간다(레일이면 종료, 매칭되는 다음 소자가 여럿이면 진짜 전류 분기이므로
    각각 별도 branch로 갈라짐 -- 병렬 형제는 애초에 이 매칭 관계에 들어오지 않으므로
    분기 수가 실제 회로의 fan-out 수를 넘지 않는다).

    반환: `{"branches": [{"chain": [소자명,...], "terminates_at": "gnd"|"non_transistor"},
    ...]}`. `terminates_at="non_transistor"`는 버그가 아니라 "이 branch의 전류가 다음
    트랜지스터가 아니라 회로 밖 요소(예: `ideal_sources`의 전류원)로 빠진다"는 정직한
    신호다(예: `M18_bg`는 diode-connected로 `Vbias1`을 정하고, 그 전류는 `Iref`
    이상적 전류원을 통해 `gnd`로 빠진다 -- 어떤 트랜지스터도 `Vbias1`을 entry_net으로
    쓰지 않으므로 여기서 정상적으로 멈춘다)."""
    by_name = {t.name: t for t in transistors}

    def entry_net(t):
        return t.source if t.kind == "pmos" else t.drain

    def exit_net(t):
        return t.drain if t.kind == "pmos" else t.source

    by_entry = defaultdict(list)
    for t in transistors:
        by_entry[entry_net(t)].append(t.name)

    def _trace(name, visited):
        en = exit_net(by_name[name])
        if en in _RAIL_NETS:
            return [([name], en)]
        nxts = [n for n in by_entry.get(en, []) if n not in visited]
        if not nxts:
            return [([name], None)]
        out = []
        for n in nxts:
            for sub_chain, term in _trace(n, visited | {n}):
                out.append(([name] + sub_chain, term))
        return out

    start_names = [t.name for t in transistors if entry_net(t) == "vdd"]
    branches = [{"chain": chain, "terminates_at": "gnd" if term == "gnd" else "non_transistor"}
                for name in start_names for chain, term in _trace(name, {name})]
    return {"branches": branches}


def trace_gnd_to_vdd_branches(transistors: list) -> dict:
    """`trace_vdd_to_gnd_branches()`의 반대 방향 -- GND에서 시작해 VDD 쪽으로 거슬러
    올라간다. entry/exit 단자를 반대로 고정한다: PMOS는 `drain(부하쪽)->source(레일쪽)`,
    NMOS는 `source(레일쪽)->drain(부하쪽)` 순(하향 버전과 정확히 반대 -- "전류가 실제로
    흐르는 방향"을 반대로 거슬러 올라가는 것뿐, 원리는 동일).

    ⚠️ **왜 필요한가(세션23 실측 근거)**: telescopic/current-reuse처럼 differential pair가
    스택 안에 여러 층(예: PMOS 입력단 + NMOS 입력단 재사용)으로 있으면, 하향 추적만으로
    첫 fork만 보는 방식(하향 전용, 세션23 C-7/C-8 초기 버전)은 스택 **상단**의
    differential pair(`M1a`/`M1b`)만 잡고, 그 아래 분기 없는 직선 구간에 파묻힌
    **두 번째** differential pair(`M4a`/`M4b`)는 완전히 놓친다 -- 반대 방향(GND에서
    위로)으로 올라가면 그 두 번째 pair가 **자기 방향에서는 첫 fork**로 바로 드러난다.
    `find_differential_and_mirror_forks()`가 이 함수와 `trace_vdd_to_gnd_branches()`를
    같이 써서 양쪽에서 찾은 fork를 합친다.

    반환 형태는 `trace_vdd_to_gnd_branches()`와 동일하되, `terminates_at`이 `"vdd"`|
    `"non_transistor"`다(레일이 반대이므로)."""
    by_name = {t.name: t for t in transistors}

    def entry_net(t):
        return t.drain if t.kind == "pmos" else t.source

    def exit_net(t):
        return t.source if t.kind == "pmos" else t.drain

    by_entry = defaultdict(list)
    for t in transistors:
        by_entry[entry_net(t)].append(t.name)

    def _trace(name, visited):
        en = exit_net(by_name[name])
        if en in _RAIL_NETS:
            return [([name], en)]
        nxts = [n for n in by_entry.get(en, []) if n not in visited]
        if not nxts:
            return [([name], None)]
        out = []
        for n in nxts:
            for sub_chain, term in _trace(n, visited | {n}):
                out.append(([name] + sub_chain, term))
        return out

    start_names = [t.name for t in transistors if entry_net(t) == "gnd"]
    branches = [{"chain": chain, "terminates_at": "vdd" if term == "vdd" else "non_transistor"}
                for name in start_names for chain, term in _trace(name, {name})]
    return {"branches": branches}


def find_differential_and_mirror_forks(transistors: list, inputs=(), outputs=(),
                                         feedbacks=(), biases=(), clocks=()) -> dict | None:
    """`trace_vdd_to_gnd_branches()`(하향) + `trace_gnd_to_vdd_branches()`(상향) 양쪽
    branch tree에서 **첫 번째로 갈라지는 지점(fork)**을 전부 찾아, 그 fork의 소자쌍을
    analog-grammar gate 판정(같은 gate=mirror, 다른 gate+둘 다 `INPUT`=differential)으로
    분류한다. `find_verified_differential_and_mirror_relations()`와 같은 gate 판정
    규칙을 쓰지만, 그 함수는 (구조가 같은 branch끼리 묶은 뒤) **매칭된 쌍 안의 모든
    위치**를 보는 반면, 이 함수는 branch tree 전체의 **모든** fork를 훑는다는 게 다르다.

    ⚠️ **한 방향만으로는 안 되는 이유(세션23 실측)**: `current_reuse_telescopic_ota`
    에서 하향만 쓰면 `M1a`/`M1b`(PMOS 입력단) fork만 찾고, 상향만 쓰면 `M4a`/`M4b`
    (NMOS 입력단 재사용) fork만 찾는다 -- 각 방향은 자기 시작점에서 가장 먼저 만나는
    fork 하나만 보므로, 스택 안에 여러 층으로 있는 differential/mirror 관계 중
    "그 방향에서 첫 번째로 마주치는 것"만 잡는다. 두 방향을 합쳐야 이 회로의 진짜
    differential pair 2종류를 전부 찾는다(사용자 지적: "telescopic differential pair를
    인식 못하는 문제").

    analog-grammar가 없으면 `None`을 반환한다.

    반환(있으면): `{"forks": [{"direction": "vdd_to_gnd"|"gnd_to_vdd", "fork_prefix":
    [...], "fork_devices": (a, b), "relation": "mirror"|"differential"}, ...]}` --
    gate로 관계를 못 찾은 fork(둘 다 무관한 소자, 다른 kind 등)는 조용히 건너뛴다(이
    함수는 "관계가 있는 것"만 보고하는 목적이라, `find_verified_differential_and_mirror_
    relations()`의 `structurally_symmetric_no_connection`처럼 무관계도 보고하지 않는다 -- branch tree
    전체를 훑으면 무관한 fork가 훨씬 많아서, 전부 보고하면 신호보다 잡음이 커진다)."""
    netclass, _idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, _imp, _assume = netclass.classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)

    by_name = {t.name: t for t in transistors}

    def gate_of(name):
        return by_name[name].gate

    def gate_class(name):
        return cls.get(gate_of(name))

    def _forks_of(branches):
        forks = defaultdict(set)
        for chain in branches:
            for i in range(len(chain)):
                forks[tuple(chain[:i])].add(chain[i])
        return {prefix: members for prefix, members in forks.items() if len(members) >= 2}

    def _classify_forks(branches, direction):
        out = []
        for prefix, members in _forks_of(branches).items():
            members = sorted(members)
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    a, b = members[i], members[j]
                    if by_name[a].kind != by_name[b].kind:
                        continue
                    if gate_of(a) == gate_of(b):
                        relation = "mirror"
                    elif gate_class(a) == "INPUT" and gate_class(b) == "INPUT":
                        relation = "differential"
                    else:
                        continue
                    out.append({"direction": direction, "fork_prefix": list(prefix),
                                "fork_devices": (a, b), "relation": relation})
        return out

    down = trace_vdd_to_gnd_branches(transistors)
    down_chains = [b["chain"] for b in down["branches"] if b["terminates_at"] == "gnd"]
    up = trace_gnd_to_vdd_branches(transistors)
    up_chains = [b["chain"] for b in up["branches"] if b["terminates_at"] == "vdd"]

    return {"forks": _classify_forks(down_chains, "vdd_to_gnd")
                     + _classify_forks(up_chains, "gnd_to_vdd")}


def suggest_vertical_stack_composites(transistors: list, inputs=(), outputs=(),
                                        feedbacks=(), biases=(), clocks=(),
                                        direction: str = "vdd_to_gnd") -> list | None:
    """`trace_vdd_to_gnd_branches()`(물리 branch 골격) + analog-grammar idiom matching
    (diode-connected/floating-battery/cascode-stack/push-pull, branch **내부에서 연속된
    부분열만** 병합)을 합쳐 `vertical_stack_id` 후보를 제안한다 -- 세션23 실측(5번째
    시도)에서 `current_reuse_telescopic_ota`(51소자)에 돌려 63개 composite unit 중 62개가
    사람이 선언한 `vertical_stack_id`와 정확히 일치, 나머지 1개(`M37a`+`M38`)도 진짜 충돌이
    아니라 `M37a`의 declared 값이 애초에 비어있던 gap을 메우는 방향의 제안이었다(`.ai/
    context.md` 세션23 C절 4가지 실패 + 이 5번째 성공 전체 기록 참고). 앞선 4가지 시도
    (엄격한 2단자 KCL / 분기 허용 rail-to-rail 연결성분 / 소자 단위 분기별 경로 나열 /
    kind 기반 방향 고정 branch tracing 단독)는 전부 `vertical_stack_id`를 재현하지
    못했다 -- branch 골격만으로는 "허브 소자"와 "branch 내부 상/하 분할"을 구별 못 했는데,
    analog-grammar의 idiom 판정(diode-connected 등 role은 connectivity에서 결정론적으로
    도출됨)을 branch 위에 겹치면 바로 그 상/하 분할 경계가 자연스럽게 드러났다.

    `current-mirror`/`differential-pair` idiom은 의도적으로 제외한다 -- 이 둘은 정의상
    **서로 다른 branch**를 잇는 관계(대칭 쌍, §1.7d 주석 C절 참고)라 하나의 branch 안에서
    연속된 부분열로 나타나지 않는다(포함시켜도 매칭될 일이 없어 무해하지만, 명시적으로
    빼서 의도를 분명히 한다).

    analog-grammar가 없으면(다른 skill이라 설치 여부가 환경에 좌우됨) `None`을 반환한다
    (호출자는 이 보강 기능 없이 `trace_vdd_to_gnd_branches()`만 쓰는 폴백 필요).

    `direction`: `"vdd_to_gnd"`(기본, 하향 -- `trace_vdd_to_gnd_branches()`) 또는
    `"gnd_to_vdd"`(상향 -- `trace_gnd_to_vdd_branches()`). telescopic/current-reuse처럼
    differential pair가 스택 안에 여러 층으로 있으면 한 방향만으로는 그중 일부만 branch
    골격에 잡힐 수 있다(§1.7d 주석 C-9 참고) -- `find_verified_differential_and_mirror_
    relations()`가 두 방향 다 호출해서 합친다.

    반환(있으면): 해당 방향의 `trace_*_branches()`와 같은 `branches` 리스트에
    `"composites"` 키를 추가한 것 -- `[{"chain", "terminates_at", "composites":
    [{"members": [...], "idiom": str|None, "ports": dict}, ...]}, ...]`. `idiom=None`인
    composite는 어떤 idiom도 못 찾은 단일 소자(합쳐지지 않음, `ports={}`)다. `ports`는
    2026-08-08 추가(사용자 지적) -- 원래 `idioms.py`의 `Match.ports`(예: `cascode-stack`
    의 `lower_role`= 아래쪽 소자의 role, `mid`/`out`= 중간/출력 net)를 이 함수가 조용히
    버리고 있었다 -- `M8`(`CURRENT_SOURCE`)과 `M9a`(`CASCODE`)가 물리적으로는 정확히
    같은 PMOS diffusion column에 쌓을 수 있는 직렬 스택인데(이 사실 자체, 즉 layout
    관점의 병합은 여전히 유효), composite로 뭉치고 나면 어느 쪽이 아래쪽 전류원이고
    어느 쪽이 그 위 소자인지 구별할 정보가 사라지는 문제였다. 이제 `ports`에 그 정보가
    그대로 남아있어(예: `M8`+`M9a`의 `ports={'mid':'Vg15','out':'Vop1','lower_role':
    'CURRENT_SOURCE'}`), `headroom_role` 같은 후속 분류가 이 정보를 활용할 수 있다.
    ⚠️ **정정(2026-08-08, 사용자 재지적)**: 이 예시를 "교과서적인 캐스코드된 전류미러
    구조"라고 적었던 것은 틀렸다 -- `M9a`의 실제 기능은 `M8`의 출력 임피던스를 부스트
    하는 캐스코드가 아니라, `M9a`(PMOS)/`M9b`(NMOS)가 이루는 Monticelli class-AB
    floating current source의 절반이다(`M9a`/`M9b`가 비-레일 노드 `Vg15`<->`Vop1` 사이를
    상보 anti-parallel로 마주보고 잇고, 이 두 노드는 각각 2단 출력쌍 `M15`/`M16`의
    게이트다 -- `analog-grammar/assets/idioms.py`의 `floating-current-source` idiom,
    2026-08-08 신설 참고). `M8`+`M9a`가 같은 diffusion column에 물리적으로 쌓일 수
    있다는 layout 사실과, `M9a`가 캐스코드로 "기능"한다는 것은 별개 질문이고 후자는
    틀렸다 -- `M8`은 이 floating loop 위쪽에 바이어스 전류를 대주는 독립 전류원일
    뿐이다(`M10`이 아래쪽에서 같은 역할).

    ⚠️ **이 함수는 제안만 한다 -- `vertical_stack_id`를 자동으로 `topology.json`에 쓰지
    않는다.** 62/63이라는 실측 성공률은 이 회로 하나의 결과이지 일반 보장이 아니고,
    `M37a`/`M38` 사례처럼 "진짜 충돌"과 "gap 보완 제안"을 구별하는 것도 여전히 사람/AI
    판단 몫이다(프로젝트 원칙: connectivity에서 결정론적으로 나온 사실도 최종 채택은
    항상 검토 대상).

    ⚠️ **2026-08-08 추가(사용자 지적) -- 순수 구조 폴백, `netclass.stack_edges()` 직접
    사용은 아님(첫 시도가 회귀를 냄, 아래 참고)**: `idioms.m_cascode()`가 같은 날
    기능적으로 더 엄격해지면서(위 정정 문단 참고, `up.source`가 출력 쪽이면 -- low-Z라
    캐스코드로 기능 못 함 -- 제외) `M8`+`M9a`처럼 물리적으로는 분명히 같은 well에
    쌓이는데 기능적으로 "캐스코드"가 아닌 쌍이 idiom 매칭에서 빠지게 됐다. 이 함수의
    목적(레이아웃 스택 후보 제안)에는 "기능적으로 뭐라고 부르는가"가 아니라 "같은
    diffusion column에 물리적으로 쌓을 수 있는가"만 필요해서, 처음엔 `netclass.
    stack_edges()`(role/기능 조건 전혀 없이 `X.source==Y.drain`이면 무조건 후보)를
    그대로 폴백으로 썼다. **이게 Test 40을 깼다** -- `stack_edges()`는 fan-out 카디널
    리티를 전혀 안 봐서, `M1a`(차동쌍 다리, source=`Vx`)와 `M6`(그 tail 전류원,
    drain=`Vx`)도 그냥 "source==drain"이 성립한다는 이유만으로 물리적 스택 후보로
    잡아버렸다 -- `Vx`는 `M6`/`M7` 둘 다 drain으로 물고 `M1a`/`M1b` 둘 다 source로
    무는 **fan-out 노드**라 1:1 직렬 스택이 전혀 아닌데도(`m_cascode()`가 이미
    `diffpair_legs` 제외로 이 함정을 정확히 피하고 있었다는 걸 이 폴백이 무시한 것).
    그 결과 branch 훑기 알고리즘이 `M1a`를 `M6`과 먼저 묶어버려 `M1a`+`M2a`가 갈라짐.
    **고침**: `stack_edges()`를 직접 안 쓰고, `m_cascode()`와 정확히 같은 1차 게이트
    (role이 `CASCODE`/`AMPLIFYING`/`CONTROLLED_CURRENT_SOURCE`) + `diffpair_legs` 제외를
    여기서도 그대로 적용한 뒤(`m_cascode()`가 2026-08-08에 새로 추가한 `float_legs`
    제외와 출력-도달성 제외만 **의도적으로 생략** -- 이 둘은 "기능적으로 캐스코드가
    아니다"라는 판단이지 "물리적으로 못 쌓는다"는 뜻이 아니므로), 그 결과를
    `kind='physical-stack'`으로 폴백에 넣는다. idiom 매칭이 같은 윈도우에 이미 있으면
    (정렬이 안정적이라 원래 순서 유지) 그쪽이 항상 우선한다."""
    netclass, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = netclass.classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)
    role = netclass.assign_roles(devs, cls, imp)
    matches = idioms_mod.match_all(devs, cls, imp, role)

    diffpair_legs = {n for m in idioms_mod.m_diffpair(devs, cls, imp, role) for n in m.devices}
    by_drain = defaultdict(list)
    for d in devs: by_drain[d['D']].append(d)
    stack_fallback = []
    for up_d in devs:
        if role.get(up_d['name']) not in (idioms_mod.CASCODE, netclass.FLOAT_SRC,
                                            netclass.DIODE_CASC,
                                            idioms_mod.AMP, idioms_mod.CTRL_SRC):
            continue
        if up_d['name'] in diffpair_legs:
            continue
        for lo_d in by_drain[up_d['S']]:
            if lo_d['name'] == up_d['name'] or lo_d['type'] != up_d['type']:
                continue
            stack_fallback.append((frozenset((lo_d['name'], up_d['name'])), 'physical-stack',
                                   {'mid': up_d['S'], 'lower_role': role.get(lo_d['name'])}))
    candidates = sorted(
        [(frozenset(m.devices), m.kind, m.ports) for m in matches
         if m.kind not in ("current-mirror", "differential-pair")] + stack_fallback,
        key=lambda c: -len(c[0]))

    def _composite(chain):
        out, i, n = [], 0, len(chain)
        while i < n:
            matched = None
            for size in range(n - i, 0, -1):
                window = frozenset(chain[i:i + size])
                for cset, kind, ports in candidates:
                    if cset == window:
                        matched = (kind, chain[i:i + size], ports)
                        break
                if matched:
                    break
            if matched:
                out.append({"members": matched[1], "idiom": matched[0], "ports": matched[2]})
                i += len(matched[1])
            else:
                out.append({"members": [chain[i]], "idiom": None, "ports": {}})
                i += 1
        return out

    if direction == "gnd_to_vdd":
        branch_result = trace_gnd_to_vdd_branches(transistors)
    else:
        branch_result = trace_vdd_to_gnd_branches(transistors)
    return [{"chain": b["chain"], "terminates_at": b["terminates_at"],
              "composites": _composite(b["chain"])}
             for b in branch_result["branches"]]


def suggest_headroom_stack_groups(transistors: list, composites: list | None = None,
                                    inputs=(), outputs=(), feedbacks=(), biases=(),
                                    clocks=()) -> dict | None:
    """2026-08-10(세션27) -- `suggest_vertical_stack_composites()`의 `composites`(idiom
    경계)를 그대로 `device_roles.*.vertical_stack_id`로 옮기면 헤드룸(`allocate_stack_
    headroom()`) 배정이 깨질 수 있다는 걸 실측으로 발견하고 만든 후속 함수. 두 질문은
    다르다 -- **composite**는 "이 소자들이 어떤 회로 idiom인가"(floating-battery,
    active-load 등, 문서화/`headroom_role` 힌트용으로 여전히 유효)에 답하고, 이 함수가
    답하는 **헤드룸 그룹**은 "VDS 합이 vdd(또는 그 일부)가 돼야 하는 하나의 전기적
    컬럼이 뭔가"에 답한다. 실제 사례(`current_reuse_telescopic_ota`): `M11a`/`M11b`
    (floating-battery composite)와 `M12`(active-load composite)는 같은 `chain`
    (`VDD-M11a-M11b-M12-GND`, 진짜 물리적 직렬)인데 서로 다른 composite라 서로 다른
    `vertical_stack_id`로 선언돼 있었다 -- `M11a`/`M11b`만으로 `allocate_stack_headroom()`
    을 호출하면 cascode role만 있고 나머지를 배분할 'other' role이 없어 assert가 실패했다.

    **알고리즘**: 같은 `chain` 안에서 연속된 composite를 하나의 헤드룸 그룹으로 이어
    붙이되, **여러 `chain`에 공통으로 나타나는 "허브" 소자**(`M5`/`M6`/`M7`/`M1a`류 --
    한 tail/입력 소자가 여러 differential branch에서 재사용돼 여러 chain에 등장)를
    만나면 거기서 멈춘다 -- 허브는 이미 자기 자신의 독립된 그룹이어야 한다(여러 branch가
    같은 허브를 공유하므로 한 branch의 이웃과 합치면 안 됨). 허브에 바로 인접한(같은
    chain 안, 병합되지 않은) 비-허브 그룹은 그 허브를 `budget_reference_device`로
    받는다 -- `trace_vdd_to_gnd_branches()`의 `chain`은 항상 entry_net=vdd에서
    시작하므로(docstring 참고), 그룹이 이미 `chain[0]`을 포함해 vdd에 직접 닿아있거나
    `terminates_at="gnd"`이고 chain 끝까지 포함해 gnd에 직접 닿아있으면 그쪽엔 참조가
    필요 없다 -- 그렇지 않은 한쪽에만 인접 허브를 참조로 단다(양쪽 다 허브에 막힌
    "폴디드" 그룹은 현재 `budget_reference_device`가 참조 1개만 지원하므로 미지원 --
    `unsupported_both_sides_hub`로 표시만 하고 참조는 비워둔다, 조용히 잘못 추측하지
    않는다).

    같은 허브(예: `M5`)가 여러 chain에 반복 등장해도 멤버 집합(frozenset)으로 정규화해
    항상 같은 그룹으로 dedup한다. 헤드룸 목적이 아닌 순수 단일-소자 하이웨이(허브가 아닌
    singleton composite, `idiom=None`인 미분류 소자 포함)도 인접 규칙 그대로 적용된다.

    ⚠️ `suggest_vertical_stack_composites()`와 동일 원칙 -- **제안만 한다, topology.json에
    자동으로 쓰지 않는다.** analog-grammar가 없어 `composites`(인자로 안 주면 내부에서
    `suggest_vertical_stack_composites()`를 호출)가 `None`이면 이 함수도 `None`을 반환한다.

    반환(있으면): `{"device_to_group": {device: group_id}, "group_ref_device":
    {group_id: device|None}, "unsupported_both_sides_hub": [group_id, ...]}` --
    `group_id`는 그룹 멤버 이름을 정렬해 이어붙인 문자열(사람이 읽을 수 있게, 실제
    이름은 채택 시 자유롭게 바꿔도 됨)."""
    if composites is None:
        composites = suggest_vertical_stack_composites(
            transistors, inputs, outputs, feedbacks, biases, clocks)
        if composites is None:
            return None

    chain_membership = defaultdict(int)
    for branch in composites:
        for name in set(branch["chain"]):
            chain_membership[name] += 1
    hub_names = {name for name, count in chain_membership.items() if count > 1}

    def _is_hub_composite(comp):
        return any(m in hub_names for m in comp["members"])

    def _explode_mixed(comps):
        # 2026-08-10 -- composite 하나가 허브+비허브를 섞어 담을 수 있다(실제 사례:
        # `{M6,M58}` "physical-stack" -- M6은 다른 여러 chain에도 나타나는 허브지만
        # M58은 이 chain에만 있는 전용 소자다). 섞인 composite를 통째로 "허브 composite"
        # 취급하면 M58까지 M6의 허브 그룹에 끌려 들어가 M6의 다른 chain에서의 정체성과
        # 어긋난다 -- 허브 멤버는 1개씩 자기 자신의 원자 composite로, 나머지 비허브
        # 멤버는 원래 순서를 유지한 채 별도 run으로 쪼갠다(이후 일반 병합 로직이
        # 정상적으로 처리하도록).
        out = []
        for comp in comps:
            members = comp["members"]
            if len(members) == 1 or not any(m in hub_names for m in members):
                out.append(comp)
                continue
            buf = []
            for m in members:
                if m in hub_names:
                    if buf:
                        out.append({"members": buf, "idiom": None, "ports": {}})
                        buf = []
                    out.append({"members": [m], "idiom": None, "ports": {}})
                else:
                    buf.append(m)
            if buf:
                out.append({"members": buf, "idiom": None, "ports": {}})
        return out

    device_to_key = {}
    key_ref = {}
    key_touches_vdd = defaultdict(bool)
    key_touches_gnd = defaultdict(bool)
    unsupported = set()

    for branch in composites:
        comps = _explode_mixed(branch["composites"])
        n = len(comps)
        i = 0
        while i < n:
            comp = comps[i]
            if _is_hub_composite(comp):
                key = frozenset(comp["members"])
                for m in comp["members"]:
                    device_to_key.setdefault(m, key)
                key_ref.setdefault(key, None)
                i += 1
                continue
            run_members = list(comp["members"])
            j = i + 1
            while j < n and not _is_hub_composite(comps[j]):
                run_members.extend(comps[j]["members"])
                j += 1
            key = frozenset(run_members)
            for m in run_members:
                device_to_key.setdefault(m, key)
            touches_vdd = (i == 0)
            touches_gnd = (j == n and branch.get("terminates_at") == "gnd")
            if touches_vdd:
                key_touches_vdd[key] = True
            if touches_gnd:
                key_touches_gnd[key] = True
            ref = None
            if not touches_vdd and i > 0 and _is_hub_composite(comps[i - 1]):
                ref = comps[i - 1]["members"][0]
            if not touches_gnd and j < n and _is_hub_composite(comps[j]):
                ref2 = comps[j]["members"][0]
                if ref is not None and ref2 != ref:
                    unsupported.add(key)
                    ref = None
                elif ref is None:
                    ref = ref2
            existing = key_ref.get(key, "_unset")
            if existing == "_unset":
                key_ref[key] = ref
            elif existing != ref and ref is not None:
                unsupported.add(key)
            i = j

    def _group_name(key):
        return "_".join(sorted(key))

    device_to_group = {m: _group_name(k) for m, k in device_to_key.items()}
    group_ref_device = {_group_name(k): (None if k in unsupported else v)
                         for k, v in key_ref.items()}
    unsupported_names = [_group_name(k) for k in unsupported]
    return {"device_to_group": device_to_group, "group_ref_device": group_ref_device,
            "unsupported_both_sides_hub": unsupported_names}


def find_differential_pair_candidates(transistors: list, inputs=(), outputs=(),
                                        feedbacks=(), biases=(), clocks=()) -> dict | None:
    """구조적으로 매칭된 branch 쌍(`suggest_vertical_stack_composites()`의 composite
    시퀀스가 완전히 같은 branch끼리 묶음, C-10과 동일 원리) 안에서, 서로 다른 위치의
    소자쌍이 (1) 같은 kind, (2) 다른 gate(=mirror 아님), (3) **같은 non-rail source(진짜
    tail net)를 공유**하면 differential pair 후보로 판정한다.

    ⚠️ **왜 이게 중요한가(사용자 통찰, 2026-08-07)**: "differential pair를 먼저 찾고
    나서 mirror 관계를 분석해야 정확해진다" -- `Voc`를 `inputs=`로 미리 선언해야만
    `M37a`/`M37b`를 찾을 수 있었던 `find_verified_differential_and_mirror_relations()`
    와 정반대로, 이 함수는 **INPUT/BIAS net 분류를 전혀 안 쓴다**(net 분류 자체가
    `Voc`처럼 이름 힌트도 없고 선언도 안 된 net엔 원천적으로 못 미친다는 게 이미
    확인된 상태 -- `netclass.py` 자신도 "구조로 INPUT/BIAS 구별 불가"라고 명시). 대신
    "같은 non-rail source를 공유한다"는 **순수 connectivity 사실**만으로 진짜
    differential pair(`M1a`/`M1b`, `M4a`/`M4b`, `M37a`/`M37b`)를 전부, 그리고 정확히
    그것들만 찾는다 -- 실측: vop/vom 구조적 대응쌍(`M9a`/`M18a`, `M11a`/`M20a`,
    `M14a`/`M23a`, `M15`/`M25`, `M16`/`M26`, `M36a`/`M36b`)은 source가 서로 다른 net이라
    자동으로 걸러지고, `M6`/`M7`도 공유하는 source가 `vdd`(레일)라 걸러진다 -- 레일은
    무한 전류를 공급하는 외부 전원이라 "같은 tail을 공유해 전류가 스플릿된다"는 differential
    pair의 정의 자체가 성립하지 않는다(`kcl_series_union()`이 레일을 제외하는 것과
    같은 이유, 세션9).

    **다음 단계(반복 정제, 이 함수 자체는 여기까지만)**: 여기서 찾은 후보의 gate
    net들(예: `Voc`/`Voc_des`)을 `inputs=`로 승격해서 `find_verified_differential_and_
    mirror_relations()`를 다시 돌리면, net 분류(`BIAS`→`SIGNAL`)와 role
    (`CURRENT_SOURCE`→`AMPLIFYING` 등)까지 정확해진다는 게 검증됐다(`M7`의 role이
    정확히 이렇게 바뀜, 세션23) -- 이 승격을 자동으로 수행하는 오케스트레이션은
    아직 없음(다음 세션 후보).

    analog-grammar가 없으면(`suggest_vertical_stack_composites()`가 의존) `None`을
    반환한다. `inputs=`/`outputs=`/`feedbacks=`/`biases=`/`clocks=`는 composite 구성
    자체(idiom matching 정확도)에만 간접적으로 쓰이고, 후보 판정 자체(같은 source
    공유 여부)는 `Transistor.source`를 직접 비교하므로 net 분류와 무관하다.

    반환(있으면): `{"candidates": [{"direction": "vdd_to_gnd"|"gnd_to_vdd", "position":
    int, "devices": (a, b), "shared_source": str}, ...]}`. 같은 소자쌍이 양방향에서
    중복 검출되면 `(direction, frozenset(devices))` 기준으로 direction별 1건만 남긴다."""
    composites_down = suggest_vertical_stack_composites(
        transistors, inputs, outputs, feedbacks, biases, clocks, direction="vdd_to_gnd")
    if composites_down is None:
        return None
    composites_up = suggest_vertical_stack_composites(
        transistors, inputs, outputs, feedbacks, biases, clocks, direction="gnd_to_vdd")

    by_name = {t.name: t for t in transistors}

    def signature(b):
        return tuple((len(c["members"]), c["idiom"], tuple(by_name[m].kind for m in c["members"]))
                     for c in b["composites"])

    seen = set()
    out = []
    for direction, composite_branches, terminal in (
            ("vdd_to_gnd", composites_down, "gnd"),
            ("gnd_to_vdd", composites_up, "vdd")):
        complete = [b for b in composite_branches if b["terminates_at"] == terminal]
        groups = defaultdict(list)
        for b in complete:
            groups[signature(b)].append(b["chain"])
        for chains in groups.values():
            if len(chains) < 2:
                continue
            for i in range(len(chains)):
                for j in range(i + 1, len(chains)):
                    ca, cb = chains[i], chains[j]
                    for pos, (a, b) in enumerate(zip(ca, cb)):
                        if a == b:
                            continue
                        ta, tb = by_name[a], by_name[b]
                        if ta.kind != tb.kind or ta.gate == tb.gate:
                            continue
                        if ta.source != tb.source or ta.source in _RAIL_NETS:
                            continue
                        key = (direction, frozenset((a, b)))
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append({"direction": direction, "position": pos,
                                     "devices": (a, b), "shared_source": ta.source})

    # ⚠️ 2026-08-14 층위1 폴백 추가(사용자 지시, 근본원인 수정) -- 위 branch-composite
    # 비교는 두 branch의 idiom 라벨까지 완전히 같아야만 후보를 낸다. diode+mirror
    # 비대칭 부하(예: 5T/2단 OTA의 M3=diode-connected 레퍼런스/M4=active-load 미러 --
    # 같은 "1단 부하" 위치인데 하나는 diode-connected, 하나는 아니라서 idiom 라벨
    # 자체가 다름)가 있으면 두 branch가 영원히 다른 signature 그룹으로 갈려 이 함수가
    # 근본적으로 못 찾는다(실측: two_stage_ota에서 M1/M2가 이 이유로 후보 0건 --
    # M1쪽 composite=[diode-connected(M3),...], M2쪽 composite=[active-load(M4),...]).
    # `find_matching_candidates()`(role/idiom 분류가 전혀 필요 없는 순수 (kind,source,w)
    # 그룹핑, `Transistor.source`만 직접 비교)는 이 경우도 이미 정확히 찾는다 --
    # `propose_device_roles_gap_fill()`의 current_mirror 층위1 폴백(세션33)과 동일
    # 원칙을 이 함수 자체(모든 호출부의 공통 근본원인)에 적용한다. 순수 additive
    # (branch-composite 비교가 이미 찾은 걸 덮어쓰지 않고, 못 찾던 것만 보충)라 기존
    # 실측(Test 37 등)에 회귀가 없다."""
    for (kind, source, _w), group in _diff_pair_layer1_groups(transistors).items():
        if len(group) != 2:
            continue
        a, b = group[0].name, group[1].name
        key = ("layer1_fallback", frozenset((a, b)))
        if key in seen:
            continue
        seen.add(key)
        out.append({"direction": "layer1_fallback", "position": None,
                     "devices": (a, b), "shared_source": source})
    return {"candidates": out}


def _diff_pair_layer1_groups(transistors: list) -> dict:
    """`find_matching_candidates()`의 `diff_pair` net-only 판정(같은 kind + 같은
    non-rail source + 다른 gate, role/idiom 분류 불필요)만 떼어낸 헬퍼 -- `find_
    differential_pair_candidates()`의 층위1 폴백 전용(중복 구현 방지, `find_matching_
    candidates()`의 W-일치 필터는 topology 저작 단계엔 아직 W가 없어 항상 통과한다)."""
    by_source = defaultdict(list)
    for t in transistors:
        if t.source in _RAIL_NETS:
            continue
        by_source[(t.kind, t.source, t.w)].append(t)
    return {k: v for k, v in by_source.items()
            if len(v) == 2 and v[0].gate is not None and v[1].gate is not None
            and v[0].gate != v[1].gate}


def find_verified_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(),
                                                       feedbacks=(), biases=(), clocks=()) -> dict | None:
    """진짜 **branch 단위** 비교 -- 세션23 C-7/C-8이 확립한 원리(composite 구조가
    완전히 같은 branch끼리만 비교)를 상향까지 확장하고, 매칭된 branch
    쌍 **안의 모든 위치**를 스캔한다(첫 divergence 하나만 보던 한계 해소).

    ⚠️ **왜 필요한가**: 하향 전용+첫 divergence만 보던 초기 접근(세션23 C-7/C-8,
    `classify_symmetric_branch_pairs()` -- 세션24에 이 함수로 완전히 대체되어 삭제됨)은
    telescopic/current-reuse 구조의 **두 번째** differential pair(`M4a`/`M4b`)를
    놓쳤다(C-9). `find_differential_and_mirror_forks()`(양방향, 하지만 fork-tree의
    "갈라지는 지점"만 봄)로 이 문제는 풀었지만, 이번엔 fork가 아니라 **소자 쌍 단위**로
    비교해서 `M1a`/`M58`, `M6`/`M7`, `M18a`/`M2a` 같은 무관한 조합까지 relation 후보로
    새 게 나오는 문제가 있었다(진짜 branch 구조 일치 여부를 확인 안 했기 때문). 이 함수는
    두 접근을 합친다 -- **먼저 branch 전체의 composite 구조가 완전히 같은 것끼리만** 묶고
    (그래서 `M7`/`M36a`처럼 구조가 다른 branch는 애초에 비교조차 안 됨, C-7이 부수 효과로
    확인한 필터), **그 다음 그 매칭된 쌍 안의 모든 위치**(첫 divergence만이 아니라)를
    gate 판정한다.

    실측(`current_reuse_telescopic_ota`, 하향 한 번의 스캔만으로): `M6/M1a.../M4a/M5`
    vs `M6/M1b.../M4b/M5` 매칭 쌍 하나에서 위치1(`M1a`/`M1b`)=differential,
    위치2(`M2a`/`M2b`)=mirror, 위치3(`M3a`/`M3b`)=mirror, 위치4(`M4a`/`M4b`)=differential
    **네 관계 전부가 한 번에** 나온다 -- fork-tree 방식으로는 하향/상향 두 번 따로 돌려야
    했던 것이 branch 단위 비교에서는 한쪽 방향만으로도 이미 다 드러난다(상향도 같이 돌려서
    합치면 중복(예: 상향에서도 같은 `M1a`/`M1b`, `M4a`/`M4b`가 반대 순서로 다시 나옴) +
    하향에서 못 보는 조합(예: `M17`/`M18a`쪽 상향 전용 매칭)을 추가로 잡는다 -- 방향별
    출현 빈도 차이는 각 방향의 시작점 개수 차이일 뿐, 관계 자체가 다른 게 아니다).

    ⚠️ **알려진 한계(아직 미해결)**: 이 함수도 `find_differential_and_mirror_forks()`와
    같은 `gate_class(a)=='INPUT' and gate_class(b)=='INPUT'` 기준을 쓴다 -- `M37a`/`M37b`
    (CMFB 내부 차동쌍, 게이트가 `Voc`/`Voc_des`로 `inputs=`에 선언한 `Vip`/`Vim`이 아님)
    처럼 회로의 **2차/내부** differential pair는 여전히 못 찾는다. 이건 branch-매칭
    문제가 아니라 net 분류 문제(`netclass.py` 자체가 "구조만으로는 INPUT/BIAS 구별
    불가 -- 이름 힌트 또는 사용자 선언 필요"라고 명시)라 이 함수의 범위를 넘는다 --
    호출자가 `inputs=`에 그런 2차 differential 입력 net까지 알고 있다면 명시적으로
    추가해서 넘기면 잡힌다(검증됨, `M37a`/`M37b`가 정확히 `differential`로 옮겨감).
    2차 입력을 아직 모르는 상태에서도 이 정보를 잃지 않도록, 그런 미확정 쌍은 아래
    `structurally_symmetric_no_connection`으로 넘어가 최소한 "구조는 대칭인데 아직
    관계를 확정 못 함"이라는 신호는 남는다.

    ⚠️ **2026-08-07 수정(세션24, 사용자 지적)**: 원래 버전은 `kind`가 다르거나 gate가
    달라도 둘 다 `INPUT`이 아니면 그 위치를 그냥 `continue`로 **조용히 버렸다** --
    `classify_symmetric_branch_pairs()`(세션23 C-7/C-8, 이 함수가 완전히 대체하면서
    세션24에 삭제됨)는 이런 경우를 `structurally_symmetric_no_connection`으로 명시적으로
    보고했었는데, 정작 이 함수엔 그 세 번째 버킷이
    없어서 "구조는 확실히 대칭인데 mirror/differential로 확정은 못 하는" 쌍(예: 실회로의
    `M6`/`M7` -- 같은 tail net `Vx`에 병렬로 물린 소자지만 하나는 고정 bias, 하나는
    CMFB 출력이라 게이트가 다르고 둘 다 INPUT도 아님)이 결과에서 완전히 사라지는 문제가
    있었다. 이제 그런 위치도 `structurally_symmetric_no_connection`으로 명시적으로
    보고한다(조용히 덮어쓰지/버리지 않는다는 프로젝트 전역 원칙) -- `differential`/
    `mirror` 판정 로직 자체는 변경 없음(기존 두 버킷의 내용은 회귀 없음).

    analog-grammar가 없으면 `None`을 반환한다.

    반환(있으면): `{"differential": [...], "mirror": [...], "structurally_symmetric_
    no_connection": [...]}` -- 각 원소는 `{"direction": "vdd_to_gnd"|"gnd_to_vdd",
    "devices": (a, b), "branch_a", "branch_b", "position"}`. 같은 소자쌍이 여러 branch
    조합/양방향/버킷 후보에서 중복 검출되면 `(direction, frozenset(devices))` 기준으로
    **버킷별로** 중복 제거한다(대표 branch 쌍 하나만 남김 -- 단, 승격된 `inputs=`로
    재실행해 같은 쌍이 `no_connection`에서 `differential`/`mirror`로 옮겨가는 것 자체는
    막지 않는다, 버킷이 다르면 별개 dedup 대상).

    ⚠️ `"{category}_branch_members"`(예: `"differential_branch_members"`) 필드도 함께
    반환한다(2026-08-08 신설, 사용자 지적) -- 각 카테고리 비교에 **참여한 모든 branch의
    소자 전체**(dedup으로 버려진 branch 조합 포함, 중복 없는 정렬된 이름 리스트). 위
    소자쌍 dedup은 출력 리스트만 줄이지 이 필드에는 영향 없다 -- `Vx`처럼 두 소자
    (`M6`/`M7`)가 병렬로 같은 tail을 먹이면 `[M6,M1a,...]`/`[M7,M1a,...]`/`[M6,M1b,...]`/
    `[M7,M1b,...]` 네 chain이 전부 같은 signature 그룹이라 `(M1a,M1b)` 관계가 `M6`쪽
    조합과 `M7`쪽 조합 양쪽에서 독립적으로 검출되는데, `devices` 기준 dedup이라 먼저
    처리된 쪽만 출력 리스트에 남는다 -- 이때 `differential`(출력 리스트)만 보면 `M7`이
    이 관계에 참여했다는 사실 자체가 사라지지만, `differential_branch_members`는 dedup
    이전에 무조건 기록하므로 `M7`도 정확히 포함된다(`_propose_vertical_stack_ids()`의
    fan-in 판정이 바로 이 필드를 쓴다, 실측: `M58`의 fan-in 후보 `M6`/`M7` 중 `M7`만
    "차동쌍 소속 아님"으로 잘못 판정돼 `M58`->`M7`로 오확정되던 문제가 이걸로 해소되고
    `M58`->`M57`로 정정됨).

    ⚠️ **방향 인식 "상류 구간"만 누적(2026-08-08, 두 번의 시행착오 끝에 확정, 사용자
    통찰)** -- `branch_members`는 각 (a,b) 비교마다 `ca`/`cb`의 **그 비교 위치까지의
    상류 구간만** 담는다. `vdd_to_gnd`는 chain이 레일(VDD)에서 시작하므로 상류=앞쪽
    (`ca[:pos+1]`), `gnd_to_vdd`는 반대 방향이라 상류=뒤쪽(`ca[pos:]`, 레일이 chain의
    끝에 옴) -- 같은 `M10`/`M19`도 `vdd_to_gnd`에서는 위치3(하류, 제외)이지만
    `gnd_to_vdd`의 역순 chain에서는 위치0(방향을 안 따지면 "상류"로 잘못 보임)이라,
    방향을 명시적으로 반영해야 두 방향 모두 일관되게 "이 비교에 실제로 관여한 레일쪽
    경로"만 남는다(사용자가 "differential branch와 symmetric branch를 동시에 보고
    구별"하라고 지적한 게 이 지점 -- `M10`이 배제돼야 하는 이유는 `M19`와의 진짜
    mirror 관계 때문이 아니라 -- `M3a`/`M3b`도 서로 mirror 관계이면서 동시에 진짜
    differential branch 소속이라 그 기준은 틀렸었다 -- 이 특정 (M1a,M1b) 비교에
    도달하는 상류 경로가 아니기 때문이다). `M3a`/`M3b`는 `M4a`/`M4b` differential
    발견(위치4) 자체의 상류에 있어 그 발견을 통해 정확히 포함된다."""
    netclass, _idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, _imp, _assume = netclass.classify_nets(devs, inputs, outputs, biases, feedbacks, clocks)

    by_name = {t.name: t for t in transistors}

    def gate_of(name):
        return by_name[name].gate

    def gate_class(name):
        return cls.get(gate_of(name))

    def signature(b):
        return tuple((len(c["members"]), c["idiom"], tuple(by_name[m].kind for m in c["members"]))
                     for c in b["composites"])

    categories = ("differential", "mirror", "structurally_symmetric_no_connection")
    seen = {c: set() for c in categories}
    out = {c: [] for c in categories}
    branch_members = {c: set() for c in categories}
    for direction, terminal in (("vdd_to_gnd", "gnd"), ("gnd_to_vdd", "vdd")):
        composite_branches = suggest_vertical_stack_composites(
            transistors, inputs, outputs, feedbacks, biases, clocks, direction=direction)
        complete = [b for b in composite_branches if b["terminates_at"] == terminal]
        groups = defaultdict(list)
        for b in complete:
            groups[signature(b)].append(b["chain"])
        for chains in groups.values():
            if len(chains) < 2:
                continue
            for i in range(len(chains)):
                for j in range(i + 1, len(chains)):
                    ca, cb = chains[i], chains[j]
                    for pos, (a, b) in enumerate(zip(ca, cb)):
                        if a == b:
                            continue
                        if by_name[a].kind != by_name[b].kind:
                            category = "structurally_symmetric_no_connection"
                        elif gate_of(a) == gate_of(b):
                            category = "mirror"
                        elif gate_class(a) == "INPUT" and gate_class(b) == "INPUT":
                            category = "differential"
                        else:
                            category = "structurally_symmetric_no_connection"
                        # ⚠️ 2026-08-08 추가(사용자 지적) -- dedup은 출력 리스트(같은 소자쌍
                        # 중복 방지)에만 적용하고, 이 비교에 참여한 branch 소자는 dedup과
                        # 무관하게 항상 누적한다. 예: Vx가 M6/M7 두 소자로부터 병렬 공급되면
                        # [M6,M1a,...]/[M6,M1b,...]/[M7,M1a,...]/[M7,M1b,...] 네 chain이
                        # 전부 같은 signature 그룹에 들어가 (M1a,M1b) 관계가 M6쪽 조합과
                        # M7쪽 조합 양쪽에서 독립적으로 검출되는데, dedup_key가 (direction,
                        # frozenset(devices))라 소자쌍만 보므로 먼저 처리된 M6쪽만 out에
                        # 남고 M7쪽 발견은 조용히 버려졌다 -- 그 결과 "M7도 M1a/M1b 차동쌍의
                        # 유효한 대안 tail"이라는 사실이 diff_branch_members에서 사라져,
                        # _propose_vertical_stack_ids()의 fan-in 판정(M58 등)이 M7을
                        # 차동쌍 소속이 아니라고 잘못 판단하게 만들었다(실측 발견).
                        #
                        # ⚠️ **어느 구간을 누적할지가 두 번 틀렸다, 둘 다 실측/사용자 지적으로
                        # 발견**: (1차, 폐기) `ca`/`cb` 전체를 누적 -- 이 (ca,cb) 쌍 안에서
                        # 이 위치(pos)보다 하류에 있는, 이 관계와 무관한 별개 분기(예:
                        # `[M6,M1a,M2a,M19]` vs `[M6,M1b,M2b,M10]`의 위치3 `M19`/`M10`,
                        # `M9b`의 fan-in 후보 중 하나이자 진짜 mirror 관계의 당사자)까지
                        # 딸려 들어와 M9b의 재판정이 새로 깨졌다. (2차, 폐기) "core mirror
                        # 당사자면 differential에서 배제" -- 방향과 무관하다는 장점은 있었지만
                        # `M3a`/`M3b`처럼 **같은 differential branch 안에 물리적으로 스택된
                        # 캐스코드이면서 동시에 서로 mirror 관계**(같은 게이트)인 소자까지
                        # 배제해버려 Test 42가 깨졌다(`M3b`가 진짜 differential branch
                        # 소속인데 제외됨).
                        #
                        # **진짜 일반적 해법(사용자 통찰 -- "differential branch와 symmetric
                        # branch를 동시에 보고 구별")**: `M10`이 배제돼야 하는 이유는 "mirror
                        # 당사자라서"가 아니라 -- `M3b`도 mirror 당사자이지만 배제되면 안
                        # 되므로 -- **이 (M1a,M1b) 비교에 도달하기까지 실제로 거쳐온 상류
                        # 경로가 아니기 때문**이다. `vdd_to_gnd`에서 상류는 chain의 **앞쪽**
                        # (`ca[:pos+1]`, 레일=시작점)이고, `gnd_to_vdd`에서는 방향이 반대라
                        # 상류가 chain의 **뒤쪽**(`ca[pos:]`, 레일=끝점)이다 -- 그래서 같은
                        # `M10`/`M19`도 `vdd_to_gnd`에서는 하류(위치3, 절단으로 제외)지만
                        # `gnd_to_vdd`의 역순 chain에서는 앞쪽(위치0)에 와서 예전 "항상 접두사"
                        # 코드가 반대로 포함시켰던 것 -- 방향별로 상류 쪽 슬라이스를 쓰면
                        # 이 모순이 해소된다. `M3a`/`M3b`는 `M4a`/`M4b` differential 위치(4)
                        # 자체의 상류(`ca[:5]`)에 있어 그 발견을 통해 정확히 포함된다.
                        upstream = slice(0, pos + 1) if direction == "vdd_to_gnd" else slice(pos, None)
                        branch_members[category].update(ca[upstream])
                        branch_members[category].update(cb[upstream])
                        dedup_key = (direction, frozenset((a, b)))
                        if dedup_key in seen[category]:
                            continue
                        seen[category].add(dedup_key)
                        out[category].append({"direction": direction, "devices": (a, b),
                                                "branch_a": ca, "branch_b": cb, "position": pos})
    for c in categories:
        out[f"{c}_branch_members"] = sorted(branch_members[c])
    return out


def _propose_vertical_stack_ids(transistors, relations, base_inputs, outputs, feedbacks, biases, clocks):
    """`refine_differential_and_mirror_relations()`(아래)가 쓰는 내부 헬퍼 -- composite
    병합(§1.7d `suggest_vertical_stack_composites()`, **base_inputs만 사용** -- 세션24
    실측: promoted inputs를 쓰면 differential-pair 다리가 idiom 필터에서 정확히
    제외되면서 그 다리가 자기 tail 위에 물리적으로 붙어있다는 사실 자체가 어느
    composite에도 안 남는 부작용이 있었다, 아래 3번째 캐스케이드 참고)로 물리적 그룹의
    뼈대를 세우고, `relations`(promoted inputs로 계산된 `find_verified_differential_
    and_mirror_relations()` 결과)의 `branch_a`/`branch_b`+`position`으로 각 소자의
    leg(`a`/`b`)를 확인해 이름에 반영한다.

    ⚠️ **제안일 뿐이다** -- `suggest_vertical_stack_composites()`와 같은 원칙(이 함수도
    topology.json에 아무것도 쓰지 않는다). 이름 자체(`{idiom}_{순번}_{leg}`)는 기계적으로
    생성되지, `diffpair_top_a`처럼 회로 기능을 아는 사람이 지은 이름과 같은 수준의
    가독성은 없다 -- 실제 채택 시 이름을 사람이 다시 붙이는 걸 권장한다(세션24
    `vertical_stack_id` 15개 gap을 손으로 채울 때도 이 composite 근거를 그대로 쓰되
    이름은 직접 붙였음).

    **0. fan-in 후보 탐지(2026-08-07 추가, 사용자 지적으로 발견; 2026-08-08 `role`
    범위에 `FLOATING_CURRENT_SOURCE` 추가 -- `netclass.assign_roles()`가 `M9b`류
    floating-current-source 다리를 더 이상 `CASCODE`로 안 잡으므로, 이 fan-in
    탐지도 `CASCODE`/`FLOATING_CURRENT_SOURCE` 둘 다 봐야 `M9b` 실측 사례가 계속
    잡힌다)**: `role`이 이 둘 중 하나인 소자 `up`이 물리적으로 얹힐 수 있는 같은
    kind `lo` 후보(`lo.drain == up.source`)가 **2개 이상**이면(예: `M9b`의
    `source=Vop1`을 drain으로 쓰는 nmos가 `M3b`/`M10` 둘 다 있음) 순수 connectivity만
    으로는 어느 쪽이 진짜 물리적 이웃인지 원천적으로 못 가린다.

    **0-B. differential-pair branch 소속 여부로 재판정(2026-08-07 추가, 사용자 통찰)**:
    "이 소자 자신이 differential-pair의 핵심 신호경로 소속이 아니라면, 후보 중에서도
    그 신호경로에 안 걸리는 쪽이 더 적합하다"는 원칙 -- `relations["differential"]`의
    모든 `branch_a`/`branch_b` 멤버 합집합(`diff_branch_members`)을 구해서, 후보 중
    **정확히 하나만** 거기 안 걸리면 그쪽으로 확정(`resolved`), 나머지 하나(또는
    후보 전부가 걸리거나 전부 안 걸려서 구별 신호가 없으면)는 여전히 `ambiguous`로
    남긴다. 실측(`current_reuse_telescopic_ota`): 이 규칙으로 `M9b`→`M10`(`M3b`는
    differential branch 소속, `M10`은 아님), `M18b`→`M19`, `M58`→`M7`(`M6`은 그
    differential branch의 대표 hub라 소속, `M7`은 대표로 안 뽑혀서 비소속) 셋 다
    확정되어, 이 회로에서는 `ambiguous_alternatives`가 결국 빈 딕셔너리가 된다 --
    단 이건 이 회로의 실측 결과이지 일반 보장이 아니다(differential branch 소속
    여부로도 안 갈리는 회로/소자는 여전히 아래 `ambiguous_{name}`으로 남는다,
    self-test Test 41의 합성 fixture가 정확히 그런 "구별 신호가 아예 없는" 경우를
    검증한다).

    **1. composite 스캔(양방향, base_inputs, differential-pair branch 우선)**: 소자가
    처음 등장하는 composite(2개 이상 병합이든 단일 소자든 전부)에 그룹을 배정한다 --
    0-B에서 아직도 `ambiguous`로 남은 소자는 이 composite 병합에서 제외하고 격리
    그룹으로 따로 배정하며, `resolved`로 확정된 소자는 **자기 파트너가 포함된
    composite에서만** 합류한다(다른 후보와 얽힌 composite에는 안 낌 -- 안전망으로,
    파트너 composite이 이 스캔에서 한 번도 안 나오면 직접 합류시킨다). 각 방향의
    branch들을 처리할 때 `relations["differential"]`의 chain과 정확히 일치하는
    branch를 먼저 처리해 그 branch의 그룹 배정이 우선권을 갖게 한다(같은 물리적
    그룹이 여러 branch/방향에서 다시 나오면 이미 배정된 그룹을 재사용하는 메커니즘
    덕분). 이 재사용 메커니즘 덕분에 `M37a`/`M37b`/`M38`처럼 두 leg가 hub(`M38`)를
    공유하면 **자동으로 하나의 그룹으로 합쳐진다**(정확히 기존 `cmfb_tail` 선언과
    같은 모양, 실측으로 확인됨 -- leg가 둘 다 섞여 있으면 아래 3번에서 leg 접미사를
    안 붙인다).

    **2. differential/mirror 관계로 leg 접미사 부여 + singleton 흡수**: `relations`의
    각 `differential`/`mirror` 원소에서 `branch_a[position]`/`branch_b[position]`이 각각
    leg `a`/`b`다. 그 소자가 1번에서 이미 그룹을 받았으면 leg만 기록. 못 받았으면(예:
    idiom이 하나도 안 맞아 composite로 안 묶이는 경우) `position`의 바로 옆(±1) 소자가
    이미 그룹이 있으면 그 그룹에 흡수, 없으면 새 그룹 신설.

    **3. 최종 이름 조립**: 그룹에 속한 소자들의 leg가 **전부 하나(`a`만 또는 `b`만)**면
    그 leg를 접미사로 붙인다(`diffpair_top_a`류와 동일 패턴). leg가 섞여 있으면(hub
    공유 그룹) 접미사 없이 그대로 둔다(`cmfb_tail`류와 동일 패턴). 어느 leg에도 안
    걸리면(순수 composite만으로 배정된 그룹, 예: `stage1`류 후보) 접미사 없음.
    `ambiguous_{name}`(0-B로도 못 푼 소자)은 이 조립을 거치지 않고 이름 그대로
    반환된다(Test 41의 합성 fixture로 검증).

    ⚠️ `ambiguous_{name}`으로 격리만 하고 끝나면 나중에 `resolve_stack_layout()`류
    layout 함수가 이 소자를 어디에도 못 놓고 막힌다 -- 그래서 격리된 소자마다
    **후보 그룹 이름 목록**(fan-in 후보 `lo` 각각이 속한 그룹, 아직 그룹이 없으면
    자기 이름 그대로)도 같이 반환한다. layout 함수는 이 후보 중 하나를 골라(예:
    헤드룸/핑거 호환성 기준) 그 그룹에 합류시키는 식으로 이 정보를 쓸 수 있다 --
    이 함수 자체는 여전히 어느 쪽도 대신 고르지 않는다(제안만 하는 원칙 유지).

    반환: `{"groups": {device_name: proposed_vertical_stack_id, ...}, "ambiguous_
    alternatives": {device_name: [candidate_group_name, ...], ...}}` -- `groups`는
    51개 회로라면 51개 키 전부 포함(모든 소자가 최소한 자기 혼자만의 singleton 그룹은
    받는다). `ambiguous_alternatives`는 0-B로도 못 푼 소자만 키로 가진다(`current_
    reuse_telescopic_ota`에서는 실측상 빈 딕셔너리, Test 41의 합성 fixture로 채워지는
    경우를 검증). `suggest_vertical_stack_composites()`가 `None`을 반환하면
    (analog-grammar 없음) 이 함수도 `None`."""
    netclass, _idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    cls, imp, _assume = netclass.classify_nets(devs, base_inputs, outputs, biases, feedbacks, clocks)
    role = netclass.assign_roles(devs, cls, imp)

    by_drain_kind = defaultdict(list)
    for t in transistors:
        by_drain_kind[(t.drain, t.kind)].append(t.name)
    fan_in_candidates = {}
    for t in transistors:
        if role.get(t.name) not in (netclass.CASCODE, netclass.FLOAT_SRC, netclass.DIODE_CASC):
            continue
        candidates = [n for n in by_drain_kind.get((t.source, t.kind), []) if n != t.name]
        if len(candidates) > 1:
            fan_in_candidates[t.name] = candidates

    # ⚠️ 2026-08-07 추가(사용자 지적): fan-in 후보 중 정확히 하나만 differential-pair
    # branch 소속이 아니면(예: M9b의 후보 M3b는 differential branch 멤버, M10은 아님)
    # differential branch에 안 걸리는 쪽을 우선한다 -- "이 소자 자체가 differential
    # branch 소속이 아니라면, differential branch의 일부인 후보보다는 그렇지 않은
    # 후보가 더 적합하다"는 원칙(differential-pair의 핵심 신호경로를 곁가지 tap으로
    # 오염시키지 않음). 후보가 둘 다 걸리거나 둘 다 안 걸리면(구별 신호 없음) 여전히
    # ambiguous로 남긴다.
    #
    # ⚠️ 2026-08-08 수정(사용자 지적) -- 원래는 relations["differential"]의 branch_a/
    # branch_b만 모았는데, find_verified_differential_and_mirror_relations()가 소자쌍
    # 단위로 dedup하면서(같은 (a,b)가 여러 branch 조합에서 나오면 하나만 남김) M7처럼
    # "M1a/M1b 차동쌍의 유효한 대안 tail"인데도 M6쪽 조합이 먼저 dedup에 남는 바람에
    # branch_a/branch_b 어디에도 안 나타나는 소자가 생겼다(실측 발견: M58의 fan-in
    # 후보 M6/M7 중 M7만 "differential branch 소속 아님"으로 잘못 판정되어 M58->M7로
    # 오확정됨, 실제로는 M58->M57이 맞다 -- M7도 M6과 마찬가지로 진짜 tail이라
    # differential branch 소속이어야 한다). find_verified_differential_and_mirror_
    # relations()가 이제 dedup 이전에 비교에 참여한 모든 branch를 따로 누적해
    # "differential_branch_members"로 반환하므로 그걸 직접 쓴다 -- 없으면(구버전
    # relations 하위호환) branch_a/branch_b로 폴백.
    diff_branch_members = set(relations.get("differential_branch_members") or [])
    if not diff_branch_members:
        for r in relations.get("differential", []):
            diff_branch_members.update(r["branch_a"])
            diff_branch_members.update(r["branch_b"])

    resolved, ambiguous = {}, set()
    for dev, candidates in fan_in_candidates.items():
        outside = [c for c in candidates if c not in diff_branch_members]
        inside = [c for c in candidates if c in diff_branch_members]
        if len(outside) == 1 and inside:
            resolved[dev] = outside[0]
        else:
            ambiguous.add(dev)
    candidates_of = {dev: cands for dev, cands in fan_in_candidates.items() if dev in ambiguous}

    group_of, members_of, counter = {}, defaultdict(set), defaultdict(int)

    def assign(names, idiom):
        filtered = []
        for n in names:
            # ⚠️ 2026-08-08 수정(사용자 지적) -- 원래는 ambiguous 소자를 "어떤 composite
            # 에도" 못 끼게 조용히 전부 막았다(M58이 M6/M7 중 뭘 골라야 할지 모른다는
            # 이유로, M57과의 명확한 diode-cascode 관계까지 같이 막혀서 ambiguous_M58로
            # 고립됨). ambiguous는 "이 소자의 특정 후보들 사이에서 못 고른다"는 뜻이지
            # "이 소자가 다른 모든 관계에서도 무효"라는 뜻이 아니다 -- 그 후보가 실제로
            # 이 composite 안에 있을 때만(=이 composite에 합류하는 게 곧 그 모호한 선택을
            # 암묵적으로 확정하는 셈일 때만) 제외한다. 관련 없는 composite(M58+M57류)는
            # 정상적으로 합류한다.
            if n in ambiguous and any(c in names for c in fan_in_candidates.get(n, ())):
                continue
            if n in resolved and resolved[n] not in names:
                continue  # resolved 소자는 자기 파트너가 낀 composite에서만 합류한다
            filtered.append(n)
        names = filtered
        if not names:
            return None
        existing = next((group_of[n] for n in names if n in group_of), None)
        if existing is None:
            key = idiom or "stack"
            counter[key] += 1
            existing = f"{key}_{counter[key]}"
        for n in names:
            if n not in group_of:
                group_of[n] = existing
                members_of[existing].add(n)
        return existing

    for direction in ("vdd_to_gnd", "gnd_to_vdd"):
        branches = suggest_vertical_stack_composites(
            transistors, base_inputs, outputs, feedbacks, biases, clocks, direction=direction)
        if branches is None:
            return None
        diff_chains = {tuple(r["branch_a"]) for r in relations.get("differential", [])} | \
                      {tuple(r["branch_b"]) for r in relations.get("differential", [])}
        priority, rest = [], []
        for b in branches:
            (priority if tuple(b["chain"]) in diff_chains else rest).append(b)
        for b in priority + rest:
            for c in b["composites"]:
                assign(c["members"], c["idiom"])

    # ⚠️ 2026-08-08 이동(사용자 지적) -- 원래는 이 pre-population이 위 composite 스캔보다
    # *먼저* 실행됐다. 그러면 M58처럼 ambiguous인 소자가 M57과의 명확한 diode-cascode
    # composite을 스캔에서 만나도, group_of에 이미 "ambiguous_M58"이 박혀 있어서
    # assign()의 existing 재사용 로직이 그 이름을 그대로 물려받아 M57까지 억지로
    # ambiguous_M58에 편입되는 문제가 있었다(위 assign() 필터를 "관련 없는 composite도
    # 막는" 문제와 함께 고침, 실측 발견). 이제 스캔이 실제로 찾아준 명확한 관계를 먼저
    # 전부 반영하고, **그러고도 여전히 그룹이 없는** ambiguous 소자만 고립시킨다.
    for name in ambiguous:
        if name in group_of:
            continue
        group_name = f"ambiguous_{name}"
        group_of[name] = group_name
        members_of[group_name].add(name)

    # 위 composite 스캔에서 resolved 소자의 파트너 composite이 한 번도 안 나왔으면
    # (드문 경우, 다른 회로에서 발생 가능) 안전망으로 직접 합류시킨다.
    for dev, partner in resolved.items():
        if dev in group_of:
            continue
        target = assign([partner], None) or group_of.get(partner)
        group_of[dev] = target
        members_of[target].add(dev)

    leg_of = {}
    for category in ("differential", "mirror"):
        for r in relations.get(category, []):
            pos = r["position"]
            for letter, branch in (("a", r["branch_a"]), ("b", r["branch_b"])):
                dev = branch[pos]
                leg_of.setdefault(dev, letter)
                if dev in group_of:
                    continue
                neighbor = next((group_of[branch[j]] for j in (pos - 1, pos + 1)
                                  if 0 <= j < len(branch) and branch[j] in group_of), None)
                name = neighbor or assign([dev], category)
                group_of[dev] = name
                members_of[name].add(dev)

    out = {}
    for name, members in members_of.items():
        legs = {leg_of[m] for m in members if m in leg_of}
        final_name = f"{name}_{next(iter(legs))}" if len(legs) == 1 else name
        for m in members:
            out[m] = final_name

    # ⚠️ 2026-08-08 추가(사용자 지적 이슈의 연쇄 수정) -- ambiguous pre-population을
    # 스캔 뒤로 미루면서(위 참고) candidates_of(원래 "resolved 판정 통과 못함" 집합)
    # 그대로 쓰면, 스캔이 나중에 실제 그룹을 찾아준 소자(M9b/M18b류 -- 원래 판정은
    # ambiguous였지만 diode-cascode/physical-stack 스캔에서 자기 파트너를 찾아 진짜
    # 그룹에 합류함)까지 "여전히 미해결"로 잘못 보고하게 된다. 최종적으로 자기 자신만의
    # 고립 그룹(`ambiguous_{dev}`)에 남은 소자만 진짜 미해결이다.
    ambiguous_alternatives = {
        dev: sorted({group_of.get(c, c) for c in candidates})
        for dev, candidates in candidates_of.items()
        if group_of.get(dev) == f"ambiguous_{dev}"}

    return {"groups": out, "ambiguous_alternatives": ambiguous_alternatives}


def _propose_gm_id_roles(transistors, base_inputs, outputs, feedbacks, biases, clocks):
    """`refine_differential_and_mirror_relations()`가 쓰는 내부 헬퍼 -- `topology.json`
    `device_roles`의 `gm_id_role`(`matching`/`gain`/`balanced` 중 이 프로젝트가 실제로
    쓰는 두 값) 후보를 제안한다.

    ⚠️ **왜 이건 `headroom_role`과 달리 구조만으로 될까(사용자 지적, 2026-08-08)**:
    처음엔 `headroom_role`의 `mirror`/`cascode` 구분처럼 이것도 안 될 거라 생각했으나,
    이미 선언된 36개 소자 전체(`current_reuse_telescopic_ota`)를 대조해보니 **정확히
    하나의 구조적 신호로 36/36 다 맞는다**는 게 실측으로 확인됐다: `find_differential_
    pair_candidates()`가 찾은 `shared_source`(차동쌍이 공유하는 tail net)를 **drain으로
    받는 소자**(=그 차동쌍에 tail 전류를 대는 소자, 예: `M6`/`M7`→`Vx`, `M5`→`Vy`,
    `M38`→`Ncmfb_tail`) → `balanced`, **그 나머지 전부** → `matching`. `headroom_role`의
    `mirror`/`cascode` 구분은 세 가지 구조적 가설(up/lo 위치, `matching_pairs` 소속,
    diode 단독/체인)을 다 시도해도 반례가 나왔지만(sizing_roles.theta의 어떤 feed
    타입이 이 소자를 결정하는지 같은, 구조 분석 범위 밖 정보가 필요해 보임), `gm_id_role`
    은 "이 소자가 GBW가 중요한 차동쌍의 tail 전류원인가"라는 **단일 질문**만으로
    충분했다 -- 회로 설계 원칙상 tail 전류원(GBW 직결)과 나머지(bias/mirror, gm/ID
    최소화가 우선)라는 이분법이 정확히 이 신호와 일치하기 때문으로 보인다.

    analog-grammar가 없으면(`find_differential_pair_candidates()`가 의존) `None`을
    반환한다.

    ⚠️ **2026-08-14 정정(사용자 지시 -- `load_topology()` 자동배선 중 실측 발견)**: 원래는
    `t.drain in shared_sources`가 아니면 무조건 `"matching"`을 채웠다 -- **연결관계가 전혀
    없는 고립 소자에도** `"matching"`이 나온다는 뜻이라(실측: 소자 1개짜리 netlist),
    이 함수를 자동 파이프라인에 걸면 근거 없는 값이 조용히 주입되는 위험이 있었다. 이제는
    `_propose_L_roles()`가 이미 계산하는 것과 동일한 전역 좌우 구조 대칭(`find_structural_
    symmetry_candidates(transform="mirror")`, 부트스트랩이 찾은 차동쌍 gate net으로 seed
    자동 구성)에서 **자기 자신이 아닌 다른 소자로 실제로 풀리는 경우만** `"matching"`으로
    확정한다 -- 그 외(대칭 파트너를 못 찾음)는 이 dict에서 아예 뺀다(값을 안 채움, 틀린
    기본값을 넣지 않음).

    반환(있으면): `{device_name: "balanced"|"matching", ...}` -- **이제 sparse dict다**
    (근거 있는 소자만 키로 있음, 51개 회로 전부가 아닐 수 있음 -- 이전 버전과 반대).
    `M1a`/`M1b`/`M2a`/`M2b`/`M3a`/`M3b`/`M4a`/`M4b`/`M15`/`M16`/`M25`/`M26`류(차동쌍 자신 +
    보상 스테이지 소자)는 `compensation.stage_devices`/`sizing_roles.theta`(type C)가 이미
    L/W/gm을 직접 정하므로 `device_roles`에 `gm_id_role`을 안 써도 되는 소자이지만, 이
    함수는 여전히(구조적으로 매칭 파트너가 실제로 있으면) 포함한다 -- `topology.json`에
    실제로 반영할지는 소자마다 다를 수 있다."""
    candidates = find_differential_pair_candidates(
        transistors, base_inputs, outputs, feedbacks, biases, clocks)
    if candidates is None:
        return None
    shared_sources = {c["shared_source"] for c in candidates["candidates"]}
    by_name = {t.name: t for t in transistors}
    seeds = {"vdd": "vdd", "gnd": "gnd"}
    for c in candidates["candidates"]:
        a, b = c["devices"]
        ga, gb = by_name[a].gate, by_name[b].gate
        seeds[ga] = gb
        seeds[gb] = ga
    symmetry = find_structural_symmetry_candidates(transistors, seeds, transform="mirror")
    out = {}
    for t in transistors:
        if t.drain in shared_sources:
            out[t.name] = "balanced"
            continue
        partner = symmetry.device_map.get(t.name)
        if partner is not None and partner != t.name:
            out[t.name] = "matching"
    return out


def _propose_L_roles(transistors, relations, base_inputs, outputs, feedbacks, biases, clocks):
    """`refine_differential_and_mirror_relations()`가 쓰는 내부 헬퍼 -- `topology.json`
    `device_roles`의 `L_role`(`mirror`=2.5*L_min | `bias_replica`=1.2*L_min) 후보를
    제안한다.

    ⚠️ **2026-08-08 두 번째 수정(사용자 지적: "극성을 고려해서 매칭 파트너를 잡게")**:
    처음 버전은 `relations["mirror"]`(branch 구조가 완전히 같은 쌍만 봄, 10/36만
    커버)로만 근거를 댔는데, `M11a`의 진짜 좌우 파트너가 (같은 스택 안의 `M11b`가
    아니라) **`M20a`라는 걸 놓치는 문제**가 있었다 -- `M11a`/`M20a`는 서로 다른 branch
    (vom쪽 diode 체인 vs vop쪽 diode 체인)에 있어서 `relations["mirror"]`(같은
    matched-branch-pair 안에서만 비교)가 원천적으로 못 찾는다. 이미 있는
    `find_structural_symmetry_candidates()`(§1.8, `transform="mirror"`로 kind를
    보존하며 전역 netlist 자동매칭 -- 바로 이 함수가 세션6에서 `M11a`의 진짜 짝이
    `M20a`임을 처음 밝혀낸 도구)를 seed 없이 놀리지 않고 연결했다: `find_differential_
    pair_candidates()`가 찾은 각 차동쌍의 게이트 net(예: `Vip`/`Vim`, `Voc`/`Voc_des`)을
    좌우 대응 seed로 자동 생성하고(+ `vdd`/`gnd` 자기자신 seed), `transform="mirror"`로
    전역 대칭을 푼다. 실측: `current_reuse_telescopic_ota` 51개 중 **48개**가 풀리고
    (`M11a<->M20a`, `M14a<->M23a`, `M9a<->M18a`, `M8<->M17` 등 정확히 declared
    `matching_pairs`와 일치), `M39`/`M40`/`M7`만 `unresolved`로 남는다(이 함수 자체의
    docstring이 명시하듯 "실패가 아니라 사람 판정 신호" -- `M7`은 `M6`과 원래 비대칭
    설계라 정상).

    **최종 규칙**: (1) tail 공급 소자(`gm_id_role=='balanced'`) -> `bias_replica`.
    (2) `find_structural_symmetry_candidates()`의 `device_map`에서 **자기 자신이 아닌
    다른 소자**로 풀리면 -> `mirror`, `confirmed_by_structural_symmetry=True`,
    `symmetry_partner`에 그 소자 이름. (3) 그 외(unresolved거나 자기자신-대칭)는
    여전히 `mirror`를 기본값으로 제안하되 `confirmed_by_structural_symmetry=False`
    (이전 버전의 "기본값" 근거만 남음 -- 실측: `current_reuse_telescopic_ota`에서
    이 경로로 떨어지는 건 tail 소자 자신 말고는 없음, 대부분 (2)로 확정됨).

    ⚠️ **`M38`은 이 규칙의 유일한 예외(35/36)** -- `topology.json`의 `_M38_L_role_
    comment`에 이미 상세히 문서화됨: `M38`도 tail 공급 소자(`gm_id_role=balanced`)라
    이 규칙대로면 `bias_replica`가 나와야 하는데, 실제 declared 값은 `mirror`다.
    CMFB 루프이득(`A_c`) 재분석 결과 `gds38`이 작을수록 `|A_c|`가 커져 CM 루프이득에
    유리하다는 **전기적 분석**으로 사람이 의도적으로 override한 사례라, 구조 분석만으로
    재현 가능한 성질이 아니다 -- 이 함수는 이 예외를 반영하지 않는다(구조적 기본값만
    제안, `topology.json` 채택 시 `M38`은 사람이 직접 `mirror`로 남겨둘 것).

    analog-grammar가 없으면 `None`을 반환한다.

    ⚠️ **2026-08-14 정정(사용자 지시)**: 이전엔 대칭 파트너를 못 찾은 소자도 `"mirror"`를
    기본값으로 채우고 `confirmed_by_structural_symmetry=False`로만 표시했다 -- 근거 없는
    값이 자동 파이프라인에 조용히 흘러들어갈 위험이 있었다(`_propose_gm_id_roles()`와
    동일 문제, 같은 이유로 정정). 이제 tail 공급 소자도 아니고 구조 대칭 파트너도 없으면
    이 dict에서 아예 뺀다 -- `confirmed_by_structural_symmetry=False`인 항목은 더 이상
    안 나온다(있으면 항상 `True`).

    반환(있으면): `{device_name: {"L_role": "bias_replica"|"mirror",
    "confirmed_by_structural_symmetry": bool, "symmetry_partner": str|None}, ...}` --
    **이제 sparse dict다**(근거 있는 소자만)."""
    gm_id_roles = _propose_gm_id_roles(transistors, base_inputs, outputs, feedbacks, biases, clocks)
    if gm_id_roles is None:
        return None
    candidates = find_differential_pair_candidates(
        transistors, base_inputs, outputs, feedbacks, biases, clocks)
    if candidates is None:
        return None
    by_name = {t.name: t for t in transistors}
    seeds = {"vdd": "vdd", "gnd": "gnd"}
    for c in candidates["candidates"]:
        a, b = c["devices"]
        ga, gb = by_name[a].gate, by_name[b].gate
        seeds[ga] = gb
        seeds[gb] = ga
    symmetry = find_structural_symmetry_candidates(transistors, seeds, transform="mirror")

    out = {}
    for t in transistors:
        if gm_id_roles.get(t.name) == "balanced":
            out[t.name] = {"L_role": "bias_replica",
                            "confirmed_by_structural_symmetry": False, "symmetry_partner": None}
            continue
        partner = symmetry.device_map.get(t.name)
        confirmed = partner is not None and partner != t.name
        if confirmed:
            out[t.name] = {"L_role": "mirror", "confirmed_by_structural_symmetry": True,
                            "symmetry_partner": partner}
        # else: 근거(tail 공급도 아니고 구조 대칭 파트너도 없음) 없이 "mirror"를 기본값으로
        # 채우지 않는다(2026-08-14 정정, _propose_gm_id_roles()와 동일 이유) -- 이 dict에서
        # 그냥 뺀다.
    return out


def _propose_headroom_roles(transistors, gm_id_role_candidates, vertical_stack_id_candidates,
                              L_role_candidates, base_inputs, outputs, feedbacks, biases, clocks):
    """`refine_differential_and_mirror_relations()`가 쓰는 내부 헬퍼 -- `topology.json`
    `device_roles`의 `headroom_role`(`mirror`/`cascode`/`tail`/`floating_current_source`)
    후보를 제안한다.

    ⚠️ **6가지 실패한 가설 뒤에 나온 37/37 규칙(2026-08-08, 사용자와 함께 여러 라운드
    반례 검증)** -- `.ai/context.md` 세션25 F/G절에 전체 경위 기록. 이전 6가지 가설
    (up/lo 위치, `matching_pairs` 소속, diode 단독/체인, `m_mirror()` 단독, `m_mirror()`+
    tail 제외(9/35까지), "lo-of-cascode-stack" 예외)은 전부 `m_cascode()`/`netclass.
    assign_roles()` 자체가 `M9a`류(Monticelli floating current source)와 `M63`류
    (diode-cascode)를 그냥 `CASCODE`로 뭉뚱그리던 **더 아래 계층의 오분류**를 물려받고
    있었다 -- 그 두 role(`FLOATING_CURRENT_SOURCE`/`DIODE_REFERENCED_CASCODE`)이
    `netclass.py`에 분리되고 나서야 이 규칙이 성립했다.

    **최종 규칙(위→아래 순서로 첫 매치)**:
    1. `role == FLOATING_CURRENT_SOURCE` → `floating_current_source`
    2. `gm_id_role_candidates[dev] == "balanced"`(차동쌍 tail 전류원) → `tail`
    3. `role in (CURRENT_SOURCE, ACTIVE_LOAD)`(레일에 직접 닿은 고정 바이어스) → `mirror`
    4. `role == DIODE_REFERENCED_CASCODE`(diode 바로 아래서 그 노드를 게이트로 받음,
       `idioms.m_diode_cascode()`) → 그 diode 파트너가 `current-mirror` idiom의 `ref`
       이거나, 파트너의 `vertical_stack_id_candidates` 그룹에 그런 `ref`가 있거나,
       파트너의 `L_role_candidates.symmetry_partner`가 `ref`면 → `mirror`, 아니면
       → `cascode`
    5. `role == CASCODE` → `cascode`
    6. `role == DIODE_CONNECTED` → 규칙 4와 같은 "mirror_ref 여부/그룹·대칭 공유" 판정

    **실측**: `current_reuse_telescopic_ota` 선언된 37개(`headroom_role`이 있는 전체)
    **37/37 일치**(`M10`/`M19`/`M9a`/`M9b`/`M18a`/`M18b`/`M37b`/`M63`/`M39`/`M40`이
    이번 세션에 선언 오류로 정정된 뒤 기준, `.ai/context.md` F/G절 참고 -- `M39`/`M40`
    은 `M11a`/`M11b`와 구조적으로 동일한 diode-connected 2단 floating-battery(mirror_
    ref도 대칭 파트너도 없음)인데 `mirror`로 잘못 선언돼 있었다, 사용자 지적으로 확정)
    -- 이전 최고 기록(9/35 불일치)에서 크게 개선됐지만 **다른 회로에서의 일반성은
    검증 안 됨**(이 회로 하나로만 확인, 프로젝트 원칙 그대로 사람 재검토 권장).

    ⚠️ `M1a`/`M1b`/`M2a`/`M2b`/`M3a`/`M3b`/`M4a`/`M4b`/`M15`/`M16`/`M25`/`M26`류(차동쌍
    자신 + 보상 스테이지)와 `M37a`/`M37b`(CMFB 2차 차동쌍, `M37b`도 이번 세션에 같은
    이유로 gap 처리됨)는 `compensation.stage_devices`가 이미 L/W/gm을 결정하므로
    `device_roles`에 `headroom_role`을 안 써도 되는 소자다 -- `_propose_gm_id_roles()`
    와 똑같은 원칙(사용자 지적, 2026-08-08)으로 이 함수도 이 소자들을 **제외하지 않고**
    51개 전부 일관되게 반환한다(하드코딩된 제외 목록을 두면 이 회로 전용이 되고, 다른
    회로엔 이름이 안 맞아 조용히 무의미해진다) -- `topology.json`에 실제로 채택할지는
    소자마다, 그리고 이 12+2개는 대개 다른 경로가 이미 값을 정하므로 채택 안 해도 됨.

    analog-grammar가 없으면 `None`을 반환한다.

    ⚠️ **2026-08-14 -- `_propose_gm_id_roles()`/`_propose_L_roles()`와 달리 이 함수는
    그대로 둔다(사용자 지시로 시도했다가 Test 45 회귀로 잘못됐음을 확인하고 되돌림)**:
    gm_id_role="matching"/L_role="mirror"는 다른 소자와의 매칭 관계가 있어야만 의미가
    있는 "이 소자를 저 소자와 짝지어 매칭 배치하라"는 제안이라, 매칭 파트너가 없는
    고립 소자에 붙으면 `select_L_by_role()`/`search_gm_id_for_role()`을 실제로 실행시켜
    크래시까지 낸다(그래서 구조 대칭 파트너가 실제로 확인될 때만 값을 낸다). 반면
    `headroom_role`(특히 규칙 3, `CURR_SRC`/`ACTIVE_LOAD` → `mirror`)은 **소자 자신의
    connectivity만으로 완결되는 독립 판정**이다 -- "레일에 직접 물린 고정 전류원인가"는
    매칭 파트너 유무와 무관하게 참/거짓이 정해지고(Test 45의 M8이 실측 반례: 매칭
    파트너가 fixture에 전혀 없어도 여전히 `mirror`가 정답), `allocate_stack_headroom()`의
    VDS 예산 라벨일 뿐이라 크래시를 유발하지도 않는다.

    반환(있으면): `{device_name: "mirror"|"cascode"|"tail"|"floating_current_source"|
    None, ...}` -- 51개 회로라면 51개 키 전부 포함(role이 이 규칙 어디에도 안 걸리면
    `None`, 예: gate가 SIGNAL/INPUT을 직접 받는 `AMPLIFYING`류)."""
    netclass, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass is None:
        return None
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return None
    cls, imp, _assume = netclass.classify_nets(devs, base_inputs, outputs, biases, feedbacks, clocks)
    role = netclass.assign_roles(devs, cls, imp)
    matches = idioms_mod.match_all(devs, cls, imp, role)
    mirror_refs = {m.ports['ref'] for m in matches if m.kind == 'current-mirror'}
    diode_cascode_lo = {m.ports['lo']: m.ports['diode'] for m in matches if m.kind == 'diode-cascode'}

    vs_groups = (vertical_stack_id_candidates or {}).get('groups', {})
    group_has_ref = defaultdict(bool)
    for n, g in vs_groups.items():
        if n in mirror_refs and g:
            group_has_ref[g] = True

    def _diode_like_mirror(name):
        if name in mirror_refs: return 'mirror'
        if group_has_ref.get(vs_groups.get(name)): return 'mirror'
        # 물리적으로 안 쌓여도(병렬 load쌍처럼) 구조적 좌우 대칭 파트너가 mirror_ref면
        # 같은 취급(예: M36b의 대칭 파트너 M36a가 current-mirror ref).
        partner = (L_role_candidates or {}).get(name, {}).get('symmetry_partner')
        if partner and partner in mirror_refs: return 'mirror'
        return 'cascode'

    out = {}
    for t in transistors:
        n = t.name
        r = role.get(n)
        if r == netclass.FLOAT_SRC:
            out[n] = 'floating_current_source'
        elif gm_id_role_candidates and gm_id_role_candidates.get(n) == 'balanced':
            out[n] = 'tail'
        # 2026-08-14 -- 이 규칙(레일에 직접 닿은 고정 바이어스 => mirror)은 gm_id_role/
        # L_role과 달리 **소자 자신의 connectivity만으로 완결되는 독립 판정**이다(다른
        # 소자와의 매칭 관계가 전제 조건이 아니다 -- "이 소자가 레일에 직접 물린 고정
        # 전류원/부하인가"는 그 소자 하나만 봐도 답이 나온다). 실측(Test 45 합성 fixture,
        # M8): 매칭 파트너가 fixture에 전혀 없어도 M8은 여전히 'mirror'가 맞다. 처음엔
        # gm_id_role/L_role과 같은 이유(고립 소자에도 'mirror' 나옴)로 여기도 confirmed
        # 소자만으로 좁혔다가, 이 회귀로 잘못됐음을 확인하고 되돌렸다 -- headroom_role은
        # gm_id_role/L_role(select_L_by_role()/search_gm_id_for_role()을 실제로 실행시켜
        # TypeError를 내는 위험한 필드)과 달리 allocate_stack_headroom()의 VDS 예산 배분
        # 라벨일 뿐이라, 매칭 파트너 없이 붙어도 크래시를 유발하지 않는다(위험의 성격이
        # 다르다).
        elif r in (netclass.CURR_SRC, netclass.ACTIVE_LOAD):
            out[n] = 'mirror'
        elif n in diode_cascode_lo:
            out[n] = _diode_like_mirror(diode_cascode_lo[n])
        elif r == netclass.CASCODE:
            out[n] = 'cascode'
        elif r == netclass.DIODE:
            out[n] = _diode_like_mirror(n)
        else:
            out[n] = None
    return out


def refine_differential_and_mirror_relations(transistors: list, inputs=(), outputs=(),
                                               feedbacks=(), biases=(), clocks=(),
                                               max_iterations: int = 5) -> dict | None:
    """`find_differential_pair_candidates()`(C-11)가 `inputs=` 선언 없이 순수
    connectivity로 찾아낸 differential pair 후보의 gate net을 **자동으로**
    `inputs=`에 승격해서 `find_verified_differential_and_mirror_relations()`를
    재실행하는 오케스트레이션(`.ai/context.md` D절 item 0, 2026-08-07 사용자 지시로
    세션24에 신설). 세션23까지는 이 승격을 사람이 손으로 한 번(`Voc`/`Voc_des`를
    수동으로 `inputs=`에 넣어) 했을 뿐 코드화되어 있지 않았다.

    **왜 반복(iteration)인가**: 한 번의 승격이 새 net을 SIGNAL로 바꾸고, 그 net을
    게이트로 받는 다른 소자의 role도 바꿀 수 있다(아래 실측). 그 role 변화가 다시
    새로운 differential-pair 후보를 드러낼 가능성을 이론적으로 배제할 수 없어서(세션23
    C-11 마지막 문단이 "1회 반복으로 충분할 것으로 예상되나 미검증"이라고 명시),
    새 후보가 더 이상 안 나올 때까지(고정점) 반복하되 `max_iterations`로 상한을 둔다
    (무한루프 방지, 대부분 회로는 후보 재확인 라운드까지 포함해 2회 안에 고정점 도달 --
    `find_differential_pair_candidates()`는 net 분류를 안 쓰므로 후보 자체는 첫 라운드
    이후 보통 안 바뀐다).

    **설계 스케치(그대로 구현)**:
    1. `find_differential_pair_candidates(transistors, cur_inputs, ...)`로 후보 수집.
    2. 후보 `devices` 쌍의 gate net(`by_name[dev].gate`)을 전부 추출해 아직 `cur_inputs`
       에 없는 것만 승격 대상으로 모음.
    3. 승격 대상이 없으면 고정점 도달, 종료. 있으면 `cur_inputs`에 합쳐 1로 돌아감.
    4. 최종 `cur_inputs`로 `find_verified_differential_and_mirror_relations()` 재실행.
    5. **role/net class가 바뀐 소자·net은 조용히 덮어쓰지 않고 결과에 명시**(프로젝트
       전역 원칙) -- 원래 `inputs=`와 최종 `cur_inputs` 각각으로 `netclass.classify_
       nets()`/`assign_roles()`를 돌려 전/후를 비교한다(실측 예: `Voc`가 `BIAS`→
       `INPUT`으로 선언되면 그 net을 드라이브하는 소자의 drain net이 `BIAS`→`SIGNAL`로
       재분류되고, 그 net을 게이트로 받는 소자의 role이 `ACTIVE_LOAD`/`CURRENT_SOURCE`
       →`AMPLIFYING`으로 바뀔 수 있다 -- 세션23 `M7`: `CURRENT_SOURCE`→`AMPLIFYING`).

    analog-grammar가 없으면(`find_differential_pair_candidates()`가 의존) `None`을
    반환한다.

    ⚠️ **2026-08-07 추가(세션24, 사용자 지시)**: `vertical_stack_id_candidates` 필드로
    cascode-stack 등 composite 병합(물리적 그룹)과 differential-pair/mirror 관계(leg
    a/b 판정)를 합친 최종 `vertical_stack_id` 후보를 같이 반환한다 -- 자세한 알고리즘은
    `_propose_vertical_stack_ids()` 참고. **이 필드도 제안일 뿐이다**(topology.json에
    자동으로 쓰지 않음, 이름도 기계적으로 생성되어 사람이 다시 붙이는 걸 권장). 같은
    kind의 물리적 fan-in 후보가 2개 이상이라 구조만으로 못 가리는 소자는 `ambiguous_
    {name}`으로 격리하고, `ambiguous_alternatives`에 그 소자가 들어갈 수 있는 후보
    그룹 이름 목록을 같이 반환한다(2026-08-07 추가, 사용자 요청 -- 나중에 `resolve_
    stack_layout()`류 layout 함수가 이 후보 중 하나를 골라 합류시킬 수 있도록).

    ⚠️ **2026-08-08 추가(사용자 지시)**: `gm_id_role_candidates` 필드로 `device_roles`
    `gm_id_role` 후보(`"balanced"`|`"matching"`)도 같이 반환한다 -- 자세한 근거는
    `_propose_gm_id_roles()` 참고(36/36 실측 일치, `headroom_role`의 `mirror`/`cascode`
    구분과 달리 이건 구조 신호 하나로 충분히 갈렸다). **2026-08-13 정정(사용자 지시)**:
    이 필드에 최종 노출되는 값은 `_propose_gm_id_roles()`의 원본(balanced/matching)이
    아니라, `L_role_candidates`가 있는(=mirror 또는 bias_replica로 분류된) 모든 소자를
    `"matching"`으로 덮어쓴 값이다(mirror/bias_replica 둘 다 레이아웃 매칭이 필요하므로
    -- `"balanced"`는 W_bounds 안 아무 feasible gm/ID나 골라 매칭을 보호하지 않음).
    `_propose_headroom_roles()`에 넘기는 원본 신호(tail 판정)는 이 덮어쓰기 이전 값을
    그대로 쓰므로 `headroom_role_candidates`는 영향받지 않는다. `L_role_candidates` 필드로
    `L_role` 후보(`"mirror"`|`"bias_replica"`)도 반환한다 -- `_propose_L_roles()` 참고,
    `find_differential_pair_candidates()`의 차동쌍 게이트를 seed로 `find_structural_
    symmetry_candidates()`(전역 좌우 대칭, kind 보존)를 자동으로 돌려 48/51 소자의
    진짜 좌우 파트너를 찾는다(35/36 declared 일치, `M38`만 문서화된 예외).
    `headroom_role_candidates` 필드로 `headroom_role` 후보(`"mirror"`|`"cascode"`|
    `"tail"`|`"floating_current_source"`|`None`)도 반환한다 -- `_propose_headroom_
    roles()` 참고, 6가지 실패한 가설 끝에 37/37 declared 일치(2026-08-08, `M9a`류/
    `M63`류를 role 계층(`FLOATING_CURRENT_SOURCE`/`DIODE_REFERENCED_CASCODE`)에서부터
    분리한 뒤에야 성립).

    반환(있으면): `{"relations": find_verified_differential_and_mirror_relations()의
    최종 반환값, "promoted_inputs": [자동 승격된 gate net, 승격 순서대로, 중복 없음],
    "final_inputs": tuple(원래 inputs 중복제거 + promoted_inputs), "role_changes":
    [{"device", "before", "after"}, ...], "net_class_changes": [{"net", "before",
    "after"}, ...], "iterations": int(실행한 라운드 수), "stop_reason": "fixed_point"|
    "max_iterations_reached", "vertical_stack_id_candidates": {"groups": {device_name:
    proposed_id, ...}, "ambiguous_alternatives": {device_name: [candidate_group_name,
    ...], ...}}, "gm_id_role_candidates": {device_name: "balanced"|"matching", ...},
    "L_role_candidates": {device_name: {"L_role","confirmed_by_structural_symmetry",
    "symmetry_partner"}, ...}, "headroom_role_candidates": {device_name: "mirror"|
    "cascode"|"tail"|"floating_current_source"|None, ...}}`.
    `role_changes`/`net_class_changes`는 `device`/`net` 이름 순 정렬,
    `before`/`after`가 다른 것만 포함(`before`가 `None`이면 원래 미분류였다가 새로
    분류된 것)."""
    by_name = {t.name: t for t in transistors}

    def classify(cur_inputs):
        netclass, _idioms_mod = _import_analog_grammar("netclass", "idioms")
        if netclass is None:
            return None, None
        devs = _to_analog_grammar_devs(transistors)
        cls, imp, _assume = netclass.classify_nets(devs, cur_inputs, outputs, biases, feedbacks, clocks)
        role = netclass.assign_roles(devs, cls, imp)
        return cls, role

    base_inputs = tuple(dict.fromkeys(inputs))
    cur_inputs = base_inputs
    cls_before, role_before = classify(cur_inputs)
    if cls_before is None:
        return None

    promoted_inputs = []
    iterations = 0
    stop_reason = "fixed_point"
    while True:
        iterations += 1
        candidates = find_differential_pair_candidates(
            transistors, cur_inputs, outputs, feedbacks, biases, clocks)
        if candidates is None:
            return None
        new_nets = []
        known = set(cur_inputs)
        for c in candidates["candidates"]:
            for dev in c["devices"]:
                g = by_name[dev].gate
                if g not in known:
                    new_nets.append(g)
                    known.add(g)
        if not new_nets:
            break
        promoted_inputs.extend(new_nets)
        cur_inputs = cur_inputs + tuple(new_nets)
        if iterations >= max_iterations:
            stop_reason = "max_iterations_reached"
            break

    relations = find_verified_differential_and_mirror_relations(
        transistors, cur_inputs, outputs, feedbacks, biases, clocks)
    if relations is None:
        return None

    vertical_stack_id_candidates = _propose_vertical_stack_ids(
        transistors, relations, base_inputs, outputs, feedbacks, biases, clocks)
    gm_id_role_candidates = _propose_gm_id_roles(
        transistors, base_inputs, outputs, feedbacks, biases, clocks)
    L_role_candidates = _propose_L_roles(
        transistors, relations, base_inputs, outputs, feedbacks, biases, clocks)
    headroom_role_candidates = _propose_headroom_roles(
        transistors, gm_id_role_candidates, vertical_stack_id_candidates,
        L_role_candidates, base_inputs, outputs, feedbacks, biases, clocks)

    cls_after, role_after = classify(cur_inputs)

    role_changes = sorted(
        ({"device": name, "before": role_before.get(name), "after": after}
         for name, after in role_after.items() if role_before.get(name) != after),
        key=lambda r: r["device"])
    net_class_changes = sorted(
        ({"net": net, "before": cls_before.get(net), "after": cls_after.get(net)}
         for net in set(cls_before) | set(cls_after)
         if cls_before.get(net) != cls_after.get(net)),
        key=lambda r: r["net"])

    # 2026-08-13 -- 사용자 지시(two_stage_ota의 M3/M4/M5/M7 L 자유도 확장 논의 계기,
    # "mirror나 bias_replica는 매칭특성을 요구하니까" -- balanced 롤은 W_bounds 안
    # 아무 feasible값이나 골라 매칭을 전혀 보호하지 않는 반면 matching 롤은 명시적으로
    # strong inversion을 골라 매칭에 유리함, gm-id-methodology.md §7.1). L_role이
    # mirror든 bias_replica든(이 함수 스코프의 모든 소자가 결국 둘 중 하나로 분류됨,
    # `_propose_L_roles()` 참고) gm_id_role 제안값을 "matching"으로 통일한다.
    # ⚠️ `headroom_role_candidates`는 이미 위에서 원래(balanced/matching) 신호로 계산이
    # 끝난 뒤라 이 override와 무관하다 -- `_propose_headroom_roles()`의 "balanced"==tail
    # 판정 로직은 원본 `gm_id_role_candidates`를 그대로 썼으므로 안 깨진다(여기서 만드는
    # 건 최종 노출용 별도 dict일 뿐, 위 호출에 넘긴 원본은 그대로 둠).
    gm_id_role_candidates_final = {
        name: ("matching" if L_role_candidates and name in L_role_candidates else raw)
        for name, raw in (gm_id_role_candidates or {}).items()
    }

    # ⚠️ 2026-08-14(세션34, 사용자 지적) -- role_after 하나만으로 "이 소자가 active-load
    # 성격을 가진다"를 판정하면 M4류(current-mirror의 non-ref leg인데 gate net이 SIGNAL로
    # 분류돼 role이 AMPLIFYING으로 나오는 경우, netclass.assign_roles()의 단일-role 우선순위
    # 설계상 ACTIVE_LOAD 판정보다 AMP 판정이 항상 먼저 걸림)을 놓친다. `idioms.m_mirror()`가
    # 이제 `active_load_legs`/`ref_is_signal` 포트(role과 무관하게 imp/cls만으로 판정)로
    # 이 경우도 노출하고, `idioms.m_diffpair_branch_load()`(같은 세션 후속, `nmcnr_
    # amplifier`의 M108/M109 계기로 캐스코드 관통까지 지원)가 diffpair 두 branch의
    # 부하를 직접 idiom으로 찾으므로(`analog-grammar/assets/idioms.py` 동일 세션 수정),
    # 이 세 신호를 **`match_all()` 한 번**으로 전부 뽑는다(재계산 없음, `find_diffpair_
    # branch_load_partners()`/`find_differential_pair_candidates()` 별도 재호출 불필요 --
    # `m_diffpair_branch_load()`가 내부적으로 `m_diffpair()`를 재사용해 그 역할을 대체).
    active_load_leg_candidates = set()
    signal_referenced_mirror_legs = {}
    branch_load_partner_candidates = {}
    _netclass_al, _idioms_al = _import_analog_grammar("netclass", "idioms")
    if _netclass_al is not None:
        _devs_al = _to_analog_grammar_devs(transistors)
        _cls_al, _imp_al, _ = _netclass_al.classify_nets(_devs_al, cur_inputs, outputs, biases,
                                                            feedbacks, clocks)
        _by_name_al = {d["name"]: d for d in _devs_al}
        # 2026-08-15(세션35 후속, 사용자 지적 -- "신호경로인지는 analog-grammar를 쓰면
        # 알 수 있다") -- role_after==ACTIVE_LOAD만으로는 위상(레일 소스+HIGH_Z 드레인)
        # 사실만 보고, 그 드레인이 진짜 신호 경로인지 다른 바이어스 생성기가 읽어가는
        # 순수 DC 기준 노드(cls==BIAS)인지 구분 못 한다(idioms.m_mirror() 같은 세션 수정과
        # 동일 원칙 -- current_reuse_telescopic_ota의 M60/M61/M68 실측 계기, 드레인이
        # Vbias3/Vbias4/Vbias2로 전부 cls==BIAS).
        active_load_leg_candidates = {
            n for n, r in role_after.items()
            if r == _netclass_al.ACTIVE_LOAD
            and _cls_al.get(_by_name_al.get(n, {}).get("D")) != _netclass_al.BIAS
        }
        _matches_al = _idioms_al.match_all(_devs_al, _cls_al, _imp_al, role_after)
        for m in _matches_al:
            if m.kind == "current-mirror":
                active_load_leg_candidates.update(m.ports.get("active_load_legs", []))
                ref = m.ports.get("ref")
                if ref is not None and m.ports.get("ref_is_signal"):
                    for leg in m.devices:
                        if leg != ref:
                            signal_referenced_mirror_legs[leg] = ref
            elif m.kind == "diffpair-branch-load":
                la, lb = m.devices
                branch_load_partner_candidates[la] = lb
                branch_load_partner_candidates[lb] = la

    return {"relations": relations, "promoted_inputs": promoted_inputs,
            "final_inputs": cur_inputs, "role_changes": role_changes,
            "net_class_changes": net_class_changes, "iterations": iterations,
            "stop_reason": stop_reason,
            "vertical_stack_id_candidates": vertical_stack_id_candidates,
            "gm_id_role_candidates": gm_id_role_candidates_final,
            "L_role_candidates": L_role_candidates,
            "headroom_role_candidates": headroom_role_candidates,
            "role_candidates": role_after,
            "branch_load_partner_candidates": branch_load_partner_candidates,
            "active_load_leg_candidates": active_load_leg_candidates,
            "signal_referenced_mirror_legs": signal_referenced_mirror_legs}


@dataclass
class SymmetryDispositionsVerdict:
    ok: bool
    case_collisions: dict
    undisposed: list


def check_symmetry_dispositions(transistors: list, matching_pairs: list,
                                  dispositions: dict | None = None) -> SymmetryDispositionsVerdict:
    """`find_matching_candidates()`/`find_hub_merge_candidates()`는 **후보**만 낸다 — "이
    회로 기능상 진짜 matching/병합인가"는 항상 판단(설계자/AI)이 남아 있는데, 그 판단이
    조용히 누락(후보를 발견하고도 topology JSON `symmetry.matching_pairs`에 채택도, 명시적
    기각도 안 하고 그냥 빼먹는 것)되는 걸 이 함수가 구조적으로 차단한다. `run_full_circuit_
    audit()`의 3번 체크("every matching/hub-merge candidate has a recorded disposition")와
    정확히 같은 원리를 topology-authoring 단계(사이징 이전, `devices`/`expected_counts` 같은
    무거운 인자 없이)에 맞게 경량화한 것이다.

    ⚠️ **2026-07-28 수정: `hub_merge` 후보 체크 추가** — 최초 버전은
    `find_matching_candidates()`(current_mirror/diff_pair)만 확인하고
    `find_hub_merge_candidates()`는 아예 호출하지 않았다(함수 중복 감사 중 `run_full_circuit_
    audit()`의 3번 체크와 대조하다 발견) — 사고1(`find_hub_merge_candidates()`를 stage
    경계를 넘어 돌리지 않음)과 같은 종류의 누락이 topology-authoring 단계에서 재발할 수
    있는 gap이었다. 지금은 세 tag(`current_mirror`/`diff_pair`/`hub_merge`) 전부 검사한다.

    **입력**:
    - `transistors`: `load_topology()`가 반환한 것 그대로(connectivity만 있어도 된다 —
      2026-07-28 수정으로 `find_matching_candidates()`가 W 없이도 후보를 낸다).
    - `matching_pairs`: topology JSON `symmetry.matching_pairs`와 같은 형식
      (`[{"names": [...], "kind": ...}, ...]`) — **채택된** 쌍/그룹.
    - `dispositions`(선택): `{(tag, kind, key): (category, reason)}` — **기각된** 후보의
      사유. `tag`는 `"current_mirror"`/`"diff_pair"`(`find_matching_candidates()`,
      current_mirror는 gate net, diff_pair는 source net) 또는 `"hub_merge"`
      (`find_hub_merge_candidates()`, key는 공유 hub net) 중 하나. `category`는 `real_match_
      already_covered` 또는 `false_positive_{coincidental|diode_chain|
      consumer_reads_bias|feedback_loop}` 등을 권장하지만 문자열 값 자체는 검사하지 않는다
      — **키가 존재하는지만** 검사한다(`run_full_circuit_audit()`와 동일 계약, tag를 절대
      섞지 말 것도 동일 — 같은 (kind,net)이 우연히 두 함수 모두에서 나올 수 있다).

    **판정 순서(고정, 둘 다 실행)**:
    0. **net 이름 대소문자 자기모순 스캔이 먼저다** — `run_full_circuit_audit()` 2번 체크와
       똑같은 검사를 여기서도 한다(실제 사고: `design-report-spec.md` §1.5 사고9 — 서로 다른
       스크립트/세션이 같은 물리 net을 `Vbias1`/`vbias1`로 다르게 명명해서 매칭이 가려짐.
       `linked_topology_files`로 여러 파일을 합칠 때 이 사고가 가장 재발하기 쉽다 — 파일마다
       작성 시점/작성자가 다를 수 있기 때문). 대소문자 차이만 나는 net이 하나라도 있으면
       **그 자체로 `ok=False`** — 대소문자가 다르면 `find_matching_candidates()`가 같은
       net을 다른 net으로 착각해 후보 자체를 못 찾고, 그러면 아래 1번 판정도 신뢰할 수 없기
       때문이다(자동으로 소문자 통일하는 식으로 조용히 고치지 않는다 — 원본 어느 쪽이
       오타인지 판단은 여전히 사람/AI 몫이다).
    1. `find_matching_candidates()`(current_mirror/diff_pair)와
       `find_hub_merge_candidates()`(hub_merge)가 찾은 그룹마다, 그 그룹의 소자 이름 전체가
       `matching_pairs`의 어느 한 항목에 (부분집합으로) 포함돼 있으면 "채택됨"으로 통과.
       아니면 `dispositions`에 해당 `(tag, kind, key)`가 기록돼 있어야 통과. 둘 다 아니면
       `undisposed`에 남는다.

    **`ok=False`면(0번이든 1번이든) 이 topology JSON을 저장하지 말 것.**

    반환: `SymmetryDispositionsVerdict(ok, case_collisions, undisposed)` —
    `case_collisions`는 `{net_lower: {실제 표기, ...}, ...}`,
    `undisposed`는 `[(tag, kind, key, [names...]), ...]`."""
    dispositions = dispositions or {}

    all_nets = (net for t in transistors for net in (t.source, t.drain, t.gate) if net is not None)
    case_collisions = _scan_case_collisions(all_nets)

    matching_candidates = find_matching_candidates(transistors)
    hub_candidates = find_hub_merge_candidates(transistors)
    found_groups = []
    for tag in ("current_mirror", "diff_pair"):
        for key, group in matching_candidates[tag].items():
            found_groups.append((tag,) + key + (group,))
    for key, group in hub_candidates.items():
        found_groups.append(("hub_merge",) + key + (group,))

    undisposed = []
    for *tag_and_key, group in found_groups:
        names = frozenset(t.name for t in group)
        covered = any(names <= frozenset(p["names"]) for p in matching_pairs)
        if covered:
            continue
        if tuple(tag_and_key) in dispositions:
            continue
        undisposed.append(tuple(tag_and_key) + (sorted(names),))

    ok = len(case_collisions) == 0 and len(undisposed) == 0
    return SymmetryDispositionsVerdict(ok=ok, case_collisions=case_collisions, undisposed=undisposed)


# ---------------------------------------------------------------------------
# 1.75) Stage 경계를 넘는 stack 병합 후보 탐지 — "stack = stage"라는 가정 자체가 틀렸다
#       (2026-07-24, Maloberti PDF p.29 "Layout Oriented Design" 재확인). 이 슬라이드의
#       M3/M4(1단 PMOS 부하)+M6(2단 PMOS gain) 예시가 보여주듯, 물리 행(stack) 배정은
#       "같은 stage인가"가 아니라 "같은 극성 + 하나의 공유 net(hub)을 갖는가 + 그 병합이
#       실제로 한붓그리기 되는가"로 결정해야 한다. 이 절은 그 판단을 위한 두 도구를 제공한다.
# ---------------------------------------------------------------------------

def find_hub_merge_candidates(transistors: list) -> dict:
    """`stack_id`/stage 배정을 무시하고, 극성 + 공유 단자(source 또는 drain) 하나만으로
    "이 소자들을 한 물리 행으로 합칠 수 있을까"의 **후보**를 전체 회로에서 찾는다.

    `find_matching_candidates()`가 "matching이 필요한 쌍"을 찾는 것과 달리, 이 함수는
    "matching과 무관하게 같은 diffusion에 물릴 수 있는 후보"를 찾는다 — 서로 다른 stage에
    속한, matching 관계도 전혀 아닌 소자들(예: 1단 부하 M3/M4와 2단 gain 소자 M6)도
    **같은 hub net(예: vdd)을 공유하기만 하면** 후보로 잡힌다. `stack_id`는 무시하고
    `source`/`drain` 필드만 본다 — 이 함수를 쓸 때는 각 소자에 stack_id를 미리 강제하지
    않는 편이 좋다(이미 넣었다면 무시되니 상관없지만, "stage별로 분리하겠다"는 선입견을
    갖고 stack_id부터 정하면 애초에 병합 후보 자체가 안 보인다).

    반환: `{(kind, hub_net): [Transistor, ...], ...}` — 크기 2 이상인 후보만.

    ⚠️ 이 함수가 찾은 후보는 "같은 net을 공유한다"는 사실만 확인한 것이지, 실제로
    **한붓그리기가 되는지는 검증하지 않는다** — 반드시 `build_graph()`+`check_euler_condition()`
    (또는 아래 `check_multi_leaf_hub_parity()`로 먼저 빠르게 스크리닝한 뒤)으로 직접
    검증할 것. 후보 중에는 leaf가 3개 이상이라 홀수 finger 조합에서 불가능한 경우가
    실제로 있다(아래 `check_multi_leaf_hub_parity()` 참고)."""
    by_net = defaultdict(list)
    for t in transistors:
        by_net[(t.kind, "source", t.source)].append(t)
        by_net[(t.kind, "drain", t.drain)].append(t)
    return {(kind, net): group for (kind, _role, net), group in by_net.items() if len(group) >= 2}


# ---------------------------------------------------------------------------
# 1.8) 전역 구조 대칭(좌우 미러/상하 극성쌍) 탐지 — find_matching_candidates()/
#      find_hub_merge_candidates()는 "같은 net 하나를 공유하는 소자쌍"(국소 신호)만 찾는다.
#      current_reuse_telescopic_ota에서 M8<->M17(공유 노드 없음, 각자 다른 net에 물림)처럼
#      "netlist 전체를 어떤 net 재라벨링으로 자기 자신에 사상하는가"(전역 구조, graph
#      automorphism)는 이 국소 탐지로 원천적으로 못 찾는다 -- 2026-08 세션6 신설.
# ---------------------------------------------------------------------------

@dataclass
class StructuralSymmetryVerdict:
    net_map: dict     # net -> 대응 net (양방향 self-consistent)
    device_map: dict  # device name -> 대응 device name(자기 자신이면 그 transform에서 자기-대칭)
    conflicts: list    # [(device, terminal, net, expected, actual), ...] -- 전파 중 모순 발견
    unresolved: list   # 끝까지 유일한 파트너를 못 찾은 소자 이름(사람 판정 필요, 실패 아님)
    low_confidence_pairs: list  # [frozenset({a,b}), ...] -- 단자 1개(len(known)<2)짜리 약한
                                 # 근거로만 확정된 쌍 -- 우연의 일치일 위험이 있어 사람이 반드시
                                 # 재검토해야 한다(2026-08 세션6, dual transform 오탐 실측 계기)


def find_structural_symmetry_candidates(transistors: list, seed_net_pairs: dict,
                                         transform: str = "mirror") -> StructuralSymmetryVerdict:
    """전역 구조 대칭 후보를 `seed_net_pairs`(이미 아는 net 대응 — 보통 differential I/O
    포트나 vdd/gnd)에서 시작해 고정점까지 전파해 찾는다. `propagate_topology_forced_
    currents()`(A엔진, KCL 버전)와 정확히 같은 스타일의 반복 전파를 net/device 대응에
    적용한 것 — 오늘 current_reuse_telescopic_ota에서 M8<->M17, M13<->M22, M11a-chain<->
    M20a-chain 같은 대응관계를 손으로 하나씩 재발견했던 작업을 이 함수 하나로 대체한다.

    두 가지 `transform`:
    - `"mirror"`(좌우 대칭, 예: Vom블록<->Vop블록): kind가 **보존**된다(pmos->pmos).
      vdd/gnd처럼 공통 rail은 `seed_net_pairs`에 자기 자신으로(`{"vdd":"vdd",...}`) 넣고,
      Vip<->Vim/Vop<->Vom처럼 진짜 좌우로 바뀌는 differential net만 서로 다른 값으로 넣는다.
    - `"dual"`(상하/극성 대칭, 예: PMOS 다이오드스택<->NMOS 다이오드스택): kind가 **반전**된다
      (pmos<->nmos). vdd<->gnd를 서로 다른 값으로 넣는 게 유일하게 항상 확실한 seed다 —
      그 외 공용 net(Vbias1..4 등)이 PMOS 전용/NMOS 전용 레퍼런스로 갈라져 있으면(이 회로의
      Vbias1↔Vbias4처럼) 그 대응도 seed로 넣어야 전파가 그 지점까지 도달한다 -- **이 함수는
      seed 없이 스스로 축을 추측하지 않는다**(다른 find_*_candidates()와 같은 계약).

    알고리즘(고정점 반복):
    1. 아직 안 풀린 소자 중 최소 1개 단자(source/drain/gate)라도 이미 `net_map`에 있는
       소자를 훑는다.
    2. 그 소자의 "기대 파트너"(kind는 transform에 따라 보존/반전, **이미 알려진** 단자만
       사상값으로 제약, 아직 모르는 단자는 와일드카드)와 일치하는 소자를 netlist 전체에서
       찾는다.
    3. **정확히 하나**면 채택(`device_map`에 기록, 자기 자신이 유일한 후보면 그 transform
       에서 자기-대칭으로 기록) -- 그 파트너와의 나머지(아직 `net_map`에 없는) 단자쌍을
       새 net 대응으로 추가한다. 이미 있는 net 대응과 값이 다르면(모순) `conflicts`에
       기록하고 덮어쓰지 않는다(추측으로 채우지 않음). 0개나 2개 이상이면 이번 라운드는
       보류(다음 라운드에 제약이 더 채워지면 풀릴 수 있다).
    4. 더 이상 새로 배정되는 게 없을 때까지 반복.

    **라운드 내 처리 순서(2026-08 세션6 정정)**: 한 라운드 안에서 여러 소자가 동시에
    풀릴 수 있게 되면, **알려진 단자 개수(len(known))가 많은(=더 확실한) 소자부터** 매칭을
    확정한다 -- current_reuse_telescopic_ota의 `"dual"` transform 실측에서 이 순서를
    안 지키면 오탐이 났다: M9a(단자 1개, drain=Vop1만 앎)가 M2b/M3b(단자 2개 이상으로
    이미 확실히 풀리는 진짜 쌍)보다 먼저 후보 풀을 보면, 아직 안 나간 M3b까지 후보에
    남아있어 모호하게 남는 게 정상인데, 처리 순서가 뒤집히면 M3b가 먼저 소비되고 M9a가
    "우연히 마지막 남은 M10과만 매칭"돼버린다(둘 다 진짜 dual 짝이 없는데도). 단자 1개
    짜리 근거는 원천적으로 우연의 일치(coincidental) 위험이 있으므로, `low_confidence_
    pairs`에 별도로 표시해 사람이 반드시 재검토하게 한다(device_map에는 그대로 들어가되
    "확정"과 같은 신뢰도로 취급하지 말 것).

    끝까지 유일한 파트너를 못 찾은 소자는 `unresolved`에 남는다 -- **이건 실패가 아니라
    사람 판정이 필요하다는 신호**다(예: M6/M7처럼 원래 비대칭으로 설계된 소자가 여기 남는
    것이 정상 -- 조용히 추측해서 채우지 않는다)."""
    if transform not in ("mirror", "dual"):
        raise ValueError(f"알 수 없는 transform: {transform!r} -- 'mirror' 또는 'dual'이어야 한다")

    def expected_kind(k):
        if transform == "mirror":
            return k
        return "nmos" if k == "pmos" else "pmos"

    net_map = dict(seed_net_pairs)
    device_map: dict = {}
    conflicts: list = []
    low_confidence_pairs: list = []

    changed = True
    while changed:
        changed = False
        pending = []
        for t in transistors:
            if t.name in device_map:
                continue
            known = {}
            if t.source in net_map:
                known["source"] = net_map[t.source]
            if t.drain in net_map:
                known["drain"] = net_map[t.drain]
            if t.gate is not None and t.gate in net_map:
                known["gate"] = net_map[t.gate]
            if known:
                pending.append((t, known))
        # 단자 개수 많은(확실한) 소자부터 -- 위 docstring 참고. 동점이면 이름순(재현성).
        pending.sort(key=lambda item: (-len(item[1]), item[0].name))

        for t, known in pending:
            if t.name in device_map:
                continue  # 이번 라운드 안에서 이미 다른 매칭에 의해 소비됐다.
            tgt_kind = expected_kind(t.kind)
            candidates = [
                u for u in transistors
                if u.kind == tgt_kind and u.name not in device_map
                and ("source" not in known or u.source == known["source"])
                and ("drain" not in known or u.drain == known["drain"])
                and ("gate" not in known or u.gate == known["gate"])]
            if len(candidates) != 1:
                continue  # 0개(아직 파트너가 안 풀림) 또는 2개 이상(모호) -- 보류.

            partner = candidates[0]
            device_map[t.name] = partner.name
            device_map[partner.name] = t.name
            if len(known) < 2 and partner.name != t.name:
                low_confidence_pairs.append(frozenset((t.name, partner.name)))
            changed = True
            for attr in ("source", "drain", "gate"):
                tv, pv = getattr(t, attr), getattr(partner, attr)
                if tv is None or pv is None:
                    continue
                if tv not in net_map:
                    net_map[tv] = pv
                    net_map.setdefault(pv, tv)
                    changed = True
                elif net_map[tv] != pv:
                    conflicts.append((t.name, attr, tv, net_map[tv], pv))

    unresolved = sorted(t.name for t in transistors if t.name not in device_map)
    return StructuralSymmetryVerdict(net_map=net_map, device_map=device_map,
                                      conflicts=conflicts, unresolved=unresolved,
                                      low_confidence_pairs=low_confidence_pairs)


@dataclass
class MultiLeafHubParityVerdict:
    ok: bool
    kind: str
    m_odd_leaves: int


def check_multi_leaf_hub_parity(n_fingers_by_leaf: dict) -> MultiLeafHubParityVerdict:
    """hub 하나에 leaf가 N개(N≥2) 달린 구조(각 leaf = 서로 다른 소자 하나, 그 소자의
    finger 개수가 `n_fingers_by_leaf`)가 **finger 개수를 그대로 실현했을 때** 한붓그리기
    가능한지를 그래프를 만들지 않고 공식으로 빠르게 판정한다(설계 공간 탐색 시 여러 k
    후보를 빠르게 스크리닝하는 용도 — 최종 채택 전에는 반드시 `build_graph()`+
    `check_euler_condition()`으로 재확인할 것, 이 함수는 그 결과와 항상 일치함을 self-test로
    직접 검증했다).

    **일반 규칙(직접 유도 + `build_graph`/`check_euler_condition`으로 재확인됨)**: hub 차수는
    모든 leaf의 finger 합, 각 leaf 차수는 그 소자의 finger 개수다. 홀수 finger를 가진
    leaf의 개수를 m이라 하면:
    - m == 0: 전부 짝수 → 홀수차수 노드 0개 → **closed circuit** (항상 가능)
    - m in (1, 2): 홀수차수 노드가 정확히 2개(leaf에서 m개, hub는 m의 홀짝을 따라가며
      m과 합쳐 항상 정확히 2로 맞춰짐) → **open path** (항상 가능)
    - m >= 3: 홀수차수 노드가 4개 이상 → **한붓그리기 불가능** (leaf 개수 N과 무관하게
      항상 실패)

    2개-leaf hub(이 세션에서 지금까지 다룬 전류거울/차동쌍 형태)는 m이 최대 2라 이 제약에
    걸릴 일이 없었다 — 이 문제가 실제로 드러나는 건 Maloberti p.29처럼 **leaf가 3개 이상인
    병합 stack**을 만들 때뿐이다: 그런 stack은 **최소 (N-2)개의 leaf가 짝수 finger**여야
    한다(m<=2 유지). 특히 모든 leaf가 같은 finger 개수 k를 쓰는 경우(§8 box-shape처럼
    "공통 finger 수"를 원하는 상황), N>=3이면 k는 반드시 짝수여야 한다 — k가 홀수면
    m=N>=3이 되어 항상 실패한다.

    반환: `MultiLeafHubParityVerdict(ok, kind, m_odd_leaves)` — `kind`는
    `"circuit"|"path"|"impossible"`.
    """
    m = sum(1 for k in n_fingers_by_leaf.values() if k % 2 == 1)
    if m == 0:
        return MultiLeafHubParityVerdict(ok=True, kind="circuit", m_odd_leaves=m)
    if m <= 2:
        return MultiLeafHubParityVerdict(ok=True, kind="path", m_odd_leaves=m)
    return MultiLeafHubParityVerdict(ok=False, kind="impossible", m_odd_leaves=m)


# ---------------------------------------------------------------------------
# 1.8) A/C 엔진 — 위상-강제 전류 전파 / diode-stack 탐지
#      (§7.3.2, 배치 7-3, 2026-07-31 — `analog-topology-json-library.do.md` 참고)
#      LUT가 필요 없는 순수 그래프 연산만 여기 둔다. LUT가 필요한 나머지 절반(B엔진
#      `solve_id_for_target_gm()`, C엔진의 실제 전류 역산 `solve_diode_stack_current()`,
#      F엔진 `metrics` 레지스트리)은 sizing_recipe.py에 있다.
# ---------------------------------------------------------------------------

def propagate_topology_forced_currents(netlist: list, seed_currents: dict,
                                        mirror_ratios: dict) -> dict:
    """A엔진(§7.3.2) — 위상(그래프 구조)만으로 100% 결정되는 전류를 두 가지 전파 규칙으로
    고정점(fixed-point)까지 반복 전파한다:

    1. **직렬 스택**(같은 `Transistor.stack_id`): 물리적으로 하나의 전류경로이므로 KCL상
       전부 같은 ID를 갖는다 — 한 소자라도 전류가 알려지면 같은 stack의 나머지 전부에
       그대로 퍼진다.
    2. **미러비**(`mirror_ratios: {(ref_name, mirror_name): ratio}`) — `ref`의 전류가
       알려지면 `mirror`의 전류 = `ref.ID * ratio`(반대 방향도 `ratio`가 0이 아니면 성립).
       `ratio`는 보통 `find_matching_candidates()`가 찾아낸 `current_mirror` 쌍의 W비에서
       얻는다.

    반환: `{device_name: ID}` — `seed_currents`에 두 규칙을 반복 적용해 확정된 전류 전부
    (seed 자체도 포함해 그대로 돌려준다).

    ⚠️ 정직한 한계(2026-07-31): 3개 이상 branch가 한 노드에서 만나 미지수 하나를 자동으로
    푸는 일반 KCL solver는 포함하지 않는다 — `analog-topology-json-library.do.md` §7.3.1이
    실측 분류한 45개 A유형 소자는 전부 위 두 규칙(직렬 스택 + 미러비)만으로 설명된다
    ("M6·M7 전류 총합"도 M1a/M4a와의 직렬 관계로 커버됨, `bias-gen 9개`도 미러/스택 KCL로만
    파생). 다중 branch 합류 노드의 일반 KCL 해석은 이 배치의 실측 범위 밖이다 — 그런 A유형
    소자가 실제로 나타나는 회로가 생기면 그때 확장한다."""
    ids = dict(seed_currents)
    stacks: dict = defaultdict(list)
    for t in netlist:
        if t.stack_id is not None:
            stacks[t.stack_id].append(t.name)

    changed = True
    while changed:
        changed = False
        for members in stacks.values():
            known = {ids[n] for n in members if n in ids}
            if not known:
                continue
            if len(known) > 1:
                raise ValueError(
                    f"직렬 스택 {members}에 서로 다른 seed 전류가 섞여 있다: {sorted(known)} -- "
                    "같은 물리적 전류경로는 반드시 하나의 ID만 가져야 한다(KCL 위반)")
            val = next(iter(known))
            for n in members:
                if n not in ids:
                    ids[n] = val
                    changed = True
        for (a, b), ratio in mirror_ratios.items():
            if a in ids and b not in ids:
                ids[b] = ids[a] * ratio
                changed = True
            elif b in ids and a not in ids and ratio != 0:
                ids[a] = ids[b] / ratio
                changed = True
    return ids


@dataclass
class DiodeStackMember:
    name: str
    position: int          # 스택(netlist 순서) 내 위치
    gate_refers_to: str    # 이 소자의 gate와 같은 net을 drain으로 갖는 소자 이름
                            # (자기 자신이면 self-diode, 다른 이름이면 이웃-diode)


@dataclass
class DiodeStack:
    stack_id: str
    members: list  # list[DiodeStackMember] — diode-connected로 판정된 소자만(스택 전부 아님)


def find_diode_stacks(netlist: list) -> list:
    """C엔진(§7.3.2) — `find_diode_loops()`(자기 자신의 gate==drain만 보는 구식 자기참조
    체크)를 대체. **2026-07-30 정정 근거**: M57은 게이트가 자기 자신의 drain에 물려 self-diode로
    잡히지만, M58은 게이트가 **M57의** drain에 물려 있어 자기참조 체크로는 놓친다 — 그래서
    "같은 물리적 스택(`stack_id`) 안에서, 각 소자의 gate가 그 스택 위 **어떤 소자의
    drain과든**(자기 것이든 이웃 것이든) 같은 net인지"를 보는 그래프 워크로 재정의했다.

    반환: `list[DiodeStack]` — diode-connected 소자가 하나도 없는 stack은 결과에서 제외.
    `find_hub_merge_candidates()`/`find_matching_candidates()`가 앞으로 이 결과를 재사용해
    diode-stack 내부 노드를 hub-merge/current_mirror 오탐에서 사전에 걸러낼 수 있다
    (§7.3.2 콜아웃 참고, 이 배치의 스코프는 아님)."""
    by_stack: dict = defaultdict(list)
    for t in netlist:
        if t.stack_id is not None:
            by_stack[t.stack_id].append(t)

    stacks = []
    for stack_id, members in by_stack.items():
        drain_owner = {}
        for t in members:
            drain_owner.setdefault(t.drain, t.name)
        diode_members = []
        for pos, t in enumerate(members):
            owner = drain_owner.get(t.gate)
            if owner is not None:
                diode_members.append(DiodeStackMember(name=t.name, position=pos, gate_refers_to=owner))
        if diode_members:
            stacks.append(DiodeStack(stack_id=stack_id, members=diode_members))
    return stacks


# ---------------------------------------------------------------------------
# 2) Stack 분할 — 기본 휴리스틱은 (극성, finger 폭)만 본다
# ---------------------------------------------------------------------------

def split_into_stacks(transistors: list[Transistor]) -> dict:
    """트랜지스터 리스트를 stack_id -> [Transistor,...]로 분할한다.

    우선순위:
    1. `stack_id`를 명시한 트랜지스터는 그 값을 그대로 stack key로 쓴다 — 대칭성/matching 때문에
       특정 소자들을 강제로 묶고 싶을 때 이렇게 지정한다(예: folded cascode 상단 그룹
       MP/M3/M4/M5/M6을 하나의 stack_id로 묶는 것은 회로 지식이 필요한 판단이라 이 함수가 대신
       결정하지 않는다).
    2. `stack_id`가 없으면 (kind, finger_w) 조합을 key로 자동 그룹핑한다 — 같은 diffusion
       strip에 물리려면 최소한 극성과 finger 폭이 같아야 하기 때문(Maloberti p.25 "Use ~same
       finger count per stack"의 필요조건만 기계적으로 강제한 것).
    3. finger_w도 없으면 (kind, 'unspecified')로 묶는다 — 이 경우 실제로 같은 stack에 넣을 수
       있는지는 호출자가 직접 확인해야 한다(경고 없이 넘어가지 않도록 결과에 표시됨).
    """
    stacks: dict = defaultdict(list)
    for t in transistors:
        if t.stack_id is not None:
            key = t.stack_id
        else:
            width_key = round(t.finger_w, 6) if t.finger_w is not None else "unspecified"
            key = (t.kind, width_key)
        stacks[key].append(t)
    return dict(stacks)


_RAIL_NETS = frozenset({"vdd", "gnd", "vss"})


def shares_diffusion_node(ra: "Transistor", rb: "Transistor") -> bool:
    """L1 축B(2026-08-05, 세션10 L1/L2 구현) — 두 소자가 source/drain(어느 조합이든)을
    직접 공유해 물리적으로 같은 diffusion을 연장할 수 있는가. **gate는 포함하지 않는다**
    — gate 공유는 "같은 바이어스를 읽는다"는 것일 뿐 diffusion 연장과 무관하다(세션8에서
    M106/M107이 gate=VB3를 공유해서 이걸 착각한 적이 한 번 있었다, 실측 중 발견해 고침).

    `audit_row_split()`이 이미 **선언된** matching pair 하나의 interdig/centroid 정책을
    정할 때만 쓴다 — rail(vdd/gnd) 공유도 유효한 근거로 인정한다(예: 둘 다 source=vdd인
    전류거울 쌍은 실제로 인접 배치 가능하고, §2.7이 이미 이런 쌍의 interdigitation을
    검증했다). 이건 `geometry_colocation_union()`(세션22부터 matching_pairs 기반 +
    검증된 stacked-composite 확장만 쓴다, 아래 참고)과는 **다른 목적의 다른 판단**이니
    헷갈리지 말 것 — 여기는 이미 확정된 쌍 하나만 보므로 무근거 그룹 확장 위험이 없다."""
    na = {ra.source, ra.drain} - {None}
    nb = {rb.source, rb.drain} - {None}
    return bool(na & nb)


def kcl_series_union(netlist: list, matching_pairs: list) -> dict:
    """L2 축A(2026-08-05, 세션10 L1/L2 구현) — `derive_stack_groups()`를 KCL용/geometry용
    두 함수로 분리한 것 중 KCL(축A, `sizing_recipe.py`의 `stack_groups_kcl`) 쪽. 두 규칙으로
    union-find 병합한다:

    1. **내부 노드(2단자 net, 레일 제외)**: 어떤 net이 **레일(vdd/gnd/vss)이 아니고**
       정확히 2개의 소자 단자에만 연결되면, 전하보존으로 그 두 소자 전류가 반드시 같다 —
       극성과 무관한 물리 법칙(예: `folded_cascode`의 `M106`(nmos)/`M108`(pmos)이
       `NodeM1`을 공유하면 극성이 달라도 KCL로 전류가 같다). **레일 제외는 세션9에서
       추가됨**: `two_stage_ota`처럼 소자 수가 적은 회로에서는 `gnd`/`vdd`가 우연히 정확히
       2번만 쓰일 수 있는데(실제 사례: `M5/M7`이 둘 다 `gnd`를 쓰는 게 우연히 2건이라 이
       규칙이 거짓 KCL 관계를 만들었다, 사용자가 회로 역할로 정정) — 레일은 외부 전원으로
       무한히 전류를 흘릴 수 있어 "2단자=닫힌 계=전하보존" 논리가 성립하지 않는다. 4개
       회로 전부 실측(레일 단자 수 3~16개)으로 이 배제가 기존 KCL 판정에 회귀를 주지
       않음을 확인했다(세션9/10).
    2. **선언된 `matching_pairs`**: 호출자가 이미 `current_forced=true`로 거른 쌍만
       넘겨준다는 계약(L1) — 이 함수 자체는 어떤 쌍이 오든 그대로 병합한다.

    반환: `{stack_id: [소자명,...]}` — `stack_id`는 그 그룹의 netlist상 최초 등장 소자
    이름(입력 순서에만 의존하는 결정론적 값)."""
    net_uses: dict = defaultdict(list)
    for t in netlist:
        net_uses[t.source].append(t.name)
        net_uses[t.drain].append(t.name)

    parent = {t.name: t.name for t in netlist}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for net, uses in net_uses.items():
        if net in _RAIL_NETS:
            continue
        if len(uses) == 2 and uses[0] != uses[1]:
            union(uses[0], uses[1])
    for names in matching_pairs:
        for a, b in zip(names, names[1:]):
            union(a, b)

    order = {t.name: i for i, t in enumerate(netlist)}
    groups: dict = defaultdict(list)
    for t in netlist:
        groups[find(t.name)].append(t.name)

    result = {}
    for members in groups.values():
        members_sorted = sorted(members, key=lambda n: order[n])
        result[members_sorted[0]] = members_sorted
    return result


def geometry_colocation_union(netlist: list, matching_pairs: list) -> dict:
    """L2 축B(세션22 전면 재설계) — `derive_stack_groups()`를 분리한 것 중 geometry(축B,
    `sizing_recipe.py`의 `stack_groups_geometry`, `assign_finger_geometry()`의 finger_w
    공유 단위) 쪽. `kcl_series_union()`(현재 전류 propagation용, 이 함수와 목적이 다르므로
    별개로 유지)과는 이제 union 규칙 자체가 다르다.

    ⚠️ 세션22 재설계 배경(`.ai/context.md` 세션22 참고) — 옛 버전(2026-08-05, 세션10)은
    "같은 극성 + non-rail + drain=source"면 **선언 여부와 무관하게** 자동 병합했다. 이
    규칙이 `current_reuse_telescopic_ota`의 `Vx` 노드(stage-1 tail/diff-pair 공유
    노드)에 `M58`(bias-gen 하우스키핑 소자, source=Vx)이 얹혀있다는 이유만으로 전류
    규모가 수십~수백 배 다른 `M57/M58`을 `M6/M7/M1a/M1b/M2a/M2b`와 한 finger-공유
    stack으로 묶어 `assign_finger_geometry()`가 공통 finger_w를 못 찾고 크래시하는
    실제 사고로 이어졌다. 사용자 확정 설계: **matching_pairs가 그룹의 유일한 근거이고
    (base), 물리적 직렬 스택 관계는 그 base 위에 "레이아웃 최적화를 위해 추가로
    묶을 수 있는 후보"로만 확장한다** — KCL(같은 전류)과 geometry(같은 finger_w)가
    다른 질문이라는 원칙(세션10)은 유지하되, geometry 쪽의 "자동 발견"을 무근거
    connectivity 추측 대신 이미 검증된 `find_stacked_matching_candidates()`(세션19
    C-3, 복합소자 상속 — declared matching pair 위에 **직접 stacked**된(같은 극성,
    `drain=source`) 소자를 재귀적으로 찾는다)로 교체한다.

    1. **base**: `matching_pairs`(호출자가 `current_forced=true`로 거른 쌍만 넘긴다는
       계약은 그대로 — `current_mirror`/`branch_symmetric`류 순수 문서용 선언은 여전히
       제외)를 그대로 union한다.
    2. **확장**: `find_stack_edges()`(analog-grammar 재사용, 없으면 soft-fail로 확장
       생략) + `find_stacked_matching_candidates()`로 각 base pair 위에 재귀적으로
       쌓인 소자를 찾아 같은 그룹으로 union한다. 이 상속은 **base pair의 대표 소자
       바로 위에 직렬로 얹힌, 같은 kind인 소자**만 좇아가므로(M1a→M2a처럼), `M58`처럼
       "같은 노드를 소스로 공유하는 병렬 소비자"(M1a/M1b의 **형제**이지 위에 얹힌 게
       아님)는 애초에 후보에 안 들어온다 — 별도 예외처리 없이 알고리즘 자체가 걸러낸다.
    3. matching_pairs에도 없고 어떤 base 위에도 안 얹힌 소자(M6/M7/M57/M58류)는
       각자 독립 그룹(finger_w를 자유롭게 고를 수 있음)으로 남는다 — 이게 정답이다,
       레이아웃 압축을 위해 finger_w를 공유해야 할 전기적 근거가 없다.

    반환 형태는 `kcl_series_union()`과 동일."""
    parent = {t.name: t.name for t in netlist}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    base_pairs = []
    for names in matching_pairs:
        for a, b in zip(names, names[1:]):
            union(a, b)
            base_pairs.append((a, b))

    stack_edges = find_stack_edges(netlist)
    if stack_edges:
        for (_kind, a, b), members in find_stacked_matching_candidates(
                netlist, base_pairs, stack_edges).items():
            union(a, members[0].name)
            union(b, members[1].name)

    order = {t.name: i for i, t in enumerate(netlist)}
    groups: dict = defaultdict(list)
    for t in netlist:
        groups[find(t.name)].append(t.name)

    result = {}
    for members in groups.values():
        members_sorted = sorted(members, key=lambda n: order[n])
        result[members_sorted[0]] = members_sorted
    return result


def _kcl_and_matching_edges(transistors: list, matching_pairs: list) -> list:
    """`kcl_series_union()`이 union할 때 실제로 쓰는 것과 똑같은 두 종류의 edge(내부
    2단자 net + declared `current_forced` matching_pairs)를 `(a, b, kind, detail)`
    리스트로 재구성한다 -- `audit_vertical_stack_id_vs_kcl()`과
    `propose_vertical_stack_id_gap_fill()` 둘 다 같은 edge 정의를 써야 서로 어긋나지
    않으므로(2026-08-13 세션31, N-way 조인트 스캔 때 만든 `_shared_current_groups_
    from_compensation()`와 같은 이유로 단일 정의로 분리) 원래 `audit_vertical_stack_id_
    vs_kcl()` 안에 있던 로직을 그대로 추출."""
    net_uses: dict = defaultdict(list)
    for t in transistors:
        net_uses[t.source].append(t.name)
        net_uses[t.drain].append(t.name)
    edges = []
    for net, uses in net_uses.items():
        if net in _RAIL_NETS:
            continue
        if len(uses) == 2 and uses[0] != uses[1]:
            edges.append((uses[0], uses[1], "internal_series", net))
    for names in matching_pairs:
        for a, b in zip(names, names[1:]):
            edges.append((a, b, "declared_matching_pair", None))
    return edges


def audit_vertical_stack_id_vs_kcl(transistors: list, matching_pairs: list,
                                    device_roles: dict) -> dict:
    """L2 축A(`kcl_series_union()`)와 declared `vertical_stack_id`(topology.json
    `device_roles`)가 서로 다른 질문에 답한다는 걸 2026-08-10 세션 대화에서 실측으로
    확인한 뒤 만든 감사(audit) 도구 -- **탐색 입력이 아니라 사후 대조표**로 쓴다(대화
    결론: `vertical_stack_id`로 KCL 탐색 범위를 좁히면 오히려 `M11b`/`M12`처럼 진짜
    2단자 직렬 관계를 vsid 경계가 가로막아 놓친다, 실측 확인됨 -- 그래서 탐색기가
    아니라 검증 대상으로 쓴다).

    `kcl_series_union()`이 union할 때 실제로 쓰는 것과 **똑같은 두 종류의 edge**를
    독립적으로 재구성한다(내부 2단자 net + declared `current_forced` matching_pairs) --
    이 edge 목록 자체가 "왜 두 소자가 같은 kcl 그룹인가"의 증거이므로, `kcl_series_
    union()`의 최종 그룹 딕셔너리만 봐서는 알 수 없는 **원인**을 그대로 들고 있다.

    반환 `{"boundary_findings": [...], "hub_findings": [...]}`:

    - **`boundary_findings`**: kcl edge(2단자 직렬 또는 declared 미러쌍)가 실제로
      **다른 declared `vertical_stack_id`를 잇는 경우** 전부. `kind="internal_series"`
      면 물리적으로 진짜 이어진 직렬 체인이 사람이 그은 기능적 경계(예:
      `biasgen_vom_battery_a`→`_battery_a_sink`)를 가로지른다는 뜻(정상 -- 그저
      "이 vsid 경계는 전기적 경계가 아니라 기능 이름 경계"라는 신호), `kind=
      "declared_matching_pair"`면 선언된 미러쌍이 서로 다른 물리적 branch에 있다는
      뜻(항상 정상 -- 미러 출력은 원래 다른 위치). 둘 다 review 불필요한 정상
      케이스지만, **한쪽만 `vertical_stack_id`가 선언**된 edge는 `note`에 gap으로
      표시 -- 이건 사람이 채워야 할 진짜 gap.
    - **`hub_findings`**: 하나의 declared `vertical_stack_id` 그룹의 멤버들이 kcl로는
      **여러 그룹으로 갈리는 경우** -- `candidate_hub_nets`에 그 그룹 멤버가 쓰는 net
      중 3단자 이상인 것(원인 후보)을 전부 나열한다. 후보가 있으면 `M9a`/`M9b`류
      floating-current-source처럼 "물리적으론 한 기능블럭이지만 전류는 3-branch
      KCL이라 단순 union-find로 못 푸는" 정상 케이스(수치 MNA가 필요할 수 있다는
      신호). **후보가 비어있으면(`candidate_hub_nets=[]`) 진짜 review 대상** --
      3단자 이상 net도 없이 kcl이 갈렸다는 건 간접 연결(다른 소자를 거친 declared
      pair 체인 등)이거나 declared `vertical_stack_id` 자체가 재검토가 필요하다는
      뜻일 수 있다.

    ⚠️ 이 함수는 아무것도 자동으로 고치거나 topology.json에 쓰지 않는다 -- 대조표만
    낸다(이 프로젝트 전역 원칙: 제안만, 최종 판단은 사람)."""
    net_uses: dict = defaultdict(list)
    for t in transistors:
        net_uses[t.source].append(t.name)
        net_uses[t.drain].append(t.name)
    edges = _kcl_and_matching_edges(transistors, matching_pairs)
    parent = {t.name: t.name for t in transistors}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b, _kind, _detail in edges:
        union(a, b)

    vsid_of = {name: entry.get("vertical_stack_id")
               for name, entry in device_roles.items()
               if isinstance(entry, dict) and entry.get("vertical_stack_id")}

    boundary_findings = []
    for a, b, kind, detail in edges:
        va, vb = vsid_of.get(a), vsid_of.get(b)
        if va is not None and vb is not None and va != vb:
            boundary_findings.append({"pair": (a, b), "kcl_reason": kind, "detail": detail,
                                       "vsid_a": va, "vsid_b": vb, "note": None})
        elif (va is None) != (vb is None):
            boundary_findings.append({"pair": (a, b), "kcl_reason": kind, "detail": detail,
                                       "vsid_a": va, "vsid_b": vb,
                                       "note": "한쪽만 vertical_stack_id 선언됨(gap)"})

    by_name = {t.name: t for t in transistors}
    vsid_groups: dict = defaultdict(list)
    for name, vsid in vsid_of.items():
        vsid_groups[vsid].append(name)

    hub_findings = []
    for vsid, members in vsid_groups.items():
        kcl_ids = {find(m) for m in members if m in parent}
        if len(kcl_ids) > 1:
            member_nets = set()
            for m in members:
                t = by_name[m]
                member_nets.add(t.source)
                member_nets.add(t.drain)
            hub_nets = sorted((n, len(net_uses[n])) for n in member_nets
                               if n not in _RAIL_NETS and len(net_uses.get(n, [])) >= 3)
            hub_findings.append({"vsid": vsid, "members": sorted(members),
                                  "kcl_subgroup_count": len(kcl_ids),
                                  "candidate_hub_nets": hub_nets})

    return {"boundary_findings": boundary_findings, "hub_findings": hub_findings}


def propose_vertical_stack_id_gap_fill(transistors: list, matching_pairs: list,
                                        device_roles: dict, inputs=(), outputs=(),
                                        feedbacks=(), biases=(), clocks=()) -> dict:
    """선언 안 된 소자가 **결합(union) 그룹** 안에서 이미 선언된 `vertical_stack_id`를
    물려받는 제안을 만든다(2026-08-13 세션31, 사용자 요청 -- `two_stage_ota.topology.
    json`의 M1/M2/M6 gap을 손으로 추론했던 걸 재사용 가능한 함수로 코드화).

    결합에 쓰는 edge 두 종류(전부 union-find로 묶은 뒤, 한 그룹에 declared 값이
    **정확히 하나**면 그 값을 미선언 멤버 전체에 제안):
    1. **`internal_series` KCL edge**(`_kcl_and_matching_edges()`, 진짜 2단자 직렬) --
       항상 사용. `declared_matching_pair` edge는 **의도적으로 제외**한다(`audit_
       vertical_stack_id_vs_kcl()` docstring대로 미러 출력이 회로 반대편 -- 원거리 --
       에 있는 경우가 흔해 "같은 헤드룸 컬럼"이라는 보장이 없다, 항상 참인 규칙이
       아니라 하드코딩하면 조용히 틀린 제안이 나올 위험).
    2. **`differential` 관계**(`find_verified_differential_and_mirror_relations()`,
       선택 -- `inputs=` 등 포트 분류를 넘겨야 활성화됨. 사용자 지적: 차동쌍 두 다리는
       전기적 정의상(공통 tail) 항상 같은 물리적 헤드룸 컬럼에 있어야 하므로 `mirror`
       관계(위와 같은 원거리 모호성 있음)와 달리 유니온해도 안전 -- 그래서 `mirror`는
       **의도적으로 제외**하고 `differential`만 쓴다. 실제로 diff pair의 공통 tail
       net은 보통 3단자 이상(두 다리+tail 전류원)이라 `internal_series`(정확히
       2단자)로는 애초에 못 잡는 관계 -- 이게 이 확장이 KCL 단독보다 진짜로 더 푸는
       실제 사례다). `inputs=`를 안 주거나 analog-grammar가 없으면 조용히 건너뛴다
       (기존처럼 KCL만으로 동작, 하위호환).

    ⚠️ 다른 `_propose_*`류와 같은 원칙(제안만, `topology.json`에 자동으로 안 씀).

    반환: `{"proposals": {device_name: proposed_vsid}, "conflicts": {device_name:
    [candidate_vsid, ...]}, "components_used": [[device,...], ...]}` -- `conflicts`는
    한 union 그룹 안에 서로 다른 declared 값이 2개 이상 섞인 경우(자동으로 못 정함,
    사람 검토 필요), `components_used`는 미선언 멤버가 하나라도 있던 그룹만(디버깅용)."""
    edges = [(a, b) for a, b, kind, _detail in _kcl_and_matching_edges(transistors, matching_pairs)
             if kind == "internal_series"]
    if inputs or outputs or feedbacks or biases or clocks:
        relations = find_verified_differential_and_mirror_relations(
            transistors, inputs, outputs, feedbacks, biases, clocks)
        if relations is not None:
            edges.extend(rel["devices"] for rel in relations["differential"])

    parent = {t.name: t.name for t in transistors}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in edges:
        union(a, b)

    vsid_of = {name: entry.get("vertical_stack_id")
               for name, entry in device_roles.items()
               if isinstance(entry, dict) and entry.get("vertical_stack_id")}

    groups = defaultdict(list)
    for t in transistors:
        groups[find(t.name)].append(t.name)

    proposals, conflicts, components_used = {}, {}, []
    for members in groups.values():
        members = sorted(members)
        undeclared = [m for m in members if vsid_of.get(m) is None]
        if not undeclared:
            continue
        declared = {vsid_of[m] for m in members if vsid_of.get(m) is not None}
        components_used.append(members)
        if len(declared) == 1:
            value = next(iter(declared))
            for m in undeclared:
                proposals[m] = value
        elif len(declared) > 1:
            for m in undeclared:
                conflicts[m] = sorted(declared)
    return {"proposals": proposals, "conflicts": conflicts, "components_used": components_used}


def audit_theta_root_direction(transistors: list, sizing_roles: dict | None,
                                 inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> list:
    """`sizing_roles.theta`의 `"A"`/`"A_signed"` feed가 `root`(이 theta가 전류를 **정의**하는
    소자)의 값을, `analog-grammar`의 `idioms.m_cascode()`가 이미 찾아둔 캐스코드 관계에서
    **`root`가 lo(전류생성원 쪽)인데 정작 그 위에 얹힌 up(캐스코드)을 reference/terms로
    참조**하는 경우를 찾는다 -- **방향이 거꾸로일 가능성이 높다는 신호**(캐스코드는 전류를
    정의하지 않고 그 아래 소자가 이미 정한 전류를 그대로 물려받을 뿐이므로, lo가 자기 위의
    up을 참조해 자기 값을 정하는 건 인과관계가 뒤바뀐 것).

    2026-08-18 신설 동기(3단계 정정 이력): (1) `nmcnr_amplifier`의 `M106`(캐스코드)/
    `M108`(다이오드) 관계를 사람 손으로 재추론하다 방향을 두 번 틀림 -- 사용자가
    "analog-grammar가 이미 이 관계를 알고 있지 않냐"고 지적. (2) 처음엔 role 우선순위
    비교(`DIODE_CONNECTED` root가 `CASCODE` reference를 참조하면 항상 걸어냄) + `bounds`
    퇴화 여부로 짰는데, `current_reuse_telescopic_ota`의 `r_cmfb_vocdes`(root=`M39`=diode,
    reference=`M37a`/`M37b`=cascode, 하지만 게이트로만 연결된 전압 구동 관계라 실제 KCL
    아님)에 오탐 -- 자체 source/drain 인접 그래프로 "실제 연결" 여부를 확인하도록 정정.
    (3) 사용자 재지적("이미 하는 analog-grammar 함수가 있지 않나? cascode구조를 seed를
    주어서 탐색하는?") -- `idioms.propagate_reference_role_through_cascode()`가 정확히
    그 역할인데 처음엔 안 썼다. 재확인해보니 `m_cascode()`가 **같은 kind끼리의 직렬(`up.S==
    lo.D`)만** 인정해서 `M106`(nmos)/`M108`(pmos)처럼 **PMOS/NMOS 경계(drain-drain 접합)**
    캐스코드는 아예 못 찾는다는 게 드러남 -- `idioms.m_cascode()` 자체에 cross-kind D-D
    분기를 신설(2026-08-18, `up.source`가 non-rail이어야 함 -- 안 그러면 `M15`/`M16` 같은
    complementary push-pull 출력단까지 오탐, 실측으로 발견) -- 이제 이 함수가 idiom 결과를
    그대로 재사용한다(자체 인접 그래프/BFS는 폐기).

    반환: `[{"theta": name, "root": root_dev, "reference": ref_dev, "note": ...}, ...]` --
    analog-grammar를 못 불러오면 빈 리스트(다른 analog-grammar 연동 함수와 동일한 하위호환
    원칙). ⚠️ 다른 `propose_*`/`audit_*`류와 같은 원칙 -- 아무것도 자동으로 안 고친다(찾기만).
    ⚠️ `m_cascode()`가 찾는 lo/up 관계에 안 걸리는 방향 오류(예: 둘 다 CASCODE도 DIODE도
    아닌 CURRENT_SOURCE류 두 소자 중 어느 쪽이 진짜 자유도인가, nmcnr_amplifier가 처음에
    `M104`를 자유변수로 잘못 뒀던 것과 같은 유형)는 KCL 자유도 개수를 세는 별도 분석이
    필요해 이 함수 범위 밖이다."""
    netclass_mod, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass_mod is None or idioms_mod is None:
        return []
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return []
    matches = find_idiom_matches(transistors, inputs, outputs, feedbacks, biases, clocks)
    if matches is None:
        return []

    findings = []
    for theta in (sizing_roles or {}).get("theta") or []:
        feed = theta.get("feeds")
        if not isinstance(feed, dict):
            continue
        ftype = feed.get("type")
        if ftype not in ("A", "A_signed"):
            continue
        roots = feed["root"] if isinstance(feed["root"], list) else [feed["root"]]
        if ftype == "A":
            others = list(feed.get("reference") or [])
        else:
            others = [term["device"] for term in feed.get("terms") or []]
        for root_dev in roots:
            # root_dev를 seed로 캐스코드 체인을 위로 전파 -- other_dev가 그 안에 있으면
            # root_dev가 lo(전류생성원)이고 other_dev가 그 위에 얹힌 up(캐스코드)이라는 뜻
            # (다단 캐스코드까지 고정점 반복으로 커버).
            reachable_up = idioms_mod.propagate_reference_role_through_cascode(
                matches, {root_dev}, devs) - {root_dev}
            for other_dev in others:
                if other_dev not in reachable_up:
                    continue
                findings.append({
                    "theta": theta.get("name"), "root": root_dev, "reference": other_dev,
                    "note": (f"root={root_dev!r}이 캐스코드 체인에서 reference/terms의 "
                             f"{other_dev!r}보다 아래(lo, 전류생성원)인데, {other_dev!r}은 "
                             f"그 위에 얹힌 캐스코드다(idioms.m_cascode()) -- root의 값을 "
                             f"자기보다 위에 있는 캐스코드에서 끌어오는 건 방향이 거꾸로일 "
                             f"가능성이 높음")})
    return findings


# 2026-08-18(사용자 승인 -- "propose_theta_kcl_gap_fill 만들자") -- 전류(ID) KCL 구조를
# connectivity + analog-grammar idiom만으로 제안한다. "이 회로에 어떤 종류의 자유도가
# 있는지"(root/reference 방향, diffpair 50/50 분배, 캐스코드 추종, KCL 합)는 오늘 세션
# 내내 확인했듯 대부분 구조적으로 결정되고(자유도 없음), 진짜 자유도(예: nmcnr_amplifier의
# Ibg_tail/r_fold_M108_M109)는 딱 "이 소자는 온칩 레퍼런스가 없다"는 사실만 구조로
# 알 수 있을 뿐 그 절대값/비율 자체는 사람 판단이 필요하다 -- 그래서 이 함수는 자유도
# 있는 소자엔 `const` placeholder(값은 항상 review 대상)만 제안하고, 나머지(자유도 없는
# 관계)는 실제 ratio/부호까지 확정해서 제안한다.
def _kcl_terminal_sign(kind: str, terminal: str) -> int:
    """PMOS/NMOS의 관례적 전류 방향(2026-08-18 세션, 사용자 지적 "PMOS/NMOS 경계는 항상
    drain-drain" 이후 sympy로 재확인한 부호 규칙)을 net 기준 부호로 변환한다 -- PMOS는
    source->drain(그 net에 전류를 **공급**하는 쪽이 drain, +1 / **흡수**하는 쪽이 source,
    -1), NMOS는 drain->source(그 반대, drain=-1/source=+1)다. 어떤 net에 모인 모든
    소자의 이 부호*ID 합은 KCL로 항상 0이다(nmcnr_amplifier의 NodeF1/NodeM1/NodeM2를
    이 부호로 sympy 재유도해 검증 완료, 세션 앞부분 참고)."""
    if kind == "pmos":
        return 1 if terminal == "drain" else -1
    return -1 if terminal == "drain" else 1


def propose_theta_kcl_gap_fill(transistors: list, matching_pairs_meta: list,
                                 ideal_sources: list | None = None,
                                 compensation_stage_devices: list | None = None,
                                 inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict:
    """`sizing_roles.theta`의 전류(ID) 구조(`"const"`/`"A"`/`"A_signed"` feed -- gm_id를
    직접 다루는 `"B"`/`"C"`/`"metric_stage_budget"`류는 범위 밖)를 connectivity와
    analog-grammar idiom만으로 제안한다.

    **알고리즘(고정점 반복)** -- 아무것도 "resolved"(전류가 이미 어떤 theta로 정의됐다)
    상태 없이 시작해서, 아래 규칙을 더 이상 진전이 없을 때까지 반복 적용한다(전부 실측
    검증 중 발견한 버그를 고치며 확정된 순서 -- 처음엔 1/2/3/4만 있었는데 folded_cascode
    실행 검증으로 2.5/2.7이 빠졌던 것과 규칙 2가 hub 노드에서 오판정하는 걸 둘 다 실측으로
    발견했다):

    1. **diffpair 50/50 분배**(`idioms.m_diffpair()`) -- 두 다리의 tail net을 drain으로
       공급하는 소자(tail 전류원)가 이미 resolved면, 두 다리를 `ratio=0.5`로 동시에
       resolved 처리(`"A"` feed, `root=[다리A,다리B]`, `reference=[tail]`).
    2. **캐스코드 추종**(`idioms.m_cascode()`의 `cascode-stack` Match, `ports['lo']`/
       `['up']`/`['mid']` 직접 사용) -- `lo`가 resolved면 `up`도 `ratio=1.0`으로 resolved.
       ⚠️ **`mid` net의 실제 사용자 수가 정확히 2일 때만** 적용한다 -- 3 이상(hub/fold
       노드)이면 규칙 2를 건너뛰고 규칙 3에 맡긴다(실측 발견한 진짜 버그: `folded_cascode`의
       X 노드(`M1`/`M3`/`M6`, 3-way fold)에서 `m_cascode()`가 `M3`→`M6`을 2소자 캐스코드로
       오판정해 `ratio=1.0`을 적용했더니, 그 값이 `M1`의 KCL에 그대로 흘러들어가
       `I(M1)=0`이라는 물리적으로 틀린 결과를 냈다 -- 세 번째 기여자(`M1`)를 무시한 2소자
       단순화가 원인).
    2.5. **declared mirror**(`symmetry.matching_pairs`의 `current_forced=true` 쌍) --
       규칙 2/1이 다루지 않는(source/drain 비인접, diffpair 아님) 순수 게이트 미러 관계.
       한쪽이 resolved면 나머지를 `ratio=1.0`(placeholder, review 대상)으로 resolved.
    2.7. **gate mirror**(`idioms.m_mirror()`) -- declared 매칭쌍에도 없는 diode 레퍼런스
       ↔ 미러 출력 관계(예: `folded_cascode`의 `MP`→`M3`/`M4` -- `M3`/`M4`끼리만 declared
       pair고 `MP`와는 안 묶여 있음). 이 규칙이 없으면 `MP`가 회로 나머지와 완전히 단절된
       고아 자유변수로 남는다(실측 발견).
    3. **KCL 합**(net 인접 그래프, `_kcl_terminal_sign()`) -- 레일도 아니고 `ideal_sources`
       종단도 아닌 net에서, 그 net을 source/drain으로 쓰는 소자 중 **정확히 1개만**
       미해결이면 나머지(전부 resolved)의 부호 있는 합으로 그 1개를 구한다(`"A_signed"`
       feed).
    4. **자유 root 승격**(교착 시에만, **한 번에 하나씩**) -- 1~3을 더 못 돌리는데 미해결
       소자가 남으면, **레일에 직접 닿은 단자가 있는** 소자 중 diode-connected(`gate==
       drain`, 자기참조로 스스로 동작점을 고정하는 진짜 전류생성원) 후보를 최우선으로,
       없으면 그 외 레일 인접 소자 중 아무거나 **딱 하나만** `const` placeholder로 resolved
       처리(review 필수 표시)하고 곧바로 1~3으로 돌아간다 -- 실측 발견한 버그: 교착 시
       레일 인접 소자를 전부 한꺼번에 승격시켰더니 `M104`/`M202`처럼 KCL로 풀렸어야 할
       소자까지 조기에 자유 root로 잘못 확정됐다. declared `matching_pairs`(`current_
       forced=true`)로 묶인 파트너가 같이 승격 대상이면 **하나의 theta로 합쳐 제안**한다
       (`root=[a,b]`) -- 별개 theta 2개로 선언하면 대칭이 구조적으로 보장 안 되던 사고
       (`M104`/`M105`)를 반복하지 않기 위함.
    5. 그래도 남는 미해결 소자(레일 인접 단자가 하나도 없어 4번도 못 거는 경우 -- `idioms.
       m_float_source()`의 Monticelli class-AB floating current source류가 실제 사례,
       `current_reuse_telescopic_ota`의 `M9a`/`M9b`/`M18a`/`M18b` 등 -- 이 패턴은 아직
       이 함수의 규칙 범위 밖이다, 정직한 한계)는 `unresolved_devices`로만 보고한다(값을
       지어내지 않음).

    **마지막 검증 패스**: 모든 theta_proposals를 `bounds` 중앙값으로 직접 재평가해(내부
    `_sim_ids`, `sizing_recipe.py` 의존 없이 이 함수 자신이 계산) 결과 전류가 0 이하인
    소자를 찾아 `review_needed`에 추가한다 -- 실측 발견: 서로 다른 독립 자유 root
    그룹(예: `folded_cascode`의 `MP`측/`M9`-`M10`측)이 같은 KCL 노드로 수렴하면, 둘 다
    같은 placeholder 값(`1e-05`)을 받아 우연히 상쇄돼 0이 나올 수 있다(구조 결함이
    아니라 "이 자유 root들의 실제 값을 서로 조율해야 한다"는 신호 -- 조용히 넘기지 않는다).

    ⚠️ 다른 `propose_*`류와 같은 원칙 -- 아무것도 자동으로 안 씀(제안만 반환). 자유
    root의 `bounds`는 항상 `[1e-05, 1e-05]`(folded_cascode/nmcnr_amplifier가 이미 쓴
    "1차 실행 가능하게 하는 임의값" 관행 그대로) + `review_needed`에 반드시 표시된다 --
    최종 숫자는 사람이 스펙 맞춰 정할 것.

    `compensation_stage_devices`(2026-08-19 세션37 신설, `propose_device_roles_gap_fill()`의
    동명 파라미터와 동일 계약 -- `[n for grp in topology["compensation"]["stage_devices"]
    for n in grp]`로 caller가 미리 평탄화해서 넘긴다) -- 이 소자들(예: `nmcnr_amplifier`의
    `M102`/`M103`/`M201`/`M301`)은 gm_id를 compensation이 별도로 관리하므로 **이 함수의
    theta 자유도 구조에 안 들어간다**: 함수 시작 시 곧바로 `resolved`에 편입시키되 이
    소자들 자체의 `theta_proposals` 항목은 만들지 않는다(compensation이 이미 그 소자의
    gm/ID를 결정하므로 이 함수가 또 다른 값을 강제하면 충돌). ⚠️ 이 파라미터를 안 주면
    (기본 `None`, 하위호환) 예전처럼 compensation 소속 소자도 평범한 KCL 자유 root로
    잘못 제안될 수 있다(2026-08-18 세션36이 처음 발견한 한계, 실제 사례: `nmcnr_amplifier`
    의 `M301`이 `r_free_M301`이라는 독립 `const` 자유 root로 제안돼 compensation의 gm3
    target 탐색과 정면으로 충돌하고, `M201`이 resolved로 안 잡혀 있던 탓에 `M203`/`M204`도
    "compensation과 무관한 독립 자유쌍"으로 잘못 묶였다 -- `compensation_stage_devices`를
    주면 `M301`은 아예 제안 대상에서 빠지고, `M203`은 `M201`(compensation이 결정)에서 온
    KCL(`kcl_M203`)로, `M204`는 그 `M203`의 declared mirror(규칙 2.5)로 **올바르게**
    재분류된다). 검증 패스(`_sim_ids`)에서는 compensation 소속 소자에 순수 검증용
    placeholder(`1e-05`)를 채워 넣는다(이 함수 자신의 theta로 낸 값이 아니라 부호 일관성만
    확인하기 위한 것 -- 실제 값은 compensation이 정한다).

    반환: `{"theta_proposals": [{"name",...,"bounds","feeds","intended_role_type",
    "_comment"}, ...], "review_needed": [{"device"|"devices", "reason"}, ...],
    "unresolved_devices": [...]}` -- analog-grammar를 못 불러오면 전부 빈 값 +
    `unavailable_reason`."""
    netclass_mod, idioms_mod = _import_analog_grammar("netclass", "idioms")
    if netclass_mod is None or idioms_mod is None:
        return {"theta_proposals": [], "review_needed": [], "unresolved_devices": [],
                "unavailable_reason": "analog-grammar를 import할 수 없음"}
    devs = _to_analog_grammar_devs(transistors)
    if not devs:
        return {"theta_proposals": [], "review_needed": [], "unresolved_devices": [],
                "unavailable_reason": "gate가 있는 소자가 없음"}
    by_name = {t.name: t for t in transistors}
    matches = find_idiom_matches(transistors, inputs, outputs, feedbacks, biases, clocks)
    if matches is None:
        return {"theta_proposals": [], "review_needed": [], "unresolved_devices": [],
                "unavailable_reason": "find_idiom_matches() 실패"}

    ideal_terms = set()
    for src in (ideal_sources or []):
        ideal_terms.update(src.get("terminals", []))

    diffpair_legs = [(m.devices[0], m.devices[1], m.ports["tail"])
                      for m in matches if m.kind == "differential-pair"]
    # 2026-08-18 신설(folded_cascode 실행 검증 중 발견) -- idioms.m_mirror()는 (gate,source,
    # type)이 전부 같은 소자군에서 diode-connected 레퍼런스(ref)와 그 미러 출력(non-ref)을
    # 찾는다. MP(diode)->M3/M4(미러)처럼 **게이트로만** 이어지는 관계(source/drain 인접
    # 아님, declared matching_pairs에도 없음 -- M3/M4끼리만 서로 쌍으로 declared돼 있고
    # MP와는 안 묶여 있음)는 규칙 2(캐스코드)도 규칙 2.5(declared mirror)도 못 잡아서 MP가
    # 회로 나머지와 완전히 단절된 고아 자유변수로 남는 실제 사고가 있었다.
    gate_mirror_groups = [(m.ports["ref"], [n for n in m.devices if n != m.ports["ref"]])
                           for m in matches if m.kind == "current-mirror"]

    net_uses: dict = defaultdict(list)  # net -> [(device_name, 'source'|'drain')]
    for t in transistors:
        if t.source not in _RAIL_NETS:
            net_uses[t.source].append((t.name, "source"))
        if t.drain not in _RAIL_NETS:
            net_uses[t.drain].append((t.name, "drain"))

    # 2026-08-18 신설(folded_cascode 실행 검증 중 발견한 진짜 버그) -- m_cascode()의
    # same-kind 규칙(up.S==lo.D)은 그 net이 진짜 2소자 직렬인지 3-way+ hub(fold 노드)인지
    # 구분하지 않는다. X 노드(M1/M3/M6, 3-way fold)에서 M6.source==M3.drain(같은 kind)이라
    # (lo=M3,up=M6) 캐스코드-추종(ratio=1.0)으로 잘못 제안됐고, 그 값이 M1의 KCL(규칙 3,
    # I(M1)=I(M6)-I(M3))에 그대로 흘러들어가 I(M1)=0이라는 물리적으로 틀린 결과를 냈다
    # (M1이라는 세 번째 기여자를 무시한 채 2소자 관계로 단순화했기 때문). mid net의
    # 실제 사용자 수(`net_uses`)가 정확히 2일 때만(진짜 직렬) 규칙 2를 적용하고, 3 이상
    # (hub/fold)이면 규칙 2는 건너뛰고 규칙 3(KCL 합, 모든 기여자를 정확히 반영)에 맡긴다.
    lo_up_pairs = [(m.ports["lo"], m.ports["up"]) for m in matches
                   if m.kind == "cascode-stack" and len(net_uses.get(m.ports["mid"], [])) == 2]

    forced_pair_of: dict = {}
    for p in matching_pairs_meta:
        if p.get("current_forced") and len(p["names"]) == 2:
            a, b = p["names"]
            forced_pair_of[a] = b
            forced_pair_of[b] = a

    # 2026-08-19(세션37) -- compensation 소속 소자는 시작부터 resolved로 편입(이 함수의
    # theta 구조엔 안 들어가지만, 다른 소자가 이들을 KCL/캐스코드/미러로 참조할 땐 "이미
    # 결정된 값"으로 취급되게 하기 위함 -- 위 docstring 참고).
    resolved: set = set(compensation_stage_devices or [])
    theta_proposals: list = []
    review_needed: list = []

    def _mark(names, theta):
        for n in names:
            resolved.add(n)
        theta_proposals.append(theta)

    def _run_rules_1_to_3() -> bool:
        """규칙 1(diffpair)/2(캐스코드)/2.5(mirror)/3(KCL 합)을 진전이 없을 때까지
        반복한다. 하나라도 새로 resolve됐으면 True."""
        any_progress = False
        progressed = True
        while progressed:
            progressed = False
            # 규칙 1: diffpair 50/50
            for leg_a, leg_b, tail_net in diffpair_legs:
                if leg_a in resolved or leg_b in resolved:
                    continue
                tail_devs = [n for n, t in by_name.items() if t.drain == tail_net]
                if len(tail_devs) != 1 or tail_devs[0] not in resolved:
                    continue
                _mark([leg_a, leg_b], {
                    "name": f"r_split_{leg_a}_{leg_b}", "bounds": [0.5, 0.5],
                    "feeds": {"type": "A", "root": [leg_a, leg_b], "reference": [tail_devs[0]]},
                    "intended_role_type": "A",
                    "_comment": (f"diffpair({leg_a}/{leg_b})가 tail({tail_devs[0]}) 전류를 "
                                 f"반씩 나눠 가짐(idioms.m_diffpair()로 탐지, 자유도 없음) -- "
                                 f"propose_theta_kcl_gap_fill() 자동 제안.")})
                progressed = any_progress = True

            # 규칙 2: 캐스코드 추종(source/drain으로 직접 이어진 관계, idioms.m_cascode())
            for lo, up in lo_up_pairs:
                if up in resolved or lo not in resolved:
                    continue
                _mark([up], {
                    "name": f"r_series_{up}", "bounds": [1.0, 1.0],
                    "feeds": {"type": "A", "root": [up], "reference": [lo]},
                    "intended_role_type": "A",
                    "_comment": (f"{up}(캐스코드)은 전류를 스스로 정의하지 않고 {lo}(그 아래 "
                                 f"전류를 정하는 소자)를 그대로 따라감(idioms.m_cascode() lo/up, "
                                 f"자유도 없음) -- propose_theta_kcl_gap_fill() 자동 제안.")})
                progressed = any_progress = True

            # 규칙 2.5: mirror(게이트로만 연결되는 declared current_forced 쌍 -- 2026-08-18
            # 신설, 실측 발견: M203(diode)/M204(mirror output)는 source/drain을 전혀 안
            # 공유해서(M204.gate==M203.drain일 뿐) 규칙 2(m_cascode, source/drain 인접
            # 전용)가 못 잡는다. declared current_forced=true 매칭쌍이면서 한쪽이 이미
            # resolved면 나머지를 ratio=1.0으로 propose -- 실제 W비율은 아직 topology
            # 단계에선 모르므로 1.0을 review 대상 placeholder로 쓴다(sizing_recipe.py의
            # auto_mirror_ratios와 동일 기본값 관례).
            for a, b in list(forced_pair_of.items()):
                if a in resolved or b not in resolved:
                    continue
                if (b, a) in lo_up_pairs or (a, b) in lo_up_pairs:
                    continue  # 이미 규칙 2(캐스코드)가 다루는 관계 -- 중복 제안 방지
                is_diffpair_pair = any({a, b} == {la, lb} for la, lb, _t in diffpair_legs)
                if is_diffpair_pair:
                    continue  # 규칙 1이 다루는 관계
                _mark([a], {
                    "name": f"r_mirror_{a}_{b}", "bounds": [1.0, 1.0],
                    "feeds": {"type": "A", "root": [a], "reference": [b]},
                    "intended_role_type": "A",
                    "_comment": (f"{a}는 declared current_forced 매칭쌍({b}와)의 미러 -- "
                                 f"source/drain으로 안 이어진 순수 게이트 미러라 실제 W비율은 "
                                 f"topology 단계에서 모름, ratio=1.0은 placeholder(review 필요). "
                                 f"propose_theta_kcl_gap_fill() 자동 제안.")})
                review_needed.append({"devices": [a, b],
                                       "reason": "미러 비율 1.0은 placeholder -- 실제 W비율로 재확인 필요"})
                progressed = any_progress = True

            # 규칙 2.7: gate mirror(idioms.m_mirror() -- diode 레퍼런스가 게이트만으로
            # 미러 출력을 구동하는 관계, declared matching_pairs에도 없고 source/drain도
            # 안 이어짐 -- 2026-08-18 신설, folded_cascode 실행 검증 중 발견: MP(diode)가
            # M3/M4(둘 다 M3/M4끼리만 declared pair, MP와는 무관)를 게이트로만 미러하는데
            # 이 관계를 못 잡아서 MP가 회로 나머지와 완전히 단절된 고아 자유변수로 남았다.
            for ref, outputs in gate_mirror_groups:
                if ref not in resolved:
                    continue
                for out_dev in outputs:
                    if out_dev in resolved:
                        continue
                    _mark([out_dev], {
                        "name": f"r_mirror_{out_dev}_{ref}", "bounds": [1.0, 1.0],
                        "feeds": {"type": "A", "root": [out_dev], "reference": [ref]},
                        "intended_role_type": "A",
                        "_comment": (f"{out_dev}는 {ref}(diode 레퍼런스)를 게이트로만 "
                                     f"미러(idioms.m_mirror(), source/drain 비인접) -- 실제 "
                                     f"W비율은 topology 단계에서 모름, ratio=1.0은 "
                                     f"placeholder(review 필요). propose_theta_kcl_gap_fill() "
                                     f"자동 제안.")})
                    review_needed.append({"devices": [out_dev, ref],
                                           "reason": "미러 비율 1.0은 placeholder -- 실제 W비율로 재확인 필요"})
                    progressed = any_progress = True

            # 규칙 3: KCL 합(net에서 정확히 1개만 미해결)
            for net, uses in net_uses.items():
                if net in ideal_terms or len(uses) < 2:
                    continue
                unresolved_here = [(n, term) for n, term in uses if n not in resolved]
                if len(unresolved_here) != 1:
                    continue
                root_name, root_term = unresolved_here[0]
                root_sign = _kcl_terminal_sign(by_name[root_name].kind, root_term)
                terms = []
                for n, term in uses:
                    if n == root_name:
                        continue
                    other_sign = _kcl_terminal_sign(by_name[n].kind, term)
                    terms.append({"device": n, "sign": -root_sign * other_sign})
                _mark([root_name], {
                    "name": f"kcl_{root_name}", "bounds": [1.0, 1.0],
                    "feeds": {"type": "A_signed", "root": root_name, "terms": terms},
                    "intended_role_type": "A",
                    "_comment": (f"{net} net KCL(PMOS source->drain/NMOS drain->source 관례, "
                                 f"_kcl_terminal_sign()) -- propose_theta_kcl_gap_fill() 자동 "
                                 f"제안, 자유도 없음.")})
                progressed = any_progress = True
        return any_progress

    _run_rules_1_to_3()

    # 규칙 4: 교착 시에만, **한 번에 하나씩만** 자유 root로 승격하고 곧바로 규칙 1~3을
    # 다시 돌린다(2026-08-18 정정, 실측 발견 -- 교착 시 레일 인접 소자를 전부 한꺼번에
    # 승격시켰더니 M104/M202처럼 KCL로 풀렸어야 할 소자까지 조기에 자유 root로 잘못
    # 확정됐다). diode-connected(gate==drain, 자기참조로 스스로 동작점을 고정하는 진짜
    # 전류생성원) 후보를 항상 우선한다 -- 그런 후보가 하나도 없을 때만 diode가 아닌
    # 레일 인접 소자를 승격한다(예: nmcnr_amplifier의 M101 -- tail, diode 아님).
    while True:
        unresolved_all = [t.name for t in transistors if t.name not in resolved]
        if not unresolved_all:
            break
        rail_adjacent = [n for n in unresolved_all
                          if by_name[n].source in _RAIL_NETS or by_name[n].drain in _RAIL_NETS]
        if not rail_adjacent:
            break  # 레일 인접 후보가 아예 없음 -- 5번(진짜 미분류)으로 남김
        diode_candidates = [n for n in rail_adjacent if by_name[n].gate == by_name[n].drain]
        pick = diode_candidates[0] if diode_candidates else rail_adjacent[0]
        partner = forced_pair_of.get(pick)
        if partner is not None and partner in rail_adjacent:
            names = sorted([pick, partner])
            _mark(names, {
                "name": f"r_free_{names[0]}_{names[1]}", "bounds": [1e-05, 1e-05],
                "feeds": {"type": "const", "root": names},
                "intended_role_type": "D",
                "_comment": (f"{names[0]}/{names[1]}는 온칩 레퍼런스가 없는 자유 root로 "
                             f"보임(레일에 직접 닿음 + declared current_forced 매칭쌍이라 "
                             f"하나로 합침 -- 별개 theta 2개로 선언하면 대칭이 구조적으로 "
                             f"보장 안 됨, 이번 세션 M104/M105 사고와 동일 클래스). "
                             f"propose_theta_kcl_gap_fill() 자동 제안 -- 값은 임의(1차 "
                             f"실행용), 사람이 스펙 맞춰 재확인할 것.")})
            review_needed.append({"devices": names,
                                   "reason": "자유 root(placeholder 값, 사람 확인 필요)"})
        else:
            _mark([pick], {
                "name": f"r_free_{pick}", "bounds": [1e-05, 1e-05],
                "feeds": {"type": "const", "root": [pick]},
                "intended_role_type": "D",
                "_comment": (f"{pick}은 온칩 레퍼런스가 없는 자유 root로 보임(레일에 직접 "
                             f"닿음, 다른 소자에서 전류를 유도할 KCL/캐스코드/diffpair/mirror "
                             f"관계가 없음). propose_theta_kcl_gap_fill() 자동 제안 -- 값은 "
                             f"임의(1차 실행용), 사람이 스펙 맞춰 재확인할 것.")})
            review_needed.append({"devices": [pick],
                                   "reason": "자유 root(placeholder 값, 사람 확인 필요)"})
        _run_rules_1_to_3()  # 방금 승격한 root로 규칙 1~3이 더 풀 수 있는지 즉시 재시도

    # 2026-08-18 신설(folded_cascode 실행 검증 중 발견) -- 서로 다른 자유 root 그룹(예:
    # MP측 / M9-M10측)이 같은 KCL 노드로 수렴하면, 둘 다 같은 placeholder 값(1e-5)을 받는
    # 이 함수의 기본 평가에서는 우연히 상쇄돼 0(또는 음수)이 나올 수 있다(I(M1)=I(M6)-I(M3)
    # 실측 사례) -- 이건 theta **구조** 자체의 결함이 아니라 "이 자유 root들이 서로 조율된
    # 값이어야 한다"는 신호인데, 조용히 넘기면 사람이 못 알아챈다. theta_proposals를
    # 실제로 bounds 중앙값으로 평가해 음수/0이 나오는 소자를 전부 찾아 review_needed에
    # 남긴다(지어내지 않는다 원칙 -- 문제를 숨기지 않고 구조화된 형태로 보고).
    # 2026-08-19(세션37) -- compensation 소속 소자는 theta_proposals에 없어 이 검증 루프가
    # 자연스럽게 채우지 못한다(참조하는 다른 theta가 `_sim_ids.get(r, 0.0)`으로 0을 받아
    # 가짜 "전류 0/음수" 경고를 낼 위험) -- 순수 검증용 placeholder(1e-05, 이 함수의 다른
    # 자유 root와 동일 관행)로 미리 채워 이 오탐을 막는다. 실제 값은 compensation이 정한다.
    _sim_ids: dict = {n: 1e-05 for n in (compensation_stage_devices or [])}
    for _t in theta_proposals:
        _feed, _mid = _t["feeds"], sum(_t["bounds"]) / 2.0
        _root_list = _feed["root"] if isinstance(_feed["root"], list) else [_feed["root"]]
        if _feed["type"] == "const":
            _val = _mid
        elif _feed["type"] == "A":
            _val = _mid * sum(_sim_ids.get(r, 0.0) for r in _feed["reference"])
        else:  # A_signed
            _val = _mid * sum(_term.get("sign", 1) * _sim_ids.get(_term["device"], 0.0)
                               for _term in _feed["terms"])
        for _r in _root_list:
            _sim_ids[_r] = _val
    nonpositive = sorted(n for n, v in _sim_ids.items() if v <= 0)
    if nonpositive:
        review_needed.append({
            "devices": nonpositive,
            "reason": ("bounds 중앙값(placeholder)으로 평가하면 전류가 0 또는 음수로 나옴 -- "
                       "서로 다른 자유 root 그룹이 같은 KCL 노드로 수렴하는데 우연히 같은 "
                       "placeholder 값을 받아서일 가능성이 높음(구조 결함 아님). 자유 root "
                       "값을 정할 때 이 소자들이 양수가 되도록 서로 조율할 것.")})

    unresolved_devices = [t.name for t in transistors if t.name not in resolved]
    return {"theta_proposals": theta_proposals, "review_needed": review_needed,
            "unresolved_devices": unresolved_devices}


def apply_theta_kcl_gap_fill(topology_json_path: str, result: dict) -> dict:
    """`propose_theta_kcl_gap_fill()`의 순수 결과를 받아 **실제로 topology.json 파일을 읽고
    병합하고 다시 쓴다**(`sizing_roles.theta`에 새 항목 append) -- `apply_device_roles_gap_fill()`
    과 정확히 같은 계약: 이미 declared된 소자와 충돌하면 그 제안은 조용히 건너뛴다(덮어쓰지
    않는다), 파일을 통째로 다시 씀.

    "충돌"의 정의(2026-08-19 세션37 신설) -- 제안 하나(`theta_proposals[i]`)가 다루는
    root 소자 중 **단 하나라도** 이미 기존 `sizing_roles.theta`의 어느 항목의 root에
    들어있으면 그 제안 전체를 스킵한다(부분 적용 안 함 -- 예: `nmcnr_amplifier`의 `kcl_M101`
    제안은 `M101`이 이미 기존 `Ibg_tail` theta의 root라서 스킵되고, `r_free_M108_M109`도
    `M108`/`M109`가 이미 기존 `r_fold_M108_M109`의 root라서 스킵된다 -- 이 두 소자는 이미
    이번 세션 baseline 실측까지 끝난 확정 설계라 재제안으로 조용히 갈아엎지 않는다). 이미
    theta가 있는 소자를 전혀 다루지 않는 순수 신규 제안(예: 지금까지 `sizing_roles.theta`가
    아예 없던 `M202`/`M203`/`M204`/`M302`)만 실제로 추가된다.

    반환: `{"applied": [theta_name, ...], "skipped_conflict": [{"name","conflicting_devices"}
    , ...]}`."""
    with open(topology_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sizing_roles = data.get("sizing_roles")
    if sizing_roles is None:
        sizing_roles = {}
    existing_theta = sizing_roles.get("theta") or []

    existing_roots: set = set()
    for t in existing_theta:
        feed = t.get("feeds")
        if not isinstance(feed, dict):
            continue
        root = feed.get("root")
        existing_roots.update(root if isinstance(root, list) else [root])

    applied, skipped = [], []
    for proposal in result.get("theta_proposals", []):
        feed = proposal["feeds"]
        root = feed["root"] if isinstance(feed["root"], list) else [feed["root"]]
        conflicting = [n for n in root if n in existing_roots]
        if conflicting:
            skipped.append({"name": proposal["name"], "conflicting_devices": conflicting})
            continue
        existing_theta.append(proposal)
        existing_roots.update(root)
        applied.append(proposal["name"])

    sizing_roles["theta"] = existing_theta
    data["sizing_roles"] = sizing_roles

    with open(topology_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return {"applied": applied, "skipped_conflict": skipped}


def propose_device_roles_gap_fill(transistors: list, device_roles: dict, matching_pairs_meta: list,
                                    compensation_stage_devices: list | None = None,
                                    vds_theta_authoritative: set | None = None,
                                    inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> dict:
    """`symmetry.matching_pairs`/`device_roles`(`gm_id_role`/`L_role`/`headroom_role`)를 **netlist
    connectivity만으로** 제안한다(2026-08-14, `.ai/context.md` 세션32 I절 설계 + 다음 세션 실측
    검증을 반영해 확정). `vertical_stack_id`는 제안하지 않는다 -- I-1의 `propose_vertical_stack_
    id_gap_fill()`이 이미 그 필드를 전담하고(같은 이유: mirror edge를 vsid 유니온에 안 쓰는 것과
    동일 원칙), 이 함수와 역할이 겹치면 두 제안이 서로 다른 값을 낼 위험이 생긴다.

    호출자가 `inputs=`를 안 줘도(기본값 `()`) 동작한다 -- `refine_differential_and_mirror_
    relations()`의 부트스트랩(포트 분류 없이 diffpair 후보를 찾고 그 gate net을 자동 승격, 고정점
    까지 반복)에 그대로 맡긴다. `inputs=`를 준다면 그 위에서 시작할 뿐 결과가 틀려지지 않는다.

    **실측으로 확정된 3단계 소스(세션32 I-3 설계 대비 2가지 확장)**:
    1. `relations["mirror"]`/`relations["differential"]`(branch-composite 비교, 기존 I-3
       설계 그대로) -- `differential` -> `matching_sensitivity="offset", current_forced=True`
       (공유 tail의 차동쌍은 KCL로 물리적으로 강제되는 관계, 4개 회로 전수 확인 무예외).
       `mirror` -> `"ratio", current_forced=False`(기본 제안일 뿐 -- 진짜 강제 여부는
       `sizing_roles`/theta 선언에만 있어 netlist로는 확정 불가, 아래 review_needed 참고).
    2. **신규(세션32엔 없었음)** `find_structural_symmetry_candidates(transform="mirror")` --
       seed를 손으로 안 넣고 1번이 이미 찾은 `differential` 쌍의 gate net(+ `vdd`/`gnd`/`vss`)만
       기계적으로 넣는다. 51소자 실회로 실측: 1번만으로는 declared 21그룹 중 9그룹만 찾지만, 이
       보강을 더하면 18그룹(진짜 2-소자 매칭쌍 전부, 오탐 0건)까지 늘어난다 -- composite 비교가
       "rail-to-rail branch 전체가 완전히 같아야" 찾는 것과 달리, 이건 전역 좌우 net 재라벨링
       (graph automorphism)이라 물리적으로 먼 위치(예: `M8`<->`M17`)의 매칭도 찾는다.
    3. **신규(세션32엔 없었음)** 층위1 폴백(`find_matching_candidates()`) -- 1번/2번이 전혀
       못 찾는 회로(실측: `folded_cascode`/`two_stage_ota`/`nmcnr_amplifier`처럼 folding node나
       cross-coupling이 있어 branch 전체가 안 대칭인 회로, composite 비교가 통째로 0건을 냄)를
       위한 안전망. `diff_pair` 태그는 정확히 2소자면 그대로 채택(1번과 동일 근거, 4개 회로
       전수 무예외 확인). `current_mirror` 태그는 정확히 2소자이고 그중 diode-connected
       (`gate==drain`) 소자가 있을 때만 채택(`ratio`, `current_forced=False`) -- diode 레퍼런스가
       없는 경우(예: `folded_cascode`의 `M5`/`M6`, 같은 `bias3`를 공유하지만 "구조적 유사성뿐
       KCL 근거 없음"이라고 그 파일 자신의 주석에 명시)는 채택하지 않고 `review_needed`로 넘긴다.

    이미 `matching_pairs_meta`에 (부분집합으로) 포함된 쌍은 다시 제안하지 않는다.

    **device_roles**: `find_verified_differential_and_mirror_relations()`/`find_structural_
    symmetry_candidates()`가 이미 검증한 구조 신호로 `refine_differential_and_mirror_relations()`가
    함께 반환하는 `gm_id_role_candidates`/`L_role_candidates`/`headroom_role_candidates`를 그대로
    옮긴다(51소자 실회로 실측: `gm_id_role` 33/37, `L_role` 36/37, `headroom_role` 34/37 declared
    일치 -- 세션32가 수동으로 `inputs=("Vip","Vim")`을 미리 넣고 검증했던 수치보다 부트스트랩
    전용이라 약간 낮지만, 사람이 포트를 미리 알려줄 필요가 전혀 없다는 게 이 함수의 존재 이유다).
    `compensation_stage_devices`에 있는 소자도 **똑같이 제안한다**(세션32 I-3 "정정 3" 그대로
    -- "스킵하면 spec 기반 재설계 검증 자체가 안 된다"는 근거). ⚠️ 2026-08-14 실측 경위: 처음엔
    이 "충돌 시 compensation이 이긴다"는 전제가 `gm_id_role`엔 실제로 안 지켜진다는 걸 발견하고
    (`L_role`은 `_AUTHORITATIVE_L_SOURCES` 가드로 안전했지만 `gm_id_role`엔 대칭 가드가 없어서
    `search_gm_id_for_role()`이 그대로 돌아 compensation이 정한 사이징을 덮어쓰는 진짜 버그였음)
    한때 이 함수에서 compensation 소속 소자를 통째로 건너뛰도록 막았으나, 사용자 지시("가드를
    만들어야지 왜 제외해")로 방향을 바꿔 **근본원인(sizing_recipe.py의 누락된 가드)을 직접
    고쳤다** -- `_AUTHORITATIVE_GM_ID_SOURCES={"compensation"}`(gm_id_role 루프 진입 직전 가드,
    `_evaluate()` 내부, `_L_source=="compensation"`이면 스킵). `_AUTHORITATIVE_L_SOURCES`를
    그대로 재사용하지 않은 이유: 그 집합엔 `"replica"`도 있는데, C타입 K_replica feed는 정반대로
    **이 gm_id_role 루프가 재검색해서 값을 덮어쓰는 것 자체가 설계 의도**다(`_feed_diode_stack_
    target()` docstring에 이미 명시돼 있었음 -- L/vds/vs만 replica가 권위 있고 gm_id는 처음부터
    placeholder). 이제 이 함수는 compensation 소속 여부와 무관하게 제안하고, `review_needed`에
    "compensation 소속이라 gm_id_role은 가드로 무시됨(안전)"이라는 참고 정보만 남긴다.

    이미 `device_roles`에 선언된 값과 제안값이 다르면 **그 소자의 그 필드는 조용히 덮어쓰지 않고**
    `review_needed`로만 보고한다(프로젝트 전역 원칙).

    **4번째 소스(2026-08-14 세션34 신설) -- "gain" `gm_id_role` 제안**: 사용자 질문("mirror
    구조로 bias를 잡아주지만 실제로는 gain stage의 load인 경우를 mirror 대신 gain으로
    분류해야 하지 않나")에서 시작 -- `active_load_leg_candidates`(레일에 직접 물린 소자의
    드레인이 HIGH_Z 이득노드, `role`이 `AMPLIFYING`으로 가려진 경우까지 `idioms.m_mirror()`의
    `active_load_legs` 포트로 포함, `two_stage_ota`의 `M7`/`M4` 둘 다 실측 확인) 중 **파트너가
    전혀 없는 소자만** `gm_id_role="gain"`을 제안한다 -- 파트너 유무는 두 가지 메커니즘으로
    확인한다: (1) `L_role_candidates[name].symmetry_partner`(전역 그래프 자기동형, 예:
    `current_reuse_telescopic_ota`의 `M13`<->`M22`), (2) `branch_load_partner_candidates`
    (diffpair 두 branch에 각각 앉은 부하, 예: `two_stage_ota`의 `M3`<->`M4`, `idioms.
    m_diffpair_branch_load()` 참고).

    **왜 파트너가 있으면 "gain"을 제안 안 하는가(2026-08-14 정정-- 처음엔 "구조로 확정
    불가, 사람 판단 필요"라고 봤으나 재검토로 더 강한 결론이 나옴)**: 두 파트너 메커니즘
    다 정의상 "이 소자가 differential balance 역할을 한다"는 사실을 이미 내포한다 -- 구조
    대칭 partner는 주변 서브그래프 전체가 좌우대칭이라는 뜻이고, diffpair branch-load
    partner는 정의상 differential pair의 두 branch에 앉은 부하다(어느 쪽이든 미스매치가
    곧바로 차동 비대칭/오프셋으로 이어짐). 실측 확인된 2건 -- `two_stage_ota`의 `M3`/`M4`
    (세션31이 `gain_db` 붕괴 방지를 위해 `matching`+`gm_id_min=8.0`으로 확정), `current_
    reuse_telescopic_ota`의 `M13`<->`M22`/`M12`<->`M21`(각각 Vom쪽/Vop쪽 class-AB
    quiescent 바이어스를 독립 net(N14a14b/N24b23a 등)으로 생성해 M9a/M9b<->M18a/M18b
    Monticelli 쌍에 먹이는 구조, netlist 직접 추적으로 확인) -- 전부 "matching"이 맞았고
    반례는 없었다. 그래서 파트너 있는 소자는 이 4번째 소스에서 "gain"을 제안하지 않는다
    (`gm_id_role_candidates`의 기존 경로가 이미 "matching"을 정확히 제안한다 -- 파트너
    없는 소자만 새로 다루면 되는 gap이었다), review_needed에는 판단을 요구하는 미확정
    항목이 아니라 이 근거를 투명하게 남기는 정보성 기록만 남긴다.

    analog-grammar가 없으면(`refine_differential_and_mirror_relations()`가 의존) 빈 제안 +
    `unavailable_reason`을 반환한다.

    **5번째 소스(2026-08-20 세션40 신설) -- `vds_match_vgs_of` 자동 제안**: `compensation.
    stage_devices` 소속 Y의 gate net이 다른 소자 X의 drain net과 같고 X.source==Y.source면
    VGS(Y)=VDS(X)가 KVL로 강제된다(M301/M204·M109/M201·M10/M16 실측 사례와 동일 판정
    기준, `.ai/context.md` 세션38~39 참고) -- X에 `vds_match_vgs_of=Y`를 제안한다. X가
    diode-connected(평범한 current mirror 레퍼런스 -- 다른 메커니즘의 영역)거나, X도
    compensation 소속(방향 태그만으론 판정 불가, M4/M6 실례)이거나, X에 `vertical_stack_id`
    가 없거나(theta feed 레벨이 맞는 자리), X가 `vds_theta_authoritative`(아래 인자,
    theta feed가 헤드룸보다 먼저 vds를 채우는 소자 -- `vertical_stack_id`가 있어도
    선언이 조용히 무시되는 케이스, two_stage_ota의 M4가 실제 사례)에 속하거나, source가
    다르거나, 대상이 여럿이면 제안하지 않고 `review_needed`에 구체적 근거를 남긴다
    (자동 적용 안 함). `vds_theta_authoritative`를 안 주면(기본값) 이 필터는 건너뛴다 --
    호출자가 `find_authoritative_sizing_devices(data)`(같은 파일, raw topology.json dict
    그대로 넘기면 됨)로 계산해 넘겨줘야 정확하다(`load_topology()`가 실제로 이렇게 함).

    **6번째 소스(2026-08-20 세션41 연속)** -- `budget_reference_device` 자동 제안(위
    상세 근거는 구현부 주석 참고): X가 `vertical_stack_id` 소속이고 자기 그룹 밖으로 열린
    유일한 단자가 소자 Y의 drain(Y.source=레일)과 같으면, X가 속한 그룹의 진짜 헤드룸
    예산은 `vdd`가 아니라 `vdd-VDS(Y)`다 -- X에 `budget_reference_device=Y`를 제안.

    **7번째 소스(2026-08-20 세션41 연속)** -- `fold_group` 자동 제안: 서로 다른
    `vertical_stack_id` 소속 X/Y가 kind가 반대이고 drain을 공유하면(폴디드 캐스코드의
    폴딩 노드) 둘 다 vdd~gnd 단일 컬럼이 아니라는 뜻이다 -- 같은 `fold_group` 태그를
    제안(`_fold_group_check()`가 검증하는 것과 동일 connectivity 근거).

    반환: `{"matching_pairs_proposals": [{"names","matching_sensitivity","current_forced",
    "_comment"}, ...], "device_roles_proposals": {device_name: {"gm_id_role"?,"L_role"?,
    "headroom_role"?,"vds_match_vgs_of"?,"budget_reference_device"?,"fold_group"?}, ...},
    "review_needed": [...], "diagnostics":
    {"promoted_inputs", "final_inputs", "structural_symmetry_unresolved"}}`."""
    refined = refine_differential_and_mirror_relations(transistors, inputs, outputs, feedbacks,
                                                          biases, clocks)
    if refined is None:
        return {"matching_pairs_proposals": [], "device_roles_proposals": {}, "review_needed": [],
                "unavailable_reason": "analog-grammar를 import할 수 없어 이 오케스트레이션 전체가 "
                                        "동작하지 않는다(refine_differential_and_mirror_relations()가 "
                                        "None을 반환)."}

    relations = refined["relations"]
    by_name = {t.name: t for t in transistors}
    gm_id_role_candidates = refined["gm_id_role_candidates"] or {}
    L_role_candidates = refined["L_role_candidates"] or {}
    headroom_role_candidates = refined["headroom_role_candidates"] or {}
    active_load_leg_candidates = refined.get("active_load_leg_candidates") or set()
    branch_load_partner_candidates = refined.get("branch_load_partner_candidates") or {}
    signal_referenced_mirror_legs = refined.get("signal_referenced_mirror_legs") or {}

    # ⚠️ 4번째 소스(2026-08-14 세션34, 이후 M203/M204 계기로 세 번째 제외 조건 추가) --
    # 위 docstring "gain gm_id_role 제안" 참고. 파트너(구조 대칭 또는 diffpair branch-load)가
    # 있거나, diode-connected 레퍼런스 자신의 노드가 SIGNAL인 미러의 다리(아래 참고)인
    # active-load 소자만 제외하고 "gain"으로 덮어쓴다.
    gain_role_candidates = {
        name for name in active_load_leg_candidates
        if not (L_role_candidates.get(name) or {}).get("symmetry_partner")
        and name not in branch_load_partner_candidates
        and name not in signal_referenced_mirror_legs
    }

    seed_net_pairs = {net: net for net in _RAIL_NETS}
    for rel in relations["differential"]:
        a, b = rel["devices"]
        ga, gb = by_name[a].gate, by_name[b].gate
        seed_net_pairs[ga] = gb
        seed_net_pairs[gb] = ga
    structural = find_structural_symmetry_candidates(transistors, seed_net_pairs, transform="mirror")

    declared_covered = set()
    for p in matching_pairs_meta:
        for a, b in itertools.combinations(p["names"], 2):
            declared_covered.add(frozenset((a, b)))

    matching_pairs_proposals = []
    seen = set()

    def _propose_pair(a, b, sensitivity, current_forced, source, confidence="high"):
        key = frozenset((a, b))
        if key in declared_covered or key in seen:
            return
        seen.add(key)
        aa, bb = sorted((a, b))
        matching_pairs_proposals.append({
            "names": [aa, bb], "matching_sensitivity": sensitivity, "current_forced": current_forced,
            "_comment": f"propose_device_roles_gap_fill() 자동 제안 -- source={source}, "
                        f"confidence={confidence}"})

    # ⚠️ 2026-08-14 정정(사용자 지적 -- "대칭적인 branch이면 branch 전류가 같아야 하는것
    # 아니야?") -- mirror/structural_symmetry 출처는 원래 current_forced=False 기본값이었다
    # (근거 없이 추측, "current_forced은 netlist만으로 결정 불가"라는 이전 결론을 여기
    # 잘못 적용함). 4개 실회로의 declared current_forced를 전수 재조사한 결과: **2-소자
    # matching_pairs는 예외 없이 current_forced=True**였다(current_reuse_telescopic_ota
    # 18/18, folded_cascode 4/5 -- 유일한 예외 M5/M6은 diode 참조가 아예 없는 "구조적
    # 유사성뿐" 케이스로 애초에 이 함수가 그런 경우는 제안하지 않음, two_stage_ota 2/2).
    # current_forced=False는 오직 **3개 이상(N-ary) 그룹**(예: Vbias1을 공유하는 7-way
    # 문서화 그룹, 서로 다른 전류 스케일이 섞여 있음)과 diode 참조가 netlist에 아예 안
    # 보이는 경우(nmcnr_amplifier의 M104/M105 등, 이 함수는 diode 미확인 시 애초에 제안
    # 안 함)에만 나타난다. mirror/structural_symmetry는 이미 "진짜 매칭 관계가 확인된
    # 2-소자 쌍"만 내므로(대칭 branch는 설계 의도상 같은 전류를 흘리도록 사이징되는 게
    # 정상) True가 맞는 기본값이다. ⚠️ 이 기본값도 100% 확실하진 않다(M38처럼 사람이
    # 전기적 이유로 override한 선례가 있음) -- 그래서 differential(순수 KCL, 예외 0건)과
    # 달리 review 게이트 대상에 그대로 남긴다(require_device_roles_reviewed() 확장, 아래).
    for rel in relations["mirror"]:
        a, b = rel["devices"]
        _propose_pair(a, b, "ratio", True, "branch_composite_mirror")
    for rel in relations["differential"]:
        a, b = rel["devices"]
        _propose_pair(a, b, "offset", True, "branch_composite_differential",
                       confidence="high(공유 tail KCL로 물리적 강제, review 불필요)")
    for a, b in structural.device_map.items():
        if a == b:
            continue
        low_conf = frozenset((a, b)) in structural.low_confidence_pairs
        _propose_pair(a, b, "ratio", True, "structural_symmetry",
                       confidence="low(단자 1개 근거)" if low_conf else "high")

    # ⚠️ 실측으로 발견(2026-08-14) -- 층위1 current_mirror 태그는 "같은 gate를 공유"만
    # 확인하므로, diode-connected 참조가 있어도 그 gate를 읽는 상대가 진짜 미러 출력이
    # 아니라 Monticelli floating-current-source(예: 51소자 회로의 M9a/M9b/M18a/M18b)나
    # CMFB 피드백을 받는 소자(M7, gate=Vcmfb)일 수 있다 -- 이 경우 그룹을 매칭쌍으로
    # 제안하면 오탐이다(51소자 회로에서 실측: {M11b,M9a}, {M14a,M9b}, {M18a,M20b},
    # {M18b,M23a}, {M36a,M7} 5건 전부 declared에 없는 오탐이었음).
    #
    # ⚠️ 2026-08-14 세션34 정정(사용자 지적, `folded_cascode`의 M11/MN 계기) -- 원래는
    # `headroom_role_candidates in ("mirror","cascode")`로 걸렀는데, 이건 잘못된 대리
    # 신호였다: `folded_cascode`의 `M11`(diffpair 진짜 tail, `ideal_sources`의 `Ibg`가
    # MN/MP 각각을 독립된 진짜 바이어스 레퍼런스로 명시)은 `headroom_role='tail'`이라
    # 이 조건에 걸려 review 후보에서 통째로 빠졌다 -- `tail`이라는 사실 자체가 오탐의
    # 원인이 아니었다(사용자 지적: "M11이 tail이라는 것" 자체는 `Ibg` ideal source로
    # 오히려 확인되는 정상 사실). 진짜 오탐 원인은 게이트가 **CMFB처럼 동적으로 조정되는
    # 신호**(고정 레퍼런스가 아님)인가였다 -- 실측: `M7`의 `role`은 `AMPLIFYING`이다
    # (게이트 `Vcmfb`가 `netclass.classify_nets()`에서 BIAS가 아니라 SIGNAL로 분류돼
    # `assign_roles()`의 role 우선순위상 AMP가 먼저 걸림), 반면 `M11`의 `role`은
    # `CURRENT_SOURCE`다(게이트 `vb2`가 진짜 고정 BIAS로 분류됨) -- `headroom_role`이
    # 아니라 **`role`**(고정 레퍼런스=CURRENT_SOURCE/ACTIVE_LOAD/CASCODE vs 동적/신호=
    # AMPLIFYING/CONTROLLED_CURRENT_SOURCE)이 정확한 구분 신호였다. floating_current_
    # source(M9a류)는 role 자체가 FLOATING_CURRENT_SOURCE라 이 허용 목록에 없어 여전히
    # 배제된다(회귀 없음, 아래 self-test로 재확인).
    _netclass_lcmf, _idioms_lcmf = _import_analog_grammar("netclass", "idioms")
    _static_ref_roles = (
        (_netclass_lcmf.DIODE, _netclass_lcmf.CURR_SRC, _netclass_lcmf.ACTIVE_LOAD,
         _netclass_lcmf.CASCODE) if _netclass_lcmf is not None else ())
    role_candidates = refined.get("role_candidates") or {}

    # ⚠️ 2026-08-14 세션34(사용자 지적, `folded_cascode`의 M7/M8 계기, 이후 같은 세션에서
    # `idioms.propagate_reference_role_through_cascode()`로 일반화 재배선) -- role
    # 하나만 보면 M8(`AMPLIFYING`, 게이트 Vg7이 M5 폴딩 노드와 겹쳐 SIGNAL로 분류됨)이
    # 위 정적 레퍼런스 집합에서 빠진다. 하지만 M8은 `M10`(role=`CURRENT_SOURCE`, 정적
    # 레퍼런스) 위에 물리적으로 직렬 적층된(`idioms.m_cascode()`의 `cascode-stack`) 소자다
    # -- 아래에 정적 레퍼런스가 있으면 그 위에 캐스코드로 쌓인 소자도 "이 전류경로가 고정
    # 레퍼런스에서 온다"는 성질을 물려받는다. "무엇을 정적 레퍼런스로 볼지"(아래
    # `_static_ref_roles`)는 이 호출부의 판단이라 그대로 seed로 넘긴다 -- 전파 알고리즘
    # 자체(다단 캐스코드 고정점 반복)는 소비자 무관 순수 그래프 유틸리티라
    # `idioms.py`(`m_cascode()` 바로 옆)로 옮겨 재사용 가능하게 했다.
    static_like_roles = {n for n, r in role_candidates.items() if r in _static_ref_roles}
    if _idioms_lcmf is not None:
        _devs_lcmf = _to_analog_grammar_devs(transistors)
        _cls_lcmf, _imp_lcmf, _ = _netclass_lcmf.classify_nets(
            _devs_lcmf, refined["final_inputs"], outputs, biases, feedbacks, clocks)
        _all_matches_lcmf = _idioms_lcmf.match_all(_devs_lcmf, _cls_lcmf, _imp_lcmf, role_candidates)
        static_like_roles = _idioms_lcmf.propagate_reference_role_through_cascode(
            _all_matches_lcmf, static_like_roles, _devs_lcmf)
        # ⚠️ 6번째 소스(2026-08-15 세션35, 사용자 통찰 -- "stacked current mirror의 output
        # impedance가 active load 값이 되는 거다, 전형적인 stacked current mirror 형태다")
        # -- m_mirror()의 active_load_legs는 다리 "자기 자신의" 드레인이 HIGH_Z인지만
        # 본다. 그 다리 위에 캐스코드가 쌓여 있으면(예: folded_cascode의 M10 위 M8) 자기
        # 드레인은 그 캐스코드의 소스라 정상적으로 LOW_Z로 분류돼(netclass.classify_nets()
        # §1f) 놓친다 -- 캐스코드 스택 꼭대기까지 걸어 올라가 진짜 이득노드를 다시 찾는다
        # (idioms.find_cascoded_active_load_legs(), _cascode_lo_up_pairs() 공유).
        # `leg`(비율을 정하는 아래층, 예: M10)는 그대로 두고 `top`(임피던스를 만드는
        # 위층, 예: M8)만 gain 후보에 추가한다 -- 아래 3가지 제외조건(구조 대칭/diffpair
        # branch-load/signal-referenced 파트너)은 "비율 정밀도가 그 소자 자신의 W/L에
        # 달려있다"는 전제로 만들어졌는데, top은 그 전제가 성립하지 않는다(비율은 이미
        # leg에서 확정됨, top의 역할은 순수 임피던스 부스트) -- 그래서 top엔 그 제외를
        # 적용하지 않는다(사용자 확정: "gain이니 gain으로 봐야 한다", folded_cascode의
        # M8이 branch_load_partner_candidates에 걸려도 gain이 맞음을 실측 확인).
        cascoded_active_load_legs = _idioms_lcmf.find_cascoded_active_load_legs(
            _devs_lcmf, _all_matches_lcmf, _imp_lcmf, cls=_cls_lcmf)
    else:
        cascoded_active_load_legs = set()
    # 2026-08-15(리팩터, 사용자 지적 -- "seed name 주는 helper를 이미 만들어뒀는데 재사용
    # 안 했다") -- find_cascoded_active_load_legs()가 이제 propagate_reference_role_
    # through_cascode()를 내부에서 재사용해서 "새로 캐스코드로 편입된 소자"만 반환한다
    # (leg==top, 즉 캐스코드가 전혀 없는 경우는 자동으로 빠짐 -- 그런 소자는 이미 위
    # active_load_leg_candidates 경로가 제외조건까지 정확히 적용해 처리하는 대상이다,
    # current_reuse_telescopic_ota의 M12/M13/M21/M22·nmcnr_amplifier의 M109/M204가
    # 실제 사례). 그래서 여기서 제외조건 없이 그대로 합쳐도 안전하다(idioms.py의
    # find_cascoded_active_load_legs() docstring 참고 -- 예전엔 이 필터를 여기서 손으로
    # 다시 걸어야 했는데, 그러다 실제로 한 번 빠뜨려 회귀를 낸 적이 있다 -- 재사용이
    # 그 사고 클래스 자체를 구조적으로 없앤다).
    gain_role_candidates |= cascoded_active_load_legs

    matching_candidates = find_matching_candidates(transistors)
    for group in matching_candidates["diff_pair"].values():
        if len(group) == 2:
            _propose_pair(group[0].name, group[1].name, "offset", True, "layer1_diff_pair_fallback")
    for group in matching_candidates["current_mirror"].values():
        if (len(group) == 2 and any(t.gate == t.drain for t in group)
                and all(name in static_like_roles for name in (t.name for t in group))):
            # diode-connected 참조가 실제로 확인된 2-소자 미러 -- 위와 동일 근거로 True
            # (folded_cascode의 M9/M10, M7/M8 실측: 둘 다 declared current_forced=True).
            _propose_pair(group[0].name, group[1].name, "ratio", True,
                           "layer1_current_mirror_fallback(diode-connected 소자 확인됨, "
                           "role=고정 레퍼런스류 확인됨)")

    compensation_names = set(compensation_stage_devices or [])

    device_roles_proposals = {}
    review_needed = []

    # ⚠️ 5번째 소스(2026-08-20, 세션40 -- `.ai/context.md` 세션39 §4① "자동 탐지 엔진"
    # 이월 항목) -- `device_roles.vds_match_vgs_of`(세션38 신설, M203/M204 계기) 자동 제안.
    # `compensation.stage_devices` 소속 Y의 gate net이 다른 소자 X의 drain net과 같고
    # X.source==Y.source면(오프셋 없이 VGS(Y)=VDS(X)가 KVL로 강제됨 -- 이 세션 이전에
    # M301/M204·M109/M201(nmcnr_amplifier)·M4/M6(two_stage_ota, theta feed 레벨)·
    # M10/M16(current_reuse_telescopic_ota)을 전부 손으로 이렇게 유도해 확정한 것과
    # 정확히 같은 판정 기준 -- `.ai/context.md` 세션38~39 참고), X에 vds_match_vgs_of를
    # 제안한다.
    #
    # ⚠️ 반드시 걸러야 하는 가짜양성(사용자 지적, 이 함수 설계 논의 중 발견) -- 평범한
    # current mirror(Xref diode-connected, `Xref.gate==Xref.drain`)도 이 조건에 걸린다:
    # Xref가 diode-connected면 정의상 `Xref.gate==Xref.drain`이므로, 그 gate를 공유하는
    # 미러 다리(=Y, 우연히 compensation 소속이면) 입장에서 `Y.gate==Xref.drain`이 항상
    # 참이 된다 -- 그런데 이건 "X가 다음 단을 구동"이 아니라 "X와 Y가 같은 게이트를
    # 공유하는 미러쌍"이라는 전혀 다른 관계고, 이미 다른 메커니즘(`gm_id_match_vgs_of`,
    # `signal_referenced_mirror_legs`)이 담당한다 -- diode-connected인 X는 자기 자신의
    # 구조로 이미 `VDS(X)=VGS(X)`가 강제돼 있어 헤드룸으로 또 강제할 대상이 아니다.
    # `X.gate==X.drain`이면 제안하지 않고 건너뛴다.
    # ⚠️ 2026-08-20 구현 중 실측으로 발견 -- "X.drain==Y.gate인 소자가 몇 개인가"로 먼저
    # 걸러내면(초안) 실제 4개 회로 전수 테스트에서 **매번** 여러 개가 나와 하나도 제안을
    # 못 냈다(폴디드/캐스코드 노드는 원래 여러 소자가 같은 net에 물림 -- 예: nmcnr의
    # `NodeS2`엔 `M202`(source=vdd)/`M204`(source=vss) 둘 다 drain이 물려있다). 진짜
    # 구별 신호는 개수가 아니라 **source가 Y와 같은가**다(M301.source=vss==M204.source,
    # M202.source=vdd는 다름) -- 그래서 원시 drain-매치 목록에 아래 필터(source 일치/
    # diode 아님/compensation 아님/vertical_stack_id 있음/기존 선언 없음)를 **전부** 적용한
    # 뒤에도 후보가 둘 이상 남을 때만 진짜 모호한 것으로 본다(review_needed).
    vds_match_vgs_of_candidates = {}
    for y_name in compensation_names:
        y = by_name.get(y_name)
        if y is None or y.gate in _RAIL_NETS:
            continue
        raw_drivers = [x for x in transistors if x.name != y.name and x.drain == y.gate]
        if not raw_drivers:
            continue
        valid = []
        excluded_notes = []
        for x in raw_drivers:
            if x.gate == x.drain:
                continue  # diode-connected 미러 레퍼런스 -- 다른 메커니즘(gm_id_match_vgs_of)의 영역, 조용히 제외
            if x.source != y.source:
                continue  # 오프셋 없는 VGS(Y)=VDS(X) 전제가 안 맞음(예: M202) -- 조용히 제외
            if x.name in compensation_names:
                excluded_notes.append(
                    f"{x.name}도 compensation.stage_devices 소속이라 방향(어느 쪽이 진짜 AC "
                    f"스펙이고 어느 쪽이 헤드룸 상수인지)을 태그만으론 자동 판정 불가"
                    f"(two_stage_ota의 M4/M6 실례 -- 둘 다 authoritative 태그가 있었지만 M4는 "
                    f"실제로 하드코딩 placeholder였다, `.ai/context.md` 세션38 §1-⑯ 참고) -- "
                    f"사람이 실제 theta feed의 _L_source 근거를 직접 확인해야 한다.")
                continue
            x_vsid = (device_roles.get(x.name) or {}).get("vertical_stack_id")
            if not x_vsid:
                excluded_notes.append(
                    f"{x.name}에 vertical_stack_id가 없어 헤드룸 루프를 안 탄다 -- device_"
                    f"roles 레벨 vds_match_vgs_of는 여기선 적용 안 됨(선언해도 조용히 무시됨). "
                    f"이 소자는 theta feed로 sizing되는 쪽일 가능성이 높다 -- 적절한 자리는 "
                    f"`_feed_metric_stage_budget()`의 theta feed 레벨 vds_match_vgs_of"
                    f"(two_stage_ota의 M4/M6, `.ai/context.md` 세션38 §1-⑳(b) 참고).")
                continue
            # 2026-08-20 실측으로 발견(위 vertical_stack_id 체크만으론 부족했던 케이스) --
            # X가 `vertical_stack_id`를 가지고 있어도, `metric_stage_budget`/B/C타입 theta
            # feed가 헤드룸 루프보다 **먼저** 실행돼 그 소자의 vds를 이미 채워버리면(실제
            # 사례: two_stage_ota의 M4 -- `vertical_stack_id="stage1"`이 있는데도
            # `L_mirror_M3` feed가 vds를 먼저 정함) 헤드룸 pre-pass의 "이미 vds 있으면
            # skip" 가드에 걸려 device_roles 레벨 제안이 조용히 무시된다(적용해도 죽은
            # 선언). `find_authoritative_sizing_devices()`(같은 파일, `load_topology()`
            # 호출부가 넘겨줌)로 이 경우도 걸러낸다.
            if x.name in (vds_theta_authoritative or ()):
                excluded_notes.append(
                    f"{x.name}는 theta feed(metric_stage_budget/B/C)로 vds/gm_id가 헤드룸 "
                    f"루프보다 먼저 정해지는 소자다(`find_authoritative_sizing_devices()` "
                    f"보호 대상) -- device_roles 레벨 vds_match_vgs_of를 선언해도 pre-pass의 "
                    f"'이미 vds 있으면 skip' 가드에 걸려 조용히 무시된다(죽은 선언). 적절한 "
                    f"자리는 그 theta feed 자신의 vds_match_vgs_of dict(`_feed_metric_stage_"
                    f"budget()`, two_stage_ota의 M4/M6이 실제 사례).")
                continue
            x_existing = device_roles.get(x.name) or {}
            if any(x_existing.get(f) for f in ("vds_match_vgs_of", "same_as_device",
                                                "budget_reference_device")):
                continue  # 이미 다른 KVL 관계가 선언돼 있음(declared=review완료) -- 조용히 안 건드림
            valid.append(x)
        if len(valid) == 1:
            x = valid[0]
            if x.name in vds_match_vgs_of_candidates and vds_match_vgs_of_candidates[x.name] != y.name:
                review_needed.append({
                    "device": x.name,
                    "note": f"{x.name}이 서로 다른 compensation 소자 여럿의 gate를 구동하는 "
                            f"것처럼 보임({vds_match_vgs_of_candidates[x.name]!r} vs {y.name!r}) "
                            f"-- 자동 판정 불가, vds_match_vgs_of 제안 보류."})
                del vds_match_vgs_of_candidates[x.name]
            else:
                vds_match_vgs_of_candidates[x.name] = y.name
        elif len(valid) > 1:
            review_needed.append({
                "device": y.name,
                "note": f"gate net {y.gate!r}=drain, source={y.source!r}까지 일치하는 진짜 "
                        f"후보가 여럿({[v.name for v in valid]}) -- 어느 쪽이 진짜 구동 소자인지 "
                        f"자동 판정 불가, vds_match_vgs_of 제안 보류."})
        elif excluded_notes:
            for note in excluded_notes:
                review_needed.append({"device": y.name, "note": note})

    # ⚠️ 6번째 소스(2026-08-20 세션41 연속 -- 사용자 지시 "이건 json의 role을 생성하는
    # 함수에서 해야 하는 것 아닌가") -- `device_roles.budget_reference_device` 자동 제안.
    # 계기: `current_reuse_telescopic_ota`의 Vom측(M9a/M9b/M10)엔 세션39가 이미 이 관계를
    # 손으로 유도해 선언해뒀는데, 완전히 대칭인 Vop측(M18a/M18b/M19)엔 빠져 있었다(세션41이
    # `_verify_group_kvl_sum()`으로 39mV KVL 불일치를 실측으로 찾아냄, `.ai/context.md`
    # 세션41 참고) -- 사람이 매 회로 손으로 대칭 짝을 감사하는 대신, 이미 5번째 소스가
    # `vds_match_vgs_of`에 쓰는 것과 같은 "netlist connectivity로 KVL 관계를 판정" 원칙을
    # 여기도 적용한다.
    #
    # 판정 기준: X가 `vertical_stack_id`(헤드룸 관리 대상) 소속이고, X의 "열린 단자"
    # (자기 그룹 내 다른 소자의 단자와도, 레일과도 안 닿는 유일한 단자)가 소자 Y의 drain과
    # 같은 net이고 Y.source가 레일이면, X가 속한 그룹의 진짜 헤드룸 예산은 vdd 전체가
    # 아니라 vdd-VDS(Y)다(M9a.drain=Vop1=M10.drain(M10.source=gnd)이 원형 사례,
    # `_resolve_vertical_group()`의 `budget_reference_device` 계약과 동일 판정 기준).
    # X에 `budget_reference_device=Y`를 제안한다(선언은 소자 단위 필드지만 `group_ref_
    # device[vsid]`로 그룹 전체에 적용됨, sizing_recipe.py 참고).
    #
    # 이미 다른 KVL 관계(budget_reference_device/same_as_device/vds_match_vgs_of)가
    # declared면 건드리지 않는다. Y가 diode-connected여도 상관없다 -- X는 Y의 gate가
    # 아니라 drain(=VDS(Y))만 참조하므로 5번째 소스(gate==drain 가짜양성)와 다른 축이다.
    # ⚠️ 2026-08-20 실측으로 발견(사용자 질문 "이 규칙이 일반적인가"에 답하며 정정) --
    # "Y.source가 레일인 후보가 유일한가"만 보면 불충분하다: 그 open_net 자체를 **다른
    # 비-레일 소자도 같이 건드리고 있으면**(예: Vom1을 M2a/M3a/M18a/M19 네 소자가 전부
    # drain으로 공유) 그 순간부터 이 노드 전압은 여러 branch의 KCL이 동시에 정하는 값이라
    # "이웃 하나의 VDS로 유일하게 결정된다"는 전제 자체가 깨진다(로컬 연결성만으론 판정
    # 불가 -- 일반 원칙, 이 회로 전용 아님). 그래서 open_net을 drain으로 갖는 소자가
    # **X를 제외하고 정확히 1개**(=Y 하나뿐)일 때만 제안한다 -- 순수 2-소자 직렬 링크로
    # 확인된 경우만 자동 판정하고, 3개 이상 모이는 노드(fold/merge 노드)는 애매함을
    # 인정하고 review_needed로 넘긴다.
    # ⚠️ 2026-08-20 실측으로 발견(일반 원칙) -- 어떤 소자 R이 이미 다른 그룹의
    # `budget_reference_device`로 declared돼 있으면(예: M66은 M60의 참조 대상으로 이미
    # 선언됨), R 자신은 **또 다른 소자를 참조하도록 제안하면 안 된다** -- R은
    # `_referenced_singleton` 우회(sizing_recipe.py)로 이미 role 기반 작은 값을 받는
    # 쪽이지, "vdd - 참조.vds"로 나머지를 받는 쪽이 아니다. 이 구분을 안 하면 R이
    # 거꾸로 자신을 참조하는 소자를 다시 참조하는 2-사이클이 생긴다(M66→M60,
    # M60→M66이 서로를 기다리는 실제 데드락으로 재현됨).
    # 2026-08-24(세션42) -- budget_reference_device가 소자 1개(str)뿐 아니라 여러 개
    # (list, sizing_recipe.py의 _sum_ref_vds() 확장과 짝)도 선언할 수 있게 됐다 --
    # set comprehension에 list를 그대로 넣으면 unhashable로 즉시 TypeError이므로 풀어서
    # 담는다.
    existing_referenced = set()
    for v in device_roles.values():
        if not isinstance(v, dict):
            continue
        ref = v.get("budget_reference_device")
        if not ref:
            continue
        existing_referenced.update(ref) if isinstance(ref, list) else existing_referenced.add(ref)
    budget_reference_device_candidates = {}
    for x in transistors:
        x_existing = device_roles.get(x.name) or {}
        x_vsid = x_existing.get("vertical_stack_id")
        if not x_vsid:
            continue
        if any(x_existing.get(f) for f in ("budget_reference_device", "same_as_device",
                                            "vds_match_vgs_of")):
            continue
        if x.name in existing_referenced:
            continue
        own_group_nets = {n for m in transistors
                           if m.name != x.name
                           and (device_roles.get(m.name) or {}).get("vertical_stack_id") == x_vsid
                           for n in (m.source, m.drain)}
        open_terminals = [n for n in (x.source, x.drain)
                           if n not in _RAIL_NETS and n not in own_group_nets]
        if len(open_terminals) != 1:
            continue  # 그룹 안에서 완결되거나(0개) 경계가 하나가 아니면(2개) 단일 참조로 표현 불가
        open_net = open_terminals[0]
        other_drain_touches = [y for y in transistors if y.name != x.name and y.drain == open_net]
        if len(other_drain_touches) != 1:
            if len(other_drain_touches) > 1:
                review_needed.append({
                    "device": x.name,
                    "note": f"'{x.name}'의 열린 단자({open_net!r})를 drain으로 공유하는 소자가 "
                            f"{len(other_drain_touches)}개({[d.name for d in other_drain_touches]}) "
                            f"-- 이 노드는 여러 branch가 합류하는 지점이라 이웃 하나의 VDS로 유일하게 "
                            f"결정된다고 볼 수 없다(로컬 연결성만으론 판정 불가) -- budget_reference_"
                            f"device 자동 판정 보류, fold_group 등 다른 관계일 수 있음."})
            continue
        y = other_drain_touches[0]
        if y.source not in _RAIL_NETS:
            continue
        # ⚠️ 2026-08-20 실측으로 발견(일반 원칙, 이 회로 전용 아님) -- X.source==Y.source면
        # 두 소자가 "직렬로 이어진다"가 아니라 **같은 레일에서 같은 net으로 나란히 연결된
        # 평행 소자**라는 뜻이다(예: M6.source=vdd,drain=Vx / M7.source=vdd,drain=Vx --
        # 실제로는 same_as_device 관계, X 아래로 예산이 이어지는 게 아니라 X/Y가 병렬로
        # Vx를 같이 구동한다). 이 경우 Y를 "X 컬럼 아래의 나머지 예산"으로 취급하면
        # 순환 참조가 생긴다(M7.same_as_device=M6인데 M6.budget_reference_device=M7을
        # 제안하면 서로가 서로를 기다림, 실측 재현). 진짜 직렬(M9a→M10, M18b→M17)은
        # X.source와 Y.source가 항상 다르다(X는 자기 그룹 안쪽 노드에서, Y는 레일에서
        # 시작) -- 이 차이로 평행 소자를 걸러낸다.
        if x.source == y.source:
            continue
        if (device_roles.get(y.name) or {}).get("vertical_stack_id") == x_vsid:
            continue
        budget_reference_device_candidates[x.name] = y.name

    # ⚠️ 7번째 소스(2026-08-20 세션41 연속) -- `device_roles.fold_group` 자동 제안. 계기:
    # `current_reuse_telescopic_ota`의 `diffpair_top_a`(M1a/M2a, source=Vx)/`diffpair_
    # bottom_a`(M3a/M4a, source=Vy)는 vdd~gnd 단일 컬럼이 아니라 폴딩 노드(Vom1)에서
    # 합류하는 두 개의 독립 컬럼인데, 이 사실이 선언 어디에도 없어 `_verify_group_kvl_
    # sum()`이 "diffpair_bottom_a 합=1.1V(!=vdd)"로 거짓 양성을 냈다(세션41). `_fold_
    # group_check()`(세션35, connectivity로 fold_group 정당성을 검증하는 기존 함수)가
    # 쓰는 것과 정확히 같은 판정 근거를 여기서도 자동 제안에 적용한다: 서로 다른
    # `vertical_stack_id` 소속 X/Y가 종류(kind)가 반대이고 drain이 같은 net을 공유하면
    # (예: M2a(pmos).drain=Vom1=M3a(nmos).drain) 폴딩 노드에서 합류하는 구조다 -- 둘
    # 다에 같은 `fold_group` 태그(공유 net 이름 기반, 결정론적이라 재현 가능)를 제안한다.
    #
    # ⚠️ 2026-08-20 실측으로 발견(budget_reference_device 6번째 소스와 동일한 일반
    # 원칙 -- 이 회로 전용 아님) -- Vom1처럼 **3개 이상**의 소자가 같은 net을 drain으로
    # 공유하면(M2a/M3a/M18a/M19 넷 다) "이 둘만 폴딩 노드에서 합류한다"고 국소적으로
    # 단정할 수 없다 -- 그 노드에 물린 다른 소자와의 관계(예: M18a/M19의 budget_
    # reference_device 관계)와 뒤섞여 어느 관계가 진짜인지 로컬 연결성만으론 판정
    # 불가능하다. 그 net을 drain으로 갖는 소자가 **X/Y 딱 둘뿐**일 때만(합=정확히 2)
    # 순수 2-branch fold로 확정하고 제안한다 -- 3개 이상이면 review_needed로 넘긴다
    # (사람이 더 넓은 구조를 보고 판단할 몫).
    fold_group_candidates = {}
    _fold_seen_pairs = set()
    for x in transistors:
        x_existing = device_roles.get(x.name) or {}
        x_vsid = x_existing.get("vertical_stack_id")
        if not x_vsid or x_existing.get("fold_group"):
            continue
        own_group_nets = {n for m in transistors
                           if m.name != x.name
                           and (device_roles.get(m.name) or {}).get("vertical_stack_id") == x_vsid
                           for n in (m.source, m.drain)}
        if x.drain in _RAIL_NETS or x.drain in own_group_nets:
            continue
        all_drain_touches = [y for y in transistors if y.name != x.name and y.drain == x.drain]
        if len(all_drain_touches) != 1:
            if len(all_drain_touches) > 1:
                review_needed.append({
                    "device": x.name,
                    "note": f"'{x.name}'의 drain({x.drain!r})을 공유하는 소자가 "
                            f"{len(all_drain_touches)}개({[d.name for d in all_drain_touches]}) -- "
                            f"단순 2-branch 폴딩 노드가 아니라 3개 이상이 모이는 지점이라 로컬 "
                            f"연결성만으론 fold_group 판정 불가, 제안 보류."})
            continue
        y = all_drain_touches[0]
        if y.kind == x.kind:
            continue  # 같은 kind끼리 drain 공유는 fold가 아니라 다른 관계(예: 값-동일 그룹)의 영역
        # ⚠️ 2026-08-20 실측으로 발견(일반 원칙, 이 회로 전용 아님) -- Y.source가 레일이면
        # 이건 폴딩(독립된 두 branch의 합류)이 아니라 **직렬 링크**다(예: Vg15에서
        # M8(source=vdd,drain=Vg15)/M9b(source=Vop1,drain=Vg15)이 만나는 건 M8이 위에서
        # 내려오고 M9b가 그 노드에서 자기 컬럼을 이어가는 것 -- budget_reference_device의
        # 영역이지 fold_group이 아니다, 6번째 소스가 이미 이 관계를 정확히 담당). 진짜
        # 폴딩 노드(Vom1의 M2a/M3a)는 양쪽 다 source가 레일이 아니라 각자의 그룹 안쪽
        # 노드에서 온다 -- 이 차이로 "직렬"과 "폴딩"을 구분한다.
        if y.source in _RAIL_NETS:
            continue
        y_existing = device_roles.get(y.name) or {}
        # 2026-08-24(세션42, 세션41이 남긴 회귀 재현 중 발견 -- 일반 원칙, 이 회로
        # 전용 아님) -- X/Y 중 한쪽이 이미 다른 KVL 관계(budget_reference_device/
        # same_as_device/vds_match_vgs_of)로 **서로를** 직접 참조하도록 선언돼 있으면,
        # 그 관계 자체가 "이 둘은 하나의 연속된 vdd-gnd 컬럼을 두 vertical_stack_id로
        # 쪼갠 것"이라는 뜻이다(Y.source가 레일인 경우와 물리적으로 동일한 "직렬" 판정
        # -- 다만 T가 T2 위에 한 단 더 있어 Y.source 자체는 레일이 아닌 경우까지
        # 잡아낸다). fold 후보로 다시 제안하면 이미 확정된 series 관계와 모순되는
        # fold_group을 덧씌워, 그 vertical_stack_id가 헤드룸 검증(_verify_group_kvl_
        # sum())에서 제외되는 부작용이 생긴다(재현: `_fpw_test` 합성 fixture의 F/T2 --
        # F.budget_reference_device="T2"인데도 드레인 공유만으로 fold_group이 잘못
        # 제안되어 grpB가 정상 예산 대신 min_vds만 받는 회귀, `.ai/context.md` 세션41
        # §5/세션42 참고).
        # 2026-08-24 -- budget_reference_device가 list일 수도 있어졌으므로(위 참고) "가리킴"
        # 판정도 문자열 동일 비교 하나가 아니라 list 소속까지 봐야 한다.
        def _points_at(existing, field, target_name):
            v = existing.get(field)
            return v == target_name or (isinstance(v, list) and target_name in v)
        _kvl_link_fields = ("budget_reference_device", "same_as_device", "vds_match_vgs_of")
        if (any(_points_at(x_existing, f, y.name) for f in _kvl_link_fields)
                or any(_points_at(y_existing, f, x.name) for f in _kvl_link_fields)):
            continue
        y_vsid = y_existing.get("vertical_stack_id")
        if not y_vsid or y_vsid == x_vsid:
            continue
        pair_key = tuple(sorted((x.name, y.name)))
        if pair_key in _fold_seen_pairs:
            continue
        _fold_seen_pairs.add(pair_key)
        tag = f"{x.drain}_fold"
        fold_group_candidates[x.name] = tag
        fold_group_candidates[y.name] = tag

    for t in transistors:
        name = t.name
        existing = device_roles.get(name) if isinstance(device_roles.get(name), dict) else {}
        proposal = {}
        if existing.get("gm_id_match_vgs_of"):
            # 2026-08-19(세션38, sizing_recipe.py의 device_roles.gm_id_match_vgs_of 2차 pass
            # 신설과 짝 -- nmcnr_amplifier M204 계기) -- gm_id_role과 gm_id_match_vgs_of는
            # "이 소자의 gm/ID를 어떻게 정하는가"에 대한 상호배타적인 두 방법이다(우선순위
            # 아니라 양자택일 -- companion의 실제 VGS로 역산하는 쪽이 role 기반 독립 탐색보다
            # 항상 더 정확하다, 물리적으로 게이트·소스가 공유된 미러쌍이라는 뜻이므로). 이미
            # declared gm_id_match_vgs_of가 있으면 여기서 gm_id_role을 제안하지 않는다 --
            # 안 그러면 declared 필드가 "review 안 됨"으로 오탐돼(require_device_roles_
            # reviewed() 회귀, 실측 발견) 매 load마다 불필요한 리뷰 게이트에 걸린다.
            pass
        elif name in gain_role_candidates:
            proposal["gm_id_role"] = "gain"
        elif name in signal_referenced_mirror_legs:
            # diode-connected 레퍼런스 자신의 노드가 SIGNAL(고정 BIAS 아님) -- 목적이
            # 전류비가 아니라 신호-종속 전압/전류 관계를 그대로 복사하는 것이므로 diffpair/
            # 구조 대칭이 없어도 matching이 맞다(사용자 지적, `nmcnr_amplifier`의 M203/M204
            # 계기 -- 위 docstring 참고). `gm_id_role_candidates`가 별도로 값을 못 내는
            # 소자(구조 대칭 파트너 없음)에도 명시적으로 matching을 제안한다.
            proposal["gm_id_role"] = "matching"
        elif name in gm_id_role_candidates:
            proposal["gm_id_role"] = gm_id_role_candidates[name]
        if name in L_role_candidates:
            proposal["L_role"] = L_role_candidates[name].get("L_role")
        if headroom_role_candidates.get(name) is not None:
            proposal["headroom_role"] = headroom_role_candidates[name]
        if name in vds_match_vgs_of_candidates:
            proposal["vds_match_vgs_of"] = vds_match_vgs_of_candidates[name]
        if name in budget_reference_device_candidates:
            proposal["budget_reference_device"] = budget_reference_device_candidates[name]
        if name in fold_group_candidates:
            proposal["fold_group"] = fold_group_candidates[name]
        if not proposal:
            continue
        conflicts = {f: (existing.get(f), v) for f, v in proposal.items()
                     if f in existing and existing[f] is not None and existing[f] != v}
        if conflicts:
            # 2026-08-20(세션40, vds_match_vgs_of 5번째 소스 구현 중 실측으로 발견한 버그
            # 수정) -- 예전엔 필드 하나라도 충돌하면 그 소자의 proposal 전체를 통째로
            # 버렸다(`continue`). 이 함수가 한 소자에 여러 독립적 필드(gm_id_role/L_role/
            # headroom_role/vds_match_vgs_of)를 동시에 제안할 수 있게 되면서, 이 전체
            # 버림이 실제 사고를 냈다 -- nmcnr_amplifier의 M109는 `gm_id_role="load"`(사람이
            # 구조적 기본값 "matching" 대신 직접 override한 값)라 gm_id_role 필드만 충돌
            # 나는데, 완전히 무관한 새 `vds_match_vgs_of="M201"` 제안까지 같이 버려져서
            # 아예 제안 자체가 안 나왔다(실측 확인). 이제 **충돌한 필드만** 제외하고
            # 나머지 필드는 그대로 제안한다 -- 사람이 override한 값을 조용히 덮어쓰지
            # 않는다는 원칙은 그대로 지키면서(그 필드는 여전히 review_needed로만 보고),
            # 무관한 다른 필드까지 연좌 책임으로 막지는 않는다.
            review_needed.append({"device": name, "field_conflicts": conflicts,
                                    "note": "이미 선언된 값과 제안이 달라 그 필드만 자동 "
                                            "반영하지 않음(다른 무관한 필드는 그대로 제안)"})
            proposal = {f: v for f, v in proposal.items() if f not in conflicts}
        if not proposal:
            continue
        device_roles_proposals[name] = proposal
        if name in compensation_names:
            review_needed.append({"device": name, "note": "compensation.stage_devices 소속 -- "
                                    "gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_"
                                    "SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 "
                                    "적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 "
                                    "막을 필요는 없음)."})

    # ⚠️ 2026-08-14 세션34 정정(사용자 지시로 "단일 공유 net vs 독립 net" 구분을 새 신호로
    # 일반화하려다 발견) -- 파트너(구조 대칭 또는 diffpair branch-load) 유무만으로 이미
    # "matching이 구조적으로 맞다"가 결정된다는 게 재검토로 드러났다: 두 메커니즘 다 정의상
    # "이 소자가 differential balance 역할을 한다"는 사실을 이미 내포한다 -- 구조 대칭
    # partner는 주변 서브그래프 전체가 좌우대칭이라는 뜻이고, diffpair branch-load partner는
    # 정의상 differential pair의 두 branch에 앉은 부하다. 실측 2건(`two_stage_ota`의 M3/M4,
    # `current_reuse_telescopic_ota`의 M13/M22 -- 각각 Vom쪽/Vop쪽 class-AB quiescent
    # 바이어스를 독립 생성해 서로 다른 net(N14a14b/N24b23a)으로 넘기는 것까지 실측 확인,
    # `.ai/context.md` 세션34 참고) 전부 이 원칙과 일치, 반례 없음 -- "파트너가 있는데
    # gain이 나을 수도 있다"는 이전 버전의 불확실한 표현은 근거 없는 추측이었다(정정).
    # `gm_id_role_candidates`가 이미 이런 소자에 "matching"을 정확히 제안하므로(구조 대칭
    # partner가 있으면 자동으로 "matching", `_propose_gm_id_roles()` 참고) 여기서 추가로
    # 할 일은 없다 -- 이 review_needed 항목은 그 근거를 투명하게 남기는 정보성 기록일 뿐,
    # 사람 판단을 요구하지 않는다.
    # ⚠️ 2026-08-14 세션34 후속 추가(사용자 지적, `nmcnr_amplifier`의 M203/M204 계기) --
    # diffpair/구조 대칭이 전혀 없어도 "matching"이 맞는 세 번째 경로: diode-connected
    # 레퍼런스 자신의 노드가 SIGNAL(고정 BIAS 아님)이면, 목적이 전류비가 아니라 그
    # 신호-종속 전압/전류 관계를 그대로 "복사"하는 것이라 미러 다리도 matching이 필요하다
    # (예: `M203`이 `M201`의 신호 스윙을 그대로 받는 이득단의 능동부하 자신이면서
    # diode-connected -- `M204`는 그 전압을 그대로 복사해 `M301`을 구동). `M18_bg`/`M66`
    # (current_reuse_telescopic_ota)/`MN`/`MP`/`M9`(folded_cascode) 같은 고정 BIAS
    # 레퍼런스와 정반대(실측: 전부 BIAS, `nmcnr_amplifier`의 `M203`/`M108`만 SIGNAL).
    for name in sorted(active_load_leg_candidates - gain_role_candidates):
        sym_partner = (L_role_candidates.get(name) or {}).get("symmetry_partner")
        br_partner = branch_load_partner_candidates.get(name)
        sig_ref = signal_referenced_mirror_legs.get(name)
        if sym_partner:
            reason = (f"구조 대칭 partner={sym_partner}가 있음 -- 파트너 존재 자체가 "
                      f"differential balance 역할을 내포하므로")
        elif br_partner:
            reason = (f"diffpair branch-load partner={br_partner}가 있음 -- 파트너 존재 "
                      f"자체가 differential balance 역할을 내포하므로")
        else:
            reason = (f"diode-connected 레퍼런스({sig_ref})의 노드가 SIGNAL(고정 BIAS "
                      f"아님)이라 목적이 전류비가 아니라 신호-종속 전압/전류 복사이므로")
        review_needed.append({"device": name, "note": f"active-load 성격(레일 직결+HIGH_Z "
            f"드레인)인데 {reason} 'gain'이 아니라 'matching'이 구조적으로 맞다(실측 3건, "
            f"`two_stage_ota` M3/M4·`current_reuse_telescopic_ota` M13/M22·`nmcnr_"
            f"amplifier` M203/M204 전부 일치, 반례 없음) -- 정보성 기록일 뿐 별도 판단 "
            f"불필요, device_roles_proposals가 이미 'matching'을 정확히 제안 중."})

    tentative_pairs_meta = matching_pairs_meta + matching_pairs_proposals
    disp = check_symmetry_dispositions(transistors, tentative_pairs_meta, dispositions={})
    if disp.undisposed:
        review_needed.append({"undisposed_candidates": disp.undisposed,
                                "note": "제안으로도 못 채운 층위1/2 candidate -- current_forced 세분화는 "
                                         "sizing_roles/theta 선언이 있어야만 판단 가능하거나(예: 51소자 "
                                         "실회로의 Vbias1 8-소자 그룹), 그 외엔 사람 판단이 필요하다."})
    if disp.case_collisions:
        review_needed.append({"case_collisions": disp.case_collisions})

    return {
        "matching_pairs_proposals": matching_pairs_proposals,
        "device_roles_proposals": device_roles_proposals,
        "review_needed": review_needed,
        "diagnostics": {"promoted_inputs": refined["promoted_inputs"],
                          "final_inputs": refined["final_inputs"],
                          "structural_symmetry_unresolved": structural.unresolved},
    }


def apply_device_roles_gap_fill(topology_json_path: str, result: dict) -> dict:
    """`propose_device_roles_gap_fill()`의 순수 결과를 받아 **실제로 topology.json 파일을 읽고
    병합하고 다시 쓴다**(`symmetry.matching_pairs`/`device_roles` 갱신) -- I-3 정정 2(세션32)
    그대로: `vertical_stack_id`(층위4, `propose_vertical_stack_id_gap_fill()`)와 달리 이 필드들은
    사이징 결과에 직접 영향을 주므로 `load_topology()`의 메모리상 자동채움이 아니라 파일 자체를
    영구히 갱신하는 쪽을 사용자가 확정했다.

    이미 declared된 쌍/필드와 충돌하는 제안은 `propose_device_roles_gap_fill()` 단계에서 이미
    걸러져 있지만(review_needed로만 보고, proposals에는 안 실림), 방어적으로 여기서도 다시 한 번
    확인한다 -- 조용히 덮어쓰지 않는다.

    ⚠️ `json.dump(..., indent=2)`로 다시 쓰기 때문에, 원본 파일이 사람이 손으로 넣은 섹션 사이
    빈 줄 등 부가적 포맷팅을 갖고 있었다면 그 포맷팅은 사라진다(값 자체는 100% 보존 -- 모든
    `_comment`/`_correction_log_*` 긴 문자열은 원래도 줄바꿈 없는 단일 JSON 문자열이라 내용
    손실은 없다). 실제 라이브러리 파일에 적용하기 전에 diff를 사람이 검토할 것을 권장한다.

    반환: `{"applied_matching_pairs": [[a,b],...], "applied_device_roles": {device_name:
    {최종 저장된 entry}, ...}, "review_needed": result["review_needed"] 그대로 전달}`."""
    with open(topology_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_pairs = data["symmetry"]["matching_pairs"]
    existing_covered = set()
    for p in existing_pairs:
        for a, b in itertools.combinations(p["names"], 2):
            existing_covered.add(frozenset((a, b)))

    applied_pairs = []
    for p in result.get("matching_pairs_proposals", []):
        key = frozenset(p["names"])
        if key in existing_covered:
            continue
        existing_pairs.append(dict(p))
        existing_covered.add(key)
        applied_pairs.append(p["names"])

    device_roles = data.get("device_roles")
    if device_roles is None:
        device_roles = {}
    applied_roles = {}
    for name, proposal in result.get("device_roles_proposals", {}).items():
        entry = device_roles.get(name)
        if not isinstance(entry, dict):
            entry = {}
        skip = False
        for field, value in proposal.items():
            if field in entry and entry[field] is not None and entry[field] != value:
                skip = True
                break
        if skip:
            continue
        entry.update(proposal)
        entry.setdefault("vs", 0.0)
        device_roles[name] = entry
        applied_roles[name] = dict(entry)
    data["device_roles"] = device_roles or None

    with open(topology_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return {"applied_matching_pairs": applied_pairs, "applied_device_roles": applied_roles,
            "review_needed": result.get("review_needed", [])}


def find_authoritative_sizing_devices(meta: dict) -> set:
    """`gm_id_role`/`L_role`가 없어도(또는 있어도 무시돼도) 안전한 소자 이름 집합을
    `meta`(`load_topology()`의 반환값)만으로 계산한다 -- 2026-08-14, `_AUTHORITATIVE_L_
    SOURCES`/`_AUTHORITATIVE_GM_ID_SOURCES`(`sizing_recipe.py`)가 실제로 보호하는 소자와
    **반드시 같은 정의**여야 한다(실측으로 발견한 사고: `current_reuse_telescopic_ota`의
    `L_cascode` theta(`metric_stage_budget`) 대상 `M2a`/`M2b`/`M3a`/`M3b`에
    `propose_device_roles_gap_fill()`이 제안한 `L_role="mirror"`를 실제로 적용했더니, 당시
    `sizing_recipe.py`에 이 소자들을 보호하는 가드가 없어서 `select_L_by_role()`이 그
    theta의 그리드서치 결과를 조용히 덮어써 `gain_db`가 76.48->74.8로 떨어지는 회귀가
    실제로 발생했다 -- 이 함수는 그 사고를 `optimize_full_circuit_budget()` 실행 **전에**
    미리 잡아내는 `require_device_roles_reviewed()`의 재료다).

    포함 대상(전부 `sizing_recipe.py`의 `_evaluate()`가 `ctx.sized[name]["_L_source"]`를
    `compensation`/`replica`/`metric_stage_budget`/`gm_target_convention`으로 태그하는
    소자와 정확히 대응):
    - `compensation.stage_devices`(전부 flatten).
    - `sizing_roles.theta[].feeds.type`이 `"metric_stage_budget"`인 항목의 `devices`.
    - `sizing_roles.theta[].feeds.type`이 `"B"`인 항목의 `target`(N×ωc 컨벤션,
      `_feed_gm_target_convention()`).
    - `sizing_roles.theta[].feeds.type`이 `"C"`인 항목의 `target`(replica, `_feed_diode_
      stack_target()`) -- `L`만 보호되고 `gm_id`는 의도적으로 재검색 대상이지만(위
      함수 docstring 참고), 이 함수는 `gm_id_role`/`L_role` 둘 다 "리뷰 불필요"로 넓게
      잡는다(과잉 허용 방향 -- 그 소자의 `gm_id_role`은 구조 대칭 근거로 제안되는
      값이라 다른 confirmed 제안과 신뢰도가 다르지 않다, 안전-critical한 건 L 쪽이었다)."""
    out = set()
    comp = meta.get("compensation") or {}
    for grp in comp.get("stage_devices", []):
        out.update(grp)
    thetas = (meta.get("sizing_roles") or {}).get("theta") or []
    for t in thetas:
        feeds = t.get("feeds")
        if not isinstance(feeds, dict):
            continue
        ftype = feeds.get("type")
        if ftype == "metric_stage_budget":
            out.update(feeds.get("devices", []))
        elif ftype in ("B", "C"):
            target = feeds.get("target")
            if target is not None:
                out.add(target)
    return out


def find_unreviewed_device_roles(meta: dict) -> dict:
    """`load_topology()`가 `_device_roles_autofilled`로 노출하는 제안(=topology.json
    파일엔 아직 없고 이번 load 시점에 메모리상으로만 채워진 값) 중, `gm_id_role`/`L_role`
    필드이면서 `find_authoritative_sizing_devices()`의 보호를 못 받는 소자만 골라낸다.
    `headroom_role`/`vertical_stack_id`는 여기 안 걸린다(`select_L_by_role()`/`search_
    gm_id_for_role()`을 실제로 실행시켜 값을 바꾸는 필드가 아니라 크래시/오사이징 위험이
    질적으로 다르다 -- Test 45 회귀로 확인됨, `_propose_headroom_roles()` docstring 참고).

    2026-08-20(세션40, 사용자 지적으로 정정 -- "review가 필요한 것이 아니면 자동적용해야
    해. 앞선 설계도 그렇게 되어 있어. 구조적으로 명확한 것은 자동적용이라고") --
    `vds_match_vgs_of`(`propose_device_roles_gap_fill()`의 5번째 소스)는 여기서
    **gate하지 않는다**. 처음엔 "sizing 결과를 크게 바꿀 수 있다"는 이유로 무조건
    review 대상으로 넣었으나, 이건 `find_unreviewed_matching_pairs()`가 이미 정확히
    확립해둔 기준(`mirror`/`ratio`는 review 필요, `differential`은 "순수 KCL 물리
    법칙, 예외 없음"이라 review 불필요)과 어긋났다 -- "값에 영향을 준다"가 아니라
    "구조적으로 확정 가능한가(판단이 필요 없는 물리 법칙인가)"가 진짜 기준이다.
    `vds_match_vgs_of` 제안은 5번째 소스의 필터(X.source==Y.source/X가 diode 아님/
    X·Y 둘 다 compensation 소속 아님/X에 vertical_stack_id 있음/X가 theta-authoritative
    아님/후보 유일)를 **전부** 통과해야만 나온다 -- 이 필터를 통과한 뒤에는
    `VGS(Y)=VDS(X)`가 순수 KVL(같은 두 노드 사이 전압차는 물리적으로 하나뿐)이라
    `differential`과 동급으로 판단의 여지가 없다("gm_id_role='gain' vs 'matching'"류의
    설계 판단과는 성격이 다르다).

    반환: `{device_name: {"gm_id_role": value, ...}}` -- gm_id_role/L_role 중 실제로
    unreviewed인 필드만 포함(둘 다 없으면 그 소자는 키 자체가 없음). 비어 있으면 review
    없이 안전하게 `optimize_full_circuit_budget()`을 돌려도 된다는 뜻."""
    authoritative = find_authoritative_sizing_devices(meta)
    autofilled = meta.get("_device_roles_autofilled") or {}
    out = {}
    for name, proposal in autofilled.items():
        if name in authoritative:
            continue
        risky = {f: v for f, v in proposal.items() if f in ("gm_id_role", "L_role")}
        if risky:
            out[name] = risky
    return out


def find_unreviewed_matching_pairs(meta: dict) -> list:
    """`load_topology()`가 `_matching_pairs_autofilled`로 노출하는, 아직 topology.json에
    없는 매칭쌍 중 `differential`이 아닌 것만 골라낸다.

    ⚠️ 2026-08-14 신설(사용자 지적으로 발견한 실제 위험 -- "대칭적인 branch이면 branch
    전류가 같아야 하는것 아니야?"라는 질문에 답하며 두 가지를 재확인했다): (1)
    `propose_device_roles_gap_fill()`이 `mirror`/`structural_symmetry`/층위1 미러 폴백에
    제안하는 `current_forced`를 4개 실회로 전수 재조사 후 `True`로 정정했다(2-소자
    matching_pairs는 예외 없이 True였다, 위 함수 docstring 참고). (2) 그런데
    `sizing_recipe.py`의 `_evaluate()`(3963행 근처, "matching_pairs로 선언된 두 소자는
    반드시 같은 L을 써야")는 **`current_forced` 값과 무관하게 `pairs_meta`의 모든 쌍**에
    L 일치를 강제/전파한다 -- 즉 `current_forced=False`인 매칭쌍도 실제 sizing(L 값)에
    영향을 준다는 뜻이라, "matching_pairs는 게이트 대상이 아니다"(구버전 결론)는 틀렸다.

    안전한 유일한 카테고리는 `differential`(공유 tail의 KCL 분배, 순수 물리 법칙이라
    review 없이도 항상 참 -- `matching_sensitivity="offset"`은 이 프로젝트 전체에서
    `differential` 출처에만 붙는 값이라 기계적으로 식별 가능하다). 그 외(`mirror`/
    `structural_symmetry`/층위1 미러 폴백, 전부 `matching_sensitivity="ratio"`)는
    `current_forced=True`가 실측상 압도적으로 맞는 기본값이지만 100% 확실친 않다(M38처럼
    구조적 기본값을 사람이 전기적 이유로 override한 선례가 실제로 있음) -- 그래서 여전히
    review 대상이다.

    ⚠️ 2026-08-14 추가 정정: `ratio`(review 필요) 제안은 애초에 `load_topology()`가
    `meta["symmetry"]["matching_pairs"]`(=`all_matching_pairs`)에 자동 병합하지 않는다
    (그러면 review 없이도 sizing L 전파에 영향을 줄 수 있으므로) -- 그래서 `_matching_
    pairs_autofilled`가 아니라 `_matching_pairs_needs_review`(병합 안 된 순수 제안
    목록)에서 읽는다.

    반환: `[{"names",...}, ...]` -- unreviewed하고 review가 필요한 매칭쌍 리스트. 비어
    있으면 review 없이 안전하다는 뜻."""
    return list(meta.get("_matching_pairs_needs_review") or [])


def require_device_roles_reviewed(topology_json_path: str, meta: dict) -> None:
    """`optimize_full_circuit_budget()`이 실제 사이징(`select_L_by_role()`/`search_gm_id_
    for_role()`/matching_pairs L 전파)을 돌리기 **전에** 호출하는 게이트(2026-08-14,
    사용자 지시 -- "구조적으로 명확한 기능과 필요한 기능을 구분해서 사용자가 review해준
    적이 없는 부분은 error로 띄우고 일단 review를 받고 review받았다는 표시를 해서
    optimize함수가 실행되도록"). `device_roles`(gm_id_role/L_role)와 `matching_pairs`
    둘 다 검사한다(이름은 `device_roles`만 가리키지만 하위호환을 위해 유지, 실제로는
    `find_unreviewed_matching_pairs()`도 함께 확인).

    "review받았다는 표시"를 이 프로젝트에 새 스키마/플래그로 새로 만들지 않는다 -- **이미
    있는 declared-vs-autofilled 경계를 그대로 재사용**한다: `apply_device_roles_gap_fill()`
    로 topology.json에 실제로 값을 써넣는 행위 자체가 "사람이 검토하고 받아들였다"는
    증거이고(값을 그대로 받아들이든, 제안과 다른 값으로 직접 고쳐 쓰든 둘 다 "review완료"로
    친다), `find_unreviewed_device_roles()`/`find_unreviewed_matching_pairs()`가 그 반대
    (아직 파일엔 없고 메모리 제안으로만 존재)를 정확히 골라낸다. 새 상태를 만들지 않으므로
    "제안 내용이 나중에 바뀌면 리뷰가 stale해지는" 문제도 없다 -- 파일에 이미 쓰인 값과
    다른 새 제안이 나오면 그건 다시 자동 채움 목록에 안 잡히고(이미 declared라
    `propose_device_roles_gap_fill()`이 애초에 제안하지 않음, 대신 자동으로 다른 값을
    강제하지도 않음 -- 사람이 선언한 값이 최종이다) 그대로 유지된다.

    `find_authoritative_sizing_devices()`가 보호하는 소자(compensation/metric_stage_
    budget/B/C 대상)는 device_roles 쪽 게이트 대상에서 애초에 제외한다 -- `gm_id_role`/
    `L_role`이 있어도 `sizing_recipe.py`의 `_AUTHORITATIVE_L_SOURCES`/`_AUTHORITATIVE_
    GM_ID_SOURCES` 가드가 무시하므로 review를 요구할 이유가 없다("구조적으로 명확해
    review 불필요"의 첫 번째 카테고리). `matching_pairs` 쪽은 `differential`(순수 KCL
    물리 법칙, 예외 없음)만 두 번째 카테고리로 제외한다 -- 자세한 이유는 `find_unreviewed_
    matching_pairs()` docstring 참고.

    아무것도 unreviewed면 조용히 반환한다(에러 없음). 하나라도 있으면 정확히 무엇이
    unreviewed인지, 그리고 어떻게 review를 완료하는지(파일에 직접 쓰거나 `apply_device_
    roles_gap_fill()`을 호출)를 담은 `ValueError`를 낸다."""
    unreviewed_roles = find_unreviewed_device_roles(meta)
    unreviewed_pairs = find_unreviewed_matching_pairs(meta)
    if not unreviewed_roles and not unreviewed_pairs:
        return
    lines = [f"  - device_roles[{name!r}]: {fields}" for name, fields in sorted(unreviewed_roles.items())]
    lines += [f"  - matching_pairs: {p['names']} (matching_sensitivity={p['matching_sensitivity']!r}, "
              f"current_forced={p['current_forced']!r})" for p in unreviewed_pairs]
    raise ValueError(
        "optimize_full_circuit_budget() 실행 전 review가 필요하다 -- 아래 device_roles/"
        "matching_pairs는 propose_device_roles_gap_fill()이 netlist 구조만으로 추론한 "
        "제안일 뿐, 아직 topology.json에 사람이 검토·확정한 적이 없다(구조적으로 명확한 "
        "compensation/metric_stage_budget/replica 대상 소자와 differential 매칭쌍은 이미 "
        "제외됨, 잘못된 추론값으로 sizing/layout이 조용히 진행되는 걸 막기 위한 게이트):\n"
        + "\n".join(lines) +
        f"\n\nreview 방법: 위 제안이 맞다고 판단하면 propose_device_roles_gap_fill()로 다시 "
        f"계산한 결과를 apply_device_roles_gap_fill({topology_json_path!r}, result)로 "
        "topology.json에 실제로 써서 '검토완료'로 표시할 것(제안과 다른 값이 맞다고 "
        "판단하면 그 값을 직접 파일에 써도 동일하게 review완료로 인정됨). 그 다음부터는 "
        "이 소자들이 declared로 인식되어 이 게이트를 통과한다.")


def _verified_euler_fix(transistors: list, local_pairs: list):
    """`audit_vertical_stack_id_euler_feasibility()`/`merge_layout_groups_by_matching_
    pairs()`/`find_euler_repair_options()`가 공유하는 내부 헬퍼(2026-08-10 신설,
    세 곳에서 같은 로직이 중복되던 걸 통합) -- `transistors`(한 그룹)가 이미 오일러
    조건을 만족하면 그대로 통과, 아니면 `local_pairs`(그 그룹 내부로 이미 필터링된
    `(a, b)` 2-tuple 리스트)로 `suggest_pair_finger_adjustments()`를 돌려 1순위
    제안부터 **실제로 적용한 그래프를 다시 전체 조건(연결성 포함)으로 재검증**한다.

    ⚠️ `suggest_pair_finger_adjustments()`가 보고하는 `resulting_odd_count`는
    연결성을 안 본다(내부적으로 `check_euler_condition().odd_nodes`의 길이만 세고
    `.connected`는 버림, 2026-08-10 실측 발견) -- 그래서 서로 완전히 무관한(공유
    net이 아예 없는) 두 소자가 한 그룹으로 잘못 섞이면 "홀수차수가 2개로 줄어드니
    해결"처럼 보이지만 실제로는 여전히 끊긴 그래프다. 이 헬퍼는 그 착시를 피하려고
    제안을 실제로 적용해 다시 확인한다.

    반환: `(ok: bool, verified_suggestion: PairAdjustmentSuggestion | None)` --
    `ok=True`이고 `verified_suggestion=None`이면 애초에 조정 없이도 이미 통과.

    ⚠️ **2026-08-11(세션28) kind 동질성 하드 게이트 대응** -- `build_graph()`가 이제
    PMOS/NMOS가 섞인 그룹에 `ValueError`를 낸다(diffusion 공유 불가, 구조적으로
    finger 조정으로 못 고치는 문제). 이 헬퍼의 세 호출부(`audit_vertical_stack_id_
    euler_feasibility()`/`merge_layout_groups_by_matching_pairs()`/`find_euler_
    repair_options()`) 전부 "ok=False로 취급하고 계속 진행"이 맞는 반응이라(병합
    후보를 스킵하거나, review 대상으로 보고하거나) 여기서 한 번만 잡아 `(False,
    None)`으로 정규화한다 -- kind mismatch는 `suggest_pair_finger_adjustments()`를
    시도해봐야 절대 안 풀리므로 그 단계 자체를 건너뛴다."""
    try:
        verdict = check_euler_condition(build_graph(transistors))
    except ValueError:
        return False, None
    if verdict.kind != "impossible":
        return True, None
    for sugg in suggest_pair_finger_adjustments(transistors, local_pairs):
        trial = list(transistors)
        for name in sugg.names:
            idx = next(i for i, t in enumerate(trial) if t.name == name)
            trial[idx] = _dc_replace(trial[idx], n_fingers=trial[idx].n_fingers + sugg.delta_fingers)
        if check_euler_condition(build_graph(trial)).kind != "impossible":
            return True, sugg
    return False, None


def audit_vertical_stack_id_euler_feasibility(transistors: list, device_roles: dict,
                                               matching_pairs: list) -> dict:
    """2026-08-10 세션26 후속(2) K-3에서 발견된 `cmfb_tail`류 문제를 정면으로 잡는
    audit -- `audit_vertical_stack_id_vs_kcl()`(전기적 정합성)과는 다른 질문에 답한다:
    **declared `vertical_stack_id` 그룹 하나가 그 자체로 오일러 실현 가능한가**.

    `merge_layout_groups_by_matching_pairs()`의 오일러 게이트는 "병합으로 **새로**
    생기는" 문제만 막는다 -- declared로 **이미** 하나의 그룹인 소자들(예: `M37a`/
    `M37b`/`M38` -> `cmfb_tail`, `Ncmfb_tail`이 `M37a`/`M37b`의 source이자 `M38`의
    drain인 3단자 허브라 `n_fingers=1` 기준으로 이미 홀수차수 4개)은 그 게이트가
    손댈 대상이 아니다(union만 하지 입력으로 받은 그룹을 쪼개지 않으므로). 이 gap을
    메운다 -- `resolve_stack_layout()`이 병합 이전에 이미 안고 있는 문제를 병합
    이후에야 `optimize_full_circuit_budget()`의 `unresolved_row`로 뒤늦게 발견하는
    대신, 그룹을 조립하는 시점에 바로 잡아낸다.

    각 declared `vertical_stack_id` 그룹에 대해:
    1. `build_graph()`+`check_euler_condition()`으로 `n_fingers=1`(topology 원본
       상태) 기준 오일러 조건을 확인한다. `path`/`circuit`이면 정상(findings에서
       제외).
    2. `impossible`이면, 그 그룹 내부에 닫힌(양쪽 다 그룹 소속인) declared 매칭쌍만
       추려 `suggest_pair_finger_adjustments()`로 후보를 받고, **1순위 제안을 실제로
       적용한 그래프를 다시 `check_euler_condition()`으로 재검증**한다 -- ⚠️
       2026-08-10 실측 발견: `suggest_pair_finger_adjustments()`가 보고하는
       `resulting_odd_count`는 **연결성(connectivity)을 안 본다**(내부적으로
       `check_euler_condition().odd_nodes`의 길이만 세고 `.connected`는 버림) --
       그래서 서로 완전히 무관한(공유 net이 아예 없는) 두 소자가 한 declared
       그룹으로 잘못 선언된 경우, 각자 짝수/홀수 차수만 보면 "2개로 줄어드니 해결"
       처럼 보이지만 실제로는 여전히 끊긴 그래프라 오일러 경로 자체가 불가능하다
       (합성 fixture로 직접 재현: 완전히 분리된 두 2단자 소자를 한 그룹으로 선언 →
       `resulting_odd_count=2`로 보고되지만 재검증하면 여전히 `impossible`,
       `connected=False`). 이 함수는 그 착시를 피하려고 제안을 실제로 적용해
       **다시 전체 조건**(연결성 포함)을 확인한다 -- `path`/`circuit`이면 그제서야
       `resolvable_by_finger_adjustment=True`.

       ⚠️ 그럼에도 이 판정은 **필요조건일 뿐 충분조건은 아니다**(2026-08-10 K-4
       실측, `biasgen_ref` 사례) -- `n_fingers=1` 기준 제안이 실제 sizing 이후
       finger 수 기준으로는 안 통할 수 있다. 그래도 "이 baseline에서조차 연결성
       포함 완전히 안 풀린다"(`resolvable=False`)와 "적어도 baseline에서는 실제로
       풀린다"(`resolvable=True`)는 실질적으로 다른 심각도라 구분해 보고한다.

    반환: `{"findings": [{"vsid", "members", "odd_nodes", "resolvable_by_finger_
    adjustment", "verified_suggestion"(적용해서 실제로 통과 확인된
    `PairAdjustmentSuggestion`|`None`), "kind_mismatch"}, ...]}` -- 오일러가 이미
    `path`/`circuit`인 정상 그룹은 findings에 안 나온다(사후 대조표 원칙 그대로:
    문제 있는 것만 보고, 아무것도 자동으로 고치지 않는다).

    ⚠️ `resolvable_by_finger_adjustment=False`인 항목이 진짜 구조적 review 대상이다
    -- 어떤 매칭쌍 조정을 적용해봐도(연결성까지 포함해) 안 풀리는 경우는 그룹 구성
    자체(예: 애초에 무관한 소자가 섞였거나, `stack_groups_override`로 수동 재구성이
    필요)를 재검토해야 한다는 뜻이다.

    ⚠️ **2026-08-11(세션28) `kind_mismatch` 필드 신설** -- `build_graph()`가 이제
    PMOS/NMOS 혼합 그룹에 `ValueError`를 낸다(diffusion 공유 불가). 이 함수는 그
    ValueError를 그룹별로 잡아 별도 finding으로 보고한다 -- `odd_nodes`/`resolvable_
    by_finger_adjustment`(항상 `False`, kind 문제는 finger 조정으로 원천적으로 못
    고침)/`verified_suggestion`(항상 `None`)은 이 경우 의미가 없으므로 `kind_mismatch
    =True`와 `kinds`(그룹의 실제 kind 구성)만 채운다. 기존 홀짝-차수 findings는
    `kind_mismatch=False`로 채워 두 원인을 명확히 구분한다 -- 이 회로 실측: 26개
    declared vsid 그룹 중 8개(`biasgen_vom_battery_a`/`_b`, `biasgen_vop_battery_a`/
    `_b`, `vbias2_stack`, `vbias3_stack`, `output_stage_a`/`_b`)가 kind_mismatch다."""
    by_name = {t.name: t for t in transistors}
    vsid_groups: dict = defaultdict(list)
    for name, entry in device_roles.items():
        if isinstance(entry, dict) and entry.get("vertical_stack_id"):
            vsid_groups[entry["vertical_stack_id"]].append(name)

    pair_list = [(a, b) for names in matching_pairs for a, b in zip(names, names[1:])]

    findings = []
    for vsid, members in vsid_groups.items():
        trs = [by_name[n] for n in members if n in by_name]
        try:
            verdict = check_euler_condition(build_graph(trs))
        except ValueError:
            findings.append({
                "vsid": vsid, "members": sorted(members), "odd_nodes": None,
                "resolvable_by_finger_adjustment": False, "verified_suggestion": None,
                "kind_mismatch": True, "kinds": sorted({t.kind for t in trs}),
            })
            continue
        if verdict.kind != "impossible":
            continue
        member_set = set(members)
        local_pairs = [(a, b) for a, b in pair_list if a in member_set and b in member_set]
        ok, verified = _verified_euler_fix(trs, local_pairs)
        findings.append({
            "vsid": vsid, "members": sorted(members), "odd_nodes": verdict.odd_nodes,
            "resolvable_by_finger_adjustment": ok,
            "verified_suggestion": verified, "kind_mismatch": False,
        })

    return {"findings": findings}


def merge_layout_groups_by_matching_pairs(transistors: list, groups: dict,
                                           matching_pairs: list) -> dict:
    """2026-08-10 세션26 후속(`.ai/context.md` J-4/J-9) 논의에서 설계 합의된 함수 --
    `vertical_stack_id`(declared/candidates 아무 쪽이든, `resolve_stack_layout()`의
    tier 2/3 결과) 기반 그룹이 **수직 방향**만 답해서, 매칭 파트너가 서로 다른 물리
    branch에 있으면(예: `folded_cascode`의 `M1`/`M2` 차동입력쌍, `M3`/`M4` 전류원쌍)
    항상 서로 다른 그룹으로 쪼개진다는 문제를 푼다 -- 그 결과 `audit_row_split()`의
    3b(interdigitation)/3c(common-centroid)가 실패하는 걸 실측으로 확인했다(`folded_
    cascode` 5개 매칭쌍 전부 실패, `.ai/context.md` 세션26 후속 대화 초반).

    `geometry_colocation_union()`을 고치는 대신 **새 함수로 분리한 이유**(설계
    합의): `geometry_colocation_union()`은 `stick_diagram.py` Test 29가 `folded_
    cascode`의 정확한 그룹 구성을 하드핀해둔 레거시 폴백이라 시맨틱을 바꾸면 안 되고,
    그 함수의 위험한 부분(`find_stacked_matching_candidates()`의 재귀적 connectivity
    climb -- `M6`/`M5`가 서로 다른 두 매칭쌍(`M1/M2`, `M3/M4`) 양쪽에 동시에 "유일한
    상위 소자"로 잡혀 무관한 두 쌍을 조용히 하나로 합쳐버리는 실제 버그, 세션26 후속
    J-1)와 안전한 부분(declared 매칭쌍 union)이 그 함수 안에 이미 섞여 있었다.

    **이 함수는 그 위험한 부분(재귀적 connectivity climb)을 아예 안 쓴다** -- `vertical_
    stack_id`가 이미 수직 방향(무엇이 진짜로 직렬로 쌓여있는가, cascode 다단 포함)을
    전부 답해놨으므로, 남은 일은 **그룹과 그룹을 잇는 것**뿐이다: declared 매칭쌍
    `(a, b)`마다 `a`가 속한 그룹과 `b`가 속한 그룹을 union하는 **그룹 단위(소자 단위
    아님) union-find**. `M6`처럼 애초에 어느 매칭쌍에도 속하지 않는 소자(candidates가
    `ambiguous_*`로 격리했든, declared에 아예 없든)는 이 함수가 절대 건드리지 않는다
    -- 모호한 건 그대로 격리 유지, 확실한 매칭만 합친다는 프로젝트 원칙이 구조적으로
    보장된다(`M6`을 통한 우회 병합 자체가 불가능 -- `M6`이 그룹 키가 아니라 매칭쌍의
    당사자가 아니므로 union 대상이 될 수 없다).

    ⚠️ **2026-08-10 추가(같은 날 end-to-end 품질비교 중 발견) -- 오일러 실현가능성
    사전 검사**: 초판은 매칭쌍마다 무조건 그룹을 합쳤는데, `current_reuse_telescopic_
    ota` 51소자 실회로로 `optimize_full_circuit_budget()`을 실제로 태워보니 `cmfb_tail`
    (`M37a`/`M37b`/`M38`)이 병합 후 오일러 조건이 깨져서(4개 홀수차수) `run_topology_
    pipeline_with_finger_fixup()`의 기존 자동수정으로도 못 풀리는 `unresolved_row`가
    나왔다(legacy `geometry_colocation_union()`에는 없던 새 실패 -- 사용자 지적). 이제
    매칭쌍마다 union하기 **전에** 먼저 시험적으로 합쳐보고(`build_graph()`+`check_euler_
    condition()`), (a) 합친 결과가 이미 `path`/`circuit`이면 그대로 확정. (b) `impossible`
    이면 그 임시 병합 그룹 내부의 매칭쌍만으로 `suggest_pair_finger_adjustments()`를
    돌려 **한 번의 핑거 조정으로 2개 이하까지 줄일 수 있는지** 확인 -- 줄일 수 있으면
    (`run_topology_pipeline_with_finger_fixup()`이 나중에 실제로 이 조정을 적용해 풀
    수 있다는 근거이므로) 합치고, 줄일 수 없으면(핑거 조정 한 번으로도 안 풀리는 진짜
    구조적 홀수차수 불균형) **이 매칭쌍은 건너뛰고 두 그룹을 분리된 채로 남긴다** --
    과병합보다 "매칭 파트너가 다른 행에 남는 것"(3b/3c 실패, 인지 가능하고 눈에 보임)이
    "오일러 자체가 안 풀리는 것"(euler-blocked, 자동수정 루프가 소진될 때까지 못 알아챔)
    보다 낫다는 판단 -- 이 함수 자체는 여전히 `n_fingers=1`(원본 topology 상태) 기준
    으로만 판단한다(실제 sizing 이후 finger 배분은 뒤 단계 `assign_finger_geometry()`
    소관이므로 여기서 W/finger를 미리 알 필요는 없다, `n_fingers=1` 판정도 그 이후 실제
    핑거 배분에서 동일 부모/자식 관계가 유지되는 한 유효하다). ⚠️ 핑거 조정 판정은
    `suggest_pair_finger_adjustments()`의 `resulting_odd_count`를 그대로 믿지 않고
    실제로 적용한 그래프를 다시 전체 조건(연결성 포함)으로 재검증한다 -- 그 값이
    연결성을 안 보고 홀짝만 세기 때문에(`audit_vertical_stack_id_euler_feasibility()`
    와 같은 이유로 실측 발견), 서로 완전히 무관한 두 그룹을 매칭쌍 하나로 잘못
    이어붙이는 착시를 그대로 두면 놓칠 수 있다.

    `matching_pairs`: 병합 기준으로 쓸 선언된 쌍 목록, 호출자가 직접 고른다(새
    파라미터로 "선택 가능하게" 만들지 않고 이 인자 자체가 선택지 -- `resolve_stack_
    layout()`이 이미 쓰는 `current_forced=True` 필터링을 그대로 재사용하면 기본값이
    된다). **기본으로 `current_forced=True`만 넘기길 권장** -- 세션9/10 실측: declared
    `matching_pairs` **전부**(`branch_symmetric`/`current_mirror` 등 `current_forced=
    False`까지)를 병합 기준으로 쓰면 무관한 hub 그룹을 끌고 들어와 매칭 품질이 악화된
    선례가 있다(dx=6.00 vs 제외한 경우 dx=3~4). `M5`/`M6`(`folded_cascode`,
    `current_forced=False`) 같은 쌍은 기본값으로는 병합 안 되고 각자 그룹에 남는다
    (모호하면 병합하지 않는 게 안전).

    반환은 `kcl_series_union()`/`geometry_colocation_union()`과 동일한 계약
    `{stack_id: [device_name, ...]}` -- `assign_finger_geometry()`에 그대로 넘길 수
    있다. 대표 키는 병합에 참여한 원본 그룹 키 중 사전순으로 가장 작은 것을 그대로
    쓴다(새 이름을 짓지 않음 -- declared/candidates가 이미 붙인 의미 있는 이름을
    보존하기 위해)."""
    by_name = {t.name: t for t in transistors}
    group_of = {name: gid for gid, members in groups.items() for name in members}
    parent = {gid: gid for gid in groups}
    root_members = {gid: list(members) for gid, members in groups.items()}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def euler_feasible(names):
        trs = [by_name[n] for n in names if n in by_name]
        name_set = set(names)
        local_pairs = [(a, b) for a, b in pair_list if a in name_set and b in name_set]
        ok, _sugg = _verified_euler_fix(trs, local_pairs)
        return ok

    pair_list = [(a, b) for names in matching_pairs for a, b in zip(names, names[1:])]

    for a, b in pair_list:
        ga, gb = group_of.get(a), group_of.get(b)
        if ga is None or gb is None:
            continue
        ra, rb = find(ga), find(gb)
        if ra == rb:
            continue
        tentative = root_members[ra] + root_members[rb]
        if not euler_feasible(tentative):
            continue
        if ra < rb:
            parent[rb] = ra
            root_members[ra] = tentative
            del root_members[rb]
        else:
            parent[ra] = rb
            root_members[rb] = tentative
            del root_members[ra]

    return {gid: sorted(members) for gid, members in root_members.items()}


def derive_horizontal_stack_groups(transistors: list, vertical_groups: dict,
                                    matching_pairs: list) -> dict:
    """2026-08-11(세션28 후반부) -- `vertical_stack_id`(전기적 VDD->GND 컬럼, 헤드룸/VDS
    예산용)와 물리 레이아웃 행(같은 kind끼리 diffusion을 공유하는 오일러 trail 대상)이
    애초에 서로 다른 두 개념이라는 사용자 통찰로 신설. 세션28 전반부는 `resolve_stack_
    layout()`이 `vertical_stack_id` 그룹을 그대로 `merge_layout_groups_by_matching_
    pairs()`에 넘겨 물리 레이아웃 그룹으로 썼는데, `vertical_stack_id`는 정의상 PMOS/NMOS
    경계를 넘나든다(예: `output_stage_a`=class-AB 출력단, M15=pmos/M16=nmos가 한 전기적
    컬럼) -- `build_graph()`의 kind 동질성 하드 게이트(같은 세션 신설)가 이걸 잡아냈다.

    이 함수는 "두 stack 개념을 같은 근원 정보(branch 연결성 + declared `matching_pairs`)
    에서 각자 다른 기준으로 파생시킨다"는 설계를 코드 두 줄로 구현한다:
    1. **kind로 분할**: `vertical_groups`(수직 기준으로 이미 묶인 1차 그룹)의 각 그룹을
       `t.kind`로 쪼갠다. 이미 kind 동질인 그룹(이 회로 26개 중 18개)은 이름 그대로 유지
       -- 접미사로 인한 불필요한 이름 변경을 피한다. 실제로 섞인 그룹만 `{vsid}__{kind}`
       서브그룹으로 나뉜다(예: `output_stage_a` -> `output_stage_a__pmos`={M15},
       `output_stage_a__nmos`={M16}).
    2. **대칭 branch 재병합**: 그 kind-homogeneous 서브그룹을 그대로 `merge_layout_
       groups_by_matching_pairs()`에 넘긴다 -- 이 함수가 이미 "declared matching_pairs로
       그룹과 그룹을 잇되 실제 오일러 재검증을 통과해야만 확정"하는 안전한 그룹 단위
       union-find를 갖고 있으므로 재발명하지 않는다. `output_stage_a__pmos`(M15)와
       `output_stage_b__pmos`(M25)는 `M15`-`M25` declared matching_pairs로 다시 만나
       (kind가 이제 같으므로) 정상적으로 한 물리 행으로 재병합된다.

    반환은 `merge_layout_groups_by_matching_pairs()`와 동일 계약 `{stack_id:
    [device_name, ...]}` -- 반환된 모든 그룹은 항상 kind 동질이다(1단계가 보장, 2단계는
    같은 kind끼리만 다시 합치므로 절대 재오염되지 않음).

    ⚠️ 이건 `vertical_stack_id`를 대체하는 게 아니라 그 위에 얹는 **2번째 파생 축**이다
    -- 헤드룸(`allocate_stack_headroom()`)은 여전히 원본 `vertical_stack_id`를 직접 읽고,
    이 함수의 결과(`horizontal_stack_id` 성격의 그룹)는 오직 물리 레이아웃 파이프라인
    (`assign_finger_geometry()`/`run_topology_pipeline()`)에만 쓰인다.

    ⚠️ 2026-08-11 현재는 **candidates 전용**(topology.json에 영구 저장되는 declared
    필드 없음, `vertical_stack_id`+`matching_pairs`+`kind`에서 매번 새로 계산) --
    `vertical_stack_id` 자신도 세션22~23엔 candidates만이었다가 세션24~25에 검증 후
    declared로 승격됐던 것과 같은 경로를 의도적으로 밟는다(`.ai/context.md` 세션28
    "## Q" 참고). 다른 회로 최소 1개로 교차검증한 뒤 declared 승격을 논의할 것."""
    by_name = {t.name: t for t in transistors}
    split_groups = {}
    for vsid, members in vertical_groups.items():
        by_kind = defaultdict(list)
        for name in members:
            t = by_name.get(name)
            if t is not None:
                by_kind[t.kind].append(name)
        if len(by_kind) <= 1:
            split_groups[vsid] = members
        else:
            for kind, names in by_kind.items():
                split_groups[f"{vsid}__{kind}"] = names
    return merge_layout_groups_by_matching_pairs(transistors, split_groups, matching_pairs)


def find_euler_repair_options(transistors: list, blocked_members: list, matching_pairs: list,
                               candidate_groups: dict | None = None) -> dict:
    """2026-08-10 세션26 후속(2) -- 사용자 질문("unresolved_row를 resolved로 만들려면
    어떤 row를 병합해야 하는가")에 답하려고 신설. 실제 `optimize_full_circuit_budget()`
    끝까지 태운 뒤 `unresolved_row`로 남은 그룹(`biasgen_ref_seg1_seg1_seg1_seg1_seg1`
    = `M18_bg`/`M60`/`M61`, `n_fingers=7`)과 `cmfb_tail`(`M37a`/`M37b`/`M38`,
    `n_fingers=5`)을 이 함수로 직접 진단해보니 **둘 다 실제로는 병합이 전혀 필요
    없었다** -- 같은 행 안에서 핑거 조정 하나만으로 이미 풀린다는 게 실측으로
    확인됐다(연결성까지 재검증 완료: `cmfb_tail`은 `M38` 핑거 5→6, `biasgen_ref`는
    `M18_bg`+`M60` 또는 `M60`+`M61` 쌍 ±1). 즉 이 두 실패 사례의 진짜 원인은
    "병합이 필요한 구조적 문제"가 아니라 **`run_topology_pipeline_with_finger_
    fixup()`의 실제 탐색 전략이 이미 존재하는 이 해법을 못 찾고 있다**는 것이었다
    -- 이 함수는 그 진단을 자동화하되(1단계), 정말로 같은 행만으로 안 풀리는 경우를
    대비해 다른 row와의 병합 탐색(2단계)도 제공한다(요청하신 기능 자체는 완전히
    구현하되, 실측으로 밝혀진 "지금 당장은 이 두 사례엔 불필요하다"는 사실도 그대로
    보고한다 -- 상상으로 채우지 않는다는 원칙).

    **1단계 -- 같은 행 안에서 먼저 확인**: `blocked_members`만으로 `_verified_euler_
    fix()`를 돌린다. 여기서 풀리면(`same_row_fix`가 채워짐) 2단계는 아예 실행하지
    않는다 -- 병합은 더 큰 그룹을 만드는 더 무거운 개입이라, 가벼운 해법이 있으면
    그걸 우선한다.

    **2단계 -- 같은 행만으로 안 풀리면 다른 row와의 병합 탐색**: `candidate_groups`
    (다른 row 후보들, `{row_name: [device,...]}` -- 보통 같은 `stack_groups_geometry`
    의 나머지 row 전부)를 하나씩 `blocked_members`와 임시로 합쳐보고
    `_verified_euler_fix()`로 실현 가능한지 확인한다(직접 되거나, 합친 그룹 내부
    매칭쌍으로 1회 조정하면 되거나). 실현 가능한 후보만 반환하되, **병합 후 그룹
    크기가 작은 순**으로 정렬한다(가장 적게 섞는 병합을 우선 제안 -- 큰 그룹일수록
    box-shape/finger_w 호환성이 깨질 위험이 커지므로, 세션26 후속 legacy 비교에서
    실측한 그 위험).

    반환: `{"same_row_fix": {"verified_suggestion": ...} | None,
    "merge_candidates": [{"row", "members", "resolvable_by_finger_adjustment",
    "verified_suggestion"}, ...]}` -- `same_row_fix`가 있으면 `merge_candidates`는
    항상 빈 리스트(1단계에서 이미 풀렸으므로 2단계 자체를 안 돌림). `candidate_groups`
    를 안 주고 1단계도 실패하면 `merge_candidates=[]`(탐색할 후보가 없었을 뿐, "병합
    불가능"이라는 뜻이 아님 -- 호출자가 후보를 안 줬다는 뜻)."""
    by_name = {t.name: t for t in transistors}
    blocked_set = set(blocked_members)
    pair_list = [(a, b) for names in matching_pairs for a, b in zip(names, names[1:])]

    blocked_trs = [by_name[n] for n in blocked_members if n in by_name]
    local_pairs = [(a, b) for a, b in pair_list if a in blocked_set and b in blocked_set]
    ok, sugg = _verified_euler_fix(blocked_trs, local_pairs)
    if ok:
        return {"same_row_fix": {"verified_suggestion": sugg}, "merge_candidates": []}

    merge_candidates = []
    for row_name, members in (candidate_groups or {}).items():
        if set(members) == blocked_set:
            continue
        combined_members = blocked_members + list(members)
        combined_set = set(combined_members)
        trs = [by_name[n] for n in combined_members if n in by_name]
        c_pairs = [(a, b) for a, b in pair_list if a in combined_set and b in combined_set]
        c_ok, c_sugg = _verified_euler_fix(trs, c_pairs)
        if c_ok:
            merge_candidates.append({
                "row": row_name, "members": sorted(members),
                "resolvable_by_finger_adjustment": c_sugg is not None,
                "verified_suggestion": c_sugg,
            })
    merge_candidates.sort(key=lambda c: len(c["members"]))

    return {"same_row_fix": None, "merge_candidates": merge_candidates}


# ---------------------------------------------------------------------------
# 2.5) Finger 폭 정합성 검사 — 오일러 조건보다 먼저 확인해야 하는 더 기본적인 제약
# ---------------------------------------------------------------------------

@dataclass
class FingerWidthIssue:
    transistor: str
    w: float
    finger_w: float
    exact_ratio: float
    nearest_valid_w: tuple           # (내림 옵션, 올림 옵션) — 둘 다 finger_w의 정수배


@dataclass
class FingerWidthVerdict:
    ok: bool
    issues: list = field(default_factory=list)


def check_finger_width_compatibility(transistors: list[Transistor], tol: float = 1e-9) -> FingerWidthVerdict:
    """W가 그 stack의 finger_w로 정확히 나누어떨어지는지 확인한다.

    `n_fingers`를 그냥 `round(w / finger_w)`로 계산해서 넘기면 이 문제가 조용히 묻힌다 —
    "4.75개 finger"처럼 물리적으로 존재할 수 없는 요구를 반올림이 감춰버리기 때문이다. 실제로
    Maloberti PDF의 folded cascode 예제(p.34→p.35 "Split of Transistors")가 정확히 이 이유로
    W를 조정했다: bottom stack의 finger 폭을 8µm로 정했더니 M7/M8=38µm(38/8=4.75), M9/M10=25µm
    (25/8=3.125)가 정수가 아니어서 각각 40µm(=5×8), 24µm(=3×8)로 바꿨다 — 반올림하면 두 경우
    모두 우연히 "5개", "3개"로 **똑같이** 반올림되어 버려서(round(4.75)=5=round(40/8),
    round(3.125)=3=round(24/8)) 반올림 기반 확인으로는 이 문제를 애초에 발견할 수 없었다.

    따라서 이 함수는 반올림하지 않고 **정확한 나머지**를 검사한다 — `Transistor.w`와
    `Transistor.finger_w`를 둘 다 지정한 소자만 대상이며, `stick-diagram-euler-layout.md` §5
    피드백 루프에서 오일러 조건 분석보다 먼저 통과해야 하는 선행 게이트다.
    """
    issues = []
    for t in transistors:
        if t.w is None or t.finger_w is None:
            continue
        ratio = t.w / t.finger_w
        nearest = round(ratio)
        if abs(ratio - nearest) > tol:
            down = math.floor(ratio) * t.finger_w
            up = math.ceil(ratio) * t.finger_w
            issues.append(FingerWidthIssue(t.name, t.w, t.finger_w, ratio, (down, up)))
    return FingerWidthVerdict(ok=not issues, issues=issues)


# ---------------------------------------------------------------------------
# 3) 그래프화 + Euler 조건 판정
# ---------------------------------------------------------------------------

@dataclass
class StackGraph:
    """하나의 stack을 무방향 multigraph로 표현. edge_id -> (transistor_name, u, v)."""

    nodes: set = field(default_factory=set)
    edges: dict = field(default_factory=dict)        # edge_id -> (t_name, u, v)
    adjacency: dict = field(default_factory=lambda: defaultdict(list))  # node -> [(edge_id, other)]


def build_graph(transistors: list[Transistor]) -> StackGraph:
    """§2.5.4 "최대한 섞는다"를 hierholzer()가 자동으로 따르게 만드는 지점이 바로 여기다.

    ⚠️ 2026-07-23 발견한 문제: 예전엔 이 함수가 트랜지스터 하나의 finger를 전부(`for i in
    range(t.n_fingers)`) 연달아 추가한 뒤 다음 트랜지스터로 넘어갔다 — Euler trail
    feasibility(오일러 조건)에는 전혀 영향이 없지만(어떤 순서로 edge를 추가해도 각 node의
    차수는 그대로다), `hierholzer()`가 LIFO 스택으로 adjacency를 그대로 소진하다 보니 실제
    나온 순서가 "AAAA BBBB"처럼 완전히 뭉친 배치였다(current mirror M2/M2b 4:4 사례에서
    실측). §2.5~§2.6이 공들여 만든 interdigitation 원칙(최대한 섞는다)이 정작
    `build_stick_diagram()` 파이프라인에는 전혀 연결되어 있지 않았던 것 — Euler trail이
    "가능한지"와 "잘 섞여 있는지"는 별개 질문인데 코드가 후자를 신경 쓰지 않았다.

    고친 방법: 이 stack에 속한 트랜지스터들의 finger를 **라운드로빈**(각 트랜지스터에서
    한 개씩 돌아가며)으로 추가한다. Euler 조건(각 node 차수의 짝/홀)은 edge 추가 순서와
    무관하므로 판정 결과는 그대로고, `hierholzer()`가 만드는 구체적 trail만 자연스럽게
    여러 트랜지스터를 번갈아 방문하는 형태가 된다 — 완벽한 대칭 패턴표(§2.5 INTERDIGITATION_
    PATTERNS)만큼 정교하진 않지만(그건 여전히 별도 후처리가 필요할 수 있다), 적어도 "한
    소자를 다 쓴 뒤에야 다음 소자로 넘어가는" 최악의 뭉침은 기본값에서부터 막는다.

    ⚠️ **2026-08-11(세션28) kind 동질성 하드 게이트 추가** — 이 함수가 만드는 그래프는
    "이 트랜지스터들을 finger 단위로 이어붙인 하나의 물리 diffusion 행(Euler trail =
    실제 배치 순서)"이라는 전제로 하류 전체(`check_euler_condition()`/`hierholzer()`/
    `audit_row_split()`/`merge_layout_groups_by_matching_pairs()`/`audit_vertical_
    stack_id_euler_feasibility()`)가 그 결과를 소비한다. 그런데 이 알고리즘 자체는
    노드=net/엣지=트랜지스터인 순수 connectivity 그래프만 보고 `t.kind`를 전혀 참조하지
    않아서, PMOS/NMOS가 섞인 그룹을 넣어도 수학적으로는 "유효한 오일러 경로"가 태연히
    나온다 — 실측 확인(`vbias2_stack`=M57(pmos)/M58(pmos)/M68(nmos)): `hierholzer()`가
    `M58→M57→M68` trail을 "path"로 확정했는데, 이는 PMOS(M57)와 NMOS(M68)가 diffusion을
    공유하며 바로 이어붙는다는 뜻이라 물리적으로 존재할 수 없다(PMOS=n-well, NMOS=p-well/
    p-sub, 같은 diffusion strip을 공유 불가). `split_into_stacks()`의 자동 `(kind,
    finger_w)` 그룹핑에는 이 극성 동질성 규칙이 있었지만, `stack_id`가 이미 명시된
    입력(`resolve_stack_layout()`의 `vertical_stack_id` 기반 그룹 등)은 그 규칙을 우회해
    바로 여기로 들어왔다 — 그 결과 이 함수가 마지막 방어선이었는데 검사가 없었다. 이제
    여기서 막는다: "finger 조정으로 풀 수 있는 홀수차수 불균형"과 범주가 다른, 조정으로
    절대 못 푸는 구조적 불가능이므로 `EulerVerdict(kind="impossible")`(소프트 실패,
    `suggest_pair_finger_adjustments()` 같은 자동수정 루프가 시도할 대상)가 아니라
    즉시 `ValueError`(하드 실패, 호출자가 그룹 자체를 kind별로 재구성해야 함)로 낸다."""
    kinds = {t.kind for t in transistors}
    if len(kinds) > 1:
        raise ValueError(
            f"build_graph()에 서로 다른 kind가 섞인 소자 그룹이 들어왔다: "
            f"{sorted((t.name, t.kind) for t in transistors)} -- PMOS/NMOS는 diffusion을 "
            f"공유할 수 없어 하나의 물리 행(Euler trail 대상)이 될 수 없다(finger 조정으로도 "
            f"못 고치는 구조적 문제). 호출자가 이 그룹을 kind별로 먼저 분리할 것.")
    g = StackGraph()
    max_fingers = max((t.n_fingers for t in transistors), default=0)
    for i in range(max_fingers):
        for t in transistors:
            if i >= t.n_fingers:
                continue
            g.nodes.add(t.source)
            g.nodes.add(t.drain)
            edge_id = f"{t.name}#{i}"
            g.edges[edge_id] = (t.name, t.source, t.drain)
            g.adjacency[t.source].append((edge_id, t.drain))
            g.adjacency[t.drain].append((edge_id, t.source))
    return g


def _degrees(g: StackGraph) -> dict:
    return {n: len(g.adjacency[n]) for n in g.nodes}


def _is_connected_ignoring_isolated(g: StackGraph) -> bool:
    active = [n for n in g.nodes if g.adjacency[n]]
    if not active:
        return True
    seen = {active[0]}
    stack = [active[0]]
    while stack:
        v = stack.pop()
        for edge_id, u in g.adjacency[v]:
            if u not in seen:
                seen.add(u)
                stack.append(u)
    return seen.issuperset(active)


@dataclass
class EulerVerdict:
    kind: str                # 'circuit' | 'path' | 'impossible'
    odd_nodes: list
    connected: bool
    start: str | None = None
    end: str | None = None


def check_euler_condition(g: StackGraph) -> EulerVerdict:
    """PDF/pptx가 명시한 3가지 오일러 조건을 그대로 판정한다:
    0개 홀수차수 → circuit(닫힌 한붓그리기), 2개 → path(열린 한붓그리기), 4개 이상 → impossible.
    연결성도 함께 확인한다(차수 조건을 만족해도 그래프가 끊겨 있으면 한 줄 diffusion으로 불가능)."""
    degrees = _degrees(g)
    odd_nodes = sorted(n for n, d in degrees.items() if d % 2 == 1)
    connected = _is_connected_ignoring_isolated(g)

    if not connected:
        return EulerVerdict("impossible", odd_nodes, connected)
    if len(odd_nodes) == 0:
        # ⚠️ 2026-07-27 실제 사고: `g.nodes`가 set이라 `next(iter(...))`의 결과가 프로세스마다
        # 다르다(문자열 hash가 PYTHONHASHSEED로 랜덤화되는 CPython 기본 동작 때문 -- 실측
        # 확인: 동일 입력을 별도 프로세스 3번 실행해 서로 다른 3가지 transistor_sequence를
        # 얻었다). 같은 입력이 실행마다 다른 배치로 나오면 audit_row_split()의 interdigitation/
        # common-centroid 판정도 실행마다 뒤집힐 수 있어 검증 게이트로서 신뢰할 수 없다 --
        # `sorted()`로 시작 노드를 고정해 재현 가능하게 만든다(어떤 시작 노드를 고르든 Euler
        # circuit 자체의 유효성엔 영향이 없으므로, 고정한다고 판정 결과가 왜곡되지 않는다).
        start = min((n for n in g.nodes if g.adjacency[n]), default=None)
        return EulerVerdict("circuit", odd_nodes, connected, start=start, end=start)
    if len(odd_nodes) == 2:
        return EulerVerdict("path", odd_nodes, connected, start=odd_nodes[0], end=odd_nodes[1])
    return EulerVerdict("impossible", odd_nodes, connected)


# ---------------------------------------------------------------------------
# 4) Hierholzer 알고리즘 — 실제 stick sequence(node열 + 사용된 트랜지스터열) 생성
# ---------------------------------------------------------------------------

def hierholzer(g: StackGraph, start: str) -> tuple[list, list]:
    """오일러 경로/회로가 존재한다는 전제 하에 실제 순회 순서를 구한다(반복문 버전, 재귀 깊이 문제 없음).

    반환: (node_sequence, transistor_sequence) — transistor_sequence[i]는
    node_sequence[i]에서 node_sequence[i+1]로 갈 때 쓰인 트랜지스터 이름이다
    (길이는 node_sequence보다 1 짧다)."""
    adj = {n: list(v) for n, v in g.adjacency.items()}
    used = set()
    stack = [(start, None)]           # (node, 여기 도착할 때 쓴 edge_id)
    circuit = []                       # 역순으로 쌓인다

    while stack:
        v, arrive_edge = stack[-1]
        advanced = False
        while adj[v]:
            edge_id, u = adj[v].pop()
            if edge_id in used:
                continue
            used.add(edge_id)
            stack.append((u, edge_id))
            advanced = True
            break
        if not advanced:
            circuit.append(stack.pop())

    circuit.reverse()
    node_sequence = [c[0] for c in circuit]
    transistor_sequence = [g.edges[c[1]][0] for c in circuit[1:]]
    return node_sequence, transistor_sequence


# ---------------------------------------------------------------------------
# 4.5) 최소 crossover routing 배치 — check_euler_condition()이 "impossible"이어도 포기하지
#      않는다. 2026-07-28 신설(사용자 요청): §2.6 조사에서 3소자 이상 interdigitation
#      패턴(ABC/ABCD 등)이 hub-leaf 단일 diffusion으로는 무효였지만, 외부 문헌 조사로
#      실무에서는 이런 경우 crossover routing(열 사이를 metal+via로 건너뛰는 배선)으로
#      실현한다는 걸 확인했다 — 그럼 "최소 몇 번의 crossover가 필요한가"를 실제로 계산해
#      찾아주는 함수가 있어야 한다는 데서 출발.
# ---------------------------------------------------------------------------

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
# 급증한다 -- 다른 조합 탐색(`_MAX_MIRROR_TRAIL_COMBO_PAIRS` 등)과 동일한 관례로 8에서 캡.


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
            raise ValueError(f"모든 소자가 같은 hub(source)를 공유해야 한다 — 실제: {hub_nets}")
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


# ---------------------------------------------------------------------------
# 5) Finger 수 조정 후보 탐색 — impossible일 때 "무엇을 바꾸면 되는지" 제안
# ---------------------------------------------------------------------------

@dataclass
class AdjustmentSuggestion:
    transistor: str
    delta_fingers: int             # +1 또는 -1
    resulting_odd_count: int
    note: str


def suggest_finger_adjustments(transistors: list[Transistor]) -> list[AdjustmentSuggestion]:
    """홀수차수 노드가 ≥4개(또는 그래프가 끊김)일 때, 트랜지스터 하나의 finger 수를 ±1 조정하면
    홀수차수 노드 개수가 어떻게 바뀌는지 전수 탐색한다.

    원리(stick-diagram-euler-layout.md §2): finger 1개 추가/제거는 그 트랜지스터의 두 끝 노드
    (source, drain) 차수를 동시에 1씩 바꾼다 — 두 노드가 모두 홀수였다면 조정 후 둘 다 짝수가
    되어 홀수 노드 수가 2 감소하고, 하나만 홀수였다면 그 불균형이 반대쪽 노드로 옮겨갈 뿐 총
    홀수 개수는 그대로다, 둘 다 짝수였다면 오히려 2 증가한다. 결과를 홀수 개수 오름차순으로
    정렬해 반환하므로, 맨 앞 후보가 "이 조정 하나로 가장 많이 개선되는" 선택이다.

    ⚠️ 이 함수는 순수 그래프 계산이다 — 제안된 조정이 회로 스펙(gain/GBW/matching/noise)을
    깨지 않는지는 전혀 모른다. 반드시 stick-diagram-euler-layout.md §5 체크리스트로 재검증한
    뒤에만 채택할 것. 특히 신호 경로/matching-critical 소자보다 cascode·미러·바이어스 소자를
    조정 대상으로 우선 고려하라(같은 문서 §5 "조정 대상 판단").
    """
    baseline_graph = build_graph(transistors)
    baseline_odd = len(check_euler_condition(baseline_graph).odd_nodes)

    results = []
    for idx, t in enumerate(transistors):
        for delta in (+1, -1):
            new_n = t.n_fingers + delta
            if new_n < 1:
                continue
            trial = list(transistors)
            trial[idx] = Transistor(
                name=t.name, kind=t.kind, source=t.source, drain=t.drain,
                n_fingers=new_n, finger_w=t.finger_w, stack_id=t.stack_id,
            )
            trial_graph = build_graph(trial)
            odd_count = len(check_euler_condition(trial_graph).odd_nodes)
            if odd_count < baseline_odd:
                note = f"차수 개선: 홀수 노드 {baseline_odd}개 → {odd_count}개"
            elif odd_count == baseline_odd:
                note = "총 홀수 노드 수는 그대로(불균형이 다른 노드로 이동)"
            else:
                note = f"오히려 악화: 홀수 노드 {baseline_odd}개 → {odd_count}개"
            results.append(AdjustmentSuggestion(t.name, delta, odd_count, note))

    results.sort(key=lambda s: s.resulting_odd_count)
    return results


@dataclass
class PairAdjustmentSuggestion:
    names: tuple                   # (name,) 미매칭 단독 소자, 또는 (a, b) 매칭쌍
    delta_fingers: int             # +1 또는 -1, names의 전 소자에 동일하게 적용
    resulting_odd_count: int
    note: str


def suggest_pair_finger_adjustments(transistors: list[Transistor],
                                     matching_pairs: list) -> list[PairAdjustmentSuggestion]:
    """세션11 M3a 그룹 실측(`.ai/context.md` B-4)에서 확인된 원리를 일반화한다 —
    `suggest_finger_adjustments()`(개별 소자 ±1)와 달리 조정 단위를 **매칭쌍 또는 미매칭
    단독 소자 하나**로 잡는다. 매칭쌍은 **양쪽에 동일한 delta를 동시에 적용**하므로 조정 후에도
    두 소자의 `n_fingers`가 항상 같게 유지된다(=비율 1:1이 구조적으로 보장됨, 개별 조정을
    우연히 짝맞추는 게 아니다).

    실측(M3a 그룹, 11소자): `M9b`/`M18b`(선언된 ratio 매칭쌍)에 동시에 +1을 적용하면 전체
    그래프 홀수차수 노드가 6개→2개로 줄어 `check_euler_condition()`이 `path`가 된다 — 개별
    함수로는 2단계(M9b, M18b 각각 ±1)가 필요했던 걸 이 함수는 1번의 제안으로 찾아낸다.

    ⚠️ `suggest_finger_adjustments()`와 마찬가지로 순수 그래프 계산이다 — gm/ID 스펙을
    깨지 않는지는 호출자가 별도로 재검증해야 한다(L4, 아직 미구현).

    ⚠️ **2026-08-10 버그 수정(세션26 후속(2), 실측 발견)**: 이전 구현은 `pair_map:
    name -> partner` 단일 매핑으로 "쌍"을 표현했는데, `matching_pairs`에 3-way 이상
    declared 그룹의 **모든 쌍 조합**(예: `itertools.combinations(['A','B','C'], 2)` =
    `[(A,B),(A,C),(B,C)]`, `run_topology_pipeline_with_finger_fixup()`이 실제로 이
    형태로 넘김)이 들어오면 나중 쌍이 앞 쌍의 매핑을 조용히 덮어써서 일부 조합이
    **후보에서 통째로 사라졌다**(`current_reuse_telescopic_ota`의 `M18_bg`/`M60`/
    `M61` 실측: `(M18_bg,M60)` 조합-- 유일하게 gm/ID까지 통과하는 해법이었다 --가
    이 덮어쓰기로 한 번도 시도되지 못해 `unresolved_row`로 5라운드를 전부 소진하는
    실제 사고로 이어짐). 이제 **선언된 쌍마다 독립적인 조정 단위**로 취급한다(단일
    매칭 커버가 아니라, 그 소자가 참여하는 모든 declared 쌍 각각을 후보로 낸다) --
    한 소자가 여러 쌍에 동시에 나타나도(3-way 이상 그룹의 정상적인 모습) 전부 별도
    후보로 살아남는다. 어느 쌍에도 없는 소자만 미매칭 단독 후보가 된다.

    반환: `resulting_odd_count` 오름차순 정렬(맨 앞이 가장 많이 개선되는 조정)."""
    baseline_graph = build_graph(transistors)
    baseline_odd = len(check_euler_condition(baseline_graph).odd_nodes)

    group_names = {t.name for t in transistors}
    units = []
    seen_pairs = set()
    paired_names = set()
    for a, b in matching_pairs:
        if a not in group_names or b not in group_names:
            continue
        key = tuple(sorted((a, b)))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        units.append(key)
        paired_names.add(a)
        paired_names.add(b)
    for t in transistors:
        if t.name not in paired_names:
            units.append((t.name,))

    by_name = {t.name: t for t in transistors}
    results = []
    for unit in units:
        if len(unit) == 2 and by_name[unit[0]].n_fingers != by_name[unit[1]].n_fingers:
            continue  # 이미 비율이 깨진 쌍 — 동시 조정으로는 비율을 못 지키므로 제외
        for delta in (+1, -1):
            trial = list(transistors)
            ok = True
            for name in unit:
                idx = next(i for i, t in enumerate(trial) if t.name == name)
                new_n = trial[idx].n_fingers + delta
                if new_n < 1:
                    ok = False
                    break
                trial[idx] = _dc_replace(trial[idx], n_fingers=new_n)
            if not ok:
                continue
            trial_graph = build_graph(trial)
            odd_count = len(check_euler_condition(trial_graph).odd_nodes)
            if odd_count < baseline_odd:
                note = f"차수 개선: 홀수 노드 {baseline_odd}개 → {odd_count}개"
            elif odd_count == baseline_odd:
                note = "총 홀수 노드 수는 그대로(불균형이 다른 노드로 이동)"
            else:
                note = f"오히려 악화: 홀수 노드 {baseline_odd}개 → {odd_count}개"
            results.append(PairAdjustmentSuggestion(unit, delta, odd_count, note))

    results.sort(key=lambda s: s.resulting_odd_count)
    return results


# ---------------------------------------------------------------------------
# 5.5) Unit cell 사이징 후보 탐색 — gm/ID 스펙(nominal W)에 가까우면서 §3.5(정수배)는 처음부터
#      만족하는 (unit cell 폭, finger 수) 후보를 생성한다. §8(box-shape)은 이 함수가 보장하지
#      않는다 — 호출자가 후보를 §5/§8 기준으로 직접 골라야 한다(아래 docstring 참고).
#      suggest_finger_adjustments()가 "이미 있는 finger 구성을 ±1 고치는" 반응형이라면, 이건
#      "애초에 어떤 unit cell로 조립할지" 하나를 정하는 생성형 탐색이다 — §1 워크플로우의
#      "stack 분할" 이전 단계에서 쓴다.
# ---------------------------------------------------------------------------

@dataclass
class UnitCellCandidate:
    unit_w: float
    n_fingers: int
    w: float                 # = unit_w * n_fingers
    rel_error: float         # nominal_w 대비 상대오차


def search_unit_cell_sizing(nominal_w: float, candidate_unit_widths: list,
                             min_n: int = 1, max_n: int = 20) -> list:
    """gm/ID sizing이 준 `nominal_w` 근방에서, 후보 unit cell 폭(`candidate_unit_widths`,
    보통 같은 stack의 다른 matched 소자들이 이미 쓰는 finger 폭들)마다 정수 finger 수 N을
    전부 나열해 W=N×unit_w 후보를 만든다 — §3.5(W가 finger 폭의 정수배)를 처음부터 만족하는
    후보만 생성하는 것이므로, 이후 `check_finger_width_compatibility()`를 다시 돌릴 필요가 없다.

    결과는 `nominal_w` 대비 상대오차 오름차순으로 정렬된다 — 맨 앞 후보가 gm/ID 스펙에 가장
    가깝다. 하지만 **오차가 가장 작은 후보가 항상 정답은 아니다**: 이 함수는 스펙(§5
    체크리스트)도 shape(§8)도 모른다 — 후보들을 순서대로 훑으며 (a) §5 체크리스트 재검증을
    통과하는지, (b) 그 stack/다른 stack들과 finger 수가 비슷해 box-shape에 가까워지는지를
    호출자가 직접 판단해서 골라야 한다. 이 함수는 "후보 생성"만 한다.
    """
    candidates = []
    for uw in candidate_unit_widths:
        for n in range(min_n, max_n + 1):
            w = n * uw
            candidates.append(UnitCellCandidate(uw, n, w, abs(w - nominal_w) / nominal_w))
    candidates.sort(key=lambda c: c.rel_error)
    return candidates


# ---------------------------------------------------------------------------
# 5.7) Cell shape(box) 균형 탐색 — §8 지원 도구
# ---------------------------------------------------------------------------

def _quantize_to_grid(x: float, grid_step: float, mode: str = "nearest") -> float:
    """`sizing_recipe.quantize_L()`과 정확히 같은 공식(길이 치수를 `grid_step`의 배수로
    스냅)의 로컬 사본 — `sizing_recipe.py`가 이 파일(`stick_diagram.py`)을 import하므로
    반대 방향 import는 순환참조가 된다(2026-08-13 세션31 이어, box-shape finger_w에도
    공정 manufacturing grid를 적용하기 위해 신설 — `.ai/context.md` 세션31 CD 참고).
    구현이 3줄짜리 순수 함수라 사본 유지 비용이 낮다."""
    if grid_step <= 0:
        raise ValueError(f"grid_step={grid_step}은 0보다 커야 한다")
    fn = {"nearest": round, "floor": math.floor, "ceil": math.ceil}.get(mode)
    if fn is None:
        raise ValueError(f"알 수 없는 mode={mode!r}")
    return fn(x / grid_step) * grid_step


@dataclass
class BoxLayoutCandidate:
    finger_w: float                  # 이 stack에 쓸 unit cell 폭(um) — 다른 stack과 다를 수 있다
    n_fingers_per_device: dict       # {device_name: n_fingers}
    total_row_fingers: int           # 이 stack 전체 행의 finger 총합 = 물리적 행 길이(box 판정 기준)
    snap_error_per_device: dict = field(default_factory=dict)  # grid_step 지정 시만 채워짐(그 외 빈 dict = 오차 0)
    max_snap_error: float = 0.0      # snap_error_per_device의 최댓값(grid_step 미지정이면 0.0)


def search_stack_finger_w(devices: dict, target_row_fingers: int,
                           min_finger_w: float = 1.0, max_finger_w: float = 40.0,
                           tol_fingers: int = 3, max_n: int = 200,
                           grid_step: float | None = None,
                           max_snap_error: float = 0.01) -> list:
    """§8 "cell shape(box) 판단 기준"을 실제로 실행 가능하게 만드는 탐색 도구.

    배경(2026-07-23 사용자 피드백): N단(예: 3핑거)과 P단(예: 32핑거)처럼 stack마다 총 W가
    크게 다르면, **같은 finger_w를 억지로 맞추려 하면 안 되고 애초에 맞출 필요도 없다** —
    finger_w(unit cell)가 균일해야 하는 범위는 §3.5/§4가 요구하는 대로 "같은 stack(같은 물리
    행) 안"뿐이다. 서로 다른 stack(N단/P단, 혹은 folded cascode의 top/mid/bot tier)은 각자
    다른 finger_w를 써도 무방하며, PDF의 folded cascode 예제도 실제로 tier마다 다른 finger_w
    (M3/M4/MP=10, M1/M2=8, M9/M10/M7/M8/M11/MN=8 등)를 쓰고 있다 — 이 자유도를 "총 W가 다른
    stack들의 행 길이(=finger 개수)를 서로 맞추는" 용도로 적극 활용하는 것이 §8의 실제 실행
    방법이다. 이 함수가 그 "stack마다 finger_w를 얼마로 잡을지"를 숫자로 먼저 탐색하는 절차를
    코드화한다 — PDF가 숫자/문자 라벨(1,2,3,...,x,o,n,P)로 각 stack의 배치를 미리 탐색해보고
    box가 되는 조합을 확정하는 것과 같은 역할.

    devices: {device_name: W_um} — 이 stack에 속한 소자들의 총 W(gm/ID sizing 결과, 아직
    finger로 안 쪼갠 실수 값). 보통 matching pair/mirror는 W가 서로 동일하므로 그 경우
    후보가 충분히 나온다. Ratio-matched(W가 서로 다른) 그룹은 finger_w가 모든 W의 공약수여야
    하므로 후보가 급격히 줄거나 없을 수 있다 — 그때는 빈 리스트가 반환되며, unit cell 자체를
    재정의(§4)하는 논의로 넘어가야 한다는 신호다.

    target_row_fingers: 맞추고 싶은 목표 행 길이(finger 개수) — 보통 다른 stack의 실제
    finger 개수. tol_fingers 이내로 차이나는 후보까지 포함해 반환한다(정확히 일치하는 후보가
    없을 수 있으므로).

    반환은 total_row_fingers가 target에 가까운 순으로 정렬된 BoxLayoutCandidate 리스트다.
    이 함수는 **한 stack**만 다룬다 — 여러 stack을 동시에 맞추려면 각 stack에 대해 따로 호출한
    뒤, 나온 total_row_fingers들을 호출자가 직접 비교해서 그 조합이 정말 서로 가까운지
    판단해야 한다(2-stack 이상을 동시에 맞추는 완전탐색은 하지 않는다 — search_unit_cell_sizing
    과 같은 철학: "후보 생성"까지만 하고 최종 채택은 §5 재검증 + 설계자 판단에 맡긴다).

    `grid_step`(선택, m 단위 — 예: sky130 MANUFACTURINGGRID 5nm, `sizing_recipe.py`의
    `L_grid_step`과 동일 근거): 주어지면 후보 finger_w를 공정 그리드에 스냅한다(`_quantize_
    to_grid()`) — 그리드 스냅 전엔 `base_w/n1`이 항상 정확히 나누어떨어졌지만, 스냅 후엔
    작은 오차가 남는다(예: sky130 5nm 그리드 실측 최악 케이스 W 상대오차 0.25% —
    `.ai/context.md` 세션31 CD 참고). W는 gm/ID LUT의 `W_ref` 선형 스케일링이라(L처럼
    비선형 재보간이 필요 없음) 이 정도 오차는 gm/gds/ID에도 선형으로만 실려 안전하다.
    `max_snap_error`(기본 1%)를 넘는 소자가 하나라도 있으면 그 후보는 버린다. 반환되는
    `BoxLayoutCandidate.snap_error_per_device`/`max_snap_error`로 실제 오차를 확인할 것.
    `grid_step=None`(기본)이면 기존 동작(정확히 나누어떨어지는 후보만, 오차 0) 그대로 —
    100% 하위호환, 기존 호출부는 전혀 영향받지 않는다."""
    names = list(devices.keys())
    widths = list(devices.values())
    if not widths:
        return []
    base_w = widths[0]
    results = []
    seen_fw = set()
    for n1 in range(1, max_n + 1):
        fw = base_w / n1
        if grid_step is not None:
            fw = _quantize_to_grid(fw, grid_step, mode="nearest")
            if fw <= 0 or fw in seen_fw:
                continue
            seen_fw.add(fw)
        if not (min_finger_w <= fw <= max_finger_w):
            continue
        per_device = {}
        snap_err = {}
        total = 0
        ok = True
        for name, w in zip(names, widths):
            n = w / fw
            if grid_step is None:
                if abs(n - round(n)) > 1e-6 or round(n) < 1:
                    ok = False
                    break
                per_device[name] = round(n)
            else:
                rn = max(1, round(n))
                err = abs(w - rn * fw) / w
                if err > max_snap_error:
                    ok = False
                    break
                per_device[name] = rn
                snap_err[name] = err
            total += per_device[name]
        if ok and abs(total - target_row_fingers) <= tol_fingers:
            results.append(BoxLayoutCandidate(
                finger_w=fw, n_fingers_per_device=per_device, total_row_fingers=total,
                snap_error_per_device=dict(snap_err),
                max_snap_error=max(snap_err.values()) if snap_err else 0.0))
    results.sort(key=lambda c: (abs(c.total_row_fingers - target_row_fingers), c.finger_w))
    return results


def assign_finger_geometry(sizing_results: dict, stack_groups: dict, area_priors: dict | None = None,
                            min_finger_w: float = 1.0, max_finger_w: float = 40.0) -> dict:
    """배치 7-6(2026-07-31) — `size_transistor()`가 만든 raw `W`(사이징 결과)와
    `derive_stack_groups()`가 만든 stack 후보를 이어 `run_topology_pipeline()`이 요구하는
    `sizing_overrides`(`{name: {"n_fingers","finger_w","w","stack_id","l"}}`)를 자동 구성한다
    — bootstrapping 문제(`search_stack_finger_w()`/`search_unit_cell_sizing()` 둘 다 "맞출
    참조값"이 이미 있어야 동작하는데, 맨 처음 stack엔 맞출 대상이 없음)를 seed 선택으로
    해결한다.

    `sizing_results`: `{device_name: SizingResult 또는 {"W": float, "L": float, ...}}` —
    `size_transistor()`류의 결과, `.W` 속성 또는 `["W"]` 키 둘 다 받는다. **2026-08-13(세션31)**:
    `l`(channel length, `Transistor.l` — box-shape/floorplan 실제 물리 폭 계산에 쓰임)도
    같은 방식으로 뽑아서 `overrides`에 함께 채운다 — `sizing_results[name]`이 대문자
    `"L"` 키(`optimize_full_circuit_budget()`의 `ctx.sized`가 실제로 쓰는 키)인 반면
    `Transistor`/`overrides`는 소문자 `l`이다: **의도적 rename**이지 통과시키는 키가
    아니다(이 프로젝트가 반복 겪은 키 이름 불일치 사고를 피하려고 여기 명시해둔다).
    L이 없는 입력(예: `{"W": val}`만 있는 self-test/legacy 호출)이면 `overrides[name]["l"]
    = None`이 되고, 이는 `Transistor.l=None`과 동일한 의미(근사 계산에서 그 소자만
    빠짐, `compute_row_geometry()` 참고)다 — 조용히 실패하지 않는다.

    정책(§7.9 질문12(a) — 미결, 아래 참고): `stack_groups`를 총 W 합 내림차순 정렬해 가장
    큰 stack을 **seed**로 놓고, 그 stack 자체의 `search_stack_finger_w()` 후보 중
    `total_row_fingers`가 가장 작은(=finger_w가 가장 큰, 가장 컴팩트한) 후보를 채택한다.
    나머지 stack은 이미 확정된 stack들의 `total_row_fingers`를 target으로 순서대로
    `search_stack_finger_w()`를 호출하고, 후보가 없으면 (a) target 없이 폭넓게 재탐색,
    그래도 없으면 (b) `search_unit_cell_sizing()`(이미 확정된 stack들의 finger_w를
    `candidate_unit_widths`로)으로 완화한다. 그래도 후보가 없으면 이 stack의 소자들이
    서로 비율-호환되지 않는다는 뜻이라 `ValueError`(조용히 억지 배정하지 않음 — 이후
    `audit_row_split()`/`repair_matching_safety()`가 아니라 사이징 자체를 재검토해야 하는
    더 근본적인 문제이므로).

    ⚠️ 정직한 한계(2026-07-31): (1) `area_priors`는 아직 계산에 쓰이지 않는다(시그니처에만
    있음 — do.md 원안의 "완화 기준"이 정확한 공식으로 확정되지 않아, `estimate_area_budget()`
    의 `kind` 인자와 같은 성격의 예약 필드로 남겨둠). (2) seed stack 선택 정책("가장 큰
    stack 먼저")이 항상 최선인지는 검증되지 않았다(§7.9 질문12(a) 그대로 미결 — 실제 회로
    몇 개를 더 돌려봐야 판단 가능)."""
    def _w_of(name):
        r = sizing_results[name]
        return r.W if hasattr(r, "W") else r["W"]

    def _l_of(name):
        r = sizing_results[name]
        if hasattr(r, "L"):
            return r.L
        if isinstance(r, dict):
            return r.get("L")
        return None

    stacks = {sid: {n: _w_of(n) for n in members} for sid, members in stack_groups.items()}
    order = sorted(stacks.keys(), key=lambda sid: sum(stacks[sid].values()), reverse=True)

    overrides = {}
    assigned_targets: list = []
    assigned_finger_widths: list = []

    for i, sid in enumerate(order):
        devices = stacks[sid]
        if i == 0:
            candidates = search_stack_finger_w(devices, target_row_fingers=1,
                                                min_finger_w=min_finger_w, max_finger_w=max_finger_w,
                                                tol_fingers=10 ** 6)
        else:
            candidates = search_stack_finger_w(devices, target_row_fingers=assigned_targets[-1],
                                                min_finger_w=min_finger_w, max_finger_w=max_finger_w)
            if not candidates:
                candidates = search_stack_finger_w(devices, target_row_fingers=1,
                                                    min_finger_w=min_finger_w, max_finger_w=max_finger_w,
                                                    tol_fingers=10 ** 6)
            if not candidates and assigned_finger_widths:
                nominal_w = next(iter(devices.values()))
                unit_candidates = search_unit_cell_sizing(nominal_w, assigned_finger_widths)
                if unit_candidates:
                    best_unit = unit_candidates[0]
                    for name, w in devices.items():
                        n = max(1, round(w / best_unit.unit_w))
                        overrides[name] = {"n_fingers": n, "finger_w": best_unit.unit_w,
                                           "w": n * best_unit.unit_w, "stack_id": sid,
                                           "l": _l_of(name)}
                    assigned_targets.append(sum(overrides[n]["n_fingers"] for n in devices))
                    assigned_finger_widths.append(best_unit.unit_w)
                    continue
        if not candidates:
            raise ValueError(
                f"stack {sid!r}(소자 {sorted(devices)})에 대해 어떤 finger_w 후보도 못 찾음 "
                f"(min_finger_w={min_finger_w}, max_finger_w={max_finger_w}) -- 이 stack의 "
                f"소자들이 서로 비율-호환되지 않는다는 뜻(사이징 자체를 재검토할 것)")
        best = candidates[0]
        for name in devices:
            n = best.n_fingers_per_device[name]
            overrides[name] = {"n_fingers": n, "finger_w": best.finger_w,
                               "w": n * best.finger_w, "stack_id": sid,
                               "l": _l_of(name)}
        assigned_targets.append(best.total_row_fingers)
        assigned_finger_widths.append(best.finger_w)

    return overrides


def apply_explicit_row_split(rows: dict, row_split: dict) -> dict:
    """`row_split`(`{stack_id: n_rows}`)에 명시된 stack을 `n_rows`개 물리 행으로 균등
    분할한다 -- box-shape 비율을 맞추기 위한 **명시적 소자 folding**(2026-08-13 세션31,
    사용자 승인 -- `two_stage_ota`의 M6처럼 매칭 파트너가 없는 단독 소자가 box-shape
    비율을 지배할 때, 그 소자 자체를 여러 병렬 물리 인스턴스로 접는 것 -- 추가 contact/via
    비용이 실제로 든다). `repair_matching_safety()`/`common_centroid_layout()`이 이미
    하는 "매칭 품질(3c) 개선을 위한 자동 재배치"와는 목적이 다르다 -- 그건 자동 판단이지만,
    이건 순수 면적/비율 목적이라 자동으로 판단하지 않고 **호출자가 명시적으로 선언**해야만
    적용된다(§8.5 원칙: box-shape FAIL을 수용할지 분할할지는 설계자 판단).

    `rows`의 각 stack 안에 소자가 여러 개(예: 매칭쌍)여도 **소자별로 독립적으로** 접는다
    (`_fixup_euler_blocked_rows()`의 `_connected_components()`처럼 여러 소자를 하나로
    묶어 재배치하는 게 아니다 -- 이건 "이 stack의 모든 소자를 각자 n_rows로 접어라"는
    단순 요청). 소자의 `n_fingers`를 `n_rows`로 최대한 고르게 나누고(나머지는 앞쪽 조각부터
    +1), 0개가 되는 조각은 만들지 않는다(n_fingers < n_rows면 실제로는 그보다 적은 행만
    생긴다 -- 조용히 무시하지 않고 반환된 행 개수로 그 사실이 드러난다).

    각 조각은 새 `stack_id` `f"{sid}_split{i}"`를 받는다. `row_split`에 없는 stack은
    손대지 않고 그대로 반환한다(기본 동작 100% 보존, opt-in).

    반환: 갱신된 `rows` dict."""
    new_rows = {}
    for sid, devs in rows.items():
        n_rows = row_split.get(sid)
        if not n_rows or n_rows <= 1:
            new_rows[sid] = list(devs)
            continue
        per_device_chunks = {}
        for t in devs:
            base, rem = divmod(t.n_fingers, n_rows)
            chunk_ns = [base + (1 if i < rem else 0) for i in range(n_rows)]
            per_device_chunks[t.name] = [n for n in chunk_ns if n > 0]
        max_chunks = max((len(v) for v in per_device_chunks.values()), default=0)
        for i in range(max_chunks):
            split_sid = f"{sid}_split{i}"
            row_devs = []
            for t in devs:
                chunks = per_device_chunks[t.name]
                if i < len(chunks):
                    row_devs.append(_dc_replace(t, n_fingers=chunks[i], stack_id=split_sid))
            if row_devs:
                new_rows[split_sid] = row_devs
    return new_rows


# ---------------------------------------------------------------------------
# 5.75) Cell shape(box) 균형 — 가로 배치(Case B) 자매 함수. search_stack_finger_w()(Case A,
#       위)는 "행 폭(n_fingers)을 목표로 고정하고 stack마다 finger_w를 다르게 찾아" 여러 행을
#       **세로로 쌓는다.** schematic의 다단(multi-stage) 캐스케이드가 좌→우로 흐르는 경우
#       (예: NGCC 3단을 schematic 그대로 나란히 배치), 맞춰야 하는 건 반대다 — **행 높이
#       (finger_w)를 stage 전체에서 하나로 통일하고, 각 stage의 폭(n_fingers)은 자유도로
#       둬서** 좌우로 나란히 놓는다(책이 두께는 달라도 높이가 같으면 책장에 나란히 꽂히는
#       것과 같은 원리). 어느 쪽을 쓸지는 schematic의 캐스케이드 방향(세로로 이어지면 Case A,
#       가로로 이어지면 Case B)이 1차 기준이다 — §4.2 참고.
# ---------------------------------------------------------------------------

@dataclass
class SharedFingerWCandidate:
    finger_w: float                   # 여러 stage가 공유할 단일 finger_w(um) 후보
    n_fingers_per_device: dict        # {device_name: n_fingers} — round(W/finger_w), 최소 min_fingers
    snap_error_per_device: dict       # {device_name: |W - n*finger_w| / W} — 상대 스냅 오차
    max_snap_error: float             # 이 후보의 가장 나쁜(=제일 안 맞는) 소자의 오차


def search_shared_finger_w(devices: dict, min_finger_w: float = 0.4, max_finger_w: float = 45.0,
                            min_fingers: int = 1, max_n: int = 200,
                            grid_step: float | None = None) -> list:
    """§4.2/Case B — 여러 stage에 걸친 소자들이 **하나의 공통 finger_w**를 쓰도록(=행 높이를
    통일해 좌우로 나란히 배치할 수 있도록) finger_w 후보를 찾는다. `search_stack_finger_w()`
    (Case A)의 정반대 방향 자매 함수: 거기서는 n_fingers를 고정하고 finger_w를 stack마다
    다르게 찾았는데, 여기서는 finger_w 하나를 고정하고 n_fingers가 stage마다 자유도다.

    ⚠️ Case A와 근본적으로 다른 점: Case A는 **정확히**(1e-6 이내) 나누어떨어지는 finger_w를
    요구해도 대개 존재한다(matching pair는 W가 같으니까). 하지만 서로 다른 stage의 W는 대개
    서로 무관한 실수값이라(실측 예: Example 3의 M2=4.185um vs M3b=313.626um, 75배 차이),
    **모든 소자에 정확히 맞는 finger_w는 일반적으로 존재하지 않는다.** 그래서 이 함수는
    "완전히 맞는 후보"가 아니라 **"가장 스냅 오차가 적은 후보"**를 찾는다 — 반환되는
    `max_snap_error`(가장 안 맞는 소자 기준)를 보고 그 오차가 §5 재검증을 통과할 만큼
    작은지 호출자가 판단해야 한다(오차가 크면 이 stage-column은 Case B로 묶기보다 별도
    행으로 두는 게 나을 수 있다는 신호 — §4.1의 "병합이 항상 이득은 아니다"와 같은 맥락).

    devices: {device_name: W_um} — **여러 stage에 걸친** 전체 소자 목록(한 stack이 아니라
    "행 높이를 맞추고 싶은 모든 소자"). min_fingers: 소자당 최소 finger 수(기본 1 — matching
    쌍이 짝수/특정 최소치가 필요하면 반환값에서 호출자가 추가로 걸러낼 것. §4.1의 3-leaf
    병합까지 겹치는 경우는 `check_multi_leaf_hub_parity()`로 별도 확인).

    반환: 후보를 **최대 스냅 오차가 작은 순**으로 정렬한 `SharedFingerWCandidate` 리스트.
    후보 finger_w는 각 소자의 W/k(k=1..max_n)를 전부 모은 값들에서 가져온다 — "적어도 한
    소자에게는 정확히 맞는" 값들이 전체적으로도 좋은 근사일 가능성이 높기 때문이다.

    `grid_step`(선택, m 단위 — `search_stack_finger_w()`와 동일 근거/`_quantize_to_grid()`
    재사용): 주어지면 seed finger_w를 공정 그리드에 스냅한다. 이 함수는 애초에 "정확히
    안 맞을 수 있다"는 전제로 설계돼 `snap_error`를 이미 항상 계산하므로(§8.2와 달리
    tolerance로 후보를 버리지 않음), 그리드 스냅은 seed 생성 단계에 한 줄만 추가하면
    충분하다 — 스냅으로 늘어나는 오차는 반환된 `max_snap_error`에 그대로 반영되어 호출자가
    판단한다. `grid_step=None`(기본)이면 기존 동작 그대로."""
    seeds = set()
    for w in devices.values():
        for k in range(1, max_n + 1):
            fw = w / k
            if grid_step is not None:
                fw = _quantize_to_grid(fw, grid_step, mode="nearest")
                if fw <= 0:
                    continue
            if min_finger_w <= fw <= max_finger_w:
                seeds.add(fw)
    results = []
    for fw in seeds:
        per_device_n, per_device_err = {}, {}
        for name, w in devices.items():
            n = max(min_fingers, round(w / fw))
            per_device_n[name] = n
            per_device_err[name] = abs(w - n * fw) / w
        results.append(SharedFingerWCandidate(
            finger_w=fw, n_fingers_per_device=per_device_n,
            snap_error_per_device=per_device_err, max_snap_error=max(per_device_err.values()),
        ))
    results.sort(key=lambda c: c.max_snap_error)
    return results


# ---------------------------------------------------------------------------
# 5.8) 실제 물리 치수 근사 — Transistor.l/finger_w 기반 행 폭/높이 (2026-08-13 세션31 신설)
#
# 왜: check_box_shape()/block_from_row_widths()가 지금까지 row_widths={row: n_fingers 합}만
# 받아서 실제 물리 폭(L에 비례하는 finger pitch)도, 실제 물리 높이(finger_w)도 전혀 반영하지
# 못했다. sizing↔layout 피드백 루프가 실제로 수렴하려면(레이아웃에서 고친 finger/finger_w가
# 다시 sizing에 반영돼 면적이 실제로 최소화돼야 하므로) 이 추정치가 real layout과 상관성이
# 있어야 한다는 게 이 신설의 근거(.ai/context.md 세션31 CQ 이후 사용자 지적) — 기존
# "실제 물리 치수로 착각하지 말 것, 순수 비율 프록시" 원칙보다 이 요구가 우선한다.
# ---------------------------------------------------------------------------

PROCESS_GEOMETRY = {
    # sky130 poly pitch/gate-to-gate spacing(CPP)이 미확보 상태다 -- 로컬 PDK
    # (/c/pdk/sky130_fd_pr)엔 SPICE 모델만 있고 LEF/tech 파일이 전혀 없고,
    # references/lut-generation-checklist.md §8.2의 W_min/L_min과 동일하게 "sky130
    # 자신도 1차 출처로 확정 못함" 처지다. 확보 전까지 L 이외의 추가 폭(overhead)은
    # 0으로 둔다(과소평가 근사) -- 확보되면 이 값 하나만 교체하면 전체 파이프라인에
    # 반영된다(호출부 수정 불필요).
    "finger_pitch_overhead_m": 0.0,
}


def pitch(l: float) -> float:
    """finger 1개가 실제로 차지하는 폭(gate 방향) 근사치.

    ⚠️ sky130 CPP(poly pitch/gate-to-gate spacing)를 확보하기 전까지의 **잠정 근사**다:
    `pitch(l) = l + PROCESS_GEOMETRY["finger_pitch_overhead_m"]`(현재 0 — L 이외 추가 폭
    없음으로 둔다). 실제로는 poly-to-poly spacing/contact 여유가 있어 진짜 pitch는 l보다
    크다 — 이 함수는 그 사실을 숨기지 않고 **과소평가(낙관적) 근사**임을 호출자에게
    명시하기 위해 존재한다(값을 호출부마다 따로 박아넣지 않고 반드시 이 함수를 거치게
    해서, CPP 확보 시 `PROCESS_GEOMETRY` 한 곳만 고치면 되게 만든다)."""
    return l + PROCESS_GEOMETRY["finger_pitch_overhead_m"]


@dataclass
class RowGeometry:
    row_name: str
    width_m: float | None       # sum(n_fingers * pitch(l)) -- 결측 있으면 None
    height_m: float | None      # 그 행의 finger_w(균일해야 함) -- 결측 있으면 None
    n_fingers_total: int
    approx_devices: list = field(default_factory=list)  # l/finger_w 없어 근사에서 빠진 소자명


def compute_row_geometry(rows: dict, tol: float = 1e-9) -> dict:
    """`rows: {row_name: [Transistor,...]}` -> `{row_name: RowGeometry}`.

    width_m: 그 행의 실제 물리 폭 근사 = `sum(t.n_fingers * pitch(t.l) for t in devices)`
    (한 행 안에 서로 다른 l을 가진 소자가 섞여도 각자의 pitch로 기여분을 따로 계산한다 —
    Euler trail로 여러 소자가 한 diffusion strip에 섞이는 게 이 모듈의 정상 동작이므로).

    height_m: 그 행의 실제 물리 높이 = 그 행에 속한 모든 소자의 `finger_w`. **반드시
    동일해야 한다** — 물리적으로 diffusion strip 하나는 폭(=finger_w)이 하나뿐이다.
    `check_finger_width_compatibility()`는 이 균일성을 보장하지 않는다(소자별 W/finger_w
    정수배만 검사한다) — 여기서 새로 검증한다: 한 행 안에서 finger_w가 다르면 물리적으로
    불가능하므로 `ValueError`(`build_graph()`의 kind 동질성 하드 게이트와 같은 성격).

    `l` 또는 `finger_w`가 없는 소자가 있으면(아직 실사이징 전 등) 그 소자는
    `RowGeometry.approx_devices`에 이름이 남고, 그 행의 `width_m`/`height_m`은 `None`이
    된다(조용히 옛 finger-count 근사로 대체하지 않는다 — 이 모듈의 기존 "조용한 자동
    수정 금지" 원칙과 동일). 호출자(`check_box_shape` 등)가 `None`을 어떻게 다룰지는
    거기서 결정한다."""
    geoms = {}
    for row_name, devices in rows.items():
        approx = [t.name for t in devices if t.l is None or t.finger_w is None]
        n_total = sum(t.n_fingers for t in devices)
        if approx:
            geoms[row_name] = RowGeometry(row_name, width_m=None, height_m=None,
                                           n_fingers_total=n_total, approx_devices=approx)
            continue
        finger_ws = {t.finger_w for t in devices}
        if len(finger_ws) > 1:
            raise ValueError(
                f"행 {row_name!r}: 같은 diffusion strip인데 finger_w가 소자마다 다름"
                f"({ {t.name: t.finger_w for t in devices} }) -- 물리적으로 불가능하다"
                f"(diffusion strip 하나는 폭이 하나뿐). §2.7/§8로 행 구성을 다시 정할 것.")
        width_m = sum(t.n_fingers * pitch(t.l) for t in devices)
        height_m = next(iter(finger_ws))
        geoms[row_name] = RowGeometry(row_name, width_m=width_m, height_m=height_m,
                                       n_fingers_total=n_total, approx_devices=[])
    return geoms


@dataclass
class BoxShapeVerdict:
    ok: bool                 # rectangular and elongation_ok
    rectangular: bool        # row_width_tol 통과 여부(행 폭들이 서로 일치 -> 진짜 직사각형)
    elongation_ok: bool      # max_elongation 통과 여부(max_elongation=None이면 항상 True)
    row_widths: dict         # {row_label: width_m} -- 실제 물리 폭(m). 결측 있으면 finger_count 근사
    row_heights: dict        # {row_label: height_m} -- 실제 물리 높이(m). 결측 있으면 1(옛 근사)
    total_width_m: float
    total_height_m: float
    width_ratio: float       # max(row_widths)/min(row_widths) -- rectangular 판정 근거
    elongation: float        # max(total_w,total_h)/min(total_w,total_h)
    approx: bool             # 하나 이상의 행이 l/finger_w 없어 근사(finger_count)로 계산됐으면 True
    message: str


def check_box_shape(rows: dict, row_width_tol: float = 1.5,
                     max_elongation: float | None = None,
                     orientation: str = "either") -> BoxShapeVerdict:
    """§8 cell shape 게이트 — **SPICE 검증으로 넘어가기 전에 반드시 통과해야 하는 체크포인트**.

    이 세션에서 반복된 실수(Example 1: nstack 3 vs pstack 32, 10.7:1 'ㄱ'자 셀 / Example 2:
    diffpair 9×2행 vs tailstack 24 vs loadstack 38)는 전부 "sizing → SPICE 검증"으로 바로
    넘어가고 box-shape를 나중에야(혹은 사용자가 지적해서야) 확인했기 때문에 생겼다.

    2026-08-13(세션31): "행 폭이 다르면 쌓아도 직사각형이 안 된다"는 것과 "직사각형이어도
    너무 길쭉하면 문제다"는 것은 **서로 다른 질문**이라(사용자 지적) 판정을 둘로 분리한다:

    1) **직사각형 형성 여부**(`rectangular`): `compute_row_geometry(rows)`가 계산한 각 행의
       실제 물리 폭(`width_m`)이 서로 얼마나 일치하는지 — `max(width)/min(width) <=
       row_width_tol`이어야 쌓았을 때 계단형이 아니라 진짜 직사각형이 된다. 이게 옛
       `max_ratio`가 실질적으로 하던 역할(Example 1의 10.7:1이 바로 이 실패)이다 — 이름만
       명확히 하고 기본값(1.5)은 그대로 유지한다.
    2) **길이 제한**(`elongation_ok`, opt-in): 1)을 통과해 직사각형이 만들어진 뒤, 전체
       폭(`total_width_m` = 각 행 폭의 최댓값, 1)이 PASS면 전부 거의 같음) 대 전체
       높이(`total_height_m` = 각 행 높이의 합)의 비율이 너무 크면 지나치게 길쭉한
       직사각형이 된다 — 예전엔 모든 행 height가 구조적으로 1로 고정돼 있어 이 축 자체가
       검사된 적이 없었다. `max_elongation=None`(기본)이면 이 축은 검사하지 않는다(기존
       회로가 이 신설 게이트로 갑자기 FAIL하지 않도록). `orientation`으로 허용 방향을
       고른다: `"wide"`(가로로만 길게 허용, height<=width 강제), `"tall"`(세로로만 길게
       허용, width<=height 강제), `"either"`(기본, 어느 방향이든 `max_elongation` 이내면
       OK).

    rows: `{row_label: [Transistor,...]}` — 실제 물리적 행이 될 모든 stack/행에 속한
    소자 리스트. common-centroid로 나눈 stack은 **행별로 따로** 넣을 것.

    l/finger_w가 없는 소자가 있는 행은 `compute_row_geometry()`가 `width_m=None`을
    반환하고, 여기서는 그 행만 옛 finger-count 근사(`sum(t.n_fingers ...)`, height=1)로
    대체해 계산을 계속하되 `BoxShapeVerdict.approx=True`로 명시한다(조용히 넘어가지
    않음 — 어떤 행이 근사인지는 `message`에 남는다).

    ⚠️ FAIL이면 §5 sizing↔layout 피드백 루프로 돌아가 §8(`search_stack_finger_w`)이나
    §2.7(`common_centroid_layout`)로 finger_w·행 구성을 다시 정해야 한다.
    """
    if not rows:
        return BoxShapeVerdict(ok=True, rectangular=True, elongation_ok=True, row_widths={},
                                row_heights={}, total_width_m=0.0, total_height_m=0.0,
                                width_ratio=1.0, elongation=1.0, approx=False,
                                message="행이 없음 — 검사 대상 없음")

    geoms = compute_row_geometry(rows)
    approx_rows = [name for name, g in geoms.items() if g.width_m is None]
    row_widths, row_heights = {}, {}
    for name, g in geoms.items():
        if g.width_m is None:
            row_widths[name] = float(g.n_fingers_total)   # 옛 finger-count 근사로 대체
            row_heights[name] = 1.0
        else:
            row_widths[name] = g.width_m
            row_heights[name] = g.height_m

    widths = list(row_widths.values())
    width_ratio = max(widths) / min(widths)
    rectangular = width_ratio <= row_width_tol

    total_width_m = max(widths)
    total_height_m = sum(row_heights.values())
    elongation = max(total_width_m, total_height_m) / min(total_width_m, total_height_m)

    orientation_ok = True
    if orientation == "wide":
        orientation_ok = total_height_m <= total_width_m
    elif orientation == "tall":
        orientation_ok = total_width_m <= total_height_m
    magnitude_ok = max_elongation is None or elongation <= max_elongation
    elongation_ok = orientation_ok and magnitude_ok

    ok = rectangular and elongation_ok
    verdict = "PASS" if ok else "FAIL"
    rect_detail = "직사각형 형성 OK" if rectangular else (
        f"행 폭 비율({width_ratio:.2f}) > row_width_tol({row_width_tol}) -- 계단형, "
        f"§8/§2.7로 finger_w·행 구성을 다시 정할 것")
    if max_elongation is None:
        elong_detail = ""
    elif elongation_ok:
        elong_detail = " / 길이 제한 OK"
    elif not orientation_ok:
        elong_detail = (f" / orientation={orientation!r} 위반 -- "
                         f"total_width_m={total_width_m:.3g}, total_height_m={total_height_m:.3g}"
                         f"(방향이 안 맞음, elongation 수치 자체는 {elongation:.2f}"
                         f"{'<=' if magnitude_ok else '>'}max_elongation({max_elongation})와 무관하게 FAIL)")
    else:
        elong_detail = f" / elongation({elongation:.2f}) > max_elongation({max_elongation})"
    approx_detail = f" [근사: {approx_rows}]" if approx_rows else ""
    message = f"{verdict}: {rect_detail}{elong_detail}{approx_detail}"
    return BoxShapeVerdict(ok=ok, rectangular=rectangular, elongation_ok=elongation_ok,
                            row_widths=row_widths, row_heights=row_heights,
                            total_width_m=total_width_m, total_height_m=total_height_m,
                            width_ratio=width_ratio, elongation=elongation,
                            approx=bool(approx_rows), message=message)


# ---------------------------------------------------------------------------
# 6) 최상위 API — stack 분할부터 stick diagram(또는 진단)까지 한 번에
# ---------------------------------------------------------------------------

@dataclass
class StickResult:
    stack_id: object
    status: str                     # 'ok' | 'blocked'
    node_sequence: list = field(default_factory=list)
    transistor_sequence: list = field(default_factory=list)
    odd_nodes: list = field(default_factory=list)
    connected: bool = True
    suggestions: list = field(default_factory=list)
    method: str = "graph"           # 'graph'(기존 build_graph+hierholzer) | 'mirror_symmetric'(D)


@dataclass
class WalkVerdict:
    ok: bool
    node_path: list = field(default_factory=list)
    break_index: int | None = None
    break_reason: str = ""
    finger_count_mismatch: dict = field(default_factory=dict)


def check_walk_sequence(transistor_sequence: list, transistors: list) -> WalkVerdict:
    """제안된(또는 손으로 재배열한) `transistor_sequence`가 실제로 하나의 연속된 diffusion
    strip(한붓그리기)으로 이어지는지 **독립적으로** 검증한다 — `build_stick_diagram()`/
    `hierholzer()`가 순서를 "만드는" 것과 반대로, 이미 만들어졌거나 사람이 제안한 순서를
    "검산"하는 함수다.

    ⚠️ 왜 필요한가(2026-07-27 실제 사고): 사용자가 "이런 순서로 섞을 수는 없나"며 finger
    개수는 실제 채택된 배치와 정확히 같지만 손으로 재배열한 순서(예: top_row0에
    `M3,M4,M6,M6,M5,MP,M5,M6,M6,M4`)를 제안했다 — 직접 그래프를 추적해보니 4번째 단계에서
    끊겼다(M6,M6로 Y에 돌아온 뒤 M5(X/outA에만 닿음)로 못 넘어감 — X와 Y는 vdd를 거쳐야만
    이어지는데 중간에 vdd를 거치지 않았기 때문). **"finger 개수가 맞다"는 것과 "그 순서가
    실제로 하나의 연속된 diffusion으로 이어진다"는 것은 별개 질문**이다 —
    `build_stick_diagram()`이 실제로 반환한 시퀀스가 아니라 사람이 손으로 제안했거나
    재배열한 시퀀스라면, 리포트/문서에 싣거나 채택하기 전에 반드시 이 함수로 먼저 검증할 것.

    **입력**:
    - `transistor_sequence`: 검증할 순서(예: `["M3","M6","M6","M4","M4","M3"]`).
    - `transistors`: 그 행에 속한 실제 `Transistor` 리스트 — 이름별 source/drain 조회와
      `n_fingers` 총합 대조에 쓰인다.

    **검증 절차** (둘 다 통과해야 `ok=True`):
    1. **finger 개수 일치**: `transistor_sequence`에서 각 이름의 등장 횟수가 그 소자의
       `n_fingers` 합과 정확히 같은가(다르면 `finger_count_mismatch`에 이름별 기대/실제값 기록
       — 목록에 없는 이름이 나오거나, 목록엔 있는데 시퀀스에 안 쓰인 이름도 여기 잡힌다).
    2. **연속성(continuity)**: 첫 소자의 두 단자 중 하나를 시작점으로 삼아, 순서대로 각
       소자가 "현재 위치한 노드"에 실제로 닿아 있는지 확인하며 반대쪽 단자로 이동한다 —
       중간에 현재 노드와 안 닿는 소자가 나오면 그 지점에서 끊긴 것으로 판정하고
       `break_index`/`break_reason`에 정확한 위치와 이유를 남긴다. 양쪽 시작점을 다 시도해
       하나라도 끝까지 이어지면 그 경로(`node_path`)를 채택한다."""
    by_name: dict = {}
    for t in transistors:
        if t.name not in by_name:
            by_name[t.name] = [t.source, t.drain, 0]
        by_name[t.name][2] += t.n_fingers

    actual_counts: dict = {}
    for name in transistor_sequence:
        actual_counts[name] = actual_counts.get(name, 0) + 1
    mismatches = {}
    for name, (_, __, expected) in by_name.items():
        actual = actual_counts.get(name, 0)
        if actual != expected:
            mismatches[name] = {"expected": expected, "actual": actual}
    for name in actual_counts:
        if name not in by_name:
            mismatches[name] = {"expected": 0, "actual": actual_counts[name]}

    if not transistor_sequence:
        return WalkVerdict(ok=not mismatches, finger_count_mismatch=mismatches)

    first = transistor_sequence[0]
    if first not in by_name:
        return WalkVerdict(ok=False, break_index=0,
                            break_reason=f"'{first}'가 transistors 목록에 없음",
                            finger_count_mismatch=mismatches)

    best_break_index = -1
    best_break_reason = ""
    for start in set((by_name[first][0], by_name[first][1])):
        cur = start
        path = [cur]
        ok = True
        for i, name in enumerate(transistor_sequence):
            if name not in by_name:
                ok = False
                if i > best_break_index:
                    best_break_index, best_break_reason = i, f"'{name}'가 transistors 목록에 없음"
                break
            a, b = by_name[name][0], by_name[name][1]
            if cur == a:
                nxt = b
            elif cur == b:
                nxt = a
            else:
                ok = False
                reason = (f"{i}번째 단계({name}): 현재 위치={cur}인데 {name}은 ({a},{b})에만 "
                          f"닿아 있음 -- 연결 안 됨")
                if i > best_break_index:
                    best_break_index, best_break_reason = i, reason
                break
            path.append(nxt)
            cur = nxt
        if ok:
            return WalkVerdict(ok=not mismatches, node_path=path,
                                break_reason=(f"경로는 이어지지만 finger 개수 불일치: {mismatches}"
                                              if mismatches else ""),
                                finger_count_mismatch=mismatches)
    return WalkVerdict(ok=False, break_index=best_break_index, break_reason=best_break_reason,
                        finger_count_mismatch=mismatches)


_MAX_MIRROR_TRAIL_COMBO_PAIRS = 12  # 2**12=4096 조합 — 이보다 매칭쌍이 많으면 탐색 생략(첫 조합만 시도)


def mirror_symmetric_trail(group: list[Transistor], matching_pairs: list) -> dict | None:
    """L3(walk 선택) — 세션11, `matching_pairs`를 아예 모르는 `build_graph()`+`hierholzer()`
    대신, 선언된 매칭쌍을 거울대칭으로 반영한 trail을 **구성**해본다(탐색이 아니라 구성 —
    자기동형사상을 그래프에서 찾는 대신 `matching_pairs`가 이미 알려준 대응에서 역산).

    **원리**(folded_cascode top row, current_reuse_telescopic_ota의 실제 그룹 2개로
    교차검증됨): 각 매칭쌍(A,B)에서 대표 소자 하나만 골라 "절반 그래프"를 구성하고, 그 절반의
    오일러 trail을 `build_mirror_symmetric_pattern()`으로 거울반사하면 전체 trail이 나온다 —
    실제로 그래프상 유효한지는 `check_walk_sequence()`로 직접 검증하므로(구성이 자기동형사상을
    잘못 가정했다면 여기서 실패로 걸러진다), 별도로 노드 레벨 매핑을 미리 검증할 필요가 없다.

    **대표 선택은 탐색이다(세션12 확장)**: "그룹 내 원본 순서상 먼저 나오는 쪽"을 1순위로 항상
    먼저 시도하고(세션11 기존 동작과 완전히 동일한 결과를 보장), 그 절반 그래프가 오일러
    불가능하면 나머지 대표 조합(매칭쌍마다 둘 중 하나, 2^n가지)을 순서대로 시도한다. 실측
    (`current_reuse_telescopic_ota` M3a 그룹, 4개 매칭쌍): "항상 먼저 나오는 쪽" 조합은
    홀수차수 노드 4개로 불가능하지만, 특정 조합(`M4a,M3a,M19,M18b`)은 2개(`path`)로 성립한다
    — 대표 선택에 따라 절반 그래프의 실현 가능성 자체가 달라짐을 확인했다(`.ai/context.md`
    세션12 참고).

    **홀수 self-pair = "다리"(세션12 신규)**: self-pair(미매칭)는 짝수 `n_fingers`면 기존대로
    반씩 쪼개 미러하지만, **홀수**면 쪼개지 않고 실제 `n_fingers` 그대로 절반 그래프에 한 번만
    넣고 미러 복사본에서는 제외한다(`build_mirror_symmetric_pattern()`의 `pair_map=None` 값
    지원에 의존) — 두 홀수차수 "고정점" 사이를 잇는 다리 역할. 실측(M3a 그룹의 `M5`/`M63`/
    `M64`, 전부 1개씩): 이 셋이 `gnd-M5-Vy-M63-N64_63-M64-Vbias3`로 이어지는 하나의 사슬을
    이루고, 위 대표 조합과 결합하면 11소자(핑거조정 후 13핑거) 전체가 유효한 walk로 검증된다.

    **적용 범위(의도적으로 좁음, 알려진 한계)**:
    - 1:1이 아닌(개수가 다른) 매칭쌍이 섞인 그룹은 `None`(폴백) — `auto_mirror_ratios`가 만드는
      비율 미러 등.
    - 다중 trail이 필요한 그룹(홀수차수 노드가 다리를 포함해도 2개를 못 넘는 경우)은 여전히
      이 함수 책임이 아니다(호출자가 그룹 분할 등으로 판단).
    - 매칭쌍이 매우 많으면(`_MAX_MIRROR_TRAIL_COMBO_PAIRS` 초과) 대표 조합 탐색을 생략하고
      1순위 조합만 시도한다(조합 폭발 방지).

    반환: 성공하면 `{"node_sequence": [...], "transistor_sequence": [...]}`, 실패하면 `None`."""
    pair_map = {t.name: t.name for t in group}
    group_names = set(pair_map)
    for a, b in matching_pairs:
        if a in group_names and b in group_names:
            pair_map[a] = b
            pair_map[b] = a

    n_fingers_of = {t.name: t.n_fingers for t in group}
    for a, b in pair_map.items():
        if a != b and n_fingers_of[a] != n_fingers_of[b]:
            return None

    order = {t.name: i for i, t in enumerate(group)}
    by_name = {t.name: t for t in group}

    seen = set()
    matched_pair_list = []      # [(rep_first_by_order, rep_second), ...]
    fixed_half_extra = []       # 매칭 안 된 소자(짝수 self-pair 반쪽 + 홀수 self-pair "다리")
    bridge_names = set()
    for t in group:
        if t.name in seen:
            continue
        partner = pair_map[t.name]
        seen.add(t.name)
        seen.add(partner)
        if partner == t.name:
            if t.n_fingers % 2 == 0:
                fixed_half_extra.append(_dc_replace(t, n_fingers=t.n_fingers // 2))
            else:
                fixed_half_extra.append(t)
                bridge_names.add(t.name)
        else:
            a_name, b_name = (t.name, partner) if order[t.name] < order[partner] else (partner, t.name)
            matched_pair_list.append((by_name[a_name], by_name[b_name]))

    n_pairs = len(matched_pair_list)
    combos = (itertools.product((0, 1), repeat=n_pairs) if n_pairs <= _MAX_MIRROR_TRAIL_COMBO_PAIRS
              else [(0,) * n_pairs])

    for combo in combos:
        reps = [matched_pair_list[i][choice] for i, choice in enumerate(combo)]
        half_transistors = reps + fixed_half_extra
        half_graph = build_graph(half_transistors)
        verdict = check_euler_condition(half_graph)
        if verdict.kind == "impossible":
            continue
        _, half_seq = hierholzer(half_graph, verdict.start)

        mirror_pair_map = dict(pair_map)
        for name in bridge_names:
            mirror_pair_map[name] = None
        full_seq = build_mirror_symmetric_pattern(half_seq, mirror_pair_map)
        wv = check_walk_sequence(full_seq, group)
        if wv.ok:
            return {"node_sequence": wv.node_path, "transistor_sequence": full_seq}
    return None


def build_stick_diagram(transistors: list[Transistor], matching_pairs: list | None = None) -> dict:
    """어떤 회로든(트랜지스터 리스트) 입력으로 받아 stack별 StickResult를 반환하는
    최상위 엔트리 포인트. 이 함수 하나가 skill의 "결과물"인 stick diagram 출력이다.

    `matching_pairs`(선택, 세션11 신규 — 완전한 하위호환, 기본값 `None`이면 기존 동작과
    바이트 단위로 동일): 주어지면 각 stack마다 `mirror_symmetric_trail()`을 먼저 시도하고,
    실패(`None`)하면 기존 `build_graph()+hierholzer()`로 폴백한다 — "감싸기"이지 "대체"가
    아니다. 안 주면(기본값) `mirror_symmetric_trail()`을 아예 시도하지 않는다."""
    stacks = split_into_stacks(transistors)
    results = {}
    for stack_id, group in stacks.items():
        mirrored = mirror_symmetric_trail(group, matching_pairs) if matching_pairs else None
        if mirrored is not None:
            g = build_graph(group)
            verdict = check_euler_condition(g)
            results[stack_id] = StickResult(
                stack_id=stack_id, status="ok",
                node_sequence=mirrored["node_sequence"],
                transistor_sequence=mirrored["transistor_sequence"],
                odd_nodes=verdict.odd_nodes, connected=verdict.connected,
                method="mirror_symmetric",
            )
            continue
        g = build_graph(group)
        verdict = check_euler_condition(g)
        if verdict.kind == "impossible":
            results[stack_id] = StickResult(
                stack_id=stack_id, status="blocked",
                odd_nodes=verdict.odd_nodes, connected=verdict.connected,
                suggestions=suggest_finger_adjustments(group),
            )
        else:
            nodes, trs = hierholzer(g, verdict.start)
            results[stack_id] = StickResult(
                stack_id=stack_id, status="ok",
                node_sequence=nodes, transistor_sequence=trs,
                odd_nodes=verdict.odd_nodes, connected=verdict.connected,
            )
    return results


def render_stick_diagram(result: StickResult) -> str:
    """PDF 예제(예: `3 4 3 2 1 2 1 2 3 4 3` + 그 아래 M3/M2/M1/M2/M3 레이블 줄)와 같은 형식으로
    출력한다."""
    if result.status == "blocked":
        lines = [
            f"stack {result.stack_id}: 한붓그리기 불가능"
            f"(홀수차수 노드 {len(result.odd_nodes)}개: {result.odd_nodes}, connected={result.connected})",
            "조정 후보(상위 5개, 반드시 §5 체크리스트로 재검증 후 채택):",
        ]
        for s in result.suggestions[:5]:
            sign = "+1" if s.delta_fingers > 0 else "-1"
            lines.append(f"  {s.transistor} fingers{sign} → {s.note}")
        return "\n".join(lines)

    node_strs = [str(n) for n in result.node_sequence]
    label_strs = [""] + list(result.transistor_sequence)  # 첫 node 밑엔 레이블 없음(도착 edge가 없음)
    widths = [max(len(a), len(b)) for a, b in zip(node_strs, label_strs)]
    node_row = "  ".join(s.center(w) for s, w in zip(node_strs, widths))
    label_row = "  ".join(s.center(w) for s, w in zip(label_strs, widths))
    header = f"stack {result.stack_id} ({'circuit' if not result.odd_nodes else 'path'}):"
    return f"{header}\n{node_row}\n{label_row}"


# ---------------------------------------------------------------------------
# 6.5) Worked example — Folded Cascode(PDF p.34~p.38), 원본 슬라이드에서 직접 도출한 넷리스트
# ---------------------------------------------------------------------------

def folded_cascode_example() -> list:
    """Maloberti PDF의 Folded Cascode 예제(p.34~p.38) 넷리스트.

    W·finger 폭·조정값(M7/M8 38→40µm, M9/M10 25→24µm)은 PDF p.34/p.35에서 직접 확인.
    source/drain 연결은 pptx `ppt/slides/slide5.xml`·`slide6.xml`의 실제 텍스트 도형을
    (x,y) 좌표까지 파싱해 얻은 finger-순서 문자열(`433PP443` 등)과 p.37 정답 node 시퀀스를
    위치 대조해서 역산했다 — 짐작이 아니라 원본에서 직접 읽어낸 값이다.

    ⚠️ 유일한 잔여 불확실성: top stack에서 M3/M4 중 어느 쪽이 정확히 몇 번째 finger에
    해당하는지는 finger 하나(M5 블록 바로 다음 위치)가 어느 쪽에 붙어도 그 트랜지스터의
    net-pair가 완전히 일관되지 않는다 — 원본 슬라이드 자체의 사소한 오탈자로 추정된다.
    이건 순수 命名(어느 이름을 붙이는가) 문제이고, net 차수·오일러 판정 결과 자체(§6.1
    결과 0에서 이미 원본 정답과 100% 일치 검증됨)에는 영향이 없다. 여기서는 회로이론상
    필수인 "M3.drain ≠ M4.drain"(서로 다른 folding node로 가야 함) 제약으로 확정했다:
    M3→folding node X(왼쪽, M5 방향), M4→folding node Y(오른쪽, M6 방향).
    """
    # gate net은 Euler 분석엔 안 쓰이지만 find_matching_candidates()로 matching 그룹을
    # 재현하려고 채웠다 — M3/M4, M5/M6, M7/M8, M9/M10은 각각 gate를 공유하는 전류거울/캐스코드
    # 쌍이고, M1/M2는 source(tail) 공유+gate(vin_p/vin_n) 상이라 차동쌍으로 잡힌다.
    top = [
        Transistor("MP", "pmos", source="vdd", drain="tail", gate="bias1", w=20, finger_w=10, n_fingers=2, stack_id="top"),
        Transistor("M3", "pmos", source="vdd", drain="X",    gate="bias2", w=30, finger_w=10, n_fingers=3, stack_id="top"),
        Transistor("M4", "pmos", source="vdd", drain="Y",    gate="bias2", w=30, finger_w=10, n_fingers=3, stack_id="top"),
        Transistor("M5", "pmos", source="X",   drain="outA", gate="bias3", w=60, finger_w=10, n_fingers=6, stack_id="top"),
        Transistor("M6", "pmos", source="Y",   drain="outB", gate="bias3", w=60, finger_w=10, n_fingers=6, stack_id="top"),
    ]
    mid = [
        Transistor("M1", "pmos", source="tail", drain="X", gate="vin_p", w=80, finger_w=8, n_fingers=10, stack_id="mid"),
        Transistor("M2", "pmos", source="tail", drain="Y", gate="vin_n", w=80, finger_w=8, n_fingers=10, stack_id="mid"),
    ]
    bot = [
        Transistor("M9",  "nmos", source="gnd", drain="X",   gate="bias5", w=24, finger_w=8, n_fingers=3, stack_id="bot"),
        Transistor("M10", "nmos", source="gnd", drain="Y",   gate="bias5", w=24, finger_w=8, n_fingers=3, stack_id="bot"),
        Transistor("M7",  "nmos", source="X", drain="outA",  gate="bias4", w=40, finger_w=8, n_fingers=5, stack_id="bot"),
        Transistor("M8",  "nmos", source="Y", drain="outB",  gate="bias4", w=40, finger_w=8, n_fingers=5, stack_id="bot"),
        Transistor("M11", "nmos", source="gnd", drain="vb1", gate="vb1", w=16, finger_w=8, n_fingers=2, stack_id="bot"),
        Transistor("MN",  "nmos", source="gnd", drain="vb2", gate="vb2", w=16, finger_w=8, n_fingers=2, stack_id="bot"),
    ]
    return top + mid + bot


def two_stage_ota_example() -> list:
    """Maloberti PDF의 2-Stage OTA 예제(p.28~p.33) 넷리스트.

    W·finger 수는 PDF p.28(원 W)와 p.29~p.31(finger 배분, "for M3 and M4 use 2 fingers"
    명시)에서 직접 확인. node 이름(D3, O1, CS, OUT, VDD, GND)은 p.30/p.31 스키매틱에 전부
    명시적으로 라벨링되어 있어 folded cascode 때와 달리 추론이 필요 없었다.

    ⚠️ **p.29 본문("change the size of M6 and M7 to 80 and 120 respectively")을 문자
    그대로 읽으면 M6→80, M7→120이지만, 이는 finger 구성과 모순된다**: M3/M4가 "2 fingers"로
    확정되어 있으므로 top stack의 unit cell 폭은 30µm/2=15µm/finger로 고정되고, 이 폭에서
    M6가 그림의 8 fingers를 가지려면 8×15=120µm이어야 한다(80µm이면 80/15=5.33으로 정수가
    아니라 §3.5를 어긴다). 마찬가지로 bottom stack은 M5=40µm/4finger=10µm/finger로 고정되고,
    M7이 8 fingers이려면 8×10=80µm이어야 한다(120µm이면 120/10=12로 그림의 8과 안 맞는다).
    즉 finger 수(그림에 명시된 값)와 unit cell 폭(M3/M4/M5로 고정된 값)을 함께 보면 **실제로는
    M6→120µm, M7→80µm**이 맞다 — 본문 문장의 "80과 120"이라는 언급 순서가 M6/M7과 반대로
    쓰인 것으로 보인다(원문 오탈자 추정, §6.1에서 발견한 M3/M4 사례와 같은 종류의 사소한 오류).
    """
    top = [
        Transistor("M3", "pmos", source="vdd", drain="D3",  gate="D3", w=30,  finger_w=15, n_fingers=2, stack_id="top"),
        Transistor("M4", "pmos", source="vdd", drain="O1",  gate="D3", w=30,  finger_w=15, n_fingers=2, stack_id="top"),
        Transistor("M6", "pmos", source="vdd", drain="OUT", gate="O1", w=120, finger_w=15, n_fingers=8, stack_id="top"),
    ]
    mid = [
        Transistor("M1", "nmos", source="CS", drain="D3", gate="vin_p", w=60, finger_w=10, n_fingers=6, stack_id="mid"),
        Transistor("M2", "nmos", source="CS", drain="O1", gate="vin_n", w=60, finger_w=10, n_fingers=6, stack_id="mid"),
    ]
    bot = [
        Transistor("M5", "nmos", source="gnd", drain="CS",  gate="bias", w=40, finger_w=10, n_fingers=4, stack_id="bot"),
        Transistor("M7", "nmos", source="gnd", drain="OUT", gate="bias", w=80, finger_w=10, n_fingers=8, stack_id="bot"),
    ]
    return top + mid + bot


# ---------------------------------------------------------------------------
# 6.6) 전체회로 감사 harness — sub-block별 국부 검증 반복으로 생기는 사각지대 차단
#      (2026-07-27 신설: 같은 세션에서 "sub-block 하나씩 확인 → 다른 sub-block/net-name-
#      case/cross-block 매칭을 놓침"이 4번 연속 재발한 뒤, "매번 전체를 처음부터 다시 감사하는
#      단일 게이트 스크립트"로 구조적으로 막기 위해 추가. 이 함수는 새로운 그래프 이론을
#      도입하지 않는다 — find_hub_merge_candidates()/find_matching_candidates()/
#      check_box_shape()를 "항상 전체 목록에 대해, 항상 판정 기록을 요구하며" 호출하도록
#      강제하는 얇은 오케스트레이션 계층이다.
# ---------------------------------------------------------------------------

@dataclass
class AuditCheck:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class AuditResult:
    checks: list = field(default_factory=list)
    ok: bool = True
    # 2026-08-14(세션32, 사용자 지적 -- 재계산 비효율 감사 중 발견) -- audit_row_split()이
    # "2. box-shape" 체크를 위해 이미 내부에서 check_box_shape()를 계산해두고도 ok/message만
    # AuditCheck에 남기고 그 구조화된 BoxShapeVerdict 객체 자체는 버리고 있었다 -- 그래서
    # 이 audit 결과와 별개로 box_shape가 또 필요한 호출자(예: sizing_recipe.py의
    # pipeline_result["box_shape"])는 같은 rows에 check_box_shape()를 또 불러야 했다(순수
    # 함수라 결과는 항상 같지만, "한 번 계산한 걸 저장해서 참조" 원칙에는 어긋난다). 이
    # 필드에 그 객체를 그대로 보관해 재계산 없이 재사용할 수 있게 한다 -- 순수 추가 필드라
    # 기존 .ok/.checks만 쓰던 호출부는 전혀 영향 없다.
    box_shape: "BoxShapeVerdict | None" = None

    def add(self, name, ok, detail=""):
        self.checks.append(AuditCheck(name, ok, detail))
        if not ok:
            self.ok = False


def run_full_circuit_audit(devices: dict, expected_counts: dict, dispositions: dict,
                            box_shape_checks: dict | None = None, row_width_tol: float = 1.5,
                            accept_fail_blocks: set | None = None) -> AuditResult:
    """리포트를 "완료"로 선언하기 전 **반드시 이 함수 하나로** 전체 회로를 감사한다 —
    sub-block마다 따로 짠 1회용 검증 스크립트를 다시 만들지 않는다(이게 바로 이 함수가 막으려는
    사고 패턴이다: bias-gen만 확인 → CMFB만 확인 → net 이름은 확인 안 함 → 다른 sub-block과
    합쳐야만 보이는 매칭을 놓침, 이 순서로 실제 4번 반복됐다).

    **입력**(전부 호출자가 채우는 것 — 이 함수는 회로 지식이 없다):
    - `devices`: `{name: (kind, source, drain, gate, block)}` — **정본 데이터 1벌**. 이 dict를
      만드는 스크립트가 여러 개면 안 된다(그게 net 이름 대소문자 드리프트의 실제 원인이었다).
    - `expected_counts`: `{block: 개수}` — **사이징 시작 전에** 소스(논문/스펙)에서 미리 선언한
      총 소자 수. differential 회로면 "출력이 2개인데 mirror branch가 있는가"를 이 단계에서
      먼저 답해야 한다(실제 사고: Class-AB 출력단이 우측 branch뿐이고 좌측 12개 소자가 통째로
      빠진 채 최종 리포트까지 갔었다 — 이 매니페스트가 있었다면 1번 체크에서 즉시 걸렸다).
    - `dispositions`: `{(tag, kind, net): (category, reason)}` — `tag`는 `"current_mirror"`/
      `"diff_pair"`(게이트 net 기준, `find_matching_candidates()`) 또는 `"hub_merge"`
      (source/drain net 기준, `find_hub_merge_candidates()`) 중 하나. **두 tag를 절대 섞지
      말 것** — 같은 (kind,net) 쌍이 우연히 두 함수 모두에서 나올 수 있는데(예: 한 net이
      어떤 소자의 drain이면서 동시에 다른 소자들의 gate), 하나의 key로 합치면 뒤에 발견된
      그룹이 조용히 "이미 처리됨"으로 덮여 사라진다(실제로 이 함수의 첫 버전이 이 버그를 냈다
      — 반드시 tag로 구분해서 저장할 것). `category`는 `real_match` 또는
      `false_positive_{coincidental|diode_chain|consumer_reads_bias|feedback_loop}` 중 하나를
      권장하지만 이 함수는 문자열 값 자체를 검사하지 않는다 — **키가 존재하는지만** 검사한다.
    - `box_shape_checks`: `{block_label: {row_id: [Transistor,...]}}` — sub-block별 실제 물리
      행 구성(2026-08-13 세션31: `check_box_shape()`가 실제 물리 치수를 계산하도록 바뀌면서
      `{row_id: n_fingers_total}`에서 이 형태로 재정의됨 — `l`/`finger_w`가 있는 `Transistor`
      리스트를 넘겨야 실제 폭/높이가 계산된다, 없으면 `approx=True`로 근사). common-centroid로
      물리 행이 2개로 쪼개진 그룹(§2.7)은 그 두 행을 각각의 `row_id`로 넣을 것 — 이 함수가
      그 분할을 자동으로 재계산하지 않는다(단일 Transistor 리스트로는 "같은 소자가 2개 물리
      행에 나눠 들어간다"는 구조를 표현할 수 없기 때문 — 이건 알려진 한계이지 숨겨진 가정이
      아니다).
    - `accept_fail_blocks`: box-shape FAIL을 근거와 함께 수용하기로 한 block 이름 집합(예:
      CMFB — §8.5 분할비용 계산 후 수용). 없으면 모든 block이 PASS여야 한다.

    **반환**: `AuditResult(checks=[...], ok=bool)` — `ok=False`면 리포트를 완료로 선언하지 말 것.
    """
    result = AuditResult()

    # 1) 소자 수 vs 선언된 매니페스트
    by_block = defaultdict(list)
    for name, (kind, s, d, g, block) in devices.items():
        by_block[block].append(name)
    count_detail = []
    count_ok = len(devices) == sum(expected_counts.values())
    for block, expected in expected_counts.items():
        actual = len(by_block.get(block, []))
        if actual != expected:
            count_ok = False
            count_detail.append(f"{block}: expected {expected}, found {actual}")
    result.add("1. device count vs manifest", count_ok,
               "; ".join(count_detail) if count_detail else
               f"total {len(devices)} == expected {sum(expected_counts.values())}")

    # 2) net 이름 대소문자 자기모순 스캔
    all_nets = (net for name, (kind, s, d, g, block) in devices.items() for net in (s, d, g))
    bad = _scan_case_collisions(all_nets)
    result.add("2. net-name case consistency", len(bad) == 0,
               f"case collisions: {bad}" if bad else "all net names already single-case")

    # 3) 전체 목록 기준 매칭/hub-merge 후보 전수 판정 대조
    trs = [Transistor(name, kind, source=s, drain=d, gate=g, n_fingers=1)
           for name, (kind, s, d, g, block) in devices.items()]
    hub = find_hub_merge_candidates(trs)
    mc = find_matching_candidates(trs)

    found_groups = []
    for (kind, net), group in hub.items():
        if len(group) >= 2:
            found_groups.append((("hub_merge", kind, net), [t.name for t in group]))
    for (kind, net), group in mc["current_mirror"].items():
        found_groups.append((("current_mirror", kind, net), [t.name for t in group]))
    for (kind, net), group in mc["diff_pair"].items():
        found_groups.append((("diff_pair", kind, net), [t.name for t in group]))

    undisposed = [(key, names) for key, names in found_groups if key not in dispositions]
    result.add("3. every matching/hub-merge candidate has a recorded disposition",
                len(undisposed) == 0,
                f"UNDISPOSED: {undisposed}" if undisposed else
                f"{len(found_groups)} candidate groups, all disposed")

    # 4) sub-block별 box-shape
    accept_fail_blocks = accept_fail_blocks or set()
    for block, block_rows in (box_shape_checks or {}).items():
        v = check_box_shape(block_rows, row_width_tol=row_width_tol)
        accepted = block in accept_fail_blocks and not v.ok
        result.add(f"4. box-shape [{block}]", v.ok or accepted,
                   v.message + ("  (FAIL accepted — see report reasoning)" if accepted else ""))

    return result


# ---------------------------------------------------------------------------
# 6.62) check_stick_diagram_coverage() — "sizing은 됐는데 layout이 통째로 빠짐" 최후의 방어선
#      (2026-07-28 신설, 힌트 없는 fresh agent 재현 테스트에서 실제로 재발한 사고 대응).
#      21개 소자 전부 gm/ID sizing은 끝났는데, CMFB/bias-gen/Class-AB 9개 소자는
#      stick diagram(물리 행)이 아예 없이 "완료"로 리포트가 게시됐다 — 심지어
#      `run_full_circuit_audit`를 스크립트 상단에 **import는 했지만 실제로 호출하지
#      않아서** 이 gap을 그 게이트조차 잡지 못했다(이 자체가 별도 경고 대상 —
#      아래 docstring 참고). `run_full_circuit_audit()`은 caller가 넘긴 `devices` dict
#      **안에서만** 정합성을 본다 — 애초에 그 dict에서 통째로 빠진 소자는 검사 대상에도
#      안 들어가 놓칠 수 있다. 이 함수는 그것과 다른, 더 원초적인 질문("사이징한 소자
#      전부가 어떤 물리 행에든 실려 있는가?")을 답한다.
# ---------------------------------------------------------------------------

@dataclass
class CoverageVerdict:
    ok: bool
    missing: set


def check_stick_diagram_coverage(sized_device_names, stick_diagram_devices: dict) -> CoverageVerdict:
    """리포트를 완료로 선언하기 **직전** 반드시 호출한다 — sizing이 끝난 소자 이름 전부가
    실제로 어떤 stick-diagram 물리 행에든 배치돼 있는지, 단순 집합 차집합으로 확인한다.

    ⚠️ 왜 필요한가: `run_full_circuit_audit()`(§6.6)는 caller가 넘긴 `devices` dict **안의**
    정합성(matching/hub-merge/box-shape)만 본다 — 그 dict 자체에서 소자가 통째로 빠지면
    (예: CMFB/bias-gen/Class-AB 서브블록 전체를 stick diagram 단계에서 깜빡하고) 애초에
    검사 대상이 아니므로 못 잡는다. 이 함수는 사이징 단계의 정본(예: `sizing_results.json`
    또는 그에 준하는 소자 이름 목록)과 stick diagram 단계의 정본을 **서로 다른 두 산출물**로
    보고 직접 대조한다 — 같은 스크립트 안에서 한쪽만 업데이트하고 다른 쪽을 깜빡해도 잡힌다.

    **입력**:
    - `sized_device_names`: 사이징이 끝난 모든 소자 이름의 집합/리스트(§3 사이징 표 전체).
    - `stick_diagram_devices`: `{row_name: [device_name, ...]}` — 실제 stick diagram 각
      물리 행에 실제로 배치된 소자 이름들(`build_stick_diagram()`에 넘긴 `Transistor`
      리스트의 `.name`들, 또는 `transistor_sequence`에서 뽑은 고유 이름 집합).

    **반환**: `CoverageVerdict(ok, missing)` — `missing`이 비어있지 않으면 그 소자들은
    사이징만 되고 물리 행이 없다는 뜻 — **리포트를 완료로 선언하지 않는다.**

    ⚠️⚠️ **"게이트 함수를 import만 하고 실제로 호출·assert하지 않은 채 완료 선언"도 그
    자체로 이 사고의 일부였다** — `run_full_circuit_audit`/`audit_row_split`/
    `check_stick_diagram_coverage`(이 함수) 같은 게이트를 코드 상단에 import해뒀다는
    사실은 "확인했다"는 증거가 되지 않는다. 리포트를 완료로 선언하기 전, 실제 소스에
    `run_full_circuit_audit(`/`check_stick_diagram_coverage(` **호출문**이 있고 그 반환값의
    `.ok`를 실제로 확인(assert 등)했는지 grep으로 직접 재확인할 것."""
    covered = set()
    for names in stick_diagram_devices.values():
        covered.update(names)
    missing = set(sized_device_names) - covered
    return CoverageVerdict(ok=not missing, missing=missing)


# ---------------------------------------------------------------------------
# 6.65) audit_row_split() — row 분할 하나를 제안할 때마다 반드시 통과해야 하는 고정-순서
#       게이트 (2026-07-27 신설, 실제 사고 대응). box-shape를 맞추려고 한 functional
#       group을 2개 이상의 물리 행으로 재구성할 때, "Euler 조건만 통과하면 끝"이라고
#       착각하기 쉽다 — 실제로 이 세션에서 정확히 그 실수가 발생했다: folded_cascode_
#       example()의 top/bot을 2행으로 나누면서 M3/M4(전류거울, source=vdd 공유)를 "M3는
#       row0 통째로, M4는 row1 통째로"로 배치했다. build_stick_diagram() 상태는 둘 다
#       "ok"(Euler 유효)였고 check_box_shape()도 PASS였다 — 그런데 두 매칭 소자가 완전히
#       분리 배치되어 interdigitation/common-centroid가 전혀 없는 배치였다(사용자가
#       "matching pattern은 왜 적용이 안 됐지?"라고 직접 지적해서야 발견). Euler-유효성과
#       box-shape는 "물리적으로 지을 수 있고 모양이 box인가"만 보장하지, "매칭 소자쌍이
#       실제로 잘 섞여 있는가"는 전혀 보지 않는다 — 별개의 체크가 반드시 필요하고, 사람이
#       그 순서를 기억해서 매번 재현하는 대신 이 함수 하나로 고정시킨다.
# ---------------------------------------------------------------------------

def select_layout_tool(matching_sensitivity: str, shares_node: bool,
                        area_budget: str | None = None) -> str:
    """배치 7-4b(2026-07-30/31), **2026-08-05(세션10) L1 하드컷** — `audit_row_split()`의
    kind→게이트 매핑(§2.6/§2.7 실측 기준)을 구성(construction) 단계에서도 쓸 수 있도록 뽑은
    함수. 세션10에서 `kind`(`current_mirror`/`current_matched`/`diff_pair`/`branch_symmetric`)
    문자열 하나 대신 L1이 분해한 두 독립 축을 직접 받도록 시그니처를 바꿨다(하위호환 shim
    없음, kind 문자열은 더 이상 받지 않는다):
    - `matching_sensitivity`(축C, 선언값): `"offset"`이면 offset/CMRR 민감도 때문에
      `common_centroid_layout`이 무조건 필수(구 `diff_pair`).
    - `shares_node`(축B, `shares_diffusion_node()`로 계산): `matching_sensitivity=="ratio"`인
      쌍 중 source/drain을 공유하면(구 `current_mirror`/`current_matched`) 미러비 오차
      전파만 관심사라 `interdigitate_layout`으로 충분(§2.7) — 공유 안 하면(구
      `branch_symmetric`) interdigitation 자체가 그래프상 불가능해 `common_centroid_layout`이
      필수.

    `area_budget`(선택): `"generous"`를 주면 `shares_node=True`인 ratio쌍도
    `common_centroid_layout`으로 격상한다("최소면적이 아니면 더 나은 매칭을 써도 된다"는
    원칙, §7.9 질문 6) — `estimate_area_budget()`(배치 7-4b 확장)의 결과를 근거로 호출자가
    지정할 것을 권장.

    등록 안 된 `matching_sensitivity`는 즉시 `ValueError`(다른 레지스트리들과 동일 계약)."""
    if matching_sensitivity not in ("ratio", "offset"):
        raise ValueError(f"알 수 없는 matching_sensitivity: {matching_sensitivity!r} -- "
                          f"'ratio'/'offset' 중 하나여야 한다")
    if matching_sensitivity == "offset":
        return "common_centroid_layout"
    if shares_node:
        return "common_centroid_layout" if area_budget == "generous" else "interdigitate_layout"
    return "common_centroid_layout"


def audit_row_split(rows: dict, matching_pairs: list | None = None,
                     pair_sensitivity: dict | None = None,
                     row_width_tol: float = 1.5, area_budget: str | None = None) -> AuditResult:
    """box-shape를 위해 한 functional group을 여러 물리 행으로 재구성했을 때 **반드시 이
    함수 하나만** 호출한다 — 그때그때 손으로 `build_stick_diagram()`/`check_box_shape()`/
    interdigitation을 따로따로 확인하다가 순서를 빼먹는 실수(실제 사고, 위 §6.65 docstring)를
    막기 위해, 고정된 순서로 전부 실행하고 전부 보고한다. 하나라도 실패하면 `ok=False`이고
    `checks`에 어떤 항목이 왜 실패했는지 전부 남는다 — 조용히 건너뛰는 항목이 없다.

    ⚠️ 2026-07-27 세 번째 수정(사용자 지적: "interdigitation과 common centroid를 판별하는 건
    matching 특성을 분석해서 해야 하는데 기존 기준은 왜 안 쓰나 — mirror는 interdigitation이
    적합/효율적이고, differential pair는 offset/CMRR 민감도 때문에 common-centroid가 필요하다")
    — 첫 버전은 모든 `matching_pairs`에 3b/3c를 **똑같이** 요구했다. 하지만
    `stick-diagram-euler-layout.md` §2.7(PDF Fig.4 실측: interdigitation ≈0.04% → common-centroid
    ≈0.02%, 약 절반 개선)이 이미 확립한 기준은 pair 종류에 따라 다르다: **전류거울(같은 gate
    공유)은 1행 interdigitation으로 충분**(미러비 오차 전파가 주 관심사, 면적/배선 효율이
    우선), **차동쌍(같은 source 공유 + 다른 gate)은 offset/CMRR이 W·L 불일치에 직접 비례해
    더 민감하므로 common-centroid(2행, y방향까지 상쇄)가 필요**하다.

    **2026-08-05(세션10) L1 하드컷**: 이전엔 이 판정을 `kind` 문자열 하나(내부 `_kind_of()`가
    `pair_kinds` override가 없으면 connectivity에서 즉석 재추론)로 했는데, L1이 `kind`를
    독립된 두 축(축B `shares_diffusion_node()`/축C `matching_sensitivity`)으로 분해하면서
    이 함수도 그 두 축을 직접 받도록 바꿨다(하위호환 shim 없음, `pair_kinds`/`kind` 문자열은
    더 이상 받지 않는다) — connectivity 재추론도 폐지됐다(예전엔 `pair_kinds` 없이 호출하면
    `rows`의 gate/source만 보고 즉석 분류했지만, `matching_sensitivity`는 축C라 connectivity로
    자동 도출이 안 되므로 이제 **항상 명시적으로 선언**해야 한다).

    **입력**:
    - `rows`: `{row_name: [Transistor, ...]}` — 각 `Transistor.stack_id`는 그 `row_name`과
      일치해야 한다(그래야 `build_stick_diagram()`이 행별로 정확히 묶는다).
    - `matching_pairs`: `[(name_a, name_b), ...]` — 실제 matching이 필요하다고 판단된 소자쌍.
    - `pair_sensitivity`: `{(name_a, name_b) 또는 (name_b, name_a) 또는 frozenset({a,b}):
      "ratio"|"offset"}` — **필수**(`matching_pairs`에 있는 모든 쌍이 여기 있어야 한다,
      없으면 `ValueError`). 축B(`shares_diffusion_node(ra, rb)`)는 `rows`의 실제 connectivity로
      항상 자동 계산되므로 여기 넣지 않는다 — `ra`/`rb` 조회에 실패하면(행 분할로 원본
      `Transistor`가 안 남아있는 경우) `_kind_of()`의 옛 `"unknown"` 폴백과 동일하게 보수적으로
      3b/3c 둘 다 필수로 취급한다.

    **고정 실행 순서** (매번 전부, 순서 무관하게 건너뛸 수 없다):
    1. 행마다 `build_stick_diagram()` 호출 → `status=="ok"`(Euler 유효) 확인.
    2. 전체 `row_widths`로 `check_box_shape()` 호출.
    3. 선언된 `matching_pairs`마다:
       - **3a. row-presence**: 어느 행에 둘 다 있고 어느 행에 한쪽만 있는지 **정보로만** 보고한다
         — solo(한쪽만 있는 행이 존재)가 자동으로 실패를 뜻하지 않는다(2026-07-27 다섯 번째
         수정: 처음엔 solo를 하드 실패로 봤는데, `branch_symmetric`(공유 노드 없는 캐스코드
         대칭쌍, 예: folded_cascode의 M7/M8)도 두 소자를 **양쪽 행에 swap-대칭으로 나눠
         분배**하면 실측으로 dx=0.00/dy=0.20까지 나온다는 게 확인됐다 — "각자 한쪽 행에
         통째로"(dy=1.0)보다 훨씬 낫다. solo는 가능한 배치 중 하나일 뿐 강제되는 구조가
         아니므로, 실제 품질 판정은 아래 3c가 한다.
       - **3b. interdigitation**(행별 지역 인접성)과 **3c. common-centroid**(전체 무게중심
         일치, 허용오차 0.5) 둘 다 **항상 계산하고 리포트한다** — 하지만 pair의 축B/축C에
         따라 **어느 쪽이 전체 `ok`를 좌우하는 필수 게이트인지가 다르다**:
         - `matching_sensitivity=="ratio"` and `shares_node`(구 `current_mirror`/
           `current_matched`): **3b가 필수**(3c는 참고 정보로만 보고, FAIL이어도 전체 ok에
           영향 없음) — §2.7 "단순 전류거울은 1행 interdigitation으로 충분". `area_budget=
           "generous"`면 3c도 필수로 격상된다(`select_layout_tool()`과 동일 정책).
         - `matching_sensitivity=="offset"`(구 `diff_pair`) 또는 `ratio`+`not shares_node`
           (구 `branch_symmetric`): **3c가 필수**(3b는 참고 정보) — §2.7 "차동쌍은 offset/CMRR
           민감도 때문에 common-centroid 필요", §2.6 "캐스코드 대칭쌍도 CMRR/PSRR에 직접 영향"이
           같은 수준의 민감도임을 명시. `branch_symmetric` 쪽의 3b는 공유 노드가 없어 그래프상
           사실상 항상 실패한다(전수 탐색 확인) — 그래도 3c는 위 실측처럼 swap 분배로 달성
           가능하므로 별개로 요구한다.
         - `ra`/`rb` 조회 실패(구 `"unknown"` 폴백): 보수적으로 **3b와 3c 둘 다 필수**."""
    result = AuditResult()
    sequences: dict = {}
    reps: dict = {}  # name -> 대표 Transistor(gate/source 조회용, 행 무관하게 아무거나 하나)

    for row_name, devices in rows.items():
        for t in devices:
            reps.setdefault(t.name, t)

        # 세션11 -- 이 행에 두 이름 다 속하는 matching_pairs만 걸러 build_stick_diagram()에
        # 넘긴다(run_topology_pipeline()의 cell_pairs 필터링, 3830행 부근과 동일 패턴) --
        # mirror_symmetric_trail()이 이 행 안에서만 대칭을 구성하도록.
        device_names = {t.name for t in devices}
        row_pairs = [(a, b) for (a, b) in (matching_pairs or [])
                     if a in device_names and b in device_names]
        out = build_stick_diagram(devices, matching_pairs=row_pairs)
        r = out.get(row_name)
        if r is None:
            result.add(f"1. euler[{row_name}]", False,
                       f"stack_id 불일치 -- build_stick_diagram()이 반환한 키 {list(out.keys())}"
                       f"에 '{row_name}'이 없다 (Transistor.stack_id를 다시 확인할 것)")
            continue
        if r.status != "ok":
            result.add(f"1. euler[{row_name}]", False, f"status={r.status}, odd_nodes={r.odd_nodes}")
        else:
            result.add(f"1. euler[{row_name}]", True, f"odd_nodes={r.odd_nodes}")
            sequences[row_name] = r.transistor_sequence

    bs = check_box_shape(rows, row_width_tol=row_width_tol)
    result.add("2. box-shape", bs.ok, bs.message)
    result.box_shape = bs  # 호출자가 재계산 없이 참조할 수 있게 원본 객체를 보관(위 필드 docstring)

    pair_sensitivity = pair_sensitivity or {}

    def _sensitivity_of(a, b):
        for key in ((a, b), (b, a), frozenset({a, b})):
            if key in pair_sensitivity:
                return pair_sensitivity[key]
        raise ValueError(f"pair_sensitivity에 ({a},{b}) 쌍의 matching_sensitivity가 없다 -- "
                          f"matching_pairs의 모든 쌍은 축C를 명시적으로 선언해야 한다")

    row_order = list(rows.keys())
    for a, b in (matching_pairs or []):
        sens = _sensitivity_of(a, b)
        ra, rb = reps.get(a), reps.get(b)
        if ra is None or rb is None:
            shares = None  # 구 "unknown" 폴백과 동일 -- 아래서 3b/3c 둘 다 필수로 강제
        else:
            shares = shares_diffusion_node(ra, rb)
        kind = f"sensitivity={sens},shares_node={shares}"  # 3a 리포트용 표시 문자열
        count_a = {rn: sum(t.n_fingers for t in devs if t.name == a) for rn, devs in rows.items()}
        count_b = {rn: sum(t.n_fingers for t in devs if t.name == b) for rn, devs in rows.items()}
        touched = [rn for rn in rows if count_a[rn] > 0 or count_b[rn] > 0]

        # 3a는 이제 순수 정보성 보고일 뿐 별도 하드게이트가 아니다(2026-07-27 네 번째 수정
        # — 아래 참고). solo(한쪽만 있는 행이 존재)가 자동으로 실패를 뜻하지 않는다: 사용자가
        # 직접 확인시켜 준 반례가 있다 — branch_symmetric(공유 노드 없는 캐스코드 대칭쌍,
        # 예: folded_cascode의 M7/M8)도 "M7 3f/M8 2f를 한 행에, M7 2f/M8 3f를 swap해서
        # 다른 행에" 식으로 **일부러 두 행 모두에 걸치게 나누면** 실제로 dx=0.00, dy=0.20까지
        # 나온다(실측) — "각자 한쪽 행에 통째로"(dy=1.0)보다 훨씬 낫다. 즉 solo는 **가능한
        # 선택지 중 하나일 뿐 강제되는 구조가 아니고**, 그 자체를 하드 실패로 보면 이 더 나은
        # 대안을 놓친다 — 3c(common-centroid)가 실제로 그 dx/dy를 계산해 정직하게 점수를
        # 매기게 두고, solo 여부는 정보로만 남긴다.
        solo = [rn for rn in touched if (count_a[rn] > 0) != (count_b[rn] > 0)]
        result.checks.append(AuditCheck(
            f"3a. row-presence[{a}/{b}] (kind={kind})", True,
            f"두 소자 모두 있는 행: {[rn for rn in touched if rn not in solo]}; "
            f"{a}/{b} 중 한쪽만 있는 행: {solo or '없음'} (정보성 — solo 자체는 실패가 아님, 3c가 실제 품질을 판정)"))

        # 3b. interdigitation -- 행별 국소 인접성
        details = []
        adjacency_ok = True
        for rn in touched:
            seq = sequences.get(rn)
            if seq is None:
                details.append(f"{rn}: sequence 없음(Euler 실패)")
                adjacency_ok = False
                continue
            pos_a = [i for i, x in enumerate(seq) if x == a]
            pos_b = [i for i, x in enumerate(seq) if x == b]
            adjacent = any(abs(i - j) == 1 for i in pos_a for j in pos_b)
            details.append(f"{rn}: {'인접' if adjacent else 'NOT 인접'}")
            if not adjacent:
                adjacency_ok = False

        # 3c. common-centroid -- 행-내부 x(index) + 행-간 y(행 순서) 전체 무게중심 비교
        def _centroid(name):
            total_n = 0
            sx = 0.0
            sy = 0.0
            for y, rn in enumerate(row_order):
                seq = sequences.get(rn)
                if seq is None:
                    continue
                positions = [i for i, x in enumerate(seq) if x == name]
                if not positions:
                    continue
                total_n += len(positions)
                sx += sum(positions)
                sy += y * len(positions)
            return (sx / total_n, sy / total_n) if total_n else None

        cen_a, cen_b = _centroid(a), _centroid(b)
        if cen_a is None or cen_b is None:
            centroid_ok = False
            centroid_detail = "sequence 없음(Euler 실패)이라 무게중심 계산 불가"
        else:
            dx, dy = abs(cen_a[0] - cen_b[0]), abs(cen_a[1] - cen_b[1])
            centroid_ok = dx <= 0.5 and dy <= 0.5
            centroid_detail = (f"{a} centroid=({cen_a[0]:.2f},{cen_a[1]:.2f}), "
                               f"{b} centroid=({cen_b[0]:.2f},{cen_b[1]:.2f}), |dx|={dx:.2f} |dy|={dy:.2f}"
                               f" (허용오차 0.5)")

        # 축B/축C에 따라 어느 체크가 전체 ok를 좌우하는 필수 게이트인지 결정 (§2.7 기준).
        # branch_symmetric류(ratio + not shares_node)도 offset류(diff_pair)와 같이
        # common-centroid를 필수로 본다 -- interdigitation(행 내부 인접)은 그래프 구조상
        # 사실상 항상 불가능하지만(전수 탐색으로 확인), common-centroid(전체 무게중심 일치)는
        # 두 소자를 swap-대칭으로 양쪽 행에 걸쳐 분배하면 실제로 달성 가능하다(실측: solo
        # 배치 dy=1.0 -> 분배 배치 dx=0.00/dy=0.20). 참고용(비필수) 체크는 result.checks에는
        # 남기되 result.add()를 거치지 않아 overall ok를 흔들지 않는다 -- FAIL이어도 눈에는
        # 보이되 게이트를 막지는 않는다.
        # 2026-08-05(세션10) L1 하드컷 -- select_layout_tool(matching_sensitivity, shares_node,
        # area_budget)의 반환값에서 centroid_required를 유도한다(로직 중복 제거, 배치
        # 7-4b부터 유지된 원칙). interdig_required는 ra/rb 조회 실패(구 "unknown" 폴백)에
        # 대해서만 예외를 유지한다 -- select_layout_tool()은 구성 단계에서 도구 하나를 골라야
        # 해서 그 경우를 표현할 방법이 없지만, 감사 단계는 "확신 못 하면 둘 다 확인"이라는
        # 기존 보수적 정책을 그대로 유지한다(behavior 변경 없음).
        if ra is None or rb is None:
            interdig_required, centroid_required = True, True
        else:
            centroid_required = select_layout_tool(sens, shares, area_budget) == "common_centroid_layout"
            interdig_required = (sens == "ratio") and shares
        note_b = "" if interdig_required else " [참고용 -- 이 kind는 필수 아님]"
        note_c = "" if centroid_required else " [참고용 -- 이 kind는 필수 아님]"
        if interdig_required:
            result.add(f"3b. interdigitation[{a}/{b}]{note_b}", adjacency_ok, "; ".join(details))
        else:
            result.checks.append(AuditCheck(f"3b. interdigitation[{a}/{b}]{note_b}", adjacency_ok, "; ".join(details)))
        if centroid_required:
            result.add(f"3c. common-centroid[{a}/{b}]{note_c}", centroid_ok, centroid_detail)
        else:
            result.checks.append(AuditCheck(f"3c. common-centroid[{a}/{b}]{note_c}", centroid_ok, centroid_detail))

    return result


# ---------------------------------------------------------------------------
# 6.66) repair_matching_safety() — 검증→수리 closed-loop (배치 7-4, 2026-07-31)
#       audit_row_split()이 FAIL한 matching pair를 select_layout_tool()(배치 7-4b)이 고른
#       도구로 자동 재배치하고 재검증하는 걸 반복한다. §7.9 질문3 결정대로
#       run_topology_pipeline()엔 자동 포함하지 않고 별도 함수로 호출자가 명시적으로 쓴다.
# ---------------------------------------------------------------------------

def _failing_required_pairs(result: AuditResult) -> list:
    """AuditResult에서 **필수 게이트(참고용 아님)로 실패한** 3b/3c 체크의 (a,b) pair 이름을
    뽑는다. 체크 name은 `"3b. interdigitation[a/b]"`/`"3c. common-centroid[a/b]"` 형태
    (참고용이면 뒤에 `" [참고용..."`가 붙는다) — name 문자열에서 직접 파싱한다(AuditCheck
    자체엔 구조화된 pair 필드가 없다)."""
    import re
    seen = []
    for check in result.checks:
        if check.ok or "[참고용" in check.name:
            continue
        if not (check.name.startswith("3b.") or check.name.startswith("3c.")):
            continue
        m = re.search(r"\[(.+?)/(.+?)\]", check.name)
        if m and (m.group(1), m.group(2)) not in seen:
            seen.append((m.group(1), m.group(2)))
    return seen


def _layout_result_to_rows(layout: dict, templates: dict, base_row_name: str,
                            existing_rows: dict | None = None) -> dict:
    """`interdigitate_layout()`/`common_centroid_layout()`의 반환값(`"rows"`: 각 원소가
    `transistor_sequence`를 가진 새 물리 행)을 실제 `{row_name: [Transistor,...]}`로
    변환한다 — 각 이름의 `transistor_sequence` 등장 횟수가 그 행에서의 `n_fingers`다.
    `templates`: `{name: Transistor}` — 원본 소자(kind/source/drain/gate 등 connectivity
    필드를 그대로 복사하고 `n_fingers`/`stack_id`만 새로 채운다).

    ⚠️ 2026-08-14(세션32, 사용자 절대원칙 "만들면 반드시 배선" 이행 중 실측 발견) --
    새 행 이름을 항상 `f"{base_row_name}_repair0"`(i는 이 호출 안에서만 0부터 -- 여러
    라운드에 걸쳐 전역적으로 유일하지 않음)로 지었다 -- `repair_matching_safety()`에서
    한 "hub" 소자(예: 여러 매칭쌍에 동시에 걸린 M18_bg류 current_mirror 기준 소자)가
    라운드마다 새 파트너와 반복해서 재배치될 때, 예전에 함께 있다가 떨어져나가
    다른 소자만 남은 행("X_repair0" = 남은 소자 하나)의 이름을, 나중에 완전히 무관한
    다른 쌍이 우연히 같은 `base_row_name`을 거쳐 같은 이름을 다시 생성해 `current_rows.
    update(new_rows)`가 **조용히 덮어써서 그 남은 소자를 통째로 지워버렸다**(실측:
    current_reuse_telescopic_ota, M17/M18_bg/M61 3개가 이렇게 사라짐 -- repro 스크립트로
    `pair=(M8,M61)` 처리 중 'M17' 소실을 직접 확인). `existing_rows`(호출자가 넘긴,
    이 시점의 `current_rows` -- 필터/삭제까지 끝난 뒤의 최신 상태)에 이미 있는 이름은
    건너뛰고 다음 `_repair{i}`를 시도해 충돌을 원천 차단한다."""
    result = {}
    reserved = set(existing_rows.keys()) if existing_rows is not None else set()
    for row in layout["rows"]:
        counts = Counter(row["transistor_sequence"])
        i = 0
        new_row_name = f"{base_row_name}_repair{i}"
        while new_row_name in reserved:
            i += 1
            new_row_name = f"{base_row_name}_repair{i}"
        reserved.add(new_row_name)
        result[new_row_name] = [_dc_replace(templates[name], n_fingers=n, stack_id=new_row_name)
                                 for name, n in counts.items()]
    return result


def _kcl_branch_map(devices: list) -> dict:
    """`devices`에 `kcl_series_union()`의 순수 자동발견 규칙(2단자 net, `matching_pairs`
    강제병합 없음)만 돌려 `{소자명: branch 전체 소자명 리스트}`로 펼쳐 반환한다 --
    `repair_matching_safety()`의 branch 복합 매칭(세션16)이 "이 소자가 다른 소자와 물리적으로
    같은 직렬 컬럼(예: 캐스코드 스택)을 이루는가"를 판단하는 데 쓴다. 이미 있는 `kcl_series_
    union()`(세션10 L2, `stack_groups_kcl`용)을 그대로 재사용할 뿐 새 그래프 로직은 없다."""
    groups = kcl_series_union(devices, [])
    branch_of: dict = {}
    for members in groups.values():
        for n in members:
            branch_of[n] = members
    return branch_of


def _two_device_branch_outer(x: "Transistor", y: "Transistor"):
    """2소자 직렬 branch(x,y)의 내부 연결 net과 바깥쪽 두 단자(x_outer, y_outer)를 구한다.
    정확히 하나의 공유 net이 있어야 하고(`kcl_series_union()`이 이미 보장하지만 방어적으로
    재확인), x/y 각각 남는 단자가 정확히 하나여야 한다(self-loop 등 이상 케이스 방어).
    실패하면 `None`."""
    x_terms = {x.source, x.drain}
    y_terms = {y.source, y.drain}
    shared = x_terms & y_terms
    if len(shared) != 1:
        return None
    internal_net = next(iter(shared))
    x_rest, y_rest = x_terms - {internal_net}, y_terms - {internal_net}
    if len(x_rest) != 1 or len(y_rest) != 1:
        return None
    return internal_net, next(iter(x_rest)), next(iter(y_rest))


def _branch_composite_pair(a: str, b: str, devices_by_name: dict, matching_pairs: list):
    """실패한 매칭쌍 (a,b)가 서로 다른 hub(source)를 써서 `interdigitate_layout()`/
    `common_centroid_layout()`을 직접 적용할 수 없을 때(세션15 A-3/세션16에서 확인된 한계 --
    예: branch_symmetric인 M2a/M2b), 각자 속한 `kcl_series_union()` 직렬 branch가 서로
    완전히 대응되는 거울 branch인지 확인한다 -- 대응되면(길이 2, hub쪽 소자끼리도 leaf쪽
    소자끼리도 둘 다 선언된 matching_pairs) 그 branch 전체를 감싸는 합성(composite)
    `Transistor` 한 쌍을 만들어 반환한다: 이러면 두 composite가 (진짜 공유 hub인)
    같은 source를 갖게 되어 기존 도구를 그대로 적용할 수 있다 -- "M1a+M2a를 하나의 소자처럼
    다룬다"는 아이디어(세션16 사용자 제안)를 이미 있는 `kcl_series_union()`으로 구현한 것,
    새 그래프 탐색 로직은 없다.

    **적용 범위(의도적으로 좁음, 다른 함수들과 동일 원칙)**: 정확히 2소자로 이루어진 선형
    branch만 지원한다(3소자 이상 체인, 분기형 구조는 `None` -- 호출자가 기존처럼 skip).
    branch 내부 두 소자의 `n_fingers`가 다르면(물리적으로 한 컬럼인데 폭이 다른 건 이상
    케이스) 마찬가지로 `None`.

    반환: 성공하면 `{"composite_a": Transistor, "composite_b": Transistor,
    "expand": {composite_a.name: [hub_dev_a, leaf_dev_a], composite_b.name: [...]}}` --
    어느 도구(interdigitate/common-centroid)를 쓸지는 호출자가 hub쌍/leaf쌍 각각의
    `matching_sensitivity`로 직접 판단한다(이 함수는 구조 정합성만 확인). 실패하면 `None`."""
    branch_map = _kcl_branch_map(list(devices_by_name.values()))
    branch_a, branch_b = branch_map.get(a, [a]), branch_map.get(b, [b])
    if len(branch_a) != 2 or len(branch_b) != 2:
        return None  # branch가 없거나(단독) 2소자 선형 체인이 아님 -- 이 함수 범위 밖

    outer_a = _two_device_branch_outer(devices_by_name[branch_a[0]], devices_by_name[branch_a[1]])
    outer_b = _two_device_branch_outer(devices_by_name[branch_b[0]], devices_by_name[branch_b[1]])
    if outer_a is None or outer_b is None:
        return None
    _, outer_a0, outer_a1 = outer_a
    _, outer_b0, outer_b1 = outer_b

    if outer_a0 == outer_b0:
        hub_net, hub_a, leaf_a, hub_b, leaf_b = outer_a0, branch_a[0], branch_a[1], branch_b[0], branch_b[1]
    elif outer_a0 == outer_b1:
        hub_net, hub_a, leaf_a, hub_b, leaf_b = outer_a0, branch_a[0], branch_a[1], branch_b[1], branch_b[0]
    elif outer_a1 == outer_b0:
        hub_net, hub_a, leaf_a, hub_b, leaf_b = outer_a1, branch_a[1], branch_a[0], branch_b[0], branch_b[1]
    elif outer_a1 == outer_b1:
        hub_net, hub_a, leaf_a, hub_b, leaf_b = outer_a1, branch_a[1], branch_a[0], branch_b[1], branch_b[0]
    else:
        return None  # 두 branch가 공유하는 바깥쪽 hub가 없음 -- 거울 branch 아님, skip

    declared = {frozenset(p) for p in matching_pairs}
    if frozenset({hub_a, hub_b}) not in declared or frozenset({leaf_a, leaf_b}) not in declared:
        return None  # hub쪽/leaf쪽 둘 다 선언된 matching_pair여야 "완전히 대응"으로 인정

    dev_hub_a, dev_leaf_a = devices_by_name[hub_a], devices_by_name[leaf_a]
    dev_hub_b, dev_leaf_b = devices_by_name[hub_b], devices_by_name[leaf_b]
    if dev_hub_a.n_fingers != dev_leaf_a.n_fingers or dev_hub_b.n_fingers != dev_leaf_b.n_fingers:
        return None  # 한 컬럼인데 finger 수가 다름 -- 이상 케이스, 방어적으로 skip
    # 2026-08-13(세션31, box-shape 실제 물리 치수 반영 중 발견) -- hub_a/leaf_a/hub_b/leaf_b
    # 4개 실제 소자는 interdigitate_layout()/common_centroid_layout() 뒤 _layout_result_
    # to_rows()를 거쳐 결국 **같은 물리 행(같은 diffusion strip)**에 함께 배치된다 -- 그러려면
    # finger_w가 전부 같은 unit cell이어야 한다(§2.5 INTERDIGITATION_PATTERNS의 전제와 동일,
    # compute_row_geometry()가 새로 추가한 행 내 finger_w 균일성 게이트와 같은 이유). 이
    # 검증이 없어서 서로 다른 finger_w(예: 별도 stack에서 각자 assign_finger_geometry()가
    # 고른 값)를 가진 소자들을 한 물리 행으로 합치는 결과가 실제로 나왔다(실측: current_
    # reuse_telescopic_ota L5c 테스트의 M12/M19, finger_w 1.158um vs 1.074um). n_fingers
    # 불일치와 동일하게 물리적으로 불가능한 조합이므로 같은 방식(None, 호출자가 기존
    # 개별-소자 경로로 폴백하거나 skip)으로 방어한다.
    _fw_known = {v for v in (dev_hub_a.finger_w, dev_leaf_a.finger_w,
                              dev_hub_b.finger_w, dev_leaf_b.finger_w) if v is not None}
    # finger_w가 아직 없는 소자(순수 구조 테스트, 사이징 이전 load_topology() 산출물 등)는
    # 비교 대상에서 뺀다 -- None을 "다르다"로 오판하지 않는다(approx 취급과 동일 원칙).
    if len(_fw_known) > 1 and not all(
            math.isclose(x, y, rel_tol=1e-9) for x in _fw_known for y in _fw_known):
        return None  # 4개 소자가 같은 diffusion strip에 들어가는데 finger_w가 다름 -- 물리적으로 불가능

    leaf_net_a = outer_a1 if hub_net == outer_a0 else outer_a0
    leaf_net_b = outer_b1 if hub_net == outer_b0 else outer_b0
    if leaf_net_a == leaf_net_b:
        # 세션22 실측 발견 -- hub쪽/leaf쪽 둘 다 선언된 matching_pair라도, 두 branch의
        # leaf net이 같은 물리 노드면(예: M36a-M37a/M36b-M37b -- M37a/M37b가 진짜
        # 차동쌍이라 서로 다른 legs가 아니라 공유 tail net(Ncmfb_tail)로 만나는 경우)
        # "거울 branch"가 아니다 -- 이대로 composite를 만들면 두 composite의 drain이
        # 똑같아져 나중에 common_centroid_layout()이 "leaf가 서로 달라야 한다"로 크래시한다
        # (구조 정합성 확인이 불완전했던 gap, 여기서 조용히 None으로 거부해 호출자가
        # 기존 개별-소자 경로로 폴백하게 한다).
        return None
    composite_a = Transistor(name=f"__branch__{hub_a}_{leaf_a}", kind=dev_hub_a.kind,
                              source=hub_net, drain=leaf_net_a, n_fingers=dev_hub_a.n_fingers)
    composite_b = Transistor(name=f"__branch__{hub_b}_{leaf_b}", kind=dev_hub_b.kind,
                              source=hub_net, drain=leaf_net_b, n_fingers=dev_hub_b.n_fingers)
    return {
        "composite_a": composite_a, "composite_b": composite_b,
        "expand": {composite_a.name: [hub_a, leaf_a], composite_b.name: [hub_b, leaf_b]},
    }


def _composite_collapse_for_crossover(transistors: list, matching_pairs: list,
                                       pair_sensitivity: dict | None = None) -> tuple:
    """**세션17 신설** -- `find_min_crossover_layout()`을 부르기 전에 이 그룹의 branch
    (예: M1a-M2a 캐스코드 컬럼)를 `_branch_composite_pair()`로 미리 합성 소자 하나로
    뭉친다. `repair_matching_safety()`가 `interdigitate_layout()`/`common_centroid_
    layout()`을 부르기 전에 이미 이렇게 하고 있는 것과 정확히 같은 이유 -- branch는
    물리적으로 한 덩어리로 움직여야 하는데, `find_min_crossover_layout()`은 raw 개별
    소자만 보면 그 사실을 전혀 모른다(사용자 확인, 세션17). 이걸 안 하면 crossover
    짝짓기가 같은 branch의 두 소자를 서로 다른 segment로 갈라놓을 수 있다 -- M6 그룹이
    지금까지 우연히 안 갈라진 것뿐, 구조적 보장이 아니었다.

    선언된 `matching_pairs`를 순회하며 각 쌍에 `_branch_composite_pair()`를 시도한다.
    성공하면(hub쪽/leaf쪽 모두 선언된 branch 쌍) 그 4개 실제 소자(hub_a/leaf_a/hub_b/
    leaf_b)를 "소비됨"으로 표시하고, 합성 쌍 하나(`composite_a.name`, `composite_b.name`)
    를 새 matching_pairs에 넣는다 -- **원래 두 선언 쌍(hub쪽 M1a/M1b, leaf쪽 M2a/M2b)이
    같은 branch를 가리키면 새 목록엔 이 합성 쌍 하나만 남는다**(중복 방지 -- 소비된
    소자를 참조하는 이후 선언 쌍은 건너뛴다). 실패하면(branch 없음/부분만 선언/구조
    안 맞음) 그 쌍은 원래 이름 그대로 새 목록에 남는다(하위호환 폴백, 기존 개별-소자
    경로와 동일).

    `pair_sensitivity`가 주어지면 합성 쌍의 민감도는 **hub쪽/leaf쪽 중 하나라도
    "offset"이면 "offset"**으로 정한다(더 엄격한 쪽 우선 -- `repair_matching_safety()`가
    `select_layout_tool()`로 "둘 중 하나라도 common_centroid가 필요하면 common_centroid
    채택"하는 것과 동일한 보수적 원칙, 사용자 확인). 원래 두 선언 쌍의 민감도가 다르면
    이 규칙으로 합쳐지고, `pair_sensitivity=None`이면 새 pair_sensitivity도 `None`.

    반환: `(new_transistors, new_matching_pairs, new_pair_sensitivity, expand_map)` --
    `expand_map`은 `{composite_name: [real_name1, real_name2]}`(합성 안 된 이름은 키에
    없음, 호출자가 `expand_map.get(name, [name])`로 처리)."""
    devices_by_name = {t.name: t for t in transistors}
    consumed: set = set()
    composite_pairs: dict = {}   # frozenset(실제 4소자 or 합성 안 된 2소자) -> (new_a, new_b)
    expand_map: dict = {}
    new_devices_by_name = dict(devices_by_name)

    def _sensitivity_of(a, b):
        if pair_sensitivity is None:
            return None
        for key in ((a, b), (b, a), frozenset({a, b})):
            if key in pair_sensitivity:
                return pair_sensitivity[key]
        return None

    new_matching_pairs = []
    for a, b in matching_pairs:
        if a in consumed and b in consumed:
            continue  # 이미 다른 선언 쌍(같은 branch의 반대쪽)에서 합성됨
        composite = _branch_composite_pair(a, b, devices_by_name, matching_pairs)
        if composite is None:
            new_matching_pairs.append((a, b))
            continue
        ca, cb = composite["composite_a"], composite["composite_b"]
        real_names = [n for names in composite["expand"].values() for n in names]
        consumed.update(real_names)
        for name, members in composite["expand"].items():
            new_devices_by_name.pop(members[0], None)
            new_devices_by_name.pop(members[1], None)
            new_devices_by_name[name] = ca if name == ca.name else cb
            expand_map[name] = members
        hub_a, leaf_a = composite["expand"][ca.name]
        hub_b, leaf_b = composite["expand"][cb.name]
        new_matching_pairs.append((ca.name, cb.name))
        if pair_sensitivity is not None:
            sens_hub = _sensitivity_of(hub_a, hub_b)
            sens_leaf = _sensitivity_of(leaf_a, leaf_b)
            composite_pairs[(ca.name, cb.name)] = \
                "offset" if "offset" in (sens_hub, sens_leaf) else "ratio"

    new_transistors = list(new_devices_by_name.values())
    new_pair_sensitivity = None
    if pair_sensitivity is not None:
        new_pair_sensitivity = dict(pair_sensitivity)
        for key in composite_pairs:
            new_pair_sensitivity[key] = composite_pairs[key]
    return new_transistors, new_matching_pairs, new_pair_sensitivity, expand_map


def find_min_crossover_layout_with_branch_composite(
        transistors: list, matching_pairs: list, pair_sensitivity: dict | None = None) -> dict:
    """**세션17 신설** -- `find_min_crossover_layout()`을 branch-인지형으로 감싸는
    wrapper(`find_min_crossover_layout()` 자체는 안 건드림, 완전히 별도 함수). 호출
    전에 `_composite_collapse_for_crossover()`로 branch를 합성 소자로 뭉쳐서 crossover
    짝짓기가 branch를 갈라놓을 수 없게 만들고(구조적 보장 -- 합성 소자는 그래프에서
    원자 단위 edge 하나라 애초에 쪼갤 방법이 없다), 결과 segment의
    `transistor_sequence`를 실제 소자 이름으로 다시 펼쳐서 반환한다(`_layout_result_
    to_rows()`가 쓰는 것과 동일한 펼치기 패턴).

    ⚠️ `node_sequence`는 합성 소자의 경계 net(hub_net/leaf_net) 그대로 남는다 --
    branch 내부 net(예: M1a.drain=M2a.source인 N1a2a)은 합성 과정에서 감춰지므로
    이 필드에서 복원하지 않는다(이 함수의 소비자는 지금까지 `transistor_sequence`만
    필요로 했다 -- `_count_matching_pair_splits()`도 그렇다).

    반환: `find_min_crossover_layout()`과 동일한 키 + `"branch_composites"`:
    `{composite_name: [real_name1, real_name2]}`(어떤 branch가 합성됐는지 투명하게
    남김, 세션16 F절 "성공 필드 하나로 전체를 판단하지 말 것" 원칙과 같은 이유로
    디버깅 정보를 조용히 숨기지 않는다)."""
    new_transistors, new_matching_pairs, new_pair_sensitivity, expand_map = \
        _composite_collapse_for_crossover(transistors, matching_pairs, pair_sensitivity)
    result = find_min_crossover_layout(new_transistors, new_matching_pairs, new_pair_sensitivity)
    expanded_segments = [
        {"transistor_sequence": [n for name in seg["transistor_sequence"]
                                  for n in expand_map.get(name, [name])],
         "node_sequence": seg["node_sequence"]}
        for seg in result["segments"]
    ]
    return {**result, "segments": expanded_segments, "branch_composites": expand_map}


def repair_matching_safety(rows: dict, matching_pairs: list, pair_sensitivity: dict | None = None,
                            max_iter: int = 3, relaxed_pairs: set | None = None) -> tuple:
    """배치 7-4 — `audit_row_split()`이 FAIL한 matching pair에 대해 `select_layout_tool()`
    (배치 7-4b)이 고른 도구(`interdigitate_layout`/`common_centroid_layout`)로 그 pair가
    속한 행을 재배치하고 재검증하는 걸 최대 `max_iter`회 반복한다.

    각 반복: (1) `audit_row_split()` 호출 (2) 필수 게이트로 실패한 pair들을 찾음(3) 두
    소자가 **같은 hub(source)를 공유**하면(같은 행에 있든, 서로 다른 행에 각각 통째로
    있든 — 실제 사고 사례가 정확히 후자였다, `known-incidents.md`) 원래 있던 행(들)에서
    둘 다 꺼내 `select_layout_tool()`이 고른 도구로 재배치 — 도구가 반환한 새
    행들(`f"{원래행}_repair{i}"`)로 대체한다 (4) 하나라도 재배치가 있었으면 다시 (1)로.

    반환: `(rows, AuditResult)` — 최종 rows(수정됐을 수 있음)와 그 rows에 대한 마지막
    `audit_row_split()` 결과.

    **2026-08-05(세션10) L1 하드컷**: `pair_kinds`(kind 문자열) 대신 `pair_sensitivity`
    (축C, `{pair: "ratio"|"offset"}`)를 받는다 — `audit_row_split()`과 동일 계약, 하위호환
    shim 없음. 축B(`shares_node`)는 이미 같은 hub(source)를 공유한다는 전제(아래 참고)가
    확인된 뒤라 항상 `shares_diffusion_node(ta, tb)`로 즉석 계산한다.

    ⚠️ 정직한 한계(2026-07-31, 세션16에 일부 완화): `interdigitate_layout()`/
    `common_centroid_layout()`은 "같은 hub net(source)을 공유하는 소자들"만 입력으로
    받는다 — pair의 두 소자가 서로 다른 hub를 쓰면(공유 노드가 없는 `branch_symmetric` 쌍이
    실제로 이런 경우가 있다) 원래는 이 도구들 자체가 적용 불가능했다. **세션16부터**: 그런
    경우에도 각자 `kcl_series_union()` 직렬 branch(예: M1a-M2a 캐스코드 컬럼)가 서로
    완전히 대응되는 거울 branch(`_branch_composite_pair()`)면, branch 전체를 하나의
    합성 소자처럼 묶어 적용한다 — "M2a/M2b가 M1a/M1b와 같이 움직이게" 만들어 조용히
    스킵되던 사각지대를 좁힌다. branch 구조 자체가 없거나(단독 소자) 대응이 안 맞으면
    (부분만 선언됨, 길이 다름, 3소자 이상 체인 등) 여전히 그 pair를 건드리지 않고 넘어간다
    (진행이 전혀 없으면 `max_iter`를 다 채우지 않고 조기 종료) — `run_topology_pipeline()`의
    기존 docstring이 이미 밝힌 한계(사람이 `search_stack_finger_w()`로 직접 조정)는 이
    범위 밖에서는 그대로 유효하다.

    ⚠️⚠️ branch 복합 매칭으로도 3c(common-centroid)가 항상 통과하는 건 아니다 — `n_fingers`가
    너무 작으면(예: 1) `common_centroid_layout()`의 회전-최적 경로 자체가 기하학적으로
    `dx<=0.5`를 달성 못 한다(세션16에서 실측 확인, 최선이 `dx=1.0`). 이건 이 함수의 책임
    밖이다(핑거 수를 늘리는 건 gm/ID 재검증이 필요해 `sizing_recipe.py` 쪽 오케스트레이션
    몫 — 세션17에 `run_matching_safety_with_finger_growth()`로 구현됨, 아래 `relaxed_pairs`
    참고).

    **세션17 신설 — `relaxed_pairs`(레이아웃 전용 최후수단 완화)**: `{frozenset({a,b}), ...}`
    형태로 주어지면, 그 쌍은 `select_layout_tool()`의 판단(offset/branch_symmetric은 항상
    common-centroid)을 무시하고 `interdigitate_layout`을 강제 적용한다 — sizing은 전혀
    건드리지 않는 순수 layout 오버라이드다. 호출자(`run_matching_safety_with_finger_growth()`)가
    "핑거증가가 gm/ID 예산 때문에 막혔다"고 판단한 쌍에 대해서만 이 집합을 채워 넘긴다 —
    trim으로 보정 가능한 layout mismatch가, trim 불가능한 gm/ID 스펙 위반보다 감수할 만한
    열화라는 판단(세션17 설계 논의, `.ai/context.md` 참고). 공유 hub도 없고 branch composite도
    안 되는 쌍은(위 "정직한 한계") `relaxed_pairs`에 있어도 여전히 손 못 댄다 — 완화는 이미
    존재하는 layout 자유도를 최후수단으로 쓰는 것이지, 없는 자유도를 만들어내지 않는다."""
    pair_sensitivity = pair_sensitivity or {}
    relaxed_pairs = relaxed_pairs or set()
    current_rows = {k: list(v) for k, v in rows.items()}

    def _sensitivity_of_pair(a, b):
        for key in ((a, b), (b, a), frozenset({a, b})):
            if key in pair_sensitivity:
                return pair_sensitivity[key]
        raise ValueError(f"pair_sensitivity에 ({a},{b}) 쌍의 matching_sensitivity가 없다")

    result = audit_row_split(current_rows, matching_pairs=matching_pairs,
                              pair_sensitivity=pair_sensitivity)
    for _ in range(max_iter):
        if result.ok:
            break
        failing = _failing_required_pairs(result)
        if not failing:
            break
        progressed = False
        touched_this_round: set = set()  # 세션16: 같은 branch가 이번 라운드에 이미 재배치
        # 됐으면 재처리하지 않는다 -- (M1a,M1b)/(M2a,M2b)처럼 같은 branch를 가리키는 두
        # 실패 항목이 `failing`에 둘 다 있으면, 하나를 처리하는 순간 branch 전체(4소자)가
        # 이미 옮겨지므로 나머지 하나를 또 처리하면 새 행 이름에 "_repair0"이 raound마다
        # 중첩돼 쌓이기만 하고(회전 위치는 이미 최선) 실질적 진전은 없다.
        for (a, b) in failing:
            if a in touched_this_round and b in touched_this_round:
                continue
            devs_by_name, origin_rows = {}, {}
            for rn, devs in current_rows.items():
                for t in devs:
                    if t.name in (a, b):
                        devs_by_name[t.name] = t
                        origin_rows[t.name] = rn
            if a not in devs_by_name or b not in devs_by_name:
                continue
            ta, tb = devs_by_name[a], devs_by_name[b]
            # 세션16: source 공유 여부와 무관하게 항상 먼저 branch 복합 매칭을 시도한다 --
            # (a,b)가 kcl 직렬 branch(예: M1a-M2a)에 속해 있으면, 설령 ta.source==tb.source라
            # 개별 소자 단위로도 이 도구들을 바로 적용할 수 있는 경우조차, branch 전체를
            # 하나로 묶어야 그 branch의 나머지 반쪽(예: M2a/M2b)이 조용히 스킵되지 않는다.
            # branch 구조가 없으면(단독 소자, 3소자+ 체인 등) `None`을 돌려주므로 아래 기존
            # 개별-소자 경로로 자연히 폴백된다(하위호환, branch 없는 회로는 완전히 그대로).
            all_devs_by_name = {t.name: t for devs in current_rows.values() for t in devs}
            composite = _branch_composite_pair(a, b, all_devs_by_name, matching_pairs)
            if composite is not None:
                ca, cb = composite["composite_a"], composite["composite_b"]
                # (finger_w 물리 정합성 검증은 _branch_composite_pair() 안에서 실제 4개
                # 소자로 이미 확인됨 -- ca/cb는 finger_w 없는 합성 래퍼라 여기서 비교 불가.
                # 아래 §2.5 INTERDIGITATION_PATTERNS 참고, 2026-08-13 세션31 신설.)
                expand_map = composite["expand"]
                hub_a, leaf_a = expand_map[ca.name]
                hub_b, leaf_b = expand_map[cb.name]
                real_names = (hub_a, leaf_a, hub_b, leaf_b)
                if frozenset({a, b}) in relaxed_pairs:
                    # 세션17: 완화 대상 -- select_layout_tool()의 common-centroid 판단을
                    # 무시하고 최후수단으로 interdigitate_layout을 강제한다(layout 전용).
                    layout = interdigitate_layout([ca, cb])
                else:
                    tool_hub = select_layout_tool(_sensitivity_of_pair(hub_a, hub_b), True)
                    tool_leaf = select_layout_tool(_sensitivity_of_pair(leaf_a, leaf_b), True)
                    if "common_centroid_layout" in (tool_hub, tool_leaf):
                        layout = common_centroid_layout([ca, cb], n_rows=min(2, ca.n_fingers, cb.n_fingers))
                    else:
                        layout = interdigitate_layout([ca, cb])
                expanded_rows = [{"transistor_sequence":
                                   [n for name in row["transistor_sequence"]
                                    for n in expand_map.get(name, [name])]}
                                  for row in layout["rows"]]
                devs2, origin2 = {}, {}
                for rn, devs in current_rows.items():
                    for t in devs:
                        if t.name in real_names:
                            devs2[t.name] = t
                            origin2[t.name] = rn
                if any(n not in devs2 for n in real_names):
                    continue  # branch 구성원 일부가 이미 없어짐 -- 안전하게 skip
                base_row_name = origin2[hub_a]
                # 2026-08-14(세션32) -- 이름 충돌 방지를 위해 필터/삭제를 먼저 끝내고
                # (남겨진 다른 소자가 있는 행은 그대로, 빈 행은 삭제) 그 *이후*의
                # current_rows를 existing_rows로 넘겨야 한다 -- _layout_result_to_rows()
                # docstring 참고(같은 이름을 나중에 다른 쌍이 재생성해 덮어쓰던 버그).
                for rn in set(origin2.values()):
                    current_rows[rn] = [t for t in current_rows[rn] if t.name not in real_names]
                    if not current_rows[rn]:
                        del current_rows[rn]
                new_rows = _layout_result_to_rows({"rows": expanded_rows}, devs2, base_row_name,
                                                   existing_rows=current_rows)
                current_rows.update(new_rows)
                progressed = True
                touched_this_round.update(real_names)
                continue
            if ta.source != tb.source:
                continue  # 공유 hub 없음 + branch 복합도 안 됨 -- 이 도구들 적용 불가(정직한 한계)
            if (ta.finger_w is not None and tb.finger_w is not None
                    and not math.isclose(ta.finger_w, tb.finger_w, rel_tol=1e-9)):
                continue  # finger_w가 다른 unit cell -- 위 composite 경로와 동일 이유로 적용 불가
            sens = _sensitivity_of_pair(a, b)
            # 세션17: relaxed_pairs에 있으면 select_layout_tool()의 판단을 무시하고
            # interdigitate_layout을 강제한다(위 docstring "relaxed_pairs" 참고).
            tool_name = "interdigitate_layout" if frozenset({a, b}) in relaxed_pairs \
                else select_layout_tool(sens, shares_diffusion_node(ta, tb))
            if tool_name == "interdigitate_layout":
                layout = interdigitate_layout([ta, tb])
            else:
                # common_centroid_layout()의 기본 n_rows(=len(transistors)=2)는 회전-최적
                # 경로(_common_centroid_nway_exact)를 타는데, 그 경로는 소자마다 행당 최소
                # 1핑거가 필요해 n_fingers<2(예: n_fingers=1인 매칭쌍)면 ValueError로 크래시
                # 한다(세션15 A-3에서 발견, 세션16에서 원인 확정) -- n_rows를
                # min(2, n_fingers)로 낮춰 그 경우에만 탐색 경로(_common_centroid_nway_search)
                # 로 보낸다. n_fingers>=2인 기존 케이스는 n_rows=2로 기존 기본값과 완전히
                # 동일하게 동작(회귀 없음).
                n_rows = min(2, ta.n_fingers, tb.n_fingers)
                layout = common_centroid_layout([ta, tb], n_rows=n_rows)
            base_row_name = origin_rows[a]
            # 2026-08-14(세션32) -- 필터/삭제를 먼저 끝낸 뒤 그 이후의 current_rows를
            # existing_rows로 넘긴다(_layout_result_to_rows() docstring 참고 -- 이름
            # 충돌로 남은 소자가 조용히 덮어써지던 실측 버그의 근본수정).
            for rn in set(origin_rows.values()):
                current_rows[rn] = [t for t in current_rows[rn] if t.name not in (a, b)]
                if not current_rows[rn]:
                    del current_rows[rn]
            new_rows = _layout_result_to_rows(layout, {a: ta, b: tb}, base_row_name,
                                               existing_rows=current_rows)
            current_rows.update(new_rows)
            progressed = True
            touched_this_round.update((a, b))
        if not progressed:
            break
        result = audit_row_split(current_rows, matching_pairs=matching_pairs,
                                  pair_sensitivity=pair_sensitivity)
    return current_rows, result


# ---------------------------------------------------------------------------
# 6.7) Floorplan 패킹 — stick diagram으로 확정된 stack들을 빈 공간 없이 box로 packing
#      (2026-07-27 신설, 그리고 곧바로 재작성됨: 첫 버전은 spine을 세로 한 줄로 쌓고 좌우 대칭
#      쌍도 그 순서 그대로 나열하기만 해서 "대칭은 맞지만 빈 공간을 늘어놓아 box 모양처럼 보이게"
#      만들 뿐이었다 — 사용자가 직접 지적: "빈공간을 없애서 box형태로 만들어야 의미가 있다,
#      아날로그 layout은 대칭·매칭이 중요하지만 면적도 작게 만드는 게 target이다." 이 지적을
#      받아 실제 2D bin-packing(스카이라인/bottom-left 알고리즘 — Jylänki, "A Thousand Ways to
#      Pack the Bin", 2010; 이 알고리즘이 만드는 "낮은 컨투어를 유지하며 쌓는다"는 원리는
#      analog placement 문헌의 B*-tree/ASF-B*-tree contour packing(Lin & Chang 등, symmetry-
#      island 개념)이 대칭 그룹을 다루는 방식과 같은 원리다 — 이 구현은 그 전체 최적화 도구
#      (simulated annealing 기반 B*-tree 등)까지는 아니지만, 핵심 아이디어인 "각 블록을 현재
#      컨투어에서 가장 낮아지는 위치에 배치"는 실제로 구현한다)로 재작성했다.
# ---------------------------------------------------------------------------

@dataclass
class FloorplanBlock:
    """floorplan 배치 대상 1개 — stick diagram의 stack(들)을 하나의 사각형으로 집계한 것.
    `width`/`height`는 절대 물리 치수가 아니라 **비율 프록시**다(finger 개수/행 개수 기반) —
    실제 실리콘 치수를 아는 것처럼 지어내지 않는다는 원칙을 여기서도 지킨다."""
    name: str
    width: float
    height: float


@dataclass
class PlacedBlock:
    name: str
    x: float
    y: float
    width: float
    height: float


@dataclass
class FloorplanResult:
    placements: dict            # name -> PlacedBlock
    bbox_width: float
    bbox_height: float
    aspect_ratio: float          # max(w,h)/min(w,h) -- check_box_shape()과 같은 개념, 스케일만 다름
    packing_density: float       # 전체 block 면적 합 / bbox 면적 -- 1.0에 가까울수록 빈 공간 없음
    symmetry_axis_x: float
    symmetry_max_error: float    # 좌우 대칭쌍의 위치/크기 불일치 최대값(0이면 완전 대칭)
    row_split_candidates: list   # 아래 evaluate_row_split_candidates() 참고


def _block_center(p: "PlacedBlock"):
    return (p.x + p.width / 2, p.y + p.height / 2)


def _total_wire_cost(placements: dict, connections: dict | None, y_targets: dict | None = None) -> float:
    """완성된 배치 하나에 대해, `connections`/`y_targets`가 요구하는 근접성을 실제로 얼마나
    만족했는지 하나의 숫자(가중 맨해튼 거리 합)로 집계한다. `skyline_pack()`이 배치 "도중"
    후보 하나를 고를 때 쓰는 지역적 판단과 달리, 이건 배치가 끝난 뒤 결과 전체를 평가하는
    용도다 — `pack_to_height()`가 "여러 폭 후보 중 어느 게 실제로 배선에 더 유리한가"를
    비교하려면 배치 도중 판단이 아니라 이 완성본 평가가 필요하다."""
    connections = connections or {}
    y_targets = y_targets or {}
    cost = 0.0
    seen = set()
    for name, conns in connections.items():
        if name not in placements:
            continue
        cx1, cy1 = _block_center(placements[name])
        for other, w in conns.items():
            if other not in placements or other == name:
                continue
            key = tuple(sorted((name, other)))
            if key in seen:
                continue
            seen.add(key)
            cx2, cy2 = _block_center(placements[other])
            cost += w * (abs(cx1 - cx2) + abs(cy1 - cy2))
    for name, target_y in y_targets.items():
        if name in placements:
            _, cy = _block_center(placements[name])
            cost += abs(cy - target_y)
    return cost


def skyline_pack(blocks: list, max_width: float, gap: float = 1.0,
                  connections: dict | None = None, y_targets: dict | None = None,
                  height_tolerance: float = 0.0):
    """Bottom-left skyline bin packing (Jylänki 2010) — 폭 `max_width` 안에서 각 블록을
    "지금까지 쌓인 윤곽선(skyline) 중 가장 낮아지는 위치"에 순서대로 배치해 빈 공간을
    최소화한다. 높이가 큰 블록부터 배치하는 것이 이 휴리스틱의 표준 순서(정렬 없이 입력
    순서대로 넣으면 큰 블록이 나중에 들어와 이미 채워진 자리를 못 쓰고 새 공간을 만든다).

    **신호선 근접 배치(2026-07-27 신설)**: 순수 면적 최적화만 하면 실제로 서로 강하게
    연결된 두 블록(예: bias-gen의 vbias1 leg와 그걸 게이트로 읽는 Class-AB 소자)이 아무
    회로적 이유 없이 멀리 떨어지는 사고가 실제로 있었다(§7에 "classab_p2는 biasgen 바로
    옆에 둬야 한다"고 명시했으면서도 §8 floorplan 좌표는 10칸 떨어져 있었다). 면적(높이)
    최소화가 여전히 **1순위**이므로, `height_tolerance` 이내로 높이가 비슷한 후보들 중에서만
    아래 두 가지로 2순위 배점한다(면적을 크게 희생하면서까지 배선 근접을 강제하지 않는다):
    - `connections`: `{name: {other_name: weight}}` — 이 함수 호출 안에서 **같이 packing되는**
      다른 블록과의 연결 가중치. 이미 배치된 연결 상대와의 중심점 거리 합에 가중치를 곱해 비용을
      계산하고, 낮을수록 선호한다.
    - `y_targets`: `{name: target_y}` — **이 호출 밖에서 이미 확정된** 다른 그룹의 y좌표에
      맞추고 싶을 때(예: spine을 먼저 packing해 bias-gen의 y를 알아낸 뒤, 별도로 packing하는
      Class-AB pair 유닛을 그 y에 가깝게 배치) 쓴다. `|y - target_y|`가 비용에 더해진다.

    반환: `(placements: {name: PlacedBlock}, bbox_width, bbox_height)` — 어떤 블록이 `max_width`
    안에 전혀 들어갈 자리가 없으면(폭 자체가 `max_width`보다 크거나, 배치 시도 중 자리를 못
    찾으면) `None`을 반환한다 — 호출자(`skyline_pack_best_width`)가 더 큰 `max_width`로 재시도."""
    connections = connections or {}
    y_targets = y_targets or {}
    ordered = sorted(blocks, key=lambda b: -b.height)
    skyline = [[0.0, max_width, 0.0]]  # [x_start, width, y] 세그먼트 목록
    placements = {}

    def height_at_span(x0, w):
        x1 = x0 + w
        y = 0.0
        for seg_x, seg_w, seg_y in skyline:
            if seg_x < x1 and seg_x + seg_w > x0:
                y = max(y, seg_y)
        return y

    def update_skyline(x0, w, new_y):
        x1 = x0 + w
        new_segs = []
        for seg_x, seg_w, seg_y in skyline:
            seg_x1 = seg_x + seg_w
            if seg_x1 <= x0 or seg_x >= x1:
                new_segs.append([seg_x, seg_w, seg_y]); continue
            if seg_x < x0:
                new_segs.append([seg_x, x0 - seg_x, seg_y])
            if seg_x1 > x1:
                new_segs.append([x1, seg_x1 - x1, seg_y])
        new_segs.append([x0, w, new_y])
        new_segs.sort(key=lambda s: s[0])
        skyline[:] = new_segs

    def wire_cost(name, x, y, w, h):
        cx, cy = x + w / 2, y + h / 2
        cost = 0.0
        for other, weight in connections.get(name, {}).items():
            if other in placements:
                ox, oy = _block_center(placements[other])
                cost += weight * (abs(cx - ox) + abs(cy - oy))
        if name in y_targets:
            cost += abs(cy - y_targets[name])
        return cost

    for b in ordered:
        if b.width > max_width:
            return None
        xs = [s[0] for s in skyline if s[0] + b.width <= max_width + 1e-9]
        if not xs:
            return None
        raw = [(x, height_at_span(x, b.width)) for x in xs]
        min_h = min(y for _, y in raw)
        candidates = [(x, y) for x, y in raw if y <= min_h + height_tolerance]
        if connections.get(b.name) or b.name in y_targets:
            x, y = min(candidates, key=lambda xy: (wire_cost(b.name, xy[0], xy[1], b.width, b.height), xy[1], xy[0]))
        else:
            x, y = min(candidates, key=lambda xy: (xy[1], xy[0]))
        placements[b.name] = PlacedBlock(b.name, x=x, y=y, width=b.width, height=b.height)
        update_skyline(x, b.width + gap, y + b.height + gap)

    bbox_w = max(p.x + p.width for p in placements.values())
    bbox_h = max(p.y + p.height for p in placements.values())
    return placements, bbox_w, bbox_h


def _sweep_widths(blocks: list, gap: float, width_steps: int,
                   connections: dict | None, y_targets: dict | None,
                   height_tolerance: float) -> list:
    """`min_w`(가장 넓은 블록의 폭)~`max_w`(모든 블록을 옆으로 늘어놓은 폭) 구간을
    `width_steps`개로 나눠 각 폭에서 `skyline_pack()`을 한 번씩 돌려본 `(w, placements, bw,
    bh)` 후보 리스트를 낸다 — `skyline_pack_best_width()`/`pack_to_height()`가 이 스윕 루프를
    각자 복붙해서 갖고 있던 걸 공용 코어로 뽑았다(2026-07-28, 순수 리팩터 — 동작 동일).
    스윕 자체는 후보만 생성하고, "어느 폭을 채택할지"(ratio 최근접인지, target_height 이하
    중 최소폭/배선비용인지)는 호출자가 반환값 위에서 직접 판단한다."""
    min_w = max(b.width for b in blocks)
    max_w = sum(b.width for b in blocks) + gap * len(blocks)
    candidates = []
    for i in range(width_steps + 1):
        w = min_w + (max_w - min_w) * i / width_steps
        result = skyline_pack(blocks, w, gap=gap, connections=connections, y_targets=y_targets,
                               height_tolerance=height_tolerance)
        if result is None:
            continue
        placements, bw, bh = result
        candidates.append((w, placements, bw, bh))
    return candidates


def skyline_pack_best_width(blocks: list, gap: float = 1.0, width_steps: int = 60,
                             target_ratio: float = 1.0, connections: dict | None = None,
                             y_targets: dict | None = None, height_tolerance: float = 0.0):
    """`skyline_pack()`은 컨테이너 폭을 입력으로 받는데, 그 폭 자체는 이 알고리즘이 정하지
    않는다(문헌에서도 호출자가 폭을 정하거나 스윕하는 것이 표준 사용법이다). 여기서는 후보 폭을
    여러 개 스윕해 **이 skill의 box-shape 목표(`check_box_shape()`, ratio<=1.5)와 같은 기준**
    으로 가장 정사각형에 가까운(= `target_ratio`에 가장 가까운) 결과를 고른다 — 단순히 면적을
    최소화하면 아주 옆으로 길쭉한 모양이 최소 면적일 수 있어(실제로 이 함수 작성 중 확인됨)
    이 skill이 지금까지 일관되게 써온 "비율" 기준과 다른 목표를 최적화하게 된다.

    **언제 이 함수를 쓰는가**: 대칭쌍이 전혀 없는(모두 spine뿐인, 또는 대칭 요구사항이 없는)
    단일 블록 그룹을 그 자체로 정사각형에 가깝게 packing하고 싶을 때 직접 쓴다. spine과 좌우
    대칭쌍을 함께 다뤄야 하면(이 skill의 일반적인 상황) 이 함수 대신 `pack_floorplan()`이
    내부에서 쓰는 `pack_to_height()`를 쓴다 — 두 조각을 각자 독립적으로 이 함수로 최적화하면
    서로 높이가 안 맞아 결합 결과가 길쭉해지는 문제가 실제로 있었다(`pack_floorplan()`
    docstring 참고)."""
    candidates = _sweep_widths(blocks, gap, width_steps, connections, y_targets, height_tolerance)
    best = None
    for w, placements, bw, bh in candidates:
        ratio = max(bw, bh) / min(bw, bh) if min(bw, bh) > 0 else float("inf")
        density = sum(b.width * b.height for b in blocks) / (bw * bh)
        score = (round(abs(ratio - target_ratio), 3), -density)
        if best is None or score < best[0]:
            best = (score, placements, bw, bh)
    return best[1], best[2], best[3]


def pack_to_height(blocks: list, target_height: float, gap: float = 1.0, width_steps: int = 60,
                    connections: dict | None = None, y_targets: dict | None = None,
                    height_tolerance: float = 0.0, width_tolerance: float = 0.0):
    """`skyline_pack_best_width()`가 "가장 정사각형에 가까운 폭"을 고르는 것과 달리, 이 함수는
    "결과 높이가 `target_height`를 넘지 않는 폭"을 찾는다 — spine과 좌우 pair-stack을
    **같은 목표 높이에 맞춰야** 나란히 배치했을 때 전체가 정사각형에 가까워지기 때문에
    (`pack_floorplan()`의 결합 단계가 이 함수를 쓰는 이유), 각 조각을 독립적으로 최적화하는
    `skyline_pack_best_width()`만으로는 부족하다(실제로 그렇게 짰다가 spine과 pair-stack의
    높이가 서로 안 맞아 전체 bbox가 옆으로 길쭉해지는 걸 이 함수 작성 전 버전에서 확인했다).

    **`width_tolerance`(2026-07-27 신설, `connections`/`y_targets`와 함께 쓸 것)**: 기본값
    0이면 이전과 동일하게(가장 좁은 폭 하나만 선택) 동작한다. 0보다 크면, "가장 좁은 폭"부터
    "가장 좁은 폭 + width_tolerance"까지의 후보들을 전부 계산해 그중 **완성된 배치의 실제
    배선 비용(`_total_wire_cost()`)이 가장 낮은 것**을 고른다.

    **왜 필요한가(실제 사고)**: `connections`/`y_targets`를 `skyline_pack()`에 줘도, 이 함수가
    "가장 좁은 폭 하나"만 시도하면 그 폭에서는 애초에 배치 후보가 1개뿐이라(컨테이너가 꽉
    차서 곁가지로 놓을 자리 자체가 없음) 배선 비용을 반영할 여지가 물리적으로 없다 — 실제로
    이 상태로 "bias-gen과 vbias1로 연결된 classab_p2를 가깝게 배치하라"를 시도했더니 폭을
    조금도 안 늘려서 전혀 안 움직였다. 폭을 살짝 늘려 곁가지로 놓을 자리를 만들어줘야 배선
    비용 비교가 의미를 갖는다 — 이것도 "면적을 무한정 희생하지 않는다"는 원칙과 같은 방식으로
    상한(`width_tolerance`)을 둔다."""
    max_w = sum(b.width for b in blocks) + gap * len(blocks)
    candidates = _sweep_widths(blocks, gap, width_steps, connections, y_targets, height_tolerance)
    valid = [(bw, placements, bh) for w, placements, bw, bh in candidates if bh <= target_height]
    if not valid:  # target_height too tight for any width -- fall back to widest (flattest) packing
        placements, bw, bh = skyline_pack(blocks, max_w, gap=gap, connections=connections,
                                           y_targets=y_targets, height_tolerance=height_tolerance)
        return placements, bw, bh
    min_bw = min(bw for bw, _, _ in valid)
    if width_tolerance <= 0 or not (connections or y_targets):
        bw, placements, bh = min(valid, key=lambda t: t[0])
        return placements, bw, bh
    band = [t for t in valid if t[0] <= min_bw + width_tolerance]
    bw, placements, bh = min(band, key=lambda t: _total_wire_cost(t[1], connections, y_targets))
    return placements, bw, bh


def find_diffusion_safe_split_points(transistor_sequence: list) -> list:
    """`build_stick_diagram()`이 반환한 실제 `transistor_sequence`(finger 순서)에서, 어느
    소자의 finger도 반으로 갈리지 않는 분할 지점을 전부 찾는다. 두 물리 finger가 연속
    diffusion을 공유하면(같은 소자의 병렬 finger들이 항상 그렇다) 그 사이를 끊어 서로 다른
    물리 행에 넣으려면 실제로는 그 소자를 2개로 쪼개 만들고 별도 contact/via를 추가해야 한다
    (이른바 "소자 folding") — 이건 사소한 배치 조정이 아니라 별도 설계 결정이므로, 이 함수는
    그런 지점을 "안전한 분할점"으로 취급하지 않는다.

    분할 지점 i(1<=i<len(seq))가 안전하려면 `seq[:i]`와 `seq[i:]`에 **공통으로 등장하는 소자
    이름이 하나도 없어야** 한다 — 즉 각 소자가 어느 한쪽에만 통째로 들어있어야 한다.

    반환: 안전한 분할 지점 인덱스 리스트(오름차순, 없으면 빈 리스트 — 예: 이 세션의 실제
    S1_TAILP 시퀀스 `[M6,M6,M6,M6,M7,M6,M7,M6,M7,M6]`은 M6/M7이 전체 구간에 걸쳐 완전히
    인터리브돼 있어 안전한 분할 지점이 하나도 없다 — `find_diffusion_safe_split_points()`로
    실제 확인됨)."""
    n = len(transistor_sequence)
    valid = []
    for i in range(1, n):
        left, right = set(transistor_sequence[:i]), set(transistor_sequence[i:])
        if not (left & right):
            valid.append(i)
    return valid


def evaluate_row_split_candidates(blocks: list, bbox_width: float, bbox_height: float,
                                   dominance_ratio: float = 0.6,
                                   transistor_sequences: dict | None = None) -> list:
    """packing이 끝난 뒤, 특정 블록 하나의 폭(또는 높이)이 전체 bbox의 지배적인 부분을 차지해
    box-shape를 깨뜨리고 있는지 진단한다 — §8.5(row-split 비용 계산)와 같은 목적을 floorplan
    레벨로 옮긴 것. **이 함수는 스스로 finger 수를 바꾸지 않는다** — 후보만 알려준다.

    `transistor_sequences`(선택, `{block_name: transistor_sequence}` — `build_stick_diagram()`
    이 실제로 반환한 값 그대로): 주어지면 각 후보에 대해 `find_diffusion_safe_split_points()`로
    **실제로 안전하게 쪼갤 수 있는 지점이 있는지까지 확인**한다(사용자 지적: "packing할 때
    MOS의 diffusion 영역이 고려돼서 엉뚱하게 split되는 문제가 없도록 해야 한다" — 폭/높이가
    지배적이라는 사실만으로 분할을 추천하면 특정 소자의 finger를 반으로 가르는 물리적으로
    무의미한 분할을 제안할 위험이 있다. 실제로 이 회로의 S1_TAILP(M6:M7 인터리브 tail)가 정확히
    이런 사례 — 폭이 가장 넓은 spine 행이지만 안전한 분할 지점이 하나도 없다). `splittable`이
    `False`면 **분할을 제안하지 말고** 대신 §8.5의 "행 분할 없이 수용" 논리를 적용할 것.
    `transistor_sequences`를 안 주면 `diffusion_check: "not_verified"`로 정직하게 표시한다 —
    확인 안 했으면서 안전하다고 가정하지 않는다.

    실제로 쪼개기로 결정하면(그리고 `splittable`이 True면) 그 블록의 원래 stick diagram
    (`build_stick_diagram()`/`check_box_shape()`)부터 그 안전한 지점 기준으로 다시 계산하고,
    그 결과로 바뀐 gm/ID·W가 있으면 §5(sizing Definition of Done)와 SPICE 재검증까지
    되먹여야 한다(design-report-spec.md §1.7 참고) — 이 함수 하나로 끝나는 최적화가 아니다."""
    candidates = []
    for b in blocks:
        dominant = b.width >= dominance_ratio * bbox_width
        dominant_h = b.height >= dominance_ratio * bbox_height
        if not dominant and not dominant_h:
            continue
        dim = "width" if dominant else "height"
        value = b.width if dominant else b.height
        bbox_dim = bbox_width if dominant else bbox_height
        entry = {
            "name": b.name, "dimension": dim, "value": value, "bbox": bbox_dim,
            "reason": f"{dim} {value} covers >= {dominance_ratio*100:.0f}% of bbox {dim} {bbox_dim}",
        }
        if transistor_sequences is not None and b.name in transistor_sequences:
            splits = find_diffusion_safe_split_points(transistor_sequences[b.name])
            entry["diffusion_check"] = "verified"
            entry["splittable"] = len(splits) > 0
            entry["safe_split_points"] = splits
            if not splits:
                entry["reason"] += (" -- but NO diffusion-safe split point exists (every device's "
                                     "fingers are interleaved across the whole row) -- do not split, "
                                     "accept per sec8.5 reasoning instead")
        else:
            entry["diffusion_check"] = "not_verified"
            entry["splittable"] = None
        candidates.append(entry)
    return candidates


def pack_floorplan(spine: list, mirror_pairs: list, gap: float = 1.0, height_steps: int = 40,
                    transistor_sequences: dict | None = None,
                    net_weights: dict | None = None, height_tolerance: float = 1.0,
                    width_tolerance: float = 2.0) -> FloorplanResult:
    """공유(비대칭) 블록(spine)과 좌우 대칭 블록 쌍(mirror_pairs)을 함께 packing한다.

    좌우 대칭 쌍은 **각 쌍을 (max(오른쪽폭,왼쪽폭) x max(오른쪽높이,왼쪽높이)) 크기의 단일
    유닛으로 취급해 그 유닛들끼리 packing**한 뒤, 유닛이 배치된 자리를 좌우로 거울반사해서
    실제 두 블록을 채운다 — 대칭은 유닛을 반으로 나눠 채우는 방식 자체가 구조적으로 보장한다
    (ASF-B*-tree의 symmetry-island와 같은 원리: 대칭 그룹을 따로 다뤄 사후 검증하는 게 아니라
    애초에 깨질 수 없게 만든다).

    spine과 pair-unit들은 **같은 목표 높이 H에 맞춰(`pack_to_height()`) 나란히 배치**한다 —
    spine과 pair-stack을 각자 독립적으로 "제일 정사각형에 가까운 모양"으로 최적화하면(첫
    재작성 버전이 이렇게 했다) 둘의 높이가 서로 안 맞아서 나란히 붙였을 때 전체가 옆으로
    길쭉해지는 문제가 실제로 나왔다 — "spine 폭 + pair-stack 폭 x 2"가 전체 폭이고 "두 높이의
    max"가 전체 높이이므로, 두 조각의 높이를 미리 맞춰야 결합 결과도 정사각형에 가까워진다.
    여러 후보 H를 스윕해서 결합 결과의 aspect ratio가 가장 낮아지는 H를 채택한다.

    이 결합 방식에도 한계가 있다 — spine과 pair-stack을 여전히 "따로 packing한 뒤 옆으로
    붙이는" 2단계 구조라, 완전한 non-slicing floorplan(모든 블록을 한 번에 최적화)만큼
    빈틈이 없지는 않다. 잔여 비대칭/저밀도는 `packing_density`/`row_split_candidates`로
    그대로 보고한다 — FAIL이면 §8.5/§1.7 절차로 재검토할 것(이 함수가 자동으로 재귀
    최적화하지 않는다 — 그렇게 하려면 전체를 simulated annealing급 B*-tree로 다시 짜야 하고,
    이 skill의 범위를 넘는다).

    `transistor_sequences`(선택, `{block_name: transistor_sequence}` — `build_stick_diagram()`
    의 실제 반환값): 주면 `row_split_candidates`가 각 후보에 대해 실제로 diffusion을 깨지 않고
    쪼갤 수 있는 지점이 있는지까지 확인한다(`evaluate_row_split_candidates()` 참고) — packing
    단계가 어떤 소자의 finger를 반으로 가르는 분할을 조용히 추천하는 일을 막는다. 안 주면 그
    확인 자체를 안 했다고 `diffusion_check: "not_verified"`로 정직하게 표시한다.

    **신호선 근접 배치(2026-07-27 신설)**: `net_weights`(선택, `{name: {other_name: weight}}`,
    양방향 대칭 아니어도 됨 — 한쪽만 적어도 조회됨) — 실제 회로 net 공유(예: bias-gen의 vbias1
    leg와 그걸 게이트로 읽는 Class-AB 소자)를 반영해 강하게 연결된 block/pair를 서로 가깝게
    배치한다. **면적(box-shape)이 여전히 1순위** — `height_tolerance`(기본 1.0)만큼 높이가
    늘어나는 것까지만 허용하고, 그 안에서만 배선 비용을 줄이는 위치를 고른다(면적을 무한정
    희생하면서 배선 근접을 강제하지 않는다). spine 블록/그룹 간 연결은 spine packing에 직접
    반영되고, `mirror_pairs`(spine과 별도로 packing되는 대칭 유닛)는 이미 배치가 끝난 spine
    블록들과의 연결 가중치를 바탕으로 `y_target`(연결된 spine 블록들의 y좌표 가중평균)을 계산해
    반영한다 — **실제 사고**: 이 파라미터가 없던 버전은 "classab_p2는 bias-gen 바로 옆에 둬야
    한다"(§7에 이미 명시돼 있었음)는 회로 지식을 floorplan 좌표에 전혀 반영하지 못해 둘이
    10칸이나 떨어져 있었다(사용자가 직접 지적: "배치는 신호선과 근접한 곳에 위치시키면
    routing delay가 없어진다")."""
    sym_errors = []
    pair_units, unit_of_pair = [], {}
    for right, left in mirror_pairs:
        uw, uh = max(right.width, left.width), max(right.height, left.height)
        unit_name = f"__unit__{right.name}__{left.name}"
        pair_units.append(FloorplanBlock(unit_name, uw, uh))
        unit_of_pair[unit_name] = (right, left)
        sym_errors.append(abs(right.width - left.width) + abs(right.height - left.height))

    net_weights = net_weights or {}
    total_area = sum(b.width * b.height for b in spine) + 2 * sum(u.width * u.height for u in pair_units)
    h0 = total_area ** 0.5 if total_area > 0 else 1.0

    best = None
    for i in range(height_steps + 1):
        H = h0 * 0.3 + (h0 * 2.2) * i / height_steps
        sp, sw, sh = pack_to_height(spine, H, gap=gap, connections=net_weights,
                                     height_tolerance=height_tolerance,
                                     width_tolerance=width_tolerance) if spine else ({}, 0.0, 0.0)
        # pair-unit y_target = weighted-average y-center of already-placed spine blocks it connects to
        pair_y_targets = {}
        for unit_name, (right, left) in unit_of_pair.items():
            weighted, total_w_ = 0.0, 0.0
            for other, w_ in net_weights.get(right.name, {}).items():
                if other in sp:
                    cy = sp[other].y + sp[other].height / 2
                    weighted += w_ * cy
                    total_w_ += w_
            if total_w_ > 0:
                pair_y_targets[unit_name] = weighted / total_w_
        pp, pw, ph = pack_to_height(pair_units, H, gap=gap, y_targets=pair_y_targets,
                                     height_tolerance=height_tolerance,
                                     width_tolerance=width_tolerance) if pair_units else ({}, 0.0, 0.0)
        total_w = sw + (2 * (gap + pw) if pair_units else 0.0)
        total_h = max(sh, ph)
        ratio = max(total_w, total_h) / min(total_w, total_h) if min(total_w, total_h) > 0 else float("inf")
        if best is None or ratio < best[0]:
            best = (ratio, sp, sw, sh, pp, pw, ph, total_w, total_h)

    _, spine_placements, spine_w, spine_h, pair_placements, pair_stack_w, pair_stack_h, bbox_width, bbox_height = best

    placements = {}
    for name, p in spine_placements.items():
        placements[name] = PlacedBlock(name, x=p.x - spine_w / 2, y=p.y, width=p.width, height=p.height)

    right_anchor = spine_w / 2 + gap
    for unit_name, p in pair_placements.items():
        right, left = unit_of_pair[unit_name]
        placements[right.name] = PlacedBlock(right.name, x=right_anchor + p.x, y=p.y,
                                              width=right.width, height=right.height)
        placements[left.name] = PlacedBlock(left.name, x=-(right_anchor + p.x + left.width), y=p.y,
                                             width=left.width, height=left.height)

    physical_area = sum(b.width * b.height for b in spine) + sum(
        r.width * r.height + l.width * l.height for r, l in mirror_pairs)
    bbox_area = bbox_width * bbox_height
    all_blocks = list(spine) + [b for pair in mirror_pairs for b in pair]
    return FloorplanResult(
        placements=placements, bbox_width=bbox_width, bbox_height=bbox_height,
        aspect_ratio=(max(bbox_width, bbox_height) / min(bbox_width, bbox_height)
                      if min(bbox_width, bbox_height) > 0 else float("inf")),
        packing_density=(physical_area / bbox_area if bbox_area > 0 else 0.0),
        symmetry_axis_x=0.0, symmetry_max_error=max(sym_errors) if sym_errors else 0.0,
        row_split_candidates=evaluate_row_split_candidates(
            all_blocks, bbox_width, bbox_height, transistor_sequences=transistor_sequences),
    )


def block_from_rows(name: str, rows: dict) -> FloorplanBlock:
    """`rows`(`{row_name: [Transistor,...]}`, §8 box-shape 입력과 동일한 dict)를 하나의
    FloorplanBlock으로 집계한다 — 2026-08-13 세션31: `compute_row_geometry()`로 실제 물리
    폭/높이를 계산해서 쓴다(옛 `block_from_row_widths()`는 width=최대 행의 finger 개수,
    height=행 개수(=항상 1, `rebuild_floorplan()`이 매번 단일 행 dict로 호출했으므로)로
    실제 치수를 전혀 반영 못 했다 — `Transistor.finger_w`가 이미 있었는데도 안 쓰던
    구조적 버그). l/finger_w 결측 행은 `compute_row_geometry()`가 `width_m=None`을 주므로
    옛 finger-count/height=1 근사로 대체한다(조용히 넘기지 않고 `approx_devices`로 추적됨
    — 상위 호출자가 필요하면 `compute_row_geometry(rows)`를 직접 불러 확인할 것)."""
    geoms = compute_row_geometry(rows)
    widths = [g.width_m if g.width_m is not None else float(g.n_fingers_total) for g in geoms.values()]
    heights = [g.height_m if g.height_m is not None else 1.0 for g in geoms.values()]
    return FloorplanBlock(name, width=max(widths), height=sum(heights))


def rebuild_floorplan(rows: dict, floorplan_hints: dict | None = None) -> FloorplanResult:
    """`rows`(`{row_name: [Transistor,...]}`)만으로 floorplan을 새로 packing한다 --
    `run_topology_pipeline()`의 §8 floorplan 조립 로직(spine_groups 기본값 구성 ->
    `block_from_rows()` -> `pack_floorplan_grouped()`)을 그대로 추출한 것(동작
    변화 없음, `run_topology_pipeline()`도 이 함수를 호출하도록 리팩터됨).

    2026-08-13(세션31 CO) 신설 -- `optimize_full_circuit_budget()`이 `row_split`/
    matching-safety repair로 물리 행 구성을 재조정한 *뒤*에도 `floorplan`을 다시 계산할
    수 있도록 재사용 가능한 함수로 분리했다. 배경: 지금까지 `floorplan`은 그 재조정
    *이전*(euler-fixup 직후) 시점의 `row_widths`로 딱 한 번만 계산되고 다시는 갱신되지
    않아서, box-shape/stick-diagram은 최종 물리 행(예: `M6_split0`/`M6_split1` 2개)을
    보여주는데 floorplan만 재조정 이전의 통짜 블록(예: `M6` 1개, width=합산값)을 보여주는
    불일치가 있었다(실측 발견: `two_stage_ota`, `.ai/context.md` 세션31 CO 참고).

    같은 세션 후반(box-shape 실제 물리 치수 반영)에서 `row_widths: {name: finger_count}`
    대신 `rows: {name: [Transistor,...]}`를 받도록 재정의했다 — `block_from_rows()`가
    실제 폭/높이를 계산하려면 `Transistor.l`/`finger_w`가 필요하기 때문(§8 CI 이월 항목
    해소, `.ai/context.md` 참고).

    `floorplan_hints.spine_groups`가 있으면 그 그룹핑을(예: 여러 row를 한 macro-block으로
    묶는 지정) 그대로 쓴다. **2026-08-13(세션31, 사용자 지시 + 문헌 확인)**: 없으면 더 이상
    "행 하나=독립 spine"(옛 기본값)이 아니라 **kind(pmos/nmos)별 2개 super-block**으로
    묶는다 -- Xiao/Young/He/Pun, "Practical Placement and Routing Techniques for Analog
    Circuit Designs"(CUHK) §IV.C: "약 90%의 NMOS/PMOS가 source를 GND/Vdd에 물려 안정된
    전원 공급과 IR-drop 완화를 위해 같은 극성끼리 붙여 놓는다 -- NMOS와 PMOS를 두
    super-block으로 취급해 배치에서 서로 contiguous하도록 강제한다." PMOS 행들이 서로
    떨어져 배치되면 매번 n-well 경계/guard-ring 비용이 드는데, 같은 극성끼리 붙이면
    well을 공유해 면적을 아낄 수 있다(반대로 PMOS/NMOS를 번갈아 배치하는 건 면적
    최적화 관점에서 불리함, 사용자 지적). 이 그룹핑은 이미 있는 `pack_group_as_unit()`
    (super-block 내부를 촘촘히 먼저 패킹한 뒤 하나의 블록으로 상위 packing에 넘김)을
    그대로 재사용한다 -- 새 packing 알고리즘이 아니라 기본 그룹 구성만 바꾼 것.

    2026-08-13(세션31, box-shape/floorplan 실측 상관성 개선 중 신설) -- `FloorplanResult.
    row_split_candidates`(`evaluate_row_split_candidates()`)의 diffusion-safe 분할점 검증
    (`splittable` 필드)이 지금까지 `transistor_sequences`를 아무도 안 넘겨줘서 항상
    `"not_verified"`(`None`)였다 -- 자동 row_split 재시도 루프(호출자, 예:
    `workspaces/run_harness.py`)가 "안전하게 쪼갤 수 있는 후보만" 골라 쓰려면 이 값이
    실제로 채워져 있어야 한다. 여기서 각 row마다 `build_stick_diagram()`을 다시 계산해
    채운다(`audit_row_split()`이 이미 하는 것과 같은 계산 1회 추가뿐 -- 비용 문제 없음).
    euler 실패(status != "ok")한 행은 sequence가 무의미하므로 건너뛴다(그 행만
    not_verified로 남고 나머지는 정상 검증됨 -- 부분 실패를 전체 실패로 안 키운다).
    `spine_groups`로 여러 row를 하나의 group으로 묶은 경우, 그 group 블록의 이름은 어떤
    개별 row 이름과도 안 맞으므로(합쳐진 블록이라 단일 sequence가 없음) 그 그룹은 여전히
    "not_verified"로 정직하게 남는다(기본 1행=1그룹 경우에만 실제로 채워짐).

    ⚠️ 2026-08-13(세션31, box-shape 실측 물리 치수 반영 직후 실측으로 발견) -- `pack_
    floorplan_grouped()`/`pack_floorplan()`류의 `gap` 기본값(1.0)은 옛 finger-count
    좌표계(블록 폭이 대략 1~50 사이 정수)를 전제로 정해진 값이다. `block_from_rows()`가
    이제 실제 물리 치수(m 단위, 대략 1e-8~1e-4 스케일)를 만들어내면서, `gap=1.0`(사실상
    1미터)이 블록 크기를 통째로 집어삼켜 aspect_ratio가 수만대1로 튀는 버그가 실측
    확인됐다(`two_stage_ota`, floorplan.aspect_ratio=125605 -- 명백히 물리적으로
    무의미). `gap`도 CPP/spacing과 같은 "미확보 PDK 상수" 범주라 절대값을 지어내지
    않고, 대신 **블록 크기에 비례하는 상대값**(중앙값 폭의 5%)을 쓴다 -- 실제 spacing
    규칙을 확보하면 이 비율만 교체하면 된다."""
    hints = floorplan_hints or {}
    spine_groups_names = hints.get("spine_groups")
    if not spine_groups_names:
        spine_groups_names = defaultdict(list)
        for name, devs in rows.items():
            kind = devs[0].kind if devs else "nmos"
            spine_groups_names[kind].append(name)
        spine_groups_names = dict(spine_groups_names)
    blocks_by_name = {name: block_from_rows(name, {name: rows[name]})
                      for name in rows}
    spine_groups = {gname: [blocks_by_name[bname] for bname in members if bname in blocks_by_name]
                    for gname, members in spine_groups_names.items()}
    transistor_sequences = {}
    for name, devs in rows.items():
        out = build_stick_diagram(devs)
        r = out.get(name)
        if r is not None and r.status == "ok":
            transistor_sequences[name] = r.transistor_sequence
    all_widths = sorted(b.width for b in blocks_by_name.values() if b.width > 0)
    gap = hints.get("gap")
    if gap is None:
        gap = 0.05 * all_widths[len(all_widths) // 2] if all_widths else 1.0
    return pack_floorplan_grouped(spine_groups, hints.get("mirror_pairs") or [],
                                    gap=gap, net_weights=hints.get("net_weights"),
                                    transistor_sequences=transistor_sequences)


def _pack_by_subkind(blocks: list, sub_kind: dict, gap: float = 1.0, height_steps: int = 40):
    """`blocks`를 `sub_kind`(예: `{"cmfb_p1": "pmos", "cmfb_n1": "nmos", ...}` — 같은 물리
    diffusion/폴러리티에 속하는 row를 묶는 키)로 나눠, 각 하위그룹을 **공통 목표 높이에
    맞춰서(`pack_to_height()`) 따로 packing한 뒤 옆으로 나란히 붙인다** — `pack_floorplan()`이
    spine과 mirror-pair-stack을 결합하는 것과 정확히 같은 원리를 그룹 내부에도 한 단계 더
    적용한 것. 2개 미만의 하위그룹이면(전부 같은 kind면) 나눌 의미가 없어 `None`을 반환한다.

    반환: `(FloorplanBlock, internal_placements)` — `pack_group_as_unit()`과 같은 형식."""
    by_kind: dict = {}
    for b in blocks:
        by_kind.setdefault(sub_kind.get(b.name, "_default"), []).append(b)
    if len(by_kind) < 2:
        return None

    total_area = sum(b.width * b.height for b in blocks)
    h0 = total_area ** 0.5 if total_area > 0 else 1.0
    best = None
    for i in range(height_steps + 1):
        H = h0 * 0.3 + (h0 * 2.2) * i / height_steps
        packed = []
        for kind, blks in by_kind.items():
            pl, bw, bh = pack_to_height(blks, H, gap=gap)
            packed.append((pl, bw, bh))
        total_w = sum(bw for _, bw, _ in packed) + gap * (len(packed) - 1)
        total_h = max(bh for _, _, bh in packed)
        ratio = max(total_w, total_h) / min(total_w, total_h) if min(total_w, total_h) > 0 else float("inf")
        if best is None or ratio < best[0]:
            best = (ratio, packed, total_w, total_h)
    _, packed, gw, gh = best

    internal = {}
    x_off = 0.0
    for pl, bw, bh in packed:
        for bname, p in pl.items():
            internal[bname] = PlacedBlock(bname, x=p.x + x_off, y=p.y, width=p.width, height=p.height)
        x_off += bw + gap
    return FloorplanBlock("_", gw, gh), internal


def pack_group_as_unit(name: str, blocks: list, gap: float = 1.0, target_ratio: float = 1.0,
                        net_weights: dict | None = None, height_tolerance: float = 1.0,
                        sub_kind: dict | None = None):
    """기능적으로 묶여야 하는 block 그룹(예: CMFB의 5개 stack 전부)을 그 그룹 내부에서만
    `skyline_pack_best_width()`로 촘촘히 packing한 뒤, 그 결과를 **하나의 FloorplanBlock으로
    캡슐화**한다 — 상위 packer(`pack_floorplan()`)는 이 그룹을 더는 쪼갤 수 없는 블록 하나로만
    본다.

    **왜 필요한가(실제 사고)**: `pack_floorplan()`에 spine 전체(Stage-1/bias-gen/CMFB 등 서로
    무관한 기능 블록의 모든 물리 행)를 평평한 리스트로 넘기면, skyline packer는 "빈 공간 최소화"
    만 최적화하지 "같은 회로 블록끼리 뭉쳐 있어야 한다"는 건 전혀 모른다 — 실제로 이 회로에서
    `cmfb_n1`(높이 2)이 CMFB의 나머지 4개 행(cmfb_p1/p2/n2, 전부 높이 1)과 떨어져 Stage-1의
    높이-2 블록들 사이에 끼어 들어가는 결과가 나왔다(사용자가 직접 지적: "cmfb_n1은 왜
    어중간하게 중간에 배치돼 있지?"). 이 함수는 좌우 대칭쌍을 하나의 유닛으로 다루는
    `pack_floorplan()`의 원리(§6.7 상단 설명)를 spine 내부의 **기능적 그룹**에도 그대로
    적용한 것 — 대칭 유닛이 "절대 갈라지면 안 되는 쌍"이듯, 기능 그룹도 "절대 갈라지면 안 되는
    묶음"으로 다룬다.

    **`sub_kind`(선택, 2026-07-27 신설)**: `{block_name: kind}` — 같은 물리 diffusion/폴러리티
    에 속하는 row를 표시한다(예: CMFB의 P측 legs vs N측 legs). 주어지면 이 함수는 **두 가지
    packing을 실제로 계산해서 비교한다**: (1) 이 그룹 전체를 하나로 보고 packing(기존 방식),
    (2) `_pack_by_subkind()`로 kind별로 나눠 각각 공통 높이에 맞춰 packing한 뒤 옆으로 붙이는
    방식(사용자 제안: "P영역/N영역을 구분해서 배치하면 더 compact해지지 않을까 — 확인해보라") —
    **둘 중 aspect ratio가 `target_ratio`(정사각형)에 더 가까운 쪽을 채택**한다(어느 쪽이
    더 나은지 가정하지 않고 매번 실측 비교). `sub_kind`를 안 주면 (1)만 계산한다(기존 동작과
    동일).

    **왜 밀도가 아니라 ratio로 고르는가(실제로 발견된 함정)**: 처음엔 "이 그룹만의
    `packing_density`가 더 높은 쪽"을 채택했는데, Stage-1에 실제로 적용해보니 그룹 자체의
    밀도는 같은데도(둘 다 밀도가 그대로거나 오히려 개선됐는데도) 모양이 10x9(거의 정사각형)
    에서 19x4(아주 옆으로 길쭉)로 바뀌었고, 이 길쭉한 그룹 블록이 상위 `pack_floorplan()`에서
    bias-gen/CMFB/Class-AB pair-stack과 결합되자 **전체 회로의 aspect ratio가 1.36→3.10으로
    악화**됐다 — "이 그룹만 보면 더 나은 선택"이 "전체로 보면 더 나쁜 선택"이었다. 그래서
    그룹 하나의 밀도가 아니라, 그 그룹이 **다른 조각과 잘 결합될 모양(정사각형에 가까움)**을
    기준으로 바꿨다.

    반환: `(group_block: FloorplanBlock, internal_placements: {name: PlacedBlock})` —
    `internal_placements`의 좌표는 그룹 내부 상대좌표(그룹의 좌상단이 원점)다. 상위 packing이
    이 그룹 블록의 최종 위치를 정하면, 그 위치를 이 상대좌표에 더해 각 구성 block의 절대좌표를
    복원한다(`pack_floorplan_grouped()`가 이 과정을 자동으로 한다)."""
    if len(blocks) == 1:
        b = blocks[0]
        return (FloorplanBlock(name, b.width, b.height),
                {b.name: PlacedBlock(b.name, 0.0, 0.0, b.width, b.height)})

    flat_placements, flat_w, flat_h = skyline_pack_best_width(
        blocks, gap=gap, target_ratio=target_ratio, connections=net_weights,
        height_tolerance=height_tolerance)
    flat_ratio = max(flat_w, flat_h) / min(flat_w, flat_h) if min(flat_w, flat_h) > 0 else float("inf")

    if sub_kind:
        by_kind_result = _pack_by_subkind(blocks, sub_kind, gap=gap)
        if by_kind_result is not None:
            _, kind_placements = by_kind_result
            kind_w = max(p.x + p.width for p in kind_placements.values())
            kind_h = max(p.y + p.height for p in kind_placements.values())
            kind_ratio = max(kind_w, kind_h) / min(kind_w, kind_h) if min(kind_w, kind_h) > 0 else float("inf")
            # 선택 기준은 "이 그룹만의 밀도"가 아니라 **aspect ratio(정사각형에 얼마나 가까운가)**다
            # -- 실제로 확인된 함정: Stage-1을 P/N으로 나누면 그 그룹 자체의 밀도는 그대로면서도
            # 모양이 10x9(정사각형)에서 19x4(옆으로 아주 길쭉)로 바뀌었다 -- 이 그룹 블록이 다른
            # 그룹/pair-stack과 결합되는 상위 packing에서는 "이 조각 자체가 얼마나 정사각형인가"가
            # "이 조각 내부에 빈틈이 없는가"보다 전체 결과에 더 크게 영향을 준다(실측: 이 기준으로
            # 안 걸렀을 때 전체 회로 aspect ratio가 1.36→3.10으로 악화됐었다). 그래서 밀도가 아니라
            # ratio로 고른다 — "이 그룹만 보면 더 나은 선택"이 "전체로 보면 더 나쁜 선택"일 수 있다는
            # 걸 발견한 뒤 반영한 기준이다.
            if abs(kind_ratio - target_ratio) < abs(flat_ratio - target_ratio):
                return FloorplanBlock(name, kind_w, kind_h), kind_placements

    return FloorplanBlock(name, flat_w, flat_h), flat_placements


def pack_floorplan_grouped(spine_groups: dict, mirror_pairs: list, gap: float = 1.0,
                           height_steps: int = 40, transistor_sequences: dict | None = None,
                           net_weights: dict | None = None, height_tolerance: float = 1.0,
                           width_tolerance: float = 2.0, sub_kinds: dict | None = None) -> FloorplanResult:
    """`pack_floorplan()`과 같은 일을 하지만, spine을 평평한 리스트가 아니라
    **`{group_name: [FloorplanBlock, ...]}`로 미리 기능별로 묶어서** 받는다 — 각 그룹은
    `pack_group_as_unit()`으로 먼저 내부 packing된 뒤 하나의 블록으로 상위 packing에 들어가므로,
    같은 그룹의 block들이 서로 갈라져 무관한 다른 블록 사이에 끼어 들어가는 일이 구조적으로
    불가능하다. 대칭쌍(`mirror_pairs`) 처리는 `pack_floorplan()`과 동일 — 그룹화는 spine에만
    적용된다(mirror_pairs는 이미 그 자체로 "갈라지면 안 되는 쌍" 처리가 돼 있다).

    반환된 `FloorplanResult.placements`는 그룹 이름이 아니라 **원래의 개별 block 이름**으로
    키가 채워진다(그룹은 packing 중간 단계의 내부 표현일 뿐, 최종 결과에는 노출되지 않는다).

    **트레이드오프**: 그룹 단위로 묶었으므로 `pack_floorplan()`이 평평한 리스트로 할 수 있었던
    "그룹 경계를 넘나드는 미세한 빈틈 채우기"는 못 한다 — packing_density가 약간 낮아질 수
    있다. 이건 의도된 것이다: 회로 구조(어떤 block들이 기능적으로 묶여야 하는지)를 지키는 것이
    빈 공간을 1~2칸 더 줄이는 것보다 우선이다.

    `net_weights`(선택, `{group_or_pair_name: {other_name: weight}}`): `pack_floorplan()`과
    같은 개념이지만 키는 **그룹 이름**(spine_groups의 key, 예: "biasgen") 또는 **mirror_pairs의
    오른쪽 소자 이름**(예: "classab_p2") 기준이다 — 개별 물리 행 이름이 아니다(그룹으로
    묶였으므로 그룹 단위로만 위치를 조정할 수 있다).

    `sub_kinds`(선택, `{group_name: {block_name: kind}}`, 2026-07-27 신설): 특정 그룹 안의
    row를 같은 물리 diffusion/폴러리티 기준으로 나눠(예: CMFB의 P측 legs vs N측 legs), 그
    구분을 지킨 배치와 안 지킨 배치 중 실제로 더 촘촘한 쪽을 채택한다 — `pack_group_as_unit()`
    의 `sub_kind` 파라미터 참고. 이 그룹화는 spine_groups의 기능 그룹화(반드시 지켜야 하는
    제약)와 다르다 — polarity 구분은 **더 나은 결과를 낼 때만 채택되는 후보**다."""
    group_blocks, group_internal = [], {}
    for gname, blocks in spine_groups.items():
        gblock, internal = pack_group_as_unit(gname, blocks, gap=gap,
                                               sub_kind=(sub_kinds or {}).get(gname))
        group_blocks.append(gblock)
        group_internal[gname] = internal

    result = pack_floorplan(group_blocks, mirror_pairs, gap=gap, height_steps=height_steps,
                             transistor_sequences=transistor_sequences,
                             net_weights=net_weights, height_tolerance=height_tolerance,
                             width_tolerance=width_tolerance)

    final_placements = {}
    for name, p in result.placements.items():
        if name in group_internal:
            for bname, bp in group_internal[name].items():
                final_placements[bname] = PlacedBlock(bname, x=p.x + bp.x, y=p.y + bp.y,
                                                        width=bp.width, height=bp.height)
        else:
            final_placements[name] = p
    result.placements = final_placements
    return result


# ---------------------------------------------------------------------------
# 6.9) topology library JSON 오케스트레이션 레이어 (2026-07-28 신설) — 이 레이어는 I/O만
#      담당한다. 계산 로직은 한 줄도 새로 만들지 않는다 — 기존 함수를 그대로 호출한다.
#      정본: docs/02-design/features/analog-topology-json-library.design.md
# ---------------------------------------------------------------------------

def load_topology(json_path: str) -> tuple[list[Transistor], dict]:
    """topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

    meta = {"topology_name": str, "schema_version": str, "source": str|None,
            "symmetry": {"matching_pairs": [...], "dispositions": [...]},
            "compensation": {"function": str, "parameters": [...], ...} | None,
            "sizing_roles": {"theta": [...], "metrics": {...}, "objective": {...},
                              "constraints": [...]} | None,  # 배치 7-3d, 2026-07-31 신설
            "device_roles": {name: {"headroom_role":..., "gm_id_role":..., "L_role":...,
                              "vertical_stack_id":..., "vs":...}} | None,  # 배치 7-5, 2026-07-31 신설
            "netlist_sections_structured": {block_key: {"label":..., "confidence":...,
                              "devices": [...]}} | None,  # 세션20 신설, run_full_circuit_
                              # audit_from_topology()의 expected_counts 자동 구성용.
                              # `_netlist_sections_structured`(topology.json 최상위 키)가
                              # 없는 회로는 None -- 이 회로들엔 run_full_circuit_audit_
                              # from_topology()를 아직 쓸 수 없다(구조화 선행 필요).
            "ideal_sources": [{"name":..., "kind": "current_source"|"voltage_source",
                              "value_amp"|"value_volt":..., "implementable": False,
                              "terminals": [net1, net2]}, ...] | None,  # 세션28 신설,
                              # allocate_stack_headroom() singleton 우회의 물리적 근거
                              # 검증용(전류원 종단=전압 자유=예산 흡수, 전압원 종단=별개 계약)
            "_linked_files_loaded": [str, ...]}

    ⚠️ 반환된 `transistors`는 **connectivity만** 채워져 있다(name/kind/source/drain/gate) —
    `n_fingers`(기본값 1)/`finger_w`/`w`/`stack_id`는 아직 없다. 이건 사이징 산출물이라
    topology 단계엔 존재하지 않는다(2026-07-28 재설계, 사용자 지적 — 예전 버전은 `layout`
    필드에 특정 사이징에서만 유효한 row 분할을 저장하려다, 재사이징하면 그 값 자체가
    무의미해진다는 게 드러났다). 실제 layout은 `run_topology_pipeline()`에
    `sizing_overrides`(n_fingers/finger_w/w/stack_id 포함)를 넘겨야 계산된다.

    ⚠️⚠️ 2026-07-28 신설(사용자 지적, PRE-FLIGHT 사고8 재발 방지): 회로 하나가 여러
    topology JSON 파일로 쪼개져 있으면(예: 소자 수가 많아 stage별로 파일을 나눈 경우),
    각 파일의 최상위 `"linked_topology_files"`(같은 폴더 기준 상대경로 리스트, **자기 자신을
    뺀 나머지 형제 파일 전부**를 나열)를 따라가 **자동으로 전부 합쳐서** 반환한다 — 어느
    파일을 진입점으로 읽든 항상 회로 전체가 보인다. 이게 강제되는 이유: 사고8이 정확히
    "sub-block을 나눠서 find_matching_candidates()를 따로 돌리는 바람에 stage 경계를
    넘는 매칭 관계(예: bias-gen의 미러 레퍼런스와 신호 경로 소자가 같은 gate를 공유)를
    놓친" 사고였다 — topology JSON을 여러 파일로 쪼개는 것 자체는 막지 않되, **읽는 함수가
    항상 전체를 합쳐서 주면** 그 사고 유형이 파일이 여러 개여도 재발할 수 없다. 재귀는
    하지 않는다(형제 파일이 또 자기 형제를 나열하는 체인 구조는 지원 안 함 — 방사형으로,
    그룹 안의 모든 파일이 서로를 전부 나열해야 한다)."""
    def _read_one(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    data = _read_one(json_path)
    all_netlist = list(data["netlist"])
    all_matching_pairs = list(data["symmetry"]["matching_pairs"])
    all_dispositions = list(data["symmetry"].get("dispositions", []))
    all_device_roles = dict(data.get("device_roles") or {})
    all_netlist_sections_structured = dict(data.get("_netlist_sections_structured") or {})
    all_ideal_sources = list(data.get("ideal_sources") or [])

    linked = data.get("linked_topology_files") or []
    base_dir = os.path.dirname(os.path.abspath(json_path))
    for rel_path in linked:
        linked_data = _read_one(os.path.join(base_dir, rel_path))
        all_netlist.extend(linked_data["netlist"])
        all_matching_pairs.extend(linked_data["symmetry"]["matching_pairs"])
        all_dispositions.extend(linked_data["symmetry"].get("dispositions", []))
        all_device_roles.update(linked_data.get("device_roles") or {})
        all_netlist_sections_structured.update(linked_data.get("_netlist_sections_structured") or {})
        all_ideal_sources.extend(linked_data.get("ideal_sources") or [])

    transistors = [Transistor(**d) for d in all_netlist]

    # 2026-08-13(세션31, 사용자 지시) -- vertical_stack_id gap(예: two_stage_ota의
    # M1/M2/M6, resolve_stack_layout()이 audit_vertical_stack_id_vs_kcl()로 실제
    # 크래시시켜 발견)을 매번 손으로 채워 넣는 대신, 로드 시점에 자동으로 채운다.
    # propose_vertical_stack_id_gap_fill()(내부적으로 audit_vertical_stack_id_vs_kcl()/
    # _kcl_and_matching_edges() 재사용)이 만드는 제안 중 **충돌 없는 것만**(proposals,
    # 한 union 그룹 안에 declared 값이 정확히 하나뿐이라 사실상 확정적) 자동 반영 --
    # conflicts(서로 다른 declared 값이 섞인 경우, 자동으로 못 정함)는 그대로 두어
    # 기존 audit/크래시 경로가 여전히 사람 검토를 요구하게 둔다(조용히 추측하지 않음).
    # `_vertical_stack_id_autofilled`로 무엇이 자동 채움됐는지 투명하게 노출한다(이
    # 프로젝트 전역 원칙 -- 조용한 수정 금지, refine_differential_and_mirror_
    # relations()의 role_changes/net_class_changes와 같은 패턴).
    _vsid_forced_pairs = [tuple(p["names"]) for p in all_matching_pairs if p.get("current_forced")]
    _vsid_gap_fill = propose_vertical_stack_id_gap_fill(
        transistors, _vsid_forced_pairs, all_device_roles)
    for _name, _vsid in _vsid_gap_fill["proposals"].items():
        all_device_roles.setdefault(_name, {})["vertical_stack_id"] = _vsid

    # 2026-08-14(사용자 지시 -- 절대원칙 "만들면 반드시 배선하라", vsid 선례와 동일 패턴으로
    # 배선) -- symmetry.matching_pairs/device_roles(gm_id_role/L_role/headroom_role) 둘 다
    # propose_device_roles_gap_fill()의 **충돌 없는 제안만** 매 load 시점에 자동으로
    # 메모리상 병합한다(파일은 안 건드림 -- apply_device_roles_gap_fill()만 파일을 쓴다,
    # 그건 여전히 명시적으로 호출하는 authoring-time 도구).
    #
    # ⚠️ 처음엔 device_roles를 자동 병합에서 뺐었다(실측: 매칭 관계가 전혀 없는 고립 소자
    # 1개짜리 netlist에도 `gm_id_role="matching"`/`L_role="mirror"`가 근거 없이 붙었음) --
    # 근본원인(`_propose_gm_id_roles()`/`_propose_L_roles()`가 매칭 신호 없이도 기본값을
    # 채우던 것)을 실제로 고쳤다(두 함수 모두 구조 대칭 파트너가 확인된 소자만 값을 냄,
    # 이 docstring 상단 대신 그 두 함수 자신의 docstring에 정정 이력 기록). 이제 안전해서
    # device_roles도 vsid와 동일하게 자동 병합한다. `compensation.stage_devices` 소속
    # 소자에 `gm_id_role`을 채워도 안전하다는 건 `sizing_recipe.py`의
    # `_AUTHORITATIVE_GM_ID_SOURCES` 가드로 실측 검증됨(이 세션).
    _comp = data.get("compensation")
    _comp_stage_devices = [n for grp in (_comp or {}).get("stage_devices", []) for n in grp]
    # 2026-08-20(세션40) -- vds_match_vgs_of 5번째 소스가 "theta feed로 vds가 헤드룸보다
    # 먼저 정해지는 소자"(예: M4)를 걸러내려면 find_authoritative_sizing_devices()의 결과가
    # 필요하다 -- `data`(raw topology.json dict)가 이미 그 함수가 기대하는 "compensation"/
    # "sizing_roles" 키를 그대로 갖고 있어 재계산 없이 바로 넘길 수 있다.
    _droles_gap_fill = propose_device_roles_gap_fill(
        transistors, all_device_roles, all_matching_pairs,
        compensation_stage_devices=_comp_stage_devices,
        vds_theta_authoritative=find_authoritative_sizing_devices(data))
    # 2026-08-14 -- device_roles_proposals를 그대로 "_device_roles_autofilled"로 노출하면
    # 안 된다(실측으로 발견한 버그): propose_device_roles_gap_fill()의 conflict 검사는
    # "이미 declared된 값과 제안이 **다를 때만**" 걸러내므로, 이미 declared된 값과 제안이
    # **우연히 같으면** 그 필드도 그대로 proposal에 남는다 -- 그러면 이미 사람이 검토·확정한
    # 필드까지 "review 안 됨"으로 잘못 보고돼 require_device_roles_reviewed()가 불필요하게
    # 막는다(current_reuse_telescopic_ota의 M10/M11a/M11b 등 실측 재현). 실제로 **새로
    # 채워진**(파일에 없었던) 필드만 추적한다.
    _device_roles_autofilled = {}
    for _name, _proposal in _droles_gap_fill["device_roles_proposals"].items():
        _entry = all_device_roles.setdefault(_name, {})
        _newly_added = {}
        for _field, _value in _proposal.items():
            if _entry.get(_field) is None:
                _entry[_field] = _value
                _newly_added[_field] = _value
        if _newly_added:
            _device_roles_autofilled[_name] = _newly_added
    # 2026-08-14(사용자 지적으로 발견 -- "대칭적인 branch이면 branch 전류가 같아야 하는것
    # 아니야?" 계기로 current_forced 기본값을 True로 정정한 뒤, `sizing_recipe.py`의
    # matching_pairs L 전파 루프가 `current_forced` 값과 무관하게 **모든** 선언된 쌍에
    # 작동한다는 걸 재확인했다 -- 즉 review 안 된 매칭쌍을 메모리상으로만 자동 병합해도
    # 실제 sizing(L 값)에 영향을 줄 수 있다는 뜻이라, `differential`(순수 KCL, review
    # 불필요)만 자동 병합하고 나머지(`mirror`/`structural_symmetry`/층위1 폴백, 전부
    # `matching_sensitivity="ratio"`)는 review 게이트를 통과하기 전까지 메모리에도 안
    # 넣는다 -- `require_device_roles_reviewed()`의 Tier 구분(`find_unreviewed_matching_
    # pairs()`)과 정확히 같은 기준을 여기서도 적용해 일관성을 맞춘다.
    _droles_new_pairs = []
    _droles_needs_review_pairs = []
    _droles_existing_pair_keys = {frozenset(p["names"]) for p in all_matching_pairs}
    for _p in _droles_gap_fill["matching_pairs_proposals"]:
        _key = frozenset(_p["names"])
        if _key in _droles_existing_pair_keys:
            continue  # 이미 declared -- review 완료로 취급, 어느 목록에도 안 넣음
        if _p.get("matching_sensitivity") == "offset":
            all_matching_pairs.append(_p)
            _droles_existing_pair_keys.add(_key)
            _droles_new_pairs.append(_p)
        else:
            _droles_needs_review_pairs.append(_p)  # ratio -- 메모리에도 자동 병합 안 함

    meta = {
        "topology_name": data["topology_name"],
        "schema_version": data["schema_version"],
        "source": data.get("source"),
        "symmetry": {"matching_pairs": all_matching_pairs, "dispositions": all_dispositions},
        "compensation": data.get("compensation"),
        "sizing_roles": data.get("sizing_roles"),  # 배치 7-3d(§7.3.2 D), 2026-07-31 신설
        "device_roles": all_device_roles or None,  # 배치 7-5, 2026-07-31 신설
        "netlist_sections_structured": all_netlist_sections_structured or None,  # 세션20 신설
        # 2026-08-11(세션28 계속) 신설 -- passive_elements처럼 소자로 안 잡히는 "가짜" 소스
        # (bias-gen 최상단 레퍼런스 전류원 등)를 헤드룸 루프가 실제로 대조하려면 필요
        # (allocate_stack_headroom() singleton 우회의 ideal_sources 근거 검증용).
        "ideal_sources": all_ideal_sources or None,
        "_linked_files_loaded": linked,
        "_vertical_stack_id_autofilled": _vsid_gap_fill["proposals"] or None,
        "_vertical_stack_id_conflicts": _vsid_gap_fill["conflicts"] or None,
        "_matching_pairs_autofilled": _droles_new_pairs or None,
        # ratio(mirror/structural_symmetry/층위1 폴백) 제안 -- offset(differential)과 달리
        # review 전까지 all_matching_pairs에 자동 병합 안 됨(위 주석 참고). require_device_
        # roles_reviewed()/find_unreviewed_matching_pairs()가 이 필드로 review 필요 여부를 판단.
        "_matching_pairs_needs_review": _droles_needs_review_pairs or None,
        "_device_roles_autofilled": _device_roles_autofilled or None,
        # 충돌(이미 declared된 값과 다름) 때문에 자동 반영 안 되고 review만 필요한 항목 +
        # 층위1/2 candidate인데 아직 확정 못 한 것들(예: current_forced 세분화가 sizing_
        # roles/theta 정보 없이는 불가능한 경우) -- vsid의 conflicts와 같은 투명성 원칙.
        "_device_roles_gap_fill_review_needed": _droles_gap_fill["review_needed"] or None,
    }
    return transistors, meta


def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict,
                           floorplan_hints: dict | None = None,
                           cell_groups: dict | None = None) -> dict:
    """`load_topology()` -> `sizing_overrides`로 소자별 layout 필드(n_fingers/finger_w/w/
    stack_id — **필수**, 사이징+finger 배분이 끝난 뒤에만 이 함수를 의미 있게 호출할 수 있다)
    덮어쓰기 -> `check_finger_width_compatibility()`(§3.5, **세션18 배선** — W가 finger_w의
    정수배가 아니면 물리적으로 존재할 수 없는 요구라 여기서 즉시 `ValueError`, 아래 euler
    분석은 이 게이트를 통과해야만 의미가 있다) -> `split_into_stacks()`로 스택(=기본 물리
    행 후보) 구성 -> §1.6/§1.7이 정한 순서 그대로: 행별 Euler 유효성 -> `check_box_shape()`
    -> `audit_row_split()`(matching-safety, `symmetry.matching_pairs`의 kind 사용) ->
    `pack_floorplan_grouped()` -> `check_stick_diagram_coverage()`.

    `floorplan_hints`(선택): `{"spine_groups": {...}, "mirror_pairs": [...],
    "net_weights": {...}}` — `pack_floorplan_grouped()`에 그대로 전달할 그룹핑. 안 주면
    스택마다 자기 자신만 담긴 1:1 그룹으로 기본 처리한다(`{stack: [stack]}`).

    `cell_groups`(선택, `dict[str, list[str]] | None`, 배치 7-2/2026-07-31): `{cell명:
    [행(stack)명, ...]}` — `check_box_shape()`/`audit_row_split()`을 물리적으로 독립된 cell별로
    나눠 실행한다. `floorplan_hints.spine_groups`(물리 배치 인접성 제약,
    `pack_floorplan_grouped()` 전용)와는 **목적이 다르므로 별개 인자**다(§7.9 질문 1 결론) —
    같은 회로에서 두 파티션이 실제로 다를 수 있다. `cell_groups`를 명시적으로 안 주면
    `floorplan_hints.spine_groups`의 파티션을 그대로 fallback으로 재사용한다(둘 다 안 주면
    기존 동작 그대로: 전체 소자를 combined 단일 cell로 감사 — 하위호환 유지). `cell_groups`(또는
    fallback)가 있으면 반환값의 `box_shape`/`audit_row_split`은 `{cell명: Verdict}` dict가
    된다(`save_instance_json()`이 이미 두 형태를 모두 받는 것과 동일 패턴). cell별 감사에서
    `matching_pairs`는 두 소자 이름이 **모두** 그 cell에 속할 때만 그 cell의 감사에 포함한다 —
    한쪽만 속하면(다른 cell에 있으면) common-centroid 비교 자체가 무의미해지고, 걸러내지
    않으면 `audit_row_split()`이 그 소자를 찾지 못해 거짓 FAIL을 낸다(실측 확인됨).

    ⚠️ 이 함수는 matching-safety를 위한 **행 분할을 자동으로 탐색하지 않는다** — 스택 전체를
    그대로 물리 행 하나로 놓고 감사한다. `audit_row_split`이 FAIL이면(예: branch_symmetric
    쌍이 단일 행에서 common-centroid를 못 만족) 그건 이 파이프라인의 버그가 아니라 정직한
    결과다 — 호출자가 `search_stack_finger_w()`/`common_centroid_layout()`로 새 finger 배분을
    찾아 `sizing_overrides`를 조정한 뒤 다시 호출하는 것이 이 skill의 정상 워크플로우다
    (§1.6/§1.7의 피드백 루프와 동일한 패턴).

    ⚠️ `run_full_circuit_audit()`는 **의도적으로 포함하지 않는다** — 그 함수의
    `dispositions` 인자(각 matching/hub-merge 후보가 real_match인지 false_positive인지의
    판단)는 이 스키마가 구조적으로 자동 도출할 수 없는 정보다(사람/agent의 판단이 필요하다는
    게 이 함수 자신의 docstring에도 명시돼 있다). 완전한 회로 감사가 필요하면 호출자가
    `run_full_circuit_audit()`를 별도로 직접 호출할 것.

    ⚠️⚠️⚠️ `sizing_overrides`는 **topology의 모든 소자를 빠짐없이 포함해야 한다** —
    2026-07-28 실측 발견: 소자 하나를 빠뜨리면 `_dc_replace()`를 안 거쳐 `n_fingers=1`
    기본값 + `stack_id=None`으로 그대로 남는데, `split_into_stacks()`가 `stack_id`가 없는
    소자를 `(kind, "unspecified")` 폴백 그룹으로 **자동 흡수**해버려서(원래 의도된 동작)
    `check_stick_diagram_coverage()`가 "이름이 어딘가 있다"고 통과시켜버린다 — 즉 사실상
    사이징 안 된 소자가 `coverage.ok=True`인 채로 조용히 넘어간다(PRE-FLIGHT 사고27과
    똑같은 실패 유형이 이 함수 안에 그대로 남아있었다, `check_stick_diagram_coverage()`가
    이 경우를 잡아내지 못한다는 게 실측 확인됨). 그래서 이 함수는 **시작하자마자**
    `sizing_overrides`가 전체 소자를 커버하는지 확인하고, 하나라도 빠지면 나머지 계산을
    전혀 하지 않고 즉시 `ValueError`를 낸다.

    반환: {"transistors": list[Transistor](layout 필드까지 채워진 최종 netlist),
           "box_shape": BoxShapeVerdict 또는 {cell명: BoxShapeVerdict}(cell_groups/
           spine_groups fallback이 있을 때), "audit_row_split": AuditResult 또는
           {cell명: AuditResult}(위와 동일 조건), "floorplan": FloorplanResult,
           "coverage": dict}."""
    transistors, meta = load_topology(topology_json_path)

    missing_overrides = {t.name for t in transistors} - set(sizing_overrides.keys())
    if missing_overrides:
        raise ValueError(
            f"sizing_overrides가 다음 소자를 빠뜨렸다: {sorted(missing_overrides)} -- "
            "모든 소자는 sizing_overrides에 반드시 있어야 한다. 빠뜨리면 n_fingers=1 "
            "기본값+stack_id=None으로 조용히 처리되고, check_stick_diagram_coverage()는 "
            "그 소자가 폴백 그룹에 흡수돼 '존재'하므로 이 누락을 잡지 못한다 -- "
            "PRE-FLIGHT 사고27과 동일한 실패 유형(실측 확인됨)."
        )

    transistors = [_dc_replace(t, **sizing_overrides[t.name]) for t in transistors]

    # 세션18 -- check_finger_width_compatibility()(§3.5)는 원래 "euler 조건 분석보다
    # 먼저 통과해야 하는 선행 게이트"로 설계됐지만(Transistor.w/finger_w 필드 주석,
    # 위 함수 자신의 docstring 참고) 실제 파이프라인 어디에도 호출부가 없었다 --
    # assign_finger_geometry()가 만든 sizing_overrides는 w=n_fingers*finger_w로
    # 항상 정확히 나누어떨어지게 구성하므로 그 경로는 이 게이트에 절대 안 걸리지만,
    # 이 함수(run_topology_pipeline())는 호출자가 sizing_overrides를 손으로 직접
    # 구성해 넘기는 것도 허용한다(Transistor.n_fingers 필드 주석: "호출자가 직접
    # 정해서 넣는다") -- 그 경로에서 W/finger_w가 정수배가 아니면(Maloberti PDF의
    # 38um/8um=4.75 사례처럼 물리적으로 존재할 수 없는 요구) 지금까지는 조용히 넘어가
    # euler 분석 이하 전부가 잘못된 전제로 돌아갔다. 여기서 막는다.
    fw_verdict = check_finger_width_compatibility(transistors)
    if not fw_verdict.ok:
        detail = "; ".join(
            f"{i.transistor}: w={i.w}, finger_w={i.finger_w} -> {i.exact_ratio:.4f}개"
            f"(정수 아님, 가능한 값: {i.nearest_valid_w[0]:.6g} 또는 {i.nearest_valid_w[1]:.6g})"
            for i in fw_verdict.issues
        )
        raise ValueError(
            f"sizing_overrides의 W가 finger_w의 정수배가 아닌 소자가 있다(§3.5 divisibility "
            f"게이트, 물리적으로 존재할 수 없는 finger 개수를 요구하는 것과 같다): {detail}"
        )

    rows = split_into_stacks(transistors)  # {stack_id: [Transistor, ...]}

    pairs_meta = meta["symmetry"]["matching_pairs"]
    # audit_row_split()은 순수 2-tuple 쌍 계약이다 -- names가 2개보다 많은 그룹(기준 소자
    # 하나를 여러 소자가 미러하는 current_mirror)은 모든 쌍별 조합으로 펼친다(2026-08-01,
    # 3개짜리 그룹에서 첫 두 이름만 쓰던 실제 gap 수정).
    matching_pairs = [pair for p in pairs_meta for pair in itertools.combinations(p["names"], 2)]
    # 2026-08-05(세션10) L1 하드컷 -- pair_kinds(kind 문자열) 대신 pair_sensitivity(축C)를
    # topology.json에서 직접 읽는다. 축B(shares_node)는 이제 connectivity에서 항상 자동
    # 계산되므로(shares_diffusion_node()) 여기서 조립할 필요가 없다.
    pair_sensitivity = {pair: p["matching_sensitivity"] for p in pairs_meta
                         for pair in itertools.combinations(p["names"], 2)}

    hints = floorplan_hints or {}
    effective_cell_groups = cell_groups if cell_groups is not None else hints.get("spine_groups")

    if effective_cell_groups is None:
        box_shape = check_box_shape(rows)
        audit_row = audit_row_split(rows, matching_pairs=matching_pairs,
                                     pair_sensitivity=pair_sensitivity)
    else:
        box_shape = {}
        audit_row = {}
        for cell_name, row_names in effective_cell_groups.items():
            cell_rows = {rn: rows[rn] for rn in row_names if rn in rows}
            box_shape[cell_name] = check_box_shape(cell_rows)
            cell_device_names = {t.name for devs in cell_rows.values() for t in devs}
            cell_pairs = [(a, b) for (a, b) in matching_pairs
                          if a in cell_device_names and b in cell_device_names]
            cell_pair_sensitivity = {k: v for k, v in pair_sensitivity.items()
                                      if set(k) <= cell_device_names}
            audit_row[cell_name] = audit_row_split(cell_rows, matching_pairs=cell_pairs,
                                                    pair_sensitivity=cell_pair_sensitivity)

    # 2026-08-13(세션31 CO) -- rebuild_floorplan()으로 추출(동작 변화 없음, optimize_full_
    # circuit_budget()이 row_split/repair 이후 재호출할 수 있도록 재사용 가능하게 만든 것).
    floorplan = rebuild_floorplan(rows, hints)

    sized_names = {t.name for t in transistors}
    stick_diagram_devices = {name: [t.name for t in devs] for name, devs in rows.items()}
    coverage = check_stick_diagram_coverage(sized_names, stick_diagram_devices)

    return {
        "transistors": transistors,
        "box_shape": box_shape,
        "audit_row_split": audit_row,
        "floorplan": floorplan,
        "coverage": coverage,
    }


def run_full_circuit_audit_from_topology(topology_json_path: str,
                                           box_shape_checks: dict | None = None,
                                           row_width_tol: float = 1.5,
                                           accept_fail_blocks: set | None = None) -> AuditResult:
    """`run_full_circuit_audit()`(§1.6)의 자동 로더 -- topology.json 경로 하나만 주면
    `devices`/`expected_counts`/`dispositions`를 `load_topology()`가 이미 읽은 정보에서
    전부 자동으로 구성해 호출한다. 호출자가 connectivity를 별도 dict로 다시 손타이핑하거나
    (사고9 net-이름 드리프트의 근본원인 재발) 이미 topology.json `symmetry.dispositions`에
    적힌 판단을 다시 옮겨적을 필요가 없다(세션20, `.ai/context.md` 참고).

    ⚠️ 이 함수가 새로 **판단**하는 건 없다 -- `expected_counts`는 `_netlist_sections_
    structured`(§0, prose `_netlist_sections`를 기계적으로 구조화한 필드)에서, `dispositions`
    는 `symmetry.dispositions`에서 **이미 기록된** 값을 형식만 변환해 재사용한다. 두 필드가
    비어 있으면(아직 이 스키마로 갱신 안 된 회로) `run_full_circuit_audit()`의 게이트 자체가
    무의미해지므로(빈 expected_counts는 "선언 없음"과 같다) 조용히 넘어가지 않고
    `ValueError`를 낸다.

    `box_shape_checks`/`row_width_tol`/`accept_fail_blocks`는 사이징/레이아웃 이후에만 나오는
    정보라 topology.json에 없다 -- `run_full_circuit_audit()`에 그대로 전달한다(호출자가
    `run_topology_pipeline()`류의 반환값에서 직접 뽑아 넘길 것, 이 함수가 자동 변환하지
    않는다 -- box_shape의 형태가 `cell_groups` 유무로 달라져 자동 변환이 오히려 조용한
    오판을 낼 수 있다)."""
    transistors, meta = load_topology(topology_json_path)
    structured = meta.get("netlist_sections_structured")
    if not structured:
        raise ValueError(
            f"{topology_json_path}에 _netlist_sections_structured가 없다 -- "
            "run_full_circuit_audit_from_topology()는 expected_counts를 자동 도출할 수 없다"
            "(prose _netlist_sections를 구조화된 dict로 먼저 변환할 것, 세션20 참고).")

    block_of = {}
    expected_counts = {}
    for block_key, info in structured.items():
        expected_counts[block_key] = len(info["devices"])
        for name in info["devices"]:
            block_of[name] = block_key

    devices = {}
    for t in transistors:
        block = block_of.get(t.name)
        if block is None:
            raise ValueError(
                f"{t.name}이 netlist에는 있지만 _netlist_sections_structured 어느 블록에도 "
                "없다 -- 구조화가 netlist 전수를 커버하지 못한다(불일치, 재확인 필요).")
        devices[t.name] = (t.kind, t.source, t.drain, t.gate, block)

    dispositions = {
        (d["tag"], d["kind"], d["key"]): (d["category"], d["reason"])
        for d in meta["symmetry"]["dispositions"]
    }

    return run_full_circuit_audit(devices, expected_counts, dispositions,
                                    box_shape_checks=box_shape_checks, row_width_tol=row_width_tol,
                                    accept_fail_blocks=accept_fail_blocks)


def _box_shape_json(bs):
    """`BoxShapeVerdict` 하나(단일-cell 회로, `run_topology_pipeline()`의 기본 가정) 또는
    `{cell_name: BoxShapeVerdict}`(물리적으로 독립된 cell이 여러 개인 회로 — 각 cell은 자기
    자신의 aspect-ratio 제약만 가지므로 cell을 넘나드는 단일 combined ratio는 의미가 없다)를
    둘 다 받는다. 2026-07-29 확장: `current_reuse_telescopic_ota` 리포트처럼 물리적으로
    독립된 cell 3개(core_signal/bias_tail/stage2_output)를 갖는 회로에서 실측 필요성 확인."""
    if isinstance(bs, dict):
        return {name: _box_shape_json(v) for name, v in bs.items()}
    return {"ok": bs.ok, "rectangular": bs.rectangular, "elongation_ok": bs.elongation_ok,
            "row_widths": bs.row_widths, "row_heights": bs.row_heights,
            "total_width_m": bs.total_width_m, "total_height_m": bs.total_height_m,
            "width_ratio": bs.width_ratio, "elongation": bs.elongation,
            "approx": bs.approx, "message": bs.message}


def _audit_result_json(ar):
    """`AuditResult` 하나 또는 `{cell_name: AuditResult}` 둘 다 받는다(`_box_shape_json()`과
    동일한 이유 — `audit_row_split()`은 cell 하나당 한 번씩 호출되는 게 정상 사용법이다)."""
    if isinstance(ar, dict):
        return {name: _audit_result_json(v) for name, v in ar.items()}
    return {"ok": ar.ok, "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail}
                                     for c in ar.checks]}


def save_instance_json(path: str, topology_json_path: str, sizing_results: dict,
                        pipeline_result: dict) -> None:
    """instance-output JSON 작성 — `pipeline_result`(`run_topology_pipeline()`의 반환값, 또는
    독립된 물리 cell이 여러 개인 회로라면 §6.9 아래 문단처럼 직접 조립한 동일 스키마의 dict)를
    손대지 않고 그대로 옮겨 쓴다(§1 표 5번 원칙: 함수 반환값 그대로, 손으로 축약/재구성 금지).
    `sizing_results`는 `{name: {"W":..., "L":..., "ID":..., "gm":..., "gm_id":...}}` 형태를
    기대한다(sizing_recipe.py의 SizingResult 필드명 그대로).

    `box_shape`/`audit_row_split`는 단일 `BoxShapeVerdict`/`AuditResult` 또는 `{cell_name: ...}`
    dict 둘 다 받는다 — 물리적으로 독립된 cell이 여러 개면(예: 이 회로처럼 core_signal/bias_tail/
    stage2_output 3개 cell이 서로 다른 aspect-ratio 제약을 갖는 경우) cell별로 별도 호출한 결과를
    그대로 dict로 넘길 것(cell을 넘나드는 단일 combined 값은 의미 없는 숫자가 된다).
    `pipeline_result`에 `scope_note`(str)를 선택적으로 넣으면 그대로 옮겨 쓴다 — 이 instance가
    전체 회로가 아니라 일부만 감사/배치했을 때 그 범위를 정직하게 밝히는 용도(§1.5 원칙과 동일한
    이유로, 부분 스코프를 "완료"인 것처럼 보이게 만들지 않기 위함)."""
    data = {
        "schema_version": "2.0",
        "topology_ref": topology_json_path,
        "sizing": sizing_results,
        "netlist": [_dc_asdict(t) for t in pipeline_result["transistors"]],
        "floorplan": {
            "placements": {name: {"x": p.x, "y": p.y, "width": p.width, "height": p.height}
                           for name, p in pipeline_result["floorplan"].placements.items()},
            "bbox": {"width": pipeline_result["floorplan"].bbox_width,
                     "height": pipeline_result["floorplan"].bbox_height},
            "aspect_ratio": pipeline_result["floorplan"].aspect_ratio,
            "packing_density": pipeline_result["floorplan"].packing_density,
        },
        "box_shape": _box_shape_json(pipeline_result["box_shape"]),
        "audit_row_split": _audit_result_json(pipeline_result["audit_row_split"]),
        "coverage": {"ok": pipeline_result["coverage"].ok,
                     "missing": sorted(pipeline_result["coverage"].missing)},
    }
    if pipeline_result.get("scope_note"):
        data["scope_note"] = pipeline_result["scope_note"]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 7) Self-test — python stick_diagram.py로 바로 확인 가능
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== Test 1a: pptx slide 2의 원본 연결 그래프 (finger 1개씩, node 1-2-3-4 체인) ===")
    chain_1finger = [
        Transistor("M1", "nmos", source="1", drain="2", n_fingers=1, stack_id="row"),
        Transistor("M2", "nmos", source="2", drain="3", n_fingers=1, stack_id="row"),
        Transistor("M3", "nmos", source="3", drain="4", n_fingers=1, stack_id="row"),
    ]
    for stack_id, res in build_stick_diagram(chain_1finger).items():
        print(render_stick_diagram(res))
        print(f"  (odd_nodes={res.odd_nodes} — 홀수차수 노드가 정확히 2개(1, 4)라 open path여야 함)")

    print()
    print("=== Test 1b: 실제 finger 수(M1=4, M2=2, M3=4)를 반영하면 모든 노드가 짝수차수 → 닫힌 회로 ===")
    chain_sized = [
        Transistor("M1", "nmos", source="1", drain="2", n_fingers=4, stack_id="row"),
        Transistor("M2", "nmos", source="2", drain="3", n_fingers=2, stack_id="row"),
        Transistor("M3", "nmos", source="3", drain="4", n_fingers=4, stack_id="row"),
    ]
    for stack_id, res in build_stick_diagram(chain_sized).items():
        print(render_stick_diagram(res))
        print(f"  (odd_nodes={res.odd_nodes} — 비어있으면 closed circuit, start=end)")

    print()
    print("=== Test 2: 홀수차수 노드 4개인 예(한붓그리기 불가능 + 조정 후보 확인) ===")
    disjoint = [
        Transistor("MA", "nmos", source="a", drain="b", n_fingers=1, stack_id="row2"),
        Transistor("MB", "nmos", source="b", drain="c", n_fingers=1, stack_id="row2"),
        Transistor("MC", "nmos", source="c", drain="d", n_fingers=1, stack_id="row2"),
        Transistor("MD", "nmos", source="d", drain="e", n_fingers=1, stack_id="row2"),
        Transistor("ME", "nmos", source="e", drain="f", n_fingers=1, stack_id="row2"),
        # b-e를 직접 잇는 별도 branch를 추가 → b, e의 차수가 2에서 3(홀수)로 바뀌어
        # 홀수차수 노드가 a, b, e, f 총 4개로 늘어나는 상황을 만든다.
        Transistor("MX", "nmos", source="b", drain="e", n_fingers=1, stack_id="row2"),
    ]
    for stack_id, res in build_stick_diagram(disjoint).items():
        print(render_stick_diagram(res))

    print()
    print("=== Test 3: 극성이 다르면 자동으로 별도 stack으로 분리되는지 확인 ===")
    mixed = [
        Transistor("MP1", "pmos", source="vdd", drain="x", n_fingers=2, finger_w=5.0),
        Transistor("MP2", "pmos", source="x", drain="vdd", n_fingers=2, finger_w=5.0),
        Transistor("MN1", "nmos", source="gnd", drain="y", n_fingers=2, finger_w=3.0),
        Transistor("MN2", "nmos", source="y", drain="gnd", n_fingers=2, finger_w=3.0),
    ]
    stacks = split_into_stacks(mixed)
    print(f"  자동 분할된 stack 수: {len(stacks)} (기대: 2 — pmos 1개, nmos 1개)")
    for stack_id, res in build_stick_diagram(mixed).items():
        print(render_stick_diagram(res))

    print()
    print("=== Test 4: Folded Cascode(PDF p.34~p.38) 실제 넷리스트 — pptx 원본 정답과 대조 ===")
    # pptx 원본 답(순수 node 시퀀스만으로 §6.1 "결과 0"에서 이미 검증됨): top은 홀수노드
    # {X,Y}인 open path, mid는 홀수노드 없는 closed circuit(시작점은 아무 node나 가능),
    # bot은 홀수노드 {outA,outB}인 open path.
    expected_odd_nodes = {"top": {"X", "Y"}, "mid": set(), "bot": {"outA", "outB"}}
    for stack_id, res in build_stick_diagram(folded_cascode_example()).items():
        print(render_stick_diagram(res))
        got_odd = set(res.odd_nodes)
        want_odd = expected_odd_nodes[stack_id]
        print(f"  홀수차수 노드={got_odd or '{}'}, pptx 정답 기준 기대값={want_odd or '{}'} "
              f"-> {'일치' if got_odd == want_odd else '불일치'}")

    print()
    print("=== Test 5: PDF p.14 'Axis of Symmetries' — folded cascode top 행의 실제 대칭성 검증 ===")
    # pptx 원본 finger 순서(MP,M3,M4,M5,M6 row) — 중앙 수직축 기준 좌우대칭 구조인지 확인.
    top_row_labels = list("555555344PP334666666")
    pair_map = {"5": "6", "6": "5", "3": "4", "4": "3", "P": "P"}
    is_symmetric = check_mirror_symmetry(top_row_labels, pair_map)
    print(f"  원본 시퀀스: {''.join(top_row_labels)}")
    print(f"  축대칭(5<->6, 3<->4, P<->P) 만족: {is_symmetric.ok}")
    rebuilt = build_mirror_symmetric_pattern(list("555555344P"), pair_map)
    print(f"  왼쪽 절반만으로 재구성: {''.join(rebuilt)} -> 원본과 일치: {rebuilt == top_row_labels}")

    print()
    print("=== Test 5.5: mirror_symmetric_trail() — 세션11 L3(D), 실제 회로 2개로 교차검증 ===")
    print("  [사례1: folded_cascode top row — MP(self-pair,2f)/M3-M4(3f)/M5-M6(6f)]")
    top_group = [t for t in folded_cascode_example() if t.stack_id == "top"]
    top_pairs = [("M3", "M4"), ("M5", "M6")]
    mirrored_top = mirror_symmetric_trail(top_group, top_pairs)
    print(f"  성공: {mirrored_top is not None}")
    if mirrored_top is not None:
        seq = mirrored_top["transistor_sequence"]
        pm = {"M3": "M4", "M4": "M3", "M5": "M6", "M6": "M5", "MP": "MP"}
        wv = check_walk_sequence(seq, top_group)
        print(f"  전체 그래프에서 유효한 walk: {wv.ok} (finger_count_mismatch={wv.finger_count_mismatch})")
        print(f"  거울대칭 만족: {check_mirror_symmetry(seq, pm).ok}")
        print(f"  구성된 시퀀스: {seq}")

    print("  [사례2: current_reuse_telescopic_ota 그룹 M8 — M8/M17, M9a/M18a(둘 다 1:1, self-pair 없음)]")
    m8_group = [
        Transistor("M8", "pmos", source="vdd", drain="Vg15", gate="Vbias1", n_fingers=1, stack_id="m8"),
        Transistor("M17", "pmos", source="vdd", drain="Vg25", gate="Vbias1", n_fingers=1, stack_id="m8"),
        Transistor("M9a", "pmos", source="Vg15", drain="Vop1", gate="N11b", n_fingers=1, stack_id="m8"),
        Transistor("M18a", "pmos", source="Vg25", drain="Vom1", gate="N20b", n_fingers=1, stack_id="m8"),
    ]
    m8_pairs = [("M8", "M17"), ("M9a", "M18a")]
    mirrored_m8 = mirror_symmetric_trail(m8_group, m8_pairs)
    print(f"  성공: {mirrored_m8 is not None}")
    if mirrored_m8 is not None:
        seq2 = mirrored_m8["transistor_sequence"]
        pm2 = {"M8": "M17", "M17": "M8", "M9a": "M18a", "M18a": "M9a"}
        wv2 = check_walk_sequence(seq2, m8_group)
        print(f"  전체 그래프에서 유효한 walk: {wv2.ok} (finger_count_mismatch={wv2.finger_count_mismatch})")
        print(f"  거울대칭 만족: {check_mirror_symmetry(seq2, pm2).ok}")
        print(f"  구성된 시퀀스: {seq2} (손 검증한 [M9a,M8,M17,M18a]와 일치: {seq2 == ['M9a', 'M8', 'M17', 'M18a']})")

    print("  [사례3(음성 대조): build_stick_diagram()에 matching_pairs를 안 주면 기존 동작과 완전히 동일해야 함]")
    old_style = build_stick_diagram(top_group)
    new_style_no_pairs = build_stick_diagram(top_group, matching_pairs=None)
    print(f"  matching_pairs=None -> method={old_style['top'].method} vs {new_style_no_pairs['top'].method} "
          f"(둘 다 'graph'여야 하위호환): {old_style['top'].method == new_style_no_pairs['top'].method == 'graph'}")
    print(f"  시퀀스도 완전히 동일: {old_style['top'].transistor_sequence == new_style_no_pairs['top'].transistor_sequence}")

    print()
    print("=== Test 5.6: suggest_pair_finger_adjustments() + mirror_symmetric_trail() 다리 지원")
    print("    — 세션12, current_reuse_telescopic_ota M3a 그룹(11소자) 실측 재현 ===")
    # M3a 그룹(geometry_colocation_union() 실측, .ai/context.md 세션11 B-4/세션12) --
    # 매칭쌍 4개(M4a/M4b offset, M3a/M3b ratio, M10/M19 ratio, M9b/M18b ratio) +
    # 홀수 self-pair 3개(M5, M63, M64 -- gnd-M5-Vy-M63-N64_63-M64-Vbias3 사슬).
    m3a_group = [
        Transistor("M3a", "nmos", source="N3a4a", drain="Vom1", gate="Vbias3", n_fingers=1, stack_id="m3a"),
        Transistor("M3b", "nmos", source="N3b4b", drain="Vop1", gate="Vbias3", n_fingers=1, stack_id="m3a"),
        Transistor("M4a", "nmos", source="Vy", drain="N3a4a", gate="Vip", n_fingers=1, stack_id="m3a"),
        Transistor("M4b", "nmos", source="Vy", drain="N3b4b", gate="Vim", n_fingers=1, stack_id="m3a"),
        Transistor("M5", "nmos", source="gnd", drain="Vy", gate="Vbias4", n_fingers=1, stack_id="m3a"),
        Transistor("M9b", "nmos", source="Vop1", drain="Vg15", gate="N14a14b", n_fingers=1, stack_id="m3a"),
        Transistor("M10", "nmos", source="gnd", drain="Vop1", gate="Vbias4", n_fingers=1, stack_id="m3a"),
        Transistor("M18b", "nmos", source="Vom1", drain="Vg25", gate="N24b23a", n_fingers=1, stack_id="m3a"),
        Transistor("M19", "nmos", source="gnd", drain="Vom1", gate="Vbias4", n_fingers=1, stack_id="m3a"),
        Transistor("M64", "nmos", source="N64_63", drain="Vbias3", gate="Vbias3", n_fingers=1, stack_id="m3a"),
        Transistor("M63", "nmos", source="Vy", drain="N64_63", gate="Vbias3", n_fingers=1, stack_id="m3a"),
    ]
    m3a_pairs = [("M4a", "M4b"), ("M3a", "M3b"), ("M10", "M19"), ("M9b", "M18b")]

    print("  [1. 조정 전: build_graph()+check_euler_condition() 그대로면 홀수차수 6개(다중 trail 필요)]")
    baseline_odd = check_euler_condition(build_graph(m3a_group)).odd_nodes
    print(f"  홀수차수 노드: {sorted(baseline_odd)} ({len(baseline_odd)}개)")

    print("  [2. suggest_pair_finger_adjustments() — 매칭쌍 단위 제안 1순위가 M9b/M18b 동시 +1인지]")
    suggestions = suggest_pair_finger_adjustments(m3a_group, m3a_pairs)
    top = suggestions[0]
    print(f"  1순위 제안: {top}")
    print(f"  M9b/M18b 쌍을 +1 -> 홀수 6->2개로 최대 개선: "
          f"{set(top.names) == {'M9b', 'M18b'} and top.delta_fingers == 1 and top.resulting_odd_count == 2}")

    m3a_adjusted = [_dc_replace(t, n_fingers=t.n_fingers + 1) if t.name in top.names else t
                    for t in m3a_group]

    print("  [3. 조정 후: mirror_symmetric_trail()이 대표 조합 탐색 + 홀수 self-pair 다리로 11소자 전체를 구성하는지]")
    m3a_result = mirror_symmetric_trail(m3a_adjusted, m3a_pairs)
    print(f"  성공: {m3a_result is not None}")
    if m3a_result is not None:
        seq3 = m3a_result["transistor_sequence"]
        wv3 = check_walk_sequence(seq3, m3a_adjusted)
        print(f"  전체 그래프에서 유효한 walk: {wv3.ok} (finger_count_mismatch={wv3.finger_count_mismatch})")
        print(f"  총 finger 수: {len(seq3)} (기대: {sum(t.n_fingers for t in m3a_adjusted)})")
        print(f"  구성된 시퀀스: {seq3}")

    print("  [4(회귀 대조). 조정 없이 원본 그대로면 여전히 None(폴백)이어야 함 -- 다리만으로는 안 풀림]")
    m3a_unadjusted_result = mirror_symmetric_trail(m3a_group, m3a_pairs)
    print(f"  성공: {m3a_unadjusted_result} (None이어야 정상 -- 핑거조정과 다리 지원 둘 다 있어야 풀림)")

    print()
    print("=== Test 6: matching 그룹 자동 탐지 — folded cascode 넷리스트에서 전류거울/차동쌍 추출 ===")
    found = find_matching_candidates(folded_cascode_example())
    print("  current_mirror 후보:")
    for (kind, gate), group in found["current_mirror"].items():
        print(f"    gate={gate}({kind}): {[t.name for t in group]}")
    print("  diff_pair 후보:")
    for (kind, source), group in found["diff_pair"].items():
        print(f"    source={source}({kind}): {[t.name for t in group]}")
    expected_mirrors = {frozenset(["M3", "M4"]), frozenset(["M5", "M6"]),
                        frozenset(["M7", "M8"]), frozenset(["M9", "M10"])}
    got_mirrors = {frozenset(t.name for t in g) for g in found["current_mirror"].values()}
    print(f"  기대한 4개 전류거울/캐스코드쌍과 일치: {got_mirrors == expected_mirrors}")
    got_diffpair = {frozenset(t.name for t in g) for g in found["diff_pair"].values()}
    print(f"  차동쌍 M1/M2 탐지: {frozenset(['M1', 'M2']) in got_diffpair}")

    print()
    print("=== Test 7: unit cell 사이징 후보 탐색 — nominal W 근방에서 정수배 후보 생성 ===")
    # 예: gm/ID가 W=37um을 요구하는데 그 stack의 unit cell 후보가 8um 또는 10um뿐이라면?
    top5 = search_unit_cell_sizing(nominal_w=37.0, candidate_unit_widths=[8.0, 10.0])[:3]
    for c in top5:
        print(f"  unit_w={c.unit_w}um x {c.n_fingers} = {c.w}um (상대오차 {c.rel_error:.1%})")

    print()
    print("=== Test 8: 2-Stage OTA(PDF p.28~p.33) 실제 넷리스트 — 3개 stack 전부 닫힌 회로 확인 ===")
    for stack_id, res in build_stick_diagram(two_stage_ota_example()).items():
        print(render_stick_diagram(res))
        print(f"  홀수차수 노드={set(res.odd_nodes) or '{}'} -> "
              f"{'닫힌 회로(기대대로)' if not res.odd_nodes else '경로(예상과 다름)'}")

    print()
    print("=== Test 9: 홀수 개수 매칭쌍의 교차 대칭 배치 — folded cascode M9/M10(각 3개) 실제 사례 ===")
    bottom_full = list("777779xxoo99nno88888")
    bottom_pair_map = {"7": "8", "8": "7", "9": "o", "o": "9", "x": "n", "n": "x"}
    print(f"  원본 시퀀스 전체 축대칭: {check_mirror_symmetry(bottom_full, bottom_pair_map).ok}")
    splits = find_interleaved_symmetric_splits(count_a=3, count_b=3)
    print(f"  M9/M10(각 3개) 가능한 대칭 분할 후보: {splits}")
    actual = (bottom_full[:10].count("9"), bottom_full[10:].count("9"),
              bottom_full[:10].count("o"), bottom_full[10:].count("o"))
    print(f"  실제 pptx가 채택한 분할(M9좌,M9우,M10좌,M10우): {actual} -> 후보 목록에 포함: {actual in splits}")
    print(f"  '최대한 섞는다' 원칙에 따른 1순위(최선) 추천: {splits[0]} -> 실제 채택값과 일치: {splits[0] == actual}")

    print()
    print("=== Test 10: §8 box-shape 탐색 — Intrinsic Gain Stage 예제(N=15um 1소자 vs P=80+80um 2소자) ===")
    print("  기존 방식(두 stack 모두 finger_w=5um 고정): nstack=3개, pstack=32개 → 10.7:1, 'ㄱ'자 비정상 셀")
    pstack_candidates = search_stack_finger_w({"M2": 80.0, "M2b": 80.0}, target_row_fingers=8)
    print(f"  pstack(M2=M2b=80um) 후보 중 상위 3개: {pstack_candidates[:3]}")
    best_p = pstack_candidates[0]
    nstack_candidates = search_stack_finger_w({"M1": 15.0}, target_row_fingers=best_p.total_row_fingers)
    print(f"  nstack(M1=15um) 후보 중 상위 3개: {nstack_candidates[:3]}")
    best_n = nstack_candidates[0]
    print(f"  채택: pstack finger_w={best_p.finger_w}um(총 {best_p.total_row_fingers}개), "
          f"nstack finger_w={best_n.finger_w}um(총 {best_n.total_row_fingers}개) "
          f"-> {best_n.total_row_fingers}:{best_p.total_row_fingers} 거의 정사각형 box")

    print()
    print("=== Test 11: §2.7 2D common-centroid 표 기반 경로 — M2/M2b(전류거울, 4:4) ===")
    print("  M2/M2b는 1행만으로도 y방향 gradient는 못 잡는다 — ABBA/BAAB 2행으로 그것까지")
    print("  상쇄한다. 2026-07-24 세 번째 정정: ABBA/BAAB는 추가 metal layer 없이도 실제로")
    print("  1개 layer로 실현 가능하다(직접 검증됨) — 표의 모든 pattern이 그런 건 아니라서")
    print("  (예: ABA/BAB는 불가능) 이 함수가 이제 반환 전 각 행을 직접 검증한다.")
    print("  (2026-07-28 4차: 옛 common_centroid_layout(pattern_key=...)는 common_centroid_")
    print("  layout_nway()에 완전히 흡수돼 제거됨 — 내부 헬퍼 _common_centroid_from_pattern_")
    print("  table()을 직접 검증하고, nway의 N=2 비율 자동 dispatch도 아래 Test 12.5에서 확인)")
    cc = _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                              count_a=4, count_b=4, pattern_key=("ABBA", "BAAB"))
    print(f"  pattern={cc['pattern']} repeat={cc['repeat']}")
    for i, row in enumerate(cc["rows"]):
        print(f"  row{i}: {row['transistor_sequence']}  node_sequence: {row['node_sequence']}")
    print(f"  검증: total_a(M2)={cc['total_a']}, total_b(M2b)={cc['total_b']} (둘 다 4여야 함) "
          f"-> {'OK' if cc['total_a'] == cc['total_b'] == 4 else 'FAIL'}")
    print("  (node_sequence가 채워져 있다는 것 자체가 각 행이 1개 layer로 실현 가능한 오일러")
    print("  경로임을 이 함수가 이미 검증했다는 뜻이다 — 실패했다면 ValueError가 났을 것.)")
    print("  위/아래 두 행이 서로 point-symmetric(common-centroid)해서 1D interdigitation보다")
    print("  고차 gradient 잔여 mismatch를 더 줄인다(실측: 1D~0.04% vs 2D~0.02%, §2.7 인용 문헌).")
    print("  대조: 'ABA'/'BAB'는 hub-leaf 구조로 1개 layer 실현이 불가능한 패턴이다(직접 검증됨)")
    print("  — 이 함수가 그걸 걸러내는지 확인:")
    try:
        _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                             count_a=6, count_b=6, pattern_key=("ABA", "BAB"))
        print("  FAIL: ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"  OK: 예상대로 ValueError -> {e}")
    print("  대조 2: 표에는 3-소자 패턴(ABCCBA/CBAABC)도 있지만 이 함수는 2-소자 전용 —")
    print("  KeyError가 아니라 명확한 ValueError로 거부하는지 확인(2026-07-28 병합 중 발견/수정):")
    try:
        _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                             count_a=6, count_b=6, pattern_key=("ABCCBA", "CBAABC"))
        print("  FAIL: ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"  OK: 예상대로 ValueError(명확한 메시지) -> {e}")

    print()
    print("=== Test 12: common_centroid_layout() 회전 경로 — 홀수 개수(M1/M2 차동쌍 9:9)도")
    print("  실제 오일러 trail 기반 2행 ===")
    print("  표 기반 경로는 COMMON_CENTROID_PATTERNS의 정해진 repeat만 지원해 홀수를 못")
    print("  다룬다 — Example 2의 M1/M2(각 9개, 홀수)는 §2.5.4 비대칭 분할을 2행으로 확장한")
    print("  회전 경로(_common_centroid_nway_exact, pattern_key 없음)로 처리해야 한다.")
    print("  2026-07-24 두 번째 수정: row1을 round-robin으로 손으로 섞던 것에서, hub-leaf")
    print("  쌍(tail 공유)의 실제 build_graph()+hierholzer()로 계산하도록 바꿨다 — 매 finger")
    print("  완전 1:1 교대(ABAB...)는 hub-leaf 구조에서 그래프 이론적으로 불가능하다(§2.5.6).")
    splits99 = find_interleaved_symmetric_splits(9, 9)
    print(f"  9:9 대칭 분할 후보(상위3): {splits99[:3]}")
    cc2 = common_centroid_layout([
        Transistor("M1", "nmos", source="tail", drain="d1", n_fingers=9),
        Transistor("M2", "nmos", source="tail", drain="d2", n_fingers=9),
    ])
    print(f"  method={cc2['method']} residual={cc2['residual']} (회전 경로여야 함, 표 대상 아님)")
    assert cc2["method"] == "rotation_exact" and cc2["residual"] == 0.0
    for i, row in enumerate(cc2["rows"]):
        print(f"  row{i}: {row['transistor_sequence']}")
        print(f"    node_sequence: {row['node_sequence']}")

    print()
    print("=== Test 12.5: common_centroid_layout() — 대칭(1:1)에서 표/회전 두 경로가")
    print("  실제로 같은 패턴을 내는지 + 비율(2:1)에서 표 기반 흡수(pattern_table)가 회전보다")
    print("  나은지 실측(2026-07-28: 옛 common_centroid_layout()의 두 경로를 흡수·통합) ===")
    cc_table = _common_centroid_from_pattern_table("M2", "out", "M2b", "bias", hub_net="vdd",
                                                    count_a=4, count_b=4, pattern_key=("ABBA", "BAAB"))
    cc_graph_nway = common_centroid_layout([
        Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=4),
        Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=4),
    ])
    table_rows = [r["transistor_sequence"] for r in cc_table["rows"]]
    graph_rows = [row["transistor_sequence"] for row in cc_graph_nway["rows"]]
    same_set = {tuple(r) for r in table_rows} == {tuple(r) for r in graph_rows}
    print(f"  표 경로 rows: {table_rows}")
    print(f"  nway 회전 경로(method={cc_graph_nway['method']}) rows: {graph_rows}")
    print(f"  -> 두 경로가 (행 순서 무관) 같은 물리 패턴 집합인가: {'OK' if same_set else 'FAIL'}")
    assert same_set
    print("  대조: pattern_key로만 가능한 비율(2:1) 패턴 — nway가 이제 자동으로 표를 찾아")
    print("  흡수하는지 확인(2026-07-28 4차, 사용자 요청 '표 기반 경로도 nway에 흡수'):")
    cc_ratio_nway = common_centroid_layout([
        Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=4),
        Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=2),
    ])
    print(f"  count_a=4,count_b=2 -> method={cc_ratio_nway['method']}, "
          f"residual={cc_ratio_nway['residual']}, "
          f"rows={[row['transistor_sequence'] for row in cc_ratio_nway['rows']]}")
    assert cc_ratio_nway["method"] == "pattern_table" and cc_ratio_nway["residual"] == 0.0, (
        f"2:1 비율인데 표 기반 흡수(pattern_table)로 안 갔다 -- 회귀: {cc_ratio_nway}"
    )
    print("  OK: nway가 표 기반 비율 패턴을 자동으로 찾아 residual=0 달성")
    print("  (대조: 탐색 경로만 썼다면 residual=0.75까지 나왔음을 실측 확인했었다 —")
    print("  탐색 경로는 회전/swap 후보를 못 만들어 표만큼 못한다)")

    print()
    print("=== Test 12.6: interdigitate_layout() — common_centroid_layout()와 동급으로 재설계")
    print("  (내부 검증 + crossover 폴백, dict 반환) — 사용자 요청, 2026-07-28 5차 ===")
    r_base = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=2),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=2),
    ], base="AB", repeat=2)
    print(f"  base='AB' repeat=2, M3=M4=2 -> method={r_base['method']}, "
          f"rows={[row['transistor_sequence'] for row in r_base['rows']]}")
    assert r_base["method"] == "pattern_table" and r_base["crossover_count"] == 0
    assert r_base["rows"][0]["transistor_sequence"] == ["M3", "M4", "M4", "M3"]
    print("  OK: 표에 정확히 맞는 repeat -> method=pattern_table, crossover 0")

    r_ratio = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=3),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=1),
    ], base="AABA", repeat=1)
    print(f"  base='AABA'(3:1 비율, hub-leaf 무효로 알려진 표) -> method={r_ratio['method']}, "
          f"crossover_count={r_ratio['crossover_count']}")
    assert r_ratio["method"] == "search"
    print("  OK: 표가 hub-leaf 무효라 자동으로 탐색 경로로 폴백(예외 없이 성공)")

    r_3dev = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=1),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=1),
        Transistor("M5", "nmos", source="tail", drain="LM5", n_fingers=1),
    ], base="ABC", repeat=1)
    print(f"  base='ABC'(3소자, hub-leaf 무효로 알려진 표) -> method={r_3dev['method']}, "
          f"crossover_count={r_3dev['crossover_count']} (0보다 크면 crossover 폴백까지 쓴 것)")
    assert r_3dev["method"] == "search" and r_3dev["crossover_count"] > 0
    print("  OK: 3소자 hub-leaf는 0-crossover가 원천 불가능(§18) -> crossover 폴백으로 성공")

    r_rr = interdigitate_layout([
        Transistor("M9", "nmos", source="tail", drain="LM9", n_fingers=3),
        Transistor("M10", "nmos", source="tail", drain="LM10", n_fingers=3),
    ])
    print(f"  base 없음(2소자, 3:3) -> method={r_rr['method']}, "
          f"crossover_count={r_rr['crossover_count']}, residual={r_rr['residual']:.4f}")
    assert r_rr["method"] == "search" and r_rr["crossover_count"] == 0
    print("  OK: base 없이도 2소자는 여전히 0-crossover로 성공")

    r_rr3 = interdigitate_layout([
        Transistor("M3", "nmos", source="tail", drain="LM3", n_fingers=1),
        Transistor("M4", "nmos", source="tail", drain="LM4", n_fingers=1),
        Transistor("M5", "nmos", source="tail", drain="LM5", n_fingers=1),
    ])
    print(f"  base 없음(3소자, 예전엔 ValueError였음) -> method={r_rr3['method']}, "
          f"crossover_count={r_rr3['crossover_count']}")
    assert r_rr3["method"] == "search" and r_rr3["crossover_count"] > 0
    print("  OK: base 없이도 이제 N>=2 전부 지원(예전 '2소자 전용' 제약 제거) — crossover")
    print("  폴백까지 있어 실패하지 않는다(round-robin이 counts만 보고 그래프로 직접 계산하므로")
    print("  base='ABC'와 결과가 우연이 아니라 필연적으로 동일하다 — 둘 다 {M3:1,M4:1,M5:1}")
    print("  이라는 같은 Counter로 귀결되기 때문)")

    def is_valid_hubleaf_sequence(node_seq, trs, hub, leaf_of):
        """row가 실제로 한 붓 그리기 가능한지(인접 finger가 공유 net을 갖는지) 직접 검증
        — 이 함수의 결과를 그냥 믿지 않고 1차 원리(그래프 인접성)로 재확인한다."""
        if len(node_seq) != len(trs) + 1:
            return False
        for i, name in enumerate(trs):
            edge = {hub, leaf_of[name]}
            if {node_seq[i], node_seq[i + 1]} != edge:
                return False
        return True

    leaf_of = {"M1": "d1", "M2": "d2"}
    row0_valid = is_valid_hubleaf_sequence(cc2["rows"][0]["node_sequence"], cc2["rows"][0]["transistor_sequence"], "tail", leaf_of)
    row1_valid = is_valid_hubleaf_sequence(cc2["rows"][1]["node_sequence"], cc2["rows"][1]["transistor_sequence"], "tail", leaf_of)
    print(f"  검증: 두 행 모두 실제로 인접 finger가 공유 net을 갖는 유효한 오일러 경로인가(1차 원리 재확인) "
          f"-> row0={row0_valid}, row1={row1_valid}")

    row0, row1 = cc2["rows"][0]["transistor_sequence"], cc2["rows"][1]["transistor_sequence"]
    swap = {"M1": "M2", "M2": "M1"}
    # row1은 row0의 swap(reverse 없음)이어야 한다(2026-07-24 수정 — reverse+swap은 완전
    # 1:1 교대 배열에서 자기 자신으로 퇴화하는 실제 버그였다, 함수 docstring 참고).
    is_swap_only = row1 == [swap[x] for x in row0]
    distinct_rows = row0 != row1
    col_avg_m1 = sum(i for i, x in enumerate(row0) if x == "M1") + sum(i for i, x in enumerate(row1) if x == "M1")
    col_avg_m2 = sum(i for i, x in enumerate(row0) if x == "M2") + sum(i for i, x in enumerate(row1) if x == "M2")
    n_m1 = row0.count("M1") + row1.count("M1")
    n_m2 = row0.count("M2") + row1.count("M2")
    print(f"  검증: 총 M1={n_m1}, 총 M2={n_m2}(둘 다 9여야 함), row1==swap(row0)(reverse 없음) "
          f"-> {is_swap_only}, 두 행이 서로 다른가(퇴화 방지) -> {distinct_rows}")
    print(f"  열(column) 평균 상쇄 확인: M1 열평균={col_avg_m1/n_m1:.3f}, M2 열평균={col_avg_m2/n_m2:.3f} "
          f"(가까울수록 좋음 — 완전일치는 균등분할일 때만 보장됨)")

    print()
    print("=== Test 12.7: common_centroid_layout() — N=3 이상 hub-leaf common-centroid ===")
    print("  2026-07-28 신설(사용자 요청: common_centroid_layout()의 3-소자 확장). COMMON_CENTROID_")
    print("  PATTERNS의 ABCCBA/CBAABC는 hub-leaf로 실현 불가능함을 실측 확인(아래 대조) — 대신")
    print("  N개 leaf를 회전 대칭으로 N개 행에 배치하면 항상 모든 소자가 모든 열을 정확히 1번씩")
    print("  지나가 진짜 common-centroid가 됨을 이론+실측으로 확인했다. 2026-07-28 2차: 사용자")
    print("  요청으로 Transistor 리스트 입력 + n_rows(N 위아래 자유 지정) 지원으로 일반화.")
    trs_n3 = [
        Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=6),
        Transistor("MB", "nmos", source="vdd", drain="Lb", n_fingers=6),
        Transistor("MC", "nmos", source="vdd", drain="Lc", n_fingers=6),
    ]
    nway3 = common_centroid_layout(trs_n3)
    print(f"  N=3, count=6 각각(균등) -> {len(nway3['rows'])}개 행, method={nway3['method']}, "
          f"residual={nway3['residual']}:")
    for i, row in enumerate(nway3["rows"]):
        print(f"    row{i}: {row['transistor_sequence']}")
    col_sums = defaultdict(list)
    for row in nway3["rows"]:
        for col, name in enumerate(row["transistor_sequence"]):
            col_sums[name].append(col)
    avgs = {name: sum(cols) / len(cols) for name, cols in col_sums.items()}
    counts_n3 = {name: len(cols) for name, cols in col_sums.items()}
    print(f"  열평균: {avgs} (전부 일치해야 진짜 common-centroid), 소자별 총 개수: {counts_n3} (전부 6이어야 함)")
    assert nway3["method"] == "rotation_exact" and nway3["residual"] == 0.0
    assert len(set(round(v, 9) for v in avgs.values())) == 1, f"열평균이 안 맞는다: {avgs}"
    assert all(c == 6 for c in counts_n3.values()), f"소자별 총 개수가 6이 아니다: {counts_n3}"
    print("  OK: MA/MB/MC 열평균 완전 일치 + 소자별 총 개수 전부 6 + method=rotation_exact(증명된 최적)")
    print("  각 행이 실제로 유효한 hub-leaf walk인지 1차 원리로 재확인(구성 로직을 그냥 믿지 않음):")
    leaf_of_n3 = {"MA": "La", "MB": "Lb", "MC": "Lc"}
    for i, row in enumerate(nway3["rows"]):
        node_seq_check = _hubleaf_sequence_node_path(row["transistor_sequence"], "vdd", leaf_of_n3)
        print(f"    row{i} 독립 재검증: {'OK(유효)' if node_seq_check is not None else 'FAIL'}")
        assert node_seq_check is not None, f"row{i}이 유효한 walk가 아니다"

    print("  대조: PDF 표의 3-소자 패턴(ABCCBA/CBAABC)은 hub-leaf 구조로 애초에 실현 불가능함을")
    print("  재확인(모든 repeat에서 None — 이게 이 함수를 새로 만든 이유다):")
    for repeat, (top, bot) in COMMON_CENTROID_PATTERNS[("ABCCBA", "CBAABC")].items():
        for label, pat in [("top", top), ("bot", bot)]:
            trs_pat = [{"A": "MA", "B": "MB", "C": "MC"}[ch] for ch in pat]
            result = _hubleaf_sequence_node_path(trs_pat, "vdd", leaf_of_n3)
            print(f"    repeat={repeat} {label}={pat} -> {'FAIL(예상외로 유효)' if result is not None else 'OK(예상대로 무효)'}")
            assert result is None, f"repeat={repeat} {label}이 예상과 달리 유효한 walk로 나왔다"

    print("  N=2로 넣으면 회전 1회=swap과 동등한지 확인:")
    trs_n2 = [
        Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=4),
        Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=4),
    ]
    nway2 = common_centroid_layout(trs_n2)
    col_sums2 = defaultdict(list)
    for row in nway2["rows"]:
        for col, name in enumerate(row["transistor_sequence"]):
            col_sums2[name].append(col)
    avgs2 = {name: sum(c) / len(c) for name, c in col_sums2.items()}
    print(f"    N=2 rows: {[r['transistor_sequence'] for r in nway2['rows']]}, 열평균={avgs2}, "
          f"method={nway2['method']}, residual={nway2['residual']}")
    assert nway2["method"] == "rotation_exact" and nway2["residual"] == 0.0
    assert len(set(round(v, 9) for v in avgs2.values())) == 1

    print("  대조군 — 실패 케이스들:")
    # 2026-07-28 3~4차 crossover 폴백 통합 후: 4소자 count=5(모든 block이 홀수, parity
    # repair로도 못 고치는 케이스)는 더 이상 ValueError가 아니라 crossover 배치로 성공한다
    # — 이 케이스가 바로 "crossover 폴백이 실제로 필요한 사례"의 실례다.
    r_odd4 = common_centroid_layout([
        Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=5),
        Transistor("MB", "nmos", source="vdd", drain="Lb", n_fingers=5),
        Transistor("MC", "nmos", source="vdd", drain="Lc", n_fingers=5),
        Transistor("MD", "nmos", source="vdd", drain="Ld", n_fingers=5),
    ])
    assert r_odd4["method"] == "rotation_exact" and r_odd4["residual"] == 0.0
    assert r_odd4["crossover_count"] > 0, \
        f"4소자 count=5는 crossover 폴백이 실제로 발동해야 하는 케이스인데 crossover_count=0: {r_odd4}"
    print(f"    OK: 4소자 count=5(모든 block 홀수) -> crossover 폴백으로 성공, "
          f"crossover_count={r_odd4['crossover_count']}, residual=0.0(변화 없음)")
    try:
        common_centroid_layout([Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=4)])
        print("    FAIL: 소자 1개는 ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"    OK: 소자 부족 거부 -> {e}")
    try:
        common_centroid_layout([
            Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=4),
            Transistor("MA", "nmos", source="vdd", drain="Lb", n_fingers=4),
        ])
        print("    FAIL: 중복 이름은 ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"    OK: 중복 이름 거부 -> {e}")
    try:
        common_centroid_layout([
            Transistor("MA", "nmos", source="vdd", drain="La", n_fingers=4),
            Transistor("MB", "nmos", source="tail", drain="Lb", n_fingers=4),
        ])
        print("    FAIL: hub(source) 불일치는 ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"    OK: hub 불일치 거부 -> {e}")

    print()
    print("=== Test 12.8: common_centroid_layout() 일반화 — 소자 개수가 다르거나 n_rows를")
    print("  N 위아래로 지정(사용자 요청, 2026-07-28 2차) — 휴리스틱 탐색 경로(증명된 최적 아님) ===")
    trs_uneven = [
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=6),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=4),
        Transistor("C", "nmos", source="vdd", drain="Lc", n_fingers=2),
    ]
    print("  [개수가 다름(A=6,B=4,C=2), n_rows 미지정 -> 기본 n_rows=N=3, 탐색 경로로 감]")
    r_uneven = common_centroid_layout(trs_uneven)
    print(f"    rows={[row['transistor_sequence'] for row in r_uneven['rows']]}, "
          f"method={r_uneven['method']}, residual={r_uneven['residual']:.4f}")
    assert r_uneven["method"] == "search"
    for row in r_uneven["rows"]:
        check = _hubleaf_sequence_node_path(row["transistor_sequence"], "vdd",
                                             {"A": "La", "B": "Lb", "C": "Lc"})
        assert check is not None, f"탐색 결과 행이 무효한 walk다: {row}"
    print("    OK: 개수가 달라도 각 행이 실제로 유효한 walk임을 재확인")

    print("  [n_rows=4 (N=3보다 많음, 더 잘게 쪼갬) -- 슬라이싱만으론 모든 phase가 오일러 조건을")
    print("  못 만족했으나 보정(parity repair) 추가 후 성공함을 확인]")
    r_more = common_centroid_layout(trs_uneven, n_rows=4)
    print(f"    rows={[row['transistor_sequence'] for row in r_more['rows']]}, "
          f"residual={r_more['residual']:.4f}")
    assert len(r_more["rows"]) == 4
    for row in r_more["rows"]:
        if row["transistor_sequence"]:
            check = _hubleaf_sequence_node_path(row["transistor_sequence"], "vdd",
                                                 {"A": "La", "B": "Lb", "C": "Lc"})
            assert check is not None, f"n_rows=4 행이 무효한 walk다: {row}"
    print("    OK: n_rows=4 전부 유효한 walk(보정 성공)")

    print("  [n_rows=2 (N=3보다 적음, 회전을 다 못 채움) -- 잔차가 0이 아닐 수 있음을 확인]")
    r_fewer = common_centroid_layout(trs_uneven, n_rows=2)
    print(f"    rows={[row['transistor_sequence'] for row in r_fewer['rows']]}, "
          f"residual={r_fewer['residual']:.4f}, method={r_fewer['method']}")
    assert len(r_fewer["rows"]) == 2 and r_fewer["method"] == "search"

    print("  [균등 개수(N=3, 전부 8) + n_rows=3(=N) 명시 -- target_rows==N+개수 균등이면")
    print("  n_rows를 명시했어도 회전 경로(잔차 0)로 가야 정상(2026-07-28 버그 수정 확인)]")
    trs_even3 = [
        Transistor("X", "nmos", source="vdd", drain="Lx", n_fingers=8),
        Transistor("Y", "nmos", source="vdd", drain="Ly", n_fingers=8),
        Transistor("Z", "nmos", source="vdd", drain="Lz", n_fingers=8),
    ]
    r_explicit_n = common_centroid_layout(trs_even3, n_rows=3)
    print(f"    method={r_explicit_n['method']}, residual={r_explicit_n['residual']:.4f}")
    assert r_explicit_n["method"] == "rotation_exact" and r_explicit_n["residual"] == 0.0, \
        f"target_rows==N+균등개수인데 회전 경로로 안 갔다: {r_explicit_n}"

    print("  [버그 재현+수정 확인: N=2, n_rows=2(=N) 명시 -- 사용자 지적으로 발견됨]")
    print("  기존 탐색 경로(비례 라운드로빈+균등분할)는 '하나의 선형 시퀀스를 자르는' 방식이라")
    print("  swap 관계(두 행이 서로 뒤바뀐 관계)인 후보를 구조적으로 못 만든다 -- 주기적인")
    print("  시퀀스를 반으로 자르면 항상 똑같은 두 조각만 나오기 때문이다(실측 확인, 아래).")
    print("  finger 수를 늘려가며 확인:")
    for nf in (2, 4, 6, 8, 10, 20, 50, 101):
        trs_bug = [
            Transistor("M2", "nmos", source="vdd", drain="out", n_fingers=nf),
            Transistor("M2b", "nmos", source="vdd", drain="bias", n_fingers=nf),
        ]
        r_bug = common_centroid_layout(trs_bug, n_rows=2)
        status = "OK" if r_bug["method"] == "rotation_exact" and r_bug["residual"] == 0.0 else "FAIL"
        print(f"    n_fingers={nf:4d} -> method={r_bug['method']}, residual={r_bug['residual']:.6f} -> {status}")
        assert r_bug["method"] == "rotation_exact" and r_bug["residual"] == 0.0, \
            f"n_fingers={nf}: n_rows=2(=N)인데 회전 경로(잔차 0)를 안 씀 -> {r_bug}"
    print("    OK: 전부 회전 경로로 가서 잔차 0 (수정 전엔 n_fingers=2에서 residual=1.0까지 나왔었다)")

    print()
    print("=== Test 12.9: n_rows==N 전수 스윕(N=2~6, count 다양) — dispatch 버그 수정 후")
    print("  전체 회귀 + '최대한 균등한 분배가 우연히 홀수뿐이면 포기하던' 2차 버그 발견/수정 ===")
    print("  사용자 요구: '다른 n_rows 값(3,4,5)에서도 같은 버그 없는지 다 스윕해봐' — N=2~6,")
    print("  count 다양(N,N+1,N+2,N+3,4,6,8,10,20,50,101 중 count>=N인 것)로 전수 확인.")
    n_rows_sweep_bugs, n_rows_sweep_infeasible = [], []
    for n_dev in (2, 3, 4, 5, 6):
        letters = ["A", "B", "C", "D", "E", "F"][:n_dev]
        for nf in sorted({n_dev, n_dev + 1, n_dev + 2, n_dev + 3, 4, 6, 8, 10, 20, 50, 101}):
            if nf < n_dev:
                continue
            trs_sweep = [Transistor(letters[i], "nmos", source="vdd", drain=f"L{letters[i]}",
                                     n_fingers=nf) for i in range(n_dev)]
            try:
                rr = common_centroid_layout(trs_sweep, n_rows=n_dev)
            except ValueError:
                n_rows_sweep_infeasible.append((n_dev, nf))
                continue
            if not (rr["method"] == "rotation_exact" and rr["residual"] == 0.0):
                n_rows_sweep_bugs.append((n_dev, nf, rr["method"], rr["residual"]))
    print(f"  결과: 회귀(residual!=0인데 통과) {len(n_rows_sweep_bugs)}건, "
          f"ValueError로 거부 {len(n_rows_sweep_infeasible)}건")
    assert not n_rows_sweep_bugs, f"n_rows==N 스윕에서 잔차!=0인 사례 발견: {n_rows_sweep_bugs}"
    print(f"  OK: 회귀 없음. ValueError 사례: {n_rows_sweep_infeasible} "
          f"(2026-07-28 3차 crossover 폴백 추가 후로는 이 스윕 범위(count>=n_dev) 안에서는")
    print(f"  전부 0건이어야 정상 — find_min_crossover_layout()이 절대 실패하지 않으므로)")
    assert not n_rows_sweep_infeasible, (
        f"count>=n_dev인데 ValueError가 났다 — crossover 폴백이 실패했다는 뜻(회귀): "
        f"{n_rows_sweep_infeasible}"
    )
    print("  [발견된 2차 버그: N=4,count=20처럼 '최대한 균등'([5,5,5,5], 전부 홀수)이 오일러")
    print("  불가일 때, 살짝 덜 균등해도 홀짝만 맞는 배분([6,6,4,4] 등)이 있으면 회전 자체는")
    print("  똑같이 잔차 0을 보장하는데(row_0 블록 배분과 무관), 예전엔 그걸 안 찾고 바로")
    print("  ValueError를 냈다 — _fix_block_parity()로 홀수쌍을 짝지어 1개씩 주고받는 보정 추가]")
    trs_n4_c20 = [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=20) for n in ["A", "B", "C", "D"]]
    r_n4_c20 = common_centroid_layout(trs_n4_c20, n_rows=4)
    print(f"    N=4, count=20(균등분배 [5,5,5,5]는 전부 홀수라 원래 실패) -> "
          f"method={r_n4_c20['method']}, residual={r_n4_c20['residual']}")
    assert r_n4_c20["method"] == "rotation_exact" and r_n4_c20["residual"] == 0.0
    block_counts = [Counter(row["transistor_sequence"])["A"] for row in r_n4_c20["rows"]]
    print(f"    실제 채택된(보정 후) 블록 배분 확인 — row0의 A 개수 등으로 짝수 배분임을 간접 확인: "
          f"소자별 총합 A={sum(row['transistor_sequence'].count('A') for row in r_n4_c20['rows'])}(=20이어야 함)")
    print("    OK: 보정으로 잔차 0 달성 (수정 전엔 ValueError로 거부됐었다)")

    print("  [소자별 개수(count)가 소자 수(N)보다 작으면(예: N=4, 각 2개씩) 명확한 ValueError인지")
    print("  확인 — 이 스윕 중 발견: 균등분배 시 일부 소자가 0개가 되는 경우가 있었다]")
    try:
        common_centroid_layout(
            [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=2) for n in ["A", "B", "C", "D"]],
            n_rows=4,
        )
        print("    FAIL: count=2 < n=4는 ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"    OK: count < 소자 수는 명확한 ValueError로 거부 -> {e}")

    print()
    print("=== Test 12.9b: 회전 경로에 crossover 폴백 통합 (사용자 요청, 2026-07-28 3차) ===")
    print("  사용자 질문: 'common_centroid도 최소 crossover routing 조건을 추가하면")
    print("  어떻게 되지?' -> 프로토타입으로 먼저 확인: 회전은 순수 relabeling이라 row_0에")
    print("  crossover가 있어도 잔차 0 증명은 그대로 유지됨을 확인한 뒤 통합.")
    print("  [Test 12.9에서 '진짜 불가능'으로 확인됐던 10개 조합 전부 재확인 -- 이제는")
    print("  ValueError 대신 crossover_count>0으로 성공해야 하고, 잔차는 여전히 0이어야 함]")
    genuinely_infeasible_before = [(3, 3), (4, 4), (4, 5), (5, 5), (5, 6), (5, 7),
                                    (6, 6), (6, 7), (6, 8), (6, 9)]
    for n_dev, nf in genuinely_infeasible_before:
        letters = "ABCDEF"[:n_dev]
        trs_gi = [Transistor(letters[i], "nmos", source="vdd", drain=f"L{letters[i]}",
                              n_fingers=nf) for i in range(n_dev)]
        r_gi = common_centroid_layout(trs_gi, n_rows=n_dev)
        print(f"    N={n_dev}, count={nf}: method={r_gi['method']}, residual={r_gi['residual']}, "
              f"crossover_count={r_gi['crossover_count']}")
        assert r_gi["method"] == "rotation_exact" and r_gi["residual"] == 0.0, (
            f"N={n_dev},count={nf}: crossover 폴백 후에도 잔차가 0이 아니다 -> {r_gi}"
        )
        assert r_gi["crossover_count"] > 0, (
            f"N={n_dev},count={nf}: 예전엔 ValueError였던 사례인데 crossover_count가 0이다 "
            f"-- 회귀(원래부터 됐던 건지 재확인 필요): {r_gi}"
        )
        for row in r_gi["rows"]:
            for seg in row["segments"]:
                if seg["transistor_sequence"]:
                    leaf_of_gi = {letters[i]: f"L{letters[i]}" for i in range(n_dev)}
                    check = _hubleaf_sequence_node_path(seg["transistor_sequence"], "vdd", leaf_of_gi)
                    assert check is not None, f"segment이 유효한 walk가 아니다: {seg}"
            total_here = sum(len(s["transistor_sequence"]) for s in row["segments"])
            assert total_here == len(row["transistor_sequence"])
    print("  OK: 10개 조합 전부 crossover_count>0으로 성공 + 잔차 정확히 0 + 각 segment")
    print("  독립적으로 유효한 walk (이전엔 전부 ValueError로 거부됐던 조합들)")

    print("  [이미 0-crossover로 성공하던 케이스(N=2,count=4)는 전혀 안 바뀌었는지 회귀 확인]")
    r_no_regress = common_centroid_layout([
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=4),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=4),
    ])
    print(f"    crossover_count={r_no_regress['crossover_count']} (0이어야 함), "
          f"rows={[row['transistor_sequence'] for row in r_no_regress['rows']]}")
    assert r_no_regress["crossover_count"] == 0
    print("    OK: 기존 0-crossover 케이스는 전혀 안 바뀜")

    print()
    print("=== Test 12.10: n_rows != N(N보다 크거나 작은 경우) 전수 스윕 — 사용자 요구 ===")
    print("  '나머지 n_rows도 스윕해봐(N보다 크거나 작은 경우)' — N=2~6, n_rows=1~2N+1,")
    print("  finger 다양(총 360개 조합)으로 크래시/구조 오류/잔차 지표 결함을 확인.")
    print("  2026-07-28 4차: 탐색 경로에도 crossover 폴백이 추가돼 이제 실패가 훨씬 줄어든다 —")
    print("  행 전체(transistor_sequence)가 아니라 각 segment를 독립적으로 검증한다(crossover가")
    print("  있으면 flat 시퀀스 자체는 더 이상 단일 연속 walk가 아닌 게 정상이기 때문).")
    sweep_crashes, sweep_struct_bugs, sweep_total, sweep_valueerrors = [], [], 0, 0
    sweep_total_crossovers = 0
    for n_dev in (2, 3, 4, 5, 6):
        letters = ["A", "B", "C", "D", "E", "F"][:n_dev]
        for n_rows_sw in range(1, 2 * n_dev + 2):
            if n_rows_sw == n_dev:
                continue  # Test 12.9에서 이미 전수 확인
            for nf in sorted({n_dev, n_dev + 1, n_dev + 2, 4, 6, 8, 10, 20}):
                if nf < 1:
                    continue
                sweep_total += 1
                trs_sw = [Transistor(letters[i], "nmos", source="vdd", drain=f"L{letters[i]}",
                                      n_fingers=nf) for i in range(n_dev)]
                try:
                    rr = common_centroid_layout(trs_sw, n_rows=n_rows_sw)
                except ValueError:
                    sweep_valueerrors += 1
                    continue
                except Exception as e:
                    sweep_crashes.append((n_dev, n_rows_sw, nf, type(e).__name__))
                    continue
                if len(rr["rows"]) != n_rows_sw:
                    sweep_struct_bugs.append((n_dev, n_rows_sw, nf, "row count mismatch"))
                    continue
                leaf_of_sw = {letters[i]: f"L{letters[i]}" for i in range(n_dev)}
                total_counter = Counter()
                ok = True
                for row in rr["rows"]:
                    for seg in row["segments"]:
                        if not seg["transistor_sequence"]:
                            continue
                        check = _hubleaf_sequence_node_path(seg["transistor_sequence"], "vdd", leaf_of_sw)
                        if check is None:
                            sweep_struct_bugs.append((n_dev, n_rows_sw, nf, "invalid segment"))
                            ok = False
                            break
                    if not ok:
                        break
                    total_counter.update(row["transistor_sequence"])
                if ok and sum(total_counter.values()) != n_dev * nf:
                    sweep_struct_bugs.append((n_dev, n_rows_sw, nf, "count mismatch"))
                if ok:
                    sweep_total_crossovers += rr["crossover_count"]
    print(f"  {sweep_total}개 조합: 크래시 {len(sweep_crashes)}건, 구조 오류(무효 segment/개수·행수 "
          f"불일치) {len(sweep_struct_bugs)}건, ValueError {sweep_valueerrors}건, "
          f"성공한 조합의 crossover 총합={sweep_total_crossovers}")
    assert not sweep_crashes, f"예상치 못한 예외 발생: {sweep_crashes}"
    assert not sweep_struct_bugs, f"구조적 오류 발견: {sweep_struct_bugs}"
    print("  OK: 크래시/구조 오류 없음 (모든 결과가 segment 단위로 유효한 walk + 개수/행수 일치)")

    print("  [발견된 잔차 지표 결함: 길이 1인 행을 건너뛰면 그 행에만 있는 소자가 완전히")
    print("  안 잡혀 잔차가 거짓으로 낮게(0.0) 나올 수 있었다 — _common_centroid_residual()에")
    print("  '중립값 0.5' 처리 추가로 최소한 그 소자가 반드시 기록되도록 수정]")
    residual_before_fix_sim = 0.0  # 옛 버전 시뮬레이션(길이1 스킵) -- A만 있어서 0.0
    r_blind = _common_centroid_residual([
        {"transistor_sequence": ["A", "A", "B", "B"]},
        {"transistor_sequence": ["C"]},
    ])
    print(f"    A=[0,0.33],B=[0.67,1](비대칭) + C(길이1 행에만 존재) -> residual={r_blind:.4f} "
          f"(C가 반영돼 0이 아님을 확인)")
    assert r_blind > 0.0, "길이 1 행의 소자가 잔차 계산에서 여전히 안 보인다"

    print("  [발견된 더 근본적 한계: 소자 하나가 통째로 자기 행에만 격리되면(다른 소자와 단")
    print("  한 번도 같은 행에 있어본 적 없음) 그 자체는 대칭적으로 보여 잔차가 낮게 나올 수")
    print("  있다 — n_rows가 총 finger 수 대비 너무 많으면(모든 행 길이가 1) 구조적으로")
    print("  피할 수 없다. isolated_pairs 필드를 추가해 이 상황을 정직하게 드러낸다:]")
    trs_isolate = [
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=2),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=2),
    ]
    r_isolate = common_centroid_layout(trs_isolate, n_rows=4)
    print(f"    N=2,count=2,n_rows=4(모든 행이 길이 1일 수밖에 없음) -> "
          f"rows={[row['transistor_sequence'] for row in r_isolate['rows']]}")
    print(f"    residual={r_isolate['residual']}, isolated_pairs={r_isolate['isolated_pairs']} "
          f"(0이 아님 — A/B가 단 한 행에서도 같이 있어본 적 없다는 뜻, residual만 보면 놓칠 뻔함)")
    assert r_isolate["isolated_pairs"] > 0, "격리 상황이 isolated_pairs에 반영되지 않았다"
    print("    OK: isolated_pairs로 격리 상황이 정직하게 드러남")
    print("  [증명된 최적 경로(rotation_exact)는 항상 isolated_pairs=0인지 확인]")
    r_exact_check = common_centroid_layout(trs_isolate)
    assert r_exact_check["method"] == "rotation_exact" and r_exact_check["isolated_pairs"] == 0
    print(f"    OK: n_rows 미지정(회전 경로)이면 isolated_pairs=0 (rows="
          f"{[row['transistor_sequence'] for row in r_exact_check['rows']]})")

    print()
    print("=== Test 12.11: INTERDIGITATION_PATTERNS 표 전체 — interdigitate_layout()가 표/탐색+")
    print("  crossover 중 맞는 경로를 자동으로 찾는지 전수 스윕(§18 발견의 연장,")
    print("  2026-07-28 5차: interdigitate_layout()를 common_centroid_layout()와 동급으로")
    print("  재설계 — 검증+crossover 폴백을 함수 내부로 흡수) ===")
    pattern_table_count = 0
    pattern_total = 0
    expected_valid = {("A", 1), ("A", 2), ("A", 3), ("A", 4), ("AB", 1), ("AB", 2), ("AB", 3)}
    for base, reps in INTERDIGITATION_PATTERNS.items():
        for repeat, pattern in reps.items():
            letter_counts = Counter(pattern)
            letters = sorted(letter_counts)
            names_p = list("ABCDEFG"[:len(letters)])
            trs_p = [Transistor(nm, "nmos", source="vdd", drain=f"L{nm}", n_fingers=letter_counts[ch])
                     for nm, ch in zip(names_p, letters)]
            result_p = interdigitate_layout(trs_p, base=base, repeat=repeat)
            pattern_total += 1
            is_table = result_p["method"] == "pattern_table"
            if is_table:
                pattern_table_count += 1
            expected = (base, repeat) in expected_valid
            assert is_table == expected, (
                f"base={base} repeat={repeat}: 예상(table={expected})과 실제(table={is_table})가 "
                f"다르다 -- INTERDIGITATION_PATTERNS 표가 바뀌었거나 매칭 로직에 회귀가 있다"
            )
            assert result_p["rows"] and result_p["crossover_count"] >= 0  # 예외 없이 항상 결과 반환
    print(f"  {pattern_total}개 조합 중 method=pattern_table {pattern_table_count}건 "
          f"(A 4개 + AB의 repeat 1,2,3 = 7건 예상과 일치), 나머지 {pattern_total - pattern_table_count}건은")
    print("  전부 method=search로 자동 폴백해 예외 없이 성공(hub-leaf 무효였던 표도 crossover까지")
    print("  동원해 결과를 낸다)")
    print("  OK: interdigitate_layout()가 이제 common_centroid_layout()처럼 검증+폴백을 함수")
    print("  내부에서 전부 처리한다 -- 호출자가 별도로 _hubleaf_sequence_node_path()를 부를")
    print("  필요가 없어졌다.")

    print()
    print("=== Test 12.12: find_min_crossover_layout() — 최소 crossover 배치 신설 ===")
    print("  사용자 요청: 'crossover routing이 최소인 조합을 찾아 갯수도 표시, 우선순위는")
    print("  crossover가 안 생기는 연속 diffusion' -- route inspection/T-join 정리 적용.")
    print("  [이미 가능한 경우(0 crossover) — 우선순위대로 단일 연속 diffusion부터 확인]")
    r_ok = find_min_crossover_layout([
        Transistor("A", "nmos", source="vdd", drain="La", n_fingers=2),
        Transistor("B", "nmos", source="vdd", drain="Lb", n_fingers=2),
    ])
    print(f"    crossover_count={r_ok['crossover_count']}, segments="
          f"{[s['transistor_sequence'] for s in r_ok['segments']]}")
    assert r_ok["crossover_count"] == 0 and len(r_ok["segments"]) == 1

    print("  [ABC 3소자 1개씩(4개 홀수차수 노드, m=2) -> crossover=1이어야 함]")
    r_abc = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABC"])
    print(f"    crossover_count={r_abc['crossover_count']}, segments="
          f"{[s['transistor_sequence'] for s in r_abc['segments']]}")
    assert r_abc["crossover_count"] == 1
    total_abc = sum(len(s["transistor_sequence"]) for s in r_abc["segments"])
    assert total_abc == 3, f"실제 finger 총합이 3이 아니다: {total_abc}"
    print("    OK: crossover=1, 전체 소자 3개 그대로 보존")

    print("  [6소자 1개씩(6개 홀수차수 노드, m=3) -> crossover=2, 소자 6개 보존]")
    r_6 = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABCDEF"])
    print(f"    crossover_count={r_6['crossover_count']}, segments="
          f"{[s['transistor_sequence'] for s in r_6['segments']]}")
    assert r_6["crossover_count"] == 2
    assert sum(len(s["transistor_sequence"]) for s in r_6["segments"]) == 6

    print("  [각 segment 내부가 실제로 유효한 hub-leaf walk인지 1차 원리로 재확인]")
    leaf_of_6 = {n: f"L{n}" for n in "ABCDEF"}
    for seg in r_6["segments"]:
        check = _hubleaf_sequence_node_path(seg["transistor_sequence"], "vdd", leaf_of_6)
        assert check is not None, f"segment이 유효한 walk가 아니다: {seg}"
    print("    OK: 모든 segment가 독립적으로 유효한 walk (crossover로 이어붙이는 지점만 끊김)")

    print("  [ABCD 표 패턴(4소자 1개씩)이 실제로 crossover=1로 해결되는지 -- 사용자가")
    print("  질문했던 INTERDIGITATION_PATTERNS의 무효 패턴에 실제 답을 주는 사례]")
    r_abcd = find_min_crossover_layout(
        [Transistor(n, "nmos", source="vdd", drain=f"L{n}", n_fingers=1) for n in "ABCD"])
    print(f"    crossover_count={r_abcd['crossover_count']}, segments="
          f"{[s['transistor_sequence'] for s in r_abcd['segments']]}")
    assert r_abcd["crossover_count"] == 1

    print("  [대조군 -- 입력 검증]")
    try:
        find_min_crossover_layout([])
        print("    FAIL: 빈 리스트는 ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"    OK: 빈 리스트 거부 -> {e}")
    try:
        find_min_crossover_layout([
            Transistor("A", "nmos", source="vdd", drain="La", n_fingers=1),
            Transistor("B", "nmos", source="tail", drain="Lb", n_fingers=1),
        ])
        print("    FAIL: hub 불일치는 ValueError가 나야 하는데 안 남")
    except ValueError as e:
        print(f"    OK: hub 불일치 거부 -> {e}")

    print()
    print("=== Test 12.13: find_min_crossover_layout() matching_pairs 확장(세션15) —")
    print("  node_map 기반 짝짓기로 hub-leaf 아닌 일반 그룹도 지원, 세션17에 짝짓기 선택")
    print("  방식 자체가 재작성됨(아래) ===")
    print("  [실전: current_reuse_telescopic_ota.topology.json M6 그룹(8소자) — 핑거조정")
    print("  으로는 절대 못 푸는 실제 사례(세션15 probe로 확인, .ai/context.md 참고).")
    print("  ⚠️ 세션16 D-1에서 이 사례의 tier1 짝짓기(Vom1/Vop1 직접)가 실제로는 matching_")
    print("  pairs(M1a/M1b, M2a/M2b)를 서로 다른 segment로 갈라놓는 최악의 선택이었음이")
    print("  드러났다(splits=2, probe_crossover_pairing_alternatives.py) — 세션17")
    print("  _select_crossover_pairing()이 대안(Vbias2/Vom1 + Vop1/Vx, crossover는 미매칭")
    print("  M57/M58 쪽에서만)으로 자동 교체해 splits=0을 달성하는지 확인]")
    print("  ⚠️ 세션22부터 이 8소자는 geometry_colocation_union()이 더 이상 자동으로")
    print("  묶지 않는다(M6/M7/M57/M58은 matching_pairs가 없어 각자 독립 그룹 -- stack")
    print("  M6 크래시의 근본원인이었던 Vx fan-out 자동병합을 제거했기 때문, .ai/")
    print("  context.md 세션22 참고). 이 테스트는 find_min_crossover_layout()/짝짓기")
    print("  로직 자체(레이아웃 압축을 위해 이 8개를 한 행에 두기로 **의도적으로**")
    print("  선언했다고 가정)를 검증하는 것이므로, 그룹을 geometry_colocation_union()")
    print("  경유가 아니라 직접(수동 override와 동일한 방식으로) 구성한다.")
    import os as _os1213
    _lib1213 = _os1213.path.join(_os1213.path.dirname(_os1213.path.abspath(__file__)), "library")
    _m6_trs, _m6_meta = load_topology(
        _os1213.path.join(_lib1213, "current_reuse_telescopic_ota.topology.json"))
    _m6_pairs_meta = _m6_meta["symmetry"]["matching_pairs"]
    _m6_by_name = {t.name: t for t in _m6_trs}
    _m6_order = {t.name: i for i, t in enumerate(_m6_trs)}
    _m6_names = sorted({"M6", "M7", "M1a", "M1b", "M2a", "M2b", "M58", "M57"},
                        key=lambda n: _m6_order[n])
    _m6_group_trs = [_dc_replace(_m6_by_name[n], stack_id="M6") for n in _m6_names]
    _m6_inside_pairs = [tuple(p["names"]) for p in _m6_pairs_meta
                         if set(p["names"]) <= set(_m6_names)]

    _m6_g = build_graph(_m6_group_trs)
    _m6_odd = check_euler_condition(_m6_g).odd_nodes
    print(f"    baseline odd_nodes({len(_m6_odd)}): {_m6_odd}")
    assert len(_m6_odd) == 4, f"baseline 홀수차수가 4개가 아님(사례 자체가 바뀜): {_m6_odd}"

    # 세션17 -- 옛 tier1 짝짓기(Vom1/Vop1)로 구성했을 때 실제로 splits=2였는지 먼저
    # 확인한다(비교 기준선, D-1 발견을 이 self-test 안에서도 재현).
    _m6_node_map_early = _mirror_node_map_from_pairs(_m6_inside_pairs, _m6_group_trs)
    _m6_tier1_pairs, _ = _pair_odd_nodes_by_mirror(_m6_odd, _m6_node_map_early)
    _m6_tier1_segments = _build_crossover_segments(_m6_group_trs, _m6_tier1_pairs)
    _m6_tier1_splits = _count_matching_pair_splits(_m6_tier1_segments, _m6_inside_pairs)
    assert _m6_tier1_splits == 2, (
        f"D-1 재현 실패 -- 옛 tier1 짝짓기({_m6_tier1_pairs})가 여전히 matching_pairs를 "
        f"안 갈라놓는다면(splits={_m6_tier1_splits}) 이 회귀 대조 자체가 틀렸을 수 있으니 "
        f"topology.json이 바뀌었는지부터 확인할 것"
    )
    print(f"    (회귀 대조: 옛 tier1 짝짓기({_m6_tier1_pairs})는 splits={_m6_tier1_splits} -- "
          f"세션16 D-1 재현)")

    _m6_result = find_min_crossover_layout(_m6_group_trs, _m6_inside_pairs)
    print(f"    crossover_count={_m6_result['crossover_count']}, "
          f"node_pairing_fallback_used={_m6_result['node_pairing_fallback_used']}")
    assert _m6_result["crossover_count"] == 1, \
        f"m=2(crossover=1)이어야 하는데: {_m6_result['crossover_count']}"
    assert _m6_result["node_pairing_fallback_used"] is False, \
        "tier1/tier2만으로 다 짝지어져야 하는데 fallback이 발동함"
    _m6_total = sum(len(s["transistor_sequence"]) for s in _m6_result["segments"])
    assert _m6_total == len(_m6_group_trs), \
        f"trail 분해 후 소자 총합이 안 맞음: {_m6_total} != {len(_m6_group_trs)}"
    _m6_final_splits = _count_matching_pair_splits(_m6_result["segments"], _m6_inside_pairs)
    assert _m6_final_splits == 0, (
        f"세션17 재작성의 핵심 목표(matching_pairs를 안 갈라놓기)가 실패함 -- "
        f"splits={_m6_final_splits}, segments={_m6_result['segments']}"
    )
    print(f"    PASS: crossover=1(m=2) 그대로(T-join 불변, 세션16 tier1과 동일), 하지만 "
          f"splits=2(옛 tier1) -> splits=0(세션17 _select_crossover_pairing)으로 개선 -- "
          f"M1a/M1b/M2a/M2b가 이제 같은 segment에 유지되고 crossover는 미매칭 M57/M58 "
          f"쪽에서만 발생, 소자 {len(_m6_group_trs)}개 전부 보존")

    print("  [node_map 역산 단위 확인 -- M2a/M2b가 서로 공유 끝이 없어도 Vom1<->Vop1이")
    print("  바로 나오는지(체인 전이 없이 규칙 자체로 유도됨을 확인)]")
    _m6_node_map = _mirror_node_map_from_pairs(_m6_inside_pairs, _m6_group_trs)
    assert _m6_node_map.get("Vom1") == "Vop1" and _m6_node_map.get("Vop1") == "Vom1", \
        f"Vom1<->Vop1 대응이 안 나옴: {_m6_node_map}"
    assert _m6_node_map.get("Vx") == "Vx", f"Vx가 자기대응이 아님: {_m6_node_map.get('Vx')}"
    assert "Vbias2" not in _m6_node_map, \
        f"Vbias2는 orphan이어야 하는데 node_map에 들어있음: {_m6_node_map.get('Vbias2')}"
    print(f"    PASS: Vom1<->Vop1(거울쌍), Vx(자기대응), Vbias2(orphan) 전부 예상과 일치")

    print("  [폴백 발동 확인 -- matching_pairs가 텅 비어 전부 orphan이면(자기대응 노드가")
    print("  하나도 없음) 기존 방식(순서대로)으로 폴백하고 그 사실이 플래그로 남는지]")
    _fb_trs = [Transistor(n, "nmos", source="hubX", drain=f"L{n}", n_fingers=1)
               for n in ("P", "Q", "R", "S")]
    _fb_result = find_min_crossover_layout(_fb_trs, matching_pairs=[])
    print(f"    crossover_count={_fb_result['crossover_count']}, "
          f"node_pairing_fallback_used={_fb_result['node_pairing_fallback_used']}")
    assert _fb_result["node_pairing_fallback_used"] is True, \
        "matching_pairs가 전혀 없으면 전부 orphan이라 100% 폴백이어야 함"
    assert _fb_result["crossover_count"] == 1
    print("    PASS: matching_pairs=[] -> node_map이 텅 비어 전부 orphan -> 전부 폴백 짝짓기")

    print("  [회귀 -- matching_pairs=None(기존 호출부 경로, 하위호환)이면 hub-leaf 사전조건과")
    print("  순서대로 짝짓기가 완전히 그대로인지 -- 위 ABC/6소자 테스트가 이미 이 경로를 타므로")
    print("  여기선 node_pairing_fallback_used가 정확히 None(신규 로직 미개입)인지만 추가 확인]")
    assert r_abc["node_pairing_fallback_used"] is None
    assert r_6["node_pairing_fallback_used"] is None
    print("    PASS: matching_pairs=None 경로는 node_pairing_fallback_used=None")

    print("  [세션17 offset 우선순위 가중치 -- _count_matching_pair_splits()의")
    print("  pair_sensitivity 튜플 채점이 offset 쌍을 ratio 쌍보다 우선 보호하는지.")
    print("  ⚠️ 실제 회로(M6 등)로 '동점인데 가중치로 갈리는' 진짜 tradeoff 사례를 여러")
    print("  구조(순수 star, hub-bridge 1개/2개, leaf-bridge)로 찾아봤으나 못 찾음(전부")
    print("  offset 쌍이 항상 갈라지거나 항상 안 갈라지는 두 극단으로만 수렴함, hierholzer")
    print("  순회 특성 때문 -- probe_offset_tradeoff*.py, 스크래치패드). 그래서 segment를")
    print("  손으로 구성해 채점 함수 자체를 직접 검증한다(그래프 탐색에 의존하지 않는 확실한")
    print("  검증), 그리고 M6 실제 회로로는 pair_sensitivity를 줘도 이미 달성한 (0,0)이")
    print("  안 깨지는지(회귀 안전성)만 확인]")
    _w_pairs = [("Ma", "Mb"), ("Mc", "Md")]
    _w_sensitivity = {("Ma", "Mb"): "offset", ("Mc", "Md"): "ratio"}
    assert _count_matching_pair_splits(
        [{"transistor_sequence": ["Ma", "Mc"]}, {"transistor_sequence": ["Mb", "Md"]}],
        _w_pairs) == 2, "둘 다 갈라진 경우 스칼라=2가 아님"
    assert _count_matching_pair_splits(
        [{"transistor_sequence": ["Ma", "Mc"]}, {"transistor_sequence": ["Mb", "Md"]}],
        _w_pairs, _w_sensitivity) == (1, 1), "둘 다 갈라진 경우 가중치 튜플=(1,1)이 아님"
    print("    PASS: pair_sensitivity 없으면 스칼라(=2), 있으면 (offset=1,other=1) 튜플")

    # 핵심 -- "동점인데 가중치로 갈리는" 상황을 손으로 구성: segA는 offset(Ma/Mb) 보호+
    # ratio(Mc/Md) 희생, segB는 ratio 보호+offset 희생. 스칼라 총합은 둘 다 1로 완전히
    # 동점이라 pair_sensitivity 없이는 구분이 안 되지만(먼저 발견된 후보 유지, 근거 없는
    # 임의 선택), 튜플 비교는 (0,1) < (1,0)이라 항상 offset 보호를 우선한다.
    _seg_protect_offset = [{"transistor_sequence": ["Ma", "Mb"]}, {"transistor_sequence": ["Mc"]},
                            {"transistor_sequence": ["Md"]}]
    _seg_protect_ratio = [{"transistor_sequence": ["Mc", "Md"]}, {"transistor_sequence": ["Ma"]},
                           {"transistor_sequence": ["Mb"]}]
    _plain_a = _count_matching_pair_splits(_seg_protect_offset, _w_pairs)
    _plain_b = _count_matching_pair_splits(_seg_protect_ratio, _w_pairs)
    _weighted_a = _count_matching_pair_splits(_seg_protect_offset, _w_pairs, _w_sensitivity)
    _weighted_b = _count_matching_pair_splits(_seg_protect_ratio, _w_pairs, _w_sensitivity)
    assert _plain_a == _plain_b == 1, \
        f"두 후보의 스칼라 총합이 동점(=1)이어야 tradeoff 시나리오가 성립: {_plain_a}, {_plain_b}"
    assert _weighted_a == (0, 1) and _weighted_b == (1, 0), \
        f"가중치 튜플이 예상과 다름: A={_weighted_a}, B={_weighted_b}"
    assert _weighted_a < _weighted_b, \
        "offset 보호 후보(A)가 ratio 보호 후보(B)보다 더 나은 점수여야 함(사전식 비교)"
    print(f"    PASS: 스칼라로는 완전히 동점(둘 다 1)이라 가중치 없이는 근거 없이 아무 후보나")
    print(f"    선택됐을 상황 -- pair_sensitivity를 주면 (0,1)<(1,0)로 offset 보호 후보가")
    print(f"    항상 결정적으로 이김")
    assert _is_perfect_crossover_score(0) and _is_perfect_crossover_score((0, 0))
    assert not _is_perfect_crossover_score(1) and not _is_perfect_crossover_score((1, 0))
    print("    PASS: _is_perfect_crossover_score()가 스칼라/튜플 둘 다 올바르게 판정")

    print("  [M6 실제 회로 회귀 -- pair_sensitivity를 줘도 이미 달성한 (0,0)이 안 깨지는지]")
    _m6_sensitivity_for_split = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _m6_weighted_result = find_min_crossover_layout(
        _m6_group_trs, _m6_inside_pairs, pair_sensitivity=_m6_sensitivity_for_split)
    _m6_weighted_splits = _count_matching_pair_splits(
        _m6_weighted_result["segments"], _m6_inside_pairs, _m6_sensitivity_for_split)
    assert _m6_weighted_splits == (0, 0), \
        f"pair_sensitivity를 줬더니 M6 그룹의 완벽한 결과(0,0)가 깨짐: {_m6_weighted_splits}"
    assert _m6_weighted_result["crossover_count"] == 1
    print(f"    PASS: pair_sensitivity 지정해도 M6 그룹은 여전히 (0,0) 유지(회귀 없음), "
          f"crossover_count={_m6_weighted_result['crossover_count']}")

    print()
    print("=== Test 13: check_box_shape() 게이트 — SPICE 전에 반드시 통과해야 하는 §8 체크포인트 ===")
    print("  2026-08-13(세션31): rows: dict[str, list[Transistor]] 기반으로 재작성 --")
    print("  finger_w=l=1.0 균일값을 쓰면 pitch(l)=1.0이라 옛 finger-count 수치를 그대로 재현한다.")

    def _row13(row, n, finger_w=1.0, l=1.0, kind="nmos"):
        return {row: [Transistor(f"{row}_dev", kind, source="s", drain="d",
                                  n_fingers=n, finger_w=finger_w, l=l)]}

    print("  Example 1의 실제 최초 실수(nstack=3, pstack=32)를 이 게이트에 넣으면:")
    before1 = check_box_shape({**_row13("nstack", 3), **_row13("pstack", 32)})
    print(f"  {before1.message}")
    print("  §8로 고친 뒤(8:8):")
    after1 = check_box_shape({**_row13("nstack", 8), **_row13("pstack", 8)})
    print(f"  {after1.message}")
    print(f"  -> 게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: "
          f"{'OK' if (not before1.ok and after1.ok) else 'FAIL'}")
    print("  Example 2의 실제 최초 실수(diffpair 2행x9, tailstack 24, loadstack 38)를 넣으면:")
    before2 = check_box_shape({**_row13("diffpair_row0", 9), **_row13("diffpair_row1", 9),
                                **_row13("tailstack", 24), **_row13("loadstack", 38)})
    print(f"  {before2.message}")
    print("  §8로 고친 뒤(전부 폭 10):")
    after2 = check_box_shape({**_row13("diffpair_row0", 10), **_row13("diffpair_row1", 10),
                               **_row13("tailstack", 10), **_row13("loadstack", 10)})
    print(f"  {after2.message}")
    print(f"  -> 게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: "
          f"{'OK' if (not before2.ok and after2.ok) else 'FAIL'}")

    print("  결측치(l/finger_w 없음) 근사 처리 확인:")
    approx_verdict = check_box_shape({"row_full": [Transistor("full_dev", "nmos", source="s",
                                                                 drain="d", n_fingers=8,
                                                                 finger_w=1.0, l=1.0)],
                                       "row_bare": [Transistor("bare_dev", "nmos", source="s",
                                                                 drain="d", n_fingers=8)]})
    print(f"  {approx_verdict.message}")
    print(f"  -> approx=True로 명시(조용히 finger-count로 대체하지 않음): "
          f"{'OK' if approx_verdict.approx else 'FAIL'}")

    print("  높이(finger_w) 편차 축 -- 폭은 같지만 finger_w가 다른 두 행(elongation 신설 축):")
    tall_rows = {**_row13("row_thin", 8, finger_w=1.0, l=1.0),
                 **_row13("row_thick", 8, finger_w=6.0, l=1.0)}
    # width_m 둘 다 8(정합) / total_height_m=1+6=7 -> elongation=8/7≈1.14, max_elongation=1.1로
    # 걸리게 설정(마진 없이 정확히 걸리도록 수치를 직접 계산해서 잡음).
    tall_verdict = check_box_shape(tall_rows, max_elongation=1.1, orientation="either")
    print(f"  {tall_verdict.message} (row_heights={tall_verdict.row_heights}, "
          f"elongation={tall_verdict.elongation:.2f})")
    print(f"  -> 폭은 정합(rectangular)이지만 elongation 축이 새로 FAIL을 잡아냄: "
          f"{'OK' if (tall_verdict.rectangular and not tall_verdict.elongation_ok) else 'FAIL'}")

    print("  orientation 선택(가로로만 길게 허용 vs 세로로만 길게 허용):")
    wide_rows = {**_row13("row_a", 20, finger_w=1.0, l=1.0),
                 **_row13("row_b", 20, finger_w=1.0, l=1.0)}  # width=20, height=2 -> 가로로 김
    wide_ok = check_box_shape(wide_rows, max_elongation=15.0, orientation="wide")
    tall_fail = check_box_shape(wide_rows, max_elongation=15.0, orientation="tall")
    print(f"  wide 허용 시: {wide_ok.message}")
    print(f"  tall 허용 시(방향 안 맞음): {tall_fail.message}")
    print(f"  -> orientation이 방향까지 구분: "
          f"{'OK' if (wide_ok.elongation_ok and not tall_fail.elongation_ok) else 'FAIL'}")

    print()
    print("=== Test 14: stage 경계를 넘는 stack 병합 — Maloberti p.29 'Layout Oriented Design' 재현 ===")
    print("  슬라이드 원문: 1단 PMOS 부하(M3/M4)와 2단 PMOS gain 소자(M6)를 stage가 다름에도")
    print("  '같은 극성 + vdd 공유'라는 이유만으로 한 물리 행에 합친다. 이걸 재현하고, 3개 이상의")
    print("  leaf가 한 hub를 공유하면 공통 finger 수 k가 반드시 짝수여야 함을 직접 검증한다.")

    # 1차 원리 재확인: check_multi_leaf_hub_parity() 공식이 실제 build_graph()+check_euler_condition()
    # 결과와 항상 일치하는지 폭넓게 대조(공식만 믿지 않는다 — 이 세션 내내 지켜온 원칙).
    import itertools
    mismatch = 0
    for kis in itertools.product(range(1, 5), repeat=3):
        ts = [Transistor(f"D{i}", "pmos", source="hub", drain=f"leaf{i}", n_fingers=k)
              for i, k in enumerate(kis)]
        g = build_graph(ts)
        real = check_euler_condition(g).kind
        formula = check_multi_leaf_hub_parity({f"leaf{i}": k for i, k in enumerate(kis)}).kind
        if real != formula:
            mismatch += 1
            print(f"  불일치! kis={kis} real={real} formula={formula}")
    print(f"  check_multi_leaf_hub_parity() 공식 vs 실제 build_graph()+check_euler_condition(): "
          f"3-leaf 조합 {4**3}개 전수 대조 -> {'전부 일치(OK)' if mismatch == 0 else f'{mismatch}개 불일치(FAIL)'}")

    # find_hub_merge_candidates(): stack_id로 이미 stage별로 분리해놔도(현실적인 입력 상황을
    # 그대로 재현) 무시하고 hub 공유만으로 병합 후보를 찾아내는지 확인.
    circuit = [
        Transistor("M3", "pmos", source="vdd", drain="bias", gate="bias", w=30, finger_w=30/8, n_fingers=8, stack_id="stage1_load"),
        Transistor("M4", "pmos", source="vdd", drain="out1", gate="bias", w=30, finger_w=30/8, n_fingers=8, stack_id="stage1_load"),
        Transistor("M6", "pmos", source="vdd", drain="out2", gate="out1", w=90, finger_w=90/8, n_fingers=8, stack_id="stage2_gain"),
        Transistor("M1", "nmos", source="tail", drain="out1", gate="vin_p", w=60, n_fingers=6, stack_id="stage1_diffpair"),
        Transistor("M2", "nmos", source="tail", drain="d2", gate="vin_n", w=60, n_fingers=6, stack_id="stage1_diffpair"),
    ]
    candidates = find_hub_merge_candidates(circuit)
    vdd_group = candidates.get(("pmos", "vdd"))
    print(f"  find_hub_merge_candidates(): stack_id로 이미 stage1_load/stage2_gain으로 나뉜 M3/M4/M6를")
    print(f"  hub=vdd 공유만으로 다시 묶어내는가 -> "
          f"{'OK: ' + str(sorted(t.name for t in vdd_group)) if vdd_group and {t.name for t in vdd_group} == {'M3','M4','M6'} else 'FAIL'}")

    # 실제 병합: k=8(짝수)로 맞추면(§8 box-shape 탐색과 동일한 방식) 유효, k=7(홀수)이면 무효 —
    # 둘 다 공식과 실제 그래프 양쪽으로 재확인.
    for k, label in [(8, "짝수 k=8"), (7, "홀수 k=7")]:
        ts = [Transistor("M3", "pmos", source="vdd", drain="bias", n_fingers=k),
              Transistor("M4", "pmos", source="vdd", drain="out1", n_fingers=k),
              Transistor("M6", "pmos", source="vdd", drain="out2", n_fingers=k)]
        g = build_graph(ts)
        v = check_euler_condition(g)
        formula = check_multi_leaf_hub_parity({"M3": k, "M4": k, "M6": k})
        print(f"  {label}: 실제 그래프 판정={v.kind}(홀수차수 {len(v.odd_nodes)}개), "
              f"공식 판정={formula.kind}(m={formula.m_odd_leaves}) -> "
              f"{'OK' if (v.kind != 'impossible') == formula.ok else 'FAIL'}")
    print("  -> Maloberti 슬라이드가 '공통 finger 수 k'를 요구하는 이유가 단순 규칙이 아니라")
    print("  실제 그래프 이론(leaf 3개 이상이면 k는 짝수여야 함)이었음을 직접 확인.")

    print()
    print("=== Test 15: search_shared_finger_w() — 가로 배치(Case B) 탐색, Example 3로 정직하게 검증 ===")
    print("  Case A(search_stack_finger_w)는 n_fingers를 고정하고 stack마다 finger_w를 다르게")
    print("  찾아 세로로 쌓는다. Case B는 반대로 finger_w 하나를 stage 전체가 공유하고")
    print("  n_fingers를 자유도로 둬서 좌우로 배치한다 — schematic이 좌→우로 흐르면 이 모드가")
    print("  기본 후보다. 하지만 실제로 맞는지는 반드시 숫자로 확인해야 한다(가정 금지).")
    ex3_devices = {"M1": 13.252, "M1b": 2.384, "M1c": 2.384, "M2": 4.185, "M2b": 23.286,
                   "M2c": 23.286, "M3": 56.363, "M3b": 313.626, "M3c": 313.626}
    cands = search_shared_finger_w(ex3_devices, min_finger_w=0.4, max_finger_w=45.0)
    best = cands[0]
    width_ratio = max(best.n_fingers_per_device.values()) / min(best.n_fingers_per_device.values())
    print(f"  제약 없이 스냅 오차만 최소화: finger_w={best.finger_w:.4f}um, "
          f"최대 스냅오차={best.max_snap_error*100:.2f}% -> 오차는 작지만 행 폭 비율이 "
          f"{width_ratio:.0f}:1(M1b/M1c=4핑거 vs M3b/M3c={best.n_fingers_per_device['M3b']}핑거) "
          f"— 실무에서 못 쓸 정도로 한쪽 stage만 극단적으로 넓어진다.")
    capped = [c for c in cands
              if max(c.n_fingers_per_device.values()) / min(c.n_fingers_per_device.values()) <= 25]
    c25 = capped[0]
    print(f"  행 폭 비율을 25:1로 강제 제한: finger_w={c25.finger_w:.4f}um -> 이번엔 M1b/M1c "
          f"스냅오차가 {c25.snap_error_per_device['M1b']*100:.0f}%까지 뛴다(1개 finger로는 "
          f"2.384um를 도저히 못 맞춤) — 도저히 실무에서 쓸 수 없는 수준.")
    print(f"  -> 결론: Example 3는 gm3/gm1≈24배 차이 때문에 소자 W 범위가 130배(M1b 2.384um vs")
    print(f"  M3b 313.626um)까지 벌어져 있다 — schematic이 좌→우로 흐르는 3단 캐스케이드라도")
    print(f"  Case B(공통 finger_w 하나)를 전체에 적용하면 숫자가 안 맞는다는 게 직접 확인됐다.")
    print(f"  이번 세션에서 실제로 채택한 Case A(§8, load3만 4행으로 쪼갬)가 이 회로에는 맞는")
    print(f"  선택이었다 — schematic 방향은 출발 가설일 뿐, search_shared_finger_w()의")
    print(f"  최대 스냅오차/행폭비율 트레이드오프로 반드시 재확인해야 함을 보여주는 사례.")

    print()
    print("=== Test 16: run_full_circuit_audit() — 4단계 harness가 실제로 잡아내는지 확인 ===")
    print("  작은 합성 회로(2단 미러 M1/M2 + M3, diff 입력 M4/M5)로 4가지 실패 모드를 재현:")
    tiny_devices = {
        "M1": ("nmos", "gnd", "bias", "bias", "mirror"),
        "M2": ("nmos", "gnd", "out", "bias", "mirror"),
        "M3": ("nmos", "gnd", "out2", "Bias", "mirror"),   # 일부러 'Bias'(대문자) -- 대소문자 불일치 재현
        "M4": ("pmos", "tail", "out", "vip", "diffpair"),
        "M5": ("pmos", "tail", "out2", "vim", "diffpair"),
    }
    expected = {"mirror": 3, "diffpair": 2}

    print("  (a) 대소문자 불일치를 안 고치고, 판정도 안 채운 상태 -> 여러 항목 FAIL 기대:")
    r = run_full_circuit_audit(tiny_devices, expected, dispositions={})
    for c in r.checks:
        print(f"      [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")
    print(f"      전체 결과: {'PASS' if r.ok else 'FAIL'} -> "
          f"{'OK(의도대로 FAIL)' if not r.ok else 'FAIL(이 harness가 문제를 못 잡음)'}")

    print("  (b) net 이름을 정규화하고 모든 후보에 판정을 채운 뒤 -> 전부 PASS 기대:")
    fixed_devices = dict(tiny_devices)
    fixed_devices["M3"] = ("nmos", "gnd", "out2", "bias", "mirror")  # 대소문자 수정
    dispositions = {
        ("current_mirror", "nmos", "bias"): ("real_match", "M1/M2/M3 3-way mirror, gate=bias"),
        ("hub_merge", "nmos", "gnd"): ("real_match", "공유 rail, 병합 불필요"),
        ("hub_merge", "pmos", "tail"): ("real_match", "M4/M5 diff pair tail, 이미 매칭 처리"),
        ("hub_merge", "pmos", "out"): ("false_positive_coincidental", "합성 예제용 — 실제 회로 아님"),
    }
    r2 = run_full_circuit_audit(fixed_devices, expected, dispositions)
    for c in r2.checks:
        print(f"      [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")
    print(f"      전체 결과: {'PASS' if r2.ok else 'FAIL'} -> "
          f"{'OK' if r2.ok else 'FAIL(예상과 다름 — dispositions 키를 재확인할 것)'}")

    print()
    print("=== Test 17: pack_floorplan() — 실제 Xie&Chen 51-소자 회로 전체 블록으로 검증 ===")
    print("  (첫 버전은 spine을 세로 한 줄로 쌓기만 해 빈 공간이 많았다 -- 사용자가 직접 지적한")
    print("  뒤 skyline/bottom-left 2D packing으로 재작성. 여기서 실측으로 개선을 확인한다.)")
    def _blk(name, row_fingers):
        """block_from_rows() 자체 self-test 헬퍼(2026-08-13 세션31) -- finger_w=l=1.0
        균일값을 쓰면 width_m=n_fingers, height_m=행 개수가 그대로 나와 옛
        block_from_row_widths({row: n_fingers}) 리터럴 dict 시대의 수치를 그대로 재현한다
        (이 Test 17은 pack_floorplan()의 패킹 알고리즘 자체를 검증하는 것이 목적이라
        실제 물리 치수 정확도는 무관 -- 상대적 크기 관계만 보존하면 충분)."""
        rows_ = {rn: [Transistor(f"{name}_{rn}", "nmos", source="s", drain="d",
                                   n_fingers=n, finger_w=1.0, l=1.0)]
                 for rn, n in row_fingers.items()}
        return block_from_rows(name, rows_)

    spine = [
        _blk("S1_PMOS", {"row0": 8, "row1": 8}),
        _blk("S1_NMOS", {"row0": 8, "row1": 8}),
        _blk("S1_TAILP", {"row0": 10}),
        _blk("S1_TAILN", {"row0": 7}),
        _blk("biasgen_pmos", {"row0": 5}),
        _blk("biasgen_nmos", {"row0": 4}),
        _blk("cmfb_p1", {"row0": 2}),
        _blk("cmfb_p2", {"row0": 1}),
        _blk("cmfb_n1", {"top": 2, "bot": 2}),
        _blk("cmfb_n2", {"row0": 2}),
    ]
    mirror_pairs = [
        (_blk("classab_p1", {"row0": 3}), _blk("classabL_p1", {"row0": 3})),
        (_blk("classab_p2", {"row0": 2}), _blk("classabL_p2", {"row0": 2})),
        (_blk("classab_n1_new", {"row0": 2}), _blk("classabL_n1_new", {"row0": 2})),
        (_blk("classab_n2_new", {"row0": 2}), _blk("classabL_n2_new", {"row0": 2})),
        (_blk("classab_n_mirror", {"top": 2, "bot": 2}), _blk("classabL_n_mirror", {"top": 2, "bot": 2})),
        (_blk("S2_M15", {"row0": 1}), _blk("S2_M25", {"row0": 1})),
        (_blk("S2_M16", {"row0": 1}), _blk("S2_M26", {"row0": 1})),
    ]
    r3 = pack_floorplan(spine, mirror_pairs, gap=1.0)

    # 겹침 검증 -- packing이 실제로 유효한지(어떤 두 블록도 겹치지 않는지) 직접 확인
    def overlap(a, b):
        return not (a.x + a.width <= b.x or b.x + b.width <= a.x or
                    a.y + a.height <= b.y or b.y + b.height <= a.y)
    names = list(r3.placements)
    n_overlaps = sum(1 for i in range(len(names)) for j in range(i+1, len(names))
                      if overlap(r3.placements[names[i]], r3.placements[names[j]]))
    print(f"  overlap check: {n_overlaps}개 쌍 겹침 -> {'OK(겹침 없음)' if n_overlaps == 0 else 'FAIL'}")
    print(f"  bbox={r3.bbox_width:.1f}x{r3.bbox_height:.1f}, aspect_ratio={r3.aspect_ratio:.2f}, "
          f"packing_density={r3.packing_density*100:.1f}%, symmetry_max_error={r3.symmetry_max_error:.3f}")
    print(f"  -> {'OK(대칭 완전 보존)' if r3.symmetry_max_error == 0 else '비대칭 감지(강제로 안 맞춤)'}, "
          f"{'OK(box-shape 목표 <=1.5 충족)' if r3.aspect_ratio <= 1.5 else 'box-shape 목표 초과 -- row_split_candidates 확인 필요'}")
    if r3.row_split_candidates:
        print("  row-split 후보(§8.5/§1.7로 재검토 필요):")
        for c in r3.row_split_candidates:
            print(f"    {c['name']}: {c['reason']}")
    else:
        print("  row-split 후보 없음 -- 특정 행 하나가 전체 비율을 지배하지 않음")

    print("  대칭 깨진 경우도 확인(좌우 크기 다르게):")
    asym_pairs = [(_blk("R", {"row0": 5}), _blk("L", {"row0": 3}))]
    r4 = pack_floorplan([], asym_pairs, gap=1.0)
    print(f"  symmetry_max_error={r4.symmetry_max_error:.3f} -> "
          f"{'OK(비대칭을 있는 그대로 보고)' if r4.symmetry_max_error == 2.0 else 'FAIL'}")

    print()
    print("=== Test 18: find_diffusion_safe_split_points() — 실제 S1_TAILP 시퀀스로 검증 ===")
    print("  사용자 지적: \"packing할 때 MOS의 diffusion 영역이 고려돼서 엉뚱하게 split되는")
    print("  문제가 없도록 해야 한다\" -- 실제 S1_TAILP(M6:M7 tail, 이 세션에서 실제")
    print("  build_stick_diagram()이 반환한 시퀀스)로 확인.")
    s1_tailp_seq = ["M6","M6","M6","M6","M7","M6","M7","M6","M7","M6"]  # stick_stage1_results.json 실측값
    pts = find_diffusion_safe_split_points(s1_tailp_seq)
    print(f"  S1_TAILP 시퀀스 {s1_tailp_seq}")
    print(f"  안전 분할 지점: {pts} -> {'OK(안전 지점 없음 -- M6/M7이 완전히 인터리브돼 어디를 잘라도 소자가 갈라짐)' if pts == [] else 'FAIL(있으면 안 되는데 나옴)'}")

    biasgen_seq = ["M29","M28","M27","M33","M34"]  # 실제 biasgen_pmos 시퀀스(서로 다른 소자가 순서대로만 연결)
    pts2 = find_diffusion_safe_split_points(biasgen_seq)
    print(f"  biasgen_pmos 시퀀스 {biasgen_seq}")
    print(f"  안전 분할 지점: {pts2} -> {'OK(각 소자가 통째로 한쪽에만 있는 지점 존재)' if pts2 else 'FAIL'}")

    print("\n  evaluate_row_split_candidates()에 실제 시퀀스를 줬을 때 vs 안 줬을 때:")
    dominant_block = FloorplanBlock("S1_TAILP", 10, 1)
    seqs = {"S1_TAILP": s1_tailp_seq}
    cands_checked = evaluate_row_split_candidates([dominant_block], bbox_width=12, bbox_height=13,
                                                    dominance_ratio=0.6, transistor_sequences=seqs)
    cands_unchecked = evaluate_row_split_candidates([dominant_block], bbox_width=12, bbox_height=13,
                                                      dominance_ratio=0.6)
    print(f"  시퀀스 제공: diffusion_check={cands_checked[0]['diffusion_check']}, "
          f"splittable={cands_checked[0]['splittable']} -> "
          f"{'OK' if cands_checked[0]['splittable'] is False else 'FAIL'}")
    print(f"  시퀀스 미제공: diffusion_check={cands_unchecked[0]['diffusion_check']}, "
          f"splittable={cands_unchecked[0]['splittable']} -> "
          f"{'OK(정직하게 미확인으로 표시)' if cands_unchecked[0]['diffusion_check']=='not_verified' else 'FAIL'}")

    print("\n  skyline_pack_best_width() 단독 사용(대칭쌍 없는 단일 그룹 packing):")
    solo_placements, sw, sh = skyline_pack_best_width(spine, gap=1.0)
    solo_overlaps = sum(1 for i,a in enumerate(solo_placements.values())
                         for j,b in enumerate(solo_placements.values()) if i<j and overlap(a,b))
    print(f"  spine 단독: bbox={sw:.1f}x{sh:.1f}, overlap={solo_overlaps} -> "
          f"{'OK' if solo_overlaps==0 else 'FAIL'}")

    print()
    print("=== Test 19: pack_floorplan_grouped() — 기능 그룹이 실제로 흩어지지 않는지 확인 ===")
    print("  사용자 지적: \"cmfb_n1은 왜 어중간하게 중간에 배치돼 있지?\" -- pack_floorplan()이")
    print("  평평한 spine 리스트를 순수 공간 최적화로만 packing해서, CMFB의 나머지 행들과")
    print("  떨어져 Stage-1 사이에 끼어드는 실제 결과가 나왔었다. 그룹 단위 packing으로 재검증.")
    spine_groups = {
        "stage1": [b for b in spine if b.name.startswith("S1_")],
        "biasgen": [b for b in spine if b.name.startswith("biasgen_")],
        "cmfb": [b for b in spine if b.name.startswith("cmfb_")],
    }
    r5 = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0)
    n_ov5 = sum(1 for i in range(len(list(r5.placements))) for j in range(i+1, len(list(r5.placements)))
                if overlap(r5.placements[list(r5.placements)[i]], r5.placements[list(r5.placements)[j]]))
    print(f"  overlap check: {n_ov5} -> {'OK' if n_ov5==0 else 'FAIL'}")
    print(f"  bbox={r5.bbox_width:.1f}x{r5.bbox_height:.1f}, aspect_ratio={r5.aspect_ratio:.2f}, "
          f"packing_density={r5.packing_density*100:.1f}%, symmetry_max_error={r5.symmetry_max_error:.3f}")

    def group_is_contiguous(names):
        ys = sorted((r5.placements[n].y, r5.placements[n].y + r5.placements[n].height) for n in names)
        # 그룹 내 y-구간들이 서로 붙어있거나 겹치는지(gap<=1.01) 확인 -- 완전히 흩어졌으면 FAIL
        for k in range(len(ys) - 1):
            if ys[k+1][0] - ys[k][1] > 1.01:
                return False
        return True

    for gname, members in [("stage1", ["S1_PMOS","S1_NMOS","S1_TAILP","S1_TAILN"]),
                            ("biasgen", ["biasgen_pmos","biasgen_nmos"]),
                            ("cmfb", ["cmfb_p1","cmfb_p2","cmfb_n1","cmfb_n2"])]:
        ok = group_is_contiguous(members)
        print(f"  group '{gname}' stays contiguous (no unrelated block sandwiched in): "
              f"{'OK' if ok else 'FAIL'}")

    print()
    print("=== Test 20: net_weights — 신호선 근접 배치, 실제 vbias1 연결로 검증 ===")
    print("  사용자 지적: \"배치는 신호선과 근접한 곳에 위치시키면 좋겠어, routing delay가")
    print("  없어지지.\" -- bias-gen(vbias1 소스)과 classab_p2(M8/M13, vbias1을 게이트로")
    print("  읽는 소자)가 실제로는 10칸이나 떨어져 있었다(사&sect;7은 '바로 옆에 둬야 한다'고")
    print("  이미 명시했었는데 &sect;8 좌표는 이를 전혀 반영 못 했다).")
    net_weights = {
        "biasgen": {"stage1": 4.0, "cmfb": 1.0}, "stage1": {"biasgen": 4.0, "cmfb": 1.0},
        "cmfb": {"biasgen": 1.0, "stage1": 1.0},
        "classab_p2": {"biasgen": 2.0}, "classab_n1_new": {"biasgen": 1.0},
    }
    r6_before = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0)
    r6_after = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights)
    dist_before = abs(r6_before.placements["biasgen_pmos"].y - r6_before.placements["classab_p2"].y)
    dist_after = abs(r6_after.placements["biasgen_pmos"].y - r6_after.placements["classab_p2"].y)
    print(f"  net_weights 없음: biasgen<->classab_p2 y거리={dist_before:.1f}, "
          f"bbox={r6_before.bbox_width:.1f}x{r6_before.bbox_height:.1f}, aspect={r6_before.aspect_ratio:.2f}")
    print(f"  net_weights 적용: biasgen<->classab_p2 y거리={dist_after:.1f}, "
          f"bbox={r6_after.bbox_width:.1f}x{r6_after.bbox_height:.1f}, aspect={r6_after.aspect_ratio:.2f}")
    print(f"  -> {'OK(거리 개선, box-shape 목표(<=1.5) 안에서)' if dist_after < dist_before and r6_after.aspect_ratio <= 1.5 else 'FAIL'}")

    n_ov6 = sum(1 for i,a in enumerate(list(r6_after.placements.values()))
                for j,b in enumerate(list(r6_after.placements.values())) if i<j and overlap(a,b))
    print(f"  overlap check (net_weights 적용 후): {n_ov6} -> {'OK' if n_ov6==0 else 'FAIL'}")
    for gname, members in [("stage1", ["S1_PMOS","S1_NMOS","S1_TAILP","S1_TAILN"]),
                            ("biasgen", ["biasgen_pmos","biasgen_nmos"]),
                            ("cmfb", ["cmfb_p1","cmfb_p2","cmfb_n1","cmfb_n2"])]:
        ys = sorted((r6_after.placements[n].y, r6_after.placements[n].y + r6_after.placements[n].height) for n in members)
        ok = all(ys[k+1][0] - ys[k][1] <= 1.01 for k in range(len(ys)-1))
        print(f"  group '{gname}' still contiguous after net_weights: {'OK' if ok else 'FAIL'}")

    print()
    print("=== Test 21: sub_kind — 같은 diffusion(폴러리티)별로 나눠 배치하면 더 compact한지 실측 ===")
    print("  사용자 제안: \"cmfb_n1은 top/bot 합친 것인데, 다른 cmfb 행과 높이 맞춰 옆으로 배치하면")
    print("  P/N 영역이 구분되면서 더 compact해지지 않을까 -- 확인하는 기능도 보강해달라.\"")
    sub_kind_stage1 = {"S1_PMOS":"pmos","S1_TAILP":"pmos","S1_NMOS":"nmos","S1_TAILN":"nmos"}
    flat_s1, _ = pack_group_as_unit("stage1", [b for b in spine if b.name.startswith("S1_")], gap=1.0)
    ratio_flat = max(flat_s1.width,flat_s1.height)/min(flat_s1.width,flat_s1.height)
    kind_result = _pack_by_subkind([b for b in spine if b.name.startswith("S1_")], sub_kind_stage1, gap=1.0)
    _, kind_internal = kind_result
    kw = max(p.x+p.width for p in kind_internal.values()); kh = max(p.y+p.height for p in kind_internal.values())
    ratio_kind = max(kw,kh)/min(kw,kh)
    print(f"  Stage-1 단독: flat={flat_s1.width:.0f}x{flat_s1.height:.0f}(ratio={ratio_flat:.2f}) vs "
          f"by-kind={kw:.0f}x{kh:.0f}(ratio={ratio_kind:.2f})")
    print(f"  -> flat이 이미 거의 정사각형(1.11), by-kind는 P열/N열을 옆으로 붙이며 옆으로 길쭉해짐")
    print(f"  (4.75) -- 초기엔 '그룹 자체 밀도'로 골랐다가 이 사례에서 전체 회로 aspect ratio가")
    print(f"  오히려 악화되는 걸 발견하고 ratio 기준으로 바꿨다 -- 아래에서 전체 회로로 재확인)")

    r7_before = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights)
    r7_after = pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, net_weights=net_weights,
                                        sub_kinds={"stage1": sub_kind_stage1,
                                                    "cmfb": {"cmfb_p1":"pmos","cmfb_p2":"pmos",
                                                             "cmfb_n1":"nmos","cmfb_n2":"nmos"}})
    print(f"  전체 회로: sub_kinds 없음 bbox={r7_before.bbox_width:.1f}x{r7_before.bbox_height:.1f} "
          f"aspect={r7_before.aspect_ratio:.2f} density={r7_before.packing_density*100:.1f}%")
    print(f"  전체 회로: sub_kinds 적용 bbox={r7_after.bbox_width:.1f}x{r7_after.bbox_height:.1f} "
          f"aspect={r7_after.aspect_ratio:.2f} density={r7_after.packing_density*100:.1f}%")
    same = (abs(r7_before.aspect_ratio - r7_after.aspect_ratio) < 0.01)
    print(f"  -> {'OK(ratio 기준 선택이 Stage-1의 해로운 by-kind 분할을 올바르게 거부, 결과 동일 유지)' if same else '결과가 달라짐 -- 개별 확인 필요'}")
    n_ov7 = sum(1 for i,a in enumerate(list(r7_after.placements.values()))
                for j,b in enumerate(list(r7_after.placements.values())) if i<j and overlap(a,b))
    print(f"  overlap check: {n_ov7} -> {'OK' if n_ov7==0 else 'FAIL'}")

    print()
    print("=== Test 21.5: check_symmetry_dispositions() — 매칭 후보를 조용히 빼먹는 것 차단 ===")
    print("  2026-07-28 신설(사용자 지적): find_matching_candidates()는 '후보'만 낸다 --")
    print("  AI가 그 후보를 실제로 채택/기각 판단해서 기록했는지, 조용히 빠뜨린 후보는 없는지")
    print("  run_full_circuit_audit() 3번 체크(매 candidate는 disposition을 가져야 함)와")
    print("  똑같은 원리를 topology-authoring 단계(가벼운 인자로)에 적용한다.")
    vsd_trs = [
        Transistor("MA", "nmos", source="tail", drain="outA", gate="vip"),
        Transistor("MB", "nmos", source="tail", drain="outB", gate="vim"),
        Transistor("MC", "nmos", source="gnd", drain="tail", gate="bias"),
    ]
    # MA/MB(diff_pair, source=tail 공유)와 MC는 서로 무관 -- MC는 그냥 tail 전류원이라
    # find_matching_candidates()의 diff_pair 후보엔 안 잡히지만(gate가 다르고 source가
    # 다름), 아래에서 일부러 MA/MB 후보를 matching_pairs에서 빼먹은 상황을 재현한다.
    print("  [MA/MB(진짜 diff_pair)를 matching_pairs에 빼먹은 상황]")
    v1 = check_symmetry_dispositions(vsd_trs, matching_pairs=[])
    print(f"  ok={v1.ok} (빠뜨린 후보가 있으니 FAIL이어야 정상)")
    for u in v1.undisposed:
        print(f"    UNDISPOSED: {u}")
    assert not v1.ok, "빼먹은 후보를 잡아내지 못했다"

    print("  [MA/MB를 matching_pairs에 정상 기록하면 PASS]")
    v2 = check_symmetry_dispositions(vsd_trs, matching_pairs=[{"names": ["MA", "MB"], "kind": "diff_pair"}])
    print(f"  ok={v2.ok}")
    assert v2.ok

    print("  [net 이름 대소문자 불일치(사고9와 동일 패턴)를 잡아내는지 -- Vbias1 vs vbias1]")
    vsd_case_trs = [
        Transistor("MX", "pmos", source="vdd", drain="outA", gate="Vbias1"),
        Transistor("MY", "pmos", source="vdd", drain="outB", gate="vbias1"),  # 같은 net, 다른 표기
    ]
    v_case = check_symmetry_dispositions(vsd_case_trs, matching_pairs=[])
    print(f"  ok={v_case.ok} (대소문자 차이가 있으니 FAIL이어야 정상)")
    print(f"  case_collisions={v_case.case_collisions}")
    assert not v_case.ok and v_case.case_collisions, \
        "대소문자 불일치(사고9와 동일 패턴)를 잡아내지 못했다"

    print("  [실전: current_reuse_telescopic_ota.topology.json 전체 재검증]")
    import os as _os21
    _lib21 = _os21.path.join(_os21.path.dirname(_os21.path.abspath(__file__)), "library")
    _telescopic_trs, _telescopic_meta = load_topology(
        _os21.path.join(_lib21, "current_reuse_telescopic_ota.topology.json"))
    _telescopic_pairs = _telescopic_meta["symmetry"]["matching_pairs"]
    _telescopic_disp_list = _telescopic_meta["symmetry"].get("dispositions", [])
    _telescopic_disp = {(d["tag"], d["kind"], d["key"]): (d["category"], d["reason"])
                         for d in _telescopic_disp_list}
    v3 = check_symmetry_dispositions(_telescopic_trs, _telescopic_pairs, _telescopic_disp)
    print(f"  ok={v3.ok} (41개 소자, {len(_telescopic_pairs)}개 matching_pairs + "
          f"{len(_telescopic_disp_list)}개 dispositions로 전부 처리됨)")
    assert v3.ok, f"telescopic OTA topology JSON에 미처리 후보가 남아있다: {v3.undisposed}"

    print()
    print("  [linked_topology_files -- 회로가 여러 파일로 쪼개져도 항상 전체를 합쳐서 보는지]")
    print("  2026-07-28 신설(사용자 지적, PRE-FLIGHT 사고8 재발 방지): sub-block별로 파일을")
    print("  나눠도 어느 파일을 진입점으로 읽든 형제 파일 전부가 자동으로 합쳐져야 한다.")
    import tempfile as _tempfile21
    with _tempfile21.TemporaryDirectory() as _tmpdir21:
        _partA = {
            "schema_version": "2.0", "topology_name": "demo_partA", "source": "self-test synthetic",
            "compensation": None,
            "netlist": [{"name": "MSIG", "kind": "nmos", "source": "gnd", "drain": "out", "gate": "vbias_shared"}],
            "symmetry": {"matching_pairs": [], "dispositions": []},
            "linked_topology_files": ["partB.topology.json"],
        }
        _partB = {
            "schema_version": "2.0", "topology_name": "demo_partB", "source": "self-test synthetic",
            "compensation": None,
            "netlist": [
                {"name": "MBIAS1", "kind": "nmos", "source": "gnd", "drain": "vbias_shared", "gate": "vbias_shared"},
                {"name": "MBIAS2", "kind": "nmos", "source": "gnd", "drain": "x", "gate": "vbias_shared"},
            ],
            "symmetry": {"matching_pairs": [], "dispositions": []},
            "linked_topology_files": ["partA.topology.json"],
        }
        _pathA = _os21.path.join(_tmpdir21, "partA.topology.json")
        _pathB = _os21.path.join(_tmpdir21, "partB.topology.json")
        with open(_pathA, "w", encoding="utf-8") as f:
            json.dump(_partA, f)
        with open(_pathB, "w", encoding="utf-8") as f:
            json.dump(_partB, f)

        _linked_trs, _linked_meta = load_topology(_pathA)  # partA만 진입점으로 읽음
        print(f"  partA만 읽었는데 로드된 소자 수: {len(_linked_trs)} "
              f"({[t.name for t in _linked_trs]}) -- partB가 자동으로 합쳐졌어야 함")
        assert len(_linked_trs) == 3, "linked_topology_files를 따라가 병합하지 못했다"

        _linked_candidates = find_matching_candidates(_linked_trs)
        _cross_file_group = _linked_candidates["current_mirror"].get(("nmos", "vbias_shared"))
        print(f"  cross-file matching 후보(MSIG는 partA, MBIAS1/2는 partB): "
              f"{[t.name for t in _cross_file_group] if _cross_file_group else None}")
        assert _cross_file_group and len(_cross_file_group) == 3, \
            "파일을 쪼갰더니 cross-file matching 관계를 다시 놓쳤다 -- 사고8 재발"
        print("  PASS: 파일을 쪼개도 사고8(cross-block 매칭 관계 누락)이 재발하지 않는다")

    print()
    print("=== Test 22: audit_row_split() — Euler/box-shape만으론 못 잡는 matching 회귀 실측 ===")
    print("  사용자 지적: \"matching pattern은 왜 적용이 안 됐지?\" -- folded_cascode_example()의")
    print("  top/bot을 2행으로 나눌 때 M3는 row0 통째로, M4는 row1 통째로 배치했다. Euler 조건과")
    print("  box-shape는 둘 다 PASS였지만 전류거울 쌍(M3/M4, source=vdd 공유)이 완전히 분리돼")
    print("  interdigitation/common-centroid가 전혀 없었다 -- 이후 사용자가 한 번 더 지적:")
    print("  \"interdigitation과 common-centroid 둘 다 살펴보는 과정을 추가하라 했는데 하나만")
    print("  하면 어떡하냐\" -- 3b(행 내부 인접성)와 3c(전체 무게중심 일치)를 별개 체크로 분리.")
    old_top_row0 = [
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="old_row0"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=3,stack_id="old_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=6,stack_id="old_row0"),
    ]
    old_top_row1 = [
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="old_row1"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=3,stack_id="old_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=6,stack_id="old_row1"),
    ]
    old_audit = audit_row_split({"old_row0": old_top_row0, "old_row1": old_top_row1},
                                  matching_pairs=[("M3", "M4")],
                                  pair_sensitivity={("M3", "M4"): "ratio"})
    print(f"  [회귀 재현] M3 row0 통째로/M4 row1 통째로: overall={'OK(FAIL, 의도대로 검출됨)' if not old_audit.ok else 'FAIL(놓침!)'}")
    for c in old_audit.checks:
        if c.name.startswith("3"):
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    cc34 = common_centroid_layout([
        Transistor("M3", "pmos", source="vdd", drain="X", n_fingers=3),
        Transistor("M4", "pmos", source="vdd", drain="Y", n_fingers=3),
    ])
    a34_r0 = cc34["rows"][0]["transistor_sequence"].count("M3")
    b34_r0 = cc34["rows"][0]["transistor_sequence"].count("M4")
    a34_r1 = cc34["rows"][1]["transistor_sequence"].count("M3")
    b34_r1 = cc34["rows"][1]["transistor_sequence"].count("M4")
    fixed_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r0,stack_id="fix_row0"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r0,stack_id="fix_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=6,stack_id="fix_row0"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="fix_row0"),
    ]
    fixed_top_row1 = [
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r1,stack_id="fix_row1"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r1,stack_id="fix_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=6,stack_id="fix_row1"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="fix_row1"),
    ]
    fixed_audit = audit_row_split({"fix_row0": fixed_top_row0, "fix_row1": fixed_top_row1},
                                    matching_pairs=[("M3", "M4")],
                                    pair_sensitivity={("M3", "M4"): "ratio"})
    print(f"  [common_centroid_layout로 재구성] overall={'OK' if fixed_audit.ok else 'FAIL'}")
    for c in fixed_audit.checks:
        if c.name.startswith("3"):
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    print()
    print("  [kind-aware 재판정 -- two_stage_ota_example() top(M3/M4=2f+2f) + M6(8f)] 사용자의")
    print("  세 번째 지적(\"mirror는 interdigitation이 적합, 차동쌍은 common-centroid가 필요 --")
    print("  기존 §2.7 기준을 왜 안 쓰나\")을 반영하기 전에는, M3/M4의 common-centroid dx=1.0을")
    print("  '해결 안 된 한계'로 오판했었다 -- 하지만 M3/M4는 gate=D3를 공유하는 전류거울이지")
    print("  차동쌍이 아니다. §2.7 기준대로 kind=current_mirror면 interdigitation만 필수이고")
    print("  common-centroid는 참고용이므로, dx=1.0은 애초에 실패가 아니라 잘못된 기준을 적용해")
    print("  생긴 오탐이었다 -- kind-aware 판정으로 바로잡는다.")
    small_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="D3",gate="D3",n_fingers=2,stack_id="small_row0"),
        Transistor("M4","pmos",source="vdd",drain="O1",gate="D3",n_fingers=2,stack_id="small_row0"),
        Transistor("M6","pmos",source="vdd",drain="OUT",gate="O1",n_fingers=2,stack_id="small_row0"),
    ]
    small_top_row1 = [
        Transistor("M6","pmos",source="vdd",drain="OUT",gate="O1",n_fingers=6,stack_id="small_row1"),
    ]
    small_audit = audit_row_split({"small_row0": small_top_row0, "small_row1": small_top_row1},
                                    matching_pairs=[("M3", "M4")],
                                    pair_sensitivity={("M3", "M4"): "ratio"})
    print(f"  overall={'OK(sensitivity=ratio+shares_node -> interdigitation만 필수, 정확히 통과)' if small_audit.ok else 'FAIL'}")
    for c in small_audit.checks:
        if c.name.startswith("3"):
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    print()
    print("  [대조군 -- 진짜 차동쌍이 common-centroid를 실패하면 이번엔 진짜로 FAIL해야 한다]")
    diffpair_bad_row0 = [
        Transistor("MX","nmos",source="tail2",drain="da",gate="vp",n_fingers=1,stack_id="dp_row0"),
        Transistor("MY","nmos",source="tail2",drain="db",gate="vn",n_fingers=3,stack_id="dp_row0"),
    ]
    diffpair_bad_row1 = [
        Transistor("MX","nmos",source="tail2",drain="da",gate="vp",n_fingers=3,stack_id="dp_row1"),
        Transistor("MY","nmos",source="tail2",drain="db",gate="vn",n_fingers=1,stack_id="dp_row1"),
    ]
    diffpair_audit = audit_row_split({"dp_row0": diffpair_bad_row0, "dp_row1": diffpair_bad_row1},
                                       matching_pairs=[("MX", "MY")],
                                       pair_sensitivity={("MX", "MY"): "offset"})
    print(f"  overall={'FAIL(sensitivity=offset -> common-centroid 필수, 의도대로 검출됨)' if not diffpair_audit.ok else 'OK(놓침!)'}")
    for c in diffpair_audit.checks:
        if c.name.startswith("3"):
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    print()
    print("=== Test 23: branch_symmetric kind — M5/M6, M7/M8 (공유 노드 없는 캐스코드 대칭쌍) ===")
    print("  사용자 지적: \"bot_row0/row1에서 M7과 M8은 왜 한군데 몰아두었지?\" -- 확인해보니 M7/M8을")
    print("  matching_pairs에 넣어본 적이 없었다(M9/M10만 확인). §2.6 재확인: M5/M6, M7/M8은 gate만")
    print("  공유하고 source/drain은 서로 완전히 다르다(공유 노드 0개) -- M3/M4(source=vdd 공유)와")
    print("  다른 하위 종류다.")
    cc34_2 = common_centroid_layout([
        Transistor("M3", "pmos", source="vdd", drain="X", n_fingers=3),
        Transistor("M4", "pmos", source="vdd", drain="Y", n_fingers=3),
    ])
    a34_r0b = cc34_2["rows"][0]["transistor_sequence"].count("M3")
    b34_r0b = cc34_2["rows"][0]["transistor_sequence"].count("M4")
    a34_r1b = cc34_2["rows"][1]["transistor_sequence"].count("M3")
    b34_r1b = cc34_2["rows"][1]["transistor_sequence"].count("M4")

    print("  [1차: M5/M6 통째로 한 컬럼씩(solo)] -- 전수 탐색으로 interdigitation(3b)이 그래프상")
    print("  0건임을 먼저 확인했지만, solo 배치 자체의 common-centroid(3c)를 계산해보니 FAIL이었다:")
    solo_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r0b,stack_id="solo_row0"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r0b,stack_id="solo_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=6,stack_id="solo_row0"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="solo_row0"),
    ]
    solo_top_row1 = [
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r1b,stack_id="solo_row1"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r1b,stack_id="solo_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=6,stack_id="solo_row1"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="solo_row1"),
    ]
    solo_audit = audit_row_split({"solo_row0": solo_top_row0, "solo_row1": solo_top_row1},
                                   matching_pairs=[("M3", "M4"), ("M5", "M6")],
                                   pair_sensitivity={("M3", "M4"): "ratio", ("M5", "M6"): "ratio"})
    print(f"  overall={'OK' if solo_audit.ok else 'FAIL(solo 배치의 common-centroid 미달, 의도대로 검출됨)'}")
    for c in solo_audit.checks:
        if "M5/M6" in c.name:
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    print()
    print("  [사용자 재지적: \"differential pair처럼 stack 분리+finger 조절로 common-centroid를")
    print("  만들 수 있잖아\" -- M5/M6도 양쪽 행에 swap-대칭으로 나눠 분배해 재시도(M5=2/4, M6=4/2,")
    print("  swap). interdigitation(그래프상 인접)은 여전히 불가능하지만 common-centroid(전체")
    print("  무게중심)는 이 분배로 실제 달성됨을 확인:")
    dist_top_row0 = [
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r0b,stack_id="dist_row0"),
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r0b,stack_id="dist_row0"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=2,stack_id="dist_row0"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=4,stack_id="dist_row0"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="dist_row0"),
    ]
    dist_top_row1 = [
        Transistor("M4","pmos",source="vdd",drain="Y",gate="bias2",n_fingers=b34_r1b,stack_id="dist_row1"),
        Transistor("M3","pmos",source="vdd",drain="X",gate="bias2",n_fingers=a34_r1b,stack_id="dist_row1"),
        Transistor("M6","pmos",source="Y",drain="outB",gate="bias3",n_fingers=2,stack_id="dist_row1"),
        Transistor("M5","pmos",source="X",drain="outA",gate="bias3",n_fingers=4,stack_id="dist_row1"),
        Transistor("MP","pmos",source="vdd",drain="tail",gate="bias1",n_fingers=1,stack_id="dist_row1"),
    ]
    dist_audit = audit_row_split({"dist_row0": dist_top_row0, "dist_row1": dist_top_row1},
                                   matching_pairs=[("M3", "M4"), ("M5", "M6")],
                                   pair_sensitivity={("M3", "M4"): "ratio", ("M5", "M6"): "ratio"})
    print(f"  overall={'OK(swap-분배로 common-centroid 실제 달성)' if dist_audit.ok else 'FAIL'}")
    for c in dist_audit.checks:
        if c.name.startswith("3"):
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    print()
    print("  [대조군 -- 진짜 finger 수가 안 맞는 branch_symmetric 쌍은 여전히 FAIL해야 한다]")
    mismatched_row0 = [
        Transistor("MA","pmos",source="p1",drain="d1",gate="g",n_fingers=4,stack_id="bad_row0"),
    ]
    mismatched_row1 = [
        Transistor("MB","pmos",source="p2",drain="d2",gate="g",n_fingers=6,stack_id="bad_row1"),
    ]
    mismatched_audit = audit_row_split({"bad_row0": mismatched_row0, "bad_row1": mismatched_row1},
                                         matching_pairs=[("MA", "MB")],
                                         pair_sensitivity={("MA", "MB"): "ratio"})
    print(f"  overall={'FAIL(finger 수 4 != 6 -- 진짜 mirror 짝이 아님, 의도대로 검출됨)' if not mismatched_audit.ok else 'OK(놓침!)'}")
    for c in mismatched_audit.checks:
        if c.name.startswith("3"):
            print(f"    [{'PASS' if c.ok else 'FAIL'}] {c.name}: {c.detail}")

    print()
    print("=== Test 24: check_walk_sequence() — 제안된 순서가 실제로 이어지는지 독립 검산 ===")
    print("  사용자 제안: \"top_row0를 M3,M4,M6,M6,M5,MP,M5,M6,M6,M4처럼 섞을 수는 없나?\" --")
    print("  finger 개수는 실제 채택안(dist_top_row0)과 정확히 같지만, 직접 그래프를 추적해보니")
    print("  M6,M6로 Y에 돌아온 뒤 M5(X/outA에만 닿음)로 못 넘어가 4번째 단계에서 끊긴다 --")
    print("  X/Y는 vdd를 거쳐야만 이어지는데 이 순서는 중간에 vdd를 거치지 않았기 때문이다.")
    proposed_row0 = ["M3","M4","M6","M6","M5","MP","M5","M6","M6","M4"]
    v = check_walk_sequence(proposed_row0, dist_top_row0)
    print(f"  proposed row0 ok={v.ok}"
          f"{', break_index='+str(v.break_index)+' reason='+v.break_reason if not v.ok else ''}")

    print("  대조: 실제 채택된 순서(dist_top_row0의 실제 build_stick_diagram() 결과)는 당연히 이어진다:")
    real_seq = build_stick_diagram(dist_top_row0)["dist_row0"].transistor_sequence
    v2 = check_walk_sequence(real_seq, dist_top_row0)
    print(f"  real sequence {real_seq}: ok={v2.ok}, node_path={v2.node_path}")

    print()
    print("  [finger 개수 자체가 안 맞는 경우도 잡아내는지 확인]")
    v3 = check_walk_sequence(["M3","M4","M5","M6","MP"], dist_top_row0)  # 각 1번씩만, 실제 개수와 다름
    print(f"  개수 불일치 시퀀스: ok={v3.ok}, finger_count_mismatch={v3.finger_count_mismatch}")

    print()
    print("=== Test 25: check_stick_diagram_coverage() — sizing은 됐는데 layout이 통째로 빠짐 방지 ===")
    print("  실제 사고(2026-07-28, 힌트 없는 fresh agent 재현 테스트): current-reuse telescopic")
    print("  OTA 리포트에서 21개 소자 전부 gm/ID sizing은 됐는데, CMFB/bias-gen/Class-AB 9개")
    print("  소자는 stick diagram(물리 행)이 아예 없이 '완료'로 게시됐다 -- run_full_circuit_audit를")
    print("  import만 하고 실제로 호출하지 않아서 이 gap을 그 게이트조차 못 잡았다.")
    sized = {"M1a","M1b","M2a","M2b","M3a","M3b","M4a","M4b","M5","M6","M7",  # stage-1 (11)
             "M15","M25","M16","M26",  # stage-2 output (4)
             "M14a","M14b","M11a","M11b","M8","M13",  # Class-AB (6) -- 실제로 stick diagram 없었음
             "M27","M28","M29","M30","M31","M32","M35","M33","M34",  # bias-gen (9) -- 없었음
             "M36a","M36b","M37a","M37b","M38","M39","M40"}  # CMFB (7) -- 없었음
    stick_rows_actual = {  # 실제 재현 -- 이 사고에서 실제로 만들어진 6개 행만
        "row1_pmos_in_casc": ["M1a","M1b","M2a","M2b"],
        "row2_nmos_in_casc": ["M4a","M4b","M3a","M3b"],
        "row3_top_load": ["M6","M7"],
        "row4_tail": ["M5"],
        "rowP_out": ["M15","M25"],
        "rowN_out": ["M16","M26"],
    }
    cov = check_stick_diagram_coverage(sized, stick_rows_actual)
    print(f"  overall={'OK' if cov.ok else 'FAIL(정확히 그 사고를 재현 -- Class-AB/bias-gen/CMFB 22개 소자 누락 검출됨)'}")
    print(f"  missing count={len(cov.missing)}: {sorted(cov.missing)}")

    print()
    print("  [대조: 전부 커버되면 OK로 통과하는지 확인]")
    stick_rows_complete = dict(stick_rows_actual)
    stick_rows_complete["row5_classab"] = ["M14a","M14b","M11a","M11b","M8","M13"]
    stick_rows_complete["row6_biasgen"] = ["M27","M28","M29","M30","M31","M32","M35","M33","M34"]
    stick_rows_complete["row7_cmfb"] = ["M36a","M36b","M37a","M37b","M38","M39","M40"]
    cov2 = check_stick_diagram_coverage(sized, stick_rows_complete)
    print(f"  overall={'OK' if cov2.ok else 'FAIL'}, missing={cov2.missing}")

    print()
    print("=== Test 26: topology library JSON 오케스트레이션 레이어 (load_topology/"
          "run_topology_pipeline/save_instance_json) ===")
    print("  2026-07-28 신설 -- library/*.topology.json이 folded_cascode_example()/")
    print("  two_stage_ota_example()과 connectivity 단위로 diff=0인지, 파이프라인이")
    print("  실제로 끝까지 도는지 회귀 확인. topology JSON은 connectivity+symmetry+")
    print("  compensation만 담는다 -- n_fingers/finger_w/w/stack_id(사이징 산출물)는")
    print("  sizing_overrides로만 채워진다(사용자 지적으로 3차 재설계된 최종 스키마).")
    import os as _os

    _lib_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "library")

    print()
    print("  [folded_cascode: n_fingers/finger_w/w/stack_id 산출물만 folded_cascode_example()에서")
    print("  빌려 파이프라인 기계적 동작을 확인 -- 2026-08-05(세션9) folded_cascode.topology.json이")
    print("  다이오드 레퍼런스 구조(MP/MN, Vg7/Vg9/Vg10 등) 반영으로 Maloberti 교과서 예제와 다른")
    print("  실제 회로로 전면 재구성돼, connectivity diff=0 비교는 더 이상 유효한 회귀 기준이")
    print("  아니다(의도적 차이, 세션9 사용자 승인) -- 소자 이름 집합만 일치 확인하고 connectivity")
    print("  diff는 참고 정보로만 출력한다.")
    _fc_original = folded_cascode_example()
    _fc_loaded, _fc_meta = load_topology(_os.path.join(_lib_dir, "folded_cascode.topology.json"))
    _fc_orig_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _fc_original}
    _fc_load_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _fc_loaded}
    _fc_diff_ok = _fc_orig_by_name == _fc_load_by_name
    assert set(_fc_orig_by_name) == set(_fc_load_by_name), \
        "folded_cascode_example()과 topology.json의 소자 이름 집합이 다름 -- sizing_overrides 구성 불가"
    print(f"  connectivity diff=0: {_fc_diff_ok} ({len(_fc_original)}개 소자, 참고 정보 -- "
          f"세션9 재구성으로 항상 False가 정상)")
    print(f"  compensation={_fc_meta['compensation']} (단일 스테이지라 null이 정상)")

    _fc_overrides = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                               "w": t.w, "stack_id": t.stack_id} for t in _fc_original}
    _fc_result = run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                                        _fc_overrides)
    print(f"  run_topology_pipeline(): box_shape.ok={_fc_result['box_shape'].ok}, "
          f"audit_row_split.ok={_fc_result['audit_row_split'].ok} "
          f"(단일 행 후보라 branch_symmetric 쌍 FAIL 예상 -- row 분할 미탐색은 알려진 한계), "
          f"coverage.ok={_fc_result['coverage'].ok}")

    print()
    print("  [two_stage_ota: 동일 회귀 + compensation 함수 실제 연결 확인]")
    _ts_original = two_stage_ota_example()
    _ts_loaded, _ts_meta = load_topology(_os.path.join(_lib_dir, "two_stage_ota.topology.json"))
    _ts_orig_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _ts_original}
    _ts_load_by_name = {t.name: (t.kind, t.source, t.drain, t.gate) for t in _ts_loaded}
    _ts_diff_ok = _ts_orig_by_name == _ts_load_by_name
    print(f"  connectivity diff=0: {_ts_diff_ok} ({len(_ts_original)}개 소자)")
    print(f"  compensation={_ts_meta['compensation']['function']} "
          f"(구조가 2단 Miller OTA와 일치해 참조 연결됨)")

    _ts_overrides = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                               "w": t.w, "stack_id": t.stack_id} for t in _ts_original}
    _ts_result = run_topology_pipeline(_os.path.join(_lib_dir, "two_stage_ota.topology.json"),
                                        _ts_overrides)
    print(f"  run_topology_pipeline(): box_shape.ok={_ts_result['box_shape'].ok}, "
          f"audit_row_split.ok={_ts_result['audit_row_split'].ok}, "
          f"coverage.ok={_ts_result['coverage'].ok}")

    print()
    print("  [save_instance_json(): pipeline_result를 손대지 않고 그대로 파일에 옮기는지]")
    import tempfile as _tempfile
    with _tempfile.TemporaryDirectory() as _tmpdir:
        _inst_path = _os.path.join(_tmpdir, "folded_cascode.instance.json")
        save_instance_json(_inst_path,
                            _os.path.join(_lib_dir, "folded_cascode.topology.json"),
                            {}, _fc_result)
        with open(_inst_path, "r", encoding="utf-8") as _f:
            _inst_data = json.load(_f)
        print(f"  기록된 최상위 키: {sorted(_inst_data.keys())}")
        print(f"  netlist 소자 수={len(_inst_data['netlist'])}, "
              f"floorplan.packing_density={_inst_data['floorplan']['packing_density']:.3f}")

    assert _ts_diff_ok, "two_stage_ota connectivity diff가 0이 아니다 -- 이관 회귀 실패"
    print()
    print("  Test 26 PASS: two_stage_ota connectivity diff=0, folded_cascode는 이름 집합만 "
          "일치 확인(세션9 재구성으로 diff 비교 자체는 더 이상 유효한 기준이 아님), "
          "파이프라인 정상 실행, save_instance_json 정상 기록")

    print()
    print("=== Test 26.5: run_topology_pipeline() -- sizing_overrides에서 소자 하나를")
    print("    빠뜨리면 즉시 에러가 나는지(PRE-FLIGHT 사고27 재발 방지) ===")
    print("  2026-07-28 실측 발견: split_into_stacks()가 stack_id=None인 소자를")
    print("  (kind,'unspecified') 폴백 그룹으로 자동 흡수해버려서, check_stick_diagram_")
    print("  coverage()는 '이름이 어딘가 있다'고 통과시킨다 -- 즉 사실상 사이징 안 된")
    print("  소자가 coverage.ok=True인 채로 조용히 넘어갈 뻔했다(M11로 실제 재현됨).")
    _fc_overrides_incomplete = {t.name: {"n_fingers": t.n_fingers, "finger_w": t.finger_w,
                                          "w": t.w, "stack_id": t.stack_id}
                                 for t in _fc_original if t.name != "M11"}  # M11을 일부러 빠뜨림
    try:
        run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                               _fc_overrides_incomplete)
        raise AssertionError("M11을 빠뜨렸는데도 에러가 안 났다 -- 사고27이 재발 가능한 상태")
    except ValueError as _e26_5:
        print(f"  PASS: ValueError로 즉시 거부됨 -- {str(_e26_5)[:80]}...")

    print()
    print("=== Test 26.55: run_topology_pipeline() -- check_finger_width_compatibility()가")
    print("    §3.5 선행 게이트로 실제 배선됐는지(세션18) -- W가 finger_w의 정수배가 아니면")
    print("    euler 분석 이전에 즉시 ValueError로 막는지, 정상 케이스는 그대로 통과하는지 ===")
    _fc_overrides_bad_w = dict(_fc_overrides)
    _fc_bad_name = next(iter(_fc_overrides_bad_w))
    _fc_bad_entry = _fc_overrides_bad_w[_fc_bad_name]
    _fc_overrides_bad_w[_fc_bad_name] = {
        **_fc_bad_entry, "w": _fc_bad_entry["finger_w"] * (_fc_bad_entry["n_fingers"] + 0.5)}
    try:
        run_topology_pipeline(_os.path.join(_lib_dir, "folded_cascode.topology.json"),
                               _fc_overrides_bad_w)
        raise AssertionError(
            f"{_fc_bad_name}의 W가 finger_w의 정수배가 아닌데도 에러 없이 통과함 -- "
            "§3.5 게이트가 배선 안 됨")
    except ValueError as _e26_55:
        assert "정수배" in str(_e26_55) and _fc_bad_name in str(_e26_55), \
            f"에러는 났지만 §3.5 게이트가 아닌 다른 이유로 보임: {_e26_55}"
        print(f"  PASS(비정상 W): ValueError로 즉시 거부됨 -- {str(_e26_55)[:100]}...")
    _fc_result_gate_ok = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides)
    print(f"  PASS(정상 W): 기존 정상 케이스는 게이트에서 안 걸리고 그대로 통과 -- "
          f"box_shape.ok={_fc_result_gate_ok['box_shape'].ok}")

    print()
    print("=== Test 26.6: run_topology_pipeline() -- cell_groups 인자 (배치 7-2/2026-07-31) ===")
    print("  fixture: folded_cascode(stack_id=top/mid/bot 3개) -- 물리적으로 독립된 cell이")
    print("  없는 회로지만, cell_groups 메커니즘 자체(파티션별 box_shape/audit_row_split)를")
    print("  검증하는 데는 임의의 2-cell 분할로 충분하다.")

    print()
    print("  [(a) cell_groups/spine_groups 둘 다 None -- 기존 단일-Verdict 동작 그대로]")
    assert not isinstance(_fc_result["box_shape"], dict), "cell_groups 없이도 dict로 바뀜 -- 하위호환 깨짐"
    assert not isinstance(_fc_result["audit_row_split"], dict), "cell_groups 없이도 dict로 바뀜 -- 하위호환 깨짐"
    print(f"  PASS: box_shape={type(_fc_result['box_shape']).__name__}, "
          f"audit_row_split={type(_fc_result['audit_row_split']).__name__} (dict 아님)")

    print()
    print("  [(b) cell_groups 생략, floorplan_hints.spine_groups만 제공 -- fallback으로 그대로 재사용]")
    _spine_only_hints = {"spine_groups": {"cellA": ["top", "mid"], "cellB": ["bot"]}}
    _fc_result_fallback = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides,
        floorplan_hints=_spine_only_hints)
    assert isinstance(_fc_result_fallback["box_shape"], dict), "spine_groups fallback이 dict를 안 만듦"
    assert set(_fc_result_fallback["box_shape"].keys()) == {"cellA", "cellB"}, \
        f"fallback cell 키 불일치: {sorted(_fc_result_fallback['box_shape'].keys())}"
    print(f"  PASS: box_shape 키={sorted(_fc_result_fallback['box_shape'].keys())}, "
          f"audit_row_split 키={sorted(_fc_result_fallback['audit_row_split'].keys())}")

    print()
    print("  [(c) cell_groups를 명시하면 spine_groups와 달라도 cell_groups가 우선(오버라이드)]")
    _explicit_cell_groups = {"signal": ["top", "mid", "bot"]}  # spine_groups와 다른 파티션(1-cell)
    _fc_result_explicit = run_topology_pipeline(
        _os.path.join(_lib_dir, "folded_cascode.topology.json"), _fc_overrides,
        floorplan_hints=_spine_only_hints, cell_groups=_explicit_cell_groups)
    assert set(_fc_result_explicit["box_shape"].keys()) == {"signal"}, \
        f"cell_groups가 spine_groups fallback에 밀림: {sorted(_fc_result_explicit['box_shape'].keys())}"
    # cell_groups가 3개 스택 전부를 담은 단일 cell이므로, combined(cell_groups=None) 결과와
    # box_shape/checks 내용이 일치해야 한다 -- 파티션만 감쌌을 뿐 감사 로직 자체는 그대로.
    assert _fc_result_explicit["box_shape"]["signal"].row_widths == _fc_result["box_shape"].row_widths, \
        "1-cell 전체 파티션인데 combined 결과와 row_widths가 다름"
    print(f"  PASS: box_shape 키={sorted(_fc_result_explicit['box_shape'].keys())} "
          f"(spine_groups={sorted(_spine_only_hints['spine_groups'].keys())}와 다름 -- 오버라이드 확인), "
          f"row_widths 일치(단일 cell=combined)")

    print()
    print("=== Test 27: propagate_topology_forced_currents() / find_diode_stacks() "
          "(A/C엔진, §7.3.2, 배치 7-3/2026-07-31) ===")

    print()
    print("  [A엔진 (a) 직렬 스택 전파 -- folded_cascode 'bot' 스택 한 소자만 seed]")
    _a_ids = propagate_topology_forced_currents(_fc_original, {"M9": 24e-6}, {})
    _bot_names = {t.name for t in _fc_original if t.stack_id == "bot"}
    _bot_propagated_ok = all(_a_ids.get(n) == 24e-6 for n in _bot_names)
    assert _bot_propagated_ok, f"직렬 스택 'bot' 전체에 24uA가 안 퍼짐: {_a_ids}"
    assert "MP" not in _a_ids, "다른 스택(top)까지 잘못 전파됨"
    print(f"  PASS: 'bot' 스택 {sorted(_bot_names)} 전부 24uA로 전파, 'top'/'mid'는 안 건드림")

    print()
    print("  [A엔진 (b) 미러비 전파 -- ref(M9)->mirror(MN) 1:1 미러 가정]")
    _a_ids2 = propagate_topology_forced_currents(_fc_original, {"M9": 24e-6}, {("M9", "MN"): 1.0})
    assert _a_ids2.get("MN") == 24e-6, f"미러비 전파 실패: MN={_a_ids2.get('MN')}"
    print(f"  PASS: M9=24uA -> 미러비 1.0으로 MN={_a_ids2['MN']*1e6:.1f}uA 전파")

    print()
    print("  [A엔진 (c) 같은 직렬 스택에 서로 다른 seed 전류가 섞이면 즉시 ValueError]")
    try:
        propagate_topology_forced_currents(_fc_original, {"M9": 24e-6, "M7": 40e-6}, {})
        raise AssertionError("모순된 seed인데 에러가 안 났다")
    except ValueError as _e27c:
        print(f"  PASS: ValueError로 즉시 거부됨 -- {str(_e27c)[:70]}...")

    print()
    print("  [C엔진 find_diode_stacks() (a) folded_cascode -- M11/MN이 실제로 self-diode임을 검출]")
    print("  fixture 재확인: M11(gate=drain=vb1)/MN(gate=drain=vb2)은 folded_cascode_example()")
    print("  원본부터 diode-connected 바이어스 생성 소자로 정의돼 있다(bias1~5는 외부 net이라")
    print("  아님) -- find_diode_stacks()가 이걸 실제로 찾아내는지가 맞는 검증이다.")
    _fc_diode_stacks = find_diode_stacks(_fc_original)
    assert len(_fc_diode_stacks) == 1 and _fc_diode_stacks[0].stack_id == "bot"
    _fc_diode_names = {m.name: m.gate_refers_to for m in _fc_diode_stacks[0].members}
    assert _fc_diode_names == {"M11": "M11", "MN": "MN"}, \
        f"M11/MN self-diode 판정 실패: {_fc_diode_names}"
    print(f"  PASS: {_fc_diode_names} -- 둘 다 self-diode(gate==자기 drain)로 정확히 검출")

    print()
    print("  [C엔진 find_diode_stacks() (b) 실제 회로(current_reuse_telescopic_ota.topology.json)의")
    print("  M61/M58/M57 stacked-diode를 파일에서 직접 읽어 검증 -- 손타이핑 아님(2026-07-31,")
    print("  사용자 지적으로 합성 넷리스트를 실제 topology.json 로드로 교체)]")
    print("  실제 구조(2026-07-30 사용자와 함께 확인, topology.json _correction_log_2 참고):")
    print("  M61(전류원, gate=Vbias1)->M58(gate=M57의 drain)->M57(gate=자기 drain=Vbias_p)")
    print("  -- 자기참조만 보는 구식 체크는 M58을 놓친다.")
    _crt_path = _os.path.join(_lib_dir, "current_reuse_telescopic_ota.topology.json")
    _crt_transistors, _crt_meta = load_topology(_crt_path)
    _crt_by_name = {t.name: t for t in _crt_transistors}
    # stack_id는 topology.json 스키마에 없는 sizing/layout 산출물이라(§1 스키마 원칙)
    # 테스트가 직접 지정한다 -- name/kind/source/drain/gate(connectivity)는 전부 파일에서
    # 그대로 읽은 값이고 손으로 다시 짓지 않는다.
    _biasstack = [_dc_replace(_crt_by_name[n], stack_id="biasstack_p") for n in ("M61", "M58", "M57")]
    _diode_stacks = find_diode_stacks(_biasstack)
    assert len(_diode_stacks) == 1 and _diode_stacks[0].stack_id == "biasstack_p"
    _diode_names = {m.name: m.gate_refers_to for m in _diode_stacks[0].members}
    assert _diode_names == {"M58": "M57", "M57": "M57"}, \
        f"M57(self)/M58(이웃-M57) 판정 실패: {_diode_names}"
    assert "M61" not in _diode_names, "diode-connected가 아닌 M61(전류원)이 잘못 검출됨"
    print(f"  PASS: {_diode_names} -- M57=self-diode, M58=M57 참조(이웃), M61(전류원)은 제외됨 "
          f"(전부 topology.json에서 실제로 읽은 connectivity)")

    print()
    print("=== Test 28: select_layout_tool()/repair_matching_safety() (배치 7-4/7-4b, 2026-07-31) ===")

    print()
    print("  [select_layout_tool() -- 2026-08-05(세션10) L1 하드컷: 축B/축C 조합별 도구 선택")
    print("  + area_budget 격상. 구 kind 문자열 대신 (matching_sensitivity, shares_node)를 받는다.]")
    assert select_layout_tool("ratio", True) == "interdigitate_layout"          # 구 current_mirror/current_matched
    assert select_layout_tool("ratio", True, area_budget="generous") == "common_centroid_layout"
    assert select_layout_tool("offset", True) == "common_centroid_layout"       # 구 diff_pair
    assert select_layout_tool("ratio", False) == "common_centroid_layout"       # 구 branch_symmetric
    try:
        select_layout_tool("not_a_real_sensitivity", True)
        raise AssertionError("잘못된 matching_sensitivity인데 에러가 안 났다")
    except ValueError as _e_slt:
        print(f"    PASS: 축B/축C 조합 매핑 확인(ratio+shares_node->interdigitate, 나머지"
              f"->common_centroid) + 미등록 matching_sensitivity ValueError -- {str(_e_slt)[:50]}...")

    print()
    print("  [repair_matching_safety() -- known-incidents.md 사고3 재현: folded_cascode.topology.json의")
    print("  current_matched 쌍(어느 이름인지는 topology.json의 symmetry.matching_pairs에서")
    print("  직접 찾는다 -- 특정 소자명을 테스트가 가정하지 않음, 2026-07-31 사용자 지적으로 교체.")
    print("  2026-08 세션6에서 kind 이름이 'current_mirror'->'current_matched'로 바뀌어 픽스처도")
    print("  같이 옮김 -- folded_cascode.topology.json엔 이제 진짜 전류강제 미러가 전부")
    print("  current_matched로 선언돼 있다, sizing_recipe.py 세션6 주석 참고)")
    print("  이 쌍이 서로 다른 행에 통째로 분리 배치된 걸 자동으로 interdigitate 재배치하는지]")
    _fc_by_name = {t.name: t for t in _fc_loaded}

    def _first_pair_matching(pairs_meta, current_forced, matching_sensitivity):
        """topology.json의 symmetry.matching_pairs에서 축A/축C가 일치하는 첫 쌍을 찾는다 --
        어느 소자명이 그 조합인지는 이 함수가 파일에서 알아낼 뿐 테스트가 가정하지 않는다.
        2026-08-05(세션10) L1 하드컷 -- 구 kind 문자열 매칭을 축A(current_forced)/축C
        (matching_sensitivity) 조합 매칭으로 교체."""
        for p in pairs_meta:
            if p["current_forced"] == current_forced and p["matching_sensitivity"] == matching_sensitivity:
                return tuple(p["names"])
        raise AssertionError(f"folded_cascode.topology.json에 current_forced={current_forced!r}, "
                              f"matching_sensitivity={matching_sensitivity!r}인 matching_pair가 "
                              f"없다 -- 테스트 픽스처를 다시 확인할 것")

    _fc_pairs_meta = _fc_meta["symmetry"]["matching_pairs"]
    _mirror_a, _mirror_b = _first_pair_matching(_fc_pairs_meta, True, "ratio")
    print(f"    (JSON에서 발견한 current_forced=True,ratio 쌍(구 current_matched): {_mirror_a}/{_mirror_b})")
    # n_fingers/stack_id는 topology.json에 없는 sizing/layout 산출물이라 테스트가 직접
    # 지정한다(§1 스키마 원칙) -- source/drain/gate(connectivity)는 파일에서 그대로 읽은 값.
    _t_mirror_a = _dc_replace(_fc_by_name[_mirror_a], n_fingers=3, stack_id="row0")
    _t_mirror_b = _dc_replace(_fc_by_name[_mirror_b], n_fingers=3, stack_id="row1")
    _repair_rows_before = {"row0": [_t_mirror_a], "row1": [_t_mirror_b]}
    _repair_pairs = [(_mirror_a, _mirror_b)]
    _repair_sensitivity = {(_mirror_a, _mirror_b): "ratio"}
    _before_audit = audit_row_split(_repair_rows_before, matching_pairs=_repair_pairs,
                                     pair_sensitivity=_repair_sensitivity)
    assert not _before_audit.ok, "수리 전인데 이미 PASS -- 재현 시나리오 실패"
    print(f"    수리 전: ok={_before_audit.ok} (예상대로 FAIL -- 분리배치로 3b 인접성 실패, 사고3 재현)")

    _repaired_rows, _after_audit = repair_matching_safety(_repair_rows_before, _repair_pairs, _repair_sensitivity)
    assert _after_audit.ok, f"수리 후에도 FAIL: {[c for c in _after_audit.checks if not c.ok]}"
    print(f"    수리 후: ok={_after_audit.ok}, 최종 행={sorted(_repaired_rows.keys())} (PASS로 전환)")

    print()
    print("  [repair_matching_safety() -- 공유 hub가 없는 pair(같은 파일에서 발견한 진짜")
    print("  branch_symmetric 쌍)는 건드리지 않고 정직하게 실패 유지(정직한 한계)]")
    _branch_a, _branch_b = _first_pair_matching(_fc_pairs_meta, False, "ratio")
    print(f"    (JSON에서 발견한 current_forced=False,ratio 쌍(구 branch_symmetric): {_branch_a}/{_branch_b})")
    _t_branch_a = _dc_replace(_fc_by_name[_branch_a], n_fingers=6, stack_id="rowA")
    _t_branch_b = _dc_replace(_fc_by_name[_branch_b], n_fingers=6, stack_id="rowB")
    _norepair_rows = {"rowA": [_t_branch_a], "rowB": [_t_branch_b]}
    _norepair_pairs = [(_branch_a, _branch_b)]
    _norepair_sensitivity = {(_branch_a, _branch_b): "ratio"}
    _norepair_result_rows, _norepair_audit = repair_matching_safety(
        _norepair_rows, _norepair_pairs, _norepair_sensitivity)
    assert not _norepair_audit.ok, "공유 hub 없는 쌍인데 수리된 것처럼 PASS가 나옴 -- 버그"
    assert sorted(_norepair_result_rows.keys()) == ["rowA", "rowB"], \
        "건드리면 안 되는데 행 구조가 바뀜"
    print(f"    PASS: ok={_norepair_audit.ok}(여전히 FAIL, 의도대로), "
          f"행 구조 불변={sorted(_norepair_result_rows.keys())} "
          f"({_branch_a}/{_branch_b}은 source가 달라 도구 적용 불가)")

    print()
    print("  [repair_matching_safety() -- 세션16 branch 복합 매칭: current_reuse_telescopic_ota.")
    print("  topology.json의 M6 그룹 실제 사례(M1a-M2a/M1b-M2b가 각각 kcl 직렬 branch, M2a/M2b는")
    print("  source가 서로 달라 예전엔 조용히 스킵됐다) -- 이제 M1a/M1b와 함께 묶여 재배치되는지,")
    print("  branch 구조가 없는 위 테스트는 여전히 완전히 그대로인지(회귀 없음) 확인]")
    _m6b_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library")
    _m6b_trs, _m6b_meta = load_topology(
        os.path.join(_m6b_lib, "current_reuse_telescopic_ota.topology.json"))
    _m6b_by_name = {t.name: t for t in _m6b_trs}
    _m6b_names = ["M1a", "M1b", "M2a", "M2b", "M6", "M7"]
    _m6b_row = [_dc_replace(_m6b_by_name[n], stack_id="seg1") for n in _m6b_names]
    _m6b_pairs = [("M1a", "M1b"), ("M2a", "M2b")]
    _m6b_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    assert _m6b_by_name["M2a"].source != _m6b_by_name["M2b"].source, \
        "M2a/M2b가 source를 공유하면 이 테스트가 재현하려는 사례(branch_symmetric)가 아님"

    _m6b_before = audit_row_split({"seg1": _m6b_row}, matching_pairs=_m6b_pairs,
                                   pair_sensitivity=_m6b_sensitivity)
    assert not _m6b_before.ok, "수리 전인데 이미 PASS -- 재현 시나리오 실패"

    _m6b_rows, _m6b_after = repair_matching_safety({"seg1": _m6b_row}, _m6b_pairs, _m6b_sensitivity)
    _m6b_final_names = {rn: {t.name for t in devs} for rn, devs in _m6b_rows.items()}
    _m6b_row_of = {n: rn for rn, names in _m6b_final_names.items() for n in names}
    assert _m6b_row_of["M2a"] == _m6b_row_of["M2b"], \
        f"M2a/M2b가 같은 행에 안 묶임(branch 복합 매칭 실패): {_m6b_row_of}"
    assert _m6b_row_of["M1a"] == _m6b_row_of["M2a"] == _m6b_row_of["M1b"] == _m6b_row_of["M2b"], \
        f"M1a/M1b/M2a/M2b 4개가 한 branch 복합으로 전부 같은 행에 묶여야 하는데: {_m6b_row_of}"
    assert not _m6b_after.ok, (
        "n_fingers=1인 M1a/M1b/M2a/M2b는 dx<=0.5(3c)를 기하학적으로 달성할 수 없다(세션16 실측,"
        " 최선이 dx=1.0) -- 지금 PASS라면 회귀가 아니라 오히려 이 함수 범위 밖의 일(핑거증가,"
        " 다음 세션 확장 지점)이 우연히 된 것이니 이 assert부터 다시 확인할 것")
    print(f"    PASS: M2a/M2b가 더 이상 스킵되지 않고 M1a/M1b와 같은 행({_m6b_row_of['M1a']})에 "
          f"묶임 -- audit.ok={_m6b_after.ok}(3c는 n_fingers=1 한계로 여전히 FAIL, 예상대로 -- "
          f"핑거증가는 이 함수 범위 밖, gm/ID 재검증이 필요해 sizing_recipe.py 몫)")

    print("  [_branch_composite_pair() -- branch 구조가 없는(2단자 net으로 안 이어진) 단독 소자")
    print("  쌍은 None을 돌려줘 기존 폴백(위 rowA/rowB 테스트)이 안 깨지는지 직접 확인]")
    _bc_none = _branch_composite_pair(_branch_a, _branch_b,
                                       {_branch_a: _t_branch_a, _branch_b: _t_branch_b}, _norepair_pairs)
    assert _bc_none is None, f"branch 구조가 없는데 composite가 나옴(오탐): {_bc_none}"
    print("    PASS: branch 구조 없음 -> None(기존 폴백 경로 그대로 보존)")

    print()
    print("  [세션17 _composite_collapse_for_crossover()/find_min_crossover_layout_with_")
    print("  branch_composite() -- find_min_crossover_layout()을 부르기 전에 branch(M1a-M2a,")
    print("  M1b-M2b)를 미리 합성 소자로 뭉쳐서, crossover 짝짓기가 애초에 branch를 갈라놓을")
    print("  수 없게 만드는지(채점 기반 회피가 아니라 구조적 보장) M6 그룹으로 확인 -- 사용자")
    print("  질문(세션17): 'find_min_crossover_layout() 호출 전에도 branch_composite_pair를")
    print("  써야 하지 않나?']")
    _cc_sensitivity = {("M1a", "M1b"): "offset", ("M2a", "M2b"): "ratio"}
    _cc_trs, _cc_pairs, _cc_sens, _cc_expand = _composite_collapse_for_crossover(
        _m6b_row, _m6b_pairs, _cc_sensitivity)
    assert len(_cc_trs) == len(_m6b_row) - 2, \
        f"4개 실제 소자(M1a/M2a/M1b/M2b) -> 2개 합성으로 순감소 2여야 하는데: " \
        f"{len(_m6b_row)} -> {len(_cc_trs)}"
    assert len(_cc_pairs) == 1, \
        f"hub쪽(M1a/M1b)/leaf쪽(M2a/M2b) 선언 쌍 2개가 합성 쌍 1개로 합쳐져야 하는데: {_cc_pairs}"
    _cc_composite_name = _cc_pairs[0]
    assert set(_cc_expand[_cc_composite_name[0]]) == {"M1a", "M2a"} or \
        set(_cc_expand[_cc_composite_name[0]]) == {"M1b", "M2b"}, \
        f"합성 이름의 expand_map이 예상과 다름: {_cc_expand}"
    assert {"M6", "M7"} <= {t.name for t in _cc_trs}, \
        "미매칭 소자(M6/M7)가 합성 과정에서 사라지면 안 됨"
    assert _cc_sens[_cc_composite_name] == "offset", \
        f"hub쪽(M1a/M1b)이 offset이므로 합성 쌍도 offset이어야 하는데: {_cc_sens}"
    print(f"    PASS: {len(_m6b_row)}소자 -> {len(_cc_trs)}개(합성 2 + 미매칭 그대로), "
          f"선언 쌍 2개 -> 합성 쌍 1개({_cc_composite_name}), 민감도=offset(hub쪽 우선, 보수적 규칙)")

    _cc_result = find_min_crossover_layout_with_branch_composite(_m6b_row, _m6b_pairs, _cc_sensitivity)
    _cc_total = sum(len(s["transistor_sequence"]) for s in _cc_result["segments"])
    assert _cc_total == sum(t.n_fingers for t in _m6b_row), \
        f"펼친 뒤 finger 총합이 원본과 안 맞음: {_cc_total} != {sum(t.n_fingers for t in _m6b_row)}"
    _cc_seg_of: dict = {}
    for i, seg in enumerate(_cc_result["segments"]):
        for name in seg["transistor_sequence"]:
            _cc_seg_of.setdefault(name, set()).add(i)
    assert _cc_seg_of["M1a"] == _cc_seg_of["M2a"], \
        f"M1a/M2a(같은 branch)가 합성 소자인데도 다른 segment에 나옴 -- 구조적 보장 실패: {_cc_seg_of}"
    assert _cc_seg_of["M1b"] == _cc_seg_of["M2b"], \
        f"M1b/M2b(같은 branch)가 합성 소자인데도 다른 segment에 나옴 -- 구조적 보장 실패: {_cc_seg_of}"
    print(f"    PASS: 펼친 뒤에도 M1a/M2a, M1b/M2b가 각각 정확히 같은 segment에 있음(branch가")
    print(f"    애초에 그래프에서 원자 단위 edge였으므로 crossover 짝짓기가 갈라놓을 방법이")
    print(f"    없음 -- 이전 raw 개별소자 버전은 이게 채점 결과였을 뿐 구조적 보장이 아니었음), "
          f"crossover_count={_cc_result['crossover_count']}, "
          f"branch_composites={sorted(_cc_result['branch_composites'].keys())}")

    print("  [회귀 -- branch 구조 없는 그룹(위 rowA/rowB 픽스처)은 _composite_collapse_for_")
    print("  crossover()가 아무것도 안 합치고 원본 그대로 통과시키는지]")
    _cc_none_trs, _cc_none_pairs, _cc_none_sens, _cc_none_expand = \
        _composite_collapse_for_crossover(
            [_t_branch_a, _t_branch_b], _norepair_pairs, _norepair_sensitivity)
    assert _cc_none_pairs == _norepair_pairs and _cc_none_expand == {}, \
        f"branch 구조가 없는데 뭔가 합성됨(오탐): pairs={_cc_none_pairs}, expand={_cc_none_expand}"
    assert {t.name for t in _cc_none_trs} == {_branch_a, _branch_b}
    print(f"    PASS: branch 없음 -> _composite_collapse_for_crossover()가 아무것도 안 건드림"
          f"(expand_map 비어있음, matching_pairs 그대로 {_cc_none_pairs})")

    print()
    print("  [repair_matching_safety() -- 세션17 relaxed_pairs: 최후수단 인접배치 완화가")
    print("  select_layout_tool()의 common-centroid 판단을 실제로 무시하는지(위 M6 그룹 fixture")
    print("  재사용), 그리고 공유 hub도 branch composite도 없는 쌍(위 rowA/rowB)은 relaxed_pairs에")
    print("  있어도 여전히 손 못 대는지(완화가 없는 layout 자유도를 만들어내지 않음) 확인]")
    _rlx_rows, _rlx_after = repair_matching_safety(
        {"seg1": _m6b_row}, _m6b_pairs, _m6b_sensitivity,
        relaxed_pairs={frozenset({"M1a", "M1b"})})
    assert not _rlx_after.ok, (
        "완화됐다고 audit.ok가 True가 되면 안 됨 -- relaxed_pairs는 3c 요구사항 자체를 없애지"
        " 않는다(sizing_recipe.py의 run_matching_safety_with_finger_growth()가 감사 정책을"
        " 그대로 존중하는지 확인하는 하위 계약)")
    _rlx_3c = next(c for c in _rlx_after.checks
                    if c.name.startswith("3c.") and "[M1a/M1b]" in c.name)
    assert not _rlx_3c.ok and "[참고용" not in _rlx_3c.name, \
        f"3c[M1a/M1b]가 여전히 필수 게이트로 FAIL이어야 하는데: {_rlx_3c}"
    print(f"    PASS: relaxed_pairs 적용 후에도 3c[M1a/M1b]는 필수 게이트로 정직하게 FAIL 유지"
          f"(audit.ok={_rlx_after.ok})")

    _rlx_norepair_rows, _rlx_norepair_audit = repair_matching_safety(
        _norepair_rows, _norepair_pairs, _norepair_sensitivity,
        relaxed_pairs={frozenset({_branch_a, _branch_b})})
    assert sorted(_rlx_norepair_rows.keys()) == ["rowA", "rowB"] and not _rlx_norepair_audit.ok, \
        "공유 hub도 branch composite도 없는 쌍인데 relaxed_pairs로 뭔가 바뀜(있지도 않은 layout" \
        " 자유도를 만들어냄 -- 버그)"
    print(f"    PASS: 공유 hub/branch composite 없는 쌍은 relaxed_pairs에 있어도 여전히 손 못 댐"
          f"(행 구조 불변={sorted(_rlx_norepair_rows.keys())}, 정직한 한계 유지)")

    print()
    print("=== Test 29: derive_stack_groups()/assign_finger_geometry() (배치 7-6, 2026-07-31) ===")
    print("  folded_cascode.topology.json 전체(13개 소자, matching_pairs -- 세션34에 M11/MN")
    print("  gap-fill 반영 후 6개)를 그대로 사용 -- 손타이핑 넷리스트 없음(topology.json")
    print("  단일 소스 원칙).")

    print()
    print("  [geometry_colocation_union() -- 2026-08-05(세션10) L1/L2 하드컷: derive_stack_groups()가")
    print("  kcl_series_union()/geometry_colocation_union() 두 함수로 분리됐고, folded_cascode netlist도")
    print("  세션9에 전면 재구성됐다(outA/outB -> Vg7/out) -- assign_finger_geometry()가 실제로 받는")
    print("  것과 동일하게 current_forced=True 쌍만 필터링해 geometry_colocation_union()으로 병합]")
    _fc_forced_pairs = [tuple(p["names"]) for p in _fc_pairs_meta if p["current_forced"]]
    _fc_groups = geometry_colocation_union(_fc_loaded, _fc_forced_pairs)
    _fc_all_members = sorted(n for members in _fc_groups.values() for n in members)
    assert _fc_all_members == sorted(t.name for t in _fc_loaded), \
        "geometry_colocation_union()가 소자를 빠뜨리거나 중복시킴"
    _fc_group_sets = {frozenset(members) for members in _fc_groups.values()}
    # 실측(2026-08-05 세션10, 손으로 미리 추정했다가 실행 결과로 정정됨) -- rule1(같은 극성+
    # non-rail+drain=source)이 declared pair보다 훨씬 넓게 병합한다:
    #   PMOS 6개: M6.source=X가 M1.drain=X/M3.drain=X와 매칭(둘 다 pmos) -> {M1,M3,M6},
    #             M5.source=Y가 M2.drain=Y/M4.drain=Y와 매칭 -> {M2,M4,M5}, 그리고 선언된
    #             M1/M2(diff_pair)가 이 두 하위그룹을 하나로 잇는다 -> {M1,M2,M3,M4,M5,M6}.
    #   NMOS 4개: M7.source=Vg9가 M9.drain=Vg9(diode)와, M8.source=Vg10이 M10.drain=Vg10
    #             (diode)와 매칭(둘 다 nmos) -> {M7,M9}/{M8,M10}, 선언된 M7/M8(current_matched)이
    #             이 둘을 잇는다 -> {M7,M8,M9,M10}.
    # 즉 rule1이 "다이오드 레퍼런스 체인 전체"를 자동으로 찾아내 선언된 2-소자 쌍보다 훨씬
    # 유용한 물리 그룹을 만든다 -- M5/M6(branch_symmetric, current_forced=False라 declared
    # 병합엔 안 들어가지만)는 이미 rule1으로 각자 PMOS/NMOS 그룹에 흡수돼 있다.
    assert frozenset({"M1", "M2", "M3", "M4", "M5", "M6"}) in _fc_group_sets, \
        f"PMOS 6개(M1..M6)가 diff_pair+drain=source 체인으로 한 그룹이 돼야 하는데 안 됨: {_fc_group_sets}"
    assert frozenset({"M7", "M8", "M9", "M10"}) in _fc_group_sets, \
        f"NMOS 4개(M7..M10)가 current_matched+drain=source 체인으로 한 그룹이 돼야 하는데 안 됨: {_fc_group_sets}"
    assert frozenset({"MP"}) in _fc_group_sets, \
        "MP는 다른 어떤 소자와도 안 묶여야 하는데(rail만 공유, drain=source 체인/matching_pair 없음) 그룹이 다름"
    # ⚠️ 2026-08-14 세션34 정정 -- M11/MN은 더 이상 고립 singleton이 아니다.
    # propose_device_roles_gap_fill()의 층위1 current_mirror 폴백(role 기반 정적
    # 레퍼런스 판정으로 정정된 뒤, `.ai/context.md` 세션34 참고)이 M11(diffpair 진짜
    # tail, `ideal_sources`의 `Ibg`로 MN이 독립 레퍼런스임이 확인됨)/MN(diode-connected
    # 레퍼런스) 쌍을 declared matching_pairs(ratio, current_forced=True)로 실제
    # topology.json에 반영했다 -- 다른 declared 2-소자 mirror쌍(M9/M10, M7/M8)과 정확히
    # 같은 패턴이라 이제 이 둘도 같은 이유로 한 그룹이 된다.
    assert frozenset({"M11", "MN"}) in _fc_group_sets, \
        f"M11/MN이 declared matching_pair(current_forced=True)로 한 그룹이 돼야 하는데 안 됨: {_fc_group_sets}"
    print(f"    PASS: {len(_fc_groups)}개 그룹 -- PMOS 6개(M1..M6), NMOS 4개(M7..M10, 다이오드 "
          f"레퍼런스 체인), M11/MN(diffpair tail+레퍼런스 미러쌍), MP(단독) 전부 확인")

    print()
    print("  [geometry_colocation_union() -- 재현성: 같은 입력 다시 넣으면 완전히 같은 그룹]")
    _fc_groups_again = geometry_colocation_union(_fc_loaded, _fc_forced_pairs)
    assert _fc_groups == _fc_groups_again, "같은 입력인데 결과가 달라짐 -- 재현성 위반"
    print("    PASS: 재실행 결과 완전 동일")

    print()
    print("  [assign_finger_geometry() -- 위 그룹 + 합성 sizing_results(가상 gm/ID 결과, ")
    print("  matching pair는 W 동일하게)로 sizing_overrides 자동 구성]")
    # W 값은 sizing 산출물(이 함수가 실제로 테스트하는 대상)이라 topology.json에 없다 --
    # 합성해서 채우는 게 정당하다(§1 스키마 원칙). matching pair는 W를 동일하게 둬서
    # search_stack_finger_w()가 실제로 후보를 찾을 수 있게 구성.
    _fc_sizing_results = {
        "M3": {"W": 30e-6, "L": 0.5e-6}, "M4": {"W": 30e-6, "L": 0.5e-6},
        "M9": {"W": 24e-6, "L": 0.5e-6}, "M10": {"W": 24e-6, "L": 0.5e-6},
        "M1": {"W": 80e-6, "L": 0.35e-6}, "M2": {"W": 80e-6, "L": 0.35e-6},
        "M5": {"W": 30e-6, "L": 1.0e-6}, "M6": {"W": 30e-6, "L": 1.0e-6},
        "M7": {"W": 40e-6, "L": 0.5e-6}, "M8": {"W": 40e-6, "L": 0.5e-6},
        "MP": {"W": 20e-6, "L": 1.5e-6}, "M11": {"W": 16e-6, "L": 0.5e-6}, "MN": {"W": 16e-6, "L": 0.5e-6},
    }
    _fc_overrides = assign_finger_geometry(_fc_sizing_results, _fc_groups,
                                            min_finger_w=1e-6, max_finger_w=40e-6)
    assert set(_fc_overrides.keys()) == set(_fc_sizing_results.keys()), \
        "assign_finger_geometry()가 일부 소자를 빠뜨림"
    for _name, _ov in _fc_overrides.items():
        assert _ov["n_fingers"] >= 1 and isinstance(_ov["n_fingers"], int)
        assert abs(_ov["w"] - _ov["n_fingers"] * _ov["finger_w"]) < 1e-15, \
            f"{_name}: w != n_fingers*finger_w"
        assert abs(_ov["w"] - _fc_sizing_results[_name]["W"]) / _fc_sizing_results[_name]["W"] < 1e-6, \
            f"{_name}: 배정된 w가 원래 sizing W와 너무 다름"
        _owning_group = next(sid for sid, members in _fc_groups.items() if _name in members)
        assert _ov["stack_id"] == _owning_group, f"{_name}: stack_id가 자기 그룹 키와 다름"
        # 2026-08-13(세션31) -- overrides["l"]이 sizing_results[name]["L"]과 정확히 일치하는지
        # 확인(assign_finger_geometry()의 "L"(대문자, sizing 쪽 키) -> "l"(소문자, Transistor
        # 필드) 의도적 rename이 조용히 깨지지 않았는지 잡는 회귀 테스트).
        assert _ov["l"] == _fc_sizing_results[_name]["L"], \
            f"{_name}: overrides['l']={_ov['l']} != sizing_results['L']={_fc_sizing_results[_name]['L']}"
    print(f"    PASS: {len(_fc_overrides)}개 소자 전부 n_fingers*finger_w==w로 원래 W 정확히 "
          f"재현, stack_id가 derive_stack_groups() 그룹 키와 일치, l이 sizing_results의 L과 일치")
    _row_lengths = {}
    for _name, _ov in _fc_overrides.items():
        _row_lengths.setdefault(_ov["stack_id"], 0)
        _row_lengths[_ov["stack_id"]] += _ov["n_fingers"]
    print(f"    참고: stack별 total_row_fingers={_row_lengths} "
          f"(box-shape 판정은 audit_row_split()/repair_matching_safety()의 몫)")

    print()
    print("=== Test 30: analog-grammar 연동(Tier 1) — find_idiom_matches()/find_matching_")
    print("    candidates(idiom_matches=)/find_stack_edges()/find_stacked_matching_candidates()")
    print("    (2026-08-06, analog-topology-json-library 세션18 K/L절 + 사용자 설계 논의) ===")

    print()
    print("  [0. analog-grammar 사용 가능 확인 -- 없으면 이 Test 전체가 무의미하니 먼저 확인]")
    _ag_matches_probe = find_idiom_matches(folded_cascode_example())
    assert _ag_matches_probe is not None, \
        "analog-grammar skill을 찾지 못함 -- skills/analog-grammar/assets가 있는지 확인할 것"
    print("    PASS: analog-grammar import 성공")

    print()
    print("  [1. 하위호환 -- idiom_matches=None(기본값)이면 Test 6과 완전히 동일한 net-only 동작]")
    _t30_old_again = find_matching_candidates(folded_cascode_example())
    assert _t30_old_again["current_mirror"].keys() == found["current_mirror"].keys()
    assert _t30_old_again["diff_pair"].keys() == found["diff_pair"].keys()
    print("    PASS: idiom_matches 파라미터 추가 후에도 기본값 동작 무변경")

    print()
    print("  [2. M57/M58 오탐 재현 -- 세션18 실사고 connectivity(2026-07-29 disposed -> 2026-08-03")
    print("  정정)를 그대로 fixture로 구성. 양성대조(MrefA/MrefB, 진짜 diode 레퍼런스 미러)도 함께]")
    _mirror_fixture = [
        Transistor("M57", "pmos", source="N58_57", drain="Vbias2", gate="Vbias2", n_fingers=1),
        Transistor("M58", "pmos", source="Vx", drain="N58_57", gate="Vbias2", n_fingers=1),
        Transistor("MrefA", "pmos", source="vdd", drain="Vbias9", gate="Vbias9", n_fingers=1),
        Transistor("MrefB", "pmos", source="vdd", drain="out9", gate="Vbias9", n_fingers=1),
    ]
    _old_mirror = find_matching_candidates(_mirror_fixture)
    _old_mirror_sets = {frozenset(t.name for t in g) for g in _old_mirror["current_mirror"].values()}
    assert frozenset({"M57", "M58"}) in _old_mirror_sets, \
        "옛 동작(gate만 봄)이 M57/M58을 current_mirror로 잡는지부터 재현 안 됨 -- fixture 확인 필요"
    print(f"    옛 동작(재현): {[sorted(s) for s in _old_mirror_sets]} -- M57/M58 오탐 포함 확인")

    _mirror_matches = find_idiom_matches(_mirror_fixture)
    _new_mirror = find_matching_candidates(_mirror_fixture, idiom_matches=_mirror_matches)
    _new_mirror_sets = {frozenset(t.name for t in g) for g in _new_mirror["current_mirror"].values()}
    assert frozenset({"M57", "M58"}) not in _new_mirror_sets, \
        f"gate+source 그룹핑 후에도 M57/M58이 여전히 current_mirror로 잡힘: {_new_mirror_sets}"
    assert frozenset({"MrefA", "MrefB"}) in _new_mirror_sets, \
        f"진짜 diode 레퍼런스 미러(MrefA/MrefB)까지 같이 사라짐(과잉 필터): {_new_mirror_sets}"
    print(f"    새 동작: {[sorted(s) for s in _new_mirror_sets]} -- M57/M58 제외, MrefA/MrefB는 유지")

    print()
    print("  [3. M11/MN 오탐 재현 -- folded_cascode_example(), 둘 다 self-diode(role=DIODE_CONNECTED)")
    print("  라 diff_pair의 AMPLIFYING 요구를 애초에 통과 못해야 함. inputs 선언 없으면 vin_p/vin_n도")
    print("  이름 힌트 미매치로 BIAS 취급돼 M1/M2까지 같이 사라지므로 반드시 inputs= 선언]")
    _fc_matches_bare = find_idiom_matches(folded_cascode_example())
    _fc_new_bare = find_matching_candidates(folded_cascode_example(), idiom_matches=_fc_matches_bare)
    assert _fc_new_bare["diff_pair"] == {}, \
        f"inputs 미선언 상태에서도 diff_pair가 나오면 안 되는데 나옴(vin_p/vin_n 힌트 이슈 재확인 필요): {_fc_new_bare['diff_pair']}"

    _fc_matches = find_idiom_matches(folded_cascode_example(), inputs=("vin_p", "vin_n"))
    _fc_new = find_matching_candidates(folded_cascode_example(), idiom_matches=_fc_matches)
    _fc_new_diffpair_sets = {frozenset(t.name for t in g) for g in _fc_new["diff_pair"].values()}
    assert frozenset({"M11", "MN"}) not in _fc_new_diffpair_sets, \
        f"M11/MN이 여전히 diff_pair로 잡힘: {_fc_new_diffpair_sets}"
    assert frozenset({"M1", "M2"}) in _fc_new_diffpair_sets, \
        f"진짜 차동쌍(M1/M2)까지 같이 사라짐(과잉 필터): {_fc_new_diffpair_sets}"
    print(f"    inputs=vin_p,vin_n 선언 후: {[sorted(s) for s in _fc_new_diffpair_sets]} "
          f"-- M11/MN 제외, M1/M2는 유지")

    print()
    print("  [4. 캐스코드 대칭쌍(M2a/M2b류) 복합소자 상속 -- folded_cascode의 M1/M2(확정 diff_pair)")
    print("  위에 직접 stacked된 M5/M6를 find_stacked_matching_candidates()가 재귀적으로 찾는지.")
    print("  M1 위엔 극성이 다른 M5(pmos)/M7(nmos)이 동시에 얹혀 있어(폴딩 노드 X 공유) 같은")
    print("  kind로 좁히는 로직이 실제로 필요한 fixture -- 2026-08-06 실측으로 발견된 버그 재발 방지]")
    _fc_edges = find_stack_edges(folded_cascode_example())
    assert _fc_edges is not None
    _fc_base_pairs = [(g[0].name, g[1].name) for g in _fc_new["diff_pair"].values()]
    assert _fc_base_pairs == [("M1", "M2")], f"base_pairs 예상과 다름: {_fc_base_pairs}"
    _fc_stacked = find_stacked_matching_candidates(folded_cascode_example(), _fc_base_pairs, _fc_edges)
    _fc_stacked_sets = {frozenset(t.name for t in g) for g in _fc_stacked.values()}
    assert frozenset({"M5", "M6"}) in _fc_stacked_sets, \
        f"M1/M2 위의 M5/M6(둘 다 pmos)이 상속되지 않음(극성 필터 버그 재발?): {_fc_stacked_sets}"
    assert frozenset({"M5", "M7"}) not in _fc_stacked_sets, \
        f"극성이 다른 M7(nmos)이 M5 자리에 잘못 섞여 들어옴: {_fc_stacked_sets}"
    print(f"    PASS: {[sorted(s) for s in _fc_stacked_sets]} -- M5/M6(같은 pmos)만 상속, "
          f"극성 다른 M7/M8은 안 섞임")

    print()
    print("  [5. 어댑터 자체 폴백 -- gate가 전혀 없는(레거시) Transistor 목록을 주면")
    print("  _to_analog_grammar_devs()가 전부 걸러내 devs=[]가 되고, find_idiom_matches()/")
    print("  find_stack_edges()가 (analog-grammar 자체는 멀쩡해도) 자연스럽게 None을 반환하는지.")
    print("  analog-grammar 미설치 상황(ImportError 경로)은 사용자 환경에 실제로 있을 때만")
    print("  검증 가능하므로(설치를 일부러 지웠다 복원하는 건 self-test로 하기엔 위험한 파일시스템")
    print("  조작이라 하지 않는다), 여기서는 두 어댑터가 실제로 소비하는 '입력이 비게 되는'")
    print("  경로로 None-반환을 재현한다]")
    _no_gate_fixture = [Transistor("Ma", "pmos", source="vdd", drain="n1"),
                         Transistor("Mb", "pmos", source="vdd", drain="n2")]
    assert find_idiom_matches(_no_gate_fixture) is None, \
        "gate 없는 소자만 있는데도 find_idiom_matches()가 None이 아님"
    assert find_stack_edges(_no_gate_fixture) is None, \
        "gate 없는 소자만 있는데도 find_stack_edges()가 None이 아님"
    _fallback_result = find_matching_candidates(_no_gate_fixture,
                                                  idiom_matches=find_idiom_matches(_no_gate_fixture))
    assert _fallback_result == {"current_mirror": {}, "diff_pair": {}}
    print("    PASS: gate 없는 fixture -> 두 어댑터 전부 None, find_matching_candidates()는 빈 결과")

    print()
    print("  === Test 30 전체 PASS ===")

    print()
    print("=== Test 31: run_full_circuit_audit_from_topology() -- topology.json 하나만으로")
    print("    devices/expected_counts/dispositions 자동 구성 (세션20, harness 실배선 전 단계) ===")
    import os as _os31

    _lib_dir31 = _os31.path.join(_os31.path.dirname(_os31.path.abspath(__file__)), "library")
    _crt_path = _os31.path.join(_lib_dir31, "current_reuse_telescopic_ota.topology.json")

    print()
    print("  [1. 실제 회로(51개 소자)로 자동 구성 -- ok=True, 세 체크 전부 자동 데이터로 통과하는지]")
    _crt_transistors, _crt_meta = load_topology(_crt_path)
    _crt_structured = _crt_meta["netlist_sections_structured"]
    assert _crt_structured is not None, "current_reuse_telescopic_ota가 구조화 필드를 못 읽음"
    _crt_expected_total = sum(len(v["devices"]) for v in _crt_structured.values())
    assert _crt_expected_total == len(_crt_transistors) == 51, \
        f"구조화 블록 합({_crt_expected_total})이 netlist 전체 개수({len(_crt_transistors)})와 불일치"
    _crt_audit = run_full_circuit_audit_from_topology(_crt_path)
    assert _crt_audit.ok, f"실제 회로 자동감사가 FAIL: {_crt_audit.checks}"
    _crt_check_names = [c.name for c in _crt_audit.checks]
    assert any(c.startswith("1.") for c in _crt_check_names) and \
           any(c.startswith("2.") for c in _crt_check_names) and \
           any(c.startswith("3.") for c in _crt_check_names), \
        f"체크 1/2/3이 전부 실행되지 않음: {_crt_check_names}"
    print(f"    PASS: ok={_crt_audit.ok}, {[(c.name, c.ok) for c in _crt_audit.checks]}")

    print()
    print("  [2. dispositions 변환 -- symmetry.dispositions(list)와 개수가 일치하고, 형식이 (category,")
    print("  reason) 튜플로 정확히 바뀌는지]")
    _crt_raw_dispositions = _crt_meta["symmetry"]["dispositions"]
    _crt_sample = _crt_raw_dispositions[0]
    _crt_key = (_crt_sample["tag"], _crt_sample["kind"], _crt_sample["key"])
    _crt_expected_val = (_crt_sample["category"], _crt_sample["reason"])
    # run_full_circuit_audit_from_topology()는 dispositions dict를 반환하지 않으므로(§1.6 계약을
    # 그대로 따름, AuditResult만 반환) 변환 로직 자체를 직접 재현해 대조한다.
    _crt_disp_dict = {(d["tag"], d["kind"], d["key"]): (d["category"], d["reason"])
                       for d in _crt_raw_dispositions}
    assert len(_crt_disp_dict) == len(_crt_raw_dispositions), \
        "dispositions 변환 중 (tag,kind,key) 키 충돌로 일부가 사라짐"
    assert _crt_disp_dict[_crt_key] == _crt_expected_val, "dispositions 변환 형식이 계약과 다름"
    print(f"    PASS: {len(_crt_raw_dispositions)}건 전부 키 충돌 없이 변환, 샘플 {_crt_key} 일치")

    print()
    print("  [3. 구조화 필드가 없는 회로(folded_cascode) -- ValueError로 명확히 실패하는지,")
    print("  조용히 빈 expected_counts로 넘어가지 않는지]")
    try:
        run_full_circuit_audit_from_topology(_os31.path.join(_lib_dir31, "folded_cascode.topology.json"))
        raise AssertionError("구조화 필드가 없는데도 ValueError가 안 남")
    except ValueError as _e31:
        assert "_netlist_sections_structured" in str(_e31), f"에러 메시지가 원인을 안 가리킴: {_e31}"
        print(f"    PASS: ValueError 발생 -- {_e31}")

    print()
    print("  [4. 구조화가 netlist 전수를 못 커버하면(소자 하나가 어느 블록에도 없음) ValueError --")
    print("  임시 topology.json으로 실제 함수를 태워 확인(내부 로직 재현이 아니라 진짜 호출)]")
    import tempfile as _tempfile31
    _broken_topo = {
        "schema_version": "1.0", "topology_name": "broken_test_fixture", "source": None,
        "ports": {}, "passive_elements": [], "ideal_sources": [],
        "netlist": [
            {"name": "Ma", "kind": "pmos", "source": "vdd", "drain": "n1", "gate": "vb"},
            {"name": "Mb", "kind": "pmos", "source": "vdd", "drain": "n2", "gate": "vb"},
        ],
        "symmetry": {"matching_pairs": [], "dispositions": []},
        "compensation": None,
        "_netlist_sections_structured": {
            "only_block": {"label": "test", "confidence": "HIGH", "devices": ["Ma"]},  # Mb 누락
        },
    }
    with _tempfile31.NamedTemporaryFile(mode="w", suffix=".topology.json", delete=False,
                                          encoding="utf-8") as _f31:
        json.dump(_broken_topo, _f31)
        _broken_path = _f31.name
    try:
        try:
            run_full_circuit_audit_from_topology(_broken_path)
            raise AssertionError("Mb가 어느 블록에도 없는데도 ValueError가 안 남")
        except ValueError as _e31b:
            assert "Mb" in str(_e31b), f"에러 메시지가 빠진 소자를 안 가리킴: {_e31b}"
            print(f"    PASS: ValueError 발생 -- {_e31b}")
    finally:
        _os31.remove(_broken_path)

    print()
    print("  === Test 31 전체 PASS ===")

    print()
    print("=== Test 32: trace_vdd_to_gnd_branches() -- 세션23 실측(4가지 vertical_stack_id")
    print("    자동화 시도 중 유일하게 성공한 branch tracing)의 핵심 성질 3가지를 합성 fixture로")
    print("    재확인: (1) 병렬 형제(같은 kind, 같은 타입 단자 공유)는 절대 안 이어짐,")
    print("    (2) PMOS drain=NMOS drain 만남 지점은 정상적으로 이어짐, (3) 진짜 fan-out은")
    print("    branch 여러 개로 정확히 갈라지고, 소비자가 없는 net은 non_transistor로 종료 ===")
    _t32_fixture = [
        Transistor("M6", "pmos", source="vdd", drain="Vx"),
        Transistor("M7", "pmos", source="vdd", drain="Vx"),
        Transistor("M1a", "pmos", source="Vx", drain="N1"),
        Transistor("M1b", "pmos", source="Vx", drain="N2"),   # M1a의 병렬 형제 -- N2는 아무도 안 씀
        Transistor("M2a", "pmos", source="N1", drain="Nout"),
        Transistor("M3a", "nmos", source="Ngndmid", drain="Nout"),  # M2a와 drain=drain으로 만남
        Transistor("M19", "nmos", source="gnd", drain="Nout"),      # Nout의 두 번째 소비자(진짜 fork)
        Transistor("M4a", "nmos", source="gnd", drain="Ngndmid"),
        Transistor("Mbg", "pmos", source="vdd", drain="Vbiasx", gate="Vbiasx"),  # diode, 소비자 없음
    ]
    _t32_result = trace_vdd_to_gnd_branches(_t32_fixture)
    _t32_branches = _t32_result["branches"]
    _t32_complete = [b for b in _t32_branches if b["terminates_at"] == "gnd"]
    _t32_dead = [b for b in _t32_branches if b["terminates_at"] == "non_transistor"]
    assert len(_t32_branches) == 7, f"branch 총 개수가 7이 아님(조합 폭발/과소탐지 재확인): {len(_t32_branches)}"
    assert len(_t32_complete) == 4 and len(_t32_dead) == 3, \
        f"완주/dead-end 분류가 예상과 다름: complete={len(_t32_complete)} dead={len(_t32_dead)}"
    print(f"    PASS: branch 7개(완주 4 + non_transistor 3), 조합 폭발 없음")

    for b in _t32_branches:
        assert not ({"M1a", "M1b"} <= set(b["chain"])), \
            f"병렬 형제 M1a/M1b가 같은 branch에 같이 들어감(회귀): {b['chain']}"
    print("    PASS: M1a/M1b(같은 kind, 같은 Vx를 source로 공유하는 병렬 형제)는 어떤 branch에서도 안 이어짐")

    assert ["M6", "M1a", "M2a", "M3a", "M4a"] in [b["chain"] for b in _t32_complete], \
        "M2a(pmos)->M3a(nmos) drain=drain 만남 경로가 안 나옴"
    assert ["M6", "M1a", "M2a", "M19"] in [b["chain"] for b in _t32_complete], \
        "Nout의 두 번째 소비자(M19)로 갈라지는 fork branch가 안 나옴"
    print("    PASS: M2a/M3a drain=drain 만남 정상 연결 + Nout에서 M3a/M19로 정확히 2-way fork")

    _t32_mbg = [b for b in _t32_branches if b["chain"] == ["Mbg"]]
    assert len(_t32_mbg) == 1 and _t32_mbg[0]["terminates_at"] == "non_transistor", \
        "diode-connected Mbg(소비자 없는 Vbiasx)가 non_transistor로 안 끝남"
    print("    PASS: 소비자 없는 net(Vbiasx)에서 dead-end가 non_transistor로 정직하게 보고됨")

    print()
    print("  === Test 32 전체 PASS ===")

    print()
    print("=== Test 33: suggest_vertical_stack_composites() -- branch tracing(Test 32) +")
    print("    analog-grammar idiom matching(floating-battery 등)을 합쳐 세션23 5번째 실측")
    print("    (62/63 vertical_stack_id 일치)의 핵심 성질을 합성 fixture로 재확인: 연속된")
    print("    diode-connected 소자 쌍만 floating-battery로 병합되고, 그 아래 non-diode")
    print("    소자는 별도 composite으로 남는지 ===")
    _t33_probe = find_idiom_matches(folded_cascode_example())
    assert _t33_probe is not None, "analog-grammar skill을 찾지 못함 -- Test 30과 동일 전제조건"
    _t33_fixture = [
        Transistor("Ma", "pmos", source="vdd", drain="Ntop", gate="Ntop"),   # diode(G=D)
        Transistor("Mb", "pmos", source="Ntop", drain="Nmid", gate="Nmid"),  # diode(G=D), Ma 위에 직렬
        Transistor("Mc", "nmos", source="gnd", drain="Nmid", gate="Vbias4"), # non-diode, 체인 종단
    ]
    _t33_result = suggest_vertical_stack_composites(_t33_fixture)
    assert _t33_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    assert len(_t33_result) == 1, f"branch 1개짜리 fixture인데 결과가 {len(_t33_result)}개"
    _t33_composites = _t33_result[0]["composites"]
    assert _t33_result[0]["chain"] == ["Ma", "Mb", "Mc"], \
        f"branch 골격 자체가 어긋남(Test 32 회귀 가능성): {_t33_result[0]['chain']}"
    assert len(_t33_composites) == 2, f"composite 개수가 2가 아님(과잉/과소 병합): {_t33_composites}"
    assert _t33_composites[0]["members"] == ["Ma", "Mb"] and _t33_composites[0]["idiom"] == "floating-battery", \
        f"Ma/Mb가 floating-battery로 안 묶임: {_t33_composites[0]}"
    assert _t33_composites[1]["members"] == ["Mc"], \
        f"Mc가 diode 쌍에 잘못 흡수됨: {_t33_composites[1]}"
    assert isinstance(_t33_composites[1]["ports"], dict), \
        f"ports는 항상 dict여야 함(단일 소자 idiom이 있으면 그 내용, 없으면 빈 dict): {_t33_composites[1]}"
    print(f"    PASS: [Ma,Mb](floating-battery) | [Mc] -- 사람이 vertical_stack_id를 이 경계로")
    print(f"    쪼갠 실제 사례(M11a+M11b vs M12 등, .ai/context.md 세션23 C절)와 같은 패턴 재현")

    print()
    print("  === Test 33 전체 PASS ===")

    print()
    print("=== Test 35: trace_gnd_to_vdd_branches()/find_differential_and_mirror_forks() --")
    print("    telescopic/current-reuse 구조처럼 differential pair가 스택 안에 여러 층으로")
    print("    있을 때, 하향(VDD->GND) 단독으로는 위쪽 pair만, 상향(GND->VDD) 단독으로는")
    print("    아래쪽 pair만 잡고, 양방향을 합쳐야 둘 다 잡히는지(세션23 실측 -- 사용자")
    print("    지적: \"telescopic differential pair를 인식 못하는 문제\") 합성 fixture로 재현 ===")
    _t35_fixture = [
        Transistor("M6", "pmos", source="vdd", drain="Vx", gate="Vbias1"),
        Transistor("M1a", "pmos", source="Vx", drain="N1", gate="Vip"),    # 위쪽 diff pair
        Transistor("M1b", "pmos", source="Vx", drain="N2", gate="Vim"),
        Transistor("M2a", "pmos", source="N1", drain="Nout1", gate="Vbias2"),
        Transistor("M2b", "pmos", source="N2", drain="Nout2", gate="Vbias2"),
        Transistor("M3a", "nmos", source="N3", drain="Nout1", gate="Vbias3"),
        Transistor("M3b", "nmos", source="N4", drain="Nout2", gate="Vbias3"),
        Transistor("M4a", "nmos", source="Vy", drain="N3", gate="Vip"),    # 아래쪽 diff pair
        Transistor("M4b", "nmos", source="Vy", drain="N4", gate="Vim"),
        Transistor("M5", "nmos", source="gnd", drain="Vy", gate="Vbias4"),
    ]
    _t35_down = trace_vdd_to_gnd_branches(_t35_fixture)
    _t35_down_chains = [b["chain"] for b in _t35_down["branches"] if b["terminates_at"] == "gnd"]
    assert _t35_down_chains == [["M6", "M1a", "M2a", "M3a", "M4a", "M5"],
                                  ["M6", "M1b", "M2b", "M3b", "M4b", "M5"]], \
        f"하향 branch 골격이 예상과 다름: {_t35_down_chains}"
    _t35_up = trace_gnd_to_vdd_branches(_t35_fixture)
    _t35_up_chains = [b["chain"] for b in _t35_up["branches"] if b["terminates_at"] == "vdd"]
    assert _t35_up_chains == [["M5", "M4a", "M3a", "M2a", "M1a", "M6"],
                                ["M5", "M4b", "M3b", "M2b", "M1b", "M6"]], \
        f"상향 branch 골격이 예상과 다름(하향의 정확한 역순이어야 함): {_t35_up_chains}"
    print("    PASS: 상향 branch가 하향 branch의 정확한 역순으로 재구성됨")

    _t35_result = find_differential_and_mirror_forks(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t35_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t35_forks = _t35_result["forks"]
    assert len(_t35_forks) == 2, f"fork가 정확히 2개(위/아래 diff pair 하나씩)여야 함: {_t35_forks}"
    _t35_down_forks = [f for f in _t35_forks if f["direction"] == "vdd_to_gnd"]
    _t35_up_forks = [f for f in _t35_forks if f["direction"] == "gnd_to_vdd"]
    assert len(_t35_down_forks) == 1 and _t35_down_forks[0]["fork_devices"] == ("M1a", "M1b") \
        and _t35_down_forks[0]["relation"] == "differential", \
        f"하향에서 M1a/M1b differential fork를 못 찾음: {_t35_down_forks}"
    assert len(_t35_up_forks) == 1 and _t35_up_forks[0]["fork_devices"] == ("M4a", "M4b") \
        and _t35_up_forks[0]["relation"] == "differential", \
        f"상향에서 M4a/M4b differential fork를 못 찾음(양방향 탐지의 핵심 --" \
        f" 하향만으로는 이 fork가 분기 없는 직선 구간에 파묻혀 절대 안 보임): {_t35_up_forks}"
    print("    PASS: 하향은 M1a/M1b(위쪽 diff pair)만, 상향은 M4a/M4b(아래쪽 diff pair)만")
    print("    각자 찾고, 합쳐야 둘 다 잡힘 -- 세션23 실측(current_reuse_telescopic_ota:")
    print("    하향 M1a/M1b ×2, 상향 M4a/M4b ×1)과 같은 패턴 재현")

    print()
    print("  === Test 35 전체 PASS ===")

    print()
    print("=== Test 36: find_verified_differential_and_mirror_relations() -- 진짜 branch")
    print("    단위 비교(composite 구조가 완전히 같은 branch끼리만 묶음, C-7 원리를 양방향")
    print("    으로 확장) + 매칭된 쌍 안의 모든 위치 스캔(첫 divergence만 보던 한계 해소).")
    print("    Test 35의 telescopic fixture 하나로 differential/mirror 4가지 관계가 전부")
    print("    (하향 스캔 한 번만으로도) 나오는지 재확인 ===")
    _t36_result = find_verified_differential_and_mirror_relations(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t36_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t36_diff_devs = {r["devices"] for r in _t36_result["differential"]}
    _t36_mirror_devs = {r["devices"] for r in _t36_result["mirror"]}
    assert {("M1a", "M1b")} <= _t36_diff_devs, \
        f"M1a/M1b differential이 안 잡힘: {_t36_diff_devs}"
    assert {("M4a", "M4b")} <= _t36_diff_devs, \
        f"M4a/M4b differential이 안 잡힘(양방향+전체위치 스캔의 핵심): {_t36_diff_devs}"
    assert {("M2a", "M2b")} <= _t36_mirror_devs, f"M2a/M2b mirror가 안 잡힘: {_t36_mirror_devs}"
    assert {("M3a", "M3b")} <= _t36_mirror_devs, f"M3a/M3b mirror가 안 잡힘: {_t36_mirror_devs}"
    _t36_down_diff = [r for r in _t36_result["differential"] if r["direction"] == "vdd_to_gnd"]
    assert {r["devices"] for r in _t36_down_diff} == {("M1a", "M1b"), ("M4a", "M4b")}, \
        f"하향 방향 스캔 하나만으로 두 differential 관계가 전부 안 나옴: {_t36_down_diff}"
    print("    PASS: M1a/M1b(위치1)+M4a/M4b(위치4) differential, M2a/M2b(위치2)+M3a/M3b")
    print("    (위치3) mirror -- 전부 하향 방향 한 번의 branch-쌍 스캔만으로 동시에 검출됨")
    print("    (find_differential_and_mirror_forks()는 fork-tree라 방향마다 하나씩만 봤었음)")

    print()
    print("  === Test 36 전체 PASS ===")

    print()
    print("=== Test 37: find_differential_pair_candidates() -- inputs= 선언 없이 순수")
    print("    connectivity(같은 non-rail source 공유)만으로 진짜 differential pair를")
    print("    찾는지(사용자 통찰: \"differential pair를 먼저 찾고 나서 mirror를 분석해야")
    print("    정확해진다\") Test 35의 telescopic fixture로 재확인 ===")
    _t37_result = find_differential_pair_candidates(_t35_fixture)  # inputs= 아예 안 넘김
    assert _t37_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t37_devs = {c["devices"] for c in _t37_result["candidates"]}
    assert ("M1a", "M1b") in _t37_devs, \
        f"inputs= 선언 없이 M1a/M1b를 못 찾음(핵심 주장 실패): {_t37_devs}"
    assert ("M4a", "M4b") in _t37_devs, \
        f"inputs= 선언 없이 M4a/M4b를 못 찾음(핵심 주장 실패): {_t37_devs}"
    _t37_sources = {c["devices"]: c["shared_source"] for c in _t37_result["candidates"]}
    assert _t37_sources[("M1a", "M1b")] == "Vx" and _t37_sources[("M4a", "M4b")] == "Vy", \
        f"shared_source가 예상과 다름: {_t37_sources}"
    print("    PASS: inputs= 파라미터를 아예 안 넘겼는데도(Vip/Vim 선언 없음)")
    print("    M1a/M1b(source=Vx)/M4a/M4b(source=Vy) 둘 다 순수 connectivity만으로 검출됨")

    print()
    print("  === Test 37 전체 PASS ===")

    print()
    print("=== Test 38: refine_differential_and_mirror_relations() -- input 승격")
    print("    오케스트레이션(.ai/context.md D절 item 0, 세션24 신설). M37a/M37b류")
    print("    (게이트가 inputs=에 없는 2차 differential pair)를 축소 재현한 합성")
    print("    fixture로: (1) 승격 전에는 못 찾다가 승격 후 differential로 잡히는지,")
    print("    (2) 그 승격의 연쇄효과로 다른 소자 role/net class가 바뀌었을 때 조용히")
    print("    덮어쓰지 않고 명시적으로 보고하는지 검증 ===")
    _t38_fixture = [
        Transistor("M61", "nmos", source="gnd", drain="Ncmfb_tail", gate="Vbias_tail"),
        Transistor("M60a", "nmos", source="Ncmfb_tail", drain="Vcmfb_a", gate="Voc"),
        Transistor("M60b", "nmos", source="Ncmfb_tail", drain="Vcmfb_b", gate="Voc_des"),
        Transistor("M63a", "pmos", source="vdd", drain="Vcmfb_a", gate="Vbias_x"),
        Transistor("M63b", "pmos", source="vdd", drain="Vcmfb_b", gate="Vbias_x"),
        Transistor("M62", "pmos", source="vdd", drain="Nload", gate="Vcmfb_a"),
    ]
    _t38_pre = find_verified_differential_and_mirror_relations(_t38_fixture)
    assert _t38_pre is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t38_pre_devs = {r["devices"] for r in _t38_pre["differential"]}
    assert ("M60a", "M60b") not in _t38_pre_devs, \
        f"승격 전인데 M60a/M60b가 이미 differential로 잡힘(fixture 설계 오류): {_t38_pre_devs}"
    _t38_pre_no_conn = {r["devices"] for r in _t38_pre["structurally_symmetric_no_connection"]}
    assert ("M60a", "M60b") in _t38_pre_no_conn, \
        f"승격 전 M60a/M60b가 세 번째 버킷에도 안 잡힘(조용히 버려짐, 세션24 수정 취지 위반): {_t38_pre_no_conn}"
    print("    PASS: 승격 전(inputs= 미선언)에는 M60a/M60b가 differential로 안 잡히지만,")
    print("    조용히 버려지지도 않고 structurally_symmetric_no_connection으로 명시 보고됨")
    print("    (Voc/Voc_des가 기본 BIAS로 분류되어 gate_class=='INPUT' 조건을 못 만족)")

    _t38_result = refine_differential_and_mirror_relations(_t38_fixture)
    assert _t38_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    assert set(_t38_result["promoted_inputs"]) == {"Voc", "Voc_des"}, \
        f"승격된 gate net이 예상과 다름: {_t38_result['promoted_inputs']}"
    assert _t38_result["stop_reason"] == "fixed_point", \
        f"고정점 도달 전에 반복이 끝남(예상 밖): {_t38_result['stop_reason']}"
    _t38_post_devs = {r["devices"] for r in _t38_result["relations"]["differential"]}
    assert ("M60a", "M60b") in _t38_post_devs, \
        f"승격 후에도 M60a/M60b가 differential로 안 잡힘(오케스트레이션 핵심 실패): {_t38_post_devs}"
    _t38_post_no_conn = {r["devices"] for r in _t38_result["relations"]["structurally_symmetric_no_connection"]}
    assert ("M60a", "M60b") not in _t38_post_no_conn, \
        f"승격 후에도 M60a/M60b가 여전히 세 번째 버킷에 남아 있음(differential로 옮겨가야 함): {_t38_post_no_conn}"
    print(f"    PASS: Voc/Voc_des가 자동 승격됨(iterations={_t38_result['iterations']},")
    print("    stop_reason=fixed_point) -- 승격 후 M60a/M60b가 no_connection에서 differential로 옮겨감")

    _t38_role_changes = {c["device"]: (c["before"], c["after"]) for c in _t38_result["role_changes"]}
    assert _t38_role_changes.get("M62") == ("ACTIVE_LOAD", "AMPLIFYING"), \
        f"M62 role 변화가 예상과 다름(연쇄효과 보고 실패): {_t38_role_changes}"
    _t38_net_changes = {c["net"]: (c["before"], c["after"]) for c in _t38_result["net_class_changes"]}
    assert _t38_net_changes.get("Voc") == ("BIAS", "INPUT"), \
        f"Voc net class 변화가 예상과 다름: {_t38_net_changes}"
    assert _t38_net_changes.get("Vcmfb_a") == ("BIAS", "SIGNAL"), \
        f"Vcmfb_a(M60a의 drain) net class 변화가 예상과 다름: {_t38_net_changes}"
    print("    PASS: 승격의 연쇄효과(Voc: BIAS->INPUT, Vcmfb_a: BIAS->SIGNAL,")
    print("    M62 role: ACTIVE_LOAD->AMPLIFYING)가 조용히 덮이지 않고 명시적으로 보고됨")
    print("    (세션23 실측 Vcmfb: BIAS->SIGNAL, M7: CURRENT_SOURCE->AMPLIFYING과 같은 패턴)")

    print()
    print("  === Test 38 전체 PASS ===")

    print()
    print("=== Test 39: find_verified_differential_and_mirror_relations() -- 세 번째 버킷")
    print("    structurally_symmetric_no_connection (세션24, 사용자 지적: \"이 대칭쌍들도")
    print("    symmetric branch로 출력되도록 해\"). 구조는 완전히 대칭인데 gate로는")
    print("    mirror/differential 어느 쪽도 확정 못 하는 쌍이 조용히 버려지지 않고")
    print("    명시적으로 보고되는지, 실회로에서 실제로 나온 M6/M7 패턴(같은 tail net에")
    print("    병렬로 물린 소자, 하나는 고정 bias 하나는 다른 신호)을 Test 35 fixture에")
    print("    M7 analog(M7t)를 얹어 재현해 검증 ===")
    _t39_fixture = _t35_fixture + [
        Transistor("M7t", "pmos", source="vdd", drain="Vx", gate="Vbias_other"),
    ]
    _t39_result = find_verified_differential_and_mirror_relations(_t39_fixture, inputs=("Vip", "Vim"))
    assert _t39_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    assert "structurally_symmetric_no_connection" in _t39_result, \
        f"세 번째 버킷 키 자체가 없음(회귀): {sorted(_t39_result)}"
    _t39_no_conn_devs = {r["devices"] for r in _t39_result["structurally_symmetric_no_connection"]}
    assert ("M6", "M7t") in _t39_no_conn_devs, \
        f"M6/M7t(구조 대칭이지만 gate 근거 없음)가 세 번째 버킷에 안 잡힘: {_t39_no_conn_devs}"
    _t39_diff_devs = {r["devices"] for r in _t39_result["differential"]}
    _t39_mirror_devs = {r["devices"] for r in _t39_result["mirror"]}
    assert ("M6", "M7t") not in _t39_diff_devs and ("M6", "M7t") not in _t39_mirror_devs, \
        f"M6/M7t가 잘못 differential/mirror로도 분류됨: diff={_t39_diff_devs}, mirror={_t39_mirror_devs}"
    assert {("M1a", "M1b")} <= _t39_diff_devs and {("M4a", "M4b")} <= _t39_diff_devs, \
        f"M7t 추가로 기존 differential 판정이 회귀함: {_t39_diff_devs}"
    assert {("M2a", "M2b")} <= _t39_mirror_devs and {("M3a", "M3b")} <= _t39_mirror_devs, \
        f"M7t 추가로 기존 mirror 판정이 회귀함: {_t39_mirror_devs}"
    print("    PASS: M6/M7t(같은 Vx를 공유하는 병렬 소자, 게이트가 다르고 둘 다 INPUT 아님)가")
    print("    structurally_symmetric_no_connection으로 명시 보고됨(differential/mirror 아님)")
    print("    -- 실회로 M6/M7과 정확히 같은 패턴, 기존 M1a/M1b 등 판정도 회귀 없음")

    print()
    print("  === Test 39 전체 PASS ===")

    print()
    print("=== Test 40: refine_differential_and_mirror_relations()의")
    print("    vertical_stack_id_candidates -- cascode-stack composite(물리) +")
    print("    differential-pair/mirror 관계(leg a/b)를 합쳐 최종 vertical_stack_id")
    print("    후보를 만드는지(세션24, 사용자 지시) Test 35 fixture로 검증 ===")
    _t40_result = refine_differential_and_mirror_relations(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t40_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t40_cand = _t40_result["vertical_stack_id_candidates"]["groups"]
    assert set(_t40_cand) == {t.name for t in _t35_fixture}, \
        f"10개 소자 전부 후보를 받아야 함: {sorted(_t40_cand)}"
    assert _t40_cand["M1a"] == _t40_cand["M2a"], \
        f"M1a/M2a가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M1a']} vs {_t40_cand['M2a']}"
    assert _t40_cand["M1b"] == _t40_cand["M2b"], \
        f"M1b/M2b가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M1b']} vs {_t40_cand['M2b']}"
    assert _t40_cand["M3a"] == _t40_cand["M4a"], \
        f"M3a/M4a가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M3a']} vs {_t40_cand['M4a']}"
    assert _t40_cand["M3b"] == _t40_cand["M4b"], \
        f"M3b/M4b가 같은 vertical_stack_id 후보를 못 받음: {_t40_cand['M3b']} vs {_t40_cand['M4b']}"
    assert _t40_cand["M1a"] != _t40_cand["M1b"], \
        f"M1a(leg a)/M1b(leg b)가 같은 그룹으로 잘못 합쳐짐: {_t40_cand['M1a']}"
    assert _t40_cand["M1a"] != _t40_cand["M3a"], \
        f"M1a/M2a(위쪽 stack)와 M3a/M4a(아래쪽 stack)가 잘못 합쳐짐: {_t40_cand['M1a']}"
    assert _t40_cand["M1a"].endswith("_a") and _t40_cand["M1b"].endswith("_b"), \
        f"leg 접미사가 안 붙음: M1a={_t40_cand['M1a']}, M1b={_t40_cand['M1b']}"
    print("    PASS: M1a/M2a, M1b/M2b, M3a/M4a, M3b/M4b가 각각 같은 그룹으로 묶이고")
    print("    (composite 병합), leg별로 다른 그룹+접미사(_a/_b)를 받음(differential 관계)")
    print("    -- 10개 소자 전부 후보 반환, 서로 다른 물리 stack끼리는 안 섞임")

    print()
    print("  === Test 40 전체 PASS ===")

    print()
    print("=== Test 41: _propose_vertical_stack_ids()의 fan-in 모호성 탐지 --")
    print("    같은 kind의 lo 후보가 2개 이상인 CASCODE 소자는 어느 쪽에도 억지로")
    print("    합치지 않고 ambiguous_{name}으로 격리하는지(세션24, 실회로 M9b/M10")
    print("    사례를 축소 재현) 검증 ===")
    _t41_fixture = [
        Transistor("Mup", "nmos", source="Vshared", drain="Vout", gate="Vbias_up"),
        Transistor("Mlo1", "nmos", source="gnd", drain="Vshared", gate="Vbias_lo1"),
        Transistor("Mlo2", "nmos", source="gnd", drain="Vshared", gate="Vbias_lo2"),
    ]
    _t41_result = refine_differential_and_mirror_relations(_t41_fixture, inputs=())
    assert _t41_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t41_groups = _t41_result["vertical_stack_id_candidates"]["groups"]
    _t41_alt = _t41_result["vertical_stack_id_candidates"]["ambiguous_alternatives"]
    assert _t41_groups["Mup"] == "ambiguous_Mup", \
        f"fan-in 후보 2개(Mlo1/Mlo2)인 Mup이 격리 안 됨: {_t41_groups}"
    assert _t41_groups["Mlo1"] != _t41_groups["Mup"] and _t41_groups["Mlo2"] != _t41_groups["Mup"], \
        f"Mup이 Mlo1/Mlo2 중 하나에 잘못 합쳐짐: {_t41_groups}"
    print("    PASS: Mup(같은 kind lo 후보 2개, Mlo1/Mlo2)이 ambiguous_Mup으로 격리되고")
    print("    Mlo1/Mlo2 어느 쪽과도 안 합쳐짐 -- 실회로 M9b(candidates=M3b,M10),")
    print("    M18b(candidates=M3a,M19), M58(candidates=M6,M7)와 같은 패턴")

    assert "Mup" in _t41_alt, f"ambiguous_alternatives에 Mup 후보 목록이 없음: {_t41_alt}"
    assert set(_t41_alt["Mup"]) == {_t41_groups["Mlo1"], _t41_groups["Mlo2"]}, \
        f"Mup의 후보 그룹이 Mlo1/Mlo2 자기 그룹과 안 맞음: {_t41_alt['Mup']} vs " \
        f"{{{_t41_groups['Mlo1']!r}, {_t41_groups['Mlo2']!r}}}"
    print("    PASS: ambiguous_alternatives['Mup']이 Mlo1/Mlo2 각자의 그룹 이름을")
    print("    정확히 담고 있음 -- layout 함수가 이 중 하나를 골라 합류시킬 수 있는 근거")

    print()
    print("  === Test 41 전체 PASS ===")

    print()
    print("=== Test 42: fan-in 후보 중 differential-pair branch 소속 여부로 재판정 --")
    print("    후보 2개 중 정확히 하나만 differential branch 소속이 아니면 그쪽으로")
    print("    확정되어 ambiguous 상태를 벗어나는지(세션24, 사용자 통찰: 실회로")
    print("    M9b->M10/M18b->M19/M58->M7이 이 규칙으로 풀림) 축소 재현으로 검증 ===")
    _t42_fixture = _t35_fixture + [
        Transistor("Mamb", "nmos", source="Nout2", drain="Vg_out", gate="Vbias_amb"),
        Transistor("Mout", "nmos", source="gnd", drain="Nout2", gate="Vbias_out2"),
    ]
    _t42_result = refine_differential_and_mirror_relations(_t42_fixture, inputs=("Vip", "Vim"))
    assert _t42_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t42_vsid = _t42_result["vertical_stack_id_candidates"]
    assert "Mamb" not in _t42_vsid["ambiguous_alternatives"], \
        f"Mamb가 differential branch 재판정으로 안 풀리고 여전히 ambiguous로 남음: {_t42_vsid['ambiguous_alternatives']}"
    assert _t42_vsid["groups"]["Mamb"] == _t42_vsid["groups"]["Mout"], \
        f"Mamb가 M3b(differential branch 소속) 대신 Mout(비소속)과 묶여야 하는데: {_t42_vsid['groups']}"
    assert _t42_vsid["groups"]["Mamb"] != _t42_vsid["groups"].get("M3b"), \
        f"Mamb가 M3b와 잘못 묶임(differential branch 오염): {_t42_vsid['groups']}"
    print("    PASS: Mamb(fan-in 후보 M3b/Mout)가 M3b는 differential branch 소속이라")
    print("    제외되고 Mout(비소속)과 묶임 -- 실회로 M9b->M10 패턴과 동일하게 재현됨")

    print()
    print("  === Test 42 전체 PASS ===")

    print()
    print("=== Test 43: refine_differential_and_mirror_relations()의")
    print("    gm_id_role_candidates -- 2026-08-13 정정(사용자 지시, two_stage_ota L 자유도")
    print("    확장 논의 계기) -- L_role(mirror/bias_replica) 둘 다 레이아웃 매칭이 필요하므로")
    print("    최종 노출값은 전부 matching으로 통일됐는지(원래 tail 소자만 balanced였던 걸")
    print("    matching으로 덮어씀), headroom_role_candidates(tail 판정)는 원본 신호를 써서")
    print("    안 바뀌는지 Test 35 fixture로 검증 ===")
    _t43_result = refine_differential_and_mirror_relations(_t35_fixture, inputs=("Vip", "Vim"))
    assert _t43_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t43_gmid = _t43_result["gm_id_role_candidates"]
    assert set(_t43_gmid) == {t.name for t in _t35_fixture}, \
        f"10개 소자 전부 후보를 받아야 함: {sorted(_t43_gmid)}"
    assert all(_t43_gmid[n] == "matching" for n in _t43_gmid), \
        f"L_role(mirror/bias_replica)로 덮이는 소자는 전부 matching으로 덮어써야 함(M5/M6 " \
        f"tail 소자 포함): {_t43_gmid}"
    _t43_headroom = _t43_result["headroom_role_candidates"]
    assert _t43_headroom.get("M6") == "tail" and _t43_headroom.get("M5") == "tail", \
        (f"gm_id_role_candidates를 matching으로 덮어써도 headroom_role_candidates의 tail "
         f"판정(원본 balanced 신호 사용)은 안 바뀌어야 함: M6={_t43_headroom.get('M6')!r}, "
         f"M5={_t43_headroom.get('M5')!r}")
    print("    PASS: 10개 소자 전부 gm_id_role_candidates='matching'(M5/M6 tail 소자도 포함,")
    print("    매칭 보호가 필요하다는 사용자 판단 반영) -- 그러나 headroom_role_candidates는")
    print("    M5/M6 둘 다 여전히 'tail'로 정확히 분류됨(내부 원본 신호는 안 바뀜)")

    print()
    print("  === Test 43 전체 PASS ===")

    print()
    print("=== Test 44: suggest_vertical_stack_composites()가 idioms.Match.ports를")
    print("    조용히 버리지 않고 composite에 보존하는지(사용자 지적: M8/M9a가 물리적으론")
    print("    캐스코드 스택이 맞지만, M8=mirror 기준/M9a=그 위 캐스코드라는 구분이")
    print("    composite 단계에서 사라지고 있었음) Test 35 fixture로 검증 ===")
    _t44_branches = suggest_vertical_stack_composites(_t35_fixture, inputs=("Vip", "Vim"), direction="vdd_to_gnd")
    _t44_composite = None
    for b in _t44_branches:
        for c in b["composites"]:
            if set(c["members"]) == {"M1a", "M2a"}:
                _t44_composite = c
                break
    assert _t44_composite is not None, "M1a/M2a cascode-stack composite을 못 찾음(회귀)"
    assert _t44_composite["ports"].get("lower_role") == "AMPLIFYING", \
        f"lower_role(M1a의 role)이 ports에 보존돼야 함: {_t44_composite}"
    print("    PASS: M1a/M2a composite의 ports에 lower_role='AMPLIFYING'(M1a의 role)이")
    print("    그대로 보존됨 -- 이전엔 {'members','idiom'}만 남기고 버려지던 정보")

    print()
    print("  === Test 44 전체 PASS ===")

    print()
    print("=== Test 45: refine_differential_and_mirror_relations()의")
    print("    headroom_role_candidates -- 6가지 실패한 가설 끝에 나온 37/37 규칙")
    print("    (role==FLOATING_CURRENT_SOURCE/DIODE_REFERENCED_CASCODE 분리 +")
    print("    mirror_ref/그룹/대칭 판정, 세션25, 사용자와 함께 여러 라운드 검증)이")
    print("    tail/cascode/mirror/floating_current_source 네 값 전부와 mirror_ref")
    print("    유무에 따른 diode-cascode 분기(있음/없음)까지 실제로 가르는지 합성")
    print("    fixture로 검증 ===")
    _t45_fixture = _t35_fixture + [
        # Monticelli floating-current-source 축소 재현(M8/M9a/M9b/M10)
        Transistor("M8", "pmos", source="vdd", drain="Vg", gate="Vbias5"),
        Transistor("M9a", "pmos", source="Vg", drain="Vout", gate="Nref1"),
        Transistor("M9b", "nmos", source="Vout", drain="Vg", gate="Nref2"),
        Transistor("M10", "nmos", source="gnd", drain="Vout", gate="Vbias6"),
        # diode-cascode WITH mirror_ref: M50(bottom cs)-M51(lo)-M52(diode,top),
        # M53이 M52와 (gate,source,type) 공유 -> M52가 current-mirror ref가 됨
        Transistor("M50", "pmos", source="vdd", drain="Va", gate="Vbias7"),
        Transistor("M51", "pmos", source="Va", drain="Vb", gate="Vc"),
        Transistor("M52", "pmos", source="Vb", drain="Vc", gate="Vc"),
        Transistor("M53", "pmos", source="Vb", drain="Vd", gate="Vc"),
        # diode-cascode WITHOUT mirror_ref: M60(bottom cs)-M61(lo)-M62(diode,top),
        # 짝 없는 단독 diode
        Transistor("M60", "nmos", source="gnd", drain="Ve", gate="Vbias8"),
        Transistor("M61", "nmos", source="Ve", drain="Vf", gate="Vg2"),
        Transistor("M62", "nmos", source="Vf", drain="Vg2", gate="Vg2"),
    ]
    _t45_result = refine_differential_and_mirror_relations(_t45_fixture, inputs=("Vip", "Vim"))
    assert _t45_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t45_hr = _t45_result["headroom_role_candidates"]
    assert set(_t45_hr) == {t.name for t in _t45_fixture}, \
        f"headroom_role_candidates가 fixture 전체 소자를 다 포함해야 함: {set(_t45_hr)}"
    _t45_expected = {
        "M6": "tail", "M5": "tail",                              # 진짜 차동쌍 tail
        "M1a": None, "M1b": None, "M4a": None, "M4b": None,      # AMP(차동쌍 입력) -- 규칙 밖
        "M2a": "cascode", "M2b": "cascode",                       # 고정 게이트 캐스코드
        "M3a": "cascode", "M3b": "cascode",
        "M8": "mirror", "M10": "mirror",                          # floating loop 위/아래 전류원
        "M9a": "floating_current_source", "M9b": "floating_current_source",
        "M50": "mirror",                                          # 레일에 직접 닿은 전류원
        "M51": "mirror",     # diode-cascode lo, 파트너(M52)가 mirror_ref -> mirror
        "M52": "mirror",     # diode 자신이 mirror_ref(M53가 미러함)
        "M53": "cascode",    # M52를 미러하는 별도 branch, 고정 게이트 캐스코드
        "M60": "mirror",                                          # 레일에 직접 닿은 전류원
        "M61": "cascode",    # diode-cascode lo, 파트너(M62)가 mirror_ref 아님 -> cascode
        "M62": "cascode",    # diode 자신도 mirror_ref 아니고 대칭 파트너도 없음
    }
    for name, expected in _t45_expected.items():
        actual = _t45_hr.get(name)
        assert actual == expected, \
            f"{name}: headroom_role 후보가 {expected!r}이어야 하는데 {actual!r} -- 회귀 의심"
    print("    PASS: tail(M6/M5) / cascode(M2a/M2b/M3a/M3b) / floating_current_source")
    print("    (M9a/M9b) / mirror(M8/M10/M50/M60) 기본 갈래 전부 정확")
    print("    PASS: diode-cascode lo가 diode 파트너의 mirror_ref 여부를 그대로 물려받음")
    print("    -- M51(파트너 M52가 mirror_ref)=mirror, M61(파트너 M62가 mirror_ref 아님)=cascode")
    print("    PASS: 차동쌍 입력(M1a/M1b/M4a/M4b)은 None(compensation.stage_devices 소관,")
    print("    이 규칙 범위 밖) -- 51개(여기선 fixture 전체) 일관 반환, 하드코딩 제외 없음")

    print()
    print("  === Test 45 전체 PASS ===")

    print()
    print("=== Test 46: find_verified_differential_and_mirror_relations()의")
    print("    differential_branch_members -- '진짜 differential branch 소속'과")
    print("    'symmetric(mirror) branch 소속'을 방향(vdd_to_gnd/gnd_to_vdd)에 안")
    print("    흔들리고 정확히 구별하는지(세션25, 사용자 통찰: M10은 M19와의 진짜")
    print("    mirror 관계 당사자라 differential branch가 아니다, M3a/M3b는 M4a/M4b")
    print("    differential 발견의 상류라 mirror 관계이면서도 진짜 differential branch")
    print("    소속이다) 합성 fixture로 검증 ===")
    _t46_fixture = _t35_fixture + [
        Transistor("M7", "pmos", source="vdd", drain="Vx", gate="Vbias5"),
        # M2a/M2b의 drain(Nout1/Nout2)에서 갈라지는 별개 mirror branch(M19/M10류) --
        # M1a/M1b differential 발견과 같은 chain-prefix를 공유하지만 그 발견의 하류
        # (혹은 gnd_to_vdd 역순에서는 상류처럼 보이는) 무관한 분기.
        Transistor("Mfork_a", "nmos", source="gnd", drain="Nout1", gate="Vbias6"),
        Transistor("Mfork_b", "nmos", source="gnd", drain="Nout2", gate="Vbias6"),
    ]
    _t46_result = refine_differential_and_mirror_relations(_t46_fixture, inputs=("Vip", "Vim"))
    assert _t46_result is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t46_diff_mem = set(_t46_result["relations"]["differential_branch_members"])
    for dev in ("M6", "M7", "M1a", "M1b", "M4a", "M4b", "M3a", "M3b"):
        assert dev in _t46_diff_mem, \
            f"{dev}는 진짜 differential branch 소속이어야 하는데 빠짐: {_t46_diff_mem}"
    for dev in ("Mfork_a", "Mfork_b"):
        assert dev not in _t46_diff_mem, \
            f"{dev}는 별개 mirror branch 소속이라 제외돼야 하는데 포함됨: {_t46_diff_mem}"
    print("    PASS: M6/M7(병렬 tail, 서로 structurally_symmetric_no_connection)과")
    print("    M3a/M3b(M4a/M4b 발견의 상류이자 서로 mirror 관계)는 전부 differential")
    print("    branch 소속으로 정확히 포함됨")
    print("    PASS: Mfork_a/Mfork_b(M19/M10류 별개 mirror branch, M1a/M1b 발견과")
    print("    chain-prefix만 우연히 겹침)는 정확히 제외됨 -- 방향 인식 상류 슬라이스가")
    print("    이 구별을 만들어냄(단순 전체 체인 누적이나 무조건 mirror 배제 둘 다 실패했던")
    print("    반례들)")

    print()
    print("  === Test 46 전체 PASS ===")

    print()
    print("=== Test 47: audit_vertical_stack_id_vs_kcl() -- declared vertical_stack_id와")
    print("  kcl_series_union()의 불일치를 internal_series/declared_matching_pair/")
    print("  multi_terminal_hub로 자동 분류하는지(2026-08-10 세션 대화, 사용자와 함께")
    print("  M11b/M12 진짜 직렬 체인 + M9a/M9b류 floating-current-source 3-branch 허브")
    print("  두 반례를 실측으로 확인한 뒤 신설) current_reuse_telescopic_ota.topology.json")
    print("  실회로(51소자)로 검증 -- 손타이핑 넷리스트 없음. ⚠️ 원래 예시였던 M11b/M12는")
    print("  세션27이 헤드룸 버그 수정으로 M11a/M11b/M12를 같은 vertical_stack_id로")
    print("  합쳐 이 divergence 자체가 해소됐다(의도된 결과) -- 세션28에서 같은 패턴의")
    print("  다른 실측 사례(M60/M66, Vbias4 2단자 직렬, 세션27이 손대지 않은 그룹)로")
    print("  교체해 감사 함수의 검증력을 유지한다 ===")
    import os as _os47
    _lib47 = _os47.path.join(_os47.path.dirname(_os47.path.abspath(__file__)), "library")
    _t47_trs, _t47_meta = load_topology(
        _os47.path.join(_lib47, "current_reuse_telescopic_ota.topology.json"))
    _t47_pairs_meta = _t47_meta["symmetry"]["matching_pairs"]
    _t47_forced = [tuple(p["names"]) for p in _t47_pairs_meta if p["current_forced"]]
    _t47_device_roles = {k: v for k, v in (_t47_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _t47_result = audit_vertical_stack_id_vs_kcl(_t47_trs, _t47_forced, _t47_device_roles)

    _t47_m60_m66 = [f for f in _t47_result["boundary_findings"]
                      if set(f["pair"]) == {"M60", "M66"}]
    assert len(_t47_m60_m66) == 1, f"M60/M66 경계가 안 잡힘: {_t47_m60_m66}"
    assert _t47_m60_m66[0]["kcl_reason"] == "internal_series" and _t47_m60_m66[0]["detail"] == "Vbias4", \
        f"M60/M66는 Vbias4 2단자 직렬이 원인이어야 하는데: {_t47_m60_m66[0]}"
    print("    PASS: M60(vbias4_gen)/M66(vbias4_stack) -- "
          "Vbias4 2단자 직렬(진짜 KCL 체인)이 declared vsid 기능 경계를 가로지름을 정확히 검출")

    _t47_hub_by_vsid = {f["vsid"]: f for f in _t47_result["hub_findings"]}
    for _vsid, _hub_net, _terminals_min in [
            ("biasgen_vom_a", "Vg15", 3), ("biasgen_vom_floatsrc_sink", "Vg15", 3),
            ("biasgen_vop_a", "Vg25", 3), ("biasgen_vop_floatsrc_sink", "Vg25", 3)]:
        assert _vsid in _t47_hub_by_vsid, f"{_vsid} hub_finding 누락"
        _nets = dict(_t47_hub_by_vsid[_vsid]["candidate_hub_nets"])
        assert _nets.get(_hub_net, 0) >= _terminals_min, \
            f"{_vsid}: {_hub_net}가 {_terminals_min}단자 이상 허브로 안 잡힘: {_nets}"
    print("    PASS: M9a/M9b(Vg15/Vop1)·M18a/M18b(Vg25/Vom1) floating-current-source 4개")
    print("    declared 그룹 전부 3+단자 허브(candidate_hub_nets)로 정확히 설명됨 -- ")
    print("    kcl_series_union()의 union-find로는 못 푸는 3-branch KCL이라는 신호 그대로 반환")

    _t47_unexplained_hubs = [f for f in _t47_result["hub_findings"] if not f["candidate_hub_nets"]]
    _t47_gaps = [f for f in _t47_result["boundary_findings"] if f["note"]]
    assert _t47_unexplained_hubs == [], \
        f"실회로에서 원인 불명 hub_finding이 나오면 안 됨(이번 회로는 완전 정합): {_t47_unexplained_hubs}"
    assert _t47_gaps == [], \
        f"실회로에서 vertical_stack_id gap이 나오면 안 됨(51/51 선언 완료 회로): {_t47_gaps}"
    print(f"    PASS: candidate_hub_nets 없는 review 대상 0건, vsid gap 0건 -- "
          f"declared vertical_stack_id가 이 회로의 KCL 현실과 완전히 정합함을 재확인")

    print()
    print("  === Test 47 전체 PASS ===")

    print()
    print("=== Test 48: merge_layout_groups_by_matching_pairs() -- vertical_stack_id 기반")
    print("  그룹(수직 방향만 앎)이 서로 다른 물리 branch에 있는 매칭 파트너를 잡아주지")
    print("  못하는 문제(2026-08-10 세션26 후속 J-4/J-9, folded_cascode 5개 매칭쌍 전부")
    print("  3b/3c 실패 실측)를, geometry_colocation_union()의 위험한 재귀 climb 없이")
    print("  그룹 단위 union만으로 해결하는지 -- folded_cascode 실회로(candidates 경로)로")
    print("  검증. 손타이핑 넷리스트 없음 ===")
    import os as _t48_os
    _t48_lib = _t48_os.path.join(_t48_os.path.dirname(_t48_os.path.abspath(__file__)), "library")
    _t48_trs, _t48_meta = load_topology(
        _t48_os.path.join(_t48_lib, "folded_cascode.topology.json"))
    _t48_pairs_meta = _t48_meta["symmetry"]["matching_pairs"]
    _t48_forced = [tuple(p["names"]) for p in _t48_pairs_meta if p["current_forced"]]

    _t48_refined = refine_differential_and_mirror_relations(_t48_trs)
    assert _t48_refined is not None, "analog-grammar 있는데 None 반환(회귀)"
    _t48_candidates = {}
    for _name, _sid in _t48_refined["vertical_stack_id_candidates"]["groups"].items():
        _t48_candidates.setdefault(_sid, []).append(_name)

    _t48_before_pairs_together = sum(
        1 for _names in _t48_forced
        for _a, _b in zip(_names, _names[1:])
        if any({_a, _b} <= set(_members) for _members in _t48_candidates.values()))
    assert _t48_before_pairs_together == 0, \
        f"병합 전에 이미 매칭쌍이 같은 그룹이면 이 테스트가 검증하려는 문제가 재현 안 됨: " \
        f"{_t48_before_pairs_together}건"
    print(f"    확인: 병합 전(candidates 그룹 {len(_t48_candidates)}개)에는 declared 매칭쌍 "
          f"{len(_t48_forced)}개 전부 서로 다른 그룹(문제 재현)")

    _t48_merged = merge_layout_groups_by_matching_pairs(_t48_trs, _t48_candidates, _t48_forced)
    _t48_all_members = sorted(m for members in _t48_merged.values() for m in members)
    assert _t48_all_members == sorted(t.name for t in _t48_trs), \
        "merge_layout_groups_by_matching_pairs()가 소자를 빠뜨리거나 중복시킴"

    _t48_group_sets = {frozenset(members) for members in _t48_merged.values()}
    assert frozenset({"M1", "M2"}) in _t48_group_sets, f"M1/M2가 병합 안 됨: {_t48_group_sets}"
    assert frozenset({"M3", "M4"}) in _t48_group_sets, f"M3/M4가 병합 안 됨: {_t48_group_sets}"
    assert frozenset({"M7", "M8", "M9", "M10"}) in _t48_group_sets, \
        f"M7/M8/M9/M10(두 물리스택이 M9/M10 매칭쌍으로 이어짐)이 병합 안 됨: {_t48_group_sets}"
    print("    PASS: declared 매칭쌍(current_forced=True)마다 그룹이 정확히 합쳐짐 -- "
          "{M1,M2}/{M3,M4}/{M7,M8,M9,M10}(M9/M10 매칭쌍이 두 물리스택을 이어붙임)")

    for _isolated in ("M5", "M6"):
        assert frozenset({_isolated}) in _t48_group_sets, \
            f"{_isolated}(candidates가 ambiguous로 격리, current_forced=False라 매칭 기준에도 " \
            f"없음)은 그대로 격리 유지돼야 하는데 다른 그룹과 합쳐짐: {_t48_group_sets}"
    print("    PASS: M5/M6(ambiguous 격리 + current_forced=False) -- 매칭쌍 기준에 안 걸려서 "
          "우회 병합도 전혀 안 되고 격리 그대로 유지됨(geometry_colocation_union()의 실제 "
          "버그였던 M6을 통한 M1/M2<->M3/M4 우회 병합이 이 함수에선 구조적으로 불가능함을 확인)")

    print()
    print("  [current_forced=False까지 전부 넘기면(세션9/10 dx 악화 반례 재현 의도)")
    print("  M5/M6도 시도는 되는지 -- ⚠️ 2026-08-10 오일러 게이트 신설 이후 재확인:")
    print("  M5/M6은 공유 net이 아예 없어(source=Y/drain=Vg7 vs source=X/drain=out) 어떤")
    print("  핑거조정으로도 연결 안 됨 -- 오일러 게이트가 이 병합 자체를 막는다(필터링과")
    print("  다른 이유). 함수가 current_forced를 몰래 걸러서가 아니라 진짜 연결 불가능")
    print("  해서 안 합쳐진다는 걸 구분해서 확인]")
    _t48_all_pairs = [tuple(p["names"]) for p in _t48_pairs_meta]
    _t48_merged_all = merge_layout_groups_by_matching_pairs(_t48_trs, _t48_candidates, _t48_all_pairs)
    _t48_group_sets_all = {frozenset(members) for members in _t48_merged_all.values()}
    assert frozenset({"M5"}) in _t48_group_sets_all and frozenset({"M6"}) in _t48_group_sets_all, \
        f"M5/M6은 공유 net이 없어 오일러 게이트가 병합을 막아야 하는데 합쳐짐(회귀): {_t48_group_sets_all}"
    print("    OK: M5/M6은 여전히 안 합쳐짐 -- current_forced 필터링이 아니라 오일러 게이트가 "
          "막은 것(둘이 진짜 물리적으로 무관하므로 정당)")

    print()
    print("  [current_forced=False라도 실제로 물리적으로 이어진(오일러 실현 가능한) 쌍이면")
    print("  이 함수가 필터링 없이 그대로 병합함을 합성 fixture로 확인 -- \"기본값은")
    print("  current_forced=True만 권장\"이 강제가 아니라 권고일 뿐임을 증명]")
    _t48_syn_trs = [
        Transistor("Sa", "nmos", source="sn1", drain="sn2"),
        Transistor("Sb", "nmos", source="sn2", drain="sn3"),  # Sa와 진짜 직렬(2단자 sn2 공유)
    ]
    _t48_syn_groups = {"Sa": ["Sa"], "Sb": ["Sb"]}
    _t48_syn_merged = merge_layout_groups_by_matching_pairs(
        _t48_syn_trs, _t48_syn_groups, [("Sa", "Sb")])  # current_forced 여부와 무관하게 이 함수는 그냥 쌍만 봄
    assert frozenset({"Sa", "Sb"}) in {frozenset(v) for v in _t48_syn_merged.values()}, \
        f"물리적으로 직렬(오일러 실현 가능)인 쌍은 current_forced 여부와 무관하게 병합돼야 함: {_t48_syn_merged}"
    print("    OK: 물리적으로 이어진 쌍은 current_forced 값과 무관하게 병합됨 -- "
          "필터링은 함수가 강제하지 않고 호출자(resolve_stack_layout())의 책임으로 남김")

    print()
    print("  === Test 48 전체 PASS ===")

    print()
    print("=== Test 49: audit_vertical_stack_id_euler_feasibility() -- declared")
    print("  vertical_stack_id 그룹이 그 자체로 오일러 실현 가능한지(merge_layout_")
    print("  groups_by_matching_pairs()의 오일러 게이트가 손 못 대는, 병합 이전부터")
    print("  이미 declared로 들어온 그룹의 문제) 검사. 2026-08-10 세션26 후속(2) K-3")
    print("  cmfb_tail 추적 중 발견한 suggest_pair_finger_adjustments()의 연결성 착시")
    print("  (resulting_odd_count는 홀짝만 보고 그래프가 끊겼는지는 안 봄)를 실제")
    print("  적용+재검증으로 피하는지도 함께 검증. 2026-08-11(세션28) 신설 kind_mismatch")
    print("  finding(PMOS/NMOS 혼합 declared 그룹)도 크래시 대신 구조화 보고되는지 확인 ===")
    import os as _t49_os
    _t49_lib = _t49_os.path.join(_t49_os.path.dirname(_t49_os.path.abspath(__file__)), "library")
    _t49_trs, _t49_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t49_pairs_meta = _t49_meta["symmetry"]["matching_pairs"]
    _t49_forced = [tuple(p["names"]) for p in _t49_pairs_meta if p["current_forced"]]
    _t49_device_roles = {k: v for k, v in (_t49_meta.get("device_roles") or {}).items()
                          if not k.startswith("_")}
    _t49_result = audit_vertical_stack_id_euler_feasibility(_t49_trs, _t49_device_roles, _t49_forced)
    _t49_by_vsid = {f["vsid"]: f for f in _t49_result["findings"]}
    assert "cmfb_tail" in _t49_by_vsid, \
        f"cmfb_tail(M37a/M37b/M38)이 findings에 안 잡힘(회귀 -- 이 그룹은 실제로 " \
        f"n_fingers=1 기준 오일러 impossible이어야 함): {_t49_result}"
    _t49_cmfb = _t49_by_vsid["cmfb_tail"]
    assert _t49_cmfb["members"] == ["M37a", "M37b", "M38"], f"멤버 불일치: {_t49_cmfb}"
    assert set(_t49_cmfb["odd_nodes"]) == {"N36b", "Ncmfb_tail", "Vcmfb", "gnd"}, \
        f"홀수차수 노드 불일치: {_t49_cmfb['odd_nodes']}"
    assert _t49_cmfb["resolvable_by_finger_adjustment"] is True, \
        f"cmfb_tail은 M38(또는 M37a/M37b) 핑거 +1로 실제 검증 가능한데 False로 나옴: {_t49_cmfb}"
    assert _t49_cmfb["verified_suggestion"] is not None
    assert _t49_cmfb["kind_mismatch"] is False, f"cmfb_tail은 전부 nmos인데 kind_mismatch=True: {_t49_cmfb}"
    print(f"    PASS: cmfb_tail(M37a/M37b/M38) -- n_fingers=1 기준 오일러 impossible(홀수차수 4개, "
          f"Ncmfb_tail이 M37a/M37b의 source이자 M38의 drain인 3단자 허브) 정확히 검출")
    print(f"    PASS: resolvable_by_finger_adjustment=True -- 제안({_t49_cmfb['verified_suggestion']})을 "
          f"실제로 적용해 재검증(연결성 포함)까지 통과함을 확인(단순 resulting_odd_count<=2 착시가 아님)")

    # 2026-08-11(세션28) -- build_graph()의 kind 동질성 하드 게이트 신설 이후, 이 회로의
    # declared vertical_stack_id 26개 중 8개가 실제로 PMOS/NMOS를 섞고 있음이 이 감사로
    # 처음 드러났다(class-AB 출력단 output_stage_a/b 포함 -- "vertical_stack_id"가 VDD->GND
    # 전기적 컬럼이라 애초에 정의상 극성 경계를 넘나드는 게 정상이라는 뜻, 세션28 대화
    # 참고). 이 8개는 finger 조정으로 못 고치는 구조적 문제이므로 kind_mismatch=True로
    # 명확히 구분돼야 한다 -- cmfb_tail(홀짝-차수 문제, kind_mismatch=False)과 섞이면 안 됨.
    _t49_kind_mismatch_vsids = {"biasgen_vom_battery_a", "biasgen_vom_battery_b",
                                 "biasgen_vop_battery_a", "biasgen_vop_battery_b",
                                 "vbias2_stack", "vbias3_stack",
                                 "output_stage_a", "output_stage_b"}
    _t49_other_findings = [f for f in _t49_result["findings"] if f["vsid"] != "cmfb_tail"]
    _t49_other_vsids = {f["vsid"] for f in _t49_other_findings}
    assert _t49_other_vsids == _t49_kind_mismatch_vsids, \
        f"cmfb_tail 외 kind_mismatch finding 집합이 예상과 다름(회귀 또는 declared vsid 변경): " \
        f"실제={_t49_other_vsids}, 예상={_t49_kind_mismatch_vsids}"
    assert all(f["kind_mismatch"] is True for f in _t49_other_findings), \
        f"kind_mismatch 그룹인데 False로 나온 항목: {[f for f in _t49_other_findings if not f['kind_mismatch']]}"
    assert all(f["resolvable_by_finger_adjustment"] is False and f["verified_suggestion"] is None
               for f in _t49_other_findings), \
        f"kind_mismatch는 finger 조정으로 못 고치므로 resolvable/verified_suggestion 둘 다 " \
        f"False/None이어야 하는데: {_t49_other_findings}"
    assert all(f["kinds"] == ["nmos", "pmos"] for f in _t49_other_findings), \
        f"kind_mismatch finding의 kinds 필드 불일치: {[f['kinds'] for f in _t49_other_findings]}"
    print(f"    PASS: cmfb_tail 외 {len(_t49_other_findings)}개 declared vsid 그룹"
          f"({sorted(_t49_other_vsids)})이 전부 kind_mismatch=True로 정확히 구분 보고됨 -- "
          f"PMOS/NMOS 혼합(전기적 컬럼 개념상 정상)을 크래시 없이 감사 결과로 포착")

    print()
    print("  [합성 fixture -- 완전히 무관한(공유 net 없는) 두 소자를 한 declared 그룹으로")
    print("  잘못 선언한 경우, suggest_pair_finger_adjustments()의 resulting_odd_count가")
    print("  연결성을 안 보고 착시를 일으키는지, 이 함수가 실제 적용+재검증으로 정확히")
    print("  잡아내는지(진짜 review 대상 = resolvable_by_finger_adjustment=False) 확인]")
    _t49_iso_trs = [
        Transistor("T1", "nmos", source="n1", drain="n2"),
        Transistor("T2", "nmos", source="n3", drain="n4"),
    ]
    _t49_iso_roles = {"T1": {"vertical_stack_id": "isolated_test_group"},
                       "T2": {"vertical_stack_id": "isolated_test_group"}}
    _t49_iso_result = audit_vertical_stack_id_euler_feasibility(_t49_iso_trs, _t49_iso_roles, [])
    assert len(_t49_iso_result["findings"]) == 1, f"1건 잡혀야 함: {_t49_iso_result}"
    _t49_iso_finding = _t49_iso_result["findings"][0]
    assert _t49_iso_finding["resolvable_by_finger_adjustment"] is False, (
        f"T1/T2는 서로 공유 net이 아예 없어 어떤 핑거 조정으로도 연결 안 됨(진짜 review "
        f"대상)인데 True로 나옴 -- suggest_pair_finger_adjustments()의 resulting_odd_count "
        f"착시(연결성 미검사)를 못 걸렀다는 뜻: {_t49_iso_finding}")
    print("    PASS: 서로 무관한 두 소자를 잘못 한 그룹으로 선언한 경우 "
          "resolvable_by_finger_adjustment=False로 정확히 구분됨(연결성 착시 회피 확인)")

    print()
    print("  === Test 49 전체 PASS ===")

    print()
    print("=== Test 50: find_euler_repair_options() -- unresolved_row를 resolved로")
    print("  만들려면 어떤 row를 병합해야 하는지 찾는 탐색(2026-08-10 사용자 질문으로")
    print("  신설). 실제 optimize_full_circuit_budget() 끝까지 태운 뒤 unresolved_row로")
    print("  남았던 두 실사례(cmfb_tail/biasgen_ref)를 이 함수로 진단하면 놀랍게도")
    print("  **병합이 전혀 필요 없다** -- 같은 행 안 핑거 조정 하나로 이미 풀린다(실측)")
    print("  -- run_topology_pipeline_with_finger_fixup()이 이 해법을 못 찾고 포기했을")
    print("  뿐. 그리고 합성 fixture로 '진짜 병합이 필요한' 경우도 검증 ===")
    _t50_by_name = {t.name: t for t in _t49_trs}
    _t50_cmfb_r = find_euler_repair_options(
        _t49_trs, ["M37a", "M37b", "M38"], _t49_forced, candidate_groups=None)
    assert _t50_cmfb_r["same_row_fix"] is not None, \
        f"cmfb_tail은 같은 행 안에서 풀려야 하는데(Test 49로 이미 확인됨) 못 찾음: {_t50_cmfb_r}"
    assert _t50_cmfb_r["merge_candidates"] == [], \
        "same_row_fix가 있으면 merge_candidates는 항상 빈 리스트여야 함(2단계 안 돌림)"
    print(f"    PASS: cmfb_tail -- 같은 행 안 조정으로 해결됨(병합 불필요), "
          f"제안={_t50_cmfb_r['same_row_fix']['verified_suggestion']}")

    _t50_bg_r = find_euler_repair_options(
        _t49_trs, ["M18_bg", "M60", "M61"], _t49_forced, candidate_groups=None)
    assert _t50_bg_r["same_row_fix"] is not None, \
        f"biasgen_ref(M18_bg/M60/M61)도 같은 행 안에서 풀려야 하는데 못 찾음: {_t50_bg_r}"
    print(f"    PASS: biasgen_ref(M18_bg/M60/M61) -- 같은 행 안 조정으로 해결됨(병합 불필요), "
          f"제안={_t50_bg_r['same_row_fix']['verified_suggestion']} -- 즉 이 실사례들의 진짜 "
          f"원인은 '병합이 필요한 구조적 문제'가 아니라 다운스트림 fixup 탐색 전략의 gap이었음")

    print()
    print("  [합성 fixture -- 같은 행 안에서는 절대 안 풀리는(서로 완전히 끊긴) blocked 그룹을")
    print("  만들고, 후보 row 2개(하나는 진짜 다리 역할, 하나는 완전히 무관) 중 실제로 연결을")
    print("  살려주는 쪽만 merge_candidates로 정확히 찾아내는지 확인]")
    _t50_blocked = [Transistor("X1", "nmos", source="a", drain="b"),
                    Transistor("X2", "nmos", source="c", drain="d")]
    _t50_bridge = [Transistor("Y1", "nmos", source="b", drain="c")]
    _t50_unrelated = [Transistor("Z1", "nmos", source="e", drain="f")]
    _t50_all = _t50_blocked + _t50_bridge + _t50_unrelated
    _t50_syn_r = find_euler_repair_options(
        _t50_all, ["X1", "X2"], [],
        candidate_groups={"bridge_row": ["Y1"], "unrelated_row": ["Z1"]})
    assert _t50_syn_r["same_row_fix"] is None, \
        f"X1/X2는 서로 완전히 끊겨 같은 행 안에서는 절대 안 풀려야 함: {_t50_syn_r}"
    _t50_cand_rows = [c["row"] for c in _t50_syn_r["merge_candidates"]]
    assert _t50_cand_rows == ["bridge_row"], \
        f"다리 역할을 하는 bridge_row만 후보로 잡히고 unrelated_row는 빠져야 함: {_t50_cand_rows}"
    print("    PASS: same_row_fix=None(진짜 병합 필요) -- bridge_row(b-c를 이어줌)만 "
          "merge_candidates로 정확히 찾고, unrelated_row(완전히 무관)는 제외됨")

    print()
    print("  === Test 50 전체 PASS ===")

    print()
    print("=== Test 51: derive_horizontal_stack_groups() -- vertical_stack_id 그룹(전기적")
    print("  컬럼, PMOS/NMOS 혼합 가능)을 kind로 분할한 뒤 declared matching_pairs로 대칭")
    print("  branch끼리 재병합해 물리 레이아웃 행(kind 동질, 오일러 대상) 후보를 만드는지")
    print("  검증(2026-08-11 세션28 후반부, 사용자 설계 제안 -- vertical_stack_id는 헤드룸")
    print("  전용, 물리 레이아웃 행은 레이아웃 전용으로 두 축을 분리) ===")
    _t51_by_name = {t.name: t for t in _t49_trs}
    _t51_declared = {k: v.get("vertical_stack_id") for k, v in _t49_device_roles.items()
                      if isinstance(v, dict) and v.get("vertical_stack_id")}
    _t51_vgroups = defaultdict(list)
    for _t51_name, _t51_sid in _t51_declared.items():
        _t51_vgroups[_t51_sid].append(_t51_name)
    for _t51_t in _t49_trs:
        if _t51_t.name not in _t51_declared:
            _t51_vgroups[_t51_t.name].append(_t51_t.name)

    _t51_hgroups = derive_horizontal_stack_groups(_t49_trs, dict(_t51_vgroups), _t49_forced)

    _t51_all_members = sorted(m for members in _t51_hgroups.values() for m in members)
    assert _t51_all_members == sorted(t.name for t in _t49_trs), \
        f"51/51 소자 전부 커버해야 하는데 손실/중복 발생: 실제 {len(_t51_all_members)}개"
    print(f"    PASS: {len(_t51_hgroups)}개 물리 레이아웃 행으로 51/51 소자 전부 커버 "
          f"(손실/중복 없음)")

    for _t51_hsid, _t51_members in _t51_hgroups.items():
        _t51_kinds = {_t51_by_name[m].kind for m in _t51_members if m in _t51_by_name}
        assert len(_t51_kinds) <= 1, f"{_t51_hsid} 그룹이 kind 동질이 아님(회귀): {_t51_members} -> {_t51_kinds}"
    print("    PASS: 반환된 모든 그룹이 kind 동질(PMOS/NMOS 혼합 0건)")

    _t51_group_of = {m: hsid for hsid, members in _t51_hgroups.items() for m in members}
    assert _t51_group_of["M15"] == _t51_group_of["M25"], \
        f"output_stage_a/b의 PMOS 절반(M15/M25)이 M15-M25 매칭쌍으로 재병합돼야 함: {_t51_hgroups}"
    assert _t51_group_of["M16"] == _t51_group_of["M26"], \
        f"output_stage_a/b의 NMOS 절반(M16/M26)이 M16-M26 매칭쌍으로 재병합돼야 함: {_t51_hgroups}"
    assert _t51_group_of["M15"] != _t51_group_of["M16"], \
        "M15(pmos)/M16(nmos)는 같은 vertical_stack_id(output_stage_a)였지만 물리 행에서는 분리돼야 함"
    print(f"    PASS: output_stage_a/output_stage_b(class-AB 출력단, 전기적으론 M15=pmos+"
          f"M16=nmos 한 컬럼) -- PMOS 절반(M15,M25)/NMOS 절반(M16,M26)이 각각 kind 동질 "
          f"물리 행으로 올바르게 재병합됨(vsid={_t51_group_of['M15']!r}/{_t51_group_of['M16']!r}) -- "
          f"게이트만 있고 kind-split이 없던 상태(세션28 (a) 직후)에서는 이 재병합 자체가 안 됐었음")

    print()
    print("  [합성 fixture -- 매칭 파트너가 없는 순수 mixed-kind vsid 하나가 kind로만")
    print("  정확히 쪼개지는지(병합 시도 없이) 확인]")
    _t51_syn_trs = [
        Transistor("SP1", "pmos", source="vdd", drain="mid"),
        Transistor("SN1", "nmos", source="mid", drain="gnd"),
    ]
    _t51_syn_groups = derive_horizontal_stack_groups(
        _t51_syn_trs, {"totem": ["SP1", "SN1"]}, [])
    assert set(_t51_syn_groups.keys()) == {"totem__pmos", "totem__nmos"}, \
        f"매칭 파트너 없는 mixed-kind 그룹은 kind별로만 쪼개져야 함: {_t51_syn_groups}"
    assert _t51_syn_groups["totem__pmos"] == ["SP1"] and _t51_syn_groups["totem__nmos"] == ["SN1"], \
        f"쪼개진 서브그룹 멤버 불일치: {_t51_syn_groups}"
    print("    PASS: totem(SP1=pmos/SN1=nmos, 매칭쌍 없음) -- totem__pmos=[SP1]/"
          "totem__nmos=[SN1]로 정확히 분할됨(재병합 시도는 없음, 매칭쌍이 없으므로 정상)")

    print()
    print("=== Test 52: propose_vertical_stack_id_gap_fill() -- audit_vertical_stack_id_")
    print("  vs_kcl()의 '한쪽만 선언됨(gap)' boundary_findings를 KCL 직렬 파트너의 값으로")
    print("  자동 채우기 제안(2026-08-13 세션31, two_stage_ota.topology.json의 M1/M2/M6")
    print("  gap을 손으로 추론했던 걸 재사용 가능한 함수로 코드화 -- 사용자 요청) ===")
    print("  [합성 fixture -- internal_series gap은 채우고 declared_matching_pair gap은")
    print("  안 채우는지(둘의 의미가 다름 -- 후자는 미러 출력이 다른 branch에 있는 게")
    print("  원래 정상이라 audit_vertical_stack_id_vs_kcl() docstring이 명시적으로 구분함)]")
    _t52_syn_trs = [
        Transistor("P1", "pmos", source="vdd", drain="D1"),
        Transistor("N1", "nmos", source="D1", drain="tail"),
        Transistor("MIR_A", "nmos", source="gnd", drain="ref", gate="ref"),
        Transistor("MIR_B", "nmos", source="gnd", drain="out", gate="ref"),
    ]
    _t52_roles = {"P1": {"vertical_stack_id": "colA"}, "MIR_A": {"vertical_stack_id": "biasgen"}}
    _t52_pairs = [("MIR_A", "MIR_B")]
    _t52_result = propose_vertical_stack_id_gap_fill(_t52_syn_trs, _t52_pairs, _t52_roles)
    assert _t52_result["proposals"] == {"N1": "colA"}, \
        f"internal_series gap(P1-N1, D1 공유)만 채워져야 함: {_t52_result['proposals']}"
    assert "MIR_B" not in _t52_result["proposals"], \
        "declared_matching_pair gap(MIR_A-MIR_B)은 채우면 안 됨(다른 branch가 정상)"
    assert _t52_result["conflicts"] == {}
    print(f"    PASS: internal_series gap(N1)만 partner(P1)의 vsid='colA'로 채워짐, "
          f"declared_matching_pair gap(MIR_B)은 그대로 미선언 유지 -- 실제 제안: "
          f"{_t52_result['proposals']}")

    print()
    print("  [합성 fixture -- 같은 소자가 서로 다른 edge에서 서로 다른 vsid를 물려받게")
    print("  되면(충돌) proposals가 아니라 conflicts로 분리되는지]")
    _t52c_trs = [
        Transistor("A", "nmos", source="gnd", drain="x"),
        Transistor("B", "nmos", source="x", drain="y"),
        Transistor("C", "nmos", source="y", drain="vdd"),
    ]
    _t52c_roles = {"A": {"vertical_stack_id": "left"}, "C": {"vertical_stack_id": "right"}}
    _t52c_result = propose_vertical_stack_id_gap_fill(_t52c_trs, [], _t52c_roles)
    assert _t52c_result["proposals"] == {}, \
        f"B가 A('left')/C('right') 양쪽에서 서로 다른 값을 물려받아 충돌해야 함: {_t52c_result}"
    assert _t52c_result["conflicts"] == {"B": ["left", "right"]}, \
        f"충돌 후보 집합 불일치: {_t52c_result['conflicts']}"
    print(f"    PASS: B가 A/C 양쪽에서 다른 vsid를 물려받아 충돌 -- proposals에 안 들어가고 "
          f"conflicts={_t52c_result['conflicts']}로 분리됨(자동 확정 안 함, 사람 검토 대상)")

    print()
    print("  [실제 회로 -- two_stage_ota.topology.json 원본(device_roles에 M1/M2/M6")
    print("  미선언), propose_vertical_stack_id_gap_fill()을 직접 호출하면 손으로")
    print("  추론했던 것과 정확히 같은 제안이 나오는지 -- load_topology()를 거치지")
    print("  않고 원본 JSON을 직접 읽어 함수 자체의 회귀만 검증]")
    import json as _t52r_json
    with open(_t49_os.path.join(_t49_lib, "two_stage_ota.topology.json"), encoding="utf-8") as _t52r_f:
        _t52r_raw = _t52r_json.load(_t52r_f)
    _t52r_trs = [Transistor(**d) for d in _t52r_raw["netlist"]]
    _t52r_roles = {k: v for k, v in (_t52r_raw.get("device_roles") or {}).items()
                    if not k.startswith("_")}
    _t52r_pairs = [tuple(p["names"]) for p in _t52r_raw["symmetry"]["matching_pairs"]
                    if p["current_forced"]]
    # 2026-08-14 -- "M1" not in _t52r_roles였던 원래 검사는 propose_device_roles_gap_fill()을
    # 이 파일에 실제 적용한 뒤로 더 이상 유효한 전제가 아니다(M1이 이제 gm_id_role/L_role/
    # headroom_role은 갖지만 vertical_stack_id는 여전히 없음 -- 그게 이 함수가 실제로
    # 검사하는 필드다). 정확한 전제로 좁힌다.
    assert _t52r_roles.get("M1", {}).get("vertical_stack_id") is None, \
        "원본 topology.json에 M1의 vertical_stack_id가 이미 선언돼 있음(fixture 전제 깨짐)"
    _t52r_result = propose_vertical_stack_id_gap_fill(_t52r_trs, _t52r_pairs, _t52r_roles)
    # 2026-08-24(세션42) -- 세션41이 "stage1"을 "stage1_ref"(M3)/"stage1_out"(M4)로
    # 분리했다(각각 독립된 vdd->gnd branch, `.ai/context.md` 세션41 §3 참고 -- M5(tail)를
    # 공유하는 두 branch를 하나의 vertical_stack_id로 묶은 게 애초에 잘못이었다는 사용자
    # 정정). M1/M2는 이 함수가 M3/M4의 새 vsid를 그대로 물려받는 것으로 갱신돼야 한다
    # (기대값을 옛 "stage1" 단일값에서 분리된 값으로 정정 -- 로직 회귀 아니라 golden
    # value가 stale해진 것, 실제 제안은 새 설계와 정확히 일치함).
    assert _t52r_result["proposals"] == {"M1": "stage1_ref", "M2": "stage1_out", "M6": "stage2"}, \
        f"two_stage_ota의 알려진 gap 제안과 불일치(회귀): {_t52r_result['proposals']}"
    assert _t52r_result["conflicts"] == {}
    print(f"    PASS: two_stage_ota 원본 -- M1이 stage1_ref(M3와 D3 직렬), M2가 stage1_out"
          f"(M4와 O1 직렬), M6이 stage2(M7과 OUT 직렬)로 정확히 제안됨 -- {_t52r_result['proposals']}")

    print()
    print("  [load_topology() 배선 -- 위 제안이 실제로 harness 최상위 진입점에서")
    print("  자동 반영되는지(2026-08-13 세션31, 사용자 지시로 load_topology()에 배선)]")
    _t52w_trs, _t52w_meta = load_topology(_t49_os.path.join(_t49_lib, "two_stage_ota.topology.json"))
    # 2026-08-24(세션42) -- 바로 위 golden value 정정과 같은 이유(stage1 -> stage1_ref/
    # stage1_out 분리, 세션41)로 이 기대값도 stale해졌다 -- 함께 정정.
    assert _t52w_meta["_vertical_stack_id_autofilled"] == {"M1": "stage1_ref", "M2": "stage1_out", "M6": "stage2"}, \
        f"load_topology()의 자동 반영 기록과 불일치(회귀): {_t52w_meta['_vertical_stack_id_autofilled']}"
    assert _t52w_meta["_vertical_stack_id_conflicts"] is None
    for _t52w_name, _t52w_vsid in (("M1", "stage1_ref"), ("M2", "stage1_out"), ("M6", "stage2")):
        assert _t52w_meta["device_roles"][_t52w_name]["vertical_stack_id"] == _t52w_vsid, \
            f"{_t52w_name}의 device_roles에 자동 채움이 실제로 반영 안 됨(회귀)"
    print(f"    PASS: load_topology()가 반환하는 meta['device_roles']에 M1/M2/M6의 "
          f"vertical_stack_id가 이미 채워져 있음(_vertical_stack_id_autofilled="
          f"{_t52w_meta['_vertical_stack_id_autofilled']}) -- resolve_stack_layout()이 "
          f"더 이상 이 gap으로 크래시하지 않음")
    _t52w_pairs_meta = _t52w_meta["symmetry"]["matching_pairs"]
    _t52w_forced = [tuple(p["names"]) for p in _t52w_pairs_meta if p["current_forced"]]
    _t52w_droles = {k: v for k, v in (_t52w_meta.get("device_roles") or {}).items()
                     if not k.startswith("_")}
    _t52w_audit = audit_vertical_stack_id_vs_kcl(_t52w_trs, _t52w_forced, _t52w_droles)
    _t52w_gaps = [f for f in _t52w_audit["boundary_findings"] if f["note"] is not None]
    assert _t52w_gaps == [], \
        f"resolve_stack_layout()이 크래시 근거로 삼는 gap이 여전히 남아있음(배선 실패): {_t52w_gaps}"
    print("    PASS: audit_vertical_stack_id_vs_kcl()이 gap 0건 -- resolve_stack_layout()이 "
          "이 이유로는 더 이상 크래시하지 않음(sizing_recipe.py는 별개 모듈이라 여기서 직접 "
          "안 부름, 순환 import 방지)")

    print()
    print("  === Test 52 전체 PASS ===")

    print()
    print("=== Test 53: propose_device_roles_gap_fill() -- netlist(+load_topology())만으로")
    print("  symmetry.matching_pairs/device_roles 재구성 -- 51소자 실회로 회귀(2026-08-14")
    print("  신설, 사용자 요청 -- 'netlist 정보만 가지고 이 필드들을 구성해봐') ===")
    _t53_trs, _t53_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t53_result = propose_device_roles_gap_fill(_t53_trs, {}, [])
    _t53_declared_pairs = _t53_meta["symmetry"]["matching_pairs"]
    _t53_declared_keys = set()
    for _t53_p in _t53_declared_pairs:
        for _t53_a, _t53_b in itertools.combinations(_t53_p["names"], 2):
            _t53_declared_keys.add(frozenset((_t53_a, _t53_b)))
    _t53_proposed_keys = {frozenset(p["names"]) for p in _t53_result["matching_pairs_proposals"]}
    assert len(_t53_proposed_keys) == 18, \
        f"제안 개수 회귀(branch-composite 9 + structural_symmetry 9): {len(_t53_proposed_keys)}"
    assert _t53_proposed_keys <= _t53_declared_keys, \
        f"declared에 없는 오탐 발생(회귀): {sorted(sorted(k) for k in _t53_proposed_keys - _t53_declared_keys)}"
    for _t53_pair in (("M1a", "M1b"), ("M4a", "M4b"), ("M37a", "M37b"),  # branch-composite differential
                        ("M8", "M17"), ("M13", "M22"),                    # branch-composite mirror
                        ("M11a", "M20a"), ("M15", "M25"), ("M36a", "M36b")):  # structural_symmetry
        assert frozenset(_t53_pair) in _t53_proposed_keys, f"{_t53_pair}가 제안에서 빠짐(회귀)"
    print(f"    PASS: 51소자 실회로에서 {len(_t53_proposed_keys)}개 매칭쌍 제안, 전부 declared "
          f"21그룹의 부분집합(오탐 0건) -- branch-composite(differential/mirror) + "
          f"structural_symmetry(전역 좌우대칭) 두 소스를 합친 결과, 어느 쪽도 손으로 넣은 "
          f"inputs= 없이 순수 부트스트랩만으로 나옴")

    for _t53_name, _t53_expected in (
            ("M8", {"gm_id_role": "matching", "L_role": "mirror", "headroom_role": "mirror"}),
            ("M1a", {"gm_id_role": "matching", "L_role": "mirror"}),
            ("M5", {"gm_id_role": "matching", "L_role": "bias_replica", "headroom_role": "tail"})):
        _t53_actual = _t53_result["device_roles_proposals"].get(_t53_name)
        for _t53_field, _t53_val in _t53_expected.items():
            assert _t53_actual is not None and _t53_actual.get(_t53_field) == _t53_val, \
                f"{_t53_name}.{_t53_field} 제안 회귀: {_t53_actual}"
    print(f"    PASS: device_roles_proposals -- M8/M1a/M5의 gm_id_role/L_role/headroom_role "
          f"제안이 declared 값과 정확히 일치(51개 중 다수가 일치하는 세션 검증 재확인, "
          f"전수는 아님 -- gm_id_role 33/37, L_role 36/37, headroom_role 34/37, 다음 세션 diff 필요)")
    assert len(_t53_result["review_needed"]) >= 1, "undisposed_candidates review가 하나도 없음(회귀)"
    print(f"    PASS: review_needed에 undisposed_candidates 보고됨(층위1/2가 찾았지만 이 함수가 "
          f"확정 못 한 candidate -- 7-way Vbias1 문서화 그룹처럼 current_forced 세분화가 "
          f"sizing_roles/theta 정보 없이는 원천적으로 불가능한 경우가 여기 담김)")

    print()
    print("  [compensation_stage_devices를 넘겨도 M1a/M4a/M15/M25 등 8개 소자에 gm_id_role이")
    print("  그대로 제안되는지(2026-08-14 사용자 지시로 방향 전환 -- 처음엔 위험을 피하려고")
    print("  이 8개를 건너뛰게 만들었으나, '가드를 만들어야지 왜 제외해'라는 지적으로 근본원인")
    print("  (sizing_recipe.py의 누락된 gm_id_role 가드)을 직접 고치는 쪽으로 정정. 이제 이 함수는")
    print("  다시 compensation 소속과 무관하게 제안하고, review_needed에 참고 정보만 남긴다]")
    _t53_stage_devices = _t53_meta["compensation"]["stage_devices"]
    _t53_flat_stage = [n for grp in _t53_stage_devices for n in grp]
    assert "M1a" in _t53_flat_stage, "fixture 전제 확인(compensation.stage_devices 구조 변경됨?)"
    _t53_result_comp = propose_device_roles_gap_fill(
        _t53_trs, {}, [], compensation_stage_devices=_t53_flat_stage)
    for _t53_comp_name in _t53_flat_stage:
        assert "gm_id_role" in _t53_result_comp["device_roles_proposals"].get(_t53_comp_name, {}), \
            f"{_t53_comp_name}(compensation.stage_devices 소속)에 gm_id_role이 다시 제안 안 됨(회귀): " \
            f"{_t53_result_comp['device_roles_proposals'].get(_t53_comp_name)}"
    assert any(r.get("device") in _t53_flat_stage and "compensation.stage_devices" in r.get("note", "")
                for r in _t53_result_comp["review_needed"]), \
        "compensation 소속 소자의 참고 안내가 review_needed에 안 남음(회귀)"
    print(f"    PASS: compensation_stage_devices={sorted(_t53_flat_stage)} 전부에 gm_id_role이 "
          f"정상 제안되고, review_needed엔 '가드로 무시되니 안전' 참고 정보만 남음")

    print()
    print("  [실제로 M1(compensation.stage_devices 소속)에 gm_id_role을 채운 topology.json으로")
    print("  optimize_full_circuit_budget()을 돌려도 sizing 결과가 안 채운 원본과 완전히 같은지")
    print("  -- _AUTHORITATIVE_GM_ID_SOURCES 가드가 실제로 동작하는지, workspaces/run_harness.py의")
    print("  실제 검증된 spec(_spec_two_stage_ota())을 그대로 재사용해 회귀 검증]")
    _t53g_workspaces = _t49_os.path.normpath(_t49_os.path.join(_t49_lib, "..", "..", "..", "..", "workspaces"))
    _t53g_harness_path = _t49_os.path.join(_t53g_workspaces, "run_harness.py")
    if not _t49_os.path.exists(_t53g_harness_path):
        print(f"    SKIP: {_t53g_harness_path}를 못 찾아 실제 사이징 회귀는 건너뜀")
    else:
        import importlib.util as _t53g_ilu
        _t53g_spec_mod = _t53g_ilu.spec_from_file_location("_t53g_run_harness", _t53g_harness_path)
        _t53g_harness = _t53g_ilu.module_from_spec(_t53g_spec_mod)
        _t53g_spec_mod.loader.exec_module(_t53g_harness)
        from sizing_recipe import optimize_full_circuit_budget

        _t53g_two_stage_path = _t49_os.path.join(_t49_lib, "two_stage_ota.topology.json")
        with open(_t53g_two_stage_path, encoding="utf-8") as _t53g_f:
            _t53g_raw = json.load(_t53g_f)
        _t53g_spec = _t53g_harness._spec_two_stage_ota()
        # 2026-08-24(세션42) -- 세션41이 two_stage_ota.topology.json을 stage1_ref/
        # stage1_out으로 분리하며 발견한, 아직 미해결인 DC/AC 아키텍처 갭(`.ai/context.md`
        # 세션41 §3 참고 -- compensation이 정하는 M1/M2/M6과 헤드룸이 정하는 M3/M4/M5/M7이
        # 이 회로의 실제 spec(GBW=7MHz 등, run_harness.py의 검증된 spec)에서 KVL로 안
        # 맞는다, 여기 vdd=1.8V 기준 diff=+0.80V)로 `before`/`after` 둘 다 항상 같은
        # ValueError로 실패한다 -- 이 테스트 본연의 목적(_AUTHORITATIVE_GM_ID_SOURCES 가드
        # 검증)은 DC/AC 갭이 풀려야 재개 가능하다(별도 이월 과제). 여기서는 둘 다 **정확히
        # 같은 이유로** 실패하는지만 확인해 이 known-limitation이 새 회귀로 바뀌지 않았음을
        # 남긴다.
        try:
            _t53g_before = optimize_full_circuit_budget(
                _t53g_two_stage_path, dict(_t53g_spec), grid_points_per_theta=_t53g_harness.SPECS["two_stage_ota"]["grid_points_per_theta"])
        except ValueError as _t53g_e:
            if not ("stage1_out" in str(_t53g_e) and "KVL" in str(_t53g_e)):
                raise
            _t53g_before = None
            print(f"    참고(정직한 한계, DC/AC 아키텍처 미분리 -- 세션41이 이미 발견해 별도 "
                  f"과제로 이월): {str(_t53g_e)[:120]}...")

        import tempfile as _t53g_tempfile
        with _t53g_tempfile.TemporaryDirectory() as _t53g_tmpdir:
            _t53g_mut_path = _t49_os.path.join(_t53g_tmpdir, "two_stage_ota.mutated.topology.json")
            _t53g_mut = dict(_t53g_raw)
            _t53g_mut["device_roles"] = dict(_t53g_raw["device_roles"])
            # 2026-08-14 -- M1은 원본에 device_roles 자체가 없다(compensation.stage_devices
            # 소속이라 사람 저자가 의도적으로 비워둔 자리, 이 Test 53 앞부분에서 이미 확인됨) --
            # 그 빈 자리에 gm_id_role만 새로 채워 넣는 게 정확히 이 회귀가 검증하려는 시나리오다.
            _t53g_mut["device_roles"]["M1"] = {"gm_id_role": "matching"}
            with open(_t53g_mut_path, "w", encoding="utf-8") as _t53g_f:
                json.dump(_t53g_mut, _t53g_f)
            if _t53g_before is None:
                try:
                    optimize_full_circuit_budget(
                        _t53g_mut_path, dict(_t53g_spec), grid_points_per_theta=_t53g_harness.SPECS["two_stage_ota"]["grid_points_per_theta"])
                    raise AssertionError("before는 known-limitation ValueError였는데 after(M1 gm_id_role 채움)는 "
                                          "성공함 -- 가드/KVL 상호작용이 바뀐 것일 수 있음, 확인 필요")
                except ValueError as _t53g_e2:
                    assert "stage1_out" in str(_t53g_e2) and "KVL" in str(_t53g_e2), \
                        f"after가 다른 이유로 실패함(회귀 의심): {_t53g_e2}"
                    print("    PASS(known-limitation 일관성): M1에 gm_id_role을 채워도 before와 "
                          "정확히 같은 이유로 실패 -- _AUTHORITATIVE_GM_ID_SOURCES 가드 자체의 회귀는 아님"
                          "(가드의 최종 sizing-불변 검증은 DC/AC 갭 해소 후 재개할 것)")
            else:
                _t53g_after = optimize_full_circuit_budget(
                    _t53g_mut_path, dict(_t53g_spec), grid_points_per_theta=_t53g_harness.SPECS["two_stage_ota"]["grid_points_per_theta"])
                assert _t53g_before["sizing"]["M1"] == _t53g_after["sizing"]["M1"], \
                    f"M1에 gm_id_role='matching'을 채웠는데 sizing 결과가 바뀜(가드 실패, 진짜 회귀): " \
                    f"{_t53g_before['sizing']['M1']} vs {_t53g_after['sizing']['M1']}"
                assert _t53g_before["theta_star"] == _t53g_after["theta_star"], \
                    "gm_id_role 추가가 theta_star까지 바꿈(가드가 전혀 안 먹힘)"
                print("    PASS: two_stage_ota의 M1(compensation.stage_devices 소속)에 gm_id_role="
                      "'matching'을 실제로 채워도 optimize_full_circuit_budget() 최종 sizing.M1/"
                      "theta_star가 안 채운 원본과 완전히 동일함(_AUTHORITATIVE_GM_ID_SOURCES 가드 "
                      "실측 확인, run_harness.py의 실제 검증된 spec 그대로 재사용)")

    print()
    print("  === Test 53 전체 PASS ===")

    print()
    print("=== Test 54: propose_device_roles_gap_fill() -- 층위1 폴백(비대칭/폴딩 구조라")
    print("  branch-composite/structural_symmetry가 전부 0건인 회로) 안전망 검증 --")
    print("  folded_cascode 실회로 회귀 ===")
    _t54_trs, _t54_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t54_result = propose_device_roles_gap_fill(_t54_trs, {}, [])
    _t54_proposed_keys = {frozenset(p["names"]) for p in _t54_result["matching_pairs_proposals"]}
    for _t54_pair in (("M1", "M2"), ("M9", "M10"), ("M7", "M8")):
        assert frozenset(_t54_pair) in _t54_proposed_keys, \
            f"층위1 폴백이 {_t54_pair}를 못 찾음(회귀) -- diff_pair 또는 diode-connected 미러여야 함"
    assert frozenset(("M3", "M4")) not in _t54_proposed_keys, \
        "M3/M4는 3-way 후보({M3,M4,MP})라 이 함수가 확정 안 하고 review로 넘겨야 하는데 제안됨(회귀)"
    print(f"    PASS: composite/structural_symmetry가 이 회로에서 0건인데도(폴딩 구조라 branch "
          f"전체가 안 대칭) 층위1 폴백이 diff_pair(M1/M2)와 diode-connected 미러(M9/M10,M7/M8)를 "
          f"정확히 재현 -- proposed={sorted(sorted(k) for k in _t54_proposed_keys)}")
    print("    (참고: M11/MN도 같은 패턴(MN이 diode, M11이 소비자, 둘 다 headroom_role="
          "mirror)이라 제안됨 -- 이 파일엔 declared로 없지만, folded_cascode.topology.json은 "
          "이 4개 라이브러리 회로 중 유일하게 symmetry.dispositions 배열 자체가 없어서 "
          "check_symmetry_dispositions()로 한 번도 완결성 검증을 안 받은 파일이다. 오탐인지 "
          "원래 파일의 누락인지는 이 함수가 판단할 수 없다 -- review_needed로 남을 뿐, 이 "
          "함수 자신의 결함으로 취급하지 않는다.)")
    _t54_undisposed_tags = {u[0:3] for r in _t54_result["review_needed"]
                              for u in r.get("undisposed_candidates", [])}
    assert ("current_mirror", "pmos", "vb1") in _t54_undisposed_tags, \
        "3-way {M3,M4,MP} 후보가 review_needed에 안 남음(회귀)"
    print("    PASS: {M3,M4,MP} 3-way 후보와 (다이오드 없는) M5/M6은 review_needed의 "
          "undisposed_candidates에만 남고 matching_pairs_proposals엔 안 실림")

    print()
    print("  === Test 54 전체 PASS ===")

    print()
    print("=== Test 55: apply_device_roles_gap_fill() -- 실제 파일 읽기/병합/쓰기 왕복 +")
    print("  멱등성(같은 결과를 두 번 적용해도 중복 안 생김) ===")
    import tempfile as _t55_tempfile, shutil as _t55_shutil
    with _t55_tempfile.TemporaryDirectory() as _t55_tmpdir:
        _t55_path = _t49_os.path.join(_t55_tmpdir, "folded_cascode.topology.json")
        _t55_shutil.copy(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"), _t55_path)

        _t55_trs, _t55_meta = load_topology(_t55_path)
        _t55_before_pairs = len(_t55_meta["symmetry"]["matching_pairs"])
        _t55_before_pair_keys = {frozenset(p["names"]) for p in _t55_meta["symmetry"]["matching_pairs"]}
        # ⚠️ 2026-08-14 -- folded_cascode.topology.json 원본이 이제(사용자 승인으로 실제
        # 적용됨) M1/M2/M9/M10/M7/M8/M11/MN 8쌍 중 일부를 이미 declared로 갖고 있을 수 있다
        # -- 이 테스트는 "몇 쌍이 새로 채워지는가"를 하드코딩하지 않고, propose()가 이번에
        # 실제로 낸 제안 집합에서 **현재 파일이 이미 아는 것**을 뺀 나머지만 기대값으로 쓴다
        # (파일이 나중에 더 채워져도 이 테스트가 stale해지지 않도록).
        _t55_result_empty = propose_device_roles_gap_fill(_t55_trs, {}, [])
        _t55_expected_new = sorted(
            (sorted(frozenset(p["names"])) for p in _t55_result_empty["matching_pairs_proposals"]
             if frozenset(p["names"]) not in _t55_before_pair_keys))
        _t55_apply1 = apply_device_roles_gap_fill(_t55_path, _t55_result_empty)
        assert sorted(_t55_apply1["applied_matching_pairs"]) == _t55_expected_new, \
            f"파일에 실제로 반영된 쌍이 기대와 다름(이미 declared인 쌍은 걸러지고 새 쌍만 " \
            f"남아야 함): applied={_t55_apply1['applied_matching_pairs']} expected={_t55_expected_new}"

        with open(_t55_path, encoding="utf-8") as _t55_f:
            _t55_written = json.load(_t55_f)
        assert len(_t55_written["symmetry"]["matching_pairs"]) == _t55_before_pairs + len(_t55_expected_new), \
            f"파일에 새 쌍 {len(_t55_expected_new)}개가 실제로 추가되지 않음(쓰기 실패)"
        assert _t55_written["device_roles"] is not None and "M9" in _t55_written["device_roles"], \
            "device_roles가 파일에 실제로 안 써짐"
        assert _t55_written["device_roles"]["M9"]["vs"] == 0.0, \
            "vs 기본값(템플릿 관례) 미적용"
        print(f"    PASS: 파일에 실제로 matching_pairs {_t55_before_pairs}->"
              f"{len(_t55_written['symmetry']['matching_pairs'])}(신규 {_t55_expected_new}), "
              f"device_roles {len(_t55_written['device_roles'])}개 소자로 반영됨(디스크에 "
              f"다시 읽어 확인)")

        _t55_trs2, _t55_meta2 = load_topology(_t55_path)
        _t55_result2 = propose_device_roles_gap_fill(
            _t55_trs2, _t55_meta2["device_roles"] or {}, _t55_meta2["symmetry"]["matching_pairs"])
        _t55_apply2 = apply_device_roles_gap_fill(_t55_path, _t55_result2)
        assert _t55_apply2["applied_matching_pairs"] == [], \
            f"멱등성 위반 -- 이미 반영된 쌍을 다시 적용하려 함: {_t55_apply2['applied_matching_pairs']}"
        print("    PASS: 같은 파일에 다시 적용해도 새로 추가되는 쌍/필드가 0개(멱등성 확인)")

    print()
    print("  === Test 55 전체 PASS ===")

    print()
    print("=== Test 56: propose_device_roles_gap_fill()/apply_device_roles_gap_fill() --")
    print("  이미 선언된 값과 제안이 충돌하면 조용히 덮어쓰지 않고 review_needed로만")
    print("  보고하는지(프로젝트 전역 원칙) 합성 fixture로 검증 ===")
    _t56_trs = [
        Transistor("MA", "pmos", source="tail", drain="outA", gate="vin_p"),
        Transistor("MB", "pmos", source="tail", drain="outB", gate="vin_n"),
        Transistor("MT", "pmos", source="vdd", drain="tail", gate="biasp"),
        # 2026-08-14 -- outA/outB가 gnd까지 안 이어지면(dangling) find_differential_pair_
        # candidates()(branch가 terminates_at="gnd"이어야 함)가 후보를 못 찾아 MA/MB가
        # confirmed 안 되고, 그러면 애초에 "gm_id_role='matching' 제안 vs 기존 'balanced'
        # 선언 충돌"이라는 이 테스트의 전제 자체가 성립 안 한다(gm_id_role이 아예 제안 안
        # 됨) -- 실제 회로처럼 완결된 branch를 만들기 위해 NMOS 부하를 추가.
        Transistor("MLA", "nmos", source="gnd", drain="outA", gate="biasn"),
        Transistor("MLB", "nmos", source="gnd", drain="outB", gate="biasn"),
    ]
    _t56_conflicting_roles = {"MA": {"gm_id_role": "balanced"}}  # 실제 제안은 "matching"이어야 함
    _t56_result = propose_device_roles_gap_fill(_t56_trs, _t56_conflicting_roles, [])
    # 2026-08-20(세션40) 정정 -- 예전엔 필드 하나(gm_id_role)만 충돌해도 그 소자의 proposal
    # 전체를 통째로 버렸다(atomic). vds_match_vgs_of 5번째 소스 구현 중 이게 실제 사고를
    # 냈음을 발견(nmcnr_amplifier의 M109 -- gm_id_role만 충돌하는데 완전히 무관한 새
    # vds_match_vgs_of 제안까지 같이 버려짐)해서, **충돌한 필드만** 제외하고 나머지 필드는
    # 그대로 제안하도록 고쳤다 -- MA는 gm_id_role(충돌)은 빠지고 L_role/headroom_role(무관,
    # 충돌 없음)은 그대로 제안돼야 한다.
    assert "MA" in _t56_result["device_roles_proposals"], \
        "MA의 무관한 필드(L_role/headroom_role)까지 통째로 안 걸러졌어야 하는데 아예 안 실림(회귀)"
    assert "gm_id_role" not in _t56_result["device_roles_proposals"]["MA"], \
        f"MA의 충돌 필드(gm_id_role)가 그대로 제안에 남음(원칙 위반): {_t56_result['device_roles_proposals']['MA']}"
    assert set(_t56_result["device_roles_proposals"]["MA"]) == {"L_role", "headroom_role"}, \
        f"MA의 무관한 필드 제안이 예상과 다름: {_t56_result['device_roles_proposals']['MA']}"
    assert any(r.get("device") == "MA" and "field_conflicts" in r for r in _t56_result["review_needed"]), \
        f"MA의 충돌이 review_needed에 안 남음(회귀): {_t56_result['review_needed']}"
    assert "MB" in _t56_result["device_roles_proposals"], \
        "충돌 없는 MB까지 같이 걸러짐(과잉 차단, 회귀)"
    print(f"    PASS: MA(기존 선언 gm_id_role=balanced, 제안=matching -- 충돌)는 그 필드만 "
          f"device_roles_proposals에서 빠지고(L_role/headroom_role은 정상 제안) "
          f"review_needed로 보고됨, 충돌 없는 MB는 완전히 정상 제안됨")

    with _t55_tempfile.TemporaryDirectory() as _t56_tmpdir:
        _t56_path = _t49_os.path.join(_t56_tmpdir, "conflict_fixture.topology.json")
        with open(_t56_path, "w", encoding="utf-8") as _t56_f:
            json.dump({
                "schema_version": "2.0", "topology_name": "conflict_fixture", "source": "self-test",
                "compensation": None, "_compensation_status": "not_applicable",
                "netlist": [_dc_asdict(t) for t in _t56_trs],
                "symmetry": {"matching_pairs": []},
                "device_roles": _t56_conflicting_roles,
            }, _t56_f)
        _t56_applied = apply_device_roles_gap_fill(_t56_path, _t56_result)
        with open(_t56_path, encoding="utf-8") as _t56_f:
            _t56_written = json.load(_t56_f)
        assert _t56_written["device_roles"]["MA"]["gm_id_role"] == "balanced", \
            "apply_device_roles_gap_fill()이 이미 선언된 MA.gm_id_role을 덮어씀(원칙 위반)"
        print("    PASS: apply_device_roles_gap_fill()도 파일에 이미 있던 MA.gm_id_role=balanced를 "
              "그대로 유지(제안값 matching으로 덮어쓰지 않음)")

    print()
    print("  === Test 56 전체 PASS ===")

    print()
    print("=== Test 57: find_authoritative_sizing_devices()/find_unreviewed_device_roles()/")
    print("  require_device_roles_reviewed() -- optimize_full_circuit_budget() 실행 전 review")
    print("  게이트(2026-08-14 사용자 지시 -- '구조적으로 명확한 기능과 필요한 기능을")
    print("  구분해서... review 안 된 부분은 error로 띄우고... review 받았다는 표시를")
    print("  해서 optimize함수가 실행되도록'). 실측 사고 재발 방지: current_reuse_")
    print("  telescopic_ota의 L_cascode(metric_stage_budget) 대상 M2a/M2b/M3a/M3b에")
    print("  자동 제안된 L_role이 실제로 적용됐다가 그 theta 탐색을 무력화해 gain_db가")
    print("  76.48->74.8로 떨어지는 회귀를 이 세션이 직접 재현/원인규명했다 ===")
    _t57_lib_path = _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json")
    with open(_t57_lib_path, encoding="utf-8") as _t57_f:
        _t57_raw = json.load(_t57_f)
    _t57_trs, _t57_meta = load_topology(_t57_lib_path)
    _t57_authoritative = find_authoritative_sizing_devices(_t57_meta)
    for _t57_name in ("M1a", "M4a", "M15", "M25"):  # compensation.stage_devices
        assert _t57_name in _t57_authoritative, f"{_t57_name}(compensation)이 authoritative에 안 잡힘"
    for _t57_name in ("M2a", "M2b", "M3a", "M3b"):  # L_cascode(metric_stage_budget) 대상
        assert _t57_name in _t57_authoritative, \
            f"{_t57_name}(metric_stage_budget 대상)이 authoritative에 안 잡힘(회귀 -- 실제 사고 재발 위험)"
    assert "M37a" in _t57_authoritative, "M37a(N_cmfb_bw, B타입 대상)가 authoritative에 안 잡힘"
    assert "M8" not in _t57_authoritative, "M8(일반 소자)이 잘못 authoritative로 잡힘(과잉 허용)"
    print(f"    PASS: compensation({sorted({'M1a','M4a','M15','M25'})})/metric_stage_budget"
          f"({sorted({'M2a','M2b','M3a','M3b'})})/B타입(M37a) 전부 authoritative로 잡히고, "
          f"일반 소자(M8)는 안 잡힘")

    _t57_unreviewed_real = find_unreviewed_device_roles(_t57_meta)
    assert _t57_unreviewed_real == {}, \
        f"실제 라이브러리 파일(이미 review 완료된 상태)인데 unreviewed가 남음(회귀): {_t57_unreviewed_real}"
    require_device_roles_reviewed(_t57_lib_path, _t57_meta)  # 예외 안 나야 정상
    print("    PASS: 실제 current_reuse_telescopic_ota.topology.json(이미 review 완료)은 "
          "find_unreviewed_device_roles()=={}이고 require_device_roles_reviewed()도 "
          "조용히 통과함")

    print()
    print("  [합성 fixture -- 일반 소자(authoritative 아님)의 gm_id_role/L_role이 파일에")
    print("  없으면(=아직 review 안 됨) require_device_roles_reviewed()가 명확한 ValueError를")
    print("  내고, apply_device_roles_gap_fill()로 review를 완료하면 그 다음부터 통과하는지]")
    _t57_mut = json.loads(json.dumps(_t57_raw))  # deep copy
    _t57_mut["device_roles"]["M8"] = {"headroom_role": "mirror", "vertical_stack_id": "biasgen_vom_a",
                                        "vs": 0.0}  # gm_id_role/L_role 일부러 뺌(review 전 상태 재현)
    with _t55_tempfile.TemporaryDirectory() as _t57_tmpdir:
        _t57_mut_path = _t49_os.path.join(_t57_tmpdir, "crt_unreviewed.topology.json")
        with open(_t57_mut_path, "w", encoding="utf-8") as _t57_f:
            json.dump(_t57_mut, _t57_f)
        _t57_mut_trs, _t57_mut_meta = load_topology(_t57_mut_path)
        _t57_unreviewed = find_unreviewed_device_roles(_t57_mut_meta)
        assert "M8" in _t57_unreviewed, \
            f"M8의 gm_id_role/L_role을 일부러 뺐는데 unreviewed로 안 잡힘(회귀): {_t57_unreviewed}"
        assert set(_t57_unreviewed["M8"]) == {"gm_id_role", "L_role"}, \
            f"M8의 unreviewed 필드가 예상과 다름: {_t57_unreviewed['M8']}"
        try:
            require_device_roles_reviewed(_t57_mut_path, _t57_mut_meta)
            raise AssertionError("unreviewed device_roles가 있는데 ValueError가 안 남(회귀)")
        except ValueError as _t57_e:
            assert "M8" in str(_t57_e), f"에러 메시지에 M8이 없음: {_t57_e}"
            print(f"    PASS: M8의 gm_id_role/L_role이 review 안 된 상태 -- "
                  f"require_device_roles_reviewed()가 ValueError로 명확히 막음")

        # review 완료(apply_device_roles_gap_fill()로 파일에 실제로 씀) 이후 통과하는지
        _t57_propose = propose_device_roles_gap_fill(
            _t57_mut_trs, _t57_mut_meta.get("device_roles") or {},
            _t57_mut_meta["symmetry"]["matching_pairs"])
        apply_device_roles_gap_fill(_t57_mut_path, _t57_propose)
        _t57_trs2, _t57_meta2 = load_topology(_t57_mut_path)
        require_device_roles_reviewed(_t57_mut_path, _t57_meta2)  # 이제 예외 안 나야 정상
        print("    PASS: apply_device_roles_gap_fill()로 M8의 gm_id_role/L_role을 파일에 "
              "실제로 쓴 뒤로는(review 완료 표시) require_device_roles_reviewed()가 통과함")

    print()
    print("  === Test 57 전체 PASS ===")

    print()
    print("=== Test 58: find_unreviewed_matching_pairs() -- matching_pairs도 review 게이트")
    print("  대상(2026-08-14, 사용자 재지적 -- '대칭적인 branch이면 branch 전류가 같아야")
    print("  하는것 아니야?' 계기로 두 가지를 재확인: (1) mirror/structural_symmetry 출처의")
    print("  current_forced 기본값을 False->True로 정정(4회로 declared 전수 재조사, 2-소자")
    print("  쌍은 예외 없이 True), (2) sizing_recipe.py의 matching_pairs L 전파가 current_")
    print("  forced 값과 무관하게 모든 선언된 쌍에 작동함을 재확인 -- 'current_forced=False는")
    print("  sizing에 안 쓰인다'는 이전 주장이 틀렸었다). 그래서 differential(offset)만")
    print("  load_topology()가 메모리에도 자동 병합하고, mirror류(ratio)는 review 전까지")
    print("  병합도 안 하고 review 목록에만 남긴다 -- folded_cascode의 실제 gap(M11/MN,")
    print("  diode-connected MN + 소비자 M11이지만 한때 이 파일이 한 번도 check_symmetry_")
    print("  dispositions() 검증을 받은 적 없어 사람이 확정하지 않았던 사례 -- 2026-08-14")
    print("  세션34에 사용자 승인으로 실제 declared에 반영됐으므로, 이 테스트는 이제 임시")
    print("  사본에서 그 declared 쌍을 다시 지워 '아직 review 안 된 상태'를 재현한다(실제")
    print("  라이브러리 파일이 나중에 더 채워져도 이 테스트가 stale해지지 않도록)) ===")
    import tempfile as _t58_tempfile, shutil as _t58_shutil
    _t58_srcdir = _t58_tempfile.mkdtemp()
    _t58_path = _t49_os.path.join(_t58_srcdir, "folded_cascode.topology.json")
    _t58_shutil.copy(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"), _t58_path)
    with open(_t58_path, "r", encoding="utf-8") as _t58_f:
        _t58_raw = json.load(_t58_f)
    _t58_raw["symmetry"]["matching_pairs"] = [
        p for p in _t58_raw["symmetry"]["matching_pairs"] if set(p["names"]) != {"M11", "MN"}]
    if isinstance(_t58_raw.get("device_roles"), dict):
        for _t58_n in ("M11", "MN"):
            _t58_raw["device_roles"].pop(_t58_n, None)
    with open(_t58_path, "w", encoding="utf-8") as _t58_f:
        json.dump(_t58_raw, _t58_f)
    _t58_trs, _t58_meta = load_topology(_t58_path)
    _t58_declared_keys = {frozenset(p["names"]) for p in _t58_meta["symmetry"]["matching_pairs"]}
    assert frozenset(("M11", "MN")) not in _t58_declared_keys, \
        "M11/MN이 declared에 있음(임시 사본에서 방금 지웠는데도 남아있으면 이 테스트 setup 자체가 잘못됨)"
    _t58_needs_review = find_unreviewed_matching_pairs(_t58_meta)
    assert any(set(p["names"]) == {"M11", "MN"} for p in _t58_needs_review), \
        f"M11/MN이 find_unreviewed_matching_pairs()에 안 잡힘(회귀): {_t58_needs_review}"
    assert all(p.get("matching_sensitivity") != "offset" for p in _t58_needs_review), \
        "offset(differential) 제안이 review 목록에 잘못 섞임(differential은 review 불필요해야 함)"
    print(f"    PASS: folded_cascode의 M11/MN(ratio, 아직 declared 아님)이 find_unreviewed_"
          f"matching_pairs()에 정확히 잡힘: {[p['names'] for p in _t58_needs_review]}")

    try:
        require_device_roles_reviewed(_t58_path, _t58_meta)
        raise AssertionError("M11/MN이 unreviewed인데 require_device_roles_reviewed()가 통과함(회귀)")
    except ValueError as _t58_e:
        assert "M11" in str(_t58_e) and "MN" in str(_t58_e), f"에러 메시지에 M11/MN이 없음: {_t58_e}"
        print("    PASS: require_device_roles_reviewed()가 M11/MN 때문에 ValueError로 명확히 막음")

    print()
    print("  [differential(offset) 출처는 review 없이도 메모리에 자동 병합되는지 -- M1/M2")
    print("  (folded_cascode, 이미 declared)로 회귀 없음만 재확인(새 제안은 이미 declared라")
    print("  없어야 정상, 순수 하위호환 확인)]")
    assert find_unreviewed_matching_pairs(_t58_meta) == [
        p for p in find_unreviewed_matching_pairs(_t58_meta) if set(p["names"]) != {"M1", "M2"}], \
        "이미 declared된 M1/M2(differential)가 review 목록에 잘못 나타남"
    print("    PASS: 이미 declared된 differential 쌍(M1/M2)은 review 목록에 안 나타남")

    print()
    print("  === Test 58 전체 PASS ===")

    print()
    print("=== Test 60: audit_theta_root_direction() -- sizing_roles.theta의 'A'/'A_signed'")
    print("  feed가 캐스코드 체인에서 lo(전류생성원)인 root를 그 위에 얹힌 up(캐스코드)에서")
    print("  유도하는(방향이 거꾸로인) 경우를 idioms.m_cascode()/propagate_reference_role_")
    print("  through_cascode()로 잡아내는지(2026-08-18, 사용자 지적 3단계 -- 'analog-grammar를")
    print("  통해서 각 소자의 관계를 알고 있는 것 아닌가' -> 'm_cascode()가 이미 하지 않나' ->")
    print("  실측 결과 m_cascode()가 PMOS/NMOS 경계(drain-drain)를 못 잡는 gap을 발견해 그")
    print("  자체를 확장. 그 확장 검증 중 m_diffpair()가 CTRL_SRC(FEEDBACK게이트 CMFB 차동쌍)를")
    print("  놓치는 별개 gap도 발견해 같이 확장) ===")

    _t60_trs, _t60_meta = load_topology(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"))
    _t60_clean = audit_theta_root_direction(_t60_trs, _t60_meta["sizing_roles"], inputs=("Vin_p", "Vin_n"))
    assert _t60_clean == [], f"실제(정정된) nmcnr_amplifier가 깨끗해야 하는데: {_t60_clean}"
    print(f"    PASS: 실제 nmcnr_amplifier.topology.json(M108/M109가 lo, M106/M107이 그 위에 "
          f"얹힌 up인 현재 설계)는 findings 0건 -- M106<->M108은 PMOS/NMOS 경계(drain-drain) "
          f"캐스코드라 m_cascode()의 cross-kind 확장이 실제로 이 검증에 쓰임")

    print("  [세션 초반 실제로 저질렀던 버그(M106을 root로 두고 M108을 그 반대로 참조) 재현 -- "
          "잡히는지]")
    import copy as _t60_copy
    _t60_buggy = _t60_copy.deepcopy(_t60_meta["sizing_roles"])
    _t60_buggy["theta"] = [t for t in _t60_buggy["theta"] if t["name"] not in ("kcl_M104", "r_series_M106")]
    _t60_buggy["theta"].append({
        "name": "kcl_M106_BUGGY", "bounds": [1.0, 1.0],
        "feeds": {"type": "A_signed", "root": "M106",
                  "terms": [{"device": "M104", "sign": 1}, {"device": "M102", "sign": -1}]}})
    _t60_buggy["theta"].append({
        "name": "r_series_M108_BUGGY", "bounds": [1.0, 1.0],
        "feeds": {"type": "A", "root": ["M108"], "reference": ["M106"]}})
    _t60_buggy_findings = audit_theta_root_direction(_t60_trs, _t60_buggy, inputs=("Vin_p", "Vin_n"))
    assert len(_t60_buggy_findings) == 1, f"버그 재현판이 정확히 1건 잡혀야 하는데: {_t60_buggy_findings}"
    assert (_t60_buggy_findings[0]["root"] == "M108"
            and _t60_buggy_findings[0]["reference"] == "M106"), \
        f"잡힌 방향이 예상과 다름: {_t60_buggy_findings}"
    print(f"    PASS: root='M108'(lo)가 reference='M106'(그 위에 얹힌 up)에서 유도되는 거꾸로 "
          f"방향을 정확히 1건 잡아냄")

    print("  [current_reuse_telescopic_ota의 kcl_tail_M38(root=M38 tail, reference=M37a/M37b "
          "CMFB 차동쌍)이 오탐 없는지 -- M37a/M37b는 게이트(Voc/Voc_des)가 FEEDBACK으로 "
          "분류돼 role=CONTROLLED_CURRENT_SOURCE가 되는데, m_diffpair()가 원래 role==AMP만 "
          "인정해 이 CMFB 차동쌍을 못 알아보고 m_cascode()가 'M38 위에 얹힌 캐스코드'로 "
          "오분류하던 걸 실측으로 발견(m_cascode() cross-kind 확장과는 별개 gap) -- "
          "m_diffpair()에 CTRL_SRC도 추가해 정정, feedbacks=('Voc','Voc_des')를 정확히 "
          "선언하면 오탐이 사라지는지 재확인(회귀 감시)]")
    _t60_crt_trs, _t60_crt_meta = load_topology(
        _t49_os.path.join(_t49_lib, "current_reuse_telescopic_ota.topology.json"))
    _t60_crt_findings = audit_theta_root_direction(
        _t60_crt_trs, _t60_crt_meta["sizing_roles"], inputs=("Vip", "Vim"),
        feedbacks=("Voc", "Voc_des"))
    assert _t60_crt_findings == [], \
        f"kcl_tail_M38(CMFB 차동쌍) 오탐이 재발함: {_t60_crt_findings}"
    print("    PASS: feedbacks를 정확히 선언하면 kcl_tail_M38 오탐 없음")

    print("  [나머지 실제 library 회로(folded_cascode/two_stage_ota)도 findings 0건인지 -- "
          "이미 검증된 설계에 오탐이 없어야 함(inputs는 각 회로 실제 net 이름 그대로)]")
    _t60_fc_trs, _t60_fc_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t60_fc_findings = audit_theta_root_direction(_t60_fc_trs, _t60_fc_meta["sizing_roles"],
                                                    inputs=("vin_p", "vin_n"))
    assert _t60_fc_findings == [], f"folded_cascode에 오탐: {_t60_fc_findings}"
    _t60_tso_trs, _t60_tso_meta = load_topology(_t49_os.path.join(_t49_lib, "two_stage_ota.topology.json"))
    _t60_tso_findings = audit_theta_root_direction(_t60_tso_trs, _t60_tso_meta["sizing_roles"],
                                                     inputs=("vin_p", "vin_n"))
    assert _t60_tso_findings == [], f"two_stage_ota에 오탐: {_t60_tso_findings}"
    print("    PASS: folded_cascode/two_stage_ota 둘 다 findings 0건")

    print()
    print("  === Test 60 전체 PASS ===")

    print()
    print("=== Test 61: propose_theta_kcl_gap_fill() -- 전류(ID) KCL 구조를 connectivity +")
    print("  analog-grammar idiom만으로 제안(2026-08-18, 사용자 승인 후 신설 -- 'propose_")
    print("  theta_kcl_gap_fill 만들자'). 규칙 1(diffpair 50/50)/2(캐스코드 추종)/2.5(declared")
    print("  mirror)/2.7(gate mirror)/3(KCL 합)/4(자유 root 승격, diode 우선)를 실측으로")
    print("  검증한다 ===")

    _t61_trs, _t61_meta = load_topology(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"))
    _t61_result = propose_theta_kcl_gap_fill(
        _t61_trs, _t61_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_meta.get("ideal_sources"), inputs=("Vin_p", "Vin_n"))
    assert _t61_result["unresolved_devices"] == [], \
        f"nmcnr_amplifier는 전부 resolve돼야 하는데: {_t61_result['unresolved_devices']}"
    _t61_by_name = {t["name"]: t for t in _t61_result["theta_proposals"]}
    assert set(_t61_by_name["r_split_M102_M103"]["feeds"]["root"]) == {"M102", "M103"}, \
        "diffpair 50/50 규칙(M102/M103)이 안 잡힘"
    assert _t61_by_name["r_series_M106"]["feeds"]["reference"] == ["M108"], \
        "M106이 M108(lo)을 따라가야 하는데(캐스코드 추종): " + str(_t61_by_name["r_series_M106"])
    _t61_free_names = {n for t in _t61_result["theta_proposals"] if t["feeds"]["type"] == "const"
                        for n in t["feeds"]["root"]}
    assert _t61_free_names == {"M101", "M108", "M109", "M203", "M204", "M301"}, \
        f"nmcnr_amplifier의 자유 root 집합이 예상과 다름: {_t61_free_names}"
    print(f"    PASS: nmcnr_amplifier 전부 resolve(자유 root={sorted(_t61_free_names)}), "
          f"diffpair 50/50·캐스코드 추종 관계 정확 -- M203/M204/M301은 이 함수 범위 밖인 "
          f"compensation.stage_devices(M201/M301)와 얽혀 있어 이 함수 혼자서는 온칩 "
          f"레퍼런스를 못 찾음(정직한 한계, 사람이 compensation 쪽과 함께 재검토할 것)")

    print("  [compensation_stage_devices=[M102,M103,M201,M301]을 주면 위 한계가 풀리는지 -- "
          "2026-08-19 세션37 신설]")
    _t61c_flat = [n for grp in _t61_meta["compensation"]["stage_devices"] for n in grp]
    _t61c_result = propose_theta_kcl_gap_fill(
        _t61_trs, _t61_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_meta.get("ideal_sources"), compensation_stage_devices=_t61c_flat,
        inputs=("Vin_p", "Vin_n"))
    assert _t61c_result["unresolved_devices"] == [], \
        f"compensation 제외해도 전부 resolve돼야 하는데: {_t61c_result['unresolved_devices']}"
    _t61c_names = {t["name"] for t in _t61c_result["theta_proposals"]}
    _t61c_roots = {n for t in _t61c_result["theta_proposals"]
                    for n in (t["feeds"]["root"] if isinstance(t["feeds"]["root"], list)
                              else [t["feeds"]["root"]])}
    assert not (_t61c_roots & set(_t61c_flat)), \
        f"compensation 소속 소자가 theta root로 잘못 제안됨: {_t61c_roots & set(_t61c_flat)}"
    assert "kcl_M203" in _t61c_names, \
        "M201(compensation)이 resolved로 처리되면 M203은 독립 자유쌍이 아니라 KCL로 유도돼야 함"
    _t61c_by_name = {t["name"]: t for t in _t61c_result["theta_proposals"]}
    assert _t61c_by_name["kcl_M203"]["feeds"]["terms"] == [{"device": "M201", "sign": 1}], \
        "kcl_M203이 M201에서 유도돼야 함: " + str(_t61c_by_name["kcl_M203"])
    assert "r_mirror_M204_M203" in _t61c_names, \
        "M204는 M203의 declared mirror(규칙 2.5)로 재분류돼야 함(더 이상 독립 자유쌍 아님)"
    assert "kcl_M302" in _t61c_names, \
        "M301(compensation)이 resolved로 처리되면 M302는 그 KCL 유도값이어야 함"
    print(f"    PASS: M201/M301이 theta 구조에서 빠지고, M203({_t61c_by_name['kcl_M203']['feeds']}) "
          f"이 M201에서 KCL로, M204가 M203의 declared mirror로 재분류됨(더 이상 독립 자유쌍 아님)")

    print("  [folded_cascode -- 규칙 2.7(gate mirror, MP->M3/M4)가 실제로 필요한지 재확인 "
          "-- 처음엔 이 규칙이 없어서 MP가 회로 나머지와 완전히 단절된 고아 자유변수로 "
          "남았었다(실측 발견)]")
    _t61_fc_trs, _t61_fc_meta = load_topology(_t49_os.path.join(_t49_lib, "folded_cascode.topology.json"))
    _t61_fc_result = propose_theta_kcl_gap_fill(
        _t61_fc_trs, _t61_fc_meta["symmetry"]["matching_pairs"],
        ideal_sources=_t61_fc_meta.get("ideal_sources"), inputs=("vin_p", "vin_n"))
    assert _t61_fc_result["unresolved_devices"] == [], \
        f"folded_cascode는 전부 resolve돼야 하는데: {_t61_fc_result['unresolved_devices']}"
    _t61_fc_by_name = {t["name"]: t for t in _t61_fc_result["theta_proposals"]}
    assert "r_mirror_M3_MP" in _t61_fc_by_name and "r_mirror_M4_MP" in _t61_fc_by_name, \
        "MP->M3/M4 게이트 미러(규칙 2.7)가 안 잡힘 -- MP가 다시 고아 변수로 남을 위험"
    print("    PASS: MP->M3/M4 게이트 미러(규칙 2.7)가 정확히 잡혀서 MP가 고립되지 않음")

    print("  [서로 다른 자유 root 그룹(MP측/M9-M10측)이 같은 KCL 노드로 수렴하면 placeholder "
          "값 충돌(0/음수)을 review_needed로 잡아내는지 -- 실측으로 처음 발견한 현상(구조 "
          "결함이 아니라 '이 자유 root들을 서로 조율해야 한다'는 신호), 조용히 넘기지 "
          "않는지 회귀 감시]")
    _t61_nonpositive_flags = [r for r in _t61_fc_result["review_needed"]
                                if "전류가 0 또는 음수" in r["reason"]]
    assert len(_t61_nonpositive_flags) == 1, \
        f"MP측/M9-M10측 수렴 경고가 정확히 1건이어야 하는데: {_t61_nonpositive_flags}"
    assert set(_t61_nonpositive_flags[0]["devices"]) == {"M1", "M2", "M11", "MN"}, \
        f"경고 대상 소자가 예상과 다름: {_t61_nonpositive_flags[0]}"
    print(f"    PASS: {_t61_nonpositive_flags[0]['devices']}에 placeholder 값 충돌 경고 "
          f"정확히 1건")

    print()
    print("  === Test 61 전체 PASS ===")

    print()
    print("=== Test 62: apply_theta_kcl_gap_fill() -- propose_theta_kcl_gap_fill() 결과를")
    print("  실제 topology.json에 반영(2026-08-19 세션37 신설, 사용자 지시 'propose_theta")
    print("  적용하자'). 이미 declared된 소자를 다루는 제안은 충돌로 스킵되고(M101/M108/M109")
    print("  등 이미 baseline 실측까지 끝난 stage1은 그대로), stage2/3(M202/M203/M204/M302,")
    print("  세션37에 이 함수로 처음 채워진 소자)만 실제로 추가되는지 검증한다. 실제 라이브러리")
    print("  파일은 이미 세션37에 이 4개가 적용된 상태이므로, 임시 사본에서 그 4개를 제거해")
    print("  '적용 전' 상태를 재구성한 뒤 테스트한다(파일 현재 상태와 무관하게 항상 재현 가능")
    print("  하도록) ===")
    import tempfile as _t62_tempfile, shutil as _t62_shutil

    _T62_NEW_NAMES = {"kcl_M203", "r_mirror_M204_M203", "kcl_M202", "kcl_M302"}
    with _t62_tempfile.TemporaryDirectory() as _t62_tmpdir:
        _t62_path = _t49_os.path.join(_t62_tmpdir, "nmcnr_amplifier.topology.json")
        _t62_shutil.copy(_t49_os.path.join(_t49_lib, "nmcnr_amplifier.topology.json"), _t62_path)
        with open(_t62_path, encoding="utf-8") as _f:
            _t62_data = json.load(_f)
        # '적용 전' 상태 재구성(이 함수로 세션37에 이미 추가된 4개를 제거) -- stage1 7개만 남김
        _t62_data["sizing_roles"]["theta"] = [
            t for t in _t62_data["sizing_roles"]["theta"] if t["name"] not in _T62_NEW_NAMES]
        with open(_t62_path, "w", encoding="utf-8") as _f:
            json.dump(_t62_data, _f, indent=2, ensure_ascii=False)
        _t62_before_names = {t["name"] for t in _t62_data["sizing_roles"]["theta"]}
        assert _t62_before_names == {"Ibg_tail", "r_split_M102_M103", "r_fold_M108_M109",
                                       "kcl_M104", "kcl_M105", "r_series_M106", "r_series_M107"}
        _t62_before_by_name = {t["name"]: t for t in _t62_data["sizing_roles"]["theta"]}
        _t62_applied = apply_theta_kcl_gap_fill(_t62_path, _t61c_result)
        assert set(_t62_applied["applied"]) == _T62_NEW_NAMES, \
            f"실제로 추가돼야 할 신규 theta 집합이 예상과 다름: {_t62_applied['applied']}"
        _t62_skipped_names = {s["name"] for s in _t62_applied["skipped_conflict"]}
        assert _t62_skipped_names == {"kcl_M101", "r_free_M108_M109", "r_series_M106",
                                        "r_series_M107", "kcl_M104", "kcl_M105"}, \
            f"이미 declared된 stage1 소자를 다루는 제안이 스킵되지 않음: {_t62_skipped_names}"
        with open(_t62_path, encoding="utf-8") as _f:
            _t62_after = json.load(_f)
        _t62_after_names = {t["name"] for t in _t62_after["sizing_roles"]["theta"]}
        assert _t62_after_names == _t62_before_names | _T62_NEW_NAMES, \
            "적용 후 theta 목록이 (기존 7개 + 신규 4개)와 일치하지 않음"
        # 기존 7개 theta는 값 자체가 한 글자도 안 바뀌었는지 확인(스킵=완전 불변 보장)
        for _name in _t62_before_names:
            _after_entry = next(t for t in _t62_after["sizing_roles"]["theta"] if t["name"] == _name)
            assert _after_entry == _t62_before_by_name[_name], \
                f"기존 theta {_name!r}가 스킵됐는데도 값이 바뀜(apply_ 계약 위반)"
    print(f"    PASS: 신규 적용={sorted(_t62_applied['applied'])}, 충돌로 스킵된 기존 "
          f"소자={sorted(_t62_skipped_names)} -- 기존 7개 theta는 바이트 단위로 불변, "
          f"파일 밖(임시 디렉터리)에서만 검증해 실제 라이브러리 파일은 안 건드림")

    print()
    print("  === Test 62 전체 PASS ===")
