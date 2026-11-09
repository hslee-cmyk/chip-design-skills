# B26-1 carry 준비 점검 (2026-10-07, gate master 6df4bd7 = 1차 base B1)

범위: `_drafts/b26_1_carry.sh` 운반(두 번 시도 절차 2)이 1차 역할 산출물을 받을 준비가 됐는지. 저장소는 읽기만, 모래상자 `/c/g422`만(끝에 삭제).
실제 저장소 status·HEAD·gate/master·reflog 앞뒤 같음(cmp). 실제 test worktree `wt/20260930-b26-rail-accessor-set-test`는 건드리지 않음.

## 결론

**차단 요인 없음.** 자기 시험 4개 모두 PASS, 핀 5개 일치, 모래상자 복제본에서 1차 산출물을 흉내 내 carry 전 단계
(prep -> cleanup -> 정리 실행 -> local -> push(모래상자 gate) -> after-push)가 끝까지 통과.
남은 위험 1건(아래 주의 1)은 1차 auditor가 브리프 2.1 형식을 지키는지에 달림.

## 1. 자기 시험

| 시험 | 실행 | 결과 |
|---|---|---|
| b26_1_quote_bind_test.py | `python -B b26_1_quote_bind_test.py /c/g422/qb` | exit 0, 사례 27 불일치 0 |
| t0_quote_check_test.py | `… /c/g422/t0 <projects jsonl 폴더> /c/g422/t0_result.tsv` | exit 0, 사례 30/30, 실제 답 전수 87/87 수용 |
| out_check_test.sh | `env OUT_CHECK_SCR=/c/g422/oc bash …` | exit 0, 사례 62 불일치 0, heredoc 밖 556줄 바이트 같음 |
| records_u3_test.sh | `env RECORDS_U3_SCR=/c/g422/rt bash …` | exit 0, 사례 24 불일치 0(기록 5 13, 기록 4 qbind 6, bytes_ok 5) |

결과 tsv는 각 시험이 설계대로 `b26_1_kit_selftest/out/`에 덧붙였다(qbind·out_check·records_u3). t0는 /c/g422에 썼다.

## 2. 핀(b26_1_carry.sh 상수 = 현재 파일 sha256)

| 상수 | 파일 | 일치 |
|---|---|---|
| U3_DRAFT_SHA256 3d2333b7… | approval_20261001-b26-v3-equiv-range.md | 일치 |
| U3_FILL_SHA256 fb8a1948… | b26_1_kit_selftest/fill_u3.py | 일치 |
| P9_DRAFT_SHA256 22da78b7… | approval_20261001-b26-p9-signature-update.md | 일치 |
| QBIND_SHA256 050a27cd… | b26_1_quote_bind.py | 일치 |
| QCHK_SHA256 03d07619… | t0_quote_check.py (t0_carry.sh T0_QCHK_SHA256과도 같음) | 일치 |

## 3. carry가 기대하는 경로·상태

| 항목 | 지금 | 판정 |
|---|---|---|
| launch 상태 `B1=` | 6df4bd7fd992… = HEAD = gate/master | OK |
| 상태 파일 `_drafts/b26_1_carry_state.txt` | 없음 | OK(check가 새로 씀) |
| 보관 `_drafts/b26_1_attempt1/` | 없음 | OK(archive는 있으면 멈춤) |
| B1 트리: 운반 디렉터리 `v5-carry/<id>`, 기록 4·5, dispute 파일 | 모두 없음 | OK |
| B1 트리: SD, P9T, spec·interface card, approval 3개 | 모두 있음 | OK |
| card: 머리 approval 3줄, `## ` 절 12개(NSEC), 닻 `**운반 경로(고정` 1회, `**1차 시도 기록(` 0회 | 맞음(모래상자 commit 단계 parse_spec_card·interface card 재생성 바이트 대조 통과) | OK |
| 메인 `status -- docs/ .ai/` | 빈 출력 | OK |
| `refs/heads/role/` | role/test/<id>만(code·audit는 1차 역할이 만듦) | OK -- carry check 시점에 정확히 세 개여야 함 |
| 다른 worktree(.claude/worktrees/agent-*, bootstrap-replay) | role 브랜치 아님 | 영향 없음 |
| user.email, JSONL5(63c6146a… 세션 jsonl) | 있음 | OK |
| 1차 auditor 산출물 `<audit wt>/.ai/verification/<id>/{base_check.json, attempt1_v3.json, attempt1_v3.out.jsonl}` | 아직 없음 -- 1차 auditor가 만듦(b26_1_briefs.md 2.1·2.2, launch.sh 475행 안내와 경로 같음) | 대기 |

## 4. 모래상자 모의(1차 산출물 흉내)

- 복제본 `/c/g422/s/r`(gate_config gate_path -> 모래상자 bare gate, B1 = 그 커밋), worktree 부모 `/c/g422/s/wt`.
- T1(Role: test): P9 두 시그니처 test의 `==`를 다른 비교로 바꿈 -> 게이트 캐시 weakening_diff가 FAIL, 발견 = 두 단위, diff_paths = [P9T].
  (참고: 목록에 원소만 더하는 변경은 V5 PASS였다 -- 실제 1차 T1이 card 기대대로 '비교 완화'를 내는지는 1차 auditor 측정이 정한다. 아니면 card 단계 1대로 멈춤.)
- K1(Role: code): find_differential_pair_candidates에 문장 하나(def 해시 변경, 경로 body[9]…로 이동).
- audit 산출물: base_check.json = 브리프 2.1 형식(`"V5"` 키에 weakening_diff 출력 JSON 객체), attempt1_v3.json·out.jsonl = 합성(K1 def 묶기 해시·경로를 K1 원본에서 계산, mutate_changed 실행은 안 함).
- carry `--repo/--state/--launch-state/--archive/--wt` 모래상자 옵션으로 실행:
  - prep: check(V5 3중 대조, V3 묶기 해시 재계산·경로 노드) · archive(blob·paths.tsv, 보관 11파일 SHA256SUMS) · records(qbind 기록 4 인용 OK, fill_u3 src·jsonl OK, bytes_ok, parse-approval) 모두 OK
  - cleanup: 명령 6개 출력 -> 모의에서 실행 -> local(cleaned·commit·final) OK. commit은 전역 core.hooksPath(실제 `.githooks` pre-commit·commit-msg)를 거쳐 통과
  - push(모래상자 gate, 전역 pre-push 통과) -> after-push OK(B2 트리에서 V5 승인 해시·V3 원소 조회)
- 모래상자 gate에는 실제 gate의 EL4 pre-receive가 없다 -- 실제 push 판정은 모의하지 못함(정보).

## 5. 주의(차단 아님)

1. **base_check.json 형식 의존**: carry check는 파일 전체에서 `diff_hash` 키를 훑어 정확히 하나를 요구한다. P9 선례 `attempt1_base_check.json`은
   V5 출력을 `v5_base_to_T.output` **문자열**로 넣었다 -- 그 모양이면 diff_hash 0개로 check가 멈춘다. 브리프 2.1(180~182행)이 "출력 JSON을 그대로 `"V5"` 키에,
   다른 곳에 diff_hash·diff_paths 금지"를 요구하므로, 1차 auditor 보고를 받을 때 V5가 **객체**로 들어갔는지 먼저 확인할 것(문자열이면 check 전에 auditor에게 다시 쓰게 한다).
2. check는 test·code worktree `status --porcelain`이 **미추적 포함** 빈 출력이어야 한다. `.gitignore`는 `__pycache__/`·`*.pyc`만 있다(.pytest_cache는 자체 .gitignore로 숨음).
   역할 agent가 worktree에 다른 임시 파일을 남기면 check가 멈춘다.
3. V3 재측정 시 `attempt1_v3.out.jsonl`을 먼저 지울 것(도구 append -> 'id 중복'으로 멈춤) -- 브리프 203행·launch 안내와 같음.
4. dispute가 생기면 card에 `## dispute 기록` 절을 더해야 carry가 진행되는데, 그러면 절 수가 13이 되어 commit 단계 NSEC=12 단정이 깨진다 -- dispute 경로로 갈 때만 NSEC를 같이 고칠 것.
