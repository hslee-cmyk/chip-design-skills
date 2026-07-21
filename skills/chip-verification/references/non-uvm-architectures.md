# Non-UVM / Legacy 테스트벤치 아키텍처

듀얼탑(hdl_top/hvl_top) 구조와 레이어드 테스트벤치 원칙은 UVM 전용이 아니다.
이 문서는 UVM을 쓰지 않는(또는 아직 도입하지 않은) 프로젝트에서 동일한 구조적 판단을
어떻게 내릴지 다룬다. `refmodel-patterns.md`, `regression-strategy.md`와 마찬가지로
Digital/AMS 공통 참조 파일이다.

## 1. 테스트벤치 진화 6세대 — 어디까지 필요한가

UVM은 테스트벤치 개념을 새로 발명한 것이 아니라, 이미 쓰이던 구조를 표준 클래스
라이브러리로 "포장"한 것이다. 프로젝트가 실제로 어느 세대까지 필요한지 먼저 판단한다.

| 세대 | 구조 | 특징 | 한계 | 적합한 상황 |
|------|------|------|------|------------|
| G1. Linear | 단일 module, 고정 자극 순서 | DUT 피드백 없음, 수동 출력 확인 | 시나리오 늘면 유지보수 불가 | 컴파일/리셋 스모크 테스트, 5가지 이하 조합의 combinational 블록 |
| G2. File-based | `$readmemh`로 외부 벡터 주입 | 여전히 DUT 상태 무관하게 순서대로 주입 | DUT ready와 무관한 자극 | 벡터 재생 기반 회귀(레거시 벤치 이관 초기) |
| G3. State-machine | FSM이 DUT 출력 보고 다음 자극 결정 | 프로토콜 handshake 가능 | 작성자가 명시한 시나리오만 커버 | 프로토콜 1~2개, 코너케이스가 유한한 leaf 모듈 |
| G4. Linear-random | `$random`/`$urandom` + seed | 매 run 다른 입력 | 제약 없는 랜덤 → 불법 조합, 체크 없음 | 단독으로는 비권장 (G5와 결합) |
| G5. Self-checking | `rand`/`constraint` + scoreboard | 무인 overnight 회귀 가능 | 팀마다 구조가 달라 재사용 안 됨 | **UVM 없이도 팀 표준만 있으면 충분한 지점** — 재사용 범위가 팀 내부 |
| G6. UVM | agent/driver/monitor/sequencer/env/test 표준 패키징 | 컴포넌트 재사용, factory override, config_db | 초기 셋업 비용, 소규모 블록엔 과잉 | VIP를 여러 프로젝트/여러 팀이 재사용, SoC 레벨 통합 |

**판단 규칙**: G5(self-checking, class-based, virtual interface 사용)에서 멈추는 것은
"UVM을 못 배워서"가 아니라 정당한 아키텍처 선택일 수 있다 — 재사용 범위가 한 팀·한 IP를
넘지 않는다면 UVM의 factory/config_db/phase 오버헤드는 투자 대비 이득이 없다.

## 2. 듀얼탑 구조는 UVM 전용이 아니다

### 왜 hdl_top/hvl_top으로 나누는가

`hdl_top`/`hvl_top` 분리는 UVM의 발명품이 아니라, e(Verisity)의 eRM(2001) → Vera 기반
RVM(Synopsys, 2003) → VMM/OVM을 거쳐 UVM까지 그대로 이어진 패턴이다. class-based
검증 컴포넌트가 처음 등장한 시점부터 이미 "synthesizable 계층"과 "non-synthesizable
계층"을 분리할 이유가 있었다.

분리 이유는 UVM 유무와 무관하게 세 가지다:

1. **에뮬레이션/합성 호환**: hdl_top(DUT + interface + clock/reset gen)만 합성 가능해야
   emulation 플랫폼에 올릴 수 있다. hvl_top의 class 코드는 애초에 합성 대상이 아니다.
2. **타이밍 vs 비-타이밍 분리**: hdl_top은 `@(posedge clk)` 등 타이밍에 종속된 코드,
   hvl_top은 트랜잭션 레벨의 비-타이밍 로직. gate-level(SDF 타이밍 annotated) 시뮬레이션
   전환 시 hdl_top 내부의 netlist만 교체하면 되고 hvl_top은 손대지 않는다.
3. **DUT 교체 용이성**: RTL ↔ gate-level netlist ↔ (AMS의 경우 analog model)을
   hdl_top 내부에서만 바꾸면, hvl_top(검증 환경)은 그대로 재사용된다 — UVM 컴포넌트가
   있든 없든 동일하게 성립하는 이점.

### hvl_top, UVM 베이스클래스 없이

`uvm_component`/`uvm_sequence`/factory/`uvm_config_db` 없이도 순수 SystemVerilog
class + virtual interface로 동일한 dual-top 구조를 구현할 수 있다("UVM sans UVM"
패턴 — Siemens/Rich Edelman 화이트페이퍼가 이 접근을 다룬다).

```systemverilog
// hdl_top.sv — 합성 가능 계층 (UVM 유무 무관, 동일)
module hdl_top;
    logic clk, rst_n;
    my_if vif(clk, rst_n);          // interface (signal layer)

    my_dut dut (
        .clk(clk), .rst_n(rst_n),
        .data_in(vif.data_in), .data_out(vif.data_out),
        .valid(vif.valid), .ready(vif.ready)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    // virtual interface 핸들을 hvl_top으로 넘김 — config_db 없이 함수 인자로 직접 전달
    initial hvl_top::run(vif);
endmodule
```

```systemverilog
// hvl_top.sv — class-based 검증 계층, UVM 베이스클래스 없음
package hvl_top;
    import my_bfm_pkg::*;

    class env;
        my_driver   drv;
        my_monitor  mon;
        my_scoreboard scb;

        function new(virtual my_if vif);
            drv = new(vif);
            mon = new(vif);
            scb = new();
            mon.item_collected.connect(scb.check);  // 콜백/이벤트, TLM analysis port 아님
        endfunction

        task run();
            fork
                drv.run();
                mon.run();
            join_any
        endtask
    endclass

    task automatic run(virtual my_if vif);
        env e = new(vif);
        e.run();
    endtask
endpackage
```

`uvm_component_utils`, `build_phase`, `run_test()` 대신 plain constructor + `task run()`을
쓴다는 점만 다르고, **hdl_top/hvl_top 분리 자체, virtual interface를 통한 연결, 계층
구조(driver/monitor/scoreboard)는 동일하다.** 이는 SKILL.md의 듀얼탑 다이어그램이
"UVM 전용"이 아니라 "class-based 검증 계층 전반"에 적용됨을 보여준다.

## 3. Flat(단일-top) 구조 — 언제 정당한가

듀얼탑을 굳이 쓰지 않고 하나의 top module 안에서 DUT+TB를 전부 인스턴스화하는 구조.

```systemverilog
module tb_top;
    logic clk, rst_n;
    logic [7:0] data_in, data_out;
    logic       valid, ready;

    my_dut dut(.*);

    // task 기반 BFM: 신호 조작과 트랜잭션 API를 한 module 안에 둠
    task automatic send(input [7:0] d);
        @(posedge clk);
        data_in <= d;
        valid   <= 1;
        @(posedge clk iff ready);
        valid <= 0;
    endtask

    // self-checking: 결과를 직접 비교
    initial begin
        logic [7:0] expected;
        rst_n = 0; #20 rst_n = 1;
        send(8'hA5);
        expected = 8'hA5 + 1;   // 스펙에 따른 예측
        @(posedge clk iff valid == 0);
        if (data_out !== expected)
            $error("Mismatch: exp=%0h got=%0h", expected, data_out);
        $finish;
    end
endmodule
```

**정당한 경우:**
- Unit-level TB — 단일 combinational 블록, 프로토콜이 1개뿐인 leaf 모듈
- 1회성 디버그 세션 (특정 시나리오 하나 재현)
- 재사용 범위가 "이 파일 하나"를 넘지 않을 것이 확실한 경우

**부채가 되는 경우 (flat → 최소 layer 분리로 승격해야 하는 신호):**
- 같은 BFM 로직(task)을 두 번째 테스트벤치에 복붙하기 시작함
- `send()` task 안에 체크 로직까지 섞여 있어 자극과 검증을 분리할 수 없음
- 프로토콜이 2개 이상으로 늘어남 (예: 버스 프로토콜 + 인터럽트)
- gate-level/timing 시뮬레이션 전환이 예정되어 있음 → 이 시점에 dual-top 전환 필요

## 4. 레이어드 테스트벤치 원칙 (UVM 이전부터 존재)

Signal/Command/Functional/Scenario/Test 5계층은 UVM이 만든 것이 아니라 UVM이
표준 패키징한 것이다. 계층 자체는 UVM 유무와 무관하게 성립한다.

| 계층 | 책임 | UVM 매핑 | Non-UVM 매핑 |
|------|------|---------|-------------|
| Signal | interface, clocking block, modport — RTL과 물리적 연결 | `virtual interface` | 동일 (변화 없음) |
| Command | 저수준 driver/monitor, 프로토콜 assertion, 핀 토글 ↔ 트랜잭션 변환 | `uvm_driver`/`uvm_monitor` | plain class + `virtual interface` 멤버, task 기반 API |
| Functional | 복합 오퍼레이션(DMA read/write 등)을 command 단위로 분해, self-check | `uvm_agent`, `uvm_scoreboard` | class 조합(driver+monitor+checker), 콜백/이벤트로 연결 |
| Scenario | 제약 있는 파라미터로 시나리오 스트림 생성 | `uvm_sequence` | task/class 기반 stimulus generator (`rand`+`constraint`는 UVM 없이도 사용 가능) |
| Test | 최상위 지휘 — 무엇을 실행할지 결정, 직접 동작 안 함 | `uvm_test` | top-level `initial`/`program` 블록 |

**핵심 포인트**: `rand`/`constraint`, virtual interface, class 상속·다형성은
전부 SystemVerilog 언어 기능이지 UVM 라이브러리 기능이 아니다. UVM이 추가하는 것은
factory(런타임 타입 교체), config_db(전역 설정 전달), phase(build/run/report 동기화)
3가지뿐이며, 이 3가지가 필요 없다면 계층 구조는 그대로 두고 이 부분만 생략할 수 있다.

## 5. UVM 없이 쓸 수 있는 재사용 패턴

### 5.1 Config object — plain struct/class

```systemverilog
// uvm_config_db 없이: config를 생성자 인자로 명시적 전달
typedef struct packed {
    int unsigned baud_div;
    bit          parity_en;
    int unsigned timeout_cycles;
} uart_cfg_t;

class uart_driver;
    virtual uart_if vif;
    uart_cfg_t      cfg;

    function new(virtual uart_if vif, uart_cfg_t cfg);
        this.vif = vif;
        this.cfg = cfg;
    endfunction
endclass
```
`uvm_config_db#(uart_cfg_t)::set(...)`가 하는 "계층 간 암묵적 전달"을 포기하는 대신,
생성자 인자로 명시적 전달 — 컴포넌트 트리가 얕을 때(2~3단)는 이쪽이 오히려 추적하기 쉽다.

### 5.2 Virtual interface 기반 재사용

```systemverilog
class bfm_base #(type IF_TYPE = virtual generic_if);
    IF_TYPE vif;
    function new(IF_TYPE vif); this.vif = vif; endfunction
    virtual task drive(); endtask   // 하위 클래스에서 override
endclass

class spi_bfm extends bfm_base #(virtual spi_if);
    task drive(); /* SPI 전용 핀 토글 */ endtask
endclass
```
parameterized class + virtual interface만으로 프로토콜별 BFM을 다형적으로 교체 —
factory override 없이도 동일 효과(단, 런타임 스위칭이 아니라 컴파일 타임 바인딩).

### 5.3 Directed → constrained-random (UVM 없이 확장)

```systemverilog
class stimulus_gen;
    rand bit [7:0] data;
    rand bit [3:0] delay;
    constraint c_delay { delay inside {[1:8]}; }

    task automatic run(uart_driver drv, int n);
        repeat (n) begin
            void'(this.randomize());
            drv.send(data, delay);
        end
    endtask
endclass
```
`uvm_sequence` 없이도 `rand`/`randomize()`/`constraint`는 그대로 쓸 수 있다 —
directed test에서 constrained-random으로 넘어가는 데 UVM 도입이 전제조건이 아니다.

### 5.4 인터페이스 기반 컴포넌트 재사용 across testcase

BFM class를 package로 묶고, 여러 top-level testcase 모듈이 동일 package를 import.
UVM의 `env`/`test` 계층 없이도 "환경 재구성"은 package + class 조합으로 달성 가능.

## 6. 의사결정 기준

### Dual-top vs Flat

| 조건 | 권장 구조 |
|------|----------|
| Gate-level/SDF 타이밍 시뮬레이션 예정 | **Dual-top 필수** — hdl_top 내부만 netlist로 교체 |
| Emulation 플랫폼(HW-assisted) 사용 예정 | **Dual-top 필수** — hvl_top이 합성 대상에서 빠져야 함 |
| 동일 검증 환경을 여러 DUT 버전(RTL→netlist→analog)에 재사용 | **Dual-top** |
| 테스트케이스가 3개 이상, BFM 재사용 필요 | **최소 Dual-top 또는 레이어 분리** |
| Unit-level TB, 1~2개 프로토콜, 팀 내부 전용 | **Flat으로 충분** |
| 1회성 디버그, 코드 수명 < 1주 | **Flat** |

### UVM vs Non-UVM class-based (G5)

| 조건 | 권장 |
|------|------|
| VIP를 여러 프로젝트/여러 팀이 재사용 | **UVM** — factory override, config_db 표준화 이득이 셋업 비용을 상회 |
| SoC 레벨 통합, 다수 IP 조합 | **UVM** — phase 동기화, register model(RAL) 필요 |
| 신규 팀원이 프로젝트 표준(자체 규약)에 이미 익숙 | **UVM 없이 G5 유지** — 학습 곡선 회피 |
| 소규모 IP, 프로토콜 1~2개, 프로젝트 수명 < 6개월 | **UVM 없이 G5 유지** |
| 런타임 컴포넌트 타입 교체(factory override)가 실제로 필요 | **UVM** — 이 기능은 plain class로 대체 어렵다 |

## 7. Legacy/Non-UVM 테스트벤치 안티패턴

OVM→UVM 전환의 핵심 동기 자체가 "드라이버/체커가 DUT 및 서로에게 강결합되어 있던"
구조적 문제 해결이었다. 아래는 UVM 유무와 무관하게 새 `verilog-tb-architect-advisor`가
구조가 굳어지기 전에 잡아야 할 패턴이다.

| 안티패턴 | 증상 | 문제 | 해결 |
|---------|------|------|------|
| Top module에 자극 하드코딩 | `initial` 블록 안에 `data_in <= 8'hA5;` 같은 리터럴이 직접 나열 | 두 번째 테스트 작성 시 전체 복붙, 재사용 불가 | 자극 로직을 `task`/`class` (BFM)로 추출, top은 호출만 |
| Checker가 driver 안에 내장 | `send()` task 안에서 바로 `if (data_out != exp) $error` | 자극 생성과 검증이 분리 안 돼 새 시나리오마다 checker 재작성 | driver/checker를 별도 함수·컴포넌트로 분리 (Command/Functional 계층 분리) |
| 프로토콜-무관 시퀀싱과 핀 토글이 뒤섞임 | "3개 패킷 보내기" 로직 안에 `@(posedge clk)` 핀 조작이 직접 등장 | 프로토콜이 바뀌면 시나리오 로직까지 다시 작성 | Scenario 계층(무엇을 보낼지)과 Command 계층(어떻게 핀을 흔들지)을 분리 |
| Global 변수/계층적 참조(`tb_top.dut.internal_reg`)로 DUT 내부 직접 접근 | 여러 파일에서 동일 hierarchical path를 참조 | virtual interface 우회, 계층 바뀌면 전부 깨짐; 재사용/이식 불가 | interface의 모니터 포트로만 관측, 내부 신호 필요 시 assertion/checker를 interface에 바인딩 |
| BFM에 시나리오 로직 혼입 | task 하나가 "3개 보내고 리셋하고 다시 5개" 같은 특정 테스트 절차를 통째로 구현 | 그 task는 해당 테스트에서만 재사용 가능 | BFM은 단일 트랜잭션 단위 API(`send`, `receive`)만 제공, 절차는 상위 scenario에 위치 |
| Config 값이 코드 곳곳에 매직넘버로 산재 | `#10`, `8'h5A` 같은 리터럴이 여러 파일에 중복 | 스펙 변경 시 누락 수정 위험 | §5.1의 config struct/class로 단일화 |

**판단 규칙(에이전트용)**: 위 표의 "증상" 열에 해당하는 코드가 보이면 — 그것이 UVM
환경이든 아니든 — "새 컴포넌트로 분리할지 vs 기존에 접을지"를 판단할 때 재사용 범위
(테스트케이스 1개 한정인가, 여러 개에서 쓰이는가)를 기준으로 삼는다. 재사용 범위가
1개를 넘는 순간 위 표의 "해결" 열로 리팩터링을 권고한다.

## 참고 자료

- [Testbench Evolution (6 Generations)](https://chipverify.com/verification/testbench-evolution) — ChipVerify
- [Testbench Architecture: Layered Verification](https://www.electronics-ed.com/2026/04/testbench-architecture-layered-verification.html)
- [Testbench architecture – Layered view](https://www.verifsudha.com/2016/07/27/testbench-architecture-layered-view/)
- [DUAL TOP UVM Architecture Issue](https://verificationacademy.com/forums/uvm/dual-top-uvm-architecture-issue) — Verification Academy
- [How are two tops (hvl_top and hdl_top) run in one simulation?](https://verificationacademy.com/forums/t/how-are-two-tops-hvl-top-and-hdl-top-run-in-one-simulation/40787) — Verification Academy
- [From Simulation to Emulation: 3 Steps to a Portable SystemVerilog/UVM Testbench](https://semiwiki.com/eda/5744-from-simulation-to-emulation-3-steps-to-a-portable-systemverilog-uvm-testbench/) — SemiWiki
- [FROM SIMULATION TO EMULATION – A FULLY REUSABLE UVM FRAMEWORK](https://www.academia.edu/10384392/FROM_SIMULATION_TO_EMULATION_A_FULLY_REUSABLE_UVM_FRAMEWORK_INTRODUCTION)
- [UVM Sans UVM: An Approach to Automating UVM Testbench Writing](https://resources.sw.siemens.com/en-US/white-paper-uvm-sans-uvm-an-approach-to-automating-uvm-testbench-writing/) — Siemens/Rich Edelman
- [UVM Sans UVM (DVCon paper PDF)](https://dvcon-proceedings.org/wp-content/uploads/uvm-sans-uvm-an-approach-to-automating-uvm-testbench-writing.pdf)
- [RVM — Reference Verification Methodology](https://semiengineering.com/knowledge_centers/eda-design/verification/methodology/rvm/) — Semiconductor Engineering
- [Universal Verification Methodology](https://en.wikipedia.org/wiki/Universal_Verification_Methodology) — Wikipedia (eRM/RVM/VMM/OVM 계보)
- [Writing Testbenches: Functional Verification of HDL Models](https://link.springer.com/book/10.1007/978-1-4615-0302-6) — Janick Bergeron, Springer
- [Bus functional model](https://en.wikipedia.org/wiki/Bus_functional_model) — Wikipedia
- [What is a Bus Functional Model (BFM)?](https://verificationacademy.com/forums/t/what-is-a-bus-functional-model-bfm/32708) — Verification Academy
- [Using bind for Class-based Testbench Reuse with Mixed-Language Designs](https://www.doulos.com/media/1300/snug09_paper.pdf) — Doulos, SNUG San Jose 2009
- [Gate level simulations: verification flow and challenges](https://www.edn.com/gate-level-simulations-verification-flow-and-challenges/) — EDN
- [Netlist Enabled Emulation Platform for Accelerated Gate Level Verification](https://dvcon-proceedings.org/wp-content/uploads/1B1_DVCon_India_2023_Final_Paper_6285.pdf) — DVCon India 2023
