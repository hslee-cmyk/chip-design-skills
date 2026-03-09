# Verilog-A Coding Guideline

## 1. Overview

Verilog-A는 아날로그 회로 동작을 모델링하기 위한 하드웨어 기술 언어입니다.
이 가이드라인은 효율적이고 수렴 가능한 시뮬레이션을 위한 코딩 규칙을 정의합니다.

---

## 2. Basic Syntax

### 2.1 Module Structure

```verilog-a
`include "disciplines.vams"
`include "constants.vams"

module module_name(port1, port2, ...);
    inout port1, port2;
    electrical port1, port2;

    parameter real param1 = default_value from [min:max];

    real internal_var;

    analog begin
        // contribution statements
    end
endmodule
```

### 2.2 Discipline and Nature

```verilog-a
// disciplines.vams에 정의된 표준 discipline
electrical node1, node2;    // voltage(potential), current(flow)
ground gnd;                  // ground reference
```

### 2.3 Branch Access Functions

```verilog-a
V(p, n)      // p와 n 사이 전압
I(p, n)      // p에서 n으로 흐르는 전류
V(p)         // p와 ground 사이 전압 (= V(p, gnd))
I(p)         // p로 흐르는 전류
```

### 2.4 Contribution Statement (`<+`)

```verilog-a
// 전압 기여 (전압원처럼 동작)
V(out) <+ 1.0;

// 전류 기여 (전류원처럼 동작)
I(out) <+ V(in) / R;

// 누적 기여 (여러 contribution은 합산됨)
V(out) <+ V(in1);
V(out) <+ V(in2);  // 결과: V(out) = V(in1) + V(in2)
```

### 2.5 Parameters

```verilog-a
parameter real resistance = 1k from (0:inf);      // 0 < R < inf
parameter real capacitance = 1p from [0:inf);    // 0 <= C < inf
parameter integer bits = 8 from [1:16];           // 1 <= bits <= 16
```

### 2.6 Derivative and Integral Operators

```verilog-a
// 시간 미분: ddt() - Capacitor
I(p, n) <+ C * ddt(V(p, n));

// 시간 적분: idt() - Inductor
V(p, n) <+ L * idt(I(p, n));
V(p, n) <+ L * idt(I(p, n), ic);  // ic: 초기값
```

### 2.7 Mathematical Functions

| Function | Description |
|----------|-------------|
| `abs(x)` | 절대값 |
| `sqrt(x)` | 제곱근 |
| `pow(x, y)` | x^y |
| `exp(x)` | e^x |
| `ln(x)` | 자연로그 |
| `log(x)` | 상용로그 |
| `sin(x), cos(x), tan(x)` | 삼각함수 |
| `sinh(x), cosh(x), tanh(x)` | 쌍곡선함수 |
| `min(x, y), max(x, y)` | 최소/최대 |
| `limexp(x)` | 오버플로우 방지 exp |

### 2.8 Events and Timing

```verilog-a
// Timer event (주기적 이벤트)
@(timer(period, offset))

// Signal crossing event (threshold crossing)
@(cross(V(in) - vth, +1))   // 상승 교차
@(cross(V(in) - vth, -1))   // 하강 교차
@(cross(V(in) - vth, 0))    // 양방향

// Initialization event
@(initial_step) begin
    // 시뮬레이션 시작 시 1회 실행
end
```

---

## 3. Signal Types and Continuity (Critical)

### 3.1 Three Types of Analog Signals

아날로그 실수 변수는 다음 세 가지 유형으로 분류됩니다:

| Type | Description | Example |
|------|-------------|---------|
| **Continuous** | 값이 절대 불연속적으로 변하지 않음 | V(), I(), $abstime, $realtime |
| **Discrete** | 대부분 일정하다가 특정 시점에 불연속 변화 | if/case 결과, cross/timer 이벤트, 정수 변수 |
| **Mixed** | 연속적으로 변하거나 불연속적으로 변할 수 있음 | 문제의 주요 원인 |

### 3.2 Golden Rule: Continuity for Analog Outputs

> **아날로그 핀을 구동하는 모든 신호는 연속 값으로만 구성되어야 합니다.
> 모든 이산 신호는 사용 전에 반드시 `transition` 필터를 통해 연속 형태로 변환해야 합니다.**

```verilog-a
// BAD: 불연속 변화 - 수렴 문제 유발
analog begin
    if (SEL)
        V(OUT) <+ V(IN1);
    else
        V(OUT) <+ V(IN0);
end

// GOOD: transition으로 연속 변환
parameter real Tr = 1n;
real ASEL;
analog begin
    ASEL = transition(SEL, 0, Tr);
    V(OUT) <+ ASEL * V(IN1) + (1 - ASEL) * V(IN0);
end
```

---

## 4. Convergence Best Practices

### 4.1 Causes of Convergence Problems

1. **해가 없는 시스템** - 이상적인 전류원이 개방 노드로 흐르는 경우
2. **다중 해를 가진 시스템** - dead zone 특성, 완전히 분리된 노드
3. **불연속 출력 변화** - if/else로 인한 급격한 값 변화
4. **Piecewise-linear 전달 특성** - Newton-Raphson 반복에서 기울기 불연속

### 4.2 Avoid Piecewise-Linear in Feedback

```verilog-a
// BAD: Piecewise-linear (기울기 불연속)
if (V(in) > vth)
    V(out) <+ gain * (V(in) - vth);
else
    V(out) <+ 0;

// GOOD: Continuous smooth function (tanh 사용)
V(out) <+ gain * 0.5 * (V(in) - vth) * (1 + tanh(k * (V(in) - vth)));
```

### 4.3 Feedback Systems Requirements

피드백 시스템에서 전달 함수는:
- **값과 기울기 모두 연속**이어야 함
- **단조(monotonic)** 함수 선호 (zero slope 구간 없음)
- tanh, exponential, power law 등 연속 함수 사용

```verilog-a
// Saturation with smooth limiting
parameter real vsat = 1.0;
parameter real k = 10;  // smoothness factor

// Soft saturation using tanh
V(out) <+ vsat * tanh(gain * V(in) / vsat);
```

### 4.4 Floating Node Prevention

```verilog-a
// BAD: OFF 시 floating node + transition 없음
parameter real Ron = 100;
I(in, out) <+ V(in, out) * (enable ? 1/Ron : 0);

// GOOD: OFF 저항으로 floating 방지 + transition으로 연속 변환
parameter real Ron = 100;
parameter real Roff = 1G;
parameter real Tr = 1n;
I(in, out) <+ V(in, out) * transition(enable ? 1/Ron : 1/Roff, 0, Tr);
```

---

## 5. Transition and Slew Functions

### 5.1 transition() - Discrete to Continuous Conversion

```verilog-a
transition(value, delay, rise_time, fall_time)

// Example: Digital control to analog
real ctrl_analog;
analog begin
    ctrl_analog = transition(digital_ctrl, 0, 1n, 1n);
    V(out) <+ ctrl_analog * vhi + (1 - ctrl_analog) * vlo;
end
```

### 5.2 slew() - Slew Rate Limiting

```verilog-a
slew(value, max_pos_slope, max_neg_slope)

// Example: Op-amp slew rate limiting
parameter real sr = 1e6;  // 1V/us
V(out) <+ slew(gain * V(inp, inn), sr, -sr);
```

### 5.3 Guidelines for transition/slew

- **delay는 0 사용** - 작은 non-zero delay는 작은 timestep 강제
- **rise/fall time은 가능한 크게** - timestep 영향 최소화
- **모든 discrete 신호에 적용** - analog 출력 구동 전 필수

---

## 6. Cross and Above Events

### 6.1 Performance Impact

`@(cross())` 와 `@(above())`는 정확한 threshold crossing 시점을 찾기 위해:
1. 매 timestep마다 crossing 확인
2. Tolerance 내로 반복 수렴
3. 필요시 backstep 수행

> **많은 cross/above 문은 시뮬레이션 속도를 크게 저하시킵니다.**

### 6.2 Efficient Alternatives

```verilog-a
// 정확한 타이밍이 불필요한 경우: if() 사용
real Vlast;
analog begin
    if (V(in) >= vth && Vlast < vth) begin
        // rising edge action
    end
    Vlast = V(in);
end

// 정확한 crossing 시간이 필요한 경우: last_crossing()
real Tcross;
analog begin
    Tcross = last_crossing(V(in) - vth, +1);
end
```

### 6.3 Tolerance Specification

```verilog-a
// Moderate tolerance로 성능 개선
@(cross(V(in) - vth, +1, 1n, 100m)) begin
    // 1ns time tolerance, 100mV voltage tolerance
end
```

---

## 7. Timestep Considerations

### 7.1 Functions That Force Small Timesteps

| Function | Impact | Alternative |
|----------|--------|-------------|
| `$absdelay(sig, td)` | td보다 작은 timestep 강제 | 1st-order LPF 사용 |
| `transition(v, td, tr)` | 작은 td, tr은 작은 timestep 강제 | td=0, tr 최대화 |
| `$bound_step(dt)` | dt 이하로 timestep 제한 | 꼭 필요한 경우만 사용 |
| `@(cross())` | crossing 정밀도를 위한 backstep | if() 또는 last_crossing() |

### 7.2 Timestep Recovery

작은 timestep 후 복구 시:
- 다음 timestep은 이전의 최대 2배까지만 증가 가능
- 1ps → 2ps → 4ps → ... → 1ns (약 10 timesteps)
- **하나의 작은 timestep이 시뮬레이션 속도를 10배 저하시킬 수 있음**

---

## 8. Mixed-Signal Considerations

### 8.1 DC Operating Point Sequence

1. 모든 discrete 초기화 수행
2. 모든 discrete `initial` 블록 실행 (time zero)
3. 모든 discrete `always` 블록 실행 (time zero)
4. Analog 시스템이 모든 전압/전류 해를 반복 계산

### 8.2 Transient Simulation Flow

1. Analog solver가 T0에서 T1으로 timestep 시도
2. 수렴 실패 시 더 작은 timestep으로 재시도
3. Digital solver가 T0+에서 T1까지 순차 실행
4. Discrete 데이터 변경 시 analog solver backstep 필요

### 8.3 Efficient A/D Conversion

```verilog-a
// Digital code에서 analog 신호 샘플링
// 주기적 샘플링으로 cross() 대체
always #(Ts) Vsamp = V(in);

// 변화량 기반 샘플링
always @(absdelta(V(in), Vdelta, Ttol, Vtol))
    Vsamp = V(in);
```

---

## 9. 4-State Logic Handling

### 9.1 Use === Instead of ==

```verilog-a
// BAD: X, Z 입력 시 결과도 X가 되어 시뮬레이션 실패
if (SEL == 1)
    V(out) <+ V(in1);

// GOOD: X, Z를 명시적으로 처리
if (SEL === 1)
    V(out) <+ V(in1);
else
    V(out) <+ V(in0);  // SEL이 0, X, Z일 때 모두 in0 선택
```

---

## 10. Debugging Tips

### 10.1 Convergence Issues

1. **$strobe로 값 확인** - 수렴 실패 직전 상태 확인
2. **Timestep 분석** - 급격히 작아지는 구간 확인
3. **Discontinuity 검색** - if/case 문에서 analog 출력 직접 구동 확인
4. **Floating node 확인** - 모든 노드에 DC path 존재 확인

### 10.2 Simulation Performance

1. **cross/above 개수 최소화**
2. **transition delay = 0 사용**
3. **rise/fall time 최대화**
4. **불필요한 $bound_step 제거**

---

## 11. Checklist

### 작성 전 확인

- [ ] 모델의 동작 정의가 명확한가?
- [ ] 모든 입력 조건(정상/비정상)이 정의되었는가?
- [ ] 파라미터 범위가 적절히 정의되었는가?

### 작성 후 확인

- [ ] 모든 analog 출력이 continuous 신호로만 구동되는가?
- [ ] 모든 discrete 신호가 transition 필터를 통과하는가?
- [ ] Feedback 경로의 전달함수가 값과 기울기 모두 연속인가?
- [ ] Piecewise-linear 대신 smooth 함수 (tanh, limexp) 사용했는가?
- [ ] 모든 노드에 DC path가 존재하는가? (floating node 없음)
- [ ] 4-state logic (X, Z)이 적절히 처리되는가?
- [ ] cross/above 이벤트가 최소화되었는가?
- [ ] transition의 delay가 0이고 rise/fall time이 적절한가?
- [ ] @(initial_step)에서 적절한 초기 조건을 제공했는가?

### 검증 확인

- [ ] Model과 transistor-level 회로의 동작이 동일한가?
- [ ] 모든 동작 모드에서 테스트되었는가?
- [ ] 경계 조건에서 테스트되었는가?
- [ ] Invalid 입력 (X, Z, out-of-range)에 대한 응답이 정의되었는가?

---

## 12. References

1. Verilog-AMS 2.3 Language Reference Manual
2. Mixed-Signal Methodology Guide (Cadence)
3. IEEE Standard 1364-2005 (Verilog HDL)
4. Newton-Raphson Method: http://en.wikipedia.org/wiki/Newton%27s_method
