"""Phase 2 복원 계약: P5에서 잘못 지운 계획 지정 함수 둘(20260930-restore-plan-functions).

spec card `docs/02-design/specs/20260930-restore-plan-functions.spec.md` 계약 2·3을 판정한다.
계약 1(AST가 P5 base 0ecb686 정의와 같음)·5(레지스트리)·6(E-LIB·E-INST)은 auditor가 git 이력·도구로 대조한다 --
이 test는 git 이력을 읽지 않고 기대 해시를 박지 않는다. 계약 4(P5 계약 test 목록 조정)는
`test_d_delete_dead.py` 쪽 변경이다.

* 계약 2 -- `sizing_recipe.lut_conditions_from_npz(npz_data)`: `files`에 `corner`·`temp_c`가 있으면
  `{"recorded": True, ...}`에 **있는 키만** 담고, 둘 다 없으면 `recorded` False + `note` 문자열(값을 지어내지 않는다).
  저장소 LUT `A/sky130_nfet_pfet_lut_sample.npz`는 corner 'tt'·temp_c 27.0을 기록하고 있다(spec card 2026-09-30 실측).
* 계약 3 -- `run_harness.derived_spec(circuit_key, why, **overrides)`: 빈·공백 `why` -> `ValueError`, 미등록 key ->
  `ValueError`, override 없음 -> 정본과 같은 spec(`_spec_source` 추가 없음), override 있음 -> 명시 키만 바뀌고 나머지는
  정본과 같으며 `_spec_source`에 바꾼 키와 `why`가 남는다. `_spec_source` 문구에서 비지 않은 list·tuple 값(override 값·정본 값)은
  값 대신 `n<길이>`, 스칼라는 값 그대로 적힌다.

이 test는 base(두 함수가 없다)에서 red이고 복원 뒤 green이다.

oracle 대조(계획 N3.12.3):

* test_lut_conditions_* (합성) -- (a) 구성 입력: `files`·키 조회를 갖춘 합성 npz 대역 객체. 어떤 키를 넣었는지로 정답
  (담길 키와 값)이 정해진다. 값(`'ff'`, `-40.0`)은 이 test가 고른 입력 그대로다 -- 피검 식이 아니다.
* test_lut_conditions_from_repository_npz -- (d) spec card 계약 2의 실측 문장("corner 'tt'·temp_c 27.0 기록",
  2026-09-30)이 기대값. 피검 함수 출력을 붙여넣은 것이 아니다.
* test_derived_spec_without_override_* -- (a) 성질 판정(spec card 계약 3 보강 문장, V4 규칙 (2)): 기대값은 피검 반환식
  (`canonical_spec(key)`)이 아니라 `run_harness.SPECS[key]["spec_fn"]()`(등록 표가 가리키는 spec 생성 함수 -- 다른 경로)로
  만들고, 키 집합과 값을 키별로 대조하며, `_spec_source`에 `why`가 추가되지 않았음을 본다.
* test_derived_spec_with_override_* / test_derived_spec_sequence_override_* -- (a) 구성 입력: 회로 key는 `run_harness.SPECS`의
  키 전부(회로 이름을 박지 않는다), override 값은 이 test가 정본과 다르게 만든 값. `_spec_source` 기대 문자열(`n<길이>`, 스칼라 값
  그대로)은 spec card 계약 3 문장에서 만든다. 거부(ValueError)는 spec card 계약 3·'거부해야 할 입력'이 정한 행동이다.
"""
import importlib
import pathlib
import re
import sys

import numpy as np
import pytest

# contracts -> tests -> assets(A) -> analog-gmid-design -> skills -> 저장소 루트
_TESTS_DIR = pathlib.Path(__file__).resolve().parents[1]
_ASSETS_DIR = _TESTS_DIR.parent
_REPO_ROOT = _ASSETS_DIR.parents[2]
_WORKSPACES_DIR = _REPO_ROOT / "workspaces"
_REPO_LUT = _ASSETS_DIR / "sky130_nfet_pfet_lut_sample.npz"

# import 순서: A를 sys.path 맨 앞에 두고 `sizing_recipe`를 **먼저** import한 뒤 `run_harness`를 import한다.
# `run_harness`가 import 때 메인 저장소 assets 경로를 sys.path 맨 앞에 넣으므로(기존 결함), 먼저 import하면
# 이 트리(worktree·격리 복제본)가 아닌 메인 트리의 `sizing_recipe`가 잡힌다.
if str(_WORKSPACES_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKSPACES_DIR))
if str(_ASSETS_DIR) in sys.path:
    sys.path.remove(str(_ASSETS_DIR))
sys.path.insert(0, str(_ASSETS_DIR))
import sizing_recipe  # noqa: E402,F401  (run_harness보다 먼저 -- 위 주석)
import run_harness  # noqa: E402,F401


def _import(name: str):
    return importlib.import_module(name)


# 회로 key는 SPECS에서 읽는다(회로 이름을 코드에 박지 않는다 -- `_library_sized_contexts.py` 선례).
_CIRCUIT_KEYS = sorted(_import("run_harness").SPECS)
# 정본에 없을 것이 확실한 key(전제를 test에서 확인한다).
_UNREGISTERED_KEY = "no_such_circuit_restore_plan_functions"
_WHY = "20260930-restore-plan-functions 계약 3 판정용 합성 변형"


# --------------------------------------------------------------------------------------
# 계약 2: lut_conditions_from_npz
# --------------------------------------------------------------------------------------
class _FakeNpz:
    """`numpy.load(...npz)` 결과(NpzFile)의 대역: `files` 목록과 키 조회. 값은 NpzFile처럼 0차원 배열."""

    def __init__(self, entries: dict):
        self._entries = {k: np.asarray(v) for k, v in entries.items()}
        self.files = list(self._entries)

    def __getitem__(self, key):
        return self._entries[key]

    def __contains__(self, key):
        return key in self._entries

    def keys(self):
        return list(self._entries)


# LUT 본체 키(조건 메타가 아닌 것) -- 대역이 실제 LUT 파일처럼 보이도록 넣는 채움 데이터.
_BODY = {"L": [0.15e-6, 0.3e-6], "VGS": [0.0, 0.9, 1.8]}


def assert_recorded_conditions(result, expected_conditions: dict) -> None:
    """판정: 기록이 있는 입력 -> `recorded` True이고 입력에 있던 조건 키만, 그 값 그대로 담는다."""
    assert isinstance(result, dict), f"dict가 아니다: {type(result).__name__}"
    assert result == {"recorded": True, **expected_conditions}, result
    if "corner" in expected_conditions:
        assert isinstance(result["corner"], str), type(result["corner"]).__name__
    if "temp_c" in expected_conditions:
        assert isinstance(result["temp_c"], float), type(result["temp_c"]).__name__


def assert_not_recorded(result) -> None:
    """판정: 기록이 없는 입력 -> `recorded` False, `note` 문자열, corner·temp_c 값을 지어내지 않는다."""
    assert isinstance(result, dict), f"dict가 아니다: {type(result).__name__}"
    assert result.get("recorded") is False, result
    assert isinstance(result.get("note"), str) and result["note"].strip(), result
    assert "corner" not in result and "temp_c" not in result, f"기록 없는 값을 지어냈다: {result}"


def test_lut_conditions_both_recorded():
    # oracle (a): corner·temp_c 둘 다 넣은 합성 대역 -> 둘 다 그 값 그대로(입력이 곧 기대값).
    sr = _import("sizing_recipe")
    fake = _FakeNpz({"corner": "ff", "temp_c": -40.0, **_BODY})
    assert_recorded_conditions(sr.lut_conditions_from_npz(fake), {"corner": "ff", "temp_c": -40.0})


def test_lut_conditions_corner_only():
    # oracle (a): corner만 넣은 합성 대역 -> corner만 담고 temp_c는 지어내지 않는다.
    sr = _import("sizing_recipe")
    fake = _FakeNpz({"corner": "ss", **_BODY})
    assert_recorded_conditions(sr.lut_conditions_from_npz(fake), {"corner": "ss"})


def test_lut_conditions_temp_only():
    # oracle (a): temp_c만 넣은 합성 대역 -> temp_c만 담고 corner는 지어내지 않는다.
    sr = _import("sizing_recipe")
    fake = _FakeNpz({"temp_c": 125.0, **_BODY})
    assert_recorded_conditions(sr.lut_conditions_from_npz(fake), {"temp_c": 125.0})


def test_lut_conditions_none_recorded():
    # oracle (a): 조건 키가 없는 합성 대역 -> recorded False + note, 값 없음(spec card '거부해야 할 입력').
    sr = _import("sizing_recipe")
    assert_not_recorded(sr.lut_conditions_from_npz(_FakeNpz(dict(_BODY))))


def test_lut_conditions_from_repository_npz():
    # oracle (d): spec card 계약 2 실측 문장 -- 저장소 LUT는 corner 'tt'·temp_c 27.0을 기록한다(2026-09-30).
    sr = _import("sizing_recipe")
    assert _REPO_LUT.is_file(), f"저장소 LUT가 없다: {_REPO_LUT}"
    with np.load(_REPO_LUT, allow_pickle=False) as data:
        result = sr.lut_conditions_from_npz(data)
    assert_recorded_conditions(result, {"corner": "tt", "temp_c": 27.0})


def test_lut_condition_checks_reject_wrong_results():
    # oracle (a): 판정 보조 함수 자기 점검 -- 손으로 만든 틀린 결과를 거부한다(공허한 통과 방지).
    with pytest.raises(AssertionError):
        assert_recorded_conditions({"recorded": True, "corner": "ss", "temp_c": 27.0}, {"corner": "ss"})  # 지어낸 temp_c
    with pytest.raises(AssertionError):
        assert_recorded_conditions({"recorded": False, "note": "x"}, {"corner": "ss"})
    with pytest.raises(AssertionError):
        assert_not_recorded({"recorded": False, "note": "x", "corner": "tt"})  # 지어낸 corner
    with pytest.raises(AssertionError):
        assert_not_recorded({"recorded": False})  # note 없음
    with pytest.raises(AssertionError):
        assert_not_recorded({"recorded": True, "note": "x"})
    assert_not_recorded({"recorded": False, "note": "기록 없음"})
    assert_recorded_conditions({"recorded": True, "temp_c": 125.0}, {"temp_c": 125.0})


# --------------------------------------------------------------------------------------
# 계약 3: derived_spec
# --------------------------------------------------------------------------------------
def _registry_spec(circuit_key: str) -> dict:
    """정본 기대값의 **피검과 다른 경로**: 등록 표 `SPECS[key]["spec_fn"]`를 직접 불러 만든 spec.

    `derived_spec`이 부르는 `canonical_spec(key)` 호출을 기대값으로 쓰지 않는다(spec card 계약 3 보강, V4 규칙 (2)).
    """
    H = _import("run_harness")
    spec_fn = H.SPECS[circuit_key]["spec_fn"]
    assert callable(spec_fn), f"SPECS[{circuit_key!r}]['spec_fn'] 이 callable이 아니다"
    spec = spec_fn()
    assert isinstance(spec, dict) and spec, f"spec_fn 결과가 비었거나 dict가 아니다: {type(spec).__name__}"
    return spec


def test_circuit_keys_present():
    # 판정 범위가 공허하지 않다: SPECS에 등록 회로가 있고, 미등록 key 전제가 성립한다.
    H = _import("run_harness")
    assert _CIRCUIT_KEYS, "run_harness.SPECS가 비었다(판정 범위 공허)"
    assert _UNREGISTERED_KEY not in H.SPECS


@pytest.mark.parametrize("why", ["", "   ", "\t\n"])
@pytest.mark.parametrize("circuit_key", _CIRCUIT_KEYS)
def test_derived_spec_rejects_blank_why(circuit_key, why):
    # oracle (a): 빈·공백 why -> ValueError(spec card 계약 3·'거부해야 할 입력'). override 유무 둘 다.
    H = _import("run_harness")
    with pytest.raises(ValueError):
        H.derived_spec(circuit_key, why)
    with pytest.raises(ValueError):
        H.derived_spec(circuit_key, why, vdd=1.2)


def test_derived_spec_rejects_unregistered_key():
    # oracle (a): SPECS에 없는 key -> ValueError(spec card 계약 3). why는 유효하게 준다.
    H = _import("run_harness")
    assert _UNREGISTERED_KEY not in H.SPECS
    with pytest.raises(ValueError):
        H.derived_spec(_UNREGISTERED_KEY, _WHY)
    with pytest.raises(ValueError):
        H.derived_spec(_UNREGISTERED_KEY, _WHY, vdd=1.2)


def assert_unchanged_without_override(result: dict, reference: dict, why: str) -> None:
    """판정(성질): override 없는 변형은 정본과 같다 -- 키 집합이 같고, 값이 키별로 같고, `_spec_source`에 why가
    추가되지 않았다(정본에 없으면 결과에도 없다). `reference`는 피검과 다른 경로로 만든 정본이다."""
    assert isinstance(result, dict), f"dict가 아니다: {type(result).__name__}"
    assert set(result) == set(reference), sorted(set(result) ^ set(reference))
    for key, value in reference.items():
        assert result[key] == value, f"{key}: {result[key]!r} != 정본 {value!r}"
    if "_spec_source" not in reference:
        assert "_spec_source" not in result
    else:
        assert why not in str(result["_spec_source"]), f"override 없는데 why가 남았다: {result['_spec_source']!r}"


def assert_only_overrides_changed(result: dict, canonical: dict, overrides: dict, why: str) -> None:
    """판정: 명시한 키만 override 값이고, `_spec_source` 밖의 나머지 키는 정본과 같으며, `_spec_source`에 키와 why가 남는다."""
    assert isinstance(result, dict), f"dict가 아니다: {type(result).__name__}"
    for key, value in overrides.items():
        assert result[key] == value, f"override {key}: {result.get(key)!r} != {value!r}"
    untouched = set(canonical) - set(overrides) - {"_spec_source"}
    assert untouched, "비교할 나머지 키가 없다(판정 공허)"
    for key in untouched:
        assert key in result, f"정본 키 {key}가 사라졌다"
        assert result[key] == canonical[key], f"{key}: {result[key]!r} != 정본 {canonical[key]!r}"
    expected_keys = (set(canonical) | set(overrides)) - {"_spec_source"}
    assert set(result) - {"_spec_source"} == expected_keys, sorted((set(result) - {"_spec_source"}) ^ expected_keys)
    assert "_spec_source" in result, "override가 있는데 _spec_source가 없다"
    source = str(result["_spec_source"])
    for key in overrides:
        assert key in source, f"_spec_source에 바꾼 키 {key}가 없다: {source!r}"
    assert why in source, f"_spec_source에 why가 없다: {source!r}"


def _length_token(n: int) -> str:
    """spec card 계약 3 문장의 `n<길이>` 서식(앞뒤가 다른 영숫자·숫자에 붙지 않은 토큰)."""
    return rf"(?<![0-9A-Za-z_])n{n}(?![0-9])"


def assert_sequence_value_written_as_length(source: str, key: str, old, new) -> None:
    """판정: 비지 않은 list·tuple 값은 `_spec_source`에 값 대신 `n<길이>`로 적힌다(정본 값·override 값 둘 다),
    키 이름은 남고 원시 값(list·tuple 표기)은 들어가지 않는다."""
    assert len(old) != len(new) and len(old) > 0 and len(new) > 0, "전제 위반: 길이가 같거나 빈 값"
    assert key in source, f"_spec_source에 바꾼 키 {key}가 없다: {source!r}"
    for n in (len(old), len(new)):
        assert re.search(_length_token(n), source), f"_spec_source에 n{n}이 없다: {source!r}"
    for raw in (old, new):
        for text in {repr(raw), str(raw), repr(list(raw)), repr(tuple(raw))}:
            assert text not in source, f"_spec_source에 원시 값 {text[:60]}...이 들어갔다: {source[:200]!r}"


def assert_scalar_value_written_as_is(source: str, key: str, old, new) -> None:
    """판정: 스칼라 값은 `_spec_source`에 값 그대로 적힌다(정본 값·override 값 둘 다)."""
    assert key in source, f"_spec_source에 바꾼 키 {key}가 없다: {source!r}"
    for value in (old, new):
        assert str(value) in source, f"_spec_source에 스칼라 값 {value!r}이 없다: {source!r}"


@pytest.mark.parametrize("circuit_key", _CIRCUIT_KEYS)
def test_derived_spec_without_override_keeps_registry_spec(circuit_key):
    # oracle (a) 성질: 기대값은 SPECS[key]["spec_fn"]()(피검과 다른 경로) -- 키 집합·키별 값이 같고 why가 추가되지 않는다.
    H = _import("run_harness")
    reference = _registry_spec(circuit_key)
    assert_unchanged_without_override(H.derived_spec(circuit_key, _WHY), reference, _WHY)


@pytest.mark.parametrize("circuit_key", _CIRCUIT_KEYS)
def test_derived_spec_with_override_changes_only_named_keys(circuit_key):
    # oracle (a): override 값은 이 test가 정본 값과 다르게 구성한 입력(vdd 절반, L_min 두 배) --
    # 명시 키만 그 값, 나머지는 canonical_spec과 같다. 정본 자체가 변형되지 않았는지도 본다.
    H = _import("run_harness")
    canonical = H.canonical_spec(circuit_key)
    overrides = {"vdd": canonical["vdd"] * 0.5, "L_min": canonical["L_min"] * 2.0}
    for key, value in overrides.items():
        assert value != canonical[key], f"전제 위반: override {key} 가 정본과 같다"
    result = H.derived_spec(circuit_key, _WHY, **overrides)
    assert_only_overrides_changed(result, canonical, overrides, _WHY)
    assert H.canonical_spec(circuit_key) == canonical, "derived_spec이 정본을 바꿨다"


def _first_key_of_type(spec: dict, kind: type) -> str:
    """정본에서 비지 않은 `kind`(list 또는 tuple) 값을 가진 첫 키(정렬 순) -- 키 이름을 박지 않는다."""
    keys = sorted(k for k, v in spec.items() if type(v) is kind and len(v) > 0)
    assert keys, f"전제 위반: 정본에 비지 않은 {kind.__name__} 값 키가 없다"
    return keys[0]


@pytest.mark.parametrize("kind", [list, tuple], ids=["list", "tuple"])
@pytest.mark.parametrize("circuit_key", _CIRCUIT_KEYS)
def test_derived_spec_sequence_override_written_as_length(circuit_key, kind):
    # oracle (a): 정본의 list(또는 tuple) 키를 길이가 하나 긴 같은 종류 값으로, 스칼라 vdd를 절반으로 바꾼 구성 입력.
    # 기대 문자열은 spec card 계약 3 문장 -- 시퀀스는 `n<정본 길이>`·`n<새 길이>`(원시 값 없음), 스칼라는 값 그대로.
    H = _import("run_harness")
    reference = _registry_spec(circuit_key)
    seq_key = _first_key_of_type(reference, kind)
    old_seq = reference[seq_key]
    new_seq = kind(list(old_seq) + [old_seq[-1]])
    new_vdd = reference["vdd"] * 0.5
    overrides = {seq_key: new_seq, "vdd": new_vdd}
    result = H.derived_spec(circuit_key, _WHY, **overrides)
    assert_only_overrides_changed(result, reference, overrides, _WHY)
    source = str(result["_spec_source"])
    assert_sequence_value_written_as_length(source, seq_key, old_seq, new_seq)
    assert_scalar_value_written_as_is(source, "vdd", reference["vdd"], new_vdd)


def test_derived_spec_checks_reject_wrong_results():
    # oracle (a): 판정 보조 함수 자기 점검 -- 손으로 만든 틀린 spec을 거부한다(공허한 통과 방지).
    canonical = {"vdd": 1.8, "L_min": 0.15, "_spec_source": "run_harness.SPECS"}
    with pytest.raises(AssertionError):
        assert_unchanged_without_override({"vdd": 1.2, "L_min": 0.15, "_spec_source": "run_harness.SPECS"},
                                          canonical, _WHY)
    with pytest.raises(AssertionError):
        assert_unchanged_without_override({"vdd": 1.8, "L_min": 0.15}, canonical, _WHY)  # 키 누락
    with pytest.raises(AssertionError):
        assert_unchanged_without_override({"vdd": 1.8, "_spec_source": "x"}, {"vdd": 1.8}, _WHY)  # 없던 _spec_source
    with pytest.raises(AssertionError):  # override 없는데 why 추가
        assert_unchanged_without_override({**canonical, "_spec_source": f"run_harness.SPECS; {_WHY}"}, canonical, _WHY)
    assert_unchanged_without_override(dict(canonical), canonical, _WHY)
    good = {"vdd": 0.9, "L_min": 0.15, "_spec_source": f"derived: vdd -- {_WHY}"}
    assert_only_overrides_changed(good, canonical, {"vdd": 0.9}, _WHY)
    with pytest.raises(AssertionError):  # 정본에 없던 키가 생김
        assert_only_overrides_changed({**good, "extra": 1}, canonical, {"vdd": 0.9}, _WHY)
    with pytest.raises(AssertionError):  # 명시하지 않은 키까지 바뀜
        assert_only_overrides_changed({**good, "L_min": 0.3}, canonical, {"vdd": 0.9}, _WHY)
    with pytest.raises(AssertionError):  # why 누락
        assert_only_overrides_changed({**good, "_spec_source": "derived: vdd"}, canonical, {"vdd": 0.9}, _WHY)
    with pytest.raises(AssertionError):  # 바꾼 키 이름 누락
        assert_only_overrides_changed({**good, "_spec_source": _WHY}, canonical, {"vdd": 0.9}, _WHY)
    with pytest.raises(AssertionError):  # override 값 미반영
        assert_only_overrides_changed({**good, "vdd": 1.8}, canonical, {"vdd": 0.9}, _WHY)


def test_sequence_and_scalar_format_checks_reject_wrong_sources():
    # oracle (a): `_spec_source` 서식 판정의 자기 점검 -- 손으로 만든 문구로 거부·통과를 본다.
    old, new = [1.0, 2.0, 3.0], [1.0, 2.0, 3.0, 3.0]
    assert_sequence_value_written_as_length("derived: grid n3->n4 -- why", "grid", old, new)
    with pytest.raises(AssertionError):  # 원시 list 값이 들어감
        assert_sequence_value_written_as_length(f"derived: grid {old}->{new} n3 n4", "grid", old, new)
    with pytest.raises(AssertionError):  # 길이 토큰 하나 없음
        assert_sequence_value_written_as_length("derived: grid n3 -- why", "grid", old, new)
    with pytest.raises(AssertionError):  # 다른 숫자에 붙은 토큰은 길이 토큰이 아니다(n30·n4)
        assert_sequence_value_written_as_length("derived: grid n30->n4", "grid", old, new)
    with pytest.raises(AssertionError):  # 키 이름 없음
        assert_sequence_value_written_as_length("derived: n3->n4", "grid", old, new)
    with pytest.raises(AssertionError):  # 원시 tuple 값이 들어감
        assert_sequence_value_written_as_length("derived: wb (1.0, 2.0)->n3 n2", "wb", (1.0, 2.0), (1.0, 2.0, 2.0))
    assert_scalar_value_written_as_is("derived: vdd 1.8->0.9 -- why", "vdd", 1.8, 0.9)
    with pytest.raises(AssertionError):  # 스칼라를 길이 토큰 등으로 바꿔 적음
        assert_scalar_value_written_as_is("derived: vdd n1->n1 -- why", "vdd", 1.8, 0.9)
    with pytest.raises(AssertionError):  # 정본 값 누락
        assert_scalar_value_written_as_is("derived: vdd ->0.9 -- why", "vdd", 1.8, 0.9)
