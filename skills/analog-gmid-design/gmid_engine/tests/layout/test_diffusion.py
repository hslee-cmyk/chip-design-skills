"""CONTRACT 4.10a `diffusion_geometry(rows, devices, pdk) -> tuple[DeviceDiffusion]` (LY8, DEC-89 (5)·DEC-91 (2), U12 D-LY3 / R22).

소자별 finger 하나 평균 확산 기하(ad·as·pd·ps), BSIM4 perMod=1 둘레(게이트 쪽 변 W 포함). 영역 길이 D = pdk.finger_pitch_overhead_m,
영역 폭 = 행 finger_w W. 공유 영역(양쪽 finger) = finger 마다 W·D/2, 둘레 W + D. 섬 끝 영역 = W·D, 둘레 W + 2D + W(반대쪽 끝 변).

oracle: (d) 계약 손계산 예(CONTRACT 4.10a: 한 행 (A, B), 노드 (da, h, db), W 1 µm, D 0.28 µm -> A ad 0.28 pm², pd 2.56 µm, as 0.14 pm²,
ps 1.28 µm) + (a) 구성으로 정답이 정해진 합성 행(손계산 값을 주석에 적었다; 피검 함수로 만든 값 없음).
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import DeviceDiffusion, RowLayout
from gmid_engine.layout.diffusion import diffusion_geometry

from .conftest import dev, toy_pdk

W = 1e-6
D = 0.28e-6
# 손계산 단위 값(W = 1 µm, D = 0.28 µm)
END_A = W * D                 # 섬 끝 영역 면적  0.28 pm²
SHR_A = W * D / 2             # 공유 영역 면적(finger 하나 몫) 0.14 pm²
END_P = W + 2 * D + W         # 섬 끝 둘레 2.56 µm
SHR_P = W + D                 # 공유 둘레 1.28 µm


def mkrow(rid, seq, nodes, segments=None, fw=W, key=100):
    devs = {}
    for n in seq:
        devs[n] = devs.get(n, 0) + 1
    if segments is None:
        segments = ((tuple(seq), tuple(nodes)),)
    return RowLayout(rid, "r", "nmos", key, fw, 0.0, tuple(sorted(devs.items())), tuple(seq), tuple(nodes), tuple(segments),
                     "euler", 0, len(segments), True, None, False)


def by_name(out):
    assert all(isinstance(d, DeviceDiffusion) for d in out)
    names = [d.name for d in out]
    assert names == sorted(names)                                           # 소자 이름순
    return {d.name: d for d in out}


def check(d, n, ad, as_, pd, ps, fw=W):
    assert d.n_fingers == n
    assert d.finger_w_m == pytest.approx(fw, rel=1e-12)
    assert (d.ad_m2, d.as_m2, d.pd_m, d.ps_m) == pytest.approx((ad, as_, pd, ps), rel=1e-9)


@pytest.fixture
def pdk(toy_lut):
    return toy_pdk(toy_lut, overhead=D)


def test_contract_hand_example(pdk):
    # CONTRACT 4.10a 손계산 예 그대로: A 의 drain da = 섬 끝, source h = 공유. B 도 대칭(drain db 섬 끝, source h 공유).
    devices = {"A": dev("A", "h", "da", 1e-6), "B": dev("B", "h", "db", 1e-6)}
    out = by_name(diffusion_geometry((mkrow("r/w100", ("A", "B"), ("da", "h", "db")),), devices, pdk))
    assert set(out) == {"A", "B"}
    check(out["A"], 1, ad=0.28e-12, as_=0.14e-12, pd=2.56e-6, ps=1.28e-6)
    check(out["B"], 1, ad=0.28e-12, as_=0.14e-12, pd=2.56e-6, ps=1.28e-6)


def test_orientation_from_source_net(pdk):
    # 같은 행에서 A 의 source 를 섬 끝 넷 da 로 바꾸면 A 의 source·drain 값이 서로 바뀐다(영역의 넷 == source 이면 source 쪽).
    devices = {"A": dev("A", "da", "h", 1e-6), "B": dev("B", "h", "db", 1e-6)}
    out = by_name(diffusion_geometry((mkrow("r/w100", ("A", "B"), ("da", "h", "db")),), devices, pdk))
    check(out["A"], 1, ad=SHR_A, as_=END_A, pd=SHR_P, ps=END_P)
    check(out["B"], 1, ad=END_A, as_=SHR_A, pd=END_P, ps=SHR_P)


def test_two_fingers_shared_drain(pdk):
    # (M, M), 노드 (s, d, s): 가운데 drain 공유, 양끝 source 섬 끝.
    # 합: as = 2 WD, ad = 2 x WD/2 = WD, ps = 2 x END_P, pd = 2 x SHR_P -> finger 평균(/2):
    #   as 0.28 pm², ad 0.14 pm², ps 2.56 µm, pd 1.28 µm
    devices = {"M": dev("M", "s", "d", 2e-6)}
    out = by_name(diffusion_geometry((mkrow("r/w100", ("M", "M"), ("s", "d", "s")),), devices, pdk))
    check(out["M"], 2, ad=0.14e-12, as_=0.28e-12, pd=1.28e-6, ps=2.56e-6)


def test_three_fingers_alternating(pdk):
    # (M, M, M), 노드 (s, d, s, d): finger0 s끝·d공유, finger1 d공유·s공유, finger2 s공유·d끝.
    # 합: as = WD + WD/2 + WD/2 = 2WD, ad = 2WD, ps = END_P + 2 SHR_P = 5.12 µm, pd = 5.12 µm -> /3:
    #   ad = as = 0.18666... pm², pd = ps = 1.70666... µm
    devices = {"M": dev("M", "s", "d", 3e-6)}
    out = by_name(diffusion_geometry((mkrow("r/w100", ("M", "M", "M"), ("s", "d", "s", "d")),), devices, pdk))
    check(out["M"], 3, ad=0.56e-12 / 3, as_=0.56e-12 / 3, pd=5.12e-6 / 3, ps=5.12e-6 / 3)


def test_diffusion_break_islands_are_ends(pdk):
    # 섬 둘(segments): 각 finger 의 두 영역 모두 섬 끝 -> ad = as = WD, pd = ps = 2.56 µm
    devices = {"A": dev("A", "a1", "a2", 1e-6), "B": dev("B", "b1", "b2", 1e-6)}
    segs = ((("A",), ("a1", "a2")), (("B",), ("b1", "b2")))
    out = by_name(diffusion_geometry((mkrow("r/w100", ("A", "B"), ("a1", "a2", "b1", "b2"), segs),), devices, pdk))
    for n in ("A", "B"):
        check(out[n], 1, ad=END_A, as_=END_A, pd=END_P, ps=END_P)


def test_device_over_two_rows_averaged(pdk):
    # 접힌 소자: 행1 (M, M) 노드 (s, d, s) + 행2 (M) 노드 (s, d). 행2 finger 는 두 영역 모두 섬 끝.
    # 합: as = 2WD + WD = 3WD, ad = WD + WD = 2WD, ps = 2 END_P + END_P = 3 END_P, pd = 2 SHR_P + END_P = 5.12 µm -> /3:
    #   as 0.28 pm², ad 0.18666... pm², ps 2.56 µm, pd 1.70666... µm
    devices = {"M": dev("M", "s", "d", 3e-6)}
    rows = (mkrow("r/w100_split1", ("M",), ("s", "d")), mkrow("r/w100_split0", ("M", "M"), ("s", "d", "s")))
    out = by_name(diffusion_geometry(rows, devices, pdk))
    check(out["M"], 3, ad=0.56e-12 / 3, as_=0.28e-12, pd=5.12e-6 / 3, ps=2.56e-6)
    # 행 입력 순서와 무관
    assert diffusion_geometry(tuple(reversed(rows)), devices, pdk) == diffusion_geometry(rows, devices, pdk)


def test_region_length_is_pdk_overhead(toy_lut):
    # D 를 PDK 양으로만 받는다: D = 0 이면 면적 0, 둘레 = 게이트 쪽 변(공유 W, 섬 끝 2W). D = 0.5 µm 면 손계산 그대로.
    devices = {"A": dev("A", "h", "da", 1e-6), "B": dev("B", "h", "db", 1e-6)}
    rows = (mkrow("r/w100", ("A", "B"), ("da", "h", "db")),)
    z = by_name(diffusion_geometry(rows, devices, toy_pdk(toy_lut, overhead=0.0)))
    check(z["A"], 1, ad=0.0, as_=0.0, pd=2 * W, ps=W)
    h = by_name(diffusion_geometry(rows, devices, toy_pdk(toy_lut, overhead=0.5e-6)))
    check(h["A"], 1, ad=0.5e-12, as_=0.25e-12, pd=3e-6, ps=1.5e-6)          # W+2D+W = 3 µm, W+D = 1.5 µm


def test_finger_width_from_row(pdk):
    # 영역 폭 = 행 finger_w: W = 2 µm 행 -> 계약 예의 면적·둘레가 W 를 따라간다(ad = 2 x 0.28 = 0.56 pm², pd = 2+0.56+2 = 4.56 µm)
    devices = {"A": dev("A", "h", "da", 2e-6), "B": dev("B", "h", "db", 2e-6)}
    out = by_name(diffusion_geometry((mkrow("r/w200", ("A", "B"), ("da", "h", "db"), fw=2e-6, key=200),), devices, pdk))
    check(out["A"], 1, ad=0.56e-12, as_=0.28e-12, pd=4.56e-6, ps=2.28e-6, fw=2e-6)
