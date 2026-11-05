"""U6 test 공용 toy: 이상 꼬리 전류원 5T OTA(이름 없는 손 회로) -- offset Monte-Carlo·스윙·ICMR test 가 같이 쓴다.

회로(손으로 정함): NMOS 입력쌍 M1(gate inp, drain d1)·M2(gate inn, drain out), 공통 소스 tail, 이상 전류원 IT(tail -> gnd, 20 µA),
PMOS 미러 부하 M3(diode, d1)·M4(drain out), 부하 C CL(out). 크기 L = 1 µm, finger_w = 2 µm, finger 2 개(전 소자). VDD 1.8 V, 입력 DC 0.9 V.
단일 출력·차동 입력이라 오라클 free 넷리스트는 out -> inn 단위 되먹임 servo(README C5)를 건다.

독립 기준(oracle (c), 이 파일이 손으로 쓴 ngspice 넷리스트 -- 오라클 소스·출력과 무관):
  * 동작점: inn 을 고이득 VCVS servo(Esv, 이득 1e6)로 움직여 out 을 목표 전압에 묶는다(오라클의 단위 되먹임과 다른 구조).
  * mismatch 1σ 결정적 섭동: PDK 카드의 p = p0 + <var>_slope_spectre·(slope/sqrt(l·w·mult)) 에서 subckt 인자 `mult` 를 이용해
    섭동할 소자만 mult = 1, 나머지는 mult = 1e40(기여 0)으로 두고 전역 slope_spectre 를 1e-6/sqrt(n_fingers) 로 놓는다 --
    finger 인스턴스마다 l·w 가 SI 숫자(µm 숫자의 1e-12 배)라 그 소자 Δp = slope/sqrt(L_µm·finger_µm·n_fingers)
    (설계 41 §6.4-2 A_eff 의 면적 법칙 = README offset MC '단위'). 오라클의 '소자별 래퍼 subckt 지역 .param' 과 다른 방법.
  * 스윙·ICMR: 같은 servo 넷리스트의 `.dc` 스윕(출력 목표 / 입력 공통모드)에서 모든 MOS 의 vds − vdsat − 여유와 회로 노드의 레일
    여유(± reltol·레일 폭)를 표본마다 계산해, 공칭점을 포함하는 연속 구간의 끝을 선형 보간으로 찾는다(README 스윙·ICMR 의 포화 조건
    문안을 독립 구현; 오라클의 거친 격자 + 7 점 확대와 다른 방법).
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np

import conftest
from conftest import NFET, PFET, make_lut, zero_diffusion
from independent_ref import _includes             # 같은 폴더로 옮긴 손 넷리스트 독립 기준(card 20261104-op23, D §18.2)

T5 = dict(vdd=1.8, vin=0.9, it=20e-6, L=1e-6, fw=2e-6, n=2, cl=1e-12)
DEV = {"M1": ("nmos", "d1", "inp", "tail", "gnd"), "M2": ("nmos", "out", "inn", "tail", "gnd"),
       "M3": ("pmos", "d1", "d1", "vdd", "vdd"), "M4": ("pmos", "out", "d1", "vdd", "vdd")}
NODES = ("inp", "inn", "out", "d1", "tail")
RELTOL = 1e-4                                       # conftest.testbench_block options.reltol
VARS = {"nmos": ("toxe", "vth0", "voff"), "pmos": ("toxe", "vth0", "voff", "nfactor")}   # PDK *__mismatch.corner.spice 의 *_slope_spectre


def _n(node):
    return "0" if node == "gnd" else node


def body(vref, vinp=None, mult_param=False):
    """servo 넷리스트 본문: out 은 Vref 로, inp 는 Vinp(기본 입력 DC)로."""
    c = T5
    b = [f"Vdd vdd 0 DC {c['vdd']}", f"Vinp inp 0 DC {c['vin'] if vinp is None else vinp}", f"IT tail 0 DC {c['it']}",
         f"CL out 0 {c['cl']}", "Esv inn 0 vref out 1e6", f"Vref vref 0 DC {vref}"]
    for nm, (k, d, g, s, bb) in DEV.items():
        sub = NFET if k == "nmos" else PFET
        mult = f" mult={{m_{nm}}}" if mult_param else ""
        b += [f"X{nm}_{i} {_n(d)} {_n(g)} {_n(s)} {_n(bb)} {sub} l={c['L']} w={c['fw']}{mult}" for i in range(c["n"])]
        if mult_param:
            b.append(f".param m_{nm} = 1e40")
    return b


def _head():
    return ["* u6 toy 5T", _includes("tt"), ".temp 27.0", ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7"]


def _run(lines, wd: Path, name):
    import subprocess
    wd.mkdir(parents=True, exist_ok=True)
    (wd / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    p = subprocess.run([str(conftest.NGSPICE), "-b", name], capture_output=True, text=True, cwd=str(wd),
                       encoding="utf-8", errors="replace", timeout=600)
    return p


def _parse_tagged(stdout):
    cur, vals = None, {}
    for ln in stdout.splitlines():
        if ln.startswith("TAG "):
            cur = ln.split(None, 1)[1].strip()
        m = re.match(r"\s*v\((\w+)\)\s*=\s*([-+0-9.eE]+)", ln)
        if m and cur is not None:
            vals.setdefault(cur, {})[m.group(1).lower()] = float(m.group(2))
    return vals


def nominal_op(wd: Path, vout_target=None):
    """독립 동작점: out 을 목표(없으면 입력 DC 와 같은 전압)로 묶은 해의 노드 전압."""
    vref = T5["vin"] if vout_target is None else vout_target
    ctrl = [".control", "set noaskquit", "op", "echo TAG nominal", "print " + " ".join(f"v({x})" for x in NODES),
            "quit", ".endc", ".end"]
    p = _run(_head() + body(vref) + ctrl, wd, "op.cir")
    v = _parse_tagged(p.stdout).get("nominal")
    assert v and set(NODES) <= set(v), (p.stdout + p.stderr)[-1500:]
    return v


def mismatch_sensitivities(wd: Path, vout):
    """소자 k·변수 v 마다 1σ 결정적 섭동의 입력 환산 offset 변화 ΔV_os = −Δ(V_inp − V_inn) [V](servo 가 out 을 고정)."""
    c = T5
    ctrl = [".control", "set noaskquit", "op", "echo TAG base", "print v(inn)"]
    keys = []
    for nm, (k, *_r) in DEV.items():
        sub = NFET if k == "nmos" else PFET
        for v in VARS[k]:
            tag = f"{nm}:{v}"
            keys.append(tag)
            ctrl += [f"alterparam m_{nm} = 1", f"alterparam {sub}__{v}_slope_spectre = {1e-6 / math.sqrt(c['n'])}",
                     "reset", "op", f"echo TAG {tag}", "print v(inn)", f"alterparam m_{nm} = 1e40",
                     f"alterparam {sub}__{v}_slope_spectre = 0", "reset"]
    ctrl += ["quit", ".endc", ".end"]
    p = _run(_head() + body(vout, mult_param=True) + ctrl, wd, "mm.cir")
    vals = _parse_tagged(p.stdout)
    assert "base" in vals and all(k in vals for k in keys), (p.stdout + p.stderr)[-2000:]
    base = vals["base"]["inn"]
    return {k: vals[k]["inn"] - base for k in keys}


def _probe(nm, q):
    k = DEV[nm][0]
    return f"@m.x{nm.lower()}_0.m{NFET if k == 'nmos' else PFET}[{q}]"


def dc_window(wd: Path, which, nominal, lo, hi, step, margin, vout=None):
    """독립 .dc 스윕 창. which = 'swing'(Vref 스윕, inp = 입력 DC) | 'icmr'(Vinp 스윕, out = vout 고정).
    표본마다 slack = min(모든 MOS vds − vdsat − margin, 노드 − (0 − tol), (VDD + tol) − 노드), tol = reltol·레일 폭.
    공칭점을 포함하는 slack >= 0 연속 구간의 양 끝(선형 보간)과 그 변수(스윕 변수, 및 icmr 이면 공통모드 (inp+inn)/2)를 돌려준다."""
    c = T5
    src = "Vref" if which == "swing" else "Vinp"
    vref = nominal if which == "swing" else vout
    probes = [_probe(nm, q) for nm in DEV for q in ("vds", "vdsat")]
    ctrl = [".control", "set noaskquit", "save " + " ".join([f"v({x})" for x in NODES] + probes),
            f"dc {src} {lo} {hi} {step}", "set wr_singlescale", "set numdgt=12",
            "wrdata dc.txt " + " ".join([f"v({x})" for x in NODES] + probes), "quit", ".endc", ".end"]
    p = _run(_head() + body(vref) + ctrl, wd, f"{which}.cir")
    a = np.loadtxt(wd / "dc.txt")
    x = a[:, 0]
    nodes = a[:, 1:1 + len(NODES)]
    pr = a[:, 1 + len(NODES):]
    tol = RELTOL * (c["vdd"] - 0.0)
    sat = np.min(pr[:, 0::2] - pr[:, 1::2] - margin, axis=1)          # vds − vdsat − margin, 소자별 최솟값
    rail = np.min(np.minimum(nodes + tol, (c["vdd"] + tol) - nodes), axis=1)
    slack = np.minimum(sat, rail)
    i0 = int(np.argmin(np.abs(x - nominal)))
    assert slack[i0] > 0, ("공칭점이 이미 창 밖", x[i0], slack[i0])
    i = i0
    while i > 0 and slack[i - 1] >= 0:
        i -= 1
    j = i0
    while j < len(x) - 1 and slack[j + 1] >= 0:
        j += 1
    assert 0 < i and j < len(x) - 1, ("스윕 범위가 창 끝을 덮지 못함", x[0], x[-1], (p.stdout + p.stderr)[-800:])

    def edge(k_in, k_out):
        t = slack[k_in] / (slack[k_in] - slack[k_out])
        return k_in, k_out, t

    out = {}
    sat_each = pr[:, 0::2] - pr[:, 1::2] - margin                    # 소자별 포화 여유(열 순서 = DEV)
    rail_each = np.minimum(nodes + tol, (c["vdd"] + tol) - nodes)    # 노드별 레일 여유(열 순서 = NODES)
    for name, (k_in, k_out, t) in (("lo", edge(i, i - 1)), ("hi", edge(j, j + 1))):
        xv = x[k_in] + t * (x[k_out] - x[k_in])
        cm = 0.5 * (nodes[:, 0] + nodes[:, 1])
        out[name] = xv
        out[name + "_cm"] = cm[k_in] + t * (cm[k_out] - cm[k_in])
        lerp = lambda col: float(col[k_in] + t * (col[k_out] - col[k_in]))
        out[name + "_slack"] = {**{nm: lerp(sat_each[:, q]) for q, nm in enumerate(DEV)},
                                **{f"rail:{nd}": lerp(rail_each[:, q]) for q, nd in enumerate(NODES)}}
    out["nominal_cm"] = float(0.5 * (nodes[i0, 0] + nodes[i0, 1]))
    return out


def toy_input(lut_dir: Path, nominal_v: dict, **blocks):
    """오라클 입력(예측 = 독립 동작점, 확산 면적 0 명시, 꺼짐 문턱 0)."""
    c = T5

    def dev(nm):
        k, d, g, s, b = DEV[nm]
        return {"name": nm, "kind": k, "drain": d, "gate": g, "source": s, "bulk": b, "L": c["L"], "finger_w": c["fw"],
                "n_fingers": c["n"], "W": c["fw"] * c["n"]}

    inp = {"schema": "spice_oracle_input/1", "circuit": "t5ota",
           "process": conftest.process_block(make_lut(lut_dir / "lut.npz")),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": [dev(nm) for nm in DEV],
           "sources": [{"name": "IT", "kind": "current", "terminals": ["tail", "gnd"], "value": c["it"],
                        "value_basis": "test toy"}],
           "passives": [{"name": "CL", "kind": "capacitor", "terminals": ["out", "gnd"], "value": c["cl"]}],
           "ports": {"input_p": "inp", "input_n": "inn", "output": "out"},
           "predictions": {"nodes": {k: nominal_v[k] for k in NODES},
                           "devices": {nm: {"off_current_A": 0.0} for nm in DEV}, "metrics": []},
           "testbench": conftest.testbench_block()}
    inp.update(blocks)
    return zero_diffusion(inp)
