# Verilog-A Convergence Issues

## Newton-Raphson 반복 이해

SPICE 기반 아날로그 시뮬레이터는 Newton-Raphson 반복을 사용하여 비선형 시스템의 해를 찾습니다.

```
┌─────────────────────────────────────────────────────────────┐
│                Newton-Raphson Iteration                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  f(x) = 0 의 해를 찾기 위해:                                │
│                                                             │
│  x_{n+1} = x_n - f(x_n) / f'(x_n)                          │
│                                                             │
│  → 기울기(f')를 사용하여 해 추정                            │
│  → 연속적이고 monotonic한 함수에서 빠르게 수렴              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 수렴 문제 유형

### 1. 해가 없는 시스템

**원인:**
- 이상 전류원이 개방 노드로 흐름
- 토폴로지적으로 불가능한 연결

**예시:**
```verilog-a
// BAD: 개방 노드에 전류 구동 → 해 없음
I(floating_node) <+ 1m;

// GOOD: 저항으로 DC path 제공
I(node) <+ 1m;
I(node) <+ V(node) / 1G;  // 1G 저항으로 접지
```

### 2. 다중 해를 가진 시스템

**원인:**
- Dead zone 특성
- 완전히 분리된 노드
- Ill-conditioned matrix

**예시:**
```verilog-a
// BAD: 스위치 OFF 시 floating + transition 없음
if (enable)
    I(in, out) <+ V(in, out) / Ron;
// OFF 시 out 노드에 대한 방정식 없음

// GOOD: OFF 저항으로 항상 방정식 존재 + transition으로 연속 변환
I(in, out) <+ V(in, out) * transition(enable ? 1/Ron : 1/Roff, 0, Tr);
```

### 3. 불연속 출력 변화

**원인:**
- if/else로 인한 급격한 값 변화
- 이산 변수가 직접 아날로그 출력 구동

**문제점:**
- 시뮬레이터가 작은 timestep을 시도해도 불연속은 사라지지 않음
- 수렴 실패 또는 극도로 느린 시뮬레이션

**해결:**
```verilog-a
// BAD: 불연속
V(out) <+ sel ? vhi : vlo;

// GOOD: transition으로 연속화
V(out) <+ transition(sel ? vhi : vlo, 0, 1n, 1n);
```

### 4. Piecewise-Linear 전달 특성

**문제점:**
- 기울기가 불연속적으로 변함
- Newton-Raphson이 기울기 정보로 다음 추정을 계산
- 기울기 불연속 지점에서 반복이 발산

```
F(x)                          F(x)
  ↑   Piecewise-Linear          ↑   Continuous (tanh)
  │     /                       │      ___
  │    /                        │    /
  │___/                         │   /
  │                             │__/
  └───────→ x                   └───────→ x

  기울기 0 구간 → 반복 실패      항상 non-zero 기울기 → 수렴
```

**해결:**
```verilog-a
// BAD: Piecewise-linear saturation
if (V(in) > vsat)
    V(out) <+ vsat;
else if (V(in) < -vsat)
    V(out) <+ -vsat;
else
    V(out) <+ V(in);

// GOOD: Smooth saturation with tanh
V(out) <+ vsat * tanh(V(in) / vsat);
```

---

## 피드백 시스템의 특수 요구사항

피드백이 있는 시스템에서는 더 엄격한 연속성이 필요합니다:

### 값 연속성만으로는 부족

```
┌─────────────────────────────────────────────────────────────┐
│              Feedback System Requirements                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  일반 시스템:      값 연속성 필요                            │
│  피드백 시스템:    값 + 기울기 연속성 필요                   │
│                                                             │
│  기울기가 0인 구간이 있으면:                                 │
│  → 해가 없거나 무한히 많음                                  │
│  → Newton-Raphson이 방향 정보를 잃음                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 단조(Monotonic) 함수 사용

```verilog-a
// BAD: Zero slope 구간 있음 (dead zone)
if (abs(V(in)) < vdead)
    V(out) <+ 0;
else
    V(out) <+ gain * V(in);

// GOOD: 항상 non-zero slope (smooth)
V(out) <+ gain * V(in) / (1 + abs(gain * V(in) / vsat));
```

---

## 수렴 문제 디버깅

### 1. 증상 식별

| 증상 | 가능한 원인 |
|------|-------------|
| DC operating point 실패 | Floating node, 해 없음 |
| Transient에서 timestep 급감 | 불연속, piecewise-linear |
| 특정 시점에서 수렴 실패 | 스위칭 이벤트의 불연속 |
| 매우 느린 시뮬레이션 | 많은 cross 이벤트, 작은 timestep |

### 2. 디버깅 절차

```verilog-a
// Step 1: 문제 지점에서 값 출력
analog begin
    @(initial_step)
        $strobe("Initial: V(out) = %g", V(out));

    // 매 timestep 출력 (성능 저하 주의)
    $strobe("t=%g: V(in)=%g, V(out)=%g", $abstime, V(in), V(out));
end

// Step 2: Timestep 모니터링
analog begin
    real t_last;
    @(initial_step) t_last = 0;

    if ($abstime - t_last < 1p)
        $strobe("Very small timestep at t=%g", $abstime);
    t_last = $abstime;
end
```

### 3. 체크리스트

1. **모든 노드에 DC path가 있는가?**
   - 모든 노드가 저항이나 전압원을 통해 접지 연결
   - 스위치 OFF 시에도 유지

2. **아날로그 출력이 연속인가?**
   - if/else에서 직접 V()/I() 구동 확인
   - transition() 사용 여부 확인

3. **피드백 경로에 기울기 불연속이 있는가?**
   - Piecewise-linear 전달 특성 확인
   - Zero slope 구간 확인

4. **4-state logic이 처리되었는가?**
   - X, Z 입력 시 동작 확인
   - `===` 연산자 사용 확인

---

## 수렴 개선 기법

### 1. Gmin Stepping

시뮬레이터 옵션으로 작은 conductance 추가:

```
// Spectre 예시
options gmin=1e-12
```

### 2. Source Stepping

전원을 0에서 목표값까지 점진적으로 증가:

```verilog-a
// 수동 source stepping
parameter real t_ramp = 10n;
real scale;

analog begin
    scale = min(1.0, $abstime / t_ramp);
    V(vdd) <+ vdd_target * scale;
end
```

### 3. Initial Condition 제공

```verilog-a
analog begin
    @(initial_step) begin
        V(cap_node) <+ 0.5;  // 예상 동작점 근처로 초기화
    end
end
```

### 4. Continuation Method

점진적으로 비선형성 증가:

```verilog-a
parameter real t_cont = 100n;
real nl_factor;

analog begin
    // 처음에는 선형, 점점 비선형으로
    nl_factor = min(1.0, $abstime / t_cont);

    // 선형과 비선형의 blend
    V(out) <+ (1 - nl_factor) * linear_model + nl_factor * nonlinear_model;
end
```

---

## 모범 사례 요약

```
┌─────────────────────────────────────────────────────────────┐
│              Convergence Best Practices                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 모든 노드에 DC path 보장                                │
│     → OFF 저항, bias 저항 추가                              │
│                                                             │
│  2. Discrete → Analog는 항상 transition() 통과              │
│     → delay=0, tr/tf=maximum feasible                       │
│                                                             │
│  3. Piecewise-linear 대신 smooth 함수 사용                  │
│     → tanh, limexp, soft limiting                           │
│                                                             │
│  4. 피드백 경로는 monotonic 전달 함수                       │
│     → zero slope 구간 제거                                  │
│                                                             │
│  5. 4-state logic 명시적 처리                               │
│     → `===` 연산자로 X, Z 처리                              │
│                                                             │
│  6. 적절한 초기 조건 제공                                   │
│     → @(initial_step)에서 예상 동작점 설정                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
