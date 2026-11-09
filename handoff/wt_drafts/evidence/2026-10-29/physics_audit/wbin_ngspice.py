"""W-bin: ngspice가 bin을 고르는 폭이 인스턴스 w인지(손가락 m·nf 처리)와 호환 모드 영향 확인. sky130 nfet tt.
같은 총 폭 W_tot를 (a) w=W_tot nf=1 m=1 (b) w=W_tot/2 m=2 (c) w=W_tot nf=2 로 두고 ID를 비교.
compat: 없음 / 'hs' (set ngbehavior=hs, .spiceinit 대신 .control 앞 줄 불가 -> -D 옵션 사용).
결과 wbin_ngspice.out.jsonl append."""
import json, os, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "wbin_ngspice.out.jsonl")
NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
PDK = r"C:\pdk\sky130_fd_pr"
INC = [rf'.include "{PDK}\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__tt.pm3.spice"',
       rf'.include "{PDK}\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"']


def run(inst, compat):
    net = "\n".join(["* wbin"] + INC + [
        "vd d 0 0.9", "vg g 0 0.9",
        f"xm1 d g 0 0 sky130_fd_pr__nfet_01v8 l=0.5u {inst}",
        ".control", "op", "print -i(vd)", "quit", ".endc", ".end"])
    with tempfile.TemporaryDirectory() as td:
        cir = os.path.join(td, "t.cir")
        open(cir, "w").write(net)
        args = [NG, "-b"]
        if compat:
            args += ["-D", f"ngbehavior={compat}"]
        r = subprocess.run(args + [cir], capture_output=True, text=True, timeout=120)
    txt = r.stdout + r.stderr
    val = None
    for ln in txt.splitlines():
        if "-i(vd)" in ln and "=" in ln:
            val = float(ln.split("=")[1])
    return val, ("could not find a valid modelname" in txt)


if __name__ == "__main__":
    for wtot in (6.0, 10.0, 14.0, 20.0):
        for compat in (None, "hs"):
            rows = {}
            for tag, inst in (("w_total_nf1", f"w={wtot}u"), ("w_half_m2", f"w={wtot/2}u m=2"),
                              ("w_total_nf2", f"w={wtot}u nf=2")):
                rows[tag] = run(inst, compat)
            rec = {"case": "wbin", "W_tot_um": wtot, "compat": compat,
                   **{k: {"ID_A": v[0], "no_bin": v[1]} for k, v in rows.items()}}
            with open(OUT, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(json.dumps(rec))
