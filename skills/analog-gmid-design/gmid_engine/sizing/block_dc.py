"""④⑤ DC 블록 `dc_solve` -- 노드전압 정본 풀이 + 소자별 폭 슬라이스 선택 + 소자 동작점 (WB-1, 설계 40 §3.7-A, 계획 DEC-105 (2)·DEC-31·DEC-88).

진입점: `dc_solve`(`@compute_block`, writer `dc_solve`) -- `dc_solve(snapshot, column_items, fixed_values, resistor_values, lut, geometry=None, realized=None)`.
옛 `dc_columns`(노드전압)·`dc_widths`(W·동작점)를 합쳤다 -- `device.dc_op`·`dc_sat_v`·`dc_ln_idu`·`node.dc_v`·`dc_path_values`·`dc_window`·`graph.dc_scc_log` 와 새 필드
`device.dc_finger`(`FingerGeom(m, w_f_m, residual)`)의 writer 는 이 블록 하나다.

* extras: `column_items` = θ 의 ln_idu·y·resistance 성분 (((kind, key), v), ...), `fixed_values` = ((넷, V), ...) W3·입력 DC, `resistor_values` = ((저항, Ω), ...) spec 선언값,
  `lut` = LutAccess(memo 만 -- 슬라이스 키 칸 없음), `geometry` = `RealizedGeometry`(레이아웃 뒤, 없으면 None), `realized` = `RealizedFinger`(실현 평가, 없으면 None).
* **순서(한 호출, 설계 40 §3.7-A 2)**: (1) 쓰기 소자(`dc_coord.role` = writer)마다 W = ID·L/exp(θ ln IDu) 를 상수로 `finger_slice` 가 (m, 슬라이스 폭, 키)를 고른다(반복 없음).
  (2) 노드 풀이(SCC 위상 순서; Rʳ 소자의 시작 키 = 그 kind 기준 폭 슬라이스 `cap_map[kind].w_key`). (3) 종속 소자마다 후보 슬라이스 s 의 W(s) = ID·L/IDu_s(노드 점)를
  `finger_slice` 에 넘겨 (m, s) 를 고른다(`op_point` 가 `is_slice_gap` 이면 그 후보를 뺀다, 그 밖 예외는 그대로). (4) Rʳ ≠ ∅ 이고 키 벡터가 달라졌으면 (2)부터 다시, 직전과 같으면 수렴, 이전
  벡터로 돌아가면 `SealViolationError`(reason `slice_cycle`, devices = Rʳ, detail `cycle`). Rʳ = writer 없는 순환 SCC 에서 수렴 허용오차 셀을 내는 종속 MOS(그 슬라이스 tol 표가 노드 풀이의
  tol 이 된다). Rʳ = ∅ 이면 노드 풀이는 한 번이다. (5) `DeviceOp.w_key`·`gm_id`·`idu_forward`·`dc_finger` 가 같은 슬라이스를 가리킨다.
* 평가는 θ 의 순수 함수다. `slice_missing` 이 나면 `devices = (소자,)` 를 채워 다시 던진다(reason 은 그대로).
* **레이아웃 뒤(`geometry`)**: `w_request` 소자는 총 폭이 요청값(`DeviceOp.W`)이고 `dc_finger` 행을 쓰지 않는다(빈 열). `layout_ref`(= 배치 소자의 실현 확산 기하 ((소자, 기하), ...))에 있는 소자는
  그 finger 폭 `finger_w` 의 `slice_of_finger` 가 슬라이스이고(선택 함수를 부르지 않는다), 없는 소자(요청 대기)는 탐색 규칙(상수 W)을 쓴다.
  **미구현(보고)**: 실현 평가(`realized`, W′·바이어스 고정 KCL 재풀이)는 이 커밋에 없다(`realized` 를 주면 `NotImplementedError`).
* 노드 x 의 writer 식(소자 m, kind 부호 s = +1 nmos / −1 pmos, VDS·VSB 는 노드전압 차의 크기):
  `vgs_gate`: V(g) = V(s) + s·VGS(ln IDu_m, L_m, VDS, VSB) / `vgs_source`: V(s) = V(g) − s·VGS(...) / `resistor_drop`: V(t1) = V(t0) − I·R(또는 반대쪽) /
  `free_window`(W4): V = lo + y·(hi − lo), [lo, hi] = x 에 채널이 닿는 전도 MOS 마다 VDS ≥ 0 이 되는 쪽의 교집합(KVL 순서 창, VDSAT 항 없음), 제약 없는 쪽은 레일 전압 범위 끝.
  창이 비면(lo > hi) `SealViolationError`(item 7, reason `empty_window`). 저항 강하 전류는 `device.dc_current` 를 읽는다(둘째 필드 `dc_drop_current` 삭제).
* 1변수 노드(diode gate·소스 추종 source)는 구간 괄호 근(`solve_self`, Brent). VDS 쪽 구간 끝 = writer 슬라이스의 VDS 정의역 하한(`vds_floor`), 다변수 순환 SCC 는 `gauss_seidel`
  (N3.6 q 규칙·K_max) 뒤 strict 검증 바퀴, 못 닿으면 감쇠 Newton(`newton_solve`). 허용오차 = SCC 쓰기 MOS(없으면 단자가 닿는 MOS) 슬라이스의 id_equivalent tol_V 셀의 최솟값(N3.6, tol_V 는 수치 자기 정합
  tolerance 이고 물리 경계가 아니다 O-240). 폭 = 레일 전압 범위.
* 종속 소자 좌표 ln IDu = ln(그 소자 슬라이스의 순방향 LUT IDu(노드 VGS, VDS, VSB)). 쓰기 소자 좌표 = θ.
* `path_values`(봉인 1 입력): 노드에 닿는 관계마다 그 관계가 함의하는 노드 전압(MOS = 좌표에서 VGS 역산, 저항 = 강하, W4·고정 = 값).
* `dc_sat_v` = `sat_threshold(memo, kind, DeviceOp.w_key, L, vgs, vds, vsb)`(선언 없음·`triode`, 비전도 포함), `off` 선언 소자 = `SatBound(None, None, "off_declared")`.
* 커널 창 `node.dc_window` = W4 뿌리마다 KVL 순서 창 하나(상태·`tol_v` 없음); 입력 창 측정은 `icm_config` 한 자리.
"""
import dataclasses
import math

from gmid_engine.authoring import REGION_OFF, REGION_TRIODE
from gmid_engine.core import NonconvergentError, SealViolationError, compute_block
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import (AXES, tol_v_table, REASON_OFF_DECLARED, FingerSlice, SatBound, derived, finger_slice, gmb, is_slice_gap, op_point,
                             sat_threshold, slice_of_finger, vgs_for_current_density)

from ._helpers_dc_solve import Circuit
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
    ("node", "port_direction"), ("device", "region_decl"),
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
        self.placed = {} if geometry is None or geometry.layout_ref is None else dict(geometry.layout_ref)      # 배치 소자 -> 확산 기하(finger_w, m)
        self.keys = {}                             # 소자 -> 지금 쓰는 슬라이스 키(블록 안 값: 쓰기 소자 = 선택 결과, 종속 소자 = 기준 슬라이스에서 시작해 Rʳ 되풀이로 바뀐다)
        self.r_dep = set()                         # Rʳ: writer 없는 순환 SCC 의 수렴 허용오차 셀을 내는 종속 MOS(`_solve` 가 채운다)
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

    def transient(self, exc, m, vds):
        """반복 중(시작값 둘째 단계 포함, strict=False) 현재 값을 유지할 LUT 정의역 이탈인가: `lut_axis_out_of_range`·
        `lut_target_out_of_range`, 또는 VDS 정의역 하한(`vds_floor`(LUT 파생)) 아래에서 난 `lut_curve_undefined`."""
        lut_reason = dict(exc.record.detail).get("lut_reason")
        if lut_reason in _TRANSIENT_LUT_REASONS:
            return True
        return lut_reason == _CURVE_UNDEFINED and vds < derived(self.lut.memo, "vds_floor", self.kinds[m], self.keys[m])

    def start_writer(self, net, values):
        """시작값 둘째 단계(쓰기 계획 순서): MOS writer 노드는 writer 식을 VDS = 레일 범위 절반에서 한 번 평가한 값
        (diode·소스 추종의 고정점 근처). VSB 는 `vgs_gate`(source 를 안다)면 현재값, `vgs_source`(source 가 x 자신)면 0
        -- 체효과가 가장 작은 쪽에서 시작해 소스 추종이 레일 밖으로 튀지 않게 한다. 저항은 writer 식, W4 는 기둥
        위치 시작값 그대로. 시작값일 뿐이고 수렴값은 시작값과 무관하다(수렴 판정 = N3.6)."""
        w = self.writers[net]
        if self.self_referential(net):
            return self.solve_self(net, values, strict=False)[0]
        if w.relation in (REL_VGS_GATE, REL_VGS_SOURCE):
            m = w.element
            _vds, vsb = self.vds_vsb(m, values)
            vsb = vsb if w.relation == REL_VGS_GATE else 0.0
            vds = (self.hi - self.lo) / 2
            try:
                vgs = _vgs_of_coordinate(self.lut, m, self.kinds[m], self.keys[m], self.L[m], vds, vsb, self.ln_idu[m])
            except SealViolationError as exc:
                if not self.transient(exc, m, vds):
                    raise
                return values[net]
            sign = self.kind_sign(self.kinds[m])
            return values[w.known] + sign * vgs if w.relation == REL_VGS_GATE else values[w.known] - sign * vgs
        if w.relation == REL_RESISTOR:
            return self.update(net, values)
        return values[net]

    def self_referential(self, net):
        """writer 소자의 VDS·VSB 가 x 자신을 읽는가(diode 의 gate 쓰기, 소스 추종의 source 쓰기) -- 1변수 방정식 노드. 판정은 쓰기 계획이 S0 당 한 번 쓴
        `device.dc_self_referential`(설계 40 §2.4.8)을 읽는다(소자는 노드 하나만 쓴다)."""
        w = self.writers[net]
        return w.relation in (REL_VGS_GATE, REL_VGS_SOURCE) and w.element in self.self_ref

    def _vgs_signed(self, m, vds, vsb):
        """bisection 용 VGS: 목표 전류가 그 (vds, vsb) 곡선의 강반전 분지 위 범위 밖이면 부호가 정해진 무한대
        (위 = +inf: 필요한 VGS 가 격자 위, 아래 = −inf: 분지 시작 아래) -- 단조 함수의 정의역 밖 쪽을 알려 준다.
        그 밖 LUT 실패(축 밖·비단조)는 소자 이름을 붙여 그대로 낸다."""
        kind = self.kinds[m]
        w_key = self.keys[m]
        try:
            return vgs_for_current_density(self.lut.memo, kind, w_key, self.ln_idu[m], self.L[m], vds, vsb)
        except SealViolationError as exc:
            detail = dict(exc.record.detail)
            if detail.get("reason") != _TARGET_OUT_OF_RANGE:
                raise with_device(exc, m, "vgs_of_coordinate") from exc
            return math.inf if detail["target"] > detail["branch_max"] else -math.inf

    def solve_self(self, net, values, strict=True):
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
        grids = self.lut.memo.lut.slice_map[(kind, self.keys[m])].grids
        sign = self.kind_sign(kind)
        known = values[w.known]

        def channel(x):
            trial = dict(values)
            trial[net] = x
            return self.vds_vsb(m, trial)

        (vds0, vsb0), (vds1, vsb1) = channel(0.0), channel(1.0)
        bounds = [(self.lo, self.hi, _BOUND_RAIL)]
        vds_domain = (derived(self.lut.memo, "vds_floor", kind, self.keys[m]), grids[_VDS_AXIS][-1])
        for a, b, axis, label in ((vds0, vds1 - vds0, vds_domain, _BOUND_VDS),
                                  (vsb0, vsb1 - vsb0, grids[_VS_AXIS], _BOUND_VS)):
            if b != 0:
                ends = sorted(((axis[0] - a) / b, (axis[-1] - a) / b))
                bounds.append((_inward(ends[0], ends[-1], a, b, axis), _inward(ends[-1], ends[0], a, b, axis), label))
        lo, lo_from = max((b[0], b[2]) for b in bounds)
        hi, hi_from = min((b[1], b[2]) for b in bounds)

        def h(x):
            vds, vsb = vds0 + (vds1 - vds0) * x, vsb0 + (vsb1 - vsb0) * x
            vgs = self._vgs_signed(m, vds, vsb)
            target = known + sign * vgs if w.relation == REL_VGS_GATE else known - sign * vgs
            return x - target

        if lo > hi and not strict:
            return (lo + hi) / 2, 0, None
        if lo > hi:
            raise SealViolationError(devices=(m,), detail={"item": SEAL_SATURATION, "reason": REASON_NO_ROOT,
                                                           "node": net, "lo": lo, "hi": hi,
                                                           "bounds": (lo_from, hi_from)})
        middle = dict(values)
        middle[net] = (lo + hi) / 2
        tol = self.tolerance((m,), middle)

        def solved():
            root, h_a, h_b = bracket_root(h, lo, hi, tol)
            if root is not None:
                polished = root - h(root)
                if math.isfinite(polished) and lo <= polished <= hi:
                    root = polished
            return root, h_a, h_b

        # h 는 (소자 종류·L·ln IDu·writer 관계·known 값·VDS/VSB 의 x 1차식 계수·구간·tol) 만의 함수 -- 같은 입력이면 풀이를 다시
        # 하지 않는다(GS 반복·strict 재검증·FD 형제·탐색 평가 사이 중복). LUT memo root 영역(상한 있는 LRU).
        key = (kind, self.keys[m], self.L[m], self.ln_idu[m], w.relation, known, vds0, vds1, vsb0, vsb1, lo, hi, tol)
        x, h_lo, h_hi = self.lut.memo.lookup("root", _SOLVE_SELF_MEMO, key, solved)
        if x is None and not strict:
            return min((abs(h_lo), lo), (abs(h_hi), hi))[1], 0, tol
        if x is None:
            finite = [abs(v) for v in (h_lo, h_hi) if math.isfinite(v)]
            item = SEAL_SATURATION if _BOUND_VDS in (lo_from, hi_from) else SEAL_BULK_REVERSE
            raise SealViolationError(devices=(m,), margin=min(finite) / tol if finite else None,
                                     detail={"item": item, "reason": REASON_NO_ROOT, "node": net, "lo": lo, "hi": hi,
                                             "h_lo": h_lo, "h_hi": h_hi, "bounds": (lo_from, hi_from)})
        return x, k_max(hi - lo, tol) if hi > lo else 1, tol

    def reference_key(self, m):
        """종속 소자의 시작 키 = 그 kind 기준 폭 슬라이스 키(`cap_map[kind].w_key`, LUT 선언만의 함수). 없으면 `slice_missing`."""
        if m in self.placed:
            return self.placed_slice(m).w_key
        key = self.lut.memo.lut.cap_map[self.kinds[m]].w_key
        if key is None:
            raise SealViolationError(devices=(m,), detail={"reason": "slice_missing", "kind": self.kinds[m], "L": self.L[m], "why": "no_w_hi", "excluded": ()})
        return key

    def pick_writer(self, m):
        """쓰기 소자 m 의 (m, 슬라이스 폭, 키): W = ID·L/exp(θ ln IDu) 를 상수로 `finger_slice`(반복 없음)."""
        width = self.current[m] * self.L[m] / math.exp(self.ln_idu[m])
        if m in self.placed:
            return self.placed_slice(m)
        try:
            return finger_slice(self.lut.memo.lut, self.kinds[m], self.L[m], lambda _key: width)
        except SealViolationError as exc:
            raise with_device(exc, m, "finger_slice") from exc

    def placed_slice(self, m):
        """레이아웃이 놓은 소자의 (nf, finger 폭, 슬라이스 키) -- 선택 함수 없이 `slice_of_finger`."""
        geom = self.placed[m]
        try:
            return FingerSlice(round(geom.m), geom.finger_w, slice_of_finger(self.lut.memo.lut, self.kinds[m], self.L[m], geom.finger_w))
        except SealViolationError as exc:
            raise with_device(exc, m, "slice_of_finger") from exc

    def pick_dependent(self, m, values):
        """종속 소자 m 의 선택: 후보 슬라이스 s 마다 W(s) = ID·L/IDu_s(노드 점)(조회 불능 사유 다섯은 후보 제외, 그 밖은 그대로)."""
        if m in self.placed:
            return self.placed_slice(m)
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

    def tol_cell(self, m, vds):
        """소자 m 의 슬라이스(`keys[m]`) (L 앵커, VDS) 셀 id_equivalent tol_V -- 정의된 셀이 없으면 None."""
        try:
            return tol_v_table(self.lut.memo, self.kinds[m], self.keys[m]).at(self.L[m], vds, "id_equivalent")
        except SealViolationError as exc:
            raise with_device(exc, m, "tol_v_cell") from exc

    def has_channel_values(self, m, values):
        d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
        return d in values and s in values and self.bulk[m] in values

    def update(self, net, values, strict=True):
        """노드 writer 식. `strict=False`(다변수 SCC Gauss-Seidel 반복 중): 1변수 노드는 투영 bisection, MOS writer 의 LUT
        정의역 이탈(`lut_axis_out_of_range`·`lut_target_out_of_range`·VDS 정의역 하한 아래의 `lut_curve_undefined` -- 이웃의
        과도 반복값 때문)과 W4 창이 빈 경우는 실패
        대신 현재 값을 그대로 둔다. 수렴 뒤 `strict=True` 검증 한 바퀴가 같은 식을 다시 재므로 최종값에 남지 않는다."""
        w = self.writers[net]
        if self.self_referential(net):
            return self.solve_self(net, values, strict=strict)[0]
        if w.relation in (REL_VGS_GATE, REL_VGS_SOURCE):
            m = w.element
            vds, vsb = self.vds_vsb(m, values)
            try:
                vgs = _vgs_of_coordinate(self.lut, m, self.kinds[m], self.keys[m], self.L[m], vds, vsb, self.ln_idu[m])
            except SealViolationError as exc:
                if strict or not self.transient(exc, m, vds):
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

    def writer_grad(self, net, values):
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
            vgs = _vgs_of_coordinate(self.lut, m, kind, self.keys[m], self.L[m], vds, vsb, self.ln_idu[m])
            w_key = self.keys[m]
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

    def newton_system(self, nodes, values):
        """SCC 잔차 r_i = V_i − g_i(V) 와 야코비안 J = I − ∂g/∂V(SCC 노드 열만 -- 바깥 노드는 이미 확정된 상수).
        한 노드라도 정의역 밖(LUT 조회 실패·빈 창 = `SealViolationError`)이면 None(선 탐색이 α 를 줄인다)."""
        index = {n: i for i, n in enumerate(nodes)}
        residuals = []
        rows = []
        for n in nodes:
            try:
                g, grad = self.writer_grad(n, values)
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

    def tolerance(self, devices, values):
        tols = []
        for m in devices:
            vds, _vsb = self.vds_vsb(m, values)
            key = (m, self.keys[m], vds)                   # 한 평가 안에서 같은 (소자, 슬라이스, VDS) 셀 조회는 한 번(L·kind 는 소자마다 고정)
            if key not in self.tol_cells:
                self.tol_cells[key] = self.tol_cell(m, vds)
            tol = self.tol_cells[key]
            if tol is not None:
                tols.append(tol)
        if not tols:
            raise SealViolationError(devices=tuple(devices), detail={"reason": REASON_TOL_UNDEFINED})
        return min(tols)


def _strict_recheck(c, entry, values, tol):
    """검증 바퀴: 수렴점에서 SCC 노드마다 writer 식을 strict 로 다시 잰다(1변수는 bisection 전체). 정의역 밖이면 그
    `SealViolationError` 그대로, |새 값 − 수렴값| > tol 이면 `NonconvergentError`(reason `strict_recheck_residual`)."""
    for net in entry.nodes:
        residual = abs(c.update(net, values) - values[net])
        if residual > tol:
            raise NonconvergentError(devices=entry.devices, margin=residual / tol,
                                     detail={"node": net, "reason": REASON_STRICT_RECHECK, "nodes": entry.nodes})


def _solve(c):
    """쓰기 계획 위상 순서로 SCC 를 풀어 (노드전압, SccLog 열)을 낸다 -- 현재 `c.theta` 한 벌에 대한 풀이 한 번."""
    values = dict(c.rail_v)
    for net, w in c.writers.items():
        if w.relation in (REL_TARGET, REL_INPUT_DC):
            values[net] = float(c.fixed[net])
    logs = []
    for entry in c.order:
        entry_devices = tuple(sorted(entry.devices, key=lambda m: (c.device_colour.get(m, 0), m)))      # 구조 색 순서(이름이 처음 실패할 소자를 정하지 않게)
        if not entry.cyclic:
            (net,) = entry.nodes
            values[net] = c.update(net, values)
            logs.append(SccLog(entry.index, entry.nodes, 1, (), None, None))
            continue
        for net in entry.nodes:
            values[net] = c.start(net)
        if len(entry.nodes) == 1:
            (net,) = entry.nodes
            values[net], k, tol = c.solve_self(net, values)
            logs.append(SccLog(entry.index, entry.nodes, k, (), tol, k, SCC_BISECTION))
            continue
        positional = dict(values)
        for net in entry.nodes:
            values[net] = c.start_writer(net, values)
        writers = tuple(sorted({c.writers[n].element for n in entry.nodes
                                if c.writers[n].relation in (REL_VGS_GATE, REL_VGS_SOURCE)},
                               key=lambda m: (c.device_colour.get(m, 0), m)))              # 구조 색 순서 -- 이름이 처음 실패할 소자를 정하지 않게
        devices = writers or tuple(m for m in entry_devices if c.has_channel_values(m, values))
        if not writers:
            c.r_dep.update(devices)                        # Rʳ -- 수렴 허용오차 셀을 종속 소자가 내는 SCC

        def tolerance(v, devs=devices):
            return c.tolerance(devs, v)

        method, fallback, solved, seal_failure = SCC_GAUSS_SEIDEL, None, None, None
        try:
            solved, (k, deltas, tol, limit) = gauss_seidel(
                entry.nodes, values, lambda n, v: c.update(n, v, strict=False), tolerance, c.hi - c.lo, entry_devices)
            _strict_recheck(c, entry, solved, tol)
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
                return c.newton_system(nodes, v)

            start = next((s for s in starts if system(s) is not None), values)
            try:
                solved, (k, deltas, tol, limit) = newton_solve(entry.nodes, start, system, tolerance, c.hi - c.lo,
                                                               entry_devices)
            except NonconvergentError as newton_exc:       # Newton 도 해를 못 찾았다 -- GS 수렴점에서 잰 strict 검증 위반이
                if seal_failure is None:                   # 있었으면 그 사실(봉인 위반)을 낸다(strict 검증 규약 불변)
                    raise
                raise seal_failure from newton_exc
            _strict_recheck(c, entry, solved, tol)
        values = solved
        logs.append(SccLog(entry.index, entry.nodes, k, deltas, tol, limit, method, fallback))
    return values, tuple(logs)


def _windows(c, values):
    """`node.dc_window` -- W4 뿌리 항목마다 KVL 순서 창 하나(`Window(lo, hi, constraints)`, 상태·`tol_v` 없음)."""
    out = {}
    for net, w in c.writers.items():
        if _is_root(w):
            lo, hi, ncols = c.window(net, values)
            out[net] = Window(lo, hi, ncols)
    return out


def _rounds(c):
    """노드 풀이(+ Rʳ 키 되풀이): (values, logs, 풀이 횟수, {Rʳ 소자: FingerSlice}). 키 벡터가 직전과 같으면 수렴, 이전 벡터로 돌아가면 `slice_cycle`."""
    seen = []
    rounds = 0
    while True:
        values, logs = _solve(c)
        rounds += 1
        devices = sorted(c.r_dep - c.placed.keys())            # 배치 소자의 키는 고정이다
        if not devices:
            return values, logs, rounds, {}
        now = tuple((m, c.keys[m]) for m in devices)
        picks = {m: c.pick_dependent(m, values) for m in devices}
        after = tuple((m, picks[m].w_key) for m in devices)
        if after == now:
            return values, logs, rounds, picks
        seen.append(now)
        if after in seen:
            raise SealViolationError(devices=tuple(devices), detail={"reason": REASON_SLICE_CYCLE, "cycle": tuple(seen) + (after,)})
        c.keys.update({m: picks[m].w_key for m in devices})


@compute_block(DC_SOLVE_WRITER, reads=READS, writes=WRITES)
def dc_solve(projection):
    c = _Circuit(projection)
    if c.realized is not None:
        raise NotImplementedError("dc_solve: 실현 평가(RealizedFinger)는 이 커밋에 없다")
    requested = {} if c.geometry is None else dict(c.geometry.w_request)
    picks = {}
    for m, coord in sorted(c.coord.items()):
        if coord.role == COORD_WRITER:
            picks[m] = c.pick_writer(m)
            c.keys[m] = picks[m].w_key
        else:
            c.keys[m] = c.reference_key(m)
    values, logs, rounds, rpicks = _rounds(c)
    picks.update(rpicks)
    for m, coord in sorted(c.coord.items()):
        if coord.role != COORD_WRITER and m not in picks:
            picks[m] = c.pick_dependent(m, values)
        c.keys[m] = picks[m].w_key
    ln_idu, ops, sat, fingers = {}, {}, {}, {}
    for m, coord in c.coord.items():
        kind, key = c.kinds[m], c.keys[m]
        vgs, vds, vsb = c.mos_point(m, values)
        point = forward_point(c.lut, m, kind, key, c.L[m], vgs, vds, vsb)
        ln_idu[m] = c.ln_idu[m] if coord.role == COORD_WRITER else math.log(point.IDu)
        free_width = c.current[m] * c.L[m] / math.exp(ln_idu[m])
        width = requested[m] if m in requested else free_width
        ops[m] = DeviceOp(kind, c.current[m], ln_idu[m], point.gm_over_id, c.L[m], width, vgs, vds, vsb, key, point.IDu)
        pick = picks[m]
        if c.geometry is None:
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
        vgs = _vgs_of_coordinate(c.lut, m, c.kinds[m], c.keys[m], c.L[m], vds, vsb, ln_idu[m])
        sign = c.kind_sign(c.kinds[m])
        paths[g].append(PathValue((_REL_MOS, m), values[s] + sign * vgs))
        paths[s].append(PathValue((_REL_MOS, m), values[g] - sign * vgs))
    for net, w in c.writers.items():
        if w.relation == REL_RESISTOR:
            far_from_near = c.drop(w.element, w.known, net)
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
