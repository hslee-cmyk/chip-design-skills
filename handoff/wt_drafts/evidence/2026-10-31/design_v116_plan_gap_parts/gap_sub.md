# gap_sub -- 하위 계획 5개(v6.38.5 전파) ↔ design v1.16.0 (40/41/42, HEAD bc3b3572) + 하위 design

분석자: design↔계획 gap 분석(읽기 전용). design 줄은 `kws_sub.py`(scratchpad)로 직접 읽어 확인. 약칭 40/41/42 = gain-budget design, OSd/OTd/OPd = offset-strategy/offset-trim/oracle-portability design.

하위 design 존재 실측(`git -C wt/design-v115 log -1`):
- headroom-chain design(HC-D) = **없음**(docs/02-design/features에 파일 0). graph-consumption design(GC-D) = **없음**.
- `offset-strategy.design.md` v0.3.3, plan_version 0.7.3, 마지막 커밋 `01989bcc`(2026-10-21) -- 이번 v0.7.6 개정 미반영.
- `offset-trim.design.md` v0.3.3, plan_version 0.5.5, 마지막 커밋 `4b38ac99`(2026-10-16) -- v0.6 이후 미반영.
- `oracle-portability.design.md` v0.3.10, plan_version 0.6.17, 마지막 커밋 `4169d35e`(2026-10-21) -- v0.6.22 미반영.

## 표 A -- 항목별 판정

### headroom-chain (new_headroom-chain.md)

| # | 계획 자리(new 줄) | 변경 요지 | design 자리 | 판정 | 메모 |
|---|---|---|---|---|---|
| H0 | 24·115·383·491·522·545·581·529·541 | 판 머리, 9→library 13(O-181), ME-1→CL-1 괄호, '옛' 표지 | 40:12(library 13·held-out 0) | 해당 없음(계획서 정리) | -- |
| H1 | 58·162·540 | SPICE 다리 = O-178 oracle 판정(정의 관문 + 닫힌 점, 수치 차 = 대조 기록) | 40:1964, 42:364 | 일치 | -- |
| H2 | 72 | 창 뿌리 = `node.dc_writer` W4 `free_window` 넷, 구조 색 `dc_colour`(정점마다 유일) | 40:442(구조 색 행), 41:644(relation `free_window`) | 일치 | 계획 인용 'design 40 535행'은 낡은 줄 번호(40:535는 빈 줄, 정의는 40:442) → C-1 |
| H3 | 72 | 열린 표지 M-2(고립 넷 W4 y 범위 = 순서 창 여부) | 41:1463 | 일치 | -- |
| H4 | 75·332 | MOS 극성 규칙 P 하나(VDS 위쪽·VGS 변), 변마다 1회 | 40:451, 41:1795 | 일치 | 서명 = HC-D design(미작성) |
| H5 | 83·85·372·541 | KCL 항등 0 전류 MOS = 봉인 9 (i)(iv) 밖, 오라클 독립 유도 대조(O-182 Q-S9 A′) | 40:1126 | 일치 | -- |
| H6 | 157·256-258·514(N7.1)·571 | 세 자리 배선 = LA-1, 순서 HC-1 → LA-1(#16, O-190), 호출 수 보고 = LA-1 | 41:1283, 42:319, 40:2181 | 일치 | -- |
| H7 | 220·326·353·555·565·569 | R-1′ 묶음 생산 = HC-1(O-190), `vds_saturation` 같은 변경 삭제, R-1′ 정의 toy·VDS-1 포함 비교 = HC-1 | 40:451, 41:899, 41:1736, 42:312 | 일치 | -- |
| H8 | 227 | F_exist 정의, writer_root 행 ∈ F_exist, 한 구간 여부 = HC-D | 40:451, 40:2201 (d) | 일치 | -- |
| H9 | 234·236 | 마지막 키 = DEC-97 정준 위치(O-189), 발동 여부 HC-D 확인; R-1′ 블록은 TieBreak 형식만 빌려 **자기 출력**에 기록, `graph.dc_tie_breaks` writer = 쓰기 계획 블록 하나 | 40:2201 (a)(키·공허 여부), 41:644(dc_tie_breaks decision = writer_edge·w4_root·current_pivot) | 누락(minor) | 키 위임은 일치. 'R-1′ 자기 출력 TieBreak 기록'과 dc_tie_breaks와의 경계 문언이 40:451 '담는 것'·41:644 어디에도 없음(형식은 HC-D 몫이라 착수 차단은 아님) |
| H10 | 241 | 판정 = J_point(DEC-104 (0)), F_exist 용도(재개방·W4·V_R·순환 출처), 퇴화 등가 → 판정 자리는 J_point만 | 41:1795, 40:451 | 일치 | -- |
| H11 | 250-251 | 출발 충돌 기록 writer = R6 블록, 칸 기록은 R6 출력 읽기·F_exist 재호출 0 | 41:1795('writer = R6 -- O-142 (5)', '새 슬롯·사본 0') | 일치 | '같은 입력 F_exist 재호출 0' 명시 문언은 없음(새 슬롯·사본 0으로 포괄) |
| H12 | 254 | HC-1 design 조건: `StartConflict`를 처음부터 7a(=R6) 자리, 과도 기간 꼴 = 비활성 갈래 0 | 41:1795 | 일치 | 과도 기간 7a 꼴은 HC-1 design 몫으로 넘김(계획과 같음) |
| H13 | 256-258 | 단좌표 자르기 정의 1곳·호출 2곳(N3.1-5 / R5′ (4)(iii)) | 41:903 | 일치 | -- |
| H14 | 256·791 | S/B/F/X → S/B/F(X 칸 삭제, O-187) | 41:875, 41:1407, 40:449 | 일치 | -- |
| H15 | 271·341-343·584 | `order_terms` 배선 = GC-8, HC-1과 같은 통합 병합(#17, O-191) → O-157 S8 '창 함수 하나'·예산 경로 규칙이 HC-1 병합부터 성립 | 40:2201, 40:441 | 일치 | -- |
| H16 | 330·514(HC-S 행)·631 | `dc_sat_v` `off` 갈래 = HC-S, 순서 EO-1 → HC-S(#7, O-183), HC-S → WB-1(#6·#11, O-185) | 41:784, 41:686, 40:2205(WB-1 행) | **다름** | 41:784 '`device.dc_sat_v`의 `off` 갈래(HC-S·EO-1 중 늦게 병합되는 쪽)' = O-183이 버린 옛 문언. 40:2205 WB-1 선행 = card B·OP-7·EO-1 -- HC-S 없음(O-185 #6·#11 누락). 41:686 'O-56 (b)로 HC-S·EO-1 몫' 모호 |
| H17 | 341-347·349 | `off` 선언 소자를 구조적 전도 집합에서 뺌(검증 32 M-1) | 40:441(`iv_headroom` 구조적 전도 집합 = `zeros` READS만) | 누락(minor) | gain-budget design에는 `off` 제외 문언 없음. 정의 자리는 headroom-chain N3.4·HC-D design(미작성) |
| H18 | 349-350 | `current_symmetry` 결과 전체 HC-1 한 길(GC-8 통합, O-183 과도기 금지) + 열린 표지 M-6 | 40:441, 41:1463 | 일치 | 생산자 둘 기간 0 = HC-D·GC-D 몫(40:2201 (e)) |
| H19 | 514(HC-1 선행 열) | HC-1 선행 += GC-D design 승인·GC-1(O-191), TB-1 → HC-1(#5) | 40:2201 | 일치(부분) | 40:2201 선행 열거 = TB-1·HC-S·GC-D·GC-1뿐. 계획의 HC-D·XRUN-F1 card C·IT-1·EO-1(완료 판정 선행) 생략(minor) |
| H20 | 631 | HC-S → TB-1 삭제(O-192), [HC-1 + GC-8] → LA-1 | 40:2200(TB-1 선행 HC-S 삭제), 40:2209(LA-1 선행) | 일치 | -- |

### graph-consumption (new_graph-consumption.md)

| # | 계획 자리 | 변경 요지 | design 자리 | 판정 | 메모 |
|---|---|---|---|---|---|
| G0 | 15·97·439·552·640·791 | 판 머리, library 13(O-181), '이관 전' | 40:12 | 해당 없음(계획서 정리) | -- |
| G1 | 382·724·743·773 | 쓰기 계획 블록 KVL 관계 필드(뿌리 경로·변 필드) 생산 = HC-1 한 길(O-190, O-183 과도기 금지), GC-2·GC-8 읽기 | 40:451(넷별 뿌리 경로·Gs⁺ VGS 변 = HC-1), 42:312 | 일치 | GC-2 행 자체는 40/41/42에 0건 -- GC-D design 몫 |
| G2 | 560 | 판정 = O-178 oracle 판정 | 40:1964 | 일치 | -- |
| G3 | 643·658 | GC-8 = HC-1과 같은 통합 병합(GC-8 커밋이 HC-1 뒤), 방향 사본 셋(`order_terms`·`_edges`·`_edge_nets`)·`headroom_bound` 정책 분기 한 병합에서 0 | 40:2201, 40:441 | 일치(병합 규칙) / design 몫 아님(사본 삭제 세부) | 40/41/42에 `_edge_nets` 0건, `CurveBook._edges`는 40:343 edge_costs 행에만. 사본 삭제·정책 통일 세부는 GC-D·HC-D design 몫(40:2201 '`order_terms` 배선 = GC-D design') |
| G4 | 643 | `off` 선언 소자도 구조적 전도 집합에서 뺌(HC N3.4 인용) | -- | H17과 같음 | -- |
| G5 | 773 | N10.3 GD-2: 뿌리 경로가 VGS 변 참조형 여부 = HC-D design과 공유 | 40:2201 (c) | 일치 | -- |

### offset-strategy (new_offset-strategy.md)

| # | 계획 자리 | 변경 요지 | design 자리 | 판정 | 메모 |
|---|---|---|---|---|---|
| S0 | 3·94·353·362·490 | 판 0.7.6, library 13, 이관 전 | -- | 해당 없음(계획서 정리) | -- |
| S1 | 11·180·257·376·378·402·406·539·552·564 | DS-1 = (나)(O-176 Ⅵ): 같은 θ 1회 평가 + 변형별 판정. 조건 (1) 판정 행 → graph 필드 `constraint_rows`, `EvalResult` 판정 칸 같은 변경 삭제 | 40:471, 40:611 | 일치(조건 1) | -- |
| S2 | 같음 | 조건 (2) metric 블록은 요청별 분할 S3 graft, 추가 변형이 새 metric 요청을 가져오면 fail-closed; 반영 시점 = OS-5 착수 전; 구현 = OS-5·OS-L(OSd §10) | 40/41/42: 0건('요청별'·'추가 변형'·'변형별' 0). OSd:393·478·480·516 = **DS-1 = (다)(S-14)** | **다름**(OSd) / 누락(40) | OSd §10 전체가 옛 (다) 키 분리(`constraint_set_fp`)로 남음 -- O-176 Ⅵ과 정면 충돌. gain-budget 40 §2.4.9 graft 키에 '요청별 분할' 문언 없음 |
| S3 | 152·477 | S3 색인 대체 시점 = card B + LA-1 범위 15 (iv) 뒤(#8) | 40:305 | 일치 | -- |
| S4 | 418-423 | LA-1 → OS-2 고정(#8·#9, O-183) | 40:305, 40:611, 40:2209 | 일치 | OSd:198 'gain-budget LA-1이 먼저 병합됐으면' = 옛 문언(다름, OSd) |
| S5 | 426 | Q8 = LA-1 design이 닫는 열린 질문(사용자 결정 아님), 기본안 = 행 안 `unmeasured` + 사유; OS-2 착수 = LA-1 병합(Q8 닫힘 포함) | 40:611(Q8 닫힘 v1.16.0, `measure_state`·`reason`), 41:1454 | 일치 | OSd:63·132 'OS-2 착수 = U17 ② 병합 + Q8 결정(사용자)' = 옛 문언(다름, OSd) |
| S6 | 443·463 | 열거 API·분할·`constraint_rows` writer = LA-1이 만들고 OS-2는 읽기 | 40:305, 40:611 | 일치 | -- |
| S7 | 463 | LA-1 → DE-1 → OS-2(#2) | 40:2204, 40:2209 | 일치 | -- |
| S8 | 348·388 | 실행 중 변형 추가와 O-178 oracle 닫기 경계 = 상위 Q-W1과 함께 | 40:12(Q-W1 보류), 40:1149 | design 몫 아님 | 계획 개정 대기(DEC-72 (5), graph 규칙 6) |

### offset-trim (new_offset-trim.md)

| # | 계획 자리 | 변경 요지 | design 자리 | 판정 | 메모 |
|---|---|---|---|---|---|
| T0 | 17·89·115·495·549·553·606·654·796 | 판 머리, library 13 | -- | 해당 없음(계획서 정리) | -- |
| T1 | 138·151·197·337·413·419·550·556·585·601·707·732·750·803-809 | model_error/모델 오차 → 대조 기록, SPICE 다리 = O-178 oracle 판정, ME-1 → CL-1 | 40:426, 40:1964, 42:364 | 일치(gain-budget 쪽) | OTd:1078 `tj_model_error`(§17-1 σ 불일치 또는 엔진·오라클 차) = 옛 개념 이름(다름, OTd) |
| T2 | 276 | DAC 단위 셀 θ = ln IDu·L | OTd:975(X-T2 ln IDu·L) | 일치(OTd) | -- |
| T3 | 376-394·441(새 문단)·463 | Δ_T 기록 형식은 옛 `model_error_<metric>` 인용 무효, 닫기 Δ와 자리 통일 안 함(O-178 (7)), 문턱 합성은 Q-W1 계획 개정 전 금지, spec 측정 선언 절 만들지 않음 | 40:426(spec `derived.model_error_*` 삭제), 40:12(Q-W1 보류) | 일치 / design 몫 아님(Δ 정본 자리) | 40/41/42에 Δ_T 0건 -- Δ 자리가 계획 미정이라 만들지 않는 것이 맞음 |
| T4 | 572 | 완료 9 grep 정의(O-176 Ⅳ): 대신호 양 정확값 고정 기하 Newton 풀이 0, W′ E-0 재봉인은 밖 | 41:697 | 일치(gain-budget) | OTd:606·846 `balance_solve` 고정 기하 DC 균형 풀이가 아직 정의됨(다름, OTd) -- 계획 N7.5가 TR-0T design 개정 범위로 이미 적음 |

### oracle-portability (new_oracle-portability.md)

| # | 계획 자리 | 변경 요지 | design 자리 | 판정 | 메모 |
|---|---|---|---|---|---|
| P0 | 18·183·230·510·522·550·575·580·762 | 판 머리, 9회로 → library (13)회로 | -- | 해당 없음(계획서 정리) | -- |
| P1 | 60·140·143·150·423·442·452·454·458·506·577·593·604·772-775 | 엔진·오라클 차 = 대조 기록(oracle 판정 기록 칸, 판정 기준 아님), X-6 무효 대상 = 대조·판정 기록 | 40:426, 41:661, 42:271(`verified_by` -- `model_error_ref`·`max_error` 칸 없음) | 일치(gain-budget) | OPd:77·88·852·1060·1845 '모델 오차(DEC-72)' 문언 = 다름(OPd) |
| P2 | 430·432·508·553·592·634 | 오라클 1단계 꺼짐·포화 판정에서 KCL 항등 0 전류 MOS 제외 + 독립 유도 대조(O-182 Q-S9 A′) | 40:1126 | 일치(gain-budget) | OPd에 해당 문언 0(누락, OPd) |
| P3 | 418-420·512-513 | `derived.model_error_power_dc_w` 삭제, PW-1b 삭제, 전력 축 사슬 OP-11 → PW-1a → CL-1, `power_dc_w` 대조 근거 = 정의 동일성 관문(DEC-72 (3)·PW-1a) | 40:426(spec derived 삭제), 40:1964(정의 동일성 관문) | 일치(규칙) / 누락(card) | card PW-1a는 40/41/42에 **0건**(gain-budget 계획 N6.17에 card로 있음 -- design card 표에 자리 없음). OPd:1963 '모델 오차 기록 `derived.model_error_power_dc_w`' = 다름(OPd) |
| P4 | 419 | 'CL-1 신설은 상위 N5.3 Q-CL1 승인 대기' | 42:364(O-182 Q-CL1 승인 인용) | -- | 계획 낡음: O-182가 Q-CL1을 승인함 → C-3 |
| P5 | 480·619 | `A/sky130_nfet_pfet_lut_sample.npz` O-180 삭제, 그 기준선 입력 처리는 OP-1b 착수 때 | -- | design 몫 아님(40/41/42) | OPd:194·715·1575가 sample npz를 실재 입력으로 적음(다름, OPd) |
| P6 | 521 | 동작 변경 card SPICE 다리 선행 목록 ME-1 → CL-1 | 40:2190, 41:766 | 일치 | -- |

## 표 B -- card 착수 가능성(이번 개정이 바꾼 card)

| card | 항목 | design 자리 | 판정 |
|---|---|---|---|
| HC-1 | 범위: R-1′ S0 필드 + `vds_saturation` 삭제 | 40:451, 42:312 | 일치(형식 = HC-D 미작성) |
| HC-1 | 범위: F_exist·J_point·P | 40:451, 41:1791·1795 | 일치(서명 = HC-D 미작성) |
| HC-1 | 범위: 출발 구간 반영(조정 = R6), 층 0 거르기 함수 | 41:1795, 41:1283 | 일치 |
| HC-1 | 범위: 쓰기 계획 출력 S0 필드(뿌리 경로·Gs⁺ VGS 변) | 40:451, 42:312 | 일치 |
| HC-1 | 범위: `current_symmetry` 한 길 | 40:441 | 일치 |
| HC-1 | 범위: `iv_headroom._edge_nets` 사본 삭제 | 40/41/42 0건 | design 몫 아님(HC-D) |
| HC-1 | 범위: `off` 선언 소자 호출 제외·구조적 전도 집합 제외 | 40:441에 없음 | 누락(minor, HC-D 몫) |
| HC-1 | design 조건(7a 기록 자리·퇴화 등가·P 1회·단좌표 1곳) | 41:1795, 41:903 | 일치 |
| HC-1 | GC-8 통합 병합 | 40:2201 | 일치 |
| HC-1 | 완료: R-1′ 정의 toy·VDS-1 포함 비교·`vds_saturation` grep 0 | 42:312 '확인 = HC-1 완료 조건' | 일치 |
| HC-1 | 착수: HC-D design 승인, GC-D design 승인·GC-1, TB-1·HC-S 병합 | HC-D·GC-D 파일 없음 | 착수 불가(정상 대기 -- 선행 design 미작성) |
| HC-S | 범위: `dc_sat_v` `off` 갈래 = HC-S | 41:784(옛 '늦게 병합되는 쪽') | **다름** |
| HC-S | 선행 EO-1(#7), 뒤따름 WB-1(#6·#11) | 40:2205 WB-1 선행에 HC-S 없음 | **다름** |
| GC-8 | HC-1과 같은 통합 병합, 커밋 순서 | 40:2201 | 일치 |
| GC-8 | 방향 사본 셋 0·`headroom_bound` 정책 통일 | 40/41/42 0건 | design 몫 아님(GC-D 미작성) |
| OS-2 | 선행 LA-1(#8·#9), `constraint_rows`·열거 API 읽기만, Q8 = LA-1 design | 40:305, 40:611 | 일치(gain-budget) / OSd 다름 |
| OS-5 | DS-1 = (나) 조건 (1) | 40:471, 40:611 | 일치 |
| OS-5 | DS-1 = (나) 조건 (2) 요청별 분할 graft·새 요청 fail-closed; 착수 전 반영 | OSd §10 = (다) | **다름 -- 착수 차단** |
| TR-(완료 9) | grep 정의 O-176 Ⅳ | 41:697 / OTd:606 balance_solve | gain-budget 일치, OTd 다름(TR-0T 개정 범위로 기지) |
| PW-1a(OP 쪽 근거) | 정의 동일성 관문으로 근거 교체 | 40:1964 규칙만, card 행 0 | 누락(card 행) |

## 목록 C -- 계획 개정 필요 / 하위 design 미반영

- C-1 headroom-chain N0.1 72행 '상위 design 40 535행 정의 -- `dc_colour`': design v1.16.0에서 정의 행은 40:442(40:535 빈 줄) -- 줄 번호 대신 '40 §2.4.8 구조 색 행'으로. 같은 줄 'design 41 §6.7-1a 정정 대상'은 41:639에서 이미 O-189로 정정됨 -- 낡은 표지.
- C-2 headroom-chain N7.1 HC-1 선행 '상위 card TB-1 병합(S/B/F 분류 필드 -- 상위 O-144 J3)': O-144 J3은 R-1′ 생산 = TB-1 결정이고 O-190이 되돌렸다 -- S/B/F 분류 필드 근거로 J3을 인용하는 것은 낡음(근거 = DEC-104 R13·(3)(a), O-187).
- C-3 oracle-portability N3.7 419행 'CL-1 신설은 상위 N5.3 Q-CL1 승인 대기' -- O-182가 Q-CL1(card CL-1 신설) 승인함(design 42:364도 O-182 Q-CL1 인용). 낡은 문언.
- C-4 oracle-portability N2 140·143·150, offset-trim N7.4 726 근거 칸('상위 DEC-72 모델 오차 선례(같은 기록 모양)')은 '(→ O-178 뒤 대조 기록)' 화살표 덧댐으로만 남음 -- 원칙 25(계획서는 현재 규칙만)상 본문을 현재 문언으로 바꾸고 옛 말은 history로.
- C-5 offset-strategy 11행 Status의 지난 판 서술('PS-7 열거 생산자 문언 = 먼저 병합 card', '조건부 제작 단위') -- 지금 규칙(LA-1 생산, O-183)과 반대 문언이 Status에 남음 → history로.
- C-6 **하위 design 미반영(파일·마지막 커밋)**:
  - `offset-strategy.design.md` v0.3.3(plan 0.7.3), `01989bcc` 2026-10-21: §10·§3.3 132·393·478-488·516 DS-1 = (다)(S-14), §63·132 'OS-2 착수 = Q8 결정(사용자)', 198 'LA-1이 먼저 병합됐으면' -- O-176 Ⅵ·O-183 미반영. OS-5 착수 전 개정 필수(계획 '반영 시점 = OS-5 착수 전').
  - `offset-trim.design.md` v0.3.3(plan 0.5.5), `4b38ac99` 2026-10-16: 606·846 `balance_solve` 고정 기하 DC 풀이(O-53 A3·O-176 Ⅳ 위반 꼴), 1078 `tj_model_error`, 9회로 문언 -- 계획 N7.5(TR-0T design 개정 범위)에 O-178·O-176 Ⅳ 항목 추가 필요.
  - `oracle-portability.design.md` v0.3.10(plan 0.6.17), `4169d35e` 2026-10-21: 77·88·852·1060·1845·1963 모델 오차(DEC-72)·`derived.model_error_power_dc_w`, 815·1657 ME-1, 194·715·1575 sample npz(O-180 삭제), Q-S9 A′ 제외 문언 0 -- O-178·O-180·O-182 미반영.
  - headroom-chain HC-D design, graph-consumption GC-D design: 파일 없음(HC-1·GC-8 착수 조건). 40:2201 (a)~(f)가 넘긴 항목 + H9(R-1′ 자기 TieBreak 기록)·H17(`off` 제외)·G3(방향 사본 셋·정책 통일)이 그 design의 몫.

## 목록 D -- Major 후보

- **D-1 (S2, O-176 Ⅵ 어긋남·OS-5 착수 차단)**: offset-strategy design §10이 DS-1 = (다) 키 분리(`constraint_set_fp`) 그대로(OSd:393·478·480·516). 조건 (2) '요청별 분할 graft + 새 metric 요청 fail-closed'는 40/41/42에도 대응 자리 0. 계획 N10.1 '반영 시점 = OS-5 착수 전'.
- **D-2 (H16, O-183·O-185 어긋남)**: 41:784 '`device.dc_sat_v`의 `off` 갈래(HC-S·EO-1 중 늦게 병합되는 쪽)' = O-183이 버린 조건부 제작 문언(계획: 생산 = HC-S, 순서 EO-1 → HC-S, 표 #7). 40:2205 WB-1 행 선행에 HC-S 없음(계획 표 #6·#11, O-185 HC-S → WB-1). HC-S·WB-1 card 동결 때 순서·생산자 판정이 갈림.
- (참고, 경계 판정) P3: card PW-1a(gain-budget 계획 N6.17)가 design 40/41/42 card 표에 0건 -- 하위 계획 몫이 아니라 gain-budget 몫 분석자가 같이 볼 것.

## 집계

- 항목 수 48(표 A): headroom-chain 21, graph-consumption 6, offset-strategy 9, offset-trim 5, oracle-portability 7 -- 판정 기준 = gain-budget design 40/41/42(하위 design 판정은 메모·목록 C).
- 일치 34(부분 일치 포함: H19, G3 병합 규칙, T3), 누락 3(H9·H17 minor, P3 card 행), 다름 2(H16, S2), 해당 없음 9(계획서 정리 5, design 몫 아님 2(S8, P5), 낡은 계획 문언 1(P4 → C-3), H17과 같음 1(G4)).
- 하위 design(OSd·OTd·OPd) 대비 다름: OSd 3곳 묶음(S2·S4·S5), OTd 2(T1·T4), OPd 4(P1·P2·P3·P5). HC-D·GC-D = 파일 없음.
