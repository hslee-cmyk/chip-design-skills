"""B74 회로 동작점 재현 -- it2c free 넷리스트 본문(연결·바이어스·follower 구성 B·nodeset) 은 그대로 두고 MOS instance 기하만 바꿔 .op.

기하 3가지:
  net : it2c 넷리스트 그대로(finger = W / floor(W/1um), w_key 를 nm 로 읽은 변환)
  m5  : w = 5 um, m = W/5um(실수 배수) -- 엔진 모형(5 um 슬라이스 x W/5um) 그대로
  f5  : finger n5 = max(1, floor(W/5um)), finger_w = W/n5 -- 5 um 이상 finger 로 실현(물리적으로 만들 수 있는 배치)
결과: out/<c>.circop.json (노드 전압, 소자 id·vds·vdsat·vgs), 넷리스트·로그 run/.
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

EV = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\evidence\2026-10-22\it2c_spice_frame")
ROOT = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_b74")
NGSPICE = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
W5 = 5e-6


def geom(l_m, w_m, n):
    w_um = w_m * 1e6
    ad = w_um * 0.5
    pd = w_um + 2.0
    return f"l={l_m:.10g} w={w_m:.10g} m={n:.12g} ad={ad:.10g}p as={ad:.10g}p pd={pd:.10g}u ps={pd:.10g}u"


def run(name, mode, eng):
    src = (EV / "spice" / f"{name}.free.cir").read_text(encoding="utf-8")
    body = src.split(".control")[0]
    ops = eng["device_cols"]["dc_op"]
    out_lines, devs, nodes = [], [], set()
    for ln in body.splitlines():
        m = re.match(r"^X(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(sky130_fd_pr__[np]fet_01v8)\s+(.*)$", ln)
        if m:
            dev = m.group(1)
            devs.append((dev, m.group(6)))
            op = ops[dev]
            W, L = op["W"], op["L"]
            if mode == "m5":
                ln = " ".join(m.group(i) for i in range(1, 7)).join(["X", " "]) + geom(L, W5, W / W5)
            elif mode == "f5":
                n5 = max(1, math.floor(W / W5 + 1e-9))
                ln = " ".join(m.group(i) for i in range(1, 7)).join(["X", " "]) + geom(L, W / n5, n5)
        out_lines.append(ln)
    nodes = sorted(k for k in eng["values"])
    ctl = [".control", "set noaskquit", "option numdgt=10", "op"]
    for n in nodes:
        ctl.append(f"print v({n})")
    for dev, cell in devs:
        for q in ("id", "vds", "vdsat", "vgs", "vth"):
            ctl.append(f"print @m.x{dev.lower()}.m{cell}[{q}]")
    ctl += ["quit", ".endc", ".end"]
    cir = ROOT / "run" / f"{name}.circop.{mode}.cir"
    cir.write_text("\n".join(out_lines).rstrip() + "\n" + "\n".join(ctl) + "\n", encoding="utf-8")
    pr = subprocess.run([NGSPICE, "-b", str(cir)], capture_output=True, text=True, cwd=str(ROOT / "run"), timeout=600)
    (ROOT / "run" / f"{name}.circop.{mode}.log").write_text(pr.stdout + "\n--stderr--\n" + pr.stderr, encoding="utf-8")
    res = {"rc": pr.returncode, "nodes": {}, "devices": {}}
    for ln in pr.stdout.splitlines():
        mm = re.match(r"^v\((\S+)\)\s*=\s*([-+0-9.eE]+)", ln.strip())
        if mm:
            res["nodes"][mm.group(1).lower()] = float(mm.group(2))
        mm = re.match(r"^@m\.x(\w+)\.m\S+\[(\w+)\]\s*=\s*([-+0-9.eE]+)", ln.strip())
        if mm:
            res["devices"].setdefault(mm.group(1).upper(), {})[mm.group(2)] = float(mm.group(3))
    return res


def main(name):
    eng = json.loads((EV / "engine" / f"{name}.engine.json").read_text(encoding="utf-8"))
    out = {"circuit": name, "engine_nodes": eng["values"], "modes": {}}
    for mode in ("net", "m5", "f5"):
        out["modes"][mode] = run(name, mode, eng)
    (ROOT / "out" / f"{name}.circop.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(name, {m: r["rc"] for m, r in out["modes"].items()})


if __name__ == "__main__":
    for c in sys.argv[1:]:
        main(c)
