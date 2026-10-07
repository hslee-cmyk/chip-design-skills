"""봉인 스냅샷 하나 -> 소신호 선형화 + spec 제약 metric + 전력·면적 (계획 N3.5 커널 '봉인 -> ss_linearize -> mna -> metric',
설계 design_mod1_lut_mod5_mna 3.2·3.5 커널 순서, 7a design 4.5 단계 5 배선 지점, metrics CONTRACT 7절).

진입점: `ss_evaluate(sealed, ctx, theta, constraints, counted_rails=(), passive_theta=()) -> SsEvaluation`.

* `sealed` = sizing `SealedSnapshot`(DEC-67 -- 타입으로 강제, 봉인 안 된 스냅샷의 ss 는 계산하지 않는다), `ctx` = 그 스냅샷을
  만든 `KernelContext`, `theta` = 그 θ(`Theta` 또는 매핑 -- `check_theta` 로 다시 정규화, θ 저항 값을 읽는다),
  `constraints` = spec `ConstraintDecl` tuple(metric 결정 대기 = metric None 은 건너뛴다 -- 그 표지는 spec `pending` 에 있다),
  `counted_rails` = DEC-78 합산 레일 넷(선언이 생길 때까지 부르는 쪽이 넘긴다), `passive_theta` = ((수동소자, 값), ...) --
  값 선언이 없는(engine) 보상 수동소자의 θ 값(DEC-92, GB5 가 θ 스키마에 등록하면 그 값이 여기로 온다).
* 수동소자 값 = spec 선언(`ctx.inputs.element_values`, 수동소자만) ∪ θ 저항 ∪ `passive_theta`. 같은 소자에 둘 이상이면
  ValueError(값의 정본은 하나), `passive_theta` 이름이 S1 수동소자가 아니면 ValueError.
* 요청 = 제약의 (metric, view) 중복 제거(문서 순서). view_kind 가 있는 metric -> `metrics_ss`, 없는 metric(전력·면적)은
  `metrics_dc` 묶음이 늘 낸다(목적 축). 미등록 metric 은 `KeyError`(spec 로드가 `metric_unknown` 으로 먼저 거른다).
* 블록 순서: `ss_dev(lut)` -> `metrics_ss(requests, passive_values)` -> `metrics_dc(passive_values, counted_rails)`. 입력 버전이
  같으면 재사용, FD 로 θ 한 성분이 바뀌면 dc_op 를 읽는 블록만 다시(바뀌지 않은 소자의 LUT 조회는 memo 적중).
* 재사용은 필드가 든 lineage 에서만 일어난다(core 6.2): 결과 `lineage`(ss 필드를 담은 `DcEvaluation`)를 다음 `size_and_seal` 의
  parent 로, 같은 θ 를 다시 볼 때는 `ss_evaluate(lineage.sealed, ...)` 로 넘긴다. 그 lineage 에서 `size_and_seal` 이 낸 스냅샷에는
  앞 점의 ss 필드가 입력 버전과 함께 남아 있다 -- `ss_evaluate` 를 거치기 전에는 읽지 않는다(값의 정본은 이 함수의 결과).
"""
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.sizing import (METRICS_KEY, THETA_RESISTANCE, DcEvaluation, KernelContext, SealedSnapshot, Theta,
                                check_theta)

from .dc_metrics import metrics_dc
from .registry import metric_registry
from .ss_linearize import ss_dev
from .ss_metrics import metrics_ss
from .ss_types import MetricRequest, SsEvaluation


def _passive_values(snapshot, ctx, theta, passive_theta):
    classes = dict(snapshot.column("device", "element_class"))
    passives = {n for n, c in classes.items() if c == ELEMENT_PASSIVE}
    values = {n: v for n, v in ctx.inputs.element_values if n in passives and v is not None}
    sources = [tuple((key, v) for (kind, key), v in theta.values if kind == THETA_RESISTANCE), tuple(passive_theta)]
    for pairs in sources:
        for name, value in pairs:
            if name not in passives:
                raise ValueError("ss_evaluate: %r 은 S1 수동소자가 아니다" % (name,))
            if name in values:
                raise ValueError("ss_evaluate: 수동소자 %r 의 값이 두 곳에서 온다(spec·θ 중 하나만)" % (name,))
            values[name] = float(value)
    return tuple(sorted(values.items()))


def _requests(constraints):
    seen = []
    for c in constraints:
        if c.metric is not None:
            request = MetricRequest(c.metric, c.view)
            if request not in seen:
                seen.append(request)
    return tuple(seen)


def ss_evaluate(sealed, ctx, theta, constraints, counted_rails=(), passive_theta=()):
    if not isinstance(sealed, SealedSnapshot):
        raise TypeError("ss_evaluate: 봉인 스냅샷(SealedSnapshot)만 받는다(DEC-67)")
    if not isinstance(ctx, KernelContext):
        raise TypeError("ss_evaluate: ctx 는 build_kernel_context 결과여야 한다")
    theta = check_theta(ctx.schema, theta.values if isinstance(theta, Theta) else theta)
    snapshot = sealed.snapshot
    values = _passive_values(snapshot, ctx, theta, passive_theta)
    requests = _requests(tuple(constraints))
    registry = metric_registry()
    ss_requests = tuple(r for r in requests if registry[r.metric].signature.view_kind is not None)
    snapshot = ss_dev(snapshot, ctx.lut)
    snapshot = metrics_ss(snapshot, ss_requests, values)
    snapshot = metrics_dc(snapshot, values, tuple(counted_rails))
    lineage = DcEvaluation(snapshot, sealed.report, SealedSnapshot(snapshot, sealed.report))
    return SsEvaluation(snapshot, snapshot.value("graph", METRICS_KEY, "metrics_ss"),
                        snapshot.value("graph", METRICS_KEY, "metrics_dc"), lineage)
