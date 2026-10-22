"""④ 노드전압 정본 풀이 계산 블록 -- 쓰기 계획대로 SCC 위상 순서로 노드전압을 쓰고 종속 소자 좌표를 순방향으로 정한다
(설계 3.2 3·3.3·3.4, 계획 DEC-31 노드전압 = DC 정본, N3.4, SC-c, DEC-88).

진입점: `dc_columns`(`@compute_block`) -- `dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)`.

* 풀이 본체(`Circuit`·`solve`·`FAILURES`)는 `_helpers_dc_solve.py` 에 있다(다듬은 창 블록과 공용, 설계 41 4.7-4). 이 파일은 블록 진입점과 입력 창 되풀이(A6)·
  입력 포트 창 만들기만 갖는다.
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
* **커널 창 `node.dc_window`**(설계 41 4.7-2·4.7-3, 카드 IT-2b): W4 뿌리 + 모든 입력 포트. 입력 포트가 아닌 W4 뿌리는 순서 창(`input_status` None).
  (1) 입력 포트인 W4 뿌리(최대 하나): A6 -- y = 1/2 풀이 → 창 측정 → 창을 y 범위(`override`)로 두고 다시 풀며 경계가 tol 안에서 같아질 때까지(상한 `k_max`)
  되풀이. 수렴하면 `measured`, 수렴하지 않았거나(c) tol 미정(b)이면 `unsettled`(y 범위는 그대로 쓴다), 창을 못 재면(a) `unmeasured`(순서 창).
  (2) 뿌리 아닌 입력 포트(같은 성분): 뿌리 창 끝을 마지막 `override` 를 잰 같은 해의 감도로 옮긴 두 끝 전압 [min, max] ∩ 레일. (3) 입력 DC 선언 포트: 묶음
  전부가 같은 x 이동량 Δ 로 함께 움직이는 창(`saturation_window` roots = 선언 포트 묶음), 포트 창 = 선언값 + Δ 의 [min, max] ∩ 레일. F 성분에 속한 입력 DC
  미선언 포트는 `f_component_undeclared`(lo·hi None). (4) 측정 실패는 뿌리 항목만 `unmeasured`(뿌리 아닌 포트·선언 포트 항목 없음). 끝 다듬기(끝 x 고정 Newton)는 이
  블록이 하지 않는다(다듬은 창 블록 몫). (5) 동작점 불일치(`op_mismatch`)는 이 card 밖이다(EO-1 묶음, 사용자 결정 O-98).
* writes `node.dc_v`(레일 밖 모든 노드), `node.dc_path_values`(모든 노드), `node.dc_window`(W4 뿌리 + 입력 포트),
  `device.dc_ln_idu`(모든 MOS), `graph.dc_scc_log`.
"""
import dataclasses
import math

from gmid_engine.core import SealViolationError, compute_block
from gmid_engine.graph import MOS_TERMINAL_NAMES

from ._helpers_dc_solve import FAILURES, Circuit, solve
from ._helpers_lut import forward_point, tol_v_cell
from .k_max import k_max
from .scc_order import FIXED_RELATIONS
from .s2_values import (
    COORD_WRITER,
    DC_COLUMNS_WRITER,
    DC_KEY,
    INPUT_STATUS_F_COMPONENT_UNDECLARED,
    INPUT_STATUS_MEASURED,
    INPUT_STATUS_UNMEASURED,
    INPUT_STATUS_UNSETTLED,
    PATH_FIXED,
    PATH_MOS,
    PATH_RESISTOR,
    PATH_Y,
    REL_INPUT_DC,
    REL_RESISTOR,
    REL_VGS_GATE,
    REL_VGS_SOURCE,
    REL_WINDOW,
    THETA_Y,
    PathValue,
    Window,
)

READS = (
    ("node", "dc_writer"), ("node", "dc_rail_v"), ("node", "dc_column_nbrs"),
    ("device", "dc_drop_current"), ("node", "dc_colour"), ("device", "dc_colour"), ("device", "dc_L"), ("device", "pins"), ("device", "kind"), ("device", "bulk"),
    ("device", "element_class"), ("device", "dc_coord"), ("graph", "dc_scc_order"), ("device", "dc_self_referential"),
    ("node", "port_direction"),
)
WRITES = (("node", "dc_v"), ("node", "dc_path_values"), ("node", "dc_window"), ("device", "dc_ln_idu"),
          ("graph", "dc_scc_log"))
_REL_MOS, _REL_RES, _REL_FIXED, _REL_Y = PATH_MOS, PATH_RESISTOR, PATH_FIXED, PATH_Y
_MID = 1 / 2                                         # y_icm 창을 재기 시작하는 해의 위치(순서 창 한가운데)
_HALVING = round(1 / _MID)                          # 분모가 늘어나는 비 -- 구간을 이분하는 수(1/2 다음 후보 열)


@dataclasses.dataclass(frozen=True)
class _Measured:
    """한 해에서 잰 입력 뿌리 창: `window` = (순서 창 ∩ 잰 창) 끝 전압, `slope` = 그 연립의 감도 {넷: dV/dx}, `values` = 그 해(뿌리 아닌 포트 창이
    같은 해의 값끼리만 쓴다 -- 설계 41 4.7-3 2). 한 `dc_columns` 호출 안에서만 산다."""

    window: tuple
    slope: dict
    values: dict


@dataclasses.dataclass(frozen=True)
class _Kernel:
    """커널 풀이 결과: 마지막 풀이 `values`·`logs`, 입력 뿌리의 `status`(뿌리가 없으면 None)와 `tol`, 마지막 측정 `measured`(못 쟀으면 None)."""

    values: dict
    logs: tuple
    status: object
    tol: object
    measured: object


def _dyadic_ys(count):
    """y 후보 열 1/4, 3/4, 1/8, 3/8, 5/8, 7/8, ... (앞 `count` 개) -- 구간을 이분 수준마다 훑는 순서(1/2 는 이미 해 봤다)."""
    out, level = [], _HALVING
    while len(out) < count:
        out.extend(k / level for k in range(1, level, _HALVING))
        level *= _HALVING
    return out[:count]


def _measure(c, root, values):
    """해 `values` 에서 입력 뿌리 `root` 의 입력 포화 창 -- 순서 창 ∩ (뿌리 전압 + 잰 이동량 창). 잴 수 없으면 None."""
    found = c.input_windows(values, (root,))
    if found is None:
        return None
    dlo, dhi, slope = found
    lo, hi, _ncols = c.kvl_window(root, values)
    return _Measured((max(lo, values[root] + dlo), min(hi, values[root] + dhi)), slope, values)


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
            values, logs = solve(c)
        except FAILURES:
            continue
        finally:
            c.theta[key] = requested
        measured = _measure(c, root, values)
        if measured is not None:
            return values, logs, measured
    return None


def _root_windows(c, roots, values):
    """{뿌리: (lo, hi)} -- 해 `values` 에서 잰 입력 포화 창. 하나라도 잴 수 없으면 None."""
    out = {}
    for root in roots:
        measured = _measure(c, root, values)
        if measured is None:
            return None
        out[root] = measured.window
    return out


def _refine_ends(c, roots, windows, tol):
    """창 끝을 끝에서 다시 푼다 (뉴턴 -- 끝에서 잰 1차 외삽은 오차가 이차). 끝 x 에 입력을 고정(창 (x, x))해 풀고 그 해에서 창을 다시 재
    (a) x 가 잰 창 안(봉인 7 의 포화 여유 ≥ 0 과 같은 식)이고 (b) 잰 끝과 x 의 차가 tol 이하이면 x 를 끝으로 삼는다 -- 그 점은 풀려 있고 여유가 음수가 아니다.
    아니면 잰 끝을 다음 x 로 쓴다. 풀리지 않으면 지금까지의 끝을 둔다. 상한 k_max(레일 폭, tol). 끝이 무한이면(제약 없음) 손대지 않는다."""
    refined = {root: list(w) for root, w in windows.items()}
    for side in (0, 1):
        inward = 1.0 if side == 0 else -1.0                 # 아래 끝은 x 가 잰 끝 이상이어야 안, 위 끝은 이하
        for _ in range(k_max(c.hi - c.lo, tol)):
            ends = {root: refined[root][side] for root in roots}
            if not all(math.isfinite(x) for x in ends.values()):
                break
            c.override = {root: (x, x) for root, x in ends.items()}
            try:
                values, _logs = solve(c)
            except FAILURES:
                break
            again = _root_windows(c, roots, values)
            if again is None:
                break
            inside = all(inward * (ends[root] - again[root][side]) >= 0 for root in roots)
            close = all(abs(again[root][side] - ends[root]) <= tol for root in roots)
            if inside and close:
                break
            for root in roots:
                refined[root][side] = again[root][side]
    return {root: tuple(w) for root, w in refined.items()}


def _solve_input_window(c):
    """입력 DC 대기 회로의 y_icm 범위 = 입력 포화 창 (사용자 결정 J-E, 설계 41 §4.6 SP-2 (c), 4.7-3 1).

    입력 포트인 W4 뿌리가 없으면 풀이 한 번(종래). 있으면: (1) y_icm = 1/2 로 풀어 해를 얻고(순서 창 사상; 풀리지 않으면 순서 창 안에서 풀리는
    점을 찾는다) (2) 그 해에서 잰 포화 창 [Vin,min, Vin,max] ∩ 순서 창을 y_icm 범위로 삼아 요청 y_icm 으로 다시 풀며 (3) 새 해에서 창을 다시 재
    경계가 tol 안에서 같아질 때까지 되풀이한다(상한 K_max = `k_max`(레일 폭, tol)). 끝 다듬기는 하지 않는다(커널 창은 선형 감도 끝, 설계 41 4.7-3 1).
    (1) 이 어디서도 풀리지 않거나 창을 잴 수 없으면(VDSAT 열 없음·tol 미정) 종래 사상(요청 y_icm, 순서 창)으로 푼다 -- 종래보다 나빠지지 않는다.
    상태: 되풀이가 tol 안에서 수렴하면 `measured`, 수렴하지 않았거나 tol 미정이면 `unsettled`(창은 잰 해에서 쟀으니 y 범위로는 쓴다), 창을 못 재면 `unmeasured`."""
    roots = c.input_roots()
    if not roots:
        values, logs = solve(c)
        return _Kernel(values, logs, None, None, None)
    (root,) = roots
    key = (THETA_Y, c.writers[root].y_key)
    requested = c.theta[key]
    c.theta[key] = _MID
    try:
        values, logs = solve(c)
        measured = _measure(c, root, values)
    except FAILURES:
        measured = None
    finally:
        c.theta[key] = requested
    if measured is None:
        found = _interior_solution(c, key, requested)
        if found is None:
            values, logs = solve(c)
            return _Kernel(values, logs, INPUT_STATUS_UNMEASURED, None, None)
        values, logs, measured = found
    tol = _tolerance(c, values)
    if tol is None:                                    # tol 이 어느 소자에서도 미정 -- 되풀이 수렴 판정을 할 수 없다(창은 한 번만 적용)
        c.override = {root: measured.window}
        values, logs = solve(c)
        return _Kernel(values, logs, INPUT_STATUS_UNSETTLED, None, measured)
    settled = False
    for _ in range(k_max(c.hi - c.lo, tol)):
        c.override = {root: measured.window}
        values, logs = solve(c)
        again = _measure(c, root, values)
        if again is None:
            break
        settled = all(abs(a - b) <= tol for a, b in zip(again.window, measured.window))
        measured = again
        if settled:
            break
    c.override = {root: measured.window}
    values, logs = solve(c)
    return _Kernel(values, logs, INPUT_STATUS_MEASURED if settled else INPUT_STATUS_UNSETTLED, tol, measured)


def _windows(c, values, kernel):
    """`node.dc_window` -- W4 뿌리 + 모든 입력 포트(설계 41 4.7-2·4.7-3). 뿌리 아닌 입력 포트·입력 DC 선언 포트는 순서 창이 없어 `constraints` 0."""
    out = {}
    for net, w in c.writers.items():
        if w.relation == REL_WINDOW:
            lo, hi, ncols = c.window(net, values)
            out[net] = Window(lo, hi, ncols, kernel.status, kernel.tol) if net in c.inputs else Window(lo, hi, ncols)
    group = c.declared_inputs()
    if group:                                          # x 를 따로 두는 선언 포트: 묶음 전체가 같은 이동량 Δ (측정 실패면 항목 없음)
        found = c.input_windows(values, group)
        if found is not None:
            dlo, dhi, slope = found
            tol = _tolerance(c, values)
            status = INPUT_STATUS_MEASURED if tol is not None else INPUT_STATUS_UNSETTLED
            for net in group:
                lo, hi = c.port_window(values[net], slope[net], dlo, dhi)
                out[net] = Window(lo, hi, 0, status, tol)
    for net, w in c.canonical_writers():               # 입력 DC 미선언인 뿌리 아닌 입력 포트
        if net not in c.inputs or w.relation in (REL_WINDOW, REL_INPUT_DC):
            continue
        head, relation = c.writer_head(net)
        if relation in FIXED_RELATIONS:                # F 성분에 속한 포트 -- 창이 정의되지 않는다(fail-closed)
            out[net] = Window(None, None, 0, INPUT_STATUS_F_COMPONENT_UNDECLARED)
        elif kernel.measured is not None:              # 뿌리 성분의 포트 -- 뿌리 창 끝을 같은 해의 감도로 옮긴다
            lo_x, hi_x, _ncols = c.window(head, values)
            x_k = kernel.measured.values[head]
            lo, hi = c.port_window(kernel.measured.values[net], kernel.measured.slope.get(net, 0.0), lo_x - x_k, hi_x - x_k)
            out[net] = Window(lo, hi, 0, kernel.status, kernel.tol)
    return {net: out[net] for net in c.writers if net in out}


@compute_block(DC_COLUMNS_WRITER, reads=READS, writes=WRITES)
def dc_columns(projection):
    c = Circuit(projection)
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
        vgs = c.coordinate_vgs(m, vds, vsb, ln_idu[m])
        sign = c.sign(m)
        paths[g].append(PathValue((_REL_MOS, m), values[s] + sign * vgs))
        paths[s].append(PathValue((_REL_MOS, m), values[g] - sign * vgs))
    for net, w in c.writers.items():
        if w.relation == REL_RESISTOR:
            far_from_near = c.drop(w.element, w.known, net)
            paths[net].append(PathValue((_REL_RES, w.element), values[w.known] + far_from_near))
            paths[w.known].append(PathValue((_REL_RES, w.element), values[net] - far_from_near))
        elif w.relation == REL_WINDOW:
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
