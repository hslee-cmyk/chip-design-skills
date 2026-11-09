# Phase 3 design 30 착수 커밋 -- 절차·게이트 요구·모래상자 리허설 결과 (2026-10-02)

스크립트: `_drafts/p3_design_commit.sh`(sha256 앞 16 `ad52f99614b1690a`). 승인 기록 초안: `_drafts/approval_20260930-30-module-split-design.md`(`8b297e75148728ca`),
UD-5 초안(나중 G1 card용): `_drafts/approval_20260930-p3-gate-move-aware.md`(`24d3c00f715800f2`). r1(2026-10-02, 검토 `review_p3_design_commit.md` S-1·S-2·m1~m3 + mk-sandbox 경로 가드) 이전 판은 `*.pre-r1.*`. 사용자 답: `_drafts/user_decisions.md` 마지막 절, 원문 = 세션 jsonl
tool_use `toolu_01VKN8qT3BbTikfZQyV9sdQi`(질문 2026-10-01T16:46:15Z) / tool_result(답 2026-10-02T02:05:20Z). 저장소 쓰기는 하지 않았다(리허설은 모두 `C:/g188` 복제본).

## 1. 게이트가 요구하는 것(gate `master` `dd60db6` 판 `merge_gate.py`·`role_paths.py`를 읽고 실측)

* EL3·EL4 커밋 판정(`judge_commit_change`): 경로표와 겹치는 경로를 바꾸는 커밋은 트레일러 `Role:` 정확히 하나. `Role: doc` = 오케스트레이터, 쓰기 경로표(계획 N3.12.2) 행
  `docs/01-plan/**`·`docs/02-design/**`·`docs/03-analysis/**`(레지스트리 제외)·`.ai/context.md`·`.ai/approvals/**` 모두 조건 `없음` -- 새 `.py`(docs/03-analysis/…/scripts/)도 이 행이다.
  Change-Id는 doc 커밋에 필요 없다(역할 커밋·병합만).
* 계획서를 바꾸는 커밋: 바뀐 뒤 `plan_tables_hash`가 바뀌면 같은 push 안에 `target_kind: plan_tables` 승인 기록이 필요하다. 해시 입력은 N4.1·N4.2·N6.1·N3.12.2 표뿐 --
  이번에 바뀌는 계획서 줄(N3.10 표 8행, 534행, 687행)은 입력 밖이고 실측으로 전후 `7167e02839f86c4ecbcd91a63a9833c4d83a8aab8008bfe2d8cfc36206d2596d` 동일. **plan_tables 승인 불필요**.
* 승인 기록 자체는 doc push의 필수 요건이 아니다(EL4는 파싱 실패 파일을 승인으로 세지 않을 뿐). 쓰임: (1) spec card `approval:` 줄 -- FU·T0·D0a·D0b가 `20260930-30-module-split-design`을 가리키고,
  FU 착수 조건 S-1이 gate `master`의 이 기록에서 `grep -c 20261002-p3-future-annotations`(1 이상)를 본다(초안에 2회). (2) `gate_change: yes` card(G1)는 `gate_change_ok`가 base 트리에서
  `approval:` 기록 파싱을 요구한다 -- G1의 `20260930-p3-gate-move-aware`는 G1 역할 커밋 전에 gate에 있어야 한다(이 순서 밖).
* `target_kind: diff`는 diff_head 커밋이 있어야 해시를 낼 수 있다 -> **문서 커밋 C1 뒤에 승인 기록 C2**(선례 `20260930-v3-exempt-binding`: 84e91a4 → 7718505 → dd60db6). 둘을 한 push로.
* EL1: 역할 브랜치(`refs/heads/role/*`)가 남아 있으면 문서 push를 거부한다(design 05 §12) -- 지금 실제 저장소에 V3 면제 묶기 card 브랜치 3개가 있다. 그래서 **실제 실행은 그 card의
  판정 기록 push와 브랜치 정리가 끝난 뒤**(pre가 실제 모드에서 `lc_pred_ok`(판정 기록 V1~V10 PASS·N/A)와 role 브랜치 0을 강제).

결론 -- 순서: (V3 묶기 card 판정 기록 push·정리) → C1 문서 커밋 → C2 승인 기록 + context → push 1회 → (나중) G1 문서·spec card 커밋 → UD-5 승인 기록 → FU·T0·D0a·D0b spec card.
D-19·UD-1은 별도 기록 없이 같은 승인 기록에 접는다(`phase3_approval_question.md` 19~20행: "UD-0·D-19 → `20260930-30-module-split-design` …, UD-1 → 같은 design 승인 기록의 범위 설명에 U-03 답").

## 2. 커밋 내용

| 커밋 | 경로 | 내용 |
|---|---|---|
| C1 `Role: doc` | `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`(새) | 초안 v8.5 바이트(sha256 `a4350dc0…` 확인 후), **3행 초안 표지만** 승인 표지로(아래 §5-1) |
| | 계획서 | `p3_doc_amendments.md` v8.5(sha256 `363e3cc2…`) §1 (a)**(가)**·(b)·(c)·(d), §2(534행 shim), §3(687행 T0·T1), §9 (e)~(h) -- '현재' 줄을 내용으로 찾아(정확히 1회) 교체, 10줄 |
| | 00-common | §4 103행·431행(`topology_path`) |
| | 10-test-separation | §5 250·252행('파일' 열 = 설명) |
| | `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`·`e_lib_p3.py`(새) | 같은 바이트(sha256 `7d26134a…`·`c6b82fc7…`, blob 재확인) |
| C2 `Role: doc` | `.ai/approvals/20260930-30-module-split-design.md` | `fill_v3_approval.py`(diff_base = C1^ = gate master, diff_head = C1, diff_path 6개, target = `weakening_diff.diff_hash` = `merge_gate.compute_diff_hash`) |
| | `.ai/context.md` | 바이너리 append 3줄(빈 줄 + 사용자 결정 4문항 + C1 기록), 삭제 0줄, 스테이징 blob = 이전 blob + 3줄 확인 |

계획 **533행(UD-5)은 넣지 않는다** -- 문서 개정 '덮지 않는 것'과 G1 spec card 계약 13대로 G1 문서 커밋(`g1_kit/patch_g1_docs.py`) 몫. final 단계가 그 패치의 앵커가 이 개정 뒤에도
그대로인지 `--check --no-preconditions`로 확인한다(5곳 모두 'would apply', 533행 포함).

적용 확인(스크립트 `amend`, 기대 바이트에서): `mod_table` 10행, N3.10 4열·10행, 두 행 이상에 걸린 백틱 식별자 0, 이동 토큰 16개(`load_topology` … `_kv_table`, `rail_declaration` = MOD2)가 기대 행에만,
`import_layering --root` exit 0, 10-test-separation §5.6 21행·새 머리, `plan_tables_hash` 불변. 거부 확인: pre에서 `verify`가 적용 전 판을 통과시키면 멈춘다(실측 거부됨).
사용자 원문: 승인 기록 초안 두 개의 질문·선택지·답을 jsonl tool_use/tool_result와 바이트 대조(pre·appr) -- 질문 항목(`* 질문 [H] 원문: "…"`부터 다음 항목 앞까지) 안에서 선택지마다
`"라벨" -- "설명"` **짝**과 `답: "…"`을 찾는다(r1, 검토 m1 -- 전에는 각 문자열을 따로 찾아 짝을 맞바꾼 사본도 통과했다). design 기록은 '사용자에게 보인 것'의 오케스트레이터 메시지 두 건
(uuid `ddf321ed…` 질문 바로 앞 텍스트, `4a9d93cf…` 마지막 Phase 3 요약)도 jsonl text 블록과 `` ```text `` 펜스 안 바이트로 대조한다(`msg:<uuid>`).
거부 실측(r1, `C:/g206`): D-19 두 선택지 설명 맞바꿈 rc=1, 요약 한 글자 변경 rc=1, D-19 `답:` 줄 삭제 rc=1, 원본 rc=0. (r0: 마침표 하나 삭제 거부.)

## 3. 실행 명령

```bash
D=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
bash $D/p3_design_commit.sh pre        # 저장소 변경 없음. 실제 모드: V3 묶기 판정 기록·role 브랜치 0 강제
bash $D/p3_design_commit.sh local      # pre -> c1 -> appr -> final (로컬 커밋 2개, 끝에 push 명령 출력)
# final이 출력한 명령을 단독 호출(EL1 판정 대상, 병렬·tail 금지, 전체 출력 확인):
env APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills push gate master:master
bash $D/p3_design_commit.sh after-push # gate master = C2
```
중단 뒤 이어 하기: 단계 이름 하나(`c1`·`appr`·`final`) -- 상태 파일 `_drafts/p3_design_commit_state.txt`. appr는 추적 안 된 승인 기록 파일이 fill 결과와 같으면 이어 간다.
`final`은 먼저 `git fetch gate`를 하고 `gate/master` = pre 때 gate master(`GATE_BASE`)를 본다(r1, 검토 m3 -- 그사이 gate가 움직였으면 push의 non-ff 거부 전에 여기서 멈춘다; 그때는 처음부터 다시 판단).

커밋 전에 c1·appr가 멈췄을 때 손으로 되돌리기(r1, 검토 m2 -- `post_p10b_runbook.md` §4와 같은 방식). 같은 단계를 그냥 다시 돌리면 c1은 "작업 트리가 base 판과 다르다 / 새 파일이 이미 있다",
appr는 `.ai/context.md` 변경 검사에서 멈춘다(안전 쪽). EL1은 `reset`을 막으므로 바뀐 경로만 되돌린다 -- 아래를 **한 줄씩 단독 호출**(EL1 판정 대상, 병렬 금지), `R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`:
* c1이 커밋 전에 멈췄을 때(HEAD = `GATE_BASE`). 먼저 `git -C <R> diff --cached --name-only`를 본다 -- 빈 출력이면(`add` 전) 첫 줄 `restore --staged`는 건너뛴다
  (`add` 전에는 새 파일 셋이 index에 없어 `restore --staged`가 "pathspec did not match"로 실패한다 -- 모래상자 실측):
  ```bash
  git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills restore --staged -- docs/01-plan/features/gain-budget-gmid-sizing.plan.md docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py
  git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills checkout -- docs/01-plan/features/gain-budget-gmid-sizing.plan.md docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md
  rm /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py
  ```
  (`add` 뒤라면 6경로가 모두 index에 있어 첫 줄이 통과한다. `scripts/` 디렉터리가 비면 그대로 둬도 된다 -- git은 빈 디렉터리를 보지 않는다.)
  그 뒤 `git -C … status --porcelain -- <위 6경로>`가 빈 출력인지 보고 `bash $D/p3_design_commit.sh c1`.
* appr가 커밋 전에 멈췄을 때(HEAD = C1). 같은 이유로 `diff --cached --name-only`가 비었으면 첫 줄을 건너뛴다(승인 기록 파일이 아직 없으면 `rm`도 건너뛴다):
  ```bash
  git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills restore --staged -- .ai/approvals/20260930-30-module-split-design.md .ai/context.md
  git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills checkout -- .ai/context.md
  rm /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/.ai/approvals/20260930-30-module-split-design.md
  ```
  (`.ai/context.md`는 append만 했으므로 `checkout --`이 원래 바이트로 돌린다. 승인 기록 파일은 fill 결과와 같으면 남겨 둬도 appr가 이어 가지만, 원인을 모르면 지운다.) 그 뒤 `bash $D/p3_design_commit.sh appr`.
* 커밋한 뒤 멈췄으면(c1 커밋 뒤 상태 파일 `C1` 기록 전, appr 커밋 뒤 `C2` 기록 전 등): 되돌리지 않는다(EL1이 `reset`·`revert` 거부). `git log -3`으로 무엇이 커밋됐는지 보고
  사용자에게 보고한다 -- 상태 파일 값을 손으로 채워 이어 가는 것은 그 커밋을 스크립트 검사(numstat·verify·트레일러)와 같은 명령으로 손으로 다시 확인한 뒤에만.

## 4. 모래상자 리허설(EL3 = 복제본 `.githooks`, EL4 = 가짜 bare gate에 실제 `pre-receive`·`gate-runner.py`)

| | A: base `dd60db6`(현재 gate master) | B: base `5a602d4`(V3 묶기 card 병합 M -- 착지 뒤 트리 근사) |
|---|---|---|
| 준비 | `--sbx /c/g188/a mk-sandbox` | `--sbx /c/g188/b --base 5a602d4… mk-sandbox` |
| pre | OK(선행 판정 기록 없음은 모래상자라 보고만), 원문 대조 OK 2건, plan_tables_hash `7167e028…` | 같음 |
| c1 | `b9e6b26`, 6경로 numstat plan 10/10·00-common 2/2·10-test 2/2·design 1397/0·스크립트 100/0·91/0 | `1ce8104`, 같은 blob(design `fb058be9`, plan `bf30a739`, e_inst `2558b914`, e_lib `b57d3380`) |
| appr | `4e562fa`, target `cb273b10d79670e688eb6c06a920a379f57d705601edd51c8ac6adc4894aa14c` | `3514fd9`, target 같음(blob만으로 정해짐 -- 실제 실행에서도 base 3파일 blob이 그대로면 같은 값) |
| final | 로컬 `merge_gate receive` exit 0, G1 앵커 5/5 | 같음 |
| push(EL3 pre-push + EL4 pre-receive) | 수락, accept-log `1c3a360 4e562fa` | 수락, accept-log `42dc2a0 3514fd9` |
| after-push | OK | OK |

거부 확인(A, push 뒤): 트레일러 없는 계획서 커밋 -> **EL3 차단**(`[EL3 차단] 트레일러 Role…`); commit-tree로 만든 같은 커밋 -> 로컬 receive exit 1, 가짜 gate push ->
**`[EL4 거부]` + `pre-receive hook declined`**. 게이트가 살아 있는 상태에서 위 두 커밋이 통과했다는 뜻이다.

## 5. 오케스트레이터 확인 요청(결정 아님 -- 기본안으로 스크립트에 넣음)

1. design 파일 3행: 초안 표지 "[초안 v8.5 -- 저장소 미반영] … (현재 없음)."은 커밋 뒤 거짓이 되므로 승인 표지로 바꿨다(나머지 1,396행은 승인 바이트 그대로, 승인 기록 범위 설명에 명시).
   바이트 그대로를 원하면 `amend`의 `d[2] = NEW3` 한 줄을 빼고 승인 기록 범위 설명의 해당 문장을 지운다.
2. 승인 기록 `date: 2026-10-02`(답 날짜), id는 계획된 `20260930-30-module-split-design`(초안 card들이 이미 이 id를 씀).
3. UD-5 기록 초안은 `g1_kit/` 원본을 고치지 않고 `_drafts/approval_20260930-p3-gate-move-aware.md`로 새로 만들었다(날짜·사용자 원문·질문 원문 채움, `<rev-parse>` 3자리와 끝 주석은 G1 때 fill이 채우고 지운다).
   원본 초안의 선택지 표기 "(가) 전역 이동 인식 규칙 (Recommended)"는 실제 질문 라벨 "(가) 전역 이동 인식 (Recommended)"와 달라 실제 라벨을 썼다.
4. 리허설이 덮지 못한 것: 실제 모드 전용 분기(`lc_need_real`), 실제 `.ai/context.md`(w/lf -- 모래상자 복제는 autocrlf로 w/crlf; append는 작업 트리 줄 끝을 따르고 blob은 LF로 확인).
   선행 판정 기록 PASS 경로는 독립 검토(`review_p3_design_commit.md` §5, `C:/g201`)가 모의 착지 판에서 덮었다.

## 6. r1 고침과 다시 한 리허설(2026-10-02, `C:/g206`, 끝에 삭제)

* S-1: design 승인 기록에 '## 사용자에게 보인 것' 절 -- 사용자가 본 것은 AskUserQuestion 네 질문 문안·선택지와 질문 앞 오케스트레이터 메시지뿐. 질문 바로 앞 텍스트(16:33:31Z)는 Phase 3와 무관한
  진행 보고였고, 마지막 Phase 3 요약은 16:17:04Z 메시지 -- 둘 다 jsonl text 블록 바이트 그대로 인용. design 초안·문서 개정·스크립트·`_drafts/phase3_approval_question.md`는 파일도 경로도 제시하지
  않았다(세션 assistant 텍스트 grep: `phase3_approval_question`·`p3_doc_amendments` 0회). '질문 때 올린 바이트' → '질문 시점의 초안 바이트(파일은 제시하지 않음 -- 오케스트레이터 요약과 질문 문안으로 승인)',
  'design v8.5 전체'에 "질문 문안을 질문 시점 초안 전체로 읽은 것" 명시. UD-5 초안도 배경 문안을 '제시하지 않은 작업 문서'로.
* S-2(UD-5 초안): redteam 단계 = red 8 + 거부 23 = 31단계 x 3 = 93(card 174행). 질문 시점 G1 card `b8a47418…` → 지금 `b758140a…`: 질문 뒤 02:00:59~02:01:12 KST G1 재측정 agent의 Edit 3건 --
  지금 판에 거꾸로 적용하면 `b8a47418c8923b6082037986d57f3e9cd9b2bae8990939b39319cf0f0b7013a6`이 정확히 나온다(실측). 바뀐 곳은 '판정 유형 근거' 1문장·'작성 전 실측' 머리 문단·9 (b)(c) -- '관찰 가능한 계약'(계약 0~13, redteam 표) 무변경.
* m1 짝 대조, m2 위 §3 되돌리기, m3 final fetch, 그리고 mk-sandbox 경로 가드를 glob `/c/g[0-9]*/*` → 정규식 `^/c/g[0-9]+/[A-Za-z0-9_][A-Za-z0-9._-]*$`(거부 실측: `/c/g206x/a`·`/c/g196x/a`·`/c/g206/..`·`/c/g206/.a`·`/c/g206/a/b`·`/c/g/a`·`/c/g206`·`/c/g206/a b`·`/c/g206/a/` 모두 exit 2, `/c/g206/s`는 가드 통과).
* 리허설(base = gate master `dd60db6`, 합성 audit `81d898c`): `local` rc=0 -- 원문 대조 OK(design: UD-0·D-19·UD-1 + msg 2건, UD-5), C1 `1ddcbf4`, C2 `4c0b109`, target `cb273b10d79670e688eb6c06a920a379f57d705601edd51c8ac6adc4894aa14c`(r0·독립 검토와 같은 값),
  로컬 receive exit 0, G1 앵커 5/5. 출력된 push 명령 단독 호출 → 가짜 gate **수락** `81d898c..4c0b109`(accept-log 한 줄). `after-push` OK.
  m3 거부 확인: 원격 추적 ref를 `GATE_BASE`로 되감은 뒤 `final` -- fetch가 실제 gate(`4c0b109`)를 가져와 `gate/master = GATE_BASE` 단정에서 rc=1.
  m2 되돌리기 실측(모래상자): `.ai/context.md` append + 새 승인 파일 `add` 상태에서 `restore --staged` → `checkout -- .ai/context.md` → 리터럴 `rm` 세 단독 호출 뒤 status 깨끗;
  index에 없는 경로에 `restore --staged`는 rc=1("pathspec did not match") -- 그래서 §3에 '`diff --cached`가 비면 건너뛴다'.
