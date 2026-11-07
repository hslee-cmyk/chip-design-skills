"""평가 커널 본체 -- θ -> ②③④⑤ 계산 블록 -> 봉인 (설계 3.2·5절, 계획 N3.5 평가 커널).

진입점: `run_kernel(ctx, theta, wf, parent, w_request, raise_on_violation, realized=None, layout=None) -> DcEvaluation`.
`size_and_seal`(후보 위반이면 예외)과 `size_and_seal_local`(위반 보고서를 항목별로 읽는다)이 같은 계산을 쓴다. 규칙·순서·캐시는 `size_and_seal.py`
머리 설명과 같다. 함께 있는 도우미: `normalize_w_request`(W_request 검증·정렬). 봉인 3 tol_I 의 gm 은 `dc_tolerances` 가 쓰는 자기 동작점
`dc_gm` 이라 parent 에서 넘기는 입력이 없다(설계 40 §3.7-3) -- `parent` 는 같은 lineage 재사용(필드가 곧 캐시)에만 쓴다.
θ 스키마·고정 노드·DC 저항 선언값·L 묶음은 커널 컨텍스트 `base` 의 S0 수준 필드 `graph/kernel` 에서 읽고, parent 가 같은 컨텍스트에서 나왔는지는 base writer
(`ctx.base.block_versions` 키 전부)의 `block_version` 이 `base` 와 같은지로 본다. parent 스냅샷은 `derive_child(base writer ∪ 커널 블록 ∪ 봉인 항목 블록 일곱)` 로 파생한다
(계획 v6.31 N3.3, 설계 41 4.7-3c, 설계 40 §2.4.7 `KernelContext` 행 -- 사본 없음). keep 은 봉인 4 호출 목록과 같은 집합이고 base writer 밖 writer 의 낡은 필드는 뺀다.
모든 블록 호출은 `ctx.donors`·`ctx.counters` 로 부른다(같은 입력은 계보와 무관하게 이식·재연). 블록 단계마다 후보 실패 클래스를 이름으로 잡아 그 블록에 들어간 스냅샷을
부분 스냅샷(`exc.partial`)으로 붙인 뒤 다시 낸다(`core.attach_partial`, 설계 40 §2.4.7 -- 재연한 예외도 같다).
"""
import math

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, attach_partial
from gmid_engine.graph import ELEMENT_MOS

from .block_currents import dc_currents
from .block_dc import dc_solve
from .block_lengths import dc_lengths
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
    RealizedGeometry,
    RealizeInput,
    Theta,
    WfInput,
)
from .seal import SEAL_ITEM_BLOCKS, seal_dc
from .seal_versions import writers_in_scope
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


def _call_block(ctx, block, snapshot, extras, before):
    """블록 하나를 `ctx` 의 색인·계수로 부른다. 후보 실패면 그 블록에 들어간 `snapshot` 을 base writer ∪ `before`(앞 블록) 로 줄여 부분 스냅샷으로 붙여 다시 낸다
    (parent 의 낡은 필드를 지워 지문이 (평가 키, 실패 지점)만으로 정해진다 -- 계획 N3.3 실패 평가의 부분 스냅샷)."""
    positional, named = block.split(extras)          # 필수 키워드 인자(dc_solve 의 `wf`)는 extras 맨 뒤 -> 키워드로 부른다
    try:
        return block(snapshot, *positional, donors=ctx.donors, counters=ctx.counters, **named)
    except CANDIDATE_FAILURE_CLASSES as exc:
        attach_partial(exc, snapshot.derive_child(writers_in_scope(ctx.base, before)))
        raise


def run_kernel(ctx, theta, wf, parent, w_request, raise_on_violation, realized=None, layout=None):
    """평가 커널 본체 -- `size_and_seal`(위반이면 예외)과 `size_and_seal_local`(위반 보고서를 그대로 읽는다)이 같은 계산을 쓴다.
    `wf` = `WfInput`(평가 입력 w_f 칸 -- 필수 인자, 기본값 없음; `dc_solve` 의 필수 키워드로 간다).
    `realized` = `RealizeInput`(실현 평가: DC 블록이 칸마다 `realize_fingers` 로 m 을 정하고 W' 고정으로 다시 푼다) 또는 None. W_request 와 함께 줄 수 없다(`ValueError`).
    `layout` = `RealizedGeometry`(레이아웃 뒤 평가: 실현 평가와 같은 W'·바이어스 고정 KCL 재풀이이고 W' 만 레이아웃 기하에서 온다) 또는 None. 기준 스냅샷을 나르는
    `realized` 와 함께만 주고 W_request 와는 함께 줄 수 없다(`ValueError`)."""
    if not isinstance(ctx, KernelContext):
        raise TypeError("size_and_seal: ctx 는 build_kernel_context 결과여야 한다")
    if not isinstance(wf, WfInput):
        raise TypeError("size_and_seal: wf 는 WfInput 이어야 한다")
    if realized is not None and (not isinstance(realized, RealizeInput) or w_request):
        raise ValueError("size_and_seal: realized 는 RealizeInput 이어야 하고 w_request 와 함께 줄 수 없다")
    if layout is not None and (not isinstance(layout, RealizedGeometry) or realized is None or w_request):
        raise ValueError("size_and_seal: layout 은 RealizedGeometry 여야 하고 기준 스냅샷 realized 가 필요하며 w_request 와 함께 줄 수 없다")
    base = ctx.base
    snapshot = base
    theta = check_theta(base.value("graph", KERNEL_KEY, "theta_schema"), theta.values if isinstance(theta, Theta) else theta)
    base_writers = tuple(base.block_versions)
    if parent is not None and (not isinstance(parent, DcEvaluation)
                               or any(parent.snapshot.block_version(w) != base.block_version(w) for w in base_writers)):
        raise ValueError("size_and_seal: parent 는 같은 커널 컨텍스트에서 나온 DcEvaluation 이어야 한다")
    items = theta.values
    currents = tuple((key, v) for (kind, key), v in items if kind == THETA_CURRENT)
    lengths = tuple((key, v) for (kind, key), v in items if kind == THETA_L)
    owner_length = dict(lengths)
    lengths += tuple((member, owner_length[owner]) for member, owner in base.value("graph", KERNEL_KEY, "l_ties"))     # L 동치류: 멤버 L = 주인 θ L (LR1)
    column_items = tuple(((kind, key), v) for (kind, key), v in items if kind in _COLUMN_KINDS)
    requested = normalize_w_request(ctx, w_request)
    steps = [(dc_currents, (currents,)), (dc_lengths, (lengths,))]
    later_blocks = (dc_solve,)      # steps 뒤에 부르는 블록의 구성원 정의(extras 는 아래에서 붙인다)
    if parent is not None:      # 스냅샷 파생: keep = base writer ∪ 커널 블록(steps·later_blocks) ∪ 봉인 항목 블록 여덟(seal.py 상수) -- 봉인 4 의 호출 목록과 같은 집합(계획 N3.3, 설계 41 4.7-3c)
        snapshot = parent.snapshot.derive_child(writers_in_scope(base, later_blocks + tuple(b for b, _ in steps) + SEAL_ITEM_BLOCKS))
    done = []       # 이 평가에서 이미 부른 블록 -- 실패 부분 스냅샷의 범위(`writers_in_scope`)
    for block, extras in steps:
        snapshot = _call_block(ctx, block, snapshot, extras, done)
        done.append(block)
    if requested:
        # LY3: 쓰기 소자의 좌표를 요청 W 에서 정한다 -- ln IDu = ln(ID·L/W). 종속 소자는 좌표가 노드 VGS 순방향이라 건드리지 않는다
        writers = {m for m, coord in base.column("device", "dc_coord") if coord.role == COORD_WRITER}
        current, length = dict(snapshot.column("device", "dc_current")), dict(snapshot.column("device", "dc_L"))
        override = {(THETA_LN_IDU, m): math.log(current[m] * length[m] / w) for m, w in requested if m in writers}
        column_items = tuple((key, override.get(key, v)) for key, v in column_items)
    resistor_values = base.value("graph", KERNEL_KEY, "resistor_values")
    columns_extras = (column_items, base.value("graph", KERNEL_KEY, "fixed_values"), resistor_values, ctx.lut)
    if requested:
        columns_extras += (RealizedGeometry(None, requested),)
    elif layout is not None:
        columns_extras += (layout, realized)
    elif realized is not None:
        columns_extras += (None, realized)
    columns_extras += (wf,)         # 필수 키워드 `wf` 는 extras 맨 뒤(`dc_solve.split` 이 키워드로 가른다) -- 봉인 4 도 같은 extras 로 입력 버전을 다시 잰다
    later = list(zip(later_blocks, (columns_extras,)))
    for block, extras in later:
        snapshot = _call_block(ctx, block, snapshot, extras, done)
        done.append(block)
    steps = tuple(steps + later)
    resistances = resistor_values + tuple((key, v) for (kind, key), v in items if kind == THETA_RESISTANCE)
    return seal_dc(snapshot, steps, ctx.lut, resistances, raise_on_violation,
                   base=base, donors=ctx.donors, counters=ctx.counters)
