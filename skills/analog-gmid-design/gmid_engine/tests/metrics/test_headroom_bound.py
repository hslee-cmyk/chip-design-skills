"""metrics/headroom_bound.py -- `headroom_bound(local, rail_v, edges, windows, constraints, input_dc_v, differential_out)`
(metrics CONTRACT 10.6, 설계 41 4.6, D-GB4f·D-J5).

oracle (a) 구성으로 정답이 정해진 합성 입력: 엣지 비용(`EdgeCost`)을 손으로 정한 값으로 주고, 41 4.6 '경로 폭 = ΔV_rail − Σ VGS 엣지 비용 −
Σ VDS 엣지 비용' 을 손으로 계산한다(엣지 방향: nmos 소스→드레인 VDS·소스→게이트 VGS, pmos 드레인→소스 VDS·게이트→소스 VGS, 계약 10.6).
- 인버터(입력 두 극성 공유 gate): in 창 = [0 + vgs_n, 1.8 − vgs_p] = [0.5, 1.2] -> 폭 0.7; out 창 = [0.2, 1.5] -> 1.3(VGS 엣지 없는 경로라 대상 아님).
- CS + 소스 팔로워(sf 출력): out 의 U = min(1.8 − vds_n(M1), 1.8 − vds_p(M4) − vgs_n(M1)) = 1.0, L = 0.2 -> 폭 0.8(대상: gnd→out→x→vdd 가 VGS 엣지를 지난다);
  버퍼 입력 x: L = max(vds_n(M3), vds_n(M2) + vgs_n(M1)) = 0.7, U = 1.8 − vds_p(M4) = 1.5 -> 폭 0.8.
판정은 41 4.3 과 같은 규칙: 인증된 대상 창의 상한 < 선언 목표면 정지(`headroom_unattainable`), 아니면 보고만.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from gmid_engine.metrics import EdgeCost, HeadroomResult, HeadroomRow, headroom_bound

from .gb4_hand import local_inputs

RAILS = {"gnd": 0.0, "vdd": 1.8}
# 손으로 정한 엣지 비용(구성 입력): nmos VGS 0.5 / VDS 0.2, pmos VGS 0.6 / VDS 0.3. L bin 별 VGS 비용: nmos bin1 1.25(긴 L 이면 VT 가 커진다),
# pmos bin1 0.7.
EDGES = {"nmos": EdgeCost("nmos", 100, 0.5, ((0, 0.5), (1, 1.25)), 0.2, (("L", 1e-6),)),
         "pmos": EdgeCost("pmos", 100, 0.6, ((0, 0.6), (1, 0.7)), 0.3, (("L", 1e-6),))}
INV = (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "in", "vdd"))
SF = (("M3", "nmos", "x", "in", "gnd"), ("M4", "pmos", "x", "pb", "vdd"), ("M1", "nmos", "vdd", "x", "out"),
      ("M2", "nmos", "out", "vb", "gnd"))


def _run(devs, windows, constraints=(), input_dc_v=None, differential_out=False, edges=EDGES):
    return headroom_bound(local_inputs(devs), RAILS, edges, tuple(windows), tuple(constraints), input_dc_v,
                          differential_out)


def _row(res, kind, net):
    hits = [r for r in res.rows if r.window_kind == kind and r.net == net]
    assert len(hits) == 1, [(r.window_kind, r.net) for r in res.rows]
    return hits[0]


def _codes(items):
    return [c for c, _ in items]


def test_inverter_windows_are_rail_span_minus_edge_costs():
    res = _run(INV, (("input", "in"), ("output", "out")))
    assert isinstance(res, HeadroomResult)
    inp = _row(res, "input", "in")
    assert isinstance(inp, HeadroomRow)
    # 손: in = [0 + 0.5, 1.8 − 0.6]
    assert inp.lo_edge_v == pytest.approx(0.5, abs=1e-12)
    assert inp.hi_edge_v == pytest.approx(1.2, abs=1e-12)
    assert inp.upper_bound_v == pytest.approx(0.7, abs=1e-12)
    assert inp.status == "certified"
    out = _row(res, "output", "out")
    assert (out.lo_edge_v, out.hi_edge_v, out.upper_bound_v) == pytest.approx((0.2, 1.5, 1.3), abs=1e-12)
    # 경로 엣지는 (소자, 엣지 종류, 아랫 넷, 윗 넷, 비용) -- 손 경로
    assert sorted(inp.path) == sorted((("M1", "vgs", "gnd", "in", 0.5), ("M2", "vgs", "in", "vdd", 0.6)))
    assert res.stops == ()


def test_icmr_target_above_certified_window_stops():
    # 0.7 < 0.8 -> 정지(41 4.6 판정), 상세에 metric·window·upper_bound·target·derivation
    res = _run(INV, (("input", "in"), ("output", "out")), (("icmr_v", ">=", 0.8),))
    assert _codes(res.stops) == ["headroom_unattainable"]
    detail = dict(res.stops[0][1])
    assert detail["metric"] == "icmr_v" and detail["window"] == "input" and detail["net"] == "in"
    assert detail["upper_bound"] == pytest.approx(0.7, abs=1e-12) and detail["target"] == 0.8
    assert sorted(d[:2] for d in detail["derivation"]) == [("M1", "vgs"), ("M2", "vgs")]
    assert _row(res, "input", "in").verdict == "infeasible"


def test_icmr_target_below_window_does_not_stop():
    res = _run(INV, (("input", "in"),), (("icmr_v", ">=", 0.6),))
    assert res.stops == ()
    assert _row(res, "input", "in").verdict != "infeasible"


def test_window_without_vgs_edge_is_not_a_stop_target():
    # 인버터 출력의 레일–레일 경로(gnd→out→vdd)는 VGS 엣지가 없다 -> 대상 아님(41 4.6 '대상'), 1.3 < 1.4 라도 정지하지 않는다
    res = _run(INV, (("input", "in"), ("output", "out")), (("swing_out_v", ">=", 1.4),))
    assert res.stops == ()
    assert _row(res, "output", "out").verdict != "infeasible"


def test_follower_output_window_and_buffer_window():
    res = _run(SF, (("input", "in"), ("output", "out"), ("buffer", "x")), (("swing_out_v", ">=", 0.9),))
    out = _row(res, "output", "out")
    assert (out.lo_edge_v, out.hi_edge_v, out.upper_bound_v) == pytest.approx((0.2, 1.0, 0.8), abs=1e-12)
    buf = _row(res, "buffer", "x")
    assert (buf.lo_edge_v, buf.hi_edge_v, buf.upper_bound_v) == pytest.approx((0.7, 1.5, 0.8), abs=1e-12)
    # 0.8 < 0.9 -> 정지, 유도는 M2 vds + M1 vgs + M4 vds (손 경로 gnd→out→x→vdd)
    assert _codes(res.stops) == ["headroom_unattainable"]
    detail = dict(res.stops[0][1])
    assert detail["metric"] == "swing_out_v" and detail["upper_bound"] == pytest.approx(0.8, abs=1e-12)
    assert sorted(d[:2] for d in detail["derivation"]) == [("M1", "vgs"), ("M2", "vds"), ("M4", "vds")]
    # 선언 제약이 없는 버퍼 창은 보고만(no_target)
    assert buf.verdict == "no_target"


def test_differential_output_doubles_swing():
    # 차동 출력 포트쌍이면 폭 × 2 (계약 10.6, 40 3.8-8): 0.8 × 2 = 1.6 >= 1.5 -> 정지 없음, 단일 출력이면 0.8 < 1.5 -> 정지
    single = _run(SF, (("output", "out"),), (("swing_out_v", ">=", 1.5),), differential_out=False)
    double = _run(SF, (("output", "out"),), (("swing_out_v", ">=", 1.5),), differential_out=True)
    assert _codes(single.stops) == ["headroom_unattainable"]
    assert double.stops == ()


def test_icm_margin_uses_declared_input_dc_distance():
    # 창 [0.5, 1.2], 선언 입력 DC 0.9 -> 경계까지 최소 거리 0.3 (손)
    stop = _run(INV, (("input", "in"),), (("icm_margin_v", ">=", 0.35),), input_dc_v=0.9)
    ok = _run(INV, (("input", "in"),), (("icm_margin_v", ">=", 0.25),), input_dc_v=0.9)
    pending = _run(INV, (("input", "in"),), (("icm_margin_v", ">=", 0.35),), input_dc_v=None)
    assert _codes(stop.stops) == ["headroom_unattainable"]
    assert dict(stop.stops[0][1])["metric"] == "icm_margin_v"
    assert ok.stops == ()
    # 입력 DC 대기(SP-2)면 판정할 수 없다 -> 보고만(41 4.6)
    assert pending.stops == ()


def test_icm_margin_outside_window_stops_even_for_zero_margin():
    # 선언 입력 DC 1.5 는 창 [0.5, 1.2] 밖 -> icm_margin_v >= 0 위반(41 4.6 J-E '창이 인증되었고 상한 밖이면 exit 3')
    res = _run(INV, (("input", "in"),), (("icm_margin_v", ">=", 0.0),), input_dc_v=1.5)
    assert _codes(res.stops) == ["headroom_unattainable"]


def test_short_l_bin_warning_when_only_lowest_bin_opens_input_window():
    # nmos 비용만 bin 값으로 바꾼 폭: bin0 1.8 − 0.5 − 0.6 = 0.7 > 0, bin1 1.8 − 1.25 − 0.6 = −0.05 -> 양인 bin 이 맨 아래 하나 -> 경고
    # pmos: bin0 0.7, bin1 1.8 − 0.5 − 0.7 = 0.6 > 0 -> 경고 없음
    res = _run(INV, (("input", "in"),))
    warns = [dict(d) for c, d in res.warnings if c == "icmr_window_short_l_bin"]
    assert [w["kind"] for w in warns] == ["nmos"]
    assert warns[0]["bin"] == 0
    by_bin = dict(warns[0]["upper_bound_by_bin"])
    assert by_bin[0] == pytest.approx(0.7, abs=1e-12) and by_bin[1] == pytest.approx(-0.05, abs=1e-12)
    # 경고는 정지가 아니다
    assert res.stops == ()


def test_no_short_bin_warning_when_upper_bins_also_open():
    edges = dict(EDGES)
    edges["nmos"] = EdgeCost("nmos", 100, 0.5, ((0, 0.5), (1, 0.6)), 0.2, (("L", 1e-6),))
    res = _run(INV, (("input", "in"),), edges=edges)
    assert [c for c, _ in res.warnings if c == "icmr_window_short_l_bin"] == []


def test_name_bijection_gives_same_widths():
    ren = {"in": "zz_in", "out": "aa_out", "x": "mm", "pb": "q1", "vb": "b0"}
    dev = {"M1": "Q7", "M2": "A1", "M3": "Z9", "M4": "B2"}
    sf2 = tuple((dev[n], k, ren.get(d, d), ren.get(g, g), ren.get(s, s)) for n, k, d, g, s in reversed(SF))
    r1 = _run(SF, (("output", "out"), ("buffer", "x")), (("swing_out_v", ">=", 0.9),))
    r2 = _run(sf2, (("output", "aa_out"), ("buffer", "mm")), (("swing_out_v", ">=", 0.9),))
    w1 = sorted((r.window_kind, r.upper_bound_v, r.lo_edge_v, r.hi_edge_v, r.status) for r in r1.rows)
    w2 = sorted((r.window_kind, r.upper_bound_v, r.lo_edge_v, r.hi_edge_v, r.status) for r in r2.rows)
    assert w1 == w2
    assert _codes(r1.stops) == _codes(r2.stops) == ["headroom_unattainable"]


def test_deterministic():
    a = _run(SF, (("input", "in"), ("output", "out"), ("buffer", "x")), (("swing_out_v", ">=", 0.9),))
    b = _run(SF, (("input", "in"), ("output", "out"), ("buffer", "x")), (("swing_out_v", ">=", 0.9),))
    assert a == b


_CYCLE_CHILD = r"""
import json, sys
sys.path[:0] = [%(skill)r, %(tests)r]
from gmid_engine.metrics import EdgeCost, headroom_bound
from metrics.gb4_hand import local_inputs
E = {"nmos": EdgeCost("nmos", 100, 0.5, ((0, 0.5),), 0.2, ()), "pmos": EdgeCost("pmos", 100, 0.6, ((0, 0.6),), 0.3, ())}
loc = local_inputs((("M1", "nmos", "vdd", "in", "out"), ("M2", "pmos", "gnd", "in", "out")))
import os, threading
threading.Timer(3.0, lambda: os._exit(3)).start()          # 감시: 호출이 3 s 안에 끝나지 않으면 자식이 스스로 끝난다(메모리 증가 제한)
r = headroom_bound(loc, {"gnd": 0.0, "vdd": 1.8}, E, (("input", "in"), ("output", "out")), (("icmr_v", ">=", 100.0),), None, False)
print(json.dumps({"status": sorted((x.window_kind, x.status) for x in r.rows), "stops": [c for c, _ in r.stops]}), flush=True)
os._exit(0)
"""


def test_positive_cost_cycle_terminates_as_unknown():
    # 상보 push-pull follower(M1 nmos 소스 out·게이트 in, M2 pmos 소스 out·게이트 in): out→in(nmos VGS 0.5), in→out(pmos VGS 0.6)
    # 의 비용 양수 사이클. 계약 10.6/모듈 문서: '라운드 상한(= 상태 수) 안에 끝나지 않으면 그 창은 미상' -> 함수는 끝나야 하고,
    # 미상 창은 정지 근거가 아니다(목표 100 V 라도 정지 없음). 끝나지 않으면(무한 반복) 자식 프로세스의 감시 타이머가 3 s 뒤 exit 3 으로
    # 끝낸다(자식 프로세스로 격리: 무한 반복이 메모리를 키워도 pytest 프로세스는 영향받지 않고, 증가량도 3 s 로 제한된다).
    skill = str(Path(__file__).resolve().parents[3])
    tests = str(Path(__file__).resolve().parents[1])
    code = _CYCLE_CHILD % {"skill": skill, "tests": tests}
    try:
        done = subprocess.run([sys.executable, "-P", "-c", code], capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        pytest.fail("child process did not finish within 120 s")
    assert done.returncode != 3, "headroom_bound did not terminate within 3 s on a positive-cost VGS cycle (contract: round cap -> unknown)"
    assert done.returncode == 0, done.stderr[-2000:]
    out = json.loads(done.stdout.strip().splitlines()[-1])
    assert out["stops"] == []
    assert ["input", "unknown"] in out["status"]
