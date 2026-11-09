"""q2_cbox m3: 보상 C 하한의 물리 결정자 -- 합성 toy(2단 Miller, 이상 gm, 소신호 MNA 정확해).
held-out 값 미사용. 모든 수치는 이 toy 가 고른 구성 입력(spec 근거 아님).
회로: vin -gm1-> n1 (R1, C1) ; n1 -gm2-> out (R2, CL) ; Cc (+ 선택 Rz) n1-out.
질문: (1) PM 목표가 Cc 하한을 정하는가 (2) 최소 MIM(2.76 fF, m2) 이 묶이는 조건 (3) 마디 기생 C1 의 역할.
출력: m3_comp_toy.txt
"""
import math, pathlib
import numpy as np

OUT = pathlib.Path(__file__).with_suffix(".txt")
OUT.write_text("", encoding="utf-8")


def emit(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


def H(f, gm1, gm2, R1, R2, C1, CL, Cc, Rz):
    s = 2j * math.pi * f
    yc = 1.0 / (Rz + 1.0 / (s * Cc)) if Cc > 0 else 0.0
    Y = np.array([[1 / R1 + s * C1 + yc, -yc], [gm2 - yc, 1 / R2 + s * CL + yc]], dtype=complex)
    b = np.array([-gm1, 0.0], dtype=complex)   # vin=1
    v = np.linalg.solve(Y, b)
    return v[1]


def pm(gm1, gm2, R1, R2, C1, CL, Cc, Rz):
    fs = np.logspace(0, 11, 4000)
    mag = np.array([abs(H(f, gm1, gm2, R1, R2, C1, CL, Cc, Rz)) for f in fs])
    idx = np.where((mag[:-1] >= 1) & (mag[1:] < 1))[0]
    if len(idx) == 0:
        return None, None
    i = idx[0]
    lo, hi = fs[i], fs[i + 1]
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if abs(H(mid, gm1, gm2, R1, R2, C1, CL, Cc, Rz)) >= 1:
            lo = mid
        else:
            hi = mid
    fu = math.sqrt(lo * hi)
    # 위상: 저주파 위상(DC 이득 부호 = +, 두 단 반전)에서 연속 추적
    ph = np.unwrap([np.angle(H(f, gm1, gm2, R1, R2, C1, CL, Cc, Rz)) for f in np.logspace(0, math.log10(fu), 800)])
    ph0 = ph[0]
    return fu, 180.0 + math.degrees(ph[-1] - ph0)


C_MIN_MIM = 2.760e-15   # m2_pdk_mim.txt tt
cases = [  # (이름, gm1, gm2, R1, R2, C1, CL)
    ("A 소부하", 50e-6, 500e-6, 2e6, 2e5, 50e-15, 1e-12),
    ("B 중부하", 100e-6, 1e-3, 1e6, 1e5, 100e-15, 3e-12),
    ("C 대부하", 100e-6, 2e-3, 1e6, 5e4, 200e-15, 20e-12),
]
PM_T = 70.0
for name, gm1, gm2, R1, R2, C1, CL in cases:
    emit(f"== {name}: gm1={gm1:g} gm2={gm2:g} R1={R1:g} R2={R2:g} C1(마디 기생)={C1:g} CL={CL:g} ==")
    for rz_mode in ("Rz=0", "Rz=1/gm2"):
        Rz = 0.0 if rz_mode == "Rz=0" else 1.0 / gm2
        # PM >= PM_T 인 최소 Cc (Cc 증가에 PM 단조 증가 가정 -- 격자로 확인)
        grid = np.logspace(math.log10(1e-16), math.log10(1e-10), 241)
        rows = [(c, *pm(gm1, gm2, R1, R2, C1, CL, c, Rz)) for c in grid]
        ok = [c for c, fu, p in rows if p is not None and p >= PM_T]
        cmin = ok[0] if ok else None
        mono = all((rows[i + 1][2] or -999) >= (rows[i][2] or -999) - 1e-6 for i in range(len(rows) - 1) if rows[i][2] is not None)
        hand = math.tan(math.radians(PM_T)) * gm1 / gm2 * CL if rz_mode == "Rz=0" else None
        p_mim = pm(gm1, gm2, R1, R2, C1, CL, C_MIN_MIM, Rz)
        p_box = pm(gm1, gm2, R1, R2, C1, CL, 1e-13, Rz)
        emit(f"  {rz_mode}: Cc_min(PM>={PM_T:.0f}) = {cmin:.3g} F" + (f" | 손계산 tan(PM)*gm1/gm2*CL = {hand:.3g} F (비 {cmin/hand:.2f})" if hand and cmin else "")
             + f" | PM 단조={mono}")
        emit(f"     Cc=C_min_MIM {C_MIN_MIM:.3g}: fu={p_mim[0]:.3g} Hz PM={p_mim[1]:.1f} deg ; Cc=0.1pF: fu={p_box[0]:.3g} PM={p_box[1]:.1f} ; Cc_min/C_min_MIM = {cmin/C_MIN_MIM:.0f}배, Cc_min/C1 = {cmin/C1:.1f}")
emit("")
emit("해석 열쇠: Cc_min 은 PM 목표·gm 비·CL(선언 부하)이 정한다. 최소 MIM 은 PM 목표가 있는 한 묶이지 않는다(Cc_min >> C_min_MIM).")
emit("PM 목표가 없으면 면적 목적이 Cc 를 상자 하한으로 민다 -> 하한 = 설계값 (하한 값이 무엇이든). 그 경우 실현 가능한 가장 작은 값 = 최소 MIM 이 물리 하한.")
