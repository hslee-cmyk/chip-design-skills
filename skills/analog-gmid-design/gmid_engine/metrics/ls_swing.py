"""포화 기준 출력 스윙 -- 레일에서 노드까지 DC 경로 합 (설계 40 §3.8-8 `swing_out_v`, 41 §4.6, 계획 N3.8 '스윙·입력 범위', 체크리스트 D-SW).

진입점: `ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr`. 입력 공통모드 창·창 여유(`icmr_v`·`icm_margin_v`)는 이 함수의 일이 아니다 --
`icm_window_metrics`(`graph.icm_config` V_cm 칸, 카드 IT-2d, O-109 C1)가 내고 `metrics_aux` 가 한 `SwingIcmr` 로 합친다. 이 함수 출력의 입력 쪽 칸은 기본값이다.

**경로 합 = 차분 제약계의 가장 긴 경로.** 노드 전압 V_n 에 대한 제약:
* 채널 포화(VDS 엣지, 사용자 SPICE 포화 규칙 + LUT `tol_vdsat`): NMOS V_d − V_s ≥ sat, PMOS V_s − V_d ≥ sat, sat = VDSAT + tol_vdsat(`SatDevice.sat_v`).
  선형 영역 선언 소자(`linear`)는 채널 제약이 없다.
* 게이트-소스(VGS 엣지, 그 전류에서 VSB 를 포함한 |VGS|): NMOS V_g − V_s = +|VGS|, PMOS V_g − V_s = −|VGS| (등식 -- 양쪽 부등식). 전류가 바깥 회로로 고정되는
  소자에만 건다: source 가 레일이 아닌 소자(follower·차동쌍 -- source 가 gate 를 따라 움직인다)와 gate = drain 인 diode 연결 소자(VDS 엣지가 아니라 VGS 엣지 하나로
  떨어진다). source 가 레일이고 diode 도 아닌 소자(CS 구동 소자·미러 출력·바이어스 전류원)는 gate 가 자유라 VGS 엣지가 없다.
* 레일: V = 선언 전위. 수동소자 엣지는 제약이 없다(저항 전압강하는 신호 전류에 따라 변하고, 용량은 DC 에서 열려 있다).
V_a − V_b ≥ c 에서 lo(a) ≥ lo(b) + c, hi(b) ≤ hi(a) − c 를 노드 수 + 1 번까지 완화한다(Bellman–Ford, 단순 경로 길이 상한). 출발 구간은 모든 노드 [rail_min, rail_max]
(레일 밖 입력 불허, 사용자 결정 Q4 (4) -- 그래서 follower 의 V(out)max = min(레일 − VDsat, V(g)max − VGS), V(g)max 가 레일이면 레일 − VGS)이고 각 노드의 [lo, hi] 는
"레일에서 그 노드까지 경로 합"의 최소 여유다. 완화 문턱 = 부동소수 해상도
(float epsilon × 레일 전위 크기)로, 같은 경로의 반올림 되먹임이 끝없이 올리지 않게 한다.

* `swing_out_v`: 출력 포트 넷마다 반폭 = min(hi − V_dc, V_dc − lo), 단일 출력(들) = 2·min 반폭, 차동 출력 쌍(`diff_outputs`) = 출력마다 반폭 최솟값 × 4(차동 p-p).
  구간 [lo, hi, V_dc] 를 `out_ranges` 로 낸다. 빈 구간(반폭 음수)은 음수 폭 그대로.
* 분해능(`swing_resolution`): 가장 긴 경로를 따라 엣지 허용오차(채널 = tol_vdsat, VGS 엣지 = 그 소자 tol_V)를 누적한 값 × 계수(2 또는 4). 엣지 허용오차가 없으면 None.
* 정의 불가(`swing_out_v` 하나): 출력 포트 없음(`no_output_port`), 포화 판정 열이 없는 소자(`sat_unavailable`, 근사하지 않는다 DEC-88), 노드 전압 없음(`node_v_missing`).
"""
import sys

from .aux_types import SwingIcmr
from .mna_types import Undefined

PAIR = 1 + 1                                    # 차동 출력 = 포트 둘


def _add(u, d):
    return None if u is None or d is None else u + d


def _constraints(devices, rail_nets):
    """차분 제약 ((a, b, c, 허용오차), ...) -- V_a − V_b ≥ c. 입력 순서 그대로(호출자가 정준 순서로 준다)."""
    out = []
    for m in devices:
        if not m.linear:
            hi_net, lo_net = (m.d, m.s) if m.polarity > 0 else (m.s, m.d)
            out.append((hi_net, lo_net, m.sat_v, m.sat_tol_v))
        if m.s not in rail_nets or m.g == m.d:
            shift = m.polarity * m.vgs_v
            out.append((m.g, m.s, shift, m.vgs_tol_v))
            out.append((m.s, m.g, -shift, m.vgs_tol_v))
    return tuple(out)


def _relax(nets, cons, rails):
    """-> ({넷: lo}, {넷: hi}, {넷: lo 허용오차 누적}, {넷: hi 허용오차 누적})."""
    fixed = dict(rails)
    bottom, top = min(fixed.values()), max(fixed.values())
    lo = {n: bottom for n in nets}                  # 모든 노드는 레일 사이(레일 밖 불허, Q4 (4)) -- 출발 구간부터 레일로 자르고 경로 합이 좁힌다
    hi = {n: top for n in nets}
    ulo = {n: 0.0 for n in nets}
    uhi = {n: 0.0 for n in nets}
    for net, v in fixed.items():
        lo[net] = hi[net] = v
    scale = max([abs(v) for v in fixed.values()] + [1.0])
    slack = sys.float_info.epsilon * scale
    for _ in range(len(nets) + 1):
        moved = False
        for a, b, c, d in cons:
            if a not in fixed and lo[b] + c > lo[a] + slack:
                lo[a], ulo[a] = lo[b] + c, _add(ulo[b], d)
                moved = True
            if b not in fixed and hi[a] - c < hi[b] - slack:
                hi[b], uhi[b] = hi[a] - c, _add(uhi[a], d)
                moved = True
        if not moved:
            break
    return lo, hi, ulo, uhi


def _bare(code, detail=()):
    return SwingIcmr(None, None, None, undefined=(Undefined("swing_out_v", code, "definitional", detail),))


def ls_swing(devices, rails, node_v, outputs, diff_outputs=False):
    if not outputs:
        return _bare("no_output_port")
    missing = tuple(m.label for m in devices if not m.linear and m.sat_v is None)
    if missing:
        return _bare("sat_unavailable", (("devices", missing),))
    volts = dict(node_v)
    lacking = tuple(n for n in outputs if n not in volts)
    if lacking:
        return _bare("node_v_missing", (("nets", lacking),))
    nets = sorted({n for m in devices for n in (m.d, m.g, m.s)} | {n for n, _v in rails} | set(outputs))
    lo, hi, ulo, uhi = _relax(nets, _constraints(devices, frozenset(n for n, _v in rails)), rails)
    # 출력 스윙
    ranges = tuple((n, lo[n], hi[n], volts[n]) for n in outputs)
    halves = []
    for n in outputs:
        up, down = hi[n] - volts[n], volts[n] - lo[n]
        halves.append((min(up, down), uhi[n] if up <= down else ulo[n]))
    worst, worst_u = min(halves, key=lambda h: h[0])
    factor = 2 * (1 + int(diff_outputs and len(outputs) == PAIR))
    swing_res = None if worst_u is None else factor * worst_u
    return SwingIcmr(factor * worst, None, None, ranges, swing_resolution=swing_res, bounds=tuple((n, lo[n], hi[n]) for n in nets))
