# review25 -- `00-common` design v1.4 검증(review24 R-01~R-05 닫힘 + 판정 표 직접 읽기 §9)

* 대상: `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` v1.4(작업 트리, 607줄), 계획서 v5.19(`git diff HEAD -- docs/01-plan`), `.ai/approvals/_TEMPLATE.md`
* 기준: review24의 R-01~R-05(와 S3 잔여 R-06~R-14 참고), 지정 점검 1~6
* 검증자: 독립 검증 agent. 이 설계도, review21~24도 쓰지 않았다. 측정 스크립트는 저장소 밖 scratchpad `review25/`에 있다.
  * `rpt.py`(+`rpt_out.txt`, `mut_out.txt`): §9.2만 보고 새로 짠 `read_plan_tables`와 변형 입력 검사
  * `pt/`(+`run1~3.txt`, `capture_*.jsonl`): pytest 9.0.2 수집 오류 훅 실측
  * `blobhash.py`(+`blobhash.txt`): §8.2 blob 기반 diff 해시
  * `cells.py`(+`cells.txt`): 표 셀 수 검사
  * 저장소에서 바꾼 파일은 이 보고서 하나다.
* 심각도: **S1** = 승인을 막는다(틀림·모순·구현 불가) / **S2** = 승인 전에 고친다 / **S3** = 경미

---

## 1. 닫힘 표 (R-01~R-05)

| ID | 판정 | 근거(인용) |
|---|---|---|
| R-01 | **닫힘**(새 S1 Q-01을 낳음) | §11.1: "옛 커밋에 도구를 소급 적용하지 않는다(review24 R-01 …)". 대신 "Phase 4 순서를 **TS4 → DF-35 → DF-36 → CC-7·CC-8 → 나머지**로 둔다". TS4, DF-35·36, CC-7·8 각각을 어떻게 다루는지도 적었다. 계획 N6.1 4행에도 같은 순서가 있다. 소급 비교는 없어졌다. 그러나 이 순서 때문에 CC-7·CC-8이 CC-4(`FAILURE_CLASSES`·`exit_code_for`·`FailureRecord`·DF-37)보다 앞에 온다(Q-01). |
| R-02 | **부분** | §8.1: "예외 타입 = `call.excinfo.value.__cause__`의 타입 … `__cause__`가 없으면 `call.excinfo.type`". 실측(§3)에서 훅 호출과 `__cause__`는 설계대로 동작한다. 남은 것은 둘이다. (1) 수집 오류가 하나라도 나면 pytest가 세션 전체를 중단한다. 그래서 같은 실행의 실행 단계 red가 기록되지 않는다(Q-03, 새 S2). (2) R-02가 요구한 '신규 심볼' 판정 방법(`exc.name` 대조)이 아직 없다. "interface card의 **신규** 심볼을 import하는 경우에 한해"라는 문구만 있다. |
| R-03 | **닫힘** | §6.3 `where`·`scope` 행: "**옛 이름이 지금(이관 전) 놓인 곳**이다. N3.16 '저장 위치' 칸은 새 이름이 갈 곳이라 쓰지 않는다 … (예: `vs`는 topology의 `/device_roles/*` -- 현재 `validate_no_legacy_vs_key`가 보는 곳과 같다)". §6.2 `vs` 행과 이제 일치한다. |
| R-04 | **닫힘**(설계 변경으로 해소) | §9: "**사본을 두지 않는다**", §9.1: "merge gate는 **base 판** 계획서를 읽는다". 병합본 상수를 읽을 일이 없어졌으므로 R-04의 문제 자체가 사라졌다. 남은 판 규칙 문제는 Q-04에 적는다. |
| R-05 | **닫힘** | §10.1: "**CC-7이 이 부분을 함수로 추출한다**(동작 보존 추출이라 그 spec card는 `equivalence`). Phase 3는 이동만 하므로 … 추출은 Phase 4다. 추출된 함수의 목적 모듈은 MOD6". 적힌 곳도 셋이다. §14 CC-7 "θ 탐색부 함수 추출(`equivalence` card)", §13 표, 계획 N9.1 `40-defect-fixes` 행 "CC-7(θ 탐색부 함수 추출…)". 빌더 호출은 탐색 함수 밖에 둔다("평가 커널 빌더 호출 뒤 grid·slsqp 분기"). |

**집계: 닫힘 4(R-01·03·04·05) / 부분 1(R-02) / 안 닫힘 0**

review24 S3 잔여:

| ID | 상태 | 근거 |
|---|---|---|
| R-06 | 닫힘 | §8.2가 blob id 방식으로 바뀌었다(실측 §4). |
| R-07 | 닫힘 | §8.2: "`diff_path`는 그 design 문서와 그 문서가 기댄 개정 파일 전부다(§16)". |
| R-08 | 닫힘 | 계획 N4.2: "`N/A`로 적고 근거를 `도입 <Phase>: <사유>` 형식으로 쓴다". |
| R-09 | 닫힘 | history: "S1은 review22·23 두 라운드 0이었다(review21은 3건)". |
| R-10 | 닫힘 | EL3 행의 `\|`가 이스케이프됐다(셀 수 §5). |
| R-11 | 남음 | §7.1 "진입점은 최상위에서 … `exit_code_for`로 종료"와 §10.2-6 "진입점 호출 전체를 잡는다"가 그대로다. |
| R-12 | 대체로 소멸 | 상수가 없어졌다. 다만 gate **코드**를 어느 판으로 실행하는지는 이제 어디에도 적혀 있지 않다. |
| R-13 | 남음 | §10.2-4 "N6.3 '탐색 1회 wall-clock'은 `wall_clock_s`다"와 N6.3 "파일럿 탐색 1회의 **전체** wall-clock"이 여전히 다르다. |
| R-14 | 남음 | §6.3 '단계' 행의 "JSON 쪽 토큰만 쓴다"는 그대로다. |

---

## 2. 지정 점검 2: 새 §9

### (a) "base 판 계획서 읽기"와 "EL4 판정 표 diff 승인"의 정합성, 공격 16

* **기본 구조는 맞다.** 계획 EL4는 "판정에 쓰는 계획서 표 -- N4.1 `담당 Phase`, N4.2 `도입`, N6.1 `Phase` 열 -- 의 diff는 승인 기록 필수"라고 하고, 설계 §9 머리와 §9.1도 같다. 공격 16은 (i) 승인 없는 표 개정 → EL4 거부, (ii) 표가 깨진 base → merge gate가 판정하지 않고 거부, 오거부 0(승인이 있는 개정은 통과)이다. 설계 §9.1 "N4.3 공격 16 (ii)가 이것을 증명한다", §3.3의 "0.5 공격 16(표 파손 거부, 승인 없는 표 개정 거부)"과 맞는다.
* **빈칸**(Q-04, S2): 표 diff를 판정하려면 gate가 **head 판** 계획서도 파싱해야 한다. 그런데 §9.1은 "merge gate는 **base 판** 계획서를 읽는다"만 적었다.
  * head 판 표가 깨진 경우의 처리가 정해져 있지 않다.
  * 깨진 표가 한 번 병합되면 다음 병합부터 base가 깨진 상태다. 공격 16 (ii)에 따라 **모든 병합이 거부**되고, 표를 복구하는 병합도 거부된다(교착).
  * 'diff'의 기준도 정해져 있지 않다. 파싱 값(`v_intro`·`ic_parts`·`phase_order`)이 바뀐 것인지, 해당 열의 원문이 바뀐 것인지가 없다.
* **보호 범위 밖 열**(S3): §9.3 대조 test는 `ic_test`(N4.1 '강제 test' 열)도 입력으로 쓴다. 그러나 이 열은 EL4 보호 목록에 없다.
* 판이 갈리는 점(S3): gate는 base 판 `phase_order`로 spec card `Phase`를 검사하고, test(`--gmid-phase`)는 병합본 판으로 검사한다. 그래서 Phase를 새로 더하는 개정과 그 Phase를 쓰는 card는 한 병합에 넣을 수 없다(두 단계). 교착은 아니지만 §9.1에 적어 둘 만하다.

### (b) `read_plan_tables`를 §9.2만으로 구현할 수 있는가 -- 예(조건부)

§9.2 문장만 보고 독립 구현(`rpt.py`)을 만들어 현재 계획서(작업 트리, CRLF)에 돌렸다. **거부된 행은 없다.**

* `v_intro` = V1 `1`, V2 `1`, V3 `1`, V4 `1`, V5 `1`, V6 `1`, V7 `2`, V8 `4`, V9 `6b`, V10 `0.5`. V1의 괄호 안 "0.5는 redteam"은 토큰이 아니다(설계 주장과 같다).
* `ic_parts` = IC1 {6b}, IC2 {6b}, IC3 {1}, IC4 {6c}, IC5 {1}, IC6 {6c}, **IC7 {(6a, from_phase=True), (6c, sub=True)}**, IC8 {6c}, IC9 {6b}, IC10 {6b}, **IC11 {4, 6a}**. IC11의 괄호 안 `DEC-60`·`2레일`·`3레일`은 토큰이 아니다. 괄호 안 토큰은 IC7의 6c 하나뿐이다(§9.2-3 주장과 같다).
* `ic_test` = IC마다 `test_…` 함수 이름 하나씩, 11개 모두 뽑혔다.
* `phase_order` = `0.5, 1, 2, 3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c`. 빈 집합 행은 `0`과 `**0(문서)**` 정확히 둘이다(주장과 같다).
* N3.14(§9.3 CC-4용, §7.1 키 규칙)의 결과는 다음과 같다. 키가 두 번 나오는 STRUCTURE_UNRESOLVED는 두 행이 같은 값이다.

| 키 | 결과 |
|---|---|
| STRUCTURE_UNRESOLVED | (StructureUnresolvedError, 2) |
| `structure_inconsistent` | parent STRUCTURE_UNRESOLVED |
| `local_infeasible` | parent SEAL_VIOLATION |
| INFEASIBLE_TARGET | 3 |
| NONCONVERGENT | 4 |
| SEAL_VIOLATION | 5 |
| SEARCH_FAILED | 6 |
| SCHEMA_REJECTED | (SchemaRejectedError, 7) |

변형 입력(`mut_out.txt`)도 돌렸다. 모두 설계 뜻대로 거부했다.

| 변형 | 결과 |
|---|---|
| V8 `4, 5` | 거부 |
| V8 `(4)` | 거부(괄호 밖 빈 집합) |
| N4.1 행에 이스케이프 안 된 `\|` | 거부(6/5셀) |
| N6.1 빈 행 추가 | 거부(빈 행 3개) |
| `### N4.1 ` 중복 | 거부 |
| IC7 "6a부터" | 거부(`6a부` 뒤 글자 불허로 빈 집합) |

구현하면서 **정해야 했던 것**(S3, 구현자마다 갈린다):

1. **열 식별 규칙**이 없다. N4.1 머리는 `강제 test(\`tests/contracts/\`)`, N3.14 머리는 `예외(SCHEMA_REJECTED 외에는 …)`·`파이프라인 exit code(…)`다. 머리가 정확히 같아야 한다고 구현하면 거부된다. 이 검증 구현은 앞머리 일치로 했다.
2. `from_phase` = "칸에 그 토큰 **뒤** '이후 매 Phase'가 있는가": 바로 뒤인지, 칸 어딘가 뒤인지가 없다. 예: `4, 6a 이후 매 Phase`에서 4.
3. 줄 끝(CRLF) 처리와 base 판을 읽는 방법(`git show <base>:<path>` 대 worktree 파일)이 없다. autocrlf 체크아웃은 `w/crlf`, 인덱스는 `i/lf`다. §8.2는 `\r?\n`을 명시했지만 §9.2는 명시하지 않았다.
4. §9.3의 test(CC-3·CC-4)가 `merge_gate.read_plan_tables`를 import하는지, "같은 규칙"으로 다시 구현하는지 정해지지 않았다. 다시 구현하면 파서가 둘이 된다(WP-14).

### (c) §9.3 xfail 표식과 IC7·IC11

* **Q-02 (S1)**: 만료 시점이 계획과 모순이다.
  * §9.3은 "표식 Phase가 현재 Phase보다 **뒤면** xfail"이라고 한다. 그러면 표식 Phase = 현재 Phase인 test는 그 Phase의 **첫 card부터** 활성이다.
  * 계획 N3.12.3은 "XFAIL은 … 만료(그 Phase **DoD**)", N6.2 1행은 "IC3·IC5 PASS, 나머지 IC xfail 선언"이다. 두 문장 모두 만료를 Phase 끝으로 본다.
  * 결과: Phase 4 첫 card인 TS4(test 전용)의 V1("slow 포함 전체")에서 `test_rail_origin_shift_invariance`의 `"4"` 케이스(IC11 2레일)가 활성이 된다. 이 케이스는 DEC-60 구현 전이라 FAIL한다. 따라서 TS4 → DF-35 → … 순서가 성립하지 않는다.
  * 6a(IC7·IC11 3레일), 6b(IC1·2·9·10), 6c(IC4·6·8·IC7 정지)에서도 IC 구현 card 앞의 모든 card가 같은 방식으로 막힌다.
  * v1.4에서 새로 생긴 것은 아니다. 그러나 (c) 점검에서 처음 드러났고 승인을 막는다.
* **`from_phase`는 소비자가 없다**(S3, WP-01): §9.3 "`from_phase=True`인 Phase의 표식은 이후 Phase에서 xfail이 되지 않는다"는 규칙이 없어도 모든 표식에 대해 참이다. 비교식 "표식 Phase가 현재보다 뒤면 xfail" 때문이다. 그래서 IC7의 "6a 이후 매 Phase"를 기계가 따로 강제하는 곳이 없다. 이 필드를 쓰지 않는 구현과 쓰는 구현이 같은 결과를 낸다.
* **IC7**: 비교 대상 집합은 {6a, 6c}다. 정지 케이스에 `"6c"`, 나머지 케이스에 `"6a"`를 달면 만족한다(모호하지 않다). 6c 케이스는 6a·6b 동안 xfail이다. Q-02가 여기에도 적용된다: 6a 첫 card부터 `"6a"` 케이스가 활성이다.
* **IC11**: 비교 대상은 {4, 6a}이고, 2레일 `"4"`와 3레일 `"6a"`로 만족한다. **모호한 곳은 "거부 케이스(선행)"다**(S3).
  * N4.1 IC11은 "같은 test **파일**에서 먼저 증명한다"고 한다. 그러나 §9.3 대조는 `ic_test[IC]` **함수**의 표식만 본다. 거부 케이스를 별도 함수로 두면 대조 밖이 되고, 담당 Phase가 없다.
  * 이 거부는 GB0 로드 게이트(공격 13, "실행 Phase = 6a")에 기댄다. 표식이 없으면 Phase 4에서 FAIL한다. 같은 함수의 케이스로 두면 `"4"`와 `"6a"` 중 무엇을 달지 계획이 서로 어긋난다. IC11 칸은 "4(DEC-60 구현…)"이고 공격 13은 6a다.
* red 재수집·재현 명령(§8.1 "`$PY -m pytest --rootdir=… -p tools.gates.merge_gate …`")에 `--gmid-phase`가 없다(S3). CC-3 뒤에는 옵션이 없으면 수집 오류가 나므로 red 재현이 전부 수집 오류로 끝난다. base 실행에 줄 Phase 값(spec card `Phase`)을 명령에 적어야 한다.

### (d) 남은 옛 참조(V_CHECKS·PHASE_ORDER·IC_TABLE·ic_table.py·자기검사·일치 검사)

`grep` 결과는 다음과 같다. `V_CHECKS`·`IC_TABLE`·`ic_table.py`·`자기검사`는 설계와 계획에 남아 있지 않다. history는 경위 기록이라 대상에서 뺀다.

| 위치 | 문구 | 판정 |
|---|---|---|
| 계획 N6.1 머리 문단(897행) | "(`00-common` §9.3 `PHASE_ORDER`)" | **stale**. 이제 §9.2 `phase_order`다 |
| 계획 N9.1 `05-role-separation` 행(1055행) | "N6.1 전체(`PHASE_ORDER`)" | **stale** |
| 계획 N6.2 `0(문서)` 행(920행) | "V 도입 표·IC 담당 표의 **형식과 계획서 일치 test 명세**" | **stale**. 이 문서 자신의 DoD다(Q-05) |
| 계획 N9.1 `00-common` 행(1054행) | "V 도입 표(N4.2)·IC 담당 표(N4.1)의 형식과 계획서 일치 test 명세" | **stale** |
| 설계 §15 'V/IC 표' 행(555행) | "형식 + 일치 검사 명세" | **stale**. §9는 일치 검사가 아니라 직접 읽기다 |
| 설계 §2 표 '판정 표' 행(52행) | V 도입·IC 담당을 "코드 상수 하나 + 계획서 표와의 일치 검사"에 포함 | 바로 아래 정정 문단이 덮으므로 경미(S3). 표에 '정정 후' 표시가 없다 |
| 설계 §18.2 모듈 키 `common-ic-table` | 이름만 남음 | S3 |
| history Version History 5.19 행 | "review22 반영으로 N4.3 공격 16"(옛 자기검사 뜻) | 재정의가 반영되지 않음(S3). 머리 절 52행에는 적혀 있다 |

---

## 3. 지정 점검 3: pytest 9.0.2 수집 오류 실측

scratch `pt/`에서 실측했다.

* 준비: `conftest.py` 훅, `-p gatepkg.plug` 플러그인 훅, test 모듈 넷
  * `import nonexistent_module_xyz_12345`
  * `from existing_mod import NEW_SYMBOL`
  * 모듈 머리의 `existing_mod.NEW_ATTR`
  * 실행 단계 `assert 1 == 2`
* 명령: `python -m pytest --rootdir=. -p no:cacheprovider -p gatepkg.plug -q tests`

| 모듈 | `pytest_exception_interact` 호출 | `report` | `call.when` | `call.excinfo.type` | `__cause__` | `__cause__.name` |
|---|---|---|---|---|---|---|
| 없는 모듈 import | **예**(conftest·`-p` 둘 다) | `CollectReport` | `collect` | `_pytest.nodes.Collector.CollectError` | `builtins.ModuleNotFoundError` | `nonexistent_module_xyz_12345` |
| 없는 심볼 import | **예** | `CollectReport` | `collect` | `_pytest.nodes.Collector.CollectError` | `builtins.ImportError` | `existing_mod`(**모듈 이름**. 심볼은 3.12+ `name_from`=`NEW_SYMBOL`) |
| 모듈 머리 AttributeError | **예** | `CollectReport` | `collect` | `builtins.AttributeError`(감싸지 않음) | `None` | -- |

* node id는 모듈 경로다(`tests/test_missing_module.py`). `pytest_collectreport`의 `CollectReport` 속성은 `longrepr, nodeid, outcome, result, sections`이고 예외 타입 필드는 없다(review24와 같다).
* **새 사실 -- Q-03 (S2)**: 수집 오류가 하나라도 나면 "Interrupted: N errors during collection"으로 **세션 전체가 중단**된다. 그래서 `tests/test_ok.py::test_fail`(실행 단계 red)이 **실행되지 않았다**.
  * `run1.txt`: 3 errors, 0 failed
  * `run2.txt`: `test_missing_module.py`와 `test_ok.py::test_fail` 지정 → exit 2, 1 error만
  * `--continue-on-collection-errors`를 주면 1 failed + 1 error, exit 1(`run3.txt`)
  * 설계 §8.1의 red 수집·재현은 `red.test_ids`를 한 번에 실행한다. 여기에 수집 단계 red와 실행 단계 red가 섞이면 실행 단계 red의 해시가 기록되지도 재현되지도 않는다. 그러면 V2가 거짓 FAIL을 낸다(이번 병합의 red-green이 거부된다).
* 결론: §8.1의 `__cause__` 규칙과 '없으면 `excinfo.type`' 규칙은 실측과 맞는다. AttributeError는 감싸지지 않아 `excinfo.type`으로 잡힌다. 명령에 `--continue-on-collection-errors`를 넣어야 한다. '신규 심볼' 판정 입력도 정해야 한다. `ModuleNotFoundError.name`은 모듈 이름이고, 심볼은 `ImportError.name_from`이다(3.12+, 프로젝트 3.14에서 사용 가능).

---

## 4. 지정 점검 4: §8.2 blob 기반 diff 해시

`blobhash.py`로 실측했다. `HEAD~3`..`HEAD`, 경로는 계획서와 history다.

| git 설정 | 해시 |
|---|---|
| 기본 | `220942e6…3931` |
| `-c diff.suppressBlankEmpty=true` | `220942e6…3931` |
| `-c diff.context=7` | `220942e6…3931` |
| 둘 + `diff.noprefix=true` + `core.autocrlf=false` | `220942e6…3931` |

* **diff 설정과 무관함을 확인했다**(R-06 닫힘). 경로 순서를 바꿔도 같다(정렬).
* base에 없는 경로: `rev-parse --verify --quiet`는 exit 1, 출력이 없어 `-`가 된다. 추가된 파일(`review19_delta_d05_d12_d13.md`)은 `-\tcc3590b7…`로 정상 계산된다.
* **경계 입력**(S3): 모두 **거부 없이** 해시가 나온다.
  * 양쪽 모두 없는 경로: 추적되지 않는 이 design 문서가 `-\t-`가 된다.
  * 바뀌지 않은 경로: base = head.
  * 디렉터리 경로(`docs/01-plan/features`): **tree id**가 blob 자리에 들어간다.
  * `./` 접두 경로: 같은 blob인데 해시 입력 문자열이 달라 해시가 다르다.
  * 백슬래시 경로는 git에서 해석되지 않는다.
  * 수정: 적어도 한쪽이 blob(`^{blob}` 또는 `cat-file -t`)이고 base ≠ head여야 한다. 경로는 저장소 루트 기준 POSIX로 정규화한다고 §8.2에 적는다.
* 참고: 이 design 문서는 아직 추적되지 않는다. §16 승인 기록을 만들려면 먼저 커밋해야 한다. 그러지 않으면 `-\t-`가 되어 아무것도 덮지 않는 승인이 된다.

---

## 5. 지정 점검 5: 표 셀 수

`cells.py`로 셌다. 이스케이프되지 않은 `|` 기준이고 코드 블록은 뺐다.

| 파일 | 표 | 파손 행 |
|---|---|---|
| 설계 v1.4 | 16 | **0** |
| 계획 v5.19 | 42 | **0**(review24의 EL3 616행·U-04 985행 파손은 해소됐다) |
| history | 115 | 8. 모두 이번 diff 밖의 기존 행이다: 3786·3800·3806·5285, Version History 4.8·4.11·4.13·4.36(5510·5513·5515·5538). 이번 diff가 더한 행(229 U-38, 5572 v5.19)은 정상이다 |

---

## 6. 새 결함

### S1

#### Q-01 (S1) Phase 4 순서에서 CC-7·CC-8이 CC-4보다 앞이라 두 도구의 규정과 oracle이 성립하지 않는다
* **위치**:
  * 순서: §11.1과 §18.1 "TS4 → DF-35 → DF-36 → CC-7·CC-8 → CC-4·CC-5와 나머지 DF", 계획 N6.1 4행
  * 의존: §10.2-6, §11.4, §14 CC-7·CC-8 oracle
* **근거**: CC-7과 CC-8은 다음 규정에 기댄다. 그런데 기대는 것들이 모두 CC-4(§13: "N3.14 예외 계층, `FAILURE_CLASSES`, …, `exit_code_for` | MOD4 | 4", §14 CC-4 "DF-37 광범위 except 재raise, 진입점 exit code")에서 생긴다.
  * §10.2-6: "`failure_class` = `FAILURE_CLASSES`에서 찾은 분류 이름 … 도구는 `exit_code_for(exc)`로 끝난다"
  * CC-7 oracle: "탐색이 예외를 내게 한 입력 → `status=failed`·파일 존재·그 예외의 exit code"
  * §11.4: "두 `FailureRecord.to_json()`의 정규화 해시"
  * 그 전까지 하네스 `run()`은 모든 예외를 삼키고 0으로 끝난다(DF-37, §7.1). 그래서 도구 자식 프로세스에는 예외가 도달하지도 않는다.
* **영향**: CC-7 red의 green을 만들 수 없다. 방법은 셋뿐이다. 구현자가 CC-4 범위를 앞당기거나(범위 위반), 도구 안에 임시 분류를 만들거나(사본), oracle을 건너뛰는 것이다(WP-02). R-01을 고치면서 생긴 순서 결함이다.
* **수정**: Phase 4 순서를 TS4 → DF-35 → DF-36 → **CC-4(적어도 §7.1 형식·`exit_code_for`·하네스 `run()` 삼킴 제거)** → CC-7·CC-8 → 나머지로 바꾼다. 또는 CC-7·CC-8 도구의 예외 경로 규정과 oracle을 CC-4 뒤 card로 떼어 낸다. 계획 N6.1 4행과 §11.1의 '그 앞 card' 목록도 함께 고친다.

#### Q-02 (S1) xfail이 '표식 Phase = 현재 Phase'에서 이미 풀려, 그 Phase의 IC 구현 card 앞 card들이 V1에서 막힌다
* **위치**: §9.3 "표식 Phase가 현재 Phase보다 뒤면 xfail", reason "만료: `<phase>` DoD". 계획 N3.12.3 "만료(그 Phase DoD)", N4.2 V1 "전체 test 실행".
* **근거와 영향**: §2(c)와 같다. Phase 4 첫 card TS4가 IC11 `"4"` 케이스 FAIL로 V1을 통과하지 못한다. 6a·6b·6c도 마찬가지다. 문구(만료 = DoD)와 기계 규칙(만료 = Phase 시작)이 어긋난다.
* **수정**: xfail 조건을 "표식 Phase ≥ 현재 Phase"(non-strict. 구현 card 뒤에는 XPASS 허용)로 바꾼다. DoD 판정 실행에만 "표식 Phase = 현재 Phase 케이스는 xfail 없음"(예: `--gmid-dod`)을 둔다. 이렇게 해야 만료가 DoD와 맞는다. 구현 card의 red(base FAIL)는 `pytest_runtest_makereport`가 xfail 케이스의 `call.excinfo`도 받으므로 그대로 잡힌다.

### S2

#### Q-03 (S2) 수집 단계 red가 섞이면 pytest가 세션을 중단해 실행 단계 red가 기록·재현되지 않는다
* **위치**: §8.1 red 수집. 실측은 §3.
* **수정**: red 수집과 재현 명령에 `--continue-on-collection-errors`를 명시한다. '신규 심볼' 판정 입력(`ModuleNotFoundError.name` / `ImportError.name_from`과 interface card 신규 모듈·심볼 목록의 대조)을 적는다(R-02 잔여).

#### Q-04 (S2) EL4 판정 표 diff 검사가 head 판 파싱을 요구하는데 규정이 없고, 깨진 표가 병합되면 교착이 생긴다
* **위치**: §9.1 "merge gate는 **base 판** 계획서를 읽는다", "거부: 표를 못 읽으면 … 거부", 계획 EL4, 공격 16.
* **수정**:
  * "EL4는 base·head 두 판을 모두 `read_plan_tables`로 읽는다. head 판을 못 읽으면 거부한다(깨진 표는 병합되지 않는다)"를 적는다.
  * 'diff'는 파싱 값(`v_intro`, `ic_parts`, `ic_test`, `phase_order`)의 차이로 정의한다. '강제 test' 열(`ic_test`)도 보호 목록에 넣는다.
  * 공격 16에 (iii) "head 판 표 파손 → 거부"를 더한다.

#### Q-05 (S2) 이 문서 자신의 DoD(계획 N6.2 `0(문서)`)와 N9.1 행이 없어진 '일치 test 명세'를 요구한다
* **위치**: 계획 N6.2 `0(문서)` "V 도입 표·IC 담당 표의 **형식과 계획서 일치 test 명세**", N9.1 `00-common` 행 같은 문구, 설계 §15 'V/IC 표' "형식 + 일치 검사 명세"
* **근거**: v1.4 §9는 일치 검사가 아니라 직접 읽기다. DoD 문구대로 판정하면 해당 항목이 없어 FAIL이거나, 판정자가 해석해야 한다.
* 같은 부류: N6.1 머리의 "`00-common` §9.3 `PHASE_ORDER`", N9.1 `05` 행 "N6.1 전체(`PHASE_ORDER`)".
* **수정**: 다섯 곳을 "판정 표 직접 읽기 규칙(§9)과 EL4 판정 표 diff 승인"으로 바꾼다.

### S3

* **Q-06** `from_phase`는 소비자가 없는 필드다(§2(c)). 지우거나 실제 규칙(예: `from_phase` IC는 이후 모든 Phase의 DoD에서 PASS 필수)을 준다.
* **Q-07** IC11 '거부 케이스(선행)'의 담당 Phase와 표식이 정해지지 않았다. IC11 칸은 4이고 공격 13은 6a다. 함수 단위 대조의 범위 밖이기도 하다.
* **Q-08** §9.2 열 식별 규칙, `from_phase` 인접성, 줄 끝·base 판 읽는 방법, test 쪽 파서 재사용 여부가 정해지지 않았다(§2(b) 1~4).
* **Q-09** §8.1 red 수집·재현 명령에 `--gmid-phase <spec card Phase>`가 빠졌다(CC-3 뒤에는 수집 오류가 난다).
* **Q-10** §8.2 diff 해시가 없는 경로, 바뀌지 않은 경로, 디렉터리(tree id), 정규화되지 않은 경로를 거부하지 않는다(§4).
* **Q-11** 설계 §2 표 52행에 '정정 전' 표시가 없다. §18.2 `common-ic-table` 이름, history Version History 5.19 행의 공격 16 옛 뜻(§2(d)).
* **Q-12** gate **코드**의 실행 판(base인가 head인가)이 v1.4에서 빠졌다(옛 §9.4 삭제). 판정 기록 스키마는 "base의 스키마로 검증"(§8.1 변경 주체 문단)인데, 코드는 명시가 없다.
* 남은 review24 S3: R-11, R-13, R-14(§1 표).

---

## 7. 지정 점검 6: §17 "열린 질문 없음"

**성립하지 않는다.** 아래는 넘긴 곳이 없는 설계 결정이다. 어느 발행 문서의 착수 범위에도 들어가 있지 않다.

* Q-01: Phase 4 안의 CC-4 대 CC-7·8 순서
* Q-02: xfail 만료를 DoD와 맞추는 방법
* Q-04: head 판 파싱과 파손 처리, 'diff'의 정의
* Q-03: '신규 심볼' 판정 입력

§17 표의 다른 항목(S1·S2 필드 이름, `qualifier`, raise 지점 분류, MOD6/MOD8, EL1 glob·EL3 조합표·U-38 파일, spec card 분할)은 넘길 곳이 적혀 있다. 그 가운데 `30-module-split`에 넘긴 'MOD6 대 MOD8'은 계획 N9.1 `30` 행에 명시돼 있지 않다. 이관표 생성 항목에 암묵적으로 포함된다고 볼 수 있다(S3 수준).

---

## 8. 집계와 판정

| 구분 | 건수 | ID |
|---|---|---|
| 닫힘 | 4 | R-01, R-03, R-04, R-05 |
| 부분 | 1 | R-02 |
| 안 닫힘 | 0 | -- |
| 새 S1 | 2 | Q-01(Phase 4 순서: CC-7·8이 CC-4의 `FAILURE_CLASSES`·`exit_code_for`·`FailureRecord`·DF-37보다 앞), Q-02(xfail이 Phase 시작에 풀려 IC 구현 전 card가 V1에서 막힘, 계획 "만료 = DoD"와 모순) |
| 새 S2 | 3 | Q-03(수집 오류가 세션을 중단해 실행 단계 red 소실 -- `--continue-on-collection-errors` 필요, 실측), Q-04(EL4 표 diff에 head 판 파싱·파손 거부 규정 없음 → 깨진 표 병합 시 교착), Q-05(DoD·N9.1·N6.1·§15에 '일치 test 명세'·`PHASE_ORDER` 옛 참조) |
| 새 S3 | 7 | Q-06 ~ Q-12(+ review24 잔여 R-11·R-13·R-14) |

§9의 방향은 맞다. 사본을 없애고 검증 도구가 계획서를 직접 읽으며, 표 개정에는 승인 기록을 요구한다. `read_plan_tables`도 §9.2 문장만으로 독립 구현할 수 있었고 현재 계획서에서 거부 없이 설계 주장과 같은 값이 나왔다. blob 해시는 diff 설정과 무관하다.

**판정: 수정 후 승인.** Q-01은 Phase 4 순서 한 줄(CC-4 앞당김)로 닫힌다. Q-02는 xfail 조건 한 줄과 DoD 실행 옵션 하나로 닫힌다. Q-03~Q-05는 명령 옵션 하나, §9.1 두 문장, 옛 참조 다섯 곳 치환이다. 재작성은 필요 없다.
