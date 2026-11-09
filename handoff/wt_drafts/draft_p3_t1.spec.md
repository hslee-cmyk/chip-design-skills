---
id: 20261006-p3-test-relocate
phase: 3
evidence_type: test-only
gate_change: no
approval: 20260930-30-module-split-design
approval: 20261006-p3-test-relocate
approval: 20261006-p3-t1-v4-exempt
---
## 의도

design `30-module-split` **v8.5**(사용자 승인 UD-0 `20260930-30-module-split-design`, gate `master` `6df4bd7` 판 -- 작성 전 실측을 잰 `6c724de`와 비교해 `skills`·`tools` 변경은 test 2파일 추가(`A/tests/contracts/test_b26pre_existing_paths.py` test 19 -- b26pre, `A/tests/contracts/test_b26_backfill_interdig.py` test 5 -- backfill)와 `A/sizing_recipe.py` `run_matching_safety_with_finger_growth` 본문 −5/+4(최상위 이름 증감 0)뿐이다. 두 test 파일은 `unit/` 밖이고 옛 4파일·ts3·probe 2파일과 무관하다(7경로 blob이 `6c724de`·`6df4bd7`에서 같음 -- r4 실측). 그래서 T1 매핑·V5 해시·V4 영향은 0이고 PT3 총수만 +24다. 커밋 직전 재확인 '작성 전 실측' 11 (iv)) §1-5·§7.1 C군·§8 T1 행·§8.1·§9.2 '뒤에 올 승인', card **T1**.
A = `skills/analog-gmid-design/assets`, U = `A/tests/unit`.

**무엇을 하는가**: TS2(C9 `20260922-ts2-pytest-split`)가 만든 `U/test_selftest_<모듈>.py` 4개(`sizing_recipe`·`stick_diagram`·`design_report`·`topology_library` -- 옛 엔진 파일 이름)의 test 함수를
N3.10 모듈별 파일 `U/test_mod<k>_<N3.10 줄기>.py`(계획 N3.11 541~543행 `unit/test_mod1_gmid_lut.py ... unit/test_mod9_instance_report_builder.py`, `10-test-separation` 187·413행 "매핑의 test id는 `30-module-split`이 `unit/test_mod*.py`로 옮길 때 그 design이 새 매핑을 낸다")로
**본문 그대로** 옮기고 옛 4개를 지운다. test 이름·assert·기대값·fixture 본문은 바꾸지 않는다. 판정은 바뀌지 않는다(수집 test id 집합 = 매핑, id별 결과 = base).
그 파일 이름을 목록으로 가진 계약 test(design §7.1 **C군** `contracts/test_ts3_no_print_verdicts.py` `_LEGACY_SCRIPTS`)를 새 이름으로 바꾼다.

**매핑 규칙(이 card가 정한다 -- design 30은 규칙 문장을 두지 않았다, '결정 필요 항목' T1-1)**: test t의 목적 MOD k(t) = t의 **닫힘**(t 본문 + t가 요청하는 fixture와 부르는 모듈 수준 도우미, 전이적으로)이 이름으로 읽는 엔진 정의의 N3.10 번호 중 **최댓값**.
엔진 정의 = R-DEF(design §7.1 -- `A/*.py`(하위 디렉터리 제외)·`workspaces/run_harness.py` 최상위에서 그 이름을 def·class·대입으로 바인딩하는 파일이 정확히 하나) +
**도구 경유 조항**: 닫힘이 `A/tests/tools/` 모듈에서 import한 이름을 하나라도 읽으면(그 이름이 무엇이든), 그 도구 모듈이 최상위 `from <엔진> import`로 받는 이름 **전부**를 닫힘이 읽는 엔진 정의로 센다
(test가 읽는 이름 자체가 엔진에서 받은 이름일 때만 세는 좁은 읽기가 아니다). 모의 해당 1: `sizing_recipe::test_s004_optimize_multistage` -- 본문은 `run_regression_case`(`regression_runner`)·`_os`만 읽고, `regression_runner`가 엔진에서 받는 `SemiEmpiricalGmIdLUT`(MOD1)·`_COMPENSATION_REGISTRY`(MOD4)·`optimize_multistage`(MOD4)로 닫힘 최댓값 4 → **MOD4**(좁은 읽기로는 본 규칙 0·메서드 0이라 SR 출신으로 멈춘다).
닫힘이 엔진 정의를 하나도 읽지 않는 test에만 아래 **대체 조항을 이 순서로** 쓴다:
(대체 1) **메서드 조항** -- 닫힘이 속성으로 읽는 이름 중 엔진 클래스의 메서드 이름(그 이름의 최상위 정의가 없고 그 메서드를 정의한 파일이 하나)의 N3.10 번호 최댓값.
(대체 2) **옛 파일 조항** -- 그래도 없으면 옛 파일의 엔진 모듈 단위가 모두 간 MOD. 이것이 하나로 정해지는 옛 파일은 TL뿐이다(TL → MOD4 -- TL은 M4에서 완전 shim, design §8 M행). SR·SD·DR 출신 test가 여기까지 오면 card를 멈춘다(모의 0).
메서드 조항이 대체로만 쓰이는 근거: 매핑 규칙은 'import는 작은 번호로만'의 test 판인데 메서드 호출은 test 파일에 import 줄을 만들지 않는다(수신 객체는 fixture·지역 값이 준다). 그래서 메서드 이름은 계층 판정의 입력이 아니고, 배정할 다른 근거가 없을 때만 쓰는 근거다.
수신자를 보지 않는 이름 대조라 본 규칙에 넣으면 내장 메서드도 엔진 메서드로 읽는다(독립 검토 S-1 실례: `test_s155_propose_device_roles_gap_fill`의 지역 `set()`의 `.add`가 `stick_diagram` 클래스의 `add`와 맞아 MOD7로 감 -- 본 규칙으로는 MOD3).
근거: 계층 규칙 N3.10 "import는 번호가 작은 모듈 쪽으로만"을 test 파일에 같은 뜻으로 적용한다 -- `test_mod<k>`는 MOD ≤ k만 필요로 한다(F1 뒤 import 줄이 그대로 그 모양이 된다). 정의 위치는 손 목록이 아니라 card base 트리에서 도구로 계산한다(정의 하나).
매핑 표 = `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/t1-mapping.json`(생성기 `build_t1_mapping.py` 같은 폴더 -- 오케스트레이터가 이 spec card와 같은 커밋에 넣는다. C9 매핑표 선례 `c9-mapping.json`), 키 = base test id, 값 = 새 test id·k·적용 조항(본 규칙·대체 1·대체 2)·근거(그 조항이 쓴 닫힘 이름과 정의 파일 -- 대체 조항을 쓰지 않은 test에는 메서드 이름을 근거로 적지 않는다).

**왜 이 순서인가(design §8.1)**: `M1 → … → M9 → M10 → T1 → F1 → F2`. 매핑은 정의가 MOD 파일에 있어야 계산된다(M1~M9 병합 뒤 -- 그 전에는 정의가 split 파일에 있어 번호가 없다). F1은 이 card 병합본이 base다(F1 초안 25행 "T1이 `unit/test_selftest_*.py` 4개를 `unit/test_mod*.py`로 옮긴 뒤").
T1은 test 파일의 **위치**만 바꾸고 import 줄은 옛 파일의 머리 그대로 가져간다 -- import를 정의 모듈로 바꾸는 것은 F1 몫(design §7.2, 계획 534행).

**착수 조건**: (1) M10(`p3-mod10-entry`) 판정 기록이 gate `master`에 있음(이 card base = M10 병합본) (2) T0(`20260930-p3-tests-location-free`)·T0-V4 면제 기록(`20261002-p3-t0-v4-s009-exempt`) 병합(그 card가 W-1 import 3줄을 고친 판을 옮긴다)
(3) **V4 면제 다시 받기(`20261006-p3-t1-v4-exempt`) -- '결정 필요 항목' T1-2, 사용자 질문**: 옮기면 test id가 바뀌어 기존 decision 면제 3건이 저절로 풀린다(그 기록들의 '덮지 않는 것' 문장). 승인 전에는 test worktree를 만들지 않는다.

**만들면 배선**: 새 도우미 `U/_selftest_shared.py`(fixture 2개 이상 파일이 쓰는 것만)는 그 fixture를 쓰는 test 파일이 import한다(계약 4). 매핑 생성기는 auditor 판정(계약 2)과 이 card의 매핑 표가 부른다.

## 관찰 가능한 계약

1. **범위(diff, auditor)**: test 커밋 diff = `U/test_selftest_{sizing_recipe,stick_diagram,design_report,topology_library}.py` 삭제 + `U/test_mod<k>_<줄기>.py` 추가(매핑 표에 나오는 k마다 하나) + `U/_selftest_shared.py` 추가 +
   `A/tests/contracts/test_ts3_no_print_verdicts.py`(`_LEGACY_SCRIPTS` 리터럴만) + 다른 test의 **docstring 안** 옛 test id 문자열(계약 7)뿐. 엔진 소스·`tests/tools/**`·`tests/conftest.py`·`tools/**`·문서 0. code 커밋 없음.
2. **매핑(auditor)**: 병합본 `U/test_mod*.py`에서 수집한 test 함수 id 집합 = 매핑 표 값 집합(파라미터 id 포함 수집 id로 비교 -- base 수집 id를 매핑으로 옮긴 집합과 같다). 각 test가 든 파일 = 매핑 표의 k. 매핑 표 자체는 auditor가 card base 트리에서 생성기를 다시 돌려 같은지 본다(규칙 재현).
   **생성기는 엔진 모듈을 import하지 않는다**: `build_t1_mapping.py`는 card base 트리를 `git show` + `ast`로만 읽고, import는 표준 라이브러리와 게이트 도구(`import_layering`·`role_paths`)뿐이다. 이유: 생성기 자리(`docs/03-analysis/…`)는 E3/E3b 스캔 범위 안이고 F1 쓰기 경로 밖이라, 엔진을 import하면 F2 뒤 E3/E3b가 FAIL하고 F1이 고칠 수 없다(review_phase3_dod_refresh m6).
   auditor 판정: 생성기 AST에 엔진 줄기(card base `A/*.py`(하위 제외) 줄기 + `run_harness`)를 모듈로 갖는 `Import`·`ImportFrom` 0, `importlib`·`runpy`·`__import__`·`import_module`·`run_path` 0, 그리고 생성기 실행 뒤 `sys.modules`에 `A`·`workspaces` 아래 파일의 모듈 0(R-11).
   test 함수 이름은 바뀌지 않는다. **목적 파일 안**에서 이름 충돌 0(test 0; fixture는 계약 5의 1건만)이 매핑의 성질이다 -- test 이름 충돌이 생기면 card를 멈춘다, 이름 바꾸기로 풀지 않는다.
   옛 파일 사이 같은 이름 test(모의 12쌍, 예 `test_s030_section`)가 서로 다른 목적 파일에 나뉘는 것은 정상이다(수집 id가 파일 경로를 담아 겹치지 않는다 -- 판정 대상 아님).
3. **본문 그대로(auditor AST)**: 옮긴 test 함수·fixture·도우미마다 `ast.dump`(데코레이터·docstring 포함)가 base의 같은 함수와 같다. 예외는 계약 5의 fixture 이름 바꾸기 하나(그 이름 토큰만 다르고 나머지 같음).
   새 파일 머리 = 그 파일에 test를 보낸 옛 파일들의 머리 문장(모듈 docstring 뒤 def 앞의 import·대입·`if` -- `sys.path` 설정 포함) 원문을 옛 파일 순서대로 이은 것(같은 원문은 한 번) + 계약 4의 `from _selftest_shared import …` 한 줄 + 새 모듈 docstring.
   **같은 이름을 두 머리 문장이 묶으면 두 문장이 묶는 객체가 같아야 한다**(`is` -- auditor가 문장마다 따로 실행해 비교; 옛 파일들이 모두 card base의 같은 재수출을 가리키므로 성립).
4. **fixture·도우미 배치**: 옛 파일의 fixture·모듈 수준 도우미 f를 쓰는(전이적으로) test가 **한 목적 파일**에만 있으면 f는 그 파일로, **둘 이상**이면 `U/_selftest_shared.py`로(정의 하나 -- 복사하지 않는다) 옮기고 쓰는 파일이 이름으로 import한다
   (그 fixture가 요청하는 fixture도 같은 규칙으로 따라간다). `_selftest_shared.py`는 `_` 접두라 pytest가 수집하지 않는다. 쓰는 test가 없는 fixture·도우미는 0이어야 한다(있으면 멈춘다 -- 지우는 것은 이 card 범위 밖).
5. **fixture 이름 충돌**: 서로 다른 옛 파일의 같은 이름 fixture가 한 목적 파일에 함께 필요하면, **뒤 옛 파일**(순서: sizing_recipe, stick_diagram, design_report, topology_library) 쪽 fixture를 `<이름>__<옛 모듈>`로 바꾸고, 그 목적 파일 안의 같은 옛 파일 출신 def에서 **그 fixture 이름 토큰**(def 이름, 사용처의 매개변수와 그 매개변수의 본문 참조 -- 예 `s065_state.<속성>`)만 같이 바꾼다. 다른 변경 없음(R-10과 같은 문언).
6. **C군**: `_LEGACY_SCRIPTS` = 병합본의 `unit/test_mod*.py` 파일 상대 경로 전부(이름순, 이 card가 만든 것 -- `_selftest_shared.py`는 판정 문장을 갖지 않아 넣지 않는다). 같은 test 파일의 다른 줄·test 함수는 바꾸지 않는다.
   **주석도 바꾸지 않는다**: base(`6c724de`) 27~28행("이 4개 파일에 있다")·68~69행("unit/test_selftest_<m>.py 4개")은 C9 시점 경위를 적은 주석이라 T1 뒤 낡은 서술로 **남는다**(AST·V5 밖, 판정 영향 없음). 남기는 이유: test-author가 정하는 문장을 늘리지 않아 ts3 blob이 매핑 표만으로 정해진다(계약 10 운반 대상 -- 2차 시도가 같은 blob을 만들기 쉽다). 주석 정정은 문서 후속 후보(open items X-6).
   `test_target_set_includes_legacy_scripts`·`test_tree_has_no_print_verdicts`가 병합본에서 PASS(목록이 실제 파일을 가리키고 판정 대상 T = 0).
7. **docstring 안 옛 test id**: 추적 `A/tests/**/*.py`의 문자열에 남은 `unit/test_selftest_<옛>.py::<test>`(모의: `unit/test_probe_revalidation_scope.py`·`unit/test_probe_role_L_derivation.py` 모듈 docstring 각 1)를 매핑 표의 새 id로 바꾼다.
   병합본에서 추적 `.py`(`.ai/verification/**` 제외 -- 기록 불변)에 옛 test **id** 꼴 문자열(`test_selftest_[a-z_]+\.py::` -- `::`까지) 0. 경위를 적는 파일 이름 언급(`::` 없음 -- ts3 주석 base `6c724de` 27·68행 = 모의 head 27·74행(목록이 2줄 → 8줄로 늘어 6줄 밀림), 새 파일 docstring)은 남는다(모의 실측 11줄, 전부 `::` 없음).
8. **동작 불변(auditor)**: PT3(design §10) base·병합본 -- 병합본 수집 id 집합 = base 집합을 매핑으로 옮긴 집합(수 같음), id별 결과 같음, 실패 0(T0 병합 뒤). `--shuffle-seed=1..5`로 `U/` 전체 실행이 다섯 번 모두 실패·오류 0(C9 §10 D3 선례 -- fixture 배치가 바뀌므로).
9. **게이트(auditor)**: V1(PT3) PASS. V2 test-only -- basis = 계약 2 매핑·계약 8. V3·V6·V7: 엔진 소스 변경 0이라 대상 0(`targets` []). V5: **FAIL이 예상되고 승인으로 닫는다**(계약 10). V4: 계약 11.
10. **V5 승인 범위(test 커밋 뒤 diff 해시로 `20261006-p3-test-relocate`, `target_kind: diff`)**: `weakening_diff`가 (a) 옛 4파일의 test 함수 삭제를 'assert 삭제'로 센다(이동을 추적하지 않는다 -- 옮긴 함수는 계약 2·3이 새 파일에서 같음을 판정) (b) `_LEGACY_SCRIPTS` 리터럴 변경 1 (c) 계약 7 docstring 리터럴 변경.
    승인 범위 설명에 '이동(판정 불변 -- 계약 2·3·8) + 판정 대상 목록 리터럴 갱신 + docstring 안 test id 갱신'을 적는다. 새 파일(`A`)은 V5 대상이 아니다(추가 파일의 함수는 '삭제'가 아니다).
    **해시 입력(실측)**: `diff_hash` = 00-common §8.2 식 -- V5 `diff_paths` 7경로(옛 4파일·ts3·docstring 2파일)의 (base blob, head blob)만 쓴다. 커밋 id·새 `test_mod*.py`·`_selftest_shared.py`는 입력이 아니다.
    증거: 독립 검토가 커밋 id가 전부 다른 사슬에서 같은 해시 `aad79872…0131`을 냈고, 이 판(S-1 반영, 사슬 `C:/g369`)에서도 같은 값이다('작성 전 실측' 7).
    **운반(design 05 §12 'V5 승인 운반' -- 2회 시도 필요)**: 1차 시도 순서 1~3에서 auditor가 V5 FAIL로 멈춘 뒤, 정리 **전에** 오케스트레이터가
    (가) head에 있는 **3경로**(ts3·docstring 2파일)만 `git -C $W/<id>-test cat-file blob <T>:<path>`로 `v5-carry/<id>/<blob id>.blob`을 만든다 -- 옛 4파일은 T에 없어 `cat-file`이 실패하므로 만들지 않는다;
    (나) `paths.tsv`에 7경로를 모두 적고 옛 4파일의 blob 칸은 `-`(00-common §8.2 '없으면 `-`'과 같은 표기 -- head blob `-`는 2차 test-author가 옛 4파일을 지우면 재현된다);
    (다) 사용자 승인 뒤 승인 기록 `20261006-p3-test-relocate`(`target_kind: diff`, `diff_base` = card base, `diff_head` = 1차 T, `diff_path` = 7경로 전부, `target` = `diff_hash`).
    2차 시도 test-author: 3경로는 `paths.tsv`대로 `cp`, 옛 4파일은 삭제, 새 `test_mod*.py`·`_selftest_shared.py`는 매핑 표로 다시 만든다 -- 새 파일은 해시 경로 밖이라 1차와 **바이트로 같을 필요가 없다**(계약 2·3이 판정한다).
    2차 auditor: `diff_hash`(2차) = 승인 `target`(= 1차 해시) 확인. 1차와 2차 사이 card base는 승인·운반 `Role: doc` 커밋만 늘어난다(7경로 base blob 불변 -- 바뀌면 해시가 달라져 V5 FAIL로 드러난다).
    **2회 시도를 없앨 수 없는 이유**: 해시는 T에 기대지 않아 1차 전에 계산할 수는 있다. 그러나 (1) 00-common §8.2 staged_diff 항은 `diff_head`를 금지하는 이유를 "아직 없는 그 커밋의 id를 적을 수 없다"로 적고, design 05 §12 'V5 승인 운반' 행 (2)는 승인 기록을 `diff_head` = T(1차 시도 test 커밋)로 만든다 -- `target_kind: diff`의 `diff_head`(§8.2 필수, 40자리)는 승인한 내용이 실제로 든 커밋이고, 1차 전에는 **1차 시도가 만든 실제 커밋이 아직 없다**(모의 사슬 커밋은 저장소 밖 스크래치에서 오케스트레이터가 만든 것이라 그 자리에 쓸 수 없다; gate `merge_gate.py`는 형식만 보지만 뜻을 바꾸는 것은 문서 기준 변경).
    그 커밋이 gate에서 도달 가능해야 한다는 뜻은 아니다: 기존 운반형 승인은 정리 뒤 `diff_head`가 도달 불가능한 1차 시도 커밋이다(gate `master` `863a037`의 `20260923-ts2-pytest-split`: `diff_head` `bdf9ca626f0000056152f192e60f29bcc8a95755` -- `merge-base --is-ancestor` exit 1, 어느 브랜치에도 없음; 독립 검토 r2: 운반형 11건 모두 같은 모양) (2) `diff_head` 없는 `staged_diff`는 design 05 §8.2-5가 topology·`Role: user` 커밋에만 둔다(test 커밋 판정 V5는 `diff`)
    (3) 사용자가 승인하는 것은 test-author가 실제로 만든 diff여야 한다 -- 1차 전 승인은 오케스트레이터가 예상한 내용(작성자≠검증자 위반 위험)을 승인받는 것이다. 그래서 §12 절차대로 2회 시도하되, 2차가 맞춰야 할 것은 3 blob과 옛 4파일 삭제뿐이다(비용이 작다).
    design 05 §12 문언에 삭제 경로(`.blob` 없음, `paths.tsv` `-`) 서술이 없는 것은 문서 정정 후보다(open items X-7 -- 기준 변경 아님).
11. **V4(판정 때 interface card 피검)**: interface card의 '기존 함수' = 옮기는 test가 이미 V4로 판정받은 피검의 합집합 -- C9 `20260922-ts2-pytest-split` interface(`optimize_full_circuit_budget`) ∪ T0 `20260930-p3-tests-location-free` interface(모의 5: `size_transistor`·`width_from_id_density`·`check_quasi_static`·`_build_theta_evaluator`·`load_topology`) -- 판정 범위를 좁히지 않는다.
    `interface_card.py`는 이 card 본문의 backtick 심볼로 피검을 정하므로 위 목록은 '등' 없이 정확해야 한다: card 커밋 직전 gate `master`의 T0 판정 기록이 쓴 interface card의 '기존 함수' 목록과 C9 판정 기록의 것을 그대로 옮겨 적는다('작성 전 실측' 11 (v)). 모의에서 이 문장으로 만든 interface card의 기존 함수 = 6(아래 '작성 전 실측' 10).
    판정 기록 `checks.V4.basis`에 UNJUDGED(모의 182)의 근거 문장을 적는다: "옮긴 test 본문의 `ast.dump` = base(계약 3) -- base에서 같은 식으로 같은 판정(UNJUDGED·NO-SUBJECT 분류는 본문과 피검 목록의 함수라 같다)" (T0 선례와 같은 꼴).
    판정 명령은 파일 인자 없이 `test_lint.py --root <복제본> --interface-card <카드> --base <base> --head <병합본>`이다(도구가 `--no-renames --diff-filter=AM`으로 고른다 -- 옛 파일과 비슷한 새 파일이 rename으로 잡혀 빠지지 않게, R-12).
    병합본(옮긴 파일 전체가 `A`라 파일 전체를 lint, 모의 파일 12): 규칙 (1) 발견은 기존 decision 면제 3 test(`test_s009_revalidate_finger_override` 2줄·`test_s052_compensation`·`test_s054_section`)의 **새 id**뿐이어야 하고 그 셋은 `20261006-p3-t1-v4-exempt`로 `exempt`, FAIL 0.
    그 밖의 test에서 규칙 (1)~(5) FAIL이 나오면 멈춘다(이동이 새 FAIL을 만들 수 없다 -- 판정이 같은 본문이므로; 나오면 원인 확인).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**test-only**: 엔진 소스가 바뀌지 않아 code 커밋이 없다(`00-common` §8.1 `code_commit: null`, 계획 N3.12.3 '순서 4·5 생략'). 판정 유형은 커밋 모양이 정한다(`20-dead-code-dup` §8 P2 정정). red-green은 성립하지 않는다(피검이 base와 같다).
계획 N3.12.3 test-only 열거에 "Phase 3 T0·T1"이 있다(UD-0 문서 개정 §3 -- design 커밋에서 반영). 증거(V2 test-only, `checks.V2.basis`): 매핑(계약 2) + PT3 id별 결과 대조(계약 8) + 셔플 다섯 번 -- 스키마상 test-only는 `red`·`equivalence` 필드가 없어 `basis` 문장으로 남긴다(선례 C9·T0).

## oracle 종류와 출처

(c) 동작 보존: 옮긴 test의 결과 = base의 같은 test 결과(PT3 id별). (d) 문서: 매핑 규칙(이 card '의도' -- 계획 N3.10 계층 규칙과 N3.11 파일 이름), 파일 이름 = N3.10 표 '파일' 열 줄기. (a) 구성: 매핑 표는 card base 트리에서 생성기가 낸다(정의 위치는 R-DEF).
test-author는 매핑 표를 입력으로 옮기기만 한다(정의 위치를 스스로 정하지 않는다 -- 소스 열람 없음). 모의 스크립트(`_drafts/p3kit_m10_t1/`)는 작성 전 실측용 시제품이다(작성자≠검증자 -- 역할 agent에게 건네지 않는다; 생성기 정본은 오케스트레이터가 docs에 넣는 `build_t1_mapping.py`).

## 거부해야 할 입력

auditor 판정기 자기 점검(병합본 사본에 하나씩 커밋 -- R-1~R-11은 커밋 변형, R-12는 절차 변형이라 커밋 없이 판정 명령만 바꾼다):
| ID | 변형(병합본 기준) | 거부해야 할 판정 |
|---|---|---|
| R-1 | 매핑과 다른 파일에 test 하나(예 MOD3 test를 `test_mod7_stick_diagram.py`로) | 계약 2(파일 = 매핑 k) |
| R-2 | 옮긴 test 하나의 assert 리터럴 하나 변경 | 계약 3(`ast.dump` 다름) -- V5는 새 파일을 보지 않아 못 잡는다 |
| R-3 | test 하나를 옮기지 않고 빠뜨림 | 계약 2(id 집합) + 계약 8(수) |
| R-4 | 공유 fixture를 두 파일에 복사(`_selftest_shared.py` 대신) | 계약 4(정의 하나 -- **같은 출처 (옛 파일, 이름)**의 def가 목적 파일 둘 이상에 있음. 이름만 같은 것은 거부 근거가 아니다: 출처가 다른 같은 이름 fixture 3개(`s040_state` MOD7·8, `s051_state` MOD7·8, `s063_state` MOD5·7)와 같은 이름 test 12쌍은 정상 병합본에서 두 파일에 나뉜다. 모의 정상 병합본: 같은 출처 def 중복 0) |
| R-5 | 머리에서 같은 이름을 다른 객체로 묶는 줄(예 `import cmath as math`) | 계약 3(`is` 비교) |
| R-6 | `_LEGACY_SCRIPTS`에 옛 이름 하나 남김 | 계약 6 -- `test_target_set_includes_legacy_scripts` FAIL(파일 없음) |
| R-7 | `_LEGACY_SCRIPTS`에서 새 파일 하나 뺌 | 계약 6(목록 = 병합본 `test_mod*` 전부) -- ts3 test는 통과하므로 auditor 대조 몫 |
| R-8 | 면제 기록 없이 병합 | 계약 11 V4 FAIL(규칙 (1) 4줄 -- 모의) |
| R-9 | docstring의 옛 id 하나 남김 | 계약 7(`test_selftest_…py::` 꼴 1) |
| R-10 | fixture 충돌을 test 이름·다른 fixture 이름까지 바꿔 풂 | 계약 3·5(바뀐 토큰이 그 fixture 이름 밖) |
| R-11 | 매핑 생성기에 `import stick_diagram` 한 줄 추가(오케스트레이터 문서 커밋 판 사본에서) | 계약 2(생성기 엔진 import 0 -- AST 검사가 `stick_diagram` 1을 낸다; 모의: 시제품 0, 변형 1) |
| R-12 | (절차 변형 -- 커밋 없음) 병합본은 그대로 두고 V4를 `git diff --diff-filter=AM` 파일 목록(`--no-renames` 없이)을 인자로 넘겨 돌림 | 계약 11 판정 명령(파일 인자 없이 `test_lint.py --base --head`가 `--no-renames`로 고른다). 모의: rename 탐지가 `test_mod7`·`test_mod8`을 R로 빼서 파일 10개만 lint -- 규칙 (1) 발견 0으로 **거짓 PASS**; 도구 자체 선택은 파일 12·FAIL 4 |

## library 회로 적용 여부

해당 없음(test 위치 변경 -- 판정 대상 엔진 동작 불변). 옮기는 test 중 library 회로를 읽는 것은 base와 같은 입력으로 같은 판정을 한다(계약 8).

## 무동작 판정 입력(무발동 값)

PT3 base·병합본 id별 결과가 같다(계약 8). 새 산출물·발동 계수 없음. 전수 스캔 test(`test_ts3_no_print_verdicts`, `test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`의 삭제·이관 이름 참조, `test_ic_markers_match_plan`)에서 새 발견 0 --
새 파일은 옛 파일의 본문을 그대로 담으므로 토큰 집합이 같다(PT3 결과로 판정).

## 재현할 수치

(모의 -- '작성 전 실측' 머리 사슬, 2026-10-06, 스크래치 `C:/g369`(r2 재측정; r1은 `C:/g323`). **전부 관찰**: 실제 base(M10 병합본)에서 auditor·오케스트레이터가 다시 잰다. 바뀔 수 있는 수는 관계로 적는다.)
* 옮기는 test 함수 = base 4파일의 test 함수 전부(모의 212 = sizing 67·stick 131·design_report 4·topology_library 10), fixture·도우미 = 4파일의 모듈 수준 def 중 test가 아닌 것 전부(모의 57, 쓰는 test 없는 것 0).
* 매핑(모의, r2 규칙): MOD1 2·MOD3 58·MOD4 20·MOD5 15·MOD6 1·MOD7 76·MOD8 32·MOD9 8 -- 파일 8개(MOD2·MOD10 파일 없음). 옛 파일별: sizing → 1:2·3:9·4:10·5:15·6:1·8:30, stick → 3:49·7:76·8:2·9:4, design_report → 9:4, topology_library → 4:10.
  적용 조항: 본 규칙 210, 대체 1(메서드) 1 = `test_s056_noise_1f_density`(MOD1), 대체 2(옛 파일) 1 = `test_s011_tan`(TL → MOD4), 멈춤 0.
  본 규칙 210 중 도구 경유 조항으로 정해진 test 1 = `sizing_recipe::test_s004_optimize_multistage`(MOD4 -- 닫힘에 도구 경유 이름이 있는 test도 이 1뿐, 좁은 읽기면 멈춤). 닫힘에 메서드 이름이 있는 test 19 중 18은 최상위 엔진 정의를 읽어 메서드를 쓰지 않는다; r1 문언(메서드를 본 규칙에 넣음)과 결과가 다른 test는 1(`test_s155_propose_device_roles_gap_fill` -- r1 MOD7(`.add`), r2 MOD3).
* 목적 파일 안 test 이름 충돌 0, fixture 이름 충돌 1(`s065_state` -- MOD3에서 sizing·stick; 이름 토큰을 바꾼 사용처 def 1 = `test_s067_MB`), 둘 이상 파일이 쓰는 fixture 2(`s086_state` MOD7·9, `s120_state` MOD3·9).
  같은 출처 (옛 파일, 이름) def가 두 파일 이상 0. 이름만 같아 두 파일에 나뉜 것: test 12쌍, 출처가 다른 fixture 3(`s040_state` MOD7·8, `s051_state` MOD7·8, `s063_state` MOD5·7) -- 정상(계약 2·R-4).
* PT3 수집 id: 관계 'base id를 매핑으로 옮긴 집합 = 병합본 집합', id별 결과 차이 0. 모의 수는 '작성 전 실측' 4.
* V4 규칙 (1) 발견 test = 기존 면제 3 test의 새 id(모의 MOD8 파일 4줄), 면제 기록 있으면 `exempt` 4·FAIL 0.
* V5 발견 = 옛 4파일 test 함수 수(assert 삭제) + 리터럴 변경(`_LEGACY_SCRIPTS` 1 + docstring 파일 수) -- 모의 212 + 3. `diff_hash`는 7경로 blob만의 함수(계약 10) -- 모의 r1·독립 검토·r2 모두 `aad798728d13d4bab9bd9479a3dd0af79ea67137d8a491ae08020e6b5fa30131`(S-1은 7경로 blob을 바꾸지 않는다: s155는 새 파일 사이에서만 옮겨지고, ts3 목록의 파일 8개와 docstring 2파일의 새 id(MOD8)는 그대로).

## 결정 필요 항목

사용자 질문 1건(T1-2) -- 나머지는 원칙 기본안. 상세·근거는 `_drafts/m10_t1_open_items.md`.
* **T1-1 매핑 규칙**(원칙 기본안 -- '의도'): 닫힘의 N3.10 번호 최댓값(계층 규칙의 test 판). 메서드 이름은 대체로만 쓴다(S-1 -- 메서드 호출은 import 줄을 만들지 않아 계층 판정의 입력이 아니다). 대안 '슬러그(test 이름의 함수)의 MOD'는 212개 중 125개가 슬러그로 정할 수 없고(`section` 등), 정할 수 있는 87개 중 10개가 r2 규칙 값과 달라(r1 셈 11에서 s155가 빠짐 -- 이제 슬러그 3 = 규칙 3)
  그 test 파일이 자기 번호보다 큰 MOD를 필요로 한다(계층 규칙과 어긋남 -- 모의, 예 `test_s099_find_diode_stacks` 슬러그 3·규칙 7, `test_s047_nmcnr_3stage_topology` 슬러그 4·규칙 8). 사용자 결정 아님(판정 불변, design 승인 범위 안의 배치 규칙).
* **T1-2 V4 면제 3건을 새 id로 다시 받기 -- 사용자 질문**(승인 기록은 사용자 답으로만 생긴다): 기존 decision 기록 `20260923-c9-v4-exempt`(s052·s054)와 `20261002-p3-t0-v4-s009-exempt`(s009)는 "이름·경로가 바뀌면 면제가 저절로 풀린다"고 적었다.
  기본안 (가) 같은 세 test·같은 규칙 (1)만 덮는 decision 기록 하나 `20261006-p3-t1-v4-exempt`(target = 새 id 셋, 범위 = 옛 기록들과 같음, 재검토 줄은 옛 기록 것을 잇는다). 대안 (나) T1에서 V4 피검을 C9 interface 하나로 좁혀
  s009를 판정 밖으로 빼기 -- 판정 범위 축소라 원칙상 기본안이 아니다(그래도 s052·s054 면제는 다시 필요). 질문 문안·시점: open items T1-2. **test worktree 생성 전**에 답이 있어야 한다(V4가 head 트리의 `.ai/approvals`를 읽는다 -- T0 선례).
* **T1-3 docstring 안 옛 id 갱신**(기본안: 이 card에서 고친다 -- 계약 7). 죽은 참조를 남기지 않는다. V5 리터럴 발견 2가 늘지만 승인 범위 설명에 적는다.
* **T1-4 공유 fixture 자리 = `U/_selftest_shared.py`**(기본안). 대안 `U/conftest.py`는 판정 환경 파일(V5 무조건 승인·EL 경로 조건)이라 고르지 않는다. 대안 '낮은 번호 test 파일에 두고 높은 파일이 import'는 test 모듈끼리 import라 고르지 않는다.
* **id 날짜**: 초안 id `20261006-p3-test-relocate`(slug = design §8 `p3-test-relocate`), 승인 id 둘도 card 커밋 날짜로.

## 작성 전 실측

(2026-10-06 r2. 실제 저장소 쓰기 없음. 격리 복제본 `C:/g369/r`(`clone -c core.autocrlf=false --no-hardlinks --no-local`, origin 제거, hooksPath 빈 디렉터리, TMP/TEMP `C:/g369/tmp`, 작업 끝에 삭제).
사슬: gate `6c724de` → FU 대역 → T0 W-1 대역 → G1 시제품(`g1_kit/install_proto.py` md5 `733d173f…`, `installed 4`) → D0a 대역 → D0b 재생성(`one 354·multi 0·nested 7·nounit 18`) = M1 base `ff5719c` → M1~M9 `chain_lean.py` `7ec2fd4`…`7fd4b16`(8 card 모두 plan 일곱 목록 0, `check` 발견 0, 단위 8·18·82·104·21·11·30·16).
**T1 모의 base = M9 끝 `7fd4b16`**(M10 모의 없음 -- 매핑은 M10에 기대지 않는다: r1 `t1_map.json`(base `b6d4eb2` = 처리부까지 옮긴 M10 대안 `a83a46b` 위, 기본안 M10 `1306cfc` 아님 -- review m-8)과 독립 검토의 M9 트리 매핑이 212개 모두 같은 k). head = `93d7c0a`. PT3 총수가 r1(1124)보다 적은 것은 M10 진입점 test 시제품 19개가 없어서다.
스크립트·원자료 `_drafts/p3kit_m10_t1/`(r2: `t1_map.py`·`gen_t1.py` 고침(`*.pre-r2.bak`), `build369.sh`·`t1_run.sh`·`t1_verify.py`·`junit_cmp.py`·`pt3_t1.sh` 추가, 결과 `out/r2/`; r3: `t1_run.sh` V4 줄을 파일 인자 없이(R-12, `*.pre-r3.bak`) -- `out/r2/t1_v4.json`(files 12)과 같은 선택).
r3(2026-10-07)는 문언만 고쳤다(재측정 없음). 아래 gate `6c724de` 측정은 gate `master` `6df4bd7`에서도 유효하다: `skills`·`tools` 차이는 머리에 적은 test 2파일과 SR 함수 본문 1곳뿐이다(V5 7경로 blob `0791457`·`4f3b7ae`·`ceefa7e`·`aeddecf`·`fe724a8`·`50dae17`·`7d6e893`이 `6c724de`·`863a037`·`6df4bd7`에서 같음 -- r4). 독립 검토 r2가 `2db7622`에서 매핑·V5 해시·V4를 같은 값으로 냈다. PT3 총수(실측 4)는 그 판에서 +24다(gate 실측: `863a037` 1109 passed → `6df4bd7` 트리 1114 passed, 15 xfailed -- backfill 판정 기록 V1).)

1. **사실 문장 재측정(gate `6c724de`)**: U의 `test_selftest_*.py` 4개(sizing 3063줄·test 67·fixture 15·도우미 1, stick 4348줄·131·33·2, design_report 114줄·4·2·0, topology_library 233줄·10·4·0; 옛 파일 사이 같은 이름 test 12·fixture 4).
   `contracts/test_ts3_no_print_verdicts.py` 29~30행 `_LEGACY_SCRIPTS` 4개 원문. 계획 N3.11 test 트리 `unit/test_mod1_gmid_lut.py ... unit/test_mod9_instance_report_builder.py`. `10-test-separation` 187·413행 원문(위 '의도'). `A/tests/README.md` 22행이 이미 같은 이름 줄을 가진다.
   추적 `.py`(`.ai/verification` 제외)에서 `test_selftest` 문자열: ts3 4줄(주석 27·68행, 목록 29·30행)·두 probe 승격 test docstring 각 1(`::` 있는 id 꼴)·옛 파일 자신의 docstring. 승인 기록에서 그 id를 target으로 가진 것: `20260923-c9-v4-exempt`(s052·s054); T0 초안의 `20261002-p3-t0-v4-s009-exempt`(s009, 아직 미커밋). gate에 T0 판정 기록 없음(T0 미병합).
2. **매핑 계산(`t1_map.py` r2 -- 메서드 조항 대체 전용, 출력 `k`·`rule`)**: 위 '재현할 수치'. 독립 검토 S-1의 예측(MOD3 58·MOD7 76, 나머지 같음)과 같다. r1 규칙 값(`R2c`)은 MOD3 57·MOD4 19 + 정해지지 않음 1·MOD7 77로 같은 파일에 남아 차이가 s155 하나임을 보인다.
   슬러그 규칙: 정할 수 없는 test 125, 정할 수 있는데 r2 규칙 값과 다른 것 10.
   도구 경유 조항(r3 문언 = 시제품 `t1_map.py` 133~134행, 도구 모듈 이름을 읽으면 그 모듈이 엔진에서 받은 이름 전부): r2 출력 `out/r2/t1_map.json`에서 `closure_top`에 `tools:` 이름이 있는 test는 `test_s004_optimize_multistage` 1(도구 이름 3, 그 밖의 엔진 이름 0 → k 4). r3는 문언만 고쳤고 시제품·출력은 r2 그대로라 위 매핑 수는 같다.
   **생성기 엔진 import 0(계약 2)**: 시제품 AST의 import = `ast`·`collections`·`json`·`subprocess`·`sys`·`import_layering`(게이트 도구, 그 안은 `role_paths`); 실행 뒤 `sys.modules`의 표준 밖 모듈 = `import_layering`·`role_paths`뿐, `A`·`workspaces` 아래 모듈 0. `import stick_diagram` 한 줄 변형(R-11)은 AST 검사가 `stick_diagram` 1을 낸다. 같은 base에서 두 번 돌린 `k`가 같다.
3. **모의 T1(`gen_t1.py`)**: 새 파일 8 + `_selftest_shared.py`(fixture 2), 옛 4파일 삭제, fixture 이름 바꾸기 1(`s065_state` → `s065_state__stick_diagram`, MOD3, 토큰 바꾼 사용처 `test_s067_MB`), ts3 목록 8줄(29~36행), docstring 2파일. diff `--shortstat` 14파일 +3322 −3177(r1 +3284 −3139 -- 줄 수 차는 git diff의 짝 맞춤 차이, 순증 145 같음).
   계약 2·3·4 대조(`t1_verify.py`): 옮긴 def 269 = test 212 + fixture·도우미 57, `ast.dump` 불일치 0(바꾼 토큰을 되돌린 1 포함), base def 중 안 옮긴 것 0, test가 든 파일 ≠ 매핑 k 0, **같은 출처 def가 두 파일 이상 0**, 목적 파일 안 이름 충돌 0, 이름만 같아 나뉜 test 12쌍·fixture 3.
   머리 중복 바인딩 21이름(6파일) -- 문장마다 따로 실행한 객체가 전부 `is` 같음(`t1_header_ident.py`, 다른 것 0).
   ts3: 주석 27행 그대로, 68행 주석 → 74행(목록 6줄 늘어 밀림). 추적 `.py`(`.ai/verification` 제외)에 `test_selftest_[a-z_]+\.py::` 0, `test_selftest` 언급 11줄(전부 `::` 없음).
4. **PT3(design §10)**: base `7fd4b16` `3 failed, 1087 passed, 15 xfailed`, head `93d7c0a` `3 failed, 1087 passed, 15 xfailed` -- junit 대조(`junit_cmp.py`): base id를 매핑으로 옮긴 집합 = head id 집합(1105 = 1105, 옮긴 수집 id 213 = 함수 212 중 하나가 파라미터 2개, 한쪽에만 있는 id 0), id별 결과 차이 0. 실패 3 = T0 A군(`test_dup_w_calc`·`test_ic5`·`test_ts6_dead_probes` 각 1 -- 모의 사슬에 T0 R-DEF 없음, base·head 같음).
5. **셔플**: head에서 `U/` 전체 `--shuffle-seed=1..5` 각 `239 passed, 3 xfailed`(exit 0, 실패·오류 0, 각 2.5~3.2분).
6. **V4**(gate `6c724de` 판 `test_lint.py --root <r> --interface-card <카드> --base 7fd4b16 --head 93d7c0a`, 파일 인자 없음 → 도구가 고른 파일 12 = 새 9 + ts3 + docstring 2): 피검 = 이 초안으로 만든 interface card 기존 함수 6(아래 10) →
   **FAIL 규칙 (1) 4줄**(s009 535·560행, s052 2006행, s054 2059행 -- 전부 `test_mod8_sizing_layout_convergence.py`), UNJUDGED 182, NO-SUBJECT 478. 새 id 셋을 target으로 한 decision 기록 시제품 커밋(`710d90c`)을 head로 하면 **PASS**(`exempt` 4, FAIL 0), `merge_gate.py parse-approval` 통과.
   **함정(R-12)**: 파일 목록을 `git diff --name-only --diff-filter=AM`(`--no-renames` 없이)로 넘기면 git이 `test_mod7`·`test_mod8`을 옛 파일의 rename으로 잡아 빼서 파일 10개만 lint -- 규칙 (1) 발견 0으로 거짓 PASS(NO-SUBJECT 280·UNJUDGED 72). 계약 11 판정 명령은 파일 인자 없이 쓴다.
7. **V5**(gate `6c724de` 판 `weakening_diff.py --base 7fd4b16 --head 93d7c0a`): FAIL, 발견 215 = assert 삭제 212(sizing 67·stick 131·DR 4·TL 10) + 리터럴 변경 3(ts3 목록, docstring 2), `diff_paths` 7, `diff_hash` `aad798728d13d4bab9bd9479a3dd0af79ea67137d8a491ae08020e6b5fa30131` -- r1·독립 검토와 같다(S-1 뒤에도 바뀌지 않음). `merge_gate.py diff-hash`로 다시 계산해도 같다.
   경로별 (base blob, head blob): ts3 `0791457`→`de632fe`, `test_probe_revalidation_scope.py` `4f3b7ae`→`6eb83e3`, `test_probe_role_L_derivation.py` `ceefa7e`→`0bf3bd2`, 옛 4파일 base blob → `-`(DR `56cc5a1`, SR `5396d84`, SD `fe724a8`, TL `1ad977e`). 실제 사슬에서는 T0가 고친 옛 파일 blob이 base에 들어가 해시 값은 달라질 수 있다(관계는 같다).
8. **V3·V6·V7**: 엔진 소스 변경 0 -- V7 PASS(`new_defs` 없음), V6 PASS `targets` [](r1 측정 -- r2는 엔진 diff가 같은 0이라 다시 재지 않음).
9. **이름 충돌(새 이름)**: `test_mod<k>_*.py`·`_selftest_shared.py` -- gate `6c724de` 추적 파일에 같은 이름 0. `contracts/*.py`를 읽는 `test_ic_markers_match_plan`은 contracts만, `rglob` 전수 스캔 3종은 본문 토큰을 보므로 옮긴 본문이 같으면 결과 같음(계약 8 PT3로 확인).
10. **양식**: gate `6c724de` `role_paths.parse_spec_card(text, expect_id="20261006-p3-test-relocate")` -- 예외 없음, phase 3·test-only·gate_change no·approval 3, 절 11. `interface_card.py <초안> --root <r2 T1 head>` -- exit 0, 기존 함수 6(`sizing_layout_convergence.optimize_full_circuit_budget`·`_build_theta_evaluator`, `gmid_sizing_engine.size_transistor`·`width_from_id_density`·`check_quasi_static`, `circuit_state_graph.load_topology`), 신규 시그니처 표 빈 것.
    r4(gate `6df4bd7` `tools/gates`·`A`·H 사본 `C:/g428`, 끝에 삭제): `parse_spec_card` 예외 없음·approval 3·절 11; `interface_card.py --root <6df4bd7 사본>` exit 0, 기존 함수 같은 6(정의 모듈 SR·SD -- M1~M9 미병합), 신규 시그니처 빈 표.
11. **앞 card 의존 재확인(오케스트레이터, card 커밋 직전)**: (i) gate `master`에 M10 판정 기록 (ii) 그 `code_commit`에서 생성기로 매핑 표를 다시 만들어 '재현할 수치'를 그 값으로 바꾼다(T0가 바꾼 W-1 3줄과 B26-1 계약 12의 `rails=` 입력 갱신이 머리·본문에 들어 있음 -- 매핑 규칙은 그대로)
    (iii) V4 면제 기록(T1-2 답) 커밋 확인 (iv) `git diff --stat <M10 병합> gate/master -- skills tools` 빈 출력 (v) 계약 11의 T0 interface 함수 목록을 gate의 T0 판정 기록 interface card '기존 함수'와 대조해 정확히 적는다('등' 금지 -- `interface_card.py`가 backtick 심볼로 피검을 정한다)
    (vi) 생성기 정본 `build_t1_mapping.py`가 계약 2 '엔진 import 0'을 만족(AST 검사·`sys.modules` 검사, 위 2와 같은 방법).
12. **브리프 가드(역할 agent 지시문에 넣을 것)**: 순서 3(auditor freeze·base 측정) 브리프에는 '이 단계에서는 커밋하지 않는다(no-commit)'를, 순서 6(병합본 판정) 브리프에는 '격리 경로 + `git -C <경로>` + `set -e` + 끝나면 reflog·status 확인'을 그대로 넣는다(메모리 원칙 -- 검증 agent git 실측 가드). auditor 브리프에 V4 판정 명령은 파일 인자 없이(R-12).
