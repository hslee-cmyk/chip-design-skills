# Coverage Methodology

## 1. Coverage 이론

### 에러 검출 3조건

버그를 검출하려면 세 가지 조건이 **모두** 충족되어야 한다:

1. **Activate** — 버그를 포함한 코드 경로가 실행됨
2. **Propagate** — 버그의 영향이 관찰 가능한 지점까지 전파됨
3. **Monitor** — 관찰 지점에 checker가 존재하여 오류를 감지함

이 세 조건 중 하나라도 빠지면 버그는 잠복(latent)한다.

### Controllability vs Observability

- **Controllability**: DUT의 특정 상태/조건을 만들어낼 수 있는 능력 (stimulus 생성)
- **Observability**: DUT 내부 상태를 관찰하고 검증할 수 있는 능력 (checker/coverage)
- Coverage는 **observability** 측에 해당 — 얼마나 다양한 시나리오가 **관찰**되었는가

### Explicit vs Implicit Coverage

| 유형 | 정의 | 생성 주체 |
|------|------|----------|
| Explicit (Functional) | 검증 엔지니어가 의도적으로 정의한 coverage | 수동 (covergroup, cover property) |
| Implicit (Code) | 시뮬레이터가 RTL 구조에서 자동 추출 | 자동 (tool) |

### Specification-Derived vs Implementation-Derived

- **Spec-derived** (Functional): 스펙 요구사항에서 도출 → 기능 검증
- **Impl-derived** (Code): RTL 코드 구조에서 도출 → 코드 커버리지
- 두 가지는 **상호 보완** 관계: 한쪽만으로 완전하지 않음

### Coverage Space (2×2 분류)

위 두 축을 결합하면 4가지 coverage space를 형성:

| | Specification (스펙) | Implementation (구현) |
|---|---|---|
| **Explicit** (수동) | Functional coverage — 스펙 요구사항에서 수동 정의 | Instrumentation — 구현 동작 관찰용 수동 계측 (예: FIFO fill/empty) |
| **Implicit** (자동) | Auto-extracted from spec (학술 연구 영역) | Code coverage — RTL 모델에서 도구가 자동 추출 |

★ 실무 주요 영역: Explicit-Specification (functional) + Implicit-Implementation (code)
★ 100% code coverage ≠ 100% functional coverage — 상호 보완 필수

---

## 2. Code Coverage Metrics

| Metric | 설명 | 측정 대상 |
|--------|------|----------|
| **Toggle** | 신호 비트의 0→1, 1→0 전환 | 포트, 내부 신호 |
| **Line/Statement** | 실행된 코드 라인/구문 수 | HDL 소스 |
| **Block** | 실행된 연속 코드 블록 | begin-end 블록 |
| **Branch/Decision** | 조건문의 true/false 분기 실행 | if/else, case |
| **Expression/Condition** | 복합 Boolean 조건 내 각 부분조건의 true/false | `(a && b)` → a, b 각각 |
| **MC/DC (FEC)** | 각 조건이 독립적으로 결과에 영향 | DO-178B/C, DO-254 |
| **FSM** | 상태 진입(state), 전이(transition) | FSM 상태 머신 |

### Code Coverage의 한계

- 100% line coverage여도 **관찰(assertion/check)**이 없으면 버그 미검출
- 경계값, 코너 케이스를 자동으로 보장하지 않음
- **Controllability만 측정** — observability는 functional coverage/assertion이 담당
- Code coverage가 낮으면 → 해당 코드가 미실행 (stimulus 부족 확실)
- Code coverage가 높아도 → 기능 검증 완료를 의미하지 않음

---

## 3. Functional Coverage 이론

두 가지 모델링 접근:

### Covergroup Modeling (상태 값 샘플링)
- 특정 시점의 **값/조합**을 캡처
- 예: 버스 전송 시 주소 범위 분포, 명령어 종류 조합
- `covergroup`, `coverpoint`, `cross` 사용

### Cover Property Modeling (시퀀스/타이밍)
- 시간에 걸친 **시퀀스 완료**를 캡처
- 예: 핸드셰이크 프로토콜, 인터럽트 응답 시퀀스
- `cover property`, `cover sequence` 사용

### 선택 기준

| 검증 대상 | 적합한 모델 |
|----------|-----------|
| 값 분포/조합 | Covergroup |
| 타이밍/순서 관계 | Cover Property |
| 프로토콜 핸드셰이크 | Cover Property |
| 레지스터 내용 | Covergroup |
| FSM 전이 시퀀스 | Cover Property |
| 알고리즘 knob/파라미터 | Covergroup |

---

## 4. Spec → Testplan

### Bottom-up 접근 (Yellow Sticky Method)

1. 스펙의 각 세부 항목을 독립 요구사항으로 분리
2. 각 요구사항마다 **Generation** / **Checking** / **Coverage** 관점 기술
3. 상세하고 체계적 → 놓치는 항목 최소화
4. 단점: 시간 소요 크고, use-model 시나리오 놓칠 수 있음

### Top-down 접근 (DITL — Day-In-The-Life)

1. 실제 사용 시나리오 기반 (시스템이 하루 동안 겪는 이벤트)
2. 아키텍처/use-model에서 검증 시나리오 도출
3. 높은 추상도 → 빠른 커버리지 초기 구축
4. 단점: 세부 코너 케이스 놓칠 수 있음

### 권장: Top-down + Bottom-up 조합

1. Top-down으로 주요 use-model 시나리오 먼저 정의
2. Bottom-up으로 세부 스펙 요구사항 보충
3. 두 접근의 gap 분석

### Diagram 유형

| 유형 | 용도 |
|------|------|
| Tables | 레지스터 필드, 명령어 인코딩 |
| Bubble Diagram | 상태 머신, 모드 전이 |
| Y-Tree | 계층적 기능 분해 |
| Sequence Diagram | 프로토콜 핸드셰이크, 타이밍 |

---

## 5. Executable Testplan Format

### 필수 필드

| 필드 | 설명 |
|------|------|
| **Section** | 스펙 섹션 (계층 구조) |
| **Title** | 요구사항 제목 |
| **Link** | coverage element 식별자 (covergroup.coverpoint 등) |
| **Type** | Covergroup / Coverpoint / Cross / Assertion / Cover Directive / Directed test |
| **Description** | 검증할 내용 상세 기술 |

### 선택 필드

| 필드 | 설명 |
|------|------|
| Weight | 항목별 가중치 |
| Goal | 목표 coverage % |
| Path | HDL 경로 또는 파일 |
| Unimplemented | 미구현 플래그 |

### 계층적 Import

- Block-level testplan → SoC-level testplan으로 import
- 상위에서 하위 testplan을 참조하여 중복 방지
- SoC에서 block coverage를 재사용, 필요 시 exclusion 처리

---

## 6. Testplan → Functional Coverage 매핑

### 핵심 원칙

1. **Observation 기반**: stimulus(입력)가 아닌 **DUT 출력/상태**를 샘플링
   - Anti-pattern: sequence item에서 coverage 수집 (stimulus 측정)
   - Good: monitor analysis port에서 DUT 응답 기반 coverage 수집
2. **Check 통과 시에만 유효**: checker가 에러를 감지하지 않은 트랜잭션만 sampling
3. **Positive/Negative 분리**: 정상 동작과 에러 시나리오를 별도 coverage element로
4. **Fidelity 결정**: 넓은 필드(32-bit 주소 등)는 전체 범위 대신 **의미 있는 값/범위**로 추상화

### 값 추상화 전략 (Fidelity)

```
32-bit 주소 필드 → 전체 2^32 bin은 불가능
→ 의미 있는 범위: {0, align_boundary, region_start, region_end, max}
→ 또는: {[region_A], [region_B], ..., [reserved]}
```

---

## 7. Coverage Closure Process

### Hole 원인 3가지

| 원인 | 설명 | 대응 |
|------|------|------|
| **자극 부족** | stimulus가 해당 조건을 생성하지 못함 | constraint 조정, directed test 추가 |
| **버그** | DUT 버그로 해당 상태에 도달 불가 | 버그 수정 후 재실행 |
| **Unreachable** | 설계상 도달 불가능한 코드/상태 | exclusion 처리, formal tool 확인 |

### Closure 프로세스

1. Coverage 리포트에서 미달 항목 식별
2. 각 항목의 원인 분류 (위 3가지)
3. 자극 부족 → constraint 조정 또는 directed test 추가
4. 버그 → 버그 리포트 후 수정 대기
5. Unreachable → formal verification tool로 확인 → exclusion 문서화
6. Regression suite 재실행 → 결과 확인 → 반복

### Formal Tool 활용

- Unreachable code/state를 **수학적으로 증명** → 안전한 exclusion
- Code coverage hole 중 stimulus로 도달 불가능한 항목 자동 식별
- 예: dead code, 불가능 FSM 전이

### Regression Suite 최적화

- 중복 test 제거: 동일 coverage를 수집하는 test 통합
- 핵심 test만 유지하여 실행 시간 단축
- Coverage merge 후 incremental 분석

---

## 8. Coverage 목표

| 유형 | 일반 목표 | 고신뢰 목표 (DO-254 등) |
|------|----------|----------------------|
| Line/Statement | 90% | 100% |
| Branch/Decision | 85% | 95% |
| FSM (state + transition) | 100% | 100% |
| Functional Coverage | 100% | 100% |
| Toggle | 80% | 95% |
| Expression/MC/DC | - | 100% |

**주의**: 목표 달성 자체가 아닌, **미달 항목의 원인 분석**이 더 중요

---

## 9. 디자인 유형별 Coverage 전략

| 디자인 유형 | Covergroup | Assertion | 주요 전략 |
|-------------|-----------|-----------|----------|
| Control (bus protocol) | Maybe | **Yes** | 프로토콜 타이밍, 핸드셰이크 시퀀스 |
| Peripheral (register-based) | **Yes** | Maybe | 레지스터 필드 값/조합, 설정 모드 |
| DSP datapath | **Yes** | No | 알고리즘 knob/파라미터 조합, 입력 범위 |
| Aggregator/Controller | **Yes** | **Yes** | stimulus 조합 + spec 기반 시퀀스 |
| SoC Integration | **Yes** | Maybe | Use-case driven (DITL), block reuse |

### Control 디자인 (예: 버스 프로토콜)

- 타이밍 관계 중심 → `cover property` 위주
- 핸드셰이크 시퀀스, 중재(arbitration) 패턴
- Covergroup은 보조적 (주소/데이터 분포)

### Peripheral 디자인 (예: UART, SPI)

- 레지스터 내용 중심 → `covergroup` 위주
- 설정 조합 (word length × parity × stop bits)
- Assertion은 보조적 (인터럽트 타이밍 등)

### DSP Datapath

- 알고리즘 파라미터 중심 → `covergroup` 위주
- coefficient/mode/input range 조합
- Assertion 불필요 (연속 데이터 흐름)

### SoC Integration

- Use-model (DITL) 기반 → `covergroup` 위주
- Block-level coverage 재사용 + SoC-specific 추가
- 인터럽트, 전원 관리, 다중 마스터 시나리오
