---
id: 20260930-p3-move-plan-tool
phase: 3
evidence_type: red-green
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split`(초안 v2) §6.3, card D0a. 계획 N3.10 517행 "Phase 3 design 문서가 그 열(레지스트리 '이관 목적지')에서 이관표와 실제 의존 그래프를 생성한다"와
N9.1 `30-module-split` 행("이관표, 계산된 import 그래프, `import_layering.py` 규칙, AST 해시 증명 명령, shim 재수출 목록 생성법")을 **손이 아니라 도구로** 만든다.
실측(design v2 §6.1): 열이 N3.10 이전 판 이름을 쓰고(MOD 이름 없는 셀 62, MOD1·5·6 행 0), 쪼개라는 셀이 16행이며, 초안 배정만으로 큰 번호로 향하는 참조 64개가 남는다 --
그래서 이동 전에 배정과 계층을 계산하는 도구가 첫 준비물이다.

새 도구 `tools/migrate/move_plan.py`(code-author, 명령행 도구 -- `extract_selftest.py` 선례). 두 명령:
* `plan`: N3.10 표(`import_layering.mod_table`로 읽는다)·레지스트리 목적지 열·엔진 소스로 design v2 §6.2 규칙 A-1~A-5를 적용해 **최상위 정의 → MOD 배정**(근거 규칙 ID 포함),
  PLAN-LAYER(큰 번호로 향하는 import 생성 참조 0, 모듈 순환 0), 미배정(A-5 FAIL), 모듈별 **shim 재수출 목록**, card 순서를 한 번의 실행으로 낸다.
* `check`: 이동 card 한 건의 base·head에서 MOVE-AST(design v2 §3)와 ORDER를 판정한다 -- 옮긴 정의 목록은 **G1의 `reachability.moved_defs`를 부른다**(같은 개념을 다시 구현하지 않는다).

원칙: 도구는 코드 구조만 읽는다 -- 회로·넷·소자 이름, `library/`·`*.topology.json`을 읽지 않는다(topology 무관). 분할 대상·도구로 남는 파일 이름과 옛 목적지 이름 별칭은
**명령행 입력**으로만 받는다(도구 소스에 엔진 파일·모듈 이름 리터럴 없음). 결과는 JSON 한 줄(WP-11 -- 호출자가 파일로 받는다). 판정 도구라 숫자 임계값이 없다(WP-03).
이 card는 **G1 병합 뒤 base**에서 시작한다(`check`가 `moved_defs`를 부른다). A = `skills/analog-gmid-design/assets`.

## 관찰 가능한 계약

1. **`plan` 명령**: `$PY tools/migrate/move_plan.py plan --root <저장소> --plan <계획서> --registry <레지스트리> --split <파일>… --keep <파일>… [--aliases <json>]`.
   `--split` = 정의를 MOD로 나눌 파일(A 기준 이름), `--keep` = 도구로 남는 파일(목적지 셀이 그 파일 이름이면 그대로 둔다 -- `--split`에도 있을 수 있다: 일부 정의만 나가고 파일은 남는다), `--aliases` = 옛 목적지 이름 → MOD 파일 이름 사전.
   출력 JSON 키: `assignment`(`{"<파일>::<이름>": {"mod": "<MOD 파일>", "rule": "A-1|A-2|A-3|A-4|A-5"}}`), `upward`(σ(u) < σ(v)인 참조 목록), `cycles`, `unassigned`,
   `conflicts`(한 이름이 N3.10 두 행에 걸림 등), `reexports`(`{"<split 파일>": ["from <MOD> import …" 한 줄씩]}`), `order`(MOD 번호순 card 목록).
   exit 0 = `upward`·`cycles`·`unassigned`·`conflicts` 모두 비었음, 1 = 하나라도 있음, 2 = 입력 오류(파일 없음, N3.10 표 파손 -- `mod_table`의 GateError, 레지스트리 표 없음).
2. **규칙 적용(design v2 §6.2)**: A-1 = N3.10 '대표 대상' 칸의 백틱 이름(`*` 글롭 포함, `<파일>.py` 토큰은 그 파일의 최상위 정의 전부, `모듈.이름`은 이름), A-2 = dataclass·예외·
   레코드 클래스는 그것을 만들거나 받는 정의의 가장 낮은 MOD, A-3 = 목적지 셀이 둘 이상 MOD를 적은 행은 피참조 전부를 담는 가장 낮은 MOD(통째), A-4 = 셀의 MOD 파일 이름 또는
   `--aliases`, `〃`는 위 행, A-5 = 행 없는 정의·최상위 대입은 그것을 참조하는 정의의 가장 낮은 MOD, 참조자가 없으면 `unassigned`(조용히 원래 파일에 두지 않는다).
   레지스트리 값으로 등록된 함수(최상위 dict·튜플 값의 이름)는 그 레지스트리와 같은 MOD(A-2의 레코드 규칙과 같은 '소비자 따라' 원리).
3. **PLAN-LAYER 참조**: `reachability._refs`로 뽑은 참조 중 `name`·`modattr`만, 해석은 같은 파일 최상위 바인딩·`--split`/MOD 모듈의 `from` import·모듈 별칭 속성으로만(해석 못 한 이름은
   참조가 아니다 -- `build_graph`의 '같은 이름의 모든 def' 과대 근사를 쓰지 않는다). `str`(문자열 레지스트리)·`attr`(임의 속성)은 import를 만들지 않으므로 계층 참조가 아니다.
4. **`check` 명령**: `$PY tools/migrate/move_plan.py check --root <저장소> --base <커밋> --head <커밋> --card <MOD 파일> --plan … --registry … --split … --keep … [--aliases …]`.
   head의 소스 분류 파일을 `reachability.read_tree`로 읽고 `reachability.moved_defs(base, head)`로 옮긴 정의를 받아 판정한다. 발견(JSON `findings`, 0이면 exit 0):
   * `move-set`: 옮긴 정의 중 목적지가 `--card` 파일인 것의 집합 ≠ base 트리로 계산한 `plan` 배정에서 그 MOD의 집합(빠짐·더함 모두).
   * `changed`: 옮긴 정의가 아니면서 base의 같은 자리와 해시가 다르거나 base에 없는 head 정의(= V3 대상과 같은 뜻).
   * `lost`: base 정의 중 head의 같은 자리에도, 옮긴 자리에도 없는 것.
   * `non-import-diff`: 바뀐 파일의 최상위에서 정의 밖에 바뀐 문장이 import 문·옮긴 최상위 문장이 아닌 것.
   * `order`: `--card` 파일이 import하는 `--split` 파일이나 더 큰 번호 MOD.
   * `shim`: `--split` 파일에 남은 재수출이 `plan`의 `reexports`와 다르거나, `--split` 파일에 def·class·`import *`가 새로 생김.
5. **재사용(정의 하나)**: MOD 표는 `import_layering.mod_table`, 참조 추출은 `reachability._refs`, 트리 읽기는 `reachability.read_tree`, 이동 판정은 `reachability.moved_defs`,
   해시는 `reachability.def_hash`를 import해 쓴다. 도구 안에 같은 개념의 새 구현이 없다(auditor: `move_plan.py` AST에 `hashlib`·`ast.dump` 호출 0, `def mod_table` 0).
6. **재계산 없음**(NFR-2): 한 번의 실행에서 소스 파일마다 `ast.parse` 1회, 참조 그래프 1회 계산으로 `plan` 출력 전부를 낸다(auditor: 합성 입력에서 `cProfile`의 `ast.parse` 호출
   수 = 입력 소스 파일 수). `check`는 `moved_defs`를 1회 부른다.
7. **topology 무관·이름 무관**: 도구 소스에 `library`·`.topology.json`·`sizing_recipe`·`stick_diagram`·`topology_library`·`design_report`·`optimizer` 문자열 리터럴이 없다(auditor:
   `git grep -n -E "library|topology\.json|sizing_recipe|stick_diagram|topology_library|design_report|optimizer" -- tools/migrate/move_plan.py` 0건). 합성 입력(회로 없음, 가짜 모듈
   이름)에서 모든 계약이 성립한다.
8. **실제 저장소 실행**(배선 전제 확인, 판정 아님): 병합본에서 design v2 §2.1의 `--split sizing_recipe.py stick_diagram.py topology_library.py design_report.py audit_current_forced.py
   --keep audit_current_forced.py --aliases <optimizer → theta_search>`로 `plan`을 돌리면 exit 0 또는 1이고(열 재생성 전이라 1이 정상) exit 2가 아니다. 결과 JSON은 D0b 입력이다.
9. **배선**: 이 도구는 (i) D0b가 만드는 계약 test `contracts/test_p3_registry_dest.py`(레지스트리 열 = `plan` 배정, PLAN-LAYER 0 -- 매 card V1에서 실행) (ii) M card 판정 기록
   `equivalence.commands`의 `check` (iii) design 30 DoD E2·E4에서 불린다. D0b 병합 전에 이 셋 중 (i)이 없으면 D0b card가 막는다(미배선 상태로 Phase를 넘기지 않는다).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `move_plan` | `*` | 신규 모듈 `tools/migrate/move_plan.py` |
| `move_plan` | `main` | `def main(argv: list) -> int` |

## 판정 유형 근거

red-green: 도구가 없는 base에서 `A/tests/tooling/test_move_plan.py`의 모든 test가 도구 존재 단언에서 실패한다(신규 모듈 -- ImportError류 실패가 인정되는 경우, 계획 N3.12.3 순서 3,
`test_extract_selftest.py` 선례처럼 수집 오류가 아니라 test 실패로). 병합본에서 green. code 커밋이 있으므로 test-only가 아니다(P7 선례 -- DoD 도구도 red-green).

## oracle 종류와 출처

(a) 구성: test가 `tmp_path`에 합성 저장소를 만든다 -- 가짜 N3.10 표(MOD 3~4개, 가짜 파일 이름), 가짜 레지스트리 표(목적지 셀에 MOD 이름·옛 이름·`〃`·두 MOD·빈 셀), 가짜 엔진
소스(서로 참조하는 def·레코드 클래스·레지스트리 dict·모듈 캐시), 이동 전후 두 커밋. 기대 배정·위반·발견은 design v2 §6.2 규칙을 합성 입력에 손으로 적용한 것이다(피검 도구
출력에서 가져오지 않는다). CLI 계약이라 하위 프로세스로만 부른다.

## 거부해야 할 입력

`plan`: 큰 번호로 향하는 참조가 생기는 배정(upward → exit 1), 두 MOD 순환(exit 1), 참조자 없는 미배정 정의(exit 1 `unassigned`), 한 이름이 N3.10 두 행에 걸림(exit 1 `conflicts`),
N3.10 표 파손·레지스트리 없음(exit 2). `check`: 옮기며 한 줄 바뀐 정의(`changed`), 배정 밖 정의를 함께 옮김(`move-set`), 정의 삭제(`lost`), import 아닌 최상위 문장 변경
(`non-import-diff`), 새 MOD가 잔여 split 파일 import(`order`), shim에 def 래퍼(`shim`) -- 각각 exit 1.

## library 회로 적용 여부

해당 없음(코드 구조 도구). 실제 엔진 소스 실행은 계약 8(판정 아님)과 D0b.

## 무동작 판정 입력(무발동 값)

엔진 소스·기존 test·게이트 도구는 바뀌지 않는다. 합성 입력에서 이동이 없는 base = head 쌍의 `check`는 `move-set` 외 발견 0(`--card`에 배정된 정의가 있으면 `move-set` 하나 -- 아직
옮기지 않았다는 뜻), 배정된 정의가 없는 MOD면 발견 0.

## 재현할 수치

없음(실제 저장소 배정 수치는 D0b 판정 기록에서 인용한다).

## 결정 필요 항목

없음 -- 도구 위치(`tools/migrate/`, design v2 D-7)와 규칙(§6.2)은 design 30 승인(UD-0)이 덮는다. N3.10 표 개정이 필요한 충돌(`conflicts`·`upward`)은 이 도구가 **보고**하고
해소는 D0b(UD-0 범위)다.

## 작성 전 실측

(기준 gate `master` `cd64170` -- G1 병합 뒤 base에서 5의 `moved_defs`·`def_hash` 위치를 다시 잰다)
1. 사실: `sed -n 20,40p tools/gates/import_layering.py` → `mod_table(plan_text)`(22~35행)이 N3.10 표를 `rp.read_section_table(plan_text, "### N3.10 ")`로 읽어 `{파일 줄기: MOD 번호}`를
   돌린다. `sed -n 69,95p tools/gates/reachability.py` → `_refs(nodes, imports, mod_alias)`가 (`name`|`modattr`|`attr`|`str`|`nested`, 값) 집합. `sed -n 97,158p`(97행 `def build_graph`) → `build_graph`의 해석이
   `by_name` 과대 근사(해석 못 한 이름 → 같은 이름의 모든 def). 레지스트리 목적지 분포·16행·64 참조: design v2 부록 A M9·M11·M14(`p3_measure.py`·`p3_assign.py` cd64170 재실행).
   `ls tools/migrate` → `extract_selftest.py` 하나, test는 `A/tests/tooling/test_extract_selftest.py`(하위 프로세스 CLI 호출, `_REPO_ROOT = parents[5]`).
2. 이름 충돌: `ls tools/migrate A/tests/tooling` → `move_plan.py`·`test_move_plan.py` 없음. `git grep -n "glob(" -- skills/analog-gmid-design/assets/tests` → `tooling/` 디렉터리를
   glob하는 test 없음, `rglob("*.py")` 전수 스캔 4곳(ts3 print 토큰, d_delete_dead·d_delete_telescopic·d_move_tests 삭제·이관 이름 참조) -- 새 test가 그 토큰·이름을 쓰지 않으면
   무발동. `tools/migrate/`는 `A/*.py` glob 밖이라 엔진 스캔 대상이 아니다.
3. 원칙: topology·이름 무관 -- 계약 7, 재계산 없음 -- 계약 6, 정의 하나 -- 계약 5, 만들면 배선 -- 계약 9, 조용한 기본값 금지 -- 계약 2 A-5 `unassigned`.
4. 쓰기 경로: `tools/migrate/move_plan.py` = code-author(계획 N3.12.2 601행 `tools/migrate/**`), `A/tests/tooling/test_move_plan.py` = test-author(계획 N3.11 549행 `tooling/`).
   role_paths 분류: `tools/**` = tool(게이트 코드 아님 -- `GATE_CODE_PREFIX = "tools/gates/"`) → `gate_change: no`.
5. 계획서 소비자: 새 이름만. `git grep -n "move_plan" -- docs/01-plan docs/02-design` → 0건. 재사용 함수 `mod_table`·`_refs`·`read_tree`·`moved_defs`·`def_hash`의 시그니처는 G1 뒤
   base에서 확인(`moved_defs`·`reachability.def_hash`는 G1이 만든다).
6. 미배선: 새 def는 도구 모듈 안(`main`이 부른다). V7 검사 범위(`A/*.py`·`run_harness.py`) 밖. 도구 자체의 배선은 계약 9 -- D0b의 계약 test가 매 card 부른다.
7. 기존 계약 test: 바뀌는 이름·파일 없음(`git grep -n -E "tools/migrate" -- skills/analog-gmid-design/assets/tests/contracts` → 0건).
