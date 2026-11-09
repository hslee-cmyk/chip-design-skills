---
id: 20260930-v3-history-clone
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v3-history-clone
---
## 의도

백로그 B28(P8 1차 auditor 실측, 사용자 지시 2026-09-30 "1부터 4까지 다 개선해"): 게이트 V3 도구 `tools/gates/mutate_changed.py`가 root 작업 트리를 `.git` 없이
`%TEMP%`에 복사해(`shutil.copytree(root, work, ignore=shutil.ignore_patterns(".git"))`) 그 안에서 test를 돌린다. git 이력을 읽는 test(`contracts/test_ts6_probe_relocate.py`의
`test_base_blob_reader_reads_the_base_tree`·`test_moved_tool_matches_base_except_path_lines`)가 기준 실행에서 실패하고, 도구는 기준 실행이 실패한 인벤토리의 변이를
실행 없이 '생존'으로 센다 -- P8에서 변이 2060개가 실행 0으로 전부 '생존', DF-36 1차에서 26개 전부 '기준 실행 실패, 생존'(두 번 모두 auditor가 `.git` 있는 복제본에서
같은 도구 함수로 대체 측정했다). 판정 도구가 환경 때문에 판정을 못 하면서 그 사실을 드러내지 않는 결함이다.

고칠 방향(사전 조사 비교 뒤 (c)):
1. 사본을 **이력이 있는 격리 복제본**으로 만든다 -- design 05 §12-7과 같은 형태(`git clone --no-hardlinks --no-local -c core.longpaths=true <root>`, `remote remove origin`),
   체크아웃 대상은 `--head` 커밋(지금은 root 작업 트리를 복사하면서 호출 그래프는 `--head` 트리에서 만든다 -- 이 암묵 전제도 없앤다).
2. 기준 실행이 실패한 인벤토리가 하나라도 있으면 도구 판정은 `ERROR`(exit 2, design 05 §17의 V3~V7 '실행 오류')이고 실패한 인벤토리를 출력에 담는다 -- 그 변이를 '생존'으로
   세지 않는다. 복제본 생성 실패도 exit 2 `ERROR`다(traceback·exit 1이 아니다). 광범위 `except`는 쓰지 않는다(공격 27f).
3. 임시 복제본을 남기지 않는다(읽기 전용 pack 파일 때문에 `rmtree(ignore_errors=True)`가 조용히 남긴다 -- 사전 실측 33MB).
판정 기준을 약화하지 않는다(기준 실행 실패는 지금 FAIL, 이후 ERROR -- 둘 다 거부이고 원인이 드러난다. auditor는 도구 exit 2를 FAIL로 적는다). 비용: clone 약 6.5초·54MB,
현재 copytree 8.9초·231MB(사전 실측). 설치 사본이 없어 재설치 불필요(`mutate_changed.py`는 §4.4 캐시에서 실행, 설치 사본은 pre-receive·gate-runner.py뿐) --
새 도구는 이 변경이 반영된 뒤의 base 캐시부터 쓰인다.

## 관찰 가능한 계약

1. 도구가 test를 실행하는 사본은 git 저장소이고 `origin` 원격이 없으며, 그 안에서 test가 `--head`의 조상 커밋 blob을 읽을 수 있다(`git show HEAD~1:<경로>`가 base 내용을
   돌려준다). 사본의 `HEAD`는 `--head` 커밋이다 -- 합성 저장소에서는 root 작업 트리가 head 트리와 같아 redteam으로 구별되지 않으므로, 이 부분은 auditor가 병합본 코드와
   실측(root 작업 트리에 미커밋 변경을 둔 복제본에서 사본 `rev-parse HEAD`)으로 확인한다.
2. 도구 실행 전후로 root 저장소의 refs·작업 트리 상태·worktree 목록이 같다(사본 생성이 root를 바꾸지 않는다).
3. 기준 실행에서 실패한 인벤토리가 하나라도 있으면 출력 JSON `verdict`가 `ERROR`, exit 2이고, 실패한 인벤토리(test id)를 출력에 담는다. 그 인벤토리의 변이는 `survived`에
   들어가지 않는다. 인벤토리 없음 → `survived`는 그대로다(도달하는 test가 없는 변이는 판정 불가가 아니라 생존).
4. 복제본 생성이 실패하면 exit 2 `ERROR`(JSON 한 줄)이고 traceback·exit 1이 아니다.
5. 도구가 끝난 뒤(PASS·FAIL·ERROR 모두) 도구가 만든 임시 디렉터리가 남지 않는다.
6. 무동작: 기존 redteam V3 케이스(`tools/gates/redteam/v3_survivor/` attack exit 1·control exit 0, `attacks/28-v3-gmid-options/` 단계 전부)와 공격 26·27f의 결과가 바뀌지 않는다.
7. 새 redteam 케이스 `attacks/31-v3-git-history/`: (a) `git-history-kill` -- 인벤토리 test가 `git show HEAD~1:<경로>`로 base blob을 읽고 내용까지 단언하는 합성 저장소에서
   변이가 실제로 실행되고 죽는다(exit 0; base 도구 exit 1 -- red), 같은 test가 `git remote` 출력이 빈 것을 단언한다(계약 1의 origin 없음) (b) `baseline-fail-error` -- 항상
   실패하는 test가 인벤토리에 있으면 exit 2와 `"verdict": "ERROR"`(base 도구 exit 1 -- red).
8. 문서: design 05 §10 V3 행 ④(317행 "변이마다 임시 복사본에서 그 test만")를 "변이마다 `--head` 커밋의 격리 복제본(이력 포함, origin 없음)에서 그 test만, 인벤토리 기준
   실행이 실패하면 `ERROR`"로 고친다(이 card의 문서 커밋). `mutate_changed.py` 모듈 docstring ④도 같은 뜻으로(code-author).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 7의 두 단계가 base 도구에서 exit 1(기준 실행 실패를 '생존'으로)이라 red, 병합본 도구에서 green(사전 실측: 시제품에서 (a) exit 0 5/5 killed, (b) exit 2).
design 05 §18: ⑤ 뒤 게이트 변경은 spec card(red-green).

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py`의 `build_vrepo`·`a_vcase` -- base 커밋 → (interface card) → head 커밋의 실제 이력, root HEAD = `--head`, HEAD~1 = base)에
조상 blob을 읽는 test·항상 실패하는 test를 둔다 -- 기대 exit·verdict는 이 card 계약 문장. ERROR 기대 표기는 `"expect": {"exit": 2, "message_contains": ["\"verdict\": \"ERROR\""]}`.

## 거부해야 할 입력

항상 실패하는 test가 인벤토리에 있는 합성 저장소 → exit 2 `ERROR`(조용한 '생존' 아님). 기존 `v3_survivor` attack → exit 1 그대로.

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

기존 redteam 전체(`run_all.py --phase 0.5 --mode direct`)와 `--cases 0.5`의 케이스 판정이 base와 같다(계약 7의 새 케이스 제외).

## 재현할 수치

없음.

## 결정 필요 항목

없음(사용자 지시 "1부터 4까지 다 개선해", 게이트 변경 승인 기록 `20260930-v3-history-clone`).

## 작성 전 실측

(사전 조사 `prep_b28.md`·`prep_b28_redteam.md`, base 070cf69)
1. 사실: `grep -n "copytree\|survived\|rmtree\|-x" tools/gates/mutate_changed.py` → 285행 copytree(`.git` 제외, root 작업 트리), 312행 인벤토리 실행 명령(`-x`),
   328-331행 인벤토리별 기준 실행, 339행 인벤토리 없음 → `survived`, 340-342행 기준 실행 실패 → `survived`, 359행 좁은 except 튜플(→ ERROR exit 2), 364행
   `rmtree(tmp, ignore_errors=True)`. ts6 두 test: clone 사본 2 passed, copytree 사본 2 failed. 합성 저장소 base 도구 두 단계 모두 exit 1, 시제품 exit 0 / exit 2.
   clone 실패를 `check=True`로 두면 `CalledProcessError`가 359행 튜플 밖이라 exit 1 -- 계약 4.
2. 이름 충돌: `tools/gates/redteam/attacks/31-*` 없음(`ls attacks/`: 마지막 30-rejudge-cache). `--only v3`가 attacks의 v3 케이스를 잡는지는 test-author가 확인.
3. 원칙: 판정 불가를 드러냄(조용한 생존 금지) -- 계약 3·4, 임시 파일 누수 없음 -- 계약 5.
4. 쓰기 경로: `tools/gates/mutate_changed.py` = code-author(게이트 변경), redteam 케이스 = test-author(`tools/gates/redteam/`), design 05 문구 = 오케스트레이터 문서 커밋.
5. 계획서 소비자: 바꾸는 이름 없음. 호출처 = redteam iface·공격 26·27f·auditor 스크립트(merge_gate·gate/*·hooks는 부르지 않는다), 미커밋 파일에 기대는 호출 없음.
6. 미배선: 새 def를 만들면 `main`이 부른다.
7. 기존 test: redteam `v3_survivor`·공격 26·27f·28 -- 계약 6으로 불변 판정.
