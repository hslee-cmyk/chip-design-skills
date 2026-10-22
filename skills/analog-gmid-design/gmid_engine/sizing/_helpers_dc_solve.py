"""노드전압 풀이 helper -- 커널 창(`dc_columns`)과 다듬은 창(`dc_window_refine`)이 같이 쓰는 θ 고정 노드 풀이 (설계 41 §4.7-3a·4.7-4 '공유하는 것', 카드 IT-2b).

공개 이름: `Circuit`(옛 `block_columns._Circuit` -- 블록 한 번의 읽기 전용 입력 묶음과 writer 식), `solve`(옛 `_solve` -- 쓰기 계획 위상 순서 SCC 풀이),
`FAILURES`(옛 `_FAILURES` -- 풀이가 낼 수 있는 실패 예외 tuple).

`Circuit.region_rows(values)` = 창 경계 행 셋(설계 41 4.7-3a 1): 전도 MOS 마다 5원소 행 `(a, b, sign, slack, kind)`.
* (가) 선언 없음 = `(d, s, 부호, VDS − VDsat − tol_VDsat, "sat")`(봉인 7 의 판정식), (나) `triode` 선언 = `(d, s, −부호, VDsat − VDS − tol_VDsat, "triode")`
  (여유가 VDS↑에 줄어 기울기 부호가 반대). tol_VDsat 은 두 행이 같은 LUT 셀값이다(새 상수 없음).
* (S4-나)(카드 IT-2b): `off` 행·V_on 호출은 없다(공용 전도 판정 함수가 아직 없다 -- card EO-1 몫).
동작점 불일치 판정은 이 card 밖이다(EO-1 묶음).
"""
import math

from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import NonconvergentError, SealViolationError
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import AXES, gmb, tol_vdsat_table, vdsat, vgs_for_current_density

from ._helpers_lut import forward_point, terminal_voltages, tol_v_cell, w_key_of, with_device
from .bracket_root import bracket_root
from .fixed_point import gauss_seidel
from .input_window import saturation_window
from .k_max import k_max
from .scc_newton import newton_solve
from .scc_order import FIXED_RELATIONS
from .s2_values import (
    REASON_EMPTY_WINDOW,
    REASON_NO_ROOT,
    REASON_STRICT_RECHECK,
    REASON_TOL_UNDEFINED,
    REL_INPUT_DC,
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
    DC_KEY,
    SccLog,
)

ROW_SAT = "sat"                                       # `region_rows` 행 종류: 선언 없음(포화)
ROW_TRIODE = "triode"                                 # `intended_region: triode` 선언 소자
_TARGET_OUT_OF_RANGE = "lut_target_out_of_range"       # lut CONTRACT 4.1·3.1 vgs_for_current_density·gm_id_for_target 사유 키
_TRANSIENT_LUT_REASONS = (_TARGET_OUT_OF_RANGE, "lut_axis_out_of_range")   # 반복 중 정의역 이탈(검증 바퀴가 다시 잰다)
_CURVE_UNDEFINED = "lut_curve_undefined"     # lut CONTRACT 4.1 -- VDS 정의역 하한(`_vds_floor`) 아래에서만 반복 중 이탈로 본다
_VDS_AXIS, _VS_AXIS = AXES.index("VDS"), AXES.index("VS")
_BOUND_RAIL, _BOUND_VDS, _BOUND_VS = "rail", "vds_axis", "vs_axis"
_SOLVE_SELF_MEMO = "solve_self"            # LUT memo root 영역의 함수 이름 칸(1변수 풀이 재사용)
_GS_STOPPED = "gauss_seidel_stopped"                  # SccLog.fallback[0]: GS 가 K_max 안 tol 도달 불가로 멈춤
FAILURES = (SealViolationError, NonconvergentError)


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


def _kind_sign(kind):
    """V(g) = V(s) + s·VGS 의 s -- `terminal_voltages` 의 부호 정의를 그대로 읽는다(정의 하나)."""
    return terminal_voltages(kind, 0.0, 1.0, 0.0, 0.0)[0]


def _vgs_of_coordinate(lut, device, kind, L, vds, vsb, ln_idu):
    """좌표 ln IDu(DEC-88)에서 VGS 크기 -- 강반전 분지 역산(lut `vgs_for_current_density`: 칸 안 Hermite 근, DEC-87)."""
    w_key = w_key_of(lut, kind)
    try:
        return vgs_for_current_density(lut.memo, kind, w_key, ln_idu, L, vds, vsb)
    except SealViolationError as exc:
        raise with_device(exc, device, "vgs_of_coordinate") from exc


class Circuit:
    """블록 한 번의 읽기 전용 입력 묶음과 writer 식."""

    def __init__(self, projection):
        theta_items, fixed_values, resistor_values, lut, *rest = projection.extras
        self.linear = frozenset(rest[0]) if rest else frozenset()      # `triode` 선언 소자 -- 창 경계 행이 triode 행(`region_rows`)
        self.override = {}                                             # {W4 입력 뿌리 넷: (lo, hi)} 입력 포화 창 (y_icm 범위)
        self.theta = dict(theta_items)
        self.fixed = dict(fixed_values)
        self.lut = lut
        self.writers = dict(projection.column("node", "dc_writer"))
        self.rail_v = dict(projection.column("node", "dc_rail_v"))
        self.nbrs = dict(projection.column("node", "dc_column_nbrs"))
        self.pins = {n: dict(p) for n, p in projection.column("device", "pins")}
        self.kinds = dict(projection.column("device", "kind"))
        self.bulk = {n: b.net for n, b in projection.column("device", "bulk")}
        self.classes = dict(projection.column("device", "element_class"))
        self.L = dict(projection.column("device", "dc_L"))
        self.current = dict(projection.column("device", "dc_drop_current"))
        self.net_colour = dict(projection.column("node", "dc_colour"))
        self.device_colour = dict(projection.column("device", "dc_colour"))
        self.coord = dict(projection.column("device", "dc_coord"))
        self.self_ref = frozenset(m for m, flag in projection.column("device", "dc_self_referential") if flag)   # 쓰기 계획 파생 S0 필드(1변수 writer)
        self.order = projection.value("graph", DC_KEY, "dc_scc_order")
        self.resistance = {n: v for n, v in resistor_values if v is not None}
        self.resistance.update({key: v for (kind, key), v in self.theta.items() if kind == THETA_RESISTANCE})
        self.ln_idu = {key: v for (kind, key), v in self.theta.items() if kind == THETA_LN_IDU}
        volts = tuple(self.rail_v.values())
        self.lo, self.hi = min(volts), max(volts)
        self.order_terms = {}
        for m in sorted(self.coord, key=lambda x: (self.device_colour.get(x, 0), x)):     # 구조 색 순서 -- 이름 치환이 항 순서(동률 tie-break)를 바꾸지 않게
            d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
            source_side, sink_side = (d, s) if _kind_sign(self.kinds[m]) > 0 else (s, d)
            self.order_terms.setdefault(source_side, []).append((True, sink_side))
            self.order_terms.setdefault(sink_side, []).append((False, source_side))
        self.tol_cells = {}                        # (소자, VDS) -> tol_V 또는 None -- `tolerance` 의 한 평가 안 재사용
        self.inputs = frozenset(net for net, d in projection.column("node", "port_direction") if d == INPUT_DIRECTION)

    def sign(self, m):
        """소자 m 의 극성 부호 s(+1 nmos / −1 pmos)."""
        return _kind_sign(self.kinds[m])

    def coordinate_vgs(self, m, vds, vsb, ln_idu):
        """소자 m 의 좌표 ln IDu 에서 VGS 크기(`_vgs_of_coordinate`)."""
        return _vgs_of_coordinate(self.lut, m, self.kinds[m], self.L[m], vds, vsb, ln_idu)

    def mos_point(self, m, values):
        """(vgs, vds, vsb) 크기 -- 네 단자 값이 모두 있어야 한다."""
        d, g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
        return terminal_voltages(self.kinds[m], values[d], values[g], values[s], values[self.bulk[m]])

    def vds_vsb(self, m, values):
        """(vds, vsb) 크기 -- gate 값을 읽지 않는다(writer 가 gate 를 쓰는 중일 수 있다)."""
        d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
        _vgs, vds, vsb = terminal_voltages(self.kinds[m], values[d], values[s], values[s], values[self.bulk[m]])
        return vds, vsb

    def kvl_window(self, net, values):
        """W4 순서 창: x 에 채널이 닿는 전도 MOS 마다 VDS ≥ 0 이 되는 쪽 -- x 가 전류가 나가는 단자면
        lo ≥ V(반대 단자), 들어오는 단자면 hi ≤ V(반대 단자). 제약이 없는 쪽은 레일 전압 범위 끝."""
        terms = self.order_terms.get(net, ())
        lo, hi = self.lo, self.hi
        for is_lower, other in terms:
            if is_lower:
                lo = max(lo, values[other])
            else:
                hi = min(hi, values[other])
        return lo, hi, len(terms)

    def window(self, net, values):
        """W4 창 = 순서 창 ∩ (입력 뿌리면) 입력 포화 창 `override`(y_icm 범위, `input_windows`가 정한다)."""
        lo, hi, ncols = self.kvl_window(net, values)
        if net in self.override:
            lo, hi = max(lo, self.override[net][0]), min(hi, self.override[net][1])
        return lo, hi, ncols

    def canonical_writers(self):
        """(넷, writer) 를 쓰기 순번 순으로 -- 이름순이 아니다(이름 치환이 행·합산 순서를 바꾸지 않게)."""
        return sorted(self.writers.items(), key=lambda kv: kv[1].order)

    def input_roots(self):
        """입력 포트인 W4 뿌리 넷(y 키 = 그 넷; 입력 DC 미선언 회로, `dc_writer_plan` 이 둘 이상이면 정지시킨다 -- 최대 하나) -- 쓰기 순번 순."""
        return tuple(net for net, w in self.canonical_writers() if w.relation == REL_WINDOW and net in self.inputs)

    def declared_inputs(self):
        """입력 DC 가 선언된 입력 포트 넷(writer 관계 `input_dc` -- x 를 따로 두는 포트) -- 쓰기 순번 순."""
        return tuple(net for net, w in self.canonical_writers() if w.relation == REL_INPUT_DC and net in self.inputs)

    def writer_head(self, net):
        """net 의 writer 사슬(`known` 을 거슬러) 끝 넷과 그 관계: 고정 노드(F)면 F 성분, `free_window` 면 그 W4 뿌리의 성분."""
        w = self.writers[net]
        while w.relation not in FIXED_RELATIONS and w.relation != REL_WINDOW:
            net = w.known
            w = self.writers[net]
        return net, w.relation

    def region_rows(self, values):
        """창 경계 행 셋(설계 41 4.7-3a 1): 전도 MOS 마다 `(a, b, sign, slack, kind)`, kind ∈ {"sat", "triode"}. LUT 에 VDSAT 열이 없거나 tol 이 미정이면
        그 판정을 할 수 없어 None(창을 좁히지 않는다 -- 종래 사상)."""
        out = []
        for m in sorted(self.coord, key=lambda x: (self.device_colour.get(x, 0), x)):
            kind = self.kinds[m]
            d, _g, s = (self.pins[m][t] for t in MOS_TERMINAL_NAMES)
            vgs, vds, vsb = self.mos_point(m, values)
            w_key = w_key_of(self.lut, kind)
            try:
                sat = vdsat(self.lut.memo, kind, w_key, self.L[m], vgs, vds, vsb)
                tol = tol_vdsat_table(self.lut.memo, kind, w_key).at(self.L[m], vds)
            except SealViolationError:
                return None
            if tol is None:
                return None
            sign = _kind_sign(kind)
            if m in self.linear:
                out.append((d, s, -sign, sat - vds - tol, ROW_TRIODE))
            else:
                out.append((d, s, sign, vds - sat - tol, ROW_SAT))
        return tuple(out)

    def input_windows(self, values, roots):
        """해 `values` 에서 잰 이동량 창과 감도 `(dlo, dhi, slope)`(`saturation_window`) -- `roots` = x 로 함께 움직이는 넷 tuple(커널 뿌리 하나 또는 입력 DC
        선언 포트 묶음 -- 설계 41 4.7-3 2·3). 고정 노드 가운데 roots 의 넷은 미지수로 넣는다(그 행은 s = 1). 잴 수 없으면 None."""
        rows = self.region_rows(values)
        if rows is None:
            return None
        moving = frozenset(r for r in roots if isinstance(r, str))
        unknown = tuple(net for net, w in self.canonical_writers() if w.relation not in FIXED_RELATIONS or net in moving)     # 쓰기 순번 순 -- 선형 연립 행 순서가 이름을 따르지 않게
        return saturation_window(unknown, roots, values, self.writer_grad, rows)

    def port_window(self, value, slope, dlo, dhi):
        """포트 창 = 두 끝 전압 V + s·dlo, V + s·dhi 의 [min, max] ∩ [레일 최소, 레일 최대](설계 41 4.7-3 2: 감도 음수 포트는 아래 끝이 위 끝이 된다).
        감도 0 이면 포트가 x 를 따라 움직이지 않으므로 두 끝이 모두 V 다."""
        if slope == 0:
            a = b = value
        else:
            a, b = value + slope * dlo, value + slope * dhi
        return max(min(a, b), self.lo), min(max(a, b), self.hi)

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
            sign = _kind_sign(self.kinds[m])
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
        sign = _kind_sign(kind)
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
            sign = _kind_sign(self.kinds[m])
            return values[w.known] + sign * vgs if w.relation == REL_VGS_GATE else values[w.known] - sign * vgs
        if w.relation == REL_RESISTOR:
            return values[w.known] + self.drop(w.element, w.known, net)
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
            sign = _kind_sign(kind)
            grad = {}
            for node, value in ((w.known, 1.0), (d, sigma * dvgs_dvds), (s, sigma * (dvgs_dvsb - dvgs_dvds)),
                                (self.bulk[m], -sigma * dvgs_dvsb)):
                grad[node] = grad.get(node, 0.0) + value
            return values[w.known] + sign * sigma * vgs, grad
        if w.relation == REL_RESISTOR:
            return values[w.known] + self.drop(w.element, w.known, net), {w.known: 1.0}
        terms = self.order_terms.get(net, ())
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


def solve(c):
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
