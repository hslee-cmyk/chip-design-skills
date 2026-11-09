"""O-174 재검토 측정 (2026-10-31). 읽기 전용 측정, 결과는 results.txt 에 케이스마다 append.

D. 부유 드레인 평형 V(d)-V(s): bulk {레일 vdd, source} x 온도 {-40, 27, 85, 125} x 접합 기하 {0, 1x, 2x}.
   기하 1x = 2026-10-29 evidence 와 같은 ad=as=0.87p pd=ps=6.58u (W=3u, 확산 길이 0.29u 가정 -- 이전 측정 재현용).
E. 드레인 강제 DC I-V: M19 꼴(S=VCN 0.7, G=V_Z) 드레인을 0.0~1.8 V 로 쓸어 채널·접합(드레인-벌크) 전류 분리.
   bulk = source 이면 드레인 > source + 접합 문턱에서 p+/n-well 순바이어스(클램프) 여부.
F. 과도: 드레인 = 채널 + CBAT(스캔 0.1/1/10 pF, 원문 값 미기재) + 반대편 X 에 계단 dX(스캔 0.2~0.8 V).
   M19 꼴의 승압(드레인이 VCN 위로) 최대값과 0.5 us(원문 1% 정착 0.473 us 근방) 뒤 값, bulk 두 경우.
   M21 꼴은 CBAT2 를 통한 계단 양방향.
값 출처: VCN 0.7, VCP 1.1, VDD 1.8 = 원문 Fig.6 표(p.8); W/L 3/1 um = Table 1(p.9); V_Z 0.4957 = 2026-10-29 sky130 전체 회로 .op 실측.
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results.txt")
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
LIB = "\n".join(['.include "C:/pdk/sky130_fd_pr/models/parameters/lod.spice"'] + [
    f'.include "C:/pdk/sky130_fd_pr/cells/{c}/sky130_fd_pr__{c}__{f}.spice"'
    for c in ("nfet_01v8", "pfet_01v8") for f in ("tt.pm3", "mismatch.corner")])
P = "sky130_fd_pr__pfet_01v8"
VDD, VCN, VCP, VZ = 1.8, 0.7, 1.1, 0.4957
GEOM = {"0": "", "1x": "ad=0.87p as=0.87p pd=6.58u ps=6.58u", "2x": "ad=1.74p as=1.74p pd=13.16u ps=13.16u"}


def log(t):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(t + "\n")


def run(name, deck):
    cir = os.path.join(HERE, name + ".cir")
    with open(cir, "w", encoding="utf-8") as f:
        f.write(deck)
    r = subprocess.run([NG, "-b", cir], capture_output=True, text=True, timeout=600)
    with open(cir + ".log", "w", encoding="utf-8") as f:
        f.write(r.stdout + "\n" + r.stderr)
    return r.stdout


def vals(out):
    d = {}
    for m in re.finditer(r"^\s*([\w\(\)\.\#\[\]:@]+)\s*=\s*([-+0-9.eE]+)", out, re.M):
        d[m.group(1).lower()] = float(m.group(2))
    return d


def part_d():
    log("\n### D. 부유 드레인 평형 V(d)-V(s) [V] (gmin 1e-18, 드레인 = 채널 + 드레인 접합 + 1 pF)")
    log("| 꼴 | bulk | 기하 | -40C | 27C | 85C | 125C |\n|---|---|---|---|---|---|---|")
    cases = [("M19/M20 S=VCN G=V_Z", VCN, VZ), ("M21 S=VCP G=VCN", VCP, VCN)]
    for lab, vs, vg in cases:
        for bulk in ("vdd", "src"):
            for gk, gs in GEOM.items():
                row = []
                for T in (-40, 27, 85, 125):
                    b = "s" if bulk == "src" else "vdd"
                    deck = "\n".join(["* D", LIB, ".option gmin=1e-18", f".temp {T}", f"vdd vdd 0 {VDD}",
                                      f"vs s 0 {vs}", f"vg g 0 {vg}", f"x1 d g s {b} {P} w=3u l=1u {gs}", "c1 d 0 1p",
                                      ".control", "op", "print v(d)-v(s)", ".endc", ".end"])
                    o = run(f"d_{lab[:3]}_{bulk}_{gk}_{T}".replace("/", ""), deck)
                    m = re.search(r"v\(d\)-v\(s\)\s*=\s*([-+0-9.eE]+)", o)
                    row.append(f"{float(m.group(1)):+.4f}" if m else "ERR")
                log(f"| {lab} | {bulk} | {gk} | " + " | ".join(row) + " |")


def part_e():
    log("\n### E. M19 꼴 드레인 강제 DC 쓸기 (S=VCN 0.7, G=V_Z 0.4957, 기하 1x, 27C): I_d 전체, 드레인-벌크 접합 전류 ibd")
    log("| V(d) | bulk=vdd I_d [A] | bulk=vdd ibd [A] | bulk=src I_d [A] | bulk=src ibd [A] |\n|---|---|---|---|---|")
    res = {}
    for bulk in ("vdd", "src"):
        b = "s" if bulk == "src" else "vdd"
        deck = "\n".join(["* E", LIB, ".option gmin=1e-18", f"vdd vdd 0 {VDD}", f"vs s 0 {VCN}", f"vg g 0 {VZ}",
                          "vd d 0 0.7", f"x1 d g s {b} {P} w=3u l=1u {GEOM['1x']}",
                          ".control", "save all @m.x1.m" + P + "[ibd]",
                          "dc vd 0 1.8 0.1",
                          "print v(d) i(vd) @m.x1.m" + P + "[ibd]", ".endc", ".end"])
        o = run(f"e_{bulk}", deck)
        rows = []
        for line in o.splitlines():
            p = line.split()
            if len(p) == 5 and p[0].isdigit():
                try:
                    rows.append((float(p[2]), -float(p[3]), float(p[4])))
                except ValueError:
                    pass
        res[bulk] = rows
    for (v, i1, j1), (_, i2, j2) in zip(res["vdd"], res["src"]):
        log(f"| {v:.1f} | {i1:+.3e} | {j1:+.3e} | {i2:+.3e} | {j2:+.3e} |")


def part_f():
    log("\n### F. 과도 승압: 드레인 = 채널 + CBAT -> 계단 dX (상승 1 ns, 27C, 기하 1x). peak = 최대 V(d)-V(s), v@0.5us = 계단 0.5 us 뒤 V(d)-V(s), qloss = 0.5 us 까지 드레인 접합으로 빠진 전하 / (CBAT*dX)")
    log("| 꼴 | CBAT | dX | bulk=vdd peak | bulk=vdd v@0.5us | bulk=src peak | bulk=src v@0.5us |\n|---|---|---|---|---|---|---|")
    cases = [("M19 S=VCN G=V_Z", VCN, VZ), ("M21 S=VCP G=VCN", VCP, VCN)]
    for lab, vs, vg in cases:
        dxs = (0.2, 0.4, 0.6, 0.8) if lab.startswith("M19") else (-0.8, -0.4, 0.4, 0.8)
        for cb in ("0.1p", "1p", "10p"):
            for dx in dxs:
                row = []
                for bulk in ("vdd", "src"):
                    b = "s" if bulk == "src" else "vdd"
                    deck = "\n".join(["* F", LIB, ".option gmin=1e-18", f"vdd vdd 0 {VDD}", f"vs s 0 {vs}",
                                      f"vg g 0 {vg}", f"vx x 0 pwl(0 0 10n 0 11n {dx})",
                                      f"x1 d g s {b} {P} w=3u l=1u {GEOM['1x']}", f"cb d x {cb}",
                                      f".ic v(d)={vs}",
                                      ".control", "tran 1n 520n uic", "let e = v(d)-v(s)",
                                      "meas tran pk MAX e", "meas tran mn MIN e", "meas tran v05 FIND e AT=510n",
                                      ".endc", ".end"])
                    o = run(f"f_{lab[:3]}_{cb}_{dx}_{bulk}", deck)
                    d = vals(o)
                    pk = d.get("pk"); mn = d.get("mn"); v05 = d.get("v05")
                    ext = pk if dx > 0 else mn
                    row += [f"{ext:+.3f}" if ext is not None else "ERR", f"{v05:+.3f}" if v05 is not None else "ERR"]
                log(f"| {lab} | {cb} | {dx:+.1f} | " + " | ".join(row) + " |")


if __name__ == "__main__":
    open(OUT, "w", encoding="utf-8").close()
    log("O-174 재검토 측정 (sky130 tt, ngspice-46, 스크립트 recheck.py)")
    part_d()
    part_e()
    part_f()
    log("\nDONE")
