"""CONTRACT 3.22 [r8] `ln_idu_floors(sctx, variables, cells, one_var_only=False, start=None) -> {변수 index: 하한}` + S-4f 적용(3.13·3.21 4).

- 칸 정점 하한(kind, w_key, 칸) = 칸 [lo, hi] 안 L 앵커 × VDS·VS 전 격자 곡선 중 gm/ID 정점 마디가 on_mask 인 곡선마다 정점 마디의
  lnID + ln L − ln w_m, 그 최댓값 -- 이 파일이 npz 배열에서 직접 계산한다(`peak_floor`). 피검 함수로 기대값을 만들지 않는다.
- 정점 위치가 곡선마다 다르고 L 앵커마다 IDu 가 다른 toy LUT(`_floor_arrays`)를 써서 '곡선 최댓값'·'칸마다 다름'이 실제로 갈리게 했다.
- 1변수 writer: diode 회로(M1 nmos (out, out, gnd) 가 out 을 vgs_gate 로 쓰고 out 은 M1 drain)는 {M1}, 회로 C(gate 쓰기만)는 {}.
- 실 LUT v2: bin 이 앵커 여럿을 묶는 칸에서 같은 독립 계산과 대조.
- [r9] 칸 전도 하한(봉인 9 조건 IDu(VGS)·(gm/ID)·tol_V ≥ IDu(VGS = 0) 의 ln_idu 근, 3.22 r9)도 이 파일/conftest 가 npz 배열 + lut
  `tol_v_table` 입력(lut 계약 소관 공개 API)으로 직접 계산한다(`conduction_floor`). 성분별 하한 = max(전도(모든 ln_idu 성분),
  정점(one_var_only 면 1변수 writer 만)), start 캡은 start 에 그 성분이 있을 때만(oracle (a): 계약 문장의 격자 계산 + 봉인 9 조건).
"""
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

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

from .conftest import l_ties_of  # [U17 ①-b] graph/kernel 필드 읽기
from .conftest import (R4_GRIDS, R4_L, SKILL_DIR, W_M, build_case, circuit_c, circuit_diode, conduction_floor, expected_floor,
                       peak_floor, r4_arrays, tol_v_at)
from .conftest import CODE_FP, SRC, load_spec, new_access, write_decls
from sizing.conftest import LClassStub, inject_l_classes, mos, topo

KIND = {"M1": "nmos", "M2": "pmos"}
DIODE_ONE_VAR = ("M1",)


# ---------------------------------------------------------------- 독립 계산

FLOOR_GM_ID_AT_ZERO = 2.0      # VGS = 0 마디 GM/ID (정점 20 까지 선형으로 오른다)


def _floor_arrays(kind):
    """정점 VGS 가 곡선마다 다른 toy: j*(i, s) = 1 + (3i + s) mod 9, VGS* = VGS[j*]. GM/ID = 2 → B(= 20, VGS*) 선형 상승,
    그 뒤 B − C·(VGS − VGS*) (C = 8: r4 toy 의 gm/ID 기울기, 격자 끝에서도 > 0 -> on_mask 유지). L index 1 의 ID 는 e^0.7 배 -> IDu 가
    L 앵커마다 다르다.
    [r7 2026-10-09 lut CONTRACT 1.4 기울기 열 단위 검사 복원] ln ID 를 이 GM/ID 의 적분으로 만든다(oracle (a) 구성): VGS = 0 마디는 r4 toy
    값 그대로, 칸마다 ln ID 차 = h·(g_j + g_(j+1))/2(GM/ID 가 VGS 에 조각 선형이라 정확한 적분, 현 = 두 끝 평균 -> 두 끝 사이, FC 단조).
    옛 판(GM/ID = 20 − 4·|j − j*|, j* 에 2k 항, ID 는 r4 의 VGS 2차식 그대로)은 기울기 자료가 ln ID 와 무관해 칸 과반이 1.4 위반(로드 거부).
    정점 위치는 VDS 와 무관하게 둔다 -- VDS 마다 다르면 ln ID 의 VDS 기울기가 곡선 모양 차이를 품어 GDS/ID = 0.1(= r4 의 VDS 기울기 LAM)
    과 모순이다. VGS = 0 의 GM/ID 를 낮게(2) 둔 것은 옛 판처럼 전도 하한 곡선(VGS 0 에서 GM·tol < ID)이 생기게 하려는 것."""
    from sizing.conftest import B, C

    a = r4_arrays(kind)
    ID0 = a["ID"].copy()
    ID0[1] *= math.exp(0.7)
    nL, nG, nD, nS = ID0.shape
    vgs = np.asarray(a["VGS"], dtype=float)
    g = np.empty_like(ID0)
    for i in range(nL):
        for s in range(nS):
            vp = vgs[1 + (3 * i + s) % 9]
            up = FLOOR_GM_ID_AT_ZERO + (B - FLOOR_GM_ID_AT_ZERO) * vgs / vp
            g[i, :, :, s] = np.where(vgs <= vp, up, B - C * (vgs - vp))[:, None]
    h = np.diff(vgs)[None, :, None, None]
    cum = np.concatenate([np.zeros_like(ID0[:, :1]), np.cumsum(h * 0.5 * (g[:, :-1] + g[:, 1:]), axis=1)], axis=1)
    ID = ID0[:, :1] * np.exp(cum)
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


def _tols(lut, case):
    """kind -> tol_at(L, VDS) (lut 공개 API 입력, conftest `tol_v_at`)."""
    wk = dict(case.acc.w_keys)
    return {k: tol_v_at(lut, k, wk[k]) for k in ("nmos", "pmos")}


def _cond(arrays_of, tols, kind, cell):
    return conduction_floor(arrays_of(kind), cell[0], cell[1], tols[kind])


def _expected(sctx, arrays_of, variables, cells, tols, one_var=None, start=None):
    """[r9] 3.22: 전도 하한은 모든 ln_idu 성분, 정점 하한은 one_var(None = 모든 쓰기 소자) 안의 성분만, 성분별 max, start 캡은
    start 에 그 성분이 있을 때만, 원래 lo < 하한 < hi 일 때만."""
    l_cells = dict(sctx.domain.l_cells)
    order = [m for m, _ in sctx.domain.l_cells]
    out = {}
    for idx, v in enumerate(variables):
        t, m = v.component
        if t != "ln_idu":
            continue
        cell = l_cells[m][cells[order.index(m)]]
        cond = _cond(arrays_of, tols, KIND[m], cell)
        peak = peak_floor(arrays_of(KIND[m]), *cell) if (one_var is None or m in one_var) else None
        f = expected_floor(cond, peak)
        if f is None:
            continue
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
    exp = _expected(s, _floor_arrays, V, cells, _tols(floor_lut, case))
    assert len(exp) == 2                                     # 두 쓰기 소자 모두 상자 안 하한(비공허)
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
    """[r9] one_var_only: 정점 하한은 1변수 writer(M1)만, 전도 하한은 모든 ln_idu 성분(M2 도) -- 3.22 r9."""
    case = build_case(tmp_path, circuit_diode(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    tols = _tols(floor_lut, case)
    i2 = _index(V, ("ln_idu", "M2"))
    for cells in [(0, 0), (1, 1)]:
        allw = ln_idu_floors(s, V, cells)
        one = ln_idu_floors(s, V, cells, one_var_only=True)
        _close(allw, _expected(s, _floor_arrays, V, cells, tols))
        exp_one = _expected(s, _floor_arrays, V, cells, tols, one_var=DIODE_ONE_VAR)
        _close(one, exp_one)
        assert len(allw) == 2
        # 비공허: M2 는 1변수 writer 가 아니지만 전도 하한이 상자 안이라 one_var_only 결과에도 있다(r8 이면 빠졌다)
        assert i2 in exp_one
        cell2 = dict(s.domain.l_cells)["M2"][cells[1]]
        assert math.isclose(one[i2], _cond(_floor_arrays, tols, "pmos", cell2), rel_tol=1e-12)


def test_one_var_only_empty_for_gate_writers(tmp_path, floor_lut):
    """회로 C: M1·M2 는 자기 gate(in·pb)를 쓴다 -- 1변수 아님 -> 정점 하한은 비고(이름의 empty), [r9] one_var_only 결과 = 전도 하한만.
    모든 쓰기 소자 판은 max(전도, 정점)."""
    case = build_case(tmp_path, circuit_c(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    tols = _tols(floor_lut, case)
    cells = (0, 1)
    one = ln_idu_floors(s, V, cells, one_var_only=True)
    exp_one = _expected(s, _floor_arrays, V, cells, tols, one_var=())
    _close(one, exp_one)
    assert len(exp_one) == 2                                  # 두 성분 모두 전도 하한이 상자 안
    allw = ln_idu_floors(s, V, cells)
    _close(allw, _expected(s, _floor_arrays, V, cells, tols))
    assert len(allw) == 2
    # 이 LUT·칸에서는 정점 하한이 전도 하한보다 커서 두 판이 실제로 갈린다(max 가 정점 쪽)
    lc = dict(s.domain.l_cells)
    for m, j in (("M1", 0), ("M2", 1)):
        cell = lc[m][cells[j]]
        assert peak_floor(_floor_arrays(KIND[m]), *cell) > _cond(_floor_arrays, tols, KIND[m], cell)


def test_start_coordinate_caps_floor(tmp_path, floor_lut):
    """start 가 있으면 하한 = min(하한, start[성분]); 그 값이 원래 lo 이하이면 결과에서 빠진다. [r9] start 에 없는 성분은 캡 없음
    (r8 은 KeyError) -- M2 는 start 에 없을 때 전도 하한 그대로 남는다."""
    case = build_case(tmp_path, circuit_diode(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    tols = _tols(floor_lut, case)
    i1 = _index(V, ("ln_idu", "M1"))
    i2 = _index(V, ("ln_idu", "M2"))
    v = V[i1]
    base = _expected(s, _floor_arrays, V, (1, 1), tols, one_var=DIODE_ONE_VAR)
    f, f2 = base[i1], base[i2]
    _close(ln_idu_floors(s, V, (1, 1), one_var_only=True), base)
    below = (v.lo + f) / 2
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start={v.component: below}) == {i1: below, i2: f2}
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start={v.component: f + 1.0}) == {i1: f, i2: f2}
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start={v.component: v.lo}) == {i2: f2}
    v2 = V[i2]
    cap2 = (v2.lo + f2) / 2                                    # M2 도 start 에 있으면 캡된다
    th = {v.component: below, ("ln_idu", "M2"): cap2, ("L", "M1"): R4_L[1]}       # θ Mapping 의 다른 성분은 무관
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start=th) == {i1: below, i2: cap2}
    th2 = {v.component: below, ("ln_idu", "M2"): v2.lo - 1.0}
    assert ln_idu_floors(s, V, (1, 1), one_var_only=True, start=th2) == {i1: below}


# ---------------------------------------------------------------- 캐시 (sctx.cell_floors, 정점 (kind, w_key, 칸)·전도 ("conduction", kind, w_key, 칸) 1회)

def _cell_of(l_cells, cell):
    return tuple(l_cells[cell]) if isinstance(cell, int) else tuple(cell)


def _floor_keys(s, kind, m):
    """sctx.cell_floors 의 정점 키 (kind, w_key 100, 칸) -> 칸 (lo, hi). 칸은 index 또는 (lo, hi) 어느 표기든 받는다."""
    l_cells = dict(s.domain.l_cells)[m]
    return {key: _cell_of(l_cells, key[2]) for key in list(s.cell_floors)
            if isinstance(key, tuple) and len(key) == 3 and key[0] == kind and key[1] == 100}


def _cond_keys(s, kind, m):
    """[r9] 전도 키 ("conduction", kind, w_key 100, 칸) -> 칸 (lo, hi)."""
    l_cells = dict(s.domain.l_cells)[m]
    return {key: _cell_of(l_cells, key[3]) for key in list(s.cell_floors)
            if isinstance(key, tuple) and len(key) == 4 and key[0] == "conduction" and key[1] == kind and key[2] == 100}


def test_cell_floor_cache_is_read(tmp_path, floor_lut):
    case = build_case(tmp_path, circuit_diode(), floor_lut)
    s = case.sctx
    V = s.domain.variables
    tols = _tols(floor_lut, case)
    r1 = ln_idu_floors(s, V, (0, 1))
    n = len(s.cell_floors)
    assert ln_idu_floors(s, V, (0, 1)) == r1 and len(s.cell_floors) == n          # 같은 칸 -> 새 항목 없음
    lc = dict(s.domain.l_cells)
    nk, pk = _floor_keys(s, "nmos", "M1"), _floor_keys(s, "pmos", "M2")
    nc, pc = _cond_keys(s, "nmos", "M1"), _cond_keys(s, "pmos", "M2")
    assert set(nk.values()) == set(nc.values()) == {tuple(lc["M1"][0])}
    assert set(pk.values()) == set(pc.values()) == {tuple(lc["M2"][1])}
    for key, cell in list(nk.items()) + list(pk.items()):
        assert math.isclose(s.cell_floors[key], peak_floor(_floor_arrays(key[0]), *cell), rel_tol=1e-12)
    for key, cell in list(nc.items()) + list(pc.items()):
        assert math.isclose(s.cell_floors[key], _cond(_floor_arrays, tols, key[1], cell), rel_tol=1e-12)
    # 캐시 값을 읽는다(다시 계산하지 않는다): 항목을 바꾸면 결과가 따라온다 -- 정점·전도 두 항목 모두
    i1 = _index(V, ("ln_idu", "M1"))
    lo = V[i1].lo
    for key in nk:
        s.cell_floors[key] = lo + 0.5
    for key in nc:
        s.cell_floors[key] = lo + 0.25
    assert ln_idu_floors(s, V, (0, 1))[i1] == lo + 0.5                              # max(전도, 정점) = 정점 항목
    for key in nc:
        s.cell_floors[key] = lo + 0.75
    assert ln_idu_floors(s, V, (0, 1))[i1] == lo + 0.75                             # 전도 항목이 더 크면 전도 항목


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
    tols = _tols(lut, case)
    arrs = {}
    for kind in ("nmos", "pmos"):
        with np.load(files[(kind, wk[kind])]) as z:
            arrs[kind] = {k: np.asarray(z[k]) for k in ("L", "VGS", "VDS", "ID", "GM", "W")}
    l_cells = dict(s.domain.l_cells)
    assert any(lo < hi for lo, hi in l_cells["M1"])          # 앵커 여럿을 묶는 칸이 있다
    n1, n2 = len(l_cells["M1"]), len(l_cells["M2"])
    checked = cond_wins = 0
    for c1 in range(n1):
        cells = (c1, c1 % n2)
        got = ln_idu_floors(s, V, cells)
        exp = {}
        for idx, v in enumerate(V):
            if v.component[0] != "ln_idu":
                continue
            m = v.component[1]
            lo_c, hi_c = l_cells[m][cells[0] if m == "M1" else cells[1]]
            peak = peak_floor(arrs[KIND[m]], lo_c, hi_c)
            cond = conduction_floor(arrs[KIND[m]], lo_c, hi_c, tols[KIND[m]])
            f = expected_floor(cond, peak)
            if f is not None and v.lo < f < v.hi:
                exp[idx] = f
                cond_wins += cond is not None and cond > peak
        _close(got, exp)
        checked += len(exp)
    assert checked >= n1                                       # 칸마다 적어도 하나는 상자 안 하한
    assert cond_wins >= 1                                      # 실 LUT 에서 전도 하한이 정점 하한을 이기는 칸이 있다(r9 비공허)


# ---------------------------------------------------------------- S-4f 적용: solve_eps·층 0 최대-최소

def _lines(root, ctx_fp):
    p = Path(root) / ctx_fp / "evals.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def _th(line):
    return {tuple(k): v for k, v in line["theta"]}


def _m1_cell(s, cells):
    order = [m for m, _ in s.domain.l_cells]
    return dict(s.domain.l_cells)["M1"][cells[order.index("M1")]]


# [r7 2026-10-09] floor LUT 를 1.4 단위 검사와 맞게 다시 만들어(`_floor_arrays`) M1 칸(L 2 µm) 정점 하한이 −7.04 -> −13.18 로 바뀌었다
# (peak_floor 독립 계산). 시작 좌표 ln_idu(M1) 는 옛 판과 같은 뜻(하한 바로 위, 간격 0.04)으로 −13.14 -- 이 값에서 시작점이 봉인된다
# (start_points 로 확인한 입력 선택이지 기대값이 아니다; 판정은 아래 test 의 '하한 아래 평가 없음').
DIODE_START = {("L", "M1"): 2e-6, ("L", "M2"): 2e-6, ("current", "M2"): 1.6e-8, ("ln_idu", "M1"): -13.14,
               ("ln_idu", "M2"): -15.0}


@pytest.mark.parametrize("axis", [AXIS_POWER, "area_search_m2"])
def test_solve_eps_respects_one_var_floor(tmp_path, floor_lut, short_root, axis):
    """solve_eps 는 1변수 writer(M1)의 ln_idu 를 min(칸 정점 하한, 시작 좌표) 아래에서 평가하지 않는다(S-4f, 3.13).
    floor LUT 에서 하한(≈ −13.18)은 봉인된 시작 좌표 −13.14 바로 아래 -- 전력·면적 최소화가 내려가려는 방향이다."""
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


# ---------------------------------------------------------------- L 동치류 멤버 = 주인 L 칸 (설계 40 §3.7 / D-GB7a, fix-cellfloor-lclass)
# θ 는 동치류마다 주인 L 하나(멤버 ("L", m) 성분 없음, sctx.dc.l_ties = ((멤버, 주인), ...)) -> l_cells 에 멤버 칸이 없다.
# 멤버의 ("ln_idu", m) 성분 하한은 주인 L 칸에서 계산한다(멤버 L = 주인 L). 이 절 test 는 모두 l_classes 를 넘겨 l_ties 가 비지
# 않은 경로를 쓴다 -- l_classes 없는 build_case(l_ties = ()) 로는 고치기 전 KeyError(멤버 이름)가 재현되지 않는다.
# [U17 ①-b] l_classes 는 S1v 필드로 넣는다(sizing conftest `inject_l_classes`), l_ties 는 graph/kernel 필드(conftest `l_ties_of`).

TIED_KIND = {"M1": "nmos", "M2": "pmos", "M3": "nmos", "M4": "pmos"}     # 아래 손 회로의 MOS kind(입력 선언)


def circuit_tied_cs2():
    """2단 CS: M1 nmos (o1, in, gnd) + M2 pmos 부하 (o1, pb, vdd) -> M3 nmos (o2, o1, gnd) + M4 pmos 부하 (o2, pb, vdd).
    두 단이 비대칭(M3 gate = o1)이라 궤도 묶음으로 M3 가 사라지지 않고 ("ln_idu", "M3") 성분이 남는다. 동치류 {M1(주인), M3}."""
    return topo("hand_tied_cs2",
                [mos("M1", "nmos", "o1", "in", "gnd"), mos("M2", "pmos", "o1", "pb", "vdd"),
                 mos("M3", "nmos", "o2", "o1", "gnd"), mos("M4", "pmos", "o2", "pb", "vdd")],
                {"in": ("input", "single_ended_input"), "o2": ("output", "single_ended_output")},
                bias=["pb"])


def _tied_case(tmp, lut):
    """build_case 와 같은 입력 사슬에 l_classes(LClassStub, sizing CONTRACT 14.1 속성 셋)만 더한다."""
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    acc = new_access(lut)
    td, spec = load_spec(Path(tmp) / "case", circuit_tied_cs2())
    inputs = dc_inputs_from_spec(spec)
    s1 = build_s1(td, dict(inputs.supplies_v))
    # [U17 ①-b] L 동치류 입력 = S1v 필드 `graph/s1v: l_classes`(설계 40 v1.9.1 §2.4.8 D1; build_kernel_context(l_classes=) 삭제)
    dc = build_kernel_context(inject_l_classes(s1, (LClassStub("M1", ("M1", "M3")),)), inputs, acc)
    pdk, rule = write_decls(Path(tmp) / "pdk")
    sctx = build_search_context(dc, spec, SearchSettings(600.0, 40, None, tuple(SRC), None), None, pdk, rule, code_fp=CODE_FP)
    return SimpleNamespace(acc=acc, dc=dc, sctx=sctx)


@pytest.mark.parametrize("owner_cell", [0, 1])
def test_l_class_member_floor_in_owner_cell(tmp_path, floor_lut, owner_cell):
    case = _tied_case(tmp_path, floor_lut)
    s = case.sctx
    V = s.domain.variables
    ties = dict(l_ties_of(case.dc))
    # 전제(비공허): 멤버 M3 는 l_ties 에 있고 l_cells 에 칸이 없으며 ln_idu 성분은 있다.
    assert ties == {"M3": "M1"}
    order = [m for m, _ in s.domain.l_cells]
    assert "M3" not in order and "M1" in order
    i3 = _index(V, ("ln_idu", "M3"))
    i1 = _index(V, ("ln_idu", "M1"))
    l_cells = dict(s.domain.l_cells)
    tols = _tols(floor_lut, case)

    def expect(cells):
        # oracle (a)+(d): 기대 하한 = 그 성분 소자의 L 칸 -- 멤버면 주인(l_ties) 칸 -- 에서 npz 배열로 직접 계산한 전도·정점 하한의
        # max(conftest conduction_floor·peak_floor·expected_floor = 계약 3.22 문장의 격자 계산). 멤버 L = 주인 L 은 설계 40 §3.7 D-GB7a.
        out = {}
        for idx, v in enumerate(V):
            t, m = v.component
            if t != "ln_idu":
                continue
            cm = ties.get(m, m)
            cell = l_cells[cm][cells[order.index(cm)]]
            f = expected_floor(_cond(_floor_arrays, tols, TIED_KIND[m], cell), peak_floor(_floor_arrays(TIED_KIND[m]), *cell))
            if f is not None and v.lo < f < v.hi:
                out[idx] = f
        return out

    cells = tuple(owner_cell if m == "M1" else 0 for m in order)
    other = tuple((1 - owner_cell) if m == "M1" else 0 for m in order)       # 주인 칸만 바꾼다
    exp, exp2 = expect(cells), expect(other)
    assert i3 in exp and i1 in exp and i3 in exp2                     # 멤버·주인 하한이 상자 안(비공허)
    assert exp2[i3] != exp[i3]                                         # toy LUT 는 칸마다 IDu 가 e^0.7 배 -> 주인 칸이 갈린다
    _close(ln_idu_floors(s, V, cells), exp)
    _close(ln_idu_floors(s, V, other), exp2)


# ---------------------------------------------------------------- 실경로: 단계 A l_classes -> kernel -> search -> find_front (library)

LCLASS_LIB = ("two_stage_ota_sf", "folded_cascode", "ngcc_3stage_ff")


@pytest.fixture(scope="module")
def lib_env():
    from generality.pipeline import Env
    return Env()


@pytest.mark.parametrize("name", LCLASS_LIB)
def test_library_real_path_find_front_with_l_classes(tmp_path, lib_env, name):
    """고치기 전에는 solve_eps -> _layout -> ln_idu_floors 에서 KeyError(멤버 이름)로 죽었다. oracle (a): 계약 3.16 의 반환형
    (SearchFront) + '예외 없음' -- 기대 수치는 없다. two_stage_ota_sf spec 은 two_stage_ota 를 value_from_file 로 참조하므로
    library 폴더(두 원본이 같이 있음)에서 그대로 읽는다. 단계 A 상태(ok·stopped)와 무관하게 l_classes 를 넘긴다."""
    from generality.pipeline import CAPACITANCE_BOX, LIBRARY, RESISTANCE_BOX
    from gmid_engine.authoring import load_sizing_spec, load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.pipeline import run_stage_a
    from gmid_engine.search import SearchFront, SearchSettings, build_search_context, find_front
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec

    env = lib_env
    tp = LIBRARY / (name + ".topology.json")
    td = load_topology(str(tp))
    spec = load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), td, env.catalog)
    inputs = dc_inputs_from_spec(spec)
    sup = dict(inputs.supplies_v)
    stage_a = run_stage_a(tp, None, env.lut, pdk_decl=env.pdk, lut_rule_decl=env.lut_rule, output_dir=tmp_path / "a", supplies_v=sup)
    # [U17 ①-b] 단계 A 의 L 동치류 = S1v 필드 `graph/s1v: l_classes`(D1) -- 같은 build_s1(td, sup) 에 그 필드를 넣어 커널 컨텍스트를 만든다(옛 l_classes= 입력과 같은 값).
    l_classes = stage_a.s1.value("graph", "s1v", "l_classes")
    dc = build_kernel_context(inject_l_classes(build_s1(td, sup), l_classes), inputs, env.access)
    settings = SearchSettings(60.0, 40, RESISTANCE_BOX, (("cellfloor_lclass", "test_fixture"),), CAPACITANCE_BOX)
    sctx = build_search_context(dc, spec, settings, None, env.pdk, env.lut_rule, code_fp=stage_a.code_fp)
    comps = {v.component for v in sctx.domain.variables}
    # 전제(비공허): 동치류 멤버가 있고 그중 하나 이상이 ln_idu 성분을 가지며 l_cells 에는 멤버가 없다(하한 계산이 멤버를 만난다).
    assert l_ties_of(dc)
    # [U17 ①-d] 40 v1.8 §6-8 D-2(MOS d·s 같은 라벨 c)로 정준 순서·dc_colour 순서가 바뀌어 two_stage_ota_sf 의 writer 계획이 달라졌고, 그 회로에서는
    # 동치류 멤버에 ln_idu 성분이 더 이상 없다(§6-8 '이 순서를 기대값으로 쓰는 test 는 독립 test 작성 주체가 다시 만든다'). 비공허 전제는 나머지 두 회로
    # (folded_cascode·ngcc_3stage_ff)가 지키고, two_stage_ota_sf 는 '예외 없음'만 본다.
    if name != "two_stage_ota_sf":
        assert any(("ln_idu", m) in comps for m, _ in l_ties_of(dc))
    assert not {m for m, _ in l_ties_of(dc)} & {m for m, _ in sctx.domain.l_cells}
    fr = find_front(sctx, [])
    assert isinstance(fr, SearchFront)
