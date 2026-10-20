"""평가 커널 본체 -- θ -> ②③④⑤ 계산 블록 -> 봉인 (설계 3.2·5절, 계획 N3.5 평가 커널).

진입점: `run_kernel(ctx, theta, parent, w_request, raise_on_violation) -> DcEvaluation`.
`size_and_seal`(후보 위반이면 예외)과 `size_and_seal_local`(위반 보고서를 항목별로 읽는다)이 같은 계산을 쓴다. 규칙·순서·캐시는 `size_and_seal.py`
머리 설명과 같다. 함께 있는 도우미: `normalize_w_request`(W_request 검증·정렬). 봉인 3 tol_I 의 gm 은 `dc_tolerances` 가 쓰는 자기 동작점
`dc_gm` 이라 parent 에서 넘기는 입력이 없다(설계 40 §3.7-3) -- `parent` 는 같은 lineage 재사용(필드가 곧 캐시)에만 쓴다.
θ 스키마·고정 노드·DC 저항 선언값·L 묶음은 커널 컨텍스트 `base` 의 S0 수준 필드 `graph/kernel` 에서 읽고, parent 가 같은 컨텍스트에서 나왔는지는 계획 블록
(`PLAN_WRITERS`)의 `block_version` 이 `base` 와 같은지로 본다(설계 40 §2.4.7 `KernelContext` 행 -- 사본 없음).
모든 블록 호출은 `ctx.donors`·`ctx.counters` 로 부른다(같은 입력은 계보와 무관하게 이식·재연). 블록 단계마다 후보 실패 클래스를 이름으로 잡아 그 블록에 들어간 스냅샷을
부분 스냅샷(`exc.partial`)으로 붙인 뒤 다시 낸다(`core.attach_partial`, 설계 40 §2.4.7 -- 재연한 예외도 같다).
"""
import math

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, attach_partial
from gmid_engine.graph import ELEMENT_MOS

from .block_columns import dc_columns
from .block_currents import dc_currents
from .block_lengths import dc_lengths
from .block_widths import dc_widths
from .kernel_context import PLAN_WRITERS
from .s2_values import (
    COORD_WRITER,
    KERNEL_KEY,
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
from .theta_check import check_theta

_COLUMN_KINDS = (THETA_LN_IDU, THETA_RESISTANCE, THETA_Y)


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


def _call_block(ctx, block, snapshot, extras):
    """블록 하나를 `ctx` 의 색인·계수로 부른다. 후보 실패면 그 블록에 들어간 `snapshot` 을 부분 스냅샷으로 붙여 다시 낸다."""
    try:
        return block(snapshot, *extras, donors=ctx.donors, counters=ctx.counters)
    except CANDIDATE_FAILURE_CLASSES as exc:
        attach_partial(exc, snapshot)
        raise


def run_kernel(ctx, theta, parent, w_request, raise_on_violation):
    """평가 커널 본체 -- `size_and_seal`(위반이면 예외)과 `size_and_seal_local`(위반 보고서를 그대로 읽는다)이 같은 계산을 쓴다."""
    if not isinstance(ctx, KernelContext):
        raise TypeError("size_and_seal: ctx 는 build_kernel_context 결과여야 한다")
    base = ctx.base
    theta = check_theta(base.value("graph", KERNEL_KEY, "theta_schema"), theta.values if isinstance(theta, Theta) else theta)
    snapshot = base
    if parent is not None:
        if not isinstance(parent, DcEvaluation) or any(parent.snapshot.block_version(w) != base.block_version(w) for w in PLAN_WRITERS):
            raise ValueError("size_and_seal: parent 는 같은 커널 컨텍스트에서 나온 DcEvaluation 이어야 한다")
        snapshot = parent.snapshot
    items = theta.values
    currents = tuple((key, v) for (kind, key), v in items if kind == THETA_CURRENT)
    lengths = tuple((key, v) for (kind, key), v in items if kind == THETA_L)
    owner_length = dict(lengths)
    lengths += tuple((member, owner_length[owner]) for member, owner in base.value("graph", KERNEL_KEY, "l_ties"))     # L 동치류: 멤버 L = 주인 θ L (LR1)
    column_items = tuple(((kind, key), v) for (kind, key), v in items if kind in _COLUMN_KINDS)
    requested = normalize_w_request(ctx, w_request)
    steps = [(dc_currents, (currents,)), (dc_lengths, (lengths,))]
    for block, extras in steps:
        snapshot = _call_block(ctx, block, snapshot, extras)
    if requested:
        # LY3: 쓰기 소자의 좌표를 요청 W 에서 정한다 -- ln IDu = ln(ID·L/W). 종속 소자는 좌표가 노드 VGS 순방향이라 건드리지 않는다
        writers = {m for m, coord in base.column("device", "dc_coord") if coord.role == COORD_WRITER}
        current, length = dict(snapshot.column("device", "dc_current")), dict(snapshot.column("device", "dc_L"))
        override = {(THETA_LN_IDU, m): math.log(current[m] * length[m] / w) for m, w in requested if m in writers}
        column_items = tuple((key, override.get(key, v)) for key, v in column_items)
    resistor_values = base.value("graph", KERNEL_KEY, "resistor_values")
    columns_extras = (column_items, base.value("graph", KERNEL_KEY, "fixed_values"), resistor_values, ctx.lut)
    later = [(dc_columns, columns_extras + ((ctx.inputs.linear_devices,) if ctx.inputs.linear_devices else ())),
             (dc_widths, (ctx.lut, requested) if requested else (ctx.lut,))]
    for block, extras in later:
        snapshot = _call_block(ctx, block, snapshot, extras)
    steps = tuple(steps + later)
    resistances = resistor_values + tuple((key, v) for (kind, key), v in items if kind == THETA_RESISTANCE)
    return seal_dc(snapshot, steps, ctx.lut, resistances, ctx.inputs.linear_devices, raise_on_violation,
                   donors=ctx.donors, counters=ctx.counters)
