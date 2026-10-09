"""`mirror_ratio` -- 설계 40 §3.8-8 `mirror_ratio_sigma_pct`(S1 mirror 계열 matching 그룹마다 σ(ΔI/I) = (gm/ID)·σ_ΔVGS,pair, pct, 보고),
체크리스트 D-MR, metrics CONTRACT 10.4: 기준 diode(DC 역할 `ROLE_DIODE`)가 있으면 (기준, 나머지) 쌍, 없으면 전쌍,
σ = √((gm/ID_a·σ_a)² + (gm/ID_b·σ_b)²), 값 = 그룹·쌍 최댓값.

oracle (a) 물리: 같은 VGS 의 전류 상대 오차 ΔI/I = (gm/ID)·ΔVGS, 독립 두 소자 오차의 차의 σ 는 RSS. 손 수치:
gm/ID 10, σ 1 mV 두 소자 -> 10·1e-3·√2 = 1.41421 %. (gm/ID 10, 1 mV)·(20, 1 mV) -> √(1e-4 + 4e-4) = 2.23607 %.
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.graph import ROLE_DIODE
from gmid_engine.metrics import MirrorRatio, mirror_ratio

from .conftest import codes


def test_two_equal_devices_root2():
    got = mirror_ratio((("whole", ("Ma", "Mb")),), (("Ma", ROLE_DIODE),), (("Ma", 10.0), ("Mb", 10.0)),
                       (("Ma", 1e-3, None), ("Mb", 1e-3, None)))
    assert isinstance(got, MirrorRatio) and got.undefined == ()
    assert got.sigma_pct == pytest.approx(10.0 * 1e-3 * math.sqrt(2.0) * 100.0, rel=1e-12)


def test_reference_pairs_only_when_diode_present():
    """기준 Ma 가 있으면 쌍은 (Ma, Mb)·(Ma, Mc) 뿐 -- (Mb, Mc) 의 더 큰 값은 쓰지 않는다."""
    gmid = (("Ma", 10.0), ("Mb", 10.0), ("Mc", 30.0))
    sig = (("Ma", 1e-3, None), ("Mb", 1e-3, None), ("Mc", 2e-3, None))
    with_ref = mirror_ratio((("whole", ("Ma", "Mb", "Mc")),), (("Ma", ROLE_DIODE),), gmid, sig)
    want_ref = max(math.hypot(10e-3, 10e-3), math.hypot(10e-3, 60e-3)) * 100
    assert with_ref.sigma_pct == pytest.approx(want_ref, rel=1e-12)
    no_ref = mirror_ratio((("whole", ("Ma", "Mb", "Mc")),), (), gmid, sig)
    want_all = max(math.hypot(10e-3, 10e-3), math.hypot(10e-3, 60e-3), math.hypot(10e-3, 60e-3)) * 100
    assert no_ref.sigma_pct == pytest.approx(want_all, rel=1e-12)


def test_unequal_gmid_general_form_and_max_over_groups():
    gmid = (("Ma", 10.0), ("Mb", 20.0), ("Mc", 12.0), ("Md", 12.0))
    sig = (("Ma", 1e-3, None), ("Mb", 1e-3, None), ("Mc", 1e-3, None), ("Md", 1e-3, None))
    got = mirror_ratio((("whole", ("Ma", "Mb")), ("bias_distribution", ("Mc", "Md"))), (), gmid, sig)
    g1 = math.hypot(10e-3, 20e-3) * 100
    g2 = 12e-3 * math.sqrt(2.0) * 100
    assert got.sigma_pct == pytest.approx(max(g1, g2), rel=1e-12)
    table = {row[0]: row for row in got.groups}
    assert table["whole"][3] == pytest.approx(g1, rel=1e-12) and table["bias_distribution"][3] == pytest.approx(g2, rel=1e-12)
    assert table["whole"][1] == ("Ma", "Mb") and table["whole"][2] == ()


def test_resolution_from_sigma_tolerances():
    """분해능 = 최댓값 쌍에서 σ_a, σ_b 를 각각 +tol 로 흔든 변화 합(계약 10.4). 손: gm/ID 10, σ 1 mV, tol 0.1 mV 둘 다 ->
    2·(√(1.1² + 1²) − √2)·10 mV·100."""
    got = mirror_ratio((("whole", ("Ma", "Mb")),), (), (("Ma", 10.0), ("Mb", 10.0)), (("Ma", 1e-3, 1e-4), ("Mb", 1e-3, 1e-4)))
    want = 2 * (math.hypot(11e-3, 10e-3) - math.hypot(10e-3, 10e-3)) * 100
    assert got.resolution_pct == pytest.approx(want, rel=1e-10)
    none = mirror_ratio((("whole", ("Ma", "Mb")),), (), (("Ma", 10.0), ("Mb", 10.0)), (("Ma", 1e-3, 1e-4), ("Mb", 1e-3, None)))
    assert none.resolution_pct is None and none.sigma_pct is not None


def test_undefined_codes():
    gmid = (("Ma", 10.0),)
    assert codes(mirror_ratio((), (), gmid, (("Ma", 1e-3, None),)).undefined) == {"no_mirror_group"}
    got = mirror_ratio((("whole", ("Ma", "Mb")),), (), gmid, (("Ma", 1e-3, None),))
    assert got.sigma_pct is None and codes(got.undefined) == {"sigma_missing"}


def test_name_bijection_invariance():
    a = mirror_ratio((("whole", ("Ma", "Mb", "Mc")),), (("Mb", ROLE_DIODE),), (("Ma", 11.0), ("Mb", 9.0), ("Mc", 15.0)),
                     (("Ma", 1e-3, None), ("Mb", 2e-3, None), ("Mc", 1.5e-3, None)))
    b = mirror_ratio((("whole", ("Z", "Y", "X")),), (("Y", ROLE_DIODE),), (("Z", 11.0), ("Y", 9.0), ("X", 15.0)),
                     (("Z", 1e-3, None), ("Y", 2e-3, None), ("X", 1.5e-3, None)))
    assert a.sigma_pct == pytest.approx(b.sigma_pct, rel=1e-14)
