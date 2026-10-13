"""목적 값 -- S2 `graph.metrics_dc` 필드(MOD5 `metrics_dc` 계산 블록)에서 읽는다 (설계 2.2 '목적' 행, DEC-77·78·79,
metrics CONTRACT 7.5).

진입점: `objective_values(snapshot) -> Objectives`.

* [r4] 값의 정본 = `metrics_dc` 블록이 쓴 `graph.metrics_dc`(key `METRICS_KEY`) `MetricBundle` -- search 는 다시 계산하지 않는다
  (필드가 곧 캐시; 옛 S-6 해소). 부르는 쪽(`kernel.evaluate`)이 봉인 점은 `ss_evaluate`, 대기·미정 점은 `metrics_dc` 를 같은
  (`passive_values` 블록 뒤, counted_rails = ()) 로 불러 필드를 만든 스냅샷을 넘긴다 -- 같은 입력이면 블록 재사용.
* 전력 축 = `power_dc_w`(선언된 모든 공급 레일 Σ V·I, metrics 7.5 Q4), 면적 축 = `area_search_m2`. `supply_current_dc` 는
  `counted_rails_undeclared`(spec 선언 대기 -- 쓰지 않는다). 둘 중 하나라도 값이 None 이면 `ValueError`(metrics 계약상 DC 점에서
  정의된다 -- 어기면 호출 계약 위반).
* `per_rail`·`kcl_residual_a`·`passive_area_undeclared`·`passive_value_undetermined` = bundle detail. `gate_area_m2`(Σ W·L)와
  `power_resolution_w`(전력 축 분해능 b_P, tol_I = tol_V × `dc_gm`)는 같은 블록이 쓴 `graph.gate_area_m2`·`graph.power_resolution_w` 필드를
  읽는다(설계 40 §2.4.7·§2.4.8 -- search 는 다시 계산하지 않는다).
"""
from gmid_engine.sizing import METRICS_KEY

from .search_values import AXIS_AREA, AXIS_POWER, Objectives


def objective_values(snapshot):
    bundle = snapshot.value("graph", METRICS_KEY, "metrics_dc")
    values = {req.metric: res.value for req, res in bundle.entries}
    detail = dict(bundle.detail)
    if values.get(AXIS_POWER) is None or values.get(AXIS_AREA) is None:
        raise ValueError("objective_values: metrics_dc 묶음에 목적 축 값이 없다 " + repr(values))
    return Objectives(values[AXIS_POWER], values[AXIS_AREA], tuple(detail["per_rail_amp"]),
                      detail["kcl_residual_amp"], snapshot.value("graph", METRICS_KEY, "gate_area_m2"),
                      tuple(detail["passive_area_undeclared"]), tuple(detail["passive_value_missing"]),
                      snapshot.value("graph", METRICS_KEY, "power_resolution_w"))
