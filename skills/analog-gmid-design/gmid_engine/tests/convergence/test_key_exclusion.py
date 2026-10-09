"""`key_exclusion(pdk, placements, kinds, sized_w, keys) -> ((kind, 키), narrower_pdk)` (CONTRACT 7절 끝, 설계 40 §3.9 gap (c)).

oracle (a): 손으로 고른 W 비에서 |ln(W/W_사이징)| 를 손으로 비교해 어긋남이 가장 큰 kind 를 정한다(동률 = kind 이름순).
"""
from __future__ import annotations

import math

from gmid_engine.convergence import key_exclusion
from gmid_engine.layout import LayoutPdk

from .conftest import pdk, placement


def test_largest_shift_kind_loses_its_current_key():
    # nmos: W 1.2 / 사이징 1.0 -> ln 1.2 = 0.182 ; pmos: W 1.5 / 1.0 -> ln 1.5 = 0.405 (더 큼) -> pmos 의 지금 키 40 을 뺀다
    base = pdk((("nmos", (10, 20)), ("pmos", (30, 40, 50))))
    pl = (placement("N", 10, 12, 1.2e-6), placement("P", 40, 3, 1.5e-6))
    excluded, narrower = key_exclusion(base, pl, {"N": "nmos", "P": "pmos"}, {"N": 1e-6, "P": 1e-6}, (("nmos", 10), ("pmos", 40)))
    assert math.log(1.5) > math.log(1.2)
    assert excluded == ("pmos", 40)
    assert isinstance(narrower, LayoutPdk)
    assert narrower.slice_width_keys == (("nmos", (10, 20)), ("pmos", (30, 50)))
    assert base.slice_width_keys == (("nmos", (10, 20)), ("pmos", (30, 40, 50)))   # 입력 불변
    # 나머지 PDK 필드는 그대로
    assert (narrower.manufacturing_grid_m, narrower.rule_ids, narrower.source_fp) == (base.manufacturing_grid_m, base.rule_ids, base.source_fp)


def test_shrinking_w_counts_by_absolute_log_ratio():
    # nmos: W 0.5 / 1.0 -> |ln 0.5| = 0.693 > pmos ln 1.5 = 0.405 -> nmos
    base = pdk((("nmos", (10, 20)), ("pmos", (30, 40))))
    pl = (placement("N", 20, 1, 0.5e-6), placement("P", 30, 1, 1.5e-6))
    excluded, narrower = key_exclusion(base, pl, {"N": "nmos", "P": "pmos"}, {"N": 1e-6, "P": 1e-6}, (("nmos", 20), ("pmos", 30)))
    assert excluded == ("nmos", 20)
    assert narrower.slice_width_keys == (("nmos", (10,)), ("pmos", (30, 40)))


def test_tie_breaks_by_kind_name():
    base = pdk((("nmos", (10, 20)), ("pmos", (30, 40))))
    pl = (placement("N", 20, 1, 2e-6), placement("P", 30, 1, 2e-6))         # 둘 다 ln 2
    excluded, _ = key_exclusion(base, pl, {"N": "nmos", "P": "pmos"}, {"N": 1e-6, "P": 1e-6}, (("nmos", 20), ("pmos", 30)))
    assert excluded == ("nmos", 20)


def test_last_key_of_kind_gives_none():
    base = pdk((("nmos", (20,)), ("pmos", (30, 40))))
    pl = (placement("N", 20, 1, 3e-6),)
    excluded, narrower = key_exclusion(base, pl, {"N": "nmos"}, {"N": 1e-6}, (("nmos", 20), ("pmos", 30)))
    assert excluded == ("nmos", 20)
    assert narrower is None
