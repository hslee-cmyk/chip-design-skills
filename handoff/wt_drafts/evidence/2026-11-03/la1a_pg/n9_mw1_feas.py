"""D3: M-W1 입력 'library front 점' 교착 판정과 '봉인 통과 점'으로 넓힐 때의 실현 가능성. 엔진 무변경(integ-it12 import).

M-W1 자체가 아니다. 물음은 '그 점에서 Q-W1을 물을 수 있나'다.
(1) as-built find_front(E_B 40, 시제품 출발 없음)로 13회로 front 수·봉인 점 수를 다시 잰다. ngcc는 O-216 내용 TEMP.
(2) 봉인 점(front 우선, 없으면 봉인 cache에서 균등 5점)마다
    r = m·w_s/W(s) − 1 (W(s) = I·L/IDu_s, 후보 = W_min ≤ w_s ≤ w_hi, |r| 최소, 같으면 w_s 큰 쪽 -- P:305 손가락 선택).
    스크립트 안 LUT KCL Newton으로 두 측정 구성을 푼다(계획 P:1218):
    fixed = 선언 입력 고정, 출력 미지수 / servo = 출력을 봉인점 값에 고정, 입력 차 미지수.
    기록: 수렴 여부, ΔV_out, ΔV_id, 포화 깨짐 수(VDS < VDSAT), 첫 Newton 걸음(1차 근사 -- DEC-23 성분 (3) 식 자체는 아님), gain 값.
    기준 점검: 재풀이 전 W·기준 슬라이스 KCL 잔차가 작아야 스크립트 KCL을 믿는다(baseline_max_rel).
수렴 판정 1e-6은 이 스크립트의 측정 허용오차이고 계획 문턱이 아니다.
결과 = n9_mw1_feas.jsonl, 회로마다 append."""
import collections
import json
import math
import pathlib
import sys
import time
import traceback

from n0_common import *  # noqa: F401,F403
import numpy
from gmid_engine.graph import MOS_TERMINAL_NAMES
from gmid_engine.lut import vdsat
from gmid_engine.lut.point_query import op_point
from gmid_engine.metrics import theta_passive_pairs
from gmid_engine.sizing._helpers_lut import terminal_voltages

OUT = pathlib.Path(__file__).parent / "n9_mw1_feas.jsonl"
NAMES = sys.argv[1:] or sorted(p.name[:-len(".sizing_spec.json")] for p in LIB.glob("*.sizing_spec.json"))
RAW = {}
_orig_record = km._record


def _rec(sctx, result, origin):
    RAW[result.key] = raw_now() if result.status == "sealed" else {}
    return _orig_record(sctx, result, origin)


km._record = _rec


def emit(rec):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


class Net:
    def __init__(self, sctx, r, ports, memo):
        snap = r.evaluation.snapshot
        self.memo = memo
        self.ops = dict(snap.column("device", "dc_op"))
        self.pins = {n: dict(p) for n, p in snap.column("device", "pins")}
        self.bulk = {n: b.net for n, b in snap.column("device", "bulk")}
        self.classes = dict(snap.column("device", "element_class"))
        self.currents = dict(snap.column("device", "dc_current"))
        self.rails = set(dict(snap.column("node", "dc_rail_v")))
        self.values = dict(snap.column("node", "dc_rail_v"))
        self.values.update(snap.column("node", "dc_v"))
        basis = dict(snap.column("graph", "dc_current_basis"))
        self.ends = next(iter(basis.values())).ends
        self.R = dict(sctx.dc.inputs.element_values)
        self.R.update(theta_passive_pairs(r.theta))
        self.inputs = sorted(k for k, v in ports.items() if isinstance(v, dict) and v.get("direction") == "input")
        self.outputs = sorted(k for k, v in ports.items() if isinstance(v, dict) and v.get("direction") == "output")
        self.geom = {m: (op.w_key, op.W) for m, op in self.ops.items()}

    def term(self, m, v):
        p = self.pins[m]
        op = self.ops[m]
        d, g, s_ = (p[t] for t in MOS_TERMINAL_NAMES)
        return terminal_voltages(op.kind, v[d], v[g], v[s_], v[self.bulk[m]])

    def i_mos(self, m, v, geom):
        op = self.ops[m]
        vgs, vds, vsb = self.term(m, v)
        key, W = geom[m]
        return op_point(self.memo, op.kind, key, op.L, vgs, vds, vsb).IDu * W / op.L

    def flows(self, v, geom):
        out = collections.defaultdict(float)
        scale = collections.defaultdict(float)
        for name, a, b in self.ends:
            cls = self.classes.get(name)
            if name in self.ops:
                i = self.i_mos(name, v, geom)
            elif name in self.R and self.R[name]:
                i = (v[a] - v[b]) / float(self.R[name])
            else:
                i = float(self.currents.get(name) or 0.0)
            for net, s in ((a, 1), (b, -1)):
                if net not in self.rails:
                    out[net] += s * i
                    scale[net] += abs(i)
        return out, scale

    def saturation_breaks(self, v, geom):
        n, names = 0, []
        for m, op in self.ops.items():
            vgs, vds, vsb = self.term(m, v)
            sat = vdsat(self.memo, op.kind, geom[m][0], op.L, vgs, vds, vsb)
            if vds < sat:
                n += 1
                names.append(m)
        return n, names


def realize(net, kind_slices, w_min, grid):
    """P:305 손가락 선택. 반환 {소자: (key, W', r, m, w_s)}."""
    out, fail = {}, {}
    for m, op in net.ops.items():
        sl = net.memo.lut.slice_map[(op.kind, op.w_key)]
        w_hi = sl.l_bins.w_bin[1] if sl.l_bins and sl.l_bins.bins else None
        best = None
        for key, w_s in kind_slices[op.kind]:
            if w_s < w_min - grid / 2 or (w_hi is not None and w_s > w_hi + grid / 2):
                continue
            try:
                W = op.current * op.L / op_point(net.memo, op.kind, key, op.L, op.vgs, op.vds, op.vsb).IDu
            except Exception:
                continue
            k = max(1, round(W / w_s))
            r = k * w_s / W - 1
            cand = (abs(r), -w_s, key, k * w_s, r, k, w_s)
            if best is None or cand[:2] < best[:2]:
                best = cand
        if best is None:
            fail[m] = "slice 없음"
        else:
            out[m] = (best[2], best[3], best[4], best[5], best[6])
    return out, fail


def newton(net, geom, unknown, assign, x0, eqs, iters=60):
    """x 미지수, assign(x) -> 노드 전압, eqs = KCL 쓰는 넷. 첫 걸음과 끝 해를 돌려준다."""
    def f(x):
        v = assign(x)
        fl, sc = net.flows(v, geom)
        return numpy.array([fl.get(n, 0.0) for n in eqs]), numpy.array([max(sc.get(n, 0.0), 1e-30) for n in eqs])

    x = numpy.array(x0, float)
    first = None
    fx, sc = f(x)
    for it in range(iters):
        rel = float(numpy.max(numpy.abs(fx) / sc)) if len(fx) else 0.0
        if rel < 1e-6:
            return dict(ok=True, iters=it, rel=rel), x, first
        J = numpy.zeros((len(eqs), len(x)))
        for j in range(len(x)):
            xp = x.copy()
            xp[j] += 1e-5
            fp, _ = f(xp)
            J[:, j] = (fp - fx) / 1e-5
        step = numpy.linalg.lstsq(J, -fx, rcond=None)[0]
        if first is None:
            first = step.copy()
        lim = float(numpy.max(numpy.abs(step)))
        if lim > 0.1:
            step = step * 0.1 / lim
        a, done = 1.0, False
        n0 = float(numpy.linalg.norm(fx / sc))
        while a > 1e-3:
            try:
                fn, sn = f(x + a * step)
                if float(numpy.linalg.norm(fn / sn)) < n0 or a <= 2e-3:
                    x, fx, sc, done = x + a * step, fn, sn, True
                    break
            except Exception:
                pass
            a /= 2
        if not done:
            return dict(ok=False, iters=it, why="line_search_or_lut_domain", rel=rel), x, first
    return dict(ok=False, iters=iters, why="iter_limit", rel=rel), x, first


def measure_point(net, kind_slices, w_min, grid):
    rec = {}
    fl, sc = net.flows(net.values, net.geom)
    rec["baseline_max_rel"] = max((abs(fl[n]) / max(sc[n], 1e-30) for n in fl), default=0.0)
    rec["sat_breaks_base"] = net.saturation_breaks(net.values, net.geom)[0]
    real, fail = realize(net, kind_slices, w_min, grid)
    rec["unrealizable"] = fail
    rs = sorted(abs(v[2]) for v in real.values())
    rec["r_abs"] = dict(n=len(rs), med=rs[len(rs) // 2] if rs else None, max=rs[-1] if rs else None,
                        worst=max(real, key=lambda m: abs(real[m][2])) if real else None)
    rec["devices"] = {m: dict(r=real[m][2], m=real[m][3], w_s_um=real[m][4] * 1e6, gm_id=net.ops[m].gm_id) for m in real}
    if fail:
        rec["fixed"] = rec["servo"] = dict(ok=False, why="unrealizable")
        return rec
    geom = {m: (real[m][0], real[m][1]) for m in real}
    nets = sorted(set(fl) - net.rails - set(net.inputs))
    # 선언 입력 고정
    def a_fix(x):
        v = dict(net.values)
        v.update(zip(nets, x))
        return v
    try:
        st, x, first = newton(net, geom, nets, a_fix, [net.values[n] for n in nets], nets)
        v = a_fix(x)
        rec["fixed"] = dict(st, dV_out={o: v[o] - net.values[o] for o in net.outputs if o in v},
                            dV_out_first={o: float(first[nets.index(o)]) for o in net.outputs if first is not None and o in nets},
                            sat_breaks=net.saturation_breaks(v, geom)[0] if st["ok"] else None,
                            max_dv=max((abs(v[n] - net.values[n]) for n in nets), default=0.0))
    except Exception as exc:
        rec["fixed"] = dict(ok=False, why="%s: %s" % (type(exc).__name__, str(exc)[:160]))
    # servo: 출력 하나, 입력 차 하나
    if len(net.outputs) != 1 or not (1 <= len(net.inputs) <= 2) or net.outputs[0] not in nets:
        rec["servo"] = dict(ok=False, why="n/a inputs=%s outputs=%s" % (net.inputs, net.outputs))
        return rec
    out = net.outputs[0]
    others = [n for n in nets if n != out]
    signs = {net.inputs[0]: 0.5, net.inputs[1]: -0.5} if len(net.inputs) == 2 else {net.inputs[0]: 1.0}
    def a_servo(x):
        v = dict(net.values)
        v.update(zip(others, x[:-1]))
        for n, s in signs.items():
            v[n] = net.values[n] + s * x[-1]
        return v
    try:
        st, x, first = newton(net, geom, others, a_servo, [net.values[n] for n in others] + [0.0], nets)
        v = a_servo(x)
        rec["servo"] = dict(st, dV_id=float(x[-1]), dV_id_first=float(first[-1]) if first is not None else None,
                            sat_breaks=net.saturation_breaks(v, geom)[0] if st["ok"] else None,
                            max_dv=max((abs(v[n] - net.values[n]) for n in others), default=0.0))
    except Exception as exc:
        rec["servo"] = dict(ok=False, why="%s: %s" % (type(exc).__name__, str(exc)[:160]))
    return rec


for c in NAMES:
    rec = {"circuit": c, "engine": ENGINE_ROOT}
    t0 = time.time()
    try:
        sctx = build_ctx(c, eval_budget=40, budget_s=300.0)
        memo = sctx.dc.lut.memo
        RAW.clear()
        fr = find_front(sctx, [])
        res = [r for r in sctx.cache.values() if getattr(r, "seq", -1) >= 0]
        sealed = sorted((r for r in res if r.status == "sealed" and r.evaluation is not None), key=lambda r: r.seq)
        front = [p.result for p in fr.front]
        tg = targets(sctx)
        rec.update(status="searched", n_eval=len(res), n_sealed=len(sealed), n_front=len(front), E_B=sctx.eval_budget,
                   targets={k: list(v) for k, v in tg.items()}, stop=[str(s)[:160] for s in (getattr(fr, "stop_reasons", ()) or ())][:4])
        pts = front if front else sealed
        pool = "front" if front else "sealed"
        if len(pts) > 5:
            idx = sorted({round(i * (len(pts) - 1) / 4) for i in range(5)})
            pts = [pts[i] for i in idx]
        topo = json.loads((LIB / (c + ".topology.json")).read_text(encoding="utf-8"))
        lut = memo.lut
        grid = lut.spec.manufacturing_grid_m
        kind_slices = collections.defaultdict(list)
        for (kd, key), sl in lut.slice_map.items():
            if sl.l_bins and sl.l_bins.bins:
                kind_slices[kd].append((key, sl.w_m))
        w_min = float(dict(read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), BoundedLRU(4)).quantities)["min_finger_w_m"].value_m)
        rec["pool"] = pool
        rec["points"] = []
        for r in pts:
            net = Net(sctx, r, topo.get("ports", {}), memo)
            pr = {"seq": r.seq, "raw": {k: RAW.get(r.key, {}).get(k) for k in ("gain_ss_db", "gbw_ss_hz", "pm_ss_deg")}, "inputs": net.inputs, "outputs": net.outputs}
            try:
                pr.update(measure_point(net, kind_slices, w_min, grid))
            except Exception as exc:
                pr["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:200])
                pr["trace"] = traceback.format_exc()[-600:]
            rec["points"].append(pr)
    except BaseException as exc:
        rec.update(status="stopped", error="%s: %s" % (type(exc).__name__, str(exc)[:300]), trace=traceback.format_exc()[-800:])
    rec["s"] = round(time.time() - t0, 1)
    emit(rec)
    print(c, rec.get("status"), rec.get("n_front"), rec.get("n_sealed"), rec["s"], flush=True)
