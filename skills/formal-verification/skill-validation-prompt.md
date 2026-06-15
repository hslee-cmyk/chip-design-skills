# formal-verification Skill Validation Prompt

## 검증 방법

아래 6개 Check를 순서대로 실행하고 각 결과를 PASS/FAIL로 보고한다.

---

## Check 1: 참조 마커 유효성

**대상**: SKILL.md에 있는 모든 `references/` 포인터

**절차**:
1. SKILL.md에서 `references/` 경로를 모두 추출
2. 각 파일이 파일시스템에 실존하는지 확인:
   - `references/smt-solvers.md`
   - `references/directives.md`
   - `references/bmc-prove-cover.md`
   - `references/sby-workflow.md`
   - `references/sva-patterns.md`
   - `references/consistency-map.md`
3. SKILL.md의 포인터 텍스트와 실제 파일명 일치 여부 확인

**PASS 조건**: 모든 참조 경로가 실존하고 포인터 텍스트와 파일명이 일치
**FAIL 시**: 누락 파일 또는 불일치 포인터 목록 출력

---

## Check 2: 요약 vs 상세 분리

**대상**: SKILL.md 본문의 포인터 역할 준수 + 핵심 요약 섹션의 의미 일치

**절차**:
1. 15줄 이상 코드 블록이 SKILL.md에 인라인으로 포함되지 않았는지 확인
2. 반복 내용(SKILL.md에도 있고 ref에도 있는 상세 내용)이 없는지 확인
3. 핵심 요약 섹션의 의미가 상세 내용(reference)과 일치하는지 확인:
   - **§2 Formal Directives 표** (assert/assume/cover/restrict 상태공간 영향) → `references/directives.md`와 의미 일치
   - **§3 검증 모드 요약** (BMC/Cover/Prove 설명) → `references/bmc-prove-cover.md`와 의미 일치
   - **§8 결과 해석 표** (PASS/FAIL/UNREACHABLE/ERROR 의미) → 실제 sby 동작과 일치
   - 허용: 축약, 동의어
   - 불허: 반대 의미, 누락된 조건, 추가된 조건

**PASS 조건**: 15줄 초과 인라인 코드 없음, 반복 내용 없음, 요약-상세 의미 일치
**FAIL 시**: 위반 항목, 불일치 요약 문구, 상세 문구를 나란히 출력

---

## Check 3: 코드 예제 정확성

**대상**: SKILL.md 및 모든 reference 파일의 코드 블록

**절차**:
1. SKILL.md 내 코드 블록 검증:
   - `` `ifdef FORMAL `` 블록: `` `endif `` 쌍 확인
   - `always @(posedge clk)` 블록 구조 확인
   - assert/assume/cover 인자 괄호 확인
   - `.sby` 파일 예시: `[options]`, `[engines]`, `[script]`, `[files]` 섹션 존재
2. reference 파일 내 코드 블록도 동일 기준 적용:
   - `references/sby-workflow.md` — .sby 형식, ifdef FORMAL 패턴
   - `references/directives.md` — assert/assume/cover/restrict 예제
   - `references/bmc-prove-cover.md` — 검증 모드 코드 예제
   - `references/sva-patterns.md` — SVA 문법 (|->，|=>，##N, disable iff)

**PASS 조건**: 모든 코드 블록이 문법적으로 올바름
**FAIL 시**: 위반 코드 블록, 문제점, 수정 제안을 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 5개 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:

| 용어 | 허용 표기 | 금지 표기 |
|------|-----------|-----------|
| SymbiYosys | sby, SymbiYosys | SBY, symbiyosys |
| 반례 | CEX, 반례(CEX) | counterexample만 단독 |
| 검증 모드 | BMC, Prove, Cover (대문자) | bmc (일반 텍스트에서) |
| directive | assert, assume, cover, restrict | Assert, Assume |
| SVA implication | `\|->` (overlapping), `\|=>` (non-overlapping) | 방향 오기 또는 혼용 |
| SVA delay | `##N`, `##[m:n]` | 소문자 표기 |
| disable iff | `disable iff (!rst_n)` | 대문자, 하이픈 |
| f_past_valid | `f_past_valid` | 대소문자 혼용 |

2. 5개 reference 파일 간 동일 개념에 다른 용어 사용 탐지:
   - `references/smt-solvers.md`
   - `references/directives.md`
   - `references/bmc-prove-cover.md`
   - `references/sby-workflow.md`
   - `references/sva-patterns.md`

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 파일 위치를 출력

---

## Check 5: Consistency Map 동기화

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map의 각 행에서 `SKILL.md 위치` 섹션 번호가 실제 SKILL.md에 존재하는지 확인 (FV-01 ~ FV-14 전체)
2. consistency-map의 `Reference 위치`의 파일과 섹션이 실제 존재하는지 확인
3. reference 파일 경로가 실제로 존재하는지 확인:
   - `references/smt-solvers.md`
   - `references/directives.md`
   - `references/bmc-prove-cover.md`
   - `references/sby-workflow.md`
   - `references/sva-patterns.md`
   - `references/consistency-map.md`
4. **역방향 확인**: SKILL.md에 있는 원칙이 consistency-map에 누락되지 않았는지 확인
   - §6 Windows 주의사항 (FV-06, FV-07) 존재 여부
   - §10 SVA 섹션 (FV-12, FV-13, FV-14) 존재 여부

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
