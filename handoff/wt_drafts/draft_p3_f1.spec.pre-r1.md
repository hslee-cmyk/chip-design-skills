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

**원칙**: 동작 불변(계약 3·5·6), 정의 하나(목적지 = G1 `binding_origin`의 정의 파일 -- 손으로 정한 표가 아니다, 계약 2 (i)), 만들면 배선(새 def 없음 -- D-17 대입 대상은 실제 호출자 모듈), 작성자≠검증자(동등 판정기는 auditor가 독립으로 -- 계약 3),
topology 무관(회로·넷 이름 없음), 범위 최소(import 줄·모듈 식 자리·D-17 대입 대상·계약 1 (c)(d)의 줄 밖 변경 0).

**자리(design §8.1)**: `M1 → … → M9 → M10 → T1 → F1 → F2`. base = **T1 병합 뒤 master**(T1이 `unit/test_selftest_*.py` 4개를 `unit/test_mod*.py`로 옮긴 뒤 -- 아래 실측의 파일 이름은 T1 전 이름이다).
F2의 착수 조건이다(design F9: F1이 빠뜨린 곳은 F2 뒤 E3b·E3가 잡는다).

## 관찰 가능한 계약

1. **대상(auditor가 F1 base에서 계산 -- 손 목록이 아니다)**: D-9 제외 집합 밖 추적 `.py`(엔진 파일 `A/*.py` 제외 -- 엔진은 M card가 이미 MOD에서 직접 import한다. ACF는 아래 (b)에 걸리지 않으면 대상 아님) 중
   (a) design §10 `E3_AST`(그대로)가 SR·TL·DR의 import 문(`stmt`)이나 import 호출(`call`)을 찾는 파일,
   (b) design §10 `E3B_AST`의 `file_reads`(그대로)로 SD에서 읽는 이름 중 **F2 삭제 집합**에 드는 이름을 읽는 파일 -- F2 삭제 집합 = F1 base SD의 최상위 재수출 줄(`from <N3.10 줄기> import …`, level 0)이 묶는 이름 중
       SD 단위가 **어느 유효 범위에서도** 읽지 않는 이름(G1 `SourceIndex.global_names(SD)`의 합에 없는 이름 -- design §2.2 v8 정정: 함수 몸체에서만 읽는 이름도 '읽는다'),
   (c) 엔진 파일 이름 앵커(design §7.1 B군): 문자열 상수 `"sizing_recipe.py"`·`"topology_library.py"`·`"design_report.py"`나 모듈 이름 문자열로 그 파일의 **존재**·그 모듈의 **import**를 단언하는 계약 test 줄
       -- 모의 실측 7줄·6파일(아래 실측 1): `test_d_delete_dead.py:74`·`test_d_delete_telescopic.py:117`·`test_d_move_tests.py:69·73`·`test_df35_harness_paths.py:206`·`test_dup_w_calc.py:56`·`test_ts6_probe_relocate.py:528`,
   (d) (a)~(c)의 변경 때문에 판정이 깨지는 **기준 blob 대조 test**: `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`(672행 근처 -- `tests/tools/derive_achievable_bounds.py`를
       base 커밋 `939f926` blob과 비교해 '경로 줄 밖 차이 0'을 단언; 그 도구 33행 `import sizing_recipe as sr`이 (a) 대상이라 F1이 바꾸면 FAIL -- 모의 실측 4. **design §7.1 B군 표에 없다** -- design 정정 항목, '결정 필요 항목' 1).
       단 Phase 4 #2 card가 먼저 병합되어 그 test가 이미 HEAD 도구를 읽지 않으면 (d)는 빈 집합이다('결정 필요 항목' 1 경우 (1)).
   대상 = (a) ∪ (b) ∪ (c)의 파일 ∪ (d)의 파일. auditor는 이 집합을 F1 base에서 계산해 판정 기록에 적고, **F1 병합본(과 계약 4의 역할 밖 커밋)이 바꾼 파일 집합 = 이 집합**이어야 한다(더함·빠짐 0).
   A군(정의 위치 가정 -- `test_ic5.py`·`test_dup_w_calc.py:442`·`test_ts6_dead_probes.py:221·261`)은 T0 몫이라 대상이 아니다(design D-12; 모의에서 T0 미적용 판은 그 3 test가 FAIL -- 실측 4).
2. **바꾸는 모양(정의 하나)**:
   (i) **목적지 = 정의 모듈**: 대상 파일이 SR·TL·DR(또는 SD의 F2 삭제 집합)에서 읽는 이름 n마다, F1 base 트리에서 그 모듈의 `binding_origin(…, n)`(G1 `reachability.SourceIndex`)이 가리키는 정의 파일의 모듈에서 직접 읽는다
       (`from <정의 모듈> import n [as a]`). 엔진 밖 출처(`numpy`·`json`·`math`·`os`·`dataclasses.replace` 등 -- shim이 import로 받아 재수출하던 이름)는 그 출처에서 직접 import한다.
       재수출 모듈(정의 모듈이 아닌 MOD)을 거쳐 읽지 않는다 -- 예외는 SD에 F2 뒤에도 남는 이름(design §7.2)뿐이다.
   (ii) **모듈 객체**(`import X as a`·`import X`·`import_module/_import/__import__("X")`·그 결과를 대입받은 이름·그것을 돌려주는 함수): 그 모듈 식으로 읽는 이름의 목적지가 하나면 **import 줄(또는 import 호출 문자열)만** 바꾼다
       (`import <정의 모듈> as a` -- 그 밖 줄 불변). 둘 이상이면 모듈 식 자리(속성 접두 `a.` · `getattr`류 첫 인자)를 이름별 정의 모듈로 바꾼다(새 별칭은 card 접두 없이 자유, 단 계약 3 (가)가 같은 정규형으로 본다).
       동적 이름(`getattr(m, 변수)`)·부재 단언(`not hasattr(m, X)`)처럼 목적지를 이름으로 정할 수 없는 모듈 객체는 '결정 필요 항목' 2의 기본안(이름마다 R-DEF 정의 모듈 / 부재는 모든 N3.10 모듈)으로 쓴다.
   (iii) **D-17 대입**(엔진 모듈 식 속성을 대상으로 하는 대입 -- F1 base 실측 14줄, 아래 실측 3): 대상을 **그 이름을 전역으로 읽는, base에서 덮어쓴 모듈 X의 단위가 F1 base에서 놓인 모듈 전부**로 바꾼다
       (한 문장의 사슬 대입 `M1.n = M2.n = 값` 또는 같은 값의 대입 문장 여럿 -- 정확한 문언은 test-author 몫, 판정은 계약 3 (라)). 덮어쓰기 범위를 늘리거나 줄이지 않는다(D-17 '호출자 모듈 전부'의 정밀 정의 --
       14줄 모두 'F2 모의 트리의 모든 호출자 모듈'과 같은 집합, 실측 3).
   (iv) **앵커(1 (c))**: 존재·import 단언의 파일·모듈 이름을 **R-DEF**(design §7.1, T0와 같은 규칙 -- 그 test가 판정하는 이름의 정의 파일, 정확히 하나)로 구한 것으로 바꾼다. 범위를 좁히지 않는다(빈 범위 FAIL 유지).
   (v) **기준 blob 대조(1 (d))**: '결정 필요 항목' 1의 기본안 (다).
   (vi) 정의가 없는 이름(base에서도 해석되지 않는 import -- 모의 실측 1건 `workspaces/current-reuse-telescopic-ota-report/diagnose_cmrr_cmfb.py:20` `_cmfb_amp_gain_diode_load`, Phase 2 `d-delete-telescopic`(`6612902`)이 지운 함수):
       '결정 필요 항목' 3의 기본안.
3. **호출부 동등(auditor, 정적 -- 대상 파일마다 base(F1 base)·head(F1 병합본))**: auditor가 독립으로 쓴 판정기로 (가)~(라)가 모두 참.
   (가) **정규화 AST 같음**: 엔진·N3.10 모듈 import 문의 그 별칭(`import a, X as b`에서는 X 별칭만)을 지우고, 모듈 식(위 2 (ii)의 모듈 객체 식)을 표지 하나로, D-17 대입 대상 목록을 표지 하나로 바꾼 뒤
       `ast.dump(…, include_attributes=False)`가 같다. 1 (c)(d)의 줄(그 test 함수·상수)은 이 비교에서 빼고 계약 2 (iv)(v)로 따로 판정한다.
   (나) **해석 같음**: from-import 이름마다 (묶는 이름 → 정의), 모듈 식 속성·`getattr`류 상수 이름마다 등장 순서대로 정의 -- base는 F1 base 트리(shim 경유), head는 F1 병합본 트리에서 G1 `binding_origin`으로 푼 결과가 같다.
   (다) **정의 모듈**: head의 바뀐 import·모듈 식마다 그 이름의 정의 파일 모듈을 직접 가리킨다(계약 2 (i) -- 예외: SD에 남는 이름).
   (라) **D-17**: head 대입 대상 모듈 집합 = 계약 2 (iii) 집합(이름마다).
   판정기 자기 점검(먼저, auditor): '거부해야 할 입력'의 세 변이가 각자 해당 식에서 FAIL.
4. **역할 밖 경로(쓰기 경로표)**: 대상 중 `workspaces/<하위 디렉터리>/*.py`(모의 16파일)는 계획 N3.12.2 어느 역할 행에도 없어(`role_paths.allowed` '맞는 행 없음') 역할 커밋에 넣을 수 없다.
   기본안('결정 필요 항목' 4): **오케스트레이터가 F1 test 커밋 전에 역할 밖 커밋 하나로 갱신**하고(트레일러 없음 -- design 05 §8.2-1), F1 auditor가 그 커밋(부모 → 그 커밋)에 계약 3을 같은 판정기로 재고 판정 기록에 함께 적는다.
   그래서 F1 base는 그 커밋 뒤 master이고, 계약 1의 대상 계산·계약 5의 E3는 그 커밋을 포함한 트리에서 한다.
5. **트리 판정(auditor, F1 병합본)**:
   (a) design §10 **E3 AST 식**: D-9 밖 추적 `.py`에서 SR·TL·DR의 import 문·import 호출 0(PARSE-ERROR 포함, fail-closed). shim 셋은 아직 있으므로 §10 E3의 첫 루프(파일 부재)는 이 card의 판정이 아니다.
   (b) **SD 삭제 집합 reader 0**: design §10 `E3B_AST`의 `file_reads`로 D-9 밖 추적 `.py`가 SD에서 읽는 이름 중 F2 삭제 집합(계약 1 (b) 정의, F1 병합본 SD로 계산)에 드는 것 0.
   (c) **IMPORT-ANY**(design §10 `import_any` 그대로): `IMPORT-ANY tried=<n> expected=<n> failed=0`, `FAIL`·`INVALID` 줄 없음.
6. **동작 보존(auditor, base·병합본 같은 체크아웃 경로에서 차례로)**: (a) **PT3 전체**와 **PT3 --gmid-dod** 전체(design §10 정의): 두 판 모두 실패 0, 수집 test id 집합이 같고 id마다 결과가 같다.
   (b) **E-INST**(`e_inst_p3.py` -- design D-28 정본, design 커밋의 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`) 파일럿·`folded_cascode`: 출력 JSON이 `engine_origin` 밖 키 모두 같다
       (`engine_origin`은 shim 모듈 이름이 빠지는 것만 다를 수 있다 -- 같은 판정을 df36 사본으로 하지 않는 이유, D-28 (a)). stdout 사본은 `elapsed=<n>s`를 가리면 같다.
   (c) **E-LIB**(`e_lib.py` 사본 그대로) `hash` 같음.
7. **범위 밖 변경 0(이 card `Change-Id` 커밋들의 diff + 계약 4의 역할 밖 커밋)**: 엔진 파일(`A/*.py`)·`tools/**`(단 `A/tests/tools/**`는 대상이면 허용)·레지스트리·계획·design·library·`.ai/verification/**`·D-9 파일 변경 0.
   바뀐 파일마다 바뀐 줄은 import 문·모듈 식 자리·D-17 대입 대상·1 (c)(d)의 줄뿐(계약 3 (가)가 그 밖 차이를 잡는다).
8. **게이트(auditor, 판정 때 gate `master` 판 도구)**: V3 대상 def 0·변이 0(`defs` []·`moved` []·`move_rejected` {}; 범위 정책(35) 키 `not_targeted` 0·`targets_by_def` {}), V6 `findings` [], V7 `new_defs` [].
   V5는 test 변경의 **승인 대상**(design §9.2 '뒤에 올 승인: T1·F1의 V5 승인') -- 발견은 import 문자열 리터럴 변경·`tests/conftest.py`(무조건 승인)·1 (c)(d)의 판정 변경이고, 승인 기록 범위 설명에 그 목록을 test 커밋 diff 해시와 함께 적는다.
   V4는 interface card의 '피검 심볼'이 비면 `ERROR` -- FU 선례(`--subject` 운영 진입 함수)대로 준다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**equivalence**(design §8 F1 행). 계획 N3.12.3(686행) "동작을 보존하는 변경(…Phase 3 이동)은 `equivalence`". F1은 엔진 동작을 바꾸지 않고 호출부의 import 경로만 바꾼다(계약 3 (나): 모든 읽기의 정의 출처가 같다).
test 커밋이 있다(test-author가 `A/tests/**`의 대상 파일을 고친다) -- equivalence의 "test 커밋이 그대로이고 base와 병합본 모두 통과"(680·686행): F1 test 커밋은 MOD에서 직접 import하므로
shim이 있는 base에서도, 병합본에서도 통과해야 한다(계약 6 (a)). code 커밋은 `A/tests/tools/**`·`workspaces/run_harness.py`(code-author 경로)다.
red-green이 아닌 이유: 새 동작이 없고, "shim을 거치지 않는다"를 단언하는 새 test는 F2(shim 삭제)의 red가 맡는다(F2 card 계약 6) -- 같은 단언을 두 card가 영구 test로 두지 않는다.

## oracle 종류와 출처

(c) 동작 보존: PT3·PT3 --gmid-dod test id별 결과, E-INST·E-LIB 출력, 계약 3의 정적 동등(base = F1 base 트리 자체). 기대값 = base 실행·해석 결과(auditor가 격리 복제본에서 같은 명령으로).
(a) 구성: 계약 1의 대상 집합(design §10 E3·E3b 식 그대로), 계약 2의 목적지(G1 `binding_origin` -- 정의 하나), D-17 호출자 집합(base에서 덮어쓴 모듈 단위의 F1 base 위치).
test-author가 쓰는 import는 **interface card의 '이름 → 정의 모듈' 표**(오케스트레이터가 F1 base에서 계약 2 (i)로 생성해 넣는다 -- test-author는 엔진 소스를 읽지 않는다)에서 온다.
`_drafts/p3kit_f12/f12_f1sim.py`(기계적 재작성)·`f12_equiv.py`(동등 판정 시제품)는 작성 전 실측용이고 판정 도구가 아니다(작성자≠검증자).

## 거부해야 할 입력

auditor 판정기(계약 3) 자기 점검 -- 모의 F1 병합본 위의 변이 커밋(실측 5):
* 정의 모듈이 아닌 MOD를 거친 import(`workspaces/run_harness.py`의 `from gmid_lut import SemiEmpiricalGmIdLUT` → `from gmid_sizing_engine import SemiEmpiricalGmIdLUT` -- MOD4가 MOD1에서 import해 같은 객체로 풀린다) → (다) FAIL.
* import 밖 줄 변경(probe 문자열 리터럴 `"offset"` → `"offs"`) → (가) FAIL.
* D-17 대상에서 호출자 모듈 하나를 뺌(`probe_vds_assignment_paths.py` `resolve_feed_vds`의 `circuit_metrics`) → (라) FAIL.
* 계약 5 (a): 대상 하나를 빠뜨린 병합본 → E3 AST 식이 그 파일을 FAIL로 낸다(design §10 E3 실측과 같은 식).

## library 회로 적용 여부

적용 -- E-INST 파일럿·`folded_cascode`(하네스 `run()`이 F1이 바꾼 `workspaces/run_harness.py` import로 엔진을 부른다), E-LIB 9회로(`e_lib.py`는 D-9 사본이라 F1이 바꾸지 않는다 -- 대조 기준선).

## 무동작 판정 입력(무발동 값)

새 산출물 필드 없음. library 회로 전부·기존 test 전부의 판정·산출물이 base와 같다(계약 6). 발동 계수 ID 없음.

## 재현할 수치

(모의 -- 아래 '작성 전 실측' 머리의 사슬, 2026-10-02. **전부 관찰이고 기대값 근거가 아니다**: F1 base(M10·T1 뒤)에서 auditor가 다시 계산한다.)
* 대상: (a) 65파일 + (b)만 걸리는 6파일 = 71(+ (c)만 걸리는 3파일 = **74**). 쓰기 경로: test-author `A/tests/**` 55(그중 `tests/conftest.py` 1), code-author 3(`A/tests/tools/` 2 + `workspaces/run_harness.py`), 역할 밖 `workspaces/<하위>/` 16.
* 바꾸는 이름: (모듈, 이름) 136쌍. 모듈 객체 뿌리 52개 중 목적지 하나 18·둘 이상 34(34파일). from-import 문 39(25파일), import 호출 9(5파일), 동적 `getattr` 9, D-17 14줄(8파일).
* E3(AST) F1 전 65파일(D-9 밖) → F1 뒤 0, D-9 안 1(`probe_stage_partition.py`). E3b 식(F2 삭제 50이름) reader: F1 전 50줄·12파일 → F1 뒤 0. IMPORT-ANY `tried=13 expected=13 failed=0`(F1 전·뒤 같음).
* E-INST(`e_inst_p3.py` `7d26134a…`) 파일럿 `raw_sha256` `2fc426d9…`·`folded_cascode` `ef3cd996…` F1 전 = F1 뒤(22키 중 `engine_origin`만 다름: `sizing_recipe`·`design_report` 빠짐). E-LIB `hash` `1d2e3bf6…` 같음.
* V3 `targets` [`workspaces/run_harness.py`]·`mutants` 0·`defs` [], V6 PASS `findings` [], V7 PASS `new_defs` [], V5 FAIL(승인 없음) 발견 10 = 무조건 승인 1(`tests/conftest.py`) + 리터럴 변경 9(import 문자열).
* 계약 3 판정 시제품: 71파일 중 PASS 63, FAIL 8 = 모의 재작성의 동적·부재 단언 형태 5(계약 2 (ii) 기본안 미적용) + F1 base가 이미 깨진 selftest 3('결정 필요 항목' 5). 변이 세 개 각각 해당 식만 FAIL.

## 결정 필요 항목

1. **(오케스트레이터 지시 -- 확정 사실) 기준 blob 대조 test가 F1에서 깨진다, design §7.1 B군 누락.** `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`는
   `A/tests/tools/derive_achievable_bounds.py`(현재 HEAD 내용)를 `939f926` blob과 비교해 경로 줄 밖 차이 0을 단언한다. 그 도구 33행 `import sizing_recipe as sr`은 계약 1 (a) 대상(추적 파일, `A/tests/tools/**` -- D-9 밖)이라
   **F1이 반드시 바꾸고**(U-03/UD-1 (가) '추적 파일은 전부 F1에서 갱신' -- 추적 안 된 파일만 깨진 채 둔다; D-9 제외 집합에도 없다), 바꾸면 이 test가 FAIL한다(모의 F1 병합본 실측: 33 passed → 1 failed·32 passed;
   리뷰 `_drafts/review_p4_first.md` S1도 같은 결과 -- 33행만 바꾼 본에서 `non_path_line_changes` = `[('base', 33, 'import sizing_recipe as sr'), ('new', 33, 'import theta_search as sr')]`).
   design 30 §7.1 B군 표는 같은 파일의 528행(파일 존재 앵커)만 적었다.
   * **병합 순서별 처리(오케스트레이터 지시 -- 두 경우 모두)**:
     (1) **Phase 4 첫 card #2(`_drafts/draft_p4_first.spec.md` D1 -- r1 초안이 (다)를 택함)가 F1보다 먼저 병합되면** 그 test는 이미 HEAD 도구가 아니라 이동 커밋 `9d6800e` blob을 base `939f926` blob과 대조한다 -- F1이 도구 33행·`sr.` 속성 줄을
         바꿔도 판정이 달라지지 않으므로 **F1은 이 test를 고치지 않는다**(계약 1 (d) 대상에서 빠진다 -- auditor가 F1 base에서 그 test가 HEAD 도구를 읽지 않음을 확인해 적는다).
     (2) **F1이 먼저면** F1 test 커밋이 같은 test를 Q3 답대로 고친다. 기본안 = **(다) 이동 커밋 blob 대조**(#2 r1과 같은 규칙): 비교 대상을 HEAD 도구 내용 대신 이동 card(`ts6-probe-relocate`)의 이동 커밋 blob(`9d6800e` -- 새 자리 있음·부모 `a574f97`에 없음을
         test가 구조로 확인)으로 바꾼다. 계약 5의 원래 뜻('이동이 경로 줄만 바꿨다')은 이력 사실이라 불변 blob 둘로 판정하고 HEAD 내용을 영구 고정하지 않는다 -- F1·#2 어느 쪽도 이후 이 test를 다시 건드리지 않는다(허용 목록 유지 비용 0).
         그 뒤 #2는 이 test를 고치지 않는다(같은 규칙).
     대안: Q3 초안(`_drafts/p3_followup_questions.md` §4.3)의 (가) 기준선에 F1 import 치환 반영 / (나) 허용 줄에 import 줄 추가 / (다) test 은퇴 -- (가)·(나)는 card마다 허용 목록이 쌓이고(#2가 또 고친다), 은퇴는 판정 삭제라 약화가 가장 크다.
   * **승인 경로**: 어느 안이든 'HEAD 도구가 경로 줄 밖 그대로'라는 영구 고정을 푸는 **기존 계약 test의 판정 변경**이라 **V5 사용자 승인**(test 커밋 diff 해시)이다 -- design §9.2 '뒤에 올 승인: T1·F1의 V5 승인'의 범위 안이고,
     승인 기록 범위 설명에 "비교 대상 변경 1(test 이름)"을 이름으로 적는다(T0 '비교 완화 1' 선례). 경우 (1)이면 그 승인은 #2 card에서 받고 F1 V5 질문에서는 빠진다.
   * **Q3 질문 문안 제안(오케스트레이터가 `p3_followup_questions.md` §4.3에 반영 -- 이 card 작성 범위 밖 파일이라 직접 고치지 않았다)**:
     header `[F1] TS6`, question "[F1] shim 삭제 전에 tests/tools/derive_achievable_bounds.py의 `import sizing_recipe as sr`(와 sr. 속성 줄)를 바꿔야 하는데, TS6 이동 계약 test(test_ts6_probe_relocate)는 지금 도구 내용이 2026-09-23 이동 때와 경로 줄 밖에서 같기를 요구해 실패합니다. 어떻게 할까요?"
     선택지: 1. **"(다) 이동 커밋끼리 대조 (Recommended)"** -- "test가 지금 도구 대신 이동 커밋(9d6800e)의 도구를 원본(939f926)과 비교합니다. 이동 검증은 그대로 남고 이후 도구 변경(F1·Phase 4)은 이 test에 걸리지 않으며, Phase 4 첫 card와 같은 규칙입니다."
     2. "(가) 기준선에 import 치환 반영" -- "비교 기준을 '이동 때 원본 + F1의 import 치환'으로 바꿉니다. 치환 밖 줄은 지금처럼 그대로여야 하고, 도구를 고치는 card마다 기준을 다시 고칩니다."
     3. "(나) 허용 줄에 import 줄 추가" -- "경로 줄 정의에 shim 모듈 import 줄과 그 속성 참조 줄을 더합니다. 단순하지만 그 줄들의 다른 변경도 통과시키는 완화입니다."
     4. "(라) 이동 비교 test 은퇴" -- "이동 검증은 2026-09-23 판정 기록에 남아 있으므로 비교 test 하나를 지웁니다. 가장 간단하지만 이 test가 더는 아무것도 보지 않습니다."
     ((다)를 Recommended로 둔 근거: 원래 계약의 뜻 보존 + 반복 수정 없음 + #2와 정의 하나. (다)가 '영구 고정 해제'라 약화인지는 사용자 판단 -- 리뷰 `review_p4_first.md` B1과 같은 입장.)
   * **design 정정 항목(따로)**: design 30 §7.1 B군 표에 `test_ts6_probe_relocate.py:668-673`(`test_moved_tool_matches_base_except_path_lines`, F1)을 더한다. 사실 목록 갱신이라 design §9.1 마지막 문장('인용 줄·개수가 바뀌면 사실 문장 갱신')에
     해당하고, UD-0의 '다시 묻는 개정'(D0b가 계산할 **N3.10** 추가 개정, D-11)에는 해당하지 않는다 -- 사용자에게 따로 묻지 않는다. 사용자 몫은 위 V5 승인뿐이다.
2. **목적지를 이름으로 정할 수 없는 모듈 객체**(계약 2 (ii) 끝): `test_d_delete_dead.py`·`test_d_delete_telescopic.py`·`test_dup_w_calc.py`의 `_import_sizing_recipe()`(동적 `getattr(module, registry_name)`·여러 MOD 이름),
   `test_ts6_dead_probes.py:229`(`not hasattr(importlib.import_module("sizing_recipe"), _MISSING_SYMBOL)`), `test_dup_kcl_edges.py:35` `_sd()`(SD + MOD3 이름). 기본안(원칙 '정의 하나'·'판정 범위를 좁히지 않는다'):
   이름을 받는 도우미는 이름마다 R-DEF 정의 모듈을 돌려주고, **부재 단언은 '어느 N3.10 모듈에도 그 이름이 없다'**(한 MOD만 보면 범위가 좁아진다 -- 약화). 대안: 도우미가 MOD 이름 공간 합을 돌려준다(모의가 쓴 모양 --
   판정은 같지만 계약 3 (가)의 정규형 밖이라 auditor가 따로 본다). V5 승인 범위에 든다.
3. **정의 없는 이름의 import**(계약 2 (vi)): `diagnose_cmrr_cmfb.py:20` `from sizing_recipe import (…, _cmfb_amp_gain_diode_load)` -- 그 함수는 Phase 2에서 지웠고(design 20 §5.4-3 기본안 '삭제하고 스크립트는 그대로 둔다') 스크립트는 base에서 이미
   `ImportError`다(같은 성격: design §11-10 `stick.py`의 `block_from_row_widths` -- E3b `pre_existing`). E3에는 `pre_existing` 장치가 없어 고치지 않으면 E3 FAIL. 기본안: 정의가 있는 이름은 계약 2 (i)대로, 없는 이름은 **같은 문장의 정의 모듈 중 N3.10 번호가 가장 큰 것의 import**에 둔다
   (같은 문장에서 같은 `ImportError` -- 깨진 상태를 고치지도 숨기지도 않는다; 모의가 이렇게 했다). 대안: 사용자 workspaces 정리(백로그 -- §11-10과 함께).
4. **역할 밖 workspaces 스크립트 16개의 전달**(계약 4): 기본안 = F1 test 커밋 전 오케스트레이터의 역할 밖 커밋(같은 push에 역할 커밋과 섞지 않는다 -- design 05 §8.2-4 '다른 커밋이 끼면 거부'), F1 auditor가 같은 판정기로 잰다.
   대안: F1 뒤·F2 전 -- 그러면 계약 5 (a)가 F1 병합본에서 16파일 때문에 FAIL하므로 계약 5를 'F2 base' 판정으로 옮겨야 한다(판정이 늦어진다).
5. **(cross-card -- M card 초안에 넘김) F1 base에서 이미 깨져 있을 import**: SR·TL·DR이 완전 shim이 되는 M card(모의 TL = M4, SR = M8, DR = M9)에서 design §3 SHIM (b)는 '남은 일반 import 줄'을 지우게 한다. 그런데
   `unit/test_selftest_sizing_recipe.py:24`는 SR에서 `np`·`json`·`math`·`_dc_replace`와 TL 이름 `nmcnr_predict_ac_response`를, `unit/test_selftest_topology_library.py:24`는 TL에서 `math`를, `unit/test_selftest_design_report.py:24`는 DR에서 `os`를 import한다(V1 수집 test).
   모의 M9 트리에서 세 파일 모두 수집 `ImportError`(PT3 `3 errors during collection`, exit 2 -- 실측 4). SR의 `from stick_diagram import (Transistor, load_topology, …)`(base 5302행)는 SHIM (c)상 base 재수출이라 남아야 한다(모의 정정 판에서 남김).
   이 card의 처리: F1 base에서 그 이름들이 어떤 상태든 계약 2 (i)대로 **실제 출처**(표준 라이브러리·정의 MOD)에서 import한다. 같은 사실을 `_drafts/p3_followup_questions.md` §2(W-1, Q2 -- 권고 (가) T0에서 세 줄의 비엔진 이름을 출처 import로)가
   이미 다룬다 -- Q2 답이 (가)·(다)면 F1 base에서 그 7이름은 이미 출처 import이고 F1은 같은 줄의 엔진 이름만 바꾼다(T1 뒤 파일 이름은 `test_mod*.py`). 답이 (나)(SHIM (b) 완화)면 shim에 남은 import가 F2까지 살아 있으므로 F1이 출처로 바꾼다.
6. **(cross-card -- D0b에 넘김) 단위 키 문언과 시제품의 차이가 배정을 바꾼다**: D0a 계약 2 문언(문장 단위 키 = 바인딩 이름)대로 레지스트리 행과 짝지으면 상수 행 7개가 A-4가 되어 `upward` 1(`sizing_recipe.py::SemiEmpiricalGmIdLUT -> _QUERY_CACHE_MAX`)·`cycles` 1(MOD1 ↔ MOD4)이 나온다.
   G1 시제품 키(`<stmt:해시>`)로 짝지으면(D0b·G1 키트가 잰 판) 0·0·0·배정 403(A-4 229·A-5 64 -- D0b spec 실측 3과 같다). 이 card의 모의는 후자를 썼다. 같은 사실을 `_drafts/p3_followup_questions.md` §1(M1-2, Q1)이 다룬다 --
   Q1 답에 따라 `_QUERY_CACHE_MAX` 등 상수의 MOD가 바뀌면 F1 대상의 목적지 표(interface card)가 그 판으로 바뀔 뿐 계약은 그대로다(목적지는 F1 base에서 `binding_origin`으로 계산).

## 작성 전 실측

(재측정 = gate `master` `dd60db6`(`git -C <repo> rev-parse gate/master master HEAD` 셋 다 `dd60db6515b6…`), 2026-10-02. 격리 복제본 `C:/g202/r`(`git clone --no-local`, origin 제거, 빈 hooksPath, `core.autocrlf false`, TMP/TEMP `C:/g202/tmp`), 작업 끝에 `C:/g202` 삭제.
실제 저장소 쓰기 없음(`status --porcelain` 37줄·HEAD·reflog 시작과 같음). 스크립트 `_drafts/p3kit_f12/`.
**모의 사슬**(B34·b26pre·backfill·B26-1·B33·G1·FU·D0a·D0b·T0·M1~M10·T1 모두 미병합): `dd60db6` → `4e932be`(FU 대역 두 줄 + UD-0 문서 개정 v8.5 N3.10 8블록, `apply_ud0_v85.py` -- '현재' 정확 일치 단언) →
`ccb93aa`(G1 시제품 `g1_kit/install_proto.py` `5790433c…`·`g1_core.py` `b3c4e391…`) → **D-31 배정**: `plan_d31.py`(D0a 시제품 `move_plan_proto.py` `d2f3da97…` + D0a 계약 2 v8.4/v8.5 문언 규칙, `F12_STMTKEY=hash`) =
배정 403·A-4 229·A-5 64·A-1 60·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1·`upward`/`cycles`/`unassigned`/`conflicts` 0·`reg_mismatch` 79·MOD별 8·18·82·102·21·11·SD 110·32·17·ACF 2 = D0b spec 실측 3과 같음 →
`8810fc1`(M1~M9: `p3_scripts/p3v6_order_shim_sim.py`의 근사 배정을 그 배정으로 바꾼 사본 `sim_m_d31.py`, `bottom7` -- 옮긴 단위 M1 8·M2 18·M3 82·M4 102·M5 21·M6 11·M8 32·M9 17, 모든 card IMPORT-ANY 실패 0) →
`3f61526`(**M9 정정**: 모의 생성기가 완전 shim SR·DR에서 지운 `from stick_diagram import …` base 재수출 줄을 SHIM (c)대로 되살림) = **F1 모의 base**. M10(진입점 추출)·T1(test 재배치)·T0·D0b 재생성은 모의하지 않았다.
F1 모의 `2fd53cc`(`f12_f1sim.py` 기계적 재작성 + `test_restore_plan_functions.py` `_import` 4곳 보정), F2 모의 `3bcab98`(`mk_f2.py --acf`), F1 없는 F2 `0305d7e`.
`import_layering --root`: `3f61526`·`2fd53cc` exit 1(SD → `instance_report_builder` 임시 재수출 -- D-22 (4), F1 판정 아님), `3bcab98` exit 0.)
1. **사실 문장 재측정**: 대상 계산 `f12_callers.py 3f61526` → 엔진 split 모듈을 읽는 추적 `.py` 99개 중 바꿀 곳 74(D-9 안 3: `e_lib_inst.py`·`diff_dup.py`·`probe_stage_partition.py`) → **D-9 밖 71**
   (SR·TL·DR importer 65 + SD 삭제 이름만 읽는 6: `test_df36_instance_relpath.py`·`test_dup_kcl_edges.py`·`test_ic3.py`·`rerun_symmetry.py`·`stick.py`·`structural_symmetry_probe.py`), 디렉터리별 probes 32·workspaces/current-reuse 12·unit 10·contracts 8·
   workspaces/two-stage 4·tests 루트 2(`conftest.py`·`probe_physical_consistency.py`)·tests/tools 2(`derive_achievable_bounds.py`·`regression_runner.py`)·`run_harness.py` 1. design §10 E3 블록(문서에서 잘라 실행, `run_sec10.sh`)의 F1 전 E3 목록 65파일 = 위 65(차이 0).
   SD 재수출 이름 58 중 F2 삭제 50·SD가 읽어 남는 8(`Transistor`·`_scan_case_collisions`·`find_hub_merge_candidates`·`find_matching_candidates`·`find_stack_edges`·`find_stacked_matching_candidates`·`kcl_series_union`·`load_topology`).
   앵커(문자열 상수, import 호출 인자·docstring 제외 AST 스캔 `an5.py`): 계약 1 (c) 7줄·6파일 + T0 몫 A군(`test_ic5.py:49-55`·`test_dup_w_calc.py:442`·`test_ts6_dead_probes.py:60`) + 판정 밖(합성 입력 `test_reg_check.py`, 인벤토리 고정 `test_df23_inventory.py`,
   분석 원자료 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/build_c9_mapping.py`·`count_selftest_sections.py` -- 이름 문자열로 파일 목록을 든 기록 스크립트, import 아님).
2. **이름 충돌**: 새 파일 없음(기존 파일만 고친다). 새 별칭은 대상 파일 안 지역 이름이라 glob·전수 스캔과 무관 -- 단 T0 계약 9의 전수 스캔 토큰 목록을 test-author가 피한다(design §7.1 R-DEF 절).
3. **D-17(design §7.2 S11 재측정, 대입문 + `setattr`)**: 대입 14줄·8파일(probe 12 + workspaces 2), `setattr(` 0(`git grep -c "setattr(" dd60db6 -- '*.py'` 0건 -- B26-1 미병합). 이름마다 'base에서 덮어쓴 모듈(SR)의 단위 중 그 이름을 전역으로 읽던 단위의 모의 배정 MOD' =
   'F2 모의 트리의 모든 호출자 모듈'(`an6.py`, 14/14 같음): `probe_b22_headroom_attribution.py:104·116` `diode_vds_window` → MOD4; `probe_diode_gmid_readiness.py:63` `_hr_resolve_vertical_group` → MOD4·MOD8; `probe_diode_pass_skips.py:94`
   `apply_diode_self_consistent_gm_id` → MOD8(정의는 MOD4 -- 정의 모듈이 아니라 호출자); `probe_diode_window_corner.py:100·108` `diode_vds_window` → MOD4; `probe_matching_pair_divergence.py:124` `_optimize_theta_slsqp` → MOD8;
   `probe_vds_assignment_paths.py:47` `resolve_feed_vds` → MOD5·MOD4, `:53` `_feed_vds_fallback` → MOD4·MOD8, `:62` `allocate_stack_headroom` → MOD4, `:73` `_metric_stage_budget_vds_by_device` → MOD8(정의 MOD4), `:79` `_hr_resolve_vertical_group` → MOD4·MOD8;
   `diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20` `repair_matching_safety`(정의 SD) → MOD8.
4. **기존 계약 test(PT3 모의, `run_pt3.sh` -- design §10 PT3 명령, 게이트 사본 = `ccb93aa` `tools/gates`)**: F1 모의 base `3f61526` = `3 errors during collection`(exit 2 -- 결정 필요 항목 5), F1 모의 `2fd53cc` = 5 failed·1042 passed·15 xfailed
   (F1 몫 2: `test_d_move_tests::test_new_tool_modules_do_not_copy_engine_definitions`(69행 `_REQUIRED_ENGINE_IMPORT` -- 계약 1 (c)), `test_ts6_probe_relocate::test_moved_tool_matches_base_except_path_lines`(계약 1 (d)) /
   T0 몫 3: `test_dup_w_calc::test_size_transistor_calls_new_function`·`test_ic5::test_gate_docstring_declares_blind_spots`·`test_ts6_dead_probes::test_audit_vsb_consistency_has_operational_caller` -- 모의에 T0 없음),
   F2 모의 `3bcab98` = 14 failed(+9: 계약 1 (c) 앵커 7줄이 부르는 test 8 + T0 몫 `test_sizing_recipe_source_has_no_l_role_multipliers` 1). 단일 실행: `test_ts6_probe_relocate.py` 33 passed(`3f61526`) → 1 failed·32 passed(F1 모의).
   조정은 전부 V5 승인 경로(design §9.2 '뒤에 올 승인').
5. **계약 3 판정 가능성**(`f12_equiv.py 3f61526 <head> --d17 f1sim2.json`): `2fd53cc` 71파일 PASS 63·FAIL 8(재현할 수치). 변이 `58d23cd`(정의 아닌 MOD 경유 import) → `run_harness.py` (다)만 FAIL, `dc1d7a7`(리터럴) → 그 probe (가)만 FAIL,
   `4dc9d31`(D-17 호출자 하나 뺌) → 그 probe (라)만 FAIL. (다)의 예외(SD에 남는 이름)를 넣지 않으면 `test_ic3.py`·`test_selftest_stick_diagram.py`·`rerun_symmetry.py`·`stick.py`·`structural_symmetry_probe.py` 5파일이 거짓 FAIL(design §7.2가 남기기로 한 import).
6. **트리 판정(§10 블록 그대로 실행)**: F1 모의 `2fd53cc`(재작성기 첫 판 `4ee4df6`도 같은 결과): `E3 PASS`(첫 루프는 shim 세 파일 있음 -- 이 card 판정 밖), `E3b LIVE moved_out=58 base_files_reading_moved_out=31 pre_existing=1`·`E3b PASS`,
   `IMPORT-ANY tried=13 expected=13 failed=0`. F1 없는 F2 `0305d7e`: E3 FAIL 65파일, **E3b FAIL 50줄·12파일**(test_df36_instance_relpath 4·test_dup_kcl_edges 2·test_ic3 5·test_selftest_design_report 1·test_selftest_stick_diagram 27·rerun_symmetry 1·
   smoke_run_harness_session20 2·stick 1·structural_symmetry_probe 1·run_harness 2·check_box_shape 2·check_box_shape_M5M7split 2 -- design v8 근사 '49줄·12파일'과 파일 집합 같음, 줄 +1).
7. **V 도구(`run_vtools.sh` -- base 판 = G1 시제품 설치본, `3f61526 → 2fd53cc`, 첫 판 `4ee4df6`도 같음)**: V3 PASS `targets` [`workspaces/run_harness.py`]·`mutants` 0·`defs` [](모듈 수준 import만 바뀐다 -- V3는 def만 본다), V6 PASS `findings` [], V7 PASS `new_defs` []·`unreached` [],
   V5 FAIL 발견 10(`diff_paths` 6). 범위 정책(35) 시제품은 이 판에 없다 -- 바뀐 def 0이라 `not_targeted`·`targets_by_def`도 0·{}일 것(FU 실측 8과 같은 이유).
8. **V3 규모**: 바뀐 def 0(엔진 소스 중 바뀌는 것은 `run_harness.py` 모듈 수준 import 줄뿐 -- M10 뒤 하네스 import 모양은 F1 base에서 다시 잰다). 인벤토리 test 0.
9. **동작(E-INST·E-LIB, `C:/g202/tools/run_einst.sh` -- 같은 체크아웃 경로에서 차례로)**: `3f61526`·`2fd53cc`·`3bcab98` 세 판 모두 exit 0, 파일럿 `raw_sha256` `2fc426d9ef3a…`·`folded_cascode` `ef3cd9963d0a…`(FU card 재현 수치와 같다),
   22키 중 `engine_origin`만 다름(M9 모의 11모듈 → F1·F2 9모듈: `sizing_recipe`·`design_report` 빠짐). E-LIB `hash` `1d2e3bf6acf7…` 세 판 같음(Phase 2 DoD E-LIB 판과 같음). 한 판 시간 파일럿 289~330 s·`folded_cascode` 37~44 s(스크래치 실행).
10. **쓰기 경로**(계획 N3.12.2): `A/tests/**`(tools 제외) = gmid-test-author(55파일 -- `tests/conftest.py`는 `판정 환경` 행의 제외 glob이라 test-author가 쓰고 V5 무조건 승인), `A/tests/tools/**`·`workspaces/run_harness.py` = gmid-code-author(3),
    `workspaces/<하위>/*.py` 16 = 역할 행 없음(`role_paths.allowed` '맞는 행 없음' -- 결정 필요 항목 4). 판정 기록 = auditor. interface card '이름 → 정의 모듈' 표 = 오케스트레이터(F1 base에서 계약 2 (i)로 생성).
11. **계획서 소비자**: 지우거나 옮기는 이름 없음(import 경로만). 계획 534행 shim 문장·D-9 개정 문안은 design 커밋에 이미 있다(UD-0).
12. **미배선**: 새 def 없음. V7 `new_defs` [].
13. **승인 줄**: 동작 변경 없음 -- 결정 승인 불필요, design 승인 UD-0 `20260930-30-module-split-design`이 덮는다(D-9·D-17 기본값은 UD-0 '기준에 닿는 기본값' (a)(b)로 사용자 답 "승인 (Recommended)"이 있다).
    작업 중 gate `master`가 `4a286f0`으로 나아가 그 기록이 `36e170e`로 들어왔다 -- 범위 설명 105~111행이 "F1 `p3-callers-update`, F2 `p3-shim-delete`"를 slug로 적고 "id 날짜는 card 작성 때"라 한다(이 초안 id `20261002-p3-callers-update`와 맞는다).
    `dd60db6..4a286f0`의 엔진·`workspaces` 변경 0(`git diff --stat … -- skills/analog-gmid-design/assets workspaces` 빈 출력), `tools/gates`는 V3 면제 묶기 병합(`mutate_changed.py`)뿐 -- 이 card의 V3 관찰(def 0)은 영향 없다.
    test 판정 변경(결정 필요 항목 1·2·계약 2 (iv))은 V5 승인 -- test 커밋 뒤 diff 해시로.
14. **범위 계약**: 계약 7은 '이 card `Change-Id` 커밋들의 diff + 계약 4의 역할 밖 커밋 하나'로 한정.
15. **같음 판정**: 계약 3은 `ast.dump(include_attributes=False)` 문자열과 (이름, 정의 튜플) 정렬 목록·등장 순서 목록을 비교한다(`set`의 `==` 없음). 계약 6 (a)는 test id별 결과 문자열.
16. **red 모양**: red 없음(equivalence). 계약 3·5는 auditor 측정이다.
