"""`converge_point(sctx, pdk, point) -> ConvergedPoint` -- front 점 하나의 W_request 루프 (CONTRACT 7절·11절 불변식 2~6, 계획 LY3·LY5·LY7, N3.6 K_max).

oracle (a) 합성 픽스처: `place_layout` 을 스크립트 가짜(호출마다 손으로 정한 배치 -> 실현 기하)로, `evaluate` 를 가짜 커널(기하 지문마다 처음 한 번만
`sctx.counters["kernel_calls"] += 1` -- 캐시 모형, 결과의 통과·실패는 스크립트)로 바꾼다. 수동소자 값은 [U17 ①] 평가 스냅샷의 S2 필드
`device.passive_value`(설계 40 §2.4.8 -- 가짜 스냅샷엔 열이 없어 빈 값)이고, 면적 입력 변환 `passives_from_decl` 만 가짜(빈 값)다. 기대 상태·반복 수·K_max·margin 은 스크립트와 계획 N3.6(반감 횟수) 에서 손으로 센다.

oracle (b)·(d) 실경로(뒤쪽): 실 LUT v2 + sky130 + common_gate_amplifier·two_stage_ota 손 봉인 점에서 스파이로 커널 계수를 잰다(불변식 2·3·4·8),
접합 용량은 BSIM4 폐형식(metrics CONTRACT 8.2, ngspice 대조식)을 test 가 직접 계산해 맞춘다.
"""
from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from gmid_engine.convergence import (
    STATUS_CONVERGED,
    STATUS_INFEASIBLE,
    STATUS_NONCONVERGENT,
    STATUS_UNPLACEABLE,
    JunctionChange,
    PlacedLayout,
    converge_point,
)
from gmid_engine.core import fp_of
from gmid_engine.search import FrontPoint

from .conftest import (
    GRID,
    FakeSnapshot,
    bsim4_junction,
    ddiff,
    eval_result,
    floorplan,
    isclose,
    layout,
    module,
    op,
    pdk,
    placement,
    rows,
    ssdev,
)

SIZED_W = 1e-6


def snap(W=SIZED_W, current=1e-6, cdb=1e-15, csb=2e-15):
    return FakeSnapshot({("device", "dc_op"): {"M1": op(W=W, current=current)}, ("device", "ss_dev"): {"M1": ssdev(cdb, csb)}})


class Loop:
    """스크립트: `layouts` = place_layout 호출마다 (W, 키, nf, pending, tol, 확산 ad, 면적) 또는 "unplaced";
    `verdict(geometry, n)` = n 번째 커널 호출 결과 종류 ("ok" | "fail" | "lost")."""

    def __init__(self, layouts, verdict=lambda g, n: "ok", pdk_keys=(("nmos", (10, 20, 30)),)):
        self.layouts, self.verdict = list(layouts), verdict
        self.place_args, self.eval_args, self.cache, self.kernel_n = [], [], {}, 0
        self.pdk = pdk(pdk_keys)

    # -- 가짜 place_layout (CONTRACT 7절 시그니처)
    def place_layout(self, memo, snapshot, pdk_, passives, rejected, relaxed, first_seen, previous, kinds, current_keys):
        n = len(self.place_args)
        self.place_args.append(SimpleNamespace(memo=memo, snapshot=snapshot, pdk=pdk_, rejected=rejected, relaxed=relaxed,
                                               previous=previous, kinds=kinds, current_keys=current_keys, sctx_kernel=None))
        spec = self.layouts[min(n, len(self.layouts) - 1)]
        if spec == "unplaced":
            lay = layout()
            return PlacedLayout(lay, None, (), (), ("M1",), (), pdk_, frozenset(relaxed), dict(first_seen), 1, ())
        W, key, nf, pending, tol, ad, area = spec
        pl = (placement("M1", key, nf, W, pending=pending, tol=tol),)
        diff = () if ad is None else (ddiff("M1", key * GRID, nf, ad, ad, 1e-6, 1e-6),)
        lay = layout(diffusion=diff, plan=floorplan(1e-5, 1e-5, area=area))
        return PlacedLayout(lay, None, (("gx", "members_span_row_groups"),), pl, (), (("nmos", key),), pdk_, frozenset(relaxed),
                            dict(first_seen), 1, ())

    # -- 가짜 evaluate (search CONTRACT 10절 시그니처 + geometry=)
    def evaluate(self, sctx, theta, cells, parent=None, origin=(), geometry=None):
        self.eval_args.append(SimpleNamespace(theta=theta, cells=cells, parent=parent, geometry=geometry))
        key = fp_of(geometry)
        if key in self.cache:
            return self.cache[key]
        sctx.counters["kernel_calls"] += 1
        self.kernel_n += 1
        kind = self.verdict(geometry, self.kernel_n)
        W = dict(geometry.w_request)["M1"]
        s = snap(W=W, cdb=1e-15 * self.kernel_n, csb=3e-15 * self.kernel_n)
        if kind == "ok":
            r = eval_result(s, power=1e-3 + self.kernel_n * 1e-6, constraints=rows(2.0, 0.5), tag="eval%d" % self.kernel_n)
        elif kind == "lost":       # 봉인·c >= 0 이지만 출발 점이 재던 (metric, op) 를 새로 못 잼
            r = eval_result(s, constraints=rows(2.0), unmeasured=(("gain_ss_db", ">=", "x"),), tag="lost%d" % self.kernel_n)
        else:
            r = eval_result(s, constraints=rows(2.0, -0.25), failure=None, tag="fail%d" % self.kernel_n)
        self.cache[key] = r
        return r


@pytest.fixture
def run(monkeypatch):
    mod = module("converge_point")

    def go(loop, start=None):
        monkeypatch.setattr(mod, "place_layout", loop.place_layout)
        monkeypatch.setattr(mod, "evaluate", loop.evaluate)
        # [U17 ①, 설계 40 §2.4.7·§2.4.8] 수동소자 값은 평가 스냅샷의 S2 필드 `device.passive_value` 를 읽는다(converge_point 가
        # passive_values·check_theta 를 다시 부르지 않는다) -- 가짜 스냅샷에는 그 열이 없어 빈 값이고, 면적 입력 변환만 가짜로 둔다.
        monkeypatch.setattr(mod, "passives_from_decl", lambda decl, values: ())
        sctx = SimpleNamespace(counters={"kernel_calls": 0}, area_decl=None,
                               dc=SimpleNamespace(schema=None, lut=SimpleNamespace(memo="MEMO", w_keys=(("nmos", 30),))))
        start = start or eval_result(snap(), power=2e-3, area=7e-11, constraints=rows(3.0), tag="start")
        point = FrontPoint("p0", start, ())
        return converge_point(sctx, loop.pdk, point), sctx, start
    return go


def lay(W, key=10, nf=2, pending=False, tol=0.01, ad=None, area=1e-10):
    return (W, key, nf, pending, tol, ad, area)


# ---------------------------------------------------------------- 고정점·재평가 계수 (불변식 3·4)

def test_fixed_point_converges_after_one_reevaluation(run):
    loop = Loop([lay(2e-6, area=3e-10), lay(2e-6, area=3e-10)])
    cp, sctx, start = run(loop)
    assert cp.status == STATUS_CONVERGED and cp.failure is None
    assert len(loop.place_args) == 2 and len(loop.eval_args) == 1
    assert cp.kernel_calls == 1 == sctx.counters["kernel_calls"]
    assert [(i.index, i.status, i.kernel_calls) for i in cp.iterations] == [(1, "sealed", 1)]
    assert cp.result.tag == "eval1"
    assert cp.geometry == loop.eval_args[-1].geometry                    # 불변식 4: 마지막 기하 == 마지막 통과 재평가의 기하
    assert cp.geometry.w_request == (("M1", 2e-6),) and cp.geometry.w_keys == (("nmos", 10),)
    # evaluate 는 출발 점의 θ·L 칸으로, parent = 현재 점(처음엔 출발 점)
    assert loop.eval_args[0].theta == start.theta and loop.eval_args[0].cells == start.key.cells
    assert loop.eval_args[0].parent is start
    # 두 번째 레이아웃은 재평가 점의 스냅샷으로, 커널 키 = 재평가 기하의 키
    assert loop.place_args[1].snapshot is cp.result.evaluation.snapshot
    assert loop.place_args[0].current_keys == (("nmos", 30),) and loop.place_args[1].current_keys == (("nmos", 10),)
    assert loop.place_args[0].kinds == {"M1": "nmos"} and loop.place_args[0].memo == "MEMO"
    # k_max: |ln 2| / tol 0.01 = 69.3 -> 반감 7회 (계획 N3.6)
    assert cp.k_max == 7
    assert cp.layout_calls == 2
    assert cp.layout_area_m2 == 3e-10 and cp.search_area_m2 == 7e-11
    assert (cp.power_w, cp.power_resolution_w) == (cp.result.objectives.power_w, cp.result.objectives.power_resolution_w)
    assert cp.junction == (JunctionChange("M1", 1e-15, 2e-15, 1e-15, 3e-15),)
    assert cp.undelivered == (("gx", "members_span_row_groups"),)
    assert cp.unmatched == () and cp.rejected == () and cp.excluded == ()


def test_diffusion_only_change_is_reevaluated_not_a_cycle(run):
    # 같은 W·키, 확산만 다름 -> 다른 기하라 재평가(주기 아님) -> 같은 기하 재등장 -> 수렴
    loop = Loop([lay(2e-6, ad=1e-13), lay(2e-6, ad=2e-13), lay(2e-6, ad=2e-13)])
    cp, sctx, _ = run(loop)
    assert cp.status == STATUS_CONVERGED
    assert [i.status for i in cp.iterations] == ["sealed", "sealed"]
    assert cp.kernel_calls == 2 == sctx.counters["kernel_calls"]
    assert dict(cp.geometry.diffusion)["M1"].ad_m2 == 2e-13


# ---------------------------------------------------------------- K_max (불변식 5)

def test_k_max_reached_is_nonconvergent(run):
    # 첫 배치 W 1.03 (ln 1.03 = 0.02956), tol 0.01 -> 2.956 -> 반감 2회 -> K_max 2. 기하가 매번 달라 고정점이 없다.
    loop = Loop([lay(1.03e-6), lay(1.02e-6), lay(1.025e-6), lay(1.021e-6)])
    cp, sctx, _ = run(loop)
    assert cp.k_max == 2
    assert cp.status == STATUS_NONCONVERGENT
    assert len(cp.iterations) == 2 == len(loop.eval_args) == sctx.counters["kernel_calls"]
    assert cp.failure.failure_class == "NONCONVERGENT"
    detail = dict(cp.failure.detail)
    assert detail["cycle"] is False and detail["k_max"] == 2 and detail["iterations"] == 2
    # margin = 그때 배치의 max|ln(W/W_사이징)| / tol = ln 1.025 / 0.01
    assert cp.failure.margin == pytest.approx(math.log(1.025) / 0.01, rel=1e-12)
    assert cp.result.tag == "eval2"                                   # 마지막 통과 재검증 점
    assert cp.geometry.w_request == (("M1", 1.025e-6),)              # 마지막 레이아웃 기하(평가 안 함)


def test_exact_cycle_is_detected_before_k_max(run):
    # A -> B -> A: 같은 상태에서 직전보다 앞서 평가한 DC 상태로 돌아옴 = 주기. K_max = 7(ln 2 / 0.01) 보다 일찍 끝난다.
    A, B = lay(2e-6), lay(2.1e-6)
    loop = Loop([A, B, A, B, A])
    cp, sctx, _ = run(loop)
    assert cp.status == STATUS_NONCONVERGENT
    assert dict(cp.failure.detail)["cycle"] is True
    assert len(cp.iterations) == 2 < cp.k_max == 7
    assert sctx.counters["kernel_calls"] == 2 and len(loop.place_args) == 3


# ---------------------------------------------------------------- 거부·제외·실패 (LY3, CONTRACT 7절)

def test_pending_request_rejected_then_converges(run):
    # 1회: W_request 응답 대기 소자 M1 로 평가 -> 제약 위반 -> 거부(rejected), 같은 current 로 다시 놓는다
    loop = Loop([lay(2e-6, pending=True), lay(1.5e-6), lay(1.5e-6)], verdict=lambda g, n: "fail" if n == 1 else "ok")
    cp, _sctx, start = run(loop)
    assert cp.status == STATUS_CONVERGED
    assert [(i.status, i.requested, i.rejected) for i in cp.iterations] == [("rejected", ("M1",), ("M1",)), ("sealed", (), ())]
    assert cp.iterations[0].margin == -0.25                           # 실패 margin = 가장 작은 c
    assert loop.place_args[1].rejected == frozenset({"M1"})
    assert loop.place_args[1].snapshot is start.evaluation.snapshot    # 거부 뒤에도 같은 current
    assert cp.rejected == ("M1",)


def test_key_exclusion_then_infeasible_when_no_key_left(run):
    loop = Loop([lay(2e-6, key=20), lay(1.5e-6, key=10)], verdict=lambda g, n: "fail", pdk_keys=(("nmos", (10, 20)),))
    cp, sctx, start = run(loop)
    assert cp.status == STATUS_INFEASIBLE
    assert [(i.status, i.excluded) for i in cp.iterations] == [("excluded", (("nmos", 20),)), ("failed", ())]
    assert cp.excluded == (("nmos", 20),)
    assert loop.place_args[1].pdk.slice_width_keys == (("nmos", (10,)),)      # 뺀 키 없이 다시 놓는다
    assert cp.result is None                                                  # 통과한 재검증 없음
    notes = dict(cp.notes)
    assert notes["violated_rows"] == (("r1", -0.25),)
    assert sctx.counters["kernel_calls"] == 2


def test_excluded_retries_do_not_count_toward_k_max(run):
    # 첫 배치 ln 1.005 <= tol 0.01 -> K_max 1. 1회 실패 -> 키 제외(세지 않음), 2회 통과, 3번째 레이아웃 = 고정점 -> 수렴
    loop = Loop([lay(1.005e-6, key=20), lay(1.004e-6, key=10), lay(1.004e-6, key=10)],
                verdict=lambda g, n: "fail" if n == 1 else "ok", pdk_keys=(("nmos", (10, 20)),))
    cp, _sctx, _ = run(loop)
    assert cp.k_max == 1
    assert cp.status == STATUS_CONVERGED
    assert [i.status for i in cp.iterations] == ["excluded", "sealed"]


def test_lost_measurement_is_not_accepted(run):
    # 봉인·c >= 0 이어도 출발 점이 재던 (metric, op) 를 새로 미측정으로 잃으면 통과가 아니다(CONTRACT 7절 accepted)
    loop = Loop([lay(2e-6, key=20), lay(2e-6, key=10)], verdict=lambda g, n: "lost", pdk_keys=(("nmos", (10, 20)),))
    cp, _sctx, _ = run(loop)
    assert cp.status == STATUS_INFEASIBLE
    assert cp.result is None
    assert [i.status for i in cp.iterations] == ["excluded", "failed"]


# ---------------------------------------------------------------- 레이아웃 전 종료

def test_nonpositive_current_is_unplaceable_without_layout(run):
    loop = Loop([lay(2e-6)])
    start = eval_result(snap(current=0.0), tag="start")
    cp, sctx, _ = run(loop, start=start)
    assert cp.status == STATUS_UNPLACEABLE
    assert dict(cp.notes)["nonpositive_current"] == ("M1",)
    assert loop.place_args == [] and loop.eval_args == []
    assert (cp.layout_calls, cp.kernel_calls, cp.k_max, cp.result, cp.layout) == (0, 0, None, None, None)


def test_unplaced_device_is_unplaceable(run):
    loop = Loop(["unplaced"])
    cp, sctx, _ = run(loop)
    assert cp.status == STATUS_UNPLACEABLE
    assert dict(cp.notes)["unplaced_devices"] == ("M1",)
    assert loop.eval_args == [] and sctx.counters["kernel_calls"] == 0
    assert cp.result is None and cp.layout_calls == 1


# ---------------------------------------------------------------- 실경로 (실 LUT v2 + sky130, 손 봉인 점)

REAL = ("common_gate_amplifier", "two_stage_ota")


@pytest.mark.parametrize("name", REAL)
def test_real_kernel_counts_and_fixed_point(real, name):
    r = real.run(name)
    cp, spy = r.point, r.spy
    assert r.start.status == "sealed" and all(row.c >= 0 for row in r.start.constraints)     # 출발 조건(손 봉인 점)
    assert cp.status == STATUS_CONVERGED, (cp.status, cp.notes, cp.failure)
    # 불변식 2: place_layout 전후 커널 계수 불변(레이아웃 안 재시도는 커널 0)
    assert spy.place and all(before == after for before, after, _p, _g in spy.place)
    # 불변식 3: 재평가 = 레이아웃 결과마다 1회, 새 기하라 커널 1회씩
    assert len(spy.evals) == len(cp.iterations) == len(spy.place) - 1
    assert all(after - before == 1 for before, after, _g, _r, _p in spy.evals)
    assert all(i.kernel_calls == 1 for i in cp.iterations)
    assert cp.kernel_calls == len(cp.iterations) == r.sctx.counters["kernel_calls"] - spy.start_kernel
    # 불변식 4: 마지막 place_layout 기하 == 마지막 통과 재평가의 기하 == ConvergedPoint.geometry, 평가 키의 고정 W 지문
    assert spy.place[-1][3] == spy.evals[-1][2] == cp.geometry
    assert cp.result is spy.evals[-1][3]
    assert cp.result.key.w_fixed_fp == fp_of(cp.geometry)
    assert cp.result.key.cells == r.start.key.cells and cp.result.theta == r.start.theta
    # 불변식 5: 제외 아닌 반복 수 <= K_max
    assert sum(1 for i in cp.iterations if i.status != "excluded") <= cp.k_max
    # 재평가 점은 고정 W 를 그대로 이행한다(구성: w_request 가 dc_op.W)
    ops = dict(cp.result.evaluation.snapshot.column("device", "dc_op"))
    assert {m: ops[m].W for m in ops} == dict(cp.geometry.w_request)
    # 실현 W = nf x finger_w (레이아웃 소자 기록에서 손으로)
    for d in cp.layout.devices:
        assert dict(cp.geometry.w_request)[d.name] == pytest.approx(d.n_fingers * d.finger_w_m, rel=1e-15)
    # 판정 축 값의 출처
    assert cp.layout_area_m2 == cp.layout.floorplan.outline_area_m2
    assert cp.search_area_m2 == r.start.objectives.area_m2
    assert cp.power_w == cp.result.objectives.power_w


@pytest.mark.parametrize("name", REAL)
def test_real_junction_caps_from_realized_diffusion(real, name):
    """불변식 8 + DEC-91 (2): 재검증 점의 cdb·csb = 실현 확산 기하(ly.diffusion)와 PDK 접합 파라미터로 BSIM4 폐형식을 test 가 직접 푼 값."""
    from gmid_engine.metrics import JunctionParams
    r = real.run(name)
    cp = r.point
    diffusion = {d.name: d for d in cp.layout.diffusion}
    assert diffusion, "레이아웃이 확산 기하를 내지 않았다"
    ss = dict(cp.result.evaluation.snapshot.column("device", "ss_dev"))
    ops = dict(cp.result.evaluation.snapshot.column("device", "dc_op"))
    temp = r.sctx.junction.temp_c
    for m, d in diffusion.items():
        assert ss[m].junction_model == "pdk_bsim4_layout_diffusion"
        params = JunctionParams.from_pdk_decl(real.env.pdk, ops[m].kind)
        cdb, csb = bsim4_junction(params, d.finger_w_m, d.ad_m2, d.as_m2, d.pd_m, d.ps_m, float(d.n_fingers),
                                  ops[m].vds + ops[m].vsb, ops[m].vsb, temp)
        assert isclose(ss[m].cdb, cdb, 1e-12) and isclose(ss[m].csb, csb, 1e-12), (m, ss[m].cdb, cdb, ss[m].csb, csb)
    # 레이아웃 전(출발 점)은 LUT 생성 규칙 기하
    before = dict(r.start.evaluation.snapshot.column("device", "ss_dev"))
    assert {s.junction_model for s in before.values()} == {"pdk_bsim4_lut_rule_diffusion"}
    # junction 기록 = 출발 점 -> 재검증 점
    assert {j.device: (j.cdb_before, j.csb_before, j.cdb_after, j.csb_after) for j in cp.junction} == {
        m: (before[m].cdb, before[m].csb, ss[m].cdb, ss[m].csb) for m in ss}


@pytest.mark.parametrize("name", REAL)
def test_real_same_geometry_reevaluation_is_cache_hit(real, name):
    """같은 (θ, 기하)는 커널 0(평가 캐시) -- 불변식 3 '같은 기하 재방문은 커널 0'."""
    from gmid_engine.search import evaluate
    r = real.run(name)
    cp = r.point
    k0 = r.sctx.counters["kernel_calls"]
    again = evaluate(r.sctx, r.start.theta, r.start.key.cells, parent=cp.result, geometry=cp.geometry)
    assert r.sctx.counters["kernel_calls"] == k0
    assert again is cp.result
