# 계획 v6.38.6 검증 51 -- plan/v6386 b17957d3·fe53f211·ef911010(부모 a4d87f1a)

- 검증자: 독립 검증 agent(계획 작성자 아님). 읽기 전용, 저장소·계획·git 쓰기 0.
- 대상: `wt/plan-v6386` 계획 5개(gain-budget·offset-trim·headroom-chain·graph-consumption·oracle-portability)와 history.
- 기준: 루트 CLAUDE.md 원칙 1·2·3·7·8·9·10·11(O-197)·12·17·19·20(O-208)·22·24·25, 결정 원문 `wt/_drafts/user_decisions.md` O-200~O-213(1181~1194행 직접 읽음), K13 정본 = `wt/_drafts/ask_gates/2026-10-31_K13v2.md` '권고와 판정', 후보 문서 `o200_audit_k10_physical_v5.md` §3.3·§3.4, `o208_rereview_candidates.md`.
- 실측 폴더: `wt/_drafts/evidence/2026-11-01/plan_v6386_v51/` (스크립트 `chunks.py`·`kw.py`·`stale_strict.py`·`seg.py`·`design_scan.py`·`design_hits.py`·`hist_bytes.py`·`moved_check.py`, 결과 `*_out.txt`·`kw_*.txt`·`seg*.txt` 등).
- 줄 번호 = ef911010 기준(P = gain-budget plan, GC = graph-consumption, HC = headroom-chain, OT = offset-trim, OP = oracle-portability).

## Major

### M1 -- 엔진 2단계 전도 판정 잔재가 하위 계획의 card·완료 조건·스키마·위험 표에 정본처럼 남음(원칙 20·7, O-205 (2)·O-210 RR-2·O-202 (1))
정본(P:659 N3.6 정본 (6), OP:431 '판정 위치 -- 오라클 한 단계': 엔진 2단계 함수·호출 자리·`stage2_judgment` 없음, 엔진 import 0)과 정반대 문언이 표지 없이 살아 있다.
- OP:510 OP-5 card(N5.1): 'I_off·tol_V 계산과 전도 판정 마무리는 EO-1 쪽 2단계 엔진 정본 LUT 함수, N3.9 전도 판정 위치 -- 두 단계; 2단계 함수 엔진 커밋 Role: code는 이 card의 같은 통합 병합에', '합격 판정 전도 기준을 봉인 9 식으로 정정(I_off·tol_V는 판정 점 VDS·VSB의 엔진 LUT 조회)', '선언 영역 칸 {triode, off}로 넓혀 범위·합격 판정에서 대조'.
- OP:523 N5.2: 'OP-5 통합 병합에는 생산자 갱신과 함께 전도 판정 2단계 함수(EO-1 쪽, 엔진 정본 LUT 함수로 I_off·tol_V 계산)의 엔진 커밋도 들어간다'.
- OP:555 N5.3 완료 조건 10: 깨진 변형 목록에 '2단계를 거치지 않고 오라클 1단계 결과만으로 PASS를 내는 경로'(= 지금 정본 동작을 실패로 요구), 'off → 전도를 범위 끝으로 보지 않는 경로'(O-202 (1)·O-54 off 끝 조항 철회와 반대), '2단계(엔진 함수)의 깨진 변형 test는 EO-1 쪽 몫, 이 조건은 두 단계를 이은 끝 판정을 본다'.
- OP:594 G-18(N7.2): 'I_off·tol_V는 엔진 정본 LUT 함수가 2단계에서 SPICE op 점으로 계산', 결과 칸 '2단계 대기', '2단계가 끝 괄호를 다시 좁힐 때 쓰는 훑기 구간 입력 칸', B1 off 동작점 불일치 = 거부 코드.
- OP:421 U-6: '전도 판정 2단계 함수(G5)는 OP-5 통합 병합의 엔진 커밋'. OP:772·773 N9 위험: '오라클 결과는 2단계 없이 PASS를 내지 않고 2단계 대기로 표시', '2단계 ↔ 오라클 재훑기 왕복'.
- GC:688 N7.3 완료 조건(표지 없음): '공용 전도 판정 함수 ... oracle 판정 둘째 단계가 SPICE op 점으로 부름 -- 둘째 단계 호출 자리는 OP-5 통합 병합의 엔진 커밋 ... OP-5 통합 병합 전 확인에서 검증자가 AST 호출 그래프로 잰다' -- 같은 문장 안 '(둘째 단계는 상위 O-205로 삭제)'와 자기 모순.
- 작성자 grep(`plan_v6386_stale_grep.txt`)은 OP:510·GC:688을 '정정 인용'으로 분류했고 OP:421·523·555·594·772·773은 키워드 밖이라 잡지 않았다(실측 `stale_strict_out.txt` 143~162행, `seg`·sed 출력).
- 고칠 방향: 위 자리를 N3.9 '한 단계' 정본 인용으로 바꾸고 옛 문언은 history로; 완료 조건 10의 깨진 변형은 '오라클이 엔진을 import하거나 LUT 양으로 판정하는 경로'·'off 선언 소자를 판정하는 경로'로 뒤집는다.

### M2 -- headroom-chain에 +tol 포화 항과 `off` 선언 대조가 정본 문언으로 남음(O-204·O-202 (1), 원칙 20)
- +tol: HC:247 '선언 triode가 아닌 적층 후보: 일반 전도 소자와 같은 항(VDsat + tol)', HC:248 'diode 연결 소자: 기초 부등식 VGS ≥ VDsat + tol', HC:283 R-3 유도 'VDS(X) ≥ VDsat + tol ... − VDsat(X) − tol', HC:331 N3.4 `sat_threshold` 소비자 'saturation_rows(측정 구성 판정 창·봉인 쪽 +tol 판정 여유 행, VDS ≥ VDsat + tol)', HC:411 N3.9 C-6 '유도 성립 조건 VGS ≥ VDsat + tol'. 바로 위 HC:244(일반 전도 소자 = VDsat, 옛 + tol 대체)·HC:281(판정식 − tol 삭제)과 자기 모순이고, P:655 정본 (2) '적용 자리 전부 ... headroom-chain 출발 단계·R-1′ 항·R-3, DEC-12 diode 창 바닥'과 다르다.
- off 대조: HC:20 '포화 면제 집합 {triode, off} ... 선언 영역은 실제와 대조하고 다르면 거부', HC:128 FR-H7, HC:517 HC-O card '선언 영역과 대조해 기록(불일치 = 선언 오류 거부)', HC:577 완료 조건 9(대조 toy에 off 값 소자) -- O-202 (1) '선언 영역 대조 행 삭제'와 반대(HC:84만 고쳐짐). Status(HC:24) '`off` 선언 대조 삭제' 주장과 다름.
- 실측: `hc_lines.txt`, `kw_off_short.txt` 2~12행, `stale_strict_out.txt` 122~128행.

### M3 -- N3.6 정본 (5)(마) G2-a 정의 결함: `triode` 선언 소자에 'VDS < VDSAT = 거부'를 걸고, 판정 자리가 층 순서와 어긋남(원칙 1·7·20)
- P:658 (마) 'ΔV를 선언 없는·`triode` 선언 소자의 VDS와 VDSAT에 1차로 옮긴 보정 포화 여유 s = VDS − VDSAT로 (2)의 경계를 판정한다: s < 0이면 E-0 거부'. `triode` 선언 소자는 정의상 s < 0(P:655 정본 (2) '`triode` = VDS < VDSAT')이라 이 문언대로면 off 소자와 triode 소자가 함께 있는 모든 점이 E-0 정지한다. 결정 원문 O-202 (3)은 '다른 소자', 후보 문서 v5 §3.3 (2)는 '각 선언 없는 소자'이며 triode 확대는 작성자 추가다(물리: triode 소자의 보정 판정은 s ≥ 0이면 선언 불일치여야 함).
- 판정 자리: ΔV writer = '`graph.ss_nodal` 뒤 블록'(작성자 판단, P:658 (라))이고 ss 층은 '봉인 통과 스냅샷의 파생'(P:550)인데, 봉인 7행(P:646)은 'off 선언 소자가 있는 점은 같은 기준을 정본 (5) (마) G2-a 보정 여유에도 건다'로 G2-a를 봉인 7에 묶는다. 봉인(ss 앞)이 ss 뒤 필드를 읽는 꼴이라 층 역전이거나, 아니면 봉인 표 밖의 새 E-0 관문인데 그 관문의 자리(커널 순서·'봉인 통과' 뜻)가 정의돼 있지 않다('커널 = 봉인 전 항목', P:651).
- 고칠 방향: (마)를 '선언 없는 소자 s < 0 → E-0, `triode` 선언 소자 s ≥ 0 → 선언 불일치 E-0'으로 나누고, G2-a 관문 자리를 ss_nodal 뒤 평가 커널 순서에 명시(봉인 7행 문언은 인용으로).

### M4 -- ICMR 기능 기준의 생산 card·병합 순서가 정해지지 않았고 기존 표 #2(O-183)·SF-1 순서와 충돌(원칙 9·20, O-183·O-211)
- spec 칸(기준점·허용 저하) 로더 = SF-1(P:729 N3.8 'spec 로더 소유 card = SF-1', 낡은 card 표 P:1333 'spec 로더 단독 소유 card라는 기존 규칙에서 유도'). 그런데 SF-1은 IT-1 + IT-2 통합 병합 뒤(P:1299 선행 칸)이고, 낡은 card 표 IT-2c 행(P:1323)·N6.6(P:1703)은 IT-2c 재동결에 'ICMR 기능 기준·조건 넷'을 넣는다 -- IT-2c가 아직 없는 spec 칸을 소비하는 꼴(과도기 코드 금지, O-183).
- 점별 증분 DC 이득 함수 = 'DE-1 (e)와 같은 순수 함수'인데 그 함수 생산 = LA-1(표 #2 'LA-1 → DE-1, 생산 LA-1(O-183)', P:1346)이고 LA-1은 IT-1 + IT-2 뒤(P:1306). DE-1 card(P:1807)는 '생산 card = 첫 소비 card, IT-2c와 이 card의 선후는 머리 규칙(O-183)으로 착수 때 확인'이라 적어 #2(사용자 지정 생산 LA-1)와 다르고, 표에 새 쌍 행(#21)이 없다(O-213 조건처럼 '병합 순서는 card 정할 때'를 미룬 꼴, O-183은 표 한 자리 정의).
- 같은 판의 `judged_by`는 '생산·소비 같은 card(EO-1)'로, ICMR 칸은 'spec 로더 단독 소유(SF-1)'로 서로 다른 배정 원칙을 써서 작성자 판단 둘이 서로 모순이다(원칙 20).
- 고칠 방향: ICMR 기능 기준의 첫 소비 card(IT-2c 또는 DE-1)를 하나로 정하고, spec 칸·이득 함수의 생산 card와 순서를 병합 순서 규칙 표에 행으로 둔다(#2 변경이 필요하면 사용자 결정).

### M5 -- 원칙 19 design 후속 정정 표(P:2037~2044) 누락(design 40·41 `wt/design-v115` e957ba44 실측)
표에 없는 영향 자리(실측 `design_hits_out.txt`):
- design 40 §3.11-5 'g = s 소자 한 규칙과 신호 넷 술어'(d40:1490~1495 -- `off_vgs0` 분류·신호 경로 정지, O-210 RR-6 직접 대상) -- 표에는 design 41 §6.7-1a·design 40 §11만 있음.
- design 41 §9 test 표 IT-1 범위 재작성 5 행(d41:2056 -- '신호 경로 g = s toy 정지', `off_device_on_signal_path`).
- design 40 §3.11 E-35 행(d40:1534 'tol_V 미정 점은 봉인 6이 상류에서 막음' -- O-210 RR-7 판정 자리 이동)·E-13 서술(d40:1467 'VDSAT + tol').
- design 40 §4 오라클 절(d40:1551 E-21 '전도 판정 문턱 off_current_A ... 판정 불능', d40:1553 역할 (iii) '엔진이 전도로 예측한 MOS가 꺼지지 않음(off_current_A)') -- O-205 (2)·O-210 RR-2.
- design 40 §10.5 A' 기준(d40:2095 '전도 문턱 off_current_A는 같은 엔진 코드로 sizing W에서 계산') -- 계획 T4-pre(P:1407)는 고쳤으나 design 행 없음.
- design 40 §3.6 GB6 'DEC-88 ln IDu 연속 하한 -- P-7 동작점 의존 연속 부등식'(d40:1103), §2.4.6 LUT memo `peak_floor`·`conduction_floor` 행(d40:345), §3.10.11 U-69 행(d40:1458), §10.2 test 표 '경계 = VDSAT + tol_vdsat'(d40:1984).

## Minor
- m1. P:305 실현 평가 '봉인 전 항목(봉인 9 전도 여유 포함)' -- 옛 용어(봉인 9는 부호 판정, 여유 없음).
- m2. P:1716 IT-2 완료 (6) 'v6.36 O-118: 전도 행(R0) ... 동작 변경 원인'과 P:1720 IT-2 착수 전 (vii) '측정 구성 창 전도 행(R0 ... E-22 문턱을 design에서 먼저 고친다)' -- O-205 (3)·E-22 '대상 소멸'(P:2438)과 모순되는 살아 있는 지시.
- m3. P:1316 offset-strategy 행·OT:493 'OP-5(... 2단계 전도 판정의 oracle 쪽 칸)', 그리고 개정 대상에 없는 offset-strategy plan:326 'EO-1(2단계 전도 판정 함수)·OP-5(2단계 전도 판정 1단계)' -- 낡은 card 표·하위 계획 전파에 offset-strategy가 없다(원칙 19 전수).
- m4. 행 머리 '[정정됨 ... 이 행의 옛 ... 문언은 결정 기록]' 표지를 살아 있는 규칙 행에 붙인 자리(P:2429 N6.35 E-13 '+tol 포화 창은 측정 구성 판정 창 `node.dc_window_cfg`에만 둔다', GC:347 확인 시점 칸 '둘째 단계 reader ≥ 1')는 행 안 옛 문언과 현행 규칙이 섞여 문장마다 판정해야 한다 -- 살아 있는 칸은 현행 문언으로 고치는 편이 원칙 25에 맞음.
- m5. HC:60 인용 출처 문단의 옛 창 필드 목록('측정 구성 판정 창(+tol_VDsat)', `node.dc_window_def`, `_refined`, '정의는 상위 한 자리다')이 정본 서술처럼 읽힘.
- m6. P:654 정본 (1) '정의역 경계 활성 점 = 출력 전용 기록' -- writer 블록·card 배정 없음(원칙 7 출력 전용 선언은 있음).
- m7. P:729 ICMR 창 끝 근 찾기: '첫 교차를 보장하는 구간 나눔'을 요구하면서 선택지에 'bisection 단독'(비단조 이득 곡선에서 첫 교차 보장 불가)을 둠 -- 위임 범위를 '보장하는 수단'으로 좁힐 것.
- m8. P:658 (마) VDSAT 1차 전파가 ∂VDSAT/∂VGS 항만 -- ΔVS(body)·ΔVDS 항이 빠짐(LUT 축 VS·VDS 있음, 원칙 1 물리 정합; 후보 문서 유래).
- m9. O-213 결정 행 원문 'SF-1 커밋 순서 로더(R9 포함) → 선언 → 식 → 소비자'를 계획(P:425·P:2305)은 K13v2 조건 1·2대로(R9 = PD-1, PD-1 로더 커밋도 sha 불변) 반영했다 -- 정본 판정과 맞지만 결정 행 문언과 다른 해석이므로 해석 표지 한 줄(원칙 24).
- m10. 표 #19 'LA-1 → SB-1(LA-1과 통합 병합)' -- 순서 고정인지 통합 병합인지 문언 모호(SB-1 선행 칸 P:1295는 LA-1 뒤).
- m11. 표 #20 소비 쪽 'offset-trim LUT 확장 작업'은 card가 아님 -- 받을 card(TR card 착수 조건) 명시.
- m12. P:11 Status에 커밋별 경위가 계속 누적(원칙 25 -- 기존 관행이나 이번 판도 추가).

## 검사별 결과
1. 결정 반영(O-202~O-213): 결정 행(P:415~425)·N3.6 정본·N3.8·card 문언은 대가·원래 취지와 다름 포함 대체로 원문과 맞음(O-203·O-204 표지 (a)(b)·U-122 별도, O-205 (4) 묶음 반영·'묶음 결정 대기' 표지 0, O-206 4/13 대가, O-207 (다) 기각, O-210 RR-1/2/6/7, O-211 조건 넷·RR-5, O-212 LUT 확장 = TR 착수 조건, O-213 SF-1·PD-1·R7). 발명: G2-a triode 확대(M3). 작성자 판단 판정: dc_window_cfg 하나 = 맞음(O-204 조건 점검, 측정 구성·경계 행·여유 0·'추정'이 같아 정의 동일) / ΔV writer 자리 = 조건부(층 순서 M3) / `judged_by` 소유 EO-1 = O-183(생산 = 소비 card)로 맞음, 다만 ICMR 칸과 원칙 불일치(M4) / ICMR 기준 로더 SF-1 = 틀림(M4) / K_max 첫 교차 design 위임 = 조건부(m7) / '확정 지목' 왕복 삭제 = 한 단계 판정의 논리적 귀결, '사용자 확인 필요 항목'(P:12) 표지 있음 -- 적절 / PD-1 신설 = O-213 (s2) 정의('(가)이면 새 card')대로 맞음 / 'R9 포함' 해석 = K13v2 정본과 일치(m9 표지).
2. 옛 정의 잔재(엄격 기준): 정본처럼 읽히는 잔재 = M1(OP 7자리·GC 1자리)·M2(HC 9자리)·m1·m2·m3·m5. 실측 `stale_strict_summary.txt`(C 162건 수작업 분류 -- 다수는 floorplan·`gain_ss_db` 일반 용례·offset-trim '2단계'(trim 2단계 흐름) 등 다른 뜻), `kw_*.txt`.
3. 결정·정본 간 모순: M1·M2·M3·M4, m2.
4. graph 정본: ΔV 필드(writer 하나·소비자 G2-a·card EO-1 -- 층 순서 M3), `judged_by`(EO-1 생산·소비), ICMR 기준 spec 칸(생산 card·첫 소비 순서 미정 M4), R10 두 필드(PD-1 writer = 선언 로더, 소비자 넷 READS), `dc_window_cfg`(writer = 봉인 뒤 측정 구성 블록, 소비자 넷) -- 삭제 필드 `dc_off_current`·`dc_conduction_floor`의 소비자 정리는 P:660·GC:311~312에서 됨, 남은 소비 문언은 M1(GC:347·688).
5. 원칙 19: 낡은 card 표(P:1319~1338)는 IT-2c/2d/공통·IT-2a/2b·IT-1/IT-0b·EO-1·DE-1·LA-1·SB-1·WB-1·SF-1·DR-1·HC·GC·OP-5·TR 포함, offset-strategy 누락(m3). design 후속 정정 표 누락 M5. 표 #19·#20 = m10·m11.
6. 원칙 25: 계획 본문에 새 측정 수치 유입 없음(측정 토큰 증감 실측 `numbers_out.txt` -- '4/13'·'0/13' 범위 사실만), PDK 고유 토큰 증가 0(`pdk_tokens.txt`, O-197). Status 경위 누적 m12.
7. history 무손실: 5개 모두 a4d87f1a→ef911010 연산 = insert만, '새 파일 − 삽입 줄 = 옛 파일' 바이트 일치 True, CRLF 수 불변(`hist_bytes_out.txt`); b17957d3의 1줄 삭제는 fe53f211이 복원(커밋별 numstat 같은 파일). 계획에서 지운 150자 이상 구간 37개 모두 history에 보존(1개는 표 escape `|`→`\|` 차이, `moved_check_out.txt`·`moved_427.txt`).

## git 상태 확인
- 시작: chip-design-skills `git status --porcelain` 69줄 md5 f76d6870169eade7b1b1a6a8d936e435, plan-v6386 깨끗(0줄). 끝 상태는 보고 본문에 기록.

verdict: Major 5
