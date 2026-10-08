"""공통 모드 루프 절단 분할 -- 차동 출력 넷에 channel 단자가 물린 MOS 를 구동자(x 쪽)·소비자(n 쪽)로 가른다 (사용자 결정 2026-10-08).

진입점: `cm_partition(outputs, mos, two_terminals, rails, declared=None, source_nets=()) -> CmPartition`.

순수 함수(이름·회로 리터럴 없음). 입력은 넷 이름(또는 정수 인덱스 -- 동등 비교만 쓴다)으로 쓴 중립 구조:
`outputs` = 차동 출력 넷 tuple, `mos` = (이름, drain, gate, source) tuple, `two_terminals` = 수동소자 (a, b) tuple (저항·커패시터),
`rails` = 공급 레일 넷, `source_nets` = 이상원(전류·전압) 단자 넷 -- 둘 다 닿으면 레일에 닿은 것으로 센다(RR). 공급 레일은 감지 쪽 판정(ST)에서 빼지만
이상원 단자 넷은 뺀다 하지 않는다(감지 노드에 기준 전원이 바로 붙은 경우를 모호로 잡는다).

분류(후보 = drain·source 중 정확히 하나가 출력 넷인 MOS; 둘 다 출력 넷이면 포트 사이 통과 소자라 옮기지 않는다):
* 도달 집합 R = 후보의 **다른** channel 단자에서 MOS channel(drain–source)과 수동소자 2단자를 따라 퍼진 넷(어느 출력 넷도 지나지 않고,
  레일 넷은 닿으면 표시만 하고 더 퍼지지 않는다).
* RR = R 이 레일에 닿는다. ST = R 의 비레일 넷 중 어떤 MOS 의 gate 가 걸린 넷이 있다(= 감지 쪽 구조에 닿는다).
* RR 이고 ST 가 아님 -> **구동자**(출력 단: 전류원·캐스코드·소스 축퇴 등, x 쪽). RR 아님 -> **소비자**(감지망, n 쪽).
  RR 이고 ST -> **모호**(레일에 닿지만 감지 쪽 넷을 거친다: 기준 저항·기준 전원이 감지 쪽에 있음 등).
* 후보 MOS 의 gate 가 출력 넷이면(다이오드 접속·자기참조) 모호.
선언(`declared` = 소비자 MOS 이름 집합)이 있으면 분류를 덮어쓴다: 소비자 = 선언 ∩ 후보, 나머지 후보는 구동자. 구조 분류가 모호하지 않은데
선언이 구조 소비자 집합과 다르면 `disagrees` 에 두 집합을 남긴다(호출자가 거부).
**절단 교차 검사(최종 분할에 항상)**: (i) 구동자 gate 가 출력 넷이거나 자기 도달 집합에 있지 않다, (ii) x 영역(구동자 도달 집합의 비레일
넷)에 gate 가 걸린 MOS 의 channel 이 x 영역에 닿지 않는다 -- 어기면 CM 되먹임이 절단선을 지나지 않고 x 안에서 닫힐 수 있어 모호로 멈춘다.
이 검사는 국소 충분조건이며 모든 CM 경로를 증명하지는 않는다.
결과(`CmPartition`): `drivers` = ((MOS 이름, 옮길 출력 넷), ...) -- **MOS 이름 오름차순**(canonical 순서; 이름 비의존 순서는 아니다: 이름을 바꾸면 순서가 바뀔 수 있으므로
소비자는 `cuts` 를 집합으로 읽어야 하고 값 계산은 순서와 무관하다), `consumers` = 소비자 MOS 이름 오름차순 tuple, `ambiguity` = None 또는 사유 문자열,
`disagrees` = None 또는 (구조 소비자 이름 tuple, 선언 이름 tuple).

인자 형식(모두 필수 위치 인자, 이름·넷은 비교 가능한 hashable -- authoring 은 문자열, metrics 는 소신호 회로 정수 노드 인덱스·MOS 라벨):
* `outputs`: 출력 넷 tuple(보통 2개: 차동 쌍). `mos`: (이름, drain, gate, source) tuple 의 iterable -- 이름은 유일. `two_terminals`: 수동소자 (a, b) tuple 의 iterable
  (저항·커패시터; 스위치드 kind 는 호출 전에 `cm_loop_view` 가 `cm_switched` 로 멈춘다).
* `rails`: 공급 레일 넷 iterable. `source_nets`: 이상원 단자 넷 iterable(기본 ()). `declared`: None(구조 분류만) 또는 소비자(CM 감지) MOS 이름 iterable(빈 것 가능).
"""
import dataclasses


@dataclasses.dataclass(frozen=True)
class CmPartition:
    drivers: tuple = ()
    consumers: tuple = ()
    ambiguity: object = None
    disagrees: object = None


def _reach(start, adjacency, outputs, rails):
    seen, rail_hit, stack = set(), False, [start]
    while stack:
        net = stack.pop()
        if net in seen or net in outputs:
            continue
        seen.add(net)
        if net in rails:
            rail_hit = True
            continue
        stack.extend(adjacency.get(net, ()))
    return seen, rail_hit


def cm_partition(outputs, mos, two_terminals, rails, declared=None, source_nets=()):
    out = frozenset(outputs)
    rails = frozenset(rails)
    stops = rails | frozenset(source_nets)
    adjacency = {}
    for _name, d, _g, s in mos:
        adjacency.setdefault(d, []).append(s)
        adjacency.setdefault(s, []).append(d)
    for a, b in two_terminals:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)
    gate_nets = frozenset(g for _n, _d, g, _s in mos)
    candidates = []
    for name, d, g, s in sorted(mos):
        ends = [net for net in (d, s) if net in out]
        if len(ends) == 1 and d != s:
            candidates.append((name, ends[0], s if d == ends[0] else d, g))
    structural, reaches, reasons = {}, {}, []
    for name, net, other, gate in candidates:
        seen, rail_hit = _reach(other, adjacency, out, stops)
        reaches[name] = seen - rails
        sense = any(n in gate_nets for n in seen - rails)
        if gate in out:
            reasons.append("소자 " + repr(name) + " 의 gate 가 출력 넷 " + repr(gate) + " 에서 구동된다(다이오드 접속·자기참조)")
        elif rail_hit and sense:
            reasons.append("소자 " + repr(name) + " 은 레일에 닿지만 gate 가 걸린 감지 쪽 넷을 거친다(기준 저항·기준 전원이 감지 쪽에 있음)")
        structural[name] = "driver" if rail_hit else "consumer"
    structural_consumers = frozenset(n for n, kind in structural.items() if kind == "consumer")
    if declared is not None:
        consumers = frozenset(declared) & frozenset(structural)
        disagrees = None
        if not reasons and structural_consumers != consumers:
            disagrees = (tuple(sorted(structural_consumers)), tuple(sorted(declared)))
        reasons = []
    else:
        consumers, disagrees = structural_consumers, None
    drivers = tuple((name, net) for name, net, _o, _g in candidates if name not in consumers)
    ambiguity = "; ".join(reasons) if reasons else None
    if ambiguity is None and drivers:
        ambiguity = _crossing_check(drivers, candidates, reaches, mos, out)
    return CmPartition(drivers, tuple(sorted(consumers)), ambiguity, disagrees)


def _crossing_check(drivers, candidates, reaches, mos, out):
    names = {name for name, _net in drivers}
    x_region = set()
    for name in names:
        x_region |= reaches[name]
    gates = {name: g for name, _net, _o, g in candidates}
    for name in sorted(names):
        if gates[name] in x_region or gates[name] in out:
            return "구동자 " + repr(name) + " 의 gate 가 출력 넷 또는 자기 도달 집합에 있다(CM 되먹임이 절단선을 지나지 않을 수 있다)"
    for name, d, g, s in sorted(mos):
        if name not in names and g in x_region and (d in x_region or s in x_region):
            return ("소자 " + repr(name) + " 의 gate 가 구동자 쪽 넷에 걸리고 channel 도 구동자 쪽 넷에 닿는다 -- CM 되먹임이 "
                    "절단선을 지나지 않고 구동자 쪽 안에서 닫힐 수 있다")
    return None
