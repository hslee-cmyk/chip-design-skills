"""XRUN-F1 card B interface card C3 -- `graft(target, block, part, donor, input_version)` 단독(B-T14).

oracle 종류:
* (비교) 결과 스냅샷을 손으로 만든 donor·target 스냅샷과 비교 -- C3 '결과: donor 의 그 블록 열(block.writes) 전부를 target 에 쓴
  스냅샷. 결과 block_version(block.name) == input_version, 그 열 필드의 value_fp·input_version 이 donor 와 같다. 블록이 쓰지 않는 열은
  target 그대로'.
* (식) C3 'part != "*" -> ValueError', 'donor.block_version(block.name) != input_version -> ValueError'.
donor 는 블록을 부르지 않고 `GraphSnapshot.write` 로 손으로 만든다(입력 버전 문자열도 손으로 정한 값) -- 피검 블록 호출과 독립.
"""
import pytest

from gmid_engine.core import GraphSnapshot, WriterTable, compute_block, graft

_TABLE = WriterTable([
    ("node", "v", "bias"),
    ("node", "u", "other"),
    ("device", "w", "sizer"),
    ("device", "gm", "sizer"),
])
_WRITES = (("device", "w"), ("device", "gm"))
_IV = "hand_input_version"


@compute_block("sizer", reads=(("node", "v"),), writes=_WRITES)
def _block(projection):
    raise AssertionError("graft 는 블록 함수를 부르지 않는다")


def _donor(version=_IV):
    s = GraphSnapshot.empty(_TABLE).write("bias", "in1", {("node", "v"): {"a": 1.0}})
    return s.write("sizer", version, {("device", "w"): {"m1": 2.0, "m2": 4.0}, ("device", "gm"): {"m1": 3.0}})


def _target(stale=False):
    s = GraphSnapshot.empty(_TABLE).write("bias", "in7", {("node", "v"): {"a": 1.0}})
    s = s.write("other", "o1", {("node", "u"): {"a": 5.0, "b": 6.0}})
    if stale:
        s = s.write("sizer", "stale_version", {("device", "w"): {"old": 9.0}, ("device", "gm"): {"old": 8.0}})
    return s


@pytest.mark.parametrize("stale", [False, True], ids=["target_without_block", "target_with_stale_block"])
def test_graft_writes_donor_block_columns(stale):
    donor = _donor()
    target = _target(stale)
    target_fp = target.fp
    out = graft(target, _block, "*", donor, _IV)
    # oracle 대조: C3 '결과 block_version(block.name) == input_version'
    assert out.block_version("sizer") == _IV
    for kind, field in _WRITES:
        # oracle 대조: C3 'donor 의 그 블록 열 전부를 target 에 쓴' -- 열 key·값이 donor 와 같다(target 의 옛 key 는 남지 않는다)
        assert out.column(kind, field) == donor.column(kind, field)
        for key, fv in donor.column_fields(kind, field):
            got = out.field(kind, key, field)
            # oracle 대조: C3 '그 열 필드의 value_fp·input_version 이 donor 와 같다'
            assert got.value_fp == fv.value_fp
            assert got.input_version == fv.input_version == _IV
    # oracle 대조: C3 '블록이 쓰지 않는 열은 target 그대로'
    for kind, field in (("node", "v"), ("node", "u")):
        assert out.column(kind, field) == target.column(kind, field)
        for (key, a), (key2, b) in zip(out.column_fields(kind, field), target.column_fields(kind, field)):
            assert key == key2 and a.value_fp == b.value_fp and a.input_version == b.input_version
    assert out.block_version("bias") == target.block_version("bias") == "in7"
    assert out.block_version("other") == target.block_version("other") == "o1"
    # 원본 불변(CONTRACT 5.6 '원본 불변')
    assert target.fp == target_fp
    assert donor.block_version("sizer") == _IV


def test_graft_input_version_mismatch_value_error():
    # oracle 대조: C3 'donor.block_version(block.name) != input_version -> ValueError'
    with pytest.raises(ValueError):
        graft(_target(), _block, "*", _donor(version="v_a"), "v_b")


def test_graft_donor_without_block_value_error():
    # oracle 대조: 같은 식 -- donor 에 그 블록 결과가 없으면 block_version None != input_version
    no_block = GraphSnapshot.empty(_TABLE).write("bias", "in1", {("node", "v"): {"a": 1.0}})
    with pytest.raises(ValueError):
        graft(_target(), _block, "*", no_block, _IV)


@pytest.mark.parametrize("part", ["P", "", "**"])
def test_graft_part_not_star_value_error(part):
    # oracle 대조: C3 'part != "*" -> ValueError'
    with pytest.raises(ValueError):
        graft(_target(), _block, part, _donor(), _IV)
