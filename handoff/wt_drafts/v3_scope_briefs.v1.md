# V3 범위 정책 card `20260930-v3-changed-stmt-scope` -- 착수 키트(세 역할 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` `0f23786`(P10b spec card 재시도 개정). 저장소 쓰기·상태 변경 git 없음. 측정·모의는 격리 복제본 `C:/g109`(origin 제거, 빈 hooksPath, 끝나고 삭제)에서만.
선행 card: 면제 묶기 `20260930-v3-exempt-binding`(키트 `v3_binding_briefs.md`) -- **이 card는 그 card의 병합·정리 뒤에 시작한다.** 이 키트는 묶기 card의 '의도한 결과'(그 spec card 계약 1~11, 그 키트 §2.1)를
base로 가정한다(§0.4).
대상 산출물: `draft_v3_scope_policy.spec.md`(재검증 반영판 v4, 직전판 `.spec.v3.md`), `approval_20260930-v3-changed-stmt-scope.md`(수치 갱신, 직전판 `.v1.md`), `v3_cards_commit_plan.md` §4.2,
`patch_v3_scope_docs.py`, `fill_v3_approval.py`. 측정 스크립트·출력: `v3scope_kit/`(README는 이 문서 §5).

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(HEAD `0f23786`) -- 고친 것

| 확인 | 결과 | 조치(v3 → v4) |
|---|---|---|
| `tools/` 변경(`7535799` → `0f23786`) | 차이 0(`a796468..0f23786`은 test 2파일·문서·승인 기록뿐) | 도구 사실 문장 그대로 |
| 엔진 소스 | `7535799` 뒤 P9 병합 `93b18db`만(`2d58fd8..0f23786` `skills/` 차이 = test 2파일) | B26-1 모의 base를 `0f23786`(+B34 코드)로 재측정 |
| design 05 317행 ①·318행(V4), 계획 839행 V3·533행 이동 규칙, design 05 §2 표 65행 'V3~V7' 판정 기준 소유 `사용자` | 일치 | -- |
| `merge_gate` N4.2 읽기 | **123~133**·`plan_tables_object` 158~168(card 124~133) | 계약 10 줄 번호 고침 |
| `mutate_changed.py` | `changed_defs` 88~100(`bmap` 90~95), `_replace_def` 196~206(`fn.lineno` 199, `decorator_list = []` 203), `main` base 읽기 359~361·`changed_defs` 호출 364 | 실측 8에 "`0f23786` 줄 번호 -- 묶기 card 병합 뒤 다시 잰다" |
| 계약 7 무동작 목록 | `v3_survivor`·28·31은 모든 단계가 새 def `rt_scale`(실측). **26은 없는 리비전(ERROR 경로), 27f는 도구 소스 AST 검사** -- '새 def'가 아니다 | 계약 7 문장 고침 |
| G1 연결 문장(계약 3, B45) | G1 초안 v7(`draft_p3_g1.spec.md` 97행)이 이미 "def 안의 변이 선택은 … 계약 1 그대로"를 담음 | "G1 초안 v7 계약 4에 반영됨"으로 |
| redteam 번호·새 이름 | `attacks/` 마지막 `31-v3-git-history`, 35 없음. `not_targeted`·`targets_by_def`·`def_header_changed` `tools/`·`docs/` 0건 | -- |
| 계약 1 해석 자리(독립 프로토타입을 쓰며 발견) | `replace` 짝 후보가 여럿일 때 순서, 새·지운 복합문이 바꾸는 이름의 범위, 매개변수 '위치'의 뜻이 문장에 없었다. 어느 해석이든 B26-1 수는 같다(`out/variants.txt`) | 계약 1에 확정 문구 3개(실측 11) |
| 계약 4·5와 묶기 card | 변이 하나의 처리 순서, `--out`의 `not_targeted` 레코드 순서가 없었다 | 계약 4에 ①대상 판정 → ②면제 판정 → ③실행, 계약 5에 '생성 순서대로(대상 레코드와 섞여)' |
| 계약 5 `targets_by_def` 키의 `<파일>` | 경로인지 basename인지 없었다 | `targets`의 저장소 상대 경로로 |
| 계약 8 (f) 기대 조각 | "`survivors`: [대상 변이 id 전부, **도구 생성 순서**]" -- test-author는 도구 소스를 볼 수 없어 생성 순서를 기대값으로 만들 수 없다(oracle 독립 위반 소지) | `"verdict": "FAIL"`·`"mutants": <n>`·id마다 `"<id>"`(순서 무관)로 |
| B26-1 수치 | §0.2 | 실측 1·2·3·4, 의도 절 '판단' 문장, 승인 초안 재측정 문단 |

결정을 바꾼 것은 없다(규칙 = A1-b ② N2 + A1-b 정정 '넓힌 T6' 그대로). 위는 사실 정정·해석 고정·oracle 실행 가능성 보정이다.

### 0.2 B26-1 변이 수 재측정(N2(b) + 넓힌 T6, gate `master` `0f23786`)

방법: 계약 1 문장만 보고 새로 쓴 독립 프로토타입(`v3scope_kit/scope_proto.py` -- 이전 분류기 `v3_scope_widen`을 import·복사하지 않음)을 격리 복제본의 모의 커밋에 도구 `main`과 같은 경로
(`git diff --name-only --no-renames --diff-filter=AM` → `rch._is_source` → `changed_defs` → `mutants` → 변이 id)로 적용(`measure_b26.py`). pytest는 돌리지 않음.

| head(모의) | 바뀐 def | 지금(def 전체) | 승인 당시 N2(T6 = 바로 뒤만) | **이 card(넓힌 T6)** | 하한 ~ 상한 | 현실 하한 |
|---|---|---|---|---|---|---|
| **B26-1 card v4**(정본: 인계 9·10b·13·B40, 사이트 10·14는 B35. base = `0f23786` + B34 코드) | 32(새 1) | 2,442 | 235 | **301** | 25.1분 ~ 16.0 h | 0.89 h |
| B26-1 review2(인계 9·10·10b·13·14·B40, 같은 base) | 32(새 1) | 2,437 | 265 | **330** | 27.5분 ~ 17.6 h | 0.93 h |
| B26-1 옛 시뮬레이션(`7535799` + `build_b26` -- 승인 질문의 228) | 31(새 1) | 2,472 | 228 | **294** | 24.5분 ~ 15.6 h | 0.88 h |
| P9 실제(`6bf510b..93b18db`) | 2 | 28 | 12 | **12** | 1.0분 ~ 0.64 h | -- |
| B34 좁힌 초안(`0f23786` → B34 코드) | 4 | 55 | 10 | **10** | 0.8분 ~ 0.27 h | -- |

* **사용자 보고용 한 줄**: "넓힌 규칙으로 B26-1 대상 변이는 **301개**(B26-1 card v4 기준, 2,442개 중), 승인 당시 정의로는 235개입니다. 처음 알려드린 228 → 294는 옛 시뮬레이션 head 값이고,
  그 뒤 B26-1 card가 사이트 10·14를 B35로 넘겨 301이 됐습니다(넘기기 전 판이면 330). 직렬 실행 하한 25분, 현실 하한 약 0.9시간."
* 교차 확인: 이전 분류기(`b26_scripts` 사본, 같은 `0f23786` 모의 커밋)도 v4 301 / review2 330 -- 변이 id 집합 대칭차 **0**(N2b·N2w 모두). 적대 21건도 변이별 불일치 0.
* 상한·현실 하한: `0f23786` 트리 인벤토리(P10 test 포함) × `7535799` junit 시간 -- 시간 기록 없는 인벤토리 test 4개는 0초. 미실행 줄 대상 변이 9(N2b 6), 인벤토리 0 대상 6(`_metric_kcl_residual`).
* v4 def별 대상 상위: `propose_device_roles_gap_fill` 52, `run_matching_safety_with_finger_growth` 19, `refine_…` 17, `audit_vertical_stack_id_vs_kcl`·`load_topology` 16, `_branch_composite_pair` 15,
  `rail_declaration`(새 def) 14 -- 전체는 `v3scope_kit/out/measure_b26.txt`. B26-1 card v4 'V3 계획' 1의 표와 같다.
* 묶기 card는 이 수를 바꾸지 않는다(`tools/gates/**`는 `rch._is_source` 밖, 엔진 불변). 착수 때 `git diff 0f23786 <base> -- skills/analog-gmid-design/assets/*.py`가 비면 재측정 불필요.

### 0.3 모의 결과(`C:/g109/seq` = gate `master` `0f23786` 복제, `v3scope_kit/sim_sequence.py`, 결과 `out/sim_sequence.txt` -- **NG 0**)

| 단계 | 결과 |
|---|---|
| 0 범위 패치를 묶기 card 전에 | `patch_v3_scope_docs.py --check` exit 2(선행 card 문구 없음), 무쓰기 |
| 묶기 card A·B·C(전제 상태) | 문서 3파일 각 `1 1`, 멱등, interface card 13줄, `fill_v3_approval` → `gate_change_ok` HEAD True / HEAD~1 False, target == `diff_hash` == `compute_diff_hash`, `approved_hashes(HEAD)` 포함, diff_path 5 |
| 범위 card A 문서 | `--check` pending 2 → 적용 → `git diff --numstat` 계획·design 05 각 `1 1` → `Role: doc` 커밋 → 재실행 already-applied |
| 범위 card B spec+interface | v4 spec 사본 + `interface_card.py` **절대 경로 호출** exit 0, 13줄(두 표 빈 -- 게이트 card 선례 모양). `parse_spec_card`: phase 0.5, red-green, gate_change yes, approval = 자기 id |
| 범위 card C 승인 | `gate_change_ok` HEAD True / HEAD~1 False, target == `diff_hash` == `compute_diff_hash`, `approved_hashes(HEAD)` 포함, blob에 HTML 주석·CR 없음, diff_path 4 |
| 표·인용 | `plan_tables_hash` `7167e028…6d2596d` 불변, `_approved_ids` 36 불변, **spec card 계약 10 인용문 2개(356자·129자)가 패치된 design 05·계획 V3 행에 그대로**, design 05 V3 행 `|` 개수 불변 |
| EL4 | `merge_gate.py receive --git-dir <seq>/.git`: (old `0f23786` → 묶기 C) exit 0, (묶기 C → 범위 C) exit 0. 대조: 트레일러 없는 커밋이 `tools/gates/mutate_changed.py`를 고치면 exit 1 `[EL4 거부] … Role … 정확히 하나가 아니다`, spec card를 고쳐도 exit 1 -- 게이트가 실제로 거부함 확인 |

(모의 해시는 모의 커밋 id에 묶인 예시다. 복제본 `core.autocrlf=true` -- 패치는 줄 끝을 보존했다.)
주의: 이 모의는 묶기 card의 **코드·test·판정 커밋**(순서 2~8)을 모의하지 않았다. 범위 card 문서 패치 앵커·승인 기록·`gate_change_ok`는 그 커밋들에 닿지 않는다(문서 3파일·spec card·승인 기록만 읽음).

### 0.4 묶기 card 위에서 -- 가정과, 묶기 card 병합 뒤 다시 잴 것

이 card가 묶기 card와 같은 코드(`mutate_changed.main`의 면제·출력)를 고치므로, 범위 card spec·브리프는 다음을 **가정**한다(묶기 spec card 계약 1~11, 묶기 키트 §2.1 7항):

| # | 가정(묶기 card 병합본) | 범위 card가 기대는 곳 | 병합 뒤 확인(착수 전, 오케스트레이터) |
|---|---|---|---|
| A1 | 면제 판정이 '변이 하나 → (`exempt` 레코드 \| `exempt_ignored` 항목들)'을 돌려주는 한 곳에 있고, `main` 루프에서 그 호출 **앞에** 대상 판정을 넣을 자리가 있다 | 계약 4 처리 순서(①대상 → ②면제 → ③실행) | 병합본 `main` 읽기: 면제 판정 호출 위치, 인벤토리 없음 생존 분기와의 순서 |
| A2 | 출력 키 = `tool, verdict, targets, mutants, killed, survivors, survivor_bindings, exempt_ignored` | 계약 5(뒤에 `not_targeted`, `targets_by_def`) | 병합본 출력 `json.dumps` 키 순서 |
| A3 | `exempt` 레코드 `{"id","result":"exempt","bind_hash"}`가 `results`·`--out`에 들어가고 `mutants` = 결과 레코드 수 | 계약 5 `mutants` = 대상 변이 수(= `exempt`+`killed`+`survived`) | 병합본 `mutants` 계산 |
| A4 | `exempt_ignored`의 '이번 실행의 변이 id' = 대상 변이(묶기 card 용어 절이 이미 그렇게 적음) | 계약 4 마지막 문장 | 병합본에서 `exempt_ignored`를 만드는 위치가 대상 판정 뒤로 옮겨질 수 있는지 |
| A5 | rt.py `"observe": "out_jsonl"` = `{"lines": <줄 수>, "by_result": {<result>: [id 오름차순]}}`, `killed`·`survived` 제외, 실행 전 파일 삭제, 파일 없으면 `{"lines":0,"by_result":{}}` | 계약 8 (a)·(k)의 `observed_equals` | 병합본 `lib/rt.py` 그 분기 읽기(키 이름·모양이 다르면 범위 card 계약 8 문구를 맞춘 뒤 문서 커밋) |
| A6 | 34 케이스의 X는 base와 다른 문장 안 또는 `early_return`, (c)는 모든 문장이 다름 | 계약 7(34 결과 불변) | 병합된 `attacks/34-v3-exempt-binding/v.json`의 base·head 소스에 `v3scope_kit/binding34_under_scope.py` 방식 분류 적용(키트 예시 구성은 6/6·7/7 전부 대상 -- `out/binding34_under_scope.txt`) |
| A7 | 묶기 card가 `_replace_def`·`changed_defs`·`mutants`를 바꾸지 않는다 | 계약 9(데코레이터 치환)·변이 id 불변 | 병합본에서 세 함수 diff 0, 줄 번호 재측정(실측 8·계약 9 인용 줄) |

**다시 잴 것(묶기 card 병합 뒤, 범위 card 문서 커밋 전)**: ① 위 A1~A7 ② `patch_v3_scope_docs.py --root <R> --check` → pending 2·`plan_tables_hash` 불변(선행 문구 3개는 묶기 card 문서 커밋이 넣는다)
③ spec card의 `mutate_changed.py` 줄 번호(계약 9 문장은 줄 번호 없이 `fn.lineno`·`decorator_list = []`만 말함 -- 실측 8의 359~364·90~95만 갱신) ④ B26-1 수치는 엔진 변경이 없으면 그대로(§0.2 끝)
⑤ A5가 다르면 계약 8 (a)·(k) 문구만 고치고 이 키트 `sim_sequence.py`를 다시 돌린다.

### 0.5 착수 직전에 다시 볼 것

1. **지금 `role/*` 브랜치 3개**(`role/{audit,code,test}/20260930-df23-registry-record`, P10b 진행 중, 2026-10-01 실측). 순서: P10b → Phase 2 DoD → 묶기 card(순서 8 push·정리) → 이 card. `test -z "$(git branch --list 'role/*')"`.
2. 커밋 계획 §4.2의 `(cd "$R" && $PY tools/gates/interface_card.py … --out <상대>)`는 PreToolUse hook(`role_guard.py`)이 "`cd` 뒤 상대 경로 쓰기 대상"으로 거부한다(이번 작업에서 같은 꼴이 거부됨).
   **절대 경로 형태**(모의에서 사용):
   `C:/Python314/python.exe -B <R>/tools/gates/interface_card.py <R>/docs/02-design/specs/20260930-v3-changed-stmt-scope.spec.md --root <R> --out <R>/docs/02-design/specs/20260930-v3-changed-stmt-scope.interface.md`.
   같은 hook은 셸 변수·명령 치환이 든 리다이렉트·`rm` 대상도 거부한다 -- 정리는 리터럴 경로로.
   `gate_change_ok` 확인도 `(cd …)` 없이: `C:/Python314/python.exe -B -P -c "import sys;sys.path.insert(0,'<R>/tools/gates');import merge_gate as mg;print(mg.gate_change_ok(mg.TreeView(['-C','<R>'],'HEAD'),'20260930-v3-changed-stmt-scope'))"`.
3. spec card 사본은 v4(`draft_v3_scope_policy.spec.md`)를 쓴다 -- 모의는 이 판으로 했다. 문서 커밋 전 §0.4를 다시 보고 고치면 `sim_sequence.py`를 다시 돌린다(해시는 커밋마다 새로 계산).
4. 승인 초안 끝 주석의 '사용자 고지'(228 → 294 → 301)는 기록에서 지워지므로(fill이 지움) **사용자 보고로 따로** 한다(§0.2 한 줄).
5. 역할 커밋 트레일러: `--trailer "Role: …" --trailer "Change-Id: 20260930-v3-changed-stmt-scope"`. 문서 커밋은 `Role: doc`만.

### 0.6 오케스트레이터 메모(이 card 밖)

* **묶기 card 실측 드리프트**: `0f23786`에서 decision 승인 기록 **13개**, `_approved_ids` 원소 **36**, V3 모양 **23**(새 `20261001-p10b-v3-equiv`가 `reg_check` id 9개 -- 해시 없는 원소). 묶기 card '작성 전 실측' 1(12·27·14)과
  '결정 필요 항목 (i)'(V3 원소 14개)을 착수 전 갱신해야 한다. 묶기 병합 뒤 이 9개는 `unbound`(fail-closed) -- P10b가 먼저 병합되므로 P10b 판정에는 영향 없음, 뒤에 `reg_check`의 그 def를 고치는 card는 재승인 필요.
* history(H 절)로 옮길 경위: spec card v3 → v4 변경(§0.1 표), B26-1 수치 흐름 228 → 294 → 301(330).

---

## 1. test-author 브리프(gmid-test-author, §12 순서 2)

```
역할: gmid-test-author. change id = 20260930-v3-changed-stmt-scope (게이트 변경, red-green, phase 0.5).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-changed-stmt-scope-test (브랜치 role/test/20260930-v3-changed-stmt-scope). 모든 명령은 절대 경로로(git -C, cd 금지).
쓰기 경로: tools/gates/redteam/** 만(design 10 C10·C11 행 -- spec card gate_change: yes + 승인 기록). lib/rt.py는 고치지 않는다(이 card 승인 범위에 rt.py 동작 추가 없음 -- 묶기 card의 out_jsonl을 쓴다).
입력: interface card docs/02-design/specs/20260930-v3-changed-stmt-scope.interface.md(두 표 빈 13줄),
      spec card '관찰 가능한 계약' 용어·계약 1~8, 'oracle 종류와 출처'. 묶기 card spec(계약 9의 out_jsonl 관찰 모양).
열람 금지: tools/gates/mutate_changed.py(피검 도구) 소스. redteam 하네스(lib/rt.py·run_all.py)와 기존 케이스(v3_survivor, attacks/28·31·34)는 읽어도 된다.
기대값: 계약 1을 구성에 손으로 적용해 만든다. 피검 도구 출력을 복사하지 않는다(base 도구 출력은 red 확인용).
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20260930-v3-changed-stmt-scope" -m "test: …"
```

### 1.1 산출물

* `tools/gates/redteam/attacks/35-v3-changed-scope/`: `expect.json`(케이스 머리 -- 선례 `attacks/31-v3-git-history/expect.json`·`attacks/34-v3-exempt-binding/expect.json`: `"layer": "V3"`, `"modes": ["direct"]`,
  `"phase": "0.5"`, `"steps_from_records": true`, `basis`·`title`), `run.sh`(`rt vcase v.json`), `v.json`(V 케이스 11단계 (a)~(k)). 단계마다 `expect`에 `exit`, `layer`, `message_contains`(정확한 JSON 조각 목록 -- 각 조각을
  부분 문자열로 대조, `run_all.py` 92행), 필요하면 `observe: "out_jsonl"` + `observed_equals`, `basis`(계약 문장 출처).
* 출력 JSON은 `json.dumps(…, ensure_ascii=False)` 기본 구분자(`", "`·`": "`) -- 조각은 그 모양으로 쓴다(예 `"not_targeted": 4`, `"survivors": ["rt_engine:rt_b:stmt_delete:body[1]"]`).
* 변이 id = `<모듈>:<qualname>:<연산자>:<경로>`, 모듈 = 파일 basename 줄기(`rt_engine`). 경로 규칙(필드 이름과 목록 첨자를 `.`으로 잇고 def 노드 기준)은 기존 케이스의 id(`v3_survivor` 기대 조각)와 묶기 card 계약에서 읽는다.

### 1.2 단계(계약 8) -- 각 단계가 잡는 잘못된 구현

공통: attack은 **겨냥한 변이 X가 대상 변이 중 유일한 생존**(나머지 대상 변이는 그 단계 test가 모두 죽인다). 그래서 그 규칙을 빠뜨린 구현에서는 X가 대상 밖 → exit 0.

| 단계 | kind | 기대(exit, 조각) | 잡는 잘못된 구현 | 지금 도구(base) |
|---|---|---|---|---|
| (a) `unchanged-stmt-survivor` | control | exit 0, `"verdict": "PASS"`, `"survivors": []`, `"not_targeted": <n>`; `out_jsonl` → `{"lines": <대상+n>, "by_result": {"not_targeted": [<id 오름차순>]}}` | 대상을 좁히지 않는 구현, `not_targeted`를 `--out`에 안 쓰는 구현 | exit 1(S 생존) -- **red** |
| (b) `changed-stmt-survivor` | attack | exit 1, `"verdict": "FAIL"`, `"survivors": ["<X>"]` | 바뀐 문장을 대상에서 빼는 구현(T1) | exit 1 |
| (c) `enclosing-guard-survivor` | attack | exit 1, `"survivors": ["<X>"]` | 감싸는 제어문(T4)을 빼는 구현 | exit 1(생존 더 많음 -- 조각 불일치) |
| (d) `unwrapped-stmt` | attack | exit 1, `"survivors": ["<X>"]` | 들여쓰기만 바뀐 문장을 '바뀌지 않음'으로 보는 구현 | exit 1 |
| (e) `header-only-change` | attack | exit 1, `"survivors": ["<X>"]` | 머리만 바뀐 복합문(T2)을 빼는 구현 | exit 1 |
| (f) `header-default-bool` | attack | exit 1, `"verdict": "FAIL"`, `"mutants": <대상 수>`, 대상 id마다 `"<id>"`(순서 무관 -- v4 개정) | 대상 0개를 허용하는 구현(T5·T3 없음) | exit 1(`mutants` 다름) |
| (g) `delete-then-use` | attack | exit 1, `"survivors": ["<X>"]` | 삭제 지점 뒤 문장(T6 가)을 빼는 구현 | exit 1 |
| (h) `decorator-mutant-applied` | control | exit 0, `"verdict": "PASS"` | 데코레이터 변이를 소스에 반영하지 않는 구현(계약 9) | exit 1(데코레이터 NOOP 생존) -- **red** |
| (i) `same-block-later-use` | attack | exit 1, `"survivors": ["<X>"]` | T6를 '바로 뒤 문장'만으로 둔 구현(승인 당시 정의) | exit 1(생존 더 많음) |
| (j) `loop-carried-use` | attack | exit 1, `"survivors": ["<X>"]` | 반복문 본문 앞쪽(다음 회차) 규칙이 없는 구현 | exit 1 |
| (k) `cross-block-not-targeted` | control | exit 0, `"verdict": "PASS"`; `out_jsonl` → `by_result.not_targeted`에 Y 포함(목록 전체) | 다른 블록까지 넓힌 구현(승인 범위와 다른 규칙) | exit 1(Y 생존) -- **red** |

* base 표(auditor 순서 3)에서 exit가 다른 단계는 (a)·(h)·(k). (c)·(f)·(i)는 exit는 같고 조각이 달라 단계 FAIL, (b)·(d)·(e)·(g)·(j)는 키트 예시 구성에서는 base에서도 단계 PASS(같은 X 하나만 생존)다 -- 회귀 방지·판별력 단계.
  red 집합은 auditor가 base 표로 정한다(구성에 따라 달라진다).

### 1.3 검증된 구성 예(선택 -- 출발점일 뿐, 기대값은 계약으로 손으로 확인할 것)

2026-10-01 `C:/g109`에서 **프로세스 안 모의**로 확인(`v3scope_kit/redteam35_examples.py` → `out/redteam35_examples.txt`): 변이 = `0f23786` 도구 `mutants`, 치환 = 계약 9 판, test = 함수 호출(예외 = 죽음),
대상 = 키트 독립 프로토타입. 실제 하네스(pytest, 합성 저장소)에서는 test-author가 다시 확인한다. 모듈 머리(모든 단계 공통):
```python
"""rt."""
import functools

LOG = []


def rt_gain(gm, ro):
    """이득."""
    return gm * ro
```
(test는 `skills/analog-gmid-design/assets/tests/test_rt_*.py`, 선례 케이스처럼 `sys.path`에 assets를 넣고 import. `LOG`는 모듈 전역이라 test 안에서 길이 차이로 본다.)

| 단계 | base def → head def(바뀐 곳) | test가 보는 것 | X / 결과(이 card) | 대상 / 대상 밖 |
|---|---|---|---|---|
| (a) | `rt_calc(x)`: `LOG.append(x * 3)` / `t = x + 1` → **`x + 2`** / `return t` | `rt_calc(1) == 3`, `rt_calc(-4) == -2`(LOG는 안 봄) | 생존 0 → exit 0. 대상 밖 = `LOG.append(x * 3)`의 4개(`arith`·`const±`·`stmt_delete:body[0]`) | 6 / 4 |
| (b) | `rt_b(x)`: `t = x + 1` / `return t` → 사이에 **`LOG.append(t)`** 삽입 | `rt_b(1) == 2` | X = `stmt_delete:body[1]` | 2 / 5 |
| (c) | `rt_c(a, b)`: `r = 0` / `if a < b or True:` 안 `r = a + 1` → **`a + 2`** / `return r` | `rt_c(1, 5) == 3`, `rt_c(5, 1) == 7` | X = `cmp_flip:body[1].test.values[0].ops[0]`(`or True`로 등가 -- 진리값 부정 연산자가 없어 이 꼴) | 7 / 4 |
| (d) | `rt_d(x)`: `y = x + 1` / `if x > -1000:` 안 `LOG.append(y)` / `return y` → **if를 없애 `LOG.append(y)` 내어씀** | `rt_d(1) == 2` | X = `stmt_delete:body[1]` | 3 / 4 |
| (e) | `rt_e(xs)`: `out = []` / `for v in [w for w in xs if w > -3]:` 안 `out.append(v * 2)` / `return out` → 머리만 **`w > -1`** | `rt_e([0, 1, 2]) == [0, 2, 4]` | X = `const+:body[1].iter.generators[0].ifs[0].comparators[0].operand`(`-1`은 `UnaryOp(-, 1)` -- const+는 -2) | 5 / 6 |
| (f) | `rt_f(x, strict=False)`: `if strict: raise ValueError(x)` / `return x` → 기본값만 **`strict=True`**, test 없음 | (인벤토리 0) | 대상 = `stmt_delete:body[0]`(strict를 읽는 if의 몫), `early_return:body[0]` → 둘 다 생존, `"mutants": 2` | 2 / 2 |
| (g) | `rt_g(x)`: `LOG.append(x)` / `x = abs(x)` / `return str(x)` → **`x = abs(x)` 삭제** | `rt_g(3)` 호출 뒤 LOG 길이 +1(반환값은 안 봄) | X = `stmt_delete:body[1]`(바로 뒤 `return`). `early_return`은 LOG로 죽는다 | 2 / 1 |
| (h) | `rt_h(x)`: `return x * 2` → **`@functools.lru_cache(maxsize=128)` 추가** | `rt_h.cache_info().maxsize == 128`, `rt_h(3) == 6` | 생존 0(데코레이터 `const±` 2개가 계약 9 판으로 적용되어 죽음). 지금 도구는 그 2개가 NOOP 생존 → exit 1 | 3 / 4 |
| (i) | `rt_i(x)`: `mode = "fast"` → **`"exact"`** / `LOG.append(x)` / `if mode == "exact": r = x * 2 + 1` `else: r = x * 2 + 1` / `return r` | `rt_i(3) == 7`, LOG 길이 +1 | X = `cmp_flip:body[2].test.ops[0]`(두 가지가 같은 값 -- 등가, if 삭제는 `r` 미정의로 죽음). **승인 당시 정의에서는 X가 대상 밖** | 5 / 15 |
| (j) | `rt_j(xs)`: `out = []` / `acc = 0` / `for x in xs:` 안 `LOG.append(acc)`·`out.append(acc)`·`acc = x + 1` → **`x + 2`** / `return out` | `rt_j([1, 5]) == [0, 3]` | X = `stmt_delete:body[2].body[0]`(앞쪽 `LOG.append(acc)`). 승인 당시 정의·반복문 규칙 없는 구현에서는 대상 밖 | 8 / 5 |
| (k) | `rt_k(x)`: `y = 0` / `if x > 0:` 안 `y = x * 2` → **`x * 3`**, `LOG.append(y)` / `return y + 1` | `rt_k(1)`, `rt_k(-0.5)`, `rt_k(0.5)` 뒤 LOG 끝 두 값 `[3, 1.5]`(반환값은 안 봄) | 생존 0 → exit 0. Y = `return y + 1`의 변이(`arith:body[2].value`·`const±:body[2].value.right`·`stmt_delete:body[2]`) -- 대상 밖, 지금 도구에서는 생존 | 10 / 7 |

* 계약 8 (j) 문장은 X 예로 `out.append(acc - 1)` 안 상수 ±1을 들지만 그 꼴은 ±1 두 변이가 함께 살아 '유일 생존'을 만들기 어렵다 -- 위처럼 앞쪽 단순문의 `stmt_delete`를 쓰면 된다(계약 문장 "X(상수 ±1 등)" 범위 안).
* (k)는 계약 문장대로 `return y + 1` 안 변이가 지금 도구에서 살아야 하므로 test가 반환값을 보지 않고 `if` 안 `LOG.append(y)`로 관찰한다(그 문장은 T6 나로 대상이고 죽는다).
* 같은 지문의 문장을 한 def 안에 반복하지 않는다(규범 알고리즘이 어느 사본을 '새 문장'으로 고르는지에 기대지 않게 -- spec card 'oracle'). (i)의 두 가지는 다른 블록이라 맞춤에 섞이지 않는다.

### 1.4 2차 검토 적대 21건 -- 이 card 규칙에서 어떻게 되나(설계상 놓치는 것 표시)

`v3scope_kit/out/adv21_proto.txt`(독립 프로토타입, 이전 분류기와 변이별 불일치 0). 형식 = 대상 / weak test만으로의 판정 / 변경 고유 변이(weak은 못 죽이고 strong만 죽이는 대상 변이).
'설계상 놓침' = 승인 기록 범위 설명 '놓치는 것' ②(다른 블록)·③(두 단계 이상)에 해당해 **변경을 관찰하지 않는 test로도 PASS**가 되는 것 -- 승인된 약화다. redteam에 attack으로 넣지 않는다.

| # | 동작 변경 | 지금 | 이 card | 분류 | redteam 35 |
|---|---|---|---|---|---|
| 1a | `**kw` 전달 bool 기본값 | 6 / PASS / 0 | 2 / PASS / 0 | 기존 한계(bool 변이 없음, B46) | -- |
| 1b | `**kw` 전달 int 기본값 | 8 / FAIL / 2 | 4 / FAIL / 2 | 덮음(T3 자기 필드) | -- |
| 1c | bool 기본값 → 별칭 `s = strict` → `if s and x < 0` | 12 / FAIL / 3 | **2 / PASS / 0** | **설계상 놓침 ③**(매개변수 → 다른 이름 → 사용) | -- |
| 2 | 모듈 상수 `THRESH` | 0 / PASS / 0 | 0 / PASS / 0 | 기존 한계(def만 봄, B46) | -- |
| 3a | 문장 안 helper 이름 교체 | 6 / PASS / 0 | 6 / PASS / 0 | 기존 한계(이름 교체 변이 없음) | -- |
| 3b | 모듈 수준 `helper = ha → hb` | 0 / PASS / 0 | 0 / PASS / 0 | 기존 한계 | -- |
| 4a | 문장 안 lambda | 9 / FAIL / 1 | 9 / FAIL / 1 | 덮음(T1) | (b) 꼴 |
| 4b | 기본값 lambda `key=…` → `sorted(…, key=key)` → `return s[0][1]` | 9 / FAIL / 1 | **4 / PASS / 0** | **설계상 놓침 ③**(매개변수 → `s` → 사용, 두 단계) | -- |
| 5 | 컴프리헨션 필터 | 7 / FAIL / 1 | 7 / FAIL / 1 | 덮음 | (e) 꼴(머리 안) |
| 6 | 문장 순서 바꾸기 | 10 / FAIL / 4 | 10 / FAIL / 4 | 덮음(넓힌 T6) | -- |
| 7 | `raise ValueError → KeyError` | 7 / PASS / 0 | 6 / PASS / 0 | 기존 한계(예외 종류 변이 없음) | -- |
| 8 | `a + b → a + c` | 3 / PASS / 0 | 3 / PASS / 0 | 기존 한계(이름 교체 없음) | -- |
| 9 | dict 키 문자열 | 6 / PASS / 0 | 6 / PASS / 0 | 기존 한계(문자열 변이 없음) | -- |
| 10a | 데코레이터 인자 `maxsize` | 7 / FAIL / 2 | 3 / FAIL / 2 | 덮음(T3, 계약 9 전제) | (h) |
| 10b | 데코레이터 문자열 인자 | 5 / PASS / 0 | 1 / PASS / 0 | 기존 한계 | -- |
| 11 | `mode` 값, 한 문장 건너 같은 블록 `if` | 16 / FAIL / 4 | 5 / FAIL / 2 | **덮음(넓힌 T6 나 -- 승인 당시 정의는 놓침)** | (i) |
| 11b | 11과 같되 바로 뒤 `if` | 16 / FAIL / 4 | 4 / FAIL / 2 | 덮음(T6 가) | (g) 꼴 |
| 12 | 문장 삽입 `y = max(y, 0)` | 12 / FAIL / 3 | 8 / FAIL / 3 | 덮음(T1·T6 나) | (b) |
| 13 | `elif x > 5 → 6` | 18 / FAIL / 1 | 9 / FAIL / 1 | 덮음(T2·T4) | (c)·(e) 꼴 |
| 14 | `neg` 값, 두 문장 뒤 같은 블록 `if neg:` | 7 / FAIL / 2 | 4 / FAIL / 1 | **덮음(넓힌 T6 나 -- 승인 당시 정의는 놓침)** | (i) |
| 15 | `else` 절 통째 삭제 → 바깥 `return y * 3` | 15 / FAIL / 3 | **5 / FAIL / 0** | **설계상 놓침 ②**(블록 끝 삭제, 다른 블록 -- weak FAIL은 변경과 무관한 생존) | (k) 꼴(control) |

합계 대상: 지금 179 / 승인 당시 87 / 이 card 98. 키트가 더한 경계 3건: 반복문 앞쪽 사용(K1) 15 / 6 / **10**(덮음, (j)), 다른 블록 사용(K2) 16 / 9 / **9**(놓침 ②, (k)),
두 단계 흐름(K3) 17 / 6 / **6**(놓침 ③). **설계상 놓치는 것 = 1c·4b(③)·15(②)와 K2·K3 꼴** -- 이 중 (k)만 control로 고정한다(③을 control로 고정하는 단계는 계약 8에 없다 -- 넣지 않는다).

### 1.5 자기 점검(커밋 전)

* `C:/Python314/python.exe -B <worktree>/tools/gates/redteam/run_all.py --phase 0.5 --mode direct --only 35-v3-changed-scope` → 지금 도구에서 적어도 (a)·(h)·(k)가 FAIL(red), 나머지 단계 결과를 기록.
  attack 단계가 base에서 '생존 0'으로 PASS가 되면 구성이 틀렸다(X가 죽음).
* 기존 케이스 무변화: `--only` 없이 한 번. FAIL은 35뿐이어야 한다(34 포함 그대로).
* 각 attack 단계의 '유일 생존'을 계약 1로 손으로 다시 셈(대상 목록을 `basis`에 적는다). 피검 도구 출력은 복사하지 않는다.

---

## 2. code-author 브리프(gmid-code-author, §12 순서 5)

```
역할: gmid-code-author. change id = 20260930-v3-changed-stmt-scope (게이트 변경, red-green).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-changed-stmt-scope-code (브랜치 role/code/20260930-v3-changed-stmt-scope, 부모 = test 커밋 T). 절대 경로만, cd 금지.
쓰기 경로: tools/gates/mutate_changed.py 하나(design 10 C11 행). redteam/**·reachability.py·merge_gate.py·test_lint.py·문서는 쓰지 않는다.
입력: spec card·interface card. 묶기 card(20260930-v3-exempt-binding) 병합본의 mutate_changed.py가 출발점이다(면제 판정·출력 키가 이미 있다).
test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20260930-v3-changed-stmt-scope.md)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다.
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20260930-v3-changed-stmt-scope" -m "…"
```

### 2.1 바꿀 것(계약 번호)

1. **맞춤·대상 분류(계약 1)** -- 해시가 바뀐 기존 def마다 **한 번** 계산해 대상 변이 (연산자, 경로) 집합을 만든다(변이 루프 안에서 다시 맞추지 않는다 -- 캐시 원칙).
   * 맞춤: 블록 필드(`body`·`orelse`·`finalbody`·`handlers`·`cases`) 목록을 지문 `ast.dump(n, include_attributes=False)`로 `difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()`.
     `replace` 구간은 head 원소를 앞에서부터, 복합문이면 짝 없는 base 원소 중 같은 종류·같은 머리 지문 → 없으면 같은 종류(가장 앞의 것). 머리 지문 = 블록 필드를 빈 목록으로 바꾼 노드의 지문
     -- **원본 노드를 바꾸지 말 것**(변이는 원본 트리에서 경로로 만든다. 복사본 또는 필드를 모아 새 노드로).
   * 맞추는 트리는 `changed_defs`가 준 head def 노드 **원본**(docstring 포함 -- `mutants`가 받는 바로 그 노드)과 base 소스에서 같은 qualname의 원본. ①의 `def_hash`(docstring 제외)와 섞지 않는다.
   * 경로 표기는 `_path_nodes`와 같게(`body[2].orelse[0]`, `handlers[0]`, `cases[1]`). 변이 경로 → 변이 노드: `cmp_flip`은 끝의 `.ops[k]`를 떼고, `stmt_delete`는 그 문장 경로 자체, `except_body_delete`는 처리기 경로,
     `early_return`은 항상 대상(T5).
   * T1~T6·용어('몫', '읽는다', '바꾸는 이름' ⓐ~ⓓ, 반복문 규칙)는 spec card 계약 1 문장 그대로. 새·지운 복합문의 '바꾸는 이름'은 부분 트리 전체, 매개변수 '위치'는 같은 종류 목록 안의 순번(v4에서 확정).
   * 새 def(base 같은 경로에 같은 qualname 없음)는 전부 대상(계약 3). 새 파일(`base_src is None`)이면 모든 def가 새 def.
2. **판정 순서(계약 4, 묶기 card 위)**: 변이마다 ① 대상 판정 → 대상 밖이면 `{"id": mid, "result": "not_targeted"}`를 `--out`에 append하고 다음 변이(결과 목록·`mutants`·면제 판정·`exempt_ignored`에 넣지 않는다)
   ② 대상이면 묶기 card의 면제 판정 함수 ③ `exempt`가 아니면 지금처럼(인벤토리 없음 → 생존, 있으면 실행). def마다의 기준 실행은 그대로.
3. **출력(계약 5)**: 묶기 card 키 뒤에 `not_targeted`(정수 -- 실행하지 않은 수), `targets_by_def`(`{"<파일>::<qualname>": {"targeted", "not_targeted", "deleted_statements", "def_header_changed"}}`, 처리 순서).
   `<파일>`은 `targets`에 나오는 저장소 상대 경로. `deleted_statements` = 맞춤에서 '지운 문장' 수, 새 def는 `targeted` = 전체·`not_targeted` 0·`deleted_statements` 0·`def_header_changed` false.
   `--out`의 `not_targeted` 레코드는 생성 순서대로(대상 레코드와 섞여).
4. **데코레이터 치환(계약 9)**: `_replace_def`가 `min(fn.lineno, 데코레이터 줄들)`부터 `end_lineno`까지를 변이된 def(데코레이터 포함)의 `unparse`로 바꾼다. 들여쓰기는 시작 줄 기준.
5. **모듈 docstring ①**: "① 대상 = diff가 닿은 `def` 중 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는 바뀐 문장·감싸는 제어문·바꾸거나 지운 문장 자리 바로 뒤 문장·같은 블록 뒤쪽(반복문 본문이면 그 본문 전체)에서
   바뀐 이름을 읽는 문장·def 머리 변경 몫·`early_return`. 대상 밖 변이는 실행하지 않는다"와 같은 뜻으로(design 05 317행 새 문구와 맞춘다). 지금 docstring의 "(새 def 포함)"은 새 문구로 대체.

### 2.2 하지 말 것

* 광범위 `except`(Exception·bare) 추가 금지(V6·공격 27f가 도구 소스 AST를 본다). 새 import는 표준 라이브러리(`difflib`)만.
* 변이 연산자·경로·id 규칙(`mutants`, `mid`)·인벤토리·면제 규칙(묶기 card)·`_approved` 변경 금지. 새 CLI 옵션 금지(`--report-untargeted`는 별도 card).
* 새 함수를 만들고 `main`에서 안 부르는 것 금지. 옛 '모든 변이 실행' 흐름은 같은 커밋에서 대체.

### 2.3 자기 확인(판정 근거 아님)

* `run_all.py --phase 0.5 --mode direct --only 35-v3-changed-scope` → 11단계 PASS, `--only` 없이 전체 FAIL 0(34 포함).
* 선택 집합 대조(키트 probe, §3.3 p8): 키트 `v3scope_kit/probe_selection.py`로 P9 실제(`6bf510b..93b18db`)에서 대상 12·대상 밖 16, id가 `out/ids_p9_real.json`의 `N2w`와 같은지.

---

## 3. auditor 브리프(gmid-verification-auditor, §12 순서 3·7)

```
역할: gmid-verification-auditor. change id = 20260930-v3-changed-stmt-scope, evidence_type red-green, 게이트 변경(phase 0.5), 판정 기준 적용 범위 축소(약화) 승인 card.
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-changed-stmt-scope-audit (브랜치 role/audit/20260930-v3-changed-stmt-scope).
모든 측정은 격리 복제본에서(§12-7): git clone --no-hardlinks --no-local <audit worktree> <scratch>/iso → git -C <scratch>/iso remote remove origin.
scratch는 새 C:/g<n> 하나만(다른 C:/g* 건드리지 말 것), 끝나면 그 폴더만 삭제. 셸 가드: set -euo pipefail, git -C <절대 경로>만. 끝나면 실제 저장소 git status·reflog 불변 확인.
게이트 코드는 base 판(= 승인 커밋 뒤 gate master = 묶기 card 병합본 + 이 card 문서 커밋)을 git cat-file로 추출한 사본(선례 extract_gate.py).
작성자(test·code) 보고는 증거로 받지 않는다. 판정 기록 .ai/verification/20260930-v3-changed-stmt-scope.json + scripts/out, Role: audit 커밋. approvals = ["20260930-v3-changed-stmt-scope"].
```

### 3.1 순서 3(freeze·base 확인 → `base_check.json`)

* T 해시 고정, T 경로가 `tools/gates/redteam/attacks/35-v3-changed-scope/**`뿐인지(rt.py 변경 0 -- 승인 범위에 rt.py 동작 추가 없음).
* base 게이트로 T 복제본 `run_all.py --phase 0.5 --mode direct`(전체)·`--cases 0.5` → base 표 보관(log sha256). red = base에서 FAIL인 35 단계(최소 (a)·(h)·(k) -- exit가 다름). `failure_hashes`는
  base 판 `merge_gate.red_failure_hash("tools/gates/redteam/attacks/35-v3-changed-scope::<step>", "redteam.FAIL")`.
* **판별력 확인**(base 표로 못 보는 것): attack 단계마다 ① base 도구 `--out`에서 X가 생존인지 ② 계약 1을 auditor가 **직접** 적용해(손 또는 auditor 자신의 분류) X가 대상이고 나머지 대상 변이가
  test로 죽는지(대상 목록과 base `--out`의 killed 대조) ③ 겨냥한 규칙을 뺀 정의에서 X가 대상 밖인지((i)·(j)는 승인 당시 정의 = T6 나 없음). 하나라도 아니면 test 결함으로 보고.
  참고 도구: 키트 `scope_proto.py`(오케스트레이터 쪽 독립 프로토타입 -- 작성자 산출물 아님. 쓰면 판정 기록에 '참고 대조'로만 적는다).
* control (a)·(k)의 `observed_equals` 목록이 계약 1로 정한 대상 밖 id 전부인지 손으로 대조.

### 3.2 순서 7(병합본 판정)

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | **PASS** 기준 | (1) pytest 전체(base 판 `pytest_gate.ini`, `--gmid-phase=0.5 --gmid-strict=`, `v1_command_check` 위반 0) -- 변경 경로가 `tools/gates/**`뿐. (2) 병합본 redteam 전체 + `--cases 0.5`, **순서 3 base 표와 케이스·단계 단위 기계 대조**: 달라진 케이스는 `35-v3-changed-scope` 하나(red 단계 FAIL→PASS), `34-v3-exempt-binding`·`v3_survivor`·26·27f·28·29·31 같음(계약 7) |
| V2 | N/A(도입 1) | 참고: 커밋 사슬 base → T(Role: test) → code(Role: code, 부모 T, `mutate_changed.py` 1경로) → 병합. red·green 집합 |
| V3 | N/A(도입 1) | 참고: base 판 V3(게이트 도구는 대상 밖 -- targets 빈 목록) |
| V4 | N/A(도입 1) | 참고 + oracle 대조: 35 기대값이 계약 문장·구성에서 왔는지 단계별, 피검 출력 복사 아닌지 |
| V5 | N/A(도입 1) | 사람 판단: 기존 `expect.json`·`v.json` 변경 0, **판정 기준 적용 범위 축소는 승인 기록 `20260930-v3-changed-stmt-scope` 범위 설명('덮는 대상'·'놓치는 것' ①②③)과 같은가** -- 병합본 규칙이 그보다 넓게 빼면(예: T6 나 없음, 반복문 규칙 없음) 승인 밖 약화. 승인 `target` 재계산 일치 |
| V6 | N/A(도입 1) | 참고: base 판 `source_lint.py`, 광범위 except 0(27f) |
| V7 | N/A(도입 2) | 배선 관찰: 맞춤·분류 함수가 `main`에서 불리고, 옛 '모든 변이 실행' 흐름이 대체됐는지 |
| V8·V9 | N/A | 엔진·회로 무관 |
| V10 | PASS | '재현할 수치: 없음'. 계약 확인은 3.3 probe |

### 3.3 redteam이 덮지 않는 계약 -- probe(병합본 도구, 기대값은 계약 문장에서)

| probe | 계약 | 입력·기대 |
|---|---|---|
| p1 출력 모양 | 5 | 키 순서 `…, survivors, survivor_bindings, exempt_ignored, not_targeted, targets_by_def`; `mutants` = 대상 수; `targets_by_def` 키 `<경로>::<qualname>`·처리 순서·네 필드; 새 def `targeted` = 전체·`def_header_changed` false |
| p2 `--out` 순서 | 5 | `not_targeted` 레코드가 생성 순서대로 대상 레코드와 섞여 있음(키 `id`, `result` 순서) |
| p3 면제 × 대상 밖 | 4 | 대상 밖 변이에 묶인 원소(해시 맞음) → `not_targeted`(exempt 아님), 해시 없는 원소 → `exempt_ignored`에 없음. 대상 변이에는 묶기 card 규칙 그대로 |
| p4 머리 변경 | 1 T3 | 기본값만 바꾼 def(`def_header_changed` true) → 자기 필드 변이 + 바뀐 매개변수를 읽는 문장(다른 블록 포함)의 몫 + early_return. 매개변수 순서만 바꾼 def, `*args` 추가 |
| p5 맞춤 경계 | 1 | 같은 지문 문장 반복(규범 알고리즘 결과와 일치), `try/except` 처리기 머리 변경(`except ValueError → KeyError` -- 몫), `match`/`case`, 중첩 def 안 변경(조상에 중첩 def 포함), docstring만 더한 def(① 해시가 같아 대상 def가 아니다 -- 변이 0) |
| p6 데코레이터 치환 | 9 | 여러 줄 데코레이터·데코레이터 여러 개·클래스 메서드에서 변이 소스의 AST가 원본과 다름, 들여쓰기 유지 |
| p7 무기록·새 def만 | 7 | 새 def만 있는 변경: 출력이 묶기 병합본과 새 두 키(`not_targeted` 0, `targets_by_def`)만 다름 |
| p8 **선택 집합 실측(원래 문제 대체)** | 1·3 | 키트 `probe_selection.py`(가짜 pytest로 도구 `main`을 실제 경로로 돌려 `--out`에서 대상 집합을 읽음 -- 2026-10-01 base 도구로 P9에서 동작 확인: all 28 일치, N2w 기대에는 16개 초과로 불일치=판별). 병합본 도구로 ① P9 실제 `6bf510b..93b18db` → 대상 12·대상 밖 16, id = `out/ids_p9_real.json` N2w ② **B26-1 card v4 모의**(키트 `measure_b26.py`의 모의 커밋 방식으로 auditor 복제본에 다시 만듦) → 대상 **301**·대상 밖 2,141, id = `out/ids_b26_v4.json` N2w. 다르면 차이 id를 계약 1로 손 판정(구현 결함인지 키트 프로토타입 결함인지) -- 판정 기록 V10 관찰에 '원래 문제(B26-1 V3 비용) 대체' 측정값으로 |

관찰(판정 약화 아님)은 V10 끝에 따로: 대상 밖 id 목록을 기존 test 강도 백로그로 넘김(계약 5 끝), 중첩 def 이중 변이 비용(묶기 card 백로그 6).

---

## 4. 순서 요약(오케스트레이터)

P10b 병합·정리 → Phase 2 DoD → 묶기 card 끝(순서 8 push·정리) → **§0.4 A1~A7 확인·필요하면 spec card 문구 보정 + `sim_sequence.py` 재실행** → `role/*` 0개 확인 →
커밋 계획 §4.2 A(문서)·B(spec v4 + interface, **절대 경로 호출**)·C(승인 기록) → `gate_change_ok` True(절대 경로 `-c` 형태) → push 단독 실행·전체 출력 확인 → §12 순서 1(test worktree) →
test-author(1절) → 순서 3 auditor freeze·base 표(3.1) → 순서 4 code worktree → code-author(2절) → 순서 6 병합 → 순서 7 auditor(3.2·3.3) → 순서 8 push → 정리 → 사용자에게 B26-1 수 보고(§0.2 한 줄) → B26-1.

## 5. 키트 파일(`_drafts/v3scope_kit/`)

| 파일 | 내용 |
|---|---|
| `setup_g109.py` | scratch 준비: `C:/g109/b1`(gate master archive), `repo`(격리 복제), `scripts`(`b26_scripts` 측정 스크립트 사본, 경로 `C:/g83` → `C:/g109`), junit·실행 줄 재사용 |
| `scope_proto.py` | 계약 1 독립 프로토타입(`select(base_fn, head_fn, mutants, "N2w"|"N2b")`), 해석 스위치 2개 |
| `measure_b26.py` | 모의 커밋(B1 = +B34, H4 = B26-1 v4, H2 = review2, HO = 옛 시뮬, P9 실제, B34)을 복제본에 만들고 도구 경로로 대상 수·시간 → `out/measure_b26.txt`·`.json`·`ids_*.json` |
| `variants.py` | 해석 자리 다른 판으로 재측정 → `out/variants.txt`(전부 같은 수) |
| `adv21_proto.py` | 적대 21건 + 경계 3건, 이전 분류기와 변이별 대조 → `out/adv21_proto.txt`(불일치 0) |
| `binding34_under_scope.py` | 묶기 키트 구성 예가 이 card 아래에서도 전부 대상인지 → `out/binding34_under_scope.txt` |
| `redteam35_examples.py` | 계약 8 (a)~(k) 구성 예 프로세스 안 모의 → `out/redteam35_examples.txt`(11단계 기대대로) |
| `sim_sequence.py` | 묶기·범위 card 문서 커밋 → interface card → 승인 fill → `gate_change_ok` → EL4 receive 모의 → `out/sim_sequence.txt`(NG 0) |
| `probe_selection.py` | auditor p8: 가짜 pytest로 도구 `main`의 대상 집합 실측 → 기대 id와 대조 |
| `out/classify_v4.txt`·`classify_review2.txt` | 이전 분류기를 `0f23786`에서 다시 돌린 결과(301·330 재현) |

재현: `C:/Python314/python.exe -B setup_g109.py 0f23786` → `C:/g109/scripts/mk_b1.py` → `measure_b26.py`(약 12분) → 나머지 스크립트(각 1~3분). `C:/g109`는 측정 뒤 삭제했다.
