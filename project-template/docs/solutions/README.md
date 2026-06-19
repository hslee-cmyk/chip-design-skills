# docs/solutions — 프로젝트 단기 지식 (RTL 자산화)

이 프로젝트에서 해결한 **비자명 RTL 문제**를 분류·검증 가능한 자산으로 기록한다.
2-tier 지식 시스템의 **단기·프로젝트 계층** (관계 탐색은 graphify, 자세히 `.ai/KNOWLEDGE_MAP.md`).

> 일반화된 원칙은 여기 두지 않는다 — 정본 `chip-design-skills/kb-global/principles/`(git, 장기·전역)로 격상한다.

## 카테고리 (problem_type → 폴더) = AI Verilog Failure Taxonomy T1..T9
`protocol-spec`(T1) `port-integration`(T2) `clock-reset-cdc`(T3) `timing-cycle`(T4)
`fsm-corner`(T5) `pointer-handshake`(T6) `structure-style`(T7) `fpga-ram`(T8)
`width-truncation`(T9) `toolflow`(툴/환경). 전체 enum: `schema.yaml`.

## 워크플로우
1. 버그 해결 확인 → 해당 `T*/` 폴더에 `[증상]-[module]-[YYYYMMDD].md` 작성(frontmatter).
2. 검증: `"$KB_PY" docs/solutions/validate.py`.
3. bkit 동기: `"$KB_PY" docs/solutions/sync_rules.py` → `regression-rules.json`.
4. **일반화**(3건+/원칙)되면 → 정본 `chip-design-skills/kb-global/principles/`(git)에 추가·push
   → `kb_index.py` 재색인(전 프로젝트 공유). 런타임 `.tools/kb-global`엔 쓰지 않는다.

`$KB_PY` = `fpga/.tools/kb-venv/Scripts/python.exe` (공유 venv). 착수 전 조회는 `.ai/rag/preflight.py`.
