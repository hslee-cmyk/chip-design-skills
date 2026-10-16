"""CONTRACT 4.11 `compose_rows`(@compute_block) -- graph `ly_rows`(RowsLayout)·`ly_floorplan`.

초기 행(패턴 행·폭 키별 행) -> hub 병합(면적 감소만 채택) -> box 개선(matching 패턴 행은 재구성만, matching 비그룹 행은 자동 접기 금지,
그 밖만 접기; 채택 = 외곽 면적 감소). 하드 box 게이트 없음. 같은 내용의 row_euler·floorplan_of 는 블록 호출 안에서 한 번(계측).
"""
from __future__ import annotations

from collections import Counter

import pytest

from gmid_engine.layout import rows as rows_mod
from gmid_engine.layout.contract_output import (MERGE_NOISE_NOTE, BoxVerdict, FloorplanSummary, FoldAttempt, GroupRebuild,
                                                MergeDecision, RowLayout, RowsLayout)
from gmid_engine.layout.floorplan import floorplan_of
from gmid_engine.layout.rows import compose_rows

from .conftest import centroid_offsets, dev, graph_value, make_input, mg, new_memo, rg, staged_snapshot, toy_pdk
from .conftest import block_row, fresh_run  # [XRUN-F1 card B C0·C1]
from .test_floorplan import row as plain_row
from .test_row_euler import walk_ok


def compose(toy_lut, devices, groups=(), rgs=None, pdk=None):
    rgs = rgs or [rg("r1", [d.name for d in devices])]
    inp = make_input(devices, groups, rgs, pdk or toy_pdk(toy_lut))
    snap = staged_snapshot(inp, new_memo(toy_lut), "compose_rows")
    rl = graph_value(snap, "ly_rows")
    fp = graph_value(snap, "ly_floorplan")
    assert isinstance(rl, RowsLayout) and isinstance(fp, FloorplanSummary)
    return rl, fp, snap


def finger_totals(rows):
    c = Counter()
    for r in rows:
        for n, k in r.devices:
            c[n] += k
    return c


def check_rows_basic(rl, devices):
    by = {d.name: d for d in devices}
    ids = [r.row_id for r in rl.rows]
    assert ids == sorted(ids)
    for r in rl.rows:
        assert isinstance(r, RowLayout)
        assert list(r.devices) == sorted(r.devices)
        assert Counter(r.transistor_sequence) == Counter(dict(r.devices))
        flat = []
        for seq, nodes in r.segments:
            flat += list(seq)
        assert flat == list(r.transistor_sequence)
        assert r.crossover_count == len(r.segments) - 1 if r.method.startswith("pattern:") else True
    assert isinstance(rl.box, BoxVerdict)


# --- 초기 행 ----------------------------------------------------------------------------------------------------------

def test_initial_rows_pattern_and_width_key_rows(toy_lut):
    ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("C", "x", "y", 0.75e-6)]
    pdk = toy_pdk(toy_lut, overhead=0.1e-6)
    rl, fp, _ = compose(toy_lut, ds, [mg("g1", ("A", "B"), "diff_pair", "h")], pdk=pdk)
    by = {r.row_id: r for r in rl.rows}
    assert set(by) == {"r1/g1/0", "r1/g1/1", "r1/w100"}
    for i, seq in enumerate((("A", "B"), ("B", "A"))):
        r = by["r1/g1/%d" % i]
        assert r.transistor_sequence == seq
        assert (r.method, r.group, r.matching, r.walk_ok, r.row_group) == ("pattern:rotation_exact", "g1", True, True, "r1")
        assert r.width_m == pytest.approx(2 * (1e-6 + 0.1e-6), rel=1e-12)      # sum(nf x (L + overhead))
        assert r.finger_w_m == pytest.approx(1e-6)
    c = by["r1/w100"]
    assert (c.group, c.matching, c.method, c.devices) == (None, False, "euler", (("C", 1),))
    assert c.width_m == pytest.approx(1.1e-6, rel=1e-12)
    assert rl.merge_decisions == () and rl.rebuilt_groups == ()
    check_rows_basic(rl, ds)
    # box 는 기록만(Q8 (vi)): 최종 행에서 다시 계산한 값과 같다
    assert rl.box.total_width_m == pytest.approx(max(r.width_m for r in rl.rows))
    assert rl.box.width_ratio == pytest.approx(max(r.width_m for r in rl.rows) / min(r.width_m for r in rl.rows))


def test_walk_ok_reflects_segments(toy_lut):
    ds = [dev("E", "p", "q", 2e-6, gate="gc"), dev("F", "r", "t", 2e-6, gate="gc")]
    rl, _, _ = compose(toy_lut, ds, [mg("g2", ("E", "F"), "branch_symmetric", None)])
    from gmid_engine.layout.transistor import Transistor as T
    trs = [T(d.name, "nmos", d.source, d.drain, 2) for d in ds]
    for r in rl.rows:
        assert r.group == "g2" and r.method == "pattern:row_swap"
        assert r.walk_ok is all(walk_ok(seq, nodes, trs) for seq, nodes in r.segments)
        assert r.crossover_count == len(r.segments) - 1


def test_no_initial_rows_raises(toy_lut):
    ds = [dev("Z", "a", "b", 2e-6, gm_id=25.0)]
    with pytest.raises(ValueError):
        compose(toy_lut, ds)


# --- hub 병합 (Q8 (viii)) ---------------------------------------------------------------------------------------------

def test_hub_merge_hand_oracle(toy_lut):
    ds = [dev("C", "x", "y", 1e-6), dev("D", "y", "z", 1e-6), dev("G", "y", "w", 1e-6)]
    rl, fp, _ = compose(toy_lut, ds, rgs=[rg("r", ("C", "D")), rg("r2", ("G",))])
    assert len(rl.merge_decisions) == 1
    m = rl.merge_decisions[0]
    assert isinstance(m, MergeDecision)
    assert (tuple(m.rows), m.net) == (("r/w100", "r2/w100"), "y")
    assert m.merged is (m.area_after_m2 < m.area_before_m2)
    assert m.reason == ("area_decreased" if m.merged else "area_not_decreased")
    assert m.note == MERGE_NOISE_NOTE
    if m.merged:
        assert [r.row_id for r in rl.rows] == ["r/w100+r2/w100"]
        merged = rl.rows[0]
        assert merged.row_group == "r"
        assert dict(merged.devices) == {"C": 1, "D": 1, "G": 1}
        assert fp.outline_area_m2 == pytest.approx(m.area_after_m2)
    assert finger_totals(rl.rows) == Counter({"C": 1, "D": 1, "G": 1})


def test_hub_merge_rejected_when_area_not_decreasing(toy_lut):
    # 2+2 finger 두 행: 합친 4 finger 한 행 = 같은 면적 -> 채택 안 함(면적 감소만 채택)
    ds = [dev("C", "x", "y", 1e-6), dev("D", "y", "z", 1e-6), dev("G", "y", "w", 1e-6), dev("J", "w", "v", 1e-6)]
    rl, fp, _ = compose(toy_lut, ds, rgs=[rg("r", ("C", "D")), rg("r2", ("G", "J"))])
    assert rl.merge_decisions, "병합 시도가 기록되지 않았다"
    for m in rl.merge_decisions:
        assert m.merged is (m.area_after_m2 < m.area_before_m2)
    assert any(not m.merged and m.reason == "area_not_decreased" for m in rl.merge_decisions)
    assert sorted(r.row_id for r in rl.rows) == ["r/w100", "r2/w100"]


def test_hub_merge_skips_matching_and_other_width_rows(toy_lut):
    # 차동쌍(ID 1e-6, 요청 pending -> 패턴 없음) 멤버 A·B 는 matching 비그룹 행. 같은 hub "h" 의 G 행과 병합하지 않는다.
    # K 는 hub "h" 를 공유하지만 폭 키 200 행(같은 폭 키 행끼리만 병합).
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6), dev("G", "h", "w", 1e-6)]
    rl, _, _ = compose(toy_lut, ds, [mg("g1", ("A", "B"), "diff_pair", "h")], rgs=[rg("r1", ("A", "B")), rg("r2", ("G",))])
    assert rl.merge_decisions == ()
    ab = [r for r in rl.rows if "A" in dict(r.devices)][0]
    assert ab.group is None and ab.matching is True
    ds2 = [dev("P", "x", "h", 1e-6), dev("K", "h", "k", 4e-6)]
    rl2, _, _ = compose(toy_lut, ds2, rgs=[rg("r1", ("P",)), rg("r2", ("K",))])
    keys = {r.row_id: r.finger_w_key for r in rl2.rows}
    if len({keys[k] for k in keys}) == 2:
        assert rl2.merge_decisions == ()


# --- box 개선 (Q8 (v)(vi)) --------------------------------------------------------------------------------------------

def fold_sequences(attempts):
    seqs = {}
    for a in attempts:
        if a.action == "fold" and a.reason in ("evaluated", "adopted"):
            seqs.setdefault(a.row_id, []).append(a)
    return seqs


def check_fold_rules(rl):
    for rid, seq in fold_sequences(rl.fold_attempts).items():
        assert [a.n_rows for a in seq] == list(range(2, 2 + len(seq)))           # n = 2, 3, ... 차례로
        for prev, nxt in zip(seq, seq[1:-1]):
            assert nxt.outline_area_m2 < prev.outline_area_m2                     # 줄지 않으면 거기서 멈춘다
        adopted = [a for a in seq if a.adopted]
        assert len(adopted) <= 1
        if adopted:
            assert adopted[0].reason == "adopted"
            assert adopted[0].outline_area_m2 == min(a.outline_area_m2 for a in seq)
            assert (rid, adopted[0].n_rows) in tuple(rl.box.folds)
    adopted_ids = {a.row_id for a in rl.fold_attempts if a.action == "fold" and a.adopted}
    assert {f[0] for f in rl.box.folds} == adopted_ids


def test_fold_hand_oracle_single_row(toy_lut):
    # 4.15: r3 의 H(ID 12e-6) 혼자 -> 키 200 nf 6 행 r3/w200 -> fold n = 2, 3, ... 기록
    rl, fp, _ = compose(toy_lut, [dev("H", "k", "m", 12e-6)], rgs=[rg("r3", ("H",))])
    seq = fold_sequences(rl.fold_attempts)["r3/w200"]
    assert seq[0].n_rows == 2
    assert all(isinstance(a, FoldAttempt) and (a.dx, a.dy) == (None, None) for a in seq)
    a0 = floorplan_of((plain_row("r3/w200", "r3", 6e-6, fw=2e-6, key=200, devices=(("H", 6),)),), {"r3": "sub"},
                      toy_pdk(toy_lut)).outline_area_m2
    # 행 하나(폭 6 finger x 높이 2e-6)를 n 행으로 접으면 폭 ceil(6/n) x 높이 2n >= 원래 면적 -> 어떤 n 도 면적을 줄이지 못한다
    assert a0 == pytest.approx(12e-12, rel=1e-9)
    assert all(a.outline_area_m2 >= a0 * (1 - 1e-12) for a in seq)
    assert not any(a.adopted for a in rl.fold_attempts)                         # 게이트가 실제로 거부
    assert rl.box.folds == () and [r.row_id for r in rl.rows] == ["r3/w200"]
    check_fold_rules(rl)
    assert finger_totals(rl.rows) == Counter({"H": 6})


def test_fold_adopted_only_when_area_decreases(toy_lut):
    # 긴 행 H(6 finger) + 짧은 행 K(1 finger): 접으면 외곽 면적이 준다 -> 채택, 조각 id "<id>_split<j>"
    ds = [dev("H", "k", "m", 12e-6), dev("K", "k2", "m2", 2e-6)]
    rgs = [rg("r3", ("H",)), rg("r4", ("K",))]
    rl, fp, _ = compose(toy_lut, ds, rgs=rgs)
    a0 = floorplan_of((plain_row("r3/w200", "r3", 6e-6, fw=2e-6, key=200, devices=(("H", 6),)),
                       plain_row("r4/w200", "r4", 1e-6, fw=2e-6, key=200, devices=(("K", 1),))),
                      {"r3": "sub", "r4": "sub"}, toy_pdk(toy_lut)).outline_area_m2
    adopted = [a for a in rl.fold_attempts if a.adopted]
    assert adopted, "면적이 줄어드는 접기가 채택되지 않았다"
    for a in adopted:
        assert a.outline_area_m2 < a0
    assert fp.outline_area_m2 < a0
    assert any(r.row_id.startswith("r3/w200_split") for r in rl.rows)
    assert finger_totals(rl.rows) == Counter({"H": 6, "K": 1})                 # 접기 전후 finger 합 불변
    check_fold_rules(rl)


def test_matching_row_not_auto_folded(toy_lut):
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6), dev("H", "k", "m", 12e-6)]
    rl, fp, _ = compose(toy_lut, ds, [mg("g1", ("A", "B"), "diff_pair", "h")], rgs=[rg("r1", ("A", "B")), rg("r3", ("H",))])
    ab = [r for r in rl.rows if "A" in dict(r.devices)]
    assert len(ab) == 1 and ab[0].matching is True and ab[0].group is None
    recs = [a for a in rl.fold_attempts if a.row_id == ab[0].row_id]
    assert len(recs) == 1
    a = recs[0]
    assert (a.action, a.n_rows, a.dx, a.dy, a.adopted, a.reason) == ("fold", 1, None, None, False, "matching_row_not_auto_folded")
    check_fold_rules(rl)


def matching_devices(rl, groups):
    return {m for g in groups for m in g.members}


def test_fold_never_adopted_on_matching_rows(toy_lut):
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6), dev("H", "k", "m", 12e-6), dev("K", "k2", "m2", 2e-6)]
    groups = [mg("g1", ("A", "B"), "diff_pair", "h")]
    rl, _, _ = compose(toy_lut, ds, groups, rgs=[rg("r1", ("A", "B")), rg("r3", ("H",)), rg("r4", ("K",))])
    matching = matching_devices(rl, groups)
    for rid, n in rl.box.folds:
        pieces = [r for r in rl.rows if r.row_id.startswith(rid + "_split")]
        assert pieces and not any(set(dict(p.devices)) & matching for p in pieces)


def rebuild_case(toy_lut, ID, role):
    if role == "branch_symmetric":
        ds = [dev("E", "p", "q", ID, gate="gc"), dev("F", "r", "t", ID, gate="gc")]
        g = mg("g2", ("E", "F"), role, None)
    else:
        ds = [dev("A", "h", "da", ID), dev("B", "h", "db", ID)]
        g = mg("g1", ("A", "B"), role, "h")
    ds.append(dev("X", "x1", "x2", 2e-6))
    return compose(toy_lut, ds, [g], rgs=[rg("r1", g.members), rg("r2", ("X",))]), g


@pytest.mark.parametrize("ID, role", [(8e-6, "diff_pair"), (16e-6, "diff_pair"), (8e-6, "branch_symmetric"),
                                      (12e-6, "branch_symmetric"), (16e-6, "branch_symmetric")])
def test_matching_rows_rebuilt_and_rejected_if_worse(toy_lut, ID, role):
    (rl, fp, snap), g = rebuild_case(toy_lut, ID, role)
    groups = graph_value(snap, "ly_groups")
    gl = [x for x in groups if x.gid == g.gid][0]
    orig = max(gl.dx, gl.dy)
    reb = [a for a in rl.fold_attempts if a.action == "rebuild"]
    assert reb, "matching 패턴 행 재구성 시도가 없다"
    assert all(a.row_id == "r1/" + g.gid for a in reb)
    assert all(a.action != "fold" for a in rl.fold_attempts if a.row_id.startswith("r1/" + g.gid))   # 패턴 행은 접기 대상 아님
    for a in reb:
        if a.reason in ("evaluated", "adopted"):
            assert max(a.dx, a.dy) <= orig                                     # 통과한 재구성은 matching 이 나빠지지 않음
        else:
            assert a.reason == "matching_worse" and a.adopted is False
    adopted = [a for a in reb if a.adopted]
    assert len(adopted) <= 1
    if adopted:
        a = adopted[0]
        assert a.reason == "adopted"
        assert len(rl.rebuilt_groups) == 1
        gr = rl.rebuilt_groups[0]
        assert isinstance(gr, GroupRebuild) and (gr.gid, gr.n_rows) == (g.gid, a.n_rows)
        assert max(gr.dx, gr.dy) <= orig
        grows = [r for r in rl.rows if r.group == g.gid]
        assert len(grows) == a.n_rows
        dx, dy = centroid_offsets([r.transistor_sequence for r in grows], g.members)
        assert (float(dx), float(dy)) == pytest.approx((gr.dx, gr.dy))
        assert fp.outline_area_m2 <= a.outline_area_m2 + 1e-24
    else:
        assert rl.rebuilt_groups == ()
    nf = {m: dict(gl.n_fingers)[m] for m in g.members}
    assert {m: finger_totals(rl.rows)[m] for m in g.members} == nf             # 재구성 전후 finger 합 불변


def test_rebuild_gate_actually_rejects(toy_lut):
    # 차동쌍 nf 4:4 (ID 8e-6): k = 3·4 재구성은 모두 무게중심이 어긋난다 -> matching_worse 로 거부, 원 배치 유지
    (rl, _, _), g = rebuild_case(toy_lut, 8e-6, "diff_pair")
    reb = [a for a in rl.fold_attempts if a.action == "rebuild"]
    assert [a.n_rows for a in reb] == [3, 4]
    assert all(a.reason == "matching_worse" and not a.adopted for a in reb)
    assert all(max(a.dx, a.dy) > 0 for a in reb)
    assert rl.rebuilt_groups == ()
    assert sorted(r.row_id for r in rl.rows if r.group == "g1") == ["r1/g1/0", "r1/g1/1"]


def test_rebuild_adopted_reduces_area(toy_lut):
    # branch_symmetric nf 8:8 (ID 16e-6, 키 200): 2행(폭 8 finger) -> 4행 재구성이 외곽 면적을 줄인다
    (rl, fp, _), g = rebuild_case(toy_lut, 16e-6, "branch_symmetric")
    a0 = floorplan_of((plain_row("r1/g2/0", "r1", 8e-6, fw=2e-6, key=200, devices=(("E", 4), ("F", 4))),
                       plain_row("r1/g2/1", "r1", 8e-6, fw=2e-6, key=200, devices=(("E", 4), ("F", 4))),
                       plain_row("r2/w200", "r2", 1e-6, fw=2e-6, key=200, devices=(("X", 1),))),
                      {"r1": "sub", "r2": "sub"}, toy_pdk(toy_lut)).outline_area_m2
    adopted = [a for a in rl.fold_attempts if a.adopted]
    assert len(adopted) == 1 and adopted[0].action == "rebuild"
    assert adopted[0].outline_area_m2 < a0
    assert fp.outline_area_m2 < a0
    assert rl.rebuilt_groups and rl.rebuilt_groups[0].method == "row_swap"


def test_interdigitation_pattern_not_rebuildable(toy_lut):
    # [U12] 옛 픽스처(조정 불가 차동쌍 -> interdigitation 즉시 완화)는 LY5 즉시 완화 제거(D-LY2/R21)로 pattern None 이 되어 패턴 행이 없다.
    # interdigitation 패턴 행은 mirror 정렬 키 첫 칸(interdigitation 성립)으로 만든다: ID 2e-6 mirror -> interdigitation
    # (test_pattern_select.test_mirror_prefers_feasible_interdigitation 과 같은 구성).
    ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6)]
    rl, fp, _ = compose(toy_lut, ds, [mg("g1", ("A", "B"), "mirror", "h")])
    assert [r.row_id for r in rl.rows if r.group == "g1"] == ["r1/g1/0"]          # 패턴 행 하나(전제 확인)
    recs = [a for a in rl.fold_attempts if a.row_id == "r1/g1"]
    assert len(recs) == 1
    a = recs[0]
    assert (a.action, a.n_rows, a.dx, a.dy, a.adopted, a.reason) == ("rebuild", 1, None, None, False, "pattern_not_rebuildable")
    assert a.outline_area_m2 == pytest.approx(fp.outline_area_m2)


def test_no_hard_box_gate_extreme_ratio_kept(toy_lut):
    # 행 폭 비가 아주 커도(긴 matching 패턴 행 + 1 finger 행) 거부·실패 없이 기록만 한다
    ds = [dev("A", "h", "da", 40e-6), dev("B", "h", "db", 40e-6), dev("X", "x1", "x2", 1e-6)]
    rl, fp, _ = compose(toy_lut, ds, [mg("g1", ("A", "B"), "diff_pair", "h")], rgs=[rg("r1", ("A", "B")), rg("r2", ("X",))])
    assert rl.box.width_ratio == pytest.approx(max(r.width_m for r in rl.rows) / min(r.width_m for r in rl.rows))
    assert not hasattr(rl.box, "ok")
    for a in rl.fold_attempts:
        if a.adopted:
            assert a.reason == "adopted"


# --- 같은 내용 한 번만(memo) -------------------------------------------------------------------------------------------

def _key(obj):
    if isinstance(obj, dict):
        return ("dict", tuple(sorted((_key(k), _key(v)) for k, v in obj.items())))
    if isinstance(obj, (list, tuple)):
        return ("seq", tuple(_key(x) for x in obj))
    if hasattr(obj, "__dataclass_fields__"):
        return ("dc", type(obj).__name__, tuple((f, _key(getattr(obj, f))) for f in obj.__dataclass_fields__))
    return obj


def test_same_content_computed_once_per_block_call(toy_lut, monkeypatch):
    calls = {"row_euler": Counter(), "floorplan_of": Counter()}
    real_re, real_fp = rows_mod.row_euler, rows_mod.floorplan_of

    def re_spy(transistors, matching_pairs, pair_sensitivity):
        k = _key(sorted((t.name, t.kind, t.source, t.drain, t.n_fingers) for t in transistors))
        calls["row_euler"][(k, _key(matching_pairs), _key(pair_sensitivity))] += 1
        return real_re(transistors, matching_pairs, pair_sensitivity)

    def fp_spy(rows, bodies, pdk, passives=()):
        # [U12] floorplan_of(rows, bodies, pdk, passives=()) -- 수동소자 블록 인자 추가(CONTRACT 4.10)
        calls["floorplan_of"][(_key(sorted(rows, key=lambda r: r.row_id)), _key(bodies), _key(tuple(passives)))] += 1
        return real_fp(rows, bodies, pdk, passives)

    monkeypatch.setattr(rows_mod, "row_euler", re_spy)
    monkeypatch.setattr(rows_mod, "floorplan_of", fp_spy)
    ds = [dev("H", "k", "m", 12e-6), dev("K", "k2", "m2", 2e-6), dev("C", "x", "y", 1e-6), dev("D", "y", "z", 1e-6),
          dev("G", "y", "w", 1e-6), dev("E", "p", "q", 16e-6, gate="gc"), dev("F", "r", "t", 16e-6, gate="gc")]
    compose(toy_lut, ds, [mg("g2", ("E", "F"), "branch_symmetric", None)],
            rgs=[rg("r3", ("H",)), rg("r4", ("K",)), rg("r", ("C", "D")), rg("r2", ("G",)), rg("r1", ("E", "F"))])
    assert sum(calls["row_euler"].values()) > 0 and sum(calls["floorplan_of"].values()) > 0, "계측이 걸리지 않았다"
    dup_re = {k: v for k, v in calls["row_euler"].items() if v > 1}
    dup_fp = {k: v for k, v in calls["floorplan_of"].items() if v > 1}
    assert not dup_re, "같은 행 내용 row_euler 재계산 %d건" % len(dup_re)
    assert not dup_fp, "같은 행 집합 floorplan_of 재계산 %d건" % len(dup_fp)


def test_block_reuse(toy_lut):
    # oracle 대조: card B C4 판정 1 -- 같은 실행(run)에서 같은 lineage 재호출 = reuse, 같은 입력 재계산 0(C1 행)
    run = fresh_run()
    inp = make_input([dev("C", "x", "y", 1e-6)], [], [rg("r", ("C",))], toy_pdk(toy_lut))
    snap = staged_snapshot(inp, new_memo(toy_lut), "compose_rows", run=run)
    assert compose_rows(snap, **run) is snap
    st = block_row(run["counters"], compose_rows.name)
    assert st[5] == 0 and st[1] == 1
