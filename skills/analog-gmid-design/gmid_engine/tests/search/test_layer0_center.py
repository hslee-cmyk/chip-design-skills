"""CONTRACT 3.21 [r5·r5b·r5c·r8] `layer0_start(sctx, origin=()) -> Layer0Result` + 5절 I-13~I-18.

기대값은 이 파일이 계약 문장으로 독립 계산한다(피검 함수로 만들지 않는다):
- 1 상자 중심: ln_idu 상자(npz 포락선, conftest `expect_ln_idu_bounds`) 중점, y = 0.5, L 칸 = ln 좌표 중점에 가장 가까운 칸
  (L 격자 (1, 1.8, 2.6, 4) µm -- ln 중점 2 µm 는 1.8, 선형 중점 2.5 µm 는 2.6 이라 둘이 갈린다).
- 2 전류 중심: minimax |ln(I/I_c)| 의 닫힌 해(행이 단일항이면 z* = (ln I_c 최소 + 최대)/2, u* = 반폭), I_c = √(I_off·I_max)
  (conftest `expect_box`).
- 3 Halton·hit-and-run: 이 파일의 근기 역순 `phi`·소수 열과 선형 전류 좌표의 열린 현 걸음을 S3 evals 줄(origin probe k)과 대조.
  ln_idu 시험 하한 = [r9] max(칸 전도 하한, 칸 정점 하한)(conftest `conduction_floor`·`peak_floor`, 모든 쓰기 소자 -- 3.21 3 r8 의
  `ln_idu_floors` 위임 + 3.22 r9 전도 하한).
- 3b 수리: 디스크 실패 줄(3.10 3 -- 같은 schema·code 의 ok 아닌 줄은 커널 0 실패)로 위반 크기·h 를 정한 `no_root_in_window` 를 시험
  점에 심고, ⌈log2(|끝 − x|/res)⌉ bisection 의 평가 좌표를 계산한다(res = tol_V·gm/ID 최대, tol_V = 끝 |h| 최솟값/margin).
- 4·5 최대-최소: t = 출발점 봉인 보고 항목 중 margin 유한한 i 의 min(1 − margin_i), 경성 행 ≥ 0.
"""
import json
import math
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from gmid_engine.search import (
    ACCEPTED_STATUSES,
    ROW_SEAL_ITEM,
    SOURCE_LAYER0,
    STATUS_FAILED,
    Layer0Result,
    cone_rows,
    evaluate,
    layer0_start,
    start_points,
)

from .conftest import schema_of  # [U17 ①-b] graph/kernel 필드 읽기
from .conftest import (
    R4_VDS,
    R4_VGS,
    R4_VS,
    build_case,
    circuit_c,
    conduction_floor,
    expect_box,
    expect_ln_idu_bounds,
    expected_floor,
    mos,
    on_mask,
    peak_floor,
    r4_arrays,
    tol_v_at,
    topo,
    write_r4_lut,
)

L4 = (1e-6, 1.8e-6, 2.6e-6, 4e-6)
GRIDS4 = (L4, R4_VGS, R4_VDS, R4_VS)
SS = (("gain_ss_db", ">=", 10.0, None),)
FIELDS = ("start", "t", "hard_ok", "stop", "centre_u", "start_status", "start_failure", "iterations", "restarts", "aborts",
          "frozen", "kernel_calls", "rows", "probes", "origin_point", "repairs")


@pytest.fixture(scope="module")
def lut4(tmp_path_factory):
    return write_r4_lut(tmp_path_factory.mktemp("l0_lut4"), grids=GRIDS4)


@pytest.fixture(scope="module")
def lut2(tmp_path_factory):
    return write_r4_lut(tmp_path_factory.mktemp("l0_lut2"))


@pytest.fixture
def roots():
    made = []

    def new():
        d = tempfile.mkdtemp(prefix="l0", dir=os.environ.get("TEMP") or None)
        made.append(d)
        return d
    yield new
    for d in made:
        shutil.rmtree(d, ignore_errors=True)


def circuit_window():
    """빈 창 회로(sizing conftest D): MA nmos (x, vdd, vdd) -> x ≥ V(vdd), MB pmos (x, gnd, gnd) -> x ≤ V(gnd), MC nmos (x, inp, gnd).
    모든 평가가 empty_window 로 실패(위반 크기 없음 -- 수리 대상 아님). 자유 전류 MA·MB, 원뿔 행 MC = MB − MA(차 전류)."""
    return topo("hand_empty_window",
                [mos("MA", "nmos", "x", "vdd", "vdd"), mos("MB", "pmos", "x", "gnd", "gnd"),
                 mos("MC", "nmos", "x", "inp", "gnd")],
                {"inp": ("input", "single_ended_input"), "x": ("output", "single_ended_output")})


def circuit_follower():
    """nmos 만: M1 (vdd, in, x) 소스 추종 + M2 (x, nb, gnd) 전류 싱크 -> 원뿔 행 둘 다 같은 nmos 원천 단일항(I-14)."""
    return topo("hand_nfollow", [mos("M1", "nmos", "vdd", "in", "x"), mos("M2", "nmos", "x", "nb", "gnd")],
                {"in": ("input", "single_ended_input"), "x": ("output", "single_ended_output")},
                bias=["nb"])                                  # nb: M2 gate 에만 (authoring 9절 입력 선언)


# ---------------------------------------------------------------- 독립 계산 도구

def primes(n):
    out, k = [], 2
    while len(out) < n:
        if all(k % p for p in out):
            out.append(k)
        k += 1
    return out


def phi(b, k):
    """근기 역순(radical inverse), 스크램블 없음."""
    f, r = 1.0, 0.0
    while k > 0:
        f /= b
        r += f * (k % b)
        k //= b
    return r


def lines_of(root, ctx_fp):
    p = Path(root) / ctx_fp / "evals.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def th_of(line):
    return {tuple(k): v for k, v in line["theta"]}


def arrays(kind, grids=GRIDS4):
    return r4_arrays(kind, grids=grids)


def box_centre_ln(kind, grids=GRIDS4):
    a = arrays(kind, grids)
    i_off, i_max = expect_box(a, [a])
    return 0.5 * (math.log(i_off) + math.log(i_max))


def write_failures(root, ctx_fp, lines):
    d = Path(root) / ctx_fp
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "evals.jsonl", "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(json.dumps(ln) + "\n")


def as_failure(line, fail):
    """엔진이 쓴 evals 줄(같은 schema·code·cells·θ hex)을 ok 아닌 줄로 -- 3.9/3.10 3 디스크 실패 적중 입력."""
    d = {k: v for k, v in line.items() if k not in ("objectives", "power_resolution_w", "snapshot_fp")}
    d.update(ok=False, status=STATUS_FAILED, fail=fail, constraints=[], unmeasured=[])
    return d


def no_root(dev, node, margin, h_lo, h_hi):
    return {"class": "SEAL_VIOLATION", "devices": [dev], "margin": margin,
            "detail": {"reason": "no_root_in_window", "node": node, "lo": 0.0, "hi": 1.8, "h_lo": h_lo, "h_hi": h_hi,
                       "item": 7, "bounds": ["vds_axis", "rail"]}}


def empty_window(node):
    return {"class": "SEAL_VIOLATION", "devices": [], "margin": None,
            "detail": {"reason": "empty_window", "node": node, "lo": 1.8, "hi": 0.0, "item": 7, "constraints": 3}}


def run_l0(tmp, topo_doc, lut, root, eval_budget=40, inject=(), constraints=()):
    """root 에 실패 줄을 미리 쓴 뒤 새 컨텍스트로 layer0_start. -> (case, result, 이 실행이 새로 쓴 줄)."""
    if inject:
        probe = build_case(Path(tmp) / "fp", topo_doc, lut, eval_budget=eval_budget, constraints=constraints)
        write_failures(root, probe.sctx.context_fp, inject)
    case = build_case(tmp, topo_doc, lut, eval_budget=eval_budget, archive_root=root, constraints=constraints)
    r = layer0_start(case.sctx)
    return case, r, lines_of(root, case.sctx.context_fp)[len(inject):]


# ---------------------------------------------------------------- 형식

def test_result_fields_and_constants(tmp_path, lut4, roots):
    _, r, _ = run_l0(tmp_path, circuit_c(), lut4, roots())
    assert isinstance(r, Layer0Result)
    for f in FIELDS:
        assert hasattr(r, f), f
    assert SOURCE_LAYER0 == "layer0"
    assert r.start is not None and r.start.start_id == "layer0" and r.start.source == SOURCE_LAYER0
    assert all(isinstance(x, str) and x.startswith(ROW_SEAL_ITEM + ":") for x in r.rows)


# ---------------------------------------------------------------- 1·2 상자 중심·전류 중심

def test_centre_point_box_centre_and_current_centre(tmp_path, lut4, roots):
    case, r, lines = run_l0(tmp_path, circuit_c(), lut4, roots())
    s = case.sctx
    c = lines[0]
    assert c["origin"] == {"stage": "layer0"} and c["seq"] == min(x["seq"] for x in lines)
    th = th_of(c)
    # L 칸: ln 좌표 중점(2 µm)에 가장 가까운 칸 = 1.8 µm(index 1) -- 선형 중점 2.5 µm 이면 2.6 µm 였다
    lnmid = 0.5 * (math.log(min(L4)) + math.log(max(L4)))
    j = min(range(len(L4)), key=lambda i: (abs(math.log(L4[i]) - lnmid), i))
    assert j == 1
    assert th[("L", "M1")] == L4[j] and th[("L", "M2")] == L4[j]
    assert tuple(c["cells"]) == (j, j)
    for m, kind in (("M1", "nmos"), ("M2", "pmos")):
        lo, hi = expect_ln_idu_bounds(arrays(kind))
        assert math.isclose(th[("ln_idu", m)], 0.5 * (lo + hi), rel_tol=1e-12)
    assert th[("y", "out")] == 0.5
    # 전류 중심: 행 M1(nmos)·M2(pmos) 모두 I = e^z 단일항 -> z* = 두 I_c 의 ln 중점, u* = |ln I_c,n − ln I_c,p| / 2
    zn, zp = box_centre_ln("nmos"), box_centre_ln("pmos")
    z = math.log(th[("current", "M2")])
    assert abs(z - 0.5 * (zn + zp)) <= 1e-5
    assert abs(r.centre_u - 0.5 * abs(zn - zp)) <= 1e-5 and r.centre_u > 0.1
    assert all(row.c > 0 for row in cone_rows(schema_of(s.dc), tuple(sorted(th.items()))))


def test_same_kind_single_term_cone_centre_is_box_centre(tmp_path, lut4, roots):
    """I-14: 원뿔 행이 모두 같은 kind(nmos) 원천의 계수 1 단일항 -> u = 0, θ 전류 = 상자 기하 중심 √(I_off·I_max)."""
    case, r, lines = run_l0(tmp_path, circuit_follower(), lut4, roots())
    cur = [k for k in schema_of(case.dc).components if k[0] == "current"]
    assert len(cur) == 1
    th = th_of(lines[0])
    assert abs(r.centre_u) <= 1e-9
    assert math.isclose(math.log(th[cur[0]]), box_centre_ln("nmos"), rel_tol=0, abs_tol=1e-9)


# ---------------------------------------------------------------- 3 Halton·hit-and-run (I-17·I-18)

def cell_floor_of(case, lut, kind, cell):
    """[r9] 층 0 시험·수리의 ln_idu 하한(모든 쓰기 소자, start 없음) = max(칸 전도 하한, 칸 정점 하한) -- 3.21 3(r8 `ln_idu_floors`
    위임) + 3.22 r9. 둘 다 없으면 None. tol 입력 = lut 공개 `tol_v_table`(conftest `tol_v_at`)."""
    tol_at = tol_v_at(lut, kind, dict(case.acc.w_keys)[kind])
    return expected_floor(conduction_floor(arrays(kind), cell[0], cell[1], tol_at), peak_floor(arrays(kind), *cell))


def _expected_probes(case, centre_line, ks, lut):
    """3 의 시험 점 독립 계산: 변수 i 는 i 번째 소수, 마지막 소수 = 걸음 비율. ln_idu 하한 = [r9] max(전도, 정점)(모든 쓰기 소자)."""
    s = case.sctx
    V = s.domain.variables
    P = primes(len(V) + 1)
    cone = dict(schema_of(s.dc).current_cone)
    cidx = [i for i, v in enumerate(V) if v.component[0] == "current"]
    pos = {V[i].component[1]: n for n, i in enumerate(cidx)}
    centre = th_of(centre_line)
    cells = dict(zip([m for m, _ in s.domain.l_cells], centre_line["cells"]))
    lcell = dict(s.domain.l_cells)
    kinds = {e["name"]: e["kind"] for e in json.loads(json.dumps(case.td_netlist))}
    p = [centre[V[i].component] for i in cidx]
    floors = {}
    for v in V:
        if v.component[0] == "ln_idu":
            key = v.component[1]
            floors[key] = cell_floor_of(case, lut, kinds[key], lcell[key][cells[key]])
    out = {}
    for k in ks:
        d = [2 * phi(P[i], k) - 1 for i in cidx]
        tlo, thi = -math.inf, math.inf
        for n, i in enumerate(cidx):
            lo, hi = math.exp(V[i].lo), math.exp(V[i].hi)
            if d[n] > 0:
                tlo, thi = max(tlo, (lo - p[n]) / d[n]), min(thi, (hi - p[n]) / d[n])
            elif d[n] < 0:
                tlo, thi = max(tlo, (hi - p[n]) / d[n]), min(thi, (lo - p[n]) / d[n])
        for _, terms in cone.items():
            a = sum(t.num / t.den * p[pos[t.source]] for t in terms)
            b = sum(t.num / t.den * d[pos[t.source]] for t in terms)
            if b > 0:
                tlo = max(tlo, -a / b)
            elif b < 0:
                thi = min(thi, -a / b)
        if tlo < thi:
            ts = tlo + phi(P[-1], k) * (thi - tlo)
            p = [pj + ts * dj for pj, dj in zip(p, d)]
        th = {}
        for i, v in enumerate(V):
            t, key = v.component
            if t == "current":
                th[v.component] = p[cidx.index(i)]
            elif t == "ln_idu":
                lo2 = floors[key]
                lo2 = lo2 if lo2 is not None and v.lo < lo2 < v.hi else v.lo
                th[v.component] = lo2 + phi(P[i], k) * (v.hi - lo2)
            else:
                th[v.component] = v.lo + phi(P[i], k) * (v.hi - v.lo)
        out[k] = th
    return out


def _attach_netlist(case, topo_doc):
    case.td_netlist = topo_doc["netlist"]
    case.td_doc = topo_doc
    return case


def test_halton_hit_and_run_probe_points(tmp_path, lut4, roots):
    """중심 실패(빈 창) -> 시험 k = 1..E_B−1. 좌표 = I-17 식, θ 전류 = 원뿔 안 hit-and-run(I-18): 원뿔 밖 평가 0, 모든 시험 점 원뿔 안,
    ln_idu 는 칸 정점 하한 위. 평가 예산 E_B 에서 멈춘다."""
    eb = 30
    topo_doc = circuit_window()
    case, r, lines = run_l0(tmp_path, topo_doc, lut4, roots(), eval_budget=eb)
    _attach_netlist(case, topo_doc)
    s = case.sctx
    assert r.start is None and r.origin_point is None and r.repairs == ()
    assert r.start_status == STATUS_FAILED and dict(r.start_failure.detail)["reason"] == "empty_window"
    assert r.stop == "start_empty_window+probe_eval_budget"
    assert r.probes == eb - 1 and r.kernel_calls == eb == len(lines)
    cnt = dict(s.counters)
    assert cnt["kernel_calls"] == eb and cnt["outside_domain"] == 0 and cnt["recompute_same_key"] == 0
    assert len({tuple(x["theta_hex"]) for x in lines}) == len(lines)            # 커널 수 = 고유 키
    assert [x["origin"] for x in lines] == [{"stage": "layer0"}] + [{"stage": "layer0", "probe": k} for k in range(1, eb)]
    exp = _expected_probes(case, lines[0], range(1, eb), lut4)
    mc_cell = dict(s.domain.l_cells)["MC"][lines[0]["cells"][[m for m, _ in s.domain.l_cells].index("MC")]]
    assert cell_floor_of(case, lut4, "nmos", mc_cell) > peak_floor(arrays("nmos"), *mc_cell)   # [r9] 비공허: 전도 하한이 이긴다
    for ln in lines[1:]:
        k = ln["origin"]["probe"]
        got = th_of(ln)
        for comp, want in exp[k].items():
            assert math.isclose(got[comp], want, rel_tol=1e-9), (k, comp, got[comp], want)
        assert tuple(ln["cells"]) == tuple(lines[0]["cells"])
        assert all(row.c > 0 for row in cone_rows(schema_of(s.dc), tuple(sorted(got.items())))), k
    # 비공허 대조: 같은 Halton 을 전류 상자에 독립으로 쓰면(r5 초안) 원뿔 MC = MB − MA 밖 점이 나온다
    V = s.domain.variables
    P = primes(len(V) + 1)
    ia = [i for i, v in enumerate(V) if v.component == ("current", "MA")][0]
    ib = [i for i, v in enumerate(V) if v.component == ("current", "MB")][0]
    outside = 0
    for k in range(1, eb):
        xa = math.exp(V[ia].lo + phi(P[ia], k) * (V[ia].hi - V[ia].lo))
        xb = math.exp(V[ib].lo + phi(P[ib], k) * (V[ib].hi - V[ib].lo))
        outside += xb - xa <= 0
    assert outside >= 1


def test_single_current_first_probe_direction_zero(tmp_path, lut4, roots):
    """θ 전류 변수 하나(변수 0, 기저 2): k = 1 이면 d = 2·φ_2(1) − 1 = 0 -- 걸음이 없어 시험 1 의 θ 전류 = 전류 중심 그대로이고
    모든 시험 점은 상자 안 유한 값이다(3.21 3 'θ 전류 = p(상자로 자름)', I-18). 중심은 디스크 실패 줄로 실패시킨다."""
    root0 = roots()
    case0, _, lines0 = run_l0(tmp_path / "a", circuit_c(), lut4, root0)
    centre = lines0[0]
    root = roots()
    case, r, lines = run_l0(tmp_path / "b", circuit_c(), lut4, root, eval_budget=3,
                            inject=[as_failure(centre, empty_window("out"))])
    s = case.sctx
    assert dict(s.counters)["disk_hits"] >= 1
    v = [x for x in s.domain.variables if x.component[0] == "current"][0]
    assert lines and lines[0]["origin"] == {"stage": "layer0", "probe": 1}
    assert th_of(lines[0])[v.component] == th_of(centre)[v.component]
    for ln in lines:
        if "probe" in ln["origin"]:
            x = th_of(ln)[v.component]
            assert math.isfinite(x) and math.exp(v.lo) * (1 - 1e-12) <= x <= math.exp(v.hi) * (1 + 1e-12)


# ---------------------------------------------------------------- 3b 1단계 수리 (bisection)

def _window_with_probe_failures(tmp_path, lut4, roots, fails):
    """빈 창 회로: 1차 실행으로 시험 점 줄을 얻고, fails = {k: 실패 dict} 를 그 시험 점의 디스크 실패로 심어 다시 실행."""
    topo_doc = circuit_window()
    _, _, base = run_l0(tmp_path / "a", topo_doc, lut4, roots(), eval_budget=8)
    by_k = {ln["origin"].get("probe"): ln for ln in base}
    inject = [as_failure(by_k[k], f) for k, f in sorted(fails.items())]
    case, r, lines = run_l0(tmp_path / "b", topo_doc, lut4, roots(), eval_budget=60, inject=inject)
    return _attach_netlist(case, topo_doc), r, lines, by_k


def test_repair_bisection_count_and_points(tmp_path, lut4, roots):
    """묶음 = n + 1 = 5 시험. 수리 가능 실패 둘(시험 2 margin 3, 시험 4 margin 2) 중 margin 최소 = 시험 4 에서 MC 좌표 수리:
    끝 = 칸 하한([r9] max(전도, 정점) -- 빈 창 실패 = 'MC 의 같은 실패' 아님 -> 통과 끝), 이어 ⌈log2(|끝 − x|/res)⌉ 번 bisection, 중점은 모두
    통과 쪽(빈 창)이라 좌표 = x + (끝 − x)/2^j. 마지막 점도 빈 창 실패(위반 크기 없음) -> 사슬 끝, 시험 6 으로 이어진다."""
    h_lo, h_hi, margin = -0.004, 0.01, 2.0
    fails = {2: no_root("MC", "inp", 3.0, -0.003, 0.02), 4: no_root("MC", "inp", margin, h_lo, h_hi)}
    case, r, lines, by_k = _window_with_probe_failures(tmp_path, lut4, roots, fails)
    s = case.sctx
    seq_of = [ln["origin"].get("probe") for ln in lines]
    assert seq_of[:4] == [None, 1, 3, 5]                   # 중심 + 커널 시험 1·3·5 (2·4 는 디스크 실패, 커널 0)
    i5 = seq_of.index(5)
    x_th = th_of(by_k[4])
    comp = ("ln_idu", "MC")
    x = x_th[comp]
    lcell = dict(s.domain.l_cells)["MC"][by_k[4]["cells"][[m for m, _ in s.domain.l_cells].index("MC")]]
    end = cell_floor_of(case, lut4, "nmos", lcell)
    assert end > peak_floor(arrays("nmos"), *lcell)           # [r9] 비공허: 이 LUT 에서는 전도 하한이 끝을 정한다
    v = [vv for vv in s.domain.variables if vv.component == comp][0]
    assert v.lo < end < v.hi and end < x
    a = arrays("nmos")
    m = on_mask(a)
    gmid_max = float((a["GM"][m] / a["ID"][m]).max())
    res = (min(abs(h_lo), abs(h_hi)) / margin) * gmid_max
    nb = 0 if abs(end - x) <= res else math.ceil(math.log2(abs(end - x) / res))
    assert nb >= 3
    rep = lines[i5 + 1:i5 + 2 + nb]
    assert len(rep) == 1 + nb
    want = [end]
    lo_fail, hi_pass = x, end
    for _ in range(nb):
        mid = 0.5 * (lo_fail + hi_pass)
        want.append(mid)
        hi_pass = mid
    for ln, w in zip(rep, want):
        got = th_of(ln)
        assert math.isclose(got[comp], w, rel_tol=1e-12, abs_tol=1e-12), (got[comp], w)
        assert {k: vv for k, vv in got.items() if k != comp} == {k: vv for k, vv in x_th.items() if k != comp}
        assert "probe" not in ln["origin"] or ln["origin"]["probe"] == 5
    nxt = lines[i5 + 2 + nb]
    assert nxt["origin"].get("probe") == 6                  # 사슬 끝(빈 창 = 위반 크기 없음) -> 다음 시험
    # 시험 2(margin 3)의 좌표는 수리되지 않았다
    x2 = th_of(by_k[2])
    assert not any(th_of(ln) != x2 and {k: vv for k, vv in th_of(ln).items() if k != comp}
                   == {k: vv for k, vv in x2.items() if k != comp} for ln in lines)
    assert dict(s.counters)["kernel_calls"] == len(lines) == len({tuple(ln["theta_hex"]) for ln in lines})


def test_no_repair_without_finite_window_ends(tmp_path, lut4, roots):
    """h 끝이 무한이면 위반 크기 없음 -> 수리하지 않는다: 시험 5 다음 줄이 곧 시험 6."""
    fails = {2: no_root("MC", "inp", 3.0, -0.003, math.inf), 4: no_root("MC", "inp", 2.0, -math.inf, 0.01)}
    _, r, lines, _ = _window_with_probe_failures(tmp_path, lut4, roots, fails)
    seq_of = [ln["origin"].get("probe") for ln in lines]
    i5 = seq_of.index(5)
    assert seq_of[i5 + 1] == 6
    assert r.repairs == () or all(len(x) == 0 for x in r.repairs)


# ---------------------------------------------------------------- 4·5 최대-최소, I-13·I-15·I-16

def _min_s(ev):
    vals = [(it.item, 1.0 - it.margin) for it in ev.evaluation.report.items
            if it.margin is not None and math.isfinite(it.margin)]
    return sorted(vals)


def _hard_rows(ev):
    return [c for c in ev.constraints if c.name.startswith("w_min:") or c.name.startswith("inversion_floor:")] + \
        list(ev.cone)


def test_maxmin_t_rows_hard_and_monotone(tmp_path, lut4, roots):
    case, r, lines = run_l0(tmp_path, circuit_c(), lut4, roots())
    s = case.sctx
    assert r.start is not None and r.origin_point == "centre" and r.probes == 0
    ev = evaluate(s, r.start.theta, r.start.cells)
    assert ev.status in ACCEPTED_STATUSES
    items = _min_s(ev)
    assert tuple(r.rows) == tuple("%s:%d" % (ROW_SEAL_ITEM, i) for i, _ in items)
    assert math.isclose(r.t, min(v for _, v in items), rel_tol=1e-12, abs_tol=1e-15)
    assert r.hard_ok == all(c.c >= 0 for c in _hard_rows(ev))
    assert r.hard_ok
    # 결과 = 수락 반복 중 (경성 ≥ 0, min s, −seq) 최대 -> 중심(수락 반복)보다 t 가 작지 않다
    cen = evaluate(s, tuple(sorted(th_of(lines[0]).items())), tuple(lines[0]["cells"]))
    assert cen.status in ACCEPTED_STATUSES
    if all(c.c >= 0 for c in _hard_rows(cen)):
        assert r.t >= min(v for _, v in _min_s(cen)) - 1e-12
    # 커널 = 이 호출 동안 늘어난 kernel_calls = 고유 키
    cnt = dict(s.counters)
    assert r.kernel_calls == cnt["kernel_calls"] == len(lines) == len({tuple(x["theta_hex"]) for x in lines})
    assert cnt["recompute_same_key"] == 0
    assert all(x["origin"].get("stage") is not None for x in lines)


def test_start_reused_by_start_points_without_kernel(tmp_path, lut4):
    """I-13: start 의 평가는 받아들일 상태이고 start_points(sctx, (), (start,)) 는 커널 0(hits +1)으로 첫 시작점을 돌려준다."""
    case = build_case(tmp_path, circuit_c(), lut4, eval_budget=40)
    s = case.sctx
    r = layer0_start(s)
    before = dict(s.counters)
    starts, log = start_points(s, (), (r.start,))
    after = dict(s.counters)
    assert after["kernel_calls"] == before["kernel_calls"] and after["hits"] == before["hits"] + 1
    assert starts and tuple(starts[0].theta) == tuple(r.start.theta)
    assert dict(log[0])["source"] == SOURCE_LAYER0


def test_deterministic_and_spec_constraints_unread(tmp_path, lut4):
    """I-15 새 컨텍스트 두 번 같은 start θ·t, I-16 spec judged 제약을 바꿔도 같은 start θ."""
    outs = []
    for name, cons in (("a", ()), ("b", ()), ("c", SS)):
        case = build_case(tmp_path / name, circuit_c(), lut4, eval_budget=40, constraints=cons)
        r = layer0_start(case.sctx)
        outs.append((tuple((k, float(v).hex()) for k, v in r.start.theta), float(r.t).hex(), r.stop))
    assert outs[0] == outs[1]
    assert outs[2][0] == outs[0][0]


def test_origin_prefix_kept(tmp_path, lut4, roots):
    """evaluate origin = origin + (("stage", "layer0"),) -- 부르는 쪽 태그가 S3 줄에 남는다."""
    root = roots()
    case = build_case(tmp_path, circuit_c(), lut4, eval_budget=40, archive_root=root)
    layer0_start(case.sctx, (("run", "x"),))
    lines = lines_of(root, case.sctx.context_fp)
    assert lines[0]["origin"] == {"run": "x", "stage": "layer0"}

