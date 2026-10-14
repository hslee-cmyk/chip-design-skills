"""graph/s1v_build.py -- `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(),
stop_on_unsupported=True) -> S1Graph`(계약 10.1·10.2 '기록과 정지', 10.3 불변량 1·2·8).

oracle (a):
- 인자: count_budget 은 1 이상 int(bool 거부) -- 그 밖 TypeError.
- 결정론·재사용(불변량 1): 같은 입력 두 번 -> S1v 필드 값 `==`, 같은 입력 재호출 -> 블록 재사용(계산 0) [U17 ①-b, previous= 삭제].
- 정지(불변량 8): `기록만` 코드가 하나라도 있으면 기본 모드에서 core `StructureUnresolvedError`(exit 2, detail reason
  `unsupported_rule_branch`, rule_branch = 첫 분기, branches, findings), `stop_on_unsupported=False` 는 기록을 돌려준다. review_needed 는
  정지가 아니다. 각 코드를 일으키는 손 회로는 해당 test 파일의 손 유도를 따른다.
- 이름 전단사·순서 섞기(불변량 2): 모든 구조 필드가 사상으로만 바뀐다. 예외 = 이름 tie-break 인 L 동치류 주인(owner_rule 이
  이름 순)·전달 뷰 순번.

[U1b 2026-10-09] oracle (d) 40 3.2-3 소비 방식: confirm 사실은 유도 값과 같으면 그 유도 레코드 status ratified + approval_id, 다르면
`structure_fact_mismatch`(review_needed), 엔진이 그 대상을 만들지 않았으면 `structure_fact_orphan`(review_needed). override 사실은
`applied_facts`(S1v.facts_applied)에 남는다. sf 의 `composite_dag_not_chain` 정지는 41 1.13 sf 행('composite_dag_not_chain·
record_only·혼재 8건 해소', 복합 diode 미러 인식 1.12.1-2)으로 사라져 정지하지 않는 쪽으로 바꿨다.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import StructureUnresolvedError, exit_code_for
from gmid_engine.graph import build_s1v

import s1v_hand as H

CMFB_SE = H.topo("cmfb_se", tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in H.CMFB["netlist"]),
                 {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.SE_OUT, "om": H.SE_OUT},
                 passives=tuple((e["name"], e["kind"], tuple(e["terminals"])) for e in H.CMFB["passive_elements"]),
                 bias=("vb", "vref"))


@pytest.mark.parametrize("budget", [True, False, 0, -3, 1.5, "100", None])
def test_count_budget_must_be_positive_int(tmp_path, budget):
    s1, _ = H.build(tmp_path, H.CS)
    with pytest.raises(TypeError):
        build_s1v(s1, None, count_budget=budget)


def test_count_budget_is_keyword_only(tmp_path):
    s1, _ = H.build(tmp_path, H.CS)
    with pytest.raises(TypeError):
        build_s1v(s1, None, H.BIG_BUDGET)          # noqa -- 위치 인자 금지(시그니처 `*, count_budget`)


def test_deterministic_and_field_reuse(tmp_path):
    """[U17 ①-b] 옛 `previous=` 인자(같은 키면 그 객체 `is`)는 설계 40 v1.9.1 §2.4.2 로 없어졌다 -- 재사용은 계산 블록 입력 버전으로 한다
    ('입력 버전이 같으면 다시 계산하지 않는다'). 같은 입력의 두 결과는 S1v 필드 값이 같고(결정론), S1v 필드가 이미 있는 S1Graph 위에 같은
    입력으로 다시 부르면 블록 `s1v_fields` 는 계산하지 않고(computes 0, reuses 1) 같은 스냅샷을 돌려준다. 예산이 다르면 다시 계산한다."""
    from gmid_engine.graph import s1v_fields
    s1, first = H.build(tmp_path, H.CMFB)
    fields = ("views", "l_classes", "findings", "declared", "applied_facts")
    again = H.read_s1v(build_s1v(s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False))
    assert [getattr(again, f) for f in fields] == [getattr(first, f) for f in fields]
    s1v_fields.reset_stats()
    reused = build_s1v(first.graph, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False)
    st = s1v_fields.stats()
    assert (st.computes, st.reuses) == (0, 1)
    assert reused.snapshot is first.graph.snapshot
    other = build_s1v(first.graph, None, count_budget=H.BIG_BUDGET + 1, stop_on_unsupported=False)
    assert s1v_fields.stats().computes == 1 and other.snapshot is not first.graph.snapshot


STOPPERS = [
    (H.AMB, "cell_ambiguous", {}),
    (H.PASS3, "pass_group_unsupported", {}),
    (H.TAP, "gate_on_current_node", {}),
    (H.CSDIODE, "cs_output_low_impedance", {}),
    (H.BMULTI, "buffer_multi_output", {}),
    (H.XCOUP, "loop_record_only", {}),
    (H.RFB, "loop_record_only", {}),
    (H.CMFB, "cycle_enumeration_over_budget", {"count_budget": 1}),
    (CMFB_SE, "undeclared_loop_constraint", {}),
]


@pytest.mark.parametrize("doc,code,kw", STOPPERS, ids=[c for _, c, _ in STOPPERS])
def test_invariant8_record_only_code_stops_by_default(tmp_path, doc, code, kw):
    _, diag = H.build(tmp_path, doc, **kw)
    assert code in [f.code for f in diag.unsupported]
    with pytest.raises(StructureUnresolvedError) as ei:
        H.build(tmp_path, doc, stop_on_unsupported=True, **kw)
    assert exit_code_for(ei.value) == 2
    d = dict(ei.value.record.detail)
    assert d["reason"] == "unsupported_rule_branch"
    assert code in d["branches"]
    assert d["rule_branch"] == d["branches"][0]
    assert len(d["findings"]) == len(diag.unsupported)


def test_library_sf_no_longer_stops_after_j_rules():
    # [U1b] 41 1.13 sf 행: 복합 diode(1.12.1) 미러 인식으로 이득 블록 {Y} 하나 + 버퍼 블록 {vout}, composite_dag_not_chain·
    # record_only·혼재 정지가 사라진다 -> 기본 모드(stop_on_unsupported=True)에서도 정지하지 않는다
    _, s1v = H.build_lib("sf_pushpull_output_opamp", stop_on_unsupported=True)
    assert s1v.unsupported == ()
    codes = H.all_codes(s1v)
    for gone in ("composite_dag_not_chain", "loop_record_only", "mixed_drive_unresolved_group", "composite_block_pending_ratify"):
        assert gone not in codes
    assert {b.key: b.kind for b in H.view(s1v).blocks} == {("Y",): "gain", ("vout",): "buffer"}


def test_clean_circuits_do_not_stop(tmp_path):
    for doc in (H.OTA5, H.MILLER, H.FOLDED, H.CS, H.CG, H.FOLLOWER, H.PUSHPULL, H.CMFB, H.REPLICA):
        _, s1v = H.build(tmp_path, doc, stop_on_unsupported=True)
        assert s1v.unsupported == (), doc["topology_name"]


# ------------------------------------------------------------------ 불변량 2: 이름 전단사 + 순서 섞기
def _bijection(doc):
    """정렬 순서를 뒤집는 새 이름(이름 tie-break 가 결과를 바꾸면 드러나게)."""
    nets = sorted(H.json_nets(doc))
    elems = sorted(H.json_mos(doc) | {e["name"] for e in doc["passive_elements"]})
    nmap = {n: "w%02d" % (len(nets) - i) for i, n in enumerate(nets)}
    dmap = {n: "E%02d" % (len(elems) - i) for i, n in enumerate(elems)}
    return nmap, dmap


def _canon(s1v, nm, dm):
    """구조 필드를 사상 nm(넷)·dm(원소)으로 옮긴 비교용 표현(뷰는 kind+여기 넷 집합으로 짝짓는다)."""
    n = lambda x: nm.get(x, x)  # noqa: E731
    d = lambda x: dm.get(x, x)  # noqa: E731
    out = {}
    for v in s1v.views:
        vk = (v.kind, frozenset(n(x) for x, _ in v.excite))
        out[vk] = {
            "ground": frozenset(map(n, v.ac_ground)),
            "vg": frozenset(map(n, v.virtual_ground)),
            "signal": frozenset(map(n, v.signal_nets)),
            "forward": frozenset(map(n, v.forward_nets)),
            "cells": frozenset((d(c.dev), c.kind) for c in v.cells),
            "drive": frozenset((n(i.net), i.kind) for i in v.drive_kind),
            "starts": frozenset(map(d, v.stage_starts)),
            "blocks": frozenset((tuple(sorted(map(n, b.key))), b.kind, b.stage, frozenset((d(x), r) for x, r in b.roles))
                                for b in v.blocks),
            "poles": frozenset((n(p.net), p.impedance) for p in v.pole_nodes),
            "loops": frozenset((frozenset(map(n, lp.nodes)), lp.classes, (d(lp.cut[0]), n(lp.cut[1])) if lp.cut else (),
                                lp.polarity) for lp in v.loops),
            "outdir": frozenset((n(o.net), frozenset((d(x), k) for x, k in o.charge),
                                 frozenset((d(x), k) for x, k in o.discharge), o.topology) for o in v.output_direction),
            "findings": frozenset((f.code, f.severity) for f in v.findings),
        }
    out["l_classes"] = frozenset((frozenset(map(d, lc.members)), lc.status) for lc in s1v.l_classes)
    return out


@pytest.mark.parametrize("doc", [H.MILLER, H.FOLDED, H.CMFB, H.REPLICA, H.FF, H.TAP, H.XCOUP, H.PASS, H.BIASSCC,
                                 H.LCREV, H.OTA5], ids=lambda d: d["topology_name"])
def test_invariant2_rename_and_shuffle(tmp_path, doc):
    nm, dm = _bijection(doc)
    _, base = H.build(tmp_path, doc, stem="base")
    _, moved = H.build(tmp_path, H.rename(doc, nm, dm, seed=3), stem="moved",
                       supplies={nm[r]: v for r, v in H.SUPPLIES.items()})
    assert _canon(base, nm, dm) == _canon(moved, {}, {})
    loop_ids = sorted("loop:%s:%s" % (dm[v.id.split(":")[1]], nm[v.id.split(":")[2]]) for v in base.views if v.kind == "loop")
    assert loop_ids == sorted(v.id for v in moved.views if v.kind == "loop")
    # L 동치류 주인: 사상을 따르지 않는 주인은 이름 tie-break 하나의 규칙(owner_rule 같음)에서만 나올 수 있다(불변량 2 예외).
    # tail·diode 기준이 있는 동치류(OTA5·MILLER·CMFB·FOLDED {M7, M8})의 주인은 사상을 따른다(아래 손 유도 목록).
    moved_owner = {frozenset(lc.members): lc.owner for lc in moved.l_classes}
    broken = {lc.owner_rule for lc in base.l_classes if moved_owner[frozenset(map(dm.get, lc.members))] != dm[lc.owner]}
    assert len(broken) <= 1, broken
    must_follow = {"ota5": ("M3",), "miller": ("M3", "M5"), "cmfb": ("M0", "M8"), "folded": ("M7",)}
    for owner in must_follow.get(doc["topology_name"], ()):
        lc = next(c for c in base.l_classes if c.owner == owner)
        assert moved_owner[frozenset(map(dm.get, lc.members))] == dm[owner]


# ------------------------------------------------------------------ [U1b] structure.json 사실 소비(40 3.2-3 '소비 방식')
import jrules_hand as J  # noqa: E402


def _lib_facts(name, *rows):
    st = J.facts(*rows)
    from gmid_engine.authoring import load_topology
    from gmid_engine.graph import build_s1
    s1 = build_s1(load_topology(str(H.LIBRARY / (name + ".topology.json"))), H.lib_supplies(name), structure=st)
    return H.read_s1v(build_s1v(s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False, structure=st))


def _review(s1v, code):
    return sorted((f.subject, f.severity) for f in s1v.findings if f.code == code)


def test_loop_role_confirm_ratifies():
    # 40 3.2-3 사실 표 ngcc `loop_role` loop:M8:V1 = compensation_internal(confirm) -- 유도(41 1.12.3)와 같다 -> ratified + approval_id
    s1v = _lib_facts("ngcc_3stage_ff", ("loop_role", "loop:M8:V1", "compensation_internal", "B-5"))
    roles = [(r.loop_id, r.role, r.status, r.approval_id) for v in s1v.views for r in v.loop_roles]
    assert roles == [("loop:M8:V1", "compensation_internal", "ratified", "B-5")]
    assert ("loop_role", "loop:M8:V1") in s1v.facts_applied
    assert _review(s1v, "structure_fact_mismatch") == [] and _review(s1v, "structure_fact_orphan") == []


def test_feedforward_cell_confirm_ratifies_whole_bundle():
    # 40 3.2-3 사실 표 ngcc `feedforward_cell`(confirm): FF1 = M6B·M7 ff, M6A ff_load, M5 ff_bias (탭 ND, merge Vout), FF2 = M14 ff
    # (탭 V1). 묶음의 모든 소자에 일치 사실이 있으면 그 FeedforwardCell 이 ratified(계약 10.6)
    s1v = _lib_facts("ngcc_3stage_ff", ("feedforward_cell", "M6B", "ff:ND->Vout", "A-5"), ("feedforward_cell", "M7", "ff:ND->Vout", "A-5"),
                     ("feedforward_cell", "M6A", "ff_load:ND->Vout", "A-5"), ("feedforward_cell", "M5", "ff_bias:ND->Vout", "A-5"),
                     ("feedforward_cell", "M14", "ff:V1->Vout", "A-6"))
    got = {(c.tap, c.merge): (c.status, c.approval_id) for v in s1v.views for c in v.feedforward}
    assert got == {("ND", "Vout"): ("ratified", "A-5"), ("V1", "Vout"): ("ratified", "A-6")}
    assert _review(s1v, "structure_fact_mismatch") == [] and _review(s1v, "structure_fact_orphan") == []


def test_partial_feedforward_confirm_does_not_ratify_bundle():
    # 묶음 소자 일부(M7)에만 사실 -> 그 묶음은 derived 그대로(계약 10.6 '묶음의 모든 소자에 일치하는 사실이 있을 때')
    s1v = _lib_facts("ngcc_3stage_ff", ("feedforward_cell", "M7", "ff:ND->Vout", "A-5"))
    got = {(c.tap, c.merge): c.status for v in s1v.views for c in v.feedforward}
    assert got == {("ND", "Vout"): "derived", ("V1", "Vout"): "derived"}


@pytest.mark.parametrize("row,subject", [
    (("loop_role", "loop:M8:V1", "loop_view", "C-1"), ("loop:M8:V1",)),                 # 유도 = compensation_internal
    (("feedforward_cell", "M14", "ff:ND->Vout", "C-2"), ("M14",)),                       # 유도 = ff:V1->Vout
    (("feedforward_cell", "M5", "ff_load:ND->Vout", "C-3"), ("M5",)),                    # 유도 = ff_bias
])
def test_confirm_mismatch_is_review_needed(row, subject):
    s1v = _lib_facts("ngcc_3stage_ff", row)
    assert (subject, "review_needed") in _review(s1v, "structure_fact_mismatch")
    # 유도 값은 그대로(사실이 덮지 않는다)
    roles = {r.loop_id: (r.role, r.status) for v in s1v.views for r in v.loop_roles}
    assert roles == {"loop:M8:V1": ("compensation_internal", "derived")}


@pytest.mark.parametrize("row,subject", [
    (("loop_role", "loop:M99:V1", "loop_view", "D-1"), ("loop:M99:V1",)),               # 그런 루프 없음
    (("feedforward_cell", "M12", "ff:V1->Vout", "D-2"), ("M12",)),                       # M12 는 FF 묶음 소자가 아님
    (("dc_role", "Mzz", "signal", "D-3"), ("Mzz",)),                                    # 그런 소자 없음
    (("drive_kind", "no_such_net", "voltage", "D-4"), ("no_such_net",)),                # topology 에 없는 넷
    (("ac_ground_exception", "V2", "loop:M1:X", "D-5"), ("V2",)),                       # 그런 뷰 없음
    (("matching_pair", '["M5","Mq"]', "branch_symmetric", "D-6"), ('["M5","Mq"]',)),    # 멤버 Mq 없음
])
def test_fact_about_missing_subject_is_orphan(row, subject):
    s1v = _lib_facts("ngcc_3stage_ff", row)
    assert _review(s1v, "structure_fact_orphan") == [(subject, "review_needed")]
    assert s1v.facts_applied == ()


def test_dc_role_override_resolves_unresolved_group_review():
    # 41 1.11 ③ / 1.13: ngcc {M8, M14} 는 기준 없는 그룹 -> 사실이 없으면 dc_role_unresolved_group(review_needed, 그룹 단위),
    # override 사실(40 3.2-3 표, M8·M14 = signal)이 있으면 사라지고 L 동치류 {M8, M14} 도 derived(주인 M8 main_path_signal)
    plain = _lib_facts("ngcc_3stage_ff")
    assert _review(plain, "dc_role_unresolved_group") == [(("M14", "M8"), "review_needed")]
    fixed = _lib_facts("ngcc_3stage_ff", ("dc_role", "M8", "signal", "A-8"), ("dc_role", "M14", "signal", "A-14"))
    assert _review(fixed, "dc_role_unresolved_group") == []
    assert {("dc_role", "M8"), ("dc_role", "M14")} <= set(fixed.facts_applied)
    lc = {c.members: (c.owner, c.owner_rule, c.status) for c in fixed.l_classes}
    assert lc[("M14", "M8")] == ("M8", "main_path_signal", "derived")


@pytest.mark.parametrize("doc", [J.FF3, J.NMC3, J.SFLOAD, J.FDIFF, J.POL_AC], ids=lambda d: d["topology_name"])
def test_invariant2_rename_on_u1b_toys(tmp_path, doc):
    # 41 1.11 불변식을 U1b 손 회로에도 건다(필드 표현은 위 _canon 재사용 -- 셀·블록·루프·극성·기록 코드)
    nm, dm = _bijection(doc)
    _, base = H.build(tmp_path, doc, stem="base")
    _, moved = H.build(tmp_path, H.rename(doc, nm, dm, seed=11), stem="moved",
                       supplies={nm[r]: v for r, v in H.SUPPLIES.items()})
    assert _canon(base, nm, dm) == _canon(moved, {}, {})
    roles = lambda s1v, n, d: {(r.role, r.view.split(":")[0]) for v in s1v.views for r in v.loop_roles}  # noqa: E731
    assert roles(base, nm, dm) == roles(moved, {}, {})
