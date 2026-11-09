# card 감사 묶음 A -- 20260921·20260922·20260923 card (2026-10-29)

- 역할: card 감사자(묶음 A). 감사만 함 -- card·계획·git 쓰기 0. 이 파일만 Write.
- 대상: master `docs/02-design/specs/2026092{1,2,3}-*` 44 파일 = card id 22(spec + interface 쌍).
- 판단 기준(승인된 것만): master 계획 v6.38.4 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(이하 P), 결정 O-173~O-181. v6.38.5(`plan/v6385`, 미병합)와 열린 Q-는 기준에서 뺌 -- 이 묶음과 닿는 곳 없음(`git diff master plan/v6385 -- P`에 `2026092[123]`·TS·이 card id 0건).
- 상태 확인 방법(실측): `.ai/verification/<id>.json` 유무, `git -C <repo> log --oneline master --grep=<id>` 커밋 수, 경로 존재(`test -e`), `git diff --name-status master...data/lut-v2-only`(O-180 적용 브랜치, 미병합), `git merge-base --is-ancestor`.
- 앞선 정리(`cards_simplify.md`, 커밋 `1451b1da`, master 병합)는 이 묶음 21개를 "(a) 기록 -- 판독·수정 안 함"으로 두었다. 그 문서의 기준 줄(5행)은 "손계산 오차는 DEC-72 `model_error`로 기록"인데 이는 O-178(e_m·model_error 폐지)로 낡았다 -- 다만 그 정리가 이 묶음에 넣은 문언(consistency 대체 표지)에는 model_error가 없다(grep 0).

## 1. 분류 집계

| 판정 | 수 | card |
|---|---|---|
| 그대로 | 1 | `20260923-probe-promote-consistency`(대체 표지 이미 있음, 문언 정확) |
| 상태 표지(한 줄) 후보 | 21 | 아래 2절의 나머지 전부 -- 실행·병합 완료 기록이지만 옛 Phase 0.5·1·2 card를 현행처럼 읽게 함 |
| 내용 개정 | 0 | 미착수·진행 card가 없음(21개 실행 완료 + 1개 이미 대체 표지) |
| 대체됨 표지(새로) | 0 | 미착수 card는 consistency 하나뿐이고 이미 표지됨 |
| 개정 대기(v6.38.5 승인 뒤) | 0 | v6.38.5·열린 Q-에 기대는 항목 없음 |

낡은 용어 grep(44 파일, `e_m|model_error|ME-1|guard|sample|heldout|held-out|as-built|grammar|device_roles|symmetry|sizing_roles`): e_m·model_error·ME-1·guard band·sample LUT·heldout 경로·as-built 근거 = **0건**. 걸린 것은 interface card에 기계적으로 뜬 옛 엔진 docstring(`device_roles`·`symmetry.matching_pairs`·`analog-grammar idioms`, ic3·ic5·d-delete-dead interface)과 ts2의 `guarded_only`(무관)뿐 -- 기록 문언이라 본문은 고치지 않고 상태 표지로 처리한다.

## 2. 왜 21개 모두 상태 표지 후보인가(공통 근거)

모두 실행·병합 완료(판정 기록 + master 커밋 2~9개). 그런데 지금 읽는 사람을 다음 넷으로 오도한다:

1. **옛 Phase 폐기**: 머리 `phase: 0.5|1|2`와 본문 "TS0~TS7(계획 N3.11)", "계획 N6.2 Phase 1 DoD"를 현행 계획 항목처럼 적는다. P 1244~1246 '옛 Phase 처리': Phase 0.5 폐기(DEC-86), Phase 1 test 분리(TS0~TS5) 폐기, Phase 2 죽은 코드·DUP 정리 폐기. P 769: "TS0~TS6(옛 인라인 self-test 이관 단계)은 폐기했다(2026-10-07)".
2. **절차 폐기**: spec card·interface card·판정 기록·auditor·V1~V10·EL1~EL4·DEC-40 승인·R1('V5 승인 운반')·§13.4 재설치를 현행 절차처럼 적는다. P 119~121(spec card·interface card·판정 기록 폐기), P 239(DEC-40 폐기), P 772~774(N3.12 폐기), P 1068~1070(N4.2 V1~V10 폐기), P 1087~1089(N4.3 폐기), P 285(DEC-86).
3. **경로 이동**: `A = skills/analog-gmid-design/assets` 아래 `sizing_recipe.py`·`stick_diagram.py`·`tests/**`·`workspaces/run_harness.py`를 적지만 지금은 `skills/analog-gmid-design/legacy/`에 있다(실측: `assets/sizing_recipe.py` 없음, `legacy/sizing_recipe.py`·`legacy/tests/conftest.py`·`legacy/tests/{contracts,unit,probes}` 있음; 이동 커밋 `60727b06`). 옛 엔진·test는 card LT-1에서 지운다(P 298 DEC-99, P 767).
4. **gate 잔여물**: gate card가 다루는 `tools/gates/**`·`hooks/role_*.py`·`.githooks`는 디스크에 남아 있으나 꺼졌다(DEC-86 "gate 잔여물은 정리", P 285).

이 넷은 card 본문을 고칠 일이 아니라(O-169: 본문은 기록) **머리에 상태 한 줄**을 다는 일이다 -- 앞선 정리의 대체 표지와 같은 자리·형식.

## 3. 제안 문안(표지 3종 + 덧붙임)

자리: spec card = 머리 블록(`---` 닫는 줄) 바로 뒤 빈 줄 다음, `## 의도` 앞. interface card = `# interface card: <id>` 줄 바로 뒤 빈 줄 다음. 끝에 앞선 정리와 같은 `## 변경 이력` 한 줄(`- 2026-10-29 <브랜치>: 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = git show <base>:<path>`). 방법은 Python 바이너리 치환(heredoc append 금지, 원칙 29).

**[G] gate·게이트 도구 card**(옛 Phase 0.5·gate 변경):
> **[상태 표지 2026-10-29] 실행·병합 완료 기록(판정 기록 `.ai/verification/<id>.json`) -- 옛 Phase 0.5·역할 분리 gate는 폐기(DEC-86, 계획 N6.1 '옛 Phase 처리'·N3.12·N4.2·N4.3).** 이 card의 게이트 동작(EL1~EL4·V1~V10)·재설치·승인(DEC-40·R1) 문장은 현행이 아니다. `tools/gates/**`·`hooks/role_*`·`.githooks`는 꺼진 잔여물이다(DEC-86). 본문은 기록이다(O-169).

**[T] 옛 test 분리(Phase 1) card**:
> **[상태 표지 2026-10-29] 실행·병합 완료 기록(판정 기록 `.ai/verification/<id>.json`) -- 옛 Phase 1 test 분리(TS0~TS6)는 폐기(계획 N6.1 '옛 Phase 처리', N3.11).** spec card·auditor·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다. `A = skills/analog-gmid-design/assets`의 옛 엔진·test는 지금 `skills/analog-gmid-design/legacy/`에 있고 card LT-1(DEC-99)에서 지운다(tag `legacy-final`). 본문은 기록이다(O-169).

**[D] 옛 죽은 코드·probe 정리(Phase 2) card**:
> **[상태 표지 2026-10-29] 실행·병합 완료 기록(판정 기록 `.ai/verification/<id>.json`) -- 옛 Phase 2 죽은 코드·DUP 정리는 폐기(계획 N6.1 '옛 Phase 처리'; 새 엔진은 모듈 지도 N3.10로 개념당 정본 하나).** spec card·auditor·DEC-40 승인 절차는 DEC-86으로 폐기했다. `A = skills/analog-gmid-design/assets`의 옛 엔진·test는 지금 `skills/analog-gmid-design/legacy/`에 있고 card LT-1(DEC-99)에서 지운다(tag `legacy-final`). 본문은 기록이다(O-169).

덧붙임(해당 card의 표지 끝에 한 문장):
- (+IC) ic3·ic5: "계획 N4.1 IC3·IC5 강제 test는 새 엔진 담당 패키지 test 폴더에 새 API로 다시 쓴다(N4.1 머리, N3.11 -- 옛 `contracts/` 폴더는 만들지 않는다) -- 이 card의 구현은 옛 엔진용이고 IC 충족 근거가 아니다."
- (+TS7) ts7: "현행 TS7은 새 엔진 계약 test를 담당 구현 단위까지 xfail로 둔다(N3.11) -- 이 card의 `--gmid-phase` conftest는 옛 Phase용이다."
- (+O180) probe-relocate·probe-promote-clean·probe-promote-differential: "이 card의 산출물(`legacy/tests/probes/**`·`tests/tools/derive_achievable_bounds.py`·`unit/test_probe_*`·P1/P2 계약 test)은 O-180 적용(LUT v2 정리) 병합 때 LT-1보다 먼저 지워진다."
- (+dispute) gate-output-utf8: "dispute의 계획 개정 요청(N3.12.2 쓰기 경로표 행)은 N3.12 폐기로 소멸했다."

자기 점검: 표지 문언은 계획 행·DEC만 인용(새 규칙·새 결정 0), 상수·회로 이름 0, 본문 삭제 0, 기준 약화 0, graph 정본과 무관(문서 표지), 사용자 결정 문장을 근거로 쓰지 않음(DEC-86·DEC-99·N6.1은 승인 계획 행; O-180은 '삭제 예정' 사실 서술에만 씀). 엔진 코드 읽기 = 경로 존재 확인(엔진 밖 사실·재작성 범위)뿐.

## 4. card별 표

| card id | 상태 | 판정 | 고칠 줄과 제안 문안 | 근거 경로:줄 |
|---|---|---|---|---|
| 20260921-gate-flow-liveness | 실행·병합 완료(판정 기록, master 커밋 7) | 상태 표지 | spec 8행 뒤·interface 1행 뒤에 [G]. 오도 문장: spec 머리 `phase: 0.5`, 계약 1~5(EL1~EL3 동작) | P:1245, P:772-774, P:285 |
| 20260921-gate-output-utf8 | 실행·병합 완료(판정 기록, 커밋 8) | 상태 표지(우선) | [G] + (+dispute). 오도 문장: spec 17-19 "§13.4 재설치(…)가 필요하다", 끝 dispute 요청 "계획 N3.12.2 … 행을 추가 … 승인해 달라" | P:772-774, P:1245, P:285 |
| 20260922-ic3-completeness | 실행·병합 완료(판정 기록, 커밋 5) | 상태 표지(우선) | [T] + (+IC). 오도 문장: spec 8-15 "IC3(계획 N4.1 …) … C6 뼈대 `contracts/test_ic3.py`를 실제 검사로", 15·64 DEC-40·R1, 23·52·56 "library 9회로"(지금 library 13, O-181 -- 기록 수치라 고치지 않음) | P:1052, P:1058, P:766, P:1246, P:239 |
| 20260922-ic5-gate-docstrings | 실행·병합 완료(판정 기록, 커밋 5) | 상태 표지(우선) | [T] + (+IC). 오도 문장: spec 8-12 "IC5 … 현존 21개 게이트에 두 줄", 17 대상 `A/*.py`; interface 13-23·52-121 옛 엔진 docstring(`device_roles`·`analog-grammar idioms`) | P:1052, P:1060, P:1246 |
| 20260922-sections-major-merge | 실행·병합 완료(판정 기록, 커밋 5) | 상태 표지 | [T]. 오도 문장: 머리 `phase: 1`, 의도 "C9(TS2 …) 전에 고친다". 도구 `tools/migrate/extract_selftest.py`는 남아 있으나 쓰임(인라인 self-test 이관)이 끝났다 | P:769, P:1246 |
| 20260922-ts0-test16-fixture | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지 | [T]. 오도 문장: spec 9-14 "TS0(계획 N3.11 …)", "DEC-40 승인 … R1", "완료 시 DF-17 해소"(DF 표 삭제됨) | P:769, P:1246, P:1248, P:239 |
| 20260922-ts1-extract-tool | 실행·병합 완료(판정 기록, 커밋 5) | 상태 표지 | [T]. 오도 문장: spec 9-13 "TS1(계획 N3.11)의 선행 도구 … 이 card 병합 커밋이 C2(TS1 이관)의 base" | P:769, P:1246 |
| 20260922-ts1-legacy-move | 실행·병합 완료(판정 기록, 커밋 5) | 상태 표지 | [T]. 오도 문장: spec 9-14 "TS1(계획 N3.11)", 계약 1 `A/tests/legacy/…`(TS2가 지움) | P:769, P:1246 |
| 20260922-ts2-pytest-split | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지 | [T]. 오도 문장: spec 9-13 "TS2(계획 N3.11)", 13·65 DEC-40·R1, 계약 6 conftest(`real_lut` = 옛 LUT, O-180 브랜치가 이 conftest를 고침) | P:769, P:1246, P:239 |
| 20260922-ts3-assert-verdicts | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지 | [T]. 오도 문장: spec 9-13 "TS3(계획 N3.11)", 13·54 DEC-40·R1 | P:769, P:1246, P:239 |
| 20260922-ts5-baseline-retire | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지 | [T]. 오도 문장: spec 9-15 "TS5(계획 N3.11)", DEC-40·R1, "사용자가 `.gitignore` … `Role: user`" | P:769, P:1246, P:239 |
| 20260922-ts7-ic-xfail | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지(우선) | [T] + (+TS7). 오도 문장: spec 9-13 "TS7(계획 N3.11)과 `00-common` CC-3 … `--gmid-phase`", 계약 1 conftest `read_plan_tables`가 `tools/gates/merge_gate.py` import | P:769, P:1052, P:1246, P:285 |
| 20260922-v3-gmid-options | 실행·병합 완료(판정 기록, 커밋 7) | 상태 표지 | [G]. 오도 문장: spec 9-14 "V3 도구 `mutate_changed.py` … §13.4 재설치는 필요 없다" | P:1068-1070, P:1245 |
| 20260923-caa970b-replay | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지 | [G]. 오도 문장: spec 11-15 "auditor V2 … 계획 N6.2 Phase 1 DoD의 '사례 caa970b 적발'", 계약 7 §13.4 | P:1068-1070, P:1087-1089, P:1246 |
| 20260923-d-delete-dead | 실행·병합 완료(판정 기록, 커밋 4) | 상태 표지 | [D]. 오도 문장: spec 10-12 `A = …/assets`, 계약 1 위치 `sizing_recipe.py:126` 등, 계약 3 `sizing_recipe.py:5875` 거부를 현행 엔진 거부처럼 | P:1247, P:298, P:767 |
| 20260923-d-delete-telescopic | 실행·병합 완료(판정 기록, 커밋 4) | 상태 표지 | [D]. 오도 문장: 의도 "일반 대체는 … `_metric_smallsignal_ratio_db` … 파일럿이 이미 그쪽을 쓴다"(옛 엔진 현행 서술), 76 DEC-40 | P:1247, P:298, P:239 |
| 20260923-probe-dead-delete | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지 | [D]. 오도 문장: spec 9-13 "TS6(계획 N3.11)", 계약 3 `contracts/test_ts6_dead_probes.py`(O-180 브랜치가 고침) | P:769, P:1247 |
| 20260923-probe-promote-clean | 실행·병합 완료(판정 기록, 커밋 3) | 상태 표지(우선) | [D] + (+O180). 오도 문장: spec 9-14 "TS6(계획 N3.11)", 계약 1·7-a 산출물(4 `unit/test_probe_*`·`_library_sized_contexts.py`·계약 test 2) -- O-180 브랜치에서 모두 D 또는 M | P:769, P:1247, `git diff --name-status master...data/lut-v2-only` |
| 20260923-probe-promote-consistency | 미착수(커밋·판정 기록 0) -- 이미 대체 표지(`1451b1da`, master) | 그대로 | 없음. 표지 문언 점검: 대체 근거(DEC-86·N6.1·LT-1 DEC-99) 맞음, `legacy/tests/probe_physical_consistency.py` 실재(O-180 브랜치 삭제 목록에 없음 = LT-1까지 남음), model_error 등 낡은 용어 0 | P:1247, P:298; spec 336·401행 |
| 20260923-probe-promote-differential | 실행·병합 완료(판정 기록, 커밋 2) | 상태 표지(우선) | [D] + (+O180). 오도 문장: 계약 1 산출물 2 test(O-180 브랜치에서 D), 61 "C13이 연 `target_kind: decision` 면제로 처리"(V4 폐기) | P:1247, P:1068-1070, O-180 브랜치 diff |
| 20260923-probe-relocate | 실행·병합 완료(판정 기록, 커밋 9) | 상태 표지(우선) | [D] + (+O180). 오도 문장: 계약 1 `A/tests/probes/` 32개·계약 5 `tests/tools/derive_achievable_bounds.py`(O-180 브랜치에서 D), 판정 유형 근거 "계획 N6.1 Phase 2 행의 판정 유형" | P:1247, P:939(`derive_achievable_bounds` 참고 위치), O-180 브랜치 diff |
| 20260923-v4-decision-exempt | 실행·병합 완료(판정 기록, 커밋 5) | 상태 표지 | [G]. 오도 문장: spec 9-16 "V4 규칙 (1) … 계획 N4.2 V4 … `05` §10 V4"를 현행 규칙처럼 | P:1068-1070, P:1245 |

'우선' = 지금 읽고 행동을 잘못할 위험이 큰 것(현행 계획 항목 IC3·IC5·TS7과 이름이 겹침, 산출물이 곧 지워짐, 열린 요청처럼 보이는 dispute). 21개를 한 번에 표지하는 것이 기본안이고, 범위를 줄인다면 '우선' 8개(gate-output-utf8·ic3·ic5·ts7·probe-promote-clean·probe-promote-differential·probe-relocate + gate-flow-liveness)부터.

## 5. 따로 보고(card 밖, 이 감사가 고치지 않음)

| # | 자리 | 내용 |
|---|---|---|
| R-1 | design `docs/02-design/features/gain-budget-gmid-sizing.{05-role-separation,10-test-separation,20-dead-code-dup}.design.md` | 이 card들의 정본 design인데 머리에 폐기 표지가 없다(grep `폐기|DEC-86` 머리 0건; 05는 "v3.6 승인됨"). 계획은 N3.12·N4.2·N4.3·N6.1에 폐기 표시를 했다(DEC-86 "지우지 않고 폐기 표시"). card만 표지하면 design으로 거슬러 읽는 사람이 다시 오도된다 -- design 정리 감사 후보. |
| R-2 | `wt/_drafts/evidence/2026-10-29/cards_simplify.md` 5행 | 기준 문언 "손계산 오차는 DEC-72 `model_error`로 기록"이 O-178로 낡았다. 그 정리가 card에 넣은 표지 문언에는 영향 없음(model_error 0건). 증거 문서라 기록으로 두되, 다음 card 정리 브리핑에서 이 기준을 옮겨 쓰지 않아야 한다. |
| R-3 | O-180 적용 브랜치 `data/lut-v2-only`(미병합) | 병합되면 probe-relocate·probe-promote-clean·probe-promote-differential 산출물과 P1/P2 계약 test가 지워지거나 바뀐다. 상태 표지 (+O180) 문장은 병합 전·후 모두 참이 되게 '병합 때 지워진다'로 썼다. |
| R-4 | ic3 spec "library 9회로" | O-181로 library는 13회로(held-out 0). 기록 수치라 고치지 않음 -- 현행 수치로 오해될 여지는 [T] 표지가 막는다. |
