"""목적 값 -- S2 dc 스냅샷 -> metrics `supply_currents`·`area_search` 입력 레코드 (설계 2.2 '목적' 행, DEC-77·78·79).

진입점: `objective_values(snapshot, resistances, element_values) -> Objectives`.

* 전력 축 = `power_dc_w` = Σ_k V_k·I_k(모든 레일, metrics 3.13). 레일 전류 합 `supply_current_dc` 는 합산 레일 선언
  (`counted_rails`)이 spec 에 없어 계산하지 않는다(열린 항목 S-5) -- 레일별 I_k 는 `per_rail` 로 남긴다.
* 면적 축(탐색 축) = `area_search_m2` = Σ W·L(dc_op) + 선언 수동소자 면적. 수동소자 단위 면적 선언(U-36)이 없어 값이 있는
  수동소자는 `passive_area_undeclared`, 값 자체가 미정(engine·pending)인 수동소자는 `passive_value_undetermined` 로 남긴다
  (DEC-79: 보상·부하 수동소자가 있는데 면적 선언이 없으면 front 는 `review_needed` -- 판단은 find_front 기록).
* 노드 = 넷 이름 정렬 index(metrics 는 정수 노드만 받는다). 채널 전류는 `dc_current_basis.ends`(양의 전류 from -> to)와
  `dc_current` 로 만든다(ChannelCurrent(from, to, I) -- metrics 는 drain·source 를 대칭으로 읽는다). 이상 전류원도 ends 로.
  DC 저항은 가지치기 밖(`basis.resistors`) 중 값이 있는 것(선언 또는 θ)만 -- 가지치기 저항은 전류 0 이다.
* metrics 계산 블록 배선(S2 metric 필드)이 아직 없어 search 가 순수 함수를 부른다(열린 항목 S-6).
"""
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE
from gmid_engine.metrics import (
    ChannelCurrent,
    CurrentSource,
    DcOperatingPoint,
    GateArea,
    PassiveArea,
    RailBias,
    Resistor,
    area_search,
    supply_currents,
)
from gmid_engine.sizing import DC_KEY

from .search_values import Objectives


def objective_values(snapshot, resistances, element_values):
    nodes = tuple(k for k, _v in snapshot.column("node", "is_rail"))
    index = {n: i for i, n in enumerate(nodes)}
    rails = tuple(RailBias(index[n], float(v)) for n, v in snapshot.column("node", "dc_rail_v"))
    node_v = tuple((index[n], float(v)) for n, v in snapshot.column("node", "dc_v"))
    classes = dict(snapshot.column("device", "element_class"))
    currents = dict(snapshot.column("device", "dc_current"))
    basis = snapshot.value("graph", DC_KEY, "dc_current_basis")
    ohms = dict(resistances)
    channels, sources, resistors = [], [], []
    for element, src, dst in basis.ends:
        amp = currents.get(element)
        if amp is None:
            continue
        if classes[element] == ELEMENT_MOS:
            channels.append(ChannelCurrent(index[src], index[dst], float(amp)))
        elif classes[element] == ELEMENT_SOURCE:
            sources.append(CurrentSource(index[src], index[dst], float(amp)))
        elif element in basis.resistors and ohms.get(element) is not None:
            resistors.append(Resistor(index[src], index[dst], float(ohms[element]), element))
    op = DcOperatingPoint(rails, node_v, tuple(channels), tuple(resistors), tuple(sources))
    # counted_rails = 모든 레일: power_dc_w·per_rail 만 쓰고 그 합(= KCL 잔차)인 supply_current_dc 는 쓰지 않는다(S-5)
    supply = supply_currents(op, tuple(r.node for r in rails))
    gates = tuple(GateArea(o.W, o.L, m) for m, o in snapshot.column("device", "dc_op"))
    values = dict(element_values)
    values.update(ohms)
    passives, undetermined = [], []
    for name, cls in sorted(classes.items()):
        if cls != ELEMENT_PASSIVE:
            continue
        if values.get(name) is None:
            undetermined.append(name)
        else:
            passives.append(PassiveArea(name, float(values[name])))
    area = area_search(gates, tuple(passives))
    per_rail = tuple((nodes[i], amp) for i, amp in supply.per_rail)
    return Objectives(supply.power_dc_w, area.area_search_m2, per_rail, supply.kcl_residual_amp, area.gate_area_m2,
                      area.passive_area_undeclared, tuple(undetermined), _power_resolution(snapshot))


def _power_resolution(snapshot):
    """b_P = Σ_레일 |V_k|·tol_I,k. tol_I,k = 레일 넷 k 에 d 또는 s 가 닿는 MOS 의 dc_tol_v·dc_gm_bound 최댓값(봉인 3 KCL 허용오차
    식을 레일 노드에 건 것 -- 레일 전류 한 칸의 판정 분해능). 어느 레일에도 정의된 행이 없으면 None."""
    tols = dict(snapshot.column("device", "dc_tol_v"))
    bounds = dict(snapshot.column("device", "dc_gm_bound"))
    channel = {e: (a, b) for e, a, b in snapshot.value("graph", DC_KEY, "dc_current_basis").ends}   # MOS 채널 = (d, s)
    total, defined = 0.0, False
    for rail, volt in snapshot.column("node", "dc_rail_v"):
        rows = [tols[m] * bounds[m] for m, _op in snapshot.column("device", "dc_op")
                if tols.get(m) is not None and rail in channel.get(m, ())]
        if rows:
            defined = True
            total += abs(float(volt)) * max(rows)
    return total if defined and total > 0 else None
