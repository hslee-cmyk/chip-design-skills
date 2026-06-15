# SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 수정 후, 병렬 agent로 아래 검증을 실행하여 내부 모순을 사전 차단한다.
> **실행 방법**: 수정된 SKILL.md 경로를 지정하고 아래 체크를 순서대로 수행한다.

---

## 적용 범위

모든 5개 skill에 **개별 검증 프롬프트**가 존재한다. 이 파일은 공통 Check 정의 원본이며, 각 skill 폴더의 `skill-validation-prompt.md`가 실제 실행 프롬프트이다.

| Skill | 개별 프롬프트 | Check 특성 |
|-------|-------------|-----------|
| verilog-rtl | `verilog-rtl/skill-validation-prompt.md` | 참조마커, 요약vs상세, 코드예제, 용어, map, BP (규칙 중복 구조) |
| verilog-a | `verilog-a/skill-validation-prompt.md` | 참조마커, 요약vs상세, 코드예제, 용어, map, BP (규칙 중복 구조) |
| chip-verification | `chip-verification/skill-validation-prompt.md` | 참조경로, 워크플로우-참조, 다이어그램, 용어, map, BP (절차적 구조) |
| lattice-fpga | `lattice-fpga/skill-validation-prompt.md` | 참조경로, 워크플로우-참조, 다이어그램, 용어, map, BP (절차적 구조) |
| uvm-verification | `uvm-verification/skill-validation-prompt.md` | 참조경로, 워크플로우-참조, 코드예제, 용어, map, BP (절차적+코드) |

---

## Check 1: 참조 마커 무결성

**대상**: `[→§X]` 마커가 포함된 모든 줄

**절차**:
1. SKILL.md에서 `[→§` 패턴을 모두 추출
2. 각 마커가 가리키는 섹션 번호(§1, §2, ... 또는 §1.CDC 등)가 SKILL.md 내에 실존하는지 확인
3. 서브토픽 마커(§X.Topic)의 경우, 해당 섹션 내에 Topic 관련 내용이 실제로 존재하는지 확인

**PASS 조건**: 모든 마커가 실존하는 섹션을 가리킴
**FAIL 시**: 잘못된 마커 목록과 올바른 섹션 번호 제안을 출력

---

## Check 2: 요약 vs 상세 일치

**대상**: 요약 Zone(필수규칙 테이블, 핵심원칙 Box, 체크리스트, Quick Reference)

> **개별 프롬프트 작성 원칙**: 각 skill의 프롬프트에서는 Zone 이름과 섹션 번호(§X)를 명시적으로 열거할 것. 일반적 "요약 Zone" 표현 대신 해당 skill의 실제 섹션명으로 구체화.

**절차**:
1. 요약 Zone의 각 항목을 추출 (개별 프롬프트에서 Zone과 섹션 번호 명시)
2. `[→§X]` 마커가 가리키는 상세 섹션의 내용을 읽음
3. 요약 문구와 상세 내용이 **의미적으로 동일**한지 비교
   - 허용: 축약, 동의어
   - 불허: 반대 의미, 누락된 조건, 추가된 조건

**PASS 조건**: 모든 요약 항목이 상세 내용과 의미 일치
**FAIL 시**: 불일치 항목, 요약 문구, 상세 문구를 나란히 출력

---

## Check 3: 코드 예제 준수

**대상**: SKILL.md 내 모든 코드 블록 + **reference 파일 내 코드 블록** (동일 기준 적용)

> **개별 프롬프트 작성 원칙**: 각 skill의 프롬프트에서는 대조할 규칙 항목(섹션명 포함)과 검증 대상 reference 파일 목록을 명시적으로 열거할 것.

**절차**:
1. SKILL.md 및 모든 reference 파일의 코드 예제를 추출
2. SKILL.md 자체 규칙과 대조 (개별 프롬프트에서 규칙 항목과 섹션 번호 명시)
3. GOOD 예제가 규칙을 준수하는지, BAD 예제가 실제로 규칙을 위반하는지 확인

**PASS 조건**: GOOD 예제 100% 규칙 준수, BAD 예제가 의도된 위반만 포함
**FAIL 시**: 위반 예제, 위반 규칙, 수정 제안을 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md 전체 텍스트 + 모든 reference 파일

> **개별 프롬프트 작성 원칙**: 각 skill의 프롬프트에서는 핵심 용어 목록(허용 표기 / 금지 표기)과 교차 검증할 reference 파일명을 명시적으로 열거할 것. 일반적 "불일치 탐지"로는 누락이 발생함.

**절차**:
1. 개별 프롬프트에 명시된 핵심 용어 목록을 기준으로 SKILL.md 전체에서 표기 확인
2. 동일 개념에 대해 다른 용어를 사용하는 경우 탐지
3. 개별 프롬프트에 열거된 reference 파일과 SKILL.md 간 용어 불일치 교차 검증

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍, 파일 위치, 권장 통일 용어를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

> **개별 프롬프트 작성 원칙**: 각 skill의 프롬프트에서는 검증 대상 원칙 목록과 reference 파일 경로를 명시적으로 열거할 것. 일반적 절차만으로는 원칙 누락을 탐지할 수 없음.

**절차**:
1. consistency-map에 기록된 모든 원칙의 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인
2. consistency-map의 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인
3. reference 파일 경로가 실제로 존재하는지 확인 (개별 프롬프트에 경로 목록 명시)
4. **역방향 확인**: SKILL.md에 존재하는 원칙이 consistency-map에 누락되지 않았는지 확인

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
=== SKILL.md 일관성 검증 결과 ===
대상: [skill명] SKILL.md
일시: [날짜]

Check 1 (참조 마커): PASS / FAIL
  - [상세 내용]

Check 2 (요약 vs 상세): PASS / FAIL
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
1. SKILL.md를 수정
2. 동일 검증을 재실행
3. 전체 PASS 확인 후 consistency-map.md 변경 이력에 기록
