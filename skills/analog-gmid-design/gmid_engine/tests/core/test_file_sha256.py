"""WB-1 B-2 -- `gmid_engine.core.file_sha256` (interface card §1). oracle (식): sha256(바이트의 CRLF -> LF), 독립 hashlib."""
import hashlib

import pytest

from gmid_engine.core import file_sha256


def test_file_sha256_crlf_equals_lf(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"a\r\nb\n")
    b.write_bytes(b"a\nb\n")
    want = hashlib.sha256(b"a\nb\n").hexdigest()
    assert file_sha256(str(a)) == want
    assert file_sha256(str(b)) == want


def test_file_sha256_path_object_and_differs_by_content(tmp_path):
    a = tmp_path / "a.txt"
    a.write_bytes(b"x\n")
    assert file_sha256(a) == hashlib.sha256(b"x\n").hexdigest()
    a.write_bytes(b"y\n")
    assert file_sha256(a) == hashlib.sha256(b"y\n").hexdigest()


def test_file_sha256_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        file_sha256(str(tmp_path / "nope.txt"))
