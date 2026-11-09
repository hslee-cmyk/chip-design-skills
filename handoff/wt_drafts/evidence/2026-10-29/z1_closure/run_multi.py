"""다제약 닫기 케이스 구동(multi.jsonl에 케이스마다 append, 화면은 run_multi.out.txt)."""
import z1_multi as M
import z1_toy as z

RES = 0.01
if __name__ == "__main__":
    # toy A: 5T, {GBW, A0}, 손계산 기본 꼴 / 정밀화 꼴(out+mirror)
    for caps in (False, "mirror"):
        for cl, gbw in ((1e-12, 50e6), (1e-13, 300e6), (3e-14, 600e6)):
            for g in (12.0, 18.0):
                base = {"L1": 5e-7, "L3": 5e-7, "gmid1": g, "gmid3": 10.0, "I": 50e-6, "CL": cl}
                spec = {"GBW": gbw, "A0": round(z.hand(base)["A0"], 2)}
                toy = M.ToyA(base, spec, caps=caps)
                for meth in ("a", "b", "c"):
                    M.close_multi(toy, f"A_{'caps' if caps else 'base'}_cl{cl:.0e}_g{g:g}", meth, RES)
    # toy B: 2단 Miller, {GBW, PM, A0}
    bb = {"L1": 5e-7, "L3": 5e-7, "L6": 5e-7, "L7": 5e-7, "gmid1": 14.0, "gmid3": 10.0, "gmid6": 10.0,
          "gmid7": 10.0, "I1": 10e-6, "I2": 30e-6}
    for cl, cc, gbw, pm in ((1e-12, 3e-13, 30e6, 60.0), (2e-13, 6e-14, 100e6, 60.0), (2e-13, 6e-14, 100e6, 70.0)):
        base = dict(bb, CL=cl, Cc=cc)
        a0 = round(M.ToyB(base, {}).hand(base)["A0"], 1)
        toy = M.ToyB(base, {"GBW": gbw, "PM": pm, "A0": a0})
        for meth in ("a", "b", "c"):
            M.close_multi(toy, f"B_cl{cl:.0e}_pm{pm:g}", meth, RES)
