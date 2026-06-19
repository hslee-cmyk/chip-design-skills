#!/usr/bin/env bash
# program.sh — FPGA SPI Flash / NVCM 프로그래밍
#
# 사용법:
#   bash db/scripts/program.sh              # SPI Flash (Diamond → iceprog fallback)
#   bash db/scripts/program.sh --nvcm       # NVCM 프로그래밍 (비가역!)
#   bash db/scripts/program.sh --cram       # CRAM 직접 프로그래밍 (휘발성, JTAG)
#   bash db/scripts/program.sh --test       # 연결 테스트만
#   bash db/scripts/program.sh --programmer diamond   # Diamond Programmer 강제
#   bash db/scripts/program.sh --programmer iceprog   # iceprog 강제
#   bash db/scripts/program.sh --help       # 도움말
#
# 대상 보드: ICE5LP4K-B-EVN (iCE40 Ultra Breakout Board)
# 프로그래머: 보드 내장 FTDI FT2232H (USB, Interface A)
#
# 프로그래머 선택:
#   Diamond Programmer (기본): D2XX 드라이버, Zadig/WinUSB 불필요
#   iceprog (fallback):        libusb/WinUSB 드라이버 필요 (Zadig)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.sh"

cd "$PROJECT_ROOT"

# ── Diamond Programmer 경로 ──────────────────────────────────
PGRCMD="${PGRCMD:-}"
for _d in \
    "/c/lscc/programmer/diamond/3.14/bin/nt64" \
    "/c/lscc/diamond/3.14/bin/nt64"
do
    [ -z "$PGRCMD" ] && [ -x "$_d/pgrcmd.exe" ] && PGRCMD="$_d/pgrcmd.exe"
done

# ── iceprog 경로 (OSS CAD Suite) ─────────────────────────────
ICEPROG="${ICEPROG:-}"
if [ -z "$ICEPROG" ]; then
    if command -v iceprog &>/dev/null; then
        ICEPROG="iceprog"
    elif [ -x "$OSS_CAD_SUITE/bin/iceprog.exe" ]; then
        ICEPROG="$OSS_CAD_SUITE/bin/iceprog.exe"
    fi
fi

# ── FTDI 디바이스 설정 ────────────────────────────────────────
FTDI_DEVICE="i:0x0403:0x6010"
FTDI_INTERFACE="A"

# ── 옵션 파싱 ────────────────────────────────────────────────
MODE="spi"
TEST_ONLY=0
FORCE_PROGRAMMER=""

show_help() {
    cat <<'USAGE'
FPGA Programming Script (ICE5LP4K-B-EVN)

Usage: bash db/scripts/program.sh [OPTIONS]

Options:
  --test                  연결 테스트만 수행
  --nvcm                  NVCM 프로그래밍 (비가역 OTP!)
  --cram                  CRAM 직접 프로그래밍 (휘발성, 전원 끄면 소멸)
  --programmer diamond    Diamond Programmer 강제 사용
  --programmer iceprog    iceprog 강제 사용
  --help                  도움말

기본값: SPI Flash 프로그래밍 (Diamond Programmer 우선, iceprog fallback)

프로그래머 비교:
  Diamond Programmer  D2XX 드라이버, Zadig 불필요, SPI/NVCM/CRAM 지원
  iceprog             WinUSB 드라이버 필요 (Zadig), SPI/NVCM 지원

모드별 J10 점퍼 위치:
  SPI Flash (기본)    J10 세로 (1-3, 2-4) — Flash 통해 간접 부팅
  NVCM (Diamond)      J10 가로 (1-2, 3-4) — JTAG 직접 연결
  CRAM (Diamond)      J10 가로 (1-2, 3-4) — JTAG 직접 연결 (휘발성)
  NVCM (iceprog)      J10 세로 (1-3, 2-4) — SPI 경유
USAGE
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        --nvcm)          MODE="nvcm"; shift ;;
        --cram)          MODE="cram"; shift ;;
        --test)          TEST_ONLY=1; shift ;;
        --programmer)
            FORCE_PROGRAMMER="${2:-}"
            if [ -z "$FORCE_PROGRAMMER" ]; then
                log_error "--programmer requires: diamond or iceprog"
                exit 1
            fi
            shift 2
            ;;
        --help|-h)       show_help ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# ── 프로그래머 선택 ───────────────────────────────────────────
select_programmer() {
    case "$FORCE_PROGRAMMER" in
        diamond)
            if [ -z "$PGRCMD" ]; then
                log_error "Diamond Programmer not found."
                log_error "PGRCMD 환경변수로 pgrcmd.exe 경로를 지정하세요."
                exit 1
            fi
            echo "diamond"
            ;;
        iceprog)
            if [ -z "$ICEPROG" ]; then
                log_error "iceprog not found. OSS CAD Suite PATH를 설정하세요."
                exit 1
            fi
            echo "iceprog"
            ;;
        "")
            # CRAM 모드는 Diamond 전용
            if [ "$MODE" = "cram" ] && [ -z "$PGRCMD" ]; then
                log_error "CRAM 모드는 Diamond Programmer 전용입니다. pgrcmd.exe를 설치하세요."
                exit 1
            fi
            if [ -n "$PGRCMD" ]; then
                echo "diamond"
            elif [ -n "$ICEPROG" ]; then
                log_warn "Diamond Programmer not found. Falling back to iceprog."
                log_warn "  iceprog는 WinUSB 드라이버(Zadig)가 필요합니다."
                echo "iceprog"
            else
                log_error "프로그래머를 찾을 수 없습니다."
                log_error "  Diamond Programmer: /c/lscc/programmer/diamond/3.14/bin/nt64/pgrcmd.exe"
                log_error "  iceprog: OSS CAD Suite PATH 설정 후 재시도"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown programmer: $FORCE_PROGRAMMER (use 'diamond' or 'iceprog')"
            exit 1
            ;;
    esac
}

# ── MSYS2 → Windows 경로 변환 ────────────────────────────────
to_win_path() {
    if command -v cygpath &>/dev/null; then
        cygpath -w "$1"
    else
        echo "$1" | sed 's|^/\([a-zA-Z]\)/|\1:/|' | sed 's|/|\\|g'
    fi
}

# ── XCF 파일 생성 (Diamond Programmer용) ─────────────────────
#
# SPI 모드: GUI 생성 템플릿(img/$BASE_NAME-spi-programmer.xcf) 기반.
#   파일 경로만 치환. IOVectorData 등 바이너리 필드는 보존.
#   핵심: <AccessMode>SPI Flash Programming</AccessMode> + FPGALoader 구조
#
# NVCM/CRAM 모드: 직접 생성 (GUI 템플릿 없음)
#
PYTHON="/c/Python314/python.exe"
SPI_TEMPLATE="$PROJECT_ROOT/img/$BASE_NAME-spi-programmer.xcf"
SPI_TEMPLATE_PATH="$PROJECT_ROOT/$OUTPUT_DIR/$TOP_MODULE_bitmap.bin"
NVCM_TEMPLATE="$PROJECT_ROOT/img/$BASE_NAME-nvcm-programmer.xcf"
NVCM_TEMPLATE_PATH="$PROJECT_ROOT/$OUTPUT_DIR/$TOP_MODULE_bitmap.nvcm"

CRAM_TEMPLATE="$PROJECT_ROOT/img/$BASE_NAME-cram-programmer.xcf"
CRAM_TEMPLATE_PATH="$PROJECT_ROOT/$OUTPUT_DIR/$TOP_MODULE_bitmap.bin"

# Diamond Programmer log (pgrcmd exit code unreliable in MSYS2 — use log parsing instead)
if command -v cygpath &>/dev/null && [ -n "${APPDATA:-}" ]; then
    DIAMOND_LOG="$(cygpath "$APPDATA")/LatticeSemi/programmer.log"
elif [ -n "${APPDATA:-}" ]; then
    # Manual conversion: C:\Users\...\AppData\Roaming → /c/Users/.../AppData/Roaming
    _drive=$(printf '%s' "$APPDATA" | head -c1 | tr 'A-Z' 'a-z')
    _path=$(printf '%s' "${APPDATA:2}" | tr '\\' '/')
    DIAMOND_LOG="/${_drive}${_path}/LatticeSemi/programmer.log"
elif [ -n "${USERPROFILE:-}" ] && command -v cygpath &>/dev/null; then
    DIAMOND_LOG="$(cygpath "$USERPROFILE")/AppData/Roaming/LatticeSemi/programmer.log"
else
    DIAMOND_LOG="/c/Users/${USERNAME:-$(id -un)}/AppData/Roaming/LatticeSemi/programmer.log"
fi

generate_xcf() {
    local xcf_file="$1"
    local mode="$2"
    local file_path_fwd="$3"   # forward-slash Windows path

    case "$mode" in
        spi)
            if [ ! -f "$SPI_TEMPLATE" ]; then
                log_error "SPI XCF template not found: $SPI_TEMPLATE"
                log_error "img/$BASE_NAME-spi-programmer.xcf 파일이 필요합니다."
                exit 1
            fi
            # 백슬래시 → 포워드슬래시 (템플릿 경로 형식 맞춤)
            local file_fwd="${file_path_fwd//\\//}"
            # 템플릿의 바이너리 데이터를 보존하면서 파일 경로만 치환
            "$PYTHON" -c "
import sys
template, xcf_out, old_path, new_path = sys.argv[1:]
with open(template, 'rb') as f:
    data = f.read()
data = data.replace(old_path.encode(), new_path.encode())
with open(xcf_out, 'wb') as f:
    f.write(data)
" "$SPI_TEMPLATE" "$xcf_file" "$SPI_TEMPLATE_PATH" "$file_fwd"
            ;;
        nvcm)
            if [ ! -f "$NVCM_TEMPLATE" ]; then
                log_error "NVCM XCF template not found: $NVCM_TEMPLATE"
                log_error "img/$BASE_NAME-nvcm-programmer.xcf 파일이 필요합니다."
                exit 1
            fi
            local file_fwd="${file_path_fwd//\\//}"
            "$PYTHON" -c "
import sys
template, xcf_out, old_path, new_path = sys.argv[1:]
with open(template, 'rb') as f:
    data = f.read()
data = data.replace(old_path.encode(), new_path.encode())
with open(xcf_out, 'wb') as f:
    f.write(data)
" "$NVCM_TEMPLATE" "$xcf_file" "$NVCM_TEMPLATE_PATH" "$file_fwd"
            ;;
        cram)
            if [ ! -f "$CRAM_TEMPLATE" ]; then
                log_error "CRAM XCF template not found: $CRAM_TEMPLATE"
                log_error "img/$BASE_NAME-cram-programmer.xcf 파일이 필요합니다."
                exit 1
            fi
            local file_fwd="${file_path_fwd//\\//}"
            "$PYTHON" -c "
import sys
template, xcf_out, old_path, new_path = sys.argv[1:]
with open(template, 'rb') as f:
    data = f.read()
data = data.replace(old_path.encode(), new_path.encode())
with open(xcf_out, 'wb') as f:
    f.write(data)
" "$CRAM_TEMPLATE" "$xcf_file" "$CRAM_TEMPLATE_PATH" "$file_fwd"
            ;;
    esac
}

# ── pgrcmd wrapper: log-based success detection ───────────────
# pgrcmd.exe (CONSOLE subsystem) requires a real Windows console handle to
# initialize its DLLs. Direct bash subprocess invocation fails with
# STATUS_DLL_INIT_FAILED because MSYS2 pipes are not valid console handles.
#
# Fix: use PowerShell WMI Win32_Process.Create, which spawns pgrcmd via the
# WMI service — completely outside the MSYS2 process hierarchy. This gives
# pgrcmd a clean process context with valid system handles.
# Works from both Claude Code subprocess and interactive MSYS2 terminal.
run_pgrcmd() {
    local xcf="$1"
    local win_pgrcmd
    win_pgrcmd=$(cygpath -w "$PGRCMD")

    # Remove stale log so Diamond creates a fresh one each run.
    rm -f "$DIAMOND_LOG"

    powershell.exe -NoProfile -NonInteractive -Command "
\$wmi = [wmiclass]'Win32_Process'
\$result = \$wmi.Create('\"$win_pgrcmd\" -infile \"$xcf\"')
if (\$result.ReturnValue -eq 0 -and \$result.ProcessId) {
    \$p = Get-Process -Id \$result.ProcessId -ErrorAction SilentlyContinue
    if (\$p) { \$p.WaitForExit(30000) }
}
Start-Sleep -Milliseconds 500
" || true

    local log_content=""
    if [ -f "$DIAMOND_LOG" ]; then
        log_content=$(cat "$DIAMOND_LOG" 2>/dev/null || true)
    fi

    [ -n "$log_content" ] && echo "$log_content"

    if echo "$log_content" | grep -q "Operation: successful"; then
        return 0
    fi
    if [ -z "$log_content" ]; then
        log_error "  Diamond log not created — board connected? J10 올바른 위치?"
    fi
    return 1
}

# ── 보드 체크리스트 ───────────────────────────────────────────
show_board_checklist_spi() {
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  ICE5LP4K-B-EVN Board Checklist (SPI Flash 모드)           │"
    echo "├─────────────────────────────────────────────────────────────┤"
    echo "│  [ ] USB Mini-B 케이블 연결됨                              │"
    echo "│  [ ] D3 녹색 LED 점등 (전원 확인)                          │"
    echo "│  [ ] J10: 핀 1-3, 2-4 쇼트 (세로 방향, SPI Flash 선택)    │"
    echo "│  [ ] J9:  Shunt ON (Flash CSn 연결)                        │"
    echo "│  [ ] J51: Shunt ON (12MHz 클럭)                            │"
    echo "│                                                             │"
    echo "│  ┌──J10──┐    J10 세로 = SPI Flash                        │"
    echo "│  │ 1──3  │    Diamond Programmer: Zadig/WinUSB 불필요      │"
    echo "│  │ 2──4  │                                                  │"
    echo "│  └───────┘                                                  │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
}

show_board_checklist_jtag() {
    local mode_label="$1"
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│  ICE5LP4K-B-EVN Board Checklist (${mode_label} 모드)              │"
    echo "├─────────────────────────────────────────────────────────────┤"
    echo "│  [ ] USB Mini-B 케이블 연결됨                              │"
    echo "│  [ ] D3 녹색 LED 점등 (전원 확인)                          │"
    echo "│  [ ] J10: 핀 1-2, 3-4 쇼트 (가로 방향, JTAG 직접 연결)   │"
    echo "│  [ ] J51: Shunt ON (12MHz 클럭)                            │"
    echo "│                                                             │"
    echo "│  ┌──J10──┐    J10 가로 = JTAG 직접                        │"
    echo "│  │ 1  3  │    Diamond Programmer: Zadig/WinUSB 불필요      │"
    echo "│  │ │  │  │                                                  │"
    echo "│  │ 2  4  │                                                  │"
    echo "│  └───────┘                                                  │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
}

# ── Test 모드 ─────────────────────────────────────────────────
if [ $TEST_ONLY -eq 1 ]; then
    PROGRAMMER=$(select_programmer)
    log_info "Programmer: $PROGRAMMER"

    if [ "$PROGRAMMER" = "diamond" ]; then
        log_info "Diamond Programmer: $PGRCMD"
        log_info "Testing connection (scan chain)..."
        XCF_TEMP="$PROJECT_ROOT/db/work/$BASE_NAME/$BASE_NAME_test_$$.xcf"
        BIN_FILE="$OUTPUT_DIR/${TOP_MODULE}_bitmap.bin"
        WIN_BIN=$(to_win_path "$PROJECT_ROOT/$BIN_FILE")
        generate_xcf "$XCF_TEMP" "spi" "$WIN_BIN"
        WIN_XCF=$(to_win_path "$XCF_TEMP")
        run_pgrcmd "$WIN_XCF" && RC=0 || RC=$?
        rm -f "$XCF_TEMP"
    else
        log_info "iceprog: $ICEPROG"
        "$ICEPROG" -d "$FTDI_DEVICE" -I "$FTDI_INTERFACE" -t
        RC=$?
    fi

    [ $RC -eq 0 ] && log_info "Connection OK." || log_error "Connection failed (exit: $RC)"
    exit $RC
fi

# ── SPI Flash 프로그래밍 ──────────────────────────────────────
if [ "$MODE" = "spi" ]; then
    BIN_FILE="$OUTPUT_DIR/${TOP_MODULE}_bitmap.bin"
    if [ ! -f "$BIN_FILE" ]; then
        log_error "Bitstream not found: $BIN_FILE"
        log_error "Run 'bash db/scripts/build.sh' first"
        exit 1
    fi

    PROGRAMMER=$(select_programmer)
    show_board_checklist_spi

    FILE_SIZE=$(stat -c%s "$BIN_FILE" 2>/dev/null || stat -f%z "$BIN_FILE" 2>/dev/null || echo '?')
    log_info "Programming SPI Flash via $PROGRAMMER..."
    log_info "  File: $BIN_FILE ($FILE_SIZE bytes)"

    if [ "$PROGRAMMER" = "diamond" ]; then
        log_info "  Tool: $PGRCMD"
        XCF_TEMP="$PROJECT_ROOT/db/work/$BASE_NAME/$BASE_NAME_spi_$$.xcf"
        WIN_BIN=$(to_win_path "$PROJECT_ROOT/$BIN_FILE")
        generate_xcf "$XCF_TEMP" "spi" "$WIN_BIN"
        WIN_XCF=$(to_win_path "$XCF_TEMP")
        log_info "  XCF:  $XCF_TEMP"
        echo ""
        run_pgrcmd "$WIN_XCF" && RC=0 || RC=$?
        rm -f "$XCF_TEMP"
    else
        log_info "  Tool: $ICEPROG"
        echo ""
        "$ICEPROG" -d "$FTDI_DEVICE" -I "$FTDI_INTERFACE" "$BIN_FILE"
        RC=$?
    fi

    if [ $RC -eq 0 ]; then
        echo ""
        log_info "Programming complete."
        log_info "  → SW1 (CRESET) 버튼 눌러 리셋"
        log_info "  → D2 (DONE LED) 점등 확인"
        log_info "  → 전원 재투입 시 SPI Flash에서 자동 부팅"
    else
        log_error "Programming failed (exit: $RC)"
        if [ "$PROGRAMMER" = "iceprog" ]; then
            log_error "  → Zadig에서 FT2232H Interface 0을 WinUSB로 변경 후 재시도"
            log_error "  → 또는 Diamond Programmer 사용: bash db/scripts/program.sh --programmer diamond"
        fi
    fi
    exit $RC
fi

# ── CRAM 프로그래밍 (Diamond 전용, 휘발성) ────────────────────
if [ "$MODE" = "cram" ]; then
    BIN_FILE="$OUTPUT_DIR/${TOP_MODULE}_bitmap.bin"
    if [ ! -f "$BIN_FILE" ]; then
        log_error "Bitstream not found: $BIN_FILE"
        log_error "Run 'bash db/scripts/build.sh' first"
        exit 1
    fi

    PROGRAMMER=$(select_programmer)
    show_board_checklist_jtag "CRAM"

    log_warn "⚠  CRAM 프로그래밍은 휘발성입니다. 전원을 끄면 소멸됩니다."
    echo ""

    log_info "Programming CRAM via Diamond Programmer (JTAG)..."
    log_info "  File: $BIN_FILE"
    log_info "  Tool: $PGRCMD"

    XCF_TEMP="$PROJECT_ROOT/db/work/$BASE_NAME/$BASE_NAME_cram_$$.xcf"
    WIN_BIN=$(to_win_path "$PROJECT_ROOT/$BIN_FILE")
    generate_xcf "$XCF_TEMP" "cram" "$WIN_BIN"
    WIN_XCF=$(to_win_path "$XCF_TEMP")
    echo ""
    run_pgrcmd "$WIN_XCF" && RC=0 || RC=$?
    rm -f "$XCF_TEMP"

    [ $RC -eq 0 ] && log_info "CRAM programming complete." || log_error "Programming failed (exit: $RC)"
    exit $RC
fi

# ── NVCM 프로그래밍 ───────────────────────────────────────────
if [ "$MODE" = "nvcm" ]; then
    PROGRAMMER=$(select_programmer)

    if [ "$PROGRAMMER" = "diamond" ]; then
        NVCM_FILE="$OUTPUT_DIR/${TOP_MODULE}_bitmap.nvcm"
    else
        NVCM_FILE="$OUTPUT_DIR/${TOP_MODULE}_bitmap.nvcm"
    fi

    if [ ! -f "$NVCM_FILE" ]; then
        log_error "File not found: $NVCM_FILE"
        [ "$PROGRAMMER" = "iceprog" ] && log_error "  iCEcube2 빌드 결과물(.nvcm)이 필요합니다."
        exit 1
    fi

    if [ "$PROGRAMMER" = "diamond" ]; then
        show_board_checklist_jtag "NVCM"
    else
        show_board_checklist_spi
    fi

    log_warn "╔══════════════════════════════════════════════════════════════╗"
    log_warn "║  WARNING: NVCM PROGRAMMING IS IRREVERSIBLE!                 ║"
    log_warn "║  한 번 프로그래밍하면 변경 불가 — 양산용 전용               ║"
    log_warn "╚══════════════════════════════════════════════════════════════╝"
    log_warn ""
    log_warn "File: $NVCM_FILE  Programmer: $PROGRAMMER"
    log_warn ""
    log_warn "Type 'PROGRAM NVCM' to confirm, or anything else to cancel:"
    read -r CONFIRM
    if [ "$CONFIRM" != "PROGRAM NVCM" ]; then
        log_info "NVCM programming cancelled."
        exit 0
    fi

    log_info "Programming NVCM via $PROGRAMMER..."

    if [ "$PROGRAMMER" = "diamond" ]; then
        XCF_TEMP="$PROJECT_ROOT/db/work/$BASE_NAME/$BASE_NAME_nvcm_$$.xcf"
        WIN_BIN=$(to_win_path "$PROJECT_ROOT/$NVCM_FILE")
        generate_xcf "$XCF_TEMP" "nvcm" "$WIN_BIN"
        WIN_XCF=$(to_win_path "$XCF_TEMP")
        run_pgrcmd "$WIN_XCF" && RC=0 || RC=$?
        rm -f "$XCF_TEMP"
    else
        "$ICEPROG" -d "$FTDI_DEVICE" -I "$FTDI_INTERFACE" -n "$NVCM_FILE"
        RC=$?
    fi

    [ $RC -eq 0 ] && log_warn "NVCM programming complete. Device is permanently programmed." \
                  || log_error "NVCM programming failed (exit: $RC)"
    exit $RC
fi
