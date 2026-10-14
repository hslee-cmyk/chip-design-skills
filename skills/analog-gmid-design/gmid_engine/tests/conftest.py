"""gmid_engine test 경로 설정 -- editable 설치 없이 skills/analog-gmid-design 을 sys.path 앞에 둬 `import gmid_engine` 이 되게 한다.

[2026-10-08 오케스트레이터 결정] test 세션은 사용자의 실제 파생 표 캐시 폴더(lut/CONTRACT.md 2.1, 설정
`assets/lut_v2_location.json` 의 `table_cache.default`)에 쓰거나 그곳에서 정리(삭제)를 돌리지 않는다. 그래서 이 conftest 가
세션 전체에 `GMID_LUT_TABLE_CACHE_DIR` 을 전용 test 캐시 폴더로 고정한다(하위 프로세스·spawn 도 os.environ 을 물려받는다).
- 폴더 = 실제 default 의 부모 + 고정 접미사 `_TEST_CACHE_DIRNAME`(예: .../fpga/lut_table_cache_tests). 저장소 밖, 실제 캐시 밖,
  세션 사이에 남아 프로세스 간 캐시 이득은 유지된다.
- 경로는 60자 미만이어야 한다(칸 파일 이름 약 150자 + 임시 접미사 -> Windows MAX_PATH 260). 넘으면 즉시 실패(조용한 write_error 방지).
- 임시 캐시가 필요한 test 는 자기 폴더를 따로 쓴다(test_table_cache.py 등).
"""
import json
import os
import shutil
import sys
import tempfile

# [U17 ①-b 2차, 사용자 결정 8(2026-10-14)] 판정 환경 OpenBLAS 스레드 수 1 고정 -- NFR-4 결정론 결함 우회, 엔진 원인 수정은 U17 ② 착수 전
# (wt/_drafts/engine/U17_FOLLOWUPS.md 2026-10-14 항목: 미지정 시 two_stage_ota·two_stage_ota_sf·sf_pushpull 의 start.row·rungs·macro·
# area_est_m2 지문이 비트 단위로 달라진다). 이 고정은 결함을 고친 것이 아니다 -- 결함 자체는
# tests/integration/test_blas_thread_determinism.py 의 xfail(strict) test 가 계속 드러내고, 엔진이 고쳐지면 XPASS(=FAIL)로 알린다.
# 판정 재현성을 위해 바깥 환경 값을 존중하지 않고 1 로 강제한다(하위 프로세스도 물려받는다). numpy 가 이미 import 됐으면 OpenBLAS 가
# 스레드 수를 이미 정해 고정이 듣지 않으므로 조용히 넘어가지 않고 멈춘다.
_BLAS_THREAD_ENV = ("OPENBLAS_NUM_THREADS",)
if "numpy" in sys.modules:
    raise RuntimeError("numpy 가 gmid_engine tests conftest 보다 먼저 import 됐다 -- OPENBLAS_NUM_THREADS=1 고정이 듣지 않는다")
for _name in _BLAS_THREAD_ENV:
    os.environ[_name] = "1"

# tests -> gmid_engine -> analog-gmid-design(패키지 부모)
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _SKILL_DIR not in sys.path:
    sys.path.insert(0, _SKILL_DIR)

_LOCATION_CONFIG = os.path.join(_SKILL_DIR, "assets", "lut_v2_location.json")
_TEST_CACHE_DIRNAME = "lut_table_cache_tests"      # 실제 캐시 폴더 옆 test 전용 폴더 이름(고정 접미사)
_TEST_CACHE_MAX_LEN = 60                           # 오케스트레이터 결정: MAX_PATH 여유(위 docstring)


def _isolate_table_cache():
    with open(_LOCATION_CONFIG, encoding="utf-8") as f:
        entry = json.load(f)["table_cache"]
    real = os.path.normcase(os.path.abspath(entry["default"]))
    test_dir = os.path.join(os.path.dirname(os.path.abspath(entry["default"])), _TEST_CACHE_DIRNAME)
    if os.path.normcase(test_dir) == real or len(test_dir) >= _TEST_CACHE_MAX_LEN:
        raise RuntimeError("test 캐시 폴더가 실제 캐시와 같거나 너무 길다: %s" % test_dir)
    os.environ[entry["env"]] = test_dir


_isolate_table_cache()


# [U17 ①-a] S0 수준 스냅샷(core.snapshot_codec, 설계 40 §2.4.3): test 세션은 실제 `gmid_engine/.s0_snapshot` 에 쓰지 않고 그곳의 정리(U-68)도
# 돌리지 않는다 -- 세션마다 새 임시 폴더를 `GMID_S0_SNAPSHOT_DIR` 로 고정한다(하위 프로세스도 물려받는다). 세션 사이에 남기지 않는다:
# library 회로처럼 저장소 안 입력 파일의 키는 세션을 넘어 적중해 첫 실행의 블록 계수를 보는 test 결과가 저장소 상태에 따라 바뀐다.
# 기본 위치 자체는 tests/core/test_snapshot_codec.py 가 환경 변수를 지운 상태로 본다.
_S0_ENV = "GMID_S0_SNAPSHOT_DIR"
_S0_DIR = tempfile.mkdtemp(prefix="gmid_s0_tests_")
os.environ[_S0_ENV] = _S0_DIR


def pytest_unconfigure(config):
    shutil.rmtree(_S0_DIR, ignore_errors=True)
