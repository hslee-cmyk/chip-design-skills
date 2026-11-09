# 4차 독립 검토 -- Phase 3 `30-module-split` 초안 v6 (UD-0 승인 요청 전)

검토자: 독립 검토 agent(초안 작성자·이전 검토자 아님). 저장소 읽기 전용(HEAD = gate `master` `a796468`), 상태 변경 git 없음.
측정: `C:/g92/repo`(`git clone --no-hardlinks`, `a796468`)와 그 아래 모의 트리. 합성 커밋은 이 스크래치 복제본에서만 만들었다. 끝난 뒤 `C:/g92`를 지웠다. Python `C:/Python314/python.exe -B`.
대상: `draft_phase3_design_v6.md`, `draft_p3_{g1,t0,d0a}.spec.md`, `p3_doc_amendments.md`, `phase3_approval_question.md`, `phase3_revision_log.md`('v5 → v6' 절), `p3_scripts/`.
대조: `review3_phase3_v5.md`, `draft_b26_1.spec.md`, `draft_b34.final.spec.md`, `draft_b33.final.spec.md`, `draft_v3_{exempt_binding,scope_policy}.spec.md`, `backlog_additions.md`, 계획(`8356c1e` 반영본).

## 판정

**아직 승인 요청 준비가 안 됐다(not approval-ready).** 막는 것은 1건이고, 고치는 양은 작다.

* **N1**: DoD가 `stick_diagram` 임시 재수출 제거(F2) 뒤 조용히 깨지는 추적 파일을 잡지 못한다. 이것은 3차 검토 B3과 같은 결함 부류다(V1 밖 파일의 공허 PASS).

3차 검토의 B1~B4는 **모두 실제로 고쳐졌다.** 모의와 DoD 블록을 직접 다시 돌려 확인했다(§1).
새 규칙 D-22~D-25는 방향이 맞고 판정을 약화하지 않는다. 다만 DoD 명령 두 곳이 **도구 오류 때 통과로 떨어진다**(S1·S2, 둘 다 실증). N1과 같은 개정에서 함께 고치기를 권한다.
문서 개정 7건은 현재 원문과 일치한다. 보호 판정 표(`plan_tables_hash`)도 두 안 모두 바뀌지 않는다.

---

## 1. 3차 검토 B1~B4 재확인 (직접 재실행, `a796468`)

| # | 확인 방법 | 결과 |
|---|---|---|
| B1 `order` | `p3v6_order_shim_sim.py <repo> … bottom7 pull`, `… top pull`을 `C:/g92`에서 실행 | 두 변형 모두 `order_old_fail` = [M8, M9], `order_new_fail` = []. 개정 기록 수치와 같다 |
| B2 `shim` | 같은 실행 | `shim_old_fail` = M1~M9 전부, `shim_new_fail` = []. D0a 계약 4 (a)~(d) 문언이 design §3 SHIM과 일치한다 |
| D-22 근거 | 같은 실행의 `import_fail` | `top`(import 줄 모두 머리): M9에서 `instance_report_builder`·`design_report`가 `ImportError: cannot import name '_audit_result_json'`. `bottom7`: M1~M9 모두 {}(실패 0). 개정 기록의 주장이 재현된다 |
| B3 E3 | design §10 블록의 E3 부분을 `sed`로 **문서에서 그대로 잘라** 실행 | (i) `B0 = a796468`: `E3 INVALID` 없음(문장 69줄·63파일, 호출 9줄·5파일 -- 개정 기록과 같음). (ii) **고장 입력**: 존재하지 않는 `B0`(`deadbeef`)를 주면 `E3 INVALID: base에서 빈 결과(명령 고장)`가 출력된다. **거부 확인 자체가 동작한다.** (iii) 합성 커밋 C1: 적중 파일 중 `probe_L_search_window.py`(`import numpy as np, sizing_recipe as sr` 모양, 정규식이 놓치던 것) 하나와 제외 파일만 남기고 SR·TL·DR와 나머지 적중 파일을 지웠다 → `E3 FAIL: …probe_L_search_window.py`. (iv) C2: 그 파일도 지움 → `E3 PASS`. 거부와 수용이 모두 성립한다. (v) 단, 도구 오류 경로는 열려 있다(S1) |
| B4 문서 개정 | `p3v6_amend_check.py`를 `a796468` 복제본에서 재실행. 출력 JSON을 `p3v6_amend_check.a796468.json`과 키 정렬 비교 | **동일**. '현재' 블록 10개가 모두 일치한다(계획 522·523·526·528·534·687, `00-common` 103·431, `10` 250·252). 두 안 모두 `mod_table` 10행, N3.10 4열·10행, 두 행에 걸린 백틱 0, `import_layering` exit 0. 추가로 **`merge_gate.plan_tables_hash`를 개정 전·후 계획서(두 안)에서 계산했다: 셋 다 `7167e028…`로 같다.** N3.10·N3.12.3은 보호 표 밖이다. `plan_tables` 승인은 필요 없다는 문장이 맞다 |

S1~S8, m1~m6 대응도 문서에서 확인했다. 남은 것은 아래 minor m1(옛 base 문장)뿐이다.

---

## 2. Blocking

### N1. F2가 `stick_diagram` 재수출을 지운 뒤 깨지는 추적 파일을 DoD·F1·F2가 보지 않는다

* design §2.2와 §8 F2행에 따르면 F2는 **SD 자신이 읽지 않는 이름**의 임시 재수출을 지운다(WP-14).
  GONE-SHIM·E3은 `sizing_recipe`·`topology_library`·`design_report` 세 모듈의 import만 본다. E5 `import_any`는 N3.10 파일과 split 파일만 import하고 호출부는 import하지 않는다.
  F1 oracle은 "호출부 AST가 import 줄 외 동일"이라서 **빠뜨린 호출부**를 잡지 못한다. F2 oracle은 GONE-SHIM + LAYER뿐이다.
* 실측(`a796468`, AST). V1이 수집하지 않는 추적 파일 중, N3.10·레지스트리상 SD 밖으로 가는 이름을 `from stick_diagram import …`로 읽는 곳이 여럿이다.
  * `load_topology`(→ MOD3): `workspaces/current-reuse-telescopic-ota-report/spice/*.py` 11개, `rerun_symmetry.py`, `probe_l3_groups.py`, `structural_symmetry_probe.py`, `topology_to_markdown.py`(A 루트).
  * `find_structural_symmetry_candidates`·`find_matching_candidates`(→ `circuit_state_graph`), `check_symmetry_dispositions`(→ `topology_authoring`): `structural_symmetry_probe.py:10`, `rerun_symmetry.py:5`.
  * `save_instance_json`·`run_full_circuit_audit_from_topology`(→ MOD9): `smoke_run_harness_session20.py:28`, `two-stage-ota-report/check_box_shape*.py`.
* 결과: F1이 이 중 하나를 빠뜨려도 Phase 3 DoD는 전부 PASS한다. probe·workspaces 스크립트는 조용히 깨진 채 남는다.
  design이 D-24에서 든 이유("probe는 V1이 수집하지 않아 shim 삭제 뒤 조용히 깨진다")가 SD 이름에도 그대로 적용된다. 계획 534행의 '추적 파일 갱신 후 삭제' 조건도 이 경로에서는 판정되지 않는다.
  `p3_doc_amendments.md` §2가 `.ai/verification/**` 스크립트가 "`stick_diagram` 경유 이름으로 깨질 수 있다"고 이미 적는다. 그런데 제외 집합 **밖**의 같은 경우를 재는 명령이 없다.
* 고칠 것(작다):
  1. §10에 **E3b**를 더한다. 마지막 병합본의 추적 `.py`(D-9 제외 집합 밖)에서 AST로 다음 이름 N을 모은다.
     * `from stick_diagram import N`
     * `import stick_diagram as a` 뒤의 `a.N` 속성
     * `importlib.import_module("stick_diagram").N`과 그 반환값 이름의 속성(예 `tests/contracts/test_dup_kcl_edges.py:35`의 `_sd()._kcl_and_matching_edges`)

     N마다 head `stick_diagram.py` 최상위에 바인딩이 있어야 한다. 바인딩이 없는 N = FAIL이다. 파싱 오류와 도구 오류는 FAIL로 센다(S1과 같은 방식).
  2. 거부 확인: `B0`에서는 전부 해석되므로 '비지 않음'을 쓸 수 없다. 대신 "B0에서 D0b 이관표가 SD 밖으로 배정한 이름을 SD에서 읽는 추적 파일 수 > 0"을 확인한다. 이 명령이 살아 있다는 증거다. 지금 위 목록이 그 예다.
  3. F2 oracle에 E3b를 넣고, F1 범위 문장에 '이름 단위(SD 잔류 여부)로 고른다'를 적는다. 지금 §7.2의 "모듈 집합에 `stick_diagram` 포함"은 모듈 단위라서 SD에 남는 이름의 import까지 대상으로 잡는다.
* 왜 승인 전인가: DoD는 승인 대상 design의 일부다. 승인 뒤에 판정 명령을 더하면 기준 변경이 되어 다시 승인을 받아야 한다.

---

## 3. Should-fix

| # | 위치 | 발견(근거) | 고칠 것 |
|---|---|---|---|
| S1 | §10 E3 `E3_AST`·`e3_files` | **도구 오류가 PASS로 떨어진다(fail-open).** 거부 확인은 `B0` 쪽만 본다. HEAD 쪽 실행에서 `git grep` 실패(`sys.exit`)나 `git show` 실패(`check=True` → 예외)가 나면 stdout이 비거나 일부만 남는다. 그러면 `OUT`이 비어 `E3 PASS`가 출력된다. **실증**(합성 커밋 C3, 스크래치 복제본): 남은 importer가 비ASCII 경로 파일 하나(`workspaces/k/probe_전압.py`, `import sizing_recipe`)일 때 `git grep -l`이 경로를 `"…\354\240\204…"`로 인용한다(`core.quotepath` 기본값). `git show`가 exit 128로 실패하고 traceback이 나는데, 판정 줄은 **`E3 PASS`**다. 지금 저장소의 추적 `.py`에 비ASCII 경로는 0개다. 하지만 `assets/`에 한글 이름 파일이 이미 있고(추적 안 된 zip), "PARSE-ERROR는 fail-closed"라는 문서 주장과 어긋난다 | `git -c core.quotepath=off grep -z -l …`로 바꾼다(또는 경로를 `-z`로 받는다). `git show` 실패는 `ERROR <경로>` 줄로 내고 계속한다. 셸에서 파이썬 종료 코드를 받아 0이 아니면 `E3 FAIL(도구 오류)`를 낸다(`set -o pipefail` 또는 `rc` 캡처). E3b(N1)도 같은 틀로 둔다 |
| S2 | §10 `import_any` | **모듈 목록 계산이 실패하면 조용히 일부만 본다.** `local mods=$(…mod_table…)`는 실패를 숨긴다. `[ -f … ] || continue`는 없는 파일을 건너뛴다. **실증**: `p3v6` 모의 M9 트리(`top` 변형, 실제로 순환 실패가 있는 트리)에 대해, 올바른 `GC`에서는 `IMPORT-ANY FAIL: instance_report_builder`·`design_report`가 나온다. `GC`가 잘못되면(`ModuleNotFoundError: import_layering`) **`design_report`만** 나오고 MOD9 실패는 사라진다. split 모듈에 실패가 없었다면 출력 0 = PASS다. E3에서 고친 '살아 있음 확인'이 여기에는 없다 | `mods`가 비거나 그 명령이 실패하면 `IMPORT-ANY INVALID`를 낸다. 실제로 import를 시도한 모듈 수를 출력하고, 통과 기준에 "시도 수 = 그 트리에 있는 N3.10·split 파일 수(`layer.json` `present` + split)"를 넣는다 |
| S3 | §2.3·§8 M10·D-25 | **M10 V3는 비용 문제만이 아니라 생존 변이 문제가 있다.** `mutate_changed.mutants`는 문장마다 `stmt_delete`를 만든다(실측 146~187행). 지금 `run()`(`run_harness.py:422`~)에는 `print` 문장이 20개 이상 있다. 또 한 회로 E-INST로는 지나가지 않는 분기도 있다: `pr is None`, `except ValueError` 진단(`diagnose_sizing_roles_gap`), `audit_ok`·`floorplan_ok`가 False일 때 note를 붙이는 분기. E-INST 해시 대조 test 하나는 이 변이를 죽이지 못한다. 그래서 §2.3 추정("E-INST test가 죽일 때 30~40분")은 낙관적이다. 생존이 남으면 V3 FAIL이고, 면제에는 사용자 승인이 필요하다. D-25가 고르는 회로 하나는 이 분기들을 덮지 못할 수 있다 | M10 '작성 전 실측'에 넣을 것: (i) 진입점으로 옮길 문장 범위. 특히 `print`가 `run()`에 남는지 진입점으로 가는지. (ii) 회로별로 지나가는 분기. (iii) 생존 추정과 그것을 죽일 test 모양(stdout·반환값 대조 등). 또 D-25가 **새 test의 회로만** 정하고, M10 equivalence의 E-INST 회로 집합(`20-dead-code-dup` §3 정의)은 그대로라는 점을 한 줄로 적는다. 지금 문구 "어느 회로든 E-INST 해시 대조"는 둘로 읽힌다 |
| S4 | §6.4·§9.1 | **D0b와 F2 사이에 다른 엔진 card가 끼어드는 경우의 규칙이 없다.** 계획(`8356c1e`) 769행과 929행은 B26-1뿐 아니라 **B26-2~B26-4도 "Phase 3 착수 전에 해도 된다"**고 적는다. B34·B26-1은 사이트 5~8·10·14를 **B35**(백로그)로 넘겼고, 그 함수(`refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill`·`suggest_vertical_stack_composites`)는 MOD2·MOD3로 가는 SD 단위다. design v6에는 B26-2~4와 B35가 한 번도 나오지 않는다. D0b 뒤에 병합되면 이관표(레지스트리 열)와 §6.4 수치가 낡는다. M card 사이에 병합되면 A2 '재검토'와 같은 편집 범위 문제가 생긴다 | §9.1에 한 문장을 더한다: "D0b 병합부터 F2까지 엔진 파일(`A/*.py`, `run_harness.py`)을 바꾸는 Phase 3 밖 card는 병합하지 않는다. 필요하면 D0b를 다시 계산하고, N3.10 밖 개정이 나오면 D-11대로 따로 승인받는다." B26-2~4가 M1 전에 병합되면 §9.1 재측정 (1)에 포함된다는 것도 적는다. §6.4에는 'B35 인계 사이트는 Phase 3 뒤 새 모듈(MOD2·MOD3)에서 바뀐다'는 인계 한 줄을 둔다 |
| S5 | §2.2 D-22 (2) | D-22의 전제는 "MOD8·MOD9의 import 시점 읽기는 번호 7 미만 MOD에서만 온다"이다. 이것은 근사 배정에서 잰 사실이고 규칙으로 보장되지 않는다. 실측(`a796468`)으로 SR·DR·TL·`audit_current_forced`의 데코레이터, 기본값, 클래스 기반·본문, 모듈 문장, `__future__`가 없는 DR의 주석에서 SD 이름을 import 시점에 읽는 곳은 **0**이다. 그래서 지금은 성립한다. 그런데 D0b의 실제 배정이나 B26-1의 `rails: RailDeclaration` 같은 주석이 이것을 깨면 갈 곳이 없다. 머리 배치는 순환을 만들고, 끝 배치는 `NameError`를 내고, 지연 import는 금지다(F3). F3의 처리("순서·import 줄 위치를 고친다")로는 풀 수 없다 | D0b 계약 test에 단언을 하나 더한다: "MOD8·MOD9 배정 단위와 모듈 문장의 import 시점 이름 중 출처가 MOD ≥ 7인 것 0". 위반하면 D0b가 멈추고 배정을 바꾼다(N3.10 밖이면 D-11 승인). F3 처리 칸에도 이 경로를 적는다 |

---

## 4. Minor

| # | 위치 | 내용 |
|---|---|---|
| m1 | 승인 질문 머리 "기준 gate `master` `7535799`", G1 29행 "지금 gate `master` = `7535799`", T0 3곳, D0a 2곳 | `a796468` 기준으로 다시 확인했다는 사실 문장으로 고친다. design 머리는 이미 고쳐져 있다 |
| m2 | §9.3 D-9 "판정 기록 스크립트 6개", §9.2 UD-0 | `a796468`에서 E3(SR·TL·DR) AST로 잡히는 `.ai/verification/**` 파일은 **0**이다(제외 집합 안 적중은 `probe_stage_partition.py` 1개뿐). `.ai` 스크립트는 `import stick_diagram as sd` 8개로 SD 이름을 통해서만 깨진다. `p3_doc_amendments.md` §2는 이것을 맞게 적는다. D-9와 §9.2 수치를 그 문장에 맞춘다(N1의 E3b 제외 집합 = D-9) |
| m3 | §7.1 B군 | P9가 더한 `tests/contracts/test_dup_kcl_edges.py`(`importlib.import_module("stick_diagram")` + `_kcl_and_matching_edges`·`kcl_series_union` 속성 호출)가 표에 없다. `_kcl_and_matching_edges`는 N3.10 MOD3이다. V1 수집 test라 F2에서 소리 나게 FAIL하겠지만, F1 목록에 미리 넣는다(§9.1 재측정 M24에 포함된다는 문장만으로는 v6가 `a796468`에서 다시 확인했다는 주장과 맞지 않는다) |
| m4 | §10 E3 첫 줄 | 파일 부재 확인이 `sizing_recipe.py` 하나뿐이다. TL·DR 부재는 E4 `absent_split`이 본다. E3 행에 그 사실을 적거나 세 파일을 함께 확인한다 |
| m5 | D-24 | AST 호출 판정의 한계: `from importlib import import_module as im; im("sizing_recipe")`, `subprocess … "-c", "import sizing_recipe"`, 변수 인자는 잡지 못한다. 지금 저장소에는 0건이다(`git grep` 실측). 한계 문장으로 남긴다 |
| m6 | 승인 질문 UD-0 | N1을 고치면 "SD 재수출을 지운 뒤 추적 호출부 확인"이 DoD에 들어간다는 것을 ② 문장에 반 줄 더한다. 기준을 더하는 쪽이라 선택지는 바뀌지 않는다 |

---

## 5. 새 규칙 D-22~D-25 점검(점검 (2))

| 규칙 | 건전성·판정 가능성 | 약화 여부 | 반례 시도 |
|---|---|---|---|
| D-22(import 줄 위치 + IMPORT-ANY) | 위치 규칙은 지침이고, 판정은 IMPORT-ANY(모듈마다 새 프로세스에서 첫 import)가 한다. 결정 가능하다. `shim` (a)가 위치를 보지 않는다는 문장도 일관된다(SD 끝 줄도 '재수출 줄'). ORDER는 `--card` 파일만 보므로 SD → MOD9 위쪽 줄을 잡지 않는다. 그 줄이 순수 재수출인지는 PLAN-LAYER가 보장한다(SD 단위 → MOD9 참조가 있으면 배정이 거부된다). F2 뒤 LAYER로 닫힌다 | 강화(판정 추가). LAYER를 F2 뒤로 미루는 것은 계획 N6.2(Phase 끝 DoD)와 같은 시점이다. per-merge로 `import_layering`을 돌리는 test·게이트는 없다(`git grep` 실측) | ① SD를 먼저 import → SD 끝에서 MOD9 → MOD9 끝에서 SD(부분 초기화지만 정의는 다 묶임): 성립. ② MOD9를 먼저 import: 성립(모의 `bottom7` 실측). ③ MOD8·MOD9에 import 시점 SD 이름 읽기가 생기는 배정: 위치 규칙으로 풀 수 없다 → **S5**. 그리고 판정 명령의 fail-open → **S2** |
| D-23(phase 3 card는 Phase 2 DoD 뒤 병합) | 계획 991행을 문언대로 읽었다. `merge_gate.rule10_phase`는 순서를 강제하지 않는다(실측 532행~: phase_order 소속·N/A 도입만 본다). 그래서 오케스트레이터가 지키는 규칙이고 계획의 다른 Phase와 같은 수준이다 | 약화 없음(더 보수적) | -- |
| D-24(E3를 AST로) | 정규식이 놓친 6파일 모양을 잡는다(합성 C1 실증). docstring 거짓 FAIL도 없앤다 | 강화 | ① 별칭 `import_module as im` → 놓침(m5). ② 비ASCII 경로 → 도구 예외 → PASS(**S1**, 실증). ③ SD 이름 경유 깨짐은 범위 밖 → **N1** |
| D-25(M10 test 회로 = 가장 싼 library 회로) | '작성 전 실측'으로 정한다. 판정 가능하다 | 기준 불변. 단, 한 회로가 덮지 못하는 분기의 생존은 V3 FAIL로 드러나므로 약화는 아니다 | print 삭제 변이·`except ValueError` 진단 분기 → 생존 → 비용·가능성 추정을 고쳐야 한다(**S3**) |

---

## 6. 문서 개정 7건(점검 (3))

* 원문 일치: 10블록 모두 `a796468`의 해당 줄과 바이트 일치(§1 B4 재실행).
* 보호 표: 개정 전·후 계획서의 `plan_tables_hash`가 같다(두 안 모두 `7167e028…`). N3.10(515~536행)과 N3.12.3(687행)은 N4.1·N4.2·N6.1·N3.12.2 밖이다(`merge_gate.py:107-176`).
* 계획 A2 정정 `8356c1e`는 개정 대상 줄을 건드리지 않았다(위 일치로 확인).
* §1 (a) 가안은 B26-1 병합 전에는 존재하지 않는 이름(`rail_declaration`)을 A-1 토큰으로 둔다. D0b가 B26-1 뒤에 처음 계산하므로(§6.4) 문제는 없다. 참고만 한다.

---

## 7. 승인 질문(점검 (4))

* UD-0: D-9·D-17(기준에 닿는 기본값)이 드러나 있다. 추가 표 개정을 **위임하지 않음**이 기본이고, '승인 + 위임'은 중립 선택지로 따로 있다. 질문 4개·선택지 각 4개 이하로 AskUserQuestion 형식에 맞는다.
* D-19: 두 안과 그 한계(`validate_theta_declaration_order`가 MOD3로 가서 선언 검사는 어느 쪽이든 나뉨)를 중립으로 적었다.
* UD-5: (가)·(나) 비교가 v4 수치(51 = 26 + 25)와 맞다. UD-1: 대안 (나)·(다)가 있다.
* 숨은 회로 해석 결정: 없다. N3.10 MOD3 '책임' 열에 더하는 "topology 로딩(구조 자동채움을 부르므로)"은 호출 계층 사실이다. D-25는 test 비용 선택이다. 모두 코드 배치·판정 절차다.
* 고칠 것은 m1(머리 base)과 m6(N1 반영 시 반 줄)뿐이다.

---

## 8. 확정 card와의 일관성(점검 (5))

| 항목 | 결과 |
|---|---|
| V3 면제 묶기·범위 정책 출력 키 | `survivor_bindings`·`exempt_ignored`·`not_targeted`·`targets_by_def`(`def_header_changed` 포함)의 이름·의미가 design §8 M행·§10 E2와 일치한다(범위 정책 77~83행). "옮긴 def는 두 card 모두에서 대상이 아니다"(76행)와 M card `targets_by_def = {}` 요구가 맞다 |
| B33 final | phase 0.5·`gate_change: yes`·redteam 33. G1 base = 33·34·35 병합 뒤. 일치 |
| B34 final | phase 2, A2 승인. 사이트 5~8·10·14를 B35로 넘김(35행). design은 B35를 다루지 않는다 → S4 |
| B26-1(최종) | 새 인자를 받는 함수 SD 18·SR 2(419행) = design §6.4. 사이트 10·14는 B35로 감(43·51행). design의 '바뀌는 def' 행과 모순은 없다 |
| A2 계획 정정 `8356c1e` | B26-1·B34의 Phase 3 전 착수는 반영됐다. 같은 정정의 'B26-2~B26-4도 Phase 3 전 가능'은 반영되지 않았다 → S4 |

---

## 9. 정리

* **고치면 승인 질문을 올릴 수 있다**: N1(E3b와 F1·F2 문장). 권고로 같은 개정에서 S1·S2(DoD 두 곳의 fail-closed)를 함께 고친다. 셋 다 §10 bash 블록과 표 몇 줄 수준이다.
* S3~S5는 승인 뒤 card '작성 전 실측'·D0b 계약에서 고쳐도 판정 기준을 바꾸지 않는다. 그래도 S4(엔진 card 동결 문장)는 승인 범위에 넣는 편이 낫다. 오케스트레이터의 병합 순서를 정하는 규칙이기 때문이다.
* 재현 자료: 모의 `p3v6_order_shim_sim.py`(`top pull`·`bottom7 pull`), 문서에서 잘라낸 E3·`import_any` 블록, 합성 커밋 C1~C3(스크래치 복제본 전용). 모두 `C:/g92`에서 실행했고 끝난 뒤 지웠다.
