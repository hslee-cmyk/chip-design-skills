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

---

# v2 → v3 (2026-10-01, 커밋용 확정) -- 2차 검토 `review2_v3_cards.md` + 사용자 결정 `user_decisions.md` 반영

v2 사본: `draft_v3_exempt_binding.spec.v2.md`, `draft_v3_scope_policy.spec.v2.md`, `v3_cards_revision_log.v2.md`(이 파일), `backlog_additions.v2.md`.
결정: A1-a 승인(묶기 card), A1-b ② N2 (b), A1-b 정정 "규칙을 안내에 맞게 넓힘" -- T6를 '같은 블록 뒤쪽에서 바뀐 이름을 읽는 문장 전부'로.
측정: gate `master` `7535799`, scratch `C:/g69`(archive 사본), 저장소 쓰기·상태 변경 git 없음. 새 스크립트·출력 `v3_scripts/`(README 8~10단계).

## 5. 지적·결정별 처리

| 지적·결정 | 처리 |
|---|---|
| B1(놓치는 범위 문안이 실제보다 좁음) + A1-b 정정 | **T6 넓힘(선택지 2)**: 계약 1 T6 = (가) 삭제 지점 바로 뒤 문장 + (나) 바뀐 영역(새 문장·머리 변경 복합문·지운 문장)이 바꾸는 이름을 같은 블록 뒤쪽에서 읽는 문장의 몫, 반복문 `body`면 위치 무관(다음 회차). '바꾸는 이름' = Name Store/Del + 속성·첨자 대입 대상의 맨 앞 이름 + 메서드 호출 수신자 맨 앞 이름 + `except as` 이름. 의도 절·승인 기록에 '놓치는 것' ①~③ 정확한 문장(다른 블록 / 두 단계 이상 / 기존 test 강도). redteam (i) `same-block-later-use`·(j) `loop-carried-use` attack, (k) `cross-block-not-targeted` control(약화 경계 고정) |
| 반복문 규칙(추가 판단) | 사용자 문장 "같은 블록 뒤쪽"만이면 반복문 다음 회차로 흐르는 **앞** 문장(같은 블록·한 단계)이 남아 '다른 블록·두 단계 이상만 놓침'이 다시 거짓이 된다 -- 그래서 반복문 `body`는 위치 무관으로 넣었다(강화 쪽, 사용자 문장의 의도와 같은 방향). 오케스트레이터 보고에 명시 |
| S1 번호 | 34(묶기)·35(범위), D-18 배정 문장으로 교체 |
| S2 판별력 | 두 card 모든 attack에 'X가 대상 변이 중 유일 생존' 공통 구성, 기대 = 정확한 JSON 조각(`"survivors": ["<X>"]`, `{"id": "<X>", "reason": "unbound"}`, `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "`, `{"id": "<X>", "reason": "malformed", "element": "<X>@abc"}`, `"not_targeted": <n>`). 출력 키 순서·레코드 키 순서 명시 |
| S3 `--out` 관찰 | (가) 채택: rt.py `"observe": "out_jsonl"`(`--out` 줄 수 + killed·survived 아닌 결과별 id 목록)을 묶기 card 계약 9·승인 범위 (ii)에. 범위 card는 같은 관찰 사용(rt.py 추가 없음). 묶기 (c)·범위 (a)·(k)에서 `observed_equals` |
| S4 상호작용 | 묶기 계약 9 공통 구성: X는 바뀐 문장 안(T1) 또는 `early_return`, (c) head def는 모든 문장이 base와 다름. 우선순위 '대상 밖 → 면제 판정 안 함(`not_targeted` 먼저)'을 두 card(묶기 용어 절, 범위 계약 4)에. 범위 계약 7을 '34는 대상 집합 안 -- 결과 불변'으로 |
| S5 결정 대기 문장 | 범위 card: '선택적·결정 대기', '선택지별 대상 정의'(N2a·D1·N1), T3(a), T7 삭제. 기각 대안은 '결정 필요 항목' 한 줄 + 수치 참고 한 줄. 묶기 card: '승인 요청' → 'A1-a 승인 완료' |
| S6 design 05 문구 | "지운 문장 자리의 앞뒤" → "바꾸거나 지운 문장 자리 바로 뒤 문장·바뀌거나 지운 문장이 바꾸는 이름을 같은 블록 뒤쪽(반복문 본문이면 그 본문 전체)에서 읽는 문장·def 머리가 바뀌면 그 자기 필드(기본값·데코레이터 인자·주석)와 바뀐 매개변수를 읽는 문장, 그리고 `early_return`" |
| S7 G1 순서 | 계약 3 확정(이 card가 G1보다 먼저, 새 def 규칙 그대로). G1 초안 문장은 백로그 B45(`backlog_additions.md`) |
| M1 실수 표기 | 묶기 계약 11(묶기 해시 = 같은 노드, 변이 값은 표기 단위 -- 등가 승인은 표기 무관할 때만, 승인 범위 (v)). 범위 계약 1 끝에 표기만 바뀐 문장 = 바뀌지 않은 문장 |
| M2 `@bindhash` 순서 | 모든 파일 내용을 만든 뒤 두 번째 단계 치환, 자리표시자 든 파일은 참조 불가(순환 금지), 참조 없음·qualname 없음 → RuntimeError |
| M3 기존 한계 | 백로그 B46 |
| M4 design 10 382행 | 문구 고침을 묶기 계약 10에 넣음(원소 형식은 design 05 ⑤로 넘김), 승인 diff_path에 design 10 |
| M5 출력 세부 | 묶기: `exempt_ignored` 순서 = 변이 생성 순서, 같은 id는 원소 문자열 오름차순, `mutants`에 exempt 포함. 범위: `mutants` = 대상 변이 수(`not_targeted`는 `--out`에만), `targets_by_def` 키 순서·새 def 값 |
| M6 | 기각 대안이라 card에서 정의를 지웠다(이 기록에만) |

## 6. 재측정 -- 넓힌 T6(`v3_scope_widen.py` → `out/v3_scope_widen.txt`)

| card | 지금(def 전체) | 승인 당시 N2(T6 바로 뒤) | **넓힌 T6(card 확정)** | 시간(넓힌 T6) | 미실행 줄 대상 변이 |
|---|---|---|---|---|---|
| P9 실제 `7535799→b7765b0` | 28 | 12 | **12** | 1.0분 ~ 0.64 h | 0 |
| B26-1 시뮬레이션 | 2,472 | 228 | **294** | 24.5분 ~ 15.6 h, **현실 하한 0.88 h**(승인 당시 0.63 h, 지금 19.2 h) | 6 → **9** |
| B34 좁힌 초안 | 55 | 10 | **10** | 0.8분 ~ 0.27 h | 0 |

* B26-1 +66: `propose_device_roles_gap_fill` +18, `_branch_composite_pair` +12, `run_matching_safety_with_finger_growth` +8, `_composite_collapse_for_crossover` +5, `refine_differential_and_mirror_relations` +4,
  `load_topology` +4, 그 밖 10 def +1~2. 맞춤 결과는 원래 분류기와 같음을 스크립트가 단언(MatchW == Match).
* 적대 21건(`v3_adv21.py` → `out/v3_adv21.txt`, 2차 검토 scratch가 지워져 표 설명대로 다시 씀 -- 변이 수는 검토와 다름): **사례 11·14 덮임**(11: 3/PASS/0 → 5/FAIL/2, 14: 3/PASS/0 → 4/FAIL/1),
  사례 6도 승인 당시 6/FAIL/0 → 10/FAIL/4로 지금 규칙과 같아짐. 지금 규칙보다 더 놓치는 것 = 1c·4b(③ 두 단계 -- 4b는 재작성본에서 `key` → `s` → `return` 흐름이 드러난 것, 검토 판은 FAIL/2였다)·15(② 다른 블록).
  합계 대상 지금 179 / 승인 당시 87 / 넓힌 98.
* 경계(`v3_widen_boundary.py`): 반복문 앞 문장 대상, 다른 블록 대상 밖, 속성·메서드 수신자 대상, 두 단계 대상 밖 -- card 계약 1 문장과 일치.

## 7. 머리 검증과 승인 기록 초안

* `role_paths.parse_spec_card` 두 card 통과(phase 0.5, red-green, gate_change yes, approval = 각 id, 절 11개).
* 승인 기록 초안 `approval_20260930-v3-exempt-binding.md`(diff_path 5: 계획, design 05, design 10, interface, spec), `approval_20260930-v3-changed-stmt-scope.md`(diff_path 4: 계획, design 05, interface, spec) --
  target·diff_base·diff_head = `<rev-parse>`. 더미 값으로 바꿔 `merge_gate.parse_approval_header` 통과 확인. 범위 card 기록에 '약화 승인'·'놓치는 것' ①~③·두 사용자 답 원문 인용.
* 남은 것(오케스트레이터): interface card 두 개 작성(경로는 승인 diff_path), 문서 커밋(design 05 ①·⑤, design 10 382행, 계획 N4.2) 뒤 rev-parse로 승인 기록 채움, B26-1 card의 V3 수치 228 → 294 갱신,
  사용자에게 수치 변경 한 줄 보고, backlog B45·B46 반영, 경위(v1·v2 정의·옛 수치)는 history H 절로.
