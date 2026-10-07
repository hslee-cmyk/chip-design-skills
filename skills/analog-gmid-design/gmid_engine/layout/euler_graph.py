"""MOD7 stack multigraph 구성 `build_graph`(+`StackGraph`) -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .transistor import Transistor


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
