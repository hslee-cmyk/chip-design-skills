# 전체 정합 검증 4차 요약 (2026-10-20, 감사 A 원칙별 + 감사 B 교차) -- 대상 gb v6.20 0a7868b5, oracle v0.6.10 84cc5410, offset-trim v0.6 2eba8353, offset-strategy v0.7 07326bf9, headroom-chain·graph-consumption master 9401e98f

사용자 결정 O-55(U1·U2·V5). 줄 번호는 각 머리 판 기준. 감사 사본: scratchpad full_audit4_A/, full_audit4_B/.

## 결정 (O-55)
- U1: 동작점 불일치 원인 구분 -- 선언된(triode·off) 소자 불일치 = 선언 오류 거부(판정 불능 집계), 선언 없는 소자 비포화 = 설계 실패 FAIL(범위 측정 공칭 점은 음수 margin 또는 꺼짐이면 정의 불능). gb N3.8 '선언 오류' 범위를 선언 소자로 한정, DEC-90 (1)·N3.6 SPICE 대조 (ii)·T4(289·504·1203행)를 같은 문언으로(V1 해소), A' 집계에서 거부 = 판정 불능 규칙 한 줄.
- U2: EO-1 범위 4 = (b) 공용 전도 판정 함수 하나(봉인 7·9가 바로 부름)만; (a) 2단계 호출 자리·끝 괄호 재요청은 OP-5 통합 병합의 엔진 커밋(U-6)으로, gb 1883·1885·1887 정리, oracle 414 정합. O-50 G5 'EO-1 배선 쪽'은 엔진 쪽이라는 뜻으로 해석.
- V5: O-53 B1 'off 소자 LUT·gm/ID 경로에서 빠짐' = 사이징·역산 경로 한정, 꺼짐 판정은 같은 판정 함수가 LUT(I_off) 읽음; 범위 훑기 off 유지 경계는 VGS 감도(s_g − s_s)와 그 점의 봉인 9 전도 정의를 만족하는 VGS(LUT)로(gb IT-2 1471행 VDS 감도 문언 정정, 495·1883행).

## 원칙대로 고칠 것
gain-budget v6.20: U1·U2·V5; V6 후속 정정 표에 headroom-chain·graph-consumption 행; V8 A-1 '판정 분해능' 정의 자리 하나(N3.8, 유도 근거 = 선언 판정 분해능) -- oracle은 인용; V9 LR6 σ 목표 = '커널 판정 문턱(루프에서는 조인 문턱 항목)/k'; B-2(c) N6.1에 OS-2·LA-1 선후 한 줄; B-6 on 스위치 saturation 선언 = 선언 없음으로 사상(intended_region 값 집합과 정합) 문언.
oracle v0.6.10: V7 포화 확인 대상 485·622행 = '선언 없는(포화 기본) ID > 0 MOS'(off 제외); B-4 408·429행 낡은 범위 조건 인용 앞에 'O-54로 대체' 표시·인용 해시 gb 0a7868b5 이후로·'승인 전 문안' 표기 삭제; B-5 OP-5 통합 병합 목록에 graph-consumption dc_off_current 출력 전용 선언 커밋과 U2의 2단계 배선 커밋; A 해석 보완 -- T_j 점의 공칭 판정(LUT I_off)과 온도 요청(SPICE I_off) 출처 차는 모델 오차로 기록; V8 판정 분해능은 gb 인용.
offset-trim v0.6: V4 O-54 반영(223행 '전 소자 포화 유지' 인용 → 'DC 범위 조건 = 모든 MOS가 선언 영역에 머무름'); V3 346행 온도 점 판정 담당 = oracle OP-5(구현 안 하고 부름), 인용 oracle 해시 84cc5410 이후; B-2 668행 G-12 정본 = gb LR6(1cddba6a), design은 읽는 자리만; B-3 인용 gb 해시 갱신; 739·740행 낡은 후속 정정 2건 정리; B-6 on 스위치 saturation 선언 사상 문언.
offset-strategy v0.7: V9 FR 표 669행 부근 옛 기호 |V_sys| → |V_id*|; B-7 TR-5b 이름(offset-trim card 표에 없음) → 'TR-5 안의 국면 2 게이트 해제'로; B-3 인용 gb 해시 갱신.
headroom-chain v0.7.7(새 판, master v0.7.6에서): hc 81 '포화 면제 = 선언 triode뿐' → 선언 {triode, off}; hc 329 sat_threshold 호출부·saturation_rows -- off 선언 소자 행 제외, triode 선언 소자 '포화로 넘어가지 않음'(VDS < VDSAT) 경계 행(O-54, gb N3.8 정본 인용); HC-O(81·529) 칸 이름·범위 = intended_region {triode, off}(oracle G-18 정본), 생산자 갱신 커밋 칸 대조 toy에 off 값; hc 83 봉인 9 (i) '선언 없는 MOS ID ≤ 0 거부'와 출발 단계 '전도 = 자리값 전류 양수'의 관계 명시, HC-S·HC-1 SPICE 다리·변화표에 새 거부 가능성.
graph-consumption v0.12(새 판, master v0.11에서): gc 309·573·658 dc_off_current 출력 전용 선언 시점 = OP-5 통합 병합(oracle OP-5 범위와 정합 인용); gc F-G14·U-G4·679 정본 소유 표에 공용 전도 판정 함수(EO-1 (b), 봉인 7·9·2단계 공용) 등록, conduction_mask(탐색 격자)와의 관계; off 선언 소자가 사이징·역산 경로에서 빠지는 것이 탐색 소비자(cell_floor, edge_costs, current_box)에 미치는 영향; dc_window_def_refined 기준 칸, 방향별 슬루 행, 봉인 9 판정 행 변경, 부호 있는 V_id* 필드 소비자.
