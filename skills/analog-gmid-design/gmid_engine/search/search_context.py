"""탐색 컨텍스트 -- S0 당 1회 루프 불변 입력 + 실행 수명 평가 캐시·계수 (설계 2.1·7.2·7.4, WP-23 (3)).

진입점: `build_search_context(dc_ctx, spec, settings, archive_root) -> SearchContext`.

* 담는 것: sizing `KernelContext`(dc), `SearchDomain`, 지문 3개(S0 = `context_fp`, θ 스키마 = `schema_fp`, 코드 =
  `code_fp` -- core·lut·graph·sizing·metrics·search 소스 바이트 sha256), spec 요소 값, 판정 보류 제약 기록, S3 기록기.
* **평가 캐시**(설계 7.2): `cache` = {EvalKey: EvalResult}(실패 포함). 상한 = 실행이 만드는 고유 키 수 -- 요약은 θ 길이에
  비례하는 작은 값이라 퇴출이 없다. `disk_failures` = S3 evals 실패 줄에서 재구성한 {EvalKey: FailureRecord}(같은 S0·코드 지문만,
  설계 7.3). 모듈 수준 캐시가 아니라 이 객체가 소유한다.
* 계수 `counters`(설계 7.4): requests, kernel_calls, hits, fail_hits, disk_hits, outside_domain, recompute_same_key.
* spec 제약: 판정 대상(`judged_constraints`) 중 metric 이 목적 축(power_dc_w·area_search_m2)인 것만 커널 결과로 잴 수 있다.
  나머지(ss 영역 등)는 MOD5 `ss_linearize` 가 없어 `constraint_notes` 에 '판정 보류'로 남긴다(통과로 세지 않는다, S-1).
"""
import hashlib
from pathlib import Path

from gmid_engine.core import FailureRecord, fp_of

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


def build_search_context(dc_ctx, spec, settings, archive_root):
    domain = search_domain(dc_ctx, settings)
    context_fp = fp_of((dc_ctx.base.fp, dc_ctx.plan_versions, dc_ctx.lut, dc_ctx.fixed_values, dc_ctx.resistor_values,
                        dc_ctx.inputs))
    schema_fp = fp_of(dc_ctx.schema)
    code_fp = _code_fp()
    judged, notes = [], []
    for decl in spec.judged_constraints:
        if decl.metric in AXES and decl.value is not None:
            judged.append((decl.metric, decl.op, float(decl.value)))
        else:
            notes.append({"metric": decl.metric, "op": decl.op, "value": decl.value,
                          "verdict": "judgment_pending", "reason": "metric_not_evaluable_without_ss_linearize"})
    archive = None if archive_root is None else S3Archive(archive_root, context_fp, code_fp)
    ctx = SearchContext(dc_ctx, domain, settings, context_fp, schema_fp, code_fp,
                        tuple(dc_ctx.inputs.element_values), tuple(judged), tuple(notes), archive)
    if archive is not None:
        ctx.disk_failures = _disk_failures(archive, context_fp, schema_fp)
    return ctx
