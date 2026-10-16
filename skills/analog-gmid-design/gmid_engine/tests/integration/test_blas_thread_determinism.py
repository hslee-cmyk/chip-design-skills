"""[NFR-4 card 2, N-T29] BLAS 스레드 수 결정성 -- 9 library 회로, 바깥 OPENBLAS_NUM_THREADS 1 대 max(2, cpu) (interface card nfr4c2 C1·C3·C6·C7,
설계 40 §2.4.13 (5) '실행 하네스와 9회로 test 실행 방식', 사용자 결정 N-2·N-2 정정).

[NFR-4 card 2] 다시 썼다(3.2 표): 옛 docstring·`CODE`(출발 구간 지문만)·병렬 `_launch`(Popen 둘 동시)·예상 실패 표시를 지웠다. 엔진이 import 때 BLAS
스레드를 1 로 고정하므로(C1) 바깥 스레드 설정은 결과를 바꾸지 않아야 하고, 이 test 는 그것을 통과 조건으로 단언한다(설계 40 §2.4.13 (5)
'승인 불필요: 예상 실패 표시 제거·범위 확장(기준 강화)').

무엇을 보나(회로마다): 하네스 `nfr4_run_dump.py` 를 새 프로세스로 둘 -- 바깥 스레드 1, max(2, cpu) -- **순차**로 돌려(subprocess.run, 병렬 금지)
실행 기록을 받고,
- 두 실행의 `env_fp`(단계 A 보고서·S3 runs 줄 기록)가 같다(엔진 고정 -> 같은 실행 환경),
- 비교기 `nfr4_compare.first_pass`(같은 환경 1차 검사): 비트 동일 집합(S0 수준 필드 지문, 단계 A·B 보고서, 층 0 결과, 탐색 결과, 평가 캐시, S3 줄 --
  T 시간 칸만 뺌)이 같고(diffs 빈 목록), 판정 불능 0, PASS.
- `test_single_thread_start_fp_matches_base`(유지): 스레드 1 실행의 two_stage_ota 출발 구간 S0 필드 값 지문 = 기준선
  (`fixtures/u17_1b_s0_baseline.json`, oracle (c) 독립 기준선 파일 -- test_s0_layer_9circuits 와 같은 기준선).
oracle: (비교) 같은 하네스의 두 실행 출력을 맞댄다, (독립) 기준선 파일. 모든 test 는 예상 실패 표시 없이 통과해야 한다.
실행 방식(C7): 환경 = 허용 목록 dict(PATH·SYSTEMROOT·APPDATA·TEMP/TMP·GMID_LUT_TABLE_CACHE_DIR·PYTHONDONTWRITEBYTECODE·PYTHONIOENCODING
+ 바깥 OPENBLAS_NUM_THREADS + LUT·PDK 데이터 위치 변수(있으면)), TEMP 와 표 캐시는 회로마다 한 경로를 실행마다 비워서 쓴다(빈 폴더 -- 경로 문자열이 실행
사이에 같아 S0 값 지문에 경로 차이가 끼지 않는다), 실행마다 별도 작업 폴더(S3·보고서), E_B 40 선언, front_budget_s 7200 s, 회로마다 기록 파일.
비용: 9회로 × 2 실행 ≈ 1,800 s(설계 40 측정). 파일 전체 `slow`(`--run-slow` 일 때만 실행, C6). 다른 9회로 test 와 동시에 돌리지 않는다.
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

pytestmark = pytest.mark.slow

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[2]
LIBRARY = SKILL / "assets" / "library"
CIRCUITS = sorted(p.name.removesuffix(".topology.json") for p in LIBRARY.glob("*.topology.json") if not p.name.startswith("_"))
BASELINE = json.loads((HERE / "fixtures" / "u17_1b_s0_baseline.json").read_text(encoding="utf-8"))
DUMP = HERE / "nfr4_run_dump.py"
MANY = str(max(2, os.cpu_count() or 2))
PASS_THROUGH = ("PATH", "SYSTEMROOT", "APPDATA", "GMID_LUT_V2_ROOT", "GMID_PDK_ROOT")
CIRCUIT_FP = "two_stage_ota"
START_FIELDS = ("rungs", "conflicts", "inactive", "macro", "records", "area_est_m2", "area_fraction", "uncovered")
BASE_KEYS = {"rungs": "ladder_fp", "conflicts": "conflicts_fp", "inactive": "inactive_fp", "macro": "macro_fp", "records": "records_fp",
             "area_est_m2": "area_est_m2_fp", "area_fraction": "area_fraction_fp", "uncovered": "uncovered_fp"}

sys.path.insert(0, str(HERE))
import nfr4_compare as N  # noqa: E402


def _fresh(path):
    shutil.rmtree(path, ignore_errors=True)
    Path(path).mkdir(parents=True)
    return path


class _Runs:
    """회로마다 (스레드 1, MANY) 두 실행 기록 -- 순차, 결과는 모듈 캐시(같은 회로의 두 test 가 다시 돌리지 않는다)."""

    def __init__(self, root):
        self.root = Path(root)
        self.done = {}
        shared = os.environ["GMID_LUT_TABLE_CACHE_DIR"]                     # conftest 가 고정한 test 캐시(경로 길이 60자 미만 규칙)
        self.cache = tempfile.mkdtemp(prefix="n4c_", dir=os.path.dirname(shared))
        assert len(self.cache) < 60, self.cache
        self.tmp = tempfile.mkdtemp(prefix="n4t_", dir=os.environ.get("TEMP") or None)

    def get(self, circuit):
        if circuit not in self.done:
            out = {}
            for threads in ("1", MANY):
                work = _fresh(self.root / ("%s_%s" % (circuit, threads)))
                rec_path = self.root / ("%s_%s.json" % (circuit, threads))
                env = {k: os.environ[k] for k in PASS_THROUGH if k in os.environ}
                env.update(TEMP=_fresh(self.tmp), TMP=self.tmp, GMID_LUT_TABLE_CACHE_DIR=_fresh(self.cache),
                           PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS=threads)
                proc = subprocess.run([sys.executable, "-P", str(DUMP), circuit, str(rec_path), str(work), "--eval-budget", "40",
                                       "--front-budget-s", "7200"], cwd=str(work), env=env, capture_output=True, text=True,
                                      encoding="utf-8", errors="replace", timeout=7200)
                assert proc.returncode == 0, "%s threads=%s 실패:\n%s" % (circuit, threads, proc.stderr[-4000:])
                out[threads] = N.load_record(str(rec_path))
                assert out[threads]["threads_env"] == threads
            self.done[circuit] = out
        return self.done[circuit]

    def close(self):
        shutil.rmtree(self.cache, ignore_errors=True)
        shutil.rmtree(self.tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    r = _Runs(tmp_path_factory.mktemp("nfr4"))
    yield r
    r.close()


@pytest.mark.parametrize("circuit", CIRCUITS)
def test_blas_thread_count_does_not_change_run(runs, circuit):
    one, many = runs.get(circuit)["1"], runs.get(circuit)[MANY]
    rep = N.first_pass(one, many)                                         # env_fp·code_fp 가 다르면 ValueError(같은 환경 전제)
    report_path = runs.root / ("%s_report.json" % circuit)
    N.write_report(rep, str(report_path))
    assert rep["diffs"] == [], (circuit, rep["diffs"][:40], str(report_path))   # 비트 동일 집합 전체가 같다
    assert N.env_of(one) is not None and N.env_of(one) == N.env_of(many), (one["env_fp"], many["env_fp"])
    assert rep["preconditions"] == {"base": [], "other": []}, rep["preconditions"]
    assert rep["undecidable"] == 0 and rep["verdict"] == "PASS", (rep["verdict"], str(report_path))


def test_single_thread_start_fp_matches_base(runs):
    # oracle (c): base 기준선(fixtures/u17_1b_s0_baseline.json) -- 스레드 1 실행의 출발 구간 S0 필드 값 지문(value_fp)이 기준선과 같다.
    # [library spec card 2026-10-14, U-3] two_stage_ota 항목은 Q-S2 spec 변경 뒤 base 41a2c4a 코드로 재측정한 값(test_s0_layer_9circuits 와 같은 기준선).
    # [NFR-4 card 2] 하네스 기록의 S0 칸(`s0/<kind>/<key>/<field>`, 값 = value_fp)에서 읽는다(옛 CODE 의 dc.base.field(...).value_fp 와 같은 값).
    rec = runs.get(CIRCUIT_FP)["1"]
    f = rec["fields"]
    want = BASELINE[CIRCUIT_FP]["start"]
    got = {"device/%s: start.row" % d: f.get("s0/device/%s/start.row" % d, {}).get("value") for d in want["row_fp"]}
    got.update({"graph/start: " + k: f.get("s0/graph/start/" + k, {}).get("value") for k in START_FIELDS})
    exp = {"device/%s: start.row" % d: fp for d, fp in want["row_fp"].items()}
    exp.update({"graph/start: " + k: want[BASE_KEYS[k]] for k in START_FIELDS})
    assert got == exp
