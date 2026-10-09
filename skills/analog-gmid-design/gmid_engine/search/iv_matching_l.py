"""matching L 하한(절대 offset 제약)과 offset 가드 부하 gm/ID 상한 (설계 41 §6.4-2·2a, 사용자 결정 2026-10-08 Q3; D-SId, 40 §11 U13 `iv_matching_l`).

진입점: `matching_bounds(ctx, currents, lengths, gm_id_lo) -> MatchingBounds`.

* **절대 offset 제약이 있는 회로에서만 L 하한이 활성이다**(`offset_in_sigma_mv <= s`). 구조 가드(`offset_excess <= E`)만 있는 회로는 L 하한이 아니라 부하 gm/ID 상한으로 간다.
* **mismatch 모델**(A_eff): 소자 하나의 게이트 환산 σ_VGS(W, L, 점) 는 U3 `mismatch_sigma_vgs` 가 낸다 -- LUT 감도 열 DVGS_k(변수 `vth0`·`toxe`·`voff`·`nfactor` 등 slope 변수 전수)에
  PDK bin slope 를 곱해 √Σ 로 합성하고 √(W_ref/W) 로 기하 환산한 값. 쌍의 σ_ΔVGS = √2·σ_VGS(두 소자 독립), A_eff(L, gm/ID) = σ_ΔVGS·√(W·L)(읽는 쪽에서 계산, 열로 저장하지 않는다).
* **L 하한**(41 §6.4-2): 입력 셀 몫 σ_share = σ_target/√2(입력 셀 분산 = 나머지 분산 -- 부하 기여 ≤ 입력쌍 기여의 경계, 새 상수가 아니다). 입력 셀 소자 면적 하한
  A_min(L, gm/ID) = A_eff²/σ_share², **L ≥ √(A_min·IDu/I)**. A_eff 가 L 에 의존하므로 LUT L 앵커를 오름차순으로 훑고, 앞 앵커가 실패하고 같은 bin 의 다음 앵커가 만족하면 그 bin 안에서
  bisection(`bracket_root`)한다 -- L 은 같은 모델 bin 안에서만 보간한다. gm/ID 는 입력 소자의 하한(gm/ID_lo, 헤드룸), 전류 I 는 1회차 매크로 전류.
* **offset 가드 부하 상한**(41 §6.4-2a): 부하 소자 k 의 입력 환산 분산 비 Σ_k (gm_k·σ_VGS,k)² / Σ_in (gm_in·σ_VGS,in)² ≤ E² − 1(offset_excess = √(총 분산 / 입력 분산)) 이 되도록
  부하 gm/ID 를 상한으로 둔다(`guard_bounds`). gm_k/gm_in 은 매크로 전류 비, gm/ID_in 은 입력 소자의 하한.
* LUT mismatch 데이터가 없으면(`lut_mismatch_unavailable` 등 U3 사유) 계산하지 않고 그 사유를 비활성으로 남긴다 -- 41 §6.4-2b 의 `mismatch_lut_missing` 정지는 로드 단계의 몫이다.
출발값 전용(EP-7): 판정은 봉인 스냅샷의 `offset_in_sigma_mv`·`offset_excess`(MNA 전회로)가 한다.
"""
import dataclasses
import math
import sys

from gmid_engine.core import MILLI, SchemaRejectedError, SealViolationError
from gmid_engine.lut import mismatch_sigma_vgs
from gmid_engine.sizing import bracket_root

from ._helpers_guard import guard_bounds, guard_devices
from .iv_curves import QUANTITY_IDU, QUANTITY_VGS
from .start_values import (
    QUANTITY_L,
    SIDE_LO,
    SRC_MATCH_L,
    SRC_OFFSET_GUARD,
    WHY_NO_CURRENT,
    WHY_NO_LUT,
    WHY_NO_TARGET,
    Bound,
    StartConflict,
)

_METRIC_ABSOLUTE = "offset_in_sigma_mv"
_METRIC_GUARD = "offset_excess"
_LUT_ERRORS = (SealViolationError, SchemaRejectedError)
_SQRT2 = math.hypot(1, 1)          # √2 -- 두 소자 독립인 쌍의 σ 합성 계수


@dataclasses.dataclass(frozen=True)
class MatchingBounds:
    """`bounds` = {소자: (Bound, ...)}(입력 소자 L 하한, 부하 gm/ID 상한), `conflicts`, `inactive` = ((경계 식, 사유), ...)."""

    bounds: object
    conflicts: tuple
    inactive: tuple


def _reason(exc):
    return dict(exc.record.detail).get("reason", WHY_NO_LUT)


def _sigma_vgs(ctx, name, g, L, current):
    """소자 `name` 의 σ_VGS(V) -- 폭 W = I·L/IDu(gm/ID, L), 기준 (VDS, VSB) 점."""
    d = ctx.by_name[name]
    bundle = ctx.curves.bundle_of(d.name, d.kind, L)
    w = current * L / ctx.curves.value(bundle, QUANTITY_IDU, g)
    vgs = ctx.curves.value(bundle, QUANTITY_VGS, g)
    curve = bundle[QUANTITY_IDU]
    return mismatch_sigma_vgs(ctx.memo, ctx.pdk.mismatch_model(d.kind), d.kind, d.w_key, L, vgs, curve.vds, curve.vsb, w).sigma_v


def _l_lower(ctx, name, current, g, sigma_share):
    """입력 소자의 L 하한 -- 쌍 σ_ΔVGS = √2·σ_VGS ≤ σ_share 인 최소 L (앵커 오름차순 + 같은 bin 안 bisection). 없으면 None."""
    d = ctx.by_name[name]

    def slack(L):
        return sigma_share - _SQRT2 * _sigma_vgs(ctx, name, g, L, current)

    anchors = [L for L in ctx.curves.l_anchors(d.kind) if ctx.curves.bundle_of(d.name, d.kind, L) is not None]
    bins = ctx.curves.slice_of(d.kind).l_bins
    index = {float(a): i for i, a in enumerate(ctx.curves.l_anchors(d.kind))}
    previous = None
    for L in anchors:
        if slack(L) >= 0:
            same_bin = previous is not None and bins.anchor_bin and bins.anchor_bin[index[previous]] == bins.anchor_bin[index[L]]
            if same_bin:
                root, _a, _b = bracket_root(slack, previous, L, math.sqrt(sys.float_info.epsilon) * L)
                return L if root is None else root
            return L
        previous = L
    return None


def matching_bounds(ctx, currents, lengths, gm_id_lo):
    absolute = [v for m, op, v in ctx.constraints if m == _METRIC_ABSOLUTE and op == "<="]
    guard = [v for m, op, v in ctx.constraints if m == _METRIC_GUARD and op == "<="]
    inputs, loads = guard_devices(ctx)
    inactive = []
    if not absolute:
        inactive.append((SRC_MATCH_L, WHY_NO_TARGET))
    if not guard:
        inactive.append((SRC_OFFSET_GUARD, WHY_NO_TARGET))
    if not (absolute or guard):
        return MatchingBounds({}, (), tuple(inactive))
    if not inputs or any(currents.get(n) is None for n in inputs + loads):
        return MatchingBounds({}, (), tuple(inactive) + ((SRC_OFFSET_GUARD, WHY_NO_CURRENT),))
    bounds, conflicts = {}, []
    try:
        if absolute:
            share = min(absolute) * MILLI / _SQRT2
            for name in inputs:
                L = _l_lower(ctx, name, currents[name], gm_id_lo[name], share)
                if L is None:
                    conflicts.append(StartConflict(name, QUANTITY_L, ((SRC_MATCH_L, share),), share))
                else:
                    bounds[name] = (Bound(QUANTITY_L, SIDE_LO, SRC_MATCH_L, L),)
        if guard and loads:
            def term(name, g):
                return (g * currents[name] * _sigma_vgs(ctx, name, g, lengths[name], currents[name])) ** 2
            found, lost = guard_bounds(ctx, inputs, loads, term, min(guard) ** 2 - 1, lengths, gm_id_lo, gm_id_lo[inputs[0]], SRC_OFFSET_GUARD)
            bounds.update(found)
            conflicts.extend(lost)
    except _LUT_ERRORS as exc:
        return MatchingBounds({}, (), tuple(inactive) + ((SRC_MATCH_L if absolute else SRC_OFFSET_GUARD, _reason(exc)),))
    return MatchingBounds(bounds, tuple(conflicts), tuple(inactive))
