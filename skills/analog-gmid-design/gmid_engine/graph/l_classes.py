"""L 동치류 derived 처리와 주인 결정 (설계 40 §3.2 보완 1, 계획 DEC-17·LR1).

진입점: `l_equivalence_classes(s1, model, views) -> tuple[LClass]`.

동치류 = S1 `rel_l_class` 의 각 관계(같은 gate 넷·같은 source 넷·같은 kind 인 MOS 묶음, LR1 증거). S1 쪽 관계는 주인을 정할 수 없어(뷰가 필요) `proposed` 로
남고, 여기서 주인을 정해 `derived` 로 낸다 -- 소비자(θ 스키마)는 이 결과를 읽는다. 멤버는 L 을 공유하고 공통 L 은 모든 선언 제약을 동시에 만족하도록 탐색한다.
**주인 순서**(DEC-17):
1. 동치류에 **tail** 이 있으면 tail. tail = DC 역할이 바이어스 전류원이고 drain 이 둘 이상 소자의 공통 source 넷인 멤버(뷰 무관 정의). 여럿이면 **첫 전달
   뷰의 가장 앞 stage 블록에 tail 역할로 붙은 것**을 우선하고(규칙 `tail_first_gain_stage`), 그래도 같으면 이름 순.
2. tail 이 없으면 같은 묶음의 다른 멤버 전류를 정하는 전류 출처 멤버(diode 기준 멤버, 규칙 `current_source_member`).
3. 그것도 없으면 이름 정렬 첫 멤버(규칙 `name_order`).
멤버 DC 역할이 구조로 못 가르는 그룹(S1 status review_needed)이면 동치류 status 는 review_needed 다.
"""
from gmid_engine.core import sorted_items

from .s1_values import GRAPH_KEY, REL_L_CLASS, ROLE_BIAS, ROLE_DIODE, STATUS_DERIVED, STATUS_REVIEW_NEEDED
from .s1v_values import ROLE_TAIL, VIEW_TRANSFER, LClass

RULE_TAIL = "tail_owner"
RULE_TAIL_STAGE = "tail_first_gain_stage"
RULE_CURRENT_SOURCE = "current_source_member"
RULE_NAME_ORDER = "name_order"


def _tail_stages(views):
    """첫 전달 뷰에서 tail 역할 소자 -> 그 블록의 가장 앞 stage."""
    for view in views:
        if view.kind != VIEW_TRANSFER:
            continue
        stages = {}
        for block in view.blocks:
            for name, role in block.roles:
                if role == ROLE_TAIL:
                    stages[name] = min(block.stage, stages.get(name, block.stage))
        return stages
    return {}


def l_equivalence_classes(s1, model, views):
    stage = _tail_stages(views)
    result = []
    for edge in s1.value("graph", GRAPH_KEY, "rel_" + REL_L_CLASS):
        members = [model.mos_by_name[name] for name in edge.members]
        tails = [m for m in members if m.dc_role == ROLE_BIAS and len(model.by_source.get(m.d, ())) > 1]
        if len(tails) == 1:
            owner, rule = tails[0].name, RULE_TAIL
        elif tails:
            owner = min(tails, key=lambda m: (stage.get(m.name, len(model.mos)), m.name)).name
            rule = RULE_TAIL_STAGE
        else:
            sources = [m for m in members if m.dc_role == ROLE_DIODE]
            owner, rule = (sources[0].name, RULE_CURRENT_SOURCE) if sources else (members[0].name, RULE_NAME_ORDER)
        unresolved = any(m.dc_status == STATUS_REVIEW_NEEDED for m in members)
        result.append(LClass(tuple(sorted(edge.members)), owner, rule, STATUS_REVIEW_NEEDED if unresolved else STATUS_DERIVED))
    return sorted_items(result, key=lambda c: c.members)
