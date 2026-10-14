"""S1v 매크로 모델 -- 블록 gm·보상 수동소자의 출발값 (설계 41 §6.5, §6.3 극점, D-SIe·D-DN; 단계 A8).

진입점: `macro_solve(ctx, model, gm_id, lengths, refine=True) -> MacroResult`. `refine=False` 면 전원 전류 최소화(SLSQP)를 건너뛰고 실행 가능한 출발점(|H(jω_GBW)| = 1)만 낸다 -- 목표가 이미 달성 불가로 판명된 회로의 반복 비용을 줄인다.

**망**(전달 뷰): 노드 = 이득 블록의 출력 넷 + 그 넷에서 수동소자(커패시터·저항)만 거쳐 닿는 내부 넷. 블록 i 는 VCCS `s_i·gm_i`(입력 넷 -> 출력 넷, 입력 넷이 없으면 포트 여기 1 V)와 출력
컨덕턴스 `G_i = gm_i / A_i`(A_i = 블록 입력 소자의 LUT 진성 이득 gm/gds -- 41 §6.5 마지막 규칙, 캐스코드를 가정하지 않아 보수적)를 가진다. 노드 용량 = (노드에 gate 가 닿는 MOS 의 cgg +
drain 이 닿는 MOS 의 cdd(없으면 cgd)) + 수동소자. 앞의 둘은 소자 전류에 비례하므로 `current_model` 의 아핀 전류로 gm_i 에 선형이다. feedforward 묶음은 탭 -> 합류 VCCS `s_ff·G_ff`
(G_ff = r_ff·gm_in(B_b), r_ff = 1)를 더한다. 수동소자 값: spec 선언값, engine 저항 중 영점 상쇄 구조 규칙(`ZeroCancel`)이 정한 것은 R = 1/Σ_c gm_c(gm_c = I_c·(gm/ID)_c),
그 밖 engine 저항은 θ 상자의 기하 중점(고정), engine 커패시터는 아래 풀이 변수.

**풀이**: 설계 41 §6.5 의 순차 바퀴(gm_1 을 UGF 로 -> gm_k 를 PM 최소로 -> C 를 PM 최소로)는 두 가지로 퇴화해 쓰지 않았다(설계 공백으로 보고). gm_1 을 고정한 채 gm_k 를 줄이면 이득이 1 아래로 떨어져
(i) 이 풀리지 않고, gm_1 을 함께 다시 맞추면 gm_1 의 상자 상한 모서리(수 mA)로 퇴화한다; 실제 UGF 에서 잰 PM 은 모든 gm 을 함께 줄이면 변하지 않아(척도 불변) '최소 gm' 이 하한(1e-25 S)으로 간다.
대신 같은 제약을 한 번에 푼다 -- **제약**: |H(jω_GBW)| = 1(UGF = GBW), PM(ω_GBW) ≥ 목표(교차 주파수를 목표로 고정해 gm_k 와 얽히지 않게), 낮은 극점(주극점)을 뺀 나머지 극점 ≥ ω_GBW·tan(PM)(41 §6.3 의
비주극점 조건), **목적**: 전원 전류 합 최소(KCL 기저에서 정해진 θ 전류의 합; 정해진 것이 없으면 Σgm). 변수 = ln gm_b(블록 입력 소자의 gm), ln C(engine 커패시터; 상자는 θ 상자). 실행 가능한 출발점은
단일 극점 근사 gm = 2π·GBW·C_ref(41 §6.5 '특수 경우')에서 뒤 블록 gm 을 2 배씩 올리며 gm_1 을 UGF 에 맞춰(`bracket_root`) 얻고, SLSQP(`scipy`)가 목적을 줄인다. 극점·영점은 pencil 고유값
(`pencil_roots`, `solve_responses` 가 부른다), 위상 지연·UGF·PM 은 U7 MNA 풀이(`solve_responses`·`analyze_loop`)를 그대로 쓴다 -- 이 파일은 행렬 조립과 제약·목적이다. 출발점이 안 잡히면
`macro_root_missing`, SLSQP 가 제약을 만족하는 해를 못 내면 출발점을 쓰고 `macro_nonconvergent` 를 남긴다(둘 다 보고만, 정지 아님). PM 목표 풀이가 하나도 못 이루어지면 호출부는 출발점 gm 으로 전류를 잡되
그 선택 점을 실행 불가로 센다.
* **PM 목표 없음**: 2극점 근사 PM = atan(f_np/GBW) 에서 f_np = GBW 인 경계(PM = atan(1) = 45°, 비주극점이 UGF 에 놓임)를 PM 하한으로 쓴다 -- 비주극점이 UGF 아래로 내려가면 GBW 라는 양이
  성립하지 않는 경계라 선언이 아니라 구조에서 나온 값이다. 이 사실은 `macro_nonconvergent`/`macro_root_missing` 처럼 기록 코드로 남는다(`pm_floor_pole_at_ugf`).
* **GBW 목표 없음**: 매크로 모델을 돌리지 않는다(`macro_inactive`, 사유 `gbw_target_missing`).
* 허용오차는 상수가 아니라 부동소수 분해능(√ε)이다. 출발값은 판정에 쓰이지 않는다(EP-7).
"""
import math
import sys

import numpy as np
from scipy.optimize import minimize as scipy_minimize

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE
from gmid_engine.metrics import Excitation, Factor, MnaSystem, Sense, analyze_loop, solve_responses
from gmid_engine.sizing import bracket_root

from ._helpers_curves import QUANTITY_GAIN, curve_bundle_of, curve_value
from .dominant_node import dominant_node
from .start_values import MACRO_INACTIVE, MACRO_NONCONVERGENT, MACRO_ROOT_MISSING, PM_FLOOR_DEG, WHY_NO_GBW, MacroResult

_CAPACITOR = "capacitor"
_RESISTOR = "resistor"
_PASSIVE = "passive"
_MOS = "mos"
_KEY_CAPACITANCE = "capacitance"
_KEY_RESISTANCE = "resistance"
_KEY_SS_RESISTANCE = "ss_resistance"
RECORD_PM_FLOOR = "pm_floor_pole_at_ugf"


def _declared_gains(ctx):
    """{블록 키: 진폭비} -- 41 §6.5 의 출력노드 컨덕턴스 G_i = gm_i / A_i 의 A_i. 이득 제약이 있고 모든 블록의 A_i,max 가 인증되면 블록 목표 g_i(`iv_gain_l`: G·A_i,max/ΣA_max)를 쓴다.
    그 밖의 블록은 포함하지 않는다 -- 호출부가 입력 소자의 LUT 진성 이득을 쓴다. 설계의 중간 단계 'g_i 가 없으면 A_i,max'는 쓰지 않았다: 이득 제약이 없는 회로에서 인증 상한을 블록의
    실제 이득으로 가정할 근거가 없고, 독립 test 의 닫힌 식 oracle(A_k = (gm/ID)_k/LAM = 진성 이득)과 어긋난다(보고의 이견 절)."""
    return {} if ctx.gain is None else {spec.key: _amplitude(db) for spec, db in ctx.gain.blocks}


def _amplitude(db):
    return math.exp(db / AMPLITUDE_DB_PER_DECADE / math.log10(math.e))


class _Network:
    """망 구조와 gm·용량 값에서 `MnaSystem` 을 만드는 조립기. 구조는 한 번, 값은 풀이마다."""

    def __init__(self, ctx, model, gm_id, lengths):
        self.ctx, self.model = ctx, model
        self.blocks = model.blocks
        self.records = []
        ground = set(ctx.rails) | set(ctx.transfer.ac_ground)
        self.nodes, passives = self._nodes(ctx, ground)
        self.index = {net: i for i, net in enumerate(self.nodes)}
        n, nb = len(self.nodes), len(self.blocks)
        self.c0, self.kappa = np.zeros(n), np.zeros((n, nb))
        for d in ctx.devices:
            vec, amp = model.mos.get(d.name), model.per_amp.get(d.name)
            if vec is None or amp is None:
                continue
            for net, per_amp in ((d.gate, amp[0]), (d.drain, amp[1])):
                i = self.index.get(net)
                if i is not None:
                    self.kappa[i] += per_amp * vec[:-1]
                    self.c0[i] += per_amp * vec[-1]
        self.a_intr = []
        given = _declared_gains(ctx)
        for b in self.blocks:
            d = ctx.by_name[b.inputs[0]]
            bundle = curve_bundle_of(ctx, d.name, d.kind, lengths[d.name])
            # 버퍼(팔로어) 블록의 출력 컨덕턴스는 gm 이라 이득 1; 이득 블록은 41 §6.5 순서로 g_i(목표 블록 이득) -> A_i,max(U9 인증) -> 입력 소자의 LUT 진성 이득
            if b.buffer:
                self.a_intr.append(1.0)
            elif b.key in given:
                self.a_intr.append(given[b.key])
            else:
                self.a_intr.append(None if bundle is None else curve_value(bundle, QUANTITY_GAIN, gm_id[d.name]))
        self.fixed = {}
        self.variables = {}
        self.stamps = []
        self.zc_fallback = {}
        self.capacitors = ()
        self._passives(ctx, passives, gm_id, ground)
        self.capacitors = tuple(sorted(n for n in self.fixed if ctx.kinds[n] == _CAPACITOR))

    def _nodes(self, ctx, ground):
        outs = [b.out_net for b in self.blocks]
        attach = {}
        for name, pin_map in ctx.pins.items():
            for net in pin_map.values():
                attach.setdefault(net, []).append(name)
        inside = set(outs)
        passives = sorted((n for n, c in ctx.cls.items() if c == _PASSIVE and ctx.kinds[n] in (_CAPACITOR, _RESISTOR)),
                          key=lambda n: (ctx.node_colour.get(next(iter(ctx.pins[n].values())), 0), n))
        added = True
        while added:
            added = False
            for name in passives:
                ends = tuple(ctx.pins[name].values())
                inner = [e for e in ends if e in inside]
                for e in ends:
                    if e in inside or e in ground or not inner:
                        continue
                    if all(ctx.cls[x] == _PASSIVE for x in attach[e]):
                        inside.add(e)
                        added = True
        internal = sorted(inside - set(outs), key=lambda n: (ctx.node_colour.get(n, 0), n))
        used = tuple(n for n in passives if all(e in inside or e in ground for e in ctx.pins[n].values())
                     and any(e in inside for e in ctx.pins[n].values()))
        return tuple(outs) + tuple(internal), used

    def _passives(self, ctx, passives, gm_id, ground):
        for name in passives:
            ends = tuple(self.index.get(e) for e in ctx.pins[name].values())
            declared = ctx.element_values.get(name)
            if declared is not None:
                self.fixed[name] = float(declared)
            elif ctx.kinds[name] == _CAPACITOR:
                box = ctx.box.get((_KEY_CAPACITANCE, name)) or ctx.theta_bounds.get(name)
                if box is None:
                    self.records.append((MACRO_ROOT_MISSING, (("variable", name), ("condition", "capacitance_box_undeclared"))))
                    continue
                self.variables[name] = box
                self.fixed[name] = math.sqrt(box[0] * box[1])
            else:
                zc = ctx.zero_cancel.get(name)
                box = ctx.box.get((_KEY_RESISTANCE, name)) or ctx.box.get((_KEY_SS_RESISTANCE, name)) or ctx.theta_bounds.get(name)
                if zc is not None and zc.reason is None and zc.cells:
                    if box is not None:                  # 구성 소자 전류를 정하지 못해 1/Σgm 이 정의되지 않을 때의 대체값 = θ 상자 기하 중점
                        self.zc_fallback[name] = math.sqrt(box[0] * box[1])
                    self.stamps.append(("zc", name, ends, zc.cells))
                    continue
                if box is None:
                    self.records.append((MACRO_ROOT_MISSING, (("variable", name), ("condition", "resistance_box_undeclared"))))
                    continue
                self.fixed[name] = math.sqrt(box[0] * box[1])
            self.stamps.append((ctx.kinds[name], name, ends, None))

    def zc_value(self, name, cells, gm, gm_id):
        """영점 상쇄 저항 R = 1/Σ_c gm_c (gm_c = I_c·(gm/ID)_c). 구성 소자 전류를 모르면 θ 상자 기하 중점, 그것도 없으면 None(열림)."""
        total = sum(float(self.model.mos[x][:-1] @ gm + self.model.mos[x][-1]) * gm_id[x] for x in cells if x in self.model.mos)
        return 1.0 / total if total > 0 else self.zc_fallback.get(name)

    def system(self, gm, values, gm_id):
        n = len(self.nodes)
        g, c, bg = np.zeros((n, n)), np.diag(self.c0 + self.kappa @ gm), np.zeros(n)
        for i, b in enumerate(self.blocks):
            o = self.index[b.out_net]
            g[o, o] += gm[i] / self.a_intr[i]
            if b.in_net is None:
                bg[o] += b.sign * gm[i]
            else:
                g[o, self.index[b.in_net]] -= b.sign * gm[i]
        for tap, merge, sign, vec in self.model.ff:
            m = self.index.get(merge)
            if m is None:
                continue
            gm_ff = float(vec[:-1] @ gm + vec[-1])
            if tap in self.index:
                g[m, self.index[tap]] -= sign * gm_ff
            else:
                bg[m] += sign * gm_ff
        for kind, name, ends, cells in self.stamps:
            a, b = ends
            if kind == "zc":
                value, kind = self.zc_value(name, cells, gm, gm_id), _RESISTOR
                if value is None:
                    continue
            else:
                value = values.get(name, self.fixed[name])
            target, weight = (g, 1.0 / value) if kind == _RESISTOR else (c, value)
            for p, q, w in ((a, a, weight), (b, b, weight), (a, b, -weight), (b, a, -weight)):
                if p is not None and q is not None:
                    target[p, q] += w
        charge = tuple(i for i in range(n) if not g[i].any())
        sense = np.zeros((1, n))
        out = self._sense_node()
        sense[0, out] = 1.0
        return MnaSystem(tuple(range(n)), (), g, c, bg[:, None], np.zeros((n, 1)), sense, np.zeros((1, 1)),
                         (Excitation("stimulus", currents=((0, 1.0),)),), (Sense(out),), charge, ())

    def _sense_node(self):
        sensed = [self.index[n] for n in self.ctx.transfer.sense if n in self.index]
        return min(sensed) if sensed else self.index[self.blocks[-1].out_net]

    def at_target(self, gm, values, gm_id, omega):
        """목표 교차 주파수 ω(= 2π·GBW)에서의 (|H(jω)|, 위상 여유 deg 또는 None, 계 극점). 위상 여유 = 180° − (T(0) 대비 ω 까지 누적 위상 지연); 격자(`solve_responses` 의 ω 격자, 극점 기준)
        위 위상을 펴고 ω 의 정확한 값을 덧붙여 지연을 잰다. 개방 우반면 극점이 있으면 None(metrics `analyze_loop` 와 같은 전제)."""
        system = self.system(gm, values, gm_id)
        resp = solve_responses((system,))[0]
        try:
            h = complex(system.sense_rows[0] @ np.linalg.solve(system.G + complex(0, omega) * system.C, system.BG[:, 0]))
        except np.linalg.LinAlgError:
            return 0.0, None, ()
        grid, samples = np.asarray(resp.omegas), resp.values[:, 0, 0]
        keep = grid < omega
        poles = resp.roots.poles
        if any(p.real > 0 for p in poles) or not np.isfinite(samples[keep]).all():
            return abs(h), None, poles
        phase = np.unwrap(np.angle(np.concatenate([samples[keep], [h]])))
        return abs(h), math.degrees(math.pi - (phase[0] - phase[-1])), poles

    def analyse(self, gm, values, gm_id):
        resp = solve_responses((self.system(gm, values, gm_id),))[0]
        loop = analyze_loop((Factor(resp, 0, 0),))
        return loop.ugf_hz, loop.phase_margin_deg, resp.roots.poles


def _signed(value, target):
    """근 찾기 함수 값: 정의되지 않은 양은 부호만 아는 ±inf (None -> 목표 아래)."""
    return -math.inf if value is None else value - target


def macro_solve(ctx, model, gm_id, lengths, refine=True):
    if ctx.gbw_hz is None:
        return MacroResult((), (), (), None, None, 0, ((MACRO_INACTIVE, (("reason", WHY_NO_GBW),)),), ())
    pm_target = ctx.pm_deg
    records = []
    if pm_target is None:
        pm_target = PM_FLOOR_DEG
        records.append((RECORD_PM_FLOOR, (("pm_deg", pm_target),)))
    if not model.blocks or any(not b.inputs for b in model.blocks):
        return MacroResult((), (), (), None, None, 0, ((MACRO_INACTIVE, (("reason", "block_input_device_missing"),)),), ())
    net = _Network(ctx, model, gm_id, lengths)
    records.extend(net.records)
    if any(a is None for a in net.a_intr):
        return MacroResult((), (), (), None, None, 0, tuple(records) + ((MACRO_INACTIVE, (("reason", "intrinsic_gain_curve_undefined"),)),), ())
    return _iterate(ctx, net, gm_id, pm_target, records, refine)


def _solve(f, x0, lo, hi, tol, minimal):
    """f(x) = 0 의 1-D 근. f 는 x 에 대해 증가한다(UGF·PM 모두 gm·C 에 대해 증가) -- 시작점 x0 에서 2 배(ln 2 = log1p(1))씩 넓혀 부호가 바뀌는 괄호를 잡고 `bracket_root`.
    반환 (x 또는 None, 사유 또는 None). minimal=True 이고 하한까지 f ≥ 0(이미 만족)이면 x = lo."""
    step = math.log1p(1)
    f0 = f(x0)
    if f0 == 0:
        return x0, None
    if f0 < 0:
        a, b = x0, min(x0 + step, hi)
        while f(b) < 0:
            if b >= hi:
                return None, "target_not_reached_at_upper_limit"
            a, b = b, min(b + step, hi)
    else:
        a, b = max(x0 - step, lo), x0
        while f(a) > 0:
            if a <= lo:
                return (lo, None) if minimal else (None, "target_exceeded_at_lower_limit")
            a, b = max(a - step, lo), a
    x, _f_lo, _f_hi = bracket_root(f, a, b, tol)
    if x is None:
        return None, "no_sign_change_in_range"
    return (x + tol if minimal else x), None          # minimal: 근의 만족하는 쪽(f 는 증가)으로 한 허용오차만큼


def _power(ctx, net, gm):
    """전원 전류 합(A) -- 값이 정해진 θ 전류 원소(KCL 독립 기저)의 합. 기저에서 정해진 것이 없으면 Σ gm."""
    free = [net.model.affine[e] for e in ctx.basis.free if e in net.model.affine]
    return float(sum(v[:-1] @ gm + v[-1] for v in free)) if free else float(np.sum(gm))


def _iterate(ctx, net, gm_id, pm_target, records, refine):
    """풀이: gm_1 을 UGF = GBW(|H(jω_GBW)| = 1)로 맞춘 **실행 가능한 출발점**에서 시작해, 같은 제약(|H(jω_GBW)| = 1, PM(ω_GBW) ≥ 목표)을 지키는 전원 전류 합 최소점을 SLSQP 로 찾는다.
    41 §6.5 의 순차 바퀴(gm_1 -> gm_k 최소 -> C 최소)는 gm_1 을 고정한 채 gm_k 를 줄이면 이득이 1 아래로 떨어져 풀리지 않거나, gm_1 을 함께 맞추면 gm_1 상자 상한 모서리로 퇴화한다
    (`macro_nonconvergent` 가 아니라 구조적 퇴화 -- 설계 공백으로 보고). 같은 제약 아래 '최소'를 전원 전류 합 최소로 한 번에 푼다."""
    blocks = net.blocks
    nb = len(blocks)
    tol = math.sqrt(sys.float_info.epsilon)
    first = [ctx.by_name[b.inputs[0]] for b in blocks]
    box = [ctx.current_box[d.kind] for d in first]
    lo = [math.log(box[i][0] * gm_id[first[i].name]) for i in range(nb)]
    hi = [math.log(box[i][1] * gm_id[first[i].name]) for i in range(nb)]
    cap_names = sorted(net.variables)
    cap_lo = [math.log(net.variables[n][0]) for n in cap_names]
    cap_hi = [math.log(net.variables[n][1]) for n in cap_names]
    omega = math.tau * ctx.gbw_hz
    c_ref = max((net.fixed[n] for n in net.capacitors), default=None)
    start = [math.log(math.tau * ctx.gbw_hz * c_ref) if c_ref is not None else (lo[i] + hi[i]) / 2 for i in range(nb)]
    start = [min(max(start[i], lo[i]), hi[i]) for i in range(nb)]
    cap0 = [math.log(net.fixed[n]) for n in cap_names]
    missing = {}

    def unpack(z):
        return np.exp(np.asarray(z[:nb], dtype=float)), {n: math.exp(z[nb + j]) for j, n in enumerate(cap_names)}

    last = []                # [(점, 결과)] -- 가장 최근 한 점만 둔다(상한 1)

    def mag_pm(z):
        # SLSQP 는 한 점에서 등식·부등식 제약과 목적을 연달아 부른다 -- 같은 점은 한 번만 푼다
        key = tuple(float(v) for v in z)
        if not last or last[0][0] != key:
            gm, vals = unpack(z)
            last[:] = [(key, net.at_target(gm, vals, gm_id, omega))]
        return last[0][1]

    def log_mag(z):
        mag = mag_pm(z)[0]
        return math.log(mag) if mag > 0 else -math.inf

    step = math.log1p(1)

    def feasible_start(k):
        """블록 k 의 gm 으로 UGF = GBW 를 맞춘 실행 가능한 출발점(나머지 블록 gm 을 2 배씩 올려 가며). 블록 k 가 낮은 극점(주극점)이 되는 출발점이다. 없으면 None."""
        z = start + cap0
        while True:
            def f(v, z=z):
                return log_mag(z[:k] + [v] + z[k + 1:nb] + z[nb:])
            v, _why = _solve(f, z[k], lo[k], hi[k], tol, False)
            if v is not None:
                return z[:k] + [v] + z[k + 1:]
            if nb == 1 or all(z[i] >= hi[i] for i in range(nb) if i != k):
                return None
            z = [z[i] if i == k else min(z[i] + step, hi[i]) for i in range(nb)] + z[nb:]

    # 출발 순서: 구조로 정한 주극점 노드(`dominant_node`, 41 §6.3)의 블록을 먼저, 그 뒤 나머지 블록 순서 -- 같은 전류면 구조 쪽을 쓴다
    front = dominant_node(ctx.transfer).nets
    order = sorted(range(nb), key=lambda i: (blocks[i].out_net not in front, i))
    starts = [(k, feasible_start(k)) for k in (order if refine else order[:1])]
    starts = [(k, z) for k, z in starts if z is not None]
    z = starts[0][1] if starts else start + cap0
    feasible = bool(starts)
    sweeps = 0
    if feasible and refine and nb + len(cap_names) > 1:
        # 비볼록: 주극점이 어느 단에 놓이는지가 국소 최소를 가른다(순차 바퀴가 퇴화하는 이유와 같은 구조) -- 단마다 그 단을 주극점으로 하는 실행 가능한 출발점에서 SLSQP 를 돌려 전원 전류가
        # 가장 작은 만족해를 쓴다(다중 출발). 하나도 만족하지 못하면 첫 출발점을 쓰고 `macro_nonconvergent`.
        bounds = list(zip(lo, hi)) + list(zip(cap_lo, cap_hi))
        omega_np = omega * math.tan(math.radians(pm_target))        # 2극점 근사 PM = atan(ω_np/ω_GBW): 낮은 극점(주극점)을 뺀 나머지 극점은 ω_np 이상 (41 §6.3)
        scale = _power(ctx, net, unpack(starts[0][1])[0])
        best, last_message = None, ""
        for k, z0 in starts:
            out = scipy_minimize(lambda w: _power(ctx, net, unpack(w)[0]) / scale, np.asarray(z0, dtype=float), method="SLSQP", bounds=bounds,
                                 constraints=[{"type": "eq", "fun": lambda w: log_mag(w) if np.isfinite(log_mag(w)) else -1.0 / tol},
                                              {"type": "ineq", "fun": lambda w: _signed_pm(mag_pm(w)[1], pm_target)},
                                              {"type": "ineq", "fun": lambda w: _pole_margin(mag_pm(w)[2], omega_np)}])
            sweeps += int(out.nit)
            last_message = str(out.message)
            candidate = [float(t) for t in out.x]
            mag_c, pm_c, poles_c = mag_pm(candidate)
            if (out.success and abs(math.log(mag_c)) <= math.sqrt(tol) and pm_c is not None and pm_c >= pm_target - math.sqrt(tol)
                    and _pole_margin(poles_c, omega_np) >= -math.sqrt(tol)):
                power = _power(ctx, net, unpack(candidate)[0])
                if best is None or power < best[0] * (1 - tol):
                    best = (power, candidate, k)
        if best is not None:
            z = best[1]
        else:
            records.append((MACRO_NONCONVERGENT, (("sweeps", sweeps), ("status", last_message))))
    elif not feasible:
        missing["gm:" + "/".join(blocks[0].key)] = "target_not_reached_at_upper_limit"
    gm, values = unpack(z)
    ugf, pm, poles = net.analyse(gm, values, gm_id)
    if feasible:
        pm_t = net.at_target(gm, values, gm_id, omega)[1]
        if pm_t is None or pm_t < pm_target - math.sqrt(tol):
            missing["pm"] = "pm_target_not_met_within_ranges"
    for label, why in sorted(missing.items()):
        records.append((MACRO_ROOT_MISSING, (("variable", label), ("condition", why))))
    resistors = []
    for kind, name, _ends, cells in net.stamps:
        if kind == "zc":
            value = net.zc_value(name, cells, gm, gm_id)
            if value is not None:
                resistors.append((name, value))
    return MacroResult(tuple((b.key, float(gm[i])) for i, b in enumerate(blocks)),
                       tuple((name, float(values[name])) for name in cap_names), tuple(resistors), ugf, pm, sweeps, tuple(records),
                       tuple(sorted(abs(p) / math.tau for p in poles)))


def _pole_margin(poles, omega_np):
    """비주극점 조건 값: (두 번째로 낮은 극점 크기 / ω_np) − 1 (극점이 둘 미만이면 0 = 제약 없음). 주극점은 가장 낮은 극점이다."""
    mags = sorted(abs(p) for p in poles if abs(p) > 0)
    return 0.0 if len(mags) <= 1 or not omega_np > 0 else mags[1] / omega_np - 1


def _signed_pm(pm, target):
    """부등식 제약 값: 정의되지 않은 PM(개방 우반면 극점)은 한 단위 크기의 위반으로 센다(경사를 만들지 않는다)."""
    return -1.0 if pm is None else pm - target
