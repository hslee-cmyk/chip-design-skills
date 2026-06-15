# SMT Solver Reference

## 주요 SMT Solver 비교

| Solver | 강점 | 약점 | sby 사용 |
|--------|------|------|---------|
| **Z3** | 범용, 안정적, 비트벡터 강력 | 속도 | `smtbmc z3` |
| **Yices2** | 빠른 선형 산술 | 비선형 약함 | `smtbmc yices` |
| **Bitwuzla** | 비트벡터 특화, 최신 | 범용 약함 | `smtbmc bitwuzla` |
| **CVC5** | 배열/양화사 강력 | 설정 복잡 | `smtbmc cvc5` |
| **Boolector** | 비트벡터 (구형) | 유지보수 감소 | `smtbmc boolector` |

## SMT Theory 선택 기준

```
RTL 설계 특성 → 적합 solver

정수/BV 연산 위주  → Z3 (기본 권장)
빠른 결과 필요    → Yices2 (선형 산술)
BV 집약 설계      → Bitwuzla
배열 모델 사용    → CVC5
```

## SMT Solver 이론 계층

```
QF_BV   (Quantifier-Free BitVector) — RTL 핵심
QF_ABV  (QF_BV + Arrays)           — 메모리 모델
QF_LIA  (Linear Integer Arith)     — 카운터/포인터
QF_NIA  (Nonlinear)                — 곱셈/나눗셈 (느림)
```

## Z3 sby 설정 예시

```ini
[engines]
smtbmc z3

# 타임아웃 설정 (초)
# smtbmc --timeout 60 z3

# 멀티스레드 (z3 4.x+)
# smtbmc --solver-option=parallel.enable=true z3
```

## Eager vs Lazy SMT

| 방식 | 동작 | 적합 |
|------|------|------|
| **Eager** | 전체 공식 → SAT으로 인코딩 후 1회 풀기 | 중소형 설계 |
| **Lazy** (DPLL(T)) | SAT 검색 ↔ Theory Solver 상호작용 | 복잡한 이론 조합 |

`yosys-smtbmc`는 Lazy 방식 사용 (SMT-LIB2 인터페이스로 solver 호출).
