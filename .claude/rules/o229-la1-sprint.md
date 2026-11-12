# 임시 규칙 O-229 — LA-1(card LA-1a + LA-1) 병합까지, 세션이 바뀌어도 적용

> 정본. 2026-11-12 P-INSTR-CONCISE로 압축(의미 동일 — 독립 판정 기록: docs/01-plan/features/rules-compression.verdicts.md). 옛 원문은 git 이력 `e9d8bc55`.
> 기한이 있는 규칙이다 — 의무 `o229-la1-sprint`(.ai/obligations.yaml)로 수명을 관리한다.

원칙 1–33·계획 문언(예: P:1511 '매 변경 뒤 전체')보다 우선. 끝나면 LA-1 재점검(O-225). 모든 agent 브리핑에 포함.
1. 완화 금지: 물리 정합(원칙 1·6, E-0 물리 관문, fail-closed)·graph 단일 정본·단일화(원칙 7, 상위 `fpga/CLAUDE.md`). 위반 = 언제나 정지.
2. test는 원인 규명 범위만: 그 card test(toy·회귀) + `tests/structure` + 2회로 smoke(`folded_cascode`, `ngcc_3stage_ff`;
   stage_b·s0·g10 파일을 `--run-slow -k`) + `search/test_canonical_order.py`. 전체 test는 LA-1 측정 때 1회.
   판정 기록에 돌린 범위를 적고, 안 돌린 것은 통과로 세지 않음. 엔진 card는 ngspice 없음, 오라클 card(OP-3, OP-7 어댑터, OP-5)는
   ngspice 기준선 대조 1회만(O-232).
3. card 뒤엔 필수만: 독립 판정 1회(author ≠ verifier), 재판정은 Major 수정 때만. Major = 물리 정합·graph 정본 위반, fail-open,
   기준 약화, 엔진 변경 누출, 범위 위반, 2번 test 실패. 그 밖의 지적은 왕복 없이 `wt/_drafts/la1_auto_decisions.md`(LA-1 재점검 입력).
4. 새 검증 도구·인프라·부가 측정은 만들지도 제안하지도 않음(LA-1을 실제로 막을 때만 예외).
5. 유지: O-226 위임과 위임 밖 항목(push, 저장소 밖 공유, 근본원칙 변경, topology connectivity, 기준 약화로 test 통과), bkit 순서, F절.
6. LA-1 뒤: 이 규칙 해제 → 전체 test + 전체 모순 점검 → 한 번 더 수정(여기로 넘긴 지적은 모두 그 입력).
7. LA-1까지 승인 위임: 계획·design·card 승인과 병합은 사용자에게 묻지 않고 오케스트레이터가 권고대로 채택해
   `la1_auto_decisions.md`에 기록. 사용자에게는 5번의 위임 밖 항목만.
   한계(O-267 — 원칙 19·20 재확인, O-266 대체): 계획의 규칙·정의·결정 문언 개정은 병합 전 사용자에게 묻는다
   (옛→새·이유·독립 판정·결정 간 모순 점검 첨부) — 위임은 그 질문을 건너뛰는 근거가 아니다. code·design·card·test 작성과 판정·병합은 위임대로
   (원칙 8·9 — 원칙에 맞지 않는 code는 덧대지 말고 재작성).
