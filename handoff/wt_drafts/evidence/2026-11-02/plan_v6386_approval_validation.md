# 계획 v6.38.6 검증 57(e71aa597) + 승인 질문 점검 파일 판정(2026-11-02_PLANAP.md)

- 검증자: 독립 검증 agent(계획 작성자·점검 파일 작성자 아님). 읽기 전용, 저장소·계획·점검 파일·git 쓰기 0.
- 대상 (1): plan/v6386 e71aa597(부모 84e4ec99, 스물셋째 커밋 -- ⑩ R2·R10·R3·R12 + 검증 56 m56-1~3).
- 대상 (2): `wt/_drafts/ask_gates/2026-11-02_PLANAP.md`(sha256 02f351a22208b4c9a4928d4910c4929f9fa371e6d9e96c3f107a6172424272ed, headers PLAN-AP·C4-Q2, candidate_doc = 계획 gain-budget plan.md 작업 트리 sha a58db22f…7ec7a).
- 실측 `wt/_drafts/evidence/2026-11-02/plan_v6386_v57/`:
  - `win.py`→`win_out.txt`, `hist_check.py`→`hist_check_out.txt`
  - `ngcc_devs.txt`(topology.json 직접 파싱)
  - `run_gate_eval.py`→`gate_eval_out.txt`(hook `ask_gate.evaluate` 직접 실행)

## (1) 계획 검증 57 -- e71aa597

### 변경 판정(바뀐 줄 13곳, `win_out.txt`)
- **⑩ R2**(O-205 (4)·O-206 묶음 해제): P:11 Status·P:427 O-215 행·P:731 N3.8에 '원래 취지와 다름'으로 적혔다. 내용은 O-206은 O-205 R0의 성립 조건이었는데 O-215가 풀었고, 위험은 성능 spec과 재검토 항목 (9)로 넘어갔다는 것이다. O-215 원문의 'O-206 부분 철회·O-205 R0 유지'에서 나오는 귀결 기록이고, 새 결정은 아니다. 맞음.
- **⑩ R3**: 'O-54(O-202 (1)·O-204·O-205 (3)으로 고친 판) 복원'이 P:427·P:731에 들어갔다. 맞음.
- **⑩ R10**: P:12 미룬 결정 (8)에 '정하는 주체 = 사용자(O-214 (i) 지목 방법이 바뀔 수 있음)'가 들어갔다. 맞음.
- **⑩ R12**: LA-1a 완료 조건 5의 '비θ 갈래 0'은 스물한째 커밋에 이미 있다(검증 56 확인).
- **m56-1**: P:731·P:1708에 '그 칸이 master에 들어가는 병합에 엔진 쪽 규칙이 함께 든다(칸과 규칙이 같은 병합 -- O-183)'가 들어갔다. 해소.
- **m56-2**: OP:18 Status 괄호에 O-215(임시) 정정이 적혔다(0.6.25 여섯째 커밋 -- history 실재). 해소.
- **m56-3**: P:1962·1967·1991·2001·2003, HC:158의 `_repair`·`_repairable`이 '수리 함수(범위 6 -- 옛 꼴, O-153)'로 바뀌었다. 해소.
- 결정 발명 0: 새 배정·새 규칙이 없다. 위 문언은 모두 결정 원문의 귀결 표기이거나 이름 정정이다. fail-open 0.

### history 무손실 -- 삭제 0
- gain-budget(15행)·headroom-chain·oracle-portability(각 1행)는 insert만이다. '새 − 삽입 = 옛' 바이트 일치 True, CRLF 불변이다. 다른 3개는 변경 0이다. 계획에서 지운 60자 이상 연속 구간 0(`hist_check_out.txt`).

### Minor
- m57-1(범위 밖이지만 같은 계열): LA-1 완료 조건 1 (v)(P:2001)의 'base는 최소형 max-min 점을 출발점으로 냄 -- red'는 base 서술이 낡았다. LA-1의 base는 LA-1a 병합 뒤라(P:1997) 최소형 max-min 경로가 없다. red 판정의 base 문언을 'LA-1a 한 규칙 출발점'으로 고치기를 권한다. 정의 변화는 없다(test design 착수 때 확인).

## (2) 점검 파일 2026-11-02_PLANAP.md 판정

### 사실 대조
| 점검 파일 주장 | 대조 결과 |
|---|---|
| 계획 HEAD e71aa597, base 0acb5e63, 커밋 24개 | 맞음(`git rev-list --count 0acb5e63..e71aa597` = 24, 조상 관계 확인) |
| candidate_sha256 a58db22f…7ec7a | 맞음(작업 트리 파일 sha256 실측 일치) |
| 미룬 결정 (1)~(6)·(8), 재검토 (9) | 계획 P:12와 일치. (5)는 C4-Q2 자체(완료 대상 조건), (7)은 미룬 결정 아님 -- 질문 문언 '승인 = (1)(2)(3)(4)(6)(8) 확인 아님'은 정확 |
| O-215 = 임시·번복 가능 | 질문 요지·원래 취지와 다름 절에 표지. 결정 원문(UD 끝 행)과 일치 |
| 원래 취지와 다름(O-215: O-206·O-211 부분 철회, O-205 (4)·O-206 묶음 해제, O-54 고친 판 복원; O-214: LA-1 분리·sf 봉인 재현·R7 가드·R-a 자리) | 계획 P:426·427과 일치. ⑩ R2·R3 조건 충족 |
| 검증 56 Major 0, ⑩ 확정 모순 0·금지 항목 0 | 맞음(`plan_v6386_validation56.md` verdict, `plan_v6386_consistency.md`:95·96) |
| 순환 0, LA-1a 조상 ⊆ LA-1 조상 | 맞음(검증 55 재실행 `plan_v6386_v55/cycle_rerun_out.txt`) |
| C4-Q2 ① M8·M14 gate = V1(M2·M4 drain), source = gnd, 묶음에 diode 없음 | 맞음 -- topology.json 직접 파싱(`ngcc_devs.txt`): M8 {gate V1, drain NP, source gnd}, M14 {gate V1, drain Vout, source gnd}, M2·M4 drain = V1; 둘 다 gate ≠ drain |
| 단계 A 정지 문자열 `dc_role_unresolved_group M14,M8` | agent 기록 `icmr4/ngcc_3stage_ff.md`:14·58과 일치(agent 인용) |
| C4-Q2 ⑧ 원문 Fig. 1(c) PDF p.2, gmf2 = gm2 p.21, single transistor p.22 | 내용 맞음 -- `paper.md` p.2(저널 21쪽) 135~140·181행 Fig. 1·'gmf2 = gm2', p.3(저널 22쪽) 649행 'implemented by a single transistor'. 단 p.21·p.22는 저널 쪽 번호(PDF p.2·p.3)라 표기가 섞였다(g-1) |
| C4-Q2 ⑨ 물리 결정자 | 맞음 -- V1은 1단 고임피던스 출력이고, M8 = 2단 CS(gm2), M14 = FF2(gmf2, V1 → Vout). 둘은 같은 VGS 묶음이지만 bias 기준(diode)이 아니라 신호 소자이며, 원문 NGCC 조건 gmf2 = gm2와 맞다 |

### 형식 -- hook 직접 실행(`gate_eval_out.txt`)
- `ask_gate.evaluate({PLAN-AP, C4-Q2})` 결과는 오류 1건이다. 'validation 파일이 없음(이 파일)' -- 이 검증 기록이 생기기 전이라 예상된 것이다.
- 그 밖에 5묶음 절, '## 권고 확인표: PLAN-AP'·'C4-Q2' 두 표의 ①~⑩, 근거 칸 세 범주(실측(/agent 인용/해당 없음(), ⑩ 실측 경로(measured_only), 금지어 5종 0(본문 전체 grep도 0), 근거 칸 경로 실재(13개 별도 `ls` 확인), candidate sha 일치까지 모두 통과했다.

### 승인만 해도 틀린 결정이 되지 않는가 -- 그렇다(조건부)
- 계획 승인이 미룬 결정을 확정하지 않는다는 문언이 질문 요지와 계획 P:12(1) '계획 승인은 (1) 확인이 아니다'에 있다. 미룬 결정은 각 card 착수 조건이라, 결정 없이 해당 card로 넘어갈 길이 없다.
- O-215는 임시이고, 번복 검토 조건 (9)가 LA-1a front 실측에 묶여 있다.
- LA-1a는 (8)(목표 이득 출처 -- 정하는 주체 사용자)이 design 착수 조건이다. 승인 뒤 바로 design 단계로 가도 그 결정을 건너뛰지 않는다.
- C4-Q2는 회로 해석 사실(원칙 14·15 -- 사용자 몫)이고, 물리·원문 근거가 직접 확인됐다.

### 점검 파일 Minor(질문 문언 개선 권고 -- 승인 판정은 막지 않음)
- g-1. C4-Q2 ⑧ 쪽 번호에 '저널 p.21 = PDF p.2, 저널 p.22 = PDF p.3'을 함께 적기를 권한다. agent 기록(ngcc md:37)은 이렇게 적었다.
- g-2. '원래 취지와 다름' 절에 미룬 결정 (8)의 가능성을 한 줄 더하기를 권한다. 출처가 `gain_target_first`가 되면 O-214 (i)가 지목한 방법(DEC-71 (4)(b))이 바뀐다(⑩ R10 '원래 취지와 다름 후보 표지'). 질문 요지에는 '정하는 주체 사용자'만 있다.
- g-3. C4-Q2 대상 파일 `ngcc_3stage_ff.structure.json`은 지금 저장소에 없다(library에 nmcnr·current_reuse 두 개만 있음). '선언 = 새 structure.json 생성(topology_hash·rule_hash 포함)'이라는 사실을 질문에 밝히기를 권한다.

## git 상태 확인
- 시작·끝 같음: chip-design-skills `git status --short` 70줄 md5 8c63c9a16d4a51505e1bea83a5cd2e2d, plan-v6386 0줄 HEAD e71aa597. 점검 파일 sha256 시작 = 끝 = 02f351a2…2ed. 쓴 파일 = 이 보고서와 `plan_v6386_v57/`(저장소 밖).

verdict: Major 0
gate_sha256: 02f351a22208b4c9a4928d4910c4929f9fa371e6d9e96c3f107a6172424272ed
