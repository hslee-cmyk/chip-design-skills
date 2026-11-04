"""④ 노드전압 정본 풀이 계산 블록 -- 쓰기 계획대로 SCC 위상 순서로 노드전압을 쓰고 종속 소자 좌표를 순방향으로 정한다
(설계 3.2 3·3.3·3.4, 계획 DEC-31 노드전압 = DC 정본, N3.4, SC-c, DEC-88).

진입점: `dc_columns`(`@compute_block`) -- `dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)`.

* extras: `theta_items` = θ 의 ln_idu·y·resistance 성분 (((kind, key), v), ...), `fixed_values` = ((넷, V), ...) W3·입력 DC,
  `resistor_values` = ((저항, Ω), ...) spec 선언값, `lut` = LutAccess.
* 노드 x 의 writer 식(소자 m, kind 부호 s = +1 nmos / −1 pmos, VDS·VSB 는 노드전압 차의 크기):
  `vgs_gate`: V(g) = V(s) + s·VGS(ln IDu_m, L_m, VDS, VSB) / `vgs_source`: V(s) = V(g) − s·VGS(...) /
  `resistor_drop`: V(t1) = V(t0) − I·R(또는 반대쪽) /
  `free_window`(W4): V = lo + y·(hi − lo), [lo, hi] = x 에 채널이 닿는 전도 MOS 마다 VDS ≥ 0 이
  되는 쪽의 교집합(전류가 나가는 단자면 lo ≥ V(반대), 들어오는 단자면 hi ≤ V(반대)), 제약 없는 쪽은 레일 전압 범위 끝.
  설계 3.4 는 기둥(레일~x 소자들의 VDsat 합)으로 적었으나 S1 기둥은 노드-단순 경로라 전류 방향을 거스르는 경로(분기 노드에서
  위로 돌아가는 경로)를 포함해 순서가 뒤집힌다 -- 인접 소자 제약을 이웃 노드가 다시 자기 창 안에 있는 사슬로 쓰면 같은
  뜻이다. **VDsat 항은 넣지 않는다**: lut r6 에 VDSAT 열 조회가 생겼지만 인접 MOS 의 VDsat 은 그 소자 gate·bulk·x 자신을
  읽어야 해서 W4 의존(`dc_scc_order`)을 바꿔야 한다(계약 12절 O1 잔여, 결정 대기) -- 창은 KVL 순서 창이고 포화는 봉인 7 이
  판정한다. 창이 비면(lo > hi) `SealViolationError`(item 7, reason `empty_window`).
* 1변수 노드(diode gate·소스 추종 source)는 구간 bisection(`solve_self`, 설계 3.4). VDS 쪽 구간 끝 = writer 슬라이스의 VDS
  정의역 하한(`_vds_floor`, 데이터 유도), 끝점은 부동소수 반올림으로 축 밖에 떨어지지 않게 안쪽으로 맞춘다(`_inward`). 다변수 순환 SCC 는 `gauss_seidel`
  (N3.6 q 규칙·K_max) -- 반복 중에는 정의역 이탈을 투영하고(`update(strict=False)`) 수렴 뒤 strict 검증 바퀴로 확인한다.
  Gauss-Seidel 이 K_max 안에 tol 에 닿지 못하면(측정한 수축비 q 로 판정 -- q ≥ 1 또는 q < 1 이지만 남은 상한 안 도달 불가)
  같은 시작값에서 SCC 잔차 r = V − g(V) 에 감쇠 Newton(`newton_solve`, 야코비안 = `writer_grad` 의 LUT 미분)으로 바꾼다.
  strict 검증 바퀴는 두 경우 모두 같다. GS 수렴점의 strict 검증이 `SealViolationError` 였는데 Newton 도
  `NonconvergentError` 로 끝나면 그 strict 검증 위반을 그대로 낸다(cause = Newton 실패). 허용오차 = SCC 쓰기 MOS(없으면 단자가 닿는 MOS) id_equivalent tol_V
  셀의 최솟값(현재 반복값의 L·VDS). 폭 = 레일 전압 범위. 시작값 = 기둥 위치 비례(레일 사이 선형, 기둥 밖이면 레일 중앙)
  다음 `start_writer`(MOS writer 식 1회). 저항 강하 전류는 `device.dc_drop_current`(저항만)를 읽는다 -- MOS 전류만 바뀐 θ 는
  이 블록을 다시 돌리지 않는다.
* 종속 소자 좌표 ln IDu = ln(순방향 LUT IDu(노드 VGS, VDS, VSB)) -- 같은 gate 넷에 소자마다 다른 전압을 요구하는 상태는
  표현할 수 없다(설계 3.3 4). 쓰기 소자 좌표 = θ.
* `path_values`(봉인 1 입력): 노드에 닿는 관계마다 그 관계가 함의하는 노드 전압(MOS = 좌표에서 VGS 역산, 저항 = 강하,
  W4·고정 = 값).
* **창 경계 행 `Circuit.region_rows`**(`_helpers_dc_solve`, 설계 41 4.7-3a·4.7-W W2, 카드 IT-2c): 이 블록이 쓰는 입력 포화 창 측정(`input_windows`)도 같은 행을 쓴다 --
  판정 여유 0(VDS = VDSAT, tol 항 없음).
* **커널 창 `node.dc_window`**(설계 41 4.7-2·4.7-3 1, 카드 IT-2c 뒤): **W4 뿌리 항목만**. 입력 포트가 아닌 W4 뿌리는 순서 창(`input_status` None).
  입력 포트인 W4 뿌리(최대 하나): A6 -- y = 1/2 풀이 → 창 측정 → 창을 y 범위(`override`)로 두고 다시 풀며 경계가 tol 안에서 같아질 때까지(상한 `k_max`)
  되풀이. 수렴하면 `measured`, 수렴하지 않았거나(c) tol 미정(b)이면 `unsettled`(y 범위는 그대로 쓴다), 창을 못 재면(a) `unmeasured`(순서 창). 뿌리 아닌 입력 포트·입력 DC
  선언 포트·F 성분 미선언 포트의 창은 이 블록의 항목이 아니다 -- 측정 구성 블록 `icm_config` 가 모든 입력 포트를 함께 구동해 잰다(`node.dc_window_cfg`).
  이 입력 창 측정(`_measure`·`_interior_solution`·`_dyadic_ys`·`INPUT_STATUS_UNSETTLED`)은 card WB-1 범위 3a 가 재작성한다.
  `k_max` 는 이 모듈 수준 이름이다(L12 (a) 주입 지점).
* writes `node.dc_v`(레일 밖 모든 노드), `node.dc_path_values`(모든 노드), `node.dc_window`(W4 뿌리 + 입력 포트),
  `device.dc_ln_idu`(모든 MOS), `graph.dc_scc_log`.
"""
import dataclasses
import math

from gmid_engine.authoring import INPUT_DIRECTION, REGION_TRIODE
from gmid_engine.core import NonconvergentError, SealViolationError, compute_block
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import AXES, gmb, vgs_for_current_density

from ._helpers_dc_solve import Circuit
from ._helpers_lut import forward_point, tol_v_cell, w_key_of, with_device
from .bracket_root import bracket_root
from .fixed_point import gauss_seidel
from .input_window import saturation_window
from .k_max import k_max
from .scc_newton import newton_solve
from .scc_order import FIXED_RELATIONS
from .s2_values import (
    COORD_WRITER,
    DC_COLUMNS_WRITER,
    DC_KEY,
    INPUT_STATUS_MEASURED,
    INPUT_STATUS_UNMEASURED,
    INPUT_STATUS_UNSETTLED,
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
    Window,
)

READS = (
    ("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "dc_column_nbrs"),
    ("device", "dc_drop_current"), ("node", "dc_colour"), ("device", "dc_colour"), ("device", "dc_L"), ("device", "pins"), ("device", "kind"), ("device", "bulk"),
    ("device", "element_class"), ("device", "dc_coord"), ("graph", "dc_scc_order"), ("device", "dc_self_referential"),
    ("node", "port_direction"), ("device", "region_decl"),
)
WRITES = (("node", "dc_v"), ("node", "dc_path_values"), ("node", "dc_window"), ("device", "dc_ln_idu"),
          ("graph", "dc_scc_log"))
_REL_MOS, _REL_RES, _REL_FIXED, _REL_Y = PATH_MOS, PATH_RESISTOR, PATH_FIXED, PATH_Y
def _is_root(w):
    """W4 뿌리 writer 인가 -- `free_window` 또는 입력 점의 뿌리(`input_point` 이고 known 없음; known 이 있으면 뿌리와 같은 전압인 짝 포트)."""
    return w.relation == REL_WINDOW or (w.relation == REL_INPUT_POINT and w.known is None)


_TARGET_OUT_OF_RANGE = "lut_target_out_of_range"       # lut CONTRACT 4.1·3.1 vgs_for_current_density·gm_id_for_target 사유 키
_TRANSIENT_LUT_REASONS = (_TARGET_OUT_OF_RANGE, "lut_axis_out_of_range")   # 반복 중 정의역 이탈(검증 바퀴가 다시 잰다)
_CURVE_UNDEFINED = "lut_curve_undefined"     # lut CONTRACT 4.1 -- VDS 정의역 하한(`_vds_floor`) 아래에서만 반복 중 이탈로 본다
_VDS_AXIS, _VS_AXIS = AXES.index("VDS"), AXES.index("VS")
_BOUND_RAIL, _BOUND_VDS, _BOUND_VS = "rail", "vds_axis", "vs_axis"
_SOLVE_SELF_MEMO = "solve_self"            # LUT memo root 영역의 함수 이름 칸(1변수 풀이 재사용)
_MID = 1 / 2                                         # y_icm 창을 재기 시작하는 해의 위치(순서 창 한가운데)
_HALVING = round(1 / _MID)                          # 분모가 늘어나는 비 -- 구간을 이분하는 수(1/2 다음 후보 열)
_GS_STOPPED = "gauss_seidel_stopped"                  # SccLog.fallback[0]: GS 가 K_max 안 tol 도달 불가로 멈춤


def _vds_floor(lut, kind):
    """writer 슬라이스의 VDS 정의역 하한 = on_mask((ID > 0) & (GM > 0))가 그 VDS 격자 열부터 끝 열까지 모든 (L, VGS, VS)
    점에서 켜진 첫 VDS 격자점(그런 열이 없으면 VDS 격자 최소 -- 축 범위 그대로). 그보다 작은 VDS 는 꺼진 열(LUT v2 는
    VDS = 0 열: 전류 0)과 보간되어 gm/ID 곡선 마디가 정의되지 않는다(lut `lut_curve_undefined`) -- LUT 가 그 VDS 의 동작점을
    표현하지 못한다는 데이터 사실이다. 상수 없음(데이터에서 유도). LUT memo derived 영역에 슬라이스당 1회(다른 캐시 없음)."""
    w_key = w_key_of(lut, kind)
    sl = lut.memo.lut.slice_map[(kind, w_key)]

    def compute():
        on = sl.on_mask
        full = on.all(axis=tuple(a for a in range(on.ndim) if a != _VDS_AXIS))
        axis = sl.grids[_VDS_AXIS]
        for j in range(len(axis)):
            if bool(full[j:].all()):
                return float(axis[j])
        return float(axis[0])

    return lut.memo.lookup("derived", "sizing_vds_floor", (kind, w_key), compute)


def _inward(x, toward, a, b, axis):
    """1차식 v = a + b·x 의 구간 끝 x = (축 끝 − a)/b 를 부동소수 반올림으로 v 가 축 [axis[0], axis[-1]] 밖에 떨어지면
    `toward` 쪽으로 한 ulp 씩 옮긴다(축 끝은 정의역 안 -- 반올림 때문에 끝점 조회가 축 밖·정의역 밖이 되지 않게)."""
    while not axis[0] <= a + b * x <= axis[-1] and x != toward:
        x = math.nextafter(x, toward)
    return x


def _vgs_of_coordinate(lut, device, kind, L, vds, vsb, ln_idu):
    """좌표 ln IDu(DEC-88)에서 VGS 크기 -- 강반전 분지 역산(lut `vgs_for_current_density`: 칸 안 Hermite 근, DEC-87)."""
    w_key = w_key_of(lut, kind)
    try:
        return vgs_for_current_density(lut.memo, kind, w_key, ln_idu, L, vds, vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "vgs_of_coordinate") from exc


class _Circuit(Circuit):
    """블록 한 번의 입력 묶음과 writer 식 -- 읽기 전용 공용 부분(`Circuit`)에 θ·고정 값·`override` 등 이 블록이 쓰는 상태를 더한다."""

    def __init__(self, projection):
        theta_items, fixed_values, resistor_values, lut = projection.extras
        super().__init__(projection, lut=lut, linear=frozenset(m for m, r in projection.column("device", "region_decl") if r.region == REGION_TRIODE))      # `triode` 선언 소자 -- 창 경계 행이 triode 행(`region_rows`)
        self.override = {}                                             # {W4 입력 뿌리 넷: (lo, hi)} 입력 포화 창 (y_icm 범위)
        self.theta = dict(theta_items)
        self.fixed = dict(fixed_values)
        self.nbrs = dict(projection.column("node", "dc_column_nbrs"))
        self.classes = dict(projection.column("device", "element_class"))
        self.current = dict(projection.column("device", "dc_drop_current"))
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
        self.inputs = frozenset(net for net, d in projection.column("node", "port_direction") if d == INPUT_DIRECTION)

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
        """W4 창 = 순서 창 ∩ (입력 뿌리면) 입력 포화 창 `override`(y_icm 범위, `input_windows`가 정한다)."""
        lo, hi, ncols = self.kvl_window(net, values)
        if net in self.override:
            lo, hi = max(lo, self.override[net][0]), min(hi, self.override[net][1])
        return lo, hi, ncols

    def input_roots(self):
        """입력 포트인 W4 뿌리 넷(y 키 = 그 넷; 입력 DC 미선언 회로 -- 단일 입력 뿌리 또는 입력 점의 p 포트, `dc_writer_plan` 이 그 밖은 정지시킨다 -- 최대 하나) -- 쓰기 순번 순."""
        return tuple(net for net, w in self.canonical_writers() if _is_root(w) and net in self.inputs)

    def input_windows(self, values, root):
        """해 `values` 에서 잰 이동량 창과 감도 `(dlo, dhi, slope)`(`saturation_window`) -- `root` = x 로 움직이는 커널 뿌리 넷 하나(설계 41 4.7-3 1). 고정 노드 가운데
        root 는 미지수로 넣는다(그 행은 s = 1). 잴 수 없으면 None."""
        rows = self.region_rows(values)
        if rows is None:
            return None
        unknown = tuple(net for net, w in self.canonical_writers() if w.relation not in FIXED_RELATIONS or net == root)     # 쓰기 순번 순 -- 선형 연립 행 순서가 이름을 따르지 않게
        return saturation_window(unknown, root, values, self.writer_grad, rows)

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
        `lut_target_out_of_range`, 또는 VDS 정의역 하한(`_vds_floor`) 아래에서 난 `lut_curve_undefined`."""
        lut_reason = dict(exc.record.detail).get("lut_reason")
        if lut_reason in _TRANSIENT_LUT_REASONS:
            return True
        return lut_reason == _CURVE_UNDEFINED and vds < _vds_floor(self.lut, self.kinds[m])

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
                vgs = _vgs_of_coordinate(self.lut, m, self.kinds[m], self.L[m], vds, vsb, self.ln_idu[m])
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
        w_key = w_key_of(self.lut, kind)
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
        grids = self.lut.memo.lut.slice_map[(kind, w_key_of(self.lut, kind))].grids
        sign = self.kind_sign(kind)
        known = values[w.known]

        def channel(x):
            trial = dict(values)
            trial[net] = x
            return self.vds_vsb(m, trial)

        (vds0, vsb0), (vds1, vsb1) = channel(0.0), channel(1.0)
        bounds = [(self.lo, self.hi, _BOUND_RAIL)]
        vds_domain = (_vds_floor(self.lut, kind), grids[_VDS_AXIS][-1])
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
        key = (kind, self.L[m], self.ln_idu[m], w.relation, known, vds0, vds1, vsb0, vsb1, lo, hi, tol)
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
                vgs = _vgs_of_coordinate(self.lut, m, self.kinds[m], self.L[m], vds, vsb, self.ln_idu[m])
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
            vgs = _vgs_of_coordinate(self.lut, m, kind, self.L[m], vds, vsb, self.ln_idu[m])
            point = forward_point(self.lut, m, kind, self.L[m], vgs, vds, vsb)
            w_key = w_key_of(self.lut, kind)
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
        if net in self.override:                    # 입력 포화 창이 순서 창보다 좁으면 그 끝은 상수(이웃 노드 항 없음)
            if self.override[net][0] > lo:
                lo, lo_node = self.override[net][0], None
            if self.override[net][1] < hi:
                hi, hi_node = self.override[net][1], None
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
            key = (m, vds)                                 # 한 평가 안에서 같은 (소자, VDS) 셀 조회는 한 번(L·kind 는 소자마다 고정)
            if key not in self.tol_cells:
                self.tol_cells[key] = tol_v_cell(self.lut, m, self.kinds[m], self.L[m], vds)
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
    """쓰기 계획 위상 순서로 SCC 를 풀어 (노드전압, SccLog 열)을 낸다 -- 현재 `c.theta`·`c.override` 한 벌에 대한 풀이 한 번."""
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


_FAILURES = (SealViolationError, NonconvergentError)


@dataclasses.dataclass(frozen=True)
class _Measured:
    """한 해에서 잰 입력 뿌리 창: `window` = (순서 창 ∩ 잰 창) 끝 전압, `values` = 그 해(되풀이 판정의 tol 을 같은 해에서 잰다). 한 `dc_columns` 호출 안에서만 산다."""

    window: tuple
    values: dict


@dataclasses.dataclass(frozen=True)
class _Kernel:
    """커널 풀이 결과: 마지막 풀이 `values`·`logs`, 입력 뿌리의 `status`(뿌리가 없으면 None)와 `tol`."""

    values: dict
    logs: tuple
    status: object
    tol: object


def _dyadic_ys(count):
    """y 후보 열 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, ... (앞 `count` 개) -- 구간을 이분 수준마다 훑는 순서(1/2 는 이미 해 봤다)."""
    out, level = [], _HALVING
    while len(out) < count:
        out.extend(k / level for k in range(1, level, _HALVING))
        level *= _HALVING
    return out[:count]


def _measure(c, root, values):
    """해 `values` 에서 입력 뿌리 `root` 의 입력 포화 창 -- 순서 창 ∩ (뿌리 전압 + 잰 이동량 창). 잴 수 없으면 None."""
    found = c.input_windows(values, root)
    if found is None:
        return None
    dlo, dhi, _slope = found
    lo, hi, _ncols = c.kvl_window(root, values)
    return _Measured((max(lo, values[root] + dlo), min(hi, values[root] + dhi)), values)


def _tolerance(c, values):
    """해 `values` 의 소자 전부 tol_V 셀 최솟값(A6 되풀이 판정·`Window.tol_v`). 어느 소자에서도 미정이면 None."""
    devices = tuple(sorted(c.coord, key=lambda m: (c.device_colour.get(m, 0), m)))
    try:
        return c.tolerance(devices, values)
    except SealViolationError:
        return None


def _interior_solution(c, key, requested):
    """y_icm = 1/2 가 풀리지 않을 때 입력 창을 재려고 순서 창 안에서 풀리고 창을 잴 수 있는 점을 찾는다 (설계 41 §4.6 '범위 = 입력 창').
    1/2 에서 이분 수준마다 y 를 훑되 시도 수는 `k_max`(레일 폭, 그 점 근처 tol) 이내. 반환 (값, 로그, 잰 창) 또는 None (못 찾음 -- 종래 사상)."""
    middle = (c.hi - c.lo) / 2                         # 풀이가 없어 VDS 를 모른다 -- 레일 폭의 절반 VDS 셀의 tol_V 로 시도 수 상한을 잰다
    tols = [tol for m in c.coord for tol in (tol_v_cell(c.lut, m, c.kinds[m], c.L[m], middle),) if tol is not None]
    if not tols:
        return None
    budget = k_max(c.hi - c.lo, min(tols))
    (root,) = c.input_roots()
    for y in _dyadic_ys(budget):
        c.theta[key] = y
        try:
            values, logs = _solve(c)
        except _FAILURES:
            continue
        finally:
            c.theta[key] = requested
        measured = _measure(c, root, values)
        if measured is not None:
            return values, logs, measured
    return None


def _solve_input_window(c):
    """입력 DC 대기 회로의 y_icm 범위 = 입력 포화 창 (사용자 결정 J-E, 설계 41 §4.6 SP-2 (c), 4.7-3 1).

    입력 포트인 W4 뿌리가 없으면 풀이 한 번(종래). 있으면: (1) y_icm = 1/2 로 풀어 해를 얻고(순서 창 사상; 풀리지 않으면 순서 창 안에서 풀리는
    점을 찾는다) (2) 그 해에서 잰 포화 창 [Vin,min, Vin,max] ∩ 순서 창을 y_icm 범위로 삼아 요청 y_icm 으로 다시 풀며 (3) 새 해에서 창을 다시 재
    경계가 tol 안에서 같아질 때까지 되풀이한다(상한 K_max = `k_max`(레일 폭, tol)). 끝 다듬기는 하지 않는다(커널 창은 선형 감도 끝, 설계 41 4.7-3 1).
    (1) 이 어디서도 풀리지 않거나 창을 잴 수 없으면(VDSAT 열 없음·tol 미정) 종래 사상(요청 y_icm, 순서 창)으로 푼다 -- 종래보다 나빠지지 않는다.
    tol = 창을 잰 해의 `tolerance`(되풀이 판정은 새 창을 잰 해, `Window.tol_v` 는 마지막 창을 잰 해 -- 설계 41 4.7-2·4.7-3 5; 해마다 한 번 계산, 저장 없음).
    상태: 되풀이가 tol 안에서 수렴하면 `measured`, 수렴하지 않았거나 tol 미정이면 `unsettled`(창은 잰 해에서 쟀으니 y 범위로는 쓴다), 창을 못 재면 `unmeasured`."""
    roots = c.input_roots()
    if not roots:
        values, logs = _solve(c)
        return _Kernel(values, logs, None, None)
    (root,) = roots
    key = (THETA_Y, c.writers[root].y_key)
    requested = c.theta[key]
    c.theta[key] = _MID
    try:
        values, logs = _solve(c)
        measured = _measure(c, root, values)
    except _FAILURES:
        measured = None
    finally:
        c.theta[key] = requested
    if measured is None:
        found = _interior_solution(c, key, requested)
        if found is None:
            values, logs = _solve(c)
            return _Kernel(values, logs, INPUT_STATUS_UNMEASURED, None)
        values, logs, measured = found
    tol = _tolerance(c, values)
    if tol is None:                                    # tol 이 어느 소자에서도 미정 -- 되풀이 수렴 판정을 할 수 없다(창은 한 번만 적용)
        c.override = {root: measured.window}
        values, logs = _solve(c)
        return _Kernel(values, logs, INPUT_STATUS_UNSETTLED, None)
    settled = False
    solved_with = None                                 # 마지막으로 푼 override -- 최종 override 가 같으면 같은 인자를 다시 풀지 않고 그 (values, logs) 를 쓴다(블록 안 지역 변수)
    for _ in range(k_max(c.hi - c.lo, tol)):          # 상한은 첫 해의 tol 로 정한다(설계 L12 상한식); 판정·tol_v 는 창을 잰 해마다의 tolerance
        c.override = {root: measured.window}
        values, logs = _solve(c)
        solved_with = c.override
        again = _measure(c, root, values)
        if again is None:
            break
        previous, measured, tol = measured, again, _tolerance(c, again.values)
        if tol is None:                                # 되풀이 중간에 tol 미정 -- A6 b 와 같이 수렴 판정 불가(마지막으로 잰 창을 y 범위로 쓴다)
            break
        settled = all(abs(a - b) <= tol for a, b in zip(again.window, previous.window))
        if settled:
            break
    c.override = {root: measured.window}
    if c.override != solved_with:
        values, logs = _solve(c)
    return _Kernel(values, logs, INPUT_STATUS_MEASURED if settled else INPUT_STATUS_UNSETTLED, tol)


def _windows(c, values, kernel):
    """`node.dc_window` -- W4 뿌리 항목만(입력 점 뿌리 포함, 설계 41 4.7-2). 입력 포트인 뿌리는 커널 입력 창 상태(`kernel.status`·`tol`)를 싣고, 아닌 뿌리는 순서 창이다."""
    out = {}
    for net, w in c.writers.items():
        if _is_root(w):
            lo, hi, ncols = c.window(net, values)
            out[net] = Window(lo, hi, ncols, kernel.status, kernel.tol) if net in c.inputs else Window(lo, hi, ncols)
    return out


@compute_block(DC_COLUMNS_WRITER, reads=READS, writes=WRITES)
def dc_columns(projection):
    c = _Circuit(projection)
    kernel = _solve_input_window(c)
    values, logs = kernel.values, list(kernel.logs)
    ln_idu = {}
    for m, coord in c.coord.items():
        if coord.role == COORD_WRITER:
            ln_idu[m] = c.ln_idu[m]
        else:
            vgs, vds, vsb = c.mos_point(m, values)
            ln_idu[m] = math.log(forward_point(c.lut, m, c.kinds[m], c.L[m], vgs, vds, vsb).IDu)
    paths = {net: [] for net in c.writers}
    for m in ln_idu:
        d, g, s = (c.pins[m][t] for t in MOS_TERMINAL_NAMES)
        _vgs, vds, vsb = c.mos_point(m, values)
        vgs = _vgs_of_coordinate(c.lut, m, c.kinds[m], c.L[m], vds, vsb, ln_idu[m])
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
        ("node", "dc_window"): _windows(c, values, kernel),
        ("device", "dc_ln_idu"): ln_idu,
        ("graph", "dc_scc_log"): {DC_KEY: tuple(logs)},
    }
