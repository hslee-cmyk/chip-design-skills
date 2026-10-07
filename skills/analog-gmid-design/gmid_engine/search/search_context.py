"""탐색 컨텍스트 -- S0 당 1회 루프 불변 입력 + 실행 수명 평가 캐시·계수 (설계 2.1·7.2·7.4, WP-23 (3)).

진입점: `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl) -> SearchContext`(`pdk_decl` = core
`read_pdk_decl` 결과 -- W 하한·b_A 의 `min_finger_w_m`·`manufacturing_grid_m`).

* 담는 것: sizing `KernelContext`(dc), `SearchDomain`, 지문 3개(S0 = `context_fp`, θ 스키마 = `schema_fp`, 코드 =
  `code_fp` -- core·lut·graph·sizing·metrics·search 소스 바이트 sha256), spec 요소 값, 판정 보류 제약 기록, S3 기록기.
* **평가 캐시**(설계 7.2): `cache` = {EvalKey: EvalResult}(실패 포함). 상한 = 실행이 만드는 고유 키 수 -- 요약은 θ 길이에
  비례하는 작은 값이라 퇴출이 없다. `disk_failures` = S3 evals 실패 줄에서 재구성한 {EvalKey: FailureRecord}(같은 S0·코드 지문만,
  설계 7.3). 모듈 수준 캐시가 아니라 이 객체가 소유한다.
* 계수 `counters`(설계 7.4): requests, kernel_calls, hits, fail_hits, disk_hits, outside_domain, recompute_same_key.
* spec 제약(`spec.judged_constraints`): 값이 결정 대기면 `constraint_notes`(judgment_pending). 목적 축(power_dc_w·
  area_search_m2) 제약은 `judged_constraints` -- 커널 결과로 잰다. 그 밖(ss 영역 등)은 `ss_constraints` -- 점마다
  `ss_constraint_rows` 가 재거나 '미측정'으로 남긴다(S-1, 빠뜨리지 않음).
* 예산: `eval_budget`(커널 평가 수 E_B, 선언 또는 find_front 가 한 번 유도), `deadline`(벽시계 바깥 정지).
"""
import hashlib
from pathlib import Path

from gmid_engine.core import FailureRecord, PdkDecl, fp_of
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.metrics import JunctionSource, metric_registry

from .archive import S3Archive
from .search_domain import search_domain
from .search_values import AXES, EvalKey

_CODE_PACKAGES = ("core", "lut", "graph", "sizing", "metrics", "search")


def _code_fp():
    root = Path(__file__).resolve().parents[1]
    digests = []
    for pkg in _CODE_PACKAGES:
        for path in sorted((root / pkg).glob("*.py")):
            digests.append((pkg + "/" + path.name, hashlib.sha256(path.read_bytes()).hexdigest()))
    return fp_of(tuple(digests))


class SearchContext:
    """`build_search_context` 결과. 불변 입력(dc·domain·settings·지문·제약)과 실행 수명 상태(cache·counters·eval_times·seq)."""

    def __init__(self, dc, domain, settings, context_fp, schema_fp, code_fp, element_values, judged, notes, archive):
        self.dc = dc
        self.domain = domain
        self.settings = settings
        self.context_fp = context_fp
        self.schema_fp = schema_fp
        self.code_fp = code_fp
        self.element_values = element_values
        self.judged_constraints = judged
        self.constraint_notes = notes
        self.archive = archive
        self.cache = {}
        self.disk_failures = {}
        self.computed_keys = set()
        self.counters = {k: 0 for k in ("requests", "kernel_calls", "hits", "fail_hits", "disk_hits",
                                         "outside_domain", "recompute_same_key")}
        self.eval_times = []
        self.seq = 0
        self.ss_constraints = ()
        self.spec_passive_values = ()
        self.junction = None
        self.eval_budget = settings.eval_budget          # None 이면 evaluate 가 n + 1 평가 뒤 한 번 유도해 기록
        self.eval_budget_source = "declared" if settings.eval_budget is not None else None
        self.deadline = None                             # 벽시계 바깥 정지(perf_counter 기준) -- find_front 가 정한다
        self.cell_floors = {}                            # [r8] `cell_floor` 의 (kind, w_key, L 칸) -> 칸 정점 하한 등 S0 수명 캐시


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


def build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl):
    """[r6] `lut_rule_decl` = core `read_pdk_decl(<LUT 생성 규칙 선언>)`(sky130 = assets/sky130_lut_rule_decl.json). 여기서 S0 당
    1회 `JunctionSource.from_decls(pdk_decl, lut_rule_decl, dc_ctx.lut.memo.lut)`(metrics 7.6 필수 junction)를 만든다."""
    for name, value in (("pdk_decl", pdk_decl), ("lut_rule_decl", lut_rule_decl)):
        if not isinstance(value, PdkDecl):            # 무엇이든 만들기 전에 입력 형식부터(§3.7·3.9)
            raise TypeError("build_search_context: " + name + " 는 core read_pdk_decl 결과여야 한다")
    domain = search_domain(dc_ctx, settings, pdk_decl)
    junction = JunctionSource.from_decls(pdk_decl, lut_rule_decl, dc_ctx.lut.memo.lut)
    context_fp = fp_of((dc_ctx.base.fp, dc_ctx.plan_versions, dc_ctx.lut, dc_ctx.fixed_values, dc_ctx.resistor_values,
                        dc_ctx.inputs))
    schema_fp = fp_of(dc_ctx.schema)
    code_fp = _code_fp()
    judged, ss, notes = [], [], []
    registry = metric_registry()
    for decl in spec.judged_constraints:
        if decl.value is None:
            notes.append({"metric": decl.metric, "op": decl.op, "verdict": "judgment_pending",
                          "reason": "constraint_value_pending", "decision": decl.value_decision})
        elif decl.metric in AXES:
            judged.append((decl.metric, decl.op, float(decl.value)))
        elif decl.metric in registry and registry[decl.metric].signature.view_kind is not None:
            ss.append(decl)
        else:
            notes.append({"metric": decl.metric, "op": decl.op, "value": decl.value, "verdict": "unmeasured",
                          "reason": "metric_not_in_registry_or_no_ss_view"})
    archive = None if archive_root is None else S3Archive(archive_root, context_fp, code_fp)
    ctx = SearchContext(dc_ctx, domain, settings, context_fp, schema_fp, code_fp,
                        tuple(dc_ctx.inputs.element_values), tuple(judged), tuple(notes), archive)
    ctx.ss_constraints = tuple(ss)
    ctx.junction = junction
    classes = dict(dc_ctx.base.column("device", "element_class"))
    ctx.spec_passive_values = tuple(sorted((n, float(v)) for n, v in dc_ctx.inputs.element_values
                                           if v is not None and classes.get(n) == ELEMENT_PASSIVE))
    if archive is not None:
        ctx.disk_failures = _disk_failures(archive, context_fp, schema_fp)
    return ctx
