# Covergroup Patterns

## 1. Covergroup 기본 구조

### Event-Triggered Covergroup

```systemverilog
covergroup cg_bus @(posedge clk);
    cp_addr: coverpoint addr;
    cp_data: coverpoint data;
endgroup
```

### Function-Triggered Covergroup (권장)

```systemverilog
covergroup cg_transaction with function sample(bit [3:0] cmd, bit [31:0] addr, bit [7:0] data);
    option.per_instance = 1;
    option.name = "txn_cg";

    cp_cmd:  coverpoint cmd;
    cp_addr: coverpoint addr;
    cp_data: coverpoint data;
endgroup

// 사용: cg_transaction.sample(tr.cmd, tr.addr, tr.data);
```

`with function sample()` 방식 장점:
- 외부 변수 의존 없음 (self-contained)
- 조건부 sampling 용이
- 명시적 파라미터로 가독성 향상

---

## 2. Coverpoint 패턴

### 2.1 자동 Bin

```systemverilog
coverpoint tr.opcode;  // 모든 값에 자동 bin 생성

coverpoint tr.opcode {
    option.auto_bin_max = 16;  // bin 수 제한
}
```

**주의**: 자동 bin은 분석성이 낮음 — 명시적 bin 권장

### 2.2 명시적 Bin (범위/값)

```systemverilog
coverpoint tr.addr {
    bins zero      = {0};
    bins low       = {[1:63]};
    bins mid       = {[64:191]};
    bins high      = {[192:254]};
    bins max       = {255};
    bins others[]  = default;  // 나머지 각각 별도 bin
}
```

### 2.3 전이 Bin

```systemverilog
coverpoint tr.state {
    // 단일 전이
    bins idle_to_active = (IDLE => ACTIVE);
    bins active_to_done = (ACTIVE => DONE);

    // 다단계 전이
    bins full_cycle = (IDLE => ACTIVE => DONE => IDLE);

    // Wildcard 전이
    bins any_to_idle = (default => IDLE);

    // 연속 반복
    bins idle_repeat = (IDLE [*3]);        // IDLE 3회 연속
    bins active_burst = (ACTIVE [*2:5]);   // 2~5회 연속
}
```

### 2.4 Wildcard Bin

```systemverilog
coverpoint tr.cmd {
    wildcard bins read_any  = {4'b00??};  // 00xx 패턴
    wildcard bins write_any = {4'b01??};  // 01xx 패턴
    wildcard bins ctrl_any  = {4'b1???};  // 1xxx 패턴
}
```

### 2.5 Illegal / Ignore Bin

```systemverilog
coverpoint tr.addr {
    bins valid_range[] = {[0:99]};
    illegal_bins reserved = {[100:127]};  // 발생 시 시뮬레이션 에러
    ignore_bins unused    = {[128:255]};  // coverage 계산에서 제외
}
```

- `illegal_bins`: 해당 값이 관찰되면 에러 → 프로토콜 위반 검출
- `ignore_bins`: coverage 분모에서 제외 → 불필요 bin 제거

---

## 3. Cross Coverage

### 3.1 기본 Cross

```systemverilog
covergroup cg_cross;
    cp_cmd:  coverpoint cmd  { bins read = {0}; bins write = {1}; }
    cp_size: coverpoint size { bins byte_sz = {1}; bins word_sz = {4}; }
    cx_cmd_size: cross cp_cmd, cp_size;
endgroup
```

### 3.2 Cross with binsof/intersect

```systemverilog
cx_cmd_addr: cross cp_cmd, cp_addr {
    // 특정 조합 무시
    ignore_bins no_write_high = binsof(cp_cmd.write) && binsof(cp_addr.high);

    // 특정 조합만 선택
    bins read_low = binsof(cp_cmd.read) && binsof(cp_addr) intersect {[0:63]};
}
```

### 3.3 Concatenated Value Coverpoint

다수 필드의 조합을 하나의 coverpoint로 표현:

```systemverilog
covergroup cg_config;
    // 개별 coverpoint 대신 연결(concatenation)
    cp_mode_config: coverpoint {word_length, stop_bits, parity_en} {
        bins mode_8n1 = {3'b100};  // 8-bit, 1-stop, no parity
        bins mode_8e1 = {3'b101};  // 8-bit, 1-stop, even parity
        bins mode_7n2 = {3'b010};  // 7-bit, 2-stop, no parity
        // ... 의미 있는 조합만 열거
    }
endgroup
```

장점: cross 대비 명시적 bin 제어가 용이하고, 불가능 조합을 자연스럽게 배제

---

## 4. Coverage Options (Critical Three)

### per_instance × merge_instances 조합

| per_instance | merge_instances | 동작 |
|:---:|:---:|------|
| 0 | 0 | 가중 평균 (기본) — 인스턴스 구분 없이 평균 |
| 1 | 0 | 인스턴스별 분리 — 각 인스턴스 개별 리포트 |
| 0 | 1 | 논리적 OR (병합) — 어떤 인스턴스든 hit이면 covered |
| 1 | 1 | 병합 + 인스턴스별 조회 가능 |

**권장**: 일반적으로 `per_instance=1` (각 인스턴스가 독립 coverage 보유)

### 주요 Options

```systemverilog
covergroup cg;
    // Instance-level options
    option.per_instance = 1;          // 인스턴스별 분리
    option.name = "my_cg";           // 리포트에 표시될 이름
    option.at_least = 5;             // bin 최소 hit 횟수 (기본 1)
    option.goal = 100;               // 목표 % (기본 100)
    option.weight = 2;               // 전체 coverage 내 가중치
    option.comment = "Bus coverage";

    // Type-level options (모든 인스턴스에 적용)
    type_option.strobe = 1;          // posedge에서 안정값 샘플링
    type_option.merge_instances = 1; // 인스턴스 간 병합
endgroup
```

### type_option.strobe

- `strobe = 1`: 클록 posedge 시점의 **안정된 값**만 샘플링
- 글리치(glitch) 방지에 유용
- `@(posedge clk)` 트리거와 함께 사용 권장

---

## 5. Assertion Coverage

### 5.1 Cover Property

```systemverilog
// 시퀀스 완료 시 coverage 수집
cover property (@(posedge clk) disable iff (!rst_n)
    req |-> ##[1:3] gnt
);

// Named cover (추적 용이)
cp_handshake: cover property (@(posedge clk) disable iff (!rst_n)
    valid && ready ##1 !valid
);
```

### 5.2 Cover Sequence

```systemverilog
// 시퀀스 매칭 시 coverage 수집
sequence s_burst;
    req ##1 ack ##1 data[*4] ##1 done;
endsequence

cover sequence (s_burst);
```

### 5.3 Hybrid: Sequence → Covergroup Sampling

assertion 성공 시 covergroup을 sampling하여 **값 분포까지 캡처**:

```systemverilog
// Transfer 완료 시 covergroup sampling
sequence s_end_of_transfer;
    @(posedge clk) psel && penable && pready;
endsequence

covergroup cg_transfer with function sample(bit [31:0] addr, bit write);
    cp_addr:  coverpoint addr  { bins regions[] = {[0:255]}; }
    cp_write: coverpoint write { bins rd = {0}; bins wr = {1}; }
    cx_access: cross cp_addr, cp_write;
endgroup

cg_transfer cg = new();

// 시퀀스 성공 시 샘플링
cover property (s_end_of_transfer) cg.sample(paddr, pwrite);
```

이 패턴의 장점:
- **타이밍** (assertion) + **값 분포** (covergroup)을 동시에 캡처
- False sampling 방지 (프로토콜 완료 확인 후에만 수집)

---

## 6. Bin 설계 전략

### 넓은 필드 추상화

32-bit 주소처럼 넓은 필드는 전체 값 공간을 커버할 수 없다. 전략적 값 선택:

```systemverilog
coverpoint baud_divisor {
    // Powers of 2
    bins pow2[] = {1, 2, 4, 8, 16, 32, 64, 128, 256};
    // 경계값
    bins min_val = {0};
    bins max_val = {16'hFFFF};
    // 표준 baud rate 관련 값
    bins standard[] = {16'd1, 16'd2, 16'd12, 16'd24, 16'd96};
}
```

### Named Bins vs Auto-Bins

| 항목 | Named Bins (권장) | Auto-Bins |
|------|------------------|-----------|
| 분석성 | 높음 — bin 이름으로 의미 파악 | 낮음 — 숫자 범위만 표시 |
| 제어 | 정밀 — 필요한 값만 선택 | 조잡 — 균등 분할 |
| Cross 호환 | 우수 — 의미 있는 cross bin | 폭발적 bin 수 |
| 유지보수 | 명확한 의도 전달 | 의도 불명확 |

### Array of Covergroups (다중 인스턴스)

```systemverilog
// Slave별 개별 coverage
covergroup cg_slave_access with function sample(bit [7:0] addr, bit write);
    option.per_instance = 1;
    cp_addr:  coverpoint addr;
    cp_write: coverpoint write;
endgroup

cg_slave_access slave_cg[NUM_SLAVES];

initial begin
    foreach (slave_cg[i])
        slave_cg[i] = new($sformatf("slave_%0d_cg", i));
end

// 선택적 sampling — 해당 slave만
function void sample_access(int slave_id, bit [7:0] addr, bit write);
    slave_cg[slave_id].sample(addr, write);
endfunction
```

---

## 7. Coding for Analysis

### option.name 설정

```systemverilog
// Constructor에서 설정
function new(string name);
    cg = new();
    cg.option.name = name;  // 리포트에 인스턴스 식별 가능
endfunction

// UVM 환경에서
cg.option.name = get_full_name();  // 계층 경로 포함
```

### 명시적 Bin 레이블로 분석 용이성 확보

```systemverilog
// BAD — auto-bin, 분석 불가
coverpoint addr;  // auto_bin_max개의 "auto[N:M]" bin

// GOOD — named bin, 의미 파악 가능
coverpoint addr {
    bins peripheral_region = {[32'h4000_0000:32'h4000_FFFF]};
    bins sram_region       = {[32'h2000_0000:32'h2000_FFFF]};
    bins flash_region      = {[32'h0800_0000:32'h080F_FFFF]};
    bins system_region     = {[32'hE000_0000:32'hE00F_FFFF]};
}
```

### Anti-pattern: Auto-Bin으로 넓은 필드

```systemverilog
// ANTI-PATTERN — 32-bit 필드에 auto-bin
coverpoint tr.addr;  // 64개 bin, 각각 67M 범위 → 분석 무의미

// ANTI-PATTERN — auto_bin_max로 제한해도 의미 없는 범위
coverpoint tr.addr {
    option.auto_bin_max = 8;  // 범위만 균등 분할, 의미 없음
}
```
