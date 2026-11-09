# B33 spec card 개정 기록 (`draft_b33.spec.md`, 2026-10-01)

입력: 독립 검토 `_drafts/review_b33.md`(blocking B1~B3, should-fix S1~S6, minor 1~5). 개정 전 사본 `_drafts/draft_b33.v1.spec.md`.
측정: 저장소 HEAD `7535799` 읽기 전용. scratch `C:/g64`에 저장소 복제본 두 벌(`base` = HEAD 그대로, `head` = HEAD + 시제품 `reachability.py`)을 만들고 그 안에서
실제 `run_all.py`·도구 CLI·`build_graph`를 돌렸다(TMP/TEMP도 `C:/g64/tmp`). 시제품·측정 스크립트는 `_drafts/b33_scripts/`. **아래 수치는 작성자 측정이고 판정 기록 수치가 아니다**
(auditor가 다시 잰다). 시제품은 test-author·code-author 산출물이 아니다(작성자≠검증자 -- card 문장에서만 test를 쓴다).

## 1. 검토 지적 처리

| 지적 | 처리 | card 위치 |
|---|---|---|
| **B1** `super().__init__` 속성 폴백 | 반영. R2' "dunder 속성(`x.__y__`·`M.__y__`)은 같은 이름 전역 폴백 없음" + `super().__d__` → 기반 클래스의 `__d__`(검토가 '선택'으로 둔 것을 채택 -- 없으면 `ctor-super-chain`이 거짓 FAIL, HEAD 비용 0). 거부 단계 `ctor-super-leak`, 계약 4 문장 추가 | 의도 4·R2·R2', 계약 3·4·9, 표 |
| **B2** 재수출 폴백이 그래프 밖 모듈로 | 반영. M·X는 그래프 안 모듈일 때만, 재수출은 "M 파일의 `from X import NAME`을 따라감". 거부 단계 `registry-external-attr` | R1, 계약 1, 표 |
| **B3** 해석 형식 미고정 | 반영. 계약 1에 "바인딩으로 가는 간선은 이 네 형식뿐" + 음성 목록, R2에 같은 문장. 거부 단계 `registry-attr-collision`·`registry-str-collision` | R1·R2, 계약 1, 표 |
| **S1** 바인딩 값 안 문자열 | 반영(권고 채택). 바인딩 값은 이름·속성·생성자 참조만, 문자열 상수 제외(함수 몸체 str 규칙은 그대로). 거부 단계 `registry-name-strings`. V3 증가 2.35배 → 1.31배 | R1, 계약 1·6, 비용 문단, 승인 범위 |
| **S2** 함수 지역 이름 | 반영(규칙). 거부 단계 `registry-local-shadow`(검토 권고안 -- known_limit 아님) | R1, 계약 1 |
| **S3** 같은 이름 다른 모듈 바인딩 | B2 수정(import 추적)으로 해결. 거부 단계 `registry-reexport-other` | 계약 1, 표 |
| **S4** 계약 12 대상 | 반영. (i) `20260930-restore-plan-functions`(실제 도구 PASS, 32/32) 두 도구 실행 + `"exit": "timeout"` 건수, (ii) 정적 인벤토리 비교(과거 V3 대상 + B26-1·B34 대상), (iii) 최대 인벤토리 대상 기준 실행만 1회 | 계약 12, 의도 '새 위험' |
| **S5** 계약 9 문구 | 반영. "노드 집합에 없고 간선 사전의 키·값에만", "dunder 속성 폴백 간선만 뺀다", auditor가 (i) 빠진 간선 분류 (ii) 도달 감소 수를 잰다 | 계약 9 |
| **S6** 번호 | 반영. D-18 고정: 33 = `33-v7-registry-edges`. 102행(문구 변경 338행) → 공격 33, 115·125행 경로, 계약 14 "새 케이스 33 제외 + 그 시점 attacks 전체", 189-191행 '순서' 단락 → "번호는 D-18 고정, 순서는 권고만" | 문구 변경, 판정 유형 근거, oracle 표, 계약 14, 결정 필요 항목 |
| minor 1 red 9 vs 10 | 새 표 기준으로 다시 셈: red 12(V7 11 + V3 1) | 판정 유형 근거 |
| minor 2 바인딩 값 생성자 | 반영. R2 "도달 가능한 코드 = … 바인딩 노드의 값 식" + green 단계 `ctor-in-binding` | R2, 계약 3 |
| minor 3 하네스 최상위 | 반영. 계약 머리·oracle 절 "하네스 최상위에는 import 문만" | 계약 머리, oracle |
| minor 4 거짓 FAIL 모양 | 반영. 의도 '알려진 한계' 한 단락 | 의도 |
| minor 5 시간 | 반영(1회 측정 4.8 → 5.4초, 잡음 범위, 임계값 없음) | 비용 문단 |
| 4.3 보충 27/31 | 반영. "27건, 서로 다른 커밋 쌍 27(정규식 일치 수는 그보다 많다)". 내 정규식으로는 일치 34 -- 패턴마다 다르므로 card에는 서로 다른 쌍 수만 기준으로 적었다 | 계약 14, 작성 전 실측 7 |

추가 결정(검토에 없음): 재수출 추적 깊이 상수를 두지 않고 방문 집합으로 순환을 끊는다(상수 임의 생성 금지 원칙). 계약 11에 적었다.

## 2. 재측정 결과

### 2.1 HEAD 트리(`m1_head.py`, 소스 def 494, test 함수 454, 루트 합집합 4·두 벌)

| 변형 | 미도달(합집합+R3) | before/after+R3 | 누수 비운영 노드(R3 없음) | V3 쌍 | 인벤토리 0 | 중앙값 | `build_graph` s |
|---|---|---|---|---|---|---|---|
| base(HEAD 도구와 간선 사전 동일 확인) | 116 (R3 없이 115) | 116 / 122 (R3 없이 115/121) | 64 | 33,991 | 82 | 61 | 4.4~4.8 |
| 초안 v1 규칙 | 39 | 39 / 39 | 66 | 79,809 | 14 | 146 | 4.0~4.6 |
| 개정(super 없음) | 39 | 39 / 39 | 64 | 44,493 | 19 | 67 | 4.7~5.3 |
| **개정(card)** | **39** | **39 / 39** | 64(R3 적용 시 0) | **44,493 (1.31배)** | **19** | **67** | 5.3~5.4 |

* 미도달 39 집합: 개정 = 초안 v1 = super 없음(차이 집합 공집합). 면제 두 id(`lut_conditions_from_npz`·`derived_spec`) 모든 변형에서 미도달 유지.
* 인벤토리 0 개정 19 = v1 14 + `audit_current_forced.py` 4(`_as_set`·`_theta_evidence_for_pair`·`audit_topology`·`render_report`) + `stick_diagram.py::check_mirror_symmetry`.
  개정 19 − base 82 = 공집합(base에서도 0이 아니던 def가 0이 된 것 없음).
* 표본: `SemiEmpiricalGmIdLUT.__init__` 0 → 249(v1 335), `_metric_sum_current` 0 → 87(v1 166).
* 간선 단조성(계약 9): v1 규칙은 옛 간선 전부 포함. 개정은 옛 간선 3개가 빠짐 -- 전부 `InfeasibleSizingError.__init__` → (속성 `__init__`) → `SemiEmpiricalGmIdLUT.__init__`·
  `tests/unit/_library_sized_contexts.py::SizedCircuit.__init__`·`tests/contracts/test_restore_plan_functions.py::_FakeNpz.__init__`(dunder 속성 폴백). 이로 인한 소스 def 도달 감소 0
  (R3 없이·있이, 루트 합집합·두 벌).
* 검토 수치와 일치: 미도달 39, V3 쌍 44,493, 인벤토리 0 = 19, 늘어난 5개 base에서도 0.
* 중앙값: card v1의 148은 이번 측정 146(중앙값 정의 차이 추정) -- card에는 개정 값 67만 적었다.

### 2.2 정적 인벤토리 미리보기(`m5_inventory.py`, 계약 12 (ii) 미리보기, test 실행 없음)

| 대상 def | base | 개정 | v1 |
|---|---|---|---|
| `sizing_recipe.py::lut_conditions_from_npz` | 5 | 5 | 5 |
| `run_harness.py::derived_spec` | 5 | 5 | 5 |
| `sizing_recipe.py::width_from_id_density` | 227 | 249 | 340 |
| `_build_theta_evaluator._evaluate` | 60 | 60 | 139 |
| `compute_metric` | 82 | 87 | 166 |
| `apply_theta_feed` | 66 | 66 | 145 |
| `stick_diagram.py::kcl_series_union` | 70 | 70 | 149 |
| `optimize_full_circuit_budget` | 60 | 60 | 139 |

→ 계약 12 (i)의 대상(`restore-plan-functions`의 두 def)은 인벤토리가 base와 같다(5·5) -- 비용 비교는 (ii)·(iii)이 주로 맡는다.

### 2.3 공격 33 합성 단계(`gen_attack33.py` → 두 복제본에서 `run_all.py --only 33-v7`, 실제 `rt vcase`)

단계별 exit(기대 대비 PASS/FAIL). 변형 열은 head 복제본의 시제품을 `RCH_VARIANT`로 바꿔 돌린 것.

| 단계 | 기대 | base 도구 | 개정 | v1 규칙 | 느슨한 구현 | super 없음 |
|---|---|---|---|---|---|---|
| registry-wired | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| registry-imported | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| registry-modattr | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| registry-reexport | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| registry-orphan | 1 | 1 P | 1 P | 1 P | 1 P | 1 P |
| registry-dead-reader | 1 | 1 P | 1 P | 1 P | 1 P | 1 P |
| registry-external-attr | 1 | 1 P | 1 P | **0 F** | **0 F** | 1 P |
| registry-attr-collision | 1 | 1 P | 1 P | 1 P | **0 F** | 1 P |
| registry-str-collision | 1 | 1 P | 1 P | 1 P | **0 F** | 1 P |
| registry-name-strings | 1 | 1 P | 1 P | **0 F** | **0 F** | 1 P |
| registry-local-shadow | 1 | 1 P | 1 P | **0 F** | **0 F** | 1 P |
| registry-reexport-other | 1 | 1 F(목록 다름) | 1 P | **0 F** | **0 F** | 1 P |
| ctor-wired | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| ctor-raise | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| ctor-inherited | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| ctor-dataclass-post-init | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| ctor-super-chain | 0 | 1 F | 0 P | 0 P | 0 P | **1 F** |
| ctor-in-binding | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| ctor-isinstance-only | 1 | 1 P | 1 P | 1 P | 1 P | 1 P |
| ctor-super-leak | 1 | 1 P | 1 P | **0 F** | **0 F** | 1 P |
| leak-test-name | 1 | **0 F** | 1 P | 1 P | 1 P | 1 P |
| leak-test-string | 1 | 1 P | 1 P | 1 P | 1 P | 1 P |
| approved-still-exempt | 0 | 0 P | 0 P | 0 P | 0 P | 0 P |
| direct-call-control | 0 | 0 P | 0 P | 0 P | 0 P | 0 P |
| binding-not-a-def | 0 | 0 P | 0 P | 0 P | 0 P | 0 P |
| v3-registry-inventory (V3) | 0 | 1 F | 0 P | 0 P | 0 P | 0 P |
| **합계** | | 13 FAIL / 13 PASS | **26 PASS** | 5 FAIL | 7 FAIL | 1 FAIL |

* red(base exit ≠ 기대 exit) 12 = V7 11 + V3 1. `registry-reexport-other`는 base exit 1(기대와 같음)이지만 미도달 목록이 `_f_y`·`_f_y2`라 메시지 대조로 FAIL.
* 새 거부 단계들은 검토가 지적한 잘못된 구현(v1 문장 그대로, 느슨한 색인 구현)을 실제로 거부한다(이 표가 근거). `ctor-super-chain`은 `super()` 규칙을 넣는 근거.
* 주의: 이 열은 개정 규칙의 시제품을 처음 버전(재수출 깊이 상한 4)으로 돌렸다. 그 뒤 깊이 상수를 방문 집합으로 바꾼 최종 시제품으로 §2.4에서 33을 다시 돌렸다.

### 2.4 기존 redteam 무동작(계약 14 미리보기)

범위 판단: 이 변경은 `reachability.py` 한 파일이다. 그 파일을 실행하거나 import하는 redteam 경로를 `grep`으로 골랐다 -- V7 `v7_unwired`, V3(`mutate_changed.py`가 `build_graph`
사용) `v3_survivor`·28·31, 인코딩 26(두 도구 직접 실행), V6 27f(두 도구 소스 검사 -- 새 코드의 broad except도 걸린다), V4 06·07·23·29(`test_lint.py`가 `import reachability`, `_approved_ids`만
사용), 공격 33, `--cases 0.5` 전체. 나머지 케이스는 이 파일을 부르지 않는다(`grep -rln "reachability\|mutate_changed" tools/gates redteam/lib redteam/*/run.sh` -- `test_lint.py`·`iface.py`·
`sb.py`(문자열만)·26·27f뿐). 전체 `run_all.py`는 base 쪽에서 15-records 하나가 27분이라 두 벌 전체 실행(수 시간)을 중단하고 이 범위만 두 벌로 돌렸다.
(중단 전 base 쪽 01~15 결과: 전부 PASS/SKIPPED -- 이 파일과 무관한 케이스라 비교 대상에서 뺐다.)

결과(`run_redteam_variants.py`, 최종 시제품 = 깊이 상수 없는 판, 단계별 exit·판정 대조):

| 케이스 | 단계 | base = 개정(exit·판정 같음) |
|---|---|---|
| 06-v4-expected-from-subject | 2 | 2 |
| 07-v4-assert-under-if | 2 | 2 |
| 23-v4-boundary | 169 | 169 |
| 26-gate-output-utf8 | 42 | 42 |
| 27f-v6-reconfigure-except | 16 | 16 |
| 28-v3-gmid-options | 4 | 4 |
| 29-v4-decision-exempt | 4 | 4 |
| 31-v3-git-history | 3 | 3 |
| v3_survivor | 2 | 2 |
| v7_unwired | 1 | 1 |
| 33-v7-registry-edges(새 케이스) | 26 | 13 같음 / 13 다름 = §2.3의 base FAIL 13 그대로, 개정은 26/26 PASS |
| `--cases 0.5`(사례 7개 중 5 실행, 2 SKIPPED) | 6 | 6 |

* 케이스 판정: base `PASS 10·FAIL 1(33)` / 개정 `PASS 11`, 단계 base `PASS 258·FAIL 13` / 개정 `PASS 271`. 사례: 두 벌 모두 `PASS 5·SKIPPED 2`, 단계 PASS 6.
* 33을 뺀 차이 0단계 -- 계약 14의 redteam 부분 무동작 미리보기 충족(범위 판단은 위).

### 2.5 과거 판정 기록 V7 쌍(`m4_records.py`)

* `.ai/verification/2026*.json`(HEAD) 중 V7 근거에 `reachability.py … --base X --head Y`가 있는 기록 27건, 서로 다른 커밋 쌍 27(내 정규식 일치 34 -- 짧은/긴 해시 중복).
* 27쌍 전부 base 도구·개정 시제품·v1 규칙의 `verdict`·`unreached`·`unreached_without_approval`이 같다(전부 PASS). `--config`는 27쌍 모두 head 트리의 `gate_config.json`.
* new_defs 있는 쌍: `20260922-ic3-completeness`(2)·`20260930-df36-instance-relpath`(1)·`20260930-dup-w-calc`(1)·`20260930-restore-plan-functions`(2 -- `lut_conditions_from_npz`·`derived_spec`
  세 도구 모두 미도달, 면제 승인으로 PASS). 검토 4.3과 같다.
* 이 측정은 깊이 상한 4 판 시제품으로 돌렸다(HEAD에서 최종판과 결과 동일 -- §2.1은 최종판으로 재측정해 같은 값).

### 2.6 머리 블록 검증

`tools/gates/role_paths.parse_spec_card(text, "20260930-v7-registry-edges")` 통과: `phase 0.5`, `evidence_type red-green`, `gate_change yes`, `approval` = card id, 절 11개
(의도 / 관찰 가능한 계약 / 신규 시그니처 / 판정 유형 근거 / oracle 종류와 출처 / 거부해야 할 입력 / library 회로 적용 여부 / 무동작 판정 입력(무발동 값) / 재현할 수치 /
결정 필요 항목 / 작성 전 실측).

## 3. V3 card 번호

`draft_v3_exempt_binding.spec.md`·`draft_v3_scope_policy.spec.md`·`v3_cards_revision_log.md`가 12:04~12:10에 다른 agent에 의해 수정 중이라 고치지 않았다. 확인해 보니 두 초안은
이미 34·35를 쓰고 있다. 남은 일(design v4 D-18의 B33 이름 `33-v7-graph-edges` → `33-v7-registry-edges`)은 `_drafts/redteam_numbering.md`에 적었다.

## 4. 남은 것

* 사용자: Q1((a) 권고), 게이트 변경 승인(범위에 R2'·S1·바인딩 값 문자열 제외 포함).
* 오케스트레이터: design v4 D-18 이름 정정(`redteam_numbering.md`), 재검토 여부 판단. timeout을 별도 결과로 분리하는 V3 변경은 백로그 후보(card 범위 밖).
* 측정하지 않은 것: Q1 (b)를 개정 규칙 위에서 HEAD로 잰 값(card의 "39 = 39"는 준비 자료의 옛 규칙 측정), 전체 redteam 두 벌 실행(§2.4 범위 판단).

## 5. 파일

* 개정 card: `_drafts/draft_b33.spec.md` (개정 전 `_drafts/draft_b33.v1.spec.md`)
* 스크립트: `_drafts/b33_scripts/` -- `reachability_b33.py`(시제품, `RCH_VARIANT` = fixed/draft/loose/nosuper/base), `m1_head.py`, `gen_attack33.py`, `run_redteam_variants.py`, `m4_records.py`, `m5_inventory.py`
* 결과 원본(같은 디렉터리): `m1.jsonl`(첫 판)·`m1b.jsonl`(최종판) §2.1, `m5.json` §2.2, `a33.jsonl` §2.3, `tgt.jsonl`·`cases.jsonl` §2.4, `m4.jsonl` §2.5
* 번호 메모: `_drafts/redteam_numbering.md`
