"""tests/convergence 공용 -- MOD8 수렴(U14) 독립 test 입력.

근거: `gmid_engine/convergence/CONTRACT.md`(주장으로 읽는다), 설계 40 §3.9 MOD8·§11 U14(+U12 인계), 계획 N3.17 LY1~LY8·N3.6 K_max,
체크리스트 D-M8·R12. 기대값은 이 파일·각 test 의 손계산과 독립 출처(topology JSON·PDK 선언·BSIM4 폐형식)에서만 만든다 -- 피검 함수로 만들지 않는다.

두 종류의 입력:
1. **합성 픽스처**(이 파일 앞부분): layout 출력 계약(`layout.contract_output`) 레코드를 손으로 만들고, 스냅샷·EvalResult·sctx 는 피검 코드가 읽는
   속성만 가진 가짜(`FakeSnapshot`·`SimpleNamespace`)다. [U17 1-e] design 40 v1.6 §2.4.7: `LayoutResult` 는 (설계점 스냅샷, 계산 블록 목록)뿐이고
   MOD8 은 레이아웃 값을 그 스냅샷의 `ly_*` 필드(layout `LAYOUT_KEY`·`F_*`)로 읽는다 -- 합성 `layout()` 은 손 레코드를 그 필드 이름으로 담은
   `FakeSnapshot` 을 든 `LayoutResult` 다. 루프 test 는 `place_layout`·`evaluate` 를 스크립트 가짜로 바꾸고(monkeypatch)
   가짜 `evaluate` 가 기하 지문마다 한 번만 `sctx.counters["kernel_calls"]` 를 올린다(커널 캐시 모형).
2. **실경로**(뒷부분 `RealPath`): 실 LUT v2 + sky130 선언 + library 회로(generality `pipeline.Env/Pipe`). 탐색이 front 를 내지 못하는 동안
   (설계 40 §3.9 gap (e)) 손으로 봉인한 점을 쓴다 -- 층 0 θ 에서 `ln_idu` 성분을 모두 `REAL_LN_IDU` 로 옮기고 `current` 성분을 `REAL_CURRENT_SCALE`
   배 한다(봉인·제약 행 c >= 0 은 test 가 확인하는 출발 조건이지 기대값이 아니다).
"""
from __future__ import annotations

import importlib
import math
from types import SimpleNamespace

import pytest

from gmid_engine.layout import F_DEVICE, F_DIFFUSION, F_FINGER, F_FLOORPLAN, F_GROUPS, F_GROUPS_IN, LAYOUT_KEY, LayoutPdk
from gmid_engine.layout.contract_input import PDK_RULE_QUANTITIES
from gmid_engine.layout.contract_output import (
    DeviceDiffusion,
    DeviceFinger,
    FloorplanSummary,
    GroupAttempt,
    GroupLayout,
    LayoutResult,
)
from gmid_engine.convergence import ConvergedPoint, Placement
from gmid_engine.search import ConstraintRow

GRID = 1e-8                     # 합성 제조 격자 1e-8 m (2진 분수 아님 -- 비교는 같은 식으로 만든 값끼리만)
STATUS_SEALED = "sealed"        # search CONTRACT 상태 낱말(search_values STATUS_SEALED)


# ---------------------------------------------------------------- layout 출력 레코드 (layout CONTRACT 4.2 필드 순서)

def floorplan(w, h, grid=GRID, area=None, passive=0.0, included=()):
    """FloorplanSummary: bbox w x h, 외곽 면적 = area(없으면 w*h)."""
    return FloorplanSummary(w, h, w * h if area is None else area, grid, w / h, 1.0, (), included, passive)


def dlay(name, fw, nf, W, tol=0.01):
    """놓인 소자: (이름, `ly_finger` 값 DeviceFinger). W = 실현 W(손으로 준다). 폭 키 = fw / 격자(손으로 고른 값이 정수 근처)."""
    return (name, DeviceFinger(name, round(fw / GRID), fw, nf, W, W, 0.0, tol / 2, tol, tol, False, True, "row", None, None))


def dunplaced(name, tol=0.01):
    """놓지 못한 소자: `ly_device` 에는 있고 `ly_finger` 값이 없다."""
    return (name, None)


def attempt(fw, nfs, step="w_request", ok=False, reason=""):
    return GroupAttempt(step, None, fw, tuple(nfs), tuple(n * fw for n in nfs), None, None, None, ok, reason)


def glay(gid, role, members, pattern=None, pending=False, attempts=(), reason="", dx=None, dy=None, ok=False):
    return GroupLayout(gid, role, tuple(members), pattern, None, None, None, (), (), None, None, None, dx, dy, ok, pending,
                       pending, reason, tuple(attempts), ())


def ddiff(name, fw, nf, ad, as_, pd, ps):
    return DeviceDiffusion(name, fw, nf, ad, as_, pd, ps)


def layout(devices=(), groups=(), diffusion=(), plan=None, groups_in=()):
    """손 레이아웃 결과: 레이아웃 필드(`ly_device`·`ly_finger`·`ly_groups`·`ly_groups_in`·`ly_floorplan`·`ly_diffusion`)를 든 FakeSnapshot 의
    `LayoutResult(snapshot)`(O-17 (3) 뒤 칸은 스냅샷 하나). `devices` = `dlay`/`dunplaced` 항목, `groups_in` = 입력 그룹(gid·hub_net)."""
    fields = {
        ("device", F_DEVICE): {n: SimpleNamespace(name=n) for n, _f in devices},
        ("device", F_FINGER): {n: f for n, f in devices if f is not None},
        ("graph", F_GROUPS): {LAYOUT_KEY: tuple(groups)},
        ("graph", F_GROUPS_IN): {LAYOUT_KEY: tuple(groups_in)},
        ("graph", F_FLOORPLAN): {LAYOUT_KEY: plan if plan is not None else floorplan(1e-5, 1e-5)},
        ("graph", F_DIFFUSION): {LAYOUT_KEY: tuple(diffusion)},
    }
    return LayoutResult(FakeSnapshot(fields))


def groups_in(*hubs):
    """입력 그룹(`ly_groups_in`) 가짜: ((gid, hub_net), ...) -> 피검이 읽는 gid·hub_net 만."""
    return tuple(SimpleNamespace(gid=g, hub_net=h) for g, h in hubs)


def with_groups_in(lay, hubs):
    """손 레이아웃 결과에 입력 그룹 필드를 넣는다(gid 순)."""
    lay.snapshot.fields[("graph", F_GROUPS_IN)] = {LAYOUT_KEY: groups_in(*sorted(hubs))}
    return lay


def placement(name, key, nf, W, pending=False, tol=0.01, grid=GRID):
    return Placement(name, key, key * grid, nf, W, pending, tol)


def rule_ids():
    return tuple((q, "RULE." + q) for q in PDK_RULE_QUANTITIES)


def pdk(keys, grid=GRID):
    """실 LayoutPdk(검사 통과) -- 폭 키 ((kind, (키, ...)), ...)."""
    return LayoutPdk(grid, tuple((k, tuple(v)) for k, v in keys), 0.0, 0.0, 0.0, 0.0, 0.0, rule_ids(), "toy")


# ---------------------------------------------------------------- 가짜 스냅샷·결과

class FakeSnapshot:
    """피검이 읽는 두 메서드만: `column(table, field) -> ((key, value), ...)`, `value(table, key, field)`."""

    def __init__(self, fields):
        self.fields = {k: dict(v) for k, v in fields.items()}

    def column(self, table, field):
        return tuple(sorted(self.fields.get((table, field), {}).items()))

    def value(self, table, key, field):
        return self.fields[(table, field)][key]


def op(kind="nmos", W=1e-6, current=1e-6, L=1e-6, gm_id=10.0, vds=0.5, vsb=0.0):
    return SimpleNamespace(kind=kind, W=W, current=current, L=L, gm_id=gm_id, vds=vds, vsb=vsb)


def ssdev(cdb, csb, model="m"):
    return SimpleNamespace(cdb=cdb, csb=csb, junction_model=model)


def rows(*cs):
    """제약 행: c 값마다 ConstraintRow(이름 r<i>, c, active = c <= 1)."""
    return tuple(ConstraintRow("r%d" % i, float(c), c <= 1) for i, c in enumerate(cs))


def eval_result(snapshot, power=1e-3, area=1e-10, b_p=1e-6, status=STATUS_SEALED, constraints=(), unmeasured=(), failure=None,
                theta=(("t", 1.0),), cells=(0,), sealed=True, tag=""):
    """search.EvalResult 의 피검이 읽는 속성만 가진 가짜."""
    return SimpleNamespace(
        evaluation=SimpleNamespace(snapshot=snapshot, sealed=object() if sealed else None),
        objectives=SimpleNamespace(power_w=power, area_m2=area, power_resolution_w=b_p),
        status=status, constraints=tuple(constraints), unmeasured=tuple(unmeasured), failure=failure,
        theta=theta, key=SimpleNamespace(cells=cells), tag=tag)


def converged(pid, power, area, bbox, b_p=1e-9, slack_rows=(5.0,), status="converged", grid=GRID):
    """refilter·admission·alternation 입력용 ConvergedPoint(판정 축 값만 의미 있음)."""
    plan = floorplan(bbox, bbox, grid=grid, area=area)
    res = SimpleNamespace(constraints=rows(*slack_rows))
    return ConvergedPoint(pid, status, None, res, layout(plan=plan), None, area, area, power, b_p, 1, (), (), (), (),
                          (), (), (), (), 0, 0, None, ())


def candidate(pid, power, search_area, b_p=1e-9, slack_rows=(5.0,)):
    """교대 후보 FrontPoint 가짜(봉인 점, 탐색 축 값)."""
    res = SimpleNamespace(objectives=SimpleNamespace(power_w=power, area_m2=search_area, power_resolution_w=b_p),
                          constraints=rows(*slack_rows), status=STATUS_SEALED,
                          evaluation=SimpleNamespace(sealed=object(), snapshot=None))
    return SimpleNamespace(point_id=pid, result=res, origin=())


# ---------------------------------------------------------------- BSIM4 접합 용량 폐형식 (metrics CONTRACT 8.2, ngspice 대조 8.4)

def bsim4_junction(params, fw, ad, as_, pd, ps, m, v_db, v_sb, temp_c):
    """oracle (b): BSIM4 4.5 접합 용량 폐형식(metrics CONTRACT 8.2 -- ngspice BSIM4v5 와 90점 대조된 식). 엔진 `junction_caps` 를 부르지 않는다.
    반환 (cdb, csb) 소자 전체 F."""
    p = params
    dt = temp_c - p.tnom
    weff = fw - 2.0 * p.dwj

    def side(cj, cjsw, cjswg, mj, mjsw, mjswg, pb, pbsw, pbswg, area, perim, v):
        cj_t = cj * max(0.0, 1.0 + p.tcj * dt)
        cjsw_t = cjsw * max(0.0, 1.0 + p.tcjsw * dt)
        cjswg_t = cjswg * max(0.0, 1.0 + p.tcjswg * dt)
        pb_t, pbsw_t, pbswg_t = pb - p.tpb * dt, pbsw - p.tpbsw * dt, pbswg - p.tpbswg * dt
        p_eff = perim - weff if p.permod == 1.0 else perim
        total = 0.0
        for c0, mj_, pb_ in ((cj_t * area, mj, pb_t), (cjsw_t * p_eff, mjsw, pbsw_t), (cjswg_t * weff, mjswg, pbswg_t)):
            if v > 0:
                total += c0 * (1.0 + v / pb_) ** (-mj_) if c0 > 0 else 0.0
            else:
                total += c0 * (1.0 - mj_ * v / pb_)
        return total

    cdb = m * side(p.cjd, p.cjswd, p.cjswgd, p.mjd, p.mjswd, p.mjswgd, p.pbd, p.pbswd, p.pbswgd, ad, pd, v_db)
    csb = m * side(p.cjs, p.cjsws, p.cjswgs, p.mjs, p.mjsws, p.mjswgs, p.pbs, p.pbsws, p.pbswgs, as_, ps, v_sb)
    return cdb, csb


# ---------------------------------------------------------------- 실경로 (실 LUT v2 + sky130 + library 회로)

REAL_LN_IDU = -14.0             # 손 봉인 점: 모든 ln_idu 성분(= ln(ID·L/W)) -- 실측(2026-10-09) 두 회로 모두 봉인·제약 행 c >= 0 인 값
REAL_CURRENT_SCALE = 3e5        # 손 봉인 점: 층 0 θ 의 current 성분 배율(층 0 은 전류 하한 근처 ~5e-11 A -> ~1.5e-5 A)
# [library spec card 2026-10-14] two_stage_ota spec 에 pm_ss_deg >= 70(사용자 Q-S2)이 들어와 위 공통 규칙의 점은 PM 행만 c = -3.21 로 출발 조건
# (봉인 + 모든 제약 행 c >= 0)을 잃었다. 출발 조건이지 기대값이 아니므로 다시 잡았다 -- 고른 방법(엔진 밖 스크립트, 피검 함수 출력은 출발 조건
# 확인에만 씀): wt/_scratch_libspec_tests/conv_p0_diag2.py(결과 conv_diag2.json·txt).
#  1. 축 선택: 성분 하나씩 x10^(±1/8)(ln_idu ±0.5) 바꾼 민감도 진단(conv_p0_sens.py)에서 PM 행 c 를 올리는 성분 = Cc 증가·2단 소자(M6, gate = O1,
#     drain = OUT) current 증가(회로 해석: Miller 보상 2단 OTA 의 비주극점 gm6/CL 상승·주극점 하강). 공통 배율 축(current 전부·ln_idu 전부)과
#     단일 축(M6 만 -- c 가 -1.07 에서 포화, Cc 만 -- 상자 상한 전에 gbw 행이 깨짐)은 모두 실패.
#  2. 탐색: (i, j) = (M6 current 배율 10^(i/16), Cc 배율 10^(j/16)), j <= 8(Cc 상자 [1e-13, 1e-11] F 상한, 층 0 Cc = 3.16 pF), i + j 를 0 부터
#     늘리고 같은 합에서는 j 오름차순으로 돌아 '봉인 + 모든 제약 행 c >= 0' 인 첫 점 -> (i, j) = (10, 6). 그 점 PM 행 c = 0.117, gbw 행 c = 0.055.
# common_gate_amplifier 는 항목이 없어 옛 점 그대로다.
REAL_EXTRA_FACTORS = {
    "two_stage_ota": ((("current", "M6"), 10 ** (10 / 16)), (("capacitance", "Cc"), 10 ** (6 / 16))),
}
REAL_CIRCUITS = ("common_gate_amplifier", "two_stage_ota")


class RealPath:
    """회로·변형마다 (case, sctx, 출발 EvalResult, converge 결과, 스파이 기록) 을 만든다. 입력(LUT·PDK·S1)은 세션 1회, 실행(두 객체)은
    부를 때마다 새로([XRUN-F1 card B M-d] -- `run` 참고)."""

    def __init__(self, tmp):
        from generality.pipeline import Env, Pipe
        try:
            self.env = Env()
        except RuntimeError as e:          # 입력 없음은 skip 이 아니라 FAIL
            pytest.fail("convergence 실경로 test 입력(실 LUT v2·PDK) 없음: %s" % e, pytrace=False)
        self.pipe = Pipe(self.env, tmp)

    def start(self, name, variant="orig"):
        from generality.pipeline import map_cells, map_theta
        from gmid_engine.search import evaluate
        case = self.pipe.case(name, variant)
        (th, cells), res = self.pipe.theta0(name)
        assert th is not None, (name, res.stop)
        theta = {}
        for (kind, key), v in th.items():
            theta[(kind, key)] = REAL_LN_IDU if kind == "ln_idu" else (v * REAL_CURRENT_SCALE if kind == "current" else v)
        for comp, factor in REAL_EXTRA_FACTORS.get(name, ()):      # 회로별 추가 배율(아래 상수 주석) -- 이름 전단사 변형도 원 이름 θ 에서 곱한 뒤 사상
            theta[comp] *= factor
        sctx = self.pipe.fresh_sctx(case)
        theta = map_theta(theta, case)
        result = evaluate(sctx, theta, map_cells(cells, case, sctx.domain))
        return case, sctx, result

    def run(self, name, variant="orig"):
        """[XRUN-F1 card B 규칙 M M-d, interface card C0·C6] 결과(SimpleNamespace)가 sctx(실행의 두 객체를 칸으로 쥠)를 담으므로 test 사이에
        캐시하지 않는다 -- 부를 때마다 새 실행(Pipe.case 가 새 open_run() 쌍의 KernelContext). 이 객체는 session fixture 라 test 하나보다 오래 산다."""
        return self._converge(name, variant)

    def _converge(self, name, variant):
        from gmid_engine.convergence import converge, realized_geometry
        from gmid_engine.search import FrontPoint
        cp_mod = module("converge_point")
        case, sctx, start = self.start(name, variant)
        spy = SimpleNamespace(place=[], evals=[], start_kernel=None)
        real_place, real_eval = cp_mod.place_layout, cp_mod.evaluate

        def place_spy(*a, **k):
            before = sctx.counters["kernel_calls"]
            placed = real_place(*a, **k)
            spy.place.append((before, sctx.counters["kernel_calls"], placed,
                              None if placed.unplaced else realized_geometry(placed.layout.snapshot, placed.placements, placed.keys)))
            return placed

        def eval_spy(*a, **k):
            before = sctx.counters["kernel_calls"]
            r = real_eval(*a, **k)
            spy.evals.append((before, sctx.counters["kernel_calls"], k.get("geometry"), r, k.get("parent")))
            return r

        spy.start_kernel = sctx.counters["kernel_calls"]
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(cp_mod, "place_layout", place_spy)
            mp.setattr(cp_mod, "evaluate", eval_spy)
            front = converge(sctx, self.env.pdk, (FrontPoint("p0", start, ()),))
        return SimpleNamespace(case=case, sctx=sctx, start=start, front=front, point=front.points[0], spy=spy)


@pytest.fixture(scope="session")
def real(tmp_path_factory):
    return RealPath(tmp_path_factory.mktemp("conv_real"))


def module(name):
    """`gmid_engine.convergence.<name>` 모듈 객체 -- 패키지가 같은 이름의 함수(converge·converge_point)를 공개해 속성 접근은 함수를 준다."""
    return importlib.import_module("gmid_engine.convergence." + name)


def isclose(a, b, rel=1e-12):
    return math.isclose(a, b, rel_tol=rel, abs_tol=0.0)
