"""루프 역할 -- 루프 뷰 | 중첩 Miller 내부 루프 | 복합 diode 내부 | 바이어스 SCC (설계 41 §1.12.3, 40 §3.2-3 `loop_role`).

진입점: `loop_roles(view_loops, transfer_views, declared_pm_views) -> tuple[LoopRole]`.

* `view_loops` = ((전달 뷰 id, 그 뷰의 `Loop` tuple), ...) -- `classify_loops` 가 단 분류(`Loop.classes`)와 끊는 점(`Loop.cut`)이 이미 들어 있다.
* `transfer_views` = ((전달 뷰 id, 그 뷰의 `CellInfo` tuple), ...) -- 조건 (b) 가 '그 뷰의 순방향 셀'을 읽는다.
* `declared_pm_views` = 전체 안정도 제약 `pm_ss_deg` 가 선언된 전달 뷰 id 집합.

**역할 결정**(루프마다 하나, 같은 id 는 한 번):
* 분류 `bias_scc` / `composite_diode_internal` 인 루프 -> 같은 이름의 역할. id = 사이클 노드 열(이름 정렬 첫 노드에서 시작)의 JSON 배열 텍스트.
* 분류 `loop_view` 이고 끊는 점이 있는 루프 -> 끊는 점마다 후보 루프 뷰 ℓ(id `loop:<끊는 소자>:<끊는 넷>`). ℓ 이 다음 (a)(b)를 모두 만족하면 `compensation_internal`
  (루프 뷰를 만들지 않는다), 아니면 `loop_view`:
  (a) ℓ 의 모든 사이클이 (2) Miller 조건을 만족한다(`Loop.classes` 에 miller),
  (b) 사이클 위 능동 셀(CS·CG·CD·off)이 모두 그 전달 뷰의 순방향 셀이다 -- 순방향 밖 능동 셀(공통 모드 감지·주입 셀)이 낀 루프는 개루프 증폭기 **내부**가 아니다.
  `compensation_internal` 의 `reason` 은 그 전달 뷰에 `pm_ss_deg` 가 선언돼 있으면 `overall_pm_declared`, 아니면 `compensation_internal_needs_overall_pm`
  (호출자가 기존 정지 `undeclared_loop_constraint` 를 유지한다).
(3-b) 판정 자체는 바꾸지 않는다 -- 수동소자 엣지를 뺀 거리로 (3-b) 를 다시 정하는 안(B3)은 9회로 실측에서 다른 회로를 깨 기각했다(41 §1.12.3).
"""
import json

from .s1v_values import (
    CELL_CD,
    CELL_CG,
    CELL_CS,
    CELL_OFF,
    LOOP_BIAS_SCC,
    LOOP_COMPENSATION_INTERNAL,
    LOOP_COMPOSITE_INTERNAL,
    LOOP_MILLER,
    LOOP_VIEW,
    REASON_COMPENSATION_NEEDS_PM,
    LoopRole,
)

REASON_PM_DECLARED = "overall_pm_declared"
_ACTIVE = (CELL_CS, CELL_CG, CELL_CD, CELL_OFF)


def _flat(devices):
    names = []
    for device in devices:
        names.extend(device if isinstance(device, tuple) else (device,))
    return names


def _inside_forward(loop, cells):
    """조건 (b): 사이클 위 능동 셀이 모두 순방향이다."""
    return all(cells[name].forward for name in _flat(loop.devices) if name in cells and cells[name].kind in _ACTIVE)


def _view_roles(view_id, loops, cells, declared_pm):
    by_cut = {}
    roles = []
    for loop in loops:
        if LOOP_BIAS_SCC in loop.classes or LOOP_COMPOSITE_INTERNAL in loop.classes:
            role = LOOP_BIAS_SCC if LOOP_BIAS_SCC in loop.classes else LOOP_COMPOSITE_INTERNAL
            roles.append(LoopRole(json.dumps(list(loop.nodes)), role, view_id))
        elif LOOP_VIEW in loop.classes and loop.cut:
            by_cut.setdefault(loop.cut, []).append(loop)
    for cut, members in sorted(by_cut.items()):
        internal = all(LOOP_MILLER in m.classes and _inside_forward(m, cells) for m in members)
        reason = (REASON_PM_DECLARED if declared_pm else REASON_COMPENSATION_NEEDS_PM) if internal else ""
        roles.append(LoopRole("loop:" + cut[0] + ":" + cut[1], LOOP_COMPENSATION_INTERNAL if internal else LOOP_VIEW, view_id, reason))
    return roles


def loop_roles(view_loops, transfer_views, declared_pm_views):
    cells_of = {view_id: {c.dev: c for c in cells} for view_id, cells in transfer_views}
    result = []
    for view_id, loops in view_loops:
        for role in _view_roles(view_id, loops, cells_of.get(view_id, {}), view_id in declared_pm_views):
            if role not in result:
                result.append(role)
    return tuple(result)
