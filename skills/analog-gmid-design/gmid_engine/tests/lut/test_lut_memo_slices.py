"""WB-1 T-3 (interface card 20261104-wb1 §8 memo): 슬라이스 조회 하나의 U 계수 = 그 kind `widths` 수, 같은 키 재계산 0.

oracle (손): 합성 LUT 슬라이스 키 {100, 200} 두 장(`sizing/wb1_toy`). `finger_slice` 가 키마다 `w_of(key)` 를 한 번씩 부르고 `w_of` 는 키마다
`op_point(memo, kind, key, ...)` 를 한 번 조회한다. 계수 상태 memo(`LutMemo.counting`)에서 창 안 서로 다른 키 수 U = 2 이므로 상한 = (n_θ + 1)·U = (0 + 1)·2.
같은 조회를 한 번 더 하면 계산(miss) 0, 적중(hit) 2. 호출 수 단언마다 호출 >= 1 을 같은 test 에서 단언한다.
"""
import pytest

from gmid_engine.lut import LutMemo, TableCache, finger_slice, op_point, widths
from gmid_engine.core import LruStats

from sizing.wb1_toy import write_r4_bins_lut

L = 1e-6


def stats(m):
    return dict(m.stats())


def test_slice_lookup_window_counts_one_key_per_width_and_never_recomputes(tmp_path):
    lut, _, _ = write_r4_bins_lut(tmp_path, widths=(1e-6, 2e-6))
    keys = widths(lut, "nmos")
    assert keys == (100, 200)                                        # 전제: 슬라이스 2개
    m = LutMemo.counting(lut, 0, table_cache=TableCache(None))
    m.open_count()
    asked = []

    def w_of(key):
        asked.append(key)
        return 1e-6 * L / op_point(m, "nmos", key, L, 0.3, 0.6, 0.2).IDu

    first = finger_slice(lut, "nmos", L, w_of)
    assert sorted(asked) == list(keys) and len(asked) >= 1           # 호출 >= 1, 키마다 한 번
    m.fix_bound()
    st = stats(m)["point"]
    assert isinstance(st, LruStats)
    assert st.capacity == (0 + 1) * len(keys) == 2                   # U = widths 수
    assert st.misses == 2
    again = finger_slice(lut, "nmos", L, w_of)
    st2 = stats(m)["point"]
    assert len(asked) == 2 * len(keys)                               # 두 번째 호출도 키마다 w_of 를 부른다 (저장은 memo 만)
    assert st2.misses == st.misses                                   # 같은 키 재계산 0
    assert st2.hits == st.hits + len(keys)
    assert again == first


@pytest.mark.parametrize("n", [0, 2])
def test_slice_lookup_capacity_scales_with_n_theta_times_widths(tmp_path, n):
    lut, _, _ = write_r4_bins_lut(tmp_path, widths=(1e-6, 2e-6))
    m = LutMemo.counting(lut, n, table_cache=TableCache(None))
    m.open_count()
    finger_slice(lut, "nmos", L, lambda key: 1e-6 * L / op_point(m, "nmos", key, L, 0.3, 0.6, 0.2).IDu)
    m.fix_bound()
    assert stats(m)["point"].capacity == (n + 1) * 2
