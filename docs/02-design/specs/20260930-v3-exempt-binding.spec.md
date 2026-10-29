---
id: 20260930-v3-exempt-binding
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v3-exempt-binding
---

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260930-v3-exempt-binding.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 0.5(역할 분리 인프라) card다. 역할 분리 gate·auditor는 DEC-86으로 꺼졌다(계획 N6.1 '옛 Phase 처리' 0.5행; N3.12 역할 분리·N4.2 auditor V1~V10·N4.3 게이트 거부 증명은 폐기 절). 본문의 게이트 동작(EL1~EL4·V1~V10)·§13.4 재설치·승인(DEC-40·R1) 문장은 현행 절차가 아니다 -- 현행 완료 조건은 계획 N6.3(가벼운 절차)이다. `tools/gates/**`·`hooks/role_*`·`.githooks/`에 남은 파일은 꺼진 잔여물이다(DEC-86). 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 본문은 기록이며 덧대지 않는다(O-169).

## 의도

게이트 V3(`tools/gates/mutate_changed.py`)의 **등가 변이 면제가 승인한 코드에 묶이지 않는 결함**을 고친다. 정책 질문이 아니라 결함이다(조용한 면제 = '게이트가 실제로 거부하는가' WP-02 위반).
사용자 승인 2026-10-01 A1-a(승인 기록 `20260930-v3-exempt-binding`). 병합 순서: P9·P10·P10b 뒤, V3 범위 정책 card `20260930-v3-changed-stmt-scope` **앞**, B26-1 앞.

지금 동작(HEAD 7535799 실측, gate `master` `a796468`·`0f23786`·`19eb475`에서 재확인 -- `7535799..19eb475` 사이 `tools/` 변경 0. 착수 때 0단계 명령('작성 전 실측' 1 셋째 항목)으로 다시 잰다):
* 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`(도구 `main`의 `mid`). def 해시·card에 묶이지 않는다.
* 도구는 head 트리 `.ai/approvals/*.md` 중 머리에 `target_kind: decision`이 있는 **모든** 기록의 `target` 원소를 한 집합으로 읽고(`reachability._approved_ids`),
  변이 id가 그 집합에 있으면 실행하지 않고 `exempt`로 센다(`mutate_changed.main`, `if mid in approved`).
* 그래서 한 card에서 승인한 면제가 **뒤 card의 같은 경로 변이를 조용히 면제한다** -- 그 경로에 다른 문장이 와 있어도. 실측(`_drafts/v3_scope_systemic.md` §3):
  B26-1 시뮬레이션 head의 '닿지 않은 변이' 2,366개를 면제 목록으로 만들면 그 위에서 B34(v1 넓은 범위) 대상 def의 변이 1,402개 중 **619개**가 이미 면제된다.
* **이 누수는 실제 판정에 쓰였다(DF-36)**: 판정 기록 `.ai/verification/20260930-df36-instance-relpath.json`(커밋 `148bd6d`) V3 basis = head `b29be01`에서 변이 26 중 "killed 22, **exempt 4**
  (head 트리 승인 `20260922-ic3-v3-exempt`), 생존 0". 이 4개는 C8 기록의 `save_instance_json` id다. 그런데 `save_instance_json`은 DF-36 base `070cf69`(① 해시 `9cb09766…`)에서
  head `b29be01`(`11a55c19…`)로 **바뀌었다**(그래서 V3 대상이 됐다). C8 기록 범위 설명은 "두 함수의 본문 구조가 바뀌면 이 면제는 맞지 않는다"고 적었는데, 도구는 경로만 보고 4개를 면제했다.
  auditor는 4개가 base·head에서 같은 문장(`scope_note` 분기 `body[2]`·`body[2].body[0]`, `json.dump(indent=2)` ±1)을 가리킴을 손으로 확인했다(같은 판정 기록. 이 card 재측정
  `v3_scripts/out/v3_anchors.txt`도 같음). 그래서 결과는 맞았을 수 있으나 **승인 범위 밖 면제에 기댄 PASS**다. 자동 재판정으로 뒤집히지는 않는다(`integrity.py` 행 3(나)는 옛 판
  `merge_gate.py receive`를 돌리고, `merge_gate.py`는 V3를 부르지 않는다 -- `grep` 0건). 처리: 백로그 B41.

고칠 방향: **면제 원소를 (변이 id, 승인 시점 def의 '묶기 해시') 쌍으로 묶는다.** 원소 형식 `<변이 id>@<묶기 해시>`. 면제는 head의 그 def 묶기 해시가 원소의 해시와 같을 때만 적용한다.
* **묶기 해시는 design 05 §10 V3 ①의 해시와 다르다.** ①(대상 선택, 도구 `def_hash`)은 docstring을 지운 트리를 해시한다. 그런데 변이 경로(`body[i]` 등)는 docstring을 **지우지 않은** 트리에서
  만든다(`mutants(fn, …)`). docstring 한 줄을 더하거나 빼면 ① 해시는 같고 경로는 한 칸씩 밀린다 -- 같은 해시에서 같은 id가 다른 문장을 가리킨다(재측정
  `v3_scripts/out/v3_probes.txt`: `def f(x): y = clamp(x); log(y); return y`에 docstring만 더하면 ① 해시 같음, `stmt_delete:body[1]`이 `log(y)` → `y = clamp(x)`). 그래서 묶기 해시는
  **변이 경로를 정하는 바로 그 트리**(docstring·데코레이터를 포함한 head def 노드 원본)를 해시한다. 정의는 계약 머리.
* card 묶음은 따로 두지 않는다: V3는 base와 ① 해시가 다른 def만 변이하므로, 승인한 def 형태가 병합된 뒤 그 def를 바꾸는 card에서는 ① 해시가 달라지고(그래서 대상이 되고) 묶기 해시도 달라져
  면제가 풀린다. 같은 card의 재시도에서 def를 바꾸면 -- docstring만 바꿔도 -- 묶기 해시가 달라져 풀린다. 묶기 해시가 같으면 변이 경로가 가리키는 노드가 승인한 형태와 같다
  (같은 트리, 같은 경로). 그래서 면제가 그 **노드**에 정확히 적용된다. 단 실수 상수의 표기만 다른 경우는 노드는 같고 변이 값이 다르다(계약 11).
* 승인 기록 머리 형식(`merge_gate.parse_approval_header`, `00-common` §8.2)은 바꾸지 않는다 -- decision `target`은 쉼표로 나눈 비지 않은 원소 목록이고 `@`는 이미 허용된다. 새 키가 없으므로
  스키마·redteam 15-records 영향이 없다.
* **기존 승인 기록은 고치지 않는다**(N3.12.2: 기존 기록 수정·삭제 거부). 이행 규칙 = 해시 없는 V3 모양 원소는 **적용하지 않고 출력에 싣는다**(fail-closed. 출력에 싣는 것은 그 id가 이번 실행의 변이 id일 때 -- 계약 3).
  잃는 것: **앞으로의 card 기준으로는 없다**('작성 전 실측' 1). 다만 이미 내려진 DF-36 V3 PASS는 위 누수에 기댔다 -- 그 판정은 바뀌지 않고(재판정 경로에 V3 없음) 백로그로 확인한다.
  V3 모양이지만 **V3 대상 영역 밖 파일**의 원소(auditor 보충 뮤테이션 면제 -- 예 `20261001-p10b-v3-equiv`의 `reg_check:…` 9개, 파일 `skills/analog-gmid-design/assets/tests/tools/reg_check.py`는
  `reachability._is_source` 밖이라 도구가 그 변이를 만들지 않는다)는 지금도 도구가 적용한 적이 없고 이 card 뒤에도 계약 3 셋째 문장으로 출력에 실리지 않는다 -- 이 card로 달라지는 것이 없다(범위 밖 절).
  암묵 앵커(승인 커밋 시점의 def 해시)는 쓰지 않는다 -- 실측으로 틀린 앵커다(같은 절).
* 강화다(면제되는 변이 집합이 줄고 거부 집합이 넓어진다). 게이트 판정 기준 변경이므로(design 05 §2 표 'V3~V7' 행: 판정 기준 소유 = `사용자`) `target_kind: diff` 사용자 승인(A1-a)으로 덮는다.

범위 밖(이 card에서 바꾸지 않는다, 백로그):
* V7(`reachability.py`) 면제: 같은 읽기(`_approved_ids`)를 쓰지만 V7은 **base에 없던 def**만 판정하므로, 승인한 def가 병합되면 그 id는 다시 판정되지 않는다. 누수 조건은 '같은 qualname을
  지웠다가 다른 본문으로 다시 더함'뿐이다. 지금 V7 원소 2개(`20260930-restore-unwired-until-6a`)는 두 def가 HEAD에 있어 판정 대상이 아니다.
* V4(`test_lint.py`) 면제: 같은 부류의 누수(test id `<파일>::<test 이름>`에 묶임, test 본문 해시 미묶임)다. 그러나 V4는 바뀐 test 파일의 **모든** test를 lint하므로 기존 원소 2개
  (`20260923-c9-v4-exempt`)가 뒤 card에서 계속 필요하다 -- fail-closed 이행이 V3와 달리 무손실이 아니어서 이행 설계가 따로 필요하다.
* `reachability._approved_ids`의 반환값·동작은 바꾸지 않는다(V4·V7 소비자 불변).
* **auditor 보충 뮤테이션 면제**(V3 대상 영역 밖 파일에 auditor가 손으로 넣은 변이의 등가 면제 -- 지금 `20261001-p10b-v3-equiv` 9개, `tests/tools/reg_check.py`): 도구는 `targets`를
  `rch._is_source`로 거르므로(`mutate_changed.py` 315행) 이 id를 만들지 않고, 면제 적용은 auditor 판정 몫이다(그 기록 범위 설명: "2차 시도 auditor가 병합본에서 각 id를 다시 만들어 여전히
  등가라고 판정한 것에만 적용"). 묶기 해시는 정의상 계산할 수 있다(id에는 모듈 basename만 있으므로 경로는 basename으로 찾는다 -- 지금 `reg_check`는 트리에 하나뿐). gate `master` `0f23786`에는
  P10b가 병합되지 않아 qualname 4개 중 3개가 없었고, P10b 재시도 3차 병합(`54ef51c`, 판정 기록 `afcf36c`) 뒤 `19eb475`에는 4개가 모두 있다(묶기 해시 앞 16자 `_df23_expected` `7e3615bc…`,
  `check_df23` `10ddb443…`, `_df23_rows_under` `b3c9b826…`, `main` `279df768…` -- 1차 병합본 `4294048` 값과 같다. 측정 `v3_decision_census.py`). 그래도 이 card는 그 원소를 고치거나 묶지 않는다
  (기존 기록 수정 금지 N3.12.2, 도구가 읽지 않으므로 묶어도 도구 효과 0). 부수 효과(강화): 앞으로 V3 대상 영역에
  basename이 같은 모듈(`…/assets/reg_check.py`)이 생겨 경로·qualname이 맞아떨어져도, 이 card 뒤에는 해시 없는 원소라 `unbound`로 실리고 적용되지 않는다(지금 도구라면 조용히 면제된다).
  보충 뮤테이션 면제를 묶는 규칙은 백로그 7.

## 관찰 가능한 계약

용어.
* "V3 모양 원소" = decision 승인 기록 `target` 원소 중 `@` 앞부분(아래 분리 규칙)이 `<모듈>:<qualname>:<연산자>:<경로>` 모양(연산자 ∈ `cmp_flip`, `arith`, `const+`, `const-`,
  `stmt_delete`, `early_return`, `except_body_delete`)인 것.
* **"묶기 해시"(binding hash)** = `hashlib.sha256(ast.dump(F, annotate_fields=True, include_attributes=False, indent=None, show_empty=False).encode("utf-8")).hexdigest()`(소문자 16진 64자).
  F = 변이를 만든 head 소스를 `ast.parse`한 트리에서 그 qualname의 def 노드 **원본**(docstring을 지우지 않고, 데코레이터·중첩 def·중첩 docstring 포함 -- `mutants(fn, …)`가 받는 `fn`과
  같은 노드). 중첩 def의 노드를 바깥 def의 변이로 만든 id면 F는 바깥 def다(id의 qualname = F의 qualname). `ast.dump`의 인자는 **모두 명시**한다(3.13에서 생긴 `show_empty`처럼 기본값이
  판마다 바뀌어도 출력이 따라 바뀌지 않게). 측정 인터프리터는 gate 인터프리터 `$PY`(`C:/Python314/python.exe`, 3.14.2)다. AST 노드 필드 집합이 바뀌는 Python 판 변경(예: 3.12의
  `type_params`)은 해시를 바꾼다 -- 그때 묶인 면제는 모두 `hash_mismatch`(계약 2)가 되고(fail-closed, 누수 아님) 필요한 면제는 다시 승인한다.
  ①의 해시(`def_hash`, docstring 제외 -- 대상 선택용)와 이름·용도가 다르다. 도구 안에서 둘을 섞지 않는다.
* **원소 분리 규칙**: 원소 문자열(앞뒤 공백 제거)에 `@`가 없으면 '해시 없는 원소'(id = 원소 전체). `@`가 정확히 하나면 `id, h = 원소.split("@")`. `h`가 정규식 `^[0-9a-f]{64}$`에 맞지 않거나
  `@`가 둘 이상이면 '형식 오류 원소'(id = 첫 `@` 앞). 변이 id에는 `@`가 들어갈 수 없다(모듈·qualname·연산자·경로 문자 집합 -- 도구 `mid` 구성).
  V3 모양 원소라도 모듈이 V3 대상 영역(`reachability._is_source`) 밖이면(auditor 보충 뮤테이션 면제) 이번 실행의 변이 id가 될 수 없다 -- 계약 3 셋째 문장으로 출력에 싣지 않는다.
* "이번 실행의 변이 id" = 도구가 이번 실행에서 **실행 대상으로 만든** 변이의 id. 범위 정책 card `20260930-v3-changed-stmt-scope`가 병합된 뒤에는 그 card의 대상 변이만이다:
  **대상 밖 변이는 면제 판정을 하지 않는다**(`not_targeted`가 먼저 -- 결과는 `not_targeted`, `exempt`도 `exempt_ignored`도 아니다. 범위 card 계약 4와 같은 규칙).

1. **묶인 면제 적용**: head 트리의 decision 승인 기록에 원소 `<id>@<H>`가 있고 H가 그 변이의 head def 묶기 해시와 같으면 그 변이는 실행하지 않고 결과가 `exempt`다.
   결과 레코드 `{"id": <id>, "result": "exempt", "bind_hash": H}`(키 순서 그대로)를 결과 목록에 넣고 **`--out`에도** append한다(지금은 `exempt`가 `continue`로 `--out` append를 건너뛴다 --
   WP-11 기록 누락을 함께 고친다).
2. **해시 불일치**: 같은 id의 원소가 모두 `<id>@<H'>`(H' ≠ head 묶기 해시)이면 면제하지 않는다 -- 변이를 정상 실행해 `killed`/`survived`로 센다. 출력 JSON `exempt_ignored`에 원소마다
   `{"id": <id>, "reason": "hash_mismatch", "approved_hash": H', "head_hash": H}`(키 순서 그대로)가 든다.
3. **해시 없는 원소·형식 오류 원소**: 원소의 id가 이번 실행의 변이 id와 같으면 면제하지 않는다(정상 실행). 출력 `exempt_ignored`에 `{"id": <id>, "reason": "unbound"}` 또는
   `{"id": <id>, "reason": "malformed", "element": <원소 문자열>}`(키 순서 그대로)이 든다. id가 이번 실행의 변이 id와 같지 않은 원소는 싣지 않는다(다른 도구의 id·다른 def의 id·대상 밖 변이).
4. **같은 id에 원소가 여럿**(시도마다 승인한 경우 등): 하나라도 계약 1에 맞으면 `exempt`이고 그 id의 다른 원소는 `exempt_ignored`에 싣지 않는다. 하나도 맞지 않으면 원소마다 계약 2·3의 항목을 싣는다.
   여러 기록에 같은 원소 문자열이 있으면 한 번만 센다.
5. **판정**: 1의 `exempt`를 뺀 변이 중 생존이 있으면 FAIL(exit 1), 없으면 PASS(exit 0) -- 지금과 같다. `exempt_ignored`는 판정을 바꾸지 않는다(정보). 2·3으로 풀린 변이가 생존하면 FAIL이다.
6. **출력 형식**: 출력 JSON은 지금 키(`tool`, `verdict`, `targets`, `mutants`, `killed`, `survivors`) 뒤에 이 순서로 `survivor_bindings`, `exempt_ignored`를 더한다(`json.dumps(…, ensure_ascii=False)`,
   기본 구분자 -- 지금 도구 그대로). `survivor_bindings` = 생존 변이마다 `<id>@<head def 묶기 해시>`(순서는 `survivors`와 같음). `survivors`는 지금 형식 그대로다(변이 id만).
   `exempt_ignored` 원소 순서 = 도구가 변이를 만드는 순서(`targets` 경로 순, 파일 안 `changed_defs` 순, def 안 `mutants` 순)이고, 같은 id의 원소가 여럿이면 원소 문자열 오름차순.
   `mutants`(= 결과 레코드 수)에는 `exempt`가 든다(지금과 같다).
7. **다른 도구 무영향**: 같은 입력에서 V4(`test_lint.py`)·V7(`reachability.py`)의 출력 JSON과 exit가 base 도구와 같다(`_approved_ids` 불변). `@`가 든 원소는 V4·V7의 어떤 id와도 같지 않다.
   `merge_gate.parse_approval_header`·`weakening_diff.approved_hashes`(`target_kind: diff`만 읽음)·`A/tests/tools/engine_dup_scan.py`(decision `target` 원소 `<path>::<rule>` 집합 비교)의 결과도 같다.
8. **무동작**: 기존 redteam V3 케이스(`v3_survivor/` attack exit 1·control exit 0, `attacks/28-v3-gmid-options/`, `attacks/31-v3-git-history/`, 공격 26·27f)와 V4 `attacks/29-v4-decision-exempt/`의
   결과가 base와 같다. 승인 기록이 없는 저장소에서 V3 출력은 새 키(`survivor_bindings`, `exempt_ignored` 빈 목록)를 빼면 base와 같다.
9. **새 redteam 케이스** `tools/gates/redteam/attacks/34-v3-exempt-binding/`(번호는 design v4 D-18 배정: 32 = G1 `32-moved-defs`, 33 = B33, **34 = 이 card**, 35 = 범위 정책 card. V 케이스 `v.json`,
   합성 저장소). 승인 기록은 V 케이스의 `head`(또는 `base`) 파일 사전 안 `.ai/approvals/<id>.md` 파일로 둔다(선례 `attacks/29-v4-decision-exempt`). 원소의 해시는 아래 rt.py 자리표시자로 넣는다.
   **모든 단계의 공통 구성**:
   * 면제 대상 변이 X는 head def에서 **base def와 다른 문장의 부분 트리 안**(범위 card 계약 1 T1) 또는 `early_return`이다 -- 범위 card(35)가 뒤에 병합돼도 X가 대상으로 남아 결과가 같다.
   * **X가 그 def 대상 변이 중 유일한 생존 변이**다(다른 변이는 그 단계의 test가 모두 죽인다 -- 구성으로 정한다). 그래서 피검 도구가 그 단계가 겨냥한 규칙을 빠뜨리면 X가 면제되어 생존이 0이 되고
     exit 0이 된다(판별력).
   * 기대 출력은 `message_contains`에 쓸 **정확한 JSON 조각**이다. `<X>`는 test-author가 구성으로 정한 변이 id 문자열(모듈 = `reachability.module_name(<경로>)`, 예 `rt_engine:rt_scale:const+:body[0].value.left`)이다.
   (a) `legacy-unbound-leak`(attack) -- base 커밋에 해시 없는 원소 X로 면제하는 decision 승인 기록이 있고, head가 그 def를 바꿔 X가 생존 → exit 1, 조각 `"verdict": "FAIL"`, `"survivors": ["<X>"]`,
       `{"id": "<X>", "reason": "unbound"}`. base 도구 exit 0(조용한 면제) -- **red**.
   (b) `hash-mismatch`(attack) -- 원소 `<X>@<바꾸기 전 def의 묶기 해시>`(자리표시자 `base:`), head가 def를 바꿔 X가 생존 → exit 1, 조각 `"survivors": ["<X>"]`,
       `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "`. (base 도구도 exit 1 -- 회귀 방지.)
   (c) `bound-exempt`(control) -- 원소 `<X>@<head def의 묶기 해시>`(자리표시자 `head:`) → exit 0, 조각 `"verdict": "PASS"`, `"survivors": []`, `"exempt_ignored": []`.
       관찰 `"observe": "out_jsonl"`(아래) → `observed_equals` = `{"lines": <head def 변이 수>, "by_result": {"exempt": ["<X>"]}}`(WP-11 `--out` 기록). 이 단계의 head def는 **base def와 모든 문장이
       다르게** 구성한다(범위 card 계약 1 T1로 모든 변이가 대상 -- 35 병합 뒤에도 `lines`·`by_result`가 같다). base 도구 exit 1(`@` 원소를 모른다) -- **red(green 쪽)**.
   (d) `bound-other-def`(attack) -- 원소가 같은 파일 다른 qualname def의 묶기 해시를 달고 있음(`<X>@<다른 def 묶기 해시>`) → exit 1, 조각 `"survivors": ["<X>"]`,
       `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "`.
   (e) `docstring-shift`(attack) -- base def D0, 시도 k의 def Dk(D0과 ① 해시가 다르고 모든 문장이 D0과 다르다)의 소스를 V3 대상 밖 경로(예: `notes/attempt_k.py`)에 두고 원소
       `<X>@<Dk의 묶기 해시>`(X는 Dk에서 등가 변이). head def = Dk에 docstring 한 줄만 더한 것(① 해시는 Dk와 같고 X 경로가 한 칸 밀린 다른 문장을 가리킨다), 그 X 변이가 생존 → exit 1,
       조각 `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "`. (① 해시로 묶은 구현이면 X가 면제되어 exit 0 -- X가 유일 생존이라 판별된다.
       base 도구는 `@`를 몰라 exit 1이므로 red는 (a)·(c)가 맡고 (e)는 회귀 방지 단계다.)
   (f) `malformed-element`(attack) -- 원소 `<X>@abc`(64자 16진 아님), X 생존 → exit 1, 조각 `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "malformed", "element": "<X>@abc"}`.
   **rt.py 동작 추가 두 개(test-author, design 10 C10 행 -- 승인 범위 (ii))**:
   * 자리표시자 `@bindhash(<base|head>:<경로>:<qualname>)`: V 케이스의 모든 파일 내용(`str` 명세는 `subst_str`까지, `{"text": …}` 명세는 `replace`까지 -- `_file_content` 그대로)을 **다 만든 뒤
     두 번째 단계에서** 치환한다. 값 = 그 케이스 `base`/`head` 사전의 `<경로>` 파일 텍스트(첫 단계 결과)에서 그 qualname def의 묶기 해시. 계산은 표준 라이브러리 `ast`·`hashlib`만으로 위 정의대로
     한다 -- **피검 도구 모듈(`mutate_changed`)을 import하지 않는다**. 자리표시자가 든 파일은 참조 대상이 될 수 없다(순환 금지 -- 참조 파일에 자리표시자가 있으면 `RuntimeError`).
     참조 경로가 그 사전에 없거나 qualname def가 없으면 `RuntimeError`(조용한 통과 금지 -- 그 단계 ERROR). 기존 `subst_str`의 `@{…}`(상태 변수)와 겹치지 않는 문법이다(`@{BINDHASH:…}`는
     `subst_str`가 상태 변수 `BINDHASH`로 읽어 '치환 변수 없음'으로 실패한다 -- `rt.py` 39~48행 정규식). 자리표시자가 없는 케이스의 동작은 그대로다.
   * 관찰 `"observe": "out_jsonl"`: rt.py가 도구 명령 끝에 `--out <$WORK/vout/<단계 이름>.jsonl>`을 더하고(실행 전 그 파일이 있으면 지운다), 실행 뒤 `observed` =
     `{"lines": <줄 수>, "by_result": {<result>: [id 오름차순]}}` -- `by_result`는 `result`가 `killed`·`survived`가 아닌 레코드만(이 card 뒤 `exempt`, 범위 card 뒤 `not_targeted`). 파일이 없으면
     `{"lines": 0, "by_result": {}}`. 줄이 JSON 객체가 아니면 `RuntimeError`(그 단계 ERROR). `observe` 키가 없거나 다른 값인 케이스의 동작은 그대로다(`v4_first`·`tool_tmpdir`·`root_state` 불변).
10. **문서**: design 05 §10 V3 행 ⑤의 "등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록"을 "등가 변이 면제는 `target_kind: decision`, `target` 원소 =
    `<변이 id>@<묶기 해시>`(승인할 때 head def 노드 원본 -- docstring 포함 -- 의 `ast.dump` sha256, 정의: spec card `20260930-v3-exempt-binding`)인 승인 기록 -- head의 그 def 묶기 해시가 같을
    때만 적용. 해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다"로 고친다. 계획 N4.2 V3 행의 "등가 변이 면제는 승인 기록으로만"을 "등가 변이 면제는
    승인 기록으로만(변이 id와 그 def의 AST 묶기 해시에 묶임)"으로 고친다. design 10 §6.7 IC3 (C8) 항목(382행) 끝 "`target_kind: decision` 승인 기록(변이 id 목록)으로만 면제한다(N4.2 V3)"를
    "`target_kind: decision` 승인 기록으로만 면제한다(N4.2 V3. 원소 형식은 design 05 §10 V3 ⑤ -- 2026-10-01부터 `<변이 id>@<묶기 해시>`)"로 고친다(규칙 문장이 옛 원소 형식을 말하므로 -- 검토 M4).
    `mutate_changed.py` 모듈 docstring ⑤도 같은 뜻으로(code-author). 계획 N4.2의 이 칸은 `plan_tables_hash` 입력이 아니다(`merge_gate.plan_tables_object`는 `v_intro`·`ic_parts`·`ic_test`·
    `phase_order`·`write_paths`만, `v_intro`는 N4.2 '도입' 칸만 -- 실측 `merge_gate.py` 123~133·158~168행).
11. **실수 표기**: 실수 상수의 원문 표기만 다른 def(`x * 0.5`와 `x * 0.50`)는 AST가 같아 묶기 해시가 같지만, 같은 id `const+:…`의 변이 값은 표기 단위에서 나온다(`0.6` 대 `0.51` --
    `mutants`의 `_float_unit`). 그래서 묶기 해시가 보장하는 것은 '같은 노드'이고 '같은 변이 값'이 아니다. 실수 상수 변이의 등가 판단은 **표기와 무관한 경우에만** 승인한다(승인 기록 범위 설명에
    적는다). 실제 발생 가능성은 낮다(같은 card 재시도에서 표기만 바꾸는 경우). 도구 동작은 이 문장 때문에 바뀌지 않는다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 9 (a)는 base 도구에서 exit 0(해시 없는 면제를 경로만으로 적용), (c)는 base 도구에서 exit 1(`@` 원소를 모른다) -- 둘 다 red, 병합본 도구에서 green. design 05 §18: ⑤ 뒤 게이트 변경은
spec card(red-green, oracle (a)). (b)·(d)·(e)·(f)는 base·병합본 모두 exit 1인 회귀 방지 단계이고, X가 유일 생존이라 해당 규칙을 빠뜨린 구현에서는 exit 0이 된다(판별력).
단 하네스 단계 판정으로는 (b)·(d)·(e)·(f)도 base 도구에서 FAIL이다(base 출력에 `exempt_ignored` 조각이 없다) -- 판정 기록의 red 집합(base에서 FAIL인 단계)은 6단계 전부이고,
그중 exit 자체가 base와 다른 단계가 (a)·(c)다.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py`의 V 케이스 -- `build_vrepo`가 `base` 사전으로 base 커밋, `head` 사전으로 head 커밋을 만든다)에서 생존 변이 집합이 구성으로 정해진 def를 쓴다.
승인 기록은 `head`(또는 `base`) 사전의 `.ai/approvals/<id>.md` 파일이다(V 케이스는 `_commit_case`의 `approval`·`more_approvals`·`base_files` 키를 읽지 않는다 -- `rt.py` 446·459행, `build_vrepo` 523행~).
기대 exit·출력 조각은 이 card 계약 문장. **묶기 해시 기대값은 피검 도구 함수를 불러 만들지 않는다** -- test-author가 계약 머리의 정의(표준 `ast.dump` 인자 명시 + sha256)로 rt.py 자리표시자
`@bindhash(…)`(계약 9)에서 독립 계산한다. 같은 인터프리터(`$PY` 3.14)에서 계산한다.

## 거부해야 할 입력

해시 없는 원소로 면제된 변이가, 그 def가 바뀐 head에서 생존 → exit 1(계약 9 (a)). 다른 해시·다른 def의 해시·docstring만 다른 def의 해시·형식 오류 해시를 단 원소 → exit 1(계약 9 (b)·(d)·(e)·(f)).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

기존 redteam 전체(`run_all.py --phase 0.5 --mode direct`)와 `--cases 0.5`의 케이스 판정이 base와 같다(계약 9의 새 케이스 제외). 승인 기록이 없는 저장소의 V3 판정·`survivors`가 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

* **사용자 승인 완료(2026-10-01 A1-a "승인 (Recommended)")**: 승인 기록 `20260930-v3-exempt-binding`(`target_kind: diff`, 이 card + interface card + design 05 §10 V3 ⑤ + 계획 N4.2 V3 문구 +
  design 10 382행 문구 커밋). 범위 설명에 적을 것:
  (i) 강화: 면제 적용 범위 축소. 기존 `20260922-ic3-v3-exempt`의 V3 원소 14개는 해시가 없어 더는 적용되지 않는다(앞으로의 card 기준 무손실 -- '작성 전 실측' 1. 이미 내려진 DF-36 V3 PASS는
  그 4개에 기댔다 -- 백로그 B41). V3 대상 영역 밖의 V3 모양 원소(auditor 보충 뮤테이션 면제, `19eb475` 기준 `20261001-p10b-v3-equiv` 9개)는 도구가 만들지 않는 id라 영향이 없다(범위 밖 절).
  (ii) redteam `lib/rt.py`에 실행 동작 두 개 추가(자리표시자 `@bindhash(…)`, 관찰 `"observe": "out_jsonl"` -- 계약 9) -- 선례 C10(`20260923-caa970b-replay`)처럼 승인 범위에 따로 적는다.
  (iii) 묶기 해시는 gate 인터프리터(3.14)의 `ast.dump`(인자 명시)로 잰다. 인터프리터 판을 올리면 묶인 면제가 풀릴 수 있다(fail-closed) -- 그때 필요한 면제는 다시 승인한다.
  (iv) **운영 비용**: 승인한 def를 재시도에서 고치면(docstring만 고쳐도) 면제가 풀려 **시도마다 재승인**이 필요하다. 의도된 동작이다(승인한 코드와 다른 코드에 면제를 쓰지 않는다).
  (v) 실수 상수 변이의 등가 승인은 표기와 무관한 경우에만(계약 11).
* 백로그(오케스트레이터가 더한다):
  1. (B41) DF-36 V3 확인: HEAD에서 `save_instance_json` 면제 id 4개(`scope_note` 분기 2, `indent` ±1 2)를 실제로 돌려 생존이면 test 보강(B8과 같은 기존 공백) 또는 묶인 면제 승인. 판정 기록은 고치지 않는다.
  2. V7 면제 원소를 def 해시에 묶기(누수 조건 = 같은 qualname 삭제 후 재추가, 지금 영향 0).
  3. V4 면제 원소를 test 함수 해시에 묶기(기존 2원소의 이행 설계 필요 -- V4는 바뀐 파일의 모든 test를 보므로 fail-closed가 무손실이 아니다).
  4. `reachability._approved_ids`는 머리 블록만이 아니라 **파일 전체**에서 `target: `로 시작하는 줄을 읽는다(본문 줄도 원소가 된다 -- 묶기 뒤에도 남는 위조 경로).
  5. 같은 qualname의 def가 둘인 경우(`@x.setter`, 조건부 정의): `changed_defs`의 `bmap`이 마지막 것만 남기고 변이 id가 겹친다. 묶기 해시로 면제는 구분되지만 대상 선택은 틀릴 수 있다.
  6. 관찰: 도구는 중첩 def의 노드를 바깥 def 변이로도, 해시가 바뀐 중첩 def 자신의 변이로도 만든다 -- B26-1 시뮬레이션 head에서 `optimize_full_circuit_budget` 안의 `_evaluate_row_split`
     62개가 두 id로 두 번 돈다. 판정은 같고 비용만 는다.
  7. auditor 보충 뮤테이션 면제(V3 대상 영역 밖 파일 -- 첫 사례 `20261001-p10b-v3-equiv`, `tests/tools/reg_check.py` 9개)의 묶기: 도구가 읽지 않아 이 card의 규칙이 닿지 않는다. 지금은 그 기록의
     범위 설명("2차 시도 auditor가 병합본에서 각 id를 다시 만들어 여전히 등가라고 판정한 것에만")이 유일한 묶음이다. 원소 형식을 `<id>@<묶기 해시>`로 맞추고(해시는 이 card 정의, 경로는 보충
     뮤테이션 대상 파일) auditor 절차에 '해시 같을 때만 적용'을 넣을지 정한다.
* redteam 번호는 D-18 배정(34). 범위 card(35)가 같은 rt.py `out_jsonl` 관찰을 쓴다(그 card는 rt.py를 더 고치지 않는다).

## 작성 전 실측

(측정 2026-10-01, gate `master` HEAD `7535799`. **재확인 2026-10-01 gate `master` `a796468`**(격리 복제본 `C:/g102`, 저장소 쓰기 없음): `tools/` 차이 0이라 도구 줄 번호·동작 문장은 그대로이고,
승인 기록 집계(아래 셋째 항목)와 해시 앵커 표의 P9 병합 커밋을 고쳤다(`b7765b0`은 gate `master`의 조상이 아닌 1차 병합 -- 실제 P9 병합은 2차 `93b18db`).
**재확인 2026-10-01 gate `master` `0f23786`**(격리 복제본 `C:/g119`): `a796468..0f23786` 차이는 `.ai/approvals/20261001-p10b-v3-equiv.md` 추가와 P10b spec card 개정뿐(`tools/`·엔진 소스 차이 0) --
도구 문장·줄 번호·해시 앵커 그대로, 승인 기록 집계(셋째 항목)를 측정 명령 출력으로 바꿨다.
**재확인 2026-10-01 gate `master` `19eb475`**(격리 복제본 `C:/g158`): `0f23786..19eb475` = P10b 재시도 3차(`572d767`·`b7b1e00`·병합 `54ef51c` -- `tests/tools/reg_check.py`·
`tests/contracts/test_reg_check_df23.py`·레지스트리), 판정 기록 `afcf36c`, 문서 커밋 7개(`58024de`..`19eb475`, 승인 기록 `20261001-b47-md-sync`·`20261001-p2dod-e2-wording`(diff)·
`20261001-b26-backfill-interdig-fix` 추가). `git diff --name-only 0f23786 19eb475 -- tools/ skills/analog-gmid-design/assets/stick_diagram.py` 비어 있음, design 05·design 10·계획서·
`engine_dup_scan.py`·`agents/` 차이 0 -- 아래 도구 줄 번호(전부 다시 읽어 대조)·해시 앵커·문서 패치 대상 줄 그대로. 집계(셋째 항목)와 계획서 소비자(5)를 측정 출력으로 바꿨다. 저장소 쓰기 없음, scratch `C:/g60`(`git archive 7535799` 사본 + 스크립트, 끝나면 삭제). 스크립트·출력 사본은
`wt/_drafts/v3_scripts/`(재현 방법은 그 폴더 `README.txt`). `$PY` = `C:/Python314/python.exe -B`(3.14.2). 도구 함수는 저장소 `tools/gates`에서 읽기 전용 import, 도구 `main`은 돌리지 않음.)

1. **사실 문장 재측정.**
   * 도구 읽기: `mutate_changed.py` `main`의 `approved = _approved(root, ns.head)`·`if mid in approved:` → `results.append({"id": mid, "result": "exempt"})`·`continue`(375~377행 -- `--out`
     append(394~396행)를 건너뛴다), `_approved` = `rch._approved_ids(root, rev)`(218·219행). 출력 JSON(407~408행) = `json.dumps({"tool", "verdict", "targets", "mutants", "killed", "survivors"},
     ensure_ascii=False)`, `--out` 줄도 `ensure_ascii=False`(396행). `reachability._approved_ids`(180행)는 head 트리 `.ai/approvals/*.md`(이름이 `_`로 시작하는 것 제외) 중
     `---\n`으로 시작하고 `\ntarget_kind: decision\n`이 있는 기록의 `target: ` 줄을 쉼표로 나눠 합집합. 소비처 3곳: `mutate_changed._approved`(V3, 219행), `reachability.main`(V7, 233행),
     `test_lint.py` 731행(V4 규칙 (1)) -- `grep -rn "_approved_ids" tools/ skills/`. decision `target`을 따로 읽는 넷째 소비처 `A/tests/tools/engine_dup_scan.py`(102~122행, `<path>::<rule>`
     집합 비교 -- `@` 원소와 겹치지 않음. 함수 `_read_exemptions` 101~123행 -- 이전 판 인용 '102~122'를 `19eb475`에서 다시 읽어 고침, `0f23786`에서도 같은 줄).
   * 승인 기록 머리 파서: `merge_gate.parse_approval_header`는 모르는 키를 거부하고(APPROVAL_KEYS 8개), decision `target` 원소는 비지 않음만 검사한다 → `@` 원소 허용, 새 키는 불가(그래서 새 키
     대신 원소 접미사).
   * **decision 기록 집계 -- 고정값이 아니다.** gate `master`에 승인 기록이 계속 더해지므로(이 card 착수 전에도 P10b 판정·`20261001-b47-md-sync` 등) 수치는 측정 커밋과 함께만 적고,
     **착수 0단계에서 아래 명령으로 다시 잰다**(읽기 전용 -- `git ls-tree`/`git show`만, `reachability.py`도 `<rev>` 판을 `git show`로 읽어 메모리에서 실행):
     ```
     C:/Python314/python.exe -B <wt>/_drafts/v3_scripts/v3_decision_census.py --repo <저장소 또는 격리 복제본> --rev "$(git -C <저장소> rev-parse gate/master)" --out <scratch>/census.txt
     ```
     출력: decision 기록 수·이름·기록별 원소 수와 V3 모양 수, 자체 합집합 == `_approved_ids(<rev>)`(다르면 exit 1), V3 모양 원소마다 모듈 경로·V3 대상 영역(`_is_source`) 여부·`@` 접미사 유무·
     그 def 묶기 해시 앞 16자.
     **measured at `19eb475`**(격리 복제본 `C:/g158`, exit 0): decision 기록 **15**, 원소 **38**(`_approved_ids`와 같음), V3 모양 **23** = V3 대상 영역 **14**
     (전부 `20260922-ic3-v3-exempt` -- `load_topology` 10, `save_instance_json` 4) + 대상 영역 밖 **9**(전부 `20261001-p10b-v3-equiv` -- `tests/tools/reg_check.py`, 범위 밖 절). `@` 접미사 원소 0.
     나머지 15: 결정 id 10, V4 test id 2(`20260923-c9-v4-exempt`), V7 def id 2(`20260930-restore-unwired-until-6a`), probe 스캐너 1(`20260929-p4-scan-exempt`).
     `0f23786` 뒤 새 decision 기록 2개는 원소가 결정 id 하나씩이다(`20261001-b47-md-sync` = `B47-MD-SYNC`, `20261001-b26-backfill-interdig-fix` = `U-BF-BACKFILL-INTERDIG` -- V3 모양 아님, `@` 없음).
     `20261001-p2dod-e2-wording`은 `target_kind: diff`라 decision이 아니다(`20260923-v4-decision-exempt`도 diff).
     이전 판: `0f23786` 13·36·23(대상 영역 14 + 밖 9, 출력 `v3_scripts/out/v3_decision_census_0f23786.txt`), `a796468` 12·27·14(대상 영역 14, 밖 0). (`7535799` 측정 `v3_anchors.txt`는 11·26 --
     `2d58fd8`이 `20260930-b26-before-phase3`를 더했다.) `19eb475` 출력 사본은 남기지 않았다(같은 명령으로 재현 -- 착수 스크립트 `_drafts/v3_binding_launch.sh`의 `pre` 단계가 매번 다시 재고
     위 수치와 다르면 멈춘다).
     **착수 때 다시 볼 판단**: 이 card 문장이 기대는 것은 수치 자체가 아니라 (가) V3 대상 영역 V3 모양 원소가 `20260922-ic3-v3-exempt` 14개뿐이고(이행 근거), (나) `@` 접미사 원소가 0이며,
     (다) 대상 영역 밖 원소는 도구가 만들지 않는 id라는 것이다. 0단계 출력에서 (가)·(나)가 깨지면(새 V3 대상 영역 면제 기록이 생기면) 그 원소의 이행 근거를 card에 더한 뒤 착수한다.
     `19eb475` 판정: (가) 성립(대상 영역 14 = `stick_diagram` `load_topology` 10 + `save_instance_json` 4, 다른 기록의 V3 모양 원소는 `20261001-p10b-v3-equiv` 9개뿐), (나) 성립(0),
     (다) 성립(9개 모두 `skills/analog-gmid-design/assets/tests/tools/reg_check.py` -- `_is_source` 밖, basename `reg_check` 경로 하나, `mutate_changed.py` 315행 `targets` 필터).
   * **해시 앵커**(앞 16자, ① = `def_hash` docstring 제외, 묶기 = 계약 머리 정의) -- `v3_anchors.txt`:

     | def | 58e954c(C8 승인 커밋) | 6fe9cff(C8 병합)·070cf69 | b29be01(DF-36 병합)·cd64170·7535799·93b18db(P9 병합)·a796468·0f23786·19eb475 |
     |---|---|---|---|
     | `load_topology` ① | `104fac77…` | `c22bdd32…` | `c22bdd32…` |
     | `load_topology` 묶기 | `0b9eb2d6…` | `7e81d370…` | `7e81d370…` |
     | `save_instance_json` ① | `0f519721…` | `9cb09766…` | `11a55c19…` |
     | `save_instance_json` 묶기 | `043c6c88…` | `1dbcaa2d…` | `4a96ecf0…` |

   * **이행 근거(앞으로의 card 기준, 해시 없는 원소를 적용하지 않아도 잃는 것이 없다)**:
     * `load_topology`: 면제가 승인한 형태(C8 병합 `c22bdd32…`)가 지금 base다. V3는 base와 ① 해시가 다른 def만 변이하므로 뒤 card가 `load_topology`를 대상으로 삼는 순간 head ① 해시는
       `c22bdd32…`가 아니고 묶기 해시도 `7e81d370…`가 아니다 -- 어떤 앵커를 붙여도 적용되지 않는다. fail-closed와 결과가 같다.
       (참고: B26-1 시뮬레이션 head에서는 `load_topology` 본문 앞쪽에 문장이 들어가 C8 경로 10개가 이미 다른 경로가 된다 -- 지금 도구로도 면제되지 않는다(`b26_v3_measure.out.txt` leak2:
       B26-1 head 적중 4개 = `save_instance_json`뿐). 좁힌 B34(def 4개)는 `load_topology`를 대상으로 삼지 않는다 -- `v3_scope_classify.txt`.)
     * `save_instance_json`: 승인 커밋 = `0f519721…`, C8 병합 = `9cb09766…`, `b29be01`에서 `11a55c19…`로 바뀜. 승인한 형태는 이미 지나갔는데 지금 도구는 4개를 여전히 적용한다
       -- DF-36(`070cf69` → `b29be01`)에서 실제로 적용됐고(의도 절), B26-1 시뮬레이션 head에서도 4/4 적중한다(leak2). fail-closed가 C8 범위 설명과 맞다.
     * **암묵 앵커(승인 커밋의 def 해시)는 틀린 앵커다**: V3 승인 기록은 card 병합 **전**에 master에 커밋된다(`58e954c` → 병합 `6fe9cff`) -- 승인 커밋의 def는 card 전 형태(① `104fac77…`)다.
       V7 기록 `c31e0b6`에는 두 def가 아예 없다(`no-def`; 복원 병합은 `f1c4b7d`). 병합 커밋 앵커는 승인 기록에 card id가 기계 판독으로 없어 정할 수 없다.
   * **docstring 경로 밀림 재현**(`v3_probes.py` → `v3_probes.txt`): `def f(x): y = clamp(x); log(y); return y`와 docstring만 더한 판 -- ① 해시 같음(True), 묶기 해시 다름(False),
     `stmt_delete:body[1]` = `log(y)` 대 `y = clamp(x)`, `body[2]` = `return y` 대 `log(y)`. 두 판의 (연산자, 경로) 집합이 겹친다 -- ① 해시로 묶으면 밀린 문장에 면제가 적용된다.
     2차 검토(`review2_v3_cards.md` §1)가 같은 정의를 프로토타입으로 구현해 같은 결과와 원소 분리 규칙(`X@<0*64>`·`X@H`·`X` → exempt, `X@abc`·`X@a@b` → malformed, 대문자 16진 → malformed)을 확인했다.
   * `ast.dump` 서명(3.14.2 실측): `(node, annotate_fields=True, include_attributes=False, *, indent=None, show_empty=False)` -- `show_empty`는 3.13에서 생겼다(그 전 판에는 인자가 없다 --
     다른 판 인터프리터는 이 환경에 없어 출력 차이는 재지 않았다. 계약은 판 변경을 fail-closed + 재승인으로 다룬다).
   * 실수 표기(계약 11): 2차 검토 실측 -- `return x * 0.5`와 `x * 0.50` 묶기 해시 같음(True), 같은 id 변이 값 `0.6` 대 `0.51`.
   * B26-1 → B34(v1) 누수 619/1,402: `_drafts/b26_v3_leak.py`·`b26_v3_measure.out.txt`(C:/g39, cd64170) -- 재사용(auditor 측정 재사용 규칙). 엔진 소스가 HEAD와 같아 다시 재지 않았다.
   * DF-36 V3 basis(판정 기록 `checks.V3.basis`): 도구 직접 실행은 사본에 `.git`이 없어 기준 실행 ERROR, 대체 측정(`scripts/mut_def.py`, 도구 함수 그대로)으로 26 → killed 22·exempt 4·생존 0.
2. **이름 충돌.**(`19eb475` 재확인 같음) `ls tools/gates/redteam/attacks/` 마지막 = `31-v3-git-history`, 32~35 없음 → `34-v3-exempt-binding` 없음(번호는 D-18 배정, G1 `32-moved-defs`·B33 `33-v7-registry-edges`와 다름).
   출력 키 `exempt_ignored`·`survivor_bindings`·`bind_hash`: `grep -rn "exempt_ignored\|survivor_bindings\|bind_hash" tools/ docs/` 0건. rt.py 자리표시자 `@bindhash(`: `grep -rn "@bindhash" tools/` 0건.
   rt.py 관찰 값 `out_jsonl`: 지금 `observe` 값은 `v4_first`뿐이고(`rt.py` 613행) 그 밖의 선택 관찰은 `tool_tmpdir`·`root_state` 키(616~621행) -- 겹치지 않는다. G1 초안의 `observe: "moved"`와도 다르다.
3. **원칙의 계약화.** 조용한 면제 금지 → 계약 2·3(적용하지 않은 원소를 출력에 싣는다)과 9 (a). 거부 집합이 실제로 넓어짐(WP-02) → 계약 9 (a)·(b)·(d)·(e)·(f) attack(X 유일 생존으로 판별).
   다른 도구 무영향 → 계약 7. 기록 누락 금지(WP-11) → 계약 1의 `--out`과 9 (c)의 `out_jsonl` 관찰(회귀 방지). oracle 독립 → 계약 9의 rt.py 자리표시자(피검 모듈 import 금지).
4. **쓰기 경로.** `tools/gates/mutate_changed.py` = gmid-code-author(design 10 C11 행 "spec card `gate_change: yes` + 승인 기록일 때"), `tools/gates/redteam/**`(새 케이스 + `lib/rt.py` 자리표시자·관찰)
   = gmid-test-author(C10 행), design 05 §10·design 10 382행·계획 N4.2 문구 = 오케스트레이터 문서 커밋(승인 기록이 덮는다). 설치 사본 재설치 불필요(`mutate_changed.py`는 §4.4 캐시에서 실행 -- B28 card와 같음).
5. **계획서 소비자.** `grep -rn "변이 id" docs/01-plan docs/02-design` → design 05 317행(고침), design 10 382행(C8 항목의 규칙 문장 "(변이 id 목록)으로만 면제한다" -- 원소 형식을 말하므로 계약 10에서 고침),
   P9 spec card 118·168행(면제 형식 언급 -- 병합된 기록이라 고치지 않음). agent 정의(`agents/gmid-verification-auditor.md` 41행)는 도구 이름만 -- 고칠 것 없음. 지우거나 옮기는 이름 없음.
   `19eb475` 재측정(`git grep -n "변이 id" 19eb475 -- docs/01-plan docs/02-design`)에서 더 나온 줄 -- 모두 규칙 문장이 아니라 고치지 않는다: history 336행(A1-a 결정 이력)·392행(DF-36 면제 4 이력),
   P10b spec card `20260930-df23-registry-record` 78·154행(auditor 보충 뮤테이션 면제 `20261001-p10b-v3-equiv` 적용 방법 -- 병합된 card, 범위 밖 절), md 일치 spec card `20261001-topology-md-sync`
   153행(결정 id `B47-MD-SYNC`가 어떤 변이 id와도 같지 않다 -- 이 card 뒤에도 참).
6. **미배선.** 새 def(묶기 해시 계산, 원소 분리)를 만들면 `mutate_changed.main`이 부른다(V7 면제 불필요).
7. **기존 계약 test.** redteam `v3_survivor`·28·31·26·27f·29 -- 계약 8로 불변 판정. 기존 redteam에 V3 면제를 쓰는 케이스 없음(검토 `grep` 0건). `tests/`의 엔진 test는 도구를 부르지 않는다.
   게이트 도구에는 redteam 밖 unit test가 없다(`tools/gates/` 실측) -- `--out` 기록은 그래서 rt.py `out_jsonl` 관찰로 고정한다(계약 9).

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260930-v3-exempt-binding.spec.md`.
