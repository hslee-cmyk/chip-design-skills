# 단계 B 보고서(GB4 달성가능성): two_stage_ota

- 상태: ok (exit 0) [진단 모드: 단계 A 정지에도 계산]
- N_S(계수 예산): 13829760


## gain (뷰 transfer:0, 목표 57 dB, 판정 undetermined)
- 상한 합 n/a dB (+b n/a), 하한 추정 합(found) 128.9 dB, 미상 2
  - main ['O1']: unknown A_max=n/a dB, b=n/a, found=61.17 dB, Π=17094434585424729422400, 사유=grid_product_over_budget
  - main ['OUT']: unknown A_max=n/a dB, b=n/a, found=67.72 dB, Π=1867795524, 사유=grid_product_over_budget

## 면적
- A_lb=5e-11 m², 예산=1.5e-08 m², b_A=2.1e-15 m², 판정 not_excluded

## 헤드룸 창
- input vin_n: 폭 상한 1.762 V [0.03784, 1.8], certified, 판정 no_target, 소자 M1,M5
- input vin_p: 폭 상한 1.762 V [0.03784, 1.8], certified, 판정 no_target, 소자 M2,M5
- output OUT: 폭 상한 1.723 V [0.03784, 1.76], certified, 판정 no_target, 소자 M6,M7

## DOF
- free_dof: rank 7, 변수 23, 등식 7, 자유 변수 16

