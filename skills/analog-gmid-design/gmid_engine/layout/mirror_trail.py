"""MOD7 축대칭 Euler trail `mirror_symmetric_trail`(+`check_walk_sequence`) -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace as _dc_replace

from .transistor import Transistor
from .euler_graph import build_graph
from .euler_condition import check_euler_condition
from .euler_trail import hierholzer


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
       하나라도 끝까지 이어지면 그 경로(`node_path`)를 채택한다.

    검사하지 않는 것: source/drain 연결만 보므로 PMOS/NMOS가 섞인 시퀀스도 연결만 맞으면
    통과시킨다 -- kind 동질성 검사는 `build_graph()`의 몫이라 이 함수는 하지 않는다.
    영역: 없음(배치)
    """
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
