# backfill 사전 실행 -- 실제 B34 병합본(M c851e54) 위 (2026-10-06)

작성: 리허설 agent. 실제 저장소·worktree·_drafts 기존 파일은 읽기만 했다(이 파일만 씀). 모래상자 `/c/g302`(TMP·TEMP 그 안, 끝나고 삭제). `/c/g297`(b26pre 사전 실행 agent)은 건드리지 않음.

## 0. 결론

**멈춤 1건(drift) -- 원본 키트 그대로면 `local`의 `pre`에서 멈춘다.** 실제 B34 코드 커밋 2eb7e55가 `sizing_recipe.py`를 바꿨다
(`resolve_stack_layout` docstring 6510~6512, 3줄 → 2줄, 순 −1줄, 동작 무관). 그래서
1. `backfill_launch.sh:257`(engine_since) `[중단] measured dd60db6 뒤 sizing_recipe.py 또는 selftest가 바뀌었다` -- 실측으로 재현(rc 1).
2. 고쳐도 `backfill_launch.sh:287` v3count의 줄 글 단정 `exp={11800:…,11879:…}`이 깨진다 -- 수정 후보 줄은 이제 **11799·11878**(c851e54에서 grep 확인).

이 두 줄만 모래상자 사본에서 바꾸고(아래 §2) 나머지는 그대로 돌리면 **값 차이 0**: conds 0·0·0·0·0, v3count 대상 4·not_targeted 93·4/4 killed PASS, card·final·push(EL4)·after-push OK. 변이 전 dry run은 seed 0·1 모두 2 failed(기대 그대로).

| 항목 | 기대 | 실측(실제 B34 c851e54 + 자리표시) | 판정 |
|---|---|---|---|
| `conds` | 0·0·0·0·0 | 0·0·0·0·0, approval 2건 gate에 있음, targets_by_def 3, rc 0 | 같음 |
| `local` (원본 키트) | pre OK | **pre 중단**(`backfill_launch.sh:257`, SR 차이) rc 1 | **drift** |
| `local` (사본: measured `c851e54` + 11799·11878) | OK | pre OK(`_approved_ids` 39, plan hash `16b899d1…`) → v3count → card → final, rc 0 | 같음 |
| v3count (card 35 실제 도구, gate 캐시 `mutate_changed.py`) | 대상 4 / not_targeted 93, 4/4 killed | `{"verdict":"PASS","mutants":4,"killed":4,"survivors":[],"not_targeted":93}`, targets_by_def 한 def(targeted 4, not_targeted 93, deleted_statements 2) | 같음 |
| card | parse ('3','red-green','no',[U-BF, phase3-cards],[],11), interface 4행 | 같음(interface 36줄) | 같음 |
| push(모래상자 EL4) / after-push | 통과 / OK | 통과(accept-log 한 줄) / OK | 같음 |
| 변이 전 dry run(새 test + 옛 코드) | 2 failed | seed 0·1 각각 **2 failed**, `assert e["interdig_ok"] is c3b[0].ok` → `assert False is True` | 같음 |
| (참고) green: 11799·11878 삭제 + backfill 2 + b26pre 19 | -- | seed 0·1 각각 21 passed | -- |

## 1. 모래상자

* `/c/g302/r` = 작업 트리 저장소 복제(`git -c core.autocrlf=false clone --no-hardlinks --no-local`, 복제본 `core.autocrlf false`), `role/audit/20260930-b34-grammar-explicit`는 복제본에만 fetch(`refs/remotes/src/b34audit` = c851e54).
* master 7243f28 → ff **c851e54**(실제 B34 M: test d504784 + code 2eb7e55) → `a4c0eab` 합성 `Role: audit`(gate 경로·pre-receive 경로 + B34 판정 기록 자리표시 V1~V10 PASS + `DRY_RUN`).
* bare 가짜 gate = 실제 `pre-receive`·`gate-runner.py`(EL4), 복제본 `core.hooksPath=.githooks`(EL3) + `.claude/hooks/role_*.py`·settings 복사(post_p10b_dryrun_setup.sh 방식).
* b26pre 병합 모의(EL3 켠 채): `bbdc0d6` `Role: test` 시제품 19 test → `A/tests/contracts/test_b26pre_existing_paths.py`
  (= `b26pre_v2_scripts/proto_v2_test_b26pre.py` 17, 계약 10은 v3 단언 'Mx1·Mx2 중 정확히 하나'로 + `b26_reconcile/proto_test_b26pre_trace.py` 2, `layer1_fallback` 원소 제외 -- post35 리허설과 같은 조립),
  `75ac79a` `Role: audit` b26pre 판정 기록 자리표시. gate에는 hook 없이 bare fetch + accept-log 한 줄(이전 리허설 방식).
  b26pre spec card 커밋은 모의하지 않았다(backfill 착수 조건에 없음 -- b26pre 키트 실행은 /c/g297 몫).

## 2. 모래상자 사본에서만 바꾼 것(원본 _drafts 미수정)

`/c/g302/kit/backfill_launch.sh`(+ `launch_common.sh` 그대로 복사):
* `:39` `DR=$W_REAL/_drafts` → 모래상자 사본 디렉터리(초안 사본을 읽게)
* `:287` `exp={11800:…,11879:…}` → `{11799:…,11878:…}`
초안 사본 `draft_b26_backfill_audit.spec.md:172` `**measured at `dd60db6`**` → `` `c851e54` `` (c851e54..gate에서 SR·selftest 차이 0이 되어 pre 통과).
※ 사본 card가 바뀌었으므로 `final`의 `cmp`·card blob은 사본 기준이다. 실제 착수 때는 card 초안 자체를 고쳐야 한다(아래 §3).

## 3. drift -- 고칠 곳(file:line, 이 agent는 수정하지 않음)

공통 사실: `dd60db6..c851e54`의 sizing_recipe.py 차이는 6510~6512 docstring 한 덩어리(−3 +2)뿐. 따라서 **SR 6513행 이후 인용 줄은 전부 −1**(옛 n행 글 = 새 n−1행 글, 아래 인용 58줄 모두 기계 대조 불일치 0). blob `97a6c7bb` → `2a7a1a0`. selftest·`run_matching_safety_with_finger_growth` 본문 내용은 같음. test 1480행 그대로.

### 3.1 멈춤을 만드는 것(필수)

| file:line | 지금 | 고칠 것 |
|---|---|---|
| `backfill_launch.sh:287` | `exp={11800:…,11879:…}` | `{11799:…,11878:…}` (줄 글은 같음) |
| `draft_b26_backfill_audit.spec.md:172` | `**measured at `dd60db6`**`, `a796468..dd60db6` SR blob `97a6c7bb` 같음 | B34 병합본 기준 measured rev로 새 재측정 문단(마지막 출현 규약 -- 덧붙이거나 교체), SR blob `2a7a1a0`, '인용 줄 −1' 명시. 그러지 않으면 `backfill_launch.sh:257`에서 멈춘다 |

### 3.2 문장이 틀려지는 것(card·briefs·스크립트 메시지)

| file:line | 지금 | 사실(c851e54) |
|---|---|---|
| `draft_b26_backfill_audit.spec.md:153` | 'B34는 stick_diagram의 4 def만 바꾸고 sizing_recipe는 바꾸지 않는다' | 실제 B34는 sizing_recipe `resolve_stack_layout` docstring도 바꿨다(−1줄, 동작 무관) |
| `draft_b26_backfill_audit.spec.md:15,19,22,26,27,39,59,65,70,71,96,99,105,115,123,140,154,155,183` | SR 11xxx·9369·9398 인용(예 11800·11879, 11758~11759, 11769~11770, 11784~11786, 11787~11794, 9369·9398) | 전부 −1(11799·11878, 11757~11758, … 9368·9397) |
| `draft_b26_backfill_audit.spec.md:176` | 'a796468..dd60db6 … 인용 줄(11712·…·11877~11884)·수정 후보 11800·11879' | 시점 기록이라 그대로 두고 새 재측정 문단에서 −1을 적는 쪽이 맞음 |
| `draft_b26_backfill_audit.spec.md:167` | B26-1 인계 '11809 … 11888'(v4 모의 head 줄) | 모의 head도 SR 기반이면 −1 -- B26-1 쪽에서 병합본으로 다시 잰다는 문장(166) 그대로면 선택 |
| `b26_backfill_briefs.md:11` | 'measured at `dd60db6`' 단일 출처 | card 앵커 갱신에 맞춰 |
| `b26_backfill_briefs.md:18` | `(가) 비어 있어야(B34는 stick_diagram만, …)` | 실제 B34 병합 뒤 (가)는 **비지 않는다**(docstring 1 hunk) -- '동작 무관 docstring만이면 −1 재인용 후 진행'으로 판정 문구 필요 |
| `b26_backfill_briefs.md:19` | `sed -n '11758,11759p;…;11877,11881p'` | −1 범위 |
| `b26_backfill_briefs.md:27,30,42,44,49,62,74,76,79~88,91,92,96,136,266~269,272,299` | SR 줄 인용 | 전부 −1(74의 head 11800·11878도 BP..H head 기준 −1 → 11799·11877) |
| `backfill_launch.sh:19,213,282,293,295` | 주석·메시지 '11800·11879', '11758~11881' | −1(동작 무관, 293은 출력 문구 '수정 후보: 11800·11879 삭제'가 실제와 어긋남) |
| `approval_20261001-b26-backfill-interdig-fix.md:13` | 11784~11786·11769~11770 | **이미 gate에 커밋된 기록(card oracle (d) 바이트 동일, `:257` 옆 cmp)** -- 고치지 말 것. card에서 '기록의 줄은 dd60db6 기준'이라고만 적으면 됨 |

### 3.3 기타(동작 영향 없음, 이전 보고와 같음)

* `backfill_launch.sh:276` scratch clone은 `-c core.autocrlf=false`를 clone에만 줘서 이후 checkout·commit에서 'LF will be replaced by CRLF' 경고가 난다. numstat `0 2`·대상 수 정상.

## 4. 격리 확인

* 실제 저장소: HEAD = gate/master = `7243f28`, status md5 `76eea762…`, reflog 354줄, role 브랜치 3개(c851e54·2eb7e55·d504784) -- 시작과 끝 같음. `_drafts/backfill_launch_state.txt` 생기지 않음.
* 상태 파일·TMP·TEMP·scratch 전부 `/c/g302` 아래. `/c/g302` 삭제.
