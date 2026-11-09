# b26pre·backfill 사전 실행 -- card 35 실제 도구(a17b8bd) 기준 (2026-10-02)

작성: 리허설 agent. 저장소·audit worktree·_drafts 기존 파일은 읽기만 했다. 모래상자 `/c/g265`(측정 뒤 삭제).
도구 = audit worktree 병합본 `a17b8bd`(T `0ef7430` + K `b70a05a`, gate master `4a286f0` 위)의 `tools/gates`. 복제는 작업 트리 저장소에서 `-c core.autocrlf=false --no-local`, a17b8bd는 role/audit 브랜치로 복제본에만 들어왔다.

## 0. 결론(값 차이)

**값 차이 0.** 키트·card에 적힌 수치가 실제 도구로 전부 그대로 나온다. 고쳐야 할 숫자는 없다.
선택적 문구 갱신(시제품 기준 → 실제 도구 재확인)과 deferred였던 항목 채우기만 아래 §5에 file:line으로 적는다.

| 항목 | 적힌 값 | 실제 도구(a17b8bd) | 판정 |
|---|---|---|---|
| b26pre 주표 N2w 대상(B1..H4, v4 head) | 20/20 대상 | 20/20 targeted(전체 301 대상 / 2,141 not_targeted, scope_proto 대칭차 0) | 같음 |
| b26pre 주표 죽임(시제품 19 test) | 20 중 18 | **18/20 죽음**, 생존 = SR 11800·11879(backfill 2) -- 죽인 test 이름까지 card 표 1과 같음 | 같음 |
| b26pre 주표 → v5 head(C4B..H5, B26-1 착수 정의) | (B26-1 인계: backfill 2 사라짐) | 18 targeted, 2 absent(11800·11879 문장이 head에 없음), 경로 당김 `body[10].body[2]→body[10].body[1]`, `body[13]→[12]`, `body[14]→[13]` | 인계 문구(spec:166~167)와 같음 |
| backfill v3count(launch, 실제 pytest) | 대상 4 · not_targeted 93 | targeted **4**, not_targeted **93**(97), verdict **PASS**(4/4 killed, b26pre 시제품 test가 base에 있는 상태, backfill test 없이) | 같음 |
| B26-1 V3 대상(v5 = C4B..H5) | 299 | **299** / not_targeted **2,136**(2,435), defs 32 | 같음 |
| carry check heredoc(out_check_test.sh 피검, 엄격 m1~m4) on 실제 출력 | -- | U3 실행(H5T): **전체 heredoc PASS**(m1~m4 포함, 생존 1 = U3, 묶기 해시 일치). v5 실행(가짜 pytest 전부 생존): m1~m4 블록 **PASS**, 전체 heredoc은 '생존 U3 1개' 단정에서 FAIL(기대대로 -- 생존 299) | m1~m4 PASS |

## 1. 모래상자(가짜 gate)

`/c/g265/sb/r` = 작업 트리 저장소 복제(autocrlf false) → `master` ff `a17b8bd` → 커밋 4개(빈 hooksPath):
1. `audit:` 35 판정 기록 자리표시(V1~V10 PASS + `DRY_RUN` 키) + gate_config/pre-receive 경로만 모래상자로(`post_p10b_dryrun_setup.sh` 방식)
2. `docs:` 승인 기록 `20261001-b26-phase3-cards`(= `_drafts/approval_20261001-b26-phase3-cards.md` 그대로)
3. B34 코드 모의 = `mk_b1` SD(사이트 1·2·3·11·11b, post35_kit B1과 같은 파일), 트레일러 `Change-Id: 20260930-b34-grammar-explicit`
4. `audit:` B34 판정 기록 자리표시

bare 가짜 gate = 실제 `pre-receive`·`gate-runner.py`(EL4), 복제본 `core.hooksPath=.githooks`(EL3) + `.claude/hooks/role_*.py` 복사. gate master `265e9f7`.

## 2. b26pre (`b26pre_launch.sh --repo/--state/--wt` 모래상자)

* `conds`: exit **0·0·0·0·0**, 조건 3 규약 전체 0, approval 줄 gate에 있음, `targets_by_def` = **3**(≥1 -- 244행 단정 통과), 역할 브랜치 없음. rc 0.
* `local`: pre OK(measured `dd60db6` → gate: sizing_recipe 차이 0, SD 커밋 1개 전부 Change-Id B34, `_approved_ids` 39) → card: parse_spec_card `('3','test-only','no',['20261001-b26-phase3-cards'],[],11)`, interface card 기존 함수 **19** = IFC_FUNCS, 밑줄 0, EL3 통과 → final OK. rc 0.
* push(EL4) 통과(accept-log 한 줄) → `after-push` OK.
* **변이 전 dry run(새 test + 옛 코드)**: 시제품 19 test(`proto_v2_test_b26pre.py` 17 -- 계약 10은 card v3 단언 'Mx1·Mx2 중 정확히 하나'로 바꿔 넣음 + `b26_reconcile/proto_test_b26pre_trace.py` 2)를 `test_b26pre_existing_paths.py`로 gate `a4645b8`(a17b8bd + B34 모의) archive 사본에 넣고 gate ini·`--gmid-phase=3`: seed 0 **19 passed**, seed 1 **19 passed**(test-only 기대 = base PASS).
* **주표 20 죽임(실제 도구 변이)**: 실제 도구 `changed_defs`·`_Scope.targets`·`mutants`·`_replace_def`(a17b8bd)로 B1..H4 대상 집합을 만들고, head id를 B1(base+B34) 문장에 대응(가장 안쪽 문장 ast.dump, `rails=` 키워드 제거 -- trace 2는 for 머리가 B26-1에서 바뀌어 `iter` 식으로 대응)시켜 base 사본에 같은 연산자 변이를 써서 시제품 파일만 실행(seed 1):
  죽음 18 -- SR 11696·11698·11700(euler_fixup_group_split), 9404·9406 × 두 def(ofcb_lutless_repair), 6573(resolve_stack_candidates), 11801(growth_already_ok), 11877(growth_zero_rounds), 11880(growth_zero_rounds_euler), 11881(둘 다), SD 4521·3278·6884·6886(B34 사본 줄 = card 4529·3282·6892·6894), trace const+(두 test)·arith(three_branches_order) 1563(= card 1567, B34 1563).
  생존 2 -- SR 11800·11879(backfill). 기준·복원 실행 19 passed.
  참고: v4 모의 head(H4) 자체는 실행 불가(측정 전용 -- `sizing_recipe.py:9150` UnboundLocalError로 19 failed)라 죽임은 이전 통합 측정과 같이 base 대응으로 쟀다.

## 3. backfill (`backfill_launch.sh`, b26pre 병합 모의 뒤)

* b26pre 병합 모의: 시제품 19 test(`Role: test`) + 판정 기록 자리표시(`Role: audit`)를 EL3 켠 채 커밋. push는 EL4가 거부(`로더 규칙 4: 스키마 위반 … 'DRY_RUN' was unexpected` -- 자리표시 기록이라 정상) → 이전 리허설처럼 bare gate에 직접 fetch(hook 없이) + accept-log 한 줄. gate master `636ec96`.
* `conds`: exit **0·0·0·0·0**, approval 2건 gate에 있음, `targets_by_def` 3. rc 0.
* `--scratch /c/g265/bfv3 local`: pre OK(sizing_recipe·selftest 차이 0, b26pre test 있음, U-BF 기록 = 초안) → **v3count: mutate_changed exit 0, `{"verdict":"PASS","mutants":4,"killed":4,"survivors":[],"not_targeted":93, targets_by_def {run_matching_safety_with_finger_growth: targeted 4, not_targeted 93, deleted_statements 2, def_header_changed false}}`** → 대상 4 = V3_WANT, scratch 지움 → card: parse_spec_card `('3','red-green','no',['20261001-b26-backfill-interdig-fix','20261001-b26-phase3-cards'],[],11)`, interface 4행 → final OK. rc 0.
  대상 4 id(같은 명령 재현본 `bf_v3_replica.sh`, 출력 보존): `stmt_delete body[9]`, `body[11]`, `body[9].body[1]`, `early_return body[1]` -- 전부 killed.
* push(EL4) 통과 → `after-push` OK.
* **변이 전 dry run(새 test + 옛 코드)**: `proto_bf_test.py` 2 test를 gate `636ec96`(b26pre 모의 병합본) 사본에: seed 0·1 모두 **2 failed**, 이유 `AssertionError: assert False is True`(`e["interdig_ok"] is c3b[0].ok`, 3b `seg1_seg1: 인접` ok=True) -- card '판정 유형 근거' red 그대로.
  참고 green: 같은 사본에 수정 후보(11800·11879 삭제) → seed 0·1 **2 passed**, b26pre 시제품 19 passed.

## 4. B26-1 V3(299)와 carry check

* post35 키트(`post35_kit/remeasure.sh --scratch /c/g265 --skip-slow a17b8bd`, 실제 도구 + 가짜 pytest): V3-B26v5 **299/2136**, V3-B26A 299/2141, V3-B26v4 301/2141, V3-B26U3 299/2136, V3-BF 4/93, V3-B34 10/45(ids 10/10), V3-P9 12/16 -- 전부 scope_proto 대칭차 0, `--out` 순서 일치. EQ4-b26a 4/4 대상, EQ4-b26v5 range `const-` 대상·`[0]` `const-` absent. 69항목 중 changed 20은 전부 G1·B33 줄 번호·앵커(아래 §6), skipped 1(G1 redteam).
* v5 실제 도구 출력을 따로 다시 받아(raw 판정 JSON 보존, `C4B..H5`, 가짜 pytest exit 0): verdict FAIL, mutants 299, not_targeted 2136, 생존 299, defs 32.
* `out_check_test.sh`의 추출 규칙(`split()` -- `local v3; v3=$("$PY" -B - "$WT_A/$AUD/attempt1_v3.json"` 다음 줄 ~ `EOF`, `b26_1_carry.sh` 240~298행, 59줄)으로 heredoc을 뽑아 인자 `<v.json> <out.jsonl> <head SD> '^stick_diagram:find_differential_pair_candidates:const-:' <SD>`로 실행:
  * U3(H5T, 가짜 pytest = `range(i + 0, len(chains))`만 생존): **PASS** -- 출력 `stick_diagram:find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right@cdab7b02…`(묶기 해시 = head def 해시, 노드 = `range(… + 1, …)`의 1). m1~m4(닫힌 result 집합, int 전용, `not_targeted`·`targets_by_def` 필수, not_targeted 레코드 키 `["id","result"]`, Σtargeted = mutants 299, Σnot_targeted = 2136) 전부 통과.
  * v5(전부 생존): m1~m4 블록(`# 범위 card 35(` ~ `assert v["killed"]`, `== [mid]` 줄 제외 20줄) **PASS**. 전체 heredoc은 `('생존이 U3 대상 1개가 아니다 -- 멈춤(card 단계 1)', …)`에서 FAIL -- 가짜 pytest라 당연(실제 1차 출력은 B26-1 1차 auditor 몫).
  * 사례 fixture self-test(`out_check_test.sh` 자체)는 돌리지 않았다 -- 결과를 `_drafts/b26_1_kit_selftest/out/`에 쓰기 때문(쓰기 금지 범위).

## 5. 갱신 후보(file:line -- 값은 같고 문구·deferred만)

| 파일:줄 | 지금 | 제안 |
|---|---|---|
| `post35_remeasure.md:40` (B26PRE-20 행) | '18 죽임'은 deferred | 실측: 실제 도구 변이로 18/20 죽음(생존 SR 11800·11879), 이 문서 §2 |
| `post35_remeasure.md:45` (CARRY-FULL 행) | 기대 PASS | 실측 PASS(a17b8bd) + v5 실제 출력에서도 m1~m4 블록 PASS |
| `draft_b26_backfill_audit.spec.md:159` | '사전 수치 4는 시제품 `scope_proto.py` N2w 기준이다' | (선택) '실제 도구 a17b8bd로 4·not_targeted 93 재확인(모래상자, b26pre 시제품이 base에 있으면 V3 PASS 4/4 killed)' |
| `draft_b26_backfill_audit.spec.md:94~97` | 대상 4·생존 0(head에 이 card 시제품 test 포함 측정) | (선택) b26pre test만 있는 base에서도 4/4 killed라는 사실 한 줄 -- 착수 판정 수치는 auditor 몫이라 필수 아님 |
| `backfill_launch.sh:312` | 'N2w 시제품 기준' 메시지 | (선택) '실제 도구 a17b8bd 재확인' -- 동작 무관 |
| `draft_b26pre.spec.md:12` | 분류기 = `v3_scope_widen.py`(시제품) | (선택) 실제 도구 대상 집합이 시제품과 대칭차 0(B1..H4 301, 주표 20/20) |
| `b26_backfill_briefs.md:71` | N2w 대상 4(scope_proto) | (선택) 실제 도구 4/93 PASS |
| `draft_b26pre.spec.md:472`, `draft_b26_backfill_audit.spec.md:177` | `dd60db6` 조건 exit 128·128·0·128·128 | 시점 기록이라 고치지 않아도 됨. 참고: 지금 실제 gate `4a286f0`는 조건 1(V3 묶기 기록)이 이미 0 |

measured rev(`dd60db6`)는 그대로 유효: `dd60db6..a17b8bd`에서 sizing_recipe.py·stick_diagram.py·selftest 변경 0(엔진 .py 차이 0).

## 6. 범위 밖 부수 발견(post35 키트 같은 실행)

* G1 시제품 `g1_kit/install_proto.py` 앵커 `mc print`가 a17b8bd에서 **0개**(옛 1) → `G1-INSTALL` 실패('앵커 mc print: 0개'). G1 card 착수 전 재앵커 필요(post35_remeasure.md 'G1-ANCH-*' 행 예상대로).
* `mutate_changed.py` 줄 이동(G1·B33 인용): `changed_defs(base_src` 413→676, `in mutants(` 423→691, `make_clone(` 371→627, `_is_source` 363→619, `rch.build_graph(head_files)` 365→621, `rch.reach` 263→519, `TimeoutExpired` 404→661·`return "timeout"` 405→662, `killed += 1` 449→725, json.dumps 465→741. `reachability.py`·`source_lint.py`·`rt.py`·`run_all.py:98`은 같음. 게이트 밖 호출 12줄·9파일 그대로. 출력 키 = 옛 키 + `not_targeted`·`targets_by_def`.
* `backfill_launch.sh:276` v3count 복제는 `-c core.autocrlf=false` 없이 clone한다 -- 전역 autocrlf 때문에 'LF will be replaced by CRLF' 경고만 나고 numstat `0 2`·대상 수는 정상(blob LF로 씀). 동작 영향 없음.

## 7. 격리 확인

* 실제 저장소: HEAD `4a286f0`, status md5 `dcc7b56b…`, reflog 345줄, refs 목록 -- 시작과 끝 같음. 로컬 `gate/master` `4a286f0`. audit worktree HEAD `a17b8bd`, status는 기존 auditor 디렉터리 1줄(`?? .ai/verification/20260930-v3-changed-stmt-scope/`) 그대로(이 작업은 쓰지 않음).
* TMP·TEMP는 모든 실행에서 `/c/g265/tmp`(launch는 상태 파일 옆 `.tmpd`). `C:\Windows\Temp\gmid-redteam`은 있으나 생성 17:14·마지막 쓰기 17:17로 이 작업(19:18 시작) 전 것 -- 이 작업 산출물 아님(redteam도 돌리지 않음).
* `/c/g264`(다른 agent) 건드리지 않음. `/c/g265` 삭제.
