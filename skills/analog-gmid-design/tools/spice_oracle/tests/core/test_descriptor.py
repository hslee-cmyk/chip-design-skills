"""OP-2 기술자 읽기(core/descriptor.py) -- interface 20261104-op23 §3·§4 T2-1 ~ T2-10.

oracle 종류: (a) 구성으로 정답이 정해진 합성 입력. 기대 sha256 은 test 가 `hashlib` 로 직접 잰 값 또는 손으로 쓴 바이트의
해시다(피검 함수 `lf_sha256` 등으로 기대값을 만들지 않는다). 출처는 각 test 주석(interface 표 번호).
거부 test 는 양성 대조(같은 toy 가 통과)와 짝이다: test_t2_4 가 양성 대조.
"""
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest

from core.descriptor import (canonical_sha256, lf_sha256, load_descriptor, match_recorded, raw_sha256)
from core.results import OracleError

from op23_support import A_LIB, B_LIB, X_LIB, build_toy, dump, lf_of, sha, write


def H(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ T2-1 ~ T2-3 해시 정의 (a)
def test_t2_1a_lf_converts_crlf():
    # oracle (a): 구성으로 정해짐 -- \r\n 은 \n 이 된 바이트의 해시 (interface T2-1a)
    assert lf_sha256(b"x\r\ny\n") == H(b"x\ny\n")


def test_t2_1b_lone_cr_unchanged():
    assert lf_sha256(b"x\ry\n") == H(b"x\ry\n")           # T2-1b 홀로 있는 \r 불변


def test_t2_1c_left_to_right_once():
    # T2-1c: b"\r\r\n" 는 왼쪽부터 한 번 -> 앞 \r 은 남고 \r\n 만 \n: b"\r\n"
    assert lf_sha256(b"\r\r\n") == H(b"\r\n")


def test_t2_1d_bom_not_stripped():
    assert lf_sha256(b"\xef\xbb\xbfx\n") != H(b"x\n")
    assert lf_sha256(b"\xef\xbb\xbfx\n") == H(b"\xef\xbb\xbfx\n")   # BOM 불변(바이트 그대로)


def test_t2_1e_raw_is_plain_sha256():
    assert raw_sha256(b"a\r\nb") == H(b"a\r\nb")           # raw 는 정규화 없음 (interface §3 raw_sha256)


def test_t2_2_canonical_sha256_sorted_compact_utf8():
    # T2-2: 키 정렬, 구분자 (",", ":"), ensure_ascii=False, UTF-8
    assert canonical_sha256({"b": 1, "a": "가"}) == H('{"a":"가","b":1}'.encode("utf-8"))


def test_t2_3_match_recorded_lf_raw_none():
    c = b"p\r\n"
    assert match_recorded(H(b"p\n"), c) == "lf"             # T2-3a: LF 값과 같음 (기대 해시는 손으로 쓴 바이트)
    assert match_recorded(H(c), c) == "raw"                  # T2-3b: raw 와만 같음
    assert match_recorded("0" * 64, c) is None               # T2-3c
    c2 = b"q\n"                                              # T2-3d: LF = raw 이면 'lf' 우선
    assert match_recorded(H(c2), c2) == "lf"


# ------------------------------------------------------------------ T2-4 양성 대조
def test_t2_4_load_ok_record_root_and_machine_dependent(tmp_path):
    toy = build_toy(tmp_path)
    d = load_descriptor(toy.d, env={})
    assert d.record_root == os.path.abspath((tmp_path / "pdk").as_posix())
    assert d.record_root_source == "config_default"
    # a.lib 는 CRLF 라 엔진 선언 기록(raw)이 LF 와 다르다 -> 기계 의존 하나. b 는 기술자가 쓰지 않아 없음.
    refs = [r["ref"] for r in d.machine_dependent_refs]
    assert refs == ["engine_source:a"], refs
    assert all(r["matched"] == "raw" for r in d.machine_dependent_refs)


def test_t2_4b_record_root_env_wins(tmp_path):
    toy = build_toy(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    d = load_descriptor(toy.d, env={"PR": str(other)})
    assert d.record_root == os.path.abspath(str(other))
    assert d.record_root_source == "env:PR"


# ------------------------------------------------------------------ T2-5 stale
def _stale(path, **kw):
    with pytest.raises(OracleError) as ei:
        load_descriptor(path, env={}, **kw)
    return ei.value


def test_t2_5a_engine_decl_raw_sha_is_stale_on_crlf_checkout(tmp_path):
    toy = build_toy(tmp_path, e_crlf=True)
    toy.doc["engine_decl"]["sha256"] = sha(toy.e_path.read_bytes())    # raw (LF 와 다름)
    assert sha(toy.e_path.read_bytes()) != lf_of(toy.e_path.read_bytes())
    toy.write_descriptor()
    e = _stale(toy.d)
    assert e.code == "pdk_descriptor_stale" and e.stage == "2" and e.detail["ref"] == "engine_decl"


def test_t2_5b_extra_source_raw_sha_is_stale(tmp_path):
    toy = build_toy(tmp_path)
    toy.doc["extra_sources"]["x"]["sha256"] = sha(X_LIB)               # raw(CRLF) != LF
    toy.write_descriptor()
    e = _stale(toy.d)
    assert e.code == "pdk_descriptor_stale" and e.detail["ref"] == "extra_source:x"


@pytest.mark.parametrize("new_bytes", [b"* x\r", b"\xef\xbb\xbf* x\r\n"], ids=["lone_cr", "bom"])
def test_t2_5c_changed_bytes_are_stale(tmp_path, new_bytes):
    toy = build_toy(tmp_path)                                          # 기술자 x sha = 원래 바이트의 LF 값
    write(tmp_path / "pdk" / "x.lib", new_bytes)
    e = _stale(toy.d)
    assert e.code == "pdk_descriptor_stale" and e.detail["ref"] == "extra_source:x"


def test_t2_5d_engine_source_sha_changed(tmp_path):
    toy = build_toy(tmp_path)
    s = toy.e["sources"]["a"]["sha256"]
    toy.e["sources"]["a"]["sha256"] = ("0" if s[0] != "0" else "1") + s[1:]    # 한 글자 바꿈
    toy.write_engine_decl()                                                    # e.json 바이트가 바뀌므로 engine_decl.sha256 을 맞춤
    e = _stale(toy.d)
    assert e.code == "pdk_descriptor_stale" and e.detail["ref"] == "engine_source:a"
    assert e.detail["expected_sha256"] == toy.e["sources"]["a"]["sha256"]


def test_t2_5e_missing_engine_source_file(tmp_path):
    toy = build_toy(tmp_path)
    (tmp_path / "pdk" / "a.lib").unlink()
    e = _stale(toy.d)
    assert e.code == "pdk_descriptor_stale" and e.detail["ref"] == "engine_source:a"
    assert e.detail["actual_sha256"] == "missing"


def test_t2_5f_input_descriptor_sha_mismatch(tmp_path):
    toy = build_toy(tmp_path)
    e = _stale(toy.d, expected_lf_sha256="0" * 64)
    assert e.code == "pdk_descriptor_stale" and e.detail["ref"] == "input_descriptor"
    # 양성 대조: 맞는 값이면 통과
    ok = load_descriptor(toy.d, env={}, expected_lf_sha256=lf_of(toy.d.read_bytes()))
    assert ok.path is not None


# ------------------------------------------------------------------ T2-6 duplicated
def _dup(path):
    with pytest.raises(OracleError) as ei:
        load_descriptor(path, env={})
    return ei.value


def test_t2_6a_same_path(tmp_path):
    toy = build_toy(tmp_path)
    toy.doc["extra_sources"]["x"]["path"] = "a.lib"
    toy.doc["extra_sources"]["x"]["sha256"] = lf_of(A_LIB)             # stale 을 먼저 지나게 sha 를 파일 LF 에 맞춤
    toy.write_descriptor()
    e = _dup(toy.d)
    assert e.code == "descriptor_source_duplicated" and e.stage == "2" and e.detail["why"] == "path"


def test_t2_6b_same_lf_sha_with_unused_engine_source(tmp_path):
    toy = build_toy(tmp_path, x_bytes=b"* b\n")                        # x.lib 바이트 = b.lib 바이트 (b 는 기술자가 안 씀)
    assert toy.doc["extra_sources"]["x"]["sha256"] == lf_of(B_LIB)
    e = _dup(toy.d)
    assert e.code == "descriptor_source_duplicated" and e.detail["why"] == "sha"


def test_t2_6c_unused_engine_source_missing_is_file_missing(tmp_path):
    toy = build_toy(tmp_path)
    (tmp_path / "pdk" / "b.lib").unlink()                              # 안 쓰는 원본도 잰다
    e = _dup(toy.d)
    assert e.code == "descriptor_source_duplicated" and e.detail["why"] == "file_missing"


# ------------------------------------------------------------------ T2-7 순서
def test_t2_7_order_schema_before_sha_before_dup(tmp_path):
    t1 = build_toy(tmp_path / "t1")
    t1.doc["schema"] = "oracle_pdk_descriptor/0"
    t1.doc["extra_sources"]["x"]["sha256"] = "0" * 64                  # sha 도 틀림
    t1.write_descriptor()
    assert _dup(t1.d).code == "descriptor_schema_invalid"
    t2 = build_toy(tmp_path / "t2")
    t2.doc["extra_sources"]["x"]["path"] = "a.lib"                     # 중복
    t2.doc["extra_sources"]["x"]["sha256"] = "0" * 64                  # sha 틀림
    t2.write_descriptor()
    assert _dup(t2.d).code == "pdk_descriptor_stale"


# ------------------------------------------------------------------ T2-8 스키마 거부
def _mut_mc(doc):
    doc["mc"] = {}


def _mut_unknown_kind_key(doc):
    doc["kinds"]["nk"]["unknown_key"] = 1


def _mut_empty_provenance(doc):
    doc["extra_sources"]["x"]["provenance"] = ""


@pytest.mark.parametrize("mut", [_mut_mc, _mut_unknown_kind_key, _mut_empty_provenance],
                         ids=["mc_key", "unknown_kind_key", "empty_provenance"])
def test_t2_8_schema_invalid(tmp_path, mut):
    toy = build_toy(tmp_path)
    load_descriptor(toy.d, env={})                                     # 양성 대조
    mut(toy.doc)
    toy.write_descriptor()
    e = _dup(toy.d)
    assert e.code == "descriptor_schema_invalid" and e.stage == "2"


def test_t2_8b_non_json_and_uppercase_sha(tmp_path):
    toy = build_toy(tmp_path)
    toy.d.write_bytes(b"{not json")
    assert _dup(toy.d).code == "descriptor_schema_invalid"
    toy2 = build_toy(tmp_path / "u")
    toy2.doc["extra_sources"]["x"]["sha256"] = toy2.doc["extra_sources"]["x"]["sha256"].upper()
    toy2.write_descriptor()
    assert _dup(toy2.d).code == "descriptor_schema_invalid"            # 소문자 16진 64자 아님


# ------------------------------------------------------------------ T2-9 기하 선택 칸
def test_t2_9_geometry_fields_optional_at_load(tmp_path):
    toy = build_toy(tmp_path, geometry_unit=None, multiplier=False)
    assert "geometry_unit" not in toy.doc["kinds"]["nk"] and "parallel_multiplier" not in toy.doc["kinds"]["nk"]
    d = load_descriptor(toy.d, env={})                                 # 거부는 T3-1c (실행 전)
    assert d.doc["kinds"]["nk"]["call_form"] == "subckt_wrapper"


# ------------------------------------------------------------------ T2-10 fp
def test_t2_10_fp_crlf_invariant_and_content_sensitive(tmp_path):
    toy = build_toy(tmp_path)
    fp0 = load_descriptor(toy.d, env={}).fp
    toy.write_descriptor(crlf=True)                                    # d.json 만 CRLF (참조 sha 칸은 그대로)
    assert b"\r\n" in toy.d.read_bytes()
    assert load_descriptor(toy.d, env={}).fp == fp0
    toy.doc["model_family"] = "toy2"                                   # 내용 한 칸 바꿈
    toy.write_descriptor()
    assert load_descriptor(toy.d, env={}).fp != fp0


def test_t2_10b_fp_follows_referenced_file_content(tmp_path):
    # fp 입력 = (기술자 LF, 엔진 선언 LF들, extra 파일 LF들): 참조 파일이 바뀌어 sha 칸도 맞추면 fp 가 다르다
    toy = build_toy(tmp_path)
    fp0 = load_descriptor(toy.d, env={}).fp
    new_x = b"* x changed\n"
    write(tmp_path / "pdk" / "x.lib", new_x)
    toy.doc["extra_sources"]["x"]["sha256"] = lf_of(new_x)
    toy.write_descriptor()
    assert load_descriptor(toy.d, env={}).fp != fp0
