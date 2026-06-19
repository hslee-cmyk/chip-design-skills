# Coding Conventions — {{PROJECT_NAME}}

> 🔒 **MUST — RTL 코딩/네이밍 최우선 규칙**: 모든 RTL 신호·모듈·코딩 네이밍은 **`verilog-rtl` skill을 최우선(single source of truth)으로 적용한다.**
> 이 문서의 RTL 관련 항목은 `verilog-rtl` skill 규칙을 **보강·구체화**할 뿐이며, **충돌 시 언제나 `verilog-rtl` skill이 우선**한다.
> - RTL 작성·수정 전 **반드시 `verilog-rtl` skill을 먼저 로드**한다 (스킬 없이 RTL 네이밍을 임의 결정 금지).
> - 이 문서엔 `verilog-rtl` skill에 **없는 프로젝트 고유 규칙만** 추가한다 (예: 칩 접두사, 패키지별 define). 표준 네이밍을 여기서 재정의·변경하지 않는다.
> - 그 외 프로젝트별 항목(<!-- 채울 것 -->)만 보강한다.

## Module Naming  *(프로젝트 고유 — verilog-rtl skill 보강)*
- 칩 공유 모듈 접두사: <!-- 예: `ext_` --> · 기능 블록 디렉토리: <!-- 예: `d_*` -->
- FPGA 전용 탑: <!-- 예: `{{PROJECT_NAME}}_fpga_top` -->

## Signal Naming  *(정본 = `verilog-rtl` skill — 아래는 요약, 충돌 시 skill 우선)*
- camelCase + 접두사: `i_`(input) · `o_`(output) · `io_`(inout) · `w_`(wire) · `r_`(reg) · `c_`(combinational)
- 차동: `_p`/`_n` 접미사 · Active-low: `_n` 접미사
- ⚠️ 위는 편의 요약일 뿐 — 세부·예외는 `verilog-rtl` skill을 따른다.

## Top I/O Restriction (iCEcube2 사용 시)
- **bus index 금지** — Top I/O는 single-bit 이름으로 선언 (`output [2:0] o_x` → `o_x_0/1/2`).
- 이유: iCEcube2 VHDL netlister 버그(`signal[n]`→`signal[n]_wire` OA syntax error). Radiant/Diamond은 해당 없음.

## Conditional Compilation
| Define | 용도 |
|--------|------|
| <!-- 예: CE5 --> | <!-- iCE40 Ultra 전용 --> |
| <!-- 예: INC_EXT_DTOP --> | <!-- 칩 코어 인스턴스 포함 --> |

## Synthesis Attributes (Lattice 예시)
```verilog
/* synthesis syn_keep=1 */          // 신호 유지(최적화 방지)
/* synthesis syn_noprune = 1 */     // 미사용 신호 제거 방지
/* synthesis ROUTE_THROUGH_FABRIC=1 */
```

## Verification
- <!-- 검증 방법론 명시. 예: RTL 검증은 모두 UVM 기반, non-UVM directed TB 금지 -->

## File Encoding
- 소스·텍스트 파일은 **UTF-8 (BOM 없음)**. EUC-KR/CP949면 한글 깨짐 방지 위해 먼저 UTF-8(no BOM) 변환 후 수정.
