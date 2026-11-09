# Phase 3 D0a card `20260930-p3-move-plan-tool` -- 착수 키트(test-author·code-author·auditor 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` **`19eb475`**(작업 시작 `0f23786` -- 그 사이 `tools/gates`·엔진 무변경, 레지스트리에 §8 DF-23 표 2개가 늘었다). 저장소 쓰기·상태 변경 git 없음.
측정은 격리 복제본 `C:/g150`(`git init` + `git fetch`, origin 없음, 작업 끝에 삭제)에서만. G1은 미병합이라 **G1 시제품**(`_drafts/g1_kit/install_proto.py` + `g1_core.py`, sha256 앞
`5790433c…`·`8fc4ab4b…`, 21:37·21:43판 -- 다른 agent가 만드는 중인 키트를 측정에만 썼다)을 복제본에 설치해 `reachability.SourceIndex`·`moved_defs`를 얻었다(stub 아님).
대상: spec 초안 `_drafts/draft_p3_d0a.spec.md`(이 키트 반영판, 직전판 `.spec.pre-kit.md`), 키트 `_drafts/p3kit_d0a/`.
**착수 조건**: Phase 3 design 승인(UD-0 -- 아직 아님) + **G1 병합**(D0a는 G1의 `SourceIndex`·`moved_defs`를 import) + Phase 2 DoD PASS(확정 순서상 자동) + **아래 0.3의 G1 AST 접근 결정**.

**착수 0단계(읽기 전용)**:
```
R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills; B=$(git -C $R rev-parse gate/master)
git -C $R diff --stat 19eb475 $B -- tools/gates tools/migrate docs/01-plan/features/gain-budget-gmid-sizing.plan.md docs/03-analysis/gain-budget-gmid-sizing.function-registry.md skills/analog-gmid-design/assets/tests/tooling
git -C $R grep -n -E "def (read_tree|iter_defs|_refs|_is_source|build_graph)|^SOURCE_GLOBS|class SourceIndex|def (moved_defs|units|global_names|binding_origin)" $B -- tools/gates/reachability.py
git -C $R grep -n -E "^def (mod_table|read_section_table|_split_cells|_is_empty_dict)|^GATE_CODE_PREFIX" $B -- tools/gates/import_layering.py tools/gates/role_paths.py tools/gates/source_lint.py
```
판단: (가) `SourceIndex`의 공개 메서드에 모듈 AST(또는 단위 노드)를 돌려주는 것이 있는가(0.3) (나) 재사용 이름 6개(`mod_table`·`read_section_table`·`read_tree`·`SourceIndex`·`moved_defs`·`_is_empty_dict`)의
시그니처가 card 계약 5와 맞는가 (다) 레지스트리에 `함수`·`이관 목적지` 열을 함께 가진 표가 있고 다른 `함수` 표(§8.2)와 구별되는가 (라) `tools/migrate`에 `move_plan.py` 없음, `tooling/`에
`test_move_plan.py` 없음. 맞으면 spec card measured 문장(rev)만 갱신.

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(`0f23786` → `19eb475`)

| 확인 | 결과 | 조치 |
|---|---|---|
| `tools/gates` | `git diff --quiet 0f23786 19eb475 -- tools/gates` 차이 0. `import_layering.mod_table` 22~35, `role_paths.read_section_table` 226·`GATE_CODE_PREFIX` 23, `reachability.read_tree` 31·`iter_defs` 51·`_refs` 69·`SOURCE_GLOBS` 172, `source_lint._is_empty_dict` 168 | B33·G1이 `reachability.py` 줄을 민다 -- 착수 때 재측정(card 그대로 적음) |
| 엔진 사실(작성 전 실측 1·8) | future SR 35·SD 32·TL 24, SR 1411·5302, DR 32, ACF 43, TTM 29(`from stick_diagram import load_topology` -- split 밖), 캐시 SR 2391·2530·7697, TL `lru_cache` 248, main 블록 ACF 160뿐, star·`global` 0. G1 시제품 단위 수 SR def 174·class 13·stmt 31 / SD def 132·class 28·stmt 9 / TL def 7·stmt 1 / DR def 5·stmt 2 / ACF def 4·stmt 2, 단위 키 중복 0 | -- |
| `tools/migrate`·`tooling/` | `extract_selftest.py` 하나 / `test_extract_selftest.py` 하나. `move_plan` 문서 소비자 0, contracts의 `tools/migrate` 참조 0 | -- |
| **레지스트리 표(새로 생김)** | P10b(`b7b1e00`)가 §8 DF-23 기록을 더했다: §8.1 `\| 축 \| 값 \| 항목 수 \|`, §8.2 `\| 함수 \| 파일 \| 항목 수 \| DF \| 담당 Phase \|` 52행 -- **`함수` 열이 있는 표가 목적지 열 없이 생겼다**. card 계약 2는 '레지스트리 함수 표'를 정의하지 않았다. 또 레지스트리는 같은 제목(`### sizing_recipe.py (…)`)이 절마다 되풀이되어 `read_section_table`(제목 정확히 하나)로 읽을 수 없다 | 계약 2 A-4에 정의 문장 추가: 머리에 `함수`·`이관 목적지` 열이 **둘 다** 있는 표 전부, 열 위치는 머리에서(§7은 5열), 표 읽기는 도구 안(`_split_cells`와 같은 칸 규칙) |
| interface card 생성 | **결함 발견**: 계약 3의 맨 이름 `` `build_graph` ``(뜻은 `reachability.build_graph`)를 `interface_card.py`가 엔진 SD의 같은 이름 레이아웃 함수로 잡아 '기존 함수' 1행을 넣었다. 그 card로 V4(`--module-dir tools/migrate`)를 돌리면 **ERROR exit 2**(`git show …:tools/migrate/stick_diagram.py 실패`) | 계약 3 문장을 `` `reachability.build_graph` ``로 -- 재생성 '기존 함수 0개', V4 PASS(`out/d0a.interface.generated.md`) |
| 계약 6 `ast.parse` 상한 문언 | 시제품 실측: `read_tree` 1회 88파일 읽음(`SOURCE_GLOBS`가 `tests/` 포함), 색인 8파일, `ast.parse` 35 = **exec 8 + eval 27**(G1 계약 2의 문자열 주석 파싱). '소스 파일 수'를 읽은 88로 세면 공허하게 넓고, 색인 8로 세며 eval을 넣으면 정직한 구현이 FAIL | 계약 6에 문언 정리: 모듈 파싱(`mode="exec"`) ≤ 색인 파일 수 |
| 계약 8 (a)(관찰) | 시제품 `plan`을 실제 저장소에 §10 `MP_ARGS`로: exit **1**(≠ 2), `import_time_high` **[]**(card 실측 9의 예상과 같다) | card 작성 전 실측 10 |
| phase 3 card 변경 | D0a 계약은 phase 3 card를 세지 않는다. 의도의 순서 문장에 b26pre·backfill이 빠져 있었다 | 순서 문장에 키트 v9 |
| 단위 키 충돌(계약 밖 관찰) | 같은 이름 집합을 바인딩하는 최상위 문장 둘(`X = 1` … `X = 2`)이면 단위 키가 겹친다 -- card는 정하지 않았다. 실제 엔진 5파일 중복 0 | 시제품은 해시 접미로 구분. code-author에게 '겹치면 조용히 덮지 말 것'(아래 2절) |

**작업 끝 확인**: gate `master`가 `5f643a9`로 나아갔다(`19eb475..` = md 일치 계약 test 1파일과 판정 기록뿐 -- `tools/`·엔진·계획서·레지스트리 무변경, 위 표 그대로).

### 0.2 시제품 측정(`_drafts/p3kit_d0a/` -- 측정 전용, 역할에게 건네지 않는다)

| 측정 | 결과 |
|---|---|
| `plan` on 실제 저장소(`19eb475` + G1 시제품, §10 `MP_ARGS`) | 26초, exit 1, `upward` 48, `cycles` 1(MOD 9개 한 SCC), `unassigned` 18(ACF 3 -- `render_report`·문장 2, DR 문장 1, SR 6 -- `_invq_newton`·`build_toy_lut`·`node_pole_estimate`·`signal_path_nodes`·`solve_diode_stack_current`·문장 1, SD 8), `conflicts` 0, `reg_mismatch` 38(대부분 A-1이 레지스트리 열을 이김 -- D0b가 열을 재생성), `import_time_high` **[]**, `absent_split` [], 배정 390(A-4 241·A-5 56·A-1 55·A-2 37·A-3 1). **근사 구현이라 D0b 관찰용** -- 이 card의 기대값 아님(`out/plan_base_19eb475.json`) |
| v7 필수 합성 단계 `import-time-high`(`gen_ith.py`, 가짜 N3.10 MOD1 `lowmod`·MOD2 `lmod`(split, s=2)·MOD3 `jmod`·MOD4 `kmod`, split = `src.py` + `lmod.py`, A-1 토큰으로 배정 고정) | 6단계 전부 구성 기대와 같음, 다른 목록(`upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`) 전부 빈 목록: (i) 기본값이 `lmod.C` → exit 1, `[src.py::f, C]` (ii) 본문에서만 → exit 0 (iii-a) future 없는 파일의 주석이 MOD3 클래스 → exit 1 `[f, Jcls]` (iii-b) future 있으면 → exit 0 (iv) 모듈 dict 문장(MOD4)이 MOD3 함수 → exit 1 `[TABLE, g]` (v) MOD1 함수 → exit 0 (`out/ith_stages.jsonl`) |
| red/green 모양 | 같은 6단계를 담은 시제품 test(`test_move_plan.proto.py`, 도구 존재 단언을 도우미 맨 앞에): 도구 없는 커밋에서 **6 failed `AssertionError: 도구가 없다`**(수집 오류 0), 도구 커밋에서 6 passed(`PT3`, 18초) |
| V3·V4·V5·V6·V7(`v_tools.sh`, base = G1 시제품 커밋, head = test + 도구) | V3 PASS `targets [] mutants 0`(**`tools/migrate`는 `_is_source` 밖 -- 선례 `20260922-ts1-extract-tool` V3와 같은 DESIGN-GAP**: 도구 자체는 변이되지 않는다) · V4 PASS(`--interface-card` + `--module-dir tools/migrate`, NO-SUBJECT만 -- test가 도구를 하위 프로세스로만 부른다) · V5 PASS `diff_paths []` · V6 PASS · V7 PASS `new_defs []`(그래프 밖) |
| 계약 5·7 모양 | 시제품 파일에 `hashlib`·`symtable` import 0, `ast.dump` 0, 금지 토큰 `git grep` 0건 |

### 0.3 결정 필요(착수 조건) -- G1 공개 표면의 AST 접근

D0a가 단위·모듈 AST를 쓰는 곳: 계약 2 A-2(데코레이터·기반·메서드 유무)·`import_time_high`, 계약 3 `Attribute(value=Name)` 참조, 계약 4 `changed`(옮긴 클래스 안 `iter_defs`)·`order`(import 문)·
`shim`(최상위 문장 다중집합 -- import 줄은 G1 단위가 아니다)·`cache`(모듈 대입). G1 spec card 계약 0의 공개 표면은 `units`(종류·키·해시·바인딩 이름)·`global_names`·`binding_origin`뿐이다.
D0a 계약 6('다시 파싱하지 않는다', `ast.parse` ≤ 파일 수)은 AST 접근이 있어야 성립한다. 시제품은 G1 시제품의 내부 속성 `SourceIndex.mod(path).units[i][3]`로 우회했다.
* **기본안**(정의 하나·NFR-2): G1 interface card에 공개 이름 하나(예: `SourceIndex.tree(path) -> ast.Module | None`)를 더하는 G1 spec card 개정 -- G1 착수 전이면 G1 card 소유자가 넣는다. D0a는 그것과
  `reachability.iter_defs`로 단위 노드를 찾는다.
* 대안 1: D0a가 내부 속성에 기댄다(G1 내부 변경에 조용히 깨짐 -- 비권고). 대안 2: D0a가 파일을 다시 파싱하고 계약 6 상한을 두 배로(재계산 -- 비권고).
* draft_p3_g1.spec.md는 이 키트 범위 밖(다른 작업자 편집 중)이라 고치지 않았다. D0a 초안 '결정 필요 항목'에 위 내용을 적었다.

### 0.4 앞선 card가 같은 파일을 건드리는 것 -- 착수 때 다시 잴 것

| card | D0a 관련 | 착수 때 |
|---|---|---|
| B33 `20260930-v7-registry-edges`(게이트, phase 0.5) | `reachability.py`(`build_graph`·`main` -- `<파일>::=<이름>` 간선). D0a가 쓰는 `read_tree`·`SOURCE_GLOBS`·`iter_defs`는 card상 그대로 | 줄 번호, `read_tree(root, rev, prefixes)` 시그니처 |
| G1 `20260930-p3-gate-move-aware`(게이트, phase 0.5) | `SourceIndex`·`moved_defs`·`def_hash`를 `reachability`에 만든다(D0a 재사용 대상) | 0.3 결정 반영 여부, `units` 반환 모양(`[(종류, 키, 해시, 바인딩 이름)]` -- 문장 키는 `None`?), `global_names` 문장 키 `<stmt:해시12>`, `binding_origin` 반환 튜플 모양(`("def", path, name)`·`("module", path)`) |
| V3 면제 묶기·범위 정책(게이트) | `mutate_changed` 출력 키 -- D0a V3 명령의 출력만 바뀜(`targets []`라 판정 영향 0) | -- |
| B34·b26pre·backfill·B26-1(phase 3, 엔진·test) | 엔진 단위 수·클래스(card 작성 전 실측 v5 추정: SD 클래스 28 → 29 `RailDeclaration`, SD 함수 132 → 133 `rail_declaration`), SD future·`__file__` 줄, SR 캐시 줄 이동, 레지스트리 행(B26-1이 행을 더하면 목적지 셀) | 계약 8 (a) 관찰 재실행(exit ≠ 2), 단위 키 중복 0, 레지스트리 함수 표 정의대로 행 수 |
| UD-0 design 커밋(계획 N3.10 개정 3건 + D-19) | `plan`의 실제 입력(대표 대상 토큰) -- 이 card의 test는 합성 입력이라 무관 | 계약 8 (a) 재실행만 |
| P10b(병합됨 `54ef51c`) | 레지스트리 §8 표 | 0.1에서 반영 |

### 0.5 착수 직전에 다시 볼 것

0. 착수 0단계 명령. 1. `role/*` 0개(문서 커밋 push), G1 병합 확인. 2. 0.3 결정이 G1 병합본에 반영됐는지(공개 AST 접근 이름) -- 반영되지 않았으면 착수하지 않는다.
3. interface card 절대 경로 생성, '기존 함수 0개'인지(맨 이름 백틱 토큰이 엔진 이름과 겹치면 다시 생긴다). 4. EL1: 리다이렉트 변수 경로 금지 -- 스크립트 파일로.

---

## 1. gmid-test-author 브리프(순서 2)

```
역할: gmid-test-author. change id = 20260930-p3-move-plan-tool (red-green, phase 3, gate_change: no).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p3-move-plan-tool-test (브랜치 role/test/20260930-p3-move-plan-tool). 절대 경로만.
쓰기 경로: skills/analog-gmid-design/assets/tests/tooling/test_move_plan.py 하나(계획 N3.11 tooling/).
입력: interface card(신규 move_plan.* · move_plan.main, 기존 함수 0행) + spec card '관찰 가능한 계약' 1~10·'oracle 종류와 출처'(v6·v7 필수 합성 단계)·'거부해야 할 입력'·'무동작 판정 입력'.
열람 금지: tools/migrate/move_plan.py(아직 없음), tools/gates 소스(G1 SourceIndex 구현 포함), _drafts/. 
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20260930-p3-move-plan-tool" -m "test: …"
```

**모양 요구(card + 시제품에서 찾은 것)**
1. **CLI만**(하위 프로세스, 인자 목록 -- 셸 없음). 모든 test는 먼저 `<저장소>/tools/migrate/move_plan.py` 존재와 출력 첫 줄이 JSON이고 `"tool": "move_plan"`임을 단언(계약 10 -- 도우미 맨 앞에 두면
   도구 없는 base에서 모든 test가 `AssertionError`로 FAIL, 수집 오류 아님 -- 시제품 확인).
2. **합성 git 저장소**(`tmp_path`): 도구는 게이트 모듈을 **`--root`의 `tools/gates`**에서 import한다(계약 1) -- 합성 저장소에 test가 도는 저장소의 `tools/gates`를 복사해 넣는다(`redteam`·`__pycache__` 제외면 충분).
   경로 = `skills/analog-gmid-design/assets/<가짜>.py`(G1 `_is_source` 범위), 가짜 계획서·레지스트리는 아무 경로(`--plan`·`--registry`로 넘김). 커밋은 `git -c user.name=… -c user.email=… commit`.
   파일은 LF로 쓴다. `check`는 커밋 둘 이상(이동 card를 하나씩 적용한 커밋들 + shim 삭제 커밋 -- 계약 8 (b)(c)).
3. 가짜 N3.10 표: `### N3.10 ` 제목 + `| ID | 파일 | 책임 | 대표 대상 |`(`mod_table`은 `MOD<n>`·`` `<파일>.py` ``만 받는다 -- 다른 모양이면 exit 2). 대표 대상에 식별자·글롭(`*` 하나)·`<파일>.py`·`<모듈>.<이름>`·
   무시할 기호(예 `∂X/∂Y`)·산문을 섞는다(oracle (a)).
4. 가짜 레지스트리: `| 함수 | 책임 | 이관 목적지 | 비고 |` 표 + **목적지 열 없는 `| 함수 | 파일 | … |` 표 하나를 미끼로**(키트 v9 정의 -- 미끼 행이 배정·`reg_mismatch`에 영향 0이어야 한다),
   목적지 셀에 MOD 이름·옛 이름(`--aliases`)·`〃`·두 MOD·빈 셀, 5열 표(`처리` 열)도 하나.
5. 필수 합성 단계(card 'oracle' 절): v6 `order-split-n310-lower`·`shim-partial-move`·`shim-complete`(i)(ii)·`shim-all-mode`, v7 `import-time-high` (i)~(v)((iii)는 future 유무 둘 -- 시제품 구성:
   N3.10 MOD1 낮은 층·MOD2 split이자 N3.10(s)·MOD3(j)·MOD4(k), 배정은 A-1 토큰으로 고정하고 다른 목록이 빈지 함께 단언해야 exit 1이 `import_time_high` 하나 때문임을 보인다).
   각 단계는 **구성으로 기대가 정해진다** -- 도구 출력에서 기대값을 만들지 않는다.
6. 그 밖의 계약: A-0~A-5와 우선순위·고정점(A-2·A-3·A-5가 서로 기대는 구성), 단위 키(함수·클래스 = 이름, 문장 = 바인딩 이름 정렬 `,` 연결, 무바인딩 = `<stmt:해시12>` -- 해시 값을 손으로 만들 수
   없으면 접두 `<stmt:` 모양만), `reexports` 모양(`from <줄기> import a, _b` 이름순, `_` 포함), `order`, `absent_split`(shim 지운 커밋에서 exit ≠ 2), `reg_mismatch`, `upward`·`cycles`·`unassigned`·
   `conflicts`, `check` 발견 종류 키 10개 항상 있음, 각 발견의 거부 구성(card '거부해야 할 입력' 목록)과 **거부하지 않아야 할 것**(v6), exit 2 경우들(오류 JSON `{"tool","verdict":"ERROR","error"}`),
   무동작(base = head `check`: `move-set` 외 발견 0).
7. 이름: 가짜 모듈·함수 이름만(회로·넷·소자·실제 엔진 모듈 이름 금지 -- 계약 7 '합성 입력에서 모든 계약 성립'). test 함수마다 if·try 밖 assert ≥ 1.

**자기 실행**: `PT3`로 이 파일만 -- 도구가 없으니 전부 FAIL이어야 한다(red). 하나라도 PASS면 존재 단언이 빠진 것.
**소요 예상**: 작성 90~120분(단계 수가 많다 -- 시제품 6단계 = 90줄), 자기 실행 수십 초.

---

## 2. gmid-code-author 브리프(순서 5)

```
역할: gmid-code-author. change id = 20260930-p3-move-plan-tool (red-green).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p3-move-plan-tool-code (브랜치 role/code/20260930-p3-move-plan-tool, 부모 = T). 절대 경로만.
쓰기 경로: tools/migrate/move_plan.py 하나(계획 N3.12.2 tools/migrate/**). tools/gates/**·tests/**·문서는 쓰지 않는다.
입력: spec card·interface card. test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20260930-p3-move-plan-tool.md) 커밋 후 멈춘다.
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20260930-p3-move-plan-tool" -m "…"
```

**만들 것 / 지킬 것**
1. `main(argv) -> int`(card 시그니처 -- `sys.exit`는 `if __name__ == "__main__":`에서만). 출력은 stdout JSON 한 줄, 첫 키 `tool`·`command`·`verdict`. 오류도 JSON 한 줄 + exit 2(argparse 오류 포함 --
   기본 argparse는 JSON 없이 exit 2를 낸다).
2. 게이트 모듈은 `--root`의 `tools/gates`를 `sys.path` 앞에 넣고 import(도구 파일 위치와 무관). 재사용 6개(계약 5) -- `mod_table`·`read_section_table`·`read_tree`·`SourceIndex`·`moved_defs`·
   `_is_empty_dict`. 같은 개념을 다시 만들지 않는다. AST는 0.3 결정의 공개 이름으로(내부 속성 금지).
3. 계약 5·7: `hashlib`·`symtable` import 0, `ast.dump` 호출 0(문장 비교는 `reachability.def_hash`), 파일 텍스트 어디에도(주석·docstring 포함) `library`·`topology.json`·`sizing_recipe`·
   `stick_diagram`·`topology_library`·`design_report`·`optimizer` 0 -- **`library`는 부분 문자열**이라 `lru_cache` 설명·예시 문장도 조심. 사용 예는 가짜 이름.
4. 계약 6: 커밋마다 `SourceIndex` 하나(`plan` 1, `check` 2 -- base 색인을 `plan` 계산과 `moved_defs`가 같이 씀), `read_tree` `plan` 1·`check` 2, `moved_defs` `check` 1. 반복 안 질의는
   색인 캐시로(바인딩 이름 → 단위 사전은 한 번 만든다 -- 시제품 실측 실제 저장소 `plan` 26초).
5. 레지스트리 함수 표 = 머리에 `함수`·`이관 목적지`가 둘 다 있는 표 전부(키트 v9 정의), 열 위치는 머리에서, `〃` = 위 행 셀(같은 표 안). 표 읽기는 도구 안(레지스트리 제목이 되풀이되어
   `read_section_table` 불가). 칸 나누기는 `\|` 이스케이프 규칙(`role_paths._split_cells`와 같게).
6. A-1 토큰 분류 순서: `<이름>.py` → 파일, `<모듈>.<이름>` → 이름, 식별자(`*` 하나 허용) → 이름/글롭, 나머지 무시. 문장 단위는 바인딩 이름 중 하나가 맞으면 그 단위.
7. 고정점: A-2·A-3·A-5 반복(상한을 두고, 상한에 닿으면 조용히 끝내지 말 것). 참조자가 아직 배정되지 않은 단위는 다음 반복에서 다시 본다. 끝까지 없으면 `unassigned`(조용한 기본값 금지).
8. `import_time_high`: s = split이면서 N3.10인 파일 번호의 최솟값. 함수 = 데코레이터·기본값(+ 그 파일에 `from __future__ import annotations`가 없으면 인자·반환 주석), 클래스 = 데코레이터·기반·키워드 +
   메서드 몸체 밖 클래스 몸체 전부(메서드 머리는 함수 규칙), 문장 = 전체(lambda 몸체 제외, 주석 대입의 주석은 future 없을 때만).
9. 단위 키 충돌(card가 정하지 않음 -- 0.1 마지막 행): 겹치면 조용히 덮지 말고 오류 또는 구분(덮으면 배정이 사라진다). 고른 방식을 dispute가 아닌 커밋 메시지에 적는다.
10. 광범위 `except` 금지. 새 import는 표준 라이브러리 + 게이트 모듈뿐.

**자기 확인(판정 아님)**: `PT3`로 `tooling/test_move_plan.py` 전부 PASS. 실제 저장소 `MP_ARGS`로 `plan` exit ≠ 2(card 계약 8 (a)).

---

## 3. gmid-verification-auditor 브리프(순서 3·7)

```
역할: gmid-verification-auditor. change id = 20260930-p3-move-plan-tool, red-green, phase 3.
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-p3-move-plan-tool-audit (브랜치 role/audit/20260930-p3-move-plan-tool).
격리 복제본에서만, scratch 새 C:/g<n> 하나(끝나면 그 폴더만 삭제), set -euo pipefail, git -C 절대 경로. 실제 저장소 status·reflog 불변 확인.
게이트 코드 = base 판(gate master, G1 병합 뒤) 캐시. 작성자 보고는 증거가 아니다. 판정 기록 .ai/verification/20260930-p3-move-plan-tool.json + {scripts,out}/, Role: audit 커밋.
```

### 3.1 순서 3(freeze·base 확인)
* T 고정, `git diff --name-only <base> <T>` = `tests/tooling/test_move_plan.py` 하나.
* red: base(도구 없음)에서 그 파일 `PT3 --gmid-strict=` → **모든 test FAIL, 원인 = 도구 존재 단언**(수집 오류 0 -- `-p merge_gate --continue-on-collection-errors`·`GMID_RED_CAPTURE`로 기록,
  `failure_hashes` = base 판 `merge_gate.red_failure_hash`). exit 2를 기대하는 test가 `can't open file`로 통과하면 test 결함(계약 10).
* oracle 대조 준비: v6·v7 필수 단계가 모두 있는지(단계 이름 또는 구성으로), 각 기대가 구성에서 왔는지.

### 3.2 순서 7(병합본 판정)

| V | 기대 | 증거 |
|---|---|---|
| V1 | PASS. 전체 `PT3 --gmid-strict=`(card phase 3), base 대비 새 test만 늘고 나머지 같음 | base·병합본 전체 실행 대조(각 6~7분) |
| V2 | PASS red-green: red 집합 = 새 파일 test 전부(3.1), green = 병합본 전부 PASS | 3.1 기록 + 병합본 실행 |
| V3 | PASS `targets []` -- `tools/migrate`는 `_is_source` 밖(선례 `20260922-ts1-extract-tool` V3 DESIGN-GAP 문장). 보조 측정(판정 입력 아님): 캐시 `mutate_changed.mutants()`로 도구 def 변이를 새 test로 판정한 생존 수 | `mutate_changed.py … --gmid-phase=3 --gmid-strict=` |
| V4 | PASS. `--interface-card`(생성본 -- '기존 함수 0개'인지 먼저 확인) + `--module-dir tools/migrate`. findings NO-SUBJECT만이면 basis는 oracle 대조 문장으로(단계마다 card 문장·구성) | `test_lint.py --root --base --head --interface-card <card> --module-dir tools/migrate` |
| V5 | PASS `diff_paths []`(새 파일) | `weakening_diff.py` |
| V6 | PASS. 도구 파일은 V6 대상 밖이면 `targets []` -- 그래도 광범위 except 0을 직접 grep | `source_lint.py` + AST |
| V7 | PASS `new_defs []`(그래프 밖) -- 배선 관찰은 card 계약 9: D0b test·M card equivalence·DoD E2·E4·E6가 부른다(지금은 D0b 전 -- 계약 9 (i)이 없으면 D0b가 막는다) | `reachability.py` |
| V8·V9 | N/A(도입 4·6b) | -- |
| V10 | PASS, 재현 수치 없음. **계약 확인 측정**(probe, 병합본 도구, 기대값은 card 문장): 계약 5(AST: `hashlib`·`symtable` import 0, `ast.dump` 0, `def mod_table`·`def moved_defs`·`def binding_origin` 0), 계약 6(`cProfile` 합성 입력 -- `SourceIndex` 생성 `plan` 1·`check` 2, `read_tree` 1·2, `moved_defs` 0·1, **모듈 파싱 `mode="exec"` ≤ 색인 파일 수** -- G1 문자열 주석 eval 파싱 제외, 키트 v9 문언), 계약 7(`git grep` 0건), 계약 8 (a)(실제 저장소 `MP_ARGS` exit ≠ 2 -- 관찰, 사전 측정 exit 1·`import_time_high` []), 레지스트리 미끼 표 무영향 | auditor 스크립트 |

판정 기록 `approvals` = `["20260930-30-module-split-design"]`. M card·DoD가 실행할 사본의 출처 = 이 판정 기록의 `code_commit`(card 계약 1) -- 기록에 그 sha와 파일 sha256을 적는다.

---

## 4. 순서 요약(오케스트레이터)

design 30 승인 → (B34 → b26pre → backfill → B26-1 → B33) → **G1 병합(0.3 결정 반영)** → 착수 0단계 → spec card(rev 갱신) + interface card(절대 경로, 기존 함수 0개 확인) → 순서 1 test worktree →
test-author(1절) → 순서 3 auditor(3.1) → 순서 4 code worktree → code-author(2절) → 순서 6 병합 → 순서 7 auditor(3.2) → push 단독·전체 출력 확인 → 정리 → D0b.

## 5. 키트 파일(`_drafts/p3kit_d0a/`)

| 파일 | 내용 |
|---|---|
| `move_plan_proto.py` | `plan` 시제품(계약 1·2·3, G1 시제품 SourceIndex 사용, 내부 속성으로 AST 접근) -- **역할에게 건네지 않는다** |
| `gen_ith.py` | v7 `import-time-high` 6단계 합성 저장소 생성·실행 → `out/ith_stages.jsonl` |
| `test_move_plan.proto.py` | red/green·V4 모양 확인용 시제품 test(6단계) -- **역할에게 건네지 않는다** |
| `count_calls.py` | 계약 6 관찰(`ast.parse` mode별·`read_tree`·`SourceIndex` 호출 수) → `out/calls_base.json` |
| `v_tools.sh` | V3·V4(`--interface-card` + `--module-dir tools/migrate`)·V5·V6·V7 → `out/vtools/` |
| `out/plan_base_19eb475.json` | 실제 저장소 `plan` 시제품 출력(관찰) |
| `out/red_T.txt`, `out/green_K.txt` | 시제품 test red(6 failed)·green(6 passed) |
| `out/d0a.interface.generated.md`, `out/iface_proto.md` | 키트 반영 초안으로 생성한 interface card(기존 함수 0개), V4 시험용 card |
