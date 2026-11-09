# gain-budget-gmid-sizing -- Phase 3 `30-module-split` design

> **[초안 v5 -- 저장소 미반영]** 정식 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`(현재 없음).
> 측정 시점 = gate `master` `7535799`(2026-09-30, **B28 병합 `2b41e79`·판정 기록 `8790b24` 뒤**). 엔진·계획서·design 00/05/10/20의 인용 줄은 v3 측정 시점 `cd64170` 이후 불변
> (`git diff --stat cd64170 HEAD`는 tools·P9 spec·design 20 E4뿐) -- 줄 번호가 바뀐 것은 `tools/gates/mutate_changed.py`(B28)와 redteam뿐이다. 측정은 읽기 전용, 스크래치 `C:/g51`(끝나면 삭제).
> v5는 v4 뒤 확정된 결정·card를 반영한다(2026-10-01, HEAD는 여전히 `7535799`): 사용자 결정 **A2**(B26-1·B34를 Phase 3 전에 병합, 승인 기록 `20260930-b26-before-phase3`),
> **A1-a·A1-b**(V3 면제 묶기 `20260930-v3-exempt-binding`, V3 범위 정책 N2 + 넓힌 T6 `20260930-v3-changed-stmt-scope`), B33(`20260930-v7-registry-edges`)가 G1보다 먼저 병합된다는 순서와
> redteam 번호(G1 32, B33 33, 면제 묶기 34, 범위 정책 35). 그 card들이 바꿀 사실은 **초안에서 추정해 '§9.1 재측정 조건'으로 표시**했다(병합 전이라 잴 수 없다 -- 추정치를 판정 근거로 쓰지 않는다).
> 측정 명령·결과는 부록 A, v1→v2 정정은 부록 B, v2→v3 정정은 부록 C, v3→v4 정정은 부록 D, v4→v5 정정은 부록 E(발견별 대응은 `phase3_revision_log.md`).
> **재측정 조건(Phase 3 시작 때 -- 상세는 §9.1)**: (1) P9·P10·**B34·B26-1**(엔진 변경 card)이 병합되면 엔진 줄 인용(`sizing_recipe.py:2391·2530·7697`, `stick_diagram.py:1050·8973`,
> `run_harness.py:422·427·446`)과 부록 A M6·M9~M15·M18·M22·M24·G6'·S6·S7·S11·S13·m6·m7을 그 병합본에서 다시 잰다(2차 검토 S8, §6.4). (2) B33·면제 묶기·범위 정책(게이트 card)이 병합되면
> §5.1·G1 card '작성 전 실측'의 `tools/gates` 줄 번호·출력 키와 부록 A G2·G5'(base 열)를 그 병합본에서 다시 잰다(§5.5).

버전 v0.5(초안). 정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05-role-separation`·`20-dead-code-dup`의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 표 `30-module-split` 행): N3.10, N6.1·N6.2 Phase 3, U-03. 추가로 읽은 절: N3.11(test 배치), N3.12.2(역할 경로), N3.12.3(card 단위·판정 유형), N4.2 V2·V3·V6·V7, N8,
WP-01·WP-03·WP-11·WP-14, NFR-2.

실측 원자료: `p3_measure.py`·`p3_assign.py`·`p3_refs.py`(초안 v1), `p3v2_g1_measure.py`(v2), `p3v3_g1_measure.py` → `p3v3_g1_results.json`(v3), `p3v3_facts.py` → `p3v3_facts.json`
(v3: N3.10 열·토큰, 중첩 참조, 인벤토리, 전수 스캔 이름, V3 출력 키), **`p3v4_g1_measure.py` → `p3v4_g1_results.json`**(v4: v3 규칙과 v4 규칙을 같은 입력에서 나란히 -- v3 27단계 +
2차 검토 새 반례 전부, 각 단계 합성 저장소에서 HEAD 게이트 도구 3개 실제 실행, D0a `check` 발견 모의, 실제 엔진 통째 이동 거짓 거부, 판정 기록 무동작).
참조 구현은 design 문장이 판정 가능한지 확인하는 초안 측정이다 -- G1 구현이나 test 기대값의 근거가 아니다(작성자≠검증자).
정식 문서로 올릴 때 원자료는 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/`에 둔다(20-dead-code-dup 선례).

---

## 1. 범위 (N9.2-1)

계획 N6.1 Phase 3 행(1000행)이 정본이다: "10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03". 이 Phase가 구현하는 것:

1. **게이트의 이동 인식**(G1): 계획 N3.10 533행 "해시가 같은 함수는 V3 대상에서 뺀다"가 도구에 없다(§5). 이동 card가 판정 가능하려면 먼저 필요하다. G1은 먼저 병합되는 게이트 card
   셋(B33 V7 그래프 간선, V3 면제 묶기, V3 범위 정책)과 합성된다(§5.5).
2. **계약 test 위치 독립화**(T0): 정의가 **특정 파일에 있다고 가정하는** 계약 test 3개가 첫 이동 card에서 깨지거나 공허해진다(§7.1).
3. **이관표**(D0a·D0b): 레지스트리 '이관 목적지' 열을 N3.10 10모듈 이름으로 재생성하고, 계층 규칙(import는 작은 번호로만, 순환 0)을 **옮기기 전에** 계산으로 만족시키는 단위→모듈 배정(§6).
4. **이동**(M1~M9, 모듈 하나당 card 하나 -- 계획 N3.12.3 674행)과 **MOD10 진입점**(M10).
5. **test 재배치**(T1): `unit/test_selftest_<모듈>.py` 4개 → `unit/test_mod*.py`(계획 N3.11 test 배치 541~543행, `10-test-separation` 187·413행).
6. **호출부 갱신과 shim 삭제**(F1·F2), 모듈 속성을 덮어써 계측하는 probe의 처리(§7.2 D군, D-17).
7. `00-common` §17 표가 넘긴 `optimize_full_circuit_budget` 목적지 불일치(MOD6 대 MOD8) 해소(§6 A-3, D-3).

범위 밖(명시): 함수 분할·추출(CC-7 θ 탐색부 추출은 Phase 4, `00-common` §10.1 435행), 이름 리터럴 교체(DF-23 → Phase 4/7a), D 함수 배선(Phase 4), 레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4), 광범위 except 정리(DF-37, Phase 4), V7 그래프 한계·Phase 3 밖의 같은 경로 import 재바인딩·클래스 수준 문장의 **게이트** 사각(§5.4 관찰 -- 백로그 후보; Phase 3 이동 card 안에서는 `move_plan check`의 `rebind`·`changed`가 닫는다).

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
* **정의 하나**: 이동 판정의 해시 정의는 `def_hash` 하나다(G1이 `reachability`로 옮기고 `mutate_changed`는 import -- 이름·시그니처 유지). 면제 묶기 card의 **묶기 해시**(docstring·데코레이터
  포함 def 원본의 `ast.dump` sha256)는 용도(면제 대조)가 다른 별개 정의다 -- G1은 그것을 읽거나 바꾸지 않고, 이동 판정에 쓰지 않는다(§5.5.3). '모듈 전역에서 읽는 이름'·'이름의 바인딩 출처'도
  `reachability.SourceIndex` 하나다. `move_plan.py`는 계층 표를 `import_layering.mod_table`, 대표 대상 열을 `role_paths.read_section_table`, 참조·이동·해시를 G1 이름으로 읽는다.
* **작성자≠검증자**: 도구의 test는 test-author가 interface card만 보고 합성 입력(oracle (a))으로 쓴다. 판정 수치는 auditor 판정 기록에서만 인용한다. 이동 card의 판정 도구(`move_plan.py`)는
  **`tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit`**(지금은 D0a)에서 꺼낸 사본을 쓴다(M card code-author가 같은 card에서 바꿀 수 없다 -- §8, 1차 검토 S9·2차 검토 m6).

---

## 3. 판정식 (N9.2-3)

숫자를 박지 않는다(WP-03). 모두 `영역: 없음(스키마)`. E-LIB·E-INST는 `20-dead-code-dup` §3 정의를 그대로 쓴다(재서술하지 않는다). '판정 도구' 열이 비지 않는 것만 판정식이다(만들면 배선).

**단위**: 소스 파일(`reachability._is_source`: `A/*.py`, `workspaces/run_harness.py`)의 최상위 **함수**(해시 `def_hash`), 최상위 **클래스 골격**(ClassDef에서 안의 모든 def를 이름 표지로
바꾼 사본의 `def_hash` -- 머리·데코레이터·클래스 수준 문장·메서드 이름과 순서 포함, 메서드 몸체 제외), 최상위 **문장**(import·def·class·`if __name__` 블록 밖, 문장 `ast.dump` 해시 --
문장은 해시로만 식별). **바인딩** = 모듈 공간(def·class·lambda·컴프리헨션 몸체 밖)에서 이름이 `Store`/`Del` 문맥이거나 import·def·class·`except … as`·`match` 포획·`type` 별칭으로
묶이는 모든 곳(증강 대입·walrus·`del` 포함 -- 2차 검토 S2). **바인딩 출처** `binding_origin(p, n)` = 모듈 p 최상위에서 n이 가리키는 정의를 `from … import` 사슬을 따라가 얻은
`("def", 파일, 이름)`(또는 `ext`·`ext-module`(**가져오는 파일의 디렉터리 포함**)·`module`·`builtin`·`unbound`·`multi`·`star`(**모듈에 star import가 하나라도 있으면 모든 이름**)·
`global-dynamic`(**모듈 어디서든 `global` 선언된 이름**, 경로 포함)·`cycle`·`file-dir`(`__file__`)·`module-identity`(`__name__` 등·`globals`/`eval`/`exec`) -- 2차 검토 S1).
**전역 읽기** `global_names(u)` = u와 그 안 모든 유효 범위에서 Python 유효 범위 규칙상 모듈 전역으로 해석되는 이름(문장 단위도 같은 규칙 -- lambda 인자·컴프리헨션 대상은 지역) ∪
데코레이터·기본값·기반·키워드의 이름 ∪ 주석(문자열 주석 포함)의 이름. 정확한 문언은 G1 spec card 계약 0~3.

| ID | 판정 | 식 | 판정 도구 |
|---|---|---|---|
| E-LIB / E-INST | 동작 보존 | `20-dead-code-dup` §3 | 그 정의의 측정 명령 |
| MOVED | 이동 인식(G1) | head 단위 u = (p_h, 키 q, 해시 h)가 **옮긴 단위** ⇔ (M-1) base에서 (종류, q, h)를 가진 소스 파일이 정확히 하나 p_b ≠ p_h(파일 안에서도 하나) (M-0) u가 바인딩하는 이름마다 base p_h의 바인딩 출처가 없거나 `("def", p_b, 이름)`(**덮어쓰기 거부**) (M-0h) u가 바인딩하는 이름마다 **head** p_h의 바인딩 출처 = `("def", p_h, 이름)` -- 목적 파일에서도 u가 그 이름의 유일한 바인딩(`multi`·`star`·`global-dynamic`이면 거부: **목적 파일의 조건부 재정의·재바인딩 거부**, 2차 검토 B1 (1)의 M-0') (M-2) head p_b에 같은 단위가 없고 p_b에 남은 그 이름의 출처는 없거나 `("def", p_h, 이름)`(재수출뿐) (M-3) head에서 (종류, q, h)가 p_h 한 곳 (M-4) p_b와 p_h의 `__future__` 기능 집합이 같고(2차 검토 S3), `global_names(u)`의 이름마다 base p_b의 출처 = head p_h의 출처, 또는 head 출처가 함께 옮긴 단위이고 그 원본 출처가 base 출처(**재바인딩·`__file__`·import 디렉터리 변경·star 가림·`global` 쓰기 대상 거부**, 고정점). 메서드는 클래스 골격이 옮겨지고 자기 해시가 원본과 같을 때만 옮긴 def(**클래스 머리·필드 변경 거부**). **옮긴 def**(V3·V7 제외 목록)에는 p_b 또는 p_h에서 qualname이 둘 이상인 def를 넣지 않고(property getter/setter 등, 2차 검토 B1 (2)), V3·V7은 (경로, qualname, `def_hash`)가 모두 같을 때만 뺀다(B1 (3)) | `reachability.moved_defs`(V3·V6·V7이 부름) |
| MOVE-AST | 이동 동일성(533·1018행) | card k의 병합본에서 (a) 이 base→head에서 MOVED가 낸 **모든** 옮긴 단위 집합 = 이관표가 card k에 배정한 **최상위 단위**(함수·클래스·문장) 집합이고 목적지가 전부 card k의 MOD 파일(2차 검토 S4) (b) 옮긴 단위가 아닌데 해시가 바뀌었거나 새로 생긴 단위 0(클래스 골격·문장 포함 -- V3가 보지 않는 클래스 필드 기본값 변경도 여기서 잡힌다) + 옮긴 클래스 안 def의 해시가 원본과 다른 것 0(2차 검토 S6) (c) 사라진 단위 0 (d) MOVED가 거부한 후보 0 (e) 옮긴 단위·제자리 단위 모두 전역 읽기 출처가 base와 같음(옮긴 단위 사상 적용 -- import 줄 교체 거부, 2차 검토 S5) (f) 목적 파일 `__future__` ⊇ 원본(S3) (g) 옮긴 문장 단위의 원본 상대 순서 보존(m2) | `move_plan check`(`move-set`·`changed`·`lost`·`move-rejected`·`rebind`·`future`·`stmt-order`) + card마다 V3 JSON `defs` = `[]`(§8 M행, §10 E2) |
| MOVE-TOTAL | 정의 보존 | Phase 전 base와 Phase 후 병합본 사이에서 MOVE-AST (b)(c)(d)를 전 단위로: 바뀐·새·사라진 단위는 M10이 선언한 것(`run_harness.py::run`, `gmid_design_pipeline.py::run_gmid_design_pipeline`)뿐 | `move_plan check --card ALL --allow-changed …`(E6) |
| PLAN-LAYER | 이동 전 계층 사전 검사 | 이관표 σ에서, 단위 u의 참조 R(u)(`global_names`의 이름 중 출처가 split·MOD 파일의 정의인 것 + 그 파일 모듈 별칭 속성, 중첩 def·메서드 포함 -- 문자열·해석 못 한 이름 제외) u→v 중 σ(u) < σ(v)인 것 0, 모듈 순환 0 | `move_plan plan`(`upward`·`cycles`) |
| LAYER | 계층 | `import_layering.py --root <iso>` exit 0 | 그 도구 |
| ORDER | 중간 상태 | card k 병합본에서 새 MOD 파일의 import가 가리키는 트리 파일 ⊆ {번호가 작은 MOD}(잔여 split 파일 없음). `import_layering`은 표 밖 파일을 보지 않으므로 별도 | `move_plan check`(`order`) |
| SHIM | 재수출 정확성 | 재수출 shim에 docstring과 `from <MOD> import …` 밖 문장 0(def·class·대입·`import *` 0), 재수출 이름 집합 = (base 재수출) ∪ (이 card가 그 파일에서 옮긴 이름), 이름마다 shim의 바인딩 출처 = MOD의 바인딩 출처(출처가 같으면 import가 같은 객체를 묶는다 -- `getattr(shim, s) is getattr(MOD, s)`의 정적 형태. 실행 중 속성 덮어쓰기는 §7.2 D군), base에 있던 `if __name__ == "__main__"` 블록 불변(2차 검토 m3) | `move_plan check`(`shim`) |
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
| F5 | G1 병합 전 이동 card | 판정 불가(V3 변이 약 1.6만 개, V6 새 항목 861, V7 미도달 약 108 -- B33 병합 뒤에는 약 39로 줄 것으로 추정(B33 시제품, 소스 전체 기준), 그래도 0이 아니다 -- §5.1·§5.5.4) | G1 병합 전에는 M card를 시작하지 않는다(§8) |
| F6 | 계약 test가 첫 이동에서 깨지거나 공허해짐 | equivalence 불성립 | T0 병합 전에는 M card를 시작하지 않는다 |
| F7 | MOVED 거부(`move-rejected` M-0/M-0h/M-4) | 옮긴 단위가 아니라 V3 대상·`changed` | 배정을 따라 **함께 옮길 것을 함께** 옮기거나(재바인딩 대상이 이 card 배정이면) 새 MOD가 원본과 같은 출처에서 import하게 import 줄만 고친다(`from __future__ import annotations` 포함). 몸체를 고치지 않는다 |
| F8 | 모듈 속성 덮어쓰기 probe가 이동 뒤 계측을 잃음(§7.2 D군) | probe 결과가 조용히 비거나 달라짐(V1이 probe를 수집하지 않아 FAIL로 드러나지 않는다) | D-17대로 F1에서 덮어쓰기 대상을 호출자 모듈로 옮긴다 |

---

## 5. 게이트의 이동 인식 (G1)

### 5.1 실측: 지금 게이트는 옮긴 정의를 새 정의로 본다

| 도구 | '새/바뀐 def'를 정하는 곳(`7535799`, B28 병합 뒤) | 옮긴 정의에 대한 결과 |
|---|---|---|
| V3 `mutate_changed.py` | `changed_defs(base_src, head_src)`(88~100행, `_strip_doc` 74·`def_hash` 84)이 **같은 경로**의 base 소스와만 비교. `main`이 `git cat-file -e <base>:<path>`(359행)로 base 파일이 없으면 `base_src = None`(361행) → 그 파일의 def 전부가 대상(`changed_defs` 호출 364행). diff는 `--no-renames --diff-filter=AM`(314행). test 실행 환경은 B28의 `make_clone`(53행 정의, 323행 호출 -- 옛 `copytree` 없음), 정리 `_rmtree_force`(406행), 출력 398·402(ERROR)·407(PASS/FAIL) | 엔진 4파일을 새 파일로 옮기면 대상 def 473개·변이 15,677개(부록 A G1). 인벤토리 없는 def는 변이 전부 '생존' |
| V6 `source_lint.py` | `compare(path, base_src, head_src, kd)`(212행)가 같은 경로 base와 단위별 항목 수 비교, base 없으면 전부 '새 항목' | 새 파일로 옮기면 새 항목: magic_number 500·continue 347·broad_except 8·id_call 6(부록 A G1) |
| V7 `reachability.py` | `base_defs` = base의 (파일, qualname) 집합(224~229행), `new_defs` = head 노드 중 그 집합에 없는 것(230~231행) | 지금 운영 루트로 도달하지 못하는 엔진 def 109개(승인 면제 1) -- 옮기면 전부 '새 def 미도달'로 FAIL(부록 A G2) |

**v5 주의(재측정 대상)**: 위 줄 번호는 `7535799`의 값이다. G1 전에 병합되는 게이트 card 셋이 이 세 파일을 바꾼다 -- 면제 묶기·범위 정책은 `mutate_changed.py`의 `main`(면제 대조 375행 근처, 대상 선택
364행 근처, 출력 407행), B33은 `reachability.py`의 `build_graph`(97행~)와 `main`의 도달 계산(223·230행 근처, R3 소스 범위). V7 '미도달 109'는 B33 뒤 줄어든다(B33 시제품: 소스 전체 기준 미도달
115 → 39 -- `draft_b33.spec.md` '작성 전 실측' 1, 판정 기록 수치 아님). 옮긴 def를 새 def로 보는 결함 자체는 B33과 무관하게 남는다(B33은 '무엇이 도달하는가', G1은 '무엇이 새 def인가'). G1 card는
이 줄 번호와 수치를 그 병합본에서 다시 잰다(G1 card '작성 전 실측' 1).

합성 저장소 red 실측(부록 A G5 `move-exact`): def 하나를 바이트 그대로 새 파일로 옮기고 원래 파일은 재수출만 남긴 커밋에서 base V3·V6·V7 모두 exit 1.

**계획 원문**(N3.10 533행): "무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. **해시가 같은 함수는 V3 대상에서 뺀다.**" -- V3 행(N4.2 839행)도 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것"이고 경로를 말하지 않는다. V6(842행)·V7(843행)은 이동을 말하지 않는다.

### 5.2 고칠 방향

* **판정식은 그대로, 비교 기준만 옮긴다**: 옮긴 단위(§3 MOVED)는 비교 기준이 '같은 경로의 base'에서 '이동 원본'으로 바뀐다.
  * V3: 옮긴 def는 대상이 아니다 -- (경로, qualname, `def_hash`)가 모두 맞을 때만 뺀다(2차 검토 B1 (3)). 옮기며 한 토큰이라도 바뀐 def, 거부된 후보(M-0·M-0h·M-1~M-4)의 def,
    qualname이 겹치는 def(B1 (2))는 지금처럼 대상. 대상이 된 def 안의 변이 선택은 범위 정책 card(N2)의 규칙 그대로이고, 새 경로에서 base 같은 경로에 같은 qualname이 없으면 '새 def'(본문 전체)다
    -- 이동 원본과 문장 단위로 맞추지 않는다(D-20, §5.5.2).
  * V6: 옮긴 def 단위의 '이전 항목 수'는 원본 단위를 원본 파일 맥락에서 센 값. 옮긴 문장은 새 파일 `<module>` 단위의 이전 항목 수에 원본 맥락 값(그 문장 줄 범위)으로 더해진다.
    **새 파일 맥락에서 항목이 늘면 FAIL**(부록 A G5 `cache-split`: 캐시 dict만 옮기고 `len()` 검사를 원래 파일에 남기면 `unbounded_cache` -- 옮긴 문장이라도 걸린다).
  * V7: 옮긴 def는 '새 def'가 아니다(V3와 같은 (경로, qualname, `def_hash`) 대조).
* **약화하지 않는다 -- 반례 재실행**(부록 A G5·G5', base 도구는 **HEAD `7535799`의 실제 도구**를 단계마다 합성 git 저장소에서 실행, v3·v4 규칙은 같은 입력에서 참조 구현 모의).
  초안 v2 규칙(M-1~M-3)이 통과시키던 1차 검토 반례 3종은 v3에서, v3 규칙(M-0~M-4)이 통과시키던 **2차 검토 반례 7종**은 v4에서 모두 거부된다. v3 규칙으로 잰 27단계 결과는 초안 v3 측정
  (`p3v3_g1_results.json`)과 27/27 같고(회귀 없음), v4 규칙은 그 27단계의 exit를 하나도 바꾸지 않는다.

  | 단계 | 무엇을 막나 | 규칙 | base V3/V6/V7 | v3 규칙 | v4 규칙 |
  |---|---|---|---|---|---|
  | `overwrite` | 목적 파일의 같은 이름 정의(다른 본문)를 옮긴 본문으로 덮음 -- 호출자 동작이 바뀜(1차 B1) | M-0 | 1/1/0 | 1/1/0 | 1/1/0 |
  | `overwrite-import` | 목적 파일이 base에서 같은 이름을 다른 모듈에서 import | M-0 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `swap` | 두 파일 def 교환 | M-0 | 1/1/0 | 1/1/0 | 1/1/0 |
  | `rebind` | 옮긴 def가 읽는 `helper`를 목적 파일이 다른 정의에 묶음(1차 B2) | M-4 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `file-dir-change-noshim` | `__file__`을 읽는 def를 다른 디렉터리 소스 파일로 | M-4 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `class-header-changed` / `class-field-changed` | 클래스 기반·필드를 바꾸며 메서드 이동(1차 B3) | 골격 해시 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `copy`·`wrapper`·`ambiguous`·`two-targets`·`move-edited` | 초안 v2부터 거부 | M-2·M-2·M-1·M-3·해시 | 1/1/1 | 1/1/1 | 1/1/1 |
  | `N1` 목적 파일 조건부 재정의(원본 재수출 없음) | `if FLAG: def f(x): return -x`가 옮긴 f 뒤에서 이름을 가로챔(2차 B1) | M-0h | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N2` 목적 파일 def 없는 재바인딩 | `f = (lambda g: …)(f)` | M-0h | 1/1/1 | **0/0/0** | 1/1/1 |
  | `S2` 증강 대입·`except … as` 재바인딩 | 계약 문언이 def·class·대입·`for`/`with`만이면 뚫림(2차 S2) | M-0h | 1/1/1 | 1/1/1·**0/1/0** | 1/1/1 |
  | `P` 옮긴 클래스의 property getter 변경 | 골격 같음, `P.x` 키가 setter 해시로 제외돼 getter 변경이 V3에서 빠짐(2차 B1) | qualname 중복 제외 | 1/0/1 | **0/0/0** | 1/0/1 |
  | `N3b` star import가 함께 옮긴 helper를 가림 | 명시 바인딩 뒤의 `from c import *`(2차 S1 (c)) | M-0h | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N4` `global`로 쓰이는 X를 읽는 g만 이동 | base·head 모두 `unbound`라 같다고 봄(2차 S1 (a)) | M-4 | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N13` 같은 import 줄, 다른 디렉터리 | `A/`의 `from wsutil import h` → `workspaces/`(2차 S1 (b)) | M-4 | 1/1/1 | **0/0/0** | 1/1/1 |
  | `N5` 목적 파일에 `from __future__ import annotations` 누락 | 주석 문자열 → 평가값(2차 S3) | M-4 | 0/0/0 | 0/0/0(인정) | 0/0/0(**거부**, 관찰) |

  인정 9단계(red → green): `move-exact`, `absorb-own-import`(목적 파일이 base에서 원본을 import하던 경우), `move-with-helper-import`(새 파일이 원본 모듈에서 helper를 import -- 출처가 같아
  G1은 인정, Phase 3에서는 `move_plan check` `order`가 잔여 split import로 거부), `move-together`, `move-chain`(앞 card에서 옮긴 이름을 새 MOD가 그 MOD에서 import),
  `local-shadow`(지역 이름이 원본 최상위 이름과 같음 -- 유효 범위 규칙으로 전역 아님), `file-same-dir`, `class-exact`, `cache-together` -- 모두 base 1/1/1 → v3·v4 0/0/0. 추가 인정
  `N5ok`(future 줄을 가진 목적 파일)·`N6ok`(문장 순서 보존)도 v4에서 인정. **알려진 보수 비용**: `P-property-exact`(바이트 그대로 옮긴 property 클래스)는 qualname 중복 제외 때문에
  v4에서 V3/V7 1(base와 같음) -- 엔진 4파일 qualname 중복 0이라 Phase 3 노출 0.
* **2차 검토 새 반례 22건 전부 거부**(부록 A G5' `adversarial_summary`): G1이 19건(주체 def가 V3·V7 대상으로 남거나 `move_rejected`), `move_plan check` 발견만으로 3건 --
  `same-path-rebind`·`S5-inplace-rebind-in-move-card`(제자리 단위의 import 교체 → `rebind`), `N6`(옮긴 문장 순서 교환 → `stmt-order`). G1이 잡은 19건 중 N5·N7·P·N1 등은 `check`도 함께
  잡는다(`future`·`changed` def 단위·`changed`/`lost`). 2차 검토 §3 표의 N8a·N8b·N9a·N9b·N10·N11·N12는 v3에서도 거부였고 v4에서도 거부.
* **거짓 거부 측정**(부록 A G6'): 실제 엔진 4파일 각각을 같은 디렉터리 새 파일로 통째 옮기고 원래 파일은 명시 재수출만 남긴 모의에서 **v4 규칙으로** 옮긴 단위 402/402(SR 218·SD 169·TL 8·DR 7),
  옮긴 def 473/473, 거부 0(M-0h 위반 0, qualname 중복 제외 0), `move_plan check` 발견 모의 0(`changed`·`lost`·def 단위 `changed`·`stmt-order`·`future`·`rebind` 모두 0 -- 트리 전체 단위의
  `rebind` 대조 포함). `stick_diagram`의 `__file__` 사용 2곳(1050·8973행)도 같은 디렉터리라 인정. 참조 구현 한 호출 7.9~15.6초(전체 소스 두 벌 색인 -- v3 측정 5.8~9.2초와 같은 규모,
  기계 부하 차), `check` 모의 1.3~2.4초.
* **관찰 가능**: 세 도구의 판정 JSON에 `moved`(`[{"from", "to"}]`)와 `move_rejected`를 더하고, V3에는 변이 대상 def 목록 `defs`를 더한다(§10 E2가 `targets`가 아니라 이것을 잰다 -- 검토 B5).
  먼저 병합된 card가 더한 키(범위 정책 `not_targeted`·`targets_by_def`, 면제 묶기 `exempt_ignored`·`survivor_bindings`, B28 `baseline_failed`)는 이름·뜻을 그대로 둔다(§5.5).
* **기존 이름·시그니처 유지**: `mutate_changed.changed_defs(base_src, head_src)`·`def_hash(fn)`은 기존 판정 기록 스크립트 3곳이 부른다(부록 A G4). 해시 정의는 `reachability`로 옮기고
  `mutate_changed`는 그것을 import해 같은 이름으로 둔다(`mutate_changed`가 `reachability`를 import하므로 반대 방향이면 순환 -- 정의 하나).
* **비용 선택(UD-5)**: 이 절의 방식은 **전역 이동 인식 규칙**이다. 대안은 '승인 기록에 선언된 이동 목록(from→to)만 인정'이다. 비교와 권고는 §9.2 UD-5.

### 5.3 B28(`20260930-v3-history-clone`)과의 합성 -- B28 병합 완료

B28은 병합됐다(code `dee338d` → 병합 `2b41e79`, 판정 기록 `8790b24` -- 지금 gate `master` = `7535799`). B28은 `mutate_changed.main`의 **test 실행 환경**(copytree → `make_clone`
격리 복제본(53·323행), 기준 실행 실패 → `ERROR`(398행, `baseline_failed`), 임시 디렉터리 정리 `_rmtree_force`(406행))을 바꿨다. G1은 **대상 선택**(`changed_defs` 호출 364행 앞 이동
제외)과 판정 JSON 필드 추가만 바꾼다. 출력 키는 병합본에서도 `tool, verdict, targets, mutants, killed, survivors`(PASS/FAIL 407행, ERROR는 `tool, verdict, error` + `baseline_failed`)
-- **E2 기준은 영향 없음**(2차 검토 S8 재측정). `lib/rt.py`에 B28이 `vcase` 선택 관찰(`tool_tmpdir`·`root_state`, 599~621행)을 더했다. 합성 규칙:

1. G1의 test worktree는 **B33·면제 묶기·범위 정책이 병합된 뒤의 gate `master`**에서 만든다(05 §12 순서 1, §5.5.1). G1 spec card의 '작성 전 실측' 줄 번호는 `7535799`에서 잰 값이다 --
   그 세 card가 `tools/gates`를 바꾸므로 G1 착수 때 반드시 다시 잰다.
2. G1의 무동작 입력에 B28의 redteam `attacks/31-v3-git-history/` 세 단계를 넣는다(결과 불변).
3. G1은 B28의 계약(격리 복제본·`ERROR`·임시 디렉터리 무누수)을 건드리지 않는다. G1이 새로 여는 git 호출은 base 트리 읽기(`ls-tree`·`show`)뿐이다.
4. §10 E2는 G1이 더하는 `defs`·`moved`와 공통 키 `mutants`를 읽는다 -- 출력 키가 다시 바뀌면 E2 명령을 다시 잰다(의존 명시).
5. **redteam 번호 배정**(D-18, v5 개정): 마지막 번호 `31-v3-git-history`(B28). 오케스트레이터 배정 = **G1 `32-moved-defs`, B33 `33-…`, 면제 묶기 `34-…`, 범위 정책 `35-…`**
   (디렉터리 이름 꼬리는 각 card의 것: B33 `33-v7-registry-edges`, 면제 묶기 `34-v3-exempt-binding`, 범위 정책 `35-v3-changed-scope`). 병합 순서(33·34·35가 32보다 먼저 들어간다)와
   무관하게 번호를 미리 나눈다. v4의 `33-v7-graph-edges`는 B33 card가 정한 꼬리 `v7-registry-edges`로 바꿨다. 지금 세 card 초안은 각각 32·32·33을 적고 있다(`draft_b33.spec.md`
   `attacks/32-v7-registry-edges`, `draft_v3_exempt_binding.spec.md` `32-v3-exempt-binding`, `draft_v3_scope_policy.spec.md` `33-v3-changed-scope`) -- 그 card들의 개정 몫이다(이 design은
   고치지 않는다, `phase3_revision_log.md` v5 절 인계). G1 card '작성 전 실측' 2는 `ls attacks`에 33·34·35가 있고 32가 비었는지 확인한다.

### 5.4 관찰(범위 밖, 백로그 후보)

* V7 그래프는 클래스 인스턴스화에서 `__init__`로, 모듈 최상위 레지스트리 dict에서 값 함수로 가는 간선이 없어 `SemiEmpiricalGmIdLUT.__init__`·`_feed_*` 같은 def를 미도달로 센다(부록 A G2).
  **v5: B33(`20260930-v7-registry-edges`)이 G1 전에 병합되어 닫는다**(R1 레지스트리 바인딩·R2 생성자·R3 소스 범위). G1과의 합성은 §5.5.4.
* **같은 경로 import 재바인딩**: `a.py`의 `from c import helper`를 `from d import helper`로 바꾸면 V3·V6·V7 모두 exit 0이다(부록 A G5 `same-path-rebind(observation)` -- def가 바뀌지 않았으므로).
  G1의 M-4는 **옮긴** def에 대해 이 사각을 막지만 같은 경로 변경에는 관여하지 않는다(약화도 강화도 아님). **Phase 3 이동 card 안에서는** `move_plan check`의 `rebind`(head의 모든 단위의
  전역 읽기 출처 = base 출처, 옮긴 단위 사상 적용 -- 2차 검토 S5)가 닫는다(부록 A G5' `same-path-rebind`·`S5-inplace-rebind-in-move-card` → `rebind` 발견). Phase 3 밖 card의 같은 경로
  import 교체는 여전히 게이트 사각이다(백로그 후보).
* **클래스 수준 문장**: V6 `_units`는 클래스 몸체의 리터럴을 어느 단위에도 넣지 않고 V3는 def만 보므로 dataclass 필드 기본값 변경은 세 도구 모두 보지 않는다(부록 A G5
  `record-class-default-changed` base·v3 모두 0/0/0). 이동 card에서는 `move_plan check`의 `changed`(클래스 골격 해시)가 잡는다.
* **옮긴 클래스 안 메서드 본문 변경**: 골격 해시는 메서드 몸체를 빼므로 클래스 단위는 '옮김'이다. V3는 그 메서드를 대상으로 잡지만(해시가 원본과 달라 옮긴 def가 아님) 인벤토리 test가
  변이를 죽이면 V3 PASS다 -- 그래서 M card 판정은 **card마다** V3 JSON `defs` = `[]`을 요구하고(§8 M행), `check` `changed`가 옮긴 클래스 안 def 해시까지 본다(2차 검토 S6).

### 5.5 먼저 병합되는 게이트 card와의 합성(v5)

#### 5.5.1 순서와 base

사용자 결정 A1-a·A1-b(`_drafts/user_decisions.md`, 2026-10-01)와 B33 card의 권고 순서로 G1 앞에 게이트 card 셋이 병합된다. 셋 다 `tools/gates`를 바꾸고 G1도 같은 파일을 바꾸므로 **나중에
병합하는 G1이 합성 문장을 가진다**(범위 정책 card '결정 필요 항목'이 정한 규칙 -- "나중에 병합하는 card가 문장을 고친다").

| card | 바꾸는 파일·동작 | G1과의 관계 |
|---|---|---|
| B33 `20260930-v7-registry-edges`(redteam 33) | `reachability.py` `build_graph`(R1 레지스트리 바인딩·R2 생성자 간선)와 `main`의 도달 계산(R3 소스 범위). V3 인벤토리도 같은 그래프 | 판정 효과 독립(B33 = 무엇이 도달하는가, G1 = 무엇이 새 def인가). 같은 파일 -- §5.5.4 |
| 면제 묶기 `20260930-v3-exempt-binding`(redteam 34) | `mutate_changed.py` `main`의 면제 대조(원소 `<변이 id>@<묶기 해시>`), 출력 `exempt_ignored`·`survivor_bindings`, `--out`에 exempt 기록 | 옮긴 def의 면제 -- §5.5.3 |
| 범위 정책 `20260930-v3-changed-stmt-scope`(redteam 35) | `mutate_changed.py` 대상 선택(해시가 바뀐 기존 def는 바뀐 문장·감싸는 제어문·삭제 지점·넓힌 T6·바뀐 매개변수·`early_return`, 새 def는 전체), 출력 `not_targeted`·`targets_by_def`, 데코레이터 변이 적용 | 옮긴 def 제외와 N2 -- §5.5.2 |

G1 base = 이 셋이 병합된 gate `master`. 셋 사이의 순서는 G1에 영향이 없다(면제 묶기는 A1-a대로 B26-1 전, 범위 정책은 B26-1의 V3 비용 근거라 B26-1 전, B33은 G1 전 어느 때든).

#### 5.5.2 V3 대상: 옮긴 def 제외와 N2

* **먼저 제외, 그다음 N2**: G1의 옮긴 def((경로, qualname, `def_hash`) 일치 -- §3 MOVED)는 V3 대상 def가 아니다. 변이를 만들지 않으므로 `not_targeted`에도 `targets_by_def`에도 들지 않는다
  (실행하지 않은 변이가 아니라 대상 def가 아니다). 범위 정책 계약 3의 G1 읽기("옮긴 def는 대상 아님")와 같다.
* **나머지 def**에는 범위 정책 계약 1이 그대로 적용된다: base **같은 경로**에 같은 qualname이 있고 해시가 다르면 문장 단위 대상(T1~T6, 넓힌 T6 포함), 없으면 새 def 본문 전체.
* **D-20 -- 옮기며 바뀐 def·거부된 이동 후보는 새 경로의 '새 def'(본문 전체)다.** 이동 원본과 문장 단위로 맞추지 않는다. 근거: (1) 범위 정책 승인(A1-b, 약화 승인)이 덮는 것은 '같은 경로의 해시가
  바뀐 기존 def'뿐이다 -- 원본을 경로 밖에서 찾아 문장 단위로 좁히는 것은 승인 범위 밖의 추가 약화다. (2) Phase 3에서는 옮기며 본문을 바꾸는 것 자체가 F2(card 되돌림)이고 M card는
  `defs` = `[]`을 요구하므로 좁힐 이유가 없다. (3) 거부 후보(M-0·M-0h·M-4 등)는 '이동으로 인정할 수 없다'는 판정이므로 원본과 맞추는 것은 그 판정을 무르는 것이다.
* 범위 정책 계약 2(해시가 바뀐 기존 def마다 대상 ≥ 1)는 옮긴 def에 걸리지 않는다 -- 옮긴 def는 '해시가 바뀐 기존 def'가 아니다(이동 원본과 해시가 같다).
* G1 redteam 29단계의 V3 exit는 범위 정책 뒤에도 바뀌지 않을 것으로 본다: 합성 저장소에 test가 없어 대상 변이가 하나라도 있으면 전부 생존(exit 1)이고, 대상이 0인 경우는 '옮긴 def만 있음'뿐이다
  (새 def는 본문 전체, 해시가 바뀐 기존 def는 `early_return` 항상). G1 card '작성 전 실측'에서 병합본 도구로 base 열을 다시 잰다.

#### 5.5.3 면제 묶기와 옮긴 def

* 변이 id = `<모듈>:<qualname>:<연산자>:<경로>`이고 `<모듈>` = 파일 줄기(`reachability.module_name` 47행, `mutate_changed.py` 362·374행 -- 부록 A E2). 그래서 **def를 옮기면 그 def 변이 id의 모듈
  부분이 바뀐다**. 묶기 해시(docstring 포함 def 원본)는 바이트 그대로 옮기면 같다.
* 옮긴 def(G1 인정): V3 대상이 아니어서 변이 id가 만들어지지 않는다 → 면제 대조 자체가 없다. 옛 경로 id의 원소는 '이번 실행의 변이 id'와 같지 않아 `exempt_ignored`에도 실리지 않는다(면제 묶기 계약 3).
* 거부된 이동 후보(본문은 같지만 M-0h·M-4 등으로 대상): 새 모듈 이름의 id로 변이된다. 옛 모듈 이름 id의 원소는 **적용되지 않는다**(fail-closed, 누수 아님). 면제가 필요하면 `<새 모듈>:…@<묶기 해시>`로
  다시 승인한다(묶기 해시는 바이트가 같으면 옛 승인 값과 같다). Phase 3에서는 거부 후보가 곧 F7(배정을 고치거나 import 줄만 고친다)이라 면제로 넘기는 경로가 아니다.
* 이동 뒤 card가 옮긴 def를 바꾸면 묶기 해시가 바뀌어 어떤 옛 원소도 맞지 않는다 -- 모듈 부분과 무관하게 면제 묶기 card 계약 2의 동작.
* 결론: G1은 면제 대조를 바꾸지 않는다(**D-21**). 이동 때문에 면제가 다른 문장으로 새는 경로는 없다(id가 바뀌면 적용 안 됨, 해시가 바뀌면 적용 안 됨). 지금 HEAD의 V3 모양 원소 14개
  (`20260922-ic3-v3-exempt`: `load_topology` 10·`save_instance_json` 4)는 해시가 없어 면제 묶기 병합 뒤 이미 적용되지 않는다.

#### 5.5.4 B33(V7 그래프)과 G1

* G1의 V7 변경은 `new_defs`에서 옮긴 def를 빼는 것뿐이고 `build_graph`·도달 계산을 바꾸지 않는다 -- B33의 R1~R3와 그 card의 그래프 계약(초안 계약 9 간선 단조성 -- 검토 `review_b33.md` B1·S5로 dunder 속성 폴백 제거에 맞춰 고쳐질 예정, 최종 문언은 B33 card)이 G1 뒤에도 그대로다. G1 card의 무동작 입력에
  B33 redteam `33-v7-registry-edges` 전 단계를 넣는다.
* B33 바인딩 노드(`<파일>::=<이름>`)는 def가 아니다(B33 계약 7) -- G1 `moved_defs`의 `defs`·V7 `new_defs` 제외 대상에 나오지 않는다. 옮긴 **문장** 단위(레지스트리 dict 대입)는 새 파일의 바인딩
  노드가 되고, 소비자가 shim(`from <MOD> import _REG`)을 거쳐 읽어도 B33 R1의 재수출 해석이 값 함수로 잇는다(B33 단계 `registry-reexport`. 초안 문언은 "M에 바인딩이 없으면 같은 이름의 바인딩"이고 검토 `review_b33.md` S3·B2가 "M의 import 문을 따라감(chase)"으로 고치길 권했다 -- Phase 3 중간 상태에서 옛·새 모듈에 같은 이름이 잠시 공존하는 모양이 바로 S3의 반례라 chase 판이 맞다. 최종 문언은 B33 card).
  그래서 Phase 3 중간 상태에서 레지스트리 값 함수가 미도달로 바뀌지 않는다 -- 옮긴 def는 어차피 V7 대상이 아니고, 이 성질은 이동과 같은 card에서 생긴 **새** def(예: M10 진입점)의 도달 판정에 쓰인다.
* B33 R3(도달은 `_is_source` 노드 안에서만)와 G1 `moved_defs` 입력(소스 파일만, `_is_source`)은 같은 소스 분류를 쓴다 -- 새 MOD 파일(`A/*.py`)은 둘 모두에서 소스다.
* B33은 V3 인벤토리를 키운다(사전 실측 쌍 33,991 → 79,809). G1은 인벤토리를 바꾸지 않는다. M card의 V3는 `defs` = `[]`이라 인벤토리 비용이 없다.
* §4 F5·§5.1의 'V7 미도달 약 108'은 B33 뒤 값으로 G1 card에서 다시 잰다(시제품 추정 약 39).

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

실제 저장소 인자(§10과 M card가 쓴다). **bash 배열**로 두고 `"${MP_ARGS[@]}"`로 넘긴다 -- 문자열 변수 `$MP_ARGS` 전개는 따옴표를 다시 해석하지 않아 `--aliases`의 JSON이 공백에서
쪼개지고 D0a 계약 1대로 exit 2가 된다(2차 검토 B2: `printf '[%s]\n' $MP_ARGS` → `['{"optimizer":]`, `["theta_search.py"}']`). `--aliases`의 CLI 모양(JSON)은 D0a 정본 그대로 둔다.

```bash
MP_ARGS=(--plan docs/01-plan/features/gain-budget-gmid-sizing.plan.md
         --registry docs/03-analysis/gain-budget-gmid-sizing.function-registry.md
         --split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
         --keep audit_current_forced.py
         --aliases '{"optimizer": "theta_search.py"}')
printf '[%s]\n' "${MP_ARGS[@]}" | tail -1   # 확인: [{"optimizer": "theta_search.py"}] 한 줄
```

### 6.4 B26-1·B34(A2 -- Phase 3 전 병합)가 바꾸는 단위와 배정(v5)

사용자 결정 A2(승인 기록 `20260930-b26-before-phase3`, decision): B26-1(`20260930-b26-rail-accessor-set`)과 B34(`20260930-b34-grammar-explicit`)는 Phase 2 진행 중(순서 P9 → B34 → B26-1)에
병합되고 **Phase 3 M card보다 먼저**다. 그 기록의 '재검토' 절: 둘 중 병합되지 않은 card가 있는 채 M card가 `stick_diagram`·`sizing_recipe`를 나누기 시작하면 그 card의 앞당김은 효력을 잃고
편집 범위를 새 모듈 기준으로 다시 잰다 -- 그래서 §9.1 착수 조건에 'M1 전 두 card 병합'을 둔다.

두 card 초안(`_drafts/draft_b26_1.spec.md`, `draft_b34.spec.md`)에서 **추정한** Phase 3 영향(병합 전이라 잴 수 없다 -- 전부 'Phase 3 시작 때 재측정', D0b가 실제 값으로 확정):

| 항목 | v4 값(`7535799`) | B26-1·B34 뒤 추정 | 근거(초안) |
|---|---|---|---|
| SD 최상위 정의 | Class 28·Func 132 | Class 29·Func 133(`RailDeclaration` frozen dataclass, `rail_declaration`) | B26-1 '신규 시그니처'. 지우는 def 0(B26-1 '작성 전 실측' 마지막, B34 범위 2·3) |
| 엔진 단위·def(G6' 통째 이동 모의) | 단위 402(SD 169)·def 473(SD 181) | 단위 404(SD 171)·def 474(SD 182) | 위 두 정의. `RailDeclaration`은 메서드 없는 dataclass(def 0) |
| 엔진 클래스(A-2 입력) | 41(dataclass 36·메서드 없음 36·예외 3) | 42(dataclass 37·메서드 없음 37·예외 3) | 같음 |
| 레지스트리에 행이 없는 최상위 정의(M12) | SD 24 | SD 26 | B26-1 계약 11은 §2(개념 정본)·§6 문장만 고친다 -- 함수 행 추가 없음 |
| 바뀌는 def | -- | B34: `_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`. B26-1: 판정·통과 사이트 SD 18·SR 2(`true_current_mirror_groups`·`resolve_stack_layout`)에 키워드 전용 `rails: RailDeclaration`, `load_topology`·`l_sharing_classes`·`_metric_kcl_residual` 등 본문 | B34 사이트 표, B26-1 계약 4·5·6 |
| SD 줄 이동 | `__file__` 1050·8973, future 32행 | B34 코드만으로 1073 이후 4줄 당김(B26-1 초안 '순서' 절) + B34 docstring 수정분 + B26-1 접근자·클래스 추가분. 1050(`_import_analog_grammar` 안 `_ag_path`)은 B34가 그 def를 바꾸므로 근처에서 다시 잰다 | B26-1 의도 '순서' |
| SR 캐시 줄 | 2391·2530·7697 | B26-1이 SR 2191~2230·4200대·6470대·8000대 본문을 바꿔 몇 줄 밀릴 수 있다 | B26-1 계약 4·6 |
| `run_harness.py:422·427·446`, `topology_library.py:248` | -- | 바뀌지 않을 것으로 봄(두 card 모두 편집 목록에 없음) -- 확인만 | 두 card '바꾸는 것' 표 |
| 계약 test(§7.1) | contracts 3개가 엔진 모듈 import(M22) | `tests/contracts/test_b34_grammar_explicit.py`(B군 -- `stick_diagram.<이름>(…)` 직접 호출), `tests/contracts/test_b26_rail_accessor.py`(**A군 후보** -- 계수 래퍼가 `stick_diagram.rail_declaration` 모듈 속성을 바꿈, B군 -- `sizing_recipe._metric_kcl_residual` 이름 호출) | §7.1 v5 행, T0 계약 10 |

**배정(D-19)**: `rail_declaration`은 topology 선언 `supply_nets`의 형식을 검사하고 `ValueError`로 거부하는 접근자다 -- N3.10 MOD2 책임 "topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트"에
해당한다. 규칙만 적용하면 행이 없는 정의라 A-5(소비자 따라)로 **MOD3**(유일한 운영 호출자 `load_topology`가 A-3로 MOD3 -- B26-1 계약 3·4: SR은 `meta["rails"]`로만 받고 접근자를 부르지 않는다)에
간다. 책임과 어긋나므로 **N3.10 MOD2 '대표 대상'에 `rail_declaration`을 더해 A-1로 MOD2에 둔다**(UD-0 문서 개정, §9.2). 계층: `load_topology`(MOD3) → `rail_declaration`(MOD2)은 작은 번호
쪽이라 허용, `rail_declaration`의 참조는 `RailDeclaration`·내장뿐. `RailDeclaration`은 A-2(레코드 하강): 참조하는 단위 중 가장 낮은 번호 -- `rail_declaration`(MOD2)과 `rails: RailDeclaration`
주석을 단 MOD2 구조 제안 함수(`refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill` 등, 레지스트리 목적지 `topology_authoring`)가 있으므로 MOD2(주석이 없어도 `rail_declaration`
때문에 MOD2). 이렇게 두면 MOD2 함수의 주석이 MOD3를 가리키는 위쪽 참조(PLAN-LAYER 위반)가 생기지 않는다.
* **B37a 접근자(`port_declaration`·`PortDeclaration`)**: B37a는 Phase 3 뒤 card라 이 design의 이관표 단위가 아니다. B37a 초안이 적은 위치("`rail_declaration` 옆", "접근자는 `ports`를 읽는 MOD2 쪽")는
  D-19와 같은 MOD2(`topology_authoring.py`)다 -- B37a card 커밋 때 오케스트레이터가 모듈 이름을 적는다.
* `_import_analog_grammar`(B34가 바꾸는 def): 레지스트리 행이 있으면 A-4, 없으면 A-5로 가장 낮은 소비자(구조 제안·유도 함수 -- MOD2 또는 MOD3)로 간다. `__file__`을 읽지만 MOD 파일이 `A/` 평면이라
  `file-dir` 출처가 같아 G1 M-4가 인정한다(§5.2 `file-same-dir`). B34 계약 3의 탐색 경로 `os.path.dirname(stick_diagram.__file__)`도 `stick_diagram.py`가 MOD7로 남고 같은 디렉터리라 그대로 성립한다.
  B34 범위 1 "지연 import 유지 -- 레이아웃 전용 모듈이 analog-grammar 없이 import"는 이동이 바이트 그대로라 보존된다(E-LIB와 별도로 M card가 확인할 필요 없음 -- 모듈 최상위 문장이 바뀌지 않는다).

**D0b 재측정 조건**: D0b의 이관표·`reg_mismatch`·PLAN-LAYER 수치는 **B26-1·B34가 병합된 master에서 처음 계산한다**. 그 전에 D0a 합성 test 밖에서 실제 저장소로 돌린 `plan` 출력(D0a 계약 8 (a) 포함)은
참고 관찰일 뿐 이관표가 아니다. D0b 착수 때 위 표의 추정 행을 전부 실측으로 바꾸고, 다르면 이 절을 사실 문장 갱신으로 고친다(규칙은 줄 번호·개수에 기대지 않는다).

---

## 7. 계약 test와 호출부

### 7.1 위치에 묶인 계약 test(실측 cd64170, 부록 A M24)

`A/tests/contracts/`에서 엔진 파일·모듈 이름을 **실제 트리 판정에** 쓰는 곳(합성 소스 문자열 안의 `import sizing_recipe`는 입력이라 제외):

| 군 | 깨지는 시점 | test(줄) | 처리 |
|---|---|---|---|
| **A. 정의가 특정 파일에 있다고 가정** | 그 정의를 옮기는 첫 M card | `test_ic5.py:47-69`(`_DOMAIN_TABLE` 키 = (파일 이름, 함수) 21개), `test_dup_w_calc.py:442`(`size_transistor` 정의를 `sizing_recipe.py`에서 찾음 → M4에서 FAIL), `test_ts6_dead_probes.py:221-222`(`_L_ROLE_MULTIPLIERS` 바인딩 검사 범위가 `sizing_recipe.py` 한 파일 -- 옮긴 뒤 **조용히 공허**), `:261-262`(`audit_vsb_consistency`의 운영 호출자를 `sizing_recipe.py`에서만 찾음) | **T0**(M1 전) |
| **B. 모듈 이름으로 import·파일 존재 앵커** | shim 삭제(F2) 또는 호출부 갱신(F1) | `test_d_delete_dead.py:74·98-101·201·286·295`, `test_d_delete_telescopic.py:108-117·155·233`, `test_d_move_tests.py:69·73`, `test_dup_w_calc.py:56·72-75`, `test_df35_harness_paths.py:206`, `test_ts6_probe_relocate.py:528`, `test_ts6_dead_probes.py:229`, `test_restore_plan_functions.py:54·113-140`, `test_ic3.py:107·271`, `test_df36_instance_relpath.py:76·87·237·274·288` | **F1** |
| **C. test 파일 이름 목록** | T1 | `test_ts3_no_print_verdicts.py:29-30` `_LEGACY_SCRIPTS` | **T1** |
| **A(v5, B26-1 병합 뒤 생김)** | M3(D-19: `rail_declaration`은 M2에서 MOD2로 가도 SD 재수출을 `load_topology`가 SD 전역으로 읽어 계수가 유지되고, `load_topology`가 M3에서 MOD3로 가면 깨진다) | `test_b26_rail_accessor.py`(B26-1 계약 3 계수 test -- `stick_diagram.rail_declaration` **모듈 속성**을 래퍼로 바꿔 호출 수를 센다. 호출자 `load_topology`가 자기 모듈 전역에서 이름을 읽으므로, 둘 중 하나라도 다른 파일로 가면 shim 속성 교체가 호출을 가로채지 못해 0회 → FAIL) | **T0**(계약 10, B26-1 병합 뒤 실측) |
| **B(v5, B26-1·B34 병합 뒤 생김)** | F1 | `test_b34_grammar_explicit.py`(`stick_diagram.<이름>(…)` 직접 호출 -- V3 인벤토리 조건이라 F1도 `<MOD>.<이름>(…)` 속성 호출 모양을 유지), `test_b26_rail_accessor.py`(`sizing_recipe._metric_kcl_residual` 이름 호출) | **F1** |

A군만 T0에 둔다(최소 수정). v5 A군 행은 V1이 수집하는 계약 test라 §7.2 D군(V1 밖 probe -- 조용히 빈다)과 달리 첫 이동 card에서 **FAIL**로 드러나 equivalence를 깬다(F6) -- 그래서 F1이 아니라
T0다(D-12 그대로: 위치 가정은 T0, 모듈 이름 import는 F1). B군은 shim이 살아 있는 동안 통과하고, 계획 534행이 '추적 파일 호출부 갱신'을 shim 삭제 조건으로 적었으므로 F1이 import를 목적 모듈로 바꾼다. 스캔 범위가
이미 `A/*.py` 전체인 판정(`_engine_files()` glob, GONE 검사)은 새 MOD 파일을 자동으로 포함하므로 고치지 않는다. T0는 `test_ts6_dead_probes.py`의 모듈 상수 `_SIZING_RECIPE`(소비자가
바꾸는 두 test뿐)도 지운다(부록 A S13 -- 초안 v2의 "229행이 계속 쓴다"는 틀렸다).

**T0의 해석 규칙 R-DEF**: 이름 n의 정의 파일 = `A/*.py`(하위 디렉터리 제외)와 `workspaces/run_harness.py` 중 최상위(메서드는 `Class.method`)에서 n을 def·class·대입으로 **바인딩**하는
파일(AST, import로 받은 이름은 정의가 아니다 -- shim 재수출은 정의가 아님). 정의 파일이 정확히 하나가 아니면 FAIL(0 = 공허, 2 이상 = 모호·사본). 이 규칙은 **판정 범위를 넓힌다**.
T0의 새 줄이 피해야 할 전수 스캔 토큰 목록은 T0 spec card 계약 9(부록 A m6).

### 7.2 추적 호출부(F1 대상, 실측 cd64170, 부록 A M22)

엔진 4모듈을 줄 머리 `import`/`from`으로 가져오는 추적 `.py` 86개: `A/` 루트 4, `A/tests/unit` 10, `A/tests/probes` 27, `A/tests/contracts` 3, `A/tests/tools` 2, `A/tests/conftest.py` 1(conftest 변경은 V5 무조건 승인 대상), `workspaces/run_harness.py` 1, `workspaces/current-reuse-telescopic-ota-report/**` 27, `workspaces/two-stage-ota-report/**` 4, `.ai/verification/**/scripts` 6, `docs/03-analysis/**` 1. **문자열 import** 10곳(`importlib.import_module("sizing_recipe")`·`_import("sizing_recipe")` -- 전부 B군 계약 test, 부록 A m7). 추적 안 된 `workspaces/*.py` 1개(`smoke_run_harness_session18_save.py`).

**D군 -- 모듈 속성 덮어쓰기**(부록 A S11): 엔진 모듈 속성에 대입해 계측·차단하는 추적 파일 8개(대입 **14줄** -- probe 12 + workspaces 2, `p3v3_facts.json` `S11_attr_overrides`; v3 '12줄'은 오기, 2차 검토 m1): probe 6개(`probe_b22_headroom_attribution.py:104·116`,
`probe_diode_gmid_readiness.py:63`, `probe_diode_pass_skips.py:94`, `probe_diode_window_corner.py:100·108`, `probe_matching_pair_divergence.py:124`, `probe_vds_assignment_paths.py:47·53·62·73·79`)와
`workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20`. unit·contracts·conftest·엔진·하네스에는 0. S11 패턴은 **대입문**만 센다 --
`setattr(`·`monkeypatch.setattr(` 형태는 HEAD `7535799`에서 `git grep -n setattr -- '*.py'` 0건이라 v4 결론은 그대로다(부록 A E3). B26-1이 그 형태를 contracts에 처음 들인다(위 §7.1 v5 A군 행 --
V1 수집 test라 T0). Phase 3 시작 때 S11을 대입문과 `setattr` 두 형태로 다시 잰다. 분할 뒤 호출자는 **자기 모듈 전역**에서
이름을 읽으므로 shim이나 정의 모듈의 속성을 바꿔도 다른 모듈의 호출자는 가로채지 못한다 -- probe는 V1이 수집하지 않아 계측이 **조용히** 빈다(F8). 처리 = **D-17**(F1에서 덮어쓰기 대상을 `binding_origin`으로 찾은 **호출자 모듈 전부**로 바꾸고, F1 oracle의 'import 줄 외 동일'에 이 대입 줄만
예외로 둔다 -- probe 기능을 보존하므로 삭제·범위 축소가 아니다. 초안 v3의 UD-7을 2차 검토 §5 권고대로 UD-0에 흡수, 대안 '동작 안 하는 probe로 표시'는 사용자가 원할 때만).

---

## 8. 역할별 산출물 -- spec card 목록 (N9.2-5)

card 단위는 N3.12.3(674행: 이동은 모듈 하나가 한 건). 판정 유형은 **커밋 모양이 정한다**(code 커밋이 없으면 test-only, 있으면 red-green 또는 equivalence -- `20-dead-code-dup` §8 P2·P7 정정).

| # | id(초안) | 대상 | 판정 유형 | oracle | 원칙 제약 |
|---|---|---|---|---|---|
| **G1** | `p3-gate-move-aware` | `tools/gates/reachability.py`(`SourceIndex`·`moved_defs`·해시 정의), `mutate_changed.py`(V3 대상 선택·`defs`·`moved`), `source_lint.py`(V6 비교 기준), redteam 새 케이스, design 05 §10 V3·V6·V7 행·계획 533행 문구(spec card와 같은 커밋) | red-green, `gate_change: yes`, phase 0.5(05 §18) | (a) 합성 저장소 29단계(red 7, 거부 22 -- 2차 검토 새 부류 9단계 포함), redteam `attacks/32-moved-defs/`(D-18), 규칙 이름은 `observe: "moved"` 관찰로 대조 | 약화 금지(M-0·M-0h·M-1~M-4·골격·qualname 중복 제외·(경로, qualname, 해시) 대조), `moved`·`move_rejected`·`defs` 출력, 해시·이름 해석 정의 하나, 실행당 색인 1회. base = **B33·면제 묶기·범위 정책 병합 뒤** master(§5.5): 대상이 된 def 안 변이 선택은 범위 정책 그대로, 옮기며 바뀐 def·거부 후보는 새 def(D-20), 면제 대조 불변(D-21), `build_graph` 불변. 무동작에 redteam 33·34·35 |
| **T0** | `p3-tests-location-free` | §7.1 A군 3파일을 R-DEF로, `_SIZING_RECIPE` 삭제, **v5: B26-1 계수 test의 래퍼 대상을 R-DEF 정의 파일 + 그 이름을 import로 바인딩하는 엔진 파일 전부로**(B26-1 병합 뒤) | **test-only** + V5 승인 | (c) base 트리 결과 동일 + (a) 합성 이동 트리에서도 PASS(옛 test는 FAIL) | 판정 범위를 좁히지 않는다, 정의 파일 유일성, 전수 스캔 토큰 회피 |
| **D0a** | `p3-move-plan-tool` | 새 `tools/migrate/move_plan.py`(`plan`·`check` -- `move-set`(모든 옮긴 단위)·`changed`(옮긴 클래스 안 def 포함)·`rebind`·`future`·`stmt-order`·`shim`(main 블록 포함)) | red-green | (a) 합성 저장소(이동 card를 차례로 적용한 커밋들·shim 삭제 커밋 포함) | CLI 정본(셸은 bash 배열), A-0으로 Phase 전 구간 동작, G1 뒤 base |
| **D0b** | `p3-registry-dest` | 레지스트리 목적지 열 전 행 = MOD 이름 하나(+ 근거 규칙 열), §7 `보류(Phase 3)` 9행 처리 열 = `보류(Phase 4)`, N3.10 표 개정(A-3 결과), 새 계약 test `contracts/test_p3_registry_dest.py`(`move_plan plan` exit 0·`reg_mismatch` 0·`upward`·`cycles` 0) | red-green(base 열에서 `reg_mismatch`로 FAIL) | (d) 도구 출력 = 열. 동어반복 방지로 oracle을 둘로 나눈다: 규칙 손적용 합성 입력(도구 test와 별도 표본) + 실제 트리 drift guard(검토 §2 (3) V4) | 손으로 쓰지 않는다(도구 출력). N3.10 개정은 이 design 승인(D-11·D-19). **B26-1·B34 병합 뒤 master에서 처음 계산**(§6.4 재측정 조건) |
| **M1**~**M6**, **M8**, **M9** | `p3-move-mod<n>-<이름>` | 이관표 MODn 배정 전부(파일:줄은 D0b 뒤 도구 출력) | equivalence(test 커밋 0 가능 -- 05 §9.2 289행) | (c) MOVE-AST + E-LIB·E-INST + SHIM + CACHE-ID + ORDER(`check` 발견 0 -- `rebind`·`future`·`stmt-order`·옮긴 클래스 안 def `changed` 포함) + **card마다 V3 JSON `defs` = `[]`·`move_rejected` = `{}`·`not_targeted` = 0·`targets_by_def` = `{}`**(범위 정책 키 -- 옮긴 def는 대상 def가 아니므로 둘 다 비어야 한다, §5.5.2)(옮긴 클래스의 메서드 본문 변경은 인벤토리 test가 변이를 죽이면 V3 PASS라 `defs`로만 드러난다 -- 2차 검토 S6; DoD E2까지 미루지 않는다) | G1·T0·D0b 뒤. **`tools/**` 변경 0**(`git diff --name-only <base> <head> -- tools` 빈 출력). 판정 도구는 `tools/migrate/move_plan.py`를 **마지막으로 바꾼 판정 기록의 `code_commit`**에서 꺼낸 사본(`git show <그 code_commit>:tools/migrate/move_plan.py` -- 지금은 D0a; 1차 검토 S9·2차 검토 m6) -- code-author가 판정 도구를 같은 card에서 바꿀 수 없게. 목적 MOD 파일은 원본의 `from __future__` 줄을 가진다(F7) |
| **M7** | -- | `stick_diagram.py`에 레이아웃만 남았는지 -- 이동 없음 | M2·M3·M9에 흡수(빈 card 금지) | -- | -- |
| **M10** | `p3-mod10-entry` | 새 `gmid_design_pipeline.run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)`, 하네스 `run()`이 부른다 | **red-green**(새 test가 library 회로로 진입점을 불러 E-INST 해시 대조 -- base에 진입점 없음) | (c) E-INST·E-LIB + (a) ENTRY | 만들면 배선: 하네스 즉시 호출, `after_phase3` 루트. 지금 인벤토리는 이름 과대 근사뿐(§2.3) |
| **T1** | `p3-test-relocate` | `unit/test_selftest_*.py` 4개 → `unit/test_mod*.py`, C군, 새 C9 매핑 | test-only + V5 승인 | (c) 수집 test id 집합 = 매핑 | `10-test-separation` 413행 |
| **F1** | `p3-callers-update` | §7.2 추적 호출부 import(줄 머리·문자열)를 목적 모듈로(D-9 제외 집합 밖), B군 계약 test, D군 덮어쓰기 대상(D-17) | equivalence | (c) 호출부 AST가 import 줄(과 D-17이 허용한 D군 대입 줄) 외 동일 + E-INST | test 쪽 문자열 변경은 V5 승인 |
| **F2** | `p3-shim-delete` | shim 3파일 삭제, `stick_diagram` 임시 재수출 제거, REG-DEST | red-green | (a) GONE-SHIM | WP-14 |

**card 수 15**(G1, T0, D0a, D0b, M1~M6, M8, M9, M10, T1, F1, F2 -- M7 흡수).

### 8.1 순서와 병렬 준비

```
(Phase 2 진행 중) P9 → P10 → P10b → 면제 묶기(34) → 범위 정책(35) → B34 → B26-1 ──┬──> T0 ──────────────┐
B28(병합 2b41e79) ── B33(33, G1 전 어느 때든) ──────────────────────────────┴──> G1(32) → D0a → D0b ──┴──> M1 → M2 → M3 → M4 → M5 → M6 → M8 → M9 → M10 → T1 → F1 → F2
```

* **v5 순서 근거**: 면제 묶기는 A1-a대로 P9·P10·P10b 뒤 B26-1 전, 범위 정책은 B26-1의 V3 비용 근거(228 변이)라 B26-1 전, B34 → B26-1은 두 card 초안의 순서, B26-1·B34는 A2대로 M card 전,
  게이트 card 셋은 G1 전(§5.5.1). **T0는 B26-1 병합 뒤**(계약 10이 B26-1의 계수 test를 고친다). D0b는 B26-1·B34 병합 뒤 master에서 이관표를 처음 계산한다(§6.4). G1은 Phase 2 DoD와 독립이지만
  M card는 Phase 2 DoD PASS 뒤(§9.1).
* **지금 병렬로 준비 가능(spec card 초안·작성 전 실측)**: G1, T0, D0a. 실행 순서는 G1 → D0a(D0a가 G1의 `SourceIndex`·`moved_defs`를 부른다 -- 같은 개념을 둘로 구현하지 않기 위한 의존), T0는 G1과 독립.
* M 순서가 번호순인 이유: 작은 번호부터 만들면 매 card 병합본에서 새 파일이 잔여 shim을 import할 일이 없다(ORDER). M 작성 전 실측은 D0b 이관표 한 벌에서 결정적으로 나온다.

---

## 9. 착수 조건과 사용자 결정 (N9.2-7)

### 9.1 착수 조건

* 공통(N6.1 991행): 이 문서의 사용자 승인(DEC-51), **Phase 2 DoD PASS**(현재 남은 것: P9, P10, DoD E0~E5 -- `.ai/context.md` 기준, P3c 보류 B21).
* U-03(N7.2 1078행): 승인 기록 없음(부록 A M27).
* 게이트 선행: B28 병합(**완료** -- `2b41e79`, 판정 기록 `8790b24`), **B33·면제 묶기·범위 정책 병합(G1 전, §5.5.1)**, G1 병합.
* **엔진 선행(A2, v5)**: B34·B26-1 병합(M1 전). 승인 기록 `20260930-b26-before-phase3` '재검토': 둘 중 하나라도 병합되지 않은 채 M card를 시작하면 그 card의 앞당김이 효력을 잃는다 -- 그래서 M1의
  착수 조건이다. T0는 B26-1 병합 뒤(§8.1).
* 재측정(2차 검토 S8, v5 확장 -- Phase 3 시작 때): (1) P9·P10·B34·B26-1 병합본에서 머리의 재측정 조건 (1)의 엔진 줄 인용·부록 A 행과 §6.4 표의 추정 행 전부, §7.1 v5 행(B26-1·B34 계약 test의
  실제 줄), §7.2 S11(대입문 + `setattr`). (2) B33·면제 묶기·범위 정책 병합본에서 §5.1 줄 번호·V7 미도달 수, G1 card '작성 전 실측' 1·2, 부록 A G2·G5' base 열, §10 E2의 출력 키.
  (3) D0b는 (1) 뒤 master에서 이관표를 처음 계산한다(§6.4). 인용 줄·개수가 바뀌면 이 design의 개정이 아니라 사실 문장 갱신이다 -- 규칙·판정식은 줄 번호에 기대지 않는다.
* 문서 개정 커밋 시점(검토 S4): 게이트 변경 card(G1)는 spec card와 그것이 개정하는 design 05·계획서 문구를 **같은 커밋(승인 전)**에 넣고, 승인 기록(`target_kind: diff`)의 `diff_path`가
  세 경로를 덮는다(B28 승인 `20260930-v3-history-clone`의 `diff_path` 두 줄 선례). 이 design의 UD-0 문서 개정도 design 커밋과 함께 승인 대상 diff에 든다.

### 9.2 사용자 결정(진짜 사용자 몫만 -- 착수 조건 3개)

초안 v3의 5개(UD-0·1·5·6·7)에서 2차 검토 §5 권고대로 줄였다: **UD-7 → D-17**(기본안이 probe 기능을 보존하므로 삭제·범위 축소가 아니다 -- 원칙으로 확정, UD-0이 덮는다),
**UD-6 → '뒤에 올 승인'**(T0 V5 승인은 test 커밋 뒤 diff 해시로만 받을 수 있어 착수 전 결정이 될 수 없다 -- T1·F1의 V5 승인과 같은 기준).

| ID | 결정 | 기본안(원칙에서) | 왜 사용자 몫인가 |
|---|---|---|---|
| **UD-0** | 이 design 승인(DEC-51). §9.3 기본값(D-1~D-21, **D-17 probe 처리 포함**)과 문서 개정을 함께 덮는다: 계획 N3.10 표(A-3 계산 결과 -- `load_topology`·`validate_theta_declaration_order` 위치, `optimize_full_circuit_budget` Phase 3 위치 MOD8, **v5: MOD2 '대표 대상'에 `rail_declaration` 추가(D-19)**), N3.10 533행에 "V6·V7의 '새'도 같은 규칙"(G1 spec card와 같은 커밋), 534행 '추적 파일' 제외 집합(D-9), N3.12.3 test-only 열거에 "Phase 3 T0·T1", `00-common` §3.2 103행·§10.1 431행(D-5), `10-test-separation` §5.6 영역 표 '파일' 열을 설명으로(T0) | §9.3 | 계획서 표·판정 문구 개정은 승인 대상(0.5 공격 16) |
| **UD-1** | **U-03**: 추적 안 된 `workspaces` 스크립트가 shim 삭제로 깨지는 것을 허용 | 계획 기본안 그대로 -- 추적 파일은 전부 F1에서 갱신, 추적 안 된 1개(`smoke_run_harness_session18_save.py`)는 깨지게 둔다 | 계획이 사용자 결정으로 지정(N7.2) |
| **UD-5** | **G1 게이트 변경 승인** + **이동 인식 방식의 비용 선택** | **(가) 전역 규칙**(G1 spec card 그대로) | 판정 기준(게이트) 변경은 사용자 승인(05 §18). 두 방식 모두 '약화 금지'를 만족하므로 비용 선택은 사용자 몫(1차 검토 §3-2) |

**UD-5 비용 비교**(권고 (가)). 근거 수치는 v4 재측정(`p3v4_g1_results.json`, HEAD `7535799`의 실제 게이트 도구 + 참조 구현 모의)이다:

| | (가) 전역 이동 인식 규칙 | (나) 승인 기록에 선언된 이동만 인정 |
|---|---|---|
| 막는 것 | M-0·M-0h·M-1~M-4·골격·qualname 중복 제외가 거부하는 부류. 합성 단계 51개 중 거부 단계 전부 거부 -- 1차 검토 반례(거부 13단계)와 2차 검토 새 반례 22건(G1 19 + `move_plan check` 3). 규칙 밖의 새 부류가 나오면 규칙을 고쳐야 한다(v3 → v4가 그 예: 2차 검토가 v3 규칙을 통과한 7부류를 찾았고 M-0h·qualname 중복 제외·해시 대조·출처 정밀화(S1)·`__future__` 대조를 더해 닫았다) | 선언 밖 이동은 전부 '새 정의'. **선언 안에서는 (가)와 같은 규칙이 필요**하다 -- 2차 검토의 N1·P·N3b·N4·N13·N5는 모두 선언된 from→to 안에서 일어나므로 선언만으로는 막지 못한다 |
| 비용 | 게이트 변경 1회(G1). card마다 추가 승인 없음 | 게이트 변경 1회 + M card 8개마다 승인 기록 1건(+ 선언 형식·대조 코드) |
| 이중 대조 | Phase 3 안에서는 이미 `move_plan check`의 `move-set`이 **이 base→head의 모든** 옮긴 단위를 **이관표(D0b 승인 결과)**와 대조한다(2차 검토 S4 반영) -- 선언이 이관표로 존재한다 | 이관표와 승인 선언이 같은 내용을 두 번 적는다 |
| Phase 3 밖 | 규칙대로인 이동은 어느 card에서든 인정 -- 실제 엔진 4파일 통째 이동 모의에서 거짓 거부 0(단위 402/402, def 473/473, M-0h 위반 0) | 선언 없는 이동은 불인정(보수적) |

권고 근거(v4 수치로 다시 씀): (나)가 (가)보다 더 막는 것은 '규칙을 통과하는 이동이 Phase 3 밖에서 계획 없이 일어나는 것'뿐이다. 그 이동은 v4 규칙상 (i) 단위 해시가 원본과 같고
(M-1·골격), (ii) 목적 파일에서 유일하게 바인딩되며 덮어쓰지 않고(M-0·M-0h), (iii) 원본 자리에 재수출만 남고(M-2), (iv) 전역 읽기 출처·`__future__`가 원본과 같다(M-4) -- 2차 검토가 v3에서
찾은 약화 7부류(N1·N2·P·N3b·N4·N13·S2 `except as`)는 v4 규칙에서 전부 base 도구와 같은 exit로 돌아왔고(§5.2 표), v3 27단계의 exit는 하나도 바뀌지 않았으며, 실제 엔진 통째 이동의 거짓 거부는
0이다. 규칙이 모든 부류를 증명하지는 않는다(측정 한계: 합성 반례 + 엔진 통째 이동) -- 그래서 Phase 3 안에서는 `move_plan check`(이관표 대조·`rebind`·`future`·`stmt-order`·def 단위
`changed`)가 두 번째 선을 이루고, M card마다 V3 `defs` = `[]`을 요구한다(§8). (나)의 선언은 그 두 번째 선과 같은 정보를 한 번 더 적을 뿐 선언 안의 약화(N1·P 등)는 막지 못한다 --
추가 승인 8건은 원칙('결정은 원칙으로 기본안부터')에 비해 이득이 없다.

뒤에 올 같은 성격의 승인(지금 결정할 것 아님 -- 각 card의 test 커밋 뒤 diff 해시로 받는다): **T0 V5 승인**(판정 범위 확대 + 유일성 검사 추가, 기대값 불변, 죽은 상수 삭제 -- 초안 v3 UD-6),
T1·F1의 V5 승인(test 파일 이동·import 문자열).

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
| D-16 | M card는 `tools/**` 변경 0, 판정 도구는 `move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit` 사본(지금은 D0a) | 작성자≠검증자(1차 검토 S9, 2차 검토 m6) |
| D-17 | §7.2 D군 probe·진단 스크립트(8파일, 대입 14줄): F1에서 덮어쓰기 대상을 `binding_origin`으로 찾은 호출자 모듈 전부로 바꾸고, F1 oracle에 그 대입 줄만 예외. 대안('Phase 3 뒤 동작하지 않는 probe'로 표시)은 사용자가 원할 때만 | probe 기능 보존 -- 삭제·범위 축소가 아니므로 원칙('결정은 원칙으로 기본안부터')상 사용자 결정 불필요(2차 검토 §5, 초안 v3 UD-7 흡수) |
| D-18 | redteam 번호(v5): G1 `32-moved-defs`, B33 `33-v7-registry-edges`, 면제 묶기 `34-v3-exempt-binding`, 범위 정책 `35-v3-changed-scope`(오케스트레이터 배정, 병합 순서 무관) | 네 게이트 card의 번호 충돌 방지(§5.3-5) |
| D-19 | `rail_declaration`(B26-1)은 N3.10 MOD2 '대표 대상'에 더해 A-1로 MOD2, `RailDeclaration`은 A-2로 MOD2. B37a 접근자도 같은 MOD2 | MOD2 책임 '스키마·선언 게이트', A-5(MOD3)는 책임과 어긋남, 계층 허용(3→2)(§6.4) |
| D-20 | 옮기며 바뀐 def·거부된 이동 후보의 V3 대상 = 새 경로의 새 def(본문 전체). 이동 원본과 문장 단위로 맞추지 않는다 | 범위 정책 약화 승인(A1-b)은 같은 경로의 기존 def만 덮는다, Phase 3는 옮기며 바꾸지 않는다(F2)(§5.5.2) |
| D-21 | G1은 V3 면제 대조(면제 묶기 card)를 바꾸지 않는다. 옮긴 def는 대상이 아니라 대조 없음, 거부 후보는 새 모듈 id라 옛 원소 미적용(fail-closed) | 변이 id 모듈 = 파일 줄기, 묶기 해시 = def 원본(§5.5.3) |

---

## 10. DoD 측정 명령 (N9.2-6)

auditor가 Phase 3 마지막 card 병합본의 격리 복제본 `<iso>`에서 **bash**로 실행한다. `PT`는 `10-test-separation` §10 정의를 그대로 쓴다. `$PY` = `C:/Python314/python.exe -B`. `MP_ARGS`는 §6.3의
bash 배열이고 명령에는 반드시 `"${MP_ARGS[@]}"`로 넣는다(2차 검토 B2).
`MP` = `tools/migrate/move_plan.py`를 **마지막으로 바꾼 판정 기록의 `code_commit`**(`MPC` -- 지금은 D0a; 2차 검토 m6)에서 꺼낸 사본: `git -C <iso> show <MPC>:tools/migrate/move_plan.py > <S>/move_plan.py`(`<S>` = auditor 스크래치).
`CARDS` = M1~M6·M8·M9 판정 기록(`.ai/verification/<M id>.json`)의 (`base_commit`, `code_commit`, MOD 파일) 목록.

| ID | N6.2 `3` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | MOD1~MOD10 존재 | `$PY <iso>/tools/gates/import_layering.py --root <iso>` 출력 `present` | `present`가 N3.10 표 10행 전부(표는 도구가 계획서에서 읽는다) |
| E1 | import 계층 위반 0 | 같은 명령 | exit 0, `findings` 0 |
| E2 | 이동 커밋마다 AST 해시 동일 | `CARDS`의 (b, h, m)마다 ① `$PY <iso>/tools/gates/mutate_changed.py --root <iso> --base b --head h --pytest-ini <캐시>/pytest_gate.ini > <S>/v3_m.json` ② `$PY <S>/move_plan.py check --root <iso> --base b --head h --card m "${MP_ARGS[@]}" > <S>/chk_m.json` | ① exit 0, JSON `defs` = `[]`, `mutants` = 0, `move_rejected` = `{}`, `not_targeted` = 0, `targets_by_def` = `{}`(범위 정책 키, v5)(M card 판정에서 card마다 이미 요구한 것의 재확인 -- §8 M행). `exempt_ignored`·`survivor_bindings`(면제 묶기 키)는 기준이 아니다(변이 0이면 비어 있다) ② exit 0, `findings`의 모든 목록 비어 있음(`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`stmt-order`·`order`·`shim`·`cache`) ③ **일관성 점검(증거로 세지 않는다)**: ①의 `moved`(`to`→`from`) = ②의 `moved_defs`, ②의 `moved_units` 목적지 집합 = ②의 `assigned` -- ①과 ②는 같은 `<iso>/tools/gates`의 같은 `moved_defs`를 부르므로(D0a가 `--root`에서 import) 동어반복이다(2차 검토 m5). `targets`(파일 목록)는 기준이 아니다(1차 검토 B5). 출력 키가 바뀌면 이 행을 다시 잰다(§5.3-4) |
| E3 | `sizing_recipe.py` 삭제 | `git -C <iso> cat-file -e HEAD:skills/analog-gmid-design/assets/sizing_recipe.py`(실패해야 함) + `git -C <iso> grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|topology_library\|design_report)\b" -- '*.py'` + `git -C <iso> grep -l -E 'import_module\("(sizing_recipe\|topology_library\|design_report)"\|_import\("(sizing_recipe\|topology_library\|design_report)"' -- '*.py'` | 첫 명령 exit ≠ 0, 둘째·셋째 결과 ⊆ D-9 제외 집합 |
| E4 | 레지스트리 목적지 = 실제 위치 | `PT <iso>/skills/analog-gmid-design/assets/tests/contracts/test_p3_registry_dest.py`(D0b) + `$PY <S>/move_plan.py plan --root <iso> "${MP_ARGS[@]}"` | test PASS, 도구 exit 0, `reg_mismatch`·`unassigned`·`upward`·`cycles`·`conflicts` 0, `absent_split` = `[sizing_recipe.py, topology_library.py, design_report.py]`, `stick_diagram.py`·`audit_current_forced.py` 밖 단위의 `rule` 전부 `A-0` |
| E5 | 동작 보존(N6.3) | `PT` 전체 + E-LIB·E-INST 재측정 | Phase 2 DoD와 같은 해시 |
| E6 | 정의 보존(MOVE-TOTAL) | `$PY <S>/move_plan.py check --root <iso> --base <M1 판정 기록 base_commit> --head HEAD --card ALL "${MP_ARGS[@]}" --allow-changed workspaces/run_harness.py::run skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline` | exit 0(모든 발견 목록 비어 있음). `shim`은 F2 뒤 shim 파일이 없어 해당 없음. base를 'Phase 3 첫 card base'가 아니라 **M1 판정 기록 `base_commit`**(D0b 병합 뒤)로 둔다 -- G1·T0·D0a·D0b 뒤라 `check`의 `assigned`가 D0b 레지스트리로 계산된다(2차 검토 m4) |

---

## 11. 열린 질문 (N9.2-8)

없다. §9.2의 UD는 착수 전 사용자 결정 대기 항목이다. 이 초안이 드러낸 **계획·문서 개정 요청**(UD-0에 포함):

1. 레지스트리 목적지 열이 N3.10 이전 판 이름을 쓴다(§6.1) -- 517행 "레지스트리 열이 정본"은 D0b 재생성 뒤에 성립한다.
2. N3.10 533행의 이동 제외가 V3에만 적혀 있다 -- V6·V7도 같은 규칙이어야 이동 card가 판정 가능하다(§5.1). '옮긴 단위'의 정의는 이 design §3(G1 spec card 계약 0~3)을 인용한다.
3. N3.12.3 test-only 열거에 Phase 3 T0·T1이 없다.
4. 534행 '추적 파일 전부 갱신'과 판정 기록 불변(D-9)의 충돌.
5. `00-common` §3.2 103행과 §10.1 431행의 MOD10 인자 담당, 431행 시그니처에 topology 경로 인자가 없음(D-5).
6. 백로그 후보(§5.4): Phase 3 밖 card의 같은 경로 import 재바인딩(Phase 3 안은 `check` `rebind`), 클래스 수준 문장이 V3·V6에 보이지 않음. (V7 그래프의 `__init__`·레지스트리 값 간선은 B33이
   G1 전에 닫는다 -- v5.)
7. (v5) N3.10 MOD2 '대표 대상'에 `rail_declaration` 추가(D-19, §6.4).
8. (v5) 다른 초안에 넘기는 정정(이 design이 고치지 않는다): B33·면제 묶기·범위 정책 card의 redteam 번호를 33·34·35로(D-18), 범위 정책 card '결정 필요 항목'의 G1 순서 문장(이제 G1이 나중 --
   G1 card 계약 4가 합성 문장을 가진다), B37a의 접근자 모듈(D-19 MOD2와 같음 -- 확인만).

---

## 부록 A. 측정 명령과 결과 (모두 읽기 전용; v3 행은 gate `master` `cd64170`, v4 행(G5'·G6'·H'·B2·S8·F)은 `7535799`)

`R` = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `D` = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts`, `$PY` = `C:/Python314/python.exe -B`. v1·v2 스크립트는 초안 v2 부록 A대로.
v3 스크립트는 `D/p3v3_g1_measure.py`(합성 저장소는 `C:/g29` 아래에 만들고 단계마다 지움)와 `D/p3v3_facts.py`. v4 스크립트는 `D/p3v4_g1_measure.py`(합성 저장소는 `C:/g51` 아래, 단계마다 지움,
케이스마다 `p3v4_g1_results.partial.jsonl`에 누적 기록) → `D/p3v4_g1_results.json`.

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
| S7 | 같은 실행 `future_annotations` | `from __future__ import annotations` SR 35행, SD 32행(**TL 24행 누락 -- v4 F행에서 정정**, 2차 검토 S3) |
| S11 | 같은 실행 `S11_attr_overrides`(`git grep -n -E "^\s*(sr\|sd\|sizing_recipe\|stick_diagram\|topology_library\|design_report\|tl\|dr)\.[A-Za-z_]+\s*=[^=]" -- '*.py'`) | **14줄** 8파일(probe 12 + workspaces 2, §7.2 D군 -- v3 '12줄'은 오기, 2차 검토 m1) |
| S12 | 같은 실행 `S12_run_inventory` + 파일별 집계·`run`의 직접 호출자 | 60 test(`test_extract_selftest.py` 24, `test_selftest_sizing_recipe.py` 22, `test_probe_parasitic_pm_all_circuits.py` 5, …), 직접 호출자 12 = `_run_combo`·`_run`·`base_blob_text`·spice `run` 등 이름 과대 근사 |
| S13 | `git -C R grep -n _SIZING_RECIPE -- .` | `test_ts6_dead_probes.py` 60·221·222·261·262뿐 |
| m6 | 같은 실행 `m6_scan_names` | T0 spec card 계약 9 목록 |
| m7 | 같은 실행 `m7_string_imports` | 10곳(모두 `A/tests/contracts`) |
| G5' | `$PY D/p3v4_g1_measure.py` → `p3v4_g1_results.json` `counterexamples`(51단계 = v3 27 + 2차 검토 새 반례 24: N1·N1b·N1c·P·P-exact·N2·N3·N3b·N4·N5·N5ok·N6·N6ok·N7·N8a·N8b·N9a·N9b·N10·N11·N12·N13·S2 2개·S5; 단계마다 합성 git 저장소에서 HEAD `7535799`의 `mutate_changed.py`·`source_lint.py`·`reachability.py` 실제 실행, v3·v4 규칙 참조 구현 나란히, v4는 D0a `check` 발견 모의까지) | `v3_regression` 27/27 참(v3 규칙 결과 = 초안 v3 측정), `v3_steps_v4_changed` 빈 사전(v4가 v3 27단계 exit를 바꾸지 않음). `adversarial_summary` 22건 전부 `rejected` 참(G1 19, `check`만 3: `same-path-rebind`·`N6`·`S5`). v3 규칙이 base보다 약했던 것 N1·N2·P·N3b·N4·N13·S2 `except as`(+ `check` 몫 N6·S5) → v4 exit = base. 보수 비용 `P-property-exact` v4 V3/V7 1 |
| G6' | 같은 실행 `real_rename_same_dir`(v4)·`engine_facts` | 단위 218/218·169/169·8/8·7/7, def 272/272·181/181·12/12·8/8, 거부 0, M-0h 위반 0, qualname 중복 제외 0, `check` 모의 발견 0(`rebind`는 트리 전체 단위 대조). `moved_defs` 한 호출 7.9~15.6초, `check` 모의 1.3~2.4초. 엔진 4파일 star 0·`global` 0·`multi` 0·qualname 중복 0, future `annotations` SR 35·SD 32·TL 24(DR 없음) |
| G7' | 같은 실행 `noop`(v4 규칙) | `df36`·`dup-w-calc` 모두 빈 결과(v3과 같음) |
| B2 | `MP_ARGS="--split a.py b.py --aliases '{\"optimizer\": \"theta_search.py\"}'"; printf '[%s]\n' $MP_ARGS` 대 §6.3 배열 `printf '[%s]\n' "${MP_ARGS[@]}"`, `$PY -c "import sys,json; json.loads(sys.argv[-1])" "${MP_ARGS[@]}"` | 문자열: `['{"optimizer":]`, `["theta_search.py"}']`(파손). 배열: 마지막 원소 `{"optimizer": "theta_search.py"}`, JSON 파싱 성공, 인자 14개 |
| S8 | `grep -n 'diff", "--name-only\|make_clone\|cat-file\|changed_defs\|rmtree\|json.dumps\|def def_hash\|def _strip_doc\|base_src' R/tools/gates/mutate_changed.py`; `grep -n 'add_parser("vcase")\|tool_tmpdir\|root_state\|observe' R/tools/gates/redteam/lib/rt.py`; `ls R/tools/gates/redteam/attacks \| tail -1`; `git -C R diff --stat cd64170 HEAD -- A/*.py workspaces/run_harness.py docs/01-plan` | `make_clone` 53·323, `_rmtree_force` 61·406, `_strip_doc` 74, `def_hash` 84, `changed_defs` 88~100·364, diff 314, cat-file 359, `base_src` 361, 출력 398·402·407; vcase 1351, 관찰 599~621, `run_all.py:98` `observed_equals`; 마지막 `31-v3-git-history`; 엔진·계획서 변경 0 |
| F | `grep -n "__future__\|import \*\|^\s*global " R/A/*.py R/workspaces/run_harness.py`; `$PY -c` symtable 실측 `X = [t*K for t in range(3)]` | future SR 35·SD 32·TL 24, star 0, global 0; 3.14 `symtable` 모듈 표에 인라인 컴프리헨션 변수 `t`가 지역·대입으로 들어감(문장 단위 전역 읽기를 AST 유효 범위로 세는 근거) |
| B33 | `grep -n "attacks/<다음 번호>" D/prep_b33_v7_edges.md`; `ls D/draft_b33.spec.md` | 278행 "G1 32 예정이면 그 다음", B33 spec card 초안 없음 → D-18(G1 32, B33 33) |
| H | `git -C R rev-parse --short HEAD`, `git -C R rev-parse --short gate/master`, `git -C R log --oneline -1 role/code/20260930-v3-history-clone` | v3: `cd64170`, `cd64170`, `dee338d`(B28 code, 미병합). **v4(H')**: `7535799`, `7535799`, B28 병합 `2b41e79`·판정 기록 `8790b24` |
| P | `PYTHONPATH=R/tools/gates $PY -c "role_paths.parse_spec_card(...)"` 세 초안 | G1·T0·D0a 머리 파싱 성공(절 11개씩) -- v4 세 card도 같은 명령으로 재확인(부록 D), v5 세 card도 재확인(부록 E) |
| E1 | `git -C R rev-parse --short HEAD`(v5, 2026-10-01) | `7535799` -- v4 측정 시점과 같다(B26-1·B34·B33·면제 묶기·범위 정책 모두 미병합 초안) |
| E2 | `grep -n "mid\|modname" R/tools/gates/mutate_changed.py`; `grep -n "def module_name" -A2 R/tools/gates/reachability.py` | `modname = rch.module_name(path)` 362, `mid = "%s:%s:%s:%s" % (modname, q, opname, npath)` 374, 면제 대조 375; `module_name` = `os.path.splitext(os.path.basename(path))[0]`(47행) -- 변이 id 모듈 = 파일 줄기(§5.5.3) |
| E3 | `git -C R grep -n setattr HEAD -- '*.py'`; `git -C R grep -n "monkeypatch\." HEAD -- skills/analog-gmid-design/assets/tests` | `setattr` 0건, `monkeypatch.`는 `test_df36_instance_relpath.py`의 `chdir` 4건뿐 -- 엔진 모듈 속성 교체 0(§7.2) |
| E4 | `grep -n "^def load_topology\|^def find_matching_candidates\|^def _import_analog_grammar\|^def true_current_mirror_groups\|^def resolve_stack_layout" R/A/*.py`; `sed -n 515,531p R/docs/01-plan/…plan.md` | `load_topology` SD 8550, `_import_analog_grammar` SD 1045, `find_matching_candidates` SD 945, `true_current_mirror_groups` SR 2191, `resolve_stack_layout` SR 6470; N3.10 MOD2 책임 "topology·spec 로딩, 스키마·단위·참조·선언 순서 게이트, 구조 제안"(D-19 근거) |
| E5 | 초안 읽기(측정 아님): `D/draft_b26_1.spec.md` 의도·계약 1~4·11·'신규 시그니처', `D/draft_b34.spec.md` 범위·사이트 표, `D/draft_b33.spec.md` 계약 7·9·'작성 전 실측' 1, `D/draft_v3_exempt_binding.spec.md` 용어·계약 2·3, `D/draft_v3_scope_policy.spec.md` 계약 1~3·'결정 필요 항목', `D/approval_20260930-b26-before-phase3.md`, `D/user_decisions.md` A1·A2 | §5.5·§6.4 추정 행의 출처. 병합 뒤 실측으로 바꾼다 |

측정 한계: M14는 초안 배정 기준·`ast.Name` 참조만. G1은 '파일 전체가 새 파일'인 상한. G5·G6의 v3 결과는 **참조 구현 모의**다(게이트 도구 자체는 바뀌지 않았다) -- G1 card의 red-green이 실제
판정이다. G6은 '같은 디렉터리 통째 이동'이라 실제 card의 부분 이동과 다르다(부분 이동의 거짓 거부는 M-4 고정점에서 '함께 옮겨야 할 것을 안 옮긴' 경우뿐이고 그것은 PLAN-LAYER·
`move-set`이 먼저 잡는다).
v4 추가 한계: G5'·G6'의 v4 결과와 D0a `check` 발견도 **참조 구현 모의**다(`move-set`·`order`·`shim`·`cache`는 이관표·MOD 표가 필요해 모의하지 않았다). '반례 전부 거부'는
합성 반례 51단계 + 엔진 통째 이동에 대한 측정이지 규칙의 완전성 증명이 아니다 -- 그래서 Phase 3 안에서는 `check`와 card별 V3 `defs` = `[]`이 두 번째 선이다(§9.2 UD-5).

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

## 부록 D. 초안 v3 대비 정정(2차 검토 `review2_phase3_v3.md` 반영 -- 발견별 대응표는 `phase3_revision_log.md` '초안 v3 → v4' 절)

| # | v3 | v4 |
|---|---|---|
| 1 | MOVED = M-0~M-4, V3·V7 제외 = `<경로>::<qualname>` 키 | **M-0h**(목적 파일에서도 유일 바인딩), p_b·p_h qualname 중복 def 제외, V3·V7 제외 대조 = (경로, qualname, `def_hash`)(B1). 새 부류 9단계를 G1 redteam에 추가(29단계) |
| 2 | `MP_ARGS="…"` 문자열, 명령 `$MP_ARGS` | 배열 `MP_ARGS=(…)`, 명령 `"${MP_ARGS[@]}"`(B2, 부록 A B2 실측). D0a 계약 1에 셸 사용 문장 |
| 3 | `binding_origin`: `unbound` 경로 없음, `ext` 디렉터리 없음, star는 바인딩 없을 때만 | `global` 선언 이름 = `global-dynamic`(경로), `ext`·`ext-module`에 가져오는 파일 디렉터리, star import가 있으면 모든 이름 `star`(S1 (a)(b)(c)) |
| 4 | 바인딩 = def·class·대입·`for`/`with` 대상, 문장 단위 전역 읽기 = 모든 `Name`(Load) | 모듈 공간 `Store`/`Del` 전부 + import·`except as`·`match` 포획·`type`, 문장 단위도 유효 범위 규칙(S2) |
| 5 | `__future__` 차이 미검사 | M-4가 기능 집합 대조, `check` `future` 발견, 엔진 사실에 TL 24행(S3) |
| 6 | `move-set` = `--card` 목적지 옮긴 단위만 | 이 base→head의 **모든** 옮긴 단위 = 배정, 목적지 전부 `--card`(S4) |
| 7 | 같은 경로 import 교체가 Phase 3 안에서도 사각 | `check` `rebind`(모든 head 단위 출처 = base 출처)(S5) |
| 8 | 옮긴 클래스 메서드 본문 변경은 E2까지 안 드러남 | M card마다 V3 `defs` = `[]`, `check` `changed`가 옮긴 클래스 안 def까지(S6) |
| 9 | D0a 계약 8(b) `assignment` 동일(문자 그대로 거짓) | (단위 키 → `mod`) 사상 동일(파일 부분·`rule` 제외), 문장 단위 키 정의(S7) |
| 10 | B28 병합 전 사실(`cd64170`, 줄 50~62·321·326, `copytree`, redteam "B28이 31") | `7535799` 재측정(88~100·359·361·364·407, `make_clone`), B28 병합 완료, redteam G1 = 32·B33 = 33(D-18), P9·P10 뒤 재측정 조건(S8) |
| 11 | D군 "대입 12줄", 문장 순서·main 블록 미검사, E6 base "첫 card base", E2 ③ 증거, 사본 출처 두 문언, 규칙 이름 관찰 방식 없음 | 14줄(m1), `check` `stmt-order`(m2)·`shim` main 블록(m3), E6 base = M1 판정 기록 `base_commit`(m4), ③ = 일관성 점검(m5), 사본 = `move_plan.py`를 마지막으로 바꾼 판정 기록 `code_commit`(m6), redteam `observe: "moved"`(m7) |
| 12 | 사용자 결정 5개(UD-0·1·5·6·7) | 3개(UD-0·1·5): UD-7 → D-17, UD-6 → 뒤에 올 승인. UD-5 권고 근거를 v4 수치로 다시 씀(2차 검토 §5) |

## 부록 E. 초안 v4 대비 정정(v4 뒤 확정된 결정·card 반영 -- 대응표는 `phase3_revision_log.md` '초안 v4 → v5' 절)

| # | v4 | v5 |
|---|---|---|
| 1 | B26-1·B34와 Phase 3의 관계 없음, 재측정 조건 = P9·P10 뒤 | A2(승인 기록 `20260930-b26-before-phase3`): B34 → B26-1을 M1 전 착수 조건으로(§9.1, '재검토' 절 인용). 두 card가 바꾸는 사실을 초안에서 추정해 §6.4 표로 두고 'Phase 3 시작 때 재측정'. **D0b는 두 card 병합 뒤 master에서 이관표를 처음 계산**(§6.4·§8 D0b행·§9.1) |
| 2 | `rail_declaration`·`RailDeclaration` 배정 미정(단위가 없었다) | D-19: N3.10 MOD2 '대표 대상'에 `rail_declaration`(A-1, UD-0 문서 개정), `RailDeclaration`은 A-2로 MOD2. 규칙만이면 A-5로 MOD3가 되어 MOD2 책임(스키마·선언 게이트)과 어긋남. B37a 접근자도 MOD2(§6.4) |
| 3 | §7.1 A군 3파일, §7.2 "contracts에 속성 덮어쓰기 0"(대입문만 셈) | B26-1 계수 test(`stick_diagram.rail_declaration` 모듈 속성 교체)를 A군(T0 계약 10)으로, B34·B26-1 test의 모듈 이름 호출을 B군(F1)으로. HEAD `setattr` 0건 실측(E3), S11을 `setattr` 형태까지 재측정 |
| 4 | G1 base = B28 병합본 `7535799`, 다른 게이트 card와의 합성 없음 | §5.5: B33·면제 묶기·범위 정책이 G1 전에 병합, G1이 나중 card로서 합성 문장을 가진다. V3 = 옮긴 def 먼저 제외 → 나머지에 N2(§5.5.2), 옮기며 바뀐 def·거부 후보 = 새 def 본문 전체(D-20), 면제 대조 불변(D-21, 변이 id 모듈 = 파일 줄기 실측 E2), B33 그래프 불변·바인딩 노드·재수출 규칙(§5.5.4) |
| 5 | §5.4 V7 `__init__`·레지스트리 간선 = 백로그 | B33이 G1 전에 닫음. F5·§5.1의 V7 미도달 108은 B33 뒤 재측정(시제품 추정 약 39) |
| 6 | redteam 번호 G1 32·B33 `33-v7-graph-edges` | G1 32·B33 `33-v7-registry-edges`·면제 묶기 `34-v3-exempt-binding`·범위 정책 `35-v3-changed-scope`(D-18 개정). 세 card 초안의 번호 정정은 그 card 몫(§11-8) |
| 7 | M card·E2 V3 기준 `defs` = `[]`·`mutants` = 0·`move_rejected` = `{}` | + `not_targeted` = 0·`targets_by_def` = `{}`(범위 정책 키). 면제 묶기 키는 기준 아님 |
| 8 | §8.1 순서도 G1·T0·D0a만 | Phase 2 쪽 선행(P9 → P10 → P10b → 면제 묶기 → 범위 정책 → B34 → B26-1)과 B33 → G1을 그림에 넣음. T0는 B26-1 뒤 |
| 9 | §10 `CARDS` 정의 줄 중복 | 한 줄로(편집 잔재 정리) |
