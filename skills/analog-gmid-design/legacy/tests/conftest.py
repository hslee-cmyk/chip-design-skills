"""analog-gmid-design test conftest -- TS7 xfail 선언(20260922-ts7-ic-xfail, 계획 N3.11 TS7, `00-common` CC-3).

정본: design `gain-budget-gmid-sizing.10-test-separation` §5.4 'C6에서 만드는 것', 의미는 `00-common` §8.1·§9.3.

* 옵션(모두 `=` 한 토큰 형식으로 넘긴다 -- `00-common` §8.1):
  * `--gmid-phase=<Phase>`: 기본값 없음. 없거나 계획서 N6.1 `phase_order` 밖이면 `pytest.UsageError`.
  * `--gmid-strict=<IC:case,...>`: 엄격 대상 케이스 키. 값 없는 `--gmid-strict=`는 키가 없는 것이다.
  * `--gmid-dod`: 그 Phase DoD 판정 실행 -- 표식 Phase가 현재 Phase인 케이스 전부가 엄격 대상.
* 표식 `gmid_ic(ic, *, phase, case)`, 케이스 키 = `"<IC>:<case>"`(케이스 하나뿐인 IC는 `case=""` -> `"IC3:"`).
* xfail 조건(`00-common` §9.3): 표식 Phase가 현재 Phase보다 뒤이거나, 같고 그 케이스 키가 엄격 대상이 아닐 때.
  reason = `"<IC> -- 담당 Phase <phase> -- 만료: <phase> DoD"`, `strict=False`. 표식 Phase가 앞이면 언제나 활성.
* 모르는 케이스 키 거부: `--gmid-strict`의 키마다 수집된 test 중 그 표식(IC·case)이 있고 표식 Phase가 현재
  Phase인 것이 없으면 `pytest.UsageError`.
* 계획서 표는 게이트 코드 `tools/gates/merge_gate.py`의 `read_plan_tables`로 읽는다(표 읽기 규칙의 정본 하나 --
  WP-14). `<저장소 루트>/tools/gates`는 `sys.path` **끝**에 더한다: V1은 게이트 코드 캐시를 `PYTHONPATH` 맨 앞에
  두므로 base 판 게이트 코드가 먼저 잡힌다(`05` §12-7).

C9(20260922-ts2-pytest-split, design §5.4 'C9에서 더하는 것')에서 더한 것:

* `--shuffle-seed=<int>`(기본 없음): `pytest_collection_modifyitems` 끝(xfail 표시 뒤)에서 값이 있으면
  `random.Random(seed).shuffle(items)`. 플러그인을 더하지 않는다(DEC-36).
* `pytest_report_header`: `shuffle-seed: <값 또는 none>`, `real_lut: <npz 상대 경로> sha256=<파일 바이트 해시>`.
  판정 문자열이 아니다.
* 세션 fixture(불변 자원만): `assets_dir`(= A, 이 파일 위치에서 계산), `library_dir`(= `assets_dir/library`),
  `toy_lut`(= `build_toy_lut()`, 이관본의 전역 `lut`), `real_lut`(`A/sky130_nfet_pfet_lut_sample.npz` 고정 경로).
"""
import hashlib
import os
import random
import sys

import pytest

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
# tests -> assets -> analog-gmid-design -> skills -> 저장소 루트
_REPO_ROOT = os.path.abspath(os.path.join(_TESTS_DIR, "..", "..", "..", ".."))
_GATES_DIR = os.path.join(_REPO_ROOT, "tools", "gates")
# tests -> assets(A)
_ASSETS_DIR = os.path.dirname(_TESTS_DIR)
_REAL_LUT_PATH = os.path.join(_ASSETS_DIR, "sky130_nfet_pfet_lut_sample.npz")
if _GATES_DIR not in sys.path:
    sys.path.append(_GATES_DIR)

import merge_gate  # noqa: E402  (위 sys.path 끝 추가 뒤)

_MARKER = "gmid_ic"
_PHASE_ORDER_KEY = pytest.StashKey[tuple]()


def pytest_addoption(parser):
    group = parser.getgroup("gmid", "analog-gmid-design 계약 test(TS7)")
    group.addoption("--gmid-phase", action="store", default=None, dest="gmid_phase",
                    help="현재 Phase(계획서 N6.1 phase_order 중 하나, 기본값 없음 -- 필수). --gmid-phase=<Phase>")
    group.addoption("--gmid-strict", action="store", default=None, dest="gmid_strict",
                    help="엄격 대상 케이스 키 목록 '<IC>:<case>,...'. 값 없는 --gmid-strict= 는 키 없음.")
    group.addoption("--gmid-dod", action="store_true", default=False, dest="gmid_dod",
                    help="Phase DoD 판정 실행: 표식 Phase가 현재 Phase인 케이스 전부를 엄격 대상으로.")
    group.addoption("--shuffle-seed", action="store", type=int, default=None, dest="shuffle_seed",
                    help="수집된 test 순서를 random.Random(<int>)로 섞는다(기본 없음 = 섞지 않음). --shuffle-seed=<int>")


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "gmid_ic(ic, *, phase, case): 계약 test 케이스의 담당 Phase와 케이스(계획서 N4.1, 00-common §9.3)",
    )
    if config.option.help:
        return
    plan_path = os.path.join(_REPO_ROOT, merge_gate.PLAN_PATH)
    try:
        phase_order = tuple(merge_gate.read_plan_tables(plan_path).phase_order)
    except (OSError, UnicodeDecodeError, merge_gate.GateError) as exc:
        raise pytest.UsageError(f"계획서 판정 표를 읽지 못함({plan_path}): {exc}") from exc
    phase = config.getoption("gmid_phase")
    if phase is None:
        raise pytest.UsageError("--gmid-phase=<Phase> 가 필요하다(기본값 없음, 00-common §9.3)")
    if phase not in phase_order:
        raise pytest.UsageError(
            f"--gmid-phase={phase} 는 계획서 phase_order {list(phase_order)} 밖이다(00-common §9.3)")
    config.stash[_PHASE_ORDER_KEY] = phase_order


def _strict_keys(raw):
    # 00-common §8.1: 값 없는 `--gmid-strict=`는 키가 없는 것이다 -- 빈 문자열을 split(",")해 키 ""를 만들지 않는다.
    if raw is None or raw == "":
        return set()
    return set(raw.split(","))


def _marker_fields(item, marker, phase_order):
    if len(marker.args) != 1 or set(marker.kwargs) != {"phase", "case"}:
        raise pytest.UsageError(
            f"{item.nodeid}: 표식 형식은 gmid_ic(ic, *, phase, case) 이다: args={marker.args!r} kwargs={marker.kwargs!r}")
    ic, phase, case = marker.args[0], marker.kwargs["phase"], marker.kwargs["case"]
    if not all(isinstance(v, str) for v in (ic, phase, case)):
        raise pytest.UsageError(f"{item.nodeid}: gmid_ic 표식의 ic·phase·case는 문자열이어야 한다")
    if phase not in phase_order:
        raise pytest.UsageError(
            f"{item.nodeid}: 표식 phase={phase} 는 계획서 phase_order {list(phase_order)} 밖이다")
    return ic, phase, case


def pytest_collection_modifyitems(session, config, items):
    phase_order = config.stash[_PHASE_ORDER_KEY]
    current = config.getoption("gmid_phase")
    cur_idx = phase_order.index(current)
    strict = _strict_keys(config.getoption("gmid_strict"))
    dod = config.getoption("gmid_dod")
    current_phase_keys = set()
    for item in items:
        markers = list(item.iter_markers(_MARKER))
        if not markers:
            continue
        if len(markers) != 1:
            # 표식이 둘이면 xfail·엄격 판정이 모호하다 -- 조용히 하나를 고르지 않고 멈춘다.
            raise pytest.UsageError(f"{item.nodeid}: gmid_ic 표식이 {len(markers)}개다(케이스마다 정확히 하나)")
        ic, phase, case = _marker_fields(item, markers[0], phase_order)
        key = f"{ic}:{case}"
        mark_idx = phase_order.index(phase)
        if mark_idx < cur_idx:
            continue
        if mark_idx == cur_idx:
            current_phase_keys.add(key)
            if dod or key in strict:
                continue
        item.add_marker(pytest.mark.xfail(reason=f"{ic} -- 담당 Phase {phase} -- 만료: {phase} DoD", strict=False))
    unknown = sorted(strict - current_phase_keys)
    if unknown:
        raise pytest.UsageError(
            f"--gmid-strict 의 모르는 케이스 키 {unknown}: 수집된 test 중 그 gmid_ic 표식(IC·case)이 있고 "
            f"표식 Phase가 현재 Phase {current} 인 것이 없다(00-common §9.3)")
    seed = config.getoption("shuffle_seed")
    if seed is not None:
        # xfail 표시 뒤에 섞는다(design §5.4 C9) -- 숨은 순서 의존을 드러내는 용도.
        random.Random(seed).shuffle(items)


def pytest_report_header(config):
    seed = config.getoption("shuffle_seed")
    rel = os.path.relpath(_REAL_LUT_PATH, _REPO_ROOT).replace(os.sep, "/")
    with open(_REAL_LUT_PATH, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    return [f"shuffle-seed: {'none' if seed is None else seed}", f"real_lut: {rel} sha256={digest}"]


@pytest.fixture(scope="session")
def assets_dir():
    return _ASSETS_DIR


@pytest.fixture(scope="session")
def library_dir(assets_dir):
    return os.path.join(assets_dir, "library")


@pytest.fixture(scope="session")
def toy_lut(assets_dir):
    if assets_dir not in sys.path:
        sys.path.insert(0, assets_dir)
    from sizing_recipe import build_toy_lut
    return build_toy_lut()


@pytest.fixture(scope="session")
def real_lut():
    return _REAL_LUT_PATH
