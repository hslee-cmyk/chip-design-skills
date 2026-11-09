# dc_columns 합침 판단용 측정 (integ-it12 d759838a, E_B=40, 시간예산 600 s) -- 전부 실측/유도/추정 표기

## 표 1: 실측 reuse·시간 (FD = fd_jacobian 의 evaluate 호출 중 발생한 블록 호출)

| 회로 | 상태 | FD dc_columns calls | FD reuse비 | FD dc_widths calls/reuse비 | FD dc_currents calls/reuse비 | 전체(search) dc_columns calls/reuse비 | dc_columns compute 평균 ms (전체/FD) | 실행 wall s | search wall s | dc_columns compute 합 s | 합/실행 | 합/커널(size_and_seal 합) | 합/search |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | ok | 27 | 11% | 27/0% | 27/89% | 34/9% | 63.4 / 32.9 | 19.9 | 5.4 | 1.96 | 10% | 80% | 36% |
| current_reuse_telescopic_ota | ok | 0 | - | 0/- | 0/- | 40/0% | 498.0 / - | 73.6 | 20.8 | 19.92 | 27% | 98% | 96% |
| folded_cascode | ok | 59 | 17% | 59/0% | 59/83% | 66/15% | 170.9 / 135.6 | 46.0 | 17.8 | 9.57 | 21% | 79% | 54% |
| ngcc_3stage_ff | stage-B만 (a=review_needed b=review_needed) | - | - | - | - | - | - | 18.4 | - | - | - | - | - |
| nmcnr_amplifier | ok | 37 | 24% | 36/6% | 37/76% | 67/13% | 207.8 / 94.6 | 56.7 | 16.9 | 12.05 | 21% | 93% | 71% |
| pushpull_follower_buffer | ok | 29 | 21% | 29/0% | 29/79% | 40/15% | 29.3 / 10.9 | 9.6 | 1.8 | 1.00 | 10% | 73% | 54% |
| sf_pushpull_output_opamp | ok | 0 | - | 0/- | 0/- | 40/0% | 50.9 / - | 27.7 | 3.3 | 2.04 | 7% | 92% | 61% |
| two_stage_ota | ok | 48 | 25% | 48/6% | 48/81% | 53/23% | 64.3 / 36.4 | 37.2 | 7.7 | 2.64 | 7% | 79% | 34% |
| two_stage_ota_sf | ok | 40 | 25% | 40/5% | 40/80% | 48/21% | 70.0 / 42.2 | 135.3 | 7.7 | 2.66 | 2% | 76% | 34% |

(전체 dc_columns 행은 perf.blocks 정본과 같은 값인지 아래 표 3에서 대조. 'search' = find_front 구간. 커널 = kernel.size_and_seal 시간 합(DC 커널만, ss 지표 제외).)

## 표 2: 열 종류별 FD (실측)

| 회로 | 1회 야코비안 열 수 (current/ln_idu/y/L/total) | θ 전류 열 비율 (1회, 실측) | FD 호출 수 | 누적 명목 열 수 (current/total) | FD evaluate 요청 current/전체 | 커널 실행 current/전체 | current 열의 dc_columns calls/reuse/compute | 다른 열(ln_idu,y,L)의 dc_columns reuse/calls |
|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 1/3/2/3/9 | 1/9 = 11% | 9 | 9/78 | 8/73 | 3/27 | 3/3/0 | 0/24 |
| current_reuse_telescopic_ota | 0/0/0/0/0 | 0/0 = - | 0 | 0/0 | 0/0 | 0/0 | 0/0/0 | 0/0 |
| folded_cascode | 5/9/3/9/26 | 5/26 = 19% | 5 | 25/130 | 25/146 | 10/59 | 10/10/0 | 0/49 |
| ngcc_3stage_ff | stage-B만 (a=review_needed b=review_needed) | | | | | | | |
| nmcnr_amplifier | 8/12/2/12/36 | 8/36 = 22% | 2 | 16/72 | 18/74 | 9/37 | 9/7/2 | 2/28 |
| pushpull_follower_buffer | 3/5/0/6/14 | 3/14 = 21% | 5 | 15/70 | 15/71 | 6/29 | 6/6/0 | 0/23 |
| sf_pushpull_output_opamp | 0/0/0/0/0 | 0/0 = - | 0 | 0/0 | 0/0 | 0/0 | 0/0/0 | 0/0 |
| two_stage_ota | 3/5/2/5/16 | 3/16 = 19% | 6 | 18/96 | 18/96 | 9/48 | 9/9/0 | 3/39 |
| two_stage_ota_sf | 4/6/2/6/19 | 4/19 = 21% | 5 | 20/95 | 20/100 | 8/40 | 8/8/0 | 2/32 |

(1회 야코비안 = 해당 회로 첫 fd_jacobian 호출의 변수 수; 이후 호출에서 변수 수가 같은지는 누적 명목/호출 수로 확인. 고정(skip) 열은 평가 없음.)

## 표 3: 유도 -- 합친 DC 블록의 예상 손실 (유도값, 실측 아님)

식 A = (FD 중 current 열에서 dc_columns 가 reuse/graft/replay 되던 횟수 R_cur) × (dc_columns compute 1회 평균 ms, 전체 평균). 식 B = (current 열의 실제 커널 실행 수 K_cur) × 같은 평균. 둘 다 '그 열들이 전부 compute 로 바뀐다'는 가정.

| 회로 | R_cur | K_cur | 평균 ms (전체) | A: 추가 s | A/실행 wall | B: 추가 s | B/실행 wall | perf.blocks dc_columns (calls/reuses/computes) 정본 |
|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 3 | 3 | 63.4 | 0.19 | 1% | 0.19 | 1% | 34/3/31 |
| current_reuse_telescopic_ota | 0 | 0 | 498.0 | 0.00 | 0% | 0.00 | 0% | 40/0/40 |
| folded_cascode | 10 | 10 | 170.9 | 1.71 | 4% | 1.71 | 4% | 66/10/56 |
| ngcc_3stage_ff | stage-B만 (a=review_needed b=review_needed) | | | | | | | |
| nmcnr_amplifier | 7 | 9 | 207.8 | 1.45 | 3% | 1.87 | 3% | 67/9/58 |
| pushpull_follower_buffer | 6 | 6 | 29.3 | 0.18 | 2% | 0.18 | 2% | 40/6/34 |
| sf_pushpull_output_opamp | 0 | 0 | 50.9 | 0.00 | 0% | 0.00 | 0% | 40/0/40 |
| two_stage_ota | 9 | 9 | 64.3 | 0.58 | 2% | 0.58 | 2% | 53/12/41 |
| two_stage_ota_sf | 8 | 8 | 70.0 | 0.56 | 0% | 0.56 | 0% | 48/10/38 |

## 표 4: 블록 안 반복 회차 추정 입력 (추정: 손가락 규칙 m=ceil(W/w_hi), w_f=W/m, w_hi=기준 슬라이스 W-bin 위 끝)

| 회로 | input_dc | 입력 포트 | W4 뿌리 입력 포트 | 판정 | front 점 수 / 사용 점 | 슬라이스 바뀌는 쓰기 소자 (점별 바뀜/쓰기수) | 슬라이스 바뀌는 종속 소자 (점별 바뀜/종속수) | 기준 슬라이스 (nmos/pmos w_um, bin) |
|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | pending | vin | vin | W4 뿌리 예 | 1 (front, cache 봉인 33) / 1 | 3/3 | 0/0 | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| current_reuse_telescopic_ota | pending | Vim,Vip | Vip | W4 뿌리 예 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 0) / 0 |  |  | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| folded_cascode | pending | vin_n,vin_p | vin_p | W4 뿌리 예 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 54) / 5 | 4/9 4/9 4/9 4/9 4/9 | 2/4 1/4 3/4 1/4 1/4 | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| ngcc_3stage_ff | stage-B만 (a=review_needed b=review_needed) | pending | Vinn,Vinp / Vinp | W4 뿌리 예 (단계 B s1.snapshot 의 dc_writer 에서) | - | - | - | - |
| nmcnr_amplifier | pending | Vin_n,Vin_p | Vin_p | W4 뿌리 예 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 37) / 5 | 0/12 0/12 0/12 0/12 0/12 | 0/3 0/3 0/3 0/3 0/3 | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| pushpull_follower_buffer | net | vin | - | W4 뿌리 아니오 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 37) / 5 | 5/5 5/5 4/5 4/5 4/5 | 0/1 0/1 0/1 0/1 0/1 | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| sf_pushpull_output_opamp | net | vin_n,vin_p | - | W4 뿌리 아니오 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 0) / 0 |  |  | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| two_stage_ota | pending | vin_n,vin_p | vin_p | W4 뿌리 예 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 51) / 5 | 1/5 1/5 1/5 1/5 1/5 | 1/2 1/2 0/2 0/2 0/2 | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
| two_stage_ota_sf | pending | vin_n,vin_p | vin_p | W4 뿌리 예 | 0 (sctx.cache sealed (front 비어 있음), cache 봉인 40) / 5 | 4/6 5/6 4/6 4/6 4/6 | 1/3 1/3 1/3 1/3 1/3 | nmos 5.00 um [3.00,5.00]; pmos 5.00 um [3.00,5.00] |
