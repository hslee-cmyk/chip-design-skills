"""current_reuse 상보 입력쌍 입력 공통모드 창 SPICE 확인 (sky130 tt, ngspice_con -b).
반 회로: 꼬리 = 이상 전류원 2I(위 vdd->Vx, 아래 Vy->gnd), 입력 PMOS M1a/M1b(source Vx), NMOS M4a/M4b(source Vy),
드레인 = 이상 캐스코드 노드(PMOS 드레인 0.5 V, NMOS 드레인 1.3 V 고정). 두 입력 묶음(공통모드)으로 Vin을 쓸어
꼬리 여유 Vy - VDSAT_tail_n, (VDD - Vx) - VDSAT_tail_p 가 둘 다 >= 0 인 Vin 구간 = 창.
꼬리 VDSAT 은 LUT 에서 gm/ID 12 기준값(lut_checks.out.jsonl cr_window_density: Vy 0.135, VDD-Vx 0.141 @ L 0.5u).
결과는 cr_input_window.out.jsonl 에 케이스마다 append."""
import json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cr_input_window.out.jsonl")
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = r"C:\pdk\sky130_fd_pr"
INC = [
    rf'.include "{PDK}\models\parameters\lod.spice"',
    rf'.include "{PDK}\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__tt.pm3.spice"',
    rf'.include "{PDK}\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"',
    rf'.include "{PDK}\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
    rf'.include "{PDK}\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"',
]
VY_MIN, VXDROP_MIN = 0.135, 0.141


def run(wp_um, wn_um, i_side_ua, L_um=0.5):
    # 손가락 w = 5u, m = W/5 (sky130 bin wmax 제한 -- W-bin 손가락 규칙과 같은 꼴)
    mp, mn = max(1, round(wp_um / 5)), max(1, round(wn_um / 5))
    fwp, fwn = wp_um / mp, wn_um / mn
    net = "\n".join(["* cr input window"] + INC + [
        "vdd vdd 0 1.8",
        "vin in 0 0.9",
        f"itp vdd vx {2*i_side_ua}u",
        f"itn vy 0 {2*i_side_ua}u",
        "vdp dp 0 0.5", "vdn dn 0 1.3",
        f"xm1a dp in vx vdd sky130_fd_pr__pfet_01v8 l={L_um}u w={fwp}u m={mp}",
        f"xm1b dp in vx vdd sky130_fd_pr__pfet_01v8 l={L_um}u w={fwp}u m={mp}",
        f"xm4a dn in vy 0 sky130_fd_pr__nfet_01v8 l={L_um}u w={fwn}u m={mn}",
        f"xm4b dn in vy 0 sky130_fd_pr__nfet_01v8 l={L_um}u w={fwn}u m={mn}",
        ".option gmin=1e-15",
        ".control", "dc vin 0.3 1.5 0.005", "wrdata __OUT__ v(vx) v(vy)", "quit", ".endc", ".end"])
    with tempfile.TemporaryDirectory() as td:
        dat = os.path.join(td, "o.txt").replace("\\", "/")
        cir = os.path.join(td, "t.cir")
        open(cir, "w").write(net.replace("__OUT__", dat))
        r = subprocess.run([NG, "-b", cir], capture_output=True, text=True, timeout=300)
        if not os.path.exists(dat):
            return {"error": r.stdout[-800:] + r.stderr[-800:]}
        rows = [list(map(float, ln.split())) for ln in open(dat) if ln.strip()]
    ok = [r[0] for r in rows if r[3] >= VY_MIN and (1.8 - r[1]) >= VXDROP_MIN]
    at09 = min(rows, key=lambda r: abs(r[0] - 0.9))
    res = {"Wp_um": wp_um, "Wn_um": wn_um, "I_side_uA": i_side_ua, "L_um": L_um,
           "IDu_p_A_per_um": i_side_ua * 1e-6 / wp_um, "IDu_n_A_per_um": i_side_ua * 1e-6 / wn_um,
           "window": [min(ok), max(ok)] if ok else None,
           "center": round((min(ok) + max(ok)) / 2, 3) if ok else None,
           "Vx_at_0p9": round(at09[1], 3), "Vy_at_0p9": round(at09[3], 3), "has_0p9": bool(ok and min(ok) <= 0.9 <= max(ok))}
    return res


if __name__ == "__main__":
    for wp, wn, i in [(10, 5, 5), (50, 5, 5), (200, 20, 5), (1000, 50, 5), (2000, 100, 5), (5000, 200, 5)]:
        rec = {"case": "cr_input_window_spice", **run(wp, wn, i)}
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(json.dumps(rec, ensure_ascii=False))
