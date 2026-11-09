"""interface card 손계산 식 검산 -- 엔진 import 0, numpy KCL 직접 풀이 대 닫힌 식. 기대값 출처 아님(test 기대값은 card의 닫힌 식에서 test 작성자가 만든다).

실행: PYTHONIOENCODING=utf-8 C:/Python314/python.exe toy_hand_check.py
결과: 같은 폴더 toy_hand_check.jsonl
"""
import json
from pathlib import Path

import numpy as np

OUT = open(Path(__file__).resolve().parent / "toy_hand_check.jsonl", "w", encoding="utf-8")


def report(name, closed, solved):
    row = {"toy": name, "closed": closed, "solved": solved, "rel": abs(closed - solved) / max(abs(closed), 1e-300)}
    OUT.write(json.dumps(row) + "\n")
    OUT.flush()
    print(row)
    assert row["rel"] < 1e-10, name


gm1, gds1, gm2, gmb2, gds2, r1, r2 = 1e-3, 2e-5, 5e-4, 5e-5, 1e-5, 3e4, 2e4
# T-1 CS -> CG. 블록 A U_b = {x}: M1(d x, g in, s gnd), R1(vdd-x), M2(d out = 고정 0, g vb = 고정 0, s x)
gin = gm2 + gmb2 + gds2
a_closed = -gm1 / (gds1 + 1 / r1 + gin)
y = np.array([[gds1 + 1 / r1 + gin]])
report("T1_A_gain", a_closed, float(np.linalg.solve(y, np.array([-gm1]))[0]))
report("T1_A_zout", 1 / (gds1 + 1 / r1 + gin), float(np.linalg.solve(y, np.array([1.0]))[0]))
# 블록 B U_b = {out}: 입력 x 구동. i(d->s)= gm(0-vx) + gmb(0-vx) + gds(vo-vx) -> KCL(out): vo/r2 + that = 0
b_closed = gin / (gds2 + 1 / r2)
report("T1_B_gain", b_closed, float(np.linalg.solve(np.array([[gds2 + 1 / r2]]), np.array([gin]))[0]))
# T-1 부하 뺀 상한(행 모드 값): |A0| = gm1/(gds1 + 1/r1) >= |A|
a0 = gm1 / (gds1 + 1 / r1)
assert a0 >= abs(a_closed)
report("T2_bound_ratio", (gds1 + 1 / r1 + gin) / (gds1 + 1 / r1), a0 / abs(a_closed))
# T-3 막다른 가지: Rz(out-mz), mz 에 저항 끝만. 미지수 {out, mz} 풀이 = {out} 풀이
rz = 5e3
gz = 1 / rz
y2 = np.array([[gds1 + 1 / r1 + gz, -gz], [-gz, gz]])
x2 = np.linalg.solve(y2, np.array([-gm1, 0.0]))
report("T3_same_gain", -gm1 / (gds1 + 1 / r1), float(x2[0]))
report("T3_mz_equals_out", float(x2[0]), float(x2[1]))
# T-3b 막다른 넷 gate 독자: M2(d o2, g mz, s gnd), R2(vdd-o2). 출력 o2 = gm2·gm1·R'·R2'
rp1, rp2 = 1 / (gds1 + 1 / r1), 1 / (gds2 + 1 / r2)
y3 = np.array([[1 / rp1 + gz, -gz, 0.0], [-gz, gz, 0.0], [0.0, gm2, 1 / rp2]])
x3 = np.linalg.solve(y3, np.array([-gm1, 0.0, 0.0]))
report("T3b_gate_reader", gm1 * rp1 * gm2 * rp2, float(x3[2]))
# T-4 용량 전용 노드: in-C1-n, n-C2-gnd, M1(d out, g n, s gnd), cgs·cgd·cgb, RL
c1, c2, cgs, cgd, cgb = 2e-12, 3e-12, 1e-13, 5e-14, 2e-14
rp = rp1
closed = -gm1 * rp * c1 / (c1 + c2 + cgs + cgb + cgd * (1 + gm1 * rp))
# 미지수 (n, out): 전하 보존 행 (c1+c2+cgs+cgb+cgd)·vn - cgd·vo = c1·1, KCL 행 gm1·vn + vo/rp = 0
m = np.array([[c1 + c2 + cgs + cgb + cgd, -cgd], [gm1, 1 / rp]])
x4 = np.linalg.solve(m, np.array([c1, 0.0]))
report("T4_charge_gain", closed, float(x4[1]))
report("T4_vn", c1 / (c1 + c2 + cgs + cgb + cgd * (1 + gm1 * rp)), float(x4[0]))
# T-5 L 안쪽 극값: gain(L) = x(L)/y (x 포물선) 은 끝점보다 안쪽 값이 크다
la, lb = 1e-6, 2e-6
lm = (la + lb) / 2


def peak(L):
    return 10 * (1 + 0.2 * (1 - ((L - lm) / (lb - la) * 2) ** 2))


assert peak(lm) > max(peak(la), peak(lb))
report("T5_peak_over_end", 1.2 / 1.0, peak(lm) / peak(la))
print("ok")
