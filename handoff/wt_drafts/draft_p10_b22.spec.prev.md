---
id: 20260930-p10-df23-inventory
phase: 2
evidence_type: test-only
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

design `20-dead-code-dup` §1·§8 P10·§10 E3와 계획 DF-23(담당 `2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)`)·N6.2 `2`(1017행 "DF-23 전수 목록 … 항목마다 담당 Phase가
적혀 있음"): 엔진 소스의 소자·넷·회로 이름 리터럴과 topology 파일 경로 리터럴 **전수 목록**을 card base에서 다시 재고, 항목마다 **담당 Phase**를 적어 E3를 충족시킨다.
함께, Phase 2가 지우거나 옮긴 엔진 이름을 아직 사용 안내로 적고 있는 skill 참조 문서를 사실에 맞춘다(**문서 백로그 B22 (b)** -- 아래 '번호 B22의 뜻'). A = `skills/analog-gmid-design/assets`.

**번호 B22의 뜻(두 가지로 쓰여 여기서 고정한다)**: 이 card의 B22는 `.ai/context.md` 14943행(2026-09-23 P5 완료 기록)의 백로그다 -- 원문: "백로그 B22(문서): (a) sizing_recipe.py
모듈 docstring 15행 '기생 CJD 반영 반복 -> optimize_multistage()의 cgg 반복' -- 되먹임은 Cgg이지 CJD 아님, 삭제 뒤 CJD 모델 없음. 제안 '기생 커패시턴스(Cgg) 반영 반복'(엔진
텍스트라 code card 필요) (b) references/function-selection-map.md 35·38·80, stick-diagram-euler-layout.md 1065·1102가 지운 converge_with_parasitics·slew_rate·render_stick_diagram 안내
(c) tests/probes/ 14개 주석의 H.derived_spec 안내 -> P4에서 정리." 뒤에 합류한 것: 14950행(P5b -- `test_s065_section`·`test_s067_family` docstring·주석의 삭제된 폐형식 언급 -> B22 합류),
14966행(P6 -- `function-selection-map.md` 99행 `find_interleaved_symmetric_splits` 위치 안내 -> B22 합류), 14977행(references의 세 이름 안내는 "B22 별도 card").
**같은 번호의 다른 항목**: history §10.3 B22(`docs/01-plan/features/gain-budget-gmid-sizing.history.md` 4002행 "`diode_vds_window()`가 diode 자신의 W만 봄 | 해소 -- `mirror_members`로
VGS 공유 소자 전원을 봄", 2026-09-09, 커밋 d64175b) -- 엔진 주석 SR 567·3425·7412와 레지스트리 77행 "(B22)"는 이 뜻이다. `.ai/context.md`의 백로그 번호(B6~B28, 2026-09-2x)는
history의 B 번호(§10.3 B1~B25, 규칙표 B10~B21)와 별개로 매겨져 겹친다. 이 card는 혼동을 막으려고 본문에서 항상 **'문서 백로그 B22'**라 쓰고 위 두 출처를 적는다(card id·test
이름에 `b22`를 넣지 않는다). 오케스트레이터 제안: 다음 `.ai/context.md` 기록에서 context 백로그를 `BL-` 접두사로 부르기 시작한다(옛 기록은 그대로 두고 대응만 한 줄 적는다).
(c)는 P4 `20260929-probe-engine-dup` 계약 4에서 처리됐다.

**왜 목록을 다시 재는가**: 지금의 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`은 `1e2e243`(HEAD cd64170보다 101커밋 앞)에서 쟀다. '동작을 정함' 266항목 중
줄이 그대로인 것 13, 내용이 다른 줄로 옮겨간 것 211, **소스에서 사라진 것 42**(P5·P5b 삭제와 DF-35 경로 변경)이고 `phase` 필드가 없다(scratch `p10_df23.py`). design §8 P10의
"266건·신규 148건"은 더 이상 사실이 아니므로 이 card의 계약 수치로 쓰지 않는다.

**판정 유형 -- test-only(문서)**: 이 card에는 code 커밋이 없다. 산출물은 오케스트레이터가 쓰는 문서(`docs/03-analysis/**`(레지스트리 제외), `skills/analog-gmid-design/references/**`,
`SKILL.md`, design 문서)와 test-author가 쓰는 계약 test뿐이다(계획 N3.12.2). 계획 DF-23의 **'레지스트리 기록'은 이 card에서 뺀다** -- 레지스트리는 gmid-code-author만 쓰는 경로
(N3.12.2 603행; 오케스트레이터 `docs/03-analysis/**` 행(626행)이 레지스트리를 제외)라 넣으면 code 커밋이 생겨 test-only 모양이 깨지고, 그렇다고 red-green으로 가면 문서(오케스트레이터
base 커밋)를 판정하는 새 test가 base에서 이미 통과해 red 모양이 성립하지 않는다. 기본안: 이 card 병합 뒤 레지스트리에 DF-23 기록(목록 경로·`measured_at`·총계)을 더하는
작은 red-green card를 따로 두고, 잃지 않도록 design §8에 그 행을 이 card의 문서 커밋에서 더한다(아래 '결정 필요 항목').

**순서**: 오케스트레이터가 N3.12.3 순서 1에서 spec card·interface card와 함께 **문서 커밋**으로 재측정 목록·참조 문서 정정·design 정정을 gate에 반영한 뒤 test worktree를 만든다
(문서 커밋은 역할 커밋(`Role` ∈ {code, test, audit})이 아닌 오케스트레이터 커밋이고 card push 전에 gate에 들어가므로 -- 선례 6398a28·ab90ec5 -- card의 test-only 모양 `old..new`에
들지 않는다, design 05 §10-3·4). 그래서 새 test는 base(문서 커밋 포함)에서 통과해야 하고,
auditor는 문서 커밋 **직전** 커밋에서 새 test가 실패함(거부 확인)을 따로 기록한다(계약 8).

**원칙 -- 정본은 topology 무관**: 이 card는 엔진을 바꾸지 않는다. 목록은 이름 종속을 **없애는 것이 아니라 기록**하는 것이고(design §1 "Phase 2는 **목록과 기록**이고 일반 규칙으로의
교체는 Phase 4·7a다"), 각 항목의 교체 Phase가 그 종속을 없앤다. 그래서 담당 Phase는 계획 DF 표의 '담당 Phase'에서 읽고(계약 3), 이름 기반 레일 판정은 새 DF를 만들지 않고 이미
있는 DF-19·DF-26(담당 4)에 묶는다.

## 관찰 가능한 계약

1. **재측정 목록**: `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`(E3 경로 그대로)이 최상위 키 `measured_at`(40자리 소문자 16진 커밋 id),
   `scope`, `method`, `vocabulary`, `totals`, `items`를 가진다. `measured_at` 커밋의 `A/*.py`·`workspaces/run_harness.py` blob이 card base의 것과 같다(엔진이 바뀐 뒤 잰 목록이 아니다).
   '동작을 정함' 항목은 모두 비지 않은 `function`(그 줄을 감싼 최상위 def 이름, 모듈 수준이면 `<module>`)을 가진다(base 목록은 90개가 빈 문자열 -- P10b 레지스트리 함수별 집계의 입력 조건).
   `scope`는 `A/*.py`(HEAD 7개: `audit_current_forced`·`design_report`·`sizing_recipe`·`sky130_lut_sweep`·`stick_diagram`·`topology_library`·`topology_to_markdown`) + `workspaces/run_harness.py`.
2. **담당 Phase(E3)**: 모든 항목이 `phase`를 가지고 값은 닫힌 집합 {`3`, `4`, `5`, `6a`, `6b`, `6c`, `7a`, `7b`, `7c`, `해당 없음`}의 원소다(계획 N6.1 Phase 이름 중 2 뒤의 것 --
   DF-23의 Phase 2 몫은 목록 자체이므로 항목의 교체 Phase가 될 수 없다). `phase == "해당 없음"`인 항목과 `plan_mapping`이 DF 번호가 아닌 항목은 비지 않은 `phase_reason`을 가진다.
   `role == "메시지뿐"`인 항목의 `phase`는 `해당 없음`이다(동작을 정하지 않음).
3. **DF 표와 일치**: `plan_mapping`이 `DF-<번호>`로 시작하는 항목은 그 번호가 계획서 DF 표에 행으로 있고, `phase`가 그 행 '담당 Phase' 열에 적힌 Phase 토큰(`2` 제외) 중 하나다
   (HEAD 실측 행: DF-19 `4`, DF-26 `4`, DF-29 `2, 7a`, DF-30 `7a`, DF-31 `7b`, DF-32 `6b, 6c`, DF-33 `7b`, DF-34 `4, 7b`, DF-23 `2, 4`). 레일 넷 이름 리터럴을 동작 조건으로 쓰는 항목은
   `plan_mapping`이 `DF-19` 또는 `DF-26`이다(design §11-1의 "DF 번호가 없다"는 틀렸다 -- 두 행이 이미 레일 이름 집합 하드코딩을 적고 있다).
4. **총계**: `totals.n_items == len(items)`, `totals.by_role`·`totals.by_phase`·`totals.by_plan_mapping`이 항목에서 센 값과 같다.
5. **참조 문서의 Phase 2 삭제·이동 이름(문서 백로그 B22 (b), 전 범위)**: 이름 집합 N = Phase 2가 지우거나 옮긴 엔진 이름(P5 `2a123ba`·P5b `6612902`·P6 `1c5b920`에서 사라진 최상위
   정의·메서드·모듈 상수와 P5b가 지운 선택 키) -- `converge_with_parasitics`, `slew_rate`, `render_stick_diagram`, `suggest_headroom_stack_groups`, 메서드 호출형 `.fT(`·`.junction_cap(`,
   `_cmrr_telescopic_class_ab`, `_cmrr_telescopic_class_ab_cmfb`, `_psrr_telescopic_class_ab`, `_psrr_telescopic_class_ab_cmfb`, `_cmfb_amp_gain_diode_load`, `_load_telescopic_topology_cached`,
   `_telescopic_class_ab_open_loop_response`, `_telescopic_open_loop_device_names`, `_telescopic_class_ab_open_loop_gains`, `_TELESCOPIC_FIXED_BASE`, 선택 키 `telescopic_class_ab`·`telescopic_class_ab_cmfb`,
   `find_interleaved_symmetric_splits`, `run_regression_case`, `_run_optimize_multistage_case`, `RegressionVerdict`, `_REGRESSION_ENGINES`. 판정 대상 문서 D = `skills/analog-gmid-design/references/**/*.md`,
   `skills/analog-gmid-design/SKILL.md`, `skills/analog-gmid-design/skill-validation-prompt.md`. N의 이름 n(식별자 경계로 대조)이 D의 한 줄에 나오면:
   * n의 정의가 `A/*.py`·`workspaces/run_harness.py`에 있으면(AST, 되살린 경우) 제약 없음.
   * 정의가 `A/tests/tools/<모듈>.py`에만 있으면(이동) 그 줄에 `Phase 2에서`와 `tests/tools/<모듈>.py`가 함께 있다.
   * 정의가 어디에도 없으면(삭제) 그 줄에 `Phase 2에서 삭제`가 있다. 선택 키 두 개는 SR `_CMRR_ESTIMATOR_REGISTRY`·`_PSRR_ESTIMATOR_REGISTRY` 딕셔너리 리터럴의 키(AST)에
     없으면 삭제로 본다(HEAD: 두 레지스트리 키는 `diff_pair_tail` 하나씩 -- P5b 판정 기록).
   줄을 지워도 된다(사용 안내·예제 코드는 지우거나 대체 경로로 고친다). HEAD 실측 대상 줄 19개: `function-selection-map.md` 35·38·80·99, `sky130-worked-example.md` 256·262,
   `stick-diagram-euler-layout.md` 113·215·464·1065·1102·1223, `design-report-spec.md` 92·308, `consistency-map.md` 207·209, `known-incidents.md` 104·125, `SKILL.md` 74.
   (문서 백로그 B22 (b)의 원래 목록 5줄 + 14966행 합류 99행보다 넓다 -- 같은 결함을 Phase 2 삭제·이동 이름 전부로 잰 것이다. 원칙 '원칙은 계약에 전 범위로'.)
6. **범위**: 문서 커밋(순서 1, card base에 포함)과 test 커밋을 합쳐 070cf69 이후 이 card가 바꾼 경로가 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/**`, `docs/02-design/**`,
   `skills/analog-gmid-design/references/**`, `skills/analog-gmid-design/SKILL.md`, `A/tests/contracts/` 아래 새 test 파일뿐이다. `A/*.py`·`workspaces/run_harness.py`·`A/library/**`·레지스트리·
   기존 test는 바뀌지 않는다(E-LIB·E-INST 자명 동일). test 커밋(`old..new^`)만 보면 `A/tests/contracts/` 새 파일뿐이다.
7. **재측정의 정확성(auditor 측정 -- 영구 test가 아니다)**: base에서 (a) 모든 항목의 `file:line` 줄이 `source_line`과 같다(옮겨감·사라짐 0) (b) auditor의 독립 스캔 --
   base library의 소자·넷·회로 이름(`vocabulary` 재계산)과 **정확히 같은** 문자열 상수(AST `Constant`)가 scope 파일에 나오는 (파일, 줄, 값) 전부 -- 가 목록 항목에 빠짐없이 있다
   (c) 그 정확 일치 항목의 `role`이 `method`에 적힌 AST 부모 규칙으로 다시 분류한 값과 같다. 줄 번호 일치를 영구 test로 두지 않는 이유: 이후 엔진 card마다 줄이 움직여 모든 card를
   막는다(P2의 영구 바이트 대조를 P4에서 폐기한 선례 -- 승인 기록 `.ai/approvals/20260930-p4-relocate-test-retire.md`, spec card `20260929-probe-engine-dup`).
8. **거부 확인(auditor 측정)**: 새 test를 오케스트레이터 문서 커밋 **직전** 커밋에서 실행하면 계약 2(`phase` 없음)와 계약 5(표시 없는 19줄) 판정이 실패한다. 결과를 판정 기록에 남긴다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

test-only: code 커밋이 없다(엔진·도구·레지스트리 불변 -- 레지스트리 기록은 분리).
* 모양이 유형을 정한다: design 05 §10-4 표(290행) test-only = "`old..new^`는 첫 부모 사슬이고 전부 `Role: test`(1개 이상), `new`는 `Role: audit` 1개, 병합 없음, T = `new^`, K 없음".
  red-green·equivalence 모양은 ②에서 `Role: code` 1개 이상과 병합 M을 요구하므로 code 커밋이 없는 변경은 test-only 모양만 EL4를 통과한다.
* 같은 논리의 선례 규칙: design 05 §18(557행, `10-test-separation` R2 개정 2026-09-22) "판정 기준 데이터만 바꾸는 게이트 변경 -- `tools/gates/redteam/**`만 바꾸고 code 커밋이 없는 것 -- 은 test-only".
* 승인된 design의 행: design 20 §8 P10 "test-only(문서) | (d) 실측 원자료".
* 증거: 계획 N3.12.3(687행)·N4.2 V2(838행)의 test-only 증거 문장은 TS 단계용("섹션->test 매핑표의 모든 섹션이 변경 후 test에서 PASS")이라 이 card에는 매핑표가 없다. 이 card의 V2는
  그 뜻 그대로 "변경 전 test 집합(기존 test 전부)이 base에서 통과시킨 것을 변경 후에도 모두 PASS + 새 test가 base(문서 커밋 포함)에서 PASS"이고, 여기에 계약 7(재측정 정확성)·계약 8
  (문서 커밋 직전에서 새 test가 실제로 거부) auditor 측정을 더한다. 계획 N3.12.3 test-only 흐름대로 순서 4·5(구현·병합)는 없다.

## oracle 종류와 출처

(d) 실측 원자료·계획서: 계약 3의 기대 Phase는 계획서 DF 표 '담당 Phase' 열(test가 계획서를 읽어 파싱 -- 목록을 쓴 오케스트레이터의 판단을 기대값으로 쓰지 않는다), 계약 2의 닫힌 집합은
계획 N6.1 Phase 이름. 계약 5의 이름 집합 N은 Phase 2 삭제·이동 커밋의 사실(위 세 커밋)이고, '삭제/이동/되살림' 구분은 test가 실행 시점에 AST로 정의 위치를 찾아 정한다.
(a) 구성 입력: 계약 2~5 판정기마다 합성 목록·합성 문서 조각(아래)으로 실제로 거부·통과하는지 자기 점검. 계약 7은 auditor의 독립 스캔(오케스트레이터의 목록 생성기를 쓰지 않는다).

## 거부해야 할 입력

합성 목록: `phase` 없는 항목, 닫힌 집합 밖 값(`2`, `8`, 빈 문자열), `해당 없음`인데 `phase_reason` 없음, `plan_mapping` `DF-30`인데 `phase` `4`, 계획에 없는 `DF-99`, `메시지뿐`인데 `phase` `4`,
`totals.n_items`가 항목 수와 다름, `measured_at`이 40자리 16진이 아님 → 거부. 통과해야 할 것: `DF-34`에 `4`와 `7b` 각각, `신규…`에 `3`과 사유.
합성 문서 줄: 삭제 이름이 표시 없이 나오는 표 행·코드 블록 import 줄, 이동 이름에 `Phase 2에서`만 있고 새 경로가 없는 줄, 식별자 일부로만 겹치는 이름(`slew_rate_limit`) → 앞의 둘은 거부,
마지막은 대상 아님. `Phase 2에서 삭제`가 붙은 줄, `Phase 2에서 tests/tools/interleave_splits.py로 이동`이 붙은 줄 → 통과.

## library 회로 적용 여부

해당 없음(문서·test). library는 목록의 어휘(`vocabulary`) 입력으로만 읽는다. 엔진 불변이라 E-LIB·E-INST는 base와 같다.

## 무동작 판정 입력(무발동 값)

엔진·library·기존 test 전부 -- 판정이 base와 같다. 새 산출물 필드: 목록 항목의 `phase`·`phase_reason`, 최상위 `measured_at`, `totals.by_phase`·`totals.by_plan_mapping`(엔진이 읽지 않는다).

## 재현할 수치

auditor가 독립으로 센다: 재측정 목록의 `totals.n_items`, `by_role`, `by_phase`(값은 오케스트레이터 재측정 뒤 확정 -- 목록 작성자의 수를 옮겨 적지 않는다), 계약 7 (a) 어긋난 줄 0 (b) 빠진
정확 일치 항목 0. 비교용 이전 상태(1e2e243 목록을 HEAD cd64170에 대조 -- 070cf69 때와 같은 값, scratch `p10_df23.py`): 590항목(메시지뿐 324·동작을 정함 266), 동작 항목 줄 일치 13·옮겨감 211·사라짐 42.
계약 5 대상 줄 HEAD 19개 → card 뒤 표시 없는 줄 0.

## 결정 필요 항목

없음. 사용자 결정 2026-09-30 원문 "E1 문구 정정 승인하고 topology.json주석은 보류해." -- library topology.json 주석 필드 정리는 **보류(이 card 범위 밖, 백로그)**. 담당 Phase는 계획 DF 표에서
읽고, DF 밖 항목의 Phase는 아래 원칙 기본안이다(목록 작성 때 항목별 사유로 적는다):
* 레일 넷 이름 리터럴 → `DF-19`/`DF-26`, Phase `4`. 픽스처 넷리스트(SD `folded_cascode_example`(def 6721)·`two_stage_ota_example`(def 6763), 운영 호출 0 -- 레지스트리에 행이 없다) → `신규`,
  Phase `3`(MOD7: `stick_diagram`은 레이아웃만 남는다), 사유 적음. 그 밖의 넷·소자 이름·파일 이름 규약 → `DF-23`, Phase `4`(DF-23 교체 Phase). 특정 회로를 가리키지 않는 규약 문자열이면
  `해당 없음`+사유. 어휘 충돌(역할 라벨·spec 키 -- 넷·소자 이름 아님) → `해당 없음`+사유.
* 목록 생성기는 `mk_tables.py` 선례처럼 같은 폴더에 `mk_df23_inventory.py`로 커밋한다(오케스트레이터 경로, 재측정 재현용 -- 판정 oracle로는 쓰지 않는다).
* design 20 정정(오케스트레이터 문서 커밋, 판정 기준 E3는 그대로): §8 P10 행(194행)의 '`df23_inventory.json` 기준 266건'·'신규 148건'을 "card base 재측정(`measured_at`)"으로,
  '레지스트리 기록'을 "레지스트리 기록은 별도 card(code 경로 -- 아래 행)"로 바꾸고, 그 별도 card 행(P10b `df23-registry-record`, red-green, (d) 목록 총계, 레지스트리)을 §8에 더한다.
  §11-1(230행) "레일 넷 이름 리터럴 63건에 DF 번호가 없다"를 "DF-19·DF-26(담당 4)이 이미 덮는다 -- 목록에서 두 행에 묶는다"로. (P7·P8 행 정정과 같은 사실 정정 -- E3 판정 기준 불변.)

### 분리한 것(이 card 밖)

| 항목 | 위치(HEAD cd64170) | 쓰는 주체(N3.12.2) | 처리 |
|---|---|---|---|
| 레지스트리 DF-23 기록 | `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` | gmid-code-author(603행) | 이 card 병합 뒤 작은 red-green card(레지스트리에 목록 경로·`measured_at`·총계, test는 목록 총계와 대조 -- base에서 기록 없음으로 red). design §8에 행을 더해 추적 |
| 문서 백로그 B22 (a) SR 모듈 docstring | `A/sizing_recipe.py:15`("5. 기생 CJD 반영 반복 -> optimize_multistage()의 cgg 반복") | gmid-code-author(599행) | 엔진 텍스트(`ast.dump`가 바뀜) -- 다음 code card에 동반. 문서 백로그 B22는 이 항목과 아래 test 주석이 남아 열린 채로 둔다 |
| 엔진 텍스트 속 삭제 이름·family | `A/sizing_recipe.py:5015`(`_metric_smallsignal_ratio_db` docstring -- "…를 대체", 이력 문장), `:4737`·`:4743`(`_mna_solve_smallsignal` 예외 메시지의 "telescopic_class_ab MNA 특이행렬" -- 회로 무관 solver인데 삭제된 family 이름 표기, P5b auditor 지적) | gmid-code-author | 위와 같이 code card에 동반. 5015는 이력 문장이라 고치지 않을 수도 있다(그 card에서 판단) |
| test 주석·docstring(14950행 합류분) | `A/tests/unit/test_selftest_sizing_recipe.py:2791`(`_cmrr_telescopic_class_ab docstring` 인용), `:2765`·`:2824`(test docstring의 family 이름) | gmid-test-author(618행) | test 역할 -- 해당 test를 건드리는 다음 test 커밋에 동반 |
| library topology.json 주석 필드 | `current_reuse_telescopic_ota.topology.json` 1250·1281(`_vertical_stack_id_comment`, `suggest_headroom_stack_groups`), 1872(`_metrics_comment`, telescopic family), `nmcnr_amplifier.topology.json:74`(`_settling_slew_comment`, `slew_rate()`) | 오케스트레이터 + 승인 기록(634행 `library/*.topology.json` 조건 '승인 기록') | **사용자 결정 2026-09-30: 보류(백로그)**. E-LIB 입력 파일이다 |
| Phase 2 전부터 낡은 이름 | `run_sizing_pipeline`(SKILL.md:52 등), `load_sizing_targets`·`write_sizing_results`, `block_from_row_widths`, `classify_device_roles`, `verify_symmetry_dispositions` 외 `consistency-map.md` 다수, `detect_extraction_anomalies` 등(scratch `b22_scan.out.txt`) | 오케스트레이터 | 문서 백로그 B22 범위(Phase 2 삭제분) 밖 -- 새 백로그 항목으로 등록, 이 card에 넣지 않는다(card 크기·결함 유입 억제) |

## 작성 전 실측

(재측정 HEAD = gate `master` cd64170, 2026-09-30. 초안 base 070cf69 이후 바뀐 것: SD `save_instance_json` 부근(DF-36), design 05·20, 승인 기록 2개, `.ai/context.md` 4줄 -- 계획서·SR·
references·SKILL.md·library·레지스트리·기존 unit test는 불변. 저장소 읽기 전용, python `C:\Python314\python.exe -B`, 결과는 scratch 파일.)
1. 사실 문장 재측정: scratch `p10_df23.py` HEAD 재실행 → 목록 590항목(324/266), `phase` 키 없음, 동작 항목 줄 일치 13·옮겨감 211·사라짐 42(사라진 함수 `''` 25·`_telescopic_class_ab_open_loop_response` 10·
   `<module>` 5·`_load_telescopic_topology_cached` 1·`suggest_headroom_stack_groups` 1), `A/*.py` 7개 목록 불변(값이 070cf69 때와 같다). `git log --oneline -1 -- …/df23_inventory.json` → acad7c8(측정 `1e2e243`),
   `git rev-list --count 1e2e243..HEAD` → 101(070cf69 기준 93).
   `grep -n "^| DF-" docs/01-plan/features/gain-budget-gmid-sizing.plan.md` → DF-19(929)·DF-26(936) 담당 4, DF-23(933) `2(전수 목록·레지스트리 기록), 4(일반 규칙으로 교체)`, DF-29(939) `2, 7a`, DF-30 `7a`,
   DF-31 `7b`, DF-32 `6b, 6c`, DF-33 `7b`, DF-34 `4, 7b`.
   scratch `p10_phase2_names.py`·`b22_scan.py` HEAD 재실행 → 출력이 070cf69 때와 바이트 동일(P5/P5b/P6 사라진 이름 23개, 참조 문서 대상 줄은 계약 5의 19줄, `fT`는 호출형 `.fT(`만 --
   단어 `fT`는 물리량 표기라 64곳 거짓 양성, `derived_spec`·`lut_conditions_from_npz`는 복원돼 정의 있음).
   분리 표 줄 번호 재확인: SR 15·4737·4743·5015, unit test 2765·2791·2824, topology.json 1250·1281·1872, nmcnr 74 -- 모두 HEAD에서 같다.
   B22 정의: `.ai/context.md` 14943행(원문 위 인용), 합류 14950·14966·14977행. 다른 뜻: history 4002행(§10.3 B22, `diode_vds_window`), SR 567·3425·7412 주석, 레지스트리 77행.
2. 이름 충돌: 새 test `A/tests/contracts/test_df23_inventory.py`·`A/tests/contracts/test_phase2_stale_refs.py`. `ls A/tests/contracts/`에 같은 이름 없음. `grep -rn "glob(" A/tests/` → `*.py`·`probe_*.py`·
   `test_probe_*.py`·`*.topology.json`(HEAD `test_df36_instance_relpath.py:58` 추가 -- library 전용)·`*.md`(tools) 패턴과 겹치지 않음. `*.py` 전수 스캔 test(`test_ts3_no_print_verdicts`, GONE 스캔
   `test_d_delete_dead`·`test_d_delete_telescopic`, `test_d_move_tests` 소비자 검사, `test_ic_markers_match_plan` IC 표식)는 Name·Attribute·import·def와 IC 호출만 센다 -- 새 test는 삭제·이동 이름을
   **문자열 상수로만** 들고(import·호출 금지), 딕셔너리 값으로 두지 않으며, IC 표식이 없다.
3. 원칙의 계약화: 이름 종속은 '기록'이고 교체 Phase가 없앤다 → 계약 2·3(Phase를 DF 표에서 읽음, 레일은 기존 DF-19·26). 작성자≠검증자 → 계약 3의 oracle은 계획서, 계약 7은 auditor 독립 스캔.
   원칙은 계약에 전 범위로 → 계약 5는 문서 백로그 B22 (b)의 5줄이 아니라 Phase 2 삭제·이동 이름 전부(19줄).
4. 쓰기 경로(계획 N3.12.2 표 599-640행, HEAD 확인): 목록·생성기 = 오케스트레이터(626행 `docs/03-analysis/**`, 제외 = 레지스트리), design 정정 = 오케스트레이터(624행 `docs/02-design/**`),
   참조 문서 = 오케스트레이터(640행 `skills/analog-gmid-design/references/**`), `SKILL.md` = 오케스트레이터(638행), `skill-validation-prompt.md` = 오케스트레이터(639행, 이번 대상 줄 없음),
   계약 test = gmid-test-author(618행 `A/tests/**`, 제외 `tests/tools/**`), 계약 7·8 측정과 판정 기록 = auditor(621·622행). 레지스트리 = gmid-code-author(603행, 그래서 분리),
   `library/*.topology.json` = 오케스트레이터 + 승인 기록(634행, 그래서 분리·보류).
5. 계획서 소비자: 지우거나 바꾸는 엔진 이름 없음. 문서에서 고치는 이름(계약 5 N)을 `grep -rn` `docs/01-plan`·`docs/02-design` → 계획·design은 Phase 2 이력·spec card로만 언급(바꾸지 않음). 목록 경로는 E3가 쓰는 경로 그대로.
6. 미배선: 새 def 없음(엔진 불변). 생성기 `mk_df23_inventory.py`는 커밋되는 목록을 만드는 데 쓰인다(재측정 재현 경로).
7. 기존 계약 test: `grep -rni "kcl\|df23\|references/\|function-selection-map" A/tests/contracts/` → 해당 없음(`test_ic5.py:59`는 무관). 참조 문서·목록을 읽는 기존 test 없음, 조정 불필요, V5 없음.
