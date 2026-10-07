"""`LutMemo` -- CONTRACT 2절: 영역별 상한 LRU, 같은 조회 반복 시 계산 1회(대원칙), from_sweep 상한 식, 키 = (fp, fn_name) + key,
가변 키 TypeError, 모르는 영역 KeyError, 실패 조회 미저장, 영역 배정.
"""
import pytest

from gmid_engine.core import LruStats, SealViolationError
from gmid_engine.lut import (DERIVED_TABLES, REGIONS, LutMemo, caps, curve_report, gm_id_curve, gm_id_for_target, gmb,
                             op_point, tol_v_table, vgs_for_gm_id)

from .conftest import new_memo, standard_toy_slices


def _stats(m):
    st = m.stats()
    assert tuple(k for k, _ in st) == ("curve", "derived", "point", "root")
    assert all(isinstance(v, LruStats) for _, v in st)
    return dict(st)


def test_constants():
    assert REGIONS == ("curve", "derived", "point", "root")
    assert DERIVED_TABLES == ("curve_report", "tol_v_table")


def test_capacities(toy):
    m = LutMemo(toy, point=3, curve=5, root=7)
    st = _stats(m)
    assert (st["point"].capacity, st["curve"].capacity, st["root"].capacity) == (3, 5, 7)
    assert st["derived"].capacity == len(toy.slice_map) * len(DERIVED_TABLES) == 4


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, None, "3"])
def test_bad_capacity_valueerror(toy, bad):
    with pytest.raises(ValueError):
        LutMemo(toy, point=bad, curve=1, root=1)


def test_from_sweep_capacity(toy):
    m = LutMemo.from_sweep(toy, 3, {"point": 5, "curve": 2, "root": 7})
    st = _stats(m)
    assert (st["point"].capacity, st["curve"].capacity, st["root"].capacity) == (20, 8, 28)
    m2 = LutMemo.from_sweep(toy, 0, (("point", 1), ("curve", 4), ("root", 2)))
    st2 = _stats(m2)
    assert (st2["point"].capacity, st2["curve"].capacity, st2["root"].capacity) == (1, 4, 2)
    assert st2["derived"].capacity == 4


def test_lookup_computes_once_principle(toy_memo):
    calls = []

    def compute():
        calls.append(1)
        return ["value"]
    first = toy_memo.lookup("point", "probe", (1.0, "a"), compute)
    for _ in range(50):
        assert toy_memo.lookup("point", "probe", (1.0, "a"), compute) is first
    assert len(calls) == 1
    st = _stats(toy_memo)["point"]
    assert st.misses == 1 and st.hits == 50
    # 다른 fn_name·다른 키는 별도 계산
    toy_memo.lookup("point", "probe2", (1.0, "a"), compute)
    toy_memo.lookup("point", "probe", (1.0, "b"), compute)
    assert len(calls) == 3


def test_lookup_errors(toy_memo):
    with pytest.raises(TypeError):
        toy_memo.lookup("point", "probe", ([1, 2],), lambda: 1)
    with pytest.raises(KeyError):
        toy_memo.lookup("nowhere", "probe", (1,), lambda: 1)


def test_failed_compute_not_stored(toy_memo):
    n = []

    def boom():
        n.append(1)
        raise RuntimeError("x")
    for _ in range(2):
        with pytest.raises(RuntimeError):
            toy_memo.lookup("root", "probe", (1,), boom)
    assert len(n) == 2


def test_failed_query_not_stored(toy_memo):
    for _ in range(2):
        with pytest.raises(SealViolationError):
            vgs_for_gm_id(toy_memo, "nmos", 100, 25.0, 1e-6, 0.5, 0.0)
    st = _stats(toy_memo)["root"]
    assert st.hits == 0 and st.misses == 2


@pytest.mark.parametrize("region,call", [
    ("point", lambda m: op_point(m, "nmos", 100, 2e-6, 0.3, 0.6, 0.2)),
    ("point", lambda m: gmb(m, "nmos", 100, 2e-6, 0.3, 0.6, 0.2)),
    ("point", lambda m: caps(m, "nmos", 2e-6, 0.3, 0.6, 0.2, 2e-6)),
    ("curve", lambda m: gm_id_curve(m, "nmos", 100, 2e-6, 0.6, 0.2)),
    ("root", lambda m: vgs_for_gm_id(m, "nmos", 100, 12.0, 2e-6, 0.6, 0.2)),
    ("root", lambda m: gm_id_for_target(m, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6)),
    ("derived", lambda m: tol_v_table(m, "nmos", 100)),
    ("derived", lambda m: curve_report(m)),
])
def test_query_regions_and_repeat_is_free(toy, region, call):
    m = new_memo(toy)
    a = call(m)
    before = _stats(m)
    for _ in range(5):
        assert call(m) is a
    after = _stats(m)
    assert after[region].hits == before[region].hits + 5
    for r in REGIONS:
        assert after[r].misses == before[r].misses, "반복 조회에서 %s 영역 재계산" % r
    assert before[region].misses >= 1


def test_distinct_fp_luts_do_not_share(toy_build):
    a = toy_build("a").load()
    sl = standard_toy_slices()
    sl[0][2]["ID"] = sl[0][2]["ID"] * 3.0
    sl[0][2]["GM"] = sl[0][2]["GM"] * 3.0
    sl[0][2]["GDS"] = sl[0][2]["GDS"] * 3.0
    b = toy_build("b", slices=sl).load()
    assert a.fp != b.fp
    ma, mb = new_memo(a), new_memo(b)
    pa = op_point(ma, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
    pb = op_point(mb, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
    assert pb.IDu == pytest.approx(3 * pa.IDu, rel=1e-12)
    assert _stats(mb)["point"].misses == 1 and _stats(mb)["point"].hits == 0
    # 같은 키를 직접 넣어도 lut 별로 따로 계산된다
    va = ma.lookup("point", "probe", (1,), lambda: "A")
    vb = mb.lookup("point", "probe", (1,), lambda: "B")
    assert (va, vb) == ("A", "B")


def test_same_content_other_folder_same_fp(toy_build, tmp_path):
    from .conftest import copy_tree, TOY_SPEC
    from gmid_engine.lut import load_lut_set
    b = toy_build("orig")
    lut1 = b.load()
    d = copy_tree(b.root, tmp_path / "moved")
    lut2 = load_lut_set(str(d / "manifest.json"), str(d / "cap_ref.npz"), TOY_SPEC)
    assert lut1.fp == lut2.fp
    m1, m2 = new_memo(lut1), new_memo(lut2)
    assert op_point(m1, "nmos", 100, 1e-6, 0.5, 0.5, 0.0) == op_point(m2, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
