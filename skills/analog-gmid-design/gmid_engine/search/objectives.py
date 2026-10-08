"""목적 값 -- S2 `graph.metrics_dc` 필드(MOD5 `metrics_dc` 계산 블록)에서 읽는다 (설계 2.2 '목적' 행, DEC-77·78·79,
metrics CONTRACT 7.5).

진입점: `objective_values(snapshot) -> Objectives`.

* [r4] 값의 정본 = `metrics_dc` 블록이 쓴 `graph.metrics_dc`(key `METRICS_KEY`) `MetricBundle` -- search 는 다시 계산하지 않는다
  (필드가 곧 캐시; 옛 S-6 해소). 부르는 쪽(`kernel.evaluate`)이 봉인 점은 `ss_evaluate`, 대기·미정 점은 `metrics_dc` 를 같은
  (수동소자 값, counted_rails = ()) 로 불러 필드를 만든 스냅샷을 넘긴다 -- 같은 입력이면 블록 재사용.
* 전력 축 = `power_dc_w`(선언된 모든 공급 레일 Σ V·I, metrics 7.5 Q4), 면적 축 = `area_search_m2`. `supply_current_dc` 는
  `counted_rails_undeclared`(spec 선언 대기 -- 쓰지 않는다). 둘 중 하나라도 값이 None 이면 `ValueError`(metrics 계약상 DC 점에서
  정의된다 -- 어기면 호출 계약 위반).
* `per_rail`·`kcl_residual_a`·`passive_area_undeclared`·`passive_value_undetermined` = bundle detail, `gate_area_m2` = Σ dc_op W·L
  (수동소자 면적 선언 U-36 이 없어 면적 축과 같다 -- 표에 병기용).
* `power_resolution_w` = b_P(아래 `_power_resolution`, 오케스트레이터 결정 S-2b).
"""
from gmid_engine.sizing import DC_KEY, METRICS_KEY

from .search_values import AXIS_AREA, AXIS_POWER, Objectives


def objective_values(snapshot):
    bundle = snapshot.value("graph", METRICS_KEY, "metrics_dc")
    values = {req.metric: res.value for req, res in bundle.entries}
    detail = dict(bundle.detail)
    if values.get(AXIS_POWER) is None or values.get(AXIS_AREA) is None:
        raise ValueError("objective_values: metrics_dc 묶음에 목적 축 값이 없다 " + repr(values))
    orbit = dict(snapshot.column("device", "dc_colour"))
    gate = sum(o.W * o.L for _m, o in sorted(snapshot.column("device", "dc_op"), key=lambda r: (orbit.get(r[0], -1), r[0])))
    return Objectives(values[AXIS_POWER], values[AXIS_AREA], tuple(detail["per_rail_amp"]),
                      detail["kcl_residual_amp"], gate, tuple(detail["passive_area_undeclared"]),
                      tuple(detail["passive_value_missing"]), _power_resolution(snapshot))


def _power_resolution(snapshot):
    """b_P = Σ_레일 |V_k|·tol_I,k. tol_I,k = 레일 넷 k 에 채널이 닿는 MOS 의 dc_tol_v·gm 최댓값, gm = 그 점의 동작점 gm =
    dc_op.current·dc_op.gm_id(오케스트레이터 결정 S-2b, 2026-10-08). 봉인 3 KCL 허용오차와 같은 모양(노드마다 닿는 소자 최댓값)이지만
    봉인 3 은 곡선 전체 최대 gm(`dc_gm_bound`)을 쓴다(sizing 계약, 바꾸지 않음) -- 봉인은 어느 동작점에서나 안전한 상계가
    필요하지만 탐색 축 해상도는 '이 점의 전류가 tol_V 만큼 흔들릴 때 전력이 움직이는 양'이라 점 국소 gm 이 맞다(gm_bound 는 W 큰
    소자에서 수십~수천 배 과대, r2 실측). 어느 레일에도 정의된 행이 없으면 None."""
    tols = dict(snapshot.column("device", "dc_tol_v"))
    channel = {e: (a, b) for e, a, b in snapshot.value("graph", DC_KEY, "dc_current_basis").ends}   # MOS 채널 = (d, s)
    total, defined = 0.0, False
    node_orbit = dict(snapshot.column("node", "dc_colour"))
    device_orbit = dict(snapshot.column("device", "dc_colour"))
    for rail, volt in sorted(snapshot.column("node", "dc_rail_v"), key=lambda r: (node_orbit.get(r[0], -1), r[0])):   # 정준 합산 순서
        rows = [tols[m] * op.current * op.gm_id
                for m, op in sorted(snapshot.column("device", "dc_op"), key=lambda r: (device_orbit.get(r[0], -1), r[0]))
                if tols.get(m) is not None and rail in channel.get(m, ())]
        if rows:
            defined = True
            total += abs(float(volt)) * max(rows)
    return total if defined and total > 0 else None
