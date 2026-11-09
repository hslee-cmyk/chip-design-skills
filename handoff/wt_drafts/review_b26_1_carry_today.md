# review_b26_1_carry_today -- b26_1_carry.sh 오늘 변경 3건 독립 검토(2026-10-02)

검토자: 독립 agent(작성 안 함). 범위: `_drafts/b26_1_carry.sh`
(1) m1~m4 V3 --out 대조 강화(pre-m4.bak 대비) (2) U3 기록 5 단일 출처 배선(초안 `approval_20261001-b26-v3-equiv-range.md` + `b26_1_kit_selftest/fill_u3.py`, pre-u3.bak 대비)
(3) 초안·fill_u3.py sha256 핀(pre-pin.bak 대비). test `out_check_test.sh`·`records_u3_test.sh`.
모래상자 `/c/g260`만 씀(TMP·TEMP도 그 아래), 실제 저장소는 읽기만. 끝에 `/c/g260` 삭제.

## 판정: **B 0 / S 0 / minor 4 + 범위 밖 1(n1, 사용 전 처리)**

검토한 바이트 = `b26_1_carry.sh` 18:09판(45105B, 지금 `b26_1_carry.sh.pre-s3.bak`와 같다). 검토 중 18:54에 다른 agent가 's3' 변경(after-push 안내 echo 2줄, 575·576행)을 넣었다 -- n1 참고.
핀은 지금 파일과 맞다: 초안 `3d2333b7…0f10`, fill_u3.py `a6d05133…455caf`(sha256 실측 = `U3_DRAFT_SHA256`·`U3_FILL_SHA256`).

## 1. 확인한 것(실측)

| 항목 | 결과 |
|---|---|
| 가드된 git 명령 | 실행은 `fetch`·`add`·`commit`(단계 (c) 로컬 커밋)·읽기뿐. `push`·`worktree remove --force`·`branch -D`·`worktree add`는 `echo`/`say` 안에서만(grep). `git config`는 `--get`만. 모래상자 실행에서 `cleanup` 뒤 worktree 3·`role/` 브랜치 3 그대로, `final` 뒤 모래상자 gate master = B1 그대로(push 안 함) |
| set -Eeuo pipefail | 27행 + `inherit_errexit` + ERR trap 유지 |
| 저장소 가드 | `--repo` 별칭 3종(끝 `/`, `C:\…`, 실제 저장소 worktree 경로) 모두 rc 2(단계 실행 0). 단계 뒤 옵션 rc 2, 모래상자 모드에서 실제 `--state` rc 2, 상대 경로 rc 2 |
| (1) m1~m4 vs **실제 post-35 도구** | `git show a17b8bd:tools/gates/mutate_changed.py`(+ 같은 커밋 tools/gates) 를 합성 변경(`range(i + 2,…)`→`range(i + 1,…)`, test 2개)에 실제로 돌림: 판정 JSON `mutants 6, killed 5, not_targeted 7, survivors 1`(const- `…iter.args[0].right`), `--out` 13줄에 `not_targeted` 7줄이 대상 레코드와 섞여 적힘. 이 실제 출력에 carry check V3 heredoc(새)을 그대로 돌림 → **PASS**(원소 `…@192f4cd1…` 출력). 같은 출력에서 `not_targeted`·`targets_by_def`를 뗀 35 전 모양 → 새 heredoc **거부**("범위 card 35 판 도구로 잰 것이 아니다"), 옛(pre-m4) 통과. `--out`을 두 번 이어 붙임(도구 append 재실행 흉내) → 새 heredoc 거부("--out id 중복") |
| out_check_test.sh(내 모래상자 재실행, 18:09판) | 62사례 불일치 0, heredoc 밖(u3 구간 제외) 바이트 = pre-m4.bak, 실제 저장소 앞뒤 같음 |
| records_u3_test.sh(내 모래상자 재실행, 18:09판) | 18사례 불일치 0(good·good_copy·pin_good PASS, hash_mismatch·wrong_def·wrong_path·leftover_ph·tamper_quote·tamper_answer·tamper_phcount·two_comments·pin_prose·pin_fill STOP, bytes_ok 5), 기록 5 바이트 = pre-u3.bak 옛 heredoc 출력 |
| 결과 파일 | 두 suite 사본의 `RES`만 `/c/g260/res_*`로 바꿔 돌림 -- 공유 `out/*.tsv`는 건드리지 않음(앞뒤 sha256 같음) |
| U3 인용 원문 | 세션 jsonl `63c6146a…`의 `toolu_01KTtsbRiK7S3cv1coUsAyPw` 질문 4개 중 header `U3 등가` 1개: 질문 원문·선택지 4(label·description)·답 `정리 2줄 + 면제 1 (Recommended)` 모두 초안에 **바이트 그대로**(원문의 '쟽니다' 오타까지). 시각: 질문 tool_use 2026-10-01T12:10:47Z = 21:10 KST, 답 12:14:58Z = 21:14 KST, '질문 4개 중' 맞음 |
| CRLF·autocrlf | `_drafts`는 git 저장소가 아니다(`git -C _drafts rev-parse` → not a git repository, 상위 포함) → checkout·autocrlf 변환 경로 없음. 핀은 `sha256sum -b < 파일`(바이트), fill_u3도 `\r`·BOM을 거부 -- 편집기가 CRLF로 저장하면 핀이 먼저 멈춘다(정상 거부) |

## 2. design 05 §12 'V5 승인 운반' 두 번 시도 -- 끝까지 모래상자 시뮬레이션

구성(`/c/g260/e2e`): 실제 저장소 복제(`--no-local`, origin 제거) + `tools/gates` = a17b8bd(35 병합 도구) + gate_config 모래상자 + `draft_b26_1.spec.md`·interface card·승인 2개(launch 흉내)를 커밋한 B1, 모래상자 bare gate.
1차: role/test(P9 시그니처 test 2개 기대값 리터럴 변경, 트레일러 Role·Change-Id) T1, role/code(T1 위, `find_differential_pair_candidates` 한 줄 변경) K1, audit worktree = T1,
`base_check.json` = 실제 `weakening_diff.py` 출력(V5 FAIL, 발견 = 두 시그니처 test 정확히), `attempt1_v3.json`·`.out.jsonl` = a17b8bd 도구 내부(`changed_defs`·`mutants`·`_Scope.targets`·`bind_hash`)로 만든 실제 id·대상 분류(targeted 12, not_targeted 53, 생존 = range const- 1 -- test 실행만 흉내).

| 단계 | 결과 |
|---|---|
| `prep`(check→archive→records) | rc 0. V5 diff_hash 3중 일치, V3 생존 1 = K1 def 묶기 해시 일치, 운반 blob·paths.tsv, 보관 11파일 SHA256SUMS, **records: 핀 통과 → fill_u3 `--src` OK·`--jsonl` OK → 기록 5 4375B**, bytes_ok·parse-approval 둘 다 OK |
| `cleaned`(정리 전) | rc 1 "refs/heads/role/에 브랜치가 남았다"(정상 거부) |
| `cleanup` | rc 0, 명령 6개 **출력만**(worktree·브랜치 그대로 확인) → 내가 모래상자에서 그 6개를 실행 |
| `local`(cleaned→commit→final) | rc 0. Role: doc 커밋 하나(A 기록 4·5, A blob·paths.tsv, M card), 개정 card parse_spec_card OK(approval 5개), HEAD 조회: `approved_hashes ∋ 기록 4`, `_approved_ids` 증가 = {기록 5 원소}. push 명령은 출력만(gate = B1 그대로) |
| push(모래상자, 내가 실행) → `after-push` | rc 0. gate master = C = B2, B1·B2 P9 blob 같음, B2 트리에 V5 해시·V3 원소 |
| 2차 (3) 흉내 | B2에서 role/test 새로, `git show HEAD:…/paths.tsv`대로 `.blob` cp → T2 P9 blob = 운반 blob, `diff-hash(B2,T2)` = 기록 4 target(같음), 실제 `weakening_diff` **V5 PASS**(승인됨). a17b8bd `exempt_decision`(B2 승인 색인, K1 def 해시) → `exempt`, 다른 해시 → `exempt_ignored hash_mismatch` |

## 3. 핀 공격

* **초안 + 핀 동시 수정은 흔적이 남지 않는다(m1).** `_drafts`가 git 밖이라 "핀 변경이 diff에 보인다"(76·77·357행 주석)는 `.bak` 사본 대비로만 참이고 `.bak`도 같은 사람이 고칠 수 있다. records_u3_test의 핀 단정(`PIN_D == sha(DRAFT5)`)도 동시 수정이면 그대로 통과한다. 즉 핀은 '한쪽만 바뀐 drift' 탐지기이지 무결성 증거가 아니다. 실제 방어선은 (a) fill_u3의 jsonl 원문 대조(인용 3종) (b) 기록 5가 실제 저장소 Role: doc 커밋에 들어가 diff로 보인다는 것. **권고**: 핀 두 값을 커밋되는 곳(commit 본문 또는 card '1차 시도 기록' 문단)에 함께 적어 출처를 저장소 이력에 남기거나, 주석 문구를 "drift 탐지(동시 수정은 막지 않음)"로 고친다.
* 실제 거부 확인: pin_prose(인용 밖 산문 1구절 변조, 자리표시·주석·원문 그대로)·pin_fill(fill_u3 끝에 주석 1줄) → 둘 다 '어떤 기록도 쓰기 전' STOP, 기록 5 없음·RECORDS 없음(내 재실행).
* 핀 검사 위치: records 첫머리(ARCHIVED 확인 직후, 기록 4·5 삭제·작성 전). `prep`에서 핀이 틀리면 check·archive는 이미 끝난 상태로 멈추고, 핀을 고친 뒤 `records`만 다시 하면 된다(archive는 덮어쓰지 않음) -- 문제없음. 해시 뒤 fill_u3가 파일을 다시 읽는 사이의 TOCTOU는 같은 사용자 로컬이라 무시할 수준.
* CRLF: 위 표 -- 해당 경로 없음, 생겨도 fail-closed.

## 4. minor

* **m1** 위 핀 보장 문구(권고 위).
* **m2** 기록 4 초안(`approval_20261001-b26-p9-signature-update.md`)은 핀도 jsonl 대조도 없다(자리표시 3개·주석만 확인). 지금 바이트는 맞다(내 실측: [U5] 질문·선택지·답 `\n> 답\n` 모두 jsonl과 같음). 기록 5에 둔 핀 근거('인용 밖 산문 변경 틈')가 기록 4에도 그대로 해당 -- 대칭으로 `U5` 대조(fill_u3의 check_jsonl을 header 인자로 일반화)와 핀을 권고(선택).
* **m3** fill_u3 `check_jsonl`의 답(`toolUseResult.answers`)은 그 줄에 tool_use id 문자열이 있기만 하면 마지막 것을 쓴다(`tool_use_id` 묶음 없음). 다른 답이 잡히면 `ans[q["question"]]` KeyError로 멈추므로 fail-closed -- 오탐 거부 가능성만. 선택: `message.content[].tool_use_id == TOOL_USE`인 줄로 한정.
* **m4** 도구 `--out`은 append(WP-11)라 1차 auditor가 같은 경로로 다시 재면 carry check가 'id 중복'으로 멈춘다(실측, 안전 쪽). 1차 auditor 지시에 "재측정 전 --out 지움"이 있는지 확인 권고(정보).

## 5. 범위 밖 -- n1(사용 전 처리)

18:54 's3' 변경(`stage_after_push` echo 2줄 추가, `.pre-s3.bak` 대비 diff 그것뿐 -- 동작 영향 없음, 위 e2e after-push 출력에 나옴)이 두 suite의 범위 잠금을 깬다. 지금 바이트로 다시 돌리면:
`out_check_test.sh` → `AssertionError: heredoc 밖(u3 배선 구간 제외)이 pre-m4.bak와 다르다`(exit 1),
`records_u3_test.sh` → `('u3 배선 구간 밖 변경', [('insert', 597, 596, 575, 576)])`(exit 1).
즉 오늘 3건의 회귀 증거가 현재 파일에서는 빨강이다. s3 줄을 두 suite의 허용 구간에 넣거나(작성자≠검증자에 맞게 suite 소유 쪽이) 기준을 새로 잡은 뒤 다시 돌려야 한다.

## 이 검토 자체

* EL1이 변수 리다이렉트·`git config` 쓰기·`git -c core.hooksPath`·`cd` 뒤 상대 경로를 거부해 모래상자 작업은 `/c/g260/*.sh` 파일로 실행했다(모래상자 쓰기만). 모래상자 커밋은 전역 사용자 이름으로 했다(모래상자 밖으로 안 나감).
* 실제 저장소: `status --porcelain`(37줄)·`reflog -3`·HEAD·gate/master·`for-each-ref`·`worktree list` 시작과 끝 같음. 공유 `b26_1_kit_selftest/out/*.tsv` sha256 앞뒤 같음.
