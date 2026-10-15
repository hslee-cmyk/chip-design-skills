"""[xrun XR-5] 실행 결과가 S3 폴더의 이전 내용과 무관하다 -- interface card C3·C5(설계 40 v1.10 §2.4.3 'S3' 행: 엔진은 S3 evals·runs 를
실행 사이에 읽지 않는다, 사용자 결정 2026-10-15 "나로 해" + U-89).

같은 프로세스에서 같은 입력(library 회로 하나 -- 기준선 status [ok, ok] 회로, 단계 A -> B -> 커널 컨텍스트 -> 탐색 컨텍스트 -> find_front, 선언 평가
예산)으로 사슬을 세 번 돈다. 실행마다 블록 계수를 reset_stats() 로 비우고(실행 경계, C4) LUT memo 를 새로 만든다.
- 실행 A: 빈 S3 루트.
- 실행 B: A 가 쓴 S3 폴더 그대로(A 의 front 점·평가 줄이 있다).
- 실행 C: 새 S3 루트에 A 의 평가 줄을 모두 실패 줄로 바꿔 손으로 넣은 폴더(옛 '디스크 실패 적중' 입력 형식,
  tests/search/test_kernel.py `_as_failure_line` 과 같은 구성).
oracle (a) 불변식(C3·C5): 세 실행의 C3 출력 -- 단계 A·B 보고서 JSON 바이트, dc.base 필드 value_fp 표, context_fp, schema_fp, find_front 결과
(front·pending·unmeasured 점 θ 의 float.hex, 시간 칸을 뺀 perf), 그 실행이 S3 에 새로 붙인 줄(evals 줄 전부, runs 줄은 perf 시간 칸
`wall_s`·`eval_time_median_s` 를 뺀 내용, 이 줄의 failed_eps 포함) -- 이 모두 같다. 기대값은 A 의 출력이다(피검 함수로 정답을 만들지 않고, 같은
함수의 세 출력이 같은지만 본다). 시간 예산은 넉넉히(600 s) 주고 벽시계 정지 0 을 전제로 단언한다.
실 LUT 데이터가 없으면 FAIL(skip 아님).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmid_engine.core import BoundedLRU, ComputeBlock, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
CIRCUIT = "common_gate_amplifier"          # 기준선 fixtures/u17_1b_s0_baseline.json 의 status = [ok, ok] 회로 가운데 하나(가장 짧은 사슬)
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
EVAL_BUDGET = 20                           # 선언 평가 예산(C3: 선언하지 않으면 벽시계로 유도되어 비결정) -- 입력 선택
TIME_FIELDS = ("wall_s", "eval_time_median_s")   # C3 '시간 칸(비교에서 뺀다)'


def _settings():
    from gmid_engine.search import SearchSettings
    return SearchSettings(600.0, EVAL_BUDGET, (1e2, 1e5), (("front_budget_s", "xrun XR-5 fixture"),), (1e-13, 1e-10))


@pytest.fixture(scope="module")
def env():
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
    return SimpleNamespace(lut=lut, pdk=pdk, rule=read_pdk_decl(str(SKILL / "assets" / "sky130_lut_rule_decl.json"), dm))


def _reset_blocks():
    for name, mod in list(sys.modules.items()):
        if name.startswith("gmid_engine.") and ".tests" not in name and mod is not None:
            for value in list(vars(mod).values()):
                if isinstance(value, ComputeBlock):
                    value.reset_stats()


def _jsonl(p):
    p = Path(p)
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.is_file() else []


def _value_fps(base):
    out = {}
    for kind in base.kinds():
        for key in base.keys(kind):
            rec = base.record(kind, key)
            for name in rec.field_names():
                out[(kind, key, name)] = rec.get(name).value_fp
    return out


def _no_time(perf):
    return {k: v for k, v in dict(perf).items() if k not in TIME_FIELDS}


def _points(seq):
    return [[p.point_id, [[list(k) if isinstance(k, tuple) else k, float(v).hex()] for k, v in p.result.theta]] for p in seq]


def _chain(env, out, archive_root):
    """단계 A -> B -> 커널 컨텍스트 -> 탐색 컨텍스트(archive_root) -> find_front(given 없음). -> C3 출력 묶음."""
    from gmid_engine.search import build_search_context, find_front
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    _reset_blocks()
    a = run_stage_a(LIBRARY / (CIRCUIT + ".topology.json"), LIBRARY / (CIRCUIT + ".sizing_spec.json"), env.lut, output_dir=out)
    memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
    b = run_stage_b(a, memo, env.pdk, output_dir=out, diagnostic=True, settings=_settings())
    assert (a.status, b.status) == ("ok", "ok"), (a.status, b.status)
    kctx = build_kernel_context(b.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo))
    sctx = build_search_context(kctx, a.spec, _settings(), str(archive_root), env.pdk, env.rule, code_fp=a.code_fp)
    d = Path(archive_root) / sctx.context_fp
    n_evals, n_runs = len(_jsonl(d / "evals.jsonl")), len(_jsonl(d / "runs.jsonl"))
    fr = find_front(sctx, [])
    new_evals = _jsonl(d / "evals.jsonl")[n_evals:]
    new_runs = [dict(r, perf=_no_time(r["perf"])) for r in _jsonl(d / "runs.jsonl")[n_runs:]]
    return SimpleNamespace(
        dir=d, perf_raw=dict(fr.perf),
        out={"report_a": Path(a.report_paths[0]).read_bytes(), "report_b": Path(b.report_paths[0]).read_bytes(),
             "value_fps": _value_fps(sctx.dc.base), "context_fp": sctx.context_fp, "schema_fp": sctx.schema_fp,
             "front": _points(fr.front), "pending": _points(fr.pending_front), "unmeasured": _points(fr.unmeasured_front),
             "perf": _no_time(fr.perf), "new_evals": new_evals, "new_runs": new_runs})


def _as_failure(line):
    from gmid_engine.search import STATUS_FAILED
    d = {k: v for k, v in line.items() if k not in ("objectives", "power_resolution_w", "snapshot_fp")}
    d.update(ok=False, status=STATUS_FAILED, constraints=[], unmeasured=[],
             fail={"class": "SEAL_VIOLATION", "devices": [], "margin": None,
                   "detail": {"reason": "empty_window", "node": "out", "lo": 1.8, "hi": 0.0, "item": 7, "constraints": 3}})
    return d


@pytest.fixture(scope="module")
def runs(env, tmp_path_factory):
    import shutil
    import tempfile
    roots = [tempfile.mkdtemp(prefix="xr5", dir=os.environ.get("TEMP") or None) for _ in range(2)]   # 짧은 경로(지문 64자 + 파일 이름)
    try:
        work = tmp_path_factory.mktemp("xr5")
        ra = _chain(env, work / "a", roots[0])
        rb = _chain(env, work / "b", roots[0])                   # A 가 남긴 S3 폴더 위
        failed = [_as_failure(x) for x in _jsonl(ra.dir / "evals.jsonl") if x.get("ok")]
        cdir = Path(roots[1]) / ra.dir.name
        cdir.mkdir(parents=True)
        (cdir / "evals.jsonl").write_text("".join(json.dumps(x) + "\n" for x in failed), encoding="utf-8")
        rc = _chain(env, work / "c", roots[1])                   # 손으로 넣은 실패 줄 위
        yield SimpleNamespace(a=ra, b=rb, c=rc, n_failed=len(failed))
    finally:
        for r in roots:
            shutil.rmtree(r, ignore_errors=True)


def test_preconditions(runs):
    # 전제: A 가 S3 에 평가 줄·front 를 남겼고(B 가 읽을 거리가 있다), C 의 폴더에 실패 줄이 있고, 벽시계 정지 0(C3 결정성 전제).
    assert runs.a.out["new_evals"] and runs.a.out["new_runs"] and runs.n_failed >= 1
    assert runs.a.out["front"] or runs.a.out["pending"]
    assert runs.b.dir == runs.a.dir and runs.c.dir.name == runs.a.dir.name
    for r in (runs.a, runs.b, runs.c):
        assert r.perf_raw["stops_wall_budget"] == 0 and r.perf_raw["eval_budget_source"] == "declared"


@pytest.mark.parametrize("which", ["b", "c"], ids=["s3_with_previous_run", "s3_with_hand_failures"])
def test_outputs_independent_of_previous_s3_content(runs, which):
    a, other = runs.a.out, getattr(runs, which).out
    diff = sorted(k for k in a if a[k] != other[k])
    assert not diff, "빈 S3 실행 A 와 다른 C3 출력(%s): %r" % (which, diff)
