"""[O-227 (2), A-71] 정지 사유 고정 공용 헬퍼 -- O-227 임시 고정, LA-1 재점검에서 해제 판단. (test 수집 대상이 아닌 이름: test_ 접두 없음)

쓰는 곳: test_stage_b_library.py(9건), test_s0_layer_9circuits.py(baseline_present·stage_reports 2건 x 2회로),
test_layer0_boundary_rows.py(layer0 존재 1건 x 2회로), test_g10_no_recompute_9circuits.py(1건 x 2회로).

규칙(oracle (c) 기준선 -- 아래 표는 머리 b8c4c189 에서 실행으로 잰 관측값이다. 사유가 물리적으로 맞는지는 판정하지 않는다):
- 관측한 정지 사유 목록이 표와 **정확히** 같으면 `pytest.xfail`(통과로 세지 않음). 다르거나(사유·소자 집합·넷·개수), 정지하지 않거나,
  읽을 수 없으면 실패한다. except·skip·`@pytest.mark.xfail` 없음.
- 정지 사유로 고정한 회로의 기준선 항목이 fixture 에 생기면 실패한다(기준선이 생겼으면 고정을 지우라는 뜻) -- 고정이 남아 있지 못하게 한다.
사유·소자 집합·불량 블록의 **값 표**(`STOP`·`BLOCK`)는 이 파일 한 자리다. 회로 이름은 이 표들과, 어느 (test, 회로) 가 고정 대상인지 정하는
쓰는 test 파일의 대상 목록(test_stage_b_library.py 의 `_STOP_PINNED`·`_BLOCK_PINNED`)에 나뉘어 있다 -- 두 곳이 어긋나도 조용히 통과하지 않는다:
대상 목록에만 있고 표에 없는 회로는 KeyError 로 실패하고, 표에만 있고 대상 목록에 없는 (test, 회로) 는 고정이 적용되지 않아 기존 단언이
그대로 실패한다(fail-closed, 판정 측정).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

BASELINE_PATH = Path(__file__).resolve().parent / "fixtures" / "u17_1b_s0_baseline.json"

# 정지 사유 표 -- 항목 = (class, detail.reason, detail.rule_branch, 정지 소자 집합(devices), 넷 집합(detail.nets, 없으면 빈 튜플)).
# O-227 임시 고정, LA-1 재점검에서 해제 판단. cnr_ota 는 단계 B 정지 1건(소자 x40, 넷 VCR·VDD_1V8), erfc_ota 는 1건(소자 M19·M20·M21).
STOP = {"cnr_ota": (("STRUCTURE_UNRESOLVED", "unsupported_rule_branch", "dc_resistor_cycle", ("x40",), ("VCR", "VDD_1V8")),),
        "erfc_ota": (("STRUCTURE_UNRESOLVED", "unsupported_rule_branch", "mos_zero_current_structural", ("M19", "M20", "M21"), ()),)}

# 불량 블록 표 -- 항목 = (블록 key, detail.reason). 이 회로는 정지가 아니다(단계 B stop_reasons 0건, achievability verdict ok, 블록 하나 unknown, pi 0).
# O-227 임시 고정, LA-1 재점검에서 해제 판단. 정확히 이 블록 하나일 때만 고정한다(둘째 불량 블록·중복은 실패).
BLOCK = {"r2r_opamp": ((("n_gn", "n_gp"), "block_input_pattern_unsupported"),)}


def load_baseline():
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def is_stop_pinned(circuit):
    return circuit in STOP


def settle(label, failing, observed, expected):
    if not failing:
        pytest.fail(f"{label}: 정지 사유로 고정한 조합이 해당 지점에서 실패하지 않는다(고정 해제 판단 필요)")
    if observed != expected:
        pytest.fail(f"{label}: 정지 사유가 표와 다르다 observed={observed!r} expected={expected!r}")
    pytest.xfail(f"O-227 임시 고정(LA-1 재점검에서 해제 판단): {expected!r}")


def observed_stop(report_b):
    """보고서 stop_reasons 각 항(JSON 문자열)의 (class, reason, rule_branch, 소자 집합, 넷 집합). 정렬한 목록(중복 보존), 문장 비교 없음."""
    got = []
    for raw in report_b["stop_reasons"]:
        item = json.loads(raw)
        d = item["detail"]
        got.append((item["class"], d["reason"], d["rule_branch"], tuple(sorted(item["devices"])), tuple(sorted(d.get("nets", ())))))
    return tuple(sorted(got))


def pin_stop(label, circuit, report_b, failing):
    """정지 고정 회로면 대조해 xfail 또는 실패. 표에 없는 회로는 아무것도 하지 않는다."""
    if circuit not in STOP:
        return
    if circuit in load_baseline():
        pytest.fail(f"{label}: {circuit} 의 기준선 항목이 fixture 에 생겼다 -- 정지 사유 고정(o227_stop_pin.STOP)을 지우고 기존 단언을 적용하라")
    settle(label, failing, observed_stop(report_b), STOP[circuit])


def bad_blocks(blocks):
    """기존 단언 `pi == ∏ 축`을 어기는 블록."""
    return [blk for blk in blocks if blk["pi"] != math.prod(size for _, size in blk["axes"])]


def pin_blocks(label, circuit, blocks):
    """불량 블록 고정 회로면 불량 블록 목록을 표와 대조해 같을 때만 그 목록을 돌려준다(다르면 실패). 표에 없는 회로는 []."""
    if circuit not in BLOCK:
        return []
    bad = bad_blocks(blocks)
    if not bad:
        pytest.fail(f"{label}: 불량 블록으로 고정한 조합이 해당 지점에서 실패하지 않는다(고정 해제 판단 필요)")
    got = tuple(sorted((tuple(blk["key"]), blk["reason"]) for blk in bad))
    if got != BLOCK[circuit]:
        pytest.fail(f"{label}: 불량 블록이 표와 다르다 observed={got!r} expected={BLOCK[circuit]!r}")
    return bad


def finish_blocks(circuit, bad):
    """다른 블록 단언을 모두 돈 뒤 마지막에 부른다. 고정한 불량 블록이 있었으면 xfail."""
    if bad:
        pytest.xfail(f"O-227 임시 고정(LA-1 재점검에서 해제 판단): {BLOCK[circuit]!r}")
