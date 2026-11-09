# 독립 검토 -- `draft_p3_m10.spec.md` (20261006-p3-mod10-entry, red-green)

검토자: 독립 verifier(작성자 아님). 2026-10-06. 대상: `_drafts/draft_p3_m10.spec.md` + `_drafts/m10_t1_open_items.md`(M10 부분).
기준: gate `master` **6c724de**(= 2183f2e + b26pre spec·interface card 문서 2파일 -- 엔진·tools 차이 0), design 30 v8.5 §2.3·§3·§8·D-5·D-15·D-25, 계획 N3.10, `00-common` §10.1·§10.2.
저자 키트(`p3kit_m10_t1/`)는 아래 측정을 다 만든 **뒤에만** 열었다(그 prototype이 report 디렉터리를 만드는지 확인하는 데만 씀).

**판정: B 0 · S 2 · minor 6 -- S 2건을 고친 뒤 card 커밋 가능.** 기본안 M10-1(try 몸체만 옮김)은 타당하고, 핵심 수치는 모두 독립 재현된다.

## 0. 측정 환경(내 사슬)

샌드박스 `C:/g354`(TMP/TEMP `C:/g354/tmp`, clone `-c core.autocrlf=false --no-local`, origin 제거, 빈 hooksPath). 실제 저장소는 `git -C … show/archive`로만 읽었다.
사슬: `6c724de` → FU 대역 `76f6bb7` → T0 W-1 대역 `0045c6b` → G1 시제품 `c8ae862`(`installed 4`) → D0a 대역 `d5c6f4c` → D0b 재생성 `47ce1c6`(one 354·nested 7·nounit 18, plan exit 0)
→ M1~M9 `chain_lean.py`(단위 8·18·82·104·21·11·30·16, card마다 `check` 발견 0) → **M10 base 대역 `1e99f72`**.
내가 만든 M10(저자 생성기 미사용, `kit/m10gen.py`): 기본안 code `754e983`, 처리부까지 옮긴 대안 `a96dbb5`, 내 prototype test `d7ce6bf`(base 위), 병합 `5b429b5`.
(절차 위반 1건 자진 기록: golden 기록 명령 하나에 `cd /c/g354/tmp`를 썼다 -- 샌드박스 안 경로, 영향 없음.)

## 1. M10-1 기본안(try 몸체만 이동, `except Exception`은 `run()`에 남김)

**타당하다(S/B 없음). 다만 근거 서술 두 곳은 고칠 것(minor m1·m2).**

* 사실 재측정(base `1e99f72` = gate와 H 바이트 같음): `run` 422~529, `try` 444, 몸체 445~511, 처리부 512~529, `stem`·`instance_out`·`report_out` 429~431, 정의 모듈 MOD8(`optimize_full_circuit_budget` 1507·`diagnose_sizing_roles_gap` 1424)·MOD9(4이름) -- card 그대로.
* **V6 FAIL 주장은 진짜다.** 내 대안 `a96dbb5`: `source_lint` **FAIL** `broad_except` base 0 → head 2(`gmid_design_pipeline.py` 83·99행 -- 저자 82·98과 한 줄 차이는 내 import 줄 바꿈 탓). 기본안 `754e983` **PASS** `findings` [].
  도구 식(`source_lint.compare` -- (경로, 단위)별 항목 수 증가 = 새 발견, 새 함수는 전부 새것)으로도 이 결과가 나온다. 이동이 아닌 추출이라 G1 이동 제외도 받지 못한다.
* 문언: §2.3 (i) "`try` 몸체부터 옮긴다". 기본안 읽기를 받칠 수 있다('try 문'이 아니라 '몸체').
  **그러나 문언은 결정적이지 않다**: '부터'는 시작점만 말하고, 같은 절 (ii)는 "실패 경로 회로 하나(…`except`·진단 분기 6개)"를 새 test가 죽일 V3 대상으로 셌으며, (iv)의 '약 58' = 71 − 13(준비 문장)으로 처리부를 포함한 모양이다(open items X-2가 이미 인정).
  기본안에서 진입점 대상 58이 design 추정 58과 같은 것은 **우연의 일치**다(진입점에 새로 생긴 준비 대입 6문장이 처리부 변이 수를 대신 채운다 -- 내 정적 계수: 처리부까지 옮기면 65). → **m1**: card 132~133행의 "대상 변이 수는 … design 추정(약 58)과 같다"를 근거처럼 쓰지 말고, "(ii)(iv)는 처리부까지 옮긴 모양을 전제했다 -- 기본안은 처리부 변이를 V3 대상 밖(`run()` not_targeted)으로 두고 분기 계약 test(계약 6 (b) 시나리오 8~10)로 동작을 고정한다"고 적을 것.
* `00-common` §10.2-6("진입점 호출 전체를 잡는다"): 진입점이 예외를 올려야 성립한다는 읽기는 맞다. **다만 §10.2-1은 도구가 하네스 `run(circuit, output_dir=…, instrument=…)`를 부른다고 적는다** -- 기본안에서도 `run()`의 `except Exception`이 예외를 삼키므로 Phase 4(DF-37)가 `run()` 쪽을 고쳐야 §10.2-6이 실제로 성립한다. 기본안은 "고칠 곳이 `run()` 한 곳으로 남는다", 대안은 "엔진 파일까지 두 곳"이라는 점에서 낫다. → **m2**: 근거 (2)를 이 정확한 모양으로 고쳐 쓸 것(지금 문장은 기본안이면 §10.2-6이 성립하는 것처럼 읽힌다). 레지스트리 `run` 행 비고도 "`except Exception`(:507)으로 실패도 exit 0"을 R2 결함으로 적어 두었다 -- 결함을 엔진 파일로 옮기지 않는 쪽이 맞다는 보강 근거.
* 사용자 질문 아님에 동의(기준 약화 없음, design 승인 문언 안의 선택, 기본안만 V6를 승인 없이 통과).

## 2. 계약의 검증 가능성·oracle 독립·V4 규칙 충돌

* 계약 2~5·10~12는 AST·도구 출력으로 auditor가 블랙박스로 판정 가능(내가 전부 같은 식으로 쟀다: 최상위 = Import·ImportFrom·ImportFrom·FunctionDef, 진입점 print 16·if 6·for 2·try 1, H 미사용 엔진 import 0 -- 내 생성기는 `sizing_recipe` 4이름만 남김).
* 계약 6 oracle: (a)(d)(e)(f)는 구성, (b)(c)는 base 하네스 기록 -- 피검(진입점) 호출 없이 만들어진다. 독립 OK.
* **V4 규칙 충돌 없음**(gate `test_lint.py` 읽고 내 prototype으로 실측): 규칙 (1)은 판정 문장 **양쪽에 같은 피검 호출 키**가 있을 때만 걸린다 -- 어느 계약도 같은 출력의 두 필드끼리 비교하라고 요구하지 않는다(모두 기록·구성값과 비교). 규칙 (4)(test 함수 안 assert 0)도 계약이 강제하지 않는다.
  관찰(minor m3): `_callee`가 속성 이름만 보므로 피검 `run_harness:run` 때문에 `subprocess.run(...)`(계약 6 (f) 새 프로세스 test)이 피검 호출로 잡힌다 -- 내 prototype에서 (2) **UNJUDGED 2**(FAIL 아님). 저자 실측 'UNJUDGED 3'과 같은 원인으로 보인다. test-author 브리프에 "공용 검사 도우미 안에만 assert를 두지 말 것(규칙 (4)), `subprocess.run` 결과의 두 필드끼리 비교하지 말 것(규칙 (1) 오탐 위험)" 한 줄을 넣으면 안전하다.

### S1 -- 계약 6 (c)가 '실패 경로끼리 같음'으로 통과할 수 있다(report 디렉터리)

하네스는 `os.path.join(WORKSPACES_DIR, cfg["report_dir"])`를 **만들지 않는다**(`save_instance_json`도 만들지 않음). 내 첫 golden 기록에서 `WORKSPACES_DIR`만 임시 디렉터리로 바꾸자 `folded_cascode`가
`[FAIL] FileNotFoundError: …/folded-cascode-report/folded_cascode.instance.json`로 끝나 instance.json이 없었다(해시 `None`). test-author가 같은 실수를 base 기록과 병합본 test 양쪽에서 하면
"해시 None = None·stdout 같음"으로 **계약 6 (c)가 PASS하면서 진입점의 instance 저장·이후 분기를 전혀 대조하지 않는다**(저자 prototype은 `os.makedirs(...report_dir)`를 해서 이 문제를 안 겪었지만, test-author는 그 키트를 받지 않는다).
고칠 것: 계약 6 (c)에 "임시 `WORKSPACES_DIR` 아래 `cfg["report_dir"]`를 미리 만든다"와 "`folded_cascode` 기록의 instance 해시는 null이 아니며 auditor가 E-INST base `raw_sha256`(같은 정의)과 같은지 대조한다"를 넣는다(무발동 오판 방지 -- 메모리 '게이트는 실제로 거부하는지 먼저').

### S2 -- 계약 10의 레지스트리 표 위치가 틀렸고 §1 집계가 빠졌다

계약 10은 "§4 '기타 모듈' 표"라고 쓰지만 base 레지스트리에서 §4는 `R1`(`### 기타 모듈 (16)`)이고, card가 인용하는 `run` 행이 있는 '기타 모듈 (1)'은 **§5 `R2`**다(작성 전 실측 1의 "§4 '기타 모듈 (1)'"도 같은 오기). 새 행의 분류 절(R0/R1/R2)을 code-author가 정할 수 없고 auditor의 "소절 제목 괄호 수 = 표 행 수"도 어느 소절인지 정해지지 않는다.
또 `## 1. 집계` 표의 '기타 모듈' 행(22·16·1·1·1)이 그 절 행 수와 맞아야 하는데 계약에 없다(`reg_check`는 §7 D 열만 본다 -- 기계 검사가 못 잡는 stale 수).
고칠 것: 절을 하나로 못박고(예: 새 진입점 = R0 또는 R1 중 하나, 근거 한 줄) §1 집계 해당 칸 갱신을 계약에 넣는다.
(R-9 자체는 재현됨: §4 R1 표에 행을 넣어 목적지 `gmid_design_pipeline` → `plan` exit 0·일곱 0·`A-0`; `theta_search` → exit 1·`reg_mismatch` 1 `registry: theta_search.py, assigned: gmid_design_pipeline.py`. 행 없이도 일곱 0, 사상 차이는 새 단위 1개뿐.)

## 3. 핵심 수치 재측정(내 사슬·내 구현)

| 항목 | card | 내 측정 | 판정 |
|---|---|---|---|
| E-INST `folded_cascode` | 다른 키 `engine_origin`만, `ef3cd996…` | 다른 키 `engine_origin`만, `raw_sha256` `ef3cd9963d0a…` 양쪽 같음, head origin에 `gmid_design_pipeline` 포함·전부 iso 안, stdout 바이트 같음 | 일치 |
| E-INST 파일럿 | 같음, `2fc426d9…` | 같음(`2fc426d9ef3a…`), stdout `elapsed` 가림 뒤 같음(바이트는 다름) | 일치 |
| E-LIB | JSON 전체 같음, `1d2e3bf6…` | 전체 같음, `1d2e3bf6acf7…` | 일치 |
| IMPORT-ANY | base 13 → 14, failed 0 | base `tried=13 expected=13 failed=0` → `tried=14 expected=14 failed=0` (cd 없이 `cwd=` 하위 프로세스로 같은 식) | 일치 |
| import_layering | 발견 2 그대로, `present` 10 | 발견 2(MOD7→MOD9·순환) 그대로, `gmid_design_pipeline` = 10 | 일치 |
| `check --card gmid_design_pipeline.py` | `order` 0 | `order` 0(발견은 `changed` 2 -- 추출이라 당연) | 일치 |
| V6 / V7 | PASS [] / PASS new_defs [진입점] | 같음(대안은 V6 FAIL 0→2) | 일치 |
| V3 정적 대상 | 진입점 58(48·8·1·1) + `run` 4(not_targeted 14, deleted 12); 대안 65+3(8) | **정확히 같음** | 일치 |
| V3 생존(표본) | 62/62 죽음 | 내 prototype test 파일만으로 62 변이 전부 실행: **62 killed, 생존 0**, 변이당 평균 4.6 s(최대 6.9 s) | 일치(전체 4,939 s V3는 재실행 안 함 -- 표본 = 전수 변이 + 새 test만) |
| red/green | 수집 오류 / 전부 PASS | base+test: `ModuleNotFoundError: No module named 'gmid_design_pipeline'` 수집 오류, 병합본 20 passed(71 s) | 일치 |

PT3 전체는 재실행하지 않았다(시간; 판정 영향 없는 관찰 수치).

## 4. 기대값 `.py` vs `.json`(V5)

gate `weakening_diff.py`: test 분류(`assets/tests/**`, `tests/tools` 제외)의 비-`.py` 파일은 내용과 무관하게 '무조건 승인 필요'. 실측: 내 병합본(golden = `m10_golden.py`) **PASS** `diff_paths` []; 같은 위치에 `m10_golden.json` 추가(R-11) → **FAIL** `무조건 승인 필요`. 새 `.py`는 base 없음이라 발견 0. card 주장 맞음.
(관찰: MOD10은 `assets/` 최상위 `.py`라 V5의 `__main__` 블록 비교 대상이지만 `__main__`이 없어 무관.)

## 5. V4 두 번 실행 요구

gate interface_card로 card를 생성하면 **base(`1e99f72`)에서 기존 함수 10개**(run_harness 3·`instance_report_builder` 5(`_topology_ref_relpath` 포함)·`sizing_layout_convergence` 2), 병합본에서는 진입점이 더해져 11.
`--interface-card` 한 번: **ERROR** `git show <head>:skills/analog-gmid-design/assets/run_harness.py` 없음 -- 재현. A 피검 8(신규 시그니처 표의 진입점 포함) `--subject` → PASS(NO-SUBJECT 7), `--module-dir workspaces --subject run_harness:{run,canonical_spec,derived_spec}` → PASS(NO-SUBJECT 5·UNJUDGED 2). 두 번 실행 요구는 맞다.
→ **m4**: open items·작성 전 실측 8의 '기존 함수 11'은 병합본 기준이다. 실제 interface card는 순서 0(base)에서 생성되므로 **10 + 신규 시그니처 1**로 적을 것(`read_card_symbols`가 두 표를 다 읽어 V4 피검 집합은 같다).

## 6. 거부 입력 표 표본 4건(내 병합본 위에 하나씩 커밋)

| ID | 결과 | 판정 |
|---|---|---|
| R-3(하네스 옛 몸체 유지) | 배선 test 4 FAIL(4키) | 거부됨 |
| R-5(MOD10 임계값 리터럴 1.5) | `test_thresholds_from_spec` 1 FAIL, 나머지 17 통과 | 거부됨 -- card와 같은 모양 |
| R-8(try 전체 이동 = 대안) | V6 FAIL `broad_except` + 실제 회로 제외 3 FAIL(예외 전파 + 진단 시나리오 2 -- 진단이 진입점 import라 하네스 속성 교체가 안 먹음) | 거부됨 |
| R-11(`.json` 기록) | V5 FAIL | 거부됨 |
| (추가) R-9 | 위 S2 괄호 | 거부됨 |

## 7. 양식(gate 6c724de `git archive`)

* `role_paths.parse_spec_card(text, expect_id="20261006-p3-mod10-entry")`: 예외 없음, `phase` 3·`evidence_type` red-green·`gate_change` no·`approval` [`20260930-30-module-split-design`], 절 11개.
* `interface_card.py`: exit 0 -- base 10개 / 병합본 11개(위 5), 신규 시그니처 표 1행.

## 8. 그 밖의 minor

* **m5** -- 의도·작성 전 실측의 기준 판이 `2183f2e`로 적혀 있다. gate `master`는 이제 `6c724de`(b26pre 문서 2파일만 추가, 엔진·tools·레지스트리 차이 0 -- `git diff --stat` 확인). 착수 전 재확인(작성 전 실측 13)에서 판 이름만 바꾸면 된다.
* **m6** -- X-1(D0a `--allow-changed`) 재현: 대역 `move_plan_sim` `check --allow-changed run…::run …::run_gmid_design_pipeline` → `lost` 1(`run_harness.py::run`) + `rebind` 1(`run_gmid_design_pipeline` unbound → `gmid_design_pipeline`)로 FAIL. open items 처리 방향(D0a 문언 정정, 기준 변경 아님)에 동의 -- M10 card가 이것에 기대지 않는다는 서술도 맞다.
* 계약 6 (c) 해시는 '키 정렬 JSON sha256, E-INST `raw_sha256`과 같은 정의'라고 했는데 E-INST 정의는 `separators=(",", ":")`·`ensure_ascii=False`까지 포함한다(내 prototype은 separators를 안 써 다른 값이 나왔다). S1을 고칠 때 정의를 그대로 옮겨 적을 것.

## 9. 정리

샌드박스 `C:/g354` 전체 삭제(작업 끝). 실제 저장소 쓰기 0.
