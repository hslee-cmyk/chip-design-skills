"""뷰와 무관한 교류접지 분류 (계획 N3.2-1 (1)(2), 설계 design_mod3_s1_graph 2.2 `ac_ground_static.py`).

진입점: `static_ac_ground(index, rails, input_nets) -> tuple`.

반환 = `index`(`terminal_index` 결과) 넷 순서 그대로 ((넷, 분류 | None), ...):
* (1) `AC_GROUND_RAIL` -- 레일 선언 넷.
* (2) `AC_GROUND_GATE_ONLY` -- 레일이 아니고, 입력 포트가 아니며, 단자가 전부 MOS gate 인 넷(수동소자·이상원 단자가
  붙으면 아님). 외부에서 바이어스 전압이 걸리는 넷으로 보고 교류 0 으로 둔다.
* 그 밖 None. (3) 이상 전압원 단자는 library 발동 0 이라 구현하지 않는다 -- 전압원은 S1 `device.unsupported` 에
  기록만 남는다. (4) 바이어스 종속 넷은 뷰 속성이라 다음 단계(U7) 몫이다.
"""
from .s1_values import AC_GROUND_GATE_ONLY, AC_GROUND_RAIL, MOS_GATE


def static_ac_ground(index, rails, input_nets):
    result = []
    for net, pins in index:
        if net in rails:
            cls = AC_GROUND_RAIL
        elif net not in input_nets and all(term == MOS_GATE for _, term in pins):
            cls = AC_GROUND_GATE_ONLY
        else:
            cls = None
        result.append((net, cls))
    return tuple(result)
