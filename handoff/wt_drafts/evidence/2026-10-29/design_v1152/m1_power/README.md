# M-1 DUT 전력 정의 후보 수치 (design v1.15.2 검증 M-1·재판정 P7) -- 정의 결정은 계획 v6.38.4 몫

- 2026-10-29, design 작성자. 손계산 toy(엔진 무관). 재현: `C:/Python314/python.exe m1_power_toy.py` → `m1_power_toy.out.jsonl`(덮어씀).
- nmcnr 연결 꼴: vdd 1.8 V·vss 0 V(넷리스트 0 V)·agnd 0.9 V, 측정 부하 RL 25 kΩ(Vout–agnd), 출력단 class-A(M301 nmos 구동·M302 pmos 전류원). 전류(I12 20 µA, I3 40 µA, push-pull IQ 20 µA)는 비교용 가정값 -- 상수 아님.
- 물리 사실(Tellegen): DUT **모든** 단자(vdd·vss·Vout)의 Σ V·I = DUT 소산(기준 전위 무관). 레일 단자만의 합 = DUT 소산 + 출력 포트 전력 (V_out − V_0)·I_out(기준 V_0 의존).

| 출력 DC | class-A (가) 레일 합·기준 0 V | class-A (나) DUT 소산 | push-pull (가) | push-pull (나) | P_RL | (가) − (나) = V_out·I_out |
|---|---|---|---|---|---|---|
| 0.65 V | 108.0 µW | 114.5 | 72.0 | 78.5 | 2.5 | −6.5 |
| 0.80 V | 108.0 | 111.2 | 72.0 | 75.2 | 0.4 | −3.2 |
| 0.90 V | 108.0 | 108.0 | 72.0 | 72.0 | 0 | 0 |
| 1.00 V | 108.0 | 104.0 | 79.2 | 75.2 | 0.4 | +4.0 |
| 1.15 V | 108.0 | 96.5 | 90.0 | 78.5 | 2.5 | +11.5 |

- 기준을 agnd로 옮긴 레일 합(A1)은 모든 공급원 전력(DUT 소산 + P_RL, C 열)과 같다 -- 레일 합은 기준 선택에 따라 다른 양이 된다.
- 판정 가능한 toy 셋(정의와 무관): class-A에서 (가) 불변, push-pull에서 Δ(가) = V_DD·ΔI_DD, 항등식 (가) − (나) = V_out·I_out.
- 검증자 독립 toy(`../../design_v1152_validation/qpw1/`)와 같은 결론.
