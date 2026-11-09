---
id: 20260930-p3-registry-dest
phase: 3
evidence_type: red-green
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split`(초안 v8.3) §6.2 '결과 조건'·§6.4 'D0b 재측정 조건'·§8 D0b 행, card D0b. 계획 N3.10 517행 "Phase 3 design 문서가 그 열(레지스트리 '이관 목적지')에서
이관표와 실제 의존 그래프를 생성한다"를 **실제 저장소에서 끝낸다**: D0a 도구 `tools/migrate/move_plan.py plan`이 낸 단위 → MOD 배정(이관표)을 레지스트리
`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`의 '이관 목적지' 열에 옮겨 적고(+ `근거 규칙` 열), 그 열이 도구 출력과 같다는 것과
이동 전 계층 사전 검사(PLAN-LAYER)·D-22 전제(`import_time_high`)를 **새 계약 test** `A/tests/contracts/test_p3_registry_dest.py`가 Phase 3의 모든 card V1에서 단언하게 한다.
A = `skills/analog-gmid-design/assets`. 지금 열은 N3.10 이전 판 이름을 쓴다(design §6.1: MOD 이름 없는 셀 62, MOD1·5·6 행 0, 두 MOD 셀 16).

이 card가 하는 일은 셋이다. (1) **이관표 확정**: D0b 자신의 base(B34 → b26pre → backfill → B26-1 → B33 → G1 → D0a가 모두 병합된 gate `master` -- design §6.4·§8.1)에서
`plan`을 처음 계산한다. 그 전의 `plan` 출력(D0a 계약 8 (a), 이 card '작성 전 실측')은 관찰이지 이관표가 아니다. (2) **레지스트리 열 재생성**(code-author):
대상 행의 목적지 칸 = 도구가 배정한 MOD 파일 줄기 하나, `근거 규칙` 칸 = 그때의 규칙 ID. 레지스트리 §7 `보류(Phase 3)` 9행의 처리 열 = `보류(Phase 4)`(D-10 -- 옮기고 D 유지).
(3) **계약 test**(test-author): `plan` exit 0과 판정 목록 전부 빈 목록, 레지스트리 열 = 도구 출력, MOD7 배정은 MOD7 파일의 단위뿐, `import_time_high` 빈 목록.
**손으로 쓰지 않는다**: 목적지 칸은 도구 출력과 바이트로 같아야 하고 test가 대상 행 전부를 대조한다(계약 6). 규칙으로 풀리지 않는 충돌은 열을 고쳐 덮지 않고
**멈춘다**(계약 8) -- UD-0이 덮는 N3.10 개정은 3건 + D-19뿐이고 그 밖의 개정은 따로 사용자 승인을 받는다(design D-11).
원칙: test는 코드 구조·계획서·레지스트리만 읽는다(topology 무관 -- 회로·넷·소자 이름, `library/`·`*.topology.json` 없음). 엔진 파일 이름은 design §6.3 `MP_ARGS`의
인자로만 쓰고, MOD 파일 이름은 계획서 N3.10 표(`import_layering.mod_table`)에서 읽는다. 숫자 임계값 없음(판정 목록이 빈지, 칸이 같은지만 -- WP-03).
**동결 시작**: 이 card 병합부터 F2 병합까지 엔진 파일(`A/*.py`, `workspaces/run_harness.py`)·`tools/gates/**`·`tools/migrate/**`·레지스트리 '이관 목적지' 열을 바꾸는
Phase 3 밖 card는 병합하지 않는다(design D-27). 그런 card가 병합되면 이 card의 계약 test가 `reg_mismatch`로 깨지고 D0b를 다시 계산한다(레지스트리 열 재생성 card).
병합은 **Phase 2 DoD PASS 뒤**(`phase: 3` card -- 계획 991행, design D-23, 확정 순서상 자동 성립)이고 D0a 병합 뒤다. 그 전에는 spec card 초안·작성 전 실측만 한다.

## 관찰 가능한 계약

1. **범위**(이 card `Change-Id` 커밋들의 diff로 한정): code 커밋이 바꾸는 파일 = 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 하나,
   test 커밋이 더하는 파일 = `A/tests/contracts/test_p3_registry_dest.py` 하나. 엔진(`A/*.py`, `workspaces/run_harness.py`)·`tools/**`·계획서·design 문서 변경 0.
   N3.10 추가 개정이 필요하면 이 card 커밋이 아니라 별도 승인 기록과 오케스트레이터 문서 커밋으로 들어간다(계약 8).
2. **이관표 = 도구 출력**. 이관표의 정본은 D0a 계약 1 CLI를 design 30 §6.3 `MP_ARGS` 그대로(bash 배열 -- `--split` 다섯·`--keep` 하나·`--aliases` JSON) `--rev HEAD`로
   돌린 `plan` 출력의 `assignment`(단위 키 → `mod`·`rule`)다. 실행하는 도구는 그 커밋의 `tools/migrate/move_plan.py`다(D0b~F2에 `tools/**` 변경 0 -- design D-16·D-27 --
   이라 판정 기록 사본 `code_commit` 판과 같은 파일이다). 레지스트리 열은 이관표 중 레지스트리 행이 있는 단위의 사본이다(레지스트리에 행이 없는 정의·최상위 문장은 열에 없고
   도구 출력에만 있다 -- 그래서 열만으로 이관표를 다시 만들지 않는다). Phase 진행 중에도 규칙 A-0(D0a 계약 2·8 (b))으로 같은 사상이 나온다.
3. **`plan` 판정**(이 card 병합본, 그리고 그 뒤 Phase 3 모든 card의 병합본 -- 배선): exit 0, `verdict` = `PASS`, `upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`·
   `import_time_high` 여섯 목록이 모두 빈 목록. `absent_split`은 판정하지 않는다(F2 뒤 shim 파일 부재는 오류가 아니다 -- D0a 계약 8 (c)).
4. **`import_time_high` = []**(design §2.2 D-22 (2)의 전제 -- 4차 검토 S5, 키 정의는 D0a 계약 2): 배정 MOD 번호가 위쪽 재수출을 받는 split 파일 번호보다 큰 단위가
   import 시점(데코레이터·기본값·`__future__` 없는 파일의 주석·클래스 몸체·모듈 문장)에 그 번호 이상 MOD의 이름을 읽지 않는다. 이 목록이 비어 있어야 MOD8·MOD9의
   번호 7 이상 모듈 import를 파일 끝에 두는 D-22 배치가 `NameError` 없이 성립한다. 계약 3과 별도로 적는 이유: 위반은 import 줄 위치로 풀 수 없고(머리 배치 = 순환,
   끝 배치 = `NameError`, 함수 안 지연 import = 금지 -- design F3) **배정을 바꿔야** 하므로 멈춤 경로가 계약 8 (b)로 따로다.
5. **MOD7은 자기 파일의 단위만**(design 3차 검토 m4 -- 옮길 card가 없다): `assignment`에서 `mod`가 N3.10 MOD7 파일(계획서 `mod_table`에서 번호 7의 줄기 + `.py`)인 단위는
   전부 키의 파일 부분이 그 파일이다. split 파일 중 MOD7 파일 밖 단위가 MOD7로 배정되면 FAIL.
6. **레지스트리 열 모양**(code 커밋이 만든다, test가 대조한다). '레지스트리 함수 표' = 머리에 `함수` 열과 `이관 목적지` 열이 **둘 다** 있는 표 전부(D0a 계약 2 A-4 정의 그대로 --
   열 위치는 머리에서 찾는다, 칸 나누기는 `\|`가 칸 안 문자). 그 표마다:
   (a) 머리에서 `이관 목적지` 바로 뒤에 `근거 규칙` 열이 있다(구분선 칸 수도 같이 는다).
   (b) **대상 행** = 함수 칸 첫 백틱 토큰의 `.` 앞(메서드 행 `Class.method`는 클래스)이 `assignment` 단위 키의 `::` 뒤 부분과 같은 행. 대상 행의 `이관 목적지` 칸 =
       그 단위 `mod`의 줄기(`.py` 없이, 백틱·공백·다른 글자 없이 정확히 그 문자열). `〃` 금지(대상 행마다 명시). 같은 키에 단위가 둘 이상이고 `mod`가 갈리면 FAIL(지금 0 -- 실측 1).
   (c) 대상 행의 `근거 규칙` 칸 = `A-0`~`A-5` 중 하나(형식만 test가 본다 -- 값은 재생성 시점 `plan`의 `rule`이고 auditor가 V10에서 D0b base 출력과 대조한다. 재생성 뒤에는 열이
       A-4 입력이 되어 도구의 `rule`이 바뀔 수 있으므로(실측 5) test가 현재 `rule`과 대조하지 않는다).
   (d) **중첩 행**(함수 칸이 `└`로 시작하는 하위 def 표기)과 **비대상 행**(키에 맞는 단위가 `--split`·N3.10 파일에 없는 행 -- 하네스·LUT 생성 도구·`topology_to_markdown` 등,
       실측 1)은 `이관 목적지` 칸 불변, `근거 규칙` 칸 `-`. 불변은 auditor가 base 대비 diff로 본다(test는 base를 모른다). (결정 필요 D0b-3)
   (e) 대상 행 수 > 0, 레지스트리 함수 표 수 > 0(공허 통과 방지).
7. **§7 처리 열**(design D-10, U-02 승인 `20260923-u02-d-list` 1항): 레지스트리에 `보류(Phase 3)` 문자열 0개. base에서 `보류(Phase 3)`이던 행(지금 9행)은 `보류(Phase 4)`이고
   그 밖의 처리 칸은 불변(auditor diff). 기존 `tests/tools/reg_check.py`(`disposition`·`count`·`stale`)는 재생성 뒤에도 발견 0이어야 한다(V1의 `test_reg_check.py`가 실제 저장소로 돈다).
8. **멈춤 조건(열을 쓰기 전 -- code-author가 아니라 오케스트레이터 절차, design §6.2·§9.1·D-11)**: D0b base에서 `plan`을 돌려
   (a) `conflicts`·`upward`·`cycles`·`unassigned` 중 비지 않은 것이 있으면 열을 쓰지 않는다. 오케스트레이터가 해소안(N3.10 '대표 대상' 토큰 개정 diff 또는 design §6.2 규칙 개정)을
   만들어 사용자 승인(`target_kind: diff`, UD-0 밖 -- 위임받지 않음)을 받고 문서 커밋으로 병합한 뒤 다시 계산한다. 그 승인 id를 이 card 머리 `approval` 줄에 더한다.
   (b) `import_time_high`가 비지 않으면 같은 경로로 **배정**을 바꾼다(위치 규칙으로 풀지 않는다 -- 계약 4).
   (c) MOD7 파일 밖 단위의 MOD7 배정이 있으면 같은 경로(N3.10 개정) 또는 M7을 실제 card로 두는 design 개정(design 3차 검토 m4 -- 결정 필요 D0b-7).
   (d) `reg_mismatch`만 비어 있지 않으면 멈추지 않는다 -- 그것이 이 card가 고치는 red다.
   이 card의 test·code 커밋은 (a)~(c)가 모두 빈 base(= 그 해소 문서 커밋이 병합된 gate `master`)에서 만든다. **지금 실측으로는 (a)가 비어 있지 않다**(작성 전 실측 3·4 -- 결정 필요 D0b-1·D0b-2).
9. **재생성 멱등**(손 편집 방지의 두 번째 선, auditor V10): 재생성 전 커밋(D0b base)의 `plan` `assignment`에서 (단위 키 → `mod`) 사상 = 병합본 `plan`의 사상(파일 부분·`rule`은
   비교에서 뺀다 -- D0a 계약 8 (b)와 같은 비교). 열이 A-4 입력이 되어도 배정이 바뀌지 않아야 한다(계층 위반이 0일 때 성립 -- 실측 5).
10. **이관표 산출물**(M card '작성 전 실측'의 한 벌 -- design §8.1 "D0b 이관표 한 벌에서 결정적으로"): auditor가 판정 기록 `.ai/verification/20260930-p3-registry-dest/out/`에
    D0b base(재생성 전)와 병합본의 `plan` JSON 전체, 그로부터 뽑은 MOD별 단위 목록(`order` 순)·`reexports`(split 파일별 재수출 줄 -- D-22 (1)의 SD MOD8·MOD9 재수출 포함)·
    규칙 분포를 남긴다. 이것은 증거이고 정본이 아니다(정본은 계약 2 -- 언제든 다시 계산된다). M card spec card의 '파일:줄'은 각 M card base에서 이 도구 출력으로 다시 잰다.
11. **test 모양**: (a) **red 조건**: 모든 test 함수는 먼저 레지스트리 함수 표 머리마다 `근거 규칙` 열이 있음을 단언한다 -- base(열 없음)에서 모든 test가 `AssertionError`로
    FAIL(수집 오류 아님). 계약 4·5처럼 base에서 이미 참인 단언(실측 4: base `import_time_high` []·MOD7 밖 0)이 혼자 test가 되면 base에서 통과해 V2 red가 깨진다.
    (b) 도구는 하위 프로세스(인자 목록, 셸 없음 -- `--aliases` JSON이 쪼개지지 않는다)로 부르고, 출력 첫 줄이 JSON이며 `"tool": "move_plan"`임을 단언한 뒤 판정한다(도구가 없거나
    exit 2이면 판정 목록 단언 전에 FAIL -- D0a 계약 10과 같은 이유). (c) `plan`은 test 모듈 실행당 한 번(모듈 범위 캐시, 상한 1 -- 실측 12~19초, NFR-2).
    (d) 저장소 루트는 test 파일 위치에서 계산하고 `--root`로 넘긴다(V1 격리 복제본에서도 같은 판).
    (e) 이름: 보조 함수·상수는 `_p3rd_` 접두. 삭제된 이름 토큰(T0 card 계약 9 목록, `test_d_*` 전수 스캔 대상)과 `print` 판정(`test_ts3_no_print_verdicts`) 없음.
12. **topology·이름 무관**: test 소스에 회로·넷·소자 이름과 `library`·`topology.json` 없음. 엔진 파일 이름은 `MP_ARGS`(design §6.3 정본) 인자 리터럴로만, MOD 파일 이름은
    계획서 `mod_table`에서 읽는다(MOD7 판정 포함). 결정 사실 표본(oracle (d)-1)의 단위 이름은 'oracle 종류와 출처' 절의 표에서 온다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: code 커밋(레지스트리)이 있으므로 test-only가 아니다(선례 `20260930-registry-grade-fix` -- 레지스트리 문서 수정 + 계약 test, red-green). 새 test 파일의 모든 test가 base에서
`AssertionError`로 FAIL한다(계약 11 (a) -- 열 머리 단언이 먼저. 그 뒤 판정도 base에서 FAIL: `reg_mismatch` 비지 않음 -- 실측 3). 병합본에서 green. equivalence가 아닌 이유: test가
새로 생기고 base에서 실패한다(동작 보존 증명 대상이 아니다). 신규 심볼 없음 -- red는 `ImportError`가 아니라 assertion이다(계획 680행).
V3: 바뀌는 소스 def 0(레지스트리·test만) → `targets []`. V7: 새 def 0. V5: 새 파일만 → `diff_paths []`. V4: interface card 두 표가 비어 `--interface-card`만으로는
`test_lint` ERROR('피검 심볼이 없다')이므로 auditor는 `--module-dir tools/migrate --subject move_plan:main`으로 돈다(선례 `20260922-sections-major-merge`·`20260922-ts1-extract-tool` --
test가 도구를 하위 프로세스로만 부르므로 판정 문장은 NO-SUBJECT, basis는 oracle 대조 문장. 작성 전 실측 14).

## oracle 종류와 출처

(d) 계획서·레지스트리·도구 출력. **동어반복 방지로 둘로 나눈다**(design §8 D0b 행, 1차 검토 §2 (3) V4 -- 레지스트리가 같은 도구 출력이라 '열 = 도구 출력'만으로는 도구와 열이 함께 틀린 것을 못 잡는다):
* **(d)-1 결정 사실 표본(손적용, 도구 실행 없이 정해진 기대값)**: design 30 승인(UD-0 -- N3.10 개정 3건 + D-19)과 계획서 N3.10 '대표 대상' 열에서 **규칙을 손으로 적용해** 정한 단위 → 목적지.
  test는 아래 표의 각 행이 대상 행이고 `이관 목적지` 칸이 기대 줄기와 같으며, 같은 단위의 `plan` `mod`도 같은지 단언한다. 표본은 지금 실측에서 계층 충돌(`upward`)에 걸리지 않은 단위만 골랐다
  (걸린 단위는 D0b 멈춤 해소(계약 8)가 목적지를 바꿀 수 있다 -- 작성 전 실측 3). D0b base에서 이 표의 근거를 다시 확인하고, 해소 문서 커밋이 표의 단위를 옮기면 그 커밋이 표를 고친다
  (test-author 착수 전 -- 기대값이 test 커밋 뒤에 바뀌지 않게).

  | 단위(함수 칸 첫 토큰) | 기대 목적지 | 근거(손적용) |
  |---|---|---|
  | `load_topology` | `circuit_state_graph` | UD-0 N3.10 개정 (b) -- A-1 MOD3(design §6.2 A-3 계산, `p3_doc_amendments.md` §1) |
  | `validate_theta_declaration_order` | `circuit_state_graph` | 같음 (b) |
  | `optimize_full_circuit_budget` | `sizing_layout_convergence` | UD-0 개정 (d), D-3 -- A-1 MOD8 |
  | `GmIdLUT` | `gmid_lut` | N3.10 MOD1 '대표 대상' -- A-1 |
  | `compute_metric` | `circuit_metrics` | N3.10 MOD5 -- A-1 |
  | `_optimize_theta_slsqp` | `theta_search` | N3.10 MOD6 -- A-1 |
  | `true_current_mirror_groups` | `circuit_state_graph` | N3.10 MOD3 -- A-1 |
  | `run_topology_pipeline_with_finger_fixup` | `sizing_layout_convergence` | N3.10 MOD8 -- A-1 |
  | `render_html_report` | `instance_report_builder` | N3.10 MOD9 `design_report.render_html_report` -- A-1(`<모듈>.<이름>` 토큰) |
  | `RailDeclaration` | `topology_authoring` | design §6.4 -- A-2(레코드 하강, 참조 단위 중 가장 낮은 MOD2), D-19 답과 무관. B26-1 병합 뒤에만 있다 |
  | `rail_declaration` | D-19 (가) `topology_authoring` / (나) `circuit_state_graph` | D-19 답(승인 기록 `20260930-30-module-split-design`)대로 -- 답이 나온 뒤 오케스트레이터가 이 칸을 하나로 고정 |

  지금 레지스트리에서 이 표본은 모두 기대 줄기와 다르다(`load_topology` 칸 = 파싱·자동채움 설명, `GmIdLUT` = `gmid_sizing_engine.py`, `compute_metric` = `gmid_sizing_engine` 등 --
  작성 전 실측 1) -- base red에도 기여한다.
* **(d)-2 실제 트리 drift guard**: 계약 3~7을 실제 저장소 `HEAD`에서 -- 도구 출력과 열의 일치(대상 행 전부), 판정 목록 빈 목록, MOD7, `import_time_high`, `보류(Phase 3)` 0.
  이 쪽은 Phase 3 이후 card가 엔진·열을 바꿔 생기는 어긋남(D-27 위반 포함)을 잡는 배선이다.
* design §8 D0b 행의 '규칙 손적용 **합성 입력**'은 이 card의 test에 두지 않는다 -- 합성 저장소에서 도구를 부르는 test는 base(D0a 병합 뒤)에서도 통과해 V2 red가 깨진다(계약 11 (a)).
  합성 입력으로 규칙을 검증하는 것은 D0a test(`A/tests/tooling/test_move_plan.py`, D0a oracle (a))의 몫이고, 이 card의 손적용 몫은 (d)-1의 실제 단위 표본이다(결정 필요 D0b-4).

## 거부해야 할 입력

(test가 FAIL해야 하는 저장소 상태 -- 각 상태를 test-author는 합성하지 않는다. 판정은 실제 트리 하나이고 아래는 계약의 반례 목록이다. auditor는 V10에서 병합본 사본에 하나씩 적용해
test가 실제로 FAIL하는지 잰다 -- 무동작 게이트 방지.)
레지스트리 대상 행 하나의 목적지 칸을 다른 MOD 줄기로 바꿈(`reg_mismatch` + 계약 6 (b)), 대상 행 칸에 줄기 뒤 설명 문구를 붙임(계약 6 (b) 정확 일치), 대상 행을 `〃`로 되돌림,
`근거 규칙` 열 머리 하나 삭제(계약 11 (a)), 대상 행 `근거 규칙` 칸을 `A-9`로(계약 6 (c)), `보류(Phase 3)` 하나 되살림(계약 7), N3.10 '대표 대상'에 이미 다른 행에 있는 식별자 하나를
다른 행에도 더함(`conflicts`), 작은 번호 MOD에 배정된 함수가 큰 번호 MOD 단위를 부르게 하는 배정(예: (d)-1 표본 단위 하나를 N3.10 MOD1 토큰으로 -- `upward`), MOD8 배정 단위의
기본값 인자가 MOD8 단위 상수를 읽게 함(`import_time_high`), split 파일 하나의 단위를 N3.10 MOD7 토큰으로(계약 5), `tools/migrate/move_plan.py` 부재(도구 출력 첫 줄 단언).
**거부하지 않아야 할 것**: shim 파일이 없는 트리(`absent_split` -- F2 뒤), 옮겨진 단위(A-0)만 있는 MOD 파일, 비대상 행·중첩 행의 옛 목적지 문구.

## library 회로 적용 여부

해당 없음(코드 구조·문서 판정). 회로 실행 없음.

## 무동작 판정 입력(무발동 값)

엔진 소스·기존 test·게이트 도구·D0a 도구는 바뀌지 않는다. 레지스트리에서 바뀌는 것은 대상 행의 `이관 목적지` 칸, 모든 함수 표의 `근거 규칙` 열, §7의 `보류(Phase 3)` 9칸뿐이다(계약 6 (d)·7 --
auditor가 base 대비 줄 단위 diff로 그 밖의 변경 0을 확인). 열을 더해도 기존 레지스트리 소비자(`tests/tools/reg_check.py` -- 머리 이름으로 열을 찾는다, `test_reg_check*.py`·
`test_df23_inventory.py`)의 결과가 같다(작성 전 실측 6: 재생성 모의 트리에서 그 세 파일 210 passed, `reg_check` 발견 0).

## 재현할 수치

auditor가 판정 기록 `reproduced_numbers`에 적는다(값은 **D0b base에서 처음 계산** -- 아래 괄호는 지금 관찰이고 기대값이 아니다):
* `assigned_units`(병합본 `plan` `assignment` 수 -- 관찰 390, 시제품), `assigned_per_mod`(MOD별 -- 관찰은 작성 전 실측 3), `rules`(규칙 분포, 재생성 전 base 출력 기준)
* `reg_mismatch_base`(D0b base `reg_mismatch` 수 = red의 크기 -- 관찰 36(UD-0 개정 적용 모의)) / `reg_mismatch_merge` = 0
* `registry_tables`(함수 표 수 -- 관찰 15), `target_rows`·`nested_rows`·`non_target_rows`(관찰 337·7·35, 시제품 -- 문장 단위 키 차이로 비대상은 실제 도구에서 줄어든다, 실측 1)
* `hold_phase3`(9 → 0), `hold_phase4`(14 → 23)
* `idempotent_mod_diff` = 0(계약 9), `plan_seconds`(test 한 번의 `plan` 시간 -- 관찰 12~19초)
명령: §10 `MP_ARGS`로 `"$S/move_plan.py" plan --root "$ISO" --rev <커밋>`(D0b base, 병합본 각각), 레지스트리 표 분류는 auditor 스크립트(계약 6 정의 그대로).

## 결정 필요 항목

**D0b-1(착수 조건 -- 지금 실측으로 D0b는 멈춘다, 계약 8 (a))**: `5f643a9` + UD-0 N3.10 개정(D-19 (가)) + G1·D0a 시제품에서 `plan`은 `upward` **34**, `cycles` **1**(MOD 9개 한 SCC), `unassigned` **18**
(작성 전 실측 3·4). design §6.2는 "A-3 계산으로 드러난 충돌 3건"만 UD-0에 넣고 나머지는 D0b가 B26-1·B34 뒤에 계산한다고 적었지만, 위 충돌 대부분은 **B34·B26-1과 무관하게 지금 계산된다**:
* (i) **A-1 ↔ A-1 충돌 2건**(N3.10 표 안의 모순, 원문 확인): `_build_theta_evaluator`(MOD6 토큰)가 `resolve_stack_layout`(MOD8 토큰)을 부른다(`sizing_recipe.py:8060`),
  `require_declared_spec_source`(MOD2)가 `spec_fingerprint`(MOD3)를 부른다(`:7683`). 규칙으로는 못 푼다 -- N3.10 개정만 가능.
* (ii) **A-1 → A-4 3건**: `validate_metric_units`(MOD2) → `metric_unit_scale`(레지스트리 `gmid_sizing_engine`, `:5272`), `SemiEmpiricalGmIdLUT`(MOD1) → `_multilinear_interp_point_multi`(MOD4, `:399`),
  `_METRICS_REGISTRY`(MOD5) → `_metric_nulling_resistor_ohm`(레지스트리 칸 "instance_report_builder.py(보고) 또는 gmid_s…"가 MOD9 하나로 읽힘).
* (iii) **A-4 → A-1 17건·A-4 → A-4 12건**: 옛 레지스트리 칸이 정한 배정이 큰 번호를 부른다(MOD2 → MOD3 15, MOD4 → MOD5 8 -- `_metric_*` 함수 26개 중 24개가 레지스트리 칸 `gmid_sizing_engine`으로 A-4(MOD4)가 되어
  design §6.2 A-4 주석의 "`_metric_*`는 A-5로 MOD5"가 성립하지 않고, 그중 4개가 MOD5 함수(`compute_metric`·`build_ac_network` 등)를 불러 upward다 -- 등). `〃` 이어짐이 다른 파일 행에 번져 생긴 것도 있다(§3 '기타 모듈' 표 `save_html_report` 〃 → 위 행
  `miller_ota_topology`의 `gmid_sizing_engine.py` -- 표에 파일 열이 없다).
* 기본안(원칙 '결정은 원칙으로 기본안부터' + '정의 하나'): **design 승인 질문 전에** (i)(ii)를 UD-0의 N3.10 개정 문안에 더하고(지금 계산 가능하다 -- UD-0의 '지금 계산 가능한 것' 범위),
  (iii)은 규칙 하나로 닫는다 -- **A-4 승격**: A-4 칸이 MOD 하나여도 A-3처럼 max(칸 MOD, R(u) 배정 MOD 최댓값)(design §6.2·D0a 계약 2 개정, D0a 착수 전). 시제품 측정: 승격만으로
  `upward` 34 → **7**(남는 7은 (i)(ii)와 승격이 새로 만든 1건 -- `load_topology`(MOD3) → `propose_device_roles_gap_fill`이 MOD7로 승격, 작성 전 실측 4), 단 승격은 배정 47개를 바꾸고 재생성
  멱등이 깨진다(위반이 남으면 다시 승격 -- 실측 5) -- 위반 0이 될 때까지 개정을 함께 해야 한다. 대안: (iii) 30여 단위를 N3.10 토큰으로 하나씩(표가 길어지고 단위 이름이 계획서에 쌓인다),
  또는 레지스트리 칸을 입력으로 손질(계약 '손으로 쓰지 않는다'와 충돌 -- 비권고). 판정 기준(배정 규칙·계획서 표)이라 사용자 몫이고 design 개정 범위다(오케스트레이터).
**D0b-2(착수 조건 -- D0a 규칙의 빈칸, D0a 착수 전 D0a spec card 개정 기본안)**: (a) **모듈 docstring 문장 단위**가 배정되지 않는다(`sizing_recipe`·`stick_diagram`·`design_report`·
`audit_current_forced` 4개 -- 참조도 참조자도 없어 A-5 `unassigned`; `topology_library`는 A-1 파일 토큰으로 배정). SD·ACF는 F2 뒤에도 남으므로 **E4가 영원히 FAIL**한다. 기본안: D0a 계약 2에
'모듈 docstring(첫 문장 문자열 `Expr`)은 배정 대상이 아니다(제자리 -- shim (b)도 docstring을 허용)' (b) **`--keep` 파일의 잔여 단위**(`render_report`·`sys.path.insert` 문장 -- D-8은 도구로
남긴다고 정했지만 규칙이 없다 → `unassigned`). 기본안: 규칙 A-K '`--keep` 파일의 단위 중 A-1~A-4로 정해지지 않은 것은 그 파일에 남는다'(A-5보다 먼저) (c) **참조자 없는 단위**(§7 D 목록
`보류(Phase 4)`·삭제 후보·예시 함수 -- `build_toy_lut`·`node_pole_estimate`·`folded_cascode_example` 등). 후보 규칙 A-6 'R(u)의 가장 큰 배정 MOD'(계층상 둘 수 있는 가장 낮은 자리) 측정:
`unassigned` 18 → 6(A-K와 함께). 남는 6 = (a)의 docstring 3 + `signal_path_nodes`(참조 0) + `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity`(서로만 참조) -- 이 셋은 N3.10 토큰
(D-11 승인) 또는 Phase 4 삭제 선행 중 하나다. (a)(b)는 정의 문제라 D0a 개정으로, (c)는 규칙(A-6) + 남는 것 D-11이 기본안.
**D0b-3**: 비대상 행(실측 35 -- 하네스 `canonical_spec`·`_spec_*`·`SPECS`·`run`·`derived_spec`, LUT 도구 `sky130_lut_sweep.py` 5행, `topology_to_markdown.py` 4행 등)의 목적지 칸.
design §8의 "전 행 = MOD 이름 하나"는 이 행들에 도구 출력이 없어 지킬 수 없다. 기본안: 칸 불변·`근거 규칙` `-`(계약 6 (d) -- 최소 변경, 도구가 읽지 않는 행). 대안: `이동 없음(<현재 파일>)`으로 바꾸고
옛 문구를 비고로(손으로 쓰는 문장이 늘어난다).
**D0b-4**: oracle (d)의 '합성 입력' 몫을 D0a test로 두고 이 card는 실제 단위 표본(d)-1로 대신한다(V2 red 조건 -- oracle 절). design §8 D0b 행 문구를 사실 문장으로 고치는 것은 design 개정 몫.
**D0b-5**: `근거 규칙` 열의 뜻 = 재생성 시점 규칙(이력). 재생성 뒤 도구의 `rule`은 A-4로 바뀔 수 있어(실측 5: A-5 63 → 60, A-3 1 → 0, A-4 234 → 238) test는 형식만 본다. 대안: 열을 두지 않는다
(design §8 '근거 규칙 열' 문구 삭제 -- 규칙 근거는 판정 기록 `out/`의 base 출력에만).
**D0b-6**: D-19 답(승인 질문 중) -- (d)-1 표의 `rail_declaration` 기대값이 갈린다. 답이 나오기 전에는 test-author 착수 금지.
**D0b-7**: MOD7 파일 밖 단위의 MOD7 배정이 생기면 M7을 실제 card로 둘지(design 3차 검토 m4). 지금 0(실측 3·4·5 모든 변형) -- 생기면 묻는다.

## 작성 전 실측

(기준 gate `master` **`5f643a9`**(2026-10-01, `19eb475` 대비 md 일치 계약 test 1파일·판정 기록뿐 -- 엔진·`tools/`·계획서·레지스트리 무변경). 격리 복제본 `C:/g162/r`(`git clone --no-local`,
origin 제거, 빈 hooksPath, 작업 끝에 삭제)에서만. B34·b26pre·backfill·B26-1·B33·G1·D0a는 **모두 미병합** -- G1은 시제품 `_drafts/g1_kit/install_proto.py`(sha256 `5790433c…`) +
`g1_core.py`(**`b3c4e391…`, 23:16판 -- G1 키트는 작업 중이라 그 시점 파일을 스크래치에 복사해 썼다**; D0a 키트가 쓴 `8fc4ab4b…`판과 다르다 -- 같은 트리에서 `upward` 48 → 46), D0a는 시제품
`_drafts/p3kit_d0a/move_plan_proto.py`(`d2f3da97…`, `plan`만). 측정 스크립트 `_drafts/p3kit_d0b/`. **전부 관찰 -- 기대값 근거 아님, D0b base에서 다시 잰다.**
**작업 끝 확인**: gate `master`가 `dd60db6`으로 나아갔다(`5f643a9..` = Phase 2 완료 판정 기록 `2eefda1`·백로그·V3 면제 묶기 문서/spec/승인 -- 계획서는 839행(N4.2 V3) 한 줄뿐,
N3.10(519~531행)·레지스트리·엔진·`tools/` 무변경 -- 위 측정 그대로 유효).
시제품 한계: G1 시제품 `units`는 문장 단위의 키를 `<stmt:해시>`로 내서 D0a 계약 2(바인딩 이름을 이은 것)와 다르다 -- 상수 행(`_KNEE_L_CACHE` 등 8행)이 시제품에서는 비대상으로 센다.)

1. 사실(레지스트리·계획서): `regen_registry.py`(D0a 계약 2 A-4 표 정의) → 레지스트리 함수 표 **15개**, 행 분류(UD-0 개정 적용 `plan` 기준) 대상 337·중첩 7·비대상 35·`multi` 0.
   split 다섯 파일 최상위 이름의 파일 간 중복 0(AST). `grep -c "보류(Phase 3)"` → **9**(레지스트리 495·505·509~515행), `보류(Phase 4)` 14, `보류(Phase 6a)` 2. 표본 (d)-1의 지금 칸:
   `load_topology` "파싱: circuit_state_graph S0/S1 로더 / 자동채움:…", `validate_theta_declaration_order` `topology_authoring`, `optimize_full_circuit_budget` "sizing_layout_convergence(레이아웃·row_split…",
   `GmIdLUT` `gmid_sizing_engine.py`, `compute_metric` `gmid_sizing_engine`, `_optimize_theta_slsqp` `optimizer`, `true_current_mirror_groups` "circuit_state_graph.py(S1 …", `run_topology_pipeline_with_finger_fixup`
   `sizing_layout_convergence`, `render_html_report` "`instance_report_builder.render_design_r…`" -- 정확 일치 0(red 기여). N3.10 표(계획서 519~531행) 머리 4열·10행, MOD7 '대표 대상'은 산문뿐.
2. 이름 충돌: `ls A/tests/contracts` → `test_p3_*`·`registry_dest` 0. `git grep "glob("` → contracts 전수 스캔은 `test_ic_markers_match_plan.py:91`(contracts `*.py` 텍스트 -- `gmid_ic` 표식만 본다,
   이 test는 표식 없음)·`test_d_*`·`test_ts3_no_print_verdicts.py`(tests `rglob`) -- 피할 것은 삭제 이름 AST 참조와 `print`(계약 11 (e)). `p3-registry-dest`·`test_p3_registry_dest` 저장소 참조 0.
3. **`plan` 시제품 -- 개정 없음 / UD-0 개정(ga)**(`run_plan.sh` + `analyze_plan.py`): exit 1 / 1, `upward` 46 / **34**, `cycles` 1 / 1(9 MOD SCC), `unassigned` 18 / 18, `conflicts` 0 / 0,
   `reg_mismatch` 38 / **36**(규칙 A-1 28·A-2 8), `import_time_high` [] / [], MOD7 밖 0 / 0, 배정 390(A-4 234·A-5 63·A-1 55·A-2 37·A-3 1), 개정으로 MOD가 바뀐 단위 8. UD-0 개정 뒤 MOD별:
   `gmid_lut` 5·`topology_authoring` 34·`circuit_state_graph` 66·`gmid_sizing_engine` 115·`circuit_metrics` 5·`theta_search` 25·`stick_diagram` 107·`sizing_layout_convergence` 17·`instance_report_builder` 16
   (MOD10 0 -- M10은 추출). `upward` 34 규칙 쌍: A-4→A-1 17, A-4→A-4 12, A-1→A-4 3, A-1→A-1 2(원문 확인 `sizing_recipe.py:8060`·`:7683`·`:5272`·`:399` -- 결정 필요 D0b-1). `reexports` split 5파일
   (SR 8줄·SD 3·TL 1·DR 2·ACF 2), `order` MOD1~MOD9. `unassigned` 18 = 모듈 docstring 4(SR·SD·DR·ACF)·ACF `sys.path.insert` 문장·`render_report`·SR 5(`_invq_newton`·`build_toy_lut`·`node_pole_estimate`·
   `signal_path_nodes`·`solve_diode_stack_current`)·SD 7(`MultiLeafHubParityVerdict`·`SharedFingerWCandidate`·`check_multi_leaf_hub_parity`·`find_differential_and_mirror_forks`·`folded_cascode_example`·
   `search_shared_finger_w`·`two_stage_ota_example`). 이 트리에는 `rail_declaration`이 없어 D-19 두 안의 결과가 같다.
4. **규칙 후보 변형**(`mk_variant.py` + `run_variants.sh`, UD-0 개정 트리): A-K만 → `unassigned` 15 / + A-6 → 6 / + A-4 승격 → `upward` **7**·`cycles` 1·`unassigned` 6·`reg_mismatch` 69(승격이 배정 47개를
   바꿈). 승격 뒤 남는 `upward` 7: A-1→A-1 2(위), A-1→A-4L 3(`validate_metric_units`·`SemiEmpiricalGmIdLUT`·`_METRICS_REGISTRY` 쪽), A-5→A-4L 1(`_THETA_FEED_REGISTRY` → `_feed_metric_stage_budget`),
   `load_topology`(A-1 MOD3) → `propose_device_roles_gap_fill`(승격 MOD7) 1. `import_time_high` 모든 변형 [], MOD7 밖 모든 변형 0. (변형의 A-6이 A-K보다 먼저 돌아 `render_report`를 MOD9로 보낸 것은
   변형 순서 결함 -- 규칙으로 정할 때는 A-K가 먼저다.)
5. **재생성 모의**(`regen_registry.py --write` + `sim_regen.sh`: 대상 행 칸 = 배정 줄기, 함수 표마다 `근거 규칙` 열 추가 → 측정용 커밋 → 같은 규칙으로 `plan` 재실행): 규칙 그대로(A-0~A-5) --
   `reg_mismatch` 36 → **0**, (키 → `mod`) 사상 차이 **0**(멱등), `rule` 분포는 A-4 234 → 238·A-5 63 → 60·A-3 1 → 0(열이 A-4 입력이 되므로 -- 계약 6 (c)), 레지스트리 diff 409줄 삽입·409줄 삭제(열 추가로 모든
   표 행이 바뀐다). A-4 승격 변형 -- `reg_mismatch` 1·사상 차이 5(위반이 남으면 재승격 -- 멱등은 위반 0에서만, 계약 9).
6. 기존 레지스트리 소비자: `git grep -l function-registry -- '*.py'` → test 쪽 `tests/tools/reg_check.py`(열을 머리 이름으로 찾음, `처리` 값 `^보류\(Phase [0-9]+[a-z]?\)`)·`contracts/test_reg_check.py`
   (실제 저장소 `test_main_on_this_repository_is_clean`·`test_repository_section7_lacks_r4_names`), 나머지는 `.ai/verification/**` 증거 스크립트 6개(기록된 base에서 재실행 -- 대상 아님).
   재생성 모의 커밋에서 `reg_check` exit 0(발견 0), `test_reg_check.py`·`test_reg_check_df23.py`·`test_df23_inventory.py` **210 passed**(`--gmid-phase=3 --gmid-strict=`). `tools/gates`의 레지스트리 읽기 0.
7. **test 모양 시제품**(`test_p3_registry_dest.proto.py` + `run_proto_test.sh`, 도구 = 시제품): base(G1 시제품 커밋) 7개 중 **5 failed·2 passed** -- 통과한 둘이 `import_time_high`·MOD7 단언(base에서
   이미 참) → 계약 11 (a)의 '열 머리 단언 먼저'가 필요하다. 재생성 모의 커밋 4 passed·3 failed(`plan` exit·`upward`/`cycles`·`보류(Phase 3)` -- 모의는 D-10과 계층 해소를 하지 않았다).
   실패는 모두 `AssertionError`(수집 오류 0), `plan` 1회 실행 시간 12~19초(모듈 캐시로 test 파일당 1회).
8. 원칙: topology 무관·이름 무관 -- 계약 12, 손으로 쓰지 않음 -- 계약 6·9, 만들면 배선 -- 계약 3(이후 모든 card V1·DoD E4), 조용한 기본값 금지 -- 계약 8(멈춤), 재계산 없음 -- 계약 11 (c).
9. 쓰기 경로(계획 N3.12.2, 603·626행): 레지스트리 = gmid-code-author(오케스트레이터 `docs/03-analysis/**` 행은 레지스트리를 제외한다), `A/tests/contracts/test_p3_registry_dest.py` = gmid-test-author,
   N3.10 개정(계약 8) = 오케스트레이터 `docs/01-plan/**` + 승인 기록. role_paths: 레지스트리·contracts test 모두 게이트 코드 밖 → `gate_change: no`.
10. 계획서 소비자: 지우거나 옮기는 이름 없음(열 값만 바뀐다). `git grep -n "이관 목적지" -- docs/01-plan docs/02-design` → 계획 517행 문장(이 card가 이행), design 문서들의 설명 -- 줄 바뀜 없음.
11. 미배선: 새 def 0(test 보조 함수만). 도구(`move_plan.py`)의 배선 (i)이 이 card다(D0a 계약 9 -- "D0b 병합 전에 (i)이 없으면 D0b card가 막는다").
12. V3 규모: 바뀌는 소스 def 0 → `targets []`(레지스트리는 `_is_source` 밖). 실행 비용은 V1에 `plan` 1회(12~19초)가 card마다 더해진다(D0b 뒤 Phase 3 card M1~M6·M8·M9·M10·T1·F1·F2 12개(T0가 D0b 뒤면 13개) + DoD E4·E5 두 전체 실행).
13. 같음 판정: 칸 비교는 문자열 정확 일치(앞뒤 공백은 칸 나누기에서 제거), 사상 비교는 정렬된 (키, `mod`) 튜플 목록, 판정 목록은 `== []`. red 모양: 허용 예외 `AssertionError`만(계약 11 (a)), 새 키워드 인자 없음.
14. **V 도구 모양**(`sim_chain_vtools.sh`: `c66ba0a`(G1 시제품 + UD-0 개정 모의) → D0a 대역 커밋(시제품을 `tools/migrate/move_plan.py`로) = B → test 커밋(시제품 test를 실제 위치로) → code 커밋(재생성 모의 +
    `보류(Phase 3)` → `(Phase 4)`) = H, base 판 게이트 = B의 `tools/gates`): V3 PASS `targets []`·`mutants 0`, V5 PASS `diff_paths []`, V6 PASS `targets []`, V7 PASS `new_defs []`,
    V4 `--interface-card`(생성본 -- 기존 함수 0·신규 0, `interface_card.py` exit 0)만 → **ERROR '피검 심볼이 없다'**, `--module-dir tools/migrate --subject move_plan:main` → PASS(판정 문장 7개 모두 NO-SUBJECT).
    `parse_spec_card`(gate `5f643a9` `tools/gates` -- `git archive`): exit 0, 머리 키 6개, 절 11개(양식 그대로).
