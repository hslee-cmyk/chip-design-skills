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
    M6×6)와 정확히 일치한다."""
    mirrored = [pair_map[x] for x in reversed(half)]
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

def find_matching_candidates(transistors: list) -> dict:
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
    """
    by_gate = defaultdict(list)
    by_source = defaultdict(list)
    for t in transistors:
        if t.gate is not None:
            by_gate[(t.kind, t.gate)].append(t)
        by_source[(t.kind, t.source, t.w)].append(t)

    current_mirror = {k: v for k, v in by_gate.items() if len(v) >= 2}
    diff_pair = {}
    for (kind, source, w), group in by_source.items():
        if len(group) != 2:
            continue
        if group[0].gate is not None and group[1].gate is not None and group[0].gate != group[1].gate:
            diff_pair[(kind, source)] = group

    return {"current_mirror": current_mirror, "diff_pair": diff_pair}


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
    검증했다). 이건 `geometry_colocation_union()`의 자동 발견 규칙(레일 공유를 일부러
    제외 — 서로 무관한 기능블럭이 레일 하나로 뭉개지는 false positive 방지, 아래 참고)과는
    **다른 목적의 다른 판단**이니 헷갈리지 말 것 — 여기는 이미 확정된 쌍 하나만 보므로 그런
    과병합 위험이 없다."""
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
    """L2 축B(2026-08-05, 세션10 L1/L2 구현) — `derive_stack_groups()`를 분리한 것 중
    geometry(축B, `sizing_recipe.py`의 `stack_groups_geometry`) 쪽. `kcl_series_union()`과
    똑같은 union-find 골격이지만 **자동 발견 규칙1이 다르다**(세션8 실측 근거):

    1. **같은 극성 + non-rail net + `drain=source`(직렬)만 자동 병합**. `kcl_series_union()`의
       "정확히 2단자" 규칙과 달리 극성/방향을 명시적으로 본다:
       - rail(vdd/gnd/vss)은 제외 — rail 공유는 회로 전체가 결국 거기 닿기 때문에 병합
         근거로 쓰면 서로 무관한 기능블럭이 뭉개진다(실측: `current_reuse_telescopic_ota`
         vdd 16회/gnd 13회 hub가 통째로 한 그룹이 되는 false positive).
       - 같은 극성끼리만 — PMOS/NMOS는 다른 well이라 같은 diffusion 행에 못 들어간다.
       - `drain=source`(직렬/캐스코드)만, `drain=drain`(합류/정션)은 제외 — 정션 노드는
         레이아웃 인접의 근거가 아니다(예: `M2a.drain=Vom1=M18a.drain`은 회로 메커니즘일
         뿐 인접 근거가 아님, `M8.drain=Vg15=M9a.source`는 진짜 stacked series라 병합 타당).
    2. **선언된 `matching_pairs`**: 호출자가 `current_forced=true`로 거른 쌍만 넘긴다는
       계약(L1) — `current_mirror`/`branch_symmetric`(축A=false, 순수 문서용) 선언은
       geometry 강제병합에서 완전히 제외해야 하므로(안 그러면 문서용 hub 그룹이 무관한
       기능블럭을 다시 끌고 들어와 매칭 품질을 악화시킨다, 실측: dx=6.00 vs 3~4) 이 함수는
       받은 쌍을 그대로 병합할 뿐이고 필터링은 호출자(`sizing_recipe.py`) 책임이다.

    반환 형태는 `kcl_series_union()`과 동일."""
    by_drain: dict = defaultdict(list)
    by_source: dict = defaultdict(list)
    kind_of = {t.name: t.kind for t in netlist}
    for t in netlist:
        if t.drain is not None:
            by_drain[t.drain].append(t.name)
        if t.source is not None:
            by_source[t.source].append(t.name)

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

    for net, drain_names in by_drain.items():
        if net in _RAIL_NETS:
            continue
        for src_name in by_source.get(net, []):
            for drain_name in drain_names:
                if drain_name != src_name and kind_of[drain_name] == kind_of[src_name]:
                    union(drain_name, src_name)
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
    소자를 다 쓴 뒤에야 다음 소자로 넘어가는" 최악의 뭉침은 기본값에서부터 막는다."""
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

def find_min_crossover_layout(transistors: list) -> dict:
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

    **구현**: 홀수차수 노드 2m개를 전부 짝지어(순서대로 2개씩) m개의 **가상 edge**를
    그래프에 추가하면 모든 노드가 짝수차수가 돼(항상 성립 — 짝짓기 방법과 무관하게
    이 성질은 불변) 전체가 오일러 회로가 된다. `hierholzer()`로 이 회로 전체를 계산한
    뒤, 가상 edge가 나온 지점마다 실제로 끊어서(가상 edge 자체는 버림) m개의 진짜
    trail로 분해한다 — 실측 확인(2026-07-28): ABC(3소자 1개씩, 4개 홀수차수 노드,
    m=2) -> `[C,A]`+`[B]` 2개 trail, crossover=1. ABCD(4소자 1개씩, 4개 홀수, m=2)
    -> crossover=1. 6소자 1개씩(6개 홀수, m=3) -> crossover=2. **어떤 짝짓기 방법을
    쓰든 trail 개수(=m)는 항상 같다**(T-join 정리 — 짝짓기가 다르면 어느 소자가 어느
    trail에 속하는지만 달라지지, 필요한 crossover 개수 자체는 안 바뀐다).

    **입력**: `transistors`(전부 같은 `source`=hub 공유, `drain`은 서로 달라야 함).
    **반환**: `{"segments": [{"transistor_sequence":[...], "node_sequence":[...]}, ...],
    "crossover_count": int, "odd_nodes": [...]}` — `crossover_count=0`이면 `segments`가
    1개뿐이고 그게 곧 `build_stick_diagram()`이 주는 것과 같은 단일 연속 diffusion
    결과다. `crossover_count`가 0보다 크면 `segments`를 순서대로 이어붙이되 각 경계마다
    실제로 crossover routing(추가 metal+via)이 필요하다는 뜻이다."""
    if not transistors:
        raise ValueError("최소 1개 이상의 소자가 필요하다")
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
        }

    odd = verdict.odd_nodes  # 짝수 개(그래프 이론상 항상 짝수)
    pairs = [(odd[i], odd[i + 1]) for i in range(0, len(odd), 2)]
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

    # 가상 edge 중 첫 번째가 나온 바로 다음 지점부터 시작하도록 순환을 재정렬 —
    # 이러면 "마지막 가상 edge 이후 ~ 배열 끝"과 "배열 시작 ~ 첫 가상 edge 이전"처럼
    # 순환 경계에 걸쳐 갈라지는 실제 trail이 생기지 않는다(양쪽 다 실제로는 하나로
    # 이어진 trail인데 인덱스만 둘로 쪼개져 보이는 것을 방지).
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
    return {"segments": segments, "crossover_count": len(segments) - 1, "odd_nodes": odd}


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

@dataclass
class BoxLayoutCandidate:
    finger_w: float                  # 이 stack에 쓸 unit cell 폭(um) — 다른 stack과 다를 수 있다
    n_fingers_per_device: dict       # {device_name: n_fingers}
    total_row_fingers: int           # 이 stack 전체 행의 finger 총합 = 물리적 행 길이(box 판정 기준)


def search_stack_finger_w(devices: dict, target_row_fingers: int,
                           min_finger_w: float = 1.0, max_finger_w: float = 40.0,
                           tol_fingers: int = 3, max_n: int = 200) -> list:
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
    """
    names = list(devices.keys())
    widths = list(devices.values())
    if not widths:
        return []
    base_w = widths[0]
    results = []
    for n1 in range(1, max_n + 1):
        fw = base_w / n1
        if not (min_finger_w <= fw <= max_finger_w):
            continue
        per_device = {}
        total = 0
        ok = True
        for name, w in zip(names, widths):
            n = w / fw
            if abs(n - round(n)) > 1e-6 or round(n) < 1:
                ok = False
                break
            per_device[name] = round(n)
            total += round(n)
        if ok and abs(total - target_row_fingers) <= tol_fingers:
            results.append(BoxLayoutCandidate(finger_w=fw, n_fingers_per_device=per_device,
                                               total_row_fingers=total))
    results.sort(key=lambda c: (abs(c.total_row_fingers - target_row_fingers), c.finger_w))
    return results


def assign_finger_geometry(sizing_results: dict, stack_groups: dict, area_priors: dict | None = None,
                            min_finger_w: float = 1.0, max_finger_w: float = 40.0) -> dict:
    """배치 7-6(2026-07-31) — `size_transistor()`가 만든 raw `W`(사이징 결과)와
    `derive_stack_groups()`가 만든 stack 후보를 이어 `run_topology_pipeline()`이 요구하는
    `sizing_overrides`(`{name: {"n_fingers","finger_w","w","stack_id"}}`)를 자동 구성한다
    — bootstrapping 문제(`search_stack_finger_w()`/`search_unit_cell_sizing()` 둘 다 "맞출
    참조값"이 이미 있어야 동작하는데, 맨 처음 stack엔 맞출 대상이 없음)를 seed 선택으로
    해결한다.

    `sizing_results`: `{device_name: SizingResult 또는 {"W": float, ...}}` — `size_transistor()`
    류의 결과, `.W` 속성 또는 `["W"]` 키 둘 다 받는다.

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
                                           "w": n * best_unit.unit_w, "stack_id": sid}
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
                               "w": n * best.finger_w, "stack_id": sid}
        assigned_targets.append(best.total_row_fingers)
        assigned_finger_widths.append(best.finger_w)

    return overrides


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
                            min_fingers: int = 1, max_n: int = 200) -> list:
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
    소자에게는 정확히 맞는" 값들이 전체적으로도 좋은 근사일 가능성이 높기 때문이다."""
    seeds = set()
    for w in devices.values():
        for k in range(1, max_n + 1):
            fw = w / k
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


@dataclass
class BoxShapeVerdict:
    ok: bool
    row_widths: dict          # {row_label: finger_count}
    max_ratio: float          # max(width)/min(width)
    message: str


def check_box_shape(row_widths: dict, max_ratio: float = 1.5) -> BoxShapeVerdict:
    """§8 cell shape 게이트 — **SPICE 검증으로 넘어가기 전에 반드시 통과해야 하는 체크포인트**.

    이 세션에서 반복된 실수(Example 1: nstack 3 vs pstack 32, 10.7:1 'ㄱ'자 셀 / Example 2:
    diffpair 9×2행 vs tailstack 24 vs loadstack 38)는 전부 "sizing → SPICE 검증"으로 바로
    넘어가고 box-shape를 나중에야(혹은 사용자가 지적해서야) 확인했기 때문에 생겼다 —
    §8/§2.7에 탐색 도구(`search_stack_finger_w`, `common_centroid_layout` 등)는 있었지만, 그
    결과가 실제로 "박스에 가까운가"를 **명시적으로 PASS/FAIL 판정하는 게이트가 없어서**
    사람이 눈대중으로 넘어가기 쉬웠다. `check_euler_condition()`/`check_finger_width_compatibility()`
    처럼 이 함수도 명시적 gate로 만들어, §6 워크플로우에서 **SPICE 재검증 이전에 반드시
    호출**하도록 강제한다.

    row_widths: {row_label: finger_count} — 실제 물리적 행이 될 모든 stack/행의 finger
    개수. common-centroid로 나눈 stack은 **행별로 따로** 넣을 것(예: diffpair를 2행으로
    나눴다면 "diffpair_row0", "diffpair_row1"을 각각 넣는다 — 나누기 전 합계를 넣으면
    실제 물리적 형태를 반영하지 못한다).

    max_ratio: 허용 가능한 최대/최소 행 폭 비율(기본 1.5). 이보다 크면 실무에서 셀이 너무
    길쭉해진다(Example 1의 최초 10.7:1은 이 게이트를 통과 못 했을 결과다).

    ⚠️ FAIL이면 §5 sizing↔layout 피드백 루프로 돌아가 §8(`search_stack_finger_w`)이나
    §2.7(`common_centroid_layout`)로 finger_w·행 구성을
    다시 정해야 한다 — **SPICE 검증은 이 게이트를 통과한 뒤에만 진행할 것.** finger_w를
    나중에 바꾸면 §8.3(폭 의존 전류 오차)에 따라 SPICE도 다시 돌려야 하므로, 순서를 지키는
    쪽이 재작업을 줄인다.
    """
    if not row_widths:
        return BoxShapeVerdict(ok=True, row_widths={}, max_ratio=1.0, message="행이 없음 — 검사 대상 없음")
    widths = list(row_widths.values())
    ratio = max(widths) / min(widths)
    ok = ratio <= max_ratio
    verdict = "PASS" if ok else "FAIL"
    detail = "허용치 이내" if ok else f"허용치({max_ratio}) 초과 — §8/§2.7로 finger_w·행 구성을 다시 정할 것"
    message = f"{verdict}: 행 폭 {dict(row_widths)}, 최대/최소 비율={ratio:.2f} ({detail})"
    return BoxShapeVerdict(ok=ok, row_widths=dict(row_widths), max_ratio=ratio, message=message)


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


def mirror_symmetric_trail(group: list[Transistor], matching_pairs: list) -> dict | None:
    """L3(walk 선택) — 세션11, `matching_pairs`를 아예 모르는 `build_graph()`+`hierholzer()`
    대신, 선언된 매칭쌍을 거울대칭으로 반영한 trail을 **구성**해본다(탐색이 아니라 구성 —
    자기동형사상을 그래프에서 찾는 대신 `matching_pairs`가 이미 알려준 대응에서 역산).

    **원리**(folded_cascode top row, current_reuse_telescopic_ota의 실제 그룹 2개로
    교차검증됨): 각 매칭쌍(A,B)에서 대표 소자 하나만(그룹 내 원본 순서상 먼저 나오는 쪽) 골라
    "절반 그래프"를 구성하고, 그 절반의 오일러 trail을 `build_mirror_symmetric_pattern()`으로
    거울반사하면 전체 trail이 나온다 — 실제로 그래프상 유효한지는 `check_walk_sequence()`로
    직접 검증하므로(구성이 자기동형사상을 잘못 가정했다면 여기서 실패로 걸러진다), 별도로
    노드 레벨 매핑을 미리 검증할 필요가 없다.

    **적용 범위(의도적으로 좁음, 알려진 한계)**:
    - 그룹의 모든 소자가 `matching_pairs`로 커버되거나(1:1, 개수 동일) self-pair(미매칭)여야
      한다 — self-pair는 **짝수 `n_fingers`만 지원**(홀수 self-pair, 예: 실측된
      `current_reuse_telescopic_ota`의 `M5`(1개)처럼 두 홀수차수 고정점을 잇는 "다리"로 쓰는
      패턴은 아직 미구현 — 이 경우도 `None`을 반환해 호출자가 기존 `build_graph()+hierholzer()`
      로 폴백하게 한다).
    - 1:1이 아닌(개수가 다른) 매칭쌍이 섞인 그룹도 `None`(폴백) — `auto_mirror_ratios`가 만드는
      비율 미러 등.
    - 위 조건을 만족해도 절반 그래프 자체가 오일러 불가능하면 `None`(폴백) — 이 경우 그룹 분할
      필요 여부는 이 함수의 책임이 아니다(호출자가 판단).

    반환: 성공하면 `{"node_sequence": [...], "transistor_sequence": [...]}`, 실패하면 `None`."""
    pair_map = {t.name: t.name for t in group}
    group_names = set(pair_map)
    for a, b in matching_pairs:
        if a in group_names and b in group_names:
            pair_map[a] = b
            pair_map[b] = a

    n_fingers_of = {t.name: t.n_fingers for t in group}
    for a, b in pair_map.items():
        if a == b:
            if n_fingers_of[a] % 2 != 0:
                return None
        elif n_fingers_of[a] != n_fingers_of[b]:
            return None

    order = {t.name: i for i, t in enumerate(group)}
    by_name = {t.name: t for t in group}
    seen = set()
    half_transistors = []
    for t in group:
        if t.name in seen:
            continue
        partner = pair_map[t.name]
        seen.add(t.name)
        seen.add(partner)
        if partner == t.name:
            half_transistors.append(_dc_replace(t, n_fingers=t.n_fingers // 2))
        else:
            rep = t if order[t.name] < order[partner] else by_name[partner]
            half_transistors.append(rep)

    half_graph = build_graph(half_transistors)
    verdict = check_euler_condition(half_graph)
    if verdict.kind == "impossible":
        return None
    _, half_seq = hierholzer(half_graph, verdict.start)

    full_seq = build_mirror_symmetric_pattern(half_seq, pair_map)
    wv = check_walk_sequence(full_seq, group)
    if not wv.ok:
        return None
    return {"node_sequence": wv.node_path, "transistor_sequence": full_seq}


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

    def add(self, name, ok, detail=""):
        self.checks.append(AuditCheck(name, ok, detail))
        if not ok:
            self.ok = False


def run_full_circuit_audit(devices: dict, expected_counts: dict, dispositions: dict,
                            box_shape_checks: dict | None = None, max_ratio: float = 1.5,
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
    - `box_shape_checks`: `{block_label: {row_id: n_fingers_total}}` — sub-block별 실제 행 폭.
      common-centroid로 물리 행이 2개로 쪼개진 그룹(§2.7)은 `common_centroid_layout()` 등으로
      이미 계산된 `row_widths`를 그대로 넣을 것 — 이 함수가 그 분할을 자동으로 재계산하지
      않는다(단일 Transistor 리스트로는 "같은 소자가 2개 물리 행에 나눠 들어간다"는 구조를
      표현할 수 없기 때문 — 이건 알려진 한계이지 숨겨진 가정이 아니다).
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
    for block, row_widths in (box_shape_checks or {}).items():
        v = check_box_shape(row_widths, max_ratio=max_ratio)
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
                     max_ratio: float = 1.5, area_budget: str | None = None) -> AuditResult:
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
    row_widths: dict = {}
    sequences: dict = {}
    reps: dict = {}  # name -> 대표 Transistor(gate/source 조회용, 행 무관하게 아무거나 하나)

    for row_name, devices in rows.items():
        row_widths[row_name] = sum(t.n_fingers for t in devices)
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

    bs = check_box_shape(row_widths, max_ratio=max_ratio)
    result.add("2. box-shape", bs.ok, bs.message)

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


def _layout_result_to_rows(layout: dict, templates: dict, base_row_name: str) -> dict:
    """`interdigitate_layout()`/`common_centroid_layout()`의 반환값(`"rows"`: 각 원소가
    `transistor_sequence`를 가진 새 물리 행)을 실제 `{row_name: [Transistor,...]}`로
    변환한다 — 각 이름의 `transistor_sequence` 등장 횟수가 그 행에서의 `n_fingers`다.
    `templates`: `{name: Transistor}` — 원본 소자(kind/source/drain/gate 등 connectivity
    필드를 그대로 복사하고 `n_fingers`/`stack_id`만 새로 채운다)."""
    result = {}
    for i, row in enumerate(layout["rows"]):
        counts = Counter(row["transistor_sequence"])
        new_row_name = f"{base_row_name}_repair{i}"
        result[new_row_name] = [_dc_replace(templates[name], n_fingers=n, stack_id=new_row_name)
                                 for name, n in counts.items()]
    return result


def repair_matching_safety(rows: dict, matching_pairs: list, pair_sensitivity: dict | None = None,
                            max_iter: int = 3) -> tuple:
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

    ⚠️ 정직한 한계(2026-07-31): `interdigitate_layout()`/`common_centroid_layout()`은
    "같은 hub net(source)을 공유하는 소자들"만 입력으로 받는다 — pair의 두 소자가 서로
    다른 hub를 쓰면(공유 노드가 없는 `branch_symmetric` 쌍이 실제로 이런 경우가 있다) 이
    도구들 자체가 적용 불가능해 이 함수는 그 pair를 건드리지 않고 넘어간다(진행이 전혀
    없으면 `max_iter`를 다 채우지 않고 조기 종료) — `run_topology_pipeline()`의 기존
    docstring이 이미 밝힌 한계(사람이 `search_stack_finger_w()`로 직접 조정) 그대로다."""
    pair_sensitivity = pair_sensitivity or {}
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
        for (a, b) in failing:
            devs_by_name, origin_rows = {}, {}
            for rn, devs in current_rows.items():
                for t in devs:
                    if t.name in (a, b):
                        devs_by_name[t.name] = t
                        origin_rows[t.name] = rn
            if a not in devs_by_name or b not in devs_by_name:
                continue
            ta, tb = devs_by_name[a], devs_by_name[b]
            if ta.source != tb.source:
                continue  # 공유 hub 없음 -- 이 도구들 적용 불가(정직한 한계, 위 docstring)
            sens = _sensitivity_of_pair(a, b)
            tool_name = select_layout_tool(sens, shares_diffusion_node(ta, tb))
            tool_fn = interdigitate_layout if tool_name == "interdigitate_layout" else common_centroid_layout
            layout = tool_fn([ta, tb])
            base_row_name = origin_rows[a]
            new_rows = _layout_result_to_rows(layout, {a: ta, b: tb}, base_row_name)
            for rn in set(origin_rows.values()):
                current_rows[rn] = [t for t in current_rows[rn] if t.name not in (a, b)]
                if not current_rows[rn]:
                    del current_rows[rn]
            current_rows.update(new_rows)
            progressed = True
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


def block_from_row_widths(name: str, row_widths: dict) -> FloorplanBlock:
    """stick diagram의 row_widths(§8 box-shape 입력과 동일한 dict)를 하나의 FloorplanBlock으로
    집계한다 — width=그 block 안 최대 행 폭(finger 수), height=행 개수. 이 두 값을 실제 물리
    치수로 착각하지 말 것(§6.7 docstring 참고) — 상대 비율 비교에만 쓴다."""
    return FloorplanBlock(name, width=max(row_widths.values()), height=len(row_widths))


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

    linked = data.get("linked_topology_files") or []
    base_dir = os.path.dirname(os.path.abspath(json_path))
    for rel_path in linked:
        linked_data = _read_one(os.path.join(base_dir, rel_path))
        all_netlist.extend(linked_data["netlist"])
        all_matching_pairs.extend(linked_data["symmetry"]["matching_pairs"])
        all_dispositions.extend(linked_data["symmetry"].get("dispositions", []))
        all_device_roles.update(linked_data.get("device_roles") or {})

    transistors = [Transistor(**d) for d in all_netlist]
    meta = {
        "topology_name": data["topology_name"],
        "schema_version": data["schema_version"],
        "source": data.get("source"),
        "symmetry": {"matching_pairs": all_matching_pairs, "dispositions": all_dispositions},
        "compensation": data.get("compensation"),
        "sizing_roles": data.get("sizing_roles"),  # 배치 7-3d(§7.3.2 D), 2026-07-31 신설
        "device_roles": all_device_roles or None,  # 배치 7-5, 2026-07-31 신설
        "_linked_files_loaded": linked,
    }
    return transistors, meta


def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict,
                           floorplan_hints: dict | None = None,
                           cell_groups: dict | None = None) -> dict:
    """`load_topology()` -> `sizing_overrides`로 소자별 layout 필드(n_fingers/finger_w/w/
    stack_id — **필수**, 사이징+finger 배분이 끝난 뒤에만 이 함수를 의미 있게 호출할 수 있다)
    덮어쓰기 -> `split_into_stacks()`로 스택(=기본 물리 행 후보) 구성 -> §1.6/§1.7이 정한
    순서 그대로: 행별 Euler 유효성 -> `check_box_shape()` -> `audit_row_split()`
    (matching-safety, `symmetry.matching_pairs`의 kind 사용) -> `pack_floorplan_grouped()`
    -> `check_stick_diagram_coverage()`.

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

    rows = split_into_stacks(transistors)  # {stack_id: [Transistor, ...]}
    row_widths = {name: sum(t.n_fingers for t in devs) for name, devs in rows.items()}

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
        box_shape = check_box_shape(row_widths)
        audit_row = audit_row_split(rows, matching_pairs=matching_pairs,
                                     pair_sensitivity=pair_sensitivity)
    else:
        box_shape = {}
        audit_row = {}
        for cell_name, row_names in effective_cell_groups.items():
            cell_rows = {rn: rows[rn] for rn in row_names if rn in rows}
            cell_row_widths = {rn: row_widths[rn] for rn in row_names if rn in row_widths}
            box_shape[cell_name] = check_box_shape(cell_row_widths)
            cell_device_names = {t.name for devs in cell_rows.values() for t in devs}
            cell_pairs = [(a, b) for (a, b) in matching_pairs
                          if a in cell_device_names and b in cell_device_names]
            cell_pair_sensitivity = {k: v for k, v in pair_sensitivity.items()
                                      if set(k) <= cell_device_names}
            audit_row[cell_name] = audit_row_split(cell_rows, matching_pairs=cell_pairs,
                                                    pair_sensitivity=cell_pair_sensitivity)

    spine_groups_names = hints.get("spine_groups") or {name: [name] for name in row_widths}
    blocks_by_name = {name: block_from_row_widths(name, {name: row_widths[name]})
                      for name in row_widths}
    spine_groups = {gname: [blocks_by_name[bname] for bname in members if bname in blocks_by_name]
                    for gname, members in spine_groups_names.items()}
    floorplan = pack_floorplan_grouped(spine_groups, hints.get("mirror_pairs") or [],
                                        net_weights=hints.get("net_weights"))

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


def _box_shape_json(bs):
    """`BoxShapeVerdict` 하나(단일-cell 회로, `run_topology_pipeline()`의 기본 가정) 또는
    `{cell_name: BoxShapeVerdict}`(물리적으로 독립된 cell이 여러 개인 회로 — 각 cell은 자기
    자신의 aspect-ratio 제약만 가지므로 cell을 넘나드는 단일 combined ratio는 의미가 없다)를
    둘 다 받는다. 2026-07-29 확장: `current_reuse_telescopic_ota` 리포트처럼 물리적으로
    독립된 cell 3개(core_signal/bias_tail/stage2_output)를 갖는 회로에서 실측 필요성 확인."""
    if isinstance(bs, dict):
        return {name: _box_shape_json(v) for name, v in bs.items()}
    return {"ok": bs.ok, "row_widths": bs.row_widths, "message": bs.message}


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
    print("=== Test 13: check_box_shape() 게이트 — SPICE 전에 반드시 통과해야 하는 §8 체크포인트 ===")
    print("  Example 1의 실제 최초 실수(nstack=3, pstack=32)를 이 게이트에 넣으면:")
    before1 = check_box_shape({"nstack": 3, "pstack": 32})
    print(f"  {before1.message}")
    print("  §8로 고친 뒤(8:8):")
    after1 = check_box_shape({"nstack": 8, "pstack": 8})
    print(f"  {after1.message}")
    print(f"  -> 게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: "
          f"{'OK' if (not before1.ok and after1.ok) else 'FAIL'}")
    print("  Example 2의 실제 최초 실수(diffpair 2행x9, tailstack 24, loadstack 38)를 넣으면:")
    before2 = check_box_shape({"diffpair_row0": 9, "diffpair_row1": 9, "tailstack": 24, "loadstack": 38})
    print(f"  {before2.message}")
    print("  §8로 고친 뒤(전부 폭 10):")
    after2 = check_box_shape({"diffpair_row0": 10, "diffpair_row1": 10, "tailstack": 10, "loadstack": 10})
    print(f"  {after2.message}")
    print(f"  -> 게이트가 실수는 FAIL로, 수정본은 PASS로 정확히 구분: "
          f"{'OK' if (not before2.ok and after2.ok) else 'FAIL'}")

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
    spine = [
        block_from_row_widths("S1_PMOS", {"row0": 8, "row1": 8}),
        block_from_row_widths("S1_NMOS", {"row0": 8, "row1": 8}),
        block_from_row_widths("S1_TAILP", {"row0": 10}),
        block_from_row_widths("S1_TAILN", {"row0": 7}),
        block_from_row_widths("biasgen_pmos", {"row0": 5}),
        block_from_row_widths("biasgen_nmos", {"row0": 4}),
        block_from_row_widths("cmfb_p1", {"row0": 2}),
        block_from_row_widths("cmfb_p2", {"row0": 1}),
        block_from_row_widths("cmfb_n1", {"top": 2, "bot": 2}),
        block_from_row_widths("cmfb_n2", {"row0": 2}),
    ]
    mirror_pairs = [
        (block_from_row_widths("classab_p1", {"row0": 3}), block_from_row_widths("classabL_p1", {"row0": 3})),
        (block_from_row_widths("classab_p2", {"row0": 2}), block_from_row_widths("classabL_p2", {"row0": 2})),
        (block_from_row_widths("classab_n1_new", {"row0": 2}), block_from_row_widths("classabL_n1_new", {"row0": 2})),
        (block_from_row_widths("classab_n2_new", {"row0": 2}), block_from_row_widths("classabL_n2_new", {"row0": 2})),
        (block_from_row_widths("classab_n_mirror", {"top": 2, "bot": 2}), block_from_row_widths("classabL_n_mirror", {"top": 2, "bot": 2})),
        (block_from_row_widths("S2_M15", {"row0": 1}), block_from_row_widths("S2_M25", {"row0": 1})),
        (block_from_row_widths("S2_M16", {"row0": 1}), block_from_row_widths("S2_M26", {"row0": 1})),
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
    asym_pairs = [(block_from_row_widths("R", {"row0": 5}), block_from_row_widths("L", {"row0": 3}))]
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
    print("=== Test 29: derive_stack_groups()/assign_finger_geometry() (배치 7-6, 2026-07-31) ===")
    print("  folded_cascode.topology.json 전체(13개 소자, 5개 matching_pairs)를 그대로 사용")
    print("  -- 손타이핑 넷리스트 없음(topology.json 단일 소스 원칙).")

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
    for _singleton in ("MP", "M11", "MN"):
        assert frozenset({_singleton}) in _fc_group_sets, \
            f"{_singleton}은 다른 어떤 소자와도 안 묶여야 하는데(rail만 공유, drain=source 체인/matching_pair 없음) 그룹이 다름"
    print(f"    PASS: {len(_fc_groups)}개 그룹 -- PMOS 6개(M1..M6), NMOS 4개(M7..M10, 다이오드 "
          f"레퍼런스 체인), MP/M11/MN(단독) 전부 확인")

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
        "M3": {"W": 30e-6}, "M4": {"W": 30e-6},
        "M9": {"W": 24e-6}, "M10": {"W": 24e-6},
        "M1": {"W": 80e-6}, "M2": {"W": 80e-6},
        "M5": {"W": 30e-6}, "M6": {"W": 30e-6}, "M7": {"W": 40e-6}, "M8": {"W": 40e-6},
        "MP": {"W": 20e-6}, "M11": {"W": 16e-6}, "MN": {"W": 16e-6},
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
    print(f"    PASS: {len(_fc_overrides)}개 소자 전부 n_fingers*finger_w==w로 원래 W 정확히 "
          f"재현, stack_id가 derive_stack_groups() 그룹 키와 일치")
    _row_lengths = {}
    for _name, _ov in _fc_overrides.items():
        _row_lengths.setdefault(_ov["stack_id"], 0)
        _row_lengths[_ov["stack_id"]] += _ov["n_fingers"]
    print(f"    참고: stack별 total_row_fingers={_row_lengths} "
          f"(box-shape 판정은 audit_row_split()/repair_matching_safety()의 몫)")
