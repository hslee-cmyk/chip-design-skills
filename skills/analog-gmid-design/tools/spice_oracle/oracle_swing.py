# -*- coding: utf-8 -*-
"""oracle_swing.py -- 출력 스윙·입력 공통모드 범위(ICMR)의 ngspice `.op` 스윕 측정 (설계 40 §3.8-8·§10.2, 사용자 결정 2026-10-08 Q4).

진입점(단독 실행):
    python oracle_swing.py <oracle_input.json> <netlist.cir> <out_swing.json> --ngspice <ngspice_con.exe>
                           [--timeout-s S] [--cache-dir D] [--sat-margin-v V]

  <netlist.cir> = oracle_netlist.py 가 쓴 free 본 넷리스트(+ .meta.json). 입력 JSON 의 `swing_icmr` 블록이 있을 때만 의미가 있다.
  엔진을 import 하지 않는다. 결과 JSON = swing_icmr_measure() 의 반환.

입력 `swing_icmr` 블록(선택): {"swing": true, "icmr": true, "input_dc_V": 값(선택, icm_margin 용 선언 입력 DC; 없으면 예측 입력 DC),
  "input_dc_pending": true(선택: SP-2 대기 -- icm_margin 을 내지 않고 input_dc_pending 으로 보고)}.

측정 정의
  * 포화 조건(한 점): 도통 중인 MOS(|ID| > off 문턱: judge.off_current_A, 없으면 0) 전부 VDS >= VDSAT + 포화 여유(judge.sat_margin_V, 없으면 0).
    도통 안 하는 소자는 조건에서 뺀다. (README 합격 정의의 포화 조건과 같다 -- 사용자 SPICE 포화 규칙.)
  * 스윕 변수는 free 넷리스트의 DC servo 기준원을 바꾼다(회로를 고치지 않음):
      - 입력 공통모드 Δ: 입력 넷마다 `Vofs_<넷>`(servo 있는 입력) 의 DC 에서 Δ 를 빼고 `Vdc_<넷>`(servo 없는 입력)에는 Δ 를 더한다 --
        출력 servo 기준은 그대로이므로 출력은 예측 DC 에 묶인 채 입력 CM 만 움직인다.
      - 단일 출력 목표 Vt: `Vofs_<servo 입력>` 에 (Vt - Vo,pred) 를 더한다. 차동 출력 목표 D = V(op) - V(on): 두 servo 입력의 기준을 ∓k·D
        (k = testbench.ac.diff_feedback_gain)만큼 밀어 D 를 servo 가 맞추게 한다(공통모드는 회로의 CMFB 가 정함).
    servo 가 없는 입력/출력(되먹임이 없는 회로)은 그 스윕을 할 수 없다 -> status = unavailable + 이유.
  * 창 = 공칭점(Δ = 0, Vt = Vo,pred, D = 0)에서 포화 조건이 이어지는 연속 구간. 거친 격자(간격 = V_T = kT/q -- 소신호 선형화의 물리 척도)로 한
    번의 ngspice 실행에서 점마다 `alter` + `op`, 그 뒤 경계 괄호([마지막 통과, 첫 실패])를 7 점 부분 격자로 줄여 가며(최대 ZOOM_ROUNDS 회,
    목표 분해능 = reltol·레일 폭) 경계를 구한다. 점이 수렴하지 않으면 그 점은 포화 아님으로 센다(fail-closed).
  * swing_out_v: 단일 출력 2·min(V_hi - Vo, Vo - V_lo), 차동 출력 2·min(D_hi, -D_lo) (D 는 측정된 V(op)-V(on); 설계 40 §3.8-8: 출력마다
    반폭 min × 4 와 같다). 공칭점이 이미 포화 조건을 어기면 음수(= -(최대 부족량 vdsat + margin - vds))를 낸다.
  * icmr_v: 입력 CM 창 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi] 의 폭; 공칭점이 어기면 음수 부족량.
  * icm_margin_v: 선언 입력 DC 와 창 경계의 최소 거리 min(V_icm - Vin,min, Vin,max - V_icm) (창 밖이면 음수).
"""
import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_simulate import parse_op, reltol_of, run_ngspice, thermal_voltage  # noqa: E402

ZOOM_POINTS = 7       # 경계 괄호를 한 라운드에 (ZOOM_POINTS + 1) 등분
ZOOM_ROUNDS = 8


def _rails(inp):
    v = [float(r["voltage"]) for r in inp["rails"]]
    return min(v), max(v)


def _src_lines(text, prefix):
    out = {}
    for raw in text.splitlines():
        tok = raw.split()
        if tok and tok[0].startswith(prefix):
            out[tok[0][len(prefix):]] = tok
    return out


def _control_block(text):
    """본 넷리스트 .control 의 `op` ... `echo OPEND` 줄들(소자 probe 인쇄 포함)."""
    ln = text.splitlines()
    i0 = next(i for i, x in enumerate(ln) if x.strip().lower() == "op")
    i1 = next(i for i, x in enumerate(ln) if x.strip() == "echo OPEND")
    return ln[i0:i1 + 1]


class _Sweeper:
    """점 목록(소스 DC 변경 사전)을 한 번의 ngspice 실행으로 풀어 점마다 parse_op 결과를 돌려준다."""

    def __init__(self, cir_path, meta, inp, exe, timeout_s, cache_dir, tag):
        self.cir, self.meta, self.inp, self.exe = cir_path, meta, inp, exe
        self.timeout_s, self.cache_dir, self.tag = timeout_s, cache_dir, tag
        with open(cir_path, encoding="utf-8") as fh:
            self.text = fh.read()
        self.body = []
        for raw in self.text.splitlines():
            if raw.strip().lower().startswith(".control"):
                break
            self.body.append(raw)
        self.ctrl = _control_block(self.text)
        self.n_runs = 0
        self.base = {}
        for kind in ("Vofs_", "Vdc_"):
            for net, tok in _src_lines(self.text, kind).items():
                self.base[kind + net] = float(tok[tok.index("DC") + 1])

    def run(self, points, label):
        import subprocess
        d = os.path.dirname(os.path.abspath(self.cir))
        stem = os.path.splitext(os.path.basename(self.cir))[0]
        c = [".control", "set noaskquit"]
        for k, pt in enumerate(points):
            for src, val in pt.items():
                c.append(f"alter {src.lower()} dc = {val:.12g}")
            c.append(f"echo SWP {k}")
            c += self.ctrl
        c += ["quit", ".endc", ".end"]
        self.n_runs += 1
        scir = os.path.join(d, f"{stem}.{self.tag}.{label}{self.n_runs}.cir")
        with open(scir, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.body + c) + "\n")
        try:
            rc, log, _ = run_ngspice(self.exe, scir, os.path.splitext(scir)[0] + ".log", self.timeout_s, self.cache_dir, [])
        except subprocess.TimeoutExpired:
            return None
        blocks = re.split(r"^SWP\s+\d+\s*$", log, flags=re.M)[1:]
        out = []
        for blk in blocks:
            blk = blk.split("OPSTART", 1)[-1]
            out.append(parse_op(blk, self.meta))
        return out if len(out) == len(points) else (out + [None] * (len(points) - len(out)))


def sat_violation(res, margin, off_i, rails=None):
    """한 점 판정: (모든 도통 MOS 포화인가, 최대 부족량 = max(vdsat + margin - vds) [V], 도통 소자 수). 풀이가 없으면 (False, None, 0).
    rails = (rail_lo, rail_hi, 허용) 이면 회로 노드 전압이 [rail_lo - 허용, rail_hi + 허용] 밖인 점도 위반(이상 전류원 꼬리가 레일 밖으로
    내려가는 따위의 비물리 해를 창에 넣지 않는다; 부족량에는 레일 밖으로 나간 양을 더한다)."""
    if not res or not res.get("devices"):
        return False, None, 0
    worst, n = None, 0
    if rails is not None:
        for v in (res.get("nodes") or {}).values():
            if v is None:
                continue
            over = max(rails[0] - rails[2] - v, v - rails[1] - rails[2])
            if over > 0:
                worst = over if worst is None else max(worst, over)
    for nm, dv in res["devices"].items():
        idv, vds, vdsat = dv.get("id"), dv.get("vds"), dv.get("vdsat")
        if idv is None or vds is None or vdsat is None:
            return False, None, 0                       # 값을 못 읽으면 통과로 세지 않는다
        if abs(idv) <= (off_i or 0.0):
            continue
        n += 1
        short = vdsat + margin - vds
        worst = short if worst is None else max(worst, short)
    return (worst is not None and n > 0 and worst <= 0), worst, n


def _window(sw, make_point, measure, lo, hi, p0, step, margin, off_i, res_target, label, rails=None):
    """공칭 p0 에서 포화 조건이 이어지는 연속 구간의 경계를 구한다. make_point(p) -> 소스 DC 사전, measure(res, p) -> 측정 좌표값.
    반환 {status, lo, hi, p_lo, p_hi, nominal_ok, shortage, n_points, runs} (lo/hi = 측정 좌표, 레일에 닿으면 그 값)."""
    n = max(2, math.ceil((hi - lo) / step))
    grid = sorted({lo + (hi - lo) * i / n for i in range(n + 1)} | {p0})
    res = sw.run([make_point(p) for p in grid], label)
    if res is None:
        return {"status": "failed", "reason": "ngspice 시간 상한"}
    ok = []
    for p, r in zip(grid, res):
        s, w, nc = sat_violation(r, margin, off_i, rails)
        ok.append((p, s, w, measure(r, p) if r else None))
    i0 = grid.index(p0)
    out = {"status": "ok", "n_points": len(grid), "nominal_ok": ok[i0][1],
           "shortage": None if ok[i0][2] is None else max(0.0, ok[i0][2])}
    if not ok[i0][1]:
        out.update(lo=None, hi=None, worst_at_nominal=ok[i0][2])
        return out

    def edge(direction):
        # direction -1: 아래쪽, +1: 위쪽. 마지막 통과 인덱스 j, 첫 실패 인덱스 j+direction (격자 끝이면 없음)
        j = i0
        while 0 <= j + direction < len(ok) and ok[j + direction][1]:
            j += direction
        k = j + direction
        if not (0 <= k < len(ok)):
            return ok[j][3], None            # 레일 끝까지 통과
        a, b = ok[j][0], ok[k][0]            # 통과 a, 실패 b (명령 좌표)
        last_ok = ok[j][3]
        for _ in range(ZOOM_ROUNDS):
            if abs(b - a) <= res_target:
                break
            sub = [a + (b - a) * t / (ZOOM_POINTS + 1) for t in range(1, ZOOM_POINTS + 1)]
            rs = sw.run([make_point(p) for p in sub], label + "z")
            if rs is None:
                break
            na, nb = a, b
            for p, r in zip(sub, rs):
                s, _, _ = sat_violation(r, margin, off_i, rails)
                if s:
                    na, last_ok = p, measure(r, p)
                else:
                    nb = p
                    break
            a, b = na, nb
        return last_ok, b
    lo_m, lo_fail = edge(-1)
    hi_m, hi_fail = edge(+1)
    out.update(lo=lo_m, hi=hi_m, lo_hit_rail=lo_fail is None, hi_hit_rail=hi_fail is None, runs=sw.n_runs)
    return out


def swing_icmr_measure(inp, cir_path, meta, exe, timeout_s=None, cache_dir=None, sat_margin=None, off_current=None):
    """sim.swing_icmr = {swing_out_v, icmr_v, icm_margin_v, 각 창 기록} (입력 `swing_icmr` 블록이 있을 때, 모듈 머리말)."""
    cfg = inp.get("swing_icmr")
    if not cfg:
        return None
    res = {"status": "unavailable", "margin_V": 0.0 if sat_margin is None else sat_margin, "reason": None,
           "swing": None, "icmr": None, "swing_out_v": None, "icmr_v": None, "icm_margin_v": None}
    if meta.get("blockers"):
        res["reason"] = "넷리스트 막힘: " + " | ".join(meta["blockers"])
        return res
    margin = res["margin_V"]
    tb = inp["testbench"]
    reltol = reltol_of(tb.get("options"))
    rail_lo, rail_hi = _rails(inp)
    span = rail_hi - rail_lo
    step = thermal_voltage((meta.get("lut_meta") or {}).get("temp_c") or 27.0)
    res_target = reltol * span
    rails = (rail_lo, rail_hi, reltol * span)
    sw = _Sweeper(cir_path, meta, inp, exe, timeout_s, cache_dir, "swp")
    pred = (inp.get("predictions") or {}).get("nodes") or {}
    ports = inp["ports"]
    in_nets = [ports[k] for k in ("input_p", "input_n", "input") if ports.get(k)]
    base = sw.base
    ofs = {n: "Vofs_" + n for n in in_nets if ("Vofs_" + n) in base}
    dcs = {n: "Vdc_" + n for n in in_nets if ("Vdc_" + n) in base}

    # ---- ICMR
    if cfg.get("icmr"):
        def mk_icm(delta):
            pt = {}
            for n, s in ofs.items():
                pt[s] = base[s] - delta
            for n, s in dcs.items():
                pt[s] = base[s] + delta
            return pt
        v_in = [pred[n] for n in in_nets if n in pred]
        vcm = sum(v_in) / len(v_in) if v_in else None
        if vcm is None:
            res["icmr"] = {"status": "unavailable", "reason": "입력 넷의 예측 DC 가 없다"}
        else:
            w = _window(sw, mk_icm, lambda r, p: vcm + p, rail_lo - vcm, rail_hi - vcm, 0.0, step, margin, off_current, res_target, "icm", rails)
            w["v_cm_nominal"] = vcm
            if w.get("status") == "ok" and w.get("lo") is not None:
                lo, hi = max(w["lo"], rail_lo), min(w["hi"], rail_hi)
                w.update(v_in_min=lo, v_in_max=hi, width_v=hi - lo)
                res["icmr_v"] = hi - lo
                vdec = cfg.get("input_dc_V", vcm)
                if cfg.get("input_dc_pending"):
                    res["icm_margin_v"] = None
                    w["icm_margin_reason"] = "input_dc_pending"
                else:
                    res["icm_margin_v"] = min(vdec - lo, hi - vdec)
            elif w.get("status") == "ok":
                res["icmr_v"] = -(w.get("worst_at_nominal") or 0.0)
                w["note"] = "공칭 입력 CM 에서 이미 포화 조건 위반 -- 음수 = 최대 부족량(창이 비어 있다)"
            res["icmr"] = w

    # ---- 출력 스윙
    if cfg.get("swing"):
        se_out, dp, dn = ports.get("output"), ports.get("output_p"), ports.get("output_n")
        k_fb = tb["ac"].get("diff_feedback_gain")
        if se_out and ofs:
            fbn = next(iter(ofs))                      # se 출력은 입력 한 넷(inp_n)에 servo
            vo = pred.get(se_out)
            if vo is None:
                res["swing"] = {"status": "unavailable", "reason": "출력 예측 DC 가 없다"}
            else:
                def mk_se(vt):
                    return {ofs[fbn]: base[ofs[fbn]] + (vt - vo)}
                w = _window(sw, mk_se, lambda r, p: (r.get("nodes") or {}).get(se_out) if r else None, rail_lo, rail_hi, vo, step,
                            margin, off_current, res_target, "sw", rails)
                w["v_out_nominal"] = vo
                if w.get("status") == "ok" and w.get("lo") is not None and w.get("hi") is not None:
                    res["swing_out_v"] = 2 * min(w["hi"] - vo, vo - w["lo"])
                    w.update(v_lo=w["lo"], v_hi=w["hi"])
                elif w.get("status") == "ok":
                    res["swing_out_v"] = -(w.get("worst_at_nominal") or 0.0)
                    w["note"] = "공칭 출력 DC 에서 이미 포화 조건 위반 -- 음수 = 최대 부족량"
                res["swing"] = w
        elif dp and dn and len(ofs) == 2 and k_fb:
            fp, fn = ofs.get(ports["input_p"]), ofs.get(ports["input_n"])
            if not (fp and fn):
                res["swing"] = {"status": "unavailable", "reason": "차동 입력 두 넷 모두 servo 기준원이 있어야 한다"}
            else:
                def mk_d(dv):
                    return {fp: base[fp] - k_fb * dv, fn: base[fn] + k_fb * dv}
                def meas(r, p):
                    nd = (r or {}).get("nodes") or {}
                    return None if dp not in nd or dn not in nd or nd[dp] is None or nd[dn] is None else nd[dp] - nd[dn]
                w = _window(sw, mk_d, meas, -span, span, 0.0, step, margin, off_current, res_target, "sw", rails)
                if w.get("status") == "ok" and w.get("lo") is not None and w.get("hi") is not None:
                    res["swing_out_v"] = 2 * min(w["hi"], -w["lo"])
                    w.update(d_lo=w["lo"], d_hi=w["hi"])
                elif w.get("status") == "ok":
                    res["swing_out_v"] = -(w.get("worst_at_nominal") or 0.0)
                    w["note"] = "공칭 출력에서 이미 포화 조건 위반 -- 음수 = 최대 부족량"
                res["swing"] = w
        else:
            res["swing"] = {"status": "unavailable",
                            "reason": "출력 DC 를 움직일 servo(입력 쪽 되먹임 기준원)가 없는 free 넷리스트다"}
    st = [x.get("status") for x in (res["swing"], res["icmr"]) if x]
    res["status"] = "ok" if st and all(s == "ok" for s in st) else ("partial" if "ok" in st else "unavailable")
    res["reason"] = None if res["status"] == "ok" else "; ".join(x.get("reason") or "" for x in (res["swing"], res["icmr"]) if x and x.get("reason"))
    res["ngspice_runs"] = sw.n_runs
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="스윙·ICMR ngspice 스윕")
    ap.add_argument("oracle_input")
    ap.add_argument("netlist")
    ap.add_argument("out_json")
    ap.add_argument("--ngspice", required=True)
    ap.add_argument("--timeout-s", type=float, default=None)
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--sat-margin-v", type=float, default=None)
    a = ap.parse_args(argv)
    with open(a.oracle_input, encoding="utf-8") as f:
        inp = json.load(f)
    with open(a.netlist + ".meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    margin = a.sat_margin_v if a.sat_margin_v is not None else (inp.get("judge") or {}).get("sat_margin_V")
    res = swing_icmr_measure(inp, a.netlist, meta, a.ngspice, a.timeout_s, a.cache_dir, margin,
                             (inp.get("judge") or {}).get("off_current_A"))
    with open(a.out_json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", a.out_json, "swing_out_v=", (res or {}).get("swing_out_v"), "icmr_v=", (res or {}).get("icmr_v"))
    return 0 if (res or {}).get("status") == "ok" else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
