# 단계 B 보고서(GB4 달성가능성): folded_cascode

- 상태: ok (exit 0) [진단 모드: 단계 A 정지에도 계산]
- N_S(계수 예산): 13829760


## gain (뷰 transfer:0, 목표 n/a dB, 판정 no_target)
- 상한 합 n/a dB (+b n/a), 하한 추정 합(found) 119.3 dB, 미상 1
  - main ['out']: unknown A_max=n/a dB, b=n/a, found=119.3 dB, Π=61882838559595644226959851330968233907132396032000000, 사유=grid_product_over_budget

## 면적
- A_lb=0 m², 예산=1e-08 m², b_A=2.1e-15 m², 판정 not_excluded

## 헤드룸 창
- input vin_n: 폭 상한 1.762 V [0.03784, 1.8], certified, 판정 no_target, 소자 M1,M11
- input vin_p: 폭 상한 1.762 V [0.03784, 1.8], certified, 판정 no_target, 소자 M11,M2
- output out: 폭 상한 1.645 V [0.07568, 1.721], certified, 판정 no_target, 소자 M10,M3,M6,M8

## DOF
- free_dof: rank 13, 변수 39, 등식 13, 자유 변수 26

