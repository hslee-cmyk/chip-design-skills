---
name: formal-verification
description: >
  Formal verification skill using SymbiYosys (sby). Covers SMT solver theory,
  formal directives (assert/assume/cover/restrict), BMC/prove/cover methods,
  black-box stub patterns, and Windows OSS CAD Suite setup. Triggers: formal, sby,
  SymbiYosys, BMC, model checking, assertion, property, SMT, z3, prove.
triggers:
  - formal verification
  - sby
  - SymbiYosys
  - BMC
  - bounded model checking
  - model checking
  - formal property
  - assert property
  - assume property
  - cover property
  - SMT solver
  - z3
  - k-induction
  - counterexample
  - CEX
  - formal check
  - property verification
  - RTL formal
  - SVA
  - SystemVerilog Assertion
  - concurrent assertion
  - temporal operator
  - sequence property
  - disable iff
version: 1.0
---

# Formal Verification Skill

RTL formal verification using SymbiYosys (sby) + Yosys + SMT solvers.  
이론(SMT/BMC/Prove) + 실전(sby 워크플로우 + Windows 환경) 통합 가이드.

---

## §1 핵심 개념 — SAT vs SMT

| 구분 | SAT Solver | SMT Solver |
|------|-----------|-----------|
| 입력 | Boolean 변수만 | Boolean + 정수/실수/배열/비트벡터 |
| 표현 | CNF (Conjunctive Normal Form) | First-order formulas |
| 접근 | Bit-blasting | Eager(인코딩→SAT) / Lazy(DPLL(T)) |
| 대표 | MiniSAT | Z3, CVC5, Yices2, Bitwuzla, OpenSMT |

**RTL 검증에서 SMT가 필수인 이유**: 실제 설계는 정수 연산, 비트벡터 등 Boolean 이상의 타입을 포함한다.

주요 SMT solver 특성 → `references/smt-solvers.md`

---

## §2 Formal Directives — assert / assume / cover / restrict

```
          COI (Cone of Influence)
 입력 ──→ [assume/restrict] ──→ 내부 로직 ──→ [assert/cover] ──→ 출력
```

| 지시어 | 위치 | 상태공간 영향 | 용도 |
|--------|------|-------------|------|
| `assert` | 출력/내부 | **증가** (illegal/non-reachable state 추가) | 속성 위반 탐지 |
| `assume` | assertion에 영향 주는 입력 | **감소** | 입력 제약, 환경 모델링 |
| `cover` | 출력/내부 | — | 도달 가능성 확인 |
| `restrict` | assertion 무관 입력 | **감소** | 입력 제약 (assume 불가 시) |

**핵심 규칙**:
- `assert` 추가 → state space **증가** → 분석 시간 증가
- `assume` 추가 → state space **감소** → 검증 가속  
- `assume`은 반드시 satisfiable이어야 함 (과제약 시 vacuous pass 위험)
- `cover`는 depth 부족 시 unreachable 반환

상세 예제 → `references/directives.md`

---

## §3 검증 모드 — BMC / Cover / Prove

### BMC (Bounded Model Checking)
- 초기 상태 → depth k 까지 state space 탐색
- 반례(CEX)가 직관적: 초기 상태에서 k 스텝의 순서가 명확
- 어설션 만족 여부를 SMT solver에 negation으로 질의
  - `(a && b)` → `(!a || !b)`가 SAT이면 CEX 존재
- **사용**: 버그 탐지, 초기 검증

### Cover
- cover 지시어로 지정한 상태가 reachable인지 확인
- depth 범위 내에서 SMT solver가 도달 가능한 최단 경로 탐색
- depth 부족 시 → unreachable 반환 (depth 증가 후 재시도)
- **사용**: 테스트 케이스 도달 가능성 확인, 설계 이해

### Prove (k-Induction)
- **Base case**: BMC로 k steps 검증
- **Inductive step**: k+1 스텝에서 assert+assume이 유지되는지 증명
- 모든 레지스터가 임의 상태(initial state 무관)에서 시작
- CEX가 unreachable state인 경우: `assume` 추가 또는 assertion 강화
- **사용**: 무한 깊이 증명 (design correctness)

```
Prove 실패 디버깅:
  CEX 확인 → reachable? → YES: 설계 버그 수정
                         → NO:  assume 추가 / assertion 강화 / depth 증가
```

상세 → `references/bmc-prove-cover.md`

---

## §4 Formal Core & Cone of Influence (COI)

- **COI**: 특정 property의 출력에 영향을 주는 입력-로직-출력 경로 전체
- **Formal Core**: COI의 subset — FV tool이 자동 추상화로 최적화한 state space
- assert가 많을수록 formal core 복잡도 증가
- assume/restrict으로 state space를 제한하면 formal core 간소화

---

## §5 sby 워크플로우

### 프로젝트 구조
```
project/
├── formal/
│   ├── <module>.sby          # sby 설정 파일
│   ├── src/
│   │   ├── <module>.v        # RTL 사본 + `ifdef FORMAL 속성 추가
│   │   └── <stub>.v          # 하위 모듈 black-box stub
```

### .sby 파일 형식

핵심 주의: `[script]` 경로는 파일명만 (sby work dir 내 `src/` 기준). `[files]`는 .sby 위치 기준 경로.

상세 형식 및 예제 → `references/sby-workflow.md`

### `ifdef FORMAL 패턴

`f_past_valid` 레지스터로 첫 사이클 보호 후 `$past()` 사용. reset/sequential property/cover 패턴.

상세 패턴 → `references/sby-workflow.md §ifdef FORMAL`

### Black-box Stub (`(* anyseq *)` 패턴)
```verilog
// 하위 모듈 출력을 비결정적(free)으로 만들어 sound한 black-box 검증
module sub_module (input clk, output o_valid, output [7:0] o_data);
    (* anyseq *) wire _valid;
    (* anyseq *) wire [7:0] _data;
    assign o_valid = _valid;
    assign o_data  = _data;
endmodule
```

상세 가이드 → `references/sby-workflow.md`

---

## §6 Windows 환경 설정 (OSS CAD Suite)

### 설치
OSS CAD Suite (`C:\oss-cad-suite\oss-cad-suite\`)에 yosys 0.64+, sby, 모든 SMT solver 포함.
별도 설치 불필요.

### 실행
```bash
export PATH="/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:$PATH"
cd <project>/formal
sby -f <module>.sby
```

### 지원 SMT solver

| solver | sby 설정 |
|--------|----------|
| Z3 4.15.5 | `smtbmc z3` |
| Yices 2.7.0 | `smtbmc yices` |
| Bitwuzla 1.0 | `smtbmc bitwuzla` |
| Boolector 3.2.4 | `smtbmc boolector` |
| CVC5 1.0.1 | `smtbmc cvc5` |

### Windows 주의사항
- `lib/`도 PATH에 포함해야 DLL 로드됨
- `mode prove`는 Windows에서 병렬 프로세스 문제로 실패할 수 있음 → `mode bmc` 대체

---

## §7 자주 발생하는 버그 패턴

### 초기값 미지정 (Unconstrained Initial State)
```verilog
// 문제: i_rst_n 없이 시작하면 r_stop이 임의값(1)으로 시작 가능
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) r_stop <= 0;
    else if (cond_a) begin
        if (cond_b) r_stop <= 1;
        // ← else 없음! cond_b 불충족 시 stale 1 유지
    end
    else r_stop <= 0;
end
// 수정: else r_stop <= 0; 추가
```

### Vacuous Assume (과제약)
```verilog
// 위험: 불가능한 assume → 모든 assert가 trivially pass
assume(a == 1 && a == 0); // UNSAT → vacuous pass
```

### $past() 초기 사이클
```verilog
// f_past_valid=0인 첫 사이클에서 $past()는 X (미정의)
// → f_past_valid 체크로 보호 필수
if (f_past_valid && condition)
    assert($past(signal) == expected);
```

---

## §8 결과 해석

| sby 결과 | 의미 | 대응 |
|----------|------|------|
| `PASS` | depth 내 모든 assert 통과 | depth 증가 또는 prove 모드로 완전 증명 |
| `FAIL` | CEX 발견 (`engine_0/trace.vcd`) | VCD 파형 분석 → RTL 수정 |
| `UNREACHABLE` (cover) | 지정 상태 도달 불가 | depth 증가 또는 assume 완화 |
| `ERROR` | 툴/설정 문제 | design.log 확인 |

CEX trace 파일: `<module>/engine_0/trace.vcd`, `trace_tb.v`

---

## §9 검증 속성 작성 체크리스트

- [ ] 리셋 후 초기 상태 검증 (P_reset)
- [ ] FSM state validity (undefined state 진입 불가)
- [ ] 출력 발생 조건: `$past()` 기반 원인-결과 검증
- [ ] 상태 전이: 허용된 전이만 발생
- [ ] FIFO/카운터: overflow/underflow 불가
- [ ] CDC: 동기화 체인 깊이 검증 (cover)
- [ ] f_past_valid 체크 여부
- [ ] assume이 satisfiable인지 확인 (vacuous pass 방지)

---

## §10 SVA (SystemVerilog Assertions)

Yosys 0.40+ / sby에서 SVA concurrent assertion 지원.  
절차적 formal과 달리 temporal operator로 멀티사이클 속성을 직접 표현.

### 기본 구문 비교

| 스타일 | 사용 | 장점 |
|--------|------|------|
| 절차적 (`always @(posedge clk) assert(...)`) | Verilog-only 설계, 간단한 속성 | Yosys 완전 지원, `$past()` 사용 가능 |
| SVA concurrent (`assert property (...)`) | SystemVerilog, 멀티사이클 속성 | 표준 문법, temporal operator 지원 |

### Temporal Operators

| 연산자 | 의미 | 예시 |
|--------|------|------|
| `##N` | N사이클 후 | `a ##2 b` — a 후 2사이클 뒤 b |
| `##[m:n]` | m~n사이클 범위 | `req ##[1:4] ack` |
| `\|->` | overlapping implication (같은 사이클) | `a \|-> b` |
| `\|=>` | non-overlapping implication (다음 사이클) | `a \|=> b` |
| `always` | 항상 성립 | `always valid` |
| `s_eventually` | 언젠가 성립 | `s_eventually done` |

### sequence / property 블록

재사용 가능한 시간 패턴(`sequence`)과 속성 정의(`property`) 블록으로 복잡한 멀티사이클 속성 구조화.

### sby에서 SVA 사용 시 주의

```verilog
// .sby [script]: read -formal 대신 read -sv 사용
read -sv <module>.sv
hierarchy -top <module>
prep -top <module>
```

- `$past()` → SVA에서는 `##1` 또는 `|=>` 로 대체
- `disable iff (!rst_n)` → 절차적의 `if (!rst_n)` 보호와 동일
- Yosys SVA 지원 수준: 기본 temporal(`##`, `|->`, `|=>`) 지원, 복잡한 sequence 일부 미지원

상세 패턴 → `references/sva-patterns.md`

---

## Cross-Skill 참조

- RTL 설계 규칙, FSM, CDC 패턴 → `verilog-rtl` skill
- UVM 환경과 통합 검증 → `chip-verification` skill
- iCE40/Lattice 합성 검증 → `lattice-fpga` skill
