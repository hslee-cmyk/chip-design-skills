"""design 40 v1.11.2 §2.4.8 '레이아웃 정준 별칭표' 행 -- `@compute_block` `canon_tables`(writer `ly_canonical_naming`, 파일 `layout/canon_block.py`,
규칙 H 1:1). 사용자 결정 O-36 (3) (a)·(c)·O-39 (1), 승인 O-42(2026-10-19).

계약(design 문언):
- READS device `ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`, graph `ly_groups_in`·`ly_row_groups`·`ly_passives`. `ly_rejected` 는 READS 에 없다
  (`_build` 가 쓰지 않는 인자).
- WRITES graph `ly_canon`(matching 범위 별칭표: 소자·넷·matching 그룹 별칭)·`ly_canon_rows`(행 범위: 위 + 행 그룹·수동소자 별칭). 두 필드는 다른
  개념이다 -- 행 그룹 변경이 `ly_canon` 을 바꾸지 않아야 `ly_pattern_select` 가 다시 계산되지 않는다.
- 값 = frozen dataclass `Canon`, 값 지문은 dataclass 칸 `pairs`·`orders` 만 본다.
- W 표지 `("W", W_m)` 는 `ly_attrs` 의 참고 W_m: 정준 색은 표지 값의 정렬 순위 -- 같은 배율은 순위·동률을 보존(값 같음, 완료 조건 W-1),
  W 를 빼면 같은 궤도인 구조 대칭 쌍의 W 대소를 뒤집으면 순위가 뒤바뀌어 별칭이 바뀐다(W-3).

oracle: (d) design 표 문언(READS·WRITES·칸 이름) + (a) 구성으로 정답이 정해진 입력(정확 2배, 대칭 쌍 W 맞바꿈, 행 그룹 이름만 바꿈,
수동소자 추가, 거부 목록만 바꿈). 별칭 값 자체는 단언하지 않는다(design 이 별칭 문자열 형식을 정하지 않는다) -- 두 입력 결과의 값 지문
같음·다름과 블록 입력 버전 같음·다름만 본다. 피검 블록 결과로 기대값을 만들지 않는다.
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.layout import _ly_fields as lf
from gmid_engine.layout.canon_block import canon_tables
from gmid_engine.layout.contract_input import LayoutPassive

from .conftest import (F_CANON_NAME, F_CANON_ROWS_NAME, W_CANON, block_row, dev, fresh_run, make_input, mg, new_memo, rg,
                       staged_snapshot, toy_pdk)


def _devices(wa=4e-6, wb=4e-6, w_scale=1.0, over=None):
    """차동쌍 A·B(공통 source h·공통 gate g·각자 drain da/db) + 바이어스 쌍 C·D + 단독 E. 참고 W 는 손으로 고른 값(동률 A=B 기본, C·D·E 다름)."""
    ds = [dev("A", "h", "da", 2e-6, W=wa), dev("B", "h", "db", 2e-6, W=wb),
          dev("C", "x", "y", 0.75e-6, gate="gb", W=3e-6), dev("D", "y", "z", 1e-6, gate="gb", W=6e-6),
          dev("E", "p", "q", 2e-6, gate="ge", W=5e-6)]
    ds = [dataclasses.replace(d, W_m=w_scale * d.W_m) for d in ds]
    return [dataclasses.replace(d, **(over or {}).get(d.name, {})) for d in ds]


def _inp(toy_lut, devices=None, rgs=None, rejected=(), passives=(), groups=None):
    groups = [mg("g1", ("A", "B"), "diff_pair", "h"), mg("g3", ("C", "D"), "bias_distribution", "y")] if groups is None else groups
    rgs = [rg("r1", ("A", "B")), rg("r2", ("C", "D", "E"))] if rgs is None else rgs
    return make_input(_devices() if devices is None else devices, groups, rgs, toy_pdk(toy_lut), rejected, passives)


def _staged(toy_lut, inp):
    return staged_snapshot(inp, new_memo(toy_lut))


def _canon(toy_lut, inp):
    """정준 별칭표 블록까지 적용한 스냅샷(실행마다 새 open_run() 쌍 -- 두 입력의 결과는 서로 다른 실행에서 독립으로 만든다)."""
    return staged_snapshot(inp, new_memo(toy_lut), "canon_tables")


def _fp(snap, field):
    return snap.field(lf.GRAPH, lf.GRAPH_KEY, field).value_fp


# ---------------------------------------------------------------------------------------------------------------- 선언

def test_canon_tables_declaration():
    # oracle (d): design 40 §2.4.8 '레이아웃 정준 별칭표' 행 -- writer 이름, READS, WRITES
    assert canon_tables.name == W_CANON == "ly_canonical_naming"
    assert set(canon_tables.reads) == {("device", "ly_point"), ("device", "ly_pins"), ("device", "ly_w_adjustable"),
                                       ("device", "ly_attrs"), ("graph", "ly_groups_in"), ("graph", "ly_row_groups"),
                                       ("graph", "ly_passives")}
    assert ("graph", "ly_rejected") not in set(canon_tables.reads)
    assert set(canon_tables.writes) == {("graph", F_CANON_NAME), ("graph", F_CANON_ROWS_NAME)}
    for f in (F_CANON_NAME, F_CANON_ROWS_NAME):
        assert lf.LY_WRITERS.writer_of(lf.GRAPH, f) == W_CANON


def test_canon_values_are_frozen_dataclasses_with_pairs_and_orders(toy_lut):
    # design: "값 지문과 불변 검사는 `Canon`의 dataclass 칸 `pairs`·`orders`만 본다", "`Canon`은 frozen dataclass"
    snap = _canon(toy_lut, _inp(toy_lut))
    for f in (F_CANON_NAME, F_CANON_ROWS_NAME):
        v = snap.value(lf.GRAPH, lf.GRAPH_KEY, f)
        assert dataclasses.is_dataclass(v) and not isinstance(v, type), f
        assert {x.name for x in dataclasses.fields(v)} == {"pairs", "orders"}, f
        assert type(v).__dataclass_params__.frozen, f


# ---------------------------------------------------------------------------------------------------------------- 입력 버전

def test_canon_input_version_ignores_rejected_requests(toy_lut):
    # `ly_rejected` 는 READS 밖 -> 거부 목록만 다른 두 스냅샷의 입력 버전이 같다
    a = _staged(toy_lut, _inp(toy_lut))
    b = _staged(toy_lut, _inp(toy_lut, rejected=("A",)))
    assert a.value(lf.GRAPH, lf.GRAPH_KEY, lf.F_REJECTED) != b.value(lf.GRAPH, lf.GRAPH_KEY, lf.F_REJECTED)   # 전제: 입력이 실제로 다르다
    assert canon_tables.input_version(a) == canon_tables.input_version(b)


@pytest.mark.parametrize("change", [
    "attrs_W_m", "attrs_diode", "point_ID_A", "point_gm_id", "pins_gate", "w_adjustable", "groups_in", "row_groups",
    "passives",
])
def test_canon_input_version_follows_each_read_field(toy_lut, change):
    # READS 의 각 필드(와 그 칸)가 바뀌면 입력 버전이 바뀐다 -- 한 칸씩 바꾼 입력(구성)
    base = _inp(toy_lut)
    if change == "attrs_W_m":
        other = _inp(toy_lut, devices=_devices(over={"E": {"W_m": 7e-6}}))
    elif change == "attrs_diode":
        other = _inp(toy_lut, devices=_devices(over={"C": {"diode": True}}))
    elif change == "point_ID_A":
        other = _inp(toy_lut, devices=_devices(over={"E": {"ID_A": 1.5 * _devices()[4].ID_A}}))
    elif change == "point_gm_id":
        other = _inp(toy_lut, devices=_devices(over={"E": {"gm_id": 13.0}}))
    elif change == "pins_gate":
        other = _inp(toy_lut, devices=_devices(over={"E": {"gate": "ge2"}}))
    elif change == "w_adjustable":
        other = _inp(toy_lut, devices=_devices(over={"E": {"W_adjustable": False}}))
    elif change == "groups_in":
        other = _inp(toy_lut, groups=[mg("g1", ("A", "B"), "diff_pair", "h")])
    elif change == "row_groups":
        other = _inp(toy_lut, rgs=[rg("rx", ("A", "B")), rg("r2", ("C", "D", "E"))])
    else:
        other = _inp(toy_lut, passives=(LayoutPassive("Cc", 3e-12),))
    assert canon_tables.input_version(_staged(toy_lut, base)) != canon_tables.input_version(_staged(toy_lut, other))


# ---------------------------------------------------------------------------------------------------------------- 값 (W-1·W-3 블록 단위)

def test_canon_uniform_exact_doubling_keeps_both_tables(toy_lut):
    # W-1 블록 단위: 모든 W_m 정확히 2배(2진 지수만 바뀐다) -> W 표지 순위·동률 보존 -> 두 별칭표 값 지문 같음. 입력 버전은 다르다(ly_attrs)
    a = _canon(toy_lut, _inp(toy_lut))
    b = _canon(toy_lut, _inp(toy_lut, devices=_devices(w_scale=2.0)))
    assert canon_tables.input_version(a) != canon_tables.input_version(b)
    assert _fp(a, F_CANON_NAME) == _fp(b, F_CANON_NAME)
    assert _fp(a, F_CANON_ROWS_NAME) == _fp(b, F_CANON_ROWS_NAME)


def test_canon_symmetric_pair_w_order_swap_changes_matching_table(toy_lut):
    # W-3 블록 단위: A·B 는 drain 넷 이름과 W 말고 모든 칸이 같고(구성 확인) 같은 matching 그룹 -- W_A < W_B 와 W_A > W_B 의 `ly_canon` 지문이 다르다
    d1 = _devices(wa=3e-6, wb=5e-6)
    d2 = _devices(wa=5e-6, wb=3e-6)
    a, b = d1[0], d1[1]
    same = ("kind", "gate", "source", "body", "L_m", "ID_A", "gm_id", "vds_V", "vsb_V", "diode", "W_adjustable")
    assert all(getattr(a, f) == getattr(b, f) for f in same)
    s1 = _canon(toy_lut, _inp(toy_lut, devices=d1))
    s2 = _canon(toy_lut, _inp(toy_lut, devices=d2))
    assert _fp(s1, F_CANON_NAME) != _fp(s2, F_CANON_NAME)


# ---------------------------------------------------------------------------------------------------------------- 두 범위는 다른 개념

def test_row_group_rename_changes_only_rows_scope_table(toy_lut):
    # 행 그룹 이름만 바꾼다(r1 -> rx): 행 범위 별칭표는 행 그룹 별칭을 담아 바뀌고, matching 범위 별칭표는 행 그룹을 담지 않아 그대로
    s1 = _canon(toy_lut, _inp(toy_lut))
    s2 = _canon(toy_lut, _inp(toy_lut, rgs=[rg("rx", ("A", "B")), rg("r2", ("C", "D", "E"))]))
    assert _fp(s1, F_CANON_NAME) == _fp(s2, F_CANON_NAME)
    assert _fp(s1, F_CANON_ROWS_NAME) != _fp(s2, F_CANON_ROWS_NAME)


def test_passive_added_changes_only_rows_scope_table(toy_lut):
    # 수동소자 하나를 더한다: 행 범위 별칭표만 수동소자 별칭을 담는다
    s1 = _canon(toy_lut, _inp(toy_lut))
    s2 = _canon(toy_lut, _inp(toy_lut, passives=(LayoutPassive("Cc", 3e-12),)))
    assert _fp(s1, F_CANON_NAME) == _fp(s2, F_CANON_NAME)
    assert _fp(s1, F_CANON_ROWS_NAME) != _fp(s2, F_CANON_ROWS_NAME)


# ---------------------------------------------------------------------------------------------------------------- 블록 호출 계약

def test_block_reuse(toy_lut):
    # oracle 대조: card B C4 판정 1 -- 같은 실행(run)에서 같은 lineage 재호출 = reuse(스냅샷 그대로), 같은 입력 재계산 0(C1 행)
    run = fresh_run()
    snap = staged_snapshot(_inp(toy_lut), new_memo(toy_lut), "canon_tables", run=run)
    assert canon_tables(snap, **run) is snap
    st = block_row(run["counters"], canon_tables.name)
    assert (st[1], st[4], st[5]) == (1, 1, 0)                     # reuses 1, computes 1, recomputes_same_input 0
