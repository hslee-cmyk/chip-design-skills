# B34 사슬 착수 준비 확인 -- 문서 커밋 3건 뒤 (dafe5cf → fd4ef8c → b4734cd)

작성 2026-10-06. 실제 저장소 읽기만 했다(git -C, 이 파일만 씀). 모래상자 `/c/g281`(TMP·TEMP 그 안, 끝나고 삭제).

## 0. 결론

**멈춤 0. 고칠 file:line 없음.** B34 키트는 conds → local1 → push #1(모래상자 EL4) → after-push-appr → local2 → push #2 → after-push까지 전부 통과했고,
B34 자리표시 병합 뒤 b26pre conds/local/push/after-push, b26pre 자리표시 병합 뒤 backfill conds/pre도 전부 통과했다.
키트 셋은 `plan_tables_hash`를 하드코딩하지 않는다(`pre`에서 읽어 상태 파일에 적고 뒤 단계에서 '불변'만 본다) -- `7167e028…`·`16b899d1…` 문자열은 `b34_launch.sh`·`b26pre_launch.sh`·`backfill_launch.sh`·`b34_kit`·`b26bf_kit`에 0건.

## 1. 문서 커밋 3건 시뮬레이션과 실제 커밋 대조

오케스트레이터가 도중에 실제로 올렸다(29d2fc2·300fd65·7f67ec3·fd4ef8c, 그 뒤 b4734cd = `.ai/context.md` 22줄 append). 시뮬레이션 결과는 실제와 같다:

| 커밋 | 시뮬레이션(dafe5cf 위) | 실제 |
|---|---|---|
| (1) D-11 계획 | `p3fq_kit/variant.py qtok` → numstat 1 1, 계획 blob `f2f4d2ee…` → `8f6e21db…`, plan_tables_hash 전후 `7167e028…`, EL3 통과 | 29d2fc2 계획 blob `8f6e21db…` -- 같음 |
| (1) D-11 승인 | `merge_gate.py diff-hash` target `441b80e1…`(runbook 사전값과 같음), parse-approval OK, 모래상자 EL4 push 통과 | 300fd65 -- `diff_base`·`diff_head` 두 줄(커밋 해시)만 다르고 나머지 바이트 같음 |
| (2) design 30 | `design30_dod_corrections.py --check` pending 12 → 적용 바뀐 줄 [786,788,789,793,1034,1036,1037,1038,1040,1044,1099], history +1 | 7f67ec3 두 파일 blob(`9cb9da03…`, `3a5543ae…`) 시뮬레이션과 같음 |
| (3) F1 두 행 + plan_tables 승인 | 승인 초안 = fd4ef8c의 `.ai/approvals/20261002-p3-f1-workspaces-write-path.md`와 바이트 같음(cmp), 계획 +2행(`run_harness.py` 행 뒤), hash `16b899d1c745ddd0…` | fd4ef8c를 모래상자(7f67ec3 + 경로 합성 커밋)에 cherry-pick → EL3 통과, **모래상자 EL4 push 통과**(accept-log 1줄), hash 7167e028… → 16b899d1… |

(3)의 plan_tables 승인은 EL4가 받는다(모래상자 재현 + 실제 gate가 이미 fd4ef8c를 받음).

## 2. 키트 실행(모래상자 = fd4ef8c 내용 + gate 경로 합성 커밋)

| 단계 | 결과 |
|---|---|
| b34 `conds` | 1:0 2:0 3:0 4:0 5:128, 조건 4 규약 0, exit 3(기대 -- 5는 P가 채움), targets_by_def 3 |
| b34 `pre` | measured `5f643a9` → gate: 줄 인용 대상 차이 0, tools/ 변경 10, **`_approved_ids` 38(문서 커밋 3건으로 불변 -- diff·plan_tables 기록은 decision이 아님)**, **plan_tables_hash `16b899d1…`**(이전 리허설 `7167e028…`) |
| b34 `appr`/`final-appr` | 승인 기록 4414 B, parse decision `Q-B34-PHASE-CARDS-PHASE3`, ids +1 = ATARGET, plan hash 불변 |
| push #1 / `after-push-appr` | EL4 통과 / 조건 0·0·0·0·0 |
| b34 `local2` | doc: test_phase2_stale_refs 18 passed, numstat 17 16 / card: parse_spec_card ('3','red-green','no',[두 승인],[],12), interface 14 함수·145줄 / final OK |
| push #2 / `after-push` | EL4 통과 / OK |
| B34 자리표시 병합 | mk_head(사이트 1·2·3·11·11b, HEAD SD) Role: code + 판정 기록 자리표시(V1~V10 PASS, DRY_RUN) -- bare gate 직접 fetch + accept-log(이전 리허설 방식) |
| b26pre `conds` | 0·0·0·0·0, approval 있음, targets_by_def 3 |
| b26pre `local`(pre→card→final) | measured `dd60db6`: SR 차이 0, SD 커밋 1개 전부 Change-Id B34 / `_approved_ids` 39 / hash `16b899d1…` / parse ('3','test-only','no',['20261001-b26-phase3-cards'],[],11), interface 19 함수·163줄 |
| push / `after-push` | EL4 통과 / OK |
| b26pre 자리표시 병합 | `b26pre_v2_scripts/proto_v2_test_b26pre.py`를 NEWT 경로에 + 판정 기록 자리표시 |
| backfill `conds` | 0·0·0·0·0, approval 2건 있음 |
| backfill `pre` | SR·selftest 차이 0, b26pre test 있음, 승인 기록 = 초안, approval 2건 parse OK, `_approved_ids` 39, hash `16b899d1…` |

backfill `v3count`(--scratch, 실제 pytest)는 이번 범위(conds/pre) 밖이라 돌리지 않았다 -- 직전 리허설 4/93 PASS, 이번 문서 커밋은 SR·tools/를 바꾸지 않는다.

## 3. 요청 항목별

* **MEAS_PATHS**: b34·b26pre·backfill에는 없다(measured 대조 경로 = SD·SR·install.py·references·selftest -- 문서 커밋·`.ai/context.md` 무관).
  `MEAS_PATHS`가 있는 곳은 `d0a_launch.sh:79`·`d0b_launch.sh:101`이고 둘 다 `$PLAN`을 포함한다 → (1)(3)이 계획을 바꿨으므로 D0a·D0b의 measured rev는 fd4ef8c 이후여야 한다. 지금 두 초안(`draft_p3_d0a.spec.md`·`draft_p3_d0b.spec.md`)에는 `**measured at**` 앵커가 없어(G1/D0a 병합 뒤 재는 설계) 지금 고칠 줄은 없다. `.ai/context.md`는 어느 MEAS_PATHS에도 없다.
* **plan_tables_hash**: 키트가 보는 값 `16b899d1c745ddd0d305b2a977eecc74b0c830d89507d7eb3476b7323a08aec1`. 하드코딩 없음 -- 수정 불필요. (참고 문장: `b34_post35_dryrun.md` §4-5의 `7167e028…`는 이전 판 관찰 기록일 뿐.)
* **approved_ids**: B34 pre 38 → P 뒤 39(이전 리허설과 같음). D-11(diff)·F1(plan_tables) 기록은 `_approved_ids`(decision만)에 들어가지 않는다.
* **approved hashes / 승인 기록 수**: 키트는 approval 줄 id만 parse-approval로 본다 -- 새 기록 2건 영향 없음.
* **이름 충돌 allowlist**: 세 키트에는 NEWT 존재 여부 검사뿐(이름 충돌 grep 없음) -- 걸린 것 없음.
* **measured-rev 앵커**: B34 `5f643a9`, b26pre·backfill `dd60db6` 그대로 유효(그 뒤 대조 경로 변경 0).
* **b4734cd(`.ai/context.md` +22)**: 세 키트의 `diff` 대상·`status --porcelain` 경로(docs/02-design/specs/, .ai/approvals/, references/, docs/) 어디에도 안 걸린다. 모래상자는 fd4ef8c 내용으로 돌렸고 b4734cd 차이는 이 파일뿐이라 결과가 같다.
  실제 실행 때 `pre`는 로컬 `HEAD = gate/master`를 요구하므로 로컬 master를 b4734cd로 맞춘 상태여야 한다(지금 실제 저장소 master·gate/master 모두 b4734cd 확인).

## 4. 격리

실제 저장소: 쓰기 없음(git -C 읽기·fetch 없음). `/c/g281` 삭제. 모래상자 hook 설정·리다이렉트는 `/c/g281/*.sh` 안에서만(EL1이 `git -c core.hooksPath`를 거부).
