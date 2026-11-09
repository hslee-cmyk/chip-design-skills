"""B74 소자 단위 점 대조 -- 엔진 봉인점 (W, L, VGS, VDS, VSB) 를 SPICE 단일 소자(전압원 바이어스)에 넣어 ID·gm·gds·VDsat 를 잰다.

읽기 전용 입력:
  it2c_spice_frame/engine/<c>.engine.json  (엔진 봉인점 dc_op, ss_dev, rows(vdsat), dc_tol_v)
  it2c_spice_frame/spice/<c>.free.cir      (오라클 넷리스트 instance 행 -- 그대로 복사)
  it2c_spice_frame/spice/<c>.B.up.txt      (회로 안 SPICE 동작점, x0 첫 행)
변형(소자마다, 같은 바이어스):
  net   : 넷리스트 instance 행 그대로(finger w, m = n, ad/as/pd/ps 그대로)
  s1    : w = 1 um 한 개(it2c 변환이 가정한 슬라이스 폭), 슬라이스 생성기 기하(ad = w*0.5um, pd = w+2um) -> x W/1um
  s5    : w = 5 um 한 개(엔진 실제 슬라이스 w_m = w_key 1000 x 5 nm), 같은 기하 -> x W/5um
  m5    : w = 5 um, m = W/5um (실수 배수) -- 엔진 모형(ID ∝ W, 5 um 슬라이스)을 넷리스트로 그대로 옮긴 것
  f5    : finger n5 = max(1, floor(W/5um)), finger_w = W/n5, m = n5, 슬라이스 생성기 기하(총폭 = 엔진 W)
  netG  : finger w·m = n 그대로, 기하만 슬라이스 생성기 규칙(ad/pd 영향 분리)
  total : w = W 한 개(nf=1, m=1), W <= 100 um 일 때만
결과: out/<c>.devtb.json, 넷리스트·로그는 run/ 아래.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

EV = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\evidence\2026-10-22\it2c_spice_frame")
ROOT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_b74")
RUN = ROOT / "run"
OUT = ROOT / "out"
NGSPICE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = r"C:\pdk\sky130_fd_pr"
W_SLICE_UM = 1.0
W5 = 5e-6   # 엔진 w_key 1000 x 제조 격자 5 nm = 슬라이스 w_m (engq.py 로 확인)
PARAMS = ("id", "gm", "gds", "gmbs", "vdsat", "vth", "vgs", "vds", "vbs")
SHOW = ("lmin", "lmax", "wmin", "wmax")


def inst_lines(cir):
    out = {}
    for ln in cir.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^X(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(sky130_fd_pr__[np]fet_01v8)\s+(.*)$", ln)
        if m:
            kv = dict(re.findall(r"(\w+)=(\S+)", m.group(7)))
            out[m.group(1)] = {"cell": m.group(6), "params": {k: float(v) for k, v in kv.items()}, "raw": m.group(7)}
    return out


def x0_row(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    head = lines[0].split()
    vals = [float(x) for x in lines[1].split()]
    return dict(zip(head, vals))


def build(name, eng, insts):
    ops = eng["device_cols"]["dc_op"]
    L = ['* B74 single-device point compare ' + name,
         f'.include "{PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
         f'.include "{PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"',
         f'.include "{PDK}\\models\\parameters\\lod.spice"',
         f'.include "{PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__tt.pm3.spice"',
         f'.include "{PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"',
         ".temp 27",
         ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7"]
    plan = []
    for m, op in ops.items():
        inst = insts[m]
        cell = inst["cell"]
        pol = 1 if op["kind"] == "nmos" else -1
        bsign = -1 if pol == 1 else 1
        tag = m.lower()
        L += [f"vg_{tag} g_{tag} 0 dc {pol * op['vgs']:.12g}",
              f"vd_{tag} d_{tag} 0 dc {pol * op['vds']:.12g}",
              f"vb_{tag} b_{tag} 0 dc {bsign * op['vsb']:.12g}"]
        W = op["W"]
        lm = op["L"]
        p = inst["params"]
        n = int(round(p["m"]))
        wf = p["w"]
        n5 = max(1, math.floor(W / W5 + 1e-9))
        variants = {
            "net": (inst["raw"], W / (wf * n)),
            "s1": (geom(lm, 1e-6, 1), W / 1e-6),
            "s5": (geom(lm, W5, 1), W / W5),
            "f5": (geom(lm, W / n5, n5), 1.0),
            "m5": (geom(lm, W5, W / W5), 1.0),
            "netG": (geom(lm, wf, n), W / (wf * n)),
        }
        if W <= 100e-6:
            variants["total"] = (geom(lm, W, 1), 1.0)
        for v, (params, scale) in variants.items():
            xi = f"x{v}_{tag}"
            L.append(f"{xi} d_{tag} g_{tag} 0 b_{tag} {cell} {params}")
            plan.append({"device": m, "variant": v, "inst": xi, "cell": cell, "scale": scale, "params": params})
    L += [".control", "set noaskquit", "option numdgt=10", "op"]
    for pl in plan:
        mi = f"@m.{pl['inst']}.m{pl['cell']}"
        L.append(f"echo BEGIN {pl['device']} {pl['variant']}")
        for q in PARAMS:
            L.append(f"print {mi}[{q}]")
        L.append(f"showmod m.{pl['inst']}.m{pl['cell']} : " + " ".join(SHOW))
        L.append(f"echo END")
    L += ["quit", ".endc", ".end"]
    return "\n".join(L) + "\n", plan


def geom(l_m, w_m, n):
    w_um = w_m * 1e6
    n = f"{n:.12g}"
    ad = w_um * 0.5
    pd = w_um + 2.0
    return (f"l={l_m:.10g} w={w_m:.10g} m={n} ad={ad:.10g}p as={ad:.10g}p pd={pd:.10g}u ps={pd:.10g}u")


def parse(text):
    res = {}
    cur = None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("BEGIN "):
            _, dev, var = s.split()
            cur = res.setdefault(dev, {}).setdefault(var, {})
            continue
        if s == "END":
            cur = None
            continue
        if cur is None:
            continue
        m = re.match(r"^@m\.\S+\[(\w+)\]\s*=\s*([-+0-9.eE]+)", s)
        if m:
            cur[m.group(1)] = float(m.group(2))
            continue
        t = s.split()
        if len(t) == 2 and t[0] in SHOW:
            cur["bin_" + t[0]] = float(t[1])
        m = re.search(r"(sky130_fd_pr__[np]fet_01v8__model\.\d+)", s)
        if m:
            cur["bin_model_txt"] = m.group(1)
    return res


def main(name):
    RUN.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    eng = json.loads((EV / "engine" / f"{name}.engine.json").read_text(encoding="utf-8"))
    insts = inst_lines(EV / "spice" / f"{name}.free.cir")
    net, plan = build(name, eng, insts)
    cir = RUN / f"{name}.devtb.cir"
    cir.write_text(net, encoding="utf-8")
    pr = subprocess.run([NGSPICE, "-b", str(cir)], capture_output=True, text=True, cwd=str(RUN), timeout=600)
    log = pr.stdout + "\n--stderr--\n" + pr.stderr
    (RUN / f"{name}.devtb.log").write_text(log, encoding="utf-8")
    meas = parse(pr.stdout)
    row = x0_row(EV / "spice" / f"{name}.B.up.txt")
    rows = {r["device"]: r for r in (eng.get("rows") or [])}
    res = {"circuit": name, "rc": pr.returncode, "plan": plan, "devices": {}}
    for m, op in eng["device_cols"]["dc_op"].items():
        cell = insts[m]["cell"]
        pre = f"@m.x{m.lower()}.m{cell}"
        incirc = {q: row.get(f"{pre}[{q}]") for q in ("id", "vds", "vdsat", "vgs")}
        res["devices"][m] = {
            "engine": {"W": op["W"], "L": op["L"], "vgs": op["vgs"], "vds": op["vds"], "vsb": op["vsb"], "id": op["current"],
                       "gm": eng["device_cols"]["ss_dev"][m]["gm"], "gds": eng["device_cols"]["ss_dev"][m]["gds"],
                       "gm_id": op["gm_id"], "vdsat": rows.get(m, {}).get("vdsat"), "tol_vdsat": rows.get(m, {}).get("tol"),
                       "dc_tol_v": eng["device_cols"]["dc_tol_v"].get(m), "lut_rel_tol": eng["device_cols"]["ss_dev"][m].get("lut_rel_tol"),
                       "w_key": op["w_key"]},
            "netlist": insts[m]["params"],
            "spice_dev": meas.get(m, {}),
            "spice_in_circuit_x0": incirc,
        }
    (OUT / f"{name}.devtb.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(name, "rc", pr.returncode, "devices", len(res["devices"]))


if __name__ == "__main__":
    for c in sys.argv[1:]:
        main(c)
