# design v1.16.1 진행 기록 (검증 1 + design↔계획 gap의 design 쪽 반영)

- worktree: `wt/design-v115` (브랜치 design/v115), 시작 HEAD `bc3b3572` (design v1.16.0), 계획 = 같은 worktree v6.38.5(`0acb5e63` 조상, 계획 파일 무변경 확인)
- 입력: `design_v116_validation1.md`(M1·M2·m1~m9), `design_v116_plan_gap.md` §6 M2~M7·M9~M12·경미·§2 부분 반영 5건, parts `gap_gb1..5`·`gap_sub` 누락·다름 행
- 오케스트레이터 판정: M1 = (가) 경계·sources만, M2 = 불변식 단언 + toy, gap M8 = 'Δ 자리 = 계획 결정 대기', gap M1·J1·J9·J14 계획 근거·P1~P3 = '계획 v6.38.6 대기' 표지만

## 진행

### 1. 검증 1 M1·M2·m1~m9 (+ gap M8 같은 단락) -- 첫째 커밋
- M1: `GuardRow(g_lo, g_hi, sources)` -- 40 §2.4.8 R7 행, 41 E12·J2·§6.4-2a v1.15.1 (a)·§6.7-4 (ii)·§6.7-11 writer, 42 D-TB1c(+층 0 후보 L ≠ 출발 L toy)
- M2: 41 §4.7-1 2 `TieBreak(w4_root)` → 불변식 단언 `dc_colour_not_unique`(새 이름, 근거 표지), J7 대안표(⚠ 원칙 8·10), 42 D-IT1b 신설(MISS), card 귀속 = P6 계획 개정 필요
- m1 `floor_k`→b_k·'바닥'→'분해능', gap M8 Δ 언급 삭제 + 'Δ 자리 = 계획 결정 대기'
- m2 41 §9 축소 격자 test = library 13, 40 CMP-1 괄호 13
- m3 41 §4.2 A9 고정 B 값 출처 = `loop_dep.b_ln_idu`(DEC-104 (3)(c))·KVL 등식·`start.point`; B 출발 L 칸 자리 = 열린 점(41 §5.12.8)
- m4 P4 추가, J1·J9·J14 '계획 근거 = 계획 v6.38.6 대기', P1~P4 대기 표지
- m5 D-TB1d concept 네 갈래 toy, m6 40 R13 행 sizing 안 모듈 층, m7 history 일곱째 커밋 줄, m8 41 L11 (l-ⅰ) 정준 순서 문언, m9 (d) O-183 대체 표지
- 사고 기록: scratchpad 공용 루트의 `apply.py`(이전 세션 파일)를 덮어씀 -- 이후 도구는 `scratchpad/v1161/`로 옮김
- 커밋 `62a91b72`

### 2. gap 결정 문언 (M2·M3·M4·M9·M10·M11 + 경미) -- 둘째 커밋
- M3 41 §4.7 (S4-가)/(S4-나) → (S4-나) 확정(표 #13), '늦게 병합되는 card'·'VB-1이 먼저 병합되면'(41 §4.7·40 §3.8-8 표) 삭제, `dc_sat_v` `off` 갈래 = HC-S가 EO-1 뒤(표 #7), 41 §6.7 '아니면 LA-1 때 writer를 옮긴다' 삭제
- M2 40 card 표 WB-1 선행 HC-S(표 #6·#11) + HC-1+GC-8 의미 겹침 완료 조건(계획 N6.1 WB-1 행 B5), Q-T0 13회로; SB-1 선행 DE-1(표 #1)
- M9 41 §6.8-1 거짓 거부 → 기록·원인 분류(정의 원인 결함 0건, O-178 (5)), 41 §9 행·42 D-R10
- M10 영점 R 비θ 갈래 0(표 #12): 40 §3.1-1·E-15 행·사유 목록, 41 §6.5·§9, 42 D-LA1G
- M4 40 §3.1-1 상자 규칙: 선언 상자/적용 상자(`search_domain` writer), 보상 C 하한 C_min·상한 면적 제약, spec min 삭제, 결합 C = DR-1, 9항목 = 이관 전 실측 표지; capm.1 원본 경로(40 §7); 42 D-TBX. **계획 개정 필요 P8**: 보상 C spec `theta_bounds.max` 처리 문언 없음
- M11 '9회로' → library 13회로(앞으로 할 실행·완료 조건·test 자리 32곳 + M3 안 2곳; 실측 기록 문장은 그대로)
- 경미: DF-28 fail-closed, erfc·rfc 경로 library·옮긴 4회로 판정값 문언, 옛 gm/ID 좌표 9자리, 41 R-1′ = HC-1, 41 memo, RS-1 DEC-71 (6), 42 DEC-104 행, §10.5 엔진 실패·판정 보류, oracle (ii) Q-S9 제외·forced 경고, CPG-1 이관 전 기준선
- 커밋 `9f425a20`

### 3. 누락 반영·표지·머리 판 -- 셋째 커밋
- M7 40 §2.4.5 `register_eval`·`iter_evals`((seq, EvalKey 정준 순서))·`eval_entry_count`(정의역 안 평가 항목 수, `entry_count`와 다른 양), 결정성 행 모순 정정
- M6 40 §3.8-3 R9 class-AB 결합 gate 규칙(계획 R-C 그대로), 극단 상태 VSB·VDS 입력 = 열린 점(DE-1 design, 물리 유도 필요)
- M1 40 §3.1-1·card 표 SF-1 행 = 계획 v6.38.6 대기 표지(같은 문서 안 '파일 겹침만' 모순 정정)
- card 표: CL-1(착수 조건 전 -- Δ·목표·재풀이·U-122 design 안 씀)·GL-1·DR-1(design 절 없음 → P7)·PW-1a(P9) 행 추가, TB-1(GC-B7·완료 (5))·HC-1((g) H9·(h) H17)·WB-1(완료 (3) E-2)·LA-1(M-LA16·CL-1 → LA-1 완료 → 단위 11·M-LB1) 보강
- 41: LA-1 완료 5 원인 항목 'R6 재개방 -- LA-1', §6.5 R-D E-2 조건부 기록, §9 LA-1 12 C 열 test 행, §5.12.8 P5~P10·열린 점 (1)~(3)
- 42: D-DR1 신설 MISS, D-CL1 착수 조건, D-V9 v6.38.6 대기, D-SF1d Q-CA1, §4 집계 325(기계 계수 §3 = 225행 MISS 166 확인)
- M12: 40 §2.4.12 Q8 행 조건 (2) 자리 표지 + offset-strategy design §10 낡음 표지(그 문서 판 불변)
- 머리 판 v1.16.1(40·41·42), 옛 Status → 이력 H40-35·H41-35·H42-05, 경위 H40-36
- 줄 끝: git autocrlf로 작업 사본이 CRLF로 바뀌어 섞임 → 40·41·42를 LF로 정규화(색인은 LF, 내용 변화 0)
- 잔존 grep(옛 이름 13종): 남은 줄은 모두 '옛·삭제·정정' 표지 줄
