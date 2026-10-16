"""CONTRACT 3.21 [r5·r5b·r5c·r8] `layer0_start(sctx, origin=()) -> Layer0Result` + 5절 I-13~I-18.

기대값은 이 파일이 계약 문장으로 독립 계산한다(피검 함수로 만들지 않는다):
- 1 상자 중심: ln_idu 상자(npz 포락선, conftest `expect_ln_idu_bounds`) 중점, y = 0.5, L 칸 = ln 좌표 중점에 가장 가까운 칸
  (L 격자 (1, 1.8, 2.6, 4) µm -- ln 중점 2 µm 는 1.8, 선형 중점 2.5 µm 는 2.6 이라 둘이 갈린다).
- 2 전류 중심: minimax |ln(I/I_c)| 의 닫힌 해(행이 단일항이면 z* = (ln I_c 최소 + 최대)/2, u* = 반폭), I_c = √(I_off·I_max)
  (conftest `expect_box`).
- 3 Halton·hit-and-run: 이 파일의 근기 역순 `phi`·소수 열과 선형 전류 좌표의 열린 현 걸음을 S3 evals 줄(origin probe k)과 대조.
  ln_idu 시험 하한 = [r9] max(칸 전도 하한, 칸 정점 하한)(conftest `conduction_floor`·`peak_floor`, 모든 쓰기 소자 -- 3.21 3 r8 의
  `ln_idu_floors` 위임 + 3.22 r9 전도 하한).
- 3b 수리: 위반 크기·h 를 정한 `no_root_in_window` 실패를 시험 점에 심고, ⌈log2(|끝 − x|/res)⌉ bisection 의 평가 좌표를 계산한다
  (res = tol_V·gm/ID 최대, tol_V = 끝 |h| 최솟값/margin). [xrun J-5, 사용자 결정 2026-10-15 "권장대로 해"] 실패를 심는 수단은 옛 '디스크 실패 줄'
  (엔진이 S3 evals 를 실행 사이에 읽던 경로 -- 설계 40 v1.10 §2.4.3 에서 삭제) 대신 공개 대체 지점 `gmid_engine.search.layer0_center.evaluate`
  (interface card J-5 절)를 test 안에서 감싸는 `inject_failures` 다. 아래 그 helper 의 docstring 이 커널 수·S3 줄 수 단언을 바꾼 근거를 적는다.
- 4·5 최대-최소: t = 출발점 봉인 보고 항목 중 margin 유한한 i 의 min(1 − margin_i), 경성 행 ≥ 0.
"""
import dataclasses
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

import gmid_engine.search.layer0_center as layer0_module
from gmid_engine.core import FailureRecord
from gmid_engine.sizing import REASON_NO_ROOT

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


def theta_key(theta):
    """θ(매핑 또는 (key, value) 쌍들) -> 비교 키(성분 키 tuple, float.hex). evaluate 인자 θ 와 S3 줄 θ 를 같은 형식으로 맞춘다."""
    pairs = theta.items() if hasattr(theta, "items") else theta
    return tuple(sorted((tuple(k), float(v).hex()) for k, v in pairs))


def line_key(line):
    """S3 evals 줄의 θ(`theta` 칸 -- JSON float 는 repr 왕복이라 비트 그대로) -> theta_key 형식."""
    return theta_key(line["theta"])


def no_root(dev, node, margin, h_lo, h_hi):
    return FailureRecord("SEAL_VIOLATION", devices=(dev,), margin=margin,
                         detail={"reason": REASON_NO_ROOT, "node": node, "lo": 0.0, "hi": 1.8, "h_lo": h_lo, "h_hi": h_hi,
                                 "item": 7, "bounds": ("vds_axis", "rail")})


def empty_window(node):
    return FailureRecord("SEAL_VIOLATION", devices=(), margin=None,
                         detail={"reason": "empty_window", "node": node, "lo": 1.8, "hi": 0.0, "item": 7, "constraints": 3})


def inject_failures(monkeypatch, failures):
    """[xrun J-5] layer0_center 의 평가 대체 지점(`layer0_module.evaluate`, 서명 evaluate(sctx, theta, cells, parent=None, origin=(),
    geometry=None) -> EvalResult)을 감싼다. failures = {theta_key: FailureRecord}. 지정 θ 에서는 **진짜 evaluate 를 부른 뒤** 결과를
    dataclasses.replace 로 실패로 바꾼다: status = STATUS_FAILED, failure = 합성 FailureRecord, 실패 결과의 모양(evaluation·objectives None,
    constraints·unmeasured·warnings 빈 tuple -- 엔진이 실제로 낸 실패 EvalResult 와 같은 칸 값, cone·key·seq 는 진짜 결과 그대로).
    진짜 evaluate 를 부르는 쪽을 고른 이유: EvalResult.key(평가 키)를 test 가 만들지 않아도 되고(공개 생성 경로 없음), 커널·S3 계수 관계
    (kernel_calls = S3 evals 줄 수 = 고유 θ 수)가 그대로 성립한다. 그 대가로 옛 디스크 적중(커널 0, S3 줄 없음)과 달리 심은 점도 커널을 한 번
    부르고 S3 줄(진짜 결과)을 남긴다 -- 각 test 의 줄 순서 단언은 이 줄을 넣어 고쳤다(test 주석). -> 실제로 바꾼 호출 [(theta_key, origin)] 목록."""
    real = layer0_module.evaluate
    hits = []

    def wrapped(sctx, theta, cells, parent=None, origin=(), geometry=None):
        r = real(sctx, theta, cells, parent=parent, origin=origin, geometry=geometry)
        rec = failures.get(theta_key(theta))
        if rec is None:
            return r
        hits.append((theta_key(theta), origin))
        return dataclasses.replace(r, status=STATUS_FAILED, failure=rec, evaluation=None, objectives=None, constraints=(),
                                   unmeasured=(), warnings=())

    monkeypatch.setattr(layer0_module, "evaluate", wrapped)
    return hits


def run_l0(tmp, topo_doc, lut, root, eval_budget=40, constraints=()):
    """새 컨텍스트로 layer0_start. -> (case, result, 이 실행이 쓴 S3 줄)."""
    case = build_case(tmp, topo_doc, lut, eval_budget=eval_budget, archive_root=root, constraints=constraints)
    r = layer0_start(case.sctx)
    return case, r, lines_of(root, case.sctx.context_fp)


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


def test_single_current_first_probe_direction_zero(tmp_path, lut4, roots, monkeypatch):
    """θ 전류 변수 하나(변수 0, 기저 2): k = 1 이면 d = 2·φ_2(1) − 1 = 0 -- 걸음이 없어 시험 1 의 θ 전류 = 전류 중심 그대로이고
    모든 시험 점은 상자 안 유한 값이다(3.21 3 'θ 전류 = p(상자로 자름)', I-18). 중심은 평가 대체 지점에서 빈 창 실패로 바꿔 실패시킨다
    ([xrun J-5] -- 옛 디스크 실패 줄 대신)."""
    root0 = roots()
    case0, _, lines0 = run_l0(tmp_path / "a", circuit_c(), lut4, root0)
    centre = lines0[0]
    assert centre["origin"] == {"stage": "layer0"}                       # 전제: 첫 줄 = 중심 점
    hits = inject_failures(monkeypatch, {line_key(centre): empty_window("out")})
    root = roots()
    case, r, lines = run_l0(tmp_path / "b", circuit_c(), lut4, root, eval_budget=3)
    s = case.sctx
    # [xrun J-5] 옛 단언 '디스크 실패 적중 계수 >= 1'의 대체: 대체 지점이 중심 점에서 실제로 실패를 냈다(주입이 공허하지 않다).
    assert [h[0] for h in hits] and all(h[0] == line_key(centre) for h in hits)
    assert r.start_status == STATUS_FAILED
    v = [x for x in s.domain.variables if x.component[0] == "current"][0]
    # [xrun J-5] 심은 중심도 진짜 evaluate 를 한 번 불러 S3 줄을 남긴다(inject_failures docstring) -- 옛 '첫 줄 = 시험 1' 은
    # '중심 줄 다음 첫 시험 줄 = 시험 1' 이 된다.
    assert lines and lines[0]["origin"] == {"stage": "layer0"} and line_key(lines[0]) == line_key(centre)
    probes = [ln for ln in lines if "probe" in ln["origin"]]
    assert probes and probes[0]["origin"] == {"stage": "layer0", "probe": 1}
    assert th_of(probes[0])[v.component] == th_of(centre)[v.component]
    for ln in lines:
        if "probe" in ln["origin"]:
            x = th_of(ln)[v.component]
            assert math.isfinite(x) and math.exp(v.lo) * (1 - 1e-12) <= x <= math.exp(v.hi) * (1 + 1e-12)


# ---------------------------------------------------------------- 3b 1단계 수리 (bisection)

def _window_with_probe_failures(tmp_path, lut4, roots, fails, monkeypatch):
    """빈 창 회로: 1차 실행으로 시험 점 줄을 얻고, fails = {k: FailureRecord} 를 그 시험 점의 평가 결과로 심어(평가 대체 지점,
    [xrun J-5] -- 옛 디스크 실패 줄 대신) 다시 실행. 심은 시험 점마다 대체 지점이 실제로 실패를 냈는지 확인한다(주입 비공허)."""
    topo_doc = circuit_window()
    _, _, base = run_l0(tmp_path / "a", topo_doc, lut4, roots(), eval_budget=8)
    by_k = {ln["origin"].get("probe"): ln for ln in base}
    hits = inject_failures(monkeypatch, {line_key(by_k[k]): f for k, f in fails.items()})
    case, r, lines = run_l0(tmp_path / "b", topo_doc, lut4, roots(), eval_budget=60)
    assert {h[0] for h in hits} == {line_key(by_k[k]) for k in fails}
    return _attach_netlist(case, topo_doc), r, lines, by_k


def test_repair_bisection_count_and_points(tmp_path, lut4, roots, monkeypatch):
    """묶음 = n + 1 = 5 시험. 수리 가능 실패 둘(시험 2 margin 3, 시험 4 margin 2) 중 margin 최소 = 시험 4 에서 MC 좌표 수리:
    끝 = 칸 하한([r9] max(전도, 정점) -- 빈 창 실패 = 'MC 의 같은 실패' 아님 -> 통과 끝), 이어 ⌈log2(|끝 − x|/res)⌉ 번 bisection, 중점은 모두
    통과 쪽(빈 창)이라 좌표 = x + (끝 − x)/2^j. 마지막 점도 빈 창 실패(위반 크기 없음) -> 사슬 끝, 시험 6 으로 이어진다."""
    h_lo, h_hi, margin = -0.004, 0.01, 2.0
    fails = {2: no_root("MC", "inp", 3.0, -0.003, 0.02), 4: no_root("MC", "inp", margin, h_lo, h_hi)}
    case, r, lines, by_k = _window_with_probe_failures(tmp_path, lut4, roots, fails, monkeypatch)
    s = case.sctx
    seq_of = [ln["origin"].get("probe") for ln in lines]
    # [xrun J-5] 옛 [None, 1, 3, 5](2·4 는 디스크 실패 적중 -- 커널 0, S3 줄 없음). 지금 2·4 는 대체 지점이 진짜 evaluate 뒤 실패로 바꾸므로
    # 커널 1회·S3 줄 1개씩 남는다(inject_failures docstring) -> 중심 + 시험 1~5 가 차례로.
    assert seq_of[:6] == [None, 1, 2, 3, 4, 5]
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


def test_no_repair_without_finite_window_ends(tmp_path, lut4, roots, monkeypatch):
    """h 끝이 무한이면 위반 크기 없음 -> 수리하지 않는다: 시험 5 다음 줄이 곧 시험 6."""
    fails = {2: no_root("MC", "inp", 3.0, -0.003, math.inf), 4: no_root("MC", "inp", 2.0, -math.inf, 0.01)}
    _, r, lines, _ = _window_with_probe_failures(tmp_path, lut4, roots, fails, monkeypatch)
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


# =====================================================================================================================
# [NFR-4 card 2] 층 0 끌어올림 BP1 (interface card nfr4c2 C4, 설계 41 §5.13). test N-T20~N-T22.
# 기호(C4): x = 전류 중심 풀이기 해의 θ 전류 ln 좌표, 행 m = 원뿔 행 중 움직이는 θ 전류를 읽는 행, ref_m = 사다리 칸 current_ref 의 값,
# A_m = Σ_움직이는 항 계수·e^x/ref_m, F_m = Σ_고정 항 계수·고정값/ref_m, q_m = (Σ 계수·전류)/ref_m, R = {m : A_m > 0}, √ε = sqrt(sys.float_info.epsilon).
# 결과(클램프 없음·원뿔 유지): |min_R q − (1 + √ε)| ≤ γ_n·(1 + √ε), 나머지 R 행 q ≥ 1 + √ε, γ_n = nε/(1 − nε)(n = C4 셈 규칙, 아래 `op_count`).
# 풀이기 해 주입 = 교체 지점 `layer0_module.scipy_minimize`(C4 계약: scipy.optimize.minimize 와 같은 호출, 반환의 x 를 읽는다) -- centre_start 호출 동안만.
# oracle: (손) toy 회로·ref·고정 전류·주입 x 를 test 가 정한다, (식) C4 식. 피검 함수 출력으로 기대값을 만들지 않는다 -- 결과 θ 에서 q 를 test 가 계산한다.
# 손 toy(모두 θ 전류 변수 하나 = ('current', 'M2'), 원뿔 모양은 test 가 schema 에서 읽어 전제로 확인한다):
#   C : M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd)              -> 행 M1 = I_M2, M2 = I_M2 (F = 0)
#   FN: M1 nmos (n, in, gnd) + M2 pmos (n, pb, vdd) + I1 (n -> gnd)   -> 행 M1 = I_M2 − I1 (F < 0), M2 = I_M2
#   FP: 같은 회로, I1 (vdd -> n)                                       -> 행 M1 = I_M2 + I1 (F > 0), M2 = I_M2
# =====================================================================================================================

import sys as _sys
from types import SimpleNamespace as _NS

from gmid_engine.search.start_values import StartRung

from .conftest import two as _two

SQRT_EPS = math.sqrt(_sys.float_info.epsilon)
I_FIX = 2e-6                    # 손: 이상 전류원 I1 값(spec element value)


def _lift_topo(kind):
    if kind == "C":
        return circuit_c()
    src = ("n", "gnd") if kind == "FN" else ("vdd", "n")
    return topo("hand_lift_%s" % kind.lower(), [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "pmos", "n", "pb", "vdd")],
                {"in": ("input", "single_ended_input"), "n": ("output", "single_ended_output")},
                sources=[_two("I1", "current_source", src[0], src[1])], bias=["pb"])


def _lift_case(tmp, lut, kind):
    els = () if kind == "C" else (("I1", "current_source", I_FIX),)
    return build_case(tmp, _lift_topo(kind), lut, eval_budget=20, elements=els)


def _rung_inputs(s):
    """사다리 칸 입력(전류 성분 없음 -> 전류 중심 풀이기가 돈다): 사다리 칸 없는 centre_start 의 ln_idu·L 성분과 L 칸(입력 생성)."""
    _v, th, cells, _u = layer0_module.centre_start(s)
    fixed = tuple(sorted((k, x) for k, x in th.items() if k[0] in ("ln_idu", "L")))
    lcells = tuple(zip([m for m, _ in s.domain.l_cells], cells))
    return fixed, lcells


def _rung(fixed, lcells, refs):
    return StartRung(t=1.0, theta=fixed, cells=lcells, current_ref=tuple(refs))


def _cur_var(s):
    (v,) = [x for x in s.domain.variables if x.component[0] == "current"]
    return v


def _inject(monkeypatch, v, x_of_real):
    """scipy_minimize 교체: 진짜 minimize 를 불러 반환 x 의 θ 전류 칸(경계 = 그 변수 (lo, hi) 인 칸, 정확히 하나)만 x_of_real(진짜 값) 으로 바꾼다.
    -> 호출 기록 [(진짜 x, 바꾼 x)]."""
    import numpy as np
    real = layer0_module.scipy_minimize
    seen = []

    def fake(fun, x0, **kw):
        res = real(fun, x0, **kw)
        idx = [i for i, b in enumerate(kw["bounds"]) if tuple(b) == (v.lo, v.hi)]
        assert len(idx) == 1, kw["bounds"]
        x = np.array(res.x, dtype=float)
        x[idx[0]] = x_of_real(float(res.x[idx[0]]))
        seen.append((float(res.x[idx[0]]), float(x[idx[0]])))
        return _NS(x=x, success=True, status=0, nit=getattr(res, "nit", 0), fun=getattr(res, "fun", 0.0), message="injected")

    monkeypatch.setattr(layer0_module, "scipy_minimize", fake)
    return seen


def _rows(s):
    """원뿔 행 중 움직이는 θ 전류를 읽는 행 -> ([(행, [(계수, 원천, 움직임 여부)])], {고정 원천: 값}) -- schema(입력)에서 읽는다."""
    sch = schema_of(s.dc)
    fixed = dict(sch.fixed)
    moving = {v.component[1] for v in s.domain.variables if v.component[0] == "current"}
    out = []
    for m, terms in sch.current_cone:
        ts = [(t.num / t.den, t.source, t.source in moving) for t in terms]
        if any(mv for _c, _src, mv in ts):
            out.append((m, ts))
    return out, fixed


def _q(rows, fixed, theta, refs):
    """test 의 q_m 계산(θ 의 전류 + schema 고정값) -> {m: (q, A, k 움직이는 항 수, j 고정 항 수)}."""
    ref = dict(refs)
    out = {}
    for m, ts in rows:
        a = sum(c * theta[("current", src)] for c, src, mv in ts if mv) / ref[m]
        f = sum(c * fixed[src] for c, src, mv in ts if not mv) / ref[m]
        out[m] = (a + f, a, sum(1 for t in ts if t[2]), sum(1 for t in ts if not t[2]))
    return out


def op_count(k, j):
    """C4 셈 규칙(사칙연산·exp·ln 각 1, max·min·클램프·비교 제외), 결정 행 하나의 경로:
    s 계산 = 움직이는 항마다 exp·곱·나눗셈(3k) + 합(k − 1) + 고정 항마다 곱·나눗셈(2j) + 합(max(j − 1, 0)) + 분자 (1 + √ε) − F(2) + 나눗셈(1) + ln(1),
    θ = exp(x + s)(덧셈·exp 2), q 재계산 = 항마다 곱·나눗셈(2(k + j)) + 합(k + j − 1)."""
    s_ops = 3 * k + (k - 1) + 2 * j + max(j - 1, 0) + 2 + 1 + 1
    return s_ops + 2 + 2 * (k + j) + (k + j - 1)


def gamma(n):
    e = _sys.float_info.epsilon
    return n * e / (1 - n * e)


# (toy, refs, 주입 전류 또는 None) -- 손. None 이면 x = 진짜 전류 중심 풀이기 해(교체 지점은 기록만), 값이면 교체 지점이 x = ln(그 값)으로 바꾼다
# (고정 전류가 있는 toy 는 풀이기 해가 실행마다 크게 달라(as-built 실측: 같은 입력에서 x = −4.49 와 −9.20) 손으로 x 를 정한다). 각 경우 그 x 에서
# 끌어올림이 필요한지는 전제로 확인한다.
LIFT_CASES = {
    "C_f0": ("C", (("M1", 1e-4), ("M2", 2e-4)), None),          # 결정 행 M2(F = 0)
    "FN_neg": ("FN", (("M1", 1e-4), ("M2", 1e-4)), 5e-5),       # 결정 행 M1 = I_M2 − I1 (F < 0) -- F ≠ 0 행이 최소
    "FP_pos": ("FP", (("M1", 4e-4), ("M2", 1e-4)), 1e-4),       # 결정 행 M1 = I_M2 + I1 (F > 0) -- F ≠ 0 행이 최소
    "FP_numer_le0": ("FP", (("M1", 1e-6), ("M2", 3e-6)), 1e-6),  # M1 분자 1 + √ε − F ≤ 0(F = I1/ref = 2, 그 행은 s 를 정하지 않는다), 결정 행 M2
}


@pytest.mark.parametrize("name", sorted(LIFT_CASES))
def test_layer0_lift_closed_form(tmp_path, lut4, monkeypatch, name):
    """N-T20: 손 toy 원뿔·ref·고정 전류·x(진짜 풀이기 해 또는 주입) -> centre_start(sctx, rung) 결과 θ 로 test 가 q_m 을 계산:
    |min_R q − (1 + √ε)| ≤ γ_n·(1 + √ε)(n = op_count, 결정 행의 항 수로 센다), 나머지 R 행 q ≥ 1 + √ε. 전제: 주입 x 에서 어떤 행이 1 + √ε 밑(끌어올림
    필요), 결과 θ 가 상자 안(클램프 없음), 결과 원뿔 행 c > 0(원뿔 유지), ln_idu·L 성분은 사다리 칸 값 그대로."""
    kind, refs, i_inj = LIFT_CASES[name]
    case = _lift_case(tmp_path, lut4, kind)
    s = case.sctx
    rows, fixed = _rows(s)
    assert sorted(m for m, _ in rows) == ["M1", "M2"], rows                       # 전제: 손 원뿔 모양
    assert all(any(not mv for _c, _s, mv in ts) == (kind != "C" and m == "M1") for m, ts in rows), rows
    v = _cur_var(s)
    fixed_th, lcells = _rung_inputs(s)
    seen = _inject(monkeypatch, v, (lambda x: x) if i_inj is None else (lambda _x: math.log(i_inj)))   # 기록만 또는 주입
    _vars, th, _cells, _u = layer0_module.centre_start(s, _rung(fixed_th, lcells, refs))
    assert len(seen) == 1, seen                                                   # 전류 중심 풀이기 한 번(C4: 최대-최소는 부르지 않는다)
    pre = _q(rows, fixed, {v.component: math.exp(seen[0][1])}, refs)
    assert min(q for q, _a, _k, _j in pre.values()) < 1 + SQRT_EPS, pre           # 전제: 그 x 에서 끌어올림 필요
    assert all(a > 0 for _q0, a, _k, _j in pre.values())                          # 전제: 두 행 모두 R
    assert all(th[k] == x for k, x in fixed_th), "ln_idu·L 은 사다리 칸 값 그대로"
    i_out = th[v.component]
    assert math.exp(v.lo) < i_out < math.exp(v.hi)                                # 전제: 클램프 없음
    assert all(row.c > 0 for row in cone_rows(schema_of(s.dc), tuple(sorted(th.items()))))   # 전제: 원뿔 유지
    got = _q(rows, fixed, th, refs)
    m_min = min(got, key=lambda m: got[m][0])
    q_min, _a, k, j = got[m_min]
    tol = gamma(op_count(k, j)) * (1 + SQRT_EPS)
    assert abs(q_min - (1 + SQRT_EPS)) <= tol, (name, m_min, q_min - 1, SQRT_EPS, tol)
    for m, (q, _a2, _k2, _j2) in got.items():
        if m != m_min:
            assert q >= 1 + SQRT_EPS, (name, m, q)


def test_layer0_lift_independent_of_solver_noise(tmp_path, lut4, monkeypatch):
    """N-T21: toy C, ref_m = W_min 전류(W = I·L/e^{ln_idu} 이므로 ref_m = W_min·e^{ln_idu_m}/L_m -- 손, 사다리 칸 ln_idu·L 에서) -> q_m = W_m/W_min.
    scipy_minimize 교체로 진짜 해의 θ 전류 x 를 ±1e-9 흔든 두 입력 -> (전제) 두 경우 끌어올림이 필요하고 최소 행이 같으면, 끌어올린 점 평가의 그 행
    `w_min:<행>` c 가 둘 다 > 0(BP1 √ε 여유 -- c ≈ W_min·√ε/grid 크기, 반올림 크기보다 훨씬 크다)."""
    s = _lift_case(tmp_path, lut4, "C").sctx
    rows, fixed = _rows(s)
    v = _cur_var(s)
    fixed_th, lcells = _rung_inputs(s)
    fth = dict(fixed_th)
    w_min = s.domain.w_min_m
    refs = tuple((m, w_min * math.exp(fth[("ln_idu", m)]) / fth[("L", m)]) for m, _ in rows)
    outs = []
    for d in (-1e-9, 1e-9):
        seen = _inject(monkeypatch, v, lambda x, d=d: x + d)
        _vars, th, cells, _u = layer0_module.centre_start(s, _rung(fixed_th, lcells, refs))
        ((_x_real, x_used),) = seen
        pre = _q(rows, fixed, {v.component: math.exp(x_used)}, refs)
        m_pre = min(pre, key=lambda m: pre[m][0])
        assert pre[m_pre][0] < 1 + SQRT_EPS, pre                                   # 전제: 끌어올림 필요
        got = _q(rows, fixed, th, refs)
        m_min = min(got, key=lambda m: got[m][0])
        ev = evaluate(s, tuple(sorted(th.items())), cells)
        c = {r.name: r.c for r in ev.constraints}
        outs.append((m_min, c["w_min:%s" % m_min]))
        monkeypatch.undo()
    assert outs[0][0] == outs[1][0], outs                                          # 전제: 최소 행이 같다
    assert outs[0][1] > 0 and outs[1][1] > 0, outs


EDGE_CASES = {
    # 이름: (refs 또는 None(사다리 칸 없음), 주입 x(ln 전류) 만드는 함수(변수 v)) -- 손
    "formula_negative_no_lowering": ((("M1", 1e-12), ("M2", 1e-12)), lambda v: math.log(1e-7)),
    "empty_current_ref_no_lift": ((), lambda v: math.log(1e-7)),
    "no_rung_no_lift": (None, lambda v: math.log(1e-7)),
    "clip_high_without_lift": ((("M1", 1e-12), ("M2", 1e-12)), lambda v: v.hi + 1.0),
    "clip_low_without_lift": ((("M1", 1e-30), ("M2", 1e-30)), lambda v: v.lo - 1.0),
}


@pytest.mark.parametrize("name", sorted(EDGE_CASES))
def test_layer0_lift_edges(tmp_path, lut4, monkeypatch, name):
    """N-T22 가장자리(같은 교체 지점으로 x 지정, toy C): 식 값 < 0(ref 가 아주 작아 q > 1 + √ε) -> s = 0(낮추지 않음), current_ref 빈 사다리 칸 ->
    끌어올리지 않음, 사다리 칸 없음 -> 끌어올리지 않음, 상자 밖 x -> 상자로 자름. 기대 θ 전류 = exp(clip(x, lo, hi))(손).
    'R 빔'·'분자 모두 ≤ 0' 은 θ 전류 변수의 자기 행(계수 +1, 고정 항 없음)이 언제나 R 에 들어 분자 1 + √ε > 0 이라 공개 toy 입력으로 만들 수 없다
    (보고). 분자 ≤ 0 인 행이 섞인 경우는 N-T20 `FP_numer_le0`."""
    refs, x_fn = EDGE_CASES[name]
    s = _lift_case(tmp_path, lut4, "C").sctx
    v = _cur_var(s)
    fixed_th, lcells = _rung_inputs(s)
    x_inj = x_fn(v)
    seen = _inject(monkeypatch, v, lambda _x: x_inj)
    rung = None if refs is None else _rung(fixed_th, lcells, refs)
    _vars, th, _cells, _u = layer0_module.centre_start(s, rung)
    assert seen
    want = math.exp(min(max(x_inj, v.lo), v.hi))
    assert math.isclose(th[v.component], want, rel_tol=4 * _sys.float_info.epsilon, abs_tol=0.0), (name, th[v.component], want)


# =====================================================================================================================
# [XRUN-F1 card A] interface card xrunf1a C2 층 0 행: 최대-최소의 시작 좌표 = clip(x0ᵢ), 좌표 -> θ = clip 뒤 ThetaCoords.to_theta. 결과: 시작
# 좌표가 상자 안이면 시작 좌표에서 만든 θ 는 출발점 θ 와 변수 성분마다 비트 동일. 관찰 지점(J-3) = 모듈 속성 `layer0_center.fd_jacobian`
# (서명 fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset()), 시작점 FD 에서 x = 시작 좌표, base = 출발점 평가 결과).
# 케이스: 회로 C(toy lut4). 상자 중심 출발이면 θ 전류가 exp(ln 좌표)로 만든 값이라 왕복이 원값을 잃지 않는다(전제가 서지 않음) -- 그래서
# 중심 점을 평가 대체 지점(`inject_failures`, card 1 J-5)에서 빈 창 실패로 바꿔 Halton·hit-and-run 시험 점(θ 전류 = 선형 좌표 값)에서
# 출발하게 한다. 전제(공허 방지)는 test 안에서 단언: 출발점이 시험 점, log 변수 하나 이상이 math.exp(math.log(θ)) != θ 이고 그 x 가 상자 안.
# oracle: (비교) 같은 엔진이 낸 출발점 평가 결과 θ(base.theta) 와 FD 에 넘긴 변환 출력의 비트 비교 + (Py) 전제. ThetaCoords 는 import 하지
# 않는다(A-T5 의 base 실패 사유가 import 오류가 아니라 비트 단언이어야 한다 -- 감사 A-3).
# =====================================================================================================================

def _record_fd(monkeypatch, module, store, coords_log=None):
    """module.fd_jacobian 을 진짜 함수를 부르는 기록기로 바꾼다. store 에 (variables, x 사본, base, to_theta, 그 시점 ThetaCoords 객체)."""
    real = module.fd_jacobian

    def rec(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset()):
        store.append((tuple(variables), [float(v) for v in x], base, to_theta,
                      coords_log[-1] if coords_log else None))
        return real(sctx, variables, x, base, cells, to_theta, origin, skip)
    monkeypatch.setattr(module, "fd_jacobian", rec)


def _layer0_from_probe(tmp_path, lut, roots, monkeypatch, store, coords_log=None):
    """중심 점을 빈 창 실패로 바꾼 층 0 실행(위 test_single_current_first_probe_direction_zero 와 같은 주입). -> (case, result, hits)."""
    _, _, lines0 = run_l0(tmp_path / "a", circuit_c(), lut, roots(), eval_budget=3)
    centre = lines0[0]
    assert centre["origin"] == {"stage": "layer0"}                                  # 전제: 첫 줄 = 중심 점
    hits = inject_failures(monkeypatch, {line_key(centre): empty_window("out")})
    _record_fd(monkeypatch, layer0_module, store, coords_log)
    case, r, _ = run_l0(tmp_path / "b", circuit_c(), lut, roots(), eval_budget=40)
    return case, r, hits


def test_layer0_start_fd_theta_bits_equal_start_theta(tmp_path, lut4, roots, monkeypatch):
    """A-T5: 층 0 최대-최소 첫 FD 호출 -- to_theta(x) 의 변수 성분이 출발점 평가 결과 θ(dict(base.theta))와 비트 동일."""
    calls = []
    _, r, hits = _layer0_from_probe(tmp_path, lut4, roots, monkeypatch, calls)
    assert hits                                                                     # 주입 비공허: 중심이 실제로 실패로 바뀌었다
    assert r.origin_point is not None and r.origin_point.startswith("halton:")      # 전제: 시험 점 출발
    assert calls, "층 0 최대-최소가 fd_jacobian 을 부르지 않았다"
    variables, x, base, to_theta, _ = calls[0]
    th = dict(base.theta)
    # 전제(공허 방지): 왕복이 원값을 잃는 log 변수가 있고 그 시작 좌표가 상자 안
    lossy = [v.component for i, v in enumerate(variables)
             if v.log and math.exp(math.log(th[v.component])) != th[v.component] and v.lo <= x[i] <= v.hi]
    assert lossy, [(v.component, v.log) for v in variables]
    got = to_theta(x)
    assert {v.component: float(got[v.component]).hex() for v in variables} == \
        {v.component: float(th[v.component]).hex() for v in variables}


def test_theta_coords_used_by_layer0(tmp_path, lut4, roots, monkeypatch):
    """A-T8(층 0 경로): ThetaCoords.start 를 클래스 수준에서 감싸(원래 것을 부름) 층 0 이 한 번 이상 부르고, 첫 FD 에 넘긴 변환의 출력
    (시작 좌표 x, 상자 안)이 그 직전에 만든 객체의 to_theta(x) 출력과 비트 같다. oracle (비교)."""
    from gmid_engine.search import ThetaCoords
    made = []
    orig = ThetaCoords.start

    def start(cls, variables, theta):
        c = orig(variables, theta)
        made.append(c)
        return c
    monkeypatch.setattr(ThetaCoords, "start", classmethod(start))
    calls = []
    _layer0_from_probe(tmp_path, lut4, roots, monkeypatch, calls, made)
    assert made and calls
    variables, x, _base, to_theta, coords = calls[0]
    assert coords is not None
    assert all(v.lo <= xi <= v.hi for v, xi in zip(variables, x))                  # 전제: 시작 좌표가 상자 안(자르기 = 항등)
    a, b = to_theta(x), coords.to_theta(x)
    assert {k: float(v).hex() for k, v in a.items()} == {k: float(v).hex() for k, v in b.items()}
