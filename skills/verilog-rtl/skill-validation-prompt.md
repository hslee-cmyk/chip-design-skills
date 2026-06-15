# verilog-rtl SKILL.md 일관성 검증 프롬프트

> **용도**: SKILL.md 또는 reference 파일 수정 후, 내부 모순을 사전 차단한다.
> **구조 특성**: 규칙 중복 구조 — 필수규칙 테이블, 체크리스트에 동일 규칙이 반복 기술됨.

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

**대상**: 3개 요약 Zone

**절차**:
1. 아래 3개 Zone의 각 항목을 추출:
   - **필수 규칙 테이블** (§1) — No Latches, Blocking, CDC, 단일 할당, Bit-Width Safety
   - **사이클 분석 요약** (§3) — pipe vs same-cycle 분류
   - **리뷰 체크리스트** (§10) — 합성/코딩스타일/타이밍/기능
2. `[→§X]` 마커가 가리키는 상세 섹션의 내용을 읽음
3. 요약 문구와 상세 내용이 **의미적으로 동일**한지 비교
   - 허용: 축약, 동의어
   - 불허: 반대 의미, 누락된 조건, 추가된 조건

**PASS 조건**: 모든 요약 항목이 상세 내용과 의미 일치
**FAIL 시**: 불일치 항목, 요약 문구, 상세 문구를 나란히 출력

---

## Check 3: 코드 예제 준수

**대상**: SKILL.md 내 모든 코드 블록 (```verilog, ```systemverilog)

**절차**:
1. 모든 코드 예제를 추출
2. SKILL.md 자체 규칙과 대조:
   - **네이밍 컨벤션** (§4~§6): prefix (r_, w_, c_, i_, o_), BSC postfix (_a, _z), top wire 네이밍
   - **할당 규칙** (§2): ff에 `<=`, comb에 `=`
   - **Latch 방지** (§1, §7): 기본값 할당 또는 if/case 완전성
   - **리셋 패턴** (§1.Reset): 비동기 리셋 코딩 스타일
   - **CDC 패턴** (§1.CDC): Slow→Fast에 2FF/Pulse Sync, Fast→Slow에 Handshake
3. GOOD 예제가 규칙을 준수하는지, BAD 예제가 실제로 규칙을 위반하는지 확인
4. reference 파일 내 코드 블록도 동일 기준 적용:
   - `references/fsm-patterns.md` — FSM 코드 예제
   - `references/cdc-patterns.md` — CDC 코드 예제
   - `references/naming-examples.md` — 네이밍 예제
   - `references/cycle-analysis.md` — 사이클 분석 예제

**PASS 조건**: GOOD 예제 100% 규칙 준수, BAD 예제가 의도된 위반만 포함
**FAIL 시**: 위반 예제, 위반 규칙, 수정 제안을 출력

---

## Check 4: 용어 일관성

**대상**: SKILL.md + 9개 reference 파일

**절차**:
1. 핵심 용어 목록 교차 검증:
   - `2-FF synchronizer` / `2단 동기화기` / `double-flop` — 통일 확인
   - `Pulse Synchronizer` — 방향 기술 (Slow→Fast) 일관
   - `Handshake` — 방향 기술 (Fast→Slow) 일관
   - `always_ff` / `always_comb` — 사용 맥락 일관
   - `Latch` — 방지 방법 표기 일관 (기본값 할당 또는 if/case 완전성)
   - `Blocking` / `Non-blocking` — 약어·한글 혼용 일관
   - `FSM` — 2-process 표기 일관
   - `prefix` / `postfix` — 네이밍 용어 일관
   - `BSC` — Boundary Scan Chain 풀네임·약어 일관
   - `pipe` / `same-cycle` — 사이클 분석 용어 일관
   - `Slow→Fast` / `Fast→Slow` — 화살표 표기 일관 (→ vs ->)
   - `covergroup` / `coverpoint` / `cross` — 표기 일관
   - `bin` / `bins` — 단수/복수 맥락 일관
   - `observation` / `observability` — 용어 맥락 일관
   - `functional coverage` / `code coverage` — 분류 용어 일관
2. 9개 reference 파일 간 동일 개념에 다른 용어 사용 탐지:
   - `review-checklist.md`, `naming-examples.md`, `cdc-patterns.md`
   - `fsm-patterns.md`, `synthesis-check.md`, `cycle-analysis.md`
   - `coverage-methodology.md`, `covergroup-patterns.md`, `coverage-examples.md`

**PASS 조건**: 핵심 용어가 일관되게 사용됨
**FAIL 시**: 불일치 용어 쌍과 파일 위치를 출력

---

## Check 5: consistency-map 정합성

**대상**: `references/consistency-map.md`

**절차**:
1. consistency-map에 기록된 모든 원칙(RTL 15개 + Coverage 13개)의 "SKILL.md 섹션" 항목이 실제 SKILL.md에 존재하는지 확인
2. consistency-map의 모든 "SKILL.md 내부 요약" 항목이 해당 위치에 실존하는지 확인
3. consistency-map의 모든 "reference 반영 위치" 항목이 실제 reference 파일에 존재하는지 확인
4. 원칙 목록:
   - 필수 규칙 테이블, Always 블록 유연성, CDC 방향 구분
   - 리셋 정책, Latch 방지, Blocking 규칙, 단일 할당 원칙
   - 네이밍 (Prefix, Top Wire, BSC, Clock/Reset)
   - FSM 작성 규칙, FSM 기본값, 사이클 분석, Coverage 목표
   - Coverage 분류, Observation 기반, Check 통과 시 유효, Code≠Functional 상호보완
   - 명시적 bin 설계, Cross ignore_bins, Spec→Testplan→Coverage, Coverage Closure
   - Covergroup 문법, Assertion Coverage, Coverage Options, 실전 예제, Coverage Space 2×2
5. reference 파일 경로가 실제로 존재하는지 확인:
   - `references/review-checklist.md`
   - `references/naming-examples.md`
   - `references/cdc-patterns.md`
   - `references/fsm-patterns.md`
   - `references/synthesis-check.md`
   - `references/cycle-analysis.md`
   - `references/consistency-map.md`
   - `references/coverage-methodology.md`
   - `references/covergroup-patterns.md`
   - `references/coverage-examples.md`
6. SKILL.md에 있지만 consistency-map에 누락된 원칙이 없는지 확인

**PASS 조건**: 맵의 모든 항목이 실제 파일 구조와 일치
**FAIL 시**: 불일치 항목과 실제 위치를 출력

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
=== verilog-rtl SKILL.md 일관성 검증 결과 ===
대상: verilog-rtl SKILL.md
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
