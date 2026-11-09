# review_p3_f2_cur -- F2 초안(`draft_p3_f2.spec.md`, 2026-10-06 갱신판)과 F1 r4 초안(`draft_p3_f1.spec.md`, 읽기 전용) 대조 자기 점검표

작성 2026-10-06. 판 = gate `master` `7243f28`. 근거 실측 = F2 초안 '작성 전 실측' 머리 '(gate master 7243f28 재측정 2026-10-06)'(격리 복제본 `C:/g305`, 작업 끝에 삭제).
독립 검토 형식이지만 **작성자 자신이 쓴 점검표**다(작성자≠검증자 -- 이 목록은 판정 근거가 아니고 독립 검토자의 출발점이다).
등급: **S** = 계약 문언이 F1과 어긋나거나 판정이 빗나갈 수 있음(계약 변경 -- 오케스트레이터 결정), **m** = 사실 문장·표현 불일치, **OK** = 대조해 일치 확인(기록용).
이번 갱신에서 고친 것은 사실 문장뿐이고 계약(`## 관찰 가능한 계약` 절)은 바이트 같다(md5 `10740404…` 전·후 같음). 아래 S 항목은 **고치지 않고** 올린다.

## A. F1 TS6 (마) 규칙과의 대조

| # | 등급 | 내용 | 근거 | 권고 |
|---|---|---|---|---|
| A1 | OK(이번에 문장 추가) | F2는 `A/tests/tools/derive_achievable_bounds.py`를 바꾸지 않으므로 F1 '핀 변경 규칙'(정규형을 바꾸지 않는 card는 핀 불변)대로 TS6 핀을 고치지 않는다. F2 계약 1('그 밖의 바뀐 줄 0', test 커밋 = 새 파일 하나)이 그것을 이미 강제한다. | F1 계약 1 (d) '핀 변경 규칙' 끝 문장, F2 계약 1·12 | F2 결정 필요 항목 4에 (마) 결정 완료·핀 불변 문장을 넣었다(이번 갱신). |
| A2 | m | F2 뒤 env_HEAD의 모듈 집합 M에서 shim 셋이 빠진다. F1 (A3) 정규형의 별칭표는 `X ∈ M`인 import만 엔진 별칭으로 본다 -- F1 병합본 도구에 shim import가 하나라도 남으면 F2 뒤 그 별칭이 표에서 빠져 N(HEAD)이 바뀌고 TS6 test가 F2 병합본에서 FAIL한다. F1 계약 5 (a)(E3 AST 0)가 그것을 막으므로 정상 경로에서는 같지만, **실측이 없다**(모의 F1은 (마) 규칙을 적용하지 않았다). | F1 계약 1 (d) (A3) 1·2 (c), F1 계약 5 (a) | F2 auditor는 PT3에서 `contracts/test_ts6_probe_relocate.py::test_moved_tool_matches_base_except_path_lines`의 F2 base·head 결과(둘 다 passed)를 판정 기록에 따로 적는다 -- 계약 9의 'id 결과 같음'에 이미 들지만 F1 의존 지점이라 이름을 박아 두면 원인 추적이 빠르다(계약 변경 아님, auditor 브리핑 문장). |
| A3 | S | F1 (A1)·(A3)은 test 안에서 `git rev-list --parents`·`git merge-base --is-ancestor`·`git show <pin>:…`·`git ls-tree`를 부르고 **읽기 실패는 거부(닫힌 쪽)**다. 얕은 복제·`git archive` 트리·git 없는 사본에서 PT3를 돌리면 그 test가 base·head 모두 FAIL한다. F2 계약 9 "base는 새 test 2개만 실패 -- 그 밖 id 결과 같음"은 두 판 같은 결과라 동등 판정은 서지만, "head 실패 0"이 깨져 F2 판정이 환경 탓으로 FAIL한다. | F1 계약 1 (d) (A1) (a)~(d), (A3) 핀 커밋 확인 | F2 계약 9(또는 auditor 브리핑)에 'PT3는 전체 이력 복제본(`--no-local` 전체 clone, 얕은 복제 금지)에서' 한 줄. design §10 PT3 함수는 `<iso>`가 전체 clone이라는 전제를 문장으로 두지 않는다 -- F1 쪽 문제이기도 하다(F1 계약 6 (a)도 같다). |
| A4 | m | F2 '거부해야 할 입력'에 'TS6 핀을 고친 head'(F2가 `pin_commit`·`pin_edits`·정수 리터럴을 바꿈)가 없다. 계약 1(바뀐 줄 0)·계약 12(V5 PASS)로 이미 FAIL하므로 판정 공백은 아니다. | F1 계약 1 (d) '핀 변경 규칙', F2 계약 1·12 | 넣으면 F1 규칙과의 연결이 문서상 보인다(선택). |
| A5 | OK | F2 결정 필요 항목 4의 '+9' 목록(F1이 앵커를 안 고치면 F2 뒤 깨지는 test)에 TS6 기준 blob test(668~673)가 없는 것은 맞다 -- 그 test는 F1 모의에서 이미 FAIL하는 F1 몫이다(F1 '작성 전 실측' 4: F1 몫 2 중 하나). | F1 실측 4, F2 결정 4 | -- |
| A6 | OK | F2 결정 필요 항목 5 (i)의 design 정정(§7.1 B군 표에 `test_ts6_probe_relocate.py:668-673`)은 F1 결정 1 'design 정정 항목'과 같은 항목이다. 7243f28 design 30에도 아직 없다(§7.1 B행 570행 재확인). | F1 결정 1 끝, design 30 570행 | 두 card가 같은 정정을 각자 목록에 두므로 정정 커밋 때 한 번만 반영. |

## B. F1 좁힌 쓰기 경로 행과의 대조

| # | 등급 | 내용 | 근거 | 권고 |
|---|---|---|---|---|
| B1 | OK(이번에 문장 갱신) | 두 행(`workspaces/current-reuse-telescopic-ota-report/*.py`·`workspaces/two-stage-ota-report/*.py`, gmid-code-author)은 `fd4ef8c`로 커밋됐다(계획 602·603행). 7243f28 계획의 `plan_tables_hash` = `16b899d1c745…`(gate 7243f28 `merge_gate.plan_tables_hash`로 다시 계산 -- 승인 기록 `target`과 같음). F2 '자리' 문단을 '커밋됨'으로 고쳤다. | 계획 N3.12.2, `.ai/approvals/20261002-p3-f1-workspaces-write-path.md` | -- |
| B2 | OK | F2는 `workspaces/**`를 쓰지 않는다(계약 1) -- 그래서 머리 `approval:`에 `20261002-p3-f1-workspaces-write-path`가 없는 것이 맞다(F1은 둘째 `approval:` 줄을 둔다). F2 '작성 전 실측' 4 '역할 밖 경로 없음'도 맞다. | F1 머리·계약 4, F2 계약 1 | -- |
| B3 | m(질문 후보) | F2 계약 6 판정 범위 = 판정 트리 + `workspaces/run_harness.py`. 근거(결정 필요 항목 3)는 `stick.py`의 이미 깨진 이름 하나(E3b `pre_existing`)다. F1이 좁힌 두 행으로 그 두 폴더 바로 아래 16파일을 **역할 커밋으로 관리하게 된 지금**, 상시 test가 그 16파일을 빼는 것은 'F1이 고친 곳을 F2 뒤 V1이 매번 보지 않는다'는 뜻이다(DoD E3·E3b는 Phase 3 끝 한 번). 대안: 범위에 두 폴더 `*.py`를 넣고 `(stick.py, block_from_row_widths)` 한 쌍만 base에서 이미 풀리지 않던 이름으로 빼는 판(E3b `pre_existing`과 같은 정의 -- base에서 계산). | F2 결정 3, F1 계약 4·실측 10 | 판정 범위를 넓히는 계약 변경이라 오케스트레이터 결정. 기본안 유지도 원칙상 성립(DoD 판정은 줄지 않음) -- 다만 결정 3 문장에 'F1 좁힌 두 행으로 관리되는 16파일도 상시 test 밖'을 명시해야 사실이 맞다. |
| B4 | OK | `stick.py` `block_from_row_widths`(F2 결정 3·계약 4 `pre_existing` 1)는 F1이 옮기지 않는다 -- F1은 SD 삭제 집합(49) 이름만 옮기고 그 이름은 SD에 없어 삭제 집합 밖이다. 모의 F1 `43b9d43`의 `stick.py`도 그 이름을 `from stick_diagram import …`에 그대로 둔다 → F2 head `pre_existing=1`(7243f28 실측). | F1 계약 1 (b)·2 (vi), 재측정 E3b | -- |

## C. 그 밖 F1 r4 문언과의 대조

| # | 등급 | 내용 | 근거 | 권고 |
|---|---|---|---|---|
| C1 | S | **V3 판정 문언**: F1 계약 8은 card 35 병합 판 출력 키를 모두 적는다(`defs` []·`moved` []·`move_rejected` {}; 범위 정책 `not_targeted` 0·`targets_by_def` {}). F2 계약 12는 'V3 대상 def 0·변이 0'뿐이다. 7243f28 사슬 실측(base `43b9d43` → head `d42f269`, card 35 + G1 시제품): `targets` [ACF, SD]·`mutants` 0·`not_targeted` 0·`targets_by_def` {}·`defs` []·`moved` []·`move_rejected` {}. V6·V7도 `moved` []·`move_rejected` {}. | F1 계약 8 첫 줄, F2 계약 12, 재측정 V 도구 | F2 계약 12를 F1과 같은 키 목록으로(계약 문언 변경 -- 이번 갱신에서 하지 않음). `targets`가 [ACF, SD]인데 `not_targeted` 0인 것은 바뀐 문장이 모듈 수준 import뿐이라 def 대상이 없기 때문(관찰). |
| C2 | S | **F2 계약 6 (b)의 reader 정의가 E3b·F1 (바)보다 좁다**: (b)는 `from stick_diagram import N`과 `import stick_diagram [as a]`의 `a.N`만 본다. design §10 `E3B_AST`의 `file_reads`는 `import_module("stick_diagram")` 결과와 **그것을 돌려주는 함수 호출**(예 `_sd()`)의 속성까지 본다. F1은 `contracts/test_dup_kcl_edges.py:35` `_sd()`를 계약 3 (바) 목록 단위(탈출 자리)로 다룬다. 실측(F1 없는 F2 `e71da7c`): E3b FAIL 49줄 중 판정 트리+하네스 몫은 40줄(그중 `test_dup_kcl_edges.py:274·293` `_sd()._kcl_and_matching_edges` 2줄; 나머지 9줄은 범위 밖 workspaces 두 폴더)인데 시제품 (b)는 **38**만 잡는다(그 두 줄을 놓침). | design 30 §10 E3B `file_reads`(블록 91행 주석), F1 계약 3 (바)·결정 2, 재측정 | 계약 6 (b)의 읽기 정의를 E3b `file_reads`와 같게(import 호출 결과·그것을 돌려주는 함수 포함) -- 오케스트레이터 결정. 놓친 자리는 PT3 수집 test라 V1이 실행 실패로 잡으므로 판정 공백은 작지만, '상시 판 = E3b의 판정 트리 몫'(F2 원칙 '만들면 배선')이라는 문장과 어긋난다. |
| C3 | m | **삭제 집합 계산 판**: F1 계약 1 (b)는 'F2 card 계약 2의 SD·ACF 삭제 집합(F1 base SD·ACF로 계산)', F1 계약 5 (b)는 'F1 병합본 SD·ACF로 계산', F2 계약 2는 'F2 base(= F1 병합본)에서 계산'. F1이 SD·ACF를 바꾸지 않으므로(F1 계약 7) 세 계산은 같아야 하지만 어느 card도 그 등식을 문장으로 두지 않는다. | F1 계약 1 (b)·5 (b)·7, F2 계약 2 | F2 계약 2 또는 auditor 브리핑에 'F1 base·F1 병합본·F2 base의 SD·ACF 블롭 같음(F1 계약 7) → 세 삭제 집합 같음, 다르면 멈춤' 확인 한 줄(선택). |
| C4 | m | **ACF 삭제 이름 reader의 상시 판 없음**: F1은 'E3b는 SD만 보므로 ACF reader는 이 card(F1)가 판정'이라 적는다(F1 계약 1 (b)). F2 계약 6은 SD만 본다. 그래서 ACF 삭제 이름(`_as_set`·`_theta_evidence_for_pair`)을 ACF 경유로 읽는 새 파일은 F2 뒤 어느 상시 test도 보지 않는다(지금 reader 0 -- `git grep audit_current_forced` `7243f28`: import 0, 문자열 3). | F1 계약 1 (b), F2 계약 6·결정 1 | 기록만(실제 위험 낮음). ACF를 (b)의 대상 모듈에 더하면 닫힌다(계약 변경). |
| C5 | m | **E-INST 같음 정의**: F1 계약 6 (b)는 'stdout 사본은 `elapsed=<n>s`를 가리면 같다'까지 적고, F2 계약 9는 출력 JSON(`engine_origin` 밖)만 적는다. | F1 계약 6 (b), F2 계약 9 | 같은 정의로 맞추기(선택). |
| C6 | OK | 앵커 규칙(F1 계약 2 (iv))과 F2 head: 부재·경로 앵커 5줄 → 'N3.10 MOD 파일 전부 있다'(F2 head에 M10 있음 -- 계약 5 `present` 10), 정의 앵커 → R-DEF 파일, import 앵커의 엔진 모듈 집합 = N3.10 ∪ '그 트리에 있는' shim 줄기 → F2 뒤 shim 줄기가 빠져도 `regression_runner`는 F1 뒤 MOD를 import하므로 참. F2 계약 13 E5 행 '앞 card에 기대는 것'과 맞다. | F1 계약 2 (iv), F2 계약 5·13 | F2 계약 13 E5 행의 'F1 계약 1 (c)(d)'를 '(c)(d) -- 규칙 원문 계약 2 (iv)(v)'로 적으면 참조가 정확해진다(m, 선택). |
| C7 | OK | IMPORT-ANY: F1 모의 `tried=13`, F2 모의 `tried=10`(7243f28 재측정 같음). F2 계약 7 'F1보다 3 적다'와 맞다(M10이 있는 실제 판에서는 둘 다 +1). | F1 실측 6, 재측정 | -- |
| C8 | m(F1 쪽) | **계획 줄 번호 +2**: `fd4ef8c`가 계획 602·603행에 두 행을 넣어 그 뒤 줄이 +2다. F1 r4는 '계획 991행'(→ 993)·'686행'(→ 688)·'680·686행'(→ 682·688)을 인용한다(7243f28 `sed -n` 확인: 문장 같고 번호만 +2). F2는 534행만 인용하고 삽입 앞이라 그대로다(F2 재측정 단락에 적음). | 계획 `4a286f0` vs `7243f28` | F1 갱신 때 번호 정정(F1은 이 작업에서 읽기 전용이라 고치지 않음). |
| C9 | OK | F2 '자리' -- F1 착수 조건 (1)(두 행 gate master 존재)은 이제 성립한다. F1 착수 조건 (2)(T0)·(3)(D-17·S1)은 F2 base가 F1 병합본이라 F2에 새 조건을 만들지 않는다. | F1 착수 조건 (1)~(3) | -- |

## D. 재측정에서 본 그 밖 사항(F1 무관)

* D1 (m) `p3kit_f12/mk_chain_r1.sh`는 `4a286f0`에 card 35 뒤 `install_proto.py`를 설치하려다 exit 1 -- 사슬 스크립트를 `7243f28`·토큰 단계 생략 판으로 고쳐 두면 다음 재측정이 손 단계 없이 돈다(이번엔 스크래치 사본으로 돌리고 지웠다; `_drafts` 쓰기 범위 밖이라 고치지 않음).
* D2 (m) 사슬 셸에 `APPDATA`가 없으면 `sim_m_d31.py`의 import 확인이 `numpy` 부재로 전부 실패로 찍힌다(산출 파일은 같음 -- 재실행으로 확인). 사슬 스크립트 머리에 `export APPDATA HOME`.
* D3 (m) F1 없는 F2 쌍(`68ac251 → e71da7c`)의 V3가 `ERROR`(`git checkout: --detach does not take a path argument 'e71da7c'`) -- 같은 커밋을 다른 worktree가 잡고 있던 측정 환경 탓으로 보이나 원인 미확정. F2 판정 쌍(`43b9d43 → d42f269`)은 PASS. auditor 격리 복제본에서는 worktree 공유가 없어야 한다.
* D4 (OK) parse_spec_card(gate `7243f28` `tools/gates/role_paths.py`): 갱신 전·후 모두 파싱 성공 -- `id` `20261002-p3-shim-delete`, `phase` 3, `evidence_type` red-green, `gate_change` no, `approval` [`20260930-30-module-split-design`], 11절.

* D5 (S -- 판) 측정 중 실제 저장소 `master`가 `7243f28` → `2183f2e`(B34 병합 `c851e54`·판정 기록)로 fast-forward됐다(이 작업은 실제 저장소에 읽기만 했다 -- `status --porcelain` 시작과 같음). B34가 SR 5줄·SD 70줄(함수 본문)을 바꾸고 새 계약 test를 더하므로, F2·F1 모의 수치(배정 403, SD 재수출 57/49, E3/E3b, IMPORT-ANY)는 `2183f2e` 위 사슬로 다시 재야 한다. 새 test `test_b34_grammar_explicit.py`가 SR·SD를 어떤 경로로 import하는지가 F1 대상(계약 1 (a)(b))에 들어가는지도 그때 잰다.

## 요약

S 3건(A3 PT3 전체 이력 전제, C1 V3 출력 키 문언, C2 계약 6 (b) reader 정의) -- 모두 계약 변경이라 이번 갱신에서 고치지 않았다. 그리고 판 이동 D5(B34 병합 `2183f2e` -- 수치 재측정 필요). m 10건(A2·A4·B3·C3·C4·C5·C8·D1·D2·D3), OK 10건(A1·A5·A6·B1·B2·B4·C6·C7·C9·D4).
F1 TS6 (마) 규칙과 좁힌 쓰기 경로 행에 대해 F2가 **어긋나는 계약은 없다** -- F2는 그 도구·그 폴더를 건드리지 않으므로 둘 다 '건드리지 않음'으로 따른다. 남는 위험은 (마) test의 git 의존(A3)과 F1 병합본 도구에 shim import가 남는 경우(A2 -- F1 계약 5 (a)가 막음)다.
