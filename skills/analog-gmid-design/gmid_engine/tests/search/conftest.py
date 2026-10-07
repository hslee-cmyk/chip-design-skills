"""tests/search 공용 -- `gmid_engine/search/CONTRACT.md`(r4) + sizing·metrics·core·lut 계약만 근거로 만든 입력과 독립 계산.
search `.py` 소스는 열람하지 않았다(작성자 ≠ 검증자).

- toy LUT: sizing conftest 의 r4 toy(VDSAT 열 있음 -> 봉인 7 실판정, `write_r4_lut`)와 VDSAT 열 없는 변형(봉인 7 undefined ->
  `pending_seal_7` 경로)을 그대로 쓴다. 격자는 2진 분수라 손계산이 정확하다.
- toy PDK 선언: core 9.1 형식(lef_statement 원본 하나)으로 `manufacturing_grid_m`·`min_finger_w_m` 을 선언한다.
- 손 회로: 회로 C(nmos M1 + pmos 부하 M2, sizing conftest), 회로 P(pmos M1 + θ 저항 R1 -> gnd).
- 기대값: npz 배열·스냅샷 입력 열·닫힌 식으로 이 파일/test 가 계산한다. 비지배 필터·ε 격자는 독립 구현(`ref_*`).
- S3 root 는 Windows 경로 길이(계약 6절) 때문에 %TEMP% 바로 아래 짧은 폴더(`short_root`)를 쓴다.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from sizing.conftest import (  # noqa: F401  (다른 test 파일이 여기서 가져간다)
    R4_GRIDS,
    R4_L,
    R4_VDS,
    R4_VGS,
    R4_VS,
    SUPPLIES,
    W_M,
    circuit_cs_pmos_load,
    mos,
    r4_arrays,
    r4_ln_idu,
    real_lut_v2,
    rel_close,
    tamper,
    theta_r4c,
    topo,
    two,
    write_r4_lut,
)
from sizing.conftest import I0, LAM, r4_vs_term  # noqa: E402
from metrics.conftest import load_case  # noqa: E402

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parents[2]
TESTS_DIR = HERE.parent

GRID_UM = "0.01"        # toy PDK 제조 격자 0.01 µm = 1e-8 m (toy LUT 격자와 같음)
MINW_UM = "0.5"         # toy PDK 최소 finger 폭 0.5 µm
GRID = 1e-8
W_MIN = 5e-7
SRC = (("front_budget_s", "test_fixture"),)


# ---------------------------------------------------------------- toy PDK 선언 (core 9.1)

def write_pdk(root, grid_um=GRID_UM, minw_um=MINW_UM, with_minw=True):
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    lef = root / "toy.lef"
    lef.write_text("MANUFACTURINGGRID %s ;\nMINW %s ;\n" % (grid_um, minw_um), encoding="utf-8")
    sha = hashlib.sha256(lef.read_bytes()).hexdigest()
    q = {"manufacturing_grid_m": {"source": "lef", "expression": "MANUFACTURINGGRID", "basis": "toy grid"}}
    if with_minw:
        q["min_finger_w_m"] = {"source": "lef", "expression": "MINW", "basis": "toy min finger"}
    decl = {"schema": "gmid_pdk_decl/1", "pdk": "toy", "pdk_root": str(root).replace("\\", "/"),
            "sources": {"lef": {"path": "toy.lef", "sha256": sha, "format": "lef_statement", "encoding": "utf-8",
                                "units_m": {"": 1e-6}}},
            "quantities": q}
    (root / "pdk.json").write_text(json.dumps(decl), encoding="utf-8")
    return read_pdk_decl(str(root / "pdk.json"), BoundedLRU(8))


# ---------------------------------------------------------------- LUT

@pytest.fixture(scope="session")
def lut_sealed(tmp_path_factory):
    """VDSAT 열(nmos·pmos) -> 봉인 7 판정."""
    return write_r4_lut(tmp_path_factory.mktemp("s_lut_sealed"))


@pytest.fixture(scope="session")
def lut_pending(tmp_path_factory):
    """VDSAT 열 없음 -> 봉인 7 undefined(lut_vdsat_column_missing) -> pending_seal_7."""
    return write_r4_lut(tmp_path_factory.mktemp("s_lut_pending"), vdsat=())


def new_access(lut):
    from gmid_engine.lut import LutMemo
    from gmid_engine.sizing import pre_layout_lut_access
    return pre_layout_lut_access(LutMemo(lut, point=4096, curve=4096, root=4096))


@pytest.fixture
def short_root():
    """S3 root -- %TEMP% 바로 아래 짧은 폴더(지문 두 개 64자 + 파일 이름이 260자 안에 들게)."""
    d = tempfile.mkdtemp(prefix="s6", dir=os.environ.get("TEMP") or None)
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------- 손 회로

def circuit_c(with_cap=False):
    """회로 C: M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd). with_cap: CL (out, gnd) 값은 spec 에서."""
    d = circuit_cs_pmos_load()
    if with_cap:
        d["passive_elements"] = [two("CL", "capacitor", "out", "gnd")]
    return d


def circuit_p():
    """회로 P: M1 pmos (out, in, vdd) + R1 (out, gnd), R1 값은 θ resistance(spec engine). V(out) = I·R."""
    return topo("hand_pres", [mos("M1", "pmos", "out", "in", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "out", "gnd")])


def theta_p(dc, i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    """회로 P 의 θ. 전류 성분 키는 스키마(입력)에서 읽는다(기저 free 원소가 M1/R1 중 무엇이든 같은 전류)."""
    comps = dict.fromkeys(dc.schema.components)
    th = {("L", "M1"): l1, ("ln_idu", "M1"): r4_ln_idu("pmos", vgs, 1.8 - i * r, 0.0), ("resistance", "R1"): r}
    for k in comps:
        if k[0] == "current":
            th[k] = i
    assert set(th) == set(comps), (sorted(th), sorted(comps))
    return th


def circuit_n():
    """회로 N: M1 nmos (out, in, gnd) + R1 (vdd, out), R1 = θ resistance. 레일에 채널이 닿는 MOS 는 gnd(0 V) 의 M1 뿐 ->
    b_P = |0|·tol_I = 0 -> 계약 3.6 '합이 0 이면 None'."""
    return topo("hand_nres", [mos("M1", "nmos", "out", "in", "gnd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "vdd", "out")])


def theta_n(dc, i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    comps = dict.fromkeys(dc.schema.components)
    th = {("L", "M1"): l1, ("ln_idu", "M1"): r4_ln_idu("nmos", vgs, 1.8 - i * r, 0.0), ("resistance", "R1"): r}
    for k in comps:
        if k[0] == "current":
            th[k] = i
    assert set(th) == set(comps), (sorted(th), sorted(comps))
    return th


def on_mask(a):
    return (a["ID"] > 0) & (a["GM"] > 0)


def expect_box(pre_arr, all_arrs):
    """3.19 의 독립 계산. pre_arr = 레이아웃 전 슬라이스 배열, all_arrs = 그 kind 의 모든 슬라이스 배열."""
    vgs = np.asarray(pre_arr["VGS"], dtype=float)
    tol = math.ulp(max(abs(vgs[0]), abs(vgs[-1])))
    z = [i for i, v in enumerate(vgs) if abs(v) <= tol]
    assert z, "test 입력에 VGS 0 이 있어야 한다"
    i0 = z[0]
    ID, GM = pre_arr["ID"][:, i0], pre_arr["GM"][:, i0]
    m = (ID > 0) & (GM > 0)
    i_off = float(ID[m].min())
    i_max = max(float(a["ID"][on_mask(a)].max()) for a in all_arrs)
    return i_off, i_max


def expect_ln_idu_bounds(a, w_m=W_M):
    """3.7 ln_idu 포락선의 독립 계산: hi = on_mask 점 ln(ID·L/w_m) 최대, lo = (L, VDS, VS) 곡선마다 gm/ID 최대 VGS 점(그
    점이 on_mask 인 곡선만)의 ln IDu 중 최소."""
    ID, GM = a["ID"], a["GM"]
    Ls = np.asarray(a["L"], dtype=float)
    m = on_mask(a)
    lnu = np.full(ID.shape, -np.inf)
    lnu[m] = np.log(ID[m] * np.broadcast_to(Ls[:, None, None, None], ID.shape)[m] / w_m)
    hi = float(lnu[m].max())
    lo = math.inf
    nL, nG, nD, nS = ID.shape
    for i in range(nL):
        for k in range(nD):
            for s in range(nS):
                with np.errstate(divide="ignore", invalid="ignore"):
                    g = GM[i, :, k, s] / ID[i, :, k, s]
                g = np.where(np.isfinite(g), g, -np.inf)
                j = int(np.argmax(g))
                if m[i, j, k, s]:
                    lo = min(lo, float(lnu[i, j, k, s]))
    return lo, hi


CELLS_C = (0, 1)        # 회로 C: M1 L = 1e-6 -> 칸 0, M2 L = 2e-6 -> 칸 1 (l_cells 는 L 앵커 오름차순, 이름순 MOS)
CELLS_P = (0,)


def build_case(tmp, topo_doc, lut, constraints=(), elements=(), budget_s=600.0, eval_budget=40, rbounds=None,
               archive_root=None, pdk=None, sources=SRC):
    """topology·spec -> KernelContext -> SearchContext. 반환 SimpleNamespace(td, spec, dc, acc, pdk, settings, sctx)."""
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    tmp = Path(tmp)
    acc = new_access(lut)
    td, spec = load_case(tmp / "case", topo_doc, SUPPLIES, elements=elements, constraints=constraints)
    inputs = dc_inputs_from_spec(spec)
    s1 = build_s1(td, dict(inputs.supplies_v))
    dc = build_kernel_context(s1, inputs, acc)
    pdk = pdk if pdk is not None else write_pdk(tmp / "pdk")
    settings = SearchSettings(budget_s, eval_budget, rbounds, tuple(sources))
    sctx = build_search_context(dc, spec, settings, archive_root, pdk)
    return SimpleNamespace(td=td, spec=spec, dc=dc, acc=acc, pdk=pdk, settings=settings, sctx=sctx)


# ---------------------------------------------------------------- 스냅샷 읽기 (입력 열)

def col(snap, kind, field):
    return dict(snap.column(kind, field))


def node_v(snap):
    v = col(snap, "node", "dc_rail_v")
    v.update(col(snap, "node", "dc_v"))
    return v


def snap_of(result):
    """EvalResult.evaluation -> 봉인/대기 DcEvaluation 의 스냅샷."""
    return result.evaluation.snapshot


def to_theta_fn(variables, fixed):
    """x(로그 변수는 ln) -> θ dict. fixed = 변수 밖 성분 dict(L 등)."""
    def f(x):
        th = dict(fixed)
        for v, xv in zip(variables, x):
            th[v.component] = math.exp(xv) if v.log else xv
        return th
    return f


def x_of(variables, theta):
    th = dict(theta)
    return tuple(math.log(th[v.component]) if v.log else th[v.component] for v in variables)


def fixed_l(theta):
    return {k: v for k, v in dict(theta).items() if k[0] == "L"}


def expected_fd_steps(sctx, base, vgs_grid=R4_VGS, vds_grid=R4_VDS):
    """3.11 스텝 식의 독립 계산(base 스냅샷 입력 열 + LUT 격자). -> [h | None] (sctx.domain.variables 순서, 부호 전)."""
    import bisect
    snap = snap_of(base)
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    writers = col(snap, "node", "dc_writer")
    windows = col(snap, "node", "dc_window")
    drop = col(snap, "device", "dc_drop_current")
    th = dict(base.theta)
    cone = dict(sctx.dc.schema.current_cone)
    out = []
    for v in sctx.domain.variables:
        t, key = v.component
        if t == "ln_idu":
            op = ops[key]
            g = list(vgs_grid)
            i = min(max(bisect.bisect_right(g, op.vgs) - 1, 0), len(g) - 2)
            out.append((g[i + 1] - g[i]) * op.gm_id)
        elif t == "y":
            node = [n for n, w in writers.items() if w.y_key == key][0]
            w = windows.get(node)
            d = min(b - a for a, b in zip(vds_grid, vds_grid[1:]))
            out.append(None if w is None or w.hi - w.lo == 0 else d / (w.hi - w.lo))
        elif t == "current":
            ms = [m for m, terms in cone.items() if any(tt.source == key for tt in terms) and tol.get(m) is not None]
            if not ms:
                ms = [m for m in ops if tol.get(m) is not None]
            out.append(min(tol[m] * ops[m].gm_id for m in ms) if ms else None)
        elif t == "resistance":
            tmin = min(x for x in tol.values() if x is not None)
            i = abs(drop[key])
            out.append(0.0 if i == 0 else tmin / (i * th[("resistance", key)]))
        else:
            raise AssertionError(v)
    return out


# ---------------------------------------------------------------- 독립 비지배 필터 (계약 3.1 문장 그대로)

def ref_nondominated(points, ties):
    """points = ((id, (축...), slack), ...), ties = 축마다 폭 또는 width(id_p, id_q). -> (kept, folded, dominated) index."""
    def w(ax, p, q):
        t = ties[ax]
        return t(p[0], q[0]) if callable(t) else t

    def rel(p, q):
        better = worse = 0
        for ax, (a, b) in enumerate(zip(p[1], q[1])):
            wd = w(ax, p, q)
            if abs(a - b) <= wd:
                continue
            if a < b - wd:
                better += 1
            else:
                worse += 1
        return better, worse

    order = sorted(range(len(points)), key=lambda i: (points[i][1][0], -points[i][2], points[i][0]))
    kept, folded, dominated = [], [], []
    for i in order:
        p = points[i]
        fold_to = dom_by = None
        for k in kept:
            b, wo = rel(p, points[k])
            if b == 0 and wo == 0:
                fold_to = k
                break
            if b == 0 and wo >= 1 and dom_by is None:
                dom_by = k
        if fold_to is not None:
            folded.append((i, fold_to))
            continue
        if dom_by is not None:
            dominated.append((i, dom_by))
            continue
        for k in list(kept):
            b, wo = rel(p, points[k])
            if wo == 0 and b >= 1:
                kept.remove(k)
                dominated.append((k, i))
        kept.append(i)
    pos = {i: n for n, i in enumerate(order)}
    return tuple(sorted(kept, key=pos.get)), tuple(sorted(folded)), tuple(sorted(dominated))


def dominates(p, q, wp, wa):
    """p, q = (power, area). 폭 wp·wa 로 p 가 q 를 지배."""
    better = worse = 0
    for a, b, wd in ((p[0], q[0], wp), (p[1], q[1], wa)):
        if abs(a - b) <= wd:
            continue
        if a < b - wd:
            better += 1
        else:
            worse += 1
    return worse == 0 and better >= 1


def all_tied(p, q, wp, wa):
    return abs(p[0] - q[0]) <= wp and abs(p[1] - q[1]) <= wa


# ---------------------------------------------------------------- ε 격자 (계약 3.15 문장 그대로)

def ref_eps_count(lo, hi, gap):
    """열린 구간 (lo, hi) 안의 hi − k·gap (k ≥ 1) 점 수."""
    if not hi > lo or gap <= 0:
        return 0
    n = 0
    k = 1
    while hi - k * gap > lo:
        n += 1
        k += 1
    return n


def ref_eps_values(lo, hi, gap):
    out = []
    k = 1
    while hi - k * gap > lo:
        out.append(hi - k * gap)
        k += 1
    return out


# ---------------------------------------------------------------- 스냅샷 -> 기대 목적·제약 (3.6·3.8 독립 계산)

def _dc_key():
    from gmid_engine.sizing import DC_KEY
    return DC_KEY


def expected_objectives(snap):
    basis = snap.value("graph", _dc_key(), "dc_current_basis")
    rails = col(snap, "node", "dc_rail_v")
    cur = col(snap, "device", "dc_current")
    cur_in = {k: 0.0 for k in rails}
    for el, a, b in basis.ends:
        if el not in cur:
            continue
        if a in cur_in:
            cur_in[a] += cur[el]
        if b in cur_in:
            cur_in[b] -= cur[el]
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    bp = 0.0
    rows = False
    for k, v in rails.items():
        cands = [tol[el] * ops[el].current * ops[el].gm_id for el, a, b in basis.ends
                 if el in ops and k in (a, b) and tol.get(el) is not None]
        if cands:
            rows = True
            bp += abs(v) * max(cands)
    return {
        "power": sum(rails[k] * cur_in[k] for k in rails),
        "per_rail": tuple(sorted(cur_in.items())),
        "kcl": sum(cur_in.values()),
        "gate_area": sum(o.W * o.L for o in ops.values()),
        "bp": bp if rows and bp != 0 else None,
    }


def expected_rows(snap, w_min, grid):
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    coord = col(snap, "device", "dc_coord")
    rows, undefined = [], []
    for m in [k for k, _ in snap.column("device", "dc_op")]:
        op = ops[m]
        rows.append(("w_min:%s" % m, (op.W - w_min) / grid))
        t = tol.get(m)
        if t is None or t <= 0:
            undefined.append(m)
            continue
        rows.append(("seal6_bulk:%s" % m, (min(op.vsb, op.vds + op.vsb) + t) / t))
        if coord[m].role == "writer":
            r_peak = math.log(I0[op.kind]) + LAM * op.vds + r4_vs_term(op.vsb)
            rows.append(("inversion_floor:%s" % m, (op.ln_idu - r_peak) * op.gm_id / t))
    return rows, sorted(undefined)


# ---------------------------------------------------------------- I-8 결정론 탐침 (subprocess 에서 부른다)

def front_signature(fr):
    """SearchFront -> 비교용 JSON 가능 값(점 id·θ hex·목적 hex)."""
    def pts(seq):
        return [[p.point_id, [float(v).hex() for _, v in p.result.theta],
                 float(p.result.objectives.power_w).hex(), float(p.result.objectives.area_m2).hex()] for p in seq]
    return {"front": pts(fr.front), "pending": pts(fr.pending_front), "unmeasured": pts(fr.unmeasured_front)}


def determinism_probe(tmpdir, eval_budget=40):
    """회로 C + VDSAT toy LUT, 선언 E_B 로 find_front 한 번 -> JSON 문자열(front 서명·kernel·run_id·벽시계 정지)."""
    from gmid_engine.search import find_front
    tmp = Path(tmpdir)
    lut = write_r4_lut(tmp / "lut")
    case = build_case(tmp, circuit_c(), lut, constraints=(("gain_ss_db", ">=", 10.0, None),),
                      eval_budget=eval_budget, budget_s=600.0)
    fr = find_front(case.sctx, [theta_r4c()])
    perf = dict(fr.perf)
    out = front_signature(fr)
    out.update(kernel=perf["kernel_calls"], run_id=fr.run_id, wall=perf["stops_wall_budget"])
    return json.dumps(out, sort_keys=True)
