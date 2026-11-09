"""plan v6.38.4 P7 실측 -- DUT 전력 정의 비교(손계산, KCL·Tellegen 항등식). 엔진·SPICE 미사용.

정의:
  (가) 레일 단자 합  P_rail(ref) = Σ_{k ∈ 레일 DUT 단자} (V_k − V_ref)·I_k   (I_k = 단자로 DUT에 드는 전류)
       ref = 넷리스트 0 V(지금 DEC-78 해석 -- oracle OP-11 `Σ_{레일 ∖ 기준 레일} V·I`와 같음)와 ref = 측정 부하 귀환 넷(agnd) 둘을 잰다.
  (나) DUT 소산    P_diss = Σ_{DUT 모든 단자} V_j·I_j  (KCL Σ I_j = 0 이라 ref 불변 -- Tellegen)
  (다) 전원 전체   P_src = 모든 전압원(레일 원 + agnd 원 + 입력 원)이 내는 전력 = P_diss + P_bench(측정 부하 소산) -- ref 불변
항등식 점검: P_rail(0) − P_diss = − Σ_{비레일 DUT 단자} V_j·I_j.

회로 셋:
 (1) nmcnr -- 레일 vdd 1.8 / vss 0 / agnd 0.9(spec supplies_v), RL 25 kΩ Vout–agnd(측정 부하), 출력단 class-A(M302 전류원 + M301 CS).
     동작점 = 손분석 파일럿 `wt/_pilot_nmcnr/design_point.json`(손계산 설계점, 판정 기록 아님 -- 소자 전류 ID·Vout 그대로 읽음).
     추가로 Vout을 agnd(0.9 V)로 둔 점(I_out = 0, 논문 측정 구성 -- 단위 이득 되먹임에서 출력 DC ≈ 입력 = 접지)을 같은 소자 전류로 잼(M301 = M302 + I_in).
 (2) class-A 대표 two_stage_ota -- 레일 vdd 1.8 / gnd 0, 측정 부하 = CL만(DC 전류 0). 소자 전류는 임의 손계산 값(꼬리 20 µA, 2단 100 µA) --
     항등 확인용(어느 값이든 결론 같음: 비레일 단자 DC 전류 0 -> 세 정의 같음).
 (3) common_gate -- 입력 포트 vin이 M1 drain·M2 source(채널 단자) -> 입력 원 DC 전류 I_in = I_M1 − I_M2. 임의 손계산 값 두 점.
출력: out.jsonl
"""
import json, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out.jsonl")
PILOT = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/_pilot_nmcnr/design_point.json"
rows = []


def emit(r):
    rows.append(r)
    print(json.dumps(r, ensure_ascii=False))


# (1) nmcnr
dp = json.load(open(PILOT, encoding="utf-8"))
ID = {k: v["ID"] for k, v in dp["devices"].items()}
net = {"M101": ("vdd", "NodeTail"), "M108": ("vdd", "NodeM1"), "M109": ("vdd", "NodeM2"), "M201": ("vdd", "NodeC"),
       "M202": ("vdd", "NodeS2"), "M302": ("vdd", "Vout"),
       "M104": ("NodeF1", "vss"), "M105": ("NodeF2", "vss"), "M203": ("NodeC", "vss"), "M204": ("NodeS2", "vss"), "M301": ("Vout", "vss")}
VDD, VSS, AGND, RL = 1.8, 0.0, 0.9, 25e3
for label, vout in (("pilot_point", dp["nodes"]["Vout"]), ("vout_at_agnd", AGND)):
    i_vdd = sum(ID[m] for m, (a, b) in net.items() if a == "vdd")
    i_out_into_dut = (AGND - vout) / RL                 # RL 을 거쳐 agnd -> Vout -> DUT 로 드는 전류(양 = DUT 로 듦)
    i_vss = i_vdd + i_out_into_dut                       # KCL: DUT 로 드는 전류 합 0 -> vss 단자에서 나가는 전류
    # 단자 전류(DUT 로 드는 방향): vdd +i_vdd, vss −i_vss, Vout +i_out_into_dut
    p_rail0 = (VDD - 0.0) * i_vdd + (VSS - 0.0) * (-i_vss)
    p_rail_agnd = (VDD - AGND) * i_vdd + (VSS - AGND) * (-i_vss)
    p_diss = VDD * i_vdd + VSS * (-i_vss) + vout * i_out_into_dut
    p_bench = (vout - AGND) ** 2 / RL
    p_src = p_diss + p_bench
    emit({"circuit": "nmcnr_amplifier", "point": label, "Vout_V": round(vout, 4), "I_vdd_uA": round(i_vdd * 1e6, 3),
          "I_vss_uA": round(i_vss * 1e6, 3), "I_out_into_DUT_uA": round(i_out_into_dut * 1e6, 3),
          "P_rail_ref0_uW": round(p_rail0 * 1e6, 3), "P_rail_refagnd_uW": round(p_rail_agnd * 1e6, 3),
          "P_diss_uW": round(p_diss * 1e6, 3), "P_bench_RL_uW": round(p_bench * 1e6, 3), "P_src_uW": round(p_src * 1e6, 3),
          "identity_P_rail0_minus_P_diss_uW": round((p_rail0 - p_diss) * 1e6, 3),
          "minus_Vout_Iout_uW": round(-vout * i_out_into_dut * 1e6, 3),
          "pilot_power_w_field": dp.get("power_w")})

# (2) two_stage_ota class-A, CL only
for itail, i2 in ((20e-6, 100e-6),):
    i_vdd = itail + i2; i_gnd = i_vdd
    for ref in (0.0, 0.9):
        p_rail = (1.8 - ref) * i_vdd + (0.0 - ref) * (-i_gnd)
        emit({"circuit": "two_stage_ota", "ref_V": ref, "I_vdd_uA": i_vdd * 1e6, "P_rail_uW": round(p_rail * 1e6, 3),
              "P_diss_uW": round(1.8 * i_vdd * 1e6, 3), "note": "출력 DC 전류 0(CL만), 입력 gate -- 비레일 단자 전류 0"})

# (3) common_gate: vin = M1 drain·M2 source; vdd -> M3 -> vout -> M2 -> vin -> M1 -> gnd
for i1, i3, vin in ((100e-6, 100e-6, 0.4), (120e-6, 100e-6, 0.4)):
    i_in = i1 - i3                                       # 입력 원이 vin 으로 넣는 전류
    p_rail0 = 1.8 * i3
    p_diss = 1.8 * i3 + vin * i_in
    emit({"circuit": "common_gate_amplifier", "I_M1_uA": i1 * 1e6, "I_M3_uA": i3 * 1e6, "Vin_V": vin, "I_in_uA": round(i_in * 1e6, 3),
          "P_rail_ref0_uW": round(p_rail0 * 1e6, 3), "P_diss_uW": round(p_diss * 1e6, 3),
          "P_rail_ref_vin_uW": round(((1.8 - vin) * i3 + (0 - vin) * (-i1)) * 1e6, 3)})

with open(OUT, "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
