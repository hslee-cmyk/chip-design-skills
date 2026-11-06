"""`place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, excluded=(), *, donors, counters) -> PlacedLayout` (CONTRACT 7절,
계획 LY5 완화 판정, CONTRACT 11절 불변식 2). [WB-1] kind 당 폭 키 좁히기(옛 설계 40 §3.9 gap (a))는 삭제 -- 소자마다 실현 기하의 슬라이스가 따로이고 키 제외는
행 그룹 단위 입력 `excluded` = ((행 그룹 rid, (뺀 폭 키, ...)), ...) 이다.

oracle (a): `run_layout`·`layout_input_of` 를 스크립트 가짜로 바꿔(monkeypatch) 입력(PDK 폭 키·완화 집합)에 따라 손으로 정한 레이아웃을 돌려준다.
기대 반복(좁히기 시험 수, 고른 키, 완화 집합, first_seen)은 스크립트와 CONTRACT 7절 규칙에서 손으로 센다.
[U17 1-e] `run_layout(layout_input, memo, snapshot, previous)`: 레이아웃 필드는 설계점 `snapshot` 위, 재시도 `previous` 는 같은 설계점 lineage 의 앞 결과
(design 40 v1.6 §2.4.7). hub 넷(완화 판정)은 레이아웃 결과 스냅샷의 `ly_groups_in` 필드에서 읽으므로 가짜 결과에 입력 그룹을 넣는다.
`PlacedLayout` 에 입력 사본 `layout_input` 은 없다.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from gmid_engine.convergence import PlacedLayout, place_layout

from .conftest import GRID, dlay, dunplaced, floorplan, glay, layout, module, pdk, with_groups_in

KINDS = {"A": "nmos", "B": "nmos", "C": "pmos"}


def _pair():
    """[XRUN-F1 card B C0] 새 실행 하나의 두 객체."""
    from gmid_engine.search import open_run
    return open_run()


def _run():
    donors, counters = _pair()
    return dict(donors=donors, counters=counters)


@pytest.mark.parametrize("missing", ["donors", "counters", "both"])
def test_run_pair_keywords_required(patch, missing):
    """B-T16(XRUN-F1 card B C6): place_layout 은 기존 인자 + 필수 키워드 donors·counters(기본값 없음) -- 빠지면 TypeError."""
    patch(Script(lambda li: layout(devices=(dlay("A", 1e-6, 1, 1e-6),))))
    kw = {k: v for k, v in _run().items() if missing != "both" and k != missing}
    with pytest.raises(TypeError):
        place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), set(), {}, None, {"A": "nmos"}, **kw)


class Script:
    """가짜 run_layout: `fn(layout_input) -> LayoutResult`. 호출마다 (nmos 폭 키, 완화 집합, rejected, previous, memo, 설계점 snapshot) 을 기록하고
    결과 스냅샷에 입력 그룹 필드(`ly_groups_in` = hub 넷)를 넣는다."""

    def __init__(self, fn, hubs=()):
        self.fn, self.calls, self.hubs, self.runs, self.excluded_seen = fn, [], dict(hubs), [], []

    def layout_input_of(self, snapshot, pdk_, passives, rejected=(), relaxed=(), excluded=()):
        self.excluded_seen.append(excluded)
        return SimpleNamespace(pdk=pdk_, relaxed=frozenset(relaxed), rejected=tuple(rejected), passives=passives, excluded=excluded), ()

    def run_layout(self, li, memo, snapshot, previous, *, donors, counters):
        # [XRUN-F1 card B C6] run_layout 의 두 키워드는 필수(기본값 없음) -- 가짜도 같은 서명이라 place_layout 이 넘기지 않으면 TypeError
        self.calls.append((dict(li.pdk.slice_width_keys)["nmos"], li.relaxed, li.rejected, previous, memo, snapshot))
        self.runs.append((donors, counters))
        return with_groups_in(self.fn(li), self.hubs.items())


@pytest.fixture
def patch(monkeypatch):
    mod = module("place_layout")

    def install(script):
        monkeypatch.setattr(mod, "run_layout", script.run_layout)
        monkeypatch.setattr(mod, "layout_input_of", script.layout_input_of)
        return script
    return install


def dev3_devices(nkey_a, nkey_b):
    return (dlay("A", nkey_a * GRID, 2, 2 * nkey_a * GRID), dlay("B", nkey_b * GRID, 2, 2 * nkey_b * GRID), dlay("C", 40 * GRID, 1, 40 * GRID))


def dev3(nkey_a, nkey_b, area):
    return layout(devices=dev3_devices(nkey_a, nkey_b), plan=floorplan(1e-5, 1e-5, area=area))


def test_relaxation_reruns_once_and_records_first_seen(patch):
    g_first = glay("g", "diff_pair", ("A", "B"), reason="w_request_rejected")
    h_first = glay("h", "branch_symmetric", ("C", "D"), reason="first")

    def fn(li):
        devs = (dlay("A", 1e-6, 1, 1e-6), dlay("B", 1e-6, 1, 1e-6), dlay("C", 1e-6, 1, 1e-6), dlay("D", 1e-6, 1, 1e-6))
        if "g" not in li.relaxed:
            return layout(devices=devs, groups=(g_first, h_first))
        return layout(devices=devs, groups=(glay("g", "mirror", ("A", "B"), pattern="interdigitation", ok=True),
                                            glay("h", "branch_symmetric", ("C", "D"), reason="second")))
    s = patch(Script(fn, hubs=(("g", "tail"), ("h", None))))
    kinds = {"A": "nmos", "B": "nmos", "C": "nmos", "D": "nmos"}
    out = place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), set(), {}, None, kinds, **_run())
    assert [c[1] for c in s.calls] == [frozenset(), frozenset({"g"})]
    assert out.layout_calls == 2
    assert out.relaxed == frozenset({"g"})                               # hub 없는 h 는 완화하지 않는다
    assert out.first_seen == {"g": g_first, "h": h_first}                # 완화 전 GroupLayout, gid 별 처음 한 번
    assert out.first_seen["h"].reason == "first"


def test_already_relaxed_and_first_seen_inputs_are_kept(patch):
    keep = glay("old", "diff_pair", ("X", "Y"), reason="kept")
    s = patch(Script(lambda li: layout(devices=(dlay("A", 1e-6, 1, 1e-6),))))
    relaxed, seen = {"old"}, {"old": keep}
    out = place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), relaxed, seen, None, {"A": "nmos"},
                       **_run())
    assert s.calls[0][1] == frozenset({"old"})
    assert out.relaxed == frozenset({"old"}) and out.first_seen == {"old": keep}
    assert relaxed == {"old"} and seen == {"old": keep}


def test_unplaced_stops_immediately(patch):
    s = patch(Script(lambda li: layout(devices=(dlay("A", 1e-6, 1, 1e-6), dunplaced("B")),
                                       groups=(glay("g", "diff_pair", ("A", "B")),))))
    out = place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), set(), {}, None, KINDS, **_run())
    assert len(s.calls) == 1 and out.layout_calls == 1
    assert out.unplaced == ("B",)
    assert out.relaxed == frozenset() and out.first_seen == {}


def test_excluded_row_group_keys_reach_layout_input_unchanged_and_pdk_is_not_narrowed(patch):
    """[WB-1 L-1] `excluded` 는 행 그룹별 뺀 폭 키로 `layout_input_of` 에 그대로 가고(여섯째 인자), PDK 폭 키 후보는 좁혀지지 않는다(kind 키 좁히기 삭제)."""
    s = patch(Script(lambda li: layout(devices=(dlay("A", 1e-6, 1, 1e-6),))))
    base = pdk((("nmos", (10, 20, 30)),))
    excl = (("R1", (20,)), ("R2", (10, 30)))
    out = place_layout("M", "S", base, (), (), set(), {}, None, {"A": "nmos"}, excl, **_run())
    assert s.excluded_seen == [excl] and len(s.calls) == 1             # 호출 >= 1 확인 뒤 값 단언 (공허 통과 방지)
    assert out.pdk.slice_width_keys == (("nmos", (10, 20, 30)),)       # PDK 후보 불변: 제외는 입력(excluded)으로만
    assert base.slice_width_keys == (("nmos", (10, 20, 30)),)
