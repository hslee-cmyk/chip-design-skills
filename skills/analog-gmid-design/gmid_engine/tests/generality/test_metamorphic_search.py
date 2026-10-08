"""metamorphic: θ 탐색(search `build_search_context`·`evaluate`·`layer0_start`)이 이름·순서 변형을 따라가는가.

oracle 종류 (a) -- 변형 관계(원래 결과에 치환표를 적용한 것 대 치환한 입력의 결과). 근거(search CONTRACT):
- 3.7 `search_domain`: 변수 = θ 스키마 성분마다 (log, lo, hi) -- lo·hi 는 그 소자 kind 의 LUT 슬라이스·`current_box`·선언 상자에서만
  나온다(이름을 읽지 않는다). 그래서 성분 이름을 치환표로 옮기면 같은 (log, lo, hi). `l_cells` = MOS 마다 kind 의 L 칸(3.4).
- 3.10 `evaluate`: 같은 θ(치환표로 옮김) -> 같은 상태. 목적(3.6) power = Σ_k V_k I_k·area = Σ W·L 은 합 순서만 이름을 따른다 --
  허용 = 합 재배열 상계 n·eps·Σ|항|(sizing CONTRACT 6절 봉인 1·3 이 같은 꼴을 쓴다). b_P(3.6) = Σ_rail |V|·max(...) 도 같은 상계.
  제약 행(3.8): `w_min:<m>`·`seal6_bulk:<m>`·`inversion_floor:<m>` 은 소자마다 그 소자 값만 읽어 비트 동일, 이름은 치환표로.
  `current_cone`(3.5) 행은 유리수 계산. `ss:`·`spec:` 행은 metric·분해능에서 나와 test_metamorphic_metrics 의 허용(분해능)을 따른다.
- 7절 결정론 + 3.21 '난수·시간 없음': 같은 입력(순서 섞기·태그 잡음은 같은 이름 -- authoring CONTRACT 2절 투영 밖)이면 층 0 시작점이
  같다(I-15).
- **이름 치환 뒤 층 0 시작점**: 3.21 1~2 단계(상자 중심·전류 중심)는 변수마다 자기 상자만 읽으므로 중심 평가 결과(출발 상태·실패
  레코드)는 치환표를 따라가야 한다. 3 단계 Halton 시험의 차원 배정은 [r11, r12] 3.21 3a·3.23 `canonical_order`(성분 종류·구조 색·
  궤도 키, 이름은 같은 키 안 tie-break)로 정해지고, 3.23-4 '비트 동일성'이 "이름 치환·원소 순서 섞기에 대해 층 0 시작점(θ·L 칸·t·
  `origin_point`)과 SLSQP 반복·평가 값(봉인 margin, W 하한·반전 하한·원뿔 행, `ss:` 행, 전력·면적·b_P)이 비트 동일"을 계약으로 둔다
  (`test_layer0_start_follows_renaming`. 이 branch 첫 작성 2026-10-08 에는 이름 정렬 차원 배정 때문에 4회로가 실패했고 U2 정준 순서로 해소).
"""
from __future__ import annotations

from gmid_engine.search import STATUS_SEALED, evaluate, layer0_start

import pytest

from .pipeline import map_cells, map_theta

SYNTH = ("syn_cs_load", "syn_diffpair5", "syn_follower")
LIB = ("two_stage_ota", "folded_cascode", "ngcc_3stage_ff")
CIRCUITS = SYNTH + LIB
SEEDS = (0, 1)
EPS = 2.0 ** -52
PER_DEVICE_ROWS = ("w_min", "seal6_bulk", "inversion_floor", "current_cone")


def _theta0(pipe, name):
    theta, res = pipe.theta0(name)
    assert theta is not None, "원래 회로 %s 의 층 0 시작점 없음(stop=%s)" % (name, res.stop)
    return theta


def _row_name(name, case):
    head, sep, tail = name.partition(":")
    if sep and head in PER_DEVICE_ROWS:
        return head + ":" + case.nm(tail)
    return name


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_search_domain_follows_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    da, db = pipe.sctx(a).domain, pipe.sctx(b).domain
    va = {(v.component[0], b.nm(v.component[1])): (v.log, v.lo, v.hi) for v in da.variables}
    vb = {v.component: (v.log, v.lo, v.hi) for v in db.variables}
    assert vb == va
    assert dict(db.l_cells) == {b.nm(m): c for m, c in da.l_cells}
    assert (db.current_box, db.w_min_m, db.grid_m, db.area_resolution_m2) == (
        da.current_box, da.w_min_m, da.grid_m, da.area_resolution_m2)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_evaluate_fixed_theta_follows_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    (th, cells) = _theta0(pipe, name)
    sa, sb = pipe.sctx(a), pipe.sctx(b)
    ra = evaluate(sa, th, map_cells(cells, a, sa.domain))
    rb = evaluate(sb, map_theta(th, b), map_cells(cells, b, sb.domain))
    assert ra.status == STATUS_SEALED                   # 비교가 공허하지 않음(봉인 점)
    assert rb.status == ra.status
    oa, ob = ra.objectives, rb.objectives
    volts = dict(ra.evaluation.snapshot.column("node", "dc_rail_v"))
    rails = [abs(volts[r] * i) for r, i in oa.per_rail]
    gates = [op.W * op.L for _, op in ra.evaluation.snapshot.column("device", "dc_op")]
    assert abs(ob.power_w - oa.power_w) <= len(oa.per_rail) * EPS * sum(rails)
    assert abs(ob.gate_area_m2 - oa.gate_area_m2) <= len(gates) * EPS * sum(gates)
    assert abs(ob.area_m2 - oa.area_m2) <= len(gates) * EPS * max(oa.area_m2, sum(gates))
    if oa.power_resolution_w is None:
        assert ob.power_resolution_w is None
    else:
        assert abs(ob.power_resolution_w - oa.power_resolution_w) <= len(oa.per_rail) * EPS * oa.power_resolution_w
    assert dict(ob.per_rail).keys() == {b.nm(r) for r, _ in oa.per_rail}
    assert tuple(sorted(ob.passive_area_undeclared)) == tuple(sorted(b.nm(x) for x in oa.passive_area_undeclared))
    ca = {_row_name(r.name, b): r for r in ra.constraints}
    cb = {r.name: r for r in rb.constraints}
    assert set(cb) == set(ca)
    for n, r in ca.items():
        if n.split(":", 1)[0] in PER_DEVICE_ROWS:
            assert (cb[n].c, cb[n].active) == (r.c, r.active), n
    assert sorted(rb.unmeasured) == sorted(ra.unmeasured)


@pytest.mark.parametrize("name", CIRCUITS)
def test_layer0_centre_follows_renaming(pipe, name):
    """3.21 1~2 단계(상자 중심·전류 중심)의 출발 평가: 상태와 실패 레코드(분류·소자 -- 치환표로)가 같다."""
    a, b = pipe.case(name), pipe.case(name, ("ren", 1))
    _, la = pipe.theta0(name)
    lb = layer0_start(pipe.fresh_sctx(b))
    assert lb.start_status == la.start_status
    if la.start_failure is None:
        assert lb.start_failure is None
    else:
        fa, fb = la.start_failure, lb.start_failure
        assert (fb.failure_class, tuple(sorted(fb.devices))) == (fa.failure_class, tuple(sorted(b.nm(d) for d in fa.devices)))
        assert dict(fb.detail).get("reason") == dict(fa.detail).get("reason")


@pytest.mark.parametrize("name", CIRCUITS)
def test_layer0_start_follows_renaming(pipe, name):
    """층 0 시작점(θ·L 칸·t)이 치환표를 따라간다 -- 이름은 결과를 바꾸면 안 된다(사용자 대원칙, 모듈 docstring)."""
    a, b = pipe.case(name), pipe.case(name, ("ren", 1))
    (th, cells), la = pipe.theta0(name)[0], pipe.theta0(name)[1]
    lb = layer0_start(pipe.fresh_sctx(b))
    assert lb.start is not None, lb.stop
    assert dict(lb.start.theta) == map_theta(th, b), (la.origin_point, lb.origin_point, la.t, lb.t)
    assert lb.start.cells == map_cells(cells, b, pipe.sctx(b).domain)
    assert (lb.origin_point, lb.t) == (la.origin_point, la.t)


@pytest.mark.parametrize("name", CIRCUITS)
def test_layer0_start_same_after_shuffle_and_tag_noise(pipe, name):
    a, b = pipe.case(name), pipe.case(name, ("shuf", 1))
    (th, cells), la = pipe.theta0(name)[0], pipe.theta0(name)[1]
    lb = layer0_start(pipe.fresh_sctx(b))
    assert lb.start is not None and dict(lb.start.theta) == th
    assert dict(zip([m for m, _ in pipe.sctx(b).domain.l_cells], lb.start.cells)) == cells
    assert (lb.origin_point, lb.t, lb.kernel_calls) == (la.origin_point, la.t, la.kernel_calls)
