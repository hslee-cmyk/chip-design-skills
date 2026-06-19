#!/usr/bin/env bash
# build_icecube2.sh — iCEcube2 배치 빌드 스크립트
#
# 사용법: bash db/scripts/build_icecube2.sh
#
# 빌드 흐름:
#   Phase 1: 합성 → P&R → Timer (타이밍 리포트 생성)
#   ── 타이밍 게이트 ── (리포트/SDC/제약 표시, 사용자 승인 필요)
#   Phase 2: Bitmap 생성 → img/ 복사
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

cd "$PROJECT_ROOT"

# ── iCEcube2 설치 확인 ───────────────────────────────────────
if [ ! -d "$ICECUBE2_PATH" ]; then
    log_error "iCEcube2 not found at: $ICECUBE2_PATH"
    log_error "Set ICECUBE2_PATH environment variable to your installation path"
    exit 1
fi

SBT_BACKEND="$ICECUBE2_PATH/sbt_backend"
if [ ! -d "$SBT_BACKEND" ]; then
    log_error "SBT backend not found at: $SBT_BACKEND"
    exit 1
fi

# 플랫폼 감지
if [ -f "$SBT_BACKEND/bin/win32/opt/synpwrap/synpwrap.exe" ]; then
    PLATFORM="win32"
elif [ -f "$SBT_BACKEND/bin/linux/opt/synpwrap/synpwrap" ]; then
    PLATFORM="linux"
else
    log_error "Cannot detect iCEcube2 platform (win32/linux)"
    exit 1
fi

SBT_BIN="$SBT_BACKEND/bin/$PLATFORM/opt"

# ── 소스 파일 확인 ───────────────────────────────────────────
log_info "Checking source files..."
check_files_exist "${VERILOG_SRCS[@]}" "$PCF" "$SDC"
if [ $? -ne 0 ]; then
    log_error "Missing source files. Aborting."
    exit 1
fi

# ── 출력 디렉토리 준비 ───────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

# ── 환경 변수 설정 (TCL 스크립트 및 synpwrap에 전달) ─────────
export PROJECT_ROOT
export ICECUBE2_PATH
export SBT_DIR="$SBT_BACKEND"
export SYNPLIFY_PATH="${SYNPLIFY_PATH:-$ICECUBE2_PATH/synpbase}"
export LM_LICENSE_FILE="${LM_LICENSE_FILE:-$ICECUBE2_PATH/license/license.dat}"

# ── TCL 스크립트 경로 ────────────────────────────────────────
TCL_SCRIPT="$SCRIPT_DIR/synth_icecube2.tcl"

log_info "Starting iCEcube2 batch build..."
log_info "  Device:  $DEVICE / $PACKAGE"
log_info "  Top:     $TOP_MODULE"
log_info "  Defines: $DEFINES"
log_info ""

if ! command -v tclsh &>/dev/null; then
    log_error "tclsh not found. Install Tcl or use Git Bash (includes tclsh via MSYS2/mingw64)."
    exit 1
fi
TCLSH_CMD="tclsh"
log_info "Running TCL script via: $TCLSH_CMD ($(command -v tclsh))"

# ══════════════════════════════════════════════════════════════
#  Phase 1: Synth → Route → Timer
# ══════════════════════════════════════════════════════════════
log_info "=== Phase 1: Synthesis + Place & Route + Timer ==="
"$TCLSH_CMD" "$TCL_SCRIPT"
RC=$?
if [ $RC -ne 0 ]; then
    log_error "Phase 1 FAILED (exit code: $RC)"
    exit $RC
fi

# ══════════════════════════════════════════════════════════════
#  Timing Gate: 리포트 표시 및 사용자 승인
# ══════════════════════════════════════════════════════════════
IMPL_DIR="$PROJECT_ROOT/db/work/$BASE_NAME/$BASE_NAME_Implmnt"
TIMING_RPT="$IMPL_DIR/sbt/outputs/router/${TOP_MODULE}_timing.rpt"
SBT_SDC="$IMPL_DIR/${TOP_MODULE}_sbt.sdc"
USER_SDC="$PROJECT_ROOT/$SDC"
USER_PCF="$PROJECT_ROOT/$PCF"

# Git Bash 경로(/c/...) → Windows 경로(C:\...) 변환 함수
to_win() { echo "$1" | sed 's|^/\([a-zA-Z]\)/|\1:\\|' | sed 's|/|\\|g'; }

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              TIMING GATE — 비트스트림 생성 전 확인             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Timing Report — Clock Frequency Summary ───────────────
if [ -f "$TIMING_RPT" ]; then
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  [1] Timing Report"
    echo "│      $(to_win "$TIMING_RPT")"
    echo "├─────────────────────────────────────────────────────────────┤"
    # Clock Frequency Summary 섹션 전체 표시 (ToC 제외 — Number of clocks: 행부터)
    sed -n '/Number of clocks:/,/End of Clock Frequency Summary/p' "$TIMING_RPT" \
        | sed 's/^/│  /'
    echo "├─────────────────────────────────────────────────────────────┤"
    # PASS/FAIL 판정
    sed -n '/Number of clocks:/,/End of Clock Frequency Summary/p' "$TIMING_RPT" \
        | grep "Clock:" \
        | while IFS= read -r line; do
            freq=$(echo "$line" | sed -n 's/.*Frequency:[[:space:]]*\([0-9.]*\).*/\1/p')
            target=$(echo "$line" | sed -n 's/.*Target:[[:space:]]*\([0-9.]*\).*/\1/p')
            clk=$(echo "$line" | sed -n 's/Clock:[[:space:]]*\([^|]*\).*/\1/p' | sed 's/[[:space:]]*$//')
            if [ -n "$freq" ] && [ -n "$target" ]; then
                freq_int=$(echo "$freq" | sed 's/\.//' | sed 's/^0*//')
                target_int=$(echo "$target" | sed 's/\.//' | sed 's/^0*//')
                if [ "${freq_int:-0}" -ge "${target_int:-0}" ] 2>/dev/null; then
                    echo "│  [PASS]  $clk — ${freq} MHz (target: ${target} MHz)"
                else
                    echo "│  [FAIL]  $clk — ${freq} MHz (target: ${target} MHz) ** TIMING VIOLATION **"
                fi
            else
                echo "│  [ N/A]  $clk — no flip-flop paths (SDC constraint 없음)"
            fi
        done
    echo "└─────────────────────────────────────────────────────────────┘"
else
    log_warn "Timing report not found: $TIMING_RPT"
fi

echo ""

# ── 2. SDC 파일 (사용자 SDC) ─────────────────────────────────
if [ -f "$USER_SDC" ]; then
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  [2] User SDC"
    echo "│      $(to_win "$USER_SDC")"
    echo "├─────────────────────────────────────────────────────────────┤"
    sed 's/^/│  /' "$USER_SDC"
    echo "└─────────────────────────────────────────────────────────────┘"
fi

echo ""

# ── 3. Synplify 합성 후 제약 (SCF) ────────────────────────────
SYNTH_SCF="$IMPL_DIR/$BASE_NAME.scf"
if [ -f "$SYNTH_SCF" ]; then
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  [3] Synplify SCF (합성 후 제약)"
    echo "│      $(to_win "$SYNTH_SCF")"
    echo "├─────────────────────────────────────────────────────────────┤"
    sed 's/^/│  /' "$SYNTH_SCF"
    echo "└─────────────────────────────────────────────────────────────┘"
fi

echo ""

# ── 4. SBT Edifparser SDC (합성→P&R 변환 제약) ────────────────
SBT_TEMP_SDC="$IMPL_DIR/sbt/Temp/sbt_temp.sdc"
if [ -f "$SBT_TEMP_SDC" ]; then
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  [4] SBT Temp SDC (edifparser 변환)"
    echo "│      $(to_win "$SBT_TEMP_SDC")"
    echo "├─────────────────────────────────────────────────────────────┤"
    sed 's/^/│  /' "$SBT_TEMP_SDC"
    echo "└─────────────────────────────────────────────────────────────┘"
fi

echo ""

# ── 5. SBT 생성 SDC (P&R 후 실제 적용된 제약) ────────────────
if [ -f "$SBT_SDC" ]; then
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  [5] SBT SDC (P&R 적용)"
    echo "│      $(to_win "$SBT_SDC")"
    echo "├─────────────────────────────────────────────────────────────┤"
    sed 's/^/│  /' "$SBT_SDC"
    echo "└─────────────────────────────────────────────────────────────┘"
fi

echo ""

# ── 6. PCF 핀 제약 ───────────────────────────────────────────
if [ -f "$USER_PCF" ]; then
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  [6] Pin Constraints (PCF)"
    echo "│      $(to_win "$USER_PCF")"
    echo "├─────────────────────────────────────────────────────────────┤"
    sed 's/^/│  /' "$USER_PCF"
    echo "└─────────────────────────────────────────────────────────────┘"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── 사용자 승인 ──────────────────────────────────────────────
read -r -p "[GATE] Proceed to bitmap generation? [y/N] " REPLY
if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
    log_warn "Bitmap generation cancelled by user."
    log_info "Route outputs are preserved at: $IMPL_DIR/"
    log_info "To generate bitmap later:"
    log_info "  tclsh $TCL_SCRIPT --bitmap-only"
    exit 0
fi

# ══════════════════════════════════════════════════════════════
#  Phase 2: Bitmap Generation
# ══════════════════════════════════════════════════════════════
log_info "=== Phase 2: Bitmap Generation ==="
"$TCLSH_CMD" "$TCL_SCRIPT" --bitmap-only
RC=$?
if [ $RC -ne 0 ]; then
    log_error "Phase 2 (Bitmap) FAILED (exit code: $RC)"
    exit $RC
fi

# ── 결과 확인 ────────────────────────────────────────────────
BIN_FILE="$OUTPUT_DIR/${TOP_MODULE}_bitmap.bin"
if [ -f "$BIN_FILE" ]; then
    log_info "Build SUCCESS"
    log_info "Output: $BIN_FILE ($(stat -c%s "$BIN_FILE" 2>/dev/null || stat -f%z "$BIN_FILE" 2>/dev/null || echo '?') bytes)"
else
    log_warn "Build completed but .bin file not found at expected path"
    log_warn "Check $OUTPUT_DIR/ for output files"
fi

ls -la "$OUTPUT_DIR/"*.bin "$OUTPUT_DIR/"*.hex "$OUTPUT_DIR/"*.nvcm 2>/dev/null || true
exit 0
