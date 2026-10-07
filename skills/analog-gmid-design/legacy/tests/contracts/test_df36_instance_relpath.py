"""Phase 2 DF-36 계약: instance.json `topology_ref`를 저장소 루트 기준 상대 경로로(20260930-df36-instance-relpath).

spec card `docs/02-design/specs/20260930-df36-instance-relpath.spec.md` 계약 1~4를 판정한다. 계약 5(E-INST 나머지 필드
동일)·6(문서)은 auditor가 base와 병합본을 비교한다 -- 여기서 기대 해시를 박지 않는다. A = `skills/analog-gmid-design/assets`.

* 계약 1: 저장소 안 topology(library 전부)로 `save_instance_json`을 부르면 `topology_ref`가 저장소 루트 기준 상대 경로
  (`/` 구분, `./`·`..`·역슬래시·드라이브·앞 `/` 없음)이고, 루트에 이어 붙이면 그 topology 파일과 같은 실제 파일이다.
* 계약 2: 같은 파일을 절대 경로(역슬래시·슬래시 표기)·cwd 기준 상대 경로(여러 cwd, `..` 포함)로 넘겨도 저장값이 같다.
  출력 위치(tmp 아래 서로 다른 디렉터리)와 무관하다.
* 계약 3: 쓴 파일의 모든 문자열 값(키 포함)에 이 체크아웃 루트 경로가 없다(정·역슬래시 양쪽, 대소문자 무시).
* 계약 4: 저장소 밖 topology(tmp 아래 library 복사본) -> `ValueError`, 출력 파일 없음. 결핍 sizing의 기존 IC3 거부
  (`ValueError`, 파일 없음)는 그대로. 보강(2차 시도): 저장소 루트와 **다른 드라이브**의 절대 경로(파일이 없어도 된다)
  -> 정확히 `ValueError`, 출력 파일 없음(Windows에서 실행, POSIX는 드라이브 개념이 없어 skip).

입력 구성은 `test_ic3.py` 3절의 공개 경로를 따른다: library topology를 `run_topology_pipeline`에 넣은 결과(소자마다 자기
스택, n_fingers=2 x finger_w=1.0 = w=2.0) + 소자마다 다섯 필드를 가진 손으로 만든 sizing. 이 값들은 판정 대상이 아닌 구성 입력이다.

base에서 계약 1·3·4가 red이고(절대 경로를 가공 없이 쓰고, 저장소 밖 topology도 받아 쓴다) 병합본에서 green이다.

oracle 대조(계획 N3.12.3):

* test_topology_ref_is_repo_relative_* / test_topology_ref_same_for_* -- (a) 구성: 기대 상대 경로는 이 test 파일 위치에서 구한
  저장소 루트와 입력 topology 경로로 test가 만든다(`Path.relative_to(...).as_posix()`). 피검 출력으로 만들지 않는다.
* test_instance_has_no_checkout_root_string -- (a) 구성: 금지 문자열 = test 파일 위치에서 구한 이 체크아웃 루트(spec card 계약 3,
  00-common §11.4 '경로 누출 검사').
* test_outside_repo_topology_rejected / test_missing_sizing_still_rejected -- (a) 구성: 저장소 밖에 둔 복사본·소자 하나를 뺀
  sizing이 곧 거부 사유다(spec card 계약 4·'거부해야 할 입력').
* test_other_drive_topology_rejected -- (a) 구성: 저장소 루트 드라이브와 다른 문자로 만든 절대 경로가 곧 거부 사유다
  (계약 4 보강 문장, 1차 V3 생존 변이 -- 다른 드라이브 분기).
* test_relative_ref_check_* -- (a) 판정기 자기 점검: 손으로 만든 값(역슬래시·`..`·`./`·드라이브·앞 `/`)을 거부한다.
"""
import copy
import functools
import json
import os
import pathlib
import re
import shutil
import sys

import pytest

# contracts(0) -> tests(1) -> assets(2) -> analog-gmid-design(3) -> skills(4) -> 저장소 루트(5)
_THIS_FILE = pathlib.Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[5]
_ASSETS_DIR = _THIS_FILE.parents[2]
_LIBRARY_DIR = _ASSETS_DIR / "library"
if str(_ASSETS_DIR) not in sys.path:
    sys.path.insert(0, str(_ASSETS_DIR))

# `save_instance_json` docstring 입력 계약(interface card 인용, SizingResult 필드명) -- test_ic3와 같은 구성.
_SIZING_FIELDS = ("W", "L", "ID", "gm", "gm_id")
_PILOT_NAME = "two_stage_ota.topology.json"


def _library_topologies():
    # `_TEMPLATE`은 회로가 아니라 작성 틀이다(파일 이름 `_` 머리) -- test_ic3와 같은 규칙.
    return sorted(p for p in _LIBRARY_DIR.glob("*.topology.json") if not p.name.startswith("_"))


_LIBRARY_NAMES = [p.name for p in _library_topologies()]


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _netlist_names(path) -> list:
    return [e["name"] for e in _read_json(path)["netlist"]]


@functools.lru_cache(maxsize=16)
def _pipeline_inputs(name: str):
    """library 회로 하나의 (topology 절대 경로, sizing, pipeline_result) -- 구성 입력. 회로마다 한 번 계산해 캐시한다."""
    from stick_diagram import run_topology_pipeline
    topo_path = _LIBRARY_DIR / name
    names = _netlist_names(topo_path)
    overrides = {n: {"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": f"stack_{n}"} for n in names}
    pipeline_result = run_topology_pipeline(str(topo_path), overrides)
    sizing = {n: {k: 1.0 for k in _SIZING_FIELDS} for n in names}
    return topo_path, sizing, pipeline_result


def _save(out_path, topology_arg, name: str) -> dict:
    """`save_instance_json`으로 쓰고 다시 읽는다(입력은 캐시의 복사본 -- 호출 사이 오염 방지)."""
    from stick_diagram import save_instance_json
    _, sizing, pipeline_result = _pipeline_inputs(name)
    save_instance_json(str(out_path), str(topology_arg), copy.deepcopy(sizing), copy.deepcopy(pipeline_result))
    assert os.path.exists(out_path), f"파일이 생기지 않았다: {out_path}"
    return _read_json(out_path)


def _expected_ref(topo_path) -> str:
    """oracle (a): 이 test 파일 위치에서 구한 저장소 루트 기준 상대 경로(`/` 구분)."""
    return pathlib.Path(topo_path).resolve().relative_to(_REPO_ROOT).as_posix()


# --------------------------------------------------------------------------------------
# 판정 보조 함수
# --------------------------------------------------------------------------------------
_DRIVE = re.compile(r"^[A-Za-z]:")


def assert_normalized_repo_relative(value) -> None:
    """판정: 00-common §8.2 `diff_path` 모양 -- `/` 구분 상대 경로, `./`·`..`·역슬래시·드라이브·앞 `/`·빈 구획 없음."""
    assert isinstance(value, str) and value, f"비지 않은 문자열이 아니다: {value!r}"
    assert "\\" not in value, f"역슬래시가 있다: {value!r}"
    assert not _DRIVE.match(value), f"드라이브 문자가 있다: {value!r}"
    assert not value.startswith("/"), f"앞 `/`가 있다(절대 경로): {value!r}"
    segments = value.split("/")
    assert "" not in segments, f"빈 구획(`//` 또는 끝 `/`)이 있다: {value!r}"
    assert "." not in segments, f"`./` 구획이 있다: {value!r}"
    assert ".." not in segments, f"`..` 구획이 있다: {value!r}"


def assert_ref_points_to(value: str, topo_path) -> None:
    """판정: 저장값이 기대 상대 경로와 같고, 루트에 이어 붙이면 그 topology와 같은 실제 파일이다."""
    assert_normalized_repo_relative(value)
    assert value == _expected_ref(topo_path), f"topology_ref {value!r} != 기대 {_expected_ref(topo_path)!r}"
    joined = _REPO_ROOT / pathlib.PurePosixPath(value)
    assert joined.is_file(), f"루트에 이어 붙인 경로가 파일이 아니다: {joined}"
    assert os.path.samefile(joined, topo_path), f"{joined} 가 {topo_path} 와 다른 파일이다"


def _string_leaves(obj, depth: int = 0):
    """JSON 값의 모든 문자열(키 포함)."""
    if depth > 64:
        return
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                yield k
            yield from _string_leaves(v, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _string_leaves(v, depth + 1)


def _root_spellings(root) -> set:
    """이 체크아웃 루트의 정·역슬래시 표기(소문자) -- 경로 누출 검사의 금지 문자열."""
    spellings = set()
    for form in {str(root), os.path.realpath(str(root))}:
        spellings.add(form.replace("/", "\\").lower())
        spellings.add(form.replace("\\", "/").lower())
    return spellings


def assert_no_checkout_root(data, root) -> None:
    """판정: `data`의 어떤 문자열에도 이 체크아웃 루트 경로가 없다(대소문자 무시)."""
    banned = _root_spellings(root)
    leaks = sorted({s for s in _string_leaves(data) if any(b in s.lower() for b in banned)})
    assert leaks == [], f"체크아웃 루트 경로가 누출됐다: {[s[:120] for s in leaks]}"


# --------------------------------------------------------------------------------------
# 계약 1: 저장소 루트 기준 상대 경로
# --------------------------------------------------------------------------------------
def test_library_scope_present():
    # 판정 범위가 공허하지 않다: library 회로가 있고 파일럿이 그중 하나다.
    assert _LIBRARY_NAMES, f"library topology가 없다: {_LIBRARY_DIR}"
    assert _PILOT_NAME in _LIBRARY_NAMES
    assert (_REPO_ROOT / "skills" / "analog-gmid-design" / "assets").samefile(_ASSETS_DIR)


@pytest.mark.parametrize("name", _LIBRARY_NAMES)
def test_topology_ref_is_repo_relative_for_library(tmp_path, name):
    # oracle (a): 기대 = <루트>에서 본 library 파일의 상대 경로(test가 루트·입력 경로로 만든다). 계약 1.
    topo_path, _, _ = _pipeline_inputs(name)
    saved = _save(tmp_path / "out.instance.json", topo_path, name)
    assert_ref_points_to(saved["topology_ref"], topo_path)


# --------------------------------------------------------------------------------------
# 계약 2: 입력 경로 표기·cwd·출력 위치와 무관
# --------------------------------------------------------------------------------------
def test_topology_ref_same_for_path_spellings_and_cwd(tmp_path, monkeypatch):
    # oracle (a): 같은 파일의 여러 표기 -> 저장값이 모두 기대 상대 경로 하나. 계약 2.
    topo_path, _, _ = _pipeline_inputs(_PILOT_NAME)
    expected = _expected_ref(topo_path)
    absolute = str(topo_path)
    spellings = {
        "absolute_native": ("", absolute),
        "absolute_forward": ("", absolute.replace("\\", "/")),
        "absolute_with_dotdot": ("", str(_LIBRARY_DIR / ".." / "library" / _PILOT_NAME)),
        "cwd_root_relative": (str(_REPO_ROOT), os.path.relpath(absolute, _REPO_ROOT)),
        "cwd_root_relative_forward": (str(_REPO_ROOT), os.path.relpath(absolute, _REPO_ROOT).replace("\\", "/")),
        "cwd_library_bare": (str(_LIBRARY_DIR), _PILOT_NAME),
        "cwd_library_dot": (str(_LIBRARY_DIR), "./" + _PILOT_NAME),
        "cwd_assets_dotdot": (str(_ASSETS_DIR / "tests"), os.path.join("..", "library", _PILOT_NAME)),
    }
    refs = {}
    for label, (cwd, arg) in spellings.items():
        if cwd:
            monkeypatch.chdir(cwd)
        else:
            monkeypatch.chdir(tmp_path)
        out_dir = tmp_path / label
        out_dir.mkdir()
        saved = _save(out_dir / "out.instance.json", arg, _PILOT_NAME)
        refs[label] = saved["topology_ref"]
    monkeypatch.chdir(tmp_path)
    assert refs == {label: expected for label in spellings}, refs
    assert_ref_points_to(expected, topo_path)


def test_topology_ref_same_for_output_locations(tmp_path, monkeypatch):
    # oracle (a): 출력 위치만 다르게(tmp 깊이가 다른 두 곳) -> 저장값이 같다. 계약 2.
    monkeypatch.chdir(tmp_path)
    topo_path, _, _ = _pipeline_inputs(_PILOT_NAME)
    shallow = tmp_path / "a.instance.json"
    deep_dir = tmp_path / "x" / "y" / "z"
    deep_dir.mkdir(parents=True)
    ref_a = _save(shallow, topo_path, _PILOT_NAME)["topology_ref"]
    ref_b = _save(deep_dir / "b.instance.json", topo_path, _PILOT_NAME)["topology_ref"]
    assert ref_a == ref_b == _expected_ref(topo_path), (ref_a, ref_b)


# --------------------------------------------------------------------------------------
# 계약 3: 경로 누출 없음
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", _LIBRARY_NAMES)
def test_instance_has_no_checkout_root_string(tmp_path, name):
    # oracle (a): 금지 문자열 = test 파일 위치에서 구한 이 체크아웃 루트(00-common §11.4). 계약 3.
    topo_path, _, _ = _pipeline_inputs(name)
    saved = _save(tmp_path / "out.instance.json", topo_path, name)
    assert_no_checkout_root(saved, _REPO_ROOT)


# --------------------------------------------------------------------------------------
# 계약 4: 저장소 밖 topology 거부, 기존 IC3 거부 유지
# --------------------------------------------------------------------------------------
def test_outside_repo_topology_rejected(tmp_path):
    # oracle (a): 저장소 밖(tmp)에 둔 library 복사본 -> ValueError, 출력 파일 없음. 계약 4.
    from stick_diagram import save_instance_json
    topo_path, sizing, pipeline_result = _pipeline_inputs(_PILOT_NAME)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_topo = outside_dir / _PILOT_NAME
    shutil.copyfile(topo_path, outside_topo)
    resolved = str(outside_topo.resolve())
    try:
        os.path.relpath(resolved, str(_REPO_ROOT))
        crosses_drive = False
    except ValueError:
        crosses_drive = True
    assert crosses_drive or os.path.commonpath([resolved, str(_REPO_ROOT)]) != str(_REPO_ROOT), \
        f"전제 위반: tmp 복사본이 저장소 안이다 {resolved}"
    out = tmp_path / "outside.instance.json"
    with pytest.raises(ValueError):
        save_instance_json(str(out), str(outside_topo), copy.deepcopy(sizing), copy.deepcopy(pipeline_result))
    assert not out.exists(), "거부했는데 출력 파일이 생겼다"


def _other_drive_letter() -> str:
    """저장소 루트와 **다른** 드라이브 문자 하나(Z부터 내려가며, 가능하면 이 기계에 없는 드라이브). 문자를 박지 않고
    루트 드라이브에서 고른다 -- 루트가 어느 드라이브에 있든 성립한다."""
    root_drive = os.path.splitdrive(str(_REPO_ROOT))[0]
    assert re.fullmatch(r"[A-Za-z]:", root_drive), f"전제 위반: 저장소 루트에 드라이브 문자가 없다 {str(_REPO_ROOT)!r}"
    candidates = [c for c in "ZYXWVUTSRQPONMLKJIHGFED" if c.upper() != root_drive[0].upper()]
    absent = [c for c in candidates if not os.path.exists(f"{c}:\\")]
    return (absent or candidates)[0]


@pytest.mark.skipif(os.name != "nt",
                    reason="드라이브 문자는 Windows 경로 개념이다(POSIX에는 다른 드라이브 절대 경로가 없다) -- "
                           "저장소 밖 거부는 test_outside_repo_topology_rejected가 모든 OS에서 판정한다")
@pytest.mark.parametrize("sep", ["\\", "/"], ids=["backslash", "slash"])
def test_other_drive_topology_rejected(tmp_path, sep):
    # oracle (a) 구성: 저장소 루트와 다른 드라이브 문자로 만든 절대 경로(파일이 실제로 있을 필요 없음) -> 정확히 ValueError,
    # 출력 파일 없음(계약 4 보강 -- 판정 담당이 준 관찰 가능한 동작 문장). 다른 예외 타입이면 실패한다.
    from stick_diagram import save_instance_json
    _, sizing, pipeline_result = _pipeline_inputs(_PILOT_NAME)
    letter = _other_drive_letter()
    other = f"{letter}:{sep}df36_other_drive{sep}library{sep}{_PILOT_NAME}"
    assert os.path.splitdrive(other)[0].upper() != os.path.splitdrive(str(_REPO_ROOT))[0].upper(), other
    assert os.path.isabs(other), other
    out = tmp_path / "other_drive.instance.json"
    with pytest.raises(ValueError):
        save_instance_json(str(out), other, copy.deepcopy(sizing), copy.deepcopy(pipeline_result))
    assert not out.exists(), "거부했는데 출력 파일이 생겼다"


def test_missing_sizing_still_rejected(tmp_path):
    # oracle (a): 저장소 안 topology + 소자 하나를 뺀 sizing -> 기존 IC3 거부(ValueError, 파일 없음) 유지. 계약 4.
    from stick_diagram import save_instance_json
    topo_path, sizing, pipeline_result = _pipeline_inputs(_PILOT_NAME)
    dropped = sorted(sizing)[0]
    short = {n: dict(v) for n, v in sizing.items() if n != dropped}
    out = tmp_path / "short.instance.json"
    with pytest.raises(ValueError) as exc:
        save_instance_json(str(out), str(topo_path), short, copy.deepcopy(pipeline_result))
    assert dropped in str(exc.value)
    assert not out.exists()


# --------------------------------------------------------------------------------------
# 판정기 자기 점검
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "value",
    [
        "skills\\analog-gmid-design\\assets\\library\\x.topology.json",   # 역슬래시
        "skills/analog-gmid-design/assets\\library/x.topology.json",      # 섞인 역슬래시
        "../skills/analog-gmid-design/assets/library/x.topology.json",    # 앞 ..
        "skills/analog-gmid-design/assets/tests/../library/x.topology.json",  # 중간 ..
        "./skills/analog-gmid-design/assets/library/x.topology.json",     # 앞 ./
        "skills/./analog-gmid-design/assets/library/x.topology.json",     # 중간 ./
        "C:/repo/skills/analog-gmid-design/assets/library/x.topology.json",  # 드라이브
        "c:skills/x.topology.json",                                       # 드라이브(상대)
        "/home/u/repo/skills/analog-gmid-design/assets/library/x.topology.json",  # 앞 /
        "skills//analog-gmid-design/assets/library/x.topology.json",      # 빈 구획
        "",                                                               # 빈 값
        None,                                                             # 문자열 아님
    ],
)
def test_relative_ref_check_rejects_malformed_values(value):
    # oracle (a): 손으로 만든 잘못된 모양 -> 거부(spec card '거부해야 할 입력').
    with pytest.raises(AssertionError):
        assert_normalized_repo_relative(value)


def test_relative_ref_check_accepts_normalized_value():
    # oracle (a): 손으로 만든 올바른 모양 -> 통과(판정이 과하지 않다). 파일명 안의 점(`.topology.json`)은 구획이 아니다.
    assert_normalized_repo_relative("skills/analog-gmid-design/assets/library/x.topology.json")
    assert_normalized_repo_relative("a..b/c.d")


def test_leak_and_pointer_checks_reject_wrong_values(tmp_path):
    # oracle (a): 누출 검사·지시 검사 자기 점검 -- 손으로 만든 누출·다른 파일 지시를 거부한다.
    root = str(_REPO_ROOT)
    with pytest.raises(AssertionError):
        assert_no_checkout_root({"topology_ref": root + "\\x.json"}, _REPO_ROOT)
    with pytest.raises(AssertionError):
        assert_no_checkout_root({"a": [{"b": root.replace("\\", "/").upper() + "/x"}]}, _REPO_ROOT)
    with pytest.raises(AssertionError):
        assert_no_checkout_root({root: 1}, _REPO_ROOT)  # 키 안의 누출
    assert_no_checkout_root({"topology_ref": "skills/x.json", "n": [1, "a"]}, _REPO_ROOT)
    pilot = _LIBRARY_DIR / _PILOT_NAME
    other = sorted(n for n in _LIBRARY_NAMES if n != _PILOT_NAME)[0]
    with pytest.raises(AssertionError):  # 다른 library 파일을 가리킴
        assert_ref_points_to(_expected_ref(_LIBRARY_DIR / other), pilot)
    with pytest.raises(AssertionError):  # 절대 경로
        assert_ref_points_to(str(pilot), pilot)
    assert_ref_points_to(_expected_ref(pilot), pilot)
