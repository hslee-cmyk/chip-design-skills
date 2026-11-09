# WB-1 세 질문 실측 (2026-11-06)

자리: worktree `wt/20261105-wb1-c` 머리 `7c038c89`를 복제한 `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_q3/clone`에서 실행(엔진·test 변경 0). base = `la1s_wb1_code5/base`(`2ee99d5d`). 스크립트·원 출력 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_q3/`. ngspice 0, 전체 test 0. 코드 작성자 보고는 가설로만 썼다. 엔진 읽기 용도 = 외부 사실과 재작성 범위(원칙 8).

## 질문 1 (중간 기록, 끝에 결론 절이 따로 있다)

측정 파일: `q1_ota.py`→`q1_ota.txt`, `q1_asis.py`→`q1_asis.txt`.

- 실현 평가 servo(`two_stage_ota` i=12, j=5, 탐색 손가락): 봉인 3 최대 비 0.003(3.7e-12 A 대 1.36e-9 A), Newton 1회, 비기준 슬라이스 tol_V 3.6~40 µV 그대로 통과. µV tol은 재풀이 뒤 문제가 아니다.
- 레이아웃 뒤 재평가(`evaluate(geometry=)`): 노드 재풀이 없음. 20회 전부 봉인 3 실패(비 1.97~173.7), 마지막 19회 제외 후 `infeasible_after_layout`. 종속 소자 ID 상대 오차 최대 −28 %(M1), −24 %(M7).
- 같은 레이아웃 기하 7개를 W′ 고정 KCL 재풀이로 넣은 평가: 7/7 봉인 통과, 봉인 3 최대 비 0.031, 6/7 제약 c ≥ 0(나머지 1개 = `pm_ss_deg` c = −0.097, spec 판정).
- 단일 입력 toy(`test_front_points_inside_area_budget`, r = 0.67, tol_V 7.8 mV = 기준 슬라이스): 지금 코드 = 봉인 3 비 2.95로 잃음. 입력 고정 + KCL 재풀이 = `newton_line_search` 비수렴. 단일 입력 servo = 봉인 통과, ΔV_in −23 mV.
