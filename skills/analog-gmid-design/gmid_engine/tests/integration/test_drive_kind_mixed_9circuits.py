"""혼재 노드 구동 종류 9회로 발동표 -- 설계 41 v1.8 §1.5-4 C-1 + 보완 (가)(사용자 결정 2026-10-12 "7절 권고대로"·"1, 가로 해"), 41 §9 표 행
'혼재 노드 구동 종류', 40 §10.2.

규칙(41 §1.5-4): 혼재 노드(한 소자의 drain 과 다른 소자의 source 가 만나는 노드)에서 (i) source 쪽 소자 drain 이 교류 접지(레일)이고 gate 가 그 뷰의
신호 노드면 follower -> 전압(`follower`), (ii) 아니면 drain 쪽 소자 gate 가 신호 노드면 전류(`cascode`), 아니면 전압. 옛 규칙 4 는 혼재 노드를
늘 전압(신호 drain 이면 review 기록)으로 두었으므로 '옛 판정' = 전압이고, '바뀐 키' = 새 판정이 전류인 (회로, view_key, 노드)다.

발동표(oracle (a) -- topology 연결표 손 유도, 비교 키 (회로, view_key, 노드)):
| 회로 | 노드 | drain 쪽(gate) | source 쪽(drain, gate) | 새 판정(근거) |
|---|---|---|---|---|
| sf_pushpull_output_opamp | N910 | M9(N5: R1a 로 N1 과 이어진 신호 넷) | M10(Y, N1) -- drain Y 레일 아님 | 전류(cascode) |
| sf_pushpull_output_opamp | N1112 | M11(N7: R1b 로 N2) | M12(N12, N2) | 전류(cascode) |
| sf_pushpull_output_opamp | N1516 | M16(N13: R1c 로 N12) | M15(Y, N12) | 전류(cascode) |
| sf_pushpull_output_opamp | N17 | M17(N5) | M18(vss 레일, Y 신호) | 전압(follower) -- 유지 |
| sf_pushpull_output_opamp | N20 | M20(N13) | M19(vdd 레일, Y 신호) | 전압(follower) -- 유지 |
| folded_cascode | Vg10 | M10(Vg9: 미러 입력, 신호) | M8(out, Vg7 신호) -- drain out 레일 아님 | 전류(cascode) |
| 나머지 회로·노드 | -- | -- | -- | 무동작(전압 유지) |
sf 의 N56·N78·N1314 는 복합 diode 묶음 내부 넷이라 혼재 판정 대상이 아니다(41 §1.12.1-2, §1.4-1). 꼬리 노드(TAIL·tail·Vy 등)는 꼬리 전류원이 순방향
셀이 아니라(off) 혼재가 아니다.
folded_cascode 판정 하나(41 §1.5-4 측정 의무 (2)): Vg10 이 전류 구동이 되어 M8 은 stage 시작 셀이 아니다(§1.6).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

GRAPH_TESTS = Path(__file__).resolve().parents[1] / "graph"
if str(GRAPH_TESTS) not in sys.path:
    sys.path.insert(0, str(GRAPH_TESTS))

import s1v_hand as H  # noqa: E402

NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
        "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")
MIXED_BASES = ("follower", "cascode", "mixed_bias_drain")      # 혼재 판정이 낸 근거(41 §1.5-4 (i)·(ii)·그 밖)
CHANGED = {("sf_pushpull_output_opamp", "N910"), ("sf_pushpull_output_opamp", "N1112"), ("sf_pushpull_output_opamp", "N1516"),
           ("folded_cascode", "Vg10")}
FOLLOWER_KEPT = {("sf_pushpull_output_opamp", "N17"), ("sf_pushpull_output_opamp", "N20")}


def _mixed_rows():
    rows = []
    for name in NINE:
        _, s1v = H.build_lib(name)
        for v in s1v.views:
            for i in v.drive_kind:
                if i.basis in MIXED_BASES:
                    rows.append((name, v.id, i.net, i.kind, i.basis))
    return rows


@pytest.fixture(scope="module")
def rows():
    return _mixed_rows()


def test_changed_keys_are_exactly_expected_set(rows):
    changed = {(c, n) for c, _v, n, kind, _b in rows if kind == "current"}
    assert changed == CHANGED


def test_expected_nodes_change_in_every_view_where_mixed(rows):
    for circuit, net in CHANGED:
        hits = [r for r in rows if (r[0], r[2]) == (circuit, net)]
        assert hits, (circuit, net)                                          # 그 노드가 혼재로 판정되는 뷰가 있다
        assert all((kind, basis) == ("current", "cascode") for _c, _v, _n, kind, basis in hits), hits


def test_followers_kept_voltage(rows):
    for circuit, net in FOLLOWER_KEPT:
        hits = [r for r in rows if (r[0], r[2]) == (circuit, net)]
        assert hits, (circuit, net)
        assert all((kind, basis) == ("voltage", "follower") for _c, _v, _n, kind, basis in hits), hits


def test_other_mixed_nodes_unchanged_voltage(rows):
    others = [r for r in rows if (r[0], r[2]) not in CHANGED]
    assert all(kind == "voltage" for _c, _v, _n, kind, _b in others), others
    assert {c for c, *_ in rows} <= {"sf_pushpull_output_opamp", "folded_cascode", "current_reuse_telescopic_ota"}


@pytest.mark.parametrize("name", NINE)
def test_no_old_mixed_review_codes(name):
    _, s1v = H.build_lib(name)
    assert not {"mixed_drive_signal_drain", "mixed_drive_unresolved_group"} & set(H.all_codes(s1v))


def test_folded_m8_is_not_stage_start():
    _, s1v = H.build_lib("folded_cascode")
    views = [v for v in s1v.views if any(i.net == "Vg10" and i.basis in MIXED_BASES for i in v.drive_kind)]
    assert views
    for v in views:
        assert "M8" not in v.stage_starts, (v.id, v.stage_starts)
