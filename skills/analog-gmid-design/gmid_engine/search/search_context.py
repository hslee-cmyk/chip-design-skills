"""탐색 컨텍스트 -- S0 수준 스냅샷 참조 + 실행 수명 평가 캐시·계수 (설계 2.1·7.2·7.4, WP-23 (3); 40 §2.4.7 'SearchContext 칸 배정', v1.9.1 D6).

진입점: `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp, s0=None) -> SearchContext`
(`pdk_decl` = core `read_pdk_decl` 결과 -- W 하한·b_A 의 `min_finger_w_m`·`manufacturing_grid_m`, `lut_rule_decl` = LUT 생성 규칙 선언(sky130 = assets/sky130_lut_rule_decl.json)).

* **S0 수준 블록**(설계 40 §2.4.1·§2.4.8): 커널 컨텍스트 `dc_ctx.base`(S1·S1v·쓰기 계획·커널 구조 파생, 단계 B 를 거쳤으면 GB4 필드)의 권한표를 S0 수준 권한표(`S0_WRITERS`)로
  넓히고 다음 계산 블록을 차례로 부른다 -- 입력 버전이 같으면 재사용(같은 S0 의 다음 실행은 디스크 스냅샷 위에서 계산 0):
  `search_domain`(θ 상자·L 칸·b_A -- 실행 설정의 수동소자 상자만 extras), `junction_field`(접합 출처), `mismatch_field`(mismatch 출처), `model_error_field`(모델 오차 쌍),
  `constraint_classes`(제약 분류), `passive_area_decl`(면적 선언), `metric_structure`(S1v 가 없으면 None), `noise_decl`(잡음 선언),
  `start_intervals`(S1v 뷰 필드가 있을 때만 -- 41 §6 출발 구간, 없으면 `graph/start` 필드가 없고 층 0 은 상자 중심으로 간다).
* **저장**(v1.9.1 D6): 위 블록이 모두 끝난 S0 수준 스냅샷을 `s0`(core `S0Slot`, 단계 A 가 만든 S0 키 -- `StageAResult.s0`)로 여기서 한 번 쓴다(단계 B 층 writer 는
  `transient` -- 직렬화하지 않는다). `s0` 가 None 이면(단계 A 를 거치지 않은 호출) 쓰지 않는다. 키가 이미 있고 검증되면 쓰지 않는다.
* `SearchContext` 칸 = **참조**(`dc` = S0 수준 스냅샷 뿌리를 `base` 로 담은 커널 컨텍스트 + LUT memo, `spec`, `settings`, S3 기록기 `archive`, 지문 `context_fp`·`code_fp`) +
  실행 수명 상태(평가 캐시·계수·예산·`cell_floors` -- S3 색인·실행 계수 이동은 U17 ②, LUT memo 함수 이동은 ③). 설계 값은 칸으로 들고 있지 않고 같은 이름의 읽기 속성이
  부를 때마다 S0 수준 필드를 읽는다(사본 없음): `domain`(`graph/kernel: search_domain`), `junction`·`mismatch`·`model_error`·`area_decl`(graph/kernel), `structure`·`noise_decl`
  (graph/s1v), `judged_constraints`·`ss_constraints`·`constraint_notes`(`constraint_classes` -- ss 는 spec 위치에서 spec 선언을 읽는다), `rungs`(`graph/start: rungs` 또는 None),
  `schema_fp`(θ 스키마 필드의 값 지문), `element_values`·`driving`(spec 파싱 결과 참조).
* 지문: `context_fp` = (S1 블록·커널 계획 블록(`PLAN_WRITERS`)의 입력 버전, LUT 손잡이, DcInputs) 지문 -- 평가 커널이 읽는 S0 입력만이다(정의역 상자·출발 구간·접합 선언
  경로 같은 탐색 쪽 S0 필드는 평가 결과를 바꾸지 않아 넣지 않는다: θ 상자만 바뀐 실행도 S3 평가 키·실패 기록이 그대로 맞는다), `schema_fp` = θ 스키마 필드 값 지문, `code_fp` = 호출자가 넘긴 core `engine_code_fp()` 값(단계 A 가 실행마다
  한 번 재 `StageAResult.code_fp` 로 넘긴다 -- 여기서 다시 재지 않는다).
* **평가 캐시**(설계 7.2): `cache` = {EvalKey: EvalResult}(실패 포함). 상한 = 실행이 만드는 고유 키 수. `disk_failures` = S3 evals 실패 줄에서 재구성한 {EvalKey: FailureRecord}
  (같은 S0·코드 지문만, 설계 7.3). 계수 `counters`(설계 7.4): requests, kernel_calls, hits, fail_hits, disk_hits, outside_domain, recompute_same_key.
* 예산: `eval_budget`(커널 평가 수 E_B, 선언 또는 find_front 가 한 번 유도), `deadline`(벽시계 바깥 정지).
"""
import copy
import dataclasses

from gmid_engine.authoring import THETA_BOUNDS, UNTIE_ORBITS
from gmid_engine.core import FailureRecord, PdkDecl, S0Slot, fp_of
from gmid_engine.graph import ELEMENT_MOS, S1_WRITERS, S1V_KEY
from gmid_engine.lut import require_lut_data, sweep_memo
from gmid_engine.metrics import (NoiseAnalysis, junction_field, metric_registry, metric_structure, mismatch_field, model_error_field)
from gmid_engine.sizing import KERNEL_KEY, PLAN_WRITERS, LutAccess

from .archive import S3Archive
from .area_decl import passive_area_decl
from .constraint_classes import constraint_classes
from .layer0_center import centre_start
from .kernel import evaluate
from .noise_decl import noise_decl
from .s0_fields import S0_WRITERS, STAGE_B_WRITERS, START_KEY
from .search_domain import search_domain
from .search_values import AXIS_AREA, EvalKey
from .start_intervals import start_intervals


# 평가 키 지문(`context_fp`)이 읽는 블록 -- S1 블록과 커널 계획·구조 파생 블록(평가 커널의 S0 입력)
_CONTEXT_WRITERS = tuple(sorted({writer for _kind_field, writer in S1_WRITERS.entries} | set(PLAN_WRITERS)))


class SearchContext:
    """`build_search_context` 결과. 참조(dc·spec·settings·archive·지문)와 실행 수명 상태(cache·counters·eval_times·seq·예산·cell_floors).
    설계 값은 읽기 속성이 S0 수준 필드에서 읽는다(모듈 머리 설명)."""

    def __init__(self, dc, spec, settings, context_fp, code_fp, archive):
        self.dc = dc
        self.spec = spec
        self.settings = settings
        self.context_fp = context_fp
        self.code_fp = code_fp
        self.archive = archive
        self.cache = {}
        self.disk_failures = {}
        self.computed_keys = set()
        self.counters = {k: 0 for k in ("requests", "kernel_calls", "hits", "fail_hits", "disk_hits",
                                         "outside_domain", "recompute_same_key")}
        self.eval_times = []
        self.seq = 0
        self.eval_budget = settings.eval_budget          # None 이면 evaluate 가 n + 1 평가 뒤 한 번 유도해 기록
        self.eval_budget_source = "declared" if settings.eval_budget is not None else None
        self.deadline = None                             # 벽시계 바깥 정지(perf_counter 기준) -- find_front 가 정한다
        self.cell_floors = {}                            # [r8] `cell_floor` 의 (kind, w_key, L 칸) -> 칸 정점 하한 등 LUT 파생(U17 ③에서 LUT memo 함수로)

    def _field(self, key, name):
        return self.dc.base.value("graph", key, name)

    @property
    def domain(self):
        return self._field(KERNEL_KEY, "search_domain")

    @property
    def schema_fp(self):
        return self.dc.base.field("graph", KERNEL_KEY, "theta_schema").value_fp

    @property
    def junction(self):
        return self._field(KERNEL_KEY, "junction_source")

    @property
    def mismatch(self):
        return self._field(KERNEL_KEY, "mismatch_source")

    @property
    def model_error(self):
        return self._field(KERNEL_KEY, "model_error")

    @property
    def area_decl(self):
        return self._field(KERNEL_KEY, "passive_area_decl")

    @property
    def structure(self):
        return self._field(S1V_KEY, "metric_structure")

    @property
    def noise_decl(self):
        return self._field(S1V_KEY, "noise_input_cells")

    @property
    def judged_constraints(self):
        return self._field(KERNEL_KEY, "constraint_classes").judged

    @property
    def ss_constraints(self):
        declared = self.spec.judged_constraints
        return tuple(declared[i] for i in self._field(KERNEL_KEY, "constraint_classes").ss)

    @property
    def constraint_notes(self):
        return tuple(dict(note) for note in self._field(KERNEL_KEY, "constraint_classes").notes)

    @property
    def rungs(self):
        """출발 사다리(`graph/start: rungs`, 칸 0 = 선택점) 또는 None(출발 구간을 만들지 않았다 -- S1v 없음)."""
        field = self.dc.base.field("graph", START_KEY, "rungs")
        return None if field is None else field.value

    @property
    def element_values(self):
        return tuple(self.dc.inputs.element_values)

    @property
    def driving(self):
        return self.spec.driving_spec


def _disk_failures(archive, context_fp, schema_fp):
    out = {}
    for row in archive.load_evals():
        if row.get("ok") or row.get("schema_fp") != schema_fp:
            continue
        key = EvalKey(context_fp, schema_fp, tuple(row["cells"]), row.get("w_fixed_fp"), tuple(row["theta_hex"]))
        fail = row["fail"]
        out[key] = FailureRecord(fail["class"], tuple(fail["devices"]), fail["margin"],
                                 tuple((k, v if isinstance(v, (str, int, float, bool, type(None))) else repr(v))
                                       for k, v in sorted(fail["detail"].items())))
    return out


def _wire_sweep_memo(ctx):
    """[설계 40 §7.3, D-PF1] 평가 sweep LUT memo 를 만들어 `ctx.dc` 의 것으로 바꾼다. 상한 = (n_θ + 1)·U_eval, U_eval = layer0 첫 점의
    첫 평가가 센 서로 다른 키 수(`sweep_memo`). 호출자가 준 memo 는 S0 준비(domain 등) 조회에만 쓰이고 상한 상수는 탐색에 영향이 없다.
    첫 평가는 임시 컨텍스트(archive 없음·빈 캐시)에서 돈다 -- 본 컨텍스트의 캐시·계수·S3 기록은 건드리지 않는다."""
    variables, theta, cells, _centre_u = centre_start(ctx)
    old = ctx.dc.lut

    def first_eval(probe):
        tmp = copy.copy(ctx)
        tmp.dc = dataclasses.replace(ctx.dc, lut=LutAccess(probe, old.w_keys))
        tmp.cache, tmp.disk_failures, tmp.computed_keys = {}, {}, set()
        tmp.counters = dict(ctx.counters)
        tmp.eval_times, tmp.archive, tmp.eval_budget = [], None, ctx.eval_budget
        evaluate(tmp, theta, cells)

    memo = sweep_memo(old.memo.lut, len(variables), first_eval, table_cache=old.memo.table_cache)
    ctx.dc = dataclasses.replace(ctx.dc, lut=LutAccess(memo, old.w_keys))


_OFFSET_METRICS = ("offset_in_sigma_mv", "offset_excess")


def _require_noise_data(dc_ctx, spec):
    """[U8, 설계 41 §7.2] 평가할 잡음 제약(값이 있는 판정 제약)이 선언됐는데 LUT 에 그 kind 의 잡음 r1 데이터가 없으면 `SchemaRejectedError(noise_lut_missing)`
    -- 탐색 중 조회 실패로 늦게 알지 않게 시작 때 거른다."""
    noisy = {n for n, entry in metric_registry().items() if entry.source_type is NoiseAnalysis}
    if any(d.metric in noisy and d.value is not None for d in spec.judged_constraints):
        classes = dict(dc_ctx.base.column("device", "element_class"))
        kinds = {k for n, k in dc_ctx.base.column("device", "kind") if classes[n] == ELEMENT_MOS}
        require_lut_data(dc_ctx.lut.memo.lut, kinds, noise=True)
    # [U13 후속, 설계 41 §6.4-2b·lut CONTRACT 9.5] 값이 있는 offset 제약(`offset_in_sigma_mv`·`offset_excess`)이 있으면 mismatch 감도 r1 데이터도 필수(fail-closed)
    if any(d.metric in _OFFSET_METRICS and d.value is not None for d in spec.judged_constraints):
        classes = dict(dc_ctx.base.column("device", "element_class"))
        kinds = {k for n, k in dc_ctx.base.column("device", "kind") if classes[n] == ELEMENT_MOS}
        require_lut_data(dc_ctx.lut.memo.lut, kinds, mismatch=True)


def _s0_blocks(dc_ctx, spec, settings, pdk_decl, lut_rule_decl, model_error):
    """S0 수준 블록을 차례로 부른 S0 수준 스냅샷(모듈 머리 순서)."""
    search_section = spec.search if isinstance(spec.search, tuple) else ()
    # [r10] 원소별 θ 수동소자 상자 = spec search.theta_bounds(authoring ThetaBound tuple) -- SearchSettings 값이 run 단위 재정의
    spec_bounds = next((s.value for s in search_section if s.field == THETA_BOUNDS and s.value), ())
    untie = tuple(name for name, _source in next((s.value for s in search_section if s.field == UNTIE_ORBITS and s.value), ()))
    # [결정 11] 면적 예산 = spec 판정 제약 `area_search_m2 <= 값` 중 가장 작은 값 -- θ 전류 상한(S-3b)을 닫는다
    budgets = [float(d.value) for d in spec.judged_constraints
               if d.metric == AXIS_AREA and d.op == "<=" and d.value is not None]
    lut = dc_ctx.lut
    base = dc_ctx.base.widen(S0_WRITERS)
    base = search_domain(base, lut, settings.resistance_bounds_ohm, settings.capacitance_bounds_f, pdk_decl, spec_bounds,
                         min(budgets) if budgets else None, untie)
    _require_noise_data(dc_ctx, spec)                 # [U8] 잡음 제약이 있으면 LUT 잡음 r1 데이터 필수(설계 41 §7.2)
    base = junction_field(base, pdk_decl, lut_rule_decl, lut)
    base = mismatch_field(base, pdk_decl)
    base = model_error_field(base, tuple(model_error))
    base = constraint_classes(base, tuple(spec.judged_constraints))
    base = passive_area_decl(base, tuple(sorted(e.name for e in spec.element_values if e.measurement_load)), pdk_decl)
    base = metric_structure(base)
    testbench = spec.noise_testbench
    base = noise_decl(base, tuple(spec.feedback) if isinstance(spec.feedback, tuple) else None,
                      () if testbench is None else tuple(c.element for c in testbench.sampling_caps))
    if base.field("graph", S1V_KEY, "views") is not None:
        base = start_intervals(base, spec, dc_ctx.inputs, pdk_decl, lut)
    return base


def build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp, s0=None):
    """`model_error` = ((metric, 값), ...) DEC-72 오라클 대조 모델 오차(`verified_by.model_error_pairs` 가 `derived.model_error_<metric>` 에서 만든다) -- 분해능 바닥
    (`ss_constraint_rows`). `s0` = core `S0Slot`(단계 A 결과의 S0 키) 또는 None. 잡음 제약이 있으면 LUT 잡음 r1 데이터, offset 제약이 있으면 mismatch r1 데이터가 있어야 한다."""
    if not isinstance(code_fp, str) or not code_fp:
        raise TypeError("build_search_context: code_fp 는 단계 A 가 잰 엔진 코드 지문(StageAResult.code_fp) 문자열이어야 한다")
    for name, value in (("pdk_decl", pdk_decl), ("lut_rule_decl", lut_rule_decl)):
        if not isinstance(value, PdkDecl):            # 무엇이든 만들기 전에 입력 형식부터(§3.7·3.9)
            raise TypeError("build_search_context: " + name + " 는 core read_pdk_decl 결과여야 한다")
    if s0 is not None and not isinstance(s0, S0Slot):
        raise TypeError("build_search_context: s0 는 core S0Slot(단계 A 결과 StageAResult.s0) 또는 None 이어야 한다")
    base = _s0_blocks(dc_ctx, spec, settings, pdk_decl, lut_rule_decl, model_error)
    if s0 is not None:
        s0.save(base, STAGE_B_WRITERS)             # v1.9.1 D6: S0 수준 블록이 모두 끝난 한 시점에 한 번(단계 B 층은 직렬화하지 않는다)
    dc = dataclasses.replace(dc_ctx, base=base)
    context_fp = fp_of((tuple((w, base.block_version(w)) for w in _CONTEXT_WRITERS), dc.lut, dc.inputs))
    archive = None if archive_root is None else S3Archive(archive_root, context_fp, code_fp)
    ctx = SearchContext(dc, spec, settings, context_fp, code_fp, archive)
    if archive is not None:
        ctx.disk_failures = _disk_failures(archive, context_fp, ctx.schema_fp)
    _wire_sweep_memo(ctx)
    return ctx
