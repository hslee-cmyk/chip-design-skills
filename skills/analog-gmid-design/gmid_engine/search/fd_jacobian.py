"""FD Jacobian -- 전진 차분, 열마다 parent = 기준점 (설계 design_mod6_search_front 3절).

진입점: `fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset(), *, ceiling) -> tuple[(EvalResult | None, 스텝)]`.
`skip` = 고정된 변수 index(그 열은 평가 없이 (base, 0.0)).

* `ceiling`(필수 키워드) = 이 묶음이 넘으면 안 되는 `kernel_calls` 한도 또는 None(확인 없음). 시작 전에 상계 = 평가할 열 수 × 2(`skip`·스텝 0·`None` 제외)와
  남은 한도(`ceiling` − `kernel_calls`)를 비교해, 남은 한도가 상계보다 작으면 평가 0개로 `FdBudgetShortfall(needed, remaining)`. 묶음이 시작된 뒤에는 멈추지 않는다
  (열 평가 규칙은 그대로 -- 반쪽 야코비안은 FD 를 깨뜨린다). 부르는 쪽: 층 0·외층 = 탐색 예산(`search_ceiling`), 감도 게이트 = `e_total`.

* 열 i 마다 `evaluate(θ(x + hᵢeᵢ), parent=base)` 1회 -- sizing 이 기준점 스냅샷에서 hᵢ 가 읽히는 블록과 하류만 다시
  계산한다(전류 성분은 ④ 노드전압을 건드리지 않는다, 설계 2.2). 같은 x 는 키가 같아 캐시 적중(커널 0).
* 스텝 hᵢ(상수 없음 -- 그 좌표의 LUT 해상도, 설계 3절):
  - `ln_idu`(쓰기 소자 m): 동작점 VGS 를 품는 VGS 격자 칸 폭 × gm/ID(d ln ID = (gm/ID)·dVGS).
  - `y`: VDS 격자 최소 칸 폭 / 그 W4 창 폭(창 = 그 y 키를 쓰는 뿌리 노드의 `dc_window`; writer 관계 `free_window` 항목만 -- 입력 포트 항목은 y 키를 만들지 않는다).
  - `current`(ln 좌표): 그 기저 원소를 항으로 갖는 MOS 들의 tol_V(id_eq)·gm/ID 최솟값(상대 스텝 -- M7 L1 W 허용 상대오차와 같은 식).
  - `resistance`(ln 좌표): tol_V 최솟값 / (I·R)(I·R 강하가 tol_V 만큼 움직이는 상대 ΔR). I = 0 이면 그 저항은 DC 에 닿지 않아
    열 = 0(평가 없음).
  - `L`(칸 안 연속): [r5, 오케스트레이터 결정 2026-10-08] PDK 제조 격자 한 칸(`domain.grid_m` = `manufacturing_grid_m`,
    실현 가능한 L 의 최소 변화). 유도: bin 안 L 은 이웃 앵커 사이 선형 보간(LUT 4.0)이라 앵커 칸 안의 어느 할선도 그 칸의
    기울기와 같다 -- 그래서 앵커 간격 스텝은 정보를 더하지 않고, 칸 중점에서 칸 폭만큼 가면 양방향 모두 칸 밖이라 열이 고정됐다
    (r4 실측: 9회로 L 전부 고정). 격자 한 칸 스텝은 칸 안에 머물러 양쪽이 실제로 실패할 때만 고정된다(S-16). 앵커 위 점은
    한쪽 칸의 기울기(전진, 상한이면 후진)다. ~~r4: L 을 품는 LUT L 점 칸 폭(할선)~~.
* 변수 상한을 넘으면 후진 스텝(−hᵢ). 열 점이 받아들일 상태(봉인 통과·대기)가 아니면 반대 방향을 한 번 더 시험하고, 둘 다 아니면
  그 열은 (None, h) -- 부르는 쪽(SLSQP)이 그 변수를 고정한다(S-16, 0 도함수를 지어내지 않는다).
* 값이 bound 와 1 ulp 이내면 bound 로 맞춘다(칸 끝 앵커의 반올림).
"""
import bisect
import math

import numpy as np

from gmid_engine.sizing import (KERNEL_KEY, REL_INPUT_POINT, REL_WINDOW, THETA_CURRENT, THETA_L, THETA_LN_IDU, THETA_PASSIVE_KINDS, THETA_RESISTANCE,
                                THETA_Y)

from .kernel import evaluate
from .point_wf import point_wf
from .search_values import ACCEPTED_STATUSES, STAGE_FD


def _cell_width(grid, value):
    grid = [float(g) for g in grid]
    i = min(max(bisect.bisect_right(grid, value) - 1, 0), len(grid) - 2)
    return grid[i + 1] - grid[i]


def _steps(sctx, variables, base):
    snap = base.evaluation.snapshot
    lut = sctx.dc.lut
    ops = dict(snap.column("device", "dc_op"))
    tols = dict(snap.column("device", "dc_tol_v"))
    defined = [tols[m] * ops[m].gm_id for m in ops if tols.get(m)]
    tol_min = min(t for t in tols.values() if t) if any(tols.values()) else None
    sources = {}
    for mos, terms in sctx.dc.base.value("graph", KERNEL_KEY, "theta_schema").current_cone:
        for t in terms:
            sources.setdefault(t.source, []).append(mos)
    windows = {}
    writers = dict(snap.column("node", "dc_writer"))
    for node, win in snap.column("node", "dc_window"):
        if writers[node].relation in (REL_WINDOW, REL_INPUT_POINT):      # y 스텝은 W4 뿌리 창 폭만(입력 점은 p 포트 항목 하나 -- n 포트 항목 없음, 설계 41 4.7-6)
            windows[writers[node].y_key] = win.hi - win.lo
    currents = dict(snap.column("device", "dc_current"))
    theta = dict(base.theta)
    steps = []
    for var in variables:
        kind, key = var.component
        if kind == THETA_LN_IDU:
            op = ops[key]
            sl = lut.memo.lut.slice_map[(op.kind, op.w_key)]
            steps.append(_cell_width(sl.VGS_grid, op.vgs) * op.gm_id)
        elif kind == THETA_Y:
            vds = np.diff(np.asarray(next(iter(lut.memo.lut.slice_map.values())).grids[2], dtype=float))
            width = windows.get(key)
            steps.append(float(np.min(vds)) / width if width else None)
        elif kind == THETA_CURRENT:
            rel = [tols[m] * ops[m].gm_id for m in sources.get(key, ()) if tols.get(m)]
            steps.append(min(rel) if rel else (min(defined) if defined else None))
        elif kind == THETA_RESISTANCE:
            drop = abs(currents.get(key, 0.0)) * theta[var.component]
            steps.append(tol_min / drop if drop and tol_min else 0.0)
        elif kind == THETA_L:
            steps.append(sctx.domain.grid_m)             # 제조 격자 한 칸 -- bin 안 선형 보간이라 칸 안 할선 기울기가 같다
        elif kind in THETA_PASSIVE_KINDS:
            # [r6] DEC-92 소신호 전용 수동소자(ln 좌표): LUT 축이 없다 -- 소신호 모형의 상대 분해능(ss_dev lut_rel_tol =
            # gm/ID·tol_V 의 최솟값)보다 작은 상대 변화는 metric 에서 구별되지 않으므로 그 값을 상대 스텝으로(전류 폴백과 같은 값)
            steps.append(min(defined) if defined else None)
        else:
            raise ValueError("fd_jacobian: 모르는 θ 성분 " + repr(var.component))
    return steps


class FdBudgetShortfall(Exception):
    """묶음 상계(`needed`)가 남은 한도(`remaining`)보다 크다 -- 평가를 하나도 하지 않고 낸다. `InfeasibleSizingError` 하위가 아니다(후보 실패가 아니라 예산)."""

    def __init__(self, needed, remaining):
        super().__init__("fd_jacobian: 묶음 상계 " + str(needed) + " > 남은 한도 " + str(remaining))
        self.needed = needed
        self.remaining = remaining


def fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset(), *, ceiling):
    steps = _steps(sctx, variables, base)
    if ceiling is not None:
        needed = 2 * sum(1 for i, h in enumerate(steps) if i not in skip and h)         # h = None(고정)·0(DC 에 안 닿음)은 평가 없음
        remaining = ceiling - sctx.counters["kernel_calls"]
        if remaining < needed:
            raise FdBudgetShortfall(needed, remaining)
    columns = []
    wf = point_wf(base.evaluation.snapshot)         # 기준점이 평가한 w_f 칸 입력 -- FD 스텝은 θ 만 움직인다(LR10 (W-a))
    for i, (var, h) in enumerate(zip(variables, steps)):
        if i in skip:
            columns.append((base, 0.0))       # 고정된 변수(S-16) -- 평가 없음, 부르는 쪽이 bounds 로 묶는다
            continue
        if not h:
            columns.append((None, 0.0) if h is None else (base, 0.0))
            continue
        h = -h if x[i] + h > var.hi else h
        found = None
        for step in (h, -h):
            value = x[i] + step
            for bound in (var.lo, var.hi):
                if abs(value - bound) <= math.ulp(bound):     # 칸 끝 앵커까지 스텝의 반올림(1 ulp)은 그 끝으로
                    value = bound
            if not var.lo <= value <= var.hi or value == x[i]:
                continue
            step = value - x[i]
            probe = list(x)
            probe[i] = value
            res = evaluate(sctx, to_theta(probe), cells, wf, parent=base, origin=origin + (("stage", STAGE_FD),))
            if res.status in ACCEPTED_STATUSES:
                found = (res, step)
                break
        columns.append(found if found is not None else (None, h))
    return tuple(columns)
