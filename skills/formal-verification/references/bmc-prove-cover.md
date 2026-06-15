# BMC / Prove / Cover 심화 가이드

## BMC (Bounded Model Checking)

### 동작 원리

```
초기 상태 S0 → S1 → S2 → ... → Sk

SMT 질의: ∃ S0..Sk, ¬assert(Sk)
  → SAT: CEX 존재 (반례 반환)
  → UNSAT: depth k까지 속성 성립
```

### assert negation 예시

```
속성: a && b
SMT 질의: ¬(a && b) = !a || !b
→ SAT이면 a=0 또는 b=0인 시퀀스 존재 → CEX
```

### BMC 설정 (.sby)

```ini
[options]
mode bmc
depth 25    # k steps

[engines]
smtbmc z3
```

- `depth` 는 탐색할 최대 스텝 수
- CEX 경로가 `depth` 이내에 존재하면 반드시 발견
- `depth` 이후 속성 위반은 탐지 불가 → depth 증가 또는 Prove 모드

### 적합 상황

- 버그 탐지 (CEX 길이 예측 가능)
- 초기 검증 단계
- Windows 환경 (mode prove 병렬 프로세스 문제 회피)

---

## Prove (k-Induction)

### 동작 원리

```
Base Case:     S0 → S1 → ... → Sk  (BMC로 검증)
Inductive Step: S_arb → S_arb+1   (임의 초기 상태에서 한 스텝)
  → 모든 레지스터가 unconstrained arbitrary state로 시작

두 조건 모두 PASS → 무한 깊이에서 속성 성립 (완전 증명)
```

### k-Induction 실패 디버깅

```
Prove FAIL → CEX 확인
  → reachable? YES: 설계 버그 수정
  → reachable? NO:  assume 추가 / assertion 강화 / depth 증가
```

**Unreachable CEX 원인**: Inductive step의 임의 초기 상태가 실제로 도달 불가능한 state를 포함.

**해결책**:
1. `assume`으로 불가능한 상태 제거 (invariant 추가)
2. depth 증가 (k+1에서 base case 강화)
3. `assert` 자체를 강화하여 inductive하게 만들기

### .sby 설정

```ini
[options]
mode prove
depth 10

[engines]
smtbmc z3
```

> **Windows 주의**: `mode prove`는 basecase + induction 두 프로세스를 동시 실행. Windows OSS CAD Suite에서 실패 가능. → `mode bmc` + 충분한 depth 사용.

---

## Cover

### 동작 원리

```
cover(condition) → SMT가 condition=1이 되는 최단 경로 탐색
  → PASS: trace.vcd에 도달 경로 포함
  → UNREACHABLE: depth 내 경로 없음 (depth 증가 후 재시도)
```

### .sby 설정

```ini
[options]
mode cover
depth 30    # 충분히 크게 설정

[engines]
smtbmc z3
```

### Cover 활용 패턴

```verilog
// 1. FSM 상태 도달 가능성
cover(f_past_valid && r_state == TARGET_STATE);

// 2. 복합 조건 도달
cover(f_past_valid && out_valid && o_result == EXPECTED);

// 3. 시퀀스 완료
cover(f_past_valid && r_seq_done);
```

### Cover UNREACHABLE 대응

1. `depth` 증가 (도달에 필요한 사이클이 depth를 초과)
2. `assume` 완화 (과제약으로 경로 차단됨)
3. 설계 로직 확인 (실제로 도달 불가능한 상태)

---

## 모드 선택 기준

| 상황 | 권장 모드 | 이유 |
|------|-----------|------|
| 버그 탐색 | `bmc` | CEX 직관적, 빠름 |
| 완전 증명 | `prove` | 무한 깊이 보장 |
| 도달 가능성 | `cover` | 경로 시각화 |
| Windows 환경 | `bmc` | prove 병렬 실패 회피 |

---

## CEX (Counterexample) 분석

CEX 파일 위치: `<module>/engine_0/trace.vcd`

```bash
# GTKWave로 파형 확인
gtkwave <module>/engine_0/trace.vcd

# 텍스트 TB 확인
cat <module>/engine_0/trace_tb.v
```

VCD에서 확인할 항목:
- 초기 상태 (사이클 0): 레지스터 초기값 arbitrary 여부
- assert 실패 시점: 어느 조건이 위반됐는지
- 입력 시퀀스: assume이 제대로 제약했는지
