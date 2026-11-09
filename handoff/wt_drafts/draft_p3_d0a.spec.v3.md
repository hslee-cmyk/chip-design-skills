---
id: 20260930-p3-move-plan-tool
phase: 3
evidence_type: red-green
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split`(초안 v3) §6.3, card D0a. 계획 N3.10 517행 "Phase 3 design 문서가 그 열(레지스트리 '이관 목적지')에서 이관표와 실제 의존 그래프를 생성한다"와
N9.1 `30-module-split` 행("이관표, 계산된 import 그래프, `import_layering.py` 규칙, AST 해시 증명 명령, shim 재수출 목록 생성법")을 **손이 아니라 도구로** 만든다.
실측(design v3 §6.1): 열이 N3.10 이전 판 이름을 쓰고(MOD 이름 없는 셀 62, MOD1·5·6 행 0), 쪼개라는 셀이 16행이며, 초안 배정만으로 큰 번호로 향하는 참조 64개가 남는다 --
그래서 이동 전에 배정과 계층을 계산하는 도구가 첫 준비물이다.

새 도구 `tools/migrate/move_plan.py`(code-author, 명령행 도구 -- `extract_selftest.py` 선례). 두 명령:
* `plan`: N3.10 표·레지스트리 목적지 열·엔진 소스로 design v3 §6.2 규칙 A-0~A-5를 적용해 **최상위 단위 → MOD 배정**(근거 규칙 ID 포함), PLAN-LAYER, 미배정, shim 재수출 목록,
  card 순서, 레지스트리 열 대조(REG-DEST)를 한 번의 실행으로 낸다. **Phase 3의 어느 시점(이동 전·중·F2 뒤) 트리에서든 같은 뜻으로 동작한다**(규칙 A-0, 계약 2).
* `check`: 이동 card 한 건(또는 Phase 전체, `--card ALL`)의 base·head에서 MOVE-AST·ORDER·SHIM·CACHE-ID(design v3 §3)를 판정한다 -- 옮긴 단위는 **G1의 `reachability.moved_defs`**,
  이름 해석은 G1의 `reachability.SourceIndex`를 부른다(같은 개념을 다시 구현하지 않는다).

원칙: 도구는 코드 구조만 읽는다 -- 회로·넷·소자 이름, `library/`·`*.topology.json`을 읽지 않는다(topology 무관). 분할 대상·도구로 남는 파일 이름과 옛 목적지 이름 별칭은
**명령행 입력**으로만 받는다(도구 소스에 엔진 파일·모듈 이름 리터럴 없음). 결과는 stdout JSON 한 줄(WP-11 -- 호출자가 파일로 받는다). 판정 도구라 숫자 임계값이 없다(WP-03).
이 card는 **G1 병합 뒤 base**에서 시작한다. 이 spec card의 CLI가 **정본**이고 design v3 §6.3·§10은 이것을 인용한다. A = `skills/analog-gmid-design/assets`.

## 관찰 가능한 계약

1. **CLI(정본)**. 경로 인자 `--plan`·`--registry`는 저장소 상대 경로이고 `plan`은 `--rev`, `check`는 `--base` 커밋에서 `git show`로 읽는다. `--split`·`--keep`은 A 바로 아래 파일 이름
   (`<이름>.py`), `--aliases`는 JSON 객체 문자열(`{"<옛 이름>": "<MOD 파일 이름>"}`).
   ```
   $PY tools/migrate/move_plan.py plan  --root <저장소> [--rev <커밋>] --plan <경로> --registry <경로> --split <파일>… [--keep <파일>…] [--aliases <JSON>]
   $PY tools/migrate/move_plan.py check --root <저장소> --base <커밋> --head <커밋> --card <MOD 파일 이름>|ALL --plan <경로> --registry <경로> --split <파일>… [--keep <파일>…]
                                        [--aliases <JSON>] [--allow-changed <경로>::<qualname>…]
   ```
   `--rev` 기본값 `HEAD`. exit 0 = 아래 판정 목록이 모두 비었음, 1 = 하나라도 있음, 2 = 입력 오류(`--plan`·`--registry`가 그 커밋에 없음, N3.10 표 파손 -- `mod_table`·
   `read_section_table`의 GateError, 레지스트리 함수 표 없음, `--split`/`--keep`/`--card` 값이 `<이름>.py`(또는 `ALL`) 모양이 아님, `--aliases` JSON 파손, git 실패). 오류도 JSON 한 줄
   (`{"tool": "move_plan", "verdict": "ERROR", "error": …}`). 정상 출력 첫 키는 `"tool": "move_plan"`, `"command"`, `"verdict"`(`PASS`|`FAIL`).
   게이트 모듈(`reachability`·`import_layering`·`role_paths`·`source_lint`)은 **`--root`의 `tools/gates`**에서 import한다(도구 파일 위치와 무관 -- 다른 커밋에서 꺼낸 사본을 스크래치에서
   실행해도 같은 결과. M card와 DoD는 D0a 병합 커밋의 이 파일을 꺼내 실행한다, design v3 §8·§10).
2. **`plan` 규칙(design v3 §6.2, 우선순위 순)**. 단위 = G1 `SourceIndex.units`의 최상위 함수·클래스·문장(문장 단위는 그것이 바인딩하는 이름으로 부른다). 배정 대상 = `--split` 파일의
   단위 + A-0 대상. 참조 R(u)는 계약 3.
   * **A-0 현재 위치**: N3.10 표 파일(`mod_table` 줄기 + `.py`) 중 그 커밋에 있고 `--split`에 **없는** 파일의 단위는 그 파일로 배정. (Phase 진행 중 옮겨진 단위가 여기에 걸린다.)
   * **A-1 계획 명시**: N3.10 표의 `대표 대상` 열(`role_paths.read_section_table(plan, "### N3.10 ")`에서 머리가 `대표 대상`인 열 -- `mod_table`은 ID·파일 열만 읽으므로 게이트 코드는
     바꾸지 않는다)의 백틱 토큰 중 식별자 패턴 `[A-Za-z_][A-Za-z0-9_]*`(끝이나 가운데 `*` 글롭 하나 허용)은 그 이름, `<이름>.py`는 그 파일(`--split`일 때)의 모든 단위, `<모듈>.<이름>`은
     `<이름>`. 그 밖의 백틱 내용(`∂ID/∂VSB`, `workspaces/`)과 산문은 무시한다. 한 단위가 두 행의 토큰에 걸리면 `conflicts`.
   * **A-2 레코드 클래스 하강**: 레코드 클래스 = 최상위 클래스 중 (i) 데코레이터가 `dataclass`(`Name`·`Attribute`·그 호출) 이거나 (ii) 기반 클래스의 `binding_origin`이 내장 예외
     (`("builtin", n)`이고 n이 `BaseException` 하위 이름)이거나 다른 레코드 클래스이거나 (iii) 메서드가 없는 것. 레코드 클래스는 **그것을 참조하는 단위**(R(v)에 그 클래스가 든 v,
     레코드 클래스 자신은 제외) 중 배정 MOD 번호가 가장 낮은 것으로. 문자열 주석 안의 이름도 참조다(G1 `global_names`가 문자열 주석을 넣는다). 참조자가 없으면 A-3 이하로.
   * **A-3 계층 강제**: 레지스트리 목적지 셀이 MOD를 둘 이상 적은 행(A-4의 토큰 규칙으로 센다)의 단위는 max(셀의 가장 작은 MOD 번호, R(u)의 배정 MOD 번호 최댓값)의 MOD로 통째.
   * **A-4 레지스트리 열**: 셀의 식별자 토큰(`[A-Za-z_][A-Za-z0-9_]*`) 중 N3.10 파일 줄기(또는 `<줄기>.py`)와 `--aliases` 키를 MOD로 바꾼 집합이 MOD 하나면 그 MOD, 둘 이상이면 A-3,
     0이면 A-4로 정하지 않는다. `〃`만 있는 셀은 위 행의 셀. 레지스트리 행과 단위는 행의 함수 이름 칸 = 단위 키로 짝짓는다(메서드 행 `Class.method`는 클래스 단위).
   * **A-5 소비자 따라**: 위에 걸리지 않은 단위(레지스트리에 행이 없는 정의, 최상위 문장)는 **그것을 참조하는 단위**(문장 단위 포함 -- 최상위 레지스트리 dict가 값 함수의 참조자다)의
     가장 낮은 배정 MOD로. 참조자가 없으면 `unassigned`(조용히 원래 파일에 두지 않는다).
   A-2·A-3·A-5는 다른 단위의 배정에 기대므로 배정이 바뀌지 않을 때까지 반복한다(고정점). 출력 키:
   `assignment`(`{"<A 기준 파일>::<키>": {"mod": "<MOD 파일>", "rule": "A-0|A-1|A-2|A-3|A-4|A-5"}}`), `upward`(u→v, σ(u) < σ(v) 목록), `cycles`(MOD 순환), `unassigned`, `conflicts`,
   `reexports`(`{"<split 파일>": ["from <MOD 줄기> import a, _b, …" MOD마다 한 줄]}` -- 그 split 파일에서 다른 파일로 배정된 단위가 바인딩하는 이름 **전부**(계획 534행 '인벤토리에서
   생성', `_` 접두 포함, 이름순 -- A-0으로 이미 옮겨진 단위는 split 파일의 단위가 아니므로 남은 것만 나온다), `import *` 없음), `order`(배정 단위가 있는 MOD를 번호순), `absent_split`(그 커밋에 없는 `--split` 파일 -- 오류가 아니다: F2 뒤에는 shim 파일이 없다),
   `reg_mismatch`(레지스트리 함수 행 중 목적지 셀이 MOD 파일 이름 **하나**이고 그 단위가 있는데 배정 MOD와 다른 것 -- REG-DEST). exit 1 사유 = `upward`·`cycles`·`unassigned`·
   `conflicts`·`reg_mismatch` 중 비지 않은 것.
3. **참조 R(u)**(PLAN-LAYER·A-2·A-3·A-5): u의 `SourceIndex.global_names`의 이름 v마다 `binding_origin(file(u), v)`가 `("def", f, n)`이고 f가 `--split` 파일이나 N3.10 파일이면 u → (f의 n을
   바인딩하는 단위). 그리고 u 안(중첩 def·메서드 포함 전체)의 `Attribute(value=Name(a))` 중 `binding_origin(file(u), a)`가 `("module", f)`인 것 → (f의 그 속성 이름 단위). 문자열 참조(`str`)와
   해석되지 않는 이름·임의 속성은 참조가 아니다(`build_graph`의 '같은 이름의 모든 def' 과대 근사를 쓰지 않는다). G1 `global_names`는 중첩 def·메서드·클래스 수준 문장까지 덮으므로
   `reachability._refs`가 중첩 몸체를 건너뛰는 문제(초안 v2 → 검토 S6: 엔진 최상위 단위 21개가 중첩 def·메서드 안에서만 다른 최상위 이름을 참조)가 생기지 않는다.
4. **`check`**: `reachability.read_tree(root, rev, reachability.SOURCE_GLOBS)`로 base·head 소스를 읽어 색인을 한 번씩 만들고 `moved_defs(B, H)`를 한 번 부른다. 배정 집합
   = base 커밋에서 계산한 `plan`의 단위 중 배정 MOD가 `--card`이고 base 위치가 그 파일이 아닌 것(`ALL`이면 배정 MOD ≠ base 위치인 전부). 출력 키: `assigned`(배정 집합),
   `moved_units`·`moved_defs`(`moved_defs` 반환의 `units`·`defs` 그대로 -- design v3 §10 E2가 V3 `moved`와 대조), `findings`(아래 종류별 목록 사전, 종류 키는 항상 있다). 발견:
   * `move-set`: head에서 `--card` 파일로 옮긴 단위(`moved_defs` `units`의 목적지)의 집합 ≠ 배정 집합(빠짐·더함 모두).
   * `move-rejected`: `moved_defs` `rejected`의 모든 항목(규칙 이름 그대로 -- 덮어쓰기 M-0, 재바인딩 M-4 등).
   * `changed`: head 단위 중 옮긴 단위가 아니고 base 같은 파일에 같은 (종류, 키, 해시) 단위가 없는 것(함수·**클래스 골격**·문장 모두 -- 클래스 필드 기본값 변경처럼 V3·V6·V7이 보지
     않는 변경도 여기서 잡힌다), `--allow-changed`에 적힌 id는 뺀다.
   * `lost`: base 단위 중 head 같은 파일에 같은 (종류, 키, 해시)로도 없고, 옮긴 단위의 원본도 아니며, head 같은 파일에 같은 (종류, 키)가 있어 `changed`로 보고된 것도 아닌 것
     ((파일, 키, 해시) 기준 -- 덮어쓰기에서는 목적 파일의 `changed`와 원본의 `lost`가 함께 나온다).
   * `order`: `--card` 파일(`ALL`이면 모든 MOD 파일)의 import 문이 가리키는 트리 파일 중 `--split` 파일이거나 번호가 같거나 큰 다른 MOD 파일인 것.
   * `shim`: head에 있는 `--split` 파일(N3.10 파일·`--keep` 파일이 아닌 것)의 최상위 문장이 docstring과 `from <MOD 줄기> import …` 밖에 있거나, 재수출 이름 집합이 (base에서 그 파일이 이미 재수출하던 이름) ∪ (이 card에서
     그 파일에서 옮긴 단위가 바인딩하는 이름)과 다르거나, 재수출 이름 s마다 `binding_origin(shim, s)` ≠ `binding_origin(<MOD 파일>, s)`인 것(SHIM 동일성 -- 출처가 같으면 import가 같은 객체를
     묶는다. 실행 중 모듈 속성 덮어쓰기는 design v3 §7.2 D군·UD-7). `--split`이면서 N3.10·`--keep` 파일인 것은 재수출 줄만 대조.
   * `cache`: head 모듈 최상위 캐시(대입·주석 대입의 대상 이름에 `cache`(대소문자 무시)가 들고 값이 빈 dict -- `source_lint._is_empty_dict`와 같은 판정) c가 파일 X에 있을 때,
     `global_names`에 c가 들고 `binding_origin`이 `("def", X, c)`인 단위가 X 밖에 있는 것(CACHE-ID).
5. **재사용(정의 하나)**: MOD 표 `import_layering.mod_table`, 대표 대상 열 `role_paths.read_section_table`, 트리 읽기 `reachability.read_tree`, 단위·해시·이름 해석
   `reachability.SourceIndex`, 이동 `reachability.moved_defs`, 캐시 판정 `source_lint._is_empty_dict`를 import해 쓴다. auditor: `move_plan.py` AST에 `hashlib`·`symtable` import 0,
   `ast.dump` 호출 0, `def mod_table`·`def moved_defs`·`def binding_origin` 0.
6. **재계산 없음**(NFR-2): 한 실행에서 커밋마다 `SourceIndex` 1개(`plan` 1, `check` 2 -- base 색인은 `plan` 계산과 `moved_defs`가 같이 쓴다), `moved_defs` 호출은 `check` 1·`plan` 0,
   `read_tree` 호출은 `plan` 1·`check` 2. auditor: 합성 입력 실행의 `cProfile` 함수별 호출 수. `ast.parse` 호출 수 ≤ (그 실행이 읽은 커밋들의 소스 파일 수 합) + (계획서·레지스트리 파싱
   0 -- 표는 `read_section_table`이 문자열로 읽는다).
7. **topology 무관·이름 무관**: 도구 소스에 `library`·`topology.json`·`sizing_recipe`·`stick_diagram`·`topology_library`·`design_report`·`optimizer` 토큰이 **파일 텍스트 어디에도**
   없다(주석·docstring 포함 -- auditor 명령과 같은 기준: `git grep -n -E "library|topology\.json|sizing_recipe|stick_diagram|topology_library|design_report|optimizer" -- tools/migrate/move_plan.py`
   0건). 사용 예는 가짜 이름으로 쓴다. 합성 입력(회로 없음, 가짜 모듈 이름)에서 모든 계약이 성립한다.
8. **Phase 전 구간 동작**(배선 전제): (a) 이동 전 병합본에서 design v3 §10의 `MP_ARGS`로 `plan`을 돌리면 exit 0 또는 1이고(D0b 열 재생성 전이라 `reg_mismatch`로 1이 정상) exit 2가
   아니다. (b) 합성 입력에서, 이동 card를 배정대로 하나씩 적용한 각 커밋의 `plan` `assignment`가 이동 전 커밋의 것과 같다(옮긴 단위는 A-0으로 같은 MOD). (c) shim 파일을 지운 커밋에서
   `plan`은 exit 2가 아니고 `absent_split` = 지운 파일, 모든 배정의 `rule` = `A-0`(또는 `--keep`·N3.10 파일로 남은 split 파일의 A-1~A-5).
9. **배선**: 이 도구는 (i) D0b 계약 test `contracts/test_p3_registry_dest.py`가 매 card V1에서 `plan`을 부르고 exit 0·`reg_mismatch` 빈 목록을 단언(계약 8 (b) 때문에 Phase 중에도 성립)
   (ii) M card 판정의 `equivalence.commands`에 `check` (iii) design v3 DoD E2·E4·E6에서 불린다. D0b 병합 전에 (i)이 없으면 D0b card가 막는다.
10. **test의 red 조건**: `A/tests/tooling/test_move_plan.py`의 모든 test는 먼저 도구 파일 존재와 출력 첫 줄이 JSON이며 `"tool": "move_plan"`임을 단언한다 -- exit 2를 기대하는 test가 도구
    없는 base에서 `python: can't open file`(exit 2)로 통과하지 않게.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `move_plan` | `*` | 신규 모듈 `tools/migrate/move_plan.py` |
| `move_plan` | `main` | `def main(argv: list) -> int` |

## 판정 유형 근거

red-green: 도구가 없는 base에서 `A/tests/tooling/test_move_plan.py`의 모든 test가 도구 존재 단언에서 실패한다(계약 10 -- 신규 모듈, 계획 N3.12.3 순서 3, `test_extract_selftest.py` 선례처럼
수집 오류가 아니라 test 실패로). 병합본에서 green. code 커밋이 있으므로 test-only가 아니다(P7 선례 -- DoD 도구도 red-green).

## oracle 종류와 출처

(a) 구성: test가 `tmp_path`에 합성 git 저장소를 만든다 -- 가짜 N3.10 표(MOD 3~4개, 가짜 파일 이름, `대표 대상` 열에 식별자·글롭·`<파일>.py`·`<모듈>.<이름>`·무시할 기호·산문), 가짜
레지스트리 표(목적지 셀에 MOD 이름·옛 이름·`〃`·두 MOD·빈 셀), 가짜 엔진 소스(서로 참조하는 def, 중첩 def 안에서만 다른 최상위를 부르는 def, dataclass·예외·메서드 없는 클래스, 레지스트리 dict,
모듈 캐시), 이동 card를 하나씩 적용한 커밋들과 shim을 지운 커밋. 기대 배정·위반·발견은 design v3 §6.2 규칙과 이 card 계약을 합성 입력에 손으로 적용한 것이다(피검 도구 출력에서
가져오지 않는다). CLI 계약이라 하위 프로세스로만 부른다.

## 거부해야 할 입력

`plan`: 큰 번호로 향하는 참조가 생기는 배정(`upward`), 두 MOD 순환(`cycles`), 참조자 없는 미배정 단위(`unassigned`), 한 단위가 N3.10 두 행에 걸림(`conflicts`), 레지스트리 열과 배정이
다름(`reg_mismatch`) -- 각각 exit 1. N3.10 표 파손·레지스트리 표 없음·잘못된 인자(exit 2). `check`: 옮기며 한 줄 바뀐 정의·클래스 필드 변경(`changed`), 배정 밖 단위를 함께 옮김·배정
단위를 빠뜨림(`move-set`), 덮어쓰기·재바인딩(`move-rejected` + `changed`/`lost`), 정의 삭제(`lost`), import 아닌 최상위 문장 변경(`changed`/`lost`의 문장 단위), 새 MOD가 잔여 split 파일
import(`order`), shim에 def 래퍼·다른 출처 재수출(`shim`), 캐시와 사용자 분리(`cache`) -- 각각 exit 1.

## library 회로 적용 여부

해당 없음(코드 구조 도구). 실제 엔진 소스 실행은 계약 8 (a)(판정 아님)와 D0b.

## 무동작 판정 입력(무발동 값)

엔진 소스·기존 test·게이트 도구는 바뀌지 않는다. 합성 입력에서 이동이 없는 base = head 쌍의 `check`는 `move-set` 외 발견 0(`--card`에 배정된 단위가 있으면 `move-set` 하나 -- 아직
옮기지 않았다는 뜻), 배정된 단위가 없는 MOD면 발견 0.

## 재현할 수치

없음(실제 저장소 배정 수치는 D0b 판정 기록에서 인용한다).

## 결정 필요 항목

없음 -- 도구 위치(`tools/migrate/`, design v3 D-7)와 규칙(§6.2)은 design 30 승인(UD-0)이 덮는다. N3.10 표 개정이 필요한 충돌(`conflicts`·`upward`)은 이 도구가 **보고**하고
해소는 D0b(UD-0 범위)다.

## 작성 전 실측

(기준 gate `master` `cd64170` -- G1 병합 뒤 base에서 5의 G1 이름 위치를 다시 잰다)
1. 사실: `sed -n 20,40p tools/gates/import_layering.py` → `mod_table(plan_text)`(22~35행)가 N3.10 표의 `ID`·`파일` 열만 읽어 `{파일 줄기: MOD 번호}`. `role_paths.read_section_table`(226행)은
   머리 `['ID', '파일', '책임', '대표 대상']`와 10행을 돌린다(`wt/_drafts/p3v3_facts.py` `n310_header`). `대표 대상` 토큰 분류(`n310_rep_tokens`): 식별자 41(글롭 `trace_*_branches`·`_hr_*`
   포함), `<파일>.py` 1(MOD4 `topology_library.py`), `<모듈>.<이름>` 1(MOD9 `design_report.render_html_report`), 무시 2(MOD1 `∂ID/∂VSB`, MOD10 `workspaces/`), MOD7 토큰 0(산문만).
   `sed -n 69,95p tools/gates/reachability.py` → `_refs`가 중첩 def 몸체를 건너뜀. `p3v3_facts.py` `S6_nested_refs` → 중첩 def·메서드 안에서만 다른 최상위 이름을 참조하는 최상위 단위
   SR 17·SD 4(예 `SemiEmpiricalGmIdLUT` → `_multilinear_interp`). 엔진 `from __future__ import annotations` SR 35행·SD 32행(주석은 문자열 -- G1 `global_names`가 문자열 주석을 넣는다).
   클래스(`p3v3_g1_measure.py` `classes`): SR 13(dataclass 8·예외 3·메서드 없음 10), SD 28(dataclass 28·메서드 없음 26). 모듈 캐시: SR `_KNEE_L_CACHE`·`_FEASIBLE_L_WINDOW_CACHE`·
   `_ACHIEVABLE_BOUND_CACHE`(주석 대입, 각각 사용 함수 하나 -- `knee_L_for_kind`·`feasible_L_window`·`achievable_metric_bound`), `topology_library` `lru_cache` 데코레이터 1곳(248행).
   레지스트리 목적지 분포·16행·64 참조: design v3 부록 A M9·M11·M14. `ls tools/migrate` → `extract_selftest.py` 하나, test는 `A/tests/tooling/test_extract_selftest.py`.
2. 이름 충돌: `ls tools/migrate A/tests/tooling` → `move_plan.py`·`test_move_plan.py` 없음. `git grep -n "glob(" -- skills/analog-gmid-design/assets/tests` → `tooling/`을 glob하는 test 없음,
   `rglob("*.py")` 전수 스캔 4곳의 피할 토큰은 T0 card 계약 9 목록과 같다(`p3v3_facts.py` `m6_scan_names`). `tools/migrate/`는 `A/*.py` glob 밖이라 엔진 스캔 대상이 아니다.
3. 원칙: topology·이름 무관 -- 계약 7, 재계산 없음 -- 계약 6, 정의 하나 -- 계약 5, 만들면 배선 -- 계약 9, 조용한 기본값 금지 -- 계약 2 A-5 `unassigned`, Phase 전 구간 -- 계약 8.
4. 쓰기 경로: `tools/migrate/move_plan.py` = code-author(계획 N3.12.2 601행 `tools/migrate/**`), `A/tests/tooling/test_move_plan.py` = test-author(계획 N3.11 549행 `tooling/`).
   role_paths 분류: `tools/**` = tool(게이트 코드 아님 -- `GATE_CODE_PREFIX = "tools/gates/"`, 23행) → `gate_change: no`. 판정 도구를 code-author가 쓰므로 M card에서는 D0a 병합 커밋의
   이 파일을 꺼내 실행한다(design v3 §8 M card 제약, 검토 S9).
5. 계획서 소비자: 새 이름만. `git grep -n "move_plan" -- docs/01-plan docs/02-design` → 0건. 재사용 이름 `mod_table`·`read_section_table`·`read_tree`·`SourceIndex`·`moved_defs`·
   `_is_empty_dict`의 시그니처는 G1 뒤 base에서 확인(`SourceIndex`·`moved_defs`는 G1이 만든다).
6. 미배선: 새 def는 도구 모듈 안(`main`이 부른다). V7 검사 범위(`A/*.py`·`run_harness.py`) 밖. 도구 자체의 배선은 계약 9.
7. 기존 계약 test: 바뀌는 이름·파일 없음(`git grep -n -E "tools/migrate" -- skills/analog-gmid-design/assets/tests/contracts` → 0건).
