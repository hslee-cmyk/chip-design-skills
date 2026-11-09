# V3 면제 묶기 card `20260930-v3-exempt-binding` -- 착수 키트(세 역할 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` `a796468`(P10b spec card 커밋), **재측정 `0f23786`**(P10b 재시도 개정 -- `a796468..0f23786`은 승인 기록 `20261001-p10b-v3-equiv` 추가와 P10b spec card 개정뿐,
`tools/`·엔진 차이 0; 격리 복제본 `C:/g119`), **재측정 `19eb475`**(P10b 3차 병합·판정 + 문서 커밋 7개 + 승인 기록 3개 뒤, 격리 복제본 `C:/g158` -- 0.1b·0.5·0.6). 저장소 쓰기·상태 변경 git 없음.
모의는 격리 복제본 `C:/g102`·`C:/g158`(origin 제거, 끝나고 삭제)에서만.
**착수 실행은 `_drafts/v3_binding_launch.sh`**(0.5) -- 아래 0단계 명령·판단과 커밋 계획 §4.0·§4.1 A~C를 그대로 담았다.

**착수 0단계(반드시, 다른 단계 전에)**: 승인 기록 집계는 gate `master`에 기록이 더해질 때마다 바뀐다(P10b 판정·`20261001-b47-md-sync` 등이 착수 전에 더 들어온다). 그래서 이 키트와 spec card는 수치를
'measured at <sha>'로만 적었다 -- 착수 때 다음을 다시 돌리고 출력으로 판단한다(읽기 전용):
```
C:/Python314/python.exe -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/v3_scripts/v3_decision_census.py --repo <R> --rev "$(git -C <R> rev-parse gate/master)" --out <scratch>/census.txt
git -C <R> diff --name-only 0f23786 gate/master -- tools/ skills/analog-gmid-design/assets/stick_diagram.py
```
판단(spec card '작성 전 실측' 1 셋째 항목 끝): (가) V3 대상 영역 V3 모양 원소가 `20260922-ic3-v3-exempt` 14개뿐, (나) `@` 접미사 원소 0, (다) 둘째 명령 출력 비어 있음(도구 줄 번호·해시 앵커 그대로).
셋 다 맞으면 spec card의 measured 문장(rev·수치)과 승인 기록 '덮는 것' 첫 항목 수치만 새 출력으로 바꾸고 진행. (가)(나)가 깨지면 spec card 이행 근거를, (다)가 깨지면 0.1 표 전체를 다시 잰다.
측정 `0f23786`: decision 13, 원소 36, V3 모양 23 = 대상 영역 14 + 밖 9(`20261001-p10b-v3-equiv`), `@` 0 -- `v3_scripts/out/v3_decision_census_0f23786.txt`.
**측정 `19eb475`**: decision **15**, 원소 **38**, V3 모양 23 = 대상 영역 14 + 밖 9, `@` 0 -- (가)(나)(다) 성립. 새 decision 기록 2개(`20261001-b47-md-sync` = `B47-MD-SYNC`,
`20261001-b26-backfill-interdig-fix` = `U-BF-BACKFILL-INTERDIG`)는 결정 id라 V3 모양이 아니다. `20261001-p2dod-e2-wording`은 diff. reg_check 9원소는 P10b 병합 뒤 4 qualname 모두 해시가 잡힌다
(`7e3615bc`·`10ddb443`·`b3c9b826`·`279df768` -- 1차 병합본 값과 같음, 여전히 `_is_source` 밖). spec card measured 문장·승인 기록 '덮는 것' 첫 항목을 이 수치로 바꿨다(직전판 `*.pre-19eb475.md`).
**`5f643a9`**(이 작업 중 gate `master`가 md 일치 card `20261001-topology-md-sync` test·판정으로 움직임 -- `19eb475..5f643a9` = `tests/contracts/test_topology_md_sync.py`·판정 기록 2개뿐)에서도
집계 출력이 rev 줄 말고 바이트 동일(0.5 둘째 모의).
대상 산출물: `draft_v3_exempt_binding.spec.md`(재검증 반영판, 직전판 `.spec.v3.md`), `approval_20260930-v3-exempt-binding.md`(사용자 원문 채움, 직전판 `.v3.md`),
`v3_cards_commit_plan.md` §4.1(명령 시퀀스), `patch_v3_binding_docs.py`, `fill_v3_approval.py`.

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(HEAD `a796468`)

| 확인 | 결과 | 조치 |
|---|---|---|
| `tools/` 변경(측정 기준 `7535799` → `a796468`) | `git diff --quiet 7535799 a796468 -- tools/` 차이 0 | 도구 사실 문장 그대로 |
| `mutate_changed.py` 줄 번호 | `_approved` 218·219, `approved = …` 320, `if mid in approved` 375~377, `--out` append 394~396, 출력 `print` **407~408**(초안 406~408) | 407~408로 고침 |
| `reachability._approved_ids` | 180행, 소비처 `mutate_changed` 219·`reachability.main` 233·`test_lint` 731 그대로 | -- |
| `merge_gate` | `parse_approval_header` 190, `APPROVAL_KEYS` 178(8개), decision `target` 원소 비지 않음만 검사, `plan_tables_object` 158~168, N4.2 읽기 **123~133**(초안 124~133), V3 호출 0건 | 123~133으로 고침 |
| `engine_dup_scan.py` 102~122 | 같음(정정 2026-10-01: 함수 `_read_exemptions` 실제 101~123 -- 0.1b) | -- |
| redteam `lib/rt.py` | `subst_str` 39~48(정규식 47), `_commit_case` `base_files` 446·`approval`/`more_approvals` 459, `build_vrepo` 523~, `a_vcase` 580~, `observe == "v4_first"` 613, `tool_tmpdir`·`root_state` 관찰 616~621 | 그대로 |
| redteam 번호 | `attacks/` 마지막 `31-v3-git-history`, 32~35 없음 → **34 사용 가능** | -- |
| 새 이름 충돌 | `exempt_ignored`·`survivor_bindings`·`bind_hash`·`@bindhash`·`out_jsonl` -- `tools/`·`docs/` 0건 | -- |
| decision 승인 기록 집계 | `a796468`: 12개·원소 27개(`2d58fd8`이 `20260930-b26-before-phase3` 추가, 결정 id 8), V3 모양 14. **measured at `0f23786`: 13·36·V3 모양 23(대상 영역 14 + 밖 9 = `20261001-p10b-v3-equiv` `reg_check:…`)** -- 수치는 착수 0단계 명령으로 다시 잰다 | spec card 수치를 고정값 대신 'measured at + 명령'으로 바꿈, 대상 영역 밖 원소 문장 추가 |
| `20261001-p10b-v3-equiv`(reg_check id 9개)와 묶기 규칙 | 파일 `skills/analog-gmid-design/assets/tests/tools/reg_check.py`는 `reachability._is_source` 밖 -- `mutate_changed.py` 315행 `targets` 필터로 도구가 이 id를 **만들지 않는다**. 그래서 계약 3 셋째 문장으로 `exempt_ignored`에 실리지 않고 적용도 안 된다(지금도 도구가 적용한 적 없음 -- auditor 보충 뮤테이션 면제). 묶기 해시는 정의상 계산 가능(basename `reg_check` 경로 하나): `0f23786`에서는 `_df23_expected`·`check_df23`·`_df23_rows_under` def 없음(P10b 미병합), `main`만 `79554e7e…`; P10b 1차 병합본 `4294048`·`role/*/20260930-df23-registry-record`에서 `7e3615bc…`·`10ddb443…`·`b3c9b826…`·`279df768…`. 재시도가 파일을 다시 고치므로 뜻 있는 해시는 P10b 최종 병합본 것뿐 | spec card 용어·의도·범위 밖 절에 문장, 백로그 7, 승인 기록 '덮지 않는 것'에 한 줄. 도구 계약·test 변경 없음(3.3 p2에 probe 한 줄) |
| `tools/` 변경 `a796468` → `0f23786` | `git diff --name-only a796468 0f23786` = `.ai/approvals/20261001-p10b-v3-equiv.md`, `docs/02-design/specs/20260930-df23-registry-record.spec.md` | 도구 문장·줄 번호·해시 앵커 그대로 |
| 해시 앵커 표 | `b7765b0`은 gate `master`의 조상이 **아니다**(P9 1차 병합, 버려짐). 실제 P9 병합 `93b18db`·HEAD `a796468`에서 `load_topology` ① `c22bdd32`/묶기 `7e81d370`, `save_instance_json` ① `11a55c19`/묶기 `4a96ecf0` -- 표 값 그대로 | 열 머리를 `93b18db(P9 병합)·a796468`으로 |
| 인용 커밋 조상 확인 | `7535799 58e954c 6fe9cff 070cf69 b29be01 cd64170 148bd6d c31e0b6 f1c4b7d d99919c ab90ec5 2d58fd8 fe638ab` 전부 조상 | -- |
| 판정 유형 근거 | 하네스는 (b)(d)(e)(f)도 base에서 **단계 FAIL**로 판정한다(base 출력에 `exempt_ignored` 조각 없음) | 한 문단 추가: red 집합 = 6단계, exit가 다른 단계 = (a)(c) |
| 문서 패치 대상 줄 | design 05 317, design 10 382, 계획 839 그대로(`--check` pending 3) | -- |
| `plan_tables_hash` | `7167e028…6d2596d`, 패치 전후 같음 | `plan_tables` 승인 불필요 |

### 0.1b 재검증(HEAD `19eb475`, 격리 복제본 `C:/g158/src` -- 줄 번호는 `git show 19eb475:<경로> | sed -n` 로 전부 다시 읽음)

| 확인 | 결과 | 조치 |
|---|---|---|
| `tools/` 변경 `0f23786` → `19eb475` | `git diff 0f23786 19eb475 -- tools/` 비어 있음. P10b는 `skills/analog-gmid-design/assets/tests/tools/reg_check.py`(+ `tests/contracts/test_reg_check_df23.py`·레지스트리)만 바꿈 -- `tools/` 아님 | 도구 사실 문장 그대로 |
| `stick_diagram.py`·`engine_dup_scan.py`·계획서·design 05·design 10·`agents/` | 차이 0 | 해시 앵커·문서 패치 대상 줄(317·382·839) 그대로, `patch_v3_binding_docs.py --check` pending 3·`plan_tables_hash` `7167e028…6d2596d` 불변 |
| `mutate_changed.py` | `_approved` 218·219, `targets` 필터 315, `approved = …` 320, `if mid in approved` 375~377, `--out` 394~396, 출력 407~408 | 같음 |
| `reachability.py`·`test_lint.py` | `_approved_ids` 180, `main` 233, `test_lint` 731(`git grep _approved_ids` 소비처 3곳 그대로) | 같음 |
| `merge_gate.py` | N4.2 읽기 123~133, `plan_tables_object` 158~168, `APPROVAL_KEYS` 178, `parse_approval_header` 190 | 같음 |
| `engine_dup_scan.py` | `_read_exemptions` **101~123**(카드·0.1의 '102~122'는 한 줄씩 어긋난 인용 -- `0f23786`에서도 101~123) | spec card 인용 고침 |
| redteam `lib/rt.py`·`attacks/` | 39~48·446·459·523·580·613·616~621 그대로, 마지막 `31-v3-git-history` | 같음 |
| 새 이름 충돌 | `exempt_ignored`·`survivor_bindings`·`bind_hash`·`@bindhash`·`out_jsonl` -- `tools/`·`docs/` 0건 | -- |
| 계획서 소비자 `git grep "변이 id" -- docs/01-plan docs/02-design` | 이전 3곳(design 05 317·design 10 382·P9 card 118·168) + 새 줄: history 336·392, P10b card 78·154, md 일치 card 153 -- 모두 이력·병합된 card·결정 id 설명(규칙 문장 아님) | spec card '작성 전 실측' 5에 한 문단, 고칠 문서 추가 없음 |
| `role/*` | `19eb475` 당시 `role/{audit,test}/20261001-topology-md-sync`(md 일치 card 진행) -- 이 작업 중 정리돼 `5f643a9`에서 0개 | 착수 조건은 Phase 2 DoD 뒤(0.4 1) |

(참고: 커밋 계획 §6의 계획서 정규화 sha256 '앞 `78ad5194…`'는 `2d58fd8` 값이다. `8356c1e`가 계획서를 고쳐 지금은 `8773163b…`. 패치 스크립트는 문자열 앵커로 판정하므로 영향 없음.)

### 0.2 승인 기록 초안

'사용자 원문'에 `_drafts/user_decisions.md` '2026-10-01 A1 (AskUserQuestion 답)' A1-a 항목을 그대로 인용하고, AskUserQuestion 질문 문안이 그 기록과 `draft_v3_decision_question.md` '함께 드리는 승인 요청'에
남아 있음을 적었다. 인용이 원문과 바이트 단위로 같은지 확인함(True). 기존 질문 요약 문단은 그대로 뒀다.
주의: `user_decisions.md`에 남은 것은 답(선택지 이름)과 질문 **요지**다 -- 질문 본문 전문은 `draft_v3_decision_question.md`에 있다.

### 0.3 모의 결과(`C:/g102/repo` = gate `master` `a796468` 복제, `C:/g102/sim.sh`)

| 단계 | 결과 |
|---|---|
| A 문서 패치 | `--check` pending 3·`plan_tables_hash` 불변 → 적용 `applied` → `git diff --numstat` 파일 3개 각 `1 1` → `Role: doc` 커밋 → 재실행 `already-applied` |
| B spec+interface card | 초안 복사 + `interface_card.py` exit 0(기존 함수 0개, 두 표 빈 13줄 -- 게이트 card 선례 모양). `parse_spec_card` 통과: phase 0.5, red-green, gate_change yes, approval = 자기 id. 절대 경로 호출(`--root`·`--out` 절대)도 바이트 동일 |
| C 승인 기록 | `fill_v3_approval.py --check` ok → 작성 `written` → 재실행 `already-present`. blob LF·BOM 없음·HTML 주석 없음. `diff_path` 5개 |
| 게이트 확인 | `gate_change_ok(HEAD)` **True**, 승인 커밋 전(`HEAD~1`) False. `weakening_diff.diff_hash` == `merge_gate.compute_diff_hash` == 기록 `target`. `approved_hashes(HEAD)`에 target 있음. `_approved_ids` 27 그대로(`a796468` 모의 당시 -- `0f23786`에서는 36. 판단 기준은 '승인 커밋 전후 같음'이지 수치가 아니다. diff 기록은 V3 원소에 안 들어감) |
| EL4 모의 | 베어 사본 `C:/g102/gate.git`에 `merge_gate.py receive --old a796468 --new <C 커밋>` → exit 0. 대조: 트레일러 없는 커밋 → exit 1 `[EL4 거부] … Role … 정확히 하나가 아니다`(게이트가 실제로 거부함 확인) |

(모의 해시 `target 698550f2…`는 모의 커밋 id에 묶인 예시다 -- 실제 값은 실제 커밋으로 다시 계산된다.)

### 0.4 착수 직전에 다시 볼 것

0. **착수 0단계 명령**(이 문서 머리)을 먼저 다시 돌린다 -- 집계 수치는 고정값이 아니다.
1. **지금 `role/*` 브랜치 3개가 있다**(`role/{audit,code,test}/20260930-df23-registry-record`, P10b 진행 중 -- `0f23786` 시점 재확인 그대로). design 05 §12 "역할 브랜치가 있는 동안 문서 커밋의 gate push는 EL1이 거부" -- P10b 병합·정리와 Phase 2 DoD가 끝난 뒤 착수(커밋 계획 §4.0의 `test -z "$(git branch --list 'role/*')"`).
2. 착수 시 HEAD가 `0f23786`이 아니면 0단계 명령 출력, `patch_v3_binding_docs.py --check`(pending 3·해시 불변)와 위 0.1 줄 번호 표를 다시 본다(도구가 바뀌었으면 spec card 재측정).
3. 커밋 계획 §4.1의 `(cd "$R" && $PY tools/gates/interface_card.py … --out <상대 경로>)`는 이 세션의 PreToolUse hook(`role_guard.py`)이 "`cd` 뒤 상대 경로 쓰기 대상"으로 거부할 수 있다(이번 작업에서 같은 형태의 `cp`가 거부됨).
   **절대 경로 형태로 쓴다**(바이트 동일 확인):
   `C:/Python314/python.exe -B <R>/tools/gates/interface_card.py <R>/docs/02-design/specs/20260930-v3-exempt-binding.spec.md --root <R> --out <R>/docs/02-design/specs/20260930-v3-exempt-binding.interface.md`.
   같은 hook은 셸 변수·명령 치환이 든 `rm` 대상도 거부한다 -- 정리 명령은 리터럴 경로로.
4. 모의 커밋은 `--trailer "Role: doc"`만 썼다(문서 커밋 선례). §12 순서 2·5의 역할 커밋은 `--trailer "Role: …" --trailer "Change-Id: 20260930-v3-exempt-binding"`.

### 0.5 착수 스크립트 `_drafts/v3_binding_launch.sh`와 모의(`C:/g158`, 끝나고 삭제)

단계: `pre`(착수 전 확인 + 0단계 집계) → `doc`(A) → `card`(B) → `appr`(C) → `final`(push 전 종합) / `local` = 다섯 단계 연속 / `after-push`. push는 하지 않는다(단독 호출 -- `final`이 명령을 출력).
* `pre`: `user.email`, `fetch gate`, master·HEAD == gate master, `refs/heads/role/` 0개, `$ID-` worktree 없음, index·`docs/`·`.ai/approvals/` 깨끗, spec·interface·승인 기록 아직 없음, 초안 `<rev-parse>` 3·`diff_path` 5.
  **0단계 집계**: 승인 초안 '덮는 것' 첫 항목의 `measured at gate master <rev>` 문장에서 rev·수치를 읽어(단일 출처) `v3_decision_census.py`를 그 rev와 gate master에서 돌리고, **rev 줄 말고 출력이 바이트 동일**해야
  한다(수치만이 아니라 원소·경로·묶기 해시 앞 16자). 수치가 초안·spec card measured 문장과 같고 (가) 대상 영역 원소 = `20260922-ic3-v3-exempt`의 `stick_diagram:` 원소뿐 (나) `@` 0 (다) 밖 원소는 `_is_source` 밖 경로 하나뿐.
  이어서 measured rev → HEAD 사이 `tools/`·`stick_diagram.py`·`engine_dup_scan.py`·계획서·design 05·design 10 차이 0, `patch_v3_binding_docs.py --check` = pending + `plan_tables_hash` 불변, 게이트 캐시(gate master 전체 sha) 준비, `_approved_ids` 기록.
* `doc`: 패치 적용(`applied` → 재실행 `already-applied`), 3파일 각 numstat `1 1`, `plan_tables_hash` 불변, `Role: doc` 커밋.
* `card`: 초안 복사 → **캐시 판** `role_paths.parse_spec_card`(0.5·red-green·yes·approval = 자기 id, phase ∈ phase_order) → **캐시 판** `interface_card.py`(절대 경로 `--root`·`--out`) → 기호 행 0 → `Role: doc` 커밋.
* `appr`: `fill_v3_approval.py --base <gate base> --head <B>` → `written`, target을 **캐시 판** `weakening_diff.diff_hash`로 독립 재계산 → **캐시 판** `merge_gate.py parse-approval`이 id·date·diff·target·base·head·`diff_path` 5개와 일치,
  바이트 단정(BOM·CR·주석·자리표시 0) → `Role: doc` 커밋.
* `final`: 커밋 3개·제목·병합 없음·커밋별 경로·`Role: doc` 정확히 하나, `gate_change_ok` HEAD True·HEAD~1 False, `approved_hashes(HEAD)`에 target, `_approved_ids` base == HEAD(diff 기록은 원소 아님), 패치 `already-applied`, `plan_tables_hash` 불변.
* **옵션 가드**(post_p10b_runbook.sh 수정과 같은 모양): 옵션은 단계 이름 **앞에만**(`while [ $# -gt 1 ]` 뒤 남은 인자 정확히 1개), 단계 자리에 `--…`가 오면 거부, `--repo`면 `--state` 필수,
  `--tools-ref`는 `--repo`와 함께만(실제 저장소에서는 불변 대조 기준을 바꿀 수 없다), 실제 저장소에서 `--state` 변경 거부. 모의 실측: 6가지 오용(단계 뒤 옵션, `--repo`만, `--tools-ref`만, 옵션 값 빠짐,
  모르는 단계, 단계 자리 옵션) 모두 exit 2·저장소 미접촉, 실제 상태 파일 미생성.

모의(모래상자 = 실제 저장소 `--no-hardlinks --no-local` 복제 + gate 경로 합성 커밋 + 가짜 gate bare 사본(pre-receive·gate-runner·accept-log, `post_p10b_dryrun_setup.sh`와 같은 모양) + `.githooks` EL3·역할 hook 사본):
| 모의 | 결과 |
|---|---|
| ① `19eb475` 위 `local` | pre OK(집계 15·38·23·14·9, `_approved_ids` 38, `plan_tables_hash` `7167e028…`), A·B(interface 13줄, 기존 함수 0)·C 커밋, final OK(`gate_change_ok` True/False, `approved_hashes` 28개에 target 포함). target `1ba14d40…`(모의 커밋 id와 무관 -- 문서 blob만으로 정해진다) |
| ① EL4 | 가짜 gate에 `push gate master:master` → pre-receive(무결성 대조 + 옛 판 `merge_gate.py receive`) **통과**, accept-log 한 줄. `after-push` OK |
| ① EL4 대조 | 역할 경로(`docs/02-design/specs/…`) 트레일러 없는 커밋(plumbing `commit-tree` -- EL3 commit hook이 먼저 막으므로) → **`[EL4 거부] … Role … 정확히 하나가 아니다`**, push 거부(게이트가 실제로 거부). 참고: 역할 경로 밖(`docs/zz.md`) 트레일러 없는 커밋은 설계대로 통과(§8.2-1) |
| ② `5f643a9`(지금 gate master) 위 `local` + EL4 + `after-push` | 전부 OK, 집계 바이트 동일, target 같은 값 |
| ③ 음성: `19eb475` 위에 V3 대상 영역 decision 원소 하나(`stick_diagram:save_instance_json:stmt_delete:body[3]`) 기록 추가 | `pre`가 집계 차이(`V3 모양 24`, 대상 영역 15)를 출력하고 **멈춤**(exit 1) |
| 재실행 | 완료 뒤 `doc` 재실행 → HEAD ≠ gate base로 멈춤, `pre` 재실행 → spec card 존재로 멈춤 |
측정 중 고친 것: MSYS2 bash의 프로세스 치환 `<(…)`은 `/dev/fd` 없음으로 실패 → 파일 비교. MSYS2 grep은 CR 한 글자 패턴을 빈 패턴처럼 다뤄 모든 줄을 센다 → 승인 기록 바이트 단정은 Python으로.
세션 PreToolUse hook(`role_guard.py`)은 명령줄의 `$'…'` 인용·변수가 든 `cp` 대상·`--no-verify`를 거부한다 -- 스크립트 **본문**은 검사하지 않으므로 `bash <스크립트> <단계>` 호출은 통과(이번 실측).

### 0.6 Phase 2 DoD 기록 커밋이 들어온 뒤 다시 잴 것

`pre` 단계가 아래를 자동으로 대조하고 다르면 멈춘다. 멈추면 그 항목만 다시 재고 초안을 고친 뒤 `pre`부터 다시 돈다.
1. **집계**: DoD 커밋이 `.ai/approvals/`에 decision 기록을 더하면(예: DoD 판정 근거 결정) 집계가 `19eb475`와 달라져 멈춘다 → `v3_decision_census.py`를 새 gate master에서 돌려 (가)(나)(다)를 판단하고,
   spec card measured 문장(rev·수치·'나머지' 분해)과 승인 초안 '덮는 것' 첫 항목의 rev·수치를 **같이** 바꾼다(스크립트는 두 곳을 같은 수치로 대조). diff 기록만 더하면 집계는 같다.
2. **불변 대조**(measured rev → HEAD): DoD 커밋이 **계획서**(Phase 상태·N 표)나 design 05·10을 고치면 멈춘다 → `patch_v3_binding_docs.py --check`(pending 3, 앵커 유일), 계획서 V3 행 줄 번호(839)·design 05 317·
   design 10 382 인용, `plan_tables_hash`(`7167e028…` -- 바뀌면 이 card 승인이 아니라 `plan_tables` 승인 문제이고 DoD 쪽에서 이미 처리됐어야 한다)를 다시 재고, 맞으면 measured rev를 새 gate master로 올린다
   (집계도 그 rev에서 다시). `tools/`·`stick_diagram.py`가 바뀌었으면 0.1 표·해시 앵커 표 전체를 다시 잰다.
3. **`role/*` 0개·worktree 없음**: DoD 판정 기록 커밋 push·정리 뒤(`pre`가 확인).
4. 스크립트가 보지 않는 것(손으로): `git grep -n "변이 id" <gate master> -- docs/01-plan docs/02-design`의 새 줄(DoD 기록·history가 V3 면제 형식을 규칙으로 적었는지 -- 규칙 문장이면 계약 10 문서 패치에 더해야 한다),
   `.ai/context.md`·history에 이 card 착수 조건을 바꾸는 결정이 있는지, 게이트 캐시 판의 `interface_card.py` 출력이 13줄 모양인지(`card` 단계가 기호 행 0만 단정).
5. target·diff_base·diff_head는 실제 커밋으로 새로 계산된다(`fill_v3_approval.py`). 문서 blob이 같으면 target도 `1ba14d40…`로 같다 -- DoD가 계획서를 고치면 달라지는 것이 정상.

---

## 1. test-author 브리프(gmid-test-author, §12 순서 2)

```
역할: gmid-test-author. change id = 20260930-v3-exempt-binding (게이트 변경, red-green, phase 0.5).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-exempt-binding-test (브랜치 role/test/20260930-v3-exempt-binding). 모든 명령은 이 절대 경로로(git -C, cd 금지).
쓰기 경로: tools/gates/redteam/** 만(design 10 C10·C11 행 -- spec card gate_change: yes + 승인 기록). 다른 경로를 쓰면 EL1/EL3이 거부한다.
입력: interface card docs/02-design/specs/20260930-v3-exempt-binding.interface.md(두 표 빈 13줄 -- 게이트 card),
      spec card docs/02-design/specs/20260930-v3-exempt-binding.spec.md의 '관찰 가능한 계약' 머리(용어·묶기 해시 정의·원소 분리 규칙)와 계약 1~9, 'oracle 종류와 출처'.
열람 금지: tools/gates/mutate_changed.py(피검 도구) 소스. redteam 하네스(lib/rt.py·lib/iface.py·lib/sb.py·run_all.py)와 기존 케이스(attacks/29·31, v3_survivor)는 읽어도 된다.
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20260930-v3-exempt-binding" -m "test: …"
```

### 1.1 산출물

* `tools/gates/redteam/attacks/34-v3-exempt-binding/`: `expect.json`(케이스 머리 -- 선례 `attacks/31-v3-git-history/expect.json`: `"layer": "V3"`, `"modes": ["direct"]`, `"phase": "0.5"`, `"steps_from_records": true`,
  `basis`·`title`), `run.sh`(`rt vcase v.json`), `v.json`(V 케이스 6단계). 단계마다 `expect`에 `exit`, `layer`, `message_contains`(정확한 JSON 조각), 필요하면 `observed_equals`, `basis`(계약 문장 출처).
* `tools/gates/redteam/lib/rt.py`에 실행 동작 두 개(1.4). 승인 범위 (ii)가 이 둘만 덮는다 -- 다른 하네스 동작은 바꾸지 않는다.

### 1.2 단계(계약 9 그대로)

공통 구성(계약 9 머리):
* X(면제 대상 변이)는 head def에서 base와 **다른 문장 안**이거나 `early_return`(뒤에 병합될 범위 card 35에서도 대상으로 남게).
* **X가 그 def 대상 변이 중 유일한 생존 변이**(다른 변이는 그 단계 test가 모두 죽인다). 그래야 피검 도구가 그 단계 규칙을 빠뜨리면 X가 면제되어 exit 0이 된다.
* 승인 기록은 V 케이스 `base` 또는 `head` 사전 안 `.ai/approvals/<id>.md` 파일(선례 `attacks/29-v4-decision-exempt` -- V 케이스는 `approval`/`more_approvals`/`base_files` 키를 읽지 않는다).
  머리는 `---`로 시작하고 `target_kind: decision` 줄과 `target: <원소,…>` 줄이 있어야 도구가 읽는다(`_approved_ids` 규칙: 파일 이름이 `_`로 시작하면 무시).
* `<X>` = 구성으로 정한 변이 id 문자열(모듈 = 파일 basename, 예 `rt_engine:rt_scale:stmt_delete:body[1]`).

| 단계 | kind | 원소 | 기대(exit, 조각) | 이 단계가 잡는 잘못된 구현 |
|---|---|---|---|---|
| (a) `legacy-unbound-leak` | attack | base 커밋의 기록에 해시 없는 `X` | exit 1, `"verdict": "FAIL"`, `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "unbound"}` | 해시 없는 원소를 계속 적용(지금 도구 -- exit 0, **red**) |
| (b) `hash-mismatch` | attack | `X@@bindhash(base:<엔진 경로>:<qualname>)` | exit 1, `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "` | `@` 뒤 해시를 비교하지 않고 id만 보는 구현 |
| (c) `bound-exempt` | control | `X@@bindhash(head:<엔진 경로>:<qualname>)` | exit 0, `"verdict": "PASS"`, `"survivors": []`, `"exempt_ignored": []`; `"observe": "out_jsonl"` → `observed_equals` `{"lines": <head def 변이 수>, "by_result": {"exempt": ["<X>"]}}` | `@` 원소를 모르는 구현(지금 도구 -- exit 1, **red**), exempt를 `--out`에 안 쓰는 구현(`lines`·`by_result` 불일치) |
| (d) `bound-other-def` | attack | `X@@bindhash(head:<엔진 경로>:<같은 파일 다른 qualname>)` | exit 1, `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "` | 파일·모듈 단위 해시, 또는 '아무 def 해시와 같으면' 적용하는 구현 |
| (e) `docstring-shift` | attack | `X@@bindhash(head:notes/attempt_k.py:<qualname>)`(Dk 해시) | exit 1, `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "hash_mismatch", "approved_hash": "` | docstring을 지운 ① `def_hash`로 묶는 구현(X 면제 → exit 0) |
| (f) `malformed-element` | attack | `X@abc` | exit 1, `"survivors": ["<X>"]`, `{"id": "<X>", "reason": "malformed", "element": "<X>@abc"}` | 형식 오류를 해시 없음과 같이 취급(조각 불일치)하거나 접두 일치로 적용하는 구현 |

**판정 기록의 red 집합**: base 도구에서는 6단계 전부 FAIL이다((a)(c)는 exit, (b)(d)(e)(f)는 `exempt_ignored` 조각 없음). spec card '판정 유형 근거'에 이 문장을 넣었다.

### 1.3 검증된 구성 예(선택 -- 2026-10-01 `C:/g102`에서 **지금(base) 도구**로 생존 집합을 잼, 면제 기록 없이)

base 엔진(`skills/analog-gmid-design/assets/rt_engine.py`):
```python
"""rt."""


def rt_gain(gm, ro):
    """이득."""
    return gm * ro


def rt_scale(x):
    """배율."""
    return 2.0 * x
```
test(`skills/analog-gmid-design/assets/tests/test_rt_scale.py`, head에 둔다):
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rt_engine import rt_scale


def test_rt_scale():
    assert rt_scale(2.0) == 6.0
    assert rt_scale(-2.0) == 6.0
```
* (a)(b)(c)(d)(f)용 head `rt_scale` 본문: `"""배율."""` / `_ = len("rt")` / `return 3.0 * abs(x)` → 변이 6개, **생존은 `rt_engine:rt_scale:stmt_delete:body[1]` 하나**(killed 5: `stmt_delete:body[2]`,
  `arith:body[2].value`, `const+:body[2].value.left`, `const-:body[2].value.left`, `early_return:body[1]`). docstring 밖 문장이 모두 base와 달라 범위 card 뒤에도 6개가 모두 대상 -- (c) `lines` = 6.
  (d)의 다른 def = `rt_gain`(base·head 같음).
* (e)용: Dk(`notes/attempt_k.py`, V3 대상 밖 경로) = `def rt_scale(x):` / `_ = len("rt")` / `x = abs(x)` / `return 3.0 * x`(docstring 없음 -- Dk에서 X=`stmt_delete:body[1]`은 `x = abs(x)`).
  head = Dk 맨 앞에 `"""배율."""`만 더한 것 → X 경로 `body[1]`이 `_ = len("rt")`로 밀린다. 변이 7개, **생존은 X 하나**. ① `def_hash`(Dk) == ①(head) True, 묶기 해시 다름 True, Dk ≠ D0 True(실측).
  이야기: Dk 시도 때는 음수 입력 test가 없어 `x = abs(x)` 삭제를 등가로 승인했다.
* 이 예는 출발점일 뿐이다 -- 구성은 test-author가 정하고 근거(`basis`)를 계약 문장과 구성에서 적는다. 실측 출력: `C:/g102/proto/result.json`(작업 끝에 삭제됨 -- 위 숫자가 그 전부).

### 1.4 rt.py 동작 추가(승인 범위 (ii), 계약 9 그대로)

**(1) 자리표시자 `@bindhash(<base|head>:<경로>:<qualname>)`** -- `build_vrepo` 안.
* 지금 `build_vrepo`는 base 파일을 읽자마자 쓴다. 두 단계로 바꾼다: 먼저 `base`·`head` 사전의 모든 파일 내용을 `_file_content`로 만든다(첫 단계, `str`은 `subst_str`까지·`{"text"}`는 `replace`까지).
  그 다음 각 내용의 `@bindhash(...)`를 치환한다(둘째 단계). 값 = 지정한 사전·경로의 **첫 단계 텍스트**를 `ast.parse`해 그 qualname def 노드의
  `hashlib.sha256(ast.dump(node, annotate_fields=True, include_attributes=False, indent=None, show_empty=False).encode("utf-8")).hexdigest()`.
* 표준 라이브러리 `ast`·`hashlib`만. **`mutate_changed`(피검)·게이트 도구를 import하지 않는다.** qualname 규칙은 계약 머리(`Cls.meth`, 중첩 `outer.inner`)대로 직접 구현한다.
* 오류(조용한 통과 금지, `RuntimeError`): 참조 경로가 그 사전에 없음(예: `head:` 참조인데 그 파일이 `head` 사전에 없고 base에만 있음 -- head 사전에 다시 넣을 것), 참조 파일 첫 단계 텍스트에 자리표시자가 있음(순환),
  qualname def 없음. 권고(계약 밖이지만 fail-closed라 범위 안): 같은 qualname def가 둘 이상이면 `RuntimeError`.
* `None` 명세(파일 없음·head 삭제)는 치환 대상도 참조 대상도 아니다. 자리표시자가 없는 케이스는 바이트가 그대로여야 한다(무동작 -- auditor가 base 하네스와 전 케이스 대조한다).
* `subst_str`의 `@{KEY}`·`@win(...)`과 문법이 겹치지 않는다(`@bindhash(`는 두 정규식 어디에도 안 맞는다 -- `rt.py` 47·48행).
* `RuntimeError`가 나면 `a_vcase`는 그 예외를 잡지 않으므로 `run.sh`(`set -e`)가 끝나고 run_all이 케이스를 ERROR로 둔다 -- 계약 '그 단계 ERROR'의 실제 모양은 케이스 ERROR(남은 단계 미실행)다. 조용한 통과만 아니면 된다.

**(2) 관찰 `"observe": "out_jsonl"`** -- `a_vcase` 안, 기존 `v4_first` 분기 옆.
* 명령 끝에 `--out <WORK>/vout/<step>.jsonl`(디렉터리 만들고, 실행 전 파일이 있으면 지운다). 실행 뒤 `observed = {"lines": <줄 수>, "by_result": {<result>: [id 오름차순]}}`,
  `by_result`는 `result`가 `killed`·`survived`가 **아닌** 레코드만(이 card 뒤 `exempt`, 범위 card 뒤 `not_targeted`). 파일 없으면 `{"lines": 0, "by_result": {}}`. 줄이 JSON 객체가 아니면 `RuntimeError`.
* `observe` 키가 없거나 다른 값이면 동작 그대로(`v4_first`·`tool_tmpdir`·`root_state` 불변). (c)에서는 `tool_tmpdir`·`root_state`를 함께 쓰지 않는다(관찰 객체가 하나라서).
* 범위 card 35가 같은 관찰을 다시 쓴다(그 card는 rt.py를 더 고치지 않는다) -- 키 이름·모양을 위 그대로.

### 1.5 자기 점검(커밋 전)

* `C:/Python314/python.exe -B <worktree>/tools/gates/redteam/run_all.py --phase 0.5 --mode direct --only 34-v3-exempt-binding` → 지금 도구에서 6단계 모두 FAIL이어야 한다(red). 하나라도 PASS면 구성이 틀렸다.
* 기존 케이스 무변화: 같은 명령을 `--only` 없이 한 번. FAIL은 34뿐이어야 한다.
* 기대값은 계약 문장·구성에서만 만든다. 피검 도구 출력을 복사해 기대값으로 쓰지 않는다(base 도구 출력은 red 확인용).

---

## 2. code-author 브리프(gmid-code-author, §12 순서 5)

```
역할: gmid-code-author. change id = 20260930-v3-exempt-binding (게이트 변경, red-green).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-exempt-binding-code (브랜치 role/code/20260930-v3-exempt-binding, 부모 = test 커밋 T). 절대 경로만, cd 금지.
쓰기 경로: tools/gates/mutate_changed.py 하나(design 10 C11 행 -- gate_change: yes + 승인 기록). redteam/**·reachability.py·test_lint.py·merge_gate.py·문서는 쓰지 않는다.
입력: spec card·interface card(위와 같음). test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20260930-v3-exempt-binding.md)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다.
커밋: git -C <worktree> commit --trailer "Role: code" --trailer "Change-Id: 20260930-v3-exempt-binding" -m "…"
```

### 2.1 바꿀 것(계약 번호)

1. **묶기 해시 함수**(머리 정의): `hashlib.sha256(ast.dump(fn, annotate_fields=True, include_attributes=False, indent=None, show_empty=False).encode("utf-8")).hexdigest()`.
   * 인자를 **모두 명시**(판마다 기본값이 바뀌어도 출력이 따라 바뀌지 않게). `fn`은 `changed_defs`가 준 노드 그대로 = `mutants(fn, head_src)`에 넘기는 그 노드(docstring·데코레이터·중첩 def 포함,
     `copy`·`_strip_doc`·`decorator_list = []` 하지 않는다 -- `_replace_def`의 데코레이터 제거와 섞지 말 것).
   * 기존 `def_hash`(① 대상 선택, docstring 제외)와 이름·용도를 분리한다. 둘을 섞지 않는다.
   * 중첩 def 노드에서 나온 변이도 id의 qualname = 바깥 def → 해시는 그 바깥 `fn`(루프 변수 그대로 쓰면 자연히 맞다). 같은 qualname def가 둘이어도 해시는 그 루프의 `fn`에서(qualname→노드 사전으로 다시 찾지 말 것 -- 마지막 것만 남는다).
   * **def마다 한 번** 계산해 둔다(변이 루프 안에서 반복 계산 금지 -- 캐시 원칙).
2. **원소 분리 규칙**: 원소(앞뒤 공백 제거)에 `@` 없음 → 해시 없는 원소(id = 원소 전체). `@` 정확히 하나 → `id, h = 원소.split("@")`, `h`가 `^[0-9a-f]{64}$`면 묶인 원소, 아니면 형식 오류.
   `@` 둘 이상 → 형식 오류(id = 첫 `@` 앞). 대문자 16진도 형식 오류. 원소 집합은 `_approved(root, ns.head)` 그대로(`rch._approved_ids` -- 반환값·동작 불변, 계약 7). 집합이라 같은 원소 문자열은 이미 한 번만 센다(계약 4 둘째 문장).
   루프 밖에서 id → [원소…] 색인을 한 번 만든다.
3. **변이마다**(계약 1~4):
   * 그 id의 원소 중 묶인 원소 해시 == 그 def 묶기 해시인 것이 하나라도 있으면 실행하지 않고 `rec = {"id": mid, "result": "exempt", "bind_hash": H}`(키 순서 그대로)를 `results`에 넣고
     **`--out`에도 append**(지금은 `continue`로 건너뜀 -- WP-11). 그 id의 다른 원소는 `exempt_ignored`에 싣지 않는다.
   * 하나도 맞지 않으면 원소마다(원소 문자열 오름차순) `exempt_ignored`에 싣고 **정상 실행**: 해시 다름 `{"id", "reason": "hash_mismatch", "approved_hash": H', "head_hash": H}`,
     해시 없음 `{"id", "reason": "unbound"}`, 형식 오류 `{"id", "reason": "malformed", "element": <원소 문자열>}`(모두 키 순서 그대로).
   * 이번 실행의 변이 id와 같지 않은 원소는 싣지 않는다(다른 도구의 id·다른 def의 id).
4. **판정**(계약 5): `exempt`를 뺀 생존이 있으면 FAIL(exit 1). `exempt_ignored`는 판정을 바꾸지 않는다.
5. **출력**(계약 6): 지금 키 `tool, verdict, targets, mutants, killed, survivors` 뒤에 `survivor_bindings`(생존마다 `<id>@<그 def 묶기 해시>`, `survivors`와 같은 순서), `exempt_ignored`
   (도구가 변이를 만드는 순서: `targets` 순 → 파일 안 `changed_defs` 순 → def 안 `mutants` 순, 같은 id는 원소 문자열 오름차순). `json.dumps(…, ensure_ascii=False)` 기본 구분자. `mutants` = 결과 레코드 수(`exempt` 포함).
   ERROR 출력(`BaselineFailed`·튜플 except) 모양은 계약 밖이라 바꾸지 않는다.
6. **docstring ⑤**(계약 10): "등가 변이 면제는 `target_kind: decision`, `target` 원소 = `<변이 id>@<묶기 해시>`(…)인 승인 기록 -- head의 그 def 묶기 해시가 같을 때만 적용. 해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다"와 같은 뜻으로(design 05 317행 새 문구와 맞춘다).
7. **뒤 범위 card(35)를 위한 모양**: 지금은 모든 변이가 실행 대상이다. 면제 판정을 '변이 하나 → (exempt 레코드 | exempt_ignored 항목들)'을 돌려주는 한 곳(작은 함수)에 두고 `main` 루프에서
   그 호출 **앞에** 대상 판정이 들어갈 자리가 있게 한다 -- 범위 card 계약 4: 대상 밖 변이는 면제 판정을 하지 않는다(`not_targeted`가 먼저, `exempt`도 `exempt_ignored`도 아님). **지금 `not_targeted`를 구현하지는 않는다.**

### 2.2 하지 말 것

* 광범위 `except`(Exception·bare) 추가 금지(V6·공격 27f). 새 import는 표준 라이브러리만(`re`·`hashlib`·`ast`는 이미 있음).
* `_approved`/`reachability._approved_ids`·V4·V7 동작 변경 금지(계약 7). 승인 기록 파서·형식 변경 금지(새 키 없음).
* 새 함수를 만들고 `main`에서 안 부르는 것 금지(미배선). 옛 `if mid in approved:` 분기는 같은 커밋에서 대체(남기지 않는다).

### 2.3 자기 확인(판정 근거 아님)

* `C:/Python314/python.exe -B <worktree>/tools/gates/redteam/run_all.py --phase 0.5 --mode direct --only 34-v3-exempt-binding` → 6단계 PASS. 그리고 `--only` 없이 전체 FAIL 0.
* 승인 기록 없는 저장소에서 출력이 base와 새 두 키(빈 목록)만 다른지(계약 8).

---

## 3. auditor 브리프(gmid-verification-auditor, §12 순서 3·7)

```
역할: gmid-verification-auditor. change id = 20260930-v3-exempt-binding, evidence_type red-green, 게이트 변경(phase 0.5).
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20260930-v3-exempt-binding-audit (브랜치 role/audit/20260930-v3-exempt-binding).
모든 측정은 격리 복제본에서(§12-7): git clone --no-hardlinks --no-local <audit worktree> <scratch>/iso → git -C <scratch>/iso remote remove origin.
scratch는 새 C:/g<n> 하나만(다른 C:/g* 건드리지 말 것), 끝나면 그 폴더만 삭제. 셸 가드: set -euo pipefail, git -C <절대 경로>만, cd 실패 시 중단. 끝나면 실제 저장소 git status·reflog 불변 확인.
게이트 코드는 base 판(= approval 커밋 뒤 gate master, 순서 0의 HEAD)을 git cat-file로 추출한 사본을 쓴다(선례 20260930-v3-history-clone: extract_gate.py, 캐시와 바이트 동일 확인).
작성자(test·code) 보고는 증거로 받지 않는다. 판정 기록 .ai/verification/20260930-v3-exempt-binding.json + 스크립트·출력 .ai/verification/20260930-v3-exempt-binding/{scripts,out}/, Role: audit 커밋.
```

### 3.1 순서 3(freeze·base 확인 → `base_check.json`)

* T(test 커밋) 해시 고정. T 경로가 `tools/gates/redteam/**`뿐인지(`git diff --name-only <base> <T>`).
* base 게이트로 T 복제본에서 `run_all.py --phase 0.5 --mode direct`(전체)와 `--cases 0.5` → **base 표**(케이스·단계 판정) 보관(log sha256).
* red: 34의 6단계가 base 도구에서 FAIL인지, 원인이 계약과 맞는지 단계별로 기록: (a) exit 0(해시 없는 X 면제), (c) exit 1(`@` 원소 모름) + `observed` 불일치, (b)(d)(e)(f) exit 1이지만 `exempt_ignored` 조각 없음.
  `failure_hashes` = base 판 `merge_gate.red_failure_hash("tools/gates/redteam/attacks/34-v3-exempt-binding::<step>", "redteam.FAIL")`.
* **판별력 확인**(base 표만으로는 못 보는 것): 34 단계마다 'X가 유일 생존'을 base 도구 `--out`으로 확인(면제 원소를 뺀 같은 저장소에서 survivors == [X]). 아니면 그 단계는 규칙 누락 구현을 못 잡는다 → test 결함으로 보고.
* rt.py 무동작: base 하네스(base `lib/rt.py`)와 T 하네스로 기존 V 케이스 전부를 같은 base 게이트에 돌려 단계 판정·`observed` 차이 0(선례: "base 하네스 대조 15케이스·95단계 차이 0").
* rt.py 독립 계산: `@bindhash` 값이 auditor가 직접 계산한 묶기 해시(계약 머리 정의, 표준 `ast`)와 같은지 34 케이스 저장소에서 대조. rt.py에 `mutate_changed` import가 없는지 `grep`.

### 3.2 순서 7(병합본 판정) -- design 05 §18 · B28 선례(`20260930-v3-history-clone.json`)와 같은 모양

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | **PASS** | (1) pytest 전체(auditor_run `V1:` 명령, base 판 `pytest_gate.ini`, `-k`·`--deselect`·`-x` 없음, `--gmid-phase=0.5 --gmid-strict=`, 엄격 집합은 base 판 `merge_gate.strict_set`로 재서 기록, `v1_command_check` 위반 0) -- 변경 경로가 전부 `tools/gates/**`라 대상 트리 불변. (2) 병합본 redteam 전체 `run_all.py --phase 0.5 --mode direct` + `--cases 0.5`, **순서 3 base 표와 케이스·단계 단위 기계 대조**(선례 `scripts/cmp_rt.py`): 판정이 달라진 케이스는 `34-v3-exempt-binding`(FAIL→PASS) 하나, 단계는 34의 6단계 = red 집합. `v3_survivor`·26·27f·28·29·31 포함 나머지 같음(계약 8), `--cases 0.5` 차이 0 |
| V2 | N/A(도입 1, card phase 0.5) | 참고 측정: 커밋 사슬 base → T(Role: test, redteam/**) → code(Role: code, 부모 T, `mutate_changed.py` 1경로) → 병합(Role: doc, 트리 = code 트리), `git diff T 병합 -- tools/gates/redteam` 0. red·green 집합 |
| V3 | N/A(도입 1) | 참고: base 판 `mutate_changed.py`(base..병합본) targets 빈 목록(게이트 도구는 대상 밖). 바뀐 def의 동작은 34·probe(3.3)·실제 범위 재실행이 판정 |
| V4 | N/A(도입 1) | 참고: base 판 `test_lint.py`(`--module-dir tools/gates --subject mutate_changed:main`·새 함수). oracle 대조: 34 기대값(exit·조각·`observed_equals`)이 계약 1~9 문장과 구성에서 왔는지 단계별로, 피검 출력에서 만들지 않았는지 |
| V5 | N/A(도입 1) | 참고: base 판 `weakening_diff.py`(base→T, base→병합) -- `tools/gates/**`는 발견 경로 밖이라 PASS만으로 증거 아님. 사람 판단: 기존 `expect.json`·`v.json` 변경 0, rt.py는 선택 키 두 개 추가뿐(3.1 무동작 대조), 도구는 면제 적용 범위 축소(강화 -- 승인 기록 범위 (i)). 승인 `target`을 base 판 `diff_hash`로 재계산해 일치 |
| V6 | N/A(도입 1) | 참고: base 판 `source_lint.py`. 광범위 except 추가 0(27f 관점) |
| V7 | N/A(도입 2) | 참고: base 판 `reachability.py`(게이트 도구는 그래프 밖). 배선 관찰: 새 함수(묶기 해시·원소 분리·면제 판정)가 `main`에서 불리고 옛 `if mid in approved:` 분기가 같은 커밋에서 대체됐는지 |
| V8 | N/A(도입 4) | 엔진 무관 |
| V9 | N/A(도입 6b) | 회로 무관 |
| V10 | PASS | '재현할 수치: 없음' → `reproduced_numbers` 빈 배열. 계약 확인 측정은 3.3 probe(전부 격리 실측) |

### 3.3 redteam이 덮지 않는 계약 -- probe(합성 저장소, 병합본 도구, 기대값은 계약 문장에서)

| probe | 계약 | 입력·기대 |
|---|---|---|
| p1 여러 원소 | 4 | 같은 X에 `X`, `X@<틀린>`, `X@<맞는>` → exempt, `exempt_ignored`에 X 항목 없음. 맞는 것 없이 `X@abc`·`X`·`X@<틀린>` → 항목 3개가 원소 문자열 오름차순. 두 기록에 같은 원소 → 한 번 |
| p2 무관 원소 | 3·7 | V4 test id·V7 def id·다른 def의 V3 id·결정 id(`U-01`)·**V3 대상 영역 밖 모듈의 V3 모양 id**(`20261001-p10b-v3-equiv` 꼴 -- 합성 저장소 `skills/analog-gmid-design/assets/tests/tools/<m>.py`의 def를 가리키는 `<m>:<q>:const+:…`, 해시 없음·`@<그 def 묶기 해시>` 두 꼴, 같은 커밋에서 그 파일도 바꿔 둔다) → `exempt_ignored` 빈 목록, 그 파일 변이 0(`targets`에 없음) |
| p3 출력 모양 | 1·6 | 키 순서(`…, survivors, survivor_bindings, exempt_ignored`), exempt `--out` 레코드 키 순서 `id, result, bind_hash`, `mutants`에 exempt 포함, `survivor_bindings` = `<id>@<64자>`·`survivors` 순서, 여러 파일·여러 def에서 `exempt_ignored` 순서 = 생성 순서 |
| p4 묶기 해시 정의 | 머리 | auditor 독립 계산과 도구 `bind_hash`/`head_hash` 일치: 데코레이터 달린 def, `async def`, 클래스 메서드(`Cls.meth`), 중첩 def 노드에서 나온 바깥 def 변이(F = 바깥 def), docstring 있는 def. 데코레이터 인자만 바꾼 def → 해시 다름 |
| p5 형식 경계 | 머리 | `X@a@b`, 대문자 16진 64자, 63자, 앞뒤 공백(`target:` 원소 사이 공백) → malformed/정상 분리 |
| p6 판정 불변 | 5 | 풀린 원소가 있어도 그 변이가 죽으면 PASS(exit 0, `exempt_ignored` 비지 않음) |
| p7 다른 도구 무영향 | 7 | 같은 입력(`@` 원소 포함 기록)에서 base·병합본 `test_lint.py`·`reachability.py` 출력·exit 같음. `merge_gate.parse_approval_header`(`@` 원소 통과)·`weakening_diff.approved_hashes`·`engine_dup_scan` 결과 같음 |
| p8 무기록 저장소 | 8 | 승인 기록 없는 저장소에서 base·병합본 출력이 새 두 키(빈 목록)만 다름 |
| p9 rt.py 오류 경로 | 9 | `@bindhash` 참조 경로 없음·qualname 없음·자기 참조 → 케이스 ERROR(조용한 통과 아님). `out_jsonl` 줄이 객체 아님 → ERROR |
| p10 원래 문제 대체(B28 선례와 같은 몫) | 의도 | 병합본 도구로 DF-36 범위(`--base 070cf69 --head b29be01 --gmid-phase=2`, B28 기록 443초 참고)를 다시 돌린다: C8 원소 4개(`save_instance_json`)는 `exempt_ignored` `unbound`로 나오고 **실제 실행**된다. 결과(killed/survived)는 이 card 판정이 아니라 **백로그 B41의 측정값**으로 기록(생존이면 test 보강 또는 묶인 면제 승인 -- DF-36 판정 기록은 고치지 않는다). `load_topology` 10개는 대상 아님(해시 같음)을 확인. (도구는 승인 기록을 `--head` 트리 `b29be01`에서 읽으므로 그 뒤 기록 -- `20261001-p10b-v3-equiv` 등 -- 은 이 실행에 들어오지 않는다. gate `master` 트리의 기록까지 넣어 보려면 p2로 본다.) |

판정 기록 `approvals` = `["20260930-v3-exempt-binding"]`. 관찰(판정 약화 아님)은 V10 끝에 따로 적는다(예: ERROR 출력에는 새 키가 없다, 중첩 def 이중 변이 비용 -- 백로그 6).

---

## 4. 순서 요약(오케스트레이터)

Phase 2 DoD 완료 → **`bash _drafts/v3_binding_launch.sh pre`**(`role/*` 0개·0단계 집계·불변 대조 -- 멈추면 0.6) → **`bash _drafts/v3_binding_launch.sh local`**(A 문서·B spec+interface(게이트 캐시 판, 절대 경로)·C 승인 기록·final의 `gate_change_ok` True)
→ push 단독 실행·전체 출력 확인(`git -C <R> push gate master:master`) → `bash _drafts/v3_binding_launch.sh after-push` →
§12 순서 1(test worktree) → test-author(1절) → 순서 3 auditor freeze·base 표(3.1) → 순서 4 code worktree → code-author(2절) → 순서 6 병합 → 순서 7 auditor(3.2·3.3) → 순서 8 push → 정리 →
그 뒤 범위 card `20260930-v3-changed-stmt-scope`(커밋 계획 §4.2).
