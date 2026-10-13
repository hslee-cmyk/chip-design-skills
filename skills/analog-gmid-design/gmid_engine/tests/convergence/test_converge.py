"""`converge(sctx, pdk_decl, points, pool=(), slice_keys=None) -> ConvergedFront` -- MOD8 진입점 (CONTRACT 9절·11절 불변식 1·7, 설계 40 §3.9 MOD8 (4),
DEC-79 교대, D-M8·R12).

oracle (a) 합성: `converge_point` 를 표 가짜(점 id -> 손으로 정한 ConvergedPoint)로, `LayoutPdk.from_decl` 을 손 PDK 로 바꿔 재필터·교대·거부를 손으로 판정한다.
oracle (a)·(d) 실경로: common_gate_amplifier·two_stage_ota 손 봉인 점 -- 수렴, 이름 전단사 불변(비트), 결정론(같은 입력·PYTHONHASHSEED), 판정 축 포함 항목,
수동소자 값(회로 해석: two_stage_ota 영점 상쇄 Rz = 1/gm(M6), M6 = O1 을 gate 로 받는 2단 소자 -- topology JSON).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmid_engine.convergence import (
    DROP_DOMINATED,
    DROP_FOLDED,
    DROP_NONCONVERGED,
    STATUS_CONVERGED,
    STATUS_NONCONVERGENT,
    ConvergedFront,
    DroppedPoint,
    converge,
)

from gmid_engine.layout import F_FLOORPLAN, LAYOUT_KEY

from .conftest import candidate, converged, module, pdk, rows

U = 1e-12           # 격자 1e-8 x bbox 1e-4
B = 1e-4
BP = 1e-6


class Table:
    """가짜 converge_point: id -> ConvergedPoint. 호출 (id, pdk) 기록."""

    def __init__(self, table):
        self.table, self.calls = dict(table), []

    def converge_point(self, sctx, pdk_, point):
        self.calls.append((point.point_id, pdk_))
        return self.table[point.point_id]


@pytest.fixture
def fake(monkeypatch):
    mod = module("converge")

    def install(table, keys=(("nmos", (30, 10, 20)), ("pmos", (40,)))):
        t = Table(table)
        monkeypatch.setattr(mod, "converge_point", t.converge_point)
        monkeypatch.setattr(mod, "LayoutPdk", SimpleNamespace(from_decl=lambda lut, decl: pdk(keys)))
        sctx = SimpleNamespace(counters={"kernel_calls": 0}, dc=SimpleNamespace(lut=SimpleNamespace(memo=SimpleNamespace(lut="LUT"))))
        return t, sctx
    return install


def fp(pid, power=1e-3, area=5 * U):
    return candidate(pid, power, area)


# ---------------------------------------------------------------- 입력 거부

@pytest.mark.parametrize("mutate", ["unsealed_status", "no_sealed_snapshot", "negative_row", "no_result"])
def test_rejects_unsealed_or_violating_points(fake, mutate):
    t, sctx = fake({})
    bad = fp("bad")
    if mutate == "unsealed_status":
        bad.result.status = "pending_seal_7"
    elif mutate == "no_sealed_snapshot":
        bad.result.evaluation = SimpleNamespace(sealed=None, snapshot=None)
    elif mutate == "negative_row":
        bad.result.constraints = rows(1.0, -1e-3)
    else:
        bad.result = None
    with pytest.raises(ValueError):
        converge(sctx, "DECL", (bad,))
    assert t.calls == []                                  # 무엇이든 하기 전에 거부


def test_slice_keys_restrict_layout_pdk(fake):
    t, sctx = fake({"p": converged("p", 1e-3, 10 * U, B)})
    converge(sctx, "DECL", (fp("p"),), slice_keys=(("nmos", (20, 10)),))
    (_pid, used), = t.calls
    assert used.slice_width_keys == (("nmos", (10, 20)), ("pmos", (40,)))          # 그 kind 만 줄이고 정렬, 나머지 그대로
    converge(sctx, "DECL", (fp("p"),))
    assert t.calls[-1][1].slice_width_keys == (("nmos", (30, 10, 20)), ("pmos", (40,)))


# ---------------------------------------------------------------- 재필터 (불변식 7) + 결과 조립

def test_refilter_drops_and_nonconverged(fake):
    table = {
        "p1": converged("p1", 1.0e-3, 10.0 * U, B, b_p=BP),
        "p2": converged("p2", 2.0e-3, 12.5 * U, B, b_p=BP),               # p1 이 지배(두 축 다 폭 넘게 나쁨)
        "p3": converged("p3", 1.0e-3 + 0.5 * BP, 10.5 * U, B, b_p=BP),   # p1 과 모든 축 동률 -> 접힘
        "p4": converged("p4", 0.5e-3, 1.0 * U, B, status=STATUS_NONCONVERGENT),   # 수렴 못 함 -> 재필터 밖
    }
    t, sctx = fake(table)
    out = converge(sctx, "DECL", tuple(fp(i) for i in ("p4", "p2", "p1", "p3")))
    assert isinstance(out, ConvergedFront)
    assert [p.point_id for p in out.front] == ["p1"]
    assert out.dropped == (DroppedPoint("p2", DROP_DOMINATED, "p1"), DroppedPoint("p3", DROP_FOLDED, "p1"),
                           DroppedPoint("p4", DROP_NONCONVERGED, None))
    assert [p.point_id for p in out.nonconverged] == ["p4"]
    assert [p.point_id for p in out.points] == ["p4", "p2", "p1", "p3"]          # 처리 순서
    assert out.rounds == 1 and out.admitted == ()
    # K_alt: 수렴 면적 10, 12.5, 10.5 U -> 범위 2.5 U, 폭 1 U -> 2.5 -> 1.25 -> 0.625 <= 1 -> 반감 2회
    assert out.k_alt == 2
    perf = dict(out.perf)
    assert (perf["points"], perf["rounds"], perf["kernel_calls"], perf["layout_calls"]) == (4, 1, 0, 0)
    verdicts = [dict(n)["verdict"] for n in out.notes]
    assert "judged_axis" in verdicts and "area_model_error_undeclared" in verdicts


def test_alternation_admits_pool_candidate_and_reports_nonconvergent_alternation(fake):
    # 라운드 1: p0 만 수렴(1 mW, 10 U). pool: c1(탐색 축 0.5 mW, 20 U) -> 전력이 나아 비지배 -> 들임.
    #          c2(1.5 mW, 9.5 U) -> p0 대비 면적 동률(0.5 U), 전력 나쁨 -> 지배당해 들이지 않음.
    # 라운드 2: c1 수렴 (0.5 mW, 10.9 U) -> p0 대비 전력 나음, 면적 동률(0.9 U) -> p0 지배. 남은 점 c1 하나.
    #          c2 vs c1: 면적 1.4 U 나음(> 1 U) -> 비지배 -> 후보로 남는다. K_alt = 1(첫 재필터 뒤 수렴 점 하나) 이고 재실행 1회를 이미 썼다
    #          -> 교대 NONCONVERGENT 기록, c2 는 레이아웃하지 않는다.
    table = {"p0": converged("p0", 1.0e-3, 10.0 * U, B, b_p=BP), "c1": converged("c1", 0.5e-3, 10.9 * U, B, b_p=BP)}
    t, sctx = fake(table)
    pool = (candidate("c1", 0.5e-3, 20 * U, b_p=BP), candidate("c2", 1.5e-3, 9.5 * U, b_p=BP),
            candidate("c3", 0.1e-3, 1 * U, b_p=BP, slack_rows=(1.0, -0.5)),          # c < 0 -> pool 에서도 받지 않는다
            candidate("p0", 0.1e-3, 1 * U, b_p=BP))                                  # 이미 점 -> pool 에서 뺀다
    out = converge(sctx, "DECL", (fp("p0"),), pool=pool)
    assert [c[0] for c in t.calls] == ["p0", "c1"]
    assert out.admitted == ("c1",)
    assert out.rounds == 2 and out.k_alt == 1
    assert [p.point_id for p in out.front] == ["c1"]
    assert out.dropped == (DroppedPoint("p0", DROP_DOMINATED, "c1"),)
    alt = [dict(n) for n in out.notes if dict(n)["verdict"] == "nonconvergent_alternation"]
    assert len(alt) == 1 and alt[0]["pending"] == ("c2",) and alt[0]["k_alt"] == 1


def test_no_converged_point_gives_empty_front(fake):
    t, sctx = fake({"p": converged("p", 1e-3, 10 * U, B, status=STATUS_NONCONVERGENT)})
    out = converge(sctx, "DECL", (fp("p"),), pool=(candidate("c", 0.5e-3, 1 * U),))
    assert out.front == () and out.k_alt is None and out.admitted == ()
    assert [c[0] for c in t.calls] == ["p"]
    assert out.dropped == (DroppedPoint("p", DROP_NONCONVERGED, None),)


# ---------------------------------------------------------------- 실경로

REAL = ("common_gate_amplifier", "two_stage_ota")
LIBRARY = Path(__file__).resolve().parents[3] / "assets" / "library"


@pytest.mark.parametrize("name", REAL)
def test_real_converges_and_front_kept(real, name):
    r = real.run(name)
    out = r.front
    assert r.point.status == STATUS_CONVERGED, (r.point.notes, r.point.failure)
    assert [p.point_id for p in out.front] == ["p0"] and out.dropped == () and out.nonconverged == ()
    assert out.rounds == 1 and out.k_alt == 1
    judged = [dict(n) for n in out.notes if dict(n)["verdict"] == "judged_axis"][0]
    assert tuple(judged["included"]) == tuple(
        i for i, _v, _rule in r.point.layout.snapshot.value("graph", LAYOUT_KEY, F_FLOORPLAN).included)   # [U17 1-e] ly_floorplan 필드
    assert dict(out.perf)["kernel_calls"] == r.point.kernel_calls


def test_real_two_stage_passives_feed_judged_axis(real):
    """[U17 ①] 설계 40 v1.6 §2.4.7·§2.4.8: 수동소자 값은 설계점 스냅샷의 S2 필드 `device.passive_value`(spec ∪ θ ∪ 영점 상쇄
    R = 1/Σ`dc_gm`)이고 MOD8 판정 축 면적 입력이 같은 필드를 읽는다(다시 만들지 않는다). Rz·dc_gm(M6) = 1, ss_dev gm = 같은 필드(§3.7-3)."""
    r = real.run("two_stage_ota")
    cp = r.point
    snap = cp.result.evaluation.snapshot
    values = dict(snap.column("device", "passive_value"))
    spec = json.loads((LIBRARY / "two_stage_ota.sizing_spec.json").read_text(encoding="utf-8"))
    doc = json.loads((LIBRARY / "two_stage_ota.topology.json").read_text(encoding="utf-8"))
    second = [d["name"] for d in doc["netlist"] if d["gate"] == "O1"]           # 2단 소자(1단 출력 O1 을 gate 로)
    assert second == ["M6"]
    gm = dict(snap.column("device", "dc_gm"))["M6"]
    assert dict(snap.column("device", "ss_dev"))["M6"].gm == gm                 # ss gm = dc_gm 필드 하나(§3.7-3)
    assert values["CL"] == spec["human"]["element_values"]["CL"]["value_farad"]
    assert values["Cc"] == dict(cp.result.theta)[("capacitance", "Cc")]
    assert values["Rz"] * gm == pytest.approx(1.0, rel=1e-12)                   # Miller 영점 상쇄 Rz = 1/gm2
    plan = cp.layout.snapshot.value("graph", LAYOUT_KEY, F_FLOORPLAN)                      # [U17 1-e] ly_floorplan 필드
    assert "passive_blocks_mim_poly_resistor" in [i for i, _v, _rule in plan.included]
    unit = dict(r.sctx.area_decl.unit_area)
    assert plan.passive_area_m2 >= values["Cc"] * unit["Cc"]                     # MIM 면적 >= C / 밀도 (측정 부하 CL 은 제외)


def _summary(r, nm=lambda x: x):
    cp = r.point
    return {
        "status": cp.status,
        "iterations": len(cp.iterations),
        "k_max": cp.k_max,
        "layout_area": cp.layout_area_m2.hex(),
        "w_request": sorted((nm(m), w.hex()) for m, w in cp.geometry.w_request),
        "w_keys": list(cp.geometry.w_keys),
        "diffusion": sorted((nm(m), d.ad_m2.hex(), d.as_m2.hex(), d.pd_m.hex(), d.ps_m.hex(), d.m.hex()) for m, d in cp.geometry.diffusion),
        "junction": sorted((nm(j.device), j.cdb_after.hex(), j.csb_after.hex()) for j in cp.junction),
        "rejected": [nm(x) for x in cp.rejected], "narrowed": list(cp.narrowed),
    }


@pytest.mark.parametrize("name", REAL)
def test_real_name_bijection_invariance(real, name):
    """불변식 1: 이름 전단사에 대해 면적·반복 수·상태가 같다 -- 기하·접합 용량까지 비트 동일(치환표로 옮겨 비교)."""
    a, b = real.run(name), real.run(name, ("ren", 0))
    assert set(b.case.mapping) and any(k != v for k, v in b.case.mapping.items())       # 실제로 이름이 바뀐 변형
    assert _summary(b) == _summary(a, nm=b.case.nm)


def test_real_deterministic_rerun(real):
    """불변식 1: 같은 입력(새 컨텍스트) -> 같은 결과(perf 의 wall_s 제외)."""
    a = real.run("common_gate_amplifier")
    b = real._converge("common_gate_amplifier", "orig")
    assert _summary(a) == _summary(b)
    assert a.point.iterations == b.point.iterations and a.point.relaxations == b.point.relaxations
    assert [x for x in a.front.perf if x[0] != "wall_s"] == [x for x in b.front.perf if x[0] != "wall_s"]
    assert a.front.notes == b.front.notes


SEED_CODE = r"""
import json, sys, tempfile
sys.path.insert(0, {tests!r})
sys.path.insert(0, {skill!r})
import conftest  # 표 캐시 격리(GMID_LUT_TABLE_CACHE_DIR)
from convergence.conftest import RealPath
from convergence.test_converge import _summary
r = RealPath(tempfile.mkdtemp()).run("common_gate_amplifier")
print("@@" + json.dumps(_summary(r)))
"""


def test_real_hash_seed_independent():
    """불변식 1: PYTHONHASHSEED 와 무관 -- 두 시드의 별도 프로세스 결과가 비트 같다."""
    tests = Path(__file__).resolve().parents[1]
    skill = tests.parents[1]
    code = SEED_CODE.format(tests=str(tests), skill=str(skill))
    out = []
    for seed in ("0", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="1")
        proc = subprocess.run([sys.executable, "-P", "-c", code], cwd=str(skill), env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=1800)
        assert proc.returncode == 0, proc.stderr[-4000:]
        lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("@@")]
        assert len(lines) == 1, proc.stdout[-2000:]
        out.append(json.loads(lines[0][2:]))
    assert out[0] == out[1]
    assert out[0]["status"] == STATUS_CONVERGED
