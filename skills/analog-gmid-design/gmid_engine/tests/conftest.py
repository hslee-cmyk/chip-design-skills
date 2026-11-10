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
import sys

# [NFR-4 card 2, interface card 3.2] 이 conftest 는 BLAS 스레드 환경 변수를 정하지 않는다(numpy 선행 import 도 거부하지 않는다) -- BLAS 스레드 고정은
# 엔진이 import 때 한다(interface card C1 `gmid_engine.core.pin_blas_threads`, 설계 40 §2.4.13 (1)). test 는 바깥 값을 덮지 않는다.

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
    base = os.environ.get(entry["env"]) or entry["default"]     # 환경 변수가 비어 있지 않으면 그 폴더가 실제 캐시다(기본값은 Windows 경로라 Linux 에서는 쓸 수 없다)
    if not os.path.isabs(base):
        raise RuntimeError("실제 캐시 폴더가 절대 경로가 아니다(%s): 환경 변수 %s 로 이 OS 의 폴더를 지정한다" % (base, entry["env"]))
    real = os.path.normcase(os.path.abspath(base))
    test_dir = os.path.join(os.path.dirname(os.path.abspath(base)), _TEST_CACHE_DIRNAME)
    too_long = sys.platform == "win32" and len(test_dir) >= _TEST_CACHE_MAX_LEN      # 길이 한도는 Windows MAX_PATH 때문이다(위 docstring)
    if os.path.normcase(test_dir) == real or too_long:
        raise RuntimeError("test 캐시 폴더가 실제 캐시와 같거나 너무 길다: %s" % test_dir)
    os.environ[entry["env"]] = test_dir


_isolate_table_cache()


# ---------------------------------------------------------------- 무거운 test 마커 (interface card C6, 사용자 결정 N-2)
# 마커 `slow` + 옵션 `--run-slow`. `--run-slow` 가 없으면 `slow` 표시 항목을 수집 뒤 `pytest_deselected` 로 뺀다(요약에 deselected 로 보인다).
# `-m` 식과 무관하게 옵션으로만 가른다(설계 40 §2.4.13 (5) '무거운 test 마커' -- `-m` 을 주면 규칙 H 마커의 기본 제외가 꺼져 suite 구성이 바뀐다).
# 반드시 포함 실행(판정 agent 전체 suite, 병합 직전): `python -m pytest -q gmid_engine/tests -p no:cacheprovider --run-slow`.
SLOW_MARKER = "slow"
RUN_SLOW_OPTION = "--run-slow"


def pytest_addoption(parser):
    parser.addoption(RUN_SLOW_OPTION, action="store_true", default=False,
                     help="slow 표시 test(9회로 BLAS 스레드 결정성 등)도 실행한다. 없으면 수집 뒤 deselected")


def pytest_configure(config):
    config.addinivalue_line("markers", SLOW_MARKER + ": 무거운 test -- " + RUN_SLOW_OPTION + " 를 줄 때만 실행(없으면 deselected)")


def pytest_collection_modifyitems(config, items):
    if config.getoption(RUN_SLOW_OPTION):
        return
    keep, drop = [], []
    for it in items:
        (drop if it.get_closest_marker(SLOW_MARKER) else keep).append(it)
    if drop:
        config.hook.pytest_deselected(items=drop)
        items[:] = keep
