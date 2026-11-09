# V3 card 개정 기록 -- v1 → v2 (검토 `review_v3_cards.md` 반영)

대상: `draft_v3_exempt_binding.spec.md`(id `20260930-v3-exempt-binding`), `draft_v3_scope_policy.spec.md`(id `20260930-v3-changed-stmt-scope`), `draft_v3_decision_question.md`.
v1 사본: `draft_v3_exempt_binding.spec.v1.md`, `draft_v3_scope_policy.spec.v1.md`, `draft_v3_decision_question.v1.md`. 곁 수정: `v3_scope_systemic.md` §2 한 문장(사본 `v3_scope_systemic.v1.md`).
측정: gate `master` `7535799`, 저장소 쓰기·상태 변경 git 없음. scratch `C:/g60`(`git archive 7535799` 사본·스크립트·출력), 측정 뒤 삭제. 스크립트·출력은 `v3_scripts/`(재현 `README.txt`).
`$PY` = `C:/Python314/python.exe -B`(3.14.2). 도구 함수(`mutate_changed`·`reachability`·`role_paths`)는 저장소 `tools/gates`에서 읽기 전용 import, 도구 `main`은 돌리지 않음.

## 1. 지적별 처리

| 지적 | 처리 |
|---|---|
| B1 묶기 해시가 docstring 제외 | 묶기 해시를 새로 정의: head def 노드 **원본**(docstring·데코레이터 포함)의 `ast.dump(…, annotate_fields=True, include_attributes=False, indent=None, show_empty=False)` sha256. ①(대상 선택 `def_hash`)과 이름·용도 분리. 의도의 거짓 문장("해시가 같아지는 경우는 승인한 형태와 같은 코드뿐") 교체. redteam (e) `docstring-shift` 추가. 재현 `v3_probes.txt`(① 같음·묶기 다름·`body[1]` `log(y)`↔`y = clamp(x)`) |
| B2 머리만 바꾼 변경 → 대상 0 → PASS | (1) T5 `early_return` 무조건 (2) T3 두 변형: **(b) 기본** = def 자기 필드 + 바뀐 매개변수 이름을 읽는 문장, **(a) 선택지 2a** = 본문 전체 (3) 계약 2 '해시가 바뀐 기존 def마다 대상 ≥ 1 → test가 닿지 않으면 항상 FAIL' (4) redteam (f) `header-default-bool`. 데코레이터 NOOP은 계약 9(`_replace_def`를 첫 데코레이터 줄부터)로 이 card에서 고치고 redteam (h), 선택지 1이면 그 몫만 별도 card. 재현 `v3_probes.txt`(머리만 바꾼 7종 중 6종 자기 필드 변이 0, 데코레이터 `const±` NOOP, 고친 판 NOOP 아님), `v3_b2_cases.txt`(개정 N2 대상 1~3개) |
| S1 redteam 사실 오류 | 승인 기록 위치를 V 케이스 `head`/`base` 사전의 `.ai/approvals/<id>.md`로 정정(`rt.py` 446·459행 `_commit_case` 키와 구분). 해시 자리표시자 `@bindhash(<base\|head>:<경로>:<qualname>)` -- rt.py 동작 추가, 피검 모듈 import 금지, `@{…}`는 `subst_str`가 상태 변수로 읽어 실패하므로 다른 문법. 승인 범위 (ii)에 rt.py 동작 명시. (a)에 'X가 유일한 생존 변이' 조건 |
| S2 DF-36 실제 누수 | 의도에 실제 사례(판정 기록 `148bd6d`, `save_instance_json` `9cb09766…`→`11a55c19…`, exempt 4, auditor 수동 확인, 자동 재판정 경로에 V3 없음) 추가. '잃는 것 없음'을 '앞으로의 card 기준'으로 한정. 백로그 1(4개 실제 실행). 결정 질문 첫 절에도 |
| S2 곁가지(B34 `load_topology` 10) | 실측으로 정정: 좁힌 B34(def 4개)는 `load_topology`를 바꾸지 않는다. 해당되는 것은 **B26-1** -- C8 10개 문장이 `body[11]`·`body[26]` → `body[14]`·`body[29]`로 밀려 지금 도구로도 면제되지 않고(묶기와 무관) 선택지 1이면 다시 대상, N2·N2a·D1이면 대상 밖(`v3_c8_in_b26.txt`). 결정 질문 선택지 1 칸 |
| S3 원소 해석 규칙 | 분리 규칙(`@` 0개 = 해시 없음, 1개 = `split("@")` + `^[0-9a-f]{64}$`, 아니면·2개 이상 = `malformed`), 같은 id 여러 원소(하나라도 맞으면 exempt, 나머지 미기재), 중복 원소 한 번. redteam (f) `malformed-element` |
| S4 판마다 다른 `ast.dump` | 인자 전부 명시, 측정 인터프리터 = `$PY` 3.14.2, 필드 집합 변경은 fail-closed + 재승인(승인 범위 (iii)). 다른 판 인터프리터가 이 환경에 없어 판 간 출력 차이는 재지 않았다(card에 명시) |
| S5 exempt가 `--out`에 없음 | 계약 1: `{"id", "result": "exempt", "bind_hash"}`를 `--out`에도 append(WP-11) |
| S6 삭제만 한 변경 | T4에 삭제 지점 포함, T6(같은 블록 바로 뒤 문장의 몫) 추가. "지운 문장: 차이 없음" 거짓 문장 교체. 남는 공백(블록 끝 삭제, 다른 블록의 사용)을 계약 6·결정 질문 '놓치는 결함'에. redteam (g) `delete-then-use` |
| S7 redteam (c) | `if a < b:`의 `cmp_flip`로 고침(진리값 부정 연산자 없음 명시) |
| S8 G1 관계 | 실측 8과 `v3_scope_systemic.md` §2의 거짓 문장 정정(이동 규칙은 도구 미구현, G1이 구현). 계약 3에 G1 뒤 읽기, '결정 필요 항목'에 병합 순서·나중 card가 고칠 문장(G1 계약 4에 한 구절). redteam 번호 겹침(`32-moved-defs`) 기록 |
| S9 `not_targeted` 의미 | "실행하지 않은 변이 수(생존 수 아님)"로 정정, `--out`의 id를 '돌려 보지 않은 변이'로 백로그. 판정 밖 실행 모드는 별도 card 후보로만. 묶기 card의 '이번 실행의 변이 id' = 대상 변이(`not_targeted` 제외)로 정의 |
| S10 결정 질문 | (1) "결정 없이 진행" → **승인 요청(강화)** (2) **'놓치는 결함' 열** 추가 (3) "3의 몫도 대부분 기존 공백" 삭제 → "실제로 생존할지는 재지 않았다" (4) 선택지 1 현실 하한 **약 19 h**(3.4 h + 미실행 306 × 인벤토리 ≈ 15.8 h; 검토 추정 ≈3.4 h + 15 h와 같은 방식, 이번 인벤토리 시간 187~202 s) (5) 재시도마다 재승인·인터프리터 판 (6) B2·S6 반영 뒤 수치 재측정(아래 2절), 선택지 2a 행 추가 |
| S11 스크립트 소실 | 이번 측정 스크립트 전부와 출력을 `v3_scripts/`에 둠. 검토 전 확정 생존 298(B26-1)·75(넓은 B34)를 **그대로 재현**(base 본문, `_evaluate_row_split` 제외 시 298) |
| M1 | decision 기록 11개로 정정(`v3_anchors.txt`) |
| M2 | 소비처에 `A/tests/tools/engine_dup_scan.py`(102~122행) 추가, 계약 7에 포함 |
| M3·M4 | 묶기 card 백로그 4·5 |
| M5 | `SequenceMatcher`를 규범 알고리즘으로(LCS 아님), redteam은 같은 지문 반복을 피함 |
| M6 | T4 조상 = 대상 def 제외·중첩 def/class 포함, T5 무조건, 맞추는 트리 = docstring 포함 원본 |
| M7 | 확인 사항 그대로(계약 1 끝 문장) |

## 2. 재측정 -- 개정 정의(B2·S6 반영)

`v3_scope_classify.py` → `out/v3_scope_classify.txt`. 교정: 옛 N1 139·옛 N2 176을 같은 시뮬레이션에서 그대로 재현. 옛 D1은 388(검토 전 506 -- 옛 스크립트 소실로 이름 규칙 차이 미확인).

| card | 지금(def 전체) | 옛 N2 | **N2(T3 b, 기본)** | N2a(T3 a) | D1(T3 b + T7) |
|---|---|---|---|---|---|
| P9 실제 `7535799→b7765b0`(def 2) | 28 | 4 | **12** | 12 | 11 |
| P9 시뮬레이션(def 1) | 24 | 3 | **5** | 5 | 8 |
| B26-1 시뮬레이션(def 31, 머리 변경 20) | 2,472 | 176 | **228** | 1,309 | 399 |
| B34 좁힌 초안(def 4) | 55 | 6 | **10** | 10 | 14 |

* B26-1 N2 228 = 옛 176 + S6 몫 50 + B2 몫 2. 시간(직렬): 지금 3.4 h ~ 129 h(현실 하한 19.2 h), N2 19분 ~ 12.0 h(0.6 h), N2a 1.8 h ~ 71 h(5.8 h), D1 33분 ~ 21 h(1.6 h).
* 미실행 줄 대상 변이(head 줄 → base 줄 대응, 새 줄 119개는 판정 불가): B26-1 지금 306 / N2 6 / N2a 74 / D1 20. P9 실제 0. B34 좁힌 초안 1(그 card의 새 test가 죽임 -- B34 card 55/55).
* **관찰**: B26-1의 머리 변경 20개는 모두 키워드 전용 `rails` 추가다. 검토가 기본으로 적은 'def 머리 변경 → 본문 전체'(N2a)를 쓰면 B26-1 대상이 def 전체의 53%가 되어 선택지 2의 의미가 거의 사라진다.
  그래서 card 기본을 검토가 허용한 좁은 판(바뀐 매개변수 이름을 읽는 문장, T3 b)으로 두고, 보수 판을 선택지 2a로 결정 질문에 따로 올렸다(사용자 결정 -- 둘 다 약화).

## 3. 머리 블록 검증

`role_paths.parse_spec_card(text, id)` 두 card 모두 통과: `phase 0.5`, `evidence_type red-green`, `gate_change yes`, `approval` = 각 card id, 절 11개(의도 / 관찰 가능한 계약 / 신규 시그니처 /
판정 유형 근거 / oracle 종류와 출처 / 거부해야 할 입력 / library 회로 적용 여부 / 무동작 판정 입력(무발동 값) / 재현할 수치 / 결정 필요 항목 / 작성 전 실측).

## 4. 남은 것(오케스트레이터·사용자)

* 사용자: 묶기 card 승인(강화, rt.py 동작 추가·인터프리터 판·재시도마다 재승인 명시), 범위 정책 1/2/2a/3 결정.
* 오케스트레이터 백로그: DF-36 면제 4개 실제 실행, V7·V4 면제 묶기, `_approved_ids` 파일 전체 읽기(M3), 같은 qualname 둘(M4), 중첩 def 이중 변이 관찰, 대상 밖 변이 판정 모드(S9 ii),
  (선택지 1이면) 데코레이터 NOOP 수정 별도 card.
* redteam 번호 `32-…` 겹침(G1 초안 `32-moved-defs`): 나중에 병합하는 card가 바꾼다.
* 검토 전 '약화 없는 가속' 커버리지 선택 상한 70.3 h는 이번에 다시 재지 않았다(이번 `covplug.py`는 실행 줄 합집합만 기록 -- test별 기록 아님). card에 그렇게 적었다.
