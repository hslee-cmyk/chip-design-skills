# O-168 사실 실측 -- 입력 포트 자기동형 궤도·W4 뿌리, DEC-105 (1)·(10) 조건부 전제 (계획 v6.38.3 작성용)

- 작성: 2026-10-28, 계획 v6.38.3 작성자(검증은 별도 agent). 엔진은 읽기·import만(O-165 (b) -- 엔진 밖 사실·재작성 범위 용도).
- 엔진: `wt/integ-it12` `d759838a`(integ/it12 = IT-1+IT-2 통합 브랜치, master 미병합 -- `git merge-base --is-ancestor integ/it12 master` 거짓). `E` = `skills/analog-gmid-design/gmid_engine`, `L` = `skills/analog-gmid-design/assets/library`.
- 스크립트(엔진 밖): `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/o168/measure.py`(궤도·쓰기 계획), `measure2.py`(found_db), `measure3.py`(θ 저항·영점 상쇄). 결과 jsonl 같은 폴더 `out.jsonl`·`out2.jsonl`·`out3.jsonl`. 실행: `run_stage_a` → `build_kernel_context`(쓰기 계획) / `run_stage_b`(달성가능성 보고) / `build_search_context`(θ 스키마), `OPENBLAS_NUM_THREADS=1`.
- heldout 회로는 재지 않았다.

## 1. 입력 포트 자기동형 궤도(`graph/s1: orbits`, `E/graph/automorphism_orbits.py`)와 W4 뿌리(`node.dc_writer`, `E/sizing/writer_plan.py`)

| 회로 | spec `input_dc` | 입력 포트 | 입력 포트 노드 궤도 같음? | 입력 gate 소자(궤도) | 입력 포트 writer | 입력 포트인 W4 뿌리 수 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | pending SP-2 | vin (1개) | 해당 없음 | 없음(vin = M2 source) | vin = W4 `free_window`(y 키 vin) | 1 |
| current_reuse_telescopic_ota | pending SP-2 | Vip, Vim | **같음**(95) | Vip: M1a·M4a / Vim: M1b·M4b (M1a~M1b, M4a~M4b 같은 궤도) | Vip = W4 뿌리, Vim = W2 `vgs_gate`(M4b, known Vy) | 1 |
| folded_cascode | pending SP-2 | vin_p, vin_n | **다름**(24/25) | M2 / M1 (다른 궤도) | vin_p = W4 뿌리, vin_n = W2 `vgs_gate`(M1, known tail) | 1 |
| ngcc_3stage_ff | pending SP-2 | Vinp, Vinn | **다름**(27/28) | M2 / M1 (다른 궤도) | Vinp = W4 뿌리, Vinn = W2 `vgs_gate`(M1, known TAIL) | 1 |
| nmcnr_amplifier | pending SP-2 | Vin_p, Vin_n | **다름**(33/34) | M103 / M102 (다른 궤도) | Vin_p = W4 뿌리, Vin_n = W2 `vgs_gate`(M102, known NodeTail) | 1 |
| pushpull_follower_buffer | net agnd | vin (1개) | 해당 없음 | M3·M4 | vin = W2 `input_dc`(F) | 0 |
| sf_pushpull_output_opamp | net agnd | vin_p, vin_n | 다름(45/46) | M1 / M2 | 둘 다 W2 `input_dc`(F) | 0 |
| two_stage_ota | pending SP-2 | vin_p, vin_n | **다름**(15/16) | M2 / M1 (다른 궤도) | vin_p = W4 뿌리, vin_n = W2 `vgs_gate`(M1, known CS) | 1 |
| two_stage_ota_sf | pending SP-2 | vin_p, vin_n | **다름**(16/17) | M2 / M1 (다른 궤도) | vin_p = W4 뿌리, vin_n = W2 `vgs_gate`(M1, known CS) | 1 |

요약:
- (a) 입력 DC 미선언·입력 포트 2개 6회로 가운데 두 입력 포트가 같은 궤도인 회로 = **1**(current_reuse, 차동 출력 -- 비자명 소자 궤도 22개). 나머지 **5**(folded·ngcc·nmcnr·two_stage·two_stage_sf)는 단일 출력(미러 부하·출력단)이라 비자명 소자 궤도 0, 두 포트가 다른 궤도다 → K-3·O-13 (1) (가)의 전제 '대칭이면 자기동형 묶음과 중복'은 6회로 중 5회로에서 성립하지 않는다(묶음 자체가 없음).
- (b) W4 뿌리: 미선언 6회로 모두 입력 포트인 W4 뿌리 = 1(두 포트가 같은 G_vgs 성분, 성분이 F에 닿지 않음). 둘째 포트는 입력 MOS의 `vgs_gate`(W2)가 꼬리 넷에서 쓴다 → V(둘째 포트) − V(뿌리 포트) = VGS(둘째 입력 MOS) − VGS(뿌리 쪽 입력 MOS)가 θ의 함수 = **입력 쪽 차동 DC가 설계 자유도로 남는다**(H 판정 two_stage −319 mV(입력 1.393 V·1.074 V -- `u128_value_table.md` F10)·folded +71/−118 mV·nmcnr −141 mV·two_stage_sf +27 mV -- `u128_value_table.md` F10).
- O-72 (2) 정지 분기 `input_port_multiple_roots`(`E/sizing/writer_plan.py:29`, `E/sizing/s2_values.py:94`): 발동 0(9회로 모두 입력 W4 뿌리 ≤ 1).
- 묶음(입력 포트 한 점) 뒤 예상(쓰기 계획 손 유도 -- 실측 아님, card 0이 엔진으로 잰다): 두 포트가 같은 성분인 6회로는 순환수 +1(같은 성분의 두 점을 한 점으로 묶으면 순환수가 1 는다). 입력 MOS 쌍이 같은 kind·같은 source(꼬리 넷)인 회로는 그 둘째 입력 MOS가 v0 `parallel_vgs` 종속(VGS 같음); current_reuse는 옛 ΔV 소거 v1 고리(VGS1a − VGS1b = VGS4a − VGS4b) 하나가 평행 쌍 둘(M1a∥M1b, M4a∥M4b)로 나뉜다.

- (검증 1 M-1 추가 실측) topology `ports` 역할: 차동 입력쌍(`differential_input_p`·`_n` 각 하나) 7회로(입력 DC 미선언 6 + 선언 sf_pushpull), `single_ended_input` 하나 2회로(common_gate·pushpull_follower_buffer), 그 밖의 다중 입력 0.
## 2. DEC-105 (1) 조건부 전제 -- 블록 `found_db`(단계 B 보고 `achievability/gain/blocks[*]`)

| 회로 | gain 제약 선언 | 블록(구성원 앞부분) found_db | 뷰 안 found_db 없는 블록 |
|---|---|---|---|
| common_gate_amplifier | 있음 | {M2, M3} 53.4 | 0 |
| current_reuse_telescopic_ota | 있음(SF-1 범위 5가 `gain_ss_db ≥ 54` 삭제 예정 -- O-132·O-133) | {M15, M16} None / {M10, M17, …} 80.0 / {M25, M26} None | 2/3 |
| folded_cascode | 있음 | {M1, M10, …} 119.3 | 0 |
| ngcc_3stage_ff | 있음(2행) | 68.5 / 51.7 / 71.5 (ff 68.0·50.3) | 0 |
| nmcnr_amplifier | 있음(2행) | {M101, …} 100.7 / {M201, …} 73.0 / {M301, M302} None | 1/3 |
| pushpull_follower_buffer | **없음** | {M1~M4} −1.57 | 0(비활성 회로) |
| sf_pushpull_output_opamp | 있음 | {M1, M10, …} None / {M18, M19, M21, M22} −1.57 | 1/2 |
| two_stage_ota | 있음 | 61.2 / 67.7 | 0 |
| two_stage_ota_sf | 있음 | 61.2 / 67.7 / {M8} −0.66(certified) | 0 |

- found_db = 좌표 상승 하한 추정, 기준점을 못 찾으면 None(`E/metrics/CONTRACT.md:1087`). None 블록 4개는 모두 기준점 미발견이고 구성원에 영점 상쇄 셀(M16·M26·M301 -- §3)·첫 단 입력쌍(sf block0)이 있다 = 이득을 내는 블록이다(따름단 아님; 따름단 블록은 found_db가 −1.57 dB로 있음).
- gain 선언 8회로 중 found_db가 뷰 전부에 있는 회로 5(common_gate·folded·ngcc·two_stage·two_stage_sf), 없는 블록이 있는 회로 3(current_reuse·nmcnr·sf_pushpull). SF-1 뒤(current_reuse gain 삭제) 영향 회로 = nmcnr·sf_pushpull 2.

## 3. DEC-105 (10) 조건부 전제 -- `engine: true` 수동소자와 θ 상자

`engine: true` 소자(spec `human.element_values`) 18개 = 커패시터 9(current_reuse Cc1·Cc2, ngcc Cm1·Cm2, nmcnr Cm1·Cm2, sf_pushpull Cc, two_stage Cc, two_stage_sf Cc), 저항 9(current_reuse R1·R2·Rz1·Rz2, nmcnr Rm, sf_pushpull R1a·R1b·R1c, two_stage Rz).

| 종류 | 소자 | θ 스키마 성분(`graph/kernel: theta_schema`) | spec θ 상자 | 상자 출처 |
|---|---|---|---|---|
| 커패시터 9 | 위 9개 | `capacitance` 9 | 9 모두 [1e-13, 1e-11] F | 모두 사용자 결정 2026-10-08 '10번'(같은 값·같은 출처) |
| DC 경로 저항 5 | current_reuse R1·R2, sf_pushpull R1a·R1b·R1c | `resistance` 5 | current_reuse [1e4, 1e7] Ω, sf_pushpull [1e3, 1e6] Ω | 사용자 결정 2026-10-08 '8번'(역할별로 다른 값 -- CMFB 감지 / self-bias 캐스코드) |
| 보상 저항 4 | current_reuse Rz1·Rz2, nmcnr Rm, two_stage Rz | **as-built θ 아님**(옛 DEC-92 (3)(a) 구조 규칙 고정값 판정 -- 승인 DEC-92 (3)·O-33 (10)으로는 θ이고 1/Σgm은 출발값; 아래 사실은 구조 규칙 셀 집합 S가 정의된다는 뜻으로만 씀; `zero_cancel` 4개 모두 reason None -- 영점 상쇄 구조 규칙 R = 1/Σ`dc_gm`, `E/metrics/CONTRACT.md:629-642`) | 없음 | 해당 없음(값 = 법칙이 정함) |

- (v6.38.3 둘째 커밋 정정 -- 검증 1 H-1) as-built는 보상 저항 4개를 구조 규칙 고정값으로 두어 θ가 아니지만, 승인 규칙(DEC-92 (3)·O-33 (10))으로는 θ이고 상자 출처가 필요하다(spec 상자 0, as-built 출처 = 실행 설정 재정의뿐). θ 저항 5개는 모두 회로별 사용자 선언 상자가 있고 값이 역할별로 달라 공통 값이 없다. (옛 문장 "θ 변수가 아니다(영점 상쇄 법칙이 값을 정함)"은 철회 -- R = 1/gm은 법칙이 아니라 영점 위치 선택.)
- as-built: θ 저항·영점 상쇄 실패(`ss_resistance`) 저항에 상자 선언이 없으면 `theta_resistance_bounds_undeclared` 거부(`E/search/search_domain.py:105-110`); 실행 설정 `SearchSettings.resistance_bounds_ohm`·`capacitance_bounds_f`가 None이 아니면 그 종류 모든 원소에 그 상자를 쓴다(`E/search/CONTRACT.md:72` -- 둘째 선언 자리).

## 4. 끝 점검

- `git -C wt/integ-it12 status --short`: 빈 출력(실측 직후 확인).
