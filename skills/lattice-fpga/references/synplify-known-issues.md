# Synplify Pro Known Issues & Workarounds

iCEcube2에 포함된 Synplify Pro (L-2016.09L+ice40) 관련 알려진 이슈와 우회 방법.

## 1. Mapper Crash: Register Array Dynamic Indexing

### 증상

```
Error Code [nlsim.c:2897 Equivalence check failed on net N_16]
@E::Internal Error in m_generic.exe
```

- fpga_mapper (Map & Optimize) 단계에서 internal error로 크래시
- `compiler` 및 `premap` 단계는 정상 통과

### 원인

`reg [7:0] r_mem [0:N]` 형태의 레지스터 배열을 **동적 인덱스**로 읽을 때 발생:

```verilog
// BAD: mapper equivalence check 크래시 유발
reg [7:0] r_lut [0:31];
wire [7:0] w_data = r_lut[r_addr];  // 동적 인덱싱
```

mapper의 내부 equivalence checker가 대규모 레지스터 배열의 동적 MUX를 처리하지 못하고 크래시.

### 효과 없는 우회 시도

| 시도 | 결과 |
|------|------|
| `/* synthesis syn_preserve = 1 */` on array | 동일 에러 |
| `set_option -verification_mode 0` in .prj | 동일 에러 |

### 해결: 명시적 case MUX로 변환

동적 인덱싱을 제거하고 always 블록 내 case문으로 풀어서 MUX를 명시적으로 기술:

```verilog
// GOOD: 명시적 case MUX — Synplify mapper 정상 통과
reg [7:0] r_lut [0:31] /* synthesis syn_preserve = 1 */;
reg [7:0] r_lut_rd;

always @(*) begin
    case (r_addr)
        5'd0:  r_lut_rd = r_lut[0];
        5'd1:  r_lut_rd = r_lut[1];
        // ... (모든 엔트리 명시)
        5'd31: r_lut_rd = r_lut[31];
    endcase
end

wire [7:0] w_data = r_lut_rd;  // case MUX 출력 사용
```

### 영향 범위

- iCEcube2 2020.12 (Synplify L-2016.09L+ice40) 에서 확인
- 배열 크기 32 이상에서 발생 (소규모 배열은 미확인)
- Yosys 합성에서는 동적 인덱싱 정상 동작 (Synplify 전용 이슈)
- 레지스터 배열 write (`r_lut[r_addr] <= data`)는 동적 인덱싱 사용 가능 — 크래시는 read 경로에서만 발생

### 발견 일자

2026-03-20, venezia-fpga 프로젝트 sync-xfr-extension 구현 중 Duration LUT (32ch x 8-bit) 동적 read에서 발생.
