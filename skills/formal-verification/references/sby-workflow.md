# sby 워크플로우 실전 가이드

## 프로젝트 설정 체크리스트

```
project/
├── formal/
│   ├── <module>.sby
│   └── src/
│       ├── <module>.v          # RTL 사본 + ifdef FORMAL 속성
│       ├── <sub1>_stub.v       # black-box stub
│       └── <sub2>_stub.v
```

## .sby 파일 완전 예시

```ini
[options]
mode bmc          # bmc | prove | cover
depth 25

[engines]
smtbmc z3         # z3 | yices | bitwuzla | boolector

[script]
# 파일명만 (경로 없이) — sby가 src/에 복사 후 실행
read -formal sub1_stub.v
read -formal sub2_stub.v
read -formal top_module.v
hierarchy -top top_module
prep -top top_module

[files]
# .sby 위치 기준 상대 경로
src/sub1_stub.v
src/sub2_stub.v
src/top_module.v
```

**흔한 실수**: `[script]`에 `src/sub1_stub.v` 처럼 경로 포함 → `not found` 에러.  
sby가 `[files]`를 work dir 내 `src/`에 복사한 후 `[script]`를 실행하므로 파일명만 사용.

## Black-box Stub 작성

```verilog
// anyseq: Yosys가 wire를 비결정적 자유 변수로 취급
// → 모든 가능한 출력 조합을 sound하게 모델링

module sub_module (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  i_data,
    output wire        o_valid,
    output wire [7:0]  o_result
);
    (* anyseq *) wire _valid;
    (* anyseq *) wire [7:0] _result;
    assign o_valid  = _valid;
    assign o_result = _result;
endmodule
```

`anyconst`: 상수이지만 임의값 (한 번 정해지면 변하지 않음)  
`anyseq`: 매 사이클마다 독립적으로 임의값

## RTL 파일에 ifdef FORMAL 추가

```verilog
// 원본 RTL 하단에 추가 (또는 모듈 endmodule 직전)

`ifdef FORMAL
    //=================================================================
    // Formal Properties
    //=================================================================
    reg f_past_valid;
    initial f_past_valid = 0;
    always @(posedge clk) f_past_valid <= 1;

    // P1: Reset property
    always @(posedge clk) begin
        if (!rst_n) begin
            assert(state == IDLE);
            assert(counter == 0);
        end
    end

    // P2: State validity
    always @(posedge clk) begin
        if (f_past_valid)
            assert(state <= STATE_MAX);
    end

    // P3: Output causality
    always @(posedge clk) begin
        if (f_past_valid && out_valid)
            assert($past(in_valid) && $past(state) == WORKING);
    end

    // Cover
    always @(posedge clk) begin
        cover(f_past_valid && state == DONE);
    end
`endif
```

## 실행

```bash
# OSS CAD Suite 환경
export PATH="/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:$PATH"
cd project/formal
sby -f module.sby          # -f: 기존 결과 덮어쓰기

# 결과 확인
ls module/                 # engine_0/, logfile.txt, ...
cat module/logfile.txt | tail -20
```

## 결과 디렉토리 구조

```
module/
├── logfile.txt            # 전체 로그
├── engine_0/
│   ├── trace.vcd          # CEX 파형 (FAIL 시)
│   ├── trace_tb.v         # CEX testbench
│   └── design.smt2        # SMT 인코딩 (디버그용)
└── src/                   # 복사된 소스
```

## 결과 해석

| 출력 | 의미 |
|------|------|
| `PASS [bmc]` | depth 내 모든 assert 통과 |
| `FAIL [bmc]` | CEX 발견 |
| `PASS [cover]` | 지정 상태 도달 가능 (trace 생성) |
| `UNREACHABLE [cover]` | depth 내 도달 불가 |
| `ERROR` | 툴/설정 오류 (logfile.txt 확인) |

## Windows/OSS CAD Suite 트러블슈팅

### PATH 설정

OSS CAD Suite는 `bin`과 `lib` 모두 PATH에 추가해야 한다.

```bash
export PATH="/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:$PATH"
```

`lib` 누락 시 `libz3.dll` 등 런타임 오류 발생.

### mode prove 실패 (Windows)

증상: basecase/induction 병렬 실행 시 프로세스 생성 실패.

해결: `.sby`에서 `mode prove` → `mode bmc` + `depth` 증가.

### sby 명령어 미인식

OSS CAD Suite 환경에서 `sby` 미인식 시 PATH 미설정 확인:

```bash
which sby   # /c/oss-cad-suite/oss-cad-suite/bin/sby 확인
```
