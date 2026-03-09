# RTL Code Review Checklist

## 합성 관련

### Latch 방지
- [ ] always_comb 시작에서 모든 출력에 기본값 할당 (권장)
- [ ] 또는 모든 if에 else, 모든 case에 default 있음
- [ ] ⚠️ 기본값 할당이 있으면 Latch 없음 — 잘못된 latch 보고 금지!

Latch 판단 순서, GOOD/BAD 패턴 상세: `synthesis-check.md` > Latch 방지 참조

### 리셋 정책
- [ ] 제어 신호 (state, valid, ready): 리셋 있음
- [ ] 데이터 경로: 리셋 없음 (valid로 게이팅)
- [ ] 리셋 극성 일관 (i_rst_n = active low)
- [ ] sensitivity list가 리셋 사용 여부와 일치

```verilog
// 제어 신호: 리셋 필요
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_valid <= 1'b0;
    end else begin
        r_valid <= i_valid;
    end
end

// 데이터 경로: 리셋 불필요
always_ff @(posedge i_clk) begin
    r_data <= i_data;
end
```

### CDC 처리
- [ ] 클럭 도메인 경계 식별됨
- [ ] Slow→Fast, 1-bit level: 2FF synchronizer 사용
- [ ] Slow→Fast, 1-bit pulse: Pulse Synchronizer 사용
- [ ] Fast→Slow, 1-bit: Handshake (Req/Ack) (2FF 사용 불가!)
- [ ] Multi-bit 순차적: Gray code + 2FF (포인터, 카운터)
- [ ] Multi-bit 스트림: Async FIFO 사용
- [ ] CDC 경로에 타이밍 제약 설정됨

### Blocking/Non-blocking
- [ ] always_ff: `<=` (non-blocking) 사용
- [ ] always_comb: `=` (blocking) 사용
- [ ] 혼용 없음

### Bit-Width Safety
- [ ] localparam/parameter에 explicit bit-width 필요한가? → 불필요하면 unsized 권장
- [ ] `[W-1:0] var = expr` : max(expr) < 2^W 인가? (파라미터 전 범위)
- [ ] W가 log2 계열 함수에서 파생되었나? → `$clog2` 사용 확인
- [ ] 파라미터가 2의 거듭제곱이 아닌 값을 가질 수 있나? → 경계값 테스트
- [ ] pointer width로 FIFO/Memory 전체를 인덱싱할 수 있나?

---

## 타이밍 관련

### 사이클 정확성
- [ ] 각 레지스터에 사이클 번호 주석
- [ ] 조합 로직에 [same] 표시
- [ ] 파이프라인 지연 계산 정확

### Data/Valid 정렬
- [ ] data와 valid가 같은 사이클에 유효
- [ ] valid 파이프라인이 data와 동일 단계

```verilog
// GOOD: data와 valid가 동일 사이클에 유효하도록 정렬
// 데이터 경로: 리셋 불필요
always_ff @(posedge i_clk) begin
    r_data <= c_processed;  // [N → N+1]
end

// 제어 신호: 리셋 필요
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) r_valid <= 1'b0;
    else          r_valid <= i_valid;  // [N → N+1]
end
```

### 타이밍 크리티컬 경로
- [ ] 긴 조합 경로 식별됨
- [ ] 필요시 레지스터 삽입
- [ ] 파이프라인 밸런싱 확인

---

## 코딩 스타일

### 네이밍 규칙
- [ ] 입력: `i_` prefix
- [ ] 출력: `o_` prefix
- [ ] 와이어: `w_` prefix
- [ ] 레지스터: `r_` prefix
- [ ] 조합 출력: `c_` prefix
- [ ] 클럭/리셋: `i_clk`, `i_rst_n` (입력이므로 `i_` prefix)
- [ ] 모듈: lowercase_with_underscores
- [ ] 파라미터: UPPER_CASE
- [ ] 인스턴스: `u_` prefix
- [ ] Top wire: `w_<instance>_<port>` (예: `w_u_proc_o_result`)
- [ ] BSC 통과 신호: `_a` (BSC 입력), `_z` (BSC 출력)

### Always 블록 분리

#### 필수
- [ ] 동일 신호를 여러 always에서 할당하지 않음
- [ ] always_ff에서 `<=` (non-blocking) 사용
- [ ] always_comb에서 `=` (blocking) 사용

#### 권장 (유연 적용 - 가독성 최우선)

> 분리는 가독성을 위한 **수단**이지, 그 자체가 **목적**이 아님.
> 분리가 오히려 가독성을 해친다면, 합치는 것이 정답.

- [ ] 하나의 always → 하나의 출력 (단, 단순 로직은 통합 허용)
- [ ] 순차/조합 로직 분리 (단, 가독성이 우선)

#### 통합/분리 판단 기준
- [ ] 통합 시 회로 동작이 한눈에 파악되는가? → **통합 허용**
- [ ] 분리 시 관련 로직이 흩어져 이해하기 어려워지는가? → **통합 허용**

| 상황 | 권장 | 이유 |
|------|------|------|
| 단순 capture (FSM state, pipeline) | 통합형 | 단순 구조, 관련성 높음 |
| 관련 카운터 그룹 (동일 enable) | 통합형 | 논리적 연관, 유사 구조 |
| 파이프라인 데이터 경로 | 통합형 | 모두 단순 지연, 동일 구조 |
| 제어 구조가 약간 다르지만 단순 | 통합형 | 가독성에 영향 없음 |
| 제어 구조가 복잡하게 다름 | **분리형** | 각 로직 독립적 이해 |
| 서로 다른 기능 블록 | **반드시 분리** | 모듈성, 재사용성 |

### 주석
- [ ] 모듈 헤더에 설명 있음
- [ ] 총 레이턴시 명시
- [ ] 사이클 주석 포함
- [ ] 복잡한 로직에 설명 있음

---

## 기능 관련

### 리셋 동작
- [ ] 리셋 시 모든 레지스터 초기화
- [ ] 초기값이 기능에 적합
- [ ] FSM이 초기 상태로 복귀

### 에지 케이스
- [ ] 오버플로우 처리
- [ ] 언더플로우 처리
- [ ] 경계값 동작 확인
- [ ] 빈/풀 상태 처리 (FIFO)

### FSM
- [ ] 작성: 2-process 패턴 사용 (state_reg + next_state/output)
- [ ] 타입: Mealy machine 기본
- [ ] 인코딩: One-hot (< 8 states), Binary (≥ 8 states)
- [ ] default 상태 처리됨
- [ ] 모든 상태 전이 정의됨
- [ ] 불법 상태에서 복구 가능
- [ ] 기본값 할당으로 latch 방지 (`c_next_state = r_state;`)

---

## Race Condition 체크

### 순서 의존성
- [ ] 같은 사이클에 읽기/쓰기 순서 확인
- [ ] 조합 루프 없음
- [ ] 피드백 경로에 레지스터 있음

```verilog
// BAD: 조합 루프
assign c_a = c_b + 1;
assign c_b = c_a - 1;  // 순환!

// GOOD: 레지스터로 끊음
assign c_a = r_b + 1;
always_ff @(posedge i_clk) r_b <= c_a - 1;
```

### 미정의 동작
- [ ] X/Z 전파 가능성 확인
- [ ] 초기화되지 않은 메모리 접근 없음
- [ ] 범위 초과 인덱싱 없음

---

## 최종 체크

### 합성 경고
- [ ] Latch 경고 없음
- [ ] Multi-driver 경고 없음
- [ ] Width mismatch 경고 없음
- [ ] Unconnected port 경고 없음

### 시뮬레이션
- [ ] 기본 기능 테스트 통과
- [ ] 리셋 시퀀스 확인
- [ ] 에지 케이스 테스트
- [ ] Coverage 목표 달성 (Code 95%, Func 90%)
