"""CONTRACT 3.22 [r8] `ln_idu_floors(sctx, variables, cells, one_var_only=False, start=None) -> {변수 index: 하한}` + S-4f 적용(3.13·3.21 4).

- 칸 정점 하한(kind, w_key, 칸) = 칸 [lo, hi] 안 L 앵커 × VDS·VS 전 격자 곡선 중 gm/ID 정점 마디가 on_mask 인 곡선마다 정점 마디의
  lnID + ln L − ln w_m, 그 최댓값 -- 이 파일이 npz 배열에서 직접 계산한다(`peak_floor`). 피검 함수로 기대값을 만들지 않는다.
- 정점 위치가 곡선마다 다르고 L 앵커마다 IDu 가 다른 toy LUT(`_floor_arrays`)를 써서 '곡선 최댓값'·'칸마다 다름'이 실제로 갈리게 했다.
- 1변수 writer: diode 회로(M1 nmos (out, out, gnd) 가 out 을 vgs_gate 로 쓰고 out 은 M1 drain)는 {M1}, 회로 C(gate 쓰기만)는 {}.
- 실 LUT v2: bin 이 앵커 여럿을 묶는 칸에서 같은 독립 계산과 대조.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.search import (
    ACCEPTED_STATUSES,
    AXIS_POWER,
    Variable,
    evaluate,
    layer0_start,
    ln_idu_floors,
    solve_eps,
)

from .conftest import R4_GRIDS, R4_L, SKILL_DIR, W_M, build_case, circuit_c, circuit_diode, peak_floor, r4_arrays

KIND = {"M1": "nmos", "M2": "pmos"}
DIODE_ONE_VAR = ("M1",)


# ---------------------------------------------------------------- 독립 계산

def _floor_arrays(kind):
    """r4 toy 배열에서 정점 VGS index 를 곡선마다 다르게: j*(i, k, s) = 1 + (3i + 2k + s) mod 9, GM/ID = 20 − 4·|j − j*|
    (0.5 로 아래를 잘라 on_mask 유지). L index 1 의 ID 는 e^0.7 배 -> IDu 가 L 앵커마다 다르다."""
    a = r4_arrays(kind)
    ID = a["ID"].copy()
    ID[1] *= math.exp(0.7)
    nL, nG, nD, nS = ID.shape
    g = np.empty_like(ID)
    for i in range(nL):
        for k in range(nD):
            for s in range(nS):
                js = 1 + (3 * i + 2 * k + s) % 9
                g[i, :, k, s] = np.maximum(20.0 - 4.0 * np.abs(np.arange(nG) - js), 0.5)
    a.update(ID=ID, GM=ID * g, GDS=ID * 0.1)
    return a


def _write_lut(root, arrays_of):
    """sizing conftest `write_r4_lut` 과 같은 파일 모양(npz·manifest·cap)에 임의 배열을 쓴다."""
    from gmid_engine.lut import load_lut_set
    from sizing.conftest import DEVICE_OF, SUFFIX, TOY_SPEC

    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for kind in ("nmos", "pmos"):
        p = root / ("fl_%s.npz" % kind)
        np.savez(p, **arrays_of(kind))
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in R4_GRIDS)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0)}
    for kind in ("nmos", "pmos"):
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    np.savez(root / "cap.npz", **cap)
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC)


@pytest.fixture(scope="module")
def floor_lut(tmp_path_factory):
    return _write_lut(tmp_path_factory.mktemp("floor_lut"), _floor_arrays)


def _expected(sctx, arrays_of, variables, cells, one_var=None, start=None):
    l_cells = dict(sctx.domain.l_cells)
    order = [m for m, _ in sctx.domain.l_cells]
    out = {}
    for idx, v in enumerate(variables):
        t, m = v.component
        if t != "ln_idu" or (one_var is not None and m not in one_var):
            continue
        lo_c, hi_c = l_cells[m][cells[order.index(m)]]
        f = peak_floor(arrays_of(KIND[m]), lo_c, hi_c)
        if start is not None and v.component in start:
            f = min(f, start[v.component])
        if v.lo < f < v.hi:
            out[idx] = f
    return out


def _close(got, exp):
    assert set(got) == set(exp), (got, exp)
    for k in exp:
        assert math.isclose(got[k], exp[k], rel_tol=1e-12, abs_tol=1e-12), (k, got[k], exp[k])


def _index(variables, comp):
    return [i for i, v in enumerate(variables) if v.component == comp][0]


# ---------------------------------------------------------------- 칸 정점 하한 값

@pytest.mark.parametrize("cells", [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_all_writer_floors_match_npz_peak(tmp_path, floor_lut, cells):
    case = build_case(tmp_path, circuit_c(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    got = ln_idu_floors(s, V, cells)
    exp = _expected(s, _floor_arrays, V, cells)
    assert len(exp) == 2                                      # 두 쓰기 소자 모두 상자 안 하한(비공허)
    _close(got, exp)
    assert dict(s.counters)["kernel_calls"] == 0              # LUT 배열만 읽는다


def test_floor_differs_by_cell_and_is_curve_maximum(tmp_path, floor_lut):
    """L 앵커마다 IDu 가 e^0.7 배 다른 LUT -> 칸 0·1 하한이 다르고, 하한 = 칸 곡선 정점 중 최댓값(최솟값이 아니다)."""
    case = build_case(tmp_path, circuit_c(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    i_m1 = _index(V, ("ln_idu", "M1"))
    f0 = ln_idu_floors(s, V, (0, 0))[i_m1]
    f1 = ln_idu_floors(s, V, (1, 0))[i_m1]
    assert abs(f1 - f0) > 0.1
    a = _floor_arrays("nmos")
    vals = []
    for k in range(a["ID"].shape[2]):
        for t in range(a["ID"].shape[3]):
            g = a["GM"][1, :, k, t] / a["ID"][1, :, k, t]
            j = int(np.argmax(g))
            vals.append(math.log(a["ID"][1, j, k, t]) + math.log(R4_L[1]) - math.log(W_M))
    assert math.isclose(f1, max(vals), rel_tol=1e-12) and min(vals) < f1 - 1.0


def test_floor_only_strictly_inside_variable_box(tmp_path, floor_lut):
    """원래 lo < 하한 < hi 일 때만 결과에 넣는다: 상자를 바꾼 Variable 로 경계(같음 포함)·밖을 확인."""
    case = build_case(tmp_path, circuit_c(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    i_m1 = _index(V, ("ln_idu", "M1"))
    f = ln_idu_floors(s, V, (0, 0))[i_m1]
    v = V[i_m1]

    def with_box(lo, hi):
        vs = list(V)
        vs[i_m1] = Variable(v.component, v.log, lo, hi)
        return tuple(vs)

    assert i_m1 not in ln_idu_floors(s, with_box(f, v.hi), (0, 0))           # lo == 하한
    assert i_m1 not in ln_idu_floors(s, with_box(f + 1.0, v.hi), (0, 0))     # lo > 하한
    assert i_m1 not in ln_idu_floors(s, with_box(v.lo, f), (0, 0))           # hi == 하한
    assert i_m1 not in ln_idu_floors(s, with_box(v.lo, f - 1.0), (0, 0))     # hi < 하한
    got = ln_idu_floors(s, with_box(f - 1e-9, f + 1e-9), (0, 0))
    assert math.isclose(got[i_m1], f, rel_tol=1e-15)


# ---------------------------------------------------------------- 1변수 writer·start 상한

def test_one_var_only_selects_diode_writer(tmp_path, floor_lut):
    case = build_case(tmp_path, circuit_diode(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    for cells in [(0, 0), (1, 1)]:
        allw = ln_idu_floors(s, V, cells)
        one = ln_idu_floors(s, V, cells, one_var_only=True)
        _close(allw, _expected(s, _floor_arrays, V, cells))
        _close(one, _expected(s, _floor_arrays, V, cells, one_var=DIODE_ONE_VAR))
        assert len(allw) == 2 and len(one) == 1


def test_one_var_only_empty_for_gate_writers(tmp_path, floor_lut):
    """회로 C: M1·M2 는 자기 gate(in·pb)를 쓴다 -- d·s·bulk 가 아니라 1변수 아님 -> {}(모든 쓰기 소자 판은 2개)."""
    case = build_case(tmp_path, circuit_c(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    assert ln_idu_floors(s, V, (0, 1), one_var_only=True) == {}
    assert len(ln_idu_floors(s, V, (0, 1))) == 2


def test_start_coordinate_caps_floor(tmp_path, floor_lut):
    """start 가 있으면 하한 = min(하한, start[성분]); 그 값이 원래 lo 이하이면 결과에서 빠진다."""
    case = build_case(tmp_path, circuit_diode(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    i1 = _index(V, ("ln_idu", "M1"))
    v = V[i1]
    f = ln_idu_floors(s, V, (1, 1), one_var_only=True)[i1]
    below = (v.lo + f) / 2
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start={v.component: below}) == {i1: below}
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start={v.component: f + 1.0}) == {i1: f}
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start={v.component: v.lo}) == {}
    th = {v.component: below, ("ln_idu", "M2"): -30.0, ("L", "M1"): R4_L[1]}       # θ Mapping 의 다른 성분은 무관
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start=th) == {i1: below}


# ---------------------------------------------------------------- 캐시 (sctx.cell_floors, (kind, w_key, 칸) 1회)

def _floor_keys(s, kind, m):
    """sctx.cell_floors 의 (kind, w_key 100, 칸) 키 -> 칸 (lo, hi). 칸은 index 또는 (lo, hi) 어느 표기든 받는다."""
    l_cells = dict(s.domain.l_cells)[m]
    out = {}
    for key in list(s.cell_floors):
        if isinstance(key, tuple) and len(key) == 3 and key[0] == kind and key[1] == 100:
            cell = key[2]
            out[key] = tuple(l_cells[cell]) if isinstance(cell, int) else tuple(cell)
    return out


def test_cell_floor_cache_is_read(tmp_path, floor_lut):
    case = build_case(tmp_path, circuit_diode(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    r1 = ln_idu_floors(s, V, (0, 1))
    n = len(s.cell_floors)
    assert ln_idu_floors(s, V, (0, 1)) == r1 and len(s.cell_floors) == n          # 같은 칸 -> 새 항목 없음
    nk, pk = _floor_keys(s, "nmos", "M1"), _floor_keys(s, "pmos", "M2")
    assert set(nk.values()) == {tuple(dict(s.domain.l_cells)["M1"][0])}
    assert set(pk.values()) == {tuple(dict(s.domain.l_cells)["M2"][1])}
    for key, cell in list(nk.items()) + list(pk.items()):
        assert math.isclose(s.cell_floors[key], peak_floor(_floor_arrays(key[0]), *cell), rel_tol=1e-12)
    # 캐시 값을 읽는다(다시 계산하지 않는다): 항목을 바꾸면 결과가 따라온다
    i1 = _index(V, ("ln_idu", "M1"))
    for key in nk:
        s.cell_floors[key] = V[i1].lo + 0.5
    assert ln_idu_floors(s, V, (0, 1))[i1] == V[i1].lo + 0.5


# ---------------------------------------------------------------- 실 LUT v2 (칸 = 앵커 여럿)

def test_real_lut_v2_multi_anchor_cells(tmp_path, real_lut_v2):
    from gmid_engine.core import BoundedLRU, read_pdk_decl

    lut, files = real_lut_v2
    memo = BoundedLRU(8)
    pdk = read_pdk_decl(str(SKILL_DIR / "assets" / "sky130_pdk_decl.json"), memo)
    rule = read_pdk_decl(str(SKILL_DIR / "assets" / "sky130_lut_rule_decl.json"), memo)
    case = build_case(tmp_path, circuit_diode(), lut, pdk=pdk, rule=rule)
    s = case.sctx
    V = s.domain.variables
    wk = dict(case.acc.w_keys)
    arrs = {}
    for kind in ("nmos", "pmos"):
        with np.load(files[(kind, wk[kind])]) as z:
            arrs[kind] = {k: np.asarray(z[k]) for k in ("L", "ID", "GM", "W")}
    l_cells = dict(s.domain.l_cells)
    assert any(lo < hi for lo, hi in l_cells["M1"])          # 앵커 여럿을 묶는 칸이 있다
    n1, n2 = len(l_cells["M1"]), len(l_cells["M2"])
    checked = 0
    for c1 in range(n1):
        cells = (c1, c1 % n2)
        got = ln_idu_floors(s, V, cells)
        exp = {}
        for idx, v in enumerate(V):
            if v.component[0] != "ln_idu":
                continue
            m = v.component[1]
            lo_c, hi_c = l_cells[m][cells[0] if m == "M1" else cells[1]]
            f = peak_floor(arrs[KIND[m]], lo_c, hi_c)
            if v.lo < f < v.hi:
                exp[idx] = f
        _close(got, exp)
        checked += len(exp)
    assert checked >= n1                                       # 칸마다 적어도 하나는 상자 안 하한


# ---------------------------------------------------------------- S-4f 적용: solve_eps·층 0 최대-최소

def _lines(root, ctx_fp):
    p = Path(root) / ctx_fp / "evals.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def _th(line):
    return {tuple(k): v for k, v in line["theta"]}


def _m1_cell(s, cells):
    order = [m for m, _ in s.domain.l_cells]
    return dict(s.domain.l_cells)["M1"][cells[order.index("M1")]]


DIODE_START = {("L", "M1"): 2e-6, ("L", "M2"): 2e-6, ("current", "M2"): 1.6e-8, ("ln_idu", "M1"): -7.0,
               ("ln_idu", "M2"): -15.0}


@pytest.mark.parametrize("axis", [AXIS_POWER, "area_search_m2"])
def test_solve_eps_respects_one_var_floor(tmp_path, floor_lut, short_root, axis):
    """solve_eps 는 1변수 writer(M1)의 ln_idu 를 min(칸 정점 하한, 시작 좌표) 아래에서 평가하지 않는다(S-4f, 3.13).
    floor LUT 에서 하한(≈ −7.04)은 봉인된 시작 좌표 −7.0 바로 아래 -- 전력·면적 최소화가 내려가려는 방향이다(그 아래는 diode 노드
    근 없음: 같은 LUT 에서 −10 은 no_root_in_window)."""
    from gmid_engine.search import start_points

    case = build_case(tmp_path, circuit_diode(), floor_lut, eval_budget=150, archive_root=short_root)
    s = case.sctx
    (sp,), _ = start_points(s, [DIODE_START])
    assert tuple(sp.cells) == (1, 1)
    floor = min(peak_floor(_floor_arrays("nmos"), *_m1_cell(s, sp.cells)), DIODE_START[("ln_idu", "M1")])
    assert DIODE_START[("ln_idu", "M1")] - floor < 0.1                       # 하한이 시작점 바로 아래(비공허)
    n0 = len(_lines(short_root, s.context_fp))
    solve_eps(s, sp, axis, None, (("t", "floor"),))
    new = _lines(short_root, s.context_fp)[n0:]
    assert new                                                                # 풀이가 새 점을 평가했다
    for ln in new:
        assert _th(ln)[("ln_idu", "M1")] >= floor - 1e-12 * abs(floor), ln["origin"]
    v2 = s.domain.variables[_index(s.domain.variables, ("ln_idu", "M2"))]
    assert all(_th(ln)[("ln_idu", "M2")] >= v2.lo for ln in new)
    assert dict(s.counters)["recompute_same_key"] == 0


def test_layer0_maxmin_respects_one_var_floor(tmp_path, lut_sealed, short_root):
    """층 0 최대-최소(3.21 4)도 1변수 writer 하한(출발 좌표는 넘지 않음)을 받는다 -- 시험 점 밖 층 0 평가 전부."""
    case = build_case(tmp_path, circuit_diode(), lut_sealed, eval_budget=150, archive_root=short_root)
    s = case.sctx
    r = layer0_start(s)
    lines = _lines(short_root, s.context_fp)
    assert lines and r.start is not None
    assert lines[0]["origin"] == {"stage": "layer0"}
    x0 = _th(lines[0])[("ln_idu", "M1")] if r.origin_point == "centre" else dict(r.start.theta)[("ln_idu", "M1")]
    floor = min(peak_floor(r4_arrays("nmos"), *_m1_cell(s, r.start.cells)), x0)
    after = [ln for ln in lines[1:] if "probe" not in ln["origin"]]
    assert after
    for ln in after:
        assert _th(ln)[("ln_idu", "M1")] >= floor - 1e-12 * abs(floor), ln["origin"]
    assert evaluate(s, r.start.theta, r.start.cells).status in ACCEPTED_STATUSES
