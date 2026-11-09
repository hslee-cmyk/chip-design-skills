# design 40/41 v1.12 (IT-1·IT-2) 독립 design 검증 (e721dfc2) -- 오케스트레이터가 agent 보고 원문을 옮김(agent에 Write 없음)

판정: 수정 필요 (완성도 78/100). 차단 C1·M1, 나머지 문언·인터페이스 보강.

| # | 심각도 | 위치 | 문제 | 최소 수정 |
|---|---|---|---|---|
| C1 | Critical | 41 §4.7-2 688, §4.7-4 2 (719), §4.7-7 R1 (754) | 다듬은 창이 뿌리 아래 끝 해의 포트 전압을 그대로 lo로 써 s_p<0 포트에서 lo>hi. O-49 P2(다듬은 창도 두 끝 전압 [min,max])·41 P (a) test와 충돌 | lo = max(min(v_lo,v_hi), rail_lo), hi = min(max(v_lo,v_hi), rail_hi); 끝 하나 결측 시 포트 쪽 어느 끝인지 정의; R1 단언 수정 |
| M1 | Major | 41 §4.7-3a 3 (702) | 동작점 불일치 포트 = unmeasured(사유 없음, 거부는 봉인) -- (a) triode tol 띠(VDsat−tol<VDS<VDsat)는 N3.8 정의로 triode라 봉인 거부 보장 없음 (b) 입력 DC 미선언 뿌리에서 '동작점' 풀이 정의 없음 (c) §4.7-3 4(측정 실패 때 뿌리 아닌 포트 항목 안 씀)와 충돌 (d) 사유 없음 = O-55 U1·N3.14와 어긋남 | 판정 점 = 커널 마지막 풀이; 불일치 판정은 봉인 7·9와 같은 함수·기준(EO-1 공용); 봉인 통과 가능하면 별도 code(input_window_operating_point_mismatch, definitional, detail=소자) 기록, 아니면 근거 명시 |
| W1 | Warning | 41 §4.7-3a 1 (다) (700) | off 행 부호·첫 칸: saturation_window rate = 여유의 x 미분(input_window.py:57-65); 여유 V_on−VGS는 VGS↑에 감소 → 경계 반대; 첫 칸 g | 행 = (g, s, −부호, V_on−VGS, "off"), triode = (d, s, −부호, VDsat−VDS−tol, "triode") 명시 |
| W2 | Warning | 41 §4.7-3a 1, §4.7-7 머리 (750) | region_rows 5원소 vs saturation_window 4원소 행(input_window.py:57); rows 입력 꼴 변경 미기재 | 4.7-7에 rows 원소 꼴 명시 |
| W3 | Warning | 41 §4.7-3 3 (695), §4.7-4 2 | P3 묶음 훑기 인터페이스 없음(saturation_window 단일 root, x0=values[root] -- input_window.py:34-35,55); 끝 풀이 묶음 이동 미기재 | root = 넷 tuple(각 s=1), x0=0 이동량, 반환 = 포트별 창; 끝 풀이 fixed_values[p] = 선언값+Δ |
| W4 | Warning | 41 §4.7-4 5 (a) (724), 40 §2.4.8 553 | 수락 뒤 parent = 다듬은 결과 → 다음 커널(search/kernel.py:123,126)이 refined·metrics_icm_front를 낡은 값으로 싣거나 커널 안 재계산(K3 위반) 미정 | parent = 다듬기 전 evaluation 또는 재사용 규칙이 커널 밖 writer 필드를 버림 명시; K3 단언 추가 |
| W5 | Warning | 41 §4.7-5 740 | IcmWindow.config 생산자 없음(S-1·S-2 전), metrics_icm_front 소비자 없음 | config는 S-1·S-2 뒤 추가; metrics_icm_front·criterion·window_end_solves·model_error_ref '출력 전용(EO-1·ME-1 전)' 명시(N6.6 완료 조건 (5)) |
| W6 | Warning | 41 §4.7-4 5 (723·725·726) | master 2e707d5d 기준 줄 틀림: kernel.py 캐시 :101 조회/:170 저장(·:112), evaluate :94, _point_record :51-61 | 착수 전 재측정 |
| I1 | Info | 41 §4.7-0 A8, §4.7-6 | sizing/CONTRACT.md node.dc_window 행 :202(design :196) | 재측정 |
| I2 | Info | 41 §4.7-1 1·5 | IT-1 삭제 목록에 scc_order.py:125·:137, sizing/CONTRACT.md:232·:497 없음 | 추가 |

작성자 선택 판정: triode 경계 여유 VDsat−VDS−tol_VDsat ≥ 0 = 조건부 수용(새 상수 없음·fail-closed, 단 N3.8 '+tol'은 포화에만 정의 -- triode 확장은 작성자 해석, '원래 취지와 다를 수 있음' 사용자 확인 + 봉인 triode 대조와 같은 기준이어야 함); off 행 tol 없음 = 수용(근거는 V_on 정의가 판정 분해능을 품음); 동작점 불일치 unmeasured = 수정 필요(M1).

결정 반영: P1 반영, P2 커널 창 맞음·다듬은 창 틀림(C1), P3 뜻 맞음·인터페이스 없음(W3), P4·P6 반영, P5 반영(출력 전용 선언 필요), O-54 반영(W1·W2), O-55 U1 문제(M1), V5 VGS 행 반영·부호 틀림(W1). 필드 소유표 40↔41 일치, code 일치.
확인 안 함: 41 §4.7 밖, 40 §3.8-8 전문, DE-1·LA-1·EO-1 원문 대조, writer_plan.py:157-159·228-238 등, test 구조 규칙, history, 다른 계획 후속 정정.
