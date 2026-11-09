"""(c) 순차 방식 재실행: 진전 판정을 '옮긴 metric'만으로 고친 뒤(z1_multi.py). (a)(b)는 정지 규칙 변경과 무관
(모든 metric을 매 걸음 옮김)이라 다시 돌리지 않는다. 결과 multi.jsonl append(case 이름 끝 '_c3'(같은 파일 첫 실행 '_c2'는 Edit 실패로 수정 전 코드가 돈 기록 -- 무효))."""
import z1_multi as M
import z1_toy as z

RES = 0.01
if __name__ == "__main__":
    for caps in (False, "mirror"):
        for cl, gbw in ((1e-12, 50e6), (1e-13, 300e6), (3e-14, 600e6)):
            for g in (12.0, 18.0):
                base = {"L1": 5e-7, "L3": 5e-7, "gmid1": g, "gmid3": 10.0, "I": 50e-6, "CL": cl}
                spec = {"GBW": gbw, "A0": round(z.hand(base)["A0"], 2)}
                M.close_multi(M.ToyA(base, spec, caps=caps), f"A_{'caps' if caps else 'base'}_cl{cl:.0e}_g{g:g}_c3", "c", RES)
    bb = {"L1": 5e-7, "L3": 5e-7, "L6": 5e-7, "L7": 5e-7, "gmid1": 14.0, "gmid3": 10.0, "gmid6": 10.0,
          "gmid7": 10.0, "I1": 10e-6, "I2": 30e-6}
    for cl, cc, gbw, pm in ((1e-12, 3e-13, 30e6, 60.0), (2e-13, 6e-14, 100e6, 60.0), (2e-13, 6e-14, 100e6, 70.0)):
        base = dict(bb, CL=cl, Cc=cc)
        a0 = round(M.ToyB(base, {}).hand(base)["A0"], 1)
        M.close_multi(M.ToyB(base, {"GBW": gbw, "PM": pm, "A0": a0}), f"B_cl{cl:.0e}_pm{pm:g}_c3", "c", RES)
