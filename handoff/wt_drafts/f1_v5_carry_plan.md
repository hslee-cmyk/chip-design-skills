# F1 `20261002-p3-callers-update` -- V5 승인 운반(두 번 시도) 계획 (phase3_runbook §18 X-1, 2026-10-06)

작성 2026-10-06. 읽기만 해서 쓴 판단 문서다 -- `draft_p3_f1.spec.md`는 고치지 않았다(다른 agent가 F card를 고치는 중일 수 있다). 아래 '초안에 반영할 것'은 F1 초안 담당이 옮긴다.
근거: design 05 §12 'V5 승인 운반'·§9.2-4·§9.2-9(gate `master` `6c724de` -- 실측 `git show gate/master:docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md`),
`tools/gates/merge_gate.py` 9번(`load_approvals(new_view)`), `tools/gates/weakening_diff.py` `main`·`approved_hashes`, T0 결정(`draft_p3_t0.spec.md` '결정 필요 항목' (X-1) 문단, `t0_carry.sh`, `t0_briefs.md` §4).

## 1. 결론

F1도 **두 번 시도로 운반한다**(T0와 같은 이유, B26-1 선례와 같은 모양). 1차 시도 범위는 **순서 0~3**(design 05 §12 (1) 그대로), 2차 시도는 순서 1~8 전체(equivalence -- 병합 있음).

## 2. 왜 한 번 시도로는 안 되는가(T0와 같은 분석, equivalence 모양으로)

1. **target은 T 전에 정할 수 없다**: V5 승인 기록 `target` = `weakening_diff.py`의 `diff_hash` = 발견 경로마다 `경로\tbase blob\thead blob\n`을 이은 sha256(00-common §8.2). head blob은 test-author가 쓴 F1 test 커밋의 내용이다.
   오케스트레이터가 test blob을 미리 쓰는 길은 작성자≠검증자(N3.12.1) 위반이라 없다. F1 계약 8 ⑤ 목록도 "auditor가 **실제 F1 base**에서 계산한 것을 보인다"(⑤ 제시 방법 (1)) -- T 뒤에만 있다.
2. **gate는 승인을 new 트리에서 찾는다**: `merge_gate.py receive` 9 = `load_approvals(new_view)`(new = audit 커밋), auditor V5 = `approved_hashes(root, head)`. 승인 기록은 그 push의 커밋 어딘가에 있거나 `old`에 있어야 한다.
3. **push 모양에 자리가 없다**: equivalence 모양(§9.2-4) = ① `old..M^1` 전부 `Role: test` ② `M^1..M^2` 전부 `Role: code` ③ M `Role: doc` 병합(트리 = M^2) ④ `new` = `Role: audit` 1개, "커밋 집합이 정확히 같아야(다른 커밋이 끼면 거부)".
   `.ai/approvals/**`는 오케스트레이터(Role: doc) 쓰기 경로다(계획 N3.12.2 630행) -- test·code·audit 커밋에 넣을 수 없고, M은 트리 = M^2라 새 파일을 담을 수 없다.
4. **old로 먼저 넣을 수도 없다**: 역할 브랜치가 있는 동안 메인 `git push gate master:master`는 EL1 `_judge_push`가 거부하고(§12 머리 '한 번에 변경 하나'), 넣는다 해도 그 문서 커밋이 1차 `old` 뒤에 생겨 1차 사슬이 새 `old`에서 시작하지 않는다(부분 `rebase`·`reset` 금지 -- §12 '재시도').
→ 남는 정당한 경로는 §12 'V5 승인 운반'뿐이다: 1차에서 T를 정하고 → 정리 → 승인 기록 + 운반 blob을 문서 커밋으로 gate에 → 2차에서 같은 blob을 만든다(해시 식이 blob 기반이라 2차 해시 = 1차 해시).

## 3. 1차 시도 범위 -- 순서 0~3만(code 없음)

* design 05 §12 (1)이 "1차 시도 순서 1~3"이다. B26-1이 순서 5(K1)까지 간 것은 V3 면제 기록(U3 -- 변이 id@K1 def 묶기 해시)이 **K에 의존**해 1차에서 재야 했기 때문이다(b26_1_carry.sh 머리).
* F1은 K에 의존하는 기록이 없다: 계약 8 V3 = 대상 def 0·변이 0(`defs` []·`not_targeted` 0, 모의 `7243f28` 판 실측 '바뀐 def 0'), V4 면제 질문 없음. 그래서 code-author를 1차에 부르지 않는다(2차에 한 번만 -- 같은 일을 두 번 하지 않는다).
* 남는 위험: 2차 code-author가 dispute를 내면 재시도(§12) -- test를 바꾸는 dispute 해소면 해시가 바뀌어 V5 질문을 다시 한다. 이 위험은 모든 card에 같고 1차에 code를 돌려도 '1차 K로 확인'일 뿐 2차 dispute를 막지 못하므로
  범위를 넓히는 근거가 아니다. 착수 0단계가 K 의존 기록을 예측하면(V3 생존·V4 UNJUDGED 면제 등) 그때 B26-1 모양(순서 5까지, K1 보관·show→Edit)으로 바꾸고 이 문서를 고친다.

## 4. 절차(T0 `t0_carry.sh`와 같은 단계, F1 차이만 표시)

| 단계 | 내용 | F1 차이 |
|---|---|---|
| 순서 0 | 착수 0단계 (1)~(3) 실측 → spec + interface Role: doc → push | spec 머리 `approval:` 줄에 V5 id를 **미리** 둔다(아래 5-1) -- 그 기록은 이때 gate에 없어야 한다 |
| 1차 1~3 | test worktree → test-author(T_a -- card T1과 헷갈리지 않게 'T_a'로 부른다) → audit worktree → auditor 3.1: base_check.json 키 `V5`에 `weakening_diff` 출력 그대로 + **⑤ 목록**(단위·사유·실제 diff 줄 전후 원문 -- ⑤ 제시 방법 (2)) + 계약 3 (바) S1 측정 | 순서 4·5 없음, V5 FAIL로 멈춤 |
| prep | check(B1 = F1 launch 상태의 순서 0 커밋, T_a, V5 재실행 = base_check = `diff-hash`) → archive(발견 경로 blob → `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/v5-carry/20261002-p3-callers-update/<blob id>.blob` + `paths.tsv`, 보관 `_drafts/f1_attempt1/`) | 질문 재료에 ⑤ 목록·TS6 핀 원문(`pin_commit` 40자·`pin_edits = ()`·정수 `0`)을 base_check에서 그대로 옮긴다 |
| 질문 | AskUserQuestion: 재료의 발견 목록(gate 발견 단위 = `findings` 길이)·`diff_paths`·`diff_hash` + ⑤ 목록 + 핀 원문 | runbook §3 'F1 V5(⑤ 제시 방법)'·review_p3_f12_r4 m1~m2 |
| records | 승인 기록 = 답을 채운 초안 + 해시·B1·T_a·diff_path·발견 목록, 인용 줄 jsonl 대조, parse-approval | 범위 설명에 ⑤ 목록(단위·실제 diff 줄 원문)·계산한 F1 base·계약 3 (바) S1 적용 문언(⑤ (5))·TS6 핀 원문(④) |
| cleanup·local·push·after-push | 정리 = test·audit 둘(1차에 code worktree 없음) → Role: doc 운반 커밋 하나 → push 단독 → B2 확인 | 같음 |
| 2차 1~5 | test worktree(B2) → test-author: `paths.tsv`대로 `.blob` cp + 나머지는 1차 patch → **t2-check**(바뀐 경로·blob 전부 = 1차, head V5 approved) → audit 3.1 → code worktree → code-author(K) | equivalence: 순서 4·5가 2차에만 있다 |
| 2차 6~8 | 빈 브랜치 가드 → 순서 6 병합(`Role: doc`, 트리 = K) → 순서 7 auditor(V5 basis: target = 기록, B1·B2 사이 skills/·workspaces/·tools/ 같음, ⑤ (바) (i) 대조) → 순서 8 push | **병합 있음**(T0와 다름). V5는 base B2 → 병합본으로 잰다 -- code 커밋은 test 경로를 바꾸지 않으므로(계약 7) 발견 경로 head blob = T_b = T_a blob |
| purge | 병합·정리 뒤 운반 디렉터리 삭제 Role: doc | 같음 |

TS6 (마) test(계약 1 (d))는 `git merge-base --is-ancestor <pin_commit> HEAD`를 부른다 -- `9d6800e`는 B1의 조상이고 B2는 B1의 후손이라 2차에서도 같다. PT3는 전체 이력 clone에서(review_p3_f2_cur A3 -- 얕은 복제 금지).

## 5. 초안에 반영할 것(F1 초안 담당 -- 이 문서는 고치지 않았다)

1. **spec 머리 `approval:` 셋째 줄** `approval: 20261002-p3-callers-update`(V5 diff 승인, id = card id -- T0 `20260930-p3-tests-location-free`·B33 `20260930-v7-registry-edges` 선례). 순서 0 때 gate에 **없어야** 하고(launch `pre`가 확인),
   운반 커밋이 기록을 더한다 -- 그래서 운반 커밋이 spec card를 고칠 필요가 없다(B26-1은 머리에 없어서 운반 커밋에서 card 개정을 했다 -- interface card 재생성 대조가 따로 필요했다).
   판정 기록 `approvals` = 셋(`20260930-30-module-split-design`·`20261002-p3-f1-workspaces-write-path`·이 id).
2. '결정 필요 항목' 1 '승인 경로' 줄에 "두 번 시도 운반(design 05 §12 'V5 승인 운반') -- 1차 = 순서 0~3, 2차 = 1~8, 1차 test 끝 T_a의 blob을 운반" 한 문장(T0 card (X-1) 문단과 같은 구조, 엔진 함수 이름은 백틱 없이 -- interface card 생성기).
3. auditor 브리프 3.1에 '1차 시도: base_check.json 키 `V5` = weakening_diff 출력 그대로, ⑤ 목록·S1 측정, 여기서 멈춤', 3.2에 '2차에서만, V1 `-c` 캐시 old = B2'.
4. test-author 브리프에 '2차 시도' 문단(T0 `t0_briefs.md` 1절 끝 문단과 같은 내용 -- 운반 blob cp, 나머지는 `_drafts/f1_attempt1/T_a.patch`).
5. **launch·운반 스크립트**: F1은 launch 스크립트가 아직 없다(runbook §14). F1 launch를 쓸 때 `t0_carry.sh`를 **card 매개변수화**(ID·바뀌는 경로 집합·launch 상태 파일·승인 초안·보관 디렉터리·after-push가 출력하는 2차 명령의 병합 유무)해 같은 파일로 쓰는 것을 기본안으로 한다
   -- 단계·판정은 T0와 같다(1차에 code worktree 없음 = check가 test·audit 둘만 받는 지금 모양 그대로). 지금 만들지 않는 이유: F1 launch가 없어 배선할 곳이 없다(만들면 배선). 바뀌는 경로 집합은 F1 착수 0단계 실측(계약 7 '범위 밖 변경 0'의 test 쪽 목록)에서 정한다.
6. runbook §14 '절차' 줄의 "→ V5 승인 → 순서 6~8"을 위 표 순서로(이 문서 링크) -- phase3_runbook §14 '승인' 줄은 이 문서를 가리키도록 이미 고쳤다(2026-10-06).

## 6. T1(test-only, [GAP])

초안이 없다. T1 V5도 같은 이유로 두 번 시도이고, T0와 모양이 같다(test-only, 병합 없음) -- T1 초안 때 `t0_carry.sh` 매개변수화(5-5)와 같은 판단으로 쓴다.
