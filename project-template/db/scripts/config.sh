#!/usr/bin/env bash
# config.sh — {{PROJECT_NAME}} 빌드 공유 설정
# 이 파일이 **유일한 프로젝트별 설정점**이다. 다른 스크립트는 `source config.sh` 로 이 값을 참조한다.
# (build.sh / build_icecube2.sh / build_yosys.sh / program.sh 는 공통 머신 — 보통 수정 불필요.)

# ── 프로젝트 루트 (이 파일 기준 ../../) ──────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── 프로젝트 식별 ────────────────────────────────────────────
PROJECT="{{PROJECT_NAME}}"
# db/work/<BASE_NAME>/ 작업 디렉토리 및 iCEcube2 프로젝트 base 이름.
# (venezia 예: PROJECT='venezia-fpga' 이지만 BASE_NAME='venezia' 였음 — 다를 수 있으니 명시.)
BASE_NAME="{{PROJECT_NAME}}"   # <!-- 필요 시 짧은 base 이름으로 수정 -->

# ── 디바이스 설정 ────────────────────────────────────────────
DEVICE="iCE5LP4K"              # <!-- 예: iCE5LP4K -->
DEVICE_NEXTPNR="u4k"           # <!-- nextpnr-ice40 디바이스: u4k(iCE5LP4K) 등 -->
PACKAGE="SWG36"                # <!-- 예: SWG36 -->
PACKAGE_LOWER="swg36"
TOP_MODULE="{{PROJECT_NAME}}_top"   # <!-- 실제 top 모듈명으로 수정 -->

# ── Verilog 조건부 컴파일 Define ─────────────────────────────
DEFINES=""                     # <!-- 예: "CE5 INC_EXT_DTOP" -->

# ── 툴 경로 (버전 고정하지 않음 — env/PATH 우선, 없으면 설치된 최신 버전 탐색) ─
ICECUBE2_PATH="${ICECUBE2_PATH:-$(ls -d /c/lscc/iCEcube2.* 2>/dev/null | sort -V | tail -1)}"
OSS_CAD_SUITE="${OSS_CAD_SUITE:-/c/oss-cad-suite/oss-cad-suite}"
if [ -d "$OSS_CAD_SUITE" ] && ! command -v yosys &>/dev/null; then
    export PATH="$OSS_CAD_SUITE/bin:$OSS_CAD_SUITE/lib:$PATH"
fi

# ── 소스 파일 (프로젝트 루트 기준) ───────────────────────────
# 칩 공유 RTL은 db/design 서브모듈 아래에 있다.
VERILOG_SRCS=(
    # <!-- db/design/<block>/mdl/*.v 목록을 채울 것 -->
    # db/ip/<pll>.v
    # db/top/${TOP_MODULE}.v
)
INCLUDE_PATHS=(
    # <!-- 예: db/design/d_xxx/mdl -->
)

# ── 제약 파일 ────────────────────────────────────────────────
PCF="db/sdc/${TOP_MODULE}_${PACKAGE_LOWER}_io.pcf"
SDC="db/sdc/${TOP_MODULE}_ice.sdc"

# ── iCEcube2 프로젝트 파일 / 출력 ────────────────────────────
SBT_PROJECT="db/work/${BASE_NAME}/${BASE_NAME}_sbt.project"
SYN_PROJECT="db/work/${BASE_NAME}/${BASE_NAME}_syn.prj"
OUTPUT_DIR="img"
BUILD_DIR="db/work/${BASE_NAME}/${BASE_NAME}_Implmnt"

# ── 유틸리티 함수 ────────────────────────────────────────────
log_info()  { echo "[INFO]  $*"; }
log_warn()  { echo "[WARN]  $*" >&2; }
log_error() { echo "[ERROR] $*" >&2; }

check_files_exist() {
    local missing=0
    for f in "$@"; do
        if [ ! -f "$PROJECT_ROOT/$f" ]; then
            log_error "File not found: $f"
            missing=$((missing + 1))
        fi
    done
    return $missing
}
