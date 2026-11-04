"""OP-7 어댑터 조각 코어 -- 구간 규칙 선언(`lut_bin_rule/1`) 찾기·호환 모드 대조 -- interface 20261104-op7b §3, §4 T7-1~T7-8, T7-11, §5 잠금.

oracle (a)(d): 구성으로 정해진 합성 입력(interface §4 toy 표 -- 파일 바이트 `x\\r\\n`·`y\\n`, 해시는 test 가 hashlib 로 직접 잼)과 사용자 선언
규칙(D §16 '검사 순서 처음 하나만'). 피검 함수로 기대값을 만들지 않는다. 시뮬레이터 호출 0, 엔진 import 0.
해석(interface 가 모호해 정한 것):
  * H-6 `read_under_root(rel)` 은 파일이 없으면 `None` 을 돌려주거나 `FileNotFoundError` 를 던진다 -- 둘 다 '파일 없음'(T7-1b)으로 본다.
  * H-7 `OracleError` 는 다른 card 와 같은 `core.results.OracleError`(.code, .stage, .detail).
  * H-8 '칸 없음'(순 2)의 닫힌 칸 = `model_files_sha256`·`simulator`·`compat`(뒤 검사가 읽는 칸).
  * H-9 `CompatDecl` 은 dataclass(frozen)이고 키워드로 만들어진다(`FrozenInstanceError` 로 frozen 확인).
"""
import ast
import dataclasses
import hashlib
from pathlib import Path

import pytest

from core.bin_rule import CompatDecl, check_compat, find_decl, recorded_lf_set
from core.cache import cache_key
from core.results import OracleError

from adapters.ngspice.read import compat_mode_of

from conftest import ORACLE_DIR
from op23_support import bin_rule_doc

H = lambda b: hashlib.sha256(b).hexdigest()           # noqa: E731 -- test 가 직접 재는 해시

FILE_A = b"x\r\n"                                     # LF 정규화 -> b"x\n"
FILE_B = b"y\n"
L1, L2, L3 = H(b"x\n"), H(b"y\n"), H(b"z\n")          # 손으로 정한 바이트의 해시(L3 = 어떤 파일에도 없는 값)
FP = {"sim_version": "s-1"}
MODES = {"m": {"spiceinit_text": "T", "log_line": "^MODE m$"}}


def toy_doc():
    return bin_rule_doc([L1, L2], sim_name="s", sim_version="1", mode="m", text="T")


def reading(files):
    return lambda rel: files.get(rel)


# ------------------------------------------------------------------ T7-1 recorded_lf_set
def test_t7_1a_lf_of_each_recorded_file_ignoring_recorded_values():
    # oracle (a): 기록 값(0*64, 1*64)은 읽지 않는다 -- 결과는 파일 바이트의 LF 해시 둘(L1: CRLF -> LF 뒤)뿐
    got = recorded_lf_set({"a": "0" * 64, "b": "1" * 64}, reading({"a": FILE_A, "b": FILE_B}))
    assert got == {L1, L2}


def test_t7_1a_recorded_values_do_not_change_result():
    other = recorded_lf_set({"a": "f" * 64, "b": "e" * 64}, reading({"a": FILE_A, "b": FILE_B}))
    assert other == {L1, L2}


@pytest.mark.parametrize("how", ["none", "raises"])
def test_t7_1b_missing_file_is_undeclared_model_set(how):
    def read(rel):
        if rel == "a":
            if how == "raises":
                raise FileNotFoundError(rel)
            return None
        return FILE_B
    with pytest.raises(OracleError) as ei:
        recorded_lf_set({"a": "0" * 64, "b": "1" * 64}, read)
    e = ei.value
    assert e.code == "bin_rule_undeclared" and e.stage == "8b" and e.detail["why"] == "model_set"


# ------------------------------------------------------------------ T7-2 ~ T7-6 find_decl
def test_t7_2_subset_passes_and_returns_doc():
    d = toy_doc()
    assert find_decl(d, {L1}, FP) == d
    assert find_decl(d, {L1, L2}, FP) == d                 # 같은 집합도 부분 집합


def _reject(doc, lf, fp=FP):
    with pytest.raises(OracleError) as ei:
        find_decl(doc, lf, fp)
    e = ei.value
    assert e.code == "bin_rule_undeclared" and e.stage == "8b"
    return e.detail


def test_t7_3_no_decl_ref():
    assert _reject(None, {L1})["why"] == "no_decl_ref"


def test_t7_4_decl_invalid_schema_wrong():
    d = toy_doc(); d["schema"] = "lut_bin_rule/2"
    det = _reject(d, {L1})
    assert det["why"] == "decl_invalid" and "item" in det


def test_t7_4_decl_invalid_empty_model_files():
    d = toy_doc(); d["model_files_sha256"] = []
    det = _reject(d, {L1})
    assert det["why"] == "decl_invalid" and "item" in det


@pytest.mark.parametrize("field", ["model_files_sha256", "simulator", "compat"])
def test_t7_4_decl_invalid_field_absent(field):
    d = toy_doc(); del d[field]
    assert _reject(d, {L1})["why"] == "decl_invalid"


def test_t7_5_model_set_missing_listed():
    det = _reject(toy_doc(), {L1, L3})
    assert det["why"] == "model_set" and list(det["missing"]) == [L3]


def test_t7_6_simulator_mismatch_declared_and_actual():
    det = _reject(toy_doc(), {L1}, {"sim_version": "s-2"})
    assert det["why"] == "simulator" and det["declared"] == "s-1" and det["actual"] == "s-2"


# 순서(처음 하나만, §3 표): 형식 -> 포함 -> 판
def test_order_invalid_before_model_set_before_simulator():
    d = toy_doc(); d["schema"] = "x"
    assert _reject(d, {L3}, {"sim_version": "s-2"})["why"] == "decl_invalid"
    assert _reject(toy_doc(), {L3}, {"sim_version": "s-2"})["why"] == "model_set"


# ------------------------------------------------------------------ T7-7 check_compat
def test_t7_7a_compat_decl_from_table():
    c = check_compat(toy_doc(), MODES)
    assert isinstance(c, CompatDecl)
    assert (c.mode, c.spiceinit_text, c.log_line) == ("m", "T", "^MODE m$")
    assert c.spiceinit_sha256 == H(b"T")                  # utf-8 글의 sha256(손으로 잼)
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.mode = "n"


def _compat_reject(doc, modes):
    with pytest.raises(OracleError) as ei:
        check_compat(doc, modes)
    e = ei.value
    assert e.code == "bin_rule_compat_mismatch" and e.stage == "8b"
    return e.detail


def test_t7_7b_declared_sha_changed_one_char():
    d = toy_doc()
    good = d["compat"]["spiceinit_sha256"]
    d["compat"]["spiceinit_sha256"] = ("0" if good[0] != "0" else "1") + good[1:]
    det = _compat_reject(d, MODES)
    assert det["declared"] == d["compat"]["spiceinit_sha256"] and det["actual"] == H(b"T")


def test_t7_7c_mode_absent_in_table_actual_null():
    det = _compat_reject(toy_doc(), {})
    assert det["declared"] == H(b"T") and det["actual"] is None


def test_t7_7d_table_text_differs_from_declared():
    det = _compat_reject(toy_doc(), {"m": {"spiceinit_text": "U", "log_line": "^MODE m$"}})
    assert det["declared"] == H(b"T") and det["actual"] == H(b"U")


def test_check_compat_sha_checked_before_mode():
    # §3 순 5(선언 글 대 선언 sha)가 순 6(모드 있음)보다 앞: 둘 다 틀리면 actual 은 null 이 아니라 선언 글의 sha
    d = toy_doc(); d["compat"]["spiceinit_sha256"] = "0" * 64
    det = _compat_reject(d, {})
    assert det["actual"] == H(b"T")


# ------------------------------------------------------------------ T7-8 compat_mode_of
def test_t7_8a_line_regex_matches_one_mode():
    assert compat_mode_of("x\nMODE m\ny", MODES) == "m"


def test_t7_8b_no_sentence_is_none():
    assert compat_mode_of("x\ny\n", MODES) is None


def test_t7_8b_two_modes_match_is_none():
    two = {"m": {"spiceinit_text": "T", "log_line": "^MODE m$"}, "n": {"spiceinit_text": "U", "log_line": "^MODE .$"}}
    assert compat_mode_of("MODE m", two) is None


def test_t7_8_line_anchored_not_substring():
    # 줄 정규식은 줄 단위로 맞춘다: 한 줄 안의 부분 문자열(앞에 글자가 붙음)은 적중이 아니다
    assert compat_mode_of("xMODE m", MODES) is None
    assert compat_mode_of("MODE m", {"n": {"spiceinit_text": "U", "log_line": "^MODE n$"}}) is None


# ------------------------------------------------------------------ T7-11 cache_key 다섯째 항
def test_t7_11_spiceinit_sha_alone_changes_key():
    base = dict(a="fp1", t="t1", b=["h1"], g=("-b",))
    k = {s: cache_key(base["a"], base["t"], base["b"], base["g"], s) for s in (H(b"T"), H(b"U"), "")}
    assert len(set(k.values())) == 3                       # 서로 다른 다섯째 항 = 서로 다른 키(D §9)


# ------------------------------------------------------------------ §5 잠금 (정적, 판정자도 grep 으로 재실행)
def _tree(rel):
    p = ORACLE_DIR / rel
    assert p.exists(), p
    return ast.parse(p.read_text(encoding="utf-8"))


def test_lock_core_bin_rule_imports_and_literals():
    t = _tree("core/bin_rule.py")
    mods = []
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            mods += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            mods.append(("." * n.level) + (n.module or ""))
    banned = ("adapters", "subprocess", "gmid_engine")
    assert not [m for m in mods if any(b in m for b in banned)], mods
    # 방언·PDK 토큰은 코어 문자열 리터럴에 없다(O-197, 어댑터 몫). 이름은 역할 중립 토큰만 검사
    lits = [n.value for n in ast.walk(t) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for tok in ("sky130", "ngspice", "ngbehavior", ".option", "hspice"):
        assert not [s for s in lits if tok in s.lower()], tok


def test_lock_ngspice_cache_key_fifth_arg_not_empty_literal():
    t = _tree("adapters/ngspice/__init__.py")
    calls = [n for n in ast.walk(t) if isinstance(n, ast.Call)
             and (getattr(n.func, "id", None) == "cache_key" or getattr(n.func, "attr", None) == "cache_key")]
    assert calls, "cache_key 호출 없음"
    for c in calls:
        fifth = c.args[4] if len(c.args) >= 5 else next((k.value for k in c.keywords if k.arg == "spiceinit_sha"), None)
        assert fifth is not None
        assert not (isinstance(fifth, ast.Constant) and fifth.value == ""), ast.dump(fifth)


def test_lock_oracle_run_compat_sha_not_none_literal():
    t = _tree("oracle_run.py")
    for n in ast.walk(t):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and k.value == "compat_sha256":
                    assert not (isinstance(v, ast.Constant) and v.value is None)
