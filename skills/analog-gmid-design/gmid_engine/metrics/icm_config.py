"""ICMR 측정 구성 계산 블록 -- 봉인점 KCL 선형 감도 끝 (계획 N3.8 'ICMR 측정 구성'·'ICMR servo 감도 -- KCL'·'창 필드', 설계 41 §4.7-3b·4.7-W W1·W2, 사용자 결정
O-58·O-108·O-115·O-204·O-205, 카드 IT-2c).

진입점: `icm_config_window`(`@compute_block`, writer `icm_config`) -- `icm_config_window(snapshot, lut, donors=, counters=)`.
reads `node.{dc_writer, dc_rail_v, port_direction, port_role, dc_v}`, `device.{pins, kind, bulk, dc_L, dc_colour, dc_coord, dc_tol_v, dc_sat_v}`, `graph.{ss_nodal, views}`;
writes `node.dc_window_cfg`(입력 포트마다 `Window`, 구성이 None 이면 항목 없음)·`graph.icm_config`(key `METRICS_KEY`) = `IcmConfig`.

**물리 틀**(원칙 3·4): ICMR·창은 DC 양이고 설계점 질문이 아니라 정해진 회로를 흔드는 섭동 질문이다 -- W·바이어스 전압 고정 KCL. 봉인점 DC 야코비안 `graph.ss_nodal`(용량 개방, 고정 =
교류접지 ∪ 입력 넷)에서 입력 포트를 모두 같은 x 로 움직이는 구동의 응답 vx 와 여기 방향 e 로 움직이는 구동의 응답 ve 를 같은 인수분해 위에서 풀고(`nodal_solve` 두 번), 감지 c 의
행 δs = 0 을 Schur 1칸으로 강제한다(servo): s_n = vx_n − (ve_n/span)·(c·vx)/a_e, a_e = c·ve/span. θ 감도(`writer_grad`)는 부르지 않는다. 경계 행 = 포화·`triode` 영역 행뿐
(`Circuit.region_rows`, VDS = VDSAT, 판정 여유 0 -- tol 항·전도 행 없음; VDSAT = 봉인점 필드 `device.dc_sat_v`, LUT 재호출 0). 창 끝 = `saturation_window` 의 행 교집합, 끝 상태는 레일 안 입력으로 자른다.

**갈래 순서**(앞이 이긴다, category 모두 `definitional`, 구성 None·`IcmConfig.undefined` 원소 하나·`node.dc_window_cfg` 항목 없음):
1 `graph.ss_nodal` 이 `Undefined` -> 같은 code·detail / 2 입력 포트 셋 이상 -> `icm_inputs_unsupported` / 3 입력 0 -> `view_required`(default_views 0) /
4 `default_port` 전달 뷰가 하나가 아님 -> `view_required`(default_views 수) / 4′ 그 뷰 감지가 출력 하나도 차동 출력쌍도 아님 -> `view_required`(sense) /
5 미지수 넷 가운데 G 행이 모두 0 인 넷(DC 전도 경로 없는 용량 전용 노드 -- 노달 인수분해의 `floating`) -> `icm_capacitive_only_node`(nets) / 6 입력 하나 -> `as_is_single_input`
(보정 없음, 구동 = 그 포트) / 7 입력 둘 -> `servo`(레일 폭 0·없음·특이·|a_e|·span ≤ δV_out -> `icm_servo_pivot_unresolved`).
포트 role·회로 이름은 결과를 정하지 않는다(입력 p/n·출력 p/n 을 맞바꾸면 e → −e, c → −c 로 부호가 상쇄된다). 선언 되먹임·spec 의 ICMR 기능 기준 칸은 읽지 않는다.

**기본 포트 뷰**: S1v `graph.views` 의 `kind == transfer` 이고 `default_port` 인 뷰(재유도 0 -- 여기 가중·감지 넷은 그 뷰의 `excite`·`sense`). S1v 필드가 아예 없는 스냅샷(단계 A 를
거치지 않은 단위 평가)은 같은 규칙 `graph.default_port_seeds` 를 포트 사실에서 부른다 -- 규칙 정의는 `graph/views.py` 하나다.

**창**: 이동량 [dlo, dhi] = 행 교집합, 끝 상태 레일 자름(s_p ≠ 0 인 입력 포트마다 rail_min ≤ V_p + s_p·Δ ≤ rail_max), 포트 창 = `Circuit.port_window`. 행·감도·끝 가운데 하나라도 정의되지
않거나 Δlo > Δhi(건너뛴 행의 slack < 0 포함)이면 모든 입력 포트 `Window(None, None, 0, "unmeasured")`. `tol_v` = 봉인점 `device.dc_tol_v` 가운데 `device.dc_coord` MOS 의 None 아닌 값의 최솟값.
**V_cm 칸**: `vcm0` = 봉인점 입력 포트 전압 평균, 끝 상태 Δ 의 V_cm = vcm0 + s̄·Δ (s̄ = 입력 포트 감도 평균), `vcm_lo`·`vcm_hi` = 두 끝 상태 값의 min·max(s̄ = 0 이면 둘 다 vcm0),
한 포트라도 `unmeasured` 이면 None. 커널 `node.dc_window` 의 상태는 이어받지 않는다.

**판정 분해능**(`_transfer_resolution`): δV_out = Σ_u |z_u|·(|r_u| + Σ_j E_uj·|v_j|) (z = 감지 관측의 수반 해, r = 풀이 KCL 잔차, E = `NodalSystem.g_bound`, v = 구동 = 레일 폭 풀이).
판정 불능은 |c·v| ≤ δV_out. 상수 없음 -- 부동소수 조립·풀이 오차의 1차 상계다.

* `kvl_sensitivity(nodal, drive, servo=None) -> (slope, a_e, ve) | None`: `drive` = 입력 포트 넷 tuple, `servo` = None 또는 `(excite, sense, span)`(excite = ((넷, e 가중), ...),
  sense = ((넷, 부호), ...), span = 레일 폭 V). slope = {넷: dV/dx} -- servo None 이면 구동 넷 = 1, servo 면 구동 넷 = 1 − e_p·(c·vx)/a_e, 그 밖 고정 넷·떠 있는 노드 = 0.
  a_e = (c·ve)/span(servo None 이면 None), ve = 구동 {p: span·e_p} 의 노드 전압(servo None 이면 None). 인수분해 특이·풀이 None·a_e 정확히 0 이면 None.
"""
import numpy

from gmid_engine.authoring import INPUT_DIRECTION, REGION_TRIODE
from gmid_engine.core import compute_block
from gmid_engine.graph import F_VIEW_REQUIRED
from gmid_engine.sizing import (ICM_CONFIG_SERVO, ICM_CONFIG_WRITER, INPUT_STATUS_MEASURED, INPUT_STATUS_UNMEASURED, METRICS_KEY, Circuit, Window,
                                default_port_views, saturation_window, sense_signs)

from ._helpers_nodal import nodal_adjoint, nodal_solve
from .aux_types import IcmConfig
from .mna_types import Undefined

READS = (
    ("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "port_direction"), ("node", "port_role"), ("node", "dc_v"),
    ("device", "pins"), ("device", "kind"), ("device", "bulk"), ("device", "dc_L"), ("device", "dc_colour"), ("device", "dc_coord"),
    ("device", "dc_tol_v"), ("device", "dc_sat_v"), ("device", "region_decl"),
    ("graph", "ss_nodal"), ("graph", "views"),
)
WRITES = (("node", "dc_window_cfg"), ("graph", "icm_config"))
QUANTITY = "icm_config"
CATEGORY = "definitional"
CONFIG_SERVO = ICM_CONFIG_SERVO
CONFIG_AS_IS = "as_is_single_input"
CONFIGS = (CONFIG_AS_IS, CONFIG_SERVO)                  # 입력 포트 수 − 1 이 색인: 입력 하나 = 회로 그대로, 입력 둘 = servo (셋 이상은 지원 밖)
CODE_INPUTS_UNSUPPORTED = "icm_inputs_unsupported"
CODE_CAPACITIVE_ONLY = "icm_capacitive_only_node"
CODE_PIVOT_UNRESOLVED = "icm_servo_pivot_unresolved"


def _undefined(code, detail):
    return Undefined(QUANTITY, code, CATEGORY, detail)


def _sense_vector(nodal, sense):
    """감지 벡터 c: sense = ((넷, 부호), ...) -> 길이 n 배열(관측 = c·v)."""
    index = {net: i for i, net in enumerate(nodal.nodes)}
    c = numpy.zeros(len(nodal.nodes))
    for net, sign in sense:
        c[index[net]] += sign
    return c


def kvl_sensitivity(nodal, drive, servo=None):
    index = {net: i for i, net in enumerate(nodal.nodes)}
    if not all(index[net] in nodal.fixed for net in drive):
        raise ValueError("kvl_sensitivity: 구동 넷은 고정 노드(입력 포트)여야 한다: %r" % (tuple(drive),))
    size = len(nodal.nodes)
    volt_x, _residual = nodal_solve(nodal.factor, size, {index[net]: 1.0 for net in drive})
    if volt_x is None:
        return None
    if servo is None:
        return {net: float(volt_x[i]) for net, i in index.items()}, None, None
    excite, sense, span = servo
    c = _sense_vector(nodal, sense)
    volt_e, _residual = nodal_solve(nodal.factor, size, {index[net]: span * weight for net, weight in excite})
    if volt_e is None:
        return None
    a_e = float(c @ volt_e) / span
    if a_e == 0:
        return None
    ratio = float(c @ volt_x) / a_e
    slope = {net: float(volt_x[i]) - float(volt_e[i]) / span * ratio for net, i in index.items()}
    return slope, a_e, volt_e


def _transfer_resolution(system, volt, sense):
    """δV_out = Σ_u |z_u|·(|r_u| + Σ_j E_uj·|v_j|) (V) -- 모듈 머리말 '판정 분해능'. 풀이 `volt` 가 없거나 수반 풀이가 특이하면 None."""
    if volt is None:
        return None
    z = nodal_adjoint(system.factor, len(system.nodes), sense)
    if z is None:
        return None
    unknown = system.factor[0]
    residual = system.g[unknown, :] @ volt
    rounding = system.g_bound[unknown, :] @ numpy.abs(volt)
    return float(numpy.abs(z[unknown]) @ (numpy.abs(residual) + rounding))


def _select(projection, nodal, inputs, directions):
    """갈래 1~5 -> `Undefined`, 아니면 (구성 이름, 여기 ((넷, e), ...), 감지 ((넷, 부호), ...))."""
    if isinstance(nodal, Undefined):
        return Undefined(QUANTITY, nodal.code, nodal.category, nodal.detail)
    if len(inputs) > len(CONFIGS):
        return _undefined(CODE_INPUTS_UNSUPPORTED, (("inputs", inputs),))
    views = default_port_views(projection, directions)
    if not inputs or len(views) != 1:                        # 입력 0(갈래 3)과 뷰가 하나로 정해지지 않음(갈래 4)이 같은 code
        return _undefined(F_VIEW_REQUIRED, (("default_views", len(views)),))
    (view,) = views
    sense = sense_signs(view, dict(projection.column("node", "port_role")))
    if sense is None:
        return _undefined(F_VIEW_REQUIRED, (("sense", tuple(view.sense)),))
    floating = tuple(sorted(nodal.nodes[i] for i in tuple(nodal.factor[4]) + tuple(nodal.factor[5])))      # DC 전도 경로 없는 용량 전용 노드 = floating ∪ charge(NL-1 이 둘로 가른다)
    if floating:
        return _undefined(CODE_CAPACITIVE_ONLY, (("nets", floating),))
    return CONFIGS[len(inputs) - 1], tuple(view.excite), sense


def _pivot_unresolved(detail):
    return _undefined(CODE_PIVOT_UNRESOLVED, detail)


def _sensitivity(nodal, config, inputs, excite, sense, span):
    """구성의 감도 -> (slope 또는 None, a_e, 분해능 δA_num) 또는 `Undefined`(servo 피벗 판정 불능). as_is 의 피벗 두 칸은 기록뿐이다(판정 없음)."""
    servo = config == CONFIG_SERVO
    if servo and not span:
        return _pivot_unresolved((("rail_span", span),))
    found = kvl_sensitivity(nodal, inputs, (excite, sense, span) if servo else None)
    if servo:
        if found is None:
            return _pivot_unresolved((("singular", True),))
        slope, a_e, volt = found
        delta = _transfer_resolution(nodal, volt, _sense_vector(nodal, sense))
        if delta is None:
            return _pivot_unresolved((("singular", True),))
        resolution = delta / span
        if abs(a_e) * span <= delta:
            return _pivot_unresolved((("a_e", a_e), ("resolution", resolution)))
        return slope, a_e, resolution
    slope = None if found is None else found[0]              # as_is: 감도가 특이이면 창이 정의되지 않는다(unmeasured), 피벗 두 칸은 기록뿐
    a_e = resolution = None
    if span:                                                 # 피벗 기록: 구동 = 레일 폭, 그 입력 하나의 풀이
        index = {net: i for i, net in enumerate(nodal.nodes)}
        volt, _residual = nodal_solve(nodal.factor, len(nodal.nodes), {index[net]: span for net in inputs})
        if volt is not None:
            c = _sense_vector(nodal, sense)
            a_e = float(c @ volt) / span
            delta = _transfer_resolution(nodal, volt, c)
            resolution = None if delta is None else delta / span
    return slope, a_e, resolution


def _end_state(circuit, rows, slope, inputs, volts):
    """끝 상태 이동량 (Δlo, Δhi) 또는 None: 행 교집합 ∩ 입력 포트마다 레일 안."""
    found = saturation_window(None, None, None, None, rows, slope=slope)
    if found is None:
        return None
    lo, hi = found[0], found[1]
    for net in inputs:
        s = slope[net]
        if s != 0:
            a, b = (circuit.lo - volts[net]) / s, (circuit.hi - volts[net]) / s
            lo, hi = max(lo, min(a, b)), min(hi, max(a, b))
    return None if lo > hi else (lo, hi)


def _tol_v(projection):
    """cfg `tol_v`: 봉인점 `device.dc_tol_v` 가운데 `device.dc_coord` MOS 의 None 아닌 값의 최솟값, 모두 None 이면 None."""
    tols = dict(projection.column("device", "dc_tol_v"))
    found = [tols[m] for m, _coord in projection.column("device", "dc_coord") if tols.get(m) is not None]
    return min(found) if found else None


def _vcm(inputs, slope, volts, ends):
    """V_cm 칸 (vcm0, vcm_lo, vcm_hi): 입력 포트 전압의 평균, 끝 상태 Δ 에서 vcm0 + s̄·Δ 의 min·max(측정 실패면 None)."""
    vcm0 = sum(volts[net] for net in inputs) / len(inputs)
    if ends is None:
        return vcm0, None, None
    mean_slope = sum(slope[net] for net in inputs) / len(inputs)
    if mean_slope == 0:
        return vcm0, vcm0, vcm0
    a, b = vcm0 + mean_slope * ends[0], vcm0 + mean_slope * ends[1]
    return vcm0, min(a, b), max(a, b)


@compute_block(ICM_CONFIG_WRITER, reads=READS, writes=WRITES)
def icm_config_window(projection):
    (lut,) = projection.extras
    linear = frozenset(m for m, r in projection.column("device", "region_decl") if r.region == REGION_TRIODE)                  # `triode` 선언 소자 -- 영역 선언 술어 필드 `device.region_decl` 에서(경계 행이 triode 행)
    nodal = projection.value("graph", METRICS_KEY, "ss_nodal")
    directions = dict(projection.column("node", "port_direction"))
    inputs = tuple(sorted(net for net, d in directions.items() if d == INPUT_DIRECTION))
    chosen = _select(projection, nodal, inputs, directions)
    if isinstance(chosen, Undefined):
        return {("node", "dc_window_cfg"): {}, ("graph", "icm_config"): {METRICS_KEY: IcmConfig(None, None, None, None, None, None, (chosen,))}}
    config, excite, sense = chosen
    rails = tuple(v for _net, v in projection.column("node", "dc_rail_v") if v is not None)
    span = max(rails) - min(rails) if rails else None
    volts = {**dict(projection.column("node", "dc_rail_v")), **dict(projection.column("node", "dc_v"))}
    found = _sensitivity(nodal, config, inputs, excite, sense, span)
    if isinstance(found, Undefined):
        return {("node", "dc_window_cfg"): {}, ("graph", "icm_config"): {METRICS_KEY: IcmConfig(None, None, None, None, None, None, (found,))}}
    slope, a_e, resolution = found
    ends = None
    if slope is not None and rails:
        circuit = Circuit(projection, lut=lut, linear=linear)
        rows = circuit.region_rows(volts, dict(projection.column("device", "dc_sat_v")))
        ends = None if rows is None else _end_state(circuit, rows, slope, inputs, volts)
    if ends is None:
        windows = {net: Window(None, None, 0, input_status=INPUT_STATUS_UNMEASURED) for net in inputs}
    else:
        tol_v = _tol_v(projection)
        windows = {net: Window(*circuit.port_window(volts[net], slope[net], *ends), 0, INPUT_STATUS_MEASURED, tol_v) for net in inputs}
    vcm0, vcm_lo, vcm_hi = _vcm(inputs, slope, volts, ends)
    return {("node", "dc_window_cfg"): windows,
            ("graph", "icm_config"): {METRICS_KEY: IcmConfig(config, a_e, resolution, vcm0, vcm_lo, vcm_hi)}}
