# Phase 3 design 30 착수 커밋 -- 절차·게이트 요구·모래상자 리허설 결과 (2026-10-02)

스크립트: `_drafts/p3_design_commit.sh`(sha256 앞 16 `d10b26957aa615fc`). 승인 기록 초안: `_drafts/approval_20260930-30-module-split-design.md`(`15bc6f5102f572c3`),
UD-5 초안(나중 G1 card용): `_drafts/approval_20260930-p3-gate-move-aware.md`(`d1701dcb7d99914a`). 사용자 답: `_drafts/user_decisions.md` 마지막 절, 원문 = 세션 jsonl
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
사용자 원문: 승인 기록 초안 두 개의 질문·선택지 라벨·설명·답을 jsonl tool_use/tool_result와 바이트 대조(pre·appr) -- 변조 사본(마침표 하나 삭제)은 거부됨(실측).

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
4. 리허설이 덮지 못한 것: 실제 모드 전용 분기(선행 판정 기록 PASS 경로, `lc_need_real`), 실제 `.ai/context.md`(w/lf -- 모래상자 복제는 autocrlf로 w/crlf; append는 작업 트리 줄 끝을 따르고 blob은 LF로 확인).
