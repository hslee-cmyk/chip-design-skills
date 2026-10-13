"""[U17 ①-b] S0 수준 층 필드 이동 -- 9 library 회로 통합 test (설계 40 v1.9 §2.4.2·§2.4.3·§2.4.7·§2.4.8 S0·B 층 행·§2.4.9 판정 2,
오케스트레이터 기본안 D1~D10(2026-10-13, `wt/_drafts/user_decisions.md`)).

무엇을 보나(회로마다):
1. 필드 존재·writer 유일성(§2.4.8): S0 수준 스냅샷 파일(§2.4.3 형식 -- 이 test 가 gzip JSON 을 직접 읽는다)에 아래 `GRAPH_ROWS`·`DEVICE_ROWS`
   필드가 있고, 필드마다 writer 가 파일 권한표(`writers`)의 그 (kind, field) 항목 하나와 같으며, design 이 이름을 적은 writer 는 그 이름이고,
   writer 는 계산 블록(`block_versions` 에 있고 같은 이름의 `ComputeBlock` 이 엔진에 있다)이다. 단계 B 층(residual_probe·dof_numeric)은
   파일에 없다(§2.4.3 '단계 B 층 … 쓰지 않는다', D5).
2. 디스크 왕복 비트 동일(§2.4.3): 파일의 모든 필드 값을 이 test 의 독립 디코더(design 형식: float.hex·tuple·frozenset·`<모듈>.<클래스>`)로
   되살린 값의 `fp_of` 가 실행 중 S0 수준 스냅샷(SearchContext `dc.base` = §2.4.7 '참조(S0 수준 스냅샷 뿌리)')의 같은 필드 value_fp 와 같다.
3. 소비자 필드 읽기(§2.4.2 '읽기: 소비자는 S0 수준 스냅샷의 필드를 읽는다'): 첫 실행(빈 S0 폴더)에서 S0 행 writer 블록마다 computes = 1·
   recomputes_same_input = 0 -- 단계 B·출발 구간·탐색 컨텍스트가 같은 값을 다시 계산하지 않는다(블록 계수, §2.4.9).
4. S0 스냅샷 재사용(§2.4.2 '같은 S0 의 다음 실행은 … 모든 블록이 재사용으로 끝난다(계산 0)', §2.4.9 판정 2 의 S0 부분 -- RunCounters 는 ②라
   as-built 블록 계수로 본다): 두 번째 실행은 단계 A 보고서 `s0_snapshot` = hit, 파일 바이트 불변, 파일 `block_versions` 의 모든 writer 블록
   computes = 0, S0 행 writer 블록은 한 번 이상 불린다(calls ≥ 1 -- 읽기가 블록 재사용으로 일어남).
5. 결과 불변(이 이동은 값 정의를 바꾸지 않는다): 단계 A·B 보고서의 기준선 키마다 정준 JSON sha256 이 base master a5d8ccb 코드로 이 test 작성
   주체가 직접 잰 값(`fixtures/u17_1b_s0_baseline.json`)과 같고, S0 필드 값 지문(`fp_of`)이 base 의 같은 값(StartIntervals·KernelContext·
   SearchContext 칸)의 지문과 같다. 기준선 측정 스크립트는 `wt/_scratch_u17_1b_tests/baseline.py`(엔진 밖) -- 피검 코드로 기대값을 만들지 않았다.

S0 스냅샷 저장 시점 = build_search_context 끝 1회(D6)라 실행 사슬은 단계 A -> 단계 B -> 커널 컨텍스트 -> 탐색 컨텍스트다. 단계 A 가 ok 가
아닌 회로(기준선 ngcc_3stage_ff = review_needed)는 탐색 컨텍스트를 만들지 않으므로 5 의 보고서 대조만 한다.

이름 미정(interface card 가 정하면 아래 한 곳만 고친다): `_search_context` 의 ①-b 뒤 커널·탐색 컨텍스트 생성 호출 형식(as-built 에서 `s1v=`·
`ach=` 를 뺐다), `graph/kernel` 의 fixed_values·resistor_values·l_ties(design '`build_kernel_context`를 블록으로')·constraint_classes
('제약 분류 블록')·junction_source·mismatch_source·passive_area_decl·model_error('각각 search·metrics의 S0 블록') writer 이름 -- None 은 이름을
단언하지 않고 '권한표 항목 하나 = 계산 블록 하나'만 본다.
실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import dataclasses
import gzip
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmid_engine.core import BoundedLRU, ComputeBlock, fp_of, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
BASELINE = json.loads((Path(__file__).resolve().parent / "fixtures" / "u17_1b_s0_baseline.json").read_text(encoding="utf-8"))
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
S0_ENV = "GMID_S0_SNAPSHOT_DIR"
SUFFIX = ".json.gz"

# 설계 40 v1.9 §2.4.8 S0 행 + 기본안 D1·D2·D3·D7·D8 -- (record key, 필드들, design 이 적은 writer 이름 또는 None(이름 미정)).
GRAPH_ROWS = (
    ("s1v", ("views", "l_classes", "findings", "declared", "applied_facts"), "build_s1v"),            # D1
    ("s1v", ("metric_structure",), "metric_structure"),
    ("s1v", ("noise_input_cells",), "noise_decl"),                                                     # D7 값 = NoiseDecl
    ("coupling", ("vars", "column_block_map", "bias_columns"), "coupling_vars"),                       # D8
    ("ach", ("curve_checks", "gain_checks", "area_bound", "headroom_rows", "buffer_window_report", "warnings", "reasons",
             "verdict", "dof", "count_budget", "local_inputs"), "achievability"),                      # D2·D9
    ("start", ("rungs", "conflicts", "inactive", "macro", "records", "area_est_m2", "area_fraction", "uncovered"),
     "start_intervals"),                                                                               # D3 (noise_inputs·placement·kvl_* 는 ②)
    ("kernel", ("theta_schema",), "dc_theta_schema"),                                                  # D8 writer 유지
    ("kernel", ("fixed_values", "resistor_values", "l_ties"), None),
    ("kernel", ("search_domain",), "search_domain"),                                                   # §2.4.7 Q5 표 'writer search_domain'
    ("kernel", ("constraint_classes",), None),
    ("kernel", ("junction_source",), None),
    ("kernel", ("mismatch_source",), None),
    ("kernel", ("passive_area_decl",), None),
    ("kernel", ("model_error",), None),
)
# (필드들, writer) -- start.* 는 기준선 출발 구간 행이 있는 소자마다, dc_self_referential 은 권한표·블록 선언만(값이 소자마다 있는지는 design 미정).
DEVICE_START = (("start.row", "start.point"), "start_intervals")
DEVICE_SELF_REF = ("dc_self_referential", "dc_writer_plan")         # §2.4.8 '쓰기 계획 블록(sizing)' = as-built dc_writer_plan
STAGE_B_FIELDS = ("residual_probe", "dof_numeric")                   # §2.4.8 B 층 -- 직렬화하지 않는다(§2.4.3, D5)


# ---------------------------------------------------------------- 실행 환경

@pytest.fixture(scope="module")
def env(tmp_path_factory):
    loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
    man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
    kinds = dict(DEVICE_KINDS)
    mins = {}
    for e in man["slices"]:
        mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
    dm = BoundedLRU(16)
    pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
    q = dict(pdk.quantities)
    spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                   noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
    lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                       noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
    return SimpleNamespace(lut=lut, pdk=pdk, rule=read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm),
                           root=tmp_path_factory.mktemp("u17b"), runs={})


def _blocks():
    """엔진 모듈 수준 계산 블록 {이름: ComputeBlock}(이미 import 된 gmid_engine 모듈 전부)."""
    out = {}
    for name, mod in list(sys.modules.items()):
        if name.startswith("gmid_engine.") and ".tests" not in name and mod is not None:
            for value in list(vars(mod).values()):
                if isinstance(value, ComputeBlock):
                    out[value.name] = value
    return out


def _s0_of(result):
    """결과 칸 중 graph/s1v 레코드를 가진 GraphSnapshot(§2.4.7 '단계 결과는 S0 수준 스냅샷 참조만') -- 칸 이름은 보지 않는다."""
    from gmid_engine.core import GraphSnapshot
    for f in dataclasses.fields(result):
        v = getattr(result, f.name)
        if isinstance(v, GraphSnapshot) and v.record("graph", "s1v") is not None:
            return v
    raise AssertionError("결과에 S0 수준 스냅샷 참조(graph/s1v 레코드를 가진 GraphSnapshot)가 없다: " + type(result).__name__)


def _search_context(env, a, b):
    """이름 미정 -- ①-b 뒤 커널 컨텍스트·탐색 컨텍스트 생성. 임시 형식: as-built 호출에서 `s1v=`·`ach=` 를 빼고(그 값은 S0 필드), L 동치류는
    S0 필드 `graph/s1v: l_classes` 에서 읽는다. 탐색 설정은 tests/search/u13_real.py 와 같은 입력."""
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    s0 = _s0_of(b)
    kctx = build_kernel_context(a.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(env.memo),
                                l_classes=s0.value("graph", "s1v", "l_classes"))
    settings = SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "u17-1b test fixture"),), (1e-13, 1e-10))
    return build_search_context(kctx, a.spec, settings, None, env.pdk, env.rule, code_fp=a.code_fp)


def _chain(env, circuit, tag, monkeypatch_dir):
    """단계 A -> B -> (둘 다 ok 면) 탐색 컨텍스트. 블록 계수를 비우고 돌린 뒤 {이름: BlockStats}."""
    blocks = _blocks()
    for blk in blocks.values():
        blk.reset_stats()
    out = env.root / circuit / tag
    os.environ[S0_ENV] = str(monkeypatch_dir)
    a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env.lut, pdk_decl=env.pdk,
                    output_dir=out)
    env.memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, env.memo, env.pdk, output_dir=out, diagnostic=True)
    sctx = _search_context(env, a, b) if (a.status, b.status) == ("ok", "ok") else None
    blocks = _blocks()
    return SimpleNamespace(a=a, b=b, sctx=sctx, stats={n: blk.stats() for n, blk in blocks.items()},
                           report_a=json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8")),
                           report_b=json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8")))


def _files(directory):
    return sorted(p for p in Path(directory).glob("*" + SUFFIX))


def _run(env, circuit):
    """회로마다 한 번: 빈 S0 폴더에서 첫 실행(miss) -> 같은 폴더로 두 번째 실행. 결과는 모듈 캐시."""
    if circuit not in env.runs:
        s0_dir = env.root / circuit / "s0"
        s0_dir.mkdir(parents=True)
        old = os.environ.get(S0_ENV)
        try:
            first = _chain(env, circuit, "first", s0_dir)
            files = _files(s0_dir)
            blob = files[0].read_bytes() if len(files) == 1 else None
            mtime = files[0].stat().st_mtime_ns if len(files) == 1 else None
            second = _chain(env, circuit, "second", s0_dir)
            env.runs[circuit] = SimpleNamespace(first=first, second=second, files=files, blob=blob, mtime=mtime,
                                                files_after=_files(s0_dir))
        except Exception as exc:          # test harness: 첫 실패를 저장해 같은 회로의 다른 test 가 같은 원인으로 실패하게 한다(재실행 없음)
            env.runs[circuit] = exc
        finally:
            if old is None:
                os.environ.pop(S0_ENV, None)
            else:
                os.environ[S0_ENV] = old
    if isinstance(env.runs[circuit], Exception):
        raise env.runs[circuit]
    return env.runs[circuit]


def _searched(circuit):
    return BASELINE[circuit]["status"] == ["ok", "ok"]


SEARCHED = [c for c in CIRCUITS if _searched(c)]


def _doc(run):
    assert len(run.files) == 1, "S0 수준 스냅샷 파일은 S0 하나에 하나(§2.4.3): " + repr([p.name for p in run.files])
    return json.loads(gzip.decompress(run.blob).decode("ascii"))


# ---------------------------------------------------------------- 독립 디코더 (§2.4.3 형식)

def _decode(obj):
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    tag = obj["__type__"]
    if tag == "float":
        return float.fromhex(obj["hex"])
    if tag == "bytes":
        return bytes.fromhex(obj["hex"])
    if tag == "tuple":
        return tuple(_decode(x) for x in obj["items"])
    if tag == "frozenset":
        return frozenset(_decode(x) for x in obj["items"])
    module, _, cls_name = tag.rpartition(".")
    cls = getattr(importlib.import_module(module), cls_name)
    return cls(**{name: _decode(v) for name, v in obj["fields"].items()})


def test_independent_decoder_roundtrips_design_format():
    @dataclasses.dataclass(frozen=True)
    class _P:
        x: float
    enc = {"__type__": "tuple", "items": [{"__type__": "float", "hex": (0.1).hex()}, {"__type__": "frozenset", "items": ["a", 1]}, None]}
    assert _decode(enc) == (0.1, frozenset({"a", 1}), None)
    assert fp_of(_decode({"__type__": "float", "hex": (-0.0).hex()})) == fp_of(-0.0)


# ---------------------------------------------------------------- 1. 필드 존재·writer 유일성

@pytest.mark.parametrize("circuit", SEARCHED)
def test_s0_fields_present_with_single_block_writer(env, circuit):
    run = _run(env, circuit)
    doc = _doc(run)
    table = {}
    for kind, field, writer in doc["writers"]:
        assert (kind, field) not in table, "권한표에 같은 (kind, field) 두 번: " + repr((kind, field))
        table[(kind, field)] = writer
    records = {(r["kind"], r["key"]): r["fields"] for r in doc["records"]}
    blocks = _blocks()
    problems = []
    for key, fields, named in GRAPH_ROWS:
        row_writers = set()
        for field in fields:
            cell = records.get(("graph", key), {}).get(field)
            if cell is None:
                problems.append("없음 graph/%s: %s" % (key, field))
                continue
            owner = table.get(("graph", field))
            row_writers.add(cell["writer"])
            if cell["writer"] != owner:
                problems.append("graph/%s: %s writer %r != 권한표 %r" % (key, field, cell["writer"], owner))
            if named is not None and cell["writer"] != named:
                problems.append("graph/%s: %s writer %r != design %r" % (key, field, cell["writer"], named))
        if len(row_writers) > 1:
            problems.append("graph/%s %s: 한 블록이 쓰는 행인데 writer 여럿 %r" % (key, fields, sorted(row_writers)))
        for w in row_writers:
            if w not in doc["block_versions"] or w not in blocks:
                problems.append("writer %r 가 계산 블록이 아니다(block_versions·ComputeBlock)" % w)
    devices = set(BASELINE[circuit]["start"]["row_fp"])
    assert devices
    for field in DEVICE_START[0]:
        have = {k for (kind, k), f in records.items() if kind == "device" and field in f}
        if have != devices:
            problems.append("device %s 소자 %r != 기준선 출발 구간 행 %r" % (field, sorted(have), sorted(devices)))
        writers = {f[field]["writer"] for (kind, k), f in records.items() if kind == "device" and field in f}
        if writers - {DEVICE_START[1]} or table.get(("device", field)) != DEVICE_START[1]:
            problems.append("device %s writer %r / 권한표 %r" % (field, sorted(writers), table.get(("device", field))))
    if table.get(("device", DEVICE_SELF_REF[0])) != DEVICE_SELF_REF[1]:
        problems.append("device %s 권한표 writer %r" % (DEVICE_SELF_REF[0], table.get(("device", DEVICE_SELF_REF[0]))))
    for (kind, key), fields in records.items():
        if key == "stage_b" or set(fields) & set(STAGE_B_FIELDS):
            problems.append("단계 B 층 필드가 S0 파일에 있다: %s/%s %r" % (kind, key, sorted(set(fields) & set(STAGE_B_FIELDS))))
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 2. 디스크 왕복 비트 동일

@pytest.mark.parametrize("circuit", SEARCHED)
def test_s0_file_values_roundtrip_bit_identical(env, circuit):
    run = _run(env, circuit)
    doc = _doc(run)
    base = run.first.sctx.dc.base                        # §2.4.7: KernelContext.base = S0 수준 스냅샷(참조)
    bad, n = [], 0
    for r in doc["records"]:
        for name, cell in r["fields"].items():
            mem = base.field(r["kind"], r["key"], name)
            n += 1
            if mem is None or fp_of(_decode(cell["value"])) != mem.value_fp:
                bad.append("%s/%s: %s" % (r["kind"], r["key"], name))
    assert n and not bad, "디스크 왕복 값이 실행 중 S0 필드와 다르다 %d/%d:\n%s" % (len(bad), n, "\n".join(bad[:40]))
    for key, fields, _w in GRAPH_ROWS:                  # 실행 중 S0 필드가 파일에 다 있다(부분 저장 금지)
        for field in fields:
            if base.field("graph", key, field) is not None:
                assert field in {nm for r in doc["records"] if (r["kind"], r["key"]) == ("graph", key) for nm in r["fields"]}


# ---------------------------------------------------------------- 3. 소비자 필드 읽기 (첫 실행 블록 계수)

def _s0_writers(doc):
    return sorted({cell["writer"] for r in doc["records"] if r["kind"] == "graph" and r["key"] in {k for k, _f, _w in GRAPH_ROWS}
                   for cell in r["fields"].values()} | {DEVICE_START[1]})


@pytest.mark.parametrize("circuit", SEARCHED)
def test_cold_run_computes_each_s0_block_once(env, circuit):
    run = _run(env, circuit)
    stats = run.first.stats
    bad = ["%s computes=%s recomputes_same_input=%s" % (w, getattr(stats.get(w), "computes", None),
                                                         getattr(stats.get(w), "recomputes_same_input", None))
           for w in _s0_writers(_doc(run))
           if w not in stats or stats[w].computes != 1 or stats[w].recomputes_same_input != 0]
    assert not bad, "S0 블록은 실행 하나에서 한 번만 계산된다(소비자는 필드를 읽는다):\n" + "\n".join(bad)


# ---------------------------------------------------------------- 4. 두 번째 실행 = S0 계산 0

@pytest.mark.parametrize("circuit", SEARCHED)
def test_second_run_hits_s0_snapshot_with_zero_block_computes(env, circuit):
    run = _run(env, circuit)
    doc = _doc(run)
    assert run.second.report_a["s0_snapshot"] == "hit"
    assert run.files_after == run.files and run.files[0].read_bytes() == run.blob and run.files[0].stat().st_mtime_ns == run.mtime
    stats = run.second.stats
    computed = sorted("%s computes=%d" % (w, stats[w].computes) for w in doc["block_versions"] if w in stats and stats[w].computes)
    assert not computed, "두 번째 실행에서 S0 수준 블록이 계산됐다:\n" + "\n".join(computed)
    unread = [w for w in _s0_writers(doc) if w not in stats or stats[w].calls < 1]
    assert not unread, "S0 행 writer 블록이 두 번째 실행에서 불리지 않았다(필드 읽기가 블록 재사용이 아님): %r" % unread
    assert run.second.sctx.dc.base.fp == run.first.sctx.dc.base.fp


# ---------------------------------------------------------------- 5. 결과 불변 (base a5d8ccb 기준선)

def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")).hexdigest()


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_stage_reports_unchanged_from_base(env, circuit):
    run = _run(env, circuit)
    want = BASELINE[circuit]
    assert [run.first.a.status, run.first.b.status] == want["status"]
    diff = [k for k, sha in want["stage_a_sha"].items() if _sha(run.first.report_a.get(k)) != sha]
    diff += ["stage_b." + k for k, sha in want["stage_b_sha"].items() if _sha(run.first.report_b.get(k)) != sha]
    ach = run.first.report_b.get("achievability") or {}
    diff += ["stage_b.achievability." + k for k, sha in want["achievability_sha"].items() if _sha(ach.get(k)) != sha]
    assert not diff, "base 와 다른 보고서 키: %r" % diff


@pytest.mark.parametrize("circuit", SEARCHED)
def test_s0_field_values_unchanged_from_base(env, circuit):
    run = _run(env, circuit)
    base = run.first.sctx.dc.base
    want = BASELINE[circuit]
    diff = []
    for device, fp in want["start"]["row_fp"].items():
        if base.field("device", device, "start.row") is None or base.field("device", device, "start.row").value_fp != fp:
            diff.append("device %s start.row" % device)
    for field, key in (("rungs", "ladder_fp"), ("conflicts", "conflicts_fp"), ("inactive", "inactive_fp"), ("macro", "macro_fp"),
                       ("records", "records_fp"), ("area_est_m2", "area_est_m2_fp"), ("area_fraction", "area_fraction_fp"),
                       ("uncovered", "uncovered_fp")):
        got = base.field("graph", "start", field)
        if got is None or got.value_fp != want["start"][key]:
            diff.append("graph/start: " + field)
    for key, (record, field) in {"schema_fp": ("kernel", "theta_schema"), "fixed_values_fp": ("kernel", "fixed_values"),
                                 "resistor_values_fp": ("kernel", "resistor_values"), "l_ties_fp": ("kernel", "l_ties"),
                                 "search_domain_fp": ("kernel", "search_domain"), "junction_source_fp": ("kernel", "junction_source"),
                                 "mismatch_source_fp": ("kernel", "mismatch_source"), "passive_area_decl_fp": ("kernel", "passive_area_decl"),
                                 "model_error_fp": ("kernel", "model_error"), "metric_structure_fp": ("s1v", "metric_structure"),
                                 "noise_input_cells_fp": ("s1v", "noise_input_cells")}.items():
        if key not in want["kernel"]:
            continue                                   # 기준선에서 지문을 못 낸 값 형식(픽스처 *_fp_error 칸) -- 보고서 대조가 덮는다
        got = base.field("graph", record, field)
        if got is None or got.value_fp != want["kernel"][key]:
            diff.append("graph/%s: %s" % (record, field))
    assert not diff, "base 와 다른 S0 필드 값: %r" % diff
