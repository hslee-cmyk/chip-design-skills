"""metamorphic: GB7 DC 정본 풀이(sizing `build_kernel_context`·`size_and_seal`)가 이름·순서·극성 변형을 따라가는가.

oracle 종류 (a) -- 변형 관계(원래 결과에 변형 표를 적용한 것 대 변형 입력의 결과). 피검 출력 숫자를 기대값으로 붙이지 않는다.
근거 문장(sizing CONTRACT):
- 3.0 구조 색: "이름 전단사·원소/키 순서 섞기를 해도 색 함수가 그 전단사로 옮겨진다(같은 정점 → 같은 색)" -- 그대로 확인.
- 3.0 동률 논증 + 9절 '이름 전단사': 구조 색이 먼저라 쓰기 소자·θ 기저·W4 뿌리가 전단사로 옮겨지고, 차이가 있으면 그 원소는 모두
  원래 계획의 `dc_tie_breaks`·`CurrentBasis.ties` 후보에 든다. 기록이 없는 결정은 이름과 무관하다.
- 3절 7: order 의 같은 색 안 이름 순서는 SCC 안 갱신 순서·시작값에만 쓰이고 수렴값(허용오차 안)을 바꾸지 않는다 -- 그래서 θ 를
  표로 옮기면 노드전압은 비트 동일, 단 다변수 순환 SCC(Gauss-Seidel·Newton) 노드만 그 SCC 의 기록 허용오차 `SccLog.tol` 안
  (허용오차 출처 = 5.4·5.5 노드 허용오차; 새 상수 없음). 원소 전류는 기저 행의 유리수 합(4.2·5.2)이라 θ 전류가 같으면 비트 동일.
- 9절 결정론: 같은 doc·spec·LUT·θ 면 netlist 순서 섞기와 무관하게 `size_and_seal(...).snapshot.fp` 가 같다(태그 잡음은 authoring
  CONTRACT 2절에 따라 투영 밖).
- 극성 뒤집기: LUT 는 nmos·pmos 가 달라(실데이터) 값은 비교하지 않는다. 계약이 kind 와 무관하게 정한 개수만 본다 -- 3절 불변식
  "MOS 수 = writer 수 + dependent 수; dependent 수 = G_vgs 순환수; W4 수 = F 없는 성분 수 + G_vgs 밖 노드 수"(G_vgs 는 (gate, source)·
  저항 엣지로 kind 를 보지 않는다), 4.4 θ 성분 = (ln_idu, writer)·(L, MOS)·(y, W4 키)·(current, free)·… -- free 수 = KCL 행렬의 열 수
  − 계수(4.2: nmos (d, s)·pmos (s, d) 는 열 부호만 바꿔 계수가 같다). 그래서 θ 성분 종류별 개수가 같다.
고정 θ 출처: 원래 회로의 search `layer0_start` 시작점(입력 -- 봉인 통과 점이어야 비교가 공허하지 않다, 아래 precondition test).
"""
from __future__ import annotations

import collections

import pytest

from gmid_engine.sizing import (COORD_DEPENDENT, COORD_WRITER, DC_KEY, SCC_GAUSS_SEIDEL, SCC_NEWTON, TIER_W4,
                                size_and_seal)
from gmid_engine.sizing import KERNEL_KEY   # [U17 ①-b] θ 스키마 = S0 수준 필드 graph/kernel: theta_schema(설계 40 v1.9.1 §2.4.7 KernelContext 행, D8)

from .pipeline import map_theta

SYNTH = ("syn_cs_load", "syn_diffpair5", "syn_follower")
LIB = ("two_stage_ota", "folded_cascode", "ngcc_3stage_ff")
CIRCUITS = SYNTH + LIB
SEEDS = range(3)
ITERATIVE = (SCC_GAUSS_SEIDEL, SCC_NEWTON)


def _plan(snap, f):
    return snap.value("graph", DC_KEY, f)


def _tie_candidates(ctx):
    """원래 계획에서 이름이 결정을 가른 후보 이름 전부(3절 TieBreak + 4.2 CurrentBasis.ties)."""
    names = set()
    for t in tuple(_plan(ctx.base, "dc_tie_breaks")) + tuple(_plan(ctx.base, "dc_current_basis").ties):
        names.update(t.candidates)
    return names


def _theta0(pipe, name):
    theta, res = pipe.theta0(name)
    assert theta is not None, "원래 회로 %s 의 층 0 시작점 없음(stop=%s) -- 비교할 봉인 점이 없다" % (name, res.stop)
    return theta[0]


# ------------------------------------------------------------------ θ 무관 계획


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_structure_colour_follows_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    for kind in ("node", "device"):
        ca = dict(a.ctx.base.column(kind, "dc_colour"))
        cb = dict(b.ctx.base.column(kind, "dc_colour"))
        assert cb == {b.nm(k): v for k, v in ca.items()}


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_writer_plan_and_theta_schema_follow_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    allowed = {b.nm(x) for x in _tie_candidates(a.ctx)}
    comps_a = {(k, b.nm(n)) for k, n in a.ctx.base.value("graph", KERNEL_KEY, "theta_schema").components}
    comps_b = set(b.ctx.base.value("graph", KERNEL_KEY, "theta_schema").components)
    diff = comps_a ^ comps_b
    assert {n for _, n in diff} <= allowed, (sorted(diff), sorted(allowed))
    wa = dict(a.ctx.base.column("node", "dc_writer"))
    wb = dict(b.ctx.base.column("node", "dc_writer"))
    assert set(wb) == {b.nm(n) for n in wa}
    for n, w in wa.items():
        v = wb[b.nm(n)]
        if w.element in _tie_candidates(a.ctx) or (w.known is not None and w.known in _tie_candidates(a.ctx)):
            continue                                     # 9절: 기록된 동률 후보 안의 선택은 이름이 가른다
        assert (v.tier, v.relation, v.element, v.known, v.y_key) == (
            w.tier, w.relation, b.nm(w.element) if w.element else None, b.nm(w.known) if w.known else None,
            b.nm(w.y_key) if w.y_key else None), n
    ca = dict(a.ctx.base.column("device", "dc_coord"))
    cb = dict(b.ctx.base.column("device", "dc_coord"))
    if not _tie_candidates(a.ctx):
        assert cb == {b.nm(k): type(v)(v.role, v.relation, b.nm(v.partner) if v.partner else None) for k, v in ca.items()}
    zc_a = {(b.nm(z.resistor), b.nm(z.end_net) if z.end_net else None, tuple(sorted(b.nm(x) for x in z.far_nets)),
             frozenset(b.nm(c) for c in z.cells), z.reason) for z in a.ctx.base.value("graph", KERNEL_KEY, "theta_schema").zero_cancel}
    zc_b = {(z.resistor, z.end_net, tuple(sorted(z.far_nets)), frozenset(z.cells), z.reason) for z in b.ctx.base.value("graph", KERNEL_KEY, "theta_schema").zero_cancel}
    assert zc_b == zc_a


@pytest.mark.parametrize("name", CIRCUITS)
def test_polarity_flip_keeps_kind_free_plan_counts(pipe, name):
    a, b = pipe.case(name), pipe.case(name, "pol")

    def counts(case):
        coords = collections.Counter(c.role for _, c in case.ctx.base.column("device", "dc_coord"))
        w4 = sum(1 for _, w in case.ctx.base.column("node", "dc_writer") if w.tier == TIER_W4)
        comps = collections.Counter(k for k, _ in case.ctx.base.value("graph", KERNEL_KEY, "theta_schema").components)
        return coords[COORD_WRITER], coords[COORD_DEPENDENT], w4, comps, len(_plan(case.ctx.base, "dc_current_basis").free)

    assert counts(b) == counts(a)
    # 극성이 실제로 바뀌었다(공허하지 않음): MOS kind 가 모두 맞바뀜
    ka = {d.name: d.kind for d in a.td.devices}
    assert {d.name: d.kind for d in b.td.devices} == {n: {"nmos": "pmos", "pmos": "nmos"}[k] for n, k in ka.items()}


# ------------------------------------------------------------------ 고정 θ 평가


@pytest.mark.parametrize("name", CIRCUITS)
def test_fixed_theta_is_sealed_precondition(pipe, name):
    """비교가 공허하지 않도록: 원래 회로 고정 θ 가 봉인 통과 점(`DcEvaluation.sealed`)이다."""
    a = pipe.case(name)
    ev = size_and_seal(a.ctx, _theta0(pipe, name))
    assert ev.sealed is not None, ev.report


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_dc_solution_follows_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    th = _theta0(pipe, name)
    th_b = map_theta(th, b)
    assert set(th_b) == set(b.ctx.base.value("graph", KERNEL_KEY, "theta_schema").components), "θ 키가 옮겨지지 않음(동률 후보 차이) -- 계획 test 참조"
    ea, eb = size_and_seal(a.ctx, th), size_and_seal(b.ctx, th_b)
    assert eb.report.status == ea.report.status
    assert [(i.item, i.status) for i in eb.report.items] == [(i.item, i.status) for i in ea.report.items]
    assert (eb.sealed is None) == (ea.sealed is None)
    sa, sb = ea.snapshot, eb.snapshot
    # 노드전압: 다변수 순환 SCC 노드만 그 SCC 기록 허용오차 안, 나머지 비트 동일
    tol_of = {}
    for log in _plan(sa, "dc_scc_log"):
        if log.method in ITERATIVE:
            for n in log.nodes:
                tol_of[n] = log.tol
    va, vb = dict(sa.column("node", "dc_v")), dict(sb.column("node", "dc_v"))
    assert set(vb) == {b.nm(n) for n in va}
    for n, v in va.items():
        if n in tol_of:
            assert abs(vb[b.nm(n)] - v) <= tol_of[n], (n, v, vb[b.nm(n)], tol_of[n])
        else:
            assert vb[b.nm(n)] == v, (n, v, vb[b.nm(n)])
    assert dict(sb.column("node", "dc_rail_v")) == {b.nm(n): v for n, v in sa.column("node", "dc_rail_v")}
    for f in ("dc_current", "dc_drop_current", "dc_L"):
        assert dict(sb.column("device", f)) == {b.nm(k): v for k, v in sa.column("device", f)}, f
    # 소자 op(ID·gm/ID·W·L·VGS·VDS·VSB): 반복 SCC 노드에 닿지 않는 소자는 비트 동일
    pins = {k: dict(v) for k, v in sa.column("device", "pins")}
    opa, opb = dict(sa.column("device", "dc_op")), dict(sb.column("device", "dc_op"))
    assert set(opb) == {b.nm(k) for k in opa}
    exact = 0
    for k, op in opa.items():
        other = opb[b.nm(k)]
        assert (other.kind, other.current, other.L, other.w_key) == (op.kind, op.current, op.L, op.w_key), k
        if not set(pins[k].values()) & set(tol_of):
            assert other == op, (k, op, other)
            exact += 1
    assert exact > 0


@pytest.mark.parametrize("name", CIRCUITS)
def test_shuffle_and_tag_noise_same_snapshot(pipe, name):
    a, b = pipe.case(name), pipe.case(name, ("shuf", 1))
    th = _theta0(pipe, name)
    ea, eb = size_and_seal(a.ctx, th), size_and_seal(b.ctx, th)
    assert eb.snapshot.fp == ea.snapshot.fp
    assert eb.report == ea.report
