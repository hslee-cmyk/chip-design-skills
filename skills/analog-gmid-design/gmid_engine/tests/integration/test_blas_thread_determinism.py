"""[U17 ①-b 2차] BLAS 스레드 수 결정론(NFR-4) -- 판정 환경의 OPENBLAS_NUM_THREADS=1 고정(tests/conftest.py)이 덮는 엔진 결함을 드러낸다.

근거: 사용자 결정 8(2026-10-14, wt/_drafts/user_decisions.md 'U17 1-b 병합 전 3~9') '판정 환경 OpenBLAS 스레드 1 고정 + 엔진 결정론 원인 수정은
② 착수 전', wt/_drafts/engine/U17_FOLLOWUPS.md 2026-10-14 항목(미지정 시 two_stage_ota·two_stage_ota_sf·sf_pushpull 의 start.row·rungs·macro·
area_est_m2 지문이 비트 단위로 다르다, 1 고정 시 일치).

무엇을 보나: two_stage_ota 의 출발 구간 S0 필드(`device: start.row` 소자마다 + `graph/start` 8 필드)의 값 지문(value_fp)을 BLAS 스레드 수만
다르게 한 별도 프로세스 둘(1 과 max(2, cpu 수))에서 잰다. 두 프로세스는 각자 빈 S0 폴더·빈 표 캐시 폴더를 써서 서로의 결과를 읽지 않는다.
- `test_single_thread_start_fp_matches_base` (정상 test): 스레드 1 프로세스의 지문 = base 기준선(oracle (c),
  `fixtures/u17_1b_s0_baseline.json` -- base master a5d8ccb 코드로 측정, test_s0_layer_9circuits 와 같은 기준선). 고정이 기준선을 재현함을 본다.
- `test_start_fp_independent_of_blas_thread_count` (xfail strict): 두 프로세스의 지문이 같다(oracle (a) 불변식 NFR-4 '같은 입력 -> 같은
  결과' -- 스레드 수는 입력이 아니다). 지금은 결함으로 다르다(xfail). 엔진 원인이 고쳐지면 XPASS 가 strict 라 FAIL 로 보고된다 -- 그때 이 xfail
  표시와 conftest 의 고정을 같이 거둔다(U17 ②).
실행 비용: 회로 하나의 단계 A -> B -> 탐색 컨텍스트를 두 프로세스로 병렬 실행(LUT 적재 포함).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parents[1]
SKILL = TESTS.parents[1]
CIRCUIT = "two_stage_ota"
START_FIELDS = ("rungs", "conflicts", "inactive", "macro", "records", "area_est_m2", "area_fraction", "uncovered")
BASE_KEYS = {"rungs": "ladder_fp", "conflicts": "conflicts_fp", "inactive": "inactive_fp", "macro": "macro_fp", "records": "records_fp",
             "area_est_m2": "area_est_m2_fp", "area_fraction": "area_fraction_fp", "uncovered": "uncovered_fp"}
BASELINE = json.loads((Path(__file__).resolve().parent / "fixtures" / "u17_1b_s0_baseline.json").read_text(encoding="utf-8"))
MANY = str(max(2, os.cpu_count() or 2))

# 입력 생성만(기대값을 만들지 않는다): test_s0_layer_9circuits 의 env·_settings·_search_context 와 같은 실행 사슬을 별도 프로세스에서 돈다.
CODE = r"""
import ctypes, glob, json, os, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, {tests!r})
sys.path.insert(0, {skill!r})
import numpy
from integration import test_s0_layer_9circuits as M
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b


def blas_threads():
    libs = glob.glob(os.path.join(os.path.dirname(numpy.__file__) + ".libs", "*openblas*"))
    for path in libs:
        lib = ctypes.CDLL(path)
        for name in ("scipy_openblas_get_num_threads64_", "openblas_get_num_threads64_", "openblas_get_num_threads"):
            fn = getattr(lib, name, None)
            if fn is not None:
                return int(fn())
    return None


loc = resolve_lut_location(str(M.SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(M.DEVICE_KINDS)
mins = {{}}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(M.SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), M.DEVICE_KINDS, M.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
env = SimpleNamespace(lut=lut, pdk=pdk, rule=read_pdk_decl(str(M.SKILL / "assets" / "sky130_lut_rule_decl.json"), dm))
out = Path({out!r})
a = run_stage_a(M.LIBRARY / ({circuit!r} + ".topology.json"), M.LIBRARY / ({circuit!r} + ".sizing_spec.json"), env.lut, pdk_decl=env.pdk,
                lut_rule_decl=env.rule, output_dir=out)
env.memo = LutMemo(env.lut, point=1 << 16, curve=1 << 14, root=1 << 16)
b = run_stage_b(a, env.memo, env.pdk, output_dir=out, diagnostic=True, settings=M._settings())
assert (a.status, b.status) == ("ok", "ok"), (a.status, b.status)
base = M._search_context(env, a, b).dc.base
fps = {{}}
for device in sorted(M.BASELINE[{circuit!r}]["start"]["row_fp"]):
    cell = base.field("device", device, "start.row")
    fps["device/" + device + ": start.row"] = None if cell is None else cell.value_fp
for field in {fields!r}:
    cell = base.field("graph", "start", field)
    fps["graph/start: " + field] = None if cell is None else cell.value_fp
print("@@" + json.dumps({{"env": os.environ.get("OPENBLAS_NUM_THREADS"), "blas_threads": blas_threads(), "fps": fps}}))
"""


def _launch(threads, work):
    s0 = work / "s0"
    out = work / "out"
    s0.mkdir(parents=True)
    out.mkdir(parents=True)
    # 표 캐시: 프로세스마다 빈 폴더(다른 스레드 수의 계산 결과를 읽거나 세션 공용 test 캐시를 오염시키지 않게). conftest 의 MAX_PATH 제약(60자 미만)
    # 때문에 세션 test 캐시 폴더의 부모(저장소 밖)에 짧은 이름으로 만든다.
    shared = os.environ["GMID_LUT_TABLE_CACHE_DIR"]
    cache = tempfile.mkdtemp(prefix="ltc_b%s_" % threads, dir=os.path.dirname(shared))
    assert len(cache) < 60, cache
    env = dict(os.environ, OPENBLAS_NUM_THREADS=threads, GMID_S0_SNAPSHOT_DIR=str(s0), GMID_LUT_TABLE_CACHE_DIR=cache,
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    code = CODE.format(tests=str(TESTS), skill=str(SKILL), out=str(out), circuit=CIRCUIT, fields=START_FIELDS)
    proc = subprocess.Popen([sys.executable, "-P", "-c", code], cwd=str(SKILL), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8")
    return proc, cache


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """스레드 1·MANY 두 프로세스를 병렬로 돌린 결과 {스레드 수 문자열: fps}. 실행 실패·스레드 설정 미적용은 setup 오류(xfail 로 숨지 않는다)."""
    started = {t: _launch(t, tmp_path_factory.mktemp("blas_%s" % t)) for t in ("1", MANY)}
    result = {}
    try:
        for t, (proc, _cache) in started.items():
            stdout, stderr = proc.communicate(timeout=3600)
            assert proc.returncode == 0, "threads=%s 실패:\n%s" % (t, stderr[-4000:])
            lines = [ln for ln in stdout.splitlines() if ln.startswith("@@")]
            assert len(lines) == 1, stdout[-2000:]
            got = json.loads(lines[0][2:])
            assert got["env"] == t
            assert got["blas_threads"] in (None, int(t)), got["blas_threads"]   # 조회 가능하면 실제 OpenBLAS 스레드 수 = 요청
            assert got["fps"] and all(v is not None for v in got["fps"].values()), got["fps"]
            result[t] = got["fps"]
    finally:
        for proc, cache in started.values():
            if proc.poll() is None:
                proc.kill()
                proc.communicate()
            shutil.rmtree(cache, ignore_errors=True)
    return result


def test_single_thread_start_fp_matches_base(runs):
    # oracle (c): base 기준선(fixtures/u17_1b_s0_baseline.json, base master a5d8ccb 측정) -- 스레드 1 고정이 기준선을 재현한다
    want = BASELINE[CIRCUIT]["start"]
    exp = {"device/%s: start.row" % d: fp for d, fp in want["row_fp"].items()}
    exp.update({"graph/start: " + f: want[BASE_KEYS[f]] for f in START_FIELDS})
    assert runs["1"] == exp


@pytest.mark.xfail(strict=True, raises=AssertionError,
                   reason="NFR-4 결함(U17_FOLLOWUPS 2026-10-14): BLAS 스레드 수에 따라 출발 구간 지문이 달라진다 -- 엔진 원인 수정은 U17 ② 착수 전. "
                          "XPASS 면 엔진이 고쳐진 것: 이 xfail 과 tests/conftest.py 의 OPENBLAS_NUM_THREADS 고정을 함께 거둔다")
def test_start_fp_independent_of_blas_thread_count(runs):
    # oracle (a) 불변식 NFR-4: 같은 입력 -> 같은 결과(스레드 수는 입력이 아니다)
    diff = sorted(k for k in runs["1"] if runs["1"][k] != runs[MANY].get(k))
    assert runs["1"].keys() == runs[MANY].keys()
    assert not diff, "BLAS 스레드 1 대 %s 에서 다른 출발 구간 필드: %r" % (MANY, diff)
