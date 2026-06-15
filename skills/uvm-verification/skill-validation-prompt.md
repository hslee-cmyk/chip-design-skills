# uvm-verification SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 reference 파일 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 절차적 워크플로우 가이드 + 코딩 패턴 예제 포함.

---

## Check 1: 참조 경로 무결성

**대상**: SKILL.md에 나열된 모든 참조 파일 경로

**절차**:
1. SKILL.md에서 `references/` 및 `assets/` 경로를 모두 추출
2. 각 경로가 파일시스템에 실존하는지 확인
3. 예상 파일 목록:
   - `references/component-templates.md`
   - `references/sequence-patterns.md`
   - `references/coverage-guide.md`
   - `references/debug-guide.md`
   - `references/ral-guide.md`
   - `references/testbench-architecture.md`
   - `references/consistency-map.md`
   - `assets/agent-template/` (디렉토리)

**PASS 조건**: 모든 참조 경로가 실존
**FAIL 시**: 누락 파일/디렉토리 목록 출력

---

## Check 2: 워크플로우-참조 정합

**대상**: SKILL.md 워크플로우 10단계

**절차**:
1. 워크플로우 각 단계의 내용이 reference 파일과 부합하는지:
   - `1. 스펙 분석` → coverage-guide (coverage 목표), verilog-rtl skill (cross-skill)
   - `2. TB 아키텍처 설계` → testbench-architecture §1,§6 (dual-top, config)
   - `3. 인터페이스 정의` → testbench-architecture §2 (DUT connection 패턴 3종)
   - `4. 트랜잭션 설계` → component-templates > Transaction (request=rand, response=NOT rand)
   - `5. Agent 구현` → component-templates > Driver, Monitor, Agent
   - `6. Env 통합` → component-templates > Predictor, Scoreboard, Env, Analysis Pipeline
   - `7. Register Model` → ral-guide (전체)
   - `8. 시퀀스 설계` → sequence-patterns (전체)
   - `9. 테스트 작성` → testbench-architecture §7,§8 (factory, objection), component-templates > Test
   - `10. Coverage 분석` → coverage-guide (UVM subscriber), verilog-rtl skill (cross-skill)
2. "UVM 계층 구조" 다이어그램이 component-templates의 클래스 계층과 일치하는지 (predictor, reg_block 포함)
3. "핵심 Phase 순서" 가 component-templates 각 컴포넌트의 phase 사용과 일치하는지 (extract/check 포함)
4. "핵심 원칙" 5가지가 reference 파일 내용과 부합하는지

**PASS 조건**: 워크플로우가 reference 파일 내용과 부합
**FAIL 시**: 불일치 단계, SKILL.md 문구, reference 실제 내용을 나란히 출력

---

## Check 3: 코드 예제 검증

**대상**: SKILL.md 및 모든 reference 파일의 SystemVerilog 코드 블록

**절차**:
1. "필수 코딩 패턴" 섹션의 포인터가 유효한지 (component-templates.md 참조)
2. component-templates.md 내 코드 예제가 SKILL.md 본문 원칙과 모순되지 않는지:
   - **컴포넌트 등록**: `uvm_component_utils` 매크로, `new(string name, uvm_component parent)` 시그니처
   - **트랜잭션 등록**: `uvm_object_utils` 매크로, rand 필드, constraint
   - **Config DB**: `set`/`get` 패턴, `uvm_fatal` 에러 처리
3. 코드에서 사용하는 UVM 매크로/클래스명이 본문 설명과 일치하는지
4. uvm_field_*/uvm_do_* 매크로가 SKILL.md/reference에서 사용되지 않는지 (Anti-pattern 예시 제외)
5. reference 파일 내 코드 블록도 동일 기준 적용:
   - `references/sequence-patterns.md` — Sequence 코드 (start_item/finish_item)
   - `references/ral-guide.md` — RAL 코드 (uvm_reg_block, uvm_mem)
   - `references/testbench-architecture.md` — TB 구조 코드
   - `references/coverage-guide.md` — Coverage 코드 (uvm_subscriber)

**PASS 조건**: 코드 예제가 UVM 규약을 따르고 본문/reference와 모순 없음
**FAIL 시**: 위반 코드 블록, 문제점, 수정 제안을 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 6개 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:
   - `uvm_test` / `uvm_env` / `uvm_agent` — 클래스명 정확성
   - `uvm_driver` / `uvm_monitor` / `uvm_sequencer` — 일관
   - `uvm_scoreboard` / `uvm_subscriber` — 역할 구분
   - `uvm_predictor` / `uvm_reg_predictor` — 일반 predictor vs RAL predictor
   - `uvm_reg_block` / `uvm_reg` / `uvm_reg_field` — RAL 계층
   - `uvm_component_utils` / `uvm_object_utils` — 매크로 정확성
   - `uvm_config_db` / `config_db` — 표기 일관
   - `build_phase` / `connect_phase` / `run_phase` / `extract_phase` / `check_phase` / `report_phase` — 이름 정확
   - `top-down` (build) / `bottom-up` (connect) — 실행 순서 설명 일관
   - `active` / `passive` Agent — 표기 일관
   - `TLM` / `analysis port` — 통신 메커니즘 용어
   - `Sequence` / `Virtual Sequence` — 구분 일관
   - `start_item` / `finish_item` vs `uvm_do_*` — 권장/금지 일관
   - `Explicit prediction` / `Auto prediction` / `Passive prediction` — 용어 일관
2. Reference 파일 간 동일 개념에 다른 용어 사용 탐지

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 파일 위치를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map의 모든 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인
2. consistency-map의 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인
3. Cross-Skill 참조가 대상 skill에 실존하는지:
   - `chip-verification` > interface-mapping (RTL-TB 인터페이스)
   - `chip-verification` > refmodel-patterns (Scoreboard/Ref Model)
   - `verilog-rtl` > covergroup-patterns (SV Covergroup 문법)
   - `verilog-rtl` > coverage-methodology (Coverage 이론)
   - `verilog-rtl` > coverage-examples (실전 예제)
4. SKILL.md에 있지만 consistency-map에 누락된 원칙이 없는지 확인
5. 신규 원칙 17개가 모두 맵에 반영되었는지 확인

**PASS 조건**: 맵의 모든 항목이 실제 파일 구조와 일치, 역방향 누락 없음
**FAIL 시**: 불일치 항목과 실제 위치를 출력; 역방향 누락 시 추가할 원칙 목록 제안

---

## Check 6: Best Practices 준수

**대상**: SKILL.md frontmatter + body 전체

**절차** (Anthropic "Complete Guide to Building Skills" 기준 보강):

1. **SKILL.md 크기 (Anthropic 공식 기준: 5,000 words 이하)**:
   - frontmatter 포함 전체 단어 수 측정 (`wc -w SKILL.md`)
   - 보조 지표: body 줄 수 ≤ 500줄 (자체 기준, 가독성 관리용)
   - **초과 시 대응 절차**:
     1. 상세 예시, 체크리스트 세부, 긴 코드 블록 → `references/`로 분리하고 SKILL.md에 포인터만 유지
     2. 표준 지식(Standard Knowledge) 제거 — Claude가 이미 아는 문법/패턴은 인라인 불필요
     3. 분리 후에도 초과 시 → 섹션별 단어 수 측정하여 가장 큰 섹션부터 reference 추출
     4. 규칙 테이블, 판단 기준, 핵심 원칙 1줄 요약은 SKILL.md에 유지 (분리 불가)
   - FAIL: 5,000 words 초과 + 분리 가능한 내용이 남아있음
2. **간결성 (No Standard Knowledge)**: Claude가 이미 아는 표준 문법/패턴이 인라인되지 않았는지 (표준 SV syntax, UVM 기본 코드 등 → 제거 또는 reference 포인터)
3. **Progressive Disclosure (3단계 구조)**:
   - **1단계 (frontmatter)**: 트리거 판단에 필요한 최소 정보만. 항상 시스템 프롬프트에 로드됨.
   - **2단계 (SKILL.md body)**: 핵심 규칙과 지침. skill이 활성화될 때 로드됨.
   - **3단계 (references/)**: 상세 예시, 체크리스트 세부, 긴 코드. 필요 시에만 참조.
   - 15줄 이상 코드 블록 인라인 금지 → reference로 분리
   - 핵심 지침(Critical)은 SKILL.md **상단**에 배치 (하단에 묻히면 무시될 수 있음)
4. **Description 필드 (Anthropic 공식 규칙)**:
   - 구조: `[What it does] + [When to use it/trigger phrases] + [Key capabilities]`
   - description ≤ 1024자
   - XML 태그 (`<`, `>`) 금지 — frontmatter가 시스템 프롬프트에 삽입되므로 injection 위험
   - 다른 skill 직접 참조 금지 (→ body의 Cross-Skill 섹션에 배치)
   - BAD: "Helps with projects" (너무 모호), "Implements entity model" (트리거 없음)
   - GOOD: 구체적 동작 + 사용자가 말할 수 있는 trigger phrases 포함
5. **장식용 ASCII 최소화**: 순수 장식용 ASCII box 과도 사용 금지. 구조적 다이어그램/트리는 허용.
6. **압축 vs 명확성 균형**: 규칙의 의미가 모호해지면 reference로 분리.
   - reference 분리 가능: 상세 예시, 체크리스트 세부, 긴 prose
   - SKILL.md 유지 필수: 규칙 테이블, 판단 기준, 핵심 원칙 1줄 요약
   - FAIL: "무엇을 해야 하는지" 즉시 이해 불가하면 과도 압축
7. **Composability (공존성)**: skill이 다른 skill과 동시 활성화될 수 있음을 가정. 다른 skill의 영역을 침범하는 지침이 없는지 확인.
8. **폴더 구조**: skill 폴더 내에 README.md가 없는지 확인 (모든 문서는 SKILL.md 또는 references/에 배치).

**PASS 조건**: 8개 항목 모두 충족
**FAIL 시**: 위반 항목, 현재 상태, 권장 개선을 출력

---

## 실행 결과 보고 형식

```
=== uvm-verification SKILL.md 일관성 검증 결과 ===
대상: uvm-verification SKILL.md
일시: [날짜]

Check 1 (참조 경로): PASS / FAIL
  - [상세 내용]

Check 2 (워크플로우-참조): PASS / FAIL
  - [상세 내용]

Check 3 (코드 예제): PASS / FAIL
  - [상세 내용]

Check 4 (용어 일관성): PASS / FAIL
  - [상세 내용]

Check 5 (consistency-map): PASS / FAIL
  - [상세 내용]

Check 6 (Best Practices): PASS / FAIL
  - [상세 내용]

총 결과: X/6 PASS
```

---

## 수정 후 재검증

검증에서 FAIL이 발견되면:
1. SKILL.md 또는 reference 파일 수정
2. 동일 검증을 재실행
3. 전체 PASS 확인 후 consistency-map.md 변경 이력에 기록
