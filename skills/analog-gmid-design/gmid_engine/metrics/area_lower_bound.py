"""인증된 면적 하한 A_lb (설계 41 §4.4, 40 §7.1-3, 결정 11, D-GB4d; GB4 단계 A7 `area`).

진입점: `area_lower_bound(lut, mos_kind, basis_rows, fixed, caps, budget_m2, b_a_m2) -> AreaBound`.

A_lb = Σ_k I_k,cert · L_min,k² / IDu_max,k + Σ_c C_c,min · (면적 / 용량)_c

* `mos_kind` = {MOS: kind}, `basis_rows` = {소자: ((원천 원소, 계수), ...)}(`CurrentBasis.rows`), `fixed` = {값 선언 이상 전류원: A}.
* **I_k,cert**: 그 MOS 전류식이 값이 선언된 이상 전류원만 읽을 때의 |Σ 계수·값|(KCL 로 값이 고정된 가지 전류). θ 전류 성분을 하나라도 읽으면 인증할 수 없어 0 이다(보수) --
  `AreaBound.not_certified` 에 (소자, 'current_depends_on_theta') 로 남긴다. 전류식이 비면 0.
* **L_min,k** = kind k 의 LUT L 격자 최솟값(PDK 최소 L 이상인 LUT 점). **IDu_max,k** = kind k 의 모든 폭 슬라이스의 전류밀도 IDu = ID·L/w_m (on_mask 점) 최댓값 --
  W·L = ID·L²/IDu 라 전류 밀도가 최대일 때 면적이 최소다. 격자 배열 통계이고 보간 조회가 아니다(`search_domain` 의 ln IDu 포락선과 같은 양).
* **커패시터 항**: `caps` = ((소자, C_min F, 면적/용량 m²/F), ...) -- C_min = 값이 선언된 커패시터는 그 값, 미선언은 spec θ 하한, 측정 부하는 호출부가 뺀다(`search.passive_area_decl`).
  저항 면적은 하한에 넣지 않는다(설계 식에 없음 -- 넣지 않아도 하한은 유효하다).
* `budget_m2` = `area_search_m2 <= B` 중 가장 작은 B(없으면 None), `b_a_m2` = 면적 분해능 b_A(PDK `manufacturing_grid_m` × `min_finger_w_m`). A_lb > B + b_A 이면 verdict
  `infeasible`(사유 `area_budget_below_lower_bound`), 아니면 `not_excluded`, 예산이 없으면 `no_target`. 출발값으로 만든 면적 추정 A_est 는 정지 근거로 쓰지 않는다(C1).
"""
import numpy as np

from .achievability_types import (
    VERDICT_INFEASIBLE,
    VERDICT_NO_TARGET,
    VERDICT_NOT_EXCLUDED,
    AreaBound,
)

NOT_CERTIFIED_THETA = "current_depends_on_theta"


def _kind_extrema(lut, kind):
    """(L 최솟값, IDu 최댓값) -- kind 의 모든 폭 슬라이스."""
    l_min, idu_max = np.inf, -np.inf
    for (k, _w_key), sl in sorted(lut.slice_map.items()):
        if k != kind:
            continue
        grid_l = np.asarray(sl.grids[0], dtype=float)
        l_min = min(l_min, float(grid_l.min()))
        idu = np.asarray(sl.ID, dtype=float) * grid_l[:, None, None, None] / sl.w_m
        idu_max = max(idu_max, float(np.max(np.where(np.asarray(sl.on_mask, dtype=bool), idu, -np.inf))))
    return l_min, idu_max


def area_lower_bound(lut, mos_kind, basis_rows, fixed, caps, budget_m2, b_a_m2):
    extrema = {kind: _kind_extrema(lut, kind) for kind in sorted(set(mos_kind.values()))}
    terms, not_certified = [], []
    for name in sorted(mos_kind):
        row = tuple(basis_rows.get(name, ()))
        if any(source not in fixed for source, _coeff in row):
            not_certified.append((name, NOT_CERTIFIED_THETA))
            continue
        current = abs(sum(coeff * fixed[source] for source, coeff in row))
        l_min, idu_max = extrema[mos_kind[name]]
        if current > 0:
            terms.append((name, current * l_min * l_min / idu_max))
    for name, c_min, per_farad in sorted(caps):
        terms.append((name, c_min * per_farad))
    total = float(sum(v for _n, v in terms))
    if budget_m2 is None:
        verdict = VERDICT_NO_TARGET
    else:
        verdict = VERDICT_INFEASIBLE if total > budget_m2 + b_a_m2 else VERDICT_NOT_EXCLUDED
    return AreaBound(total, tuple(terms), budget_m2, b_a_m2, verdict, tuple(not_certified))
