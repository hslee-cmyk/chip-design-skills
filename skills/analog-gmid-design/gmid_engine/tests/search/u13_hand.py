"""U13(출발 구간·매크로 모델) test 공용 손 입력 -- 근거는 설계 41 §6·§7.5·§5.8, 40 §11 U13·§7.1, search CONTRACT U13 절(주장)뿐이다.

이 모듈은 **입력**(해석식 toy LUT, toy PDK 선언, 손 회로 topology·spec, 단계 A/B 를 거친 공개 산출물 묶음)과 독립 계산(닫힌 식·
독립 MNA·격자 전수)만 둔다. 피검 함수(start_intervals·macro_solve·current_model·dominant_node·iv_*·EvalBudget)로 기대값을 만들지 않는다.

toy LUT 해석식(구성으로 정답이 정해진 합성 입력, oracle (a)) -- metrics/gb4_hand 와 같은 꼴 + VDSAT 열 + 용량 배율:
    ID    = (w_m/L)·I0[kind]·exp(f(VGS) + LAM·VDS − A·VS²),  f = B·VGS − C/2·VGS²
    gm/ID = B − C·VGS = 20 − 8·VGS  (VGS 격자 0..1.8 -> 20 .. 5.6),  gds/ID = LAM = 0.1  -> 진성 이득 gm/gds = (gm/ID)/LAM
    VDSAT = 2/(gm/ID)               (제곱 법칙 관계 VDSAT = 2·ID/gm 을 열로 둔 구성 값)
    CGG   = cap_scale·1e-15 F, CGD = cap_scale·2e-16 F (폭 1 µm 기준, 모든 마디 같은 값)
    f_T   = gm/(2π·CGG·(W/W_ref)) = (gm/ID)·IDu/(2π·CGG·L/W_ref)  (IDu = ID·L/W)
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

TESTS = Path(__file__).resolve().parents[1]
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from metrics.gb4_hand import (  # noqa: E402
    A, B, C, DEVICE_OF, GRID_M, I0, KINDS, LAM, SUFFIX, W_M, f_default, fp_default, memo_of, mos_e, slice_arrays, topology,
    two_e, write_case,
)

L_GRID = (1e-6, 2e-6)
VGS_GRID = tuple(round(0.1 * i, 10) for i in range(19))       # 0 .. 1.8
VDS_GRID = tuple(round(0.3 * i, 10) for i in range(7))        # 0 .. 1.8
VS_GRID = (-0.45, 0.0, 0.45, 0.9, 1.35, 1.8)
GRIDS = (L_GRID, VGS_GRID, VDS_GRID, VS_GRID)
CGG_REF = 1e-15
CGD_REF = 2e-16
GMID_MAX = B                         # gm/ID 정점(VGS = 0)
GMID_MIN = B - C * VGS_GRID[-1]      # 5.6 (VGS = 1.8)


def vdsat_of(gm_id):
    """toy VDSAT 열의 닫힌 식 (구성)."""
    return 2.0 / gm_id


def gm_id_for_vdsat(v):
    """VDSAT(g) ≤ v 의 최소 g = 2/v (VDSAT 는 g 에 대해 감소)."""
    return 2.0 / v


def write_toy_lut(root, cap_scale=1.0, grids=GRIDS):
    """VDSAT 열과 용량 배율이 있는 해석식 toy LUT 를 쓰고 엔진 로더로 읽는다(입력 생성). -> LutSet."""
    from gmid_engine.lut import LutSpec, load_lut_set
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, kind in enumerate(KINDS):
        p = root / ("s%d_%s.npz" % (i, kind))
        arr = slice_arrays(kind, grids, W_M, 1.0, f_default, fp_default, True,
                           vdsat=lambda G, S: 2.0 / fp_default(G))
        np.savez(p, **arr)
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, gS = (np.asarray(g, dtype=float) for g in grids)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"),
           "temp_c": np.float64(27.0)}
    for kind in KINDS:
        cap["CGG" + SUFFIX[kind]] = np.full(shp, CGG_REF * cap_scale)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, CGD_REF * cap_scale)
    np.savez(root / "cap.npz", **cap)
    spec = LutSpec(GRID_M, (("nmos", W_M), ("pmos", W_M)), (("toyn", "nmos"), ("toyp", "pmos")),
                   (("nmos", "_n"), ("pmos", "_p")))
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), spec)


def toy_decls(root):
    """toy PDK 선언 + LUT 규칙 선언(search conftest `write_decls_mim`: 격자 1e-8 m, 최소 finger 0.5 µm, MIM 4e-3 F/m²)."""
    from search.conftest import write_decls_mim
    return write_decls_mim(Path(root))


W_MIN = 5e-7                          # toy PDK 최소 finger 폭(search conftest MINW_UM 0.5 µm)
MIM_DENSITY = 4.0e-3                  # F/m² (search conftest TOY_MIM_DENSITY)


def build(root, lut, decls, topo_doc, *, elements=(), constraints=(), supplies=None, input_dc_v=None, node_targets=None,
          count_budget=10 ** 6, with_ach=True, eval_budget=40, cbounds=(1e-13, 1e-10), rbounds=(1e2, 1e5)):
    """topology·spec -> 단계 A(s1v) -> 단계 B(ach) -> kctx·domain -> SearchContext(s1v=, ach=) 공개 진입점 호출 묶음.
    기대값을 만들지 않는다. -> SimpleNamespace(a, b, s1v, ach, spec, kctx, sctx, start, pdk, rule)."""
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    root = Path(root)
    pdk, rule = decls
    tp, sp = write_case(root, topo_doc, supplies=supplies, elements=elements, constraints=constraints,
                        input_dc_v=input_dc_v, count_budget=count_budget, node_targets=node_targets)
    a = run_stage_a(tp, sp, lut, pdk_decl=pdk, output_dir=root / "out")
    assert a.s1v is not None, a.report.get("stop_reasons")
    b = run_stage_b(a, memo_of(lut), pdk, output_dir=root / "out") if with_ach else None
    ach = b.achievability if b is not None else None
    inputs = dc_inputs_from_spec(a.spec)
    kctx = build_kernel_context(a.s1, inputs, pre_layout_lut_access(memo_of(lut)), l_classes=a.s1v.l_classes)
    settings = SearchSettings(600.0, eval_budget, rbounds, (("front_budget_s", "u13 test fixture"),), cbounds)
    sctx = build_search_context(kctx, a.spec, settings, None, pdk, rule, s1v=a.s1v, ach=ach, code_fp=a.code_fp)
    return SimpleNamespace(a=a, b=b, s1v=a.s1v, ach=ach, spec=a.spec, kctx=kctx, sctx=sctx, start=sctx.start, pdk=pdk,
                           rule=rule, settings=settings, lut=lut)


def rows_by_name(start):
    return {r.device: r for r in start.rows}


# ---------------------------------------------------------------- 프로세스 캐시 (입력 재사용, 메모리·시간 한계)

_TOY = {}
_TOY_CASES = {}
_TOY_CASE_CAP = 24


def toy_env(cap_scale=1.0):
    """(LUT, decls, 작업 폴더) -- cap_scale 마다 한 번."""
    import os
    import tempfile
    if cap_scale not in _TOY:
        root = Path(tempfile.mkdtemp(prefix="u13t", dir=os.environ.get("TEMP") or None))
        _TOY[cap_scale] = SimpleNamespace(lut=write_toy_lut(root / "lut", cap_scale=cap_scale), decls=toy_decls(root / "pdk"),
                                          root=root, n=0)
    return _TOY[cap_scale]


def toy_case(topo_doc, *, cap_scale=1.0, elements=(), constraints=(), fresh=False, **kw):
    """toy 회로 한 건(같은 입력은 한 번만 만든다; fresh=True 면 새로 만든다 -- 결정론 test 용)."""
    key = (cap_scale, json.dumps(topo_doc, sort_keys=True), tuple(elements), tuple(constraints),
           tuple(sorted((k, repr(v)) for k, v in kw.items())))
    if not fresh and key in _TOY_CASES:
        return _TOY_CASES[key]
    env = toy_env(cap_scale)
    env.n += 1
    case = build(env.root / ("c%03d" % env.n), env.lut, env.decls, topo_doc, elements=elements, constraints=constraints, **kw)
    if not fresh:
        if len(_TOY_CASES) >= _TOY_CASE_CAP:
            _TOY_CASES.pop(next(iter(_TOY_CASES)))
        _TOY_CASES[key] = case
    return case


def transfer_view(s1v):
    """gain 제약 전달 뷰 = 블록이 있는 첫 `transfer` 뷰(search CONTRACT U13 iv_context, U9 achievability 와 같은 선택 -- 입력 선택 규칙)."""
    return next(v for v in s1v.views if v.id.startswith("transfer") and v.blocks)


def bound_values(row, source, quantity=None, side=None):
    return [b.value for b in row.sources if b.source == source and (quantity is None or b.quantity == quantity)
            and (side is None or b.side == side)]


def all_inactive(start):
    """회로 전체 + 행별 비활성 (경계 식, 사유) 전부."""
    out = set(start.inactive)
    for r in start.rows:
        out.update(r.inactive_reasons)
    return out


def start_ctx_with(topo_doc, elements, constraints, extra):
    """탐색 문맥 시작 검사(설계 41 §7.2·§6.4-2b 데이터 필수 거부)를 거치지 않고 `extra` 제약이 든 spec 으로 출발 입력 묶음을 만든다
    (단계 A·B 는 잡음·mismatch 데이터를 요구하지 않는다). 정의역과 전류·L·gm/ID 하한은 `extra` 없는 같은 회로의 공개 산출물(입력)이다.
    -> (StartContext, {소자: 전류}, {소자: L}, {소자: gm/ID 하한})."""
    from gmid_engine.pipeline import run_stage_a, run_stage_b
    from gmid_engine.search.iv_context import build_start_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, pre_layout_lut_access
    clean = toy_case(topo_doc, elements=elements, constraints=constraints)
    env = toy_env()
    env.n += 1
    root = env.root / ("c%03d" % env.n)
    tp, sp = write_case(root, topo_doc, elements=elements, constraints=tuple(constraints) + tuple(extra), count_budget=10 ** 6)
    a = run_stage_a(tp, sp, env.lut, pdk_decl=env.decls[0], output_dir=root / "out")
    assert a.s1v is not None, a.report.get("stop_reasons")
    b = run_stage_b(a, memo_of(env.lut), env.decls[0], output_dir=root / "out")
    kctx = build_kernel_context(a.s1, dc_inputs_from_spec(a.spec), pre_layout_lut_access(memo_of(env.lut)),
                                l_classes=a.s1v.l_classes)
    ctx = build_start_context(a.s1v, b.achievability, kctx, a.spec, env.decls[0], clean.sctx.domain)
    rows = rows_by_name(clean.start)
    return (ctx, {d: r.i_start for d, r in rows.items()}, {d: r.l_chosen for d, r in rows.items()},
            {d: r.gm_id_lo for d, r in rows.items()})


# ---------------------------------------------------------------- 손 회로

def cs_chain(n, name=None, ren=None):
    """n 단 CS 사슬: 단 k = nmos Mk_n (x_k, x_{k-1}, gnd) + pmos Mk_p (x_k, pb_k, vdd) 전류원 부하, x_0 = in, x_n = out.
    ren = 이름 치환 표(원소·넷)."""
    r = (ren or {}).get
    nets = ["in"] + ["n%d" % k for k in range(1, n)] + ["out"]
    devs, bias = [], []
    for k in range(1, n + 1):
        devs.append(mos_e(r("MN%d" % k, "MN%d" % k), "nmos", r(nets[k], nets[k]), r(nets[k - 1], nets[k - 1]), "gnd"))
        devs.append(mos_e(r("MP%d" % k, "MP%d" % k), "pmos", r(nets[k], nets[k]), r("pb%d" % k, "pb%d" % k), "vdd"))
        bias.append(r("pb%d" % k, "pb%d" % k))
    caps = [two_e(r("C%d" % k, "C%d" % k), "capacitor", r(nets[k], nets[k]), "gnd") for k in range(1, n + 1)]
    ports = {r("in", "in"): ("input", "single_ended_input"), r("out", "out"): ("output", "single_ended_output")}
    return topology(name or "u13cs%d" % n, devs, ports=ports, passives=caps, bias=bias)


def cascode_cs(name="u13casc", pmos_cascode=False):
    """CS + nmos 캐스코드: M1 nmos (x, in, gnd) + M2 nmos (out, vb, x) + [pmos 캐스코드 M4 (out, pc, y) + M3 pmos (y, pb, vdd)
    | M3 pmos (out, pb, vdd)] + CL (out, gnd). 극점 노드 x(M2 source = 낮은 임피던스 단자)·out(출력 포트)."""
    devs = [mos_e("M1", "nmos", "x", "in", "gnd"), mos_e("M2", "nmos", "out", "vb", "x")]
    bias = ["vb", "pb"]
    if pmos_cascode:
        devs += [mos_e("M4", "pmos", "out", "pc", "y"), mos_e("M3", "pmos", "y", "pb", "vdd")]
        bias.append("pc")
    else:
        devs.append(mos_e("M3", "pmos", "out", "pb", "vdd"))
    return topology(name, devs, passives=[two_e("CL", "capacitor", "out", "gnd")], bias=bias)


def miller_two_stage(name="u13mil"):
    """2단 CS 사슬 + Miller 커패시터 Cc (n1, out) + 부하 CL (out, gnd)."""
    d = cs_chain(2, name=name)
    d["passive_elements"] = [two_e("Cc", "capacitor", "n1", "out"), two_e("CL", "capacitor", "out", "gnd")]
    return d


def cs_follower(name="u13fol"):
    """CS(MN1 nmos (n1, in, gnd) + MP1 pmos (n1, pb, vdd)) -> 소스 팔로워 MF nmos (vdd, n1, out) + 전류 싱크 MS nmos (out, nb, gnd), CL (out, gnd).
    출력 포트 out 은 팔로워 소스(낮은 임피던스) 노드다."""
    devs = [mos_e("MN1", "nmos", "n1", "in", "gnd"), mos_e("MP1", "pmos", "n1", "pb", "vdd"),
            mos_e("MF", "nmos", "vdd", "n1", "out"), mos_e("MS", "nmos", "out", "nb", "gnd")]
    return topology(name, devs, passives=[two_e("CL", "capacitor", "out", "gnd")], bias=["pb", "nb"])


# ---------------------------------------------------------------- 독립 계산 (oracle (a)·(b))

def chain_response(gms, caps, a_intr, f):
    """n 단 이상 VCCS 사슬의 닫힌 식: H(jω) = Π_k gm_k / (G_k + jωC_k), G_k = gm_k / A_k. -> 복소수."""
    w = 2.0 * math.pi * f
    h = 1.0 + 0j
    for gm, c, a in zip(gms, caps, a_intr):
        h *= gm / (gm / a + 1j * w * c)
    return h


def chain_poles_hz(gms, caps, a_intr):
    """극점 = G_k / (2π C_k) 오름차순."""
    return sorted(gm / a / (2.0 * math.pi * c) for gm, c, a in zip(gms, caps, a_intr))


def chain_pm_deg(gms, caps, a_intr, f):
    """교차 주파수 f 에서 위상 여유 = 180 − Σ atan(ω/p_k) (T(0) 위상 기준, 극점만 있는 사슬)."""
    w = 2.0 * math.pi * f
    return 180.0 - sum(math.degrees(math.atan(w * c * a / gm)) for gm, c, a in zip(gms, caps, a_intr))


def _golden(f, lo, hi, n=200):
    """단봉 f 의 [lo, hi] 최소점(황금 분할, 독립 구현)."""
    r = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = lo, hi
    c, d = b - r * (b - a), a + r * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(n):
        if fc <= fd:
            b, d, fd = d, c, fc
            c = b - r * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + r * (b - a)
            fd = f(d)
    return (a + b) / 2.0


def chain_min_current(caps, g, a_intr, gbw, pm):
    """oracle (b) -- 같은 문제를 다른 방법으로 푼다: n(2·3) 단 이상 VCCS 사슬에서
    |H(jω_GBW)| = 1, PM(ω_GBW) ≥ pm, 주극점을 뺀 극점 ≥ ω_GBW·tan(pm) 를 지키는 Σ gm_k/g_k 최소(전원 전류 합 = 단마다 가지 전류).
    변수 u_k = ω/p_k (p_k = gm_k/(A_k C_k) 이므로 gm_k = ω A_k C_k / u_k). 주극점 단 d 를 전수로 고르고, 비주극점 u 는 (0, cot pm] 격자 + 황금 분할,
    주극점 u_d 는 이득 식 Π(1 + u_k²) = Π A_k² 의 닫힌 해. -> (최소 목적, gm 목록, 주극점 단 index)."""
    n = len(caps)
    w = 2.0 * math.pi * gbw
    cot = 1.0 / math.tan(math.radians(pm))
    big = math.prod(a * a for a in a_intr)

    def solve(d, us):
        """비주극점 u 목록 -> (목적, gm) 또는 None(불가능)."""
        prod = math.prod(1.0 + u * u for u in us)
        ud2 = big / prod - 1.0
        if ud2 <= 0:
            return None
        u = list(us)
        u.insert(d, math.sqrt(ud2))
        phase = sum(math.degrees(math.atan(x)) for x in u)
        if 180.0 - phase < pm - 1e-12:
            return None
        gms = [w * a_intr[k] * caps[k] / u[k] for k in range(n)]
        return sum(gms[k] / g[k] for k in range(n)), gms

    best = None
    for d in range(n):
        if n == 2:
            def obj(x, d=d):
                r = solve(d, [x])
                return math.inf if r is None else r[0]
            xs = [cot * (i + 1) / 4000.0 for i in range(4000)]
        else:
            def inner(x, d=d):
                """두 번째 비주극점 u_b: 가능한 최대(목적이 u 에 대해 감소) -- PM 경계의 이분법."""
                lo, hi = 1e-12, cot
                if solve(d, [x, lo]) is None:
                    return None
                if solve(d, [x, hi]) is not None:
                    return hi
                for _ in range(200):
                    mid = 0.5 * (lo + hi)
                    if solve(d, [x, mid]) is not None:
                        lo = mid
                    else:
                        hi = mid
                return lo

            def obj(x, d=d, inner=inner):
                y = inner(x)
                if y is None:
                    return math.inf
                r = solve(d, [x, y])
                return math.inf if r is None else r[0]
            xs = [cot * (i + 1) / 400.0 for i in range(400)]
        vals = [obj(x) for x in xs]
        i = min(range(len(xs)), key=vals.__getitem__)
        lo, hi = xs[max(i - 1, 0)], xs[min(i + 1, len(xs) - 1)]
        x = _golden(obj, lo, hi) if hi > lo else xs[i]
        xbest = x if obj(x) <= vals[i] else xs[i]
        if n == 2:
            r = solve(d, [xbest])
        else:
            r = solve(d, [xbest, inner(xbest)])
        if r is not None and (best is None or r[0] < best[0]):
            best = (r[0], r[1], d)
    return best
