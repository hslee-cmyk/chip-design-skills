"""graph/loop_classify.py -- 루프 분류 (1.5) bias_scc / (2) miller / (3) loop_view / (4) record_only
(계약 10.2 '루프', 불변량 7·8, 설계 41 1.8, 계획 N3.2-2 분류 정의).

oracle (a)·(d) 손 유도:
- MILLER: 루프 o1 -> out -> Cc -> o1 은 커패시터를 포함한 수동소자 구간이 순방향 두 노드(out, o1)를 잇는다 -> (2) miller, 루프 뷰 없음.
- BIASSCC: p <-> q(Mp1/Mp2)는 순방향 노드(in, out)를 하나도 지나지 않는다 -> (1.5) bias_scc(DC 루프, 루프 뷰 없음).
- XCOUP: 순방향 능동 셀(M3·M4)만으로 닫힌 교차결합, 수동소자 없는 2능동셀 복귀 -> (4) record_only(계획 '교차결합' 예시) + 기록.
- RFB: 복귀 경로가 저항 Rf 뿐(배타 (가)) 이고 커패시터가 없어 (2) 아님 -> (4) record_only(계획 '저항 shunt 되먹임은 (4)').
- CMFB: 공통모드 되먹임(계획 (3) 예시 '공통모드 되먹임') -> loop_view, 루프 뷰를 만든다.

[U1b 2026-10-09] 설계 41 1.8 분류 순서에 (1.6) 복합 diode 내부(1.12.1-3)가 (1.5) 바로 뒤, (2) 앞에 들어간다: 사이클의 모든 원소가 한
복합 diode 묶음 안이면 `composite_diode_internal`(info), 루프 뷰 없음. (3-b) 배타 (나)('수동소자 없는 2능동셀 루프 -> 기록만')는
묶음 밖 루프에만 남는다(XCOUP 은 그대로 record_only).
"""
from __future__ import annotations

import jrules_hand as J
import s1v_hand as H


def _classes(v):
    return sorted(lp.classes for lp in v.loops)


def test_miller_compensation_loop(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    assert _classes(H.view(s1v)) == [("miller",)]
    assert "loop_record_only" not in H.all_codes(s1v)


def test_bias_scc_off_the_forward_path(tmp_path):
    _, s1v = H.build(tmp_path, H.BIASSCC)
    v = H.view(s1v)
    assert _classes(v) == [("bias_scc",)]
    assert not set(v.loops[0].nodes) & set(v.forward_nets)            # 불변량 7: bias_scc 는 순방향 노드를 지나지 않는다
    assert [x.kind for x in s1v.views] == ["transfer"]                # 루프 뷰를 만들지 않는다
    assert H.codes(v) == []


def test_cross_coupled_loop_is_record_only(tmp_path):
    _, s1v = H.build(tmp_path, H.XCOUP)
    v = H.view(s1v)
    assert _classes(v) == [("record_only",)]
    hits = [f for f in v.findings if f.code == "loop_record_only"]
    assert [(h.severity, h.subject) for h in hits] == [("unsupported_rule_branch", ("om", "op"))]


def test_resistor_shunt_feedback_is_record_only(tmp_path):
    _, s1v = H.build(tmp_path, H.RFB)
    assert _classes(H.view(s1v)) == [("record_only",)]
    assert "loop_record_only" in H.codes(H.view(s1v))


def test_common_mode_feedback_is_loop_view(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    assert _classes(H.view(s1v)) == [("loop_view",), ("loop_view",)]
    assert any(v.kind == "loop" for v in s1v.views)


def test_bias_scc_loop_is_dc_only_no_stop(tmp_path):
    _, s1v = H.build(tmp_path, H.BIASSCC, stop_on_unsupported=True)    # 정지하지 않는다
    assert s1v.unsupported == ()


def test_composite_internal_cycle_is_class_1_6(tmp_path):
    # SFLOAD 사이클 n1 -Mb-> n5 -R1-> n1: 원소 {Mb, R1} 이 묶음 {Ma, Mb, R1} 안 -> (1.6). (2)~(4) 이전에 확정되어 다른 분류가 없다
    _, s1v = H.build(tmp_path, J.SFLOAD)
    v = H.view(s1v)
    assert _classes(v) == [("composite_diode_internal",)]
    assert [(f.code, f.severity) for f in v.findings] == [("composite_diode_internal", "info")]
    assert "loop_record_only" not in H.all_codes(s1v)


def test_two_active_cell_loop_outside_bundles_stays_record_only(tmp_path):
    # XCOUP 의 M3·M4 는 복합 diode 가 아니다(drain om·op 가 포트) -> 묶음 밖 -> (나) 유지
    _, s1v = H.build(tmp_path, H.XCOUP)
    assert _classes(H.view(s1v)) == [("record_only",)]


def test_library_sf_record_only_loops_become_composite_internal():
    # 41 1.13 '1.12.1 -> 루프 분류' 행: sf 의 복합 diode 루프가 record_only 에서 composite_diode_internal 로, 루프 뷰 0
    _, s1v = H.build_lib("sf_pushpull_output_opamp")
    v = H.view(s1v)
    assert v.loops and {lp.classes for lp in v.loops} == {("composite_diode_internal",)}
    assert [x.kind for x in s1v.views] == ["transfer"]
