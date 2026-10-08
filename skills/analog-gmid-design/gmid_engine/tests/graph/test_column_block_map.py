"""graph/column_block_map.py -- S1 기둥 x S1v 블록 매핑표와 `column_unassigned` 정지(U10, 설계 40 §3.3, 계획 DEC-71 (2)).

oracle (a) 손 유도(구성으로 정답이 정해진 손 회로, 규칙은 아래 근거 문장을 손으로 적용):
- DEC-71 (2): 두 기둥에 걸친 소자는 공유 소자, 블록 밖 소자만으로 된 기둥은 바이어스 기둥, 블록 소자와 섞인 기둥의 블록 밖 소자는
  그 기둥의 블록으로 귀속(공유 표시), 어느 블록에도 바이어스 기둥에도 들지 않는 소자는 정지(`column_unassigned`).
- 설계 40 §3.3 as-built(6707424): 매핑표 행 `basis` ∈ block_member·column_mate·bias_column, `column_unassigned` 범위 = DC 가지에
  든 원소(커패시터·가지치기된 저항 제외).
- interface(graph CONTRACT 11.1·11.2): 행 순서 (column(None 먼저), block, device), 블록 멤버인데 기둥에 없는 원소(커패시터)는
  column=None 행, shared = 둘 이상 기둥 | 한 뷰에서 둘 이상 블록 | 기둥 이웃.
oracle (b) library 9회로: `coupling_oracle.CouplingOracle`(S1·S1v 공개 필드로 같은 규칙을 집합 연산으로 다시 세운 것) 대조.
기둥 id 는 S1 열거 순번이라 손 회로에서는 '원소 집합 -> id' 로 찾는다(`coupling_hand.column_id`).
"""
from __future__ import annotations

import pytest

import coupling_hand as C
import coupling_oracle as O
import s1v_hand as H
from gmid_engine.core import StructureUnresolvedError, exit_code_for
from gmid_engine.graph import column_block_map, coupling_vars

T0 = "transfer:0"


def test_miller_rows_hand_derived(tmp_path):
    s1, s1v = H.build(tmp_path, H.MILLER)
    # 손 유도: 기둥 = {M5,M2,M4}·{M5,M1,M3}(꼬리 가지 M5 공유)·{M7,M6}. 블록 o1 = 1단(M1..M5), out = 2단(M6,M7), Cc 는 두 블록의 부하.
    a, b, c = C.column_id(s1, {"M5", "M2", "M4"}), C.column_id(s1, {"M5", "M1", "M3"}), C.column_id(s1, {"M7", "M6"})
    o1, out = (T0, ("o1",)), (T0, ("out",))
    expected = [
        (None, o1, "Cc", True, "block_member"),          # 커패시터: 가지 밖 블록 멤버, 한 뷰 두 블록 -> shared
        (None, out, "Cc", True, "block_member"),
        (a, o1, "M2", False, "block_member"),
        (a, o1, "M4", False, "block_member"),
        (a, o1, "M5", True, "block_member"),             # 두 기둥에 걸친 꼬리 -> shared (DEC-71 (2) 공유 소자)
        (b, o1, "M1", False, "block_member"),
        (b, o1, "M3", False, "block_member"),
        (b, o1, "M5", True, "block_member"),
        (c, out, "M6", False, "block_member"),
        (c, out, "M7", False, "block_member"),
    ]
    cbm = column_block_map(s1, s1v)
    assert sorted(C.rows(cbm), key=repr) == sorted(expected, key=repr)
    assert cbm.bias_columns == ()


def test_rows_are_sorted_column_none_first(tmp_path):
    # interface 11.1: rows 는 (column(None 먼저), block, device) 순
    s1, s1v = H.build(tmp_path, H.MILLER)
    got = [(r.column, r.block, r.device) for r in column_block_map(s1, s1v).rows]
    key = [(-1 if col is None else col, blk, dev) for col, blk, dev in got]
    assert key == sorted(key)


def test_column_mate_is_attributed_and_shared(tmp_path):
    s1, s1v = H.build(tmp_path, C.MATE)
    # 손 유도: 기둥 하나 {M1, M2, M3}. M1(CS 입력)·M2(부하)는 블록 out 멤버, 전류원 M3 는 블록 밖 -> 같은 기둥 블록 out 에 귀속.
    col = C.column_id(s1, {"M1", "M2", "M3"})
    out = (T0, ("out",))
    cbm = column_block_map(s1, s1v)
    assert sorted(C.rows(cbm), key=repr) == sorted([
        (col, out, "M1", False, "block_member"),
        (col, out, "M2", False, "block_member"),
        (col, out, "M3", True, "column_mate"),
    ], key=repr)
    assert cbm.bias_columns == ()


def test_bias_column_rows_have_no_block(tmp_path):
    s1, s1v = H.build(tmp_path, C.BCS)
    # 손 유도: 기둥 {M1, M2}(블록 out) 와 {Mi, Mr}(기준 diode + 전류원, 둘 다 블록 밖) -> 뒤의 것이 바이어스 기둥.
    sig, bias = C.column_id(s1, {"M1", "M2"}), C.column_id(s1, {"Mi", "Mr"})
    cbm = column_block_map(s1, s1v)
    assert sorted(C.rows(cbm), key=repr) == sorted([
        (sig, (T0, ("out",)), "M1", False, "block_member"),
        (sig, (T0, ("out",)), "M2", False, "block_member"),
        (bias, None, "Mi", False, "bias_column"),
        (bias, None, "Mr", False, "bias_column"),
    ], key=repr)
    assert tuple(cbm.bias_columns) == (bias,)


def test_capacitor_and_pruned_resistor_are_out_of_scope(tmp_path):
    # 설계 as-built: column_unassigned 범위 = DC 가지에 든 원소. Cb(커패시터)·Rx(잎 저항, DEC-70 가지치기)는 블록에도 기둥에도
    # 없지만 KVL 이 없어 정지 대상이 아니고 매핑표에도 없다.
    s1, s1v = H.build(tmp_path, C.CAPOR)
    pruned = {e for e, _round in C.gval(s1, "dc_pruned")}
    assert "Rx" in pruned                                    # 전제: Rx 는 가지치기됨(S1 공개 필드)
    cbm = column_block_map(s1, s1v)
    devices = {r[2] for r in C.rows(cbm)}
    assert devices == {"M1", "M2", "Mi", "Mr"}
    assert "Cb" not in devices and "Rx" not in devices


def test_orphan_branch_device_stops_column_unassigned(tmp_path):
    # DEC-71 (2) 정지: Mx 는 가지 (vbp, z) 에 들었으나 그 가지는 어느 기둥에도 없고(z 막다른 넷) Mx 는 블록 밖
    s1, s1v = H.build(tmp_path, C.ORPHAN)
    assert len(C.gval(s1, "column_orphans")) == 1             # 전제: S1 이 orphan 가지 하나를 기록
    for fn in (column_block_map, coupling_vars):
        with pytest.raises(StructureUnresolvedError) as ei:
            fn(s1, s1v)
        exc = ei.value
        assert exit_code_for(exc) == 2
        assert dict(exc.record.detail)["reason"] == "column_unassigned"
        assert tuple(exc.record.devices) == ("Mx",)


@pytest.mark.parametrize("name", C.NINE)
def test_library_map_matches_oracle(name):
    s1, s1v = H.build_lib(name)
    o = O.CouplingOracle(s1, s1v)
    cbm = column_block_map(s1, s1v)
    assert O.engine_map_rows(cbm) == o.map_rows
    assert tuple(cbm.bias_columns) == o.bias_columns
    assert o.unassigned == ()                                # 설계 40 §3.3: 9회로 column_unassigned 없음


@pytest.mark.parametrize("name", C.NINE)
def test_library_shared_flag_rule(name):
    # interface 11.2 shared 정의를 행마다 확인: 둘 이상 기둥 | 한 뷰에서 둘 이상 블록 | 기둥 이웃
    s1, s1v = H.build_lib(name)
    cols = C.column_devices(s1)
    ncol = {}
    for devs in cols.values():
        for d in devs:
            ncol[d] = ncol.get(d, 0) + 1
    nblk = {}
    for v in s1v.views:
        for b in v.blocks:
            for d, _r in b.roles:
                nblk[(v.id, d)] = nblk.get((v.id, d), 0) + 1
    for r in column_block_map(s1, s1v).rows:
        multi_block = any(n >= 2 for (vid, d), n in nblk.items() if d == r.device)
        expected = ncol.get(r.device, 0) >= 2 or multi_block or r.basis == "column_mate"
        assert r.shared == expected, (name, r)


@pytest.mark.parametrize("name", C.NINE)
def test_coupling_carries_same_map(name):
    s1, s1v = H.build_lib(name)
    assert coupling_vars(s1, s1v).column_block_map == column_block_map(s1, s1v)


def test_library_bias_columns_literal():
    # oracle (b) 산출을 손으로 확인한 원소 집합(기둥 id 는 열거 순번이라 원소 집합으로 적는다). 바이어스 기둥이 있는 회로만.
    expect = {
        "folded_cascode": {"Ibg", "MN", "MP"},   # 이상 전류원 + vb1·vb2 기준 diode 사슬: 블록 out 밖
        "ngcc_3stage_ff": {"M5", "M6A", "M6B"},  # VBP 미러 M5 + NX diode M6A + M6B: 세 블록 어디에도 없는 기둥
        "sf_pushpull_output_opamp": {"IBias", "M4"},  # 이상 전류원 + NB 기준 diode
    }
    counts = {}
    for name in C.NINE:
        s1, s1v = H.build_lib(name)
        bc = column_block_map(s1, s1v).bias_columns
        counts[name] = len(bc)
        if expect.get(name):
            assert [C.column_devices(s1)[c] for c in bc] == [frozenset(expect[name])], name
    # 바이어스 기둥 수: 파일럿 7(34~40), folded 1, ngcc 1, sf 1, 나머지 0
    assert counts == {"common_gate_amplifier": 0, "current_reuse_telescopic_ota": 7, "folded_cascode": 1, "ngcc_3stage_ff": 1,
                      "nmcnr_amplifier": 0, "pushpull_follower_buffer": 0, "sf_pushpull_output_opamp": 1, "two_stage_ota": 0,
                      "two_stage_ota_sf": 0}
