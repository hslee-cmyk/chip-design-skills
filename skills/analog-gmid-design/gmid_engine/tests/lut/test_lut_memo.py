"""`LutMemo` -- CONTRACT 2절: 영역별 상한 LRU, 같은 조회 반복 시 계산 1회(대원칙), 계수 상태 memo(`LutMemo.counting` -> `open_count` ->
`fix_bound`, 상한 = (n_θ + 1)·U_r -- XRUN-F1 card A interface card xrunf1a C3), 키 = (fp, fn_name) + key, 가변 키 TypeError, 모르는 영역
KeyError, 실패 조회 미저장, 영역 배정.
"""
import pytest

from gmid_engine.core import LruStats, SealViolationError
from gmid_engine.lut import (DERIVED_TABLES, REGIONS, LutMemo, caps, curve_report, derived, gm_id_curve, gm_id_for_target, gmb,
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
    # [U17 ①-b 기준 변경, 설계 40 v1.9.1 §2.4.6 'memo로 옮기는 것' edge_costs(lut, kind, w_key) 행 + §2.4.8 (a) 행 D10, lut CONTRACT 머리
    #  'DERIVED_TABLES 에 edge_costs 추가'] edge_costs 는 슬라이스(kind, w_key)마다 하나인 LUT 파생 표 -> derived 영역 8개(이름순)
    # [card 20261104-hcs 계약 변경 -- interface §1 'DERIVED_TABLES에 vds_floor가 든다(기존 항목 뒤)'] 기존 8개 그대로 + 맨 뒤 vds_floor -> 9개
    assert DERIVED_TABLES == ("curve_report", "edge_costs", "midpoint_l_bin_checks", "noise_planes", "tol_mismatch_table",
                              "tol_noise_table", "tol_v_table", "tol_vdsat_table", "vds_floor")


def test_capacities(toy):
    m = LutMemo(toy, point=3, curve=5, root=7)
    st = _stats(m)
    assert (st["point"].capacity, st["curve"].capacity, st["root"].capacity) == (3, 5, 7)
    # [r6] derived 상한 = 슬라이스 수 × 4 (toy 슬라이스 2장 -> 8; r5 는 × 2 = 4) -- [r7] × 7 -> 14
    # [U17 ①-b, 40 v1.9.1 D10] 상한 식(슬라이스 수 × 표 종류)은 그대로, 표 종류 8(edge_costs) -> 2 × 8
    # [card 20261104-hcs] 표 종류 8 -> 9 (vds_floor)
    assert st["derived"].capacity == len(toy.slice_map) * len(DERIVED_TABLES) == 2 * 9


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, None, "3"])
def test_bad_capacity_valueerror(toy, bad):
    with pytest.raises(ValueError):
        LutMemo(toy, point=bad, curve=1, root=1)


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
        derived(m, "edge_costs", "nmos", wk)     # [U17 ①-b D10] edge_costs 도 derived 영역 슬라이스당 1개
    st = _stats(m)["derived"]
    # curve_report 는 LUT 전체 1개 + 폭 2 × 표 4(midpoint·tol_v·tol_vdsat·edge_costs) = 9; [U17 ①-b D10] 상한 2 × 8 = 16 -- 퇴출 0
    assert st.capacity == 18 and st.evictions == 0 and st.size == 9               # [card 20261104-hcs] 상한만 2 × 9 = 18 (표 종류 9)
    for wk in (100, 200):                                                         # vds_floor 도 슬라이스당 1개, 퇴출 0
        derived(m, "vds_floor", "nmos", wk)
    st = _stats(m)["derived"]
    assert st.capacity == 18 and st.evictions == 0 and st.size == 11


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


# ---------------------------------------------------------------------------
# [XRUN-F1 card A] 계수 상태 memo -- interface card xrunf1a C3(design 40 §2.4.6 '첫 평가 버림 제거', cfe2e31 J-4 보완).
# `LutMemo.counting(lut, n_theta, *, table_cache=None)` 는 "counting" 으로 시작 -> open_count() -> "window_open" -> fix_bound() -> "fixed".
# U_r = 창(open_count ~ fix_bound) 안에서 조회한 서로 다른 키 수(창 전에 모은 키를 창 안에서 다시 부르면 그 키도 듦, compute 예외 조회는 제외),
# 상한 = (n_theta + 1)·U_r, U_r = 0 이면 그 영역은 memo 하지 않음(capacity 0). 모은 항목은 마지막 접근 순서로 옮기고 넘치면 가장 오래 접근하지
# 않은 것부터 퇴출(evictions). 계수 상태 stats = capacity None·size = 모은 수·evictions 0, 고정 뒤 hits·misses 는 계수 상태 것에 이어진다.
# oracle: (손) 조회 순서·키는 이 test 가 정하고 U·상한·계수를 손으로 센다, (식) C3 상한 식, (비교) 생성자 memo 와 값 비트 동일.
# 조회는 공개 `lookup(region, fn_name, key, compute)` 로 직접 넣는다(compute 호출 수 = 이 test 의 계수). 엔진 소스는 열람하지 않았다.
# ---------------------------------------------------------------------------

import struct

from gmid_engine.lut import TableCache

SWEEP = ("point", "curve", "root")
NAN_OTHER = struct.unpack("<d", struct.pack("<Q", 0x7FF8000000000777))[0]     # 다른 비트의 NaN(같은 내용 키 -- C3)


class _Calls:
    """태그별 compute 호출 수. 반환값은 호출마다 새 tuple."""

    def __init__(self):
        self.n = {}

    def of(self, tag):
        def compute():
            self.n[tag] = self.n.get(tag, 0) + 1
            return ("v", tag, self.n[tag])
        return compute


def _counting(lut, n):
    return LutMemo.counting(lut, n, table_cache=TableCache(None))


def _q(m, calls, region, key):
    return m.lookup(region, "probe", key, calls.of((region,) + tuple(key)))


@pytest.mark.parametrize("n", [0, 1, 4])
def test_counting_memo_capacity_from_window_keys(toy, n):
    """A-T15: 창 전 point a, b(+ curve x) -> open_count -> point b, c, c, d -> fix_bound: U_point = |{b, c, d}| = 3 -> capacity (n + 1)·3.
    curve 는 창 안 조회 0(창 전 x 는 세지 않음) -> capacity 0, root 도 0."""
    m = _counting(toy, n)
    c = _Calls()
    _q(m, c, "point", ("a",))
    _q(m, c, "point", ("b",))
    _q(m, c, "curve", ("x",))
    m.open_count()
    for k in ("b", "c", "c", "d"):
        _q(m, c, "point", (k,))
    m.fix_bound()
    st = _stats(m)
    assert st["point"].capacity == (n + 1) * 3
    assert st["curve"].capacity == 0 and st["root"].capacity == 0


def test_counting_memo_fix_evicts_window_outsider(toy):
    """A-T16: n = 0 -> 상한 = U. 창 전 a 하나 + 창 안 k1, k2, k3(a 는 창 안에서 다시 부르지 않음): U = 3, 모은 항목 4 -> 고정 때 퇴출 1(a, 가장
    오래 접근하지 않음). 이어서 k3 조회 = hit 증분 1(계산 0), a 조회 = miss 증분 1(재계산 -- recomputes_after_eviction 1)."""
    m = _counting(toy, 0)
    c = _Calls()
    _q(m, c, "point", ("a",))
    m.open_count()
    for k in ("k1", "k2", "k3"):
        _q(m, c, "point", (k,))
    m.fix_bound()
    st = _stats(m)["point"]
    assert (st.capacity, st.size, st.evictions) == (3, 3, 1)
    before = _stats(m)["point"]
    _q(m, c, "point", ("k3",))
    after = _stats(m)["point"]
    assert (after.hits - before.hits, after.misses - before.misses) == (1, 0)
    assert c.n[("point", "k3")] == 1
    _q(m, c, "point", ("a",))
    after2 = _stats(m)["point"]
    assert (after2.hits - after.hits, after2.misses - after.misses) == (0, 1)
    assert c.n[("point", "a")] == 2
    assert after2.recomputes_after_eviction == 1


def test_counting_memo_window_hit_refreshes_recency(toy):
    """A-T16(최근성): n = 0. 창 전 b, a(넣은 순서 b 가 먼저) -> 창 안 b(창 전 키 다시 부름 -> U 에 듦, 최근성 갱신), k1: U = |{b, k1}| = 2,
    모은 항목 3 -> 퇴출 1 = 마지막 접근이 가장 오래된 a(넣은 순서로 퇴출했다면 b). 고정 뒤 b 조회 = hit(계산 0), a 조회 = 재계산."""
    m = _counting(toy, 0)
    c = _Calls()
    _q(m, c, "point", ("b",))
    _q(m, c, "point", ("a",))
    m.open_count()
    _q(m, c, "point", ("b",))
    _q(m, c, "point", ("k1",))
    m.fix_bound()
    st = _stats(m)["point"]
    assert (st.capacity, st.size, st.evictions) == (2, 2, 1)
    _q(m, c, "point", ("b",))
    assert c.n[("point", "b")] == 1                                   # b 는 남았다
    _q(m, c, "point", ("a",))
    assert c.n[("point", "a")] == 2                                   # a 가 퇴출됐었다


QUERIES = (
    ("op_point", lambda m: op_point(m, "nmos", 100, 1e-6, 0.3, 0.5, 0.0)),
    ("gm_id_curve", lambda m: gm_id_curve(m, "nmos", 100, 1e-6, 0.5, 0.0)),
    ("vgs_for_gm_id", lambda m: vgs_for_gm_id(m,"nmos", 100, 15.0, 1e-6, 0.5, 0.0)),
)
QUERIES_AFTER = (
    ("op_point_after_fix", lambda m: op_point(m, "nmos", 100, 1e-6, 0.35, 0.6, 0.0)),
    ("gm_id_curve_after_fix", lambda m: gm_id_curve(m, "nmos", 100, 1e-6, 0.6, 0.0)),
)
# 두 목록의 이름은 모두 서로 달라야 한다(비교 dict 키 -- 겹치면 다른 인자 값으로 덮인다). 아래 test 가 먼저 단언한다.


def test_counting_memo_values_equal_constructor_memo(toy):
    """A-T17: 같은 인자의 조회 값이 counting memo(창 전·창 안·고정 뒤)와 생성자 memo 에서 비트 같다(memo 는 값을 바꾸지 않는다). 고정 뒤 처음
    부르는 인자(QUERIES_AFTER)도 같다. derived 영역 capacity = 슬라이스 수 × len(DERIVED_TABLES)(계수 상태부터, 고정 뒤도)."""
    from .test_table_cache import assert_bit_identical
    names = [name for name, _ in QUERIES + QUERIES_AFTER]
    assert len(names) == len(set(names)) == 5                           # 전제: 모든 질의가 따로 비교된다(키 덮어쓰기 없음)
    ref_memo = LutMemo(toy, point=64, curve=64, root=64, table_cache=TableCache(None))
    ref = {name: q(ref_memo) for name, q in QUERIES + QUERIES_AFTER}
    m = _counting(toy, 2)
    derived_cap = len(toy.slice_map) * len(DERIVED_TABLES)
    assert _stats(m)["derived"].capacity == derived_cap
    pre = {name: q(m) for name, q in QUERIES}
    m.open_count()
    win = {name: q(m) for name, q in QUERIES}
    m.fix_bound()
    post = {name: q(m) for name, q in QUERIES + QUERIES_AFTER}
    for got in (pre, win):
        for name, _ in QUERIES:
            assert_bit_identical(got[name], ref[name], name)
    for name, _ in QUERIES + QUERIES_AFTER:
        assert_bit_identical(post[name], ref[name], name)
    assert _stats(m)["derived"].capacity == derived_cap


def test_counting_memo_state_transitions_and_errors(toy):
    """A-T19: bound_state "counting" -> open_count -> "window_open" -> fix_bound -> "fixed". ValueError: 창 없이 fix_bound, 두 번째 open_count,
    고정 뒤 open_count·fix_bound. 오류 호출은 상태를 바꾸지 않는다(다음 정상 호출이 그대로 된다)."""
    m = _counting(toy, 1)
    assert m.bound_state == "counting"
    with pytest.raises(ValueError):
        m.fix_bound()                                                  # 창 없이
    assert m.bound_state == "counting"
    m.open_count()
    assert m.bound_state == "window_open"
    with pytest.raises(ValueError):
        m.open_count()                                                 # 두 번째
    assert m.bound_state == "window_open"
    m.fix_bound()
    assert m.bound_state == "fixed"
    for meth in (m.open_count, m.fix_bound):
        with pytest.raises(ValueError):
            meth()
    assert m.bound_state == "fixed"


def test_counting_memo_constructor_memo_is_fixed(toy):
    """A-T19: 생성자 LutMemo(...) memo 는 처음부터 "fixed" -- open_count·fix_bound 모두 ValueError."""
    m = LutMemo(toy, point=4, curve=4, root=4, table_cache=TableCache(None))
    assert m.bound_state == "fixed"
    with pytest.raises(ValueError):
        m.open_count()
    with pytest.raises(ValueError):
        m.fix_bound()


def test_counting_memo_stats_counting_then_fixed(toy):
    """A-T20: 계수 상태 stats(point·curve·root) = capacity None·size = 모은 서로 다른 키 수·evictions 0·recomputes 0, hits·misses 손계산.
    고정 뒤 hits·misses 는 계수 상태 합에 이어지고(옮기기는 바꾸지 않음), 고정 직후 같은 원 key 조회 = hit 증분 1·misses 증분 0·계산 0.
    손 순서(point): 창 전 (1.0,) miss | 창 안 (0.0,) miss, (2.0,) miss, (1.0,) hit, (2.0,) hit -> hits 2, misses 3, size 3, U = 3."""
    m = _counting(toy, 2)
    c = _Calls()
    _q(m, c, "point", (1.0,))
    st0 = _stats(m)
    for r in SWEEP:
        assert st0[r].capacity is None and st0[r].evictions == 0 and st0[r].recomputes_after_eviction == 0
    assert (st0["point"].size, st0["point"].hits, st0["point"].misses) == (1, 0, 1)
    assert (st0["curve"].size, st0["root"].size) == (0, 0)
    m.open_count()
    for k in ((0.0,), (2.0,), (1.0,), (2.0,)):
        _q(m, c, "point", k)
    st1 = _stats(m)["point"]
    assert (st1.capacity, st1.size, st1.hits, st1.misses, st1.evictions) == (None, 3, 2, 3, 0)
    m.fix_bound()
    st2 = _stats(m)["point"]
    assert (st2.capacity, st2.size, st2.hits, st2.misses, st2.evictions) == ((2 + 1) * 3, 3, 2, 3, 0)
    _q(m, c, "point", (0.0,))
    st3 = _stats(m)["point"]
    assert (st3.hits, st3.misses) == (3, 3)
    assert c.n[("point", 0.0)] == 1                                   # 계산 0(고정 직후 같은 원 key = 적중)


def test_counting_memo_zero_and_negzero_are_two_window_keys(toy):
    """A-T20 키 동치: 창 안 (0.0,)·(−0.0,) 는 다른 키 -> U = 2 -> capacity (2 + 1)·2 = 6, 계산도 각각 1회."""
    assert (0.0,) == (-0.0,)                                           # 전제: 파이썬 == 로는 같다
    m = _counting(toy, 2)
    c = _Calls()
    m.open_count()
    _q(m, c, "point", (0.0,))
    _q(m, c, "point", (-0.0,))
    m.fix_bound()
    assert _stats(m)["point"].capacity == 6
    assert sum(c.n.values()) == 2


def test_counting_memo_same_nan_is_one_window_key(toy):
    """A-T20 키 동치: 같은 내용 NaN 키 두 번(비트가 다른 NaN) -> U = 1 -> capacity (2 + 1)·1 = 3, 두 번째는 적중(계산 1회)."""
    m = _counting(toy, 2)
    c = _Calls()
    m.open_count()
    m.lookup("point", "probe", (float("nan"),), c.of("nan"))
    m.lookup("point", "probe", (NAN_OTHER,), c.of("nan"))
    m.fix_bound()
    assert _stats(m)["point"].capacity == 3
    assert c.n == {"nan": 1}


def test_counting_memo_failed_compute_not_in_window_count(toy):
    """A-T20: 창 안 compute 예외 조회는 U 에 넣지 않는다(misses 에는 센다): 창 안 good(정상)·bad(예외) -> U = 1 -> capacity (2 + 1)·1 = 3."""
    m = _counting(toy, 2)
    c = _Calls()

    def boom():
        raise RuntimeError("x")
    m.open_count()
    _q(m, c, "point", ("good",))
    with pytest.raises(RuntimeError):
        m.lookup("point", "probe", ("bad",), boom)
    st = _stats(m)["point"]
    assert (st.size, st.misses) == (1, 2)
    m.fix_bound()
    assert _stats(m)["point"].capacity == 3
