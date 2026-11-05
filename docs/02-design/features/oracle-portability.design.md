---
template: design
version: 0.4.10
plan: ../../01-plan/features/oracle-portability.plan.md
plan_version: 0.6.31
---

# oracle-portability Design Document (card OP-0)

> **Summary**: 계획 `oracle-portability.plan.md` v0.6.31(상위 위임 A-84, 독립 판정 전); 이전 기준 v0.6.30(상위 위임 A-80, 판정 PASS A-82); 이전 기준 v0.6.29(상위 위임 A-75, 판정 PASS A-77); 이전 기준 v0.6.28(상위 위임 A-62, 독립 판정 Major 0, 승인 위임 A-65); 이전 기준 v0.6.27(상위 위임 A-53·A-54·A-58, 독립 판정 Major 0, 승인 위임 A-58); 이전 기준 v0.6.26(승인 = 사용자 결정 O-226 위임 A-25, plan/v6388 HEAD `28ec6bf6`; 대조 기준 master `c0b41eee`); 이전 기준 v0.6.25 = O-216 `e71aa597`, v0.6.17 = O-86 `e87092b3`(계획 병합 plan/o85), v0.6.16 = O-83 `dae968ec`(병합 기준 master `8c2357bc`); 그 전 기준 v0.6.15 = O-80 `93a9ff82`(계획 병합 plan/o78), 그 전 기준 v0.6.14 = O-70 (2) `f4d89a23`(계획 병합 `1b4a8536`), v0.6.13 = O-65 `7675f71b`, v0.6.11 = O-60 `b9af2d6f`, v0.6.10 = O-57 `d6bd02b1`)을 오라클 설계로 옮긴다. 계획의 결정은 사용자 결정 O-1~O-224 가운데 이 기능에 닿는 것(§1.1), L-1~L-3, D-1~D-9이다. 이 문서가 정하는 것은 다음과 같다.
> * **OP-3 입력 스키마 계약**(gain-budget card EO-1 생산자의 계약, A' 손분석 입력과 같은 스키마 -- §11.0~§11.4)과 G-18 확장 칸(OP-5·headroom-chain HC-O·OP-10이 더함, §11.6), 오라클 실행 결과 계약(§11.7)
> * metric 측정 절차(계획 N3.9 -- 범위·합격 판정 전도 기준, swing·ICMR, 계통 offset, 불일치 σ의 `.tf` A: OP-5 / 슬루: OP-10 / 전력: OP-11, §21)
> * 3층 구조(코어 / 시뮬레이터 어댑터 / PDK·오라클 기술자)의 파일 분할과 import 금지
> * 회로 IR, 해석 요청, 정규화 결과의 형식
> * 어댑터 능력 선언 스키마
> * 오라클 기술자 스키마(엔진 선언 sha256 참조, D-9), 기하 단위·병렬 배수 전달 규칙(O-6 D-b), 네이티브 MC 켜는 법과 분포 값 위치(O-6 D-a)
> * 능력 확인 PC-1~PC-10의 벤치·규칙·기록 형식
> * 결정적 섭동 진단 경로의 배선
> * 옛 코드 삭제 목록과 대체 배선표
> * 완료 조건별 test 목록
> * 상위 문서 개정 문안(계획 N3.7)
>
> **Project**: chip-design-skills (analog-gmid-design skill) · **Author**: Claude Code (design 작성자 역할)
> **Status**: **design v0.4.10 -- DUT 저항 RC 극점 실측을 OP-5 판정 묶음으로(§10.6·§18.1·§20, 상위 위임 A-94)** 이전 판: **design v0.4.9 -- OP-7 어댑터 조각 + OP-5 card 결정 반영(§5·§7·§7.2·§8.1·§8.3·§10.2~§10.4·§11.6·§11.7·§16·§18.1~§18.3·§19.4·§19.7·§20·§20.1·§21.2·§21.3·§21.5), 계획 v0.6.31 기준, 독립 판정 전, 위임 A-84**(경위 history v0.4.9) 이전 판: **design v0.4.8 -- OP-2 + OP-3 card 결정 반영(§10.2·§10.3·§7·§7.1·§11.1·§11.4·§11.5·§12.5·§15.1·§18.1·§18.2·§19.3·§20·§20.1), 계획 v0.6.30 기준, 독립 판정 전, 위임 A-80**(경위 history v0.4.8) 이전 판: **design v0.4.7 -- §16 LUT 생성 모드 출처를 생성기 기록 bin 이름 대조로 교체, `evidence.source_basis` 칸 추가, 계획 v0.6.29 기준, 독립 판정 전, 위임 A-75**(경위 history v0.4.7) 이전 판: **design v0.4.6 -- §16 선언 미적용 시점 = 적재 거부(상위 위임 A-62 D2), 계획 v0.6.28 기준, 독립 판정 Major 0, 승인 위임 A-65**(경위 history v0.4.6) 이전 판: **design v0.4.5 -- 독립 판정 Major 0, 승인 위임 A-58, 재판정 R1·R2·r6 반영(위임 A-57), 계획 v0.6.27 기준**(경위 history v0.4.5) 이전 판: **design v0.4.4 -- 독립 판정 `wt/_drafts/evidence/2026-11-04/cards_d_validation.md` M1·M2·M4·m12·m14 반영(위임 A-56), 계획 v0.6.27 기준, 독립 판정 Major 0, 승인 위임 A-65**(경위 history v0.4.4) 이전 판: **design v0.4.3 -- card `20261104-op7a`·`20261104-op1b` 멈춤 항목 반영, 계획 v0.6.27 기준, 독립 판정 Major 0, 승인 위임 A-65**(상위 위임 A-53·A-54: §16 저장 자리·W 경계·LUT 생성 모드 출처·묶음 값·`evidence.mode`, §11.5 중첩 meta 대응·sample 입력; 경위 history v0.4.3) 이전 판: **design v0.4.2 -- 검증 `wt/_drafts/evidence/2026-11-03/design_b56_validation.md` M1~M9·재판정 R1·R2 반영, 계획 v0.6.26 기준(master `c0b41eee` 병합), 승인됨(사용자 결정 O-226 위임 -- la1_auto_decisions.md A-26, 2026-11-03, design/op0 `19dd467e`, 독립 검증 Major 0)**(위임 A-21·A-22; 경위 history v0.4.1·v0.4.2). v0.4.0: **개정 초안**(2026-11-03, 브랜치 `design/op0`, 기준 master `c8ecc4e7`, 승인 묶음 ⑤ -- `wt/_drafts/evidence/2026-11-03/la1a_pg/d_questions.md` §5.2). 반영: 계획 v0.6.18~v0.6.25 전체, N7.5 DR-26~DR-28, card OP-0·OP-2·OP-3·OP-7(§20.1 대응표), 상위 O-115·O-116·O-178·O-182 Q-S9·O-202·O-204·O-205 (2)·O-210 RR-2·O-215(**임시 -- 번복 가능**). 남은 사용자 확인: 지목 왕복 삭제(O-214 미룬 결정 (1) = OP-5 착수 조건), §19.2 'v0.4.0 계획 공백' 가운데 열린 PG-2·PG-3·PG-5(PG-1 = A-8로 닫힘, PG-4 = 계획 0.6.26으로 닫힘). 옛 Status 원문 = history v0.4.0(v0.3.10 판 문장 전체).
> **기준**: 코드 인용은 base `6093d07`(worktree `wt/oport-design`)의 `파일:줄`이다. v0.2.4에서 새로 적은 사실은 base `1ba9461`(worktree `wt/oracle-op0-design`)에서 다시 쟀다. 두 base 사이 `O/` 차이는 `O/README.md` 2줄 추가뿐이라(`git diff --stat 6093d07 1ba9461`) 코드 `파일:줄` 인용은 두 base에서 같다. v0.2.5에서 새로 적은 사실은 base `9069e10`(worktree `wt/oracle-op0-v025`)에서 다시 쟀고, `1ba9461`과 `9069e10` 사이 `O/` 차이는 0이다(`git diff --stat 1ba9461 HEAD -- O/` 빈 출력). v0.2.6 사실은 base `52945ce`에서 다시 쟀고, `9069e10`과 `52945ce` 사이 `skills/` 차이는 0이다(`git diff --stat 9069e10 HEAD -- skills/` 빈 출력). v0.3.0 사실(S-37~)은 base `9401e98f`(worktree `wt/design-oracle-eo1`)에서 다시 쟀고, `52945ce`와 `9401e98f` 사이 `O/` 차이는 0이다(`git diff --stat 52945ce 9401e98f -- skills/analog-gmid-design/tools/spice_oracle` 빈 출력) -- 그래서 앞 판의 `O/` 줄 인용은 그대로 맞다. 경로 약어는 계획 N0과 같다: `O/` = `skills/analog-gmid-design/tools/spice_oracle/`, `E/` = `skills/analog-gmid-design/gmid_engine/`, `A/` = `skills/analog-gmid-design/assets/`. 계획 인용은 `P N3.5`, `P D-7` 식으로 쓴다.
> **이력**: [oracle-portability.design.history.md](oracle-portability.design.history.md)
> **v0.4.0 읽는 규칙**: 정본 절 = 이 판이 다시 쓴 §21.0~§21.3·§21.5 3단계·§21.6·§21.7 일부·§11.6·§11.7·§7(v0.4.0 행)·§7.2·§8.3 끝·§10.6 끝·§12.8 끝·§16·§18.1 끝·§18.3 끝·§19.2 끝·§19.4 끝·§19.7·§20·§20.1이다. **`[낡음 표지 v0.4.0]`를 단 줄의 옛 전도·2단계·지목·ICMR 구성 문언은 기록이고 정본 절이 이긴다**(계획 머리 '상위 O-202~O-212 전파'와 같은 규칙). 옛 줄의 '§21.2 2단계 (0)'·'반전 입력 포트' 인용은 §21.6 0단계로 읽고, '§21.2 2단계 (a)~(e)' 인용은 ICMR 쪽 대상 소멸이다. 정의 정본은 언제나 gain-budget N3.6·N3.8이다.

---

## 0. 문서 안내

* **담는 것**: 계획 결정을 오라클 구조로 옮긴 규칙, 자료 형식, 함수 서명, 실패 코드, 파일 분할, card별 범위, test 목록, 상위 문서 개정 문안.
* **담지 않는 것**: 경위(history 몫)와 수치 상수. 허용 폭은 시뮬레이터 해 정확도 선언(입력 `simulator.options` 또는 출처 있는 어댑터 보정값, §8.3), MC 표본 수 규칙, 기술자가 원본 파일에서 계산한 값에서만 온다(P N0 값 원칙). 예외는 계획 NFR-P2의 '출처 미확인 기존 상수' 다섯뿐이다(§14. v0.3.0: 여섯째였던 `1e-3`은 계획 v0.6.9 O-43 D1 (d)로 지운다).
* **이름 원칙**: 회로·PDK·시뮬레이터 이름은 '사례'로만 쓴다. 코어 규칙·스키마 필드 이름에는 넣지 않는다.
* **측정 대기**: OP-1(검증자 측정)이 정해야 하는 칸은 '**측정 대기**'로 두고 값이나 하나의 안을 고르지 않는다. 목록은 §19.3에 있다.
* **오케스트레이터 기본안**: 계획이 정하지 않은 세부를 이 문서가 정할 때 '(기본안)'으로 표시한다. 목록은 §19.1에 있다.
* **용어**: 계획 N0.1을 그대로 쓴다. 이 문서가 더하는 용어는 아래와 같다.

| 용어 | 정의 |
|---|---|
| 벤치 | 코어가 만든 회로 IR 하나와 해석 요청 목록의 묶음. 어댑터 실행 한 번의 단위다 |
| 테스트벤치 원소 | 본 회로 밖에서 측정을 위해 코어가 더하는 원소. 레일 전압원, DC servo, choke, 결합 C, AC 여기원, 감지원, Middlebrook 주입원, 고정 전압원이 있다 |
| 결과 묶음 | 어댑터가 벤치 하나에 대해 돌려주는 정규화 결과(§6)의 묶음 |
| 진단 벡터 | 소자 × 기술자 진단 변수마다 값을 정한 결정적 섭동 입력(§13) |
| 기술자 지문 | 오라클 기술자 파일 sha256 + 그것이 참조한 엔진 선언 sha256 + 기술자가 직접 가진 원본 파일 sha256 묶음. (v0.3.0, 계획 OQ-5 (a) = O-14 (3), N3.4 'sha256 정의' (i)) 세 값 모두 **LF 정규화 sha256**(계획 N0.1: 바이트의 CRLF만 왼쪽부터 한 번 LF로 바꾼 뒤의 sha256)이다. 엔진 `decl_sha256`(엔진 v6.17 card SH-1 전에는 raw) 값을 옮겨 적지 않고 파일 바이트에서 다시 잰다(§10.1) |
| OP-3 입력 스키마 | (v0.3.0) card OP-3이 정하는 오라클 입력 형식 `spice_oracle_input/2`의 칸 집합(§11.1). gain-budget card EO-1 생산자와 A' 손분석 입력의 계약이다(계획 N5.2·G-18). 정본은 §11.1 표 하나이고 기계 판정 파일 `O/oracle_input.schema.json`은 그 표를 옮긴 것이다 |
| G-18 확장 칸 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.0) OP-3 스키마 뒤에 card OP-5·headroom-chain HC-O·OP-10이 더하는 입력 칸(§11.6: 선언 영역 `intended_region`, 훑기 방향 `dc_sweep`, 측정 구성 `measure_feedback`, 끝 재훑기 `sweep_rezoom`, 출력 기준 `output_reference`, 슬루 선언 `slew` -- v0.3.1에서 tol_V 열·I_off 열 입력 칸은 삭제). 더하는 card의 통합 병합에 EO-1 생산자 갱신 커밋(`Role: code`)이 함께 들어간다(계획 U-6) |
| 판정 점 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.0) 오라클이 전도·포화를 판정하는 SPICE 해의 점: 합격 판정이면 free 모드 `.op` 해, 범위 판정이면 그 훑기 점의 해. 그 점의 값 = 그 해에서 읽은 VDS·VSB·VGS·ID·gm/ID·VDSAT(1단계, 오라클)와, 그 점 VDS·VSB에서 엔진 정본 LUT 함수가 계산하는 I_off·tol_V(2단계, 엔진 쪽 -- 계획 N3.9 '전도 판정 위치 -- 두 단계', 사용자 결정 O-46 (2)·O-50 G5) |
| 기계 의존 일치 | 계획 N0.1 그대로: 옛 raw 기록값이 파일의 LF 정규화 sha256과는 다르고 raw sha256과만 같은 경우. 받되 결과에 표시한다(§6 `machine_dependent_refs`) |
| 어댑터 지문 | 어댑터 이름 + 어댑터 코드 지문 + 실행 파일 sha256 + 읽은 시뮬레이터 판. (v0.2.6, 계획 v0.6.6 N3.5 '어댑터 코드 지문의 범위') 코드 지문 = 어댑터 패키지 `O/adapters/<이름>/` 아래 **모든 파일**의 sha256 묶음에서 **제외 목록**만 뺀 것이다. 제외 목록(닫힌 목록, 근거는 계획 v0.6.6 '지문 밖'): (i) `calibration.json`의 키 `wall_s_per_window`(그 키를 뺀 정규 JSON의 sha256을 넣는다) (ii) 보정값 측정 도구 하위 폴더 `calibration_tools/`(기본안 B-25) (iii) `__pycache__/`(실행 산출물). 제외 목록 방식이라 계획의 '목록 밖 새 보정값 키는 모르면 넣는다'(fail-closed)가 자동으로 지켜진다: 새 키·새 파일은 제외 목록에 이름이 올라가기 전까지 지문에 들어간다. 계획이 적은 판정 키 넷(`default_tolerances`, `data_digits`, `global_geometry_directive`, `simulator_version_probe`)은 모두 들어간다(§8.3 키는 이 넷과 `wall_s_per_window`뿐). (v0.2.6, 계획 v0.6.6 diff 확인 M-1·M-2) **파일 집합** = 계획 v0.6.6 문구 그대로 **어댑터 패키지 아래 디스크의 모든 파일 − 닫힌 제외 목록**이다(순수 파일 열거, git 등 프로세스 호출 없음). (v0.2.6 고침: 앞선 커밋의 'git 추적 파일 기준'(B-28 옛 안)은 철회했다 -- 미추적 새 파일을 지문 밖에 둬 fail-closed·'모르면 넣는다'를 거스르고, git 작업 트리가 아닌 배포본에서 오라클을 멈춰 환경 무관 목표와 충돌한다. 재현성 영향은 §19.4 X-D6.) 묶음 = 각 파일의 (패키지 기준 **상대 POSIX 경로**, sha256) 쌍을 경로 정렬 순으로 이은 것의 sha256이다(경로도 묶음에 들어가 파일 이름 바꾸기도 지문을 바꾼다). (v0.3.0, 계획 OQ-5 (b) = O-14 (3)) 파일마다 sha256은 **LF 정규화 sha256**이다(같은 코드가 CRLF·LF 체크아웃에서 같은 지문). 어댑터 패키지에 바이너리 파일이 생기면 계획 N3.4 '바이너리' 원칙대로 그 파일 종류를 선언으로 정한다(계획 개정 대상, 지금 없음). 파일을 읽지 못하면 지문 계산을 거부한다(`adapter_fingerprint_unavailable`, §7). **정규 JSON**(제외 키를 지운 `calibration.json`): `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`를 UTF-8 바이트로 인코딩한 것의 sha256이다. 능력 기록 `record_id`(§12.4)도 같은 직렬화 규칙을 쓴다. `calibration.json`을 읽지 못하거나 JSON이 아니면 지문 계산을 거부한다(`adapter_fingerprint_unavailable`, 원래 바이트로 대체하지 않음) |

---

## 1. 입력·원칙·선행 전제

### 1.1 확정 결정(인용)

| ID | 요지 | 이 문서에서 쓰는 곳 |
|---|---|---|
| T-31·T-33 | 오라클은 공정·시뮬레이터 무관. 능력 확인은 공정 무관 방법론 | 전체 |
| O-1 | 네이티브 MC, PC-4 삭제(크기 = TR-7 §17-1 비교), PC-3 유지, OP-1에서 네이티브 MC 소자별 독립 먼저 확인, 결정적 섭동은 진단 전용 | §10.4, §12, §13 |
| O-2 | X-15(엔진 σ 기하 전제는 TR-7 비교로 잡음)와 X-17(MC 연속값 동일성 제외) 수용 | §17.3 |
| O-6 D-a | 네이티브 MC = 기술자 선언 켜는 법(종류 하나 + 대상), 분포 값은 PDK 원본 선언에서만(기술자는 원본 sha256으로 위치만 가리킴), 난수는 시뮬레이터 RNG, 오라클은 표본 값을 계산하지 않음(P N0.1, X-18 수용) | §10.4, §12.2 |
| O-6 D-b | 기술자에 기하 단위·병렬 배수 전달 규칙 선언, 어댑터는 그대로 소자 줄을 씀, 미선언 kind는 공칭 포함 모든 해석에서 거부, 손 모델 결정적 어댑터 test(완료 조건 4a) | §10.2, §10.6, §18.1 |
| O-6 D-c | 차동 이득 실수 판정 상대 폭 `1e-3`은 '출처 미확인 기존 상수' 예외로 값·동작 그대로 이동(P NFR-P2 여섯째). **(v0.3.0) O-43 D1 (d)로 대체**: `1e-3`과 `.ac` 첫 점 경로를 지우고 A는 `.tf`로 잰다 | §14, §21.5 |
| O-7 | 계획 v0.6.2 승인·병합(`1ba9461`) | v0.2.4의 기준 |
| O-8 | (계획 v0.6.3) design v0.2.4 DV-3 = (가): 진단 경로 MC 재현 판정을 (가-1) 코어 MC 수학 비트 동일과 (가-2) 진단 경로 끝까지 재현(비트 동일 목표, 다르면 표본별 V_os만 N4-2 분해능 안 + 차 기록)으로 나눔(계획 X-19) | §13.2, §18.1 |
| O-9 | (계획 v0.6.5) design v0.2.5 DV-4 (가) = 완료 조건 8a 예외 둘째(엔진 test `E/tests/metrics/test_verified_by.py:64` glob 한 줄을 `(ORACLE / "core").rglob("*.py")`로, X-25), DV-5 (가) = 기준선 표본별 V_os는 기준선 로그에 옛 식(`O/oracle_offset_mc.py:166-195`)을 적용한 검증자 재계산값, 먼저 σ_in·mean_in 비트 동일로 검증(계획 N0.1 '기준선', OP-1a (a)~(d), X-24). 계획 v0.6.5 기본안: 어댑터 코드 지문 범위 | §0, §8.3, §13.2, §15.1, §15.4, §19.2 |
| O-10 | 계획 v0.6.5 승인. B-20의 `O/smoke/u6_selfchecks.py` 삭제 승인(점검 내용 새 test로 재작성, `U6_REPORT.md` 기록 유지) | §15.4, §19.1 B-20 |
| L-1·L-2 | (계획 v0.6.3, 상위 DEC-99) 옛 엔진 삭제(gain-budget card LT-1): `legacy_adapter` 삭제 수용, 저장소 안 오라클 입력 생산자 0, `O/smoke/` 입력은 고정 자료(계획 X-5·X-21), 기준선 판정용 텍스트 + sha256 목록 커밋(card OP-1a) | §3.1, §11.4, §13.2, §15, §18.2, §20 |
| L-3 | (계획 v0.6.4) OQ-1~OQ-4 승인: OQ-1 LUT 기록 파일 역할 구분(X-22), OQ-2 토큰 적중 증거 단계 규칙(X-23), OQ-3 MC 표본 실행 방법 배치(X-20), OQ-4 σ_in·mean_in은 (가-1)로만. `legacy_adapter` 삭제 = LT-1 순서 3 | §10.4, §12.5, §13.2, §18.1 |
| D-1 | C10 판정 규칙은 코어, 시뮬레이터 안 조기 종결은 어댑터 능력, 능력이 없으면 전체 창 + 코어 사후 판정 | §8.4 |
| D-2 | 생성기 이전 범위 포함, 옛 생성기는 출처 보존본 | §15.3 |
| D-3 | 실제 두 번째 시뮬레이터는 범위 밖, stub 어댑터로 측정 | §3.3, §18 |
| D-4 | bin 경계 규칙 = LUT 생성 실행에 묶은 선언 | §16 |
| D-5 | 새 입력 형식, 옛 형식 거부. (계획 v0.6.3) 생산자 수정은 범위 밖(저장소 안 생산자 0) | §11 |
| D-6 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 모델 오차·`verified_by`를 능력 기록 id에 묶음 | §17 N3.7 문안 |
| D-7 | 능력 기록은 MC·온도 계층에만, 공칭은 모델 묶음 자동 대조 | §12.5, §12.6 |
| D-8 | 실제 두 번째 PDK는 완료 조건 아님 | §12.7 |
| D-9 | 오라클 기술자는 별도 파일, 엔진 선언 sha256 참조, 엔진 무변경 | §10 |
| T-35 | offset-trim G-14 = 네이티브 MC 표본 안(결정적 벡터 불필요). PC-11 철회 | §12.2 |
| S-7 | 계획과 다른 결정은 계획부터 | §19.2 |
| O-13 (5) | (계획 v0.6.7) 기술자가 새로 적는 참조 sha256 = LF 정규화, 이 계획 밖 옛 raw 기록 = 규칙 (ii)(정규화 또는 raw 일치, raw만이면 '기계 의존'), 정의가 다른 값끼리 비교 금지(규칙 (iii)), git 밖 LUT 데이터 파일 = raw(규칙 (iv), v0.6.8) | §0, §6, §7, §7.2, §10, §11.1, §12.4, §12.5 |
| O-14 (3)·(4) | (계획 v0.6.7) OQ-5: 지문 넷(기술자 자체, 어댑터 코드, `process.descriptor.sha256`, `check_code_fp`) = LF 정규화. J-1 (나): 입력 형식 전환·옛 형식 거부·옛 입력 읽기 전환·재생성 일치 test 삭제는 OP-3, OP-2 = 기술자·스키마·읽기 코드(따로 검토, 함께 병합, X-28). J-5 (가): 기록 뿌리 교차 검사 함수·test는 OP-3 | §0, §11, §12.4, §15, §18, §20 |
| O-16 (1)·O-18 | (계획 v0.6.8) 엔진 정본 sha256도 LF 정규화(gain-budget card SH-1) -- 그 뒤 엔진 `decl_sha256`과 기술자 `engine_decl.sha256`은 정의가 같다. X-13은 파일 재측정 유지. LUT meta `generator_sha256`은 엔진이 대조하지 않고 오라클(OP-3)·OP-8만 대조 | §10.1, §12.5, §18.1 |
| O-25·O-33 (5)(7)(8)(9) | (계획 v0.6.9 N3.9) swing·ICMR 정의 = 정의 일반형(전달 뷰 여기 방향 입력 포트 훑기), ICMR 출력 고정 해제, 포화 = VDS ≥ VDSAT 여유 0(여유는 판정 단계), 선언 triode 제외, 끝 풀이 실패 fail-closed | §11.6, §21.2 |
| O-32·O-34 | 대신호 양도 엔진 손계산 + 오라클 SPICE 검증, 오라클 측정 정의 = 엔진 정의(인용만, 정의 정본 = gain-budget N3.8). 변경 종류별 판정 기준(정의 그대로 = 동일성, 정의를 바꾼 칸 = 동작 변경 기준), 슬루 측정 조건(β 선언 없으면 β = 1 + 'β = 1 기본' 표기) | §18.1, §21 |
| O-33 (4)·O-46 (1)·O-47 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 계통 offset = 오라클 `.dc`(출력을 기준에 고정·입력 차 풀이), 엔진은 ΔW 1차 감도, 차는 모델 오차(DEC-72) | §21.4 |
| O-36 (5)·O-45 U2·O-46 (2) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 범위 판정·합격 판정의 전도 = 봉인 9 식 I_off ≤ ε·ID, ε = (gm/ID)·tol_V. 값은 판정 점 값: gm/ID = SPICE op, tol_V·I_off = 그 점 VDS·VSB의 엔진 LUT 값(동작점 `off_current_A` 고정 아님). 원래 취지와 다름 X-33 승인 | §11.6, §21.1 |
| O-43 D1 (d) | 불일치 σ 입력 환산의 A = SPICE `.tf`(servo를 연 개루프 벤치), `.ac` 첫 점·`1e-3` 경로 삭제 | §13, §14, §21.5 |
| O-44 (1)·O-45 U1 | 엔진 점 → 오라클 입력 생산자 = gain-budget card EO-1(OP-3 뒤), 그 계약 = 이 문서 OP-3 입력 스키마. EO-1 범위 = OP-3 스키마 칸까지, G-18 확장 칸은 OP-5·HC-O 통합 병합에 EO-1 생산자 갱신 커밋 포함 | §11.0, §11.4, §11.6 |
| O-48 | 계획 v0.6.9 승인(v0.3.0 판의 기준) | 전체 |
| O-50 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.1, 계획 v0.6.10) **O1′** 기준선 입력 593개의 기대 결과 = D-7 거부(동작 변경), 코어 이관 동일성의 비교 상대 = 검증자 card OP-1b 추가 기준선(N4-2 비교), 검증자 사본 LUT 안 기각; **G1** 계통 offset = 부호 있는 V_id* 한 칸, 단일 입력 = 여기 방향 일반형; **G2** 슬루 = 방향별 metric 둘, 계단 끝 = ICMR 창 끝, 차동 출력 구성 미선언 = 정의 불능; **G3** 전도 부호 = 선언 방향 ID > 0; **G4** ICMR 측정 구성 = 선언 되먹임, 없으면 β = 1 follower; **G5** 전도 판정 두 단계(오라클 = SPICE op 값, I_off·tol_V와 마무리 = 엔진 정본 LUT 함수); **O2** `judge.off_current_A` 삭제, 포화 확인 대상 = 선언 없는 ID > 0; **O3** OP-10 선행 EO-1; **O4** X-D7·X-D8 수용 | §11.5, §11.6, §11.7, §18.1, §19.2, §19.4, §20, §21 |
| O-51 | 슬루 계단 끝의 ICMR 창 = 오라클이 잰 창(2단계까지 확정), 엔진 창을 입력으로 받지 않음 | §11.6, §21.6 |
| O-52 확인 1·O-53·O-54·O-55 | O-52: 차동 출력 구성 미선언 = 정의 불능, 단일 입력 = 회로 그대로. O-53 A-1 반전 입력 포트(선언 또는 `.tf` 부호), A-2 P3 범위, B1 `intended_region` {triode, off}, B2 온도 점 전도 판정, B3 출력 기준 종류 셋 + 차동 기본·PC-10 = 같은 측정. O-54 범위 조건 = 모든 MOS가 선언 영역에 머무름(동작점 불일치 = 거부, 훑기 중 이탈 = 범위 끝). O-55 U1 원인 구분(선언 소자 불일치 = 선언 오류, 판정 불능 집계 / 선언 없는 소자 비포화 = FAIL), U2 공용 전도 판정 함수 = 엔진 쪽(OP-5 통합 병합), V5 off 소자 LUT 경로 제외는 사이징 한정. O-56은 엔진 쪽(EO-1 search_domain·`dc_sat_v` off 갈래) -- 이 문서는 가리킴만 | §11.6, §21.1~§21.4, §21.6 |
| O-56 | (v0.3.5 추가 -- gap #35) O-55 U2 확장: (a) `search_domain` kind 목록의 `off` 제외 (b) headroom-chain `dc_sat_v`의 `off` 갈래 = 엔진 쪽 EO-1 범위(판정 부분은 넓히지 않음). 오라클은 칸(`intended_region`)만 제공 | §19.2 알림, §21.3 |
| O-57 | 계획 v0.6.10 병합 승인(v0.3.2까지의 기준) | 전체 |
| O-58 | (v0.3.3) DV-10 슬루 계단 끝 = 확정 ICMR 지목(네 검사, 전압은 오라클 자기 기록), 실행 순서 ICMR → 2단계 → 슬루; DV-11 σ 입력 환산 A = 여기 방향 DC 극한 전달(DEC-23), 단일 입력 기준선 변화 = N4 0번 동작 변경; T-1 triode 경계 여유 = gain-budget N3.8(2단계 적용); B-45 | §7, §11.6, §11.7, §21.1, §21.5, §21.6 |
| O-59 | (v0.3.3) (3) DV-12 확정 범위 지목(swing·ICMR 끝)·확정 기록 `status = final`, 요청마다 확정 왕복 1회(원래 취지와 다름(경미), 승인); (4) DV-13 계통 offset 기준점 V_id,0 = 선언 입력 DC의 여기 방향 좌표(DEC-23) | §7, §11.6, §11.7, §21.2, §21.4 |
| O-60 | 계획 v0.6.11·gain-budget v6.21 병합 승인(v0.3.3의 기준, master `b9af2d6f`) | 전체 |
| O-61 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.4, 계획 v0.6.12) P7 DV-14: σ 입력 환산의 'A_dc 정의 불능 갈래'(정본 gain-budget DEC-23), `.tf` 실패와 사유를 나눔; P8 DV-15: 선언 입력 DC 칸 = `dc_sweep.input_dc` 하나, `swing_icmr.input_dc_V`·`input_dc_pending` 삭제, V_icm은 선언 사영 또는 공칭 점 입력 좌표; X-R1·X-R2 승인(design 범위) | §11.1, §11.6, §19.4, §21.2, §21.5 |
| O-62 (2)·(3) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.4, 계획 v0.6.13) P10 DV-16: 2단계 끝의 이탈 소자·정의 불능 사유 정본 = 엔진 `stage2_judgment`(gain-budget N6.20), 확정 범위 지목의 정의 불능 끝 = `{undefined: true, record_id}`(`reason` 사본 삭제), `confirmed_range`·`range_final`에 `departed`·`reason` 값 칸 0; P11: A_dc로 나누는 모든 양(σ·V_id*)에 같은 갈래 | §11.6, §11.7, §7, §21.4 |
| O-63 (1)·(2) | (v0.3.4) 갈래가 'ΔW = 0 → 0'보다 먼저(그 규칙은 엔진 1차 계산 규칙, 오라클은 ΔW를 모름); 오라클 V_id* 갈래 판정 = σ 행과 같은 `.tf` A 한 측정 + N3.8 판정 분해능, 발동이면 `.dc`가 수렴해도 값 없음, `.tf` 실패·`.dc` 수렴 실패 사유 따로, 한쪽만 발동 = '정의 경계 불일치'(계획 N3.9 `offset_sys_mv` 행 (i)~(vi)) | §21.4, §21.5, §18.1 |
| O-65 | 계획 v0.6.13·gain-budget v6.23 병합 승인(이 판의 기준, master `7675f71b`) | 전체 |
| O-67 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.6, 계획 v0.6.14) (1) S-OS2 ICMR 측정 구성 = 선언 되먹임 DC 성분만, 없거나 미선언인 차동 출력은 DC 닫힘(꼴은 O-68 (2)), 차동 출력 미선언 = 정의 불능 규칙 대체(X-35 승인) (2) DV-18 `icm_margin_v` = 엔진 포트별 정의 하나(gain-budget N6.6 IT-2 '범위' 2), V_icm 사영 폐기 (3) DV-17 \|A\|·레일 폭 ≤ δV_out (4) X-R3~X-R5 수용 | §21.2, §21.5, §19.4 |
| O-68 | (v0.3.6) (1) DV-17 등가식 δV_out/레일 폭, 레일 폭 0 fail-closed, 오라클 δV_out = vntol + reltol·\|V\| (2) 차동 모드만 닫음: (in+ − in−) = −(Vop − Von), 입력 공통모드 = x, 출력 공통모드 = CMFB, margin 대상 = 입력 포트 둘 | §21.2, §21.5 |
| O-69 (1) | (v0.3.6) OQ-11 = (다): 슬루 측정 그대로, 과도 되먹임 = 선언 구성 전체, 미선언 차동 출력 정의 불능 유지(계단 입력 망 없음·입력 망은 선언 몫), 용량만 선언된 차동 출력의 t = 0 `.op` = ICMR DC 닫힘 인용 | §21.6, §7 |
| O-78 (1)(2)·O-79·O-80 | (v0.3.8, 계획 v0.6.15 DR-23) (1) §21.6 1b(용량만 선언된 차동 출력 슬루의 t = 0 시작 동작점 경로)는 OP-10에서 만들지 않고 gain-budget card AP-1 몫, 그때까지 정의 불능 + 사유; 만들 때 시작점 = ICMR 공칭 점 기록 `v_in` 참조(둘째 `.op` 생산자 금지) (2) 단일 출력 + 용량만 선언된 되먹임의 ICMR = 정의 불능(DV-19 닫힘), 정의 자리 = gain-budget v6.26 N3.8 하나, 단일 입력이면 회로 그대로가 먼저(O-80 R2); O-80 = 두 계획 병합 승인(이 판의 기준, master `93a9ff82`) | §7, §18.1, §19.2, §20, §21.2 2단계 (e), §21.6 |
| O-85 (1)(3)·O-86 | (v0.3.10, 계획 v0.6.17 DR-25) (1) 차동 출력은 두 출력 판정이 같을 때만 그 판정, 갈리면 정의 불능(사유 이름 design) (3) 지원 밖 원소가 있으면 판정 정의 불능(엔진 code `icm_config_feedback_element_unsupported`); O-86 = 두 계획 병합 승인(이 판의 기준, master `e87092b3`) | §7, §18.1, §19.2, §19.6, §20 OP-5, §21.2 2단계 (0) |
| O-81 (2)·O-82·O-83 | (v0.3.9, 계획 v0.6.16 DR-24) 'DC 되먹임 없음'은 소자 종류가 아니라 경로로 판정(DUT DC 망 방향 의존 그래프, 끝점 = 선언 절단 넷, 시뮬레이터 호출 전), 정의 자리 = gain-budget v6.27 N3.8 문단 하나, 오라클은 따로 구현(NFR-P3), 갈리면 '정의 경계 불일치'; O-83 = 두 계획 병합 승인(이 판의 기준) | §7, §18.1, §19.2, §19.6, §21.2 2단계 (0)(a)(c)(e), §21.6 1b |
| O-70 (1)·O-71 | (v0.3.6) 오라클 δV_out 꼴(\|V\| = 공칭 `.op` 전압, 차동 δ_p + δ_n) = gain-budget N3.8 인용(R-1), 계획은 입력 출처(N0 29행)만; 엔진 δV_out = 선형해 수치 분해능(gain-budget 몫); O-70 (2) 계획 3건 병합 승인(이 판의 기준, master `f4d89a23`) | §21.5, 전체 |
| O-115·O-116·U-102·U-103·U-105·U-106 | (v0.4.0, 계획 v0.6.21 DR-26) ICMR 측정 구성 = servo(입력 포트 같은 x, 감지를 봉인점 예측값에 묶음), 보정 방향 = 여기 방향, 부호 = 자기 `.tf`, 고정 오차 ≤ δV_out 점별 확인, 좌표 = V_cm. 슬루 계단 = 슬루 구성 `.dc` 끝 | §21.2, §21.6 |
| O-119·O-120·O-121 B-2·O-157 S1·U-107 | (v0.4.0, 계획 v0.6.22 DR-27·DR-28) 판정 계단·두 계단폭·20~80 % 기울기, 계통 offset 기준 도달 불가 | §21.6, §21.4 |
| O-178·O-180·O-182 Q-S9 (A′) | (v0.4.0) 엔진·오라클 차 = 대조 기록(e_m·ME-1 폐지, CL-1), LUT v2 r2만, KCL 항등 0 전류 MOS 판정 제외·독립 유도 대조 | §21.0, §21.1 |
| O-202·O-204·O-205 (1)(2)·O-210 RR-2·O-212 | (v0.4.0, 계획 v0.6.25) 판정 = 오라클 한 단계, 채널 `@m[id]` 부호·VDS ≥ `@m[vdsat]` 여유 0, `off` 선언 대상 밖, `off_current_A`·`sat_margin_V`·2단계 삭제, 온도 점 = 부호 비교. 원래 취지와 다름(승인) | §21.1, §21.3, §11.6, §11.7 |
| O-206·O-211 RR-3 → O-215 | (v0.4.0) ICMR 판정 = 영역 행, `.tf` 기능 기준은 선택 상대 저하 항 선언 제약만(**임시 -- 번복 가능**, 재검토 = LA-1a 뒤 front 실측) | §21.2 점 판정 |
| O-214·O-219~O-224 | (v0.4.0) 미룬 결정 (1) 지목 왕복 삭제 확인 = OP-5 착수 조건; O-221 `judged_by`·`off` 칸 = SF-1 로더 조각 + EO-1 통합 병합, 오라클은 읽지 않음; O-222 triode 선언 소자 ΔV 판정 = EO-1 design(엔진 쪽, 오라클 문언 변화 0); O-223·O-224 오라클 문언 변화 0 | §21.3, §19.2 |

### 1.2 원칙과 이 문서의 강제 장치

| 원칙 | 강제 장치 |
|---|---|
| 코어 무방언·무PDK(P FR-P1) | §3.2 import 금지 test, §18 완료 조건 1 test(검증자 소유 토큰 목록) |
| 상수 발명 금지(P NFR-P2) | §14 옛 리터럴 처리표. 새 판정 상수 없음. 보정값은 출처 칸 필수(§8.3) |
| 만들면 배선(P NFR-P4) | §15 대체 배선표, §13 진단 경로 진입점, 완료 조건 7 test |
| 작성자 ≠ 검증자(P NFR-P5) | 기준선·토큰 목록·입력 변환·능력 기록·동일성 판정의 주체를 검증자로 고정(§18.2) |
| fail-closed(P NFR-P6) | §7 오류 코드, §12.6 게이트, §11.2 옛 형식·스키마 거부(v0.3.0: 닫힌 키 집합) |
| 순차 실행(P NFR-P7) | §8.2 실행 계약: 어댑터는 병렬 실행을 하지 않는다 |
| 재계산 재사용(P NFR-P8) | §9 캐시 키 |

### 1.3 선행 전제

* 상위 문서 개정(P N3.7)은 v0.2.3 때 반영 전이었고(base `6093d07`의 상위 계획에 `run_ngspice_op_ac`가 남아 있었다), 이 문서 §17이 그 **문안**을 냈다. (v0.2.4) 그 개정은 별도 card `gb-oracle-rev`로 master에 병합됐다(`b105b65`, 2026-10-16. base `1ba9461`의 상위 계획에 `run_ngspice_op_ac` grep 0). 그래서 구현 card(OP-2~)의 공통 착수 조건(P N5.1) 가운데 이 항목은 충족됐다. 병합본이 §17 문안과 같은지는 이 card가 대조하지 않았다(§19.2 아래 '알림').
* offset-trim G-15(출력 기준 DC)는 base에서는 열려 있었지만, offset-trim design TR-0T가 닫았고 master에 병합됐다(T-40). 내용은 선언 기준을 온도 무관하게 그대로 쓰고, 없으면 `reference_undeclared`다. 그래서 v0.2에서 PC-10을 정의했다(§12.2). 대조 정본은 master `offset-trim.design.md` §20이다.

---

## 2. 실측 사실(base `6093d07`, 읽기만)

| ID | 사실 | 근거 |
|---|---|---|
| S-1 | 오라클 `*.py` 8개, 합계 5114줄. 진입점: `oracle_netlist.main`, `oracle_simulate.main`, `oracle_noise.main`, `oracle_offset_mc.main`, `oracle_swing.main`, `oracle_compare.main`, `oracle_run.main`, `legacy_adapter.main` | `O/*.py` |
| S-2 | `oracle_run.run_one`: `write_netlists` → `simulate` → (free이고 입력 블록이 있을 때) `noise_measure`·`offset_mc_measure`·`swing_icmr_measure` → `<stem>.sim.json` → `compare` → `<stem>.compare.*` | `O/oracle_run.py:39-61` |
| S-3 | `simulate`의 결과 칸: `devices`, `nodes`, `rail_current_A`, `hold_current_A`, `ngspice_rc`, `cache`, `log`, `log_errors`, `op_ok`, `ac`, `ac_file`, `ratio`, `rout`, `loop`, `cm_loop`(+안정성 칸). 막힌 넷리스트는 `skipped` | `O/oracle_simulate.py:1263-1300` |
| S-4 | `offset_mc_measure`: 표본 0 = 변수 0의 기준 해, 표본 1..n = 소자·변수마다 `rng.standard_normal() * 1e-6 / sqrt(n_fingers)`(`rng = numpy.random.default_rng(seed)`, 소자 순서 = 입력 `devices` 순서, 변수 순서 = `mismatch_vars` 결과 순서). V_os = (V_out − V_out,0)/A − (V_id − V_id,0), A = `.ac` 첫 점의 실수부(허수부가 `1e-3·|h0|` 이하일 때만). 출력 `mismatch_vars`에 소자별 변수 목록이 남는다 | `O/oracle_offset_mc.py:109-196` |
| S-5 | 표본 수 규칙 `sample_count(r)` = ceil(1 + 1/(2 r²)) | `O/oracle_offset_mc.py:43-49` |
| S-6 | 입력 스키마 최상위 칸: `schema, circuit, process, rails, devices, sources, passives, feedback_passives, cm_loop_passives, cm_output_loop, feedback_passives_basis, bias_voltages, ports, predictions, acceptance, testbench, judge, noise, offset_mc, swing_icmr, topology, provenance`. 필수: `circuit, process, rails, devices, ports, predictions, testbench`. `process` 필수: `lut_npz, models`. `models[kind]` 필수: `subckt, includes, op_probe` | `O/oracle_input.schema.json` |
| S-7 | smoke 입력의 pmos `includes`에 `models/parameters/lod.spice`가 있다. 이 파일은 엔진 PDK 선언 `sources`에 없다(엔진 선언 sources: tech LEF, periphery rules, nfet·pfet tt 모델 카드, mismatch 파일 둘, MIM·poly R+C 파라미터, `models/all.spice`) | `O/smoke/current_reuse_telescopic_ota.sizing.engine.oracle_input.json` `process.models.pmos.includes`, `A/sky130_pdk_decl.json` `sources` |
| S-8 | 옛 리터럴 상수: `NYQUIST_K_MAX = 10`, `NOISE_TOP_K_MAX = 8`, `INTEGRAL_K_MAX = 4`, `ZOOM_POINTS = 7`, `ZOOM_ROUNDS = 8`, `WRDATA_NUMDGT = 8`, `_NGSPICE_DEFAULT_TOL`, 차동 이득 실수 판정 `1e-3`. 물리 상수 `_K_B`·`_Q_E`(CODATA) | `O/oracle_simulate.py:398-402, :750`, `O/oracle_noise.py:44-45`, `O/oracle_swing.py:43-44`, `O/oracle_netlist.py:727`, `O/oracle_offset_mc.py:137` |
| S-9 | 원소 이름 접두사 규약: `CIRCUIT_PREFIXES`(`X`, `Rp_`, `Cp_`, `Isrc_`, `Vsrc_`, ...), `TESTBENCH_PREFIXES`(`Vrail_`, `Efb_`, `Vofs_`, `Lfb_`, `Vdc_`, `Ldc_`, `Cac_`, `Vac_`, `Vbias_`, `Vhold_`, ...), `CHOKE_PREFIXES` | `O/oracle_netlist.py:56-60` |
| S-10 | 오라클 test 29개 `.py`(fixture helper `u6_toy5t.py` 포함). 텍스트 단언 파일은 계획 F-15 기준 test 13개 + helper 1개 | `O/tests/`, P F-15 |
| S-11 | 창당 실행 시간 보정값 `stability_transient.wall_s_per_window` = 306.1 s, 측정 방법·코퍼스·기계 메모가 함께 있다(ngspice-46, 2026-10-08) | `O/oracle_config.json` |

**OP-1 측정 사실(v0.2.4).** 검증자 OP-1 산출물을 이 판을 쓰며 다시 읽었다. 위치는 `wt/_scratch_op1/results/`(아래 `R/`), 스크립트는 `wt/_scratch_op1/scripts/`다. 사례 조합은 sky130·ngspice-46이고, 수치는 기록일 뿐 규칙이 아니다.

| ID | 사실 | 근거 |
|---|---|---|
| S-12 | 첫 조합의 네이티브 MC 켜는 법: 모델 카드가 `.param … = 0.0`으로 둔 불일치 변수(`…__{toxe,vth0,voff}_slope_spectre`)를 최상위 `.param … = agauss(0,1,1)`로 다시 선언한다. 분포 값의 출처는 모델 카드의 주석 처리된 통계 블록(`vary … dist=gauss std = 1.0`)이고, 그 시뮬레이터는 이 블록을 실행하지 않는다. 결과: 200 시드에서 소자 A·B의 vth0 표준편차 1.399·1.495 mV, 상관 −0.058(소자별 독립, 13행), 같은 시드 비트 동일·다른 시드 다름(2행), 시드 없으면 실행마다 다름(3행), 같은 시드 표본이 −40·27·85 °C에서 같음(6행), 한 실행 안 재추출 명령 셋 모두 표본 불변 = 표본마다 별도 실행(8~10행), 스위치 0은 공칭과 **출력 자릿수** 동일(15행, 비트 비교 아님), 인스턴스 줄 덮어쓰기는 효과 없고 래퍼 지역 파라미터는 효과 있음(16·17행) | `R/m1_native_mc.jsonl` 행 번호, `scripts/m1_native_mc.py:45`, `C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice:16-27` |
| S-13 | 기하 단위·병렬 배수: 카드 식은 `vth0 = … + slope_spectre*(vth0_slope/sqrt(l*w*mult))`이고(`…tt.pm3.spice:67`), 래퍼 기본 `mult = 1`(`:30`). `.option scale` 없이 SI 기하를 주면 vth0 표본이 −904 V(면적이 10¹²배 작게 읽힘), scale 아래 숫자면 0.4833 V(4행). 인스턴스 `m=4`만 주면 표본이 `m=1`과 같고(배수가 면적에 안 들어감), `m=4 mult=4`면 편차가 절반(11행). 지금 오라클은 SI 기하 + `m=`로 쓰고(`O/oracle_netlist.py:145-153`) 이 둘을 변수값 z·1e-6/√m로 덮는다(`O/oracle_offset_mc.py:22-24`). scale 지시는 PDK 파일 `models/all.spice:2`(`.option scale=1.0u`, 엔진 선언 source `scale_option`)에 있고, 지금 오라클 include 목록에는 그 파일이 없다(smoke 입력 `process.models.*.includes`) | `R/m1_native_mc.jsonl` 4·11행, 위 파일:줄 |
| S-14 | 차동 이득 실수 판정: 기준선 ac 파일 198개 가운데 옛 규칙(`|Im h0| ≤ 1e-3·|h0|`)으로 실수 174개, 결과 파일 자릿수 분해능 `data_rel`로 바꾸면 4개만 실수(170개가 ok → unavailable로 뒤집힘). 그래서 계획 D-c가 값을 유지했다 | `R/m7_gain_imag.json`(`n_ac_files`, `n_old_real`, `n_new_real`, `n_flip_ok_to_unavailable`), `O/oracle_offset_mc.py:137` |
| S-15 | LUT 메타: 슬라이스 38개 모두 `model_files_sha256` 기록이 있고 PDK 원본과 sha256이 맞으며 생성 시뮬레이터 판(`ngspice-46`) 기록이 있다. 메타 칸 이름은 `ngspice`·`ngspice_exe`(사례 이름) | `R/m2_m3_lut_meta.jsonl` 41행 SUMMARY |
| S-16 | 방언 토큰 초안(검증자 소유 `wt/_scratch_op1/g8_dialect_tokens.draft.json`, D1~D12) 사전 점검: 기준선 넷리스트 1158개와 옛 코드 리터럴에서 D11(난수·식 함수 `agauss(` 등)만 어디서도 적중하지 않았다. 코어 어휘(`op`, `ac`, `dc`, `noise`, `tran`, `pz`, `temp`, `reltol`, `vntol`, `abstol`) 단독 적중 0 | `R/g8_check.json` `tokens_with_no_hit_anywhere`, `core_vocab_false_hits` |
| S-17 | `O/oracle_compare.py`의 시뮬레이터 이름 리터럴(문자열, docstring 제외)은 3개다: `:379` 메시지 `"ngspice .op 결과 없음: "`, `:708` 메시지 조각 `' V, ngspice '`와 키 `'ngspice_runs'`. docstring 안 언급은 `:38`(모듈)·`:228`(`signed_id`). 키 `ngspice_runs`의 생산자는 `O/oracle_swing.py:306`, 다른 소비자는 `O/smoke/u6_selfchecks.py:136`이다. 결과 칸 `ngspice_rc`는 `O/oracle_simulate.py:1284` 등 여러 곳이 쓴다(S-3) | `R/g8_check.json` D9 `oracle_compare.py: 3`, `grep -n -i ngspice` (base `1ba9461`) |
| S-18 | 오류 로그: 기준선 로그 860개에서 문장 형태 25묶음. 옛 정규식(`error|fatal|singular|abort`)은 회로 제목 줄 `Circuit: * spice_oracle: tsingular …`에 적중한다(12건, 제목의 'singular'). pz 실패 표지(`giving up`)는 옛 일반 정규식에 걸리지 않고 pz 정규식에만 걸린다(43건) | `R/m8_errlog.json`, `R/m8_errlog.console.txt` |
| S-19 | C10 창당 비용(같은 기계, 순차): 기준선 폐루프 과도 150 실행(조기 종결 12), 지금 합계 137.7 s, (가) 전체 창 한 번 146.8 s, (나) 창별 재실행 463.2 s(판정 창까지)·513.2 s(계획 창 전부), 창 하나 최대 15.97 s | `R/g13_window_cost.json` `aggregate`, `scripts/g13_window_cost.py` 머리 설명(비용 모형) |
| S-20 | DC 풀이 허용오차 선언(X-D4): 옛 형식 입력 593개 가운데 `testbench.options`에 reltol·vntol·abstol 가운데 하나라도 없는 것 2개. 그중 `converted/sizing.engine.new.json`은 변환 뒤 `simulator.options`로 옮긴 파일을 옛 칸으로 읽은 스캐너 결과라 대상이 아니고, 실제 대상은 test 입력 하나(`test_plan_default_reltol0`, reltol 없음)다 | `R/m6_xd4_scan.json`, `scripts/m6_xd4_scan.py:16`(`testbench.options`만 읽음), `R/n4_convert.jsonl` `options_moved` |
| S-21 | 입력 변환 초안(검증자 소유 `wt/_scratch_op1/n4_convert_input.py`)이 §11.1 대응표 밖 `process` 키 2개를 찾았다: `lut_reference_width_m`, `provenance`. 둘 다 생산자 `legacy_adapter.process_from_lut_generator`가 쓰고(`O/legacy_adapter.py:191-192`) 오라클 본체(`O/oracle_*.py`)는 읽지 않는다(grep 0). `lut_reference_width_m`은 `legacy_adapter` 안에서 finger 분할 기준 폭의 대체값으로만 쓰인다(`:261-264`, dump `lut_meta.W_ref_m`이 없을 때) | `R/n4_convert.jsonl` `unmapped_process_keys`, 위 파일:줄 |
| S-22 | MC 수학 재현(v0.2.5 인용 정정): 1행 = 기준선 `offset_mc` 표본(seed 0, `n_requested` 201, 변수 14개)을 옛 순서로 재현해 옛 형식(`%.12e`, z·1e-6/√m)으로 쓴 `alterparam` 값 문자열이 기준선 넷리스트의 201 표본 블록과 문자열 단위로 같았다(`bit_identical: true`, 표본 0은 모두 0). 2행(`m13_vos_from_log`) = 기준선 로그의 표본별 op 값으로 다시 계산한 **σ_in·mean_in 두 값**이 기준선 출력과 비트 동일(`sigma_bit_identical`, `mean_bit_identical`). **표본별 V_os는 비교하지 않았다**: 기준선 출력 `offset_mc`에 표본별 V_os 칸이 없다(칸 목록 `status, reason, sigma_in_mV, mean_in_mV, n_samples, method, ngspice_rc, n_requested, n_failed, n_capped, rel_se_achieved, rel_resolution, seed, a_dc_signed, mismatch_vars, unit_note`). 2행을 만든 스크립트는 `scripts/`에 없다(`m13_mc_replay.py`는 1행만 쓴다) | `R/m13_mc_replay.jsonl` 1·2행, `scripts/m13_mc_replay.py:1-5, :34`, 기준선 `pytest/tmp/mc5t0/o/t5ota.free.sim.json` `offset_mc` 키 |

**v0.2.5 재측정 사실**(base `9069e10`, 읽기만. OP-1 산출물은 같은 `R/`).

| ID | 사실 | 근거 |
|---|---|---|
| S-23 | 결과 칸 `ngspice_rc`의 생산자는 10곳이다: 본 회로 `O/oracle_simulate.py:1284`(막힌 넷리스트는 `:1279`에서 `None`), β 루프 `:1314`, CM 루프 `:1248`, 안정성 동작점 패스 `:1113`(`op_pass`), 폐루프 과도 `:1178`, 연장 `:1198`(`extension`), pz `:784`(초기 `None`)·`:808`, pz 개루프 과도 확인 `:1055`(`pz.validation`), noise 개루프 `O/oracle_noise.py:151`, offset_mc `O/oracle_offset_mc.py:165`. 시간 초과 때: 안정성 세 경로는 `_run_stab`이 `rc = None`을 돌려주고(`:1066-1067`), pz는 `:805-807`에서 칸을 `None`으로 둔 채 반환, noise·offset_mc는 칸을 만들지 않은 채 반환한다(`oracle_noise.py:148-150`, `oracle_offset_mc.py:162-164`). rc를 기록하지 않는 실행: noise 폐루프(`oracle_noise.py:294`), refine(`oracle_simulate.py:857`), swing 표본(`oracle_swing.py:105`). 소비자: `O/tests/test_oracle_c10_stability.py:1364, :1371`(연장 기록), `O/README.md:489, :540, :567, :711`(문서). `oracle_compare.py`는 `ngspice_rc`를 읽지 않는다(grep 0) | `git grep -n -E "ngspice_rc\|ngspice_runs"` |
| S-24 | 결과 `method` 칸 값에 시뮬레이터 이름이 든 곳: `O/oracle_simulate.py:785`(pz, `"ngspice .pz …"`), `O/oracle_noise.py:122`(`"ngspice .noise …"`), `O/oracle_offset_mc.py:115`(`"ngspice Monte-Carlo …"`). 안정성 `method`(`:1082, :1365`)에는 없다 | `grep -n '"method"' O/oracle_*.py` |
| S-25 | 삭제 모듈을 import하는 `O/smoke/` 스크립트: `cm_loop_engine_vs_ngspice.py:104, :115`(`oracle_simulate.loop_gain`, 함수 안 import), `cm_loop_mixed_cut_example.py:28`·`cm_loop_variants.py:28`(`oracle_simulate.ac_measures, loop_gain`), `u6_selfchecks.py:28-32`(`oracle_netlist`, `oracle_noise`, `oracle_offset_mc`, `oracle_simulate`, `oracle_swing`, 그리고 `:98, :107`에서 `mismatch_vars`·`build_mc_netlist` 직접 사용). `measure_wall_s_per_window.py`는 오라클 모듈을 import하지 않고 `--ngspice`로 실행 파일을 받아 `oracle_config.json` 근거를 잰다(`:2-14, :47`). 저장소 안 다른 importer는 없다(`git grep -l -E "(from\|import) +oracle_(netlist\|simulate\|noise\|offset_mc\|swing\|compare)"`가 오라클 본체와 위 4개만) | 위 파일:줄 |
| S-26 | 엔진 test `E/tests/metrics/test_verified_by.py:62-65`가 오라클 **최상위** `O/oracle_*.py`(glob)의 소스 텍스트에서 measure 키 8개(`offset_in_sigma_mv`, `swing_out_v`, `icmr_v`, `icm_margin_v`, 잡음 4개)를 찾는다. 8개 모두 지금 `O/oracle_compare.py`에 있고(셋은 `O/oracle_swing.py`에도), 다른 최상위 파일에는 없다 | 위 파일:줄, `grep -l` 키별 |
| S-27 | `O/tests/conftest.py`의 옛 엔진 장치: `--run-legacy` 옵션(`:36-38`), `legacy_slow` 마커 등록(`:41-42`)과 건너뛰기(`:45-51`). 마커를 쓰는 곳은 `test_legacy_adapter.py:116, :129, :138`뿐이다 | 위 파일:줄 |
| S-28 | 옛 기본 허용오차 `_NGSPICE_DEFAULT_TOL = {"reltol": 1e-3, "vntol": 1e-6}`에는 **abstol이 없다**. 오라클 코드 어디에도 abstol 값·읽기가 없다(grep 0). 쓰는 곳은 `reltol_of`·`solver_floor`·`tran_plan`·`transient_decision`(`:490-500, :558, :665`) | `O/oracle_simulate.py:401-402` |
| S-29 | LUT 기록 역할(계획 F-18 재계산): 기준 슬라이스 38개 중 32개의 `model_files_sha256`에 `cells/<kind>/<…>.bins.csv`가 있다. 생성기는 넷리스트 include 목록 `_included_files(dev)`(= 넷리스트 include 줄의 대상, `A/sky130_lut_sweep.py:231-232`) 뒤에 그 파일을 덧붙여 기록한다(`:688`, `:891`). 슬라이스 meta에 `generator_sha256`·`pdk_root` 칸이 있고(`R/m2_m3_lut_meta.jsonl` `meta_json.top_keys`), 기록 경로는 `pdk_root` 기준 상대 경로다(`E/lut/provenance.py:11-13`). 엔진 선언 `pdk_root`(`A/sky130_pdk_decl.json:4`)는 그보다 한 단 위 폴더이고 `sources` 경로가 `sky130_fd_pr/…`로 시작한다. (v0.4.4 정정) 결합 파일 6개도 중첩 안에 기록한다: 38/38(`m2_m3_lut_meta.jsonl`). 32는 평탄 표만 센 값. | 위 파일:줄 |
| S-30 | 기준선 로그의 '회복 시도 실패' 경고 셋(`Dynamic gmin stepping failed`, `True gmin stepping failed`, `source stepping failed`, 각 1건)은 모두 한 로그 `pytest/tmp/cmfb0/out/tcm_cmfb.free.cmloop.pz.log`에 있고, 그 뒤 `Note: Transient op finished successfully`(동작점 회복)와 pz 반복 한도 경고가 이어지며 극점 5개가 찍혔다(`:3-21, :40-44`). 다른 로그 `mc5t0/o/t5ota.free.mc.log:2406-2407`은 `Starting dynamic gmin stepping` 뒤 `Dynamic gmin stepping completed`다. 기준선 로그 860개에 시간 걸음 실패·시간 초과 문장은 없다(25묶음 목록) | `R/m8_errlog.json` `groups`, 위 로그 파일:줄 |

**v0.2.6 재측정 사실**(base `52945ce`, 읽기만).

| ID | 사실 | 근거 |
|---|---|---|
| S-31 | **실행 전 반환 경로**(시뮬레이터를 부르지 않고 결과 칸 `ngspice_rc` 없이 돌아오는 곳): noise 개루프 `O/oracle_noise.py:125-128`(이득 식·Vac 원·출력 노드·`f_lo_hz` 없음, `status = "failed"`). offset_mc 다섯 곳(`status = "unavailable"`): 차동 입력 쌍 없음 `O/oracle_offset_mc.py:117-119`, 넷리스트 막힘 `:121-122`, 텍스트에 `Lfb_` 없음 `:127-129`, `.ac` 첫 점 없음 `:134-136`, 허수부 큼 `:137-140`(그리고 블록 없음 `:111-113`은 `None` 반환). 안정성 과도: 기본 `tr = {"status": "not_run"}`(`O/oracle_simulate.py:1096`)에 사유 다섯(닫기 부호 없음, 출력 노드 없음, 관측 노드 없음, 교차·온도·동작점 없음 `:1134-1140`, 계획 `None` `:1147`), `failed` 둘(동작점 패스 시간 초과 `:1159`, 과도 넷리스트 생성 불가 `:1161`). pz 개루프 과도 확인 `not_run` 둘(`:1033`, `:1043`). 동작점 패스가 시간 초과면 pz를 부르지 않고 `pz = {"status": "unavailable", "P": None, "reason": …}`(`:1118-1119`, 칸 `ngspice_rc` 자체가 없다). pz 자체의 실행 전 반환은 S-23(`:791-793`, `:798-800`) | 위 파일:줄 |
| S-32 | **옛 상태 칸**: 본 회로 결과의 `log`(로그 경로, `O/oracle_simulate.py:1286`), `log_errors`(정규식 `error\|fatal\|singular\|abort` 적중 줄 앞 40개, `:1287-1288`; β 루프 `:1315`, CM 루프 `:1249`), `op_ok`(소자 하나라도 `id`가 있음, `:1289`), `skipped`(막힌 넷리스트 사유, `:1278`), `cache = {"main", "loop"}`(`:1285, :1307`), 안정성 캐시 `stability_cache = {op_pass, transient, extension?, pz_validation?}`(`:1369-1375`, 주석 '캐시 상태는 결과가 아니다(C21)' -- `ac` 밖으로 뺀다). 소비자: `O/oracle_compare.py:378-379`(`op_ok`·`skipped`·`log_errors` → 막힘 문장), `:383-384`(β 루프 `measures`·`singular`·`log_errors`), `:386-387`(CM 루프 같음), `O/oracle_run.py:45`(`skipped`이면 U6 측정 안 함), `O/oracle_simulate.py:1404-1406`(CLI 종료 코드 = `op_ok`). 캐시 단언 test 넷: `O/tests/test_oracle_simulate_cache.py:57-127`, `test_oracle_ratio_db.py:287`, `test_oracle_rout.py:559, :575`, `test_oracle_c10_stability.py:832, :1321-1339`. `log`의 소비자는 없다(grep: 생산자뿐) | 위 파일:줄 |
| S-33 | 실행 전·시간 초과 `reason` 문자열에 시뮬레이터 이름이 든 곳: `O/oracle_simulate.py:1067`(`"ngspice 가 --timeout-s …"`), `O/oracle_offset_mc.py:179`(`"…(ngspice …)"`), `O/oracle_noise.py:168`(`"ngspice 로그에서 …"`), `:299`(`"…(ngspice .noise 실패)"`) | 위 파일:줄 |
| S-34 | `O/tests/conftest.py`의 **옛 형식 입력 생성기**: `process_block`(`:71-90`, `process.models[kind].{subckt, includes, op_probe}`, `process.diffusion`), `testbench_block`(`:105-109`, `testbench.options`에 reltol·vntol·abstol·gmin), 그 둘을 쓰는 `cs_input`(`:118-`), `rc_input`(`:166-`), `fb_input`(`:195-`). `make_lut`(`:60-68`)는 meta에 `corner`·`temp_c`만 쓰고 `model_files_sha256`이 없다. conftest의 입력 생성기 이름을 쓰는 곳은 conftest 밖 183곳(`O/tests/*.py`, `O/smoke/*.py`), conftest를 import하는 파일은 test 27개·`u6_toy5t.py`·`smoke/u6_selfchecks.py`(`:25-26` 경로 추가 뒤 `import conftest`, `:44, :52, :54, :66-67, :84` 생성기 사용) | `grep` |
| S-35 | LUT 기록 뿌리의 기존 정본: `A/lut_v2_location.json`(스키마 `gmid_lut_location/1`) `pdk_root = {"env": "GMID_PDK_ROOT", "default": "C:/pdk/sky130_fd_pr"}`. 읽는 함수는 엔진 `gmid_engine.lut.resolve_lut_location`(파일 `description`, `E/lut/CONTRACT.md` 1.8) | 위 파일 |
| S-36 | 오라클 파일을 인용하는 엔진 쪽 주석·문서(바뀌면 낡는 인용): `E/metrics/verified_by.py:35, :48`(`tools/spice_oracle/oracle_compare.py` MEASURES·`oracle_noise.py`), `E/tests/metrics/test_device_sigma.py:9`(`oracle_offset_mc.py` 머리말), `E/metrics/junction_cap.py:16`(spice_oracle C22), `E/tests/metrics/test_verified_by.py:1-12`(docstring의 `oracle_offset_mc`·`oracle_swing`·`oracle_compare`) | `git grep -n spice_oracle -- '*.py'` |

**v0.3.0 재측정 사실**(base `9401e98f`, 읽기와 작은 실측. 실측 스크립트·넷리스트는 scratchpad `oracle_design/`, 저장소 밖).

| ID | 사실 | 근거 |
|---|---|---|
| S-37 | 기술자가 참조할 파일의 두 sha256(이 기계, CRLF 체크아웃): `A/sky130_pdk_decl.json` raw `24f970d5…` / LF 정규화 `5f32257b…`, `A/lut_v2_location.json` raw `c7ebb3c7…` / LF `07299556…`, `C:/pdk/sky130_fd_pr/models/parameters/lod.spice` raw `20874af1…` / LF `6200b50c…`. 셋 다 디스크 바이트에 CRLF가 있다. 계획 F-19·DR-8 값과 같다 | Python `hashlib.sha256(b)`·`b.replace(b"\r\n", b"\n")` |
| S-38 | LUT v2 폴더(`A/lut_v2_location.json` `root`)의 LUT 파일 meta 모양: 폭 슬라이스 32개(`*__W*_dc.npz`)는 `meta_json.model_files_sha256`이 **평탄 표**(상대 경로 → sha256; nfet 3개 = 모델 카드·mismatch 파일·`.bins.csv`, pfet 4개 = 여기에 `models/parameters/lod.spice`), `generator_sha256` = `8df35d2e…`. 결합 파일 6개(`sky130_nfet_pfet_lut_v2*.npz`: 기준·r2·noise r1·mismatch r1·중점 둘)는 같은 칸이 **LUT 소자 키(`nfet_01v8`, `pfet_01v8`)로 한 겹 중첩**된 dict다(`generator_sha256` 4종). 모든 파일에 npz 키 `corner`·`temp_c`가 있다. 폭 슬라이스의 VGS 축 첫 값은 0.0이다(VGS = 0이 격자 마디). manifest `slices[*]` = `{device, w_um, file, bytes, sha256}` | `np.load` 실측, 계획 N9 '관찰' 행(중첩 모양)의 확인 |
| S-39 | **기준선 입력의 LUT에는 모델 기록이 없다**: 기준선 입력 593개(`wt/_scratch_op1/baseline`)의 `process.lut_npz`는 test가 만든 `…/pytest/tmp/<case>/lut.npz`(npz 키 `corner`·`temp_c`만, conftest `make_lut` S-34)와 `A/sky130_nfet_pfet_lut_sample.npz`(키 `corner, temp_c, L, VGS, VDS, VS, ID_n, …` -- `meta_json` 없음)뿐이다(상위 빈도 24·22·16·16·14·…, 모두 이 둘 중 하나). 둘 다 `model_files_sha256`이 없다 -- 공칭 자동 대조(§12.5)가 배선되면 변환 입력 전부가 `lut_model_provenance_missing`으로 거부된다(§19.2 DV-7) | `grep -o '"lut_npz": *"[^"]*"'`, `np.load` |
| S-40 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.0 검증 지적 2로 고침) 지금 합격 판정의 전도 관련 칸은 둘이고 쓰임이 다르다. (a) **C23 전도 확인**(`conduction_check`, `O/oracle_compare.py:235-247`)은 소자별 `predictions.devices.<n>.off_current_A`만 본다: 예측 항목 없음 → 'N/A(예측 없음)'(`:238-239`), `region = "off"` → 대상 밖, 소자별 칸 없음 → 'N/A(off_current_A 없음)'(`:242-244`), SPICE ID ≤ 칸 → FAIL. N/A는 판정 `INCOMPLETE`(`:402-403`). (b) **문턱 `thr`**(`:278-281` -- 소자별 칸 우선, 없으면 `judge.off_current_A`)은 `region_spice = "off"` 표시(`:280`)와 포화 확인 대상 선택(SPICE ID > 문턱인 소자, `:390-391`)에만 쓰인다. 머리말 `:26-29`. swing은 `judge.off_current_A`만 쓴다(`O/oracle_swing.py:15, :194, :326`). 두 칸 모두 ε = 1 식이다(계획 N3.9) | 위 파일:줄 |
| S-41 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 엔진 쪽 정의(오라클은 import하지 않음, 같은 정의를 맞추는 대상): 봉인 9 I_off = `op_point(memo, kind, w_key, L, 0, vds, vsb).IDu · W/L`, ε = `gm_id · dc_tol_v`(`E/sizing/seal_conduction.py:6-10, :32-37`). tol_V 셀 = `tol_v_table(kind, w_key).at(L, vds, "id_equivalent")`(`E/search/cell_floor.py:19`), 읽기 규칙 `E/lut/_helpers_loo.py:153-163` `table_at`: L이 앵커면 그 행, 같은 bin 보간이면 양옆 앵커 두 행, VDS 칸 k = min(bisect_right(grid, vds) − 1, len(grid) − 2), 그 행들 × {k, k+1} 셀 가운데 정의된 값의 최댓값(없으면 None), VDS가 축 밖이면 거부. I_off의 `op_point`는 VS·VDS 축에서 기울기 자료·단조 조건이 맞으면 3차 Hermite, 아니면 선형, L은 bin 안 선형(`E/lut/point_query.py:22-64`, `E/lut/_helpers_interp.py:133-178`) | 위 파일:줄 |
| S-42 | ngspice-46 `.tf`(실측 넷리스트 `oracle_design/tf_diff.cir`·`tf_ctrl.cir`): 차동 출력 `.tf v(op,on) Vd`가 되고 로그 세 줄 `transfer_function = 2.000000e+02`, `output_impedance_at_v(op,on) = 2.000000e+05`, `vd#input_impedance = 1.000000e+20`을 낸다(손 회로 gm·R = 100 쪽마다, 차동 200). `.control` 안 `tf v(op,on) vd`도 같은 세 줄. 단일 출력·servo 닫힘(폐루프 0.495)은 계획 OQ-6 실측(`scratchpad/tfcheck/`) | `ngspice_con.exe -b` |
| S-43 | 지금 입력 스키마: 닫힌 키 집합은 `cm_output_loop`와 `$defs` 뷰 셋뿐이고 최상위·`process`·`devices[]` 등은 열려 있다. `schema` 칸은 선택이다. 검증 = jsonschema Draft 2020-12(`O/oracle_netlist.py:224-231`), 위반이면 진입점이 반환 2, 산출물 없음(`O/oracle_run.py:80-85`). 의미 검사는 막힘(`BLOCKED`): 기준 레일 개수(`O/oracle_netlist.py:95-96`), C27 여기 가중(`:199-221`), C14 되먹임(`:234-252`), CM 루프(`:263-293`), LUT 코너·온도 없음(`:302-304`) | 위 파일:줄 |
| S-44 | 기준선 입력 593개의 키 실측(스키마 `properties` 대조): 스키마 밖 키는 `process.lut_reference_width_m`·`process.provenance`(각 16개)와 이미 변환된 사본 하나의 `process.descriptor`·`simulator`뿐이다. 최상위·`devices[]`·`rails[]`·`testbench`·`judge`·`predictions` 등에는 스키마 밖 키가 0이다. 이름 중복 입력 0, `L`·`finger_w`가 양의 숫자가 아닌 소자 6개(값이 문자열 `"0.5u"`이거나 `finger_w` 없음 -- C13 스키마 거부 test 입력, 숫자 0 이하는 0개, §11.1 보충 (d)), `passives[].value` 0 이하·비숫자 0개, `circuit` 값은 모두 `^[A-Za-z0-9_][A-Za-z0-9_.-]*$`, `topology.sha256`이 있는 입력 18개 | scratchpad `oracle_design/scan_keys.py` |
| S-45 | 지금 스윙·ICMR 측정: free 넷리스트의 servo 기준원(`Vofs_`)과 입력 DC원(`Vdc_`)을 `alter`로 바꿔 `.op`를 점마다 푸는 훑기, 격자 간격 V_T, 경계 괄호 7점 × 최대 8회(`ZOOM_POINTS`·`ZOOM_ROUNDS`), 수렴하지 않은 점 = 포화 아님(`O/oracle_swing.py:15-30, :142-189`), 차동 입력이 없으면 ICMR `unavailable`(`:233`), 결과 키 `ngspice_runs`(`:306`) | 위 파일:줄 |
| S-46 | 레일 전류·전력: `rail_current_A[net] = −i(Vrail_<net>)`(`O/oracle_simulate.py:39, :150-153`), `hold_current_A` = i(`Vhold_`)(`:40`), measure `supply_current_A` = `rail_current_A[item.rail]`(`O/oracle_compare.py:136-139`). 테스트벤치 원천 `Vdc_`(`O/oracle_netlist.py:450`)·`Vbias_`(`:480`). `O/`에 `power` 문자열 0(grep) | 위 파일:줄 |

---

## 3. 패키지·파일 분할과 import 금지

### 3.1 디렉터리(기본안: P N0.1의 `O/core/`·`O/adapters/<이름>/` 고정을 따른다)

```
O/
  oracle_run.py            진입점(CLI). 입력 검증 -> 기술자 읽기 -> 어댑터 선택·주입 -> 코어 측정 -> 판정 -> 출력
                           (능력 확인 실행도 `oracle_run capability` 하위 명령이다 -- 진입점 하나, X-D2 결정 O-3. 검증자가 실행해 능력 기록을 만든다)
  oracle_input.schema.json 입력 스키마(새 형식, §11)
  core/                    코어 모듈 집합(완료 조건 1의 검사 대상, .py만)
    ir.py                  회로 IR 자료형(§4)
    requests.py            해석 요청 자료형(§5)
    results.py             정규화 결과 자료형·오류 코드(§6, §7)
    adapter_api.py         어댑터 계약(Protocol)·능력 선언 자료형(§8)
    descriptor.py          오라클 기술자 읽기·지문·검증(§10)
    build_circuit.py       입력 -> 본 회로 IR(free/forced/iso), Z1(omit/short)
    build_benches.py       파생 벤치(β 루프, CM 루프, ratio, rout, iso, pz 개루프, noise, MC, swing, C10 과도)
    identity.py            C15 topology 대조(IR 기준)
    measures_ac.py         ac_measures·pm_crosscheck·loop_gain·ratio/rout 수학
    stability.py           Nyquist·창 판정·조기 종결 규칙·tran 계획 수학·stability_judgement
    noise_math.py          잡음 밀도·적분·꼬리 판정
    mc_math.py             표본 수·V_os 식·σ 추정·진단 벡터 적용 순서(§13)
    swing_math.py          경계 탐색·창 계산
    compare.py             판정·비교(옛 oracle_compare 수학)
    capability.py          PC 벤치·판정·기록(§12)
    bundle.py              모델 묶음 비교 규칙(§12.5)
    cache.py               실행 캐시 키 원칙(§9)
    input_check.py         (v0.3.0) 입력 교차 칸 검사(§11.2 1d·2b), LUT 파일 읽기(코너·온도·모델 기록 모양) -- OP-3
    conduction.py          (v0.4.0) 판정 점 전도·포화 판정(채널 ID 부호·VDS ≥ VDSAT, 한 단계, §21.1), KCL 항등 0 전류 MOS 독립 유도 -- OP-5
    measures_dc.py         (v0.3.0) 계통 offset `.dc` 풀이 해석(§21.4), `.tf` A(§21.5), 전력 Σ V·I(§21.7) -- OP-5·OP-11
    slew_math.py           (v0.3.0) 계단 벤치·dV/dt 판정 수학(§21.6) -- OP-10
  adapters/
    ngspice/               첫 어댑터(사례)
      __init__.py          어댑터 객체(능력 선언 포함)
      dialect.py           IR·요청 -> 방언 텍스트
      run.py               실행(subprocess는 여기만)
      read.py              결과 읽기·내부 벡터 이름 대응·극성 정규화
      errors.py            로그 -> 오류 코드
      calibration.json     보정값(§8.3, 옛 oracle_config.json·_NGSPICE_DEFAULT_TOL·WRDATA_NUMDGT 출처 포함)
      calibration_tools/   (v0.2.6) 보정값 측정 도구(어댑터 지문 밖, §0 '어댑터 지문' 제외 목록 (ii)). 사례: measure_wall_s_per_window.py.
                           판정·실행 경로에서 import하지 않는다(§3.2)
  descriptors/
    <pdk>.oracle_descriptor.json   오라클 기술자(사례: sky130, §10)
    lut_file_roles/<생성기 sha256 앞 16자>.lut_file_roles.json   기존 LUT 기록 역할 옆 선언(검증자 작성, §12.5, v0.2.5)
  capability/
    <기술자 지문>__<어댑터 지문>.json  능력 기록(검증자 생성, §12.4)
  tests/
    core/                  코어 test(stub 어댑터, 텍스트 단언 금지)
    adapters/ngspice/      어댑터 test(손 넷리스트 독립 기준 포함)
    stub_adapter.py        stub 어댑터(test 작성자 소유, §3.3)
    fixtures/
      hand_model/          손 모델 픽스처 정본 하나(OP-5 산출, test 작성자 소유, §12.7): 기술자·그것이 참조하는
                           gmid_pdk_decl/1 형식 선언·손 모델 파일. 4a·OP-6이 재사용하고 새로 만들지 않는다
```

* 옛 파일 `oracle_netlist.py`, `oracle_simulate.py`, `oracle_noise.py`, `oracle_offset_mc.py`, `oracle_swing.py`, `oracle_compare.py`, `oracle_config.json`은 대체 card에서 삭제한다(§15). 각 진입점의 CLI 기능은 `oracle_run`의 하위 명령으로 합친다(결정(O-3), X-D2 수용). 이유는 진입점 정본을 하나로 두기 위해서다. 단 `--bias`별 단독 실행처럼 test가 쓰는 기능은 하위 명령으로 남긴다.
* (v0.2.5, 계획 v0.6.3 L-1·L-2 (6)) `legacy_adapter.py`·`legacy_testbench.json`은 이 기능의 파일 분할에 없다. gain-budget card LT-1 순서 3이 그 둘과 `test_legacy_testbench.py`, `tests/conftest.py`의 `--run-legacy`·`legacy_slow` 장치(S-27)를 지운다. 이 기능의 card는 그 파일들을 고치지 않는다(§11.4). LT-1 순서 3은 OP-2·OP-3보다 먼저도 뒤도 될 수 있다(계획 OP-2 행).
* (v0.2.5) `O/smoke/`의 스크립트 가운데 삭제 모듈을 import하는 넷(S-25)은 §15.4대로 그 모듈을 지우는 card가 같은 변경에서 처리한다. `measure_wall_s_per_window.py`(방언 실행 측정 도구, S-25)는 `oracle_config.json`을 옮기는 OP-4가 `adapters/ngspice/calibration_tools/`로 옮긴다(기본안 B-20, 폴더 이름 B-25, 계획 v0.6.5 '보정값 측정 도구는 지문 밖 하위 폴더').

### 3.2 import 금지(완료 조건 1)

| 모듈 | import 해도 되는 것 | 금지 |
|---|---|---|
| `O/core/*` | 표준 라이브러리(`subprocess` 제외), numpy, `O/core/*` | `O/adapters/**`, `subprocess`, `O/oracle_*.py` 진입점, 엔진(`gmid_engine`) |
| `O/adapters/<이름>/*` | `O/core/adapter_api`, `O/core/ir`, `O/core/requests`, `O/core/results`, 표준 라이브러리 | 다른 어댑터, `O/core`의 측정·판정 모듈, 엔진 |
| 진입점 | 위 전부 | 엔진 |
| (v0.2.6) `O/adapters/<이름>/calibration_tools/*` | 그 어댑터 패키지, 표준 라이브러리 | -- (반대 방향 금지: 코어·어댑터 실행 모듈·진입점은 이 폴더를 import하지 않는다. 그래야 지문 밖 폴더가 판정에 닿지 않는다) |

* `O/core/` 안에는 `.py`만 둔다(`__pycache__` 제외, P N5.3-1).
* 코어가 `O/core/` 밖에서 여는 파일은 셋뿐이다. 입력 JSON(과 그것이 sha256으로 가리키는 LUT 파일 `process.lut_files`, v0.3.0), 기술자 JSON(과 그것이 sha256으로 가리키는 파일), 결과 출력 디렉터리. 이 목록 밖의 열기는 test가 거부한다(§18 T1-4).
* (v0.3.0) 입력 JSON Schema 검증(§11.2 1c)은 **진입점 `oracle_run`**이 `O/oracle_input.schema.json`으로 한다. 코어는 스키마 파일을 열지 않는다(위 '셋' 규칙). 스키마로 쓸 수 없는 교차 칸 검사(§11.2 1d·2b)는 코어 `input_check.py`가 한다.

### 3.3 stub 어댑터(D-3, G-10)

* 위치는 `O/tests/stub_adapter.py`이고 test 작성자가 소유한다. 코어 interface(§5·§6·§8)만 보고 쓴다.
* 능력 선언: `op`, `ac`, `pz`, `tran`(선형 시간 해), `noise`(저항 열잡음만), (v0.3.0) `tf`(선형 DC 전달 함수 = MNA 해석해, §5 `Tf`). 선언하지 않는 것: `tran_early_stop`, `mc_native`, `mc_diagnostic`, `op_sweep`, `noise_device_contrib`.
* MOS는 입력 `predictions.devices`의 gm·gds·(cgg 등 있으면) 값으로 선형 스탬프한다. 비선형 op는 풀지 않는다.
* (v0.2.4) 기하: stub은 `geometry_unit_application`을 선언하지 않는다. 그래서 stub 실행 test의 기술자 픽스처는 `geometry_unit = "si"`와 `parallel_multiplier`를 선언한다(미선언 거부는 stub 앞 코어에서 일어나므로 OP-3 병합 조건 (a) test는 stub으로 돈다). 비 SI 단위 기술자를 stub에 주면 `adapter_capability_missing`(detail `geometry_unit_application`)이다(v0.2.5: 옛 `geometry_unit_unsupported`를 기존 코드로 합침, §7). stub은 `instance_geometry_readback`도 선언하지 않는다.

| 해석 | stub 처리 | test 종류 |
|---|---|---|
| op(선형), ac, β 루프, ratio, rout | MNA 해석해 | stub 실행 |
| C10 과도 | 선형 시간 해(성장 회로 = 선형 RHP 극 IR) | stub 실행(전체 창 경로, D-1) |
| pz | 해석해 극점 | stub 실행 |
| noise | 저항 4kT/R만 | stub 실행 / MOS 기여는 '능력 없음 거부' test |
| MC(네이티브·진단) | 미선언 | '능력 없음 거부' test |
| swing·ICMR(op 스윕), 계통 offset 훑기 | 미선언 | '능력 없음 거부' test |
| (v0.3.0) `.tf` A(§21.5), 계통 offset 한 점 풀이(§21.4) | `Tf` = MNA DC 해석해, 계통 offset 한 점 = 선형 `Op` | stub 실행(개루프 벤치 IR에 servo 원소가 없음을 단언하는 test 포함) |
| (v0.3.0) 슬루 `.tran`(§21.6) | MOS 선형 스탬프의 시간 해에는 슬루 제한이 없다 | '능력 없음 거부' test(슬루 요청은 어댑터 능력 `tran_large_signal` 필요, §8.3 -- stub은 선언하지 않는다) |

---

## 4. 회로 IR(G-1, G-12)

### 4.1 자료형(`core/ir.py`, frozen dataclass)

```
Net(name: str)                                   # 입력 넷 이름 그대로. 0 넷은 Ground 상수
Mos(name, kind, d, g, s, b, L, finger_w, n_fingers, diffusion: Diffusion|None, lod: Lod|None)
Resistor(name, a, b, value)     Capacitor(name, a, b, value)     Inductor(name, a, b, value)
VSource(name, p, n, dc, ac_mag=0.0, ac_phase=0.0, tran: Pulse|None=None)
ISource(name, p, n, dc, ac_mag=0.0)
Vcvs(name, p, n, cp, cn, gain)                   # 옛 Efb_
Probe(name, kind='current', a, b)                # 0 V 감지원(옛 Vhold_ 등)
Diffusion(ad, as_, pd, ps)      Lod(sa, sb, sd)  Pulse(v1, v2, td, tr, tf, pw, per)
Circuit(elements: tuple, role: dict[name -> 'circuit'|'testbench'], meta: dict)
```

* **원소 종류는 필드다.** 이름 접두사(S-9)는 방언 규약이라 어댑터가 정한다. 그래서 IR 이름은 입력 이름 그대로 쓰고, 테스트벤치 원소 이름은 코어가 `tb:<용도>:<대상>` 형태로 만든다(예: `tb:servo:out`). 어댑터는 그 이름을 방언에서 쓸 수 있는 이름으로 바꾸고 대응표를 결과에 싣는다(§6).
* **역할 표**: `role`은 원소가 본 회로인지 테스트벤치인지 담는다. C15 topology 대조(`core/identity.py`)는 `role == 'circuit'` 원소만 topology와 비교한다. 지금은 넷리스트 텍스트를 다시 파싱해서 하지만(`parse_netlist_elements`, `O/oracle_netlist.py:1105`), 이 경로를 대체한다.
* **대소문자**(G-12): 코어는 넷·원소 이름을 그대로 둔다. 어댑터 능력 `case_insensitive_names`가 참이면, 코어는 벤치를 넘기기 전에 이름을 소문자로 접었을 때 충돌하는지 검사하고 충돌하면 거부한다(`ir_name_collision`). C15 대조는 IR 이름 기준이라 대소문자 접기의 영향을 받지 않는다. 옛 `_Nets`의 충돌 규칙(`O/oracle_netlist.py:86-110`)은 이 검사로 대체한다.

### 4.2 IR 생성기(`core/build_circuit.py`, `core/build_benches.py`)

| 옛 기능(텍스트 생성) | 새 IR 함수 | 비고 |
|---|---|---|
| `build_netlist(inp, bias, ...)` 본 회로 부분 | `circuit_ir(inp, bias) -> Circuit` | free/forced/iso, `apply_z1` 포함 |
| 같은 함수의 `.control` 부분 | `main_requests(inp, bias, meta) -> tuple[Request]` | §5 |
| `stability_op_netlist`·`stability_netlist` | `stab_benches(circuit, plan, ...)` | choke → 고정 전류원·초기 조건은 IR 원소와 요청 조건으로((v0.3.7, 검증 nice-to-fix) 초기 조건 = 슬루와 같은 `Tran.ic` 칸 하나(§5)이고 같은 능력 `tran_ic_bias_only`(§8.3)가 관문이다 -- 지금 C10 `.ic`(`O/oracle_netlist.py:596-598`·`:625` choke 노드, `:720` kick 출력 노드, `:765` `uic` 없는 `tran`)는 아직 능력 관문 밖에 있다 -- (v0.3.7 둘째 커밋 정정, 검증 보고 5: 옛 문장 '옮기는 card는 §20 범위표에 아직 없다'는 틀렸다) §20 OP-3 행이 §4(이 `stab_benches` 행 포함)·§5(`Tran`)·§8.1~8.3(능력)을 범위로 가지므로 C10을 이 칸·능력으로 옮기는 것은 **OP-3 몫**이다. (v0.3.8 둘째 커밋 정정, v0.3.8 검증 M1 -- 앞 문장의 'OP-3 몫'과 v0.3.8 첫 커밋의 'OP-3 소유'는 틀렸다: 계획 OP-4 행(`oracle-portability.plan.md` 500행 "안정성: C10 규칙 코어화 … `stability_op_netlist` 삭제")과 N4 OP-4 행(467행 "C10 판정 상태·창 수 등 … '기존 과도 fixture 판정 불변'")이 C10을 **OP-4**에 둔다; 옛 문장 history v0.3.8 둘째 커밋) 1b가 AP-1로 빠졌으므로(계획 v0.6.15 DR-23 (1)) OP 범위에서 `Tran.ic`·`tran_ic_bias_only`의 소비자는 **OP-4의 C10 하나**이고, 칸·능력을 만드는 card도 **OP-4**다(같은 card에서 만들고 배선 -- 만든 card와 쓰는 card 사이에 소비자 없는 칸이 생기지 않게): C10 동작점 패스의 choke 노드 `.ic`(`O/oracle_netlist.py:596-598`·`:625`)와 kick 출력 노드 `.ic`(`:720`)를 이 칸으로 옮기고, ngspice 어댑터가 `tran_ic_bias_only = true`를 선언한다(§20 OP-4 행·§18.1 'OP-4 C10 `.ic`' 행). 이 `stab_benches` 행 전체가 OP-4 몫이다(§20 OP-3 행의 §4·§5 범위에서 C10 과도 몫은 뺌). 남은 미확인 = DV-20(uic 없는 `.ic` 의미의 원문 쪽, C10 몫)) |
| (A-81) forced 고정원 | `circuit_ir` 의 forced 배치: 예측 전압원 + 가 넷, − 가 `hs_<넷>`, choke `hs_<넷>`→접지 (옛 `hs` 0 / choke `hs` 넷 과 DC·AC·i(V) 부호 동등). OP-4 는 C10 동작점 패스의 choke 꼴을 이 배치에 맞춘다 | |
| `open_loop_parts`·`pz_netlist`·`openloop_tran_netlist` | `pz_bench`, `openloop_tran_bench` | 동작점 값으로 개루프를 다시 만드는 규칙은 코어(회로 이론), pz 신뢰는 §8.5 |
| `_rout_runs`·`_ratio_runs`·`_loop_tail` | `rout_requests`, `ratio_requests`, `loop_requests` | 여기 전환(`alter @..[acmag]`)은 요청의 `excitation` 덮어쓰기로 바꾼다(§5) |
| `build_iso_netlist` | `iso_bench` | |
| `build_mc_netlist`(래퍼 subckt·`alterparam`) | 삭제. 네이티브 MC 요청(§5 `McNative`) + 진단 요청(§13) | O-1 |
| `_Sweeper`(`alter dc` + `op`) | `OpSweep` 요청(§5) | |
| (v0.3.2) 없음(OP-5·OP-10 새 벤치) | `sweep_bench`(swing 개루프 벤치·ICMR 측정 구성 벤치 `measure_feedback`, §21.2), `tf_bench(port=None)`(개루프 `.tf` -- `port` 없음 = `dc_sweep.excite` 가중 §21.5, `port` = 그 입력 포트 하나 단위 여기 = 반전 포트 판정 §21.2), `ioff_bench`(소자 개별 풀이, 온도 점 §21.1), 계통 offset 출력 기준 servo 벤치 `offset_bench`(§21.4), 슬루 계단 벤치 `slew_bench`(§21.6) | 이름은 기본안 B-46 범위 |
| `_refine_text` | 같은 IR에 좁은 `Ac` 요청을 다시 보냄 | |

---

## 5. 해석 요청(G-2, `core/requests.py`)

```
Condition(temp_c: float, corner: str)                          # 모든 요청에 붙는다. 기본 = LUT 메타(§11.2)
Excitation(overrides: tuple[(source_name, field, value)])       # ac_mag·dc 덮어쓰기(옛 alter)
Op(id, cond, exc=(), outputs: OpOutputs)                        # OpOutputs = (devices: names|'all', nodes, currents, nodes_full)  (v0.4.9, OP-5, 아래 '전 자릿수 넷')
Ac(id, cond, exc, f_start, f_stop, points_per_decade|None, f_list|None, outputs: tuple[Expr])
Noise(id, cond, exc, out: Expr, src: source_name, f_points, contrib: bool)
Tran(id, cond, exc, plan: TranPlan, outputs: tuple[Expr], save_only: bool, early_stop: EarlyStopRule|None, ic: tuple[(net, V)] = ())   # ic = (v0.3.6) 바이어스 전용 초기 조건, 능력 `tran_ic_bias_only`. (v0.3.8, DR-23 (1); 둘째 커밋 M1 정정) 칸을 만드는 card·소비자 = OP-4 C10(§4.2 `stab_benches`); §21.6 1b는 gain-budget card AP-1 몫
Pz(id, cond, exc, in_pair, out_pair, kind='voltage')
OpSweep(id, cond, base_exc, points: tuple[Excitation], outputs)
McNative(id, cond, n_samples, seed, outputs, keep_identity: bool)     # 네이티브 MC(§10.4)
McDiagnostic(id, cond, vectors: tuple[DiagnosticVector], outputs)      # 결정적 섭동(§13), 판정 금지
Tf(id, cond, exc, out: Expr, src: source_name)                         # (v0.3.0) DC 소신호 전달 함수(§21.5). 능력 `tf`
Expr = NodeV(net) | DiffV(net_p, net_n) | BranchI(element) | Ratio(Expr, Expr)
```

* (v0.3.0) `.dc` 훑기(swing·ICMR, §21.2)는 새 요청 종류를 만들지 않고 `OpSweep`(점마다 `Excitation`의 DC 덮어쓰기)으로 낸다. 계통 offset 한 점 풀이(§21.4)는 `Op` 하나다. 슬루(§21.6)는 `Tran`에 계단 원(`VSource.tran = Pulse`)을 둔 벤치다. 그래서 요청 종류가 느는 것은 `Tf` 하나다.

* (v0.4.9, A-84 C-10, OP-5) **전 자릿수 넷** `nodes_full`: 어댑터가 그 넷을 시뮬레이터가 내는 전 자릿수로 읽는다(자릿수 = 어댑터 보정값 `print_digits_full`, 출처 칸 필수). swing·ICMR·계통 offset·σ 요청 입력의 공칭 free 벤치에서 입력 넷만 쓴다. 비어 있으면 넷리스트 불변이라 그 요청이 없는 입력은 기준선 동일성에 영향이 없다.
* 요청은 방언을 모른다. 출력은 IR 넷·원소 이름의 식(`Expr`)이다. 옛 `let hout = ...` 같은 방언식은 어댑터가 만든다.
* `EarlyStopRule`은 코어 규칙 자체(창 경계, floor', reltol, g↑·g↓·한계 사이클 판정에 필요한 값)를 담는 자료다. 능력이 있는 어댑터는 이것을 방언 스크립트로 옮긴다. 능력이 없는 어댑터에서는 코어가 이 규칙을 사후에 적용한다. 실행 방식(전체 창 한 번 / 창별 재실행)은 §8.4의 G-13 후보 가운데 OP-4가 고른다(측정 S-19).
* `keep_identity`: 같은 `seed`·같은 `n_samples`로 다른 `Condition`(온도)을 요청하면 같은 표본(같은 불일치 값)을 재야 한다는 요구다(PC-6, offset-trim N3.8.2). 어댑터가 이 능력을 선언하지 않으면 코어가 거부한다.

---

## 6. 정규화 결과(G-2, `core/results.py`)

```
RunStatus(rc: int|None, timed_out: bool, error: ErrorCode|None, warnings: tuple[str], log_excerpt: tuple[str],
          log_path: str|None, cache_state: None|'hit'|'miss'|'off')
                                   # (v0.2.6) cache_state = 옛 run_ngspice 캐시 상태 넷 그대로(`O/oracle_simulate.py:105-110`: None = 캐시 안 씀,
                                   # 'off' = 옛 'off(모델 파일 못 찾음)'), log_path = 옛 `log`. v0.2.5의 cache_hit: bool은 넷째 상태를 담지 못해 바꿨다
                                   # 벤치(프로세스 실행) 단위. error = 벤치 전체를 막은 오류만(프로세스 실패·시간 초과·모델 없음 등, §7.1)
                                   # rc = 시뮬레이터 종료 코드. 시간 초과로 끊기면 None + timed_out = True + error = sim_timeout
OpTable(devices: {name: {param: value}}, nodes: {net: V}, currents: {element: A}, resolution: Resolution, error: ErrorCode|None,
        instance_geometry_reported: {name: {field: value}}|None)
                                   # 시뮬레이터가 보고한 인스턴스 기하 **원값**(단위 되돌리기·배수 역적용 없음). field = 코어 공통 이름 L·W·multiplier,
                                   # 각 값이 어느 시뮬레이터 보고 칸에서 왔는지는 ResultBundle.name_map에 싣는다(§10.6, 완료 조건 4a)
FreqSeries(f: array, values: {expr_key: complex array}, resolution: Resolution, error: ErrorCode|None)
NoiseResult(total_in, total_out, density: FreqSeries|None, contrib: {element: {source_kind: value}}|None, resolution, error)
TimeSeries(t: array, values: {expr_key: array}, stopped_early: bool, windows_done: int, resolution, error)
Poles(values: tuple[complex], status: 'ok'|'failed', resolution, error)
SweepResult(points: tuple[OpTable|None], error)
McResult(samples: tuple[OpTable|None], seed, identity_kept: bool, error)
TransferResult(gain: float|None, out_impedance: float|None, in_impedance: float|None, resolution, error)
                                   # (v0.3.0) Tf 요청 결과(§21.5). 부호 있는 실수(위상 검사 없음). 어댑터가 방언 로그 세 줄을 읽어 낸다(S-42)
                                   # 각 결과의 error = 그 요청 단위 오류(예: pz 반복 한도 -> Poles.status 'failed' + error, 같은 벤치의 다른 요청은 그대로, §7.1)
Resolution(reltol, abstol: {quantity: value}, data_rel: float|None, source: 'input_options'|'adapter_declared')
                                   # DC 풀이 허용오차(reltol, vntol, abstol)는 이 칸이 정본. 값이 없으면 어댑터가 결과를 내지 않는다(§8.3)
ResultBundle(bench_id, adapter_fp, descriptor_fp, status: RunStatus, by_request: {request_id: result},
             name_map: {ir_name: dialect_name, "geometry_fields": {field: <시뮬레이터 보고 칸 이름>}}, method: str,
             bundle_files: {path: {"lf": sha256, "raw": sha256}})
                                   # (v0.3.0) bundle_files = 이 벤치의 모델 묶음(§8.1 model_bundle 반환 그대로). 모델 묶음 비교(§12.5)의 입력
RunRecord.machine_dependent_refs: [{"ref": <참조 이름>, "path": ..., "recorded_sha256": ..., "matched": "raw"}]
                                   # (v0.3.0, 계획 NFR-P9·FR-P9, DR-11) 실행 하나(입력 한 개)의 결과 JSON 최상위 칸. 규칙 (ii)로 raw 값과만 맞은 옛 기록 전부.
                                   # ref = `engine_source:<키>` | `lut_model_file:<kind>:<상대 경로>` | `lut_generator:<LUT 파일>`. 없으면 빈 목록(칸은 늘 있다)
                                   # method = 어댑터가 쓴 해석 방법 설명(옛 결과 `method` 칸 값, S-24). 코어는 이 문자열을 만들지 않는다
```

* **극성 정규화는 어댑터 몫이다**(F-9). `OpTable.devices[*]`는 README '크기 규칙'(선언 단자 방향 부호, ID 부호 포함, VSB 양수)을 이미 따른다. 옛 `oracle_compare.signed_id`(`O/oracle_compare.py:226`)는 ngspice 어댑터 `read.py`로 옮긴다.
* op 파라미터 이름은 코어 공통 이름(`id, gm, gds, vth, vdsat, vgs, vds, vbs`)이다. 어댑터는 기술자 `model_family`(§10)에 맞는 표로 자기 시뮬레이터 이름과 대응시킨다. 대응이 없는 파라미터는 `None`이고 조용히 다른 값을 넣지 않는다.
* `instance_geometry_reported`는 어댑터 능력 `instance_geometry_readback`(§8.3)이 참일 때 채운다. (v0.2.5 고침, 검증 경미 지적) 어댑터는 보고값을 **되돌리지 않는다**. v0.2.4는 어댑터가 기술자 규칙을 거꾸로 적용해 IR 단위로 돌려주게 했는데, 그러면 4a 단언이 '어댑터가 쓴 변환을 같은 어댑터가 되돌린 값 = IR'이 되어 전달 규칙 오류를 잡지 못한다(같은 규칙을 두 번 적용하면 오류가 상쇄된다). 그래서 4a는 **시뮬레이터 보고 원값**을 **test 작성자가 기술자 선언과 IR에서 따로 계산한 기대값**과 비교한다(§18.1 4a 행). 보고값이 배율 적용 전인지 뒤인지의 근거는 시뮬레이터 매뉴얼 쪽(R6)이고 test 작성자가 기대값 계산에 그 쪽을 인용한다.
* 결과 칸 이름에 시뮬레이터 이름을 넣지 않는다. 옛 `ngspice_rc`(S-3, S-23)는 같은 자리의 `status`(`RunStatus`, 그 안 `rc`), 옛 `ngspice_runs`(S-17)는 `sim_runs`다(§15.1). 경로별 대응과 `None` 처리는 §11.5 '결과 칸 이름 대응'이 정본이다.
* `method` 값(S-24)은 어댑터가 `ResultBundle.method`로 낸다. 코어가 결과 JSON에 옮길 때 그대로 옮긴다. 그래서 코어 문자열 리터럴에 시뮬레이터 이름·방언 해석 이름이 들어가지 않는다(완료 조건 1 T1-1).
* 결과 JSON에는 그 실행에 쓴 DC 풀이 허용오차(`Resolution`의 reltol·vntol·abstol과 출처)를 그대로 싣는다. offset-trim trim 잔여 수렴 분해능(T-39)은 이 값을 입력 환산으로 전파해 얻는다(§13.4).
* `Resolution`은 판정 분해능 계산(§8.3, 계획 N4-2)의 입력이다. 옛 `data_rel_resolution`·`mp_resolution`·`solver_floor`·`reltol_of`의 수학은 코어에 남고, 자릿수·기본 허용오차 값만 어댑터가 준다.

### 6.1 새 칸의 소비자(v0.2.6, 검증 중간 지적 '소비자 미정 칸')

이 문서가 새로 만든 칸마다 **읽는 곳**을 정하거나 **출력 전용**으로 선언한다(사용자 확인 항목 'graph 계산값 소비'의 오라클판: 쓰고 아무도 읽지 않는 칸을 두지 않는다. 출력 전용은 결과 JSON·판정 기록에만 실리고 코드 판정이 읽지 않는 칸이다). 칸을 더하는 card는 이 표의 소비자를 같은 변경에서 배선한다(P NFR-P4).

| 칸 | 소비자(읽는 곳) 또는 출력 전용 | 근거 |
|---|---|---|
| `RunStatus.rc` | 코어 결과 조립(0이 아니고 결과가 없으면 `error`가 정해졌는지 확인), N4 비교 칸(§11.5) | 옛 `ngspice_rc` 자리 |
| `RunStatus.timed_out` | 코어 `stability`(시간 초과 → 그 과도·연장·확인 실행 `status = "failed"`, 옛 `_run_stab`의 사유 반환 `:1066-1067`과 `:1175-1176` 등을 대체), pz(시간 초과 → `Poles.status = "failed"`), §11.5 `None` 대응 | 옛 `to`·`sto` 변수 |
| `RunStatus.error` | 코어 `compare`의 막힘 판정(옛 `op_ok`·`log_errors` 막힘 `O/oracle_compare.py:378-387`을 대체: 벤치 `error`가 있으면 그 코드로 막힘 문장), 코어 `capability` PC-1(op 수렴) | §7.1 오류 단위 |
| `RunStatus.log_excerpt` | 코어 `compare` 막힘 문장의 발췌(옛 `log_errors` 600자 발췌 자리). 발췌 줄은 어댑터가 §7.1 대응표로 오류에 대응한 줄만 고른다(옛 정규식 거짓 적중 S-18 제거) | `O/oracle_compare.py:379, :384, :387` |
| `RunStatus.warnings` | **출력 전용**(정보, §7.1 회복된 경고). 판정이 읽으면 회복된 실행을 다시 실패로 만들게 되므로 읽지 않는다 | §7.1 |
| `RunStatus.log_path` | **출력 전용**(옛 `log`, 소비자 없음 S-32) | S-32 |
| `RunStatus.cache_state` | 코어 결과 조립이 캐시 상태 표 `sim.cache`·`sim.stability_cache`로 옮긴다(옛 C21 '캐시 상태는 결과가 아니다', `O/oracle_simulate.py:1369`). 결과 칸 `status` 안에는 싣지 않는다(§11.5). 판정은 읽지 않는다. test 소비자 = §18.2 캐시 test 넷 | S-32 |
| `McResult.identity_kept` | 코어 `mc_math`가 여러 조건(온도) 표본을 같은 표본으로 묶기 전에 읽는다. 요청이 `keep_identity`인데 거짓이면 그 요청 결과를 `mc_identity_lost`(요청 단위, §7)로 거부하고 묶지 않는다(어댑터 선언 `keep_identity_across_conditions`와 실제 동작이 어긋난 경우의 fail-closed). PC-6은 같은 값을 측정 증거로 기록한다 | P PC-6, §10.4 |
| `mc_enable_kinds.<how>.seed` | 코어 §7.2 5단계: `McNative` 요청은 `seed`를 싣는다. 그 켜는 법의 `seed`가 `"none"`이면 요청의 시드를 적용할 수 없으므로 `adapter_capability_missing`(`detail = "mc_seed"`)로 거부한다. 이것은 새 판정 요구가 아니라 '요청 칸을 실행할 능력'의 확인이다(계획 X-20: 시드 전달 = 어댑터 능력) | §5 `McNative.seed` |
| `mc_enable_kinds.<how>.samples_per_run` | 어댑터 자신(표본마다 별도 실행 여부, §10.4)과 코어 §11.5 offset_mc 대응(`sample_status` 묶음) | §10.4 |
| `lut_file_roles/1`의 `evidence` | 코어 기술자 읽기가 형식 검사로 읽는다: `evidence` 칸 존재, `evidence.generator.file_sha256 = generator_sha256`(다르면 `lut_file_roles_invalid`). 나머지 근거 내용(줄 번호, include 그래프 파일 목록)은 **출력 전용**(검증자 판정 기록·독립 검증이 읽는 측정 근거). 코어가 근거를 다시 재지 않는 이유: 근거는 검증자 측정이고(계획 N4-2a 예외) 코어가 재면 작성자가 측정을 대신하게 된다 | §12.5 |
| `ResultBundle.method` | **출력 전용**(결과 JSON `method` 칸, N4 비교 제외) | S-24 |
| `ResultBundle.name_map` | 코어 결과 조립(방언 이름 → IR 이름), 검증자 N4-3 정규화 입력(§10.6, 의존 기록) | §4.1 |
| `OpTable.instance_geometry_reported` | 완료 조건 4a test(§18.1). 판정 코드는 읽지 않는다 | §10.6 |
| `ResultBundle.adapter_fp`·`descriptor_fp` | 코어 캐시 키(§9), 능력 기록 유효성(§12.6), 결과 JSON 지문 칸(P FR-P9) | §9, §12.6 |
| (v0.3.0) `ResultBundle.bundle_files` | 코어 `bundle.py` 규칙 (i)~(iii) 대조(§12.5), 캐시 키의 묶음 목록(LF 값, §9) | DR-10d |
| (v0.3.0) 결과 `machine_dependent_refs` | **출력 전용**(계획 NFR-P9: 결과에 남겨 사람·검증자가 읽는다). 능력 기록에는 같은 목록을 옮긴다(§12.4). 판정 코드는 읽지 않는다 -- 기계 의존 일치는 거부 사유가 아니다(계획 N3.4 (ii)) | DR-11 |
| (v0.3.0) `TransferResult.gain` | 코어 `mc_math`(불일치 σ의 A, §21.5), 결과 `sim.a_dc.value`(v0.3.4·v0.3.5: 옛 `offset_mc.a_dc_signed`를 sim 단계 `sim.a_dc` 기록으로 옮김 -- σ·계통 offset이 함께 읽는 한 측정, §21.5 3단계), 갈래 판정(§21.5 4단계)·§21.4 4단계(a) | OQ-6 |
| (v0.3.0) `TransferResult.out_impedance`·`in_impedance` | **출력 전용**(결과 `offset_mc.tf_record`, 벤치 확인용 기록) | S-42 |
| (v0.3.0) 결과 `summary.conduction_definition` | gain-budget EO-1 판정 기록('꺼짐 정의 판' -- gain-budget N6.20 'EO-1 뒤 OP-5 전 기간') | §11.7 |
| (v0.3.0) 결과 `record_id` | gain-budget EO-1 판정 배선(엔진 점 레코드에 붙이는 판정 기록 id, gain-budget N6.20 범위 (2)) | §11.7 |

---

## 7. 오류 분류(G-4)

| 코드 | 뜻 | 낸 곳 |
|---|---|---|
| `sim_convergence_failed` | DC·과도 수렴 실패 | 어댑터 |
| `sim_singular_matrix` | 특이 행렬 | 어댑터 |
| `sim_timestep_too_small` | 시간 걸음 실패 | 어댑터 |
| `sim_timeout` | 실행 시간 상한 초과 | 어댑터 |
| `sim_model_not_found` | 모델·bin을 못 찾음 | 어댑터 |
| `sim_failed_other` | 그 밖(로그 발췌 첨부) | 어댑터 |
| `adapter_capability_missing` | 요청에 필요한 능력 미선언. `detail` = 능력 이름. (v0.2.5) 기술자가 비 SI 기하 단위를 선언했는데 어댑터 `geometry_unit_application`에 적용 방법이 없을 때도 이 코드다(`detail = "geometry_unit_application"`) | 코어 |
| `adapter_calibration_missing` | 보정값 없음(예: 창당 상한, §8.3). `detail` = 보정값 이름. (v0.2.5) `global_directive` 방법인데 `global_geometry_directive.affects`·`power` 선언이 없을 때도 이 코드다 | 코어 |
| `ir_name_collision` | 대소문자 접기 충돌(§4.1) | 코어 |
| `oracle_input_format_old` | 옛 입력 형식(D-5). (v0.3.0) `detail.markers` = 걸린 옛 표지 목록(§11.2 1b) | 진입점 |
| `oracle_input_schema_invalid` | (v0.3.0) 입력이 OP-3 스키마(§11.1)를 어김: JSON 읽기 실패, JSON Schema 위반, 스키마로 쓸 수 없는 교차 칸 규칙 위반(§11.2 1d). `detail` = `[{pointer, rule}]` 전부. (v0.3.0 검증 지적 9로 정함) **`pointer`** = 문제 키 자체의 JSON 포인터다 -- `required` 위반이면 빠진 키의 포인터(사례 `/schema`), `additionalProperties` 위반이면 남는 키의 포인터(사례 `/declared_triode` -- 옛 형식 표지 키는 1b가 먼저 거른다), 그 밖은 값이 어긴 칸의 포인터. JSON 읽기 실패는 `""`. **`rule`** = JSON Schema 키워드(`required`, `additionalProperties`, `enum`, `pattern`, `type`, `const`, `minItems`, `minimum`, `exclusiveMinimum`, `uniqueItems`, `minLength`, `minProperties`) 또는 1d 규칙 이름(`lut_kind_coverage` 등, §11.2·§11.6) 또는 `json_parse`. 정렬 = (`pointer`, `rule`) 문자열 쌍의 사전순, 중복 쌍은 하나로. 산출물(넷리스트·결과)을 쓰지 않는다(옛 C13 동작과 같음, 거부 기록 하나만 §11.7) | 진입점(1a·1c), 코어 `input_check`(1d) |
| `adapter_unknown` | (v0.3.0) `simulator.adapter`가 등록된 어댑터 이름이 아님. `detail` = `{name, known: [...]}` | 진입점 |
| `simulator_exe_missing` | (v0.3.0) 실행 파일 경로가 CLI `--sim-exe`에도 `simulator.exe`에도 없음, 또는 그 경로에 파일이 없음(옛 '실행 파일 경로 없음' 반환 2, `O/oracle_run.py:86-89`) | 진입점 |
| `descriptor_kind_undeclared` | (v0.3.0) `devices[].kind`가 기술자 `kinds`의 키가 아님. `detail` = `{kind, devices: [...]}`. 기하 칸이 빠진 경우(`descriptor_geometry_undeclared`)와 구분한다 | 코어 |
| `lut_file_stale` | (v0.3.0) `process.lut_files[i]` 파일의 raw sha256(계획 N3.4 규칙 (iv), git 밖 LUT 데이터)이 입력 값과 다르거나 파일이 없음. `detail` = `{index, path, expected_sha256, actual_sha256 \| "missing"}` | 코어 |
| `lut_meta_shape_mismatch` | (v0.3.0, 계획 N9 '관찰' 행) LUT 파일 meta `model_files_sha256`의 모양이 입력 `kinds` 선언과 맞지 않음 또는 모르는 모양. `detail.why` ∈ `flat_multi_kind`(평탄 표인데 kind가 둘 이상), `meta_key_given_for_flat`, `meta_key_missing_for_nested`, `nested_key_absent`(중첩 dict에 선언한 키가 없음), `unknown_shape`(값이 전부 문자열도 전부 dict도 아님). 조용히 평탄화하지 않는다 | 코어 |
| `lut_condition_conflict` | (v0.3.0) `process.lut_files`의 파일들이 기록한 `corner` 또는 `temp_c`가 서로 다름(§11.2 2b). `detail` = `{key, values: {index: value}}` | 코어 |
| `oracle_condition_missing` | LUT 메타와 입력 모두 온도·코너가 없음(§11.2) | 코어 |
| `descriptor_source_duplicated` | 같은 원본 파일(경로 또는 sha256)이 엔진 선언 `sources`와 기술자 `extra_sources` 두 곳에 있음(§10.1, 계획 N3.4). (v0.3.0, DR-4, 계획 N3.4 규칙 (iii)) '같은 sha256'은 **기록값끼리가 아니라** 엔진 `sources` 모든 파일(기술자가 쓰지 않는 원본 포함)과 `extra_sources` 파일을 바이트에서 LF 정규화로 다시 잰 값끼리 비교한다. 엔진 `sources`의 어느 파일이든 없으면 중복을 판정할 수 없으므로 `pdk_descriptor_stale`(`actual_sha256 = "missing"`)로 거부한다. `detail` = `{path_or_sha, engine_source_key, extra_source_key, by: "path" \| "lf_sha256"}` | 코어 |
| `descriptor_schema_invalid` | (v0.2.5) 기술자 JSON이 `oracle_pdk_descriptor/1` 스키마(필수 칸, 칸 형식, 닫힌 키 집합)를 어김. 사례: `extra_sources.<key>.provenance`가 비어 있음(§10.1). `detail` = JSON 포인터 + 어긴 규칙. `mc.distribution` 칸의 위반은 이 코드가 아니라 `mc_distribution_inline`으로 낸다(§10.4) | 코어 |
| `pdk_descriptor_stale` | 기술자가 참조한 sha256과 실제 파일 sha256이 다름. (v0.2.5) `detail` = `{ref, path, expected_sha256, actual_sha256}`. `ref` ∈ `engine_decl`, `extra_engine_decl:<key>`(v0.4.8), `engine_source:<key>`, `extra_source:<key>`, `lut_location_decl`(v0.2.6), `lut_file_roles[<i>]`, (v0.3.0) `input_descriptor`(입력 `process.descriptor.sha256`). 대조는 §7.2 2단계 한 곳에서만 한다(v0.2.6). 파일이 없으면 `actual_sha256 = "missing"`. **(v0.3.0, DR-4, 계획 N3.4 'sha256 정의') 어느 정의로 잰 값인지**: 기술자 칸·입력 `process.descriptor`는 규칙 (i)이라 `actual_sha256` = 파일의 LF 정규화 값 하나다(raw를 적은 칸은 CRLF 체크아웃에서 이 코드로 거부된다 -- 완료 조건 4의 깨진 변형). 엔진 원본 raw 기록(`engine_source:<key>`, `newline` 없는 항목)은 규칙 (ii)라 `detail`에 `actual_sha256 = {"lf": …, "raw": …}` 둘을 싣고, 기록값이 둘 다 아닐 때만 이 코드다. raw로만 맞으면 오류가 아니라 결과 `machine_dependent_refs`(§6)에 적는다. `newline: "lf"`가 있는 엔진 원본 항목은 규칙 (i)처럼 LF 값 하나로 본다 | 코어 |
| `model_bundle_mismatch` | 모델 묶음 비교 규칙 (i)·(ii) 위반(§12.5). (v0.2.5) `detail` = 어긴 규칙 번호, kind, 빠진 sha256 목록과 그 기록 경로, 역할 미선언으로 모델 파일로 본 기록 경로 목록. (v0.3.0, DR-10b) '빠짐' = 그 LUT 기록값이 묶음의 **어느 파일의 LF 값과도 raw 값과도** 같지 않음(규칙 (ii)). raw로만 맞은 기록은 빠짐이 아니라 `machine_dependent_refs`(§6)에 적는다 | 코어 |
| `lut_aux_input_mismatch` | (v0.2.5, 계획 N3.5 규칙 (iii), G-4·G-17) LUT 생성 보조 입력 기록의 sha256이 기술자 LUT 기록 뿌리 아래 같은 상대 경로 파일의 지금 sha256과 다르거나, 그 파일이 없음. `detail` = `{path, recorded_sha256, actual_sha256 \| "missing"}`. (v0.3.0, DR-10b) '다름' = 기록값이 그 파일의 LF 값도 raw 값도 아님. `actual_sha256` = `{"lf": …, "raw": …}`. raw로만 맞으면 기계 의존 표시 | 코어 |
| `lut_file_roles_invalid` | (v0.2.5) 역할 옆 선언 파일(§12.5)이 `lut_file_roles/1` 형식을 어김(닫힌 키 집합, 역할 값 ∉ {`model_file`, `generation_aux_input`}, 근거 칸 없음, (v0.2.6) `evidence.generator.file_sha256` ≠ `generator_sha256`). §7.2 2단계. 형식이 맞지만 그 슬라이스에 적용되지 않는 선언은 이 코드가 아니다(적용 안 됨 = 역할 미선언, §12.5) | 코어 |
| `lut_location_decl_invalid` | (v0.2.6) 기술자 `lut_record_root.location_decl`이 가리키는 위치 선언 파일의 형식 오류(`E/lut/CONTRACT.md` 1.8 형식 아님, `pdk_root` 칸 없음, `env`·`default` 둘 다 없음). 기술자 자체의 스키마 위반(`descriptor_schema_invalid`)과 구분한다. `detail` = `{item, why}`. §7.2 2단계 | 코어 |
| `lut_record_root_mismatch` | (v0.2.6) 기술자 `lut_record_root`(§10.2)로 푼 뿌리 아래의 파일이 LUT 기록과 다른 PDK 트리를 가리킴. 스키마 위반이 아니라 **값 불일치**다(형식은 맞고 두 정본이 서로 다른 트리를 가리킴). (v0.3.0 다시 씀, DR-10b·DR-10c, 계획 N3.4 규칙 (iii) -- 기록값끼리 비교 삭제) 판정은 §7.2 8단계 첫머리의 세 걸음이다: (1) **짝** = LUT 기록 (상대 경로, 기록값) 가운데 기록값이 어떤 엔진 원본 파일의 LF 값 또는 raw 값과 같은 (상대 경로, 엔진 원본 키) 쌍(규칙 (ii)) (2) 짝마다 뿌리 아래 그 상대 경로 파일의 **LF 값** == 그 엔진 원본 파일의 **LF 값**(둘 다 파일 바이트에서 다시 잼). 다르거나 없으면 이 코드, `detail` = `{path, engine_source_key, root_file_lf_sha256 \| "missing", engine_file_lf_sha256}` (3) 짝이 0개면 이 코드, `detail = {"why": "no_pairs"}`(두 정본이 같은 트리라는 증거가 없음). 함수와 test는 OP-3(계획 O-14 (4) J-5 (가)) | 코어 |
| `adapter_fingerprint_unavailable` | (v0.2.6) 어댑터 코드 지문을 계산할 수 없음: 패키지 아래 파일을 읽지 못함, 또는 `calibration.json`을 읽지 못함·JSON 아님(§0). `detail` = `{why, path}`. 지문이 없으면 캐시 키·능력 기록·결과 지문 칸을 만들 수 없으므로 실행 전에 거부한다(§7.2 1단계, 어댑터 선택 때) | 어댑터 `fingerprint()`(§8.1). 순수 파일 열거·읽기라 프로세스 실행이 없다 |
| `mc_identity_lost` | (v0.2.6, 요청 단위) `keep_identity` 요청의 결과 `McResult.identity_kept`가 거짓(§6.1). 어댑터 선언과 실제 동작이 어긋남 | 코어 |
| `lut_model_provenance_missing` | LUT 슬라이스 meta 모델 기록이 빈 표. (v0.3.0 검증 지적 13) 두 경우를 `detail.why`로 가른다: `meta_absent`(npz에 `meta_json` 키가 없거나 `model_files_sha256` 칸이 없음 -- 사례 기준선 LUT, S-39), `empty`(칸은 있으나 빈 표, 또는 중첩 dict에서 선언한 kind 키의 하위 표가 빔). `detail` = `{index, path, why, kind}` | 코어 |
| `oracle_capability_unverified` | 필요한 능력 기록 없음 | 코어 |
| `oracle_capability_stale` | 능력 기록 지문 불일치 | 코어 |
| `mc_method_unsupported` | 선언되지 않은 MC 방법 | 코어 |
| `diagnostic_not_a_gate` | 진단 결과를 판정 입력으로 쓰려는 호출 | 코어(§13.3) |
| `dc_tolerance_undeclared` | 입력 `simulator.options`에도 어댑터 보정값에도 DC 풀이 허용오차(reltol·vntol·abstol) 선언이 없음(§8.3) | 코어 |
| `reference_undeclared` | V_sys 측정(PC-10, 범위 판정)에 필요한 입력 `output_reference`가 없음(§11.6, v0.3.0에 §11.1에서 옮김). offset-trim design §20.1과 같은 사유 이름. (v0.3.0) 계통 offset `offset_sys_mv`(§21.4)도 같다: 단일 출력인데 `output_reference`가 없으면 이 사유로 정의 불능(엔진 DEC-23과 같은 이름, 측정 단위 거부 -- 다른 측정은 그대로 돈다) | 코어 |
| `sweep_end_unresolved` | (v0.3.0, OP-5, 계획 N3.9·O-25 (3)) swing·ICMR 훑기에서 범위 끝이 정해지지 않음: 괄호 [마지막 통과, 첫 실패]를 목표 분해능까지 좁히지 못함(유도 상한 K_zoom 도달, 실행 시간 상한) 또는 공칭점 자체가 정의 불능. 미검증 외삽 끝으로 값을 내지 않는다(측정 단위, 그 metric = 정의 불능). (v0.3.2) `detail.why` ∈ `zoom_cap`(반복 상한·`rounds_left = 0`), `time_cap`, `nominal_shift`(swing만, §21.2 B-45), `nominal_not_conducting` | 코어 `swing_math` |
| `sweep_point_unconverged` | (v0.3.0, OP-5, 계획 N3.9 '수렴하지 않은 점') 훑기 점 하나가 수렴하지 않음 → 그 측정(그 창) **전체**를 정의 불능으로 거부한다. 창을 그 점에서 자르지 않는다(옛 '수렴 안 함 = 포화 아님' `O/oracle_swing.py:25` 삭제). `detail` = `{metric, point, error}` | 코어 `swing_math` |
| `conduction_undefined` | (v0.3.0, OP-5, §21.1; v0.3.2 정정 -- 열 입력 칸 삭제 반영) (v0.4.9 문언 정정, A-84 C-9) 판정 점에서 어떤 소자의 판정 입력 ID·VDS·VDSAT 가운데 하나라도 없음(점 기록 `region_point = "undefined"`, §21.1 1단계). 합격 판정이면 '판정 불능' → `INCOMPLETE`, 범위 판정이면 그 점 = 정의 불능 → `sweep_end_unresolved`가 아니라 이 코드로 그 측정 거부(엔진 '판정 불가 undefined'와 같음) | 코어 `conduction` |
| `sweep_direction_undeclared` | (v0.3.0, OP-5, 계획 N3.9 '여기 포트·방향은 입력 선언') swing·ICMR·계통 offset·슬루 요청인데 입력 `dc_sweep`(§11.6)이 없거나 그 측정에 필요한 성분(ICMR의 `common` 등)이 없음. 이름·포트 개수로 추측하지 않는다 | 코어 |
| `slew_undeclared` | (v0.3.0, OP-10, 계획 G-19; v0.3.2 정정 -- 계단 끝 입력 칸 삭제, O-51) 슬루 측정을 요청했는데 입력 `slew`(§11.6)의 측정 노드가 없음 | 코어 |
| `intended_region_mismatch` | (v0.4.0: `triode` 선언만 대조, `off` 대조 삭제 -- O-202) (v0.3.1, OP-5, 사용자 결정 O-53 B1·O-55 U1) 동작점(합격 판정 점·범위 측정 공칭 점)에서 선언 소자(`intended_region`)의 1단계 영역이 선언과 어긋남 = 선언 오류. 합격 판정이면 판정 불능(`INCOMPLETE`) 집계(FAIL 아님), 범위 판정이면 그 측정 정의 불능. `detail` = `[{device, declared, actual}]` | 코어 `conduction` |
| `measure_feedback_undeclared` | (v0.4.9, A-84 C-9: 더하는 card = OP-10) (v0.4.0: 슬루만 -- ICMR은 이 칸을 읽지 않음, O-115) (v0.3.1, OP-5·OP-10) ICMR·슬루 요청인데 입력 `measure_feedback`(§11.6)이 없음(측정 단위). (v0.3.6, DR-21 -- 갈래 정리) 이 코드는 **입력 칸 없음** 하나만 뜻한다(ICMR·슬루 공통). 구성이 정의되지 않는 경우는 아래 `feedback_config_undeclared`(슬루만) -- ICMR에는 그 갈래가 없다(차동 모드 DC 닫힘, §21.2 2단계). (v0.3.8; v0.3.9 둘째 커밋 문언 -- 검증 M1-a) ICMR의 단일 출력 + DC 되먹임 없는 선언(§21.2 2단계 (0) 판정) 경우는 `icmr_feedback_dc_absent`(§21.2 2단계 (e))다. (v0.3.7, 검증 nice-to-fix -- 이름 대응) 계획 DR-22 문언 '`measure_feedback_undeclared` 슬루 갈래 = 미선언 차동 출력'은 이 design에서 `feedback_config_undeclared`(`detail.why = differential_undeclared`)가 맡는다 -- 이 코드(`measure_feedback_undeclared`)는 입력 칸 없음만 뜻하므로 같은 경우에 코드가 둘 생기지 않는다 | 코어 |
| `feedback_config_undeclared` | (v0.3.1; v0.3.6 다시 씀 -- 계획 v0.6.14 DR-21·DR-22, 사용자 결정 O-67 (1)·O-68 (2)·O-69 (1), X-35) **슬루만**: (a) 차동 출력 + 되먹임 미선언(`unity_follower`) → 슬루 정의 불능(`detail.why = differential_undeclared`; 근거 = 계단을 넣을 입력 망이 없고 입력 망은 선언 몫 -- 직결 닫힘을 지어 넣지 않음, 계획 N3.9 슬루 행) (b) (v0.3.8 다시 씀, 계획 v0.6.15 DR-23 (1)·O-78 (1)) 선언 구성이 모든 입력 포트에 닿음 → 계단 자리(입력 망 원소의 다른 단자)는 gain-budget card AP-1 몫이라 OP-10에서 정의 불능(`detail.why = input_network_step_deferred`; 옛 `no_input_network` 대체 -- OP-10은 입력 망 원소를 찾지 않는다) (c) (v0.3.8, DR-23 (1); v0.4.1 M6 -- 출력 꼴 무관) DC 되먹임 없는 선언(v0.3.9 -- §21.2 2단계 (0) 판정 '없음', ICMR (c)와 같은 판정 하나; 옛 괄호 '`feedback_passives`에 `Resistor`·`Inductor` 없음'은 history v0.3.9; 1b 경로 이름표 '용량만 선언된 차동 출력'은 그대로) → t = 0 시작 동작점 경로(§21.6 1b)가 AP-1 몫이라 정의 불능(`detail.why = start_op_deferred`). (b)(c) 모두 새 코드가 아니라 기존 코드의 새 `why` 값이다(슬루 측정 구성으로 정의 불능이라는 같은 뜻). (d) (v0.4.1 M5, A-21) 입력 포트 둘 이상 + `declared` 나머지 → `detail.why = beta_undefined`. 검사 순서 (a) → (b) → (c) → (d), 모두 어떤 시뮬레이터 호출보다 먼저(입력 칸과 IR 원소 종류만 읽음). `detail.why`는 처음 걸린 갈래 하나다 -- (b)와 (c)가 함께 해당해도(사례 current_reuse) 기록은 `why = input_network_step_deferred` 하나다(v0.3.10 넷째 커밋, 사용자 결정 O-89 (2): v0.3.8 둘째 커밋의 `detail.also` 칸은 소비자 0이라 지움 -- 옛 문장 history). **ICMR 갈래는 지운다**: 차동 출력 + 미선언 또는 DC 되먹임 없는 선언((0) 판정, v0.3.9)이면 ICMR은 차동 모드 DC 닫힘(§21.2 2단계)으로 정의된다(옛 O-52 확인 1 '정의 불능' 대체, 승인 X-35) | 코어 `slew_math` |
| `closure_common_asymmetric` | (**v0.4.0 삭제 -- ICMR DC 닫힘 소멸(O-115); 슬루 시작 동작점 닫힘은 AP-1 몫, 그때 다시 정함**; 옛 행 기록) (v0.3.7, OP-5, 검증 필수 3·사용자 결정 O-78 (3) 승인(비대칭 c fail-closed); 실패 규약 = gain-budget N3.14 '공통 실패 규약'(정의 불능 + 사유 기록) 적용, 코드 이름은 이 design이 붙임 -- (v0.3.7 둘째 커밋, 검증 N2) 옛 인용 'gain-budget 576행 그 구성은 정의 불능(… code 이름은 design)'은 S-OS1 문장이라 이 경우와 무관해 뺐다) 차동 모드 DC 닫힘(§21.2 2단계 (c))이 필요한 ICMR 요청인데 `dc_sweep.common`의 두 입력 포트 계수가 같지 않음(한쪽 0 포함) → ICMR 정의 불능. 거부 시점 = **어떤 시뮬레이터 호출보다 먼저**(`.tf` 짝 식별 전 -- 두 `excite` 포트 이름으로 비교, v0.3.7 둘째 커밋 통일). `detail` = `{ports: [<excite 포트 이름 둘>]}`(넷 이름만 -- 계수 값 사본 없음, 입력 `dc_sweep.common`이 정본). 근거·계획 문언은 §21.2 2단계 (c) '공통모드 가중 조건' | 코어 `swing_math` |
| `icmr_feedback_dc_absent` | (**v0.4.0 삭제 -- DV-19 소멸(O-115, DR-26)**; 옛 행 기록) (v0.3.8, OP-5, DV-19 닫힘 -- 계획 v0.6.15 N3.9 ICMR 행·DR-23 (2), 사용자 결정 O-78 (2)·O-79·O-80 R2; 정의 = gain-budget v6.26 N3.8 'ICMR 측정 구성'의 '단일 출력 + DC 성분 없는(용량만) 선언 되먹임' 문장 하나 -- 이 문서는 인용만, 사유 이름은 이 design이 붙임; **v0.3.9 뜻 갱신** -- 계획 v0.6.16 DR-24·gain-budget v6.27 N3.8 표제 '단일 출력 + DC 되먹임 없는 선언 되먹임', '없음' = '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'의 경로 판정(§21.2 2단계 (0)), 소자 종류 판정 아님(O-81 (2)·O-82)) ICMR 요청이 §21.2 2단계 (e)에 해당 → ICMR 정의 불능(fail-closed). 입력이 하나인 회로는 이 코드가 아니다(§21.2 2단계 (d)가 먼저). 거부 시점 = 어떤 시뮬레이터 호출보다 먼저(입력 `measure_feedback`·`feedback_passives` IR 원소 종류·`dc_sweep.excite` 키 수만 읽음). `detail` = `{output: <출력 넷 이름>}`(넷 이름만 -- 원소 목록 사본 없음, 입력 `feedback_passives`가 정본). **엔진 쪽 대응 이름**: `icm_config_feedback_no_dc`(design 41 v1.12.5 `88bc5f2f` 734행 4.7-3b (1)·744행 code 목록; 경로 판정을 담을 v1.12.6은 v0.3.9 작성 때 브랜치 `design/it2c-o79` 머리 `2e60f9c7`에 아직 없음 = **미확인**; **승인 대기**) -- 같은 경우의 엔진 사유이고 이름이 다른 것은 오라클 어휘(§7)를 따른 것; 대응은 design 41 승인 뒤 확정(§19.2 알림) | 코어 `swing_math` |
| `dc_feedback_judgment_undefined` | (v0.4.9, A-84 C-9: 만드는 card = OP-10) (v0.4.0: 슬루만, 원인 둘 = `element_unsupported`·`differential_split`; `bias_not_gate_only`는 §11.2 1d로 옮겨 삭제 -- OP-B3) (v0.3.9, OP-5·OP-10, 계획 v0.6.16 N3.9 ICMR 행 'DC 되먹임 판정'·DR-24, 사용자 결정 O-82; 정의 = gain-budget v6.28 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'의 '지원 밖 원소'·'차동 출력' 규칙(v0.3.10 둘째 커밋 머리 정렬, 검증 N1 -- 옛 v6.27 '이상 전압원 = 지원 밖' 인용 대체). **범주**(검증 N2): `element_unsupported`·`differential_split` = 판정 정의 불능(gb 정의 문단의 갈래); `bias_not_gate_only` = **입력 계약 전제 위반**(판정 정의가 아니라 오라클 입력 `/bias_voltages`의 '게이트 전용' 전제가 깨짐 -- 지금은 판정을 부를 때만 검사하므로 이 code 아래 둠). 그 검사가 OP-3 입력 계약(§11.2 1d 교차 규칙)으로 옮겨 가면 같은 변경에서 이 `why` 값을 지운다(같은 검사 두 자리 금지)) §21.2 2단계 (0) 판정이 필요한 ICMR·슬루 요청인데 (v0.3.10 -- 계획 v0.6.17 DR-25 (1)(2), 사용자 결정 O-85 (1)(3); 정의 = gain-budget v6.28 N3.8 같은 문단 '지원 밖 원소'·'차동 출력' 규칙 인용) 지원 밖 원소가 있음 = 입력 `/sources`에 `kind = "voltage"`(`detail.why = element_unsupported`, `detail.sources` = 원 이름만; 옛 why 이름 `voltage_source`(v0.3.9)는 history v0.3.10), 또는 차동 출력의 두 출력 판정이 갈림(`detail.why = differential_split`, `detail.present`·`detail.absent` = 출력 넷 이름만 -- DV-21 닫힘), 또는 (v0.3.9 둘째 커밋, 검증 N2) `/bias_voltages` 넷이 게이트 전용이 아님(`detail.why = bias_not_gate_only`, `detail.nets` = 넷 이름만) → 그 측정 정의 불능(fail-closed). 거부 시점 = 어떤 시뮬레이터 호출보다 먼저. 엔진 쪽은 그 전에 S1 `s1_dc_conduction`이 `source_kind_unsupported`로 멈춘다(gain-budget v6.27 N3.8 같은 문단 인용) -- 대응표 §19.2 | 코어 `swing_math` |
| `inverting_port_undetermined` | (v0.4.0: 슬루 전용 -- DR-26, ICMR 갈래 삭제) (v0.3.1, O-53 A-1; v0.3.6 DV-17 닫힘·차동 출력 짝 -- 계획 N3.9 '전달 판정 분해능'·ICMR 행 '반전 입력 포트 식별') 반전 입력 포트 `.tf` 부호 판정 실패: 출력(차동 출력이면 출력 노드마다)에 대해 음수 후보 0개·2개 이상, 후보 전달이 전달 판정 분해능으로 판정 불능(§21.5 4단계 (4)의 같은 판정 함수), 차동 출력에서 두 출력의 반전 입력이 같은 포트, 레일 폭 0. `detail` = `{why, candidates: {<출력 식>: {<port>: A}}}`(v0.3.6: 옛 `resolution` 칸은 지움 -- 판정 문턱 δV_out/레일 폭은 입력(`Resolution`·레일 선언·공칭 `.op`)에서 다시 잴 수 있는 값이라 저장하지 않음, 새 값 칸 금지 DR-21). ICMR을 내지 않는다(v0.3.6: 옛 '같은 구성을 쓰는 슬루도 내지 않음'은 지움 -- 슬루는 선언 구성 전체, §21.6) | 코어 `swing_math` |
| `slew_step_end_undefined` | (**v0.4.0 삭제 -- `follower_range_undefined`로 대체**; 옛 행 기록) (v0.3.1, OP-10, O-51) 그 방향 계단 끝(같은 입력의 확정 ICMR 끝)이 정의 불능 → 그 방향 슬루 정의 불능. (v0.3.3) 끝은 입력 `confirmed_range.icmr`(§11.6)의 그 끝 지목으로만 받는다 -- 지목이 정의 불능이거나 `confirmed_range.icmr`가 없으면 이 코드(`detail.why` ∈ `pointer_undefined`, `no_confirmed_range`; 계획 G-19 'ICMR 끝 정의 불능이면 그 방향 슬루 정의 불능', 사용자 결정 O-58 DV-10) | 코어 `slew_math` |
| `range_pointer_rejected` | (**v0.4.0 삭제 -- 지목 왕복 소멸**; 옛 행 기록) (v0.3.3, OP-5·OP-10, 계획 G-19 네 검사·N3.9 '범위 판정' 끝 '최종 범위 metric', 사용자 결정 O-58 DV-10·O-59 (3)) 입력 `confirmed_range`(§11.6)의 끝 지목 하나가 오라클 자기 기록과 어긋남 → **거부**(§7.2 2c, 거부 기록 §11.7, 반환 코드 2; 끝 하나라도 어긋나면 실행 전체 거부 -- 부분 확정 없음, fail-closed). `detail` = `{metric: "swing" \| "icmr", end: "lo" \| "hi", record_id, point_id, check}`. `check` = 계획 G-19 검사 번호와 같은 순서: `record`((1) `<out_dir>`의 오라클 compare JSON 가운데 본문을 다시 재어 `record_id`가 같은 기록이 없음, 또는 그 기록의 `range_input_fp`(§11.7)가 이 입력과 다름, 또는 그 기록이 그 metric의 범위 결과·재훑기 결과가 아님), `stage1_pass`((2) `point_id`가 그 기록 `conduction.points[]`에 없음, 또는 공칭부터 지목 점까지 -- 원 범위 기록과 재훑기 기록의 점을 x 순서로 합친 열 -- 1단계 통과가 아닌 점이 있음), `within_stage1`((3) 지목 점의 x가 원 범위 기록 그 끝 `pass_point_id` 점의 x보다 바깥), `bracket`((4) 끝 확정 규칙 -- 계획 N3.9 '범위 판정' 417행 '끝 확정 규칙은 두 단계 전체에 같게 적용': **면제**는 지목 점 = 그 끝 원 범위 기록의 `pass_point_id`이고 그 끝 `end_cause` ∈ {`rail`, `rail_filter`, `stage1`}일 때만(1단계가 이미 확정한 끝을 2단계가 줄이지 않은 경우); 그 밖에는 원 범위 기록과 재훑기 기록의 점을 x 순서로 합친 열에서 지목 점의 바깥 이웃 점과의 측정 좌표 m 차 ≤ r(r = 두 점의 m으로 §18.3 식을 다시 잼, §21.2 '끝 풀이' -- 저장값 없음)이어야 하고, 아니면 이 검사 실패). 새 상수 없음. (v0.3.4, DV-16 닫힘 -- 계획 G-19 '정의 불능 끝에는 검사 (1)을 그대로, (2)~(4)는 점 지목 끝에만', 사용자 결정 O-62 (2)) **정의 불능 끝**(`{undefined: true, record_id}`, §11.6)에는 `record` 검사만 한다 -- 기준은 점 지목 끝과 같다(그 `record_id`의 기록이 `<out_dir>`에 있고 `range_input_fp`가 같고 그 metric의 범위 결과 또는 같은 끝의 재훑기 결과임); `stage1_pass`·`within_stage1`·`bracket`은 점 지목 끝에만. 정의 불능 끝의 `detail` = `{metric, end, record_id, point_id: null, check: "record"}`. (v0.3.5, 검증 M2) 검사 (1)의 '기록'은 compare JSON과 그 `sim_ref`(§11.7)가 가리키는 같은 줄기 `.sim.json`이다 -- sim.json이 없거나 정규 JSON sha256이 `sim_ref.sha256`과 다르면 `record`(범위 끝 기록 `sim.swing_icmr`는 sim.json에 있음). 어느 검사도 사유를 읽지 않는다(지목에 사유 칸이 없음 -- 사유는 엔진 `stage2_judgment`에만, gain-budget N6.20 '2단계 판정 기록') | 코어 `range_confirm` |
| `input_dc_undeclared` | (v0.3.3, OP-5, 계획 N3.9 `offset_sys_mv` 행 = gain-budget DEC-23 '이동의 기준점', 사용자 결정 O-59 (4) DV-13) 계통 offset(PC-10 포함) 요청인데 `dc_sweep.input_dc`(§11.6 선언 입력 DC)가 없음 → 그 측정만 정의 불능(기준점 V_id,0을 정할 수 없음; free servo 해로 대신하지 않음 -- DEC-23 'SPICE 해(free servo 해)는 기준점이 아니다') | 코어 `measures_dc` |
| `a_dc_undefined` | (v0.3.4, OP-5, DV-14 닫힘 -- 계획 N3.9 σ 행·`offset_sys_mv` 행 (i)~(iv), gain-budget v6.23 DEC-23 'A_dc 정의 불능 갈래', 사용자 결정 O-61 P7·O-62 (3)·O-63 (2)) A_dc로 나누는 측정(σ 입력 환산 `offset_mc`, 계통 offset `offset_sys_mv`, PC-10)이 읽는 `.tf` A 한 측정(§21.5 `sim.a_dc` 기록)이 정의 불능 → 그 측정만 정의 불능(`unavailable`, fail-closed). `detail` = `{a_dc_ref: "/a_dc"}`(v0.3.5, 검증 N1: 같은 `.sim.json` 안 JSON 포인터 -- 원인(`sim.a_dc.reason` ∈ `nominal_unconverged`, `tf_failed`, `a_dc_below_resolution`; `sweep_direction_undeclared`는 소비 측정이 먼저 자기 사유로 냄, §21.4 4단계)은 그 기록에만 있고 여기에 사본을 두지 않음). `.dc` 출력 고정 풀이의 수렴 실패는 이 코드가 아니라 `sim_convergence_failed`(§21.4 4단계) -- 사유 셋(갈래·`.tf` 실패·`.dc` 수렴 실패)이 서로 다른 자리에서 나뉜다 | 코어 `measures_dc` |
| `icmr_input_ports_unsupported` | (v0.4.0, OP-5) 입력 포트 셋 이상 -- ICMR 정의 불능(상위 N3.8), 시뮬레이터 호출 0 | 코어 |
| `icmr_sense_target_undeclared` | (v0.4.0, OP-5, DR-26) 출력 넷의 `/predictions/nodes` 봉인점 예측값 없음 -- servo 목표 s0를 정할 수 없음 | 코어 |
| `icmr_servo_sign_undefined` | (v0.4.0, OP-5, DR-26) `sim.a_dc.status = "undefined"`라 servo 부호를 정할 수 없음. `detail = {a_dc_ref: "/a_dc"}`(사본 없음) | 코어 |
| `icmr_output_lock_violated` | (v0.4.0, OP-5, U-103) 훑기 점의 감지 고정 오차 > δV_out. 그 metric 전체 정의 불능, 창을 자르지 않음. `detail = {point_id, error_V, delta_V}` | 코어 |
| `kcl_zero_set_mismatch` | (v0.4.0, OP-5, O-182 Q-S9 (A′)) 연결에서 유도한 KCL 항등 0 전류 MOS 집합 ≠ 입력 `/kcl_zero_current_devices`. 거부, 시뮬레이터 호출 0. `detail = {only_in_ir, only_in_input}` | 코어 |
| `offset_reference_unreachable` | (v0.4.0, OP-5, DR-28, U-107) V_ref가 같은 측정 구성 출력 범위 밖 -- `sim.offset_sys.reason`, `.dc` 요청 안 함 | 코어 |
| `output_range_undefined` | (v0.4.0, OP-5, DR-28) swing 정의 불능이라 도달 여부를 못 정함 -- `sim.offset_sys.reason` | 코어 |
| `follower_range_undefined` | (v0.4.0, OP-10, DR-27) `follower_input_range_v` 정의 불능 -- 슬루 정의 불능(옛 `slew_step_end_undefined` 대체) | 코어 |
| `slew_step_out_of_range` | (v0.4.0, OP-10) 선언 step ⊄ follower 사용 범위 -- 과도 측정 유효성 위반, 정의 불능 | 코어 |
| `nyquist_unresolved` | (v0.4.0, OP-4, OP-B1) 세분 상한 안에 '각 구간 편각 < π/2' 또는 '구간 폭 ≤ 주파수 분해능'을 못 맞춤 -- N 미정 | 코어 |
| `noise_tail_bound_undefined` | (v0.4.0, OP-5, OP-B1, §18.3) PSD 점근 기울기 가정이 성립하지 않거나 검사 불능 -- noise 적분 정의 불능 | 코어 |
| `noise_grid_unresolved` | (v0.4.0, OP-5, OP-B1) |I_k − I_(k−1)| > reltol·I_k인 채 유도 상한 도달(§18.3) | 코어 |
| `slew_required_undeclared` | (v0.4.1, OP-10, M4) 그 방향 SR 제약 없음 -- 끝 시각을 정할 수 없어 그 방향 정의 불능, 시뮬레이터 호출 0 | 코어 |
| `bin_rule_undeclared` | (v0.4.0, OP-7, §16) 입력 LUT의 모델 묶음·시뮬레이터 판에 묶인 bin 선언 없음. 실행 거부. (v0.4.9) `detail.why` ∈ {`no_decl_ref`, `decl_invalid`, `model_set`, `simulator`} | 코어 |
| `bin_rule_compat_mismatch` | (v0.4.0, OP-7, §16) 어댑터 실행 호환 모드 ≠ 선언 호환 모드, 또는 `.spiceinit` 내용 sha256 다름, (v0.4.9) 또는 실행 로그가 보인 모드 ≠ 선언 모드(못 읽으면 `actual = null`). `detail = {declared, actual}` | 코어·어댑터 |
| (규칙 이름 -- 코드 아님) | (v0.3.2, B-46 정정) `intended_region_unknown_device`·`measure_feedback_port`·(v0.4.0 삭제) `sweep_rezoom_bounds`는 `oracle_input_schema_invalid`의 `detail[].rule` 값이다(§11.2 1d, §11.6 교차 규칙 열) -- 별도 오류 코드가 아니다 | 코어 `input_check` |
| `power_undefined` | (v0.3.0, OP-11, 계획 OP-11 행) `power_dc_w`를 낼 수 없음: 기준 아닌 레일 하나라도 전류가 없음(부분 합 금지), 또는 결과가 막힘(`skipped`). `detail.why` ∈ `rail_current_missing`, `blocked`. 기준 레일 전압 ≠ 0인 입력은 여기까지 오지 않는다 -- OP-3 입력 검사(§11.2 1d 규칙 `reference_rail_voltage`)가 거부한다 | 코어 `measures_dc` |
| `descriptor_geometry_undeclared` | (v0.2.4, O-6 D-b) 쓰려는 kind의 기하 단위 또는 병렬 배수 전달 규칙이 기술자에 없음. 공칭 포함 모든 해석에서 낸다(§10.6). `detail` = `{kind, missing: ["geometry_unit" \| "parallel_multiplier", …]}` | 코어 |
| `mc_distribution_inline` | (v0.2.4, O-6 D-a) 기술자 `mc.distribution`에 분포 값이 직접 적혀 있음. (v0.2.5) 판정은 이름 추측이 아니라 **닫힌 키 집합**으로 한다(§10.4): `distribution`의 키 ⊄ {`source`, `locate`}, `locate`의 키 ⊄ {`pattern`, `fields`}, 또는 `fields`의 값이 패턴 그룹 이름(문자열)이 아님(숫자 등). `detail` = 어긴 JSON 포인터 | 코어 |
| `mc_distribution_unlocated` | (v0.2.4, O-6 D-a) 기술자가 분포 값 위치를 선언하지 않았거나, 선언한 위치 식이 원본에서 0개를 찾음(P NFR-P6) | 코어 |

* 가리킨 PDK 원본의 sha256이 맞지 않는 경우는 새 코드를 두지 않고 `pdk_descriptor_stale`로 낸다(완료 조건 4 분포 값 출처 깨진 변형 셋째 = 이 코드).
* (v0.2.5, 검증 경미 지적 '기존 코드 중복') v0.2.4의 `geometry_unit_unsupported`는 지웠다. 그 두 경우는 '어댑터 능력 없음'과 '보정값 없음'이고, 이미 `adapter_capability_missing`·`adapter_calibration_missing`이 같은 사실을 낸다. 한 사실에 코드 둘을 두지 않는다(v0.2.4 `pdk_descriptor_stale` 재사용과 같은 원칙).

### 7.1 시뮬레이터 로그 → 오류 코드 대응표(초안, 사례 ngspice)

* 규칙(어댑터 공통): 대응은 **로그 문장 형태**(줄 머리의 심각도 표지 + 문구)로 한다. 시뮬레이터가 다시 찍는 회로 제목 줄과 사용자 이름(넷·소자 이름)이 들어가는 부분은 대응에서 뺀다. 옛 부분 문자열 정규식이 제목 줄 `… tsingular …`에 걸린 사례(S-18) 때문이다.
* 아래는 OP-1 기준선 로그(S-18) 25묶음에서 뽑은 **초안**이다. ngspice 어댑터 `errors.py`의 사례 표가 되고, 확정은 OP-3(op·ac 실행)·OP-4(pz·과도) 구현 때 같은 기준선 로그로 다시 대조한다. 방언 문구는 사례이므로 규칙 칸에 넣지 않는다.

| 로그 문장 형태(사례, `#` = 숫자) | 기준선 건수 | 옛 정규식 / pz 정규식 | 초안 코드 | 비고 |
|---|---|---|---|---|
| `Warning: Pole-zero iteration limit reached; giving up after # trials` | 43 | 아니오 / 예 | `sim_convergence_failed`(**요청 단위**) | (v0.2.5) 그 `Pz` 요청의 `Poles(status = 'failed', error = sim_convergence_failed)`로만 낸다. 벤치 `RunStatus.error`는 바꾸지 않는다(같은 벤치의 op 등 다른 요청은 그대로 쓴다). 지금도 pz는 자기 넷리스트를 따로 돌고 실패는 `pz.status = 'failed'`·`P = None`이다(`O/oracle_simulate.py:777-812`) |
| `Warning: singular matrix: check node …` | 6 | 예 / 예 | `sim_singular_matrix`(그 요청 결과가 없을 때만) | (v0.2.5) S-30 로그처럼 회복 시도 중에 찍힌 뒤 결과가 나온 경우는 아래 '회복된 경고' 규칙으로 정보만 |
| `Warning: Dynamic gmin stepping failed`, `Warning: True gmin stepping failed`, `Warning: source stepping failed` | 각 1 | 아니오 / 아니오 | (v0.2.5 고침) **회복 시도 경고**: 결과가 없을 때만 `sim_convergence_failed`, 결과가 있으면 정보 | 셋 모두 S-30의 한 로그에 있고 그 로그는 동작점이 회복됐다(`Transient op finished successfully`). v0.2.4 초안은 셋을 무조건 `sim_convergence_failed`로 두어 회복된 실행을 실패로 만들었다 |
| `Error: Could not find include file …` | 2 | 예 / 아니오 | `sim_model_not_found` | |
| `ERROR: fatal error in ngspice, exit(#)` | 2 | 예 / 아니오 | `sim_failed_other` | 앞 줄의 구체 코드가 있으면 그것을 우선한다 |
| `Error: no such device or model name …` | 8 | 예 / 아니오 | `sim_failed_other` | 내부 벡터 이름 대응 실패(어댑터 결함)로 드러남 |
| `Error: no such parameter …` | 1 | 예 / 아니오 | `sim_failed_other` | |
| `Warning from checkvalid: vector … is not available …` | 9 | 아니오 / 아니오 | 코드 없음(정보) | 그 op 파라미터는 `None`이 되고(§6) PC-1이 판정한다 |
| `Note: Starting … stepping`, `Note: Dynamic gmin stepping completed`, `Warning: Source/Drain conductance reset to # mho.` | 2·1·1·1·2952·2952 | 아니오 / 아니오 | 코드 없음(정보) | 실패 아님 |
| 회로 제목 줄 `Circuit: * …` | 12 | 예(거짓 적중) / 아니오 | 대응 대상 아님 | 위 규칙 |
| (기준선에 없음) 시간 걸음 실패 문장 | 0 | -- | `sim_timestep_too_small` | (v0.2.5) 기준선 증거 없음(S-30). 문장 형태는 (v0.4.8, A-80) 매뉴얼에 그 문장이 없어 OP-4 실측 로그에서 옮기고, 대응은 **주입 로그 test**로만 보인다(§18.1 '오류 대응' 행). 기준선 증거가 생기기 전까지 이 행은 '주입 증거' 단계로 표시한다(계획 X-23과 같은 단계 표시 방식을 오류 대응표에 쓰는 것은 이 문서의 기본안 B-24다. 계획 X-23은 방언 토큰 목록에만 정했다) |
| (로그 문장 아님) 실행 시간 상한 초과 | 0 | -- | `sim_timeout` | (v0.2.5) 로그가 아니라 어댑터 실행 계층(프로세스 시간 상한)에서 낸다. `RunStatus(rc = None, timed_out = True, error = sim_timeout)`. 기준선에 사례가 없으므로 시간 상한을 아주 작게 준 실행 또는 시간 초과 예외 주입 test로 보인다 |

* **회복된 경고 규칙**(v0.2.5, 어댑터 공통, 이름 없는 규칙): 시뮬레이터가 실패 뒤 다른 방법으로 다시 시도하며 찍는 경고(회복 시도 경고)는 **그 요청의 결과가 정상으로 읽히면** 오류 코드로 내지 않고 `RunStatus.warnings`에 문장 그대로 싣는다(정보, 판정에 쓰지 않음). 결과가 없거나 읽을 수 없을 때만 그 경고가 가리키는 코드를 낸다. '회복 시도 경고'인지는 어댑터 대응표의 행 표시이고(사례: 위 stepping 셋, 회복 과정의 singular matrix), 회복 여부는 경고 다음 줄의 문장이 아니라 **결과 존재**로 정한다(문장 형태는 시뮬레이터마다 다르므로). 옛 정규식(`error|fatal|singular|abort`, S-18)은 결과 존재와 무관하게 `log_errors`에 모았다.
* **오류 단위**(v0.2.5): 벤치 단위(`RunStatus.error`) = 프로세스가 결과를 하나도 내지 못한 경우(모델·include 없음, 치명 오류, 시간 초과). 요청 단위(각 결과 `.error`) = 그 해석만 실패한 경우(pz 반복 한도, 그 요청 결과 없음). 같은 벤치의 다른 요청 결과는 요청 단위 오류의 영향을 받지 않는다.
* 열린 점(OP-3 몫, 계획과 다르지 않음): 'op 파라미터 이름 없음'과 '소자·모델 이름 없음'을 `sim_failed_other`에서 나눌지. 지금 초안은 나누지 않는다.
* 대응표 확정 test의 입력 로그(기준선 로그 발췌)는 OP-1a 보관 목록의 소비처다(계획 OP-1a '목록은 이 card가 소비처로 고정'). 이 문서가 그 소비처를 적고, 목록 확정은 OP-1a가 한다.

### 7.2 실행 전 검사 순서(v0.2.5, 검증 M-2)

코어는 벤치를 어댑터에 넘기기 전에 아래 순서로 검사하고 **처음 걸린 하나**만 낸다. 순서는 '데이터(기술자) 결함 → 그 요청이 쓰는 기술자 방법 → 어댑터 능력 → 보정값 → 판정 게이트 → 모델 묶음' 이다. 이유: 앞 단계가 틀리면 뒤 단계 검사의 입력이 정의되지 않는다(예: 기하 규칙 없는 기술자로는 어떤 소자 줄도 쓸 수 없으므로 MC 방법이나 어댑터 MC 능력을 볼 의미가 없다).

| 순 | 검사 | 코드 |
|---|---|---|
| 1 | 입력 형식(v0.3.0: §11.2 1a~1d 순서 -- JSON 읽기 → 옛 형식 표지 → JSON Schema → 교차 칸 규칙 → 어댑터 이름·실행 파일), (v0.2.6) 어댑터 선택과 어댑터 지문 계산 | `oracle_input_schema_invalid`, `oracle_input_format_old`, `adapter_unknown`, `simulator_exe_missing`, `adapter_fingerprint_unavailable` |
| 2 | 기술자 읽기(입력 `process.descriptor` sha256 → 스키마 → 참조 sha256 → 원본 중복 → 참조 파일 형식 → kind 대응). (v0.2.6) **기술자가 가리키는 모든 파일**(엔진 선언, 기술자가 쓰는 엔진 `sources` 키의 원본 -- include·`mc.distribution.source`·`mc.enable.source` 등 쓰는 곳과 무관하게 --, `extra_sources`, `lut_record_root`의 위치 선언 파일, `lut_file_roles` 옆 선언, (v0.4.9) `bin_rule_decl` 선언 파일)의 sha256을 이 단계에서 한 번에 대조한다. 옆 선언의 형식·`evidence` 일관과 위치 선언 파일 형식도 여기서 본다. (v0.3.0, DR-5) 대조 정의: 기술자 칸·입력 `process.descriptor` = LF 정규화 값만(규칙 (i)), 엔진 원본 raw 기록 = 규칙 (ii)(LF 또는 raw, raw만이면 `machine_dependent_refs`), 중복 = 규칙 (iii)(파일 바이트 재측정 LF 값끼리). `devices[].kind` ⊆ 기술자 `kinds`도 여기서 본다 | `pdk_descriptor_stale`, `descriptor_schema_invalid`, `descriptor_source_duplicated`, `lut_file_roles_invalid`, `lut_location_decl_invalid`, `descriptor_kind_undeclared` |
| 2b | (v0.3.0) LUT 파일 읽기(§11.2 2b): `process.lut_files[i]`마다 raw sha256(규칙 (iv)) → meta 모양·kind 키(§11.1) → 코너·온도 기록 일치 → 조건 확정(§11.2) | `lut_file_stale`, `lut_meta_shape_mismatch`, `lut_condition_conflict`, `oracle_condition_missing` |
| 2c | (**v0.4.0 삭제** -- `confirmed_range`·네 검사는 지목 왕복과 함께 없어짐, OP-5 착수 조건 = 사용자 확인; 옛 행 history v0.4.0) | -- |
| 3 | 벤치가 쓰는 kind의 기하 선언(모든 해석 공통, §10.6) | `descriptor_geometry_undeclared` |
| 4 | 요청이 쓰는 기술자 방법(MC·진단 요청만): `mc` 칸 유무·`method`·`enable.how` → 분포 값 출처(값 직접 기재 → 위치 식이 0개를 찾음) | `mc_method_unsupported`, `mc_distribution_inline`, `mc_distribution_unlocated` |
| 5 | 어댑터 능력(요청 종류, 기하 단위 적용 방법, MC 켜는 법 종류와 코어 고정 요구 ⊆ 어댑터 선언(§10.4), 요청 시드 적용(§6.1)) | `adapter_capability_missing`, `mc_method_unsupported`(켜는 법 종류·요구 불충족) |
| 6 | 보정값·허용오차 | `adapter_calibration_missing`, `dc_tolerance_undeclared`, `reference_undeclared` |
| 7 | 판정 게이트(MC·온도, §12.6) | `oracle_capability_unverified`, `oracle_capability_stale` |
| 8 | 모델 묶음 비교(§12.5): LUT 기록 빈 표 → (v0.2.6) 기록 뿌리 교차 검사(v0.3.0: 짝 찾기 → 짝마다 파일 LF 재측정 → 짝 0개 거부, §7 `lut_record_root_mismatch`) → 역할 적용 → 규칙 (i)(ii) → (iii) | `lut_model_provenance_missing`, `lut_record_root_mismatch`, `model_bundle_mismatch`, `lut_aux_input_mismatch` |
| 8b | (v0.4.0, OP-7, §16) bin 선언 찾기(모델 묶음·시뮬레이터 판) → 어댑터 호환 모드 대조. `oracle_run`의 모든 실행이 대상(입력이 LUT를 참조하므로). 생성기·옆 선언 측정·능력 확인 MC 실행은 `oracle_run`을 지나지 않아 대상 밖 | `bin_rule_undeclared`, `bin_rule_compat_mismatch` |
| 9 | IR 이름(어댑터 `case_insensitive_names`) | `ir_name_collision` |
| 9b | (v0.4.0, OP-5) KCL 항등 0 전류 MOS 집합 대조(§21.1 2단계) | `kcl_zero_set_mismatch` |
| 10 | (v0.3.0 검증 지적 8) **막힘 검사**(거부가 아님, §11.2 '막힘'): 기준 레일 개수 ≠ 1, C27 여기 가중, C14 되먹임 절단, CM 루프 구동자, 확산 기하 없음(C22), LUT 코너·온도 없음 등 옛 의미 검사. 걸려도 거부 기록을 쓰지 않고 그 벤치를 실행하지 않은 채 판정 `BLOCKED` + `blockers` 문장으로 compare 산출물을 쓴다(반환 2) | 코드 없음(`BLOCKED`) |

* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.2.6, 검증 중간 지적 5) **`pdk_descriptor_stale` 중복 정리**: v0.2.5는 2단계(참조 sha256)와 4단계(분포 값 원본 sha256)에 같은 코드를 두었다. 같은 파일이 두 단계에서 대조되면 어느 단계에서 걸렸는지가 요청 종류(MC인가)에 따라 달라진다. v0.2.6은 sha256 대조를 2단계 하나로 모았다: 기술자가 가리키는 파일은 요청과 무관하게 모두 2단계에서 대조한다. 그래서 4단계에는 sha256 대조가 없고, 완료 조건 4의 '분포 값 원본 sha256 불일치' 변형은 MC가 아닌 공칭 요청에서도 2단계 `pdk_descriptor_stale`로 걸린다(§18.1 4행의 그 변형은 요청 종류를 가리지 않는다).
* (v0.2.6, 검증 중간 지적 5) **`lut_record_root` 교차 검사의 단계와 코드**: v0.2.5 §10.2는 이 검사를 `descriptor_schema_invalid`로 냈지만 형식 위반이 아니다. 교차 검사는 LUT 기록(대조 대상)이 있어야 하므로 2단계가 아니라 8단계 첫머리이고, 코드는 값 불일치 `lut_record_root_mismatch`다(§7). 2단계는 위치 선언 파일 자체의 sha256과 형식만 본다.

* 4번과 5번에 `mc_method_unsupported`가 둘 다 있다. 4번은 **기술자 쪽** 미선언(`mc` 칸 없음, 선언 밖 `method`·`how`), 5번은 기술자 선언은 있으나 **어댑터가 그 켜는 법을 지원하지 않거나 코어 고정 요구를 선언하지 않음**이다. `detail`에 `side: "descriptor" | "adapter"`를 적어 둘을 가른다(어댑터에 MC 능력 자체가 없으면 `adapter_capability_missing`).
* OP-3 병합 조건 (a) test는 이 순서를 **양성 대조**와 함께 보인다(§18.1 'OP-3 병합 (a)' 행).

---

## 8. 어댑터 계약·능력·보정(G-3, G-13)

### 8.1 계약(`core/adapter_api.py`)

```
class Adapter(Protocol):
    name: str
    def capabilities(self) -> Capabilities
    def calibration(self) -> Calibration
    def fingerprint(self) -> AdapterFingerprint              # 이름, 코드 지문, 실행 파일 sha256, 시뮬레이터 판
    def run(self, circuit: Circuit, requests: tuple[Request], descriptor: Descriptor,
            work_dir: str, timeout_s: float|None, cache_dir: str|None, compat: CompatDecl|None) -> ResultBundle   # compat = §16 선언 compat(v0.4.1 M9), None = 선언 쓰지 않는 도구 실행
    def model_bundle(self, circuit: Circuit, descriptor: Descriptor, cond: Condition) -> {path: {"lf": sha256, "raw": sha256}}   # §12.5
```

* (v0.3.0, DR-10d, 계획 N3.5 'sha256 정의') `model_bundle`은 묶음 파일마다 **LF 정규화 값과 raw 값 둘**을 낸다. LUT 기록(raw 정의)을 규칙 (ii)로 대조하려면 둘이 다 필요하다. 묶음 파일끼리의 동일성·캐시 키·결과에 적는 묶음 지문은 `lf` 값 하나로 낸다(계획 N3.5 '묶음 지문은 정규화 값 하나'). 파일을 읽지 못하면 그 kind의 묶음을 만들지 않고 `sim_model_not_found`(§7)로 낸다.

* (v0.4.9, A-84 B-3, §16) `run`은 `compat`과 무관하게 실행 폴더 설정 파일을 언제나 쓴다. 글 = `compat`의 글, `compat is None`이면 빈 글. 캐시 키 다섯째 칸 = 쓴 글의 sha256(§9). `None`이면 §7.2 8b와 실행 뒤 모드 대조를 하지 않는다.

### 8.2 실행 계약

* `run`은 벤치 하나를 순차로 실행한다. 어댑터가 프로세스를 병렬로 띄우지 않는다(P NFR-P7).
* 실행 파일 경로는 입력 `simulator.exe`나 CLI `--sim-exe`로만 받는다. 코드에 경로를 두지 않는다.
* 어댑터는 판정하지 않는다. 판정에 필요한 분해능은 `Resolution`으로 넘긴다.

### 8.3 능력·보정 스키마(어댑터 패키지 안 `calibration.json`과 `capabilities()`)

```
Capabilities = {
  "op": bool, "ac": bool, "noise": bool, "noise_device_contrib": bool, "tran": bool,
  "tran_early_stop": bool, "pz": bool, "op_sweep": bool, "temperature": bool,
  "tf": bool,                              # (v0.3.0) DC 소신호 전달 함수(§5 Tf, §21.5)
  "tran_large_signal": bool,               # (v0.3.0) MOS 비선형 과도 해(슬루 §21.6). stub은 거짓
  "tran_ic_bias_only": bool,               # (v0.3.6, DR-22) 바이어스 해에서만 노드를 묶고 t > 0에 푸는 초기 조건(ngspice = uic 없는 .ic). stub은 거짓. (v0.3.7) C10 과도 벤치의 .ic도 같은 Tran.ic 칸·이 능력 하나(§4.2 stab_benches 행). (v0.3.8, DR-23 (1); 둘째 커밋 M1 정정) 소유 = OP-4(만들고 배선), 소비자 = C10 하나(§21.6 1b는 AP-1 몫)
  "mc_native": bool, "mc_keep_identity": bool, "mc_diagnostic": bool,
  "mc_enable_kinds": {"<켜는 법 종류>": {"per_instance_independent": bool, "samples_per_run": int|"many",
                                          "seed": "per_run_seed"|"none", "keep_identity_across_conditions": bool}},
                                          # P N3.3 '지원하는 켜는 법 종류', 표본 시드·정체 보존·소자별 독립(§10.4)
  "mc_distributions": [str],               # 분포 함수로 옮길 수 있는 분포 종류(예: "gauss")
  "geometry_unit_application": [str],      # 비 SI 기하 단위를 적용하는 방법(예: "global_directive", "instance_numbers")
  "instance_geometry_readback": bool,      # 시뮬레이터가 보고한 인스턴스 L·W·배수를 읽을 수 있음(§6, 완료 조건 4a)
  "case_insensitive_names": bool, "model_families": [str]
}
Calibration = {   # 모든 값은 출처 칸 필수
  "default_tolerances": {"reltol": {value, source}, "vntol": {...}, "abstol": {...}},
  "data_digits": {value, source},
  "wall_s_per_window": {value, safety_factor, measured_*..., source},   # 옛 oracle_config.json 그대로 이전
  "simulator_version_probe": {how, source},
  "global_geometry_directive": {"affects": [<IR 칸 경로>], "power": {<IR 칸 경로>: int}, "source": ...}
                                   # geometry_unit_application에 "global_directive"가 있을 때만 필수(§10.6)
}
```

* `mc_enable_kinds`의 값은 그 시뮬레이터의 RNG 성질이다(시드 지정, 실행당 표본 수, 표본 정체 보존, 소자별로 새로 뽑는지). 사례(ngspice, S-12): 켜는 법 `param_redefine`은 소자별 독립, 실행당 표본 1, 실행마다 시드, 조건(온도) 사이 정체 보존이다. 이 값은 OP-1 측정(S-12)을 출처로 OP-5에서 어댑터에 적고, PC-3·PC-6이 조합마다 다시 잰다. (v0.2.5, 계획 X-20·OQ-3 승인) 표본 수·시드 전달과 표본 성질(소자별 독립, 조건 사이 정체 보존)은 **어댑터 능력 선언만**이 담는다. 기술자에는 이 칸들이 없고, 판정이 요구하는 성질은 코어에 고정한다(§10.4).
* `global_geometry_directive.affects`는 그 시뮬레이터에서 전역 기하 단위 지시가 **다시 해석하는 IR 칸의 전체 목록**이고 `power`는 칸마다 단위의 거듭제곱(길이 1, 면적 2)이다. 출처는 시뮬레이터 매뉴얼 쪽 번호(R6)다. 목록 밖의 칸(이상 R·C·L 값, 전원 값 등)은 지시의 영향을 받지 않는다고 선언하는 것이 된다. 판정은 §10.6의 N4 동일성이 한다.

* **보정값과 어댑터 지문**(v0.2.6, 계획 v0.6.6 N3.5 '어댑터 코드 지문의 범위'): 위 `Calibration` 키 다섯 가운데 `wall_s_per_window`만 지문 밖이고(제외 목록, §0 '어댑터 지문'), 나머지 넷은 지문 안이다. 구현은 **제외 목록 방식**이다: 지문 함수는 `calibration.json`을 정규 JSON으로 읽어 제외 목록의 키를 지운 뒤 sha256을 낸다. 포함 목록을 두지 않으므로 새 키는 따로 판정하지 않아도 지문에 들어간다(계획 '모르면 넣는다'). 제외 목록에 키를 더하는 것은 그 키가 판정·소자 줄에 닿지 않는다는 근거(P-1)를 적는 변경이고 이 문서 개정 대상이다. 부수 영향(계획): 이 넷을 바꾸면 능력 기록 id(D-6 `verified_by`), OP-8 LUT 메타의 생성 어댑터 지문, 실행 캐시 키(§9)가 모두 바뀌고, `wall_s_per_window`만 바꾸면 바뀌지 않는다.
* ngspice 어댑터의 보정값은 지금 코드 값을 그대로 옮긴다. 출처 칸도 함께 옮긴다. 출처가 없던 값의 처리는 §14에서 정한다.
* **DC 풀이 허용오차(T-39)**: 쓰는 값의 순서는 (1) 입력 `simulator.options`의 선언값, (2) 어댑터 `default_tolerances` 선언값(출처 필수: 시뮬레이터 문서 쪽 번호 또는 측정 조건)이다. 둘 다 없거나, (2)에 출처가 없으면 실행하지 않고 `dc_tolerance_undeclared`로 멈춘다. 시뮬레이터 내부 기본값을 선언 없이 쓰지 않는다(숨은 상수 금지). 그래서 지금 `_NGSPICE_DEFAULT_TOL`(S-8)은 출처(R6 매뉴얼 쪽)가 채워져야 어댑터 선언값으로 쓸 수 있다. 채워지기 전에는 입력 `simulator.options`에 값이 있어야 한다(§14). 매뉴얼 원문 보관과 쪽 번호 채움은 **OP-2 병합 조건**이다(X-D4, v0.2.2). (v0.2.5, S-28) 옛 상수에는 reltol·vntol만 있고 **abstol 값은 옛 코드 어디에도 없다**. 그래서 `default_tolerances.abstol`은 옮길 옛 값이 없고, 값과 출처를 같은 R6 원문에서 처음 적는다(같은 OP-2 병합 조건). 그 전에는 abstol이 필요한 측정(아래 표 '전류')은 입력 `simulator.options.abstol`이 있어야 돈다. 옛 코드는 전류 칸 분해능에 abstol을 쓰지 않았으므로, N4 전류 칸 분해능(§18.3)의 abstol은 비교 실행 입력의 `simulator.options`(검증자 변환, §11.5)에서 온다.
* **필요한 키 집합은 양 종류마다 다르다**(N-2). 어느 측정이 어떤 키를 요구하는지 정해 두고, 그 측정에 필요한 키만 검사한다. 쓰지 않는 키가 없다고 멈추지 않는다.

  | 양 종류 | 필요한 허용오차 키 | 쓰는 곳 |
  |---|---|---|
  | 노드 전압과 그 차·비(V_os, V_sys, 스윙 경계, 노드 전압 비교) | reltol, vntol | §13.4 전파, §18.3 |
  | 전류(ID, 레일 전류, 전력) | reltol, abstol | §18.3 |
  | 파생 측정(dB·위상·교차 주파수·PM) | 원천 양의 키 + 데이터 자릿수(`data_digits`) | 옛 `data_rel_resolution`·`mp_resolution` |
  | 과도 창 판정(n_pp, floor') | reltol, vntol | C10 계약 §1(a)·(b) |

  `dc_tolerance_undeclared`는 요청된 측정에 필요한 키 가운데 하나라도 (1)·(2) 어디에도 없을 때 낸다.
* 이 허용오차는 시뮬레이터 성질이지 PDK 성질이 아니므로 오라클 기술자에는 두지 않는다(§10, 계획 N0 값 원칙, 처음 반영 v0.5.1 N0).
* `wall_s_per_window`가 없는 어댑터에서 C10 과도를 요청하면, 사용자 `--timeout-s`가 있을 때만 실행하고 없으면 `adapter_calibration_missing`이다(P N3.3).

* (v0.4.0) **새 능력·보정 칸**: `sweep_points_per_round`(능력, integer ≥ 1 -- 끝 좁히기 라운드당 점 수, 옛 `ZOOM_POINTS` 대체, 비용 선택), `servo_gain`(`calibration.json` 보정값, 출처 칸 필수 -- §21.2, OP-5), `compat_modes`(능력, 어댑터가 실행 설정으로 고정할 수 있는 호환 모드 이름과 그 설정 파일 내용 작성법, §16, OP-7), `nyquist_max_subdivisions`는 두지 않는다(§18.3 유도). (v0.4.9, A-84 C-7·C-10·B-1) `sweep_points_per_round` 값 = 옛 `ZOOM_POINTS`, `noise_points_per_decade_max`(능력, decade당 -- 적분 대역과 무관하게 뜻이 같다) 값 = 옛 입력 점 수 × 옛 격자 배수 상한, 둘 다 출처 칸 = 옛 코드 줄·기준선 기록. `print_digits_full`(보정값, §5). `compat_modes` = {모드 이름: {`spiceinit_text`, `log_line`}}.

### 8.4 C10 조기 종결(D-1, G-13)

| 어댑터 능력 | 실행 | 판정 |
|---|---|---|
| `tran_early_stop` 참 | 어댑터가 `EarlyStopRule`을 방언으로 옮겨 시뮬레이터 안에서 창 단위로 멈춘다 | 코어가 결과 시간열로 같은 기준을 다시 검증(지금 `transient_decision`과 같다) |
| 거짓 | **후보 둘(G-13, 확정은 OP-4)**: (가) tstop까지 전체 창을 한 번 실행하고 코어가 사후 판정 / (나) 창 j마다 tstop = t_end + j·W로 처음부터 다시 실행 | 코어가 같은 기준 적용 |

* 어느 쪽을 기본으로 할지는 OP-1 기준선의 창당 시간으로 비용을 재고 **OP-4가 정한다**(P OP-0 목록 'G-13 후보·측정 방법, 확정은 OP-4'). 이 문서는 후보 둘과 측정 방법만 정하고 고르지 않는다.
* **측정 방법**(OP-1에서 이 방법으로 잼, S-19): 기준선의 폐루프 과도 실행마다 창 하나 비용 c = (실행 끝 파일 시각 − 넷리스트 시각) / 실행 창 수로 두고, (가) = 계획 창 수 K × c, (나) = c·K(K+1)/2(K = 판정이 난 창, 또는 계획 창 전부)를 합한다. 같은 기계·순차 실행·다른 시뮬레이터 부하 없음 조건을 기록한다.
* **측정값**(기록, S-19): 지금 137.7 s, (가) 146.8 s, (나) 463.2 s(판정 창)·513.2 s(계획 창). OP-4는 이 값과, (가)에서 시간 상한에 걸려 `failed`가 되는 사례(X-2)가 기준선에 있는지를 함께 보고 고른다. 그 사례 유무는 OP-4 착수 때 검증자가 같은 기록에서 센다.
* **독립 기준으로 남기는 것**(N-9): 지금 ngspice nutmeg 스크립트(`stability_control`)는 Python `early_window`와 같은 판정을 따로 구현한 것이다. 재구성 뒤에도 이 둘의 일치를 test로 둔다. 어댑터 방언 스크립트의 창 판정 결과를 코어 `early_window`와 비교하는 것이 oracle 종류 (b) '다른 방법의 참조구현' 독립 기준이다(`adapters/ngspice/test_dialect_stability.py`).
* 창 판정 규칙의 정본은 계약 문서와 design 40 §4다. 이 문서는 위치(코어)만 바꾸고 식은 바꾸지 않는다.

### 8.5 회로 이론 규칙 대 회피책 분리표(G-3)

| 항목 | 지금 | 분류 | 새 위치 |
|---|---|---|---|
| Nyquist N, 창 판정, 한계 사이클, 조기 unstable | 코어 수학 + nutmeg 스크립트 | 회로 이론 | 코어 `stability.py`(스크립트는 어댑터 능력의 방언 표현) |
| pz 결과 신뢰: '독립 증거(개루프 과도)로 확인될 때만 P 사용' | `stability_judgement`·`pz_validate` | 회로 이론(일반 규칙) | 코어 |
| 'BSIM4 대회로 `.pz`가 거짓 RHP 극을 낸다'는 사실 | 주석·README | 시뮬레이터 결함 사실 | 어댑터 `capabilities()`의 `pz` 신뢰 범위 메모. 판정은 위 일반 규칙이 한다 |
| 개루프를 동작점 값으로 다시 만들기 | `open_loop_parts` | 회로 이론(같은 루프 절단) | 코어 `build_benches.py` |
| β 루프 choke 값(입력 `loop_dc_choke_H`) | 입력·테스트벤치 | 테스트벤치 정의(사용자 입력) | 코어(값은 입력) |
| `>`·`<` 리다이렉션 회피, `stop when time > x`, `delete all` | nutmeg 스크립트 | 방언 회피책 | 어댑터 `dialect.py` |
| tmax·n_pp(`tran_plan`) | 코어 식 + LTE 걸음 제어 전제 | 수학은 회로 이론, '최대 걸음 지정이 실제 걸음을 묶는다'는 어댑터 의미 | 수학 = 코어. 어댑터는 `tran` 능력에 '최대 걸음 지정 지원'을 선언하고, 지원하지 않으면 코어는 `adapter_capability_missing` |
| `WRDATA_NUMDGT`(가수 자릿수 = numdgt+1, ngspice-46 실측) | 상수 | 어댑터 보정값 | `calibration.json` `data_digits` |
| `_NGSPICE_DEFAULT_TOL` | 상수 | 어댑터 보정값(시뮬레이터 문서 기본값) | `calibration.json` `default_tolerances` |

---

## 9. 실행 캐시 키(G-7)

* **원칙(코어)**: 키 = sha256(어댑터 지문 ∥ 방언 텍스트 바이트 ∥ 모델 묶음 sha256 정렬 목록 ∥ 실행 인자 ∥ `spiceinit_sha256`(§16 호환 모드, 없으면 빈 값 -- v0.4.1 M9)). 같은 키는 결과를 재사용한다. 키에 없는 입력이 결과를 바꾸면 결함이다.
* (v0.3.0, DR-10e, 계획 OQ-5 = O-14 (3)) 어댑터 지문(§0)과 모델 묶음 목록의 sha256은 **LF 정규화 값**이다(§8.1 `model_bundle`의 `lf`). 그래서 같은 코드·같은 모델을 CRLF·LF로 체크아웃한 두 기계의 키가 같다. 방언 텍스트 바이트는 디스크에 쓴 파일이 아니라 어댑터가 만든 문자열(줄 끝 `\n`)의 UTF-8 인코딩이다(기본안 B-35 -- 디스크 쓰기의 줄 끝은 OS 텍스트 모드에 따라 다를 수 있어 키에 넣지 않는다).
* **어댑터 몫**: include 문법을 따라 모델 묶음을 재귀로 모으는 일(지금 `_model_files`·`_INC`, `O/oracle_simulate.py:62-90`), 방언 텍스트 생성.
* 옛 `run_cache_key`(`O/oracle_simulate.py:86`)는 이 원칙으로 대체한다. 키 구성이 바뀌므로 옛 캐시 디렉터리는 재사용하지 않는다.
* (v0.2.6) 키의 어댑터 지문은 §0 제외 목록 방식이다. 그래서 `wall_s_per_window`(실행 시간 상한)는 키에 없다. 상한은 결과 값이 아니라 실행을 끊는 조건이고, 끊긴 실행은 옛 코드처럼 캐시 슬롯을 완성하지 않는다(옛 `run_ngspice`는 시간 초과 예외가 `subprocess.run`에서 나와 슬롯 `done`을 쓰기 전에 빠진다, `O/oracle_simulate.py:122-125`). 새 캐시도 `timed_out` 실행은 저장하지 않는다.

---

## 10. 오라클 기술자(G-5, G-9, D-9)

### 10.1 위치와 엔진 선언 참조

* 파일: `O/descriptors/<pdk>.oracle_descriptor.json`, 스키마 이름 `oracle_pdk_descriptor/1`(기본안).
* 엔진 선언 참조: `engine_decl = {path, sha256}`. 코어가 읽을 때 파일 sha256을 대조하고, 다르면 `pdk_descriptor_stale`이다. 엔진 선언 `sources`의 파일은 **source 키로만** 가리키고 경로·sha256을 다시 적지 않는다(P N3.4 단일 정본).
* **(v0.3.0, DR-6·DR-16, 계획 N3.4 'sha256 정의', X-13, X-26) sha256 정의**: `engine_decl.sha256` = 엔진 선언 파일 바이트의 **LF 정규화 sha256**(계획 N0.1, 사례 `5f32257b…`, S-37). 코어는 대조할 때마다 파일 바이트에서 다시 잰다. 엔진 `decl_sha256` 값과 **견주지 않는다**: gain-budget card SH-1(엔진 정본 sha256 LF 정규화, O-16 (1)) **병합 전**에는 엔진 값이 raw(`24f970d5…`)라 정의가 다르고, **병합 뒤**에는 정의가 같지만 엔진 값은 엔진 로더가 실행 중에 내는 값이라 오라클이 읽을 수 없다(엔진 import 금지). 그래서 X-13 test도 직접 비교가 아니라 파일 재측정을 유지한다(계획 X-13 'v0.6.8', §18.1).
* **중복 검사**(v0.3.0, 계획 N3.4 규칙 (iii)): 엔진 `sources`의 **모든** 파일(기술자가 쓰지 않는 원본 포함)과 `extra_sources` 파일을 바이트에서 LF 정규화로 다시 잰 값끼리 비교하고, 경로도 비교한다. 기록값(엔진 `sources.<키>.sha256`은 raw)끼리 견주지 않는다 -- LF 체크아웃 기계·미사용 원본에서 중복을 놓친다(계획 X-13 (iv)).
* **엔진 선언이 바뀔 때**(계획 N3.4): 그 card가 같은 변경에서 `engine_decl.sha256`을 **다시 잰 LF 정규화 값**으로 갱신한다(엔진 `decl_sha256`을 옮겨 적지 않는다). 선언 파일 바이트가 바뀌지 않으면 LF 정규화 값도 그대로라 기술자도 그대로다(계획 X-26 '순서·선행 조건 없음'. SH-1이 `sources` 기록을 다시 적어 바이트가 바뀌면 그 card가 갱신한다, 계획 N3.7 U-1 (c)).
* **멈춤 항목 DV-1(§19.2)**: 오라클 넷리스트가 include해야 하는 파일 가운데 엔진 선언 `sources`에 없는 것이 있다. 사례는 pmos의 `lod.spice`(S-7)다. 계획 N3.4는 '원본 PDK 파일의 경로·sha256 정본은 엔진 선언 하나'라고 했고, D-9는 엔진 선언을 바꾸지 않는다고 했다. 둘을 함께 지키면 이 파일을 넣을 곳이 없다. 이 문서는 아래 안을 **임시로** 적는다. S-7에 따라 계획 개정 뒤에 확정한다.
  * **확정(v0.2, 사용자 결정 O-3 = DV-1 (가), 계획 v0.5 N3.4 '파일마다 정본 한 곳')**: 엔진 선언에 없는 파일만 기술자 `extra_sources = {key: {path, sha256, base, provenance}}`에 둔다. 한 파일이 두 곳에 나오지 않도록 로더가 검사한다(`descriptor_source_duplicated`).
  * `provenance`(v0.2.4, P G-5 O-3): 엔진 선언 `sources`와 같은 수준의 출처다. 원본 `PROVENANCE.txt` 위치, 또는 웹 링크 + 저장소 커밋을 적는다. 비어 있으면 기술자 스키마 검증(`oracle_pdk_descriptor/1` 필수 칸)에서 거부한다.

### 10.2 스키마

```
{
  "schema": "oracle_pdk_descriptor/1",
  "engine_decl": {"path": ".../sky130_pdk_decl.json", "sha256": "..."},     # 사례
  "extra_engine_decls": {"<key>": {"path": "...", "sha256": "..."}},         # (v0.4.8, O-14 U-3) 다른 엔진 선언 파일 참조, 없으면 {}
  "extra_sources": {...},                                                    # 엔진 선언에 없는 파일만(O-3)
  "lut_record_root": {"location_decl": {"path": ".../lut_v2_location.json", "sha256": "..."}, "key": "pdk_root"},
                                                                             # (v0.2.6) LUT 기록 상대 경로의 뿌리 = 기존 정본 참조(§12.5 규칙 (iii))
  "lut_file_roles": [{"path": "...", "sha256": "..."}],                      # (v0.2.5) 기존 LUT 역할 옆 선언 참조(§12.5), 없으면 []
  "bin_rule_decl": {"path": "...", "sha256": "..."},                         # (v0.4.9, A-84 B-1) §16 선언 파일 참조, 선택. 없으면 8b에서 거부
  "model_family": "bsim4",                                                   # 사례 값
  "kinds": {
    "<kind>": {
      "call_form": "subckt_wrapper" | "model_direct",
      "name": {"value": "..."} | {"expr": <엔진 선언 식 형식>},
      "inner_device": {"expr": <모델 파일에서 subckt 안 첫 MOS 소자 이름을 읽는 식>} | null,
      "geometry_unit": {"source": <엔진 선언 quantity 키>} | "si",      # 모델 카드 면적 의존 식이 전제하는 L·W 단위(§10.6)
      "parallel_multiplier": {                                          # (v0.2.4, O-6 D-b) 병렬 배수 전달 규칙(§10.6)
        "to": [{"target": "instance_multiplier"} | {"target": "model_param", "name": {"value": "..."} | {"expr": ...}}],
        "source": <원본 근거: 모델 파일 source 키 + 그 파라미터가 면적 식에 들어감을 보이는 위치 식>
      },
      "includes": [{"source": <키>, "corner_section": <선택>}],
      "polarity": "n" | "p"
    }
  },
  "corners": {"names": [...], "select": {"how": "include_path" | "lib_section", ...}},
  "temperature": {"tnom": {"<kind>": {"source": <엔진 선언 quantity 키>}}, "range_source": "spec"},   # (v0.4.8, O-14 U-4) kind별
  "diffusion": {"decl": <extra_engine_decls 키>, "ad_per_w": <quantity 키>, "as_per_w": <키>, "pd_extra": <키>, "ps_extra": <키>},   # (v0.4.8, O-14 U-3)
  "mc": { ... §10.4 ... },
  "diagnostic": { ... §10.5 ... }
}
```

* **(v0.3.0, DR-7, 계획 N3.4 (i)) sha256 칸의 정의**: 기술자 안 모든 참조 sha256 칸(`engine_decl.sha256`, `extra_engine_decls.<키>.sha256`(v0.4.8), `extra_sources.<키>.sha256`, `lut_record_root.location_decl.sha256`, `lut_file_roles[*].sha256`)은 **LF 정규화 sha256**이다. 모두 저장소 안 텍스트 또는 저장소 밖 PDK 텍스트(`extra_sources` 사례 `lod.spice`)다. 바이너리 파일을 참조하는 칸이 생기면 그 칸은 raw로 선언한다(계획 N3.4 '바이너리' -- 지금 없음). 스키마는 칸마다 소문자 16진 64자(`^[0-9a-f]{64}$`)를 요구하고, 값이 raw(CRLF 바이트의 sha256)로 적혀 있으면 CRLF 파일에서 `pdk_descriptor_stale`로 거부된다(완료 조건 4 깨진 변형).
* `inner_device`는 미병합 `ng-bridge`의 `oracle_models` 내용 판정 규칙(MOS 4단자 subckt 안 첫 M 소자, P F-16)을 식으로 옮긴 것이다. noise 기여 이름 대응(F-8)과 진단 경로가 이 값을 쓴다. 방언 경로 틀(`@m.{inst}.…`)은 기술자에 두지 않고 어댑터가 만든다.
* 엔진 선언 식 형식(원본 파일 + 패턴 + 식)을 그대로 쓰므로, 코어 `descriptor.py`는 그 형식의 읽기 함수를 **새로 쓴다**. 엔진 `read_pdk_decl`을 import하지 않는다(오라클 C1).
* (v0.2.4) `kinds.<kind>.geometry_unit`·`parallel_multiplier`는 스키마상 선택 칸이지만, 없는 kind를 쓰는 벤치는 실행 전에 거부된다(§10.6). 스키마 단계에서 막지 않는 이유는 '규칙을 선언하지 않은 기술자가 실제로 거부됨'을 실행 경로에서 보이는 것이 OP-3 병합 조건 (a)이기 때문이다.
* (v0.2.4) `mc`·`diagnostic` 칸은 선택이다. OP-2가 만드는 기술자에는 없고 OP-5가 더한다(§20). 없으면 MC·진단 요청은 `mc_method_unsupported`로 거부한다(기술자 쪽 미선언. 어댑터 능력이 없을 때의 `adapter_capability_missing`과 구별한다. 순서는 §7.2).
* (v0.2.6 다시 씀, 검증 중간 지적 2) `lut_record_root`: LUT 슬라이스 meta `model_files_sha256`의 상대 경로가 기대는 뿌리다. **새 출처를 만들지 않고** 이미 있는 정본 `A/lut_v2_location.json`의 `pdk_root` 칸(S-35)을 그 파일의 경로 + sha256으로 참조한다. v0.2.5안('엔진 선언 `pdk_root` + 기술자에 적은 하위 경로')은 같은 사실(LUT 기록 뿌리)을 기술자에 한 번 더 적어 정본이 둘이 되는 안이라 버렸다(단일 정본 원칙). 엔진 파일은 바꾸지 않는다(계획 D-9, 8a: 참조만 하고 읽기 코드는 코어 `descriptor.py`가 새로 쓴다, 오라클 C1).
  * **해석 규칙**: 그 파일 형식(`gmid_lut_location/1`)의 계약 문서 규칙을 그대로 따른다. 출처는 코드 줄이 아니라 계약 **`E/lut/CONTRACT.md` 1.8(256-261행, base `52945ce` 재측정)**이다: `env[이름]`이 비어 있지 않으면 그 값, 아니면 `default`, 둘 다 없으면 거부, **경로는 `os.path.abspath`**(261행). (코드 `E/lut/data_location.py:32-41, :82-83`은 이 계약의 구현이고 출처로 인용하지 않는다.) 오라클은 엔진을 import하지 않으므로 같은 규칙을 새로 쓴다. 두 구현을 서로 불러 대조하는 test는 두지 않는다 -- 오라클 test는 엔진을 import하지 않고(P NFR-P3), 엔진 쪽 새 test는 계획 8a 첫째 예외('엔진 선언·오라클 기술자만 읽는 test')에 들지 않을 수 있다. 대신 test 작성자가 형식 규칙에서 기대값을 쓴 오라클 test(환경 값 있음 / 빈 값 / 없음 + `default` 있음 / 둘 다 없음 → 거부)로 보인다, §18.1 'X-13' 아래 행). 결과에 쓴 쪽(`env:<이름>` 또는 `config_default`)을 기록한다.
  * LUT meta의 절대 `pdk_root`(기계 경로)는 읽지 않는다. 그 값은 대조 대상 쪽 기록이고, 오라클이 대조 기준을 대조 대상에서 가져오지 않기 위해서다.
  * **엔진과의 차이 = 의도된 엄격**(v0.2.6 재검증 경미 1): 위치 선언에 `pdk_root` 칸이 없으면(계약 1.8에서 '선택') 엔진은 `pdk_root = None`으로 두고 슬라이스 meta의 절대 `pdk_root`로 돌아간다(`E/lut/provenance.py:14, :64`). 오라클은 돌아가지 않고 `lut_location_decl_invalid`로 거부한다(아래). 대조 기준을 대조 대상(LUT meta)에서 가져오면 규칙 (iii)이 자기 기록과 자기를 비교하게 되기 때문이다. 엔진 규칙을 그대로 따르지 않는 유일한 곳이고, 엔진 규칙이 바뀌면 두 구현이 어긋날 위험은 §19.4 X-D5에 적었다.
  * **위치 선언 파일 형식 오류의 코드**(v0.2.6 재검증 경미 4): 위치 선언 파일 자체의 형식 오류(계약 1.8 형식이 아님, `pdk_root` 칸 없음, `env`·`default` 둘 다 없음)는 기술자 스키마 위반 `descriptor_schema_invalid`와 구분해 `lut_location_decl_invalid`(`detail` = `{item, why}`, 계약 1.8의 `lut_location_config_invalid`와 같은 detail 모양)로 낸다. 기술자는 맞고 참조한 파일이 틀린 경우이기 때문이다. sha256 불일치는 그대로 `pdk_descriptor_stale`(`ref = lut_location_decl`)이다.
  * **교차 검사**(§7.2 8단계, `lut_record_root_mismatch`): 두 정본(위치 선언, 엔진 선언)이 같은 PDK 트리를 가리킴을 실행마다 보인다. (v0.3.0 다시 씀, DR-10c, 계획 N3.4 규칙 (iii) -- v0.2.6의 '기록값끼리 같은 sha256' 비교를 지움) (1) 짝 = LUT 기록값이 엔진 원본 파일의 LF 값 또는 raw 값과 같은 (상대 경로, 엔진 원본 키) 쌍(규칙 (ii)) (2) 짝마다 위 뿌리 아래 그 상대 경로 파일의 LF 값 == 그 엔진 원본 파일의 LF 값(둘 다 파일 바이트 재측정), 없으면 거부 (3) 짝이 0개면 거부(`detail.why = "no_pairs"`). 함수·test는 OP-3이다(계획 O-14 (4) J-5 (가) -- v0.2.6 §18.1의 OP-2 배치에서 옮김).
  * 계획 G-17 '보조 입력 sha256 대조의 PDK 뿌리 출처'를 이 칸으로 닫는다(기본안 B-18, v0.2.6 고침).
  * 범위 한계: 위치 선언은 LUT v2 데이터 묶음 하나의 정본이다. 다른 LUT 묶음(사례: `A/sky130_nfet_pfet_lut_sample.npz`)을 쓰는 실행은 그 묶음의 위치 선언이 따로 있어야 한다. 없으면 기술자 `lut_record_root`가 그 LUT의 뿌리를 정하지 못하고, 교차 검사가 실패하면 `lut_record_root_mismatch`로 거부된다(조용한 대체 없음).
  * 위치 선언 파일이 바뀌면(사례: LUT 묶음 항목 추가) 기술자 참조 sha256이 맞지 않아 `pdk_descriptor_stale`(`ref = lut_location_decl`)로 멈춘다. 계획 N3.4 '엔진 선언이 바뀔 때'와 같은 절차로, 그 파일을 바꾸는 card가 같은 변경에서 기술자 참조 sha256을 갱신한다(기계적 갱신). (v0.3.0, DR-7) 갱신 값 = 그 파일의 **LF 정규화 sha256**(사례 `07299556…`, S-37 -- 위치 선언 파일은 저장소 안 텍스트라 규칙 (i)). 위치 선언 안의 `files.*.sha256`(LUT 데이터 파일)은 규칙 (iv) raw 칸이고 이 기술자 칸이 아니다. 이 절차를 관련 계획에 알리는 것은 §19.2 알림.
* (v0.2.5) `lut_file_roles`: 기존 LUT 역할 옆 선언(§12.5) 파일의 경로·sha256 목록이다. 옆 선언은 검증자가 쓰고 이 칸은 그 참조만 담는다(기계적 갱신, 계획 N4-2a 예외 '측정 결과를 담은 옆 선언'). sha256이 다르면 `pdk_descriptor_stale`(`ref = lut_file_roles[<i>]`).

### 10.3 sky130 사례 값

* 사용자가 PDK 문서에서 선언하는 값이다(P N3.4). 값을 채우는 card에서 사용자 확인을 받는다. 채우는 card는 칸마다 다르다(§20): `mc`·`diagnostic` 칸은 OP-5, 나머지는 OP-2다.
* 칸별 상태:
  * `geometry_unit`(OP-2): 엔진 선언 quantity `mismatch_slope_geometry_unit_m`(출처 `models/all.spice` `.option scale`, S-13)를 source로 가리키는 안이 OP-1 측정과 맞는다. 값 확정은 OP-2 사용자 확인이다.
  * `parallel_multiplier`(OP-2): OP-1 측정(S-13 T6)은 '인스턴스 배수 + 래퍼 모델 파라미터 `mult`' 둘 다 줄 때 편차가 면적 의존대로 줄어듦을 보였다. 근거 위치는 카드 식 `sqrt(l*w*mult)`(`…tt.pm3.spice:67`)와 래퍼 기본값(`:30`)이다. 값 확정은 OP-2 사용자 확인이다.
  * `mc.enable`(OP-5): OP-1 측정(S-12)으로 켜는 법 종류는 `param_redefine`(카드의 불일치 변수를 분포 함수로 다시 선언)이 사례로 확인됐다. 대상 변수 목록은 엔진 선언 `mismatch_models.<kind>.parameters`와 모델 카드의 변수 선언 위치 식으로 가리킨다.
  * `mc.distribution`(OP-5): 카드의 통계 블록(`…tt.pm3.spice:19-27`, 주석 처리, S-12)을 위치 식으로 가리킨다. 그 파일은 엔진 선언 source(`nfet_01v8_tt_model_card`·`pfet_01v8_tt_model_card`)이므로 sha256 정본은 엔진 선언이다.
  * `extra_sources`(OP-2): 엔진 선언에 없는 include 파일(사례 pmos `lod.spice`)의 경로·sha256·출처. (v0.3.0, DR-8) sha256 사례 값 = `6200b50c…`(LF 정규화, S-37 -- 디스크 raw `20874af1…`이 아님).
  * `engine_decl`(OP-2, v0.3.0 DR-8): sha256 사례 값 = `5f32257b…`(`A/sky130_pdk_decl.json`의 LF 정규화, S-37 -- 엔진 `decl_sha256` raw `24f970d5…`이 아님).
  * `lut_record_root`(OP-2, v0.2.6 고침): 사례 값 = `A/lut_v2_location.json`의 경로·sha256과 키 `pdk_root`(S-35). 기술자가 새 값을 적지 않으므로 사용자 확인 대상 값이 없다(참조만). (v0.3.0, DR-8) sha256 사례 값 = `07299556…`(LF 정규화, S-37).
  * 위 세 값은 사례이고 기록 시점의 파일 바이트에서 다시 잰다. 값 확정과 기록은 OP-2 spec card(계획 OP-2 행, O-14 (4))다.
  * `extra_engine_decls`·`diffusion`·`temperature.tnom`(OP-2, v0.4.8, O-14 U-3·U-4): 값을 적지 않고 키로 가리킨다. 칸 대응은 OP-2 + OP-3 spec card 기술자 값 표.
  * `lut_file_roles`(OP-3, v0.2.5): 검증자 옆 선언(OP-3 병합 조건 (c))이 생기면 그 참조를 더한다.
  * `bin_rule_decl`(OP-7 어댑터 조각, v0.4.9): 경로·LF sha256만, 값 없음. `mc.mismatch_only`(OP-5, v0.4.9): 모델 카드 통계 블록의 전역 변동 절이 비어 `how = "none"`(§10.4).
  * `corners`: tt 하나만 엔진 선언에 있다. 다른 코너는 범위 밖(P T-32)

### 10.4 네이티브 MC 켜는 법과 분포 값 위치(O-1, O-6 D-a, G-9)

```
"mc": {
  "method": "native",
  "enable": {                                   # 켜는 법 종류 하나와 그 대상(P N3.4)
    "how": "lib_section" | "param_switch" | "include" | "param_redefine",
    "target": <종류별 대상, 아래 표>,
    "source": <원본 근거(source 키 + 위치 식)>
  },
  "distribution": {                             # 분포 값의 위치만. 값은 적지 않는다(O-6 D-a)
    "source": <엔진 선언 sources 키 또는 extra_sources 키>,
    "locate": {"pattern": ..., "fields": {"kind": <그룹>, "std": <그룹>, ...}}    # 엔진 선언 식 형식
  } | null,                                     # how가 PDK 쪽 통계 기능(lib_section·param_switch·include)이면 null 허용
  "mismatch_only": {"global_off": {"how": ..., "value": ...}, "source": <원본 근거>}    # 전역 공정 변동 끄는 법. (v0.4.9, A-84 C-8) 끌 것이 없으면(원본 통계 블록의 전역 변동 절이 빔) {"how": "none"}, source 필수
}                                               # (v0.2.5) v0.2.4의 "requires" 칸은 지웠다(계획 X-20, 아래 '요구 대 능력')
```

| `enable.how` | `target` | 분포 값 |
|---|---|---|
| `lib_section` | 통계 lib 섹션(source 키 + 섹션 이름) | PDK 섹션 안(오라클은 읽지 않음), `distribution` = null |
| `param_switch` | 스위치 파라미터 이름과 켬·끔 값(원본 근거) | PDK 파일 안, `distribution` = null |
| `include` | 더 include할 원본(source 키) | 그 파일 안, `distribution` = null |
| `param_redefine` | 다시 선언할 불일치 변수 목록(엔진 선언 `mismatch_models.<kind>.parameters` + 모델 파일의 선언 위치 식) | **필수**: PDK 원본의 통계 선언 위치(`distribution`). 어댑터가 읽은 분포 값을 시뮬레이터 분포 함수로 옮긴다 |

* **값의 출처 규칙**(O-6 D-a): 분포 종류·표준편차 같은 분포 값은 `distribution.locate`가 원본에서 읽은 값만 쓴다. 코어 `descriptor.py`가 원본 sha256을 대조한 뒤 읽어 어댑터에 값으로 넘긴다. 기술자에 값이 직접 적혀 있으면 `mc_distribution_inline`, `locate`가 없거나 0개를 찾으면 `mc_distribution_unlocated`, 가리킨 원본 sha256이 다르면 `pdk_descriptor_stale`이다(완료 조건 4의 깨진 변형 셋).
* **닫힌 키 집합**(v0.2.5, 검증 경미 지적): '값이 직접 적혀 있음'은 칸 이름을 추측해 찾지 않는다(`std`, `sigma`, `dist` 같은 이름 목록은 끝이 없다). 대신 허용 키를 닫는다. `distribution` = {`source`, `locate`}, `locate` = {`pattern`, `fields`}, `fields` = {<양 이름>: <패턴 그룹 이름(문자열)>}. 이 밖의 키가 하나라도 있거나 `fields` 값이 문자열 그룹 이름이 아니면(숫자 등) `mc_distribution_inline`이다. 그래서 어떤 이름으로 값을 적어도 걸린다. `distribution` 밖 `mc` 칸의 형식 위반은 `descriptor_schema_invalid`다(§7).
* **난수**: 시뮬레이터 RNG다. 코어는 표본마다 시드만 정하고(요청 `McNative.seed`와 표본 번호에서 정하는 결정적 규칙, 위치 `core/mc_math.py`, 규칙 문안은 OP-5. 같은 seed·같은 번호면 같은 시드가 PC-6의 전제다), 표본 값을 계산하지 않는다. 판정 MC 경로에는 '오라클이 계산한 값을 변수에 넣는' 경로가 없다(진단 경로 §13은 판정 밖).
* **요구 대 능력**(v0.2.5 고침, 계획 N3.4 MC 행·X-20·OQ-3 승인 L-3): 세 층으로 나눈다.
  * **코어 고정 요구**(`core/mc_math.py`의 상수 집합, 기술자·입력으로 바꿀 수 없음): 판정 MC 요청은 `per_instance_independent = true`(PC-3 (b))를 요구하고, 조건(온도)이 둘 이상이거나 `McNative.keep_identity`가 참인 요청은 `keep_identity_across_conditions = true`(PC-6)를 함께 요구한다.
  * **어댑터 능력**(§8.3 `mc_enable_kinds`): 켜는 법 종류마다 표본 수·시드 전달(`samples_per_run`, `seed`)과 표본 성질(위 두 칸)을 선언한다. 시뮬레이터 RNG 성질이라 어댑터 몫이다(계획 N3.1 경계 규칙 3).
  * **기술자**: PDK 데이터만(`enable.how`·`target`·`source`, `distribution` 위치, `mismatch_only`). v0.2.4의 `requires` 칸은 지웠다. 기술자가 요구를 적으면 기술자 선언으로 판정 요구를 낮출 경로가 생기기 때문이다(계획 X-20 이유). 기술자에 `requires` 키가 있으면 `descriptor_schema_invalid`다(닫힌 키 집합).
  * 코어는 실행 전에 (기술자 `enable.how` ∈ 어댑터 `mc_enable_kinds`), (코어 고정 요구 ⊆ 그 종류의 어댑터 선언), (`distribution`이 있으면 읽은 분포 종류 ∈ 어댑터 `mc_distributions`)를 확인하고, 하나라도 어기면 `mc_method_unsupported`(`side = "adapter"`, §7.2)다. 선언이 실제로 맞는지는 PC-3 (b)·PC-6이 조합마다 잰다.
* **표본마다 별도 실행**: 어댑터 선언 `samples_per_run = 1`이면(사례 ngspice, S-12 T5) 어댑터는 `McNative` 표본마다 실행을 따로 하고 표본 시드를 바꾼다. 결과 `McResult`는 같은 모양이다.
* 오라클은 분포·면적 의존 식을 갖지 않는다. 면적 의존은 모델 카드 식이고, 그 식에 들어가는 기하 단위·병렬 배수는 §10.6 규칙이 전달한다(P N3.4).
* 선언되지 않은 `method`·`enable.how`는 `mc_method_unsupported`다.
* sky130·ngspice 사례: OP-1(S-12)에서 `param_redefine`으로 소자별 독립이 확인됐다(O-1 (4) 사용자 결정 불요, 계획 X-12). 직접 섭동 대안은 설계하지 않는다.

### 10.5 진단 변수(O-1 (5))

```
"diagnostic": {
  "per_kind": {"<kind>": {"variables": {"source": <엔진 선언 mismatch_models.<kind>.parameters>},
                          "instance_param_rule": {"expr": <모델 파일에서 소자별로 덮어쓸 파라미터 이름을 읽는 식>},
                          "value_rule": {"expr": <표본 z를 파라미터 값으로 바꾸는 식, 원본 근거 포함>}}}
}
```

* 진단 경로(§13)만 쓴다. 판정·능력 기록에는 쓰지 않는다.
* (v0.2.4 고침) `value_rule`은 z를 **변수 값**으로 바꾸는 식만 담는다. 그 변수가 면적 의존 식을 지나 파라미터 섭동이 되는 과정은 모델 카드가 하고, 거기에 들어가는 기하 단위·병렬 배수는 §10.6 규칙이 소자 줄로 전달한다. 그래서 옛 `z·1e-6/√m`(S-4)의 단위 배율 `1e-6`과 `1/√m`은 기술자 식에도 옮기지 않는다(그 둘은 §10.6이 넷리스트에서 해결하는 것을 값으로 덮던 것이다, S-13. P N3.6 삭제 목록 '변수값 z·1e-6/√m 배율'). sky130 사례의 `value_rule`은 `distribution`이 가리키는 표준편차를 곱하는 식이고, 값 확정은 OP-5 사용자 확인이다.
* 진단 경로로 기준선 표본을 재현하는 검증 절차(§13.2 (가-2))는 이 규칙과 §10.6 소자 줄 규칙을 쓰므로 옛 넷리스트(SI 기하 + `m=` + 배율 값)와 넷리스트가 다르다. (v0.2.5) 그 판정 방식은 사용자 결정 O-8(계획 v0.6.3 X-19)로 정해졌다: (가-2)는 비트 동일 목표, 다르면 표본별 V_os만 분해능 안 + 차 기록(§13.2). 옛 넷리스트 형식을 재현하는 코드는 두지 않는다(계획 N3.6).

### 10.6 기하 단위·병렬 배수 전달(O-6 D-b, P G-5·G-9)

* **선언 위치**: kind마다 `geometry_unit`과 `parallel_multiplier`(§10.2). 둘은 '모델 호출 형식'의 일부다(P N3.4).
* **미선언 거부**(P OP-3, N9): 어댑터의 소자 줄 작성기는 공칭·MC·진단 공용 하나이고 규칙도 하나다. 그래서 공칭을 포함한 모든 해석에서, 벤치가 쓰는 kind의 두 칸 가운데 하나라도 없으면 실행 전에 `descriptor_geometry_undeclared`로 거부한다. 기본값으로 SI나 배수 1을 쓰지 않는다(P NFR-P6).
* **기하 단위 적용**:
  * `geometry_unit = "si"`: 어댑터는 IR 값(SI 길이)을 그대로 쓴다.
  * `geometry_unit = {"source": …}`: 코어가 원본에서 단위 u(m)를 읽어 어댑터에 넘긴다. 어댑터는 자기 `geometry_unit_application` 가운데 하나로 적용한다. 없으면 `adapter_capability_missing`(`detail = "geometry_unit_application"`, v0.2.5).
  * `"global_directive"` 방법(사례: 전역 scale 지시): 그 지시는 벤치 안 다른 원소에도 걸린다. 그래서 어댑터는 보정값 `global_geometry_directive.affects`의 **모든 IR 칸**을 u^power로 나눈 숫자로 쓰고, 목록 밖 칸은 그대로 쓴다. `affects` 선언이 없으면 이 방법을 쓸 수 없다(`adapter_calibration_missing`, v0.2.5). 이 처리가 맞는지의 판정 기준은 계획 G-9대로 **N4 기준선 동일성**이다(OP-3 병합 조건 (b): 공칭 op·ac 결과 N4-2 동일). 예: MOS L·W·확산 ad/as/pd/ps(면적은 power 2), 기하로 주는 수동 소자 칸. 이상 R·C·L 값·전원 값은 목록에 없으면 그대로다.
  * `"instance_numbers"` 방법: 지시 없이 인스턴스 숫자만 바꾸는 방언이 선언할 수 있는 이름이다. 첫 어댑터는 이 방법을 선언하지 않는다(기본안).
* **병렬 배수 전달**: IR `Mos.n_fingers`를 `parallel_multiplier.to`의 모든 대상에 같은 값으로 넘긴다(`instance_multiplier` = 방언의 인스턴스 병렬 배수, `model_param` = 그 이름의 호출 파라미터). 대상을 빼거나 더하지 않는다.
* **소자 줄 변화 기록**(P OP-3 병합 조건 (b)): 첫 조합 선언값을 적용하면 소자 줄 표기가 기준선과 달라질 수 있다(예: 숫자 단위, 배수 파라미터 추가, 전역 지시 줄, 그 지시가 든 include). 검증자는 N4-3 넷리스트 정규화 대조로 차이를 기록하고, 차이가 기하 단위·병렬 배수 선언에서 나온 것뿐임을 기록으로 보인다. 판정은 결과(N4-2)가 한다.
* **'차이가 선언에서만' 판정 절차**(v0.2.5, 검증 M-3). '선언 기인 한정'을 눈으로 읽어 정하지 않고 아래 셋으로 잰다. 주체는 검증자이고 스크립트도 검증자 소유다(입력 변환 N4-2a와 같은 지위, 코드 작성자의 어댑터 코드를 쓰지 않는다).
  1. **기준선 넷리스트에 선언 변환 적용**: 기준선 넷리스트(OP-1a 보관 텍스트)에 이 절의 규칙만 기계적으로 적용한다. 입력은 기술자 선언값(kind별 `geometry_unit`이 가리키는 u, `parallel_multiplier.to`)과 어댑터 보정값 `global_geometry_directive`(`affects`·`power`)다. 적용 내용 = `affects` 칸 숫자를 u^power로 나눔, `parallel_multiplier.to`의 모든 대상에 같은 배수를 둠, 지시 줄 또는 지시가 든 원본의 include 한 줄을 더함. (v0.2.6 고침) 그 줄의 **값**은 기술자 선언(u, 지시가 든 원본의 source 키)에서만, **문법**은 시뮬레이터 매뉴얼(R6 원문 쪽)에서만 가져온다. 어댑터 산출 넷리스트에서 그 줄을 베끼지 않는다 -- 베끼면 어댑터가 쓴 줄을 기준선 쪽에도 넣어 그 줄의 결함이 '차이 0'으로 지워진다. 지시 줄로 쓸지 include로 쓸지는 어댑터 선택이므로(§10.6 '전역 지시가 든 원본') 검증자 변환은 두 형태를 다 만들 수 있고, 어느 형태를 쓸지만 어댑터 산출물에서 읽는다(형태 선택 하나만 어댑터에 기대며, 그 의존을 판정 기록에 적는다). 이 변환 밖의 수정은 하지 않는다.
  2. **N4-3 정규화**: 변환한 기준선 넷리스트와 어댑터가 쓴 넷리스트를 같은 정규화(원소 순서, 이름 접두사, 공백·숫자 표기의 정규 형식)에 넣는다. 정규화 규칙은 선언과 무관한 표기 차이만 지운다(정규화가 선언 차이를 지우면 판정이 늘 참이 되므로, 정규화 규칙 목록을 판정 기록에 함께 둔다).
  3. **남은 차이 0**: 정규화 뒤 두 넷리스트의 줄 집합 차이가 0이면 '차이가 선언에서만'이다. 0이 아니면 남은 줄을 기록하고 멈추고 보고한다(기준 약화 금지, 계획 N4-4).
  * 사례에서 테스트벤치 원소 이름이 IR 규칙(`tb:<용도>:<대상>`, §4.1)으로 바뀌어 접두사가 달라지는 차이는 2단계 이름 정규화가 맡는다(이름 대응표 `ResultBundle.name_map`이 정규화 입력이다).
  * (v0.2.6) **`name_map` 의존 기록**: 2단계 이름 정규화는 코드 작성자 산출물인 `name_map`에 기댄다. 그래서 판정 기록에 (1) 그 의존을 적고 (2) `name_map`이 단사(두 IR 이름이 한 방언 이름으로 가지 않음)이고 IR 원소 집합 전체를 덮는지, (3) 기준선 넷리스트의 원소 이름이 IR 입력 이름(본 회로)과 옛 접두사 규약(S-9, 테스트벤치)으로 같은 대응을 주는지를 검증자가 따로 재서 함께 적는다. (3)이 어긋나면 남은 차이로 보고한다.
* **전역 지시가 든 원본**: 사례(sky130)에서 scale 지시는 모델 묶음 밖 파일(`models/all.spice`)에 있고 그 파일은 모든 모델을 함께 부른다(S-13). 어댑터가 지시를 넷리스트에 직접 쓰는지, 그 원본을 include하는지는 방언 선택이고 어댑터가 정한다. 어느 쪽이든 모델 묶음 비교(§12.5)와 캐시 키(§9)에 그 결과가 반영된다.
* **읽기 확인**: 어댑터 능력 `instance_geometry_readback`이 참이면 결과 `OpTable.instance_geometry_reported`(§6)에 시뮬레이터가 보고한 L·W·배수 **원값**을 싣는다(v0.2.5: 되돌리지 않음). 완료 조건 4a는 모든 실행에서 이 원값이 test 작성자가 IR·기술자 선언에서 따로 계산한 기대값과 같음을 단언한다(§18.1). 첫 어댑터는 이 능력을 선언해야 한다(4a 실행 조건).
* (v0.4.0, OP-3, 상위 v6.38.4 열아홉째 커밋 단순화·SF-1 범위 9와 같은 통합 병합) **DUT 저항 소자 줄 = 이상 R(θ) + C_par/2 쌍**: 저항값은 엔진과 같은 θ R(이상 R)이고, 양 끝에 C_par/2를 최저 전위 레일로 단다. C_par는 입력 `/passives[].parasitic_c_F`(§11.6, 상위 엔진 수동소자 값 블록 필드를 EO-1이 실음 -- 오라클이 다시 계산하지 않음). 측정 부하 원소(`measurement_load: true`, 상위 O-73)는 이상 R 그대로이고 그 칸을 갖지 않는다. PDK 셀 X 인스턴스(머리 저항·전압 계수 포함)는 레이아웃 뒤 최종 SPICE(상위 DEC-89 (5)·LY8)에서만이고 그 차는 대조 기록이다. **card 성격 확장 -- 원래 취지와 다름**(저항 있는 회로의 오라클 PM·극점 기준선이 바뀜): 오라클 쪽 변화표(원인 = 기생 C)가 필수다. 이 커밋의 완료 = 넷리스트 줄 손계산(이상 R + C_par/2 쌍, 측정 부하 저항은 이상 R, §18.1, ngspice 0). 오라클 극점 실측(저항 하나 RC 손회로에서 오라클 극점 = 엔진 극점 = 1/(R·(C_load + C_par/2)), tol 안) = OP-5 판정 묶음 1회(상위 O-229 규칙 2·O-232, 위임 A-94); OP-5 판정이 SF-1 범위 9 병합보다 먼저면 이 1건은 SF-1 범위 9의 보류 다리이고 채울 시점 = LA-1 측정 시점이다. **순서**: OP-3이 SF-1 범위 9보다 먼저 병합되면 칸이 아직 없어 이상 R이다 -- 소자 줄 작성기는 하나이고 칸은 그 통합 병합의 오라클 커밋에서 더한다.

---

## 11. 오라클 입력 형식(D-5) -- OP-3 입력 스키마 계약

### 11.0 계약의 지위·범위·변경 종류(v0.3.0 신설)

* **정본**: 이 절의 §11.1 칸 표·§11.2 검사 순서·§11.3 예시가 OP-3 입력 스키마의 정본이다(계획 G-18 '스키마 정본은 이 계획 하나', N5.2). 기계 판정 파일 `O/oracle_input.schema.json`은 OP-3이 이 표를 JSON Schema(Draft 2020-12, `$id` `spice_oracle_input/2`)로 옮긴 것이다. 둘이 다르면 이 절이 정본이고 그 차는 결함이다.
* **소비자**(이 계약을 읽는 곳): (a) 오라클 입력 검사(§11.2) (b) gain-budget card **EO-1** 생산자 -- 엔진 점(봉인 스냅샷: 시작점·front 점) → 오라클 입력(계획 N5.2, gain-budget N6.20, 사용자 결정 O-44 (1)) (c) A' 손분석 설계의 오라클 입력 -- 같은 스키마, A' 문서가 손분석과 함께 고정, 엔진 코드 미사용(계획 N3.9 '열다섯째 커밋', gain-budget N6.2 1212행) (d) 검증자 입력 변환 스크립트(§11.5) (e) test 작성자 -- **소스를 보지 않고 이 절만으로** 입력·거부 test를 쓴다.
* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **범위 구분**(사용자 결정 O-45 U1): **OP-3 칸**(§11.1) = EO-1이 내는 칸 전부. **G-18 확장 칸**(§11.6: 선언 triode, 훑기 방향, tol_V·I_off 열, 출력 기준, 슬루 선언) = 그 칸을 쓰는 card(OP-5, headroom-chain HC-O, OP-10)가 더하고, 그 card의 **같은 통합 병합에 EO-1 생산자 갱신 커밋(`Role: code`)**이 들어간다(계획 U-6, 선행 = EO-1 병합). 키 집합이 닫혀 있어(§11.1 공통 규칙) 확장 칸은 그 card 병합 전에는 넣으면 거부된다. 그래서 '오라클에 칸은 있는데 생산자가 안 내는' 상태와 '생산자가 내는데 오라클이 모르는' 상태가 둘 다 없다.
* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **바꾸는 쪽**: 이 표의 칸 이름·형식·필수를 바꾸는 이 계획 개정은 같은 때 gain-budget EO-1·VB-1·ME-1에 알린다(계획 U-6).
* **변경 종류**(계획 N4 0번, 사용자 결정 O-34 (1)): OP-3 입력 형식 전환 = 인터페이스 변경(옛 형식 거부 `oracle_input_format_old`, 모델 묶음 자동 대조로 새로 생기는 거부). 칸의 **뜻**은 아래 '옛 스키마 대비' 칸이 '같음'인 한 옛 스키마(`spice_oracle_input/1`) 그대로다 -- 그 칸들의 판정은 N4 2번 동일성.

### 11.1 칸 표(`spice_oracle_input/2`, card OP-3)

**공통 규칙**
* 단위는 SI(m, A, V, F, Ω, Hz, deg, °C). 소자 전압·전류 부호는 **크기 규칙**(옛 스키마 설명 그대로): NMOS는 그대로, PMOS는 부호 반전 -- 켜진 포화 PMOS의 ID·VGS·VDS가 양수, VSB = PMOS 바디-소스.
* 넷·원소 이름은 비어 있지 않은 문자열이다. 대소문자 접기 충돌은 §4.1 `ir_name_collision`이다.
* **닫힌 키 집합**(기본안 B-29): 아래 표에 없는 키는 모든 객체 층에서 거부한다(`oracle_input_schema_invalid`, `rule = additionalProperties`). 예외는 `provenance` 하나(열린 객체, 출력 전용). 근거: fail-closed(P NFR-P6), G-18 확장 칸을 그 card 전에 넣은 입력이 조용히 무시되지 않게 함(§11.0). 기준선 입력 593개 실측에서 스키마 밖 키는 변환이 지우는 `process` 키뿐이라 기준선 동일성(N4)에 영향이 없다(S-44).
* sha256 칸은 소문자 16진 64자(`^[0-9a-f]{64}$`)다.
* 파일 경로 칸(`process.descriptor.path`, `process.lut_files[].path`): 절대 경로 또는 **입력 파일이 있는 폴더 기준** 상대 경로(기본안 B-30). `topology.path`는 옛 규칙(저장소 루트 기준) 그대로다.

| 칸(JSON 포인터) | 형식 | 필수 | 뜻·제약 | 옛 스키마 대비 |
|---|---|---|---|---|
| `/schema` | 상수 `"spice_oracle_input/2"` | 예 | 형식 판별. 값이 `"spice_oracle_input/1"`이면 §11.2 1b에서 `oracle_input_format_old` | 새 필수(옛은 선택) |
| `/circuit` | string, 패턴 `^[A-Za-z0-9_][A-Za-z0-9_.-]*$`(보충 (e)) | 예 | 회로 식별자(출력 파일 이름 줄기) | 필수는 같음, 패턴은 새(기준선 영향 0) |
| `/process` | 객체(닫힘) | 예 | 아래 넷 칸 | 바뀜(D-5) |
| `/process/descriptor` | `{path: string, sha256: sha}`(닫힘, 둘 다 필수) | 예 | 오라클 기술자(§10) 참조. `sha256` = 기술자 파일의 **LF 정규화** sha256(계획 OQ-5 (c) = O-14 (3), DR-10f). 다르면 §11.2 2단계 `pdk_descriptor_stale`(`ref = input_descriptor`) | 새 |
| `/process/lut_files` | 배열, 길이 ≥ 1, 원소 `{path: string, sha256: sha, kinds: {<kind>: string \| null}}`(닫힘, 셋 다 필수, `kinds` 키 ≥ 1) | 예 | 이 설계점의 소자 DC 동작점을 정한 **LUT 슬라이스 파일**(엔진이 봉인 `dc_op`에 쓴 슬라이스, 기본안 B-32). `sha256` = 파일 **raw** sha256(계획 N3.4 규칙 (iv): git 밖 LUT 데이터). `kinds` = 이 파일의 모델 기록을 쓸 `devices[].kind` → meta `model_files_sha256`의 키: 평탄 표(폭 슬라이스, S-38)면 `null`, LUT 소자 키로 중첩된 dict(결합 파일, S-38)면 그 키 문자열. 이 기록이 그 kind의 모델 묶음 비교(§12.5)와 코너·온도(§11.2 2b)의 출처다 | 새(옛 `process.lut_npz` 하나를 대체) |
| `/process/corner` | string | 아니오 | §11.2 2b | 새 |
| `/process/temp_c` | number | 아니오 | §11.2 2b. LUT 기록과 다른 온도는 온도 게이트(§12.6)를 지난다 | 새 |
| `/simulator` | 객체(닫힘) | 예 | 아래 셋 | 새 |
| `/simulator/adapter` | string, 길이 ≥ 1 | 예 | 어댑터 이름(사례 `ngspice`). 등록 밖이면 `adapter_unknown` | 새 |
| `/simulator/exe` | string | 아니오 | 실행 파일 경로. CLI `--sim-exe`가 우선. 둘 다 없거나 파일이 없으면 `simulator_exe_missing` | 옛 `process.ngspice_exe` |
| `/simulator/options` | 객체, 값은 string | 아니오 | 시뮬레이터 옵션 키 = 값. 키 검증은 어댑터(B-5). DC 풀이 허용오차의 첫 출처(§8.3) | 옛 `testbench.options` |
| `/rails` | 배열, 길이 ≥ 1, 원소 `{net: string, voltage: number, reference?: bool}`(닫힘) | 예 | `reference: true`가 정확히 하나가 아니면 막힘(옛 그대로, `BLOCKED`). (v0.3.0) 기준 레일이 하나이고 그 `voltage` ≠ 0이면 거부(§11.2 1d `reference_rail_voltage` -- 옛 코드는 기준 넷을 노드 0으로 두면서 전압 값을 버렸다. 기준선 593개 가운데 해당 0개, 기준 레일 둘인 막힘 test 3개만 0 아닌 기준을 가짐) | 같음 + 새 규칙 |
| `/devices` | 배열, 원소(닫힘): 필수 `name, kind, drain, gate, source, bulk`(string), `L, finger_w`(number > 0, 보충 (d)), `n_fingers`(integer ≥ 1); 선택 `W`(number), `diffusion{ad_m2, as_m2, pd_m, ps_m}`(number ≥ 0, 넷 다 필수) + `basis`(string) | 예 | 인스턴스 = `finger_w` × `n_fingers`(병렬 배수 전달은 기술자, §10.6). `kind`는 기술자 `kinds`의 키(아니면 2단계 `descriptor_kind_undeclared`)이고 `process.lut_files[].kinds`에 있어야 한다(1d `lut_kind_coverage`). free 실행에서 확산 기하가 소자에도 기술자 `diffusion`에도 없으면 막힘(옛 C22 그대로) | 같음(닫힘만 새) |
| `/sources` | 배열, 원소(닫힘) `{name, kind: "current" \| "voltage", terminals: [string, string], value: number, value_basis?: string, not_in_topology_reason?: string(길이 ≥ 1)}` | 아니오 | 이상 전원. current = 전류가 p에서 소스를 지나 n으로 | 같음 |
| `/passives` | 배열, 원소(닫힘) `{name, kind: "resistor" \| "capacitor", terminals: [string, string], value: number > 0(보충 (c)), value_basis?, not_in_topology_reason?}` | 아니오 | | 같음 |
| `/feedback_passives` | string 배열, 중복 없음 | 아니오 | β 되먹임망(옛 C12·C14 규칙 그대로, 위반은 막힘) | 같음 |
| `/feedback_passives_basis` | string, 길이 ≥ 1 | 아니오 | 기록 전용 | 같음 |
| `/cm_output_loop` | `{drivers: string 배열(중복 없음, 길이 ≥ 1)}`(닫힘) | 아니오 | CM 루프(옛 규칙 그대로) | 같음 |
| `/bias_voltages` | 배열, 원소(닫힘) `{net: string, value: number}` | 아니오 | 구동 소자 없는 게이트 전용 넷의 이상 전압 | 같음 |
| `/ports` | 객체(닫힘) `{input_p, input_n, input, output_p, output_n, output}`(모두 string, 모두 선택) | 예 | 입력 = `input_p`+`input_n` 또는 `input`, 출력 = `output_p`+`output_n` 또는 `output`(옛 규칙 그대로) | 같음(닫힘만 새) |
| `/predictions` | 객체(닫힘) `{nodes?, devices?, metrics?}` | 예 | | 같음 |
| `/predictions/nodes` | `{<net>: number}` | 아니오 | 예측 DC 전압. 입력 넷 값은 free 입력 DC, forced 고정값 | 같음 |
| `/predictions/devices/<name>` | 객체(닫힘): `ID, VGS, VDS, VSB, gm, gds, gm_id`(number), `region`(`"sat" \| "triode" \| "off"`), `off_current_A`(number ≥ 0), `tol{ID_rel ≥ 0, gm_rel ≥ 0, basis}`(닫힘) -- 모두 선택 | 아니오 | 엔진 예측 동작점(크기 규칙). `region = "off"` = 엔진이 꺼짐으로 예측(전도 확인 대상 아님). **`off_current_A`는 OP-3 판 한정**: 소자별 전도 문턱(ε = 1 식, S-40) -- **OP-5 병합 때 스키마에서 지운다**(§11.6, 계획 OP-5 '옛 입력 칸 삭제') | 같음 |
| `/predictions/metrics[]` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 원소(닫힘) `{measure, value: number}` 필수, `name, rail, view, basis` 선택. `measure` ∈ {`dc_gain_db, ugf_hz, pm_deg, cm_pm_deg, f3db_hz, supply_current_A, ratio_db, rout_ohm, noise_th_in_v2hz, noise_fc_in_hz, noise_excess_th, noise_out_int_vrms, offset_in_sigma_mv, swing_out_v, icmr_v, icm_margin_v, slew_rate_v_per_s, settle_s`}. `ratio_db`이면 `view` = ratio 뷰, `rout_ohm`이면 `view` = sense 뷰 필수(옛 `$defs` 그대로) | 아니오 | 엔진 예측 metric(기록·모델 오차). OP-5가 `offset_sys_mv`, OP-11이 `power_dc_w`를 집합에 더한다(§11.6) | 같음 |
| `/acceptance` | 객체(닫힘) `{constraints?, not_measurable?}`. `constraints[]` 원소(닫힘) `{measure, op: ">=" \| "<=", limit: number}` 필수, `name, rail, view, basis` 선택. `measure`는 위 집합에서 `slew_rate_v_per_s`·`settle_s`를 뺀 16개 | 아니오 | 합격 판정 대상 선언 제약(Q5·C24·C26 규칙 그대로) | 같음 |
| `/testbench` | 객체(닫힘). 필수 `dc_choke_H, ac_couple_F`(number), `ac{fstart_hz, fstop_hz: number, points_per_decade: integer}`(+ 선택 `input_p_ac, input_n_ac, input_ac, diff_feedback_gain`). 선택 `loop_dc_choke_H`(number), `nodeset_from_predictions`(bool), `nodeset_per_line`(integer) | 예 | 테스트벤치 정의(옛 C11·C27 규칙 그대로) | `options` 칸이 빠짐(→ `simulator.options`. 있으면 1b `oracle_input_format_old`) |
| `/judge` | 객체(닫힘) `{sat_margin_V?: number, off_current_A?: number, tolerances?: {…}}`. `tolerances` 키(모두 number) = `ID_rel, VGS_abs_V, VDS_abs_V, VSB_abs_V, gm_rel, gds_rel, gm_id_rel, node_abs_V, W_rel, kcl_abs_A, dc_gain_db_abs, pm_deg_abs, ugf_hz_rel, f3db_hz_rel, supply_current_A_rel, ratio_db_abs, rout_ohm_rel, noise_th_in_v2hz_rel, noise_fc_in_hz_rel, noise_excess_th_rel, noise_out_int_vrms_rel, offset_in_sigma_mv_rel, swing_out_v_abs, icmr_v_abs, icm_margin_v_abs` | 아니오 | 판정 설정, 숫자 기본값 없음(없으면 N/A). 진입점 `--judge` 파일·`--sat-margin-v`가 덮어쓴다(옛 `merge_judge` 그대로). `off_current_A`는 OP-3 판 한정(OP-5에서 삭제, 기본안 B-34) | 같음 |
| `/noise` | 객체(닫힘) `{f_lo_hz: number > 0}` 필수 + 선택 `points_per_decade`(integer ≥ 1), `input_cell_devices`(string 배열), `closed_loop`(bool), `rel_resolution`(number > 0) | 아니오 | (v0.4.8, A-80) OP-5 전 판은 있으면 거부(§20 OP-3 행 '기간 동작'). OP-5부터 있을 때만 noise 측정(옛 U6) | 같음 |
| `/offset_mc` | 객체(닫힘) `{rel_resolution: number > 0}` 필수 + 선택 `seed`(integer), `max_samples`(integer ≥ 2) | 아니오 | (v0.4.8, A-80) OP-5 전 판은 있으면 `mc_method_unsupported`로 거부(§10.2). OP-5부터 네이티브 MC·`.tf` A(§21.5), 있을 때만 | 같음 |
| `/swing_icmr` | 객체(닫힘) `{swing?: bool, icmr?: bool}`(v0.3.4, DV-15 닫힘 -- 계획 G-18 v0.6.12·N3.9 ICMR 행, 사용자 결정 O-61 P8: 옛 `input_dc_V`·`input_dc_pending` 두 칸은 **OP-5 병합에서 지운다** -- 같은 spec 입력 DC 선언의 사본이라 선언 입력 DC 칸은 §11.6 `dc_sweep.input_dc` 하나; 지운 칸을 넣은 입력은 E5. OP-3 판 스키마는 두 칸을 그대로 받고 OP-5 통합 병합의 EO-1 생산자 갱신 커밋이 같은 병합에서 맞춘다(계획 U-6)) | 아니오 | (v0.4.8, A-80) OP-5 전 판은 있으면 거부(§20 OP-3 행 '기간 동작'). OP-5부터 있을 때만 swing·ICMR 측정(§11.6 `dc_sweep`을 함께 요구). `icm_margin_v` = §21.2 'metric 값' 포트별 식(v0.3.6 DV-18 닫힘 -- 선언 입력 DC를 쓰지 않음) | 같음 |
| `/topology` | 객체(닫힘) `{path: string}` 필수 + 선택 `sha256`(sha 형식, 보충 (b)) | 아니오 | C15 대조(옛 규칙 그대로) | 같음 |
| `/provenance` | 객체(**열림**) | 아니오 | **출력 전용** 기록: 오라클은 결과에 옮길 뿐 해석·판정하지 않는다. 생산자는 여기에 생산자 이름·스냅샷 지문 등을 적는다(기본안 B-31) | 같음 |
| `/cm_loop_passives` | -- | 금지 | 옛 스키마도 `false`(금지) | 같음 |

**칸 표 보충**(v0.3.0 같은 판 넷째 커밋, 검증 지적 12 -- 코드·기준선에서 확인한 사실, 근거 scratchpad `oracle_design/scan_keys.py`와 같은 방식의 기준선 593개 스캔):
* **(a) `lut_files`의 같은 kind 여러 파일**: 폭이 다른 슬라이스 여러 개가 같은 kind를 선언하는 것은 정상이다(설계점의 소자마다 다른 폭 슬라이스를 쓴다). 그 kind의 LUT 기록은 그 파일들 기록의 **합집합**이다 -- §12.5 규칙 (i) '그 kind가 쓴 LUT 슬라이스들의 모델 파일 기록 sha256 집합 ⊆ 묶음'(계획 N3.5 '오라클이 그 kind에 쓴 LUT 슬라이스들'). 코너·온도 기록은 파일끼리 모두 같아야 한다(§11.2 2b `lut_condition_conflict`).
* **(b) `topology.sha256`**: 공통 sha256 형식 규칙(소문자 16진 64자)이 이 칸에도 걸린다(어기면 1c `pattern`). 칸 종류 = 저장소 안 텍스트(topology JSON)를 가리키는 생산자 기록이고, 옛 코드는 파일 raw 바이트 sha256과 견주어 다르면 기록만 한다(`O/oracle_netlist.py:1182-1196`, 판정 무관). 그래서 대조는 계획 N3.4 규칙 (ii)다: 기록값이 파일의 LF 정규화 값과 같으면 일치, raw 값과만 같으면 일치 + `machine_dependent_refs`(`ref = topology`), 둘 다 아니면 옛과 같이 '다름' 기록(거부 아님). 기준선 입력 가운데 이 칸이 있는 것은 18개이고 모두 옛 raw 정의라 규칙 (ii)로 옛 결과(일치/기록)와 같다.
* **(c) `passives[].value`와 `acceptance.not_measurable`**: `passives[].value` = number, **> 0**(`exclusiveMinimum: 0`), 단위 SI(저항 Ω, 커패시터 F -- `kind`가 정함). 옛 스키마는 number만 요구했지만 기준선 593개에서 0 이하·비숫자 값은 0개라 이 제약의 기준선 영향은 없다. `acceptance.not_measurable` = string 배열(중복 허용, 기록 전용 -- SPICE로 잴 수 없어 뺀 선언 제약 이름, 옛 그대로, 판정 무관).
* **(d) `devices[].L`·`finger_w`**: number, **> 0**(`exclusiveMinimum: 0`) -- **스키마 규칙**(1c 거부)으로 정한다(막힘이 아님). 기준선 확인: S-44의 'L·finger_w가 양수가 아닌 소자 6개'는 실제로는 값이 문자열(`"0.5u"`)이거나 `finger_w`가 없는 C13 스키마 거부 test 입력 6개(`test_c13_{compare,netlist,run}_rejects_schem*`)이고, 옛 스키마의 `type`·`required` 위반으로 이미 거부(반환 2)였다. 새 스키마도 같은 칸에서 거부하므로 기준선 결과(거부)와 맞는다. 숫자 0 이하인 기준선 입력은 0개라 `exclusiveMinimum` 추가의 기준선 영향은 없다. (S-44의 '양수가 아닌 소자 6개' 문구는 이 사실로 읽는다.)
* **(e) `circuit` 허용 문자**: 출력 파일 이름 줄기로 쓰이므로(`<out_dir>/<circuit>[.<tag>].<bias>.*`, §11.7 거부 기록 이름) 정규식 `^[A-Za-z0-9_][A-Za-z0-9_.-]*$`(경로 구분자 `/`·`\`, 드라이브 `:`, 예약 문자 `*?"<>|`, 공백, 앞의 `.`을 금지)을 스키마 `pattern`으로 건다(어기면 1c). 기준선 593개의 `circuit` 값은 모두 이 정규식을 만족한다(영향 0). `tag`(CLI)도 같은 규칙으로 진입점이 검사한다(어기면 `oracle_input_schema_invalid`, `pointer = ""`, `rule = tag_pattern`). 거부 기록 이름의 대체값 `circuit`(§11.7)은 이 규칙을 어긴 입력에도 쓴다.

**삭제 칸**(넣으면 §11.2 1b `oracle_input_format_old`): `process.models`(`subckt`·`includes`·`op_probe`·`polarity`), `process.ngspice_exe`, `process.lut_npz`, `process.diffusion`(기술자로 이동, 소자별 `devices[].diffusion`은 유지), `testbench.options`. **조용히 지우는 칸은 없다**: `process.lut_reference_width_m`·`process.provenance`(S-21, 생산자 내부 값)는 닫힌 키 집합이라 넣으면 1c `oracle_input_schema_invalid`다(검증자 변환은 지운다, §11.5).

### 11.2 검사 순서와 조건 해석(§7.2 1·2·2b단계의 입력 쪽 세부)

처음 걸린 하나만 낸다(§7.2 원칙). 거부면 산출물은 거부 기록 하나다(§11.7).

| 단계 | 검사 | 코드 | 주체 |
|---|---|---|---|
| 1a | 입력 파일을 UTF-8 JSON으로 읽기 | `oracle_input_schema_invalid`(`rule = json_parse`) | 진입점 |
| 1b | 옛 형식 표지: `schema == "spice_oracle_input/1"`, 또는 `process.models`·`process.ngspice_exe`·`process.lut_npz`·`process.diffusion`·`testbench.options` 가운데 하나라도 있음. 이중 지원은 하지 않는다(P D-5, X-5) | `oracle_input_format_old`(`detail.markers` = 걸린 표지 전부) | 진입점 |
| 1c | JSON Schema(§11.1 표, Draft 2020-12) 위반 전부 | `oracle_input_schema_invalid`(`detail` 형식은 §7 표 -- 문제 키 포인터, JSON Schema 키워드, (pointer, rule) 사전순) | 진입점 |
| 1d | 스키마로 쓸 수 없는 교차 칸 규칙(이 판에서 새로 생긴 칸에만 둔다 -- 옛 의미 검사는 아래 '막힘'으로 그대로): `lut_kind_coverage`(모든 `devices[].kind`가 어떤 `lut_files[].kinds`의 키이고, 모든 `kinds` 키가 어떤 `devices[].kind`임), `reference_rail_voltage`(기준 레일이 하나일 때 그 전압 = 0), (v0.4.0, OP-3, OP-B3 -- 상위 E-21) `bias_gate_nets_mismatch`(회로 IR의 **구동 소자 없는 게이트 전용 넷** 집합 == `bias_voltages` 선언 넷 집합. 게이트 전용 넷 = 그 넷에 닿은 모든 IR 단자가 MOS gate이고 `/rails`·`/ports` 넷이 아닌 넷. 다르거나 선언이 없으면 거부 -- `oracle_netlist`의 예측 노드전압 이상 전압원 대체와 경고 경로를 지운다, §15.1). 1c를 통과한 입력에만 돌고, 1d 위반도 전부 모아 같은 정렬로 낸다 | `oracle_input_schema_invalid`(`rule` = 규칙 이름, `pointer` = 그 규칙이 가리키는 칸) | 코어 `input_check` |
| 1e | 어댑터 이름 → 실행 파일 → 어댑터 지문 | `adapter_unknown`, `simulator_exe_missing`, `adapter_fingerprint_unavailable` | 진입점 |
| 2 | 기술자(§7.2 2단계): 입력 `process.descriptor.sha256` = 기술자 파일 LF 값 → 기술자 스키마 → 참조 sha256 → 원본 중복 → 참조 파일 형식 → `devices[].kind` ⊆ 기술자 `kinds` | §7.2 2단계 코드, `descriptor_kind_undeclared` | 코어 |
| 2b | LUT 파일(§7.2 2b단계): 파일마다 raw sha256 → npz 키 `meta_json`이 있으면 `model_files_sha256` 모양을 `kinds` 선언과 대조(평탄 표 = 값이 전부 문자열, 이때 `kinds`는 키 하나에 값 `null` / 중첩 = 값이 전부 객체, 이때 `kinds` 값은 그 dict의 키) → 코너·온도 확정(아래) | `lut_file_stale`, `lut_meta_shape_mismatch`, `lut_condition_conflict`, `oracle_condition_missing` | 코어 `input_check` |

* **코너·온도 확정**(옛 §11.2를 다시 씀): 입력 `process.corner`·`process.temp_c`가 있으면 그것을 쓴다. 없는 쪽은 `lut_files`의 npz 키 `corner`·`temp_c` 기록에서 가져온다: 기록이 있는 파일들끼리 값이 모두 같아야 하고(다르면 `lut_condition_conflict`), 기록이 하나도 없으면 `oracle_condition_missing`(기본안 B-6 그대로). 입력 값과 LUT 기록이 다르면 입력 값을 쓰고, 온도가 다르면 온도 게이트(§12.6)를 지난다.
* `meta_json`이 없는 LUT 파일(모델 기록 없음)은 2b에서 거부하지 않는다 -- 그 판정은 §7.2 8단계 `lut_model_provenance_missing`이다(기록 빈 표와 같은 사유).
* **막힘(거부가 아님, 옛 동작 그대로)**: 기준 레일 개수 ≠ 1, C27 여기 가중, C14 되먹임 절단, CM 루프 구동자, 확산 기하 없음(C22) 등 옛 의미 검사는 지금처럼 판정 `BLOCKED` + `blockers` 문장으로 낸다(S-43). OP-3은 이 검사들의 위치만 코어로 옮기고 조건·문장(시뮬레이터 이름이 든 문장 제외, §15.1)은 바꾸지 않는다 -- N4 2번 동일성 대상이다.

### 11.3 최소 입력 예시와 깨진 변형(test 작성자용)

값은 **사례**다(상수 아님, 단위 SI). kind 이름 `nmos`는 사례 기술자의 `kinds` 키라고 가정한 것이고, 실제 키는 OP-2 spec card의 기술자 값이 정한다.

```json
{
 "schema": "spice_oracle_input/2",
 "circuit": "cs_toy",
 "process": {
  "descriptor": {"path": "descriptors/sky130.oracle_descriptor.json", "sha256": "<기술자 파일 LF 정규화 sha256, 소문자 64자>"},
  "lut_files": [{"path": "<LUT 폴더>/sky130_fd_pr__nfet_01v8__tt__W1p0000um_dc.npz",
                 "sha256": "<그 파일 raw sha256>", "kinds": {"nmos": null}}]
 },
 "simulator": {"adapter": "ngspice", "exe": "C:/ngspice/Spice64/bin/ngspice_con.exe",
               "options": {"reltol": "1e-4", "vntol": "1e-7", "abstol": "1e-13"}},
 "rails": [{"net": "vdd", "voltage": 1.8}, {"net": "gnd", "voltage": 0.0, "reference": true}],
 "devices": [{"name": "M1", "kind": "nmos", "drain": "out", "gate": "in", "source": "gnd", "bulk": "gnd",
              "L": 5e-7, "finger_w": 1e-6, "n_fingers": 2, "W": 2e-6}],
 "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "out"], "value": 20000.0}],
 "ports": {"input": "in", "output": "out"},
 "predictions": {"nodes": {"in": 0.6, "out": 0.9},
                 "devices": {"M1": {"ID": 4.5e-5, "VGS": 0.6, "VDS": 0.9, "VSB": 0.0, "gm": 6.0e-4, "gm_id": 13.3,
                                    "region": "sat", "off_current_A": 1.2e-11}},
                 "metrics": [{"measure": "dc_gain_db", "value": 21.6}]},
 "testbench": {"dc_choke_H": 1e6, "ac_couple_F": 1.0,
               "ac": {"fstart_hz": 1.0, "fstop_hz": 1e10, "points_per_decade": 20, "input_ac": 1.0}},
 "judge": {"sat_margin_V": 0.0}
}
```

깨진 변형(위 예시에서 한 곳만 바꿈 -- 예외: E10은 두 칸을 함께 바꿔야 앞 단계(1d)를 지나 2단계에 닿고, E13은 LUT 파일을 하나 더 두며, E17·E18은 아래 '픽스처 전제'를 함께 갖춘다) → 기대 결과. 시뮬레이터 호출 0인 것은 stub 어댑터로도 돈다.

| # | 바꾼 곳 | 기대 | 시뮬레이터 호출 |
|---|---|---|---|
| E1 | `schema` 칸 삭제 | `oracle_input_schema_invalid`(`/schema` required) | 0 |
| E2 | `schema` = `"spice_oracle_input/1"` | `oracle_input_format_old`(`markers` ∋ `schema`) | 0 |
| E3 | `process.models` 추가(아무 값) | `oracle_input_format_old`(`markers` ∋ `process.models`) | 0 |
| E4 | `testbench.options` 추가 | `oracle_input_format_old` | 0 |
| E5 | 최상위에 모르는 키 추가(사례 `declared_triode` -- OP-3 판에서는 G-18 확장 칸이 없음) | `oracle_input_schema_invalid`(`additionalProperties`) | 0 |
| E6 | `predictions.devices.M1.region` = `"linear"` | `oracle_input_schema_invalid`(enum) | 0 |
| E7 | `process.descriptor.sha256`을 대문자로 | `oracle_input_schema_invalid`(pattern) | 0 |
| E8 | `process.descriptor.sha256`을 기술자 파일의 **raw** 값으로(CRLF 체크아웃 파일) | `pdk_descriptor_stale`(`ref = input_descriptor`) | 0 |
| E9 | `lut_files[0].sha256` 한 글자 바꿈 / 파일 없음 | `lut_file_stale`(`actual_sha256` = 값 / `"missing"`) | 0 |
| E10 | `devices[0].kind`와 `lut_files[0].kinds`의 키를 **함께** 같은 기술자 미선언 키(사례 `"xmos"`)로 바꿈(하나만 바꾸면 1d `lut_kind_coverage`가 먼저 걸림) | `descriptor_kind_undeclared` | 0 |
| E11 | `lut_files[0].kinds` = `{"pmos": null}`(소자 kind와 다름) | `oracle_input_schema_invalid`(`rule = lut_kind_coverage`) | 0 |
| E12 | 평탄 meta 파일에 `kinds` = `{"nmos": "nfet_01v8"}` | `lut_meta_shape_mismatch`(`why = meta_key_given_for_flat`) | 0 |
| E13 | `lut_files`에 같은 kind의 LUT 파일을 하나 더 두고 두 파일의 npz `temp_c` 기록을 다르게(입력 `temp_c` 없음) | `lut_condition_conflict` | 0 |
| E14 | `simulator.adapter` = 등록 밖 이름 | `adapter_unknown` | 0 |
| E15 | `simulator.exe` 삭제(CLI `--sim-exe`도 없음) | `simulator_exe_missing` | 0 |
| E16 | 기준 레일 `gnd`의 `voltage` = 0.5 | `oracle_input_schema_invalid`(`rule = reference_rail_voltage`) | 0 |
| E17 | 기준 레일 둘(`vdd`에도 `reference: true`) | 거부 아님 -- 판정 `BLOCKED`(옛 막힘 그대로). 산출물 = `<stem>.compare.json`·`.compare.md`(`blockers` 있음), `reject.json` 없음, 반환 2 | 0 |
| E18 | LUT 파일에 `meta_json`이 없음(npz 키 `corner`·`temp_c`는 있음 -- 2b를 지나게) | `lut_model_provenance_missing`(§7.2 8단계) | 0 |

**픽스처 전제**(v0.3.0 검증 지적 8): 예시와 E1~E16의 양성 경로가 2b·8단계를 지나려면 LUT 파일은 npz 키 `corner`·`temp_c`와 `meta_json.model_files_sha256`(기술자 kind 묶음의 모델 파일 raw sha256)을 갖고, 그 기록에 보조 입력이 있으면 그 생성기의 역할 옆 선언(§12.5, 기술자 `lut_file_roles`가 참조)이 있어야 한다. 스텁 어댑터로 도는 test는 test 작성자가 이 전제를 갖춘 작은 픽스처를 쓴다(§15.4 `make_lut`). E17은 이 전제를 갖춘 채 기준 레일만 바꾸고, 막힘은 거부가 아니므로 8단계까지 지난 뒤 판정에서 `BLOCKED`가 된다.

### 11.4 생산자와 EO-1 계약

* **생산자**(v0.3.0 다시 씀 -- v0.2.5의 '저장소 안 생산자는 0'은 EO-1 병합 전까지의 사실이다): (a) gain-budget card **EO-1**(OP-3 뒤, 사용자 결정 O-44 (1)) -- 엔진 점 → 이 스키마 (b) **A' 손분석 입력** -- A' 문서가 손분석과 함께 고정, 엔진 코드(EO-1 생산자 포함) 미사용, LUT 파생 칸은 LUT 직접 조회(계획 G-18) (c) offset-trim 구동기 -- `output_reference`(G-18 확장 칸, §11.6) (d) 미병합 `ng-bridge` -- 고치지 않는다, U16 흡수 때 이 스키마로 맞춘다. 옛 `legacy_adapter`는 gain-budget LT-1 순서 3이 지운다(이 기능은 고치지 않음).
* **EO-1 계약 조항**(생산자 쪽 test는 gain-budget EO-1 완료 조건 (1)이 쓰고, 오라클은 아래만 보장한다):
  * **K-1 형식**: EO-1 출력은 §11.2 1a~1d를 통과해야 한다. 어기면 오라클이 거부하고 거부 기록(§11.7)을 낸다 -- EO-1 완료 조건 (1)의 'oracle이 스키마 위반 입력을 거부함 red'는 §11.3 E1~E16 가운데 하나를 생산자 출력에 적용해 보이면 된다.
  * **K-2 칸 범위**: §11.1 칸까지(O-45 U1). G-18 확장 칸(§11.6)은 내지 않는다 -- 키 집합이 닫혀 있어 내면 1c에서 거부된다(E5). 확장 칸은 그 card(OP-5·HC-O·OP-10)의 통합 병합에서 생산자를 갱신해 낸다.
  * **K-3 값의 출처**: 봉인 스냅샷 필드·spec 선언·LUT 파생표의 직렬화(재계산 없음)는 gain-budget N6.20 '입력 출처'의 조항이다. 오라클은 엔진을 import하지 않으므로 출처를 검사하지 않고 형식·교차 규칙·파일 sha256만 본다.
  * **K-4 판정에 닿는 칸**: 아래 칸이 없을 때 free 판정이 어떻게 되는지(옛 `oracle_compare` 동작 그대로, S-40·S-43). 생산자가 칸을 비우면 판정이 `INCOMPLETE`가 되므로, 어떤 칸을 낼지는 EO-1 design이 정하되 이 표를 근거로 한다.

    | 칸 | 없을 때 |
    |---|---|
    | `judge.sat_margin_V`(또는 CLI `--sat-margin-v`) | 포화 판정 N/A → `INCOMPLETE` |
    | `predictions.devices.<n>` 항목 자체(그 소자 예측 없음) | 그 소자 C23 전도 확인 'N/A(예측 없음)' → `INCOMPLETE`(`O/oracle_compare.py:238-239, :402-403`) |
    | 엔진 전도 예측 소자(`region` ≠ `"off"`)의 `predictions.devices.<n>.off_current_A` | 그 소자 C23 전도 확인 'N/A(off_current_A 없음)' → `INCOMPLETE`(`:242-244, :402-403`). **C23 전도 확인은 소자별 칸만 본다** -- `judge.off_current_A`로 대체되지 않는다(OP-3 판. OP-5 뒤에는 §21.1 두 단계가 이 자리) |
    | `judge.off_current_A` | 전도 확인과 무관. 소자별 칸이 없을 때의 문턱 대체값으로 두 곳에만 쓰인다: `region_spice` 표시('off', `:279-281`)와 포화 확인 대상 선택(SPICE ID > 문턱인 소자만, `:390-391`). 없으면 문턱 0 |
    | `acceptance.constraints` | 제약 판정 없음(PASS는 포화·전도만으로) |
    | `topology` | '동일성 미검증' 표시, `--require-topology`면 `BLOCKED` |
    | `noise`·`offset_mc`·`swing_icmr` 블록 | 그 측정 안 함(결과에 키 없음). (v0.4.8) 그 card 전 판에서 블록을 내면 거부되므로 EO-1 생산자는 OP-5 통합 병합까지 내지 않는다 |
    | `process.lut_files[]` 파일의 모델 기록 | `lut_model_provenance_missing` 거부(공칭 자동 대조, D-7) |

  * **K-5 '꺼짐 정의 판'**: EO-1 뒤 OP-5 전 기간에는 오라클 합격 판정의 꺼짐이 옛 ε = 1 식이다. 결과 `summary.conduction_definition`(§11.7)이 그 판을 기계로 읽을 수 있게 적는다 -- gain-budget N6.20 '판정 기록에 꺼짐 정의 판을 적는다'의 소비 칸.
  * (v0.4.2: EO-1 판정은 OP-5 뒤라 OP-3 판 기간에 이 칸을 쓰는 판정 기록은 없다 -- A-8, §19.2 PG-1) **K-6 OP-5 병합 때 바뀌는 것**: `predictions.devices.<n>.off_current_A`·`judge.off_current_A` 칸이 스키마에서 지워지고(넣으면 E5와 같이 거부), §11.6 확장 칸이 생긴다. EO-1 생산자의 그 부분 삭제·추가는 같은 통합 병합의 엔진 커밋이다(계획 OP-5 행).
* `O/smoke/`의 옛 형식 입력 3개(`*.oracle_input.json`)는 그 어댑터의 마지막 산출물로 **고정 자료**다(계획 X-5). 새 오라클로 직접 돌리지 않는다(옛 형식 거부, §11.2 1b). N4 비교 실행은 검증자 변환 스크립트(§11.5)가 판정 기록 안에 만든 새 형식 사본으로 하고, 그 사본은 배포 산출물이 아니다(계획 N4-2a). 저장소에 새 형식 smoke 입력이 필요해지면 code 역할 card로 만든다.
* 고정 자료 test의 처리(계획 OP-3 행, LT-1 순서 3. v0.3.0, DR-10i -- 사용자 결정 O-14 (4) J-1 (나)로 스키마 적합 test 전환도 OP-3): 고정 자료 자체만 읽는 test(finger 규칙, W 자기모순, feedback_passives 선언)는 남는다. 지금 코드에 묶인 둘은 **OP-3**이 같은 변경에서 바꾼다 -- 스키마 적합 test는 '옛 형식이라 거부(`oracle_input_format_old`)' test로, 넷리스트·루프 넷리스트 재생성 일치 test는 지우고 `criteria_weakened`에 올린다(같은 비교는 검증자 N4-3 대조가 맡는다). 그 test가 LT-1 순서 3에서 이미 옮겨졌으면 옮긴 파일에서, 아직이면 `test_legacy_adapter.py`에서 바꾼다(§18.2).

### 11.5 입력 변환 필드 대응표(P N4-2a, 검증자 변환 스크립트의 유일한 근거)

옛 형식(`spice_oracle_input/1`) → 새 형식. 검증자 소유 변환 스크립트(초안 `wt/_scratch_op1/n4_convert_input.py`)는 이 표만 따른다. 표 밖 `process` 키가 나오면 변환을 거부하고 기록한다(초안의 동작 그대로).

| 옛 칸 | 새 칸 | 처리 |
|---|---|---|
| (없음) | `schema` | (v0.3.0) `"spice_oracle_input/2"`. 옛 `schema` 값은 변환 기록에 남긴다 |
| `process.lut_npz` | `process.lut_files` | (v0.3.1, DV-7 닫힘 -- 사용자 결정 O-50 O1′, 계획 N4-2a '변환 대상 둘') **기계적 대응만**: `[{path: <옛 값>, sha256: <그 파일 raw>, kinds: {<입력의 각 devices kind>: null}}]`. 모델 기록을 지어 넣지 않는다(검증자 사본 LUT 안 기각 -- 근거 발명·D-7 우회). (i) OP-1 기준선 입력 593개의 변환 결과: 그 LUT에 모델 기록이 없어(S-39) **기대 결과 = §7.2 8단계 `lut_model_provenance_missing` 거부**(동작 변경, 계획 N4 0번 표 OP-3 행) -- 검증자 원인 변화표에 입력마다 사유 열과 원인 '모델 기록 없음'. (v0.4.8, A-80) 1c·1d에서 먼저 거부되는 입력은 사유별 목록과 §11.2 규칙으로 설명되면 원인 설명됨, 그 밖의 통과·다른 사유는 원인 미설명 변화라 멈추고 보고. (ii) OP-1b 추가 기준선 입력(모델 기록 있는 LUT v2 슬라이스)의 변환 결과: '정의가 그대로인 칸'의 N4-2 동일성 대상. 두 변환 모두 같은 검증자 스크립트·이 표를 쓴다. (v0.4.3, 위임 A-54 -- §11.2 2b와 맞춤, **원래 취지와 다름**: '기계적 대응만') LUT `model_files_sha256`이 중첩이면 kind마다 값 = 옛 `process.models[kind].subckt`와 끝이 같은 meta 키, 후보가 0개·2개 이상이면 변환 거부(기록에서 유도, 값을 짓지 않음). O-180으로 지운 sample LUT 입력 15개는 (i)에 들고, `sha256`·파일은 기준선 커밋 blob에서 얻으며 기대 결과는 그대로 `lut_model_provenance_missing`이다. (v0.4.4) §11.2 앞 단계가 먼저 거부하면(예: 1d, 미측정) OP-3 변화표에 사유별로 세고 원인 미설명으로 보고한다 |
| `process.models` | (없음) | 삭제. kind 정보는 기술자 `kinds` |
| `process.ngspice_exe` | `simulator.exe` | 옮긴 뒤 삭제. (v0.4.4, **원래 취지와 다름**: '기계적 대응'에 인자 추가) 옛 칸이 없으면 변환 인자 `exe`를 쓰고 기록에 `exe_absent`를 남긴다(값을 짓지 않음, 인자도 없으면 변환 거부). |
| `process.diffusion` | (없음) | 삭제. 기술자 `diffusion`. 옛 값은 변환 기록에 남겨 OP-2 대조에 쓴다 |
| `process.lut_reference_width_m` | (없음) | (v0.2.4) 삭제. 오라클 본체가 읽지 않는다(S-21). 옛 값은 변환 기록에 남긴다 |
| `process.provenance` | (없음) | (v0.2.4) 삭제. 같은 이유(S-21). 옛 값은 변환 기록에 남긴다 |
| `testbench.options` | `simulator.options` | 옮긴 뒤 삭제. 없으면 기록에 `options_absent`(X-D4 영향 대상, S-20) |
| (없음) | `process.descriptor` | 변환 인자로 받은 기술자 경로·sha256. 없으면 그 변환 결과는 N4에 쓰지 않는다. (v0.3.0, DR-10f, 계획 OQ-5 (c)) sha256 = 기술자 파일의 **LF 정규화** 값(변환 스크립트가 파일 바이트에서 잰다) |
| (없음) | `simulator.adapter` | 변환 인자 |
| `swing_icmr.input_dc_V`, `swing_icmr.input_dc_pending` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (없음) | (v0.3.4, DV-15 닫힘 -- 계획 G-18 v0.6.12, O-61 P8) OP-5 판 변환에서 삭제하고 옛 값은 변환 기록에 남긴다(`process.provenance` 행과 같은 처리). 스칼라 V_icm에서 넷별 `dc_sweep.input_dc`를 지어 넣지 않는다(선언을 만들지 않음 -- 추론 금지). 그래서 변환 입력의 `icm_margin_v`는 포트별 식(§21.2, v0.3.6 -- 선언 입력 DC와 무관)으로 재고(§21.2), 이 칸은 이미 정의를 바꾼 칸(계획 N4-2 '정의를 바꾼 칸' `icm_margin_v`)이라 동작 변경 기준 -- 검증자 원인 변화표에 원인 '선언 입력 DC 칸 정리(O-61 P8)'. OP-3 판 변환은 두 칸을 그대로 옮긴다 |
| (없음) | `process.corner`·`temp_c` | 쓰지 않는다(옛 형식에 없음, §11.2) |
| (없음) | G-18 확장 칸(§11.6) | 쓰지 않는다(옛 형식에 없음). OP-5 이후 그 칸이 필요한 측정을 기준선 입력으로 비교하지 않는다 -- 정의를 바꾼 칸이라 N4 0번 '동작 변경' 기준이고 기준선 동일성 대상이 아니다 |
| 그 밖 모든 칸 | 같은 칸 | 바꾸지 않는다 |

**결과 칸 이름 대응**(N4 비교 때, v0.2.4. v0.2.5 경로별로 다시 씀, 검증 M-1, 근거 S-23): 새 결과에서 이름이 바뀐 칸은 아래 대응으로 비교한다. 값은 바꾸지 않는다. 옛 `ngspice_rc`가 있던 **같은 자리**에 새 결과는 `status` 객체(`RunStatus`의 `rc`·`timed_out`·`error`·`warnings`·`log_excerpt`·`log_path`)를 둔다. `cache_state`는 `status`에 싣지 않고 캐시 상태 표로 뺀다(아래 '옛 상태 칸', C21). 비교 칸은 `status.rc`이고 이산 칸 정확 일치다(P N4-2). `status`의 다른 칸은 새 칸이라 비교에서 뺀다.

| 경로(옛 결과 JSON 위치) | 옛 생산자 | 새 칸 | 옛 `None`·칸 없음의 뜻 | 새 표현과 비교 규칙 | 바꾸는 card |
|---|---|---|---|---|---|
| 본 회로 `sim.ngspice_rc` | `oracle_simulate.py:1284` | `sim.status.rc` | 막힌 넷리스트 `None`(`:1279`, `skipped` 칸이 사유) | 실행하지 않은 벤치는 `sim.status = null`. 옛 `None` ↔ 새 `status = null` | OP-3 |
| β 루프 `sim.loop.ngspice_rc` | `:1314` | `sim.loop.status.rc` | 루프 없음은 `sim.loop = None`(칸 자체 없음) | 같음(`sim.loop = null`) | OP-3 |
| CM 루프 `sim.cm_loop.ngspice_rc` | `:1248` | `sim.cm_loop.status.rc` | CM 루프 없음은 `sim.cm_loop = None` | 같음 | OP-3 |
| 안정성 동작점 패스 `sim.ac.stability.transient.op_pass.ngspice_rc` | `:1113` | `…op_pass.status.rc` | 시간 초과 `None`(`_run_stab`, `:1066-1067`) | 시간 초과는 `status = {rc: null, timed_out: true, error: sim_timeout}`. 옛 `None` ↔ 새 `rc = null` + `timed_out = true` | OP-4 |
| 폐루프 과도 `…transient.ngspice_rc` | `:1178` | `…transient.status.rc` | 시간 초과 `None` | 위와 같음 | OP-4 |
| 연장 `…transient.extension.ngspice_rc` | `:1198` | `…extension.status.rc` | 시간 초과 `None` | 위와 같음 | OP-4 |
| pz `sim.ac.stability.pz.ngspice_rc` | `:784`(초기 `None`), `:808` | `…pz.status.rc` | (a) 실행 전 반환(입출력 노드 없음 `:791-793`, 개루프 생성 `ValueError` `:798-800`): 실행 안 함 (b) 시간 초과(`:805-807`) | (a) `status = null` (b) `rc = null` + `timed_out = true`. 옛 `None`은 `reason` 칸으로 (a)·(b)를 가른 뒤 대응한다 | OP-4 |
| pz 개루프 과도 확인 `…pz.validation.ngspice_rc` | `:1055` | `…pz.validation.status.rc` | 시간 초과 `None`(`_run_stab`) | 시간 초과 표현 | OP-4 |
| noise 개루프 `sim.noise.open_loop.ngspice_rc` | `oracle_noise.py:151` | `…open_loop.status.rc` | 시간 초과면 **칸 없음**(`:148-150`) | 옛 칸 없음 ↔ 새 `rc = null` + `timed_out = true` | OP-5 |
| offset_mc `sim.offset_mc.ngspice_rc` | `oracle_offset_mc.py:165` | `sim.offset_mc.status.rc` | 시간 초과면 칸 없음(`:162-164`) | (v0.2.6 고침) **옛 `ngspice_rc`는 비교에서 뺀다.** 근거(P-1 물리 정합): 옛 값은 표본 전부를 한 프로세스로 돈 실행 하나의 종료 코드이고, 새 네이티브 MC는 표본마다 별도 실행일 수 있다(§10.4 `samples_per_run = 1`). 같은 양이 아니므로 v0.2.5의 '모든 표본 rc가 같으면 그 값' 묶음 규칙(근거 없는 합성)은 버렸다. 새 결과는 `sim.offset_mc.sample_status = [RunStatus …]`(표본마다)와 실행 전 반환·전체 시간 초과용 `sim.offset_mc.status`를 둔다. 실행 성공 여부의 비교는 옛 결과에 이미 있는 이산 칸 **`n_failed`**로 한다. (v0.2.6 재검증 경미 2) 새 `n_failed`의 정의는 **옛 정의와 같다**: 옛 `oracle_offset_mc.py:170-177`은 로그 표본 블록에서 필요한 노드 값을 읽지 못한 표본 수(= 결과가 없는 표본 수)를 센다. 새 `n_failed`도 결과(`McResult.samples[k]`)가 `None`인 표본 수이고 rc를 보지 않는다. 표본별 rc는 `sample_status`에만 싣는다(rc ≠ 0이지만 결과가 읽힌 표본은 옛 코드처럼 `n_failed`에 들지 않는다). 정확 일치. 시간 초과(옛 칸 없음)는 새 `status.timed_out = true`와 옛 `status = "failed"`·사유로 대응 | OP-5 |
| swing `sim.swing_icmr.ngspice_runs` | `oracle_swing.py:306` | `sim.swing_icmr.sim_runs` | -- | 정수 정확 일치 | OP-5 |
| (v0.3.5, 검증 M3) offset_mc `sim.offset_mc.a_dc_signed` | `oracle_offset_mc.py:189` | `sim.a_dc.value` | 옛 차동 쌍 없음·`1e-3` 판정 실패면 `offset_mc.status = unavailable`(칸 없음) | 같은 양, 자리·이름만 바뀜(§21.5 3단계). 갈래가 발동하지 않은 차동 회로 = 비트 동일((가-1) 입력, §13.2); 단일 입력 회로·갈래 발동 회로 = 정의를 바꾼 칸(계획 N4-2, 원인 변화표). 옛 `unavailable` ↔ 새 `sim.a_dc.status = undefined` + 사유 | OP-5 |
| (옛 rc 기록 없음) noise 폐루프·refine·swing 표본 | `oracle_noise.py:294`, `oracle_simulate.py:857`, `oracle_swing.py:105` | 새 `status` | 옛 칸 없음 | 새 칸, 비교 제외 | OP-4·OP-5 |
| 지문 칸(어댑터·기술자·능력 기록 id) | -- | 새 칸 | -- | 비교 제외(P N4-2) | -- |
| `method` 칸(pz·noise·offset_mc, S-24) | `oracle_simulate.py:785`, `oracle_noise.py:122`, `oracle_offset_mc.py:115` | 같은 칸(값은 어댑터 `ResultBundle.method`) | -- | 설명 문자열이라 비교 제외(값에 해석 방법 바뀜이 드러나는 칸, 기본안 B-17) | OP-4·OP-5 |

* (v0.4.8, A-80) 위 표의 OP-4·OP-5 행 칸은 OP-3 병합부터 그 card 전까지 결과에 없다(그 실행을 하지 않음, §20 OP-3 행 '기간 동작'). 그 칸의 비교는 그 card의 N4 몫이다.
* 이 표의 소비자(S-23): `O/tests/test_oracle_c10_stability.py:1364, :1371`(연장 기록의 `ngspice_rc` 키·값 단언)은 OP-4가 §18.2대로 다시 쓰며 `status.rc`로 바꾼다. `O/README.md:489, :540, :567, :711`의 칸 설명은 그 칸을 바꾸는 card가 같은 변경에서 고친다(§17.4 README card별 재작성). `smoke/u6_selfchecks.py:136`의 `ngspice_runs` 소비는 OP-3에서 스크립트째 삭제되어 없어진다(§15.4, O-10). 그래서 OP-5가 `sim_runs`로 바꿀 때 바꿀 smoke 소비자는 없다. OP-3~OP-5 사이에는 u6 점검(잡음·MC·스윙·pz 자체 점검)이 없다 -- 기록 스크립트(판정 증거 아님, 스크립트 머리말)라 게이트 손실은 아니고, 점검 내용은 OP-4·OP-5의 새 test로 돌아온다.

**실행 전 반환 경로의 대응**(v0.2.6, 검증 중간 지적 1, 근거 S-31·S-23): 옛 코드는 시뮬레이터를 부르지 않고 돌아오는 경로가 여럿이고, 그 기록에는 rc 칸이 없거나(`None` 또는 칸 없음) 시간 초과 경로와 모양이 같다. 그래서 '칸 없음 = 시간 초과'로 대응하면 틀린다. 규칙:
1. 옛 기록을 **실행 여부**로 먼저 가른다. 판별 근거는 rc 칸이 아니라 그 기록의 `status`와 `reason`(그리고 안정성 기록의 `timeout` 칸)이다. 검증자는 아래 표의 **사유 대응표**(옛 사유 문장 → 경로 종류)로 가른다. 대응표는 옛 코드의 사유 문장 전수(아래 '옛 위치' 칸)에서 만들고, 표에 없는 사유 문장이 나오면 판정하지 않고 멈추고 보고한다(조용한 기본 대응 없음).
2. 경로 종류별 새 표현: **실행 안 함** → 그 기록의 `status`(RunStatus 칸) = `null`, 옛 `status`(문자열)·`reason`은 그대로 정확 일치 대상 / **시간 초과** → `status = {rc: null, timed_out: true, error: sim_timeout}` / **실행함** → `status.rc` 비교.
3. 사유 문장 자체는 이산 칸으로 정확 일치 대상이다. 단 문장에 시뮬레이터 이름이 든 넷(S-33)은 새 문장이 이름 없이 바뀌므로(P NFR-P1) 사유 대응표에 옛 → 새 문장 쌍으로 적고 그 쌍으로 비교한다. 사유 대응표는 검증자 소유이고(입력 변환 N4-2a와 같은 지위), 판정 기록에 둔다.

| 기록 | 옛 위치(실행 전 반환) | 옛 `status` | 경로 종류 | 바꾸는 card |
|---|---|---|---|---|
| noise 개루프 | `oracle_noise.py:125-128` | `failed` | 실행 안 함 | OP-5 |
| offset_mc | `oracle_offset_mc.py:111-113`(블록 없음, 결과 `None`) | -- | 측정 칸 자체 없음(옛·새 같음) | OP-5 |
| offset_mc | `:117-119`, `:121-122`, `:127-129`, `:134-136`, `:137-140`(다섯 곳) | `unavailable` | 실행 안 함. `:127-129`의 텍스트 검사(`Lfb_`)는 IR 역할 표 검사로 바뀌지만(§15.1) 사유 문장은 그대로 둔다 | OP-5 |
| offset_mc 시간 초과 | `:162-164` | `failed` | 시간 초과 | OP-5 |
| 안정성 과도 | `oracle_simulate.py:1096`(기본 `not_run`) + 사유 `:1134-1140`, `:1147` | `not_run` | 실행 안 함 | OP-4 |
| 안정성 과도 | `:1159`(동작점 패스 시간 초과), `:1161`(과도 넷리스트 생성 불가) | `failed` | `:1159` = **앞 실행(op_pass)의 시간 초과로 실행 안 함**(이 기록 자신은 실행 안 함, `timeout` 칸으로 판별), `:1161` = 실행 안 함 | OP-4 |
| pz | `:1118-1119`(동작점 패스 시간 초과, `pz_check` 호출 없음, rc 칸 없음) | `unavailable` | 실행 안 함(앞 실행 시간 초과) | OP-4 |
| pz | `:791-793`, `:798-800` | `unavailable` | 실행 안 함 | OP-4 |
| pz 시간 초과 | `:805-807` | `failed` | 시간 초과 | OP-4 |
| pz 개루프 과도 확인 | `:1033`, `:1043` | `not_run` | 실행 안 함 | OP-4 |

**옛 상태 칸의 대응**(v0.2.6, 근거 S-32): 결과 칸 `status`(RunStatus) 밖의 옛 상태 칸은 아래로 옮긴다.

| 옛 칸 | 새 칸 | 비교 | 소비자(옛 → 새) |
|---|---|---|---|
| `sim.log`(로그 경로) | `sim.status.log_path` | 제외(경로) | 없음 → 출력 전용(§6.1) |
| `sim.log_errors`, `sim.loop.log_errors`, `sim.cm_loop.log_errors`(정규식 적중 줄) | 같은 자리 `status.log_excerpt`(§7.1 대응표로 오류에 대응한 줄) | 제외. 옛 정규식은 거짓 적중이 있어(S-18) 같은 줄 집합이 아니다. 막힘 **유무**는 아래 `compare` 막힘으로 비교 | `O/oracle_compare.py:379, :384, :387` 막힘 문장 → 코어 `compare` 막힘 문장(`status.error` 코드 + `log_excerpt`) |
| `sim.op_ok` | `sim.op_ok`(같은 이름, 같은 규칙: 소자 하나라도 `id`가 있음, 코어가 `OpTable`에서 계산) | 정확 일치 | `O/oracle_compare.py:378`, CLI 종료 코드(`O/oracle_simulate.py:1404-1406` → `oracle_run` 하위 명령) |
| `sim.skipped`(막힌 넷리스트 사유) | `sim.skipped`(같은 이름) + `sim.status = null` | 정확 일치(사유 문장) | `O/oracle_run.py:45`(U6 측정 건너뜀), `O/oracle_compare.py:378` |
| `sim.cache = {main, loop}` | `sim.cache = {main, loop}`(같은 모양, 값 = 각 벤치 `RunStatus.cache_state`) | 제외(C21: 캐시 상태는 결과가 아니다) | test 넷(S-32) → §18.2 캐시 행 |
| `sim.stability_cache = {op_pass, transient, extension?, pz_validation?}` | 같은 모양, 값 = 각 벤치 `cache_state` | 제외(C21) | `test_oracle_c10_stability.py:832, :1321-1339` |
| `sim.cm_loop.cache`, `sim.cm_loop.stability_cache` | 같은 모양 | 제외(C21) | 없음 → 출력 전용 |
| `compare` 막힘 목록(`blockers`) | 같은 칸 | **유무와 개수** 정확 일치, 문장은 제외(시뮬레이터 이름이 든 문장이 바뀜, S-17) | 판정(막힘이면 PASS 불가) |

### 11.6 G-18 확장 칸(OP-5·headroom-chain HC-O·OP-6·OP-10·OP-11, v0.3.0 신설 -- 계획 G-18·G-19, DR-17)

* **정의를 정하지 않는다**(계획 G-18 '정의 정본 = gain-budget N3.8'): 아래 칸은 확정된 엔진 정의 문장을 재는 데 필요한 **입력 선언**이다. 오라클은 엔진을 import하지 않으므로 이 값들은 입력으로 온다(이름·포트 개수로 추측하지 않는다). (v0.3.3 셋째 커밋, 계획 G-18 '소자 식별(종류·L·W 등)은 회로 IR에 이미 있는 값을 쓰고 새 사본 칸을 두지 않는다(design이 확인)' -- **확인함**: 이 절의 칸과 §11.7 `conduction.points[].devices`·`departed`의 소자 키는 회로 IR 소자 이름(입력 `devices[].name`, §4.1)이고 종류·L·W·단자는 그 IR 원소에서 읽는다 -- 소자 식별용 새 칸·사본 없음.)
* **더하는 때**: 칸마다 '더하는 card'가 병합될 때 §11.1 표에 더해진다(키 집합이 닫혀 있어 그 전에는 거부, E5). 그 card의 통합 병합에 EO-1 생산자 갱신 커밋(`Role: code`)이 함께 들어간다(계획 U-6, 선행 = EO-1 병합). 칸별 대조 toy는 EO-1 완료 조건 (1)과 같은 꼴로 그 병합에서 판정한다(gain-budget N6.20). A' 손분석 입력도 같은 칸을 같은 때부터 갖는다(A' 문서가 고정).

| 칸 | 더하는 card | 형식 | 필수 | 뜻·출처 | 교차 규칙(1d) |
|---|---|---|---|---|---|
| `/intended_region` | (v0.3.1, 사용자 결정 O-53 B1 -- 옛 `/declared_triode`를 넓힌 **같은 정본 칸 하나**, 계획 G-18 B1) OP-5와 headroom-chain HC-O 가운데 **먼저 병합하는 쪽**(나중 card는 같은 칸을 쓴다; offset-trim augment_trim이 코드 상태마다 결정적으로 만든 값도 이 칸으로 온다) | 객체(닫힘) `{<device name>: "triode" \| "off"}`(포화 = 키 없음 기본) | 예(빈 객체 허용, 기본안 B-36 그대로) | spec `intended_region`(계획 N3.9 '선언 영역'). 판정 의미(정본 = gain-budget v6.20 N3.8 소자 조건, 사용자 결정 O-54·O-55 U1 -- 이 문서는 인용): **범위 판정**(§21.2)은 모든 MOS가 선언 영역(없음 = 포화: 전도 ∧ VDS ≥ VDSAT, triode: 전도 ∧ VDS < VDSAT, off: 판정 대상 밖 -- 상위 O-202)에 머무는 구간이고 훑기 중 이탈 점이 범위 끝(측정 거부 아님). **동작점**(합격 판정 점·범위 측정 공칭 점)에서 **선언 소자**의 실제 영역이 선언과 어긋나면 `intended_region_mismatch`로 그 판정을 **판정 불능**(`INCOMPLETE`, 사유 = 선언 오류; FAIL 아님)으로 집계하고, 선언 없는 소자의 비포화는 설계 실패(합격 판정 FAIL, §21.3). 영역 판정은 §21.1 한 단계(채널 ID 부호·VDS ≥ VDSAT)다 | 키 ∈ `devices[].name`(아니면 `rule = intended_region_unknown_device`), 값 ∈ {`triode`, `off`}(아니면 E5) |
| `/dc_sweep` | OP-5 | 객체(닫힘) `{excite: {<net>: number}, common: {<net>: number} \| null, input_dc?: {<net>: number}}`(v0.3.3 `input_dc` -- 선언 입력 DC, 계통 offset 기준점 V_id,0의 입력, §21.4 3단계; 출처 = spec 입력 DC 선언(gain-budget DEC-23 '이동의 기준점' -- θ 봉인점 입력과 같은 spec 값), EO-1 생산자가 옮김(참조 직렬화만, 다시 계산하지 않음), 엔진 예측 `predictions.nodes`를 대신 읽지 않음. (v0.3.4, DV-15 닫힘 -- 계획 G-18 v0.6.12, O-61 P8) **선언 입력 DC의 정본 칸은 이것 하나**다: (v0.3.6, DR-21·DV-18 닫힘 -- 계획 N3.9 ICMR 행 v0.6.14) 소비자 = §21.4 3단계 V_id,0 **하나**(`icm_margin_v`는 이 칸을 쓰지 않음 -- 포트별 식, §21.2); 옛 `swing_icmr.input_dc_V`·`input_dc_pending`은 OP-5에서 지움(§11.1)) | swing·ICMR·계통 offset 요청 때(없으면 `sweep_direction_undeclared`) | 정의 일반형(계획 N3.9, O-33 (7))의 **여기 방향**(전달 뷰 여기 방향 -- 엔진 gain 전달 뷰 `ac_excite`와 같은 값)과 **직교 성분**(공통모드). 사례: 차동 입력 `excite = {inp: 0.5, inn: -0.5}`, `common = {inp: 1, inn: 1}`; 단일 입력 `excite = {in: 1}`, `common = null`(차동이 없으면 공통모드 = 입력 자체, gain-budget N3.8 556행) | 키 ⊆ 입력 포트 넷(`ports.input_p/input_n/input`), 값 ≠ 0, `excite` 키 ≥ 1. `common`이 있으면 키 집합 = `excite` 키 집합이고 Σ_n excite_n·common_n = 0(선언값끼리의 곱 합이 정확히 0 -- 새 허용 폭 없음). (v0.3.0 검증 지적 10) `common = null`은 `excite` 키가 정확히 1개(단일 입력)일 때만 허용하고, 키가 2개 이상인데 `null`이면 `dc_sweep_ports` 위반이다. `rule = dc_sweep_ports \| dc_sweep_zero_weight \| dc_sweep_not_orthogonal`. (v0.3.3) `input_dc`가 있으면 키 집합 = `excite` 키 집합(아니면 `rule = dc_sweep_input_dc_ports`) |
| ~~`/confirmed_range`~~ | (**v0.4.0 삭제** -- 2단계·지목 왕복 삭제의 귀결, 작성자 도출, OP-5 착수 조건 = 사용자 확인(O-214 미룬 결정 (1)); 옛 행 history v0.4.0) | -- | -- | -- | -- |
| `/measure_feedback` | (v0.4.9, A-84 C-9 -- **더하는 card = OP-10**, 이 칸의 'OP-5' 문언은 기록) (v0.4.0 -- **슬루 전용**, ICMR은 읽지 않음, O-115; 아래 옛 문언의 ICMR 갈래는 기록) (v0.3.1, 사용자 결정 O-50 G4·G2·O-52 확인 1·O-53 A-1, 계획 G-18 'ICMR 측정 구성 -- 그 선언을 받는 입력 칸'·G-19 'β 선언을 읽는 입력 칸') OP-5(ICMR이 먼저 씀, OP-10 슬루가 같은 칸을 씀 -- 정의 하나) | 객체(닫힘) `{kind: "declared" \| "unity_follower", inverting_input?: <net>}` | ICMR·슬루 요청 때(없으면 `measure_feedback_undeclared`) | `declared` = spec 되먹임 구성(β) 선언이 있어 입력 회로·`feedback_passives`가 그 구성. `unity_follower` = 선언 없음(β = 1 기본, 결과에 'β = 1 기본' 표기). **(v0.3.7, 검증 필수 6·사용자 결정 O-78 (3)) EO-1 생산자 매핑**: spec `human.feedback.elements: []`(빈 list)는 `kind = unity_follower`로 옮긴다(`feedback_passives`는 비움) -- 엔진 정의 `E/authoring/spec_elements.py:19-20` "빈 list = 되먹임 수동소자 없음 = β=1 루프"(UD 9번)와 같은 뜻이고, `unity_follower`의 정의(β = 1)와 같다. 비지 않은 list는 `declared`(그 원소 = `feedback_passives`). 이 매핑이 없으면 library 단일 출력 회로가 모두 `declared` + 빈 선언(절단 넷 없음 → §21.2 2단계 (0) 'DC 되먹임 없음'; v0.3.9 둘째 커밋 문언, 옛 'DC 성분 없음') = §21.2 2단계 (e)로 떨어진다(검증 필수 6) -- (e) 해당 회로 0개(O-78 (2))는 이 매핑을 전제로 한다(계획 v0.6.15 N3.9 ICMR 행 '`human.feedback.elements: []`의 뜻'과 같음). `{pending}` 꼴의 매핑은 이 판이 정하지 않는다(K-2·K-6: 확장 칸 생산자는 그 card 통합 병합에서 갱신). `inverting_input` = spec이 반전 입력 포트를 선언했을 때만(O-53 A-1); 없으면 오라클이 `.tf` 부호로 정한다(§21.2, 엔진 값을 받지 않음, 포트 role 이름은 근거로 쓰지 않음). **단일 입력 회로**(`dc_sweep.excite` 키 1개)는 회로 그대로가 구성이라 `kind` 값과 무관하게 덧붙이는 연결이 없다(O-52 확인 1). (v0.3.6, DR-21·DR-22 -- 계획 N3.9 ICMR 행 '구성의 경계와 DC 닫힘'·슬루 행 '시작 동작점', 사용자 결정 O-67 (1)·O-68 (2)·O-69 (1), X-35) **차동 출력**: ICMR = 선언 되먹임에 DC 되먹임이 있으면(v0.3.9 -- §21.2 2단계 (0) 경로 판정, 계획 v0.6.16 DR-24; 옛 'IR `Resistor`·`Inductor` 원소' 종류 판정은 history v0.3.9) `declared` 그대로, 없거나 `unity_follower`(미선언)이면 **차동 모드 DC 닫힘**(§21.2 2단계); 슬루 = 선언 구성 전체(용량 포함), `unity_follower`면 `feedback_config_undeclared`(슬루만 정의 불능); (v0.3.8, DR-23 (1)) DC 되먹임 없는 선언(v0.3.9 같은 판정)의 슬루 = `feedback_config_undeclared`(`why = start_op_deferred`, t = 0 시작 동작점 경로는 gain-budget card AP-1 몫). (v0.3.8, DR-23 (2); v0.3.9 '없음' = 경로 판정) **단일 출력 + DC 되먹임 없는 선언**의 ICMR = `icmr_feedback_dc_absent`(§21.2 2단계 (e)), 단일 입력이면 (d)가 먼저. 구성 종류는 이 칸과 IR 원소 종류에서 오라클이 정하고 새 입력 칸을 두지 않는다 | `inverting_input` ∈ `excite` 키(아니면 `rule = measure_feedback_port`) |
| ~~`/sweep_rezoom`~~ | (**v0.4.0 삭제** -- 끝 괄호는 오라클이 혼자 좁힌다; 옛 행 history v0.4.0) | -- | -- | -- | -- |
| ~~`/conduction_columns/<device>`~~ | (v0.3.0 행, **v0.3.1에서 삭제** -- 행 본문은 history H7로 옮김(v0.3.2)) | -- | -- | -- | -- |
| `/output_reference` | OP-5(계통 offset, §21.4. OP-6 PC-10 V_sys도 같은 칸을 쓴다 -- OP-6은 OP-5 뒤) | 단일 출력: `{"kind": "net_value", "value_V": number, "source": string}` \| `{"kind": "net", "net": string, "source": string}` \| `{"kind": "rule_e_input_cm", "source": string}`(규칙 (e): 출력 = 입력 공통모드). 차동 출력: 칸 없음 또는 `{"kind": "differential"}` | 단일 출력에서 계통 offset·V_sys를 요청할 때(없으면 `reference_undeclared`) | (v0.3.1, 사용자 결정 O-53 B3 -- 아래 v0.3.0 제한·PC-10 보류 문장을 **대체**) 정의 자리 = gain-budget DEC-23 하나(v6.20 `7fe555b1` 223행 인용). spec 선언 기준 종류 셋 = **값** `net_value`(선언 목표 전압), **넷** `net`(출력이 그 넷과 같아야 함), **입력 추종** `rule_e_input_cm`(출력이 입력 CM을 따름) -- 셋 모두 계통 offset이 받는다(`kind_not_in_dec23` 거부 삭제); 차동 출력 기본 = V(p) − V(n) = 0(칸 없음 또는 `differential`); 선언 없는 단일 출력 = `reference_undeclared`(추론 금지). **PC-10(OP-6)은 같은 칸·같은 측정(§21.4)을 온도 조건에서 돌린 것 하나**(별도 칸·별도 정의 없음; 공칭 MC 표본 offset은 V_id* 출처가 아님). 기준은 온도와 무관하게 그대로 쓰고 온도마다 다시 풀지 않는다. 엔진 결과 `output_reference` 칸을 생산자가 옮긴다(오라클은 엔진 결과 JSON을 읽지 않음). (v0.3.0 기록 문장은 history H7) | 차동 출력 포트인데 `kind` ≠ `differential`, 또는 단일 출력인데 `differential` → `rule = output_reference_vs_ports` |
| `/slew` | OP-10 | (v0.4.0, DR-27) 객체(닫힘) `{node: string, step?: {lo_V: number, hi_V: number}, input_port?: string}` | 슬루 측정 요청 때(없으면 `slew_undeclared`) | 정의 정본 = gain-budget N3.8 '슬루율 측정 정의'. `node` = 슬루 정의 노드. `step` = 상위 spec `.tran` step(원문 계단 선언 회로 -- 정착과 같은 step), 없으면 전 폭. 계단 끝은 같은 덱 `.dc` 범위(§21.6 1a)에서 정하고 엔진 창·지목을 받지 않는다. 되먹임 구성·β = 1 기본 표기는 `/measure_feedback`. **작성자 판단**: `input_port`(계단 자리, 없으면 §21.6 1단계 규칙) | `node`가 IR 넷, `step.lo_V` < `step.hi_V` |
| `/kcl_zero_current_devices` | (v0.4.0, O-182 Q-S9 (A′)) OP-5 | string 배열 | 예(빈 배열 허용) | 엔진 `graph.dc_current_basis` 빈 항 행 소자 이름. 오라클 독립 유도 집합과 대조만 하고 판정 입력으로 쓰지 않는다(§21.1 2단계). A' 손분석 입력은 손으로 쓴다. **작성자 판단**: 칸 자리 | 원소 ∈ `devices[].name` |
| `/counted_rails` | (v0.4.0, 계획 OP-11 행) OP-11 | string 배열 | 아니오 | 상위 spec `counted_rails`(EO-1이 실음). 없으면 `power_dc_w` = 레일 전부, `supply_current_A` = not_computed(§21.7 2a) | 원소 ∈ `rails[].net` |
| `/passives[].parasitic_c_F`, `/passives[].measurement_load` | (v0.4.0, OP-3 §10.6 + 상위 SF-1 범위 9 통합 병합 / OP-11) | number ≥ 0 / bool | 저항만, 둘은 배타 | §10.6 DUT 저항 소자 줄, §21.7 2a 측정 부하 전류 | capacitor에 있으면 거부 |
| ~~`/icmr_relative_gain`~~ | (v0.4.0, O-215·O-221 -- **칸을 만들지 않음**: 첫 선언 회로 때 칸·판정 행·생산 card를 같이 정함, 그 전에는 닫힌 키 집합으로 거부) | -- | -- | -- | -- |

* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **measure 이름 추가**(기본안 B-37): OP-5가 `predictions.metrics[].measure`와 `acceptance.constraints[].measure`에 `offset_sys_mv`를(acceptance 대상으로 넣는 근거: DEC-90 (2)(3) -- 오라클이 측정할 수 있는 선언 제약은 판정 대상이고 측정할 수 없는 것만 `spice_unverifiable[]`; 엔진 쪽 `SPICE_UNVERIFIABLE` 해제는 gain-budget VB-1, 계획 U-4·U-6), `judge.tolerances`에 `offset_sys_mv_abs`(mV, 값이 0 근처라 상대 폭은 정의되지 않음)를 더한다. (v0.3.2, 계획 OP-10 행·O-50 G2) OP-10이 `predictions.metrics[].measure`와 `acceptance.constraints[].measure`에 방향별 슬루 `slew_rise_v_per_s`·`slew_fall_v_per_s`(gain-budget v6.20 N3.8 슬루 metric 이름)를 더한다 -- 결과 `slew.rise`·`slew.fall`(출력 방향 기준, §21.6)이 각각 그 measure 행이다. spec이 `slew_rate_v_per_s` 하나만 선언하면 생산자가 두 measure 모두에 그 제약을 싣는다(계획 OP-10 행 '두 방향 모두에 적용'). 판정 폭은 `judge.tolerances`에 `slew_rise_v_per_s_rel`·`slew_fall_v_per_s_rel`이 있을 때만(없으면 'N/A(tol 미설정)'). OP-11이 `predictions.metrics[].measure`에 `power_dc_w`를, `judge.tolerances`에 `power_dc_w_rel`을 더한다. `power_dc_w`를 `acceptance` 판정 대상에 넣을지는 계획이 정하지 않았으므로 넣지 않는다(계획 OP-11 '판정 허용 폭은 judge 선언이 있을 때만' -- 기록·모델 오차 칸, 넣으려면 계획 개정).
* **OP-5 병합 때 지우는 칸**(계획 OP-5 '옛 입력 칸 삭제', N3.9 '옛 입력 칸', O-204·O-205): `predictions.devices.<n>.off_current_A`, `judge.off_current_A`, `judge.sat_margin_V`, CLI `--sat-margin-v`. 지운 칸을 넣은 입력은 E5로 거부. 판정 점 값은 §21.1 부호·등식이 대신한다(LUT 조회 없음). 엔진 `device.dc_off_current`는 상위 O-205로 삭제(이 계획 몫 아님). v0.3.x 'tol_V·I_off' 문장은 history v0.4.0.
* `swing_icmr` 블록은 그대로 두고, OP-5 뒤에는 swing·ICMR 요청에 `dc_sweep`을 함께 요구한다(§21.2). (v0.3.4) 단 그 블록의 `input_dc_V`·`input_dc_pending` 두 칸은 OP-5에서 지운다(§11.1, DV-15 닫힘).

### 11.7 실행 결과 계약(EO-1 판정 배선이 읽는 것, v0.3.0 신설)

* **진입점**: `oracle_run <입력.json> <out_dir> --bias {free, forced, iso}… [--simulator 이름] [--sim-exe 경로] [--judge 파일] [--sat-margin-v V] [--timeout-s S] [--tag T] [--topology 경로] [--require-topology] [--omit 이름…] [--short 이름…] [--cache-dir 폴더]`. 옛 인자 그대로이고 `--ngspice`만 `--simulator`·`--sim-exe`로 바뀐다(계획 X-7). `--sat-margin-v`는 OP-3 판까지다(OP-5에서 지움, §21.3). CLI 값이 입력 칸보다 우선한다. 엔진은 이 진입점을 외부 단계로 부른다(엔진 import 없음, §17.2 542행 문안).
* **반환 코드**: 0 = 모든 bias 판정 `PASS`/`INCOMPLETE`, 1 = `FAIL`, 2 = `BLOCKED` 또는 **거부**(§7·§11.2의 코드). **판정 우선순위**(v0.4.0, 계획 N3.9 '합격 판정', 오라클이 최종): `FAIL`(§21.3 FAIL 하나라도) > `INCOMPLETE`(판정 불능 사유 있음) > `PASS`. 옛 `PENDING_CONDUCTION`·엔진 쪽 최종 판정은 삭제(O-205 (2)·O-210 RR-2, 소비자 0).
* **거부 기록**(기본안 B-33): 거부면 넷리스트·결과를 쓰지 않고 `<out_dir>/<circuit>.reject.json` 하나만 쓴다(1a·1c에서 `circuit`을 읽지 못했거나 그 값이 §11.1 보충 (e) 패턴을 어기면 `circuit.reject.json`) = `{"schema": "oracle_reject/1", "code": <§7 코드>, "detail": <그 코드의 detail>, "stage": <§7.2 단계 번호 문자열, 사례 "1c">, "input_path": <입력 경로>, "input_sha256": <입력 파일 raw sha256>}`. 옛 C13('스키마 위반이면 아무 산출물도 쓰지 않음')에서 바뀌는 곳은 이 파일 하나다. 소비자 = EO-1 판정 배선(엔진 점 레코드에 거부 사유를 붙인다, gain-budget N6.20 범위 (2))과 §18.1 입력 계약 test.
* **정상 결과**: bias마다 옛 `<stem>.compare.json`·`.compare.md`·`.sim.json`. compare JSON 최상위에 새 칸을 더한다:
  * `record_id` = 그 compare JSON에서 `record_id` 칸과 `netlist` 칸(진입점이 넣는 넷리스트 출력 경로, 옛 `O/oracle_run.py:57` `res["netlist"] = cir`)을 뺀 본문의(v0.3.0 검증 지적 11: `stem`(`:58`)은 회로·태그·bias에서 정해지는 값이라 남긴다. **불변식**: compare JSON의 다른 칸에는 출력 디렉터리 경로가 들어가지 않는다 -- 입력에서 온 경로(사례 `topology.path`)는 입력의 일부라 그대로 둔다. OP-3 test가 out_dir만 다른 두 실행의 `record_id` 같음으로 이 불변식을 단언한다) 정규 JSON(§0 '어댑터 지문'의 직렬화 규칙) sha256. 같은 코드·환경·입력이면 같은 값(결정성, 계획 N4 0번). 소비자 = EO-1 '판정 기록 id'.
  * `fingerprints = {adapter_fp, descriptor_fp, capability_record_id, compat_sha256}`(계획 FR-P9; `compat_sha256` = §16, v0.4.1 M9. 능력 기록을 쓰지 않은 공칭 실행이면 `capability_record_id = null`).
  * `machine_dependent_refs`(§6) -- 출력 전용.
  * `input_sha256` = 입력 파일 raw sha256(출력 전용, 판정 기록과 입력의 대응 확인용).
  * (v0.3.5, 검증 M2) **`sim_ref = {sha256}`** = 같은 줄기 `.sim.json`(sim 단계 결과 -- writer = 어댑터 실행 뒤의 코어 측정 단계: `sim.a_dc`·`sim.offset_sys`·`sim.offset_mc`·`sim.noise`·`sim.swing_icmr` 등)의 정규 JSON(§0 직렬화 규칙) sha256. compare JSON은 sim 결과를 **복사하지 않고** 이 참조로 가리킨다 -- `record_id` 본문에 `sim_ref`가 들어가므로 판정 기록 id가 sim 결과까지 묶는다(sim.json 내용에는 compare의 `record_id`·파일 이름이 들어가지 않아 순환 없음). 소비자는 같은 줄기 파일을 열어 sha256을 확인한 뒤 읽는다(다르면 그 기록을 쓰지 않음, fail-closed). **옛 `summary.u6`**(`O/oracle_compare.py:464` -- `noise`·`offset_mc`·`swing_icmr`를 sim에서 compare로 복사, 소비자 `:689` 보고서)는 승인된 사본 예외(계획 N3.3·N3.5)가 아니므로 **OP-3 코어 compare 이관에서 지우고** 보고서는 `sim_ref`로 sim.json을 읽는다 -- 결과 계약 변경이라 원래 취지와 다름(경미) X-R5, 사용자 확인(§19.4).
  * `summary.conduction_definition` ∈ {`"threshold_eps1"` -- OP-3 판(OP-5 전): SPICE ID > `off_current_A` 문턱(S-40, 옛 식), `"channel_sign"` -- OP-5 뒤: 채널 ID 부호·VDS ≥ VDSAT 한 단계(§21.1·§21.3, 옛 이름 `seal9_two_stage` 삭제)}. 소비자 = EO-1 판정 기록 '꺼짐 정의 판'(gain-budget N6.20, K-5).
  * (v0.4.0 다시 씀, OP-5 뒤, 계획 N3.9 '판정 점의 값') **`conduction.points[]`**(v0.4.9, A-84 C-10 -- 정본 = `<stem>.sim.json`의 `sim.conduction.points` 하나, compare JSON에 사본 없음) = 판정 점마다 `{point_id, kind: "accept" | "sweep", metric?, x?, temp_c?, m?, v_in?, devices: {<name>: {VDS, VSB, ID, VDSAT, gm_id, region_point}}}`. `x` = 훑기 좌표, `m` = swing 점의 출력 좌표 원값(swing 점에만), `v_in` = ICMR·`follower_input_range_v` 점의 풀린 입력 포트 전압 `{<입력 넷>: V}`(좌표 사본 없음 -- V_cm은 `swing_math.icmr_coord(v_in)` 한 함수). `ID` = 채널 op 값, 선언 단자 방향 부호. `region_point` ∈ {`sat`, `triode`, `off`, `not_judged`, `undefined`}. **범위 끝 기록**(정본 스키마 하나): `sim.swing_icmr.{swing, icmr}` = `{status: "final" | "undefined", reason?, lo, hi}`, 끝마다 `{pass_point_id, fail_point_id, rounds_cap, end_cause: "rail" | "rail_filter" | "region" | "functional", departed: [{device, declared, actual}]}`. 끝 괄호의 값은 점 기록이 정본이고 끝 기록에 사본을 두지 않는다. r은 저장하지 않고 소비자가 §18.3 식으로 다시 잰다. `departed` writer = 오라클 §21.1 하나. 범위 metric 값·제약 판정은 이 기록 하나에서 §21.2 'metric 값' 식으로 낸다 -- `status = "final"`만 있고 `provisional`·`range_final`·`range_input_fp`·확정 실행은 없다(graph 규칙 1·3; 옛 문장 history v0.4.0). 범위 제약 행은 그 실행의 `summary.verdict`에 바로 들어간다.
* EO-1이 읽는 칸 목록(이 밖의 칸은 EO-1 계약이 아니다): 반환 코드, 거부 기록 `code`·`detail`·`stage`, free `compare.json`의 `summary.verdict`·`summary.verdict_reason`·`record_id`·`summary.conduction_definition`·`fingerprints`. OP-5 통합 병합부터 `sim_ref`로 같은 줄기 sim.json의 `sim.a_dc`·`sim.offset_sys`·`sim.offset_mc`·`sim.swing_icmr`와 `conduction.points[]`를 **기록·대조용으로** 읽는다(판정은 오라클이 끝냄 -- 엔진 쪽 2단계 호출 자리·재요청·`stage2_judgment` 없음, 상위 N6.20 EO-1, 소비자 0; 첫 실제 판정 호출 = OP-5 통합 병합, A-23). OP-10 통합 병합부터 같은 실행의 `sim.slew`. 옛 문장 history v0.4.0.

---

## 12. 능력 확인(PC-1~PC-10, G-11)

### 12.1 공통

* 벤치는 소자 하나 또는 쌍의 IR이다. 기하는 기술자가 가리키는 모델 bin 안, LUT 격자 위 점에서 고른다. 고르는 규칙은 'LUT 슬라이스 기준 폭 + 그 L 앵커'이고 회로·PDK 이름이 없다.
* 실행은 일반 경로(코어 요청 → 어댑터)와 같다. 능력 확인 전용 실행 경로를 두지 않는다.
* 모든 PC에 대해 '깨진 변형에서 실제로 거부'를 먼저 test로 보인다(§18 T4).

### 12.2 항목

| PC | 벤치 | 판정(새 상수 없음) | 깨진 변형 픽스처 |
|---|---|---|---|
| PC-1 | 소자 하나, 공칭 바이어스 | op 수렴. 선언 op 파라미터(vdsat 포함) 전부 값이 있다. 모델 묶음 sha256은 어댑터 `model_bundle`이 계산한다(넘긴 묶음의 지문이라는 한계를 기록한다) | 모델 경로 틀림, op 이름 틀린 `model_family` 표 |
| PC-2 | 소자 하나, 정상·역방향 전도 두 점 + 0 V 감지원 | 정규화 ID 부호 = 감지원 전류 부호 × 극성 | 극성 규약을 뒤집은 어댑터 stub |
| PC-3 | 같은 기하·같은 바이어스 소자 둘 A·B, `McNative`(n = §12.3) | (a) A의 같은 ID 기준 VGS가 공칭과 분해능 넘게 다른 표본이 있다 (b) A·B 변화가 분해능 넘게 다른 표본이 있다 (c) MC를 끈 실행은 공칭과 비트 동일 (d) 기술자 `mismatch_only` 방법으로 불일치만 끄고 표본 실행만 켜면 모든 표본이 공칭과 분해능 안이다. 하나라도 벗어나면 전역 변동이 켜진 것으로 실패. A·B 공통 성분과 σ̂는 기록만 한다 | 불일치 꺼진 선언, 전역 공유 MC, 끄기 안 되는 선언, 전역 변동이 함께 켜진 선언 |
| PC-5 | 소자 하나, 같은 바이어스, 선언 온도 범위 끝점과 기준 온도 | ID 차가 해 정확도 전파 폭을 넘는다. 결과에서 읽은 온도 = 요청 온도 | 온도 무시 어댑터 stub |
| PC-6 | PC-3 벤치, 같은 seed로 기준 온도 단독 실행과 온도 여러 점 실행 | 같은 표본의 기준 온도 값이 두 실행에서 비트 동일 | 온도마다 재추출하는 어댑터 stub |
| PC-7 | 소자 하나, LUT 격자 점 몇 개 | 모델 묶음 비교 규칙(§12.5) 통과. 공칭 op(VDSAT 포함)가 LUT 점과 LUT 허용오차 안 | 다른 모델 파일, vdsat 정의가 다른 표 |
| PC-8 | 소자 하나, LUT `temp_c`와 다른 온도 | 그 온도로 실행됨(PC-5의 읽은 온도로 확인) | 입력 온도 무시 |
| PC-10 | 차동 입력쌍 + 출력 부하 + DC servo의 최소 IR(회로·PDK 이름 없음). 불일치는 끈다. 입력 `output_reference`(§11.6) 네 종류마다 하나씩(차동은 칸 없음과 `differential` 둘 다, v0.3.0) | (a) 온도 점마다 V_sys(T)를 낸다. 부호 규약은 offset-trim 계획 N0.1(V_sys,s = `output_error_v` / A_dm, 부호 있는 계통 offset)과 offset-trim design §0의 V_in(c) = −(V_sys0 + s·t·δ(c))를 따른다. 즉 servo가 출력을 선언 기준에 붙들 때의 입력 차동 전압이 V_in이고, 불일치·DAC가 없으면 V_sys(T) = −V_in(T)다. 기준은 선언값을 온도와 무관하게 그대로 쓴다(offset-trim G-15) (b) 온도 sweep 실행의 T_j 값 = T_j 단독 실행 값(비트 동일) (c) `output_reference`가 없으면 `reference_undeclared`로 멈춘다 (d) 각 값에 DC 풀이 허용오차의 입력 환산 전파값(§13.4)을 함께 낸다 (e) (v0.3.5, 검증 N3 -- 계획 N3.9 `offset_sys_mv` 행 'PC-10 = 이 측정을 온도 조건에서 돌린 것 하나', DEC-23 갈래) 온도 점마다 그 온도 실행의 `.sim.json`에 `sim.a_dc`(그 온도의 `.tf` A 한 측정)와 `sim.offset_sys`가 있고, V_sys(T)는 `sim.offset_sys`를 읽는다(별도 칸·별도 판정 없음, §21.4 4단계). 갈래가 발동한 온도 점(A = 0 손 회로; 0이 아닌 작은 \|A\|는 DV-17 뒤)은 V_sys(T) 값 없음·사유 `a_dc_undefined` | 기준 해를 버리고 흔들림만 내는 경로, 온도마다 기준을 다시 푸는 경로, `output_reference` 없이 기본 기준을 몰래 쓰는 경로, (v0.3.5) 갈래가 발동한 온도 점에서 servo 해의 입력 차를 V_sys(T)로 내는 경로 |

* (v0.2.4) PC-3 (c) '끈 실행 = 공칭 비트 동일'은 OP-1에서 출력 자릿수 동일까지만 확인됐다(S-12 15행). 비트 비교는 OP-6 PC-3 실행이 한다. PC-6의 사례 근거는 S-12 6행(같은 시드 표본이 세 온도에서 같음)이다.
* (v0.2.4) PC-3의 깨진 변형에는 분포 값 출처의 깨진 변형 셋(§10.4: 값 직접 기재, 원본 sha256 불일치, 위치 없음)도 넣는다(완료 조건 4). 이 셋은 실행 전 기술자 검증에서 거부되므로 시뮬레이터를 부르지 않는다.
* PC-4는 삭제됐다(O-1). MC 크기 판정은 offset-trim TR-7 §17-1 비교가 맡는다.
* PC-9는 LUT 생성 측정으로 옮겼다(D-4, §16).
* PC-11은 철회됐다(T-35).

### 12.3 PC-3 표본 수

* 기본안(P 계획): `sample_count(r)` = ceil(1 + 1/(2 r²))를 재사용한다. **r의 출처**(N-5): 능력 확인은 특정 회로 입력에 묶이지 않으므로, r은 `oracle_run capability` 실행 인자 `--rel-resolution`으로 검증자가 선언한다. 기본값은 없고, 없으면 실행을 거부한다. 같은 r을 쓰는 소비 측정(MC offset 판정의 입력 `offset_mc.rel_resolution`)과 비교할 수 있도록 n·r을 능력 기록 지문에 넣는다(§12.4).
* 이 규칙은 σ 추정용이라 존재 판정에는 과하다. 예를 들어 r = 0.05면 201 표본이다.
* 대안(존재 판정 최소 수)은 P G-11에 열려 있다. 기준 확률의 출처를 새 상수 없이 정하지 못해 이 문서도 대안을 고르지 않는다. 비용은 OP-1에서 기록했다(`R/m1_native_mc.jsonl` 12행 `wall_s_mean` 0.152 s·`wall_s_total` 30.3 s(N = 200), 13행은 같은 평균만 싣는다 -- v0.2.5 인용 정정. 소자 쌍 벤치, 표본마다 별도 실행. r = 0.05의 201 표본이면 약 30 s 규모. PC-3은 (a)(b)와 (d) 두 묶음을 돌린다).

### 12.4 능력 기록 `oracle_capability/1`

```
{
  "schema": "oracle_capability/1", "record_id": "<sha256 of canonical body>",
  "descriptor_fp": {...}, "adapter_fp": {...}, "check_code_fp": "<O/core/capability.py 등 sha256>",
  "lut": {"path", "slice_model_files_sha256": {...}},
  "checks": {"PC-1": {"bench_ir_fp", "requests", "measured", "resolution", "n", "verdict", "notes"}, ...},
  "conditions": {"temps_c": [...], "corner": "..."},
  "mc_sampling": {"rel_resolution": r, "n": n, "seed": ...},     # PC-3·PC-6 표본 규모. record_id 계산에 들어간다(지문)
  "created_by": "verifier", "date": "..."
}
```

* 저장 위치는 `O/capability/<기술자 지문 앞부분>__<어댑터 지문 앞부분>.json`(기본안)이다.
* (v0.2.6) `adapter_fp`의 코드 지문은 §0 '어댑터 지문'(제외 목록 방식, 계획 v0.6.6)이다. 그래서 `calibration.json`의 판정 키를 바꾸면 기록이 무효(`oracle_capability_stale`)가 되고, `wall_s_per_window`나 `calibration_tools/`만 바꾸면 기록이 그대로 유효하다. OP-8 LUT 메타의 생성 어댑터 지문(§15.3)과 캐시 키(§9)도 같은 지문을 쓴다.
* `record_id`는 내용의 정규 JSON sha256이다. (v0.2.6) 정규 JSON 직렬화 규칙은 §0 '어댑터 지문'과 같다(`sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, UTF-8). `record_id` 칸 자체는 계산 대상 본문에서 뺀다. offset-trim Δ_T 출처 지문과 `verified_by`(D-6)가 이 id를 가리킨다.
* **(v0.3.0, DR-9, 계획 OQ-5 = O-14 (3)) 지문의 sha256 정의**: `descriptor_fp`(기술자 파일 자체와 그 참조), `adapter_fp`의 코드 지문(§0), `check_code_fp`(`O/core/capability.py` 등 확인 코드 파일)는 모두 **LF 정규화 sha256**이다. 같은 코드·같은 기술자를 다른 줄 끝으로 체크아웃한 기계에서도 기록이 `oracle_capability_stale`이 되지 않는다(계획 OQ-5 근거). 이 지문들에는 옛 raw 기록이 없어(아직 만들어지지 않음) 규칙 (ii)가 필요 없다.
* **기계 의존 표시 칸**(v0.3.0, DR-9): 기록에 `machine_dependent_refs`(§6과 같은 모양)를 둔다 -- 그 기록을 만든 실행에서 규칙 (ii)의 raw 값으로만 맞은 옛 기록(엔진 원본 raw 기록, LUT `model_files_sha256`·`generator_sha256`)의 목록이다. 이 칸은 `record_id` 계산 본문에 들어간다(같은 기록이 다른 줄 끝 기계에서 다른 기계 의존 목록을 가지면 다른 기록이다). 유효성 판정(§12.6)은 이 칸을 읽지 않는다(출력 전용, §6.1).

### 12.5 모델 묶음 비교 규칙(P N3.5, `core/bundle.py`)

(v0.2.5 다시 씀, 검증 B-1, 계획 v0.6.3~v0.6.4 N3.5 '모델 묶음 비교 규칙'·F-18·X-22·OQ-1 승인 L-3·G-17.) v0.2.4는 LUT 기록 전체를 한 집합으로 오라클 묶음과 비교했다(계획 v0.6.2 판). 그 규칙은 기준 슬라이스 32/38이 기록한 생성 보조 입력(bin 경계표, S-29) 때문에 그 슬라이스를 쓰는 모든 공칭 실행에서 깨진다(계획 F-18). (v0.4.4 정정) 결합 파일 6개도 중첩 안에 기록한다: 38/38(`m2_m3_lut_meta.jsonl`). 32는 평탄 표만 센 값.

**두 쪽의 모양**: LUT 쪽은 슬라이스 meta `model_files_sha256`(기록 뿌리 기준 상대 경로 → sha256, 없으면 빈 표, `E/lut/provenance.py:11-13`). 오라클 쪽은 어댑터 `model_bundle`(kind마다 넷리스트 include 재귀로 모은 파일, 절대 경로 → {`lf`, `raw`} 두 값, §8.1 v0.3.0).

**(v0.3.0) LUT 쪽 읽기**: kind의 LUT 기록 = 입력 `process.lut_files` 가운데 `kinds`에 그 kind가 있는 파일들의 meta `model_files_sha256`에서, `kinds` 값이 `null`이면 평탄 표 그대로, 키 문자열이면 그 키의 하위 dict(§11.2 2b, S-38 두 모양). 모양이 선언과 다르거나 모르는 모양이면 이 단계 전에 `lut_meta_shape_mismatch`로 거부된다(조용한 평탄화 금지 -- 계획 N9 '관찰' 행을 이 규칙으로 닫는다).

**(v0.3.0, DR-10, 계획 N3.5 'sha256 정의') 비교의 sha256 정의**: LUT 기록 `model_files_sha256`·`generator_sha256`은 엔진 소유 **raw** 기록이다(F-19, 사례 pmos `lod.spice` 기록 `20874af1…` = 디스크 CRLF 값, S-37). 그래서 아래 규칙 (i)~(iii)의 '같다'는 계획 N3.4 규칙 (ii)다: 기록값이 그 파일의 **LF 값과 같으면 일치**, **raw 값과만 같으면 기계 의존 일치**(받고 결과 `machine_dependent_refs`에 적음), 둘 다 아니면 그 규칙 위반. 기록 하나를 파일 바이트에 대조하는 것이고 정의가 다른 두 기록값을 서로 견주지 않는다(규칙 (iii)). 묶음 파일끼리의 동일성과 결과·캐시 키에 적는 묶음 지문은 LF 값 하나로 낸다. 엔진 card SH-1(O-16 (1)) 전에도 오라클은 CRLF 체크아웃 기계에서 기계 의존 일치로 돈다. LF 체크아웃 기계에서는 기존 공유 LUT의 raw 기록이 맞지 않아 거부된다(계획 X-27 -- 기존 LUT 파일 수정은 범위 밖).

**기록 파일의 역할**(계획 N3.5): **모델 파일** = LUT 생성 시뮬레이터가 넷리스트 include로 읽은 파일(시뮬레이션 값을 정한다). **생성 보조 입력** = 생성기가 시뮬레이터 밖에서 직접 읽은 파일(사례: bin 경계표). 포함 관계 비교는 모델 파일에만 뜻이 있고, 보조 입력은 자기 sha256과 존재만 본다. 역할은 **선언으로만** 정한다(이름·확장자 규칙 금지).

**역할 선언의 출처**(계획 OQ-1, G-17):
* 새 LUT(OP-8 생성기): 슬라이스 meta에 기존 `model_files_sha256`과 나란히 새 칸 `model_files_role = {<상대 경로>: "model_file" | "generation_aux_input"}`을 쓴다(기본안 B-21). `model_files_sha256`의 모양은 바꾸지 않는다(엔진 `E/lut/provenance.py`가 그 칸을 경로 → sha256 표로 읽으므로).
* 기존 LUT: 검증자 **옆 선언** `O/descriptors/lut_file_roles/<생성기 sha256 앞 16자>.lut_file_roles.json`(기본안 B-19), 기술자 `lut_file_roles`가 경로·sha256으로 참조(§10.2). 형식 `lut_file_roles/1`:
  ```
  {"schema": "lut_file_roles/1",
   "generator_sha256": "<이 선언이 적용되는 슬라이스 meta generator_sha256 값>",
   "roles": {"<기록 상대 경로>": {"sha256": "<기록 sha256>", "role": "model_file" | "generation_aux_input"}},
   "evidence": {
     "generator": {"commit": "<그 생성기 판이 있는 저장소 커밋>" | null, "path": "<생성기 파일>", "data_path": "<commit이 null일 때만: 위치 선언 root 기준 경로>", "file_sha256": "<= generator_sha256>",
                   "matched": "lf" | "raw",                                                       # (v0.3.0) 후보 판 바이트 정의(아래 근거 (a))
                   "aux_append_lines": [<보조 입력을 include 목록 밖에서 기록에 더한 줄 번호>]},     # 계획 근거 (a)
     "include_graph": {"start": [<그 생성기 판이 LUT 생성 넷리스트에 쓴 include·lib 대상 전부>],
                       "files": [<시작점에서 include 재귀로 닿는 기록 상대 경로 전부>]},            # 계획 근거 (b)
     "measured_by": "verifier", "date": "..."}}
  ```
  * 키 집합은 닫혀 있다(밖의 키, 역할 값 밖, `evidence` 칸 없음은 `lut_file_roles_invalid`).
  * **근거 두 측정이 모두 맞아야** 그 파일을 `generation_aux_input`으로 적는다(계획 v0.6.3.1 세부): (a) 생성기 근거 = 슬라이스 meta `generator_sha256`과 파일 sha256이 같은 생성기 판을 저장소 이력 또는 위치 선언 `root` 아래 파일(v0.4.8, A-80)에서 찾고, 그 판의 코드에서 그 파일이 넷리스트 include 목록 밖에서 기록에 더해진 위치(사례: 지금 판 `A/sky130_lut_sweep.py:688, :891`, S-29). 그 판을 못 찾으면 옆 선언을 만들지 않고 그 슬라이스는 역할 미선언으로 남는다. (v0.3.0, DR-10, 계획 N3.4 (ii)) **후보 판 바이트의 두 정의**: 정규화 = 그 판 blob(`git show <rev>:<경로>`)을 LF 정규화한 바이트의 sha256, raw = 그 판을 이 기계 줄 끝 설정으로 체크아웃한 바이트(`git cat-file --filters <rev>:<경로>`)의 sha256. 정규화로 맞으면 일치, raw로만 맞으면 기계 의존 일치(옆 선언 `evidence.generator`에 `matched: "lf" \| "raw"`를 적는다). 검증자 측정 `gen2.txt`(`gen2.py:25-27`)는 blob을 LF → CRLF로 직접 바꿔 raw를 근사했다(계획 N7.5 DR-10). (v0.4.8, A-80) 폭 슬라이스 32개의 `8df35d2e…`는 저장소 이력에 없고 위치 선언 `root` 아래 파일이다. git 밖 파일은 체크아웃 변환이 없어 파일 바이트가 곧 그 판이고 `matched`는 위 두 정의를 그 바이트에 그대로 쓴다. 어느 출처에서도 못 찾는 판은 근거 (a)를 낮추지 않고 멈추고 보고한다 (b) include 그래프 밖 = **LUT 생성 넷리스트의 include 줄**(그 생성기 판이 넷리스트에 쓴 대상, 사례 `_included_files`, S-29)에서 시작한 include 재귀 그래프에 그 파일이 없음. 시작점을 LUT 기록 파일 집합에서 고르지 않는다(기록된 보조 입력이 스스로 시작점이 되는 것을 막는다).
  * 역할 판정을 오라클 묶음에서 하지 않는 이유(계획 N3.5): LUT가 다른 모델 파일을 썼을 때(PC-7이 거부해야 하는 경우) 그 파일이 '보조 입력'으로 분류되어 규칙 (i)이 늘 참이 된다.
* **적용**: 코어는 슬라이스마다 meta `generator_sha256`이 옆 선언의 `generator_sha256`과 같고, 기록의 (경로, sha256) 쌍이 `roles`의 쌍과 같을 때만 그 역할을 쓴다. 맞지 않는 쌍은 **역할 미선언**이다. 역할 미선언 기록 파일은 모델 파일로 본다(조용한 면제 없음, 계획 N3.5).

**규칙**(kind별, sha256 **값** 집합으로 비교, 경로는 비교하지 않음):
* (i) 그 kind가 쓴 LUT 슬라이스들의 **모델 파일** 기록 sha256 집합 ⊆ 어댑터 `model_bundle`의 sha256 집합. 어기면 `model_bundle_mismatch`.
* (ii) 기술자가 정한 호출 모델(`kinds.<kind>.name`)을 정의한 파일의 sha256 ∈ 그 LUT **모델 파일** 기록 집합. 정의 파일은 묶음 파일 가운데 그 이름의 `.subckt`/`.model` 정의가 있는 파일이다. 어기면 `model_bundle_mismatch`.
* (iii) **보조 입력** 기록마다 기록 sha256 = 기술자 `lut_record_root`(§10.2) 아래 같은 상대 경로 파일의 지금 sha256. 다르거나 그 경로에 파일이 없으면 `lut_aux_input_mismatch`(없는 파일을 '대조 불가'로 넘기지 않는다).
* LUT 기록이 빈 표이면 `lut_model_provenance_missing`이다. 지금 LUT의 기록은 OP-1 (ii)에서 38/38 있음으로 측정됐다(S-15, 계획 X-14 확인됨).
* 결과: 옆 선언이 없으면 기존 LUT 32 슬라이스는 (i)에서 거부된다(보조 입력이 모델 파일로 취급되어 오라클 묶음에 없다). (v0.4.4 정정) 결합 파일 6개도 중첩 안에 기록한다: 38/38(`m2_m3_lut_meta.jsonl`). 32는 평탄 표만 센 값. 그래서 **OP-3 병합 조건 (c)**(계획 OP-3 행)가 이 공백을 막는다: 옆 선언이 있고, 그 선언으로 첫 조합의 공칭 실행이 (i)~(iii)을 통과하며, 역할을 지운 변형과 보조 입력 sha256을 바꾼 변형이 실제로 거부된다(§18.1 'OP-3 병합 (c)' 행).
* 옆 선언은 검증자가 쓰고 저장소에 둔다(계획 N4-2a 예외 '측정 결과를 담은 옆 선언'). 값의 근거가 검증자 측정이라 코드 작성자가 쓰면 자기 측정을 자기가 판정하게 되기 때문이다. 옆 선언은 측정값과 근거만 담는 데이터이고 피검 경로의 산출물이 아니다.

### 12.6 게이트와 배선

| 게이트 | 위치(진입점) | 요구 |
|---|---|---|
| 공칭 자동 대조 | `oracle_run` 모든 실행, 벤치 실행 직전 | §12.5 통과 |
| MC 게이트 | `oracle_run`의 `offset_mc` 측정 진입 | 유효 능력 기록 + PC-3 통과 |
| 온도 게이트 | 해석 요청 `Condition.temp_c`가 LUT `temp_c`와 다르거나 온도가 여럿인 모든 실행 | 유효 능력 기록 + PC-5·PC-6·PC-8·PC-10 통과 |
| 진단 금지 | `core/compare.py`·`core/capability.py`의 입력 | 진단 결과가 들어오면 `diagnostic_not_a_gate` |

* 기록이 유효하려면 descriptor_fp·adapter_fp·check_code_fp·LUT 기록이 지금 값과 모두 같아야 한다.

### 12.7 공정 무관 증거

같은 `core/capability.py`가 두 기술자에서 돈다. 하나는 sky130 기술자(사례)이고, 다른 하나는 손 모델 픽스처 기술자다(시뮬레이터 내장 단순 모델 + 면적 의존이 있는 선언 불일치 변수, test 작성자 소유). 손 모델 기술자의 네이티브 MC 켜는 법은 픽스처가 정한다. 실제 두 번째 PDK는 완료 조건이 아니다(D-8).

* **손 모델 픽스처는 정본 하나다**(P v0.6.1 B-2): `O/tests/fixtures/hand_model/` 아래 기술자 파일 하나(`hand_model.oracle_descriptor.json`, 기본안 B-14), 그것이 sha256으로 참조하는 `gmid_pdk_decl/1` 형식 선언 파일(엔진 로더는 읽지 않는 픽스처), 손 모델 파일(면적 의존 식은 test 작성자가 쓰고 PDK 공식은 쓰지 않는다)이다. **OP-5가 만들고**(완료 조건 4a), OP-6 능력 확인과 이 절의 공정 무관 증거는 같은 파일을 재사용한다. OP-6은 새 손 모델 기술자를 만들지 않는다.
* (v0.3.0, DR-10h) 손 모델 기술자의 참조 sha256 칸은 LF 정규화 값(§10.2), 손 모델 test LUT meta의 `model_files_sha256`은 raw 값(엔진 LUT 기록과 같은 정의, §15.4 `make_lut` 행)이다. 그래야 sky130 기술자와 같은 규칙 (i)·(ii) 경로가 손 모델에서도 돈다.
* 손 모델 기술자도 `geometry_unit`·`parallel_multiplier`·`mc.distribution`을 선언한다. 그래서 §10.4·§10.6의 미선언 거부와 분포 값 출처 거부가 sky130 기술자와 같은 코드 경로로 손 모델에서도 돈다.
* 4a (ii)의 '단위만 다른 둘째 기술자'는 정본 파일이 아니라 test 안에서 정본으로부터 파생한 변형이다(깨진 변형과 같은 지위, P v0.6.2). 저장소에 둘째 파일로 두지 않는다.

### 12.8 offset-trim N3.9-3 재대조(P N3.5.1, v0.2.4)

* **기준 갱신**: 계획 N3.5.1은 offset-trim 계획 v0.5.2(`trim-plan-r1` `a293411`, 미병합) 455-462행을 기준으로 했고, 그 계획이 확정되면 다시 대조하라고 했다(OP-0 design 착수 조건). 지금 master의 offset-trim 계획은 **v0.5.6**(`86e5adc`, 2026-10-16)이고 v0.5.4에서 사용자 승인됐다(`0aac966`, T-29~T-37). N3.9-3은 **466-473행**이다(`docs/01-plan/features/offset-trim.plan.md`, base `1ba9461`에서 다시 잼).
* **대조**(master v0.5.6 N3.9-3 일곱 항목 → 이 문서):

| # | master v0.5.6 N3.9-3(요지, 행) | 이 문서 | 담김 | a293411 대비 |
|---|---|---|---|---|
| 1 | MC 불일치가 실제로 분산을 만든다(네이티브 MC). 크기 일관은 능력 기록이 아니라 TR-7 판정(467) | PC-3(§12.2), MC 게이트(§12.6) | 예 | 크기 일관을 TR-7로 옮긴 문구가 offset-trim 쪽에 이미 반영됐다. 계획 N3.5.1 1행의 '알림 항목'은 처리됨 |
| 2 | 온도 지정이 동작점을 바꾸고, 읽은 온도 = 요청 온도(468) | PC-5 | 예 | 같음 |
| 3 | **같은 seed의 네이티브 MC 표본** 정체가 온도 사이에 보존된다. 꼬리 판정(G-14)이 기댄다(469) | PC-6, `McNative.keep_identity`(§5), 어댑터 `keep_identity_across_conditions`(§8.3) | 예 | 'same seed·네이티브 MC'와 G-14 의존이 더해졌다. PC-6 정의(같은 seed, 비트 동일)와 맞는다 |
| 4 | 오라클 모델 = 엔진 LUT 모델(해시 대조)(470) | PC-7, §12.5 | 예 | 같음 |
| 5 | LUT `temp_c`와 따로 온도를 받는다(471) | PC-8, §11.1 `process.temp_c`, §11.2 | 예 | 같음 |
| 6 | 온도 점마다 V_sys(T)(472) | PC-10, §11.6 `output_reference`(v0.3.0에 §11.1에서 옮김) | 예 | 같음(G-15는 offset-trim design TR-0T가 닫음, §1.3) |
| 7 | (철회, v0.5.4) 결정적 불일치 벡터 표본 요구(PC-11)는 T-35로 필요 없음. 결정적 섭동은 진단 전용(473) | PC-11 철회(§12.2), 진단 경로 §13 | 해당 없음 | a293411의 '(G-14에서 채택하면) 결정적 벡터'가 철회로 바뀌었다 |

* 결론: 일곱 모두 이 문서 항목과 맞고, 이 문서가 바꿀 것은 없다. 계획 N3.5.1의 기준 커밋 문구(`a293411`)는 계획 소유라 이 card가 고치지 않는다(§19.2 아래 '알림').
* offset-trim N3.9 '순서 의존' 문단(master 477행)은 아직 'oracle-portability 계획은 초안(브랜치 oport-plan, 승인 전)'이라고 적는다. 그 문구는 offset-trim 소유라 고치지 않고 알림만 한다(§19.2 아래 '알림').
* (v0.4.0, **OP-B13 재대조** -- 계획 N5.1 OP-0, 기준 = 현행 offset-trim 계획 v0.6.4(master `c8ecc4e7`, N3.9-3 483-488행, 요구 여섯 + 철회 하나). 계획 문언의 'v0.6.2'는 그 뒤 v0.6.4까지 나갔고 N3.9-3 본문 차이는 이 표에서 잰 현행 문언으로 본다): (1) MC 분산 = PC-3, 크기 일관 = TR-7 -- 담김 (2) 온도 지정·읽은 온도 = PC-5 -- 담김 (3) 같은 seed 표본 정체 = PC-6·`keep_identity` -- 담김 (4) 모델 해시 = PC-7·§12.5 -- 담김 (5) LUT `temp_c`와 따로 온도 = PC-8·§11.1 -- 담김 (6) **표기 정정 V_sys(T) → V_id*(T)**: 온도 점 V_id*(T) = PC-10 = §21.4 측정을 온도 조건에서 돌린 것 하나, 기준 DEC-23(O-53 B3, G-15 닫힘) -- 담김 (7) 결정적 벡터 요구 철회 -- 해당 없음. 온도 점 전도 판정 입력은 상위 O-205로 부호 비교(§21.1 6단계)이며 N3.9-3 요구에 영향 없다. 바꿀 것 0. 계획 N3.5.1 표 기준 문구는 계획 소유(§19.2 PG-4).

---

## 13. 결정적 섭동 진단 경로(O-1 (5), 계획 N3.5)

### 13.1 입력

`oracle_run --diagnostic <파일>`로 받는다. 파일 스키마는 다음과 같다.

```
{"schema": "oracle_diagnostic/1",
 "vectors": [{"id": "...", "values": {"<소자 이름>": {"<진단 변수>": <z 값>}}}],
 "base": "nominal"}
```

* 코어가 `McDiagnostic` 요청을 만든다. 어댑터는 기술자 `diagnostic` 식(§10.5)으로 z를 변수 값으로 바꿔 소자별로 넣는다. 기하 단위·병렬 배수는 공칭과 같은 소자 줄 규칙(§10.6)으로 전달한다.
* 결과는 벡터마다 `OpTable`과 코어 MC 수학의 V_os다. `mc_math.py`의 표본 처리 함수를 네이티브 MC와 같은 함수로 지난다.

### 13.2 검증자 MC 수학 동일성(P N3.5 (ii)·N4-2 MC 칸, v0.2.5 다시 씀)

사용자 결정 O-8(계획 v0.6.3 X-19, design v0.2.4 DV-3 = (가))과 OQ-4(승인 L-3)대로 둘로 나눈다. 둘 다 검증 절차이고 게이트가 아니다(O-1 (5)). 기준선 자료는 OP-1a가 `.ai/verification/<OP-1 id>/baseline/`에 커밋한 판정용 텍스트에서만 읽는다(저장소 밖 경로·`legacy/` 접근 0, 계획 OP-1a 완료 조건).

**(가-1) 코어 MC 수학 비트 동일**(시뮬레이터를 거치지 않는다):
1. 검증자는 기준선 `offset_mc` 출력의 `seed`, `n_requested`, `a_dc_signed`와 기준선 MC 로그의 **표본별 op 값**(출력·입력 노드 전압, 표본 0 = 기준 해)을 읽는다.
2. 그 값을 새 `core/mc_math.py`의 표본 처리 함수(V_os = (V_out − V_out,0)/A − (V_id − V_id,0), §13.4 식과 같은 함수)와 σ 추정 함수에 그대로 넣는다.
3. **σ_in·mean_in**이 기준선 출력과 비트 동일이면 통과, 다르면 멈추고 보고한다. **표본별 V_os**는 아래 '기준선 표본별 V_os'와 비트 동일이면 통과다.

**기준선 표본별 V_os**(v0.2.6, 사용자 결정 O-9 = DV-5 (가), 계획 v0.6.5 N0.1 '기준선'·OP-1a (a)~(d), X-24): 기준선 출력에 표본별 V_os 칸이 없으므로(S-22) 기준값은 **검증자 재계산값**이다.
* **재구현 스크립트**(검증자 소유, OP-1a (b)): base 커밋의 옛 표본 처리 `O/oracle_offset_mc.py:166-195`(로그 `MCS` 블록 → 표본별 (V_id, V_out) → V_os,k = (V_out,k − V_out,0)/A − (V_id,k − V_id,0), σ = 표준편차 `ddof=1`, 평균)를 **줄 단위로 다시 쓴** 스크립트다. 옛 함수를 부르지 않는 이유: `offset_mc_measure`는 표본별 V_os를 반환하지 않는다(`vos`는 지역 변수, 계획 N0.1). 스크립트는 판정 기록에 원문과 sha256, 실행 기록(base 커밋 sha, 입력 로그 sha256)과 함께 둔다. 재구현 범위의 표기: 스크립트 머리에 '재구현 대상 = `<base sha>:O/oracle_offset_mc.py:166-195`'를 적고, 옛 줄과 새 줄의 대응을 주석으로 단다(독립 검증이 줄 대응을 대조할 수 있게).
* **재계산이 옛 코드와 같음의 검증**(먼저): 재계산 표본별 값으로 다시 낸 σ_in·mean_in이 기준선 출력 `sigma_in_mV`·`mean_in_mV`와 비트 동일함을 보인다. 다르면 그 값을 기준선으로 쓰지 않고 멈추고 보고한다. 이 판정은 S-22 2행을 다시 재는 것이므로, OP-1a (b)·(c)를 이 스크립트 하나로 둔다(계획 OP-1a '(b)·(c)를 한 스크립트로 둘 수 있다(design이 정함)' -- 이 문서의 결정, 기본안 B-26).
* **선택 대조**(OP-1a (d), 계획 v0.6.5 검증 메모 권장 경로): 옛 함수 `offset_mc_measure`를 기준선 로그에 돌려 그 함수가 낸 σ_in·mean_in도 기준선과 비트 동일함을 확인할 때는 **모듈 전역 이름 `run_ngspice` 교체**(`O/oracle_offset_mc.py:38`의 `from oracle_simulate import … run_ngspice`로 들어온 이름을, 저장된 로그를 돌려주는 함수로 바꿈) 경로를 쓴다. 실행 캐시 `done` 슬롯 경로(`O/oracle_simulate.py:86-98`, `:104-121`)는 쓰지 않는다: 슬롯 키가 실행 파일 경로·넷리스트·모델 묶음 sha에서 나와(`run_cache_key`) 기준선 슬롯을 다시 만들려면 그 입력을 모두 재현해야 하고, 재현이 틀리면 조용히 miss가 되어 시뮬레이터가 실제로 돈다. 이 대조는 재계산 스크립트를 대신하지 않는다(표본별 기준값은 재계산 스크립트가 낸다).
* 증거(계획 완료 조건 7): 코어 MC 수학 함수가 이 판정에서 호출된 기록.
* OP-1이 σ_in·mean_in 부분을 기준선 안에서 해 봤다(S-22 2행, 옛 코드 쪽 재계산).

**(가-2) 진단 경로 끝까지 재현**(어댑터·시뮬레이터를 지난다):
1. 검증자는 기준선 `offset_mc` 출력의 `seed`, `n_requested`, `mismatch_vars`(소자별 변수 목록)를 읽는다.
2. `numpy.random.default_rng(seed).standard_normal()`을 옛 순서(표본 → 소자(입력 `devices` 순서) → 변수)대로 불러 z를 재현한다(S-4, S-22 1행이 이 순서를 확인).
3. 같은 z를 진단 벡터(§13.1)로 `oracle_run --diagnostic`에 넣는다. 표본 0은 모두 0이다. 새 경로는 §10.5 `value_rule`(z → 변수 값)과 §10.6 기하 단위·병렬 배수 규칙으로 소자 줄을 쓴다(옛 넷리스트의 z·1e-6/√m 값·SI 기하 + `m=`와 다름, S-4·S-13).
4. **표본별 V_os**: 비트 동일이 목표다. 다르면 표본마다 |차| ≤ 그 표본의 `dc_resolution_in_V`(§13.4, N4-2 해 정확도 분해능)이어야 하고 차를 기록한다. 하나라도 넘으면 실패다. 표본별 V_os의 기준값은 (가-1)과 같은 '기준선 표본별 V_os'(검증자 재계산값)다.
5. **σ_in·mean_in은 (가-2)로 판정하지 않는다**(OQ-4): 표본 통계량은 표본별 값의 함수라 (가-2) 표본별 판정과 (가-1) 수학 비트 동일이 함께 덮는다. 값은 기록만 한다.
* 증거(계획 완료 조건 7): 진단 도구가 `oracle_run` 진단 입력에서 호출되고 이 판정 기록이 그 호출 결과를 쓴 기록.
* 옛 넷리스트 형식을 재현하는 코드는 두지 않는다(계획 N3.6 '진단 도구는 새로 쓰고 옛 코드를 옮기지 않는다').
* OP-1a 보관 목록의 소비처(이 절): 기준선 `offset_mc` 출력 JSON, 기준선 MC 로그(표본별 op 값), 그 입력 JSON(`devices` 순서·`n_fingers`). 목록 확정은 OP-1a다.

* MC 칸(`sigma_in_mV`, `mean_in_mV` 등)의 N4 동일성 처리는 계획 N4-2 MC 칸 그대로다: 네이티브 MC 표본열이 기준선과 달라 동일성 판정에서 빼고 차와 표준오차를 기록만 한다(X-17). MC 이산 칸(`status`, 사유)은 정확 일치다.
* (v0.3.0 다시 씀, 계획 OQ-6 = 사용자 결정 O-43 D1 (d)) 차동 이득 A는 `.ac` 첫 점과 `1e-3` 실수 판정이 아니라 **`.tf`(servo를 연 개루프 벤치)**로 잰다(§21.5). (가-1)은 코어 MC 수학 함수(A를 인자로 받음)의 비트 동일이라 **기준선의 A**(`a_dc_signed`)를 넣고, 그래서 A 출처 변경과 무관하게 유지된다. A·σ 값 자체는 정의를 바꾼 칸이라 N4 0번 동작 변경 기준(손 회로 test + 검증자 원인 변화표)이다. MC 이산 칸 `status`·사유도 A 출처 변경 때문에 바뀌는 입력(옛 `1e-3`으로 `unavailable`이던 것 -- S-14의 24건)은 원인 변화표에 그 원인으로 적는다(동일성 대상에서 그 원인으로 바뀐 칸만 뺀다, 계획 N4-2 '정의를 바꾼 칸').

### 13.3 TR-7 사용

offset-trim TR-7 §17-1에서 엔진 σ_in과 오라클 네이티브 MC σ_in이 어긋나면, 같은 진단 경로로 소자·변수별 결정적 기여를 재서 원인을 가른다. 결과는 진단 보고에만 실린다.

### 13.4 DC 풀이 허용오차의 입력 환산 전파(T-39, `core/mc_math.py`)

* 오라클이 내는 입력 환산 offset은 V_os = (V_out − V_out,ref)/A − (V_id − V_id,ref)다(S-4의 식. V_sys는 기준 표본 쪽 항).
* 각 노드 전압의 DC 풀이 오차 한계는 그 실행 `Resolution`의 reltol·|V| + vntol이다. 이것을 V_os 식에 1차로 전파한다:
  δV_os = (δV_out + δV_out,ref)/|A| + δV_id + δV_id,ref, 여기서 δV = reltol·|V| + vntol.
  차동 전압은 두 노드 오차의 합이다. A는 결정적 값이고 1차 전파에서 뺀다. 이 근사는 결과에 표시한다.
* 결과의 표본마다(그리고 V_sys(T)마다) `dc_resolution_in_V`로 싣는다. offset-trim의 trim 잔여 수렴 분해능은 이 값을 쓴다(T-39, offset-trim design §20.6). 새 상수는 없고, 값은 선언된 허용오차와 측정 전압에서만 나온다.

---

## 14. 옛 리터럴 상수 처리(계획이 정한 것과 정하지 않은 것)

| 상수 | 계획 | 이 문서 |
|---|---|---|
| `_NGSPICE_DEFAULT_TOL` | 어댑터 보정값으로(P N3.6) | `calibration.json` `default_tolerances`, 출처 = 시뮬레이터 문서 기본값. 문서 쪽수는 OP-0 원문 보관 뒤 채움(P R6). **출처가 채워지기 전에는 선언값으로 쓰지 않는다**(§8.3, T-39 숨은 상수 금지). 그동안은 입력 `simulator.options`에 허용오차가 있어야 실행된다. (v0.2.5, S-28) 옛 값은 reltol·vntol 둘뿐이라 옮기는 것도 그 둘이다. abstol은 옮길 옛 값이 없고 같은 원문에서 값·쪽을 처음 적는다 |
| `WRDATA_NUMDGT = 8` | 어댑터 보정값(P N3.3) | `calibration.json` `data_digits`, 출처 = 코드 주석의 ngspice-46 실측 |
| 차동 이득 실수 판정 상대 폭 `1e-3`(`|Im h0| ≤ 1e-3·|h0|`, `O/oracle_offset_mc.py:137`) | (v0.6.9 아홉째 커밋, 사용자 결정 O-43 D1 (d)) **삭제**: A를 `.tf`로 직접 재므로 상수와 `.ac` 첫 점 경로를 지운다(계획 N3.6 삭제 목록, NFR-P2 예외 목록에서 빠짐) | (v0.3.0 고침) **삭제**(OP-5, §15.1). v0.2.4~v0.2.6의 '값·동작 그대로 `core/mc_math.py`로 이동'은 철회했다(경위 history H6) |
| (v0.4.0 **삭제 -- 계획 OP-4·OP-5 행 OP-B1**) 옛 `NYQUIST_K_MAX = 10`, `NOISE_TOP_K_MAX = 8`, `INTEGRAL_K_MAX = 4`, `ZOOM_POINTS = 7`, `ZOOM_ROUNDS = 8` | 분해능에서 유도, NFR-P2 예외 목록에서 빠짐(X-D1) | 상한 식 = §18.3 끝, `ZOOM_POINTS` 몫 = 어댑터 능력 `sweep_points_per_round`(§8.3). 완료 측정 = 이름 `git grep` 0, 상한 도달 toy마다 fail-closed 사유, N4 비교(상한에 닿지 않은 기준선 입력은 비트 동일, 닿은 입력 = 정의를 바꾼 칸). 옛 행 history H 표기는 v0.3.x 판 그대로 |
| `_K_B`, `_Q_E` | -- | 물리 상수(CODATA), 그대로 둔다(V_T = kT/q 격자 간격도 이 물리 상수에서 나온다) |

* (v0.4.0) 감사(완료 조건 9 gap 분석 포함)는 리터럴 판정 상수를 0으로 본다(옛 예외 다섯은 OP-4·OP-5 병합으로 사라짐 -- 그 전까지만 옛 상수). 물리 상수(`_K_B`, `_Q_E`)와 어댑터 보정값(출처 칸 있음)은 판정 상수 목록에 들지 않는다.

---

## 15. 삭제 목록과 대체 배선표

### 15.1 오라클 본체

(v0.4.8, A-80 D-1) OP-3이 지우는 이름을 OP-4·OP-5 몫 코드가 읽어도 다리 코드를 두지 않는다. 그 코드는 그 card가 옮길 때까지 호출자 없이 파일에 남는다(§20 OP-3 행 '기간 동작').

| 옛 것 | 새 것(배선 위치) | 삭제 card |
|---|---|---|
| `oracle_netlist.build_netlist` 텍스트 생성 | `core/build_circuit.circuit_ir` + `main_requests` → 어댑터 `dialect` (`oracle_run`이 호출) | OP-3 |
| (v0.4.0, OP-3, OP-B3) `oracle_netlist`의 게이트 전용 넷 예측 노드전압 이상 전압원 대체·경고 경로 | §11.2 1d 거부(`bias_gate_nets_mismatch`), 대체 갈래 `git grep` 0 | OP-3 |
| `parse_netlist_elements` | `core/identity.py`(IR 대조) | OP-3 |
| `_Nets` 대소문자 규칙 | `core/ir` 충돌 검사(§4.1) | OP-3 |
| `probe_name`, `device_line`, `_includes`, `OP_PARAMS` 이름 표 | 어댑터 `dialect`·`read`(기술자 `model_family`) | OP-3 |
| `run_ngspice`, `run_cache_key`, `_model_files`, `_INC` | 어댑터 `run`, `model_bundle` + `core/cache.py` | OP-3 |
| `parse_op`, `parse_ac_file`, `_cols`, `_grab` | 어댑터 `read` | OP-3 |
| `oracle_compare.signed_id` | 어댑터 `read`(극성 정규화) | OP-3 |
| `stability_control`, `stability_netlist`, `stability_op_netlist`, `open_loop_parts`, `pz_netlist`, `openloop_tran_netlist` | `core/build_benches` + 어댑터 `dialect`(조기 종결은 능력) | OP-4 |
| `_refine_text`, `refine_samples` | 같은 IR에 좁은 `Ac` 재요청(`core/stability.nyquist_adaptive`가 호출) | OP-4 |
| `pz_poles`, `_PZ_POLE` | 어댑터 `read` → `Poles` | OP-4 |
| `oracle_config.json` | 어댑터 `calibration.json` | OP-4 |
| `_NGSPICE_DEFAULT_TOL`, `WRDATA_NUMDGT` | 어댑터 `calibration.json` | OP-4 |
| `oracle_noise._hexpr`, `_first_vac`, `_body`, `_VEC`, `_MOS`, `_RES`, `parse_noise_totals` | `Noise` 요청 + 어댑터 `read`(기여 이름 → IR 소자, 기술자 `inner_device`) | OP-5 |
| `oracle_offset_mc.mismatch_vars`, `build_mc_netlist`, z·1e-6/√m 배율, `"Lfb_" not in text` 검사, `--ngspice` 필수 인자 | 네이티브 MC(`McNative`) + 진단 경로(`McDiagnostic`) + `core/mc_math`. servo 유무는 IR 역할 표로 본다 | OP-5 |
| (v0.3.0) `oracle_offset_mc`의 A 경로: `.ac` 첫 점 읽기(`parse_ac_file(...)`·`h0`, `O/oracle_offset_mc.py:130-136`)와 `1e-3` 실수 판정(`:137-140`) | `.tf` 개루프 벤치(§21.5, `core/measures_dc` + 어댑터 `Tf`) | OP-5(계획 OQ-6, 완료 조건 6·10: 두 경로 grep 0) |
| (v0.3.0) `oracle_swing`의 servo 출력 목표 훑기(`mk_se`·`mk_d`, `O/oracle_swing.py:270-299`)와 ICMR 출력 servo 고정(`mk_icm`, `:222-228`), '수렴 안 함 = 포화 아님'(`sat_violation`의 결과 없음 → 거짓, `:120-121, :133`), 전도 문턱 `abs(idv) <= off_i`(`:134`), 차동 입력 없으면 ICMR `unavailable`(`:232-233`) | §21.2 훑기(servo 없는 여기 방향 입력 훑기, 출력 자유) + §21.1 판정 점 전도·포화 + 수렴 실패 = 측정 거부(`sweep_point_unconverged`) + 단일 입력 일반형 | OP-5 |
| (v0.3.0) `oracle_compare`의 ε = 1 전도 판정(`thr = p.get("off_current_A") … else off_i`, `O/oracle_compare.py:242-244, :278-280`)과 `merge_judge`의 `off_current_A`(`:113-118`), 진입점 `oracle_run`이 swing에 넘기는 `off_current_A`(`O/oracle_run.py:50-51`) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** §21.3 합격 판정 봉인 9 식 + §21.1 두 단계 | OP-5(입력 칸 `predictions.devices.*.off_current_A`·`judge.off_current_A` 삭제와 같은 변경, B-34) |
| (v0.3.0) `oracle_compare`의 C25 `TRANSIENT_MEASURES`·`TRANSIENT_NOT_MEASURED_REASON` 가운데 `slew_rate_v_per_s`(`O/oracle_compare.py:85-90, :148`) | §21.6 슬루 측정(`settle_s`는 '정의 미정' 그대로) | OP-10 |
| (v0.2.4) `oracle_compare.py:379` 메시지 `"ngspice .op 결과 없음: "` | 시뮬레이터 이름·방언 토큰 없는 메시지(예: '시뮬레이터 동작점 결과 없음: '). 어댑터 이름이 필요하면 결과의 어댑터 지문에서 읽는다(토큰 초안 D9 open point) | OP-3(compare 코어 이동) |
| (v0.2.4) `oracle_compare.py:708` 메시지 조각 `' V, ngspice '`와 키 `'ngspice_runs'`, 생산자 `oracle_swing.py:306`, 소비자 `smoke/u6_selfchecks.py:136` | 메시지 '시뮬레이터 실행 {n} 회', 키 `sim_runs`(§11.5 결과 칸 대응). 생산자와 compare 소비자를 같은 변경에서 바꾼다. (v0.2.6 재검증 경미 3) 소비자 `smoke/u6_selfchecks.py:136`은 이 card보다 앞선 OP-3에서 스크립트째 삭제되므로(§15.4, O-10) OP-5 시점에는 없다 | OP-5(swing 이전) |
| (v0.2.4) 결과 칸 `ngspice_rc`(생산자 10곳, S-23) | 같은 자리의 `status`(`RunStatus`, §6). 경로별 대응·`None` 처리 = §11.5 표. 소비자 `test_oracle_c10_stability.py:1364, :1371`·README 4줄을 같은 변경에서 | 경로별(§11.5 '바꾸는 card' 칸): 본 회로·β 루프·CM 루프 OP-3, 안정성 넷(op_pass·과도·연장·pz·pz 확인) OP-4, noise·offset_mc OP-5 |
| (v0.2.5) 결과 `method` 값의 시뮬레이터 이름(S-24) | 어댑터 `ResultBundle.method`(§6) | pz OP-4, noise·offset_mc OP-5 |
| `oracle_compare.py:38`(모듈 docstring)·`:228`(`signed_id` docstring)의 시뮬레이터 이름 | `:228`은 `signed_id`와 함께 어댑터 `read.py`로 간다. `:38` '크기 규칙' 설명은 극성 정규화 규칙(어댑터 공통)으로 다시 쓰고 시뮬레이터 이름은 '사례'로만 남긴다(docstring은 T1-1 검사 밖이지만 P NFR-P1 이름 원칙) | OP-3 |
| `oracle_swing._Sweeper`, `_control_block`, `_src_lines` | `OpSweep` 요청 + `core/swing_math` | OP-5 |
| 스키마 `process.models`, `process.ngspice_exe`, `process.diffusion`, `process.lut_npz`, `testbench.options` | §11.1(새 형식 `spice_oracle_input/2`), 옛 형식 거부 §11.2 1b | **OP-3**(v0.3.0, DR-10i -- 사용자 결정 O-14 (4) J-1 (나): 입력 형식 전환·옛 형식 거부는 OP-3, OP-2는 기술자·스키마·읽기 코드만. 따로 검토·함께 병합, 계획 X-28) |
| `legacy_adapter.process_from_lut_generator` | (v0.2.5) 대체 없음: 파일째 삭제(생산자 0, §11.4) | **이 기능의 card 아님** -- gain-budget card LT-1 순서 3. 완료 조건 6(삭제 이름 grep 0)의 이 항목은 LT-1 순서 3 병합에 의존한다(계획 N5.3-6) |
| CLI `--ngspice` | `--simulator`, `--sim-exe`(§11.7) | OP-3(v0.3.0, DR-10i: 입력 형식 전환과 같은 변경) |
| 진입점 `oracle_netlist.main`·`oracle_simulate.main`·`oracle_noise.main`·`oracle_offset_mc.main`·`oracle_swing.main`·`oracle_compare.main` | `oracle_run` 하위 명령(§3.1 기본안) | 각 모듈 삭제 card |
| (v0.2.5) `oracle_compare.py`의 measure 키 표(`MEASURES`·`U6_MEASURES`, 엔진 test가 소스 텍스트로 읽음, S-26) | `core/compare.py`로 이동하면 엔진 test `E/tests/metrics/test_verified_by.py:62-65`의 glob(`O/oracle_*.py`)이 키를 못 찾는다 | (v0.2.6) DV-4 = O-9 (가)로 닫힘: 같은 변경(OP-3)에서 엔진 test 작성자가 `:64` glob 한 줄을 `(ORACLE / "core").rglob("*.py")`로 바꾼다(계획 8a 예외 둘째, §18.1) | OP-3 |

### 15.2 남는 수학의 이동(부분 수정, 함수 이름 유지)

`ac_measures`, `pm_crosscheck`, `loop_gain`, `loop_probe_singular`, `ratio_measure`·`rout_measure` 수학부, `loop_choke_ratio`, `nyquist_count`, `gain_crossings`, `low_side_gain_margin`, `thermal_voltage`, `solver_floor`, `reltol_of`, `n_pp_of`, `band_f_crit`, `tran_plan` 수학, `g_up`·`g_down`·`growth_window`·`limit_cycle_window`·`early_window`·`early_unstable`·`limit_cycle_early`·`window_ratios`, `transient_decision`(파일 대신 `TimeSeries` 입력), `extension_plan`, `final_transient_status`, `pz_rhp_count`, `nyquist_adaptive`, `stability_judgement`, `data_rel_resolution`·`mp_resolution`(입력 = `Resolution`), `sample_count`, `sat_violation`, `_window`, `oracle_compare`의 판정·markdown 함수 전부.

### 15.3 생성기(D-2, OP-8)

* 새 생성기는 새 파일(`A/` 아래, 이름에 PDK 없음)이다. 같은 어댑터와 기술자를 쓰고, LUT 메타에 어댑터 지문·기술자 지문·bin 경계 측정(§16)을 쓴다.
* (v0.3.0, DR-12, 계획 OP-8 선행·O-16 (1)) **선행**: gain-budget v6.17 엔진 sha256 정본 card SH-1(LF 정규화, 옛 U-1을 합침). 새 LUT meta의 모델 파일 sha256 기록 정의(`model_files_sha256`, 새 칸 `model_files_role`)는 그 card가 정한 형식을 따른다(이 문서가 따로 정하지 않음). 그 card 뒤 새 LUT 기록이 정규화 값이면 기계 무관이다(계획 X-27 (2)).
* 옛 `A/sky130_lut_sweep.py`·`A/sky130_pair_mc.py`는 출처 보존본으로 남긴다. 엔진 `sky130_lut_rule_decl.json`이 sha256으로 묶고 있기 때문이다(P X-10).
* 실행 경로 없음은 저장소 전체 grep 0으로 보인다. 대상은 모듈 이름 import, `runpy`, `subprocess` 인자, 경로 문자열이다. 엔진 선언 `sources` 칸과 문서 인용은 예외다.

### 15.4 삭제 모듈의 소비자(v0.2.5, 검증 M-4, 근거 S-25·S-26·S-27)

모듈을 지우는 card는 그 모듈의 소비자를 **같은 변경에서** 처리한다(P FR-P8, NFR-P4). 처리하지 않으면 그 card의 '삭제 이름 grep 0'(완료 조건 6)이 실패하고, 스크립트는 조용히 깨진 채 남는다.

| 소비자 | 쓰는 것 | 처리(기본안 B-20) | card |
|---|---|---|---|
| `O/smoke/cm_loop_mixed_cut_example.py:28`, `cm_loop_variants.py:28` | `oracle_simulate.ac_measures`, `loop_gain` | import를 `core/measures_ac`(함수 이름 유지, §15.2)로 바꾼다. `loop_gain`이 파일 경로 대신 정규화 결과(`FreqSeries`)를 받게 되면, 루프 데이터 파일 읽기는 어댑터 `read`를 거친다. 스크립트가 엔진을 import하는 것은 그대로다(오라클 코어가 아니라 기록 스크립트) | OP-3 |
| `O/smoke/cm_loop_engine_vs_ngspice.py:104, :115` | 같음(함수 안 import) | 같음. 파일 이름은 '둠'(측정 기록의 이름, 계획 N3.7 분류 규칙) | OP-3 |
| `O/smoke/u6_selfchecks.py:25-26`(`tests/conftest` import), `:28-32`, `:44, :52, :54, :66-67, :84`(conftest 옛 형식 입력 생성기), `:98, :107`, `:136` | 옛 다섯 모듈 전부, conftest 입력 생성기(`process_block`, `testbench_block`, `zero_diffusion`, `make_lut`, `rc_input`, `RC`, `NGSPICE`), 직접 섭동 경로(`mismatch_vars`, `build_mc_netlist`), 결과 칸 `ngspice_runs` | **삭제한다(사용자 승인 O-10).** 기록 문서 `O/smoke/U6_REPORT.md`는 남긴다(기록). 점검 내용(잡음 RC 손계산, MC 대 결정적 섭동 감도 RSS, 스윙 창, pz 극점)은 새 test로 다시 쓴다: pz 극점 → 어댑터 pz test(OP-4), 잡음 손계산 → 코어 noise test(stub, OP-5), MC 대 결정적 섭동 → 네이티브 MC 대 진단 경로(§13, OP-5), 스윙 → `OpSweep` 어댑터 test(OP-5)(§18.2). 이 스크립트가 정의한 회로는 기준선 입력 묶음(계획 N4-1)에 이미 들어 있다. (v0.2.6 고침) 삭제 card는 **OP-3**이다: 이 스크립트가 import하는 `oracle_netlist`·`oracle_simulate`의 실행 경로를 처음 지우는 card가 OP-3이고(§15.1), (v0.3.0) conftest 생성기의 새 형식 전환도 OP-3이라(DR-10i) 이 스크립트는 OP-3 전까지 옛 형식 그대로 돌고 OP-3에서 지워진다. OP-3~OP-5 사이에는 이 점검이 없다(기록 스크립트라 판정 공백은 아니고, 점검마다 다시 쓰는 card가 위와 같다) | OP-3(삭제), OP-4·OP-5(다시 쓴 test) |
| `O/smoke/measure_wall_s_per_window.py` | import 없음. 방언 실행(`-b`)과 `STABWIN` 줄 수 | `O/adapters/ngspice/calibration_tools/`로 옮기고(어댑터 지문 밖, §0·§3.1, 기본안 B-25) `oracle_config.json` 언급을 `calibration.json`으로 바꾼다(창당 상한 보정값의 출처 도구) | OP-4 |
| (v0.2.6) `O/tests/conftest.py`의 옛 형식 입력 생성기 `process_block`(`:71-90`), `testbench_block`(`:105-109`, `testbench.options`), 그 둘을 쓰는 `cs_input`·`rc_input`·`fb_input`(S-34) | `process.models`·`op_probe`·`process.diffusion`·`testbench.options`(옛 형식) | 새 형식(`schema` = `spice_oracle_input/2`, `process.descriptor` + `process.lut_files` + `simulator{adapter, exe, options}`, §11.1)으로 다시 쓴다. 함수 이름·인자는 그대로 두어 호출 183곳(S-34)은 바꾸지 않는다. 기술자는 test 픽스처 기술자(stub용 SI 기술자, §3.3)와 첫 조합 기술자를 인자로 고른다. 주체 = test 작성자(픽스처) | **OP-3**(v0.3.0, DR-10i: 옛 형식 거부가 들어오는 card가 OP-3으로 바뀜 -- O-14 (4) J-1 (나)) |
| (v0.2.6) `O/tests/conftest.py`의 `make_lut`(`:60-68`, meta에 `model_files_sha256` 없음, S-34) | 공칭 자동 대조(§12.5)의 LUT 기록 | 자동 대조가 배선되면 기록 없는 LUT는 `lut_model_provenance_missing`으로 거부되므로, test 기술자와 맞는 `model_files_sha256`(그리고 필요하면 `model_files_role`)을 meta에 쓰게 고친다. 기록을 일부러 빼는 변형은 거부 test로만 쓴다. 주체 = test 작성자. (v0.3.0, DR-10h) test LUT meta에 적는 기록 값의 정의 = 손 모델·test 모델 파일 바이트의 **raw** sha256(엔진 LUT 기록과 같은 정의 -- 오라클 규칙 (ii)를 test가 그대로 지나게). 기계 의존 표시를 시험하는 test는 CRLF 바이트로 만든 파일을 쓴다 | OP-3(자동 대조 배선 card) |
| `O/tests/conftest.py:36-51`(`--run-legacy`, `legacy_slow`) | 옛 엔진 test 장치 | 이 기능의 card가 아니라 gain-budget LT-1 순서 3이 지운다(S-27, 계획 LT-1 순서 3 '`--run-legacy`(conftest 마커 포함) 삭제') | LT-1 순서 3 |
| `O/tests/conftest.py`의 `run_spice`·`independent_cs/fb` | 손 넷리스트 독립 기준 | §18.2대로 `O/tests/adapters/ngspice/` 아래로 옮긴다(삭제하지 않음, v0.2.6 경로 명시) | OP-3 |
| `E/tests/metrics/test_verified_by.py:62-65` | 최상위 `O/oracle_*.py` 소스 텍스트의 measure 키(S-26) | (v0.2.6) `:64` glob 한 줄을 `(ORACLE / "core").rglob("*.py")`로(O-9, 계획 8a 예외 둘째). `O/**/*.py`로 넓히지 않는다(test·smoke 문자열이 판정을 대신함, 계획 8a) | OP-3(엔진 test 작성자) |

---

## 16. bin 경계 규칙 선언(D-4, G-14, OP-7)

* 정본은 LUT 생성 실행에 묶은 선언 하나다. 묶는 대상은 (LUT가 쓴 모델 파일 sha256 묶음, 생성 시뮬레이터 판)이고, **선언 키** = (시뮬레이터 판, 호환 모드(`.spiceinit` 내용 포함), 모델 파일 sha256)(v0.4.0 -- 계획 OP-7 행, 상위 DEC-105 (2): 경계값 소속이 호환 모드에 따라 뒤집힌다 -- ngspice-46 기본 모드 아래 bin, `set ngbehavior=hsa` 위 bin, 상위 검증 3 V3-1).
* (v0.3.0, DR-10g, 계획 N3.4 'sha256 정의') **묶음 값의 정의**: 새 선언(검증자 옆 선언·OP-8 새 LUT meta)이 적는 `model_files_sha256` 묶음은 LF 정규화 값이다(규칙 (i) -- 모델 파일은 텍스트). 엔진이 세트 meta의 옛 raw 기록과 이 선언을 대조할 때는 규칙 (ii)(LF 또는 raw로 맞으면 같은 파일, raw만이면 기계 의존)를 쓴다 -- 엔진 쪽 구현은 상위 card WB-1과 gain-budget SH-1의 정의(같은 규칙, 계획 N3.7 U-1 (b))를 따른다. 정의가 다른 두 기록값을 서로 견주지 않는다(규칙 (iii)). (v0.4.3, 위임 A-54) 기존 LUT 옆 선언의 묶음 값 = 그 LUT 세트 기록 값 전부(생성 보조 입력 포함)의 LF 값이다. 아래 적용 규칙이 '세트 meta 값 집합 ⊆ 선언 집합'이라 보조 입력을 빼면 폭 슬라이스 32개에 선언이 적용되지 않는다(S-29). (v0.4.4 정정) 결합 파일 6개도 중첩 안에 기록한다: 38/38(`m2_m3_lut_meta.jsonl`). 32는 평탄 표만 센 값. 모델이 바뀌면 그 값이 빠져 거부되므로 넓어져도 fail-open이 아니다.
* 형식: 저장소 파일 `A/lut_v2_bin_rule.json` 하나(v0.4.3, 위임 A-54 -- 계획 N4-2a 예외. 적용은 sha256·판으로 묶으므로 LUT 폴더와 무관, 둘째 자리 금지) =
  ```
  {"schema": "lut_bin_rule/1", "model_files_sha256": [...], "simulator": {"name", "version"}, "compat": {"mode", "spiceinit_text", "spiceinit_sha256"},
   "rule": "lower" | "upper", "evidence": {"points": [{"L", "W", "chosen_bin"}], "mode", "source_basis": "generator_record", "measured_by", "date"}}
  ```
  (v0.4.7, 위임 A-75) `evidence.source_basis`의 값은 `"generator_record"` 하나이고 뜻은 '출처 = 생성기 자기 기록, 값으로 독립 판별 불가'다. 엔진은 이 칸을 판정에 읽지 않는다. 새 생성기는 LUT 메타에 같은 칸(`bin_rule` 객체, 위와 같은 스키마)을 쓴다(OP-8). 새 메타의 시뮬레이터 칸 이름은 `simulator.name`·`simulator.version`이고 시뮬레이터 이름을 칸 이름에 넣지 않는다(옛 메타 칸 `ngspice`·`ngspice_exe`, S-15, 은 기존 LUT에 그대로 남는다).
* **묶는 LUT 범위**(P G-14, v0.2.4): 선언 하나는 (모델 파일 sha256 집합, 생성 시뮬레이터 이름·판) 한 쌍에 묶이고 LUT 파일 sha256에는 묶이지 않는다(계획 기본 방향). 엔진은 L·W bin 소속을 쓰는 세트(기준 슬라이스, cap, noise, mismatch)마다 그 세트 메타의 `model_files_sha256` 값 집합이 선언 `model_files_sha256` 집합에 포함되고 세트의 생성 시뮬레이터 판이 선언 판과 같을 때만 그 선언을 적용한다. 그래서 같은 모델로 일부 세트만 다시 만들어도 선언이 그대로 맞고, 모델이나 판이 다른 세트가 하나라도 있으면 LUT 적재가 거부된다(`bin_tie_undeclared`, P D-4, v0.4.6 상위 위임 A-62 D2).
  * 세트의 판 기록 위치(base `1ba9461`에서 다시 잼): 기준 슬라이스는 meta(S-15, 기록 있음), noise 세트는 meta 계약 `E/lut/CONTRACT.md:887`, mismatch 세트는 `:951`('ngspice 버전' 칸). 계획 G-14는 base `d783efe`의 881·945행을 'cap·noise'로 적었고, 그 뒤 CONTRACT가 바뀌어(`be2d6b6`, `b105b65` 등) 행이 옮겨졌다. cap 세트의 판 기록 유무는 OP-7 착수 때 검증자가 잰다. 기록이 없는 세트에는 선언을 적용하지 않는다(fail-closed).
* 엔진 읽기: 상위 gain-budget card WB-1 범위 0이 `E/lut/_helpers_bins.py`에서 이 파일을 읽는다(엔진 변경은 그 card -- 계획 v0.6.19부터 OP-7은 엔진 파일을 고치지 않는다). 오라클 능력 기록·오라클 코드 지문은 읽지 않는다.
* **측정 상태**: (a) 지금 LUT 기준 슬라이스 meta의 생성 시뮬레이터 판 기록 -- **측정됨**(OP-1 (iii), S-15: 38 슬라이스 모두 `ngspice-46`, 모델 파일 sha256 원본 일치). 그래서 기존 LUT 옆 선언의 판 값은 이 meta 기록을 출처로 적는다. (b) 지금 LUT의 경계 앵커 점에서 시뮬레이터가 고른 bin -- **측정 대기**(OP-7 검증자). (c) (v0.4.3) 모델 bin 표의 W 경계에서 고른 bin, (d) (v0.4.7) 동률 칸의 생성기 기록 bin 이름이 어느 모드를 가리키는지 -- **측정 대기**(OP-7 검증자).
* (v0.4.0, **OP-7 범위 -- 계획 OP-7 행**) **writer** = LUT 생성 기록: 새 LUT = 생성 실행 meta(OP-8 -- 생성 설정의 호환 모드로 실행하고 그 모드를 meta에 씀), 기존 LUT = 옆 선언 `A/lut_v2_bin_rule.json`(이 card, 검증자가 **지금 공유 LUT의 L 축 bin 경계 앵커 점 전부**와 (v0.4.3) **모델 bin 표의 W 경계 전부**(kind마다 그 bin 안 L 하나)에서 그 LUT를 만든 시뮬레이터 판으로 다시 잼 -- `E/lut/CONTRACT.md:432-435`의 384/384는 옛 격자 측정이라 근거 아님; 측정에 쓴 모드를 `evidence.mode`에 씀, `compat.mode`와 같다. (v0.4.3) L·W 방향이 갈리면 선언을 쓰지 않는다. (v0.4.7, 위임 A-75) **LUT 생성 모드 출처 = 생성기 자기 기록**: 폭 슬라이스의 동률 칸마다 meta `model_bin_per_L`의 기록 bin 이름을 같은 (L, W)의 두 모드 측정 bin 이름과 대조한다. 이름 비교이고 문턱이 없다. 각 칸의 기록은 한 모드와만 같아야 하고, 모든 칸이 같은 모드를 가리켜야 하며, 그 모드가 `compat.mode`여야 한다. 동률 칸 없음(`source_no_tie_cell`), 기록 칸 없음·꼴 다름(`source_record_missing`), 측정 없음(`source_cell_unmeasured`), 두 모드 다 가리킴(`source_record_both_modes`), 어느 모드도 안 가리킴(`source_record_no_mode`), 칸마다 다름(`source_record_mixed`), 선언 모드와 다름(`source_mode_differs`)이면 선언을 쓰지 않는다. LUT 값 대조 시뮬레이션은 하지 않는다. (v0.4.5) 포함 파일 = 결합 세트 생성기의 include 목록(엔진 밖 사실 `A/sky130_lut_sweep.py:220-228` `model_includes`). 재귀로 닿는 파일마다 LF·raw 중 하나가 그 슬라이스 기록 값에 있어야 한다(포함 파일 ⊆ 기록, (v0.4.7) 어기면 `include_not_recorded`). 기록에만 있는 파일은 `source_modes.jsonl`에 적고 역할은 여기서 정하지 않는다. (v0.4.7) 결합 세트는 meta `model_bin_per_L_at_w_ref`의 `model`을 본 측정 (L, 기준 폭) bin과 대조하고(`combined_bin_missing`·`combined_bin_unparsed`·`combined_bin_unmeasured`·`combined_bin_differs`), noise·mismatch는 meta `cap_npz_sha256`을 위치 선언 `files.cap_npz.sha256`과 대조한다(`cap_bind_missing`·`cap_bind_differs`). 이 대조는 측정 스크립트의 필수 단계이고 하나라도 멈추면 선언을 쓰지 않는다). 측정 스크립트는 `oracle_run`을 지나지 않고 호환 모드를 직접 준다. 이 기록 조각은 OP-0 G-14 형식 뒤·OP-3 전·WB-1 앞이라 어댑터가 없을 수 있다(A-13 -- 측정 방법 = 넷리스트 직접 실행 + 시뮬레이터가 고른 bin 읽기(사례 ngspice `showmod`), 빈 실행 폴더·격리 홈, 아직 실행 안 함; 재측정이 안 되면 선언을 쓰지 않고 멈추고 보고). **reader** = 엔진 bin 판정(WB-1 범위 0)·오라클 어댑터 실행 설정(이 card 배선 -- writer와 첫 reader가 한 card)·상위 CPG-1 bench(둘째 정본 금지).
* (v0.4.0) **오라클 배선**: `oracle_run`은 §7.2 8b단계에서 입력 LUT의 모델 묶음·시뮬레이터 판으로 선언을 찾는다(엔진 판정을 입력으로 받지 않음 -- NFR-P3과 충돌 없음). (v0.4.9, A-84 B-1·B-2) 파일 자리 = 기술자 `bin_rule_decl`. 포함 판정 = 입력 LUT 모델 기록의 파일 전부를 기록 뿌리 아래에서 다시 잰 LF 값 집합 ⊆ 선언 `model_files_sha256`. 기록값을 선언값과 직접 견주지 않는다(규칙 (iii), 기록 raw 대 선언 LF). 판 = 어댑터 `sim_version`이 `<name>-<version>`과 같음. 없으면 `bin_rule_undeclared`. 찾으면 어댑터 `run(..., compat = 선언 compat)`(§8.1)으로 실행하고, 어댑터는 실행 폴더에 `spiceinit_text`를 그대로 쓰고 그 sha256을 결과 `fingerprints.compat_sha256`에 싣는다(사례 ngspice: 실행 cwd의 `.spiceinit` -- 호환 모드 설정은 어댑터 안, 코어는 이름을 모름). 어댑터 `compat_modes`에 없거나 sha256이 다르면 `bin_rule_compat_mismatch`. (v0.4.9) 실행 뒤 로그가 보인 모드가 선언과 달라도 같은 코드이고 그 벤치 결과를 쓰지 않는다. 대상 = EO-1·CL-1 판정, library 회로 넷리스트 판정, CPG-1(모두 `oracle_run` 경유). **대상 밖** = 선언의 writer 실행(OP-8 LUT 생성, 옆 선언 측정)과 LUT·엔진 결과를 쓰지 않는 MC 생성 실행 -- 이 둘은 `oracle_run`이 아닌 도구 진입점이다. **홈 폴더 `.spiceinit`**: (v0.4.9, A-84 B-3, F-22 측정 -- 계획 history 0.6.31 행) 어댑터는 실행 폴더 설정 파일을 언제나 쓴다(§8.1). 사례 ngspice에서 실행 폴더 파일은 빈 파일이어도 홈·사용자 초기화 폴더 설정을 막는다. 환경 변수 덮기는 두지 않는다.
* (v0.4.0) **EO-1 순서**(d_questions §5.2 권고): 판정 실행은 OP-7 없으면 위 규칙으로 거부되므로 OP-7 → EO-1 판정 순서가 저절로 강제된다(병합 순서 표에 쌍을 더하지 않음, 계획 표지는 첫 단계 계획 개정 몫 -- PG-3).
* (v0.4.0) **완료 측정**: 선언 없음 toy → `bin_rule_undeclared`, 호환 모드 다른 toy → `bin_rule_compat_mismatch`, writer 실행 toy → 거부 아님, 추가 기준선 공칭 입력 1회 동일(이 card, O-232), library 13회로 오라클 판정 결과 비트 동일(지금 실행 모드 = 선언 기본값이라 바뀌지 않아야 함 -- 검증자; v0.4.9, A-84 B-4: 입력 생산자 EO-1 뒤라 LA-1 측정 시점, 통과로 세지 않음), `_helpers_bins.py` 변경 0(`git diff`), 모드만 다른 두 실행의 캐시 키가 다름(§9).

---

## 17. 상위 문서 개정 문안(P N3.7)

* 아래는 **문안**이다. 반영은 상위 계획 개정 절차(독립 검증 → 사용자 승인)를 거친다(S-7). 이 card는 상위 문서를 고치지 않는다.
* (v0.2.4) 상위 계획·design 40·C10 계약 개정은 별도 card `gb-oracle-rev`로 master에 병합됐다(`b105b65`). 이 절은 그 card의 입력 문안 기록으로 남긴다. 그 card는 `O/README.md`(2줄)·`E/lut/CONTRACT.md`(1줄)에도 줄을 더했다(`git show --stat b105b65`). §17.4의 README 3층 재작성과 CONTRACT 4.0.1 규칙 정본 문구는 해당 구현 card(OP-3~OP-7) 몫으로 남는다. 더해진 줄의 내용은 이 card가 대조하지 않았다.
* 분류는 계획 N3.7을 따른다.

### 17.1 공통 치환 문구

| 기호 | 지금 문구 | 새 문구 |
|---|---|---|
| R-A | 'ngspice로 판정', '판정자 = ngspice', 'ngspice 불합격', 'ngspice를 통과' | 'SPICE 오라클로 판정', '판정자 = SPICE 오라클(첫 어댑터 ngspice)', 'SPICE 오라클 불합격', 'SPICE 오라클을 통과' |
| R-B | '전력 = ngspice 측정' | '전력 = SPICE 오라클 측정' |
| R-C | 'ngspice는 측정할 수 있는 항목만 판정한다' | 'SPICE 오라클은 측정할 수 있는 항목만 판정한다' |
| R-D | 'VCCS ngspice 오라클' | 'VCCS SPICE 오라클' |

### 17.2 상위 계획 `gain-budget-gmid-sizing.plan.md`(줄은 base `d783efe` 기준, 계획 N3.7 표와 같은 순서)

| 줄 | 분류 | 문안 |
|---|---|---|
| 11 | 둠 | -- |
| 123 | 고침 | '판정은 ngspice만 하고' → '판정은 SPICE 오라클만 하고(공칭은 모델 묶음 자동 대조, MC·온도는 능력 기록, 첫 어댑터 ngspice)' |
| 152, 284 | 고침 | '9회로 ngspice 합격 시험' → '9회로 SPICE 오라클 합격 시험'(284는 사용자 원문 인용 밖 문구만) |
| 286, 475 | 둠(D-2 뒤 고침) | OP-8 병합 뒤: '칸 중앙을 ngspice로 직접 재는' → '칸 중앙을 LUT 생성 어댑터로 직접 재는' |
| 296 | 둠(둘째는 D-2 뒤 고침) | OP-8 병합 뒤: 'ngspice 소자 쌍 Monte Carlo 대조 test' → 'LUT 생성 어댑터 소자 쌍 Monte Carlo 대조 test' |
| 297 | 고침 | 제목 '엔진 시작점·front를 ngspice로 판정하고' → 'SPICE 오라클로 판정하고'. (1) '판정자 = ngspice' → R-A |
| 478 | 고침 | 'P = 개루프 RHP 극점 수, 오라클이 ngspice `.pz`로 독립 측정' → '오라클이 어댑터 pz 능력으로 독립 측정(능력 없으면 P = 미정 경로, design oracle-portability §8.5)' |
| 542 | 고침(인터페이스·경로) | 인터페이스 문장 전체를 '오라클은 코어·시뮬레이터 어댑터·오라클 기술자 세 층이다(oracle-portability 계획 N3.1). 엔진 GB9는 `oracle_run`을 외부 단계로 부르고, 입력 `simulator` 블록으로 어댑터와 실행 파일을 고른다'로 바꾼다. 같은 절 `verified_by` 칸에 'capability_record_id'를 더한다(D-6). 옛 대조 스크립트 파일 이름은 둔다 |
| 576, 1112 | 고침 | R-D |
| 1140, 1142, 1143, 1145, 1146 | 고침 | R-A, R-B, R-C |
| 1144 | 둠 | -- |
| 1244 | 둠 | D-4 승인 시 끝에 '(경계 규칙 정본 = LUT 생성 실행에 묶은 선언, oracle-portability D-4)' 참조만 더한다 |
| 1293 | 고침(판정 문구) | R-A, R-B, R-C(`2.5p`는 둠) |
| 1335 | 고침 | 'SPICE 모델·ngspice 환경 부재' → 'SPICE 모델·시뮬레이터 환경 부재'. 실행 파일 경로 문장 → '실행 파일은 입력 `simulator.exe`, 보정값은 어댑터 선언' |

### 17.3 design 40 `gain-budget-gmid-sizing.40-engine.design.md`

| 줄 | 분류 | 문안 |
|---|---|---|
| 26 | 둠 | -- |
| 1444 | 고침 | '끊은 개루프 테스트벤치(같은 루프 절단)에 ngspice `.pz`를 돌려' → '끊은 개루프 벤치(같은 루프 절단)에 어댑터 pz 능력으로 극점을 구해(능력이 없거나 독립 증거로 확인되지 않으면 P = 미정)' |
| 1844 | 고침 | '(c) ngspice mismatch 블록 변수를 소자마다 gauss로 둔 MC' → '(c) 오라클 기술자가 선언한 네이티브 MC(능력 확인 PC-3 통과 조합). 크기 일관은 엔진 σ_in 대 MC σ_in 비교(offset-trim TR-7 §17-1)' |
| 1940, 1941, 1942, 1953, 1955, 1956, 1962, 2018 | 고침 | R-A, R-B, R-C |
| 1954 | 둠 | -- |
| 1996 | 둠(D-2 뒤 고침) | OP-8 뒤 '격자점·칸 중앙 LUT 생성 어댑터 대조(c)' |
| 2002 | 고침 | 'ngspice `.noise`(c)' → 'SPICE 오라클 noise(c)' |

### 17.4 그 밖

| 문서 | 문안 요지 |
|---|---|
| C10 계약 §1(b) | 'ngspice 안에서 `stop when`/`resume`로 창 j를 차례로 끝내며' → '어댑터가 조기 종결 능력을 선언하면 시뮬레이터 안에서 창 단위로 멈추고, 선언하지 않으면 design oracle-portability §8.4(G-13 결정)대로 실행한다. 판정 기준은 코어가 정의한다' |
| C10 계약 §1(c) | 'ngspice 실행 시간의 상한' → '어댑터 보정값 `wall_s_per_window`(출처·측정 조건 포함)' |
| C10 계약 §3 | 구현 메모(`>` 리다이렉션, `stop when` 문법, `numdgt`)는 'ngspice 어댑터 방언 메모'로 제목만 바꾸고 둔다 |
| `O/README.md` | 3층 구조, 어댑터 절, 기술자 절, 능력 확인 절로 다시 쓴다(OP-3~OP-6에서 card마다). '확인(… ngspice-46 sky130 tt)' 기록 절은 둔다 |
| `E/lut/CONTRACT.md` 4.0.1 | D-4 승인 시: '규칙 정본 = LUT 생성 실행에 묶은 bin 규칙 선언(oracle-portability §16)'. 실측 문단은 출처로 둔다 |
| `E/lut/CONTRACT.md:528` | 둠 |

---

## 18. test 목록(완료 조건별, 계획 N5.3)

### 18.1 새 test

| 완료 조건 | test(위치 `O/tests/`) | 기준 소유 | 내용 |
|---|---|---|---|
| 1 무방언 | `core/test_no_dialect.py` | 토큰 목록 = 검증자(OP-1) | T1-1 `O/core/` 문자열 리터럴(docstring 제외)의 토큰 정규식 적중 0. T1-2 PDK 이름(모든 기술자·엔진 선언 `pdk` 값과 모델 이름 패턴) 0. T1-3 AST import 금지(§3.2) 0. T1-4 `O/core/` 안 비-.py 파일 0. 코어의 파일 열기 경로가 입력·기술자(와 그것이 sha256으로 가리키는 원본)·출력 디렉터리뿐인지는 **실행 중 기록**으로 잰다: 코어 test 전체를 도는 동안 `builtins.open`·`io.open`·`os.open`·`numpy.load`·`pathlib.Path.open`을 감싸 연 경로를 모으고, 모든 경로가 그 test가 넘긴 허용 뿌리(입력 파일, 기술자 파일·원본 뿌리, 출력 tmp 디렉터리) 아래인지 확인한다. 보조로 AST에서 코어 모듈의 열기 호출 인자가 문자열 리터럴 경로가 아님(경로를 코드에 두지 않음)을 본다. T1-0(먼저) 토큰 목록이 기준선 넷리스트와 옛 코드 리터럴에서 적중함을 보인다. (v0.2.5 고침, 계획 N5.3-1 **X-23 단계 규칙**·OQ-2 승인 L-3) 적중 증거의 출처는 토큰마다 단계로 적는다: '기준선 증거'(기준선 넷리스트·옛 코드 리터럴에서 적중) 또는 '<card> 산출물 증거'(기준선에 없는 형태는 그 형태를 처음 쓰는 card가 병합된 뒤 그 card의 **어댑터 산출 넷리스트**에서 적중을 보이고 그때 목록에 넣는다). 적중을 보이지 못한 토큰은 목록에 넣지 않고, 넣은 채 '0'을 합격으로 세지 않는다. 이 규칙의 첫 사례가 초안 D11(난수·식 함수 형태)이다: 기준선 어디서도 적중하지 않았고(S-16), 그 형태를 처음 쓰는 card는 네이티브 MC 켜는 법 `param_redefine`을 어댑터가 쓰는 OP-5다. 단계 표시는 검증자 소유 목록(G-8)의 칸이고, 이 문서는 형식만 정한다 |
| 2 stub | `core/test_*_stub.py` | test 작성자 | §3.3 표의 stub 실행 항목 전부, '능력 없음 거부' 항목 전부, D-1 전체 창 경로(G-13 결정된 방식) |
| 3 동일성 | `adapters/ngspice/test_equivalence.py`(검증자 실행) | 기준선 = 검증자(OP-1, 보관 OP-1a) | 계획 N4: 이산 칸 정확, 연속 칸 비트 동일 또는 분해능 안(§18.3 식), MC 연속 칸 제외 + §13.2 (가-1)·(가-2), 입력 변환 = 검증자 스크립트, 결과 칸 이름 대응 = §11.5. (v0.2.5) 기준선은 OP-1a가 `.ai/verification/<OP-1 id>/baseline/`에 커밋한 판정용 텍스트만 읽는다(저장소 밖 경로·`legacy/` 접근 0). 이 test가 읽는 파일 목록이 OP-1a 보관 목록의 소비처다. (v0.3.0, 계획 N4 0번 = 사용자 결정 O-34 (1), DR-17) 칸마다 **변경 종류**로 판정을 고른다: 정의가 그대로인 칸 = 위 동일성, 정의를 바꾼 칸(계획 N4 0번 표: OP-3 입력 형식 전환과 새 거부, OP-5의 ICMR·swing·계통 offset·단일 입력·A 출처와 σ·합격 판정 전도 기준, OP-10 슬루, OP-11 `power_dc_w`) = 동작 변경 기준(§18.1 '10 정의 대조' 행 + 검증자 원인 변화표, 원인 미설명 0), 결정성(두 번 실행 비트 동일) = 모든 card. (v0.3.1, DV-7 닫힘 -- O-50 O1′, 계획 N4-1 '추가 기준선'·OP-1b) **정의가 그대로인 칸의 비교 상대 = OP-1b 추가 기준선**(`.ai/verification/<OP-1b id>/baseline/`, 검증자가 옛 오라클로 만든 것 -- OP-3·OP-4·OP-5·OP-11 공통, 계획 N4-2a '적용 확장'). OP-1 기준선 입력 593개의 변환 결과는 D-7 거부를 기대하는 동작 변경 판정에만 쓴다(§11.5 `process.lut_npz` 행). (가-1) MC 수학은 시뮬레이터·D-7을 지나지 않아 OP-1 기준선 그대로(계획 OP-1b 행) |
| 4 거부 | `core/test_capability_rejects.py`, `core/test_gates.py` | test 작성자 | PC-1~3·5~8·**10**마다 §12.2 깨진 변형 거부(먼저). (v0.2.5, 검증 B-2) **PC-10 깨진 변형 셋**(OP-6): 기준 해를 버리고 흔들림만 내는 경로, 온도마다 기준을 다시 푸는 경로, `output_reference` 없이 기본 기준을 몰래 쓰는 경로가 각각 실패함 + 입력에 `output_reference`가 없는데 V_sys 측정을 요청하면 실행 전에 `reference_undeclared`로 거부됨(시뮬레이터 호출 0, §7.2 6번). (v0.2.5) 모델 묶음 규칙: LUT 생성 보조 입력의 sha256이 기록과 다르거나 그 파일이 없는 공칭 실행 → `lut_aux_input_mismatch`, 역할 선언을 지운(또는 적용되지 않는) 기존 LUT의 공칭 실행 → `model_bundle_mismatch`(규칙 (i), §12.5), 기록 없음 → `oracle_capability_unverified`, 지문 하나 바꾼 기록 → `oracle_capability_stale`, 모델 묶음 불일치 → `model_bundle_mismatch`, LUT 기록 빈 표 → `lut_model_provenance_missing`, 진단 결과가 판정 입력으로 → `diagnostic_not_a_gate`. (v0.2.4, O-6 D-a) **분포 값 출처 깨진 변형 셋**: 분포 값을 기술자에 직접 적은 기술자 → `mc_distribution_inline`, 가리킨 원본 sha256이 맞지 않는 기술자 → `pdk_descriptor_stale`, 분포 값 위치가 없거나 0개를 찾는 기술자 → `mc_distribution_unlocated`. 켜는 법 종류가 어댑터 `mc_enable_kinds` 밖이거나 코어 고정 요구(§10.4)를 어댑터가 선언하지 않으면 → `mc_method_unsupported`(`side = "adapter"`), 기술자에 `requires` 칸을 둔 변형 → `descriptor_schema_invalid`(v0.2.5, 계획 X-20: 기술자로 요구를 낮출 경로가 없음을 보인다). 같은 확인 코드가 sky130 기술자와 손 모델 기술자 둘에서 돈다. **(v0.3.0, DR-13, 계획 완료 조건 4 'sha256 정의 깨진 변형', OP-2 행) sha256 정의 변형 넷**(test 작성자가 CRLF 바이트로 만든 픽스처 파일을 쓴다): (i) 기술자 칸에 참조 파일의 raw(CRLF) 값을 적은 변형 → `pdk_descriptor_stale` (ii) 홀로 있는 `\r` 또는 BOM만 다른 참조 파일 → `pdk_descriptor_stale`(CRLF만 정규화함을 보임) (iii) raw로만 맞는 엔진 원본 기록(`newline` 없는 `sources` 항목) → 받고 결과 `machine_dependent_refs`에 그 참조가 적힘 (iv) 정규화·raw 둘 다 안 맞는 엔진 원본 기록 → `pdk_descriptor_stale`(`actual_sha256 = {lf, raw}`). 같은 꼴로 LUT 기록(규칙 (ii)): raw로만 맞는 `model_files_sha256` → 받고 기계 의존 표시, 둘 다 안 맞음 → `model_bundle_mismatch` |
| 4a 기하·배수(OP-5) | `adapters/ngspice/test_geometry_multiplier.py` | test 작성자(interface만 보고 씀) | **손 모델 픽스처 정본**(§12.7, OP-5 산출)으로 결정적 어댑터 test. 측정 양 = 회로 출력(같은 바이어스에서 같은 ID 기준 VGS 편차), 모델 파라미터 재독 값으로 판정하지 않는다. 같은 시드에서 (i) 피검 소자의 `n_fingers`만 바꾸면 편차 비 = 손 모델 식이 정하는 비 (ii) 손 모델 식이 전제하는 기하 단위만 다른 둘째 기술자(test 안 파생 변형, §12.7)에서 같은 물리 기하의 편차 비 = 두 식과 단위 환산비가 정하는 비. **표본 정체 보존**: 같은 벤치에 배수를 바꾸지 않는 기준 소자를 두고 두 실행에서 그 값이 같음. **인스턴스 기하 단언**(v0.2.5 고침): 모든 실행에서 시뮬레이터 보고 **원값** `OpTable.instance_geometry_reported`(§6)가 test 작성자 계산 기대값과 같다. 기대값 = IR 기하와 기술자 선언(기하 단위 u, `parallel_multiplier.to`)에서 test 작성자가 따로 계산하고, 보고값이 배율 적용 전·뒤 어느 쪽인지는 R6 쪽을 인용한다. 어댑터가 되돌린 값으로 단언하지 않는다(같은 규칙을 두 번 적용하면 오류가 상쇄된다). **비교 폭**: 편차 Δ = V₁ − V₂의 분해능 δΔ = Σ(reltol·|Vᵢ| + vntol)(§18.3), 비 ρ = Δa/Δb의 폭 |ρ|·(δΔa/|Δa| + δΔb/|Δb|)(새 상수 없음). **거부 먼저**: (a) 배수를 모델 파라미터로 넘기지 않는 변형은 편차 비가 달라 실패 (b) 단위 선언을 무시하는 변형은 회로 출력이 아니라 어댑터가 쓴 넷리스트와 `instance_geometry_reported` 원값 대 기대값으로 실패 판정. PDK 공식에 기대값을 걸지 않는다(PC-4와 다름) |
| OP-3 병합 (a) | `core/test_geometry_undeclared.py` | test 작성자 | `geometry_unit` 또는 `parallel_multiplier`가 없는 기술자로 공칭 op·ac·MC 요청을 각각 보내면 실행 전에 `descriptor_geometry_undeclared`로 거부됨(stub 어댑터로 충분, 시뮬레이터 호출 0, `detail.missing`이 빠진 칸과 같음). (v0.2.5, 검증 M-2) **MC 요청의 판정 순서**(§7.2)와 **양성 대조**: (1) 기하 미선언 기술자 + MC 요청 → `descriptor_geometry_undeclared`(3번이 4·5번보다 먼저) (2) 기하를 완전히 선언하고 `mc` 칸이 없는 기술자 + MC 요청 → `mc_method_unsupported`(`side = "descriptor"`) (3) (OP-5에서 더함) 기하·`mc`를 완전히 선언한 기술자 + MC 능력 없는 stub + MC 요청 → `adapter_capability_missing` (4) 같은 완전 선언 기술자 + 공칭 op·ac 요청 → stub이 실행해 결과를 낸다(거부가 기하 미선언 때문이지 다른 결함 때문이 아님을 보이는 양성 대조). `global_directive` 방법인데 `affects` 선언이 없는 어댑터 stub → `adapter_calibration_missing`, 비 SI 단위 기술자 + 적용 방법 없는 stub → `adapter_capability_missing` |
| OP-3 병합 (b) | `adapters/ngspice/test_equivalence.py`의 공칭 op·ac 부분(검증자 실행) | 검증자 | 첫 조합 선언값(§10.3)으로 쓴 공칭 op·ac 결과가 N4-2로 기준선과 동일. 소자 줄 차이는 N4-3 정규화 대조로 기록만 하고, 차이가 기하 단위·병렬 배수 선언에서 나온 것뿐임을 §10.6 '차이가 선언에서만' 절차(기준선에 선언 변환 적용 → 정규화 → 남은 차이 0)로 보인다(v0.2.5, 검증 M-3) |
| OP-3 병합 (c) | `core/test_bundle_roles.py`(test 작성자) + 옆 선언 파일(검증자) | 옆 선언 = 검증자, test = test 작성자 | (v0.2.5, 계획 OP-3 (c)) 검증자 옆 선언(§12.5)이 있고, 그 선언으로 첫 조합 공칭 실행이 규칙 (i)~(iii)을 통과(검증자 실행 기록). test: 역할을 지운 변형(옆 선언 참조를 뺀 기술자, 또는 `generator_sha256`이 다른 옆 선언) → `model_bundle_mismatch`, 보조 입력 sha256을 바꾼 변형 → `lut_aux_input_mismatch`, 보조 입력 파일을 지운 변형 → `lut_aux_input_mismatch`(`missing`), 형식 위반 옆 선언 → `lut_file_roles_invalid`. 묶음·LUT 기록은 test 작성자의 작은 픽스처로 충분하다(시뮬레이터 호출 0) |
| 오류 대응(OP-3·OP-4) | `adapters/ngspice/test_errors.py` | test 작성자 | (v0.2.5, 검증 M-5) (1) §7.1 대응표 행마다 기준선 로그 발췌(OP-1a 보관 텍스트) → 코드 (2) **회복된 경고**: S-30 로그(회복 시도 경고 뒤 결과 있음) → 벤치 `RunStatus.error = None`, `warnings`에 그 문장들, op 결과 사용 가능, 같은 로그의 pz 반복 한도는 그 `Pz` 요청 `error = sim_convergence_failed`만 (3) 결과가 없는 같은 경고 → `sim_convergence_failed` (4) **주입 로그**: 기준선 사례가 없는 `sim_timestep_too_small`(문장 형태 = R6 원문, OP-2 병합 조건 뒤)과 `sim_timeout`(시간 상한 아주 작게 또는 시간 초과 예외 주입) → 그 코드. 주입 증거 행은 '주입 증거' 단계로 표시한다(§7.1) |
| 5 텍스트 단언 이전 | `core/test_no_dialect.py` T5-1 | 검증자 토큰 | `O/tests/core/` 안 방언 토큰 단언 0 |
| 6 삭제 | `test_deleted_names.py` | test 작성자 | §15.1 옛 이름 grep 0(card별로 그 card 몫만) |
| 7 배선 | `test_wiring.py` | test 작성자 | `oracle_run` 경로에서 코어·어댑터·기술자 읽기·자동 대조·MC·온도 게이트·진단 입력이 호출됨(호출 기록 증거) + 검증자 판정 기록 둘: (가-2) 진단 도구가 `oracle_run` 진단 입력에서 호출된 기록, (가-1) 코어 MC 수학 함수가 그 판정에서 호출된 기록(v0.2.5, 계획 N5.3-7 O-8) |
| 8 엔진(D-4 승인 시) | 엔진 쪽 OP-7 test | 엔진 test 작성자 | 9회로 비트 동일, bin 규칙 선언 없음 → 경계 L 거부 |
| 8a 엔진 무변경 | `test_engine_untouched.py`(검증자 git diff) | 검증자 | OP-2~OP-6·OP-8에서 엔진 소스(`E/` 아래 test 밖 파일)·기존 test 파일·`A/sky130_pdk_decl.json` diff 0. **예외**(계획 v0.5.1 8a): `E/tests/` 아래에 엔진 선언·오라클 기술자만 읽는 새 test 파일 추가는 허용(아래 X-13 test 하나). **예외 둘째**(계획 v0.6.5 O-9): `E/tests/metrics/test_verified_by.py:64` glob 한 줄(아래 행) |
| X-13 | `E/tests/core/test_oracle_descriptor_engine_sha.py`(엔진 suite에서 돈다, 계획 v0.5.1 8a 예외) | test 작성자 | (v0.3.0 다시 씀, DR-13·DR-16, 계획 X-13 'v0.6.7'·'v0.6.8', N3.4 규칙 (iii)) (a) **엔진 선언 파일 바이트를 test가 직접 읽어 LF 정규화로 다시 잰 sha256** ≠ 기술자 `engine_decl.sha256`이면 실패. 엔진 `decl_sha256` 값과 견주지 않는다(엔진 card SH-1 전에는 raw라 정의가 다르고, 뒤에는 정의가 같아도 그 값은 엔진 실행 값이라 읽으려면 엔진 import가 필요해 8a 예외를 벗어난다 -- 재측정 유지) (b) 중복 없음: 엔진 선언 `sources`의 **모든** 파일(기술자가 쓰지 않는 원본 포함)과 기술자 `extra_sources` 파일을 바이트에서 LF 정규화로 다시 잰 값끼리, 그리고 경로끼리 겹침이 없음. 어느 파일이든 없으면 실패. 정규화는 test 안에 같은 한 줄 정의(`data.replace(b"\r\n", b"\n")` 뒤 sha256)를 쓴다 -- 오라클 코드를 import하지 않는다(계획 G-5). 엔진 코드를 import하지 않고 JSON과 파일 바이트만 읽는다 |
| 8a 예외 둘째(OP-3) | `E/tests/metrics/test_verified_by.py:64` 한 줄 | 엔진 test 작성자 | (v0.2.6, 계획 v0.6.5 O-9 DV-4 (가), X-25) `ORACLE.glob("oracle_*.py")` → `(ORACLE / "core").rglob("*.py")`. 측정 키 8개와 판정 내용 불변. 같은 변경은 compare를 코어로 옮기는 OP-3. `test_engine_untouched.py`(8a 행)는 이 한 줄과 X-13 새 파일만 diff로 허용한다 |
| 기록 뿌리 해석(OP-2) | `core/test_lut_record_root.py` | test 작성자 | (v0.2.6) §10.2 `lut_record_root` 해석: 환경 값 있음 → 그 값, 빈 값·없음 + `default` → `default`(**둘 다** `os.path.abspath` 적용, `E/lut/CONTRACT.md` 1.8 261행), 둘 다 없음 → `lut_location_decl_invalid`, 위치 선언에 `pdk_root` 칸 없음 → `lut_location_decl_invalid`(엔진과 달리 LUT meta로 돌아가지 않음, §10.2 '의도된 엄격'), 기술자 자체 형식 오류 → `descriptor_schema_invalid`(위 둘과 구분됨을 함께 단언), 위치 선언 sha256 다름 → `pdk_descriptor_stale`(`lut_location_decl`). 기대값은 형식 규칙(`E/lut/CONTRACT.md` 1.8)에서 test 작성자가 쓴다(엔진 import 없음). (v0.3.0, DR-10j) '다른 트리를 가리키는 뿌리 → `lut_record_root_mismatch`' 항목은 이 행(OP-2)에서 빼서 아래 'OP-3 기록 뿌리 교차 검사' 행으로 옮겼다(사용자 결정 O-14 (4) J-5 (가)) |
| (v0.3.0) OP-3 기록 뿌리 교차 검사 | `core/test_lut_record_root_cross.py` | test 작성자 | (DR-10c·DR-10j) §7 `lut_record_root_mismatch` 세 걸음: 짝이 있고 뿌리 아래 파일 LF 값 = 엔진 원본 LF 값 → 통과(양성 대조), 다른 트리를 가리키는 뿌리(짝 파일 바이트가 다름) → 거부(`root_file_lf_sha256` ≠ `engine_file_lf_sha256`), 뿌리 아래 짝 파일 없음 → 거부(`"missing"`), 짝 0개(LUT 기록값이 어떤 엔진 원본의 LF·raw 값과도 같지 않음) → 거부(`why = no_pairs`), LUT 기록이 raw로만 엔진 원본과 맞는 짝 → 짝으로 인정(규칙 (ii)) 그리고 결과 `machine_dependent_refs`에 표시. 기록값끼리 비교하는 구현은 CRLF 픽스처에서 이 test를 지나지 못한다(깨진 변형) |
| (v0.3.0) OP-3 입력 계약 | `test_input_contract.py`(진입점 포함, 시뮬레이터 호출 0) | test 작성자(§11만 보고 씀) | §11.3 예시가 1a~2b를 통과하고(양성 대조, stub 어댑터), E1~E18 깨진 변형이 표의 코드로 거부됨(거부는 반환 2 + `<circuit>.reject.json` 하나, 넷리스트·결과 파일 0개 -- §11.7). §11.2 순서: 두 결함을 함께 넣은 변형(사례 E2 + E5)은 앞 단계 코드 하나만 냄. 닫힌 키 집합: 각 객체 층(`process`, `devices[]`, `predictions.devices.<n>`, `testbench`, `judge`, `judge.tolerances`, `noise`, …)에 모르는 키 하나씩 넣은 변형이 모두 거부되고 `provenance`에 넣은 키는 받음. `O/oracle_input.schema.json`이 §11.1 표와 같은 칸 집합인지(표의 칸 이름 목록을 test 작성자가 옮겨 적고 스키마 파일의 `properties`와 대조) |
| (v0.3.0) 실행 결과 계약 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** `test_result_contract.py` | test 작성자 | §11.7: 같은 입력 두 번 → `record_id` 비트 동일(결정성), `netlist` 경로만 다른 두 실행 → 같은 `record_id`, `fingerprints` 세 칸 존재, `machine_dependent_refs` 칸 존재(빈 목록 포함), `summary.conduction_definition` = OP-3 판 `"threshold_eps1"` / OP-5 뒤 `"seal9_two_stage"`. (v0.3.2, OP-5 뒤) `conduction.points[]` 칸 집합(`VGS`·`m` 포함, §11.7), 범위 끝 기록 스키마 하나·창 값 `status = provisional`, 판정 우선순위(1단계 FAIL + 대기 소자 → `FAIL`, 대기 소자만 → `PENDING_CONDUCTION`·반환 0, 대기 없고 판정 불능 → `INCOMPLETE`) |
| (v0.3.0; **v0.4.0 정본 = §18.1 끝 v0.4.0 행들이 이김**) 10 정의 대조 -- OP-5 | `core/test_conduction.py`, `core/test_swing_icmr_def.py`, `core/test_offset_sys.py`(기준 종류 셋 + 차동 기본, §21.4; v0.3.3 값 식 3단계 = V_id* − V_id,0(선언 입력 DC 기준) -- free servo 해를 빼는 변형 실패, `dc_sweep.input_dc` 없음 → `input_dc_undeclared`, 차동 같은 DC 선언 → V_id,0 = 0), `core/test_range_confirm.py`(v0.3.3: 네 검사 깨진 변형 넷 → `range_pointer_rejected` `check`별 red(재훑기 기록 합친 열의 (2)·(4) 포함, (4) 면제는 `pass_point_id` ∧ `end_cause` ∈ {rail, rail_filter, stage1}일 때만), `range_input_fp`가 CLI 덮어쓰기·adapter_fp·descriptor_fp 변화에 따라 바뀜, 다른 `<out_dir>` → `record`, `range_final` 값 = §21.2 식(엔진 쪽 사본 grep 0), 잠정 실행 verdict에 범위 제약 없음, 기록 파일 이름 `<stem>.<kind>.<rid16>` 덮어쓰기 없음, `confirmed_range`+`sweep_rezoom` 동시 → E5), `adapters/ngspice/test_tf_gain.py`(v0.3.3: 단일 입력 A가 값, 차동 비트 동일) + 검증자 정의 대조표 | test 작성자(정의 문장에서 기대값), 검증자(대조표·원인 변화표) | 계획 완료 조건 10(v0.3.2 재작성 -- §21.1 깨진 변형·§11.7 기준): §21.1 1단계(ID ≤ 0 → `off_reverse`, \|ID\|로 역방향 전도를 전도로 세는 변형 실패(G3); ID > 0 → `stage2_pending`, 통과로 세지 않음; 값 하나 없음 → `stage1 = undefined`·`conduction_undefined`; 오라클 안 LUT 보간 사본 grep 0(G5); 온도 조건 요청에서 `ioff_bench`가 소자마다 돌고 `i_off_spice_A`·`tol_v_source = "T_j_lut_cell"`이 실림(B2, G3 ID ≤ 0 소자 포함); 7단계 선언 영역 세 경우(선언 없음·triode·off)), 2단계 쪽 깨진 변형(ε = 1, 동작점 값, 여유를 정의에)은 엔진 쪽 2단계 test 몫(OP-5 통합 병합 엔진 커밋), §21.2 손 회로(단일 입력 회로의 ICMR이 `unavailable`이 아니라 값이 나옴, 출력 고정 ICMR 변형은 다른 값, 수렴 실패 점 하나 → `sweep_point_unconverged`, 반복 상한 도달 → `sweep_end_unresolved`; (v0.3.2) 훑기 중 선언 영역 이탈 = 범위 끝·`departed` 기록(측정 거부로 세는 변형 실패, O-54), 훑기 이탈이 범위 축 끝이면 `end_cause = rail`, `sweep_rezoom` 1회 훑기·`rounds_left − 1`·`rounds_left = 0` → `sweep_end_unresolved`, `measure_feedback` 구성 벤치와 반전 포트 포트별 `.tf` 부호 판정(후보 0·2개 이상 → `inverting_port_undetermined`), swing만 공칭 점 차 거부·ICMR 결과에 `nominal_output_shift_V` 칸 없음(B-45)), §21.3 합격 판정(오라클 결과만으로 PASS 없음 -- 대기 소자 → `PENDING_CONDUCTION`; 동작점 선언 불일치 → `intended_region_mismatch` → `INCOMPLETE`, FAIL로 세는 변형 실패(U1); 선언 없는 소자 비포화 → FAIL), §21.5 `.tf`(개루프 손 회로 A = gm·R, servo 닫힌 변형은 다른 값, `.ac` 첫 점·`1e-3` grep 0), (옛 '선언 triode 두 경우 단언'은 v0.3.1 `intended_region`으로 대체 -- 위 7단계 항목). **(v0.3.4, DV-14·DV-15·DV-16 닫힘 -- 계획 DR-19·DR-20, 기대값은 정의 문장에서 test 작성자가 씀)** (a) `adapters/ngspice/test_tf_gain.py`·`core/test_offset_sys.py` **A_dc 갈래 손 회로**(DR-20 P11; v0.3.5 검증 M5·M6·N2 반영): A = 0 손 회로(입력이 출력에 닿지 않는 VCCS -- 그 출력 고정 `.dc`가 수렴함은 test가 같은 벤치 요청으로 따로 보임)에서 `sim.a_dc = {status: undefined, reason: a_dc_below_resolution}`, `offset_mc.status = unavailable`·사유 `a_dc_undefined`(`detail.a_dc_ref = "/a_dc"`), `sim.offset_sys.reason = a_dc_undefined`이고 **값 칸 없음**(`.dc` 해로 값을 내는 변형 red), **주 경로의 `.dc` 출력 고정 요청 수 = 0**(어댑터 요청 기록; 갈래 발동인데 `.dc`를 부르는 변형 red -- M5); (v0.3.6, DV-17 닫힘) 0이 아닌 작은 A 손 회로: \|A\|·W_rail ≤ δV_out(δV_out = vntol + reltol·\|공칭 V(o)\|, test가 정의 문장에서 계산)이면 `a_dc_below_resolution`, 바로 위(\|A\|·W_rail > δV_out)면 값(양성 대조); 차동 출력 손 회로에서 δV_out = δ_p + δ_n(한 노드만 쓰는 변형 red); \|V\|를 개루프 벤치 `.op` 값으로 쓰는 변형 red; 레일 폭 0 입력 → `rail_width_zero`; `sim.a_dc`에 문턱·δV_out 값 칸 없음; `.tf` 실패 주입 → `reason = tf_failed`(갈래와 다른 이름); 공칭 free 실행 미수렴 주입 → `nominal_unconverged`; `dc_sweep` 없음 → `sweep_direction_undeclared`(σ·offset_sys 모두 그 사유 먼저); `input_dc` 없음 → `offset_sys.reason = input_dc_undeclared`(`.tf`는 정상); `.dc` 수렴 실패 주입(A 정상) → `sim_convergence_failed`(사유가 서로 다름); 단일 출력 기준 미선언 → 실행 전 `reference_undeclared` 거부(시뮬레이터 호출 0); 한 실행에서 **여기 방향 `tf_bench`(port 없음) 요청 수 = 1**(σ·V_id* 둘 다 요청해도 -- 둘째 측정 변형 red), 반전 입력 식별의 포트별 `tf_bench(port=p)`는 따로 센다(M6); `offset_mc`·`offset_sys` 기록에 A 값 칸 없음, compare JSON에 `sim.a_dc`·`sim.offset_sys` 사본 없음(`sim_ref`만); **있는 조건**(N2): forced·iso bias 실행, `offset_mc`·`offset_sys_mv`·PC-10 요청 없는 free 실행에는 `sim.a_dc` 칸 없음·`tf_bench` 요청 0 (b) `core/test_swing_icmr_def.py` **`icm_margin_v` 포트별 식**(v0.3.6, DV-18 닫힘, DR-21): 기대값 = 정의 문장 min_p min(V_p − lo_p, hi_p − V_p)(test 작성자가 손 회로 포트 전압에서 계산) -- c = (1, 1) `declared` 손 회로, **반례 둘**: c = (2, 2)(사영 식이면 값이 1/2 -- 사영 변형 red), β = 1 follower(묶인 반전 입력은 대상 아님 -- 넣는 변형 red); 입력에 `dc_sweep.input_dc`를 바꿔도 `icm_margin_v`가 변하지 않음; `swing_icmr.input_dc_V`·`input_dc_pending` 입력 → E5; ICMR 점 기록에 `m` 칸 없음(`v_in`만, m은 `icmr_coord` 한 함수). **(d) S-OS2 DC 닫힘**(DR-21): DC 되먹임 없는 차동 되먹임 손 회로(v0.3.9 둘째 커밋 문언 -- §21.2 2단계 (0) 판정 '없음' 두 출력 모두; 이상 차동 VCCS(입력 넷은 제어 단자에만 -- 들어오는 엣지 없음) + CMFB + DC 전도 원소 없는 선언 Cf -- current_reuse 꼴)에서 ICMR 벤치 넷리스트에 `tb:icm` 1개·`tb:dmc:a`·`tb:dmc:b` 2개(이득 ±½, 제어 = 출력 짝)가 있고, 각 훑기 점에서 V(in_a) − V(in_b) = V(o_a) − V(o_b)와 ½(V(in_a) + V(in_b)) = cm0 + y·c_s가 §18.3 분해능 안; **(v0.3.7, 검증 필수 4) 판별 가능한 닫힘 부호 test** -- 옛 '짝 부호를 뒤집은 변형(양되먹임)은 수렴 실패 또는 다른 창 → red'는 지운다(DC `.op`는 평형점의 안정성을 가리지 않아 대칭 손 회로에서는 두 부호가 같은 해 d = 0을 낸다): (d-1) **오프셋 손 회로**: 같은 손 회로의 한 입력에 이상 전압원 V_os(test 픽스처 값, 0 아님)를 직렬로 넣고 유한 차동 이득 A_d = d(V(o_a) − V(o_b))/d(V(in_a) − V(in_b)) < 0(\|A_d\| > 1, 손 회로 gm·R)에서, 공칭 점(y = 0)의 출력 차 d_out의 기대값 = 정의(닫힘 V(in_a) − V(in_b) = d_out, 회로 d_out = A_d·(V(in_a) − V(in_b) + V_os))에서 test 작성자가 푼 A_d·V_os/(1 − A_d) -- 부호 = sign(A_d·V_os), 크기 < \|V_os\|; 짝을 뒤집은 변형(닫힘 V(in_a) − V(in_b) = −d_out, 또는 in_a·in_b 짝 바꿈)은 d_out = A_d·V_os/(1 + A_d)로 **부호가 반대**이고 크기 > \|V_os\|라 red (d-2) **구조 단언**(v0.3.7 둘째 커밋 고침, 검증 N3 -- 단일 끝 T(in_a → o_a) 대신 차동 이득): 이미 잰 포트별 `.tf` 네 값 T(p → o)(p ∈ {in_a, in_b}, o ∈ {o_a, o_b})로 A_d = [T(in_a → o_a) − T(in_a → o_b)] − [T(in_b → o_a) − T(in_b → o_b)]의 ½배(d(V(o_a) − V(o_b))/d(V(in_a) − V(in_b)), 두 입력에 ±½ 차동을 건 선형 중첩 -- 새 `.tf` 요청 없음)를 만들고 sign(A_d) · sign(닫힘 계수) < 0(닫힘 계수 = d(V(in_a) − V(in_b))/d(V(o_a) − V(o_b)) = (+½) − (−½) = +1, 넷리스트 `tb:dmc:*` 이득에서 읽음)을 단언 -- 루프 이득 부호가 음수(음되먹임)임을 비대칭 회로에서도 값과 무관하게 단언, `tb:dmc` 이득 부호를 바꾼 변형 red (d-3) c = (2, 2) DC 닫힘에서 ½(V(in_a) + V(in_b)) = cm0 + 2y(구성상 정확 -- v0.3.7 둘째 커밋 고침, 검증 N5: 두 포트 각각은 닫힘 차 ½·Δd_out만큼 어긋나므로 포트마다 y·2를 단언하지 않음, `tb:icm` DC = cm0 + 2y), c = (1, 2) 입력 → `closure_common_asymmetric`(시뮬레이터 호출 0 -- `.tf` 포함), (d-4) `icmr_v` = 포트 창 교집합 폭(v0.3.7, 필수 2): 기대값 = 정의 문장 min_p hi_p − max_p lo_p(test 작성자가 손 회로 포트 전압에서 계산) -- c = (2, 2) `declared` 손 회로에서 m 폭(hi − lo of `icmr_coord`)을 내는 변형 red(값 1/2), 두 포트 창이 어긋나는 DC 닫힘 손 회로(V_os 있음)에서 교집합 폭 < 각 포트 폭이고 m 폭을 내는 변형 red, 빈 교집합 → 음수 폭 그대로(0으로 자르는 변형 red); 차동 출력 + 미선언도 같은 닫힘(옛 `feedback_config_undeclared` ICMR 갈래 → 값이 나옴), 출력 공통모드를 벤치가 묶지 않음(넷리스트에 출력 CM 원 없음), 포트별 `tf_bench(port, NodeV(o))` 4회로 짝을 정함(두 출력의 반전 입력이 같으면 `inverting_port_undetermined`); (c) `core/test_range_confirm.py` **정의 불능 끝**(DR-20 P10): `{undefined: true, record_id}` 지목에서 `record_id`가 없는 기록·다른 `range_input_fp`의 기록·그 metric의 범위 결과가 아닌 기록을 가리키는 변형 → 각각 `range_pointer_rejected`(`check = record`, `point_id: null`); 검사 (1)을 통과한 정의 불능 끝은 (2)~(4)를 하지 않음(점 검사 함수 호출 0); `{undefined: true, reason: …}`(옛 꼴)·`reason` 키를 더한 지목 → E5(`confirmed_range_shape`); 통과한 정의 불능 끝의 `range_final.source.<end>` = 입력 지목과 같은 `{undefined: true, record_id}`(`null` 아님)이고 그 끝을 읽는 metric은 정의 불능; ICMR 정의 불능 끝 → 그 방향 슬루 `slew_step_end_undefined`(OP-10 행); `O/` 안 `confirmed_range`·`range_final`의 `departed`·`reason` 값 칸 `git grep` 0건(gain-budget N6.20 완료 조건 (iii)의 오라클 쪽), `end_cause` 값 ∈ {`rail`, `rail_filter`, `stage1`}만; (v0.3.5, 검증 M2) compare JSON의 `sim_ref.sha256`과 다른 sim.json(또는 없음) → 검사 (1) `record` 거부, OP-3 판부터 compare JSON에 `summary.u6` 사본 없음(보고서는 `sim_ref`로 읽음 -- X-R5 확인 뒤) |
| (**v0.4.0 삭제 -- DV-19 소멸(O-115), 만들지 않음**; 옛 행 기록) (v0.3.8) 10 정의 대조 -- OP-5 (e) | `core/test_swing_icmr_def.py`(시뮬레이터 호출 0, stub 어댑터) | test 작성자(정의 = gain-budget v6.26 N3.8 문장에서 기대값) | 계획 v0.6.15 DR-23 (2)·O-80 R2: (i) 단일 출력 + 두 입력(MOS gate에만 물림 -- v0.3.9 둘째 커밋 DUT 조건, 검증 N1) + `measure_feedback.kind = declared`·`feedback_passives` = Cf(출력–in−)만(DC 전도 원소 없음 → (0) '없음') → ICMR `icmr_feedback_dc_absent`(`detail.output` = 그 출력 넷), 시뮬레이터 호출 0 (ii) 같은 선언에 출력–반전 입력 `resistor` 하나를 더한 변형(Rf∥Cf) → 거부 안 됨(2단계 (a); v0.3.9 -- 옛 '`Resistor` 하나를 더한' 문언은 저항 위치를 정하지 않아 경로 판정에서 모호, 아래 'OP-5 (0)' 행) (iii) 단일 입력(`dc_sweep.excite` 키 1개) + 단일 출력 + DC 전도 원소 없는 선언 Cf → 거부 안 됨(2단계 (d) 먼저, 회로 그대로, 판정 미호출) -- 갈래 순서를 (e) 먼저로 바꾼 변형 red (iv) 차동 출력 + 두 출력 모두 'DC 되먹임 없음'(입력은 MOS gate에만) → 이 코드 아님(2단계 (c)) |
| (v0.3.9) 10 정의 대조 -- OP-5 (0) DC 되먹임 판정 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** `core/test_dc_feedback_judgment.py`(시뮬레이터 호출 0, stub 어댑터; 파일 이름 **미확인** -- test glob 충돌 미검사) | test 작성자(정의 = gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' 문단의 예에서 기대값; 피검 함수로 기대값을 만들지 않음) | 계획 v0.6.16 DR-24·사용자 결정 O-82 -- **공통 DUT 조건**(v0.3.9 둘째 커밋, 검증 N1): 단일 출력·두 입력(in+, in−), 레일 vdd·gnd, `measure_feedback.kind = declared`, 차동쌍 입력 DUT -- **in+·in−는 MOS gate에만 물림**(그래서 DUT 안에서 입력 넷으로 들어오는 엣지 없음; 출력은 MOS drain), `/sources`는 꼬리 전류원(`kind = "current"`, 꼬리 넷–gnd)만, `/bias_voltages`는 게이트 전용 넷만. 각 toy의 '선언'은 `/feedback_passives`, 나머지 소자는 `/passives`에만: (i) R(출력–in−) 선언 → '있음' → 2단계 (a) (ii) Cf(출력–in−) + Rb(in−–레일) 둘 다 선언 → '없음' → (e) `icmr_feedback_dc_absent` -- 종류 판정(DC 전도 원소가 있으면 '있음')으로 바꾼 변형 red (iii) R(in−–레일)만 선언 → '없음' → (e) -- 종류 판정 변형 red (iv) T망: R1(출력–X)·R3(X–gnd)는 `/passives`에만, R2(X–in−)만 선언 → '있음'(경로는 DUT DC 망 전체) → (a) -- 선언 소자만 보는 변형 red (v) Rf∥Cf(출력–in−) 선언 → '있음' → (a) (vi) **R 분압**: R1(출력–in−)·R2(in−–gnd) 선언 → '있음'(출력–R1–in−, gnd는 끝점 아닌 경유만 금지) → (a) -- gnd 경유 금지를 끝점까지 넓힌 변형 red (vii) **공통 게이트 입력 DUT**(O-83 N4, 'DC 되먹임 있음' -- 정의대로): in−가 입력 MOS의 **source**에 물리고 출력이 그 MOS drain(또는 그 drain에서 MOS d↔s 사슬로 닿음), Cf(출력–in−)만 선언 → '있음'(출력 → drain↔source → in−, DUT 채널 경로) → (a) -- '용량만이면 없음'으로 가르는 변형 red (viii) **이상원**: Cf(출력–in−) 선언 + `/sources`에 `kind = "current"`(출력–in−) → 전류원은 엣지 아님 → '없음' → (e); 같은 Cf 선언 + `/sources`에 `kind = "voltage"` 하나 → `dc_feedback_judgment_undefined`(`why = element_unsupported` -- v0.3.10 이름, 옛 `voltage_source`), 시뮬레이터 호출 0 -- 전압원을 엣지로 넣는 변형 red (ix) `/bias_voltages` 넷을 R 단자에도 물린 입력 → `why = bias_not_gate_only`. 공통 단언: 판정이 `.tf`·`.op` 요청보다 먼저(stub 호출 기록 0), 경로가 레일·끝점 아닌 입력 포트·`/bias_voltages` 넷을 중간 마디로 지나는 변형(예 출력–R–vdd–R–in−)은 '없음' -- 경유 금지를 뺀 변형 red; MOS 엣지 방향 단언(gate→drain만 있고 drain→gate 없음: 출력이 MOS drain이고 in−가 같은 MOS gate인 꼴만 있으면 '없음'). |
| (v0.3.10; v0.3.10 둘째 커밋에서 행 나눔, 검증 N6) 10 정의 대조 -- OP-5 (0) 차동 결합 | `core/test_dc_feedback_judgment.py`(같은 파일, 시뮬레이터 호출 0; 이름 **미확인**) | test 작성자(정의 = gain-budget v6.28 N3.8 '차동 출력' 규칙에서 기대값) | (DV-21 닫힘 -- 계획 v0.6.17 DR-25 (1)) **차동 출력 결합 toy 둘 -- 위 행의 공통 DUT 조건(단일 출력·꼬리 전류원)과 다른 별도 DUT**(손 판정은 아래, test 작성자가 정의 문단에서 기대값을 씀): 공통 DUT = 의사 차동(pseudo-differential) -- 입력 MOS M1(gate in_a, drain o_b, source gnd)·M2(gate in_b, drain o_a, source gnd), 부하 PMOS M3(drain o_b)·M4(drain o_a), 둘 다 source vdd·gate = `/bias_voltages` 넷 vb(게이트 전용), 꼬리 넷 없음(입력 MOS source가 레일). 선언 = **비대칭**: Rf(o_a–in_b, resistor)와 Cf(o_b–in_a, capacitor). (x) **출력이 DC로 이어지지 않음** → 정의 불능: o_a → Rf → in_b(절단 넷) = '있음'; o_b의 엣지는 M1 d↔s(→ gnd, 레일이라 경유 금지)·M3 d↔s(→ vdd, 경유 금지)뿐이고 Cf는 엣지 아님, vb는 gate→drain으로 나가기만 함 → '없음'; 갈림 → `dc_feedback_judgment_undefined`(`why = differential_split`, `present = [o_a]`, `absent = [o_b]`), 시뮬레이터 호출 0 -- 갈릴 때 한쪽 판정을 고르는 변형(o_a 기준 '있음' → (a), o_b 기준 '없음' → (c)) 둘 다 red (xi) **대조: CMFB 저항이 출력을 잇는 같은 비대칭 선언** → 정의됨: (x)에 `/passives`(선언 아님) Rc1(o_a–cm)·Rc2(o_b–cm)을 더함(cm = 자유 넷, CMFB 감지점 -- 레일·입력 포트·bias 넷 아님). o_a → Rf → in_b = '있음'; o_b → Rc2 → cm → Rc1 → o_a → Rf → in_b = '있음'; 두 판정 같음 → (0) '있음' → 2단계 (a)(선언 그대로), 사유 없음 -- cm을 경유 금지로 잘못 넣은 변형('없음' 갈림 → 정의 불능)은 red |
| (v0.3.8; 둘째 커밋 M1 -- 옛 이름 'OP-3 C10 `.ic`') OP-4 C10 `.ic` | `core/test_stab_benches.py`(stub), `adapters/ngspice/test_netlist_text.py`의 C10 몫 | test 작성자 | 계획 v0.6.15 DR-23 (1)·계획 OP-4 행(C10 코어화)·N4 OP-4(C10 판정 불변) -- `Tran.ic`·`tran_ic_bias_only`를 만드는 card·소비자 = OP-4 C10: (i) `stab_benches`의 과도 요청이 choke 노드·kick 출력 노드 초기 조건을 `Tran.ic` 하나로 담음(다른 초기 조건 칸 없음) (ii) `tran_ic_bias_only` 없는 stub → `adapter_capability_missing`(`detail = "tran_ic_bias_only"`), 시뮬레이터 호출 0 (iii) ngspice 어댑터 넷리스트 = `.ic v(<넷>)=<V>` 줄 + `uic` 없는 `tran` 제어 줄(옛 `O/oracle_netlist.py:625`·`:720`·`:765`와 같은 꼴) -- `uic`를 붙인 변형 red. 옛 C10 결과와의 동일성은 '3 동일성'(N4 OP-4 행 'C10 판정 상태·창 수 등 -- 기존 과도 fixture 판정 불변')이 잰다. 파일 이름은 **미확인**(OP-4 test 파일 목록에서 확정, test glob 충돌 미검사) |
| (v0.3.0) 10 정의 대조 -- OP-10 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** `core/test_slew_def.py`(stub은 능력 없음 거부), `adapters/ngspice/test_slew.py` | test 작성자, 검증자 | §21.6: SR = I/C 손 회로(방향 둘), `measure_feedback.kind = unity_follower` → `beta_default = true`, 결과 `slew.rise`·`slew.fall` ↔ measure 두 이름(§11.6), (v0.3.3) 계단 끝 = `confirmed_range.icmr` 지목(네 검사 깨진 변형 넷 → `range_pointer_rejected` `check`별 red, 지목 정의 불능·칸 없음 → `slew_step_end_undefined`, 전압 값 칸을 넣은 입력 → E5), `slew` 칸 없음 → `slew_undeclared`, 계획 불가 → `tran_plan_undefined` (v0.3.8, 계획 v0.6.15 DR-23 (1) -- v0.3.6 '시작 동작점 손 회로'(닫힘 원소 0개·t = 0 해 = 닫힘 `.op` 해·닫힘이 계단 응답에 남지 않음·`uic` 변형·능력 없는 stub)는 **gain-budget card AP-1 몫으로 옮김**, OP-10 test에서 뺌; 옛 문장 history v0.3.8) **측정 구성 거부**(시뮬레이터 호출 0): (i) 선언 구성이 모든 입력 포트에 닿음(current_reuse 꼴 Cf1(Vom–Vip)·Cf2(Vop–Vim)) → `feedback_config_undeclared`(`why = input_network_step_deferred` 하나 -- (c)에도 해당하지만 첫 갈래만 기록, O-89 (2)), 입력 포트에 계단 원을 거는 변형 red (ii) 차동 출력 + DC 되먹임 없는 선언(§21.2 2단계 (0) 두 출력 모두 '없음'; v0.3.10 둘째 커밋 문언, 검증 N1 -- 옛 '용량만 선언') + 구성이 닿지 않은 입력 포트 있음 → `why = start_op_deferred`(과도 벤치·`Tran.ic` 요청 0개 단언) (iii) 차동 출력 + 미선언 → `why = differential_undeclared` (iv) 단일 출력 + DC 되먹임 없는 선언(§21.2 2단계 (0); v0.3.9 둘째 커밋 문언) → 같은 입력의 ICMR이 `icmr_feedback_dc_absent`라 확정 끝이 없음 → `slew_step_end_undefined`(그 경로는 이미 위 '계단 끝' 단언과 같은 꼴). |
| (v0.3.0) 10 정의 대조 -- OP-11 | `core/test_power.py` | test 작성자 | §21.7: Σ V²/R 손 회로(양·음 레일), 레일 전류 하나 없음 → `power_undefined`(부분 합 없음), 부호 반대 변형 실패, `offrail_nonzero` 표시, `rail_current_A`·`supply_current_A`는 기준선 동일(정의 그대로) |

**v0.4.0 test 행**(위 표의 옛 OP-5 행과 다르면 이 표가 이김):

| 완료 조건 | test 파일 | 기대값 작성 | 판정 |
|---|---|---|---|
| (v0.4.0) 입력 계약 -- OP-3 OP-B3 | `test_input_contract.py` | test 작성자 | 선언 빠진 게이트 전용 넷 toy → `oracle_input_schema_invalid`(`rule = bias_gate_nets_mismatch`, base = 예측값 대체 -- red), 게이트 전용이 아닌 넷을 선언한 변형 → 같은 거부, `oracle_netlist` 대체 갈래 `git grep` 0 |
| (v0.4.0; v0.4.8: 상위 SF-1 범위 9 통합 병합의 오라클 커밋 몫, A-80 J-6) OP-3 DUT 저항 소자 줄 | `core/test_resistor_line.py` | test 작성자(기대값 = 정의) | 넷리스트 줄(ngspice 0): 이상 R + C_par/2 쌍, 측정 부하 원소는 이상 R, capacitor에 칸 → 거부. **RC 손회로 오라클 극점 = 1/(R·(C_load + C_par/2)) 실측 = OP-5 판정 묶음**(v0.4.10, 위임 A-94) |
| (v0.4.0) 10 정의 대조 -- OP-5 판정 한 단계 | `core/test_conduction.py` | test 작성자 | §21.1 깨진 변형 전부; 다리 규칙 toy: 직렬 MOS 다리 → 집합에 듦, 고리 안 MOS → 안 듦, `off` 소자와 직렬 → 듦, DC 경로가 측정 부하 저항뿐인 MOS → 집합에 안 듦 |
| (v0.4.0) 10 정의 대조 -- OP-5 servo ICMR | `core/test_swing_icmr_def.py` | test 작성자 | 손 회로 차동·단일 입력: V_cm 좌표 세 metric 값, servo 부호 = `.tf`(role 이름을 뒤바꾼 변형도 같은 값), 고정 오차 초과 변형 → `icmr_output_lock_violated`, 입력 셋 → `icmr_input_ports_unsupported`, 선택 상대 항 칸 → E5 거부; 단일 입력: 벤치에 `Vcvs` 0, V_cm 폭 = 손 해, servo를 건 변형 = 폭 0으로 실패 |
| (v0.4.0) 10 정의 대조 -- OP-5 DR-28 | `core/test_offset_sys.py` | test 작성자 | §21.4 toy, `.dc` 요청 0 단언, 엔진 U-107 toy와 같은 판정, swing 블록 없는 입력에서도 같은 판정 |
| (v0.4.0) OP-B1 상한 | `core/test_bounds_derived.py` | test 작성자 | 상한 도달 toy마다 fail-closed 사유, 네 이름 + `NYQUIST_K_MAX` `git grep` 0, N4 비교(상한에 닿지 않은 입력 비트 동일); noise: 완만해지는 꼬리 → 거부, 한 극 꼬리 → 통과, T ≤ ε·I 입력 → f_hi 불변; 격자 판정 눈금 = reltol, 옛 입력 격자 점 수 불변 |
| (v0.4.0) 10 정의 대조 -- OP-10 DR-27 | `core/test_slew_def.py` | test 작성자 | 해석해 슬루 회로: 20~80 % 기울기, 피드스루 가장자리 변형이 값을 바꾸지 않음, 계단 = 같은 덱 범위, 범위 정의 불능 → `follower_range_undefined`, 선언 step 범위 밖 → `slew_step_out_of_range`, 무릎 보고 칸, 끝 시각 식, 제약 없음 → `slew_required_undeclared`, `declared` → `beta_undefined`, 단일 출력 + DC 되먹임 없음 → `start_op_deferred`(`.dc` 요청 0) |
| (v0.4.0) OP-7 | `test_bin_rule_run.py` + 검증자 기준선 1회(13회로는 LA-1, A-84 B-4) | test 작성자·검증자 | §16 완료 측정 |

### 18.2 옛 test 이전표

(v0.4.8, A-80 D-6, 임시 규칙 O-229 기간, **원래 취지와 다름** X-R13) OP-2 + OP-3에서 아래 표의 OP-3 몫은 toy·독립 기준 이동·순수 수학 import 교체로 줄인다. 나머지 파일은 사유와 소유 card를 적어 수집에서 빼고 통과로 세지 않으며, 이전·폐기는 LA-1 재점검에서 정한다.

(v0.4.9, A-84 C-5) OP-5 이전 범위 = `test_oracle_noise.py`, `test_oracle_offset_mc.py`, `test_oracle_swing_icmr.py`, `test_oracle_conduction.py` + `test_oracle_compare.py`의 합격 사다리·PMOS 크기 규칙. 함수별 처리 = card `20261104-op5` 이전표. 측정 정의를 지키는 test는 빠뜨리지 않고, 정의가 소멸한 함수는 함수별로 원인을 적는다. 나머지는 수집 제외 유지.

| 옛 파일 | 처리 |
|---|---|
| `test_oracle_c10_stability.py`, `test_oracle_u6_stability.py`, `test_oracle_transient.py` | 수학 부분 → `core/test_stability.py`(TimeSeries 입력). 넷리스트 텍스트 단언 → `adapters/ngspice/test_dialect_stability.py` |
| `test_oracle_netlist.py`, `test_oracle_netlist_topology.py`, `test_oracle_iso.py`, `test_oracle_z1.py`, `test_oracle_c27_loop_defs.py`, `test_oracle_junction_cap.py`, `test_oracle_conduction.py` | IR 단언 → `core/test_build_*.py`. 방언 줄 단언 → 어댑터 test |
| `test_oracle_rout.py`, `test_oracle_ratio_db.py`, `test_oracle_cm_loop.py`, `test_oracle_loop_singular.py`, `test_oracle_simulate_pm_crosscheck.py` | 수학 → 코어, 실행 → 어댑터 |
| `test_oracle_simulate.py`, `test_oracle_simulate_cache.py`, `test_oracle_run.py` | 어댑터 실행·캐시(§9) test로 다시 씀 |
| `test_oracle_noise.py` | 수학 → 코어, 기여 이름 대응 → 어댑터 |
| `test_oracle_offset_mc.py` | sky130 변수 집합 기대값(직접 섭동) 삭제. 네이티브 MC·진단·MC 수학 test로 다시 씀. (v0.3.0) `.ac` 첫 점 A·`1e-3` 실수 판정을 단언하는 test는 지우고 `criteria_weakened`가 아니라 `.tf` A test(§18.1 '10 정의 대조 -- OP-5')로 대체한다(정의를 바꾼 칸, OP-5) |
| `test_oracle_swing_icmr.py` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.0 다시 씀, DR-17) 옛 servo 출력 목표 훑기·ICMR 출력 고정·'수렴 안 함 = 포화 아님'·`off_current_A` 문턱을 단언하는 test는 정의를 바꾼 칸이라 보존하지 않는다. 경계 괄호 수학(`_window`·`edge`의 좁히기)은 `core/test_swing_icmr_def.py`로 새 정의(§21.2)에서 다시 쓰고, `OpSweep` 실행은 어댑터 test로. 옛 test가 쓰던 손 회로는 기대값을 새 정의 문장에서 다시 계산한다(OP-5) |
| `test_oracle_compare.py`, `test_oracle_compare_device_tol.py`, `test_oracle_diagnosis.py` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어로 이동(함수 이동만, OP-3). (v0.3.0) 그 가운데 C23 전도 문턱(`off_current_A`, ε = 1)을 단언하는 test는 OP-5가 §21.3 봉인 9 식 test로 바꾼다(정의를 바꾼 칸) |
| `test_oracle_input_schema.py` | 새 형식 + 옛 형식 거부 test로 다시 씀. (v0.3.0) 위치는 §18.1 'OP-3 입력 계약' 행(`test_input_contract.py`), card = OP-3(DR-10i) |
| `test_legacy_adapter.py`, `test_legacy_testbench.py` | (v0.2.5 고침, 계획 v0.6.3.1 OP-2·OP-3 행, LT-1 순서 3) 이 기능이 다시 쓰지 않는다. LT-1 순서 3이 `test_legacy_testbench.py`와 `legacy_slow` 3함수 5항목을 지우고, `test_legacy_adapter.py`의 기본 실행 6함수를 고정 자료 test 파일로 옮긴다. 그 가운데 지금 코드에 묶인 둘만 이 기능의 card가 같은 변경에서 바꾼다: 스키마 적합 test → **OP-3**(v0.3.0, DR-10i -- O-14 (4) J-1 (나))이 '옛 형식이라 거부(`oracle_input_format_old`)' test로, 넷리스트·루프 넷리스트 재생성 일치 test → OP-3이 지우고 `criteria_weakened`에 올림(같은 비교 = 검증자 N4-3). 고정 자료만 읽는 test(finger 규칙, W 자기모순, feedback_passives)는 그대로 둔다. LT-1 순서 3이 먼저면 옮긴 파일에서, 아직이면 `test_legacy_adapter.py`에서 바꾼다 |
| `conftest.py`의 `--run-legacy`·`legacy_slow`(S-27) | 이 기능이 고치지 않는다. LT-1 순서 3이 지운다(§15.4) |
| `conftest.py`의 `run_spice`·`independent_cs/fb`, `u6_toy5t.py`(손 넷리스트 독립 기준) | `O/tests/adapters/ngspice/` 아래로 옮겨 그 어댑터의 독립 기준으로 쓴다(삭제하지 않음). (v0.2.6) 경로를 `O/tests/` 아래로 명시했다 -- 어댑터 패키지 `O/adapters/ngspice/`에 두면 어댑터 지문(§0)에 들어가 test 수정이 능력 기록을 무효로 만든다 |
| (v0.2.6) `conftest.py`의 옛 형식 입력 생성기(`process_block`, `testbench_block`, `cs_input`, `rc_input`, `fb_input`, S-34) | **OP-3**(v0.3.0, DR-10i)이 새 형식으로 다시 쓴다(§15.4). 이름·인자 유지 |
| (v0.2.6) `conftest.py`의 `make_lut` | OP-3이 meta에 test 기술자와 맞는 `model_files_sha256`을 쓰게 고친다(§15.4) |
| (v0.2.6) 캐시 단언 test 넷: `test_oracle_simulate_cache.py:57-127`, `test_oracle_ratio_db.py:287`, `test_oracle_rout.py:559, :575`, `test_oracle_c10_stability.py:832, :1321-1339`(S-32) | 캐시 상태 칸은 같은 모양으로 남는다(§11.5 '옛 상태 칸'). 단언 대상 값은 `RunStatus.cache_state`에서 온다. 앞 셋은 OP-3(본 회로·β 루프·ratio·rout 실행), 넷째는 OP-4(안정성)가 실행 test로 다시 쓰며 같은 단언(첫 실행 miss, 둘째 hit, 캐시 없음 None, 키 구성 §9가 바뀌면 miss)을 둔다. 옛 캐시 디렉터리는 재사용하지 않는다(§9) |
| `O/smoke/` 스크립트 넷(S-25) | 기록 스크립트라 test가 아니지만 같은 원칙으로 §15.4 표대로 처리한다 |

* test는 다시 써도 된다는 사용자 방침에 따라 텍스트 단언은 보존하려 하지 않는다. 독립 기준(손 넷리스트)만 지킨다.

### 18.3 연속 칸 분해능 식(G-6)

* 값 x(기준선), y(새)에 대해 |y − x| ≤ reltol·max(|x|, |y|) + abstol_q를 쓴다. reltol·abstol_q는 그 실행의 `Resolution`(입력 options 또는 어댑터 기본값)이고, q는 양 종류(전압 = vntol, 전류 = abstol)다. (v0.2.5, S-28) 전류의 abstol은 옛 기본값이 없으므로 비교 실행 입력 `simulator.options`의 값이거나 R6 출처로 처음 적은 어댑터 값이다. 둘 다 없으면 그 칸은 `dc_tolerance_undeclared`로 판정하지 않는다(멈추고 보고, 비트 동일만 인정하는 쪽으로 몰래 바꾸지 않는다).
* 파생 측정(dB, 위상, 교차 주파수, PM)은 옛 `data_rel_resolution`·`mp_resolution`이 이미 내는 측정 분해능을 쓴다.
* 식이 없는 칸은 비트 동일만 인정한다(기본안).
* (v0.4.0, **반복 상한 유도 -- 계획 OP-4·OP-5 행 OP-B1, X-D1, 상위 E-20**. 새 상수 없음) **끝 좁히기**: K_zoom = ⌈log_(P+1)(W0/r)⌉, §21.2. **Nyquist 세분**(OP-4): 종료 = 각 구간 편각 < π/2 또는 구간 폭 ≤ 주파수 분해능(입력 `Resolution`의 상대 분해능 × 구간 주파수). 상한 = ⌈log_2(구간 폭의 로그 폭 / 로그 분해능)⌉, 못 맞추면 `nyquist_unresolved`. **noise 상한 확장**(OP-5, OP-0 design 질문 닫음): 가정 = 적분 끝 위 PSD가 멱함수 S(f) ≤ S(f0)·(f0/f)^n으로 줄어든다. **검사**: n̂ = 마지막 격자 구간의 −d ln S/d ln f, n̂ ≥ n̂_앞 − δ(바로 앞 구간 기울기 -- 꼬리에서 완만해지지 않음. v0.4.9, A-84 C-4: δ = 2·u_S·(1/Δ_N + 1/Δ_(N−1)), 등간격 파일 진폭 d자리면 ≈ 8u/Δ, 유도 정본 = 계획 OP-5 행, u_S = `NoiseResult.density.resolution.data_rel`을 어댑터 `read`가 냄)이고 n̂ > 1이어야 한다. 어기면 상계 불능 `noise_tail_bound_undefined`(fail-closed -- 값 없음). 꼬리 상계 T(f0) = S(f0)·f0/(n̂ − 1). ε = r²(r = `noise.rel_resolution`, I는 V² 적분 -- 옛 판정 `S·f ≤ r²·cum`, `O/oracle_noise.py`와 같은 눈금; v0.4.0의 'ε = r'은 작성자 오류, n̂ = 2이면 T = 옛 상계). **T(f0) ≤ ε·I(f0)이면 확장하지 않고 f_hi = f0(격자 불변, N4 비트 동일 대상 -- 옛 `top_extensions = 0`이고 이 부등식도 참인 입력)**. 넘을 때만 닫힌 식 f_hi = f0·(S(f0)·f0/((n̂ − 1)·ε·I))^(1/(n̂ − 1))로 직접 정하고, 그 f_hi로 다시 재서 검사를 반복하지 않는다(재측정 뒤 부등식이 틀리면 같은 사유로 거부). **격자 밀도**: |I_k − I_(k−1)| ≤ reltol·I_k까지 격자를 2배(옛 판정과 같은 눈금 -- ε = r²는 꼬리 판정 전용, v0.4.2 R2), 상한 = max(0, ⌈log_2(`noise_points_per_decade_max` / 시작 decade당 점 수)⌉) -- 최대 점 수는 어댑터 능력(비용 선택, v0.4.9 decade당, §8.3), 못 맞추면 `noise_grid_unresolved`. **작성자 판단**: 멱함수 꼬리 검사 꼴과 닫힌 식(계획은 '가정과 검사는 design 질문'만 정함; 원문 쪽 없음 -- 식 유도. 고주파 영점·피킹이 격자 밖이면 가정이 틀릴 수 있음, 미측정).

---

## 19. 열린 항목

### 19.1 오케스트레이터 기본안(이 문서가 정한 세부, 사용자가 바꿀 수 있음)

| ID | 내용 | 절 |
|---|---|---|
| B-1 | 파일 분할과 이름(`core/*.py` 목록, `adapters/ngspice/*`, `descriptors/`, `capability/`) | §3.1 |
| B-2 | 옛 진입점 CLI를 `oracle_run` 하위 명령으로 합침(능력 확인 `oracle_run capability` 포함). **결정(O-3, X-D2 수용)** | §3.1 |
| B-3 | 테스트벤치 원소 IR 이름 `tb:<용도>:<대상>` | §4.1 |
| B-4 | 스키마 이름 `oracle_pdk_descriptor/1`, `oracle_capability/1`, `oracle_diagnostic/1`, `lut_bin_rule/1`, 저장 위치 | §10, §12.4, §13, §16 |
| B-5 | `simulator.options` 키 검증은 어댑터 | §11.1 |
| B-6 | LUT 메타·입력 모두 온도·코너가 없으면 `oracle_condition_missing` | §11.2 |
| B-7 | (v0.2.4 철회) 차동 이득 실수 판정 = `data_rel` 유도. 계획 v0.6 O-6 D-c로 `1e-3` 유지(NFR-P2 예외)가 정해져 이 기본안은 없어졌다. (v0.3.0) 그 `1e-3`도 O-43 D1 (d)로 지워졌다(`.tf`, §21.5) | §14 |
| B-8 | 계획이 다루지 않은 반복 상한 상수 다섯은 그대로 옮기고 표시만. **결정(O-3, X-D1 수용, 계획 NFR-P2 허용 예외 목록)** | §14 |
| B-9 | X-13 test를 엔진 suite 쪽(`E/tests/` 아래 읽기 전용 test)에 둠. **계획 v0.5.1 완료 조건 8a 예외에 따름**. (v0.3.0, DR-14·DR-16) 비교 값 = 파일 바이트 LF 정규화 재측정(엔진 `decl_sha256`과 견주지 않음 -- SH-1 전 raw, 뒤에도 엔진 실행 값이라 import 필요), 갱신 값 = 다시 잰 LF 정규화 sha256 | §18.1 |
| B-10 | 식이 없는 연속 칸은 비트 동일만 | §18.3 |
| B-11 | (v0.2.5 **기본안 아님 -- 계획을 따름**) v0.2.4 기본안(기술자 `requires` + 어댑터 선언)은 계획 v0.6.3 X-20(OQ-3 승인 L-3)으로 대체됐다: 판정 요구 = 코어 고정, 표본 수·시드·실행 방식·표본 성질 = 어댑터 능력, 기술자 = PDK 데이터만. 기술자 `requires` 칸은 지웠다 | §8.3, §10.4 |
| B-12 | (v0.2.4) 새 스키마 `process`는 정의 밖 키를 거부(`additionalProperties: false`) | §11.1 |
| B-13 | (v0.2.5 **철회**) `legacy_adapter` finger 분할 기준 폭 규칙. 계획 v0.6.3에서 `legacy_adapter`를 이 기능이 고치지 않으므로(LT-1 순서 3이 삭제) 대상이 없다 | §11.4 |
| B-14 | (v0.2.4) 손 모델 픽스처 위치·이름 `O/tests/fixtures/hand_model/hand_model.oracle_descriptor.json` | §3.1, §12.7 |
| B-15 | (v0.2.4, v0.2.5 고침) 오류 코드 `descriptor_geometry_undeclared`, `mc_distribution_inline`(닫힌 키 집합 판정), `mc_distribution_unlocated`, `descriptor_schema_invalid`, `lut_aux_input_mismatch`, `lut_file_roles_invalid`의 이름과 `detail` 형식, 분포 값 원본 sha256 불일치를 `pdk_descriptor_stale`로 내는 것. `geometry_unit_unsupported`는 지우고 `adapter_capability_missing`·`adapter_calibration_missing`으로 합침 | §7 |
| B-16 | (v0.2.4) 기하 단위 적용 방법 이름 `global_directive`·`instance_numbers`, 전역 지시 영향 칸 선언 `global_geometry_directive.affects`·`power` | §8.3, §10.6 |
| B-17 | (v0.2.4, v0.2.5 확장) 결과 칸 이름 `ngspice_rc` → 같은 자리 `status`(`RunStatus`), `ngspice_runs` → `sim_runs`, compare 메시지 일반화 문구, 경로별 `None` 대응(실행 안 함 = `status: null`, 시간 초과 = `rc: null` + `timed_out`), 표본마다 별도 실행인 MC의 `status.rc` 묶음 규칙, `method` 값은 어댑터가 내고 N4 비교 제외 | §6, §11.5, §15.1 |
| B-18 | (v0.2.5, **v0.2.6 고침**) 기술자 `lut_record_root` = 기존 정본 `A/lut_v2_location.json` `pdk_root`를 경로 + sha256으로 참조(새 출처를 만들지 않음, 그 파일 형식의 env/default 규칙, LUT meta 절대 `pdk_root`를 읽지 않음), 교차 검사 = §7.2 8단계 `lut_record_root_mismatch`. 계획 G-17 '보조 입력 대조의 PDK 뿌리 출처' | §7.2, §10.2, §12.5 |
| B-19 | (v0.2.5) 기존 LUT 역할 옆 선언의 위치 `O/descriptors/lut_file_roles/<생성기 sha256 앞 16자>.lut_file_roles.json`, 형식 `lut_file_roles/1`, 묶는 키 = 슬라이스 meta `generator_sha256` + 기록 (경로, sha256) 쌍, 기술자 `lut_file_roles`가 참조. 계획 G-17 | §3.1, §10.2, §12.5 |
| B-20 | (v0.2.5) 삭제 모듈 소비자 처리: `cm_loop_*` 셋은 import를 코어로 바꿈(OP-3), `u6_selfchecks.py`는 삭제하고 점검 내용을 새 test로 다시 씀(`U6_REPORT.md`는 기록으로 남김), `measure_wall_s_per_window.py`는 어댑터 보정값 측정 도구로 이동(OP-4). **(v0.2.6) u6 삭제는 사용자 승인됨(O-10).** 삭제 card는 OP-5가 아니라 OP-3으로 고쳤다(import하는 옛 실행 모듈을 처음 지우는 card, §15.4) | §3.1, §15.4 |
| B-21 | (v0.2.5) 새 LUT meta의 역할 칸 이름·모양 `model_files_role = {<상대 경로>: role}`(기존 `model_files_sha256` 모양은 그대로). 계획 G-17·OP-8 | §12.5 |
| B-22 | (v0.2.5) 실행 전 검사 순서(§7.2)와 `mc_method_unsupported`의 `side` 구분 | §7.2 |
| B-23 | (v0.2.5) 오류 단위(벤치 `RunStatus.error` 대 요청 `.error`)와 '회복된 경고 = 결과 존재로 판정' 규칙 | §6, §7.1 |
| B-24 | (v0.2.6) 오류 대응표에 증거 단계 표시('기준선 증거' / '주입 증거')를 두는 것. 계획 X-23의 단계 규칙은 방언 토큰 목록에 대한 것이고, 오류 대응표에 같은 방식을 쓰는 것은 이 문서의 기본안이다 | §7.1, §18.1 '오류 대응' |
| B-25 | (v0.2.6) 보정값 측정 도구 폴더 이름 `O/adapters/<이름>/calibration_tools/`(계획 v0.6.5 '폴더 이름은 design'), 어댑터 지문 제외 목록 = {`calibration.json`의 `wall_s_per_window` 키, `calibration_tools/`, `__pycache__/`}, 그 밖 어댑터 패키지 파일은 종류와 무관하게 지문에 넣음 | §0, §3.1, §3.2, §8.3 |
| B-26 | (v0.2.6) OP-1a (b) 재계산 스크립트와 (c) S-22 2행 스크립트를 한 스크립트로 둠, 선택 대조 (d)는 `run_ngspice` 이름 교체 경로 | §13.2 |
| B-27 | (v0.2.6) 결과 칸 대응: 실행 전 반환 경로를 사유 대응표로 가름, offset_mc 옛 rc 비교 제외 + `n_failed`·`sample_status`, `RunStatus.cache_state` 넷 값과 캐시 상태 표 분리(C21), 옛 `log`·`log_errors`·`op_ok`·`skipped` 대응, 막힘은 유무·개수만 비교, 새 오류 코드 `lut_record_root_mismatch`·`mc_identity_lost`·`lut_location_decl_invalid`·`adapter_fingerprint_unavailable` | §6, §6.1, §7, §11.5 |
| B-28 | (v0.2.6, 같은 판 후속에서 고침) 어댑터 지문의 묶음 = 상대 POSIX 경로 정렬 (경로, sha256) 쌍, 파일·`calibration.json` 읽기 실패 = 거부, 정규 JSON 직렬화 규칙(능력 기록 `record_id`와 공용). 파일 집합은 기본안이 아니라 **계획 v0.6.6 문구**(디스크의 모든 파일 − 닫힌 제외 목록)다. 'git 추적 파일 기준'과 '추적 판정 불가 시 거부'는 **철회**(오케스트레이터 결정, 계획 문구 복귀) | §0, §7, §12.4 |
| B-29 | (v0.3.0, **결정 대기** -- X-D7과 함께 사용자 결정) 입력 키 집합을 모든 객체 층에서 닫음(`provenance`만 열림). 근거 fail-closed + G-18 확장 칸의 병합 시점 강제, 기준선 영향 0(S-44). 원래 취지와 다름 X-D7 | §11.0, §11.1 |
| B-30 | (v0.3.0) 입력 파일 경로 칸의 상대 경로 기준 = 입력 파일 폴더 | §11.1 |
| B-31 | (v0.3.0) 생산자 이름·스냅샷 지문 같은 출처 기록은 최상위 `provenance`(열린 출력 전용 칸)에 적음 | §11.1, §11.4 |
| B-32 | (v0.3.0) `process.lut_files` = 소자 DC 동작점을 정한 LUT **슬라이스** 파일(계획 N3.5 '그 kind에 쓴 LUT 슬라이스들'). 용량·잡음·mismatch 결합 파일은 넣지 않음(모델 동일성은 DC 슬라이스 기록으로 정해지고, 결합 파일은 생성기가 달라 역할 옆 선언이 따로 필요해짐, S-38) | §11.1, §12.5 |
| B-33 | (v0.3.0, **결정 대기** -- X-D8과 함께 사용자 결정) 거부 때 `<circuit>.reject.json`(`oracle_reject/1`) 하나를 씀. 원래 취지와 다름 X-D8 | §11.7 |
| B-44 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.1) 1단계에 FAIL이 없고 2단계 대기 소자가 있을 때 오라클 `summary.verdict = "PENDING_CONDUCTION"`, 반환 코드 0(계획 N3.9 '오라클 결과만으로 PASS를 내지 않는다'의 표현 방식) | §11.7, §21.3 |
| B-45 | (v0.3.1; **사용자 결정 O-58 B-45로 확정**, v0.3.2 정정) 공칭 점 차 거부(`sweep_end_unresolved`, `why = nominal_shift`)와 칸 `nominal_output_shift_V`는 개루프 벤치를 쓰는 swing에만; ICMR은 거부도 칸도 없음(공칭 점 = 구성 벤치 y = 0 해) | §21.2 |
| B-46 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.1) 새 칸·코드 이름: `intended_region`(객체 {소자: triode \| off}), `measure_feedback`, `sweep_rezoom`, `conduction.points[]`·`stage1` 값, `seal9_two_stage`, 오류 `intended_region_mismatch`·`intended_region_unknown_device`·`measure_feedback_undeclared`·`measure_feedback_port`·`feedback_config_undeclared`·`inverting_port_undetermined`·`sweep_rezoom_bounds`·`slew_step_end_undefined`, 소자 개별 풀이 벤치 `ioff_bench`(계획이 '오류 코드는 design'으로 맡긴 이름들). (v0.3.2 이름, v0.3.3에서 기본안으로 기록) 벤치 `offset_bench`(§21.4)·`slew_bench`(§21.6)·`sweep_bench`·`tf_bench(port=)`, 판정 폭 칸 `slew_rise_v_per_s_rel`·`slew_fall_v_per_s_rel`, 결과 `slew.rise`·`slew.fall`·`slew.beta_default`·`step_end`(`lo` \| `hi`), measure 이름 `slew_rise_v_per_s`·`slew_fall_v_per_s`(정본 = gain-budget v6.21 567행, 이 문서는 인용), 범위 끝 기록 칸(`end_cause` 값 `rail`·`rail_filter`·`stage1` -- `stage2_pending` 값은 v0.3.3 둘째 커밋에서 삭제, `departed`, `rounds_cap`, `pass_point_id`·`fail_point_id` -- `x_pass`·`x_fail`·`m_pass`·`m_fail`·`resolution_r`·`range_final.*.lo/hi` 칸은 v0.3.3 셋째 커밋에서 삭제, 정본 = `conduction.points[]`), `detail.why` 값 `nominal_shift`·`nominal_not_conducting`. (v0.3.3 새 이름, 계획 G-19 '형식·오류 코드는 design') 입력 칸 `confirmed_range`(P = `{record_id, point_id}` \| `{undefined, reason}`)·`dc_sweep.input_dc`, 규칙 `confirmed_range_shape`·`dc_sweep_input_dc_ports`, 오류 `range_pointer_rejected`(`check` ∈ `record`·`stage1_pass`·`within_stage1`·`bracket`)·`input_dc_undeclared`, `slew_step_end_undefined`의 `detail.why` ∈ `pointer_undefined`·`no_confirmed_range`, 결과 `range_final`(`status = "final"`, `source`, `value`, `constraint`)·`range_input_fp`(실효 입력 지문)·`run_request`(`kind` ∈ `primary`·`rezoom`·`confirm`), 규칙 `run_request_conflict`, 기록 파일 이름 `<stem>.<kind>.<rid16>.compare.json`, 검사 단계 §7.2 2c, 코어 모듈 `range_confirm` | §7, §11.6, §11.7, §21 |
| B-34 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.1 **닫힘 -- 사용자 결정 O-50 O2**: 두 칸 모두 OP-5에서 지움) (v0.3.0, 결정 대기 -- 계획 문언 확인, 결정 전에는 지우지 않음) OP-5에서 `judge.off_current_A`도 지움(계획 문언 '옛 동작점 스칼라 `off_current_A` 입력 칸'이 judge 칸까지 포함하는지 갈리지 않음 -- 소비자가 사라지는 칸이라 같은 변경에서 지움) | §11.6, §15.1 |
| B-35 | (v0.3.0) 캐시 키의 방언 텍스트 바이트 = 어댑터가 만든 문자열(줄 끝 `\n`)의 UTF-8, 디스크 파일 바이트 아님 | §9 |
| B-36 | (v0.3.0; **대체됨** -- v0.3.1 `intended_region`(B-46), '칸이 생긴 뒤 필수·빈 값 허용' 규칙은 그 칸에 그대로) `declared_triode` 칸이 생긴 뒤에는 필수(빈 배열 허용) -- 칸 없음과 '선언 없음'을 구분하지 않으려고 | §11.6 |
| B-37 | (v0.3.0) measure·tolerance 이름 `offset_sys_mv`(+`offset_sys_mv_abs`, OP-5), `power_dc_w`(+`power_dc_w_rel`, OP-11). `power_dc_w`는 `acceptance` 판정 대상에 넣지 않음 | §11.6 |
| B-38 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.0) 결과 칸 `record_id`(본문 = compare JSON − {`record_id`, `netlist`}), `fingerprints`, `input_sha256`, `summary.conduction_definition` 값 이름(`threshold_eps1`, `seal9_point_lut` -- 둘째 값은 **대체됨**: v0.3.1 `seal9_two_stage`, B-46) | §11.7 |
| B-39 | (v0.3.0; `conduction_columns_*` 규칙과 `conduction_undefined`의 열 설명은 **대체됨** -- v0.3.1 열 칸 삭제, B-46) 새 오류 코드 이름·detail: `oracle_input_schema_invalid`, `adapter_unknown`, `simulator_exe_missing`, `descriptor_kind_undeclared`, `lut_file_stale`, `lut_meta_shape_mismatch`, `lut_condition_conflict`, `sweep_end_unresolved`, `sweep_point_unconverged`, `conduction_undefined`, `sweep_direction_undeclared`, `slew_undeclared`, `power_undefined`, 교차 규칙 이름(`lut_kind_coverage`, `reference_rail_voltage`, `dc_sweep_*`, `conduction_columns_*`, `output_reference_vs_ports`, `declared_triode_unknown_device`, `slew_node_unknown`) | §7, §11.2, §11.6 |
| B-40 | (v0.3.0) swing·ICMR 절차 세부: 공칭 free 해 v0을 먼저 풂, 측정 좌표(ICMR = 공통 방향 사영), 끝 확정 분해능 r = reltol·max(\|m\|) + vntol, 공칭 점이 전도에서만 어기면 `sweep_end_unresolved` | §21.2 |
| B-41 | (v0.3.0, 같은 판 둘째 커밋 고침) `.tf` 벤치 세부: 여기 가중 = `dc_sweep.excite`(차동 ±½ 선언이면 옛 V_id 정의와 같음, 단일 입력은 결정 대기), A는 표본 0 벤치에서 한 번, 결과 칸 `a_dc_tf`·`tf_bench_output_shift_V`·`tf_record` | §21.5 |
| B-42 | (v0.3.0; 'β = 1 = 출력 → `input_n`' 부분은 **대체됨** -- O-53 A-1 반전 포트 규칙, §21.6) 슬루 절차 세부: 시간 계획 = `tran_plan`(β 루프 교차 주파수), dV/dt = 연속 출력 점 쌍의 \|ΔV/Δt\| 최댓값 | §21.6 |
| B-43 | (v0.3.0) 전력의 레일 밖 원천 기록 대상 = forced 고정원·테스트벤치 DC 원·servo 기준원, 같은 `.op`의 전류 출력으로 읽음 | §21.7 |

### 19.2 계획과 다른 결정이 필요한 곳(S-7: 멈추고 보고)

**v0.2 상태**: DV-1·DV-2는 사용자 결정 O-3(2026-10-16 "모두 권고대로")으로 닫혔다. DV-1은 (가)로 정해져 계획 v0.5 N3.4에 반영됐고(`oport-plan-r1`), DV-2 상위 문서 개정은 별도 card다(`gb-oracle-rev`). v0.2에서 새로 생긴 멈춤 항목은 없다. 아래 표는 기록으로 남긴다.

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-1** | (**닫힘** -- 사용자 결정 O-3 = (가), 계획 v0.5 N3.4; 상태 표시는 v0.3.10 둘째 커밋, 근거 이 절 'v0.2 상태' 문단) 오라클이 include해야 하는 모델 파일 가운데 엔진 선언 `sources`에 없는 것이 있다(사례 pmos `lod.spice`, S-7). 계획 N3.4 '원본 파일 경로·sha256 정본은 엔진 선언 하나'와 D-9 '엔진 선언 무변경'을 함께 지킬 수 없다 | (가) 기술자 `extra_sources`에 엔진 선언에 없는 파일만 두고 중복은 금지(§10.1 임시안, '파일마다 정본 한 곳'으로 원칙을 고침) (나) 엔진 선언에 그 파일을 더하는 엔진 card(D-9 예외, 엔진 지문·9회로 기준선 재측정) -- 계획 개정 필요 |
| **DV-2** | (**닫힘** -- 사용자 결정 O-3; 상태 표시 v0.3.10 둘째 커밋, 근거 'v0.2 상태' 문단) 상위 문서 개정(P N3.7)이 아직 반영되지 않았다. 계획 N5.1의 공통 착수 조건이라 구현 card(OP-2~)는 상위 계획 개정 승인 뒤에만 시작할 수 있다. 이 문서는 §17에 문안만 냈다 | 상위 계획 개정 절차를 언제 누가 할지(계획과 다른 결정은 아니고 순서 확인이다). (v0.2.4) `gb-oracle-rev`가 master에 병합됨(`b105b65`, §1.3) |

**v0.2.4 멈춤 항목**(v0.2.5 상태: **닫힘** -- 사용자 결정 O-8 = (가), 계획 v0.6.3 N3.5 (ii)·N4-2 MC 칸·완료 조건 7 개정, X-19. OQ-4로 σ_in·mean_in은 (가-1)로만. 반영은 §13.2. 아래 표는 기록으로 남긴다):

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-3** | (**닫힘** -- 사용자 결정 O-8 = (가), 계획 v0.6.3 X-19; 상태 표시 v0.3.10 둘째 커밋, 근거 §1.1 O-8 행) 계획 N3.5 '결정적 섭동 = 진단 도구' (ii)와 N4-2 MC 칸은 '기준선 MC 표본을 같은 시드·같은 RNG로 재현해 진단 경로로 넣고, 표본별 V_os·σ_in이 기준선과 **비트 동일**'을 요구한다. 그런데 같은 계획 v0.6 D-b(OP-3 병합 조건 (b), v0.6.2 B-3)는 기하 단위·병렬 배수 선언 때문에 소자 줄이 기준선과 달라질 수 있음을 인정하고 공칭 결과를 'N4-2 동일'(비트 동일이 목표, 아니면 분해능 안 + 차 기록)로 판정한다. 진단 경로도 같은 소자 줄 작성기(§10.6)를 지나므로, 같은 물리 표본이라도 시뮬레이터 출력이 마지막 자리에서 다를 수 있고 그러면 V_os·σ_in의 비트 동일이 깨진다. 옛 넷리스트 형식으로 재현하면 옛 코드를 남겨야 해서 P N3.6('진단 도구는 새로 쓰고 옛 코드를 옮기지 않는다')과 맞지 않는다. OP-1 재현(S-22)은 옛 넷리스트 안에서만 비트 동일을 보였다 | (가) **권고**: 둘로 나눈다. (가-1) 코어 MC 수학 비트 동일 = 기준선 로그의 표본별 op 값을 새 `core/mc_math`에 그대로 넣어 V_os·σ_in·mean_in이 비트 동일(S-22 두 번째 방식, 시뮬레이터 없음) (가-2) 진단 경로 끝까지 재현 = 비트 동일이 목표, 다르면 N4-2 분해능(§13.4 `dc_resolution_in_V`) 안이고 차를 기록, 넘으면 실패. 계획 N3.5 (ii)·N4-2 MC 문구 개정이 필요하다 (나) 지금 문구 그대로 끝까지 비트 동일을 요구하고, 깨지면 그때 멈추고 보고 -- 맞는 구현이 막힐 수 있다(v0.6.2 B-3과 같은 종류) |

**v0.2.5 멈춤 항목**(v0.2.6 상태: **둘 다 닫힘** -- 사용자 결정 O-9 = DV-4 (가)·DV-5 (가), 계획 v0.6.5 완료 조건 8a 예외 둘째(X-25)·N0.1 '기준선'(X-24)·OP-1a (a)~(d)에 반영. design 반영은 §18.1 '8a 예외 둘째' 행, §13.2 '기준선 표본별 V_os'. v0.2.6에서 새로 생긴 멈춤 항목은 없다. 아래 표는 기록으로 남긴다):

**v0.2.6 개정 대기**(재검증 조건): **계획 v0.6.6 개정 대기(어댑터 지문 제외 목록 방식) -- 해소(v0.6.6 병합)**: 계획 v0.6.6이 master `7edd723`으로 병합됐고(사용자 X-22 승인), 이 worktree에 병합(`b21b4a9`)한 뒤 `plan_version`과 §0·§8.3·§12.4 인용을 v0.6.6으로 바꿨다. 아래는 대기 당시 기록이다. 이 문서 §0·§8.3·§12.4의 어댑터 지문(제외 목록 방식, git 추적 파일 집합(철회됨, ce9afad -- 계획 문구 복귀), 정규 JSON 규칙)은 계획 v0.6.5의 '판정 키 넷 포함 목록' 문언보다 앞서 있고, 그 문언을 맞추는 계획 v0.6.6(브랜치 `plan/oracle-v066` `c62f3bf`·`16af2cf`, diff 검증 중)이 아직 병합되지 않았다. 병합되면 `plan_version`과 §0·§12.4·§8.3의 '계획 v0.6.5' 인용을 v0.6.6으로 바꾼다(오케스트레이터 지시 대기). 그 전에는 이 부분을 계획과 맞춘 것으로 보지 않는다.

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-4** | (**닫힘** -- 사용자 결정 O-9 = (가), 계획 v0.6.5 X-25; 상태 표시 v0.3.10 둘째 커밋, 근거 'v0.2.5 멈춤 항목' 문단) 엔진 test `E/tests/metrics/test_verified_by.py:62-65`(`test_oracle_measure_key_exists_in_oracle_sources`, 8 항목)는 오라클 **최상위** `O/oracle_*.py` 소스 텍스트에서 measure 키를 찾는다(S-26). 키 8개는 모두 `O/oracle_compare.py`에 있다. 계획 N3.6·§15.1대로 compare를 `O/core/compare.py`로 옮기고 옛 파일을 지우면(OP-3) glob 대상은 `oracle_run.py`만 남아 이 엔진 test 8 항목이 실패한다. 그런데 계획 완료 조건 8a는 OP-2~OP-6·OP-8에서 `E/`의 git diff 0이고, 예외는 X-13 test 새 파일 하나뿐이다(기존 test 파일 diff 0). 코어는 최상위 진입점을 import할 수 없고(§3.2), `O/core/` 밖에 키 표 사본을 두면 정본이 둘이 된다. 그래서 계획을 지키며 갈 방법이 없다 | (가) **권고**: 계획 완료 조건 8a 예외에 '이 엔진 test의 오라클 소스 경로 glob을 `O/core/*.py`(또는 `O/**/*.py`)로 바꾸는 한 줄'을 더한다(test 기준은 그대로: 키 문자열이 오라클 소스에 있음). 근거: 그 test의 판정 대상(키가 오라클에 있다)은 바뀌지 않고 위치만 옮긴다. 바꾸는 주체는 엔진 test 작성자, 같은 변경은 OP-3 (나) 진입점 `oracle_run.py`가 measure 키 표를 정의하고 코어 `compare`에 인자로 주입 -- 엔진 무변경이지만 판정 어휘가 코어 밖에 놓인다(계획 N0.1 '판정·비교는 코어'와 어긋남) (다) 엔진 test를 지우고 다른 증거로 대체 -- 엔진 기준 약화라 사용자 승인 대상. **막는 card**: OP-3(compare 코어 이동) |
| **DV-5** | (**닫힘** -- 사용자 결정 O-9 = (가), 계획 v0.6.5 X-24; 상태 표시 v0.3.10 둘째 커밋, 근거 'v0.2.5 멈춤 항목' 문단) 계획 N3.5 (ii) (가-1)은 '기준선 로그의 표본별 op 값을 새 코어 MC 수학에 넣어 **표본별 V_os**와 σ_in·mean_in이 기준선과 비트 동일'을 요구하고, (가-2)도 표본별 V_os를 기준선과 비교한다. 그런데 기준선 출력에는 **표본별 V_os 칸이 없다**(S-22: `offset_mc` 칸 목록에 없음). OP-1이 확인한 것은 σ_in·mean_in 두 값뿐이다(S-22 2행, 그 행의 스크립트도 `scripts/`에 없음). 그래서 '기준선의 표본별 V_os'가 무엇인지 계획이 정하지 않았다 | (가) **권고**: 검증자가 base 커밋의 옛 `offset_mc_measure` 표본 처리(로그 → 표본별 V_os, `O/oracle_offset_mc.py:166-196`)를 그대로 돌려 표본별 V_os를 만들고, 그 값과 그 실행 기록(코드 sha·스크립트)을 OP-1a 보관에 넣는다. 그 표본별 값으로 다시 낸 σ_in·mean_in이 기준선 출력과 비트 동일함을 먼저 보여 그 재계산이 옛 코드와 같음을 증명한다. 계획 OP-1a 목록(소비처 고정)에 한 줄 더하는 것이고 판정 기준은 바뀌지 않는다 (나) (가-1)·(가-2)의 표본별 비교를 빼고 σ_in·mean_in만 (가-1)로 판정 -- 계획 문구 축소(사용자 결정 O-8 범위 변경). **막는 card**: OP-1a(보관 목록), OP-5(진단 경로 판정) |

**v0.3.0 멈춤 항목**(계획 v0.6.9가 정하지 않았거나 계획 안의 두 조항이 부딪혀, design이 혼자 정하면 원래 취지가 바뀔 수 있는 곳. 각 항목은 막는 부분만 막고, OP-3 입력 스키마 계약(§11.1~§11.4·§11.7)과 EO-1 계약은 막지 않는다 -- DV-7만 OP-3 병합 조건 (b)를 막는다):

| ID | 내용 | 필요한 결정 |
|---|---|---|
| **DV-6** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (**닫힘** -- 사용자 결정 O-50 G5; 상태 표시 v0.3.10 둘째 커밋, 근거 아래 'v0.3.1 닫힘 표') **I_off 열의 형식과 읽기(보간) 규칙**. 계획 N3.9·G-18·사용자 결정 O-46 (2): I_off = 판정 점 VDS·VSB에서 **엔진 LUT의 VGS = 0 누설 조회**, 오라클은 엔진을 import하지 않으므로 그 열은 입력으로 받는다. 그런데 엔진의 '조회' 값은 `op_point`의 보간이다 -- VS·VDS 축은 기울기 자료·단조 조건이 맞으면 3차 Hermite, 아니면 선형, L은 bin 안 선형, 결과에 W/L(S-41). 계획은 열의 형식도 오라클 쪽 읽기 규칙도 정하지 않았다. 고르는 안에 따라 '합격·범위 판정의 I_off = 엔진 봉인 9의 I_off와 같은 정의'(계획 N3.9 '한 정의')가 성립하는지가 갈린다. tol_V 열은 읽기 규칙이 '정의된 셀 최댓값'이라 이 문제가 없다(§21.1) | (가) **권고**: 오라클이 엔진 VGS = 0 보간 규칙의 **사본**을 새로 쓴다(선례: §10.2 `lut_record_root` 해석 사본, X-D5 승인 O-11). 입력 열 = 소자 L 행들(앵커 하나 또는 같은 bin 양옆 둘과 L 가중)의 VGS = 0 마디(폭 슬라이스 VGS 축 첫 값 = 0.0이라 VGS 방향 보간 없음, S-38)에서 VDS × VS 격자의 ln ID, VS 기울기(−GMBS/ID), VDS 기울기 자료, 기울기·단조 마스크, 그리고 W/L. EO-1 갱신 커밋이 LUT 표를 그대로 직렬화(재계산 없음). 결과는 엔진과 같은 값. 비용: 칸이 커지고 엔진 보간 규칙이 바뀌면 오라클 사본도 같은 변경에서 고쳐야 한다(gain-budget 쪽 동반 수정 절차 알림, X-D5와 같은 방식) (나) 열 = VDS × VS 격자의 I_off 값(W/L 곱함), 오라클은 ln I_off 쌍선형 보간 -- 단순하지만 격자 사이에서 엔진 값과 달라져 '한 정의'가 근사가 된다(원래 취지와 다름) (다) 2단계 실행: 오라클이 판정 점 VDS·VSB를 내고 생산자가 엔진 함수로 I_off·tol_V를 계산해 다시 넣음 -- 값은 같지만 오라클 판정이 엔진 실행에 기대게 되어 계획 N3.8 '오라클 독립' 구조와 다르고, 범위 훑기 점마다 왕복이 생긴다. **막는 것**: OP-5의 전도 판정 부분(§21.1 4단계, §21.2·§21.3) |
| **DV-7** | (**닫힘** -- 사용자 결정 O-50 O1′; 상태 표시 v0.3.10 둘째 커밋, 근거 'v0.3.1 닫힘 표') **기준선 입력의 LUT에 모델 기록이 없다**(S-39). OP-3 병합 조건 (b)(첫 조합 선언값으로 쓴 공칭 op·ac 결과가 N4-2로 기준선과 동일)를 재려면 기준선 입력 593개를 변환해 새 오라클로 돌려야 하는데, 공칭 자동 대조(D-7, §12.5)가 변환 사본 전부를 `lut_model_provenance_missing`으로 거부한다. 계획 X-14('지금 LUT에서 위험은 낮다', '확인됨')는 LUT v2 슬라이스를 잰 것이고, 기준선 입력이 실제로 쓴 LUT(test `make_lut` 파일 = `corner`·`temp_c`만, `A/sky130_nfet_pfet_lut_sample.npz` = `meta_json` 없음)는 아니었다. 계획 N4-2a·X-14·OP-3 병합 조건 (b)·D-7이 함께 성립하지 않는다 | (가) **권고**: 검증자 변환(N4-2a)이 기준선 입력의 LUT를 **검증자 사본 LUT**(같은 `corner`·`temp_c` + meta `model_files_sha256` = 그 기준선 넷리스트가 include 재귀로 읽은 모델 파일의 raw sha256 -- 검증자가 기준선 넷리스트에서 잼)로 바꾸고, 사본은 판정 기록 안에만 둔다(배포 산출물 아님, X-5). 그러면 새 오라클의 묶음 대조가 '새 어댑터 묶음 ⊇ 기준선 실행 묶음'을 재게 되어 N4의 취지(같은 모델로 돌았나)에 맞는다. 계획 N4-2a에 '측정 결과를 담은 옆 선언'과 같은 지위의 사본 한 줄을 더하는 개정이 필요하다 (나) N4 비교 실행에서만 공칭 자동 대조를 끄는 진입점 인자 -- 판정 경로에 우회가 생긴다(P NFR-P6), 권하지 않음 (다) 병합 조건 (b)의 입력을 LUT v2를 쓰는 새 test 입력으로 바꾸고 기준선 입력을 쓰지 않음 -- 기준선이 없어져 '기준선과 동일'을 잴 수 없다(기준 약화, 사용자 결정 대상). **막는 것**: OP-3 병합 조건 (b), 그리고 같은 변환 사본을 쓰는 OP-4·OP-5의 N4 동일성 실행. §11.5 `process.lut_npz` 행 |
| **DV-8** | (**닫힘** -- 사용자 결정 O-50 G1; 상태 표시 v0.3.10 둘째 커밋, 근거 'v0.3.1 닫힘 표') **`offset_sys_mv`의 값·부호와 단일 입력 회로**. DEC-23 정의 문장 '출력을 기준값에 고정하고 입력 차를 미지수로 푼 DC 해의 입력 차'와 같은 행의 계산 'ΔV_out ÷ DC 극한 전달'은 1차에서 부호가 반대다(V_out = A·V_id + V_out0이면 출력 고정 해의 입력 차 V_id* = (기준 − V_out0)/A = −ΔV_out/A). offset-trim PC-10은 V_sys = output_error/A_dm = −V_in(§12.2)이라 계산 쪽 부호다. 그리고 지금 엔진 구현 `E/metrics/offset_systematic.py:7-8`은 값을 **크기** \|오차\|/\|A_dm\|(mV, 상한 제약 `<=` 용)로 내고 부호 있는 오차는 `output_error_v`로 따로 싣는다. 또 '입력 차'는 차동 입력을 전제하는데, 정의 일반형(단일 입력 회로)에서 단일 입력 회로의 계통 offset 문장이 없다 | (가) **권고**: metric 값 = \|V_id*\|(mV, 엔진 현 구현과 같은 크기), 부호 있는 값은 `offset_sys_signed_mv` = −V_id*(= ΔV_out/A의 정확값, PC-10 V_sys와 같은 부호)로 따로 기록, 단일 입력 회로는 DEC-23이 확장될 때까지 정의 불능(사유 `offset_sys_single_input`). 정의 소유자 gain-budget에 DEC-23 문언 명확화(부호·크기·단일 입력)를 요청(계획 U-4 경로) (나) 값 = +V_id*(문장 문자 그대로, 부호 있음)로 하고 엔진 쪽 계산·제약을 맞춤 -- 엔진 card 몫. **막는 것**: OP-5의 계통 offset 부분(§21.4)만 |
| **DV-9** | (**닫힘** -- 사용자 결정 O-50 G2·O-51; 상태 표시 v0.3.10 둘째 커밋, 근거 'v0.3.1 닫힘 표') **슬루 계단 끝과 방향 묶음**. gain-budget N3.8 557행 '계단 크기·방향 = O-28 끝(입력을 허용 입력 범위 끝까지 미는 방향별 계단)'의 '허용 입력 범위'가 (a) spec 선언 입력 범위 (b) 엔진 ICMR 창 (c) 오라클이 잰 ICMR 창 가운데 무엇인지 문장에 없다. 또 metric `slew_rate_v_per_s` 하나에 방향 둘을 어떻게 담는지, 차동 출력 회로의 β = 1 follower 구성이 문장에 없다 | (가) **권고**: 계단 끝 = 입력 `slew.step_ends_V`, 그 값은 생산자가 엔진 슬루 방향 전류 정의(gain-budget N6.8 card DE-1 1557행 (d) '입력을 허용 입력 범위 끝까지 몬 DC 해')가 쓰는 같은 끝에서 옮긴다(엔진 손계산과 오라클이 같은 계단을 비교하도록). 방향별 두 값을 기록하고 metric 값 = 두 방향의 최솟값(하한 제약 `>=`에 보수). 차동 출력 회로는 `feedback = "declared"`만 받고 `unity_follower`면 `slew_undeclared`(β = 1 구성이 정의되지 않음). 정의 소유자 gain-budget에 557행 보완 요청 (나) 오라클이 자기 ICMR 측정(§21.2) 끝을 계단 끝으로 씀 -- 엔진과 다른 계단이 될 수 있다. **막는 것**: OP-10 전체 |

**v0.3.1 닫힘 표**(계획 v0.6.10 DR-18, 사용자 결정 O-50~O-55, O-57 승인):

| 항목 | 닫은 결정 | 반영 자리 |
|---|---|---|
| DV-6 I_off 열 형식·읽기 규칙 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** O-50 G5: 입력 열을 두지 않음, I_off·tol_V는 엔진 정본 LUT 함수가 2단계로(사본 안 (가) 기각); 온도 점 I_off = SPICE 소자 개별 풀이(O-53 B2) | §11.6 `conduction_columns` 삭제, §11.7 `conduction.points[]`, §21.1 |
| DV-7 기준선 입력 LUT 모델 기록 없음 | O-50 O1′: 593개 기대 결과 = D-7 거부(동작 변경), 동일성 비교 상대 = OP-1b 추가 기준선, 사본 LUT 안 기각 | §11.5 `process.lut_npz` 행, §18.1 '3 동일성' 행 |
| DV-8 `offset_sys_mv` 값·부호·단일 입력 | O-50 G1: 부호 있는 V_id* 한 칸, \|V_id*\| ≤ spec, 단일 입력 = 여기 방향 일반형; O-53 B3 기준 종류 셋 + PC-10 = 같은 측정 | §11.6 `output_reference`, §21.4 |
| DV-9 슬루 계단 끝·방향 묶음·차동 출력 | O-50 G2: 방향별 둘(`slew_rise_v_per_s`·`slew_fall_v_per_s`), 집계 없음, 차동 출력 미선언 = 정의 불능; O-51: 계단 끝 = 오라클이 잰 ICMR 확정 끝 | §11.6 `slew`·`measure_feedback`, §21.6 (전달 경로는 DV-10 멈춤) |
| B-34 `judge.off_current_A` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** O-50 O2: 지움 | §11.6 지우는 칸, §19.1 B-34 |
| X-D7·X-D8 | O-50 O4: 수용 | §19.4 |
| §21.1 2단계 ID 부호 | O-50 G3: 선언 방향 ID > 0 | §21.1 2단계 |
| §21.2 ICMR 해석 | O-50 G4·O-52 확인 1·O-53 A-1·A-2: 선언 되먹임 또는 β = 1 follower, 반전 포트 = 선언 또는 `.tf` 부호 | §11.6 `measure_feedback`, §21.2 |
| 범위 조건·선언 영역 | O-53 B1·O-54·O-55 U1: `intended_region` {triode, off}, 동작점 불일치 = 선언 오류(판정 불능 집계), 훑기 중 이탈 = 범위 끝, 선언 없는 소자 비포화 = FAIL | §11.6 `intended_region`, §21.1 7단계, §21.2, §21.3 |
| `output_reference` = PC-10 칸 | O-53 B3: 같은 칸·같은 측정 | §11.6, §21.4 |
| OP-10 선행·착수 조건 | O-50 O3·O-51: 선행 EO-1, 착수 = gain-budget v6.20 N3.8 개정 병합 + OP-5 ICMR 절차 병합 | §20 OP-10 행 |
| 판정 분해능(반전 포트 판정) | gain-budget v6.20 N3.8 '판정 분해능' 인용, 오라클 쪽 값 = 계획 N0 값 원칙(시뮬레이터 선언 해 정확도) → §18.3 식 | §21.2 |

**v0.3.1 남은 멈춤**(계획이 정하지 않아 design이 정하면 취지가 바뀔 수 있는 곳 -- 막는 부분만 막음):

| ID | 내용 | 필요한 결정 | 막는 것 |
|---|---|---|---|
| **DV-10** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.3 **닫힘** -- 계획 v0.6.11 G-19·OP-10 '실행 순서'·N3.9 슬루 행, 사용자 결정 O-58 DV-10·O-59 (3); 반영 §11.6 `confirmed_range`, §7 `range_pointer_rejected`·§7.2 2c, §11.7 `range_final`, §21.6 1·2단계. 아래는 멈춤 당시 문장) 슬루 계단 끝 = '오라클이 잰 ICMR 창 끝, 2단계 전도 판정까지 확정된 값'(O-51)인데, 확정은 엔진 쪽 2단계가 하고 계획 G-19는 '계단 끝 입력 칸은 두지 않는다'고 한다. 확정 끝이 오라클 슬루 실행에 닿는 경로가 계획에 없다 | (가) 슬루 요청이 확정 ICMR 오라클 결과를 `record_id`로 참조하고 2단계 확정 기록(엔진 쪽이 그 결과 옆에 쓰는 파일)을 오라클이 읽어 확인 -- 오라클이 엔진 산출물을 읽게 됨 (나) 2단계가 확정 끝을 '확정 ICMR 결과' 칸으로 슬루 요청에 실음 -- '계단 끝 입력 칸 없음' 문언과 충돌 여부를 계획이 판단 (다) 오라클 한 실행 안에서 ICMR → 2단계 콜백 → 슬루(엔진 함수 호출 = import 금지 위반이라 불가) -- 계획 G-19 문언 개정 필요 | OP-10의 계단 입력 부분(§21.6) |
| **DV-11** | §21.5 단일 입력 회로의 `.tf` A(불일치 σ 입력 환산)를 옛 그대로 `unavailable`로 둘지, 일반형으로 넓힐지 -- O-50 G1은 계통 offset만 일반형으로 정했고 `offset_in_sigma_mv` 행은 말하지 않는다 | 계획 N3.9 `offset_in_sigma_mv` 행 보완 -- (v0.3.3 **닫힘**: 계획 v0.6.11 같은 행 = 여기 방향 DC 소신호 전달, 정의 정본 gain-budget DEC-23, 사용자 결정 O-58 DV-11; 반영 §21.5 정의 인용·1단계 단일 입력·4단계. |A| ≤ 판정 분해능 처리는 DV-14로 따로 멈춤 -- v0.3.4 닫힘) | OP-5 §21.5 단일 입력 부분 |
| **DV-12** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.3 **닫힘** -- 계획 v0.6.11 N3.9 '범위 판정' 끝 '최종 범위 metric', 사용자 결정 O-59 (3) = (다), 원래 취지와 다름(경미) 승인됨 O-59; 반영 §11.6 `confirmed_range`, §11.7 '잠정 표시'·`range_final`·`range_input_fp`, §21.2 'metric 값'. 아래는 멈춤 당시 문장) (v0.3.2, 검증 #1) 2단계(엔진 쪽)가 창 끝을 줄인 뒤 최종 `swing_out_v`·`icmr_v`·`icm_margin_v`와 그 제약 판정을 **누가 어느 칸에** 다시 내는지 -- 계획 N3.9 '범위 판정'은 '창 끝 = 두 단계 끝 가운데 공칭에 가까운 쪽'과 재훑기 왕복만 정하고 재계산 주체·출력 칸을 정하지 않는다 | (가) 엔진 쪽 2단계 호출 자리가 값 식(§21.2 'metric 값')으로 재계산 -- 값 식이 두 곳(정본 하나 위반 우려) (나) 2단계가 확정 끝(점 식별자)을 입력 칸으로 오라클에 돌려주고 오라클이 재계산 -- 새 입력 칸 (다) O-58 DV-10의 '오라클 ICMR 기록 `record_id` + 끝마다 점 식별자' 방식을 범위 metric에도 적용 -- 계획 문언 필요 | §21.2 최종 값·§11.7 확정 칸(그 전 오라클 값은 `provisional`으로 막음) |
| **DV-13** | (v0.3.3 **닫힘** -- gain-budget v6.21 DEC-23 '이동의 기준점', 계획 v0.6.11 N3.9 `offset_sys_mv` 행 인용, 사용자 결정 O-59 (4); 반영 §11.6 `dc_sweep.input_dc`, §7 `input_dc_undeclared`, §21.4 3단계. 아래는 멈춤 당시 문장) (v0.3.2, 검증 #13) 계통 offset 값 = V_id* − V_id,0의 기준점 V_id,0 출처: 공칭 free 벤치 servo 목표가 출력 기준과 같으면 값이 늘 0. gain-budget DEC-23(v6.20 223행)은 '출력을 기준값에 고정하고 입력 차를 미지수로 푼 DC 해의 입력 차'와 '출력을 기준값으로 되돌리는 여기 방향 입력 이동량'(엔진 기준 = θ 봉인점, ΔW = 0이면 0)만 적고, 오라클 쪽 이동 기준점(free servo 해·엔진 동작점 입력 칸·차동이면 0 가운데 무엇인지)과 free 벤치 servo 목표를 정하지 않는다. O-58 DV-11 'DEC-23 먼저' 개정과 겹칠 수 있음 | 계획 N3.9 계통 offset 행(DEC-23 인용) 보완 | §21.4 3단계 값 식 |
| **DV-14** | (v0.3.4 **닫힘** -- 계획 v0.6.12 N3.9 σ 행 'A 정의 불능'(사용자 결정 O-61 P7)·v0.6.13 `offset_sys_mv` 행 (i)~(vi)(O-62 (3)·O-63 (1)(2)), 정본 gain-budget v6.23 DEC-23 'A_dc 정의 불능 갈래'·N3.8 판정 분해능; 반영 §21.5 3·4단계(`a_dc` 기록 하나, 사유 `tf_failed`·`a_dc_below_resolution`), §21.4 4단계(갈래 먼저, `a_dc_undefined`·`sim_convergence_failed`, 둘째 A 측정 없음, '정의 경계 불일치'), §7 `a_dc_undefined`, §18.1 '10 정의 대조 -- OP-5' (a). 아래는 멈춤 당시 문장) (v0.3.3, DV-11 분석이 짚은 틈) σ 입력 환산 A가 0은 아니지만 \|A\| ≤ 판정 분해능일 때: 계획 `offset_in_sigma_mv` 행은 'A = 0·`.tf` 실패 = `unavailable`'만 정하고, 반전 입력 포트 판정(§21.2)처럼 '전달 크기 ≤ 판정 분해능 = 정의 불능'을 σ 행에 두는지 말하지 않는다. design이 정하면 단일 입력·차동 모두의 기준선 값이 바뀔 수 있어(차동 비트 동일 조건과 겹침) 정하지 않는다 | 계획 N3.9 `offset_in_sigma_mv` 행 보완(또는 gain-budget DEC-23 A_dc 쪽) | §21.5 4단계의 작은 \|A\| 갈래만(A = 0·실패 갈래와 나머지는 진행 가능) |
| **DV-15** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.4 **닫힘** -- 계획 v0.6.12 G-18 '선언 입력 DC 칸은 `dc_sweep.input_dc` 하나'·N3.9 ICMR 행 'V_icm', 사용자 결정 O-61 P8; 검증자 판단 가운데 '공칭 점 갈래 대체 삭제'는 기각(엔진 정의와 같은 갈래라 유지, 계획 DR-19); 반영 §11.1 `/swing_icmr`(두 칸 OP-5에서 삭제), §11.6 `dc_sweep.input_dc` 소비자 둘, §11.5 변환 행, §21.2 'metric 값' V_icm, §18.1 (b). 아래는 멈춤 당시 문장) (v0.3.3, DV-13 반영에서 생김) 계통 offset 기준점 입력 `dc_sweep.input_dc`(넷별 선언 입력 DC)와 기존 `swing_icmr.input_dc_V`(`icm_margin_v`의 V_icm, 스칼라)가 같은 spec 입력 DC 선언에서 온다 -- 두 칸이 같은 선언의 사본이 될 수 있다(정본 하나 원칙). 하나로 묶으면(`input_dc_V` 삭제 → V_icm = Σc·V_in,decl/Σc² 유도) OP-3 입력 계약의 기존 칸이 바뀐다 | 묶을지·둘의 불일치 거부 규칙을 둘지(계획 G-18 또는 사용자). **검증자 판단**(v0.3.3 design-validator, 기록 -- 결정 아님, 계획 G-18·사용자 결정 대기): 정본 = `dc_sweep.input_dc` 하나; `swing_icmr.input_dc_V`·`input_dc_pending` 삭제; V_icm은 §21.2 4단계 사영 Σc·V_in,decl/Σc²로 유도; §21.2 'metric 값'의 '없으면 공칭 점 좌표' 대체 삭제(= 동작 변경, N4 0번); '두 칸 + 불일치 거부' 안은 기각(같은 정의의 양 두 칸 -- graph 단일 정본 규칙 3) | §11.6 `input_dc`와 §11.1 `swing_icmr.input_dc_V`의 관계만(DV-13 값 식은 진행 가능) |
| **DV-16** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.4 **닫힘** -- 계획 v0.6.13 N3.9 '범위 판정'(정의 불능 끝 `{undefined: true, record_id}`, '2단계 끝의 이탈 소자·정의 불능 사유')·G-19(검사 (1)은 정의 불능 끝에도, (2)~(4)는 점 지목 끝에만), 사용자 결정 O-62 (2) P10; 정본 = 엔진 `stage2_judgment`(gain-budget v6.23 N6.20 '2단계 판정 기록', 인용만 -- 오라클은 저장하지 않음); 반영 §11.6 `confirmed_range`(`reason` 삭제), §7 `range_pointer_rejected`·§7.2 2c, §11.7 범위 끝 기록(`end_cause`에 2단계 갈래 없음)·`range_final.source`(정의 불능 끝 = 같은 꼴), §18.1 (c). 아래는 멈춤 당시 문장) (v0.3.3 셋째 커밋, design↔계획 gap) 2단계(엔진 쪽)가 정한 끝(전도 쪽 이탈)의 이탈 소자 정보(어느 소자가 어느 선언 영역에서 벗어났는지 -- 1단계 끝의 `departed`에 해당)를 어디에 싣는지: 오라클 기록에는 2단계 판정이 없고, `confirmed_range` 지목은 점 식별자만 담는다. 계획 N3.9 '범위 판정'·G-18 '결과 칸'은 정하지 않는다 | 계획 결정(엔진 쪽 기록인지, `confirmed_range`/`range_final`에 담는지) | §11.7 범위 끝 기록의 2단계 끝 원인 정보만(검증자 원인 변화표의 2단계 끝 원인 칸) |
| **DV-17** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.6 **닫힘** -- 계획 v0.6.14 N3.9 '전달 판정 분해능', 사용자 결정 O-67 (3)·O-68 (1)·O-70 (1)·R-1, 정의 gain-budget v6.24 N3.8 576행 인용; 반영 §21.5 4단계 (4), §21.2 2단계 반전 입력, §7 `inverting_port_undetermined`, §18.1 (a). 아래는 멈춤 당시 문장) (v0.3.5 새 멈춤, 검증 M1) **'(계획 개정 대기 -- A 판정 분해능 식)'**: \|A\| ≤ 판정 분해능의 V/V 단위 분해능 식. 정의 자리(gain-budget v6.23 N3.8 570행 '감도 게이트 ε를 그 DC 전달에 적용')와 오라클 입력(계획 N0 29행 '시뮬레이터 선언 수렴 허용치')은 정해져 있지만, 오라클은 `.tf` 선형 풀이 잔차를 받지 못해 ε의 입력이 없고, §18.3 식은 전압·전류 칸 식이라 V/V로 쓰려면 구동 진폭(전압 척도)을 골라야 한다 -- 새 선택·상수 | 계획 N3.9 σ·`offset_sys_mv` 행(또는 gain-budget N3.8)에 오라클 쪽 V/V 분해능 식을 정함 | §21.5 4단계 (4)의 A ≠ 0 갈래, §21.2 반전 입력 포트의 '전달 크기 ≤ 판정 분해능' 후보 판정(같은 식). A = 0·`.tf` 실패·나머지 사유·후보 0개/2개 이상은 진행 가능 |
| **DV-18** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.6 **닫힘** -- 계획 v0.6.14 N3.9 ICMR 행 '`icm_margin_v` 정의', 사용자 결정 O-67 (2), 정본 gain-budget N6.6 IT-2 '범위' 2(v6.24 1490행); 반영 §21.2 'metric 값'(포트별 식, 사영 삭제), §11.6 `input_dc` 소비자 하나, §11.7 `v_in`, §18.1 (b) 반례 test, §19.5. 아래는 멈춤 당시 문장) (v0.3.5 새 멈춤, gap #27 -- 계획 OQ-10 (나)) `icm_margin_v`의 V_icm 사영 Σc·V_in,decl/Σc²로 잰 margin과 엔진 포트별 margin 최솟값 min_p min(V_p − lo_p, hi_p − V_p)이 **일반적으로 같지 않다**(§21.2 'metric 값'): 포트 끝 거리 = \|c(p)\|·\|Δy\| 대 m 끝 거리 \|Δy\| -- (i) 모든 \|c(p)\| = 1 (ii) 묶인 포트 없음 (iii) V_icm 기준점 = 동작점일 때만 같음. 반례 c = (2, 2), β = 1 follower(ICMR 기본 구성). 같은 이름 metric의 두 정의(graph 단일 정본 규칙 3) | 계획 N3.9 ICMR 행·gain-budget IT-2 '범위' 2의 `icm_margin_v` 정의를 하나로(포트별 margin 또는 m 좌표 margin; 이 문서는 고르지 않음) | §21.2 `icm_margin_v`의 (i)~(iii) 밖 경우만(그 밖 swing·ICMR·`icmr_v`는 진행 가능) |
| **DV-19** | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.8 **닫힘** -- 계획 v0.6.15 N3.9 ICMR 행·DR-23 (2), 사용자 결정 O-78 (2)·O-79·O-80 R2; 정의 자리 = gain-budget v6.26 N3.8 'ICMR 측정 구성'의 '단일 출력 + DC 성분 없는(용량만) 선언 되먹임' 문장 하나(이 문서는 인용만, 규칙을 다시 적지 않음); 반영 §21.2 2단계 (e)(정의 불능, 단일 입력 (d) 먼저), §7 `icmr_feedback_dc_absent`(엔진 대응 이름 `icm_config_feedback_no_dc` -- design 41 v1.12.5 승인 대기), §18.1 'OP-5 (e)'. 아래는 멈춤 당시 문장) (v0.3.6 새 멈춤, DR-21 적용 중 발견) **단일 출력 + DC 성분 없는 선언 되먹임**(용량만)의 ICMR 측정 구성: 계획 N3.9 ICMR 행은 '선언 되먹임의 DC 성분만'과 '차동 출력의 DC 닫힘'만 정하고, 단일 출력이 용량만 선언된 경우(DC에서 되먹임 없음 -- 개루프라 출력이 레일로 감)를 정하지 않는다 | 계획 N3.9 ICMR 행 보완(β = 1 follower로 갈지, 정의 불능인지) -- 이 문서는 고르지 않음 | §21.2 2단계 (e) 경우만(지금 library에 해당 회로가 있는지는 착수 실측) |
| **DV-20** | (v0.3.6 새 멈춤, 사용자 규칙 2026-10-21 '확인 안 된 것 = 미확인'; **v0.3.8 범위 줄임 -- C10만**, 계획 v0.6.15 DR-23 (1) 'DV-20의 1b 몫은 1b와 함께 옮기고, C10 쪽은 design이 적는다') **'미확인' -- ngspice `uic` 없는 `.ic`의 '바이어스 해에서만 묶고 t > 0에 푼다' 의미의 원문 쪽 번호**: 동작 근거는 저장소 코드 사용(`O/oracle_netlist.py:596-598`, `:625`, `:720`, `:765` `uic` 없는 `tran` -- 기존 C10 과도 벤치)뿐이고 매뉴얼 원문 쪽은 R6 원문 보관(OP-2 병합 조건, §19.3) 전이라 확인하지 않았다. OP 범위의 소비자는 C10 하나(OP-4 -- v0.3.8 둘째 커밋 M1 정정, 옛 'OP-3'; §4.2 `stab_benches`·§8.3 `tran_ic_bias_only`). 1b 몫(§21.6 1b의 같은 의미 의존)은 1b와 함께 gain-budget card AP-1로 옮겼다 -- AP-1에서 OP card를 열 때 다시 적는다 | R6 원문 보관에서 쪽 번호 채움(ngspice 어댑터 `tran_ic_bias_only = true` 선언의 근거 칸). C10 동작 자체는 옛 넷리스트 줄과 같은 꼴이라 OP-4 동일성(§18.1 '3 동일성', N4 OP-4 행)이 옛 결과와의 같음을 잰다 -- 그 같음은 의미의 원문 확인을 대신하지 않는다 | OP-4 C10의 `tran_ic_bias_only` 선언 근거 칸(원문 쪽 번호)만 |
| **DV-21** | (v0.3.10 **닫힘** -- 계획 v0.6.17 DR-25 (1), 사용자 결정 O-85 (1)·O-86 N3; 정의 = gain-budget v6.28 N3.8 '선언 되먹임의 DC 되먹임 판정' 문단의 '차동 출력' 규칙(두 출력 판정이 같을 때만 그 판정, 갈리면 정의 불능) 인용; 반영 §21.2 2단계 (0) '차동 출력의 결합', §7 `dc_feedback_judgment_undefined` `why = differential_split`, §18.1 OP-5 (0) (x)(xi), §20 OP-5 착수 조건 해소, §19.2 대응표. 아래는 멈춤 당시 문장) (v0.3.9 새 멈춤, DR-24 적용 중 발견) **차동 출력에서 두 출력의 DC 되먹임 판정이 갈리는 경우**: gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'는 판정을 "출력 넷(차동 출력이면 출력마다)으로부터" 정의하고, ICMR 차동 문단은 "'DC 되먹임 판정'이 '없음'이거나 선언이 없으면 차동 모드만 닫는다"고 한다 -- 한 출력은 '있음', 다른 출력은 '없음'일 때 구성(선언 그대로·DC 닫힘·정의 불능)이 무엇인지, 슬루 (c)(`start_op_deferred`)에 해당하는지 정하지 않는다. 해당 회로 0개(13개 가운데 비지 않은 선언은 current_reuse 하나이고 두 출력 모두 '없음' -- §19.6 F-13) | 계획 gain-budget N3.8(정의 자리 하나)에 차동 출력의 판정 결합 규칙을 정함 -- 이 문서는 고르지 않음. **닫는 경로**(v0.3.9 둘째 커밋, 검증 M2 4절 권고 -- **사용자 결정 대기**): gb N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' 문단에 한 문장을 더하는 계획 개정 -- 제안 문언 "차동 출력은 두 출력 판정이 같을 때만 그 판정을 쓰고, 갈리면 정의 불능(사유 기록, 이름은 design), 해당 0개"; oracle 계획 N3.9는 인용만. 그 개정이 승인되면 이 design이 사유 이름을 정한다(지금 고르지 않음) | §20 OP-5에서 이 갈래의 **구현 착수**(v0.3.9 둘째 커밋 -- 사유 이름 없는 fail-closed를 코드에 남기지 않음, N3.14); 단일 출력·두 출력 판정이 같은 차동 출력은 진행 가능 |

**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **v0.3.4 상태**: 위 표의 멈춤은 모두 닫혔다(DV-14·DV-15·DV-16 = 계획 v0.6.12·v0.6.13 DR-19·DR-20, 사용자 결정 O-61·O-62·O-63, 병합 승인 O-65). v0.3.4에서 새로 생긴 멈춤은 없다. 계획이 design에 맡긴 결정과 이 판의 선택: (1) `range_final.source`의 정의 불능 꼴 = 입력 지목과 같은 `{undefined: true, record_id}`(DR-20 '`null`이면 같은 꼴로 맞출지') (2) `end_cause`에 2단계 갈래를 두지 않음(DR-20 '`end_cause`에 2단계 갈래를 둘지') (3) 사유 이름 `a_dc_below_resolution`·`tf_failed`·`a_dc_undefined`와 기록 칸 `a_dc`·`offset_sys`(DR-20 P11 '사유 이름·기록 칸'). 셋 모두 사본 칸·둘째 생산자를 만들지 않는다(§19.5 자체 점검 표).

**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **v0.3.5 상태**: 새 멈춤 DV-17(A 판정 분해능 식)·DV-18(OQ-10 (나) V_icm 동치 불성립) -- 둘 다 계획 개정 대기, 막는 부분만 막음. **사용자 확인 대상(원래 취지와 다름(경미), §19.4)**: X-R3 갈래 발동 시 `.dc` 출력 고정 풀이를 요청하지 않음(계획 '수렴했더라도' 문언), X-R4 `.tf` A 기록 자리를 `offset_mc` 안에서 sim 단계 `sim.a_dc`로 옮김(결과 계약 변경), X-R5 compare JSON의 옛 `summary.u6` 사본을 `sim_ref` 참조로 바꿈(OP-3 결과 계약 변경). 셋 모두 graph 단일 정본 규칙(소비자 없는 계산 금지, writer 하나, 참조 전달)에서 나온 선택이고 권고는 '받아들임'.

**v0.3.6 상태**: DV-17·DV-18 닫힘(계획 v0.6.14 DR-21), X-R3~X-R5 승인됨(O-67 (4)). 새 멈춤 DV-19(단일 출력 + 용량만 선언의 ICMR 구성 -- 계획 미정)·DV-20(ngspice `.ic` 의미 원문 쪽 '미확인'). **사용자 보고**(DR-22 착수 실측, 새 결정 아님): current_reuse의 되먹임 선언에 입력 망이 없어(Cf1·Cf2만, Cs는 입력–접지) 그 회로의 슬루는 정의 불능(`no_input_network`)이 된다. design이 정한 선택(계획 위임 범위)과 그 실현 가능성은 §19.6.

**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **v0.3.7 상태**: 1b·DV-19: O-78로 계획 v0.6.15 대기. 이 판(O-78 (3))이 고친 것은 검증 필수 2~6뿐이고 새 멈춤은 없다(`closure_common_asymmetric`은 **사용자 결정 O-78 (3)이 승인한 fail-closed 선택**이고, 계획 문언(닫힘 행 (i)(ii)·'여기 직교 성분')과 스키마 직교 규칙이 그 근거다 -- §21.2 2단계 (c); v0.3.7 둘째 커밋 문구 정정, 검증 필수 B). 둘째 커밋(v0.3.7 검증 86/100 반영)도 새 멈춤 없음.

**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** **v0.3.8 상태**(계획 v0.6.15 DR-23, 사용자 결정 O-78 (1)(2)·O-79·O-80): **DV-19 닫힘**(정의 = gain-budget v6.26 N3.8 인용, `icmr_feedback_dc_absent`, 단일 입력 먼저 -- R2). **DV-20 = C10 몫으로 줄임**(1b 몫은 AP-1로). **1b 미룸**: §21.6 1b 시작 동작점 경로와 1단계 입력 망 계단 갈래는 OP-10 범위에서 빠져 gain-budget card AP-1 몫으로 표시했고(OP-10에서는 `feedback_config_undeclared` `why = start_op_deferred`·`input_network_step_deferred`), 1b 손 회로 test는 OP-10 test에서 뺐다. **1b에 딸린 IR·능력의 처리**(DR-23 (1) '어떻게 거둘지는 design' -- 만들면 배선): `Tran.ic`·`tran_ic_bias_only`는 지우지 않는다 -- 소비자 C10이 있어 **OP-4 소유**로 확정(둘째 커밋 M1 정정 -- 계획 OP-4 행 500행·N4 OP-4 행 467행이 C10을 OP-4에 둠, 첫 커밋 'OP-3'은 틀림; 만드는 card = 쓰는 card = OP-4; §20 OP-3·OP-4·OP-10 행, §18.1 'OP-4 C10 `.ic`' 행). 코어 `slew_math`의 닫힘 `.op` → `Tran.ic` 경로는 OP-10에서 만들지 않는다(쓰는 회로 0개). 이 판의 새 멈춤은 없다. design이 정한 것(계획 위임 범위): 두 사유를 새 코드가 아니라 기존 `feedback_config_undeclared`의 새 `why` 값으로 둔 것, 옛 `no_input_network`를 `input_network_step_deferred`로 바꾼 것(OP-10은 입력 망 원소를 찾지 않으므로 '입력 망 없음'을 판정하지 않음 -- current_reuse의 슬루 결과는 정의 불능 그대로, 사유 문자열만 바뀜), DV-19 사유 이름 `icmr_feedback_dc_absent`.

**원래 취지와 다름(경미) -- X-R6 승인됨 (O-87 (2))**(v0.3.10 셋째 커밋 표시 -- 사용자 결정 O-87 (2) "받아들임": 아래 (i) 범위와 (ii) 사유 문자열 그대로, 대기 목록에서 뺌; 옛 표제 '사용자 확인 필요 X-R6'; 처음 적은 판 v0.3.8 둘째 커밋, v0.3.8 검증 M2·7절; 계획 DR-23 (1) 위임 안): (i) **범위**: 계획은 '용량만 선언된 차동 출력'의 경로로서 입력 망 계단 갈래를 미룬다(N3.9 슬루 행 '시작 동작점 경로의 구현 자리', DR-23 (1)). 이 design §7 `feedback_config_undeclared` (b)는 그보다 넓게 **구성이 모든 입력 포트에 닿는 모든 선언**(DC 되먹임 있는 선언·단일 출력 포함)의 입력 망 계단을 OP-10에서 뺀다 -- 근거: 그 갈래를 쓰는 회로가 0개(13개 가운데 해당은 current_reuse 하나이고 그것은 (c)에도 해당, §19.6 F-11; 만들면 배선). (ii) **사유 문자열**: current_reuse 슬루 사유가 v0.3.6에서 사용자에게 보고한 `no_input_network`(입력 망 없음)에서 `input_network_step_deferred`(AP-1까지 미룸)로 바뀐다. 결과(정의 불능, fail-closed)는 같다. 권고 = 받아들임(current_reuse는 O-78 (1)이 AP-1 첫 대표 회로로 지목해 '미룸'이 그 회로의 더 정확한 원인). 거부하면 (b)를 용량만 선언된 차동 출력으로 좁히고 그 밖은 '입력 망 원소의 다른 단자' 갈래를 OP-10에 남긴다(쓰는 회로 0개라 권고 안 함).

**DC 되먹임 판정**(v0.3.9 **닫힘** -- 옛 포인터 'DC 성분 분류: O-81 (2) 경로 기준 일반화 -- 계획 v6.27 대기'(v0.3.8 둘째 커밋)는 history v0.3.9): 계획 v0.6.16 DR-24·gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'(사용자 결정 O-81 (2)·O-82·O-83 승인)를 §21.2 2단계 (0)에 인용·구현했다. 소자 종류(`Resistor`·`Inductor`) 판정은 지웠고, 표기 차이(엔진 `DC_CONDUCTING_PASSIVE_KINDS` 대 오라클 IR 원소 이름)는 종류 판정이 없어져 함께 사라졌다(오라클 입력 `/passives` kind는 `resistor`·`capacitor`뿐, 840행). 남은 멈춤 = DV-21(차동 출력의 두 출력 판정이 갈리는 경우).

**v0.3.9 상태**(계획 v0.6.16 DR-24, 사용자 결정 O-81 (2)·O-82·O-83): 'DC 성분' 종류 분류 → 경로 판정 하나(§21.2 2단계 (0)). design이 정한 것(계획 위임 범위, '구현 자리'): 판정 함수 이름 `swing_math.dc_feedback_judgment`, 끝점 집합 = 기존 C14 절단 규칙의 넷 목록 재사용, bulk 엣지 없음(정의 문단 엣지 목록대로), `/bias_voltages` 넷을 경유 금지에 명시, 사유 `dc_feedback_judgment_undefined`(이상 전압원), 판정 결과는 새 기록 칸 없이 갈래로만 남김. 새 멈춤 **DV-21**.

**v0.3.10 상태**(계획 v0.6.17 DR-25, 사용자 결정 O-85 (1)(3)·O-86): **DV-21 닫힘** -- 차동 출력은 두 출력 판정이 같을 때만 그 판정, 갈리면 `dc_feedback_judgment_undefined` `why = differential_split`(gain-budget v6.28 N3.8 '차동 출력' 인용); §20 OP-5 착수 막음 해소. **지원 밖 원소 정렬** -- `why = voltage_source` → `element_unsupported`(gain-budget v6.28 N3.8 '지원 밖 원소' 인용; 오라클 입력에서 판정에 닿는 지원 밖 kind는 `/sources` voltage 하나, 나머지 kind는 스키마·`descriptor_kind_undeclared`가 먼저 막음). `bias_not_gate_only`는 그대로(DR-25 (3)). design이 정한 것(계획 위임 '사유 이름은 design'): 새 code가 아니라 기존 `dc_feedback_judgment_undefined`의 `why` 값 둘(`differential_split`, `element_unsupported`) -- 셋 모두 '판정 정의 불능'이라는 같은 뜻이고 §7 어휘(code 하나 + `why`)와 맞음. 지금 열린 멈춤 없음.

(v0.3.0 결정 대기 목록은 v0.3.1에서 닫힘 -- 원문은 history H7)

**알림**(계획과 다른 결정은 아니고, 다른 문서 소유자에게 넘길 것):
* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.8, DR-23 (2) -- 교차 참조, 멈춤 아님) **DV-19 사유 이름 대응**: 오라클 `icmr_feedback_dc_absent`(§7) ↔ 엔진 `icm_config_feedback_no_dc`(design 41 v1.12.5 `88bc5f2f`(브랜치 `design/it2c-o79`) 734행 4.7-3b (1)·744행 code 목록, **승인 대기**). 두 이름은 같은 정의(gain-budget v6.26 N3.8 한 문장)의 양쪽 사유이고, 대응은 design 41 승인 뒤 확정한다. design 41 이름이 승인 전에 바뀌면 이 줄만 고친다(오라클 코드 이름은 바꾸지 않음). 검증자 원인 변화표가 두 쪽 사유를 짝지을 때 이 줄을 읽는다. 전체 짝은 아래 대응표.
* (v0.3.8 둘째 커밋, 검증 N2) **ICMR·슬루 측정 구성 사유 대응표**(엔진 code ↔ 오라클 code + `detail.why`; 검증자 원인 변화표가 읽는 자리 하나). 엔진 이름 출처 = design 41 v1.12.5 `88bc5f2f`(**승인 대기**; `icm_config_feedback_no_dc` 말고는 master `93a9ff82`의 v1.12.4에도 같은 이름이 있음). **입도 차이**: 엔진은 경우마다 code를 따로 두고(`icm_inverting_port_*` 셋 등), 오라클은 code 하나에 `detail.why`(또는 `detail`)로 가른다 -- 짝은 '같은 경우'의 대응이지 이름·개수의 대응이 아니다. 오라클은 엔진 사유를 받지 않는다(NFR-P3).

  | 경우 | 엔진(design 41 줄) | 오라클(§7) | 비고 |
  |---|---|---|---|
**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]**   | 반전 입력 후보 0개 | `icm_inverting_port_none`(734) | `inverting_port_undetermined` | 오라클은 code 하나(후보 0개·2개 이상·분해능 이하·두 출력 같은 포트·레일 폭 0을 함께) |
**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]**   | 반전 입력 후보 2개 이상 | `icm_inverting_port_ambiguous`(734) | `inverting_port_undetermined` | 같음 |
**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]**   | 반전 입력 전달 ≤ 판정 분해능 | `icm_inverting_port_unresolved`(734) | `inverting_port_undetermined` | 같음 |
**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]**   | 단일 출력 + DC 되먹임 없는 선언(입력 ≥ 2; v0.3.9 -- '없음' = 경로 판정, 옛 행 이름 '용량만 선언') | `icm_config_feedback_no_dc`(v1.12.5 734·744 새 이름; 경로 판정을 담을 v1.12.6은 **미확인**(브랜치 머리 `2e60f9c7`에 없음); **승인 대기**) | `icmr_feedback_dc_absent`(뜻 = §21.2 2단계 (0) 경로 판정 '없음') | 정의 = gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' + '단일 출력 + DC 되먹임 없는 선언 되먹임'. 두 쪽 판정이 갈리면 '정의 경계 불일치'(O-63 (2)) |
  | (v0.3.9; v0.3.10 일반화) 지원 밖 원소(오라클 입력에서는 `/sources` voltage 하나) | `icm_config_feedback_element_unsupported`(이름 = gain-budget v6.28 N3.8 '지원 밖 원소' 규칙·N2.1 O-85 (3); design 41 v1.12.7에 들어갈 예정 -- v0.3.10 작성 때 브랜치 `design/it2c-o79` 머리 `ea605a02`는 v1.12.6이라 **미확인**, **승인 대기**). 엔진 운영 경로에서는 그 전에 S1 `s1_dc_conduction`이 `source_kind_unsupported`로 멈춤(`E/graph/CONTRACT.md:394`) | `dc_feedback_judgment_undefined` `why = element_unsupported`(옛 `voltage_source`) | 오라클 = code 하나 + why, 엔진 = 판정 code 하나(S1 분기 이름은 그 앞 단계) |
  | (v0.3.10 둘째 커밋, 검증 N3 -- 경계 행) MOS kind 경계 | S1 `mos_kind_unsupported` = MOS kind ∉ {nmos, pmos}(`E/graph/CONTRACT.md:154`) → `icm_config_feedback_element_unsupported` | 짝 없음 -- 오라클 `/devices` kind는 기술자 `kinds` 키로만 거르고(`descriptor_kind_undeclared`, §7), 판정 그래프는 kind와 무관하게 drain·gate·source 엣지를 만든다 | 경계가 다름: 엔진은 nmos·pmos 밖이면 정의 불능, 오라클은 기술자가 선언한 kind면 판정함. 같은 회로에서 갈리면 '정의 경계 불일치'(O-63 (2))로 변화표에 기록. 13회로는 nmos·pmos뿐이라 지금 갈림 0(**미확인** -- 기술자 `kinds` 실측은 OP-2/OP-3 기술자 작성 뒤) |
  | (v0.3.10; 셋째 커밋 갱신 -- 사용자 결정 O-87 (1) U-1) 차동 출력 두 출력 판정이 갈림 | `icm_config_feedback_outputs_split`(**예약 이름** -- 두 출력 판정 결합과 이 code는 엔진 S-OS2 일반형 card가 구현, IT-2c 몫 아님; 계획 gain-budget v6.28 (10)(f)·O-67 (5)). **그 card 전까지** 엔진은 선언이 있는 차동 출력 전부를 `icm_config_differential_output_structure`(IT-2c fail-closed)로 낸다 | `dc_feedback_judgment_undefined` `why = differential_split`(DV-21 닫힘) | 같은 정의(gb N3.8 '차동 출력'), 이름은 각자 어휘. 같은 회로에서 두 쪽 결과가 다르면(엔진 S-OS2 card 전 `…_structure` 대 오라클 판정 결과 포함) '정의 경계 불일치'(O-63 (2))로 변화표에 기록 |
  | (v0.3.9) `/bias_voltages` 넷이 게이트 전용 아님 | 짝 없음(엔진은 topology `bias_inputs`가 authoring에서 보장됨) | `dc_feedback_judgment_undefined` `why = bias_not_gate_only`(DR-25 (3) -- 바꾸지 않음) | 오라클 입력 전제 검사 |
  | 선언 소자를 절단한 봉인점 해 | `icm_config_feedback_cut`(738) | 짝 없음 | 오라클은 봉인점 계산을 하지 않음(엔진 쪽 경우) |
  | 차동 출력 + 미선언 | `icm_config_differential_output_undeclared`(723·734) | ICMR: 사유 없음(차동 모드 DC 닫힘으로 정의됨, §21.2 2단계 (c), X-35 승인); 슬루: `feedback_config_undeclared` `why = differential_undeclared` | **같은 경우에서 결과가 다름**: 엔진 ICMR = 정의 불능, 오라클 ICMR = 정의됨. 엔진 쪽 DC 닫힘 구현 시점은 gain-budget 몫(이 문서 밖) -- 그 전까지 원인 변화표는 이 행을 '정의 경계 불일치'로 읽음(**미확인**: 엔진 DC 닫힘 card 시점) |
  | 차동 출력 + 선언 | `icm_config_differential_output_structure`(726, IT-2c fail-closed) | ICMR: 사유 없음((a) 또는 (c)로 정의됨); 슬루: (b)(c)에 걸리면 `feedback_config_undeclared` `why = input_network_step_deferred`·`start_op_deferred` | 같은 경우에서 결과가 다름(엔진 후속 card 몫) |
**[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]**   | 공통모드 가중 비대칭 | 짝 없음(**미확인**: design 41에 같은 경우 code를 찾지 못함) | `closure_common_asymmetric` | 오라클 DC 닫힘 벤치 쪽 경우 |
  | 슬루 구성 사유 | 엔진 슬루 손계산 사유는 design 41의 `icm_*` 목록 밖(**미확인**) | `feedback_config_undeclared`(`why` 셋), `slew_step_end_undefined` | -- |
* (v0.3.8, DR-23 (1)) **gain-budget card AP-1 착수 때 oracle 쪽 OP card로 옮길 것**(AP-1 행 '오라클 코드는 AP-1 착수 때 oracle-portability 계획에 OP card를 열어'): §21.6 1b 시작 동작점(시작점 = §11.7 ICMR 공칭 점 기록 `v_in[in_a]`·`v_in[in_b]` 참조, 닫힘 `.op` 둘째 생산자 없음), 1단계 입력 망 계단 갈래, 옛 1b 손 회로 test(history v0.3.8), DV-20의 1b 몫. 이때 `feedback_config_undeclared`의 `start_op_deferred`·`input_network_step_deferred`를 지운다.
* (v0.3.9 둘째 커밋, 검증 N5 -- **백로그**, 멈춤 아님) **bulk(gmb) 엣지 일반화**: §21.2 2단계 (0)은 bulk를 엣지로 넣지 않는다 -- gain-budget v6.27 N3.8 정의 문단의 엣지 목록(DC 전도 원소 양방향, MOS d↔s 양방향, g→d·g→s 한 방향)에 bulk가 없어서다(그대로 따름). bulk→d·bulk→s(gmb) 엣지를 넣을지는 정의 자리(gb N3.8)의 백로그이고, 바뀌면 계획부터. 엔진 design 41(v1.12.6, 미작성)도 같은 엣지 목록(bulk 제외)을 쓰도록 design 41 소유자에게 알린다(두 판정이 갈리면 '정의 경계 불일치').
* (v0.3.10 둘째 커밋, 검증 N4 -- **알림**, design 41 소유자에게) **출력을 건너는 경로 toy**: §18.1 'OP-5 (0) 차동 결합' (xi)처럼 한 출력이 다른 출력을 거쳐(CMFB 저항 Rc1·Rc2) 절단 넷에 닿으면 그 출력은 '있음'이다(gb v6.28 N3.8 정의 -- 끝점 = 선언 절단 넷 집합 전체, 경유 금지 = 레일·구동 입력 포트 넷뿐이라 다른 출력 넷은 지나갈 수 있음). 엔진 design 41(v1.12.7)도 같은 toy((x) 갈림 → 정의 불능, (xi) 일치 → 선언 그대로)를 test로 두어 두 판정이 일치함을 확인하기를 권한다 -- 갈리면 '정의 경계 불일치'.
* (v0.3.9 둘째 커밋, 검증 N2 -- **백로그**) `/bias_voltages` 게이트 전용 조건을 입력 계약 전체(§11.2 1d 교차 규칙, OP-3)로 넓힐지: 지금은 §21.2 2단계 (0)이 판정을 부를 때만 검사한다(`bias_not_gate_only`). 넓히면 OP-3 입력 계약 변경이라 OP-3 card에서 정한다.
* (v0.3.0) **gain-budget EO-1**(N6.20): 계약 = §11.1~§11.4·§11.7. EO-1 design이 칸 선택의 근거로 K-4 표(판정에 닿는 칸)를 쓴다. EO-1 완료 조건 (1)의 '스키마 위반 거부 red'는 §11.3 E1~E16로 보일 수 있다. 결과 `summary.conduction_definition`이 '꺼짐 정의 판' 칸이다(K-5).
* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.0) **gain-budget VB-1·ME-1·PW-1a**(계획 U-4·U-5·U-6): 새 measure 이름 `offset_sys_mv`(OP-5)·`power_dc_w`(OP-11), 슬루는 기존 이름 `slew_rate_v_per_s`(OP-10). 엔진 `verified_by` 연결 변경은 그 card들 몫.
* (v0.3.0) **gain-budget DEC-23·N3.8 557행 문언**: DV-8·DV-9의 명확화 요청(정의 소유자). (v0.3.1 처리됨 -- gain-budget v6.20 개정, O-50 G1·G2)
* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.3 셋째 커밋) **U-6 알림 -- EO-1 계약 변경**(gain-budget EO-1·OP-5/OP-10 통합 병합 엔진 커밋 소유자에게): §11.7 결과 계약이 바뀐다 -- (a) 기록 파일 이름 `<stem>.<kind>.<rid16>.compare.json`(OP-5 병합부터, `kind` = `run_request.kind`), (b) 호출자 의무: 한 요청(같은 `range_input_fp`)의 모든 실행은 같은 `<out_dir>`, (c) `run_request` 칸(출력 전용), (d) 범위 metric 최종 값·제약 판정 = 확정 실행의 `range_final` 하나(잠정 실행 verdict에 범위 제약 없음), (e) 새 입력 칸 `confirmed_range`(2단계 호출 자리가 생산)·`dc_sweep.input_dc`(EO-1 생산자가 spec 입력 DC 선언에서 옮김), (f) 범위 끝 기록의 괄호 좌표·분해능 칸 삭제(`pass_point_id`·`fail_point_id` → `conduction.points[]`, r은 §18.3 식으로 재계산). 생산자 갱신 커밋은 계획 U-6대로 OP-5·OP-10 통합 병합에 든다. (v0.3.4 더함) (g) `confirmed_range` 정의 불능 끝 = `{undefined: true, record_id}`(`reason` 없음 -- 사유는 엔진 `stage2_judgment`에) (h) `range_final.source` 정의 불능 끝 = 같은 꼴(`null` 아님) (i) `swing_icmr.input_dc_V`·`input_dc_pending` 삭제(OP-5; 선언 입력 DC = `dc_sweep.input_dc` 하나) (j) `.tf` A 기록 = sim 단계 `sim.a_dc`(v0.3.5 정정; 옛 코드·기준선 이름 `offset_mc.a_dc_signed` → `sim.a_dc.value`, §11.5), 계통 offset 기록 = `sim.offset_sys`, σ·계통 offset의 정의 불능 사유 `a_dc_undefined`(엔진 쪽 '정의 경계 불일치' 대조에 검증자가 읽음) (k) (v0.3.5) compare JSON `sim_ref`(sim.json 정규 sha256), 옛 `summary.u6` 사본 삭제(OP-3, X-R5). (v0.3.6 더함 -- DR-21 'X-R3~X-R5 계약 변경 알림', O-67 (4) 승인) (l) 승인된 계약 변경 셋: `sim.a_dc`·`sim.offset_sys`(sim.json) 자리·이름(X-R4), `sim_ref` 참조와 `summary.u6` 삭제(X-R5), 갈래 발동 시 `.dc` 미요청(X-R3) -- EO-1 2단계 배선·OP-6 PC-10·검증자 대응표가 따라 바뀜 (m) ICMR 점 기록 `m` → `v_in`(m은 `icmr_coord` 함수), `icm_margin_v` = 포트별 식, `inverting_port_undetermined.detail.resolution` 삭제 (n) 슬루 `Tran.ic`·능력 `tran_ic_bias_only`, 차동 출력 DC 닫힘 ICMR 벤치(`measure_feedback` 칸 형식은 그대로).
* **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.1) **엔진 쪽 OP-5 통합 병합 커밋**(계획 N3.9 '배선' (i)~(iii), O-55 U2): EO-1 생산자 갱신(`intended_region`·`measure_feedback`·`output_reference`·`dc_sweep`), 2단계 호출 자리·`sweep_rezoom` 재요청, graph-consumption `dc_off_current` 출력 전용 선언. O-56 (a) search_domain kind 거르기·(b) headroom-chain `dc_sat_v` off 갈래는 엔진 쪽 몫이고 이 문서는 칸(`intended_region`)만 제공한다.
* (v0.3.0) **headroom-chain HC-O**(U-H11 '입력 칸은 OP-0 스키마를 따른다'): (v0.3.2 정정) 선언 영역 칸 이름 = `intended_region`(객체 {소자: `triode` \| `off`}, 칸이 생긴 뒤 필수·빈 객체 허용, §11.6, O-53 B1 -- 옛 `declared_triode`를 넓힌 같은 칸). OP-5와 HC-O 가운데 먼저 병합하는 card가 칸을 더한다.
* (v0.3.0) **offset-trim 구동기**(design §20.1): `output_reference` 칸 형식은 그대로이고 위치가 G-18 확장 칸(§11.6, OP-5가 더함)으로 바뀌었다 -- OP-5 병합 전에는 그 칸을 넣은 입력이 거부된다(OP-6은 OP-5 뒤라 실제 영향 없음).
* 계획 N3.5.1의 기준 문구('offset-trim v0.5.2 `a293411` 455-462행')는 master v0.5.6 `86e5adc` 466-473행으로 다시 대조됐고 내용 차이가 없다(§12.8). 계획 문구 갱신은 계획 소유다.
* offset-trim 계획 N3.9 '순서 의존'(master 477행)이 oracle-portability 계획을 '초안, 승인 전'으로 적는다. offset-trim 소유 문구다.
* 상위 문서 개정 병합본(`b105b65`)과 §17 문안의 일치는 이 card가 대조하지 않았다.
* (v0.2.6, 엔진 쪽 낡은 인용, S-36) OP-3~OP-5가 옛 오라클 파일을 지우면 엔진 쪽 주석·docstring의 오라클 파일 인용이 낡는다: `E/metrics/verified_by.py:35, :48`, `E/tests/metrics/test_device_sigma.py:9`, `E/metrics/junction_cap.py:16`, `E/tests/metrics/test_verified_by.py:1-12`. 계획 완료 조건 8a(엔진 diff 0, 예외 둘)가 이 기능 card에서 고치는 것을 막으므로 고치지 않고, 엔진 소유 card(gain-budget 계획)에 알린다. 기능은 바뀌지 않는다(주석·docstring).
* (v0.2.6) `A/lut_v2_location.json`을 바꾸는 card는 같은 변경에서 오라클 기술자 `lut_record_root.location_decl.sha256`을 갱신해야 한다(§10.2). 계획 X-13 알림과 같은 내용을 gain-budget 쪽 LUT 위치 변경 절차에 넣도록 알린다. (v0.3.0, DR-14) 갱신 값 = 그 파일의 **LF 정규화 sha256**(다시 잰 값, 사례 `07299556…`)이다.

**v0.4.0 상태**(계획 v0.6.25 대조, 2026-11-03): DV-6~DV-21의 전도·2단계·지목·ICMR 구성 갈래는 상위 O-115·O-205·O-210으로 대상 소멸하거나 대체됐다(각 행 낡음 표지). 새 멈춤 없음. **계획 공백**(계획부터 고칠 것 -- 이 판은 지어내지 않고 표지만):
* **PG-1 닫힘**(위임 A-8 (b), 계획 v6.38.8·0.6.26): EO-1 판정 실행을 OP-5 뒤로 옮겼다. OP-2·OP-3·OP-5·OP-7은 공통 선행의 코드 병합을 막지 않는 병렬 줄이고 LA-1 측정 시점 전까지 끝낸다. EO-1 코드는 판정 없이 '미완료(보류 다리)'로 병합하므로 `threshold_eps1` 판정 기록이 생기지 않는다. 옛 문언은 history v0.4.2.
* **PG-2 `@m[id]` 어휘**: 정본은 채널 op ID를 `@m[id]`로 적는다(사례 ngspice). PDK·시뮬레이터 이식(O-197) 문언상 기술자 op 파라미터 칸 소관이다. 이 판은 §10.2 칸으로 읽고 어휘를 코어에 넣지 않는다. 계획 N3.9 문언 표지만 필요.
* **PG-3**: EO-1 순서 표지는 계획 0.6.26 OP-7 행에 반영됐다(닫힘). 옆 선언 기록 조각의 측정 방법 = §16(v0.4.3, 위임 A-53·A-54, 아직 실행 안 함). 재측정이 안 되면 선언을 쓰지 않고 멈추고 보고한다.
* **PG-4 닫힘**: 계획 0.6.26 '낡은 문구 넷 정리'.
* **PG-5 noise 비트 동일 범위**(v0.4.1 재판정): 계획 OP-5 행은 '상한에 닿지 않은 기준선 입력 = 비트 동일'과 'f_hi를 상계 식에서 직접'을 함께 적는다. 옛 코드가 상한 안에서 확장한 입력(`top_extensions ≥ 1`)과 n̂ ≠ 2로 T 판정이 옛 판정과 갈리는 입력은 격자가 달라 비트 동일일 수 없다 -- 이 판은 '정의를 바꾼 칸'으로 변화표에 적게 두고 계획 문언 정정을 요청한다.
* **design 40·41 본문 수정 필요 목록**(고치지 않음): design 40 §4 오라클 머리 'v1.15.2' 문단·역할 문단(이미 상위 후속 정정 표 2061행), design 41 v1.12.4 780·784·811행의 포트별 ICMR 세 metric 인용(U-106 V_cm으로), EO-1 design의 `kcl_zero_current_devices`·`counted_rails`·`parasitic_c_F`·`step`·`predictions.nodes` 출력 넷 생산(칸 이름은 이 판 작성자 판단 -- EO-1 범위 4 개정판(묶음 ⑥)이 읽음).

### 19.3 측정·확정 대기 칸(OP-1·OP-1a·OP-3·OP-7·R6 원문 보관, 하나를 고르지 않음)

(v0.2.6 머리 고침) 이 표는 OP-1·OP-7 측정만이 아니라, 다른 card(OP-1a 보관, OP-3 병합 조건 (c), R6 원문 보관 = OP-2 병합 조건)가 채울 칸도 담는다. '측정됨'·'철회' 행은 기록이다.

| 칸 | 측정 | 상태(v0.2.4) | 절 |
|---|---|---|---|
| D-1 능력 없는 어댑터의 기본 실행 방식(G-13) | OP-1 기준선 창당 시간 | **측정됨**(S-19). 확정은 OP-4 | §8.4 |
| sky130·ngspice 네이티브 MC 켜는 법·소자별 독립 여부, 직접 루프를 쓴 이유 | OP-1 (i) | **측정됨**(S-12·S-13): `param_redefine`으로 소자별 독립('전역 파라미터가 모든 인스턴스에 같은 값' 가설은 아님). 직접 루프를 고른 경위 자체는 재지 않았고, 옛 코드 주석(`O/oracle_offset_mc.py:22-24`)은 그 배율이 기하 단위·배수 차이를 덮는다고 적는다(S-13, O-6 D-b) | §10.3, §10.4, §10.6 |
| 지금 LUT 슬라이스 meta의 `model_files_sha256` 존재 | OP-1 (ii) | **측정됨**(S-15): 38/38 있음 | §12.5 |
| 지금 LUT 슬라이스 meta의 생성 시뮬레이터 판 존재 | OP-1 (iii) | **측정됨**(S-15): 38/38 `ngspice-46` | §16 |
| 지금 LUT 경계 앵커 점에서 시뮬레이터가 고른 bin | OP-7 검증자 | 대기 | §16 |
| cap·mismatch 세트 메타의 생성 시뮬레이터 판 기록 | OP-7 검증자 | 대기(v0.2.4 추가) | §16 |
| 모델 bin 표 W 경계에서 시뮬레이터가 고른 bin | OP-7 검증자 | 대기(v0.4.3 추가) | §16 |
| 동률 칸 생성기 기록 bin이 가리키는 모드 | OP-7 검증자 | 대기(v0.4.3 추가, v0.4.7 방법 교체) | §16 |
| PC-3 표본 수 기본값의 실행 비용 | OP-1 | **측정됨**(`R/m1_native_mc.jsonl` 12행, v0.2.5 인용 정정): 소자 쌍 벤치 표본당 0.152 s, 200 표본 30.3 s(r = 0.05면 201 표본) | §12.3 |
| 차동 이득 실수 판정 변경이 기준선 `status`를 바꾸는 사례 | OP-1 | **측정됨**(S-14): 바꾸면 170건. D-c로 바꾸지 않음. (v0.3.0) O-43 D1 (d)로 판정 자체가 없어진다(`.tf`, §21.5) -- 옛 `1e-3`으로 `unavailable`이던 입력의 `status` 변화는 OP-5 원인 변화표에 적는다 | §13.2, §14 |
| ngspice 오류 로그 → 오류 코드 대응표 | OP-1 기준선 로그 | **초안**(§7.1, S-18). 확정은 OP-3·OP-4 | §7 |
| ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호 | 원문 보관 문서 작업(X-D4 수용 O-4). **OP-2 병합 조건**(v0.2.2) | (v0.4.8, A-80) OP-2 + OP-3 card가 닫음: `A/simulator_sources/ngspice_46_manual/source.pdf`, 쪽 = `calibration.json`. 전역 기하 지시 `affects`의 출처(§8.3)도 같은 원문 | §8.3, §14 |
| 기준선 입력 가운데 DC 풀이 허용오차 선언이 없는 것(X-D4) | OP-1 | **측정됨**(S-20): test 입력 1개(reltol 없음) | §8.3 |
| dump `lut_meta.W_ref_m`이 없는 기준선 생산 dump | -- | **철회**(v0.2.5): B-13 철회로 대상 없음(`legacy_adapter`는 LT-1 순서 3이 삭제) | §11.4 |
| 기준선 C10 과도 가운데 (가) 방식에서 시간 상한에 걸릴 사례 | OP-4 착수 검증자 | 대기(v0.2.4 추가) | §8.4 |
| 기존 LUT 역할 옆 선언의 근거 두 측정(`generator_sha256` 판 찾기·보조 입력 추가 줄, LUT 생성 넷리스트 include 그래프) | OP-3 병합 조건 (c) 검증자 | 대기(v0.2.5 추가). 지금 판의 추가 위치는 S-29(`A/sky130_lut_sweep.py:688, :891`) | §12.5 |
| 어댑터 기본 abstol 값과 출처 쪽 | R6 원문 보관(OP-2 병합 조건) | (v0.4.8) OP-2 + OP-3 card가 닫음(S-28: 옛 값 없음) | §8.3, §14 |
| 시간 걸음 실패 로그 문장 형태 | (v0.4.8, A-80) OP-4 실측 로그(매뉴얼에 문장 없음) | 대기(v0.2.5 추가, 기준선 사례 0, S-30) | §7.1 |
| 기준선 표본별 V_os | OP-1a 검증자(재구현 스크립트) | 대기. v0.2.6: DV-5는 O-9로 닫혔고 방법이 정해짐(§13.2) | §13.2 |
| (v0.3.0) 기존 LUT meta `model_files_sha256`의 모양 | OP-3 착수 조건(계획 N9 '관찰' 행) | **측정됨**(S-38): 폭 슬라이스 32 평탄, 결합 파일 6 LUT 소자 키 중첩. 두 모양 읽기 = §11.2 2b | §11.2, §12.5 |
| (v0.3.0) 폭 슬라이스 `generator_sha256` `8df35d2e…`의 생성기 판 | OP-3 착수 조건(계획 N9 '미발견' 행) | **측정됨**(v0.4.8, A-80): 위치 선언 `root` 아래 파일, sha 일치, 저장소 이력에는 없음. 근거 (a)(b) 재확인은 OP-3 병합 조건 (c) 판정자 | §12.5 |
| (v0.3.0) 기준선 입력 LUT의 모델 기록 | OP-3 병합 조건 (b) | **측정됨**(S-39): 없음 → §19.2 DV-7 | §11.5 |
| (v0.3.0) ngspice `.tf` 차동 출력·로그 형식 | OP-5 | **측정됨**(S-42) | §21.5 |
| (v0.3.6, DR-22 착수 실측) current_reuse 되먹임 선언에 입력 망(Cin 등) 유무 | design 작성자(읽기만) | **측정됨**: `A/library/current_reuse_telescopic_ota.sizing_spec.json:141-142` `feedback.elements = ["Cf1", "Cf2"]`; topology `passive_elements` Cf1 = (Vom, Vip), Cf2 = (Vop, Vim), Cs1 = (Vip, gnd), Cs2 = (Vim, gnd) -- 입력 망 원소 없음 → 슬루 `no_input_network`(정의 불능), 사용자 보고((v0.3.8) 입력 망 갈래가 AP-1로 빠져 사유 = `input_network_step_deferred`, 정의 불능 그대로 -- §19.6 F-11) | §21.6 1단계 |
| (v0.3.6) ngspice `uic` 없는 `.ic` 의미의 매뉴얼 쪽 번호 | R6 원문 보관(OP-2 병합 조건) | **미확인**(DV-20). 코드 사용 근거 `O/oracle_netlist.py:596-598, :625, :720, :765` | (v0.3.8; 둘째 커밋 M1 OP-4로 정정) OP-4 C10의 `tran_ic_bias_only` 선언 근거(옛 '§21.6 1b'는 AP-1로 옮김) |
| (v0.3.0) 기준선 입력의 스키마 밖 키·기준 레일 전압 | OP-3 | **측정됨**(S-44, §11.1 `/rails` 행): 닫힌 키 집합·`reference_rail_voltage` 규칙의 기준선 영향 0 | §11.1 |

### 19.4 원래 취지와 다름(따로 보고)

| ID | 내용 |
|---|---|
| X-D1 | (**수용(O-3)**, v0.6 O-6 D-c로 하나 더함) '출처 미확인 기존 상수' 여섯(옛 반복 상한 다섯 + 차동 이득 실수 판정 `1e-3`)을 출처 확인 없이 그대로 옮긴다(B-8, §14). '상수 발명 금지' 원칙에서 보면 기존 위반을 이 기능이 정리하지 않고 넘기는 것이다. 정리하면 N4 동일성이 깨질 수 있어서다(`1e-3`은 실측 170건, S-14). 유도는 백로그. **(v0.3.0, 계획 X-D1 v0.6.9)** `1e-3`은 이 목록에서 빠진다 -- 사용자 결정 O-43 D1 (d)로 A를 `.tf`로 직접 재고 상수와 `.ac` 첫 점 경로를 지운다(§14, §21.5). 남는 '출처 미확인 기존 상수'는 반복 상한 다섯이다 |
| X-R1 | (v0.3.4 **승인됨 -- 사용자 결정 O-61, design 범위**(계획 DR-19); 그대로 유지) (v0.3.3, **원래 취지와 다를 수 있음 -- 사용자 보고 대상**) 기록 파일 이름 꼴 `<stem>.<kind>.<rid16>.compare.json`(§11.7): 옛 `<stem>.compare.json`을 OP-5 병합부터 바꾼다(원 범위·재훑기·확정 실행이 같은 `<out_dir>`에서 덮어쓰지 않게 -- 검증 B1). 계획은 형식을 design에 맡겼지만 EO-1 계약(파일을 찾는 쪽)과 옛 산출물 이름 관례가 바뀐다 |
| X-R2 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.4 **승인됨 -- 사용자 결정 O-61, design 범위**(계획 DR-19, 계획 G-19 검사 (1) '입력 지문' 문언이 이 구성을 인용); 그대로 유지. v0.3.4 보완(design-validator 권고): `range_input_fp`와 `input_sha256`의 축 차이를 §11.7에 적었다 -- 앞은 측정 동일성(실효 입력, 실행 종류 칸 제외), 뒤는 파일 대응(입력 파일 raw 바이트); 서로 유도·대체하지 않음) (v0.3.3, **원래 취지와 다를 수 있음 -- 사용자 보고 대상**) `range_input_fp` 구성(§11.7): 계획 G-19 검사 (1) '같은 입력 지문'을 입력 JSON만이 아니라 CLI가 덮어쓴 실효 값 + `adapter_fp` + `descriptor_fp`까지 포함한 실효 입력 지문으로 정했다(검증 M1) -- 어댑터·기술자가 바뀐 기록을 지목하면 거부되어 '같은 입력'보다 엄격하다 |
| X-R3 | (v0.3.5, **원래 취지와 다름(경미) -- 승인됨(사용자 결정 O-67 (4), design 범위; v0.3.6 표시)**, gap #21) 갈래가 발동하면 계통 offset의 `.dc` 출력 고정 풀이를 **요청하지 않는다**(§21.4 4단계 (3)). 계획 N3.9 `offset_sys_mv` 행 (iii)·O-63 (2) '`.dc` 해가 수렴했더라도 값을 내지 않음'과 판정 결과(값 없음, `a_dc_undefined`)는 같지만, 갈래 발동 실행에 `.dc` 수렴 정보가 남지 않고 (iv) '`.dc` 수렴 실패 따로 기록'이 그 점에서는 생기지 않는다. 근거: 소비자 없는 계산을 두지 않는다(만들면 쓴다·graph 규칙). 권고: 받아들임 |
| X-R4 | (v0.3.5, **원래 취지와 다름(경미) -- 승인됨(사용자 결정 O-67 (4), design 범위; v0.3.6 표시)**, gap #16·검증 M2) `.tf` A 기록 자리를 `offset_mc` 안(옛 `offset_mc.a_dc_signed`)에서 sim 단계 `sim.a_dc` 하나로 옮기고 계통 offset 기록을 `sim.offset_sys`로 둔다(§21.5 3단계, §21.4 4단계). writer 하나·사본 없음이지만 결과 칸의 자리·이름이 바뀌어 OP-6 PC-10·EO-1 2단계 배선·검증자 N4-2 비교 칸 대응(§11.5 새 행)이 따라 바뀐다. DR-20 '기록 칸' 위임 범위. 권고: 받아들임 |
| X-R5 | (v0.3.5, **원래 취지와 다름(경미) -- 승인됨(사용자 결정 O-67 (4), design 범위; v0.3.6 표시)**, 검증 M2) compare JSON의 옛 `summary.u6`(`O/oracle_compare.py:464` -- sim의 `noise`·`offset_mc`·`swing_icmr`를 compare로 복사)를 OP-3 코어 compare 이관에서 지우고 `sim_ref = {sha256}` 참조로 바꾼다(§11.7). 승인된 사본 예외(계획 N3.3·N3.5)에 없는 값 사본이라 graph 규칙 2·4로 참조가 기본이다. `record_id`가 sim 결과까지 묶게 되고, 보고서(`:689`)·검사 (1)·EO-1은 sim.json을 sha256 확인 뒤 읽는다. OP-3 결과 계약 변경(OP-3 동일성 비교에서 `summary.u6`는 sim.json 쪽 칸으로 대응). 권고: 받아들임 |
| X-35 (계획 인용) | (v0.3.6, 계획 v0.6.14 X-35, **원래 취지와 다름 -- 승인됨 O-67**) 차동 출력 ICMR 측정 구성: 미선언·DC 성분 없는 선언이면 정의 불능이던 규칙(O-52 확인 1)을 차동 모드 DC 닫힘으로 대체(§21.2 2단계 (c), §7 `feedback_config_undeclared` ICMR 갈래 삭제). 슬루는 미선언 차동 출력 정의 불능 유지(O-69 (1)) |
| X-D2 | 옛 진입점 여섯을 `oracle_run` 하위 명령으로 합친다(B-2). README의 '파일마다 독립 진입점 1개' 원칙(`O/README.md` '파일' 절)과 다르다 |
| X-D3 | (v0.2에서 해소) PC-10은 offset-trim design TR-0T가 G-15를 닫아(선언 기준을 온도 무관하게 그대로) 정의했다(§12.2). 그 design은 master에 병합됐다(T-40) |
| X-D4 | (v0.2, **수용(O-4)**. 할 일: ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호 채우기 = 원문 보관 문서 작업이고 **OP-2 병합 조건**(v0.2.2), 영향받는 기준선 입력 측정 = OP-1) T-39에 따라 DC 풀이 허용오차를 선언 없이 쓰지 않게 했다. 그래서 지금 기본 허용오차(`_NGSPICE_DEFAULT_TOL`)의 출처(매뉴얼 쪽)가 채워지기 전에는, 입력에 허용오차 선언이 없는 기존 오라클 입력이 `dc_tolerance_undeclared`로 멈춘다. 지금 smoke 입력은 `testbench.options`에 reltol·vntol·abstol을 가진다(S-6 사례). 영향받는 기준선 입력은 OP-1에서 test 입력 하나로 쟀다(S-20) |
| X-18 | (계획 X-18, **수용(O-6)**) 네이티브 MC가 '켜기만'이 아니라, 첫 조합에서는 '불일치 변수를 시뮬레이터 분포 함수로 다시 선언'(`param_redefine`)이다(S-12). 겉모양은 O-1이 지운 직접 덮어쓰기와 비슷하지만 값은 시뮬레이터 RNG가 소자마다 뽑고 분포 값은 PDK 원본 선언에서만 온다(§10.4). 이 문서는 계획 정의를 그대로 옮겼다 |
| X-D5 | (v0.2.6, **승인됨(O-11)**: 권고대로 -- 오라클 쪽 해석 사본 유지 + gain-budget 계획에 '`E/lut/CONTRACT.md` 1.8을 바꾸는 card는 오라클 해석 코드·test 기대값을 같은 변경에서 고친다' 동반 수정 절차, `pdk_root` 없을 때 거부하는 엄격 유지) `lut_record_root` 해석을 엔진 계약 `E/lut/CONTRACT.md` 1.8 규칙과 같게 오라클이 **새로 쓴다**(엔진 import 금지). 그래서 (1) **drift 위험**: 엔진 계약·구현이 바뀌어도 오라클 쪽 사본은 따라가지 않고, 두 구현을 서로 불러 대조하는 test도 두지 않았다(§10.2) -- 어긋남은 형식 규칙 기대값 test가 엔진 계약 원문에서 다시 쓰일 때만 잡힌다. 엔진 계약 1.8을 바꾸는 card가 오라클 해석 test 기대값도 같은 변경에서 고치도록 알린다(§19.2 알림과 같은 방식) (2) **의도된 엄격**: 위치 선언에 `pdk_root`가 없을 때 엔진은 LUT meta 절대 경로로 돌아가고 오라클은 거부한다(`lut_location_decl_invalid`). 엔진과 같은 데이터에서 엔진은 돌고 오라클은 멈출 수 있다 |
| X-D6 | (v0.2.6, 의도된 엄격) 어댑터 지문은 디스크의 모든 파일(제외 목록 밖)을 묶으므로(§0), 어댑터 패키지 아래에 잔여 파일(편집기 임시 파일, 지우지 않은 산출물)이 있으면 그 기계의 지문이 검증자 기계와 달라진다. 그러면 능력 기록이 `oracle_capability_stale`로 무효가 되어 다시 만들어야 하고, 캐시도 miss가 된다. 틀리는 방향이 '거부'이므로 판정 약화가 아니다. 대처는 잔여 파일을 지우거나 기록을 다시 만드는 것이고, 제외 목록을 넓히는 것은 §8.3 절차(근거 P-1을 적는 design 개정)로만 한다 |
| X-26 (계획 인용, DR-15) | 기술자 참조 sha256(LF 정규화)과 엔진 `decl_sha256`(raw)의 정의가 다르다. **계획 v0.6.8에서 해소**(사용자 결정 O-16 (1)): gain-budget card SH-1 병합 뒤에는 정의가 같다. 과도기(SH-1 전)에는 정의가 다르고, 이 문서는 어느 쪽이든 파일 바이트에서 다시 재어 대조하므로(§10.1) 순서·선행 조건이 없다. SH-1 뒤에도 '정의가 다른 값끼리 비교하지 않는다'와 X-13 재측정 방식은 유지한다 |
| X-27 (계획 인용, DR-15) | '기계 무관'은 기술자 자기 칸까지만 성립한다(계획 v0.6.8 재정리). 남는 빈틈: 기존 공유 LUT의 raw 기록(`model_files_sha256`)은 CRLF 체크아웃에서는 기계 의존 일치로 돌고 LF 체크아웃에서는 거부된다(엔진과 오라클이 같은 규칙, 같은 결과). `generator_sha256`은 엔진이 대조하지 않고 오라클(OP-3 착수 조건)·OP-8만 대조한다(O-18). 폭 슬라이스 32개의 `8df35d2e…`는 (v0.4.8) 위치 선언 `root` 아래 파일이다(§12.5 근거 (a), 계획 N9) |
| X-29·X-32 (계획 인용, DR-15) | `icmr_v`·`icm_margin_v`(출력 고정 해제)와 `swing_out_v`(정의 일반형·범위 조건 정정)는 **닫힘 -- O-34 규칙으로 해소**: 정의를 바꾼 칸이라 N4 0번 '동작 변경' 기준(정의 문장 손 회로 test + 검증자 원인 변화표)으로 판정하고 card별 예외 승인은 없다(§18.1 '10 정의 대조', §21.2) |
| X-30 (계획 인용) | 범위가 '이식'에서 측정 정의 추가·변경으로 넓어진다(계통 offset `.dc`, 슬루 `.tran` OP-10, 단일 입력 swing·ICMR, 전력 OP-11). 이 문서 §21이 그 절차다 |
| X-31 (계획 인용) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 포화 여유 `judge.sat_margin_V`를 범위 정의에서 빼고 판정 단계로 옮긴다(§21.2 -- 범위 창은 여유 0, 합격 판정의 포화 확인은 여유를 그대로 씀). `judge.off_current_A`는 판정에 쓰지 않게 되어 OP-5에서 지운다(§11.6 B-34) -- 그 칸을 쓰던 사용자 스크립트의 입력이 OP-5 뒤 `oracle_input_schema_invalid`로 거부된다 |
| X-33 (계획 인용, DR-15) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 합격 판정 '꺼짐' = 봉인 9 식(사용자 결정 O-45 U2 승인, O-46 (2) 값의 출처). 옛 ε = 1 기준으로 PASS였던 점이 FAIL이 될 수 있다(합격 기준이 엄격해짐). OP-5 전 기간 결과에는 `summary.conduction_definition = "threshold_eps1"`이 적혀 구분된다(§11.7) |
| X-D7 | (v0.3.1 **수용 -- 사용자 결정 O-50 O4**, 계획 G-18 '입력 키 집합은 모든 층에서 닫는다') (v0.3.0, 이 문서, 의도된 엄격) **입력 키 집합을 모든 층에서 닫는다**(B-29). 옛 스키마는 대부분 열려 있어 생산자가 모르는 칸을 넣어도 오라클이 조용히 무시했다. 이제는 거부한다. 기준선 입력 593개에는 영향이 없음을 쟀다(S-44). 그러나 저장소 밖에서 이 오라클을 부르던 스크립트가 여분의 칸을 넣고 있었다면 OP-3 뒤 거부된다. G-18 확장 칸이 생산자 갱신과 같은 병합에서만 들어오게 하는 장치이기도 하다(§11.0) |
| X-D8 | (v0.3.1 **수용 -- 사용자 결정 O-50 O4**) (v0.3.0, 이 문서) **거부 때 거부 기록 파일 하나를 쓴다**(B-33). 옛 C13은 '스키마 위반이면 아무 산출물도 쓰지 않음'이었다. EO-1 판정 배선이 거부 사유를 기계로 읽어 점 레코드에 붙여야 해서(gain-budget N6.20 범위 (2)) 바꿨다. 넷리스트·결과는 여전히 쓰지 않는다 |


**v0.4.0 추가**(표 아래 추가):

| ID | 내용 |
|---|---|
| X-R7 | (v0.4.0, **원래 취지와 다름 -- 작성자 도출, OP-5 착수 조건 = 사용자 확인(O-214 미룬 결정 (1))**) `confirmed_range`·`range_final`·`sweep_rezoom`·`range_pointer_rejected` 삭제, O-59 (3) DV-12·O-62 (2) P10 대상 소멸 |
| X-R8 | (v0.4.0, 승인 상위 O-205·O-210) 판정 한 단계 -- X-33·X-34·O-50 G5·O-55 U2·O-53 B2 대체. (승인 상위 O-115) ICMR servo -- O-50 G4·O-67·O-68 ICMR 갈래·O-79·DV-19 대체 |
| X-R9 | (v0.4.0, 계획 표지 그대로) OP-3 DUT 저항 C_par/2 -- card 성격 확장. OP-11 DUT 레일 단자 전류 -- 옛 '레일 전압원 전류' 대체 |
| X-R10 | (v0.4.3, 상위 위임 A-54·A-58, **원래 취지와 다름 -- LA-1 재점검**, 계획 X-37) §16 저장 자리를 `<lut 폴더>` 기본안에서 저장소 파일로, 측정에 W 경계·LUT 생성 모드 출처를 더함, 묶음 값에 보조 입력 포함, `evidence.mode` 칸 추가. §11.5 '기계적 대응만'에 중첩 meta 키 유도 한 문장 |
| X-R11 | (v0.4.4, 위임 A-56·A-58, **원래 취지와 다름 -- LA-1 재점검**, 계획 X-37) OP-1b가 OP-3 (c) 역할 근거 측정 일부를 r2에 대해 앞당겨 재고 판정 기록에 둔다(옆 선언 파일은 OP-3 몫). §11.5 '기계적 대응'에 변환 인자 `exe` 추가 |
| X-R12 | (v0.4.7, 상위 위임 A-75, **원래 취지와 다름 -- LA-1 재점검, 사용자 보고 대상, 번복 가능**, 계획 X-38) §16 LUT 생성 모드 출처: **독립 재측정 → 생성기 자기 기록**. 값 대조를 기록 bin 이름 대조로 바꾸고 §16 형식에 `evidence.source_basis` 칸을 더함. (v0.4.8 정정, 상위 위임 A-80) '생성기 원본 미발견'은 틀렸다: 위치 선언 `root` 아래에 있다. `source_basis` 표지 문언은 그대로 맞다 -- 기록 bin은 그 생성기 실행이 쓴 것이고 생성기는 호환 모드를 기록하지 않는다(계획 history 0.6.30 행) |
| X-R13 | (v0.4.8, 상위 위임 A-80, **원래 취지와 다름 -- LA-1 재점검**, 계획 X-39) OP-2 + OP-3: OP-4·OP-5 전 기간 미측정과 PM 정의 불능(§20 OP-3), 옛 test 이전 축소(§18.2), 근거 (a) 출처 확장(§12.5), DUT 저항을 SF-1 통합 병합 쪽으로(§10.6·§18.1·§20), 시간 걸음 문장 근거 이동(§7.1) |
| X-R14 | (v0.4.9, 상위 위임 A-84, **원래 취지와 다름 -- LA-1 재점검**, 계획 X-40) OP-5 병합 선행에서 OP-4 뺌(§20, OP-4 전 PM 판정 불능, LA-1 측정 전 필요), 13회로 비트 동일·엔진 리터럴 넘김(§16), 꼬리 검사 자릿수 폭(§18.3), `measure_feedback`·DC 되먹임 판정·포트별 `.tf`를 OP-10으로(§7·§11.6·§20·§21.5), 지목 왕복 삭제를 위임 채택(X-R7), `nodes_full`(§5·§21.2), `bin_rule_decl`·빈 설정 파일(§8.1·§10.2·§16) |

### 19.5 graph 단일 정본 자체 점검(v0.3.4 변경분, 프로젝트 CLAUDE.md '★graph 단일 정본' 1~7)

| 변경 | writer(하나) | 소비자(읽기만) | 사본·둘째 생산자 | 계획 밖 결정 |
|---|---|---|---|---|
| `sim.a_dc` 기록(§21.5 3·4단계) | sim 단계 코어 `measures_dc`의 여기 방향 `.tf` A 측정 1~4단계 하나(free 실행당 최대 1회, 있는 조건 §21.5 3단계) | `mc_math`(σ), §21.4 4단계(V_id*), PC-10, 검증자 원인 변화표; compare는 `sim_ref`로만 | 없음 -- 옛 `offset_mc.a_dc_signed`(design v0.3.3 이름 `a_dc_tf` 등)를 옮김(같은 양, 자리·이름만); `offset_mc`·`offset_sys`·compare에 A 값 칸 없음; V_id* 벤치에 둘째 A 측정 없음(계획 (i)) | **원래 취지와 다름(경미) -- 사용자 확인 X-R4**(DR-20 '기록 칸' 범위) |
| 갈래 판정(`a_dc_below_resolution`) | 같은 1~4단계(A = 0은 지금; A ≠ 0 분해능 식은 DV-17 대기 -- 정해지면 §21.2 반전 입력 판정과 같은 함수 하나) | σ·V_id*는 `sim.a_dc.status`만 읽음(둘째 검사 없음 -- gain-budget DEC-23 '갈래 판정 자리 하나'의 오라클 쪽 대응) | `detail.resolution`은 판정 기록(출력 전용, DV-17 뒤), 다른 자리가 재판정하지 않음 | 분해능 정의 = gain-budget N3.8 인용, 새 상수 없음 -- V/V 식 없음은 멈춤 DV-17(만들지 않음) |
| 사유 집합·순서 | `sim.a_dc.reason`(`sweep_direction_undeclared`·`nominal_unconverged`·`tf_failed`·`a_dc_below_resolution`), `sim.offset_sys.reason`(`sweep_direction_undeclared`·`input_dc_undeclared`·`a_dc_undefined`·`sim_convergence_failed`), 실행 전 거부는 §7.2 기존 단계 | 검증자 | `a_dc_undefined`는 `/a_dc`를 가리킴(원인 문자열 사본 없음); 갈래 발동 시 `.dc` 요청 0 | 이름은 DR-20 design 몫; `.dc` 미요청은 **원래 취지와 다름(경미) -- 사용자 확인 X-R3** |
| `dc_sweep.input_dc`(§11.6) | EO-1 생산자(spec 선언 참조 직렬화) | §21.4 V_id,0 하나(v0.3.6 -- `icm_margin_v`는 쓰지 않음, DV-18 닫힘) | `swing_icmr.input_dc_V`·`input_dc_pending` 삭제(같은 정의 두 칸 해소, 규칙 3); 공칭 점 갈래는 오라클이 푼 넷리스트 자신의 값이라 사본 아님 | 없음(계획 G-18 v0.6.12) |
| `confirmed_range` 정의 불능 끝 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 엔진 2단계 호출 자리(`stage2_judgment` 끝 항목의 투영) | 오라클 §7.2 2c 검사 (1), `range_final.source` | `reason` 사본 삭제; 오라클 기록에 `departed`·`reason` 값 칸 0(gain-budget N6.20 (6)) | 없음(계획 N3.9·G-19) |
| `range_final.source` 정의 불능 꼴 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 확정 실행(코어 `range_confirm`) | EO-1 2단계 배선, 검증자 결합 | 입력 지목의 참조(`record_id`) 그대로 -- 값 칸 아님(규칙 4) | DR-20이 design에 맡김 |
| `end_cause` | 오라클 1단계 하나 | 2단계·검사 (4) 면제·검증자 | 2단계 값 없음(엔진 판정 사본이 됨) | DR-20이 design에 맡김 |
| `input_sha256` 대 `range_input_fp` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 각각 진입점 하나 | 파일 대응 / 검사 (1) | 축이 다른 두 양(규칙 3 -- 축을 §11.7에 적음), 서로 유도 없음 | X-R2 승인(O-61) |
| `sim.offset_sys` 기록(§21.4 4단계) | sim 단계 코어 `measures_dc` 1~4단계 하나 | compare measure 행 `offset_sys_mv`(`sim_ref`로 읽음), PC-10, 검증자 | A 값·갈래 값 칸 없음(`sim.a_dc` 참조) | 자리는 DR-20 '기록 칸' 범위(X-R4와 함께 확인) |
| `sim_ref`·`summary.u6` 삭제(§11.7) | 진입점(compare 조립) 하나 | 보고서·검사 (1)·EO-1 | 옛 `summary.u6` 값 사본 제거, sha256 참조만(규칙 2·4) | **원래 취지와 다름(경미) -- 사용자 확인 X-R5** |
| `icm_margin_v`(§21.2, v0.3.6) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어 `swing_math`(포트별 식 하나, `range_final`도 같은 함수) | measure 행 | 정의 = gain-budget N6.6 1490행 하나(사영 정의 삭제 -- 두 정의 해소, 규칙 3); V_p·lo_p·hi_p = 점 기록 `v_in` 원값 참조 | 없음(계획 v0.6.14 DR-21) |
| ICMR 점 `v_in`(§11.7, v0.3.6) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 오라클 1단계 훑기(같은 `OpSweep` 해) | `icmr_coord`·`icm_margin_v`·r·검사 (4) | ICMR 점의 `m` 칸 삭제(m은 `v_in`에서 함수 하나로 -- 사본 없음) | 기록 꼴은 design(DR-21 '읽는 절차') |
| 차동 모드 DC 닫힘 벤치(§21.2 2단계 (c)) | 코어 `build_benches.sweep_bench` | ICMR 훑기((v0.3.8) 슬루 t = 0 소비자는 1b와 함께 AP-1로 -- OP 범위 소비자 = ICMR 하나) | 정의는 gain-budget N3.8 인용(오라클 사본 식 없음), 엔진 Schur 행 받지 않음 | 벤치 소자 꼴은 design(DR-21) |
| 전달 판정 분해능(§21.5 4단계 (4)) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** `measures_dc.transfer_resolvable` 하나 | `sim.a_dc`, §21.2 반전 입력 후보 | 문턱·δV_out·레일 폭 값 칸 없음(입력에서 다시 잼), `inverting_port_undetermined.detail.resolution` 삭제 | 없음(계획 '전달 판정 분해능') |
| 슬루 t = 0 바이어스 전용 초기 조건(§21.6 1b) | (v0.3.8) **OP 범위에 writer 없음** -- gain-budget card AP-1 몫(옛 writer 안 '코어 `slew_math`(닫힘 `.op` → `Tran.ic`)'은 계획 v0.6.15 DR-23 (1)·검증 필수 1로 기각: 닫힘 `.op`는 ICMR 공칭 점 기록 `v_in`의 둘째 생산자) | -- | AP-1에서 만들 때 시작점 = `v_in` 기록 참조(규칙 1·2·4) | 계획 DR-23 (1) |

### 19.6 설계 선택별 실현 가능성 점검(v0.3.6, 사용자 규칙 2026-10-21 -- 인용한 칸·함수·시뮬레이터 능력의 존재(파일:줄 또는 어댑터 능력 선언), 단위, 대표 회로 추론, 끝에서 끝 경로; 확인 안 된 것 = '미확인'과 멈춤)

| ID | 설계 선택(위임 근거) | 인용한 것과 존재 근거 | 단위 | 대표 회로 추론 | 끝에서 끝 경로 | 판정 |
|---|---|---|---|---|---|---|
| F-1 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 차동 모드 DC 닫힘 벤치 = `tb:icm`(VSource) + `Vcvs` 둘(이득 ±½, 제어 = 출력 짝)(§21.2 2단계 (c); DR-21 '벤치 소자 꼴은 design') | IR `Vcvs(name, p, n, cp, cn, gain)`(§4.1); ngspice 선형 E 원소를 지금 코드가 같은 꼴로 씀(`O/oracle_netlist.py:435` `Efb_`, `:641` `Ecl_` -- 출력 차를 제어로 쓰는 E; (v0.3.7 정정, 검증 필수 5) `:445` `Efb_`는 제어가 `{N(o)} 0`(단일 출력)이라 이 묶음에서 뺐다); `Vcvs`는 IR 기본 원소라 능력 칸 없음(모든 어댑터가 씀) | 이득 무차원(V/V), 원 V | current_reuse: Cf1 = (Vom, Vip) → Vip가 Vom의 반전 입력(T(Vip→Vom) < 0), Cf2 = (Vop, Vim) → Vim이 Vop의 반전 입력. 닫힘 Vip − Vim = Vom − Vop = 계획식 (Vip − Vim) = −(Vop − Vom). 짝 부호가 `.tf`에서 오므로 닫힘은 음되먹임 -- (v0.3.7, 검증 필수 4) 이를 가려내는 test는 §18.1 (d-1) 오프셋 손 회로(d_out 부호가 짝에 따라 반대)와 (d-2) 구조 단언 sign(T(in_a → o_a))·sign(닫힘 계수) < 0이다(DC `.op`의 수렴·창만으로는 부호를 가리지 못함). **판정 근거 = `.tf` 부호**(v0.3.7, 검증 nice-to-fix): 위 Cf 연결로 반전 짝을 읽은 것은 설명용이고, 오라클은 연결을 읽지 않고 포트별 `.tf` 부호(F-2)로만 짝을 정한다. 출력 CM은 회로 CMFB(current_reuse는 `pm_cm_ss_deg` 제약이 있는 CM 루프 회로) -- (v0.3.7 고침) CMFB 없는 회로면 출력 CM이 회로로 정해지지 않아 `.dc`가 수렴하지 않거나(`sweep_point_unconverged`) 레일로 간 해에 수렴한 뒤 공칭 점 영역 이탈 규칙(§21.2 '점 판정'·'metric 값' -- `intended_region_mismatch`, `sweep_end_unresolved`(`why = nominal_not_conducting`) -- 여기까지는 fail-closed(거부·정의 불능); 또는 공칭 점 포화 부족의 음수 margin -- 이것은 fail-closed가 아니라 **값으로 FAIL**(제약 판정에서 떨어짐; v0.3.7 둘째 커밋 구분, 검증 N8))에 걸린다 -- **어느 쪽이든 정상 창 값으로 통과하지 않는다**; 어느 쪽이 나오는지는 회로마다 다르고 단정하지 않는다 | spec `human.feedback.elements` → EO-1(빈 list `[]` → `unity_follower`, §11.6 `measure_feedback`) → 입력 `feedback_passives`(§11.1 839-840행 -- v0.3.7 정정(이 판 줄 번호; v0.3.6 판 838-839행), 옛 '833행'은 `/simulator/options`) → IR 원소 종류로 (a)/(c) 판정 → `sweep_bench` → `OpSweep`(`tb:icm` DC 덮어쓰기) → 점 기록 `v_in` → `icmr_coord`·`icm_margin_v` | 확인됨(코드 사용 근거 + §18.1 (d) test가 관문) |
| F-2 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 출력별 반전 입력 판정 = `tf_bench(port=p)`를 `NodeV(o)`마다(§21.2 2단계) | IR 요청 `Tf(id, cond, exc, out: Expr, src)`(§5 -- v0.3.7 정정, 옛 '§4.1'), 능력 `tf`(§8.3); ngspice `.tf` 실측(S-42, §19.3 '측정됨') | V/V | 2입력 × 2출력 = `.tf` 4회. 두 출력의 반전 입력이 같은 포트면 짝이 안 되어 `inverting_port_undetermined` | 공칭 free `.op` → `tf_bench(port)` → `TransferResult.gain` → `transfer_resolvable` → 짝 | 확인됨 |
| F-3 | 전달 판정 분해능 함수 하나 `transfer_resolvable`, \|V\| = 1단계 공칭 free 실행의 노드 전압(§21.5 4단계 (4); DR-21 '읽는 절차') | 식 = gain-budget v6.24 N3.8 576행(인용); vntol·reltol = `Resolution`(§8.3 `default_tolerances`, 입력 `simulator.options` -- 계획 N0 29행); 레일 = 입력 `/rails[].voltage`(§11.1 835행 -- v0.3.7 정정(이 판 줄 번호; v0.3.6 판에서는 834행), 옛 '829행'은 `/process/temp_c`); 공칭 free `.op` 노드 전압 = 이 측정의 1단계 실행(§21.5 1단계)이 이미 냄 | \|A\|·W_rail(V) 대 δV_out(V) -- 양쪽 전압 | 차동 A = 100, W_rail = 1.8 V, V(o) ≈ 0.9 V, reltol 1e-3·vntol 1e-6 사례에서 δV_out ≈ 1.8 mV ≪ 180 V → 값; A = 1e-4이면 0.18 mV < 1.8 mV → 갈래(사례 수치는 설명용, 상수 아님) | 입력 → `Resolution`·레일·공칭 `.op` → 함수 → `sim.a_dc.reason`/값 | 확인됨. 해석 하나: 계획 '공칭 `.op` 전압'을 공칭 free(servo) 해로 읽음(개루프 벤치 `.op` 아님) -- 독립 검증에서 확인 요청 |
| F-4 | (v0.3.8 -- AP-1 몫, OP-10 범위 밖; 계획 v0.6.15 DR-23 (1)) 슬루 t = 0 시작 동작점 경로(§21.6 1b). 옛 v0.3.6~v0.3.7 행 본문(닫힘 `.op` → `Tran.ic` 기법, 관문 = 지운 손 회로 test)은 history v0.3.8 둘째 커밋(H9) | -- | -- | -- | -- | 이 판 판정 없음(AP-1에서 다시 잼). `Tran.ic`·C10 쪽 판정 = F-10 |
| F-5 | (v0.3.8 -- '입력 망 원소의 다른 단자' 갈래는 AP-1 몫) OP-10 계단 자리 = 구성이 닿지 않은 입력 포트, 없으면 `input_network_step_deferred`(§21.6 1단계). 옛 행 본문(입력 망 원소 분류·`no_input_network`)은 history v0.3.8 둘째 커밋(H9) | `feedback_passives`(§11.1)·`dc_sweep.excite` 키(§11.6) | -- | F-11과 같음 | F-11 | F-11로 옮김 |
| F-6 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** ICMR 점 기록 `v_in`(원값), m은 `icmr_coord` 함수(§11.7; DR-21 'V_p·lo_p·hi_p = SPICE 포트 전압') | `OpSweep(id, cond, base_exc, points, outputs)`(§5 -- v0.3.7 정정, 옛 '§4.1')의 `outputs`에 `NodeV(입력 넷)`; 점 기록 스키마 §11.7 | V | DC 닫힘·follower에서 입력 포트 전압은 훑기 원 값과 다르므로(묶인 포트·Vcvs) 원값을 읽어야 포트별 식이 성립 | `OpSweep` → 점 `v_in` → `icm_margin_v`·`icmr_coord` → `range_final` | 확인됨 |
| F-7 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.7, 검증 필수 2) `icmr_v` = 포트 창 교집합 폭 min_p hi_p − max_p lo_p(§21.2 'metric 값') | 정의 = gain-budget v6.24 N6.6 IT-2 '범위' 2(1490행) "`icmr_v` = 포트 창 교집합의 폭(as-built 뜻 유지)"; 엔진 as-built `E/metrics/ls_swing.py:20`("[max lo, min hi] 폭(빈 창은 음수 폭 그대로)"); 입력 = 끝 점 기록 `v_in[p]`(F-6) | V(포트 전압) | follower: 묶지 않은 포트 하나 → 그 포트 폭; DC 닫힘(current_reuse 꼴): 두 포트 창이 닫힘 차 d_in만큼 어긋나 교집합 = 포트 폭 − \|d_in\|(d_in이 훑기 중 일정할 때) | `OpSweep` → 끝 점 `v_in` → `swing_math` 식 하나 → measure 행·`range_final` | 확인됨 |
| F-8 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.7, 검증 필수 3) DC 닫힘 c 대칭 조건, 비대칭 → `closure_common_asymmetric`(§21.2 2단계 (c), §7) | 계획 문언 = gain-budget N3.8 576행 닫힘 행 (i)(ii), oracle 계획 N3.9 ICMR 행 '여기 직교 성분(공통모드)'; 스키마 교차 규칙 Σ excite·common = 0(§11.6 `/dc_sweep`) | 무차원(계수) | current_reuse 꼴 대칭 여기 → 스키마가 대칭 c만 받음 → 갈래 미발동; 비대칭 여기 선언에서만 발동. library 값은 EO-1 생산자 전이라 **미확인** | 입력 `dc_sweep.common` → 벤치 생성 전 검사 → 거부 기록 | 확인됨(승인 = O-78 (3), 실패 규약 = gain-budget N3.14, 코드 이름은 design -- v0.3.7 둘째 커밋 인용 정정; 검사 = 시뮬레이터 호출 전 `excite` 두 포트 이름으로) |
| F-9 | (v0.3.7, 검증 필수 6) `human.feedback.elements: []` → `measure_feedback.kind = unity_follower`(§11.6) | `E/authoring/spec_elements.py:19-20`("빈 list = 되먹임 수동소자 없음 = β=1 루프", UD 9번) | -- | v0.3.7 재측정(`A/library/*.sizing_spec.json` 9개 + `A/heldout/*.sizing_spec.json` 4개 = 13개, `human.feedback.elements` 읽음): 비지 않은 것은 current_reuse(`["Cf1", "Cf2"]`) 하나, 나머지 12개는 `[]` → `unity_follower`(β = 1) -- §21.2 2단계 (e) 해당 0개(O-78 (2)와 같음) | spec → EO-1 생산자 → 입력 `measure_feedback` → §21.2 2단계 (b) | 확인됨(정의 근거), 회로 수는 검증 보고 인용 |
| F-10 | (v0.3.8, DR-23 (1); 둘째 커밋 M1 정정 -- 옛 'OP-3') `Tran.ic`·`tran_ic_bias_only`를 만드는 card·소비자 = OP-4 C10 하나(§4.2, §5, §8.3; 계획 DR-23 (1) '쓰는 회로 없는 경로를 남기지 않는다') | 귀속 근거 = 계획 OP-4 행(`docs/01-plan/features/oracle-portability.plan.md` 500행 "안정성: C10 규칙 코어화 … `_refine_text`·`stability_op_netlist` 삭제")·N4 OP-4 행(467행 "C10 판정 상태·창 수 등(계약 §1(b) '기존 과도 fixture 판정 불변')") -- 둘째 커밋 때 이 tree에서 grep으로 다시 읽음; C10 `.ic` 사용 = `O/oracle_netlist.py:596-598`(주석: uic 없이 바이어스 해에서만 묶고 t > 0에 품), `:625`(choke 노드 `.ic`), `:720`(kick 출력 노드 `.ic`), `:765`(`tran … 0 tmax`, `uic` 없음) -- v0.3.8 merge 뒤 `9554b60a` tree에서 다시 읽음; §20 OP-4 행이 §4.2 `stab_benches`·§5 `Tran.ic`·§8.3 `tran_ic_bias_only`를 범위로 가짐(둘째 커밋); `stab_benches`는 아직 구현 전(`git grep -n stab_benches -- '*.py'` 0건, v0.3.8 merge `9554b60a` tree에서 재측정) | 노드 전압 V | C10은 안정성 근거(PM)를 재는 모든 회로에서 돈다 -- 소비 회로 수 = C10 실행 회로 수(13회로 가운데 몇 개인지는 이 판에서 세지 않음 = **미확인**) | `stab_benches` → `Tran(ic=…)` → 능력 관문 → ngspice `.ic` 줄 + `uic` 없는 `tran` | 확인됨(코드 줄), 원문 쪽 = **미확인**(DV-20) |
| F-11 | (v0.3.8, DR-23 (1)) OP-10 슬루 측정 구성 거부 `input_network_step_deferred`·`start_op_deferred`(§7 `feedback_config_undeclared` (b)(c)) | 입력 `measure_feedback`·`feedback_passives`(§11.6)와 §21.2 2단계 (0) DC 되먹임 판정(v0.3.9 -- 옛 'IR 원소 종류(§4.1 `Capacitor`·`Resistor`·`Inductor`)'는 history v0.3.9), 입력 포트 = `dc_sweep.excite` 키(§11.6) -- 모두 이 문서 안 정의; 시뮬레이터 호출 없음 | -- | v0.3.8 재측정(13개 `human.feedback.elements`): current_reuse `["Cf1", "Cf2"]`(`A/library/current_reuse_telescopic_ota.sizing_spec.json:141-142`) → Cf1(Vom–Vip)·Cf2(Vop–Vim)가 두 입력 포트에 닿음 → (b) `input_network_step_deferred`(옛 `no_input_network`과 같은 '정의 불능', 사유 문자열만 다름); 나머지 12개 `[]` → `unity_follower` → (b)(c) 미발동. 그래서 (c) `start_op_deferred`가 첫 사유인 회로 0개; current_reuse는 (b) `input_network_step_deferred` 하나로 기록(O-89 (2) -- `detail.also` 삭제; 1b 대표 회로는 AP-1의 current_reuse 응용 회로) | 입력 → 코어 `slew_math` 구성 검사 → 거부 기록 | 확인됨 |
| F-12 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** (v0.3.8, DR-23 (2)) ICMR (e) = `icmr_feedback_dc_absent`, 단일 입력 (d) 먼저(§21.2 2단계) | 정의 = gain-budget v6.26 N3.8 'ICMR 측정 구성'(이 tree `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 584행 'O-79' 문장, 단일 입력 먼저 = 같은 문장 'O-80 R2'); 실패 규약 = 같은 계획 N3.14(844행); 엔진 대응 이름 `icm_config_feedback_no_dc` = design 41 v1.12.5 `88bc5f2f` 734·744행(**승인 대기**, 이 tree 밖 커밋을 `git grep`으로 읽음) | -- | 13개 가운데 단일 출력 + DC 되먹임 없는 선언 = 0개(F-11 재측정과 같음; v0.3.9 둘째 커밋 문언 -- 단일 출력 선언 회로 자체가 0개라 판정 방식과 무관) -- 해당 0개(O-78 (2)) | 입력 → 코어 `swing_math` 구성 검사(어떤 시뮬레이터 호출보다 먼저) → 거부 기록 | 확인됨 |

**v0.3.7 graph 단일 정본 점검**(프로젝트 CLAUDE.md '★graph 단일 정본' 1~7, 이 판 변경분):

| 대상 | writer(하나) | 소비자(읽기만) | 새 cache·memo·slot·값 칸·사본·둘째 생산자 | 판정 |
|---|---|---|---|---|
| `icmr_v`(§21.2) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어 `swing_math`의 포트 창 교집합 식 하나(`range_final`도 같은 함수) | measure 행, `range_final` | 없음. 옛 m 좌표 hi − lo 정의 삭제 -- 엔진 정의(gain-budget 1490행)와 같은 이름에 정의 하나(규칙 3). `v_in`은 기존 점 기록을 읽기만(규칙 4) | 준수 |
| m(`icmr_coord`) | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 함수 하나(값 칸 아님) | 끝 확정 r만 | metric 값에서 빠짐 -- 같은 양을 두 식으로 내지 않음 | 준수 |
| DC 닫힘 `tb:icm` DC = cm0 + y·c_s | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어 `build_benches.sweep_bench` | ICMR 훑기 | c_s는 입력 `dc_sweep.common`을 읽음(사본 칸 없음), cm0는 1단계 공칭 free 해를 읽음(기존). ½ 가중과 c 가중이 대칭 조건에서 같은 방향 -- 비대칭은 거부(규칙 3: 같은 정의의 양을 두 식으로 계산하지 않음) | 준수 |
| `closure_common_asymmetric` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어 검사 하나 | 거부 기록 | `detail` = 넷 이름만(계수 값 사본 없음) | 준수 |
| 닫힘 부호 test(§18.1 (d-1)·(d-2)) | test 작성자(정의 문장에서 기대값) | -- | 오라클 쪽 새 칸 없음, 구조 단언은 기존 `.tf` 기록·넷리스트 이득을 읽음 | 준수 |
| `[]` → `unity_follower`(§11.6) | EO-1 생산자(직렬화) | 오라클 §21.2 | 엔진 정의 인용만(새 정의 없음) | 준수 |
| C10 `.ic` = `Tran.ic`(§4.2) | 요청 칸 하나(슬루와 공유) | 어댑터 | 둘째 초기 조건 칸 없음, 능력 하나 | 준수 |
| (둘째 커밋) §11.7 점 기록·`range_final` 문장 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** -- | -- | `icmr_coord` 소비자에서 `icmr_v`·`icm_margin_v`를 빼고 ICMR 끝 값 = `v_in` 기록으로 맞춤 -- 문서 안 같은 이름 두 정의처럼 보이던 묵은 문장 해소(규칙 3·7) | 준수 |
| (둘째 커밋) lo_p·hi_p = 두 끝 기록 `v_in[p]`의 min·max | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** `swing_math` 식 하나(`icmr_v`·`icm_margin_v`·`range_final` 공유) | measure 행 | 새 칸 없음 -- 기존 끝 기록을 읽기만 | 준수 |
| (둘째 커밋) (d-2) A_d 부호 | test(기존 `.tf` 네 값의 선형 결합) | -- | 새 `.tf` 요청·오라클 칸 없음 | 준수 |
| (둘째 커밋) `closure_common_asymmetric` 검사 시점 | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어 검사 하나(입력 `dc_sweep` 읽음) | 거부 기록 | `detail` = 포트 이름만 | 준수 |

**v0.3.8 graph 단일 정본 점검**(프로젝트 CLAUDE.md '★graph 단일 정본' 1~7, 이 판 변경분):

| 대상 | writer(하나) | 소비자(읽기만) | 새 cache·memo·slot·값 칸·사본·둘째 생산자 | 판정 |
|---|---|---|---|---|
| 1b 닫힘 `.op` → `Tran.ic`(옛 §21.6 1b (i)) | **없음** -- OP 범위에서 지움(AP-1 몫) | -- | 옛 판의 둘째 `.op` 생산자(검증 필수 1)가 사라짐. AP-1에서 시작점 = §11.7 `v_in` 기록 참조로만(규칙 1·2·4) | 준수(위반 후보 제거) |
| `Tran.ic` 칸·`tran_ic_bias_only` 능력 | 요청 칸 하나(writer = `stab_benches` 하나)·어댑터 능력 선언 하나 -- 만드는 card = OP-4(둘째 커밋 M1 정정, 옛 'OP-3') | ngspice 어댑터(C10, OP-4) | 둘째 초기 조건 칸 없음; 만드는 card와 쓰는 card가 같아 card 사이에도 소비자 없는 칸이 생기지 않음 | 준수 |
| (둘째 커밋 → v0.3.10 넷째 커밋 삭제) `detail.also`(§7 `feedback_config_undeclared`) | 없음 -- 사용자 결정 O-89 (2): 소비자 0(test 행·대응표가 읽지 않음)이라 지움(만들면 배선) | -- | 칸 없음, `why` 하나 | 준수(소비자 없는 칸 제거) |
| (둘째 커밋) 사유 대응표(§19.2 알림) | 문서 표(코드 아님) | 검증자 원인 변화표 | 오라클 사유 어휘는 하나 그대로, 엔진 이름은 인용만(사유 문자열은 graph 필드 아님) | 준수 |
| `feedback_config_undeclared` `why` 값 둘 | 코어 `slew_math` 구성 검사 하나 | 거부 기록·검증자 | 새 코드 대신 기존 코드의 값(같은 뜻 하나 -- 규칙 3); `detail`에 원소 목록 사본 없음 | 준수 |
| `icmr_feedback_dc_absent` | **[낡음 표지 v0.4.0 -- 계획 0.6.25, 상위 O-115·O-178·O-202~O-215; 정본 = §21.1~§21.3·§21.6·§11.6·§11.7, 이 줄의 옛 문언은 기록]** 코어 `swing_math` 구성 검사 하나 | 거부 기록·검증자 원인 변화표 | 정의 = gain-budget N3.8 한 문장(인용, 오라클 사본 규칙 없음 -- 규칙 1·3); `detail` = 출력 넷 이름만; 엔진 사유와 두 이름이지만 생산자는 각자 자기 실행 하나(오라클은 엔진 값을 받지 않음, NFR-P3) | 준수 |
| 구성 판정 'DC 되먹임 없음'(v0.3.9 -- 경로 판정, 계획 v0.6.16 DR-24; 옛 행 이름 '구성 분류 DC 성분 없음(`Resistor`·`Inductor` 없음)'은 history v0.3.9) | §21.2 2단계 (0) `swing_math.dc_feedback_judgment` 하나(ICMR (a)(c)(e)·슬루 (c)가 같은 판정을 읽음) | ICMR·슬루 | 슬루 쪽에 둘째 판정 식 없음 | 준수 |

**v0.3.9 실현 가능성**(사용자 규칙 2026-10-21; 인용은 merge `44aa3932` tree에서 grep으로 다시 읽음):

| ID | 설계 선택(위임 근거) | 인용한 것과 존재 근거 | 단위 | 대표 회로 추론 | 끝에서 끝 경로 | 판정 |
|---|---|---|---|---|---|---|
| F-13 | DC 되먹임 판정 = 방향 의존 그래프 BFS(§21.2 2단계 (0); 계획 v0.6.16 N3.9 ICMR 행 'DC 되먹임 판정'·DR-24, 정의 = gain-budget v6.27 N3.8 587행 문단) | 입력 `/rails`(837행)·`/devices`(838행, drain·gate·source·bulk)·`/sources`(839행, `kind: "current" \| "voltage"`)·`/passives`(840행, kind = resistor·capacitor)·`/feedback_passives`(841행)·`/bias_voltages`(844행)·`/ports`(845행) -- 모두 이 문서 §11.1; 끝점 규칙 = `O/oracle_netlist.py:234-253` `loop_break_nets`(소자마다 입력 포트 단자 정확히 하나, 아니면 막힘 -- C14); 엔진 쪽 같은 규칙 `E/authoring/_feedback_cuts.py:11` `input_terminal_nets`(인용만, 오라클은 import 안 함) | -- | 13회로 재계측 = `wt/_drafts/evidence/2026-10-21/n7_path_rule_feasibility.md` §5(이 판에서 다시 돌리지 않음 -- 인용): 비지 않은 선언은 current_reuse(`["Cf1","Cf2"]`, 출력 Vom·Vop, 절단 넷 Vim·Vip) 하나, 방향 그래프 판정 4쌍 모두 '없음' → (c) DC 닫힘 그대로, 판정 변화 0; 나머지 12개 `[]` → (b), 판정 미호출. 두 출력 판정이 갈리는 회로 0개(DV-21 해당 0) | 입력 → C14 막힘 검사 → `dc_feedback_judgment` → 갈래 (a)/(c)/(e) 또는 거부 → (그 뒤에만) 시뮬레이터 | 확인됨(인용 줄), 13회로 수 = 증거 인용 |
| F-15 | (v0.3.10, DR-25 (1)) 차동 출력 결합: 두 판정이 같으면 그 판정, 갈리면 `why = differential_split` | 정의 = gain-budget v6.28 N3.8 589행 '차동 출력'(merge `810794a9` tree에서 grep); 입력 = (0) 판정의 출력별 결과(같은 BFS, 출력 넷마다 한 번) | -- | 13회로: 차동 출력 + 비지 않은 선언 = current_reuse 하나, 두 출력 모두 '없음'(n7 증거 §5 인용) → 같음 → (c), 갈리는 회로 0개; 손 판정 toy (x) 갈림·(xi) 같음(§18.1) | 입력 → C14 → 출력별 BFS → 결합 → 갈래 또는 거부 | 확인됨 |
| F-16 | (v0.3.10, DR-25 (2)) 지원 밖 원소 = `/sources` voltage → `why = element_unsupported` | 정의 = gain-budget v6.28 N3.8 589행 '지원 밖 원소'(엔진 = S1 `device.unsupported`, `E/graph/s1_structure.py:69·79` `put("device", "unsupported", …)` -- 이 판에서 grep으로 확인, 오라클은 import 안 함); 오라클 쪽 kind 경계 = `/sources` kind current·voltage(§11.1 839행), `/passives` 닫힌 열거(840행), `/devices` kind → `descriptor_kind_undeclared`(§7) | -- | 13회로 입력의 voltage 유무 = EO-1 전이라 **미확인** | 입력 → 판정 전 검사 → 거부 | 확인됨(경계), 회로 수 미확인 |
| F-14 | 지원 밖 원소(오라클 입력에서는 `/sources` voltage) → `dc_feedback_judgment_undefined`(§7; v0.3.10 why 이름 `element_unsupported` -- F-16) | 정의 문단 '지원 밖 원소'(gain-budget v6.28 N3.8 589행; v0.3.10 둘째 커밋 정렬, 검증 N1 -- 옛 v6.27 587행 '이상 전압원' 인용 대체); 엔진 `E/graph/CONTRACT.md:394` `source_kind_unsupported` | -- | 13회로 입력에 `/sources` voltage가 있는지 = EO-1 생산자 전이라 **미확인** | 입력 `/sources` → 판정 전 검사 → 거부 | 확인됨(정의), 회로 수 미확인 |

**v0.3.9 graph 단일 정본 점검**(프로젝트 CLAUDE.md '★graph 단일 정본' 1~7, 이 판 변경분):

| 대상 | writer(하나) | 소비자(읽기만) | 새 cache·memo·slot·값 칸·사본·둘째 생산자 | 판정 |
|---|---|---|---|---|
| DC 되먹임 판정 정의 | gain-budget v6.27 N3.8 문단 하나(정의 자리) | 이 문서 §21.2 (0)(인용) | 오라클 사본 규칙 없음 -- 구현만 따로(NFR-P3, 계획이 정함) | 준수(규칙 1·3) |
| 오라클 판정 결과 | 코어 `swing_math.dc_feedback_judgment` 하나 | ICMR (a)(c)(e), 슬루 §21.6 1단계 (c) | 새 기록 칸 없음(결과는 고른 갈래·거부 사유로만), cache 없음(입력당 BFS 한 번), 슬루 쪽 둘째 판정 없음 | 준수 |
| 끝점(절단 넷) | C14 규칙 하나(지금 `loop_break_nets`) | 판정·β 루프 끊기 | 둘째 절단 규칙 없음 | 준수 |
| `dc_feedback_judgment_undefined` | 같은 판정 함수 | 거부 기록 | `detail` = `why` + 원·넷 이름만(둘째 커밋 `bias_not_gate_only` 더함 -- 같은 함수의 판정 전 검사, 둘째 검사 자리 없음) | 준수 |
| 엔진 대 오라클 판정 비교 | 검증자 변화표(기존) | -- | 오라클이 엔진 `config`를 받지 않음; 비교는 벤치 넷리스트 갈래로 | 준수 |
| (v0.3.10) 차동 결합·`differential_split` | 같은 판정 함수 하나(출력별 BFS 결과를 그 자리에서 결합) | 갈래 선택·거부 기록 | 출력별 판정을 담는 새 칸 없음(`detail`은 넷 이름만), 결합 규칙 정의 = gb N3.8 인용(오라클 사본 규칙 없음) | 준수 |
| (v0.3.10) `element_unsupported` | 같은 판정 함수의 판정 전 검사 하나 | 거부 기록 | kind 목록 둘째 검사 없음(`/sources` voltage 한 갈래만 -- 나머지 kind는 기존 스키마·기술자 검사 몫) | 준수 |


### 19.7 v0.4.0 변경분 점검(graph 단일 정본·실현 가능성)

| 항목 | writer | 저장 | 소비자 | 판정 |
|---|---|---|---|---|
| `region_point`·점 기록 | 코어 `conduction` | `conduction.points[]` | 범위 끝·합격 판정·검증자 | 같은 정의 필드 하나 |
| V_cm | 함수 `icmr_coord(v_in)` | 없음(`v_in`만) | `range_metrics`, r | 사본 0 |
| servo 부호 | `sim.a_dc` READS | -- | 벤치 | 둘째 `.tf` 0 |
| `follower_input_range_v` | sweep 함수 하나(슬루 구성) | `sim.slew` | 계단·유효성 | ICMR 창과 정의 다름(축 = 측정 구성) |
| `ref_minus_servo_ref_V`, `knee`, `full_swing_step` | 그 측정 | sim 결과 | **출력 전용 선언** | 판정에 안 씀 |
| `/kcl_zero_current_devices` | 엔진 필드 직렬화(EO-1) | 입력 | 대조만 | 값 사본 아님 -- 참조 직렬화, 판정은 독립 유도값 |
| 새 cache·memo·슬롯 | 없음 | -- | -- | 0 |
| 상수 | `servo_gain`·`sweep_points_per_round` = 어댑터 선언, 출처 칸 | -- | -- | 코어 리터럴 0 |

| # | 설계 선택 | 상태 |
|---|---|---|
| F-20 | `servo_gain` 값과 수렴(`.dc` + 큰 K, library 회로) | **미측정** -- OP-5 착수 실측(O-225로 지금 안 잼). 안 되면 멈추고 보고 |
| F-21 | 어댑터 ID가 채널 `@m[id]`와 같은 값인지, 단자 전류 몫 분리 | **미측정** -- OP-5 어댑터 test |
| F-22 | 실행 cwd `.spiceinit`·홈 폴더 격리(사례 ngspice) | **측정됨**(v0.4.9, 계획 history 0.6.31 행): 실행 폴더 파일이 이김, 빈 파일도 막음 |
| F-23 | as-built `Vo,pred` 자리 `oracle_netlist.py:441-447` = `/predictions/nodes` 출처 | 상위 후속 정정 표 인용, 이 판 재측정 안 함 |
| F-24 | noise 꼬리: 첫 `f_top`이 평탄 구간이면 n̂ ≤ 1이라 `noise_tail_bound_undefined`(옛 코드는 10배씩 넓혀 닿음). 발동 수 | **미측정** -- OP-5 착수 실측, 많으면 계획 OP-B1 재질문 |

---

## 20. card별 범위 재확인(계획 N5.1 대 이 문서)

| card | 이 문서 절 | 선행(계획) | 추가 선행(이 문서) |
|---|---|---|---|
| OP-0 | (v0.4.0 행 신설) 이 문서 전체. 대응 = §20.1. 완료 측정 = design↔계획 gap 0(DR 표 전 행), 승인 기록 | 이 계획 승인 | 독립 검증(다른 agent) |
| OP-1 | §19.3 측정 전부, §18.1 T1-0 토큰 목록, §13.2 절차 준비, N4 입력 변환 스크립트(§11.5 대응표) | 계획 승인 | -- (v0.2.4: 측정 대부분 끝남, §19.3 상태 칸) |
| OP-1a (검증자, v0.2.5 추가) | 기준선 판정용 텍스트 + 원자료 sha256 목록을 `.ai/verification/<OP-1 id>/baseline/`에 커밋(계획 OP-1a). 이 문서가 적은 소비처: §18.1 '3 동일성'(N4-2 비교 칸 출력, N4-2a 변환 입력·결과), §10.6 '차이가 선언에서만' 절차(기준선 넷리스트), §7.1·§18.1 '오류 대응'(기준선 로그 발췌), §13.2(MC 출력·로그·입력, (v0.2.6) 기준선 표본별 V_os 재계산값·재구현 스크립트·실행 기록·선택 대조 기록) | OP-1 | gain-budget card LT-1의 착수 조건(계획). (v0.2.6) DV-5 = O-9로 닫힘 |
| OP-1b (검증자, v0.3.2 추가 -- 계획 v0.6.10 OP-1b 행, 사용자 결정 O-50 O1′) | 추가 기준선: 모델 기록(`model_files_sha256`) 있는 LUT v2 슬라이스를 쓰는 옛 형식 입력을 검증자가 쓰고, 옛 오라클(OP-1 기준선 커밋)을 격리 worktree에서 순차로 돌려 출력·넷리스트·로그를 기록(덮는 범주 = 계획 OP-1b 행). (v0.4.3, 계획 v0.6.27) LUT = 위치 선언의 결합 파일, §11.5 변환 결과는 기술자 없는 초안으로 보관하고 OP-3 판정자가 다시 낸다. 이 문서의 소비처: §20 OP-3 병합 조건 (b), §18.1 '3 동일성' | OP-1, OP-1a | -- |
| OP-2 | (v0.4.0 -- 계획 v0.6.18~0.6.25에서 OP-2 범위 변경 0, 아래 그대로) (v0.3.0 다시 씀, DR-10i -- 사용자 결정 O-14 (4) J-1 (나), 계획 X-28) **기술자·기술자 스키마·기술자 읽기 코드만**: §10.1, §10.2·§10.3 가운데 `mc`·`diagnostic` 칸을 **뺀** 기술자 전부(기하 단위·병렬 배수 선언 칸, `lut_record_root` 참조 포함, P G-5, sha256 칸 = LF 정규화 DR-6~DR-8), 코어 기술자 로더(스키마 검사, 참조 sha256 대조 -- 규칙 (i)(ii), 원본 중복 검사 -- 규칙 (iii), 위치 선언 해석, §18.1 '기록 뿌리 해석' 행). **입력 형식 전환은 하지 않는다**(§11은 OP-3): 옛 형식 입력과 옛 모듈 경로는 OP-2 병합 뒤에도 그대로 돌고, 기술자 로더는 아직 실행 경로에 배선되지 않는다 -- **OP-2·OP-3은 따로 검토하고 함께 병합**한다(만들면 배선을 병합 단위로 지킴). 기록 뿌리 교차 검사(`lut_record_root_mismatch`)도 OP-3(J-5 (가)) | OP-0, OP-1 | (충족, `b105b65`) 상위 문서 개정 card `gb-oracle-rev` 병합. **병합 조건**: ngspice 매뉴얼 원문 보관과 기본 허용오차 쪽 번호(R6) 채움(X-D4), (v0.2.5) abstol 값·쪽 포함(S-28) |
| OP-3 | (v0.4.8, A-80) **기간 동작**: 어댑터는 `tran`·`pz`·`noise`·`op_sweep`·`tf`·`mc_*`를 선언하지 않는다. `noise`·`swing_icmr` 입력 = `adapter_capability_missing`, `offset_mc` 입력 = `mc_method_unsupported`(`side = "descriptor"`). PM 값이 있으면 `pm_undefined = "stability_unverified"`, `pm_deg = null`, `pm_deg_raw` = 원값(CM 루프 포함). 옛 코드는 호출자 없이 남고 다리 코드 없음. (v0.4.0 더함) §11.2 1d `bias_gate_nets_mismatch`(OP-B3 -- `oracle_netlist` 예측값 대체 삭제), §10.6 끝 DUT 저항 소자 줄(SF-1 범위 9 통합 병합의 오라클 커밋 몫, 이 card 밖 -- v0.4.8 J-6), OP-3 판 합격 판정 `threshold_eps1`은 OP-5까지의 과도 코드이고 EO-1 판정은 OP-5 뒤다(A-8). §3, §4, §5, §6(`instance_geometry_reported`·요청 단위 오류·`bundle_files`·`machine_dependent_refs` 포함), §7(§7.1 op·ac 몫, §7.2), §8.1~8.3, §9, §10.6(소자 줄 작성·미선언 거부), **(v0.3.0) §11 전부 -- OP-3 입력 스키마 `spice_oracle_input/2`(§11.1~§11.3, EO-1 계약 §11.4), 옛 형식 거부, 옛 입력 읽기 전환, 기술자 로더의 `oracle_run` 배선, 실행 결과 계약(§11.7), `O/oracle_input.schema.json` 다시 씀**, §11.5 결과 칸 OP-3 행, §12.5(역할 구분, sha256 정의, 기록 뿌리 교차 검사 함수·test), §15.1 OP-3 행, §15.4 OP-3 행(cm_loop 스크립트, `u6_selfchecks.py` 삭제(O-10), conftest 입력 생성기 새 형식(v0.3.0 OP-2에서 옮김), `make_lut` 기록, 손 넷리스트 기준 `O/tests/adapters/ngspice/`로), §18.1 '8a 예외 둘째'(엔진 test glob 한 줄, 엔진 test 작성자)·'OP-3 입력 계약' 행, §18.2 캐시 test 앞 셋, smoke 고정 자료 '스키마 적합' test → '옛 형식이라 거부' test. **(v0.3.8 둘째 커밋, 검증 M1 -- OP-3/OP-4 경계)** 위 §4·§5·§8.1~8.3 가운데 **C10 과도 몫**(§4.2 `stab_benches` 행, §5 `Tran`의 `ic` 칸, §8.3 `tran_ic_bias_only`)은 OP-4 몫이다(계획 OP-4 행·N4 OP-4 행) -- OP-3은 그 칸·능력을 만들지 않는다(첫 커밋의 'C10 초기 조건 이전' 문장은 history v0.3.8 둘째 커밋) | OP-2(따로 검토, 함께 병합), (v0.3.2) OP-1b(병합 조건 (b)의 비교 상대) | **착수 조건**(v0.2.5): §19.2 DV-4 결정 -- (v0.2.6) 충족(O-9). (v0.3.0, 계획 OP-3 행) 옆 선언 근거 (a) 생성기 판 찾기가 폭 슬라이스 32개에서 가능한지 먼저 확인(§12.5, 계획 N9), 기존 슬라이스 meta 모양 실측(**충족** -- S-38: 폭 슬라이스 평탄, 결합 파일 중첩, §11.2 2b가 두 모양을 읽음). (v0.3.2) 병합 조건 (b)의 비교 상대 = **OP-1b 추가 기준선**(DV-7 닫힘, 사용자 결정 O-50 O1′ -- 기준선 입력 593개는 D-7 거부 `lut_model_provenance_missing`이 기대 결과, 코어 이관 동일성은 모델 기록 있는 LUT v2 슬라이스 입력으로; 선행에 OP-1b). **병합 조건**(P OP-3): (a) 기하 규칙 미선언 기술자의 실제 거부 test + 검사 순서·양성 대조 (b) 첫 조합 선언값의 공칭 op·ac 결과 N4-2 기준선 동일(검증자), 소자 줄 차이는 기록만·§10.6 절차로 선언 기인 한정 (c) (v0.2.5, 계획 v0.6.3) 기존 LUT 역할 옆 선언 + 그 선언으로 (i)~(iii) 통과 + 역할 지운 변형·보조 입력 sha256 바꾼 변형 실제 거부(§18.1 'OP-3 병합' 세 행). smoke 고정 자료 '넷리스트 재생성 일치' test 삭제 + `criteria_weakened`(§18.2) |
| OP-4 | (v0.4.0 더함) §18.3 끝 Nyquist 종료·상한, `nyquist_unresolved`, `NYQUIST_K_MAX` 삭제(OP-B1). **(v0.3.8 둘째 커밋, 계획 v0.6.15 DR-23 (1)·계획 OP-4 행 500행·N4 OP-4 행 467행, 검증 M1) C10 초기 조건의 이전 -- 만들고 같은 card에서 배선**: §4.2 `stab_benches` 행, §5 `Tran`의 `ic` 칸, §8.3 `tran_ic_bias_only`(ngspice 어댑터 선언 = 참)를 이 card가 만들고 C10이 쓴다(choke 노드·kick 출력 노드 `.ic`), §18.1 'OP-4 C10 `.ic`' 행; DV-20(원문 쪽)은 그 선언의 근거 칸(이 card를 막는 범위 = 근거 칸만). §8.4(G-13 확정), §8.5, §7.1 pz·과도 몫, §11.5 결과 칸 OP-4 행(실행 전 반환 경로 포함), §14 반복 상한 다섯, §15.1 OP-4 행, §15.4 OP-4 행(측정 도구 `calibration_tools/`로), §18.2 캐시 test 넷째, u6 pz 점검 재작성 | OP-3 | G-13 측정(S-19 있음) + (가) 시간 상한 사례 수(§19.3) |
| OP-5 | (v0.4.10, 상위 위임 A-94) 판정 묶음에 DUT 저항 RC 극점 실측 1회(§10.6 끝, §18.1). (v0.4.9, A-84 -- **이 행 안에서 앞섬**) C-9: `dc_feedback_judgment`·`dc_feedback_judgment_undefined`·`/measure_feedback`·`tf_bench(port=p)`는 이 card가 만들지 않고 OP-10이 만든다(소비자가 슬루뿐). C-3: 지목 왕복 삭제 확인 착수 조건 닫음. C-2: 오라클 커밋 → EO-1 범위 1~3 병합 대기 → 엔진 커밋 → 통합 병합. (v0.4.0 -- **이 행의 옛 문언보다 §20.1이 이김**) §21.1·§21.3 한 단계, §21.2 servo ICMR, §21.4 DR-28, §18.3 끝 상한 셋, §11.6 지우는 칸. 엔진 커밋 = 생산자 갱신 + `run_decl` 파일·호출자 경로 전달(실제 판정 호출 시작, 위임 A-23). **착수 조건 추가** = 지목 왕복 삭제 사용자 확인(O-214 미룬 결정 (1)), F-20·F-21 실측. (v0.3.9, 계획 v0.6.16 DR-24) §21.2 2단계 (0) DC 되먹임 판정(`swing_math.dc_feedback_judgment`, 슬루 OP-10도 같은 함수를 읽음 -- 만드는 card = OP-5), §7 `dc_feedback_judgment_undefined`, §18.1 'OP-5 (0)' 행 더함. (v0.3.10, 계획 v0.6.17 DR-25 (1)) DV-21 닫힘 -- v0.3.9 둘째 커밋의 착수 조건('DV-21 전에는 그 갈래 구현 안 함', 옛 문장 history v0.3.10)은 풀렸다: 갈리면 `dc_feedback_judgment_undefined`(`why = differential_split`)를 이 card가 만든다, §18.1 OP-5 (0) (x)(xi). (v0.3.8, DR-23 (2)) §21.2 2단계 (e) `icmr_feedback_dc_absent`(§7)·§18.1 'OP-5 (e)' 행 더함; §10.4·§10.5와 기술자 파일의 `mc`·`diagnostic` 칸(sky130 값, 사용자 확인), §12.7 손 모델 픽스처 정본(만듦), §13, §11.5 결과 칸 OP-5 행, §15.1 OP-5 행(v0.3.0: `.ac` 첫 점·`1e-3` 삭제, swing servo 목표 훑기·ICMR 출력 고정 삭제, ε = 1 전도 판정 삭제), §15.4 OP-5 행, §18.1 4a. **(v0.3.0, 계획 v0.6.9 N3.9·DR-17)**: §11.6 G-18 확장 칸(v0.3.2 정정: `intended_region`(HC-O가 먼저면 재사용), `dc_sweep`, `measure_feedback`, `sweep_rezoom`, `output_reference`, measure `offset_sys_mv`)과 입력 칸 `off_current_A` 둘 삭제, 결과 칸 `conduction.points[]`·범위 끝 기록·`PENDING_CONDUCTION`(§11.7), §21.1 판정 점 전도·포화, §21.2 swing·ICMR, §21.3 합격 판정 전도 기준, §21.4 계통 offset, §21.5 `.tf` A, §18.1 '10 정의 대조' OP-5 행. **같은 통합 병합에 엔진 커밋 셋(`Role: code`, 계획 N3.9 '배선' (i)~(iii), O-55 U2, U-6)**: (i) EO-1 생산자 갱신(확장 칸 생산, `off_current_A` 생산 부분 삭제) (ii) 2단계 호출 자리(공용 전도 판정 함수)와 끝 괄호 재요청(`sweep_rezoom`) (iii) graph-consumption `dc_off_current` 출력 전용 선언 | **gain-budget EO-1 병합**(생산자 갱신 대상, 계획 OP-5 선행). (v0.4.9, A-84 C-1) OP-4는 병합 선행 아님(코드 의존 0), LA-1 측정 전 필요 | (충족) OP-1 (i) 결과 = 소자별 독립(S-12). (충족, v0.2.5) DV-3 = 사용자 결정 O-8(§13.2). (충족, v0.2.6) DV-5 = O-9. OP-1a 병합(기준선 표본별 V_os 재계산값). (v0.3.2) **착수 조건**: DV-6·DV-8 닫힘(O-50 G5·G1·O-53 B3), gain-budget v6.20 정의 문장 병합(O-57, 계획 U-4 충족). 남은 막음: (v0.3.3) DV-11·DV-12·DV-13 닫힘(O-58 DV-11, O-59 (3)·(4), 계획 v0.6.11·gain-budget v6.21 DEC-23); 남은 막음 = (v0.3.4) DV-14·DV-15 닫힘(O-61 P7·P8, 계획 v0.6.12·v0.6.13); (v0.3.5) DV-17·DV-18 → (v0.3.6) **닫힘**(계획 v0.6.14 DR-21); 남은 막음 = DV-19(v0.3.6 당시) → (v0.3.8) **닫힘**(계획 v0.6.15 DR-23 (2), `icmr_feedback_dc_absent`; v0.3.9 둘째 커밋 정정 -- 검증 M1-c, 옛 '남은 막음 = DV-19(… 용량만 선언만)'은 이 행 앞머리 'DV-21'과 모순이라 고침). (v0.3.6 범위 더함) §21.2 차동 모드 DC 닫힘 벤치·출력별 반전 입력 `.tf`, `icm_margin_v` 포트별 식·ICMR 점 `v_in`, §21.5 전달 판정 분해능 함수·`rail_width_zero`, §7 `feedback_config_undeclared`(슬루만)·`inverting_port_undetermined` detail, §18.1 (b)(d). (v0.3.2 당시: DV-11(§21.5 단일 입력), DV-12(범위 최종 metric 재계산 주체), DV-13(계통 offset 기준점).) **(v0.3.3 범위 재작성, 검증 M4)** 이 card 범위에 더한다: §11.6 `confirmed_range`·`dc_sweep.input_dc`, §7 `range_pointer_rejected`·`input_dc_undeclared`·§7.2 2c, §11.7 `range_final`·`run_request`·`range_input_fp`·기록 파일 이름·같은 `<out_dir>` 호출자 의무, §3.1 `core/range_confirm.py`, §21.4 3단계 값 식, §21.5 단일 입력 A, §18.1 `core/test_range_confirm.py`. 같은 통합 병합의 엔진 커밋(U-6)에 EO-1 생산자의 `input_dc` 생산과 2단계 호출 자리의 `confirmed_range` 지목 생산·확정 실행 호출이 든다. **(v0.3.4·v0.3.5 범위 더함)** §21.5 `sim.a_dc` 기록(여기 방향 `.tf` 한 측정, 있는 조건)·사유 집합(`sweep_direction_undeclared`·`nominal_unconverged`·`tf_failed`·`a_dc_below_resolution`), §21.4 `sim.offset_sys`·사유 순서·갈래 발동 시 `.dc` 미요청, §7 `a_dc_undefined`·`range_pointer_rejected` 정의 불능 끝(검사 (1)만)·sim.json 대조, §11.1 `swing_icmr.input_dc_V`·`input_dc_pending` 삭제·§11.5 변환 행·결과 칸 `a_dc_signed` → `sim.a_dc.value` 행, §11.6 `confirmed_range` 정의 불능 꼴, §11.7 `range_final.source` 정의 불능 꼴·`end_cause` 1단계만·`sim_ref`, §21.2 V_icm, §18.1 '10 정의 대조 -- OP-5' (a)(b)(c). (OP-3 범위에는 `summary.u6` 삭제·`sim_ref`가 든다 -- X-R5 확인 뒤.) (옛 착수 조건 문장은 history H7) |
| OP-6 | §12(§12.7은 OP-5 산출물 재사용, 새로 만들지 않음) | OP-5 | (충족, T-40) offset-trim design TR-0T가 master에 병합됨. PC-10 기준의 대조 정본 = master `offset-trim.design.md` §20 |
| OP-7 | §16, §7.2 8b, §8.1 끝, §10.2 `bin_rule_decl`(v0.4.9), §8.3 끝 `compat_modes`, §18.1 v0.4.0 행. **두 조각**(계획 0.6.26, 위임 A-13): (i) 기존 LUT 옆 선언 기록 + 경계 앵커 재측정(작성 = 검증자) (ii) 어댑터 실행 설정·거부 | (i) OP-0 G-14 형식 뒤, OP-3 전, WB-1 앞 (ii) OP-3 | 옆 선언 조각의 측정 방법 = §16(v0.4.3, 아직 실행 안 함, 재측정이 안 되면 멈추고 보고). EO-1 판정 앞(거부 규칙의 귀결). WB-1이 reader. 옛 선행 'XRUN-F1 C'는 계획에 없음 |
| OP-8 | §15.3, §16 | OP-6, (v0.3.0, DR-12) gain-budget v6.17 엔진 sha256 정본 card SH-1(O-16 (1)) | -- |
| OP-10 (v0.3.0 신설 반영; v0.3.1 선행·착수 조건 닫힘 -- O-50 O3·O-51; 남았던 DV-10은 v0.3.3에서 닫힘 -- O-58 DV-10·O-59 (3)) | (v0.4.0, DR-27) 계단 전달 = §21.6 1a·2단계, 왕복 없음; 착수 조건의 §19.2 DV-10·ICMR 끝 출처는 대상 소멸. §21.6 슬루, §11.6 `slew` 칸, §5 `Tran` 계단 벤치, §8.3 능력 `tran_large_signal`, §15.1 C25 행, §18.1 '10 정의 대조' OP-10 행 | OP-4, OP-5, **EO-1**(v0.3.1, O-50 O3), gain-budget v6.20 N3.8 슬루 정의 문장(565행) | (v0.3.1) **착수 조건**(계획 OP-10 행): (i) gain-budget v6.20 N3.8 개정 병합(O-57로 병합됨) (ii) OP-5 ICMR 절차 병합(계단 끝 출처, O-51); 그리고 §19.2 DV-10(확정 끝 전달 경로) 결정. EO-1 생산자 갱신(`slew`·`measure_feedback` 칸) 커밋을 같은 통합 병합에(U-6). (v0.3.3 재작성, 검증 M4: DV-10 닫힘 -- O-58 DV-10·O-59 (3)) 슬루는 OP-5 확정 실행(`confirmed_range` → `range_final`)과 **같은 실행**에서 돈다 -- 선행에 OP-5 `range_confirm`(§3.1)이 든다; 계단 끝 = 같은 실행 `range_final.icmr`의 그 끝 `source` 지목(§21.6 2단계), 실행 순서 = ICMR → 엔진 쪽 2단계 → 확정 실행(계획 OP-10 '실행 순서'), 지목 생산·확정 실행 호출 = 이 card 통합 병합의 엔진 커밋(U-6) **(v0.3.8, 계획 v0.6.15 OP-10 행·DR-23 (1), 사용자 결정 O-78 (1) -- 범위 줄임; v0.3.6 DR-22 '범위 더함' 옛 문장은 history v0.3.8 둘째 커밋(H9))** v0.3.6에 더했던 1b 시작 동작점, 1단계 입력 망 계단 갈래, 시작 동작점 손 회로 test는 **이 card 범위가 아니다**(gain-budget card AP-1 몫, §19.2 알림); `Tran.ic`·`tran_ic_bias_only`는 OP-4 소유(C10; 둘째 커밋 M1 정정, 옛 'OP-3')라 이 card는 쓰지 않는다. 이 card에 남는 것: §21.6 1단계 구성 검사(`feedback_config_undeclared` `why` ∈ `differential_undeclared`·`input_network_step_deferred`·`start_op_deferred`), §18.1 OP-10 '측정 구성 거부' (i)~(iv). DV-20은 이 card를 막지 않는다(C10 몫). |
| OP-11 (v0.3.0 신설 반영) | §21.7 전력, §11.6 measure `power_dc_w`·`power_dc_w_rel`, §18.1 '10 정의 대조' OP-11 행 | OP-3 | -- (measure 이름 추가는 선택 칸이라 EO-1 생산자를 깨지 않는다. 엔진이 `power_dc_w` 예측을 내고 대조를 잇는 일은 gain-budget PW-1a 몫, 계획 U-5) |
| OP-9 | §18 전부 | OP-6, OP-7, OP-8, OP-10, OP-11 | -- |

* (v0.3.0) **gain-budget EO-1과의 관계**(계획 N5.2·U-6): EO-1은 OP-3 병합 뒤 착수하고 그 계약은 §11.1~§11.4·§11.7이다. G-18 확장 칸을 더하는 card(OP-5, headroom-chain HC-O, OP-10)는 EO-1 병합 뒤에만 병합할 수 있고, 각자의 통합 병합에 EO-1 생산자 갱신 커밋을 넣는다(OP-6은 OP-5 뒤라 `output_reference`를 OP-5가 이미 더했다).

* (v0.2.4, 검증자 정리) v0.2.3에서는 OP-2가 '§10'(전체), OP-5가 '§10.4·§10.5'를 함께 가져 §10.4가 겹쳤다. 위 표는 칸 단위로 나눴다: 기술자 파일 하나를 OP-2가 만들고(`mc`·`diagnostic` 칸 없음), OP-5가 같은 파일에 그 두 칸을 더한다. 계획 N5.1(OP-2 = 기술자·기하 규칙, OP-5 = 네이티브 MC·진단)과 같다.

### 20.1 card별 범위 대응표(v0.4.2, 계획 N5.1 v0.6.26 대 이 문서)

| card | 계획 범위 항목 | 이 문서 |
|---|---|---|
| OP-0 | G-1~G-14·N4-2a·test 이전 | §4~§10, §11.5, §12, §14, §16, §18 (옛 판 그대로) |
| OP-0 | DR-26 ICMR servo | §21.2 2~4단계·metric 값, §7, §19.7 표지 |
| OP-0 | DR-27 슬루 계단 전달 | §21.6 0·1a·2·4단계, §11.6 `/slew` |
| OP-0 | DR-28 기준 도달 불가 | §21.4 4단계, §7 |
| OP-0 | OP-B13 N3.5.1 재대조 | §12.8 끝 |
| OP-0 | OP-B1 '식 확정은 design', 꼬리 상계 질문 | §18.3 끝, §21.2 끝 풀이, §7 |
| OP-0 | `plan_version`, 독립 검증, 승인 | 머리(0.6.26), 검증·승인 대기 |
| OP-2 | 기술자·스키마·로더만, sha256 LF 규칙, 거부 test, 값 = spec card | §10.1~§10.3, §18.1 (옛 판 그대로, v0.6.18~0.6.25 변경 0) |
| OP-3 | 입력 형식 전환, 재생성 test 삭제, 기록 뿌리 교차 검사 | §11.0~§11.4, §12.5, §15 (옛 판 그대로) |
| OP-3 | OP-B3 게이트 전용 넷 교차 규칙 | §11.2 1d, §21.6 0단계, §18.1 v0.4.0 행 |
| OP-3 | DUT 저항 = 이상 R + C_par/2 | §10.6 끝, §11.6, §18.1 v0.4.0 행(v0.4.8: 상위 SF-1 범위 9 통합 병합의 오라클 커밋) |
| OP-3 | 착수 조건(옆 선언 근거·meta 모양) | §12.5, §19.3 (v0.4.8 측정됨) |
| OP-3 | (v0.6.30, A-80) 기간 동작, 변화표 사유 열, test 이전 축소 | §20 OP-3 행, §11.1·§11.4·§11.5, §15.1, §18.2 |
| OP-7 | 선언 키 + 호환 모드, 옆 선언 재측정, writer·reader, 오라클 배선·거부, 13회로 비트 동일 | §16, §7.2 8b, §7, §8.3 끝, §18.1 v0.4.0 행 |
| OP-7 | 엔진 파일 안 고침(WB-1) | §16 '엔진 읽기' |
| OP-7 | (v0.6.27, v0.6.29 출처 방법 교체) 저장 자리, W 경계, LUT 생성 모드 출처, 묶음 값 | §16 |
| OP-1b | (v0.6.27) 결합 파일, 변환 초안, sample 입력 처리 | §11.5, §20 OP-1b 행 |
| OP-4·OP-5·OP-10·OP-11 | (이 card 밖, 계획 전체 반영) 판정 한 단계, 칸 삭제, 온도 점, OP-B1·B5, OP-B4, DUT 전류 | §21.1·§21.3·§21.4·§21.6·§21.7, §11.6, §11.7, §18.3 |
| OP-7·OP-5 | (v0.6.31, A-84) 어댑터 조각 결정, OP-5 선행·꼬리 폭·값 출처·칸 소유 | §5, §7, §8.1, §8.3, §10.2~§10.4, §11.6, §11.7, §16, §18.1~§18.3, §20, §21.2·§21.3·§21.5 |

---

## 21. metric 측정 절차(계획 N3.9, G-18·G-19 -- OP-5·OP-10·OP-11, v0.3.0 신설, DR-17)

### 21.0 원칙

* **정의를 정하지 않는다**: 정의 정본은 gain-budget 계획 N3.8(metric)·DEC-23·DEC-78·DEC-90 (1)이다(계획 N3.9 '정의의 소유자'). 아래 절마다 정의 문장을 인용하고, 이 문서는 그 문장을 재는 **절차**(벤치 IR, 해석 요청, 읽는 법, 판정)만 정한다. 절차가 정의 문장과 어긋나 보이면 정의가 이기고, 이 문서를 고치기 전에 멈추고 보고한다.
* **같음의 증거**: test 작성자가 정의 문장에서 기대값을 쓴 손 회로 test와 검증자 정의 대조표(완료 조건 10, §18.1 '10 정의 대조' 행). 오라클은 엔진을 import하지 않는다(P NFR-P3).
* **변경 종류**(계획 N4 0번 표 그대로): OP-5 -- noise 칸·MC 수학((가-1)) = 정의 그대로(동일성) / 네이티브 MC 표본열, `icmr_v`·`icm_margin_v`·`swing_out_v`, 새 칸(`offset_sys_mv`, 단일 입력 swing·ICMR), A 출처와 σ, 합격 판정 전도 기준 = 정의를 바꾼 칸(동작 변경 기준). OP-10 -- 슬루 = 새 측정. OP-11 -- `rail_current_A` = 정의 그대로, `supply_current_A` = 정의를 바꾼 칸, `power_dc_w` = 새 칸. 모든 card에서 결정성(두 번 실행 비트 동일).
* **엔진·오라클 차**: 판정 실패가 아니라 대조 기록이다(상위 DEC-72, O-178 -- oracle 판정 기록 안의 칸, 판정 기준 아님; 옛 e_m·`derived.model_error_*`는 삭제). 합격 판정은 오라클 값으로 한다(계획 N3.9).

### 21.1 판정 점의 전도·포화(OP-5, `core/conduction.py`)

**정의 인용**(v0.4.0 다시 씀 -- 계획 v0.6.25 N3.9 '범위 조건'·'판정 위치 -- 오라클 한 단계'; 정의 정본 = gain-budget N3.6 '전도·포화 경계·`off` 선언 정본' (1)(2)(5)(6)·표 9행, N3.8 소자 조건; 사용자 결정 O-54·O-202·O-204·O-205 (1)(2)·O-210 RR-2·O-182 Q-S9 (A′)): 전도 = 선언 방향 BSIM 채널 op ID(`@m[id]` -- 단자 전류 아님) > 0, 꺼짐 = ID ≤ 0, 포화 = VDS ≥ `@m[vdsat]`(여유 0), `triode` = 전도 ∧ VDS < VDSAT, `off` 선언 소자 = 판정 대상 밖. 전류 문턱·LUT 조회·tol 칸은 없다. 옛 두 단계 판정과 그 인용은 history v0.4.0.

**절차**(판정 점 = 합격 판정의 free `.op` 해, 범위 판정의 모든 훑기 점 -- 끝 괄호 좁히기 점 포함. 판정은 오라클이 혼자 끝낸다: 엔진 import 0, LUT 양 0, 엔진 쪽 판정 함수 커밋 0):
1. **값 읽기**: 어댑터 `OpTable`에서 소자마다 VDS, VSB, 채널 ID(선언 단자 방향 부호 `signed_id`), VDSAT, gm/ID를 읽어 결과에 낸다(§11.7 `conduction.points[]`). 판정 입력은 ID·VDS·VDSAT 셋이다. 셋 가운데 하나라도 `None`이면 그 소자는 그 점에서 `conduction_undefined`(값 없음을 통과로 세지 않는다). VSB·gm/ID는 기록 칸이다(소비자 = 검증자 원인 변화표·DEC-72 대조 기록). **어댑터 조건**: `OpTable.id`는 채널 op 값이어야 한다 -- 기술자 op 파라미터 이름(§10.2)이 채널 전류를 가리키는지는 PC 벤치가 아니라 OP-5 어댑터 test가 손 모델로 단언한다(미측정 -- §19.7 F-21).
2. **KCL 항등 0 전류 MOS 제외**(정의 = gain-budget N3.6 표 9행 'KCL 항등 0 전류 MOS 예외', 인용): 코어 `conduction.kcl_zero_current_devices(ir)`가 회로 IR 연결에서 집합을 독립 유도한다(엔진 값을 쓰지 않음). **유도 규칙**(v0.4.1 M8, 위임 A-22): 입력 회로 원소(`tb:` 테스트벤치 원소 제외, `measurement_load` 저항은 DC 전류 경로이므로 엣지에 넣음 -- v0.4.2 R1)로 그래프를 만든다. 마디 = 넷, `/rails`·`/bias_voltages`·입력 포트 넷은 고정 마디 하나로 합친다. 엣지 = MOS drain–source, 저항, 이상원. 용량·gate·bulk는 엣지가 아니고, `off` 선언 소자는 엣지에서 뺀다(엔진 0 모형 전류 기저와 같은 뜻 -- **작성자 판단**). **어떤 MOS의 엣지가 다리(bridge)이면 KCL 항등 0**이다(그 엣지 하나만 지나는 절단이라 KCL로 전류가 0). 재측정 = library 13 topology에서 erfc_ota {M19, M20, M21}, 나머지 12회로 빈 집합(`wt/_drafts/evidence/2026-11-03/oracle_m8_bridge.py`·`.jsonl`, 계획 Q-S9와 일치; topology에 측정 부하 원소가 없어 이 측정은 측정 부하 조건을 가르지 못한다 -- 그 조건의 근거는 물리와 §18.1 toy). 같은 실행에서 입력 `/kcl_zero_current_devices`(§11.6, EO-1 생산자가 엔진 `graph.dc_current_basis` 빈 항 행을 직렬화)와 집합 비교해 다르면 **시뮬레이터 호출 전에** `kcl_zero_set_mismatch`로 거부한다. 제외된 소자는 값만 기록하고 판정하지 않는다. **작성자 판단**: 칸 이름·검사 자리(계획은 '대조, 다르면 거부'만 정함).
3. **`off` 선언 소자**: 값만 기록하고 판정하지 않는다(`region_point = "not_judged"`). 꺼짐의 기능 판정은 그 소자의 `judged_by` metric이 맡는다(O-202 O-h, 칸 소유 = 상위 card SF-1 로더·EO-1, O-221).
4. **점 판정**(나머지 소자): `ID ≤ 0` → `region_point = "off"`; `ID > 0 ∧ VDS ≥ VDSAT` → `"sat"`; `ID > 0 ∧ VDS < VDSAT` → `"triode"`. 정확 부등식이고 허용 폭이 없다. `|VDS − VDSAT| < tol_VDsat` 띠의 '구별 불가' 기록은 엔진 대조 기록 쪽 몫이다(tol_VDsat는 엔진 LUT 셀 -- 오라클은 그 값을 모른다, O-204).
5. **선언 영역 대조**(`intended_region`, §11.6): 선언 없음 = `"sat"`이어야 함, `triode` = `"triode"`이어야 함. 판정 종류 인자로 갈린다 -- `accept`·범위 공칭 점: 선언 없는 소자 어긋남 = 설계 실패(합격 판정 FAIL, 범위 공칭 점은 포화 부족량 음수 값 또는 꺼짐이면 정의 불능), `triode` 선언 소자 어긋남 = `intended_region_mismatch`(선언 오류, 판정 불능 집계 -- O-55 U1). `sweep`: 어느 소자든 어긋나면 그 점이 범위 끝(O-54, 측정 거부 아님).
6. **온도 점**(계획 N3.9 '온도 점 판정', O-53 B2 + 상위 O-205): 온도 조건을 단 요청의 판정 점도 1~5단계 하나다 -- 그 온도 SPICE op 값의 부호·포화 비교. 소자 개별 VGS = 0 풀이 벤치(옛 `ioff_bench`)는 만들지 않는다. OP-6·offset-trim card는 이 절차를 부른다(구현하지 않음).

**깨진 변형**(완료 조건 10, 먼저 실패를 보임): 단자 전류로 부호 판정(gmin·접합·GIDL 몫이 섞임), `|ID|`로 역방향 전도를 전도로 셈, 전류 문턱을 둠(옛 `off_current_A`·ε 식), 여유를 포화 정의에 넣음, 값 `None`을 통과로 셈, `off` 선언 소자를 판정함, KCL 항등 0 전류 MOS를 판정함, 집합이 다른 입력을 받음, 동작점의 `triode` 선언 불일치를 FAIL로 셈(판정 불능이어야 함), 훑기 중 선언 영역 이탈을 측정 거부로 셈(범위 끝이어야 함), 오라클 코드에서 엔진 import 또는 LUT 보간.

### 21.2 swing·ICMR(OP-5, `core/swing_math.py`, 요청 `OpSweep`)

**정의 인용**(v0.4.0 다시 씀 -- 계획 v0.6.25 N3.9 표 `swing_out_v`·`icmr_v`·`icm_margin_v` 행, DR-26; 정본 = gain-budget N3.8 '입력 범위 세 양' (1)·'ICMR 측정 구성 -- 정의 하나'·'ICMR 전달 뷰 = 기본 포트 뷰'·'ICMR 좌표 -- 정의 자리 하나'·'ICMR 판정 = 영역 행 창'·'ICMR 기능 기준', U-103·U-105·U-106, 사용자 결정 O-115·O-116·O-118 3번·6번·O-215(**임시 결정 -- 번복 가능**)): 스윙 = 입력 공통모드(일반형: 여기 직교 성분)를 동작점에 고정하고 여기 방향 입력을 DC로 훑을 때 출력이 움직이는 범위 중 모든 MOS가 선언 영역에 머무는 구간. ICMR = servo 측정 구성에서 입력 포트를 모두 같은 x로 함께 훑고(봉인점 입력 차 유지) 기본 포트 뷰 감지를 봉인점 동작점에 묶은 상태에서 모든 MOS가 선언 영역에 머무는 입력 범위. 끝이 정해지지 않으면 그 끝을 읽는 metric은 정의 불능이고, 수렴하지 않은 점에서 창을 자르지 않는다. 옛 인용(follower·선언 되먹임·'출력 고정 안 함')은 O-115로 대체, 원문 history v0.4.0.

**벤치 IR**(`core/build_benches.sweep_bench`):
1. 먼저 공칭 free 벤치(servo 있음, OP-3 본 벤치)를 풀어 입력 넷 n마다 동작점 v0(n)(servo 해)을 얻는다. 이 실행이 막히거나 수렴하지 않으면 측정 전체가 정의 불능이다.
2. (v0.4.0 다시 씀, **DR-26** -- 계획 N3.9 ICMR 행 '측정 구성') **ICMR 벤치 = servo**(`core/build_benches.icmr_servo_bench`, 정의 인용, 오라클이 자기 넷리스트에 만든다 -- 엔진의 끝 계산을 받지 않음, NFR-P3):
   * **입력 포트 하나인 회로 = servo 없음**(M1, gain-budget N3.8 '단일 입력 회로는 회로 그대로다 -- 보정할 입력 자유도가 없음'): `tb:icm:<n>` = v0(n) + x만 걸고 `tb:servo`를 넣지 않으며 출력은 회로가 정한다(e와 x의 방향이 같아 servo를 걸면 x를 지운다 -- 폭 0). s0·`sim.a_dc`·K·점별 고정 확인(`icmr_sense_target_undeclared`·`icmr_servo_sign_undefined`·`icmr_output_lock_violated`)은 이 갈래에 없다. 아래 '감지'·'servo' 세 항목은 입력 포트 둘일 때만이다.
   * **훑는 포트**: 입력 포트 전부(`/ports` role `input_p`·`input_n` 쌍 또는 `input` 하나 -- role 선언으로 정하고 이름으로 추측하지 않음, 입력 DC 선언 여부와 무관, 상위 O-118 3번). 포트마다 이상 전압원 `tb:icm:<n>` = v0(n) + x. **c(`dc_sweep.common`)를 쓰지 않는다** -- 모든 포트가 같은 x다. 입력 포트 셋 이상 = `icmr_input_ports_unsupported`(정의 불능, 시뮬레이터 호출 0).
   * **감지 s와 목표 s0**: 기본 포트 뷰 -- 단일 출력 s = V(out), 차동 출력 s = V(output_p) − V(output_n)(DM을 묶고 CM은 회로의 CMFB가 정함). s0 = 입력 `/predictions/nodes`의 출력 넷 봉인점 예측값(차동이면 두 값의 차). 없으면 `icmr_sense_target_undeclared`(정의 불능, 시뮬레이터 호출 0). 입력 차 유지: x = 0 점의 포트 전압 = 1단계 공칭 free 해 v0(n).
   * **servo 보정**: 미지 보정 ε 하나의 방향 = 여기 방향 e(`dc_sweep.excite`, U-105). 포트마다 `tb:icm:<n>`과 포트 사이에 `Vcvs` `tb:servo:<n>`(제어 = s − s0, 이득 = −sgn(A)·K·e(n)). 입력을 하나만 움직이지 않으므로 V_cm 정의와 섞이는 몫은 아래 좌표가 포트 전압 평균으로 그대로 잰다.
   * **servo 부호**: sgn(A) = §21.5 `sim.a_dc`의 여기 방향 `.tf` 전달 부호(그 한 측정을 읽음 -- 둘째 `.tf` 없음, 포트 role 이름 근거 금지). `sim.a_dc.status = "undefined"`이면 `icmr_servo_sign_undefined`(정의 불능, `detail = {a_dc_ref: "/a_dc"}` -- 사유 사본 없음).
   * **servo 이득 K와 출력 고정 정확도**(U-103 -- '정확 고정 + 오차 조건'): K = 어댑터 보정값 `servo_gain`(§8.3, 출처 칸 필수, 없으면 `adapter_calibration_missing` -- 코어 리터럴 없음). 정확도의 판정은 K가 아니라 **점별 사후 확인**이다: 훑기 점마다 |s − s0| ≤ 오라클 δV_out(§18.3, vntol + reltol·|V|, 차동이면 δ_p + δ_n)이어야 하고, 어긴 점이 있으면 `icmr_output_lock_violated`로 **그 metric 전체가 정의 불능**이다(창을 그 점에서 자르지 않음 -- 상수 0). **작성자 판단**: K를 어댑터 보정값으로 둔 것(계획은 '벤치 꼴 = design'만 정함). `.dc`에는 동적 안정 문제가 없으나 K가 크면 수렴이 나빠질 수 있다 -- 값은 OP-5 착수 실측(미측정, §19.7 F-20).
   * **ICMR에서 쓰지 않는 것**(계획 N3.9 ICMR 행): 선언 되먹임 구성, β = 1 follower, 차동 모드 DC 닫힘, DC 되먹임 판정, 반전 입력 포트 식별, '측정 구성이 묶은 포트' 구분. 옛 (a)~(e) 갈래와 `icmr_feedback_dc_absent`·`closure_common_asymmetric`은 ICMR에서 지운다(DV-19 소멸). 슬루 쪽 구성은 §21.6 0단계.
   * **swing 벤치**(v0.3.0 규칙 그대로) = 본 회로 IR + 레일 + 바이어스 + 입력 넷마다 이상 전압원 `tb:sweep:<n>`(DC = v0(n)). 입력 넷의 servo·choke·결합 C·AC 원·Middlebrook 원은 넣지 않는다 -- 출력을 고정하는 원소가 없다(계획 G-18). 본 회로의 β 되먹임망은 회로 원소라 그대로 둔다.
3. 점(`Excitation`의 DC 덮어쓰기): swing은 모든 입력 넷 n ∈ `excite`에 `tb:sweep:<n>` = v0(n) + x·excite(n). ICMR은 `tb:icm:<n>` = v0(n) + x(모든 입력 포트). x의 범위 = 입력 원 값이 모두 [레일 최저, 레일 최고] 안에 머무는 구간. 격자 간격 = V_T = kT/q(그 실행 온도, 옛 격자 간격 -- 소신호 선형화의 물리 척도, `thermal_voltage`), 공칭 0을 포함한다.
4. 측정 좌표: swing = 출력(단일 V(out), 차동 V(output_p) − V(output_n)). ICMR = **V_cm = 입력 포트 전압의 평균**(상위 U-106 'ICMR 좌표', 코어 `swing_math.icmr_coord(v_in)` 한 함수 -- 옛 c 가중 사영 대체). ICMR 점 기록은 원값 `v_in`을 싣고 좌표 사본을 두지 않는다(§11.7). 끝 확정 r도 V_cm으로 잰다.

**점 판정**: (v0.4.0 다시 씀 -- 계획 N3.9 '범위 판정') §21.1의 `sweep` 판정(모든 MOS가 선언 영역에 머무름, 여유 0)과 레일·수렴, 그리고 **판정 제약에 선택 상대 저하 항이 선언된 경우만** 기능 기준(아래). 공칭에서 바깥으로 첫 이탈 점까지 가고 그 끝 괄호를 좁히며 모든 점의 op 값을 `conduction.points[]`에 낸다. 공칭 점에서 `triode` 선언 불일치 = `intended_region_mismatch`, 선언 없는 소자가 공칭 점에서 꺼짐 = `sweep_end_unresolved`(`why = nominal_not_conducting`). **ICMR 기능 기준**(O-215(**임시 결정 -- 번복 가능**), 상위 N3.8 'ICMR 기능 기준'; 입력 칸 = `/icmr_relative_gain`(§11.6)): 선언이 있는 판정 제약만 훑기 점마다 `.tf`로 증분 DC 이득을 재 기준점 대비 선언 허용 저하를 판정하고, 기능 기준 끝과 영역 끝 가운데 공칭에 가까운 쪽이 창 끝이다. 미선언 = 영역 끝만(옛 '미선언 = 정의 불능' 삭제). 칸·판정 행·생산 card는 첫 선언 회로 때 같이 정한다(O-221) -- **그때까지 이 칸을 넣은 입력은 닫힌 키 집합으로 거부**되고 이 갈래는 코드를 만들지 않는다(만들면 배선). **레일 밖 노드 필터**(판정 단계 필터): 회로 노드 전압이 [레일 최저 − reltol·폭, 레일 최고 + reltol·폭] 밖인 점은 통과로 세지 않는다(옛 `sat_violation` 레일 규칙). 물리 근거(P-1): 레일 사이에서만 전원이 공급되는 회로에서 레일 밖 노드 전압은 이상원이 만든 해다. 허용 폭 reltol·폭은 그 실행의 해 정확도(새 상수 없음). 이 필터로 정해진 끝은 `end_cause = rail_filter`(§11.7). 그 점에서 판정 대상 소자가 `conduction_undefined`이면 측정 전체를 `conduction_undefined`로 거부한다.

**공칭 점 차 확인 -- swing만**(v0.3.0 검증 지적 6; O-58 B-45): swing 개루프 훑기 벤치의 x = 0 점 출력과 1단계 servo 해 출력의 차를 `nominal_output_shift_V`로 기록한다. 그 크기가 끝 확정 분해능 r을 넘으면 `sweep_end_unresolved`(`detail.why = nominal_shift`, fail-closed, 새 상수 없음). ICMR에는 이 칸이 없다 -- 입력 포트 둘인 ICMR의 x = 0 점 정확도는 위 U-103 점별 확인이 맡는다(입력 포트 하나인 회로는 출력을 묶지 않아 해당 없음)(옛 '구성이 servo 해와 다른 회로' 근거는 O-115로 소멸). (v0.4.9, A-84 C-10) 개루프 x = 0 출력 차 ≈ |A|·δv0이므로 v0(n)은 `nodes_full`로 읽는다. 기본 읽기 자릿수면 고이득 회로가 읽기 잡음만으로 이 거부에 걸린다. 거부 규칙은 그대로이고 v0 풀이 오차는 미측정이다(OP-5 판정 묶음에서 고이득 손 회로로 재고, 그래도 거부면 멈추고 보고).

**끝 풀이**: 공칭에서 바깥으로 첫 실패 점까지 가고, 괄호 [마지막 통과, 첫 실패]를 P+1 등분으로 최대 K_zoom회 좁힌다. **K_zoom = ⌈log_(P+1)(W0/r)⌉**(계획 OP-5 행 OP-B1, §18.3 '반복 상한 유도'): W0 = 첫 괄호 폭, r = 끝 확정 분해능, P = 어댑터 능력 선언 `sweep_points_per_round`(비용 선택이라 상수 아님, §8.3). 옛 `ZOOM_POINTS`·`ZOOM_ROUNDS`는 지운다. **끝 확정** = 괄호 양 끝 점의 측정 좌표 차 ≤ r, r = reltol·max(|m_a|, |m_b|) + vntol(§18.3, m = swing 출력 좌표 또는 ICMR V_cm). 끝 값 = 마지막 통과 점의 기록. 확정 전에 상한·시간 상한에 닿으면 `sweep_end_unresolved` -- 그 metric은 정의 불능이고 외삽 값을 내지 않는다. 범위 축 끝까지 모두 통과하면 그 끝은 레일 끝이다(`end_cause = rail`). 어느 점이든 수렴하지 않으면 `sweep_point_unconverged`로 측정 전체를 거부한다.

**metric 값**(v0.4.0 다시 씀 -- 계획 N3.9 ICMR 행 'ICM 세 metric 정의', 상위 U-106(O-116); 옛 포트 창 교집합·포트별 margin 식은 대체, 원문 history v0.4.0): `swing_out_v` = 단일 2·min(V_hi − V_o0, V_o0 − V_lo), 차동 2·min(D_hi, −D_lo), 기준 = 공칭 점(x = 0)의 측정 출력(설계 40 §3.8-8, DEC-96 (2) 정본). V_cm0 = 공칭 점의 SPICE 입력 포트 전압 평균(오라클이 푼 넷리스트 자신의 값, 선언 사본 아님), V_cm(lo)·V_cm(hi) = 확정 끝 점의 SPICE 입력 포트 전압 평균(두 값의 작은 쪽을 lo로 둔다 -- 기록 이름이 아니라 전압 크기). **`icmr_v` = V_cm(hi) − V_cm(lo)**, **`icm_margin_v` = min(V_cm0 − V_cm(lo), V_cm(hi) − V_cm0)**, **`required_input_cm_v` = (V_cm0, V_cm(lo), V_cm(hi))**. 값 식 정본은 이 한 곳(코어 `swing_math.range_metrics`). `dc_sweep.input_dc`는 이 metric에 쓰지 않는다. 공칭 점이 이미 포화 조건을 어기면 −(최대 포화 부족량)(옛 그대로), 꺼짐이면 위 정의 불능. **최종 범위 metric**: 범위 metric과 그 제약 판정은 오라클 기록 하나에서 확정한다 -- 옛 `provisional` → 엔진 지목 `confirmed_range` → 확정 실행 `range_final` 왕복과 `sweep_rezoom`은 지운다(O-205 (2)·O-210 RR-2의 귀결, **원래 취지와 다름 -- 작성자 도출, OP-5 착수 조건 = 사용자 확인(O-214 미룬 결정 (1))**).

**결과 칸**: 스키마 정본은 §11.7 '범위 끝 기록' 하나, 실행 수 `sim_runs`(옛 `ngspice_runs`, §11.5).

**판정**: 정의를 바꾼 칸(X-29·X-32, O-34 규칙, 상위 U-106). 기준선 값과의 차는 검증자 원인 변화표에 칸마다 적는다. 원인 변화표의 ICMR 원인 후보 = 출력 고정 정확도(이득 1 servo → U-103 조건), servo 부호 출처(role 이름 → `.tf`), V_cm 좌표, 범위 조건 전환(O-54·O-205).
**깨진 변형**(완료 조건 10): 출력을 묶지 않은 ICMR(옛 follower·선언 되먹임 구성), 포트 role 이름으로 정한 servo 부호, 고정 오차를 어긴 점에서 창을 자르는 경로, 포트별 margin 식, 차동 전제로 단일 입력을 `unavailable`로 내는 경로, 끝 풀이 실패를 외삽·마지막 통과 값으로 넘기는 경로, 수렴하지 않은 점을 '포화 아님'으로 세어 창을 자르는 경로.

### 21.3 합격 판정의 전도 기준(OP-5, `core/compare.py` + `core/conduction.py`)

(v0.4.0 다시 씀 -- 계획 N3.9 '합격 판정', 정본 = gain-budget N3.6 정본 (6), DEC-90 (1)·(3), T5. 옛 두 단계·`PENDING_CONDUCTION`은 history v0.4.0.)
* **대상**: 모든 MOS를 선언 영역 `intended_region` 하나로 가른다(§21.1 2·3·5단계 -- KCL 항등 0 전류 MOS·`off` 선언 소자는 판정 밖). 엔진 예측 칸 `predictions.devices.<n>.region`은 대상 선택에 쓰지 않는다. 판정 점 = free `.op` 해.
* **판정**: 선언 없는 MOS의 채널 ID ≤ 0 = 크기 무관 FAIL, ID > 0 ∧ VDS < VDSAT = FAIL(설계 실패), 제약 FAIL = FAIL. `triode` 선언 불일치 = `intended_region_mismatch` → `INCOMPLETE`(FAIL 아님, O-55 U1). 측정 불능 제약은 실행 전 `spice_unverifiable[]` 보고(T5, DEC-90 (3)). FAIL·판정 불능이 없으면 `PASS`. 오라클이 최종 판정을 낸다.
* **포화 확인 여유 칸 삭제**: `judge.sat_margin_V`·CLI `--sat-margin-v`는 OP-5에서 지운다(O-204, 넣으면 E5 거부). 문턱 칸 `off_current_A` 두 곳과 그 대상 선택(`O/oracle_compare.py:390-391`)도 같은 변경에서 지운다.
* **`region_spice` 표시**: §21.1 4단계 `region_point` 그대로(표시는 판정 입력이 아님). 값 없음 = `"undefined"`.
* **결과**: `summary.conduction_definition = "channel_sign"`(§11.7), 소자 행 표시 = `region_spice`, 점 기록 정본 = sim 결과(§11.7, v0.4.9 A-84 C-10). 옛 행 칸 `off_current_A_pred`·`conduction_threshold_A`는 지운다.
* **`off` 선언 소자가 있는 입력**: 기록만 한다. `judged_by` 칸·E-0 정지는 엔진 쪽(EO-1 범위 4, SF-1 로더 조각 -- O-221·O-222) 몫이고 오라클은 그 칸을 읽지 않는다.
* 판정 기준: 정의를 바꾼 칸(옛 X-33 '봉인 9 식으로 통일'은 대상 소멸). 원래 취지와 다름 = 승인 상위 O-205·O-210.

### 21.4 계통 offset `offset_sys_mv`(OP-5, `core/measures_dc.py`) -- (v0.3.1) DV-8 닫힘(사용자 결정 O-50 G1·O-53 B3); 현행 정본 = gain-budget v6.23 DEC-23(O-65 병합; 옛 착수 조건 v6.20 DEC-23 개정은 O-57로 병합됨, 계획 U-4)

**(v0.3.1) 정의 인용 갱신**: DEC-23 = gain-budget v6.20 `7fe555b1` 223행(계획 N3.9 계통 offset 행 인용). **값 = 부호 있는 V_id* 한 칸**(출력을 기준에 고정한 DC 해의 여기 방향 입력 이동량, 동작점 입력 기준 -- 차동이면 입력 차, 부호 그대로). 크기 칸을 따로 두지 않고 제약 판정은 \|V_id*\| ≤ spec으로 비교한다. **단일 입력 회로 = 여기 방향 일반형**(출력을 기준으로 되돌리는 여기 방향 입력 이동량, O-33 (7)) -- 정의 불능으로 두지 않는다. 기준 종류 = §11.6 `output_reference` 셋(값·넷·입력 추종) + 차동 기본, 선언 없는 단일 출력 = `reference_undeclared`. **PC-10 = 이 측정을 온도 조건에서 돌린 것 하나**(O-53 B3).
**정의 인용**: DEC-23 223행 "계통 offset `offset_sys_mv`는 출력을 기준값에 고정하고 입력 차를 미지수로 푼 DC 해의 입력 차다(정의) … 정확값은 oracle `.dc` … 기준값 = 엔진이 쓰는 선언 출력 목표(spec `node_voltage_targets_v` -- 쓰기 계획 W3 `REL_TARGET`), 차동 출력이면 V(p) − V(n) = 0, 단일 출력에 선언이 없으면 `reference_undeclared` 정의 불능(fail-closed)".

**절차**:
1. 벤치(`offset_bench`, v0.3.2 재작성 -- O-53 B3) = 공칭 free 벤치(servo 있음)에서 servo 목표를 **출력 기준**(§11.6 `output_reference`, DEC-23 기준 종류 셋 + 차동 기본)으로 바꾼 것: 값 `net_value` → V(out) = `value_V`; 넷 `net` → V(out) = V(`net`)(그 넷 전압을 servo 기준으로 -- 이상 VCVS, 기준 넷은 회로가 정함); 입력 추종 `rule_e_input_cm` → V(out) = 입력 CM = Σ_n c(n)·V_n / Σ_n c(n)²(c = `dc_sweep.common`, 단일 입력 `null`이면 c = excite -- §21.2 4단계와 같은 좌표); 차동 출력(칸 없음 또는 `differential`) → V(p) − V(n) = 0(공통모드는 회로 CMFB가 정함). 선언 없는 단일 출력 = `reference_undeclared`. 불일치는 끈다. PC-10 = 같은 벤치를 온도 조건에서(O-53 B3).
2. `Op` 한 점 → 입력 넷 전압 V_n → 입력 차 V_id* = Σ_n e(n)·V_n / Σ_n e(n)², e = `dc_sweep.excite`(차동 (½, −½)이면 V_p − V_n).
3. (v0.3.3, **DV-13 닫힘** -- 정의 = gain-budget DEC-23 '이동의 기준점'(v6.21 223행, 사용자 결정 O-59 (4)), 계획 N3.9 `offset_sys_mv` 행이 인용, 이 문서도 인용만) 값 = V_id* − V_id,0, mV, 부호 그대로(O-50 G1). V_id* = 위 2번의 해(출력 기준 고정 `.dc` 해)의 여기 방향 입력 좌표, **V_id,0 = Σ_n e(n)·V_in,decl(n) / Σ_n e(n)²**, V_in,decl = `dc_sweep.input_dc`(§11.6 선언 입력 DC -- spec 값, θ 봉인점 입력과 같음). **free servo 해 v0을 빼지 않는다**(DEC-23 'SPICE 해(free servo 해)는 기준점이 아니다' -- v0.3.1 식 'V_id,0 = 공칭 free 해의 Σ e·v0/Σ e²'는 이것으로 대체, 옛 식은 servo 목표가 출력 기준과 같으면 값이 늘 0이었음). 차동 입력이 같은 DC로 선언되면 V_id,0 = 0. `input_dc`가 없으면 `input_dc_undeclared`(정의 불능, 추론 금지). 엔진 봉인점 입력 = spec 선언인지의 착수 실측은 엔진 card DE-1 (c) 몫(다르면 그쪽이 멈춤). 단일 입력이면 e = 그 포트 하나라 같은 식. 함께 `dc_resolution_in_V`(§13.4의 기준 해 쪽 항)를 싣는다. 비교 measure는 `offset_sys_mv`(부호 있는 값), 제약은 \|값\| ≤ spec.
4. (v0.3.4 다시 씀, v0.3.5 사유 집합·순서·기록 자리 -- 검증 M2·M4·M5; 계획 v0.6.13 N3.9 `offset_sys_mv` 행 'A_dc 정의 불능'·'오라클의 갈래 판정' (i)~(vi)를 인용, 이 문서는 사유 이름·기록 칸·test만 정함(계획 DR-20 P11); 정본 = gain-budget v6.23 DEC-23 'A_dc 정의 불능 갈래', 사용자 결정 O-62 (3)·O-63 (1)(2)) **정의 불능 사유와 순서**(정의 쪽이 수치 쪽보다 먼저 -- 앞에 걸리면 뒤는 보지 않음, 엔진 DEC-23의 '갈래 먼저'와 같은 순서 원칙):
   * **실행 전 거부**(기존 규칙 그대로, 기록 없음): 단일 출력 기준 미선언 `reference_undeclared`(§7.2 6단계·§18.1 '4 거부' 행 -- 시뮬레이터 호출 0), `.tf`·`.dc` 능력 없음 `adapter_capability_missing`(§7.2 5단계), `dc_tolerance_undeclared`(§7.2 6단계). v0.3.4가 `offset_sys.reason`에 `reference_undeclared`를 넣은 것은 이 실행 전 거부 규칙과 어긋나 지운다.
   * (1) `sweep_direction_undeclared` -- `dc_sweep`(여기 방향 e) 없음 (2) `input_dc_undeclared` -- 선언 입력 DC 없음(V_id,0을 정할 수 없음). 둘 다 정의 쪽, 측정 단위 정의 불능.
   * (3) **갈래 먼저** `a_dc_undefined`: 1~3단계보다 먼저 §21.5의 `sim.a_dc`(같은 설계점·같은 여기 방향 e의 `.tf` A **한 측정** -- σ 입력 환산과 같은 측정, 계획 (i))를 읽는다. `sim.a_dc.status = "undefined"`(사유 `nominal_unconverged`·`tf_failed`·`rail_width_zero`·`a_dc_below_resolution` -- 원인은 `sim.a_dc.reason`이 가리킴, 사본 없음)이면 정의 불능. 이때 1~3단계의 `.dc` 출력 고정 풀이는 **요청하지 않는다**(요청 수 0 -- §18.1 (a)): 그 해가 수렴하더라도 값을 내지 않으므로(계획 (iii) -- 입력이 출력을 움직이지 못하는 점이라 해가 판정 분해능 안에서 정해지지 않음) 그 풀이의 결과는 소비자가 없다 -- 계획 문언 '수렴했더라도'는 `.dc`를 돌린다는 전제로 읽힐 수 있어 **원래 취지와 다름(경미) X-R3, 사용자 확인**(§19.4). **V_id* 벤치에 A 측정을 따로 더하지 않는다**(둘째 생산자 금지, 계획 (i)·DR-20). 'ΔW = 0 → 0(통과)'은 엔진 1차 계산 규칙이고 오라클은 ΔW를 모르므로 오라클 판정 조건이 아니다(계획 (v), O-63 (1)).
   * **(v0.4.0, DR-28 -- 계획 N3.9 `offset_sys_mv` 행 '기준 도달 불가', 상위 U-107·O-119) 기준 도달 불가** `offset_reference_unreachable`: (3) 뒤 (4) 앞에 판정한다. V_ref가 같은 측정 구성의 출력 범위 -- 같은 입력 `sim.swing_icmr.swing` 끝 기록(§11.7, 둘째 `.dc` 없음, 값 사본 없음) -- 밖이면 (v0.4.1 M7: `offset_sys_mv`·PC-10 요청이면 같은 실행·같은 온도에서 swing 훑기를 **블록 요청 여부와 무관하게** 돌려 이 기록을 쓴다 -- `swing_icmr` 블록이 있으면 그 설정, 없으면 `dc_sweep`만으로, 순서 swing → offset. §11.4 '블록 없음 = 결과에 키 없음'의 예외이고 소비자 = 이 판정, swing 제약 판정은 늘지 않음) 정의 불능이고 `.dc` 출력 고정 풀이를 요청하지 않는다(`.dc` 수렴 실패 `sim_convergence_failed`와 다른 사유). swing이 정의 불능이면 `output_range_undefined`(범위를 모르면 도달 여부를 정할 수 없음, fail-closed). 기준 = 값 `net_value`는 그 값, 넷·입력 추종 기준은 그 기준 넷의 공칭 전압, 차동 기본은 출력 차 0을 swing 좌표로 비교. **`sim.offset_sys.ref_minus_servo_ref_V`** = V_ref − s0(§21.2 ICMR servo 목표) 기록 하나(판정에 쓰지 않음, 새 문턱 없음; 소비자 = 검증자 원인 변화표, 출력 전용 선언). 입력 포트 하나인 회로는 servo가 없어 s0 뜻이 없으므로 이 칸이 없다. 손 회로 toy: 출력 범위 밖 V_ref → 이 사유(base = 수렴 실패 또는 값 -- red), 엔진 U-107 toy와 같은 판정. **작성자 판단**: swing 끝을 읽는 순서 의존(swing → offset, 같은 실행) -- 계획은 '출력 범위 행의 `.dc`'만 정함.
   * (4) **`.dc` 수렴 실패** `sim_convergence_failed`: `sim.a_dc.status = "ok"`이고 1~3단계의 `.dc` 풀이가 수렴하지 않음(측정 단위, 옛 그대로) -- (3)의 사유와 다른 자리·다른 이름이다(계획 (iv)).
   * **기록 칸**(v0.3.5 자리 정정, 검증 M2): `<stem>.sim.json`의 **`sim.offset_sys` = {status: "ok" \| "unavailable", value_mv?, reason?, detail?, dc_resolution_in_V?}** -- writer = sim 단계의 코어 `measures_dc`(이 1~4단계 하나), compare JSON은 `sim_ref`(§11.7)로 가리키고 measure 행 `offset_sys_mv`의 값은 그 참조로 읽는다(사본 없음). `reason` ∈ {`sweep_direction_undeclared`, `input_dc_undeclared`, `a_dc_undefined`, `sim_convergence_failed`}; `a_dc_undefined`의 `detail` = `{a_dc_ref: "/a_dc"}`(§7). A 값·갈래 판정 값은 싣지 않는다. PC-10(OP-6, 온도 조건)도 같은 규칙: 그 온도 실행의 sim.json에 `sim.a_dc`·`sim.offset_sys`가 있다(§12.2 PC-10 (e), 같은 함수, 둘째 판정 없음).
   * **판정**(계획 N4-2 '정의를 바꾼 칸', (vi)): 갈래가 발동한 회로의 `offset_sys_mv`는 0번 '동작 변경' 기준. 엔진과 오라클 가운데 **한쪽만** 갈래가 발동한 점은 값 차(DEC-72 대조 기록)가 아니라 **'정의 경계 불일치'**로 검증자 원인 변화표에 적는다(범주 이름·정의 = 계획 N3.9 `offset_sys_mv` 행 (vi), gain-budget DEC-23이 같은 범주를 인용). 오라클 쪽 입력은 `sim.a_dc.status`·`sim.a_dc.reason`이고, 엔진 쪽 갈래 판정은 엔진 기록(card DE-1 (c) 자리)에서 검증자가 읽는다 -- 오라클은 엔진 판정을 받지 않는다.
5. 비교: measure `offset_sys_mv`(§11.6), 판정 폭 `judge.tolerances.offset_sys_mv_abs`가 있을 때만. 엔진 1차값(ΔW 1차 감도, O-46 (1)·O-47) 대 오라클 정확값의 차 = 대조 기록(상위 DEC-72, O-178). 오라클이 재는 점은 판정 W의 설계점이라 엔진 front 판정 점과 같다(계획 N3.9 계통 offset 행 '정합한다').
6. 엔진 `E/metrics/verified_by.py:45`의 `SPICE_UNVERIFIABLE` 표시는 gain-budget VB-1이 바꾼다(계획 U-4·U-6, 이 기능은 엔진을 바꾸지 않음).

### 21.5 불일치 σ 입력 환산의 A = `.tf`(OP-5, 계획 OQ-6 = 사용자 결정 O-43 D1 (d))

**정의 인용**: 계획 N3.9 표 `offset_in_sigma_mv` 행 -- "봉인점 DC 방정식의 1차 감도로 정의되는 DC 양('1차' 표기): 표본마다 V_os,k = (V_out,k − V_out,0)/A − (V_id,k − V_id,0), **A = DC 소신호 차동 이득(`.tf`)**", 해석 = "MC `.op` + `.tf`(servo를 연 개루프 벤치)". (v0.3.3, DV-11 닫힘 -- 계획 v0.6.11 같은 행, 사용자 결정 O-58 DV-11; 정의 정본 = gain-budget DEC-23 'σ 입력 환산 = 계통 offset과 같은 여기 방향 DC 극한 전달 A_dc', 이 문서는 인용만) 현행 인용: "**A = 여기 방향 DC 소신호 전달(`.tf`, 여기 방향 e = 선언 `dc_sweep.excite`로 구동한 개루프 벤치 → 출력)**, V_id = 여기 방향 입력 좌표 Σe(n)V_n/Σe(n)²(차동 (½, −½)이면 옛 V_p − V_n과 같음, 단일 입력 회로는 그 포트 하나)" -- 위 옛 '차동 이득' 인용은 이것으로 대체. §13.4 표본 처리의 V_id도 이 좌표다(차동 (½, −½)에서 옛 식과 같은 값).

**절차**:
1. **개루프 벤치 IR**(`core/build_benches.tf_bench`): 본 회로 + 레일 + 바이어스. 입력 넷 n ∈ `dc_sweep.excite`의 키마다 이상 전압원 = 공칭 free 실행(servo 있음)의 servo 해 전압 v0(n) + e(n)·v_drive, **e = `dc_sweep.excite`**(v0.3.0 gap 지적으로 고침 -- 정의 일반형의 여기 방향 선언을 쓰고 고정 가중을 두지 않음, 계획 N3.9). 차동 입력에서 선언이 `excite = {input_p: ½, input_n: −½}`이면 옛 정의 V_id = V(input_p) − V(input_n)·C27 가중과 같아 (가-1) 비트 동일이 유지된다. `dc_sweep`이 없으면 `sweep_direction_undeclared`. **단일 입력 회로**(excite 키 1개, v0.3.3 DV-11 닫힘): 같은 `tf_bench`, e = 그 포트 하나(선언 `excite` 값 그대로)로 구동한 여기 방향 전달이 A다(차동 회로와 같은 함수·같은 규칙 -- 둘째 경로 없음). **차동 회로는 옛 값과 비트 동일**((가-1) 유지, 계획 같은 행). **단일 입력 회로의 기준선 `unavailable` → 값**은 정의를 바꾼 칸 = 계획 N4 0번 동작 변경이고, 검증자 원인 변화표에 원인 'σ 입력 환산 A의 여기 방향 일반형(O-58 DV-11)'을 칸마다 적는다. (v0.4.9, A-84 C-9: OP-10이 만든다) (v0.3.2) **포트 변형** `tf_bench(port=p)`: e = 그 포트 하나 단위(e(p) = 1, 나머지 0) -- §21.2 반전 입력 포트 판정이 입력 포트마다 이 변형을 요청한다(같은 함수·같은 개루프 규칙). v_drive = 0 V 독립원 `tb:tf:drive`, 두 입력에 VCVS로 나눠 건다(S-42 실측 방식). servo·choke·결합 C·AC 원은 넣지 않는다. 원리는 pz 개루프(`open_loop_parts`, §4.2·§8.5 '동작점 값으로 개루프를 다시 만들기 = 회로 이론')와 같다.
2. 요청 `Tf(out = DiffV(output_p, output_n) | NodeV(output), src = tb:tf:drive)` → A = `TransferResult.gain`(부호 있는 실수, 위상 검사 없음).
3. 기록(계획 N9 `.tf` 행): (v0.3.4, DV-14 닫힘 -- 계획 v0.6.13 N3.9 `offset_sys_mv` 행 (i) '`.tf` 개루프 전달 A 한 측정 -- σ 행의 A와 같은 측정이고 두 행이 그 하나를 읽는다', 사용자 결정 O-63 (2)) 기록 자리를 `offset_mc` 안에서 **sim 단계 결과 `<stem>.sim.json`의 `sim.a_dc` 하나**로 옮긴다(v0.3.5 정정 -- v0.3.4 'compare JSON 최상위'는 측정 결과가 사는 sim 단계와 판정 단계를 섞었음, 검증 M2) -- 그 A를 σ 입력 환산(`offset_mc`)·계통 offset(§21.4)·PC-10이 함께 읽고, `offset_mc`가 요청되지 않은 계통 offset 실행에도 같은 측정이 있어야 하기 때문이다(둘째 측정·사본 없음). 결과 계약이 바뀌어(OP-6 PC-10·EO-1·검증자 N4-2 대응) **원래 취지와 다름(경미) X-R4, 사용자 확인**(§19.4). `sim.a_dc = {status: "ok" \| "undefined", value?: A, reason?, detail?, tf_bench_output_shift_V?, tf_record?: {out_impedance, in_impedance}}`. 옛 칸 대응(검증 M3): 코드·기준선 이름 **`offset_mc.a_dc_signed`**(`O/oracle_offset_mc.py:189`) → `sim.a_dc.value`(§11.5 결과 칸 표); v0.3.3 design이 이름 붙인 `offset_mc.a_dc_tf`·`tf_bench_output_shift_V`·`tf_record`도 이 기록으로(같은 양, 자리·이름만; `tf_bench_output_shift_V` = V_out(개루프 벤치 `.op`) − V_out(servo 해), `tf_record`는 출력 전용). **writer = 이 1~4단계 하나**(sim 단계의 코어 `measures_dc`), 소비자 = 코어 `mc_math`(A를 인자로 받음, §13.2)·§21.4 4단계·검증자 원인 변화표('정의 경계 불일치'). compare JSON은 복사하지 않고 `sim_ref`(§11.7)로 가리킨다. `offset_mc`·`offset_sys` 기록에는 A 값 칸을 두지 않는다(사본 금지 -- graph 단일 정본 규칙 1·4). **있는 조건**(검증 N2): free bias 실행이고 `offset_mc`·`offset_sys_mv`·PC-10·**입력 포트 둘인 회로의 ICMR(servo 부호, §21.2 -- v0.4.1 M2)** 가운데 하나라도 요청됐을 때만 한 번(여기 방향 `tf_bench`(port 없음) 1회 -- 반전 입력 식별용 포트별 `tf_bench(port=p)`는 §21.6 0단계의 별도 측정); 소비자에 §21.2 servo 부호를 더한다; forced·iso bias, 넷 다 요청 없음, 벤치 `BLOCKED`, 실행 전 거부면 `sim.a_dc` 칸이 없다(소비자 없는 측정 없음).
4. (v0.3.4 다시 씀, v0.3.5 사유 집합 완성 -- 검증 M1·M4; 정본 = gain-budget v6.23 DEC-23 'A_dc 정의 불능 갈래', 계획 N3.9 σ 행(v0.6.12 O-61 P7)·`offset_sys_mv` 행 (ii)~(iv)) **`sim.a_dc`의 사유 집합과 순서**(앞에 걸리면 뒤는 보지 않음 -- 정의 쪽이 수치 쪽보다 먼저):
   * **실행 전 거부**(기존 규칙, 기록 없음): `.tf` 능력 없는 어댑터 `adapter_capability_missing`(§7.2 5단계), DC 풀이 허용오차 미선언 `dc_tolerance_undeclared`(§7.2 6단계). 공칭 free 벤치 막힘은 `BLOCKED`(§7.2 10단계) -- 셋 다 `sim.a_dc` 칸 없음.
   * (1) `sweep_direction_undeclared` -- `dc_sweep` 없음(정의 쪽; 측정 단위 정의 불능, §7 `measure_feedback_undeclared`·`input_dc_undeclared`와 같은 '그 측정만' 처리) (2) `nominal_unconverged` -- 구동 전압 v0(n)을 주는 공칭 free 실행(1단계)이 수렴하지 않음(`detail = {error: <그 실행의 오류 코드>}`) (3) `tf_failed` -- `.tf` 결과 없음(개루프 벤치 `.op` 미수렴 포함; fail-closed, `.ac` 대체 경로 없음).
   * (4) (v0.3.6 다시 씀, **DV-17 닫힘** -- 계획 v0.6.14 N3.9 '전달 판정 분해능'(이 계획의 오라클 쪽 자리 하나), 사용자 결정 O-67 (3)·O-68 (1)·O-70 (1)·R-1, DR-21; 정의·식 = gain-budget v6.24 N3.8 'ICMR 측정 구성' '판정 분해능의 정의 자리'(병합 `59ecc88e` 576행) 인용, 오라클 δV_out 꼴도 같은 자리 인용) **전달 판정 분해능** -- `.tf` 결과 A가 있을 때: (4a) 레일 폭 W_rail = 입력 `rails[].voltage`의 최대 − 최소(§11.1 `/rails`)가 0이면 `rail_width_zero`(판정 불능, fail-closed) (4b) **\|A\|·W_rail ≤ δV_out**이면 갈래 `a_dc_below_resolution`(A = 0 포함). δV_out = 그 전달 출력 식의 전압 분해능: `NodeV(o)`이면 vntol + reltol·\|V(o)\|, `DiffV(o_p, o_n)`이면 δ_p + δ_n(각 노드 vntol + reltol·\|V\|); \|V\| = **공칭 `.op` 전압** = 1단계 공칭 free 실행(servo 해)의 그 노드 전압(이 측정이 이미 읽는 값 -- 개루프 벤치 `.op` 값이 아님; 둘의 차는 `tf_bench_output_shift_V`로 따로 기록). vntol·reltol = 그 실행의 `Resolution`(계획 N0 '값 원칙' 29행: 입력 `simulator.options` → 출처 있는 어댑터 `default_tolerances`(§8.3) → 둘 다 없으면 실행 전 `dc_tolerance_undeclared`). 구동 진폭·`.tf` 잔차를 고르지 않는다(새 선택·상수 없음). **판정 함수 하나**(`core/measures_dc.transfer_resolvable(A, out_expr, nominal_op, rails, resolution)`) -- §21.2 반전 입력 후보 판정도 이 함수를 부른다(둘째 식 금지). **기록**: 사유만(`sim.a_dc.reason`) -- δV_out·W_rail·문턱 값은 입력에서 다시 잴 수 있어 저장하지 않는다(새 값 칸 금지, DR-21; v0.3.5의 `detail = {A, resolution}` 계획은 지움). 엔진 문턱(선형해 수치 분해능, O-71)과 오라클 문턱이 달라 한쪽만 발동하는 회로는 '정의 경계 불일치'(계획 `offset_sys_mv` 행 (vi))로 기록된다. 그 밖 → `status = "ok"`, `value = A`. 실현 가능성 = §19.6 F-3.
   * 소비: `sim.a_dc.status = "undefined"`이면 `offset_mc.status = "unavailable"`, 사유 `a_dc_undefined`(§7, `detail = {a_dc_ref: "/a_dc"}` -- 원인 사본 없음), 표본 처리(5단계 뒤 §13.4)를 하지 않는다(단 `sweep_direction_undeclared`면 `offset_mc`도 같은 정의 쪽 사유를 먼저 낸다). 계통 offset은 §21.4 4단계. `.tf` 실패·갈래는 `sim.a_dc.reason`으로, `.dc` 수렴 실패는 `sim.offset_sys.reason`으로 나뉜다(계획 (iv)).
   * **판정**(계획 N4-2 '정의를 바꾼 칸', O-61 P7): 갈래가 발동한 회로의 σ 칸은 0번 '동작 변경' 기준이다 -- 차동 회로의 (가-1) 비트 동일 예외는 **이 갈래가 발동한 회로뿐**이고(승인 O-61), 검증자 원인 변화표에 회로마다 원인 'A_dc 정의 불능 갈래(DEC-23)'를 적는다. 엔진·오라클 가운데 한쪽만 발동한 점 = '정의 경계 불일치'(§21.4 4단계 '판정'과 같은 범주). 갈래가 발동하지 않은 차동 회로는 (가-1) 비트 동일 그대로.
   * (v0.3.3) 옛 '차동 입력 쌍이 없으면 `unavailable`' 갈래는 지운다(DV-11 -- 단일 입력도 위 1단계로 A를 잰다).
5. A는 표본 0(공칭) 벤치에서 한 번 잰다(옛과 같음). 표본 처리 식(§13.4, `core/mc_math`)은 그대로라 (가-1)은 기준선 A(`a_dc_signed`)로 비트 동일을 유지한다(§13.2).
6. **깨진 변형**(완료 조건 10): servo가 닫힌 넷리스트에서 `.tf`로 A를 읽는 경로 -- 손 회로(gm·R 개루프 이득이 있는 차동 VCCS)에서 폐루프 값이 나와 기대값과 다름을 보인다(S-42·계획 OQ-6 실측 0.495 대 100). `.ac` 첫 점·`1e-3` 경로는 grep 0(완료 조건 6). (v0.3.4, DV-14) 갈래 깨진 변형: \|A\| ≤ 판정 분해능인 손 회로에서 σ·V_id* 값을 내는 경로, 갈래를 'ΔW = 0 → 0' 뒤에 두거나 오라클 쪽에 ΔW 조건을 두는 경로, V_id* 벤치가 A를 따로 재는 경로(둘째 측정), `.tf` 실패와 갈래를 같은 사유로 내는 경로 -- 각각 실패(§18.1 '10 정의 대조 -- OP-5' 행).

### 21.6 슬루율(OP-10, `core/slew_math.py`) -- (v0.3.1) DV-9 닫힘(사용자 결정 O-50 G2·O-51)

**(v0.4.0 다시 씀, DR-27 -- 계획 N3.9 슬루 행, OP-10 행, 상위 U-102(O-116)·O-119·O-121 B-2·O-157 S1) 정의 인용**: metric = 방향별 둘 `slew_rise_v_per_s`·`slew_fall_v_per_s`(각각 spec과 비교, spec이 하나만 선언하면 두 방향 모두에 적용, 집계 없음). **판정 계단** = 상위 spec `.tran` step(원문 계단 선언 회로), 없으면 follower 사용 범위 전 폭(상승 아래 끝 → 위 끝, 하강 위 끝 → 아래 끝). **기울기** = 판정 계단 출력의 20 %~80 % 구간 기울기(옛 '구간 최대 |dV/dt|'는 계단 가장자리 피드스루로 과대). **추종 판정** = 이상 폐루프 목표(계단 × 1/β) 기준 양 끝 검사, `.tran` 끝 시각 = t_step + |Δx|/SR_req. **과도 측정 유효성** = 계단 입력 구간 ⊆ `follower_input_range_v`, 어기면 정의 불능. 진폭 선언 칸 없음. 엔진은 슬루·계단 칸이 없다(O-122).

**0단계 -- 슬루 측정 구성 보조 정의**(§21.2에서 옮김, ICMR 갈래 문언만 뺌 -- 계획 N3.9 슬루 행 '슬루 측정 구성 보조 정의'; 코어 `slew_math`로 이동, 엔진 구현 없음):
* **DC 되먹임 판정**(v0.3.9, 계획 v0.6.16 N3.9 ICMR 행 'DC 되먹임 판정'·DR-24 (1), 사용자 결정 O-81 (2)·O-82; 정의 = gain-budget v6.27 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나' 문단 하나 -- 이 문서는 인용하고, 아래는 오라클이 같은 정의를 자기 입력만으로 따로 구현하는 자리(NFR-P3, 엔진 판정을 입력으로 받지 않음)): 슬루 측정 구성 갈래·슬루 시작 동작점 갈래(아래 1·1b단계)의 'DC 되먹임 있음/없음'은 이 판정 하나를 읽는다(코어 `slew_math.dc_feedback_judgment` 하나 -- ICMR은 읽지 않음, 상위 O-115; 엔진 구현 없음, 상위 O-116). **언제**: `measure_feedback.kind = declared`이고 입력 포트가 둘 이상일 때만(입력 하나면 회로 그대로라 부르지 않음 -- O-80 R2), §7.2 10단계 C14 막힘 검사 뒤, **어떤 시뮬레이터 호출보다 먼저**(입력 칸만 읽음; `.tf`·동작점·T_p 안 씀). **그래프**(방향 의존 그래프, 마디 = 넷): `/passives`(§11.1) `kind = resistor` → 두 단자 사이 양방향 엣지(`capacitor`는 엣지 아님 -- DC에서 열림); `/devices` → drain↔source 양방향, gate→drain·gate→source 한 방향(bulk는 엣지 아님 -- 정의 문단의 엣지 목록에 없음); `/sources` `kind = "current"` → 엣지 아님. **지원 밖 원소**(v0.3.10 정렬 -- 계획 v0.6.17 DR-25 (2), 사용자 결정 O-85 (3); 정의 = gain-budget v6.28 N3.8 같은 문단 '지원 밖 원소' 규칙 인용, 옛 인용 '이상 전압원 = 지원 밖' 대체): 오라클 입력에서 지원 밖 원소 = `/sources`의 `kind = "voltage"`(엔진 지원 이상원 = 전류원 하나와 같은 경계)이고, 하나라도 있으면 판정 **정의 불능**(`detail.why = element_unsupported`). 그 밖의 kind는 입력에서 이미 막힌다 -- `/passives` kind는 닫힌 열거(resistor·capacitor, §11.1 840행) 밖이면 스키마 거부, `/devices` kind는 기술자 `kinds` 키가 아니면 `descriptor_kind_undeclared`(§7) -- 그래서 판정 단계에 도달하는 지원 밖 kind는 `/sources` voltage 하나다(오라클은 kind 목록으로 다시 판정하는 둘째 검사를 두지 않고, 이 한 갈래만 본다). **끝점** = 선언 절단 넷 = `/feedback_passives` 원소의 `/passives` 단자 ∩ 입력 포트 넷(`/ports`의 `input_p`·`input_n`·`input`) -- 이 집합은 §7.2 10단계 C14 검사와 **같은 규칙 하나**(지금 `O/oracle_netlist.py:234-253` `loop_break_nets` -- 소자마다 입력 포트 단자 정확히 하나, 아니면 막힘)의 넷 목록을 읽는다(둘째 절단 규칙 없음). **경유 금지**(정의 문단 '고정 전위 넷'): `/rails`의 넷, 끝점이 아닌 입력 포트 넷(측정 구성이 구동), `/bias_voltages`의 넷(게이트 전용 이상 전압 넷 -- 들어오는 엣지가 없어 원래 중간 마디가 될 수 없음; 같은 뜻을 명시)은 중간 마디가 되지 않는다(끝점은 예외). (v0.4.0, OP-B3) 게이트 전용 조건은 입력 계약 §11.2 1d `bias_gate_nets_mismatch`가 먼저 보장한다(옛 `bias_not_gate_only` 갈래 삭제 -- 옛 문장 history v0.4.0). **판정**: 출력 넷(`/ports`의 `output` 또는 `output_p`·`output_n` 각각)에서 BFS로 끝점 가운데 하나라도 도달하면 그 출력은 'DC 되먹임 있음', 아니면 '없음'(정의 문단 '선언 절단 넷까지 도달하는 경로가 있다'). 단일 출력 = 그 출력의 판정. (v0.3.9 둘째 커밋, 검증 N3) 차동 출력에서 '끝점 가운데 하나라도'는 **반대쪽 절단 넷도 센다** -- 출력 o_a에서 o_b 쪽 반전 입력(절단 넷)에 닿아도 o_a는 '있음'이다(정의 문단의 끝점 = 선언 절단 넷 집합 전체, 출력과 절단 넷의 짝을 묻지 않음; 짝 식별은 `.tf` 몫이고 이 판정은 `.tf`를 쓰지 않음). **차동 출력의 결합**(v0.3.10, DV-21 닫힘 -- 계획 v0.6.17 DR-25 (1), 사용자 결정 O-85 (1)·O-86 N3; 정의 = gain-budget v6.28 N3.8 같은 문단 '**차동 출력**' 규칙 인용, 규칙을 다시 적지 않음): 두 출력의 판정이 같으면 그 판정을 슬루 갈래가 읽고, 갈리면 판정 정의 불능 → `dc_feedback_judgment_undefined`(`detail.why = differential_split`, `detail.present`·`detail.absent` = 출력 넷 이름만). (v0.3.9 둘째 커밋의 'DV-21 전에는 OP-5에서 구현하지 않음'은 풀림 -- history v0.3.10.) 판정 정의 불능(원인 둘: 지원 밖 원소 `element_unsupported`, 차동 두 출력 판정 갈림 `differential_split`)이면 그 슬루는 `dc_feedback_judgment_undefined`(§7). 판정 결과는 새 기록 칸이 아니다 -- 결과는 고른 갈래(또는 거부 사유)로만 남는다. 비용: 입력당 BFS 한 번 O(넷 수), cache 없음.
* **반전 입력 포트**: `inverting_input` 선언이 있으면 그것; 없으면 오라클이 §21.5 개루프 `tf_bench(port=p)`를 입력 포트마다, 출력마다(단일 출력 `NodeV(out)`, 차동 출력은 `NodeV(o_a)`·`NodeV(o_b)` 각각) 돌려 동작점 DC 전달 T(p → o)의 부호가 음수인 포트를 고른다(엔진 값을 받지 않음, 포트 role 이름은 근거 아님). 음수 후보 0개·2개 이상, 후보 전달이 **전달 판정 분해능**으로 판정 불능(§21.5 4단계 (4)와 같은 판정 함수 하나 -- 출력 식은 그 `NodeV`), 차동 출력에서 두 출력의 반전 입력이 같은 포트, 레일 폭 0이면 `inverting_port_undetermined`(슬루 정의 불능, 사유 기록). (v0.3.5 DV-17 멈춤은 v0.3.6에서 닫힘 -- §21.5 4단계 (4).)


**절차**(v0.4.0 -- 계단 전달 = 같은 덱 `.dc`, DR-27):
1. 벤치(`slew_bench`; v0.3.6 다시 씀 -- 계획 v0.6.14 N3.9 슬루 행 '시작 동작점', 사용자 결정 O-69 (1) OQ-11 (다), DR-22): **과도 구간 되먹임 = 선언 구성 전체**(`declared`면 입력 회로·`feedback_passives` 그대로 -- 용량 포함, O-34 (2)); 단일 출력 + `unity_follower` = 출력을 반전 입력 포트(0단계 규칙)에 잇는 이득 1 `Vcvs`; 단일 입력 = 회로 그대로; **차동 출력 + `unity_follower` = `feedback_config_undeclared`(`why = differential_undeclared`, 정의 불능 유지)**; 반전 포트 판정 실패 = `inverting_port_undetermined`. 입력 넷의 servo·choke는 넣지 않는다. 결과에 `slew.beta_default = (measure_feedback.kind == "unity_follower")`. **계단 자리**(v0.3.8 줄임 -- 계획 v0.6.15 DR-23 (1)·OP-10 행): 구성이 닿지 않은 입력 포트(선언 원소의 단자에 없는 입력 포트)가 있으면 그 포트의 원. 선언 구성이 모든 입력 포트에 닿으면 계단 자리(입력 망 원소의 다른 단자)는 gain-budget card AP-1 몫이라 OP-10에서는 `feedback_config_undeclared`(`why = input_network_step_deferred`)로 정의 불능이다(입력 포트에 원을 걸면 그 포트의 되먹임이 사라지므로 걸지 않음 -- 입력 망은 선언 몫, O-69 (1)). 옛 '입력 망 원소의 다른 단자에 원' 갈래와 `no_input_network`는 history v0.3.8. **착수 실측 결과**(DR-22, §19.3; v0.3.8 재측정 §19.6 F-11): current_reuse 선언 = {Cf1(Vom–Vip), Cf2(Vop–Vim)}가 두 입력 포트에 닿음 → `input_network_step_deferred`(정의 불능 그대로, 사유 문자열만 옛 `no_input_network`에서 바뀜). **단일 출력 + DC 되먹임 없는 선언**(0단계 판정, v0.4.1 M6): `feedback_config_undeclared`(`why = start_op_deferred`, 시뮬레이터 호출 0) -- 1a `.dc`를 돌리지 않는다. **(v0.4.1 M5, 위임 A-21) 입력 포트 둘 이상 + `declared`이고 지금까지 사유에 걸리지 않은 구성** = `feedback_config_undeclared`(`why = beta_undefined`, 정의 불능, 시뮬레이터 호출 0) -- 선언 망의 β 유도 규칙은 계획에 없다(AP-1과 함께 계획 개정, 상수 발명 금지). **원래 취지와 다름**: 선언 구성의 슬루 판정 보류(발동 0/13 -- library 비지 않은 선언은 current_reuse 하나이고 이미 `input_network_step_deferred`; 재점검 = LA-1 완료 13). 검증자 판단은 `spec_elements.py:19-20` 읽기이고 LUT·SPICE 측정 없음.
1b. **`.tran` 시작 동작점**(t = 0 해; v0.3.8 다시 씀 -- 계획 v0.6.15 N3.9 슬루 행 '시작 동작점 경로의 구현 자리'·OP-10 행·DR-23 (1), 사용자 결정 O-78 (1)): 선언 되먹임에 DC 되먹임이 있으면(v0.3.9 -- 0단계 DC 되먹임 판정 하나, 계획 v0.6.16 DR-24 (2); 옛 'DC 성분' 문언은 history v0.3.9)(또는 단일 출력 + `unity_follower`) 과도 벤치 자신의 바이어스 해 그대로. **용량만 선언된 차동 출력**의 t = 0 시작 동작점 경로(정의 = 계획 N3.9 슬루 행 '시작 동작점'이 인용하는 gain-budget N3.8 DC 닫힘)는 **OP-10에서 만들지 않는다** -- gain-budget card AP-1(N6.22) 몫이고, 그때까지 그 슬루는 `feedback_config_undeclared`(`why = start_op_deferred`, 1단계 구성 검사, 시뮬레이터 호출 0)로 정의 불능이다. AP-1에서 만들 때 t = 0 시작점은 같은 입력의 ICMR 공칭 점 기록 `v_in`(§11.7, x = 0 점 -- AP-1이 ICMR 측정을 함께 요구한다)을 참조로 읽는다 -- 시작점용 닫힘 `.op`(둘째 생산자)를 두지 않는다(검증 필수 1, graph 규칙 1·2·4). 옛 v0.3.6 1b 본문(닫힘 `.op` → `Tran.ic`, 손 회로 test)은 history v0.3.8. `Tran.ic`·`tran_ic_bias_only`는 이 경로 몫이 아니라 OP-4 C10 몫으로 남는다(§4.2, §8.3; 둘째 커밋 M1 정정).
1a. **`follower_input_range_v`**(DR-27, 새 record 이름, 상위 N3.8 '입력 범위 세 양' (3)): **같은 덱**에서 1단계와 같은 구성(같은 되먹임·같은 원 자리)의 `.dc` 훑기로 계단 자리 입력을 공칭에서 바깥으로 훑어 모든 MOS가 선언 영역에 머무는 입력 범위를 잰다. 점 판정·끝 풀이·레일 필터·r은 §21.2와 같은 함수다(sweep 절차 하나, 구성만 다름 -- 옛 ICMR 확정 끝 읽기 없음). 결과 `sim.slew.follower_input_range_v = {status, lo, hi}`(끝 기록 꼴 = §11.7 '범위 끝 기록'). 정의 불능이면 슬루 정의 불능 `follower_range_undefined`(옛 `slew_step_end_undefined` 대체, 다른 값으로 대신하지 않음). 공칭 점이 범위 밖인 회로(실측 two_stage_ota_sf 사례 -- 상위 U-102)도 이 사유다.
2. **계단**(DR-27): 1단계 계단 자리에 `Pulse`. `/slew.step`(§11.6, 상위 spec `.tran` step 선언)이 있으면 v1·v2 = 그 선언; 없으면 전 폭 -- 상승 v1 = lo → v2 = hi, 하강 v1 = hi → v2 = lo(출력 방향 기준은 4단계 시간열 부호). **왕복 없음**: 위 1a 범위에서 바로 계단을 정한다(옛 `confirmed_range.icmr` 지목·`range_final` 읽기·2단계 왕복 삭제). 선언 step이 범위 밖이면 유효성 위반 = `slew_step_out_of_range`(정의 불능). **두 계단폭 보고**(O-119 정정 4·O-120, U-110): 판정 = 위 계단. 무릎 A_lo = SR_fw/(2π·UGF_β)(UGF_β = 같은 측정 구성 oracle 측정 -- 3단계 교차 주파수 읽기 하나)와 그 계단의 기울기 SR(A_lo)는 **보고 전용** `sim.slew.knee = {a_lo_V, sr_at_a_lo_v_per_s?}`, A_lo가 범위 밖이면 `knee_out_of_range = true`('범위 안 슬루 시작 없음'). class-AB 회로 '전 폭에서 잰 값' 표기(`sim.slew.full_swing_step = true`). 소비자 = 결과 보고(출력 전용 선언).
3. 시간 계획: 코어 `tran_plan` 수학 재사용(C10, §8.5 -- 새 상수 금지, 계획 G-19). 입력은 그 되먹임 구성 루프의 교차 주파수(같은 입력의 β 루프 측정). 계획을 세울 수 없으면 `status = "unavailable"`, 사유 `tran_plan_undefined`. 어댑터는 `tran`·`tran_large_signal`과 최대 걸음 지정 능력(§8.5)을 선언해야 한다(없으면 `adapter_capability_missing`).
3a. (v0.4.1 M4 -- 상위 N3.8 '`.tran` 끝 시각') 3단계 `tran_plan`은 걸음·t_step만 정한다. **끝 시각 = t_step + |Δx|/SR_req**, SR_req = 입력 `acceptance.constraints[]`의 그 방향 measure(`slew_rise_v_per_s`·`slew_fall_v_per_s`; spec이 `slew_rate_v_per_s` 하나만 선언하면 그 값이 두 방향 -- §11.6) 값(참조, 사본 칸 없음). 제약이 없으면 그 방향 `slew_required_undeclared`(정의 불능, 시뮬레이터 호출 0 -- 상위 '속도 선언이 있을 때만 정의').
4. **기울기**(DR-27, O-121 B-2): 측정 노드 `slew.node`의 시간열에서 판정 계단 출력의 20 %~80 % 구간 기울기(방향별, 두 교차 시각의 ΔV/Δt -- 격자 사이는 선형 보간). 옛 구간 최대 |dV/dt|는 쓰지 않는다. 결과 `sim.slew.{rise, fall}`(출력 방향 기준 -- 각각 measure `slew_rise_v_per_s`·`slew_fall_v_per_s`, 어느 계단이 출력 상승인지는 시간열 변화 부호로 정함) = {`slope_v_per_s`, `t_20`, `t_80`, `max_step_s`, 추종 판정 결과}. 추종 판정 = 이상 폐루프 목표(계단 × 1/β) 양 끝 검사(상위 N3.8 (가)(나)(다) -- x_from ± 20 %·|Δx|, x_from + 0.8·Δx 통과, 끝 시각(3a)에 x_to ± 20 %·|Δx|), 어기면 그 방향 정의 불능. β = 1은 `unity_follower`와 단일 입력만(1단계 `beta_undefined`).
5. 거부: `slew_undeclared`(§11.6 칸 없음), `follower_range_undefined`, `slew_step_out_of_range`, 수렴 실패·시간 상한 → `sim_convergence_failed`·`sim_timeout`(측정 단위 `failed`).
6. 판정: 새 측정(기준선 없음, N4 동일성 대상 아님). 손 회로 test = 해석해가 있는 슬루 제한 회로(정전류 I로 부하 C를 충전하는 출력단 모형, SR = I/C를 test 작성자가 정의에서 씀). `settle_s`는 '정의 미정' 그대로(C25).

### 21.7 전력 `power_dc_w`(OP-11, `core/measures_dc.py`)

**정의 인용**: DEC-78 277행 "전력 축의 정의 = Σ_레일 V_레일 · I_레일(공급 전력, metric `power_dc_w`) … DC 정지 전류 기반이고 레일마다 전압 × 그 레일에서 들어오는 전류를 합한다. 레일별 값도 기록한다".

**절차**:
1. 같은 free `.op` 결과의 `rail_current_A`(레일 노드에서 회로로 나가는 전류 = −i(레일 원), S-46)와 입력 `rails[].voltage`를 쓴다. 새 시뮬레이션은 없다(계획 OP-11 '기존 측정 재사용').
2. `power_dc_w` = Σ_{셈하는 레일 ∖ 기준 레일} V·I(I = 아래 2a DUT 레일 단자 전류). 레일별 `power.per_rail = {net: {V, I, P}}`도 싣는다. 기준 레일은 0 V(OP-3 입력 규칙 `reference_rail_voltage`가 보장)라 항에 넣지 않는다 -- 엔진 `E/metrics/supply.py:69`(모든 레일 합)와 같은 값.
2a. (v0.4.0 -- 계획 OP-11 행 P7·M-5, 상위 O-73·DEC-78·DEC-105 (9)·SF-1 범위 8) **DUT 레일 단자 전류** I_k = `rail_current_A[k]` − (그 레일 넷에서 측정 부하 원소(입력 `/passives`의 `measurement_load: true`)로 나가는 DC 전류). 셈하는 레일 = 입력 `/counted_rails`(§11.6)가 있으면 그 레일, `power_dc_w`만 없으면 레일 전부. `power_dc_w` = Σ_{셈하는 레일 ∖ 기준 레일} V_k·I_k. **`supply_current_A`** = `counted_rails`의 Σ I_k(정의를 바꾼 칸 -- 엔진 `supply_current_dc`와 정의 하나); `counted_rails` 미선언 = measure 없음 `not_computed`(기본값 없음). 옛 '레일 하나' 부착은 삭제(`legacy_adapter`는 LT-1). 깨진 변형: 측정 부하 전류를 빼지 않음, `counted_rails` 미선언에 레일 전부 합산.
3. 레일 전류가 하나라도 없으면 합을 내지 않는다(`power_undefined`, 부분 합 금지). 막힌 실행이면 `power_undefined`(`why = blocked`).
4. **부호**(계획 OP-11 '엔진과 같음'): 음 레일(V < 0)에서는 I < 0이라 V·I > 0(공급 전력 양수).
5. **레일 밖 원천 기록**(계획 OP-11, N9): forced 실행의 `hold_current_A`(옛 `Vhold_`), 테스트벤치 DC 원(옛 `Vdc_`·`Vbias_`, servo 기준원)의 DC 전류를 `power.offrail_currents_A = {원 이름: A}`에 싣고, 0이 아닌 값이 하나라도 있으면 `power.offrail_nonzero = true`(문턱 없음 -- 값 ≠ 0 그대로). 그 원천 전류는 본 벤치 `Op` 요청의 `outputs.currents`에 넣어 같은 실행에서 읽는다.
6. 비교: measure `power_dc_w`(§11.6) 행 -- 엔진 예측(`predictions.metrics`) 대 오라클 값, 판정 폭 `judge.tolerances.power_dc_w_rel`이 없으면 'N/A(tol 미설정)'. 엔진 대 오라클 차 = oracle 판정 기록 안의 대조 기록(상위 DEC-72, O-178 -- 판정 기준 아님, 옛 `derived.model_error_power_dc_w` 삭제). 엔진 `verified_by` 연결 변경은 gain-budget PW-1a 몫(계획 U-5).
7. 손 회로 test: 레일 둘(양·음) + 저항 둘 → 기대값 Σ V²/R를 test 작성자가 정의에서 씀. 깨진 변형: 기준 레일을 항에 넣음(기준 레일 0 V 규칙 덕에 값은 같으므로 test는 기준 레일 전류가 결과 항 목록에 없음을 단언), 레일 하나 전류 누락 시 부분 합, 전압 부호 반대.
