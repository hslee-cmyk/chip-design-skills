"""L 동치류 derived 처리와 주인 결정 (설계 40 §3.2 보완 1, 계획 DEC-17·LR1).

진입점: `l_equivalence_classes(s1, model, views, gain_views=()) -> tuple[LClass]`.

동치류 = S1 `rel_l_class` 의 각 관계(같은 gate 넷·같은 source 넷·같은 kind 인 MOS 묶음, LR1 증거). S1 쪽 관계는 주인을 정할 수 없어(뷰가 필요) `proposed` 로
남고, 여기서 주인을 정해 `derived` 로 낸다 -- 소비자(θ 스키마)는 이 결과를 읽는다. 멤버는 L 을 공유하고 공통 L 은 모든 선언 제약을 동시에 만족하도록 탐색한다.
**주인 순서**(DEC-17):
1. 동치류에 **tail** 이 있으면 tail. tail = DC 역할이 바이어스 전류원이고 drain 이 둘 이상 소자의 공통 source 넷인 멤버(뷰 무관 정의). 여럿이면 **첫 전달
   뷰의 가장 앞 stage 블록에 tail 역할로 붙은 것**을 우선하고(규칙 `tail_first_gain_stage`), 그래도 같으면 이름 순.
2. tail 이 없으면 같은 묶음의 다른 멤버 전류를 정하는 전류 출처 멤버(diode 기준 멤버 -- 복합 diode 기준 포함, 41 §1.12.1, 규칙 `current_source_member`).
3. **`main_path_signal`**(41 §1.12.5): 멤버 중 gain 제약 전달 뷰(`gain_views` 의 첫 전달 뷰, 없으면 첫 전달 뷰)의 **주경로 stage 시작 셀**인 것. feedforward 묶음 멤버는 주경로 모형에서
   빠져 있어 자동으로 뒤로 밀린다(FF 셀은 주경로 전류를 복사하는 쪽이다). 여럿이면 가장 앞 stage 것(같으면 이름).
4. 그것도 없으면 이름 정렬 첫 멤버(규칙 `name_order`) -- 남은 동률만 해당하고 status `review_needed`(`build_s1v` 가 `l_owner_name_order` 기록을 올린다).
   **예외**(master edb5ee0, 41 §1.12.5-4): 동률 후보(동치류 멤버 전체)가 U2 `automorphism_orbits` 의 **한 자기동형 궤도**이면 어느 것을 주인으로 골라도 같은 회로이므로
   이름 순서로 골라도 review 를 올리지 않는다(status derived, 규칙 이름은 `name_order` 그대로). 궤도는 S1 구조만으로 센다(선언 표시 없음 -- 선언이 대칭을 깨는지는 sizing 이 본다).
   정준형은 이 분기가 실제로 나올 때만, 호출당 한 번 계산한다.
멤버 DC 역할이 구조로 못 가르는 그룹(S1 status review_needed)이면 동치류 status 는 review_needed 다.
"""
from gmid_engine.core import sorted_items

from .automorphism_orbits import automorphism_orbits
from .canonical_form import canonical_form
from .s1_values import GRAPH_KEY, REL_L_CLASS, ROLE_BIAS, ROLE_DIODE, STATUS_DERIVED, STATUS_REVIEW_NEEDED
from .s1v_values import ROLE_INPUT, ROLE_TAIL, VIEW_TRANSFER, LClass

RULE_TAIL = "tail_owner"
RULE_TAIL_STAGE = "tail_first_gain_stage"
RULE_CURRENT_SOURCE = "current_source_member"
RULE_MAIN_PATH = "main_path_signal"
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


def _main_path_starts(views, gain_views):
    """gain 제약 전달 뷰(없으면 첫 전달 뷰)의 주경로 stage 시작 셀 -> 그 블록의 stage."""
    transfer = [v for v in views if v.kind == VIEW_TRANSFER]
    chosen = next((v for v in transfer if v.id in gain_views), transfer[0] if transfer else None)
    starts = {}
    for block in () if chosen is None else chosen.blocks:
        for name, role in block.roles:
            if role == ROLE_INPUT:
                starts[name] = min(block.stage, starts.get(name, block.stage))
    return starts


def _one_orbit(orbits, names):
    """`names`(동치류 멤버 소자)가 모두 같은 자기동형 궤도인가. `orbits` = 호출당 한 번 구하는 지연 계산기."""
    table = orbits()
    return len({table[("e", name)] for name in names}) == 1


def l_equivalence_classes(s1, model, views, gain_views=()):
    memo = []

    def orbits():
        if not memo:
            memo.append(automorphism_orbits(canonical_form(s1)))
        return memo[0]

    stage = _tail_stages(views)
    main_starts = _main_path_starts(views, frozenset(gain_views))
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
            mains = [m for m in members if m.name in main_starts]
            if sources:
                owner, rule = sources[0].name, RULE_CURRENT_SOURCE
            elif mains:
                owner, rule = min(mains, key=lambda m: (main_starts[m.name], m.name)).name, RULE_MAIN_PATH
            else:
                owner, rule = members[0].name, RULE_NAME_ORDER
        tie = rule == RULE_NAME_ORDER and not _one_orbit(orbits, edge.members)
        unresolved = tie or any(m.dc_status == STATUS_REVIEW_NEEDED for m in members)
        result.append(LClass(tuple(sorted(edge.members)), owner, rule, STATUS_REVIEW_NEEDED if unresolved else STATUS_DERIVED))
    return sorted_items(result, key=lambda c: c.members)
