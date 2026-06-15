# chip-verification SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 reference 파일 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 절차적 워크플로우 가이드 — 규칙 중복 Zone 없음.

---

## Check 1: 참조 경로 무결성

**대상**: SKILL.md에 나열된 모든 참조 파일 경로

**절차**:
1. SKILL.md에서 `references/` 및 `assets/` 경로를 모두 추출
2. 각 경로가 파일시스템에 실존하는지 확인
3. 예상 파일 목록:
   - `references/interface-mapping.md`
   - `references/refmodel-patterns.md`
   - `references/debug-flow.md`
   - `references/regression-strategy.md`
   - `references/analog-model-levels.md`
   - `references/connect-modules.md`
   - `references/wreal-modeling.md`
   - `references/spectre-integration.md`
   - `references/consistency-map.md`
   - `assets/tb-template/` (디렉토리)

**PASS 조건**: 모든 참조 경로가 실존
**FAIL 시**: 누락 파일/디렉토리 목록 출력

---

## Check 2: 워크플로우-참조 정합

**대상**: SKILL.md 워크플로우 섹션 (공통 6단계 + AMS 4단계)

**절차**:
1. 워크플로우 각 단계에서 참조하는 reference 파일을 추출:
   - `1. RTL 설계 → verilog-rtl skill`
   - `2. Interface → interface-mapping.md`
   - `3. Ref Model → refmodel-patterns.md`
   - `4. Scoreboard → assets/tb-template/`
   - `5. 디버깅 → debug-flow.md`
   - `6. 회귀 테스트 → regression-strategy.md`
   - `A1. 아날로그 모델 → analog-model-levels.md`
   - `A2. Connect Module → connect-modules.md`
   - `A3. Wreal → wreal-modeling.md`
   - `A4. Spectre → spectre-integration.md`
2. 각 reference 파일의 주요 내용이 워크플로우 단계 설명과 의미적으로 부합하는지 확인
3. 아날로그 모델 교체 섹션의 3단계(Behavioral/Wreal/Spectre)가 analog-model-levels.md 내용과 일치하는지 확인

**PASS 조건**: 워크플로우 참조가 대상 파일 내용과 부합
**FAIL 시**: 불일치 단계, SKILL.md 문구, reference 실제 내용을 나란히 출력

---

## Check 3: 다이어그램/코드 일관성

**대상**: SKILL.md 내 ASCII 다이어그램 및 코드 블록 + reference 파일 내 다이어그램/코드

**절차**:
1. 듀얼탑 아키텍처 다이어그램의 구성 요소가 본문과 일치하는지:
   - `hdl_top.sv` = DUT + Interface Layer
   - `hvl_top.sv` = UVM Environment (Agent, Reference Model, Scoreboard)
   - Clock/Reset generation 위치
   - virtual interface 연결 방향
2. 프로젝트 타입 선택 다이어그램의 참조 파일 목록이 "참조 파일" 섹션과 일치하는지
3. 컴파일 옵션 코드 블록(`make sim ANALOG_MODEL=...`)이 아날로그 모델 교체 설명과 일치하는지
4. reference 파일 내 다이어그램/코드 블록도 동일 기준 적용:
   - `references/interface-mapping.md` — 인터페이스 구조 다이어그램
   - `references/refmodel-patterns.md` — Reference Model 패턴 코드
   - `references/analog-model-levels.md` — 3단계 모델 구조

**PASS 조건**: SKILL.md 및 reference 파일의 다이어그램/코드가 본문과 모순 없음
**FAIL 시**: 불일치 요소와 위치를 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 8개 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:
   - `hdl_top` / `hvl_top` — 대소문자, 파일 확장자(.sv) 포함 여부
   - `chip_top` — .v 확장자 일관성
   - `Behavioral` / `Wreal` / `Spectre` — 대문자 표기 일관
   - `Connect Module` — 단수/복수
   - `config_db` — 형식 (uvm_config_db vs config_db)
   - `DUT` / `Interface` / `Virtual Interface` — 약어 일관
   - `active/passive` Agent — 표기 일관
   - `Digital 전용` vs `Mixed-Signal (AMS)` — 구분 용어
2. reference 파일 간 동일 개념에 다른 용어 사용 탐지

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 파일 위치를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map의 모든 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인
2. consistency-map의 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인
3. Cross-Skill 참조가 대상 skill에 실존하는지:
   - `verilog-rtl` — RTL 설계 규칙, FSM 패턴
   - `uvm-verification` — UVM 컴포넌트
4. SKILL.md에 있지만 consistency-map에 누락된 원칙이 없는지 확인

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
=== chip-verification SKILL.md 일관성 검증 결과 ===
대상: chip-verification SKILL.md
일시: [날짜]

Check 1 (참조 경로): PASS / FAIL
  - [상세 내용]

Check 2 (워크플로우-참조): PASS / FAIL
  - [상세 내용]

Check 3 (다이어그램/코드): PASS / FAIL
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
