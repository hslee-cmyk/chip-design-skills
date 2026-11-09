# B26-1 사전 점검 -- gate master `863a037` + 모의 backfill 병합 (2026-10-07)

작성: 사전 점검 agent. 실제 저장소는 읽기만 했다(`git -C`, fetch는 복제본 안으로만). `_drafts`에는 이 파일만 썼다 --
launch·carry·spec·승인 초안 2개·launch_common·user_decisions·b40 초안 sha256 앞뒤 같음. `_drafts/b26_1_launch_state*` 생기지 않음.
모래상자 `/c/g390`(TMP·TEMP·TMPDIR 그 안, cd 없음, 끝나고 삭제).

## 0. 결론

| 질문 | 답 |
|---|---|
| (1) launch 단계 | 모의 post-backfill head에서 `conds` = `1~9:0 10:128 11:0`, exit 3(10 = b40 기록, local1이 채움 -- 기대). `pre`·`local1`·(모래상자 push #1)·`after-push-appr`(1~11 전부 0)·`local2`(interface 46행 = IFC_ROWS)·(push #2)·`after-push` **전부 rc 0. 실패하는 확인 없음** |
| 대조(backfill 전 `863a037`) | `conds` = `8:128 10:128` -- 조건 8은 backfill 판정 기록이 없어서 실패(지금 실제 gate 그대로 돌리면 이 표가 나온다, 정상) |
| (2) 줄 인용 이동 | 초안의 5자리 SR 인용은 381·383행 둘뿐이다. 둘 다 **모의 v4 head 줄**(측정 기록)이라 필수 수정은 없다. 착수 base 기준을 병기하려면 아래 §2의 정확한 교체안. SD 인용·SR 11799 앞 인용(16행 SR 2207·4293, 71행 6880~8090, 77행 3950 등)은 이동 없음 |
| (3) engine_since ALLOW | 맞다. ALLOW_SR에 backfill id 있음(실측 `754db1f SR Change-Id 20261001-b26-backfill-interdig-final-audit` 통과). b26pre는 SD·SR·P9T를 건드리지 않아 어느 목록에도 필요 없다(7535799..head 변경 커밋 = `2eb7e55` SD·SR, `a410f31` SD, `6bf510b` P9T, 모의 backfill code SR -- 5개). 수정 불필요 |
| (4) 승인 초안 해시 | 두 초안 모두 해시 자리가 자리표시(`<V3_BIND_HASH_64>`, `<TARGET_DIFF_HASH_64>`/`<DIFF_BASE_40>`/`<DIFF_HEAD_40>`)이고 1차 시도에서 채운다. 의존 대상(SD `find_differential_pair_candidates` def, P9T blob)은 backfill이 바꾸지 않는다(SD `9993047c`→`9993047c`, P9T `003c0d1d`→`003c0d1d`; SR만 `2a7a1a04`→`fe33a63e`). 줄 번호 의존 없음. carry 바이트 핀 5개(U3 초안·fill_u3·P9 초안·quote_bind·t0_quote_check) 현재 파일과 전부 일치. 수정 불필요 |

## 1. 모래상자 구성(가정 포함)

* `r` = 실제 저장소 `git -c core.autocrlf=false clone --no-local --no-hardlinks`(master `863a037`). 실제 `role/test/20261001-b26-backfill-interdig-final-audit`(`3004096`, 실제 test 커밋 -- `test_b26_backfill_interdig.py` 206줄)을 복제본에 fetch.
* 모의 스택(실제 병합 모양을 B34 `c851e54` 선례대로 흉내):
  1. master ff → `3004096`(실제 backfill test 커밋, Role test, Change-Id backfill)
  2. 분기 `754db1f` code: **가정** -- SR 11799·11878 `_backfill_interdig_ok(result)` 두 줄만 삭제(글 확인 후, numstat `0 2`). Role code, Change-Id backfill
  3. `7ef870b` merge --no-ff(Role doc, Change-Id backfill) -- 두 번째 부모와 SR TREESAME이라 `rev-list -- SR`에서 빠짐
  4. `db0cfb4` audit: **가정** -- `.ai/verification/20261001-b26-backfill-interdig-final-audit.json` 자리표시(b26pre 기록을 id만 바꿔 복사, V1~V10 PASS/N/A)
  5. `5a83407` **모래상자 전용** -- `tools/gates/gate_config.json` gate_path·workspace_path를 `C:/g390`으로(cache_dir가 모래상자 gate를 보게). SD·SR·P9T 무관
* bare `C:/g390/gate.git`, remote origin 제거(실제 저장소로 push 경로 없음). EL3/EL4 hook 미설치(launch 확인만 봄).
* 모의 head에서 실제 backfill test 실행: `test_b26_backfill_interdig.py` **5 passed**(`--gmid-phase=3`) -- 두 줄 삭제 가정이 그 test 기준으로 green.
* 실제 code 브랜치는 점검 시점에 아직 `3004096`(code 커밋 없음). code-author가 두 줄 외에 SR 주석·docstring을 더 고치면 §2의 수치를 다시 잰다(재측정 방법은 §2 끝).

## 2. 줄 인용 -- 초안 `draft_b26_1.spec.md`

backfill 뒤 SR: 11799 이후 −1, 11878 이후 −2(모의 head 실측 글 대조):

| 863a037(= 2183f2e) | 모의 post-backfill | 글 |
|---|---|---|
| 11799 | (없음) | `_backfill_interdig_ok(result)` 루프 안 |
| 11800 | 11799 | `if result.ok:` |
| 11801~11804 | 11800~11803 | `_finalize` · `return {…}` |
| 11876~11877 | 11875~11876 | 루프 뒤 `repair_matching_safety(` |
| 11878 | (없음) | `_backfill_interdig_ok(result)` 루프 뒤 |
| 11879~11883 | 11877~11881 | `_finalize` · `return {…}` |

초안 전수(`1[12]\d{3}` 검색)에서 SR 11799 뒤를 가리키는 인용은 두 행뿐:

* **381행** `run_matching_safety_with_finger_growth` 11810·11886·11889·11890 삭제 4 -- 모의 v4 head 줄(base 2183f2e 11800·11876·11879·11880 = `if result.ok:`·루프 뒤 repair 호출·`_finalize`·`return`, +10). 같은 모의 head에 backfill을 적용하면 11809·11885·11887·11888, 착수 base(post-backfill)에서는 11799·11875·11877·11878.
* **383행** 11809·11888 `_backfill_interdig_ok(result)` -- 모의 v4 head 줄(base 11799·11878). backfill 뒤 문장이 없다(383행 문장 자체가 그렇게 말한다).
* 주의: 모의 head 번호를 −1/−2로 '고치면' 381행 새 번호 11809·11888이 383행 옛 번호와 겹쳐 다른 문장을 가리킨다. 그래서 **번호를 바꿔 쓰지 말고 병기**를 권한다(b26_1_cite_check.md의 병기 원칙과 같음).

제안 교체(선택 -- 적용 여부는 오케스트레이터):

381행 옛 글:
```
`run_matching_safety_with_finger_growth` 11810·11886·11889·11890 삭제 4;
```
새 글:
```
`run_matching_safety_with_finger_growth` 11810·11886·11889·11890 삭제 4(모의 v4 head 줄 -- backfill 병합 착수 base에서는 11799·11875·11877·11878: `if result.ok:`·루프 뒤 `repair_matching_safety(`·`_finalize`·`return`);
```
383행 옛 글:
```
`run_matching_safety_with_finger_growth` 11809·11888 `_backfill_interdig_ok(result)` 삭제
```
새 글:
```
`run_matching_safety_with_finger_growth` 11809·11888(모의 v4 head 줄, gate `2183f2e` 11799·11878 -- backfill 병합 뒤 base에는 없다) `_backfill_interdig_ok(result)` 삭제
```

이동 없음 확인: 16행(SD 13줄, SR 2207·4293 -- "backfill은 SR 6513행 이후만 바꿔 이 줄들은 착수 base에서도 같다" 문장 맞음), 38~54행 표(SD), 65~77행(SR 3728~8091·SD), 381행의 다른 수(9411·9413·11704·11706·11708 SR은 11799 앞, 6875·6877·6578·3272·4512는 SD/SR 11799 앞), 194행("backfill test 파일은 `run_matching_safety_with_finger_growth`만 부른다" -- 실제 `3004096` 파일: `size_transistor`·`Transistor`·`SizingContext`·`run_matching_safety_with_finger_growth`만, `supply_nets` 선언 있음. 맞음).
measured rev 앵커(35행 `7535799`, 1개)는 그대로 유효(engine_since 통과).

실제 code 커밋이 나오면 다시 잴 것: `git -C <복제본> show <병합본>:skills/analog-gmid-design/assets/sizing_recipe.py | grep -n "_backfill_interdig_ok\|_finalize(current_rows"`로 위 표의 오른쪽 열을 확인하고, `git diff --numstat 863a037 <병합본> -- <SR>`가 `0 2`가 아니면 381행 병기 수치를 글로 다시 찾는다.

## 3. launch 실행 기록(모래상자)

| 단계 | 결과 |
|---|---|
| `conds` @모의 head `5a83407` | `1:0 2:0 3:0 4:0 5:0 6:0 7:0 8:0 9:0 10:128 11:0`, D2 card=0·규약 전체=0, 미충족 10, approval 줄 b40만 gate에 없음 → exit 3(기대) |
| `conds` @`863a037`(대조) | `8:128 10:128` → exit 3(backfill 판정 기록 없음) |
| `pre` | rc 0. engine_since: SD·SR·P9T 변경 5개 전부 ALLOW, 새 test 파일 없음, P9 시그니처 test 2개 있음. `_approved_ids` 39, plan_tables_hash `16b899d1…`(실제 backfill 상태 파일과 같음), APPR_SKIP 0 |
| `local1`(pre→appr→final-appr) | rc 0. b40 기록 2614 B, decision `U4-B40-UNAVAILABLE-REASON-KEY` |
| push #1(모래상자 gate) → `after-push-appr` | rc 0, 착수 조건 1~11 전부 0 |
| `local2`(card→final) | rc 0. approval 3건 parse-approval OK, parse_spec_card `('3','red-green','no',[3건],[],12)`, interface 행 46 = IFC_ROWS(신규 2), 371줄 |
| push #2 → `after-push` | rc 0, B1 = S |

## 4. 실제 실행 시 주의(점검 중 관찰)

* 지금 실제 저장소에 `role/{test,code,audit}/20261001-b26-backfill-interdig-final-audit` 브랜치가 있다 -- backfill 병합·정리 전에는 `pre`가 `test -z "$(g for-each-ref refs/heads/role/)"`에서 멈춘다(정상 순서).
* 조건 8은 backfill 판정 기록(V1~V10, PASS/N/A만, id 일치)이 gate에 들어가야 0이 된다.
* 승인 초안 4·5를 고칠 일이 생기면 carry 핀(`U3_DRAFT_SHA256`·`P9_DRAFT_SHA256`)도 같이 고친다 -- 이번 backfill로는 고칠 필요 없음.
