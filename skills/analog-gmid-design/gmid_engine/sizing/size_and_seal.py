"""GB7 공개 API -- 후보 θ 하나를 DC 정본(노드전압·가지전류·소자 op)으로 풀고 봉인한다 (설계 3.2·5절 `size_and_seal`,
계획 N3.5 평가 커널 ②③④⑤ -> 봉인, 요구 3.2).

진입점: `size_and_seal(ctx, theta, parent=None) -> DcEvaluation`.

* `ctx` = `build_kernel_context` 결과(S0 당 1회). `theta` = `check_theta` 가 받는 {(kind, key): 값} 또는 `Theta`.
* `parent` = 같은 ctx 에서 나온 이전 `DcEvaluation`(FD 스텝의 기준점·SLSQP 직전 반복 등) 또는 None(ctx.base 에서 시작).
  블록은 입력 버전이 같으면 계산하지 않고 parent 스냅샷의 필드를 그대로 쓴다(필드가 곧 캐시, 구조 공유).
  계획 블록 버전이 ctx 와 다른 parent 는 `ValueError`(다른 S0 의 스냅샷을 섞지 않는다).
* 블록 순서와 추가 인자(블록이 실제로 읽는 θ 성분만 -- 한 성분을 움직이면 그 성분을 읽는 블록과 하류만 다시 계산):
  `dc_currents`(θ current) -> `dc_lengths`(θ L) -> `dc_columns`(θ ln_idu·y·resistance, 고정 노드값, 선언 저항, LUT) ->
  `dc_widths`(LUT) -> `seal_dc`.
* 실패: 후보 실패 = `SealViolationError`·`NonconvergentError`(core `CANDIDATE_FAILURE_CLASSES`) -- 탐색 층이 이름으로 잡아 S3
  실패 레코드로 남긴다. 그 밖(ValueError·TypeError = 호출 계약 위반)은 잡지 않는다.
"""
from .block_columns import dc_columns
from .block_currents import dc_currents
from .block_lengths import dc_lengths
from .block_widths import dc_widths
from .s2_values import (
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


def size_and_seal(ctx, theta, parent=None):
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
    column_items = tuple(((kind, key), v) for (kind, key), v in items if kind in _COLUMN_KINDS)
    steps = (
        (dc_currents, (currents,)),
        (dc_lengths, (lengths,)),
        (dc_columns, (column_items, ctx.fixed_values, ctx.resistor_values, ctx.lut)),
        (dc_widths, (ctx.lut,)),
    )
    for block, extras in steps:
        snapshot = block(snapshot, *extras)
    resistances = ctx.resistor_values + tuple((key, v) for (kind, key), v in items if kind == THETA_RESISTANCE)
    return seal_dc(snapshot, steps, ctx.lut, resistances, ctx.inputs.linear_devices)
