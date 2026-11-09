# Phase 3 초안 독립 검토 (design v2 · G1 · T0 · D0a)

검토자: 독립 reviewer(초안 작성자 아님). 기준 HEAD `cd64170`(gate master). 저장소 읽기 전용, 스크래치 `C:/g24`(끝나고 삭제).
`$PY` = `C:/Python314/python.exe -B`, `R` = chip-design-skills 루트, `A` = `skills/analog-gmid-design/assets`.

요약: **blocking 6 · should-fix 13 · minor 8**. 사실 문장은 대부분 재측정으로 맞았다(부록 1). 결함은 주로 (1) G1 이동 규칙 M-1~M-3의 **약화 반례 3종**, (2) D0a `plan`의 Phase 진행 중·후 동작 미정의로 배선(D0b test, DoD E4)이 깨짐, (3) DoD E2가 V3 JSON의 엉뚱한 필드를 잰다는 것이다.

---

## 1. 발견 표 (심각도 순)

### Blocking

| # | 대상 | 발견 | 증거(명령 → 결과) | 고칠 것 |
|---|---|---|---|---|
| B1 | G1 §3 MOVED, G1 계약 1·5 | **덮어쓰기가 '이동'으로 분류된다(약화).** base에 `a.py::f`(H1)와 `b.py::f`(H2)가 있고 head에서 a.f를 지우고 b.f를 H1 본문으로 바꾸면 M-1(H1인 원본이 a.py 하나)·M-2(a.py에 f 없음)·M-3(H1이 b.py 한 곳) 모두 성립 → b.f는 V3 대상에서 빠진다. 지금 도구는 같은 경로 해시가 달라 대상이다. b.f의 모든 호출자에게 동작이 바뀌고 옛 H2 본문은 사라지는데 V3·V6·V7 어디서도 안 보인다. D0a `check`의 `changed`(옮긴 정의 제외)·`lost`(같은 자리 (p,q) 존재)도 못 잡는다. | `$PY C:/g24/ce_moved.py`(M-1~M-3를 문자 그대로 구현 + `mutate_changed.changed_defs`) → `CE1_overwrite_existing_same_name`: `moved = {b.py::f ← a.py::f}`, `old_V3_targets = [b.py::f]`, `new_V3_targets = []` | **M-0 추가**: "base에서 p_h가 q를 정의하지 않는다(p_h가 base에 없거나 q가 없음)". 계약 5에 (f) 덮어쓰기, 계약 10에 redteam 단계 `overwrite`(V3 exit 1, base도 1) 추가. D0a `lost`는 (p,q,해시) 기준으로. |
| B2 | G1 §3 MOVED, design §3 MOVE-AST (c), D0a `non-import-diff` | **자유 이름 재바인딩이 '이동'으로 분류된다(약화).** `f(){return helper()}`를 AST 그대로 b.py로 옮기면서 b.py에 `from c import helper`(다른 helper)를 두면 f는 MOVED → V3 제외, MOVE-AST (c)는 import 변경을 허용하므로 D0a도 통과. 해시 같은 def의 **실행 환경(모듈 전역)이 통째로 바뀌는 것**이 이동의 본질이라 같은 경로 무변경과 강도가 같지 않다. 저장소 실례: `stick_diagram.py:8973`(`_topology_ref_relpath`)·`:1050`이 `__file__`로 저장소 루트를 계산 -- 다른 디렉터리(예: `workspaces/run_harness.py`, 소스 분류임)로 옮기면 AST 동일·동작 변경. | `ce_moved.py` → `CE2_rebind_free_name`: moved `{b.py::f}`, new_V3_targets `[]`(old는 `[b.py::f]`). `grep -n "__file__" A/{sizing_recipe,stick_diagram,topology_library,design_report}.py` → `stick_diagram.py:1050`, `:8973` | **M-4 추가**: 옮긴 정의가 읽는 전역 이름(`reachability._refs`의 `name`·`modattr`)마다 head p_h에서의 바인딩 출처 = base p_b에서의 바인딩 출처(같은 (파일, 이름)이거나 이 커밋에서 함께 옮긴 것, 또는 p_b 모듈을 경유한 재수출). 아니면 이동 아님. `__file__`·`__name__`·`globals()`·`sys.modules`를 읽는 def는 디렉터리가 같을 때만 이동. 계약 10에 `rebind`·`dir-change` 단계. D0a `check`에 `rebind` 발견. |
| B3 | G1 계약 1(최상위 문장에서 class 제외), design §3 MOVE-AST (a), D0a 계약 4 | **클래스가 이동 판정에서 빠진다.** `iter_defs`는 함수만 내고(클래스는 재귀만), G1은 최상위 문장에서 class를 뺀다. 그래서 (i) 메서드 없는 클래스 36개(SR 10: `SizingResult`·`SizingContext`·`QuasiStaticVerdict` …, SD 26: `*Verdict`·`DiodeStack` …)는 MOVED에 영영 안 나타나 MOVE-AST (a) '배정 집합 = 옮긴 집합'이 정의되지 않고, (ii) 클래스 머리(부모·데코레이터)·필드 기본값을 바꾸며 옮겨도 메서드는 MOVED로 V3 제외된다(CE4). 계획 533행 '무변경 증명'이 클래스에는 성립하지 않는다. | `$PY C:/g24/classes.py` → `sizing_recipe classes 13 no_methods 10 … with class-level stmts 8`, `stick_diagram classes 28 no_methods 26 … 28`. `ce_moved.py` → `CE4_class_header_changed_methods_moved`: moved `{b.py::C.m}`, new_V3_targets `[]` | 클래스 골격 단위 추가: ClassDef에서 메서드 본문을 뺀 `ast.dump` 해시(머리·데코레이터·클래스 수준 문장 포함)를 MOVED 단위로. 메서드는 **감싼 클래스 골격이 함께 이동**했을 때만 이동. `moved` 출력에 클래스 항목. MOVE-AST (a)의 집합 원소를 '최상위 이름(함수·클래스·대입)'으로 명시. |
| B4 | D0a 계약 1·8·9, design §2.4·§8 D0b·§10 E4 | **`plan`이 이동 중·후 트리에서 무엇을 내는지 정의되지 않아 배선이 깨진다.** `plan`은 `--split` 파일의 정의만 배정한다. (i) M1 뒤에는 옮긴 정의가 `--split` 밖(MOD 파일)에 있어 배정 출력에 없다 → D0b 계약 test "레지스트리 열 = `plan` 배정"(매 card V1 실행, 계약 9)이 M1부터 FAIL. (ii) F2 뒤에는 `--split` 파일이 없어 계약 1대로 exit 2 → DoD E4 "도구 exit 0"이 구조적으로 불가능. | D0a 계약 1 "2 = 입력 오류(파일 없음 …)", design §10 E4 `move_plan.py plan … 도구 exit 0`, design §7.2/F2 GONE-SHIM(삭제). | `plan`에 규칙 **A-0 현재 위치**: N3.10 MOD 파일에 이미 있는 정의는 그 파일로 배정(근거 `A-0`), `--split` 파일이 없으면 오류가 아니라 빈 입력. 또는 REG-DEST 전용 `verify` 부명령(레지스트리 열 = 실제 정의 파일)을 두고 D0b test·E4가 그것을 부르게. |
| B5 | design §10 E2 | **E2가 잴 수 없는 것을 잰다.** "V3 `targets`의 소스 def 0" -- V3 JSON `targets`는 **파일 경로 목록**(diff `--diff-filter=AM`의 소스 `.py`)이다. 이동 card에서는 새 MOD 파일과 원본 파일이 항상 들어 있어 이 기준은 def 수를 재지 못하고 문자 그대로 읽으면 항상 FAIL. | `sed -n 277p;365,366p tools/gates/mutate_changed.py` → `targets = [p for p in diff.splitlines() if … rch._is_source(p)]`, 출력 `{"tool": "V3", …, "targets": targets, "mutants": …}` | 기준을 "V3 `mutants` = 0 그리고 V3 `moved` 집합 = `move_plan check`가 대조한 card 배정 집합"으로. G1 계약 2에 V3 JSON 필드 `moved`와 함께 `defs`(대상 qualname 목록)를 더하면 더 직접적이다. |
| B6 | design §3·§6.3·§10 E2 vs D0a 계약 1·4 | **CLI가 두 문서에서 다르다.** design §6.3·E2: `check --root --base --head --card MODn --registry`, `plan --root --registry --plan`. D0a: `check … --card <MOD 파일> --plan … --registry … --split … --keep … [--aliases]`. E2 명령 그대로면 필수 인자 누락으로 exit 2. auditor가 DoD를 실행할 수 없다. | 두 초안 대조(design 169·276행, D0a 26·37행) | design §6.3 표와 E2·E4 명령을 D0a 계약의 CLI로 맞추고 `--split/--keep/--aliases` 값(§2.1 파일 목록, `optimizer→theta_search`)을 E2·E4에 적는다. 한 곳(D0a)만 정본으로 두고 design은 인용. |

### Should-fix

| # | 대상 | 발견 | 증거 | 고칠 것 |
|---|---|---|---|---|
| S1 | G1 계약 10 | 단계별 '해당 도구'·기대 exit가 test-author가 결정할 수 있게 적혀 있지 않다. 예: `wrapper`는 원본 자리 래퍼가 운영 루트에서 도달하면 새 def도 도달해 V7 exit 0이다. `cache-together`의 base red는 캐시 때문이 아니다 -- 새 파일에 캐시와 `len()` 검사가 함께 있으면 base V6도 `unbounded_cache`를 내지 않는다(`source_lint.py` `unit_features`: `len(name)`을 **파일 전체 텍스트**에서 찾음). red는 다른 항목(리터럴 등)에서 나와야 한다. | `sed -n 129p tools/gates/source_lint.py`(len 검사 = `module_text`, 파일 전체) | 단계 × 도구(V3/V6/V7) × base exit × head exit × 그 exit를 만드는 픽스처 성질(인벤토리 없음·미도달·광범위 except·리터럴) 표로. |
| S2 | G1 계약 8 | `cProfile`은 인자를 기록하지 않아 "`read_tree`의 base 호출 1"을 구별할 수 없다. 또 V6는 지금 트리를 통째로 읽지 않는데 `moved_defs` 입력으로 `GRAPH_PREFIXES`(workspaces 보고 스크립트 31개 포함)를 읽으면 불필요한 읽기가 는다. | `grep -n "read_tree\|known_defs" tools/gates/source_lint.py` → V6는 `read_tree` 미사용 | 기준을 도구별 총 호출 수로(V3·V7 `read_tree` 2, V6 ≤2, `moved_defs` 1). `moved_defs` 입력은 소스 분류 파일만(`SOURCE_GLOBS`로 `ls-tree`) 읽게 명시. |
| S3 | G1 계약 1, design §3 MOVED | 최상위 문장의 식별자(q)가 정의되지 않았다. 출력 키 `<module>:<줄>`은 이동 뒤 바뀌므로 M-1~M-3의 'q'로 쓸 수 없다. 같은 파일에 같은 문장이 둘일 때의 처리도 없다. | G1 17~18·33~34행 | 문장 식별 = `ast.dump` 해시만, 한 파일 안 중복·base 여러 파일 = 모호(이동 아님)로 명시. |
| S4 | G1 계약 11, 결정 필요 항목 | 문서 개정(design 05 §10 V3·V6·V7 행, 계획 533행)이 '오케스트레이터 문서 커밋'으로만 적혀 있고 승인 전후가 불명. B28 선례는 spec card와 design 05 개정을 **승인 전에 커밋**해 승인 기록 `diff_path`에 넣었다. | `.ai/approvals/20260930-v3-history-clone.md` → `diff_path: …05-role-separation.design.md`, `diff_path: …spec.md` | "문서 개정은 spec card와 같은 커밋(승인 전), 승인 `target_kind: diff`가 spec card·design 05·계획서 세 경로를 덮는다"로. |
| S5 | D0a 계약 2·5 | A-1은 N3.10 '대표 대상' 열이 필요한데 `import_layering.mod_table`은 `{파일 줄기: MOD 번호}`만 돌려준다. "MOD 표는 `mod_table`"만으로는 A-1을 구현할 수 없고, `mod_table`을 바꾸면 게이트 변경(`tools/gates/*.py`)이 된다. | `sed -n 22,35p tools/gates/import_layering.py` → `ID`·`파일` 열만 | "번호표는 `mod_table`, 대표 대상은 `role_paths.read_section_table(plan, "### N3.10 ")`의 `대표 대상` 열"로 명시(게이트 코드 무변경). |
| S6 | D0a 계약 3 | `reachability._refs`는 중첩 def 몸체를 건너뛰고(`("nested", name)`만), 클래스를 넘기면 메서드 몸체도 건너뛴다. 최상위 정의 단위로 그대로 부르면 중첩 함수·메서드가 만드는 참조가 빠져 PLAN-LAYER가 거짓 PASS → M card에서야 import 오류. | `sed -n 69,95p tools/gates/reachability.py` | "최상위 정의 u의 참조 = u 몸체·데코레이터·기본값 + u 안 모든 중첩 def·메서드·클래스 수준 문장의 `_refs` 합집합"으로 명시, 합성 test에 중첩 함수만 상위 참조하는 경우. |
| S7 | D0a 계약 2 A-2 | "dataclass·예외·결과 레코드", "만들거나 **받는** 정의"가 기계 판정 불가. 엔진은 `from __future__ import annotations`(SR:35, SD:32)라 매개변수 주석은 문자열이다. | `head -40 A/sizing_recipe.py \| grep -n __future__` → 35 | 레코드 = `@dataclass` 데코레이터 또는 `Exception` 계열 상속 또는 메서드 없는 클래스. '받는' = 주석 문자열의 식별자 토큰 포함, 아니면 '만드는(호출)'만으로 줄인다. |
| S8 | D0a 계약 7 | 계약은 "문자열 리터럴 없음", auditor 명령은 `git grep`(주석·docstring 포함). 사용 예를 docstring에 쓰면 계약상 통과인데 auditor는 FAIL -- 재시도 원인. | D0a 49~50행 | 둘 중 하나로 통일: "파일 텍스트 전체에 없음"(grep 그대로) 또는 AST `Constant(str)` 검사 명령. |
| S9 | design §10 E2, M card, D0a 배선 | 이동 card의 판정 도구 `move_plan.py`와 그것이 import하는 게이트 모듈을 `<iso>`(병합본 head)에서 실행한다. `tools/migrate/**`는 code-author가 조건 없이 쓸 수 있어(계획 N3.12.2 601행) M card code-author가 같은 card에서 판정 도구를 바꿀 수 있다(작성자≠검증자 위반 경로). `tools/**`는 V3 대상도 아니다. | 계획 601행 `gmid-code-author` `tools/migrate/**` 조건 `없음`; `rch._is_source`는 `A/*.py`·`run_harness.py`만 | M card는 D0a 병합 커밋(또는 gate 캐시)의 `move_plan.py`를 스크래치로 꺼내 실행, 그리고 M card 계약에 "`tools/**` 변경 0". |
| S10 | design §3 CACHE-ID·SHIM(`is` 동일성)·MOVE-TOTAL | 판정식은 있는데 실행 명령·도구가 없다(DoD E0~E5·`move_plan check` 발견 목록 어디에도 없음) → auditor가 판정할 수 없고 '만들면 배선' 위반. 참고: 캐시 3개는 `_KNEE_L_CACHE: dict = {}` 형태(AnnAssign)라 V6 `unbounded_cache`(Assign만 검사)도 보지 않는다. | `sed -n '2391p;2530p;7697p' A/sizing_recipe.py` → `_KNEE_L_CACHE: dict = {}` 등 | `move_plan check`에 `cache`(모듈 캐시 이름을 읽거나 쓰는 def가 다른 모듈에 있음)·`shim-identity`(하위 프로세스 import로 `is` 대조) 발견을 더하고, MOVE-TOTAL은 E2 누적 또는 E4 `verify` 출력으로. |
| S11 | design §7.2·F1 | 추적 probe 6개가 엔진 모듈 속성을 덮어써 계측한다(`sr.X = traced`). 분할 뒤에는 호출자가 다른 모듈의 전역을 보므로 shim이나 정의 모듈 속성을 바꿔도 가로채지 못한다 -- probe는 V1이 수집하지 않아 **조용히** 계측이 비어진다. F1의 oracle "호출부 AST가 import 줄 외 동일"은 필요한 수정을 금지한다. | `git grep -n -E "^\s*(sr\|sd)\.[A-Za-z_]+\s*=[^=]" -- A/tests/probes` → `probe_b22_headroom_attribution.py:104`, `probe_diode_gmid_readiness.py:63`, `probe_diode_pass_skips.py:94`, `probe_diode_window_corner.py:100`, `probe_matching_pair_divergence.py:124`, `probe_vds_assignment_paths.py:47·53·62·73·79`. unit·contracts·conftest에는 0건 | §7.2에 'D군: 속성 덮어쓰기 probe' 6개를 따로 적고, F1에서 덮어쓰기 대상을 **호출자 모듈**로 바꾸는 편집을 허용(또는 probe 처리 방침을 정한다). |
| S12 | design §8 M10, §9.2 뒤 문단 | M10(추출, 새 def)의 판정 유형이 'equivalence'이면서 결정은 뒤로 미뤘다. 규칙으로 정해진다: 새 def는 V3 대상이라 인벤토리 test가 있어야 하고, equivalence는 "test 커밋 불변 + base·병합본 PASS"라 새 def를 부르는 새 test를 둘 수 없다(base에 없음). 기존 harness 경유 test가 인벤토리가 되는지를 지금 재야 한다. | 계획 686·838행, `mutate_changed.py` 인벤토리 없음 → `survived` | M10 spec card 전 실측: `reachability.build_graph`에서 `workspaces/run_harness.py::run`에 도달하는 test 수. 0이면 M10은 red-green(새 test)으로. |
| S13 | T0 작성 전 실측 5 | "`_SIZING_RECIPE` 상수는 229행이 계속 쓰므로 남긴다" -- 사실과 다르다. 229행 test는 `importlib.import_module("sizing_recipe")`를 쓰고, `_SIZING_RECIPE`는 221·222·261·262행에서만 쓰인다(둘 다 T0가 바꾸는 곳). T0 뒤 이 상수는 소비자 0인 죽은 이름. | `grep -n "_SIZING_RECIPE" A/tests/contracts/test_ts6_dead_probes.py` → 60·221·222·261·262 | 문장 정정. 상수는 T0에서 지우거나(계획서 소비자 grep 0 확인) 남기는 이유를 사실대로. |

### Minor

| # | 대상 | 발견 | 증거 | 고칠 것 |
|---|---|---|---|---|
| m1 | design §2.2·부록 M18 | "`topology_library` `lru_cache` 2곳" -- 데코레이터는 1곳(248행), 254행은 주석. | `grep -n lru_cache A/topology_library.py` → 248 `@functools.lru_cache(maxsize=256)`, 254 주석 | "1곳(248행)". |
| m2 | design §5.2 | "`mut_def.py:67` 등 4곳" vs 부록 G4·G1 spec은 3곳. | `git grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` → 스크립트 3개 | "3곳". |
| m3 | design §6.3 vs D0a | `--card MODn` vs `--card <MOD 파일>`(B6과 함께). | -- | 하나로. |
| m4 | D0a 계약 2 A-1 | N3.10 '대표 대상' 칸의 백틱에 식별자가 아닌 것(`∂ID/∂VSB`, `workspaces/…` 경로)과 산문("`save_instance_json` 계열", MOD7 "레지스트리 등급 R0 레이아웃 함수")이 있다. 처리 규칙이 없다. | `sed -n 519,530p` 계획서 | "식별자 패턴(`[A-Za-z_][A-Za-z0-9_]*`, 글롭 `*` 허용)만 A-1 토큰, 나머지는 무시" 명시. MOD7은 A-4로. |
| m5 | D0a 계약 6 | "`ast.parse` 호출 수 = 입력 소스 파일 수"의 '입력 소스 파일'이 `--split`만인지 엔진 전체인지 불명. | -- | 집합을 명시. |
| m6 | T0 계약·D0a 이름 충돌 절 | 새 test·도우미가 피해야 할 토큰(전수 스캔 test 4개의 삭제·이관 이름, print 판정 토큰)을 "쓰지 않으면"이라고만 적었다. test-author가 목록을 알아야 한다. | `test_d_move_tests.py:66` `_MOVED`, `test_d_delete_dead.py` 삭제 이름 | 금지 이름 목록을 card에 적는다. |
| m7 | design §10 E3 | 줄 머리 import만 센다. 문자열 import 10곳(`importlib.import_module("sizing_recipe")`·`_import("sizing_recipe")`)은 잡지 않는다(대부분 B군 계약 test라 V1이 ImportError로 잡기는 한다). | `git grep -n -E 'import_module\("(sizing_recipe\|topology_library\|design_report)"\|_import\("…"\)' -- '*.py' \| wc -l` → 10 | E3에 문자열 패턴 추가. |
| m8 | design §3 MOVED 일반성 | 한 파일 안 같은 qualname 중복(조건부 def)의 처리 미정. 현재 엔진에는 0건이라 실해 없음. | `$PY C:/g24/dupq.py` → 전 파일 `dup_qualnames: {}`, 최상위 블록 안 def 0 | "한 파일에 같은 q가 둘이면 모호 = 이동 아님" 한 줄. |

---

## 2. 항목별 점검 결과(요청 (1)~(7))

**(1) 사실 재측정** -- 불일치는 S13, m1, m2뿐. 나머지는 일치(부록 1).

**(2) 관찰 가능·역할별 판정 가능성**
* G1: 계약 1~7·9는 auditor가 합성 저장소로 판정 가능. 계약 8은 S2, 계약 10은 S1 때문에 기대값이 유일하지 않다. test-author 쓰기 경로(`tools/gates/redteam/**`, 조건 '게이트 변경')와 읽기(게이트 코드는 `tool` 분류라 열람 허용)는 문제없음(`role_paths.py:62-63`, 계획 619행).
* T0: 판정 가능. 도우미 `_engine_defs.py`는 test 분류(`A/tests/**`), 엔진은 test 실행 때 AST로만 읽으므로 DEC-38 열람 거부와 충돌하지 않음. R-DEF 전제(최상위 바인딩 중복 0, ic5 21개 이름이 모든 깊이에서 각 1개, 대상 이름 규칙 전체에서 중복 0)는 재측정으로 확인.
* D0a: `plan`의 이동 중·후 동작(B4), A-2(S7), 참조 집계(S6), 대표 대상 열 읽기(S5) 때문에 test-author가 합성 입력의 기대값을 유일하게 정할 수 없는 곳이 있다.

**(3) 증거 유형 대 규칙**
* G1 red-green·`gate_change: yes`·oracle (a)는 05 §18(555~558행)과 맞는다. red 근거 G3(base V6·V7 exit 1)도 `p3v2_g1_results.json`과 맞는다. 승인은 S4.
* T0 test-only: 계획 687행 열거에 없어서 UD-0 개정이 필요하다는 인식은 맞다. 스키마상 test-only는 `red`·`equivalence` 필드를 가질 수 없다(`_schema.json` allOf 3번째) → 계약 6·7 합성 트리 결과는 V2 `basis` 문장으로만 남는다. 선례 `20260923-probe-promote-clean`과 같은 형태라 허용. frontmatter `approval` 두 줄은 `parse_spec_card`가 다중 키로 받는다(`role_paths.py:692-693`).
* D0a red-green: 신규 모듈이라 '도구 존재 단언' 실패가 red로 인정된다(계획 680행). 단, exit 2(입력 오류)를 기대하는 test는 base에서도 `python: can't open file` exit 2로 **통과**할 수 있다 → 모든 test가 먼저 파일 존재나 JSON 첫 줄을 단언해야 한다는 문장을 계약으로(지금은 판정 유형 근거 문단에만 있다).
* M1~M9 equivalence·test 커밋 0: 05 §9.2 289행과 맞는다.
* V4: D0b의 계약 test "레지스트리 열 = `plan` 출력"은 레지스트리 자체가 같은 도구 출력이라 동어반복 위험. D0b card에서 oracle을 (d) 규칙 손적용 합성 입력 + 실제 트리 drift guard로 나눠 적을 것(이 검토 범위 밖, D0a 계약 9가 전제하므로 기록).

**(4) glob 충돌** -- `grep -rn "glob(" A/tests/ tools/gates/` 결과 기준:
* 새 MOD 파일(`A/*.py`)은 `test_ic5:86`, `test_dup_w_calc:61`, `test_d_delete_dead:82`, `test_d_move_tests:78`, `test_d_delete_telescopic:92`, `tests/tools/reg_check.py:179`, `interface_card.py` `ENGINE_GLOBS`, `redteam/lib/rt.py:688`(공격 23 엔진 전수)에 자동 포함 -- 의도대로(이름 판정이라 위치 무관). `reg_check`는 이름만 대조해 위치 무관 확인.
* `_engine_defs.py`: `test_ic_markers_match_plan.py:91`(`contracts/*.py` 표식 대조 -- 표식 없으면 무발동), rglob 4곳(m6). pytest 수집 규칙과 겹치지 않음(`_` 접두, `pytest_gate.ini` `testpaths` 기본 `test_*.py`).
* `A/tests/tooling/test_move_plan.py`: `pytest_gate.ini` `norecursedirs = tools`는 `tooling`을 막지 않아 수집됨(의도대로).
* `tools/migrate/move_plan.py`: `A/*.py` glob 밖, `interface_card` 밖. 충돌 없음. 단 S9.
* redteam `attacks/32-*`: `run_all.py:55` `attacks/*/expect.json`. 현재 마지막 30, 17 접두는 이미 중복 여럿이라 번호 충돌만 피하면 됨.

**(5) G1 이동 규칙 반례**(`C:/g24/ce_moved.py`, M-1~M-3 문자 그대로)
* 덮어쓰기(B1): 이동으로 분류 → **약화**.
* 이동 + import 재바인딩(B2): 이동으로 분류 → **약화**. `__file__` 의존 def(저장소에 2곳)도 같은 부류.
* 클래스 머리 변경 + 메서드 이동(B3): 메서드 이동으로 분류 → **약화**, 메서드 없는 클래스 36개는 판정 밖.
* 두 파일 def 교환(CE3): M-2로 걸러짐(둘 다 V3 대상 유지) -- 문제없음.
* 복사 + 원본 유지, 래퍼 shim, 모호 원본: M-1·M-2로 걸러짐 -- 문제없음.
* 무동작: 최근 판정 기록 2건(`df36` 070cf69→ed98d35, `dup-w-calc` b7d1798→a9de49c)에서 `moved` 빈 집합(`C:/g24/noop_check.py` → `{'df36': {}, 'dup-w-calc': {}}`) -- 계약 9의 전제와 맞다.

**(6) DoD 명령**
* E0·E1: `import_layering.py` 출력에 `present`(dict)·`findings`가 있다(`import_layering.py:90-91`) -- 잰다.
* E2: B5·B6 -- 지금 모양으로는 못 잰다.
* E3: `git grep -E … \b`가 Git for Windows에서 동작함을 확인(M22 재현 86개). m7.
* E4: B4 -- 마지막 병합본에서 exit 2가 된다.
* E5: `20-dead-code-dup` §3 인용이라 판정 가능.
* 판정식 CACHE-ID·SHIM 동일성·MOVE-TOTAL은 DoD 명령이 없다(S10).

**(7) 원칙**
* topology 무관: G1·D0a 모두 코드 구조만 읽음. D0a는 엔진 이름을 CLI로 받게 해 합성 입력으로 일반성 증명 가능 -- 좋다(S8만 정리).
* 만들면 배선: `moved_defs`는 세 `main`이 부름(좋음). `move_plan`은 D0b test·E4 배선이 B4 때문에 Phase 중간에 끊긴다. CACHE-ID 등은 배선 없음(S10). T0 도우미는 세 test가 부름(좋음), 대신 `_SIZING_RECIPE`가 죽은 이름이 된다(S13).
* 재계산 없음: G1 계약 8의 방향은 맞으나 측정 기준(S2)과 V6의 새 전체 트리 읽기 범위를 조일 것.
* 정의 하나: `def_hash`를 `reachability`로 옮기는 방향은 맞다(`mutate_changed`가 이미 `reachability`를 import, 게이트 밖 소비자는 `changed_defs`를 부르는 스크립트 3개뿐이고 `_strip_doc` 외부 소비자 0).

---

## 3. 사용자 결정 항목(진짜 사용자 몫만)

1. **UD-0 design 승인**(계획 N3.10 표 개정·533/534행·N3.12.3 test-only 열거·`00-common` 103/431행·`10-test-separation` §5.6 '파일' 열 성격 변경 포함). 위 B1~B6·S 항목 반영 뒤 승인 요청.
2. **UD-5 G1 게이트 변경 승인** -- 단, 승인 대상은 M-0·M-4·클래스 골격 단위를 더한 판(B1~B3). 대안(설계 선택지로 사용자에게 물을 가치가 있는 것): 이동 인식을 **전역 규칙**으로 둘지, 아니면 **승인 기록에 선언된 이동 목록(from→to)만** 인정하는 좁은 규칙으로 둘지. 후자는 반례 부류 전체를 선언·대조로 막지만 card마다 승인 한 건이 는다. '약화 금지' 원칙만으로는 둘 다 허용되므로 비용 선택은 사용자 몫.
3. **UD-6 T0 V5 승인**(test diff 해시).
4. **UD-1(U-03)** 추적 안 된 `smoke_run_harness_session18_save.py`를 깨지게 둘지 -- 계획이 사용자 결정으로 지정.
5. **S11 probe 처리 방침**: 속성 덮어쓰기 probe 6개를 F1에서 호출자 모듈 기준으로 고칠지(F1 oracle 'import 줄 외 동일'의 예외), 아니면 Phase 3에서 동작하지 않는 probe로 표시할지 -- probe 존치·기능 범위는 사용자 몫.

나머지(S1~S10, S12~S13, minor)는 규칙·실측으로 정해지므로 사용자에게 묻지 않고 고친다.

---

## 부록 1. 재측정 명령과 결과 (HEAD `cd64170`)

| 항목 | 명령 | 결과 | 초안 대비 |
|---|---|---|---|
| mutate_changed 줄 | `grep -n 'diff", "--name-only\|copytree\|cat-file\|"show", "%s:%s" % (ns.base\|for q, fn in changed_defs\|rmtree' tools/gates/mutate_changed.py` | 276·285·321·323·326·364, `def_hash` 46, `changed_defs` 50 | 일치 |
| reachability 줄 | `grep -n "base_defs\|new_defs = \|^def " tools/gates/reachability.py` | `_refs` 69, `build_graph` 97, `_is_source` 175, 224·227·230 | 일치 |
| source_lint 줄 | `grep -n "^def compare\|findings += compare"` | 212·268 | 일치 |
| redteam | `ls tools/gates/redteam/attacks`, `sed -n 52,58p run_all.py`, `grep -n 'add_parser("vcase' lib/rt.py` | 마지막 30, 발견 규칙 55행, 부명령 `vcase` 1327행 | 일치 |
| 새 이름 충돌 | `git grep -n -E "moved_defs\|move_plan" -- docs/01-plan docs/02-design`; `git grep -l -E "mutate_changed\|reachability\|source_lint" -- A/tests` | 0 / 0 | 일치 |
| G4 소비자 | `git grep -n "def_hash\|changed_defs" -- . ':!*.jsonl'` | 게이트 밖 스크립트 3개 | G1 일치, design §5.2 '4곳' 불일치(m2) |
| 계획 줄 | `sed -n "<n>p"` 517·526·527·532·533·534·541~543·549·601·674·680·686·839·842·843·991·1000·1018·1078 | 인용 문구와 일치 | 일치 |
| design 줄 | `00-common` 103·431·435, `10-test-separation` 187·252~274·413, `05` 289·317·555~558 | 일치 | 일치 |
| 레지스트리 | `grep -n "기준 커밋"`, 248·389·392·395행 | 일치 | 일치 |
| v1 스크립트 재실행 | `cp p3_measure.py p3_assign.py C:/g24/ && $PY C:/g24/p3_measure.py && $PY C:/g24/p3_assign.py` | 목적지 분포 114/87/61/32/14/7/2/미매핑 62(합 379), SR 12015줄(Class 13·Func 174·Assign 30), SD 9035줄, 미등록 SR 3·SD 24, 미배정 34, 큰 번호 참조 64(쌍별 17/14/9/8/6/3/2/1…), `_hr_resolve_vertical_group` 9 | 일치 |
| 호출부 86 | `git grep -l -E "^[[:space:]]*(import\|from)[[:space:]]+(sizing_recipe\|stick_diagram\|design_report\|topology_library)\b" cd64170 -- '*.py'` 디렉터리 집계 | 86: .ai 6, A 루트 4, conftest 1, contracts 3, probes 27, tests/tools 2, unit 10, docs 1, workspaces cr 27·ts 4·harness 1 | 일치 |
| T0 사실 1 | `git grep -c -E "(sizing_recipe\|…)\.py" -- A/tests ':!A/tests/probes'` | contracts 10, unit 6, tools 2 | 일치 |
| T0 줄 | `sed -n 40,75p test_ic5.py`, `sed -n 440,444p test_dup_w_calc.py`, `sed -n 219,263p test_ts6_dead_probes.py` | 47~69, 442, 219~222, 259~263 | 일치 |
| R-DEF 전제 | `$PY C:/g24/t0_rdef.py` | 최상위 중복 0, ic5 21개 각 1곳, 대상 이름 중복 0, `size_transistor`·`width_from_id_density`·`audit_vsb_consistency`·`_build_theta_evaluator` = sizing_recipe 1곳, `_L_ROLE_MULTIPLIERS` 0 | 일치 |
| `_SIZING_RECIPE` 소비자 | `grep -n "_SIZING_RECIPE" test_ts6_dead_probes.py` | 60·221·222·261·262 | **불일치**(S13) |
| 캐시·global | `sed -n '2391p;2530p;7697p' A/sizing_recipe.py`; `grep -n lru_cache A/topology_library.py`; `grep -c "^\s*global "` | AnnAssign 3개, lru_cache 데코레이터 1(248, 254는 주석), global 0 | lru_cache 수 **불일치**(m1) |
| harness | `sed -n '422p;427p;446p' workspaces/run_harness.py` | `def run`, `topo = os.path.join(LIBRARY_DIR, cfg["topology_file"])`, `topo, spec, …` | 일치 |
| D0a 사실 | `ls tools/migrate`; `grep -n "parents\[" A/tests/tooling/test_extract_selftest.py`; `sed -n 22,35p import_layering.py` | `extract_selftest.py`만; `mod_table` = ID·파일 열만 | 일치(단 S5) |
| 역할 경로 | `sed -n 55,65p tools/gates/role_paths.py`; 계획 601·618·619행 | `tools/**` = tool, `A/tests/**` = test(tests/tools 제외), redteam = test-author(게이트 변경) | 일치 |
| G1 측정 재현 | `p3v2_g1_results.json` 검산 | 473 = 272+181+12+8, 15,677 = 8874+5933+683+187, V6 861 = 469+353+34+5 | 일치 |

스크래치 `C:/g24`의 측정 스크립트: `ce_moved.py`(반례), `t0_rdef.py`, `dupq.py`, `classes.py`, `noop_check.py`, v1 사본 -- 검토 종료 시 디렉터리째 삭제.
