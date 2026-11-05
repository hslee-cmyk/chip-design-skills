"""graph/views.py -- 뷰 수집(계약 graph CONTRACT 10.2 '뷰 수집', 설계 41 1.1, 계획 N3.2-2).

oracle (a): 손 회로의 포트 role 선언만으로 정답이 정해진다 -- 차동 p·n 입력 한 쌍이면 가중 ±1/2 기모드 여기 하나,
아니면 입력 포트마다 단일 여기, 관측 = 출력 포트 전부, 뷰 id = `transfer:<순번>`(여기 이름 정렬 순)·`loop:<소자>:<gate 넷>`.
oracle (d): library spec 의 sense 전용 제약(rout_ss_ohm)은 구조 뷰를 만들지 않는다(계약 10.2 'mode sense·none·pending').
"""
from __future__ import annotations

from pathlib import Path

import pytest

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.graph import build_s1, build_s1v
from gmid_engine.metrics import metric_catalog

import s1v_hand as H

LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"


def test_differential_input_pair_gives_one_half_weight_view(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    # oracle (a): 차동 p(inp)·n(inn) 한 쌍 -> 기모드 여기 하나, 가중 +1/2(p)·-1/2(n), 관측 = 유일한 출력 포트 out
    assert [v.id for v in s1v.views] == ["transfer:0"]
    v = H.view(s1v)
    assert v.kind == "transfer"
    assert v.excite == (("inn", -0.5), ("inp", 0.5))
    assert v.sense == ("out",)


def test_sense_is_every_output_port(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    # oracle (a): 출력 포트 op·om 둘 다 관측(이름순)
    assert H.view(s1v).sense == ("om", "op")


def test_single_ended_inputs_give_one_view_each_in_name_order(tmp_path):
    _, s1v = H.build(tmp_path, H.REPLICA_SE)
    # oracle (a): 입력 포트 in1·in2 는 차동 role 이 아니다 -> 입력마다 단일 여기(가중 1), 순번은 여기 이름 정렬 순
    transfer = [v for v in s1v.views if v.kind == "transfer"]
    assert [(v.id, v.excite, v.sense) for v in transfer] == [
        ("transfer:0", (("in1", 1.0),), ("om", "op")),
        ("transfer:1", (("in2", 1.0),), ("om", "op")),
    ]


def test_single_input_circuit_single_excitation(tmp_path):
    _, s1v = H.build(tmp_path, H.CS)
    assert [(v.id, v.excite, v.sense) for v in s1v.views] == [("transfer:0", (("in", 1.0),), ("out",))]


def test_loop_view_id_excite_and_sense_are_the_cut_gate(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    # oracle (a): CMFB 루프 cm -> cmfb(M5 gate->drain) -> om/op(M3/M4) -> cm(R1/R2) 의 끊는 점 = (M5, cm)
    # (test_loop_cuts 손 유도) -> 루프 뷰 id `loop:M5:cm`, 여기·감지 = 끊은 gate 넷 cm(ViewSeed docstring)
    # 계약 10.2 '순서': 전달 뷰 다음 그 루프가 만든 루프 뷰
    assert [v.id for v in s1v.views] == ["transfer:0", "loop:M5:cm"]
    loop = H.view(s1v, "loop:M5:cm")
    assert loop.kind == "loop"
    assert tuple(n for n, _ in loop.excite) == ("cm",)
    assert loop.sense == ("cm",)


def test_no_loop_view_without_loop_view_loops(tmp_path):
    # oracle (a): Miller 루프(o1->out->Cc->o1)는 (2) 분류라 루프 뷰를 만들지 않는다(41 1.1 '루프 뷰: 1.8 의 (3) 루프마다')
    _, s1v = H.build(tmp_path, H.MILLER)
    assert [v.kind for v in s1v.views] == ["transfer"]


def test_sense_only_spec_constraints_make_no_extra_view():
    # oracle (d): pushpull_follower_buffer spec 의 rout_ss_ohm 은 감지 전용(output_port -> mode sense) -- 구조 뷰를 만들지 않아
    # spec 을 줘도 기본 전달 뷰 하나(입력 vin 단일 여기, 출력 vout)뿐이다.
    path = LIBRARY / "pushpull_follower_buffer.topology.json"
    doc = load_topology(str(path))
    spec = load_sizing_spec(str(LIBRARY / "pushpull_follower_buffer.sizing_spec.json"), doc, metric_catalog())
    run = H.fresh_run()                    # [XRUN-F1 card B C6] S1·S1v = 실행 하나
    s1 = build_s1(doc, H.lib_supplies("pushpull_follower_buffer"), **run)
    with_spec = H.read_s1v(build_s1v(s1, spec, count_budget=H.BIG_BUDGET, stop_on_unsupported=False, **run))
    assert [(v.id, v.kind, v.excite, v.sense) for v in with_spec.views] == [
        ("transfer:0", "transfer", (("vin", 1.0),), ("vout",))]


@pytest.mark.parametrize("doc", [H.OTA5, H.CMFB, H.REPLICA_SE, H.FOLDED], ids=lambda d: d["topology_name"])
def test_view_ids_unique_transfer_views_first_in_number_order(tmp_path, doc):
    # 계약 10.2 '순서'(전달 뷰 -> 루프 뷰)와 뷰 id 형식 `transfer:<순번>`(0 부터)
    _, s1v = H.build(tmp_path, doc)
    ids = [v.id for v in s1v.views]
    assert len(set(ids)) == len(ids)
    n = sum(1 for v in s1v.views if v.kind == "transfer")
    assert ids[:n] == ["transfer:%d" % i for i in range(n)]
    assert all(v.kind == "loop" and v.id.startswith("loop:") for v in s1v.views[n:])


# ---------------------------------------------------------------- [IT-2c T-S1V] 기본 포트 뷰 (`default_port`)
# interface 20261104-it2c-icm-config 'S1v 기본 포트 뷰': 입력 둘이 differential_input_p/_n 한 쌍이면 뷰 하나(p +1/2, n −1/2, 감지 = 출력 넷 전부), 그 밖은 입력
# 포트마다 뷰 하나(여기 가중 1, 감지 = 출력 넷 전부). 기본 포트 뷰 키 집합 안의 뷰는 `default_port == True`. 전달 뷰 순서 = 키 정렬.
# oracle: (손) 위 규칙을 손 회로(OTA5·CS·REPLICA_SE·CMFB)에 적용한 리터럴. spec 없음(선언 뷰 없음).

def test_it2c_default_port_diff_pair_view_is_flagged(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    v = H.view(s1v)
    assert (v.excite, v.sense) == ((("inn", -0.5), ("inp", 0.5)), ("out",))
    assert v.default_port is True


def test_it2c_default_port_single_ended_inputs_one_view_each_flagged(tmp_path):
    _, s1v = H.build(tmp_path, H.REPLICA_SE)
    transfer = [v for v in s1v.views if v.kind == "transfer"]
    assert [(v.excite, v.sense, v.default_port) for v in transfer] == [
        ((("in1", 1.0),), ("om", "op"), True),
        ((("in2", 1.0),), ("om", "op"), True),
    ]


def test_it2c_default_port_single_input_cs_flagged(tmp_path):
    _, s1v = H.build(tmp_path, H.CS)
    assert [(v.excite, v.sense, v.default_port) for v in s1v.views] == [((("in", 1.0),), ("out",), True)]


def test_it2c_default_port_false_for_loop_views(tmp_path):
    """oracle 대조: (손) 루프 뷰 `loop:M5:cm` 의 키(여기 = 끊은 gate 넷)는 기본 포트 뷰 키 집합 밖이라 default_port == False, 전달 뷰는 True."""
    _, s1v = H.build(tmp_path, H.CMFB)
    assert H.view(s1v, "transfer:0").default_port is True
    assert H.view(s1v, "loop:M5:cm").default_port is False
