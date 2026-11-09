---
id: 20261002-p3-callers-update
phase: 3
evidence_type: equivalence
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split` **v8.5**(사용자 승인 UD-0 `20260930-30-module-split-design`, 답 2026-10-02) §7.2·§8 F1 행·D-9·D-17·D-24·D-26·§10 E3/E3b/IMPORT-ANY, card **F1**.
A = `skills/analog-gmid-design/assets`, SR = `A/sizing_recipe.py`, TL = `A/topology_library.py`, DR = `A/design_report.py`, SD = `A/stick_diagram.py`, ACF = `A/audit_current_forced.py`.

**문제**: M1~M9(·M10·T1)가 끝나면 SR·TL·DR은 재수출만 남은 shim이고, SD는 SD 밖으로 나간 이름을 임시로 재수출한다(design §2.2). F2가 shim 셋과 SD의 임시 재수출을 지우려면 계획 534행
"추적 파일 호출부 갱신 후 shim 삭제"대로 **추적 파일이 그 경로로 읽는 곳을 먼저 전부 정의 모듈로 바꿔야 한다**. 빠뜨리면 V1이 수집하지 않는 파일(probe·workspaces 스크립트)은 F2 뒤 조용히 깨지고(design F9),
모듈 속성을 덮어써 계측하는 probe는 이동 뒤 계측을 조용히 잃는다(design F8). 이 card는 **동작을 바꾸지 않고** import 경로만 바꾼다.

**범위(design §7.2 v7 -- 이름 단위)**: SR·TL·DR은 **모듈 단위**(그 모듈을 import하는 곳 전부 -- §10 E3의 AST 식), SD는 **이름 단위**(F2 뒤 SD에 바인딩이 남지 않는 이름을 읽는 곳만 --
§10 E3b의 식). SD에 남는 이름(SD 단위가 스스로 읽어 import가 남는 `Transistor`·`load_topology` 등)의 `from stick_diagram import …`는 고치지 않는다. 그리고 그 import 변경 때문에 **판정이 깨지는 계약 test**
(엔진 파일 이름 앵커·기준 blob 대조 -- 계약 1 (c)(d))를 같은 card에서 고친다. D-9 제외 집합(`.ai/verification/**`, `docs/03-analysis/gain-budget-gmid-sizing-function-audit/probe_stage_partition.py`)은 고치지 않는다.

**원칙**: 동작 불변(계약 3·5·6), 정의 하나(목적지 = G1 `binding_origin`의 정의 파일 -- 손으로 정한 표가 아니다, 계약 2 (i)), 만들면 배선(새 def 없음 -- D-17 대입 대상은 실제 호출자 모듈), 작성자≠검증자(동등 판정기는 auditor가 독립으로 -- 계약 3;
workspaces 스크립트도 역할 커밋으로 -- 계약 4), topology 무관(회로·넷 이름 없음), 범위 최소(import 줄·모듈 식 자리·D-17 대입 대상·계약 1 (c)(d)의 줄 밖 변경 0), 판정 범위를 좁히지 않는다(앵커는 넓히거나 그대로 -- 계약 2 (iv)).

**자리(design §8.1)**: `M1 → … → M9 → M10 → T1 → F1 → F2`. base = **T1 병합 뒤 master**(T1이 `unit/test_selftest_*.py` 4개를 `unit/test_mod*.py`로 옮긴 뒤 -- 아래 실측의 파일 이름은 T1 전 이름이다).
F2의 착수 조건이다(design F9: F1이 빠뜨린 곳은 F2 뒤 E3b·E3가 잡는다). Phase 4 card는 Phase 3 DoD(F2 뒤) 전에 병합될 수 없으므로(계획 991행) **F1이 항상 Phase 4 #2보다 먼저다**.

**착수 조건(spec card 커밋 전, 오케스트레이터 확인)**:
(1) 계획 N3.12.2 쓰기 경로표에 `| gmid-code-author | \`workspaces/*/**/*.py\` | -- | 없음 |` 행이 gate `master`에 있다 -- 사용자 답 [F1] 쓰기 경로 (가) 2026-10-02, `plan_tables` 승인 기록 `20261002-p3-f1-workspaces-write-path`
    (`plan_tables_hash` `7167e028…` → `31828c5e059dd41ed7a89f4d8757c402f9f7a61340411444d8101855f0623b57`; 문서 커밋은 card 35 역할 브랜치 정리 뒤·이 card 전 -- 승인 초안 '커밋 시점').
(2) T0(W-1 (가) -- `20260930-p3-tests-location-free`)가 병합되어 F1 base에서 **shim 경유 비엔진 이름 읽기 0**: 추적 `.py`가 SR·TL·DR(과 SD의 F2 삭제 집합)에서 `from … import`·모듈 속성으로 읽는 이름 중
    `binding_origin`이 엔진 밖(`ext`·`ext-module`)인 것 0. 0이 아니면 **멈추고 묻는다**(그 줄의 비엔진 import 새 줄은 계약 3 (가)에서 FAIL한다 -- 비엔진 import는 정규화가 남긴다).
(3) D-17 정밀 정의 확인(계약 2 (iii) 끝): F1 base에서 두 정의가 다르면 멈추고 묻는다.

## 관찰 가능한 계약

1. **대상(auditor가 F1 base에서 계산 -- 손 목록이 아니다)**: D-9 제외 집합 밖 추적 `.py` 중 아래 (a)~(d)에 걸리는 파일. 엔진 파일 `A/*.py` 가운데 split 파일(SR·SD·TL·DR·ACF)과 N3.10 MOD 파일은 M card가 이미 MOD에서 직접 import하므로
   대상 계산에서 빼고, **그 밖 엔진 파일**(예: `topology_to_markdown.py` -- `from stick_diagram import load_topology`)은 같은 식으로 계산한다(대상이면 code-author 경로. 모의 0 -- SD 잔류 이름만 읽는다).
   (a) design §10 `E3_AST`(그대로)가 SR·TL·DR의 import 문(`stmt`)이나 import 호출(`call`)을 찾는 파일,
   (b) design §10 `E3B_AST`의 `file_reads`(그대로, ACF에도 같은 식)로 SD·ACF에서 읽는 이름 중 **F2 card 계약 2의 SD·ACF 삭제 집합**(정의 하나 -- F1 base SD·ACF로 계산)에 드는 이름을 읽는 파일
       (SD 삭제 집합 = F1 base SD 최상위 재수출 줄(`from <N3.10 줄기> import …`, level 0)이 묶는 이름 중 SD 단위가 **어느 유효 범위에서도** 읽지 않는 이름 -- G1 `SourceIndex.global_names(SD)`의 합에 없는 이름, design §2.2 v8 정정.
       ACF 삭제 집합 = B0 ACF에 없던 최상위 재수출 줄이 묶는 이름 중 `⋃ global_names(ACF)`에 없는 이름 -- 모의 reader 0, E3b는 SD만 보므로 이 card가 판정한다),
   (c) 엔진 파일 이름 앵커(design §7.1 B군): 문자열 상수 `"sizing_recipe.py"`·`"topology_library.py"`·`"design_report.py"`나 모듈 이름 문자열로 그 파일의 **존재**·그 모듈의 **import**를 단언하는 계약 test 줄
       -- 7줄·6파일(design §7.1 B행에 모두 있음, 실측 1): `test_d_delete_dead.py:74`·`test_d_delete_telescopic.py:117`·`test_d_move_tests.py:69·73`·`test_df35_harness_paths.py:206`·`test_dup_w_calc.py:56`·`test_ts6_probe_relocate.py:528`,
   (d) (a)~(c)의 변경 때문에 판정이 깨지는 **기준 blob 대조 test**: `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`(668~673행 -- `tests/tools/derive_achievable_bounds.py`를
       base 커밋 `939f926` blob과 비교해 '경로 줄 밖 차이 0'을 단언; 그 도구 33행 `import sizing_recipe as sr`이 (a) 대상이라 F1이 바꾸면 FAIL -- 실측 4. design §7.1 B군 표에 없다 -- design 정정 항목).
       **F1 test 커밋이 사용자 질문(F1·Phase 4 #2 한 질문, '결정 필요 항목' 1)의 답이 정한 규칙을 이 test에 적용한다** -- 이 test의 규칙 변경 주인은 F1이고 #2는 F1이 정한 규칙 위에서 시작한다.
       F1의 그 도구 변경은 **import 출처 변경뿐**이다(계약 2 (ii) -- 도구 33행 import와 `sr.` 모듈 식 자리. 계산·기록·문구 줄 불변, 계약 3 (가)).
   대상 = (a) ∪ (b) ∪ (c)의 파일 ∪ (d)의 파일. auditor는 이 집합을 **F1 base**에서 계산해 판정 기록에 적고, **F1 병합본이 바꾼 파일 집합 = 이 집합**이어야 한다(더함·빠짐 0).
   A군(정의 위치 가정 -- `test_ic5.py`·`test_dup_w_calc.py:442`·`test_ts6_dead_probes.py:221·261`)은 T0 몫이라 대상이 아니다(design D-12; 모의에서 T0 미적용 판은 그 3 test가 FAIL -- 실측 4).
2. **바꾸는 모양(정의 하나)**:
   (i) **목적지 = 정의 모듈**: 대상 파일이 SR·TL·DR(또는 SD·ACF의 F2 삭제 집합)에서 읽는 이름 n마다, F1 base 트리에서 그 모듈의 `binding_origin(…, n)`(G1 `reachability.SourceIndex`)이 가리키는 정의 파일의 모듈에서 직접 읽는다
       (`from <정의 모듈> import n [as a]`). 재수출 모듈(정의 모듈이 아닌 MOD)을 거쳐 읽지 않는다 -- 예외는 SD에 F2 뒤에도 남는 이름(design §7.2)뿐이다.
       엔진 밖 출처(shim이 import로 받아 재수출하던 `numpy`·`json`·`math`·`os`·`dataclasses.replace` 등)는 착수 조건 (2)로 F1 base에서 0이다(W-1 (가) -- T0가 닫음).
   (ii) **모듈 객체**(`import X as a`·`import X`·`import_module/_import/__import__("X")`·그 결과를 대입받은 이름·그것을 돌려주는 함수): 그 모듈 식으로 읽는 이름의 목적지가 하나면 **import 줄(또는 import 호출 문자열)만** 바꾼다
       (`import <정의 모듈> as a` -- 그 밖 줄 불변). 둘 이상이면 모듈 식 자리(속성 접두 `a.` · `getattr`류 첫 인자)를 이름별 정의 모듈로 바꾸고, 새 별칭 import는 **원래 import 문 바로 뒤**에 둔다(card 접두 없이 자유 -- 계약 3 (가)가 같은 표지 묶음으로 본다).
       `<모듈>.<이름>(…)` 속성 호출 모양은 유지한다(`from MOD import n`으로 바꾸지 않는다) -- design §7.1 v5 B행 `test_b34_grammar_explicit.py`가 V3 인벤토리 조건으로 그 모양을 요구한다.
       동적 이름(`getattr(m, 변수)`)·부재 단언(`not hasattr(m, X)`)처럼 목적지를 이름으로 정할 수 없는 모듈 객체는 '결정 필요 항목' 2의 기본안(이름마다 R-DEF 정의 모듈 / 부재는 모든 N3.10 모듈)으로 쓴다.
       **이름을 읽지 않는 엔진 import**(순서 고정용 `import sizing_recipe` -- 모의 1건 `contracts/test_restore_plan_functions.py:54`, 주석 '(run_harness보다 먼저)'): 같은 자리의 **N3.10 MOD10 진입 모듈 import**(`import <MOD10 줄기>`, 이름을 읽지 않는 채)로 바꾼다
       -- 원래 목적(트리의 엔진을 먼저 묶는다)이 MOD10에서 성립한다(MOD10이 파이프라인 진입이라 MOD1~9를 끌어온다; 모의는 MOD10이 없어 MOD9 `instance_report_builder`로 근사).
   (iii) **D-17 대입·호출**(엔진 모듈 식 속성을 대상으로 하는 대입문, 그리고 `setattr`·`delattr`·`<x>.setattr`·`<x>.delattr`(pytest `monkeypatch` 포함)의 첫 인자가 엔진 모듈 식이고 둘째 인자가 문자열 상수인 호출
       -- design §7.2 "Phase 3 시작 때 대입문과 `setattr` 두 형태로 다시 잰다"; F1 base(B26-1 뒤)에서 다시 센다, 모의 대입 14줄·호출 0): 대상을 **그 이름을 전역으로 읽고 같은 정의로 푸는 F1 base 엔진 모듈 전부**로 바꾼다
       (shim 셋 제외, 0이면 정의 모듈 하나. 대입문은 한 문장의 사슬 대입 `M1.n = M2.n = 값` 또는 같은 값의 대입 문장 여럿, 호출은 같은 값 인자의 연속한 호출 여럿 -- 정확한 문언은 test-author·code-author 몫, 판정은 계약 3 (라)).
       사슬의 모듈 속성이 아닌 대상(`… = wrapped = 값`의 `wrapped`)은 그대로 둔다. 덮어쓰기 범위를 늘리거나 줄이지 않는다.
       정밀 정의 대조: D-17 승인 원문("`binding_origin`으로 찾은 호출자 모듈 전부")과 'base에서 덮어쓴 모듈 X의 단위 중 그 이름을 전역으로 읽던 단위가 F1 base에서 놓인 모듈'이 모의 14/14 같다(실측 3) --
       **F1 base에서 한 줄이라도 다르면 멈추고 묻는다**(착수 조건 (3)).
   (iv) **앵커(1 (c)) -- 줄별 규칙**(test-author는 소스를 못 읽으므로 계약이 줄마다 정한다. 범위를 좁히지 않는다, 빈 범위 FAIL 유지):
       * 부재·경로 판정 범위 앵커 5줄 -- `test_d_delete_dead.py:74`·`test_d_delete_telescopic.py:117`(지운 이름의 **부재** 판정 범위), `test_d_move_tests.py:73`(옮긴 이름이 엔진에서 사라짐), `test_df35_harness_paths.py:206`(하네스 ASSETS 경로),
         `test_ts6_probe_relocate.py:528`(A 디렉터리 판정 전제): `"sizing_recipe.py"`(그 줄의 SR 파일 이름)를 **"계획 N3.10 표의 MOD 파일 전부가 있다"**로 바꾼다(파일 이름 목록 = interface card가 주는 N3.10 '파일' 열 10개 그대로; `stick_diagram.py`·`run_harness.py` 등 같은 줄의 다른 이름은 그대로).
         넓힘이다(F1 base·병합본·F2 뒤 모두 참). 이 줄들의 판정 이름에는 정의 파일이 없어(부재·경로) R-DEF가 정의되지 않는다(review S4).
       * 정의 앵커 1줄 -- `test_dup_w_calc.py:56` `_REQUIRED_ENGINE_FILES = ("sizing_recipe.py", "run_harness.py")`: `"sizing_recipe.py"`를 그 test가 판정하는 이름 `size_transistor`·`width_from_id_density`의 **R-DEF**(design §7.1, T0와 같은 규칙 -- 정의 파일, 이름마다 정확히 하나)로 바꾼다(모의: 둘 다 MOD4 `gmid_sizing_engine.py` -- 하나로 합친다).
       * import 앵커 1줄 -- `test_d_move_tests.py:69` `_REQUIRED_ENGINE_IMPORT = {"regression_runner": "sizing_recipe"}`(229·237행 `assert required_import in imported_modules(source)`): **"regression_runner가 import한 모듈 ∩ 엔진 모듈 집합 ≠ ∅"**로 바꾼다
         (엔진 모듈 집합 = 계획 N3.10 표 파일 줄기 ∪ 그 트리에 있는 shim 파일 줄기 `sizing_recipe`·`topology_library`·`design_report`). 판정 뜻('도구가 엔진 정의를 베끼지 않고 엔진을 import한다') 보존, 복사 금지 단언(234~235행)은 그대로.
         한 값('정의 모듈 하나')으로는 T만 얹은 F1 base(regression_runner는 아직 SR import -- code-author 경로라 F1 code가 바꾼다)와 병합본을 함께 통과할 수 없어 equivalence test-first가 불가능하다(review B1; regression_runner는 MOD1·MOD4에서 읽는다 -- 실측 1).
   (v) **기준 blob 대조(1 (d))**: '결정 필요 항목' 1의 사용자 답대로(F1 test 커밋이 적용).
   (vi) 정의가 없는 이름(base에서도 해석되지 않는 import -- 모의 1건 `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:20` `_cmfb_amp_gain_diode_load`, Phase 2 `d-delete-telescopic`(`6612902`)이 지운 함수):
       '결정 필요 항목' 3의 기본안.
3. **호출부 동등(auditor, 정적 -- 대상 파일마다 base(F1 base)·head(F1 병합본))**: auditor가 독립으로 쓴 판정기로 (가)~(마)가 모두 참.
   (가) **정규화 AST 같음**: 엔진·N3.10 모듈 import 문은 **지우지 않고 그 자리에 표지 문장**으로 바꾼다 -- 같은 문장 목록(같은 블록)에서 **연속한** 엔진 import 묶음 = 표지 하나(1→N 분할과 계약 2 (ii)의 '원래 import 바로 뒤' 새 별칭 import 허용;
       묶는 이름 집합은 (나)가 본다. `import a, X as b`처럼 섞인 문은 비엔진 몫을 남기고 그 뒤에 표지). 모듈 식(위 2 (ii)의 모듈 객체 식)은 표지 하나로 바꾼다.
       D-17 대입은 **모듈 속성 대상만** 표지 하나로 바꾸고(첫 모듈 속성 대상 자리) 그 밖의 대상(`Name` 등)은 남긴다. D-17 호출(2 (iii))을 담은 식 문장은 (종류, 이름, 값 식) 표지로 바꾸고 연속한 같은 표지는 하나로 본다.
       그 뒤 `ast.dump(…, include_attributes=False)`가 같다. 1 (c)(d)의 줄(그 test 함수·상수)은 이 비교에서 빼고 계약 2 (iv)(v)로 따로 판정한다.
       (import의 **자리**가 판정에 남는다 -- `__main__` 블록 뒤로 옮긴 import, `if False:` 안으로 넣은 import는 FAIL.)
   (나) **해석 같음**: from-import 이름마다 (묶는 이름 → 정의)의 정렬 목록이 **같고**(부분집합 아님), 모듈 식 속성·`getattr`류 상수 이름·D-17 호출 이름마다 등장 순서대로의 정의 목록이 같다
       -- base는 F1 base 트리(shim 경유), head는 F1 병합본 트리에서 G1 `binding_origin`으로 푼다. 정의가 없는 이름(2 (vi))은 (다) 대상이 아니고 (나)에서 base·head 모두 unresolved여야 한다.
   (다) **정의 모듈**: head의 바뀐 import·모듈 식마다 그 이름의 정의 파일 모듈을 직접 가리킨다(계약 2 (i) -- 예외: SD에 남는 이름).
   (라) **D-17**: 이름마다 head 대입·호출 대상 모듈 집합 = 계약 2 (iii) 집합(auditor가 F1 base에서 계산).
   (마) **이름 없는 엔진 import**: base에서 묶은 이름을 어디서도 읽지 않는 엔진 `import X`마다, head의 같은 자리(같은 표지 묶음)에 계약 2 (ii)의 MOD10 진입 모듈의 이름 없는 import가 같은 수만큼 있다.
   판정기 자기 점검(먼저, auditor): '거부해야 할 입력'의 판정기 변이가 각자 해당 식에서 FAIL(첫 일곱 줄).
4. **쓰기 경로(계획 N3.12.2 -- 사용자 답 [F1] 쓰기 경로 (가))**: 대상 중 `A/tests/**`(`A/tests/tools/**` 제외)는 gmid-test-author(test 커밋), `A/tests/tools/**`·`workspaces/run_harness.py`·**`workspaces/*/**/*.py`**(새 행 -- 모의 16파일)는
   gmid-code-author(code 커밋)다. 역할 밖 커밋·오케스트레이터 구현 없음 -- 16파일도 EL1~EL4와 계약 3·7을 그대로 받는다. `tests/conftest.py`는 `판정 환경` 행의 제외 glob이라 test-author가 쓰고 V5 무조건 승인이다.
   새 행 밖 경로(`workspaces/*.py`(한 조각)·`workspaces/*/__init__.py`·`**/conftest.py` 등 `판정 환경`)가 대상에 나오면 멈추고 묻는다(모의 0).
5. **트리 판정(auditor, F1 병합본)**:
   (a) design §10 **E3 AST 식**: D-9 밖 추적 `.py`에서 SR·TL·DR의 import 문·import 호출 0(PARSE-ERROR 포함, fail-closed). shim 셋은 아직 있으므로 §10 E3의 첫 루프(파일 부재)는 이 card의 판정이 아니다.
   (b) **삭제 집합 reader 0**: design §10 `E3B_AST`의 `file_reads`로 D-9 밖 추적 `.py`가 SD·ACF에서 읽는 이름 중 계약 1 (b)의 삭제 집합(F1 병합본 SD·ACF로 계산)에 드는 것 0.
   (c) **IMPORT-ANY**(design §10 `import_any` 그대로): `IMPORT-ANY tried=<n> expected=<n> failed=0`, `FAIL`·`INVALID` 줄 없음.
6. **동작 보존(auditor, base·병합본 같은 체크아웃 경로에서 차례로)**: (a) **PT3 전체**와 **PT3 --gmid-dod** 전체(design §10 정의): 두 판 모두 실패 0, 수집 test id 집합이 같고 id마다 결과가 같다.
   (b) **E-INST**(`e_inst_p3.py` -- design D-28 정본, design 커밋의 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`) 파일럿·`folded_cascode`: 출력 JSON이 `engine_origin` 밖 키 모두 같다
       (`engine_origin`은 shim 모듈 이름이 빠지는 것만 다를 수 있다 -- 같은 판정을 df36 사본으로 하지 않는 이유, D-28 (a)). stdout 사본은 `elapsed=<n>s`를 가리면 같다.
   (c) **E-LIB**(`e_lib.py` 사본 그대로) `hash` 같음.
7. **범위 밖 변경 0(이 card `Change-Id` 커밋들의 diff)**: 엔진 파일(`A/*.py`)·`tools/**`(단 `A/tests/tools/**`는 대상이면 허용)·레지스트리·계획·design·library·`.ai/verification/**`·D-9 파일 변경 0.
   바뀐 파일마다 바뀐 줄은 import 문·모듈 식 자리·D-17 대입·호출 대상·1 (c)(d)의 줄뿐(계약 3 (가)가 그 밖 차이를 잡는다).
8. **게이트(auditor, 판정 때 gate `master` 판 도구)**: V3 대상 def 0·변이 0(`defs` []·`moved` []·`move_rejected` {}; 범위 정책(35) 키 `not_targeted` 0·`targets_by_def` {}), V6 `findings` [], V7 `new_defs` [].
   V5는 test 변경의 **승인 대상**(design §9.2 '뒤에 올 승인: T1·F1의 V5 승인') -- 승인 목록(test 커밋 diff 해시와 함께, 승인 기록 범위 설명에 줄별로):
   ① `tests/conftest.py` import 변경 1(무조건 승인 -- `판정 환경` 제외 glob), ② import 호출 문자열 리터럴 변경(모의 9 -- 5파일), ③ 앵커 7줄(계약 2 (iv) 규칙별 -- 부재·경로 5줄 '넓힘', 정의 1줄 R-DEF, import 1줄 "비교 완화 1: `_REQUIRED_ENGINE_IMPORT`"),
   ④ TS6 비교 대상 1(`test_moved_tool_matches_base_except_path_lines` -- '결정 필요 항목' 1 답의 규칙), ⑤ '결정 필요 항목' 2 도우미(`_import_sizing_recipe` 3파일 동적 이름 → R-DEF, `test_ts6_dead_probes.py:229` 부재 → 모든 N3.10, `test_dup_kcl_edges.py:35` `_sd()`).
   (모의의 'V5 발견 10'은 ①②뿐인 판이다 -- 모의는 ③~⑤를 적용하지 않았다.)
   V4는 interface card의 '피검 심볼'이 비면 `ERROR` -- FU 선례(`--subject` 운영 진입 함수)대로 준다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**equivalence**(design §8 F1 행). 계획 N3.12.3(686행) "동작을 보존하는 변경(…Phase 3 이동)은 `equivalence`". F1은 엔진 동작을 바꾸지 않고 호출부의 import 경로만 바꾼다(계약 3 (나): 모든 읽기의 정의 출처가 같다).
test 커밋이 있다(test-author가 `A/tests/**`의 대상 파일을 고친다) -- equivalence의 "test 커밋이 그대로이고 base와 병합본 모두 통과"(680·686행): F1 test 커밋은 MOD에서 직접 import하므로
shim이 있는 base에서도, 병합본에서도 통과해야 한다(계약 6 (a)). 앵커 규칙(계약 2 (iv))은 그래서 두 트리에서 모두 참인 모양으로 정했다(B1). code 커밋은 `A/tests/tools/**`·`workspaces/run_harness.py`·`workspaces/*/**/*.py`(code-author 경로)다.
red-green이 아닌 이유: 새 동작이 없고, "shim을 거치지 않는다"를 단언하는 새 test는 F2(shim 삭제)의 red가 맡는다(F2 card 계약 6) -- 같은 단언을 두 card가 영구 test로 두지 않는다.

## oracle 종류와 출처

(c) 동작 보존: PT3·PT3 --gmid-dod test id별 결과, E-INST·E-LIB 출력, 계약 3의 정적 동등(base = F1 base 트리 자체). 기대값 = base 실행·해석 결과(auditor가 격리 복제본에서 같은 명령으로).
(a) 구성: 계약 1의 대상 집합(design §10 E3·E3b 식 그대로), 계약 2의 목적지(G1 `binding_origin` -- 정의 하나), D-17 호출자 집합(F1 base 엔진 모듈 중 그 이름을 전역으로 읽고 같은 정의로 푸는 모듈), 앵커 규칙(계약 2 (iv) -- N3.10 표·R-DEF).
test-author가 쓰는 import는 **interface card의 '이름 → 정의 모듈' 표와 N3.10 '파일' 열**(오케스트레이터가 F1 base에서 계약 2 (i)로 생성해 넣는다 -- test-author는 엔진 소스를 읽지 않는다)에서 온다.
`_drafts/p3kit_f12/f12_f1sim.py`(기계적 재작성)·`f12_equiv.py`(동등 판정 시제품 r1)는 작성 전 실측용이고 판정 도구가 아니다(작성자≠검증자).

## 거부해야 할 입력

auditor 판정기(계약 3) 자기 점검 -- 모의 F1 병합본 위의 변이 커밋(실측 5):
* 정의 모듈이 아닌 MOD를 거친 import(`workspaces/run_harness.py`의 `from gmid_lut import SemiEmpiricalGmIdLUT` → `from gmid_sizing_engine import SemiEmpiricalGmIdLUT` -- MOD4가 MOD1에서 import해 같은 객체로 풀린다) → (다) FAIL.
* import 밖 줄 변경(probe 문자열 리터럴 `"offset"` → `"offs"`) → (가) FAIL.
* D-17 대상에서 호출자 모듈 하나를 뺌(`probe_vds_assignment_paths.py` `resolve_feed_vds`의 `circuit_metrics`) → (라) FAIL.
* **h1** 엔진 from-import를 `if __name__ == "__main__": main()` **뒤**로 옮김(스크립트 실행 시 `NameError` -- V1·IMPORT-ANY는 `__main__` 블록을 돌리지 않는다) → (가) FAIL.
* **h2** D-17 호출의 대상 모듈을 바꿈(`setattr(<호출자 모듈>, "load_derived_bounds", …)` → `setattr(importlib.import_module("design_report"), …)` / 정의 아닌 재수출 MOD 별칭) → (라)·(나) FAIL.
* **h3** 이름을 읽지 않는 순서용 엔진 import 삭제(`test_restore_plan_functions.py:54` 모양 -- 순서 보장 소실) → (마) FAIL.
* **h4** 사슬 대입의 지역 대상 탈락(`M.x = wrapped = (…)` → `M.x = (…)` -- `wrapped` `NameError`) → (가) FAIL.
* 계약 5 (a): 대상 하나를 빠뜨린 병합본 → E3 AST 식이 그 파일을 FAIL로 낸다(design §10 E3 실측과 같은 식).
* 계약 2 (iv): 앵커의 범위를 좁힌 test(예: `_REQUIRED_ENGINE_FILES`를 빈 튜플이나 MOD 하나로) → 계약 8 V5 승인 목록 ③의 규칙과 diff가 다르다(auditor diff 대조).

## library 회로 적용 여부

적용 -- E-INST 파일럿·`folded_cascode`(하네스 `run()`이 F1이 바꾼 `workspaces/run_harness.py` import로 엔진을 부른다), E-LIB 9회로(`e_lib.py`는 D-9 사본이라 F1이 바꾸지 않는다 -- 대조 기준선).

## 무동작 판정 입력(무발동 값)

새 산출물 필드 없음. library 회로 전부·기존 test 전부의 판정·산출물이 base와 같다(계약 6). 발동 계수 ID 없음.

## 재현할 수치

(모의 -- 아래 '작성 전 실측' r1 사슬(gate `master` `4a286f0` + D-11 (가) 토큰 + names 키), 2026-10-02. **전부 관찰이고 기대값 근거가 아니다**: F1 base(M10·T1·T0 뒤)에서 auditor가 다시 계산한다.
'(hash 판)' 표시는 r0 사슬(`dd60db6`, `F12_STMTKEY=hash` -- 승인 판과 3문장 배정이 다름: `_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS` MOD8 → MOD4, `INSTANCE_TOP_FIELDS` MOD9 → SD 잔류)에서만 잰 수치다.)
* 대상: (a) 65파일 + (b)만 걸리는 6파일 = 71(+ (c)만 걸리는 3파일 = **74**). 쓰기 경로: test-author `A/tests/**` 55(그중 `tests/conftest.py` 1), code-author 3(`A/tests/tools/` 2 + `workspaces/run_harness.py`) + **16(`workspaces/*/**/*.py` 새 행)**.
* SD 재수출 이름 **57** = F2 삭제 **49** + SD가 읽어 남는 8. ACF 재수출 3 = 삭제 2 + 남김 1. reader(ACF 삭제 집합) 0.
* (hash 판) 바꾸는 이름: (모듈, 이름) 136쌍. 모듈 객체 뿌리 52개 중 목적지 하나 18·둘 이상 34(34파일). from-import 문 39(25파일), import 호출 9(5파일), 동적 `getattr` 9. D-17 14줄(8파일) -- r1 같음(14/14 대상 집합 같음).
* E3(AST) F1 전 65파일(D-9 밖) → F1 뒤 0. E3b(F2 삭제 49이름) F1 없는 F2: **49줄·12파일**(test_ic3 4줄 -- `INSTANCE_TOP_FIELDS`가 SD 잔류라 hash 판 50줄에서 1 빠짐) → F1 뒤 0. `E3b LIVE moved_out=57 base_files_reading_moved_out=32 pre_existing=1`. IMPORT-ANY `tried=13 expected=13 failed=0`(F1 전·뒤 같음).
* (hash 판) E-INST(`e_inst_p3.py` `7d26134a…`) 파일럿 `raw_sha256` `2fc426d9…`·`folded_cascode` `ef3cd996…` F1 전 = F1 뒤(22키 중 `engine_origin`만 다름: `sizing_recipe`·`design_report` 빠짐). E-LIB `hash` `1d2e3bf6…` 같음.
* (hash 판) V3 `targets` [`workspaces/run_harness.py`]·`mutants` 0·`defs` [], V6 PASS `findings` [], V7 PASS `new_defs` [], V5 FAIL(승인 없음) 발견 10 = 무조건 승인 1 + 리터럴 변경 9(계약 8 ①②만 적용한 판).
* 계약 3 판정 시제품 r1(`f12_equiv.py`): 71파일 중 PASS 63, FAIL 8 = 모의 재작성의 동적·부재 단언 형태 5(`ast_same`; `test_ts6_dead_probes.py`는 `attr_same`도 -- 계약 2 (ii) 기본안 미적용) + T0 미적용 selftest 3(`ast_same`·`from_same` -- 착수 조건 (2)).
  D-17 기대(판정기 계산) = 재작성기 호출자 집합 14/14. 옛 판(v1)과 PASS·FAIL 파일 같음. 변이: 위 '거부해야 할 입력' 첫 일곱 줄 모두 해당 식 FAIL(옛 판은 h1~h4 PASS -- 실측 5).

## 결정 필요 항목

1. **(사용자 질문 대기 -- F1·Phase 4 #2 한 질문, 선택지 측정 중: `_drafts/p4_ts6_question.md`) TS6 기준 blob 대조 test.** `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`는
   `A/tests/tools/derive_achievable_bounds.py`(현재 HEAD 내용)를 `939f926` blob과 비교해 경로 줄 밖 차이 0을 단언한다. 그 도구 33행 `import sizing_recipe as sr`은 계약 1 (a) 대상(추적 파일, D-9 밖)이라
   **F1이 반드시 바꾸고**(UD-1 (가) '추적 파일은 전부 F1에서 갱신'), 바꾸면 이 test가 FAIL한다(모의 실측 4: 33 passed → 1 failed·32 passed).
   * **병합 순서(확정)**: #2(`d4-delete-unwired`)는 `phase: 4`라 F1이 항상 먼저다 -- 이 test의 규칙 변경은 **F1 test 커밋**이 답대로 한 번 적용하고(계약 1 (d)), #2는 그 규칙 위에서 시작한다. 질문은 **한 번**(F1 V5와 #2 D1을 묶어).
   * **선택지(중립 -- 기본안 표기 없음, 측정은 #2 card 쪽에서 진행 중)**: 이동 커밋(`9d6800e`) blob 대조로 바꾸기((다)), 그에 HEAD 도구의 계산·기록 요소 AST 고정을 더하기(핀 -- 범위 측정 중: `_drafts/review_ts6_pin.md`),
     기준선에 F1 import 치환 반영((가)), 허용 줄에 import 문장 추가((나)), 비교 test 은퇴((라)). 각 안의 '잃는 보호'(예: (다)는 이후 어떤 도구 변경으로도 이 test가 FAIL하지 않는다 -- 고정된 두 이력 blob 대조)는 질문 문안이 실측 수치로 적는다.
     규칙 정의 본문은 답이 온 뒤 계약 1 (d)·2 (v)로 옮긴다.
   * **승인 경로**: 어느 안이든 기존 계약 test의 판정 변경이라 **V5 사용자 승인**(test 커밋 diff 해시) -- design §9.2 '뒤에 올 승인: T1·F1의 V5 승인' 범위, 계약 8 ④.
   * **design 정정 항목(따로, 사용자 질문 아님)**: design 30 §7.1 B군 표에 `test_ts6_probe_relocate.py:668-673`(F1)을 더한다(§9.1 '인용 줄·개수가 바뀌면 사실 문장 갱신'; UD-0의 '다시 묻는 개정'(N3.10)이 아니다).
2. **목적지를 이름으로 정할 수 없는 모듈 객체**(계약 2 (ii) 끝 -- 원칙 기본안, 질문 아님): `test_d_delete_dead.py`·`test_d_delete_telescopic.py`·`test_dup_w_calc.py`의 `_import_sizing_recipe()`(동적 `getattr(module, registry_name)`·여러 MOD 이름),
   `test_ts6_dead_probes.py:229`(`not hasattr(importlib.import_module("sizing_recipe"), _MISSING_SYMBOL)`), `test_dup_kcl_edges.py:35` `_sd()`(SD + MOD3 이름). 기본안(원칙 '정의 하나'·'판정 범위를 좁히지 않는다'):
   이름을 받는 도우미는 이름마다 R-DEF 정의 모듈을 돌려주고, **부재 단언은 '어느 N3.10 모듈에도 그 이름이 없다'**(한 MOD만 보면 범위가 좁아진다 -- 약화). 대안: 도우미가 MOD 이름 공간 합을 돌려준다(모의가 쓴 모양 --
   판정은 같지만 계약 3 (가)의 정규형 밖이라 auditor가 따로 본다). V5 승인 범위(계약 8 ⑤).
3. **정의 없는 이름의 import**(계약 2 (vi) -- 원칙 기본안, 질문 아님): `diagnose_cmrr_cmfb.py:20` `from sizing_recipe import (…, _cmfb_amp_gain_diode_load)` -- 그 함수는 Phase 2에서 지웠고(design 20 §5.4-3 기본안 '삭제하고 스크립트는 그대로 둔다') 스크립트는 base에서 이미
   `ImportError`다(같은 성격: design §11-10 `stick.py`의 `block_from_row_widths` -- E3b `pre_existing`). E3에는 `pre_existing` 장치가 없어 고치지 않으면 E3 FAIL. 기본안: 정의가 있는 이름은 계약 2 (i)대로, 없는 이름은 **같은 문장에 남은 정의 모듈 import 중 하나**에 둔다
   (같은 문장에서 같은 `ImportError` -- 깨진 상태를 고치지도 숨기지도 않는다. 어느 모듈에 두든 동작이 같으므로 고르는 규칙은 판정하지 않는다: 계약 3 (다) 대상 아님, (나)에서 base·head 모두 unresolved). 대안: 사용자 workspaces 정리(백로그 -- §11-10과 함께).
4. **(사용자 결정 완료 -- [F1] 쓰기 경로 (가), 2026-10-02) workspaces 하위 스크립트 16개**: 계획 N3.12.2에 code-author `workspaces/*/**/*.py` 행을 더하는 판정 표 개정(`plan_tables` 승인 `20261002-p3-f1-workspaces-write-path`)으로 F1 code 커밋이 고친다(계약 4).
   역할 밖 커밋안(r0 기본안)은 버렸다 -- design 05 §8.2-1의 '역할 밖 = gmid 밖 작업' 정의와 B36 선례에 어긋났다(review S3). 대상 계산은 F1 base 하나에서 한다(review S2 해소 -- 역할 밖 커밋·두 트리 없음).
5. **(사용자 결정 완료 -- W-1 (가), 2026-10-02) F1 base에서 이미 깨져 있을 import**: SR·TL·DR이 완전 shim이 되는 M card에서 design §3 SHIM (b)가 '남은 일반 import 줄'을 지워
   `unit/test_selftest_sizing_recipe.py:24`(SR에서 `np`·`json`·`math`·`_dc_replace`·TL 이름 `nmcnr_predict_ac_response`)·`unit/test_selftest_topology_library.py:24`(TL에서 `math`)·`unit/test_selftest_design_report.py:24`(DR에서 `os`)가 수집 `ImportError`가 된다(모의 M9 실측 4).
   **T0가 닫는다**(그 세 줄의 비엔진 이름을 출처 import로 -- T0 V5 승인 기록 `20260930-p3-tests-location-free`). F1 base에서 그 이름들은 이미 출처 import이고 F1은 같은 줄의 엔진 이름만 바꾼다(T1 뒤 파일 이름 `test_mod*.py`). 확인은 착수 조건 (2).
   SR의 `from stick_diagram import (Transistor, load_topology, …)`(base 5302행)·DR의 `from stick_diagram import load_topology, _audit_result_json`(base 32행)은 SHIM (c)상 base 재수출이라 남는다(모의 M9 정정 판에서 남김).
6. **(사용자 결정 완료 -- D-11 (가), 2026-10-02) 단위 키와 배정**: D0a 계약 2 키(바인딩 이름) + N3.10 MOD1 `_QUERY_CACHE_MAX` 토큰(`20261002-p3-d11-query-cache-max`)으로 `upward`·`cycles` 0. 이 card의 r1 모의가 그 판이다
   (배정 403, MOD 8·18·82·**104**·21·11·SD **111**·**30**·**16** -- hash 판과 3문장 다름, 실측 머리). 목적지 표(interface card)는 F1 base에서 `binding_origin`으로 계산하므로 계약은 그대로다.

## 작성 전 실측

(r1 재측정 = gate `master` `4a286f0`(`git -C <repo> rev-parse HEAD master` 둘 다 `4a286f0fad4f…`), 2026-10-02. 격리 복제본 `C:/g230/r`(`git -c core.autocrlf=false clone --no-local`, origin 제거, 빈 hooksPath, TMP/TEMP `C:/g230/tmp`), 작업 끝에 `C:/g230` 삭제.
실제 저장소 쓰기 없음(`status --porcelain` 37줄·HEAD·reflog 첫 줄 시작과 같음). 스크립트 `_drafts/p3kit_f12/`.
**모의 사슬 r1**(B34·b26pre·backfill·B26-1·B33·G1·FU·D0a·D0b·T0·M1~M10·T1 모두 미병합): `4a286f0` → `bf5f3cd`(D-11 (가) 토큰 -- 계획 521행) → `9f45a9f`(G1 시제품 `g1_kit/install_proto.py` `installed 4`) →
**D-31 배정**: `plan_d31.py`(names 키 -- D0a 계약 2 문언) = 배정 403·`upward`/`cycles`/`unassigned`/`conflicts` 0·MOD별 8·18·82·104·21·11·SD 111·30·16·ACF 2(독립 검토 1절 재현과 같음; hash 키 판 `out/plan_d31h.json`과 3문장 다름) →
`2e70cad`(M1~M9: `sim_m_d31.py bottom7`, 미대응 단위 0, 모든 card import 실패 0) → `daae48d`(**M9 정정** -- 완전 shim SR·DR에서 지워진 `from stick_diagram import …` base 재수출 문을 base 원문 그대로 파일 끝에 되살림, SHIM (c)) = **F1 모의 base**.
F2 모의(F1 없음) `8ee0845`(`mk_f2.py --acf`), F1 모의 `6b58942`(`F12_B0PRE=9f45a9f f12_f1sim.py daae48d 8ee0845` 71파일 + `test_restore_plan_functions.py` `_import("sizing_recipe")` 남은 4곳 → `_import("gmid_lut")` 손 보정 -- 재작성기가 첫 곳만 바꿈),
F2 모의 `3115856`(`mk_f2.py --acf`). 사슬 명령(손 단계 2곳 포함, review m14) = `p3kit_f12/mk_chain_r1.sh`, 출력 `p3kit_f12/out/{plan_names,callers_names,equiv_r1_f1}.json`·`sec10_*.txt`·`att_r1/`. M10·T1·T0·D0b 재생성은 모의하지 않았다. r0 사슬(`dd60db6`, hash 키, `3f61526`/`2fd53cc`/`3bcab98`)은 r1과 3문장 배정만 다르다 -- PT3·E-INST·V 도구는 r0에서만 쟀다('(hash 판)').
1. **사실 문장 재측정(r1)**: 대상 계산 `f12_callers.py daae48d` → 엔진 split 모듈을 읽는 추적 `.py` 100개(r0 99 + `docs/03-analysis/…/scripts/e_lib_p3.py` -- UD-0 design 커밋이 더함, SD 잔류 이름만 읽어 대상 아님) 중 바꿀 곳 74(D-9 안 3) → **D-9 밖 71**
   (SR·TL·DR importer 65 + SD 삭제 이름만 읽는 6: `test_df36_instance_relpath.py`·`test_dup_kcl_edges.py`·`test_ic3.py`·`rerun_symmetry.py`·`stick.py`·`structural_symmetry_probe.py`), 디렉터리별 probes 32·workspaces/current-reuse 12·unit 10·contracts 8·
   workspaces/two-stage 4·tests 루트 2·tests/tools 2(`derive_achievable_bounds.py`·`regression_runner.py`)·`run_harness.py` 1. SD 재수출 이름 57 중 F2 삭제 49·SD가 읽어 남는 8(`Transistor`·`_scan_case_collisions`·`find_hub_merge_candidates`·`find_matching_candidates`·`find_stack_edges`·
   `find_stacked_matching_candidates`·`kcl_series_union`·`load_topology`). 앵커(문자열 상수 AST 스캔 `an5.py`, r0): 계약 1 (c) 7줄·6파일 -- 줄 원문은 계약 2 (iv)에 인용(`4a286f0` `git show`로 재확인). `regression_runner.py` import: F1 모의 base `from sizing_recipe import (…)`, F1 모의 `from gmid_lut import …`·`from gmid_sizing_engine import _COMPENSATION_REGISTRY, optimize_multistage`(B1 -- 엔진 모듈 둘).
2. **이름 충돌**: 새 파일 없음(기존 파일만 고친다). 새 별칭은 대상 파일 안 지역 이름이라 glob·전수 스캔과 무관 -- 단 T0 계약 9의 전수 스캔 토큰 목록을 test-author가 피한다(design §7.1 R-DEF 절).
3. **D-17(design §7.2 S11 재측정, 대입문 + `setattr`/`delattr`/`monkeypatch.setattr`)**: 대입 14줄·8파일(probe 12 + workspaces 2), 호출형 0(`git grep "setattr(\|delattr("` 모의 F1 트리 `tools/` 밖 0 -- B26-1 미병합 판. F1 base에서 다시 센다).
   r1 대상 집합(판정기 계산 = 재작성기 호출자 집합, 14/14 같음): `probe_b22_headroom_attribution.py:104·116` `diode_vds_window` → MOD4; `probe_diode_gmid_readiness.py:63` `_hr_resolve_vertical_group` → MOD4·MOD8; `probe_diode_pass_skips.py:94`
   `apply_diode_self_consistent_gm_id` → MOD8(정의는 MOD4 -- 정의 모듈이 아니라 호출자); `probe_diode_window_corner.py:100·108` `diode_vds_window` → MOD4; `probe_matching_pair_divergence.py:124` `_optimize_theta_slsqp` → MOD8;
   `probe_vds_assignment_paths.py:47` `resolve_feed_vds` → MOD5·MOD4, `:53` `_feed_vds_fallback` → MOD4·MOD8, `:62` `allocate_stack_headroom` → MOD4, `:73` `_metric_stage_budget_vds_by_device` → MOD8(정의 MOD4), `:79` `_hr_resolve_vertical_group` → MOD4·MOD8;
   `diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20` `repair_matching_safety`(정의 SD) → MOD8. 정밀 정의 두 판(r0 `an6.py`)도 14/14 같음.
4. **기존 계약 test(PT3 모의, r0 `run_pt3.sh` -- (hash 판))**: F1 모의 base = `3 errors during collection`(exit 2 -- 결정 필요 항목 5, T0가 닫음), F1 모의 = 5 failed·1042 passed·15 xfailed
   (F1 몫 2: `test_d_move_tests::test_new_tool_modules_do_not_copy_engine_definitions`(69행 -- 계약 2 (iv) B1 규칙), `test_ts6_probe_relocate::test_moved_tool_matches_base_except_path_lines`(계약 1 (d)) /
   T0 몫 3: `test_dup_w_calc::test_size_transistor_calls_new_function`·`test_ic5::test_gate_docstring_declares_blind_spots`·`test_ts6_dead_probes::test_audit_vsb_consistency_has_operational_caller`),
   F2 모의 = 14 failed(+9: 계약 1 (c) 앵커 7줄이 부르는 test 8 + T0 몫 1). 단일 실행: `test_ts6_probe_relocate.py` 33 passed → 1 failed·32 passed(F1 모의). 조정은 전부 V5 승인 경로(계약 8).
5. **계약 3 판정기 r1(`f12_equiv.py` -- review S1 (a)~(d) 반영; 옛 판 `f12_equiv_v1.py`)**:
   * F1 모의(`daae48d → 6b58942`, `--d17 out f1sim`): 71파일 PASS 63·FAIL 8(재현할 수치) -- 옛 판 v1도 같은 판에서 63·8, FAIL 파일 같음. D-17 기대(판정기 계산) = 재작성기 호출자 집합(차이 0).
   * 합성 공격 probe(`tests/probes/zz_attack.py` -- 순서용 `import sizing_recipe`, `import sizing_recipe as sr`, `from sizing_recipe import spec_fingerprint`, `setattr(sr, "load_derived_bounds", …)`, `sr.diode_vds_window = wrapped = (…)`, `__main__` 블록;
     base `8669812` = F1 모의 base + probe, good `7fb9305` = F1 모의 + 규칙대로 고친 probe(순서용 → `import instance_report_builder`, `sr` → `gmid_sizing_engine`, `setattr` 대상 → 호출자 `theta_search` 별칭, from → `circuit_state_graph`)):
     | head(`out/att_r1/revs.txt`) | 옛 판 v1(`--d17` = 재작성기 집합 + probe) | r1 |
     |---|---|---|
     | good `7fb9305` | PASS | **PASS** |
     | h1 from-import를 `__main__` 블록 뒤로 `f837556` | PASS(속음) | **FAIL** (가) |
     | h2 `setattr` 대상 → `importlib.import_module("design_report")` `e836af3` | PASS(속음) | **FAIL** (나)·(라)(+ 안 읽힌 별칭 import → (마)) |
     | h2b `setattr` 대상 → 재수출 MOD 별칭 `sr`(MOD4) `5acf8e7` | PASS(속음) | **FAIL** (나)·(라)·(마) |
     | h3 순서용 import 삭제 `334de9e` | PASS(속음) | **FAIL** (마) |
     | h4 `sr.diode_vds_window = wrapped = (…)` → `… = (…)` `dbdbab3` | PASS(속음) | **FAIL** (가) |
     | h5 import 셋을 `if False:` 안으로 `e33f2b4` | FAIL | **FAIL** (가) |

     review 1절의 h1~h4(옛 판 4/5 속음)가 r1에서 모두 FAIL이고, 실제 F1 모의(위 첫 점)와 good은 PASS 그대로다.
   * (다)의 예외(SD에 남는 이름)를 넣지 않으면 `test_ic3.py`·`test_selftest_stick_diagram.py`·`rerun_symmetry.py`·`stick.py`·`structural_symmetry_probe.py` 5파일이 거짓 FAIL(r0 측정, design §7.2가 남기기로 한 import).
6. **트리 판정(§10 블록 그대로 실행, r1 `run_sec10.sh`, B0 = `9f45a9f`)**: F1 모의 `6b58942`: `E3 PASS`(첫 루프는 shim 세 파일 있음 -- 이 card 판정 밖), `E3b LIVE moved_out=57 base_files_reading_moved_out=32 pre_existing=1`·`E3b PASS`,
   `IMPORT-ANY tried=13 expected=13 failed=0`. F1 없는 F2 `8ee0845`: E3 FAIL 65파일, **E3b FAIL 49줄·12파일**(test_df36_instance_relpath 4·test_dup_kcl_edges 2·test_ic3 4·test_selftest_design_report 1·test_selftest_stick_diagram 27·rerun_symmetry 1·
   smoke_run_harness_session20 2·stick 1·structural_symmetry_probe 1·run_harness 2·check_box_shape 2·check_box_shape_M5M7split 2 -- design v8 근사 '49줄·12파일'과 같음).
7. **V 도구((hash 판) `run_vtools.sh` -- base 판 = G1 시제품 설치본)**: V3 PASS `targets` [`workspaces/run_harness.py`]·`mutants` 0·`defs` [](모듈 수준 import만 바뀐다 -- V3는 def만 본다), V6 PASS `findings` [], V7 PASS `new_defs` []·`unreached` [],
   V5 FAIL 발견 10(`diff_paths` 6). 범위 정책(35) 시제품은 이 판에 없다 -- 바뀐 def 0이라 `not_targeted`·`targets_by_def`도 0·{}일 것(FU 실측 8과 같은 이유). workspaces 16파일은 `classify` None(5분류 밖)이라 V3 대상 소스가 아니다.
8. **V3 규모**: 바뀐 def 0(엔진 소스 중 바뀌는 것은 `run_harness.py` 모듈 수준 import 줄뿐 -- M10 뒤 하네스 import 모양은 F1 base에서 다시 잰다). 인벤토리 test 0.
9. **동작((hash 판) E-INST·E-LIB, 같은 체크아웃 경로에서 차례로)**: M9·F1·F2 세 판 모두 exit 0, 파일럿 `raw_sha256` `2fc426d9ef3a…`·`folded_cascode` `ef3cd9963d0a…`(FU card 재현 수치와 같다),
   22키 중 `engine_origin`만 다름(M9 모의 11모듈 → F1·F2 9모듈). E-LIB `hash` `1d2e3bf6acf7…` 세 판 같음. 한 판 시간 파일럿 289~330 s·`folded_cascode` 37~44 s.
10. **쓰기 경로**(계획 N3.12.2, 개정 판으로 `role_paths.allowed` -- 승인 초안 측정): `A/tests/**`(tools 제외) = gmid-test-author(55파일), `A/tests/tools/**`·`workspaces/run_harness.py`·`workspaces/*/**/*.py` = gmid-code-author(3 + 16),
    `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py` 개정 전 '맞는 행 없음' → 개정 뒤 code-author 허용·test-author·오케스트레이터 거부. 판정 기록 = auditor. interface card '이름 → 정의 모듈' 표 = 오케스트레이터.
11. **계획서 소비자**: 지우거나 옮기는 이름 없음(import 경로만). 계획 534행 shim 문장·D-9 개정 문안은 design 커밋에 이미 있다(UD-0). 계획 개정은 N3.12.2 한 행(승인 초안 -- 이 card 밖 오케스트레이터 문서 커밋).
12. **미배선**: 새 def 없음. V7 `new_defs` [].
13. **승인 줄**: 동작 변경 없음 -- design 승인 UD-0 `20260930-30-module-split-design`이 덮는다(D-9·D-17 기본값은 UD-0 '기준에 닿는 기본값' (a)(b)). 범위 설명이 "F1 `p3-callers-update`, F2 `p3-shim-delete`"를 slug로 적는다(id 날짜는 card 작성 때).
    쓰기 경로는 `plan_tables` 승인 `20261002-p3-f1-workspaces-write-path`(착수 조건 (1)). test 판정 변경(계약 8 ①~⑤)은 V5 승인 -- test 커밋 뒤 diff 해시로.
14. **범위 계약**: 계약 7은 '이 card `Change-Id` 커밋들의 diff'로 한정(역할 밖 커밋 없음).
15. **같음 판정**: 계약 3은 `ast.dump(include_attributes=False)` 문자열과 (이름, 정의 튜플) 정렬 목록·등장 순서 목록을 `==`로 비교한다(부분집합 아님). 계약 6 (a)는 test id별 결과 문자열.
16. **red 모양**: red 없음(equivalence). 계약 3·5는 auditor 측정이다.
