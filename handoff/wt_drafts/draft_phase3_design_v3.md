# gain-budget-gmid-sizing -- Phase 3 `30-module-split` design

> **[초안 v3 -- 저장소 미반영]** 정식 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`(현재 없음).
> 측정 시점 = gate `master` `cd64170`(2026-09-30, B28 병합 전). 측정은 읽기 전용, 스크래치 `C:/g29`(끝나면 삭제). 측정 명령·결과는 부록 A, v1→v2 정정은 부록 B, v2→v3 정정은 부록 C
> (검토 `review_phase3_drafts.md` 발견별 대응은 `phase3_revision_log.md`).

버전 v0.3(초안). 정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05-role-separation`·`20-dead-code-dup`의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 표 `30-module-split` 행): N3.10, N6.1·N6.2 Phase 3, U-03. 추가로 읽은 절: N3.11(test 배치), N3.12.2(역할 경로), N3.12.3(card 단위·판정 유형), N4.2 V2·V3·V6·V7, N8,
WP-01·WP-03·WP-11·WP-14, NFR-2.

실측 원자료: `p3_measure.py`·`p3_assign.py`·`p3_refs.py`(초안 v1), `p3v2_g1_measure.py`(v2), **`p3v3_g1_measure.py` → `p3v3_g1_results.json`**(v3: 이동 규칙 참조 구현, 합성 27단계에서
base 게이트 도구 실제 실행, 실제 엔진 통째 이동 모의, 판정 기록 무동작), **`p3v3_facts.py` → `p3v3_facts.json`**(v3: N3.10 열·토큰, 중첩 참조, 인벤토리, 전수 스캔 이름, V3 출력 키).
`p3v3_g1_measure.py`의 참조 구현은 design 문장이 판정 가능한지 확인하는 초안 측정이다 -- G1 구현이나 test 기대값의 근거가 아니다(작성자≠검증자).
정식 문서로 올릴 때 원자료는 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/`에 둔다(20-dead-code-dup 선례).

---

## 1. 범위 (N9.2-1)

계획 N6.1 Phase 3 행(1000행)이 정본이다: "10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03". 이 Phase가 구현하는 것:

1. **게이트의 이동 인식**(G1): 계획 N3.10 533행 "해시가 같은 함수는 V3 대상에서 뺀다"가 도구에 없다(§5). 이동 card가 판정 가능하려면 먼저 필요하다.
2. **계약 test 위치 독립화**(T0): 정의가 **특정 파일에 있다고 가정하는** 계약 test 3개가 첫 이동 card에서 깨지거나 공허해진다(§7.1).
3. **이관표**(D0a·D0b): 레지스트리 '이관 목적지' 열을 N3.10 10모듈 이름으로 재생성하고, 계층 규칙(import는 작은 번호로만, 순환 0)을 **옮기기 전에** 계산으로 만족시키는 단위→모듈 배정(§6).
4. **이동**(M1~M9, 모듈 하나당 card 하나 -- 계획 N3.12.3 674행)과 **MOD10 진입점**(M10).
5. **test 재배치**(T1): `unit/test_selftest_<모듈>.py` 4개 → `unit/test_mod*.py`(계획 N3.11 test 배치 541~543행, `10-test-separation` 187·413행).
6. **호출부 갱신과 shim 삭제**(F1·F2), 모듈 속성을 덮어써 계측하는 probe의 처리(§7.2 D군, UD-7).
7. `00-common` §17 표가 넘긴 `optimize_full_circuit_budget` 목적지 불일치(MOD6 대 MOD8) 해소(§6 A-3, D-3).

범위 밖(명시): 함수 분할·추출(CC-7 θ 탐색부 추출은 Phase 4, `00-common` §10.1 435행), 이름 리터럴 교체(DF-23 → Phase 4/7a), D 함수 배선(Phase 4), 레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4), 광범위 except 정리(DF-37, Phase 4), V7 그래프 한계·같은 경로 import 재바인딩·클래스 수준 문장의 게이트 사각(§5.4 관찰 -- 백로그 후보).

---

## 2. 인터페이스 (N9.2-2)

A = `skills/analog-gmid-design/assets`.

### 2.1 파일 배치

| 경로 | 내용 | card |
|---|---|---|
| `A/gmid_lut.py` … `A/gmid_design_pipeline.py` | N3.10 MOD1~MOD10. **평면 배치**(하위 디렉터리 없음, D-1) | M1~M10 |
| `A/stick_diagram.py` | MOD7로 남고 줄어든다(구조 유도 함수가 MOD2·MOD3로 나간다, N3.10 527행) | M2·M3·M9 |
| `A/sizing_recipe.py` | 이관 중 **잔여 정의 + 명시 재수출 목록**(도구 생성, `_` 접두 포함, `import *` 금지 -- 534행) → F2에서 삭제 | M1~F2 |
| `A/topology_library.py`·`A/design_report.py` | N3.10 표에 없는 파일. 내용이 MOD4·MOD9로 나간 뒤 같은 방식의 재수출 shim → F2에서 삭제(D-2) | M4·M9·F2 |
| `A/audit_current_forced.py` | 도구로 남는다(`__main__` 감사 실행 경로, 레지스트리 248행 `render_report` 유지). `audit_topology`는 이관표 규칙 A-4대로(D-8) | M9 |
| `tools/migrate/move_plan.py` | 이관표·계층 사전 검사·재수출 목록·이동 대조 도구(code-author). CLI 정본 = D0a spec card 계약 1. test는 `A/tests/tooling/test_move_plan.py`(test-author) -- 계획 N3.11 549행 `tooling/`, `extract_selftest.py` 선례(D-7) | D0a |
| `tools/gates/reachability.py`·`mutate_changed.py`·`source_lint.py` | 이동 인식(`SourceIndex`·`moved_defs`, §5) -- 게이트 변경 | G1 |

### 2.2 shim 규칙

* 재수출은 `from <MODn> import a, b, _c` 형태만(명시 목록, 도구 생성 -- `move_plan plan`의 `reexports`). **def 래퍼를 두지 않는다** -- 래퍼는 동작 코드라 이동이 아니다(§3 MOVED M-2가
  이동으로 보지 않는다, 부록 A G5 `wrapper`).
* `stick_diagram.py`에서 나간 이름의 재수출은 **임시**이고 F2에서 지운다(한 이름에 import 경로 하나, WP-14).
* 모듈 수준 캐시(`sizing_recipe.py:2391 _KNEE_L_CACHE`, `:2530 _FEASIBLE_L_WINDOW_CACHE`, `:7697 _ACHIEVABLE_BOUND_CACHE` -- 셋 다 주석 대입 `: dict = {}`, 사용 함수는 각각 하나
  `knee_L_for_kind`·`feasible_L_window`·`achievable_metric_bound`; `topology_library.py:248` `@functools.lru_cache(maxsize=256)` 1곳 -- 254행은 주석)는 **읽고 쓰는 함수와 같은 모듈로**
  옮긴다(판정 CACHE-ID, NFR-2). 판정 도구는 `move_plan check`의 `cache` 발견이다. V6 `unbounded_cache`는 `ast.Assign`만 보므로 이 셋(주석 대입)을 보지 않는다 -- 그래서 CACHE-ID를
  게이트가 아니라 D0a 도구로 잰다. `global` 문 0개라 재수출 이름은 같은 객체를 가리킨다(부록 A M18; SHIM 판정 참고).

### 2.3 MOD10 진입점

* 정본 시그니처 `00-common` §10.1 431행: `run_gmid_design_pipeline(spec, *, search, output_dir, instrument=None, activations_out=None)`. **Phase 3(M10)는 `spec`·`topology_path`·`search`·`output_dir`까지만** 만든다 -- 하네스 `run()`(`workspaces/run_harness.py:422`)의 파이프라인 몸통을 옮기는 데 탐색 설정과 출력 경로가 필요하다. `instrument`·`activations_out`은 CC-7·CC-8(Phase 4).
* **정본 시그니처의 빈칸(실측)**: 하네스는 topology 경로를 spec이 아니라 `SPECS[circuit]["topology_file"]`에서 만들어(`run_harness.py:427`) `optimize_full_circuit_budget(topo, spec, …)`(446행)에 따로 넘긴다. 431행 시그니처로는 진입점이 topology를 찾을 수 없다 → 키워드 인자 `topology_path`를 더한다(D-5).
* M10은 이동이 아니라 **추출**(새 def + 하네스 `run()` 몸체 변경)이라 V3 대상이다. 지금 인벤토리(부록 A S12): `run_harness.py::run`에 도달하는 test 60개는 전부 `build_graph`의 이름 과대 근사
  (`subprocess.run`류 속성 호출 → 같은 이름의 모든 def)로 이어진 것(`tooling/test_extract_selftest.py` 24, `unit/test_selftest_sizing_recipe.py` 22 …)이고 하네스를 실제로 실행하지
  않는다 -- 변이를 죽이지 못한다. 그래서 **M10은 red-green**(새 test가 진입점을 library 회로로 불러 E-INST 해시를 대조, base에는 진입점이 없어 red)이다(§8).

### 2.4 새 함수·도구의 원칙(모든 card에 계약으로 들어간다)

* **topology 무관**: G1·D0a 도구는 코드 구조만 읽는다 -- `library/`·`*.topology.json`을 읽지 않고 회로·넷·소자 이름 리터럴이 없다. 합성 저장소(회로 없음)에서 동작함이 그 증거다.
* **만들면 배선**: `moved_defs`는 V3·V6·V7 세 도구의 `main`이 부르고, `SourceIndex`는 `moved_defs`와 `move_plan.py`가 부른다(G1). `move_plan.py`는 (i) D0b 계약 test가 매 card V1에서
  `plan`을 부르고 (ii) M card마다 판정 `equivalence.commands`에 `check`가 들어가며 (iii) DoD E2·E4·E6이 부른다. `plan`은 규칙 A-0 때문에 **Phase 어느 시점에서도** 같은 배정을 내므로
  (i)이 Phase 중간에 끊기지 않는다(검토 B4).
* **재계산 없음**(NFR-2): base·head 트리의 색인(`SourceIndex`)은 도구 실행당 커밋마다 한 번 만든다(파일마다 `ast.parse`·`symtable` 1회). `move_plan.py`는 한 번의 실행으로 배정·계층·
  재수출·순서·열 대조를 같이 낸다.
* **정의 하나**: 이동 판정의 해시 정의는 `def_hash` 하나다(G1이 `reachability`로 옮기고 `mutate_changed`는 import -- 이름·시그니처 유지). '모듈 전역에서 읽는 이름'·'이름의 바인딩 출처'도
  `reachability.SourceIndex` 하나다. `move_plan.py`는 계층 표를 `import_layering.mod_table`, 대표 대상 열을 `role_paths.read_section_table`, 참조·이동·해시를 G1 이름으로 읽는다.
* **작성자≠검증자**: 도구의 test는 test-author가 interface card만 보고 합성 입력(oracle (a))으로 쓴다. 판정 수치는 auditor 판정 기록에서만 인용한다. 이동 card의 판정 도구(`move_plan.py`)는
  D0a 병합 커밋의 사본을 쓴다(M card code-author가 같은 card에서 바꿀 수 없다 -- §8, 검토 S9).

---

## 3. 판정식 (N9.2-3)

숫자를 박지 않는다(WP-03). 모두 `영역: 없음(스키마)`. E-LIB·E-INST는 `20-dead-code-dup` §3 정의를 그대로 쓴다(재서술하지 않는다). '판정 도구' 열이 비지 않는 것만 판정식이다(만들면 배선).

**단위**: 소스 파일(`reachability._is_source`: `A/*.py`, `workspaces/run_harness.py`)의 최상위 **함수**(해시 `def_hash`), 최상위 **클래스 골격**(ClassDef에서 안의 모든 def를 이름 표지로
바꾼 사본의 `def_hash` -- 머리·데코레이터·클래스 수준 문장·메서드 이름과 순서 포함, 메서드 몸체 제외), 최상위 **문장**(import·def·class·`if __name__` 블록 밖, 문장 `ast.dump` 해시 --
문장은 해시로만 식별). **바인딩 출처** `binding_origin(p, n)` = 모듈 p 최상위에서 n이 가리키는 정의를 `from … import` 사슬을 따라가 얻은 `("def", 파일, 이름)`(또는 `ext`·`module`·`builtin`·
`unbound`·`multi`·`star`·`file-dir`(`__file__`)·`module-identity`(`__name__` 등·`globals`/`eval`/`exec`)). **전역 읽기** `global_names(u)` = u와 그 안 모든 유효 범위에서 Python 유효 범위 규칙상
모듈 전역으로 해석되는 이름 ∪ 데코레이터·기본값·기반·키워드의 이름 ∪ 주석(문자열 주석 포함)의 이름. 정확한 문언은 G1 spec card 계약 0~3.

| ID | 판정 | 식 | 판정 도구 |
|---|---|---|---|
| E-LIB / E-INST | 동작 보존 | `20-dead-code-dup` §3 | 그 정의의 측정 명령 |
| MOVED | 이동 인식(G1) | head 단위 u = (p_h, 키 q, 해시 h)가 **옮긴 단위** ⇔ (M-1) base에서 (종류, q, h)를 가진 소스 파일이 정확히 하나 p_b ≠ p_h(파일 안에서도 하나) (M-0) u가 바인딩하는 이름마다 base p_h의 바인딩 출처가 없거나 `("def", p_b, 이름)`(**덮어쓰기 거부**) (M-2) head p_b에 같은 단위가 없고 p_b에 남은 그 이름의 출처는 없거나 `("def", p_h, 이름)`(재수출뿐) (M-3) head에서 (종류, q, h)가 p_h 한 곳 (M-4) `global_names(u)`의 이름마다 base p_b의 출처 = head p_h의 출처, 또는 head 출처가 함께 옮긴 단위이고 그 원본 출처가 base 출처(**재바인딩·`__file__` 디렉터리 변경 거부**, 고정점). 메서드는 클래스 골격이 옮겨지고 자기 해시가 원본과 같을 때만 옮긴 def(**클래스 머리·필드 변경 거부**) | `reachability.moved_defs`(V3·V6·V7이 부름) |
| MOVE-AST | 이동 동일성(533·1018행) | card k의 병합본에서 (a) 이관표가 card k에 배정한 **최상위 단위**(함수·클래스·문장) 집합 = MOVED가 낸 k 목적지 옮긴 단위 집합 (b) 옮긴 단위가 아닌데 해시가 바뀌었거나 새로 생긴 단위 0(클래스 골격·문장 포함 -- V3가 보지 않는 클래스 필드 기본값 변경도 여기서 잡힌다) (c) 사라진 단위 0 (d) MOVED가 거부한 후보 0 | `move_plan check`(`move-set`·`changed`·`lost`·`move-rejected`) + V3 JSON(§10 E2) |
| MOVE-TOTAL | 정의 보존 | Phase 전 base와 Phase 후 병합본 사이에서 MOVE-AST (b)(c)(d)를 전 단위로: 바뀐·새·사라진 단위는 M10이 선언한 것(`run_harness.py::run`, `gmid_design_pipeline.py::run_gmid_design_pipeline`)뿐 | `move_plan check --card ALL --allow-changed …`(E6) |
| PLAN-LAYER | 이동 전 계층 사전 검사 | 이관표 σ에서, 단위 u의 참조 R(u)(`global_names`의 이름 중 출처가 split·MOD 파일의 정의인 것 + 그 파일 모듈 별칭 속성, 중첩 def·메서드 포함 -- 문자열·해석 못 한 이름 제외) u→v 중 σ(u) < σ(v)인 것 0, 모듈 순환 0 | `move_plan plan`(`upward`·`cycles`) |
| LAYER | 계층 | `import_layering.py --root <iso>` exit 0 | 그 도구 |
| ORDER | 중간 상태 | card k 병합본에서 새 MOD 파일의 import가 가리키는 트리 파일 ⊆ {번호가 작은 MOD}(잔여 split 파일 없음). `import_layering`은 표 밖 파일을 보지 않으므로 별도 | `move_plan check`(`order`) |
| SHIM | 재수출 정확성 | 재수출 shim에 docstring과 `from <MOD> import …` 밖 문장 0(def·class·대입·`import *` 0), 재수출 이름 집합 = (base 재수출) ∪ (이 card가 그 파일에서 옮긴 이름), 이름마다 shim의 바인딩 출처 = MOD의 바인딩 출처(출처가 같으면 import가 같은 객체를 묶는다 -- `getattr(shim, s) is getattr(MOD, s)`의 정적 형태. 실행 중 속성 덮어쓰기는 §7.2 D군) | `move_plan check`(`shim`) |
| CACHE-ID | 캐시 단일성(NFR-2) | 모듈 최상위 캐시(이름에 `cache`, 값이 빈 dict -- 대입·주석 대입)를 전역 읽기로 쓰는 단위가 모두 캐시와 같은 파일 | `move_plan check`(`cache`) |
| LOC-FREE | 위치 독립(T0) | 계약 test의 판정이 '정의 파일'을 이름으로 가정하지 않는다 -- 같은 test가 base 트리와 **정의 하나를 다른 파일로 옮긴 합성 트리**에서 같은 결과 | T0 계약 6·7(auditor 합성 트리 실행) |
| GONE-SHIM | shim 삭제 | 마지막 card 병합본에서 `sizing_recipe.py`·`topology_library.py`·`design_report.py` 없음, 추적 `.py`의 해당 import(줄 머리와 문자열 import 모두) 0(제외 집합 D-9 밖) | §10 E3 |
| REG-DEST | 레지스트리 = 실제 위치(1018행) | 레지스트리 함수 행의 목적지 셀이 MOD 파일 이름 하나이고, 그 단위의 배정 MOD(= 이동 뒤에는 규칙 A-0의 현재 파일)와 같다 | `move_plan plan`(`reg_mismatch`, A-0) |
| LAYOUT-FLAT | 평면 배치 | MOD1~MOD10 파일이 전부 `A/` 바로 아래 | E0(`import_layering` `present`) |
| ENTRY | MOD10 | `run_gmid_design_pipeline`이 있고 `workspaces`를 import하지 않으며 하네스 `run()`이 그것을 부른다 | M10 spec card(red-green) |

---

## 4. 실패 경로 (N9.2-4)

Phase 4 전이라 N3.14 실패 클래스가 없다(`20-dead-code-dup` §4와 같은 상황).

| ID | 경우 | 결과 | 처리 |
|---|---|---|---|
| F1 | PLAN-LAYER FAIL | 이동하지 않는다 | §6 규칙으로 배정을 고친다. 규칙으로 안 풀리면 N3.10 표 개정(이 design 승인 범위 -- §9 D-11) |
| F2 | MOVE-AST FAIL(옮기며 본문·클래스 머리·필드가 바뀜) | V2 FAIL(G1 뒤에는 V3 대상도 생긴다) | card 되돌림. 본문 수정이 필요한 이동은 Phase 3가 아니다 |
| F3 | 중간 상태 순환 import | V1 수집 오류 | 순서를 고친다. 함수 안 지연 import로 우회하지 않는다(우회 = skip, 메모리 원칙) |
| F4 | E-LIB·E-INST 차이 | V2 FAIL | 모듈 수준 상태 분리를 먼저 의심(CACHE-ID) |
| F5 | G1 병합 전 이동 card | 판정 불가(V3 변이 약 1.6만 개, V6 새 항목 861, V7 미도달 약 108 -- §5.1) | G1 병합 전에는 M card를 시작하지 않는다(§8) |
| F6 | 계약 test가 첫 이동에서 깨지거나 공허해짐 | equivalence 불성립 | T0 병합 전에는 M card를 시작하지 않는다 |
| F7 | MOVED 거부(`move-rejected` M-0/M-4) | 옮긴 단위가 아니라 V3 대상·`changed` | 배정을 따라 **함께 옮길 것을 함께** 옮기거나(재바인딩 대상이 이 card 배정이면) 새 MOD가 원본과 같은 출처에서 import하게 import 줄만 고친다. 몸체를 고치지 않는다 |
| F8 | 모듈 속성 덮어쓰기 probe가 이동 뒤 계측을 잃음(§7.2 D군) | probe 결과가 조용히 비거나 달라짐(V1이 probe를 수집하지 않아 FAIL로 드러나지 않는다) | UD-7 결정대로 F1에서 덮어쓰기 대상을 호출자 모듈로 옮긴다(기본안) |

---

## 5. 게이트의 이동 인식 (G1)

### 5.1 실측: 지금 게이트는 옮긴 정의를 새 정의로 본다

| 도구 | '새/바뀐 def'를 정하는 곳(cd64170) | 옮긴 정의에 대한 결과 |
|---|---|---|
| V3 `mutate_changed.py` | `changed_defs(base_src, head_src)`(50~62행)이 **같은 경로**의 base 소스와만 비교. `main`이 `git cat-file -e <base>:<path>`(321행)로 base 파일이 없으면 `base_src = None`(323행) → 그 파일의 def 전부가 대상(326행). diff는 `--no-renames --diff-filter=AM`(276행) | 엔진 4파일을 새 파일로 옮기면 대상 def 473개·변이 15,677개(부록 A G1). 인벤토리 없는 def는 변이 전부 '생존' |
| V6 `source_lint.py` | `compare(path, base_src, head_src, kd)`(212행)가 같은 경로 base와 단위별 항목 수 비교, base 없으면 전부 '새 항목' | 새 파일로 옮기면 새 항목: magic_number 500·continue 347·broad_except 8·id_call 6(부록 A G1) |
| V7 `reachability.py` | `base_defs` = base의 (파일, qualname) 집합(224~229행), `new_defs` = head 노드 중 그 집합에 없는 것(230~231행) | 지금 운영 루트로 도달하지 못하는 엔진 def 109개(승인 면제 1) -- 옮기면 전부 '새 def 미도달'로 FAIL(부록 A G2) |

합성 저장소 red 실측(부록 A G5 `move-exact`): def 하나를 바이트 그대로 새 파일로 옮기고 원래 파일은 재수출만 남긴 커밋에서 base V3·V6·V7 모두 exit 1.

**계획 원문**(N3.10 533행): "무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. **해시가 같은 함수는 V3 대상에서 뺀다.**" -- V3 행(N4.2 839행)도 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것"이고 경로를 말하지 않는다. V6(842행)·V7(843행)은 이동을 말하지 않는다.

### 5.2 고칠 방향

* **판정식은 그대로, 비교 기준만 옮긴다**: 옮긴 단위(§3 MOVED)는 비교 기준이 '같은 경로의 base'에서 '이동 원본'으로 바뀐다.
  * V3: 옮긴 def는 대상이 아니다. 옮기며 한 토큰이라도 바뀐 def, 거부된 후보(M-0~M-4)의 def는 지금처럼 대상.
  * V6: 옮긴 def 단위의 '이전 항목 수'는 원본 단위를 원본 파일 맥락에서 센 값. 옮긴 문장은 새 파일 `<module>` 단위의 이전 항목 수에 원본 맥락 값(그 문장 줄 범위)으로 더해진다.
    **새 파일 맥락에서 항목이 늘면 FAIL**(부록 A G5 `cache-split`: 캐시 dict만 옮기고 `len()` 검사를 원래 파일에 남기면 `unbounded_cache` -- 옮긴 문장이라도 걸린다).
  * V7: 옮긴 def는 '새 def'가 아니다.
* **약화하지 않는다 -- 반례 재실행**(부록 A G5, base 도구는 실제 실행, 새 규칙은 참조 구현 모의): 초안 v2 규칙(M-1~M-3)이 통과시키던 검토 반례 3종이 v3에서 모두 거부된다.

  | 단계 | 무엇을 막나 | v3 규칙 | base V3/V6/V7 | v3 V3/V6/V7 |
  |---|---|---|---|---|
  | `overwrite` | 목적 파일의 같은 이름 정의(다른 본문)를 옮긴 본문으로 덮음 -- 호출자 동작이 바뀜(검토 B1) | M-0 | 1/1/0 | 1/1/0 |
  | `overwrite-import` | 목적 파일이 base에서 같은 이름을 다른 모듈에서 import | M-0 | 1/1/1 | 1/1/1 |
  | `swap` | 두 파일 def 교환 | M-0 | 1/1/0 | 1/1/0 |
  | `rebind` | 옮긴 def가 읽는 `helper`를 목적 파일이 다른 정의에 묶음(검토 B2) | M-4 | 1/1/1 | 1/1/1 |
  | `file-dir-change-noshim` | `__file__`을 읽는 def를 다른 디렉터리 소스 파일로 | M-4 | 1/1/1 | 1/1/1 |
  | `class-header-changed` / `class-field-changed` | 클래스 기반·필드를 바꾸며 메서드 이동(검토 B3) | 골격 해시 | 1/1/1 | 1/1/1 |
  | `copy`·`wrapper`·`ambiguous`·`two-targets`·`move-edited` | 초안 v2부터 거부 | M-2·M-2·M-1·M-3·해시 | 1/1/1 | 1/1/1 |

  인정 9단계(red → green): `move-exact`, `absorb-own-import`(목적 파일이 base에서 원본을 import하던 경우), `move-with-helper-import`(새 파일이 원본 모듈에서 helper를 import -- 출처가 같아
  G1은 인정, Phase 3에서는 `move_plan check` `order`가 잔여 split import로 거부), `move-together`, `move-chain`(앞 card에서 옮긴 이름을 새 MOD가 그 MOD에서 import),
  `local-shadow`(지역 이름이 원본 최상위 이름과 같음 -- 유효 범위 규칙으로 전역 아님), `file-same-dir`, `class-exact`, `cache-together` -- 모두 base 1/1/1 → v3 0/0/0.
* **거짓 거부 측정**(부록 A G6): 실제 엔진 4파일 각각을 같은 디렉터리 새 파일로 통째 옮기고 원래 파일은 명시 재수출만 남긴 모의에서 옮긴 단위 402/402(SR 218·SD 169·TL 8·DR 7),
  옮긴 def 473/473, 거부 0. `stick_diagram`의 `__file__` 사용 2곳(1050·8973행)도 같은 디렉터리라 인정. 참조 구현 한 호출 5.8~9.2초(전체 소스 두 벌 색인).
* **관찰 가능**: 세 도구의 판정 JSON에 `moved`(`[{"from", "to"}]`)와 `move_rejected`를 더하고, V3에는 변이 대상 def 목록 `defs`를 더한다(§10 E2가 `targets`가 아니라 이것을 잰다 -- 검토 B5).
* **기존 이름·시그니처 유지**: `mutate_changed.changed_defs(base_src, head_src)`·`def_hash(fn)`은 기존 판정 기록 스크립트 3곳이 부른다(부록 A G4). 해시 정의는 `reachability`로 옮기고
  `mutate_changed`는 그것을 import해 같은 이름으로 둔다(`mutate_changed`가 `reachability`를 import하므로 반대 방향이면 순환 -- 정의 하나).
* **비용 선택(UD-5)**: 이 절의 방식은 **전역 이동 인식 규칙**이다. 대안은 '승인 기록에 선언된 이동 목록(from→to)만 인정'이다. 비교와 권고는 §9.2 UD-5.

### 5.3 B28(`20260930-v3-history-clone`)과의 합성

지금 gate `master` = `cd64170`, B28은 병합 전(`role/code/20260930-v3-history-clone` = `dee338d`). B28은 `mutate_changed.main`의 **test 실행 환경**(copytree → `--head` 격리 복제본, 기준 실행
실패 → `ERROR`, 임시 디렉터리 정리)을 바꾼다. G1은 **대상 선택**(`changed_defs` 호출 앞 이동 제외)과 판정 JSON 필드 추가만 바꾼다. B28 판에서 그 호출은 364행, base 존재 확인 359행,
출력 407~408행이다. 출력 키는 두 판 모두 `tool, verdict, targets, mutants, killed, survivors`(B28은 ERROR 출력에 `baseline_failed` 추가 -- 부록 A V3). 합성 규칙:

1. G1의 test worktree는 **B28 push 뒤 gate `master`**에서 만든다(05 §12 순서 1). G1 spec card의 '작성 전 실측' 줄 번호는 그 base에서 다시 잰다.
2. G1의 무동작 입력에 B28의 redteam `attacks/31-v3-git-history/` 세 단계를 넣는다(결과 불변).
3. G1은 B28의 계약(격리 복제본·`ERROR`·임시 디렉터리 무누수)을 건드리지 않는다. G1이 새로 여는 git 호출은 base 트리 읽기(`ls-tree`·`show`)뿐이다.
4. §10 E2는 G1이 더하는 `defs`·`moved`와 두 판 공통 키 `mutants`를 읽는다 -- B28이 출력 키를 바꾸면 E2 명령을 다시 잰다(의존 명시).

### 5.4 관찰(범위 밖, 백로그 후보)

* V7 그래프는 클래스 인스턴스화에서 `__init__`로, 모듈 최상위 레지스트리 dict에서 값 함수로 가는 간선이 없어 `SemiEmpiricalGmIdLUT.__init__`·`_feed_*` 같은 def를 미도달로 센다(부록 A G2).
* **같은 경로 import 재바인딩**: `a.py`의 `from c import helper`를 `from d import helper`로 바꾸면 V3·V6·V7 모두 exit 0이다(부록 A G5 `same-path-rebind(observation)` -- def가 바뀌지 않았으므로).
  G1의 M-4는 **옮긴** def에 대해 이 사각을 막지만 같은 경로 변경에는 관여하지 않는다(약화도 강화도 아님). Phase 3 이동 card에서는 `move_plan check`가 import 외 변경을 보지 않으므로
  같은 경로 import 교체도 이 사각에 든다 -- M card의 import 줄 변경은 E-LIB·E-INST(V2)가 동작으로 잰다.
* **클래스 수준 문장**: V6 `_units`는 클래스 몸체의 리터럴을 어느 단위에도 넣지 않고 V3는 def만 보므로 dataclass 필드 기본값 변경은 세 도구 모두 보지 않는다(부록 A G5
  `record-class-default-changed` base·v3 모두 0/0/0). 이동 card에서는 `move_plan check`의 `changed`(클래스 골격 해시)가 잡는다.

---

## 6. 이관표 생성 규칙 (N9.1 '레지스트리 목적지 열에서 생성')

### 6.1 왜 열을 그대로 읽을 수 없는가(실측, cd64170)

* 레지스트리 함수 행 379개의 목적지 셀 분류: `gmid_sizing_engine` 114, `stick_diagram` 87, `circuit_state_graph` 61, `topology_authoring` 32, `sizing_layout_convergence` 14, `instance_report_builder` 7, `gmid_design_pipeline` 2, **MOD 이름이 없는 셀 62**(`optimizer`, `〃`, `삭제 후보`, `test util`, `LUT 생성 도구 유지` 등). **MOD1 `gmid_lut`·MOD5 `circuit_metrics`·MOD6 `theta_search`로 가는 행 0**(부록 A M9).
* 레지스트리 머리: "작성 2026-09-14, 기준 커밋 78b58c6. 계획서 §13(v4.44)의 부속 문서" -- 목적지 열은 10모듈 표 이전 판의 이름을 쓴다.
* N3.10 표 '대표 대상'과 열이 다른 행: `GmIdLUT`·`SemiEmpiricalGmIdLUT`·`_multilinear_interp`(표 MOD1, 열 `gmid_sizing_engine`), `load_topology`(표 MOD2), `compute_metric`·`build_ac_network`·`_full_circuit_response`·`estimate_mismatch_sigma`(표 MOD5), `search_stage_budget_L_warm_start`·`presolve_warm_start`·`_optimize_theta_slsqp`·`repair_infeasible_baseline`(표 MOD6, 열 `optimizer`) 등(부록 A M10).
* 둘 이상 모듈로 **쪼개라**고 적은 셀 16행(부록 A M11). 이동 전용 규칙으로는 함수를 쪼갤 수 없다.
* 레지스트리에 행이 없는 최상위 정의: `sizing_recipe` 3, `stick_diagram` 24(DF-36의 `_topology_ref_relpath` 포함). 초안 배정 뒤 미배정 최상위 이름 34(대입 포함)(부록 A M12·M13).
* 초안 배정으로 **큰 번호로 향하는 참조 64개**(MOD2→MOD3 17, MOD3→MOD4 14, MOD3→MOD7 9, MOD4→MOD5 8, MOD2→MOD7 6, …, 가장 많은 원천 `_hr_resolve_vertical_group` 9)(부록 A M14). 이 계수는 `ast.Name` 참조만 센 것이다 -- PLAN-LAYER 정식 계수는 D0a 도구가 낸다.
* 참조를 최상위 몸체에서만 세면 모자란다: 중첩 def·메서드 안에서만 다른 최상위 이름을 참조하는 최상위 단위가 SR 17·SD 4(예 `SemiEmpiricalGmIdLUT` → `_multilinear_interp`)(부록 A S6). 그래서 R(u)는 G1 `global_names`(모든 하위 유효 범위)로 센다.

### 6.2 규칙(우선순위 높은 것이 이긴다. 도구가 단위마다 근거 규칙 ID를 남긴다. 정확한 문언은 D0a spec card 계약 2·3)

* **A-0 현재 위치**: N3.10 표 파일 중 그 트리에 있고 분할 대상(`--split`)이 **아닌** 파일의 단위는 그 파일. 이동 뒤에도 `plan`이 같은 배정을 내게 하는 규칙이다(Phase 중 D0b 계약 test·
  REG-DEST·E4 -- 검토 B4). 분할 대상 파일이 없는 트리(F2 뒤)는 오류가 아니라 `absent_split`으로 보고한다.
* **A-1 계획 명시**: N3.10 표 '대표 대상' 열의 백틱 토큰 -- 식별자(글롭 `*` 허용)는 그 이름, `<파일>.py`는 그 파일 전체, `<모듈>.<이름>`은 이름, 그 밖(`∂ID/∂VSB`, `workspaces/`)과 산문은 무시
  (부록 A S5: 식별자 41·파일 1·점 이름 1·무시 2, MOD7은 산문뿐). 열은 `role_paths.read_section_table`로 읽는다(`mod_table`은 ID·파일 열만 -- 게이트 코드 무변경). 계획 532행(`canonical_spec`/`SPECS`는 하네스에 남음) 포함.
* **A-2 레코드 클래스 하강**: 레코드 = `@dataclass`(이름·속성·호출), 내장 예외 또는 다른 레코드를 기반으로 하는 클래스, 메서드 없는 클래스. 그것을 참조하는 단위(문자열 주석 포함, 레코드 자신 제외)
  중 **가장 낮은 번호**로. 엔진 클래스 41 중 dataclass 36, 예외 3, 메서드 없는 클래스 36(부록 A G6 `classes`).
* **A-3 계층 강제**: 목적지 셀이 MOD를 둘 이상 적은 16행은 쪼개지 않고 max(셀의 가장 작은 MOD, 피참조의 최대 MOD)로 통째(쪼개기는 그 셀이 적은 담당 Phase). A-1과 충돌하면 N3.10 표를
  고친다(D-11). 계산으로 드러난 충돌: `load_topology`(표 MOD2)가 구조 자동채움을 부른다(부록 A M15) → MOD3. `validate_theta_declaration_order`(표 MOD2)가 `_build_shared_current_joint_plan`·
  `_shared_current_groups_from_compensation`을 부른다 → 그 둘의 MOD 이상. `optimize_full_circuit_budget`(표 MOD6 '탐색부')는 `stick_diagram` 레이아웃 함수 8개와
  `run_topology_pipeline_with_finger_fixup`(MOD8)을 부른다 → Phase 3 위치 MOD8(D-3), 탐색부 추출 뒤 MOD6(CC-7, `00-common` 435행과 일치).
* **A-4 레지스트리 열**: 셀의 식별자 토큰 중 MOD 파일 줄기와 별칭 키를 MOD로 바꾼 것이 하나면 그 MOD. 옛 이름: `optimizer` → MOD6(책임 '실패 캐시, 시작점, 전역 샘플, S3', 526행), `〃` → 위 행.
  (초안 v2의 "`_metric_*`·metric 레지스트리 → MOD5"는 이름 규칙이라 뺐다 -- `_METRICS_REGISTRY`는 A-1(MOD5)이고 `_metric_*` 함수는 그 레지스트리가 참조자라 A-5로 MOD5에 간다.)
* **A-5 소비자 따라**: 행이 없는 정의와 최상위 문장은 **그것을 참조하는 단위 중 가장 낮은 MOD**로(상수·레지스트리 dict는 소비자를, 레지스트리 값 함수는 레지스트리를 따른다). 참조자가 없으면
  `unassigned`로 **도구가 FAIL**한다(조용한 기본값 금지) -- D0b에서 사람이 규칙을 더하거나 N3.10 개정으로 닫는다.
* **결과 조건**: A-0~A-5 적용 뒤 PLAN-LAYER exit 0이어야 레지스트리 열을 갱신한다(D0b). 갱신 뒤 `plan`의 `reg_mismatch` 0 = REG-DEST.

### 6.3 도구 `tools/migrate/move_plan.py`(D0a)

CLI·출력·exit의 **정본은 D0a spec card 계약 1~4**이고 이 절은 요약이다(검토 B6 -- 두 문서가 따로 적지 않는다).

| 명령 | 요지 |
|---|---|
| `plan --root R [--rev C] --plan P --registry G --split F… [--keep F…] [--aliases JSON]` | 단위 → MOD 배정(근거 규칙), `upward`·`cycles`(PLAN-LAYER), `unassigned`, `conflicts`, `reexports`, `order`, `absent_split`, `reg_mismatch`(REG-DEST). 경로 인자는 `--rev` 커밋에서 읽는다 |
| `check --root R --base B --head H --card <MOD 파일>\|ALL --plan P --registry G --split F… [--keep F…] [--aliases JSON] [--allow-changed ID…]` | `move-set`·`move-rejected`·`changed`·`lost`(MOVE-AST), `order`(ORDER), `shim`(SHIM), `cache`(CACHE-ID). 배정은 base 커밋에서 계산 |

게이트 모듈은 `--root`의 `tools/gates`에서 import한다 -- 다른 커밋에서 꺼낸 사본으로 실행할 수 있다(§8 M card, §10).

실제 저장소 인자(§10과 M card가 쓴다):

```
MP_ARGS="--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md \
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md \
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py \
         --keep audit_current_forced.py --aliases '{\"optimizer\": \"theta_search.py\"}'"
```

---

## 7. 계약 test와 호출부

### 7.1 위치에 묶인 계약 test(실측 cd64170, 부록 A M24)

`A/tests/contracts/`에서 엔진 파일·모듈 이름을 **실제 트리 판정에** 쓰는 곳(합성 소스 문자열 안의 `import sizing_recipe`는 입력이라 제외):

| 군 | 깨지는 시점 | test(줄) | 처리 |
|---|---|---|---|
| **A. 정의가 특정 파일에 있다고 가정** | 그 정의를 옮기는 첫 M card | `test_ic5.py:47-69`(`_DOMAIN_TABLE` 키 = (파일 이름, 함수) 21개), `test_dup_w_calc.py:442`(`size_transistor` 정의를 `sizing_recipe.py`에서 찾음 → M4에서 FAIL), `test_ts6_dead_probes.py:221-222`(`_L_ROLE_MULTIPLIERS` 바인딩 검사 범위가 `sizing_recipe.py` 한 파일 -- 옮긴 뒤 **조용히 공허**), `:261-262`(`audit_vsb_consistency`의 운영 호출자를 `sizing_recipe.py`에서만 찾음) | **T0**(M1 전) |
| **B. 모듈 이름으로 import·파일 존재 앵커** | shim 삭제(F2) 또는 호출부 갱신(F1) | `test_d_delete_dead.py:74·98-101·201·286·295`, `test_d_delete_telescopic.py:108-117·155·233`, `test_d_move_tests.py:69·73`, `test_dup_w_calc.py:56·72-75`, `test_df35_harness_paths.py:206`, `test_ts6_probe_relocate.py:528`, `test_ts6_dead_probes.py:229`, `test_restore_plan_functions.py:54·113-140`, `test_ic3.py:107·271`, `test_df36_instance_relpath.py:76·87·237·274·288` | **F1** |
| **C. test 파일 이름 목록** | T1 | `test_ts3_no_print_verdicts.py:29-30` `_LEGACY_SCRIPTS` | **T1** |

A군만 T0에 둔다(최소 수정). B군은 shim이 살아 있는 동안 통과하고, 계획 534행이 '추적 파일 호출부 갱신'을 shim 삭제 조건으로 적었으므로 F1이 import를 목적 모듈로 바꾼다. 스캔 범위가
이미 `A/*.py` 전체인 판정(`_engine_files()` glob, GONE 검사)은 새 MOD 파일을 자동으로 포함하므로 고치지 않는다. T0는 `test_ts6_dead_probes.py`의 모듈 상수 `_SIZING_RECIPE`(소비자가
바꾸는 두 test뿐)도 지운다(부록 A S13 -- 초안 v2의 "229행이 계속 쓴다"는 틀렸다).

**T0의 해석 규칙 R-DEF**: 이름 n의 정의 파일 = `A/*.py`(하위 디렉터리 제외)와 `workspaces/run_harness.py` 중 최상위(메서드는 `Class.method`)에서 n을 def·class·대입으로 **바인딩**하는
파일(AST, import로 받은 이름은 정의가 아니다 -- shim 재수출은 정의가 아님). 정의 파일이 정확히 하나가 아니면 FAIL(0 = 공허, 2 이상 = 모호·사본). 이 규칙은 **판정 범위를 넓힌다**.
T0의 새 줄이 피해야 할 전수 스캔 토큰 목록은 T0 spec card 계약 9(부록 A m6).

### 7.2 추적 호출부(F1 대상, 실측 cd64170, 부록 A M22)

엔진 4모듈을 줄 머리 `import`/`from`으로 가져오는 추적 `.py` 86개: `A/` 루트 4, `A/tests/unit` 10, `A/tests/probes` 27, `A/tests/contracts` 3, `A/tests/tools` 2, `A/tests/conftest.py` 1(conftest 변경은 V5 무조건 승인 대상), `workspaces/run_harness.py` 1, `workspaces/current-reuse-telescopic-ota-report/**` 27, `workspaces/two-stage-ota-report/**` 4, `.ai/verification/**/scripts` 6, `docs/03-analysis/**` 1. **문자열 import** 10곳(`importlib.import_module("sizing_recipe")`·`_import("sizing_recipe")` -- 전부 B군 계약 test, 부록 A m7). 추적 안 된 `workspaces/*.py` 1개(`smoke_run_harness_session18_save.py`).

**D군 -- 모듈 속성 덮어쓰기**(부록 A S11): 엔진 모듈 속성에 대입해 계측·차단하는 추적 파일 8개(대입 12줄): probe 6개(`probe_b22_headroom_attribution.py:104·116`,
`probe_diode_gmid_readiness.py:63`, `probe_diode_pass_skips.py:94`, `probe_diode_window_corner.py:100·108`, `probe_matching_pair_divergence.py:124`, `probe_vds_assignment_paths.py:47·53·62·73·79`)와
`workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20`. unit·contracts·conftest·엔진·하네스에는 0. 분할 뒤 호출자는 **자기 모듈 전역**에서
이름을 읽으므로 shim이나 정의 모듈의 속성을 바꿔도 다른 모듈의 호출자는 가로채지 못한다 -- probe는 V1이 수집하지 않아 계측이 **조용히** 빈다(F8). 처리 = UD-7(기본안: F1에서 덮어쓰기 대상을
`binding_origin`으로 찾은 **호출자 모듈 전부**로 바꾸고, F1 oracle의 'import 줄 외 동일'에 이 대입 줄만 예외로 둔다).

---

## 8. 역할별 산출물 -- spec card 목록 (N9.2-5)

card 단위는 N3.12.3(674행: 이동은 모듈 하나가 한 건). 판정 유형은 **커밋 모양이 정한다**(code 커밋이 없으면 test-only, 있으면 red-green 또는 equivalence -- `20-dead-code-dup` §8 P2·P7 정정).

| # | id(초안) | 대상 | 판정 유형 | oracle | 원칙 제약 |
|---|---|---|---|---|---|
| **G1** | `p3-gate-move-aware` | `tools/gates/reachability.py`(`SourceIndex`·`moved_defs`·해시 정의), `mutate_changed.py`(V3 대상 선택·`defs`·`moved`), `source_lint.py`(V6 비교 기준), redteam 새 케이스, design 05 §10 V3·V6·V7 행·계획 533행 문구(spec card와 같은 커밋) | red-green, `gate_change: yes`, phase 0.5(05 §18) | (a) 합성 저장소 20단계(red 7, 거부 13) | 약화 금지(M-0~M-4·골격), `moved`·`move_rejected`·`defs` 출력, 해시·이름 해석 정의 하나, 실행당 색인 1회, B28 뒤 base |
| **T0** | `p3-tests-location-free` | §7.1 A군 3파일을 R-DEF로, `_SIZING_RECIPE` 삭제 | **test-only** + V5 승인 | (c) base 트리 결과 동일 + (a) 합성 이동 트리에서도 PASS(옛 test는 FAIL) | 판정 범위를 좁히지 않는다, 정의 파일 유일성, 전수 스캔 토큰 회피 |
| **D0a** | `p3-move-plan-tool` | 새 `tools/migrate/move_plan.py`(`plan`·`check`) | red-green | (a) 합성 저장소(이동 card를 차례로 적용한 커밋들·shim 삭제 커밋 포함) | CLI 정본, A-0으로 Phase 전 구간 동작, G1 뒤 base |
| **D0b** | `p3-registry-dest` | 레지스트리 목적지 열 전 행 = MOD 이름 하나(+ 근거 규칙 열), §7 `보류(Phase 3)` 9행 처리 열 = `보류(Phase 4)`, N3.10 표 개정(A-3 결과), 새 계약 test `contracts/test_p3_registry_dest.py`(`move_plan plan` exit 0·`reg_mismatch` 0·`upward`·`cycles` 0) | red-green(base 열에서 `reg_mismatch`로 FAIL) | (d) 도구 출력 = 열. 동어반복 방지로 oracle을 둘로 나눈다: 규칙 손적용 합성 입력(도구 test와 별도 표본) + 실제 트리 drift guard(검토 §2 (3) V4) | 손으로 쓰지 않는다(도구 출력). N3.10 개정은 이 design 승인(D-11) |
| **M1**~**M6**, **M8**, **M9** | `p3-move-mod<n>-<이름>` | 이관표 MODn 배정 전부(파일:줄은 D0b 뒤 도구 출력) | equivalence(test 커밋 0 가능 -- 05 §9.2 289행) | (c) MOVE-AST + E-LIB·E-INST + SHIM + CACHE-ID + ORDER(`check` 발견 0) | G1·T0·D0b 뒤. **`tools/**` 변경 0**(`git diff --name-only <base> <head> -- tools` 빈 출력). 판정 도구는 D0a 병합 커밋의 `move_plan.py` 사본(`git show <D0a code_commit>:tools/migrate/move_plan.py`) -- code-author가 판정 도구를 같은 card에서 바꿀 수 없게(검토 S9) |
| **M7** | -- | `stick_diagram.py`에 레이아웃만 남았는지 -- 이동 없음 | M2·M3·M9에 흡수(빈 card 금지) | -- | -- |
| **M10** | `p3-mod10-entry` | 새 `gmid_design_pipeline.run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)`, 하네스 `run()`이 부른다 | **red-green**(새 test가 library 회로로 진입점을 불러 E-INST 해시 대조 -- base에 진입점 없음) | (c) E-INST·E-LIB + (a) ENTRY | 만들면 배선: 하네스 즉시 호출, `after_phase3` 루트. 지금 인벤토리는 이름 과대 근사뿐(§2.3) |
| **T1** | `p3-test-relocate` | `unit/test_selftest_*.py` 4개 → `unit/test_mod*.py`, C군, 새 C9 매핑 | test-only + V5 승인 | (c) 수집 test id 집합 = 매핑 | `10-test-separation` 413행 |
| **F1** | `p3-callers-update` | §7.2 추적 호출부 import(줄 머리·문자열)를 목적 모듈로(D-9 제외 집합 밖), B군 계약 test, D군 덮어쓰기 대상(UD-7) | equivalence | (c) 호출부 AST가 import 줄(과 UD-7이 허용한 D군 대입 줄) 외 동일 + E-INST | test 쪽 문자열 변경은 V5 승인 |
| **F2** | `p3-shim-delete` | shim 3파일 삭제, `stick_diagram` 임시 재수출 제거, REG-DEST | red-green | (a) GONE-SHIM | WP-14 |

**card 수 15**(G1, T0, D0a, D0b, M1~M6, M8, M9, M10, T1, F1, F2 -- M7 흡수).

### 8.1 순서와 병렬 준비

```
B28(진행 중) ──> G1 ──> D0a ──> D0b ──┐
T0 ───────────────────────────────────┼──> M1 → M2 → M3 → M4 → M5 → M6 → M8 → M9 → M10 → T1 → F1 → F2
```

* **지금 병렬로 준비 가능(spec card 초안·작성 전 실측)**: G1, T0, D0a. 실행 순서는 G1 → D0a(D0a가 G1의 `SourceIndex`·`moved_defs`를 부른다 -- 같은 개념을 둘로 구현하지 않기 위한 의존), T0는 독립.
* M 순서가 번호순인 이유: 작은 번호부터 만들면 매 card 병합본에서 새 파일이 잔여 shim을 import할 일이 없다(ORDER). M 작성 전 실측은 D0b 이관표 한 벌에서 결정적으로 나온다.

---

## 9. 착수 조건과 사용자 결정 (N9.2-7)

### 9.1 착수 조건

* 공통(N6.1 991행): 이 문서의 사용자 승인(DEC-51), **Phase 2 DoD PASS**(현재 남은 것: P9, P10, DoD E0~E5 -- `.ai/context.md` 기준, P3c 보류 B21).
* U-03(N7.2 1078행): 승인 기록 없음(부록 A M27).
* 게이트 선행: B28 병합, G1 병합.
* 문서 개정 커밋 시점(검토 S4): 게이트 변경 card(G1)는 spec card와 그것이 개정하는 design 05·계획서 문구를 **같은 커밋(승인 전)**에 넣고, 승인 기록(`target_kind: diff`)의 `diff_path`가
  세 경로를 덮는다(B28 승인 `20260930-v3-history-clone`의 `diff_path` 두 줄 선례). 이 design의 UD-0 문서 개정도 design 커밋과 함께 승인 대상 diff에 든다.

### 9.2 사용자 결정(진짜 사용자 몫만)

| ID | 결정 | 기본안(원칙에서) | 왜 사용자 몫인가 |
|---|---|---|---|
| **UD-0** | 이 design 승인(DEC-51). §9.3 기본값과 문서 개정을 함께 덮는다: 계획 N3.10 표(A-3 계산 결과 -- `load_topology`·`validate_theta_declaration_order` 위치, `optimize_full_circuit_budget` Phase 3 위치 MOD8), N3.10 533행에 "V6·V7의 '새'도 같은 규칙"(G1 spec card와 같은 커밋), 534행 '추적 파일' 제외 집합(D-9), N3.12.3 test-only 열거에 "Phase 3 T0·T1", `00-common` §3.2 103행·§10.1 431행(D-5), `10-test-separation` §5.6 영역 표 '파일' 열을 설명으로(T0) | §9.3 | 계획서 표·판정 문구 개정은 승인 대상(0.5 공격 16) |
| **UD-1** | **U-03**: 추적 안 된 `workspaces` 스크립트가 shim 삭제로 깨지는 것을 허용 | 계획 기본안 그대로 -- 추적 파일은 전부 F1에서 갱신, 추적 안 된 1개(`smoke_run_harness_session18_save.py`)는 깨지게 둔다 | 계획이 사용자 결정으로 지정(N7.2) |
| **UD-5** | **G1 게이트 변경 승인** + **이동 인식 방식의 비용 선택** | **(가) 전역 규칙**(G1 spec card 그대로) | 판정 기준(게이트) 변경은 사용자 승인(05 §18). 두 방식 모두 '약화 금지'를 만족하므로 비용 선택은 사용자 몫(검토 §3-2) |
| **UD-6** | **T0 V5 승인**(test 커밋 뒤 diff 해시로) | 판정 범위 확대 + 유일성 검사 추가, 기대값 불변, 죽은 상수 삭제 | 기준 변경 승인(DEC-40) |
| **UD-7** | **D군 probe·진단 스크립트 처리**(§7.2, 8파일) | F1에서 덮어쓰기 대상을 호출자 모듈 전부로 바꾸고 F1 oracle에 그 대입 줄만 예외 | probe 존치·기능 범위는 사용자 몫(검토 §3-5). 대안: 'Phase 3 뒤 동작하지 않는 probe'로 표시만 |

**UD-5 비용 비교**(권고 (가)):

| | (가) 전역 이동 인식 규칙 | (나) 승인 기록에 선언된 이동만 인정 |
|---|---|---|
| 막는 것 | M-0~M-4·골격 규칙이 거부하는 부류(부록 A G5 거부 13단계). 규칙 밖의 새 부류가 나오면 규칙을 고쳐야 한다 | 선언 밖 이동은 전부 '새 정의'. 선언 안에서는 여전히 M-0~M-4가 필요(선언된 from→to라도 덮어쓰기·재바인딩은 막아야 하므로) |
| 비용 | 게이트 변경 1회(G1). card마다 추가 승인 없음 | 게이트 변경 1회 + M card 8개마다 승인 기록 1건(+ 선언 형식·대조 코드) |
| 이중 대조 | Phase 3 안에서는 이미 `move_plan check`의 `move-set`이 이동 집합을 **이관표(D0b 승인 결과)**와 대조한다 -- 선언이 이관표로 존재한다 | 이관표와 승인 선언이 같은 내용을 두 번 적는다 |
| Phase 3 밖 | 이동이 규칙대로면 어느 card에서든 인정(측정 근거: 거짓 거부 0, 반례 전부 거부) | 선언 없는 이동은 불인정(보수적) |

권고 근거: (나)가 더 막는 것은 '규칙을 통과하는 이동이 Phase 3 밖에서 계획 없이 일어나는 것'뿐이고, 그 경우에도 옮긴 단위는 바이트·전역 출처가 같아 동작이 같다(M-4). 선언의 역할은
Phase 3에서 이관표 + `move-set`이 이미 한다. 추가 승인 8건은 원칙('결정은 원칙으로 기본안부터')에 비해 이득이 없다.

뒤에 올 같은 성격의 승인(지금 결정할 것 아님): T1·F1의 V5 승인(test 파일 이동·import 문자열).

### 9.3 원칙 유도 기본값(UD-0으로 확정 -- 따로 묻지 않는다)

| ID | 기본값 | 근거 |
|---|---|---|
| D-1 | 평면 배치. B11(`extract_selftest.py:645` 비재귀 glob)은 LAYOUT-FLAT로 해당 없음 | N3.10 표 파일 이름이 경로 없는 이름 |
| D-2 | `topology_library.py`·`design_report.py`도 재수출 shim 경유 뒤 F2 삭제, `stick_diagram` 재수출은 임시 | 파일당 한 책임, WP-14 |
| D-3 | `optimize_full_circuit_budget` → Phase 3 위치 MOD8(통째) | A-3 계산, `00-common` 435행 |
| D-4 | 쪼개라고 적힌 16행은 통째로(A-3), 쪼개기는 원래 담당 Phase | 533행 이동 전용 |
| D-5 | M10 시그니처 `(spec, *, topology_path, search, output_dir)`, 나머지 인자는 CC-7·CC-8. `00-common` 431행에 `topology_path` 추가, 103행 담당 정정 | `run_harness.py:427·446` |
| D-6 | `canonical_spec`/`SPECS`/`_spec_*`는 하네스에 남김(레지스트리 392~395행 목적지 정정) | 계획 532행 |
| D-7 | `move_plan.py`는 `tools/migrate/`(code-author), test는 `A/tests/tooling/`(test-author) | 계획 N3.11 549행 |
| D-8 | `audit_current_forced.py`는 도구로 남기고 `audit_topology`는 A-4대로 | 레지스트리 248·389행 |
| D-9 | GONE-SHIM 제외 집합 = `.ai/verification/**`(판정 기록 스크립트 6개 -- 기록된 base 커밋에서 재실행되는 증거) + `docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`(기준 커밋 78b58c6 실측 원자료) | 기록 불변 |
| D-10 | 레지스트리 §7 `보류(Phase 3)` 9행은 **옮기고 D 유지**, 처리 열 `보류(Phase 4)` | U-02 승인 `20260923-u02-d-list` 1항 |
| D-11 | N3.10 표 개정은 A-3 계산 결과를 그대로 | §6.2 |
| D-12 | T0 = A군 3파일만, B군은 F1 | 최소 수정 |
| D-13 | G1은 B28 병합 뒤 base, 해시·이름 해석 정의는 `reachability` 하나 | §5.3, 정의 하나 |
| D-14 | references 문서의 모듈 위치 안내는 F2에서 grep 목록만 보고, 갱신은 B22 별도 card | B22가 이미 그 card |
| D-15 | M10은 red-green | §2.3 인벤토리 실측(이름 과대 근사뿐) |
| D-16 | M card는 `tools/**` 변경 0, 판정 도구는 D0a 병합 커밋 사본 | 작성자≠검증자(검토 S9) |

---

## 10. DoD 측정 명령 (N9.2-6)

auditor가 Phase 3 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT`는 `10-test-separation` §10 정의를 그대로 쓴다. `$PY` = `C:/Python314/python.exe -B`. `MP_ARGS`는 §6.3.
`MP` = D0a 판정 기록의 `code_commit`에서 꺼낸 사본: `git -C <iso> show <D0a code_commit>:tools/migrate/move_plan.py > <S>/move_plan.py`(`<S>` = auditor 스크래치). `CARDS` = M1~M6·M8·M9
판정 기록(`.ai/verification/<M id>.json`)의 (`base_commit`, `code_commit`, MOD 파일) 목록.

| ID | N6.2 `3` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | MOD1~MOD10 존재 | `$PY <iso>/tools/gates/import_layering.py --root <iso>` 출력 `present` | `present`가 N3.10 표 10행 전부(표는 도구가 계획서에서 읽는다) |
| E1 | import 계층 위반 0 | 같은 명령 | exit 0, `findings` 0 |
| E2 | 이동 커밋마다 AST 해시 동일 | `CARDS`의 (b, h, m)마다 ① `$PY <iso>/tools/gates/mutate_changed.py --root <iso> --base b --head h --pytest-ini <캐시>/pytest_gate.ini > <S>/v3_m.json` ② `$PY <S>/move_plan.py check --root <iso> --base b --head h --card m $MP_ARGS > <S>/chk_m.json` | ① exit 0, JSON `defs` = `[]`, `mutants` = 0, `move_rejected` = `{}` ② exit 0, `findings`의 모든 목록 비어 있음(`move-set`·`move-rejected`·`changed`·`lost`·`order`·`shim`·`cache`) ③ ①의 `moved`(`to`→`from`) = ②의 `moved_defs`(`moved_defs`의 두 호출이 같은 입력에서 같은 결과), ②의 `moved_units` 목적지 집합 = ②의 `assigned`. `targets`(파일 목록)는 기준이 아니다(검토 B5). G1이 `defs`·`moved`를 더한다 -- B28 뒤 출력 키가 바뀌면 이 행을 다시 잰다(§5.3-4) |
| E3 | `sizing_recipe.py` 삭제 | `git -C <iso> cat-file -e HEAD:skills/analog-gmid-design/assets/sizing_recipe.py`(실패해야 함) + `git -C <iso> grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|topology_library\|design_report)\b" -- '*.py'` + `git -C <iso> grep -l -E 'import_module\("(sizing_recipe\|topology_library\|design_report)"\|_import\("(sizing_recipe\|topology_library\|design_report)"' -- '*.py'` | 첫 명령 exit ≠ 0, 둘째·셋째 결과 ⊆ D-9 제외 집합 |
| E4 | 레지스트리 목적지 = 실제 위치 | `PT <iso>/skills/analog-gmid-design/assets/tests/contracts/test_p3_registry_dest.py`(D0b) + `$PY <S>/move_plan.py plan --root <iso> $MP_ARGS` | test PASS, 도구 exit 0, `reg_mismatch`·`unassigned`·`upward`·`cycles`·`conflicts` 0, `absent_split` = `[sizing_recipe.py, topology_library.py, design_report.py]`, `stick_diagram.py`·`audit_current_forced.py` 밖 단위의 `rule` 전부 `A-0` |
| E5 | 동작 보존(N6.3) | `PT` 전체 + E-LIB·E-INST 재측정 | Phase 2 DoD와 같은 해시 |
| E6 | 정의 보존(MOVE-TOTAL) | `$PY <S>/move_plan.py check --root <iso> --base <Phase 3 첫 card base> --head HEAD --card ALL $MP_ARGS --allow-changed workspaces/run_harness.py::run skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline` | exit 0(모든 발견 목록 비어 있음). `shim`은 F2 뒤 shim 파일이 없어 해당 없음 |

---

## 11. 열린 질문 (N9.2-8)

없다. §9.2의 UD는 착수 전 사용자 결정 대기 항목이다. 이 초안이 드러낸 **계획·문서 개정 요청**(UD-0에 포함):

1. 레지스트리 목적지 열이 N3.10 이전 판 이름을 쓴다(§6.1) -- 517행 "레지스트리 열이 정본"은 D0b 재생성 뒤에 성립한다.
2. N3.10 533행의 이동 제외가 V3에만 적혀 있다 -- V6·V7도 같은 규칙이어야 이동 card가 판정 가능하다(§5.1). '옮긴 단위'의 정의는 이 design §3(G1 spec card 계약 0~3)을 인용한다.
3. N3.12.3 test-only 열거에 Phase 3 T0·T1이 없다.
4. 534행 '추적 파일 전부 갱신'과 판정 기록 불변(D-9)의 충돌.
5. `00-common` §3.2 103행과 §10.1 431행의 MOD10 인자 담당, 431행 시그니처에 topology 경로 인자가 없음(D-5).
6. 백로그 후보(§5.4): 같은 경로 import 재바인딩, 클래스 수준 문장이 V3·V6에 보이지 않음, V7 그래프의 `__init__`·레지스트리 값 간선.

---

## 부록 A. 측정 명령과 결과 (모두 읽기 전용, gate `master` `cd64170`)

`R` = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `D` = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts`, `$PY` = `C:/Python314/python.exe -B`. v1·v2 스크립트는 초안 v2 부록 A대로.
v3 스크립트는 `D/p3v3_g1_measure.py`(합성 저장소는 `C:/g29` 아래에 만들고 단계마다 지움)와 `D/p3v3_facts.py`.

| # | 명령 | 결과 |
|---|---|---|
| M0 | `ls R/docs/02-design/features/ \| grep gain` | 00·05·10·20 네 개(30 없음) |
| M1 | `sed -n 985,1020p R/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` | 1000행 Phase 3 행, 1018행 DoD |
| M2 | `git -C R log --oneline 070cf69..cd64170` | 8커밋 -- 엔진 변경은 `ed98d35`(DF-36)뿐 |
| M6 | `wc -l R/skills/analog-gmid-design/assets/*.py`; `$PY p3_measure.py` `toplevel_counts` | SR 12015줄(Class 13·Func 174·Assign 30), SD 9035줄(Class 28·Func 132·Assign 8), TL 7, DR 5+1 |
| M9~M15 | 초안 v2 부록 A와 같음(독립 검토가 cd64170에서 재실행해 일치) | §6.1 |
| M18 | `grep -n "^\s*global "`; `grep -n lru_cache R/…/topology_library.py`; `sed -n '2391p;2530p;7697p' R/…/sizing_recipe.py`; 캐시 사용 함수 AST 스캔(이 절 명령과 같은 세션의 `$PY -c`) | `global` 0 / `lru_cache` 데코레이터 1곳(248행, 254행은 주석 -- **v2 '2곳' 정정**) / 주석 대입 캐시 3개, 사용 함수 각 1(`knee_L_for_kind`·`feasible_L_window`·`achievable_metric_bound`) |
| M19~M20 | 초안 v2와 같음 | §5.1, `import_layering`은 표 밖 파일 import를 보지 않는다 |
| M22 | `git -C R grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|stick_diagram\|design_report\|topology_library)\b" cd64170 -- '*.py'` | §7.2(86개) |
| M23 | `git -C R status --porcelain -- workspaces` | 추적 안 된 `.py` 1개 |
| M24 | `git -C R grep -c -E "(sizing_recipe\|stick_diagram\|topology_library\|design_report\|audit_current_forced)\.py" -- A/tests ':!A/tests/probes'` + 파일별 문맥 | §7.1 A·B·C 군 |
| M25 | `grep -n "tools/gates\|CLASS_GLOBS\|GATE_CODE_PREFIX" R/tools/gates/role_paths.py` | `tools/**` = tool, `GATE_CODE_PREFIX = "tools/gates/"`(23행) |
| M27 | `ls R/.ai/approvals \| grep -i -E "u03\|u-03\|30-module\|phase3\|p3-"` | 0건 |
| G1 | `$PY D/p3v2_g1_measure.py`(초안 v2) | 대상 def 473, 변이 15,677, V6 새 항목 861(부록 v2 G1 그대로) |
| G2 | 같은 실행 | 엔진 def 473 중 미도달 109(면제 1 → 108) |
| G4 | `git -C R grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` | 게이트 밖 호출 **3곳**(스크립트 3개: `mut_def.py:67`, `probe_t2_vs_1st_survivor.py:16`, `v3_baseline_probe.py:17` -- **v2 '4곳' 정정**) |
| G5 | `$PY D/p3v3_g1_measure.py` → `p3v3_g1_results.json` `counterexamples`(27단계: 각 단계 합성 git 저장소에서 base `mutate_changed.py`·`source_lint.py`·`reachability.py`를 실제 실행, v3 규칙은 같은 파일의 참조 구현으로 모의) | §5.2 표와 G1 spec card 계약 12 표. 인정 9단계 base 1/1/1 → v3 0/0/0, 거부 단계 base = v3, `overwrite`·`swap` V7 0/0, `cache-split` 0/1/0, `record-class-*` 0/0/0, `same-path-rebind(observation)` 0/0/0 |
| G6 | 같은 실행 `real_rename_same_dir`·`classes`·`multi_bound_names` | 엔진 4파일 통째 이동 모의: 단위 218/218·169/169·8/8·7/7, def 272/272·181/181·12/12·8/8, 거부 0, 호출당 5.8~9.2초. 클래스 SR 13(dataclass 8·예외 3·메서드 없음 10·클래스 수준 문장 8), SD 28(dataclass 28·메서드 없음 26). 최상위 중복 바인딩 0 |
| G7 | 같은 실행 `noop` | 판정 기록 `df36`(070cf69→ed98d35)·`dup-w-calc`(b7d1798→a9de49c): `units`·`defs`·`rejected` 모두 빈 결과 |
| V3 | `$PY D/p3v3_facts.py` `B5_v3_output_keys`; `git -C R show role/code/20260930-v3-history-clone:tools/gates/mutate_changed.py \| grep -n 'json.dumps({"tool"\|changed_defs(\|cat-file'` | HEAD 출력 키 `tool, verdict, targets, mutants, killed, survivors`(ERROR `tool, verdict, error`), B28 판 같음 + ERROR `baseline_failed`. B28 판 줄: cat-file 359, `changed_defs` 364, 출력 398·402·407. `targets` = `diff --name-only`의 소스 `.py` 경로 목록(277행) |
| V4 | `$PY -c` 스키마 조회 `.ai/verification/_schema.json` `$defs.check` | 판정 기록의 `checks.V3` = `{verdict, basis}`(자유 문장) -- E2가 기록이 아니라 도구 재실행 JSON을 읽는 이유 |
| S5 | `$PY D/p3v3_facts.py` `n310_header`·`n310_rep_tokens`·`mod_table` | 머리 `ID, 파일, 책임, 대표 대상`. 토큰: 식별자 41(MOD1 5·MOD2 5·MOD3 9·MOD4 7·MOD5 5·MOD6 6·MOD8 3·MOD9 1), `<파일>.py` 1(MOD4), 점 이름 1(MOD9), 무시 2(MOD1 `∂ID/∂VSB`, MOD10 `workspaces/`), MOD7 0 |
| S6 | 같은 실행 `S6_nested_refs` | 중첩 def·메서드 안에서만 다른 최상위 이름 참조: SR 17, SD 4 |
| S7 | 같은 실행 `future_annotations` | `from __future__ import annotations` SR 35행, SD 32행 |
| S11 | 같은 실행 `S11_attr_overrides`(`git grep -n -E "^\s*(sr\|sd\|sizing_recipe\|stick_diagram\|topology_library\|design_report\|tl\|dr)\.[A-Za-z_]+\s*=[^=]" -- '*.py'`) | 12줄 8파일(§7.2 D군) |
| S12 | 같은 실행 `S12_run_inventory` + 파일별 집계·`run`의 직접 호출자 | 60 test(`test_extract_selftest.py` 24, `test_selftest_sizing_recipe.py` 22, `test_probe_parasitic_pm_all_circuits.py` 5, …), 직접 호출자 12 = `_run_combo`·`_run`·`base_blob_text`·spice `run` 등 이름 과대 근사 |
| S13 | `git -C R grep -n _SIZING_RECIPE -- .` | `test_ts6_dead_probes.py` 60·221·222·261·262뿐 |
| m6 | 같은 실행 `m6_scan_names` | T0 spec card 계약 9 목록 |
| m7 | 같은 실행 `m7_string_imports` | 10곳(모두 `A/tests/contracts`) |
| H | `git -C R rev-parse --short HEAD`, `git -C R rev-parse --short gate/master`, `git -C R log --oneline -1 role/code/20260930-v3-history-clone` | `cd64170`, `cd64170`, `dee338d`(B28 code, 미병합) |
| P | `PYTHONPATH=R/tools/gates $PY -c "role_paths.parse_spec_card(...)"` 세 초안 | G1·T0·D0a 머리 파싱 성공(절 11개씩) |

측정 한계: M14는 초안 배정 기준·`ast.Name` 참조만. G1은 '파일 전체가 새 파일'인 상한. G5·G6의 v3 결과는 **참조 구현 모의**다(게이트 도구 자체는 바뀌지 않았다) -- G1 card의 red-green이 실제
판정이다. G6은 '같은 디렉터리 통째 이동'이라 실제 card의 부분 이동과 다르다(부분 이동의 거짓 거부는 M-4 고정점에서 '함께 옮겨야 할 것을 안 옮긴' 경우뿐이고 그것은 PLAN-LAYER·
`move-set`이 먼저 잡는다).

## 부록 B. 초안 v1(`draft_phase3_design.md`, 070cf69) 대비 정정

초안 v2 부록 B 그대로(12항목: A군 3파일, D-9, D-10, UD-4 흡수, 도구 하나, PLAN-LAYER 정밀 해석, M-1~M-3, B28 편집 지점, card 15, E0, D-5 근거, 줄 수).

## 부록 C. 초안 v2 대비 정정(검토 `review_phase3_drafts.md` 반영 -- 발견별 대응표는 `phase3_revision_log.md`)

| # | v2 | v3 |
|---|---|---|
| 1 | MOVED = M-1~M-3 | M-0(덮어쓰기)·M-4(전역 출처, `__file__`)·클래스 골격 단위·문장 해시 식별 추가(B1·B2·B3·S3·m8). 반례 27단계 재실행(G5), 실제 엔진 거짓 거부 0(G6) |
| 2 | D0a `plan`의 Phase 중·후 동작 미정 | A-0 현재 위치, `absent_split`, `reg_mismatch`(REG-DEST) -- D0b test·E4가 Phase 전 구간에서 성립(B4) |
| 3 | E2 = V3 `targets`의 def 0 | V3 재실행 JSON `defs` = []·`mutants` = 0·`move_rejected` 비어 있음 + `check` 발견 0 + `moved` 대조(B5) |
| 4 | design·D0a CLI 불일치 | D0a 계약 1이 정본, design은 요약·`MP_ARGS`(B6·m3) |
| 5 | 판정식 CACHE-ID·SHIM·MOVE-TOTAL 도구 없음 | `check`의 `cache`·`shim`(정적 출처 동일성), E6 `--card ALL`(S10) |
| 6 | M10 equivalence, 판정 결정 미룸 | 인벤토리 실측(이름 과대 근사뿐) → red-green(S12, D-15) |
| 7 | probe 속성 덮어쓰기 미기재 | §7.2 D군 8파일, F8, UD-7(S11) |
| 8 | M card 판정 도구 = 병합본 `tools/migrate` | D0a 병합 커밋 사본, M card `tools/**` 변경 0(S9, D-16) |
| 9 | 문서 개정 커밋 시점 불명 | spec card와 같은 커밋(승인 전), `diff_path` 세 경로(S4) |
| 10 | `lru_cache` 2곳, 게이트 밖 호출 4곳 | 1곳(248행), 3곳(m1·m2) |
| 11 | E3 줄 머리 import만 | 문자열 import 패턴 추가(m7) |
| 12 | UD-5 게이트 승인만 | 전역 규칙 대 선언 이동의 비용 비교와 권고 추가 |
