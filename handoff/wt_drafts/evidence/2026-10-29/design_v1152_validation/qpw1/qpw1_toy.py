"""Q-PW1 독립 점검: 'DUT 전력 = Σ_counted rails V_k·I_k,DUT'의 Tellegen 근거와 toy 기대.

이상 소자 toy(nmcnr 레일 값: vdd 1.8, vss 0, agnd 0.9, RL 25 kΩ -- spec·topology 값).
DUT = 첫 단 전류 I1(vdd→vss) + 출력단. 출력 DC = 0.9 + δ, I_out = δ/RL(DUT 출력 포트 → RL → agnd).
(A) class-A 출력단: 위 전류원 I_p 고정(vdd→Vout), 아래 소자가 I_p − I_out 을 vss 로.
(B) push-pull 출력단: 위 = I_q + max(I_out,0), 아래 = I_q + max(−I_out,0).
보고: P_def = Σ_rails V_k·I_k,DUT(design 정의), P_diss = DUT 소산(Tellegen -- DUT 모든 단자),
      P_RL = RL 소산, 차 P_def − P_diss = V_out·I_out(출력 포트 전력, 0 V 기준).
"""
import json
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.jsonl")
VDD, VSS, AGND, RL = 1.8, 0.0, 0.9, 25e3
I1, IP, IQ = 50e-6, 100e-6, 20e-6


def rec(kind, d):
    vout = AGND + d
    iout = d / RL
    if kind == "classA":
        i_vdd = I1 + IP
        i_vss = I1 + IP - iout
    else:
        i_vdd = I1 + IQ + max(iout, 0.0)
        i_vss = I1 + IQ + max(-iout, 0.0)
    p_def = VDD * i_vdd - VSS * i_vss + AGND * 0.0          # agnd 에 DUT 단자 없음
    # DUT 소산 = Σ 단자 V·I(들어가는 방향): vdd 단자 +i_vdd, vss 단자 −i_vss, 출력 단자 −iout
    p_diss = VDD * i_vdd + VSS * (-i_vss) + vout * (-iout)
    p_rl = d * d / RL
    # 기준 이동(모든 전위에 +0.9 V -- agnd 를 0 V 로): rail-only 합의 변화
    p_def_shift = (VDD - AGND) * i_vdd + (VSS - AGND) * (-i_vss)
    return {"kind": kind, "delta_V": d, "P_def_uW": round(p_def * 1e6, 4), "P_diss_uW": round(p_diss * 1e6, 4),
            "P_RL_uW": round(p_rl * 1e6, 4), "P_def_minus_P_diss_uW": round((p_def - p_diss) * 1e6, 4),
            "Vout_Iout_uW": round(vout * iout * 1e6, 4), "P_def_ref_agnd_uW": round(p_def_shift * 1e6, 4)}


with open(OUT, "w", encoding="utf-8") as fh:
    for kind in ("classA", "pushpull"):
        for d in (-0.3, -0.1, 0.0, 0.1, 0.3):
            r = rec(kind, d)
            fh.write(json.dumps(r) + "\n")
            print(json.dumps(r))
