# Phase 3 design·승인 질문이 반영할 것 -- B26 묶음 4문항 답(2026-10-01)에서

작성 2026-10-01. 대상: `_drafts/draft_phase3_design_v8.md`(다른 agent가 편집 중이라 이 문서로 넘긴다), `_drafts/phase3_approval_question.md`, `_drafts/pending_questions.md`.
근거: 사용자 답 4개(세션 jsonl `63c6146a-…` AskUserQuestion `toolu_01KTtsbRiK7S3cv1coUsAyPw`, 질문 21:10 KST·답 21:14 KST, 요약 `_drafts/user_decisions.md` 'B26 묶음 4문항').
줄 번호는 이 문서 작성 시점의 `draft_phase3_design_v8.md`(238,344 바이트, 21:19)·`phase3_approval_question.md`(21:19) 기준이다 -- 편집 중이라 옮길 때 다시 찾는다.

## 1. A2-③은 답해졌다 -- Phase 3 승인 질문에서 뺀다 (필수)

답: **"phase 3 + 정정 기록 (Recommended)"** = Phase 3 승인 질문 A2-③의 (가)와 같은 내용.
* 네 card(B34 `20260930-b34-grammar-explicit`, b26pre `20260930-b26-pre-test-strengthen`, backfill `20261001-b26-backfill-interdig-final-audit`, B26-1 `20260930-b26-rail-accessor-set`) 머리는 `phase: 3`(초안 반영 완료, `parse_spec_card` 통과).
* 순서 유지: P10b → Phase 2 DoD → 34 → 35 → B34 → b26pre → backfill → B26-1 → B33 → Phase 3 card.
* A2 기록 ③ 문구 정정 = 새 decision 기록 **`20261001-b26-phase3-cards`**(문안 `_drafts/approval_20261001-b26-phase3-cards.md`, parse-approval 통과). A2 기록 파일은 고치지 않는다.
* 그 기록은 **design 30 승인·U-03을 기다리지 않는다**고 명시했다 -- 네 card는 Phase 3 design 승인 전에도 착수·병합할 수 있다.

고칠 곳:
| 위치 | 지금 | 바꿀 것 |
|---|---|---|
| `phase3_approval_question.md` 10행 "**다섯 질문**(v8: A2-③ 추가)" | 질문 5개 | **질문 4개**(A2-③ 삭제, 2026-10-01 B26 묶음 [card phase]로 답해짐) |
| 같은 파일 12행 "A2-③ → 새 decision 승인 기록(답이 (가)면 …, (나)면 …)" | 대기 | 삭제하거나 "A2-③은 `20261001-b26-phase3-cards`로 이미 기록(이 질문 밖)"으로 |
| 같은 파일 79~92행 A2-③ 질문 블록 전체 | 질문 | 삭제. 끝 괄호의 "답을 받으면 Q-B34-PHASE를 닫는다" 일은 지금 한다(아래 4) |
| design v8 §9.2 머리(639행) "질문 5개(v8: A2-③ 추가)" | 5개 | 4개 |
| design v8 §9.2 표 A2-③ 행(651행) "이 design은 정하지 않는다. 질문 기본안 …" | 미결 | "**결정됨**(2026-10-01, 사용자 답 'phase 3 + 정정 기록 (Recommended)', 승인 기록 `20261001-b26-phase3-cards`): 네 card `phase: 3`, Phase 3 M card 전 병합 유지" -- 또는 §9.2(사용자 몫)에서 빼고 §6.4·§8.1 사실 문장으로 옮긴다 |
| design v8 §11-11(1073~1080행) "사용자 승인 기록 문장과의 충돌(이 design이 정하지 않는다) … 별도 항목 A2-③으로 묻는다" | 미결 | "해소됨 -- `20261001-b26-phase3-cards`가 ③ 병합 시점 문구를 'Phase 2 DoD 뒤·Phase 3 M card 전(card `phase: 3`)'으로 바로잡음". `--gmid-phase` 사실 문장(1080행)은 남기되 값은 3으로 확정 |
| design v8 §6.4 456행 괄호 "(인계: 두 card 초안의 `phase: 2`와 승인 기록 A2 ③의 'Phase 2 진행 중에 병합' 문장이 이 순서와 어긋난다 -- §11-11)" | 인계 | "(네 card `phase: 3`, ③ 문구는 `20261001-b26-phase3-cards`로 정정)" |
| design v8 머리 개정 노트 11행 "A2 ③ 'Phase 2 진행 중' 충돌은 결정하지 않고 승인 질문의 별도 항목으로(S3)" | 이력 | 이력 문장이라 지우지 않는다 -- 다음 개정 노트에 "A2-③ 답(2026-10-01)으로 승인 질문에서 뺌" 한 줄. 경위는 history로(계획서는 design용 원칙) |
| design v8 §10 E5 관련 1293행 "(A2-③ (나)면 P2D에도 같은 값 허용)" 및 §10 E5 본문의 같은 분기 | 두 갈래 | (나)는 기각됐다 -- (나) 분기 삭제. P2D(Phase 2 DoD 판)에는 B26-1이 없으므로 E-LIB `rails`는 P2D 대 HEAD에서 계약값 판정 쪽만 남는다 |
| revision log 1268·1282행 | 이력 | 그대로(이력) |

## 2. 네 card가 이제 `phase: 3` card라서 생기는 Phase 3 판정 사실 (필수 확인)

* **Phase 3 DoD 집계**: N6.3 목록이 `^phase: 3$` spec card를 세면 네 card가 **Phase 3 DoD 목록에 든다**(Phase 2 DoD 목록에서는 빠진다). design v8 §8.1 578행·§9.1 611~614행은 "Phase 2 DoD 목록에 들지 않는다"만 적는다 --
  Phase 3 DoD(§10 E 행·N6.3 판정 기록 목록)가 네 card의 판정 기록을 어떻게 세는지(그대로 포함 / '앞당긴 Phase 4 몫'으로 표시) 한 문장을 더한다. 계획 1001행(넷 몫은 Phase 4 행 범위에서 빠지지 않는다)과 함께 적는다.
* **D-23(595행) "phase 3 card의 병합 시점"**: "T0·D0a·D0b는 spec card `phase: 3`이고 …"에 네 card도 `phase: 3`임을 적는다. 계획 991행 공통 착수 조건 "이전 Phase DoD PASS"는 네 card에도 걸리고 확정 순서상(Phase 2 DoD 뒤) 자동 성립한다.
  590행 표 "Phase 2 DoD PASS | T0·D0a·D0b(phase 3 card)" 행에 네 card를 더한다.
* **strict 집합(`merge_gate.strict_set`, 1042행 -- 같은 phase card의 `activated_ic_case` 합집합)**: 네 card는 `activated_ic_case`가 없으므로 뒤에 오는 phase 3 card의 strict 집합을 바꾸지 않는다.
  네 card 자신의 strict 집합은 그 앞에 병합된 phase 3 card가 없어 빈 집합이다. Phase 3 card(T0·G1·D0a·D0b·M…) 중 `activated_ic_case`를 가진 것이 있으면 그 card 이후의 phase 3 card만 영향받는다 -- 설계 문장 변경은 필요 없고 사실 확인용.
* **V1 명령**: 네 card 판정 기록의 V1은 `--gmid-phase=3`. §11-11 1080행 사실과 맞춘다.

## 3. 다른 세 답이 Phase 3 design에 주는 영향 (확인 수준)

* **U5 "갱신 승인 (Recommended)"** -- B26-1이 P9 계약 test `test_dup_kcl_edges.py`의 두 시그니처 단언을 `rails`(키워드 전용·기본값 없음·주석 `RailDeclaration`)를 넣은 정확 일치로 바꾼다(기록 `20261001-b26-p9-signature-update`, diff, B26-1 test 커밋 T 뒤 커밋).
  Phase 3에서 `kcl_series_union`·`_kcl_and_matching_edges`가 MOD로 이동해도 이 단언은 `inspect.signature`라 바이트 이동이면 같다. 단 test가 `RailDeclaration`을 `stick_diagram` 속성으로 참조하면 T0(§7.1 A군 R-DEF 전환)·F1 호출부 목록에 `test_dup_kcl_edges.py`가 드는지 D0b/T0 base에서 다시 센다.
  design v8 117행("B26-1의 `rails: RailDeclaration` 같은 주석이 깰 수 있다 → D0b 계약 test가 단언")과 연결한다.
* **U4 "추가 승인 1건 (Recommended)"** -- B26-1이 `propose_device_roles_gap_fill`의 `refined is None` 분기 반환에서 `unavailable_reason` 키를 지운다(기록 `20260930-b26-b40-reason-key`). §6.4 467행 '바뀌는 def' 칸의 B26-1 항목에 "B40 반환 키 삭제"를 더하면 정확하다(새 def·이동 단위 변화 없음).
* **U3 "정리 2줄 + 면제 1 (Recommended)"** -- B26-1이 동작 불변 정리 C1·C2(`_propose_L_roles` 중복 None 가드, `open_terminals[0]`)를 하고 `find_differential_pair_candidates`의 `range(i + 1, …)` const− 1개를 변이 id@def 원본 해시로 면제(기록 `20261001-b26-v3-equiv-range`, K 뒤).
  면제 id는 `stick_diagram:find_differential_pair_candidates:…` 모듈 접두를 가지므로 **M card가 그 def를 다른 MOD로 옮기면 면제는 따라가지 않는다**(묶기 규칙 `20260930-v3-exempt-binding`). M card가 equivalence라 V3 변이를 재지 않으면 영향 없음 --
  Phase 3 card 중 그 def에 V3를 재는 card가 있으면 재승인이 필요하다는 한 줄을 §6.4 또는 M card 계약에 둔다. §6.4 수치(SD 최상위 정의 수 등)는 C1·C2로 바뀌지 않는다(문장 정리만).
* B26-1 auditor V3 대상 수(301 → 299, backfill 병합 뒤)는 Phase 3 design 수치와 무관하다.

## 4. 오케스트레이터 몫(이 design 밖)

* `_drafts/pending_questions.md` Q-B34-PHASE(2행~)를 **닫는다**: 답 'phase 3 + 정정 기록 (Recommended)'(2026-10-01), 기록 `20261001-b26-phase3-cards`.
* 커밋 순서: `20261001-b26-phase3-cards`(와 `20260930-b26-b40-reason-key`) decision 기록 → 네 card 각자의 순서 0 커밋(B34가 첫째). 기록 커밋 전에는 `approval: 20261001-b26-phase3-cards` 줄이 있는 card를 커밋하지 않는다.
* Phase 3 승인 질문을 올릴 때 A2-③을 빼고(위 1), 사용자에게 "A2-③은 B26 묶음 [card phase]로 이미 답하셨다"는 한 줄만 맥락으로 둔다(다시 묻지 않는다).

## 추가(2026-10-01 T0·D0a 키트)

- T0 V5: 시제품 기준 weakening_diff 발견 = 리터럴 변경 3 + 비교 완화 1(유일성 단언 `len(...) == 1`). Phase 3 승인 질문/T0 승인 기록 범위 설명에 '비교 완화 1건'을 명시해야 한다(질문 올리기 전 확인).
- D0a 착수 조건: G1 계약 0에 `SourceIndex.tree(path)` 공개 이름 추가(G1 키트 agent에 지시함). G1 card 해시가 바뀌므로 Phase 3 질문 머리 해시 재계산.

## 추가(2026-10-02 D0b v8.4 정렬)

- D0b-8: 레지스트리 표에 파일 열이 없어 `〃`가 다른 파일 행에서 이어져 `_kv_table`(HTML 표 도우미)이 규칙상 MOD4(gmid_sizing_engine)로 감 -- 계층 위반 없음, 책임 불일치. 오케스트레이터 기본안: 백로그로 넘기지 말고 Phase 3 승인 질문 전에 UD-0 개정 문안(p3_doc_amendments.md) N3.10 MOD9 행에 `_kv_table` 토큰을 더해 UD-0 승인 범위로 닫는다(D-11 사용자 승인 = UD-0 승인). v8.4 검토 결과 반영 때 함께 처리.
