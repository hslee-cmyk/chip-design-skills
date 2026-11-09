# card 감사 묶음 B -- 20260929·20260930·20261001(b26-backfill·topology-md-sync) card 19개(파일 38) (2026-10-29)

- 감사자: card 감사자 묶음 B(읽기 전용, 문서·git 쓰기 없음). 판정자 아님 -- 제안만.
- 기준: master 계획 v6.38.4(`chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`), 결정 O-173~O-181, CLAUDE.md 원칙 33항. v6.38.5·열린 Q-*에 기대는 항목은 없음(아래 '개정 대기' 0).
- 실행 여부 확인: `.ai/verification/<id>.json`(V 항목 verdict에 FAIL 0) + 그 기록의 `code_commit`이 `git merge-base --is-ancestor <c> master`로 master 조상인지(읽기만).
- 앞선 정리와의 관계: `evidence/2026-10-29/cards_simplify.md`(커밋 `1451b1da`, master 병합)도 이 19개를 (a) 기록 18 + (c) 대체 1로 분류했다. 이 감사는 그 분류에 동의하고, 그 뒤 결정(O-178~O-181)과 '지금 읽는 사람을 오도하는가'를 더 봤다.

## 1. 집계

| 분류 | card 수(파일) | card |
|---|---|---|
| 그대로(이미 대체 표지) | 1 (2) | `20260930-b26-rail-accessor-set` |
| 상태 표지 한 줄 후보 -- 우선(현행 규칙과 반대·폐기 규칙을 현행처럼 적음) | 8 (16) | b34-grammar-explicit, topology-md-sync, restore-plan-functions, df23-registry-record, p10-df23-inventory, registry-grade-fix, rejudge-cache, v3-changed-stmt-scope (+ 아래 gate 묶음 v3-exempt-binding·v3-history-clone은 같은 문안이라 '보통'에 둠) |
| 상태 표지 한 줄 후보 -- 보통(경로만 옮겨짐) | 10 (20) | probe-engine-dup, b26-pre-test-strengthen, d-move-tests, df35-harness-paths, df36-instance-relpath, dup-w-calc, p9-kcl-edges, v3-exempt-binding, v3-history-clone, b26-backfill-interdig-final-audit |
| 내용 개정(미착수·진행 card) | 0 | 미착수·진행 card 없음 |
| 대체됨 표지(새로) | 0 | -- |
| 개정 대기(v6.38.5 승인 뒤) | 0 | -- |

18개 전부 실행·병합 완료 이력이다(판정 기록 PASS, code 커밋 master 조상). 본문은 고치지 않는다(O-169). 표지 후보인 이유는 공통 셋이다.
1. **card가 속한 옛 Phase(0.5·2·3)가 폐기됐다** -- 계획 N6.1 '옛 Phase 처리'(plan:1240~1250), DEC-86(plan:285). spec card·interface card·auditor 제도 자체도 폐기(plan:31, plan:119~120, N4.2 plan:1068).
2. **본문의 `A` = `skills/analog-gmid-design/assets`가 가리키는 코드·test는 2026-10-07 `skills/analog-gmid-design/legacy/`로 옮겨졌다**(커밋 `60727b06` rename 159건, `a21a24f9` 경로 보정; `skills/analog-gmid-design/LEGACY.md` 표). 경로 실측: 이 card들이 인용한 `A/…`·`assets/…` 경로 중 추적 파일은 전부 `legacy/…`에만 있다(스크립트 `scratchpad/cardB/chk.py`, 결과 `missing_by_card.txt`).
3. **그 test는 지금 돌지 않고 곧 지워진다** -- `skills/analog-gmid-design/pyproject.toml:20` `testpaths = ["gmid_engine/tests"]`, card LT-1에서 `legacy/` 삭제(DEC-99 plan:298, plan:1194).

`_drafts/…` 같은 저장소 밖 경로(wt/_drafts)는 추적 대상이 아니라 '없음'이 정상이다 -- 개정 사유 아님.

## 2. 공통 표지 문안(제안)

각 spec card의 front matter 닫는 `---` 바로 다음 줄(빈 줄 뒤), interface card는 H1 다음 줄에 한 문단. `20260930-b26-rail-accessor-set`의 기존 표지 양식을 따른다.

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙 아님.** 판정 `.ai/verification/<id>.json`(PASS), code `<code_commit 앞 8자리>`는 master에 병합됐다. 옛 계획 Phase <p> card이고 Phase <p>와 spec card 제도는 현행 계획 N6.1 '옛 Phase 처리'·DEC-86으로 폐기됐다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 코드·test는 2026-10-07 `skills/analog-gmid-design/legacy/`로 옮겨졌고(60727b06), 새 test 체계(`gmid_engine/tests`)에서 돌지 않으며 card LT-1에서 지워진다(DEC-99). <card별 추가 문장> 본문은 기록이다(O-169).

gate card(Phase 0.5) 변형: "옛 계획 Phase 0.5(역할 분리 gate) card이고 gate는 DEC-86으로 꺼졌다. 본문의 재설치·`integrity.py`·V3 절차는 현행 검증 절차가 아니다(현행 = 매 변경 뒤 새 test 체계 전체 실행, N6.3)."

자기 점검: 표지는 사실(판정 기록·커밋·계획 행)만 적고 새 규칙·값·cache를 만들지 않는다(graph 정본·상수 발명 무관). as-built 인용은 '어디로 옮겨졌나'(재작성 범위·현재 식별자 지칭, O-166 (b))뿐이고 판정 근거로 쓰지 않는다. 사용자 결정 번호는 근거가 아니라 사실 기록으로만 둔다.

## 3. card별 표

| card id | 상태 | 판정 | 고칠 줄과 제안 문안 | 근거 경로:줄 |
|---|---|---|---|---|
| 20260930-b26-rail-accessor-set | 미병합·대체(이미 표지, `1451b1da`) | 그대로 | spec:11·interface:3 표지의 "-- 검증 대기"는 `cards_simplify` 검증이 끝나면 지운다. 다른 개정 없음. (표지의 "새 엔진은 `gmid_engine/authoring/rails.py`에…"는 현재 식별자 지칭이라 허용 범위) | plan:1246(3 모듈 분할 폐기·옛 B26-1 부품 이식), plan:1179(단위 2), plan:259(DEC-60) |
| 20260930-b34-grammar-explicit | 완료(PASS, `2eb7e559`) | 상태 표지(우선) | spec 8행 뒤·interface H1 뒤에 공통 표지 + "이 card의 계약(analog-grammar를 못 찾으면 ImportError -- spec:11~25)은 analog-grammar를 사이징 입력의 원천으로 요구한다. 현행은 반대다: analog-grammar는 쓰지 않고 지우며(DEC-99 G-1·G-2), 회로 해석은 연결과 원문만으로 한다(원칙 14)." | spec:11~25; plan:298; CLAUDE.md 원칙 14 |
| 20261001-topology-md-sync | 완료(PASS, `2de923b8`) | 상태 표지(우선) | spec 7행 뒤에 공통 표지 + "spec:13·100의 '영구 계약 test'(`legacy/tests/contracts/test_topology_md_sync.py`)는 legacy에 동결돼 지금 돌지 않는다. md↔json 일치는 LT-1 순서 4 md 렌더러 재작성(design `LT1-md-renderer`)이 맡는다." | spec:13, spec:100; pyproject.toml:20; plan:1360, plan:1377 |
| 20260930-restore-plan-functions | 완료(PASS, `0b403153`) | 상태 표지(우선) | spec 9행 뒤 공통 표지 + "spec:19의 DEC-26 인용('`canonical_spec()`만 정본 -- 구현됨')은 옛 문언이다: 현행 DEC-26은 회로 spec 파일(`<name>.sizing_spec.json`)이 정본이고 `canonical_spec()`·`derived_spec`(run_harness)은 옛 엔진 전용, 상태 미구현. spec:28의 `A/sky130_nfet_pfet_lut_sample.npz`는 지우기로 결정됐다(LUT는 v2 r2 묶음만 남김, O-180)." | spec:19, spec:28; plan:226(DEC-26); user_decisions.md:1161(O-180) |
| 20260930-df23-registry-record | 완료(PASS, `b7b1e008`) | 상태 표지(우선) | spec 8행 뒤 공통 표지 + "DF 표는 v6.38.4 백로그 재감사로 계획에서 지워졌고 DF-23은 닫혔다(history H2). `reg_check --df23-inventory`는 `legacy/tests/tools/reg_check.py`에 있고 현행 절차가 아니다." | plan:1249(4 DF 수정 폐기·DF 표 삭제), plan:209(DEC-09 '옛 DF-23 닫힘') |
| 20260930-p10-df23-inventory | 완료(PASS, `56b86c6f`) | 상태 표지(우선) | 같음(DF-23 닫힘·DF 표 삭제 문장) | plan:1249, plan:209 |
| 20260930-registry-grade-fix | 완료(PASS, `cbddcb9e`) | 상태 표지(우선) | 공통 표지 + "등급표가 있는 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`)는 '옛 엔진 부품을 새 엔진으로 가져올 때 보는 표'로 남는다. `tools/gates/reg_check.py`로 적힌 도구(spec 본문)는 실제로 `legacy/tests/tools/reg_check.py`에 있고 LT-1에서 지워진다." | plan:41; LEGACY.md 표 |
| 20260929-rejudge-cache | 완료(PASS, `cfadb761`) | 상태 표지(우선) | spec 7행 뒤 gate 변형 표지 (spec:9~20의 '§13.4 재설치 필요'·hook 348초 서술이 현행 절차로 읽힘) | plan:285(DEC-86), plan:1242(0.5 폐기) |
| 20260930-v3-changed-stmt-scope | 완료(PASS, `b70a05a4`) | 상태 표지(우선) | gate 변형 표지 + "계획 N4.2 V3 행(plan:1078)이 이 card를 V3 대상의 '정의'로 가리키지만 N4.2 자체가 폐기 절이다." | plan:1068, plan:1078 |
| 20260930-v3-exempt-binding | 완료(PASS, `dd01d1d5`) | 상태 표지(보통) | gate 변형 표지 (본문의 `skills/analog-gmid-design/assets/tests/tools/reg_check.py` = 지금 `legacy/tests/tools/`) | plan:1068 |
| 20260930-v3-history-clone | 완료(PASS, `dee338d9`) | 상태 표지(보통) | gate 변형 표지 | plan:1068 |
| 20260929-probe-engine-dup | 완료(PASS, `505b0124`) | 상태 표지(보통) | 공통 표지 + "`engine_dup_scan.py`·probe test는 `legacy/tests/`에 있다." | plan:1248(2 DUP 정리 폐기) |
| 20260930-b26-pre-test-strengthen | 완료(PASS, `e4d5833f`) | 상태 표지(보통) | 공통 표지(Phase 3). 본문의 `device_roles` 입력은 옛 엔진 태그 동작을 고정한 test 입력이라는 것만 덧붙임: "`device_roles` 등 topology 태그는 DEC-99로 저장소 데이터에서 지운다." | spec:59·154·195; plan:298 |
| 20261001-b26-backfill-interdig-final-audit | 완료(PASS, `495bb0ea`) | 상태 표지(보통) | 공통 표지(Phase 3) | plan:1246 |
| 20260930-d-move-tests | 완료(PASS, `1c5b9202`) | 상태 표지(보통) | 공통 표지(Phase 2) -- 옮긴 `regression_runner.py`·`interleave_splits.py`는 `legacy/tests/tools/` | LEGACY.md |
| 20260930-df35-harness-paths | 완료(PASS, `57781a73`) | 상태 표지(보통) | 공통 표지 + "`run_harness.py`는 `legacy/workspaces/`에 있다." | plan:125, LEGACY.md |
| 20260930-df36-instance-relpath | 완료(PASS, `ed98d35b`) | 상태 표지(보통) | 같음 | LEGACY.md |
| 20260930-dup-w-calc | 완료(PASS, `a9de49c0`) | 상태 표지(보통) | 공통 표지(Phase 2) | plan:1248 |
| 20260930-p9-kcl-edges | 완료(PASS, `a410f310`) | 상태 표지(보통) | 공통 표지(Phase 2) | plan:1248 |

폐기 규칙 어휘 점검(e_m·model_error·ME-1·guard band·heldout 경로): 38 파일에서 0건(`e_m` 일치는 전부 `compute_metric`·`optimize_multistage` 같은 부분 문자열). sample LUT 1건(restore-plan-functions, 위 표), analog-grammar 7 파일(b34가 핵심, 나머지는 옛 엔진 서술), `device_roles` 9 파일(옛 엔진 test 입력).

## 4. 실행 방식 제안(오케스트레이터 판단)

- 표지 36 파일을 한 커밋에 넣거나, 우선 8 card(16 파일)만 넣고 나머지 10 card는 LT-1(`legacy/` 삭제) 커밋에서 같은 표지를 넣는 안. LT-1 뒤에는 `legacy/` 경로도 사라지므로 표지 문장 '`legacy/`로 옮겨졌고'를 'tag `legacy-final`에만 있다'로 바꿔야 한다 -- 둘째 안이면 한 번만 쓴다.
- 대안: card마다 표지 대신 `docs/02-design/specs/` 색인 문서 하나에 '옛 계획 card = 기록' 목록. 단 card 파일을 직접 여는 사람에게는 보이지 않으므로 권고는 파일별 표지.

## 5. 범위 밖 관찰(card 아님 -- 참고)

- 계획 plan:1377 "md **10개**(library 6 + heldout 4)"는 O-181(held-out 4회로 library 이관, held-out 0) 뒤 낡은 문언(지금 `skills/analog-gmid-design/assets/library/*.topology.json` 14개, `assets/heldout` 없음). 계획 개정 몫.
- O-180이 지우기로 한 `skills/analog-gmid-design/assets/sky130_nfet_pfet_lut_sample.npz`는 master 작업 트리에 아직 있다(해당 정리 card 미병합으로 보임).
