"""WB-1 B-3 -- 위치 선언 `bin_rule` (interface card §1 '위치 선언'). oracle (식): card 표 + 독립 hashlib(CRLF -> LF 값).

설정 최상위 키 `"bin_rule": {"path", "sha256"}` (files 밖, path 는 설정 파일 폴더 기준).
"""
import hashlib
import json
import os
from pathlib import Path

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import resolve_lut_location

from .conftest import detail_of

DECL = b'{"schema": "lut_bin_rule/1"}\n'


def _lf_sha(b):
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def make(tmp, bin_rule="default", name="cfg"):
    tmp = Path(tmp)
    root = tmp / "data"
    root.mkdir(exist_ok=True)
    pdk = tmp / "pdk"
    pdk.mkdir(exist_ok=True)
    for f in ("manifest.json", "cap.npz", "mid.npz"):
        (root / f).write_bytes(b"m")
    (tmp / "rule.json").write_bytes(DECL)
    cfg = {"schema": "x",
           "root": {"default": str(root)}, "pdk_root": {"default": str(pdk)},
           "files": {k: {"path": v, "sha256": hashlib.sha256(b"m").hexdigest()}
                     for k, v in (("manifest", "manifest.json"), ("cap_npz", "cap.npz"),
                                  ("verify_midpoints", "mid.npz"))}}
    if bin_rule == "default":
        bin_rule = {"path": "rule.json", "sha256": _lf_sha(DECL)}
    if bin_rule is not None:
        cfg["bin_rule"] = bin_rule
    p = tmp / (name + ".json")
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return str(p)


def reject(path):
    with pytest.raises(SchemaRejectedError) as ei:
        resolve_lut_location(path, {})
    return detail_of(ei.value)


def test_bin_rule_normal_resolves_absolute_path(tmp_path):
    loc = resolve_lut_location(make(tmp_path), {})
    assert loc.bin_rule_path == os.path.abspath(str(tmp_path / "rule.json"))


def test_bin_rule_crlf_variant_passes(tmp_path):
    p = make(tmp_path)
    (tmp_path / "rule.json").write_bytes(DECL.replace(b"\n", b"\r\n"))
    loc = resolve_lut_location(p, {})
    assert loc.bin_rule_path == os.path.abspath(str(tmp_path / "rule.json"))


@pytest.mark.parametrize("bad", [None, "str", ["a"], {"path": "rule.json"}, {"sha256": "0" * 64},
                                 {"path": "/abs/rule.json", "sha256": "0" * 64},
                                 {"path": "C:/abs/rule.json", "sha256": "0" * 64},
                                 {"path": "../rule.json", "sha256": "0" * 64}])
def test_bin_rule_invalid_declaration(tmp_path, bad):
    # 정상 호출이 먼저 성공해야 공허하지 않다
    assert resolve_lut_location(make(tmp_path, name="ok"), {}).bin_rule_path
    d = reject(make(tmp_path, bin_rule=bad))
    assert d["reason"] == "lut_location_config_invalid" and d["item"] == "bin_rule"


def test_bin_rule_missing_file(tmp_path):
    p = make(tmp_path, bin_rule={"path": "absent.json", "sha256": "0" * 64})
    d = reject(p)
    assert d["reason"] == "lut_location_file_missing"


def test_bin_rule_sha256_mismatch(tmp_path):
    p = make(tmp_path)
    (tmp_path / "rule.json").write_bytes(DECL + b" ")
    assert reject(p)["reason"] == "lut_location_sha256_mismatch"
