# B26-1 spec card 개정 기록 -- v4 → v5

작성 2026-10-01. 대상: `_drafts/draft_b26_1.spec.md`(id `20260930-b26-rail-accessor-set`). 개정 전 사본: `_drafts/draft_b26_1.v4.spec.md`.
입력: `_drafts/b26_reconcile_edits.md` B절(9항목), 통합 질문 `_drafts/b26_survivor_final_question.md`, 통합 측정 `_drafts/b26_reconcile/out/`(`plan_summary.txt`, `survivor_table.md`, `classify_planC12.txt`), 사용자 결정 U-BF "결함으로 고침 (Recommended)"(`_drafts/user_decisions.md`).
저장소 쓰기·상태 변경 git 없음. 재검사 scratch `C:/g127`(측정 뒤 삭제).

## 1. 편집별 처리

| 편집 | 처리 |
|---|---|
| B1 'V3 계획' 2 표 교체 | '옮긴 264: 기존 인벤토리 150 + 계약 근사 87, 생존 27' → 통합 측정 '기존 test 죽임 214, **기존 test 생존 50** = B26-1 계약 26(E1 14·E3 6·E5 2·7(c) 1·직접 호출 3) + b26pre 16 + trace 2 + backfill 결함 2 + 등가 4'. '기존 인벤토리만으로의 생존 수는 재지 않았다' 문장 삭제. `_metric_kcl_residual` 3개 = '직접 호출 근사 1 test로 죽음 실측'. '재현할 수치' V3 줄도 같은 수치로(옛 수치는 v4 기록 §3로 가리킴). review2 §3 대비 문단은 그대로 둠 |
| B2 '남는 24' 표 교체 | 생존 50의 처리 표(5묶음)로: b26pre 16(E6 11 + E7 5), trace 2(b26pre 계약 11), backfill 2('등가 아님 -- 결함(U-BF)', backfill card가 문장 삭제), 등가 4(근거 그대로). 시나리오 A(대상 299 → 남는 4 = 등가 4)·C(C1·C2 → 1) 한 줄 |
| B3 'V3 계획' 3·U3 | 질문 경로 → 통합 질문 Q1. 'b26pre 19 test(1 파일)'. 등가 기본안 = 계약 15 정리 C1·C2 + `range` const− 1건 해시 면제(id 후보 `20261001-b26-v3-equiv-range`). C3(`itertools.combinations`)는 하지 않음(측정 B 새 생존 7). U3에 Q1-BF 답해짐(U-BF 원문)과 Q-B34-PHASE 동시 질문 |
| B4 계약 15 추가(Q1 1번 기준) | 동작 불변 정리 C1(`_propose_L_roles` 두 번째 `candidates is None` 가드 삭제)·C2(`open_net = open_terminals[0]` → `(open_net,) = open_terminals`)를 **엔진 변경 계약 항목**으로 명시(code-author, V3 필수). 판정 = auditor V3 대상 소멸 + 동작 불변은 계약 8·14. Q1 2번이면 항목 삭제, 3번이면 C3·새 생존 7 계약 필요. 계약 14 끝 문장을 계약 15로 연결. 판정 유형 근거 표 green 행에 15 |
| B5 대상 수 | 'V3 계획' 1에 '착수 base(b26pre + backfill 병합 뒤) 대상 299'(301 → 299, 시나리오 A, C1·C2 뒤에도 299 -- `classify_planC12.txt`). auditor 재측정 문장 유지 |
| B6 착수 조건 8·승인 필요 ① | 'U3 결정(Q1) -- b26pre 병합 + backfill 결함 card 병합(U-BF 1번) + 등가 면제 승인 기록 커밋(Q1 1번 1건 / 2번 4개 1건)'. 착수 조건 머리·'의도' 순서 줄에 b26pre → backfill card 추가 |
| B7 계약 12 직접 호출 | b26pre 새 test 파일의 `resolve_stack_layout`(계약 5) 1곳·`propose_vertical_stack_id_gap_fill`(계약 6) 2곳·`find_differential_pair_candidates`(계약 11) 2곳 추가(`rails = rail_declaration({"supply_nets": ["vdd", "gnd"]})`). backfill card test 파일(`test_b26_backfill_interdig.py`)은 시그니처 불변이라 고치지 않는다는 줄 |
| B8 U4·U5 | 문안 경로 → 통합 질문 Q2·Q3 |
| B9 옛 질문 초안 | `b26_1_survivor_question.md`·`b26_backfill_question.md` 머리에 '대체됨' 한 줄(삭제 없음) |

## 2. 재검사

* gate `0f23786` `tools/gates`(git archive -- 저장소 내부 gate 캐시 경로 인자는 role_guard EL1이 막아 같은 판을 archive로 씀)의 `role_paths.parse_spec_card`: 통과(`phase 2`, `red-green`, `gate_change no`, `approval ['20260930-b26-before-phase3']`, 절 12개).
* `interface_card.py`(card 사본 `C:/g127/ic/`, `--root` = a796468+B34 사본): 기존 함수 44개 -- **v4 사본과 같은 집합**(새 심볼 0). 밑줄 시작 14개(`_propose_L_roles`·`_propose_gm_id_roles`·`_metric_kcl_residual` 등)는 v4부터 있던 것(계약 4의 시그니처 변경 대상·계약 6·14의 직접 호출 대상)이라 이번 개정이 늘린 비공개 심볼은 없다.
* b26pre 시제품 19 test(계약 11 포함): a796468·a796468+B34 사본 × seed 0·1 모두 19 passed(`b26pre_revision_log.md` v3 → v4).

## 3. 남은 것(오케스트레이터·사용자)

* 통합 질문 Q1(등가 처리)·Q2(B40)·Q3(P9 시그니처) + Q-B34-PHASE를 한 AskUserQuestion 묶음으로. Q1이 1번이 아니면 계약 15를 지우거나(2번) C3 계약을 더한다(3번).
* backfill card 승인 기록 `20261001-b26-backfill-interdig-fix` 커밋, Q1 면제 기록 커밋 뒤 머리 `approval` 줄 갱신.
* Q-B34-PHASE 답에 따라 머리 `phase` 값.

## 4. 독립 검토 `review_b26_final.md` F1~F3 반영 (2026-10-01, 백업 `draft_b26_1.v5.spec.md`·`b26_survivor_final_question.v2.md`)

| 지적 | 처리 |
|---|---|
| F1 착수 조건 8 순서 | 착수 조건 8 = 'Q1 답 기록(`_drafts/user_decisions.md`) + b26pre 병합 + backfill 병합'. 등가 면제 decision 기록(target = 병합본 AST 경로 id@def 원본 해시)은 code 커밋 K 뒤 auditor `mutants()` 측정으로 쓰고 병합 전에 커밋, 그때 머리 `approval` 줄 갱신(선례 P10b `20261001-p10b-v3-equiv` `d6a9778` → `0f23786`). 재시도에서 면제 대상 def가 바뀌면 재승인. 승인 필요 목록 ①도 같은 시점으로. 질문 Q1 1번 (d)에 '기록은 구현 뒤 해시로 병합 전 커밋' 구절 |
| F2 Q-B34-PHASE 본문 | `b26_survivor_final_question.md`에 Q4 절 신설(네 card B34·b26pre·backfill·B26-1, gate 사실: 현재 Phase 대조 없음, V1 `--gmid-phase`(1009·1213)·strict 집합(1042)은 phase 2·3 둘 다 빈 집합이라 test 결과 같음, 차이 = V1 토큰·DoD 집계·③ 문구; 선택지 (가) phase 3 + 새 decision 기록(Recommended, id 후보 `20261001-b26-phase3-cards`) / (나) Phase 2 DoD 앞으로 당겨 phase 2 유지). 머리 상태 문단을 Q4로 연결. `pending_questions.md`의 strict 집합 오기는 정정 줄을 바이너리 append(앞 줄 그대로) |
| F3 수치 문구 | (a) Q1 배경 '301 중 50' → '대응이 있는 264개 중 50개(새 문장 37개는 B26-1 계약 몫)', 결과 '남는 생존 0'·측정 요약에 '대응 있는 변이 기준'. (b) 'V3 계획' 1: 299는 수만 같고 대상 4개가 바뀜(빠짐 4 = 지운 가드 삭제·cmp_flip, `[0]` const± / 들어옴 4 = 지운 가드 바로 뒤 문장 1, `open_net` 읽는 문장 3) -- 새 4개는 계약 7(e) E1·b26pre가 죽임(측정 B: E1 3, E1+b26pre 1). (c) 계약 15 '판정'에 새 4개도 죽어야 한다는 문장 |
| 질문 입력 | `_drafts/b26_ask_payload.md`(Q1 U3·Q2 B40·Q3 P9 시그니처·Q4 Q-B34-PHASE, 질문당 선택지 2~4, 권고 첫째) |

남은 것: 사용자 답(4질문) → `user_decisions.md` 기록 → Q4 답에 따라 네 card 머리 `phase`, Q1이 1번이 아니면 계약 15 삭제(2번) 또는 C3 계약(3번).
