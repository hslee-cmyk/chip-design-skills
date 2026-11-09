# B26-1 1차 시도 dispute 처리 절차 (20260930-b26-rail-accessor-set)

작성 2026-10-07. 읽기 전용 분석 + 문안. 기준: gate master `6df4bd7`(= 메인 HEAD = launch 상태 `B1`·`S`), 1차 시도 T1 `c247a76`(test 커밋 61751ab·c247a76), K1 `e92e6b8`(code 커밋 하나, dispute 동봉).
dispute blob `04ea6a2732fde2342f228c25e6444b7999b16309`(e92e6b8 트리 = code worktree 파일 바이트 sha1, LF -- 실측 일치).
근거 정본: design 05(`6df4bd7`) §6.2 '정리 전 dispute 보존' 행·push 행, §12 '재시도'·'정리' 행, §9.2-4 모양 표 / gate 판 `tools/gates/role_hooks.py` `_dispute_guard`·`_judge_push`·`_judge_worktree`·`_judge_branch` / `tools/gates/mutate_changed.py` 14·44·679~684행(기준 실행 실패 = ERROR) / `_drafts/b26_1_carry.sh`·`b26_1_launch.sh`.

## 1. 답 요약

| 질문 | 답 |
|---|---|
| (1) card에 무엇을, 어떻게 | `## dispute 기록` 절을 card **끝에** 더한다(현재 마지막 절 `## 작성 전 실측` 뒤 -- 양식 §11.2의 순서상 마지막 절, 선례 `21a625d`·`fb8ee35`도 끝에 추가). 내용 = dispute 원문 인용(`> ` 접두) + **40자리 blob id**(`blob: 04ea6a27…`) + 결정 원문 인용. 커밋 = 메인 worktree에 **로컬 `Role: doc` 커밋 하나**(card 한 파일, 줄 추가만). **push는 정리 전에 필요 없다**: `_dispute_guard`는 `git -C <메인> show HEAD:<card>`(메인 worktree HEAD)의 절에서 blob id를 부분 문자열로 찾는다 -- gate가 아니다. 그리고 정리 전 push는 `_judge_push`가 거부한다(역할 브랜치 존재). 순서 = 로컬 커밋 → 정리 → push(§12 재시도 행 "spec card 개정의 gate push는 정리 뒤에 한다") |
| (2) T1에 커밋을 더해 이어 갈 수 있나 | **없다. 1차 시도 전체를 같은 id로 순서 1부터 다시 한다(§12 재시도: "dispute … 뒤에는 정리 형태로 세 worktree·브랜치를 지우고 같은 id로 1부터 다시 한다. 부분 되돌리기는 쓰지 않는다").** 이어 갈 수 없는 실측 근거 4개: ① K1 `e92e6b8`의 부모는 T1 `c247a76`이고 code-author는 test 커밋을 가져올 수 없다(merge·rebase·cherry-pick·reset·branch -f 모두 EL1 거부) -- role/test에 T1'을 더해도 K1 트리에는 픽스처가 없다. ② audit 브랜치는 T1에 고정(순서 3 freeze, `base_check.json`은 T1에서 잼)이고 옮길 수 없다(reset·merge 거부, §12-6 병합만 허용). ③ card '두 번 시도 절차' 단계 1이 요구하는 V3(`mutate_changed.py --base B1 --head K1`)는 K1 트리에서 s015·s016이 실패하므로 **기준 실행 실패 = verdict ERROR**(mutate_changed 14·44·679~684행: `run_matching_safety_with_finger_growth`는 K1에서 바뀐 def라 변이 대상이고 두 test가 그 인벤토리) -- 기록 5 target(`survivor_bindings`)을 얻을 수 없다. carry check도 `verdict == "FAIL"`·`merge-base --is-ancestor T1 K1`을 요구한다(role/test 끝이 T1'이면 K1의 조상이 아니어서 멈춤). ④ 단계 1 멈춤 조건 "V1·V2·V4 등 다른 검사 FAIL도 멈춘다". **진행 중인 test-author 커밋(T1')은 측정에 쓸 수 없고, 쓸모는 다시 하는 시도의 입력 출처(patch 보관)뿐이다** -- 끝나기를 기다렸다가 보관하고 정리한다. **순서 3 산출물은 다시 잰다**(T 해시가 바뀐다: freeze·red·V5 `diff_head`가 새 T1). 중단된 `base_check.json`은 참고 보관만(기록 4 target 출처로 쓰지 않는다) |
| (3) kit 영향 | 아래 4절. 핵심: carry `NSEC=12`(card 절 수)는 dispute 절로 13이 된다 -- 상수 대신 B1 card에서 세도록 고침. carry의 단일 출처 `B1`(launch 상태 파일)을 D(dispute 커밋, push 뒤 gate master)로 옮기는 launch 단계가 필요(carry check는 `HEAD = gate/master = B1`을 단정 -- 지금 값 6df4bd7이면 D 뒤 멈춤). launch `card`·`final` 단계(초안 바이트 대조, `NSEC`)는 이미 끝난 S 커밋용이라 다시 돌지 않는다(`test ! -e $F_SPEC`로 다시 못 돈다). card sha256 핀은 kit 어디에도 없다(grep 0). 두 번 시도 절차 자체는 그대로: 다시 하는 시도가 '1차 시도'(병합 안 함)이고 그 base가 D다 |
| (4) 초안에도 넣나 | **넣는다.** 초안 `draft_b26_1.spec.md`가 커밋 card의 바이트 출처(launch `stage_card`가 `cp`, `stage_final`이 `cmp`)이므로 D도 같은 방식으로 만든다: 초안 = 옛 초안 + `\n` + 절 → `cp` → 커밋 → `git show HEAD:<card> \| cmp - 초안`. 새 launch 단계가 이 대조를 다시 한다. carry `commit` 단계는 HEAD blob에서 개정을 만들므로 초안과 무관 |

## 2. dispute 기록 문안(정확한 바이트)

* 절 파일: `_drafts/b26_1_dispute_section.md` -- sha256 `312e5c4c291044825971cb5b11bd94b27924eb786a346e8106358858dcebc72b`, 51줄, LF, BOM 없음, 끝 줄바꿈 하나.
* 새 card = `6df4bd7` card(sha256 `220778a1124624e0c4ea97fa7f9b7d80fb7b7f8a62743687729dc681003da782`) + `\n` + 절 파일 → sha256 **`0cc95c35701ba88080cde0a1c074ec7ee3f1a3cca912153126548e980302a6b2`**, 줄 추가 52·삭제 0.
* 모래상자 `/c/g446` 검증(gate 판 `role_paths.py`·`interface_card.py`를 `git show gate/master:`로 꺼내 실행): `parse_spec_card` OK, 절 13개(마지막 둘 `작성 전 실측`·`dispute 기록`), approval 3줄 그대로, `_dispute_guard`와 같은 정규식으로 절 안에 blob 있음, `interface_card.py --root <메인>` 재생성 = 커밋된 `6df4bd7` interface card와 **바이트 같음**(기존 함수 44개), carry `commit` 단계 단정(`"\n\n**운반 경로(고정"` 1회, `"**1차 시도 기록("` 0회) 통과.

절 본문(파일과 같다 -- 인용 블록은 `git show e92e6b8:docs/02-design/disputes/20260930-b26-rail-accessor-set.md` 37줄 전부, 결정 줄은 `_drafts/user_decisions.md`의 `- [B26-1 dispute 처리(` 줄 그대로):

```
## dispute 기록

1차 시도(2026-10-07, base B1 `6df4bd7`, test 끝 T1 `c247a76`, code 끝 K1 `e92e6b8` -- 병합 안 함)에서 code-author가 K1에 dispute를 동봉했다(`Role: code` 커밋 `e92e6b8`, 경로 `docs/02-design/disputes/20260930-b26-rail-accessor-set.md`). 원문 그대로:

> ---
> id: 20260930-b26-rail-accessor-set
> …(dispute 파일 37줄 전부, 빈 줄은 `>`)…
> 결정은 사람이 한다. 이 결정 전까지 K1(1차 시도)에서 이 두 test는 실패로 남는다.

blob: 04ea6a2732fde2342f228c25e6444b7999b16309

결정(오케스트레이터 원칙 결정 -- `_drafts/user_decisions.md` '2026-10-07 B26-1 1차 시도 중 결정'의 줄 그대로):

> - [B26-1 dispute 처리(오케스트레이터 원칙 결정)] s015·s016 fixture에 topology 경로 없음 → 계약 12 '기존 test 입력 갱신'(판정 불변)으로 test-author가 tmp topology(supply_nets는 계약 12 다섯째 항목 규칙)를 더한다. 계약 4 뿌리 제외(card 개정)는 택하지 않음.

dispute '요청'의 첫째 방식(test 쪽 입력 갱신)을 택했다: … interface card는 그대로다. 기준 약화가 아니어서(판정·기대값 불변, 입력 추가) 승인 기록을 두지 않는다 -- 같은 모양의 선례: `20260929-probe-engine-dup` 2차 시도 dispute의 오케스트레이터 결정(`fb8ee35`). 순수 삽입이 아니어서 V5 발견이 나면(두 경로 밖 세 번째 경로) '승인 줄 배치' (6)대로 멈추고 사용자 승인을 따로 묻는다.

design 05 §12 '재시도'대로 이 절을 커밋한 뒤 세 worktree·브랜치를 정리하고 같은 id로 순서 1부터 다시 한다. 다시 하는 시도도 '두 번 시도 절차'의 1차 시도(병합 안 함)이고, 그 base B1은 이 절을 담은 gate `master`다. T가 바뀌므로 순서 3(`base_check.json`)과 K1 뒤 V3 측정은 새 T1·K1에서 다시 잰다. 중단된 시도의 산출물(T1·K1 diff, dispute 사본, 순서 3 출력)은 저장소 밖 `_drafts/b26_1_attempt1_r0/`에 보관한다(`SHA256SUMS`).
```

(위 `…`는 이 문서에서만 줄인 것 -- 커밋할 바이트는 절 파일이다.)

## 3. 순서 있는 명령 목록 (오케스트레이터, 메인 세션)

표기: `R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, `W=/c/Users/HSLEE/Documents/Todoc/fpga/wt`, `DR=$W/_drafts`, `ID=20260930-b26-rail-accessor-set`. **아래 실제 명령은 리터럴 경로로 친다** -- EL1은 변수가 든 리다이렉트 대상을 "해석하지 못함"으로 거부한다(이 분석 중 실측). push·worktree remove·branch -D는 **하나씩 단독 호출**(병렬·묶음·tail 금지, 전체 출력 확인, 거부면 전체 출력 보고 후 멈춤 -- 재시도 루프 금지).

### A. 진행 중 작업 마무리 (정리 전)
1. test-author(T1' 픽스처 커밋)가 끝날 때까지 기다린다(정리 중 역할 agent가 돌면 안 된다). 끝나면 `git -C $R for-each-ref --format='%(refname) %(objectname)' refs/heads/role/`로 세 끝을 적는다(test 끝이 `c247a76`이 아니면 T1'이 있다).

### B. 중단된 시도 보관 (저장소 밖, 커밋 없음 -- 정리 때 사라지는 것 먼저)
2. `mkdir -p /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/b26_1_attempt1_r0`
3. `git -C $R for-each-ref --format='%(refname) %(objectname)' refs/heads/role/ > …/b26_1_attempt1_r0/refs.txt`
4. `git -C $R diff --no-color --no-ext-diff 6df4bd7 c247a76 > …/b26_1_attempt1_r0/T1.diff` (+ `git -C $R log --format='%H %s%n%(trailers)' 6df4bd7..refs/heads/role/test/$ID > …/test_log.txt`)
5. (T1'이 있으면) `git -C $R diff --no-color --no-ext-diff c247a76 refs/heads/role/test/$ID > …/T1_fixture.diff` -- 다시 하는 test-author의 s015·s016 입력 출처
6. `git -C $R diff --no-color --no-ext-diff c247a76 e92e6b8 > …/K1.diff` (기존 `_drafts/b26_1_k1v0/K1v0.diff`와 대조 -- dispute 파일 hunk 유무 차이만 있어야 함), `git -C $R show e92e6b8:docs/02-design/disputes/$ID.md > …/dispute_K1.md`, `git -C $R show e92e6b8:skills/analog-gmid-design/assets/stick_diagram.py > …/K1_SD.py`, 같은 식으로 `sizing_recipe.py > K1_SR.py`, `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md > K1_registry.md`
7. `cp -r $W/$ID-audit/.ai/verification/$ID …/b26_1_attempt1_r0/audit_order3` (순서 3 `base_check.json`·`out/`·`scripts/` -- 참고 보관, 기록 4 target 출처 아님)
8. `find …/b26_1_attempt1_r0 -type f ! -name SHA256SUMS | LC_ALL=C sort | xargs sha256sum > …/b26_1_attempt1_r0/SHA256SUMS`
   * 이름은 `b26_1_attempt1/`(carry `ADIR`)과 달라야 한다 -- carry `archive`는 `test ! -e $ADIR`로 멈춘다.

### C. dispute blob 재확인 (커밋 직전)
9. `git -C $R rev-parse refs/heads/role/code/$ID:docs/02-design/disputes/$ID.md` → `04ea6a2732fde2342f228c25e6444b7999b16309`
10. code worktree 파일 해시: `/c/Python314/python.exe -B -c "import hashlib,sys;b=open(sys.argv[1],'rb').read();print(hashlib.sha1(b'blob %d\0'%len(b)+b).hexdigest())" $W/$ID-code/docs/02-design/disputes/$ID.md` → 같은 값. (오케스트레이터의 `git -C <code worktree> hash-object`는 EL1이 "역할 worktree 쓰기 git 명령"으로 거부한다 -- 이 분석 중 실측. 파일이 LF라 필터 없는 sha1 = git blob id. 값이 다르면 절의 `blob:` 줄에 두 값을 다 적는다 -- 가드는 worktree 파일·브랜치 끝 blob 둘 다 본다)

### D. 초안·card 개정·로컬 `Role: doc` 커밋 D
11. `cp $DR/draft_b26_1.spec.md $DR/draft_b26_1.spec.md.pre-dispute.bak`
12. 초안 갱신(파이썬 바이너리 쓰기 -- heredoc·`cat >>` 금지 규칙): `/c/Python314/python.exe -B -c "import sys;d=open(sys.argv[1],'rb').read();s=open(sys.argv[2],'rb').read();assert d.endswith(b'\n') and not d.endswith(b'\n\n') and s.startswith('## dispute 기록\n'.encode()) and b'## dispute' not in d;open(sys.argv[1],'wb').write(d+b'\n'+s)" <DR>/draft_b26_1.spec.md <DR>/b26_1_dispute_section.md`
13. `sha256sum <DR>/draft_b26_1.spec.md` → `0cc95c35701ba88080cde0a1c074ec7ee3f1a3cca912153126548e980302a6b2` (아니면 멈춤)
14. `cp <DR>/draft_b26_1.spec.md <R>/docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md`
15. 검증(오케스트레이터 전용 모래상자, 예 `/c/g447` -- 다른 agent와 겹치지 않는 고유 경로): `git -C $R show gate/master:tools/gates/role_paths.py > /c/g447/role_paths.py`, `… interface_card.py > /c/g447/interface_card.py` → `parse_spec_card` 절 13·approval 3줄, `interface_card.py <card> --root $R --out /c/g447/ifc.md` 후 `git -C $R show HEAD:docs/02-design/specs/$ID.interface.md | cmp - /c/g447/ifc.md` (끝나면 `/c/g447` 삭제)
16. `git -C $R add -- docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md`
17. `git -C $R diff --cached --numstat` → 정확히 한 줄 `52	0	docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md`
18. `git -C $R commit -m "docs: B26-1 spec card 20260930-b26-rail-accessor-set dispute 기록(1차 시도 K1 e92e6b8 동봉 dispute blob 04ea6a27 -- SR selftest s015·s016 ctx에 topology_path 없음, 결정: 계약 12 기존 test 입력 갱신(오케스트레이터 원칙 결정), §12 재시도로 같은 id 순서 1부터)" --trailer "Role: doc" --trailer "Change-Id: 20260930-b26-rail-accessor-set" --trailer "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"`
19. `git -C $R show HEAD:docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md | cmp - <DR>/draft_b26_1.spec.md` 그리고 `git -C $R rev-parse HEAD^` = `6df4bd7fd9920e752da4b16bff9b0513caf78362`

### E. 정리 (§12 재시도 형태 -- 하나씩 단독 호출, D 커밋 뒤에만 EL1이 code 쪽을 통과시킨다)
20. `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree remove --force /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-test`
21. `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree remove --force /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-code`
22. `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree remove --force /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-audit`
23. `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills branch -D role/test/20260930-b26-rail-accessor-set`
24. `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills branch -D role/code/20260930-b26-rail-accessor-set`
25. `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills branch -D role/audit/20260930-b26-rail-accessor-set`
26. 확인: `git -C $R for-each-ref refs/heads/role/` 0줄, `git -C $R worktree list`에 `$ID-` 없음, `$W/$ID-{test,code,audit}` 경로 없음.
   * `--force`: audit worktree에 미커밋 `.ai/verification/$ID/`가 있다(§12 정리 행이 허용한 재시도 정리). 가드는 `branch -D role/code/…`에서도 같은 판정(`_judge_branch` → `_dispute_guard`)을 한다.

### F. push (정리 뒤에만 -- 역할 브랜치 0이어야 `_judge_push` 통과)
27. 단독: `env APPDATA='C:\Users\HSLEE\AppData\Roaming' LOCALAPPDATA='C:\Users\HSLEE\AppData\Local' git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills push gate master:master` (launch_common `lc_push_cmd` 모양. 역할 커밋 없는 push라 §9.2-3·4: `Role: doc` 비병합 커밋 하나, 경로 = spec card)
28. `git -C $R fetch gate` → `git -C $R rev-parse HEAD gate/master` 같은 값 = **D = 새 B1**
29. `bash $DR/b26_1_launch.sh after-push-dispute` (4절 K-L1의 새 단계 -- launch 상태 `B1`을 D로, `CACHE`를 새 캐시로)
30. `_drafts/user_decisions.md`에 D 해시·push 확인 한 줄(파이썬 바이너리 append, 뒤에 `wc -c` 증가·앞부분 불변 확인)

### G. 1차 시도 다시 (같은 id, base B1 = D)
31. 단독: `git -C /c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills worktree add /c/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-b26-rail-accessor-set-test -b role/test/20260930-b26-rail-accessor-set gate/master`
32. test-author(갱신 브리프, 4절 K-B) → T1. 순서 3: `git -C $R worktree add $W/$ID-audit -b role/audit/$ID role/test/$ID` → auditor **순서 3 다시**(base = D, 캐시 = `gmid-gate-cache/<D>`) → 순서 4 `git -C $R worktree add $W/$ID-code -b role/code/$ID role/test/$ID` → code-author(r0 `K1.diff`에서 dispute 파일 뺀 변경을 show→Edit) → K1 → auditor V3(`--base D --head K1`) → `bash $DR/b26_1_carry.sh prep` …(carry 그대로).

## 4. kit 수정 목록

| id | 파일 | 수정 | 이유 |
|---|---|---|---|
| K-C1 | `b26_1_carry.sh` 96행 `NSEC=12` + `stage_commit`의 `int(sys.argv[7])` | 상수 삭제 → 기대 절 수 = `$td/card.head.md`(= HEAD = B1 card)를 `parse_spec_card`로 센 값(carry 개정은 절을 더하지 않는다). 최소 수정이면 `NSEC=13`(주석: '## dispute 기록' 절, §12 재시도 D) | D 뒤 card 절 13 -- 지금 값이면 `stage_commit` 단정 `got == exp`가 멈춘다. 상수를 박지 않고 근거(B1 card)에서 센다 |
| K-L1 | `b26_1_launch.sh` 새 단계 `after-push-dispute` | `B0=$(st_get B1)`; `test "$B0" = "$(st_get S)"`(한 번만); `g fetch gate`; `H=gate/master`; `HEAD = H`; `H^ = B0`, `rev-list --count B0..H = 1`; `refs/heads/role/` 0줄; `diff-tree --name-only H` = `$F_SPEC` 하나; numstat 삭제 0; `trailer_is H Role doc`·`Change-Id $ID`; `g show H:$F_SPEC \| cmp - $DRAFT_SPEC`; `parse_spec_card` 절 수 = 13·approval = `$APPR_IDS`; 절 정규식 안에 r0 dispute blob(`04ea6a27…`); `interface_card.py` 재생성 = `H:$F_IFC` 바이트; `plan_hash` = `PLAN_HASH`; 그다음 `st_set B1_R0 $B0; st_set CACHE $(cache_dir); st_set B1 $H` + 순서 1 명령 출력. case에 `after-push-dispute) stage_after_push_dispute ;;` | carry의 B1 단일 출처가 launch 상태 `B1=`(carry 8행). carry `check`는 `gate/master = HEAD = B1`을 단정(167~172행) -- 6df4bd7 그대로면 D 뒤 멈춘다. 상태 파일 손 편집 대신 확인을 거친 단계로 옮긴다 |
| K-L2 | `b26_1_launch.sh` `NSEC=12`(80행)·`stage_card`·`stage_final` | 바꾸지 않는다(이미 끝난 S 커밋용. `stage_card`는 `test ! -e $F_SPEC`로 다시 못 돈다). 머리 주석에 "S 뒤 dispute 기록 D는 after-push-dispute" 한 줄 | 혼동 방지만 |
| K-D1 | `draft_b26_1.spec.md` | 3절 12~13(+`.pre-dispute.bak`) | 커밋 card = 초안 바이트(launch 규약) |
| K-B | `b26_1_briefs.md` | ① B1 `6df4bd7…`를 D로(3·4·33·85·147·159·169·170·205·222·267·353·383행 -- 특히 169·170·205의 게이트 캐시 경로 `gmid-gate-cache/6df4bd7f…`: 캐시는 gate master 하나만 두므로(WP-10) push 뒤 옛 디렉터리는 없어진다, V1 `-c` 캐시 old도 D) ② 1.2에 항목 추가: "SR selftest `s015_state` ctx에 `topology_path=`(tmp topology, `supply_nets`는 계약 12 다섯째 항목 규칙) -- card '## dispute 기록', 두 test 판정·기대값 그대로, 기존 줄을 바꾸지 않는 삽입으로(V5 경계)" + 출처 `_drafts/b26_1_attempt1_r0/T1.diff`(+`T1_fixture.diff`)의 `+` 줄을 Write/Edit(`git apply` 금지) ③ 3절 code-author: 출처 `b26_1_attempt1_r0/K1.diff`·`K1_SD.py`·`K1_SR.py`·`K1_registry.md`(show→Edit), dispute 파일은 만들지 않는다(s015·s016 green이면) ④ 2절 auditor: 산출물 이름 그대로(`attempt1_*` -- 새 audit worktree라 겹침 없음), r0 `audit_order3`은 판정 근거로 쓰지 않음 ⑤ 5절 순서 요약에 r0 중단·D·정리·push 줄 | 다시 하는 1차 시도 입력 |
| K-S | `b26_1_kit_selftest/*` | 바꾸지 않는다(자체 모래상자 상태 사용, `NSEC`·B1 의존 없음 -- grep 실측). `fixtures/v5_t1_c247a76.json`은 r0 T1의 V5 실측 사례 입력이라 그대로 유효(새 T1 대조는 carry check가 실제 값으로 한다) | -- |
| K-U | `user_decisions.md` | 3절 30 | 기록 |

carry의 나머지는 그대로 맞다: `check`의 `dispute_guard`(새 K1에 dispute 없으면 "없음"), `ADIR=_drafts/b26_1_attempt1/`(r0 보관과 다른 이름), `commit`의 앵커 단정(절 문안이 두 문자열을 피함 -- 검증함), interface card 바이트 대조(D가 바꾸지 않음 -- 검증함), 기록 4 `diff_base` = `st B1` = D(B1..T1의 V5 두 경로 blob은 D가 건드리지 않는다).

## 5. 열린 점 (오케스트레이터 판단)

1. dispute 원문은 "결정은 사람이 한다"고 썼다. 지금 결정은 `user_decisions.md`의 **오케스트레이터 원칙 결정**이다(선례 `fb8ee35`도 오케스트레이터 결정을 card에 적고 승인 기록 없이 진행). 판정·기대값 불변이라 기준 변경은 아니지만, 사용자 확인을 원하면 D 커밋 전에 묻고 `target_kind: decision` 기록으로 받는다(§12 재시도 행 "사용자 결정은 … decision 승인 기록으로") -- 그 경우 절의 '결정' 문단과 card 머리 `approval` 줄이 바뀌고 interface card는 그대로다.
2. s015·s016 픽스처 변경이 V5 발견을 내면(기존 fixture 함수 시그니처·`SizingContext(...)` 호출 줄 수정은 순수 삽입이 아닐 수 있다) 새 순서 3 `base_check.json`의 `diff_paths`가 세 경로가 되어 carry check가 멈춘다 -- card '승인 줄 배치' (6)대로 사용자 승인을 묻는 경로. 브리프에 "새 줄 삽입으로만"을 적어 위험을 줄인다.
3. 진행 중인 T1' 커밋은 r0 보관(`T1_fixture.diff`)으로만 남는다. 다시 하는 test-author가 같은 내용을 Write/Edit로 다시 쓴다.
