"""spice_oracle test 공용 도구.

근거: README.md 동작 계약 C1~C12 + oracle_input.schema.json 만. 오라클 소스(oracle_*.py)는 열지 않고
CLI 진입점만 subprocess 로 부른다. 기대값은 (a) 손계산, (b) 이 파일의 `independent_*` 가 손으로 쓴
독립 ngspice 넷리스트를 직접 돌린 결과에서만 만든다(피검 코드 출력으로 기대값을 만들지 않는다).

기본 실행에서 옛 엔진을 새로 돌리는 test(~260 s)는 `legacy_slow` 마커로 빠진다. `--run-legacy` 로 켠다.
독립 기준 실행이 수십 분 걸리는 test 는 `slow` 마커가 붙는다(기본 실행에 포함, 빠른 실행은 `-m "not slow"` 로 뺀다;
전체 검증은 그대로 돌린다).
환경: SPICE_ORACLE_NGSPICE(ngspice_con.exe), SPICE_ORACLE_PDK(sky130_fd_pr 루트).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

ORACLE_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = ORACLE_DIR.parents[1]
PY = sys.executable
NGSPICE = Path(os.environ.get("SPICE_ORACLE_NGSPICE", r"C:\ngspice\Spice64\bin\ngspice_con.exe"))
PDK = Path(os.environ.get("SPICE_ORACLE_PDK", r"C:\pdk\sky130_fd_pr"))

NFET = "sky130_fd_pr__nfet_01v8"
PFET = "sky130_fd_pr__pfet_01v8"


# ---------------------------------------------------------------- pytest 설정
def pytest_addoption(parser):
    parser.addoption("--run-legacy", action="store_true", default=False,
                     help="옛 엔진을 새로 돌리는 legacy_adapter test(~260 s) 실행")


def pytest_configure(config):
    config.addinivalue_line("markers", "legacy_slow: 옛 엔진 새 실행이 필요한 느린 test(--run-legacy 로 켬)")
    config.addinivalue_line("markers", "slow: 독립 기준 실행이 기본 시간 한도(600 s)를 넘는 test(빠른 실행은 -m \"not slow\" 로 뺌)")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-legacy"):
        return
    skip = pytest.mark.skip(reason="옛 엔진 새 실행(~260 s): --run-legacy 로 켬")
    for it in items:
        if "legacy_slow" in it.keywords:
            it.add_marker(skip)


def require_spice():
    if not NGSPICE.exists() or not PDK.exists():
        pytest.skip(f"ngspice({NGSPICE}) 또는 PDK({PDK}) 없음")


# ---------------------------------------------------------------- 입력 만들기
def make_lut(path: Path, corner="tt", temp_c=27.0) -> Path:
    """오라클이 메타만 읽는 LUT npz. corner/temp_c 를 None 으로 주면 그 키를 뺀다(C2 막힘용)."""
    kw = {"L": np.array([1e-6])}
    if corner is not None:
        kw["corner"] = np.array(corner)
    if temp_c is not None:
        kw["temp_c"] = np.array(float(temp_c))
    np.savez(path, **kw)
    return path


def process_block(lut: Path, diffusion=True) -> dict:
    p = PDK.as_posix()
    blk = {
        "lut_npz": str(lut),
        "models": {
            "nmos": {"subckt": NFET,
                     "includes": [f"{p}/cells/nfet_01v8/{NFET}__{{corner}}.pm3.spice",
                                  f"{p}/cells/nfet_01v8/{NFET}__mismatch.corner.spice"],
                     "op_probe": "@m.{inst}.m" + NFET + "[{param}]"},
            "pmos": {"subckt": PFET,
                     "includes": [f"{p}/models/parameters/lod.spice",
                                  f"{p}/cells/pfet_01v8/{PFET}__{{corner}}.pm3.spice",
                                  f"{p}/cells/pfet_01v8/{PFET}__mismatch.corner.spice"],
                     "op_probe": "@m.{inst}.m" + PFET + "[{param}]"},
        },
    }
    if diffusion:
        blk["diffusion"] = {"ad_per_w_m": 5e-7, "pd_extra_m": 2e-6}
    return blk


# C22(free 는 확산 기하 필수): 독립 넷리스트(ad/pd 없음 = subckt 기본 0)와 같은 회로를 free 로 돌릴 때 쓰는 명시적 면적 0.
ZERO_DIFFUSION = {"ad_m2": 0.0, "as_m2": 0.0, "pd_m": 0.0, "ps_m": 0.0,
                  "basis": "test: 면적 0 명시(독립 넷리스트에 ad/pd 없음과 같은 회로)"}
# C23(엔진 예측 전도 소자의 문턱 필수): 문턱 0 = 옛 'ID > 0 이면 전도' 규칙을 명시한 값.
OFF_ZERO = {"M1": {"off_current_A": 0.0}, "MP1": {"off_current_A": 0.0}}


def zero_diffusion(inp: dict) -> dict:
    for d in inp["devices"]:
        d["diffusion"] = dict(ZERO_DIFFUSION)
    return inp


def testbench_block() -> dict:
    return {"dc_choke_H": 1e12, "ac_couple_F": 1.0,
            "options": {"gmin": "1e-15", "reltol": "1e-4", "abstol": "1e-14", "vntol": "1e-7"},
            "ac": {"fstart_hz": 0.01, "fstop_hz": 1e10, "points_per_decade": 40, "input_ac": 1.0,
                   "input_p_ac": 0.5, "input_n_ac": -0.5, "diff_feedback_gain": 0.5}}


# 소형 회로 1: NMOS 공통소스 + 저항 부하 + 부하 C, 별도 가지로 PMOS(소스 1.5 V 레일, 바디 vdd) + 저항.
#   pb 는 PMOS 게이트에만 물린 게이트 전용 넷(C6).
CS = dict(vdd=1.8, vsp=1.5, vin=0.7, rload=1e5, cl=1e-12, L=0.5e-6, finger_w=2e-6, n=2,
          pb=0.3, rp=1e4, pL=0.5e-6, pfinger_w=2e-6, pn=3)


def cs_input(lut: Path, *, preds_nodes=None, preds_devices=None, metrics=None, constraints=None,
             judge=None, W=None, bias_voltages="default", diffusion=True, circuit="tcs_nmos_rload",
             n=None) -> dict:
    c = CS
    nfing = c["n"] if n is None else n
    dev_n = {"name": "M1", "kind": "nmos", "drain": "nout", "gate": "nin", "source": "gnd", "bulk": "gnd",
             "L": c["L"], "finger_w": c["finger_w"], "n_fingers": nfing,
             "W": c["finger_w"] * nfing if W is None else W}
    dev_p = {"name": "MP1", "kind": "pmos", "drain": "pout", "gate": "pb", "source": "vsp", "bulk": "vdd",
             "L": c["pL"], "finger_w": c["pfinger_w"], "n_fingers": c["pn"], "W": c["pfinger_w"] * c["pn"]}
    inp = {
        "schema": "spice_oracle_input/1",
        "circuit": circuit,
        "process": process_block(lut, diffusion=diffusion is True),
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "vsp", "voltage": c["vsp"]},
                  {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [dev_n, dev_p],
        "sources": [],
        "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "nout"], "value": c["rload"],
                      "value_basis": "test"},
                     {"name": "CL", "kind": "capacitor", "terminals": ["nout", "gnd"], "value": c["cl"]},
                     {"name": "RP", "kind": "resistor", "terminals": ["pout", "gnd"], "value": c["rp"]}],
        "ports": {"input": "nin", "output": "nout"},
        "predictions": {"nodes": {"nin": c["vin"], **(preds_nodes or {})},
                        "devices": preds_devices or {},
                        "metrics": metrics or []},
        "testbench": testbench_block(),
    }
    if diffusion == "zero":
        zero_diffusion(inp)
    if bias_voltages == "default":
        inp["bias_voltages"] = [{"net": "pb", "value": c["pb"]}]
    elif bias_voltages is not None:
        inp["bias_voltages"] = bias_voltages
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    if judge is not None:
        inp["judge"] = judge
    return inp


# 소형 회로 2: RC 저역통과 + 저항 분압 출력. rin -Ra- rout, rout -Rb- gnd, rout -C- gnd.
#   손계산: H0 = Rb/(Ra+Rb) = 0.5 (-6.0206 dB), fc = 1/(2 pi (Ra||Rb) C) = 159154.94 Hz.
#   DC: V(rout) = 0.5 V(rin). 레일 vdd 에 R1/R2 분압(3k/1k) -> V(dmid)=0.45.
#   소자 없는 회로는 이 계약의 대상이 아니므로 NMOS 다이오드 가지(vdd -Rd- ndio, MD) 하나를 둔다.
RC = dict(vdd=1.8, ra=2000.0, rb=2000.0, c=1e-9, r1=3000.0, r2=1000.0, vin=0.6, rd=1e5)


def rc_input(lut: Path, circuit="trc_lowpass_div") -> dict:
    c = RC
    return {
        "schema": "spice_oracle_input/1",
        "circuit": circuit,
        "process": process_block(lut),
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [{"name": "MD", "kind": "nmos", "drain": "ndio", "gate": "ndio", "source": "gnd", "bulk": "gnd",
                     "L": 1e-6, "finger_w": 1e-6, "n_fingers": 1, "W": 1e-6}],
        "passives": [{"name": "Ra", "kind": "resistor", "terminals": ["rin", "rout"], "value": c["ra"]},
                     {"name": "Rb", "kind": "resistor", "terminals": ["rout", "gnd"], "value": c["rb"]},
                     {"name": "C1", "kind": "capacitor", "terminals": ["rout", "gnd"], "value": c["c"]},
                     {"name": "R1", "kind": "resistor", "terminals": ["vdd", "dmid"], "value": c["r1"]},
                     {"name": "R2", "kind": "resistor", "terminals": ["dmid", "gnd"], "value": c["r2"]},
                     {"name": "Rd", "kind": "resistor", "terminals": ["vdd", "ndio"], "value": c["rd"]}],
        "ports": {"input": "rin", "output": "rout"},
        "predictions": {"nodes": {"rin": c["vin"]}, "devices": {}, "metrics": []},
        "testbench": testbench_block(),
    }


# 소형 회로 3: 단일단 NMOS CS + 저항 되먹임. nout -Rf- nin(게이트), nin -Cin- gnd, nout -RL- vdd, nout -CL- gnd.
#   β 망 = {Rf, Cin}(둘 다 입력 넷 nin 에 물림). 손계산 루프 이득(gm 제어원 기준 return ratio, MOS 용량 무시):
#     Zp = 1/(s Cin + 1/(s Lloop)),  Zo = 1/(1/RL + gds + s CL + 1/(Rf + Zp)),  T = gm Zo Zp/(Rf + Zp).
#   개루프 A(입력 AC 접지 via 결합 C): A = (-gm + 1/Rf) / (1/RL + gds + s CL + 1/Rf).
FB = dict(vdd=1.8, vin=0.7, rload=1e5, cl=10e-12, rf=1e6, cin=10e-12, L=0.5e-6, finger_w=2e-6, n=2,
          loop_choke=1e20)


def fb_input(lut: Path, *, feedback=("Rf", "Cin"), circuit="tfb_cs_rfeedback", loop_choke="default",
             cin=None, cl=None) -> dict:
    c = dict(FB, **{k: v for k, v in (("cin", cin), ("cl", cl)) if v is not None})
    inp = {
        "schema": "spice_oracle_input/1",
        "circuit": circuit,
        "process": process_block(lut, diffusion=False),
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [{"name": "M1", "kind": "nmos", "drain": "nout", "gate": "nin", "source": "gnd", "bulk": "gnd",
                     "L": c["L"], "finger_w": c["finger_w"], "n_fingers": c["n"], "W": c["finger_w"] * c["n"]}],
        "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "nout"], "value": c["rload"]},
                     {"name": "CL", "kind": "capacitor", "terminals": ["nout", "gnd"], "value": c["cl"]},
                     {"name": "Rf", "kind": "resistor", "terminals": ["nout", "nin"], "value": c["rf"]},
                     {"name": "Cin", "kind": "capacitor", "terminals": ["nin", "gnd"], "value": c["cin"]}],
        "ports": {"input": "nin", "output": "nout"},
        "predictions": {"nodes": {"nin": c["vin"]}, "devices": {}, "metrics": []},
        "testbench": testbench_block(),
    }
    zero_diffusion(inp)  # C22: 손계산·독립 넷리스트에 접합 용량이 없으므로 면적 0 을 명시
    if feedback is not None:
        inp["feedback_passives"] = list(feedback)
    if loop_choke == "default":
        inp["testbench"]["loop_dc_choke_H"] = c["loop_choke"]
    elif loop_choke is not None:
        inp["testbench"]["loop_dc_choke_H"] = loop_choke
    return inp


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


def fb_loop_gain(f, gm, gds, cin=None, cl=None):
    c = dict(FB, **{k: v for k, v in (("cin", cin), ("cl", cl)) if v is not None})
    s = 2j * np.pi * np.asarray(f)
    zp = 1 / (s * c["cin"] + 1 / (s * c["loop_choke"]))
    zo = 1 / (1 / c["rload"] + gds + s * c["cl"] + 1 / (c["rf"] + zp))
    return gm * zo * zp / (c["rf"] + zp)


def fb_open_loop(f, gm, gds):
    c = FB
    s = 2j * np.pi * np.asarray(f)
    return (-gm + 1 / c["rf"]) / (1 / c["rload"] + gds + s * c["cl"] + 1 / c["rf"])


def write_json(path: Path, obj) -> Path:
    path.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    return path


# ---------------------------------------------------------------- 피검 CLI 부르기
def _run(args, cwd):
    return subprocess.run([PY, "-P", *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(cwd))


def run_netlist(inp: dict, tmp: Path, bias="free", name="t", extra=()):
    """oracle_netlist.py -> (proc, 넷리스트 텍스트 또는 None, meta 또는 None)."""
    tmp.mkdir(parents=True, exist_ok=True)
    ip = write_json(tmp / f"{name}.input.json", inp)
    cir = tmp / f"{name}.{bias}.cir"
    p = _run([ORACLE_DIR / "oracle_netlist.py", ip, cir, "--bias", bias, *extra], tmp)
    text = cir.read_text(encoding="utf-8", errors="replace") if cir.exists() else None
    mp = Path(str(cir) + ".meta.json")
    meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else None
    return p, text, meta


def run_simulate(cir: Path, sim: Path, cwd: Path, extra=()):
    return _run([ORACLE_DIR / "oracle_simulate.py", cir, sim, "--ngspice", NGSPICE, *extra], cwd)


def run_compare(inp: dict, cir: Path, sim: Path, prefix: Path, judge=None, sat_margin=None, extra=()):
    """oracle_compare.py -> (proc, compare.json dict 또는 None)."""
    ip = write_json(Path(str(prefix) + ".input.json"), inp)
    args = [ORACLE_DIR / "oracle_compare.py", ip, cir, sim, prefix]
    if judge is not None:
        args += ["--judge", write_json(Path(str(prefix) + ".judge.json"), judge)]
    if sat_margin is not None:
        args += ["--sat-margin-v", repr(sat_margin)]
    p = _run([*args, *extra], prefix.parent)
    cj = Path(str(prefix) + ".compare.json")
    return p, (json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else None)


def run_oracle(inp: dict, out: Path, biases=("free",), judge=None, sat_margin=None, tag=None, name="t", extra=()):
    """oracle_run.py -> (proc, {bias: compare.json dict 또는 None})."""
    out.mkdir(parents=True, exist_ok=True)
    ip = write_json(out / f"{name}.input.json", inp)
    args = [ORACLE_DIR / "oracle_run.py", ip, out, "--bias", *biases, "--ngspice", NGSPICE]
    if judge is not None:
        args += ["--judge", write_json(out / f"{name}.judge.json", judge)]
    if sat_margin is not None:
        args += ["--sat-margin-v", repr(sat_margin)]
    if tag is not None:
        args += ["--tag", tag]
    p = _run([*args, *extra], out)
    res = {}
    for b in biases:
        cj = out / f"{stem_of(inp, b, tag)}.compare.json"
        res[b] = json.loads(cj.read_text(encoding="utf-8")) if cj.exists() else None
    return p, res


def stem_of(inp: dict, bias: str, tag=None) -> str:
    return inp["circuit"] + (f".{tag}" if tag else "") + f".{bias}"


def x_lines(text: str):
    return [ln for ln in text.splitlines() if ln[:1] in "Xx"]


def elem(text: str, name: str):
    """이름이 정확히 name(대소문자 무시)인 소자 줄의 토큰들. 없으면 None."""
    for ln in text.splitlines():
        t = ln.split()
        if t and t[0].lower() == name.lower():
            return t
    return None


def kv(tokens) -> dict:
    """['a=b', 'c=d', ...] -> {a: b}(소문자 키)."""
    return {t.split("=", 1)[0].lower(): t.split("=", 1)[1] for t in tokens if "=" in t}


def dc_value(tokens) -> float:
    """'V... n+ n- DC <v> ...' 의 DC 값."""
    up = [t.upper() for t in tokens]
    return float(tokens[up.index("DC") + 1])


def by_name(rows, key, val):
    hit = [r for r in rows if r.get(key) == val]
    assert hit, f"{key}={val} 없음: {[r.get(key) for r in rows]}"
    return hit[0]


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


@pytest.fixture(scope="session")
def ref_root(tmp_path_factory):
    require_spice()
    return tmp_path_factory.mktemp("independent")


# ---------------------------------------------------------------- 측정 정의(README "측정 정의"의 독립 구현)
def measure(f, H):
    """gain=|H(fstart)|, UGF=|H|=1 첫 하강 교차(log f 대 dB 선형 보간), PM=180-(DC위상-UGF위상),
    f-3dB=|H|<|H0|/sqrt2 인 첫 주파수 점. |H0|<1 이거나 1 아래로 안 내려가면 UGF/PM=None."""
    mag = np.abs(H)
    ph = np.degrees(np.unwrap(np.angle(H)))
    out = {"dc_gain_db": 20 * math.log10(mag[0]), "ugf_hz": None, "pm_deg": None, "f3db_hz": None}
    below = np.nonzero(mag < mag[0] / math.sqrt(2))[0]
    if below.size:
        out["f3db_hz"] = float(f[below[0]])
    if mag[0] < 1:
        return out
    for i in range(len(f) - 1):
        if mag[i] >= 1 and mag[i + 1] < 1:
            d0, d1 = 20 * math.log10(mag[i]), 20 * math.log10(mag[i + 1])
            t = d0 / (d0 - d1)
            lf = math.log10(f[i]) + t * (math.log10(f[i + 1]) - math.log10(f[i]))
            out["ugf_hz"] = 10 ** lf
            pu = ph[i] + t * (ph[i + 1] - ph[i])
            out["pm_deg"] = 180.0 - (ph[0] - pu)
            break
    return out


def ac_grid(f0, f1, ppd):
    k = np.arange(0, int(round(math.log10(f1 / f0) * ppd)) + 1)
    return f0 * 10.0 ** (k / ppd)


def preds_from_independent(ind) -> dict:
    """독립 ngspice 값을 '엔진 예측'으로 쓴 predictions(크기 규칙: VSB = -vbs, PMOS 도 @ 값 그대로)."""
    devs = {}
    for name in ("M1", "MP1"):
        d = ind[name]
        devs[name] = {"ID": d["id"], "VGS": d["vgs"], "VDS": d["vds"], "VSB": -d["vbs"], "gm": d["gm"],
                      "gds": d["gds"], "gm_id": d["gm"] / d["id"], "region": "sat", "off_current_A": 0.0}
    m = measure(ind["f"], ind["H"])
    metrics = [{"name": k, "measure": k, "value": m[k]} for k in ("dc_gain_db", "ugf_hz", "pm_deg", "f3db_hz")]
    metrics.append({"name": "ivdd", "measure": "supply_current_A", "rail": "vdd",
                    "value": (CS["vdd"] - ind["V"]["nout"]) / CS["rload"]})
    return {"nodes": {"nout": ind["V"]["nout"], "pout": ind["V"]["pout"]}, "devices": devs, "metrics": metrics}


def all_judges(cmp: dict):
    """compare.json 의 모든 판정 문자열(소자 항목별, 노드, 성능, 제약, KCL)."""
    out = []
    for d in cmp.get("devices", []):
        out += [(f"dev:{d['name']}:{k}", v) for k, v in d["judge"].items()]
    out += [(f"node:{n['net']}", n["judge"]) for n in cmp.get("nodes", [])]
    out += [(f"perf:{p.get('name')}", p["judge"]) for p in cmp.get("performance", [])]
    out += [(f"cons:{c.get('name')}", c["judge"]) for c in cmp.get("constraints", [])]
    out += [(f"kcl:{k['net']}", k["judge"]) for k in cmp.get("kcl_residual", [])]
    return out
