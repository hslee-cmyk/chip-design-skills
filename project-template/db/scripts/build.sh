#!/usr/bin/env bash
# build.sh — FPGA 통합 빌드 래퍼
#
# 사용법:
#   bash db/scripts/build.sh              # 자동 감지 (iCEcube2 우선)
#   bash db/scripts/build.sh --tool yosys # Yosys 강제 사용
#   bash db/scripts/build.sh --clean      # 빌드 출력 정리
#   bash db/scripts/build.sh --help       # 도움말
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

cd "$PROJECT_ROOT"

# ── 옵션 파싱 ────────────────────────────────────────────────
TOOL=""
CLEAN=0

show_help() {
    cat <<'USAGE'
FPGA Build Script

Usage: bash db/scripts/build.sh [OPTIONS]

Options:
  --tool icecube2   Force iCEcube2 toolchain
  --tool yosys      Force Yosys open-source toolchain
  --clean           Remove build outputs and exit
  --help            Show this help

Without --tool, automatically detects available toolchain (iCEcube2 preferred).

Output: img/ directory (*.bin, *.hex, *.nvcm)
USAGE
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --tool)
            TOOL="${2:-}"
            if [ -z "$TOOL" ]; then
                log_error "--tool requires argument: icecube2 or yosys"
                exit 1
            fi
            shift 2
            ;;
        --clean)
            CLEAN=1
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# ── Clean 모드 ───────────────────────────────────────────────
if [ $CLEAN -eq 1 ]; then
    log_info "Cleaning build outputs..."

    # Yosys build directory
    if [ -d "$PROJECT_ROOT/db/work/yosys_build" ]; then
        rm -rf "$PROJECT_ROOT/db/work/yosys_build"
        log_info "  Removed db/work/yosys_build/"
    fi

    # img/ 출력 (사용자 확인)
    if [ -d "$PROJECT_ROOT/$OUTPUT_DIR" ] && ls "$PROJECT_ROOT/$OUTPUT_DIR"/*.bin &>/dev/null 2>&1; then
        log_warn "img/ contains build outputs. Remove? [y/N]"
        read -r REPLY
        if [[ "$REPLY" =~ ^[Yy]$ ]]; then
            rm -f "$PROJECT_ROOT/$OUTPUT_DIR"/*.bin
            rm -f "$PROJECT_ROOT/$OUTPUT_DIR"/*.hex
            rm -f "$PROJECT_ROOT/$OUTPUT_DIR"/*.nvcm
            rm -f "$PROJECT_ROOT/$OUTPUT_DIR"/*_glb.txt
            rm -f "$PROJECT_ROOT/$OUTPUT_DIR"/*_int.hex
            log_info "  Cleaned img/ outputs"
        else
            log_info "  Skipped img/ cleanup"
        fi
    fi

    log_info "Clean complete."
    exit 0
fi

# ── 도구 감지 ────────────────────────────────────────────────
detect_tool() {
    if [ -d "$ICECUBE2_PATH" ]; then
        echo "icecube2"
    elif command -v yosys &>/dev/null && command -v nextpnr-ice40 &>/dev/null; then
        echo "yosys"
    else
        echo "none"
    fi
}

if [ -z "$TOOL" ]; then
    TOOL=$(detect_tool)
    if [ "$TOOL" = "none" ]; then
        log_error "No FPGA toolchain found."
        log_error ""
        log_error "Option 1: Install iCEcube2"
        log_error "  Set ICECUBE2_PATH to your installation directory"
        log_error ""
        log_error "Option 2: Install open-source toolchain"
        log_error "  yosys + nextpnr-ice40 + icestorm (icepack/iceprog)"
        exit 1
    fi
    log_info "Auto-detected toolchain: $TOOL"
fi

# ── 빌드 실행 ────────────────────────────────────────────────
case "$TOOL" in
    icecube2)
        log_info "Building with iCEcube2..."
        exec bash "$SCRIPT_DIR/build_icecube2.sh"
        ;;
    yosys)
        log_info "Building with Yosys (open-source)..."
        exec bash "$SCRIPT_DIR/build_yosys.sh"
        ;;
    *)
        log_error "Unknown tool: $TOOL (use 'icecube2' or 'yosys')"
        exit 1
        ;;
esac
