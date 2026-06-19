#!/usr/bin/env bash
# build_yosys.sh — Yosys + nextpnr-ice40 오픈소스 빌드 스크립트
#
# 사용법: bash db/scripts/build_yosys.sh
#
# iCEcube2 없이 오픈소스 툴체인으로 빌드하는 대안 스크립트.
# 결과물은 iCEcube2와 동일한 img/ 디렉토리에 저장.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

cd "$PROJECT_ROOT"

# ── 도구 설치 확인 ───────────────────────────────────────────
MISSING_TOOLS=0
for tool in yosys nextpnr-ice40 icepack; do
    if ! command -v "$tool" &>/dev/null; then
        log_error "Required tool not found: $tool"
        MISSING_TOOLS=$((MISSING_TOOLS + 1))
    fi
done

if [ $MISSING_TOOLS -gt 0 ]; then
    log_error "OSS CAD Suite PATH 설정 후 재시도:"
    log_error "  export PATH=\"/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:\$PATH\""
    log_error "  (또는 config.sh 가 자동 설정)"
    exit 1
fi

# ── 소스 파일 확인 ───────────────────────────────────────────
log_info "Checking source files..."
check_files_exist "${VERILOG_SRCS[@]}" "$PCF"
if [ $? -ne 0 ]; then
    log_error "Missing source files. Aborting."
    exit 1
fi

# ── 빌드 디렉토리 준비 (상대 경로 — MSYS2 도구 호환) ──────
YOSYS_BUILD="db/work/yosys_build"
mkdir -p "$YOSYS_BUILD"
mkdir -p "$OUTPUT_DIR"

JSON_OUT="$YOSYS_BUILD/${TOP_MODULE}.json"
ASC_OUT="$YOSYS_BUILD/${TOP_MODULE}.asc"
BIN_OUT="$OUTPUT_DIR/${TOP_MODULE}_bitmap.bin"
TIMING_RPT="$YOSYS_BUILD/${TOP_MODULE}_timing.rpt"

log_info "Starting Yosys open-source build..."
log_info "  Device:  $DEVICE_NEXTPNR / $PACKAGE_LOWER"
log_info "  Top:     $TOP_MODULE"
log_info "  Defines: $DEFINES"
log_info ""

# ── Define 플래그 구성 ───────────────────────────────────────
DEFINE_FLAGS=""
for def in $DEFINES; do
    DEFINE_FLAGS="$DEFINE_FLAGS -D$def"
done

# Include 경로 구성 (상대 경로 — Yosys는 절대경로 미인식, 상대경로 사용)
INCLUDE_FLAGS=""
for inc in "${INCLUDE_PATHS[@]}"; do
    INCLUDE_FLAGS="$INCLUDE_FLAGS -I$inc"
done

# 소스 파일 목록 (상대 경로 — cd $PROJECT_ROOT 후이므로)
SRC_LIST=""
for src in "${VERILOG_SRCS[@]}"; do
    SRC_LIST="$SRC_LIST $src"
done

# ──────────────────────────────────────────────────────────────
# Step 1: Yosys 합성
# ──────────────────────────────────────────────────────────────
log_info "[1/4] Synthesis (Yosys)..."

yosys -q -l "$YOSYS_BUILD/yosys.log" -p "
    read_verilog $DEFINE_FLAGS $INCLUDE_FLAGS $SRC_LIST;
    synth_ice40 -device u -abc2 -top $TOP_MODULE -json $JSON_OUT
"

if [ ! -f "$JSON_OUT" ]; then
    log_error "Yosys synthesis failed — JSON output not found"
    exit 1
fi
log_info "  Synthesis complete: $JSON_OUT"

# ──────────────────────────────────────────────────────────────
# Step 2: nextpnr Place & Route
# ──────────────────────────────────────────────────────────────
log_info "[2/4] Place & Route (nextpnr-ice40)..."

# SWG36 패키지는 오픈소스 chipdb에 미포함
# → sg48 패키지 + pre-pack Python으로 IO tile 직접 배치
PREPACK="db/scripts/prepack_swg36.py"
log_info "  Using pre-pack IO constraints: $PREPACK"

nextpnr-ice40 \
    --${DEVICE_NEXTPNR} \
    --package sg48 \
    --json "$JSON_OUT" \
    --pcf-allow-unconstrained \
    --pre-pack "$PREPACK" \
    --asc "$ASC_OUT" \
    --freq 24 \
    --ignore-loops \
    --log "$YOSYS_BUILD/nextpnr.log" \
    2>&1 | tail -5

if [ ! -f "$ASC_OUT" ]; then
    log_error "nextpnr P&R failed — ASC output not found"
    exit 1
fi
log_info "  P&R complete: $ASC_OUT"

# ──────────────────────────────────────────────────────────────
# Step 3: Bitstream 생성
# ──────────────────────────────────────────────────────────────
log_info "[3/4] Bitstream generation (icepack)..."

icepack "$ASC_OUT" "$BIN_OUT"

if [ ! -f "$BIN_OUT" ]; then
    log_error "icepack failed — BIN output not found"
    exit 1
fi
log_info "  Bitstream: $BIN_OUT ($(stat -c%s "$BIN_OUT" 2>/dev/null || stat -f%z "$BIN_OUT" 2>/dev/null || echo '?') bytes)"

# ──────────────────────────────────────────────────────────────
# Step 4: 타이밍 분석 (optional)
# ──────────────────────────────────────────────────────────────
if command -v icetime &>/dev/null; then
    log_info "[4/4] Timing analysis (icetime)..."
    icetime -d u4k -p "$PCF" -r "$TIMING_RPT" "$ASC_OUT" 2>&1 | tail -3
    log_info "  Timing report: $TIMING_RPT"
else
    log_warn "[4/4] icetime not found — skipping timing analysis"
fi

# ── 완료 ─────────────────────────────────────────────────────
log_info ""
log_info "Build SUCCESS (Yosys open-source toolchain)"
log_info "Output: $BIN_OUT"
exit 0
