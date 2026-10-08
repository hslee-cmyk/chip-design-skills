"""graph/coupling_vars.py -- GB3 결합 변수 y K1·K2·K3·K4·K7·K8 (U10, 설계 40 §3.3, 계획 DEC-71 (2)(7), D-GB3).

판정 기준(정본 순서):
- 설계 40 §3.3 본문: K1 부하 소자가 다른 블록의 미러·L 동치류에 속함 / K2 블록을 가로지르는 equal_vgs / K3 블록 경계를 넘는
  stacked_vsb / K4 공유 가지·기둥의 노드전압 / K7 여러 뷰가 공유하는 소자 / K8 측면 주입.
- 설계 40 §3.3 'U10 as-built 보완'(master 6707424, 이 worktree base 뒤 커밋):
  (i) 바이어스 기둥 = K1·K2·K4 판정의 의사 블록 `bias:<기둥>`(예 sf M3<->M4, ngcc M6A<->M7)
  (ii) K3 = 비레일 넷에서 MOS e 의 drain 과 MOS d 의 source 가 만나고 둘의 블록이 다름, 9회로 0건
  (iii) K7 은 동작점이 있는 소자(MOS)만 -- 커패시터·저항은 세지 않는다 (iv) 레코드 `nets`.
- interface(graph CONTRACT 11.3): 횡단 = 한 뷰 안에서 블록이 있는 소자 둘 이상의 블록 키 합집합 != 교집합, kind 별 domain·init_rule 표,
  vars 는 (kind, members, nets, domain) 순·중복 없음, K1 은 부하 역할 멤버가 횡단 블록에 있을 때.
- 설계 40 §3.3 as-built 보완(master 21bde21, 오케스트레이터 결정 2026-10-09): K1 부하 역할 = {load, mirror, diode_load, tail_source}
  (실제·의사 블록에 같게), 의사 블록 표현 = `BlockRef(view, ("bias:<기둥 id>",))`, 뷰마다 하나.

oracle 종류:
- (a) 손 회로(`s1v_hand`·`coupling_hand`) 기대 레코드는 위 정의를 손으로 적용한 리터럴. 각 test 주석에 유도를 적는다.
- (b) library 9회로는 `coupling_oracle.CouplingOracle`(S1·S1v 공개 필드에서 설계 정의를 집합 연산으로 다시 세운 독립 구현) 대조와,
  그 oracle 산출을 손으로 확인한 kind 수 표(리터럴).
- 불변식: 이름 전단사 + netlist 순서 섞기에 결과가 사상으로만 바뀐다, 같은 입력·다른 PYTHONHASHSEED 에서 같다.

base 57e81fb 는 (i)(iii)을 아직 구현하지 않았다 -- 그 기준의 test 는 설계대로 적고 red 로 둔다(코드 결함, auditor 판정).
21bde21 의 K1 tail_source 결정으로 test_side_injection_k8·kind 수 표 리터럴을 다시 유도했다(정의 변경, 기준 완화 아님).
"""
from __future__ import annotations

import collections
import os
import subprocess
import sys
from pathlib import Path

import pytest

import coupling_hand as C
import coupling_oracle as O
import s1v_hand as H
from gmid_engine.core import fp_of
from gmid_engine.graph import BlockRef, coupling_vars

T0 = "transfer:0"
# interface 11.3 표: kind -> (domain 후보, init_rule)
KIND_TABLE = {
    "K1": ({"dc", "geom"}, "class_owner_value"),
    "K2": ({"dc"}, "common_vgs_candidates"),
    "K3": ({"dc"}, "stack_node_kvl"),
    "K4": ({"dc"}, "shared_node_kvl_kcl"),
    "K7": ({"dc"}, "view_shared_split"),
    "K8": ({"dc"}, "side_injection_current"),
}


def recs(cpl):
    return sorted((C.rec(v) for v in cpl.vars), key=repr)


def by_key(cpl):
    return {(v.kind, tuple(v.members), v.domain): v for v in cpl.vars}


# ---------------------------------------------------------------- (a) 손 회로
def test_single_block_has_no_coupling(tmp_path):
    # 5T OTA: 모든 소자가 블록 out 하나 -> 횡단 없음, 뷰 하나 -> K7 없음, 측면 주입 구조 없음 (무동작 증거)
    s1, s1v = H.build(tmp_path, H.OTA5)
    assert coupling_vars(s1, s1v).vars == ()


def test_miller_k1_k2_across_stages(tmp_path):
    s1, s1v = H.build(tmp_path, H.MILLER)
    cpl = coupling_vars(s1, s1v)
    # 손 유도: 꼬리 M5(블록 o1, tail_source) 와 2단 전류원 M7(블록 out, load) 이 같은 (vb, gnd) gs 묶음
    #  -> mirror 그룹 {M5,M7}: 블록 o1/out 횡단 + 부하 역할 M7 -> K1 dc; L 동치류 {M5,M7} -> K1 geom; equal_vgs -> K2 nets (vb, gnd).
    #  {M3,M4} 미러는 둘 다 o1 -> 없음. 기둥 {M5,M2,M4}·{M5,M1,M3}·{M7,M6} 은 각자 한 블록 -> K4 없음. 뷰 하나 -> K7 없음.
    #  비레일 drain=source 접점(tail: M5 d / M1·M2 s, x·o1·out 은 source 없음)은 같은 블록 -> K3 없음.
    assert recs(cpl) == sorted([
        ("K1", ("M5", "M7"), "dc", "class_owner_value", ()),
        ("K1", ("M5", "M7"), "geom", "class_owner_value", ()),
        ("K2", ("M5", "M7"), "dc", "common_vgs_candidates", ("vb", "gnd")),
    ], key=repr)
    for v in cpl.vars:
        assert C.real_blocks(v) == {(T0, ("o1",)), (T0, ("out",))}


def test_stack_k3_and_k4(tmp_path):
    s1, s1v = H.build(tmp_path, C.STACK)
    v = H.view(s1v)
    # 전제(S1v 블록, 입력 데이터): M1·M2 는 블록 a, M3·M4·M5 는 블록 out
    owner = {d: k for b in v.blocks for d, _r in b.roles for k in [b.key]}
    assert (owner["M1"], owner["M2"], owner["M3"], owner["M4"], owner["M5"]) == (("a",), ("a",), ("out",), ("out",), ("out",))
    cpl = coupling_vars(s1, s1v)
    # 손 유도:
    #  K3: 비레일 넷 s 에서 M5 drain 과 M2 source 가 만남, 블록 out != a -> (e, d) = (M5, M2), nets (s,).
    #      같은 s 의 M3 source 는 M5 와 같은 블록 -> 없음. 넷 a 의 M1/M2 drain 에 source 없음.
    #  K4: 가지 M5(gnd-s) 를 지나는 기둥 {M5,M2,M1}·{M5,M3,M4} 의 소자 블록 = a·out -> 횡단, members (M5,), nets {gnd, s}.
    #      가지 M2-M1(s-vdd) 의 기둥 {M5,M2,M1} -> a·out 횡단 -> members (M1, M2), nets {s, vdd}.
    #      가지 M3-M4(s-vdd) 의 기둥 {M5,M3,M4} -> out 하나 -> 없음.
    #  equal_vgs·미러·L 동치류 없음(gs 묶음 없음) -> K1·K2 없음. 뷰 하나 -> K7 없음.
    assert recs(cpl) == sorted([
        ("K3", ("M5", "M2"), "dc", "stack_node_kvl", ("s",)),
        ("K4", ("M1", "M2"), "dc", "shared_node_kvl_kcl", frozenset({"s", "vdd"})),
        ("K4", ("M5",), "dc", "shared_node_kvl_kcl", frozenset({"gnd", "s"})),
    ], key=repr)
    for rv in cpl.vars:
        assert C.real_blocks(rv) == {(T0, ("a",)), (T0, ("out",))}


def test_side_injection_k8(tmp_path):
    s1, s1v = H.build(tmp_path, C.SIDE)
    cpl = coupling_vars(s1, s1v)
    # 손 유도:
    #  K8: Mc = DC 바이어스 전류원(복합 diode M6 의 (q, vdd) 묶음), 셀 CS(gate q 신호), drain n. n 에 CD Ms(gate y) 의 source.
    #      y 에서 CD 엣지(y->n Ms, n->out Mf)로 q 에 닿지 않음, n 은 이득 블록(y) 출력 아님 -> (Mc, Ms), nets (n,).
    #  K1·K2 (M6, M9, Mc): M6(diode_load)·M9(load) 는 블록 y, Mc 는 블록 밖이고 기둥 {Mc, Ms} 의 Ms 가 버퍼 블록 out -> 기둥 이웃으로 out.
    #      y/out 횡단 + 부하 역할 -> K1 dc(mirror 그룹)·K1 geom(L 동치류), equal_vgs -> K2 nets (q, vdd).
    #  K1·K2 (M0, Mk): 꼬리 M0(블록 y, tail_source) / Mk(블록 밖, 기둥 {Mk, Mf} 의 Mf 가 out -> 기둥 이웃으로 out) -> y/out 횡단.
    #      S1 mirror 그룹 {M0, Mk}(같은 (vb, gnd) gs 묶음)·L 동치류 {M0, Mk} + 부하 역할 tail_source(21bde21) -> K1 dc·geom,
    #      equal_vgs -> K2 nets (vb, gnd).
    #  K3: n 에서 Mc drain / Ms source 지만 Mc 는 블록 멤버가 아니다 -> 없음. K4: 각 기둥이 한 블록 -> 없음.
    assert recs(cpl) == sorted([
        ("K1", ("M0", "Mk"), "dc", "class_owner_value", ()),
        ("K1", ("M0", "Mk"), "geom", "class_owner_value", ()),
        ("K1", ("M6", "M9", "Mc"), "dc", "class_owner_value", ()),
        ("K1", ("M6", "M9", "Mc"), "geom", "class_owner_value", ()),
        ("K2", ("M0", "Mk"), "dc", "common_vgs_candidates", ("vb", "gnd")),
        ("K2", ("M6", "M9", "Mc"), "dc", "common_vgs_candidates", ("q", "vdd")),
        ("K8", ("Mc", "Ms"), "dc", "side_injection_current", ("n",)),
    ], key=repr)
    k8 = by_key(cpl)[("K8", ("Mc", "Ms"), "dc")]
    assert C.real_blocks(k8) == {(T0, ("out",))}            # interface: K8 blocks = 소자의 모든 블록(Ms 의 out)


def test_k7_counts_mos_shared_by_views(tmp_path):
    s1, s1v = H.build(tmp_path, H.CMFB)
    assert [v.id for v in s1v.views] == [T0, "loop:M5:cm"]   # 전제: 전달 뷰 + CMFB 루프 뷰
    cpl = coupling_vars(s1, s1v)
    ecls = dict(s1.column("device", "element_class"))
    k7 = {v.members: v for v in cpl.vars if v.kind == "K7" and all(ecls[m] == "mos" for m in v.members)}
    # 손 유도: 두 뷰 블록에 함께 있는 MOS = M1·M2(입력/부하)·M3·M4(부하/미러). M0 은 전달 뷰만, M5~M8 은 루프 뷰만.
    # (수동소자 K7 은 아래 별도 test -- 여기서는 MOS 레코드만 본다)
    assert sorted(k7) == [("M1",), ("M2",), ("M3",), ("M4",)]
    for v in k7.values():
        assert C.real_blocks(v) == {(T0, ("om", "op")), ("loop:M5:cm", ("om", "op"))}


def test_k7_excludes_shared_resistors(tmp_path):
    # 설계 as-built (iii): K7 은 MOS 만. R1·R2 는 두 뷰 블록의 부하지만 값이 뷰마다 같아 나눌 것이 없다.
    s1, s1v = H.build(tmp_path, H.CMFB)
    members = {v.members for v in coupling_vars(s1, s1v).vars if v.kind == "K7"}
    assert ("R1",) not in members and ("R2",) not in members


def test_k7_excludes_shared_capacitor(tmp_path):
    s1, s1v = H.build(tmp_path, C.CMFB_C)
    # 전제: Cx 는 두 뷰의 블록 멤버
    assert all("Cx" in dict(b.roles) for v in s1v.views for b in v.blocks)
    k7 = sorted(v.members for v in coupling_vars(s1, s1v).vars if v.kind == "K7")
    assert k7 == [("M1",), ("M2",), ("M3",), ("M4",)]       # Cx·R1·R2 없음 (as-built (iii))


def test_bias_column_pseudo_block_k1_k2(tmp_path):
    s1, s1v = H.build(tmp_path, C.BCS)
    bias = C.column_id(s1, {"Mi", "Mr"})
    cpl = coupling_vars(s1, s1v)
    # 손 유도(as-built (i)): 기준 diode Mr 는 바이어스 기둥 {Mi, Mr} = 의사 블록 bias:<그 기둥>. 부하 M2 는 블록 out.
    #  equal_vgs {M2, Mr}(vbp, vdd) -> out / bias 횡단 -> K2. L 동치류 {M2, Mr} + 부하 역할 M2 -> K1 geom.
    #  mirror matching 그룹은 S1 에 없다(gate vbp 가 바이어스 넷이라 bias_distribution 처리) -> K1 dc 없음.
    #  K4: 가지 M1-M2·Mi-Mr 각각 한 기둥, 한 (의사)블록 -> 없음.
    assert recs(cpl) == sorted([
        ("K1", ("M2", "Mr"), "geom", "class_owner_value", ()),
        ("K2", ("M2", "Mr"), "dc", "common_vgs_candidates", ("vbp", "vdd")),
    ], key=repr)
    for v in cpl.vars:
        assert C.real_blocks(v) == {(T0, ("out",))}
        assert C.mentions_bias_column(v, bias), v.blocks


def test_bias_columns_sharing_a_branch_k4(tmp_path):
    s1, s1v = H.build(tmp_path, C.BIASNET)
    ca, cb = C.column_id(s1, {"Mt", "Ma"}), C.column_id(s1, {"Mt", "Mb", "Mc"})
    cpl = coupling_vars(s1, s1v)
    # 손 유도(as-built (i) K4): 바이어스 기둥 둘 A={Mt,Ma}, B={Mt,Mb,Mc} 가 가지 Mt(gnd-t) 를 공유.
    #  가지 Mt: 기둥 A·B 소자 -> Mt{A,B}, Ma{A}, Mb·Mc{B} -> 합집합 != 교집합 -> K4 (Mt,) nets {gnd, t}.
    #  가지 Ma(t-vdd): 기둥 A 소자 Mt{A,B}·Ma{A} -> 횡단 -> K4 (Ma,) nets {t, vdd}.
    #  가지 Mb-Mc(t-vdd): 기둥 B 소자 Mt{A,B}·Mb,Mc{B} -> 횡단 -> K4 (Mb, Mc) nets {t, vdd}.
    #  신호 기둥 {M1, M2} 는 블록 out 하나 -> 없음. gs 묶음 없음 -> K1·K2 없음.
    assert recs(cpl) == sorted([
        ("K4", ("Ma",), "dc", "shared_node_kvl_kcl", frozenset({"t", "vdd"})),
        ("K4", ("Mb", "Mc"), "dc", "shared_node_kvl_kcl", frozenset({"t", "vdd"})),
        ("K4", ("Mt",), "dc", "shared_node_kvl_kcl", frozenset({"gnd", "t"})),
    ], key=repr)
    mt = by_key(cpl)[("K4", ("Mt",), "dc")]
    assert C.mentions_bias_column(mt, ca) and C.mentions_bias_column(mt, cb)


def test_bias_pseudo_block_key_format(tmp_path):
    # 설계 as-built(21bde21)·CONTRACT 11.1: 의사 블록 = BlockRef(view, ("bias:<기둥 id>",)), 기둥 id 는 S1 기둥 id 그대로, 뷰마다 하나.
    # 손 유도(BCS): 바이어스 기둥은 {Mi, Mr} 하나 -> 의사 블록 키 ("bias:<그 기둥>",). K1 geom·K2 의 blocks = {out, 의사 블록} 정확히.
    s1, s1v = H.build(tmp_path, C.BCS)
    bias = C.column_id(s1, {"Mi", "Mr"})
    cpl = coupling_vars(s1, s1v)
    assert cpl.column_block_map.bias_columns == (bias,)
    want = (BlockRef(T0, ("bias:%s" % (bias,),)), BlockRef(T0, ("out",)))
    assert len(cpl.vars) == 2
    for v in cpl.vars:
        assert set(v.blocks) == set(want), v
        assert tuple(v.blocks) == tuple(sorted(want)), v      # interface 11.1: blocks 정렬
    # 매핑표 행의 block 은 바이어스 기둥이면 None 그대로(CONTRACT 11.1)
    assert {(r.device, r.block, r.basis) for r in cpl.column_block_map.rows if r.column == bias} == {
        ("Mi", None, "bias_column"), ("Mr", None, "bias_column")}


def test_bias_pseudo_block_one_per_view(lib):
    # CONTRACT 11.1: '의사 블록은 모든 뷰에 기둥마다 하나씩' + 11.3 'blocks = 횡단이 일어난 뷰들의 횡단 블록'.
    # 손 유도(current_reuse_telescopic_ota topology + S1v 블록): M6(gate Vbias1, tail_source)는 전달 뷰 블록 (Vom1, Vop1) 과
    # 루프 뷰 loop:M37a:Voc 블록 (N1a2a, N1b2b) 의 멤버, 기준 diode M18_bg 는 바이어스 기둥 {Iref, M18_bg} -> 두 뷰 모두 횡단 ->
    # K1 dc (M18_bg, M6) blocks = 두 뷰 각각의 (실제 블록, 의사 블록) 넷.
    s1, s1v = lib["current_reuse_telescopic_ota"]
    bias = C.column_id(s1, {"Iref", "M18_bg"})
    pk = ("bias:%s" % (bias,),)
    hit = [v for v in coupling_vars(s1, s1v).vars if v.kind == "K1" and v.domain == "dc" and v.members == ("M18_bg", "M6")]
    assert len(hit) == 1
    assert set(hit[0].blocks) == {BlockRef(T0, ("Vom1", "Vop1")), BlockRef(T0, pk),
                                  BlockRef("loop:M37a:Voc", ("N1a2a", "N1b2b")), BlockRef("loop:M37a:Voc", pk)}


def test_tail_mirrored_from_bias_diode_is_k1(tmp_path):
    # 21bde21 결정: 바이어스 의사 블록에서 미러로 전류를 받는 꼬리 전류원도 K1.
    # 손 회로: 5T OTA(M1/M2 입력, M3/M4 PMOS 미러 부하, 꼬리 M5 gate nb) + 바이어스 기둥 {Mr, Mi}: 기준 diode Mr(nb-nb-gnd) + 전류원 Mi(gate vbp).
    s1, s1v = H.build(tmp_path, C.TAILREF)
    bias = C.column_id(s1, {"Mi", "Mr"})
    v = H.view(s1v)
    roles = {d: r for b in v.blocks for d, r in b.roles}
    assert [b.key for b in v.blocks] == [("out",)] and roles["M5"] == "tail_source" and "Mr" not in roles   # 전제(S1v)
    cpl = coupling_vars(s1, s1v)
    # 손 유도: Mr 는 바이어스 기둥 = 의사 블록 bias:<기둥>, M5 는 블록 out 의 tail_source -> {M5, Mr} 횡단.
    #  (nb, gnd) gs 묶음 -> mirror 그룹·L 동치류 {M5, Mr} + 부하 역할 tail_source -> K1 dc·geom, equal_vgs -> K2 nets (nb, gnd).
    #  {M3, M4} 는 둘 다 out -> 없음. 기둥 {M5,M1,M3}·{M5,M2,M4} 는 out 하나, {Mr,Mi} 는 의사 블록 하나 -> K4 없음. 뷰 하나 -> K7 없음.
    #  횡단 블록 안 멤버 역할은 tail_source 뿐 -> 옛 집합(load·mirror·diode_load)이면 K1 이 없었다(K1 의 근거가 tail_source 임).
    assert recs(cpl) == sorted([
        ("K1", ("M5", "Mr"), "dc", "class_owner_value", ()),
        ("K1", ("M5", "Mr"), "geom", "class_owner_value", ()),
        ("K2", ("M5", "Mr"), "dc", "common_vgs_candidates", ("nb", "gnd")),
    ], key=repr)
    for rv in cpl.vars:
        assert set(rv.blocks) == {BlockRef(T0, ("out",)), BlockRef(T0, ("bias:%s" % (bias,),))}


def test_bias_columns_k4_blocks_are_pseudo_only(tmp_path):
    # 두 바이어스 기둥이 가지를 공유하는 K4 (as-built (i)): blocks 는 의사 블록 둘뿐, 실제 블록 없음.
    # 손 유도(BIASNET): 가지 Mt(gnd-t) 를 기둥 A={Mt,Ma}·B={Mt,Mb,Mc} 가 지난다 -> blocks = {bias:A, bias:B}.
    #  가지 Ma 의 기둥 A 소자 Mt{A,B}·Ma{A} -> 횡단 블록 {A, B}. 가지 Mb-Mc 도 {A, B}.
    s1, s1v = H.build(tmp_path, C.BIASNET)
    ca, cb = C.column_id(s1, {"Mt", "Ma"}), C.column_id(s1, {"Mt", "Mb", "Mc"})
    cpl = coupling_vars(s1, s1v)
    assert set(cpl.column_block_map.bias_columns) == {ca, cb}
    want = {BlockRef(T0, ("bias:%s" % (ca,),)), BlockRef(T0, ("bias:%s" % (cb,),))}
    k4 = [v for v in cpl.vars if v.kind == "K4"]
    assert len(k4) == 3
    for v in k4:
        assert set(v.blocks) == want, v


@pytest.mark.parametrize("doc", [H.OTA5, H.MILLER, H.CMFB, C.STACK, C.SIDE, C.BCS, C.BIASNET, C.MATE, H.FOLDED, H.REPLICA, C.TAILREF],
                         ids=lambda d: d["topology_name"])
def test_hand_circuits_match_oracle(tmp_path, doc):
    # 손 회로 전부에서 (b) oracle 과 레코드 키가 같다(손 리터럴과 oracle 의 교차 확인 포함)
    s1, s1v = H.build(tmp_path, doc)
    assert O.engine_records(coupling_vars(s1, s1v)) == O.CouplingOracle(s1, s1v).records()


# ---------------------------------------------------------------- 형식 불변식
def _all_inputs(tmp_path):
    for doc in (H.MILLER, H.CMFB, C.STACK, C.SIDE, C.BCS, C.BIASNET):
        yield doc["topology_name"], H.build(tmp_path, doc)
    for name in C.NINE:
        yield name, H.build_lib(name)


def test_vars_sorted_unique_and_table_vocabulary(tmp_path):
    for name, (s1, s1v) in _all_inputs(tmp_path):
        cpl = coupling_vars(s1, s1v)
        keys = [(v.kind, tuple(v.members), tuple(v.nets), v.domain) for v in cpl.vars]
        assert keys == sorted(keys), name                      # interface 11.1: (kind, members, nets, domain) 순
        assert len(set(keys)) == len(keys), name              # 같은 키 중복 없음
        for v in cpl.vars:
            doms, rule = KIND_TABLE[v.kind]
            assert v.domain in doms and v.init_rule == rule, (name, v)
            assert len(v.members) >= 1 and v.blocks, (name, v)
            assert tuple(v.blocks) == tuple(sorted(v.blocks)), (name, v)
            if v.kind in ("K1", "K2", "K3", "K4") and not any("bias:" in repr(b) for b in v.blocks):
                assert len(C.real_blocks(v)) >= 2, (name, v)  # 경계 횡단: 서로 다른 블록 둘 이상


# ---------------------------------------------------------------- (b) library 9회로
@pytest.fixture(scope="module")
def lib():
    return {n: H.build_lib(n) for n in C.NINE}


def _split(name, lib, kinds):
    s1, s1v = lib[name]
    eng = {r for r in O.engine_records(coupling_vars(s1, s1v)) if r[0] in kinds}
    orc = {r for r in O.CouplingOracle(s1, s1v).records() if r[0] in kinds}
    return eng, orc


@pytest.mark.parametrize("name", C.NINE)
def test_library_k3_k4_k8_match_oracle(name, lib):
    eng, orc = _split(name, lib, {"K3", "K4", "K8"})
    assert eng == orc


@pytest.mark.parametrize("name", C.NINE)
def test_library_k1_k2_match_oracle(name, lib):
    # 바이어스 기둥 의사 블록(as-built (i)) 포함 정의
    eng, orc = _split(name, lib, {"K1", "K2"})
    assert sorted(orc - eng) == [] and sorted(eng - orc) == []


@pytest.mark.parametrize("name", C.NINE)
def test_library_k7_match_oracle(name, lib):
    # K7 = MOS 만(as-built (iii))
    eng, orc = _split(name, lib, {"K7"})
    assert sorted(eng - orc) == [] and sorted(orc - eng) == []


@pytest.mark.parametrize("name", C.NINE)
def test_library_k1_k2_blocks_match_oracle(name, lib):
    # K1·K2 blocks(의사 블록 포함) = oracle 횡단 블록(뷰별, 의사 블록 키 ("bias:<기둥 id>",))
    s1, s1v = lib[name]
    orc = O.CouplingOracle(s1, s1v)
    for v in coupling_vars(s1, s1v).vars:
        if v.kind in ("K1", "K2"):
            assert {(b.view, tuple(b.key)) for b in v.blocks} == orc.crossing_refs(v.members), (name, v)


def test_library_tail_source_k1_records(lib):
    # 21bde21 로 생긴 K1(topology 직접 읽기): 꼬리 전류원이 바이어스 기둥의 기준 diode 와 같은 gate·source.
    #  sf: M3(d TAIL, g NB, s vss) <- M4(d NB, g NB, s vss) / folded: M11(d tail, g vb2, s gnd) <- MN(d vb2, g vb2, s gnd)
    #  pilot: M6(d Vx, g Vbias1, s vdd) <- M18_bg(d Vbias1, g Vbias1, s vdd).
    got = {n: {(v.members, v.domain) for v in coupling_vars(*lib[n]).vars if v.kind == "K1"} for n in C.NINE}
    assert {(("M3", "M4"), "dc"), (("M3", "M4"), "geom")} <= got["sf_pushpull_output_opamp"]
    assert {(("M11", "MN"), "dc"), (("M11", "MN"), "geom")} <= got["folded_cascode"]
    assert (("M18_bg", "M6"), "dc") in got["current_reuse_telescopic_ota"]


def test_library_kind_count_table(lib):
    # oracle (b) 산출을 손으로 확인한 표(설계 as-built 정의). K3 은 9회로 0건(설계 문장), column_unassigned 없음.
    # 21bde21 tail_source 로 늘어난 K1(topology 직접 읽기 + S1v 블록 역할로 손 확인, 아래 test_library_tail_source_k1_records):
    #  current_reuse_telescopic_ota +1: M6(tail_source, gate Vbias1) <- 기준 diode M18_bg(바이어스 기둥 {Iref, M18_bg}) mirror -> K1 dc
    #     (L 동치류 쪽 geom 레코드는 이미 load 멤버로 있었다) 3 -> 4
    #  folded_cascode +2: M11(tail_source, gate vb2) <- 기준 diode MN(바이어스 기둥 {Ibg, MN, MP}) -> K1 dc·geom 1 -> 3
    #  sf_pushpull_output_opamp +2: M3(tail_source, gate NB) <- 기준 diode M4(바이어스 기둥 {IBias, M4}) -> K1 dc·geom 4 -> 6
    expect = {
        "common_gate_amplifier": {},
        "current_reuse_telescopic_ota": {"K1": 4, "K2": 2, "K4": 5, "K7": 11},
        "folded_cascode": {"K1": 3, "K2": 2},
        "ngcc_3stage_ff": {"K1": 4, "K2": 4},
        "nmcnr_amplifier": {},
        "pushpull_follower_buffer": {},
        "sf_pushpull_output_opamp": {"K1": 6, "K2": 3, "K8": 2},
        "two_stage_ota": {"K1": 2, "K2": 1},
        "two_stage_ota_sf": {"K1": 2, "K2": 1},
    }
    oracle_got = {n: dict(collections.Counter(r[0] for r in O.CouplingOracle(*lib[n]).records())) for n in C.NINE}
    assert oracle_got == expect                                # oracle 자체의 회귀 고정
    engine_got = {n: dict(collections.Counter(v.kind for v in coupling_vars(*lib[n]).vars)) for n in C.NINE}
    assert engine_got == expect


def test_library_k3_absent(lib):
    # 설계 as-built (ii): K3 9회로 0건
    assert [n for n in C.NINE if any(v.kind == "K3" for v in coupling_vars(*lib[n]).vars)] == []


def test_sf_side_injection_and_column_mate_k2(lib):
    cpl = coupling_vars(*lib["sf_pushpull_output_opamp"])
    got = {(v.kind, tuple(v.members), tuple(v.nets)) for v in cpl.vars if v.kind in ("K2", "K8")}
    # 손 유도(topology 직접 읽기): M17(PMOS, gate N5 = 복합 diode 넷)이 레벨 시프트 CD M18(gate Y)의 source N17 에 전류를 넣고
    # N17 은 출력 CD M22 로 간다 -> K8 (M17, M18)@N17. 대칭으로 M20(gate N13)·CD M19@N20. members 순서 = (c, CD 셀들)(interface 11.3).
    # equal_vgs {M17, M6, M9}(N5, vdd): M6·M9 는 이득 블록 Y, M17 은 기둥 {M17, M18} 이웃 -> 버퍼 블록 vout -> K2. {M14, M16, M20} 대칭.
    assert {("K8", ("M17", "M18"), ("N17",)), ("K8", ("M20", "M19"), ("N20",)),
            ("K2", ("M17", "M6", "M9"), ("N5", "vdd")), ("K2", ("M14", "M16", "M20"), ("N13", "vss"))} <= got


def test_design_named_bias_reference_examples(lib):
    # 설계 40 §3.3 as-built (i) 의 예: sf M3<->M4(NB 기준 diode M4 는 바이어스 기둥 {IBias, M4}), ngcc M6A<->M7(NX diode M6A 는
    # 바이어스 기둥 {M5, M6A, M6B}) -> equal_vgs 가 의사 블록과 블록을 가로지른다 -> K2.
    sf = {(v.kind, tuple(v.members), tuple(v.nets)) for v in coupling_vars(*lib["sf_pushpull_output_opamp"]).vars}
    ngcc = {(v.kind, tuple(v.members), tuple(v.nets)) for v in coupling_vars(*lib["ngcc_3stage_ff"]).vars}
    assert ("K2", ("M3", "M4"), ("NB", "vss")) in sf
    assert ("K2", ("M6A", "M7"), ("NX", "gnd")) in ngcc


# ---------------------------------------------------------------- 불변식: 이름 전단사·결정론
def _canon(s1, s1v, cpl, netmap=None, elmap=None):
    nm = (lambda n: netmap.get(n, n)) if netmap else (lambda n: n)
    em = (lambda n: elmap.get(n, n)) if elmap else (lambda n: n)
    cols = {cid: frozenset(em(d) for d in devs) for cid, devs in C.column_devices(s1).items()}

    def view_sig(vid):
        v = [x for x in s1v.views if x.id == vid][0]
        cut = em(vid.split(":")[1]) if v.kind == "loop" else None
        return (v.kind, frozenset((nm(n), w) for n, w in v.excite), frozenset(nm(n) for n in v.sense), cut)

    def blk(b):
        if b is None:
            return None
        return (view_sig(b.view), frozenset(nm(n) for n in b.key))

    vars_ = collections.Counter(
        (v.kind, tuple(em(m) for m in v.members) if v.kind == "K3" else frozenset(em(m) for m in v.members), v.domain, v.init_rule,
         tuple(nm(n) for n in v.nets) if v.kind in ("K2", "K3", "K8") else frozenset(nm(n) for n in v.nets),
         frozenset(blk(b) for b in v.blocks if "bias:" not in repr(b)))
        for v in cpl.vars)
    rows = collections.Counter((None if r.column is None else cols[r.column], blk(r.block), em(r.device), r.shared, r.basis)
                               for r in cpl.column_block_map.rows)
    bias = frozenset(cols[c] for c in cpl.column_block_map.bias_columns)
    return vars_, rows, bias


@pytest.mark.parametrize("name", C.NINE)
def test_name_bijection_and_order_invariance(tmp_path, name):
    raw = C.lib_raw(name)
    s1, s1v = H.build_lib(name)
    base = _canon(s1, s1v, coupling_vars(s1, s1v))
    for seed in (3, 11):
        netmap, elmap = C.bijection(raw, seed)
        doc = C.rename_all(raw, netmap, elmap, seed)
        sup = {netmap[k]: v for k, v in H.lib_supplies(name).items()}
        from gmid_engine.graph import build_s1, build_s1v
        r1 = build_s1(H.load(tmp_path, doc, stem="ren%d_%s" % (seed, name)), sup)
        r1v = build_s1v(r1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False)
        inv_n = {v: k for k, v in netmap.items()}
        inv_e = {v: k for k, v in elmap.items()}
        back = _canon(r1, r1v, coupling_vars(r1, r1v), inv_n, inv_e)
        assert back == base, (name, seed)


_HASHSEED_SCRIPT = r"""
import sys
sys.path[:0] = [{skill!r}, {graph!r}]
import s1v_hand as H
from gmid_engine.core import fp_of
from gmid_engine.graph import coupling_vars
for n in {names!r}:
    s1, s1v = H.build_lib(n)
    print(n, fp_of(coupling_vars(s1, s1v)))
"""


_PSEUDO_SCRIPT = r"""
import sys
sys.path[:0] = [{skill!r}, {graph!r}]
import s1v_hand as H, coupling_hand as C
from gmid_engine.graph import coupling_vars
for n in {names!r}:
    s1, s1v = H.build_lib(n)
    cols = {{str(k): sorted(v) for k, v in C.column_devices(s1).items()}}
    out = []
    for v in coupling_vars(s1, s1v).vars:
        for b in v.blocks:
            if b.key and str(b.key[0]).startswith("bias:"):
                out.append((v.kind, v.members, v.domain, b.view, b.key, cols[str(b.key[0])[5:]]))
    print(repr((n, sorted(out))))
"""


def test_pseudo_block_keys_deterministic_across_hashseed():
    # 의사 블록 키(기둥 id 포함)가 PYTHONHASHSEED 에 무관하고, 키의 기둥 id 가 가리키는 S1 기둥 소자 집합도 같다.
    names = ("current_reuse_telescopic_ota", "sf_pushpull_output_opamp", "folded_cascode", "ngcc_3stage_ff")
    here = Path(__file__).resolve().parent
    script = _PSEUDO_SCRIPT.format(skill=str(here.parents[2]), graph=str(here), names=names)
    outs = []
    for seed in ("0", "777"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-P", "-c", script], capture_output=True, text=True, env=env, timeout=600)
        assert p.returncode == 0, p.stderr[-2000:]
        outs.append(p.stdout)
    assert outs[0] == outs[1]
    lines = outs[0].splitlines()
    assert len(lines) == len(names) and all("bias:" in line for line in lines), outs[0]   # 네 회로 모두 의사 블록 레코드가 있다


def test_determinism_across_hashseed_and_repeat(lib):
    names = ("current_reuse_telescopic_ota", "sf_pushpull_output_opamp", "ngcc_3stage_ff")
    for n in names:
        assert fp_of(coupling_vars(*lib[n])) == fp_of(coupling_vars(*lib[n]))
    here = Path(__file__).resolve().parent
    script = _HASHSEED_SCRIPT.format(skill=str(here.parents[2]), graph=str(here), names=names)
    outs = []
    for seed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        p = subprocess.run([sys.executable, "-P", "-c", script], capture_output=True, text=True, env=env, timeout=600)
        assert p.returncode == 0, p.stderr[-2000:]
        outs.append(p.stdout.split())
    assert outs[0] == outs[1]
    here_fp = [x for n in names for x in (n, fp_of(coupling_vars(*lib[n])))]
    assert outs[0] == here_fp
