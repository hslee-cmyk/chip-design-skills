---
name: verilog-a
description: |
  Verilog-A 아날로그 behavioral 모델링 skill. 다음 상황에서 사용:
  (1) Verilog-A 모델 작성 - 아날로그 회로 behavioral 모델, 수렴 최적화
  (2) 연속성 분석 - discrete/continuous 신호 분류, transition 필터 적용
  (3) 수렴 문제 해결 - Newton-Raphson 반복, piecewise-linear 회피
  (4) 피드백 시스템 모델링 - 값/기울기 연속성, 단조 함수 사용
  (5) Mixed-signal 인터페이스 - cross/above 이벤트, timestep 최적화
  (6) 모델 검증 - transistor-level 대비 동작 검증
  Verilog-A 파일이 언급되거나 아날로그 behavioral 모델링, 수렴 문제,
  SPICE/AMS 관련 요청이 보이면 반드시 이 스킬을 사용.
  트리거: Verilog-A, .va, AMS, mixed-signal, analog behavioral model, SPICE netlist, 수렴, convergence, transition filter, cross event, ddt, idt, electrical discipline, contribution statement, Verilog-AMS
---

# Verilog-A Analog Modeling Skill

## 핵심 원칙

Verilog-A 모델링의 핵심은 **연속성(Continuity)**과 **수렴 가능성(Convergence)**:

```
┌─────────────────────────────────────────────────────────────┐
│                  Verilog-A 모델링 핵심                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 모든 Analog 출력은 CONTINUOUS 신호로만 구동 [→§2]       │
│  2. Discrete 신호는 반드시 transition() 통과 [→§2,§4]      │
│  3. Feedback 경로는 값과 기울기 모두 연속 [→§3]            │
│  4. Floating node 방지 (항상 DC path 존재) [→§3]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. 기본 문법

### 최소 Module 골격

```verilog-a
`include "disciplines.vams"
`include "constants.vams"

module my_model (out, in, vdd, gnd);
    inout  electrical out, in, vdd, gnd;

    parameter real gain = 1.0;   // 파라미터: 기본값 필수

    analog begin
        V(out, gnd) <+ gain * V(in, gnd);  // voltage contribution
        // I(out, gnd) <+ expr;             // current contribution
    end
endmodule
```

**핵심 규칙:**
- `inout electrical` — 양방향 전기 포트 (단방향 없음)
- `V(a,b) <+` — a→b 전압 기여, `I(a,b) <+` — a→b 전류 기여
- `<+` 는 기여(contribution), `=` 는 지역 변수 할당

Branch access, 미분/적분(`ddt`, `idt`), 전체 문법: `references/coding-guideline.md` §2 참조

---

## 2. Signal Types (Critical)

### Three Types of Analog Signals

| Type | Description | 처리 방법 |
|------|-------------|----------|
| **Continuous** | 절대 불연속 변화 없음 | 직접 사용 가능 |
| **Discrete** | 특정 시점에 불연속 변화 | **transition() 필수** |
| **Mixed** | 연속 또는 불연속 가능 | 분리 후 처리 |

### Golden Rule

> **아날로그 핀을 구동하는 모든 신호는 연속 값으로만 구성되어야 합니다.**
> **모든 이산 신호는 사용 전에 반드시 `transition` 필터를 통해 연속 형태로 변환해야 합니다.**

### GOOD Example

```verilog-a
// transition()으로 연속 변환
parameter real Tr = 1n;
real ASEL;

analog begin
    ASEL = transition(SEL, 0, Tr);  // 0→1 또는 1→0 램프
    V(OUT) <+ ASEL * V(IN1) + (1 - ASEL) * V(IN0);
end
```

BAD 예제 (discrete 직접 구동 문제): `references/coding-guideline.md` §3.2 참조

---

## 3. Convergence Best Practices

### Causes of Convergence Problems

| 원인 | 설명 |
|------|------|
| 해가 없는 시스템 | 이상 전류원 → 개방 노드 |
| 다중 해 | dead zone, 완전 분리 노드 |
| 불연속 출력 변화 | if/else로 급격한 값 변화 |
| Piecewise-linear | 기울기 불연속 |

### Feedback System Requirements

피드백 시스템에서 전달 함수는:
- **값과 기울기 모두 연속**
- **단조(monotonic)** 함수 선호 (zero slope 구간 없음)
- tanh, exponential, power law 등 사용

Piecewise-linear BAD/GOOD 예제, Floating Node 방지 코드: `references/convergence-issues.md` 참조
코딩 가이드라인: `references/coding-guideline.md` §4 참조

---

## 4. transition() and slew()

핵심 규칙:
- `transition(value, delay, rise_time, fall_time)` — delay=0, rise/fall time은 가능한 크게
- `slew(value, max_pos_slope, max_neg_slope)` — Op-amp slew rate 등

상세 문법 및 best practice: `references/coding-guideline.md` §5 참조

---

## 5. Events and Timing

### 이벤트 성능 비용

`@(cross())`와 `@(above())`는 비용이 큰 연산 (매 timestep 확인, tolerance 수렴, backstep)

### 효율적 대안

| 상황 | 방법 |
|------|------|
| 정확한 타이밍 불필요 | `if()` 조건 사용 |
| 정확한 시간 측정 | `last_crossing()` (backstep 없음) |
| 주기적 이벤트 | `@(timer(period, offset))` |

상세 코드 예제: `references/coding-guideline.md` §6 참조

---

## 6. Timestep Considerations

### Functions That Force Small Timesteps

| Function | Impact | Alternative |
|----------|--------|-------------|
| `$absdelay(sig, td)` | td보다 작은 timestep | 1st-order LPF |
| `transition(v, td, tr)` | 작은 td, tr | td=0, tr 최대화 |
| `$bound_step(dt)` | dt 이하로 제한 | 필요시만 사용 |
| `@(cross())` | backstep | if() 또는 last_crossing() |

### Timestep Recovery Impact

작은 timestep 후 복구: 다음 timestep은 이전의 최대 2배까지만 증가.
1ps → 2ps → 4ps → ... → 1ns (약 10 timesteps). **하나의 작은 timestep이 10배 속도 저하 유발.**

---

## 7. 4-State Logic Handling

`===` 사용 (X, Z 명시적 처리):

```verilog-a
// GOOD: X, Z 명시적 처리
if (SEL === 1)
    V(out) <+ V(in1);
else
    V(out) <+ V(in0);  // SEL이 0, X, Z일 때 모두 in0
```

---

## 8. Common Circuit Models

기본 passive (Resistor, Capacitor, Inductor), Analog MUX, Comparator with Hysteresis, Op-Amp:
→ `references/common-models.md` 참조

핵심 패턴:
- **MUX**: conductance-based switching + `transition()` + `===` (4-state safe)
- **Comparator**: `@(initial_step)` 초기화 + hysteresis + `transition()` 출력

---

## 9. Model Development Checklist

### 작성 전
- [ ] 동작 정의 명확, 입력 조건(정상/비정상) 정의, 파라미터 범위 적절 [→§1]

### 작성 후
- [ ] 모든 analog 출력이 continuous 신호로만 구동 [→§2]
- [ ] 모든 discrete 신호가 transition 필터 통과 [→§2,§4]
- [ ] Feedback 전달함수: 값+기울기 연속 [→§3]
- [ ] 모든 노드에 DC path 존재 (floating node 없음) [→§3]
- [ ] 4-state logic (===) 처리 [→§7]
- [ ] cross/above 이벤트 최소화 [→§5,§6]
- [ ] transition delay=0, tr/tf 적절 [→§4,§6]
- [ ] Piecewise-linear → smooth 함수 (tanh, limexp) [→§3]
- [ ] @(initial_step) 초기 조건 제공 [→§5]

### 검증
- [ ] Model ↔ transistor-level 동작 동일, 모든 동작 모드/경계 조건 테스트 [→§8]

---

## 10. Quick Reference

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Core Files:   `include "disciplines.vams" / "constants.vams"
Disciplines:  electrical (voltage/current), ground gnd

Branch:       V(p,n), I(p,n) — differential
              V(p), I(p) — to ground

Contribution: V(out) <+ (voltage), I(out) <+ (current)
Calculus:     ddt(x), idt(x, ic)

Signal Conv:  transition(val, delay, tr, tf) — discrete→continuous
              slew(val, sr_pos, sr_neg) — slew rate limiting

Events:       @(cross(expr)), @(above(expr)), @(timer(T, offset))
              @(initial_step) — initialization

Key Rules:
  1. Analog output ← CONTINUOUS only [→§2]
  2. Discrete → transition() → Analog [→§2,§4]
  3. Feedback: continuous in value AND slope [→§3]
  4. No floating nodes (always DC path) [→§3]
  5. Use === for 4-state logic [→§7]
  6. Minimize cross/above events [→§5,§6]
  7. transition: delay=0, tr/tf=max feasible [→§4,§6]
  8. PWL → smooth function (tanh, limexp) [→§3]
  9. Initial condition at @(initial_step) [→§5]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 참조 파일

- `references/coding-guideline.md` - Verilog-A 코딩 가이드라인 상세
- `references/convergence-issues.md` - 수렴 문제 분석 및 해결
- `references/common-models.md` - 일반 회로 모델 예제
- `references/consistency-map.md` - 일관성 맵

## Cross-Skill 참조

- RTL 설계 규칙, 합성 체크 → `verilog-rtl` skill
- Mixed-signal 검증환경, Connect Module → `chip-verification` skill
