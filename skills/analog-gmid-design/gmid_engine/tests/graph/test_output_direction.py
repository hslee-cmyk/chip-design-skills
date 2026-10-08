"""graph/output_direction.py -- 출력노드 방향별 전류 공급 셀 분류(계획 DEC-65, 설계 41 1.9, 계약 10.3 불변량 2 '출력 방향').

oracle (d) 계획 DEC-65 본문: 노드 k·방향(충전/방전)별로 그 방향 전류를 댈 수 있는 셀(채널 단자가 k, 반대 단자 경로가 그 레일)을
(β) DC 바이어스 셀(gate 가 교류접지) / (σ) 신호 셀 / (κ) 측면 주입 셀(K8: DC 역할 바이어스 전류원인데 gate 가 신호)로 나눈다.
두 방향 모두 σ -> push-pull, 한 방향만 σ -> class-A. 측정 기대(DEC-65): two_stage_ota OUT(M6 σ / M7 β) class-A,
two_stage_ota_sf vout class-A, 두 push-pull 버퍼 vout push-pull.
oracle (a): 손 회로에 같은 규칙을 적용한 값. 값 이름은 DEC-65 기호의 영문 표기(beta·sigma·kappa)와 push_pull·class_a.
"""
from __future__ import annotations

import pytest

import s1v_hand as H


def _dir(v):
    return {o.net: (dict(o.charge), dict(o.discharge), o.topology) for o in v.output_direction}


def test_two_stage_miller(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    d = _dir(H.view(s1v))
    # out: 충전 M6(PMOS 신호 셀 σ), 방전 M7(gate vb 교류접지 β) -> 한 방향만 σ = class-A
    assert d["out"] == ({"M6": "sigma"}, {"M7": "beta"}, "class_a")
    # o1: 충전 M4(diode 묶음의 바이어스 전류원인데 gate x 가 신호 -> κ), 방전 M2(σ) -> class-A
    assert d["o1"] == ({"M4": "kappa"}, {"M2": "sigma"}, "class_a")


def test_push_pull_follower(tmp_path):
    _, s1v = H.build(tmp_path, H.PUSHPULL)
    # 충전 M1(NMOS CD, drain vdd), 방전 M2(PMOS CD, drain gnd), 둘 다 신호 셀 -> push-pull
    assert _dir(H.view(s1v))["out"] == ({"M1": "sigma"}, {"M2": "sigma"}, "push_pull")


def test_single_follower_is_class_a(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLLOWER)
    assert _dir(H.view(s1v))["out"] == ({"M1": "sigma"}, {"M2": "beta"}, "class_a")


def test_common_source_with_current_source_load(tmp_path):
    _, s1v = H.build(tmp_path, H.CS)
    assert _dir(H.view(s1v))["out"] == ({"M2": "beta"}, {"M1": "sigma"}, "class_a")


def test_cross_coupled_load_both_signal(tmp_path):
    _, s1v = H.build(tmp_path, H.XCOUP)
    # om: 충전 M3(gate op 신호, gs 묶음 없음 -> DC 역할 신호 σ), 방전 M1(σ)
    assert _dir(H.view(s1v))["om"] == ({"M3": "sigma"}, {"M1": "sigma"}, "push_pull")


def test_no_signal_direction_is_neither_class(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    charge, discharge, topology = _dir(H.view(s1v))["out"]
    # out: 충전 M6(캐스코드, gate vbc 교류접지 β), 방전 M8(미러 바이어스 전류원 + gate 신호 κ) -> σ 없음
    assert (charge, discharge) == ({"M6": "beta"}, {"M8": "kappa"})
    assert topology not in ("push_pull", "class_a")


@pytest.mark.parametrize("circuit,net,expected", [
    ("two_stage_ota", "OUT", ({"M6": "sigma"}, {"M7": "beta"}, "class_a")),
    ("two_stage_ota_sf", "vout", ({"M8": "sigma"}, {"M9": "beta"}, "class_a")),
    ("pushpull_follower_buffer", "vout", (None, None, "push_pull")),
    ("sf_pushpull_output_opamp", "vout", (None, None, "push_pull")),
])
def test_library_dec65_expectations(circuit, net, expected):
    _, s1v = H.build_lib(circuit)
    charge, discharge, topology = _dir(H.view(s1v))[net]
    exp_c, exp_d, exp_t = expected
    assert topology == exp_t
    if exp_c is not None:
        assert (charge, discharge) == (exp_c, exp_d)
