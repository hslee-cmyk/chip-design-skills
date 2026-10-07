"""tests/sizing 공용 픽스처 -- `gmid_engine/sizing/CONTRACT.md`(+ core·lut·graph·authoring 계약)만 근거로 만든 입력과
독립 계산. sizing `.py` 소스는 열람하지 않았다.

- toy LUT: 이 파일이 정한 해석식으로 npz 를 직접 쓴다(nmos·pmos 한 폭 슬라이스씩). 식이 분리형이고 로그공간에서
  VGS·VDS 에 선형이라, lut 계약의 다중선형(로그공간) 보간·역보간 결과를 손으로 닫힌 식으로 낼 수 있다:
      ID[L, VGS, VDS, VS] = (W/L) · I0[kind] · exp(B·VGS + LAM·VDS − A·VS²)
      GM = ID · GMAX · exp(−VGS / V0),  GDS = ID / 10,  VTH = 0.4
  VS 방향만 곡률(−A·VS²)이 있어 tol_V id_equivalent 가 0 이 아니다(VS 축 LOO = A·h²). VS 축은 음수 점(−0.45)을 포함해
  봉인 6(bulk 역바이어스) 위반을 LUT 축 안에서 만들 수 있다.
- 손 회로: topology JSON 을 이 파일에서 dict 로 만들어 authoring `load_topology` 로 읽는다(입력 생성용 공개 API).
- 기대값: `Oracle` 이 npz 배열(numpy 로 직접 읽음)·닫힌 식으로 계산한다. 피검 함수로 기대값을 만들지 않는다.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.graph import build_s1
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set
from gmid_engine.sizing import DcInputs, LutAccess, build_kernel_context

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parents[2]
LIBRARY = SKILL_DIR / "assets" / "library"

# ---------------------------------------------------------------------------
# toy LUT 해석식 (이 test 가 정한 값)
# ---------------------------------------------------------------------------
W_M = 1e-6                      # 슬라이스 폭 -> w_key 100 (grid 1e-8)
W_KEY = 100
GRID_M = 1e-8
TOY_L = (1e-6, 2e-6)
TOY_VGS = tuple(round(0.1 * i, 10) for i in range(19))          # 0.0 .. 1.8
TOY_VDS = tuple(round(0.3 * i, 10) for i in range(7))           # 0.0 .. 1.8
TOY_VS = (-0.45, 0.0, 0.45, 0.9, 1.35, 1.8)
I0 = {"nmos": 1e-8, "pmos": 5e-9}
B = 8.0
LAM = 0.1
A = 0.5
GMAX = 25.0
V0 = 0.8
DEVICE_OF = {"nmos": "toyn", "pmos": "toyp"}
SUFFIX = {"nmos": "_n", "pmos": "_p"}
TOY_SPEC = LutSpec(GRID_M, (("nmos", 1e-6), ("pmos", 1e-6)), (("toyn", "nmos"), ("toyp", "pmos")),
                   (("nmos", "_n"), ("pmos", "_p")))
W_KEYS = (("nmos", W_KEY), ("pmos", W_KEY))
EPS = np.finfo(float).eps


def toy_arrays(kind):
    Lg = np.asarray(TOY_L)[:, None, None, None]
    G = np.asarray(TOY_VGS)[None, :, None, None]
    D = np.asarray(TOY_VDS)[None, None, :, None]
    S = np.asarray(TOY_VS)[None, None, None, :]
    ID = (W_M / Lg) * I0[kind] * np.exp(B * G + LAM * D - A * S * S)
    GM = ID * GMAX * np.exp(-G / V0)
    return {
        "W": np.float64(W_M),
        "L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
        "ID": ID, "GM": GM, "GDS": ID / 10.0, "VTH": np.full(ID.shape, 0.4),
        "meta_json": np.str_('{"model_files_sha256": {}}'),
        "corner": np.str_("tt"), "temp_c": np.float64(27.0),
    }


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_toy_lut(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for kind in ("nmos", "pmos"):
        p = root / ("toy_%s.npz" % kind)
        np.savez(p, **toy_arrays(kind))
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": _sha(p)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}),
                                        encoding="utf-8")
    shp = (len(TOY_L), len(TOY_VGS), len(TOY_VDS), len(TOY_VS))
    cap = {"L": np.asarray(TOY_L), "VGS": np.asarray(TOY_VGS), "VDS": np.asarray(TOY_VDS), "VS": np.asarray(TOY_VS),
           "w_ref_m": np.float64(W_M), "corner": np.str_("tt"), "temp_c": np.float64(27.0)}
    for kind in ("nmos", "pmos"):
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    np.savez(root / "cap.npz", **cap)
    return root / "manifest.json", root / "cap.npz"


@pytest.fixture(scope="session")
def toy_lut_paths(tmp_path_factory):
    return write_toy_lut(tmp_path_factory.mktemp("sizing_toy_lut"))


@pytest.fixture(scope="session")
def toy_lut(toy_lut_paths):
    m, c = toy_lut_paths
    return load_lut_set(str(m), str(c), TOY_SPEC)


def new_access(lut, n=4096):
    return LutAccess(LutMemo(lut, point=n, curve=n, root=n), W_KEYS)


@pytest.fixture(scope="session")
def toy_access(toy_lut):
    """세션 공용 LutAccess(memo 하나 -- tol_V 표가 프로세스당 1회 계산되게)."""
    return new_access(toy_lut)


# ---------------------------------------------------------------------------
# 독립 oracle (npz 배열 직접 + 닫힌 식)
# ---------------------------------------------------------------------------

def _lin(xs, ys, x):
    xs = list(xs)
    if x == xs[-1]:
        return float(ys[-1])
    i = min(max(bisect.bisect_right(xs, x) - 1, 0), len(xs) - 2)
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return float(ys[i] + (ys[i + 1] - ys[i]) * t)


class Oracle:
    """toy LUT 의 독립 계산. vs 항은 VS 격자 위 −A·VS² 의 구간 선형 보간(lut 계약: 로그공간 다중선형)."""

    @staticmethod
    def vs_term(vsb):
        return _lin(TOY_VS, [-A * v * v for v in TOY_VS], vsb)

    @staticmethod
    def ln_idu(kind, vgs, vds, vsb):
        # IDu = ID·L/w_m = I0·exp(...)  (L 무관)
        return math.log(I0[kind]) + B * vgs + LAM * vds + Oracle.vs_term(vsb)

    @staticmethod
    def vgs_of(kind, ln_idu, vds, vsb):
        """좌표 역산: ln IDu = ln I0 + B·vgs + LAM·vds + vs_term  ->  vgs."""
        return (ln_idu - math.log(I0[kind]) - LAM * vds - Oracle.vs_term(vsb)) / B

    @staticmethod
    def gm_id(vgs):
        return GMAX * math.exp(-vgs / V0)

    @staticmethod
    def tol_v():
        """tol_v_table(...).at(L, vds, "id_equivalent") -- lut 계약 5절 정의를 npz 배열에 직접 적용(셀 최댓값)."""
        arr = toy_arrays("nmos")
        lnI = np.log(arr["ID"])
        g = arr["GM"] / arr["ID"]
        best = 0.0
        grids = (arr["L"], arr["VGS"], arr["VDS"], arr["VS"])
        for ax in (1, 2, 3):
            x = grids[ax]
            n = len(x)
            for j in range(1, n - 1):
                t = (x[j] - x[j - 1]) / (x[j + 1] - x[j - 1])
                sl = [slice(None)] * 4
                sm, sj, sp = list(sl), list(sl), list(sl)
                sm[ax], sj[ax], sp[ax] = j - 1, j, j + 1
                loo = lnI[tuple(sm)] + t * (lnI[tuple(sp)] - lnI[tuple(sm)])
                val = np.abs(loo - lnI[tuple(sj)]) / g[tuple(sj)]
                best = max(best, float(val.max()))
        return best

    @staticmethod
    def gm_bound(kind, L, vds, vsb, W):
        """max over VGS 격자 of (id·gm/id) at (L, vds, vsb) × W/w_m. id·gm/id = GM(폭 w_m)."""
        best = max(math.exp(math.log(W_M / L) + math.log(I0[kind]) + B * v + LAM * vds + Oracle.vs_term(vsb)
                            + math.log(GMAX) - v / V0) for v in TOY_VGS)
        return best * W / W_M


def rel_close(a, b, rtol=1e-9, atol=0.0):
    return abs(a - b) <= max(atol, rtol * max(abs(a), abs(b)))


# ---------------------------------------------------------------------------
# 손 회로 topology
# ---------------------------------------------------------------------------

def mos(name, kind, d, g, s, bulk=None):
    e = {"name": name, "kind": kind, "drain": d, "gate": g, "source": s}
    if bulk is not None:
        e["bulk"] = bulk
    return e


def two(name, kind, a, b):
    return {"name": name, "kind": kind, "terminals": [a, b]}


def topo(name, netlist, ports, passives=(), sources=(), rails=("vdd", "gnd")):
    d = {"schema_version": "2.0", "topology_name": name, "netlist": list(netlist), "supply_nets": list(rails),
         "ports": {k: {"direction": v[0], "role": v[1]} for k, v in ports.items()},
         "passive_elements": list(passives)}
    if sources:
        d["ideal_sources"] = list(sources)
    return d


def load_doc(tmp_path: Path, doc: dict):
    p = Path(tmp_path) / (doc["topology_name"] + ".topology.json")
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return load_topology(str(p))


SUPPLIES = {"vdd": 1.8, "gnd": 0.0}


def circuit_cs_pmos_load():
    """C: M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd). out 은 drain 만 -> G_vgs 밖 W4. 순환 SCC 없음."""
    return topo("hand_cs_pload",
                [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")})


def circuit_cs_res(bulk_m1=None):
    """A: M1 nmos (out, in, gnd) + R1 (vdd, out). out = resistor_drop(known vdd = t0)."""
    return topo("hand_cs_res",
                [mos("M1", "nmos", "out", "in", "gnd", bulk_m1)],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "vdd", "out")])


def circuit_empty_window():
    """D: x 는 drain 만(G_vgs 밖 W4). MA nmos (x, vdd, vdd): lo >= V(vdd); MB pmos (x, gnd, gnd): hi <= V(gnd)."""
    return topo("hand_empty_window",
                [mos("MA", "nmos", "x", "vdd", "vdd"), mos("MB", "pmos", "x", "gnd", "gnd"),
                 mos("MC", "nmos", "x", "inp", "gnd")],
                {"inp": ("input", "single_ended_input"), "x": ("output", "single_ended_output")})


def build_ctx(tmp_path, doc, access, supplies=None, **inputs_kw):
    td = load_doc(tmp_path, doc)
    sup = dict(SUPPLIES if supplies is None else supplies)
    s1 = build_s1(td, sup)
    inputs = DcInputs(tuple(sorted(sup.items())), **inputs_kw)
    return s1, inputs, build_kernel_context(s1, inputs, access)


def detail(exc):
    return dict(exc.record.detail)


@pytest.fixture(scope="session")
def ctx_c(tmp_path_factory, toy_access):
    """회로 C 의 (S1, DcInputs, KernelContext)."""
    return build_ctx(tmp_path_factory.mktemp("ctx_c"), circuit_cs_pmos_load(), toy_access)


@pytest.fixture(scope="session")
def ev_c(ctx_c):
    from gmid_engine.sizing import size_and_seal
    return size_and_seal(ctx_c[2], theta_c())


@pytest.fixture(scope="session")
def ctx_a(tmp_path_factory, toy_access):
    """회로 A(저항 부하) -- R1 값은 θ resistance."""
    return build_ctx(tmp_path_factory.mktemp("ctx_a"), circuit_cs_res(), toy_access)


def theta_a(i=1e-5, r=9e4, vgs=0.6, l1=1e-6):
    """회로 A: V(out) = 1.8 − I·R, x1 = vgs 가 나오는 좌표(VDS = V(out), VSB 0)."""
    vout = 1.8 - i * r
    return {("L", "M1"): l1, ("ln_idu", "M1"): Oracle.ln_idu("nmos", vgs, vout, 0.0),
            ("current", "R1"): i, ("resistance", "R1"): r}


NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff",
        "nmcnr_amplifier", "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota",
        "two_stage_ota_sf")


def spec_catalog():
    from gmid_engine.core import MetricSignature as M
    return {  # authoring SPEC_CONTRACT 5절 픽스처 이름표
        "gain_ss_db": M("dB", "ss", "transfer"), "ugf_ss_hz": M("Hz", "ss", "transfer"),
        "gbw_ss_hz": M("Hz", "ss", "transfer"), "pm_ss_deg": M("deg", "ss", "transfer"),
        "parasitic_pm_ss_deg": M("deg", "ss", "transfer"), "rout_ss_ohm": M("ohm", "ss", "transfer"),
        "ratio_ss_db": M("dB", "ss", "ratio"), "mismatch_sigma_mv": M("mV", "dc", "none"),
        "mirror_ratio_error_mv": M("mV", "dc", "none"), "power_dc_w": M("W", "dc", "none"),
        "area_search_m2": M("m2", "geom", "none"), "supply_current_dc": M("A", "dc", "none", "power"),
        "area_layout_m2": M("m2", "geom", "none", "area"),
    }


_LIB = {}


def library_ctx(name, access):
    """library 회로: (topology raw dict, TopologyDoc, SizingSpecDoc, DcInputs, S1Graph, KernelContext). 프로세스당 1회."""
    if name not in _LIB:
        from gmid_engine.authoring import load_sizing_spec
        from gmid_engine.sizing import dc_inputs_from_spec
        raw = json.loads((LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))
        td = load_topology(str(LIBRARY / (name + ".topology.json")))
        spec = load_sizing_spec(str(LIBRARY / (name + ".sizing_spec.json")), td, spec_catalog())
        inputs = dc_inputs_from_spec(spec)
        s1 = build_s1(td, dict(inputs.supplies_v))
        _LIB[name] = (raw, td, spec, inputs, s1, build_kernel_context(s1, inputs, access))
    return _LIB[name]


def theta_c(x1=None, x2=None, y=0.5, i2=1e-5, l1=1e-6, l2=2e-6):
    """회로 C 의 θ(dict). 기본 x1·x2 = vgs 0.6·0.7 이 나오도록 oracle 로 정한 좌표(VDS = y·1.8, VSB 0)."""
    vout = y * 1.8
    if x1 is None:
        x1 = Oracle.ln_idu("nmos", 0.6, vout, 0.0)
    if x2 is None:
        x2 = Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0)
    return {("L", "M1"): l1, ("L", "M2"): l2, ("ln_idu", "M1"): x1, ("ln_idu", "M2"): x2,
            ("current", "M2"): i2, ("y", "out"): y}


def column_dict(snapshot, kind, field):
    return dict(snapshot.column(kind, field))


def tamper(snapshot, writer, kind, field, updates, version="tampered"):
    """같은 열 전체를 (기존 값 + updates)로 다시 쓴다(core write 열 교체 의미). writer 는 권한표의 그 필드 writer."""
    col = column_dict(snapshot, kind, field)
    col.update(updates)
    return snapshot.write(writer, version, {(kind, field): col})


def seal_item(snapshot, n):
    from gmid_engine.sizing import DC_KEY
    return snapshot.value("graph", DC_KEY, "dc_seal_%d" % n)


def sign_of(kind):
    return 1.0 if kind == "nmos" else -1.0


def mos_table(snap):
    """{MOS: (kind, d, g, s, b)} -- S1 필드(입력)."""
    out = {}
    for name, cls in snap.column("device", "element_class"):
        if cls == "mos":
            p = dict(snap.value("device", name, "pins"))
            out[name] = (snap.value("device", name, "kind"), p["d"], p["g"], p["s"],
                         snap.value("device", name, "bulk").net)
    return out


def terminal_mag(kind, V, d, g, s, b):
    sg = sign_of(kind)
    return sg * (V[g] - V[s]), sg * (V[d] - V[s]), sg * (V[s] - V[b])


def expected_columns(snap, theta, fixed_values=(), resistor_values=()):
    """순환 SCC 가 없는 회로의 dc_columns 독립 계산(CONTRACT 5.4 writer 식 + 창). 스냅샷에서는 계획 결과
    (dc_writer·dc_scc_order·dc_drop_current·dc_L·dc_rail_v)와 S1 필드만 입력으로 읽는다.
    반환: (V, windows, ln_idu)."""
    from gmid_engine.sizing import DC_KEY
    th = dict(theta)
    writers = dict(snap.column("node", "dc_writer"))
    V = dict(snap.column("node", "dc_rail_v"))
    fixed = dict(fixed_values)
    for n, w in writers.items():
        if w.relation in ("declared_target", "input_dc"):
            V[n] = fixed[n]
    mt = mos_table(snap)
    L = dict(snap.column("device", "dc_L"))
    drop = dict(snap.column("device", "dc_drop_current"))
    rvals = dict(resistor_values)
    rails = [v for _, v in snap.column("node", "dc_rail_v")]
    windows = {}
    entries = snap.value("graph", DC_KEY, "dc_scc_order")
    for e in entries:
        assert not e.cyclic, "expected_columns 는 비순환 회로만"
        (x,) = e.nodes
        w = writers[x]
        if w.relation in ("vgs_gate", "vgs_source"):
            kind, d, g, s, b = mt[w.element]
            # 아직 모르는 x 자신은 vgs 계산에 쓰이지 않는다(vds·vsb 는 d·s·b 만)
            vds = sign_of(kind) * (V[d] - V[s]) if x not in (d, s) else None
            vsb = sign_of(kind) * (V[s] - V[b]) if x not in (s, b) else None
            vgs = Oracle.vgs_of(kind, th[("ln_idu", w.element)], vds, vsb)
            V[x] = V[w.known] + sign_of(kind) * vgs if w.relation == "vgs_gate" else V[w.known] - sign_of(kind) * vgs
        elif w.relation == "resistor_drop":
            r = th.get(("resistance", w.element), rvals.get(w.element))
            i = drop[w.element]
            t0 = dict(snap.value("device", w.element, "pins"))["t0"]
            delta = 0.0 if i == 0 else (-i * r if w.known == t0 else i * r)
            V[x] = V[w.known] + delta
        elif w.relation == "input_tie":
            V[x] = V[w.known]
        elif w.relation == "free_window":
            lo, hi = min(rails), max(rails)
            for m, (kind, d, g, s, b) in mt.items():
                for term, other in (("d", s), ("s", d)):
                    node = d if term == "d" else s
                    if node != x:
                        continue
                    exits = (kind == "nmos" and term == "d") or (kind == "pmos" and term == "s")
                    if exits:
                        lo = max(lo, V[other])
                    else:
                        hi = min(hi, V[other])
            windows[x] = (lo, hi)
            V[x] = lo + th[("y", w.y_key)] * (hi - lo)
        else:
            raise AssertionError(w.relation)
    ln = {}
    for m, (kind, d, g, s, b) in mt.items():
        coord = snap.value("device", m, "dc_coord")
        if coord.role == "writer":
            ln[m] = th[("ln_idu", m)]
        else:
            vgs, vds, vsb = terminal_mag(kind, V, d, g, s, b)
            ln[m] = Oracle.ln_idu(kind, vgs, vds, vsb)
    return V, windows, ln


def run_blocks(ctx, theta, upto="widths"):
    """size_and_seal 의 평가 블록 4개를 계약 7절 호출 순서대로 직접 부른다(봉인 전 스냅샷)."""
    from gmid_engine.sizing import dc_columns, dc_currents, dc_lengths, dc_widths
    th = dict(theta)
    snap = dc_currents(ctx.base, tuple(sorted((k, v) for (t, k), v in th.items() if t == "current")))
    snap = dc_lengths(snap, tuple(sorted((k, v) for (t, k), v in th.items() if t == "L")))
    if upto == "lengths":
        return snap
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    snap = dc_columns(snap, items, ctx.fixed_values, ctx.resistor_values, ctx.lut)
    if upto == "columns":
        return snap
    return dc_widths(snap, ctx.lut)


def eval_calls(ctx, theta):
    """평가 블록 4개 호출 목록 ((block, extras), ...) 과 그 결과 스냅샷(봉인 전).
    `calls` 형식은 계약에 적혀 있지 않아 공개 함수 `seal_versions` 가 받는 형식((블록, extras tuple), ...)을 쓴다."""
    from gmid_engine.sizing import dc_columns, dc_currents, dc_lengths, dc_widths
    th = dict(theta)
    cur = tuple(sorted((k, v) for (t, k), v in th.items() if t == "current"))
    ls = tuple(sorted((k, v) for (t, k), v in th.items() if t == "L"))
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    calls = ((dc_currents, (cur,)), (dc_lengths, (ls,)),
             (dc_columns, (items, ctx.fixed_values, ctx.resistor_values, ctx.lut)), (dc_widths, (ctx.lut,)))
    snap = ctx.base
    for blk, ex in calls:
        snap = blk(snap, *ex)
    return snap, calls


def with_tol(ctx, theta):
    from gmid_engine.sizing import dc_tolerances
    snap, calls = eval_calls(ctx, theta)
    return dc_tolerances(snap, ctx.lut), calls


def resistances_of(ctx, theta):
    return tuple(ctx.resistor_values) + tuple(sorted((k, v) for (t, k), v in dict(theta).items()
                                                     if t == "resistance"))


def judge_expect(rows):
    """CONTRACT 6절 judge 의 독립 구현. rows = [(대상, 크기, tol|None, devices, nodes)].
    반환 dict: status, magnitude, tol, margin, devices, nodes, n_checked, n_undefined, worst."""
    def margin(mag, tol):
        return math.inf if tol == 0 else mag / tol
    defined = [r for r in rows if r[2] is not None]
    fails = [r for r in defined if r[1] > r[2]]
    undef = [r for r in rows if r[2] is None]
    if fails:
        status, tgt = "fail", fails
    elif undef:
        status, tgt = "undefined", undef
    else:
        status, tgt = "pass", []
    pool = fails if fails else defined
    out = {"status": status, "n_checked": len(rows), "n_undefined": len(undef),
           "devices": tuple(sorted({d for r in tgt for d in r[3]})),
           "nodes": tuple(sorted({n for r in tgt for n in r[4]}))}
    if pool:
        w = max(pool, key=lambda r: margin(r[1], r[2]))
        best = margin(w[1], w[2])
        # 최대 margin 동률 행들(동률 tie-break 은 계약에 없음 -> 어느 것이든 허용)
        out["ties"] = {r[0]: (r[1], r[2]) for r in pool if margin(r[1], r[2]) == best}
        out.update(magnitude=w[1], tol=w[2], margin=best, worst=w[0])
    else:
        out.update(magnitude=None, tol=None, margin=None, worst=None, ties={})
    return out


def assert_item(item, exp, n, rtol=1e-9, atol=1e-300, check_devices=True, check_nodes=True):
    from gmid_engine.sizing import SealItem
    assert isinstance(item, SealItem) and item.item == n
    assert item.status == exp["status"]
    det = dict(item.detail)
    assert [k for k, _ in item.detail] == sorted(det)
    assert det["n_checked"] == exp["n_checked"]
    assert det["n_undefined"] == exp["n_undefined"]
    if exp["status"] != "pass":
        if check_devices:
            assert item.devices == exp["devices"]
        if check_nodes:
            assert item.nodes == exp["nodes"]
    if exp["status"] == "undefined":
        return
    if exp["magnitude"] is None:
        assert item.magnitude is None and item.margin is None
        return
    assert det["worst"] in exp["ties"], (det["worst"], exp["ties"])
    mag_e, tol_e = exp["ties"][det["worst"]]
    for a, b in ((item.magnitude, mag_e), (item.tol, tol_e)):
        assert rel_close(a, b, rtol, atol), (a, b)
    if math.isinf(exp["margin"]):
        assert math.isinf(item.margin)
    elif exp["status"] == "fail":
        assert rel_close(item.margin, exp["margin"], rtol), (item.margin, exp["margin"])


def node_voltages(snap):
    V = dict(snap.column("node", "dc_rail_v"))
    V.update(dict(snap.column("node", "dc_v")))
    return V


def rref_free(columns, rows):
    """정확 유리수 RREF(열 왼쪽부터 pivot). rows = [{col: coef}]. -> (pivot 열 목록, free 열 목록, {pivot: {free: coef}})."""
    M = [[Fraction(r.get(c, 0)) for c in columns] for r in rows]
    piv = []
    r = 0
    for ci in range(len(columns)):
        p = next((i for i in range(r, len(M)) if M[i][ci] != 0), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        inv = M[r][ci]
        M[r] = [v / inv for v in M[r]]
        for i in range(len(M)):
            if i != r and M[i][ci] != 0:
                f = M[i][ci]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        piv.append(ci)
        r += 1
    free = [c for i, c in enumerate(columns) if i not in piv]
    expr = {}
    for ri, ci in enumerate(piv):
        expr[columns[ci]] = {columns[j]: -M[ri][j] for j in range(len(columns)) if j not in piv and M[ri][j] != 0}
    return [columns[i] for i in piv], free, expr
