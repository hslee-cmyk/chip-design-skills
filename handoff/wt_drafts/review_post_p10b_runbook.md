# 독립 검토 -- post_p10b_runbook v2 + 승인 초안 3개 + md 일치 spec card + DoD 브리핑 v4

검토 2026-10-01(검토자: 독립 agent, 저장소 읽기 전용, 모래상자 `C:/g129`, 끝에 삭제).
대상: `post_p10b_runbook.sh`/`.md`, `post_p10b_dryrun_setup.sh`, `post_p10b_context_append.py`, `approval_20261001-b47-md-sync.md`, `approval_20261001-p2dod-e2-wording.md`, `approval_20261001-b26-backfill-interdig-fix.md`, `draft_md_sync.final.spec.md`, `phase2_dod_brief.md`(v4).

## 판정

**조건부 통과 -- B 1건(인자 해석, 한 줄 수정)을 고치면 실행 가능.** 승인 원문은 전부 바이트 단위 일치, 모래상자 끝까지 재실행 통과(7커밋 + EL4 수신 + after-push + worktree), DoD 가드는 잘못된 상태 7가지(내가 만든 5가지 포함)를 모두 거부했다.

## B (막는 것)

### B1. 단계 뒤에 붙인 옵션은 소리 없이 무시되고 실제 저장소·실제 상태 파일로 돈다
`post_p10b_runbook.sh` 옵션 루프는 `while [ $# -gt 1 ]; case … *) break`라서 **옵션이 단계 이름 앞에 있을 때만** 읽힌다. 단계 뒤의 옵션은 남은 인자로 버려지고 기본값(`R`=실제 저장소, `STATE`=`_drafts/post_p10b_state.txt`, `T`=`_drafts/b47_render`)이 쓰인다. 파서 부분만 복사해 실측했다(`C:/g129/argtest.sh`, 실제 스크립트는 실행하지 않음):

```
argtest.sh pre --repo /c/g129/r --state /c/g129/s   -> stage=pre R=/REAL STATE=/REAL/state rest=[--repo /c/g129/r --state /c/g129/s]
argtest.sh --repo /c/g129/r pre --state /c/g129/s   -> stage=pre R=/c/g129/r STATE=/REAL/state   (반쪽만 모래상자)
argtest.sh --repo /c/g129/r --state /c/g129/s pre   -> 정상
```
결과:
* P10b push 뒤에 `… post_p10b_runbook.sh local --repo <모래상자> …`로 사전 시험을 하면 `pre`가 실제 저장소에서 통과하고(그 시점에는 착수 조건이 다 맞는다), **실제 master에 커밋 7개를 만든다**. §4대로 EL1이 `reset`·`revert`를 막으므로 되돌릴 수 없다. 첫 사전 시험 사고(환경 변수 소실 → 실제 저장소)와 같은 종류다.
* 반쪽 지정(`--repo`만 앞에)이면 모래상자 실행이 실제 상태 파일을 쓰고, `pre`의 `rm -f "$STATE"`가 실제 실행 상태 파일(C1·D·MEASURED_AT…)을 지운다 -- 실제 실행 뒤 `after-push`·이어 하기가 깨진다.

고칠 것(한 곳): 루프 뒤에 `[ $# -eq 1 ] || { echo "인자 오류: 옵션은 단계 앞에, 남은 인자 $*" >&2; exit 2; }`. 더해 `--repo`를 주면 `--state`·`--render-tmp`도 필수로(기본 `_drafts` 경로와 섞이지 않게), 또는 `R`이 기본값이 아니면 `STATE`·`T`가 `_drafts` 아래면 거부. 고친 뒤 위 세 줄 모양을 다시 재서 runbook §7b에 적는다.

## S (고쳐야 할 것)

### S1. md 일치 card 전체 주기를 DoD 앞에 둔 것은 사용자에게 알린 순서와 다르다 -- 실행 전에 알려야 한다
* 사용자 지시(`_drafts/user_decisions.md` 2026-10-01 card 순서): "P10b 끝나면 push하고 Phase 2 완료 판정 진행해".
* 16:40 답 직후 오케스트레이터가 사용자에게 보낸 메시지(jsonl 5047행, 07:40:20Z): "1. P10b push 2. 문서 커밋 3. Phase 2 완료 판정 4. md 일치 card: 재생성 커밋과 승인 기록을 함께 올립니다" -- md card는 **DoD 뒤**로 알렸다.
* runbook §3·§6, 브리핑 v4 §0·가드 (4)·§6.1~6.4, spec card '결정 필요 항목' 순서 문단은 모두 **DoD 전**(test → audit → push → 정리 → DoD)으로 서로 일관된다(점검 3 자체는 통과 -- 아래). 그러나 이 바뀐 순서는 사용자가 본 적이 없고, runbook §3은 "보고 때 한 줄"로 사후 보고만 계획한다. DoD가 test-author·auditor 한 주기만큼 늦어진다.
* spec card 145행 "사용자 지시 순서(P10b → Phase 2 DoD → …)에 이 card의 자리는 없다"는 사용자 원문에 대해서는 맞지만, 오케스트레이터가 07:40:20Z에 'DoD 뒤 4번'으로 알린 사실이 빠져 있다.
* 권고: runbook 실행 **전** 보고에 한 줄로 알린다(예: "md 일치 card는 phase 2 card라 DoD 뒤로 두면 phase 판정이 꼬여 DoD 앞으로 옮깁니다 -- DoD가 card 한 주기 늦어집니다"). 이것은 원칙상 기본안이라 질문이 아니라 알림으로 충분하다(메모리 '결정은 원칙으로 기본안부터'). spec card 145행에 07:40:20Z 문안을 한 구절 더한다.

### S2. `post_p10b_dryrun_setup.sh`가 지금은 재현되지 않는다
`git clone --no-local`은 ref에서 닿는 커밋만 가져온다. P10b 1·2차 병합 커밋(`4294048`, `e67211c`)은 역할 브랜치 정리 뒤 어느 ref에서도 닿지 않아 `merge: e67211c… - not something we can merge`로 멈췄다(실측). 나는 사본(`C:/g129/setup_mod.sh`)에서 clone 뒤
`git -C "$S/r" fetch -q --upload-pack="git -c uploadpack.allowAnySHA1InWant=true upload-pack" "$R" "$MERGE"`
한 줄을 더해 돌렸다(메인은 읽기만). 스크립트에 이 줄(또는 '병합 커밋이 ref에서 닿아야 한다' 사전 확인)을 넣고, runbook §0의 "재현용" 문구를 고친다. 사전 시험 전용 도구라 S.

## minor

* m1. E2 정정 문구(patch_e2_wording NEW)는 질문 선택지 문안('exit 0, 면제되지 않은 발견 0(면제 = decision 승인 기록이 적힌 path::rule, 현재 1건)')보다 길다 -- "`\"exempt\": true`를 붙인 발견", "면제 발견은 DoD 기록에 path·line·rule·승인 id로 적는다"가 더해졌다. 기준을 더 엄격하게 하는 쪽이고 승인 기록 '덮는 것'이 새 문구 전체를 인용하므로 범위 초과로 보지 않는다. 다만 보고 때 "선택지 문안을 다듬어 넣었다(DoD 기록 의무 추가)"를 한 줄 적는 편이 안전하다.
* m2. 브리핑 §2의 `git clone … "$R" "$ISO"`는 `refs/heads`·`HEAD`만 가져온다(`refs/remotes/gate/*` 아님). 메인 `master`가 H보다 뒤면 H가 복제본에 없어 `checkout --detach "$H"`가 `fatal: unable to read tree`(exit 128)로 멈춘다(내 W1 첫 시도에서 실측 -- 시끄럽게 멈추므로 안전). md 일치 audit push 뒤 정리에서 `merge --ff-only gate/master`를 하므로 보통은 맞지만, §0 착수 조건에 "메인 `master` = H"를 한 줄 더하면 헛걸음이 없다.
* m3. `patch_design20_231.py`·`patch_template.py`·`patch_history_groupAB.py`의 `--root` 기본값이 실제 저장소다(runbook은 항상 `--root "$R"`을 넘겨 현재는 무해). 기본값을 없애고 `required=True`로 하면 B1류 사고 면이 하나 준다.
* m4. runbook.md 머리 "기준 gate master = a796468", §1 "지금(17:00 무렵) role/audit 머리 36a6ec8" 등 시점 문장이 낡았다(§7 끝에 0f23786 이동은 적혀 있음). 또 검토 중 실제 저장소에 `role/audit`·`role/code`(·`role/test` 이동, 572d767/b7b1e00)가 다시 생겼다 -- P10b 재시도 진행 중으로 보이며 `pre`가 정리 전에는 멈춘다(정상).
* m5. `fill_v3_approval.py`는 `merge_gate`·`weakening_diff`를 게이트 캐시가 아니라 `R` 작업 트리 `tools/gates`에서 import한다. 다른 단계는 캐시를 쓴다. 문서 묶음은 tools/gates를 바꾸지 않아 값은 같다(실측 target 동일) -- 표기만 맞추면 된다.
* m6. 가드 (1)의 제목 접두 매칭(`index($2,p)==1`)은 같은 접두를 가진 미래 id(예: `…-record-v2`)도 잡는다. 지금은 해당 없음.

## 점검별 근거

### (1) 승인 원문 대조 -- 전부 일치
세션 jsonl `63c6146a-….jsonl`에서 AskUserQuestion `tool_use` 입력과 `toolUseResult.answers`, 해당 assistant 텍스트를 Python으로 뽑아 초안과 문자열 대조(`C:/g129/cmp.py`):

| 초안 | 대조 | 결과 |
|---|---|---|
| b47-md-sync 첫 인용(15:30 보고) | jsonl 4693행 assistant 텍스트(06:30:56Z = 15:30 KST) 전체 vs 초안 `>` 블록(접두 제거) | **같음**(바이트) |
| b47-md-sync 둘째 인용(16:34 요약) | 5026행(07:34:52Z) 전체 | **같음** |
| b47 답 두 개 | 4698행 06:32:24Z, 5036행 07:40:15Z "응, 그렇게 진행해" | 같음, 시각 15:32·16:40 맞음 |
| p2dod-e2 질문·선택지 3개(label·description) | `toolu_01Xrnynr6gPEWmoA8PHi7ZED`(10:21:50Z = 19:21), 답 "문구 정정 (Recommended)"(10:25:08Z = 19:25) | 질문·선택지 3개 모두 부분 문자열로 정확히 있음 |
| b26-backfill 질문·선택지 3개 | `toolu_01UB8MYiKoGaacm4JJEA3HBd`(10:17:21Z = 19:17), 답 "결함으로 고침 (Recommended)"(10:19:30Z = 19:19) | 정확히 있음. "쟽니다"(2회)도 원문 그대로의 오타 |
| E2 사실 보충 "제안대로 승인 (Recommended)" | `.ai/approvals/20260929-p4-scan-exempt.md` 사용자 원문 | 같음 |

범위: b47 '덮는 것'(재생성 별도 Change-Id 커밋 + test-only 단독 card)은 보고 1·2번 범위 안이고 커밋 경계 차이를 스스로 밝혔다. e2 '덮는 것'은 E2 칸 한 줄(m1 참고), '덮지 않는 것'에 새 면제 제외. u-bf '덮는 것'은 interdig_ok 값 의미 + card 순서(선택지 문안 그대로), 정책·다른 키·V3/V7 면제 제외. 질문 범위를 넘는 항목 없음. 순서 문제는 승인 범위가 아니라 S1.

### (2) 실제 저장소로 새는 경로
* 환경 변수 소실: 스크립트 머리에서 `HOME`·`APPDATA`·`PYTHONIOENCODING` 재설정, 경로는 옵션으로만 -- 내 실행에서도 자식 bash `HOME=/home/HSLEE`를 실측(내 보조 스크립트의 commit이 그것 때문에 실패) -- runbook은 이를 막는다.
* 남은 구멍: **B1**(단계 뒤 옵션 무시). 그 밖의 기본값: `T`·`STATE`가 `_drafts` 아래(B1 고칠 때 함께), patch 3개 `--root` 기본값(m3). python 도구는 모두 `--root "$R"`/`"$R"` 인자로 받고, 캐시는 `R`의 git-common-dir에 만들어진다(모래상자 `C:/g129/r/.git/gmid-gate-cache/…` 실측).

### (3) 순서 -- 문서들 사이에서는 일관, 사용자 알림과는 다름(S1)
* md 일치 card 머리: `phase: 2`, `evidence_type: test-only`, `approval: 20261001-b47-md-sync` -- 완전한 역할 card(test-author → auditor → audit push).
* runbook §6: "gmid-test-author → auditor → audit push → 정리. 그 뒤 Phase 2 완료 판정" -- 명시.
* 브리핑 v4: 제목·§0 "판정 기록까지 gate에 있다 … 그 뒤 DoD", 가드 (4)가 기계로 강제, §6.1 34건(32 + P10b + md 일치), §6.2 phase 2 spec card 18장·기록 17건(md 일치 포함, P3(c) 제외), §6.3 test-only 5건(P1·P3a·P3b·P10·md 일치)·비 test-only 12건, §6.4 기대 31(+md 일치 test 1). 수가 서로 맞는다.
* design 20 §8 card 목록(P1~P10b)에 md 일치 card는 없다 -- §8 밖 3건(restore-plan-functions 등)과 같은 취급이고 브리핑 §6.2가 'B47'로 따로 적는다. 계획 N6.3은 "auditor 판정 기록 PASS"로 목록을 두지 않으므로 충돌 없음. design 20 §10 "Phase 2 마지막 card 병합본"은 test-only 마지막 card(병합 없음)와 문구가 조금 어긋나지만 브리핑 v4가 H = gate master로 정의하고 '어긋나면 절차 메모'라 판정 영향 없음.

### (4) 모래상자 재실행 -- 전부 통과
`C:/g129`(S2 우회 한 줄 외에는 `post_p10b_dryrun_setup.sh` 그대로, 인자 `/c/g129 e67211c… --fake-record`): r HEAD = 가짜 gate master = 합성 audit `977f0b9`.
`post_p10b_runbook.sh --repo /c/g129/r --render-tmp /c/g129/b47_render --state /c/g129/state.txt --wt /c/g129/wt local` → rc 0:

| 단계 | 결과 |
|---|---|
| pre | OK, plan_tables_hash `7167e028…596d`(§7b와 같음), 캐시 `gmid-gate-cache/977f0b9…` |
| c1 / d / appr / card | `9f1e04d` / D `f5b26b1`(D^ = `9f1e04d`) / `1100de5`(decision `['B47-MD-SYNC']`) / `7edc636`(parse_spec_card 2·test-only·no·[b47]·절 11) |
| e2 / e2appr / ubf | `70034ea` / `d1a0983`(fill `written`, target `ddacfe22…ed64` = §7b 값, diff_base `7edc636`·diff_head `70034ea`) / `da00f18`(decision `['U-BF-BACKFILL-INTERDIG']`) |
| final | OK(7커밋, 제목 순서, 계약 9 미리보기 md 2개 등) |
| push | `git -C /c/g129/r push gate master:master` → `977f0b9..da00f18  master -> master`; 가짜 gate `pre-receive`(gate-runner 사본, **EL4**)가 받아 accept-log에 `977f0b9 da00f18 2026-10-01T11:02:50Z` 한 줄 추가 |
| after-push | OK |
| worktree | `worktree add …/20261001-topology-md-sync-test -b role/test/20261001-topology-md-sync gate/master` → `da00f18` |
| 멈춤 확인 | 끝난 뒤 `pre`(상태 파일 사본) → `role/` 비지 않음에서 rc 1; `e2` → HEAD ≠ CARD에서 rc 1 |

### (5) DoD 브리핑 v4 가드 -- 잘못된 상태 거부 확인
§2 코드 블록을 R·G·OUTF만 모래상자로 바꿔 실행(`C:/g129/guard.sh`). 상태는 모래상자 gate master를 직접 옮겨 만들고 `fetch`.

| 상태 | 결과 |
|---|---|
| 그대로(H = `da00f18`, md 일치 spec card 있음·판정 기록 없음) | 가드 (4)에서 멈춤 rc 1 "판정 기록 없음 -- card 끝난 뒤 DoD" (의도대로) |
| 양성 대조: 위 + 자리표시 md 일치 판정 기록 커밋 `333b6b1` | (1)~(5) 전부 통과(P = `977f0b9`, E = `70034ea`, AC = `d1a0983`, target = 재계산 `ddacfe22…`) -- 오탐 없음 |
| W1(내 것) 승인 target 한 글자 변조(`ddacfe22`→`ddacfe23`) | (5)에서 멈춤 "승인 target != 재계산 diff 해시" |
| W2(내 것) 뒤 커밋이 design 20 E2 행을 옛 문구로 되돌림 | (2) 계속에서 멈춤 "H 판 E2 행이 정정 문구가 아님" |
| W3(내 것) 같은 Change-Id `20261001-p2dod-e2-wording`을 단 두 번째 커밋 | (2)에서 멈춤 "커밋이 정확히 1개가 아님" |
| W4(내 것) gate가 fetch 뒤 움직임(추적 ref 낡음) | 머리에서 멈춤 "gate/master 추적 ref가 gate와 다름" |
| W5(내 것) 뒤 커밋이 E2 승인 기록 삭제 | (3) `cat-file -e "$H:$E2_APR"`에서 멈춤(set -e, rc 128) |

가드는 `$G` 밖에 쓰지 않았다(모래상자 r 상태 확인).

## 메인 저장소
읽기만 했다(clone 원본, `upload-pack` fetch 원본). 시작·끝 `git -C <repo> status --short` 36줄 동일, `reflog -n 3` 동일. `for-each-ref`는 달라졌는데 `refs/heads/role/{audit,code,test}/20260930-df23-registry-record`(572d767·b7b1e00)로, 다른 agent의 P10b 재시도 작업이다(내 명령은 메인에 ref를 만들지 않음). `_drafts`에 `post_p10b_state.txt`·`b47_render` 생기지 않음. `C:/g129` 삭제.
