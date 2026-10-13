"""이득 L 하한 (설계 41 §6.4-1, H3; D-SIc).

진입점: `gain_l_bounds(ctx, elements, resistors, gm_id_lo) -> GainLBounds`(1회차 매크로 뒤). 입력 묶음 `GainInputs` 는 출발 구간 블록 호출 안에서 `iv_context.start_view` 가 만든다(`ctx.gain`).

41 §6.4-1: 블록 목표 g_i = G·A_i,max / Σ A_max (dB 영역) 를 만족하는 최소 L(블록 국소 모델 gain ≥ g_i; bin 오름차순으로 훑고 bin 안에서 풀이). **A_max 가 하나라도 미상이거나 gain 제약이
없으면 비활성**이다(H3) -- 사유(`constraint_not_declared`·`u9_value_not_certified`)는 보고 표 `inactive` 로 간다.

* **블록 국소 모델**: U9 와 같은 모델(`metrics.block_gain_model_of` -> `BlockModel`, 파라미터 표 `ParamTables`, 행 풀이 `row_gains`)을 그대로 쓴다. 입력 묶음은 U9 가 쓴 S0 수준 필드
  `graph/ach: local_inputs`(`LocalInputs.view`), 블록 대상 `BlockSpec` 은 U9 와 같은 함수(`block_spec`)로 만든다 -- 복제하지 않는다.
* **한 행**: 블록의 모든 L 축을 같은 LUT L 앵커(색인 j)로 두고(L 하한은 블록 소자 모두에 걸린다), 전류 축·저항 축은 1회차 매크로 상태의 θ 전류·저항 값(연속 축 `cont`), VGS 축(= gm/ID)은 그룹 멤버 모두의
  gm/ID ≥ gm/ID_lo 인 마디 중 **진성 이득 gm/gds 의 최솟값(멤버 중)이 가장 큰 마디**(41 §6.1 순서 2 '[gm/ID_lo, LUT 최대] 에서 intrinsic gain 이 가장 큰 gm/ID'), VDS 축은 소자 동작점의 가장
  가까운 LUT 격자, VSB 는 격자 0. 전류 공통 배율로 뺀 축(`BlockModel.normalized`)은 기준 원소 대비 비로 준다.
* **풀이**: 앵커를 L 오름차순으로 훑어 처음 gain ≥ g_i 인 앵커 j 를 찾고, 앞 앵커가 같은 모델 bin 안에서 실패했으면 두 앵커 사이 gain(dB)이 L 에 대해 선형이라고 보고 g_i 와 만나는 L 을 내놓는다
  (파라미터 표가 앵커 격자라 bin 안 L 에서는 모델을 다시 풀 수 없다 -- 설계의 bin 안 bisection 대신 앵커 사이 선형 보간, 기록). 어느 앵커도 못 맞추면 충돌 레코드(41 §6.6)를 남기고 가장 긴 앵커로 닫는다.
* L 하한은 블록 MOS 모두에 건다(소자별 하한이 아니라 블록 하나의 L). 곡선·표가 정의되지 않은 앵커는 건너뛴다. 출발값 전용(EP-7).
"""
import dataclasses
import math

import numpy as np

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE
from gmid_engine.metrics import block_gain_model_of, row_gains

from ._helpers_curves import slice_of
from .start_values import QUANTITY_L, SIDE_LO, SRC_GAIN_L, Bound, StartConflict

# U9 축 어휘(metrics/achievability_types.py 의 AXIS_KIND_*) -- metrics 공개 API 가 이 상수를 내보내지 않아 같은 문자열을 둔다(`iv_headroom` 과 같은 사정)
AXIS_KIND_VGS = "vgs"
AXIS_KIND_L = "L"
AXIS_KIND_VDS = "vds"
AXIS_KIND_CURRENT = "current"
AXIS_KIND_RESISTOR = "resistor"


@dataclasses.dataclass(frozen=True)
class GainLBounds:
    """`bounds` = {소자: (Bound, ...)}(L 하한), `conflicts`, `inactive` = ((경계 식, 사유), ...)."""

    bounds: object
    conflicts: tuple
    inactive: tuple


def _nearest(grid, value):
    return int(np.argmin(np.abs(np.asarray(grid, dtype=float) - value)))


def _row(ctx, inputs, model, j_l, g_lo, elements, resistors):
    """L 앵커 색인 j_l 에서의 (idx 한 행, cont) 또는 None(표·값이 정의되지 않음). VGS 축은 진성 이득 최대 마디."""
    tables = inputs.tables
    grids = inputs.local.grids
    n_v = len(grids[1])
    idx = np.zeros((1, len(model.axes)), dtype=int)
    cont = {}
    for i, axis in enumerate(model.axes):
        if axis.kind == AXIS_KIND_L:
            idx[0, i] = j_l
        elif axis.kind == AXIS_KIND_VDS:
            idx[0, i] = _nearest(grids[2], ctx.points.get(axis.label[0], (grids[2][0], 0.0))[0])
        elif axis.kind == AXIS_KIND_CURRENT:
            ref = model.normalized[0] if model.normalized else None
            source = axis.label[0]
            if source not in elements or (ref is not None and ref not in elements):
                return None
            cont[i] = np.asarray([elements[source] / (1.0 if ref is None else elements[ref])])
        elif axis.kind == AXIS_KIND_RESISTOR:
            value = resistors.get(axis.label[0])
            if value is None or not value > 0:
                return None
            cont[i] = np.asarray([1.0 / value])
    nodes = np.arange(n_v)
    for i, axis in enumerate(model.axes):
        if axis.kind != AXIS_KIND_VGS:
            continue
        score = np.full(n_v, np.inf)
        for m in model.mos:
            if m.vgs_axis != i:
                continue
            i_vds = idx[0, m.vds_axis] if m.vds_axis >= 0 else tables.vds_of_vgs[nodes]
            i_vsb = idx[0, m.vsb_axis] if m.vsb_axis >= 0 else 0
            x, y, _z = tables.lookup(m.kind, np.full(n_v, j_l), np.broadcast_to(i_vds, (n_v,)), np.full(n_v, i_vsb), nodes)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = x / y
                gain = np.where((x >= g_lo.get(m.name, 0.0)) & np.isfinite(ratio), ratio, -np.inf)
            score = np.minimum(score, gain)
        if not np.isfinite(np.max(score)):
            return None
        idx[0, i] = int(np.argmax(score))
    return idx, cont


def _gain_db(model, inputs, row):
    value = float(row_gains(model, inputs.tables, row[0], row[1])[0])
    return AMPLITUDE_DB_PER_DECADE * math.log10(value) if value > 0 and math.isfinite(value) else None


def gain_l_bounds(ctx, elements, resistors, gm_id_lo):
    inputs = ctx.gain
    if inputs is None:
        return GainLBounds({}, (), ctx.gain_inactive)
    bounds, conflicts, inactive = {}, [], []
    anchors = [float(a) for a in inputs.local.grids[0]]
    for spec, target in inputs.blocks:
        members = [m for m in spec.members if m in ctx.by_name]
        model, reason = block_gain_model_of(inputs.local, spec)
        if model is None:
            inactive.append((SRC_GAIN_L, reason))
            continue
        if not members:
            continue
        bins = slice_of(ctx, ctx.by_name[members[0]].kind).l_bins
        previous = None                         # (앵커 색인, L, gain dB) 앞 유효 앵커
        found = None
        for j, L in enumerate(anchors):
            row = _row(ctx, inputs, model, j, gm_id_lo, elements, resistors)
            db = None if row is None else _gain_db(model, inputs, row)
            if db is None:
                continue
            if db >= target:
                same_bin = previous is not None and bool(bins.anchor_bin) and bins.anchor_bin[previous[0]] == bins.anchor_bin[j]
                found = previous[1] + (target - previous[2]) / (db - previous[2]) * (L - previous[1]) if same_bin and previous[2] < target else L
                break
            previous = (j, L, db)
        if found is None:
            found = anchors[-1] if previous is None else previous[1]
            conflicts.append(StartConflict(members[0], QUANTITY_L, ((SRC_GAIN_L, target),), target - (0.0 if previous is None else previous[2])))
        for m in members:
            bounds[m] = (Bound(QUANTITY_L, SIDE_LO, SRC_GAIN_L, found),)
    return GainLBounds(bounds, tuple(conflicts), tuple(inactive))
