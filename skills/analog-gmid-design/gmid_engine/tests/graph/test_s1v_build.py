"""graph/s1v_build.py -- `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None,
stop_on_unsupported=True)`(계약 10.1·10.2 '기록과 정지', 10.3 불변량 1·2·8).

oracle (a):
- 인자: count_budget 은 1 이상 int(bool 거부) -- 그 밖 TypeError.
- 결정론·재사용(불변량 1): 같은 입력 두 번 -> `==`, 같은 키 previous -> `is`.
- 정지(불변량 8): `기록만` 코드가 하나라도 있으면 기본 모드에서 core `StructureUnresolvedError`(exit 2, detail reason
  `unsupported_rule_branch`, rule_branch = 첫 분기, branches, findings), `stop_on_unsupported=False` 는 기록을 돌려준다. review_needed 는
  정지가 아니다. 각 코드를 일으키는 손 회로는 해당 test 파일의 손 유도를 따른다.
- 이름 전단사·순서 섞기(불변량 2): 모든 구조 필드가 사상으로만 바뀐다. 예외 = 이름 tie-break 인 L 동치류 주인(owner_rule 이
  이름 순)·전달 뷰 순번.
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


def test_deterministic_and_previous_reuse(tmp_path):
    s1, first = H.build(tmp_path, H.CMFB)
    again = build_s1v(s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False)
    assert again == first and again is not first
    reused = build_s1v(s1, None, count_budget=H.BIG_BUDGET, stop_on_unsupported=False, previous=first)
    assert reused is first
    other = build_s1v(s1, None, count_budget=H.BIG_BUDGET + 1, stop_on_unsupported=False, previous=first)
    assert other is not first and other.key != first.key


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


def test_library_composite_dag_not_chain_stops():
    # sf_pushpull_output_opamp: 복합 블록 후보가 여럿이라 묶은 DAG 가 사슬이 아니다(계약 10.3 불변량 8 목록의 composite_dag_not_chain)
    _, diag = H.build_lib("sf_pushpull_output_opamp")
    assert "composite_dag_not_chain" in [f.code for f in diag.unsupported]
    with pytest.raises(StructureUnresolvedError):
        H.build_lib("sf_pushpull_output_opamp", stop_on_unsupported=True)


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
