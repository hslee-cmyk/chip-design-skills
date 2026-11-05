"""손 넷리스트 독립 기준(oracle (c) 옛 오라클과도 새 어댑터와도 무관한 손으로 쓴 ngspice 넷리스트) -- 옛 `tests/conftest.py` 에서 옮김.

계획 D §18.2 '`conftest.py`의 `run_spice`·`independent_cs/fb`, `u6_toy5t.py`(손 넷리스트 독립 기준)는 `O/tests/adapters/ngspice/` 아래로
옮겨 그 어댑터의 독립 기준으로 쓴다(삭제하지 않음)'. 어댑터 패키지 `O/adapters/ngspice/` 가 아니라 `O/tests/` 아래에 둔다(어댑터 지문에
들어가면 test 수정이 능력 기록을 무효로 만든다, D §18.2 v0.2.6). 함수 본문은 옮기기 전과 같다(이동만, 약화·변경 없음).
회로 상수 `CS`·`FB` 와 모델 이름은 conftest 가 계속 갖는다.
"""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np

from conftest import CS, FB, NFET, NGSPICE, PDK, PFET


# ---------------------------------------------------------------- 독립 ngspice(손으로 쓴 넷리스트)
def _includes(corner="tt"):
    p = PDK.as_posix()
    return "\n".join(f'.include "{x}"' for x in [
        f"{p}/cells/nfet_01v8/{NFET}__{corner}.pm3.spice", f"{p}/cells/nfet_01v8/{NFET}__mismatch.corner.spice",
        f"{p}/models/parameters/lod.spice", f"{p}/cells/pfet_01v8/{PFET}__{corner}.pm3.spice",
        f"{p}/cells/pfet_01v8/{PFET}__mismatch.corner.spice"])


def run_spice(body: str, workdir: Path, prints=(), ac_out=None, ac=None, corner="tt", temp_c=27.0) -> dict:
    """손으로 쓴 소자 줄 body 를 감싸 ngspice -b 로 돌린다. prints 의 각 식을 print 해 {식: 값},
    ac_out 이면 f, H(복소)도."""
    workdir.mkdir(parents=True, exist_ok=True)
    lines = ["* independent reference", _includes(corner), f".temp {temp_c}",
             ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7", body, ".control", "set noaskquit", "op"]
    lines += [f"print {e}" for e in prints]
    if ac_out:
        f0, f1, ppd = ac
        lines += [f"ac dec {ppd} {f0} {f1}", f"let hr = real(v({ac_out}))", f"let hi = imag(v({ac_out}))",
                  "set wr_singlescale", "wrdata ref_ac.txt hr hi"]
    lines += ["quit", ".endc", ".end"]
    (workdir / "ref.cir").write_text("\n".join(lines) + "\n", encoding="utf-8")
    p = subprocess.run([str(NGSPICE), "-b", "ref.cir"], capture_output=True, text=True, cwd=str(workdir),
                       encoding="utf-8", errors="replace", timeout=120)
    out = {}
    for ln in p.stdout.splitlines():
        if " = " in ln:
            k, v = ln.split(" = ", 1)
            try:
                out[k.strip().lower()] = float(v.split()[0])
            except ValueError:
                pass
    for e in prints:
        assert e.lower() in out, f"독립 ngspice print 실패 {e}\n{p.stdout[-2000:]}\n{p.stderr[-2000:]}"
    res = {"op": out}
    if ac_out:
        a = np.loadtxt(workdir / "ref_ac.txt")
        res["f"] = a[:, 0]
        res["H"] = a[:, 1] + 1j * a[:, 2]
    return res


def probe(kind, inst, param):
    return f"@m.{inst}.m{NFET if kind == 'nmos' else PFET}[{param}]"


PARAMS = ("id", "gm", "gds", "vgs", "vds", "vbs", "vdsat")


@lru_cache(maxsize=16)
def _independent_cs_cached(workdir: str, vout_hold=None, pout_hold=None, corner="tt", temp_c=27.0):
    c = CS
    body = [f"Vdd vdd 0 DC {c['vdd']}", f"Vsp vsp 0 DC {c['vsp']}", f"Vin nin 0 DC {c['vin']} AC 1",
            f"Vpb pb 0 DC {c['pb']}"]
    # finger 규칙의 독립 표현: finger 마다 인스턴스 하나(w=finger_w), m/nf 없이 병렬 n 개.
    for i in range(c["n"]):
        body.append(f"XM1_{i} nout nin 0 0 {NFET} l={c['L']} w={c['finger_w']}")
    for i in range(c["pn"]):
        body.append(f"XMP1_{i} pout pb vsp vdd {PFET} l={c['pL']} w={c['pfinger_w']}")
    if vout_hold is None:
        body += [f"RL vdd nout {c['rload']}", f"CL nout 0 {c['cl']}"]
    else:
        body += [f"Vh nout 0 DC {vout_hold}"]
    if pout_hold is None:
        body += [f"RP pout 0 {c['rp']}"]
    else:
        body += [f"Vhp pout 0 DC {pout_hold}"]
    prints = ["v(nout)", "v(pout)"]
    for i in range(c["n"]):
        prints += [probe("nmos", f"xm1_{i}", q) for q in PARAMS]
    for i in range(c["pn"]):
        prints += [probe("pmos", f"xmp1_{i}", q) for q in PARAMS]
    ac = None if vout_hold is not None else (0.01, 1e10, 40)
    r = run_spice("\n".join(body), Path(workdir), prints, ac_out="nout" if ac else None, ac=ac,
                  corner=corner, temp_c=temp_c)
    op = r["op"]

    def dev(kind, inst, n):
        d = {q: op[probe(kind, f"{inst}_0", q).lower()] for q in PARAMS}
        for q in ("id", "gm", "gds"):  # 병렬 finger 총합
            d[q] = sum(op[probe(kind, f"{inst}_{i}", q).lower()] for i in range(n))
        return d

    return {"V": {"nout": op["v(nout)"], "pout": op["v(pout)"]},
            "M1": dev("nmos", "xm1", c["n"]), "MP1": dev("pmos", "xmp1", c["pn"]),
            "f": r.get("f"), "H": r.get("H")}


def independent_cs(root: Path, vout_hold=None, pout_hold=None, corner="tt", temp_c=27.0):
    """손으로 쓴 독립 넷리스트(finger 마다 인스턴스 1개, m/nf 없음)로 CS 회로를 직접 ngspice 에 돌린 값.
    vout_hold/pout_hold 를 주면 그 넷을 이상 전압원으로 묶는다(forced KCL 손계산용)."""
    tag = f"ind_cs_{vout_hold}_{pout_hold}_{corner}_{temp_c}".replace(".", "p").replace("-", "m")
    return _independent_cs_cached(str(root / tag), vout_hold, pout_hold, corner, temp_c)


@lru_cache(maxsize=4)
def _independent_fb_cached(workdir: str):
    c = FB
    body = [f"Vdd vdd 0 DC {c['vdd']}", f"Vin nin 0 DC {c['vin']}", f"RL vdd nout {c['rload']}",
            f"Rf nout nin {c['rf']}"]
    for i in range(c["n"]):
        body.append(f"XM1_{i} nout nin 0 0 {NFET} l={c['L']} w={c['finger_w']}")
    prints = ["v(nout)"] + [probe("nmos", f"xm1_{i}", q) for i in range(c["n"]) for q in ("gm", "gds", "id")]
    op = run_spice("\n".join(body), Path(workdir), prints)["op"]
    gm = sum(op[probe("nmos", f"xm1_{i}", "gm").lower()] for i in range(c["n"]))
    gds = sum(op[probe("nmos", f"xm1_{i}", "gds").lower()] for i in range(c["n"]))
    return {"gm": gm, "gds": gds, "vout": op["v(nout)"]}


def independent_fb(root: Path):
    """되먹임 회로 DC 동작점(손 넷리스트: 입력 넷을 이상 전압원 0.7 V 로) -> gm, gds."""
    return _independent_fb_cached(str(root / "ind_fb"))
