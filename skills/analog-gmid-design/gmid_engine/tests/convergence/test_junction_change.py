"""`junction_change(before, after) -> tuple[JunctionChange]` (CONTRACT 4절, DEC-91 (2)).

oracle (a): 두 가짜 스냅샷의 `ss_dev` 값을 손으로 놓고 소자(이름순, 둘에 모두 있는 것)마다 전·후를 읽는다.
"""
from __future__ import annotations

from gmid_engine.convergence import JunctionChange, junction_change

from .conftest import FakeSnapshot, ssdev


def test_pairs_devices_present_in_both_sorted():
    before = FakeSnapshot({("device", "ss_dev"): {"M2": ssdev(2e-15, 3e-15), "M1": ssdev(1e-15, 1.5e-15), "Mx": ssdev(9e-15, 9e-15)}})
    after = FakeSnapshot({("device", "ss_dev"): {"M1": ssdev(1.1e-15, 1.6e-15), "M2": ssdev(2.2e-15, 3.3e-15), "My": ssdev(7e-15, 7e-15)}})
    assert junction_change(before, after) == (JunctionChange("M1", 1e-15, 1.5e-15, 1.1e-15, 1.6e-15),
                                              JunctionChange("M2", 2e-15, 3e-15, 2.2e-15, 3.3e-15))


def test_empty_when_no_common_device():
    before = FakeSnapshot({("device", "ss_dev"): {"A": ssdev(1e-15, 1e-15)}})
    after = FakeSnapshot({("device", "ss_dev"): {"B": ssdev(1e-15, 1e-15)}})
    assert junction_change(before, after) == ()
