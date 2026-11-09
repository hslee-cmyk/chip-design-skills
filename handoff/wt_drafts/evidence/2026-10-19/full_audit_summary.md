# 전체 정합 검증 결과 요약 (2026-10-19, 감사 A 원칙별 + 감사 B 층·계획 교차)

대상: gain-budget v6.19 `503a31fe`(gb), oracle-portability v0.6.9 `45b51f16`(op), headroom-chain v0.7.6 `aa6e064c`(hc), graph-consumption v0.11 `0b82a214`(gc), 참고 design 40 v1.11.2 master `2305e587`. 감사 산출 사본: scratchpad `full_audit_A/`, `full_audit_B/`. 사용자 결정 O-43(D1~D3).

## 사용자 결정 대상 (O-43으로 결정됨)
- A-F1 [중대] DE-1 KVL 고정 스윙·계통 offset·슬루 방향 전류 계산법이 원칙끼리 막힘(θ 고정 = 전류 고정, O-32 크기 고정 풀이 금지, 범주 오류 금지) → O-43 D1 (a)(b)(c).
- A-F2 [중간] '봉인점 출력 오차 ÷ A_dm'을 계통 offset은 범주 오류(offset_systematic.py:1-8), 불일치 σ는 1차 정확(offset_analysis.py:7,:74,:84, op OQ-6 612행)으로 다르게 판정 → D1 (a).
- A-F7 [중간] op OQ-6을 사용자 확인 없이 닫음, 출처 불명 상수 1e-3(X-D1) → D1 (d) .tf.
- B-H2 [높음] 선언 offset_sys_mv 제약(current_reuse_telescopic_ota.sizing_spec.json:236)의 판정 자리: DEC-74(모든 제약 커널)·O-31 대 O-33 (4)·DE-1 (c)·N3.8 562행(커널 제외) → D1 (c).
- B-H1 [높음] 층 0 재정의 충돌: hc 153·252-255행(H-B: Halton 시험점·수리점 R-1′ 거르기), gc GC-5 완료 조건 6(상자 중심 출발), gb FX-1, gb LA-1 범위 6(Halton·상자 중심·사다리 순회 제외·삭제 후보); LA-1에 R-1′ 언급 0, hc에 LA-1 언급 0 → D2.
- A-F6 [중간] 고임피던스 대 KVL 고정 출력 구조 규칙 없음(gb N3.8 560·561행, DE-1 (b)) → D3.

## 원칙 기본안으로 고칠 것 (결정 불필요)
- A-F3·B-M1: 입력 창 한 필드에 정의 창(VDS ≥ VDSAT)과 탐색·판정 창(+tol) 혼재(block_columns.py:225-243 saturation_rows VDS−VDsat−tol; gb DE-1 (a) 1537행, IT-2 1446행, hc N3.4·완료 조건 11). 정의 창(전도 끝 포함, 봉인 9 식)과 탐색·판정 창을 다른 이름 필드로, DE-1 범위·완료 조건에 tol 제거·전도 끝 명시와 red toy.
- A-F4: O-34 변경 종류 표시가 DE-1·FX-1·NL-1·LI-1 완료 조건에 없음, oracle 다리 '보류' 처리 셋(LA-1 미완료 / DE-1 미룸 / UB-1 대상 없음), 출발 단계만 바꾸는 card(HC-1·GC-5)의 SPICE 다리 정의 없음 → N6.3에 '다리 보류·대상 없음' 규칙 하나, 모든 card 표시, hc·gc 인용.
- A-F5: DE-1 착수 조건에 design 40 §3.8-3·§3.8-8·design 41 J-E 개정(S-7) 없음(d40 1257·1896행 옛 정의).
- A-F8: O-36 (5) 미반영(gb 548행 '사용자 보고 대상', op 399·404행 '승인 전').
- A-F9: hc N3.4 327행 VDsat 결측 하한 0 대 NFR-H2 136행, HC-S 511행 'tol·VDsat 결측' 문구.
- A-F10: gain 분해능 정의 둘(DEC-71 (6) 270행 대 LA-1 1670행 w_g).
- A-F11: 불일치 σ 영역 표기(gb 569행 dc→ss 대 563행 DC).
- A-F12: gc N3.6-2 407행 출발 자리값 '전류 기하평균' 근거·추정 표기 없음.
- A-F13·B-L5: 낡은 줄·커밋 인용(gc 634행 hc 952d9761, gb 'hc 325·507·518행' → 327·511·522, gb F-DE1 '334행', op↔gb 커밋 인용).
- A-F14: hc 337행 정의와 계산법 섞인 문언(O-29 (2)).
- B-M2: DE-1 oracle 다리 선행 OP-5·OP-10이 gb card표 선행에 없음; offset_sys_mv(verified_by.py:45 SPICE_UNVERIFIABLE)·slew_rate_v_per_s(registry·verified_by에 없음)의 엔진 measure 연결 card 없음 → PW-1a 꼴 card.
- B-M3: '7a 측정 실행'이 card표에 없는 노드, 단위 11 선행 '전부'와 LA-1 완료 '7a 뒤'의 순환 가능 → card id 정의.
- B-M4: FX-1·GC-5·GC-9(start_intervals.py, iv_currents.py), GC-9·LA-1(layer0_center.py, fd_jacobian) 순서 없음.
- B-M5: 봉인 집합 표기(gb 470-480행 표에 9 없음, 272·904·1673·1698·1710행 '1~8', 코드 1~9 seal.py:41, gc U-G9 봉인 8 삭제 예정) → N3.6 표에 봉인 9, '커널 = 봉인 전 항목'.
- B-L1: '전도' 정의 넷(op.current>0 hc R-1′ / ID>0 봉인 7·N3.6 (ii) / I_off≤ε·ID 봉인 9 / oracle_compare.py:27,278 ε=1 합격 판정) -- oracle 합격 판정 정정 여부.
- B-L2: 훑기 점 I_off에 ε의 tol_V는 동작점 입력값(op 399행) -- 같은 점 값(P-1).
- B-L3: gb 558행 power_dc_w measure 낡음(supply_current_A).
- B-L4: gb 1449행 IT-2 HC-S 선후 문언 낡음(hc가 IT-1 → HC-S로 정함).
- B-L6: op N5.2에 headroom-chain HC-O 행 없음, 선언 triode 입력 칸 두 계획 정의.
- B-L7: '수락 반복' 층 용어가 DEC-73 층 목록에 없음, 외층 끈 뒤 다듬은 창 계산 자리.
- B-L8: gc 330행 R4 '네 곳(ls_swing 포함)' 문언.
- gc→gb 미반영: 봉인 8 행 삭제(U-G9)가 gb LA-1·DEC-73 '1~8' 근거와 충돌; U16 완료 조건 미확인.
