"""`LutMemo` -- CONTRACT 2절: 영역별 상한 LRU, 같은 조회 반복 시 계산 1회(대원칙), from_sweep 상한 식, 키 = (fp, fn_name) + key,
가변 키 TypeError, 모르는 영역 KeyError, 실패 조회 미저장, 영역 배정.
"""
import pytest

from gmid_engine.core import LruStats, SealViolationError
from gmid_engine.lut import (DERIVED_TABLES, REGIONS, LutMemo, caps, curve_report, gm_id_curve, gm_id_for_target, gmb,
                             midpoint_l_bin_checks, op_point, tol_v_table, tol_vdsat_table, vdsat, vgs_for_gm_id)

from .conftest import new_memo, standard_toy_slices


def _stats(m):
    st = m.stats()
    assert tuple(k for k, _ in st) == ("curve", "derived", "point", "root")
    assert all(isinstance(v, LruStats) for _, v in st)
    return dict(st)


def test_constants():
    assert REGIONS == ("curve", "derived", "point", "root")
    # [r6] 2절: derived 표 4개(r5 는 curve_report·tol_v_table 2개)
    # [r7] 2절: + noise_planes·tol_mismatch_table·tol_noise_table = 7개 -- 설계 41 §7.2 'tol_noise ... 디스크 캐시 대상',
    #      §6.4-2b 'tol_mismatch ... 디스크 캐시 대상'(파생 표라 derived 영역)
    assert DERIVED_TABLES == ("curve_report", "midpoint_l_bin_checks", "noise_planes", "tol_mismatch_table", "tol_noise_table",
                              "tol_v_table", "tol_vdsat_table")


def test_capacities(toy):
    m = LutMemo(toy, point=3, curve=5, root=7)
    st = _stats(m)
    assert (st["point"].capacity, st["curve"].capacity, st["root"].capacity) == (3, 5, 7)
    # [r6] derived 상한 = 슬라이스 수 × 4 (toy 슬라이스 2장 -> 8; r5 는 × 2 = 4) -- [r7] × 7 -> 14
    assert st["derived"].capacity == len(toy.slice_map) * len(DERIVED_TABLES) == 2 * 7


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
    assert st2["derived"].capacity == 2 * 7                  # [r7] 슬라이스 2 × DERIVED_TABLES 7 (from_sweep 도 같은 식)


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


@pytest.mark.parametrize("region,call", [
    ("point", lambda m: vdsat(m, "nmos", 100, 3.5e-6, 0.3, 0.6, 0.2)),
    ("derived", lambda m: midpoint_l_bin_checks(m, "nmos", 100)),
    ("derived", lambda m: tol_vdsat_table(m, "nmos", 100, ())),
])
def test_r6_query_regions_and_repeat_is_free(mid_toy_build, region, call):
    """[r6] 2절 영역: vdsat = point, midpoint_l_bin_checks·tol_vdsat_table = derived. 반복은 그 영역 hits 만 는다."""
    from .conftest import MID_L_SOURCE, mid_point_arrays
    m = new_memo(mid_toy_build("reg", mid=mid_point_arrays((3.5e-6,), l_source=MID_L_SOURCE)).load())
    a = call(m)
    before = _stats(m)
    for _ in range(3):
        assert call(m) is a
    after = _stats(m)
    assert after[region].hits == before[region].hits + 3
    for r in REGIONS:
        assert after[r].misses == before[r].misses, "반복 조회에서 %s 영역 재계산" % r
    assert before[region].misses >= 1


def test_r6_derived_capacity_holds_all_tables(mid_toy_build):
    """[r6] derived 상한 = 슬라이스 수 × 4: 두 폭의 네 표를 모두 만들어도 쫓겨나지 않는다(evictions 0)."""
    from .conftest import MID_L_SOURCE, mid_point_arrays
    lut = mid_toy_build("cap", mid=mid_point_arrays((3.5e-6,), l_source=MID_L_SOURCE)).load()
    m = new_memo(lut)
    for wk in (100, 200):
        curve_report(m)
        midpoint_l_bin_checks(m, "nmos", wk)
        tol_v_table(m, "nmos", wk)
        tol_vdsat_table(m, "nmos", wk)
    st = _stats(m)["derived"]
    assert st.capacity == 14 and st.evictions == 0 and st.size == 7     # curve_report 는 LUT 전체 1개; [r7] 상한 2 × 7


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


# ---------------------------------------------------------------------------
# [2026-10-08] 2.1 lookup_persistent + table_cache 인자 (디스크 캐시는 짧은 임시 폴더에서만 -- 실제 캐시 폴더 불변)
# ---------------------------------------------------------------------------

_ENV = "GMID_LUT_TABLE_CACHE_DIR"          # (d) 2.1 설정 table_cache.env


@pytest.fixture
def short_dir():
    """칸 파일 이름이 약 150자라 깊은 tmp_path 에선 MAX_PATH 를 넘는다 -- 시스템 임시 폴더 바로 아래 짧은 폴더."""
    import shutil
    import tempfile
    from pathlib import Path
    d = tempfile.mkdtemp(prefix="gtm")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def cache_cls(toy, monkeypatch, short_dir):
    """TableCache 클래스(공개 이름이 없으면 공개 객체 `LutMemo(...).table_cache` 의 형 -- default() 는 임시 폴더로)."""
    import gmid_engine.lut as lut_pkg
    cls = getattr(lut_pkg, "TableCache", None)
    if cls is None:
        monkeypatch.setenv(_ENV, str(short_dir / "_probe"))
        cls = type(LutMemo(toy, point=1, curve=1, root=1).table_cache)
    return cls


def _tbl(d):
    import os
    return sorted(n for n in os.listdir(d) if n.endswith(".tbl")) if d.exists() else []


def test_table_cache_argument_and_default(toy, cache_cls, short_dir, monkeypatch):
    """(d) 2.1: table_cache 를 넘기면 memo.table_cache 가 그 객체, 생략하면 default()(저장소 설정 + os.environ -> 환경 변수 폴더)."""
    import os
    off = cache_cls(None)
    assert LutMemo(toy, point=1, curve=1, root=1, table_cache=off).table_cache is off
    envd = short_dir / "envd"
    monkeypatch.setenv(_ENV, str(envd))
    t = LutMemo(toy, point=1, curve=1, root=1).table_cache
    assert isinstance(t, cache_cls)
    p = t.path_of(toy.fp, cache_cls.data_id(toy.provenance), "probe", (1,))
    assert os.path.normcase(os.path.dirname(p)) == os.path.normcase(str(envd))


def test_lookup_persistent_memory_then_disk(toy, cache_cls, short_dir):
    """(a) 2.1 불변식 (7): 같은 memo 두 번째 = 메모리 적중(`is`, 디스크 이벤트 불변, derived hits +1, compute 0);
    새 memo(같은 폴더) = 디스크 적중(compute 0, 같은 값); 파일 이름은 fn_name 으로 시작."""
    import numpy as np
    d = short_dir / "c"
    tc = cache_cls(str(d))
    m = LutMemo(toy, point=4, curve=4, root=4, table_cache=tc)
    calls = []

    def compute():
        calls.append(1)
        return ("table", 1.5, (2.0,))
    inputs = (np.arange(3.0),)
    v1 = m.lookup_persistent("derived", "probe_table", ("nmos", 100), compute, inputs, ("s",))
    ev = tc.events
    st = _stats(m)["derived"]
    v2 = m.lookup_persistent("derived", "probe_table", ("nmos", 100), compute, inputs, ("s",))
    assert v2 is v1 and len(calls) == 1
    assert tc.events == ev
    assert _stats(m)["derived"].hits == st.hits + 1
    assert [n.split("-")[0] for n in _tbl(d)] == ["probe_table"]
    tc2 = cache_cls(str(d))
    m2 = LutMemo(toy, point=4, curve=4, root=4, table_cache=tc2)
    assert m2.lookup_persistent("derived", "probe_table", ("nmos", 100), compute, inputs, ("s",)) == v1
    assert len(calls) == 1 and tc2.events == (("hit", "probe_table"),)


def test_lookup_persistent_errors_and_failed_compute_not_stored(toy, cache_cls, short_dir):
    """(d) 2절·2.1: lookup 과 같은 키 규칙(가변 키 TypeError, 모르는 영역 KeyError), 실패한 compute 는 저장되지 않는다(파일 0,
    다시 부르면 다시 compute)."""
    d = short_dir / "c"
    m = LutMemo(toy, point=4, curve=4, root=4, table_cache=cache_cls(str(d)))
    with pytest.raises(TypeError):
        m.lookup_persistent("derived", "probe", ([1, 2],), lambda: 1, ())
    with pytest.raises(KeyError):
        m.lookup_persistent("nowhere", "probe", (1,), lambda: 1, ())
    n = []

    def boom():
        n.append(1)
        raise RuntimeError("x")
    for _ in range(2):
        with pytest.raises(RuntimeError):
            m.lookup_persistent("derived", "probe", (1,), boom, ())
    assert len(n) == 2 and _tbl(d) == []


@pytest.mark.parametrize("fn,call", [
    ("tol_v_table", lambda m: tol_v_table(m, "nmos", 100)),
    ("tol_vdsat_table", lambda m: tol_vdsat_table(m, "nmos", 100)),
    ("curve_report", lambda m: curve_report(m)),
])
def test_derived_tables_go_through_disk_cache(mid_toy_build, cache_cls, short_dir, fn, call):
    """(d) 2.1 '쓰는 곳': tol_v_table·tol_vdsat_table·curve_report 는 lookup_persistent 로 디스크 캐시를 거친다 -- 첫 memo 는
    그 fn_name 의 칸 파일을 쓰고(miss·write), 새 memo 는 디스크 적중(hit), 값은 같다. midpoint_l_bin_checks 는 대상 아님(파일 없음)."""
    from .conftest import MID_L_SOURCE, mid_point_arrays
    lut = mid_toy_build("dc", mid=mid_point_arrays((3.5e-6,), l_source=MID_L_SOURCE)).load()
    d = short_dir / "c"
    t1 = cache_cls(str(d))
    a = call(LutMemo(lut, point=64, curve=64, root=64, table_cache=t1))
    assert (("miss", fn) in t1.events) and (("write", fn) in t1.events)
    assert {n.split("-")[0] for n in _tbl(d)} == {fn}
    t2 = cache_cls(str(d))
    b = call(LutMemo(lut, point=64, curve=64, root=64, table_cache=t2))
    assert t2.events == (("hit", fn),)
    from .test_table_cache import assert_bit_identical      # (b) 디스크 적중 값 = 처음 계산 값(비트 동일)
    assert_bit_identical(a, b, fn)
