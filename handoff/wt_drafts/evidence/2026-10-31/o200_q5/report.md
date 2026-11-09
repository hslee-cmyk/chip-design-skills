# O-200 Q-O200-5 사전 실측 6항목 (2026-10-31)

측정 agent 보고를 오케스트레이터가 옮겨 적음(하위 agent 보고 파일 쓰기는 하네스가 거부). 스크립트·결과 파일은 이 폴더(`q5_*.py`, `q5_*.jsonl`, `q5_*.txt`, `q5_spice_band_meta.json`). 엔진 출력·SPICE: `C:/Users/HSLEE/AppData/Local/Temp/q5_1bd9a6b5/`. 조건: master e1c455f8, library 경로 그대로(inplace), LUT `resolve_lut_location` sha 대조, 엔진 소스 수정 0, git 쓰기 0.

## 1. S_d 절단 폭·t* 이동
(a) K10 하네스(115 S·F 소자): tol 셀값 중앙 1.107 mV·최대 32.5 mV, tol/VDS 중앙 1.6e-3·최대 4.0e-2. 띠 안 노드 설정 ID 1e-5 0.8 %, 1e-3 2.4 %. **t* 바뀐 설정 0**(P2·D2P, (가)(나), ID 5칸, 예산 3경우) -- 띠 노드는 강반전 끝, t*는 S_d 아래 끝. 영향: S_d 빈 설정 2(F nfet), 면적 실행 가능 t* 잃음 ID 1e-3 full 12(F pfet)·share 4(F nfet). 파일 `q5_k10_lut.jsonl`, `q5_k10_agg.txt`.
(b) 엔진 헤드룸 행(8회로 252행): Σtol = 자기 tol 하나(경로 Σ_{j≠k} tol = 0 -- as-built 엣지 비용 tol 최솟값 규칙, design 41 §6.2 식과 다름 = 재작성 범위). Σtol 중앙 1.95~9.04 mV, Σtol/예산 최대 3.0e-2, gm/ID 하한 활성 10행·이동 ≤ 4.5 %.
(c) 출발점 칸 0 theta: tol 빼면 8/8 회로 이동, 최대 |Δln IDu| sf_pushpull 0.391(전류 −9.7 %), two_stage_ota 0.097(Cc −3.9 %), common_gate·pushpull 0.068, two_stage_ota_sf 0.056, nmcnr 0.015, current_reuse 0.006, folded 1.4e-6. **이동 전부 iv_domain 몫**(VDS 탐침 = VDSAT + tol을 LUT VDS 격자 37.5 mV 위로 올림 -- tol 몇 mV가 한 칸 이동). 대조 결정성 8/8 비트 동일. 파일 `q5_engine_*.jsonl`, `q5_engine_agg.txt`.

## 2. pmos w_key 1000 꼬리 셀 32.5 mV
위치 (L 0.15·0.18 µm, VDS 1.8 V) -- 앵커 2개 PDK bin, 중점 0.165 µm L 선형 보간 오차를 앵커 셀에 넣은 셀 구성값(같은 셀 VDSAT 자체 LOO 0.80~0.93 mV). 엔진 pmos 1029행(23소자) 모두 이 bin, 행 tol 9.4~26.2 mV(중앙 16.2), 467행은 L이 앵커와 같아 L 보간 없음. **32.5 mV 셀 도달 0**(최대 VDS 1.377 V). 점 국소 L 오차 중앙 0.074 mV -- 행 tol은 국소 오차의 중앙 14배. 파일 `q5_tail_reach.txt`.

## 3. 봉인 7 띠 안 행
find_front 예산 40: **띠 안 1/2413**(nmcnr M109 pmos, 여유 +3.477 mV, tol 10.19 mV), 위반 4. 표본 6/13 회로(current_reuse·sf_pushpull 층 0 출발점 실패, cnr·erfc·r2r stopped, ngcc·rfc review_needed).

## 4. 띠 안 점 SPICE
b74(36소자) 띠 안 0. 새 SPICE 15점(띠·위반 5 + 대조 10; ngspice-46 단일 소자, LUT DUT 기하 w 5 µm, 같은 sha 모델): **띠 안 M109 SPICE 포화(VDS − @m[vdsat] = +3.567 mV) -- 봉인 7만 거부.** 위반 4점 SPICE도 비포화(부호 같음), 대조 10점 포화. 파일 `q5_b74_band.*`, `q5_spice_band.jsonl`.

## 5. 정의 동일성
같은 양: `assets/sky130_lut_sweep.py:35·92·238`(`@m...[vdsat]`), 슬라이스 생성기 `lut_data/sky130_lut_v2/verification/slices_vdsat/sky130_dc_width_slices.py:31-32·61·167`, oracle `tools/spice_oracle/oracle_netlist.py:53·124-126`·`oracle_compare.py:276`. 모델 sha PDK 선언 = LUT 메타 = 디스크. 같은 op 차: 15점 −0.054~+0.544 mV(|차|/tol ≤ 0.28), b74 −0.020~+0.966 mV(≤ 0.355). 조건: SPICE finger 폭 = 슬라이스 폭.

## 6. tol_VDsat 독립 재계산
계획 P:635·N3.6 표 7행대로 LUT npz에서 계산: 32/32 슬라이스 864칸 엔진과 차 0.0 V. 단 중점 오차를 앵커 셀에 넣는 구성일 때만 일치(안 넣으면 w_key 1000만 다름: pmos 최대 31.7, nmos 5.3 mV). 원래 취지와 다름 후보: 계획 '점 사이 쿼리에 L 방향 값'인데 엔진은 L 보간 없는 앵커 조회에도 적용(Q-T0 셀 구성과 같은 축). 파일 `q5_tolvdsat_indep.jsonl`, `q5_tolvdsat_top_pmos1000.jsonl`.

## 물리 판단 (측정 agent)
물리 포화 경계 = VDS = VDSAT(SPICE 합격 기준 N3.6 (ii) 여유 0, oracle `vds − vdsat`, 띠 안 점 SPICE 포화). 띠 폭 tol_VDsat = 수치 분해능(LUT LOO 셀 최댓값, 꼬리는 셀 구성값; 실제 엔진−SPICE 차 ≤ 0.97 mV < tol). 정의 동일성 관문 성립 → `+tol_VDsat` 띠는 물리 경계를 분해능만큼 옮긴 꼴(O-200 위반 꼴). 영향: 봉인 7 SPICE 포화 점 거부 1/2413, K10 t* 0, 엔진 출발점 iv_domain 최대 Δln IDu 0.391, 헤드룸 행 하한 ≤ 4.5 %.

## 한계
출발 구간 표본 8/13, 봉인 7 표본 6/13 회로. SPICE는 단일 소자 대조(회로 .op는 b74 세 회로뿐, 띠 안 점 없음). 측정 2 국소 오차는 최근접 격자점 근사. K10 하네스는 VDS ≥ 0.3 V 격자만.
