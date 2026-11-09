# 독립 검토 -- Phase 3 design 30 착수 커밋(p3_design_commit.sh) 실행 전 (2026-10-02)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용, 실측은 모두 `C:/g201`(복제본 + 가짜 bare gate, 끝에 삭제).
대상: `_drafts/p3_design_commit.sh`(sha256 `d10b26957aa615fc`), `p3_design_commit.md`, `approval_20260930-30-module-split-design.md`(`15bc6f5102f572c3`),
`approval_20260930-p3-gate-move-aware.md`(`d1701dcb7d99914a`, UD-5 초안 -- 이번 커밋 대상 아님).

## 판정: **진행 가능(PASS)** -- B 0 · S 2 · minor 4

이번 커밋(C1·C2)의 바이트·승인 기록·게이트 수락은 독립 실측으로 모두 확인됐다. S 두 건 중 S-1은 승인 기록 문구 한 곳이라 실행 전에 고치는 것을 권한다(1분 편집, fill 결과 target 불변 --
target은 6경로 diff 해시라 승인 기록 본문과 무관). S-2는 UD-5 초안 몫이라 G1 때 고치면 된다.

## 1. 승인 바이트 일치(검토 항목 1)

복제본에서 `local`을 끝까지 돌린 뒤(아래 §5), 스크립트 코드와 따로 쓴 대조 스크립트(`C:/g201/verify.py`)로 C1 트리를 직접 읽어 비교했다.

| 대상 | 승인 해시(질문 시점) | 지금 초안 sha256 | C1 커밋 바이트 |
|---|---|---|---|
| design `draft_phase3_design_v8.md` | `a4350dc05ff86179` | 같음 | 1,397행 중 **3행만** 다름(초안 표지 → 승인 표지), 나머지 1,396행 바이트 동일 |
| 문서 개정 `p3_doc_amendments.md` | `363e3cc2da4fc96d` | 같음 | 아래 대조 |
| `e_inst_p3.py` | `7d26134ad00ec504` | 같음 | 바이트 동일 |
| `e_lib_p3.py` | `c6b82fc7b4cd974c` | 같음 | 바이트 동일 |

* 초안 네 파일의 mtime이 모두 질문(2026-10-02 01:46 KST) 전이다(design 01:39, 개정 01:38, 질문 배경 01:40) -- 질문 뒤 바뀌지 않았다.
* 문서 개정 독립 대조: 스크립트의 블록 번호 표(MAP)를 쓰지 않고, 개정 문서에서 '현재 …' 표지 뒤 블록과 바로 다음 '새 문안 …' 블록을 짝지어 14쌍을 만들었다((a)는 '새 문안 -- D-19 답 **(가) MOD2**' 블록).
  C1^ → C1에서 바뀐 줄이 정확히 그 14쌍과 하나씩 대응하고, 쓰이지 않은 쌍 0:
  * 계획서: 521·522·523·524·525·526·528·529(N3.10 MOD1~MOD6·MOD8·MOD9 = 8행, MOD7 527행 불변)·534·687 -- 10줄
  * 00-common: 103·431 / 10-test-separation: 250·252
  * 각 쌍의 '현재 `파일:줄`' 표기와 실제 바뀐 줄 번호도 같다. 줄 수 불변(줄 끝 보존 CRLF 작업 트리 → index LF).
* 계획 533행(UD-5)은 바뀌지 않았다. final의 G1 패치 `--check --no-preconditions`가 5/5 앵커 'would apply'(533행 포함). 복제본 status는 깨끗하다(쓰기 없음).

## 2. 사용자 원문·범위(검토 항목 2)

세션 jsonl에서 `toolu_01VKN8qT3BbTikfZQyV9sdQi`의 tool_use(2026-10-01T16:46:15Z = 10-02 01:46 KST)와 tool_result(02:05:20Z = 11:05 KST)를 직접 뽑아
승인 기록 두 초안과 비교했다(`C:/g201/cmp.py` -- 스크립트의 check_quote와 다른 코드):
* design 기록: UD-0·D-19·UD-1의 질문 원문 `"…"`, 선택지 `"라벨" -- "설명"` **짝 그대로**(모든 선택지), `> 답`, `답: "…"` 전부 바이트 일치. UD-5 내용은 들어 있지 않다.
* UD-5 초안: UD-5만 같은 방식으로 전부 일치. 다른 세 질문 내용은 없다.
* 시각 표기(01:46 / 11:05 KST)·`date: 2026-10-02`가 맞다.

범위 판정 -- 사용자가 실제로 본 것: (i) AskUserQuestion 네 질문 문안과 선택지, (ii) 그 전 오케스트레이터 요약(10-01 15:37Z v8.4 요약 -- FU, 배정 규칙 보강, UD-0 (d), 질문 넷;
16:09Z -- `_kv_table`을 MOD9 행에 넣어 UD-0 범위에서 닫는다). 질문 바로 앞 턴에는 사용자에게 보인 텍스트가 없다(thinking만). 
**`phase3_approval_question.md`와 `draft_phase3_design_v8.md` 경로는 사용자에게 보인 텍스트 어디에도 나오지 않는다**(세션 assistant 텍스트를 전부 grep -- 마지막 design 경로 언급은 v5 때).
* '덮는 것' 각 항목은 질문의 "design 30-module-split(10모듈 분할, card 17건 — 준비 card FU 포함)과 문서 개정(N3.10 표 정정 12건 등)" + (a)~(d)의 풀이다.
  design 승인 = design 문서 전체라는 읽기, "12건" = 3 + 8 + 1(실측으로 맞음), "등" = 534행·687행·00-common·10-test(질문에 이름은 없지만 v8.4 요약과 design 문서 개정 범위 안), D0b의 새 개정은
  위임하지 않음(선택지 설명 그대로) -- 범위 초과는 찾지 못했다.
* (a)~(d) = D-9·D-17·D-28 (e)·D-31 대응은 해석이지만 각 줄에 질문 원문을 먼저 인용하고 풀이를 붙여 구분된다. 문제없음.

## 3. plan_tables_hash 불변(검토 항목 3)

복제본 gate 캐시의 `merge_gate.plan_tables_hash`로 base(모의 착지 판 `2320418`)·C1·C2 계획서를 각각 따로 계산: 세 값 모두 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d`.
설명서의 dd60db6 값과 같다(V3 묶기 card 병합은 계획서를 바꾸지 않는다). `plan_tables` 승인 불필요 주장 맞음.

## 4. 스크립트 안전(검토 항목 4)

* `launch_common.sh` 가드: `lc_repo_guard`(git-common-dir 정규화 비교, 복제본의 remote gate가 실제 gate면 거부), 실제 모드 `lc_need_real --state`, 복제본 모드 `lc_need_sandbox`, `lc_tmp_setup`. 실제 경로 분기는 `--repo` 없을 때만.
* EL1 판정 대상 명령(push, worktree, branch -D, reset·checkout --·restore·update-ref)은 실제 저장소 경로에서 하나도 실행하지 않는다 -- 실제 경로에서 쓰는 git은 fetch·rev-parse·for-each-ref·diff·status·cat-file·show·add·commit·log·rev-list뿐.
  push는 `lc_push_cmd`로 출력만. mk-sandbox의 `merge --ff-only`·`remote`·`branch --set-upstream-to`·`config core.hooksPath`는 `/c/g<번호>/<이름>` 복제본에서만(`test ! -e` 선확인).
* 실제 모드 pre: `test -z "$(g for-each-ref refs/heads/role/)"`(353행, 모드 무관 -- 실측: 복제본에 `role/test/dummy-x`를 만들면 353행에서 멈춤 rc=1)와
  `lc_pred_ok`(V1~V10 PASS·N/A, id 일치) 실패 시 실제 모드만 중단(360행). 지금 실제 저장소에는 `role/{audit,code,test}/20260930-v3-exempt-binding` 3개가 남아 있고
  `.ai/verification/20260930-v3-exempt-binding.json`이 없다(audit worktree에 `base_check.json`뿐) -- **지금 실제 실행하면 pre가 멈춘다(의도대로)**.
* final의 로컬 `merge_gate receive`와 G1 패치 `--check`는 쓰기 없음(복제본 status 깨끗).

## 5. 모래상자 리허설(검토 항목 5) -- 모의 '묶기 card 착지' 위에서

1. `--sbx /c/g201/s --base 5a602d4 mk-sandbox`(병합 M `5a602d4` + 합성 audit `056664b`).
2. 그 위에 **모의 판정 기록 커밋** `2320418`(`.ai/verification/20260930-v3-exempt-binding.json`, id 일치·V1~V10 PASS/N/A, `Role: audit`·`Change-Id`): 가짜 gate에 push하면 EL4가
   "new의 부모가 이번 push의 병합 커밋 M이 아니다"로 거부(M이 이미 gate에 있는 모래상자 구조 탓 -- 실제로는 M과 같은 push) → bare gate에 fetch로 넣고 accept-log 한 줄 추가. 이 판이 '착지 뒤 gate master' 모의다.
3. 거부 확인: `role/test/dummy-x` 있을 때 pre 353행 중단(rc=1) → 지운 뒤 진행.
4. `--repo /c/g201/s/r --state /c/g201/s/state.txt local` rc=0: pre에서 **`선행 20260930-v3-exempt-binding 판정 기록 병합됨`**(lc_pred_ok PASS 경로 -- 설명서 §5-4가 '덮지 못함'이라 한 분기를 이번에 덮음),
   원문 대조 OK 2건, C1 `9e11904`, C2 `6826712`, target `cb273b10d79670e688eb6c06a920a379f57d705601edd51c8ac6adc4894aa14c`(설명서 A·B와 같은 값 -- 6경로 base blob 불변이라 착지 뒤에도 같음),
   로컬 receive exit 0, G1 앵커 5/5.
5. 출력된 push 명령을 단독 호출(가짜 gate, EL3 `.githooks` + EL4 `pre-receive`): **수락** `2320418..6826712`, accept-log `2320418 6826712`. `after-push` OK.
6. C2: 승인 기록 = 초안에서 `target`·`diff_base`(= `2320418` = C1^)·`diff_head`(= C1) 세 줄만 다름; `.ai/context.md` numstat `3 0`, blob = 이전 blob + 3줄(LF).

## 발견

### S-1 승인 기록 '범위 설명' 첫 줄이 사용자에게 보이지 않은 것을 '올렸다'고 쓴다
`approval_20260930-30-module-split-design.md` "승인 대상 판(질문 때 올린 바이트, sha256 전체)". 세션 기록상 design 초안·문서 개정·스크립트 파일(그리고 `phase3_approval_question.md`)은
사용자에게 경로·내용 어느 쪽으로도 제시되지 않았다(§2). 바이트를 고정하는 것 자체는 옳지만 표현이 사용자 노출을 과장한다(작성자≠검증자 원칙상 승인 기록은 사실만).
권고: "승인 대상 판(질문 시점 2026-10-02 01:46 KST의 초안 바이트 -- 질문에는 문안만 올렸고 파일은 제시하지 않음, sha256 전체)" 정도로. "질문의 배경 문안은 …" 문장도
"(사용자에게 제시하지 않은 오케스트레이터 작업 문서)"를 덧붙이면 정확하다. 고치면 `DRAFT_APR` sha256이 바뀌지만 스크립트는 그 해시를 고정하지 않으므로(`<rev-parse>` 3개·원문 대조만) 그대로 돈다;
설명서 머리의 해시 `15bc6f51…`만 갱신.

### S-2 (UD-5 초안, G1 때) redteam 단계 수가 G1 card와 다르고, G1 card가 질문 뒤 바뀌었다
* 초안 37행 "red 7 + 거부 22 = 29단계 x 도구 3" -- 지금 G1 card(`draft_p3_g1.spec.md`) 174·184·209·265행은 **31단계(red 8 + 거부 23) x 3 = 93**. `g1_kit/` 원본 초안에서 그대로 옮겨진 낡은 수다.
* `draft_p3_g1.spec.md` mtime 10-02 02:01 > 질문 01:46: 질문 문안이 가리킨 판 `b8a47418c8923b60`(phase3_approval_question.md 137행)은 지금 `b758140a8744fc95`이고 질문 시점 사본이 남아 있지 않다
  (`.pre-v84.md` = `cacf06ad…`는 그 전 판). G1 커밋 때 UD-5 기록이 어느 판을 덮는지, 질문 뒤 변경이 '계약·redteam 무변경'인지 diff로 밝혀야 한다. 이번 커밋에는 영향 없음(초안은 pre에서 원문 대조만 함).

### minor
* m1 `check_quote`는 질문·라벨·설명·답을 **각각 부분 문자열로만** 찾는다 -- 라벨과 설명의 짝을 바꾼 변조 사본(D-19 두 선택지 설명 맞바꿈)이 rc=0으로 통과했다(실측 `C:/g201/t2.md`).
  지금 기록은 짝이 맞다(§2 독립 대조). `'"%s" -- "%s"' % (label, description)`로 찾게 하면 닫힌다.
* m2 이어 하기: c1·appr가 작업 트리를 쓴 뒤 커밋 전에 실패하면 같은 단계 재실행은 멈춘다(c1: "작업 트리가 base 판과 다르다/새 파일이 이미 있다", appr: 407행 context.md 변경). 안전 쪽이지만 되돌리기
  (`git restore`·`checkout --`)가 EL1 대상이라 오케스트레이터 단독 호출이 필요하다 -- 설명서 §3 '이어 하기'에 한 줄 적어 두면 좋다(appr는 승인 기록 파일만 이어 간다고만 적혀 있다).
* m3 final은 fetch 없이 `gate/master`(원격 추적 ref)만 본다 -- gate가 그사이 움직이면 final은 통과하고 push가 non-ff로 거부된다. 결과는 안전, 알림만 늦다.
* m4 실제 `.ai/context.md`는 `w/lf`(실측 `git ls-files --eol`), 모래상자는 `w/crlf` -- append 코드는 끝 줄바꿈을 따르고 blob 검사(`\r` 없음 + 3줄)가 있으므로 실제 분기도 안전하다고 판단(실행 경로 동일, 분기 값만 다름).

## 실제 실행 조건(확인)
V3 묶기 card의 판정 기록이 gate master에 push되고 role 브랜치 3개가 정리된 뒤 → 로컬 master ff → `pre`. 그때 C1·C2 target은 6경로 base blob이 그대로면 `cb273b10…`이 나와야 한다(다르면 base 트리 변화를 먼저 확인).

## 검토 중 사고 기록
검토자가 대조 스크립트 출력 경로를 잘못 써(`'rC:g201q.json'` -- NTFS 대체 스트림) 실제 저장소 루트에 빈 파일 `rC`(+ 스트림)를 11:47에 만들었다. 내용(이 검토용 jsonl 발췌)을 모래상자로 옮기고
즉시 지웠다; 추적 파일·index·ref는 건드리지 않았고 status는 처음과 같다(아래).
끝 상태: 실제 저장소 `git status --porcelain`이 시작 스냅샷과 같고(HEAD = master = gate/master = `dd60db6`, role 브랜치 3개 그대로), `C:/g201` 삭제.
