---
id: 20261002-p3-move-mod3-circuit-state-graph
phase: 3
evidence_type: equivalence
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split` **v8.5**(사용자 승인 UD-0 `20260930-30-module-split-design`) §8 M행·§8.1·§2.2·§3·§10, card **M3**. 틀과 판정 문언은 M1 초안(`_drafts/draft_p3_m1.spec.md`)을 그대로 따르고, 이 card에서 다른 것만 적는다.
A = `skills/analog-gmid-design/assets`, SR = `A/sizing_recipe.py`, SD = `A/stick_diagram.py`, TL = `A/topology_library.py`, DR = `A/design_report.py`, ACF = `A/audit_current_forced.py`, MOD3 = `A/circuit_state_graph.py`(계획 N3.10 523행 `| MOD3 | `circuit_state_graph.py` | S0 지문, S1 구조 유도(개념당 정본), S1v, 결합 블록, topology 로딩(구조 자동채움을 부르므로) |`).

**무엇을 하는가**: D0b가 다시 쓴 레지스트리 '이관 목적지' 열과 N3.10 표로 `move_plan plan`이 **MOD3(`circuit_state_graph.py`)에 배정한 최상위 단위 전부**를 split 파일(모의 base: SD 39·SR 43)에서 새 파일 `A/circuit_state_graph.py`로 **바이트 그대로** 옮기고,
단위를 내보낸 split 파일마다 그 이름들의 명시 재수출 줄 하나를 남긴다(design §2.2: `from circuit_state_graph import a, b, _c`(design §2.2의 형태 예 -- 실제 이름 순서는 아래 계약 3 (b)), `import *` 금지, def 래퍼 금지). 함수 몸체·클래스·문장은 한 토큰도 바꾸지 않는다(계획 533행). 배정 집합은 card base에서 도구가 낸다 --
이 card는 단위 목록을 손으로 정하지 않는다(작성 전 실측 2의 82단위는 모의 base의 관찰).

**MOD 파일 머리(design D-30)**: `circuit_state_graph.py`의 import 줄 = card base `plan`의 `mod_imports["circuit_state_graph.py"]` **그대로**(이름마다 import 한 번). 모의 base에서 8줄이었다(재현할 수치).
MOD3는 번호 3라 D-22의 '파일 끝 import'(MOD8·MOD9 몫)는 해당 없다 -- 모든 줄이 머리다. 가리키는 트리 모듈은 번호가 작은 MOD뿐이다(ORDER, 계약 7).

**재수출 줄 위치(design §2.2·D-22, W-2 구체화)**: 재수출 줄 = 그 split 파일 앞머리 묶음(docstring 뒤 연속한 `import`·`from … import`·`sys.path` 조작 식 문장) 중 **마지막 import 문 바로 뒤**(앞 card의 재수출 줄도 import라 그 뒤에 쌓인다). **앞머리 묶음은 base 파일(단위 삭제 전)에서 정한다** -- 단위를 지운 뒤에야 머리에 붙게 된 파일 중간 import는 묶음에 넣지 않는다(독립 재검토 r1 N-1). 아래 행 번호·줄 수는 모의 생성기 출력의 **관찰**이다 -- 생성기는 단위 밖 주석을 MOD 파일로 옮기지 않고 완전 shim에서는 주석·빈 줄을 남기지 않으므로, code-author가 주석을 남기면 달라진다(판정은 계약 3의 AST 열 비교라 무관).
* SD: import 머리 바로 뒤 -- 모의 병합본 42행(앞 줄 `from topology_authoring import _import_analog_grammar, _propose_headroom_roles, _scan_case…`).
* SR: import 머리 바로 뒤 -- 모의 병합본 48행(앞 줄 `from topology_authoring import _METRIC_UNITS, _UNIT_NAME_SUFFIXES, _UNIT_SCALES, metric_un…`).

**왜 이 순서인가(design §8.1)**: ORDER(작은 번호부터). M2 병합 뒤라 `circuit_state_graph.py`의 `mod_imports`가 가리키는 트리 모듈(topology_authoring)은 이미 있는 번호 < 3 파일이다 -- 잔여 shim·split 파일 import 0(계약 7).

**착수 조건**: M1과 같음(Phase 2 DoD PASS, B34 → b26pre → backfill → B26-1 → B33 → T0·FU·G1 → D0a → D0b 병합, 면제 묶기(34)·범위 정책(35), D-27 동결 중) + **앞 card M2(`p3-move-mod2-topology-authoring`) 판정 기록**이 gate `master`에 있음. G1이 없으면 V3 대상 def 100·변이 3052(작성 전 실측 8 -- design §4 F5), T0가 없으면 계약 test 위치 가정(F6 -- 작성 전 실측 7).

**만들면 배선**: 새 def가 없다(옮긴 정의만). 새 파일 `circuit_state_graph.py`의 소비자는 split 파일의 재수출 줄(그리고 그것을 거쳐 옮긴 이름을 읽는 추적 파일 -- 작성 전 실측 9)과 뒤 MOD의 `mod_imports`다. 판정 도구 `move_plan check`는 이 card의 `equivalence.commands`에 들어간다(design §2.4 (ii)).

## 관찰 가능한 계약

1. **범위(diff, auditor)**: 이 card `Change-Id` 커밋들의 diff = `A/circuit_state_graph.py`(추가) + `A/stick_diagram.py`(수정) + `A/sizing_recipe.py`(수정) 3파일뿐이다. `git diff --name-only <base> <code_commit> -- tools` 빈 출력(D-16), test·문서·레지스트리·library·`A/` 밖 0. test 커밋 0.
2. **MOVE-AST -- `move_plan check` 발견 0(auditor)**: M1 계약 2와 같은 명령(`MPC` = `tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` 사본), `--card circuit_state_graph.py` → exit 0, 11종(`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`import-dup`·`stmt-order`·`order`·`shim`·`cache`) 모두 빈 목록.
   일관성 점검(증거로 세지 않음): `assigned` 수 = `moved_units` 수, `moved_units` 목적지 모두 `A/circuit_state_graph.py`, `moved_defs` 키 집합 = 계약 4 V3 JSON `moved`의 `to` 집합.
3. **바이트 이동(auditor, 독립 측정)**: (a) `circuit_state_graph.py` 최상위 문장 = `mod_imports["circuit_state_graph.py"]` 줄을 차례로 파싱한 import 문장들 + 옮긴 단위들(출처 파일 순서 TL→SD→SR→DR→ACF, 파일 안은 원본 순서 -- `m_cards_plan` §3-2, 모의 생성기와 같은 순서; 이 순서도 열 비교 대상이다). 옮긴 단위마다 `ast.dump(node)`(docstring 포함, `include_attributes=False`)가 base의 같은 단위와 같다. 모듈 docstring·그 밖의 새 문장 0(M1-1 기본안).
   (b) 병합본 split 파일 최상위 문장 열(`ast.dump` 열 비교): SD = base 열 − 옮긴 단위 + 재수출 하나를 앞머리 묶음의 마지막 import 뒤에; SR = base 열 − 옮긴 단위 + 재수출 하나를 앞머리 묶음의 마지막 import 뒤에. 앞머리 묶음은 base 파일(단위 삭제 전)에서 정한다 -- 단위를 지운 뒤에야 머리에 붙게 된 파일 중간 import는 묶음에 넣지 않는다. 재수출 이름 집합 = 그 파일에서 옮긴 단위가 바인딩하는 이름 전부(`_` 접두 포함, `as` 없음; 이름 순서 = card base `plan` `reexports["<그 split 파일>"]`의 이 MOD 줄 그대로 -- D0a 계약 2 결정성 문단의 코드 포인트 순, 예: 첫 글자 기준 대문자 → `_` 접두 → 소문자). (c) `from __future__ import annotations`가 `circuit_state_graph.py`의 첫 문장이다.
4. **게이트(auditor, 판정 때 gate `master` 판 도구 -- G1·면제 묶기·범위 정책 병합본)**: V3 exit 0, JSON `defs` = `[]`, `mutants` = 0, `survivors` = `[]`, `move_rejected` = `{}`, `not_targeted` = 0, `targets_by_def` = `{}`; `moved`는 비지 않는다. V6 exit 0, `findings` `[]`, `move_rejected` `{}`. V7 exit 0, `new_defs` `[]`, `move_rejected` `{}`. V5 `diff_paths` `[]`.
   V4는 FU·M1 선례대로 card가 옮기는 대표 심볼을 subject로 준다(`--subject circuit_state_graph:Transistor` `--subject circuit_state_graph:find_matching_candidates` → `PASS`, `files` `[]`). V8·V9 N/A.
5. **IMPORT-ANY(design §10 `import_any` 그대로)**: 병합본에서 `IMPORT-ANY tried=<n> expected=<n> failed=0` 한 줄, `FAIL`·`INVALID` 없음, 종료 코드 0. 기대 수 = `import_layering` `present` ∪ 트리에 있는 `--split` 파일(모의 병합본 8).
6. **동작 보존(auditor, base·병합본 같은 조건)**: (a) **PT3 전체** base·병합본 test id 집합 같고 id별 결과 같음, 실패 0(T0 병합 뒤 -- 작성 전 실측 7). (b) **E-LIB**(`e_lib.py` 사본) 출력 JSON 전체가 base와 같다. (c) **E-INST**(`e_inst_p3.py`) 파일럿·`folded_cascode`: `engine_origin`을 뺀 키 전부가 base와 같고, 병합본 `engine_origin`의 모든 경로가 `<iso>` 안이며 `circuit_state_graph`를 포함한다. stdout 사본은 `elapsed=<초>s`를 가리면 같다. base·병합본은 같은 체크아웃 경로에서 차례로 잰다.
7. **ORDER·CACHE-ID·SHIM**: 계약 2의 `order`·`cache`·`shim` 발견 0이 판정이다. 풀어 쓰면 -- `circuit_state_graph.py`의 import가 가리키는 트리 파일은 N3.10 번호 < 3 파일뿐(split 파일 import 0); 이 card 단위에 모듈 최상위 빈 dict 캐시 없음(CACHE-ID 대상 셋은 M4·M8 몫); split 파일의 새 최상위 문장은 재수출 줄뿐이고 재수출 이름마다 바인딩 출처 = `("def", A/circuit_state_graph.py, 이름)`.
8. **중간 상태 이름 해석(M1-3 기본안 -- 강화)**: (a) E3 식(§10 `E3_AST`) base·병합본 D-9 제외 집합 밖 파일 목록 같음, 두 판 모두 `stmt`·`call` 줄 0 아님. (b) E3b 식에서 `stick_diagram`을 이 card가 단위를 내보내는 split 파일 줄기(`sizing_recipe`, `stick_diagram`)로 바꾼 사본마다 `<base> <merge>`의 `E3b FAIL` 줄 집합 = `<base> <base>` 사본의 `E3b FAIL` 줄 집합(새 FAIL 0), `ERROR` 없음, `LIVE moved_out=<m>`(m > 0).
9. **레지스트리 정합(REG-DEST 유지)**: 병합본 `plan`(같은 `MPC`, `--rev <merge>`) exit 0, 판정 목록 일곱 0, (단위 키 → MOD) 사상이 base `plan`과 같다(옮긴 단위는 규칙 `A-0`).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**equivalence, test 커밋 0.** 근거는 M1 초안 '판정 유형 근거'와 같다(계획 N3.12.3 686행 'Phase 3 이동은 `equivalence`', design §8 M행 'test 커밋 0 가능 -- 05 §9.2 289행', FU spec 선례). 브랜치 `role/test/<id>`는 커밋 0으로 만들어 둔다.

**신규 시그니처가 비는 이유**: 옮긴 심볼은 새 심볼이 아니다 -- G1 `moved_defs`가 100 def 전부를 '옮긴 정의'로 인정하고(계약 4 `moved`), 같은 이름이 split 파일 재수출로 계속 import된다.

**계획 838행(V2) 'Phase 3 AST 해시 동일'을 대신하는 것**: 계약 2(`check`)와 계약 3(독립 `ast.dump` 열 비교, docstring 포함). red-green으로 하지 않는 이유는 M1 초안과 같다(위치 단언 영구 test = T0가 없앤 '정의 파일 가정'의 재도입, 위치의 영구 판정은 D0b 계약 test).

**V3 규모(작성 전 실측 8)**: G1 시제품 판 V3 대상 def 0·변이 0. G1이 없으면(gate master 판 대상 선택 식) 새 파일 `circuit_state_graph.py`와 바뀐 split 파일의 def 100개 전부가 대상, 변이 3052개.

## oracle 종류와 출처

(c) 동작 보존: PT3 test id별 결과, E-LIB·E-INST 출력 -- 기대값 = base 실행 결과(auditor가 격리 복제본에서 같은 명령으로). (a) 구성: 계약 3의 기대 모양은 계획 533·534행과 design §2.2·§3에서 손으로 정하고, 배정 집합은 card base의 `plan` 출력(D0b 레지스트리 -- 이 card가 바꾸지 않는 입력)이다.
판정 도구 `move_plan check`는 D0a `code_commit` 사본이고 code-author가 같은 card에서 바꿀 수 없다(D-16). 모의 스크립트(`_drafts/p3kit_m2_m9/`)는 작성 전 실측용 시제품이고 판정 도구가 아니다(작성자≠검증자 -- test-author·code-author·auditor에게 건네지 않는다).

## 거부해야 할 입력

auditor 판정기 자기 점검(병합본 사본에 하나씩 커밋해 판정기가 실제로 거부하는지 먼저 확인 -- 모의 실측은 작성 전 실측 10, 변형은 생성기 `neg226.py`가 card마다 같은 규칙으로 고른 것. R-6은 독립 검토 r1(`review_m2_m9.md` S-1) 뒤 `neg266.py`로 다시 고르고 잰 것 -- card base `plan` 사본의 배정 하나를 바꿔 같은 생성기로 다시 만든 병합본):
| ID | 변형(병합본 기준) | 거부해야 할 판정 |
|---|---|---|
| R-1 | 옮긴 def 하나의 몸체 정수 상수 하나 +1 (circuit_state_graph:116 in find_matching_candidates) | 계약 2 `check` `move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`shim` + 계약 4 V3 `defs` 비지 않음 + 계약 3 (a) |
| R-2 | 재수출 줄에서 이름 하나를 뺌 (stick_diagram.py drop DiodeStack) | 계약 2 `check` `shim` + 계약 3 (b) (뺀 이름을 그 파일의 남은 단위가 읽지 않아 `rebind` 0 -- `shim` (c)가 맡는다) |
| R-3 | `circuit_state_graph.py`에 `import sizing_recipe` 한 줄 | 계약 2 `check` `order` + 계약 5 IMPORT-ANY FAIL |
| R-4 | `circuit_state_graph.py` import 한 줄을 두 번 (from collections import defaultdict) | 계약 2 `check` `move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`import-dup`·`shim` + 계약 4 V3 `defs` 비지 않음 |
| R-5 | `circuit_state_graph.py`의 `from __future__ import annotations` 줄을 뺌 | 계약 2 `check` `move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`shim` + 계약 4 V3 `defs` 비지 않음 (`future` 발견 자체는 0 -- W-11: 옮긴 단위가 0이 되어 목적 파일 집합이 빈다, 거부는 `move-rejected`) |
| R-6 | 다른 MOD 배정 **순수 함수**(모듈 전역 읽기 0·데코레이터 없음 -- G1 M-4가 '옮긴 단위'로 인정하는 모양)를 함께 옮김 (sizing_recipe.py::_lerp (A-4 -> theta_search.py)) | 계약 2 `check` `move-set` 1(그 밖 발견 0) + 계약 3 (a)(b) (이 행이 배정 밖 이동 판정 `move-set`을 단독으로 깨우는 자기 점검이다 -- open items O-2) |
| R-6b | (보조 -- M-4 연쇄 모양) 모듈 전역을 읽는 다른 MOD 배정 단위를 함께 옮김 (sizing_recipe.py::_base_stack_id (A-4 -> sizing_layout_convergence.py)) | 계약 2 `check` `move-rejected`·`changed`·`lost`·`rebind`·`shim` + 계약 4 V3 `defs` 비지 않음 + 계약 3 (a) (그 단위가 MOD 파일에 없는 모듈 전역을 읽어 G1 M-4로 거부된다 -- '옮긴 단위'가 되지 못해 `move-set`이 아니라 `move-rejected`·`changed`·`lost`로 잡힌다) |
| R-7 | `circuit_state_graph.py` 머리에 모듈 docstring 한 줄 | 계약 2 `check` `changed` + 계약 3 (a) |

## library 회로 적용 여부

적용 -- E-LIB 9회로(`load_topology`·`run_topology_pipeline` 경로), E-INST 파일럿·`folded_cascode`(하네스 `run()`이 엔진 전 경로를 지난다). 회로·넷·소자 이름은 이 card의 도구·판정식에 없다(topology 무관 -- 배정은 레지스트리·N3.10·소스 구조에서만).

## 무동작 판정 입력(무발동 값)

새 산출물 필드 없음. library 회로 전부·기존 test 전부의 판정·산출물이 base와 같다(계약 6). 발동 계수 ID 없음.

## 재현할 수치

(모의 base = `c20b73d`(M1~M2 모의 병합 뒤), 모의 head = `74fd89a`, 스크래치 `C:/g226`, 2026-10-02 -- **전부 관찰**: 사슬은 '작성 전 실측' 머리. 실제 base(B34·B26-1·B33 등 병합 뒤)에서 auditor가 다시 잰다. 아래 줄 범위·줄 수·E3b 수는 **gate `2183f2e` 사슬로 갱신한 관찰**이다(아래 재측정 단락) -- 다음 병합(b26pre·backfill·B26-1·B33·T0·D0a·D0b) 뒤 또 움직이므로 판정은 계약 2·3·8의 base 대 병합본 관계로 한다.)
**(gate master 2183f2e 재측정 2026-10-06)**: B34 병합본 `2183f2e` 위 같은 대역 사슬(FU → T0 W-1 → G1 시제품 `g1_kit/install_proto.py` md5 `733d173f…` 'installed 4' → D0a 대역 → D0b 재생성 대역 = M1 base → M1·M2 이동, `MP_STMT_KEY=names`·`PYTHONHASHSEED=0`) -- 원자료 `_drafts/m_cards_at_2183.md`(스크래치 `C:/g315`), 오케스트레이터 재검증(스크래치 `C:/g329`, `chain226.py` 경로 사본, 같은 값). 같음: 단위 82(SR 43·SD 39)·규칙 A-4 48·A-1 15·A-5 10·A-2 7·A-6 2·def 100·`mod_imports` 8줄·재수출 줄 문자열(SD 42행·SR 48행)·`check` PASS 0·`moved_units` 82·`moved_defs` 100·G1 판 V3 대상 def 0·변이 0·G1 없는 def 100·변이 3052·IMPORT-ANY `tried=8`·`import_layering` 0·E3b SR 사본 `moved_out=43 base_files_reading_moved_out=22`·FAIL 9 = base 자기 대조 9·계약 3 일치·병합본 `plan` 일곱 0·W-1 shim 읽기 hits/files 131/54.
**B34 때문에 바뀐 값**: SD 단위 37개 줄 범위 −1~−3행(`find_stacked_matching_candidates` 1047~1092 → 1046~1091 … `load_topology` 8124~8313 → 8121~8310; `Transistor` 48~79·`find_matching_candidates` 938~1014 같음), SR 단위 9개(`_SPEC_RESOLUTION_KEYS` 이후, 원본 SR 6507행 B34 변경 뒤) −1행(`_SPEC_RESOLUTION_KEYS` 6841~6843 → 6840~6842 … `_theta_feed_footprint` 8875~8911 → 8874~8910), M3 base SD 8606줄·병합본 SD 5178 → 5176줄, MOD 파일 `circuit_state_graph.py` 4802 → 4801줄, **E3b SD 사본 `base_files_reading_moved_out` 26 → 27**(새 test `tests/contracts/test_b34_grammar_explicit.py`가 옮긴 이름을 SD에서 읽음; FAIL 0 = base 자기 대조 0·새 FAIL 0 그대로).
* 배정 MOD3 82단위(SD 39·SR 43), 규칙 A-4 48·A-1 15·A-5 10·A-2 7·A-6 2, 단위 안 def 100. 줄은 card base(모의) 파일 기준:
  * SD: `Transistor`(48~79, A-2)·`find_matching_candidates`(938~1014, A-4)·`find_stacked_matching_candidates`(1046~1091, A-4)·`trace_vdd_to_gnd_branches`(1125~1174, A-1)·`trace_gnd_to_vdd_branches`(1177~1222, A-1)·`find_differential_and_mirror_forks`(1225~1298, A-4)·`suggest_vertical_stack_composites`(1301~1439, A-4)·`find_differential_pair_candidates`(1442~1545, A-4)·`_diff_pair_layer1_groups`(1548~1560, A-4)·`find_verified_differential_and_mirror_relations`(1563~1746, A-4)·`_propose_vertical_stack_ids`(1749~1985, A-4)·`_propose_gm_id_roles`(1988~2048, A-4)·`_propose_L_roles`(2051~2131, A-4)·`refine_differential_and_mirror_relations`(2136~2355, A-4)·`SymmetryDispositionsVerdict`(2358~2362, A-2)·`check_symmetry_dispositions`(2365~2449, A-4)·`find_hub_merge_candidates`(2460~2483, A-1)·`StructuralSymmetryVerdict`(2494~2500, A-2)·`find_structural_symmetry_candidates`(2505~2615, A-4)·`propagate_topology_forced_currents`(2674~2725, A-1)·`DiodeStackMember`(2728~2732, A-2)·`DiodeStack`(2736~2739, A-2)·`find_diode_stacks`(2742~2770, A-4)·`_RAIL_NETS`(2802~2802, A-5)·`kcl_series_union`(2822~2867, A-4)·`_kcl_and_matching_edges`(2941~2962, A-1)·`audit_vertical_stack_id_vs_kcl`(2965~3065, A-4)·`propose_vertical_stack_id_gap_fill`(3068~3145, A-4)·`_kcl_terminal_sign`(3158~3167, A-4)·`propose_theta_kcl_gap_fill`(3170~3515, A-4)·`propose_device_roles_gap_fill`(3520~4225, A-4)·`find_unreviewed_device_roles`(4232~4267, A-4)·`find_unreviewed_matching_pairs`(4270~4300, A-4)·`require_device_roles_reviewed`(4303~4358, A-4)·`folded_cascode_example`(6292~6331, A-6)·`two_stage_ota_example`(6334~6364, A-6)·`NameCollisionVerdict`(8059~8064, A-2)·`check_topology_name_uniqueness`(8068~8112, A-5)·`load_topology`(8121~8310, A-1)
  * SR: `vgs_alias_map`(1043~1062, A-1)·`_vgs_root`(1065~1071, A-4)·`true_current_mirror_groups`(1597~1621, A-1)·`l_sharing_classes`(1624~1670, A-1)·`gain_stage_tails`(1673~1726, A-4)·`l_class_owners`(1729~1754, A-1)·`audit_l_sharing_consistency`(1757~1794, A-4)·`synthesize_l_class_thetas`(1857~1933, A-4)·`_AUTHORITATIVE_GM_ID_SOURCES`(2514~2515, A-5)·`_AUTHORITATIVE_GM_ID_ONLY_SOURCES`(2516~2516, A-5)·`_gm_id_already_authoritative`(2519~2522, A-4)·`is_diode_connected`(2525~2532, A-1)·`_DEFAULT_RAIL_HI`(3120~3120, A-5)·`_DEFAULT_RAIL_LO`(3121~3121, A-5)·`NodeVoltageReport`(3124~3130, A-2)·`propagate_node_voltages`(3133~3192, A-4)·`derive_vsb_from_nodes`(3195~3211, A-4)·`reconcile_vsb_from_nodes`(3214~3253, A-4)·`audit_vsb_consistency`(3256~3283, A-4)·`signal_path_nodes`(3286~3320, A-1)·`node_pole_estimate`(3323~3396, A-4)·`input_referred_offset_pairs`(3887~3935, A-4)·`materialize_input_offset_pairs`(3939~3965, A-4)·`_load_full_topology_cached`(4190~4221, A-4)·`_topology_meta_cached`(4224~4231, A-4)·`_l_sharing_classes_cached`(4234~4243, A-4)·`_l_class_owners_cached`(4246~4254, A-4)·`_ideal_sources_cached`(4257~4260, A-4)·`_diode_set_cached`(4263~4274, A-4)·`_device_roles_cached`(4277~4280, A-4)·`_matching_pairs_cached`(4283~4286, A-4)·`_shared_current_groups_from_compensation`(4855~4866, A-4)·`_build_shared_current_joint_plan`(4886~4941, A-4)·`validate_theta_declaration_order`(5546~5638, A-1)·`_SPEC_RESOLUTION_KEYS`(6840~6842, A-5)·`spec_fingerprint`(6845~6863, A-1)·`require_declared_spec_source`(6866~6932, A-1)·`_RESOLVE_STALE_NOTES`(7067~7067, A-5)·`resolve_constraint_references`(7070~7177, A-4)·`_FULL_CIRCUIT_METRIC_TYPES`(8794~8794, A-5)·`_DEFAULT_ALL_DEVICES_METRIC_TYPES`(8800~8818, A-5)·`_metric_device_footprint`(8821~8871, A-4)·`_theta_feed_footprint`(8874~8910, A-4)
* `mod_imports["circuit_state_graph.py"]`(머리 8줄): `from __future__ import annotations` / `from collections import defaultdict` / `from dataclasses import dataclass` / `from topology_authoring import _import_analog_grammar, _propose_headroom_roles, _scan_case_collisions, _to_analog_grammar_devs, find_authoritative_sizing_devices, find_idiom_matches` / `from typing import Sequence` / `import itertools` / `import json` / `import os`.
* SD 재수출(머리): `from circuit_state_graph import DiodeStack, DiodeStackMember, NameCollisionVerdict, StructuralSymmetryVerdict, SymmetryDispositionsVerdict, Transistor, _RAIL_NETS, _diff_pair_layer1_groups, _kcl_and_matching_edges, _kcl_terminal_sign, _propose_L_roles, _propose_gm_id_roles, _propose_vertical_stack_ids, audit_vertical_stack_id_vs_kcl, check_symmetry_dispositions, check_topology_name_uniqueness, find_differential_and_mirror_forks, find_differential_pair_candidates, find_diode_stacks, find_hub_merge_candidates, find_matching_candidates, find_stacked_matching_candidates, find_structural_symmetry_candidates, find_unreviewed_device_roles, find_unreviewed_matching_pairs, find_verified_differential_and_mirror_relations, folded_cascode_example, kcl_series_union, load_topology, propagate_topology_forced_currents, propose_device_roles_gap_fill, propose_theta_kcl_gap_fill, propose_vertical_stack_id_gap_fill, refine_differential_and_mirror_relations, require_device_roles_reviewed, suggest_vertical_stack_composites, trace_gnd_to_vdd_branches, trace_vdd_to_gnd_branches, two_stage_ota_example`.
* SR 재수출(머리): `from circuit_state_graph import NodeVoltageReport, _AUTHORITATIVE_GM_ID_ONLY_SOURCES, _AUTHORITATIVE_GM_ID_SOURCES, _DEFAULT_ALL_DEVICES_METRIC_TYPES, _DEFAULT_RAIL_HI, _DEFAULT_RAIL_LO, _FULL_CIRCUIT_METRIC_TYPES, _RESOLVE_STALE_NOTES, _SPEC_RESOLUTION_KEYS, _build_shared_current_joint_plan, _device_roles_cached, _diode_set_cached, _gm_id_already_authoritative, _ideal_sources_cached, _l_class_owners_cached, _l_sharing_classes_cached, _load_full_topology_cached, _matching_pairs_cached, _metric_device_footprint, _shared_current_groups_from_compensation, _theta_feed_footprint, _topology_meta_cached, _vgs_root, audit_l_sharing_consistency, audit_vsb_consistency, derive_vsb_from_nodes, gain_stage_tails, input_referred_offset_pairs, is_diode_connected, l_class_owners, l_sharing_classes, materialize_input_offset_pairs, node_pole_estimate, propagate_node_voltages, reconcile_vsb_from_nodes, require_declared_spec_source, resolve_constraint_references, signal_path_nodes, spec_fingerprint, synthesize_l_class_thetas, true_current_mirror_groups, validate_theta_declaration_order, vgs_alias_map`.
* `check` exit 0, 발견 11종 모두 0, `assigned` 82·`moved_units` 82·`moved_defs` 100 (`check` 85 s).
* V3(G1 시제품, 실행) PASS `defs` []·`mutants` 0·`move_rejected` {}·`moved` 100; V6 PASS `findings` []; V7 PASS `new_defs` []. G1 없는 대상 선택 식: def 100·변이 3052.
* V4 `--subject circuit_state_graph:Transistor` `--subject circuit_state_graph:find_matching_candidates` → exit 0 `{"tool": "V4", "verdict": "PASS", "files": [], "findings": [], "unjudged": []}`; V5 exit 0 `{"tool": "V5", "verdict": "PASS", "findings": [], "diff_paths": [], "diff_hash": null, "approved": false}`.
* IMPORT-ANY 병합본 `IMPORT-ANY tried=8 expected=8 failed=0`. `import_layering` 발견 0.
* PT3 base `1 failed, 1046 passed, 15 xfailed in 284.93s (0:04:44)` / 병합본 `1 failed, 1046 passed, 15 xfailed in 336.32s (0:05:36)`, test id 1062 = 1062, id별 결과 차이 0.
  병합본 실패는 전부 T0 몫 A군(모의에 T0의 R-DEF 수정이 없음 -- design §7.1, m_cards_plan W-8): `contracts/test_ic5.py::test_gate_docstring_declares_blind_spots`.
* E-LIB `hash` `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f`(base = 병합본 JSON 전체 같음: True). E-INST(`e_inst_p3.py` `7d26134a…`): 파일럿 키 22 중 다른 키 ["engine_origin"], `raw_sha256` `2fc426d9ef3a9623898d54a3ee712c64913460770f3361c830938c11a1eb863d`, `without_topology_ref_sha256` `185b675e9dd363a535d2942c651cddee4cb1a0ee98b703f0c7abef99f50e51ca`; `folded_cascode` 다른 키 ["engine_origin"], `raw_sha256` `ef3cd9963d0a80ac6e07ea5909286db1d8e67d8351a355c8aafd7a01fc9bb3f0`; 병합본 `engine_origin`에 `circuit_state_graph` 포함 True·전부 `<iso>` 안 True.
* E3 식 base `stmt` 70·`call` 9 / 병합본 `stmt` 70·`call` 9, 병합본 제외 밖 66파일(base 목록과 같음: 예).
* E3b 식(sizing_recipe 사본) `E3b LIVE moved_out=43 base_files_reading_moved_out=22 pre_existing=1`, FAIL 9줄 = base 자기 대조 9줄, 새 FAIL 0.
* E3b 식(stick_diagram 사본) `E3b LIVE moved_out=39 base_files_reading_moved_out=27 pre_existing=1`(gate `2183f2e` 사슬; `4a286f0` 사슬 26), FAIL 0줄 = base 자기 대조 0줄, 새 FAIL 0.
* `plan`(병합본) 일곱 목록 {"upward": 0, "cycles": 0, "unassigned": 0, "conflicts": 0, "reg_mismatch": 0, "import_time_high": 0, "import_conflicts": 0}, 사상 차이 0, 옮긴 단위 규칙 {"A-0": 82}.

## 결정 필요 항목

모두 **기본안이 있다**(원칙 유도 -- 사용자 질문 아님). 사용자 몫일 수 있는 것은 `_drafts/m2_m9_open_items.md`에 모았다(이 card 관련 행: O-1·O-2·O-7).
* **M1-1·M1-3 그대로**: MOD 파일 모듈 docstring 없음(M1-1 (가) -- 모의 R-7이 `changed` 1로 거부되는 것을 이 card에서도 확인), E3·E3b 식 card 단위 사용(M1-3, 강화).
* **M1-2 닫힘**: 사용자 결정 D-11 (가)(2026-10-02 "(가) 계획 표 MOD1에 추가 (Recommended)")로 `_QUERY_CACHE_MAX`는 MOD1. 이 card 수치는 그 개정과 계약 문언 키(바인딩 이름)를 적용한 판이다 -- 조건('D0b가 다른 개정을 더 계산하면 다시 묻는다')대로 이 모의에서는 그 밖의 `upward`·`conflicts`가 0이었다.
* **B26-1 계수 test(T0 계약 10)**: `load_topology`가 이 card에서 MOD3로 간다(모의 SD 8124~8313, gate `2183f2e` 사슬 8121~8310, A-1). B26-1 병합 뒤 `test_b26_rail_accessor.py`(design §7.1 v5 A군)는 래퍼 대상이 R-DEF 정의 파일 + import 바인딩 엔진 파일 전부여야 통과한다 -- T0 계약 10 몫이고 T0 병합이 착수 조건이다. 모의에는 B26-1이 없어 측정하지 못했다(실제 base에서 auditor가 PT3로 잰다). D-19 (가)면 `load_topology`(MOD3)가 `rail_declaration`(MOD2)을 import하는 줄이 `mod_imports`에 생길 것으로 본다(작은 번호 쪽 -- ORDER 허용).
* **규모(W-12)**: 82단위·100 def -- 바이트 이동이라 card를 나누지 않는다(모듈 하나 = card 하나, N3.12.3 674행).
* **id 날짜**: 초안 id `20261002-p3-move-mod3-circuit-state-graph`(slug는 design §8 `p3-move-mod<n>-<이름>`). card 커밋 날짜에 맞춰 바꾼다.

## 작성 전 실측

(재측정 = gate `master` **`4a286f0`**(`git -C <repo> rev-parse gate/master master HEAD` 셋 다 `4a286f0f…`), 2026-10-02. 실제 저장소 쓰기 없음 -- 격리 복제본 `C:/g226/r`(`git clone --no-local`, origin 제거, 빈 hooksPath, TMP/TEMP `C:/g226/tmp`), 작업 끝에 `C:/g226` 삭제, 저장소 `status --porcelain`(37줄)·reflog 시작과 같음.
B34·b26pre·backfill·B26-1·B33·범위 정책(35)·T0·FU·G1·D0a·D0b는 **모두 미병합**이라 복제본 사슬로 대역했다: `4a286f0` → `9659236` FU 대역(DR 28행·ACF 38행 앞 `from __future__ import annotations`, `fu_standin.py`) → `9a24b34` T0 W-1 대역(unit selftest 3파일 24행의 비엔진 7이름을 출처 import로, `t0w1_standin.py` -- W-1 (가)의 T0 몫만) → `b6c35d5` G1 시제품(`g1_kit/install_proto.py`·`g1_core.py`, gate master 판 `mutate_changed.py`·`rt.py`에 그대로 설치) → `744d0fe` D-11 (가) 대역(N3.10 MOD1 '대표 대상'에 `_QUERY_CACHE_MAX` 토큰, `p3fq_kit/variant.py qtok` -- p3_followup §1.4 새 문안과 같은 바이트) → `1c19dd4` D0a 대역(`p3kit_m1/move_plan_sim.py`를 `tools/migrate/move_plan.py`로, **문장 키 = 바인딩 이름(D0a 계약 2 문언, `MP_STMT_KEY=names`)**) → `1a18416` D0b 재생성 대역(`regen_registry.py --write` one 354·nested 7·nounit 18, `보류(Phase 3)` → `보류(Phase 4)`) = **M1 base 대역** → M1~M9 이동 생성기 `gen226.py`(M1 키트 `gen_move.py` + 모듈 docstring 없음(M1-1) + W-2 머리 계산) 사슬 `chain226.py`. 원자료·스크립트 `_drafts/p3kit_m2_m9/`.
M1 수치 재현(사슬 첫 card, M1 초안 '재현할 수치'와 대조): MOD1 8단위·`check` 발견 0·`moved_defs` 22·G1 없는 def 22·변이 590·IMPORT-ANY `tried=6`·PT3 1047 passed·15 xfailed(T0 W-1 대역 포함 판) -- 같은 값. 키 방식을 계약 문언(바인딩 이름)으로 바꾸고 D-11 (가) 토큰을 더한 판이라 M1 초안의 `<stmt:해시>` 판과 MOD4·MOD8·MOD9·SD 수가 다르다(MOD4 104·MOD8 30·MOD9 16·SD 111 -- `p3_followup_questions.md` §1.1 names+① 행과 같음).

1. **사실 문장 재측정**: `git show 4a286f0:<plan>` 523행 MOD3 행 원문(위 '의도'). M1 base 대역 `plan`(재생성 전) exit 1 = `reg_mismatch` 80만(나머지 여섯 0, 배정 403 -- A-4 235·A-1 61·A-5 57·A-2 38·A-6 7·A-7 2·A-K 2·A-3 1), 재생성 뒤 exit 0·일곱 0·사상 차이 0.
2. **단위 집합(관찰)**: 이 card 모의 base `plan` exit 0, 일곱 목록 {"upward": 0, "cycles": 0, "unassigned": 0, "conflicts": 0, "reg_mismatch": 0, "import_time_high": 0, "import_conflicts": 0}, MOD3 82단위(SR 43, SD 39). 배정은 앞 card들이 옮긴 단위를 `A-0`으로 같은 MOD에 두므로 사슬 어디서나 같다(card마다 사상 차이 0 -- 계약 9).
3. **`mod_imports`·PLAN-LAYER**: `mod_imports["circuit_state_graph.py"]` 8줄(재현할 수치), `import_conflicts` 0, `upward` 0, `import_time_high` 0.
4. **쓰기 경로(계획 N3.12.2)**: `A/circuit_state_graph.py`·`A/stick_diagram.py`·`A/sizing_recipe.py` = gmid-code-author(엔진 소스). test-author 산출물 없음. 판정 기록·계약 측정 = auditor. `tools/**`는 누구도 바꾸지 않는다(D-16).
5. **계획서 소비자·이름 충돌**: 이 card는 이름을 지우거나 바꾸지 않는다(위치만, 재수출로 같은 import 경로 유지). 새 파일 이름 `circuit_state_graph.py`는 `4a286f0`에 없다(`git ls-tree` 빈 출력).
6. **미배선**: 새 def 0. V7 `new_defs` [](G1 시제품) -- 면제 불필요.
7. **기존 계약 test**: 모의 사슬에는 T0의 R-DEF 수정이 없다(W-1 import 3줄만 대역). 이 card 병합본 PT3 실패 = `contracts/test_ic5.py::test_gate_docstring_declares_blind_spots` -- 전부 design §7.1 A군(T0 몫, m_cards_plan W-8); base(앞 card 병합본) 실패 = `contracts/test_ic5.py::test_gate_docstring_declares_blind_spots`.
   T0 계약 10(`test_b26_rail_accessor.py`)은 B26-1 병합 뒤에만 있다 -- 모의 밖(결정 필요 항목).
8. **V3 규모**: G1 시제품 `mutate_changed.py --root C:/g226/r --base c20b73d --head 74fd89a … --gmid-phase=3 --gmid-strict=` → 계약 4 값(재현할 수치). G1 없는 판(gate master `changed_defs`·`mutants` 정적 계수): def 100·변이 3052. 범위 정책(35) 시제품은 키트에 없다 -- 대상 def 0이라 `not_targeted`·`targets_by_def`는 0·`{}`일 것으로 본다(판정 때 실측).
9. **읽는 쪽 범위**: E3b 식 사본 sizing_recipe `moved_out=43 base_files_reading_moved_out=22 pre_existing=1`; stick_diagram `moved_out=39 base_files_reading_moved_out=26 pre_existing=1`(gate `2183f2e` 사슬 27) -- 전부 재수출로 계속 해석된다(새 FAIL 0). E3 식 importer 병합본 66파일(base와 같음). W-1 점검(`p3fq_kit/shim_import_reads.py`를 병합본에 돌려 N3.10 모듈 재수출이 아닌 import 바인딩 이름을 TL·SR·DR 경유로 읽는 곳): 0곳 -- T0 W-1 대역이 3줄을 고친 상태라 0.
10. **거부 입력 실측**(병합본 사본에 하나씩 커밋, 모의 `check` + G1 시제품 정적 V3 + IMPORT-ANY(+ ACF 밖 cwd 로드)): 원자료 `p3kit_m2_m9/out/neg.jsonl`.
    * R-1 `circuit_state_graph:116 in find_matching_candidates`: `check` exit 1 `move-set` 14·`move-rejected` 13·`changed` 14·`lost` 14·`rebind` 30·`shim` 2; G1 정적 V3 대상 def 17·변이 582·거부 13; IMPORT-ANY 통과.
    * R-2 `stick_diagram.py drop DiodeStack`: `check` exit 1 `shim` 1; G1 정적 V3 대상 def 0·변이 0·거부 0; IMPORT-ANY 통과.
    * R-3 `import sizing_recipe`: `check` exit 1 `order` 1; G1 정적 V3 대상 def 0·변이 0·거부 0; IMPORT-ANY FAIL(audit_current_forced, circuit_state_graph, design_report, stick_diagram).
    * R-4 `from collections import defaultdict`: `check` exit 1 `move-set` 35·`move-rejected` 35·`changed` 35·`lost` 35·`rebind` 37·`import-dup` 1·`shim` 2; G1 정적 V3 대상 def 64·변이 2063·거부 35; IMPORT-ANY 통과.
    * R-5 `-future`: `check` exit 1 `move-set` 82·`move-rejected` 82·`changed` 82·`lost` 82·`rebind` 77·`shim` 2; G1 정적 V3 대상 def 100·변이 3052·거부 82; IMPORT-ANY 통과.
    * R-6 `sizing_recipe.py::_lerp (A-4 -> theta_search.py)` (r1m 재측정, 스크래치 `C:/g266`, `neg266.py COMOVE=_lerp`): `check` exit 1 `move-set` 1(그 밖 발견 0); 계약 3 판정기(`c3.py`) (a) 불일치·(b) sizing_recipe.py 불일치(stick_diagram.py 일치); IMPORT-ANY 통과(`IMPORT-ANY tried=8 expected=8 failed=0`).
    * R-6b(초안 판 측정, `C:/g226`) `sizing_recipe.py::_base_stack_id (A-4 -> sizing_layout_convergence.py)`: `check` exit 1 `move-rejected` 1·`changed` 1·`lost` 1·`rebind` 1·`shim` 1; G1 정적 V3 대상 def 1·변이 2·거부 1; IMPORT-ANY 통과.
    * R-7 `docstring`: `check` exit 1 `changed` 1; G1 정적 V3 대상 def 0·변이 0·거부 0; IMPORT-ANY 통과.
11. **test 이름·모양**: 새 test 없음.
12. **같음 판정**: 계약 3은 `ast.dump` 문자열 열 비교(순서 포함), 계약 6 (a)는 test id별 결과 문자열, (b)는 JSON 전체, (c)는 `engine_origin`을 뺀 키별 값 비교 + 경로 포함 조건. `set`을 `==`로 비교하는 계약 없음.
13. **red 모양**: red 없음(equivalence). 거부 확인은 auditor 측정.
14. **양식**: gate `4a286f0` `tools/gates`(`git archive`)의 `role_paths.parse_spec_card(text, expect_id="20261002-p3-move-mod3-circuit-state-graph")` → 예외 없음, 머리 `phase` 3·`evidence_type` equivalence·`gate_change` no·`approval` 1, 본문 절 11개(양식 순서 그대로). `interface_card.py <이 spec> --root <모의 base 트리>` → exit 0, 기존 함수 표 행 0 .
15. **앞 card 의존 재확인(오케스트레이터, card 커밋 직전)**: (i) gate `master`에 M2 판정 기록 (ii) 그 판정 기록의 `code_commit`(= 이 card base)에서 `plan` 출력의 `circuit_state_graph.py` 배정 단위 목록·`mod_imports["circuit_state_graph.py"]` -- '재현할 수치'를 그 값으로 바꾼다 (iii) `git diff --stat <D0b 병합> gate/master -- tools docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 빈 출력·엔진 diff는 M1~M2 card 커밋뿐(D-27 동결).
16. **비용(모의)**: card 한 건 사슬(plan + 생성 + check + G1 정적 V3 + IMPORT-ANY + E3b + W-1 점검) 616 s, `check` 85 s, PT3 약 5~6분, E-INST 파일럿 약 6~8분(다른 측정과 겹친 시간).

