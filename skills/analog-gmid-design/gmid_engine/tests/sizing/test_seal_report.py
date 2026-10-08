"""`dc_seal_report(snapshot, item4, item5)` -- CONTRACT 6절: SealReport(items = 번호순 [r8] 9개, status) -- fail 있으면 violated,
아니고 undefined 있으면 undefined, 아니면 sealed. 항목 1·2·3·6·7·8·[r8] 9 는 graph 필드에서, 4·5 는 extras 로 받는다(11절 5).
"""
import itertools

import pytest

from gmid_engine.sizing import DC_KEY, SealItem, SealReport, dc_seal_report

from .conftest import theta_c

GRAPH_ITEMS = {1: "dc_seal_node_conflict", 2: "dc_seal_vgs_match", 3: "dc_seal_kcl", 6: "dc_seal_bulk_reverse",
               7: "dc_seal_saturation", 8: "dc_seal_kvl_branch", 9: "dc_seal_conduction"}
ITEMS = list(range(1, 10))                      # [r8] 9개


def with_statuses(snap, statuses):
    for n, w in GRAPH_ITEMS.items():
        snap = snap.write(w, "t-%d-%s" % (n, statuses[n]),
                          {("graph", "dc_seal_%d" % n): {DC_KEY: SealItem(n, statuses[n])}})
    return snap


def expected_status(sts):
    if "fail" in sts:
        return "violated"
    if "undefined" in sts:
        return "undefined"
    return "sealed"


def _case(**over):
    d = {i: "pass" for i in ITEMS}
    d.update({int(k[1:]): v for k, v in over.items()})
    return d


CASES = [_case(), _case(i7="undefined"), _case(i7="undefined", i2="fail"), _case(i4="fail"),
         _case(i5="undefined"), _case(i8="fail", i3="undefined"),
         _case(i9="fail"), _case(i9="undefined"), _case(i9="fail", i7="undefined")]          # [r8] 봉인 9


@pytest.mark.parametrize("sts", CASES)
def test_status_rule(ev_c, sts):
    snap = with_statuses(ev_c.snapshot, sts)
    out = dc_seal_report(snap, SealItem(4, sts[4]), SealItem(5, sts[5]))
    rep = out.value("graph", DC_KEY, "dc_seal_report")
    assert isinstance(rep, SealReport)
    assert [i.item for i in rep.items] == ITEMS
    assert [i.status for i in rep.items] == [sts[i] for i in ITEMS]
    assert rep.status == expected_status(list(sts.values()))


def test_all_combinations_status(ev_c):
    vals = ("pass", "fail", "undefined")
    for a, b, c in itertools.product(vals, vals, vals):
        sts = {i: "pass" for i in ITEMS}
        sts[1], sts[7], sts[9] = a, b, c
        rep = dc_seal_report(with_statuses(ev_c.snapshot, sts), SealItem(4, "pass"), SealItem(5, "pass")).value(
            "graph", DC_KEY, "dc_seal_report")
        assert rep.status == expected_status([a, b, c])


def test_report_of_real_evaluation(ev_c):
    rep = ev_c.snapshot.value("graph", DC_KEY, "dc_seal_report")
    assert rep == ev_c.report
    assert rep.status == "undefined"
    # 회로 C 기본 θ(vgs 0.6·0.7): 봉인 9 pass(누설 ≪ ε·ID), 7 만 undefined(toy 에 VDSAT 열 없음)
    assert [i.status for i in rep.items] == ["pass"] * 6 + ["undefined", "pass", "pass"]


def test_report_reuse_on_same_items(ev_c):
    snap = ev_c.snapshot
    i4, i5 = ev_c.report.items[3], ev_c.report.items[4]
    dc_seal_report.reset_stats()
    assert dc_seal_report(snap, i4, i5) is snap
    assert dc_seal_report.stats().reuses == 1
