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

**절차**:
1. 요약 Zone의 각 항목을 추출
2. `[→§X]` 마커가 가리키는 상세 섹션의 내용을 읽음
3. 요약 문구와 상세 내용이 **의미적으로 동일**한지 비교
   - 허용: 축약, 동의어
   - 불허: 반대 의미, 누락된 조건, 추가된 조건

**PASS 조건**: 모든 요약 항목이 상세 내용과 의미 일치
**FAIL 시**: 불일치 항목, 요약 문구, 상세 문구를 나란히 출력

---

## Check 3: 코드 예제 준수

**대상**: SKILL.md 내 모든 코드 블록 (```verilog, ```verilog-a 등)

**절차**:
1. 모든 코드 예제를 추출
2. SKILL.md 자체 규칙과 대조:
   - **verilog-rtl**: 네이밍 컨벤션(§4~§6), 할당 규칙(§2), latch 방지(§1,§7), 리셋 패턴(§1.Reset)
   - **verilog-a**: transition() 사용(§2,§4), 연속성(§3), floating node 방지(§3)
3. GOOD 예제가 규칙을 준수하는지, BAD 예제가 실제로 규칙을 위반하는지 확인

**PASS 조건**: GOOD 예제 100% 규칙 준수, BAD 예제가 의도된 위반만 포함
**FAIL 시**: 위반 예제, 위반 규칙, 수정 제안을 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md 전체 텍스트

**절차**:
1. 핵심 용어 목록 추출 (기술 용어, 약어, 명명 패턴)
2. 동일 개념에 대해 다른 용어를 사용하는 경우 탐지
   - 예: "2-FF synchronizer" vs "2단 동기화기" vs "double-flop" → 하나로 통일 필요
   - 예: "transition()" vs "transition 필터" → 문맥에 따라 허용 가능
3. references/ 파일과 SKILL.md 간 용어 불일치도 확인

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 권장 통일 용어를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map에 기록된 모든 섹션 위치(줄 번호 범위 또는 섹션명)를 추출
2. 실제 SKILL.md에서 해당 섹션이 존재하는지, 위치가 맞는지 확인
3. consistency-map에 누락된 섹션이 없는지 확인
4. reference 파일 경로가 실제로 존재하는지 확인

**PASS 조건**: 맵의 모든 항목이 실제 파일 구조와 일치
**FAIL 시**: 불일치 항목과 실제 위치를 출력

---

## Check 6: Best Practices 준수

**대상**: SKILL.md frontmatter + body 전체

**절차**:
1. **Body 줄 수 ≤ 500줄**: frontmatter(`---`...`---`) 이후의 body 줄 수 측정
2. **간결성 (No Standard Knowledge)**: Claude가 이미 알고 있는 표준 문법/패턴이 인라인 코드로 포함되지 않았는지 확인:
   - 표준 언어 문법 (기본 SystemVerilog/Verilog-A syntax)
   - 일반적으로 알려진 라이브러리 패턴 (UVM 기본 등록 코드 등)
   - 포인터로 대체 가능한 상세 코드 블록
3. **Progressive Disclosure**: 15줄 이상의 코드 블록이 인라인되지 않았는지 (긴 코드는 reference로 분리)
4. **Description 필드 정합**:
   - description에 `연관 skill:` 또는 다른 skill 직접 참조가 없는지 (→ body의 Cross-Skill 섹션에 배치)
   - description이 skill의 역할과 트리거를 기술하는지
5. **장식용 ASCII 최소화**: 순수 장식용 ASCII box (`━`, `┌┐└┘│├┤` 등)가 과도하지 않은지 (구조적 다이어그램/트리는 허용, 텍스트 테두리 장식은 markdown으로 대체)

**PASS 조건**: 5개 항목 모두 충족
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
