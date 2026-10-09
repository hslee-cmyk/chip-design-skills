"""출발점 면적 추정 -- 탐색 축 `area_search_m2` 와 같은 구성 (설계 41 §6.4-5, 결정 11; `iv_area`·`start_intervals` 가 함께 쓴다).

`area_estimate(ctx, currents, gm_id, lengths, cap_values, res_values) -> (총 m², {MOS: W·L m²}, 수동소자 m²)`.

A = Σ_MOS W·L + Σ_수동소자 (단위 면적 × 값) + 접촉 머리. W = I·L / IDu(gm/ID, L) (IDu = `idu_curve` -- 같은 전류밀도 좌표), 수동소자는 측정 부하를 뺀 `PassiveAreaDecl` 의 것.
전류를 모르는 MOS(`currents` 에 없음)는 합에서 빠지고 두 번째 반환값에 `{MOS: None}` 으로 남는다 -- 호출부가 채우거나 보고한다(조용히 0 이 되지 않는다).
수동소자 값 = spec 선언값 -> 매크로 값(`cap_values`·`res_values`) -> θ 상자 기하 중점 순. 값을 정할 수 없는 소자는 합에서 빠지고 `None` 이다.
"""
import math

from .iv_curves import QUANTITY_IDU

_BOX_KEYS = ("capacitance", "resistance", "ss_resistance")


def _passive_value(ctx, name, cap_values, res_values):
    declared = ctx.element_values.get(name)
    if declared is not None:
        return float(declared)
    for table in (cap_values, res_values):
        if name in table:
            return float(table[name])
    box = next((ctx.box[(k, name)] for k in _BOX_KEYS if (k, name) in ctx.box), ctx.theta_bounds.get(name))
    return None if box is None else math.sqrt(box[0] * box[1])


def area_estimate(ctx, currents, gm_id, lengths, cap_values, res_values):
    per_device, gate = {}, 0.0
    for d in ctx.devices:
        current = currents.get(d.name)
        bundle = ctx.curves.bundle_of(d.name, d.kind, lengths[d.name])
        if current is None or bundle is None:
            per_device[d.name] = None
            continue
        per_device[d.name] = current * lengths[d.name] ** 2 / ctx.curves.value(bundle, QUANTITY_IDU, gm_id[d.name])
        gate += per_device[d.name]
    heads = dict(ctx.passive_area.head_area)
    passive = 0.0
    for name, unit in ctx.passive_area.unit_area:
        value = _passive_value(ctx, name, cap_values, res_values)
        if value is not None:
            passive += unit * value + heads.get(name, 0.0)
    return gate + passive, per_device, passive
