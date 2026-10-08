"""평가 커널 본체 -- θ -> ②③④⑤ 계산 블록 -> 봉인 (설계 3.2·5절, 계획 N3.5 평가 커널).

진입점: `run_kernel(ctx, theta, parent, w_request, raise_on_violation) -> DcEvaluation`.
`size_and_seal`(후보 위반이면 예외)과 `size_and_seal_local`(위반 보고서를 항목별로 읽는다)이 같은 계산을 쓴다. 규칙·순서·캐시는 `size_and_seal.py`
머리 설명과 같다. 함께 있는 도우미: `normalize_w_request`(W_request 검증·정렬), `previous_gm_id`(S2p -- 봉인된 parent 의 소자별 gm/ID).
"""
import math
import sys

from gmid_engine.graph import ELEMENT_MOS

from .block_columns import dc_columns
from .block_currents import dc_currents
from .block_lengths import dc_lengths
from .block_widths import dc_widths
from .s2_values import (
    COORD_WRITER,
    THETA_CURRENT,
    THETA_L,
    THETA_LN_IDU,
    THETA_RESISTANCE,
    THETA_Y,
    DcEvaluation,
    KernelContext,
    Theta,
)
from .seal import seal_dc
from .seal_tolerances import gm_grid_max
from .theta_check import check_theta

_COLUMN_KINDS = (THETA_LN_IDU, THETA_RESISTANCE, THETA_Y)
_GM_ID_FRESH = 2 * sys.float_info.epsilon   # ss.gm = ID·(gm/ID) 를 ID 로 다시 나눈 값과 dc_op.gm_id 의 상대 일치 -- 곱셈·나눗셈 반올림 두 번의 몫(각 ≤ eps/2)


def normalize_w_request(ctx, w_request):
    """W_request -> ((MOS, W), ...) 이름순. MOS 가 아닌 이름·비양수·비유한 W·같은 소자가 두 번 있는 요청은 `ValueError`(호출 계약 위반)."""
    pairs = w_request.items() if hasattr(w_request, "items") else w_request
    out = {}
    mos = {name for name, cls in ctx.base.column("device", "element_class") if cls == ELEMENT_MOS}
    for name, width in pairs:
        if name not in mos:
            raise ValueError("size_and_seal: w_request 이름이 MOS 가 아니다 " + repr(name))
        if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width) or not width > 0:
            raise ValueError("size_and_seal: w_request 는 유한 양수여야 한다 " + repr((name, width)))
        if name in out:
            raise ValueError("size_and_seal: w_request 에 같은 소자가 두 번 있다 " + repr(name))
        out[name] = float(width)
    return tuple(sorted(out.items()))


def previous_gm_id(parent):
    """S2p -- 봉인된 parent 의 소자별 gm/ID = `ss_dev.gm` ÷ `dc_op.current` ((소자, gm/ID), ...). parent 가 봉인 점이 아니거나 `ss_dev` 가
    그 점에서 나온 것이 아니면(옛 점의 필드가 남은 스냅샷) 그 소자는 뺀다 -- tol_I 가 오래된 gm 에 기대지 않게."""
    if parent is None or parent.sealed is None:
        return ()
    ops = dict(parent.snapshot.column("device", "dc_op"))
    out = []
    for m, ss in parent.snapshot.column("device", "ss_dev"):
        op = ops.get(m)
        if op is not None and op.current > 0 and ss.gm > 0:
            gm_id = ss.gm / op.current
            if math.isclose(gm_id, op.gm_id, rel_tol=_GM_ID_FRESH):
                out.append((m, canonical_gm_id(gm_id * op.current, op.current)))
    return tuple(sorted(out))


def canonical_gm_id(bound, current):
    """`bound` = gm/ID × `current` (부동소수 곱)를 그대로 내는 가장 작은 gm/ID -- 같은 허용오차 상계(`dc_gm_bound`)를 낳는 gm/ID 는 하나로 정한다.
    S2p tol_I 입력을 상계에서 되찾아도 비트가 같아지게 하는 정규형(수동소자 θ 만 바뀐 자식이 parent 와 같은 허용오차 입력을 갖는다, DEC-92). 곱이 `bound` 를
    정확히 내는 값이 없으면(격자 최대 gm 에서 온 상계) None."""
    g = bound / current
    direction = None
    while g * current != bound:                         # 몫의 반올림 한 번 -- 곱이 bound 와 어긋나도 이웃 부동소수 몇 개 안에서 닿는다
        step = g * current < bound
        if direction is not None and step != direction:  # 한 방향으로 가다 건너뛰었다 -> 곱이 bound 인 g 가 없다
            return None
        direction = step
        g = math.nextafter(g, math.inf if step else 0.0)
    while math.nextafter(g, 0.0) * current == bound:
        g = math.nextafter(g, 0.0)
    return g


def inherited_gm_id(parent, snapshot, lut):
    """새 `dc_op` 전체가 parent 와 같을 때(수동소자 θ 만 바뀜) tol_I 입력 -- parent 가 허용오차에 실제로 쓴 gm/ID(상계 ÷ 전류, 정규형). 격자 최대 gm 이
    상계인 소자는 뺀다. 이 값은 parent 의 계통에서만 정해지므로 수동소자만 다른 자식은 parent 와 같은 입력을 갖는다."""
    bounds = dict(parent.snapshot.column("device", "dc_gm_bound"))
    out = []
    for m, op in snapshot.column("device", "dc_op"):
        bound = bounds.get(m)
        if bound is None or bound == gm_grid_max(lut, m, op):
            continue
        g = canonical_gm_id(bound, op.current)
        if g is not None:
            out.append((m, g))
    return tuple(sorted(out))


def run_kernel(ctx, theta, parent, w_request, raise_on_violation):
    """평가 커널 본체 -- `size_and_seal`(위반이면 예외)과 `size_and_seal_local`(위반 보고서를 그대로 읽는다)이 같은 계산을 쓴다."""
    if not isinstance(ctx, KernelContext):
        raise TypeError("size_and_seal: ctx 는 build_kernel_context 결과여야 한다")
    theta = check_theta(ctx.schema, theta.values if isinstance(theta, Theta) else theta)
    snapshot = ctx.base
    if parent is not None:
        if not isinstance(parent, DcEvaluation) or tuple(
                (w, parent.snapshot.block_version(w)) for w, _v in ctx.plan_versions) != ctx.plan_versions:
            raise ValueError("size_and_seal: parent 는 같은 커널 컨텍스트에서 나온 DcEvaluation 이어야 한다")
        snapshot = parent.snapshot
    items = theta.values
    currents = tuple((key, v) for (kind, key), v in items if kind == THETA_CURRENT)
    lengths = tuple((key, v) for (kind, key), v in items if kind == THETA_L)
    owner_length = dict(lengths)
    lengths += tuple((member, owner_length[owner]) for member, owner in ctx.l_ties)     # L 동치류: 멤버 L = 주인 θ L (LR1)
    column_items = tuple(((kind, key), v) for (kind, key), v in items if kind in _COLUMN_KINDS)
    requested = normalize_w_request(ctx, w_request)
    steps = [(dc_currents, (currents,)), (dc_lengths, (lengths,))]
    for block, extras in steps:
        snapshot = block(snapshot, *extras)
    if requested:
        # LY3: 쓰기 소자의 좌표를 요청 W 에서 정한다 -- ln IDu = ln(ID·L/W). 종속 소자는 좌표가 노드 VGS 순방향이라 건드리지 않는다
        writers = {m for m, coord in ctx.base.column("device", "dc_coord") if coord.role == COORD_WRITER}
        current, length = dict(snapshot.column("device", "dc_current")), dict(snapshot.column("device", "dc_L"))
        override = {(THETA_LN_IDU, m): math.log(current[m] * length[m] / w) for m, w in requested if m in writers}
        column_items = tuple((key, override.get(key, v)) for key, v in column_items)
    columns_extras = (column_items, ctx.fixed_values, ctx.resistor_values, ctx.lut)
    later = [(dc_columns, columns_extras + ((ctx.inputs.linear_devices,) if ctx.inputs.linear_devices else ())),
             (dc_widths, (ctx.lut, requested) if requested else (ctx.lut,))]
    for block, extras in later:
        snapshot = block(snapshot, *extras)
    steps = tuple(steps + later)
    resistances = ctx.resistor_values + tuple((key, v) for (kind, key), v in items if kind == THETA_RESISTANCE)
    if parent is not None and dict(snapshot.column("device", "dc_op")) == dict(parent.snapshot.column("device", "dc_op")):
        gm_id_prev = inherited_gm_id(parent, snapshot, ctx.lut)   # DC 동작점이 parent 와 같다(수동소자 θ 만 바뀐 FD 등) -- parent 와 같은 tol_I 입력(DEC-92 재사용)
    else:
        gm_id_prev = previous_gm_id(parent)
    return seal_dc(snapshot, steps, ctx.lut, resistances, ctx.inputs.linear_devices, gm_id_prev, raise_on_violation)
