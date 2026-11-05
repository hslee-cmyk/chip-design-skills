"""층 0 최소형 시작점 -- θ 상자 중심에서 출발한 봉인 여유 최대-최소 점 (계획 DEC-71 최소형 = R D18·U-49·PUD DF-10,
오케스트레이터 결정 2026-10-08 'feasibility centering').

진입점: `layer0_start(sctx, origin=()) -> Layer0Result`(S0 당 1회, `find_front` 가 부른다 -- 결과 시작점은 `start_points` 의
첫 후보, 출처 "layer0").

최소형의 범위: DC 정합(봉인 통과) 시작점 하나. 블록 gain 예산(GB3 블록 분해·GB4 상한표)·LR5 knee·GB5 근사식·슬루 선언은
쓰지 않는다 -- 그것들은 최소형 밖의 정밀화다(U-49·D18). 입력은 선언·유도된 것만: θ 상자(`SearchDomain`), 봉인 항목 margin
(sizing 봉인 보고), 탐색 제약 행(W 하한·반전 하한·전류 원뿔).

1. **상자 중심**(자연 좌표): 변수마다 bounds 중점 -- ln 좌표 변수(전류·저항)는 ln 중점(= 기하 중심), `ln_idu` 는 그 좌표의
   중점, `y` 는 창 중앙. L 은 소자마다 L 칸(PDK bin 안 LUT 점 구간) 중 칸의 ln 중점이 전체 L 범위 [최소 칸 lo, 최대 칸 hi] 의
   ln 중점에 가장 가까운 칸(동률은 index 작은 쪽)을 고르고, 그 칸 안 L 은 칸 중점(bin 안 L 은 선형 보간 좌표라 선형 중점).
2. **전류 중심**(커널 0): MOS 전류는 θ 전류의 선형식(`schema.current_cone`)이라 상자 중심이 원뿔 밖일 수 있다(차 전류 행).
   그래서 θ 전류 변수만 움직여 'MOS 전류가 그 kind 전류 상자의 기하 중심에서 ln 거리로 가장 덜 벗어나는 점'(Chebyshev 중심)
   을 푼다: 최소화 u, 제약 I_m/I_c,m − e^(−u) ≥ 0, e^u − I_m/I_c,m ≥ 0(원뿔의 MOS 행 중 θ 전류를 하나라도 읽는 행 -- 값 선언
   이상원만 읽는 행은 움직일 수 없어 뺀다), I_c,m = 그 MOS kind 의
   `SearchDomain.current_box` 기하 중심. 기저 원소가 MOS 하나뿐인 행은 상자 중심에서 u = 0 이라 1 의 중심과 같다.
   수렴 판정은 scipy SLSQP 기본값(이 문제는 커널이 없어 판정 분해능 단위가 없다 -- 부동소수 수준).
   끌어올림(출발 사다리 칸의 `current_ref` 가 있을 때만): 풀이기 해 x 에서 행마다 q_m(s) = A_m·e^s + F_m 을 놓고 e^s = max_{A_m>0}(1 + √ε − F_m)/A_m (s = max(0, ln 그 값), √ε =
   `math.sqrt(sys.float_info.epsilon)`)로 움직이는 θ 전류를 모두 e^s 배 한다 -- 가장 낮은 행이 q = 1 + √ε 의 경계 배치점이 된다(BP1, 풀이기 목적값 u 는 쓰지 않아 풀이기 잡음이 경계
   부호를 정하지 않는다; 41 §5.13).
3. **최대-최소**(커널): 시작점을 평가해 받아들일 상태(봉인 통과·봉인 7 대기)가 아니면(전류 중심이 원뿔 밖이어도) [S-4b,
   오케스트레이터 결정 2026-10-08] 같은 변수·같은 L 칸에서 Halton 열(스크램블 없음, [r11] 차원 = 이름 없는 정준 (종류, 구조 색) 키 -- CONTRACT 3.21 3a) 점을 순서대로 평가해 처음 받아들일 상태인
   점을 출발점으로 삼는다(`_halton_probe` -- 한도는 평가 예산 규칙). 그래도 없으면 끝(`start_<사유>+probe_<한도>`, 층 0 시작점
   없음). 받아들일 상태면 변수 x(정의역 연속 변수 + 칸이 구간인 L) 와 t 로
   최대화 t, 제약 s_i(x) − t ≥ 0(봉인 항목 i = 1..8 중 시작점 margin 이 유한한 항목, s_i = 1 − margin_i -- margin ≤ 1 이 pass
   이므로 s_i ≥ 0 ⇔ pass, 단위는 그 항목 허용오차), 그리고 경성 제약 c ≥ 0: W 하한(`w_min`)·반전 하한(`inversion_floor`)·
   전류 원뿔(`current_cone`) 행. 원뿔·W 하한 행은 판정 분해능 단위가 봉인 margin 과 달라(원뿔 c ≤ 1, W 는 제조 격자 칸)
   최소값 경쟁에 넣지 않는다 -- 넣으면 원뿔 c → 1(한 전류 → 꺼짐 전류)로 끌린다. 목적 −t 의 수렴 판정 = SLSQP ftol 1(t 의
   단위 = 허용오차 한 칸, `solve_eps` 와 같은 규칙).
   * fun·jac·constraints 는 같은 x 의 같은 평가(x float.hex 로 묶음 -- 커널 1회), jac 은 `fd_jacobian`(parent = 그 x 의 평가),
     x 평가의 parent = 직전 수락 반복. t 열은 해석적(−1/0).
   * 한도·실패 처리는 `solve_eps` 와 같다: maxiter = Σᵢ ⌈log2((hiᵢ − loᵢ)/hᵢ)⌉, 받아들일 상태가 아니거나 행 이름 집합이 바뀌면
     마지막 수락 반복 중심으로 상자 반경을 절반으로 재시작(상한 ⌈log2(최대 반경/최소 hᵢ)⌉), FD 열 양방향 실패는 그 변수 고정,
     평가 예산·벽시계 도달은 끝.
4. 결과 시작점 = 수락 반복 중 (경성 제약 모두 ≥ 0, min s_i 최대, seq 작은 쪽) 순으로 가장 좋은 점. 커널 결과는 평가 캐시에
   있어 `start_points` 의 재확인은 캐시 적중(커널 0)이다.
"""
import dataclasses
import math
import sys

import numpy as np
from scipy.optimize import minimize as scipy_minimize

from gmid_engine.core import blas_environment
from gmid_engine.sizing import KERNEL_KEY, REASON_NO_ROOT, THETA_CURRENT, THETA_L, THETA_LN_IDU

from .canonical_order import canonical_order
from .canonical_rows import canonical_row_key
from .cell_floor import ln_idu_floors
from .cone_rows import cone_rows
from .fd_jacobian import FdBudgetShortfall, fd_jacobian
from .kernel import evaluate
from .search_ceiling import search_ceiling
from .search_stop import search_stop
from .tie_expand import expand_ties
from .search_values import (
    ACCEPTED_STATUSES,
    CON_CONE,
    CON_INVERSION,
    CON_WMIN,
    STATUS_FAILED,
    StartPoint,
    Variable,
)
from .theta_coords import ThetaCoords

SOURCE_LAYER0 = "layer0"
STAGE_LAYER0 = "layer0"
ROW_SEAL_ITEM = "seal_item"
_HARD_PREFIXES = (CON_WMIN + ":", CON_INVERSION + ":")


@dataclasses.dataclass(frozen=True)
class Layer0Result:
    """층 0 결과. `start` = StartPoint(출처 "layer0") 또는 None, `t` = 그 점의 min s_i(봉인 여유, 허용오차 단위) 또는 None,
    `hard_ok` = 그 점의 경성 제약(W 하한·반전 하한·원뿔)이 모두 ≥ 0, `stop` = 종료 사유, `centre_u` = 전류 중심 문제의 해 u
    (MOS 전류의 상자 중심 대비 최대 ln 편차, θ 전류가 없으면 None), `start_status` = 출발점 평가 상태, `start_failure` = 그
    FailureRecord 또는 None, `iterations`·`restarts`·`aborts`·`frozen` = 최대-최소 풀이 기록, `kernel_calls` = 이 단계의 커널
    평가 수, `rows` = t 행 이름(봉인 항목) tuple, `probes` = S-4b Halton 시험 점 수(중심이 받아들여졌으면 0), `origin_point` =
    최대-최소 출발점 출처("centre" 또는 "halton:<k>", 시작점 없으면 None).

    **의미 한정**: 층 0 시작점은 DC 정합(봉인 통과) 가능성만 뜻한다 -- W·면적 상한 선언이 없어(S-3b) pA 전류·거대 W 점일 수
    있고, 탐색은 그 점을 출발 근거 이상으로 쓰지 않는다(front·보고 값이 아니다)."""

    start: object
    t: object
    hard_ok: bool
    stop: str
    centre_u: object
    start_status: str
    start_failure: object
    iterations: int
    restarts: int
    aborts: tuple
    frozen: tuple
    kernel_calls: int
    rows: tuple
    probes: int
    origin_point: object
    repairs: tuple = ()


class _Abort(Exception):
    """최대-최소 SLSQP 실행을 끊는 내부 신호. 이 파일 밖으로 나가지 않는다."""

    def __init__(self, reason, x=None, column=None):
        super().__init__(reason)
        self.reason = reason
        self.x = x
        self.column = column


def _schema(sctx):
    """θ 스키마(S0 수준 필드 `graph/kernel: theta_schema`)."""
    return sctx.dc.base.value("graph", KERNEL_KEY, "theta_schema")


def _selected(sctx):
    """출발 구간의 선택점 = 출발 사다리 칸 0(`StartRung`), 사다리가 없으면 None."""
    rungs = sctx.rungs
    return rungs[0] if rungs else None


def _box_centre(sctx, rung=None):
    """출발 θ 의 기반. [U13] 출발 사다리 칸 0(`graph/start: rungs` -- `start_intervals` 가 스펙에서 유도한 gm/ID·L·전류 출발 구간의 선택점)이 값을 정한 성분(ln_idu·θ 전류·보상 커패시터·L 과 그 L 칸)은 그 값을 쓴다.
    구간이 값을 정하지 못한 성분(`y`, 저항, 또는 `start` 가 None 인 컨텍스트 전부)은 상자 중심 -- bounds 중점(ln 좌표 변수는 ln 중점, `y` 는 창 중앙), L 은 칸 ln 중점이
    전체 L 범위의 ln 중점에 가장 가까운 칸의 중점. 이 상자 기하 중점은 ln IDu 가 LUT 가 정의되지 않는 영역(예: −26~−34)으로 가고 면적이 예산의 12~99 배인 퇴화점을 만들었다(41 §6 상태 MISS)."""
    variables = list(sctx.domain.variables)
    theta = {v.component: (math.exp((v.lo + v.hi) / 2) if v.log else (v.lo + v.hi) / 2) for v in variables}
    start = _selected(sctx) if rung is None else rung          # 선택점 = 사다리 칸 0(StartRung)
    given = {} if start is None else dict(start.theta)
    chosen_cell = {} if start is None else dict(start.cells)
    theta.update({component: value for component, value in given.items() if component in theta})
    cells = []
    for mos, table in sctx.domain.l_cells:
        if mos in chosen_cell and (THETA_L, mos) in given:
            j = chosen_cell[mos]
            lo, hi = table[j]
            cells.append(j)
            theta[(THETA_L, mos)] = min(max(given[(THETA_L, mos)], lo), hi)
            if lo < hi:
                variables.append(Variable((THETA_L, mos), False, lo, hi))
            continue
        mid = (math.log(min(c[0] for c in table)) + math.log(max(c[1] for c in table))) / 2
        j = min(range(len(table)), key=lambda i: (abs((math.log(table[i][0]) + math.log(table[i][1])) / 2 - mid), i))
        lo, hi = table[j]
        cells.append(j)
        theta[(THETA_L, mos)] = (lo + hi) / 2
        if lo < hi:
            variables.append(Variable((THETA_L, mos), False, lo, hi))
    variables, _dim, _n = canonical_order(sctx, variables)      # [r11] 이름 없는 정준 순서 (CONTRACT 3.23)
    return tuple(variables), theta, tuple(cells)


def _cone_canonical(sctx):
    """원뿔 행·항을 이름 없는 정준 순서로(행 = MOS 궤도 id, 항 = 원천 원소 궤도 id) -- SLSQP 제약·합산 순서가 이름을 따르지 않게(3.25)."""
    key = canonical_row_key(sctx)
    rows = sorted(_schema(sctx).current_cone, key=lambda row: key(CON_CONE + ":" + row[0]))
    return tuple((m, tuple(sorted(terms, key=lambda t: key(CON_CONE + ":" + t.source)))) for m, terms in rows)


def _expanded(sctx, theta):
    return expand_ties(sctx.domain.ties, theta, sctx.domain.negated, sctx.domain.zeros)


def _current_alias(sctx):
    """{묶인 θ 전류 원소: (대표 원소, 부호)}: 원뿔 행의 항이 묶인 전류를 읽으면 대표 변수의 항(부호만큼 곱함)으로 센다(3.24)."""
    flipped = set(sctx.domain.negated)
    return {m[1]: (rep[1], -1.0 if m in flipped else 1.0) for rep, members in sctx.domain.ties if rep[0] == THETA_CURRENT
            for m in members}


def _current_fixed(sctx):
    """고정 전류원 값 ∪ 구조적 0 θ 전류(값 0): 원뿔 행에서 변수가 아닌 상수로 읽히는 항."""
    out = {name: float(v) for name, v in _schema(sctx).fixed}
    out.update({component[1]: 0.0 for component in sctx.domain.zeros if component[0] == THETA_CURRENT})
    return out


def _current_centre(sctx, variables, theta, rung=None):
    schema = _schema(sctx)
    index = [i for i, v in enumerate(variables) if v.component[0] == THETA_CURRENT]
    if not index or not schema.current_cone:
        return theta, None
    start = _selected(sctx) if rung is None else rung
    covered = set() if start is None else {c for c, _v in start.theta}
    fixed = _current_fixed(sctx)
    fixed.update({variables[i].component[1]: theta[variables[i].component] for i in index if variables[i].component in covered})
    index = [i for i in index if variables[i].component not in covered]      # [U13] 출발 구간이 정한 θ 전류는 상수로 읽고 나머지만 Chebyshev 중심을 푼다
    if not index:
        return theta, None
    kinds = dict(sctx.dc.base.column("device", "kind"))
    box = dict(sctx.domain.current_box)
    ref = {m: math.sqrt(box[kinds[m]][0] * box[kinds[m]][1]) for m, _t in schema.current_cone}
    if start is not None:                           # [U13] 전류를 정하지 못한 소자의 기준 전류 = 선택 점에서 최소 폭 소자의 전류(상자 기하 중심 대신)
        ref.update({m: v for m, v in start.current_ref if m in ref})
    pos = {variables[i].component[1]: k for k, i in enumerate(index)}
    # θ 전류를 하나도 읽지 않는 행(값 선언 이상원만으로 정해지는 MOS 전류)은 움직일 수 없으므로 편차 경쟁에서 뺀다 -- 넣으면
    # u 가 그 고정 편차로 정해져 나머지 행이 느슨해진다(원뿔 경계까지 허용).
    alias = _current_alias(sctx)
    rows = tuple((m, tuple((float(t.num) / t.den * alias.get(t.source, (t.source, 1.0))[1], alias.get(t.source, (t.source, 1.0))[0])
                           for t in terms))
                 for m, terms in _cone_canonical(sctx) if any(alias.get(t.source, (t.source, 1.0))[0] in pos for t in terms))
    n = len(index)

    def currents(z):
        x = {name: math.exp(z[k]) for name, k in pos.items()}
        out = []
        for m, terms in rows:
            out.append(sum(w * (x[s] if s in x else fixed[s]) for w, s in terms) / ref[m])
        return np.asarray(out, dtype=float)

    def d_currents(z):
        out = np.zeros((len(rows), n))
        for r, (m, terms) in enumerate(rows):
            for w, s in terms:
                if s in pos:
                    out[r, pos[s]] += w * math.exp(z[pos[s]]) / ref[m]
        return out

    def cons(v):
        q = currents(v[:n])
        return np.concatenate([q - math.exp(-v[n]), math.exp(v[n]) - q])

    def cons_jac(v):
        dq = d_currents(v[:n])
        lower = np.hstack([dq, np.full((len(rows), 1), math.exp(-v[n]))])
        upper = np.hstack([-dq, np.full((len(rows), 1), math.exp(v[n]))])
        return np.vstack([lower, upper])

    z0 = [math.log(theta[variables[i].component]) for i in index]
    q0 = currents(z0)
    u0 = max((abs(math.log(q)) for q in q0 if q > 0), default=0.0)
    # u 의 상한 = 부동소수 범위(e^u·e^−u 가 둘 다 유한) -- 상한이 없으면 SLSQP 선 탐색이 e^u 를 넘쳐 OverflowError(변수·행 순서가 바뀌면 드러난 잠복 결함)
    bounds = [(variables[i].lo, variables[i].hi) for i in index] + [(0.0, math.log(math.sqrt(sys.float_info.max)))]
    grad = np.zeros(n + 1)
    grad[n] = 1.0
    out = scipy_minimize(lambda v: v[n], np.asarray(z0 + [u0], dtype=float), jac=lambda v: grad, method="SLSQP",
                         bounds=bounds, constraints=[{"type": "ineq", "fun": cons, "jac": cons_jac}])
    u = float(out.x[n])

    def lift_exponent(z):
        # [NFR-4 BP1, 41 §5.13] 끌어올림 닫힌 식. 행 m 의 q_m(s) = A_m·e^s + F_m (A_m = 움직이는 θ 전류 항 / 기준 전류, F_m = 고정 항 / 기준 전류). 풀이기 목적값 u 는 쓰지 않는다 --
        # 풀이기 해 z 는 '어느 행이 경계에 놓이는가'를 고르는 데만 쓰고 경계 좌표는 선언량(계수·고정 전류·기준 전류)의 닫힌 식에서 나온다. 가장 낮은 행이 q = 1 + √ε(부동소수 여유,
        # 판정 쪽 안쪽)에 놓이고 A_m > 0 인 나머지 행은 그 이상이다. A_m > 0 행이 없거나 분자가 모두 ≤ 0 이면 식이 정의되지 않아 올리지 않는다. s < 0 도 올리기만 하는 as-built 와 같이 0.
        margin = 1.0 + math.sqrt(sys.float_info.epsilon)
        ratio = 0.0
        for m, terms in rows:
            moving = sum(w * math.exp(z[pos[s]]) / ref[m] for w, s in terms if s in pos)
            if moving > 0:
                still = sum(w * fixed[s] / ref[m] for w, s in terms if s not in pos)
                ratio = max(ratio, (margin - still) / moving)
        return math.log(ratio) if ratio > 1.0 else 0.0

    # [U13] 기준 전류가 '폭 = W_min 인 전류 이상'(`StartRung.current_ref`)일 때만 움직이는 θ 전류를 모두 e^s 배 올려 모든 MOS 가 기준 이상(= 폭 ≥ W_min)이 되게 한다(적용 조건 as-built).
    # 원뿔(행 합이 양수)이 깨지면(고정 전류·음의 계수) 올리지 않는다.
    lift = lift_exponent(out.x[:n]) if start is not None and start.current_ref else 0.0
    for scale in ((lift, 0.0) if lift else (0.0,)):
        moved = dict(theta)
        for k, i in enumerate(index):
            moved[variables[i].component] = math.exp(min(max(float(out.x[k]) + scale, variables[i].lo), variables[i].hi))
        if not scale or all(r.c > 0 for r in cone_rows(schema, tuple(sorted(_expanded(sctx, moved).items())))):
            break
    return moved, u


def _item_slacks(res):
    report = res.evaluation.report
    return tuple((ROW_SEAL_ITEM + ":" + str(it.item), 1 - it.margin) for it in report.items
                 if it.margin is not None and math.isfinite(it.margin))


def _hard(res, row_key):
    rows = [(r.name, r.c) for r in res.constraints if r.name.startswith(_HARD_PREFIXES)]
    rows += [(r.name, r.c) for r in res.cone]
    return tuple(sorted(rows, key=lambda row: row_key(row[0])))        # [r12] 정준 행 순서


def _maxmin(sctx, variables, theta0, cells, first, tag):
    row_key = canonical_row_key(sctx)
    variables = list(variables)
    for i, floor in ln_idu_floors(sctx, variables, cells, one_var_only=True, start=theta0).items():
        variables[i] = Variable(variables[i].component, variables[i].log, floor, variables[i].hi)   # S-4f, solve_eps 와 같은 규칙
    lo = np.asarray([v.lo for v in variables], dtype=float)
    hi = np.asarray([v.hi for v in variables], dtype=float)
    coords = ThetaCoords.start(variables, theta0)         # 시작 좌표 원값 보존 정본(설계 40 §2.4.14 (2)) -- 자르지 않은 시작 좌표
    t_names = tuple(name for name, _s in _item_slacks(first))
    h_names = tuple(name for name, _c in _hard(first, row_key))
    n = len(variables)
    state = {"parent": first, "points": {}, "accepted": [], "frozen": set()}

    def theta_of(x):
        """풀이기·FD 가 준 x 를 상자로 자른 뒤(X-14) θ 로 -- 자른 좌표가 자르지 않은 시작 좌표와 같을 때만 시작 θ 원값(`ThetaCoords.to_theta`)."""
        return coords.to_theta([min(max(float(value), v.lo), v.hi) for v, value in zip(variables, x)])

    def rows_of(res):
        if res.status not in ACCEPTED_STATUSES:
            return None
        ts, hs = _item_slacks(res), _hard(res, row_key)
        if tuple(a for a, _ in ts) != t_names or tuple(a for a, _ in hs) != h_names:
            return False
        return np.asarray([s for _a, s in ts], dtype=float), np.asarray([c for _a, c in hs], dtype=float)

    def point(x, res=None):
        x = np.array(x[:n], dtype=float)      # 복사 -- SLSQP 가 넘긴 배열을 제자리에서 바꿔도 저장한 x 가 키와 어긋나지 않게
        hx = tuple(float(v).hex() for v in x)
        hit = state["points"].get(hx)
        if hit is not None:
            return hit
        if res is None:
            stop = search_stop(sctx)
            if stop is not None:
                raise _Abort(stop, x)
            res = evaluate(sctx, theta_of(x), cells, parent=state["parent"], origin=tag)
        rows = rows_of(res)
        if rows is None:
            raise _Abort("candidate_failure", x)
        if rows is False:
            raise _Abort("constraint_set_changed", x)
        entry = {"x": x, "res": res, "s": rows[0], "c": rows[1], "jac": None}
        state["points"][hx] = entry
        return entry

    def jac_of(x):
        entry = point(x)
        skip = frozenset(state["frozen"])
        if entry["jac"] is None or entry["jac"][2] != skip:
            try:
                cols = fd_jacobian(sctx, variables, entry["x"], entry["res"], cells, theta_of, tag, skip, ceiling=search_ceiling(sctx))
            except FdBudgetShortfall:
                raise _Abort("eval_budget", entry["x"]) from None          # 묶음이 못 시작 -- 평가 0개로 예산 정지(반쪽 야코비안 없음)
            gs = np.zeros((len(t_names), n))
            gc = np.zeros((len(h_names), n))
            for i, (col, step) in enumerate(cols):
                if col is None:
                    raise _Abort("fd_column_failure", entry["x"], i)
                if step == 0:
                    continue
                rows = rows_of(col)
                if rows is None or rows is False:
                    raise _Abort("constraint_set_changed", entry["x"])
                gs[:, i] = (rows[0] - entry["s"]) / step
                gc[:, i] = (rows[1] - entry["c"]) / step
            entry["jac"] = (gs, gc, skip)
        return entry["jac"]

    def cons(v):
        e = point(v)
        return np.concatenate([e["s"] - v[n], e["c"]])

    def cons_jac(v):
        gs, gc, _skip = jac_of(v)
        top = np.hstack([gs, np.full((len(t_names), 1), -1.0)])
        bottom = np.hstack([gc, np.zeros((len(h_names), 1))])
        return np.vstack([top, bottom])

    def accept(v):
        entry = point(v)
        state["parent"] = entry["res"]
        state["accepted"].append(entry)

    start = point(np.asarray([min(max(c, v.lo), v.hi) for v, c in zip(variables, coords.x0)], dtype=float), first)       # 상자 자르기(X-14): clip(x0ᵢ)
    accept(start["x"])
    try:
        steps0 = fd_jacobian(sctx, variables, start["x"], first, cells, theta_of, tag, frozenset(), ceiling=search_ceiling(sctx))
    except FdBudgetShortfall:
        # 첫 스텝 야코비안이 못 시작 -- 반복 0, 재시작 0, 정지 사유 eval_budget. 수락 목록은 시작점 하나(아래 끝 선택 규칙과 같다)
        return state["accepted"][0], "eval_budget", 0, 0, ("eval_budget",), (), t_names
    h = np.asarray([abs(step) for _col, step in steps0], dtype=float)
    resolved = [int(math.ceil(math.log2((hi[i] - lo[i]) / h[i]))) for i in range(n) if h[i] > 0]
    maxiter = max(1, sum(max(r, 1) for r in resolved))
    radius = (hi - lo) / 2
    cap = max(1, int(math.ceil(math.log2(float(np.max(radius)) / float(np.min(h[h > 0])))))) if np.any(h > 0) else 1
    grad = np.zeros(n + 1)
    grad[n] = -1.0
    restarts, iterations, stop, aborts, frozen_log = 0, 0, "converged", [], []
    centre = start["x"]
    while True:
        shrink = 2 ** restarts
        box_lo = np.maximum(lo, centre - radius / shrink) if restarts else lo.copy()
        box_hi = np.minimum(hi, centre + radius / shrink) if restarts else hi.copy()
        for i in state["frozen"]:
            box_lo[i] = box_hi[i] = centre[i]
        here = point(centre)
        v0 = np.concatenate([centre, [float(np.min(here["s"]))]])
        try:
            out = scipy_minimize(lambda v: -v[n], v0, jac=lambda v: grad, method="SLSQP",
                                 bounds=list(zip(box_lo, box_hi)) + [(None, None)],
                                 constraints=[{"type": "ineq", "fun": cons, "jac": cons_jac}],
                                 callback=accept, options={"ftol": 1, "maxiter": maxiter})
            iterations += int(out.nit)
            accept(out.x)
            stop = "converged" if out.success else "slsqp_" + str(out.status)
            break
        except _Abort as exc:
            stop = exc.reason
            if exc.reason in ("eval_budget", "wall_budget"):
                aborts.append(exc.reason)
                break
            if exc.reason == "fd_column_failure":
                if not np.array_equal(exc.x, state["accepted"][-1]["x"]):
                    accept(exc.x)
                    state["frozen"].clear()
                state["frozen"].add(exc.column)
                frozen_log.append(variables[exc.column].component)
                aborts.append("frozen:" + ":".join(variables[exc.column].component))
                centre = state["accepted"][-1]["x"]
                if len(state["frozen"]) == n:
                    stop = "all_columns_frozen"
                    break
                continue
            aborts.append(exc.reason)
            restarts += 1
            if restarts > cap:
                stop = "restart_cap"
                break
            if not np.array_equal(centre, state["accepted"][-1]["x"]):
                state["frozen"].clear()
            centre = state["accepted"][-1]["x"]
    best = max(state["accepted"], key=lambda e: (bool(np.all(e["c"] >= 0)), float(np.min(e["s"])), -e["res"].seq))
    return best, stop, iterations, restarts, tuple(aborts), tuple(frozen_log), t_names


def _primes(count):
    out, k = [], 1
    while len(out) < count:
        k += 1
        if all(k % p for p in out):
            out.append(k)
    return out


def _radical_inverse(index, base):
    value, scale = 0.0, 1.0 / base
    while index:
        index, digit = divmod(index, base)
        value += digit * scale
        scale /= base
    return value


def _repairable(res):
    """1변수 노드 근 없음(`no_root_in_window`)이고 창 양끝 h 가 둘 다 유한(같은 부호 = 근이 창 밖 한쪽)이며 margin(= 끝 |h| 최솟값 /
    writer tol_V, sizing 이 정규화)이 있는 실패 -- 연속 위반 크기가 있는 실패. 그 밖(빈 창·NONCONVERGENT·LUT 실패)은 None."""
    f = res.failure
    if f is None or f.margin is None or not f.devices:
        return None
    d = dict(f.detail)
    if d.get("reason") != REASON_NO_ROOT or "h_lo" not in d:
        return None
    if not (math.isfinite(d["h_lo"]) and math.isfinite(d["h_hi"])):
        return None
    return f.devices[0], f.margin, min(abs(d["h_lo"]), abs(d["h_hi"])) / f.margin


def _repair(sctx, variables, res, cells, tag, gmid_max):
    """S-4b 1단계(오케스트레이터 결정 2026-10-08): 실패 노드의 writer 소자 m 의 좌표 ln_idu 하나를 움직여 그 노드 근을 창 안으로.
    커널 실패는 SCC 순서의 첫 실패 노드에서 멈춰 한 점이 위반 크기 하나만 주고(합·최대를 쓸 수 없다), FD 기준점(받아들인 스냅샷)도
    없어 SLSQP 대신 좌표 bisection: 상자 양끝(하한은 칸 정점 하한) 중 그 노드가 통과하는 쪽을 찾고(평가 2), 불변식 '현재 쪽 = 같은
    노드 실패, 끝 쪽 = 통과'로 ⌈log2(|끝 − x| / res)⌉ 번 가른다. res = tol_V·(gm/ID 최대)(d ln ID = gm/ID·dVGS -- tol_V 만큼의 VGS
    변화가 만드는 ln IDu 변화의 상한, gm/ID 최대 = 그 슬라이스 on_mask 점 최댓값). 통과 쪽 점에서 다른 노드가 같은 종류로 실패하면
    그 노드로 이어가고(사슬), 같은 소자가 다시 나오거나 위반 크기가 없는 실패면 끝. 반환 (받아들인 점 | None, 고친 소자 tuple)."""
    index = {v.component: i for i, v in enumerate(variables)}
    rep_of = {m: rep for rep, members in sctx.domain.ties for m in members}
    floors = ln_idu_floors(sctx, variables, cells)
    kinds = dict(sctx.dc.base.column("device", "kind"))
    writers = dict(sctx.dc.base.column("node", "dc_writer"))
    fixed_seen, done = set(), []
    while True:
        if res.status in ACCEPTED_STATUSES:
            return res, tuple(done)
        info = _repairable(res)
        if info is None:
            return None, tuple(done)
        m, _margin, tol = info
        if m in fixed_seen:
            return None, tuple(done)
        fixed_seen.add(m)
        # 후보 좌표: 실패 writer m 자신, 다음 그 노드 writer 식의 '아는 쪽' 노드(diode 의 source·소스 추종의 gate)를 쓰는 소자 --
        # 적층 diode 처럼 근이 창 밖인 원인이 아래 소자 전압이면 m 의 좌표만으로는 고칠 수 없다(r8 실측 current_reuse)
        node = dict(res.failure.detail)["node"]
        known = writers[node].known
        candidates = [m]
        if known in writers and writers[known].element is not None and writers[known].element != m:
            candidates.append(writers[known].element)
        base = dict(res.theta)

        def same(r, m=m):
            # 같은 노드(writer m)가 여전히 근 없음인가 -- 위반 크기가 유한이든 아니든(정점 아래 ±inf 포함) 아직 고쳐지지 않았다
            return (r.failure is not None and dict(r.failure.detail).get("reason") == REASON_NO_ROOT
                    and r.failure.devices[:1] == (m,))

        found = None
        for c in candidates:
            i = index.get(rep_of.get((THETA_LN_IDU, c), (THETA_LN_IDU, c)))        # 묶인 소자는 대표 변수로
            if i is None:
                continue
            var = variables[i]
            for bound in (floors.get(i, var.lo), var.hi):
                if search_stop(sctx) is not None:
                    return None, tuple(done)
                th = dict(base)
                th[var.component] = bound
                r = evaluate(sctx, th, cells, origin=tag + (("repair", c),))
                if not same(r):
                    found = (c, var, bound, r)
                    break
            if found is not None:
                break
        if found is None:
            return None, tuple(done)
        c, var, end, end_res = found
        x = base[var.component]

        def run(value, base=base, var=var, c=c):
            th = dict(base)
            th[var.component] = value
            return evaluate(sctx, th, cells, origin=tag + (("repair", c),))

        res_ln = tol * gmid_max[kinds[c]]
        steps = max(1, int(math.ceil(math.log2(abs(end - x) / res_ln)))) if abs(end - x) > res_ln else 0
        lo_x, hi_x, hi_res = x, end, end_res
        for _k in range(steps):
            if search_stop(sctx) is not None:
                break
            mid = (lo_x + hi_x) / 2
            r = run(mid)
            if same(r):
                lo_x = mid
            else:
                hi_x, hi_res = mid, r
        done.append(c)
        res = hi_res


def _gmid_max(sctx):
    out = {}
    for kind, cap in sorted(sctx.dc.lut.memo.lut.cap_map.items()):
        w_key = cap.w_key
        sl = sctx.dc.lut.memo.lut.slice_map[(kind, w_key)]
        on = np.asarray(sl.on_mask, dtype=bool)
        out[kind] = float(np.exp(np.max(np.where(on, np.asarray(sl.log_GM) - np.asarray(sl.log_ID), -np.inf))))
    return out


def _halton_probe(sctx, variables, theta0, cells, tag):
    """S-4b: 상자 중심이 받아들일 상태가 아니면 Halton 열(소수 기저, 스크램블 없음, index 1 부터)의 k 번째 점을 변수 자연 좌표
    (bounds 위 선형 = ln 변수는 ln 좌표)에 놓아 순서대로 평가하고, 처음 받아들일 상태인 점에서 멈춘다. 한도 = 평가 예산 규칙
    (`search_stop`: kernel_calls ≥ 탐색 예산 또는 벽시계). 벽시계(deadline)가 없을 때만 시험 점 수 ≤ 탐색 예산(`search_ceiling`)을 더한다 -- 원뿔 밖 점은
    커널 0 이라 커널 수만으로는 끝나지 않는다. 둘 다 없으면 시험하지 않는다(`probe_budget_undeclared`).

    θ 전류(원뿔이 있을 때): 상자에서 독립으로 뽑지 않고 **상자 ∩ 원뿔 다면체 안 hit-and-run**(선형 전류 좌표)으로 옮긴다
    (오케스트레이터 결정 2026-10-08) -- 출발 = 전류 중심(`theta0`, 원뿔 안). 시험 k 마다 방향 d_j = 2·φ − 1(전류 변수 j 의 Halton
    좌표), 현재 점 p 에서 상자·원뿔 행(Σ w·I + 고정 > 0)이 허용하는 열린 현 (t_lo, t_hi) 위 t = t_lo + φ_s·(t_hi − t_lo)(φ_s =
    마지막 Halton 좌표)로 한 걸음, 새 p 가 다음 시험의 출발(사슬). 받아들이지 못한 점도 사슬은 이어간다(원뿔 안이므로). 다른
    변수는 위 Halton 좌표 그대로. 전류 중심이 원뿔 밖이면 전류도 상자 Halton(원뿔 밖 점은 커널 0)."""
    schema = _schema(sctx)
    cur = [i for i, v in enumerate(variables) if v.component[0] == THETA_CURRENT]
    inside = bool(cur) and bool(schema.current_cone) and all(
        r.c > 0 for r in cone_rows(schema, tuple(sorted(_expanded(sctx, theta0).items()))))
    _ordered, dim, n_dim = canonical_order(sctx, variables)
    bases = _primes(n_dim + (1 if inside else 0))
    floors = ln_idu_floors(sctx, variables, cells)
    gmid_max = _gmid_max(sctx)
    batch = len(variables) + 1          # 시험 묶음 = FD 한 sweep 크기(n + 1, E_B 유도와 같은 단위)
    best, repaired = None, []
    walk = None
    if inside:
        names = [variables[i].component[1] for i in cur]
        col = {name: j for j, name in enumerate(names)}
        alias = _current_alias(sctx)
        fixed = _current_fixed(sctx)
        rows_a, rows_f = [], []
        for _m, terms in _cone_canonical(sctx):
            a = np.zeros(len(cur))
            f = 0.0
            for t in terms:
                target, sign = alias.get(t.source, (t.source, 1.0))
                if target in col:
                    a[col[target]] += float(t.num) / t.den * sign
                else:
                    f += float(t.num) / t.den * fixed[t.source]
            rows_a.append(a)
            rows_f.append(f)
        rows_a, rows_f = np.asarray(rows_a), np.asarray(rows_f)
        box_lo = np.asarray([math.exp(variables[i].lo) for i in cur])
        box_hi = np.asarray([math.exp(variables[i].hi) for i in cur])
        walk = np.asarray([theta0[variables[i].component] for i in cur], dtype=float)
    tried = 0
    while True:
        if tried and tried % batch == 0 and best is not None:
            fixed_res, chain = _repair(sctx, variables, best[1], cells, tag, gmid_max)
            repaired.append(chain)
            best = None
            if fixed_res is not None:
                return fixed_res, tried, "repair", tuple(repaired)
        stop = search_stop(sctx)
        if stop is not None:
            return None, tried, "probe_" + stop, tuple(repaired)
        if sctx.deadline is None:
            ceiling = search_ceiling(sctx)
            if ceiling is None:
                return None, tried, "probe_budget_undeclared", tuple(repaired)
            if tried >= ceiling:
                return None, tried, "probe_eval_budget", tuple(repaired)
        tried += 1
        phi_dim = [_radical_inverse(tried, b) for b in bases]
        phi = [phi_dim[d] for d in dim]            # 변수별 좌표 (같은 차원 = 같은 값)
        theta = dict(theta0)
        for i, var in enumerate(variables):
            low = floors.get(i, var.lo)
            value = low + phi[i] * (var.hi - low)
            theta[var.component] = math.exp(value) if var.log else value
        if walk is not None:
            d = np.asarray([2 * phi[i] - 1 for i in cur])
            t_lo, t_hi = -math.inf, math.inf
            for j in range(len(cur)):
                if d[j]:
                    a, b = (box_lo[j] - walk[j]) / d[j], (box_hi[j] - walk[j]) / d[j]
                    t_lo, t_hi = max(t_lo, min(a, b)), min(t_hi, max(a, b))
            slope, level = rows_a @ d, rows_a @ walk + rows_f
            for s, lv in zip(slope, level):
                if s > 0:
                    t_lo = max(t_lo, -lv / s)
                elif s < 0:
                    t_hi = min(t_hi, -lv / s)
            # 방향이 0(모든 전류 성분 0 -- 예: 전류 변수 하나, 기저 2 의 첫 시험 φ = 1/2)이면 현이 정해지지 않는다(양끝 무한):
            # 걸음 없음(p 그대로). 끝이 무한인 현·빈 현도 걸음 없음 -- 무한 × 0 = NaN 을 만들지 않는다.
            if math.isfinite(t_lo) and math.isfinite(t_hi) and t_lo < t_hi:
                walk = walk + (t_lo + phi_dim[-1] * (t_hi - t_lo)) * d
            for j, i in enumerate(cur):
                theta[variables[i].component] = float(min(max(walk[j], box_lo[j]), box_hi[j]))
        res = evaluate(sctx, theta, cells, origin=tag + (("probe", tried),))
        if res.status in ACCEPTED_STATUSES:
            return res, tried, "halton", tuple(repaired)
        info = _repairable(res)
        if info is not None and (best is None or info[1] < best[0]):
            best = (info[1], res)          # 묶음 안 위반 크기(margin) 최소 시험 점 -- 묶음이 끝나면 1단계 출발점


def centre_start(sctx, rung=None):
    """layer0 가 처음 평가하는 점 `(variables, theta, cells, centre_u)` -- 상자 중심 + 전류 중심. n_θ(`variables` 길이)만 `_wire_sweep_memo` 가 이 함수로
    잰다(LUT memo 상한 (n_θ + 1)·U_eval 의 n_θ -- 설계 40 §2.4.6 '첫 평가 버림 제거')."""
    variables, theta, cells = _box_centre(sctx, rung)
    theta, centre_u = _current_centre(sctx, variables, theta, rung)
    return variables, theta, cells, centre_u


def layer0_start(sctx, origin=()):
    blas_environment()      # [NFR-4 재확인 (d)] 진입에서 BLAS 스레드 1 을 다시 확인(무상태, 값은 기록하지 않는다)
    calls0 = sctx.counters["kernel_calls"]
    tag = origin + (("stage", STAGE_LAYER0),)
    # [U13] 출발 사다리(`graph/start: rungs`: 실행 가능한 최대 gm/ID 위치에서 구간 하한 쪽으로 반씩)를 칸 순서로 커널에 확인해 처음 받아들일 상태인 칸에서 출발한다.
    # 사다리가 없으면(출발 구간 필드가 없거나 칸이 없음) 상자 중심 한 점이다.
    rungs = sctx.rungs or (None,)
    failure, probes, source, repairs = None, 0, "centre", ()
    first, start_status, base, best = None, "centre_outside_cone", None, None
    for k, rung in enumerate(rungs):
        variables, theta, cells, centre_u = centre_start(sctx, rung)
        base = (variables, theta, cells, centre_u) if base is None else base
        if any(r.c <= 0 for r in cone_rows(_schema(sctx), tuple(sorted(_expanded(sctx, theta).items())))):
            start_status = "centre_outside_cone"
            continue
        if search_stop(sctx) is not None:
            start_status = "eval_budget"          # 사다리 칸도 단일 평가다 -- 예산(또는 벽시계)에 닿았으면 평가하지 않고 사다리를 멈춘다
            break
        first = evaluate(sctx, theta, cells, origin=tag)
        start_status, failure = first.status, first.failure
        if first.status in ACCEPTED_STATUSES:
            source = "centre" if k == 0 else "ladder:" + str(k)
            break
        info = _repairable(first)
        if info is not None and (best is None or info[1] < best[0]):
            best = (info[1], first, variables, theta, cells, centre_u, k)       # 위반 크기가 가장 작은 칸 -- 아래 1단계 보정의 출발점
        first = None
    if first is None and best is not None and search_stop(sctx) is None:
        # 사다리 어느 칸도 받아들일 상태가 아니면 위반 크기가 가장 작은 칸(1변수 노드 근이 창 밖)에 S-4b 1단계(`_repair`: writer ln IDu 한 좌표 bisection)를 적용한다 --
        # Halton 시험 점에 쓰는 것과 같은 보정이다.
        _margin, res, variables, theta, cells, centre_u, k = best
        fixed_res, chain = _repair(sctx, variables, res, cells, tag, _gmid_max(sctx))
        repairs = (chain,)
        if fixed_res is not None:
            first, source, theta = fixed_res, "ladder_repair:" + str(k), dict(fixed_res.theta)
    if first is None:
        variables, theta, cells, centre_u = base
        first, probes, why, repairs = _halton_probe(sctx, variables, theta, cells, tag)
        if first is None:
            reason = start_status
            if failure is not None:
                reason = dict(failure.detail).get("reason") or failure.failure_class
            return Layer0Result(None, None, False, "start_" + str(reason) + "+" + why, centre_u, start_status, failure,
                                0, 0, (), (), sctx.counters["kernel_calls"] - calls0, (), probes, None, repairs)
        source = why + ":" + str(probes)          # 시작점 출처: "halton:k"(시험 점) 또는 "repair:k"(k 번째 시험 뒤 1단계)
        theta = dict(first.theta)
    best, stop, iterations, restarts, aborts, frozen, t_names = _maxmin(sctx, variables, theta, cells, first, tag)
    res = best["res"]
    start = StartPoint("layer0", res.theta, cells, SOURCE_LAYER0)
    return Layer0Result(start, float(np.min(best["s"])), bool(np.all(best["c"] >= 0)), stop, centre_u, start_status,
                        failure, iterations, restarts, aborts, frozen, sctx.counters["kernel_calls"] - calls0, t_names,
                        probes, source, repairs)
