"""metamorphic: 소신호·DC metric(metrics `ss_evaluate` -- `ss_dev`·`metrics_ss`·`metrics_dc`)이 이름·순서 변형을 따라가는가.

oracle 종류 (a) -- 변형 관계. 원래 회로의 봉인 점(고정 θ, 층 0 시작점 -- 입력)과 이름을 치환한 회로의 같은 θ(치환표로 옮김)를
평가해 metric 을 비교한다. 근거(metrics CONTRACT):
- 1절·I-7 '노드 재번호 불변', 7.7 S-8 '넷 이름 전단사 뒤 metric 값 같음(노드 인덱스는 이름 정렬 위치뿐)'. 이름 치환은 노드 인덱스를
  바꾸므로 MNA 행·열 순서와 공유 격자 근(근 = 행렬 고유값)의 반올림이 바뀐다 -- 7.4 가 "공유 격자가 달라 마지막 자리가 다를 수
  있다(격자 점 수는 불변식 대상이 아니다, 3.5)"고 적는다. 그래서 소신호 metric 은 **그 metric 의 분해능 안**(9절 `MetricResult.
  resolution` = max(LUT 1차 최악 전파, MNA 사후 오차 전파) -- 이 값보다 작은 차는 계약상 구별되지 않는다)에서 같아야 하고, 정의
  불가면 같은 code 로 정의 불가여야 한다. 실제 차는 기록용으로 함께 잰다.
- 7.5 전력·면적: `power_dc_w` = Σ_k V_k·I_k(레일 노드 인덱스 = 이름 정렬), `area_search_m2` = Σ W·L. 이름 치환은 합의 순서만
  바꾼다. 허용 = 부동소수 합 재배열 상계 n·eps·Σ|항| -- 계약이 같은 꼴을 이미 허용오차로 쓴다(sizing CONTRACT 6절 봉인 1
  'n·eps·max|V|', 봉인 3 'n·eps·Σ|I|'). 레일별 전류(`per_rail_amp`)는 레일마다 같은 원소 합이라 같은 상계.
- 순서 섞기·태그 잡음: 이름이 같으므로 결정론(I-3, sizing 9절)으로 결과 스냅샷 지문까지 같다.
- 극성 뒤집기: 실 LUT 는 nmos·pmos 가 달라 metric 값이 같을 근거가 계약에 없다 -- 이 파일은 극성 값을 비교하지 않는다(분류 수준
  거울은 test_metamorphic_matching·test_metamorphic_sizing).
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.sizing import METRICS_KEY, size_and_seal
from gmid_engine.metrics import ss_evaluate

from .pipeline import map_theta

SYNTH = ("syn_cs_load", "syn_diffpair5", "syn_follower")
LIB = ("two_stage_ota", "folded_cascode", "ngcc_3stage_ff")
CIRCUITS = SYNTH + LIB
SEEDS = (0, 1)
EPS = 2.0 ** -52


def _evaluate(pipe, case, theta):
    ev = size_and_seal(case.ctx, theta)
    assert ev.sealed is not None, ev.report
    sc = pipe.sctx(case)
    return ss_evaluate(ev.sealed, case.ctx, theta, sc.ss_constraints, junction=pipe.env.junction)


def _theta0(pipe, name):
    theta, res = pipe.theta0(name)
    assert theta is not None, "원래 회로 %s 의 층 0 시작점 없음(stop=%s)" % (name, res.stop)
    return theta[0]


def _entries(bundle):
    return [(req.metric, res) for req, res in bundle.entries]


def _codes(res):
    return sorted(u.code for u in (res.undefined or ()))


def _rail_terms(dc_detail, snapshot):
    rails = dict(snapshot.column("node", "dc_rail_v"))
    return [abs(rails[r] * i) for r, i in dict(dc_detail)["per_rail_amp"]]


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("name", CIRCUITS)
def test_metrics_follow_renaming(pipe, name, seed):
    a, b = pipe.case(name), pipe.case(name, ("ren", seed))
    th = _theta0(pipe, name)
    ra, rb = _evaluate(pipe, a, th), _evaluate(pipe, b, map_theta(th, b))
    # ---- DC: 전력·면적·레일 전류
    da, db = _entries(ra.dc), _entries(rb.dc)
    assert [m for m, _ in db] == [m for m, _ in da]
    terms = _rail_terms(ra.dc.detail, ra.snapshot)
    area_terms = [op.W * op.L for _, op in ra.snapshot.column("device", "dc_op")]
    bound = {"power_dc_w": len(terms) * EPS * sum(terms), "area_search_m2": len(area_terms) * EPS * sum(area_terms)}
    for (m, x), (_, y) in zip(da, db):
        assert _codes(y) == _codes(x), m
        if x.value is None:
            assert y.value is None, m
            continue
        assert abs(y.value - x.value) <= bound.get(m, 0.0), (m, x.value, y.value)
    pa = dict(dict(ra.dc.detail)["per_rail_amp"])
    pb = dict(dict(rb.dc.detail)["per_rail_amp"])
    assert set(pb) == {b.nm(r) for r in pa}
    for r, i in pa.items():
        assert abs(pb[b.nm(r)] - i) <= len(pa) * EPS * sum(abs(v) for v in pa.values()), r
    # ---- 소신호: 같은 요청 순서, 값은 분해능 안, 정의 불가는 같은 code
    sa, sb = _entries(ra.ss), _entries(rb.ss)
    assert [m for m, _ in sb] == [m for m, _ in sa]
    for (m, x), (_, y) in zip(sa, sb):
        assert _codes(y) == _codes(x), (m, x.undefined, y.undefined)
        if x.value is None:
            assert y.value is None, m
            continue
        assert x.resolution is not None and y.resolution is not None, (m, "분해능 없음 -- 허용 근거 없음")
        assert abs(y.value - x.value) <= max(x.resolution, y.resolution), (m, x.value, y.value, x.resolution)
    assert dict(ra.ss.approximations) == dict(rb.ss.approximations)


@pytest.mark.parametrize("name", CIRCUITS)
def test_metrics_same_snapshot_after_shuffle_and_tag_noise(pipe, name):
    a, b = pipe.case(name), pipe.case(name, ("shuf", 1))
    th = _theta0(pipe, name)
    ra, rb = _evaluate(pipe, a, th), _evaluate(pipe, b, th)
    assert rb.snapshot.fp == ra.snapshot.fp
    assert rb.ss == ra.ss and rb.dc == ra.dc


def test_metric_inputs_are_nontrivial(pipe):
    """공허한 통과 방지: 비교 대상에 값 있는 소신호 metric(gain·GBW·PM 중 하나 이상)과 전력·면적이 실제로 있다."""
    seen = set()
    for name in CIRCUITS:
        r = _evaluate(pipe, pipe.case(name), _theta0(pipe, name))
        seen.update(m for m, res in _entries(r.ss) if res.value is not None and math.isfinite(res.value))
        assert all(res.value is not None for m, res in _entries(r.dc) if m in ("power_dc_w", "area_search_m2"))
    assert seen & {"gain_ss_db", "gbw_ss_hz", "pm_ss_deg"}, seen
