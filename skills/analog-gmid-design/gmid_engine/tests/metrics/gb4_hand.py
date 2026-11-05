"""GB4 달성가능성(U9) test 공용 손 입력 -- 피검 함수 소스 미열람, 근거는 계약·설계 문서뿐이다.

근거(oracle 출처):
- 설계 `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md` 0절(N_S)·4절(4.1~4.6),
  `metrics/CONTRACT.md` 10절, `pipeline/CONTRACT.md` 5절, `search/CONTRACT.md` U9 절, `lut/CONTRACT.md` 1.4·4.2·4.4·4.5.
- 이 모듈은 **입력**(해석식 toy LUT npz, 손 LocalInputs/BlockModel, topology·spec JSON)과 독립 계산(oracle (a)·(b))만 둔다.
  피검 함수(curve_checks·block_gain_model_of·row_gains·block_gain_bound·area_lower_bound·edge_costs·dof_report·headroom_bound·
  achievability·count_budget·run_stage_b)를 부르지 않는다.

toy LUT 해석식(구성으로 정답이 정해진 합성 입력, oracle (a)) -- 폭 w_m 슬라이스, 밀도 배율 k:
    ID   = k·(w_m/L)·I0[kind]·exp(f(VGS) + LAM·VDS − A·VS²)
    GM   = ID·f'(VGS)            (gm/ID = f'(VGS) -- 기본 f = B·VGS − C/2·VGS², f' = B − C·VGS)
    GDS  = ID·LAM                (gds/ID = LAM)
    GMBS = ID·2A·VS              (gmb/ID = 2A·VS = −d ln ID / d VS, lut 4.4 GMBS 열 정본)
그래서 LUT 격자 마디에서 x = gm/ID, y = gds/ID, z = gmb/ID 가 닫힌 식이다(metrics 10.3 '소자 파라미터').
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

GRID_M = 1e-8                       # 제조 격자 -> 폭 1e-6 m 슬라이스의 w_key = 100
W_M = 1e-6
W_KEY = 100
B, C, LAM, A = 20.0, 8.0, 0.1, 2.0
I0 = {"nmos": 1e-11, "pmos": 5e-12}
DEVICE_OF = {"nmos": "toyn", "pmos": "toyp"}
SUFFIX = {"nmos": "_n", "pmos": "_p"}
KINDS = ("nmos", "pmos")

# 기본 격자(metrics conftest toy 와 같은 모양: VS 에 음수 마디가 있다 -> gmb/ID < 0 인 마디가 있다)
L_GRID = (1e-6, 2e-6)
VGS_GRID = tuple(round(0.1 * i, 10) for i in range(19))       # 0 .. 1.8
VDS_GRID = tuple(round(0.3 * i, 10) for i in range(7))        # 0 .. 1.8
VS_GRID = (-0.45, 0.0, 0.45, 0.9, 1.35, 1.8)
GRIDS = (L_GRID, VGS_GRID, VDS_GRID, VS_GRID)


def f_default(g):
    return B * g - 0.5 * C * g * g


def fp_default(g):
    return B - C * g


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slice_arrays(kind, grids=GRIDS, w=W_M, density=1.0, f=f_default, fp=fp_default, gmbs=True, vdsat=None,
                 gm_scale_at=()):
    """해석식 슬라이스 배열. vdsat = callable(VGS, VS) -> 값 또는 None(열 없음). gm_scale_at = ((iL, iG, iD, iS, 배율), ...)
    -- 그 격자점의 GM 만 배율을 곱한다(Fritsch–Carlson 위반 칸을 손으로 만든다)."""
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    Lg = gL[:, None, None, None]
    G = gG[None, :, None, None]
    D = gD[None, None, :, None]
    S = gS[None, None, None, :]
    ID = density * (w / Lg) * I0[kind] * np.exp(f(G) + LAM * D - A * S * S)
    GM = ID * fp(G)
    for iL, iG, iD, iS, k in gm_scale_at:
        GM[iL, iG, iD, iS] *= k
    out = {"W": np.float64(w), "L": gL, "VGS": gG, "VDS": gD, "VS": gS, "ID": ID, "GM": GM, "GDS": ID * LAM,
           "VTH": np.full(ID.shape, 0.4), "meta_json": np.str_('{"model_files_sha256": {}}'),
           "corner": np.str_("tt"), "temp_c": np.float64(27.0)}
    if gmbs:
        out["GMBS"] = ID * (2.0 * A * S)
    if vdsat is not None:
        out["VDSAT"] = vdsat(G, S) + np.zeros(ID.shape)
    return out


def write_lut(root, grids=GRIDS, slices=None, f=f_default, fp=fp_default, gmbs=True, vdsat=None, gm_scale_at=None,
              empty_bins=False):
    """toy LUT 를 쓰고 엔진 로더로 읽는다(입력 생성). slices = ((kind, 폭, 밀도 배율), ...) 기본 kind 마다 (폭 1e-6, 1).
    gm_scale_at = {kind: ((iL, iG, iD, iS, 배율), ...)}. -> LutSet."""
    from gmid_engine.lut import LutSpec, load_lut_set
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    slices = slices or tuple((k, W_M, 1.0) for k in KINDS)
    gm_scale_at = dict(gm_scale_at or {})
    entries = []
    seen = set()
    for i, (kind, w, dens) in enumerate(slices):
        p = root / ("s%d_%s.npz" % (i, kind))
        scale = gm_scale_at.get(kind, ()) if kind not in seen else ()          # 그 kind 의 첫 슬라이스에만
        seen.add(kind)
        np.savez(p, **slice_arrays(kind, grids, w, dens, f, fp, gmbs, vdsat, scale))
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": _sha(p)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0)}
    for kind in KINDS:
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
    np.savez(root / "cap.npz", **cap)
    spec = LutSpec(GRID_M, (("nmos", W_M), ("pmos", W_M)), (("toyn", "nmos"), ("toyp", "pmos")),
                   (("nmos", "_n"), ("pmos", "_p")))
    from toy_bins import retrofit_bins as _retro
    _tb = _retro(root, empty=empty_bins)       # empty_bins: bin 블록 없는 합성 모델 파일(빈 지도, 앵커 전용)
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), spec, bin_rule=_tb.bin_rule, pdk_root=_tb.pdk_root)


def memo_of(lut, n=8192):
    from gmid_engine.lut import LutMemo
    return LutMemo(lut, point=n, curve=n, root=n)


# ---------------------------------------------------------------- 닫힌 식 (oracle (a))

def x_of(vgs, fp=fp_default):
    """gm/ID 마디 값."""
    return fp(vgs)


def z_of(vs):
    """gmb/ID 마디 값(GMBS 열 정의)."""
    return 2.0 * A * vs


def db(r):
    return 20.0 * math.log10(r)


def branch_start(fp, vgs_grid=VGS_GRID):
    """곡선 정점 index p(마디 gm/ID 최댓값의 첫 index, lut 3절) -- 해석식 gm/ID 는 (L, VDS, VS) 무관."""
    vals = [fp(v) for v in vgs_grid]
    return vals.index(max(vals))


# ---------------------------------------------------------------- LocalInputs (손)

def local_inputs(devs, *, rails=("gnd", "vdd"), grids=GRIDS, passives=(), orbit=None, l_label=None,
                 basis_rows=None, free=("I0",), fixed=None, cur_rep=None, current_box=None, element_value=None,
                 resistor_box=None, bulk=None):
    """devs = ((이름, kind, d, g, s), ...), passives = ((이름, kind, t0, t1), ...). 기본: 모든 MOS 가 θ 전류 I0 한 원소를
    계수 1 로 읽고(직렬 가지), 궤도는 소자마다 따로, bulk 는 kind 기본 레일(nmos gnd, pmos vdd).

    [U17 ①-b] 필드 값 `LocalInputs`(설계 40 v1.9.1 §2.4.8 D9: dict 칸 -> 이름순 (이름, 값) tuple, memo 칸 없음)를 손으로 만들고, 소비자
    (`block_gain_model_of`·`headroom_bound`, metrics CONTRACT 머리말 'LocalView 를 받는다')가 받는 사전 질의 형식 `.view`(`LocalView`)를 돌려준다.
    구조 색·attach 는 비운다(옛 helper 와 같이 미제공 -- 이름 순서·막다른 넷 없음)."""
    from gmid_engine.metrics import LocalInputs
    kind = {n: k for n, k, *_ in devs}
    pins = {n: {"d": d, "g": g, "s": s} for n, k, d, g, s in devs}
    cls = {n: "mos" for n in kind}
    for n, k, a, b in passives:
        kind[n] = k
        pins[n] = {"t0": a, "t1": b}
        cls[n] = "passive"
    mos_names = [n for n, *_ in devs]

    def tup(d):
        return tuple(sorted(d.items()))

    bulk_map = dict(bulk) if bulk is not None else {n: ("gnd" if kind[n] == "nmos" else "vdd") for n in mos_names}
    stored = LocalInputs(
        kind=tup(kind), pins=tuple((n, tup(p)) for n, p in sorted(pins.items())), cls=tup(cls),
        bulk=tup(bulk_map),
        rails=frozenset(rails),
        orbit=tup(dict(orbit) if orbit is not None else {n: i for i, n in enumerate(mos_names)}),
        l_label=tup(dict(l_label or {})),
        basis_rows=tup(dict(basis_rows) if basis_rows is not None else {n: (("I0", 1.0),) for n in mos_names}),
        free=tuple(free), fixed=tup(dict(fixed or {})),
        cur_rep=tup(dict(cur_rep) if cur_rep is not None else {e: (e, 1) for e in free}),
        current_box=tup(dict(current_box) if current_box is not None else {e: (1e-6, 1e-4) for e in free}),
        element_value=tup(dict(element_value or {})), resistor_box=tup(dict(resistor_box or {})),
        grids=tuple(tuple(float(x) for x in g) for g in grids),
        node_colour=(), device_colour=(), attach=())
    return stored.view


def block_spec(key, members, inputs, outputs, nodes, ground=("gnd", "vdd"), excite=None, passives=(), role="main",
               drive=None, others=()):
    """[UB-1] `others` = 같은 뷰 남의 블록 노드 넷 정렬(칸이 없는 판(base)에서는 칸 없이 만든다 -- 그 판의 단정이 AssertionError 로 빨갛다)."""
    import dataclasses
    from gmid_engine.metrics import BlockSpec
    kw = {"others": tuple(sorted(others))} if others and "others" in {f.name for f in dataclasses.fields(BlockSpec)} else {}
    return BlockSpec(key=tuple(key), role=role, members=tuple(sorted(members)), passives=tuple(sorted(passives)),
                     inputs=tuple(inputs), outputs=tuple(outputs), ground=frozenset(ground),
                     excite=tuple(excite) if excite is not None else tuple((n, 1.0) for n in inputs),
                     nodes=tuple(nodes), drive=drive, **kw)


# ---------------------------------------------------------------- BlockModel (손 -- row_gains·block_gain_bound 입력)

def axis(kind, label, values, continuous=False):
    from gmid_engine.metrics import AxisSpec
    v = np.asarray(values, dtype=float)
    return AxisSpec(kind=kind, label=tuple(label), size=len(v), values=v, continuous=continuous)


def mosl(name, kind, d, g, s, bulk, vgs_axis, l_axis, vds_axis, vsb_axis, current=((-1, 1.0),)):
    from gmid_engine.metrics import MosLocal
    return MosLocal(name=name, kind=kind, d=d, g=g, s=s, bulk=bulk, vgs_axis=vgs_axis, l_axis=l_axis,
                    vds_axis=vds_axis, vsb_axis=vsb_axis, current=tuple(current))


def model(key, nodes, driven, patterns, outputs, mos, axes, res=(), normalized=()):
    from gmid_engine.metrics import BlockModel
    pi = 1
    for a in axes:
        pi *= a.size
    return BlockModel(key=tuple(key), role="main", nodes=tuple(nodes), driven=tuple(driven), patterns=tuple(patterns),
                      outputs=tuple(outputs), mos=tuple(mos), res=tuple(res), axes=tuple(axes), pi=pi,
                      normalized=tuple(normalized))


def cs_model(grids=GRIDS):
    """CS: M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd) 전류원 부하, 같은 전류 1(공통 배율). 축 순서:
    0 vgs(M1), 1 vgs(M2), 2 L(M1), 3 L(M2), 4 vds(M1), 5 vds(M2). gain = x1/(y1 + y2)."""
    gL, gG, gD, _ = grids
    axes = (axis("vgs", ("M1",), gG), axis("vgs", ("M2",), gG), axis("L", ("M1",), gL), axis("L", ("M2",), gL),
            axis("vds", ("M1",), gD), axis("vds", ("M2",), gD))
    mos = (mosl("M1", "nmos", "out", "in", "gnd", "gnd", 0, 2, 4, -1),
           mosl("M2", "pmos", "out", "pb", "vdd", "vdd", 1, 3, 5, -1))
    return model(("out",), ("out",), ("in",), ((("in", 1.0),),), (("out", 1),), mos, axes, normalized=("I0",))


def follower_model(grids=GRIDS):
    """소스 팔로워: M1 nmos (vdd, in, out), bulk gnd, 이상 전류원 부하(컨덕턴스 0). 축: 0 vgs, 1 L, 2 vds, 3 vsb.
    gain = x/(x + y + z)."""
    gL, gG, gD, gS = grids
    axes = (axis("vgs", ("M1",), gG), axis("L", ("M1",), gL), axis("vds", ("M1",), gD), axis("vsb", ("M1",), gS))
    mos = (mosl("M1", "nmos", "vdd", "in", "out", "gnd", 0, 1, 2, 3),)
    return model(("out",), ("out",), ("in",), ((("in", 1.0),),), (("out", 1),), mos, axes, normalized=("I0",))


# ---------------------------------------------------------------- 독립 소신호 풀이 (oracle (b))

def solve_lin(nodes, driven_v, mos, res=()):
    """ω → 0 KCL 독립 풀이. mos = ((d, g, s, b, gm, gds, gmb), ...) -- i(d→s) = gm·vgs + gds·vds + gmb·vbs,
    res = ((a, b, G), ...). nodes 밖 넷은 driven_v(값) 또는 0(교류접지). -> {넷: 전압}."""
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    Y = np.zeros((n, n))
    rhs = np.zeros(n)

    def stamp_vccs(p, q, cp, cq, g):
        """전류 g·(v(cp) − v(cq)) 가 p 에서 q 로(노드 p 에서 나감)."""
        for node, sgn in ((p, 1.0), (q, -1.0)):
            if node not in idx:
                continue
            r = idx[node]
            for c, cs in ((cp, 1.0), (cq, -1.0)):
                if c in idx:
                    Y[r, idx[c]] += sgn * cs * g
                else:
                    rhs[r] -= sgn * cs * g * driven_v.get(c, 0.0)

    for d, g, s, b, gm, gds, gmb in mos:
        stamp_vccs(d, s, g, s, gm)
        stamp_vccs(d, s, d, s, gds)
        stamp_vccs(d, s, b, s, gmb)
    for a, b, G in res:
        stamp_vccs(a, b, a, b, G)
    v = np.linalg.solve(Y, rhs)
    out = dict(driven_v)
    out.update({nd: float(v[i]) for nd, i in idx.items()})
    return out


# ---------------------------------------------------------------- topology / spec JSON (입력)

def mos_e(name, kind, d, g, s):
    return {"name": name, "kind": kind, "drain": d, "gate": g, "source": s}


def two_e(name, kind, a, b):
    return {"name": name, "kind": kind, "terminals": [a, b]}


SE_PORTS = {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}


def topology(name, netlist, ports=None, passives=(), sources=(), rails=("vdd", "gnd"), bias=()):
    ports = ports or SE_PORTS
    d = {"schema_version": "2.0", "topology_name": name, "netlist": list(netlist), "supply_nets": list(rails),
         "ports": {k: {"direction": v[0], "role": v[1]} for k, v in ports.items()},
         "passive_elements": list(passives)}
    if sources:
        d["ideal_sources"] = list(sources)
    if bias:
        d["bias_inputs"] = list(bias)
    return d


SRC = {"kind": "user_spec", "record": "GB4 test fixture (U9 independent tests)", "decided": "2026-10-09"}


def write_case(root, topo_doc, *, supplies=None, elements=(), constraints=(), input_dc_v=None, count_budget=None,
               node_targets=None):
    """topology·spec 를 root 에 쓴다. elements = ((이름, kind, 값 | None(engine)), ...), constraints = ((metric, op, 값), ...).
    count_budget = spec human `structure_count_budget.value`(None 이면 키 없음), node_targets = {넷: V} 선언 노드 목표.
    -> (topology 경로, spec 경로)."""
    import sys
    tests_dir = str(Path(__file__).resolve().parents[1])
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    from gmid_engine.authoring import load_topology
    from metrics.conftest import spec_json
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    tp = root / (topo_doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo_doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    sup = dict(supplies or {"vdd": 1.8, "gnd": 0.0})
    spec = spec_json(td, sup, elements, constraints=tuple((m, op, v, None) for m, op, v in constraints),
                     input_dc_v=input_dc_v)
    if count_budget is not None:
        spec["human"]["structure_count_budget"] = {"value": int(count_budget), "source": SRC}
    for net, v in (node_targets or {}).items():
        spec["human"]["node_voltage_targets_v"][net] = {"value_v": float(v), "source": SRC}
    sp = root / (topo_doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    return tp, sp


def toy_pdk(root):
    """toy PDK 선언(search conftest 의 MIM 포함 선언 -- 제조 격자 1e-8 m, 최소 finger 0.5 µm, MIM 4e-3 F/m²)."""
    import sys
    tests_dir = str(Path(__file__).resolve().parents[1])
    if tests_dir not in sys.path:
        sys.path.insert(0, tests_dir)
    from search.conftest import write_decls_mim
    return write_decls_mim(Path(root))[0]


TOY_MIM_DENSITY = 4.0e-3            # F/m² -- search conftest TOY_CAMIMC_F_PER_UM2 4.0e-15 F/µm² 의 단위 환산(구성 값)
TOY_B_A = GRID_M * 5e-7             # b_A = 제조 격자 × 최소 finger 폭(search 3.7) -- toy 선언 값의 곱


def toy_settings():
    """탐색 실행 설정(입력, 기대값 아님) -- tests/search/u13_hand.build 기본값과 같은 값(평가 예산 40, R 상자 1e2..1e5 Ω, C 상자 1e-13..1e-10 F).
    [U17 ①-b 2차, 사용자 결정 4(2026-10-14)] `run_stage_b(settings=)` 는 필수 인자(기본값 없음)라 단계 B 를 부르는 helper 가 명시한다."""
    from gmid_engine.search import SearchSettings
    return SearchSettings(600.0, 40, (1e2, 1e5), (("front_budget_s", "gb4 test fixture"),), (1e-13, 1e-10))


def stage_ab(root, lut, tp, sp, pdk, diagnostic=False, out="out", settings=None):
    """단계 A -> 단계 B(공개 진입점 두 개를 부르는 입력 helper -- 기대값을 만들지 않는다). `pdk` = 단계 B 의 PDK 선언.
    `settings` = 탐색 실행 설정(None 이면 `toy_settings()` -- 단계 B 에는 늘 명시해 넘긴다).
    [xrun, 사용자 결정 J-1 2026-10-15] run_stage_a 는 PDK 선언·LUT 생성 규칙 선언과 그 경로 인자를 받지 않는다(S0 키에만 쓰이던 인자)."""
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import open_run
    if settings is None:
        settings = toy_settings()
    # [XRUN-F1 card B 규칙 M M-c] 실행 하나 = 이 helper 호출 하나: run_stage_a 와 1:1 인 open_run() 튜플 풀기(쌍을 매개변수로 받지 않는다)
    donors, counters = open_run()
    a = run_stage_a(tp, sp, lut, output_dir=Path(root) / out, donors=donors, counters=counters)
    b = run_stage_b(a, memo_of(lut), pdk, output_dir=Path(root) / out, diagnostic=diagnostic, settings=settings)
    return a, b


def gain_blocks(report):
    g = (report.get("achievability") or {}).get("gain") or {}
    return {tuple(b["key"]): b for b in (g.get("blocks") or [])}


# ---------------------------------------------------------------- Fritsch–Carlson 독립 판정 (lut 1.4 [r5] 식, oracle (b))

def fc_monotone(y0, y1, m0, m1, h):
    b0 = m0 * h
    b2 = m1 * h
    b1 = 3.0 * (y1 - y0) - b0 - b2
    q = b1 * b1 <= b0 * b2
    up = (b0 >= 0) & (b2 >= 0) & ((b1 >= 0) | q)
    dn = (b0 <= 0) & (b2 <= 0) & ((b1 <= 0) | q)
    return up | dn


def curve_counts(arrays):
    """슬라이스 배열 dict -> {축: (칸 수, Hermite 칸 수, 위반 칸 수)} 와 VGS 위반 칸 index 목록. lut 1.4 의 정의를 numpy 로 다시 쓴 것:
    y = ln(clip(ID, 최소 양수)), 기울기 정의 VGS = on_mask((ID>0)&(GM>0)), VDS = (ID>0)&(GDS>0), VS = GMBS/ID 유한·양수,
    기울기 값 VGS = GM/ID, VDS = GDS/ID, VS = −GMBS/ID."""
    ID = np.asarray(arrays["ID"], float)
    GM = np.asarray(arrays["GM"], float)
    GDS = np.asarray(arrays["GDS"], float)
    pos = ID[ID > 0]
    y = np.log(np.clip(ID, pos.min(), None))
    with np.errstate(all="ignore"):
        defs = {"VGS": ((ID > 0) & (GM > 0), GM / ID, 1, np.asarray(arrays["VGS"], float)),
                "VDS": ((ID > 0) & (GDS > 0), GDS / ID, 2, np.asarray(arrays["VDS"], float))}
        if "GMBS" in arrays:
            r = np.where(ID > 0, np.asarray(arrays["GMBS"], float) / ID, np.nan)
            defs["VS"] = (np.isfinite(r) & (r > 0), -r, 3, np.asarray(arrays["VS"], float))
        else:
            defs["VS"] = (np.zeros(ID.shape, bool), np.zeros(ID.shape), 3, np.asarray(arrays["VS"], float))
    out = {}
    viol_vgs = []
    for ax, (ok, m, a, grid) in defs.items():
        n = ID.shape[a]
        sl0 = [slice(None)] * 4
        sl1 = [slice(None)] * 4
        sl0[a] = slice(0, n - 1)
        sl1[a] = slice(1, n)
        sl0, sl1 = tuple(sl0), tuple(sl1)
        hshape = [1, 1, 1, 1]
        hshape[a] = n - 1
        h = np.diff(grid).reshape(hshape)
        herm = ok[sl0] & ok[sl1]
        with np.errstate(all="ignore"):
            mono = fc_monotone(y[sl0], y[sl1], m[sl0], m[sl1], h)
        viol = herm & ~mono
        out[ax] = (int(herm.size), int(herm.sum()), int(viol.sum()))
        if ax == "VGS":
            viol_vgs = [tuple(int(i) for i in t) for t in np.argwhere(viol)]
    return out, viol_vgs
