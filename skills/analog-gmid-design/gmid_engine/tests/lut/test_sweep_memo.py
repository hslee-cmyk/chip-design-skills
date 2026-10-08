"""`sweep_memo` -- CONTRACT 2.2 [r7], 설계 40 §7.3 'LUT memo 상한: LutMemo.from_sweep(상한 = (n_θ + 1)·U_eval), U_eval 은 첫 평가에서 센
서로 다른 키 수'(D-PF1).

oracle (a) 구성: first_eval 이 영역마다 부르는 서로 다른 키 수를 이 파일이 정한다(같은 키 반복은 한 번) -> 상한 = (n_θ + 1)·그 수.
"""
import pytest

from gmid_engine.lut import LutMemo, TableCache, gm_id_curve, op_point, sweep_memo, vgs_for_gm_id


def _first_eval(calls):
    def run(memo):
        calls.append(memo)
        for vgs in (0.25, 0.3, 0.25, 0.35):                         # point 3 키(0.25 반복)
            op_point(memo, "nmos", 100, 1e-6, vgs, 0.5, 0.0)
        for vds in (0.5, 0.6, 0.5):                                  # curve 2 키
            gm_id_curve(memo, "nmos", 100, 1e-6, vds, 0.0)
        vgs_for_gm_id(memo, "nmos", 100, 15.0, 1e-6, 0.5, 0.0)       # root 1 키(곡선 0.5 는 이미 셈)
    return run


@pytest.mark.parametrize("n_theta", [0, 4, 31])
def test_capacity_is_n_plus_one_times_unique_keys(toy, n_theta):
    calls = []
    m = sweep_memo(toy, n_theta, _first_eval(calls), table_cache=TableCache(None))
    assert isinstance(m, LutMemo)
    st = dict(m.stats())
    assert st["point"].capacity == (n_theta + 1) * 3
    assert st["curve"].capacity == (n_theta + 1) * 2
    assert st["root"].capacity == (n_theta + 1) * 1
    assert len(calls) == 1                                           # 첫 평가는 한 번만 돈다


def test_returned_memo_is_fresh(toy):
    """계수용 memo 의 값은 넘기지 않는다(2.2) -- 반환 memo 의 통계는 비어 있다."""
    m = sweep_memo(toy, 2, _first_eval([]), table_cache=TableCache(None))
    for name, s in m.stats():
        if name in ("point", "curve", "root"):
            assert s.size == 0 and s.hits == 0 and s.misses == 0


def test_counting_memo_is_not_the_returned_one(toy):
    calls = []
    m = sweep_memo(toy, 1, _first_eval(calls), table_cache=TableCache(None))
    assert calls[0] is not m


def test_region_untouched_by_first_eval(toy):
    """[보고 -- 계약 공백] 첫 평가가 어떤 영역(여기서는 root)을 한 번도 부르지 않으면 U_eval = 0 이라 상한 0 이 되고, LutMemo 의 상한 규칙
    (1 이상, CONTRACT 2)과 부딪힌다. 설계 40 §7.3 은 이 경우를 정하지 않았다. 현재 동작(ValueError)을 고정해 두고 결정을 요청한다 --
    평가 커널이 분기에 따라 root 를 안 쓰는 첫 평가는 실제로 생길 수 있다."""
    def only_point(memo):
        op_point(memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)
    with pytest.raises(ValueError):
        sweep_memo(toy, 4, only_point, table_cache=TableCache(None))
