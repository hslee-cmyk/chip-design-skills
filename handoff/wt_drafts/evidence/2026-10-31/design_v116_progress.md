# design v1.16.0 진행 기록 (계획 v6.38.5 맞춤, 승인 O-193)

- worktree: `wt/design-v115` (브랜치 design/v115), 시작 HEAD `31b042cd`
- 대상: design 40·41·42 + design history
- 입력: 계획 diff 052465ed..0acb5e63, user_decisions O-175~O-193, card_stale_audit_o186.md(45항목 U1~U7), 검증 33 D-1~D-5, 검증 32·30 design 몫, q_tb1r_v3 (iii)-1~6, q_gc8_v2 (iii)
- 작업 순서(계획): (1) 41 Q-TH1 (A) (2) 40·42 (A)·(L2) (3) Q-KV1·O-189 이름 키 (4) O-190~192 + 이관 항목 (5) 머리·판 이력

## 진행

### 1. 41 Q-TH1 (A) -- 커밋 5d85bcbc
- 반영: T2(4.5), T3·T4(4.2 L0), T5·T6·T7(5.3.3·5.3.1), T8·T9·T10(5.3.7), T11(5.3.8), T12(5.10 표), T13(5.11), T14(별도 확인 필요 E9), T15(4.1), T16·T17(6.1·6.2·6.3·6.4), T18·T19(6.7-3·4), T20(7.5), T21(9 test), T25(6.4-2a·6.7-11·E12 -- U4 = 계획 DEC-104 (3)(b)로 '순방향 제약 행' 확정)
- U3: S·F 출발 = 출발 구간 아래 끝(ln IDu 최소) -- 계획 U-124 '위치 최대 = ln IDu 작은 쪽' + design 6.7-4 '§6.1-7과 같은 기준'으로 유도, 원래 취지와 다름 후보(pfet 비단조)로 보고
- 같이 반영: K12·K13·K14·K15·K16(E11)·K17·K18·K19(41 쪽), O-190 R-1′ 필드 card = HC-1(41 5.3.4·6.7)
- 남은 41: 669·780 이름 키(D-3), 644 order_hints(K11), 205·376·1113 이름 정렬(O-189 범위 판단), 5.12 이력, 머리 판

### 2. 40·41 Q-KV1·O-189·O-190~192·(L2) -- 커밋 ae881d7d
- K1~K10·K16(40 쪽)·K19·K11, L1~L4, T22~T24, U6(K9) = structure.json `dependent_member` concept 신설(confirm/override), U7 = l_owner_position_order(O-189 DEC-17 반영), U5 = W_m 식 ID·L/IDu, D-3(IcmPort), D-5(card 표 HC-1+GC-8 행), TieBreak(w4_root) 유지 판단
### 3. O-178·O-183·O-175/181 -- 커밋 3242bff5
- 40·41 model_error 전부, 조건부 제작 → 표 고정, SF-1·VB-1 ORACLE_ONLY 표 = 계획 개정 필요(표에 쌍 없음), §10.5 A' 13회로
- 남음: 42 전체, 9회로 규칙 자리(test 범위 등) 일부, O-182 Q-S9·Q-CB·Q-LA16·GL-1·Q-CA1, O-176 Ⅳ(41:697), 이관 D-1·D-2·D-4, Q-TB1R (iii), Q-GC8 (iii), 머리·판 이력

### 4. O-182 묶음·O-176 Ⅳ·이관 -- 커밋 6a98a9c6
### 5. 42 + 13회로 규칙 자리 -- 커밋 fd5ee69d
### 6. Q8 닫힘·MJ-B·Q-W1·41 §5.12.8·머리 판·이력 H40-33/H41-34/H42-04/H40-34 -- 커밋 3b8dcb3b
### 7. 42 남은 O-186 문언 -- 커밋 bc3b3572
## 완료 (2026-10-31) -- 다음 단계 = design 검증(design-validator) + design↔계획 gap (오케스트레이터)
- 계획 개정 필요: P1 DEC-11 문언, P2 SF-1·VB-1 ORACLE_ONLY 제작 card, P3 V9 design 자리
