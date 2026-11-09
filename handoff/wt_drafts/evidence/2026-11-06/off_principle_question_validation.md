verdict: Major 0
gate_sha256: 83739f6b250e496a09075c1754cb66add2f0e0d0382821fc6fd414d6197776b5

# Q-OFF off 원리 질문 문서·점검 파일 독립 검증 (2026-11-06)

검증자 = 질문 게이트 독립 검증 agent(질문 문서·점검 파일·감사·모순 점검의 작성자 아님).

대상:
- 질문 문서 `wt/_drafts/evidence/2026-11-06/off_principle_question.md`(sha256 203a0657…3569, 실측 일치)
- 점검 파일 `wt/_drafts/ask_gates/2026-11-06_QOFF.md`(sha256 83739f6b…76b5, 실측 일치, header Q-OFF)

원 파일 = WB-1 브랜치 머리 f1dd8f52(v6.38.27). 계획·design 40은 `git -C … show HEAD:`로 뽑아 읽었다(`C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_val16/plan_head.md`·`d40_head.md`). 엔진 인용은 원칙 8에 따라 외부 사실과 재작성 범위로만 쓴다.

실행(모두 `C:/Users/HSLEE/AppData/Local/Temp/la1s_wb1_val16/` 안):
- 훅 `evaluate`: `check_gate_qoff.py` → `gate_qoff_1.txt`
- 원본 PDF 쪽 확인: `book_off.py` → `book_off.txt`
- 계획 줄 문맥 추출: `p2058.txt`·`cf.txt`
- grep·sed

ngspice·pytest·커밋 0. 대상 두 파일 수정 0.

## 결론

Major 0, minor 4.
- 사실 문장은 원 파일·LUT 실측·원본 PDF와 맞는다.
- 점검자 지적 (a) 용어, (a)-4 tol 범위 한정, (a)-6 U-122, (a)-10 `current_box`, (b), (c), (d) 부호 판정 근거, (e) KCL 0 예외 두 조건, (f) Q2·Q3 위임이 모두 반영됐다.
- 반영분에서 새 결정 모순은 나오지 않았다.
- 형식은 훅 기준을 통과한다(남은 오류 = '검증 파일 없음' 1건, 이 파일로 해소).
- 권고 (가)에 물리·graph 위반이 없다.

## 1. 사실 대조

| # | 문서 주장 | 원 파일·측정 | 판정 |
|---|---|---|---|
| F1 | 결정 층(O-202·O-203·O-205 (1)·O-207·O-212·U-69 철회 :2822)은 '문턱으로 꺼짐을 가르지 않는다' 쪽 | `user_decisions.md` O-202(:1183)·O-203(:1184)·O-207(:1188)·O-212(:1193). 계획 :2822 U-69 "전도 여유 행은 봉인·S_d·탐색 어디에도 두지 않는다", :686 정본 (9) S_d | 맞음 |
| F2 | `_conduction_floor`(`search/cell_floor.py:53-85`) = 옛 봉인 9 ε 식 | `cell_floor.py:53-85`: VGS = 0 마디 I_off와 `gm·tol_V` 비교 근(:75 `log_gm + log(tol) − log_id[zero]`). :70 `if not tol: continue`(정의된 항만) | 맞음 |
| F3 | `_conduction_ok` ε 항(`lut/derived_fns.py:39-50`), 'VGS = 0 마디 = 꺼진 소자' | 함수는 **:41-51**이다(:47 `off = ID[VGS 첫 마디]`, :50 `gm·tol ≥ off`). 머리 docstring :9 "VGS = 0 마디는 꺼진 소자라 이 조건이 뺀다" | 맞음(줄 ±2, m1) |
| F4 | design 40 :345·:1448 '삭제' | `d40_head.md:345` "`conduction_floor` 삭제(O-205)", :1448 "폐기: 칸 정점·전도 하한으로 θ 상자를 조이는 경로" | 맞음 |
| F5 | 표 9행(:662)·oracle 정본(:290·:683)·O-210 RR-2가 부호 결과를 '꺼짐'이라 부름 | :662 "꺼짐 = 선언 방향 ID ≤ 0", :683 "ID ≤ 0 = 크기 무관 FAIL … 포화·꺼짐이면", :290 DEC-90 "꺼지면 FAIL" | 맞음 |
| F6 | LUT: VDS > 0에서 ID ≤ 0 0/423360, 포화 통과 칸 ID 최소 nfet 3.2e-19·pfet 2.9e-26 A, VGS = 0에서 8460/8820 포화 통과 | `la1s_off40/sat_vs_sign.out.txt` (a)(c)(d) n·p 행 | 맞음 |
| F7 | 부호 판정의 역할: 엔진 정의역 조건 / oracle RR-2 FAIL 그대로(순방향 포화 FAIL과 함께, 역방향·VDSAT 열 없음에서 유일) / triode 선언 | 점검 (d) '고칠 방법' 문언과 같다. :683 원문 | 맞음 |
| F8 | Q2: :2058에 `ln_idu_floors` 이미 배정, :2114 완료 8, :1368 GC-7 이중 배정 | `p2058.txt`: :2058 O-207 묶음 "`search/cell_floor.py` `_peak_floor`·`ln_idu_floors`와 호출(`layer0_center.py`, `slsqp_outer.py`) … `lut/derived_fns.py` `_conduction_ok` 분지". :2114 "O-207 묶음 완료: `CON_INVERSION`·`_peak_floor` 0"(`_conduction_floor` 이름 없음). :1368 GC-7 "`conduction_mask` 전도 술어·`_peak_floor`" | 맞음 |
| F9 | `sctx.cell_floors` 삭제 가능(Q2) | 비test 소비자 = `cell_floor.py` `_peak_floor`(:37-50)·`_conduction_floor`(:55-85)뿐이다. `_one_var_writers`는 graph 필드를 읽는다(:86-88). 둘 다 O-207 묶음에서 지워지므로 소비자 0이 된다 | 맞음(직접 grep) |
| F10 | Q3: library triode 선언 0/13 | 감사 인용 | agent 인용(판정 영향 없음 -- 현행 유지 안) |
| F11 | ⑧ 원본에 off 판정 기준 없음(6장 248쪽 근사 off, 2장 44쪽 누설 제거) | PDF 직접: `6 practical-circuit-examples-ii.pdf` PDF 23 = 책 248쪽 "about 10% of the current flows in the device that is approximated to be 'off' during slewing", `2 basic-transistor-modeling.pdf` PDF 24 = 책 44쪽 "we have removed the junction leakage component". 점검 파일 ⑧ 경로 `la1s_book33/6 practical-circuit-examples-ii.txt` 실재 | 맞음 |

## 2. 점검자 지적 반영

| 점검자 지적 | 질문 문서 | 판정 |
|---|---|---|
| (a)-1 용어 모순: 부호 결과 '꺼짐' 대 원리 '꺼짐 = 선언 전용' | 원리 문장에 "이름은 '꺼짐'이 아니라 '비전도(방향 위반)'로 바꾼다(표 9행·oracle 정본·O-210 RR-2 용어 교체, 판정 내용 불변)". 질문 문언(§5)과 원래 취지와 다름(§3)에도 있다 | 반영 |
| (a)-4 tol 금지를 off·전도 분류에 한정(O-240 남은 자리와 분리) | 원리 문장 괄호 "이 금지는 off·전도 분류에만 해당하며, 봉인 1·2·3·8이 쓰는 수치 자기 정합 허용 tol(O-240)과는 별개" | 반영 |
| (a)-6 U-122를 닫지 않음 | "약반전 VDSAT(U-122)는 이 원리로 닫지 않는다" | 반영 |
| (a)-8 O-15 (A) `conduction_mask` 철회 근거 | §3 "graph-consumption `conduction_mask` 신설 철회"·§4 "O-205·O-229 7 권한" | 반영 |
| (a)-10 `current_box` 거부 삭제 = 값 동일 실측 선행 | §3 마지막 줄 | 반영 |
| (b) :2058·:2114 이름·`git grep` 0, :1368 이중 배정, A-144 부분 철회, A-139 (4) 과도기 예외 | §4 Q2, §3 | 반영(고칠 자리 일부 누락 m2) |
| (c) ε 항을 LA-1 O-207 묶음으로 | §4 Q2 | 반영 |
| (d) 부호 판정 근거 = 'RR-2 FAIL 그대로', '사유 표지만' 금지 | §1 다섯째 줄, §3 넷째 줄. '사유 표지' 표현 0 | 반영 |
| (e) KCL 0 예외는 표 9행 인용, 다리 밖 구조적 0 = 정지 | 원리 문장 "KCL 항등 0 전류 MOS는 표 9행 정의를 인용한 예외이고, 다리 밖 구조적 0 전류(`mos_zero_current_structural`, DR-1 대기)는 정지" | 반영 |
| (f) Q1 사용자, Q2 위임(O-205 근거 기록), Q3 위임((가)일 때) | §4 "O-205·O-229 7 권한", Q3 현행 유지 | 반영 |

## 3. 결정 간 모순 (반영분)

| 결정 | 관계 | 근거 |
|---|---|---|
| O-202·O-212·O-53 B1(`off` 선언, trim) | 정합. 원리가 사용자 제안의 trim 예시와 같다 | O-202·O-212 행 |
| O-203·O-205 (1)·O-207·U-69 철회 | 정합. 원리가 이 결정들을 일반화한다 | :686·:2822 |
| O-205 (2)·O-210 RR-2(oracle 부호 FAIL) | 정합(판정 내용 불변, 용어만 교체 -- 사용자 질문에 포함) | :683 |
| O-200·O-240 | 정합. tol 금지는 off·전도 분류에 한정된다(봉인 tol 사용과 분리) | 원리 문장 괄호 |
| DEC-87 `on_mask`(부호 조건) | 정합. 크기 문턱이 아니다 | -- |
| O-15 (A)(술어 하나·캐시 제거) | 정합. `on_mask` 하나 + `sctx.cell_floors` 삭제(F9로 소비자 0 확인) | O-205 원래 취지와 다름 '대상 소멸·축소' |
| A-139 (4)·A-144 | 정합. 과도기 예외를 기록한다(상자를 넓히는 쪽, 판정 아님) | §3 |
| O-204·U-122 | 정합(열린 결정 유지) | 원리 문장 |
| O-229 1·7 | 정합. 물리 위반(tol이 VGS 하한을 정함)을 LA-1에서 지운다. 위임 범위 안 | §4 |

새 모순: 0.

## 4. 형식 (원칙 26)

훅 `evaluate` 실측(`gate_qoff_1.txt`) 결과:
- 통과: frontmatter(kind recommend, headers Q-OFF, candidate_sha256 일치), 절 4개, '## 권고 확인표: Q-OFF' ①~⑩, 근거 칸 접두, ⑩ 실측 경로, 금지어 0, 인용 경로 실재(⑧ `la1s_book33/6 practical-circuit-examples-ii.txt` 포함).
- 남은 오류: 'validation 파일 없음' 1건.

## 5. 물리·graph (권고 (가))

물리:
- 증폭기 정상 동작에서 선언 없는 소자는 전도한다. 깊은 약반전(ID 1e-19~1e-26 A)도 채널 전류가 있는 전도이고, 그 기능의 충분성은 spec 제약이 판정한다.
- 원본도 슬루 중 'off'로 근사한 소자에 전류 10 %가 흐른다고 적었다(248쪽). 문턱 분류가 물리 경계가 아니라는 근거다.
- 부호 판정(ID > 0)은 ln IDu·gm/ID 정의역 조건이라 물리 정합과 맞는다.

graph:
- `conduction_mask` 신설을 철회하므로 `on_mask`와 같은 정의의 둘째 필드가 생기지 않는다(규칙 3).
- `sctx.cell_floors` 캐시가 삭제된다(규칙 2). 새 필드·cache 0.

위반 0.

## minor

- **m1 (줄 번호)**: `lut/derived_fns.py:39-50` → `_conduction_ok`는 :41-51이다(점검 파일 ①도 같다).
- **m2 (고칠 자리 누락)**: Q2·원래 취지와 다름에 다음 계획·design 문언 세 곳이 빠졌다. 감사 `off_rules_audit.md` G10·C10이 이미 짚은 자리다. 점검 파일 bkit 계획 칸('N3.6 표 9행·정본 (5)(7)(9)·LA-1 O-207 묶음·GC-7')에 더할 것.
  - (i) **P:2651 LM-1e 3b (ii)**: "`_conduction_floor`의 '정의된 항만' 집계 → None … 존폐는 GC-7 몫". A-144 전도 하한 몫을 철회하면 이 문언을 'LA-1 O-207 묶음에서 삭제, LM-1e 범위 밖'으로 고쳐야 한다.
  - (ii) **P:663 표 10행 '규칙의 범위' (ii)** 탐색 상자 전도 하한 문언(감사 G10).
  - (iii) **P:2076** "`sctx.cell_floors`는 graph-consumption GC-7 완료 조건 13 소유(O-15 (A))". Q2가 삭제를 LA-1로 옮기므로 소유 문언도 바꾼다. design 40 :1259도 감사가 짚은 어긋남이다.
- **m3 (정본 (7) 문언)**: 점검자 (c)의 '정본 (7)(:684) "GC-7 -- 술어 = ID > 0으로 줄어듦" → "LA-1 O-207 묶음 -- ε 항 삭제, 술어 = `on_mask`"'가 Q2에 명시돼 있지 않다. bkit 칸의 '정본 (5)(7)(9)'로 묶여 있기는 하다. Q2에 한 줄 넣으면 card 브리핑에서 빠지지 않는다.
- **m4 (triode 영 전류 스위치)**: 원리 문장은 `triode` 선언 소자도 '선언 방향 ID > 0'을 요구한다. DC 전류가 0인 닫힌 스위치(예: 게이트만 구동하는 경로의 pass 소자)는 KCL 항등 0 예외(표 9행)가 받는다. 이 점을 Q3 '현행 유지' 근거에 한 줄 넣으면, 'triode 스위치가 0 전류라 거부된다'는 오독을 막는다. library triode 선언 0/13이라 지금 발동은 0이다.

## 돌린 범위

다음을 했다:
- grep·sed로 WB-1 머리의 계획·design 40·엔진 파일과 결정을 읽었다.
- LUT 실측 출력을 직접 읽었다.
- 원본 PDF 2쪽(책 44·248쪽)을 추출했다.
- 훅 `evaluate`를 1회 불렀다.

ngspice·pytest는 돌리지 않았다. F10(triode 0/13)은 감사 인용이다.
