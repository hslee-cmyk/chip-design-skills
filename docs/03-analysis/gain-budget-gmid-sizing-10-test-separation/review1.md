# review1 -- `10-test-separation` design v1.0 초안 독립 검증

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md`(586줄), 부산물 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/`
* 기준 커밋: HEAD = gate/master = `89d257c3c332158697389c9b10195b210f2ae03b`
* 검증자: 독립 검증 agent(작성자 아님). 문서는 고치지 않았다. 계수는 작성자 스크립트를 import하지 않고 새로 구현했다(스크래치 `recount.py`).
* 실행은 모두 스크래치 격리 복제본(`<scratch>/rv1iso`, `git clone --no-hardlinks --no-local` 뒤 `remote remove origin`)에서 했다. 끝난 뒤 `git -C rv1iso status --porcelain` 빈 출력.

## 종합 판정: **수정 뒤 승인**

수치 대부분과 쓰기 경로·EL3/EL4 모양 판단은 맞다. 하지만 Phase 1을 문서대로 실행하면 막히는 곳이 넷 있다(S1). 모두 국소 수정으로 고칠 수 있어 재작성은 필요 없다.
C8(IC3) 한 card에 S1 셋이 몰려 있다.

---

## S1 -- 실행을 막음(A) 또는 실행을 막는 모순(B)

| # | 분류 | 지적 | 근거 | 최소 수정 |
|---|---|---|---|---|
| S1-1 | A | **C8 배선이 이관본 stick Test 26을 깨서 V1이 FAIL한다.** Test 26은 `save_instance_json(_inst_path, <folded_cascode>, {}, _fc_result)`(sizing = 빈 dict)을 부른다. §5.5 배선 (1)을 넣으면 13개 소자 모두 `missing_sizing` → `ValueError` → 이관본 stick이 exit 1 → `test_legacy_selftests.py` FAIL. §4는 C8 행에 "이관본 판정이 모두 assert라 회귀가 exit code로 드러난다"고만 적고 이 충돌을 다루지 않는다(C9가 C8 뒤라 C8 시점에는 이관본이 있다). | `skills/analog-gmid-design/assets/stick_diagram.py:10744-10750`. 재현: 스크래치 `ic3probe.py`(§5.5 두 게이트를 격리 복제본 사본에 흉내 내 배선) → `stick_diagram 1 ... ValueError: rv1 completeness`, 로그 `SAVE_REJECT ...folded_cascode.topology.json missing_sizing=13`. 저장 검사만 끄고 다시 돌린 `ic3probe2.py`에서는 4모듈 모두 rc 0이고 이름 충돌 거부는 0건이다(`load_topology` 쪽 오거부 없음). | C8 test 커밋이 Test 26 섹션을 새 계약에 맞게 고친다: 빈 sizing이면 `ValueError`임을 단언하고, 정상 저장은 완전한 sizing으로 보인다. 이 test 변경은 V5 발견(리터럴·판정 변경)이라 승인 기록이 필요하다. §6.7과 §9 C8 행의 승인 기록 칸에 적는다. 다른 방법은 C8을 C9 뒤로 옮기는 것인데, 옮겨도 같은 섹션이 unit test로 남아 같은 수정이 필요하다. |
| S1-2 | A | **C6 conftest 뒤로는 V3 도구가 pytest를 돌리지 못해 C8 V3가 무조건 FAIL한다.** `00-common` §9.3과 §5.4는 `--gmid-phase`가 없으면 `pytest.UsageError`를 내게 한다. 그런데 `mutate_changed.py`의 `run_tests`는 `--gmid-phase`를 넘기지 않는다. 그래서 변이 전 기준 실행이 exit 4 → `baseline_ok` 거짓 → 모든 변이가 "survived" → V3 FAIL. `--gmid-phase`만 넘겨도 부족하다. 엄격 집합(`--gmid-strict` 또는 `--gmid-dod`)이 없으면 `test_ic3`가 non-strict xfail이라, 변이가 test를 깨도 exit 0이 되어 변이가 살아남는다. C6 뒤 첫 red-green이면서 소스 def를 바꾸는 card가 C8이다(C7은 docstring만 바꾸고, `def_hash`가 docstring을 빼므로 대상 0). | `tools/gates/mutate_changed.py:214-221`(명령에 `--gmid-*` 없음), `:236`·`:245-247`(기준 실행 실패 → survived). `grep -rn "gmid-phase" tools/gates/*.py` → `merge_gate.py`에만 있음. C8 대상 def: `load_topology` 변이 55개, `save_instance_json` 8개(`mutate_changed.mutants`로 셈). | Phase 1 순서에 C8 **앞** 게이트 변경 card를 하나 넣는다(code-author, `gate_change: yes`, red-green, oracle (a)). 내용은 `mutate_changed.py`가 spec card Phase와 엄격 집합을 `--gmid-phase=`·`--gmid-strict=`로 넘기는 것이다. 막는 규칙을 넓히는 것이 아니라 도구를 승인된 conftest 계약에 맞추는 수정이다. |
| S1-3 | A | **R1 운반 경로에 `conftest.py`가 오면 아무도 쓸 수 없다.** R1은 T의 blob을 `docs/03-analysis/.../v5-carry/<id>/<원래 경로>`에 둔다. C6·C9의 발견 경로가 `skills/analog-gmid-design/assets/tests/conftest.py`이므로 운반 파일 이름이 `.../conftest.py`가 된다. 이 이름은 사용자 행 `**/conftest.py`(판정 환경, 제외는 `assets/tests/conftest.py` 하나뿐)에 맞아 사용자만 쓸 수 있다. §9 쓰기 경로 대조의 R1 행("쓸 수 있음")이 틀렸다. | `role_paths.allowed` 실측: 오케스트레이터·test-author·code-author 모두 `v5-carry/<id>/skills/analog-gmid-design/assets/tests/conftest.py` → `False`, 판정 행 `(사용자, **/conftest.py, 판정 환경)`. 같은 디렉터리의 `README.md`·`legacy/*.py`는 오케스트레이터 `True`. | 운반 파일을 원래 경로 그대로 두지 않는다. 예: `v5-carry/<id>/<blob id>.blob` + 경로 대응표. test-author가 `cp`할 때 이름을 되돌린다. §12 R1의 2·3단계와 §9 R1 행을 고친다. |
| S1-4 | B | **U 번호가 충돌한다.** 계획 N7.2에는 이미 U-40(역할 분리 게이트 해제 시점, 필요 시점 7c)이 있다. 이 문서의 U-40(데모 삭제)·U-41(R1)·U-42(`.gitignore`)을 그대로 추가하면 "C4는 U-40 확정 전 착수 금지"(§11)가 7c 결정을 기다리게 된다. | `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:1114`(U-40 기존). 계획서에 `U-41`·`U-42`·`U-43`은 0건(`grep -c`). 문서 안 참조 줄: 57, 318, 327, 393, 474, 501, 530, 564-566. | U-41·U-42·U-43으로 새 번호를 매기고 위 참조를 모두 고친다. |

### R1이 실제 문제인가 (요청 5)

**실제 문제다. 다만 R1은 기존 규칙 안에서 도는 절차라 게이트 변경이 필요 없다.**

* 승인을 찾는 곳은 둘 다 head 쪽이다. `weakening_diff.py:260`은 `approved_hashes(root, ns.head)`, `merge_gate.py:1219-1224`는 `load_approvals(new_view)`(audit 커밋 트리)를 본다. 로더 규칙 6도 `new_view`에서 읽는다(`merge_gate.py:1192`).
* 그 트리에 `.ai/approvals/*`를 넣는 길이 없다.
  * 경로표에서 `.ai/approvals/**`는 오케스트레이터만 쓴다.
  * EL4 모양상 test-only는 `old..new^`가 전부 `Role: test`여야 하고(`merge_gate.py:1172-1179`), red-green·equivalence는 test 사슬·code·M·audit 외 커밋이 끼면 거부한다(`:1165-1167`).
  * M 트리는 code 끝 트리와 같아야 한다(`:1147`).
  * 진행 중에는 문서 push를 EL1이 거부한다(05 §6.2 push 행). 설령 push해도 audit 브랜치가 non-ff가 된다.
* 따라서 승인은 base에 이미 있어야 한다. 그런데 diff 해시는 T의 blob으로 만들므로(`00-common` §8.2, `weakening_diff.diff_hash`) T 전에는 알 수 없다.
* 더 작은 해법("승인을 test 커밋 전에 master에 먼저 넣기")은 발견 경로의 head blob을 미리 알 때만 된다. 순수 삭제가 그런 경우다. 다섯 card는 모두 test-author가 쓰는 내용을 발견 경로에 담는다. `weakening_diff`로 판독한 발견 경로는 다음과 같다.

  | card | 발견 경로 |
  |---|---|
  | C3 | 기준선 `.log`. `.py`에 dict 항목만 더하는 것은 `insert` opcode라 발견이 아니다 |
  | C4 | 이관본 `.py`의 리터럴 삭제 |
  | C5 | `README.md` 추가 |
  | C6 | `conftest.py` |
  | C9 | `conftest.py`, wrapper test 함수 삭제 |

  그래서 미리 넣을 수 없다. C3의 `.log` 두 줄은 결정론 출력이라 미리 계산할 수는 있다(아래 재계수 C3 행). 하지만 그러면 오케스트레이터가 test 데이터를 정하는 셈이라 N3.12.1과 어긋난다.
* 결론: 한 번 실패한 뒤 재시도하는 R1이 기존 규칙(05 §12 재시도·경로표) 안에서 가능한 최소 해법이다. 필요한 개정은 문서 서술(05 §12에 절차를 적는 것)뿐이고, 게이트나 규칙은 바꾸지 않는다.
* 단 S1-3(conftest 운반 이름)과 S3-3(운반 방식)은 고쳐야 한다.

---

## S2 -- 실행을 바로 막지는 않지만 틀리거나 다음 단계에서 막는 것

| # | 분류 | 지적 | 근거 | 수정 |
|---|---|---|---|---|
| S2-1 | B | **PASS/FAIL 토큰 522는 잘못 센 값이고, 실제는 354다**(sizing 113 · stick 232 · design_report 5 · topology_library 4). 작성자 계수기 `all_strings`가 `JoinedStr`(f-string 전체의 상수 조각을 이은 텍스트)와 그 자식 `Constant`를 둘 다 세서 f-string 상수 조각이 두 번 들어갔다(중복 168 = 90+75+2+1). §7 T의 문구("모든 `ast.Constant` 문자열과 f-string 상수 조각")도 f-string 조각이 이미 `Constant`이므로 두 번 세라는 뜻으로 읽힐 수 있다. | `count_selftest_sections.py:47-53`·`:87-99`. 재계수 명령과 출력은 아래 표 T행. | §3, §6.3 증거("T = 522"), §9 C4 auditor 칸("T=522→0")을 354로 고친다. §7 T 식은 "문자열 `Constant` 노드마다 한 번(f-string은 그 안의 `Constant` 조각만)"으로 못박는다. DoD 기준(0)과 범주 B 판정(≥1)은 영향이 없다. |
| S2-2 | A | **C8 V3 인벤토리가 설계한 test로는 모자란다(S1-2를 고친 뒤에도).** V3는 바뀐 def 전체를 변이한다. `load_topology` 변이 55개(문장 삭제 51) 중 연결 파일 루프 본문(`all_netlist.extend(linked_data[...])` 등)은 library 9회로가 모두 `"linked_topology_files": []`라서 §6.7의 입력(9회로 무변형 로드와 이름 변형 3종)으로는 죽지 않는다. 그 사이 C8 V3 인벤토리에 드는 test는 `contracts/test_ic3.py`뿐이다. 이관본은 하위 프로세스로 돌아 정적 호출 그래프에 들지 않는다. | `mutate_changed.py:174-175`(인벤토리 = 정적 도달), `:242-244`. `grep -h -A2 '"linked_topology_files"' library/*.topology.json` → 전부 `[]`. 변이 수는 `mc.mutants`로 셈. | §6.7에 V3 대상 def(`load_topology`·`save_instance_json`·새 두 함수)를 적고, test-author가 죽일 입력을 적는다. 예: library 회로를 둘로 쪼갠 연결 파일 픽스처(WP-07 '로드·변형'), `meta` 필드 단언. 등가 변이는 decision 승인으로 면제한다. |
| S2-3 | A | **C6 자기 V1에도 `--gmid-phase=1`이 있어야 한다.** §6.5는 "C6 병합 **뒤부터** V1 명령에 `--gmid-phase`가 붙는다"고 적었다. 그런데 C6의 병합본(head) conftest는 기본값 없이 그 옵션을 요구한다. 그대로 따르면 C6 V1이 UsageError(exit 4)로 끝난다. 반대로 base 쪽 실행(C6 전 conftest)에 그 옵션을 주면 모르는 옵션으로 끝난다. merge gate는 C6 때 old conftest에 옵션이 없어 대조하지 않으므로 둘 다 허용된다(`merge_gate.py:1209-1213`, `:981-985`). | §5.4 `pytest_configure`, `00-common` §9.3(`:401`). | §6.5를 "C6의 병합본 실행부터 `--gmid-phase=1`, base 쪽 실행은 붙이지 않음"으로 고친다. |
| S2-4 | A(다음 Phase)·B | **엄격 집합이 빈 경우를 정하지 않았다.** `00-common` §8.1(`:299`)은 엄격 집합이 비면 `--gmid-strict=`(값 없음)을 넘기라 하고, merge gate도 빈 집합이면 `--gmid-strict=` 토큰을 요구한다(`merge_gate.py:1008-1012`). §5.4는 "`--gmid-strict` 키마다 ... 없으면 `pytest.UsageError`"라고만 적어, 빈 값을 `split(",")`하면 키 `""`가 나와 거부된다. Phase 1은 C7 뒤로 늘 비어 있지 않지만, Phase 2의 첫 card에서 V1이 막힌다. §5.4가 `00-common` §9.3을 다시 서술하면서 이 부분을 빠뜨린 것이다(N9.4 인용 규칙). | `00-common` design `:299`·`:401-405`, `merge_gate.py:1007-1012`. | §5.4를 인용으로 줄이고 "빈 값 = 키 없음"을 명시한다. |
| S2-5 | A | **C9 V4 (3)에 걸릴 섹션이 있다.** HEAD 기준으로 assert가 모두 `if`·`try` 안에 있고 거부 try(→ `pytest.raises`)로 바뀌지도 않는 섹션이 있다: sizing S14·S51·S54(일부), stick S157, design_report S3. design_report S3은 `if os.path.exists(...)` 아래에 assert, else에 `SKIP` print가 있는 조건부 skip이다. §6.8 규칙 5("판정은 바꾸지 않는다")대로 그대로 옮기면 `test_lint` (3) FAIL이다(`test_lint.py:606-609`). 처리 규칙이 없다. | 스크래치 계수(섹션별 assert 조상): 위 5개. 조상이 `Try`뿐이고 거부 try인 8개(sizing S3·39·41·43·48, stick S90·124·125)는 `pytest.raises`로 바뀌어 해당하지 않는다. | §6.8에 규칙을 더한다. 예: 조건을 먼저 assert한다(판정 추가라 M2 ≥에 맞음). 그 조건의 oracle은 spec card에 적는다. |
| S2-6 | B | **05 §18과 어긋난다.** 05 §18은 "⑤ 뒤 게이트 변경은 spec card로 한다(red-green, oracle (a))"고 적었다. C10은 test-only인 게이트 변경이다. P5가 계획 N3.12.3만 고치고 05 §18은 개정 목록에 없다. EL4는 이를 강제하지 않아(`gate_change_ok`는 판정 유형을 보지 않는다, `merge_gate.py:720-741`) 실행은 된다. | 05 design §18. | §12에 05 §18 개정(R2: "redteam 데이터만 바꾸는 게이트 변경은 test-only")을 더한다. |

---

## S3 -- 문구·명확성

| # | 지적 | 근거 |
|---|---|---|
| S3-1 | P2가 계획 N6.1에 "C1·IC3·IC5 red-green"이라고 적는다. `C1`은 이 문서의 card 표지라 계획서에는 정의가 없다. "TS1 선행(추출 도구)"로 적는다. 판정 표 해시에는 영향이 없다(아래 재계수). | §12 P2 |
| S3-2 | "데이터 의존을 주는 섹션 sizing 30 · stick 97 · design_report 2 · topology_library 5"의 정의가 섞였다. sizing은 머리 P를 빼고(P 포함하면 31), design_report는 P를 넣었다(P 빼면 1). | 작성자 `selftest_sections.json`의 `provides_to` 재집계 |
| S3-3 | R1 2단계의 운반 방식을 명시한다. PowerShell 5.1 `>`는 UTF-16으로 써서 blob이 달라진다. bash에서 `git -C <W>/<id>-test cat-file blob <T>:<path> > <운반 파일>`로 적는다. 승인 머리의 `diff_head = T`는 정리 뒤 도달 불가 커밋이 된다(게이트는 형식만 본다). 사용자가 나중에 재확인할 수 있게 운반 디렉터리 경로도 승인 범위에 적는다. `core.autocrlf=true`이지만 기준선 blob은 LF뿐(CR 0)이라 `cp` 왕복으로 blob이 바뀌지는 않는다. | `git config --get core.autocrlf` → `true`, blob CR 계수 0 |
| S3-4 | D4·D6이 `PT` 뒤에 test 경로를 하나 더 붙인다. `PT`에 이미 tests 경로가 있어 전체를 도는 것과 같다. 기준에는 문제가 없고 중복일 뿐이다. | §10 |
| S3-5 | §6.8의 M1 "매핑표의 A·B 섹션 수"가 C2 기준 범주인지 C4 뒤 범주인지 모호하다. C4에서 판정이 사라진 B 섹션(기대 쪽이 적히지 않은 print만 있던 섹션)이 있으면 둘이 달라진다. | §6.8·§7 M1 |
| S3-6 | N9.1 `10-test-separation` 행의 '읽을 plan 절'에 없는 N3.12.2·N4.2·N4.3·N6.3을 썼다. N9.1은 "읽기 전에 그 절을 이 열에 추가"를 요구하므로 §12에 추가 요청을 넣는다. | 계획 N9.1 |
| S3-7 | §4 C10 "다른 card와 독립"은 틀렸다. §6.9가 C1 `sections`로 의존 이름을 찾으므로 C1 뒤여야 한다. | §6.9 |
| S3-8 | 계획 N4.1 IC7 칸은 "(regression)"인데 이 문서는 `contracts/test_ic7.py`에 둔다. 대조 test K는 contracts만 보므로 자기 안에서는 일관되지만, 계획과의 차이를 한 줄 적는다. | 계획 N4.1 IC7 |

---

## 확인 결과 -- 맞는 것

* **쓰기 경로**(부트스트랩 완료 기준, `role_paths.allowed` 실측)
  * code-author: `tools/migrate/extract_selftest.py` True
  * test-author: `tests/tooling/test_extract_selftest.py` True(`tooling`은 `tests/tools/**` 제외에 걸리지 않음), `tests/conftest.py` True(판정 환경 행의 제외 glob)
  * test-author: `tools/gates/redteam/lib/rt.py`·`cases/caa970b-*/run.sh` True(게이트 변경 조건)
  * 오케스트레이터: `tools/gates/**` 거짓(부트스트랩 행 소멸)
  * 틀린 것은 R1 conftest 한 곳뿐이다(S1-3).
* **TS0 test-only 판단은 맞다.** red-green·equivalence 모양은 code 커밋이 1개 이상이어야 하고(`merge_gate.py:1159-1161` "code 커밋이 없다"), U-01로 대상 코드가 그대로이므로 test-only 모양만 가능하다. 격리 복제본에서 Test 16 (b)에 키 한 줄을 더해 실행하면 rc 0이고, 출력 차이는 정확히 두 줄이다(`[FAIL] 3. ...UNDISPOSED` → `[PASS] 3. ... 4 candidate groups, all disposed`, `전체 결과: FAIL -> FAIL(예상과 다름…)` → `PASS -> OK`). §6.2의 기준선 재생성 범위("(b) 줄만")와 맞는다.
* **TS1 두 커밋(C2)은 EL3·EL4를 통과할 수 있다.**
  * test 커밋은 test 분류만, code 커밋은 소스만 바꾼다(`source_test_violation` 무관).
  * equivalence 모양은 test 1 → code ≥1 → M → audit이다(`merge_gate.py:1137-1168`).
  * V5: 소스의 `__main__` 단위가 통째로 사라져도 `compare_units`는 leaf가 `test`로 시작할 때만 삭제를 발견으로 센다(`weakening_diff.py:181-186`). 문서 주장대로 발견 0이다.
  * V4: `find_test_functions`가 최상위 `test*`만 보므로 이관본(모듈 수준 스크립트)은 대상이 아니다(`test_lint.py:620-629`).
  * V3: `tools/migrate`는 `_is_source`가 아니어서 대상 0이다(`reachability.py:175-177`). 그래서 C1도 V3 대상이 0이다.
* **P1~P5는 plan_tables 값을 바꾸지 않는다.** 원본과 P1~P5(+N7.2 행 추가)를 적용한 스크래치 사본 모두 `plan-tables-hash` = `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`. C1·C2(00-common)와 R1(05)은 계획서 밖이라 해당하지 않는다.
* **N9.2 필수 절 8개가 모두 있다**(§1·§5·§7·§8·§9·§10·§11·§13). N9.1 행의 필수 내용(TS0 원인 대조 ~ IC5 영역 줄 검사)도 모두 다룬다. TS2 매핑표는 규칙과 생성 절차로 줬는데, 섹션 번호가 C2 산출물에 달려 있으므로 타당하다. `00-common` 인용은 대체로 절 번호로 했고, 예외가 §5.4다(S2-4).

---

## 재계수 (명령과 결과)

독립 계수기: `<scratch>/recount.py`(§5.1·§7 T 문언대로 새로 구현), `C:/Python314/python.exe recount.py <A>`.

| 항목 | 문서 | 재계수 | 판정 |
|---|---|---|---|
| `__main__` 블록 | 7 파일, 인라인 4 | 7, 인라인 4. 범위 12571–15269 / 8992–12936 / 319–382 / 528–694 | 일치 |
| 섹션(P 포함) | 77·174·5·16 = 272 | 77·174·5·16 = 272 | 일치 |
| 범주 P/D/A/B/C | sizing 1/5/68/1/2 · stick 1/10/114/21/28 · dr 1/0/4/0/0 · tl 1/0/10/0/5 | 같음 | 일치 |
| C 중 뒤 섹션이 읽음 / 데모 | 2·13·2 / 18 | 2·13·2 / 18(stick 15 + tl 3, 목록 같음) | 일치 |
| assert / raise AE / 거부 try | 596 / 30 / 29 | 220+346+13+17 = 596 / 20+10 = 30 / 20+9 = 29 | 일치 |
| **print PASS/FAIL 토큰 T** | 203·307·7·5 = **522** | 113·232·5·4 = **354**(f-string 상수 조각 중복 90·75·2·1 = 168을 더하면 522) | **불일치 S2-1** |
| `lut` 섹션 / A+B / `pytest.raises` 후보 | 27 / 218 / 29 | 27 / 69+135+4+10 = 218 / 29 | 일치 |
| 블록 안 def / `__file__` / 금지 호출 | 5·6 / 8·8·2·0 전부 dirname(abspath) 꼴 / 0 | 같음(stick은 별칭 8종이 모두 같은 꼴) | 일치 |
| 모듈 이름 읽음 | 56·92·4·8, 미해결 0 | 작성자 JSON 값만 확인(독립 구현 안 함) | 확인만 |
| 실행 시간(시드 1, 1회) | sizing 11.2–12.8 · stick 23.3–24.9 · dr 0.3 · tl 1.1–2.9 s | 12.3 · 24.1 · 0.3 · 1.0 s, 모두 rc 0, 실행 뒤 작업 트리 변경 0 | tl만 범위 하한보다 0.1 s 짧음(측정 변동, 지적 아님) |
| 기준선 드리프트 | sizing 45줄(361 → 388), stick 경로 1줄 | `difflib` opcode: 삭제 9 + 추가 36 = 45(replace 5, insert 4), 줄 수 361/388. stick은 828행 절대 경로 1줄만. Test 16 `FAIL(예상과 다름` 1줄(HEAD·기준선 둘 다) | 일치 |
| IC5 대상 게이트 | 21(sizing 7 · stick 13 · acf 1 · harness 0), 절·영역 줄 0 | 21(같은 이름 21개, `__main__` 안 0), 두 줄 모두 0 | 일치 |
| library 이름 충돌 | 0 | 9회로 모두 중복·소자∩수동·casefold 0 | 일치 |
| `A/tests/` 추적 | 48(.py 44, test_*.py 0, baseline 3) | 48 / 44 / 0 / 3 | 일치 |
| `A/tests/*.py` print 토큰 | 0 | 0 | 일치 |
| D5 HEAD 줄 수 | 4 | 4(`.gitignore:19`, baseline README 18·19·121) | 일치 |
| 비-Phase-1 xfail 케이스 | 12 | IC1·2·4·6·8·9·10(7) + IC7 2 + IC11 3 = 12. `read_plan_tables`의 `ic_parts`·`ic_test`가 §6.5 표와 같음 | 일치 |
| plan_tables 해시 | 불변 주장 | 원본·P1~P5 사본 모두 `7167e028…596d` | 일치 |

사용한 주요 명령(모두 스크래치 또는 읽기 전용):

* `git ls-files skills/analog-gmid-design/assets/tests | wc -l`
* `git grep -n -I -e "tests/baseline" -e "selftest.baseline" -- skills workspaces tools .gitignore ":(exclude)tools/gates/redteam"`
* `C:/Python314/python.exe C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.git/gmid-gate-cache/89d257c3c332158697389c9b10195b210f2ae03b/merge_gate.py plan-tables-hash <파일>`
* 스크래치 스크립트: `run4.py`(4모듈 실행·해시·시간), `bdiff.py`(기준선 diff), `t16.py`(Test 16 한 줄 수정 효과), `ic3probe.py`·`ic3probe2.py`(C8 배선 흉내), `apply_p.py`(P1~P5 적용 사본). 결과 파일은 같은 스크래치 디렉터리의 `run4.jsonl`, `t16_result.txt`, `ic3probe*.json`·`.log`.
