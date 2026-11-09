# card 문서 정리 -- 손계산 우선 기준 적용 (2026-10-29)

- 작성: card 문서 정리 작성자 agent. 판정자 아님(검증 대기).
- worktree `wt/cards-simplify`, 브랜치 `cards/simplify`, base master `07181524`(계획 v6.38.3 승인), 커밋 `1451b1da`.
- 기준(사용자 2026-10-29): gm/ID 손계산 우선, 손계산 오차는 DEC-72 `model_error`로 기록하고 최종 확정은 오라클. 'SPICE와 수치가 같은가'는 완료 조건이 아니다. O-169(낡은 card를 덧대지 않음), O-153·O-165(as-built 보존은 근거 아님), graph 단일 정본, 상수 발명 금지, 만들면 배선.
- 대상: master `docs/02-design/specs/` 95 파일 = card ID 48(spec+interface 쌍 46, 단일 2) + 양식 `_TEMPLATE.spec.md`.
- 구현 상태 확인 방법: master `.ai/verification/<id>.json` 유무, `integ/it12:.ai/verification/` 유무, `git log --all --grep`, `git merge-base --is-ancestor`(B26-1 code `e92e6b84`·test `212f76a9` = master 아님), 엔진 파일(`gmid_engine/authoring/rails.py` 있음, `legacy/` 있음 = LT-1 미병합).

## 1. 분류 집계

| 분류 | 수 | card |
|---|---|---|
| (a) 구현·병합 완료 = 기록 | 42 | 옛 계획 Phase 0.5~3 card 39(master 판정 기록), IT-0·IT-2a·IT-2b(통합 브랜치 `integ/it12` 판정, master 미병합) |
| (b) 미구현, 현행 계획 범위 그대로 | **0** | -- |
| (c) 미구현이거나 범위가 바뀌어 현행 계획이 대체 | 5 + 혼합 1 | IT-1, IT-2c, IT-2d, 옛 B26-1(`b26-rail-accessor-set`), 옛 TS6 probe 승격(`probe-promote-consistency`), 혼합 = IT-2 공통(2a·2b 기록 / 2c·2d 대체) |
| (d) 판정 불가·card 아님 | 1 | `_TEMPLATE.spec.md`(양식) |

## 2. 전수 표

| card(파일 접두) | 파일 | 대상 card | 동결 판 | 구현 상태 | 현행 계획 v6.38.3과의 관계 |
|---|---|---|---|---|---|
| `20260921-gate-flow-liveness` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 0.5 | master 판정 기록 `.ai/verification/20260921-gate-flow-liveness.json` | (a) 기록 |
| `20260921-gate-output-utf8` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 0.5 | master 판정 기록 `.ai/verification/20260921-gate-output-utf8.json` | (a) 기록 |
| `20260922-ic3-completeness` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ic3-completeness.json` | (a) 기록 |
| `20260922-ic5-gate-docstrings` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ic5-gate-docstrings.json` | (a) 기록 |
| `20260922-sections-major-merge` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-sections-major-merge.json` | (a) 기록 |
| `20260922-ts0-test16-fixture` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts0-test16-fixture.json` | (a) 기록 |
| `20260922-ts1-extract-tool` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts1-extract-tool.json` | (a) 기록 |
| `20260922-ts1-legacy-move` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts1-legacy-move.json` | (a) 기록 |
| `20260922-ts2-pytest-split` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts2-pytest-split.json` | (a) 기록 |
| `20260922-ts3-assert-verdicts` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts3-assert-verdicts.json` | (a) 기록 |
| `20260922-ts5-baseline-retire` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts5-baseline-retire.json` | (a) 기록 |
| `20260922-ts7-ic-xfail` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-ts7-ic-xfail.json` | (a) 기록 |
| `20260922-v3-gmid-options` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260922-v3-gmid-options.json` | (a) 기록 |
| `20260923-caa970b-replay` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260923-caa970b-replay.json` | (a) 기록 |
| `20260923-d-delete-dead` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260923-d-delete-dead.json` | (a) 기록 |
| `20260923-d-delete-telescopic` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260923-d-delete-telescopic.json` | (a) 기록 |
| `20260923-probe-dead-delete` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260923-probe-dead-delete.json` | (a) 기록 |
| `20260923-probe-promote-clean` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260923-probe-promote-clean.json` | (a) 기록 |
| `20260923-probe-promote-consistency` | 2 | TS6 probe 승격(옛 엔진) | 옛 계획 Phase 2 | 커밋·판정 기록 없음 | (c) 대체 -- 옛 Phase 폐기(DEC-86)·LT-1(DEC-99) |
| `20260923-probe-promote-differential` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260923-probe-promote-differential.json` | (a) 기록 |
| `20260923-probe-relocate` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260923-probe-relocate.json` | (a) 기록 |
| `20260923-v4-decision-exempt` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 1 | master 판정 기록 `.ai/verification/20260923-v4-decision-exempt.json` | (a) 기록 |
| `20260929-probe-engine-dup` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260929-probe-engine-dup.json` | (a) 기록 |
| `20260929-rejudge-cache` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 0.5 | master 판정 기록 `.ai/verification/20260929-rejudge-cache.json` | (a) 기록 |
| `20260930-b26-pre-test-strengthen` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 3 | master 판정 기록 `.ai/verification/20260930-b26-pre-test-strengthen.json` | (a) 기록 |
| `20260930-b26-rail-accessor-set` | 2 | B26-1(옛 엔진) | 옛 계획 Phase 3 | code·test 커밋 있음, master 미병합, 판정 기록 없음 | (c) 대체 -- N6.1 '옛 Phase 처리' Phase 3 폐기·단위 2 rail_declaration 이식 |
| `20260930-b34-grammar-explicit` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 3 | master 판정 기록 `.ai/verification/20260930-b34-grammar-explicit.json` | (a) 기록 |
| `20260930-d-move-tests` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-d-move-tests.json` | (a) 기록 |
| `20260930-df23-registry-record` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-df23-registry-record.json` | (a) 기록 |
| `20260930-df35-harness-paths` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-df35-harness-paths.json` | (a) 기록 |
| `20260930-df36-instance-relpath` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-df36-instance-relpath.json` | (a) 기록 |
| `20260930-dup-w-calc` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-dup-w-calc.json` | (a) 기록 |
| `20260930-p10-df23-inventory` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-p10-df23-inventory.json` | (a) 기록 |
| `20260930-p9-kcl-edges` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-p9-kcl-edges.json` | (a) 기록 |
| `20260930-registry-grade-fix` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-registry-grade-fix.json` | (a) 기록 |
| `20260930-restore-plan-functions` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20260930-restore-plan-functions.json` | (a) 기록 |
| `20260930-v3-changed-stmt-scope` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 0.5 | master 판정 기록 `.ai/verification/20260930-v3-changed-stmt-scope.json` | (a) 기록 |
| `20260930-v3-exempt-binding` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 0.5 | master 판정 기록 `.ai/verification/20260930-v3-exempt-binding.json` | (a) 기록 |
| `20260930-v3-history-clone` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 0.5 | master 판정 기록 `.ai/verification/20260930-v3-history-clone.json` | (a) 기록 |
| `20261001-b26-backfill-interdig-final-audit` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 3 | master 판정 기록 `.ai/verification/20261001-b26-backfill-interdig-final-audit.json` | (a) 기록 |
| `20261001-topology-md-sync` | 2 | 옛 계획 card(엔진·gate·test) | 옛 계획 Phase 2 | master 판정 기록 `.ai/verification/20261001-topology-md-sync.json` | (a) 기록 |
| `20261021-it0-baseline` | 1 | IT-0(card 0) | 계획 v6.23·design 41 v1.12.3 | 통합 브랜치 `integ/it12` 판정 기록 있음(test-only), master 미병합 | (a) 기록 |
| `20261021-it1-input-tie-removal` | 2 | IT-1 | 계획 v6.23·design 41 v1.12.3 | `integ/it12` 구현·판정(red-green), master 미병합 | (c) 대체 -- v6.38.3 N6.5 'IT-1 범위 재작성'(O-168·DEC-106·E-19) |
| `20261021-it2-common` | 1 | IT-2 공통 | 계획 v6.23~v6.28 | 2a·2b 구현(integ/it12), 2c·2d 미구현 | (a)+(c) 혼합 -- 2a·2b 기록, 2c·2d 대체 |
| `20261021-it2a-snapshot-derive` | 2 | IT-2a | 계획 v6.24·design 41 v1.12.4 | `integ/it12` 구현·판정, master 미병합(갱신본은 integ/it12) | (a) 기록 |
| `20261021-it2b-kernel-window` | 2 | IT-2b | 계획 v6.24~·design 41 v1.12.x | `integ/it12` 구현·판정, master 미병합(갱신본은 integ/it12) | (a) 기록(θ 창 측정 삭제는 WB-1 범위 3 몫) |
| `20261021-it2c-icm-config` | 2 | IT-2c | 계획 v6.23~v6.28·design 41 v1.12.3~v1.12.7(재동결본 `card/it2c` d95c8ff8 = v6.37) | 미구현 | (c) 대체 -- v6.34 O-109·v6.35 O-115·v6.36 O-118·v6.38.3 E-09·E-13·E-22 |
| `20261021-it2d-refine-front` | 2 | IT-2d | 계획 v6.23~·design 41 v1.12.3~ | 미구현 | (c) 대체 -- O-109 C1(다듬은 창 없음)·O-111·O-112(B77) |
| `_TEMPLATE` | 1 | 양식 | 05-role-separation §11.2 | 해당 없음 | (d) card 아님 -- 손대지 않음 |

## 3. 고친 card (전부 대체 표지만 -- 본문 불변)

| 파일 | 줄 전 → 후 | 넣은 것 |
|---|---|---|
| `20261021-it1-input-tie-removal.spec.md` | 176 → 183 | 대체 표지(현행 계획 N6.5 'IT-1 범위 재작성' + card 0 IT-0b, 재동결 필요; v6.38.4 범위 6 승인 대기) + 변경 이력 |
| `20261021-it1-input-tie-removal.interface.md` | 66 → 73 | 같음 |
| `20261021-it2c-icm-config.spec.md` | 98 → 105 | 대체 표지(현행 N6.6 범위 1·6; `card/it2c` `d95c8ff8` v6.37 재동결본도 E-09·E-13·E-22 반영 전) + 변경 이력 |
| `20261021-it2c-icm-config.interface.md` | 66 → 73 | 같음 |
| `20261021-it2d-refine-front.spec.md` | 96 → 103 | 대체 표지(다듬은 창·front 범위 소멸 O-109 C1, 현행 = cfg 배선·`ls_swing` 삭제·B77) + 변경 이력 |
| `20261021-it2d-refine-front.interface.md` | 60 → 67 | 같음 |
| `20261021-it2-common.md` | 328 → 335 | 혼합 표지(2a·2b 기록, 2c·2d 대체, IT-2e card 없음) + 변경 이력 |
| `20260930-b26-rail-accessor-set.spec.md` | 547 → 554 | 대체 표지(N6.1 '옛 Phase 처리' Phase 3 폐기·'옛 B26-1은 부품으로 이식' = 단위 2, 재동결 없음) + 변경 이력 |
| `20260930-b26-rail-accessor-set.interface.md` | 371 → 378 | 같음 |
| `20260923-probe-promote-consistency.spec.md` | 67 → 74 | 대체 표지(옛 Phase 폐기 DEC-86·LT-1 DEC-99, 재동결 없음) + 변경 이력 |
| `20260923-probe-promote-consistency.interface.md` | 18 → 25 | 같음 |

합계 +77 / −0(`git diff --numstat 07181524 1451b1da`), blob CR 0(11/11, `git cat-file -p` 바이트 계수). 변경 이력 줄 = 표지 전 원문 `git show 07181524:<path>`.

## 4. 기준 적용 결과 -- 내용 수정 0인 이유

1. (b) card가 0이다. 미구현 card(IT-2c·IT-2d)와 범위가 바뀐 card(IT-1)는 모두 현행 계획이 범위를 바꿨으므로 O-169대로 본문을 맞추지 않고 표지만 했다.
2. 그래도 IT card 본문 전부(`20261021-*` 15 파일)를 'SPICE 수치 일치 완료 조건'으로 grep·판독했다(`SPICE|ngspice|oracle|오라클|정밀|as-built|일치|비트 동일`, 88 줄):
   - oracle은 모두 (손) toy 손계산·(식) design 식·(독립) 계수·grep이다. SPICE 다리는 '보류(card EO-1)'로 card 밖이다 → 원칙과 맞음.
   - '비트 동일'은 엔진 대 엔진 결정성(같은 head 두 번)·순수 리팩터링 불변(NFR-4) 기준이다. SPICE 대비 정밀도가 아니다 → 원칙과 맞음(정의 동일성).
   - 'as-built'는 '변화표 기준 = as-built IT-0 기록'과 'as-built 결정 금지(design에 없으면 멈춤)' 두 쓰임뿐이다. as-built 보존을 근거로 쓰는 문장은 없다.
3. 옛 계획 card 39(a)는 기록이라 판독·수정하지 않았다.

## 5. 멈춘 자리·계획 먼저 후보(card에서 결정하지 않음)

| # | 자리 | 내용 | 처리 |
|---|---|---|---|
| S-1 | 현행 계획 N6.6 순서 'IT-2c 착수 실측 (c) 오라클이 선언한 실제 vntol·reltol' (master card IT-2c:28·IT-2 공통:104도 같은 문언) | 오라클 수치 허용치를 엔진 판정 분해능 정의의 착수 조건으로 읽는다 -- 'SPICE 정밀도를 엔진에 들이는 범위'인지 판단 필요 | 계획 문언이라 card에서 고치지 않음. 계획 개정 후보로 보고 |
| S-2 | IT-2b `tol_v` = 매 측정 해 tol(as-built `integ/it12`) | tol_V 계열 재검토(`tolv_family_rereview.md`)·감사 E-1/E-2가 승인 대기 | 기록 card라 손대지 않음. v6.38.4 결정 뒤 WB-1 범위 3·IT-2c 재동결에서 다룸 |
| S-3 | 감사 §4 E-0·E-1·E-2(오차 합리성 = 결정 불변, 정밀화 받아들임 규칙) | 사용자 승인 대기(근본원칙 확장) | card 문언에 넣지 않음 -- 재동결 때 승인된 판으로 |
| S-4 | IT-1 범위 6(B4 S1v 파생 술어, P9-M1a)·DR-1 | 계획 v6.38.4 승인 대기 | IT-1 표지에 '승인 뒤 재동결 범위 확정'만 적음 |
| S-5 | master의 IT-2a·IT-2b·IT-2 공통 사본이 `integ/it12` 판보다 낡음(diff +97/−57 등) | 기록 판이 두 곳 | 손대지 않음. 통합 병합 때 integ/it12 판이 들어옴 |

## 6. 기준 약화 후보

없음(0건). test 기대값·완료 조건·oracle·기준선 문언을 바꾸지 않았다(본문 삭제 0줄).

## 7. 자기 점검표(작성자 자기보고 -- 판정은 검증자)

| 점검 | 결과 | 방법 |
|---|---|---|
| 분류 근거 | 실측 | 판정 기록 파일 유무(master·integ/it12), `git merge-base --is-ancestor`, 계획 N6.1·N6.5·N6.6 원문 |
| 대체 표지 사실 | 실측 | 계획 v6.38.3 N6.5 재작성 절·N6.6 범위 1·6·'IT-2d -- B77'·N6.1 '옛 Phase 처리' 판독, `card/it2c` 판의 `dc_output_structure` 8회·E-09/E-13/E-22 0회 grep |
| graph 단일 정본(새 필드·cache·사본) | 해당 없음(문서 표지만) | -- |
| 상수 발명·회로 이름 규칙 | 0 | 표지 문언 판독 |
| 만들면 배선 | 해당 없음(새 산출물 = 표지 11곳·이 문서) | -- |
| 계획·design과 어긋남 | 0 -- 표지는 계획 문언을 인용만, 새 결정 없음 | 판독 |
| 본문 삭제·기준 약화 | 0줄 / 0건 | `git diff --numstat` |
| heredoc append | 0 -- 수정 = Python 바이너리 치환(`mark_cards.py`), 이 문서 = Write | -- |
| CR | blob CR 0 (11/11) | `git cat-file -p` 바이트 계수 |
| 원래 취지와 다름 | 없음. 단 '(b) 0'이라 지시 2의 내용 수정이 실제로 일어나지 않았다는 사실은 보고 | -- |
| git 안전 | `git -C`·`set -e`만, reset/checkout/stash/push 0 | -- |
