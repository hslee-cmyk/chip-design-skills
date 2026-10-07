"""MOD7 stage 를 넘는 hub 병합 후보 `find_hub_merge_candidates` -- 옛 stick_diagram.py 본문 복사(L10, 사용자 결정 2026-10-07 Q8 (viii)).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from collections import defaultdict


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
