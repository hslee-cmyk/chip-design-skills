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
    """첫 평가가 어떤 영역(여기서는 root)을 한 번도 부르지 않으면 U_eval = 0 -> 상한 (n_θ + 1)·0 = 0.

    근거: 설계 40 §7.3 의 식 '상한 = (n_θ + 1)·U_eval' 을 U_eval = 0 에 그대로 적용한 값이 0 이고, EP-2('graph 밖 캐시는 LUT memo
    하나이고 상한이 있다')는 상한 0(= 저장 없음)으로도 지켜진다. 상한 0 영역의 동작은 CONTRACT 2·2.2 [2026-10-09 결정]: 오류가 아니라
    memo 하지 않음(매번 compute, stats capacity 0·size 0·hits 0·misses = 조회 수), 직접 생성자 `LutMemo(..., 0)` 은 여전히 ValueError.
    (옛 판정 -- ValueError 고정 -- 은 계약 공백 보고였고 이 결정으로 닫혔다.)
    oracle: 상한·통계 = (a) 구성(첫 평가가 root 를 0 번 부르도록 이 test 가 정함, 조회 횟수도 이 test 가 정함);
    값 = (c) 같은 LUT·같은 인자의 일반 memo(상한 ≥ 1) 조회 값과 같음(memo 는 값을 바꾸지 않는다, CONTRACT 2 lookup)."""
    def only_point(memo):
        op_point(memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)
    m = sweep_memo(toy, 4, only_point, table_cache=TableCache(None))
    st = dict(m.stats())
    assert st["point"].capacity == (4 + 1) * 1
    assert st["curve"].capacity == 0
    assert st["root"].capacity == 0
    ref = vgs_for_gm_id(LutMemo(toy, point=8, curve=8, root=8, table_cache=TableCache(None)),
                        "nmos", 100, 15.0, 1e-6, 0.5, 0.0)
    got = [vgs_for_gm_id(m, "nmos", 100, 15.0, 1e-6, 0.5, 0.0) for _ in range(3)]   # 같은 키 3번
    assert all(g == ref for g in got)
    st = dict(m.stats())
    assert st["root"].size == 0 and st["root"].hits == 0 and st["root"].misses == 3   # 저장 없이 매번 계산
    assert st["curve"].size == 0 and st["curve"].hits == 0


@pytest.mark.parametrize("region", ["point", "curve", "root"])
def test_direct_constructor_zero_capacity_still_rejected(toy, region):
    """CONTRACT 2: 직접 생성자의 상한 0 은 ValueError(상한 0 허용은 from_sweep/sweep_memo 경로만). oracle (d) 계약 선언."""
    caps = {"point": 1, "curve": 1, "root": 1}
    caps[region] = 0
    with pytest.raises(ValueError):
        LutMemo(toy, table_cache=TableCache(None), **caps)
