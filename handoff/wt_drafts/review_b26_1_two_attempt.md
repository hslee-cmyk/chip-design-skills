# 독립 검토 -- B26-1 '두 번 시도 절차'·'승인 줄 배치', p9-signature 승인 문안 r1, 세 card 착수 조건 (2026-10-01)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기만 했다. scratch는 C:/g155만 썼고 끝에 지웠다. 저장소 `git status --short`는 시작 때와 같다(36줄, cmp 동일).
기준: gate `master` = `19eb475`(검토 중에 오케스트레이터가 `5f643a9`(topology-md-sync)로 ff했다 -- `tools/gates`·design 05·계획서 diff 0이라 판정에 영향 없음).
`0f23786`..`19eb475` 사이 `merge_gate.py`·`weakening_diff.py`·`mutate_changed.py`·`reachability.py`·`role_hooks.py` diff 0.
범위(루프 종료 조건): 이번 회차의 새 절차와 바뀐 파일만. 그 밖에서 본 것은 끝의 '범위 밖' 한 줄씩.

## 판정

**조건부 수용 -- B 1건(순서 한 줄만 고치면 됨), S 1건, minor 4건.** 절차의 핵심 주장(한 시도 안에서는 기록을 넣을 수 없고, 두 번 시도로 운반하면 EL4가 받는다)은 모의로 확인했다.

## 확인한 것(증거)

1. **design 05 §12 'V5 승인 운반' 인용은 바이트 단위로 같다.** gate `19eb475`(그리고 `0f23786`) design 05 399행 표의 셋째 칸과 draft 445행 따옴표 안을 비교했다: 길이 717 = 717, `==` 참.
2. **receive 병합 모양 인용 맞음.** `19eb475` `merge_gate.py` 1135행(`new`가 `Role: audit` 커밋이 아니면 거부) ~ 1168행(`T, K = M1, M2`). 커밋 집합 검사는 1165행
   `set(commits) != set(chain) | set(code) | {M, new}`, M 트리 = M^2 트리 검사는 1147~1148행, test 사슬 역할 검사는 1149~1156행이다. 쓰기 경로표(계획 N3.12.2, 597~656행)에서 `.ai/approvals/**`는 오케스트레이터(`Role: doc`)만 쓴다.
   **음성 대조(B1 상태의 fake gate 사본에 실제로 push):**
   * N1 audit 커밋에 승인 기록 추가 → `[EL4 거부] 경로 권한 거부: 주체 gmid-verification-auditor, .ai/approvals/…md -- 맞는 행 없음`
   * N2 test 사슬과 병합 사이에 `Role: doc` 기록 커밋 끼우기 → `test 사슬 커밋이 Role: test…가 아니다` 등 3건 거부
   * N3 병합 커밋 M 안에 기록 추가 → `M 트리가 M^2(code 끝) 트리와 다르다`
   → 시도 안의 어느 자리에도 기록을 넣을 수 없다는 주장이 맞다. 그리고 1차 head(T1)에서 `approved_hashes(T1)`·`mutate_changed._approved(T1)` 모두 거짓이었다(기록은 base 쪽에 있어야 한다).
3. **5단계 모의(C:/g155, `19eb475` 복제본 + bare fake gate. pre-receive = `gate-runner.py`와 같은 방식(old 판 `tools/gates`를 풀어 `merge_gate.py receive`)이고 무결성 대조만 뺐다 -- scratch에 설치 사본이 없다).**
   card는 P9 card 사본(id `20261001-g155-toy`, equivalence -- 병합 모양은 red-green과 같은 분기), 판정 기록은 P9 기록 사본에 id·커밋·approvals·V5 basis·V1 명령의 old만 바꿨다. `core.autocrlf=true`(전역 설정 그대로).
   * B1(card 커밋) push → 받음.
   * 1차: T1 = 두 시그니처 test를 승인 문안대로 고침(`["…", "rails"]`, `ps[:2]` 루프, `rails` KEYWORD_ONLY·기본값 없음·`(RailDeclaration, "RailDeclaration")`). auditor 순서 3 대역 `weakening_diff.py --base B1 --head T1` → FAIL, 발견 = 정확히 두 단위(`test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`, '비교 완화'), `diff_paths` = [P9 경로]. **draft 단계 1의 기대와 같다.** `merge_gate.py diff-hash`가 같은 해시를 낸다. K1 = 두 def에 `*, rails: RailDeclaration`.
   * 운반: `cat-file blob T1:<P9>` → `v5-carry/<id>/<blob id>.blob` + `paths.tsv`. 승인 기록 2건(diff·decision) `parse-approval` 둘 다 exit 0. 정리(worktree remove·`branch -D`) **뒤** `Role: doc` 커밋 하나(기록 2 + blob + card 머리 줄 2개) push → 받음. `branch -D` 뒤에도 K1 객체는 읽힌다(`cat-file -e` 0).
   * 2차: `git diff --quiet B1 B2 -- <P9>` = 0. test worktree 체크아웃의 `.blob`은 CRLF로 풀렸지만(autocrlf) `cp` → `git add` 뒤 **T2의 P9 blob = T1 blob**(`5e79da1…`). K2를 같은 글자로 다시 써서 SD blob K2 = K1.
     §12-6 형태 병합 M. `weakening_diff --base B2 --head M` → PASS, `approved: true`, 해시 = 기록 target. 순서 3 대역(B2..T2)도 PASS·approved. `mutate_changed._approved(M)`에 decision 기록의 id가 있다.
   * 최종 push `role/audit/<id>:master` → **receive exit 0(받음)**. 첫 실행에서는 V1 명령의 old 캐시 경로가 P9 base로 남아 `[EL4 거부] V1 -c 디렉터리가 gmid-gate-cache/<old>/가 아니다`로 거부됐다(대조로서 의미: 판정 기록은 2차 base B2를 old로 적어야 한다).
   * 5단계 운반 디렉터리 삭제 `Role: doc` push → 받음.
4. **역할 경로 규칙.** 운반 blob은 test 분류 파일(`skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py`)뿐이다. test-author가 읽는 `.blob`·`paths.tsv`는 `docs/03-analysis/**`(분류 doc)라 §6.4 소스 열람 거부(`judge_read`: classify == source일 때만)에 걸리지 않고, `cp` 목적지는 자기 worktree의 `tests/**`(쓰기 허용 행 618). code-author의 `git show K1:<SD>`는 `READ_SUBS`라 EL1이 막지 않고, Edit 대상 SD는 행 599. 역할 agent에 cherry-pick/apply를 시키지 않는다(`REF_MOVE`에 cherry-pick·am 있음 -- draft가 피했다).
5. **착수 조건 명령.** `H=$(git -C "$R" rev-parse gate/master)` 뒤 `cat-file -e "$H:<경로>"`를 실제 저장소에서 돌렸다: 충족된 것(`20260930-b26-before-phase3.md`, `20261001-b26-backfill-interdig-fix.md`, 양성 대조 P9 판정 기록)은 0, 아직 아닌 것(exempt-binding·changed-stmt-scope·b34·b26pre 판정 기록, `20261001-b26-phase3-cards.md`, `phase2-dod.md`)은 128. 구별한다.
   `gate/master:<경로>` 형태는 MSYS2가 `gate\master;.ai\…`로 바꿔 존재하는 파일에도 128 -- draft의 경고가 맞다. 판정 기록 존재 = 병합이라는 등식도 맞다(기록은 최종 push의 `new`에만 생긴다). card id 세 개(`20260930-b34-grammar-explicit`, `20260930-b26-pre-test-strengthen`, `20261001-b26-backfill-interdig-final-audit`)는 각 draft 머리 `id:`와 같다.

## 발견

### B1. 단계 2의 push가 정리 **전**이라 EL1이 거부한다(그리고 인용한 정본과 어긋난다)
draft 451행 단계 2: "… = `Role: doc` 커밋 하나**, gate push(…) 뒤에 1차 역할 브랜치·worktree 정리". 그런데 EL1 `role_hooks._judge_push`(gate `19eb475` 808~811행)는 메인 worktree의 `git push gate master:master`를
역할 브랜치가 하나라도 있으면 거부한다(`진행 중인 변경이 있어(역할 브랜치 …) 문서 커밋 push를 거부한다(review29 Q-08)`, 2026-09-21 `c96e2bd`부터). scratch 모의에서 이 함수를 직접 불렀다:
역할 브랜치가 있을 때 → 이 메시지로 거부, `branch -D` 뒤 → 이 검사는 통과(scratch라 다음 무결성 대조에서 멈춤). 정본 인용(445행 (2))도 "정리 **전에** [blob 추출] … -- **정리 뒤** `Role: doc` 커밋·gate push"다.
**고침:** 단계 2를 '정리 전: blob·`paths.tsv` 추출, T1·K1 id·`git show K1:<SD>` 사본·auditor 산출물 보관 → 정리(worktree remove·`branch -D` 세 역할) → `Role: doc` 커밋 하나 → push'로. 모의는 이 순서로 돌렸고 끝까지 받았다.
같은 순서가 승인 문안 주석 1·3("1차 정리 전")에도 걸린다 -- 그쪽은 '기록을 쓰는 시점'이라 틀리지 않지만, 커밋·push는 정리 뒤라고 한 마디 더하면 혼동이 없다.

### S1. 정리하면 사라지는 1차 auditor 산출물 보관이 빠졌다
auditor 정의(`agents/gmid-verification-auditor.md` 48~49행): 순서 3 결과는 `<audit worktree>/.ai/verification/<id>/base_check.json`에 쓰고 커밋은 순서 7이다. 1차는 순서 7이 없으니 정리(audit worktree 삭제) 때 이 파일과 V3 측정 출력이 없어진다.
기록 4의 target(`diff_hash`)·기록 5의 target(변이 id@def 해시)과 2차 판정 기록이 인용할 1차 근거가 여기서 온다. 단계 2는 T1·K1 id와 K1 SD 사본만 `_drafts/b26_1_attempt1/`에 남긴다.
P9 선례는 2차 기록에 `attempt1_base_check.json`·`attempt1_order7/…`을 실었다. **고침:** 단계 2 '정리 전'에 `base_check.json`과 V3 출력(변이 목록·생존 id·해시)을 `_drafts/b26_1_attempt1/`로 복사한다고 적는다(2차 auditor가 기록에 옮길 대상).

### minor
* m1. 단계 3 test-author의 "나머지 test 파일은 T1과 같은 내용으로 다시 쓴다" -- 출처가 없다. 1차 브랜치가 지워진 뒤라 `git show T1:<test 경로>`(test 분류만, 읽기 명령) 또는 단계 2에서 남긴 사본이라고 적는다. 모의에서 `branch -D` 뒤에도 T1·K1 객체는 읽혔다(gc 유예 안).
* m2. 단계 1 "병합 후보 상당(T1+K1, 병합·push 없음)에서 V3" -- M 트리 = M^2(K1) 트리라 `--head K1`로 재면 된다고 적으면 auditor가 병합을 만들지 않는다(1차 audit worktree에 병합 상태가 남지 않는다).
* m3. 단계 2의 `<design>` 자리 "이 커밋 때 정한다" -- 게이트는 `docs/03-analysis/**` 아무 이름이나 받지만(모의 `gain-budget-gmid-sizing-toy`도 받음), 2차 test-author 브리핑에 경로가 고정돼야 하므로 지금 정해 두는 편이 낫다(선례 디렉터리 이름 하나를 고르면 끝).
* m4. B34 조건 4·b26pre 조건 3·backfill 조건 3(Phase 2 DoD PASS)만 명령이 없다. `phase2_dod_brief.md`는 FAIL도 결과 파일에 적으라 하므로 파일 존재 ≠ PASS다. `git -C "$R" show "$H:docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md"`의 `## 판정` 표 E0~E5가 모두 PASS인지 읽는다는 한 줄을 더한다.

## 모의가 덮지 않은 것(가정)
* V3 면제 형식은 `19eb475` 도구(`reachability._approved_ids`, id 목록) 기준이다. `id@def 원본 해시` 형식은 binding card(착수 조건 5) 병합 뒤 도구가 정한다 -- 그때 '기록이 head 트리에 있으면 찾는다'는 같은 `ls-tree <rev> .ai/approvals/` 구조라면 성립한다(미확인).
* fake gate는 무결성 대조(`integrity.py --scope gate`)를 뺐다. 실 pytest(V1)·V3 실행은 하지 않았다(receive는 형식만 본다).

## 범위 밖(한 줄씩)
* B26-1 자기 착수 조건 5~7·10·11은 세 card와 달리 `cat-file -e "$H:…"` 명령이 없다(이번 회차 변경 아님).
