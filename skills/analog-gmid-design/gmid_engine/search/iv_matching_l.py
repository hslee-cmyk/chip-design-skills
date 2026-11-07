"""matching L 하한(절대 offset 제약)과 offset 가드 부하 gm/ID 상한 (설계 41 §6.4-2·2a, 사용자 결정 2026-10-08 Q3; D-SId, 40 §11 U13 `iv_matching_l`).

진입점: `matching_bounds(ctx, currents, lengths, gm_id_lo, gm_id_cap=None, wf_keys=None) -> MatchingBounds`.

* **mismatch slope bin 의 손가락 폭 w_f**(FS-1, 계획 v6.39.3 DEC-108 (3) 끝): `wf_keys`(= {소자: 출발 w_f 칸 키}, 블록 안 값 -- 호출 인자) 가 있는 6단계 가드 경로는 그 소자 칸 키 × 제조 격자,
  `wf_keys` 가 없는 4단계 L 하한 경로(L 선택 전 -- w_f 칸이 정해지기 전)는 LUT 선언 기준 폭 슬라이스의 폭 `w_ref_m`(`slice_of(ctx, kind).w_m`, 출발 W (가)와 같은 슬라이스). 칸 키가 None 인
  소자(출발 불능)는 가드를 계산하지 않고 `wf_start_undefined` 로 비활성이다. 면적 항은 총 폭 W.

* **절대 offset 제약이 있는 회로에서만 L 하한이 활성이다**(`offset_in_sigma_mv <= s`). 구조 가드(`offset_excess <= E`)만 있는 회로는 L 하한이 아니라 부하 gm/ID 상한으로 간다.
* **mismatch 모델**(A_eff): 소자 하나의 게이트 환산 σ_VGS(W, L, 점) 는 U3 `mismatch_sigma_vgs` 가 낸다 -- LUT 감도 열 DVGS_k(변수 `vth0`·`toxe`·`voff`·`nfactor` 등 slope 변수 전수)에
  PDK bin slope 를 곱해 √Σ 로 합성하고 √(W_ref/W) 로 기하 환산한 값. 쌍의 σ_ΔVGS = √2·σ_VGS(두 소자 독립), A_eff(L, gm/ID) = σ_ΔVGS·√(W·L)(읽는 쪽에서 계산, 열로 저장하지 않는다).
* **L 하한**(41 §6.4-2): 입력 셀 몫 σ_share = σ_target/√2(입력 셀 분산 = 나머지 분산 -- 부하 기여 ≤ 입력쌍 기여의 경계, 새 상수가 아니다). 입력 셀 소자 면적 하한
  A_min(L, gm/ID) = A_eff²/σ_share², **L ≥ √(A_min·IDu/I)**. A_eff 가 L 에 의존하므로 LUT L 앵커를 오름차순으로 훑고, 앞 앵커가 실패하고 같은 bin 의 다음 앵커가 만족하면 그 bin 안에서
  bisection(`bracket_root`)한다 -- L 은 같은 모델 bin 안에서만 보간한다. gm/ID 는 입력 소자의 하한(gm/ID_lo, 헤드룸), 전류 I 는 1회차 매크로 전류.
* **offset 가드 부하 상한**(41 §6.4-2a): 부하 소자 k 의 입력 환산 분산 비 Σ_k (gm_k·σ_VGS,k)² / Σ_in (gm_in·σ_VGS,in)² ≤ E² − 1(offset_excess = √(총 분산 / 입력 분산)) 이 되도록
  부하 gm/ID 를 상한으로 둔다(`guard_bounds`). gm_k/gm_in 은 매크로 전류 비, gm/ID_in 은 입력 소자의 하한.
* LUT mismatch 데이터가 없으면(`lut_mismatch_unavailable` 등 U3 사유) 계산하지 않고 그 사유를 비활성으로 남긴다 -- 41 §6.4-2b 의 `mismatch_lut_missing` 정지는 로드 단계의 몫이다.
* **가드의 입력 쪽 gm/ID**: 입력 기여는 입력 소자가 가질 수 있는 최대(가드 아닌 경계가 정한 상한 `gm_id_cap`, 없으면 하한)에서 잰다 -- 부하는 최소·입력은 최대가 '가능한 가장 느슨한 경우'라서
  거짓 충돌을 만들지 않는다(`guard_input_gm_id`). 소자 폭은 PDK 최소 finger 폭 W_min 이상으로 맞춘 뒤 σ 를 잰다(모델 bin 밖 폭 방지).
출발값 전용(EP-7): 판정은 봉인 스냅샷의 `offset_in_sigma_mv`·`offset_excess`(MNA 전회로)가 한다.
"""
import dataclasses
import math
import sys

from gmid_engine.core import MILLI, SchemaRejectedError, SealViolationError
from gmid_engine.lut import mismatch_sigma_vgs
from gmid_engine.sizing import bracket_root

from ._helpers_curves import QUANTITY_IDU, QUANTITY_VGS, curve_bundle_of, curve_value, l_anchors, slice_of
from ._helpers_guard import Tolerant, guard_bounds, guard_devices, guard_input_gm_id
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

REASON_WF_START_UNDEFINED = "wf_start_undefined"      # 소자 칸 키가 None(출발 불능) -- 가드 slope bin 폭을 정할 수 없다
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


def _slope_width(ctx, name, wf_keys):
    """slope bin 의 손가락 폭 w_f: `wf_keys` 가 있으면 그 소자 칸 키 × 제조 격자(키가 None 이면 출발 불능 -- `wf_start_undefined`), 없으면(4단계, w_f 칸 이전) 기준 폭 슬라이스 폭 `w_ref_m`."""
    d = ctx.by_name[name]
    if wf_keys is None:
        return slice_of(ctx, d.kind).w_m
    key = wf_keys.get(name)
    if key is None:
        raise SealViolationError(devices=(name,), detail={"reason": REASON_WF_START_UNDEFINED})
    return key * ctx.memo.lut.spec.manufacturing_grid_m


def _sigma_vgs(ctx, name, g, L, current, wf_keys):
    """소자 `name` 의 σ_VGS(V) -- 폭 W = I·L/IDu(gm/ID, L), 기준 (VDS, VSB) 점. slope bin 은 손가락 폭 w_f(`_slope_width`), 면적 항은 총 폭 W."""
    d = ctx.by_name[name]
    bundle = curve_bundle_of(ctx, d.name, d.kind, L)
    w = max(current * L / curve_value(bundle, QUANTITY_IDU, g), ctx.w_min_m)      # 실현 폭은 PDK 최소 finger 폭 W_min 이상(W 하한 제약 S-18): 그 아래 폭은 mismatch 모델 bin 밖이다
    vgs = curve_value(bundle, QUANTITY_VGS, g)
    curve = bundle[QUANTITY_IDU]
    return mismatch_sigma_vgs(ctx.memo, ctx.pdk.mismatch_model(d.kind), d.kind, d.w_key, L, vgs, curve.vds, curve.vsb, _slope_width(ctx, name, wf_keys), w).sigma_v


def _sigma_from(ctx, name, g, L, current, wf_keys):
    """σ_VGS 를 gm/ID = g 에서 재되, 감도 열이 정의되지 않는 점(강반전 끝 등 `lut_mismatch_undefined`)이면 곡선 마디를 gm/ID 가 큰 쪽으로 올라가며 처음 정의된 점에서 잰다
    (입력 소자의 gm/ID 는 하한 이상 어디든 가능 -- 하한이 LUT 가 모르는 점이면 그 위 첫 정의 점이 하한의 가장 가까운 실현 가능 값이다). 하나도 정의되지 않으면 처음 예외를 던진다."""
    try:
        return _sigma_vgs(ctx, name, g, L, current, wf_keys)
    except _LUT_ERRORS as first:
        d = ctx.by_name[name]
        for node in sorted(float(x) for x in curve_bundle_of(ctx, d.name, d.kind, L)[QUANTITY_IDU].gm_id if x > g):
            try:
                return _sigma_vgs(ctx, name, node, L, current, wf_keys)
            except _LUT_ERRORS:
                continue
        raise first


def _l_lower(ctx, name, current, g, sigma_share):
    """입력 소자의 L 하한 -- 쌍 σ_ΔVGS = √2·σ_VGS ≤ σ_share 인 최소 L (앵커 오름차순 + 같은 bin 안 bisection). 없으면 None."""
    d = ctx.by_name[name]

    def slack(L):
        return sigma_share - _SQRT2 * _sigma_from(ctx, name, g, L, current, None)      # 4단계(L 선택 전): slope bin 은 기준 폭 슬라이스 -- w_f 칸을 읽지 않는다

    anchors = [L for L in l_anchors(ctx, d.kind) if curve_bundle_of(ctx, d.name, d.kind, L) is not None]
    bins = slice_of(ctx, d.kind).l_bins
    index = {float(a): i for i, a in enumerate(l_anchors(ctx, d.kind))}
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


def matching_bounds(ctx, currents, lengths, gm_id_lo, gm_id_cap=None, wf_keys=None):
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
    # L 하한과 가드는 서로 독립이다 -- 한쪽이 LUT 에서 정의되지 않아도 다른 쪽은 계산한다(비활성 사유는 각자)
    try:
        if absolute:
            share = min(absolute) * MILLI / _SQRT2
            for name in inputs:
                L = _l_lower(ctx, name, currents[name], gm_id_lo[name], share)
                if L is None:
                    # 어느 LUT L 앵커도 못 맞춘다 -- 충돌을 남기고(41 §6.6) 요구 방향으로 닫는다: 하한 = 정의된 가장 긴 L 앵커(가장 잘 맞는 쪽)
                    conflicts.append(StartConflict(name, QUANTITY_L, ((SRC_MATCH_L, share),), share))
                    L = max(a for a in l_anchors(ctx, ctx.by_name[name].kind) if curve_bundle_of(ctx, name, ctx.by_name[name].kind, a) is not None)
                bounds[name] = (Bound(QUANTITY_L, SIDE_LO, SRC_MATCH_L, L),)
    except _LUT_ERRORS as exc:
        bounds, conflicts = {}, []
        inactive.append((SRC_MATCH_L, _reason(exc)))
    try:
        if guard and loads:
            def term(name, g):
                return (g * currents[name] * _sigma_vgs(ctx, name, g, lengths[name], currents[name], wf_keys)) ** 2
            term = Tolerant(term)
            found, lost = guard_bounds(ctx, inputs, loads, term, min(guard) ** 2 - 1, lengths, gm_id_lo,
                                       guard_input_gm_id(ctx, term, inputs, lengths, gm_id_lo, gm_id_cap), SRC_OFFSET_GUARD)
            bounds.update(found)
            conflicts.extend(lost)
    except _LUT_ERRORS as exc:
        inactive.append((SRC_OFFSET_GUARD, _reason(exc)))
    return MatchingBounds(bounds, tuple(conflicts), tuple(inactive))
