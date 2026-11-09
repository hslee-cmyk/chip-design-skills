# 독립 검토 -- Phase 4 첫 card `20261002-d4-delete-unwired` (#2)

검토 대상: `_drafts/draft_p4_first.spec.md`, `_drafts/p4_first_card_notes.md`. 대조: Phase 4 design 초안 v0.9.9(`draft_phase4_design.md` §5.1 #2 행, §7.4, P-38/§10.1-0), 템플릿 `docs/02-design/specs/_TEMPLATE.spec.md`.
검토자는 작성자가 아니다. 저장소 쓰기 0 -- 격리 복제본 `C:/g214`(작업 저장소 clone 뒤 `36e170e` checkout, origin 제거). 끝난 뒤 `C:/g214` 삭제, 저장소 `git status` 변화 없음.
측정 판 = gate `master` = `36e170eec5b9…`(작업 저장소 `master`와 같음). python `C:\Python314\python.exe -B`. gate 도구는 같은 커밋의 `tools/gates/`.

## 판정

**조건부 통과(수정 후 커밋)** -- B 1, S 3, minor 7.
삭제 대상 6개가 운영 경로 0이라는 사실, 레지스트리·reg_check 효과, V3 0, E-LIB 동일, 전체 suite 결과, V5 발견 집합이 선언 범위와 정확히 같다는 것은 재측정으로 확인했다.
막는 것은 계약 8(TS6 도구 test 허용 차이)이 **test-first 순서로 실행할 수 없게 적혀 있다**는 점 하나다.

## 재측정 결과 (모의 card: `C:/g214/sim`, base `36e170e` → T `ff1bd1c`(test) → K `e60ce18`(code·도구·레지스트리), 측정 전용)

| 항목 | 결과 | card 주장과 |
|---|---|---|
| 정의 위치(36e170e) | SR `solve_diode_stack_current` 1499, `estimate_area_budget` 2765, `derived_bounds_path` 7700, `load_derived_bounds` 7712; SD `MultiLeafHubParityVerdict` 2800, `check_multi_leaf_hub_parity` 2806 | 같음 |
| G-1 / 운영 도달(V7 그래프 `reachability.build_graph`+`reach`, gate_config 루트 4개) | 6개 전부 **unreached**. 선행 노드: `derived_bounds_path` ← `load_derived_bounds`·`tests/tools/derive_achievable_bounds.py::<module>`; `load_derived_bounds` ← 도구 `<module>`; `estimate_area_budget` ← `test_s028`; `solve_diode_stack_current` ← `test_s007`; `check_multi_leaf_hub_parity` ← `test_ic5.py::<module>`(표 키 문자열 간선)·`test_s058_section` | 같음 |
| 문자열 등록 | `A/`·`workspaces/`에서 따옴표 붙은 이름 = `test_ic5.py:58` 표 키 1건뿐. 엔진 등록 딕셔너리 값 0. 라이브러리 `value_from_achievable` 0, 추적 `*.derived.json` 0 | 같음 |
| 엔진의 유도값 읽기 | `resolve_constraint_references`가 제약의 `_derived.spec_fingerprint`만 읽음(SR 7860~7874). 사이드카를 읽는 엔진 코드 0 | 같음 |
| docstring·주석 언급(계약 4) | SR 627·1475·7757·9140, SD 2657·2659·2851·6063·6213·7004 (+삭제될 def 안 2830) | 같음 |
| reg_check | base 발견 0 / 코드만 지움 → `stale` 5(SR 3·SD 2) / 계약 9대로 레지스트리 수정 → 발견 0 | 같음. §3 R0 행(`derived_bounds_path`)은 reg_check 규칙 밖(손 정리) |
| V7 | PASS, `new_defs` 0 | 같음 |
| **V3**(`mutate_changed.py`, 36e170e 판) | **PASS, targets SR·SD, mutants 0**(docstring 수정 포함 -- `def_hash`가 docstring 제외) | 같음 |
| E-LIB(`20260930-df36` 판 `e_lib.py`) | base·모의 병합본 해시 같음 `1d2e3bf6…`, 9/9 회로 load·V1·V2 정상 | 같음(E-INST는 재지 않음 -- 삭제 def가 루트에서 도달 불가라 근거는 V7 그래프) |
| 전체 suite(`pytest_gate.ini`, `--gmid-phase=2`, 각 트리 rootdir) | base **1047 passed, 15 xfailed** / T만(red) **2 failed(GONE ast·text, AssertionError), 1047 passed, 15 xfailed** / 병합본 **1049 passed, 15 xfailed, 실패 0** | 모의 병합본 수 = 1047 − 2(s007·s028) + 3(GONE 3개) + 1(손 규칙 거부 test) -- 계약 14의 '수집 id = base − 2 + 새 test'와 맞음 |
| **V5**(`weakening_diff.py`) | FAIL(승인 없음, 예상대로). 발견 7건 = `test_ic5` `test_domain_table_uses_allowed_values`(21→19)·`<module>`(두 표 행 + 모듈 docstring '21행'), `test_ts6_probe_relocate` `test_moved_tool_matches_base_except_path_lines`(비교 완화), `test_s007`·`test_s028`(함수 삭제), `test_s058_section`(비교 완화 + 리터럴 변경) | **선언 범위(계약 6·7·8)와 정확히 같음** -- 범위 밖 발견 0. GONE test·손 규칙 helper(추가)는 발견 아님 |

## B (막는 것)

**B1. 계약 8의 허용 목록을 test-first로 쓸 수 없다 -- 문자열 목록이 card에 없고, 실제 차이는 '4건'이 아니라 약 15줄이다.**
* 근거(측정): `non_path_line_changes(base 939f926 blob, 계약 5 전체 적용본)` = **15건**: base 쪽 2·10·11(docstring '사이드카'·'파일에 남기고'·'파일에는'), 50(`emit(... (사이드카 갱신))`), 69·70(`load_derived_bounds`, `book.setdefault`), 112~115(경로·`with open`·`json.dump`·`emit(사이드카 저장)`) + new 쪽 2·10·11·50·69. card '작성 전 실측' 7(b)의 '4건'은 두 줄만 바꾼 모의(simA)의 수다 -- 계약 5가 요구하는 쓰기 블록 삭제·docstring·출력 문구 수정을 넣으면 늘어난다.
* test 커밋 T가 K보다 먼저이고 test-author는 도구 소스를 보지 않는다. 계약 8은 "card 계약 5의 문장 목록을 interface card에 문자열로 고정"이라 하지만 계약 5에는 **지울 base 줄도, 새로 쓸 줄의 문자열도** 없다. code-author가 고르는 새 docstring·`emit` 문구·`book` 초기화 줄이 test의 목록과 한 글자라도 다르면 병합본 FAIL → 재시도(메모리 'card 처리 속도' -- 재시도 원인 1순위가 spec card 결함).
* 약화 범위 질문에 대한 답: 허용을 **(쪽, 줄 내용) 정확 쌍의 고정 집합**으로 두면 '경로 줄 + 이 card의 사이드카 문장'을 넘지 않는다(모의에서 그 모양으로 구현 -- V5 발견은 그 test의 '비교 완화' 1건뿐, 그 밖 줄은 계속 동일 판정). 넘게 되는 것은 문구가 모호해 test-author가 '`사이드카`를 담은 줄 전부'나 'base 쪽 삭제 + new 쪽 아무 줄' 같은 규칙으로 구현할 때다 -- card가 막아야 한다.
* 고칠 것(택1):
  (가') 계약 5에 **base 쪽 지울 줄 원문 목록**과 **new 쪽 새 줄 원문 전부**(docstring 2·10·11행 대체문, 50행 출력 문구, `book = {fp: {}}` 한 줄, `book.setdefault` 줄 삭제 여부)를 적고, 계약 8은 "허용 = 경로 줄 ∪ 이 두 목록의 (쪽, 원문) 쌍, 그 밖 차이 0"으로 적는다. 사용자 V5 기록 범위 설명에도 그 목록을 인용.
  (다) 대안 -- TS6 계약 5의 원래 뜻('이동이 경로 줄만 바꿨다')을 **이동 커밋 blob 대 base blob**으로 판정하게 바꾼다(불변 이력 판정 -- HEAD 도구 내용을 영구 고정하지 않음). 그러면 #2와 아래 S1(Phase 3 F1)이 둘 다 이 test를 건드리지 않는다. 이것도 V5 승인 대상이지만 허용 목록 유지 비용이 없다. 어느 쪽이 '약화'인지는 사용자 판단 -- card 결정 항목 D1에 (다)를 선택지로 추가 권고.

## S (커밋 전 고칠 것)

**S1. Phase 3 F1이 같은 TS6 test를 먼저 깨뜨린다 -- [미확인]이 아니라 확정이다(Phase 3 쪽 누락).**
* 측정: 도구 33행 `import sizing_recipe as sr`만 다른 모듈로 바꾼 본에서 `non_path_line_changes` = `[('base', 33, 'import sizing_recipe as sr'), ('new', 33, 'import theta_search as sr')]` → FAIL. F2가 `A/sizing_recipe.py`를 지우고(design 30 85행), §7.2 F1 대상에 `A/tests/tools` 2파일이 있으므로 F1은 이 줄을 반드시 바꾼다.
* design 30 §7.1 B군 표는 `test_ts6_probe_relocate.py:528`(파일 존재 앵커)만 적고 `test_moved_tool_matches_base_except_path_lines`(672행)는 없다. → Phase 3 F1 card(또는 design 30 §7.1 B군)에 이 test와 V5 처리 방법을 넣어야 한다. 오케스트레이터에 Phase 3 결함으로 보고.
* 이 card 쪽: notes §3-2·P3-5의 '[미확인]'을 '확정(측정)'으로 바꾸고, D1의 선택이 Phase 3 F1 처리와 같은 규칙이 되게 맞춘다(B1 (다)를 Phase 3에서 쓰면 #2는 이 test를 건드리지 않아도 된다).

**S2. 계약 7 (iii)이 실행 불가능하게 적혀 있다.** "(iii) k=8(가능)·k=7(불가) 실제 그래프 판정은 그대로 둔다"지만 그 블록(`test_selftest_stick_diagram.py` 1460~1470)은 `formula = check_multi_leaf_hub_parity(...)`(1466)와 `formula.ok`·`formula.kind`·`formula.m_odd_leaves`를 쓴다. card '작성 전 실측' 1도 1466을 호출로 적었다. 그대로 두면 GONE(계약 3) FAIL 또는 NameError.
고칠 것: (iii)의 기대값도 손 규칙(k=8 → m=0 → `circuit`, 가능 / k=7 → m=3 → `impossible`, 불가)에서 오고 메시지의 `m_odd_leaves` 부분도 지운다고 적는다(모의에서 그렇게 바꿨고, V5 발견은 `test_s058_section`의 비교 완화·리터럴 변경으로 이미 선언 범위 안).

**S3. card가 design 판을 v0.9.8로 적고, V8 항목이 v0.9.9에서 해소된 것을 '개정 요청'으로 남긴다.** 의도 1행 "(초안 v0.9.8, 승인 전)", 결정 필요 항목 V8 "design에 이 문장이 없다 -- design 개정 요청, notes §4". v0.9.9에 P-38·§10.1-0("#2처럼 폴백 경로를 바꾸지 않는 card는 'N/A -- 계측 미도입, 폴백 경로 불변'")이 들어갔다. → 판 번호를 v0.9.9로, V8 항목은 "P-38(§10.1-0)에 따라 N/A -- 계측 미도입, 폴백 경로 불변"으로(결정 필요 항목에서 빼고 판정 유형 근거나 무동작 절로).

## minor

1. **계약 7의 `_invert_gm_id_for_current` import는 조건문이 아니라 사실로**: 36e170e에서 `tests/unit`·`tests/contracts`의 사용은 `test_selftest_sizing_recipe.py:651`(test_s007 안) 하나뿐 → s007을 지우면 import도 뺀다고 적는다(모의에서 뺐고 suite 영향 0).
2. **test 파일의 낡은 언급 2곳이 계약 밖**: `test_selftest_sizing_recipe.py:617`(test_s006 docstring의 `solve_diode_stack_current()`), `:1221` 주석("사이드카에 저장된다(`derived_bounds_path()`)" -- 삭제 뒤 거짓). `weakening_diff`는 함수 docstring을 빼고(141행) 주석은 AST 밖이라 **V5 비용 0** -- 계약 7에 넣어 같은 test 커밋에서 고칠 것(계약 4가 엔진의 낡은 문장을 지우는 원칙과 같은 범위).
3. **참조 문서 목록 누락 1건**: 계약 10·실측 5의 `design-report-spec.md:370·454·492`에 **400행**(표 셀 안 `check_multi_leaf_hub_parity()`, 열 635 부근)이 빠졌다.
4. **계약 3의 'V3 인벤토리 간선에 걸리지 않게' 문구가 부정확**: `reachability` 그래프는 def 이름과 **같은 문자열 상수**를 간선으로 잡는다(모듈 docstring). 새 GONE test의 이름 문자열은 T-only 트리에서 삭제 대상 def로 간선이 생긴다. 병합본에는 def가 없어 무해 -- 문구를 "병합본에서 대상 def가 없으므로 간선이 생기지 않는다"로.
5. **계약 5의 동작 차이 한 줄**: 사이드카가 있을 때 한 실행에서 유도가 실패한 metric은 같은 지문의 사이드카 옛 값이 topology에 다시 쓰였고, 사이드카를 없애면 topology의 기존 값이 그대로 남는다. 라이브러리 선언 0이라 무동작이지만 사실로 적어 둘 것(동작 보존 주장 범위).
6. **D-5 표 행을 함수보다 먼저 지우는 것**(P-18)은 #2~#41 사이 `audit_vertical_stack_id_euler_feasibility`의 영역 값 판정을 끈다(형식 판정만 남음). 설계 결정(승인 경로 UD-0 + 이 V5)이므로 막지 않지만, V5 기록 범위 설명에 "남는 함수 하나의 영역 값 판정이 #41까지 꺼진다"를 원문으로 적어 사용자가 보게 할 것.
7. 표기: 계약 1의 `MultiLeafHubParityVerdict`는 `@dataclass` 데코레이터(2799)까지 지운다고 적을 것(삭제 범위 정확화).

## Phase 3 이동과의 관계(요청 항목)

* 6개 이름은 Phase 3에서 **움직인다**(SR 4개): 시제품 D0b 배정(card P3-1, 확정 아님) `estimate_area_budget` → `sizing_layout_convergence.py`, `derived_bounds_path`·`load_derived_bounds` → `theta_search.py`, `solve_diode_stack_current` → 미배정. SD 2개는 A-7 고립 단위로 `stick_diagram.py`에 남는다(design 30 445행).
* card는 위치를 **심볼로** 적고 정의 파일·IC5 표 키·import 줄·레지스트리 판·도구 모양을 F2 병합본에서 다시 정하게(P3-1~P3-9) 해 두었다 -- 적절하다. 단 F2 뒤 card 본문은 **옮긴 뒤 파일 경로**(R-DEF 결과)로 고쳐 커밋해야 한다: 계약 1('card base의 정의 파일'), 계약 4 언급 목록의 파일, 계약 9 레지스트리 행 위치(D0b가 §7 파일 소절을 다시 씀 -- §1 D 수와 소절 괄호 수가 SR 파일 기준이 아니게 됨), 계약 7 import 줄(F1이 목적 모듈로 바꿈), 계약 8(S1 -- F1이 먼저 그 test를 고침).
* SR 파일 자체가 F2에서 사라지므로 '작성 전 실측'의 SR 줄 번호는 전부 다시 잰다(card가 이미 명시).

## 템플릿 대조

머리 블록 키·절 11개·순서 맞음. '작성 전 실측' 1~13 모두 항목이 있다. 13(red 모양): base red = GONE `AssertionError`뿐(모의 T-only 실측 2 failed, 다른 실패 0) -- 맞음. 9(승인 줄): 후보 id·UD-0 범위 원문 요구는 notes §3-4·질문 문안 UD-0 #2 문단에 반영됨(확인).

## 측정 명령(재현)

`git clone <작업 저장소> C:/g214/base && git -C C:/g214/base checkout 36e170e`; 모의 = `C:/g214/sim_card.py`(측정 전용, 삭제됨); suite = `python -B -m pytest -q -p no:cacheprovider -c <base>/tools/gates/pytest_gate.ini --rootdir=<트리> --confcutdir=<트리> --gmid-phase=2 -rfE`; V3 = `mutate_changed.py --root sim --base simbase --head simhead --pytest-ini …`; V5 = `weakening_diff.py --root sim --base simbase --head simhead`(diff_hash `1de67c0b…` -- 모의 diff 해시라 실제 기록에 쓰지 말 것); V7 = `reachability.py … --config <base>/tools/gates/gate_config.json`; reg_check = `tests/tools/reg_check.py --registry … --root …`; E-LIB = `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py`.
