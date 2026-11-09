# IT-1 + IT-2 통합 병합 준비 -- 범위표, base, 브리핑 초안

기준: master `7620f5ee`(계획 v6.38.8, design v1.16.3, 재측정 때 `0d99a813` -- 문서만 더해짐), `integ/it12` `b9351eac`. 실측 = `scope_grep.txt`(스크립트 `measure_it_scope.sh`, git 읽기만). as-built는 재작성 범위로만 인용한다(원칙 8).

## 1. card별 범위표

| card | 판정 이력 | 재사용 | 재작성·신규 | 근거 결정 |
|---|---|---|---|---|
| IT-0(옛 기준선) | PASS, 9회로 | 판정 기록 보존만 | 없음. 값은 근거로 쓰지 않음 | O-153 |
| IT-0b | 착수 전 | -- | **유보**: 13회로 값, base sha와 보류 표지 | O-225, A-7. O-210 RR-6으로 신호 경로 측정 항목 삭제 |
| IT-1 옛 범위 1(같은 DC 엣지 삭제) | PASS | 코드·test 그대로(`input_tie` grep 0, `CONTRACT:889` 문언 하나 남음) | 문언 하나 | B2·K-3·O-13 |
| IT-1 범위 2~4(포트별 뿌리, 옛 정지) | PASS(낡음) | -- | **재작성** `writer_plan.py:176, :243, :254-258`, 상수·export, `block_columns` 읽는 키 | DEC-106, E-29 |
| IT-1 범위 5(g = s) | 코드 0 | -- | `gvgs_cycles.py:68-79` 정지 삭제, 칸 추가, 쓰기 계획 READS | O-210 RR-6, N3.6 (11). 신호 경로 술어 = LA-1 |
| IT-1 범위 6(B4) | 코드 0 | -- | S1v 필드 넷, `coupling_vars.py:179` | O-173 P9-M1a |
| IT-2a(파생 규칙) | PASS | **코드 재사용**. keep은 `SEAL_ITEM_BLOCKS` 블록 객체로 파생(`kernel_run.py:85-87`)하고 필드 이름 목록이 없어 봉인 9 삭제에 코드 변경 0. test의 'DC 열세 블록' 수는 EO-1이 바꿈 | 없음 | O-61 P1. P:1341 '봉인 9 writer' 표지는 실측상 코드 몫 0(J7) |
| IT-2b(커널 창) | PASS(낡음) | `region_rows` 골격, 음수 감도 정렬, `port_window` | **재작성**(IT-2c 안): tol 항, F 성분 상태, 비뿌리 항목, `dc_output_structure`, 쌍 roots | O-204, O-205, O-109 D1·D4, O-118 3번, E-09 |
| IT-2c(측정 구성) | 코드 0, 옛 card `d95c8ff8` | 옛 interface 구조(갈래·servo·V_cm·T-L10) | 신규 블록 셋 + `default_port`. **옛 card에서 빼는 것**: R0·`_conduction_rows`·`ss_dev`·`dc_op`·floor READS, +tol, 일반 1차 행, `off` toy | O-115~O-118, O-204, O-205 (3), O-211 조건, O-215 임시 |
| IT-2d(front 배선) | 코드 0, 옛 card 소멸 | 없음 | `icm_window_metrics`, `ls_swing` 축소, B77, relabel | O-109 C1, O-111~O-113, U-106 |
| IT-2e(부분 스냅샷) | 코드 0, card 없음 | 없음 | `writers_in_scope` | O-96 |
| A-20(출발 순서) | -- | -- | **IT 범위 밖**: R6·B 하한 행은 LA-1a. IT는 출발 경로를 고치지 않음 | A-20 |
| O-206·O-211 RR-3 | -- | -- | 기능 기준 칸·점별 이득 **만들지 않음**(O-215 임시, 표 #2·#21). 조건 (1)~(3)만 영역 행 창에 | O-215 |

**남기는 것(다른 card)**: 커널 입력 창 측정·`_interior_solution`·`_dyadic_ys`·`INPUT_STATUS_UNSETTLED` = WB-1. 봉인 7 +tol·`dc_seal_conduction`·`dc_off_current`·`dc_conduction_floor`·`linear_devices` = EO-1. `order_hints`·`w4_root` = TB-1. VDSAT READS = HC-S.

## 2. 옛 test·기대값이 낡은 곳(grep, 파일:건수, integ/it12)

| 패턴 | 파일 | 처리 card |
|---|---|---|
| `input_port_multiple_roots` | `sizing/test_writer_plan.py`:3, `sizing/test_s2_values.py`:1, `search/test_orbit_ties.py`:1 | IT-1 |
| `gvgs_self_edge` | `graph/test_gvgs_cycles.py`:2, `graph/test_s1_values.py`:2, `graph/graph_u2_oracle.py`:1 | IT-1 |
| `net_model`·S1v 권한표 | `graph/test_net_model.py`:1, `test_s1v_fields` | IT-1 |
| `dc_output_structure`·OUTPUT·`kvl_fixed` | `sizing/test_writer_plan.py`:23, `sizing/test_s2_values.py`:6 | IT-2c |
| `f_component_undeclared` | `sizing/test_block_columns.py`:3, `sizing/test_s2_values.py`:2 | IT-2c |
| `saturation_window` | `sizing/test_input_window.py`:18 | IT-2c |
| `region_rows`·`_Circuit` | `sizing/test_block_columns.py`:12 | IT-2c |
| tol_VDsat | `sizing/test_block_columns.py`:5, `sizing/test_input_window.py`:3 | IT-2c(여유 0 손 재유도) |
| tol_VDsat(봉인 7) | `sizing/test_seal_saturation.py`:4, `sizing/test_size_and_seal_local.py`:2 | **EO-1**, IT에서 그대로 |
| `SS_WRITES`·`DC_TABLE` | `metrics/test_ss_types.py`:4, `sizing/test_s2_values.py`:9 | IT-2c |
| `ls_swing(` | `metrics/test_ls_swing.py`:17 | IT-2d |
| 영역 `"ls"`·`"ss"` | `metrics/test_registry.py`:3, `metrics/test_pending_metrics.py`, `authoring/conftest.py`, `metrics/test_catalog.py` | IT-2d |
| 봉인 9 필드 | `sizing/test_seal_conduction.py`:16, 그 밖 6파일 | **EO-1** |
| 회귀 기준선 | `integration/fixtures/u17_1b_s0_baseline.json`(옛 IT-1 갱신분, 다시 바뀜) | IT-1 test 주체, 원인 칸 |
| 옛 판정 기록 | `.ai/verification/20261021-it1-*`·`it2a`·`it2b` | 보존, 재판정은 새 id. 옛 PASS는 IT-1 범위 2~4·IT-2b tol에 대해 근거 아님 |

계획·design 잔재 수는 `scope_grep.txt` 끝.

## 3. base

| 안 | 내용 | 충돌 파일(실측) | 판정 |
|---|---|---|---|
| **(A) integ/it12에 master `7620f5ee` 병합** | 기존 worktree·역할 커밋·판정 기록 유지, 그 위에 새 test·code | **0**(`git merge-tree --write-tree --name-only`: `7620f5ee` 대 integ/it12 트리 `ff66689e`, 작성 중 올라간 master `0d99a813` 대 integ/it12 트리 `ebbb2817`, 둘 다 exit 0. `0d99a813`에서 는 것 = GL-1 design·card 문서뿐, 엔진 변경 0). 양쪽이 고친 파일 2(`metrics/CONTRACT.md`, `sizing/CONTRACT.md`) 자동 병합. master 쪽 엔진 변경 = CONTRACT 넷 줄뿐 | **권고** |
| (B) master에서 새 통합 브랜치 + 엔진 커밋 cherry-pick | 이력이 깨끗함 | 미측정 | 판정 기록의 커밋 해시가 끊기고 얻는 것이 없음. 역할 agent cherry-pick 금지 위반 소지 |
| (C) master에서 새 브랜치, 옛 코드 버림 | 전체 재작성 | 0 | IT-2a 재사용을 버림, 지연 ⚠ |

병합 규모 표지: integ 쪽 1340 파일·703,640줄 중 엔진 42 파일(+2121/−446), 나머지는 `.ai/verification` 증거 1287 파일(+17.9 MiB, 기존 관행). 줄이려면 사용자 결정(삭제·공유 범위).

병합 뒤 card를 `docs/02-design/specs/`로 옮기고 옛 card 표지를 '대체됨 -- 새 id'로 갱신한다. `card/it2c`는 병합하지 않는다.

순서: **base 병합 → card 커밋 → IT-1 test·code → IT-2c test·code → IT-2d → IT-2e → 통합 판정·연기 시험 → (GL-1 병합 뒤) master.** 뒤따름 = WB-1(O-223), EO-1 범위 4(표 #13), card C, HC-S.

## 4. 유보(O-225)와 유지

유보·보류 표지(`미완료(보류 다리: …, 채울 시점 = LA-1 측정 시점, 채울 card = EO-1·OP-5·CL-1, base = <sha>)`, 통과로 세지 않음, 병합 판단 O-226·A-10): 13회로 변화표, IT-0b 값, IT-2c 착수 실측 (a)(b)(d)(e), `sf_pushpull` 재측정, 용량만 결측 봉인점 수, 실패 줄 수, SPICE 다리.

유지: toy 전부, 기존 회귀(새 test 체계 전체), 결정성 비트 동일, 구조 규칙, G-8·G-10·래칫, 잔재 grep, 병합 때 연기 시험(1~2회로).

연기 시험 회로: 선택 기준 = N6.1 '유지하는 것'. 후보 = 입력 DC 미선언 차동 1회로 + 단일 입력 또는 선언 1회로, 실제 고름은 직전 master에서 예외 없이 끝나는 회로로 감사가 정한다(미측정).

## 5. 병렬 가능한 조각

| 조각 | 동시 가능 | 비고 |
|---|---|---|
| IT-1 test / IT-2c test / IT-2d test / IT-2e test 초안 | 네 agent 동시 | 커밋은 card 순서대로. 파일 겹침 `test_writer_plan.py`(IT-1·IT-2c), `test_block_columns.py`(IT-1·IT-2c), `test_ss_evaluate.py`(2c·2d·`test_kernel_run`은 2e) |
| IT-1 code 커밋 ② g = s(`graph/`), ③ B4(`graph/`) | ① 쓰기 계획과 동시, 파일 안 겹침(①은 `sizing/`) | ②·③은 서로 `graph/s1_values.py` 겹침, 순차 권장 |
| IT-2c code 묶음: `metrics/ss_circuit`·`ss_nodal` + 스탬프 / `graph/views` `default_port` / `sizing/_helpers_dc_solve` 이동 | 셋 동시 | `icm_config`는 셋 뒤 |
| IT-2d·IT-2e code | IT-2c 뒤, 둘은 파일 겹침 0(`metrics/` 대 `sizing/`) | IT-2e 줄 재측정은 IT-2d head 기준이라 커밋은 뒤 |
| base 병합·test 기준 측정(D-1) | 지금 | 측정 agent 하나 |

test 주체가 소스를 보지 않으므로 test 네 개는 base 병합 직후 동시에 시작할 수 있다. red 재현만 card 순서 head에서 한다.

## 6. 브리핑 초안

아래 그대로 쓴다. `<id>` = `20261104-it1-input-point`·`20261104-it2c-icm-config`·`20261104-it2d-front-wiring`·`20261104-it2e-partial-snapshot`.

### 공통 머리(모두)

> 먼저 읽기: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/la1_sprint_brief.md`, `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/CLAUDE.md`(원칙 33개), `C:/Users/HSLEE/Documents/Todoc/fpga/CLAUDE.md` '★graph 단일 정본'.
> git은 `git -C <절대 경로>`만. **이 도구의 Bash에서 `set -e`는 동작하지 않는다**: 순서가 중요한 명령은 `&&`로 잇거나 `bash -c 'set -e; ...'`로 돌리고, 파이프는 실패를 가리니 쓰지 않거나 pipefail을 건다. reset·checkout·stash·push 금지. master에 직접 커밋하지 않는다. 파일 수정은 Edit/Write 또는 Python 바이너리 치환, heredoc append 금지. `user_decisions.md`는 쓰지 않는다. Python = `C:\Python314\python.exe`, 출력 `PYTHONIOENCODING=utf-8`. `timeout` 명령 금지. rm은 변수에 `${X:?}` 가드.
> 커밋: `git -C <worktree> commit -m "<제목>" --trailer "Role: <역할>" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ"`.
> 임시 경로 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_<역할>_<id>/`. 측정 결과는 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/it/<id>/`에 케이스마다 append. LUT를 읽는 실행은 회로마다 프로세스를 나눠 순차로, 여유 2 GB 아래면 중단.
> 사용자 질문을 만들지 말고 권고 하나와 근거·대안·원래 취지와 다름을 오케스트레이터에게 보고한다. 멈춤: push, 근본원칙 변경, topology connectivity 수정, 기준 약화. 보고는 한글로 짧게.

### test (`gmid-test-author`)

> card `<id>`. 입력 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/<id>-test/docs/02-design/specs/<id>.interface.md`만. 엔진 소스 열람 금지, `skills/analog-gmid-design/gmid_engine/tests/**` 하네스만 읽는다. 쓰는 곳 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/<id>-test`(브랜치 `role/test/<id>`)의 `gmid_engine/tests/**`.
> interface의 test 목록과 '고칠 기존 test'를 쓰고 `--trailer "Role: test"`로 커밋한다. 기대값은 손 유도·물리 불변식·정확 산술·기준 비트 동일만. 피검 함수나 현재 출력으로 기대값을 만들지 않는다. 전제 단언을 먼저 두고, 어기면 그 사례를 무효로 한다. 새 이름 접두 = card의 `test_it*_`. toy는 `input_dc`·`node.port_role`을 직접 선언하고 회로·소자 이름을 규칙에 쓰지 않는다. 13회로 값은 쓰지 않는다(O-225). 기준을 약화하게 되면 멈추고 보고한다. 보고 = 커밋, 고친 기존 test와 이유, red 예상 목록.

### code ([sonnet], `gmid-code-author`)

> card `<id>`. 입력 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/<id>-code/docs/02-design/specs/<id>.spec.md`·`.interface.md`, design 41 §4.7-W(정본, 옛 줄의 `[v1.16.3 대체]` 문언은 효력 없음)와 card가 인용한 절. 쓰는 곳 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/<id>-code`(브랜치 `role/code/<id>`, base = test 커밋). `--trailer "Role: code"`.
> test를 고치지 않는다. test가 틀리면 `docs/02-design/disputes/<id>.md`를 쓰고 멈춘다. **as-built는 재작성 범위로만 읽는다**(원칙 8). **as-built 결정 금지**: 계획·design과 다르면 멈추고 보고. graph 규칙: 필드마다 writer 하나, READS, 새 cache·memo·dict·sctx 슬롯·값 칸·사본 금지, 정본 자리가 없으면 멈춤. 만들면 배선, 옛 코드는 같은 변경에서 삭제, 레지스트리·CONTRACT·모듈 지도 갱신. 구조 규칙 A~I, G-8 새 키 0. 범위 밖(WB-1·EO-1·TB-1·HC-S 몫)은 고치지 않는다.
> rule 파일(`S1V_RULE_FILES` ∪ `STRUCTURE_RULE_EXTRA_FILES`)을 고치는 커밋은 같은 커밋에서 `skills/analog-gmid-design/assets/library/{current_reuse_telescopic_ota,nmcnr_amplifier}.structure.json`의 `rule_hash` 줄만 재기록한다(A-33·A-34). 값 = 그 커밋 트리의 `structure_rule_fp()`. IT-1은 커밋 ①②③을 나눈다(재기록은 ③). 보고 = 커밋, 바뀐 필드·소비자 표, 실행 test 결과, 원래 취지와 다른 것.

### audit (`gmid-verification-auditor`)

> card `<id>`. 쓰는 곳 = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/<id>-audit`(브랜치 `role/audit/<id>`), 실행은 격리 복제본 `C:/Users/HSLEE/AppData/Local/Temp/la1s_audit_<id>/`에서만. 작성자 보고를 증거로 받지 않는다. `--trailer "Role: audit"`.
> 순서 3: test 커밋 freeze, base red 재현(assertion, `ImportError`는 신규 함수만). 순서 6: 병합본에서 interface '판정 측정' 전부와 graph 정본 별도 항목(G-8·GL-1 `ratchet.new` 0·소유표·G-10·블록 안 재계산·소비자 ≥ 1 또는 출력 전용·구조 규칙·회로 이름 0·fail-closed·상수 0·DC/AC·작성자 ≠ 검증자). 기대값마다 spec 'oracle 종류'와 대조. 전체 0 failed가 기준이고, base에 실패가 남으면 목록을 올리고 멈춘다(A-31). `structure.json` diff = `rule_hash` 줄뿐인지와 값 비교 근거를 적는다.
> 판정 기록 = `.ai/verification/<id>.json`(`.ai/verification/_schema.json` 필수 칸). 13회로 변화표·SPICE 다리·IT-0b는 재지 말고 V 칸 basis에 `미완료(보류 다리: 13회로 변화표·IT-0b·SPICE, 채울 card = EO-1·OP-5·CL-1, base = <sha>)`로 적는다(통과로 세지 않음, A-5·A-7·A-10). 통합 판정(네 card 병합 head): 전체 suite, 연기 시험 1~2회로, gap-detector ≥ 90 %.

### 오케스트레이터 명령(test 시작까지, 절대 경로)

```bash
git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12 merge --no-ff master -m "Merge master into integ/it12 -- 계획 v6.38.8·design v1.16.3 (O-226 위임 A-33)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ" \
&& cp C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-04/it/20261104-it*.md C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/docs/02-design/specs/ \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12 add docs/02-design/specs \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12 commit -m "docs(card): IT-1·IT-2c·IT-2d·IT-2e 재동결 -- 계획 v6.38.8·design v1.16.3 (O-226 위임 A-33)" --trailer "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" --trailer "Claude-Session: https://claude.ai/code/session_011z1Da2eXxGTuSm8caX2GaZ" \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-it1-input-point-test -b role/test/20261104-it1-input-point integ/it12 \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-it2c-icm-config-test -b role/test/20261104-it2c-icm-config integ/it12 \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-it2d-front-wiring-test -b role/test/20261104-it2d-front-wiring integ/it12 \
&& git -C C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261104-it2e-partial-snapshot-test -b role/test/20261104-it2e-partial-snapshot integ/it12
```

그 뒤 test agent 넷을 동시에 띄운다. test 브랜치는 같은 head에서 갈라지므로 code 착수 때 card 순서(IT-1 → IT-2c → IT-2d → IT-2e)로 쌓고, 겹치는 test 파일은 그때 맞춘다. base 전체 test 측정(S-2)은 병합 head에서 측정 agent 하나가 따로 돈다.

## 7. 멈춤·판단 항목(권고 포함)

| # | 항목 | 권고 | 대안 | 성격 |
|---|---|---|---|---|
| S-1 | **GL-1 코드 미병합**: master `0d99a813`에 card(`20261103-gl1`, A-29)는 들어왔고 코드·도구는 아직 없음. N6.1상 엔진 card 병합 앞(A-6), `scan_shared_calls`도 그 몫 | IT test·code는 진행, master 병합은 GL-1 코드 병합 뒤 | IT 먼저 병합 ⚠ A-6·표 #10 | 순서 |
| S-2 | **base 실패 목록**: `d7800c03` 메시지 'O-181 영향 23건'. 현재 수는 미측정. A-31 `fix/o181-tests` master 미병합 | 기준 = 전체 0 failed. base에 실패가 남으면 목록을 오케스트레이터에 올리고 판정을 멈춘다(A-31 병합 여부 확인) | '새 실패 0'으로 읽기 ⚠ 기준 약화, 위임 밖 | 판정 멈춤 조건 |
| S-3 | **`rule_hash` 재기록 -- 결정됨(A-33·A-34)**: rule 파일을 고치는 커밋 안에서 두 `structure.json`의 `rule_hash` 줄만 재기록, IT-1 ③·IT-2c 해당 커밋, T-RH '사실이 적용됨', 감사가 diff·값 비교. IT-2d·IT-2e는 rule 파일 변경 없음 | -- | 통합 끝 1회 ⚠ 중간 커밋 사실 소실(fail-open) | 위임 |
| J1 | 행 꼴 5원소 유지(일반 1차 행 = R0 몫) | 채택 | 일반 꼴 ⚠ 소비자 0 | 작성자 판단 |
| J2 | F 닿는 입력 점: p = KVL relation, n = `input_point`·`known = p` | 채택 | 새 relation ⚠ | 작성자 판단 |
| J3 | 칸 `GvgsSummary.gate_source_same` | 채택 | `fixed_vgs` 뜻 넓힘 ⚠ 규칙 3 | design이 재동결에 위임 |
| J4 | 용량 전용 노드 = 갈래 5, 새 code `icm_capacitive_only_node`. design 41 §4.7에 자리 없음(N3.8 조건 넷 (3)만) | 채택, design 한 줄 후속 | 조건 무시 ⚠ O-211 / 떠 있는 노드 0 유지 ⚠ fail-open | design 공백 |
| J5 | cfg 띠 '구별 불가' 칸 없음. 띠 기록은 `dc_seal_7` `indistinct`(§4.8-3, EO-1). W5 '거부 + 기록' toy는 EO-1로 | 채택 | cfg 칸 ⚠ 소비자 0 | W1·W5 읽기 |
| J7 | P:1341 'IT-2a keep 목록' = 코드 변경 0(실측) | 표 문언 정정만 | | 계획 표지 |

**독립 판정 반영**(`it_validation.md`): I1(IT-1 `_windows` 범위), I2(`Circuit` 읽기 전용, `ratchet.new` 0), m1, m2, m3 반영. m4~m8은 지시 범위 밖이라 미반영.

**문언 잔재(동작 판단 아님, 계획·design 후속)**: N6.5 완료 5 '새 필드 = 바이어스 고정 넷'(범위 5·표 #19와 다름), N6.6 완료 (14) 'E-22 toy'(E-22 대상 소멸), 42 D-IT2 행 안 `_conduction_rows`·일반 1차 행·`dc_seal`, 41 §4.7-5 'DE-1 뒤 `dc_window_def`'(W1 대체 표지 있음), P:1341.

**기간 표지**: IT~EO-1 사이 봉인 7(+tol)과 창(여유 0)의 경계가 다르다. 봉인이 더 엄격해 fail-open 아님. `region_rows` VDSAT 조회와 봉인 7의 같은 입력 재계산은 HC-S까지 남는다(새 B 표지, 래칫 기록).

**미측정**: base test 수, 연기 시험 회로, IT-2c 착수 실측, 13회로 전체, `kernel_run.py`·`seal.py` 줄의 IT-2d head 값, 문서 잔재 전수(표본만). card는 독립 검증 전이다.
