# B33 V7 호출 그래프 card `20260930-v7-registry-edges` -- 착수 키트(세 역할 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` `0f237862c007f6a53122f2bdfb3c87e6366ec133`(`0f23786`, P10b spec card 재시도 개정). 저장소 쓰기·상태 변경 git 없음.
측정·모의는 격리 복제본 `C:/g114`(origin 제거, 빈 hooksPath, 끝나고 삭제)에서만. 측정 스크립트·출력: `_drafts/b33_kit/`(README는 이 문서 §5).
review3(`_drafts/review3_b33.md`, 2026-10-01) 반영: S1·m1 거부 단계 2개(30단계), m2 승인 초안 선택지 설명, m3 spec '거부해야 할 입력'에 `ctor-factory-limit`, m4 키트 경로·실행 시간 안내(§5). 재측정 scratch `C:/g138`(삭제). 직전판 `b33_briefs.v2.md`.
사용자 결정: `_drafts/user_decisions.md` '2026-10-01 B33' -- 게이트 변경 "승인 (Recommended)", Q1 "(a) 호출 위치만 (Recommended)"(팩토리 모양은 거짓 FAIL → 면제 승인 처리).
대상 산출물: `draft_b33.final.spec.md`(재검증 반영판, 직전판 `draft_b33.final.spec.v1.md`), `approval_20260930-v7-registry-edges.md`(직전판 `.v1.md`),
`patch_b33_design05.py`(그대로), `fill_v3_approval.py`(V3 card용을 그대로 재사용 -- id·경로를 초안에서 읽는다).
card 순서(확정): P10b → Phase 2 DoD → 34 V3 면제 묶기 → 35 V3 범위 → B34 → B26-1(앞선 test 보강 card 포함) → **B33** → Phase 3(G1 …).

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(gate master `0f23786`)

| 확인 | 결과 | 조치 |
|---|---|---|
| `tools/` 변경(측정 기준 `7535799` → `0f23786`) | `git diff --stat 7535799 0f23786 -- tools/` 차이 0 | 도구 사실 문장 그대로 |
| `reachability.py` 줄 | `_refs` 69, `build_graph` 97, `reach` 160, `GRAPH_PREFIXES` 171, `_is_source` 175, `_approved_ids` 180, `seen = reach` 223, `new_defs` 230, docstring 그래프 설명 10~13 | -- |
| `mutate_changed.py` 줄 | `inventory` 214-215(`rch.reach`), `rch._is_source` 315, `rch.build_graph(head_files)` 317, `TimeoutExpired → "timeout"` 354-356, `code != 0 → killed` 387-392, docstring ③ 9행 | 같음. **34·35가 이 파일을 고친다** → card 문장을 심볼 + "`0f23786` 줄"로 바꿈(의도 '새 위험'·`mutate_changed.py` 단락) |
| redteam | `rt.py` `build_vrepo` 523·`a_vcase` 580, `run_all.py:55` 발견 규칙 `attacks/*/expect.json`, `attacks/` 마지막 `31-v3-git-history`, `33-*` 없음 | rt.py 줄은 **34가 고친다** → '게이트 변경 승인' 단락에 "`0f23786` 줄, 착수 때 재측정" |
| `build_vrepo`의 `base` | `base_files = case.get("base", {})` -- 단계마다 `base`가 없으면 빈 base | oracle 절 "단계마다 둘 수 있다" → "**단계마다 둔다**(없으면 공통 base 파일의 def도 새 def)"로 고침 |
| 문서 | design 05 V7 행 321, 거부 증명 338, V3 ③ '같은 그래프' 317; 계획 '운영 경로' 121, N4.2 V7 843(`8356c1e`가 계획서를 고쳤지만 두 줄은 그대로) | -- |
| `super()`·이름 | `git grep "super()\.__"` → `sizing_recipe.py:6452` 1건. `::=` 0건, `_is_source` 175·230·mutate 315뿐, `library/`·`topology` 리터럴 0건, `tests/`의 `reachability\|mutate_changed` 0건, `reachability`를 부르는 설치 사본·merge gate 0건 | -- |
| 엔진·test 트리 | `7535799` 뒤 `stick_diagram.py`(P9)와 test 3개(P9 `test_dup_kcl_edges`, P10 `test_df23_inventory`·`test_phase2_stale_refs`)가 바뀜 | 머리 수치 재측정(0.2) |
| 과거 판정 기록 | V7 쌍이 있는 기록 29건·서로 다른 쌍 29(`2d58fd8` 28 + `62ae24f` `20260930-p10-df23-inventory`) | 계약 14·무동작 절·승인 초안 주석 고침 |
| D-18 인용 | card가 `draft_phase3_design_v5.md` 519·222-224행을 인용 -- 지금 초안은 v8(다른 agent가 편집 중) | 줄 번호 대신 "v8 결정표 D-18 행·'redteam 번호 배정' 항목" |
| card 순서 문장 | "34·35가 먼저면 … B33이 먼저면 …" 두 갈래 | 확정 순서 한 갈래로(34·35·B34·B26-1 뒤, 그 넷은 `reachability.py`를 안 고침) |
| 계약 12 (ii) | "착수 예정 card(draft_b26_1·draft_b34 대상 def)" -- 확정 순서상 B33 착수 때는 이미 판정 기록 | "과거 판정 기록 V3 근거의 대상 def 전부(B34·B26-1 기록 포함)" |
| 계약 12 (i) | `restore-plan-functions` "mutants 32" -- 34·35 뒤 base 도구는 대상 범위·면제가 달라 수가 다를 수 있음 | 괄호 한 문장(비교는 같은 시점 두 도구 사이) |
| Q1 팩토리 모양 | 사용자 답 "팩토리 모양은 거짓 FAIL → 면제 승인 처리"가 계약·redteam에 없음 | 계약 4·8 문장 + 단계 2개(`ctor-factory-limit` known_limit exit 1, `ctor-factory-exempt` exit 0) -- 실측 0.2 |
| interface card 토큰 | 계약 절의 맨 토큰 `run`·`build_graph`·`__post_init__`·`__init__`이 엔진 def(`run_harness.run`·`stick_diagram.build_graph` 등)와 겹쳐 기존 함수 5행 | `run_harness.py::run`·`reachability.build_graph`·`Cls.__post_init__`·`Cls.__init__`·`Sub.__init__`로(뜻 불변) → 3행(남은 것은 design 05 인용문 -- 0.5) |
| 사용자 원문 | 승인 초안의 질문 두 개·선택지가 세션 기록(jsonl, AskUserQuestion 2026-10-01T04:33:58Z, 답 04:35:41Z)의 원문과 바이트 단위로 같은 부분 문자열 | `b33_kit/check_user_quote.py` → `question_in_draft [true, true]`, `options_in_draft [true, true]`, `descriptions_in_draft [true, true]`(review3 m2 -- 선택지 설명 원문 네 개를 초안에 넣고 대조 추가) |

### 0.2 머리 수치 재측정(`b33_kit/run_headline.sh`, `run_attack33.sh` -- 복제본 `C:/g114/r` = `0f23786`)

base 도구 = 복제본의 `tools/gates/reachability.py`(시제품 `base` 변형의 간선 사전이 이것과 같음을 다시 확인: `edges_equal_head_tool true`), 개정 = 시제품 `reachability_b33.py`의 `fixed`(card 문장 구현, 측정용 -- 역할 산출물 아님).

| 수치 | 승인 질문·card(7535799) | `0f23786` 재측정 |
|---|---|---|
| 운영 루트 미도달 소스 def(494개 중) | 115 → 39 | **115 → 39**(base R3 없이 115, R3만 적용 116; 두 벌 base 116/122 → 39/39). 미도달 집합이 7535799과 **같다**(차집합 0) |
| 운영 루트가 닿는 비운영 노드(누수) | 64 → 0 | 66 → 0(늘어난 2 = P9·P10 test 파일) |
| V3 (소스 def, 도달 test) 쌍 | 33,991 → 44,493(×1.31) | **34,163 → 44,765(×1.310)**, test 함수 454 → 478 |
| 인벤토리 0인 소스 def | 82 → 19 | 82 → 19, base에서 0이 아니던 def가 0이 된 것 0(회귀 0) |
| 인벤토리 중앙값 | 61 → 67 | 61 → 67. 표본 `SemiEmpiricalGmIdLUT.__init__` 0 → 259(card 249), `_metric_sum_current` 0 → 87 |
| 계약 9 옛 간선 제거 | 3개(전부 dunder 폴백), 도달 감소 0 | 같음(3개, 전부 `InfeasibleSizingError.__init__` → 속성 `__init__`; 도달 감소 0 -- R3 없이·있이, 세 루트 벌) |
| 면제 두 id(`lut_conditions_from_npz`·`derived_spec`) | 미도달 유지 | 미도달 유지 |
| 정적 인벤토리(m5, base/개정) | `width_from_id_density` 227/249, `kcl_series_union` 70/70, 나머지 | `width_from_id_density` 237/259, `kcl_series_union` 72/72, `compute_metric` 82/87, 나머지 같음 |
| 과거 판정 기록 V7 쌍 | 27(질문)·28(`2d58fd8`) 전부 같음 | **29건·서로 다른 쌍 29**(새로 `20260930-p10-df23-inventory`) 전부 base 도구·시제품(`fixed`·`draft`)의 `verdict`·`unreached`·`unreached_without_approval` 같음, 전부 PASS, `--config` 전부 head 트리. new_defs 있는 쌍은 그대로 4개(ic3-completeness 2·df36-instance-relpath 1·dup-w-calc 1·restore-plan-functions 2) |
| 공격 33(26단계) | base 13 FAIL(red 12 + `registry-reexport-other` 목록) / 시제품 26 PASS | 같음(단계마다 같은 판정·exit) |
| 공격 33 + 팩토리 2단계(28) | -- | **base 13 FAIL / 시제품 28 PASS**. 더한 `ctor-factory-limit`은 두 도구 모두 exit 1(`RtFac.__init__` 미도달), `ctor-factory-exempt`는 두 도구 모두 exit 0(`unreached` = [`RtFac.__init__`], `unreached_without_approval` = []) -- 둘 다 red가 아니다(동작 고정 단계) |
| 공격 33 + review3 2단계(30) | -- | **base 13 FAIL / 시제품 30 PASS**(`C:/g138`). 더한 `registry-reexport-x-outside`·`registry-bare-name-other`는 base 도구에서 exit 1 PASS(red 아님 -- 거부 단계). 잘못된 구현: `xout` 1 FAIL(13번), `bare` 1 FAIL(14번), `draft` 6, `loose` 9, `nosuper` 1(`ctor-super-chain`). 표 `b33_kit/out/a33r3_0f23786.table.md` |
| `build_graph` 시간 | 4.8 → 5.4초 | HEAD 도구 5.7초, 시제품 base 6.8·fixed 10.6초(다른 측정과 동시 실행 -- 잡음, 임계값 없음. auditor가 계약 11로 다시 잰다) |

승인 질문의 머리 수치(115→39, ×1.31, 27건 불변)는 `0f23786`에서도 그대로다(기록 수만 27 → 29로 늘었다).

### 0.3 선행 card와의 관계(무엇이 B33에 걸리는가)

| 선행 card | 고치는 것(spec card 쓰기 경로) | `reachability.py` | B33에 걸리는 것 | 착수 때 할 일 |
|---|---|---|---|---|
| 34 `20260930-v3-exempt-binding` | `mutate_changed.py`(면제 묶기·`exempt_ignored`·`survivor_bindings`), `redteam/lib/rt.py`(`@bindhash`·`"observe": "out_jsonl"`), `attacks/34-*`, 문서 design 05 317·design 10 382·계획 N4.2 V3 | 안 고침(`_approved_ids` 불변이 34 계약 7) | card가 인용한 `mutate_changed.py`·`rt.py` 줄 번호가 밀린다. 34 V3 케이스가 계약 14 대상(V3가 `build_graph`를 쓴다) | 줄 번호 재측정, 34 케이스를 시제품으로 미리 돌림(0.6 ④) |
| 35 `20260930-v3-changed-stmt-scope` | `mutate_changed.py`(대상 범위·`not_targeted`), `attacks/35-*`, 문서 design 05 317·계획 N4.2 V3 | 안 고침 | 계약 12 (i)의 mutant 수가 기록 값(32)과 다를 수 있다(계약에 적음). 35 케이스가 계약 14 대상. `v3-registry-inventory` 단계는 두 def가 새 def라 전 문장이 대상 -- 기대 그대로 | 위와 같음 |
| B34 `20260930-b34-grammar-explicit` | 엔진 `stick_diagram.py`(import 실패 처리), 새 test(`_b34_` 접두 -- 지금 그래프의 이름 폴백 때문에 유일한 이름) | 안 고침 | 엔진·test 트리 → 머리 수치. 그 판정 기록의 V7 쌍이 계약 14 대상 | `run_headline.sh` 재실행 |
| B26-1 `20260930-b26-rail-accessor-set`(+ B26-pre test 보강, backfill 등 B26 계열) | 엔진 SD·SR·레지스트리, test | 안 고침 | 새 def `rail_declaration`(B26-1 계약 10: `load_topology` 경유 도달)의 V7 쌍이 계약 14에서 새 도구로 다시 판정된다 -- **옛 도구의 도달이 test 파일 이름 폴백(R3가 막는 누수)에 기댔다면 새 도구에서 FAIL로 뒤집힌다**. B26-1의 `_metric_kcl_residual`(레지스트리 값, 인벤토리 0 → 이름 직접 호출 test로 대응)은 B33 뒤 인벤토리가 생긴다(과거 기록은 V3를 다시 돌리지 않으므로 영향 없음) | `m4_records.py`로 새 쌍 미리 확인(0.6 ③). backfill이 `sizing_recipe.py`를 고치면 `super()` 줄(6452) 재확인 |
| (뒤) G1 `20260930-p3-gate-move-aware` | `reachability.py`(`SourceIndex`·`moved_defs`)·`mutate_changed.py` | **고침** | B33 → G1 순서(사용자 승인). G1 초안의 `reachability.py` 줄·사실은 B33 병합본에서 다시 재야 한다(G1 키트 몫) | B33 병합 뒤 G1 재측정 알림 |

문서 패치 겹침: 34·35 문서 패치를 먼저 적용한 트리에서 `patch_b33_design05.py`가 그대로 적용된다(모의 S 단계 -- 0.5). 두 패치는 design 05 317행(V3 행)만 바꾸고 B33의 앵커(321·338행)와 겹치지 않는다.

### 0.4 승인 기록 초안(`approval_20260930-v7-registry-edges.md`, 직전판 `.v1.md`)

* '사용자 원문'은 그대로(질문 두 개·선택지·답 -- 0.1 마지막 행에서 세션 기록과 대조).
* 고친 곳 3: 범위 설명 redteam 단계 수 26 → **28**(known_limit 1·대조군·면제 4 추가 설명), '덮지 않는 것'의 과거 V7 쌍 "28개" → "착수 시점 전부(`0f23786` 29)", 오케스트레이터 주석의 기록 수(주석은 채울 때 지운다).
* review3(2026-10-01) 반영(직전판 `.v2.md`): 범위 설명 단계 수 28 → **30**(거부 11 → 13: `registry-reexport-x-outside`·`registry-bare-name-other`), '사용자 원문' 괄호에 네 선택지의 **설명** 원문을 더함(`check_user_quote.py` `descriptions_in_draft [true, true]`). 두 단계는 승인 문장 R1 (iv) "M·X는 그래프 안 모듈"과 계약 1 "import 없이 다른 파일에 있는 같은 이름 … 가지 않는다"를 고정할 뿐이라 범위 변화 없음.
* 범위 문장 자체(R1·R2(Q1 (a))·R2'·R3, V3 인벤토리 수용, design 05 두 줄, 새 케이스)는 그대로 -- 팩토리 2단계는 사용자 답("팩토리 모양은 거짓 FAIL → 면제 승인 처리")을 단계로 고정한 것이라 범위 밖 추가가 아니다.

### 0.5 모의 결과(`b33_kit/sim_launch.sh` -- `C:/g114/sim/r` = gate master 복제, bare 가짜 gate `C:/g114/sim/gate.git`)

| 단계 | 결과 |
|---|---|
| 0 모래상자 | `C:/g114/sim/r` = `0f23786`(origin 없음, 빈 hooksPath), 가짜 gate = bare 복제(hook 없음 -- EL4는 `merge_gate.py receive`를 직접). 게이트 캐시 `C:/g114/sim/r/.git/gmid-gate-cache/0f237862c007f6a53122f2bdfb3c87e6366ec133`(`role_paths.tree_blobs`→`extract_blobs`→`dir_matches` -- `ensure_cache`와 같은 일, 22파일, `interface_card.py`가 gate master blob과 바이트 동일). `plan_tables_hash` `7167e028…6d2596d` |
| S 선행 문서 패치 겹침 | 버리는 브랜치에서 `patch_v3_binding_docs.py` → `patch_v3_scope_docs.py` → `patch_b33_design05.py` 순서로 적용: B33 패치 `applied 2 replacement(s), V7 row line 321, rejection line 338`, numstat design 05 `3 3`·design 10 `1 1`·계획 `1 1` -- **겹침 없음**(되돌림) |
| A 문서 커밋 | 패치 `applied 2` → 재실행 `already applied` → numstat `2 2` design 05 하나, `plan_tables_hash` 불변 → `Role: doc` 커밋 |
| B spec+interface | 초안 복사 → **게이트 캐시의** `interface_card.py <절대 spec> --root <R> --out <절대 interface>` exit 0, **기존 함수 3행**(아래 주의), 신규 시그니처 표 0행. `parse_spec_card`: phase 0.5·red-green·gate_change yes·approval [자기 id]·절 11, phase 0.5 ∈ `phase_order` → `Role: doc` 커밋 |
| C 승인 기록 | `fill_v3_approval.py --check` ok → 작성 `written` → 재실행 `already-present`. target = `200d6534…eeae3` = `weakening_diff.diff_hash`(PYTHONPATH = 게이트 캐시) = `merge_gate.py diff-hash` = 기록. LF·BOM 없음·HTML 주석 없음, `parse-approval` 통과, diff_path 3개. 커밋 경로 = 승인 기록 하나 |
| G 게이트 변경 조건 | `gate_change_ok(HEAD)` **True**, `HEAD~1`(승인 커밋 전) False, `approved_hashes(HEAD)`에 target, `_approved_ids` 36 그대로(diff 기록은 면제 원소가 아니다) |
| E EL4 | 가짜 gate에 커밋을 넣고 `merge_gate.py receive --git-dir <gate.git> --old 0f23786 --new <C>` → **exit 0**. 대조: 트레일러 없는 커밋 하나를 더한 것 → **exit 1** "[EL4 거부] …: 트레일러 `Role: code|test|audit|doc|user`가 정확히 하나가 아니다([])"(게이트가 실제로 거부함) |

* target은 blob 기반(00-common §8.2)이라 모의 두 번 모두 같은 값이었다. 실제 착수 때는 design 05의 base blob이 34·35 문서 패치로 바뀌므로 **값이 달라진다**(fill 스크립트가 다시 계산).
* **interface card 주의**: '관찰 가능한 계약' 절 백틱 토큰이 엔진 def 이름과 겹치면 행이 생긴다. 맨 이름 토큰(`run`·`build_graph`·`__post_init__`·`__init__`)을 `run_harness.py::run`·`reachability.build_graph`·`Cls.__post_init__`·`Cls.__init__`·`Sub.__init__`로 고쳐 5행 → 3행으로 줄였다(뜻 불변). 남은 3행(`SemiEmpiricalGmIdLUT.__init__`·`InfeasibleSizingError.__init__`·`Transistor.__post_init__`)은 계약 절 안 '문구 변경'(design 05 새 문구 인용 -- 패치와 바이트가 같아야 해서 고치지 않음)의 맨 `__init__`·`__post_init__`에서 나온다. test-author 브리프에 '피검 심볼 아님'으로 적었다.
* EL3(커밋 hook)는 모의하지 않았다(빈 hooksPath -- V3 card 키트 선례와 같은 범위).

### 0.6 착수 직전에 다시 볼 것(순서대로, 하나라도 어긋나면 멈추고 card 재측정)

1. **선행 넷 병합·정리 끝**: gate master에 34·35·B34·B26-1(그리고 그 사이 B26 계열) `audit:` 커밋, `git branch --list 'role/*'` 비어 있음(design 05 §12 -- 역할 브랜치가 있으면 문서 커밋 push가 EL1 거부).
2. **`reachability.py` 불변**: `git -C <R> diff --quiet 0f23786 gate/master -- tools/gates/reachability.py` (바뀌었으면 시제품 `base` 변형이 HEAD 도구와 간선이 같은지부터 -- `run_headline.sh`의 `edges_equal_head_tool`이 false면 card 사실 문장 전체 재측정).
3. **머리 수치·과거 기록**: 새 격리 복제본(`C:/g<n>`, gate master)에서 `bash _drafts/b33_kit/run_headline.sh <복제본> <출력>` → `python -B _drafts/b33_kit/summarize.py <출력> _drafts/b33_kit/out/head_0f23786/m1.jsonl`.
   단정: `edges_equal_head_tool true`, 개정 미도달 ⊆ base 미도달, 인벤토리 0 회귀 0, 옛 간선 제거가 전부 dunder·도달 감소 0, **m4 `not_same_or_error` 0**(새로 생긴 34·35·B34·B26 계열 기록의 쌍 포함). 하나라도 어긋나면 card '작성 전 실측'·계약 14 숫자를 고치고, m4 불일치는 그 쌍의 경로를 찾아 보고(누수에 기댄 도달이면 사용자 보고 -- 면제 승인 또는 그 card 재작업).
4. **34·35 케이스 무동작 미리보기**: `run_redteam_variants.py`로 `--only 34-v3-exempt-binding`·`--only 35-v3-changed-scope`를 base 복제본(`-`)과 시제품 복제본(`fixed`)에서 → 단계 판정 차이 0(계약 14 미리보기 -- 판정은 auditor).
5. **card 줄 번호**: `grep -n` 으로 `mutate_changed.py`(`inventory`·`build_graph`·`TimeoutExpired`·`killed`), `rt.py`(`def build_vrepo`·`def a_vcase`), `sizing_recipe.py` `super().__init__` 줄을 다시 재고 card의 "`0f23786` 줄" 표기를 실제 줄로 고친다(또는 표기 유지 -- 심볼이 앵커라 판정에 영향 없음). `ls attacks`에 `33-*` 없음·`34-*`·`35-*` 있음.
6. **문서 패치**: `patch_b33_design05.py <R>`가 `applied 2 replacement(s)`를 내는지(앵커 불일치면 exit 1, 아무것도 쓰지 않음). `plan_tables_hash` 전후 같음.
7. **interface card**: 게이트 캐시(`<git-common-dir>/gmid-gate-cache/<gate master 전체 sha>/interface_card.py`)로 만든 결과가 모의(0.5)와 같은 모양인지 -- 기존 함수 행은 계약 절 백틱 토큰과 엔진 def 이름이 겹칠 때만 생긴다(엔진 def 이름이 바뀌었으면 달라질 수 있다).
8. 셸: hook(`role_guard.py`)은 `(cd … && …)`·상대 경로 쓰기 대상·변수 든 `rm`을 거부한다 -- 아래 명령은 전부 절대 경로·`git -C`.
   또 이번 작업에서 `ls <R>/.git/gmid-gate-cache/`가 `[EL1 거부] 저장소 내부를 가리키는 인자`로 거부됐다 -- 0.7의 `$CACHE/…` 호출이 같은 이유로 거부되면
   `sim_launch.sh` A~G 부분처럼 스크립트 안에서 부른다(`bash <스크립트>` -- post_p10b runbook 선례, EL1은 스크립트 안 명령을 보지 않고 커밋은 EL3·EL4가 판정).

### 0.7 명령 시퀀스(오케스트레이터, MSYS bash -- 0.6 통과 뒤)

```bash
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
DR=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
PY=C:/Python314/python.exe
ID=20260930-v7-registry-edges
D05=docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md
# 4.0 착수 전 확인
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/ .ai/approvals/)"
GM=$(git -C "$R" rev-parse gate/master)
CACHE=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)/gmid-gate-cache/$GM   # hook의 role_paths.ensure_cache가 만든 것(없으면 아무 git 명령 한 번 뒤 다시 확인)
test -f "$CACHE/interface_card.py"
BASE=$GM
# A. 문서 커밋(design 05 §10 V7 행 + 거부 증명 줄)
$PY -B "$DR/patch_b33_design05.py" "$R"                       # applied 2 replacement(s)
$PY -B "$DR/patch_b33_design05.py" "$R"                       # already applied
git -C "$R" diff --numstat                                     # 2 2 design 05 한 줄만
git -C "$R" add -- "$D05"
git -C "$R" commit --trailer "Role: doc" -m "docs: $ID 문서 커밋(design 05 §10 V7 행 그래프 규칙 명시 -- 레지스트리 바인딩 네 형식·생성자 호출 위치·dunder 폴백 제거·소스 노드 안 도달, 거부 증명 줄 공격 33)"
# B. spec card + interface card(게이트 캐시의 interface_card.py, 절대 경로)
cp "$DR/draft_b33.final.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
$PY -B "$CACHE/interface_card.py" "$R/docs/02-design/specs/$ID.spec.md" --root "$R" --out "$R/docs/02-design/specs/$ID.interface.md"
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 게이트 변경 spec card $ID(V7 정적 호출 그래프 -- R1 레지스트리 바인딩, R2 생성자 호출 위치만, R2' dunder 폴백 제거, R3 소스 노드 안 도달) + interface card"
SPECC=$(git -C "$R" rev-parse HEAD)
# C. 승인 기록(target = weakening_diff.diff_hash(BASE, SPECC, diff_path 3개), compute_diff_hash 재대조, 주석 제거, 머리 파싱)
$PY -B "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC" --check
$PY -B "$DR/fill_v3_approval.py" --root "$R" --draft "$DR/approval_$ID.md" --base "$BASE" --head "$SPECC"
PYTHONPATH="$CACHE" $PY -B -c "import sys,weakening_diff as wd;print(wd.diff_hash(*sys.argv[1:4],sys.argv[4:]))" "$R" "$BASE" "$SPECC" \
  "$D05" "docs/02-design/specs/$ID.interface.md" "docs/02-design/specs/$ID.spec.md"     # = 기록 target
git -C "$R" add -- ".ai/approvals/$ID.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 승인 기록 $ID(B33 게이트 변경 승인 + Q1 (a) 호출 위치만, target_kind diff -- spec card·interface card·design 05 V7 행·거부 증명 줄)"
# 확인(되돌릴 수 있는 지점 -- push 전)
PYTHONPATH="$CACHE" $PY -B -c "import sys,merge_gate as mg;print(mg.gate_change_ok(mg.TreeView(['-C',sys.argv[1]],'HEAD'),sys.argv[2]))" "$R" "$ID"   # True
# D. push -- 단독 실행, 전체 출력 확인(병렬·tail 금지)
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
# E. test worktree(design 05 §12 순서 1)
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```

이어서 §12 순서 2(test-author, 1절) → 3(auditor freeze·base 표, 3.1) → 4(code worktree, 부모 = T) → 5(code-author, 2절) → 6(병합) → 7(auditor 판정, 3.2·3.3) → 8(`push gate role/audit/$ID:master`) → 정리.
그다음 G1 키트 재측정(B33 병합본 `reachability.py` 위에서).

---

## 1. test-author 브리프(gmid-test-author, §12 순서 2)

```
역할: gmid-test-author. change id = 20260930-v7-registry-edges (게이트 변경, red-green, phase 0.5).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v7-registry-edges-test (브랜치 role/test/20260930-v7-registry-edges). 모든 명령은 절대 경로(git -C, cd 금지).
쓰기 경로: tools/gates/redteam/attacks/33-v7-registry-edges/ 만(계획 N3.12.2 'gmid-test-author | tools/gates/redteam/** | 게이트 변경' -- spec card gate_change: yes + 승인 기록).
           lib/rt.py·run_all.py·다른 케이스는 고치지 않는다(이 card는 하네스 변경이 없다 -- 승인 범위).
입력: interface card docs/02-design/specs/20260930-v7-registry-edges.interface.md, spec card의 '관찰 가능한 계약'(계약 1~14 + 머리의 공통 base),
      '판정 유형 근거', 'oracle 종류와 출처'(단계 표 30행), '거부해야 할 입력'.
      interface card의 기존 함수 3행(SemiEmpiricalGmIdLUT.__init__·InfeasibleSizingError.__init__·Transistor.__post_init__)은 계약 절에 인용한
      design 05 문구의 맨 `__init__`·`__post_init__` 토큰이 엔진 def와 겹쳐 생긴 것이다 -- 피검 심볼이 아니고 합성 케이스와 무관하다(신규 시그니처 0행).
열람 금지: tools/gates/reachability.py(피검), tools/gates/mutate_changed.py, _drafts/b33_kit/·_drafts/b33_scripts/(오케스트레이터 측정 시제품 -- 기대값의 출처가 될 수 없다).
           redteam 하네스(lib/rt.py·lib/iface.py·lib/sb.py·run_all.py)와 기존 케이스(attacks/29·31, v7_unwired, v3_survivor)는 읽어도 된다.
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20260930-v7-registry-edges" -m "test: …"
```

### 1.1 산출물

* `tools/gates/redteam/attacks/33-v7-registry-edges/`:
  * `expect.json` -- 선례 `attacks/31-v3-git-history/expect.json` 모양: `"layer": "V7"`, `"exit": 1`, `"message_contains": []`, `"modes": ["direct"]`, `"phase": "0.5"`, `"steps_from_records": true`, `basis`(spec card 계약·oracle (a)), `title`.
  * `run.sh` -- `set -e`, `rt() { "$PY" -B "$RT" "$@"; }`, `rt vcase v.json`(머리 주석에 기대 근거).
  * `v.json` -- `{"cases": [ … 30단계 … ]}`. 단계마다 `step`, `tool`(`V7` 또는 `V3`), `kind`(기대 exit 0 = `control`, 1 = `attack`), **`base`**, `head`, `expect` = {`exit`, `layer`(= `tool`), `message_contains`(정확한 JSON 조각 목록), `basis`(계약 번호·문장)}. V3 단계는 `subjects`.
* 경로 상수: `A/` = `skills/analog-gmid-design/assets/`, 엔진 `A/rt_engine.py`, 하네스 `workspaces/run_harness.py`(설정 루트 `workspaces/run_harness.py::run`·`::__main__`이 실제로 있게).

### 1.2 구성 규칙(계약 머리·oracle 절)

* **`base` 사전은 단계마다 넣는다**(`build_vrepo`는 단계의 `base`만 읽는다 -- 빠지면 `rt_gain`·`run`도 새 def가 되어 기대가 틀어진다). 공통 base = 엔진 `rt_gain(gm, ro)`(docstring 포함) + 하네스 `from rt_engine import rt_gain` / `def run(x): return rt_gain(x, 2.0)`. `ctor-super-leak`만 다른 base.
* **하네스 최상위에는 import 문만**(루트에 `__main__`도 들어가 하네스 모듈 최상위가 도달한다 -- 거기서 바인딩을 읽으면 거부 단계가 의도와 다르게 통과한다). 바인딩·호출은 `run` 안에.
* 각 단계의 head는 base 파일을 **다시 적는다**(엔진 = base 엔진 + 추가분, 하네스 = 새 import + 새 `run`). head에서 빠진 base 파일은 그대로 남는다(`None`일 때만 삭제).
* 미도달 기대는 `"unreached_without_approval": ["skills/analog-gmid-design/assets/rt_engine.py::<qualname>", …]` -- **목록 전체**, `new_defs`와 같은 정렬(파일 경로 → qualname 오름차순). PASS 기대는 `"verdict": "PASS"`(+ 필요하면 `"new_defs": []`, `"unreached": [...]`).
* 면제 승인 기록은 **head** 사전의 `.ai/approvals/<id>.md` 파일(`---` 머리, `target_kind: decision`, `target: <파일>::<qualname>`) -- `approve_after_head`(diff 승인 전용)는 쓰지 않는다. 파일 이름이 `_`로 시작하면 도구가 무시한다.
* 기대값은 card 계약 문장과 구성에서만 만든다. 피검 도구 출력을 복사하지 않는다(base 도구 출력은 red 확인용).

### 1.3 단계 표(30단계 -- spec card oracle 표 그대로, 역할 열은 이 브리프의 분류)

| # | 단계 | tool | head 변경(요지) | 기대(새 도구) | base 도구 | 역할 |
|---|---|---|---|---|---|---|
| 1 | `registry-wired` | V7 | 새 `_f_b`, `_REG = {"b": _f_b}`, 새 `rt_pick(k, x)`가 `_REG[k](x)`, `run`이 `rt_pick` | exit 0 PASS | exit 1 | red (계약 1 같은 파일 이름) |
| 2 | `registry-imported` | V7 | 새 `_f_i`, `_REG_I`, 하네스 `from rt_engine import rt_gain, _REG_I`, `run`이 읽음 | exit 0 | exit 1 | red (계약 1 `from M import`) |
| 3 | `registry-modattr` | V7 | 새 `_f_m`, `_REG_M`, 하네스 `import rt_engine`, `run`이 `rt_engine._REG_M["m"]` | exit 0 | exit 1 | red (계약 1 `M.NAME`) |
| 4 | `registry-reexport` | V7 | 새 `A/rt_reg.py`(`_f_r`, `_REG_R`), `rt_engine.py` 첫 줄 `from rt_reg import _REG_R`, 하네스 `from rt_engine import _REG_R` | exit 0 | exit 1 | red (계약 1 재수출) |
| 5 | `registry-orphan` | V7 | 새 `_f_c`, `_ORPHAN = {"c": _f_c}`, 참조 없음(하네스는 `import rt_engine`만) | exit 1 `[_f_c]` | exit 1 | 거부 (계약 2, R0 배제) |
| 6 | `registry-dead-reader` | V7 | 새 `_f_d`, `_DEADREG`, 새 `_dead_reader`만 읽음(호출 0) | exit 1 `[_dead_reader, _f_d]` | exit 1 | 거부 (계약 2) |
| 7 | `registry-external-attr` | V7 | 새 `_f_p`, 고아 `pi = {"p": _f_p}`, 하네스 `import math`, `run`이 `math.pi * rt_gain(...)` | exit 1 `[_f_p]` | exit 1 | 거부 -- **독립 검토 구멍 ② 그래프 밖 재수출(B2)** |
| 8 | `registry-attr-collision` | V7 | 새 `_f_a`, 고아 `cache = {"a": _f_a}`, `run`이 `rt_gain(x.cache, 2.0)` | exit 1 `[_f_a]` | exit 1 | 거부 -- **구멍 ③ 속성만으로 레지스트리 도달(B3)** |
| 9 | `registry-str-collision` | V7 | 새 `_f_s`, 고아 `_STRREG = {"s": _f_s}`, `run`이 문자열 `"_STRREG"`만(dict 키) | exit 1 `[_f_s]` | exit 1 | 거부 -- **구멍 ③ 문자열만으로 레지스트리 도달(B3)** |
| 10 | `registry-name-strings` | V7 | 엔진 `_DOC_NAMES = ("rt_h2",)`, 새 `rt_named(n)`이 `n in _DOC_NAMES`, 새 `rt_h2` 호출 0, `run`이 `rt_named` | exit 1 `[rt_h2]` | exit 1 | 거부 -- 구멍 ③의 바인딩 값 문자열(S1) |
| 11 | `registry-local-shadow` | V7 | 새 `_f_t`, 고아 모듈 `_TABLE = {"t": _f_t}`, 새 `rt_lookup(k)`가 지역 `_TABLE = {}` 읽음, `run`이 `rt_lookup` | exit 1 `[_f_t]` | exit 1 | 거부 (계약 1 음성, 함수 지역 이름) |
| 12 | `registry-reexport-other` | V7 | 새 `A/rt_reg.py`(`_f_y`, `_REG_Y`) 재수출, 하네스 `from rt_engine import _REG_Y`, 새 `A/rt_other.py`의 고아 `_REG_Y = {"y": _f_y2}` | exit 1 `[rt_other.py::_f_y2]`만 | exit 1(목록 `_f_y`·`_f_y2` -- 조각 불일치로 FAIL) | 거부 + red(목록) -- 구멍 ②의 다른 모듈 같은 이름(S3) |
| 13 | `registry-reexport-x-outside` | V7 | `rt_engine.py` 첫 줄 `from math import pi`(재수출 사슬 끝 X = 그래프 밖), 하네스 `from rt_engine import rt_gain, pi`, `run`이 `pi * rt_gain(x, 2.0)`, 새 `A/rt_other.py`의 고아 `pi = {"q": _f_q}` | exit 1 `[rt_other.py::_f_q]` | exit 1 | 거부 -- 구멍 ②의 사슬 끝이 그래프 밖(review3 S1) |
| 14 | `registry-bare-name-other` | V7 | 하네스는 `from rt_engine import rt_gain`만, `run`이 import 없이 `_REG_Z["z"](rt_gain(x, 2.0))`, 새 `A/rt_other.py`의 고아 `_REG_Z = {"z": _f_z}` | exit 1 `[rt_other.py::_f_z]` | exit 1 | 거부 (계약 1 음성, import 없는 맨 이름 -- review3 m1) |
| 15 | `ctor-wired` | V7 | 새 `class RtBox: __init__`, `run`이 `RtBox(…)` | exit 0 | exit 1 | red (계약 3) |
| 16 | `ctor-raise` | V7 | 새 `RtError(Exception).__init__`, 새 `rt_check`가 `raise RtError`(호출 없이), `run`이 `rt_check` | exit 0 | exit 1 | red (계약 3) |
| 17 | `ctor-inherited` | V7 | 새 `RtBase.__init__`, `class RtSub(RtBase): pass`, `run`이 `RtSub(…)` | exit 0 | exit 1 | red (계약 3) |
| 18 | `ctor-dataclass-post-init` | V7 | `from dataclasses import dataclass`, `@dataclass class RtDev` + `__post_init__`, `run`이 `RtDev(…)` | exit 0 | exit 1 | red (계약 3) |
| 19 | `ctor-super-chain` | V7 | 새 `RtBase2.__init__`, `RtSub2(RtBase2).__init__`이 `super().__init__(v)`, `run`이 `RtSub2(…)` | exit 0 | exit 1 | red (계약 3 `super()`) |
| 20 | `ctor-in-binding` | V7 | 새 `RtHandler.__init__`, `_HANDLERS = {"k": RtHandler(rt_gain)}`, 새 `rt_dispatch`가 읽음, `run`이 `rt_dispatch` | exit 0 | exit 1 | red (계약 3 바인딩 값 생성자) |
| 21 | `ctor-isinstance-only` | V7 | 새 `RtOnly.__init__`, `run`은 `isinstance`·`except RtOnly:`·주석 `v: RtOnly`만 | exit 1 `[RtOnly.__init__]` | exit 1 | 거부 (계약 4, Q1 (a)) |
| 22 | `ctor-super-leak` | V7 | **단계 base**: `RtErr(ValueError).__init__`이 `super().__init__(m)`, `rt_check2`가 `raise RtErr("neg")`, `run`이 `rt_check2`. head: 인스턴스화 0인 새 `RtNever.__init__`만 | exit 1 `[RtNever.__init__]` | exit 1 | 거부 -- **구멍 ① `super().__init__` 누수(B1)** |
| 23 | `ctor-factory-limit` | V7 | 새 `RtFac.__init__`, 하네스 `from collections import defaultdict`, `run`이 `d = defaultdict(RtFac)` 후 `d["k"]` 읽음(`RtFac(...)` 호출 없음) | exit 1 `[RtFac.__init__]` | exit 1 | **known_limit -- 팩토리 모양 거짓 FAIL(Q1 (a)로 받아들임, 계약 4)** |
| 24 | `ctor-factory-exempt` | V7 | 23 + head `.ai/approvals/20260930-rt-v7-factory.md`(`target_kind: decision`, `target: …/rt_engine.py::RtFac.__init__`) | exit 0, `"unreached": [RtFac.__init__]`, `"unreached_without_approval": []` | exit 0 | **면제 처리 -- 그 거짓 FAIL을 면제 승인으로(계약 8)** |
| 25 | `leak-test-name` | V7 | 엔진 새 `rt_area(a)`가 `a.rt_sz(2.0)`, 새 `rt_g`, `A/tests/probes/p_rt.py`의 `rt_sz`만 `rt_g` 호출, `run`이 `rt_area` | exit 1 `[rt_g]` | **exit 0**(거짓 PASS) | red (계약 5 R3) |
| 26 | `leak-test-string` | V7 | 새 `rt_h`(호출 0), `A/tests/contracts/test_rt_names.py`에 `_RT_NAMES = ("rt_h",)`와 `_rt_rel`, `run`이 `_rt_rel("a")`(이름 폴백) | exit 1 `[rt_h]` | exit 1 | 거부 (계약 6) |
| 27 | `approved-still-exempt` | V7 | 5 + head `.ai/approvals/<id>.md`(decision, `target: …::_f_c`) | exit 0, `"unreached": [_f_c]` | exit 0 | 대조군 (계약 8 면제 불변) |
| 28 | `direct-call-control` | V7 | 새 `rt_twice`, `run`이 직접 호출 | exit 0 | exit 0 | 대조군 (계약 8) |
| 29 | `binding-not-a-def` | V7 | 새 def 없이 `_RT_UNUSED = {"k": 1}`만 | exit 0, `"new_defs": []` | exit 0 | 대조군 (계약 7) |
| 30 | `v3-registry-inventory` | V3 | 새 `_metric_rt_x`(2배, docstring), `_RT_METRICS = {"x": _metric_rt_x}`, 새 `rt_compute(kind, v)`가 읽음, test `A/tests/test_rt_compute.py`가 `rt_compute("x", 3.0) == 6.0`; `subjects` = `rt_engine.rt_compute`·`rt_engine._metric_rt_x` | exit 0 `"verdict": "PASS"` | exit 1(인벤토리 없음 → 생존) | red (계약 10) |

* 합계(30단계): red 12(1~4·15~20·25·30이 base exit ≠ 기대 exit = V7 11 + V3 1, 그리고 12는 exit가 같고 목록이 달라 base에서 FAIL -- red 집합에 넣지 않고 '+ 12번 목록'으로 센다) · 거부 13(5~14·21·22·26) · known_limit 1(23) · 대조군·면제 4(24·27~29).
  base 도구에서 FAIL 13 = red 12 + 12번 목록. 오케스트레이터 측정(같은 구성, `0f23786`): 28단계 base 13 FAIL / 시제품 28 PASS(0.2), review3 2단계(13·14)를 더한 30단계 base 13 FAIL / 시제품 30 PASS(0.2, `C:/g138`).
* **독립 검토 구멍 3건**(사용자 승인 질문의 "막았다"는 이 단계들이 지킨다): ① `super().__init__` 누수 = 22, ② 그래프 밖 재수출 = 7(그리고 같은 이름 다른 모듈 12, 재수출 사슬 끝 X가 그래프 밖 13), ③ 문자열·속성만으로 레지스트리 도달 = 8·9(바인딩 값 문자열 10). 계약 1의 import 없는 맨 이름 = 14. 이 단계들은 base 도구도 exit 1이라 red가 아니다 -- 몫은 **느슨한 구현을 거부하는 것**(30단계 실측 `C:/g138`: 초안 v1 문장 구현은 7·10·11·12·13·22, 바인딩을 기존 이름 색인에 넣은 구현은 7~14·22, 사슬 끝 이름 폴백 구현 `xout`은 13만, 맨 이름 다른 파일 폴백 구현 `bare`는 14만 FAIL -- 28단계 판은 개정 기록 §2.3).
* **팩토리 모양**(23·24): 사용자 Q1 답 "(a) 호출 위치만 -- 팩토리 모양은 거짓 FAIL → 면제 승인 처리"를 그대로 고정한다. 23은 '받아들인 대가'(known_limit, 계약 4), 24는 그 처리 경로(계약 8). 23을 green(exit 0)으로 바꾸는 구현은 Q1 (b) 쪽으로 넓힌 것이라 이 단계가 잡는다.
* V3 단계(30)의 test 파일은 head에 둔다. `sys.path`에 엔진 디렉터리를 넣는 import(선례 31 `test_rt_scale_history.py` 머리 모양).

### 1.4 자기 점검(커밋 전)

* `C:/Python314/python.exe -B <worktree>/tools/gates/redteam/run_all.py --phase 0.5 --mode direct --only 33-v7-registry-edges` → base 도구(지금 worktree의 `reachability.py`)에서 **FAIL 13단계 = red 12 + 12번**이어야 한다. 그 밖의 단계가 FAIL이면 구성이 틀렸다(대개 `base` 누락·하네스 최상위 코드).
* 같은 명령을 `--only` 없이 한 번 -- FAIL 케이스는 33뿐이어야 한다(케이스 하나가 수십 분 걸릴 수 있다 -- 15-records 선례 27분).
* 기대는 계약 문장에서만. `expect.json`·`v.json`의 `basis`에 계약 번호를 적는다.

---

## 2. code-author 브리프(gmid-code-author, §12 순서 5)

```
역할: gmid-code-author. change id = 20260930-v7-registry-edges (게이트 변경, red-green).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v7-registry-edges-code (브랜치 role/code/20260930-v7-registry-edges, 부모 = test 커밋 T). 절대 경로만, cd 금지.
쓰기 경로: tools/gates/reachability.py 하나(계획 N3.12.2 'gmid-code-author | tools/gates/*.py | 게이트 변경'). mutate_changed.py·redteam/**·문서는 쓰지 않는다
           (design 05 문구는 오케스트레이터 문서 커밋에 이미 있다 -- 계약 13의 docstring만 이 파일 안).
입력: spec card·interface card. test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20260930-v7-registry-edges.md)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다.
열람 금지: _drafts/b33_kit/reachability_b33.py·_drafts/b33_scripts/(오케스트레이터 측정 시제품 -- 기대값을 정할 때 쓴 것이라 구현이 그것을 베끼면 기대와 구현의 출처가 같아진다).
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20260930-v7-registry-edges" -m "…"
```

### 2.1 바꿀 것(계약 번호)

1. **바인딩 노드(R1, 계약 1·2·7·9)**: 파일마다 `tree.body` 바로 아래의 `NAME = <식>`(대상이 전부 맨 이름 -- `a = b = {...}`는 둘 다, 튜플 대상은 아님)·`NAME: T = <식>`(값 있는 것)에 노드 id `<파일>::=NAME`. **노드 집합(`nodes`)에는 넣지 않는다** -- 간선 사전의 키·값에만(계약 9, `new_defs`·`unreached`에 `::=`가 나오면 안 된다 -- 계약 7). 같은 이름이 여러 번 바인딩되면 값 식들의 참조를 합친다.
   * 바인딩 노드 → 값 식의 이름·속성 참조(기존 해석)와 생성자 참조(R2). **값 식 안의 문자열 상수는 간선을 만들지 않는다**(함수 몸체·`<module>`·`__main__`의 기존 문자열 규칙은 그대로 -- 계약 9 단조성).
2. **바인딩으로 가는 간선(네 형식뿐, 계약 1 음성 목록)**: (i) 같은 파일 맨 이름 `NAME`(Load) -- 그 함수의 지역 이름(인자·대입 대상·중첩 def/class 이름·`except … as`·`for`·`with … as`·comprehension 바깥에서 대입된 이름; `global`/`nonlocal` 선언 이름은 제외)이면 아님, (ii) `from M import NAME`(별칭 포함), (iii) `import M`(별칭 포함)의 `M.NAME`, (iv) M에 그 바인딩이 없으면 M 파일의 `from X import NAME`을 따라 X의 바인딩(재수출, **방문 집합으로 순환 차단, 깊이 상수 금지**). M·X는 `GRAPH_PREFIXES` 안 모듈일 때만. 비모듈 속성 `x.NAME`, 문자열 `"NAME"`, import 없는 다른 파일의 같은 이름, 같은 이름의 다른 모듈 바인딩은 **가지 않는다**. import 문장 자체는 간선이 아니다(R0 거절).
3. **생성자(R2, 계약 3·4)**: 도달 가능한 코드(def 몸체·`<module>`·`__main__`·바인딩 값 식)의 **호출 위치** `Cls(...)`와 `raise Cls`(호출 없이) → 그 클래스의 `__init__`·`__new__`·`__post_init__`, 없는 것은 기반 클래스(bases를 같은 규칙으로 해석, 재귀 -- 키마다 한 번 계산해 캐시). `Cls` 해석은 2와 같은 형식(같은 파일 클래스·`from M import Cls`·`M.Cls`·재수출). `x.Cls(...)`(x가 모듈 별칭 아님)·import 없는 다른 파일 클래스·호출이 아닌 클래스 이름(`isinstance`·`except`·주석·`defaultdict(Cls)` 인자)은 생성자로 가지 않는다(Q1 (a)).
   `super().__d__`(dunder) → 둘러싼 클래스의 기반 클래스의 `__d__`(기반에 없으면 그 기반의 기반).
4. **dunder 속성 폴백 제거(R2', 계약 4·9)**: 속성 참조 `x.__y__`·`M.__y__`(이름이 `__`로 시작·끝)는 같은 이름 def 전역 폴백(`by_name`)을 쓰지 않는다. 모듈 별칭 `M.__y__`의 그 모듈 def는 그대로. 옛 간선에서 빠지는 것은 이것뿐이어야 한다(HEAD 3개).
5. **운영 범위(R3, 계약 5·6)**: V7 `main`의 도달 계산만 소스 분류(`_is_source`) 파일의 노드(바인딩 노드도 그 파일이 소스일 때만)를 따라간다. `build_graph`·`reach`의 V3 쪽 동작(test 노드 출발)은 R3를 모른다 -- `mutate_changed.py`가 부르는 `rch.reach(graph_edges, [t])`의 시그니처·결과 의미를 바꾸지 않는다(선택 인자를 더하면 기본값이 지금 동작).
6. **docstring(계약 13)**: 모듈 docstring 그래프 설명(10~13행)을 design 05 §10 V7 새 문구와 같은 뜻으로.
7. **원칙(계약 11)**: 파일당 `ast.parse` 1회, 바인딩·클래스·import 색인을 같은 순회에서. 함수 지역 이름 집합은 함수당 한 번. 회로·넷·소자 이름·`library/`·`.topology.json` 리터럴 금지, `gate_config.json` 말고 JSON 읽기 금지.

### 2.2 하지 말 것

* `mutate_changed.py` 수정(계약 10은 코드 변경 없이 PASS여야 한다), `build_graph` 반환 모양(`(노드 집합, 간선 사전)`) 변경, JSON 출력 키·exit 규칙 변경(계약 8).
* 광범위 `except`(V6·공격 27f), 표준 라이브러리 밖 import, 재수출 깊이 상수.
* 새 보조 함수를 만들고 `build_graph`/`main`에서 안 부르는 것(미배선).

### 2.3 자기 확인(판정 근거 아님)

* `run_all.py --phase 0.5 --mode direct --only 33-v7-registry-edges` → 30/30 PASS. `--only` 없이 전체 FAIL 0(특히 `v7_unwired`·`v3_survivor`·26·27f·28·29·31·34·35).
* 저장소 HEAD 트리에서 `build_graph` 한 번: 옛 간선 중 빠진 것이 dunder 폴백뿐인지(계약 9).

---

## 3. auditor 브리프(gmid-verification-auditor, §12 순서 3·7)

```
역할: gmid-verification-auditor. change id = 20260930-v7-registry-edges, evidence_type red-green, 게이트 변경(phase 0.5).
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v7-registry-edges-audit (브랜치 role/audit/20260930-v7-registry-edges).
모든 측정은 격리 복제본에서(§12-7): git clone --no-hardlinks --no-local <audit worktree> <scratch>/iso → git -C <scratch>/iso remote remove origin.
scratch는 새 C:/g<n> 하나만(다른 C:/g* 건드리지 말 것), 끝나면 그 폴더만 삭제. 셸 가드: set -euo pipefail, git -C <절대 경로>만, cd 실패 시 중단, (cd … && …) 금지(role_guard 거부). 끝나면 실제 저장소 git status·reflog 불변 확인.
게이트 코드는 base 판(= approval 커밋 뒤 gate master, 순서 0의 HEAD)을 git cat-file로 추출한 사본(캐시와 바이트 동일 확인).
작성자(test·code) 보고와 오케스트레이터 착수 키트(_drafts/b33_kit 수치)는 증거로 받지 않는다 -- 다시 잰다.
판정 기록 .ai/verification/20260930-v7-registry-edges.json + .ai/verification/20260930-v7-registry-edges/{scripts,out}/, Role: audit 커밋(판정 순서에서만 한 커밋 -- 순서 3 산출물은 쓰기만).
```

### 3.1 순서 3(freeze·base 확인 → `base_check.json`)

* **커밋하지 않는다**: base_check.json 등 산출물은 audit worktree에 쓰기만 하고 커밋하지 않는다(커밋은 순서 7에서 M 위 한 커밋).
* T 해시 고정, T 경로가 `tools/gates/redteam/attacks/33-v7-registry-edges/**`뿐인지(`git diff --name-only <base> <T>`).
* base 게이트로 T 복제본에서 `run_all.py --phase 0.5 --mode direct`(전체)와 `--cases 0.5` → **base 표**(케이스·단계 판정, log sha256).
* red: 33의 30단계 중 base FAIL = red 12 + `registry-reexport-other`(목록)인지, 원인이 계약과 맞는지 단계별로(1~4·15~20 exit 1 = 레지스트리·생성자 간선 없음, 25 exit 0 = 이름 폴백 누수, 30 exit 1 = 인벤토리 없음 생존, 12 = 목록에 `_f_y` 포함). `failure_hashes` = base 판 `merge_gate.red_failure_hash("tools/gates/redteam/attacks/33-v7-registry-edges::<step>", "redteam.FAIL")`.
* **판별력**(base 표만으로 못 보는 것): 거부 단계(5~14·21·22·26)와 known_limit 23이 **느슨한 구현을 실제로 거부하는가** -- auditor가 card 문장에서 직접 만든 잘못된 구현 변형 셋 이상(예: 바인딩을 기존 이름 색인에 넣음, 재수출 폴백을 그래프 밖 모듈까지, dunder 폴백 유지, 클래스 이름 참조 전부를 생성자로)을 격리 복제본의 `reachability.py`로 바꿔 33을 돌려 각 거부 단계가 최소 한 변형에서 FAIL인지. 어느 변형에서도 FAIL하지 않는 거부 단계는 test 결함 후보로 보고.

### 3.2 순서 7(병합본 판정) -- design 05 §18, 선례 `20260930-v3-history-clone.json` 모양

* 순서 3 산출물(base_check.json 등)은 이미 audit worktree에 미커밋으로 있다 -- 이 순서 7의 한 커밋(M 위, `Role: audit`)에 판정 기록과 함께 넣는다.

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | **PASS** | (1) pytest 전체(auditor_run `V1:` 명령, base 판 `pytest_gate.ini`, `-k`·`--deselect`·`-x` 없음, `--gmid-phase=0.5 --gmid-strict=`, 엄격 집합 base 판 `merge_gate.strict_set`, `v1_command_check` 위반 0) -- 변경 경로가 전부 `tools/gates/**`라 대상 트리 불변. (2) 병합본 redteam 전체 + `--cases 0.5`, **순서 3 base 표와 케이스·단계 단위 기계 대조**: 판정이 바뀐 케이스는 33(FAIL→PASS) 하나, 단계는 33의 13단계 = red 집합 + 12번. `v7_unwired`·`v3_survivor`·26·27f·28·29·31·**34·35** 포함 나머지 같음(계약 14), `--cases 0.5` 차이 0 |
| V2 | N/A(도입 1) | 참고: 커밋 사슬 base → T(Role: test, attacks/33) → code(Role: code, `reachability.py` 1경로) → 병합(Role: doc), `git diff T 병합 -- tools/gates/redteam` 0 |
| V3 | N/A(도입 1) | 참고: base 판 `mutate_changed.py` targets 빈 목록(게이트 도구는 대상 밖). 같은 그래프의 V3 효과는 계약 10(30번)·12가 판정 |
| V4 | N/A(도입 1) | 참고: oracle 대조 -- 33 기대값이 계약 1~10 문장과 구성에서 왔는지 단계별로(피검 출력에서 만들지 않았는지) |
| V5 | N/A(도입 1) | 참고: `tools/gates/**`는 발견 경로 밖. 사람 판단: 기존 케이스 변경 0, `reachability.py`는 간선 추가 + dunder 폴백 제거(계약 9로 영향 0 실측) + R3(거짓 PASS 차단 -- 강화). 승인 `target`을 base 판 `diff_hash`로 재계산해 일치 |
| V6 | N/A(도입 1) | 참고: base 판 `source_lint.py`. 광범위 except 추가 0(27f) |
| V7 | N/A(도입 2) | 참고: 배선 관찰 -- 새 보조 함수가 `build_graph`/`main`에서 불리는가 |
| V8 | N/A(도입 4) | 엔진 무관 |
| V9 | N/A(도입 6b) | 회로 무관 |
| V10 | PASS | '재현할 수치: 없음' → `reproduced_numbers` 빈 배열. 보고 수치는 `notes`(3.3) |

### 3.3 redteam이 덮지 않는 계약 -- 측정(격리 복제본, base 도구 vs 병합본 도구, 기대값은 계약 문장에서)

| 측정 | 계약 | 내용 |
|---|---|---|
| m1 HEAD 트리 | 9·재현 수치 | 운영 루트 미도달 소스 def(합집합·두 벌, base/병합본), 옛 간선 중 빠진 것 = 전부 dunder 폴백인지와 그 제거로 도달이 준 소스 def 수(R3 없이·있이), 비운영 노드 누수, 면제 두 id(`lut_conditions_from_npz`·`derived_spec`)가 병합본에서도 미도달인지(도달로 바뀌면 경로 확인) |
| m2 코드 확인 | 11 | 파일당 `ast.parse` 1회, 색인 같은 순회, 해석 캐시, 깊이 상수 없음, 회로 리터럴·JSON 읽기 없음(`git grep`), `build_graph` 시간 base/병합본 |
| m3 V3 비용 | 12 | (i) `20260930-restore-plan-functions` V3를 두 도구로(verdict·mutants·killed·survivors·시간·대상별 인벤토리·최대 기준 실행·`--timeout`·`--out`의 `"exit": "timeout"` 건수), (ii) 과거 판정 기록 V3 대상 def 전부(B34·B26 계열 포함)의 정적 인벤토리 base/병합본, (iii) 그중 최대 인벤토리 대상 기준 실행만 두 그래프로 1회 |
| m4 과거 V7 쌍 | 14 | `.ai/verification/2026*.json` 중 V7 근거에 `reachability.py … --base X --head Y`가 있는 기록 전부(그 시점 수를 센다)의 각 쌍에서 두 도구의 `verdict`·`unreached`·`unreached_without_approval` 같음(`--config`는 head 트리의 것, 없으면 병합본의 것) |
| m5 probe | 1·2·3·4 경계 | redteam에 없는 형식: `import rt_engine as E; E._REG`, `from M import NAME as N`, `NAME: T = {...}`, `global NAME` 선언 함수(지역 아님 → 도달), 튜플 대상 대입(바인딩 아님), `__new__`만 있는 클래스, 두 단계 기반 클래스 재귀, `class Sub(M.Base)`, `M.__y__` 모듈 별칭 def(그대로), `x.Cls()`(생성자 아님), 순환 재수출(A↔B, 끝나야 한다), `field(default_factory=Cls)`(미도달 -- known_limit) |
| m6 Q1 대가 | 결정 항목 | 병합본 도구로 HEAD 엔진에서 '팩토리 모양으로만 생성되는 클래스' 수(card: 0, 개정 규칙 위 재측정은 이 판정 기록 몫) |

판정 기록 `approvals` = `["20260930-v7-registry-edges"]`. 관찰(약화 아님)은 V10 끝에: timeout 분리 백로그, 34·35 V3 케이스 인벤토리 변화.

---

## 4. 순서 요약(오케스트레이터)

34·35·B34·B26-1 병합·정리 → 0.6 확인(재측정 1~8) → 0.7 A(문서)·B(spec+interface, 게이트 캐시 `interface_card.py` 절대 경로)·C(승인 기록) → `gate_change_ok` True → push 단독·전체 출력 확인 →
§12 순서 1(test worktree) → test-author(1절) → 순서 3 auditor freeze·base 표(3.1) → 순서 4 code worktree → code-author(2절) → 순서 6 병합(병합 전 `git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v7-registry-edges-audit log --oneline role/test/20260930-v7-registry-edges..HEAD` 출력이 비어야 한다 -- 비어 있지 않으면 순서 3 커밋이 섞인 것, 병합하지 말고 멈춤) → 순서 7 auditor(3.2·3.3) → 순서 8 push → 정리 →
G1 키트 재측정(B33 병합본 위).

## 5. `_drafts/b33_kit/` 내용

| 파일 | 하는 일 |
|---|---|
| `reachability_b33.py` | 시제품(`RCH_VARIANT` = fixed/draft/loose/nosuper/xout/bare/base) -- `b33_scripts/`에서 복사, 측정 전용(역할 열람 금지). `xout`·`bare`는 review3에서 더한 잘못된 구현(fixed + 구멍 하나: 재수출 사슬 끝 X가 그래프 밖이면 이름 폴백 / import 없는 맨 이름 → 다른 파일 같은 이름 바인딩) |
| `run_headline.sh` → `m1_head.py`·`m5_inventory.py`·`m4_records.py` | 머리 수치(미도달·누수·V3 쌍·인벤토리 0·간선 단조성·정적 인벤토리·과거 V7 쌍). 결과 append(`out/<이름>/m1.jsonl`·`m5.json`·`m4.jsonl`), m4는 끊겨도 이어 잰다. 경로는 `C:/…`·`/c/…` 둘 다 된다. **실행 시간**: m4(과거 V7 쌍 29개)만 약 40분(review3 실측) -- harness 기본 background 한도 30분을 넘으므로 `run_in_background` + timeout을 늘려(예: 2시간) 돌린다 |
| `summarize.py` | 위 출력 요약 + 옛 측정(`b33_scripts/m1b.jsonl`)과 미도달 집합 비교 → `summary.json` |
| `run_attack33.sh` → `gen_attack33.py`·`run_redteam_variants.py`, `a33_table.py` | 공격 33 측정용 케이스(30단계 -- 팩토리 2단계, review3 S1·m1 2단계 추가)를 base·시제품 복제본에서 실제 `run_all.py`로. 다섯째 인자로 시제품 변형 목록(기본 `fixed`, 예: `fixed,xout,bare,draft,loose,nosuper`). **경로는 반드시 Windows 형식(`C:/…`)**: 저장소·scratch·출력 경로를 MSYS 형식(`/c/…`)으로 주면 `run_redteam_variants.py`의 Windows Python `subprocess(cwd=…)`가 `NotADirectoryError`로 죽는다. **실행 시간**(2026-10-01 실측, `C:/g138`): 복제 2벌 + base 1회 약 2.5분, 변형 1개당 약 2~2.5분 -- base + 변형 6개 전체 958초(약 16분). 변형을 더 넣거나 다른 측정과 동시에 돌리면 harness 기본 background 한도(30분)에 가까워지므로 `run_in_background` + timeout을 늘려 돌린다 |
| `sim_launch.sh` | 0.5 모의 전체(모래상자 생성부터 EL4 대조까지) |
| `check_user_quote.py` | 승인 초안 사용자 원문 ↔ 세션 기록 대조(질문·선택지 라벨·선택지 설명 -- review3 m2로 설명 대조 추가) |
| (사고 기록) | 첫 `run_headline.sh` 실행에서 `m4_records.py`가 설정 사본을 `os.environ.get("TMP", ".")`에 썼는데 자식 bash에서 TMP가 비어 실행 cwd = **실제 저장소 루트**에 `cfg_*.json` 15개(908바이트, gate 설정)를 썼다(18:07~18:34). 오케스트레이터 지적 뒤 측정 종료를 기다려 그 15개만 리터럴 경로로 지웠고 `git status --short`가 작업 시작 때와 같음을 확인했다. 스크립트는 출력 파일 옆 `cfg_tmp/`에만 쓰게 고쳤다(환경 변수·cwd 무관) |
| `out/` | `head_0f23786/`(m1·m4·m5·summary), `a33_0f23786.jsonl`(26단계)·`a33f_0f23786.jsonl`(28단계)·`a33r3_0f23786.jsonl`(30단계, base + 변형 6개 -- review3)·표, `sim_0f23786/`(모의 로그·interface card·채운 승인 기록), `user_quote.json` |
