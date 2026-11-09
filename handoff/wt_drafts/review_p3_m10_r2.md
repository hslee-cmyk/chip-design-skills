# 독립 재검토 r2 -- `draft_p3_m10.spec.md` (20261006-p3-mod10-entry)

검토자: 독립 verifier(작성자 아님, 1차 검토자 `review_p3_m10.md`와도 다름). 2026-10-06.
범위: diff 한정 -- `draft_p3_m10.spec.md` vs `.pre-r2.bak`, `m10_t1_open_items.md` vs `.pre-r2.bak`.
기준: gate `master` **`ae1b588`**(card는 `6c724de`로 적음). `git diff --stat 6c724de ae1b588 -- tools skills workspaces docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` **빈 출력**(차이는 b26pre spec card 1파일뿐), `git diff --stat 2183f2e 6c724de -- (같은 경로)`도 빈 출력 -- card 문장 확인.

**판정: B 0 · S 0 · minor 3 -- S1·S2 해소, m1~m5 반영 확인. card 커밋 가능(minor는 선택).**

## 0. 측정 환경

샌드박스 `C:/g381`(clone `-c core.autocrlf=false --no-local --no-checkout`, origin 제거, hooks 디렉터리에 sample 외 0, detach `ae1b588`, TMP/TEMP `C:/g381/tmp`, cd 없음 -- 하네스는 `importlib`로 절대 경로 로드). 끝에 삭제 확인. 실제 저장소는 `git -C … show/diff`만(쓰기 0, HEAD `ae1b588` 그대로).
저자 키트(`p3kit_m10_t1/`)는 열지 않았다.

## 1. 바뀐 범위 확인

diff hunk는 의도(첫 줄 판 이름, 옮길 범위 근거 (1)~(3), `6c724de` 표기), 계약 6 (c), 계약 10, 거부 입력 R-12~R-14, 결정 필요 M10-1·M10-2·M10-5, 작성 전 실측 머리·1·8·12·13·14(브리프 두 줄)·15뿐이다.
**계약 1~5·6 (a)(b)(d)(e)(f)·7~9·11·12, 신규 시그니처, 판정 유형·oracle·library 절은 바이트 그대로**. open items는 M10-1·M10-5 행과 양식 검사 m4 정정 문단 세 곳만 바뀜.

## 2. S1(계약 6 (c)) -- 해소

문언: 준비(임시 `WORKSPACES_DIR` 아래 `SPECS[key]["report_dir"]`를 base 기록·병합본 test 둘 다에서 미리 만듦), instance.json 존재 단언, 해시 식 전문(`sort_keys=True, ensure_ascii=False, separators=(",", ":")`, `e_inst_p3.py` `h()`와 같음 -- gate 52~53행 확인), 기록 해시 non-null 단언(test) + auditor의 E-INST base `raw_sha256` 대조, 두 회로 stdout에 `FileNotFoundError` 0. 무발동(null = null) 경로가 test 단언과 auditor 대조 양쪽에서 막힌다.

base 하네스(gate `ae1b588`, M1~M9 미병합 -- `run()` 동작은 같음) 직접 재현(`run_harness.run(key)`, `WORKSPACES_DIR`만 임시 디렉터리로 교체):

| 경우 | 결과 |
|---|---|
| `folded_cascode`, report 디렉터리 **안 만듦** | instance.json 없음 → 해시 `null`, stdout `[FAIL] FileNotFoundError: [Errno 2] … folded-cascode-report\folded_cascode.instance.json` |
| `folded_cascode`, **만듦** | instance.json 있음, `[FAIL]` 0, `FileNotFoundError` 0, report.html 없음, 해시 `ef3cd9963d0a80ac6e07ea5909286db1d8e67d8351a355c8aafd7a01fc9bb3f0` = gate `.ai/verification/20260930-b34-grammar-explicit/order7/einst/base_folded_cascode.json` `raw_sha256`, `topology_ref` 저장소 상대 경로(출력 위치 무관) |
| 같은 instance.json, `separators` 없음 | `e690b95d4c9d10075eb9f958b621be737b79f998823c80e293730be80f7e90b5` -- 다름(R-13 성립) |
| `two_stage_ota`, 만듦 | instance·report 없음, `[FAIL] ValueError: 'stage1_out' 그룹의 VDS 합…KVL…`(저장 전 `ValueError`), `FileNotFoundError` 0 -- card 문장과 같음 |

R-12(디렉터리 안 만듦 → 기록 null)는 test의 non-null·존재 단언과 auditor 대조에서, R-13은 auditor 대조에서 거부된다 -- 위 실측과 맞다. 저자의 병합본 pytest 4종(실측 15)은 다시 돌리지 않았다(base 쪽 사실만 재현 요청 범위).

## 3. S2(계약 10) -- 해소. §4 R1 배치는 §0 규칙에 맞다

gate 레지스트리 실측: §3 R0 `### 기타 모듈 (22)` 244행, §4 R1 `### 기타 모듈 (16)` 376행(표 행 16 = 괄호 16), §5 R2 `### 기타 모듈 (1)` 441행(`run` 행 445행), §1 집계 '기타 모듈' 22·16·1·1·1 -- card 숫자·줄 그대로.

판단(§0 규칙 3, design 30 §8 M10 행은 절을 정하지 않음):
* **R0 아님** -- R0는 "수정 없이 그대로 재사용"인데 옮긴 몸체는 `run` 행에 적힌 결함('3단계 분리 없음, θ* print만')을 그대로 가지고, Phase 4가 `instrument`·`activations_out`(CC-7·CC-8)을 더할 함수다.
* **R2 아님** -- R2는 "§12 구조로 대체 예정, 새 호출부를 늘리지 않는다"인데 이 함수가 바로 그 대체 목적지(`run` 행 이관 목적지 `gmid_design_pipeline.run_gmid_design_pi…`, `00-common` §10.1 정본 진입점)이고, Phase 4 계측 도구·이후 호출부가 이것을 불러야 한다. R2로 두면 규칙 자체가 계획과 충돌한다.
* **R1** -- "그 함수를 고친다, 새 함수를 만들지 않는다"는 이후 결함 수정·인자 추가가 이 함수 안에서 일어나야 한다는 계획 의도와 같다. 작성자 근거와 같은 결론.
* `run` 행을 §5 R2에 그대로 두는 것도 맞다(남은 하네스 `run()`은 여전히 '새 호출부를 늘리지 않을' 대상이고 지우지 않으므로 규칙 4 삭제 대상 아님 -- N3.10 '`SPECS`는 하네스에 남는다').

§1 집계 규칙의 기계 검증 가능성: (i) 소절 괄호 = base+1 = 표 행 수, (ii) §1 '기타 모듈' R1 칸 = base+1, 나머지 칸·행 불변 -- base 대비 diff로 auditor가 숫자만 세면 판정된다(R-14가 그 거부 입력). base 값은 계약 10의 '`### 기타 모듈 (16)`'과 실측 1의 '22·16·1·1·1'로 적혀 있다(→ minor n1).

## 4. minor m1~m5 반영

| 항목 | 반영 |
|---|---|
| m1(58 = 근거 아님) | 의도 (2)와 M10-1에 "(ii)(iv)는 처리부까지 옮긴 모양 전제, 처리부 변이는 `not_targeted` + 계약 6 (b) 시나리오 8~10으로 고정", 58 같음은 우연·대안 65로 명기 -- 반영 |
| m2(§10.2-1/§10.2-6) | 의도 (3) "기본안에서도 `run()` except가 삼키는 동안 §10.2-6 불성립, DF-37이 `run()`을 고친다, 대안이면 두 곳" + `run` 행 R2 비고 인용 -- 반영 |
| m3(V4 브리프) | 실측 14에 브리프 문장(assert를 도우미 안에만 두지 말 것, `subprocess.run` 결과 두 필드끼리 비교 금지) + 계약 6 (c) 준비 문장 -- 반영 |
| m4(기존 함수 10 + 신규 1) | 실측 8·12, open items 양식 문단 정정 -- 반영. 내 실측: gate `ae1b588`에서 `interface_card.py --root` exit 0 **기존 함수 10**(`run_harness` 3·`_topology_ref_relpath`·SR 2·SD 2·DR 2) + 신규 시그니처 1행 |
| m5(판 이름) | `6c724de` + 2183f2e 대비 빈 diff 근거 -- 반영(다만 n2) |

## 5. 양식(gate `ae1b588` `tools/gates`)

`role_paths.parse_spec_card(text, expect_id="20261006-p3-mod10-entry")` 예외 없음: `phase` 3, `evidence_type` red-green, `gate_change` no, `approval` [`20260930-30-module-split-design`], 절 11개. `interface_card.py` exit 0, 기존 함수 10 + 신규 1(위).

## 6. minor (선택, 커밋을 막지 않음)

* **n1** -- 계약 10 (i)(ii)는 'base 값 + 1'로만 적었다. "gate `6c724de` 값 16 → 17"을 함께 적고, 실측 13 (ii)(card base 재측정 목록)에 레지스트리 '기타 모듈' 괄호 수·§1 집계 행을 넣으면 auditor가 base 판 값을 한 번 더 대조할 수 있다(M1~M9가 행 수를 바꿀 계획은 없지만 재측정 목록에 없다).
* **n2** -- gate `master`는 지금 `ae1b588`(b26pre spec card 개정 1파일; tools·skills·workspaces·레지스트리 diff 빈 출력 -- 내 확인). 의도 첫 줄·실측 머리의 '이제 `6c724de`'는 실측 13 착수 직전 재확인 때 판 이름만 바꾸면 된다(사실 값 영향 0).
* **n3** -- 계약 10 R1 근거의 인용 "레지스트리 §0 규칙 3 R1 '새 함수를 만들지 말고 이것을 고친다'"는 §4 제목(271행) 문구이고 §0 규칙 3 문구는 "그 함수를 고친다. 새 함수를 만들지 않는다."다. 또 R2가 아닌 이유(이 함수가 R2 `run`의 대체 목적지라 R2면 Phase 4 호출부와 충돌) 한 마디를 더하면 auditor가 분류를 다시 따지지 않는다.

## 7. 정리

샌드박스 `C:/g381` 삭제 확인. 실제 저장소 쓰기 0(`status`는 시작 때와 같음 -- `.bkit/state` 2파일 기존 변경).
