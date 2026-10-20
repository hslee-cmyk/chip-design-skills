"""봉인 스냅샷 하나 -> 소신호 선형화 + spec 제약 metric + 전력·면적 (계획 N3.5 커널 '봉인 -> ss_linearize -> mna -> metric',
설계 design_mod1_lut_mod5_mna 3.2·3.5 커널 순서, 7a design 4.5 단계 5 배선 지점, metrics CONTRACT 7절, 계획 DEC-92).

진입점: `ss_evaluate(sealed, ctx, theta, constraints, counted_rails=(), *, junction, area_decl=None, noise_decl=None, mismatch=None, structure=None, driving=None, diffusion=()) -> SsEvaluation`
(`area_decl` = 선택 `PassiveAreaDecl` -- 면적 항의 수동소자 단위 면적·측정 부하 제외, 사용자 결정 11. [U8] `noise_decl` = 선택 `NoiseDecl` -- spec feedback·샘플링
커패시터·S1v 입력 셀(`search.noise_decl`). 잡음 metric 요청이 있을 때만 쓰이고, 그때 `noise_devices`(소자별 LUT 잡음 값·f_lo·kT)를 만들어 `metrics_ss` 의 세 번째 extras 로 넘긴다.
생략하면 `NoiseDecl()`(되먹임 미제공 -> 출력 적분 정의 불가, 입력 셀 미제공 -> excess 정의 불가)).

* [U7] `driving` = 선택 spec `DrivingDecl`(선언되면 슬루·방향별 전류 `ls_fields` 보고), `mismatch` = 선택 `MismatchSource`(`MismatchSource.from_decl(pdk_decl)` -- offset·미러비의 PDK bin slope 입력, 없으면 그 metric 은 정의 불가
  `mismatch_source_missing`), `structure` = 선택 `MetricStructure`(S0 수준 필드 `graph/s1v: metric_structure` -- offset_excess 입력 셀·FF 비·블록 잔차의 구조 사실. 없으면 그 값들은 정의 불가).
  제약 metric 중 레지스트리 결과 형식이 `AUX_TYPES` 인 것(offset·미러비·스윙·ICMR·FF 비)은 `metrics_ss` 가 아니라 계산 블록 `metrics_aux` 가 계산하고, 두 묶음의
  entries·reports 를 합쳐 `SsEvaluation.ss` 로 낸다(`metrics_aux` 가 돌지 않으면 묶음 그대로). `structure` 가 있으면 전달 뷰 제약마다 블록 잔차 보고(`reports` 의
  `block_residual`·`nqs_ratio`)를 항상 낸다. 판정 제약에 `ugf_ss_hz` 가 있으면 그 값이 `nqs_ratio` 분자다.

* [U14] `diffusion` = ((MOS, `DiffusionGeometry`), ...) -- 레이아웃 뒤 실현 확산 기하(MOD7 `ly.diffusion`, MOD8 재검증). 있는 소자의 접합 용량 cdb·csb 는 그 기하로 계산하고
  (`junction_model` = `JUNCTION_LAYOUT_DIFFUSION`) 없는 소자는 레이아웃 전 LUT 생성 규칙 기하다. 비면 `ss_dev` 입력이 그대로라 기존 점의 필드를 재사용한다.
* `junction` = metrics `JunctionSource`(DEC-91 접합 용량 입력 -- PDK 선언·LUT 생성 규칙 선언·LUT 측정 온도, 부르는 쪽이
  `JunctionSource.from_decls(read_pdk_decl(...), read_pdk_decl(...), ctx.lut.memo.lut)` 로 S0 당 1회 만든다). 필수 키워드 인자:
  `KernelContext` 에 PDK 선언이 없어서 새 입력으로 명시했다(metrics CONTRACT 7.6). 아니면 TypeError.

* `sealed` = sizing `SealedSnapshot`(DEC-67 -- 타입으로 강제, 봉인 안 된 스냅샷의 ss 는 계산하지 않는다), `ctx` = 그 스냅샷을
  만든 `KernelContext`, `theta` = 그 θ(`Theta` 또는 매핑 -- `check_theta` 로 다시 정규화, θ 수동소자 값을 읽는다),
  `constraints` = spec `ConstraintDecl` tuple(metric 결정 대기 = metric None 은 건너뛴다 -- 그 표지는 spec `pending` 에 있다),
  `counted_rails` = DEC-78 합산 레일 넷(선언이 생길 때까지 부르는 쪽이 넘긴다).
* 수동소자 값(DEC-92 -- 값의 정본은 하나): GB5 계산 블록 `passive_values`(spec 선언 ∪ θ 수동소자 ∪ 영점 상쇄 R = 1/Σ`dc_gm`)가 쓴
  `device.passive_value` 필드(설계 40 §2.4.8). 하류 블록은 이 필드를 읽는다(사본을 extras 로 넘기지 않는다). 어느 출처에도 없는 수동소자
  (결정 대기 등)는 `metrics_ss` 가 `passive_value_undeclared` 로 보고한다.
* 요청 = 제약의 (metric, view) 중복 제거(문서 순서). view_kind 가 있는 metric -> `metrics_ss`, 없는 metric(전력·면적)은
  `metrics_dc` 묶음이 늘 낸다(목적 축). 미등록 metric 은 `KeyError`(spec 로드가 `metric_unknown` 으로 먼저 거른다).
* 블록 순서: `passive_values(element_values, zero_cancel, theta_passive_pairs(θ))` -> `ss_dev(lut)` -> `metrics_ss(requests)` -> `metrics_dc(counted_rails)`.
  입력 버전이 같으면 재사용, FD 로 θ 한 성분이 바뀌면 그 성분을 읽는 블록만 다시: DC 성분이면 dc_op·dc_gm 을 읽는 블록(바뀌지 않은 소자의
  LUT 조회는 memo 적중), θ 수동소자 성분이면 `ss_dev` 재사용·`passive_values`·`metrics_ss`·`metrics_dc` 만.
* 블록 호출은 모두 `ctx.donors`·`ctx.counters`(`KernelContext` 의 실행 하나 색인·계수)로 부른다. 후보 실패 클래스(이름으로 잡는다)가 나면 그 블록에 들어간 스냅샷을
  부분 스냅샷(`exc.partial`)으로 붙여 다시 낸다(`core.attach_partial`, 설계 40 §2.4.7).
* 재사용은 필드가 든 lineage 에서만 일어난다(core 6.2): 결과 `lineage`(ss 필드를 담은 `DcEvaluation`)를 다음 `size_and_seal` 의
  parent 로, 같은 θ 를 다시 볼 때는 `ss_evaluate(lineage.sealed, ...)` 로 넘긴다. 그 lineage 에서 `size_and_seal` 이 낸 스냅샷에는
  앞 점의 ss 필드가 입력 버전과 함께 남아 있다 -- `ss_evaluate` 를 거치기 전에는 읽지 않는다(값의 정본은 이 함수의 결과).
"""
from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, attach_partial
from gmid_engine.sizing import KERNEL_KEY, METRICS_KEY, DcEvaluation, KernelContext, SealedSnapshot, Theta, check_theta

from .dc_metrics import metrics_dc
from .junction_source import JunctionSource
from .metrics_aux import AUX_TYPES, metrics_aux
from .noise_devices import noise_devices
from .noise_types import NoiseAnalysis, NoiseDecl
from .passive_values import passive_values, theta_passive_pairs
from .registry import metric_registry
from .ss_linearize import ss_dev
from .ss_metrics import metrics_ss
from .ss_types import MetricBundle, MetricRequest, SsEvaluation

def _requests(constraints):
    seen = []
    for c in constraints:
        if c.metric is not None:
            request = MetricRequest(c.metric, c.view)
            if request not in seen:
                seen.append(request)
    return tuple(seen)


TRANSFER_VIEW_KIND = "transfer"                       # 블록 잔차 보고가 짝을 찾는 뷰 종류(core VIEW_KINDS)
UGF_METRIC = "ugf_ss_hz"                              # nqs_ratio 분자


def _transfer_views(requests, registry):
    """판정 제약의 전달 뷰 선언(중복 제거, 요청 순서) -- 소신호 전달 뷰(mode port·transfer·β=1 loop)만."""
    seen = []
    for r in requests:
        if registry[r.metric].signature.view_kind == TRANSFER_VIEW_KIND and r.view not in seen:
            seen.append(r.view)
    return tuple(seen)


def _merged(ss_bundle, aux_bundle):
    return MetricBundle(ss_bundle.entries + aux_bundle.entries, ss_bundle.approximations, ss_bundle.detail,
                        ss_bundle.reports + aux_bundle.reports, ss_bundle.warnings + aux_bundle.warnings)


def ss_evaluate(sealed, ctx, theta, constraints, counted_rails=(), *, junction, area_decl=None, noise_decl=None, mismatch=None, structure=None, driving=None,
                diffusion=()):
    if not isinstance(sealed, SealedSnapshot):
        raise TypeError("ss_evaluate: 봉인 스냅샷(SealedSnapshot)만 받는다(DEC-67)")
    if not isinstance(ctx, KernelContext):
        raise TypeError("ss_evaluate: ctx 는 build_kernel_context 결과여야 한다")
    if not isinstance(junction, JunctionSource):
        raise TypeError("ss_evaluate: junction 은 JunctionSource 여야 한다(DEC-91 접합 용량 입력)")
    if noise_decl is not None and not isinstance(noise_decl, NoiseDecl):
        raise TypeError("ss_evaluate: noise_decl 은 NoiseDecl 이어야 한다")
    schema = ctx.base.value("graph", KERNEL_KEY, "theta_schema")
    theta = check_theta(schema, theta.values if isinstance(theta, Theta) else theta)
    requests = _requests(tuple(constraints))
    registry = metric_registry()
    aux_requests = tuple(r for r in requests if registry[r.metric].source_type in AUX_TYPES)
    ss_requests = tuple(r for r in requests if registry[r.metric].signature.view_kind is not None and r not in aux_requests)
    keys = {"donors": ctx.donors, "counters": ctx.counters}      # 실행 하나의 블록 결과 색인·계수 -- 모든 블록 호출에 같은 객체
    snapshot = sealed.snapshot
    try:
        snapshot = passive_values(snapshot, ctx.inputs.element_values, schema.zero_cancel, theta_passive_pairs(theta.values), **keys)
        snapshot = ss_dev(snapshot, ctx.lut, junction, *((diffusion,) if diffusion else ()), **keys)
        noisy = any(registry[r.metric].source_type is NoiseAnalysis for r in ss_requests)
        extra = (noise_devices(snapshot, ctx.lut, junction, NoiseDecl() if noise_decl is None else noise_decl),) if noisy else ()
        snapshot = metrics_ss(snapshot, ss_requests, *extra, **keys)
        bundle = snapshot.value("graph", METRICS_KEY, "metrics_ss")
        views = () if structure is None else _transfer_views(requests, registry)
        if aux_requests or views:
            ugf = next((res.value for req, res in bundle.entries if req.metric == UGF_METRIC and res.value is not None), None)
            snapshot = metrics_aux(snapshot, aux_requests, ctx.lut, mismatch, structure, ctx.inputs.node_targets, ctx.inputs.input_dc_v,
                                   ctx.inputs.linear_devices, views, ugf, driving, **keys)
            bundle = _merged(bundle, snapshot.value("graph", METRICS_KEY, "metrics_aux"))
        snapshot = metrics_dc(snapshot, tuple(counted_rails), *(() if area_decl is None else (area_decl,)), **keys)
    except CANDIDATE_FAILURE_CLASSES as exc:
        attach_partial(exc, snapshot)        # ss 단계 부분 스냅샷 = 실패 직전까지 쓴 스냅샷(그 블록에 들어간 것, 적어도 봉인 스냅샷) -- 설계 40 §2.4.7
        raise
    lineage = DcEvaluation(snapshot, sealed.report, SealedSnapshot(snapshot, sealed.report))
    return SsEvaluation(snapshot, bundle, snapshot.value("graph", METRICS_KEY, "metrics_dc"), lineage)
