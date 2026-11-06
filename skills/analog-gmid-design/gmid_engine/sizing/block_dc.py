"""④⑤ DC 블록 `dc_solve` -- 노드전압 정본 풀이 + 소자별 폭 슬라이스 선택 + 소자 동작점 (WB-1, 설계 40 §3.7-A, 계획 DEC-105 (2)·DEC-31·DEC-88).

진입점: `dc_solve`(`@compute_block`, writer `dc_solve`) -- `dc_solve(snapshot, column_items, fixed_values, resistor_values, lut, geometry=None, realized=None)`.
노드전압 풀이와 W·동작점 계산을 한 블록에 합쳤다 --`device.dc_op`·`dc_sat_v`·`dc_ln_idu`·`node.dc_v`·`dc_path_values`·`dc_window`·`graph.dc_scc_log` 와 새 필드
`device.dc_finger`(`FingerGeom(m, w_f_m, residual)`)의 writer 는 이 블록 하나다.

* extras: `column_items` = θ 의 ln_idu·y·resistance 성분 (((kind, key), v), ...), `fixed_values` = ((넷, V), ...) W3·입력 DC, `resistor_values` = ((저항, Ω), ...) spec 선언값,
  `lut` = LutAccess(memo 만 -- 슬라이스 키 칸 없음), `geometry` = `RealizedGeometry`(레이아웃 뒤, 없으면 None), `realized` = `RealizedFinger`(기준 스냅샷 참조, 실현 평가·레이아웃 뒤 평가, 없으면 None).
* **순서(한 호출, 설계 40 §3.7-A 2)**: (1) 쓰기 소자(`dc_coord.role` = writer)마다 W = ID·L/exp(θ ln IDu) 를 상수로 `finger_slice` 가 (m, 슬라이스 폭, 키)를 고른다(반복 없음).
  (2) 노드 풀이(SCC 위상 순서; Rʳ 소자의 시작 키 = 그 kind 기준 폭 슬라이스 `cap_map[kind].w_key`). (3) 종속 소자마다 후보 슬라이스 s 의 W(s) = ID·L/IDu_s(노드 점)를
  `finger_slice` 에 넘겨 (m, s) 를 고른다(`op_point` 가 `is_slice_gap` 이면 그 후보를 뺀다, 그 밖 예외는 그대로). (4) Rʳ ≠ ∅ 이고 키 벡터가 달라졌으면 (2)부터 다시, 직전과 같으면 수렴, 이전
  벡터로 돌아가면 `SealViolationError`(reason `slice_cycle`, devices = Rʳ, detail `cycle`). Rʳ = writer 없는 순환 SCC 에서 수렴 허용오차 셀을 내는 종속 MOS(그 슬라이스 tol 표가 노드 풀이의
  tol 이 된다). Rʳ = ∅ 이면 노드 풀이는 한 번이다. (5) `DeviceOp.w_key`·`gm_id`·`idu_forward`·`dc_finger` 가 같은 슬라이스를 가리킨다.
* 평가는 θ 의 순수 함수다. `slice_missing` 이 나면 `devices = (소자,)` 를 채워 다시 던진다(reason 은 그대로).
* **손가락 기하 원리 하나(A-139)**: 모든 평가의 `device.dc_finger` = 그 평가가 쓴 손가락(소자 전부의 행)이다. 입력 손가락이면 `finger_slice` 를 부르지 않는다(키만 `slice_of_finger`).
* **레이아웃 뒤(`geometry` + 기준 스냅샷 `realized`)**: 실현 평가와 같은 W'·바이어스 고정 KCL 재풀이(`_kcl_solve`)이고 입력 손가락만 레이아웃에서 온다(`_layout_picks`):
  `RealizedGeometry.input_fingers` -- 배치 소자 = `layout_ref` (nf, finger_w), 요청 대기 소자 = `w_request` 의 요청 손가락 행 (nf, finger_w). 행 = (nf, finger_w, 0.0), W' = nf·finger_w.
  입력 손가락 행이 없는 소자(배치도 요청도 아님) = `realized_finger_missing`(사이징 점 행을 읽지 않는다). 기준 스냅샷 = 사이징 점이고 거기서 측정 구성·입력 값·피벗 판정만 읽는다.
  `geometry` 만 있고 `realized` 가 없으면(sizing 호출 계약 `w_request` = 요청 총 폭 W) 노드 재풀이 없는 W_request 평가(쓰기 소자 좌표 재기록, 종속 소자 어긋남은 봉인 3)이고 탐색 평가 전용이다.
* **실현 평가(`realized`, 설계 40 §3.7-A 2-5 (ii))**: 소자마다 탐색 스냅샷 `device.dc_finger` 의 (m, w_s) 가 입력이다(선택 함수 호출 0, 키 = `slice_of_finger`, 행이 없으면 `realized_finger_missing`).
  `DeviceOp.W` = W' = m·w_s, 전류 I' = 순방향 IDu·W'/L, 전류밀도 = I'·L/W', `dc_finger` = (m, w_s, 0.0). 탐색 스냅샷의 servo 피벗 판정(`graph.icm_config.config`)이 servo 면 W'·바이어스(고정 노드)·
  입력 공통모드 고정으로 KCL 을 출력 묶음 행(감지 합 = 탐색 점 값) + 입력 차 미지수로 감쇠 Newton(`newton_solve`)으로 다시 푼다. 판정 불능·입력 하나면 입력을 봉인점 값에 고정하고 출력·나머지 KCL 노드를
  같은 Newton 으로 다시 푼다(출력 묶음 행·입력 차 미지수만 없음). 고정 넷 = 레일 ∪ 입력 포트(`input_port_nets`)뿐이고 spec 목표 넷(W3)은 미지수다(O-244). 비수렴 = `NonconvergentError`,
  푼 노드가 레일 밖(레일 안 근 없음) = `no_root_in_window`(bounds = rail) -- 둘 다 fail-closed.
* 노드 x 의 writer 식(소자 m, kind 부호 s = +1 nmos / −1 pmos, VDS·VSB 는 노드전압 차의 크기):
  `vgs_gate`: V(g) = V(s) + s·VGS(ln IDu_m, L_m, VDS, VSB) / `vgs_source`: V(s) = V(g) − s·VGS(...) / `resistor_drop`: V(t1) = V(t0) − I·R(또는 반대쪽) /
  `free_window`(W4): V = lo + y·(hi − lo), [lo, hi] = x 에 채널이 닿는 전도 MOS 마다 VDS ≥ 0 이 되는 쪽의 교집합(KVL 순서 창, VDSAT 항 없음), 제약 없는 쪽은 레일 전압 범위 끝.
  창이 비면(lo > hi) `SealViolationError`(item 7, reason `empty_window`). 저항 강하 전류는 `device.dc_current` 를 읽는다(저항 강하 전류의 둘째 필드는 없다).
* 1변수 노드(diode gate·소스 추종 source)는 구간 괄호 근(`solve_self`, Brent). VDS 쪽 구간 끝 = writer 슬라이스의 VDS 정의역 하한(`vds_floor`), 다변수 순환 SCC 는 `gauss_seidel`
  (N3.6 q 규칙·K_max) 뒤 strict 검증 바퀴, 못 닿으면 감쇠 Newton(`newton_solve`). 허용오차 = SCC 쓰기 MOS(없으면 단자가 닿는 MOS) 슬라이스의 id_equivalent tol_V 셀의 최솟값(N3.6, tol_V 는 수치 자기 정합
  tolerance 이고 물리 경계가 아니다 O-240). 폭 = 레일 전압 범위.
* 종속 소자 좌표 ln IDu = ln(그 소자 슬라이스의 순방향 LUT IDu(노드 VGS, VDS, VSB)). 쓰기 소자 좌표 = θ.
* `path_values`(봉인 1 입력): 노드에 닿는 관계마다 그 관계가 함의하는 노드 전압(MOS = 좌표에서 VGS 역산, 저항 = 강하, W4·고정 = 값).
* `dc_sat_v` = `sat_threshold(memo, kind, DeviceOp.w_key, L, vgs, vds, vsb)`(선언 없음·`triode`, 비전도 포함), `off` 선언 소자 = `SatBound(None, None, "off_declared")`.
* 커널 창 `node.dc_window` = W4 뿌리마다 KVL 순서 창 하나(상태·`tol_v` 없음); 입력 창 측정은 `icm_config` 한 자리.
* READS 중 `graph.views`·`node.port_role`·`graph.dc_current_basis` 는 재풀이(`_kcl_solve`, views·port_role 은 servo 갈래만)가 읽는다: 기본 포트 뷰(`default_port_views` -- `graph.views`, 없으면 `node.port_role`·`port_direction` 에서
  같은 규칙)의 여기 가중·감지 부호(`sense_signs`, `node.port_role`), 전류 기저 끝점(`graph.dc_current_basis.ends`, 감지 합·KCL 행의 흐름 넷). 설계 40 §3.7-A 1 READS 문언에 없던 항목이다(문언 누락 -- 읽는 한 선언해야
  입력 버전이 바뀔 때 재계산된다). `is_servo_branch(ref)` 의 `graph.icm_config` 는 이 블록 자기 스냅샷이 아니라 입력 `search_ref` 스냅샷에서 읽는다.
"""
import dataclasses
import math

from gmid_engine.authoring import REGION_OFF, REGION_TRIODE, input_port_nets
from gmid_engine.core import NonconvergentError, SealViolationError, compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, MOS_TERMINAL_NAMES
from gmid_engine.lut import (AXES, tol_v_table, REASON_OFF_DECLARED, FingerSlice, SatBound, derived, finger_slice, gmb, is_slice_gap, op_point,
                             sat_threshold, slice_of_finger, vgs_for_current_density)

from ._helpers_dc_solve import Circuit, default_port_views, is_servo_branch, sense_signs
from ._helpers_lut import with_device
from .bracket_root import bracket_root
from .fixed_point import gauss_seidel
from .k_max import k_max
from .scc_newton import newton_solve
from .s2_values import (
    COORD_WRITER,
    DC_KEY,
    DC_SOLVE_WRITER,
    PATH_FIXED,
    PATH_MOS,
    PATH_RESISTOR,
    PATH_Y,
    REASON_EMPTY_WINDOW,
    REASON_NO_ROOT,
    REASON_REALIZED_FINGER_MISSING,
    REASON_SERVO_VIEW_UNRESOLVED,
    REASON_STRICT_RECHECK,
    REASON_TOL_UNDEFINED,
    REL_INPUT_DC,
    REL_INPUT_POINT,
    REL_RESISTOR,
    REL_TARGET,
    REL_VGS_GATE,
    REL_VGS_SOURCE,
    REL_WINDOW,
    SCC_BISECTION,
    SCC_GAUSS_SEIDEL,
    SCC_NEWTON,
    SEAL_BULK_REVERSE,
    SEAL_SATURATION,
    THETA_LN_IDU,
    THETA_RESISTANCE,
    THETA_Y,
    PathValue,
    SccLog,
    DeviceOp,
    FingerGeom,
    Window,
)

READS = (
    ("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "dc_column_nbrs"),
    ("device", "dc_current"), ("node", "dc_colour"), ("device", "dc_colour"), ("device", "dc_L"), ("device", "pins"), ("device", "kind"), ("device", "bulk"),
    ("device", "element_class"), ("device", "dc_coord"), ("graph", "dc_scc_order"), ("device", "dc_self_referential"),
    ("node", "port_direction"), ("node", "port_role"), ("device", "region_decl"), ("graph", "dc_current_basis"), ("graph", "views"),
)
WRITES = (("node", "dc_v"), ("node", "dc_path_values"), ("node", "dc_window"), ("device", "dc_ln_idu"), ("device", "dc_op"),
          ("device", "dc_sat_v"), ("device", "dc_finger"), ("graph", "dc_scc_log"))
_REL_MOS, _REL_RES, _REL_FIXED, _REL_Y = PATH_MOS, PATH_RESISTOR, PATH_FIXED, PATH_Y
def _is_root(w):
    """W4 뿌리 writer 인가 -- `free_window` 또는 입력 점의 뿌리(`input_point` 이고 known 없음; known 이 있으면 뿌리와 같은 전압인 짝 포트)."""
    return w.relation == REL_WINDOW or (w.relation == REL_INPUT_POINT and w.known is None)


_TARGET_OUT_OF_RANGE = "lut_target_out_of_range"       # lut CONTRACT 4.1·3.1 vgs_for_current_density·gm_id_for_target 사유 키
_TRANSIENT_LUT_REASONS = (_TARGET_OUT_OF_RANGE, "lut_axis_out_of_range")   # 반복 중 정의역 이탈(검증 바퀴가 다시 잰다)
_CURVE_UNDEFINED = "lut_curve_undefined"     # lut CONTRACT 4.1 -- VDS 정의역 하한(`vds_floor`(LUT 파생)) 아래에서만 반복 중 이탈로 본다
_VDS_AXIS, _VS_AXIS = AXES.index("VDS"), AXES.index("VS")
_BOUND_RAIL, _BOUND_VDS, _BOUND_VS = "rail", "vds_axis", "vs_axis"
_SOLVE_SELF_MEMO = "solve_self"            # LUT memo root 영역의 함수 이름 칸(1변수 풀이 재사용)
REASON_SLICE_CYCLE = "slice_cycle"                        # Rʳ 키 벡터가 이전 벡터로 돌아옴
_GS_STOPPED = "gauss_seidel_stopped"                  # SccLog.fallback[0]: GS 가 K_max 안 tol 도달 불가로 멈춤


def _inward(x, toward, a, b, axis):
    """1차식 v = a + b·x 의 구간 끝 x = (축 끝 − a)/b 를 부동소수 반올림으로 v 가 축 [axis[0], axis[-1]] 밖에 떨어지면
    `toward` 쪽으로 한 ulp 씩 옮긴다(축 끝은 정의역 안 -- 반올림 때문에 끝점 조회가 축 밖·정의역 밖이 되지 않게)."""
    while not axis[0] <= a + b * x <= axis[-1] and x != toward:
        x = math.nextafter(x, toward)
    return x


def forward_point(lut, device, kind, w_key, L, vgs, vds, vsb):
    """순방향 조회 OpPoint(IDu, gm_over_id, ...) -- 소자 슬라이스 `w_key` 의 점."""
    try:
        return op_point(lut.memo, kind, w_key, L, vgs, vds, vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "forward_point") from exc


def _vgs_of_coordinate(lut, device, kind, w_key, L, vds, vsb, ln_idu):
    """좌표 ln IDu(DEC-88)에서 VGS 크기 -- 강반전 분지 역산(lut `vgs_for_current_density`: 칸 안 Hermite 근, DEC-87)."""
    try:
        return vgs_for_current_density(lut.memo, kind, w_key, ln_idu, L, vds, vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "vgs_of_coordinate") from exc


class _Circuit(Circuit):
    """블록 한 번의 입력 묶음과 writer 식 -- 읽기 전용 공용 부분(`Circuit`)에 θ·고정 값 등 이 블록이 쓰는 상태를 더한다."""

    def __init__(self, projection):
        theta_items, fixed_values, resistor_values, lut, geometry, realized = (tuple(projection.extras) + (None, None))[:6]
        super().__init__(projection, lut=lut, linear=frozenset(m for m, r in projection.column("device", "region_decl") if r.region == REGION_TRIODE))      # `triode` 선언 소자 -- 창 경계 행이 triode 행(`region_rows`)
        self.theta = dict(theta_items)
        self.fixed = dict(fixed_values)
        self.nbrs = dict(projection.column("node", "dc_column_nbrs"))
        self.classes = dict(projection.column("device", "element_class"))
        self.current = dict(projection.column("device", "dc_current"))
        self.geometry, self.realized = geometry, realized
        self.net_colour = dict(projection.column("node", "dc_colour"))
        self.self_ref = frozenset(m for m, flag in projection.column("device", "dc_self_referential") if flag)   # 쓰기 계획 파생 S0 필드(1변수 writer)
        self.order = projection.value("graph", DC_KEY, "dc_scc_order")
        self.resistance = {n: v for n, v in resistor_values if v is not None}
        self.resistance.update({key: v for (kind, key), v in self.theta.items() if kind == THETA_RESISTANCE})
        self.ln_idu = {key: v for (kind, key), v in self.theta.items() if kind == THETA_LN_IDU}
        self.order_terms = {}
        for m in sorted(self.coord, key=lambda x: (self.device_colour.get(x, 0), x)):     # 구조 색 순서 -- 이름 치환이 항 순서(동률 tie-break)를 바꾸지 않게
            d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
            source_side, sink_side = (d, s) if self.kind_sign(self.kinds[m]) > 0 else (s, d)
            self.order_terms.setdefault(source_side, []).append((True, sink_side))
            self.order_terms.setdefault(sink_side, []).append((False, source_side))
        self.tol_cells = {}                        # (소자, VDS) -> tol_V 또는 None -- `tolerance` 의 한 평가 안 재사용

    def kvl_window(self, net, values):
        """W4 순서 창: x 에 채널이 닿는 전도 MOS 마다 VDS ≥ 0 이 되는 쪽 -- x 가 전류가 나가는 단자면
        lo ≥ V(반대 단자), 들어오는 단자면 hi ≤ V(반대 단자). 제약이 없는 쪽은 레일 전압 범위 끝."""
        terms = self.terms(net)
        lo, hi = self.lo, self.hi
        for is_lower, other in terms:
            if is_lower:
                lo = max(lo, values[other])
            else:
                hi = min(hi, values[other])
        return lo, hi, len(terms)

    def terms(self, net):
        """x 에 채널이 닿는 MOS 의 순서 제약 항 -- 입력 점 뿌리는 짝 포트에 채널이 닿는 MOS 의 항까지(두 포트가 한 점)."""
        found = list(self.order_terms.get(net, ()))
        for mate, w in self.writers.items():                          # 쓰기 계획(node.dc_writer)에서 읽는다 -- 입력 점 뿌리의 짝 포트
            if w.relation == REL_INPUT_POINT and w.known == net:
                found.extend(self.order_terms.get(mate, ()))
        return found

    def window(self, net, values):
        """W4 창 = KVL 순서 창(`kvl_window`) 하나 -- 입력 뿌리도 같다(입력 창 측정은 `icm_config`)."""
        return self.kvl_window(net, values)

    def start(self, net):
        cols = list(self.nbrs.get(net, ()))
        if not cols:
            return (self.lo + self.hi) / 2
        # 색 열이 없는 손 조립 스냅샷은 색 0 -- 이름 순으로 떨어진다(커널 컨텍스트가 만든 스냅샷은 늘 색이 있다)
        # 기둥 방향·합산 순서를 구조 색(정준 위치)으로 -- S1 기둥은 레일 이름순 방향이라 이름 치환이 부동소수 합 순서를 바꾸는 것을 막는다
        colour = self.net_colour
        canon = []
        for c in cols:
            r0, r1, pred, succ, pos = c.rails[0], c.rails[1], c.pred, c.succ, c.position
            if (colour.get(r0, 0), r0) > (colour.get(r1, 0), r1):
                r0, r1, pred, succ, pos = r1, r0, succ, pred, c.length - c.position
            canon.append(((colour.get(r0, 0), colour.get(r1, 0), colour.get(pred, 0), colour.get(succ, 0), pos, c.length),
                          r0, r1, pos, c.length))
        total = 0.0
        for _key, r0, r1, pos, length in sorted(canon, key=lambda x: x[0]):
            v0, v1 = self.rail_v[r0], self.rail_v[r1]
            total += v0 + (v1 - v0) * pos / length
        return total / len(cols)

    def transient(self, keys, exc, m, vds):
        """반복 중(시작값 둘째 단계 포함, strict=False) 현재 값을 유지할 LUT 정의역 이탈인가: `lut_axis_out_of_range`·
        `lut_target_out_of_range`, 또는 VDS 정의역 하한(`vds_floor`(LUT 파생)) 아래에서 난 `lut_curve_undefined`."""
        lut_reason = dict(exc.record.detail).get("lut_reason")
        if lut_reason in _TRANSIENT_LUT_REASONS:
            return True
        return lut_reason == _CURVE_UNDEFINED and vds < derived(self.lut.memo, "vds_floor", self.kinds[m], keys[m])

    def start_writer(self, keys, net, values):
        """시작값 둘째 단계(쓰기 계획 순서): MOS writer 노드는 writer 식을 VDS = 레일 범위 절반에서 한 번 평가한 값
        (diode·소스 추종의 고정점 근처). VSB 는 `vgs_gate`(source 를 안다)면 현재값, `vgs_source`(source 가 x 자신)면 0
        -- 체효과가 가장 작은 쪽에서 시작해 소스 추종이 레일 밖으로 튀지 않게 한다. 저항은 writer 식, W4 는 기둥
        위치 시작값 그대로. 시작값일 뿐이고 수렴값은 시작값과 무관하다(수렴 판정 = N3.6)."""
        w = self.writers[net]
        if self.self_referential(net):
            return self.solve_self(keys, net, values, strict=False)[0]
        if w.relation in (REL_VGS_GATE, REL_VGS_SOURCE):
            m = w.element
            _vds, vsb = self.vds_vsb(m, values)
            vsb = vsb if w.relation == REL_VGS_GATE else 0.0
            vds = (self.hi - self.lo) / 2
            try:
                vgs = _vgs_of_coordinate(self.lut, m, self.kinds[m], keys[m], self.L[m], vds, vsb, self.ln_idu[m])
            except SealViolationError as exc:
                if not self.transient(keys, exc, m, vds):
                    raise
                return values[net]
            sign = self.kind_sign(self.kinds[m])
            return values[w.known] + sign * vgs if w.relation == REL_VGS_GATE else values[w.known] - sign * vgs
        if w.relation == REL_RESISTOR:
            return self.update(keys, net, values)
        return values[net]

    def self_referential(self, net):
        """writer 소자의 VDS·VSB 가 x 자신을 읽는가(diode 의 gate 쓰기, 소스 추종의 source 쓰기) -- 1변수 방정식 노드. 판정은 쓰기 계획이 S0 당 한 번 쓴
        `device.dc_self_referential`(설계 40 §2.4.8)을 읽는다(소자는 노드 하나만 쓴다)."""
        w = self.writers[net]
        return w.relation in (REL_VGS_GATE, REL_VGS_SOURCE) and w.element in self.self_ref

    def _vgs_signed(self, keys, m, vds, vsb):
        """bisection 용 VGS: 목표 전류가 그 (vds, vsb) 곡선의 강반전 분지 위 범위 밖이면 부호가 정해진 무한대
        (위 = +inf: 필요한 VGS 가 격자 위, 아래 = −inf: 분지 시작 아래) -- 단조 함수의 정의역 밖 쪽을 알려 준다.
        그 밖 LUT 실패(축 밖·비단조)는 소자 이름을 붙여 그대로 낸다."""
        kind = self.kinds[m]
        w_key = keys[m]
        try:
            return vgs_for_current_density(self.lut.memo, kind, w_key, self.ln_idu[m], self.L[m], vds, vsb)
        except SealViolationError as exc:
            detail = dict(exc.record.detail)
            if detail.get("reason") != _TARGET_OUT_OF_RANGE:
                raise with_device(exc, m, "vgs_of_coordinate") from exc
            return math.inf if detail["target"] > detail["branch_max"] else -math.inf

    def solve_self(self, keys, net, values, strict=True):
        """1변수 노드 x = g(x) 를 구간 괄호 근 찾기(`bracket_root`, Brent 법)로 푼다(설계 3.4). 구간 = 레일 전압 범위 ∩ {writer 소자의 VDS·VSB 가
        LUT 축 안}(VDS·VSB 는 x 의 1차식이라 두 점에서 계수를 잰다). h(x) = x − g(x) 끝점 부호가 같으면 근 없음 ->
        `SealViolationError`(reason `no_root_in_window`, item = 구간 끝이 VDS 축(순서·포화 쪽)에서 왔으면 7, 레일·VS 축(벌크
        접합)이면 6, margin = 끝점 |h| 최솟값/tol). 수렴 판정 = bisection 과 같다(근과의 거리 ≤ tol/2 보증); 반환 반복 수 칸은 k_max(구간 폭, writer tol_V)(상한 선언).
        같은 입력이면 LUT memo 에서 재사용한다(h 가 그 입력만의 함수). 끝으로
        writer 식을 한 번 더 적용한 값 g(x)(= x − h(x))가 유한하고 구간 안이면 그것을 쓴다(근 근처 수축 |g'| < 1 이라 오차가
        |g'| 배로 준다 -- 봉인 2 가 같은 tol 로 재므로 구간 폭 = tol 만으로는 경계에 걸린다). 반환 (x, 반복 수, tol).

        `strict=False`(다변수 SCC 의 Gauss-Seidel 갱신 중): 근이 없거나 구간이 비면 실패 대신 |h| 가 작은 구간 끝(구간이
        비면 두 끝 가운데)을 돌려준다 -- 이웃 노드의 과도 반복값 때문에 생긴 일시적 정의역 이탈로 수렴할 θ 를 거부하지
        않기 위한 반복 중 투영이다. 수렴 뒤 그 SCC 의 1변수 노드는 `strict=True` 로 다시 풀어 근이 실제로 있는지 확인한다
        (없으면 위 실패) -- 최종값에는 투영이 남지 않는다."""
        w = self.writers[net]
        m = w.element
        kind = self.kinds[m]
        grids = self.lut.memo.lut.slice_map[(kind, keys[m])].grids
        sign = self.kind_sign(kind)
        known = values[w.known]

        def channel(x):
            trial = dict(values)
            trial[net] = x
            return self.vds_vsb(m, trial)

        (vds0, vsb0), (vds1, vsb1) = channel(0.0), channel(1.0)
        bounds = [(self.lo, self.hi, _BOUND_RAIL)]
        vds_domain = (derived(self.lut.memo, "vds_floor", kind, keys[m]), grids[_VDS_AXIS][-1])
        for a, b, axis, label in ((vds0, vds1 - vds0, vds_domain, _BOUND_VDS),
                                  (vsb0, vsb1 - vsb0, grids[_VS_AXIS], _BOUND_VS)):
            if b != 0:
                ends = sorted(((axis[0] - a) / b, (axis[-1] - a) / b))
                bounds.append((_inward(ends[0], ends[-1], a, b, axis), _inward(ends[-1], ends[0], a, b, axis), label))
        lo, lo_from = max((b[0], b[2]) for b in bounds)
        hi, hi_from = min((b[1], b[2]) for b in bounds)

        def h(x):
            vds, vsb = vds0 + (vds1 - vds0) * x, vsb0 + (vsb1 - vsb0) * x
            vgs = self._vgs_signed(keys, m, vds, vsb)
            target = known + sign * vgs if w.relation == REL_VGS_GATE else known - sign * vgs
            return x - target

        if lo > hi and not strict:
            return values[net], 0, None                    # SD-1: 빈 구간 = 현재 반복값 유지(가운데 값 대체 없음)
        if lo > hi:
            raise SealViolationError(devices=(m,), detail={"item": SEAL_SATURATION, "reason": REASON_NO_ROOT,
                                                           "node": net, "lo": lo, "hi": hi,
                                                           "bounds": (lo_from, hi_from)})
        middle = dict(values)
        middle[net] = (lo + hi) / 2
        tol = self.tolerance(keys, (m,), middle)

        def solved():
            root, h_a, h_b = bracket_root(h, lo, hi, tol)
            if root is not None:
                polished = root - h(root)
                if math.isfinite(polished) and lo <= polished <= hi:
                    root = polished
            return root, h_a, h_b

        # h 는 (소자 종류·L·ln IDu·writer 관계·known 값·VDS/VSB 의 x 1차식 계수·구간·tol) 만의 함수 -- 같은 입력이면 풀이를 다시
        # 하지 않는다(GS 반복·strict 재검증·FD 형제·탐색 평가 사이 중복). LUT memo root 영역(상한 있는 LRU).
        key = (kind, keys[m], self.L[m], self.ln_idu[m], w.relation, known, vds0, vds1, vsb0, vsb1, lo, hi, tol)
        x, h_lo, h_hi = self.lut.memo.lookup("root", _SOLVE_SELF_MEMO, key, solved)
        if x is None and not strict:
            return values[net], 0, tol                     # SD-1: 근 없음 = 현재 반복값 유지(작은 |h| 끝점 대체 없음)
        if x is None:
            finite = [abs(v) for v in (h_lo, h_hi) if math.isfinite(v)]
            item = SEAL_SATURATION if _BOUND_VDS in (lo_from, hi_from) else SEAL_BULK_REVERSE
            raise SealViolationError(devices=(m,), margin=min(finite) / tol if finite else None,
                                     detail={"item": item, "reason": REASON_NO_ROOT, "node": net, "lo": lo, "hi": hi,
                                             "h_lo": h_lo, "h_hi": h_hi, "bounds": (lo_from, hi_from)})
        return x, k_max(hi - lo, tol) if hi > lo else 1, tol

    def reference_key(self, m):
        """종속 소자의 시작 키 = 그 kind 기준 폭 슬라이스 키(`cap_map[kind].w_key`, LUT 선언만의 함수). 없으면 `slice_missing`."""
        key = self.lut.memo.lut.cap_map[self.kinds[m]].w_key
        if key is None:
            raise SealViolationError(devices=(m,), detail={"reason": "slice_missing", "kind": self.kinds[m], "L": self.L[m], "why": "no_w_hi", "excluded": ()})
        return key

    def pick_writer(self, m):
        """쓰기 소자 m 의 (m, 슬라이스 폭, 키): W = ID·L/exp(θ ln IDu) 를 상수로 `finger_slice`(반복 없음)."""
        width = self.current[m] * self.L[m] / math.exp(self.ln_idu[m])
        try:
            return finger_slice(self.lut.memo.lut, self.kinds[m], self.L[m], lambda _key: width)
        except SealViolationError as exc:
            raise with_device(exc, m, "finger_slice") from exc

    def pick_dependent(self, m, values):
        """종속 소자 m 의 선택: 후보 슬라이스 s 마다 W(s) = ID·L/IDu_s(노드 점)(조회 불능 사유 다섯은 후보 제외, 그 밖은 그대로)."""
        kind, current, length = self.kinds[m], self.current[m], self.L[m]
        vgs, vds, vsb = self.mos_point(m, values)

        def w_of(key):
            try:
                idu = op_point(self.lut.memo, kind, key, length, vgs, vds, vsb).IDu
            except SealViolationError as exc:
                if is_slice_gap(exc):
                    return None
                raise
            return current * length / idu if idu > 0 and math.isfinite(idu) else None

        try:
            return finger_slice(self.lut.memo.lut, kind, length, w_of)
        except SealViolationError as exc:
            raise with_device(exc, m, "finger_slice") from exc

    def tol_cell(self, keys, m, vds):
        """소자 m 의 슬라이스(`keys[m]`) (L 앵커, VDS) 셀 id_equivalent tol_V -- 정의된 셀이 없으면 None."""
        try:
            return tol_v_table(self.lut.memo, self.kinds[m], keys[m]).at(self.L[m], vds, "id_equivalent")
        except SealViolationError as exc:
            raise with_device(exc, m, "tol_v_cell") from exc

    def has_channel_values(self, m, values):
        d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
        return d in values and s in values and self.bulk[m] in values

    def update(self, keys, net, values, strict=True):
        """노드 writer 식. `strict=False`(다변수 SCC Gauss-Seidel 반복 중): 1변수 노드는 투영 bisection, MOS writer 의 LUT
        정의역 이탈(`lut_axis_out_of_range`·`lut_target_out_of_range`·VDS 정의역 하한 아래의 `lut_curve_undefined` -- 이웃의
        과도 반복값 때문)과 W4 창이 빈 경우는 실패
        대신 현재 값을 그대로 둔다. 수렴 뒤 `strict=True` 검증 한 바퀴가 같은 식을 다시 재므로 최종값에 남지 않는다."""
        w = self.writers[net]
        if self.self_referential(net):
            return self.solve_self(keys, net, values, strict=strict)[0]
        if w.relation in (REL_VGS_GATE, REL_VGS_SOURCE):
            m = w.element
            vds, vsb = self.vds_vsb(m, values)
            try:
                vgs = _vgs_of_coordinate(self.lut, m, self.kinds[m], keys[m], self.L[m], vds, vsb, self.ln_idu[m])
            except SealViolationError as exc:
                if strict or not self.transient(keys, exc, m, vds):
                    raise
                return values[net]
            sign = self.kind_sign(self.kinds[m])
            return values[w.known] + sign * vgs if w.relation == REL_VGS_GATE else values[w.known] - sign * vgs
        if w.relation == REL_RESISTOR:
            return values[w.known] + self.drop(w.element, w.known, net)
        if w.relation == REL_INPUT_POINT and w.known is not None:      # 입력 점의 짝 포트 -- 뿌리와 같은 전압(KVL)
            return values[w.known]
        lo, hi, ncols = self.window(net, values)
        if lo > hi and not strict:
            return values[net]
        if lo > hi:
            raise SealViolationError(devices=(), margin=None,
                                     detail={"item": SEAL_SATURATION, "reason": REASON_EMPTY_WINDOW, "node": net,
                                             "lo": lo, "hi": hi, "constraints": ncols})
        return lo + self.theta[(THETA_Y, w.y_key)] * (hi - lo)

    def writer_grad(self, keys, net, values):
        """writer 식 값 g 와 노드전압에 대한 편미분 {노드: ∂g/∂V}(Newton 야코비안 행). 1변수 노드도 bisection 이 아니라 식
        그대로(x 를 읽는 VDS·VSB 항이 야코비안 대각에 들어간다).
        * MOS writer(부호 s, gate 쓰기 σ = +1 / source 쓰기 σ = −1): g = V(known) + s·σ·VGS(ln IDu, VDS, VSB). VGS 는 lnID(VGS,
          VDS, VSB) = 목표의 음함수라 ∂VGS/∂VDS = −(gds/ID)/(gm/ID) = −1/(gm/gds), ∂VGS/∂VSB = (gmb/ID)/(gm/ID) = gmb/gm --
          값은 역산 VGS 점의 lut `op_point`(gm_over_id·gm_gds, Hermite 미분과 같은 곡면)와 lut `gmb`(같은 점, 폭 w_m)에서.
          vds = s(V(d) − V(s)), vsb = s(V(s) − V(b)) 사슬: ∂g/∂V(known) += 1, ∂g/∂V(d) += σ·∂VGS/∂VDS,
          ∂g/∂V(s) += σ·(∂VGS/∂VSB − ∂VGS/∂VDS), ∂g/∂V(b) += −σ·∂VGS/∂VSB(같은 노드는 더한다).
        * 저항 강하: g = V(known) + Δ, ∂g/∂V(known) = 1. W4: g = lo + y(hi − lo), lo 를 정한 이웃 노드에 1 − y, hi 를 정한
          이웃 노드에 y(레일 끝이면 항 없음). 빈 창이면 `SealViolationError`(empty_window) -- 부르는 쪽(`newton_system`)이 정의역 밖으로 본다."""
        w = self.writers[net]
        if w.relation in (REL_VGS_GATE, REL_VGS_SOURCE):
            m = w.element
            kind = self.kinds[m]
            d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
            vds, vsb = self.vds_vsb(m, values)
            vgs = _vgs_of_coordinate(self.lut, m, kind, keys[m], self.L[m], vds, vsb, self.ln_idu[m])
            w_key = keys[m]
            point = forward_point(self.lut, m, kind, w_key, self.L[m], vgs, vds, vsb)
            w_m = self.lut.memo.lut.slice_map[(kind, w_key)].w_m
            try:
                gmb_w = gmb(self.lut.memo, kind, w_key, self.L[m], vgs, vds, vsb)
            except SealViolationError as exc:
                raise with_device(exc, m, "gmb") from exc
            gm_w = point.gm_over_id * point.IDu * w_m / self.L[m]
            dvgs_dvds = -1 / point.gm_gds
            dvgs_dvsb = gmb_w / gm_w
            sigma = 1 if w.relation == REL_VGS_GATE else -1
            sign = self.kind_sign(kind)
            grad = {}
            for node, value in ((w.known, 1.0), (d, sigma * dvgs_dvds), (s, sigma * (dvgs_dvsb - dvgs_dvds)),
                                (self.bulk[m], -sigma * dvgs_dvsb)):
                grad[node] = grad.get(node, 0.0) + value
            return values[w.known] + sign * sigma * vgs, grad
        if w.relation == REL_RESISTOR:
            return values[w.known] + self.drop(w.element, w.known, net), {w.known: 1.0}
        if w.relation == REL_INPUT_POINT and w.known is not None:
            return values[w.known], {w.known: 1.0}
        terms = self.terms(net)
        lo, hi, lo_node, hi_node = self.lo, self.hi, None, None
        for is_lower, other in terms:
            if is_lower and values[other] > lo:
                lo, lo_node = values[other], other
            elif not is_lower and values[other] < hi:
                hi, hi_node = values[other], other
        if lo > hi:
            raise SealViolationError(devices=(), margin=None,
                                     detail={"item": SEAL_SATURATION, "reason": REASON_EMPTY_WINDOW, "node": net,
                                             "lo": lo, "hi": hi, "constraints": len(terms)})
        y = self.theta[(THETA_Y, w.y_key)]
        grad = {}
        if lo_node is not None:
            grad[lo_node] = grad.get(lo_node, 0.0) + 1 - y
        if hi_node is not None:
            grad[hi_node] = grad.get(hi_node, 0.0) + y
        return lo + y * (hi - lo), grad

    def newton_system(self, keys, nodes, values):
        """SCC 잔차 r_i = V_i − g_i(V) 와 야코비안 J = I − ∂g/∂V(SCC 노드 열만 -- 바깥 노드는 이미 확정된 상수).
        한 노드라도 정의역 밖(LUT 조회 실패·빈 창 = `SealViolationError`)이면 None(선 탐색이 α 를 줄인다)."""
        index = {n: i for i, n in enumerate(nodes)}
        residuals = []
        rows = []
        for n in nodes:
            try:
                g, grad = self.writer_grad(keys, n, values)
            except SealViolationError:
                return None
            residuals.append(values[n] - g)
            row = [0.0] * len(nodes)
            row[index[n]] = 1.0
            for other, derivative in grad.items():
                if other in index:
                    row[index[other]] -= derivative
            rows.append(tuple(row))
        return tuple(residuals), tuple(rows)

    def drop(self, r, near, far):
        """V(far) − V(near) 를 저항 r 의 전류(t0 -> t1)와 저항값으로."""
        i = self.current[r]
        if i == 0:
            return 0.0
        t0 = self.pins[r][min(self.pins[r])]
        v = i * self.resistance[r]
        return -v if near == t0 else v

    def tolerance(self, keys, devices, values):
        tols = []
        for m in devices:
            vds, _vsb = self.vds_vsb(m, values)
            key = (m, keys[m], vds)                   # 한 평가 안에서 같은 (소자, 슬라이스, VDS) 셀 조회는 한 번(L·kind 는 소자마다 고정)
            if key not in self.tol_cells:
                self.tol_cells[key] = self.tol_cell(keys, m, vds)
            tols.append(self.tol_cells[key])
        undefined = tuple(sorted(m for m, t in zip(devices, tols) if t is None))
        if not tols or undefined:                     # 집계 항에 None 이 하나라도 있으면 집계 = None (계획 N3.6 표 10행) -- 정의된 셀만으로 내지 않는다
            raise SealViolationError(devices=undefined, detail={"reason": REASON_TOL_UNDEFINED})   # 기록 devices = tol 이 None 인 원인 소자(소자 없음이면 빈 tuple)
        return min(tols)


def _strict_recheck(c, keys, entry, values, tol):
    """검증 바퀴: 수렴점에서 SCC 노드마다 writer 식을 strict 로 다시 잰다(1변수는 bisection 전체). 정의역 밖이면 그
    `SealViolationError` 그대로, |새 값 − 수렴값| > tol 이면 `NonconvergentError`(reason `strict_recheck_residual`)."""
    for net in entry.nodes:
        residual = abs(c.update(keys, net, values) - values[net])
        if residual > tol:
            raise NonconvergentError(devices=entry.devices, margin=residual / tol,
                                     detail={"node": net, "reason": REASON_STRICT_RECHECK, "nodes": entry.nodes})


def _solve(c, keys):
    """쓰기 계획 위상 순서로 SCC 를 풀어 (노드전압, SccLog 열, Rʳ 소자 집합)을 낸다 -- 현재 `c.theta` 한 벌에 대한 풀이 한 번.
    Rʳ 소자 = writer 없는 순환 SCC 의 수렴 허용오차 셀을 내는 종속 MOS(이 풀이의 지역 값)."""
    values = dict(c.rail_v)
    r_dep = set()
    for net, w in c.writers.items():
        if w.relation in (REL_TARGET, REL_INPUT_DC):
            values[net] = float(c.fixed[net])
    logs = []
    for entry in c.order:
        entry_devices = tuple(sorted(entry.devices, key=lambda m: (c.device_colour.get(m, 0), m)))      # 구조 색 순서(이름이 처음 실패할 소자를 정하지 않게)
        if not entry.cyclic:
            (net,) = entry.nodes
            values[net] = c.update(keys, net, values)
            logs.append(SccLog(entry.index, entry.nodes, 1, (), None, None))
            continue
        for net in entry.nodes:
            values[net] = c.start(net)
        if len(entry.nodes) == 1:
            (net,) = entry.nodes
            values[net], k, tol = c.solve_self(keys, net, values)
            logs.append(SccLog(entry.index, entry.nodes, k, (), tol, k, SCC_BISECTION))
            continue
        positional = dict(values)
        for net in entry.nodes:
            values[net] = c.start_writer(keys, net, values)
        writers = tuple(sorted({c.writers[n].element for n in entry.nodes
                                if c.writers[n].relation in (REL_VGS_GATE, REL_VGS_SOURCE)},
                               key=lambda m: (c.device_colour.get(m, 0), m)))              # 구조 색 순서 -- 이름이 처음 실패할 소자를 정하지 않게
        devices = writers or tuple(m for m in entry_devices if c.has_channel_values(m, values))
        if not writers:
            # Rʳ -- 수렴 허용오차 셀을 종속 소자가 내는 SCC. 다른 노드의 writer 인 소자는 키가 쓰기 소자 선택(상수 W)으로 정해져 있고
            # 그 키가 자기 노드 writer 식에 들므로 되풀이로 바꾸지 않는다(종속 소자만 Rʳ).
            r_dep.update(m for m in devices if c.coord[m].role != COORD_WRITER)

        def tolerance(v, devs=devices):
            return c.tolerance(keys, devs, v)

        method, fallback, solved, seal_failure = SCC_GAUSS_SEIDEL, None, None, None
        try:
            solved, (k, deltas, tol, limit) = gauss_seidel(
                entry.nodes, values, lambda n, v: c.update(keys, n, v, strict=False), tolerance, c.hi - c.lo, entry_devices)
            _strict_recheck(c, keys, entry, solved, tol)
        except NonconvergentError as exc:                  # Gauss-Seidel 이 K_max 안에 tol 에 닿지 못함(측정한 q 로 판정)
            stopped = dict(exc.record.detail)              # 또는 수렴 판정 뒤 strict 검증 잔차 > tol
            gs_deltas = stopped.get("deltas", deltas if solved is not None else ())
            ratio = gs_deltas[-1] / gs_deltas[-2] if len(gs_deltas) > 1 and gs_deltas[-2] > 0 else None
            fallback = (stopped.get("reason", _GS_STOPPED), ratio, tuple(gs_deltas))
        except SealViolationError as exc:                  # 수렴 판정 뒤 strict 검증에서 writer 식이 정의역 밖 -- 반복 중
            if solved is None:                             # 수렴 전(반복 중 tol 미정의·정의역 밖 LUT 실패): Gauss-Seidel 값이 없다 -> 그대로 낸다
                raise
            fallback = (dict(exc.record.detail).get("reason"), None, tuple(deltas))   # 투영으로 멈춘 노드가 있었다
            seal_failure = exc
        if fallback is not None:
            method = SCC_NEWTON
            starts = (values, positional) if solved is None else (values, solved, positional)

            def system(v, nodes=entry.nodes):
                return c.newton_system(keys, nodes, v)

            start = next((s for s in starts if system(s) is not None), values)
            try:
                solved, (k, deltas, tol, limit) = newton_solve(entry.nodes, start, system, tolerance, c.hi - c.lo,
                                                               entry_devices)
            except NonconvergentError as newton_exc:       # Newton 도 해를 못 찾았다 -- GS 수렴점에서 잰 strict 검증 위반이
                if seal_failure is None:                   # 있었으면 그 사실(봉인 위반)을 낸다(strict 검증 규약 불변)
                    raise
                raise seal_failure from newton_exc
            _strict_recheck(c, keys, entry, solved, tol)
        values = solved
        logs.append(SccLog(entry.index, entry.nodes, k, deltas, tol, limit, method, fallback))
    return values, tuple(logs), r_dep


def _windows(c, values):
    """`node.dc_window` -- W4 뿌리 항목마다 KVL 순서 창 하나(`Window(lo, hi, constraints)`, 상태·`tol_v` 없음)."""
    out = {}
    for net, w in c.writers.items():
        if _is_root(w):
            lo, hi, ncols = c.window(net, values)
            out[net] = Window(lo, hi, ncols)
    return out


def _rounds(c, keys):
    """노드 풀이(+ Rʳ 키 되풀이): (values, logs, 풀이 횟수, {Rʳ 소자: FingerSlice}). 키 벡터가 직전과 같으면 수렴, 이전 벡터로 돌아가면 `slice_cycle`."""
    seen = []
    rounds = 0
    while True:
        values, logs, r_dep = _solve(c, keys)
        rounds += 1
        devices = sorted(r_dep)
        if not devices:
            return values, logs, rounds, {}
        now = tuple((m, keys[m]) for m in devices)
        picks = {m: c.pick_dependent(m, values) for m in devices}
        after = tuple((m, picks[m].w_key) for m in devices)
        if after == now:
            return values, logs, rounds, picks
        seen.append(now)
        if after in seen:
            raise SealViolationError(devices=tuple(devices), detail={"reason": REASON_SLICE_CYCLE, "cycle": tuple(seen) + (after,)})
        keys = {**keys, **{m: picks[m].w_key for m in devices}}


def _slice_pick(c, m, count, finger_w):
    """소자 m 의 입력 손가락 (m, w_s) -> `FingerSlice`: 선택 함수 없이 키만 `slice_of_finger`(슬라이스가 아닌 폭이면 `slice_missing`)."""
    try:
        return FingerSlice(count, finger_w, slice_of_finger(c.lut.memo.lut, c.kinds[m], c.L[m], finger_w))
    except SealViolationError as exc:
        raise with_device(exc, m, "slice_of_finger") from exc


def _reference_pick(c, m, fingers):
    """기준 스냅샷 `device.dc_finger` 의 소자 m 행 -> `FingerSlice`. 행이 없으면 `realized_finger_missing`."""
    found = fingers.get(m)
    if found is None:
        raise SealViolationError(devices=(m,), detail={"reason": REASON_REALIZED_FINGER_MISSING})
    return _slice_pick(c, m, found.m, found.w_f_m)


def _realized_picks(c, ref):
    """실현 평가 입력: 소자마다 탐색 스냅샷 `device.dc_finger` 의 (m, w_s) -> (`FingerSlice`, W' = m·w_s). 선택 함수는 부르지 않는다(입력 값이고 키만 `slice_of_finger`).
    그 소자 행이 없으면 `realized_finger_missing`, 슬라이스가 아닌 폭이면 `slice_missing`."""
    fingers = dict(ref.column("device", "dc_finger"))
    picks = {m: _reference_pick(c, m, fingers) for m in sorted(c.coord)}
    return picks, {m: p.m * p.w_f_m for m, p in picks.items()}


def _layout_picks(c):
    """레이아웃 뒤 평가 입력: 소자마다 (`FingerSlice`, W') -- 입력 손가락(`RealizedGeometry.input_fingers`: 배치 소자 = `layout_ref` (nf, finger_w), 요청 대기 소자 = `w_request` 의 요청
    손가락 행)을 그대로 쓴다(선택 함수 호출 0, 요청 W 로 다시 고르지 않음 -- A-62 D5; 키만 `slice_of_finger`). W' = nf·finger_w. 입력 손가락 행이 없는 소자(배치도 요청도 아님)는
    `realized_finger_missing`(사이징 점 행을 읽지 않는다)."""
    given = c.geometry.input_fingers
    picks = {}
    for m in sorted(c.coord):
        row = given.get(m)
        if row is None:
            raise SealViolationError(devices=(m,), detail={"reason": REASON_REALIZED_FINGER_MISSING})
        picks[m] = _slice_pick(c, m, *row)
    return picks, {m: p.m * p.w_f_m for m, p in picks.items()}


def _mos_flow(c, keys, m, v, width):
    """MOS m 의 전도 전류 I = IDu·W'/L 과 단자 넷 전압에 대한 편미분 {넷: ∂I/∂V}(LUT 순방향 IDu·gm/ID·gm/gds, lut `gmb`; 같은 점의 한 곡면)."""
    kind, key, length = c.kinds[m], keys[m], c.L[m]
    vgs, vds, vsb = c.mos_point(m, v)
    point = forward_point(c.lut, m, kind, key, length, vgs, vds, vsb)
    scale = width / length
    current = point.IDu * scale
    gm = point.gm_over_id * current
    gds = gm / point.gm_gds
    try:
        gmb_slice = gmb(c.lut.memo, kind, key, length, vgs, vds, vsb)
    except SealViolationError as exc:
        raise with_device(exc, m, "gmb") from exc
    gmb_w = gmb_slice * width / c.lut.memo.lut.slice_map[(kind, key)].w_m
    sign = c.kind_sign(kind)
    d, g, s = (c.pins[m][t] for t in MOS_TERMINAL_NAMES)
    out = {}
    for net, value in ((g, sign * gm), (d, sign * gds), (s, -sign * (gm + gds + gmb_w)), (c.bulk[m], sign * gmb_w)):
        out[net] = out.get(net, 0.0) + value
    return current, out, gm


_VID = "\0input_difference"                    # 입력 차 미지수의 풀이 변수 이름(넷 이름과 겹치지 않는다)


def _kcl_system(c, keys, ends, widths, free, inputs, excite, sense, ref_v):
    """실현 평가·레이아웃 뒤 평가 KCL 계 `(full, system)` -- W'·바이어스(고정 노드) 고정, 미지수 = 입력 외 KCL 노드 전압. servo 갈래(`sense` 있음)는 입력 공통모드 고정 + 입력 차 하나(`_VID`)를
    더한 미지수와 출력 묶음 행(감지 넷의 부호 합 = 탐색 점 값)을 더하고, 입력 고정 갈래(`sense` 비어 있음)는 입력을 기준 스냅샷 값에 고정하고 노드 KCL 행만 둔다(미지수 = 행).
    KCL 은 봉인 3 과 같은 식: MOS = 순방향 LUT IDu·W'/L, 저항 = 전압차/R, 이상 전류원 = `device.dc_current`. 행은 노드의 gm 로 나눠
    전압 꼴로 맞춘다(봉인 3 의 tol_I = tol_V·gm 과 같은 척도; 척도는 시작점에서 한 번 정한다). `full(x)` = 풀이 변수 -> 전 넷 전압, `system(x)` = (잔차, 야코비안) 또는 None(정의역 밖)."""
    servo = bool(sense)
    free = tuple(free)
    base_in = {n: ref_v[n] for n in inputs}
    fixed = {n: v for n, v in ref_v.items() if n not in free and n not in base_in}
    target = sum(sign * ref_v[n] for n, sign in sense)
    index = {n: i for i, n in enumerate(free)}
    size = len(free)
    scale = []                                      # 시작점에서 한 번 채운다(행 척도 -- 상수 배라 근을 바꾸지 않는다)

    def full(x):
        v = dict(c.rail_v)
        v.update(fixed)
        for n in free:
            v[n] = x[n]
        for n in inputs:
            v[n] = base_in[n] + x[_VID] * excite.get(n, 0.0) if servo else base_in[n]
        return v

    def system(x):
        v = full(x)
        res = [0.0] * size
        jac = [[0.0] * (size + 1) for _ in range(size)]            # servo 갈래 마지막 열 = 입력 차 미지수
        gains = [0.0] * size
        try:
            for name, a, b in ends:
                cls = c.classes[name]
                if cls == ELEMENT_MOS:
                    current, deriv, gm = _mos_flow(c, keys, name, v, widths[name])
                elif cls == ELEMENT_PASSIVE:
                    r = c.resistance[name]
                    current, deriv, gm = (v[a] - v[b]) / r, ({a: 1.0 / r, b: -1.0 / r} if a != b else {}), 1.0 / r
                else:
                    current, deriv, gm = c.current[name], {}, 0.0
                for net, sign in ((a, 1.0), (b, -1.0)):
                    i = index.get(net)
                    if i is None:
                        continue
                    res[i] += sign * current
                    gains[i] = max(gains[i], gm)
                    for t, d in deriv.items():
                        j = index.get(t)
                        if j is not None:
                            jac[i][j] += sign * d
                        elif t in excite:
                            jac[i][size] += sign * d * excite[t]
        except SealViolationError:
            return None
        if not scale:
            scale.extend(g if g > 0 else 1.0 for g in gains)
        residuals = [res[i] / scale[i] for i in range(size)]
        rows = [[value / scale[i] for value in jac[i]] for i in range(size)]
        if not servo:
            return tuple(residuals), tuple(tuple(r[:size]) for r in rows)
        sense_row = [0.0] * (size + 1)
        value = -target
        for n, sign in sense:
            value += sign * v[n]
            if n in index:
                sense_row[index[n]] += sign
        residuals.append(value)
        rows.append(sense_row)
        return tuple(residuals), tuple(tuple(r) for r in rows)

    return full, system


def _kcl_solve(c, keys, projection, ref, widths):
    """W' 고정 KCL 재풀이: (값 {넷: V}, SccLog). 갈래는 기준 스냅샷의 피벗 판정 `graph.icm_config.config` 가 정한다.
    servo: 입력 포트는 기본 포트 뷰 여기 가중 e 로 한 미지수 Δ 만큼 움직이고(공통모드 고정) 감지 합은 기준 점 값에 묶인다.
    입력 고정(판정 불능 None·`as_is_single_input`): 입력을 기준 점 값에 고정하고 출력·나머지 KCL 노드를 푼다(출력 묶음 행·입력 차 미지수 없음).
    푼 노드 전압이 레일 범위 밖이면 레일 안 근이 없는 점이라 `no_root_in_window`(item 7, bounds = rail)."""
    ref_v = dict(ref.column("node", "dc_v"))
    directions = dict(projection.column("node", "port_direction"))
    inputs = tuple(sorted(input_port_nets(directions.items())))
    servo = is_servo_branch(ref)
    sense, excite = (), {}
    if servo:
        views = default_port_views(projection, directions)
        found = sense_signs(views[0], dict(projection.column("node", "port_role"))) if len(views) == 1 else None
        if found is None or not inputs:
            raise SealViolationError(devices=(), detail={"reason": REASON_SERVO_VIEW_UNRESOLVED, "default_views": len(views)})
        sense, excite = tuple(found), dict(views[0].excite)
    basis = projection.value("graph", DC_KEY, "dc_current_basis")
    flow_nets = {net for _name, a, b in basis.ends for net in (a, b)}
    free = sorted((n for n in flow_nets if n not in c.rail_v and n not in inputs),         # 고정 넷 = 레일 ∪ 입력 포트뿐 -- spec 목표 넷(W3)은 KCL 미지수
                  key=lambda n: (c.net_colour.get(n, 0), n))
    full, system = _kcl_system(c, keys, tuple(basis.ends), widths, free, inputs, excite, sense, ref_v)
    nodes = tuple(free) + ((_VID,) if servo else ())
    start = {n: ref_v[n] for n in free}
    if servo:
        start[_VID] = 0.0
    devices = tuple(sorted(c.coord))

    def tolerance(x):
        return c.tolerance(keys, devices, full(x))

    if not nodes:                                   # 입력 고정 갈래에 풀 노드가 없다(모든 KCL 노드가 입력·고정) -- 행이 없어 기준 점 값 그대로
        return full({}), SccLog(0, (), 0, (), None, None, SCC_NEWTON)
    solved, (k, norms, tol, limit) = newton_solve(nodes, start, system, tolerance, c.hi - c.lo, devices)
    values = full(solved)
    for n in free:
        if not c.lo - tol <= values[n] <= c.hi + tol:
            raise SealViolationError(devices=devices, margin=None,
                                     detail={"item": SEAL_SATURATION, "reason": REASON_NO_ROOT, "node": n, "lo": c.lo, "hi": c.hi,
                                             "bounds": (_BOUND_RAIL, _BOUND_RAIL)})
    return values, SccLog(0, tuple(free), k, tuple(norms), tol, limit, SCC_NEWTON)


def _resolved(c, projection):
    """실현 평가(`RealizedFinger`)·레이아웃 뒤 평가(`geometry` + 기준 스냅샷 `RealizedFinger`)의 같은 재풀이: (값, SccLog 열, 풀이 수, {소자: FingerSlice}, {소자: W'}).
    입력 손가락만 다르다 -- 실현 평가는 기준 스냅샷 `dc_finger` 의 (m, w_s), 레이아웃 뒤는 배치 (nf, finger_w)·요청 W·대기 소자의 기준 스냅샷 `dc_finger`.
    풀이는 W'·바이어스 고정 KCL(`_kcl_solve`) 하나이고 노드 재풀이 없는 갈래는 없다."""
    ref = c.realized.search_ref
    picks, widths = _realized_picks(c, ref) if c.geometry is None else _layout_picks(c)
    keys = {m: p.w_key for m, p in picks.items()}
    values, log = _kcl_solve(c, keys, projection, ref, widths)
    return values, (log,), 1, picks, widths


def _outputs(c, projection, values, logs, rounds, picks, widths=None):
    """노드 풀이 결과 `values` 와 소자 선택 `picks` 로 필드를 낸다 -- 탐색 평가와 재풀이 평가(실현 평가·레이아웃 뒤 평가, `widths` = {소자: W'})의 조립이다."""
    realized = c.realized is not None
    requested = {} if c.geometry is None or realized else dict(c.geometry.w_request)      # 사이징 호출 계약 w_request(요청 총 폭 W) 뿐 -- 레이아웃 뒤는 widths 가 W'
    ln_idu, ops, sat, fingers = {}, {}, {}, {}
    for m, coord in c.coord.items():
        kind, key = c.kinds[m], picks[m].w_key
        vgs, vds, vsb = c.mos_point(m, values)
        point = forward_point(c.lut, m, kind, key, c.L[m], vgs, vds, vsb)
        pick = picks[m]
        if realized:                                   # W' 고정 재풀이: 전류 I' = IDu·W'/L (전류밀도 = I'·L/W' = 순방향 IDu), 잔차 0
            ln_idu[m] = math.log(point.IDu)
            width = widths[m]
            ops[m] = DeviceOp(kind, point.IDu * width / c.L[m], ln_idu[m], point.gm_over_id, c.L[m], width, vgs, vds, vsb, key, point.IDu)
            fingers[m] = FingerGeom(pick.m, pick.w_f_m, 0.0)          # 그 평가가 쓴 입력 손가락(실현 평가 = 탐색 행, 레이아웃 뒤 = 배치·요청 행)
        else:
            ln_idu[m] = c.ln_idu[m] if coord.role == COORD_WRITER else math.log(point.IDu)
            free_width = c.current[m] * c.L[m] / math.exp(ln_idu[m])
            width = requested[m] if m in requested else free_width
            ops[m] = DeviceOp(kind, c.current[m], ln_idu[m], point.gm_over_id, c.L[m], width, vgs, vds, vsb, key, point.IDu)
            fingers[m] = FingerGeom(pick.m, pick.w_f_m, pick.m * pick.w_f_m / free_width - 1.0)
        try:
            sat[m] = sat_threshold(c.lut.memo, kind, key, c.L[m], vgs, vds, vsb)
        except SealViolationError as exc:                # 값 없음 사유가 아닌 LUT 실패는 소자 이름을 붙여 낸다(fail-closed)
            raise with_device(exc, m, "sat_threshold") from exc
    for m, region in projection.column("device", "region_decl"):       # `off` 선언 소자는 동작점(dc_op)이 없다 -- 값 없이 사유만
        if region.region == REGION_OFF:
            sat[m] = SatBound(None, None, REASON_OFF_DECLARED)
    paths = {net: [] for net in c.writers}
    for m in ln_idu:
        d, g, s = (c.pins[m][t] for t in MOS_TERMINAL_NAMES)
        _vgs, vds, vsb = c.mos_point(m, values)
        vgs = _vgs_of_coordinate(c.lut, m, c.kinds[m], picks[m].w_key, c.L[m], vds, vsb, ln_idu[m])
        sign = c.kind_sign(c.kinds[m])
        paths[g].append(PathValue((_REL_MOS, m), values[s] + sign * vgs))
        paths[s].append(PathValue((_REL_MOS, m), values[g] - sign * vgs))
    for net, w in c.writers.items():
        if w.relation == REL_RESISTOR:
            far_from_near = values[net] - values[w.known] if realized else c.drop(w.element, w.known, net)      # 실현 평가: 저항 전류는 KCL 의 전압차/R 이라 강하가 노드 전압 그 자체
            paths[net].append(PathValue((_REL_RES, w.element), values[w.known] + far_from_near))
            paths[w.known].append(PathValue((_REL_RES, w.element), values[net] - far_from_near))
        elif _is_root(w):
            paths[net].append(PathValue((_REL_Y, w.y_key), values[net]))
        elif w.relation not in (REL_VGS_GATE, REL_VGS_SOURCE):
            paths[net].append(PathValue((_REL_FIXED, w.relation), values[net]))
    return {
        ("node", "dc_v"): {net: v for net, v in values.items() if net not in c.rail_v},
        ("node", "dc_path_values"): {net: tuple(sorted(p, key=lambda x: x.relation)) for net, p in paths.items()},
        ("node", "dc_window"): _windows(c, values),
        ("device", "dc_ln_idu"): ln_idu,
        ("device", "dc_op"): ops,
        ("device", "dc_sat_v"): sat,
        ("device", "dc_finger"): fingers,
        ("graph", "dc_scc_log"): {DC_KEY: tuple(dataclasses.replace(entry, slice_rounds=rounds) for entry in logs)},
    }


@compute_block(DC_SOLVE_WRITER, reads=READS, writes=WRITES)
def dc_solve(projection):
    c = _Circuit(projection)
    if c.realized is not None:
        values, logs, rounds, picks, widths = _resolved(c, projection)
        return _outputs(c, projection, values, logs, rounds, picks, widths)
    picks, keys = {}, {}
    for m, coord in sorted(c.coord.items()):
        if coord.role == COORD_WRITER:
            picks[m] = c.pick_writer(m)
            keys[m] = picks[m].w_key
        else:
            keys[m] = c.reference_key(m)
    values, logs, rounds, rpicks = _rounds(c, keys)
    picks.update(rpicks)
    for m, coord in sorted(c.coord.items()):
        if coord.role != COORD_WRITER and m not in picks:
            picks[m] = c.pick_dependent(m, values)
    return _outputs(c, projection, values, logs, rounds, picks)
