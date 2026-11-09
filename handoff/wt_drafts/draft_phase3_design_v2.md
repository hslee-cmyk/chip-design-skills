# gain-budget-gmid-sizing -- Phase 3 `30-module-split` design

> **[초안 v2 -- 저장소 미반영]** 정식 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`(현재 없음).
> 측정 시점 = gate `master` `cd64170`(2026-09-30). 측정은 읽기 전용, 스크래치 `C:/g20`(끝나면 삭제). 측정 명령·결과는 부록 A, 초안 v1 대비 정정은 부록 B.

버전 v0.2(초안). 정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05-role-separation`·`20-dead-code-dup`의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 표 `30-module-split` 행): N3.10, N6.1·N6.2 Phase 3, U-03. 추가로 읽은 절: N3.11(test 배치), N3.12.3(card 단위·판정 유형), N4.2 V2·V3·V6·V7, N8, WP-01·WP-03·WP-11·WP-14, NFR-2.

실측 원자료: `p3_measure.py`·`p3_assign.py`·`p3_refs.py`(초안 v1, cd64170에서 재실행 -- 부록 A M6·M9·M14·M15), `p3v2_g1_measure.py` → `p3v2_g1_results.json`(이 판에서 추가, 부록 A G1~G3).
정식 문서로 올릴 때 원자료는 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/`에 둔다(20-dead-code-dup 선례).

---

## 1. 범위 (N9.2-1)

계획 N6.1 Phase 3 행(1000행)이 정본이다: "10모듈 이동(N3.10), shim, 추적 파일 호출부 갱신 후 `sizing_recipe.py` 삭제 | equivalence | U-03". 이 Phase가 구현하는 것:

1. **게이트의 이동 인식**(G1): 계획 N3.10 533행 "해시가 같은 함수는 V3 대상에서 뺀다"가 도구에 없다(§5). 이동 card가 판정 가능하려면 먼저 필요하다.
2. **계약 test 위치 독립화**(T0): 정의가 **특정 파일에 있다고 가정하는** 계약 test 3개가 첫 이동 card에서 깨지거나 공허해진다(§7.1).
3. **이관표**(D0a·D0b): 레지스트리 '이관 목적지' 열을 N3.10 10모듈 이름으로 재생성하고, 계층 규칙(import는 작은 번호로만, 순환 0)을 **옮기기 전에** 계산으로 만족시키는 함수→모듈 배정(§6).
4. **이동**(M1~M9, 모듈 하나당 card 하나 -- 계획 N3.12.3 674행)과 **MOD10 진입점**(M10).
5. **test 재배치**(T1): `unit/test_selftest_<모듈>.py` 4개 → `unit/test_mod*.py`(계획 N3.11 test 배치 541~543행, `10-test-separation` 187·413행).
6. **호출부 갱신과 shim 삭제**(F1·F2).
7. `00-common` §17 표가 넘긴 `optimize_full_circuit_budget` 목적지 불일치(MOD6 대 MOD8) 해소(§6 A-3, D-3).

범위 밖(명시): 함수 분할·추출(CC-7 θ 탐색부 추출은 Phase 4, `00-common` §10.1 435행), 이름 리터럴 교체(DF-23 → Phase 4/7a), D 함수 배선(Phase 4), 레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4), 광범위 except 정리(DF-37, Phase 4), V7 그래프 한계(§5.4 관찰 -- 백로그 후보).

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
| `tools/migrate/move_plan.py` | 이관표·계층 사전 검사·재수출 목록·이동 동일성 대조 도구(code-author). test는 `A/tests/tooling/test_move_plan.py`(test-author) -- 계획 N3.11 549행 `tooling/`, `extract_selftest.py` 선례(D-7) | D0a |
| `tools/gates/reachability.py`·`mutate_changed.py`·`source_lint.py` | 이동 인식(`moved_defs`, §5) -- 게이트 변경 | G1 |

### 2.2 shim 규칙

* 재수출은 `from <MODn> import a, b, _c` 형태만(명시 목록, 도구 생성). **def 래퍼를 두지 않는다** -- 래퍼는 동작 코드라 이동이 아니다(§5.2 규칙 M-3가 이동으로 보지 않는다).
* `stick_diagram.py`에서 나간 이름의 재수출은 **임시**이고 F2에서 지운다(한 이름에 import 경로 하나, WP-14).
* 모듈 수준 캐시(`sizing_recipe.py:2391 _KNEE_L_CACHE`, `:2530 _FEASIBLE_L_WINDOW_CACHE`, `:7697 _ACHIEVABLE_BOUND_CACHE`, `topology_library` `lru_cache` 2곳)는 **읽고 쓰는 함수와 같은 모듈로** 옮긴다(판정 CACHE-ID, NFR-2 -- 캐시가 둘로 갈라지면 재계산이 생긴다). `global` 문 0개라 재수출 이름은 같은 객체를 가리킨다(부록 A M18).

### 2.3 MOD10 진입점

* 정본 시그니처 `00-common` §10.1 431행: `run_gmid_design_pipeline(spec, *, search, output_dir, instrument=None, activations_out=None)`. **Phase 3(M10)는 `spec`·`topology_path`·`search`·`output_dir`까지만** 만든다 -- 하네스 `run()`(`workspaces/run_harness.py:422`)의 파이프라인 몸통을 옮기는 데 탐색 설정과 출력 경로가 필요하다. `instrument`·`activations_out`은 CC-7·CC-8(Phase 4).
* **정본 시그니처의 빈칸(실측)**: 하네스는 topology 경로를 spec이 아니라 `SPECS[circuit]["topology_file"]`에서 만들어(`run_harness.py:427` `topo = os.path.join(LIBRARY_DIR, cfg["topology_file"])`) `optimize_full_circuit_budget(topo, spec, …)`(446행)에 따로 넘긴다. `spec_fn()` 반환값에는 topology 경로가 없다. 431행 시그니처로는 진입점이 topology를 찾을 수 없다 → 키워드 인자 `topology_path`를 더한다(spec 내용을 바꾸면 E-INST 입력이 바뀐다). `00-common` 431행과 §3.2 표 103행(계측 인터페이스 행이 `search`·`output_dir`도 CC-7 몫으로 적음)을 이 design 승인으로 고친다(D-5).
* M10은 이동이 아니라 **추출**(새 def)이라 V3 대상이다. 판정은 E-INST·E-LIB·ENTRY(§3).

### 2.4 새 함수·도구의 원칙(모든 card에 계약으로 들어간다)

* **topology 무관**: G1·D0a 도구는 코드 구조만 읽는다 -- `library/`·`*.topology.json`을 읽지 않고 회로·넷·소자 이름 리터럴이 없다. 합성 저장소(회로 없음)에서 동작함이 그 증거다.
* **만들면 배선**: `moved_defs`는 V3·V6·V7 세 도구의 `main`이 부른다(G1). `move_plan.py`는 (i) D0b의 계약 test가 매 card V1에서 실행하고 (ii) M card마다 판정 기록 `equivalence.commands`에 들어가며 (iii) DoD E2가 부른다.
* **재계산 없음**(NFR-2): base·head 트리의 정의 해시 색인은 도구 실행당 한 번 만든다(G1 계약 8). `move_plan.py`는 소스 파일마다 한 번 파싱하고 한 번의 실행으로 배정·계층·재수출·순서를 같이 낸다.
* **정의 하나**: 이동 판정의 해시 정의는 `mutate_changed.def_hash` 하나다(G1이 `reachability`로 옮기고 `mutate_changed`는 import -- 이름·시그니처 유지). `move_plan.py`는 계층 표를 `import_layering.mod_table`로, 참조 추출을 `reachability._refs`로, 이동 대조를 G1의 `moved_defs`로 읽는다(같은 개념을 다시 구현하지 않는다).
* **작성자≠검증자**: 도구의 test는 test-author가 interface card만 보고 합성 입력(oracle (a))으로 쓴다. 판정 수치는 auditor 판정 기록에서만 인용한다.

---

## 3. 판정식 (N9.2-3)

숫자를 박지 않는다(WP-03). 모두 `영역: 없음(스키마)`. E-LIB·E-INST는 `20-dead-code-dup` §3 정의를 그대로 쓴다(재서술하지 않는다).

| ID | 판정 | 식 | 입력 |
|---|---|---|---|
| E-LIB / E-INST | 동작 보존 | `20-dead-code-dup` §3 | library 회로, 하네스 |
| MOVED | 이동 인식(G1) | head 정의 d = (파일 p_h, qualname q)가 **옮긴 정의**인 것 ⇔ (M-1) base의 소스 분류 파일 중 **정확히 하나** p_b ≠ p_h가 같은 q를 가지고 `def_hash`가 같다 (M-2) head에서 p_b는 q를 정의하지 않는다(사라졌다) (M-3) head에서 (q, 해시)가 p_h 한 곳에만 있다. 최상위 문장(대입 등)은 `ast.dump` 해시로 같은 규칙 | base·head 트리 |
| MOVE-AST | 이동 동일성(533·1018행) | card k의 병합본에서 (a) 이관표가 card k에 배정한 정의 집합 = MOVED가 낸 옮긴 정의 집합 (b) V3 대상(해시가 바뀐 def·새 def) 0 (c) 바뀐 파일의 최상위에서 정의 밖에 바뀐 문장은 import 문과 옮긴 최상위 문장뿐 | 이관표 + base/head |
| MOVE-TOTAL | 정의 보존 | Phase 전 엔진 5파일의 최상위 정의·대입 이름 집합과 Phase 후 MOD1~MOD9 + 도구의 집합이 이름·해시로 1:1(사라진 것 0, 새로 생긴 것은 MOD10 진입점뿐) | 누적 |
| PLAN-LAYER | 이동 전 계층 사전 검사 | 이관표 σ에서, 최상위 정의 u의 **import를 만드는 참조**(이름 참조·엔진 모듈 별칭 속성 -- 문자열·임의 속성 제외) u→v 중 σ(u) < σ(v)인 것 0, 모듈 순환 0 | 이관표 + base 소스 |
| LAYER | 계층 | `import_layering.py --root <iso>` exit 0 | 병합본 |
| ORDER | 중간 상태 | card k 병합본에서 새 MOD 파일이 import하는 엔진 모듈 ⊆ {번호가 작은 MOD}(잔여 `sizing_recipe`·`topology_library`·`design_report`를 import하지 않는다). `import_layering`은 표 밖 파일을 보지 않으므로 이 조건은 `move_plan.py check`가 판정한다 | card별 병합본 |
| SHIM | 재수출 정확성 | shim의 재수출 이름 s마다 `getattr(shim, s) is getattr(목적 모듈, s)`, shim에 def·class 0, `import *` 0 | 병합본 |
| CACHE-ID | 캐시 단일성(NFR-2) | 모듈 수준 캐시(§2.2)마다 읽고 쓰는 함수가 같은 모듈에 있다 | 병합본 |
| LOC-FREE | 위치 독립(T0) | 계약 test의 판정이 '정의 파일'을 이름으로 가정하지 않는다 -- 같은 test가 base 트리와 **정의 하나를 다른 파일로 옮긴 합성 트리**에서 같은 결과 | base + 합성 트리 |
| GONE-SHIM | shim 삭제 | 마지막 card 병합본에서 `sizing_recipe.py`·`topology_library.py`·`design_report.py` 없음, 추적 `.py`의 해당 import 0(제외 집합 D-9 밖) | 병합본 |
| REG-DEST | 레지스트리 = 실제 위치(1018행) | 레지스트리 모든 함수 행의 목적지 셀이 MOD 파일 이름 하나이고 병합본에서 그 정의를 가진 파일과 같다 | 레지스트리 + 병합본 |
| LAYOUT-FLAT | 평면 배치 | MOD1~MOD10 파일이 전부 `A/` 바로 아래 | 병합본 |
| ENTRY | MOD10 | `run_gmid_design_pipeline`이 있고 `workspaces`를 import하지 않으며 하네스 `run()`이 그것을 부른다 | 병합본 |

---

## 4. 실패 경로 (N9.2-4)

Phase 4 전이라 N3.14 실패 클래스가 없다(`20-dead-code-dup` §4와 같은 상황).

| ID | 경우 | 결과 | 처리 |
|---|---|---|---|
| F1 | PLAN-LAYER FAIL | 이동하지 않는다 | §6 규칙으로 배정을 고친다. 규칙으로 안 풀리면 N3.10 표 개정(이 design 승인 범위 -- §9 D-11) |
| F2 | MOVE-AST FAIL(옮기며 본문이 바뀜) | V2 FAIL(그리고 G1 뒤에는 V3 대상이 생긴다) | card 되돌림. 본문 수정이 필요한 이동은 Phase 3가 아니다 |
| F3 | 중간 상태 순환 import | V1 수집 오류 | 순서를 고친다. 함수 안 지연 import로 우회하지 않는다(우회 = skip, 메모리 원칙) |
| F4 | E-LIB·E-INST 차이 | V2 FAIL | 모듈 수준 상태 분리를 먼저 의심(CACHE-ID) |
| F5 | G1 병합 전 이동 card | 판정 불가(V3 변이 약 1.6만 개, V6 새 항목 861, V7 미도달 약 108 -- §5.1) | G1 병합 전에는 M card를 시작하지 않는다(§8) |
| F6 | 계약 test가 첫 이동에서 깨지거나 공허해짐 | equivalence 불성립(test 커밋 불변 + 양쪽 PASS가 안 됨) | T0 병합 전에는 M card를 시작하지 않는다 |

---

## 5. 게이트의 이동 인식 (G1)

### 5.1 실측: 지금 게이트는 옮긴 정의를 새 정의로 본다

| 도구 | '새/바뀐 def'를 정하는 곳(cd64170) | 옮긴 정의에 대한 결과 |
|---|---|---|
| V3 `mutate_changed.py` | `changed_defs(base_src, head_src)`(50~62행)이 **같은 경로**의 base 소스와만 비교. `main`이 `git cat-file -e <base>:<path>`(321행)로 base 파일이 없으면 `base_src = None`(323행) → 그 파일의 def 전부가 대상(326행). diff는 `--no-renames --diff-filter=AM`(276행) | 엔진 4파일을 새 파일로 옮기면 대상 def 473개·변이 15,677개(부록 A G1). 인벤토리 없는 def는 변이 전부 '생존' |
| V6 `source_lint.py` | `compare(path, base_src, head_src, kd)`(212행)가 같은 경로 base와 단위별 항목 수 비교, base 없으면 전부 '새 항목' | 새 파일로 옮기면 새 항목: magic_number 500·continue 347·broad_except 8·id_call 6(부록 A G1) |
| V7 `reachability.py` | `base_defs` = base의 (파일, qualname) 집합(224~229행), `new_defs` = head 노드 중 그 집합에 없는 것(230~231행) | 지금 운영 루트로 도달하지 못하는 엔진 def 109개(승인 면제 1) -- 옮기면 전부 '새 def 미도달'로 FAIL(부록 A G2) |

합성 저장소 red 실측(부록 A G3): def 하나를 바이트 그대로 새 파일로 옮기고 원래 파일은 재수출만 남긴 커밋에서 base V7 exit 1(`new_defs: [b.py::f]`), base V6 exit 1(`broad_except`·`magic_number` 새 항목).

**계획 원문**(N3.10 533행): "무변경 증명 = 이동 전후 함수별 `ast.dump`(docstring 제외) 해시 동일 + import 줄만 차이. **해시가 같은 함수는 V3 대상에서 뺀다.**" -- V3 행(N4.2 839행)도 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것"이고 경로를 말하지 않는다. V6(842행 "새 광범위 except…")·V7(843행 "새 def")은 이동을 말하지 않는다.

### 5.2 고칠 방향

* **판정식은 그대로, 비교 기준만 옮긴다**: 옮긴 정의(§3 MOVED)는 비교 기준이 '같은 경로의 base'에서 '이동 원본(p_b, q)'으로 바뀐다.
  * V3: 옮긴 정의는 대상이 아니다(해시가 같다 = 같은 경로에서 무변경과 같은 취급). 옮기며 한 줄이라도 바뀐 정의는 MOVED가 아니므로 지금처럼 대상.
  * V6: 옮긴 정의 단위의 '이전 항목 수'는 이동 원본 단위의 항목 수(원본 파일 맥락에서 계산). 옮긴 최상위 문장은 새 파일 `<module>` 단위의 이전 항목 수에 원본 맥락의 항목 수로 더해진다. **새 파일 맥락에서 항목이 늘면 FAIL**(예: 캐시 dict만 옮기고 `len()` 상한 검사를 원래 파일에 남기면 `unbounded_cache`가 새 항목 -- 옮긴 문장이라도 걸린다).
  * V7: 옮긴 정의는 '새 def'가 아니다(같은 경로에서 무변경 def를 보지 않는 것과 같은 강도).
* **약화하지 않는다**: M-1(원본 하나)·M-2(원본 자리에서 사라짐)·M-3(한 곳에만 나타남) 때문에 **복사**(원본이 남음)·**래퍼 shim**(원본 자리에 다른 def)·**모호한 원본**(같은 (q, 해시)가 base 두 곳)은 이동이 아니고 지금처럼 새 def다.
* **관찰 가능**: 세 도구의 판정 JSON에 `moved` 목록(`{"from": "<p_b>::<q>", "to": "<p_h>::<q>"}`)을 더한다 -- auditor가 MOVE-AST (a)를 이 목록과 이관표로 대조한다.
* **기존 이름·시그니처 유지**: `mutate_changed.changed_defs(base_src, head_src)`·`def_hash(fn)`은 기존 판정 기록 스크립트가 부른다(`.ai/verification/20260930-df36-instance-relpath/scripts/mut_def.py:67` 등 4곳, 부록 A G4). 해시 정의는 `reachability`로 옮기고 `mutate_changed`는 그것을 import해 같은 이름으로 둔다(순환 import 방지 -- `mutate_changed`가 `reachability`를 import한다. 정의 하나).

### 5.3 B28(`20260930-v3-history-clone`)과의 합성

B28은 `mutate_changed.main`의 **test 실행 환경**(285행 copytree → `--head` 격리 복제본, 328~342행 기준 실행 실패 → `ERROR`, 364행 임시 디렉터리 정리)을 바꾼다. G1은 **대상 선택**(`changed_defs` 호출 326행 앞에 이동 제외, 판정 JSON에 `moved`)만 바꾼다. 둘은 서로의 입력이 아니다. 합성 규칙:

1. G1의 test worktree는 **B28 push 뒤 gate `master`**에서 만든다(05 §12 순서 1). G1 spec card의 '작성 전 실측' 줄 번호는 그 base에서 다시 잰다.
2. G1의 무동작 입력에 B28이 더한 redteam `attacks/31-v3-git-history/` 두 단계를 넣는다(결과 불변).
3. G1은 B28의 계약(격리 복제본·`ERROR`·임시 디렉터리 무누수)을 건드리지 않는다. G1이 새로 여는 git 호출은 base 트리 읽기(`ls-tree`·`show`)뿐이다.

### 5.4 관찰(범위 밖, 백로그 후보)

V7 그래프는 클래스 인스턴스화에서 `__init__`로, 모듈 최상위 레지스트리 dict에서 값 함수로 가는 간선이 없어 `SemiEmpiricalGmIdLUT.__init__`·`_feed_*`(θ feed 레지스트리 값) 같은 def를 미도달로 센다(부록 A G2 표본). 지금은 그 def가 바뀔 때만 드러난다. G1은 이 한계를 넓히지도 줄이지도 않는다(옮긴 def는 '새 def'가 아니므로 V7이 보지 않는다).

---

## 6. 이관표 생성 규칙 (N9.1 '레지스트리 목적지 열에서 생성')

### 6.1 왜 열을 그대로 읽을 수 없는가(실측, cd64170)

* 레지스트리 함수 행 379개의 목적지 셀 분류: `gmid_sizing_engine` 114, `stick_diagram` 87, `circuit_state_graph` 61, `topology_authoring` 32, `sizing_layout_convergence` 14, `instance_report_builder` 7, `gmid_design_pipeline` 2, **MOD 이름이 없는 셀 62**(`optimizer`, `〃`, `삭제 후보`, `test util`, `LUT 생성 도구 유지` 등). **MOD1 `gmid_lut`·MOD5 `circuit_metrics`·MOD6 `theta_search`로 가는 행 0**(부록 A M9).
* 레지스트리 머리: "작성 2026-09-14, 기준 커밋 78b58c6. 계획서 §13(v4.44)의 부속 문서" -- 목적지 열은 10모듈 표 이전 판의 이름을 쓴다.
* N3.10 표 '대표 대상'과 열이 다른 행: `GmIdLUT`·`SemiEmpiricalGmIdLUT`·`_multilinear_interp`(표 MOD1, 열 `gmid_sizing_engine`), `load_topology`(표 MOD2, 열 "파싱: circuit_state_graph S0/S1 로더 / 자동채움:…"), `compute_metric`·`build_ac_network`·`_full_circuit_response`·`estimate_mismatch_sigma`(표 MOD5, 열 `gmid_sizing_engine`), `search_stage_budget_L_warm_start`·`presolve_warm_start`·`_optimize_theta_slsqp`·`repair_infeasible_baseline`(표 MOD6, 열 `optimizer`) 등(부록 A M10).
* 둘 이상 모듈로 **쪼개라**고 적은 셀 16행(부록 A M11). 이동 전용 규칙으로는 함수를 쪼갤 수 없다.
* 레지스트리에 행이 없는 최상위 정의: `sizing_recipe` 3(`knee_L_for_kind`·`feasible_L_window`·`derive_role_L`), `stick_diagram` 24(DF-36이 더한 `_topology_ref_relpath` 포함). 초안 배정 뒤 미배정 최상위 이름 34(대입 포함)(부록 A M12·M13).
* 초안 배정(N3.10 대표 대상 우선 → 열의 첫 MOD 이름 → `optimizer`는 MOD6 → `_metric_*`는 MOD5 → `optimize_full_circuit_budget`는 MOD8)으로 **큰 번호로 향하는 참조 64개**: MOD2→MOD3 17, MOD3→MOD4 14, MOD3→MOD7 9, MOD4→MOD5 8, MOD2→MOD7 6, MOD4→MOD7 3, MOD6→MOD8 2, 그 밖 1씩. 가장 많은 원천은 `_hr_resolve_vertical_group`(9)(부록 A M14). 이 계수는 `ast.Name` 참조만 센 것이다 -- PLAN-LAYER 정식 계수는 D0a 도구가 낸다.

### 6.2 규칙(우선순위 높은 것이 이긴다. 도구가 행마다 근거 규칙 ID를 남긴다)

* **A-1 계획 명시**: N3.10 표 '대표 대상' 열에 이름이 있으면 그 MOD. 계획 532행(`canonical_spec`/`SPECS`는 하네스에 남음) 포함.
* **A-2 데이터 레코드 하강**: dataclass·예외·결과 레코드(`Transistor`, `SizingContext`, `InfeasibleSizingError`, `*Verdict` 등)는 그것을 만들거나 받는 정의가 배정된 MOD 중 **가장 낮은 번호**로.
* **A-3 계층 강제**: 쪼개라고 적힌 16행은 쪼개지 않고 **피참조 전부를 담을 수 있는 가장 낮은 MOD**로 통째로 보낸다(쪼개기는 그 셀이 적은 담당 Phase). A-1과 충돌하면 N3.10 표를 고친다(D-11). 계산으로 드러난 충돌: `load_topology`(표 MOD2)가 구조 자동채움(`propose_device_roles_gap_fill` → `find_matching_candidates`·`find_structural_symmetry_candidates`)을 부른다(부록 A M15 `stick_diagram:8550-8739`) → MOD3. `validate_theta_declaration_order`(표 MOD2)가 `_build_shared_current_joint_plan`·`_shared_current_groups_from_compensation`을 부른다(`sizing_recipe:6296-6388`) → 그 둘의 MOD 이상. `optimize_full_circuit_budget`(표 MOD6 '탐색부')는 `stick_diagram` 레이아웃 함수 8개와 `run_topology_pipeline_with_finger_fixup`(MOD8)을 부른다(`sizing_recipe:9075-9527`) → Phase 3 위치 MOD8(D-3), 탐색부 추출 뒤 MOD6(CC-7, `00-common` 435행과 일치).
* **A-4 레지스트리 열**: 위에 걸리지 않으면 열의 MOD 이름. 옛 이름: `optimizer`(`optimizer(S3 …)` 포함) → MOD6(책임 '실패 캐시, 시작점, 전역 샘플, S3', 526행), `〃` → 위 행, `_metric_*`·metric 레지스트리 → MOD5(525행 'metric 레지스트리').
* **A-5 미배정**: 행이 없는 정의와 최상위 대입은 **그것을 참조하는 정의 중 가장 낮은 MOD**로(상수·레지스트리 dict는 소비자를 따른다). 소비자가 없으면 원래 파일 이름을 목적지로 보고하고 **도구가 FAIL**한다(조용한 기본값 금지) -- D0b에서 사람이 규칙을 더하거나 N3.10 개정으로 닫는다.
* **결과 조건**: A-1~A-5 적용 뒤 PLAN-LAYER exit 0이어야 레지스트리 열을 갱신한다(D0b).

### 6.3 도구 `tools/migrate/move_plan.py`(D0a)

| 명령 | 입력 | 출력(JSON 한 줄, exit 0 PASS / 1 FAIL / 2 입력 오류) |
|---|---|---|
| `plan` | `--root`, `--registry`, `--plan`(N3.10 표를 `import_layering.mod_table`로 읽는다) | 정의 → MOD 배정과 근거 규칙, PLAN-LAYER 위반·모듈 순환, 미배정(A-5 FAIL), 모듈별 재수출 목록, card 순서(번호순, ORDER가 성립하는지) |
| `check` | `--root`, `--base`, `--head`, `--card MODn`, `--registry` | MOVE-AST (a)(b)(c)와 ORDER: G1 `moved_defs` 목록 = 이관표의 card 배정 집합, 대상 def 0, 정의 밖 변경이 import·옮긴 문장뿐, 새 MOD 파일의 엔진 import ⊆ 작은 번호 |

PLAN-LAYER 참조는 `reachability._refs`로 뽑고 해석은 **정밀하게**(같은 파일 최상위 바인딩, 엔진 모듈 `from` import, 엔진 모듈 별칭 속성) 한다. `build_graph`의 과대 근사(해석 못 한 이름 → 같은 이름의 모든 def)는 도달 판정에는 안전한 쪽이지만 계층 판정에는 거짓 위반을 만든다. 문자열 참조(`str`)와 임의 속성(`attr`)은 import를 만들지 않으므로 계층 참조가 아니다.

---

## 7. 계약 test와 호출부

### 7.1 위치에 묶인 계약 test(실측 cd64170, 부록 A M24)

`A/tests/contracts/`에서 엔진 파일·모듈 이름을 **실제 트리 판정에** 쓰는 곳(합성 소스 문자열 안의 `import sizing_recipe`는 입력이라 제외 -- `test_reg_check.py`·`test_probe_dup_scan.py`·`test_d_*`의 합성 케이스):

| 군 | 깨지는 시점 | test(줄) | 처리 |
|---|---|---|---|
| **A. 정의가 특정 파일에 있다고 가정** | 그 정의를 옮기는 첫 M card | `test_ic5.py:47-69`(`_DOMAIN_TABLE` 키 = (파일 이름, 함수) 21개 -- 옮기면 '대상에 없다' FAIL), `test_dup_w_calc.py:442`(`size_transistor` 정의를 `sizing_recipe.py`에서 찾음 → M4에서 FAIL), `test_ts6_dead_probes.py:221-222`(`_L_ROLE_MULTIPLIERS` 바인딩 검사 범위가 `sizing_recipe.py` 한 파일 -- 옮긴 뒤 **조용히 공허**), `:261-262`(`audit_vsb_consistency`의 운영 호출자를 `sizing_recipe.py`에서만 찾음 → 호출자 `_build_theta_evaluator`가 MOD6로 가면 FAIL) | **T0**(M1 전) |
| **B. 모듈 이름으로 import·파일 존재 앵커** | shim 삭제(F2) 또는 호출부 갱신(F1) | `test_d_delete_dead.py:74·98-101·201·286·295`, `test_d_delete_telescopic.py:108-117·155·233`, `test_d_move_tests.py:69·73`(`regression_runner`가 `sizing_recipe`를 import해야 함 -- F1이 그 import를 바꾸면 FAIL), `test_dup_w_calc.py:56·72-75`, `test_df35_harness_paths.py:206`, `test_ts6_probe_relocate.py:528`, `test_ts6_dead_probes.py:229`, `test_restore_plan_functions.py:54·113-140`, `test_ic3.py:107·271`(`from stick_diagram import load_topology …`), `test_df36_instance_relpath.py:76·87·237·274·288`(`from stick_diagram import save_instance_json`) | **F1**(호출부 갱신과 같은 card, test 쪽) |
| **C. test 파일 이름 목록** | T1 | `test_ts3_no_print_verdicts.py:29-30` `_LEGACY_SCRIPTS` | **T1** |

A군만 T0에 둔다(최소 수정 -- 이동을 막는 것만 먼저 고친다). B군은 shim이 살아 있는 동안 통과하고, 계획 534행이 '추적 파일 호출부 갱신'을 shim 삭제 조건으로 적었으므로 F1이 import를 목적 모듈로 바꾼다. 스캔 범위가 이미 `A/*.py` 전체인 판정(`_engine_files()` glob, GONE 검사)은 새 MOD 파일을 자동으로 포함하므로 고치지 않는다.

**T0의 해석 규칙 R-DEF**: 이름 n의 정의 파일 = `A/*.py`(하위 디렉터리 제외)와 `workspaces/run_harness.py` 중 최상위(메서드는 `Class.method`)에서 n을 def·class·대입으로 **바인딩**하는 파일(AST, import로 받은 이름은 정의가 아니다 -- shim 재수출은 정의가 아님). 정의 파일이 정확히 하나가 아니면 FAIL(0 = 공허, 2 이상 = 모호·사본). 이 규칙은 **판정 범위를 넓힌다**(한 파일 → 엔진 전체).

### 7.2 추적 호출부(F1 대상, 실측 cd64170, 부록 A M22)

엔진 4모듈을 줄 머리 `import`/`from`으로 가져오는 추적 `.py` 86개: `A/` 루트 4(엔진·도구), `A/tests/unit` 10, `A/tests/probes` 27, `A/tests/contracts` 3(줄 머리 import; 문자열 import까지 B군 10개), `A/tests/tools` 2, `A/tests/conftest.py` 1(`build_toy_lut` -- conftest 변경은 V5 무조건 승인 대상), `workspaces/run_harness.py` 1, `workspaces/current-reuse-telescopic-ota-report/**` 27, `workspaces/two-stage-ota-report/**` 4, `.ai/verification/**/scripts` 6, `docs/03-analysis/**` 1. 추적 안 된 `workspaces/*.py` 1개(`smoke_run_harness_session18_save.py`).

---

## 8. 역할별 산출물 -- spec card 목록 (N9.2-5)

card 단위는 N3.12.3(674행: 이동은 모듈 하나가 한 건). 판정 유형은 **커밋 모양이 정한다**(code 커밋이 없으면 test-only, 있으면 red-green 또는 equivalence -- `20-dead-code-dup` §8 P2·P7 정정, `20260923-probe-promote-clean` 13행).

| # | id(초안) | 대상 | 판정 유형 | oracle | 원칙 제약 |
|---|---|---|---|---|---|
| **G1** | `p3-gate-move-aware` | `tools/gates/reachability.py`(`moved_defs`·해시 정의), `mutate_changed.py`(V3 대상 선택), `source_lint.py`(V6 비교 기준), redteam 새 케이스, design 05 §10 V3·V6·V7 행 문구 | red-green, `gate_change: yes`, phase 0.5(05 §18) | (a) 합성 저장소: 해시 같은 이동 = 제외(base 도구 FAIL → red), 옮기며 바뀐 def·복사·래퍼·모호 원본·캐시 맥락 이탈 = 지금처럼 대상 | 약화 금지(M-1~M-3), `moved` 출력, 해시 정의 하나, 실행당 색인 1회, B28 뒤 base |
| **T0** | `p3-tests-location-free` | §7.1 A군 3파일을 R-DEF로 | **test-only**(code 커밋 없음) + V5 승인(문자열 상수 변경) | (c) base 트리 결과 동일 + (a) 합성 이동 트리에서도 PASS(옛 test는 FAIL) | 판정 범위를 좁히지 않는다(한 파일 → 엔진 전체), 정의 파일 유일성 |
| **D0a** | `p3-move-plan-tool` | 새 `tools/migrate/move_plan.py`(`plan`·`check`) | red-green | (a) 합성 엔진 트리·합성 레지스트리·합성 N3.10 표 | 배선: D0b 계약 test·M card commands·DoD E2. G1 뒤 base(`check`가 `moved_defs`를 부른다) |
| **D0b** | `p3-registry-dest` | 레지스트리 목적지 열 전 행 = MOD 이름 하나(+ 근거 규칙 열), §7 `보류(Phase 3)` 9행 처리 열 = U-02 문언대로 `보류(Phase 4)`, 새 계약 test `contracts/test_p3_registry_dest.py`(레지스트리 열 = `move_plan plan` 출력, PLAN-LAYER 0) | red-green(test가 base 열에서 FAIL) | (d) 도구 출력 = 열 | 손으로 쓰지 않는다(도구 출력). N3.10 표 개정은 이 design 승인(D-11) |
| **M1**~**M6**, **M8**, **M9** | `p3-move-mod<n>-<이름>` | 이관표 MODn 배정 전부(파일:줄은 D0b 뒤 도구 출력) | equivalence(test 커밋 0 가능 -- 05 §9.2 289행) | (c) MOVE-AST + E-LIB·E-INST + SHIM + CACHE-ID | G1·T0·D0b 뒤. 작성 전 실측은 이관표 한 벌로 한꺼번에 뽑는다 |
| **M7** | `p3-mod7-residual` | `stick_diagram.py`에 레이아웃만 남았는지 -- 이동 없음 | M2·M3·M9에 흡수(빈 card 금지) | -- | -- |
| **M10** | `p3-mod10-entry` | 새 `gmid_design_pipeline.run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)`, 하네스 `run()`이 부른다 | equivalence(E-INST) -- 추출이라 V3 대상 | (c) E-INST·E-LIB, ENTRY | 만들면 배선: 하네스 즉시 호출, `after_phase3` 루트 |
| **T1** | `p3-test-relocate` | `unit/test_selftest_*.py` 4개 → `unit/test_mod*.py`, C군, 새 C9 매핑 | test-only + V5 승인(파일 이동 = test 함수 삭제 패턴) | (c) 수집 test id 집합 = 매핑 | `10-test-separation` 413행 |
| **F1** | `p3-callers-update` | §7.2 추적 호출부 import를 목적 모듈로(D-9 제외 집합 밖), B군 계약 test | equivalence | (c) 호출부 AST가 import 줄 외 동일 + E-INST | test 쪽 문자열 변경은 V5 승인 |
| **F2** | `p3-shim-delete` | shim 3파일 삭제, `stick_diagram` 임시 재수출 제거, REG-DEST | red-green | (a) GONE-SHIM | WP-14(같은 변경 단위에서 옛 경로 삭제 + 레지스트리) |

**card 수 15**(G1, T0, D0a, D0b, M1~M6, M8, M9, M10, T1, F1, F2 -- M7 흡수).

### 8.1 순서와 병렬 준비

```
B28(진행 중) ──> G1 ──> D0a ──> D0b ──┐
T0 ───────────────────────────────────┼──> M1 → M2 → M3 → M4 → M5 → M6 → M8 → M9 → M10 → T1 → F1 → F2
```

* **지금 병렬로 준비 가능(spec card 초안·작성 전 실측)**: G1, T0, D0a. 실행 순서는 G1 → D0a(D0a `check`가 G1의 `moved_defs`를 부른다 -- 같은 개념을 둘로 구현하지 않기 위한 의존), T0는 독립.
* M 순서가 번호순인 이유: 작은 번호부터 만들면 매 card 병합본에서 새 파일이 잔여 shim을 import할 일이 없다(ORDER). M 작성 전 실측은 D0b 이관표 한 벌에서 결정적으로 나온다(card 처리 속도 규칙).

---

## 9. 착수 조건과 사용자 결정 (N9.2-7)

### 9.1 착수 조건

* 공통(N6.1 991행): 이 문서의 사용자 승인(DEC-51), **Phase 2 DoD PASS**(현재 남은 것: P9, P10, DoD E0~E5 -- `.ai/context.md` 기준, P3c 보류 B21).
* U-03(N7.2 1078행): 승인 기록 없음(부록 A M27).
* 게이트 선행: B28 병합, G1 병합.

### 9.2 사용자 결정(진짜 사용자 몫만)

| ID | 결정 | 기본안(원칙에서) | 왜 사용자 몫인가 |
|---|---|---|---|
| **UD-0** | 이 design 승인(DEC-51). §9.3의 기본값과 아래 문서 개정을 함께 덮는다: 계획 N3.10 표(A-3 계산 결과 -- `load_topology`·`validate_theta_declaration_order` 위치, `optimize_full_circuit_budget` Phase 3 위치 MOD8 명시), N3.10 533행에 "V6·V7의 '새'도 같은 규칙" 한 문장, 534행 '추적 파일' 제외 집합(D-9), N3.12.3 test-only 열거에 "Phase 3 T0·T1", `00-common` §3.2 103행·§10.1 431행(D-5), `10-test-separation` §5.6 영역 표(252~274행) '파일' 열을 판정 키가 아닌 설명으로(T0 -- 위치는 R-DEF) | §9.3 | 계획서 표·판정 문구 개정은 승인 대상(0.5 공격 16) |
| **UD-1** | **U-03**: 추적 안 된 `workspaces` 스크립트가 shim 삭제로 깨지는 것을 허용 | 계획 기본안 그대로 -- 추적 파일은 전부 F1에서 import 갱신(`workspaces` 진단 31개 포함), 추적 안 된 1개(`smoke_run_harness_session18_save.py`)는 깨지게 둔다 | 계획이 사용자 결정으로 지정(N7.2), 공유 설정(스크래치 보존) |
| **UD-5** | **G1 게이트 변경 승인**(승인 기록 `target_kind` 게이트 변경, spec card `approval`) | §5 방향 | 판정 기준(게이트) 변경은 사용자 승인(05 §18, B28 선례) |
| **UD-6** | **T0 V5 승인**(test 커밋 뒤 diff 해시로) | 승인 요청 근거: 판정 범위를 넓힘(한 파일 → 엔진 전체) + 유일성 검사 추가, 기대값 불변 | 기준 변경 승인(DEC-40) -- `weakening_diff`가 문자열 상수 변경을 기계적으로 잡는다 |

뒤에 올 같은 성격의 승인(지금 결정할 것 아님): T1·F1의 V5 승인(test 파일 이동·import 문자열), M10 판정 방식(추출 card의 V3 인벤토리 비용이 크면 그 spec card에서 보고).

### 9.3 원칙 유도 기본값(UD-0으로 확정 -- 따로 묻지 않는다)

| ID | 기본값 | 근거 |
|---|---|---|
| D-1 | 평면 배치. B11(`extract_selftest.py:645` 비재귀 glob)은 LAYOUT-FLAT로 해당 없음 | N3.10 표 파일 이름이 경로 없는 이름 |
| D-2 | `topology_library.py`·`design_report.py`도 재수출 shim 경유 뒤 F2 삭제, `stick_diagram` 재수출은 임시 | 파일당 한 책임, WP-14 |
| D-3 | `optimize_full_circuit_budget` → Phase 3 위치 MOD8(통째) | A-3 계산(레이아웃 8 + MOD8 1 참조), `00-common` 435행 |
| D-4 | 쪼개라고 적힌 16행은 통째로(A-3), 쪼개기는 원래 담당 Phase | 533행 이동 전용 |
| D-5 | M10 시그니처 `(spec, *, topology_path, search, output_dir)`, 나머지 인자는 CC-7·CC-8. `00-common` 431행에 `topology_path` 추가, 103행 담당 정정 | 하네스가 topology 경로를 spec 밖에서 넘긴다(`run_harness.py:427·446`), 몸통 추출에 탐색 설정·출력 경로 필요 |
| D-6 | `canonical_spec`/`SPECS`/`_spec_*`는 하네스에 남김(레지스트리 392~395행 목적지 정정) | 계획 532행 |
| D-7 | `move_plan.py`는 `tools/migrate/`(code-author), test는 `A/tests/tooling/`(test-author) | 계획 N3.11 549행, `extract_selftest.py` 선례 -- 초안 v1의 `A/tests/tools/`는 DoD 측정 도구 자리(reg_check) |
| D-8 | `audit_current_forced.py`는 도구로 남기고 `audit_topology`는 A-4대로 | 레지스트리 248·389행 |
| D-9 | GONE-SHIM 제외 집합 = `.ai/verification/**`(판정 기록 스크립트 6개 -- 기록된 base 커밋에서 재실행되는 증거라 고치면 기록이 바뀐다) + `docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`(기준 커밋 78b58c6 실측 원자료) | 기록 불변. 534행 '전부 갱신'의 예외라 UD-0에 문구 개정 포함 |
| D-10 | 레지스트리 §7 `보류(Phase 3)` 9행은 **옮기고 D 유지**, 처리 열 `보류(Phase 4)` | U-02 승인 `20260923-u02-d-list` 1항 "보류(Phase 3 모듈 이동·Phase 4 배선)" -- 이미 승인된 처리다. ★ `find_diode_stacks`의 회로 해석 공동분석 표기는 그대로 옮긴다(이동은 정본 확정이 아니다) |
| D-11 | N3.10 표 개정은 A-3 계산 결과를 그대로(대안인 함수 분할은 533행 위반) | §6.2 |
| D-12 | T0 = A군 3파일만, B군은 F1 | 최소 수정, 534행 '호출부 갱신' |
| D-13 | G1은 B28 병합 뒤 base, 해시 정의는 `reachability`로 옮겨 하나 | §5.3, 정의 하나 원칙 |
| D-14 | references 문서(`function-selection-map.md` 등)의 모듈 위치 안내는 F2에서 grep 목록만 보고, 갱신은 B22 별도 card | B22가 이미 그 card |

---

## 10. DoD 측정 명령 (N9.2-6)

auditor가 Phase 3 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT`는 `10-test-separation` §10 정의를 그대로 쓴다. `$PY` = `C:/Python314/python.exe -B`.

| ID | N6.2 `3` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | MOD1~MOD10 존재 | `$PY <iso>/tools/gates/import_layering.py --root <iso>` 출력 `present` | `present`가 N3.10 표 10행 전부(표는 도구가 계획서에서 읽는다 -- 목록을 손으로 쓰지 않는다) |
| E1 | import 계층 위반 0 | 같은 명령 | exit 0, `findings` 0 |
| E2 | 이동 커밋마다 AST 해시 동일 | M card마다 `$PY <iso>/tools/migrate/move_plan.py check --root <iso> --base <card base> --head <card 병합 커밋> --card MODn --registry <iso>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 그리고 각 M card 판정 기록의 V3 JSON `moved`·`targets` | 전부 exit 0, V3 `targets`의 소스 def 0(M10 제외) |
| E3 | `sizing_recipe.py` 삭제 | `git -C <iso> cat-file -e HEAD:skills/analog-gmid-design/assets/sizing_recipe.py`(실패해야 함) + `git -C <iso> grep -l -E "^[[:space:]]*(import|from)[[:space:]]+(sizing_recipe|topology_library|design_report)\b" -- '*.py'` | 첫 명령 exit ≠ 0, 두 번째 결과 ⊆ D-9 제외 집합 |
| E4 | 레지스트리 목적지 = 실제 위치 | `PT <iso>/skills/analog-gmid-design/assets/tests/contracts/test_p3_registry_dest.py`(D0b) + `$PY <iso>/tools/migrate/move_plan.py plan --root <iso> --registry … --plan <iso>/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` | test PASS, 도구 exit 0(미배정 0, 위반 0, 모든 정의의 배정 MOD = 실제 파일) |
| E5 | 동작 보존(N6.3) | `PT` 전체 + E-LIB·E-INST 재측정 | Phase 2 DoD와 같은 해시 |

---

## 11. 열린 질문 (N9.2-8)

없다. §9.2의 UD는 착수 전 사용자 결정 대기 항목이다. 이 초안이 드러낸 **계획·문서 개정 요청**(UD-0에 포함):

1. 레지스트리 목적지 열이 N3.10 이전 판 이름을 쓴다(§6.1) -- 517행 "레지스트리 열이 정본"은 D0b 재생성 뒤에 성립한다.
2. N3.10 533행의 이동 제외가 V3에만 적혀 있다 -- V6·V7도 같은 규칙이어야 이동 card가 판정 가능하다(§5.1 실측).
3. N3.12.3 test-only 열거(TS0·TS2·TS3·TS5·TS7, TS6 승격·삭제, redteam 데이터 게이트 변경)에 Phase 3 T0·T1이 없다 -- 판정 유형은 커밋 모양이 정한다는 P2 교훈대로 열거에 더한다.
4. 534행 '추적 파일 전부 갱신'과 판정 기록 불변(D-9)의 충돌.
5. `00-common` §3.2 103행과 §10.1 431행의 MOD10 인자 담당, 431행 시그니처에 topology 경로 인자가 없음(D-5).

---

## 부록 A. 측정 명령과 결과 (모두 읽기 전용, gate `master` `cd64170`)

`R` = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `D` = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts`, `$PY` = `C:/Python314/python.exe -B`. v1 스크립트(`p3_*.py`)는 `C:/g20`에서 출력 경로만 바꾼 사본으로 재실행(끝나고 삭제).

| # | 명령 | 결과 |
|---|---|---|
| M0 | `ls R/docs/02-design/features/ \| grep gain` | 00·05·10·20 네 개(30 없음) |
| M1 | `sed -n 985,1020p R/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` | 1000행 Phase 3 행, 1018행 DoD |
| M2 | `git -C R log --oneline 070cf69..cd64170` | 8커밋 -- 엔진 변경은 `ed98d35`(DF-36, `stick_diagram.py` +17줄, `_topology_ref_relpath` 신설)뿐 |
| M6 | `wc -l R/skills/analog-gmid-design/assets/*.py`; `$PY p3_measure.py` `toplevel_counts` | SR 12015줄(Class 13·Func 174·Assign 30), SD 9035줄(Class 28·Func 132·Assign 8), TL 7, DR 5+1 |
| M9 | 같은 JSON `registry_dest_mod_counts` | §6.1 분포(열 미매핑 62, MOD1·5·6 0행) -- v1과 같음 |
| M10 | 같은 JSON `plan_rep_vs_registry` | §6.1 |
| M11 | v1 M11 awk 명령 | 16 |
| M12 | 같은 JSON `coverage` | SR 3, SD 24 미등록(v1은 23 -- DF-36 `_topology_ref_relpath`) |
| M13 | `$PY p3_assign.py` `unassigned` | 34 |
| M14 | 같은 실행 `upward`, `upward_by_pair`, `upward_by_from` | 64, §6.1 쌍별 분포 -- v1과 같음 |
| M15 | `$PY p3_refs.py` | `optimize_full_circuit_budget` 9075-9527(SD 8개 + SR 12개 참조), `load_topology` 8550-8739, `validate_theta_declaration_order` 6296-6388, `_build_theta_evaluator` 7930-8933 |
| M18 | `grep -n "^\s*global "`; `grep -c lru_cache`; 모듈 dict 캐시 grep | 0 / TL 2 / SR 2391·2530·7697 |
| M19 | `sed -n 46,62p;255,375p R/tools/gates/mutate_changed.py`, `sed -n 196,249p R/tools/gates/reachability.py`, `sed -n 212,282p R/tools/gates/source_lint.py` | §5.1 표 줄 번호 |
| M20 | `sed -n 1,100p R/tools/gates/import_layering.py` | 표 ∩ 존재 파일만, 표 밖 파일 import는 보지 않는다(ORDER가 별도 필요한 이유) |
| M22 | `git -C R grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|stick_diagram\|design_report\|topology_library)\b" cd64170 -- '*.py'` 디렉터리별 집계 | §7.2(86개 -- v1 대비 `.ai/verification` 4→6, contracts 2→3) |
| M23 | `git -C R status --porcelain -- workspaces` | 추적 안 된 `.py` 1개 |
| M24 | `git -C R grep -c -E "(sizing_recipe\|stick_diagram\|topology_library\|design_report\|audit_current_forced)\.py" -- A/tests ':!A/tests/probes'` + 파일별 `grep -n` 문맥 확인 | §7.1 A·B·C 군. `test_reg_check.py`(13)·`test_probe_dup_scan.py`·`unit/test_selftest_*`의 언급은 합성 입력·주석 |
| M25 | `grep -n "tools/gates\|CLASS_GLOBS" R/tools/gates/role_paths.py` | `tools/**` = tool, `tools/gates/`(redteam 제외) = 게이트 코드, `A/*.py` = source(새 MOD 파일 포함) |
| M27 | `ls R/.ai/approvals \| grep -i -E "u03\|u-03\|30-module\|phase3\|p3-"` | 0건 |
| G1 | `$PY D/p3v2_g1_measure.py` 결과 `G1`(엔진 4파일 각각을 base 없는 새 파일로 볼 때 `mutate_changed.changed_defs(None, src)`·`mutants`, `source_lint.compare(p, None, src, set())`) | 대상 def 473, 변이 15,677(SR 8,874·SD 5,933·TL 683·DR 187), V6 새 항목 SR magic 268·continue 187·broad_except 8·id_call 6, SD magic 195·continue 158, TL magic 34, DR magic 3·continue 2. 대조: 같은 경로 무변경 `changed_defs(src, src)` = 0 |
| G2 | 같은 실행 `G2`(HEAD 트리 `build_graph` + `gate_config.json` 루트 `reach`) | 엔진 4파일 def 473 중 미도달 109(승인 면제 1 → 108). 표본 `SemiEmpiricalGmIdLUT.__init__`, `_feed_root_ratio` 등(§5.4) |
| G3 | 같은 실행 `G3`(합성 git 저장소, 임시 디렉터리를 끝나면 지움: `a.py`의 `f`(광범위 except + 리터럴 3.7)를 바이트 그대로 `b.py`로 옮기고 `a.py`는 `from b import f`만) | base `reachability.py` exit 1 `new_defs: [b.py::f]`, base `source_lint.py` exit 1 `broad_except`·`magic_number` 새 항목 |
| G4 | `git -C R grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` | 게이트 밖 호출: `.ai/verification/20260930-df36-instance-relpath/scripts/mut_def.py:67`·`probe_t2_vs_1st_survivor.py:16`, `.ai/verification/20260930-dup-w-calc/scripts/v3_baseline_probe.py:17` -- 시그니처 유지 필요 |

측정 한계: M14는 초안 배정 기준·`ast.Name` 참조만. G1은 '파일 전체가 새 파일'인 상한(실제로는 모듈 하나씩 옮기므로 card별로 나뉜다).

## 부록 B. 초안 v1(`draft_phase3_design.md`, 070cf69) 대비 정정

| # | v1 | v2(재측정) |
|---|---|---|
| 1 | 파일 이름에 묶인 계약 test 8개(test_ic5·d_delete_dead·d_move_tests·dup_w_calc·df35·d_delete_telescopic·ts6_dead_probes·ts3)를 T0 대상으로 | **깨지는 시점으로 나누면 A군 3파일만 이동을 막는다**(test_ic5, dup_w_calc:442, ts6_dead_probes:221·261). v1 목록에 없던 `test_ts6_probe_relocate:528`, `test_restore_plan_functions:54·113-140`, `test_ic3:107·271`, `test_df36_instance_relpath`(DF-36 신설)는 B군(F1). `test_ts6_dead_probes:261` 운영 호출자 검사는 v1이 놓친 FAIL 지점, `:221`은 FAIL이 아니라 **조용한 공허** |
| 2 | UD-2(`.ai/verification` 4개) 사용자 결정 | 6개(DF-36 추가). 판정 기록 불변 원칙으로 기본값 D-9(UD-0에 포함) |
| 3 | UD-3(`보류(Phase 3)` 9행) 사용자 결정 | U-02 승인 1항이 이미 "보류(Phase 3 모듈 이동·Phase 4 배선)"로 덮는다 → D-10 |
| 4 | UD-4(N3.10 개정) 별도 결정 | 계산 결과라 design 승인(UD-0)에 포함 |
| 5 | 도구 `A/tests/tools/move_plan.py`·`move_ast_check.py` 두 개 | `tools/migrate/move_plan.py` 하나(`plan`·`check`) -- 이동 판정은 G1 `moved_defs` 재사용(정의 하나), 계층은 `import_layering.mod_table`·`reachability._refs` 재사용 |
| 6 | PLAN-LAYER를 `reachability.build_graph`로 재측정 | `build_graph`의 과대 근사는 계층에 거짓 위반 -- 정밀 해석으로 |
| 7 | G1 = "base 전 파일에 해시 같은 정의가 있으면 옮긴 정의" | 복사·래퍼·모호 원본을 걸러야 약화가 아니다(M-1~M-3). V6는 '제외'가 아니라 '비교 기준 이동'(원본 맥락 항목 수), 캐시 맥락 이탈은 계속 FAIL. `changed_defs`·`def_hash` 시그니처 유지(판정 기록 스크립트 3곳) |
| 8 | G1과 B28 관계 "B28 병합 뒤" | 편집 지점을 분리해 명시(§5.3): B28 = 실행 환경(285·328~342·364행), G1 = 대상 선택(326행 앞)·출력 |
| 9 | card 17개 | 15개(M7 흡수, D0a 도구 하나) |
| 10 | E0 명령에 모듈 목록을 손으로 적음 | `import_layering` `present`로(계획 표에서 읽음) |
| 11 | MOD10 시그니처 D-5 `(spec, *, topology_path, search, output_dir)`(근거 없음) | 같은 시그니처를 유지하되 근거를 실측으로: 하네스가 topology 경로를 spec 밖(`SPECS[…]["topology_file"]`, `run_harness.py:427`)에서 넘기고 `00-common` 431행 정본 시그니처에는 그 인자가 없다 -- 431행 개정 요청(UD-0) |
| 12 | stick_diagram 9018줄, 미등록 23 | 9035줄, 미등록 24(DF-36) |
