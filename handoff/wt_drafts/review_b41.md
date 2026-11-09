# 독립 검토: B41 scope_note test card `20261002-b41-scope-note-test`

검토 대상: `_drafts/draft_b41_scope_note.spec.md`(spec card 초안), `_drafts/b41_briefs.md`(착수 키트). 검토자는 두 문서의 작성자가 아니다.
측정 판: gate `master` `4a286f0`(실제 저장소 HEAD = gate/master = `4a286f0fad4f…`). 2026-10-02.
측정 장소: 격리 복제본 `C:/g239/repo`(`clone --no-hardlinks`, `core.autocrlf=false`, origin 제거), 게이트 사본 `C:/g239/gate`(`git archive 4a286f0 tools/gates`), TMP·TEMP = `C:/g239/tmp`.
시제품 test는 **이 검토자가 card 문장만 보고 따로 썼다**(작성자 시제품 `C:/g232`·`b41_kit`은 보지 않음). 측정 뒤 `C:/g239`만 삭제, 실제 저장소 `status --porcelain`·`reflog -5`가 시작과 같음을 확인.

## 판정

**B(막는 것) 0, S(커밋 전 고칠 것) 1, minor 5.** 자리(Phase 4, #2 앞)는 원칙에 맞고 바꿀 이유가 없다. card 수치는 모두 독립 재현됐다.
S1을 고치면 card 커밋 가능(착수 조건 1~5는 Phase 3 DoD 뒤에 확인).

## 1. 독립 재측정 결과

| 항목 | card 값 | 재측정 | 일치 |
|---|---|---|---|
| 새 test 수·base PASS | `1 + 4 × 9` = 37 passed | 37 passed(4.5~5.1초) | O |
| 기존 대표 test(`test_df36_instance_relpath`·`test_ic3`·`test_s088`) | 42 passed | 42 passed | O |
| M-a(분기 삭제) / M-b(본문 → pass) | 18 / 18 failed | 18 / 18 failed, 기존 test 42 passed(생존) | O |
| H1 첫 줄만 / H2 strip | 9 / 9 | 9 / 9, 기존 생존 | O |
| H3 무조건 씀 | 27 | 27, 기존 생존 | O |
| H4 floorplan 아래 / H5 coverage에도 | 18 / 9 | 18 / 9, 기존 생존 | O |
| H6 이전 파일 값 병합 | 9 | 9, 기존 생존 | O |
| P1·P2 indent 3·1 / P3 ensure_ascii=True / P4 `in` 조건 | 37 passed | 37 passed, 기존 42 passed | O |
| P5 sort_keys=True | 새 37 passed, 기존 1 failed | 새 37 passed, 기존 1 failed / 41 passed | O |
| `bind_hash(save_instance_json)` | `4a96ecf0…2ceee` | `4a96ecf0e82205e0828ea62f88e187b83a1096d557a97ae0b410b9f3cce2ceee` | O |
| 도구 변이 수(그 def) | 14 | 14 | O |
| 참고: 나머지 도구 변이 10개 중 새 test가 죽이는 수 | 8(생존 `body[5]`·`body[5].body[0]`) | 8, 생존 동일. indent ±1 2개는 새 test 통과(의도대로) | O |
| V3(이 card) | PASS, targets [], mutants 0 | `{"verdict":"PASS","targets":[],"mutants":0,"exempt_ignored":[]}` | O |
| V4 `test_lint` | PASS, `NO-SUBJECT` 정보 줄뿐 | PASS, findings 7개 전부 rule (2) `NO-SUBJECT`(내 시제품 기준) | O |
| V5 `weakening_diff` | PASS, findings [], approved false | PASS, findings [], approved false | O |
| V6 `source_lint` / V7 `reachability` | PASS targets [] / new_defs [] | PASS / PASS(new_defs [], unreached []) | O |
| interface card | 2행(`stick_diagram.save_instance_json`·`run_topology_pipeline`), 신규 0 | "기존 함수 2개", 2행 그대로, 신규 시그니처 0행 | O |
| `parse_spec_card` | phase `4`, test-only, no, approval 1개, 본문 절 11 | 같음(절 11개: 의도 … 작성 전 실측) | O |
| 모의 뒤 card V3 (i) test 있음 | FAIL, 15/13, 생존 indent 2개 | FAIL, mutants 15, killed 13, 생존 `const±:body[7].body[0].value.keywords[0].value` 2개, `exempt_ignored` = C8 `stmt_delete:body[2]` unbound | O |
| 모의 뒤 card V3 (ii) test 없음 | FAIL, killed 11, 생존 4 | FAIL, mutants 15, killed 11, 생존 `stmt_delete:body[3]`·`body[3].body[0]` + indent 2개, `exempt_ignored` 같음 | O |
| 빈 문자열·경계값 | `""`·`None`·`0` 없음, `"  "`·`["x"]` 그대로 | 9회로 모두 같음. 더해 `False` → 없음, `"a"` → 씀 | O |
| library 9회로 PR에 `scope_note` 키 | 0 | 0(계약 2 전제 assert가 9회로 PASS) | O |
| `git diff --stat 36e170e 4a286f0 -- stick_diagram.py tools/gates` | 0 | 빈 출력 | O |
| 줄 번호(8973 def, 8975~8977, 8985~8987, 9006~9007, 9023~9024, 8410), design 10 235행, `run_harness.py` 42·492행, `test_ic3.py` 39·44·77행, `.ai/context.md` 15025행 | — | 모두 일치 | O |

### 1.1 모의 뒤 card 측정 조건

모의 card = 분기 두 줄을 `_scope_note = pipeline_result.get("scope_note")` / `if _scope_note:` / `data["scope_note"] = _scope_note` 세 줄로 바꾼 커밋(검토자가 card 문장대로 따로 만듦). base 판(`4a286f0`) `mutate_changed.py`, `--gmid-phase=4 --gmid-strict=`, (i) base = `4a286f0` + 검토자 시제품 test 커밋, (ii) base = `4a286f0`. 두 실행 동시 약 25분.
이 card의 효과(뒤 card에서 `scope_note` 분기 생존 2 → 0)가 재현됐다. 범위 정책 card 도구로 indent 2개가 대상 밖이 되는지는 검토자도 측정하지 않았다(그 도구가 gate에 없다 -- card의 '손 분류' 표기 그대로 유효).

## 2. 탐침별 판단

### 2.1 자리(Phase 4, #2 앞)는 원칙적인가 -- 예

* **N6.1 phase 규칙**: card `phase`는 병합 시점의 진행 Phase다(계획 N6.1 Phase 4 행 "먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase"). Phase 4 첫 card로 병합하면 `4`가 맞고 `read_plan_tables` `phase_order`에 `4`가 있다.
  merge gate는 phase와 evidence_type의 짝을 검사하지 않는다(`merge_gate.py`의 evidence_type 검사는 판정 기록과 spec card 일치·test-only 모양뿐 -- 1132·1171·1179·1200행).
* **앞에 두면(Phase 3 전·중) 생기는 일** -- card 근거 (1)을 Phase 3 design 30 원문으로 확인했다:
  * design 30 95~110행: `save_instance_json` 계열은 MOD9로 가고, SD의 MOD9 재수출은 **M9~F2 임시**이며 F2가 지운다. 지울 조건은 "그 이름을 SD에서 읽는 추적 파일을 F1이 전부 목적 모듈로 바꾼 뒤"(D-26, E3b). 즉 Phase 3 전에 `from stick_diagram import save_instance_json` test를 더하면 **F1 범위(추적 import 86개 집계, 592행)와 E3b 대상이 하나 늘고** D0b 원자료를 다시 재야 한다.
  * 519행: D0b 병합 뒤 F2까지 엔진 파일·`tools/gates/**`를 바꾸는 Phase 3 밖 card를 병합하지 않는다(D-27). test-only card 자체는 이 동결에 걸리지 않지만 위의 F1 영향은 그대로다.
  * 확정 순서(사용자 지정)에 끼우면 순서 변경 = 사용자 몫. 원칙 기본안으로 정할 수 없다.
* **뒤에 두면 잃는 것**: card 근거 (2)를 확인했다 -- 확정 순서·Phase 3 card 중 `save_instance_json` 본문을 바꾸는 card는 없다(Phase 3은 MOVE-AST로 본문 불변을 강제, design 30 234행 F2). Phase 4 card 중 그 def를 바꾸는 첫 card 전이면 되므로 "Phase 4 첫 card"는 가장 이른 무비용 자리다. #2(D-1~D-4 삭제)·TS4와 순서 의존이 없다(B41 test는 `save_instance_json`·`run_topology_pipeline`만 부른다). 그래서 #2 앞에 두는 것은 근거 (2)를 넉넉히 만족하는 기본안이고, 착수 조건 3(#2가 먼저 병합됐으면 자리 문장만 고치고 진행)이 순서 실수를 무해하게 한다.
* 판정: **원칙에 맞음. 자리를 바꿀 B 결함 없음.**

### 2.2 계약 0~4는 test-first로 실행 가능하고 과적합이 아닌가 -- 예

* 검토자가 card '공통 입력'과 계약 문장만으로 test를 쓸 수 있었고(엔진 소스 열람 없이 interface card 2행 + library JSON의 `netlist[].name`만 사용), base에서 37 passed였다. test-author 브리프의 열람 금지 범위로 충분히 쓸 수 있다.
* **거짓 기준값 없음**: 기대값은 test가 만든 `NOTE(n)`, '키 없음', 그리고 계약 3의 두 출력 관계뿐이다. 피검 출력으로 만든 고정값·해시·바이트 비교가 없다. 빈 문자열처럼 선언과 어긋나 보이는 현재 동작을 계약에서 뺐고(P4가 통과해야 함을 auditor가 확인), 바이트 형식도 뺐다(P1·P2·P3·P5 통과).
* **과적합 점검**: 계약 3(정확히 그 키 하나만 더함)은 앞으로 `scope_note`에서 파생 필드(예: `partial: true`)를 더하는 변경을 막는다. 이것은 docstring 첫 단락 "손대지 않고 그대로 옮겨 쓴다"와 같은 뜻이라 과적합이 아니라 선언 고정이다 -- 그런 변경은 card로 계약을 고쳐야 한다(정보).
  계약 2의 전제 assert(`"scope_note" not in PR-only`)는 `run_topology_pipeline`이 뒤에 그 키를 내면 skip이 아니라 FAIL로 드러난다(조용한 우회 없음).
* 회로·소자 이름이 test에 없고 library 전수(`_` 머리 제외)라 topology 무관이다.

### 2.3 추적 instance.json 수 6 -- 틀림(S1)

`git ls-files '*.instance.json'` = **12개**: `workspaces/**` 6(current_reuse 1, folded 1, nmcnr 1, two-stage-ota 3) + `.ai/verification/20260930-df36-instance-relpath/einst/` 4 + `.ai/verification/20260930-p9-kcl-edges/einst/` 2. 12개 모두 `scope_note` 0건이라 결론(운영 산출물에 키 없음)은 그대로다.
card '의도' 공백 절 "추적 instance.json 6개에도 없다"와 작성 전 실측 1 "추적 `*.instance.json`은 6개다(… `two-stage-ota-report`에 3개)"는 **workspaces 범위로 한정**하거나 12개(6 + 판정 기록 einst 6)로 고친다.

### 2.4 빈 문자열 동작(B41a) -- 문면과 어긋나 보이지만 결함 확정은 아님

* docstring: "`scope_note`(str)를 선택적으로 넣으면 그대로 옮겨 쓴다". 코드: `if pipeline_result.get("scope_note"):`(참거짓 판정).
* 실측(9회로 같음): `""`·`None`·`0`·`False` → 키 없음, `"  "`(공백만)·`["x"]`·`"a"` → 그대로 씀.
* 해석: (i) `""`은 str인데 버린다 -- 문면 그대로 읽으면 어긋남. 그러나 '선택적으로 넣으면'을 '내용이 있으면'으로 읽을 여지도 있다. 문제는 **공백만인 문자열은 쓰면서 빈 문자열은 버리는 비일관**이다. (ii) "(str)"라 선언하면서 비 str를 거부하지 않는다(조용한 수용 -- 조용한 기본값 금지 원칙과 같은 종류의 냄새).
* 운영 경로(`run_harness.py` 492행)는 키를 넣지 않아 지금 영향 0. 그래서 **이 card의 계약에서 뺀 것은 옳고**(거짓 기준값 금지), 의도 확인 뒤 별도 red-green card가 맞다. 백로그 B41a에 (ii) 비 str 수용도 함께 적었다.

### 2.5 해시 없는 C8 원소 메모 -- 정확함, 단 Phase 3 뒤에는 모양이 바뀜(minor m4)

* `mutate_changed.approved_index`/`exempt_decision`: `@해시`가 없는 원소는 `unbound`로 분류돼 **면제되지 않고** 같은 id의 변이가 나올 때만 `exempt_ignored`에 이유와 함께 보고된다. 모의 (i)에서 C8 `stick_diagram:save_instance_json:stmt_delete:body[2]`가 `unbound`로 나왔고, 그 경로는 모의 head에서 `_scope_note = …`(다른 문장)를 가리킨다 -- card 메모 그대로 재현.
* 다만 Phase 3 뒤에는 정의 모듈이 MOD9로 바뀌어 변이 id 접두가 `instance_report_builder:`가 되므로 C8 원소(`stick_diagram:` 접두)는 **어떤 변이 id와도 겹치지 않고 `exempt_ignored`에도 나오지 않는다**. card의 "무관한 문장 id와 겹칠 수 있다는 실례"는 Phase 3 전 판에서의 관찰임을 한 줄 덧붙이면 좋다(판정 영향 없음).

## 3. 발견 목록

| 등급 | 위치 | 내용 | 권고 |
|---|---|---|---|
| **S1** | card '의도' 공백 절, 작성 전 실측 1 | 추적 `*.instance.json` = 6이라 적었으나 실측 12(workspaces 6 + `.ai/verification` einst 6). 결론(키 0)은 불변 | "workspaces 추적 instance.json 6개(+ 판정 기록 einst 6개, 모두 키 없음)"로 고친다 |
| m1 | card '판정 유형 근거' | 계획 N6.1 Phase 4 행의 판정 유형 열은 `red-green`이고 Phase 1·2 행처럼 test-only 예외를 열거하지 않는다. 게이트는 검사하지 않고 선례(`20261001-topology-md-sync`·`probe-promote-*`, phase 2 행에 열거 없음)가 있으니 막지 않는다 | 근거 절에 "N6.1 Phase 4 판정 유형 열은 red-green -- 백로그 test-only card는 선례 md-sync(phase 2)처럼 열 밖, 게이트 무검사" 한 줄 |
| m2 | card 공통 입력 `NOTE(n)` 괄호 | "실제 운영 `scope_note` 문장 모양 -- REPORT_DATA 1682·1895행"이라 했으나 그 두 문장은 ASCII 한 줄이고 `--`·괄호·슬래시만 있다(콜론·비 ASCII·줄바꿈 없음). 또 REPORT_DATA는 instance.json이 아니라 보고서 데이터다 | "`--`·괄호·슬래시 = 운영 문장 모양, 비 ASCII·콜론·줄바꿈·앞뒤 공백 = '그대로' 경계용으로 test가 더함"으로 출처를 나눠 적는다 |
| m3 | card '재현할 수치' (C)·작성 전 실측 P | (C) 모의 수치는 Phase 3 전 판(`stick_diagram`)의 참고값인데 P 목록에 (C)가 없다 | P에 "(C)는 참고 -- 재측정 안 해도 됨" 또는 대상에 넣을지 한 줄 |
| m4 | card 작성 전 실측 끝 '모의 결과' 문단 | 위 2.5 -- C8 원소 겹침 실례는 Phase 3 전 판에서만 성립 | 한 줄 덧붙임 |
| m5 | `b41_briefs.md` §0.1-1 | design 40 §1.4 문장 정정 문안이 "B41 scope_note 몫 = card, indent 몫 = 첫 card의 승인"뿐 -- 빈 문자열 B41a 언급 없음 | 반영 시 B41a 포함(이번 Part 2에서 그렇게 반영함) |

## 4. 자리 판정이 Part 2에 주는 영향

B 결함이 없어 자리는 card 기본안(Phase 4 첫 card, #2 앞) 그대로 design 40 초안에 반영했다(v0.9.10). N6.1 정정 문구(§9-9 '#2 → TS4 → …')에는 B41을 넣지 않았다 -- N6.1 Phase 4 범위 열의 항목이 아닌 백로그 test-only card이기 때문(m1과 같은 근거).

## 5. 측정 위생

* 실제 저장소: `git -C` 읽기만(`status --porcelain`·`reflog -5`·`rev-parse`·`archive`). 쓰기·상태 변경 git 0. 시작/끝 `status`·`reflog` 비교 = 같음.
* 스크립트(격리 복제본 안, 삭제됨): 변이 행렬 `mut.py`(손 변이 13개 + 원본 복원 확인 `restored=True`), 도구 변이 `toolmut.py`(`mutate_changed.mutants`·`_replace_def` 사용, 복원 확인), 경계값 `empty.py`, 모의 card 생성 `mock.py`.
