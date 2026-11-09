"""design v1.15.2 검증 M-1 / 재판정 P7 -- DUT 전력 정의 후보의 nmcnr 꼴 손계산 toy(정의 결정은 계획 v6.38.4 몫; 이 파일은 수치만).

nmcnr 연결(topology `nmcnr_amplifier.topology.json`): 공급 vdd 1.8 V·vss 0 V(넷리스트 0 V), 중간 rail agnd 0.9 V(측정 부하
RL 25 kΩ·CL이 Vout–agnd -- spec measurement_load), 출력단 class-A(M301 nmos 구동 -- vss, M302 pmos 전류원 -- vdd).
DUT 단자 = vdd·vss·Vout(입력 DC 전류 0). 첫·둘째 단 전류 합 I12, 출력단 전류원 I3(가정값 -- 상대 비교용, 상수 아님).
출력 DC = 0.9 + δ, I_out = δ/RL(DUT → RL → agnd).
후보: (A0) 레일 단자 합, 기준 = 넷리스트 0 V: Σ_k (V_k − 0)·I_k,DUT  (A1) 같은 합, 기준 = agnd(기준 의존성 확인)
      (B) DUT 소산 = DUT 모든 단자 Σ V·I(Tellegen -- 기준 무관)  (C) 모든 공급원 전력(agnd 원 포함) = (B) + P_RL
      항등식 확인: A0 − B = V_out·I_out(0 V 기준 출력 포트 전력). push-pull 꼴(Q 전류 IQ)도 같은 표로.
결과 = m1_power_toy.out.jsonl(덮어씀)."""
import json, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m1_power_toy.out.jsonl")
VDD, VSS, AGND, RL = 1.8, 0.0, 0.9, 25e3
CASES = {"classA_nmcnr": dict(I12=20e-6, I3=40e-6), "pushpull": dict(I12=20e-6, IQ=20e-6)}


def point(kind, p, d):
    vout = AGND + d
    iout = d / RL                                   # DUT 출력 단자에서 나가는 전류
    if kind == "classA_nmcnr":
        i_dd = p["I12"] + p["I3"]                   # vdd 단자로 드는 전류(전류원 고정)
    else:
        i_dd = p["I12"] + p["IQ"] + max(iout, 0.0)
    i_ss = i_dd - iout                              # vss 단자에서 나가는 전류(KCL)
    A0 = (VDD - 0.0) * i_dd - (VSS - 0.0) * i_ss
    A1 = (VDD - AGND) * i_dd - (VSS - AGND) * i_ss
    B = VDD * i_dd - VSS * i_ss - vout * iout
    p_rl = d * d / RL
    C = B + p_rl
    return dict(kind=kind, delta_V=d, Vout=vout, Iout_uA=round(iout * 1e6, 3), A0_rail_ref0_uW=round(A0 * 1e6, 3),
                A1_rail_refagnd_uW=round(A1 * 1e6, 3), B_dut_diss_uW=round(B * 1e6, 3), C_all_sources_uW=round(C * 1e6, 3),
                P_RL_uW=round(p_rl * 1e6, 3), A0_minus_B_uW=round((A0 - B) * 1e6, 3), Vout_Iout_uW=round(vout * iout * 1e6, 3))


with open(OUT, "w", encoding="utf-8") as fh:
    for kind, p in CASES.items():
        for d in (-0.25, -0.1, 0.0, 0.1, 0.25):
            r = point(kind, p, d)
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(json.dumps(r, ensure_ascii=False))
