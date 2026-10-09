"""`place_layout(memo, snapshot, pdk, passives, rejected, relaxed, first_seen, previous, kinds, current_keys) -> PlacedLayout` (CONTRACT 7절,
설계 40 §3.9 gap (a) '폭 키를 kind 당 하나로 좁힌다', 계획 LY5 완화 판정, CONTRACT 11절 불변식 2).

oracle (a): `run_layout`·`layout_input_of` 를 스크립트 가짜로 바꿔(monkeypatch) 입력(PDK 폭 키·완화 집합)에 따라 손으로 정한 레이아웃을 돌려준다.
기대 반복(좁히기 시험 수, 고른 키, 완화 집합, first_seen)은 스크립트와 CONTRACT 7절 규칙에서 손으로 센다.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from gmid_engine.convergence import PlacedLayout, place_layout

from .conftest import GRID, dlay, dunplaced, floorplan, glay, layout, module, pdk

KINDS = {"A": "nmos", "B": "nmos", "C": "pmos"}
CUR = (("nmos", 1000), ("pmos", 1000))


class Script:
    """가짜 run_layout: `fn(layout_input) -> LayoutResult`. 호출마다 (nmos 폭 키, 완화 집합, rejected, previous) 를 기록한다."""

    def __init__(self, fn, hubs=()):
        self.fn, self.calls, self.hubs = fn, [], dict(hubs)

    def layout_input_of(self, snapshot, pdk_, passives, rejected=(), relaxed=()):
        mg = tuple(SimpleNamespace(gid=g, hub_net=h) for g, h in sorted(self.hubs.items()))
        return SimpleNamespace(pdk=pdk_, relaxed=frozenset(relaxed), rejected=tuple(rejected), passives=passives, matching_groups=mg), ()

    def run_layout(self, li, memo, previous):
        self.calls.append((dict(li.pdk.slice_width_keys)["nmos"], li.relaxed, li.rejected, previous, memo))
        return self.fn(li)


@pytest.fixture
def patch(monkeypatch):
    mod = module("place_layout")

    def install(script):
        monkeypatch.setattr(mod, "run_layout", script.run_layout)
        monkeypatch.setattr(mod, "layout_input_of", script.layout_input_of)
        return script
    return install


def dev3(nkey_a, nkey_b, area):
    return layout(devices=(dlay("A", nkey_a * GRID, 2, 2 * nkey_a * GRID), dlay("B", nkey_b * GRID, 2, 2 * nkey_b * GRID),
                           dlay("C", 40 * GRID, 1, 40 * GRID)), plan=floorplan(1e-5, 1e-5, area=area))


def test_conflict_narrows_kind_to_best_scoring_key(patch):
    def fn(li):
        keys = dict(li.pdk.slice_width_keys)["nmos"]
        if keys == (10, 20, 30):
            return dev3(10, 20, 5e-10)                       # nmos 가 키 10·20 둘 다 씀 -> 충돌
        if keys == (10,):                                    # 시험: CC 그룹 미배치(점수 2칸 1) -- 면적은 더 작다
            return layout(devices=dev3(10, 10, 1e-10).devices, groups=(glay("g", "diff_pair", ("A", "B")),),
                          plan=floorplan(1e-5, 1e-5, area=1e-10))
        if keys == (20,):                                    # 시험: 모두 배치(점수 2칸 0) -> 고른다
            return dev3(20, 20, 9e-10)
        raise AssertionError(keys)
    s = patch(Script(fn, hubs=(("g", "tail"),)))
    base = pdk((("nmos", (10, 20, 30)), ("pmos", (40,))))
    first_seen, relaxed = {}, set()
    out = place_layout("MEMO", "SNAP", base, ("pas",), ("R",), relaxed, first_seen, None, KINDS, CUR)
    assert isinstance(out, PlacedLayout)
    assert [c[0] for c in s.calls] == [(10, 20, 30), (10,), (20,), (20,)]      # 1 + 시험 2 + 다시 1
    assert out.layout_calls == 4
    assert out.narrowed == (("nmos", 20),)
    assert out.pdk.slice_width_keys == (("nmos", (20,)), ("pmos", (40,)))
    assert out.keys == (("nmos", 20), ("pmos", 40))
    assert [(p.name, p.key) for p in out.placements] == [("A", 20), ("B", 20), ("C", 40)]
    assert out.unplaced == () and out.relaxed == frozenset()
    assert all(c[2] == ("R",) and c[4] == "MEMO" for c in s.calls)              # rejected·memo 를 그대로 넘긴다
    assert s.calls[0][3] is None and s.calls[1][3] is not None                   # previous = 앞 호출 결과(graph 캐시)
    assert base.slice_width_keys == (("nmos", (10, 20, 30)), ("pmos", (40,)))   # 입력 PDK 불변
    assert first_seen == {} and relaxed == set()


def test_score_tie_picks_smaller_key(patch):
    def fn(li):
        keys = dict(li.pdk.slice_width_keys)["nmos"]
        if keys == (10, 20):
            return dev3(10, 20, 5e-10)
        return dev3(keys[0], keys[0], 4e-10)                 # 두 시험 점수 동일
    s = patch(Script(fn))
    out = place_layout("M", "S", pdk((("nmos", (10, 20)), ("pmos", (40,)))), (), (), set(), {}, None, KINDS, CUR)
    assert out.narrowed == (("nmos", 10),)
    assert [c[0] for c in s.calls] == [(10, 20), (10,), (20,), (10,)]


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
    out = place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), set(), {}, None, kinds, CUR)
    assert [c[1] for c in s.calls] == [frozenset(), frozenset({"g"})]
    assert out.layout_calls == 2
    assert out.relaxed == frozenset({"g"})                               # hub 없는 h 는 완화하지 않는다
    assert out.first_seen == {"g": g_first, "h": h_first}                # 완화 전 GroupLayout, gid 별 처음 한 번
    assert out.first_seen["h"].reason == "first"


def test_already_relaxed_and_first_seen_inputs_are_kept(patch):
    keep = glay("old", "diff_pair", ("X", "Y"), reason="kept")
    s = patch(Script(lambda li: layout(devices=(dlay("A", 1e-6, 1, 1e-6),))))
    relaxed, seen = {"old"}, {"old": keep}
    out = place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), relaxed, seen, None, {"A": "nmos"}, CUR)
    assert s.calls[0][1] == frozenset({"old"})
    assert out.relaxed == frozenset({"old"}) and out.first_seen == {"old": keep}
    assert relaxed == {"old"} and seen == {"old": keep}


def test_unplaced_stops_immediately(patch):
    s = patch(Script(lambda li: layout(devices=(dlay("A", 1e-6, 1, 1e-6), dunplaced("B")),
                                       groups=(glay("g", "diff_pair", ("A", "B")),))))
    out = place_layout("M", "S", pdk((("nmos", (100,)), ("pmos", (40,)))), (), (), set(), {}, None, KINDS, CUR)
    assert len(s.calls) == 1 and out.layout_calls == 1
    assert out.unplaced == ("B",)
    assert out.keys == () and out.relaxed == frozenset() and out.first_seen == {}
