"""[U17 ①-b] S0 수준 층 필드 -- 9 library 회로 통합 test. [xrun] 실행 사이 재사용 제거(설계 40 v1.10 §2.4.3 '수명 -- 실행 안에서만',
§2.4.9 판정 1, 사용자 결정 2026-10-15 "나로 해", interface card C3·C4)에 맞춰 파일 단위로 다시 썼다.

무엇을 보나(회로마다, 같은 프로세스에서 사슬 단계 A -> B -> 커널 컨텍스트 -> 탐색 컨텍스트를 두 번 -- 사슬마다 새 open_run() 쌍,
계수 = 그 실행 RunCounters 행[XRUN-F1 card B C1·C6]):
1. 필드 존재·writer 유일성(§2.4.8): 탐색 컨텍스트의 S0 수준 스냅샷(`dc.base`, 메모리)에 아래 `GRAPH_ROWS`·`DEVICE_START` 필드가 있고, 필드마다
   writer 가 스냅샷 권한표(`writers`)의 그 (kind, field) 항목 하나와 같으며, design 이 이름을 적은 writer 는 그 이름이고, writer 는 계산 블록
   (`block_versions` 에 있고 같은 이름의 `ComputeBlock` 이 엔진에 있다)이다.
2. 실행 안 G-10(C4, §2.4.9 판정 1): 첫 실행에서 S0 행 writer 블록마다 computes = 1·recomputes_same_input = 0.
3. [XR-1] 반복 실행은 다시 계산한다(C3): 두 번째 실행도 S0 행 writer 블록마다 computes = 1·recomputes_same_input = 0 -- 앞 실행이 남긴 것
   (디스크·S3)으로 계산을 건너뛰지 않는다. writer 목록은 디스크 파일이 아니라 두 번째 실행 `dc.base` 의 graph S0 레코드 필드 writer 에서 모은다.
4. 반복 실행 출력 비트 동일(C3, 같은 BLAS 설정 -- 엔진 import 가 BLAS 스레드를 1 로 고정, NFR-4 card 2 C1): 단계 A·B 보고서 JSON 바이트, `dc.base` 필드
   (kind, key, field) -> value_fp 표, context_fp, schema_fp.
5. 결과 불변(base 기준선, 이 card 는 값 정의를 바꾸지 않는다): 단계 A·B 보고서의 기준선 키마다 정준 JSON sha256 이 기준선
   (`fixtures/u17_1b_s0_baseline.json`, oracle (c) -- 아래 '기준선 출처')과 같고, S0 필드 값 지문(`fp_of`)이 기준선과 같다.
6. junction_source: 내용(params 지문·온도·PDK 선언 sha)이 기준선과 같고, 값(메모리)의 문자열 어디에도 이 checkout 의 저장소 경로가 없다.

[xrun] 지운 것(이유 = 설계 40 v1.10 §2.4.3 '디스크: S0 수준 층을 디스크에 쓰지도 읽지도 않는다', test 삭제 목록):
- 두 번째 실행 S0 적중·계산 0 test(옛 4) -- 판정 2 폐지(§2.4.9). XR-1(위 3)이 반대 성질(다시 계산)을 본다.
- S0 폴더 조작(S0 위치 환경 변수), S0 파일 읽기(`_doc`·`_files`), 독립 디코더와 그 자기 test, 디스크 왕복 비트 동일 test(옛 2) -- 파일이 없다.
- 옛 1 의 '단계 B 층 필드가 S0 파일에 없다' 확인 -- 직렬화 대상이 없어졌다(메모리 스냅샷에는 단계 B 층이 있을 수 있다).
옛 1·3·6 은 파일 대신 메모리 `dc.base` 로 같은 성질을 본다.

기준선 출처(옛 문서 그대로): 단계 A·B 보고서의 기준선 키마다 정준 JSON sha256 은 base master a5d8ccb 코드로 이 test 작성 주체가 직접 잰 값
(`wt/_scratch_u17_1b_tests/baseline.py`, 엔진 밖). [U17 ①-b 판정 후 2026-10-14] `tables` 는 설계 40 v1.9.1 D1 + 추가 결정 (c) 만큼만 변환
(`wt/_scratch_u17_1b_fix_tests/transform_tables_baseline.py`). [library spec card 2026-10-14, U-3] spec 입력이 바뀐 4회로는 base 41a2c4a 코드로
다시 잰 값(`wt/_scratch_libspec_tests/remeasure.py`·`merge.py`, OPENBLAS_NUM_THREADS=1). junction 내용은 base 9255a22 코드로 잰 값
(`wt/_scratch_u17_1b_fix_tests/junction_content_base.py`). 피검 코드로 기대값을 만들지 않았다.

단계 A 가 ok 가 아닌 회로(기준선 ngcc_3stage_ff = review_needed)는 탐색 컨텍스트를 만들지 않으므로 5 의 보고서 대조만 한다.
이름 미정(interface card 가 정하지 않은 writer 이름): `graph/kernel` 의 fixed_values·resistor_values·l_ties·constraint_classes·junction_source·
mismatch_source·passive_area_decl·model_error -- None 은 이름을 단언하지 않고 '권한표 항목 하나 = 계산 블록 하나'만 본다.
tests/integration/test_blas_thread_determinism.py 가 이 모듈의 `SKILL`·`LIBRARY`·`DEVICE_KINDS`·`CAP_SUFFIX`·`BASELINE`·`_settings`·
`_search_context` 를 하위 프로세스에서 쓴다(이름 유지). 실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import o227_stop_pin      # 정지 사유 고정 헬퍼·표(O-227 임시) -- tests/integration/o227_stop_pin.py
from gmid_engine.core import BoundedLRU, ComputeBlock, fp_of, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
BASELINE = json.loads((Path(__file__).resolve().parent / "fixtures" / "u17_1b_s0_baseline.json").read_text(encoding="utf-8"))
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))

# 설계 40 v1.9 §2.4.8 S0 행 + 기본안 D1·D2·D3·D7·D8 -- (record key, 필드들, design 이 적은 writer 이름 또는 None(이름 미정)).
GRAPH_ROWS = (
    ("s1v", ("views", "l_classes", "findings", "declared", "applied_facts"), "build_s1v"),            # D1 (A-76: 파생 술어 네 필드는 없다)
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
        v = getattr(v, "snapshot", v)     # [이름 정정] 결과 칸 = S1Graph(.snapshot = GraphSnapshot) -- tests/pipeline/test_stage_a.py 같은 helper 형식
        if isinstance(v, GraphSnapshot) and v.record("graph", "s1v") is not None:
            return v
    raise AssertionError("결과에 S0 수준 스냅샷 참조(graph/s1v 레코드를 가진 GraphSnapshot)가 없다: " + type(result).__name__)


def _search_context(env, a, b):
    """①-b 뒤 커널 컨텍스트·탐색 컨텍스트 생성. L 동치류는 S0 필드 `graph/s1v: l_classes` 에서 읽는다. 탐색 설정은 tests/search/u13_real.py 와
    같은 입력. [xrun] interface card C1: build_search_context 는 s0 키워드를 받지 않는다(S0 저장 폐지) -- 같은 실행 안 단계 B 결과를 메모리로 넘긴다."""
    from gmid_engine.search import build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    _s0_of(b)                             # 결과가 S0 수준 스냅샷 참조를 싣는다(§2.4.7)
    # [XRUN-F1 card B C6] 커널 컨텍스트 = 단계 A 와 같은 실행(단계 A 결과의 두 칸)
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(env.memo), donors=a.donors, counters=a.counters)
    return build_search_context(kctx, a.spec, _settings(), None, env.pdk, env.rule, code_fp=a.code_fp)


def _settings():
    """탐색 설정(tests/search/u13_real.py 와 같은 입력). [이름 정정] 단계 B 에도 같은 값을 넘긴다 -- pipeline CONTRACT 5절 `run_stage_b(settings=)`:
    'build_search_context 와 같은 값을 넘기면 정의역 블록이 한 번만 계산된다'(한 실행 = 한 설정)."""
    from gmid_engine.search import SearchSettings
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "u17-1b test fixture"),), (1e-13, 1e-10))


def _chain(env, circuit, tag):
    """단계 A -> B -> (둘 다 ok 면) 탐색 컨텍스트. 실행 경계 = 새 `open_run()` 쌍([XRUN-F1 card B C1·C6] -- 옛 블록 객체 reset_stats·stats 는
    없어졌다). 블록 계수 = 이 실행 RunCounters 의 (블록, "*") 행 {이름: 행}.
    [XRUN-F1 card B 규칙 M M-d] 모듈 캐시(env.runs)에 두므로 실행의 두 객체를 쥔 값(StageAResult·탐색 컨텍스트)은 두지 않고, 쓰는 값만 꺼내 둔다:
    상태, 보고서, S0 수준 스냅샷(dc.base -- GraphSnapshot, 두 객체가 아니다), context_fp·schema_fp, 계수 행(불변 값).
    [xrun J-1] run_stage_a 는 선언 값·선언 경로 인자를 받지 않는다."""
    from gmid_engine.search import open_run
    out = env.root / circuit / tag
    donors, counters = open_run()
    a = run_stage_a(LIBRARY / (circuit + ".topology.json"), LIBRARY / (circuit + ".sizing_spec.json"), env.lut, output_dir=out,
                    donors=donors, counters=counters)
    env.memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, env.memo, env.pdk, output_dir=out, diagnostic=True, settings=_settings())
    sctx = _search_context(env, a, b) if (a.status, b.status) == ("ok", "ok") else None
    rows = {r.block: r for r in a.counters.snapshot().blocks if r.part == "*"}       # card B: part 는 늘 "*"
    return SimpleNamespace(status=[a.status, b.status], stats=rows,
                           base=None if sctx is None else sctx.dc.base,
                           context_fp=None if sctx is None else sctx.context_fp,
                           schema_fp=None if sctx is None else sctx.schema_fp,
                           report_a=json.loads(Path(a.report_paths[0]).read_text(encoding="utf-8")),
                           report_b=json.loads(Path(b.report_paths[0]).read_text(encoding="utf-8")),
                           bytes_a=Path(a.report_paths[0]).read_bytes(), bytes_b=Path(b.report_paths[0]).read_bytes())


def _run(env, circuit):
    """회로마다 한 번: 같은 프로세스에서 같은 입력의 사슬 두 번(first, second). 결과는 모듈 캐시."""
    if circuit not in env.runs:
        try:
            env.runs[circuit] = SimpleNamespace(first=_chain(env, circuit, "first"), second=_chain(env, circuit, "second"))
        except Exception as exc:          # test harness: 첫 실패를 저장해 같은 회로의 다른 test 가 같은 원인으로 실패하게 한다(재실행 없음)
            env.runs[circuit] = exc
    if isinstance(env.runs[circuit], Exception):
        raise env.runs[circuit]
    return env.runs[circuit]


def _baseline(circuit):
    """회로의 기준선 항목. 기준선에 없는 회로는 수집 때 KeyError 로 모듈 전체를 죽이지 않고, 그 회로의 test 만 명시적으로 실패한다
    (skip 금지 -- 원칙 10: 기준선이 없으면 이 회로는 회귀 보호가 없다는 사실을 red 로 둔다). 기준선 측정은 별도 판정 몫."""
    assert circuit in BASELINE, "기준선(fixtures/u17_1b_s0_baseline.json)에 회로 %r 없음 -- 회귀 보호 없음(기준선 측정은 별도 판정)" % circuit
    return BASELINE[circuit]


def _searched(circuit):
    return BASELINE.get(circuit, {}).get("status") == ["ok", "ok"]


SEARCHED = [c for c in CIRCUITS if _searched(c)]


def _records(base):
    """S0 수준 스냅샷(메모리)의 레코드 {(kind, key): {field: FieldValue}}."""
    out = {}
    for kind in base.kinds():
        for key in base.keys(kind):
            rec = base.record(kind, key)
            out[(kind, key)] = {name: rec.get(name) for name in rec.field_names()}
    return out


def _s0_writers(base):
    """S0 행 writer 블록 = 탐색 컨텍스트 `dc.base` 의 graph S0 레코드(GRAPH_ROWS 의 key) 필드 writer + 출발 구간 소자 필드 writer."""
    keys = {k for k, _f, _w in GRAPH_ROWS}
    return sorted({fv.writer for (kind, key), fields in _records(base).items() if kind == "graph" and key in keys
                   for fv in fields.values()} | {DEVICE_START[1]})


def _value_fps(base):
    return {(kind, key, name): fv.value_fp for (kind, key), fields in _records(base).items() for name, fv in fields.items()}


# ---------------------------------------------------------------- 1. 필드 존재·writer 유일성 (메모리 S0 수준 스냅샷)

@pytest.mark.parametrize("circuit", SEARCHED)
def test_s0_fields_present_with_single_block_writer(env, circuit):
    run = _run(env, circuit)
    base = run.first.base                        # §2.4.7: KernelContext.base = S0 수준 스냅샷(참조)
    table = {}
    for (kind, field), writer in base.writers.entries:
        assert (kind, field) not in table, "권한표에 같은 (kind, field) 두 번: " + repr((kind, field))
        table[(kind, field)] = writer
    records = _records(base)
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
            row_writers.add(cell.writer)
            if cell.writer != owner:
                problems.append("graph/%s: %s writer %r != 권한표 %r" % (key, field, cell.writer, owner))
            if named is not None and cell.writer != named:
                problems.append("graph/%s: %s writer %r != design %r" % (key, field, cell.writer, named))
        if len(row_writers) > 1:
            problems.append("graph/%s %s: 한 블록이 쓰는 행인데 writer 여럿 %r" % (key, fields, sorted(row_writers)))
        for w in row_writers:
            if w not in base.block_versions or w not in blocks:
                problems.append("writer %r 가 계산 블록이 아니다(block_versions·ComputeBlock)" % w)
    devices = set(_baseline(circuit)["start"]["row_fp"])
    assert devices
    for field in DEVICE_START[0]:
        have = {k for (kind, k), f in records.items() if kind == "device" and field in f}
        if have != devices:
            problems.append("device %s 소자 %r != 기준선 출발 구간 행 %r" % (field, sorted(have), sorted(devices)))
        writers = {f[field].writer for (kind, k), f in records.items() if kind == "device" and field in f}
        if writers - {DEVICE_START[1]} or table.get(("device", field)) != DEVICE_START[1]:
            problems.append("device %s writer %r / 권한표 %r" % (field, sorted(writers), table.get(("device", field))))
    if table.get(("device", DEVICE_SELF_REF[0])) != DEVICE_SELF_REF[1]:
        problems.append("device %s 권한표 writer %r" % (DEVICE_SELF_REF[0], table.get(("device", DEVICE_SELF_REF[0]))))
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 2·3. 실행 안 G-10, 반복 실행도 다시 계산 (XR-1)

def _bad_counts(stats, writers):
    return ["%s computes=%s recomputes_same_input=%s" % (w, getattr(stats.get(w), "computes", None),
                                                        getattr(stats.get(w), "recomputes_same_input", None))
            for w in writers if w not in stats or stats[w].computes != 1 or stats[w].recomputes_same_input != 0]


@pytest.mark.parametrize("circuit", SEARCHED)
def test_cold_run_computes_each_s0_block_once(env, circuit):
    # interface card C4 / §2.4.9 판정 1: 한 실행에서 S0 행 writer 블록마다 computes = 1, recomputes_same_input = 0(소비자는 필드를 읽는다).
    run = _run(env, circuit)
    bad = _bad_counts(run.first.stats, _s0_writers(run.first.base))
    assert not bad, "S0 블록은 실행 하나에서 한 번만 계산된다(소비자는 필드를 읽는다):\n" + "\n".join(bad)


@pytest.mark.parametrize("circuit", SEARCHED)
def test_second_run_computes_each_s0_block_once_again(env, circuit):
    # [xrun XR-1] interface card C3: 같은 입력으로 같은 프로세스에서 두 번째 실행(자기 open_run() 쌍 -- card B C6)도 S0 행 writer 블록마다 computes = 1,
    # recomputes_same_input = 0 -- 앞 실행이 남긴 것으로 계산을 건너뛰지 않는다(옛 '두 번째 실행 = 계산 0' 의 반대, §2.4.9 판정 2 폐지).
    # writer 목록 = 두 번째 실행 dc.base 의 graph S0 레코드 필드 writer(디스크 파일이 아님).
    run = _run(env, circuit)
    writers = _s0_writers(run.second.base)
    assert writers == _s0_writers(run.first.base)
    bad = _bad_counts(run.second.stats, writers)
    assert not bad, "두 번째 실행에서 S0 블록이 계산되지 않았거나 두 번 계산됐다:\n" + "\n".join(bad)


@pytest.mark.parametrize("circuit", SEARCHED)
def test_second_run_outputs_bit_identical(env, circuit):
    # interface card C3: 같은 BLAS 설정이면 두 실행의 단계 A·B 보고서 JSON(바이트), dc.base 필드 value_fp 표, context_fp, schema_fp 가 같다.
    run = _run(env, circuit)
    first, second = run.first, run.second
    assert second.bytes_a == first.bytes_a
    assert second.bytes_b == first.bytes_b
    fa, fb = _value_fps(first.base), _value_fps(second.base)
    assert fa and fb.keys() == fa.keys()
    assert sorted(k for k in fa if fa[k] != fb[k]) == []
    assert (second.context_fp, second.schema_fp) == (first.context_fp, first.schema_fp)


# ---------------------------------------------------------------- 5. 결과 불변 (기준선)

def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")).hexdigest()


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_baseline_present_for_every_library_circuit(env, circuit):
    """library 회로마다 기준선 항목이 있다(O-181: 새 4회로는 기준선이 아직 없어 이 test 가 red -- 측정은 별도 판정 몫).
    [O-227 (2)] 단계 B 가 정지하는 회로(cnr_ota·erfc_ota)는 기준선을 만들지 않고 정지 사유 고정(o227_stop_pin, 임시)으로 xfail 한다 --
    기준선 항목이 생기면 고정이 실패해 지우게 한다."""
    if o227_stop_pin.is_stop_pinned(circuit):
        o227_stop_pin.pin_stop("test_baseline_present_for_every_library_circuit[%s]" % circuit, circuit, _run(env, circuit).first.report_b,
                               _run(env, circuit).first.report_b["achievability"] is None)
    assert _baseline(circuit)["status"]


def test_baseline_lookup_fails_closed_for_unknown_circuit():
    """기준선에 없는 이름은 KeyError 가 아니라 설명 있는 AssertionError 로 거부된다(skip·기본값으로 넘기지 않는다)."""
    with pytest.raises(AssertionError, match="기준선"):
        _baseline("no_such_circuit_in_baseline")
    assert not _searched("no_such_circuit_in_baseline")


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_stage_reports_unchanged_from_base(env, circuit):
    if o227_stop_pin.is_stop_pinned(circuit):        # [O-227 (2)] 정지 회로: 기준선 없이 정지 사유 고정(임시), 기준선이 생기면 실패
        rep_b = _run(env, circuit).first.report_b
        o227_stop_pin.pin_stop("test_stage_reports_unchanged_from_base[%s]" % circuit, circuit, rep_b, rep_b["achievability"] is None)
    want = _baseline(circuit)            # 기준선 없으면 실행 전에 이 회로만 실패
    run = _run(env, circuit)
    assert run.first.status == want["status"]
    diff = [k for k, sha in want["stage_a_sha"].items() if _sha(run.first.report_a.get(k)) != sha]
    diff += ["stage_b." + k for k, sha in want["stage_b_sha"].items() if _sha(run.first.report_b.get(k)) != sha]
    ach = run.first.report_b.get("achievability") or {}
    diff += ["stage_b.achievability." + k for k, sha in want["achievability_sha"].items() if _sha(ach.get(k)) != sha]
    assert not diff, "base 와 다른 보고서 키: %r" % diff


@pytest.mark.parametrize("circuit", SEARCHED)
def test_s0_field_values_unchanged_from_base(env, circuit):
    run = _run(env, circuit)
    base = run.first.base
    want = _baseline(circuit)
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
                                 "search_domain_fp": ("kernel", "search_domain"),
                                 "mismatch_source_fp": ("kernel", "mismatch_source"), "passive_area_decl_fp": ("kernel", "passive_area_decl"),
                                 "model_error_fp": ("kernel", "model_error"), "metric_structure_fp": ("s1v", "metric_structure"),
                                 "noise_input_cells_fp": ("s1v", "noise_input_cells")}.items():
        if key not in want["kernel"]:
            continue                                   # 기준선에서 지문을 못 낸 값 형식(픽스처 *_fp_error 칸) -- 보고서 대조가 덮는다
        got = base.field("graph", record, field)
        if got is None or got.value_fp != want["kernel"][key]:
            diff.append("graph/%s: %s" % (record, field))
    assert not diff, "base 와 다른 S0 필드 값: %r" % diff


# ---------------------------------------------------------------- 6. junction_source
# [U17 ①-b 판정 후] graph/kernel: junction_source 는 전체 지문이 아니라 내용으로 대조한다(옛 값의 LUT 규칙 PdkDecl 이 checkout 절대 경로를 담아
# 지문이 경로마다 달랐다). oracle: params(core fp_of)·temp_c = base 9255a22 코드로 잰 기준선(c) `kernel.junction_content`,
# pdk_decl_sha256 = 이 test 가 PDK 선언 파일 바이트를 직접 해시한 값(a, metrics CONTRACT 'pdk_decl_sha256 = PDK 선언 파일 sha256').

def _strings(node, seen=None):
    """값 안의 모든 문자열(dataclass 칸·tuple·list·frozenset·dict 키와 값을 따라 내려간다)."""
    seen = set() if seen is None else seen
    if isinstance(node, str):
        yield node
        return
    if id(node) in seen or isinstance(node, (bytes, int, float, bool, type(None))):
        return
    seen.add(id(node))
    if dataclasses.is_dataclass(node) and not isinstance(node, type):
        for f in dataclasses.fields(node):
            yield from _strings(getattr(node, f.name), seen)
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(k, seen)
            yield from _strings(v, seen)
    elif isinstance(node, (tuple, list, frozenset, set)):
        for v in node:
            yield from _strings(v, seen)


@pytest.mark.parametrize("circuit", SEARCHED)
def test_junction_source_content_unchanged_from_base(env, circuit):
    run = _run(env, circuit)
    got = run.first.base.field("graph", "kernel", "junction_source")
    assert got is not None
    want = _baseline(circuit)["kernel"]["junction_content"]
    js = got.value
    assert fp_of(js.params) == want["params_fp"]
    assert float(js.temp_c).hex() == want["temp_c_hex"]
    pdk_sha = hashlib.sha256((SKILL / "assets" / "sky130_pdk_decl.json").read_bytes()).hexdigest()
    assert js.pdk_decl_sha256 == pdk_sha == want["pdk_decl_sha256"]


@pytest.mark.parametrize("circuit", SEARCHED)
def test_junction_source_value_has_no_checkout_path(env, circuit):
    # [xrun] 옛: 디스크 S0 파일의 junction_source 칸 문자열. 지금: 메모리 값(dc.base 필드) 안 문자열 어디에도 이 checkout 의 저장소 경로가 없다.
    run = _run(env, circuit)
    got = run.first.base.field("graph", "kernel", "junction_source")
    assert got is not None
    strings = list(_strings(got.value))
    assert strings, "junction_source 값에서 문자열을 하나도 못 찾았다(검사가 공허)"
    root = str(SKILL.parents[1]).replace("\\", "/").lower()
    hits = [s for s in strings if root in s.replace("\\", "/").lower()]
    assert not hits, "junction_source 값에 checkout 경로: %r" % hits[:5]
