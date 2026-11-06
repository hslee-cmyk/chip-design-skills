"""WB-1 F-1/F-4 -- `reachable_slices`·`finger_slice` (interface card §2). 손 stub(`types.SimpleNamespace`)만 쓴다.

oracle (손): 기대값은 card §2 표의 손 유도(x = W/(key·g), k = floor(x), 반올림 규칙, 잔차 |m·key·g/W - 1|)이다.
피검 함수로 기대값을 만들지 않는다. 격자 g = 1e-8 이면 키 = 폭[m]/1e-8 정수.
"""
import math
import pathlib
import re
from types import SimpleNamespace

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import FingerSlice, LBin, LBinMap, finger_slice, reachable_slices

G = 1e-8


def _bins(w_bin=(1e-6, 5e-6), bins=(LBin("b", 5e-7, 3e-6),)):
    return LBinMap(model_files=(), w_bin=w_bin, bins=bins, anchor_bin=())


def make_lut(keys, ref_key, g=G, w_bin=(1e-6, 5e-6), w_min=1e-6, bins=(LBin("b", 5e-7, 3e-6),), kind="nmos"):
    lb = _bins(w_bin, bins)
    return SimpleNamespace(
        spec=SimpleNamespace(manufacturing_grid_m=g, min_finger_w_m=((kind, w_min),)),
        slice_map={(kind, k): SimpleNamespace(l_bins=lb) for k in keys},
        cap_map={kind: SimpleNamespace(w_key=ref_key)},
        bin_rule="lower")


def reason_of(exc):
    return dict(exc.record.detail)["reason"]


def detail(exc):
    return dict(exc.record.detail)


# ---------------------------------------------------------------- reachable_slices
def test_slice_reachable_common_stub_cuts_above_w_hi():
    lut = make_lut({200, 500, 700}, 500)
    # 손: w_hi = 5e-6 -> 키 500. 700 > 500 제외. W_min 1e-6 -> 100 이하 없음.
    assert reachable_slices(lut, "nmos", 1e-6) == (200, 500)


def test_slice_reachable_w_min_cuts_below():
    lut = make_lut({200, 500, 700}, 500, w_min=3e-6)
    assert reachable_slices(lut, "nmos", 1e-6) == (500,)           # 3e-6/1e-8 = 300 -> 200 제외


def test_slice_reachable_empty_cases():
    assert reachable_slices(make_lut({200, 500, 700}, 500), "nmos", 4e-6) == ()      # L 을 품는 bin 없음
    assert reachable_slices(make_lut({200, 500, 700}, None), "nmos", 1e-6) == ()     # 기준 키 None
    assert reachable_slices(make_lut({200, 500, 700}, 500, bins=()), "nmos", 1e-6) == ()   # bins 빈 값
    assert reachable_slices(make_lut({200, 700}, 500), "nmos", 1e-6) == ()           # 기준 슬라이스 없음


# ---------------------------------------------------------------- finger_slice
def _fs(lut, W, L=1e-6, kind="nmos"):
    calls = []

    def w_of(key):
        calls.append(key)
        return W
    return finger_slice(lut, kind, L, w_of), calls


@pytest.mark.parametrize("W, m, key", [
    (4e-6, 2, 200),      # 손: 200 -> x = 2, 잔차 0. 500 -> x = 0.8 -> m = 1, 잔차 0.25
    (12e-6, 6, 200),     # 손: 500 -> x = 2.4 -> m = 2, 잔차 1/6 > 0
    (0.5e-6, 1, 200),    # 손: W < w_s. 200 잔차 3, 500 잔차 9
])
def test_finger_slice_card_table(W, m, key):
    lut = make_lut({200, 500}, 500)
    out, calls = _fs(lut, W)
    assert isinstance(out, FingerSlice)
    assert out.m == m and out.w_key == key
    assert out.w_f_m == pytest.approx(key * G, rel=1e-12)
    assert sorted(calls) == [200, 500]                              # 키마다 w_of 한 번 (호출 >= 1)


def test_finger_slice_tie_prefers_larger_key():
    lut = make_lut({200, 400}, 400, w_bin=(1e-6, 4e-6))
    out, calls = _fs(lut, 12e-6)
    # 손: 200 -> x = 6, m = 6, 잔차 0. 400 -> x = 3, m = 3, 잔차 0. 동률 -> 큰 키
    assert (out.m, out.w_key) == (3, 400)
    assert out.w_f_m == pytest.approx(4e-6, rel=1e-12)
    assert calls


@pytest.mark.parametrize("x, m", [(2.5, 2), (2.6, 3), (0.4, 1)])
def test_finger_slice_rounding_exact_grid(x, m):
    g = 2.0 ** -26
    lut = make_lut({200}, 200, g=g, w_bin=(200 * g, 200 * g), w_min=200 * g)
    out, calls = _fs(lut, x * 200 * g)
    # 손: x - k <= k + 1 - x 이면 k (2.5 는 동률 -> 아래), k = 0 이면 m = 1
    assert out.m == m and out.w_key == 200
    assert calls == [200]


def test_finger_slice_none_candidate_dropped():
    lut = make_lut({200, 500}, 500)

    def w_of(key):
        return None if key == 200 else 12e-6
    out = finger_slice(lut, "nmos", 1e-6, w_of)
    assert (out.m, out.w_key) == (2, 500)                           # 손: 500 만 남고 x = 2.4 -> m = 2
    assert out.w_f_m == pytest.approx(5e-6, rel=1e-12)


@pytest.mark.parametrize("bad", [0.0, -1e-6, math.nan, math.inf, None])
def test_finger_slice_all_invalid_widths_no_candidate(bad):
    lut = make_lut({200, 500}, 500)
    calls = []

    def w_of(key):
        calls.append(key)
        return bad
    with pytest.raises(SealViolationError) as ei:
        finger_slice(lut, "nmos", 1e-6, w_of)
    d = detail(ei.value)
    assert d["reason"] == "slice_missing" and d["why"] == "no_candidate"
    assert tuple(d["excluded"]) == (200, 500)
    assert sorted(calls) == [200, 500]


def test_finger_slice_w_of_error_propagates():
    lut = make_lut({200, 500}, 500)
    calls = []

    def w_of(key):
        calls.append(key)
        raise SealViolationError(detail={"reason": "lut_column_unavailable"})
    with pytest.raises(SealViolationError) as ei:
        finger_slice(lut, "nmos", 1e-6, w_of)
    assert reason_of(ei.value) == "lut_column_unavailable"
    assert calls


def test_finger_slice_no_w_hi_never_calls_w_of():
    lut = make_lut({200, 500}, None)
    calls = []

    def w_of(key):
        calls.append(key)
        return 4e-6
    with pytest.raises(SealViolationError) as ei:
        finger_slice(lut, "nmos", 1e-6, w_of)
    d = detail(ei.value)
    assert d["reason"] == "slice_missing" and d["why"] == "no_w_hi"
    assert calls == []
    # 같은 stub 에 기준 키를 주면 호출이 생긴다(공허 통과 방지)
    out, calls2 = _fs(make_lut({200, 500}, 500), 4e-6)
    assert calls2 and out.m == 2


def test_finger_slice_no_storage_two_calls_double_w_of_calls():
    lut = make_lut({200, 500}, 500)
    calls = []

    def w_of(key):
        calls.append(key)
        return 4e-6
    a = finger_slice(lut, "nmos", 1e-6, w_of)
    n1 = len(calls)
    b = finger_slice(lut, "nmos", 1e-6, w_of)
    assert n1 >= 1 and len(calls) == 2 * n1 and a == b


def test_finger_slice_frozen():
    out, _ = _fs(make_lut({200, 500}, 500), 4e-6)
    with pytest.raises(Exception) as ei:
        out.m = 9
    assert type(ei.value).__name__ in ("FrozenInstanceError", "AttributeError", "TypeError")


def test_finger_slice_single_definition_in_engine_source():
    # F-4: 정의 1곳 (소스 grep). 엔진 폴더 = tests 의 부모.
    root = pathlib.Path(__file__).resolve().parents[2]
    hits = {"finger_slice": [], "slice_of_finger": []}
    for p in root.rglob("*.py"):
        if "tests" in p.relative_to(root).parts:
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for name in hits:
            if re.search(r"^def %s\(" % name, txt, re.M):
                hits[name].append(p.name)
    assert len(hits["finger_slice"]) == 1 and len(hits["slice_of_finger"]) == 1, hits
