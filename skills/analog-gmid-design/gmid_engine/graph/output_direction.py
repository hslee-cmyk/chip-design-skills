"""출력 구동 방향 구조 판정 β/σ/κ (설계 41 §1.9, 계획 DEC-65).

진입점: `output_directions(model, ground, reach, nets) -> tuple[OutputDirection]`.

노드 k 마다 충전(전류가 k 로 들어옴)/방전(k 에서 나감) 방향으로 전류를 댈 수 있는 셀을 모은다. 방향은 소자 종류와 k 가 붙은 채널 단자로 정한다
(전압 값이 필요 없다): NMOS 는 source 가 k 에 붙으면 충전·drain 이 붙으면 방전, PMOS 는 drain 이 붙으면 충전·source 가 붙으면 방전.
셀의 DC 역할 구분(값은 `ls` 가 낸다, 여기서는 구조 판정만):
* β = gate 가 신호 경로 밖(DC 바이어스 셀, 봉인점 ID 가 상한).
* σ = gate 가 신호 넷이고 DC 역할이 바이어스 전류원이 아닌 신호 셀(LUT ID(VGS_max) 가 상한).
* κ = gate 가 신호 넷이지만 DC 역할이 바이어스 전류원인 측면 주입 셀(K8, 상한 미상).
토폴로지: 두 방향 모두 σ 가 있으면 `push_pull`, 한 방향만 σ 면 `class_a`, 어느 방향도 σ 가 없으면 `none`. class-AB 대 class-B 는 DC 동작점 값이라
여기서 정하지 않는다. 제공 넷은 호출자가 정한다(감지 넷과 블록 출력노드).
"""
from gmid_engine.core import sorted_items

from .s1_values import NMOS, PMOS, ROLE_BIAS
from .s1v_values import (
    DIR_BETA,
    DIR_KAPPA,
    DIR_SIGMA,
    TOPO_CLASS_A,
    TOPO_NONE,
    TOPO_PUSH_PULL,
    OutputDirection,
)


def _direction(m, net):
    """k 에 붙은 채널 단자로 정한 방향: 'charge' / 'discharge' / None(채널 단자가 아님)."""
    if m.kind == NMOS:
        return "charge" if m.s == net else "discharge" if m.d == net else None
    if m.kind == PMOS:
        return "charge" if m.d == net else "discharge" if m.s == net else None
    return None


def _class(m, signal):
    if m.g not in signal:
        return DIR_BETA
    return DIR_KAPPA if m.dc_role == ROLE_BIAS else DIR_SIGMA


def output_directions(model, ground, reach, nets):
    out = []
    for net in sorted(set(nets) - ground):
        sides = {"charge": [], "discharge": []}
        for m in model.mos:
            side = _direction(m, net)
            if side is not None and m.g != m.d:
                sides[side].append((m.name, _class(m, reach.signal)))
        sigma = [bool([1 for _, c in sides[side] if c == DIR_SIGMA]) for side in ("charge", "discharge")]
        topology = TOPO_PUSH_PULL if all(sigma) else TOPO_CLASS_A if any(sigma) else TOPO_NONE
        out.append(OutputDirection(net, sorted_items(sides["charge"]), sorted_items(sides["discharge"]), topology))
    return tuple(out)
