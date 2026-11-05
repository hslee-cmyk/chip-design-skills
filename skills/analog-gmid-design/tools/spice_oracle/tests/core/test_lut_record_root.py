"""OP-2 LUT 기록 뿌리 해석(core.descriptor.resolve_location) -- interface §3·§4 T2-11, `E/lut/CONTRACT.md` 1.8 규칙.

oracle (a): 구성으로 정해진 합성 입력. 기대값 = 규칙 문장(env 가 비지 않으면 env 값의 abspath 와 'env:<이름>',
아니면 default 의 abspath 와 'config_default', 형식 오류는 lut_location_decl_invalid)을 그대로 대입.
"""
import os

import pytest

from core.descriptor import load_descriptor, resolve_location
from core.results import OracleError

from op23_support import build_toy, write, dump

DOC = {"pdk_root": {"env": "PR", "default": "D"}}


def test_t2_11_env_wins():
    path, source = resolve_location(DOC, "pdk_root", {"PR": "V"})
    assert path == os.path.abspath("V") and source == "env:PR"


@pytest.mark.parametrize("env", [{"PR": ""}, {}], ids=["empty_env", "absent_env"])
def test_t2_11_default_when_env_empty_or_absent(env):
    path, source = resolve_location(DOC, "pdk_root", env)
    assert path == os.path.abspath("D") and source == "config_default"


def test_t2_11_env_without_default_and_env_unset_is_invalid():
    with pytest.raises(OracleError) as ei:
        resolve_location({"pdk_root": {"env": "PR"}}, "pdk_root", {})
    assert ei.value.code == "lut_location_decl_invalid"
    assert set(ei.value.detail) >= {"item", "why"}


def test_t2_11_missing_pdk_root_key_is_rejected_not_fallen_back():
    # `pdk_root` 칸이 없으면 거부한다(LUT meta 절대 경로로 돌아가지 않음, spec C-2.5)
    with pytest.raises(OracleError) as ei:
        resolve_location({}, "pdk_root", {})
    assert ei.value.code == "lut_location_decl_invalid"


def test_t2_11_loader_reports_bad_location_decl_file(tmp_path):
    # 위치 선언 파일이 형식 오류(칸 없음)인데 기술자의 sha 칸은 그 파일에 맞춰져 있으면
    # 2단계 참조 sha 는 통과하고 형식 검사(4순)에서 lut_location_decl_invalid
    toy = build_toy(tmp_path)
    load_descriptor(toy.d, env={})                                      # 양성 대조
    b = dump({"schema": "gmid_lut_location/1"})
    write(toy.l_path, b)
    from op23_support import lf_of
    toy.doc["lut_record_root"]["location_decl"]["sha256"] = lf_of(b)
    toy.write_descriptor()
    with pytest.raises(OracleError) as ei:
        load_descriptor(toy.d, env={})
    assert ei.value.code == "lut_location_decl_invalid" and ei.value.stage == "2"
