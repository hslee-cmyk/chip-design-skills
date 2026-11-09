# DF-36 사전 조사 (instance.json `topology_ref` 절대 경로 -> 저장소 루트 상대 경로)

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, 기준 HEAD = master `c4e5fef`. 읽기 전용(저장소 쓰기·git 변경 없음).
DF-35 병합 전이다: `role/code/20260930-df35-harness-paths`(57781a7)·`role/test/...`(284cb1f)에만 DF-35 변경이 있다.

---

## 1. `topology_ref`를 만드는 줄과 값의 출처

명령: `sed -n 8940,9018p R/skills/analog-gmid-design/assets/stick_diagram.py`, `grep -n "topo\|instance" R/workspaces/run_harness.py`

- 정의: `stick_diagram.py:8967` `def save_instance_json(path: str, topology_json_path: str, sizing_results: dict, pipeline_result: dict) -> None:` (파일 총 9018줄)
- 생성 줄: `stick_diagram.py:8984` `"topology_ref": topology_json_path,` -- 인자를 **가공 없이** 그대로 쓴다.
- **같은 인자를 파일 열기에도 쓴다**: `stick_diagram.py:9006` `_device_names = [t.name for t in load_topology(topology_json_path)[0]]` (IC3 완전성 재검증, 9017 `with open(path, "w", ...)` 전에). => 수정은 "저장 값만" 상대화해야 하고, `load_topology`에는 원래 (열 수 있는) 경로를 계속 넘겨야 한다. 인자 자체를 상대 경로로 바꿔 받게 하면 cwd 의존이 생긴다.
- 최상위 키 단일 정의: `stick_diagram.py:8423` `INSTANCE_TOP_FIELDS = ("schema_version", "topology_ref", "sizing", "netlist", "floorplan", "box_shape", "audit_row_split", "coverage")` (키 이름은 바뀌지 않음).
- 운영 호출자 `R/workspaces/run_harness.py`(master):
  - 35행 `sys.path.insert(0, r"C:\Users\HSLEE\...\assets")`, 42행 `ASSETS_DIR = r"C:\...\assets"`, 43행 `LIBRARY_DIR = os.path.join(ASSETS_DIR, "library")`, 44행 `WORKSPACES_DIR = r"C:\...\workspaces"`
  - 426행 `topo = os.path.join(LIBRARY_DIR, cfg["topology_file"])` -> 절대 경로(역슬래시)
  - 491행 `save_instance_json(instance_out, topo, result["sizing"], result["pipeline_result"])`
  - DF-35 브랜치(`git show role/code/20260930-df35-harness-paths:workspaces/run_harness.py`): 35행 `WORKSPACES_DIR = os.path.dirname(os.path.abspath(__file__))`, 36행 `_REPO_ROOT = os.path.dirname(WORKSPACES_DIR)`, 37행 `ASSETS_DIR = os.path.join(_REPO_ROOT, "skills", "analog-gmid-design", "assets")`, 45행 `LIBRARY_DIR`, 427행 `topo = ...`. DF-35 후에도 `topo`는 **해당 체크아웃의 절대 경로**라 DF-36 문제는 그대로 남는다(DF-35 card 26행이 이를 명시).
- 기타 `save_instance_json` 호출자(`grep -rn "save_instance_json(" --include=*.py`, .claude/ 제외):
  | 호출자 | 넘기는 topology 경로 | 비고 |
  |---|---|---|
  | `workspaces/run_harness.py:491` | `LIBRARY_DIR` 절대 경로 | 운영 경로 |
  | `tests/contracts/test_ic3.py:207,218,226` | `str(_LIBRARY_DIR / "two_stage_ota.topology.json")` (저장소 안) | out은 `tmp_path`(저장소 밖) |
  | `tests/unit/test_selftest_stick_diagram.py:2093,2100` (test_s088) | `os.path.join(library_dir, "folded_cascode.topology.json")` (저장소 안) | out은 TemporaryDirectory, `topology_ref` 값은 판정 안 함 |
  | `workspaces/current-reuse-telescopic-ota-report/stick.py:368` | `"skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json"` (**cwd 상대**, 이미 저장소-루트 상대 모양) | 추적 파일, test가 실행하지 않음 |
  | `workspaces/two-stage-ota-report/check_box_shape.py:110`, `check_box_shape_M5M7split.py:101` | `tempfile.gettempdir()` 아래 임시 topology (**저장소 밖**) | 추적 파일, test가 실행하지 않음 |
  | `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session20.py:102`, `smoke_run_harness_session18_save.py:74`(미추적) | Temp 아래 (저장소 밖) | 옛 스모크 |

## 2. `topology_ref`를 읽는 코드 전수

명령: Grep `topology_ref` (`*.py`, R 전체), `git grep -n topology_ref -- ':!*.instance.json' ':!*.py'`

| 위치 | 하는 일 | 상대 경로로 바뀌면 |
|---|---|---|
| `stick_diagram.py:8423` `INSTANCE_TOP_FIELDS` | 키 이름 목록 | 영향 없음 |
| `stick_diagram.py:8446` (docstring) | "load_topology(topology_ref)" 설명 문장 | 영향 없음(문장). 실제 코드는 9006에서 인자를 연다 |
| `stick_diagram.py:8984` | 쓰기 | 수정 대상 |
| `tests/contracts/test_ic3.py:40` `_EXPECTED_TOP`, `:80` 손 instance `"topology_ref": "hand/made.topology.json"`, `:131` 키 삭제 반복 | 키 **존재**만 판정, 값은 안 봄 | 깨지지 않음 |
| `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/measure_ic_inputs.py:23,69,71` | `os.path.basename(d["topology_ref"])`로 library 파일 이름만 뽑아 `ROOT/skills/.../library/`에서 연다 | 깨지지 않음(`ntpath.basename`은 `/`·`\` 둘 다 처리). 옛 분석 도구 |
| `.ai/verification/20260930-restore-plan-functions/scripts/make_record.py:44` | 문장(“E-INST 해시가 복제본 경로에 기댄다”) | 영향 없음 |
| `workspaces/current-reuse-telescopic-ota-report/build_html.py:588` | HTML 문구 안 키 이름 | 영향 없음 |

- **`topology_ref` 값을 열어서 쓰는 코드는 저장소 안에 없다.** 엔진·하네스·probes·tools 어디도 instance.json을 다시 읽어 `topology_ref`로 topology를 로드하지 않는다(.ai/context.md 1920행 세션18 기록: "topology_ref에 경로 문자열만 저장하고(재로드 안 함)").
- 참고: `design_report.assemble_report_data(topology_json_path, instance_json_path, ...)`(design_report.py:93)는 topology 경로를 **따로 인자로** 받고 `topology_ref`는 읽지 않는다(`os.path.basename(topology_json_path)`를 제목에 씀).
- instance.json을 읽는 test/probe(`topology_ref`는 안 읽음): `tests/contracts/test_ts6_dead_probes.py:62`(current_reuse instance의 `sizing` 키만), `tests/contracts/test_ts6_probe_relocate.py:111`(경로 문자열), `tests/probes/probe_diode_min_vgs.py:31,35`(`["sizing"]`만).
- 설계 문서의 기존 표기(충돌 주의):
  - `docs/02-design/features/analog-topology-json-library.design.md:143` 예시 `"topology_ref": "library/folded_cascode.topology.json"` -- **assets 기준** 상대 경로 모양. 계획 DF-36의 "저장소 루트 기준"과 다르다. card에서 어느 쪽인지 명시하고 이 예시 문장의 처리(갱신 여부)를 적어야 한다.
  - `docs/01-plan/features/gain-budget-gmid-sizing.history.md:821` 예시 `"topology_ref": "current_reuse_telescopic_ota.topology.json"`(이름만) -- 이력 문서라 수정 대상 아님.

## 3. 추적된 `*.instance.json` 전수와 `topology_ref` 값

명령: `git -C R ls-files '*instance.json'` + python 한 줄(`json.load(...)['topology_ref']`), `git log -1 -- <f>`

| 파일 | topology_ref | 마지막 커밋 |
|---|---|---|
| `workspaces/current-reuse-telescopic-ota-report/current_reuse_telescopic_ota.instance.json` | `C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library\current_reuse_telescopic_ota.topology.json` | a1df744 2026-09-10 |
| `workspaces/folded-cascode-report/folded_cascode.instance.json` | `C:\...\chip-design-skills\skills\analog-gmid-design\assets\library\folded_cascode.topology.json` | 41f95e5 2026-08-15 |
| `workspaces/nmcnr-amplifier-report/nmcnr_amplifier.instance.json` | `C:\...\library\nmcnr_amplifier.topology.json` | b864239 2026-08-19 |
| `workspaces/two-stage-ota-report/two_stage_ota.instance.json` | `C:\...\library\two_stage_ota.topology.json` | b864239 2026-08-19 |
| `workspaces/two-stage-ota-report/two_stage_ota.PROVISIONAL_gain51.instance.json` | `C:\Users\HSLEE\AppData\Local\Temp\two_stage_ota_boxshape_check.topology.json` (저장소 밖) | 29da7ef 2026-08-13 |
| `workspaces/two-stage-ota-report/two_stage_ota.PROVISIONAL_gain51_M5M7split.instance.json` | `C:\Users\HSLEE\AppData\Local\Temp\two_stage_ota_boxshape_M5M7split.topology.json` (저장소 밖) | 29da7ef 2026-08-13 |

- 6개 파일 모든 문자열 값을 훑어(python, `\`·`Users`·`HSLEE`·`:/` 포함 여부) **경로가 들어간 문자열은 `topology_ref` 하나뿐**임을 확인했다(6/6 `['/topology_ref']`). 즉 DF-36만 고치면 00-common design §11.4 "경로 누출 검사"를 instance.json이 통과할 수 있다(단, `scope_note` 같은 선택 키에 경로가 새로 들어오지 않는 한).
- test·probe 입력 사용: `current_reuse_telescopic_ota.instance.json`만 쓰인다(test_ts6_dead_probes `sizing` 키, probe_diode_min_vgs `sizing`). 둘 다 `topology_ref`를 안 읽는다. 나머지 5개는 test 입력 아님. `measure_ic_inputs.py`(docs/03-analysis)가 `workspaces/*/*.instance.json` 전부를 읽지만 basename만 쓴다(PROVISIONAL 2개는 "library 파일이 아니다"로 skip -- `ic_inputs.json:240,243`).
- 추측: 추적 파일 6개는 DF-36 card가 재생성하지 않으면 옛 절대 경로를 그대로 가진다. 계획은 "산출물 재생성"을 요구하지 않는다(DF-36 행). 재생성 여부는 card 범위 결정 사항(재생성 시 LUT·엔진 실행이 필요하고 sizing 값이 바뀔 수 있어 범위가 커진다).

## 4. 기존 계약 test 중 instance.json 필드·topology_ref 판정

명령: Grep `topology_ref|instance` in `tests/contracts/`

- `test_ic3.py`(IC3, `@pytest.mark.gmid_ic("IC3", phase="1", case="")`, `test_coverage_and_field_completeness`):
  - 40행 `_EXPECTED_TOP` = `INSTANCE_TOP_FIELDS`와 튜플 동일 판정 -> 키 이름 유지면 영향 없음.
  - 131행 `topology_ref` 키 삭제 시 `missing_top == ("topology_ref",)` -> 영향 없음.
  - 3-c(224~235행) 저장본을 다시 읽어 키 순서·sizing·netlist·coverage 판정 -> **`topology_ref` 값은 판정 안 함**. topology는 저장소 안 library, out은 `tmp_path`(저장소 밖) -> "저장소 루트 기준" 계산이 out 위치에 기대지 않으면 영향 없음. 만약 구현이 **instance 파일 위치 기준** 상대 경로를 쓰면 tmp_path와 드라이브·깊이가 달라 `..` 사슬이 된다(아래 6 참고) -- 계획대로 저장소 루트 기준이면 문제 없다.
- `tests/unit/test_selftest_stick_diagram.py` test_s088(2079행): 저장 성공·ValueError만 판정, `topology_ref` 값 미판정.
- `test_ts6_dead_probes.py:62,310`: current_reuse instance의 `sizing`에 `vsb` 판정. `topology_ref` 무관.
- `test_ts6_probe_relocate.py:461,465`: probes 소스의 하드코딩 절대 경로 검출 합성 입력(`x.instance.json` 문자열) -- 무관.
- 결론: 상대 경로로 바꿔도 **조정이 필요한 기존 계약 test는 없다**(V5 승인 경로 불필요로 보임). `topology_ref` 값을 판정하는 test는 현재 0개 -> 새 test가 필요.

## 5. 계획서 문장

명령: `grep -n "DF-36\|topology_ref\|instance\.json\|CC-8" R/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, 관련 design grep

- plan.md:946 `| DF-36 | instance.json이 topology_ref에 topology의 **절대 경로**를 쓴다. worktree마다 산출물이 달라져 무동작 판정의 비트 동일 비교가 가짜 FAIL을 낸다 | stick_diagram.py:save_instance_json | 4(CC-8보다 먼저) | 저장소 루트 기준 상대 경로 |`
- plan.md:1001 Phase 4 순서: `TS4 → DF-35 → DF-36 → 00-common CC-4의 앞부분(...) → CC-7·CC-8 → 나머지`.
- plan.md:821 IC3 행(“instance.json 소자·필수 필드 누락 0”), plan.md:529 MOD9 `instance_report_builder.py`(`save_instance_json` 계열 재사용), plan.md:807 "옛 키로 저장된 워크스페이스 산출물(instance.json, 보고서)은 재생성하거나 로드 게이트가 거부한다".
- 00-common design(`docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md`):
  - 467·607행: Phase 4 순서 TS4 → DF-35 → DF-36 → CC-4 앞부분 → CC-7·CC-8.
  - 558행 CC-8: "`activations_out` 인자 + 무동작 판정 도구(§11). DF-35·36·CC-4 앞부분 뒤".
  - **490행 §11.4 경로 누출 검사**: "산출물을 JSON으로 파싱해 모든 문자열 값을 훑고, `os.path.normcase(os.path.normpath(x))`가 `<worktree>` 루트나 `output_dir`의 같은 정규화 값으로 시작하거나 그것을 포함하면 FAIL(`tool_noop_fail`, detail "경로 누출" -- DF-36 위반. 치환해서 넘기지 않는다)." -> DF-36의 사실상 합격 기준. 비교 대상은 `*.instance.json`, `*.structure.json`(488행).
- 분석 문서: review22:204·review23:252(“8966행 topology_ref: topology_json_path, 호출자는 LIBRARY_DIR 절대 경로” -- 지금은 **8984행**, 줄 번호 이동), review24:40("DF-36은 §11.4 경로 누출 검사에서 FAIL").
- DF-35 card(`docs/02-design/specs/20260930-df35-harness-paths.spec.md:26`): "DF-36 전까지 instance.json의 topology_ref는 절대 경로라 경로별로 다르다".
- .ai/verification/20260930-restore-plan-functions/base_check.json:124: "instance.json topology_ref에 복제본 경로가 들어가 해시가 경로에 기댄다('g13'->'g12' 치환 시 P8 base 값과 정확히 같음)" -- 현 E-INST 도구(`.ai/verification/*/scripts/e_inst.py`)가 이 문제를 치환으로 우회해 왔다.

## 6. 엔진이 "저장소 루트"를 아는 방법, 구분자 정책

명령: `grep -n "__file__\|REPO_ROOT" R/skills/analog-gmid-design/assets/*.py`, Grep `_REPO_ROOT =` in tests

- 엔진 모듈에 저장소 루트를 유도하는 **기존 함수·상수는 없다**. 선례:
  - `stick_diagram.py:1050` `_import_analog_grammar`: `os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "analog-grammar", "assets"))` -- 같은 모듈이 이미 `__file__` 기준 상대 위치를 쓴다(skills 디렉터리까지 `../..`).
  - `audit_current_forced.py:169` `os.path.join(os.path.dirname(os.path.abspath(__file__)), "library")`.
  - tests: `conftest.py:36` `_REPO_ROOT = os.path.abspath(os.path.join(_TESTS_DIR, "..", "..", "..", ".."))`, contracts 다수 `_REPO_ROOT = _ASSETS_DIR.parents[2]`(test_d_move_tests:49 등 9곳), `test_ic5.py:28`·`tooling/test_extract_selftest.py:25` `parents[5]`.
  - DF-35(미병합): `run_harness.py` `_REPO_ROOT = os.path.dirname(WORKSPACES_DIR)`.
- 제안(추측 포함): 엔진 쪽은 `stick_diagram.py` 위치에서 유도 -- `assets = dirname(abspath(__file__))`, 저장소 루트 = `assets/../../..`(= `Path(__file__).resolve().parents[3]`). 하네스에서 루트를 인자로 받는 방식도 가능하나 시그니처 변경(`save_instance_json` 호출자 7곳)이 생긴다. 엔진 유도가 변경 최소.
  - 주의: worktree(`R/.claude/worktrees/...`)에서 돌면 그 worktree의 `stick_diagram.py` 기준 루트가 나와 DF-35 후 하네스의 `LIBRARY_DIR`(같은 worktree)와 일치 -> 두 체크아웃에서 같은 문자열이 된다(의도한 효과).
- 구분자·형식 정책 제안:
  - 값 = `os.path.relpath(os.path.abspath(topology_json_path), repo_root)`를 `/`로 바꾼 것(`pathlib.PurePath(...).as_posix()` 또는 `.replace(os.sep, "/")`). 예: `skills/analog-gmid-design/assets/library/two_stage_ota.topology.json`.
  - 00-common design 342행(spec card 머리 `diff_path`)의 "정규화된 저장소 상대 경로(`./`·`..`·역슬래시·끝 `/` 거부)" 규칙과 같은 모양으로 맞추면 일관적이다.
  - 대소문자: Windows `ntpath.relpath`는 비교만 normcase로 하고 출력은 입력 대소문자를 유지한다 -- 추측: library 경로는 코드가 조립하므로 문제 없음.
- **저장소 밖 topology 처리(결정 필요)**: 실측 `os.path.relpath(r'C:\Users\HSLEE\AppData\Local\Temp\x.json', R)` -> `..\..\..\..\AppData\Local\Temp\x.json`. 다른 드라이브면 `ValueError`(ntpath 동작, 실측 아님). 이 경우의 정책을 card가 정해야 한다. 후보: (가) 거부(`ValueError`, 파일 안 씀) -- `check_box_shape*.py`·smoke 스크립트(추적, test 미실행)가 저장소 밖 임시 topology를 넘기므로 이들이 깨진다; (나) 저장소 밖이면 절대 경로 유지 -- §11.4 누출 검사는 `<worktree>` 루트 접두만 보므로 통과하지만 결정론은 보장 안 됨; (다) `..` 사슬 허용 -- 342행 규칙과 어긋남. 원칙상 (가)가 "조용한 우회 금지"에 가깝고, 운영 경로(run_harness)와 test(test_ic3·s088)는 전부 저장소 안 library라 영향 없음. 깨지는 옛 스크립트 처리(방치/수정)를 card에 명시 권장.
- E-INST 영향: DF-36 병합 시 instance.json 바이트가 `topology_ref` 한 필드에서 base와 달라진다(의도된 변경). 이 card의 증거 유형은 `red-green`이 자연스럽고, E-INST 비교는 "topology_ref 제외 동일 + 병합본 topology_ref가 두 경로(메인·audit 복제본)에서 같은 문자열"로 적어야 한다(추측: auditor 절차 제안).

## 7. 새 test 파일 이름 `test_df36_instance_relpath.py` 충돌 확인

명령: `grep -rn "glob(" R/skills/analog-gmid-design/assets/tests --include=*.py`

- 이름 패턴을 거는 glob: `probe_*.py`(test_ts6_dead_probes:80·85, test_ts6_probe_relocate:320~449, `_COLLECTED_NAME_RE`), `*.topology.json`(test_ic3:49), `*.md`(engine_dup_scan:107) -> `test_df36_instance_relpath.py`와 **겹치지 않음**.
- 이름 무관하게 tests 트리 전체 `*.py`를 **내용 스캔**하는 test(새 파일도 대상이 됨 -- 내용 제약 주의):
  - `test_d_delete_dead.py:87`, `test_d_delete_telescopic.py:97`, `test_d_move_tests.py:87`: 삭제된 이름(AST Name/Attribute/문자열 상수) 참조 금지.
  - `test_ts3_no_print_verdicts.py:59`: `print`/`logging` 인자에 PASS/FAIL 토큰 금지.
  - `test_ic_markers_match_plan.py:91`: `contracts/*.py`의 `gmid_ic` 표식 phase가 계획 N4.1과 일치해야 함 -> 새 파일에 `gmid_ic` 표식을 달지 않으면 무관(추측: DF card는 IC 표식 불필요).
  - `test_probe_dup_scan.py:438`: probes 디렉터리만.
- 선례 이름: DF-35 test 브랜치가 `tests/contracts/test_df35_harness_paths.py`(255줄)를 추가했다 -> `test_df36_instance_relpath.py`는 같은 규칙.
- pytest 설정 파일(pytest.ini 등)은 저장소에 없음(`git ls-files`에 redteam 입력 JSON만) -> 기본 수집 `test_*.py`로 수집된다.

---

## spec card 계약 초안 (관찰 가능한 계약, 제안)

1. **상대 경로 저장**: 저장소 안 topology 경로(절대·상대 어느 표기든)를 `save_instance_json`에 넘기면 저장된 `topology_ref`는 저장소 루트 기준 상대 경로로, `/` 구분자만 쓰고 역슬래시·드라이브 문자·선행 `/`·`./`·`..` 구성요소가 없다. 예: library의 `two_stage_ota.topology.json` -> `"skills/analog-gmid-design/assets/library/two_stage_ota.topology.json"`. (oracle (a): 구성 입력의 저장소 상대 위치가 곧 기대값)
2. **체크아웃 무관(무동작 판정 전제)**: 같은 입력으로 서로 다른 체크아웃(메인·worktree/복제본)에서 저장한 두 instance.json은 `topology_ref`가 같은 문자열이고, 정규화(키 정렬) 해시가 같다. 저장된 모든 문자열 값에 체크아웃 루트·출력 디렉터리의 정규화 경로가 접두·포함되지 않는다(00-common §11.4 경로 누출 검사와 같은 식).
3. **저장 위치 무관**: 출력 파일 `path`가 저장소 밖(`tmp_path`)이어도 `topology_ref`는 계약 1과 같다(instance 파일 위치 기준이 아니다).
4. **로드는 원래 경로로**: 호출 cwd를 저장소 루트가 아닌 곳으로 바꿔도 저장·IC3 완전성 재검증이 성공하고(파일이 생긴다), 결핍 입력은 지금처럼 `ValueError` + 파일 없음(test_ic3 3-a·3-b 동작 보존).
5. **저장소 밖 topology**(정책 결정 후 확정): 예 (가)안이면 저장소 루트 밖 topology 경로를 넘기면 `ValueError`, 파일 없음, 메시지에 경로 포함. (나)안이면 해당 조항을 "절대 경로 유지"로.
6. **나머지 필드 불변**: `topology_ref`를 뺀 instance.json 내용(키 순서 `INSTANCE_TOP_FIELDS`, sizing·netlist·floorplan·box_shape·audit_row_split·coverage·scope_note)은 base와 바이트 동일(E-INST: 4회로 run_harness 산출물에서 `topology_ref` 제외 정규화 해시 base==병합본).

범위 밖(명시 권장): 추적된 옛 instance.json 6개 재생성, `analog-topology-json-library.design.md:143` 예시(assets 기준 `library/...`) 정정 여부, `check_box_shape*.py`·smoke 스크립트 수정.
