# 독립 재검증(r2 diff 중심): `draft_p3_t1.spec.md` r2 + `m10_t1_open_items.md` T1 항목 + `p3kit_m10_t1/t1_map.py`·`gen_t1.py` r2

검증 2026-10-07. 검증자는 작성자도 아니고 1차 검토(`review_p3_t1.md`) 작성자도 아니다. 대상은 r2 diff(`*.pre-r2.bak` 대비)다.
기준은 gate `master` **`2db7622`**다(card가 적은 `6c724de`와 비교해 `skills`·`tools` 변경은 `tests/contracts/test_b26pre_existing_paths.py` 추가 1파일뿐이다. 이 파일에는 `test_selftest` 문자열이 없고 4개 옛 파일·ts3·probe 2파일과도 무관하다).
스크래치는 `C:/g386`만 썼다. TMP/TEMP는 그 아래에 두었고, `cd`는 쓰지 않았다. 복제는 `clone -c core.autocrlf=false --no-hardlinks --no-local`으로 했고 origin을 지웠으며 hooksPath는 빈 디렉터리다. 실제 저장소는 `git show`/`archive`/`ls-tree`로 읽기만 했다. 끝에 스크래치를 지웠다.
절차 자진 신고: 스크래치 안 임시 파일 하나를 heredoc(`cat >`, 덮어쓰기)로 만들었다가 바로 지웠다(append 아님, 산출물 아님).

## 판정: B 0 · S 0 · minor 4

1차 검토의 S-1·S-2·S-3은 모두 반영됐다. 독립 사슬(gate `2db7622`, 커밋 id 전부 다름)에서 card 수치와 해시를 그대로 재현했다.
새로 넣은 계약(생성기 엔진 import 0, R-11)과 R-12도 재현했다. 남은 것은 문언 정밀화 수준이다.

## 1. 사슬

`2db7622` → FU 대역 `e5c3e12` → T0 W-1 대역 `4b1beb7` → G1 시제품 `4cd7885`(`installed 4`, `install_proto.py` md5 `733d173f…`) → D0a `5dcdfe3` → D0b(`one 354·multi 0·nested 7·nounit 18`) = M1 base `b978e73`(plan exit 0)
→ `chain_lean.py` M1~M9 `6b470f2`…`58d40b8`. 8 card 모두 plan 일곱 목록 0, `check` 발견 0, 단위 8·18·82·104·21·11·30·16으로 card와 같다.
사슬 구성 도구(FU·T0W1·G1·D0a/b·`chain_lean`)는 키트 것을 썼다. **매핑은 내 구현(`my_map.py`)**으로 card 문언에서 직접 만들었다. 키트 `t1_map.py`는 내 결과를 낸 뒤에 돌렸다.

## 2. S-1 확인 -- 메서드 조항은 대체 전용

내 구현 규칙: R-DEF(직속 module body의 def·class·대입, 유일 파일)와 tools 경유 조항으로 본 규칙을 만든다. 본 규칙에 걸리는 것이 없을 때만 대체 1(메서드, 수신자 무시, 최상위 정의 없음 + 정의 파일 하나), 그다음 대체 2(TL → 4), 그 밖은 STOP이다.

| | MOD1 | MOD3 | MOD4 | MOD5 | MOD6 | MOD7 | MOD8 | MOD9 | 계 |
|---|---|---|---|---|---|---|---|---|---|
| 내 구현(아래 m-1 해석 B) | 2 | **58** | 20 | 15 | 1 | **76** | 32 | 8 | 212 |
| card '재현할 수치' r2 | 2 | 58 | 20 | 15 | 1 | 76 | 32 | 8 | 212 |

* 옛 파일별 값은 sizing 1:2·3:9·4:10·5:15·6:1·8:30, stick 3:49·7:76·8:2·9:4, DR 9:4, TL 4:10이다. card와 같다.
* 적용 조항은 본 규칙 210, 대체 1 = `test_s056_noise_1f_density` → MOD1(`noise_1f_density`), 대체 2 = `topology_library::test_s011_tan` → MOD4, STOP 0이다. card와 같다.
* `test_s155_propose_device_roles_gap_fill` → **MOD3**이다. 근거는 `load_topology`·`propose_device_roles_gap_fill`이다. r1 문언(메서드를 본 규칙에 넣음)을 따로 구현하면 이 test 하나만 MOD7로 바뀐다(MOD3 57·MOD7 77). 차이가 s155 하나뿐임을 독립 확인했다.
* **작성자 r2 `out/r2/t1_map.json`과 test별 대조**: 212개 전부 k가 같고(차이 0) 적용 조항도 같다(차이 0). 키트 `t1_map.py`를 내 사슬(`58d40b8`)에서 돌린 결과도 내 값과 차이 0이다.
* 강건성 변형은 모두 V0 대비 차이 0이다: conftest fixture를 닫힘에 넣은 판, 최상위 `if/try/with` 안의 바인딩까지 R-DEF로 센 판, 자유 이름만 센 판(SCOPE)이 그렇다(아래 m-1의 s004만 예외).
* 그 밖에 card와 같은 값: 공유 fixture 2(`s086_state` 7·9, `s120_state` 3·9), 목적 파일 안 fixture 충돌 1(`s065_state`, MOD3, 토큰 바꾼 사용처 `test_s067_MB` k=3), test 충돌 0, 쓰지 않는 fixture·도우미 0, def 57.
* 변형 트리에서 `test_mod3`·`test_mod7` 두 파일은 `--gmid-phase=3`로 `134 passed`다.

## 3. S-2 확인 -- V5 운반 범위와 '2회 시도' 근거

* 내 사슬 head `e9b47d9`(작성자 `gen_t1.py` + **내 매핑**, diff 14파일 +3322 −3177)에서 gate `weakening_diff.py`를 돌렸다. 결과는 FAIL, 발견 215, `diff_paths` 7, **`diff_hash` = `aad798728d13d4bab9bd9479a3dd0af79ea67137d8a491ae08020e6b5fa30131`**로 변하지 않았다. 경로별 (base, head) blob 7쌍도 card '작성 전 실측' 7과 글자 그대로 같다(옛 4파일 head `-`).
  gate가 `6c724de`에서 `2db7622`로 옮겨도 해시가 같다. 7경로 blob만의 함수라는 계약 10 서술의 증거가 하나 더 생긴 셈이다.
* 지워진 경로의 `git cat-file blob <T>:<옛 파일>`은 exit 128이다. 그래서 `.blob`을 3경로로 한정한 것이 맞다. `paths.tsv`의 `-`는 00-common §8.2 '없으면 `-`' 표기와 같다. `paths.tsv`를 기계로 읽는 게이트 코드는 없다(test-author `cp` 입력뿐).
* **인용 확인(gate `2db7622`)**:
  * 00-common §8.2: `target_kind: diff`이면 `diff_base`·`diff_head`(40자리)·`diff_path`가 필수다. 해시 식에 "없으면 `-`"가 있다. staged_diff 항에 "`diff_head`는 금지다(아직 없는 그 커밋의 id를 적을 수 없다)"가 있다. 모두 맞다.
  * 00-common §16: "blob 해시는 커밋된 내용을 덮으므로 승인 기록은 **이 문서와 개정이 커밋된 뒤**에 그 커밋을 `diff_head`로 만든다"는 원문과 일치한다. 다만 이 문장은 00-common 자신의 승인 절차 문장이다(m-3).
  * 05 §8.2-5: staged_diff는 topology 승인 기록과 `Role: user` 커밋에만 쓴다. 맞다.
  * 05 §12 'V5 승인 운반': (2) "발견 경로마다 `cat-file blob <T>:<path>`"에는 삭제 경로 서술이 없고, 승인은 `diff_head = T`다. 맞다(X-7 정당).
  * "gate `merge_gate.py`는 형식만 본다": `merge_gate.py` 265~266행은 diff_head 40자리 형식만 검사한다. `weakening_diff.py`는 `approved_hashes`에서 head 트리 승인 기록의 `target`만 대조한다(diff_head를 읽지 않는다). 맞다.
* 근거 (3)(사용자는 test-author가 실제로 만든 diff를 승인한다)이 실질 근거이고, (1)·(2)는 문언 근거다. 2회 시도를 유지하는 결론은 타당하다.
  참고 관찰: gate `.ai/approvals`의 기존 diff 승인 31건 중 운반형 11건(`20260923-ts2-pytest-split` 등)은 `diff_head`가 gate에서 도달 불가능한 1차 시도 커밋이다. 그러니 (1)의 "저장소에 있어야"를 '도달 가능'으로 읽으면 선례와 맞지 않는다. '1차 시도가 실제로 만든 커밋'이라는 뜻으로 읽어야 일관된다(m-3).

## 4. S-3 확인 -- R-4는 같은 출처, 계약 2는 목적 파일 안 충돌

* 출처가 다른 같은 이름 fixture 배치를 확인했다: `s040_state`(SR → 8, SD → 7), `s051_state`(SR → 8, SD → 7), `s063_state`(SR → 5, SD → 7). 같은 이름 test 12쌍은 12쌍 모두 다른 목적 파일로 나뉜다. card 계약 2·R-4 문언과 실측이 같다.
* 정상 병합본에서 같은 출처 def의 중복은 0이다(작성자 `gen_t1.py`가 공유 2개를 `_selftest_shared.py` 한 곳에 둠). R-4 거부 근거가 '같은 출처 (옛 파일, 이름)'이라 정상본을 거부하지 않는다.

## 5. 새 계약 -- 생성기 엔진 import 0(계약 2, R-11)

* 키트 `t1_map.py`의 AST import는 `ast`·`collections`·`import_layering`·`json`·`subprocess`·`sys`다. 엔진 줄기(MOD 10 + split 4 + ACF + `run_harness`)를 모듈로 갖는 Import/ImportFrom은 0이고 `importlib`·`runpy`·`__import__` 호출도 0이다.
* 내 사슬에서 `runpy`로 실행한 뒤 `sys.modules` 증분 중 표준 밖 모듈은 `import_layering`·`role_paths`(gate 캐시)뿐이다. `A`·`workspaces` 아래 모듈은 0이다.
* R-11 변형(`import stick_diagram` 한 줄 추가)에 같은 AST 검사가 `['stick_diagram']`을 낸다. 거부가 실제로 동작한다.

## 6. 새 R-12 -- 직접 재현

같은 base `58d40b8`·head `e9b47d9`, 이 초안으로 만든 interface card(기존 함수 6, 아래 7)로 돌렸다.

| 파일 선택 | files | 규칙 (1) | UNJUDGED | NO-SUBJECT | 판정 |
|---|---|---|---|---|---|
| 도구 자체(파일 인자 없음 → `--no-renames --diff-filter=AM`, `test_lint.py` 719행) | 12 | FAIL 4(s009 2·s052·s054, 전부 `test_mod8_…`) | 182 | 478 | FAIL |
| `git diff --name-only --diff-filter=AM`(no-renames 없음) 목록을 인자로 | **10** | 0 | 72 | 280 | **PASS(거짓)** |

빠진 두 파일은 git이 rename으로 잡은 `test_selftest_stick_diagram → test_mod7`(R057), `test_selftest_sizing_recipe → test_mod8`(R069)이다. card 수치와 같다.
면제 decision 기록 시제품(새 id 3)을 head에 커밋하면 `merge_gate.py parse-approval` exit 0, V4 **PASS**(`exempt` 4, FAIL 0, files 12)다.

## 7. 양식(gate `2db7622` `git archive` 사본)

* `role_paths.parse_spec_card(text, expect_id="20261006-p3-test-relocate")`: 예외 없음. phase 3, test-only, gate_change no, approval 3, 절 11.
* `interface_card.py <초안> --root <내 T1 head>`: exit 0. 기존 함수 6(`sizing_layout_convergence.optimize_full_circuit_budget`·`_build_theta_evaluator`, `gmid_sizing_engine.size_transistor`·`width_from_id_density`·`check_quasi_static`, `circuit_state_graph.load_topology`), 신규 시그니처 표는 비어 있다.
* 부수 확인: ts3 주석은 base 27·68행에서 head 27·74행이 된다(계약 6·7 표기와 같다). head 추적 `.py`(`.ai/verification` 제외)에 `test_selftest_[a-z_]+\.py::` 0.

## minor

* **m-1 tools 경유 조항 문언이 두 가지로 읽힌다 -- s004가 갈린다.** '의도' 22행 "`A/tests/tools/` 모듈을 거쳐 읽는 이름(그 도구 모듈이 최상위 `from <엔진> import`로 받는 이름)"의 두 읽기:
  (A) test가 읽는 이름 자체가 도구 모듈이 엔진에서 받은 이름일 때만 센다.
  (B) test가 도구 모듈의 이름(예 `run_regression_case`)을 읽으면 그 도구 모듈이 엔진에서 받은 이름 **전부**를 닫힘에 넣는다.
  내가 처음 문언대로 구현한 (A)에서는 `sizing_recipe::test_s004_optimize_multistage`(본문이 `run_regression_case`·`_os`만 읽음)가 본 규칙 0 → 메서드 0 → SR 출신이라 **STOP**이 된다. (B)에서는 `regression_runner`의 `SemiEmpiricalGmIdLUT`(1)·`_COMPENSATION_REGISTRY`(4)·`optimize_multistage`(4)로 MOD4가 된다. 키트(`t1_map.py` 133~134행)와 card 수치(sizing 4:10)는 (B)다.
  r1의 '작성 전 실측' 2에 있던 "`test_s004_optimize_multistage` … 닫힘 4(도구 경유)"가 r2에서 빠져 문언만으로는 (B)가 드러나지 않는다. 계약 2가 생성기 재실행으로 판정하므로 판정이 틀리지는 않는다. 다만 card가 규칙의 정본(oracle (d))이므로 (B)로 못박는다.
  고칠 문장(예): "닫힘이 `A/tests/tools/` 모듈에서 import한 이름을 읽으면, 그 도구 모듈이 최상위 `from <엔진> import`로 받는 이름 전부를 닫힘이 읽는 엔진 정의로 센다(모의 해당 1: s004 → MOD4)". '재현할 수치'에 "tools 조항으로 정해진 test 1 = s004" 한 줄을 추가한다.
* **m-2 키트 `t1_run.sh` 19행이 R-12 함정 그대로다.** `FILES=$(git diff --name-only --diff-filter=AM …)`를 인자로 넘긴다. `out/r2/t1_v4.json`은 files 12(도구 선택)라서 그 파일은 따로 다시 돌린 결과로 보인다. 스크립트와 기록 원자료가 어긋나 재현 경로가 함정을 밟는다. 역할 산출물은 아니지만 auditor 브리프 재료가 될 수 있으니 파일 인자를 빼 둔다.
  R-12 행은 '병합본 사본에 하나씩 커밋'하는 표 머리와 모양이 다르다(커밋 변형이 아니라 절차 변형이다). "(절차 변형 -- 커밋 없음)"을 붙이면 auditor 자기 점검 구현이 헷갈리지 않는다.
* **m-3 계약 10 근거 (1)의 표현.** §16 인용은 00-common 자신의 승인 문장이다. 일반 규칙의 근거로는 같은 §8.2 staged_diff 항("아직 없는 그 커밋의 id를 적을 수 없다")과 05 §12 운반 행(`diff_head = T`)이 더 직접적이다.
  또 운반형 선례 11건의 `diff_head`는 정리 뒤 gate에서 도달 불가능하다. 그러니 "저장소에 없다"를 '1차 시도가 만든 실제 커밋이 아직 없다'로 적으면 선례와 어긋나지 않는다. 결론(2회 시도 유지)은 그대로다.
* **m-4 gate 판 표기.** 머리와 '작성 전 실측'이 `6c724de` 판이다. gate는 지금 `2db7622`이고 `skills` 변경 1파일(`contracts/test_b26pre_existing_paths.py`, `sizing_recipe`·`stick_diagram` 직접 import)이 있다. T1 매핑·V5 해시·V4에는 영향 0이다(이 검토가 `2db7622`에서 같은 값을 냈다). PT3 총수는 +19로 바뀐다.
  '작성 전 실측' 11 (iv)가 card 커밋 직전에 덮는 항목이라 표기만 갱신하면 된다.

## 재측정하지 않은 것

PT3 전체·셔플 5회는 다시 돌리지 않았다. r2 변경(s155 이동)의 동작 영향은 `test_mod3`·`test_mod7` 134 passed로 확인했고, PT3·셔플은 1차 검토와 작성자 r2가 쟀다.

## 재현 방법(스크래치는 지웠다)

`build386.sh`(키트 `build369.sh`에서 REV=`2db7622`·경로만 바꿈) → `chain_lean.py` 8 card → `my_map.py <r> 58d40b8`(내 구현; 변형 V0/Vconf/VtoolsB/Vnested/Vr1 + SCOPE 판) → 내 매핑을 `gen_t1.py` 입력으로 → gate `weakening_diff.py`·`interface_card.py`·`test_lint.py`(도구 선택 / R-12 목록) → decision 시제품 + `parse-approval` → `t1_map.py` `runpy` 실행 후 `sys.modules` → R-11 AST 변형.
