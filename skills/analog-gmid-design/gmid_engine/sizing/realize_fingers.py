"""실현 정수화 -- 정합 칸 하나의 손가락 수 m 을 사전식 오차 키로 정한다 (FS-1, 계획 DEC-108 (6), 설계 40 §3.7-B 6, interface card §1).

진입점: `realize_fingers(w_theta, w_f_m, ratios) -> RealizedCell(m, ratio_err, member_err)`.

* `w_theta` = 칸 멤버의 θ W(탐색 스냅샷 `DeviceOp.W`, 멤버 순서 = 칸 키 순서), `w_f_m` = 칸 손가락 폭, `ratios` = 칸 안 선언 미러 비 `DeclaredRatio` tuple(위치 = `w_theta` index).
  순수 함수다(graph 읽기 0, 저장 0, 같은 입력 = 비트 같은 출력).
* x_i = W_θ,i / w_f. 선택 단위 = 선언 정수비 묶음(기준 d 와 출력들 -- 모든 k 가 양의 정수, 선택 = m_d 하나, m_oj = k_j·m_d) 하나, 그 밖 멤버는 멤버마다 단위 하나(선택 = 자기 m).
  후보 m = {⌊x⌋, ⌈x⌉}(1 미만은 1 로 올림), 묶음은 m_d 후보 = {⌊x_d⌋, ⌈x_d⌉} ∪ 출력별 {⌊x_oj/k_j⌋, ⌈x_oj/k_j⌉}.
* 키 K = (E1, E2, E3, E4, E5)의 사전식 최소: r_i = m_i/x_i, e_i = |m_i − x_i|/x_i, E1 = max(r)/min(r) − 1(쌍 비 오차 -- 미러비 최우선, O-251 (2)), E2 = max e, E3 = Σ e(`math.fsum`),
  E4 = Σ m, E5 = m 벡터의 사전식(멤버 순서). 곱집합을 펼치지 않는다: 최소 r 값 v 마다 단위별 최소 최대 r 을 모아 E1* 를 구하고(비교 꼴 `hi / v - 1`), E1(v) = E1* 인 v 의 허용 선택 안에서
  단위별로 (E2 상한 → (Σe, Σm) 최소)를 고르고, 그 후보 벡터들 사이에서 K 최소를 낸다.
* 호출 계약 위반(`ValueError`): 위치 범위 밖, 한 멤버가 두 묶음에 듦(같은 묶음 안 중복 포함), 기준이 자기 출력, 선언 k 비유한·`not (k > 0)`(`declared_ratio_invalid`, 정수 판정보다 먼저).
  분류된 실패(`SealViolationError`, 사유 `realize_tie_unresolved`): W_θ 가 `not (w > 0)`·비유한 또는 `w_f_m` 이 `not (w_f_m > 0)`·비유한 -- 호출자(DC 블록)가 `devices` 를 칸 멤버로 다시 올린다.
"""
import math

from gmid_engine.core import SealViolationError

from .s2_values import RealizedCell

_TIE_UNRESOLVED = "realize_tie_unresolved"
_RATIO_INVALID = "declared_ratio_invalid"


def _positive_finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _check_ratios(n, ratios):
    """선언 비 계약 검사(ValueError)."""
    seen = set()
    for ratio in ratios:
        members = (ratio.reference,) + tuple(pos for pos, _k in ratio.outputs_with_k)
        for pos in members:
            if isinstance(pos, bool) or not isinstance(pos, int) or not 0 <= pos < n:
                raise ValueError("realize_fingers: 선언 비 위치가 칸 밖이다 " + repr(pos))
            if pos in seen:
                raise ValueError("realize_fingers: 한 멤버가 선언 묶음 하나에만 들 수 있다 " + repr(pos))
            seen.add(pos)
        for _pos, k in ratio.outputs_with_k:
            if not _positive_finite(k):
                raise ValueError(_RATIO_INVALID + ": 선언 비 k 는 유한 양수여야 한다 " + repr(k))


def _units(n, x, ratios):
    """선택 단위 목록 [(멤버 위치 tuple, 선택지 [(m 벡터 = 멤버 위치 순 tuple)])] -- 선언 정수비 묶음은 단위 하나(m_d 선택), 나머지는 멤버마다 단위 하나."""
    units, grouped = [], set()
    for ratio in ratios:
        ks = tuple(k for _pos, k in ratio.outputs_with_k)
        members = (ratio.reference,) + tuple(pos for pos, _k in ratio.outputs_with_k)
        if not all(float(k) == int(k) and k >= 1 for k in ks):         # 정수가 아닌 k 가 하나라도 있으면 그 묶음 멤버는 모두 독립 단위
            continue
        grouped.update(members)
        cands = {max(1, math.floor(x[ratio.reference])), max(1, math.ceil(x[ratio.reference]))}
        for pos, k in ratio.outputs_with_k:
            cands.update((max(1, math.floor(x[pos] / k)), max(1, math.ceil(x[pos] / k))))
        factors = (1,) + tuple(int(k) for _pos, k in ratio.outputs_with_k)
        units.append((members, [tuple(factor * m_d for factor in factors) for m_d in sorted(cands)]))
    for i in range(n):
        if i not in grouped:
            units.append(((i,), [(m,) for m in sorted({max(1, math.floor(x[i])), max(1, math.ceil(x[i]))})]))
    return units


def _option_stats(members, option, x):
    """선택지 하나의 (최소 r, 최대 r, 최대 e, e 합, m 합, e 목록)."""
    r = [m / x[i] for i, m in zip(members, option)]
    e = [abs(m - x[i]) / x[i] for i, m in zip(members, option)]
    return min(r), max(r), max(e), math.fsum(e), sum(option), e


def _key(m, x):
    """벡터 m 의 K = (E1, E2, E3, E4, E5) 와 (E1, E2) -- 정의 그대로(멤버 순서)."""
    r = [mi / xi for mi, xi in zip(m, x)]
    e = [abs(mi - xi) / xi for mi, xi in zip(m, x)]
    e1 = max(r) / min(r) - 1
    return (e1, max(e), math.fsum(e), sum(m), tuple(m))


def realize_fingers(w_theta, w_f_m, ratios):
    w_theta, ratios = tuple(w_theta), tuple(ratios)
    n = len(w_theta)
    _check_ratios(n, ratios)
    if not n or not all(_positive_finite(w) for w in w_theta) or not _positive_finite(w_f_m):
        raise SealViolationError(devices=(), detail={"reason": _TIE_UNRESOLVED, "w_theta": w_theta, "w_f_m": w_f_m})
    x = [w / w_f_m for w in w_theta]
    units = _units(n, x, ratios)
    stats = [[_option_stats(members, option, x) for option in options] for members, options in units]
    lows = sorted({s[0] for per_unit in stats for s in per_unit})
    # (1) v = 최소 r 후보마다 단위별 최소 최대 r(H_u) 로 E1(v) = max_u H_u / v - 1, E1* = 최소
    table = []
    for v in lows:
        best = []
        for per_unit in stats:
            highs = [s[1] for s in per_unit if s[0] >= v]
            if not highs:
                break
            best.append(min(highs))
        else:
            table.append((max(best) / v - 1, v))
    e1_star = min(e1 for e1, _v in table)
    # (2) E1(v) = E1* 인 v 마다 허용 선택에서 E2 상한 → 단위별 (Σe, Σm) 최소로 후보 벡터 하나
    candidates = []
    for e1, v in table:
        if e1 != e1_star:
            continue
        allowed = [[(i, s) for i, s in enumerate(per_unit) if s[0] >= v and s[1] / v - 1 <= e1_star] for per_unit in stats]
        e2_star = max(min(s[2] for _i, s in per_unit) for per_unit in allowed)
        m = [0] * n
        for (members, options), per_unit in zip(units, allowed):
            index = min(((s[3], s[4]), i) for i, s in per_unit if s[2] <= e2_star)[1]
            for pos, value in zip(members, options[index]):
                m[pos] = value
        candidates.append(tuple(m))
    # (3) 후보 벡터들 사이에서 K 사전식 최소
    best_m = min(candidates, key=lambda m: _key(m, x))
    e1, e2, _e3, _e4, _e5 = _key(best_m, x)
    return RealizedCell(best_m, e1, e2)
