"""뷰별 교류접지 -- 바이어스 종속 넷 술어 (설계 41 §1.2, 계획 N3.2-1 (4)).

진입점: `view_ac_ground(model, seeds, sense, virtual, exceptions=frozenset()) -> AcGround`.

교류접지 G = (1) 레일 (2) gate 전용 미구동 넷(S1 `ac_ground_class`, 둘 다 `model.static_ground`) ∪ 이 뷰에서 여기하지 않는 입력 포트
∪ (4) 바이어스 종속 넷. (3) 이상 전압원은 S1 이 지원 밖으로 정지시켜 발동 0 이다(DEC-76).

**(4) 술어**(구조만으로 판정, 이름 없음). 이 뷰의 신호 넷 S(최소 고정점, `signal_reach`)에 든 넷 b 가 후보이려면:
* (0) b ∈ S 이고 여기 포트·감지 넷이 아니다.
* (i) 신호가 b 에서 나가는 단자가 gate 뿐이다 -- b 가 어떤 MOS 의 source 도 아니고 수동소자 단자도 아니며, 어떤 MOS 의 gate 이다.
* (ii) b 를 drain 으로 구동하는 MOS 가 하나 이상 있고 **모두** (가) b 를 gate 로도 읽거나(자기 구동 사슬의 국소 되먹임) (나) gate 가
  이 뷰의 신호 경로 밖(gate ∉ S)이다(바이어스 전류원).
* (iii) (가) 부류 소자 m 중 하나에서 **source -> drain 거슬러** 채널 단자만으로(gate 는 따라가지 않고, 교류접지 넷과 b 자신을 지나지
  않고) 올라가 닿는 넷 x 가 있고, x 가 **b 를 접지한 그래프(G ∪ {b})에서도 신호 넷**이다.
**뷰별 판정**: 후보 b 의 사슬 출발 넷 x 가 이 뷰의 여기로 움직이지 않으면 b 는 이 뷰의 교류접지다. x 가 움직이면 b 는 교류접지가 아니고
그 사슬이 만드는 폐경로는 (3) 루프로 등록된다(`AcGround.moving`). 움직임 판정은 `virtual`(자기대응 넷 = 대칭 가상접지로 확인된 넷의
집합, 호출자가 대칭 정보로 정한다. 대칭 정보가 없으면 빈 집합)을 쓴다 -- x ∈ virtual 이면 움직이지 않는다.
술어가 바뀐 G 로 다른 후보를 만들 수 있으므로 변화가 없을 때까지 반복한다(G 는 단조 증가라 끝난다).

**뷰 한정 예외**(41 §1.12.6, 40 §3.2-3 `ac_ground_exception` override): `exceptions` = ratified 사실이 **이 뷰에서만** 교류접지로 두라고 한 넷의 집합(호출자가 뷰 id 로 걸러 넘긴다).
술어 결과 위에 얹는다 -- 술어가 이미 접지한 넷은 그대로, 그렇지 않은 넷만 G 에 더하고(`AcGround.exceptions`) 변화가 없을 때까지 다시 반복한다. 다른 뷰에는 영향이 없다.
"""
import dataclasses

from gmid_engine.core import sorted_items

from .signal_reach import signal_reach


@dataclasses.dataclass(frozen=True)
class AcGround:
    """`nets` = 이 뷰의 교류접지 전체, `bias_dependent` = (4)로 접지된 넷과 그 사슬 출발 넷 ((b, (x, ...)), ...),
    `moving` = 후보였으나 출발 넷이 움직여 접지하지 않은 넷 ((b, (x, ...)), ...). `reach` = 최종 G 위의 `Reach`.
    `exceptions` = 뷰 한정 예외로 접지에 더한 넷 정렬 tuple."""

    nets: frozenset
    bias_dependent: tuple
    moving: tuple
    reach: object
    exceptions: tuple = ()


def _upstream(model, ground, start, banned):
    """`start` 에서 source -> drain 거슬러(드레인이 현재 넷인 소자의 source 로) 올라가는 닿는 넷 집합(start 포함)."""
    seen = set()
    pending = [start]
    while pending:
        net = pending.pop()
        if net in seen or net in ground or net == banned:
            continue
        seen.add(net)
        pending.extend(m.s for m in model.by_drain.get(net, ()))
    return seen


def _candidates(model, ground, reach, fixed):
    """(0)(i)(ii) 를 만족하는 넷과 (가) 부류 소자 목록."""
    out = []
    for net in sorted(reach.signal - ground - fixed):
        if model.by_source.get(net) or model.by_passive.get(net) or not model.by_gate.get(net):
            continue
        drivers = model.by_drain.get(net, ())
        if not drivers:
            continue
        if all(m.g == net or m.g not in reach.signal for m in drivers):
            own = tuple(m for m in drivers if m.g == net)
            if own:
                out.append((net, own))
    return out


def view_ac_ground(model, seeds, sense, virtual, exceptions=frozenset()):
    seeds = frozenset(seeds)
    fixed = seeds | frozenset(sense)
    ground = set(model.static_ground) | {net for net, _ in model.inputs if net not in seeds}
    bias = {}
    moving = {}
    added = set()
    while True:
        reach = signal_reach(model, ground, seeds, sense)
        grown = False
        for net, own in _candidates(model, ground, reach, fixed):
            starts = set()
            for m in own:
                chain = _upstream(model, ground, m.s, net)
                if chain:
                    starts |= chain & signal_reach(model, ground | {net}, seeds, ()).signal
            if not starts:
                continue
            ordered = tuple(sorted(starts))
            if not starts & signal_reach(model, ground | {net} | virtual, seeds, ()).signal:
                bias[net] = ordered
                ground.add(net)
                moving.pop(net, None)
                grown = True
            else:
                moving[net] = ordered
        if not grown:
            pending = (set(exceptions) - ground) & set(model.nets) - fixed
            if not pending:
                return AcGround(frozenset(ground), sorted_items(bias), sorted_items(moving), reach, tuple(sorted(added)))
            ground |= pending
            added |= pending
            for net in pending:
                moving.pop(net, None)
