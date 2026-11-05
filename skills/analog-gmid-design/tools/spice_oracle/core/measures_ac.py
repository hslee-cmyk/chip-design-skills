# -*- coding: utf-8 -*-
"""core/measures_ac.py -- AC 소신호 측정 수학과 결과 조립 (design §3.1, card 20261104-op23).

옛 `oracle_simulate.py` 의 ac_measures·pm_crosscheck·loop_gain·ratio/rout·loop_choke_ratio 수학을 이름 그대로 옮긴 것이다.
파일 대신 어댑터가 낸 `FreqSeries`(주파수 + 복소 열)를 입력으로 받는다. 시뮬레이터 이름·방언을 모른다.

기간 동작(D-1, 채택 A-80): P = 0 증명(개루프 RHP 극 수) 없이는 PM 이 안정 여유인지 정할 수 없다(C10). 안정성 검사는 OP-4 몫이라 이 기간에는
PM 값이 있으면 `ac.pm_undefined = "stability_unverified"`, `ac.pm_deg = None`, 원값은 `ac.pm_deg_raw`에 둔다(판정 PASS 불가).
"""
from __future__ import annotations

import math

import numpy as np

from core.requests import expr_key

STABILITY_UNVERIFIED = "stability_unverified"
LOOP_PROBE_SINGULAR = "loop_probe_singular"
ROUT_NEGATIVE = "negative_real_part"
PM_PERIOD_REASON = ("P = 0(개루프 RHP 극 없음) 증명이 없어 PM 이 안정 여유인지 정할 수 없다 -- 안정성 검사(Nyquist 감은 수, 개루프 극점, "
                    "폐루프 과도)는 OP-4 에서 오고 그 전에는 PM 을 값으로 두지 않는다(원값은 pm_deg_raw)")


# ---------------------------------------------------------------- 수학
def ac_measures(freq, re_, im, ref="first"):
    """기준점(DC 대용) = 첫 주파수 점. ref='peak' 이면 |H| 최대 점(진단용)."""
    f = np.asarray(freq)
    H = np.asarray(re_) + 1j * np.asarray(im)
    mag = np.abs(H)
    ph = np.unwrap(np.angle(H))
    k0 = int(np.argmax(mag)) if ref == "peak" else 0
    out = {"f_first_hz": float(f[k0]), "gain_dc": float(mag[k0]), "dc_gain_db": float(20 * np.log10(mag[k0])),
           "phase_dc_deg": float(np.degrees(ph[k0])), "reference_point": ref}
    i3 = np.where(mag[k0:] < mag[k0] / math.sqrt(2))[0]
    out["f3db_hz"] = float(f[k0 + i3[0]]) if len(i3) else None
    iu = np.where(mag[k0:] < 1.0)[0]
    if len(iu) and iu[0] > 0:
        k = k0 + iu[0]
        lf = np.interp(0.0, [np.log10(mag[k]), np.log10(mag[k - 1])], [np.log10(f[k]), np.log10(f[k - 1])])
        phu = np.interp(lf, [np.log10(f[k - 1]), np.log10(f[k])], [ph[k - 1], ph[k]])
        lag = math.degrees(ph[k0] - phu)
        out["ugf_hz"] = float(10 ** lf)
        out["phase_lag_at_ugf_deg"] = float(lag)
        out["pm_deg"] = float(180.0 - lag)
    else:
        out["ugf_hz"] = None
        out["phase_lag_at_ugf_deg"] = None
        out["pm_deg"] = None
    out["a0_f3db_hz"] = out["gain_dc"] * out["f3db_hz"] if out["f3db_hz"] else None
    return out


def mp_resolution(rel_resolution, values_per_sample):
    """Mp = |C(f_k)|/|C(f_0)| 의 분해능: (모은 값 개수 2*values_per_sample) * 상대 반올림 오차 한계."""
    return None if rel_resolution is None else 2 * values_per_sample * rel_resolution


def pm_crosscheck(freq, re_, im, mp_res=None):
    """PM 교차 측정(기록만): 폐루프 C = L/(1+L) 의 peaking Mp 를 2차계 관계로 PM 에 역산한다."""
    L = np.asarray(re_) + 1j * np.asarray(im)
    C = np.abs(L / (1.0 + L))
    k = int(np.argmax(C))
    mp = float(C[k] / C[0]) if C[0] > 0 else None
    tol = mp_res or 0.0

    def pm_of(z):
        return math.degrees(math.atan2(2 * z, math.sqrt(math.sqrt(1 + 4 * z ** 4) - 2 * z ** 2)))
    out = {"closed_loop_peaking_db": None if not mp else 20 * math.log10(mp),
           "closed_loop_peak_hz": float(freq[k]), "pm_crosscheck_deg": None,
           "pm_crosscheck_method": "closed_loop_peaking_2nd_order", "pm_crosscheck_mp_resolution": mp_res}
    if mp is None:
        out["pm_crosscheck_note"] = "폐루프 첫 점 크기 0 -- 계산 불가"
    elif k == 0 or mp <= 1.0 + tol:
        out["closed_loop_peaking_db"] = None
        out["closed_loop_peak_hz"] = None
        out["pm_crosscheck_note"] = (f"peaking 없음(Mp-1 = {mp - 1:.3g}, 데이터 분해능 {tol:.3g} 이하) -- "
                                     f"2차 근사로 PM >= {pm_of(1 / math.sqrt(2)):.4g} deg")
    else:
        z = math.sqrt((1 - math.sqrt(1 - 1 / mp ** 2)) / 2)
        out["pm_crosscheck_deg"] = pm_of(z)
        out["pm_crosscheck_note"] = None
    return out


def _loop_sums(v, i, weights, nets):
    """끊은 넷 k 마다 x=되먹임 쪽(lbx), y=증폭기 쪽. v: FreqSeries(열 v(lbx_k), v(k)), i: FreqSeries(열 i(Vlb_k), v(k)) -> (vx, vy, ix, iy)."""
    vx = sum(w * v.values[f"v(lbx_{n})"] for n, w in zip(nets, weights))
    vy = sum(w * v.values[f"v({n})"] for n, w in zip(nets, weights))
    ix = sum(w * i.values[f"i(tb:lb:{n})"] for n, w in zip(nets, weights))
    iy = sum(w * (w - i.values[f"i(tb:lb:{n})"]) for n, w in zip(nets, weights))
    return vx, vy, ix, iy


def _shape_ok(v, i):
    return v is not None and i is not None and len(v.f) == len(i.f)


def loop_probe_singular(v, i, weights, nets):
    """Middlebrook 분모가 정확히 0 인 표본 목록 [{f_hz, which}] (which = vy | iy | tv+ti+2). 열이 없으면 []."""
    if not _shape_ok(v, i):
        return []
    vx, vy, ix, iy = _loop_sums(v, i, weights, nets)
    out = []
    for k in range(len(v.f)):
        f = float(v.f[k])
        if vy[k] == 0:
            out.append({"f_hz": f, "which": "vy"})
        elif iy[k] == 0:
            out.append({"f_hz": f, "which": "iy"})
        elif (-vx[k] / vy[k]) + (ix[k] / iy[k]) + 2 == 0:
            out.append({"f_hz": f, "which": "tv+ti+2"})
    return out


def loop_gain(v, i, weights, nets):
    """Middlebrook 이중 주입 루프 이득: Tv = -sum(w*vx)/sum(w*vy), Ti = sum(w*ix)/sum(w*(w - ix)), T = (Tv*Ti - 1)/(Tv + Ti + 2).
    반환 (주파수, T 실수부, T 허수부) 또는 None(분모 0 표본이 있거나 열이 없음 -- 정의 불가)."""
    if not _shape_ok(v, i) or loop_probe_singular(v, i, weights, nets):
        return None
    vx, vy, ix, iy = _loop_sums(v, i, weights, nets)
    tv, ti = -vx / vy, ix / iy
    t = (tv * ti - 1) / (tv + ti + 2)
    return [float(x) for x in v.f], [float(x) for x in t.real], [float(x) for x in t.imag]


def ratio_measure(run, num, den):
    """C24: ratio_db 뷰 한 개의 두 .ac 한 점 결과(FreqSeries) -> {view, f_hz, num, den, ratio_db}. 값이 없거나 |H_den| = 0 이면 ratio_db None."""
    out = {"view": run["view"], "f_hz": run["f_hz"], "num": None, "den": None, "ratio_db": None}
    for side, fs in (("num", num), ("den", den)):
        if fs is not None and len(fs.f):
            h = next(iter(fs.values.values()))[0]
            out[side] = {"re": float(h.real), "im": float(h.imag), "mag": float(abs(h)), "f_hz": float(fs.f[0])}
    if out["num"] and out["den"] and out["den"]["mag"] > 0 and out["num"]["mag"] > 0:
        out["ratio_db"] = 20 * math.log10(out["num"]["mag"] / out["den"]["mag"])
    return out


def rout_measure(run, fs):
    """C26: rout_ohm 뷰 한 개의 .ac 한 점(감지 노드 단위 AC 전류) -> {view, f_hz, re, im, mag, rout_ohm, undefined}. rout_ohm = Re(H);
    Re(H) < 0 이면 None + undefined = 'negative_real_part', 값이 없으면 None + 'no_data'."""
    out = {"view": run["view"], "f_hz": run["f_hz"], "re": None, "im": None, "mag": None, "rout_ohm": None, "undefined": None}
    if fs is None or not len(fs.f):
        out["undefined"] = "no_data"
        return out
    h = next(iter(fs.values.values()))[0]
    out.update(re=float(h.real), im=float(h.imag), mag=float(abs(h)), f_hz=float(fs.f[0]))
    if h.real < 0:
        out["undefined"] = ROUT_NEGATIVE
    else:
        out["rout_ohm"] = float(h.real)
    return out


def loop_choke_ratio(i, break_nets, weights, choke_H):
    """C27 기록(판정 아님): β 루프 2회(전류 주입) 첫 점에서 끊은 넷마다 |jω·L_choke| / |V(n_k)/w_k|. 없으면 None."""
    if i is None or choke_H is None or not len(i.f):
        return None
    f0 = float(i.f[0])
    out = []
    for k, net in enumerate(break_nets):
        w = weights[k]
        z = None if not w else float(abs(i.values[f"v({net})"][0] / w))
        zl = 2 * math.pi * f0 * float(choke_H)
        out.append({"net": net, "f_hz": f0, "choke_H": float(choke_H), "node_impedance_ohm": z,
                    "ratio": None if not z else zl / z})
    return out


# ---------------------------------------------------------------- 기간 동작 (D-1): 안정성 미검증
def apply_stability_period(ac):
    """PM 값이 있으면 정의 불가(stability_unverified)로 바꾸고 원값을 남긴다. 교차 측정도 PM 이 아니므로 같이 비운다."""
    ac["pm_undefined"] = None
    ac["pm_deg_raw"] = ac.get("pm_deg")
    if ac.get("pm_deg") is None:
        ac["stability"] = {"pm_valid": None, "pm_undefined": None,
                           "reason": "PM 값 없음(|L|=1 하강 교차 없음 또는 루프 측정 없음) -- 검사 대상 아님"}
        return
    ac["stability"] = {"pm_valid": None, "pm_undefined": STABILITY_UNVERIFIED, "reason": PM_PERIOD_REASON}
    ac["pm_undefined"] = STABILITY_UNVERIFIED
    ac["pm_deg"] = None
    if ac.get("pm_definition") == "beta_1":
        ac["pm_open_loop_deg"] = None
    ac["pm_crosscheck_deg_raw"] = ac.get("pm_crosscheck_deg")
    ac["pm_crosscheck_deg"] = None
    ac["pm_crosscheck_gap_deg"] = None
    ac["pm_crosscheck_note"] = (f"정의 불가({STABILITY_UNVERIFIED}) -- P = 0 증명 없이는 peaking 역산이 위상여유가 아니다"
                                f"(원값 {ac['pm_crosscheck_deg_raw']})")


# ---------------------------------------------------------------- 결과 조립
def _plain(v):
    """결과 값을 JSON 으로 쓸 수 있는 수로: numpy 스칼라 -> Python, 허수부가 0 인 복소수 -> 실수. 허수부가 있으면 거부(fail-closed)."""
    if v is None or isinstance(v, (str, bool)):
        return v
    if isinstance(v, (complex, np.complexfloating)):
        if v.imag != 0:
            raise ValueError(f"DC 동작점 값에 허수부가 있다: {v!r}")
        return float(v.real)
    if isinstance(v, np.generic):
        return v.item()
    return v


def _status(st):
    if st is None:
        return None
    return {"rc": st.rc, "timed_out": st.timed_out, "error": st.error, "warnings": list(st.warnings),
            "log_excerpt": list(st.log_excerpt), "log_path": st.log_path}


def _series(bundle, rid):
    if bundle is None:
        return None
    r = bundle.by_request.get(rid)
    return r if r is not None and getattr(r, "error", None) is None else None


def _ac_columns(fs, key):
    h = np.asarray(fs.values[key])
    return fs.f, h.real, h.imag


def _loop_block(bundle, tag, nets, weights, choke_H):
    """β/CM 루프 한 벤치 -> (block, T 데이터 | None, 특이 목록)."""
    v, i = _series(bundle, f"{tag}.v"), _series(bundle, f"{tag}.i")
    sing = loop_probe_singular(v, i, weights, nets)
    t = None if sing else loop_gain(v, i, weights, nets)
    block = {"status": _status(bundle.status), "break_nets": list(nets),
             "log_errors": list(bundle.status.log_excerpt)[:40], "measures": ac_measures(*t) if t else None}
    if tag == "loop":
        dr = [x.resolution.data_rel for x in (v, i) if x is not None and x.resolution is not None]
        lres = mp_resolution(None if len(dr) < 2 or any(d is None for d in dr) else max(dr), 6 * len(weights))
        block["pm_crosscheck"] = pm_crosscheck(*t, mp_res=lres) if t else None
        block["choke_ratio"] = loop_choke_ratio(i, nets, weights, choke_H)
    if sing:
        block["singular"] = {"count": len(sing), "first": sing[0], "points": sing[:20]}
    return block, t, sing


def build_sim(circuit, main, loop=None, cm=None, loop_circuit=None, cm_circuit=None):
    """어댑터 결과(ResultBundle)를 옛 sim 결과 모양(oracle_compare 가 읽는 칸)으로 조립한다. 칸 이름에 시뮬레이터 이름이 없다."""
    m = circuit.meta
    op = _series(main, "op")
    res = {"status": _status(main.status), "method": main.method,
           "cache": {"main": main.status.cache_state, "loop": None if loop is None else loop.status.cache_state},
           "log_errors": list(main.status.log_excerpt)[:40]}
    res["devices"] = {k: {q: _plain(x) for q, x in v.items()} for k, v in (op.devices if op else {}).items()}
    res["nodes"] = {n: (_plain(op.nodes.get(n)) if op else None) for n in m["nets"]}
    cur = op.currents if op else {}
    res["rail_current_A"] = {n: (None if cur.get(s) is None else -_plain(cur[s])) for n, s in m["rail_sources"].items()}
    res["hold_current_A"] = {n: _plain(cur.get(s)) for n, s in m["hold_sources"].items()}
    res["op_ok"] = any(v.get("id") is not None for v in res["devices"].values())
    res["instance_geometry_reported"] = None if op is None else op.instance_geometry_reported
    ac_fs = _series(main, "ac")
    raw = None
    if ac_fs is not None and m["has_ac"]:
        o = m["outputs"]
        from core.requests import DiffV, NodeV
        key = expr_key(NodeV(o[0]) if len(o) == 1 else DiffV(o[0], o[1]))
        raw = _ac_columns(ac_fs, key)
    res["ac"] = ac_measures(*raw) if raw else None
    res["ratio"] = []
    for k, view in enumerate(m["ratio_plan"]):
        run = {"view": view, "f_hz": float(m["f_start"])}
        res["ratio"].append(ratio_measure(run, _series(main, f"ratio{k}.num"), _series(main, f"ratio{k}.den")))
    res["rout"] = []
    for k, view in enumerate(m["rout_plan"]):
        run = {"view": {"sense_p": view["sense_p"], "sense_n": view["sense_n"], "sense_mode": view["sense_mode"]},
               "f_hz": float(m["f_start"])}
        res["rout"].append(rout_measure(run, _series(main, f"rout{k}")))
    res["loop"] = None
    sing_loop = None
    Ldata = raw
    if loop is not None:
        lm = loop_circuit.meta
        res["loop"], t, sing_loop = _loop_block(loop, "loop", lm["break_nets"], lm["loop_weights"], lm["choke_H"])
        Ldata = t
    res["cm_loop"] = None
    if cm is not None:
        cmm = cm_circuit.meta
        blk, t, sing = _loop_block(cm, "cm", cmm["break_nets"], cmm["loop_weights"], None)
        shadow = {"pm_deg": blk["measures"].get("pm_deg") if blk["measures"] else None}
        apply_stability_period(shadow)
        blk.update(pm_deg=shadow["pm_deg"], pm_deg_raw=shadow["pm_deg_raw"], pm_undefined=shadow["pm_undefined"],
                   stability=shadow["stability"], weights=list(cmm["loop_weights"]), cache=cm.status.cache_state)
        if sing:
            blk["pm_undefined"] = LOOP_PROBE_SINGULAR
        res["cm_loop"] = blk
    ac = res["ac"]
    if ac is not None:
        ac["pm_open_loop_deg"] = ac["pm_deg"]
        ac["dc_path_isolation"] = m.get("dc_path_isolation")
        if loop is not None:
            lt = (res["loop"] or {}).get("measures") or {}
            ac["pm_deg"] = lt.get("pm_deg")
            ac["pm_definition"] = "beta_loop"
            ac["loop_ugf_hz"] = lt.get("ugf_hz")
            ac["loop_gain_dc_db"] = lt.get("dc_gain_db")
            ac["loop_break_nets"] = list(loop_circuit.meta["break_nets"])
            ac["loop_weights"] = dict(zip(loop_circuit.meta["break_nets"], loop_circuit.meta["loop_weights"]))
            ac["loop_choke_ratio"] = (res["loop"] or {}).get("choke_ratio")
            xc = (res["loop"] or {}).get("pm_crosscheck") or {}
        else:
            ac["pm_definition"] = "beta_1"
            ac["loop_break_nets"] = []
            ac["loop_weights"] = dict(m.get("input_ac_weights") or {})
            ac["loop_choke_ratio"] = None
            xc = pm_crosscheck(*raw, mp_res=mp_resolution(ac_fs.resolution.data_rel, 2))
        ac.update({k: xc.get(k) for k in ("pm_crosscheck_deg", "pm_crosscheck_note", "pm_crosscheck_method",
                                          "pm_crosscheck_mp_resolution", "closed_loop_peaking_db", "closed_loop_peak_hz")})
        pc, pm = ac.get("pm_crosscheck_deg"), ac.get("pm_deg")
        ac["pm_crosscheck_gap_deg"] = None if pc is None or pm is None else pc - pm
        apply_stability_period(ac)
        sg = (res["loop"] or {}).get("singular")
        if sg:
            ac["pm_undefined"] = LOOP_PROBE_SINGULAR
            ac["stability"]["reason"] = (f"β 루프 T 정의 불가: Middlebrook 분모 0 인 표본 {sg['count']}개(첫 표본 "
                                         f"{sg['first']['f_hz']:.4g} Hz, {sg['first']['which']})")
    return res


