"""`load_json_checked(path, where) -> CheckedJson(data, sha256)` -- CONTRACT 3.1 (gate `json_read`), 0절 실패 형식·exit code."""
from __future__ import annotations

import hashlib

import pytest

from gmid_engine.authoring import CheckedJson, load_json_checked
from gmid_engine.core import SchemaRejectedError, exit_code_for, require_immutable


def _write(tmp_path, data: bytes, name="j.json"):
    p = tmp_path / name
    p.write_bytes(data)
    return str(p)


def _reject(ah, path):
    exc, detail = ah.rejected(load_json_checked, path, path)
    assert detail["gate"] == "json_read"
    assert detail["where"] == path
    return exc, detail


def test_valid_json_returns_data_and_sha(tmp_path):
    raw = '{"a": [1, 2.5, "x", null, true], "b": {"c": -3}}'.encode("utf-8")
    path = _write(tmp_path, raw)
    got = load_json_checked(path, path)
    assert isinstance(got, CheckedJson)
    assert got.data == {"a": [1, 2.5, "x", None, True], "b": {"c": -3}}
    assert got.sha256 == hashlib.sha256(raw).hexdigest()


def test_bom(ah, tmp_path):
    path = _write(tmp_path, b"\xef\xbb\xbf" + b'{"a": 1}')
    exc, detail = _reject(ah, path)
    assert ah.rules(detail["hits"]) == ["bom"]
    assert exit_code_for(exc) == 7


def test_not_utf8(ah, tmp_path):
    path = _write(tmp_path, b'{"a": "\xff\xfe"}')
    exc, detail = _reject(ah, path)
    assert ah.rules(detail["hits"]) == ["not_utf8"]


def test_duplicate_key_nested_each_occurrence(ah, tmp_path):
    path = _write(tmp_path, b'{"a": 1, "a": 2, "b": {"c": 1, "d": [ {"e": 0, "e": 1} ], "c": 2}}')
    exc, detail = _reject(ah, path)
    assert ah.rules(detail["hits"]) == ["duplicate_key"] * 3


def test_duplicate_key_in_different_objects_is_fine(tmp_path):
    path = _write(tmp_path, b'{"a": {"k": 1}, "b": {"k": 2}, "c": [{"k": 3}, {"k": 4}]}')
    assert load_json_checked(path, path).data["c"][1] == {"k": 4}


@pytest.mark.parametrize("token", [b"NaN", b"Infinity", b"-Infinity", b"1e999", b"-1e999"])
def test_non_finite_single(ah, tmp_path, token):
    path = _write(tmp_path, b'{"v": ' + token + b"}")
    exc, detail = _reject(ah, path)
    assert ah.rules(detail["hits"]) == ["non_finite"]


def test_non_finite_each_occurrence(ah, tmp_path):
    path = _write(tmp_path, b'{"a": NaN, "b": [1e999, 2.0, -Infinity], "c": {"d": Infinity}}')
    exc, detail = _reject(ah, path)
    assert ah.rules(detail["hits"]) == ["non_finite"] * 4


def test_large_finite_number_is_fine(tmp_path):
    path = _write(tmp_path, b'{"v": 1e308, "w": -1.7e308}')
    assert load_json_checked(path, path).data == {"v": 1e308, "w": -1.7e308}


@pytest.mark.parametrize("text", [b'{"a": 1,}', b'{"a" 1}', b"", b'{"a": [1, 2}', b"{'a': 1}"])
def test_json_syntax(ah, tmp_path, text):
    path = _write(tmp_path, text)
    exc, detail = _reject(ah, path)
    assert ah.rules(detail["hits"]) == ["json_syntax"]


def test_json_syntax_reported_with_earlier_hits(ah, tmp_path):
    """3.1: 문법 오류는 앞서 모인 hits 와 함께 낸다."""
    path = _write(tmp_path, b'[{"a": 1, "a": 2}, {"b": NaN}, ]')
    exc, detail = _reject(ah, path)
    rules = ah.rules(detail["hits"])
    assert rules[-1] == "json_syntax"
    assert sorted(rules[:-1]) == ["duplicate_key", "non_finite"]


def test_missing_file_is_os_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_json_checked(str(tmp_path / "none.json"), "none")


def test_schema_rejected_record_is_immutable(ah, tmp_path):
    path = _write(tmp_path, b"\xef\xbb\xbf{}")
    with pytest.raises(SchemaRejectedError) as ei:
        load_json_checked(path, path)
    require_immutable(ei.value.record)
