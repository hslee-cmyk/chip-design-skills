"""OP-3 LUT 기록 뿌리 교차 검사(core.bundle.check_record_root) -- interface §6 '기록 뿌리' T3-7a~d, design §7 `lut_record_root_mismatch`.

oracle (a): 엔진 원본 E0 = CRLF 가 든 손 바이트(LF 값 L0 != raw 값 R0), 기록 = {"r/a": R0}, 뿌리 아래 파일 바이트를 바꿔 가며
세 걸음(짝 찾기, 짝마다 뿌리 파일 LF == 엔진 원본 LF, 짝 0개 거부)을 구성으로 대입한다.
해석: `engine_files = {원본 키: (상대 경로, 바이트)}`, `read_under_root(상대 경로) -> bytes | None`, 반환 = 기계 의존 항목 목록.
"""
import hashlib

import pytest

from core.bundle import check_record_root
from core.results import OracleError

E0 = b"* engine file\r\n.param s = 1\r\n"
R0 = hashlib.sha256(E0).hexdigest()
L0 = hashlib.sha256(E0.replace(b"\r\n", b"\n")).hexdigest()
ENGINE = {"a": ("r/a", E0)}


def call(root_bytes, records=None):
    rec = {"r/a": R0} if records is None else records
    return check_record_root(rec, ENGINE, lambda rel: root_bytes if rel == "r/a" else None)


def test_precondition_raw_and_lf_differ():
    assert R0 != L0


def test_t3_7a_same_lf_passes_and_is_raw_matched():
    out = call(E0.replace(b"\r\n", b"\n"))                              # 뿌리 아래 파일 LF = 엔진 원본 LF
    assert len(out) == 1 and out[0]["matched"] == "raw"                 # 기록은 raw 로만 맞음


def test_t3_7b_different_bytes():
    with pytest.raises(OracleError) as ei:
        call(b"* other PDK tree\n")
    e = ei.value
    assert e.code == "lut_record_root_mismatch"
    assert e.detail["root_file_lf_sha256"] != e.detail["engine_file_lf_sha256"]
    assert e.detail["engine_file_lf_sha256"] == L0


def test_t3_7c_missing_file():
    with pytest.raises(OracleError) as ei:
        call(None)
    assert ei.value.code == "lut_record_root_mismatch" and ei.value.detail["root_file_lf_sha256"] == "missing"


def test_t3_7d_no_pairs():
    with pytest.raises(OracleError) as ei:
        call(E0, records={"r/a": "0" * 64})
    assert ei.value.code == "lut_record_root_mismatch" and ei.value.detail["why"] == "no_pairs"
