# verilog-a SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 reference 파일 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 규칙 중복 구조 — 핵심 원칙 Box, 체크리스트, Quick Reference에 동일 규칙이 반복 기술됨.

---

## Check 1: 참조 마커 무결성

**대상**: `[→§X]` 마커가 포함된 모든 줄

**절차**:
1. SKILL.md에서 `[→§` 패턴을 모두 추출
2. 각 마커가 가리키는 섹션 번호(§1~§8 또는 §X.Topic)가 SKILL.md 내에 실존하는지 확인
3. 서브토픽 마커의 경우, 해당 섹션 내에 Topic 관련 내용이 실제로 존재하는지 확인

**PASS 조건**: 모든 마커가 실존하는 섹션을 가리킴
**FAIL 시**: 잘못된 마커 목록과 올바른 섹션 번호 제안을 출력

---

## Check 2: 요약 vs 상세 일치

**대상**: 3개 요약 Zone

**절차**:
1. 아래 3개 Zone의 각 항목을 추출:
   - **핵심 원칙 Box** (상단) — 4개 핵심 원칙 (continuous output, transition, feedback 연속성, floating node)
   - **체크리스트** (§9) — 작성 전/작성 후 확인 항목
   - **Quick Reference** (맨 하단) — Key Rule #1~#9
2. `[→§X]` 마커가 가리키는 상세 섹션의 내용을 읽음
3. 요약 문구와 상세 내용이 **의미적으로 동일**한지 비교
   - 허용: 축약, 동의어
   - 불허: 반대 의미, 누락된 조건, 추가된 조건

**PASS 조건**: 모든 요약 항목이 상세 내용과 의미 일치
**FAIL 시**: 불일치 항목, 요약 문구, 상세 문구를 나란히 출력

---

## Check 3: 코드 예제 준수

**대상**: SKILL.md + 3개 reference 파일 내 모든 코드 블록 (```verilog-a, ```verilog 등)

**절차**:
1. 모든 코드 예제를 추출
2. SKILL.md 자체 규칙과 대조:
   - **transition() 사용** (§2, §4): 이산 신호에 transition() 필터 적용 여부
   - **연속성** (§3): piecewise-linear 대신 smooth 함수 (tanh, limexp) 사용 여부
   - **Floating node 방지** (§3): 고임피던스 경로에 누설 저항 포함 여부
   - **피드백 연속성** (§3): 값+기울기 연속성 유지 여부
   - **초기 조건** (§5): @(initial_step)에서 적절한 초기 조건 제공 여부
3. GOOD 예제가 규칙을 준수하는지, BAD 예제가 실제로 규칙을 위반하는지 확인
4. reference 파일 내 코드 블록도 동일 기준 적용:
   - `references/coding-guideline.md` — 코딩 가이드라인 예제
   - `references/convergence-issues.md` — 수렴 문제 예제
   - `references/common-models.md` — 공통 회로 모델 예제

**PASS 조건**: GOOD 예제 100% 규칙 준수, BAD 예제가 의도된 위반만 포함
**FAIL 시**: 위반 예제, 위반 규칙, 수정 제안을 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 3개 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:
   - `transition()` — 함수 표기 일관 (괄호 포함)
   - `limexp()` / `tanh()` — smooth 함수 표기 일관
   - `$bound_step` — 시스템 함수 표기 일관
   - `cross()` / `above()` — 이벤트 함수 표기 일관
   - `@(initial_step)` — 이벤트 표기 일관
   - `piecewise-linear` — 하이픈 표기 일관 (piecewise linear vs piecewise-linear)
   - `Newton-Raphson` — 대문자·하이픈 일관
   - `continuous` / `discrete` — 신호 분류 용어 일관
   - `behavioral` — 철자 일관 (behavioral vs behavioural)
   - `convergence` / `수렴` — 한영 혼용 일관
   - `analog operator` — 용어 일관 (ddt, idt, transition 등)
   - `tolerance` / `abstol` / `nature` — Verilog-A 고유 용어 일관
2. 3개 reference 파일 간 동일 개념에 다른 용어 사용 탐지:
   - `references/coding-guideline.md`
   - `references/convergence-issues.md`
   - `references/common-models.md`

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 파일 위치를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map에 기록된 11개 원칙의 모든 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인
2. consistency-map의 모든 "SKILL.md 내부 요약" 항목이 해당 위치에 실존하는지 확인
3. consistency-map의 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인
4. 원칙 목록:
   - Continuous output only, Discrete → transition()
   - Feedback 연속성 (값+기울기), Floating node 방지
   - 4-state logic (===), cross/above 최소화
   - transition delay=0 tr/tf 최대화, Piecewise-linear → smooth 함수
   - 초기 조건 제공 (@initial_step), 파라미터 범위 정의
   - 공통 회로 모델
5. Cross-Skill 참조가 대상 skill에 실존하는지:
   - `chip-verification > analog-model-levels`
   - `chip-verification > connect-modules`
6. reference 파일 경로가 실제로 존재하는지 확인:
   - `references/coding-guideline.md`
   - `references/convergence-issues.md`
   - `references/common-models.md`
   - `references/consistency-map.md`
7. SKILL.md에 있지만 consistency-map에 누락된 원칙이 없는지 확인

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
=== verilog-a SKILL.md 일관성 검증 결과 ===
대상: verilog-a SKILL.md
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
1. SKILL.md 또는 reference 파일 수정
2. 동일 검증을 재실행
3. 전체 PASS 확인 후 consistency-map.md 변경 이력에 기록
