"""블록 gain 상한 A_i,max -- 격자 곱 전수 (설계 41 §4.2, D-GB4b·D-NM, GB4 단계 A6 `block_bounds`).

진입점: `block_gain_bound(model, tables, budget, members) -> BlockBound`
(`model` = `BlockModel`, `tables` = `ParamTables`, `budget` = 계수 예산 N_S(int), `members` = 보고용 MOS 이름).

**정의**: A_i,max = 블록 국소 모델 gain 의 최댓값, 최댓값은 모델 축(`BlockModel.axes`) 격자 곱 전체에서 찾는다(행마다 `row_gains`).
* **예산 게이트**(41 §4.2): 격자 곱 Π > N_S 이면 상한은 **미상**(`unknown`, 사유 `grid_product_over_budget`)이다 -- 격자를 줄이면 그 최댓값은 상한이 아니라서 줄이지 않는다.
  Π ≤ N_S 이면 모든 행을 평가한다(묶음 크기 = ceil(sqrt(Π)), 행 순서는 마지막 축이 가장 빨리 변하는 사전식 -- 같은 입력이면 같은 최대 행, 동률은 앞선 행).
* **비단조 축 세분**(미러 비·전류 배율·저항, 41 §4.2, N5): 최대 행에서 연속 축(`current`·`resistor`)을 따라 양 이웃 행의 gain 을 본다. 이웃이 둘 다 작으면 내부 최대라
  이웃 사이 구간(로그 좌표)을 이분 세분한다(구간의 두 중점을 평가해 5점 중 최대를 새 중심으로, 반복 상한 K_max = ceil(log2(구간 폭 / tol)) -- `sizing.k_max` 식, tol = √(배정밀도 ε):
  극값 근처 gain 은 (Δ)² 로 변해 상대 √ε 보다 작은 차는 보이지 않는다). 축 끝이 최대면 그대로 인증한다. 마지막 바퀴에서도 gain 이 상대 √ε 보다 크게 오르면 `unknown`(`continuous_axis_not_refined`).
  연속 축마다 한 번씩 (축 수 + 1)바퀴. 단봉(unimodal) 가정 -- 구간 안 다중 극값은 잡지 못한다(설계 N5 와 같은 한계).
* **분해능** `b_GB4,i`(dB) = 최대 행과 그 격자 이웃 행(각 축 ±1, 연속 축은 세분 마지막 구간 끝)의 gain 차 |20·log10 비|의 최댓값.
* **하한 추정** `found_db` -- 격자 곱이 예산을 넘어도 같은 평가기로 **좌표 상승**(시작점 `bit_length(최대 축 크기)`개, 축마다 모든 값을 훑는 반복, 변화 없으면 끝; 연속 축은 기준점에 고정 --
  `_reference_pick`: 축 중앙에서 출발해 모든 MOS 전류가 양수가 될 때까지 전류 여유를 최급 상승으로 올린 점)으로 찾은 최대 gain. 상한이 아니라 하한 추정이고 판정에 쓰지 않는다(Σ 판정은 `certified` 상한만
  읽는다). 시작점 s 의 축 a 위치 = ((크기_a − 1)·s) // (S − 1)  (S = 시작점 수, S ≥ 2). 기준점을 못 찾으면 추정 없음(None).
버퍼 블록도 같은 방법이다(상한은 0 dB 이하여야 한다 -- 보고만).
"""
import math

import numpy as np

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE

from .achievability_types import (
    AXIS_KIND_RESISTOR,
    REASON_AXIS_RANGE,
    REASON_NON_CONVERGED,
    REASON_OVER_BUDGET,
    STATUS_CERTIFIED,
    STATUS_UNKNOWN,
    BlockBound,
)
from .block_gain_rows import row_gains

_EPS = np.finfo(float).eps
_TOL = math.sqrt(_EPS)          # 극값 근처에서 gain 은 (Δ)² 로 변해 상대 √eps 보다 작은 차는 보이지 않는다 -- 세분 허용오차


def _db(gain):
    return AMPLITUDE_DB_PER_DECADE * math.log10(gain) if gain > 0 else -math.inf


def _eval(model, tables, idx, cont=None):
    with np.errstate(all="ignore"):
        return row_gains(model, tables, np.atleast_2d(idx), cont)


def _exhaustive(model, tables, sizes):
    chunk = max(1, math.isqrt(model.pi - 1) + 1)
    best, best_idx, n_rows = -math.inf, None, 0
    for start in range(0, model.pi, chunk):
        flat = np.arange(start, min(model.pi, start + chunk))
        idx = np.stack(np.unravel_index(flat, sizes), axis=1) if sizes else np.zeros((len(flat), 0), dtype=int)
        gain = _eval(model, tables, idx)
        n_rows += len(flat)
        finite = np.where(np.isfinite(gain), gain, -math.inf)
        k = int(np.argmax(finite))
        if finite[k] > best:
            best, best_idx = float(finite[k]), idx[k].copy()
    return best, best_idx, n_rows


def _current_margin(model, pick):
    """연속 축 index `pick` 에서 블록 MOS 전류식의 최소 상대 여유 min_m I_m / Σ|항| (양수면 모든 전류가 양수 = KCL 원뿔 안)."""
    worst = math.inf
    for m in model.mos:
        total = scale = 0.0
        for axis, coeff in m.current:
            term = coeff if axis < 0 else coeff * float(model.axes[axis].values[pick[axis]])
            total += term
            scale += abs(term)
        worst = min(worst, total / scale if scale > 0 else -math.inf)
    return worst


def _reference_pick(model):
    """연속 축 index 의 기준점: 축 격자 중앙(로그 기하 중심)에서 출발해 전류 여유(`_current_margin`)가 양수(모든 MOS 전류 > 0)가 될 때까지 한 번에 한 축·한 마디씩
    가장 여유가 많이 오르는 방향으로 옮긴다(최급 상승, 더 오르는 이웃이 없으면 멈춤). 양수가 되는 첫 점에서 멈추므로 KCL 원뿔 경계 가까운 중앙 근방이다.
    끝에서도 양수가 아니면 None -- 추정을 하지 않는다. 블록에 저항·값 선언 전류가 있으면(0차 동차가 아니면) gain 이 전류 절대 규모에 달려 있어 None."""
    cont = [a for a, ax in enumerate(model.axes) if ax.continuous]
    pick = {a: model.axes[a].size // 2 for a in cont}
    if not cont:
        return pick
    if not model.normalized or any(model.axes[a].kind == AXIS_KIND_RESISTOR for a in cont):
        return None                 # 저항·값 선언 전류가 있으면 gain 이 전류 절대 규모에 달려 있어 기준점 한 점으로는 추정할 수 없다
    margin = _current_margin(model, pick)
    for _ in range(sum(model.axes[a].size for a in cont)):
        if margin > 0:
            break
        best = None
        for a in cont:
            for step in (-1, 1):
                k = pick[a] + step
                if 0 <= k < model.axes[a].size:
                    score = _current_margin(model, {**pick, a: k})
                    if score > margin and (best is None or score > best[0]):
                        best = (score, a, k)
        if best is None:
            break
        margin, a, k = best
        pick[a] = k
    return pick if margin > 0 else None


def _ascent(model, tables, sizes):
    """좌표 상승 하한 추정: (gain, idx, 평가 행 수) -- 유효 행이 없으면 (-inf, None, n).

    연속 축(`current`·`resistor`)은 기준점(`_reference_pick`)에 고정한다: 전류 상자 [I_off, I_max] 는 열 자릿수에 걸쳐 비가 극단인 행이 거의 특이 행렬이 되어
    비물리적으로 큰 gain 을 내므로, 추정은 KCL 원뿔 안 기하 중심 근방의 비만 훑는다. 상한이 아니라 보고용 하한 추정이다(기준점을 못 찾으면 추정 없음)."""
    n_axes = len(sizes)
    if not n_axes:
        g = _eval(model, tables, np.zeros((1, 0), dtype=int))
        return (float(g[0]), np.zeros(0, dtype=int), 1) if np.isfinite(g[0]) else (-math.inf, None, 1)
    frozen = _reference_pick(model)
    if frozen is None:
        return -math.inf, None, 0
    free_axes = [a for a in range(n_axes) if a not in frozen]
    starts = max(max(sizes).bit_length(), 1 + 1)
    best, best_idx, n_rows = -math.inf, None, 0
    for s in range(starts):
        cur = np.asarray([frozen[a] if a in frozen else ((sizes[a] - 1) * s) // (starts - 1) for a in range(n_axes)], dtype=int)
        cur_gain = float(_eval(model, tables, cur[None, :])[0])
        n_rows += 1
        for _ in range(len(free_axes) + 1):
            moved = False
            for a in free_axes:
                line = np.repeat(cur[None, :], sizes[a], axis=0)
                line[:, a] = np.arange(sizes[a])
                gain = _eval(model, tables, line)
                n_rows += sizes[a]
                finite = np.where(np.isfinite(gain), gain, -math.inf)
                k = int(np.argmax(finite))
                if finite[k] > (cur_gain if np.isfinite(cur_gain) else -math.inf) and k != cur[a]:
                    cur[a], cur_gain, moved = k, float(finite[k]), True
            if not moved:
                break
        if np.isfinite(cur_gain) and cur_gain > best:
            best, best_idx = cur_gain, cur.copy()
    return best, best_idx, n_rows


def _grid_value(model, idx, axis):
    return float(model.axes[axis].values[idx[axis]])


def _refine(model, tables, idx, gain):
    """연속 축 세분(41 §4.2 비단조 축 처리). -> (gain, {축: (실수 값, 왼 끝 gain, 오른 끝 gain)}, 수렴 여부, 평가 행 수)."""
    continuous = [a for a, ax in enumerate(model.axes) if ax.continuous]
    values = {a: _grid_value(model, idx, a) for a in continuous}
    brackets, n_rows, converged = {}, 0, True
    best = gain
    for _ in range(len(continuous) + 1):
        changed = False
        for a in continuous:
            axis = model.axes[a]
            k = int(idx[a])
            lo_i, hi_i = max(k - 1, 0), min(k + 1, axis.size - 1)
            if k == 0 or k == axis.size - 1:                  # 끝점 최대: 그 방향으로 단조 -> 인증(세분 없음)
                brackets[a] = (values[a], best, best)
                continue
            left, right = math.log(axis.values[lo_i]), math.log(axis.values[hi_i])
            mid = math.log(values[a])
            rounds = max(1, math.ceil(math.log2((right - left) / _TOL)))          # K_max (sizing.k_max 식, tol = √eps)
            g_mid = best
            g_left = g_right = math.nan
            last_gain = 0.0
            for _round in range(rounds):
                pts = np.asarray([left, (left + mid) / 2, mid, (mid + right) / 2, right])
                cont = {a: np.exp(pts)}
                for other in continuous:
                    if other != a:
                        cont[other] = np.full(len(pts), values[other])
                rows = np.repeat(np.asarray(idx, dtype=int)[None, :], len(pts), axis=0)
                gains = _eval(model, tables, rows, cont)
                n_rows += len(pts)
                finite = np.where(np.isfinite(gains), gains, -math.inf)
                j = int(np.argmax(finite))
                last_gain = float(finite[j]) / g_mid - 1 if g_mid > 0 else 0.0
                lo2, hi2 = max(j - 1, 0), min(j + 1, len(pts) - 1)
                g_left, g_right = float(gains[lo2]), float(gains[hi2])
                if finite[j] >= g_mid:
                    g_mid = float(finite[j])
                left, mid, right = pts[lo2], pts[j], pts[hi2]
                if right - left <= _TOL:
                    break
            if last_gain > _TOL:
                converged = False
            if g_mid > best:
                changed = True
            best = max(best, g_mid)
            values[a] = math.exp(mid)
            brackets[a] = (values[a], g_left, g_right)
        if not changed:
            break
    return best, values, brackets, converged, n_rows


def _resolution(model, tables, idx, gain, brackets):
    """분해능 b (dB): 최대 행과 격자 이웃 행(연속 축은 세분 마지막 구간 끝)의 gain 차 최댓값."""
    spread = 0.0
    for a, axis in enumerate(model.axes):
        if axis.continuous and a in brackets:
            for g in brackets[a][1:]:
                if np.isfinite(g) and g > 0:
                    spread = max(spread, abs(_db(gain) - _db(g)))
            continue
        for step in (-1, 1):
            k = int(idx[a]) + step
            if 0 <= k < axis.size:
                row = np.asarray(idx, dtype=int).copy()
                row[a] = k
                g = float(_eval(model, tables, row[None, :])[0])
                if np.isfinite(g) and g > 0:
                    spread = max(spread, abs(_db(gain) - _db(g)))
    return spread


def _condition(model, idx, values):
    out = []
    for a, axis in enumerate(model.axes):
        v = values[a] if a in values else float(axis.values[int(idx[a])])
        out.append((axis.kind + ":" + ",".join(axis.label), v))
    return tuple(out)


def block_gain_bound(model, tables, budget, members):
    sizes = [axis.size for axis in model.axes]
    axes = tuple((axis.kind, axis.size) for axis in model.axes)
    over = model.pi > budget
    f_gain, f_idx, f_rows = _ascent(model, tables, sizes)
    found = None if f_idx is None else _db(f_gain)
    if over:
        return BlockBound(model.key, model.role, STATUS_UNKNOWN, None, None, model.pi, axes, (), REASON_OVER_BUDGET, found,
                          tuple(members), f_rows)
    best, idx, n_rows = _exhaustive(model, tables, sizes)
    if idx is None:
        return BlockBound(model.key, model.role, STATUS_UNKNOWN, None, None, model.pi, axes, (), REASON_AXIS_RANGE, found,
                          tuple(members), n_rows + f_rows)
    best, values, brackets, converged, r_rows = _refine(model, tables, idx, best)
    n_rows += r_rows
    if not converged:
        return BlockBound(model.key, model.role, STATUS_UNKNOWN, None, None, model.pi, axes, _condition(model, idx, values),
                          REASON_NON_CONVERGED, found, tuple(members), n_rows + f_rows)
    b = _resolution(model, tables, idx, best, brackets)
    return BlockBound(model.key, model.role, STATUS_CERTIFIED, _db(best), b, model.pi, axes, _condition(model, idx, values), None,
                      _db(best) if found is None else max(found, _db(best)), tuple(members), n_rows + f_rows)
