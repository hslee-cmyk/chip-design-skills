# UD-6 실행 절차 -- [D-11] (가) N3.10 MOD1 `_QUERY_CACHE_MAX` · [W-1] (가) T0 import 출처 · W-2 · D0a 첫 토큰

작성 2026-10-02. 기준 gate `master` `4a286f0`. 사용자 답(AskUserQuestion `toolu_01GVLKut4JY6FMvvZJEvhKS4`, 13:35 → 13:38 KST): [D-11] "(가) 계획 표 MOD1에 추가 (Recommended)", [W-1] "(가) T0에서 test import 수정 (Recommended)".
근거 문서 `_drafts/p3_followup_questions.md` §1.3·§1.4·§2.3·§2.4·§3.3·§5. 측정 키트 `_drafts/p3ud6_kit/`(측정 전용 -- 역할 산출물 아님, test-author·code-author·auditor에게 건네지 않는다).
경로 약칭(명령은 아래 절대 경로로 -- 오케스트레이터 cwd `chip-design-skills`에서는 `_drafts/` 상대 경로가 풀리지 않는다, review_ud6 m1): `<R>` = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`(실제 저장소), `<D>` = `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts`. 본문의 `_drafts/…` 문서 언급은 `<D>/…`다.

## 0. 재질문 필요 여부 -- 지금은 없음

계약 키(D0a 계약 2 바인딩 이름, 레지스트리 이름 칸 첫 토큰) + [D-11] 토큰으로 gate `4a286f0` 대역 사슬(FU 대역 + G1 시제품)에서 `plan`을 다시 잰 결과 `upward`·`cycles`·`unassigned`·`conflicts`·`import_time_high`·`import_conflicts` 모두 0,
MOD7 밖 0 -- **[D-11] 토큰 밖의 N3.10 개정 필요 0**(`draft_p3_d0b.spec.md` '작성 전 실측' UD-6 문단). 답의 조건("D0b가 다른 개정을 더 계산하면 그때 다시 묻습니다")은 **D0b base에서 다시** 확인한다(아래 3).
B34·b26pre·backfill·B26-1·B33·G1·D0a가 미병합이라 지금 측정은 그 card들의 변화(특히 B26-1의 `RailDeclaration`·`rail_declaration`, B34의 grammar 함수 4개)를 보지 못한다.

## 1. [D-11] 계획 표 개정 -- 어느 커밋에 넣는가 (결정: 단독 오케스트레이터 문서 커밋 + 승인 기록 커밋, card 35 정리 뒤·다음 card 순서 0 전, D0b 순서 0보다 먼저)

선례 대조:
* UD-0의 N3.10 정정 12건 = 오케스트레이터 문서 커밋 `6c8287f`(Role: doc) → 승인 기록 커밋 `36e170e`(`target_kind: diff`, `diff_base` = 그 부모, `diff_head` = `6c8287f`). 그 커밋은 계획 533행(UD-5)을 **G1 문서 커밋 몫으로 일부러 뺐다**
  ("계획 533행(UD-5)은 G1 문서 커밋 몫") -- 승인 하나의 diff에 다른 승인의 변경을 섞지 않는다.
* Q-P2DOD-E2 = 정정 커밋 `1a464e4`(Role: doc, `Change-Id: 20261001-p2dod-e2-wording`, 본문에 사용자 결정·`plan_tables_hash`) → 승인 기록 커밋 `dc196cd`.
* D-19 (가) `rail_declaration` 토큰은 B26-1(그 이름을 만드는 card)보다 **먼저** 커밋됐다 -- 토큰이 가리킬 단위가 없어도 A-1은 아무것도 배정하지 않을 뿐이다(무해).
* D0b spec 계약 1: D0b card 커밋은 계획서를 바꾸지 않는다 / 계약 8 (a): N3.10 개정은 별도 승인 기록 + 오케스트레이터 문서 커밋, 그 id를 D0b 머리 `approval`에.

그래서:
* **G1과 묶지 않는다**: G1 문서 커밋은 계획 533행 + design 05 §10이고 승인 `20260930-p3-gate-move-aware`의 diff다. 같은 커밋에 521행을 넣으면 두 승인의 diff가 한 커밋에 섞인다(경로가 같아 blob 해시도 섞인다).
* **D0b card 커밋에 넣지 않는다**(계약 1).
* **단독 문서 커밋은 card 35(`20260930-v3-changed-stmt-scope`) 정리(design 05 §12 '정리' -- 역할 브랜치 `role/*` 0개) 뒤, 다음 card의 순서 0 전 문서 슬롯에 넣는다**(review_ud6 B1).
  이유: design 05 §12 머리 "역할 브랜치가 있는 동안 문서 커밋의 gate push는 EL1이 거부" -- gate 판 `tools/gates/role_hooks.py` `_judge_push`는 `git push gate master:master`일 때 `refs/heads/role/` 브랜치가 하나라도 있으면 **경로와 무관하게** 거부한다(이 두 커밋이 문서·승인 기록뿐이어도 같다).
  작성 시점(2026-10-02) 실제 저장소에는 `role/test/20260930-v3-changed-stmt-scope`(`4a286f0`)와 worktree `wt/20260930-v3-changed-stmt-scope-test`가 있다(card 35 진행 중).
  선례: card 35 자신의 문서 커밋 `a5566c8`도 그 card 역할 브랜치 생성 **전**에 들어갔다.
  D0b base 측정 전에 토큰이 들어가 있어야 D0b 착수 확인이 '[D-11] 밖 개정 0'을 한 번에 본다. D0a·M1 '작성 전 실측'도 최종 N3.10에서 잰다 -- 그래서 위 슬롯 중 가장 이른 것에 넣는다.
  내용상 늦출 이유 없음: 토큰은 `_QUERY_CACHE_MAX` 하나만 A-1로 정하고(관찰: 사상 차이 1), `plan_tables_hash` 불변(관찰 B·Q 모두 `7167e028…`), 게이트·test 영향 0.
* 승인 기록의 `target`은 **커밋 뒤** blob으로 계산한다. 부모의 계획서 blob이 `f2f4d2ee2318ec7f6e1dc607a355d3178bf8a995`(= `4a286f0` 판)이면 새 blob `8f6e21db041296ecc6569617dca13ccf581e441d`, `target` = `441b80e153a5a9e9174986ab069a50088e687448fbac3167ce864ccf16799a99`
  (스크래치 사전 계산). G1 문서 커밋이 먼저 들어가 계획서 blob이 바뀌면 값이 달라진다 -- 다시 계산한다.

## 2. 절차(오케스트레이터)

격리 주의(메모리 '검증 agent의 git 실측은 격리 경로'): 실제 저장소 쓰기는 오케스트레이터 문서 커밋 경로대로(작업 트리 = 실제 저장소 `master`, gate = `4a286f0` 이후 최신과 같은지 먼저 확인).

실행 시점: card 35 정리 뒤(역할 브랜치 0), 다음 card 순서 0 전(§1). **push 슬롯이 열리기 전에는 로컬 `master`에 이 두 커밋을 만들지 않는다** -- 로컬 `master`가 `gate/master`에서 갈라진 채 card 35가 끝나면
§12-8 `git merge --ff-only gate/master`가 실패한다(분기된 로컬 master는 fast-forward 불가). 아래 1~6은 한 번에 이어서 실행한다(커밋만 하고 push를 미루지 않는다).

1. 시작 확인(셋 다 맞아야 진행, 하나라도 다르면 멈춘다):
   * `git -C <R> for-each-ref refs/heads/role/` **출력이 비어 있음**(역할 브랜치 0 -- EL1이 문서 커밋 push를 받는 조건, review_ud6 B1).
   * `git -C <R> status --porcelain`(문서 경로 깨끗)·`git -C <R> rev-parse HEAD gate/master`(같음 -- 로컬 master가 gate 앞에 커밋을 갖지 않음).
   * 계획서 521행 = 승인 기록 초안 '현재' 문안과 바이트 같음.
2. 적용: `python -B C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/p3fq_kit/variant.py C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills qtok` -- 앵커 정확 일치 1회 아니면 쓰지 않고 exit 1(측정 키트 스크립트지만 문안이 승인 기록 초안 §범위 '새 문안'과 같은 바이트임을 `p3ud6_kit/out/d11_plan_line.diff`로 확인했다).
3. 확인: `git -C <R> diff --numstat` = `1 1 docs/01-plan/features/gain-budget-gmid-sizing.plan.md`만, 줄 끝 보존(`git diff` 한 줄 -/+ -- autocrlf 주의: 전체 파일 diff가 나오면 중단), `plan_tables_hash`(`python -B <R>/tools/gates/merge_gate.py plan-tables-hash <R>/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`) 전후 같음,
   `mod_table` 10행·N3.10 4열 10행, `_QUERY_CACHE_MAX` 백틱 토큰이 N3.10 표 안에서 MOD1 행 하나에만.
4. 문서 커밋(Role: doc) -- 제목 예: `docs: 계획 N3.10 MOD1 대표 대상에 _QUERY_CACHE_MAX 토큰([D-11] (가) -- LUT 조회 캐시 상한 상수를 사용처 MOD1에, UD-0 밖 N3.10 개정 1건)`.
   본문: 사용자 결정 원문, 바뀐 줄 하나, `plan_tables_hash` 값, "승인 기록 20261002-p3-d11-query-cache-max가 이 커밋을 diff_head로 가리킨다", 조건(D0b base 재확인). 트레일러는 `--trailer "Role: doc" --trailer "Change-Id: 20261002-p3-d11-query-cache-max"` + Co-Authored-By(메모리 '트레일러는 --trailer').
5. 승인 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/approval_20261002-p3-d11-query-cache-max.md` → `<R>/.ai/approvals/20261002-p3-d11-query-cache-max.md`, 머리 `target`·`diff_base`(4의 부모)·`diff_head`(4) 채움(`target` = §8.2 식 재계산, 1의 사전값과 대조).
   `python -B <R>/tools/gates/merge_gate.py parse-approval <R>/.ai/approvals/20261002-p3-d11-query-cache-max.md` 통과·`id` 일치, 사용자 원문 절 따옴표 안 문자열을 세션 jsonl(`toolu_01GVLKut4JY6FMvvZJEvhKS4` input/`toolUseResult`)과 다시 바이트 대조. 커밋 제목 예: `docs: 승인 기록 20261002-p3-d11-query-cache-max([D-11] N3.10 MOD1 _QUERY_CACHE_MAX, target_kind diff -- 사용자 답과 질문 원문 인용, 조건: D0b가 다른 개정을 계산하면 재질문)`.
6. push: `git -C <R> push gate master:master` **단독 실행·전체 출력 확인**(메모리 'gate push 결과 확인 뒤에만 정리'). 그 뒤 `<R>/.ai/context.md`에 Python 바이너리 append로 한 줄(메모리) + `<D>/user_decisions.md` 끝 절에 승인 기록 id·커밋 해시.
7. 순서: 이 두 커밋은 문서·승인 기록뿐이지만 **역할 브랜치가 하나라도 있는 동안에는 넣을 수 없다**(EL1 `_judge_push`는 경로와 무관하게 거부 -- §1). 그래서 card 35 정리(역할 브랜치 0) 뒤, 다음 card 순서 0 전 슬롯에만 넣고,
   push 슬롯 전에 로컬 `master`에 미리 커밋해 두지 않는다(card 35 §12-8 `merge --ff-only gate/master` 실패 위험 -- 위 '실행 시점'). 선례 `a5566c8`(card 35 문서 커밋, 그 card 역할 브랜치 생성 전). 또 B34 이후 card의 착수 확인 스크립트가 `measured at` 이후 계획서 변화를 '재측정 필요'로 볼 수 있다 --
   각 launch 스크립트의 `MEAS_PATHS`에 계획서가 있으면(예 `d0b_launch.sh`) 그 card의 '작성 전 실측' 재측정 문단에 'N3.10 MOD1 한 토큰([D-11])'을 적는다.

## 3. D0b 착수 때(조건 확인 -- 답의 조건)

* `d0b_launch.sh`: S-1이 이제 `20261002-p3-d11-query-cache-max` 승인 기록(parse-approval)과 계획 N3.10 MOD1 행의 토큰(`D11TOK`)을 함께 본다(UD-6 수정, 사본 `d0b_launch.pre-ud6.bak`). `APPR_IDS` = 두 id(D0b spec 머리 `approval` 두 줄과 같은 순서).
* D0b base(D0a 병합 뒤 master)에서 D0a `code_commit`의 `tools/migrate/move_plan.py plan`을 design 30 §6.3 `MP_ARGS`로 돌린다: `conflicts`·`upward`·`cycles`·`unassigned`·`import_time_high`·`import_conflicts` 모두 `[]`, MOD7 밖 0, `_QUERY_CACHE_MAX` = `gmid_lut.py`·`A-1`.
  * 자동 확인: S-5가 여섯 목록·MOD7 밖, S-7이 (d)-1 표의 `mod` 줄기와 **`_QUERY_CACHE_MAX`의 `rule` = `A-1`**(review_ud6 m4로 더함 -- 다른 규칙으로 `gmid_lut`에 온 경우도 거부)을 본다.
  * 모두 비면 → 순서 0 진행(승인 조건 충족, 재질문 없음).
  * 하나라도 비지 않으면 → **멈추고 사용자에게 다시 묻는다**(승인 기록 '덮지 않는 것'·D0b 계약 8). 질문 문안은 `p3_followup_questions.md` §1.3 모양(현재 배정 → 새 배정, 위로 가는 참조와 줄 번호, (가) N3.10 토큰 / (나) 다른 해소).
* `draft_p3_d0b.spec.md` (d)-1 표에 `_QUERY_CACHE_MAX` 행을 더했다(26 표본·행 있는 24) -- D0b base에서 근거(레지스트리 277행 칸·N3.10 토큰) 재확인 후 test-author 착수.

## 4. [W-1] -- T0 card로 (별도 승인 기록 없음)

* `draft_p3_t0.spec.md`: 의도 A군 보강·계약 8(바뀌는 파일 여덟)·계약 9(여덟 파일)·**계약 11**(3파일 24행·7이름 출처 표, (a) 범위 (b) 객체 동일 (c) 잔여 0)·거부 입력·'결정 필요 항목'(W-1 질문·답 원문, V5 승인 범위에 'import 출처 변경 3줄(7이름)')·'작성 전 실측' UD-6 문단(gate `4a286f0` 실측).
  사본 `draft_p3_t0.spec.pre-ud6.bak`. `parse_spec_card` 통과, interface card '기존 함수 6개'(앞 판과 같음 -- 계약 절의 엔진 함수 이름은 백틱 없이).
* `t0_briefs.md`: 쓰기 경로 여덟 파일, freeze 경로 여덟, V2 일곱 test 파일, V5 사람 판단·질문 문안에 import 3줄, auditor 계약 11 확인 문단. 사본 `t0_briefs.pre-ud6.bak`. `t0_launch.sh`는 test 커밋 경로를 검사하지 않아 수정 없음.
* T0 V5 승인 기록 `20260930-p3-tests-location-free`(test 커밋 뒤): 사용자 원문 절에 [W-1] 질문·답을 jsonl에서 바이트 그대로(질문의 '이름 7개'는 파일별 셈 -- 원문 그대로 두고 범위 설명에 '서로 다른 이름 6' 사실 문장).

## 5. 그 밖 반영

* `draft_p3_d0a.spec.md`: 계약 2 '레지스트리 행과 단위' -- 함수 칸 첫 백틱 토큰 = 단위 키(§5 기본안, 질문 없음), 필수 합성 단계 `reg-first-token`, '결정 필요 항목' 277행 닫힘, '작성 전 실측' UD-6 재측정 문단. 사본 `draft_p3_d0a.spec.pre-ud6.bak`. `d0a_briefs.md` 합성 단계 색인 19개(사본 `.pre-ud6.bak`).
  parse 통과·interface card 바이트 같음.
* `draft_p3_d0b.spec.md`: 머리 `approval` 둘째 줄, 의도·계약 8 (a)·계약 6 (c) 예시·계약 11 표 red 크기(80·354/129/225·24 중 23)·(d)-1 표 `_QUERY_CACHE_MAX` 행·거부 입력 R-A2 대상 행 353·'결정 필요 항목'·'재현할 수치'·'작성 전 실측' UD-6 문단(2'~6').
  사본 `draft_p3_d0b.spec.pre-ud6.bak`. parse 통과(`approval` 2개)·interface card 바이트 같음. `d0b_briefs.md`(S-1b 행·0.1 UD-6 요약·0.2 닫힘·`approvals` 두 id, 사본 `.pre-ud6.bak`).
* `m_cards_plan.md` §6(새 절): W-4·W-1 닫힘, 계약 키 + 토큰 판 MOD별 단위 수, **W-2 계약 문언**(M2·M9 spec card 초안이 아직 없다 -- 만들 때 그대로 옮긴다). 사본 `m_cards_plan.pre-ud6.bak`.
  주의: M1 수정 agent가 14:26에 `m_cards_plan.pre-r1.md`를 만들었다 -- 그 agent가 `m_cards_plan.md`를 통째로 다시 쓰면 §6이 사라질 수 있다. 사라졌으면 아래 W-2 사본에서 복원한다.
* **손대지 않은 것**: `draft_p3_m1.spec.md`(M1 수정 agent 소유 -- 그 agent에 'M1-2 = [D-11] (가)로 닫힘, `_QUERY_CACHE_MAX` 규칙 A-1, MOD1 8단위'를 전할 것; 이미 그 지시로 돌고 있으면 확인만), F1/F2·M1 검토·G1 키트 파일, `user_decisions.md`(오케스트레이터가 커밋 뒤 append).

### W-2 계약 문언 사본(m_cards_plan §6과 같음)

* 계약: "split 파일의 재수출 줄 = 파일 앞머리 묶음(docstring 뒤 연속한 `import`·`from … import`·`sys.path` 조작 식 문장) 중 **마지막 import 문 바로 뒤**. ACF에서는 `from stick_diagram import load_topology  # noqa: E402` 뒤(재수출 줄에도 `# noqa: E402`)."
* 거부 입력(M2·M9): "ACF 재수출 줄을 `sys.path.insert` 앞에 둠 → auditor 측정: 저장소 밖 cwd의 새 프로세스에서 `importlib.util.spec_from_file_location`으로 ACF를 로드하면 `ModuleNotFoundError`(기대: 정상 위치에서 성공)".
* auditor 판정 명령(M2·M9 `equivalence.commands`): 위 로드를 병합본에서 실행해 exit 0. 생성기 `head_end`는 `sys.path.*` 식 문장을 머리 묶음으로 넘긴다(`p3fq_kit/w2_acf_position.py`).

## 6. 재현(측정 -- 스크래치 `C:/g222`, 실행 뒤 삭제)

```bash
D=C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts; R=C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
bash $D/p3ud6_kit/build.sh 4a286f0              # 복제본 C:/g222/r: FU 대역 → G1 시제품(B) → [D-11] 한 줄(Q) → 재생성 모의(RG), plan names_base/names_q/hash_q/names_rg
bash $D/p3ud6_kit/reject.sh <Q> <RG>            # (d)-1 대조 + 다섯 test 모사(Q·RG) + 거부 입력 14개 → out/sim5.jsonl
python -B $D/p3ud6_kit/w1_lines.py $R 4a286f0 <out.json>        # 계약 11 실측(git show만)
python -B $D/p3fq_kit/shim_import_reads.py C:/g222/r 4a286f0 <out.json>
```
이번 실행: B `ab73be6`, Q `835858c`, RG `2db9cd9`(복제본 커밋 -- 삭제됨). `install_proto.py` 13:24판(`90bd6ed8…`)은 gate master 판 `mutate_changed.py`·`rt.py`에 앵커가 맞는다(옛 `p3fq_kit/build_plan.sh`의 `dd60db6` 되돌리기 단계는 이 판에서 '앵커 mc print: 0개'로 실패 -- `build.sh`에서 뺐다).
복제본은 `git clone -c core.autocrlf=false`로 만든다(시스템 `core.autocrlf=true`면 커밋 diff가 파일 전체가 된다 -- 첫 실행에서 관찰, 다시 만들었다).


## (오케스트레이터 대기열 2026-10-02) card 35 정리(역할 브랜치 0) 뒤 문서 커밋 묶음
1. D-11 계획 N3.10 MOD1 토큰 + 승인 기록 (이 runbook §2)
2. design 30 §10 DoD 정정 D1~D4 + history H2 1행: `_drafts/design30_dod_corrections.py` (Role: doc, 승인 기록 불요 -- 독립 검증 review_phase3_dod_r1.md 결과 확인 뒤)
3. F1 쓰기 경로표(gmid 폴더로 좁힌 행) + plan_tables 승인 기록: `_drafts/approval_20261002-p3-f1-workspaces-write-path.md` (F1 spec card 전이면 됨)
각 커밋은 단독 push·결과 확인 뒤 다음.
4. [T0-V4] V4 면제 decision 승인 기록 `_drafts/approval_20261002-p3-t0-v4-s009-exempt.md` → `.ai/approvals/20261002-p3-t0-v4-s009-exempt.md` (Role: doc 커밋, 단독 push·결과 확인). 사용자 답 "test_s009 규칙(1) 면제 (Recommended)"(2026-10-02 19:54 KST, 기록에 jsonl 바이트 대조). **T0 test worktree 생성 전**에 gate master에 있어야 한다(`t0_launch.sh` 조건 11, V4가 head 트리 `.ai/approvals`를 읽는다). 커밋 전 할 일: B26-1 병합 뒤 착수 0단계 (아) `p3kit_t0/step0_v4.sh`의 `v4_summary.txt` 판단 줄을 기록 '범위 설명'의 `<MATCH 결과 줄 -- …>` 자리에 옮기고 parse-approval(gate `tools/gates/merge_gate.py`, 파일 이름 = `<id>.md`) exit 0 확인. MATCH가 아니면 커밋하지 않고 질문을 다시 올린다.


## (다음 세션 할 일 2026-10-02) F1 r3 S1 문언 좁히기 -- review_p3_f12_r3.md (2) 채택(오케스트레이터 기본안, 사용자 질문 아님)
- 계약 3 (바) S1 문장 -> "같은 이름이 파일 안(base·head 각각)에서 서로 다른 엔진 모듈에 묶이면 목록 단위로 둔다. 스코프와 횟수는 따지지 않고, 모듈은 점 경로 전체로 비교한다. head에만 그런 묶음이 새로 생기면 FAIL."
- 착수 조건 (3) 괄호·현재 목록 S1 줄·계약 8 ⑤(5단위로 되돌림)·거부 입력 T7·5c 표 good 행·f12_equiv.py multibound 조건 1줄. 이후 독립 검증.
- F1 V5 ⑤ 제시 방법은 review_p3_f12_r3.md 끝 절(실제 F1 base 계산 목록, 단위별 diff 해시, ⑤-a/⑤-b).

## (다음 세션 할 일 2026-10-02) D0a·D0b 착수 전 보완 -- review_d0a_d0b_ready.md
- D0b-S1: d0b_launch.sh plan_sum 캐시 키에 초안 해시 포함(또는 표본 대조 매번 재계산) -- 초안 표 오기가 S-7 충족으로 통과하는 것 재현됨
- D0a-S1: d0a_briefs.md 179·122행 필수 합성 단계 18 -> 19(reg-first-token)
- D0a-S2: 착수 0단계에 (e1)·(e4) AST 스캔 추가(B34·backfill·B26-1 실제 코드에서 확인)
- minor: D0b "커밋 대기" 문장(spec 11·160·218, 브리프 19·189), m6 head 단언 verdict!=ERROR, R-A2 T-E 불일치, 계약 12 library 문구, 브리프 4절 T0 선행 vs PREDS, freeze 실패 표지; D0a move_plan_sim "r1 재구현" 표기 정정

## (다음 세션 할 일 2026-10-02) M2~M9 N-1 -- review_m2_m9_r1.md
- 전 card(M2~M9) '재수출 줄 위치' 문장과 계약 3 (b)에 "앞머리 묶음은 base 파일(단위 삭제 전)에서 정한다" 추가, p3kit_m2_m9/r1m/c3.py 같은 기준으로 고친 뒤 M6 재측정(올바른 M6 병합본이 지금 문언으로는 3 (b) index 16에서 거부됨)
- m-b: M8 R-CACHE 기대 칸에 "(사용 함수를 완전 shim SR에 다시 넣는 모양이면 + rebind json)" 보충; m_cards_plan §3-2 '초기화 순서' -> '위상 순서'

## (다음 세션 할 일 2026-10-02) post-35 실측 반영 -- post35_real_a17b8bd.md
- V3 대상 수 7종·B26PRE·EQ4·CARRY 전부 옛 값과 같음(실제 a17b8bd). 고칠 것은 mutate_changed.py 인용 줄 번호뿐: draft_p3_g1.spec.md 274~276, draft_b33.final.spec.md 294~295·301·67·307, g1_briefs.md 113~114·406 (G1 재고정 agent 결과와 겹치는지 먼저 대조)
- G1 무동작 기준선 g1_kit/out/noop_base_4a286f0.* 다시 뜨기(28·31·34·v3_survivor 옛 FAIL은 환경 문제)
- 0f23786 판 표기 줄(draft_p3_g1 32·288·318, g1_briefs 26) 유지 여부 결정

## (2026-10-02 종료 상태) card 35 병합 완료 -- gate master dafe5cf, 역할 브랜치 0. 다음 세션 첫 순서: 위 문서 커밋 대기열(D-11 계획 토큰+승인, design 30 정정, F1 쓰기 경로표+승인 -- 각각 단독 push) -> B34 착수(b34_launch.sh; post35_real_a17b8bd.md·b34_post35_dryrun.md 반영 확인). G1 card: approval_20260930-p3-gate-move-aware.md pin 문단에 a6615951… 문장 추가(G1 재고정 보고), 계약 12 not_targeted 문구·qualname 중복 결정 필요.
