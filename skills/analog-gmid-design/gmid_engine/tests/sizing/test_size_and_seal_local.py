"""`size_and_seal_local(ctx, theta_block, fixed, columns) -> LocalSeal` (U4, 설계 41 §5.3 '국소 봉인 인터페이스', 40 §3.7,
확인 행 D-LS, CONTRACT 14.5) + `theta_name`.

설계 문구(41 §5.3): 계산 블록 ②~⑤를 columns 에 속한 소자·노드에만 적용, 그 밖의 값은 fixed 에서 읽는다, 봉인 1·2·6·7과 덮는 기둥의
KVL·KCL만 검사, 반환 LocalSeal{ok, failures[FailureRecord], snapshot_fragment, gain_db, power_w, area_m2}.

oracle:
- (a) 손계산 -- circuit_mirror(r4 toy) 의 닫힌 식: V(out) = y·1.8, V(nb) = M1 diode 근(θ 구성상 0.6), W = ID·L/IDu, 봉인 7 판정은
  VDS 대 r4 VDSAT 열 + tol_VDsat(conftest r4_vdsat_at·r4_tol_vdsat). power = 레일에서 덮는 소자로 나가는 전류 × 레일 전압(KCL: 각
  기둥 전류 = 10 µA), area = Σ W·L.
- (a) 덮는 집합 = S1 `graph.columns`·`graph.branches` 의 segment 원소·넷(독립 구현 `covered`, 설계 41 §5.3 '블록 소자를 덮는 기둥 집합').
- 피검 함수로 기대값을 만들지 않는다.
"""
import math

import pytest

from gmid_engine.core import FailureRecord
from gmid_engine.graph import GRAPH_KEY
from gmid_engine.sizing import LocalSeal, SnapshotFragment, size_and_seal_local, theta_name

from .conftest import (R4_L, build_ctx_u4, circuit_mirror, mos, r4_ln_idu, r4_tol_vdsat, r4_vdsat_at, rel_close,
                       theta_mirror, topo, two)
from .conftest import kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)

ID = 1e-5


@pytest.fixture(scope="module")
def mir(tmp_path_factory, r4_access):
    """(S1Graph, KernelContext) -- circuit_mirror, I1 = 10 µA."""
    return build_ctx_u4(tmp_path_factory.mktemp("loc_mir"), circuit_mirror(), r4_access, element_values=(("I1", ID),))


def covered(s1, cols):
    """기둥 id 들이 덮는 (원소 집합, 레일 아닌 넷 집합) -- S1 필드로 독립 계산."""
    columns = {str(c.id): c for c in s1.value("graph", GRAPH_KEY, "columns")}
    branches = {b.id: b for b in s1.value("graph", GRAPH_KEY, "branches")}
    rails = {n for n, r in s1.column("node", "is_rail") if r}
    elems, nets = set(), set()
    for cid in cols:
        for bid in columns[cid].branch_order:
            for seg in branches[bid].segments:
                elems.update(seg.elements)
                nets.update(n for n in seg.nets if n not in rails)
    return elems, nets


def col_with(s1, element):
    for c in s1.value("graph", GRAPH_KEY, "columns"):
        if element in covered(s1, {str(c.id)})[0]:
            return str(c.id)
    raise AssertionError(element)


def as_block(theta, keys=None):
    """θ dict -> ({이름: 값} 블록, {이름: 값} 고정). keys = 블록에 넣을 (kind, key) 집합(None = 전부 블록)."""
    blk, fix = {}, {}
    for (k, n), v in theta.items():
        (blk if keys is None or (k, n) in keys else fix)[theta_name(k, n)] = v
    return blk, fix


def w_writer(th, m):
    """쓰기 소자 W = ID·L/IDu, IDu = exp(θ ln_idu) (CONTRACT 5.7, 계획 DEC-88 쓰기 소자 좌표)."""
    return ID * th[("L", m)] / math.exp(th[("ln_idu", m)])


# ---------------------------------------------------------------------------
# theta_name·값 형식
# ---------------------------------------------------------------------------

def test_theta_name():
    assert theta_name("L", "M1") == "L:M1"
    assert theta_name("y", "input_common_mode") == "y:input_common_mode"
    assert theta_name("current", "R1") == "current:R1"


def test_covered_sets_oracle(mir):
    """전제(피검 아님): 기둥 둘이 {I1, M1}·{M3, M2} 를 덮는다."""
    s1, _ = mir
    assert {frozenset(covered(s1, {str(c.id)})[0]) for c in s1.value("graph", GRAPH_KEY, "columns")} == {
        frozenset({"I1", "M1"}), frozenset({"M2", "M3"})}


# ---------------------------------------------------------------------------
# 통과 -- 값
# ---------------------------------------------------------------------------

def test_all_columns_pass_values(mir):
    s1, ctx = mir
    th = theta_mirror()
    cols = frozenset(str(c.id) for c in s1.value("graph", GRAPH_KEY, "columns"))
    res = size_and_seal_local(ctx, *as_block(th), cols)
    assert isinstance(res, LocalSeal) and isinstance(res.snapshot_fragment, SnapshotFragment)
    assert res.ok is True and res.failures == ()
    assert res.gain_db is None                                   # U7 block_local_gain 병합 전(CONTRACT 14.5 스텁)
    nodes = dict(res.snapshot_fragment.nodes)
    assert set(nodes) == covered(s1, cols)[1] == {"nb", "out"}          # gate 전용 넷 in 은 기둥 segment 넷이 아니다
    assert abs(nodes["out"] - 0.9) <= 1e-12 and abs(nodes["nb"] - 0.6) <= 1e-6
    devs = dict(res.snapshot_fragment.devices)
    assert [m for m, _ in res.snapshot_fragment.devices] == ["M1", "M2", "M3"]
    w2 = ID * 1e-6 / math.exp(r4_ln_idu("nmos", nodes["nb"], 0.9, 0.0))
    for m, w in (("M1", w_writer(th, "M1")), ("M3", w_writer(th, "M3")), ("M2", w2)):
        assert rel_close(devs[m].W, w, 1e-9), m
    assert rel_close(res.power_w, 1.8 * ID * 2, 1e-12)            # 두 기둥이 vdd 에서 10 µA 씩
    assert rel_close(res.area_m2, sum(devs[m].W * 1e-6 for m in devs), 1e-12)
    assert rel_close(res.area_m2, (w_writer(th, "M1") + w_writer(th, "M3") + w2) * 1e-6, 1e-9)


def test_one_column_values(mir):
    """{I1, M1} 기둥만: 덮는 MOS = M1, 덮는 넷 = nb, power = 1.8·ID(I1 이 vdd 에서), area = W(M1)·L."""
    s1, ctx = mir
    th = theta_mirror()
    c = col_with(s1, "M1")
    res = size_and_seal_local(ctx, *as_block(th), frozenset({c}))
    assert res.ok and res.failures == ()
    assert [m for m, _ in res.snapshot_fragment.devices] == ["M1"]
    assert [n for n, _ in res.snapshot_fragment.nodes] == sorted(covered(s1, {c})[1]) == ["nb"]
    assert rel_close(res.power_w, 1.8 * ID, 1e-12)
    assert rel_close(res.area_m2, w_writer(th, "M1") * 1e-6, 1e-9)


# ---------------------------------------------------------------------------
# 위반 -- 덮는 범위만 판정
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("y,bad", [(0.1, "M2"), (0.9, "M3")])
def test_saturation_violation_is_local(mir, y, bad):
    """y = 0.1: VDS(M2) = 0.18 < VDsat(0.6) + tol_VDsat; y = 0.9: VSD(M3) = 0.18 < VDsat(0.7) + tol. 위반 소자가 든 기둥만 실패
    (봉인 7 한 건, 소자 = 그 소자), 다른 기둥({I1, M1})은 ok. 실패 점은 조각이 비고 power·area 는 None."""
    s1, ctx = mir
    kind, vgs = ("nmos", 0.6) if bad == "M2" else ("pmos", 0.7)
    vds = 1.8 * y if bad == "M2" else 1.8 - 1.8 * y
    assert vds < r4_vdsat_at(kind, R4_L[0], vgs, 0.0) + r4_tol_vdsat(kind)          # 전제(손계산)
    th = theta_mirror(y=y)
    blk, fix = as_block(th)
    res = size_and_seal_local(ctx, blk, fix, frozenset({col_with(s1, bad)}))
    assert res.ok is False and len(res.failures) == 1
    f = res.failures[0]
    assert isinstance(f, FailureRecord) and f.devices == (bad,) and dict(f.detail)["item"] == 7
    assert res.snapshot_fragment == SnapshotFragment() and res.power_w is None and res.area_m2 is None
    other = size_and_seal_local(ctx, blk, fix, frozenset({col_with(s1, "M1")}))
    assert other.ok is True and other.failures == ()


def test_whole_circuit_candidate_failure(tmp_path, r4_access):
    """②~⑤ 중 후보 실패(입력 창이 빈 회로 -> empty_window)는 어느 기둥을 골라도 ok = False, FailureRecord 1건(CONTRACT 14.5).
    회로: test_input_window 의 순환 follower(MA nmos (y, x, gnd), MB nmos (x, in, y)) -- VGS(MA) 0.5 / VGS(MB) 0.6 이면
    VDS(MA) + VDS(MB) = V(x) ≈ 0.5 < VDsat(MA) + VDsat(MB) + 2·tol (손계산 0.555) -> 모든 V(in) 에서 어느 한쪽이 포화 밖."""
    net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
    src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    doc = topo("loc_empty", net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)
    s1, ctx = build_ctx_u4(tmp_path, doc, r4_access)
    th = {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("ln_idu", "MA"): r4_ln_idu("nmos", 0.5, 0.3, 0.0),
          ("ln_idu", "MB"): r4_ln_idu("nmos", 0.6, 0.3, 0.0), ("y", "input_common_mode"): 0.5}
    from .conftest import free_currents
    th.update(free_currents(ctx, {"MA": ID, "MB": ID, "IX": ID, "IY": ID}))
    assert set(th) == set(kschema(ctx).components)
    for c in s1.value("graph", GRAPH_KEY, "columns"):
        res = size_and_seal_local(ctx, *as_block(th), frozenset({str(c.id)}))
        assert res.ok is False and len(res.failures) == 1
        assert dict(res.failures[0].detail)["reason"] == "empty_window"
        assert res.snapshot_fragment == SnapshotFragment() and res.power_w is None and res.area_m2 is None


# ---------------------------------------------------------------------------
# 인자 계약 -- ValueError
# ---------------------------------------------------------------------------

def test_partition_rejects(mir):
    s1, ctx = mir
    th = theta_mirror()
    cols = frozenset({col_with(s1, "M1")})
    blk, fix = as_block(th, {("L", "M1"), ("ln_idu", "M1")})
    size_and_seal_local(ctx, blk, fix, cols)                             # 정상 분할은 통과
    overlap = dict(fix, **{theta_name("L", "M1"): 1e-6})
    missing = {k: v for k, v in fix.items() if k != theta_name("y", "out")}
    unknown = dict(fix, **{theta_name("L", "ZZ"): 1e-6})
    for b, f in ((blk, overlap), (blk, missing), (blk, unknown), (dict(blk, **{"bogus": 1.0}), fix)):
        with pytest.raises(ValueError):
            size_and_seal_local(ctx, b, f, cols)


@pytest.mark.parametrize("cols", [frozenset(), frozenset({"99"}), frozenset({"0", "x"})], ids=["empty", "unknown", "mixed"])
def test_columns_rejects(mir, cols):
    _, ctx = mir
    with pytest.raises(ValueError):
        size_and_seal_local(ctx, *as_block(theta_mirror()), cols)


# ---------------------------------------------------------------------------
# 불변·결정론
# ---------------------------------------------------------------------------

def test_split_between_block_and_fixed_is_irrelevant(mir):
    """θ 를 블록·고정으로 어떻게 나눠도 같은 결과(합집합이 θ 전체이면 같은 입력)."""
    s1, ctx = mir
    th = theta_mirror(y=0.4)
    cols = frozenset({col_with(s1, "M2")})
    a = size_and_seal_local(ctx, *as_block(th), cols)
    b = size_and_seal_local(ctx, *as_block(th, {("L", "M2"), ("y", "out")}), cols)
    c = size_and_seal_local(ctx, *as_block(th, set()), cols)
    assert a == b == c


def test_repeat_identical(mir):
    s1, ctx = mir
    th = theta_mirror(y=0.45)
    cols = frozenset(str(c.id) for c in s1.value("graph", GRAPH_KEY, "columns"))
    assert size_and_seal_local(ctx, *as_block(th), cols) == size_and_seal_local(ctx, *as_block(th), cols)


def test_name_bijection(tmp_path, r4_access, mir):
    """이름 전단사(M1->Q9, M2->Q1, M3->Q5, I1->J2; nb->n7, out->o2, in->i4): 같은 θ(사상 적용)·같은 기둥(덮는 원소 사상)에서
    ok·power·area 같고, 조각의 소자·넷이 사상을 따른다(값 같음)."""
    s1, ctx = mir
    names, nets = ("Q9", "Q1", "Q5", "J2"), ("n7", "o2", "i4")
    smap = dict(zip(("M1", "M2", "M3", "I1"), names))
    nmap = dict(zip(("nb", "out", "in"), nets))
    s1b, ctxb = build_ctx_u4(tmp_path, circuit_mirror(names, nets), r4_access, element_values=(("J2", ID),))
    th = theta_mirror(y=0.4)
    thb = theta_mirror(names, "o2", y=0.4)
    for el in ("M1", "M2"):
        a = size_and_seal_local(ctx, *as_block(th), frozenset({col_with(s1, el)}))
        b = size_and_seal_local(ctxb, *as_block(thb), frozenset({col_with(s1b, smap[el])}))
        assert a.ok == b.ok and a.power_w == b.power_w and a.area_m2 == b.area_m2
        assert sorted((nmap[n], v) for n, v in a.snapshot_fragment.nodes) == list(b.snapshot_fragment.nodes)
        assert sorted((smap[m], op) for m, op in a.snapshot_fragment.devices) == list(b.snapshot_fragment.devices)
