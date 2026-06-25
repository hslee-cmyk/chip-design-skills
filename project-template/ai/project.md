# Project: {{PROJECT_NAME}}

{{PROJECT_TAGLINE}}  <!-- 한 줄 설명: 무엇을 하는 칩/FPGA인가 -->

## Device / Target

| 항목 | 값 |
|------|-----|
| FPGA / ASIC | <!-- 예: iCE5LP4K (iCE40 Ultra) / ASIC node --> |
| Package | <!-- 예: SWG36 (WLCSP) --> |
| Tool | <!-- 예: iCEcube2 (Synplify Pro) / Radiant / Diamond --> |
| Clock | <!-- 예: 내부 SB_HFOSC 24MHz --> |

## Architecture

모듈 인스턴스 계층(instantiation hierarchy) + 블록별 역할. 아래는 **예시 — 실제 구조로 교체**할 것.
(의존성·신호 연결은 `graphify-out/GRAPH_REPORT.md`와 동기화 권장. 코딩 규칙: 공유 코어 `ext_`, 기능 블록 `d_*`.)

```
{{PROJECT_NAME}}_top                         # FPGA 전용 top wrapper (db/top/)
├── <하드 IP>                                # 예: SB_HFOSC(내부 OSC), SB_IO/SB_IO_OD(I/O 버퍼·open-drain), PLL
│                                            #     ASIC이면 아날로그 매크로/패드
└── <chip_core_top>                          # 칩 공유 RTL — {{SUBMODULE_DIR}}/ (submodule, FPGA·ASIC 공용)
    ├── clk / rst_sync                       # 클럭 분배 · 리셋 동기화
    ├── <main_ctrl>                          # 메인 제어 FSM
    │
    ├── d_<rx>/        # 입력 인터페이스 블록  (예: 프로토콜 수신: slave·interface·register·checker)
    ├── d_<enc>/       # 인코딩/송신 블록      (예: 변조·토큰·CRC 생성)
    ├── d_<dec>/       # 디코딩/수신 블록      (예: 복조·CDR·라인코딩·CRC 검증)
    └── d_<cfg>/       # 호스트 제어 인터페이스 (예: I2C/SPI slave·register interface)
```

> 읽는 법: 최상위 = FPGA 전용 top(하드 IP + 코어 연결), 그 아래 `<chip_core_top>` = `{{SUBMODULE_DIR}}` submodule(공유),
> `d_*` = 기능 블록 디렉토리(데이터 경로). 각 노드 옆에 역할 한 줄을 단다.

## Signal Flow

<!-- 주요 데이터 경로를 단계로 기술. 예: 입력 RX → 디코딩 → 코어 처리 → 인코딩 → 출력 TX, 제어는 I2C 레지스터 경유. -->


## Directory Layout (db/ 구조는 모든 프로젝트 공통)

| 경로 | 내용 |
|------|------|
| `db/` | 하드웨어 빌드 루트 (공통 구조 — `db/README.md`) |
| `db/design/` | **칩 공유 RTL — git submodule** (`{{SUBMODULE_DIR}}`). 수정 시 submodule commit. read-only 취급 |
| `db/ip/` | IP 코어 (PLL/SERDES 등) |
| `db/scripts/` | **공통 빌드/프로그래밍 스크립트** — `config.sh`만 프로젝트별 수정 (`db/scripts/README.md`) |
| `db/sdc/` | 제약 파일(`.sdc` 타이밍 · `.pcf`/`.pdc`/`.lpf` 핀) |
| `db/top/` | FPGA 전용 top wrapper (`<TOP_MODULE>.v`) |
| `db/work/` | 빌드 출력 (`db/work/<BASE_NAME>/…`, 대부분 gitignore) |
| `img/` | 비트스트림 산출물 (`*.bin` SPI · `*.nvcm` OTP) |
| `sim/` | 시뮬레이션 |
| `formal/` | formal/lint 전용 workspace (공유 RTL submodule **밖** — guard hook 강제) |
| `refs/` | 프로젝트 연관 문서 (데이터시트·핀맵·사양서 — `refs/README.md`) |
| `docs/` | bkit PDCA 문서 |
| `.ai/project.md` | 이 파일 — 아키텍처·디렉토리 요약 |
| `.ai/conventions.md` | RTL 코딩 규칙 (프로젝트 고유 항목) |
| `.ai/KNOWLEDGE_MAP.md` | 지식 시스템 정본 경계 |
| `.ai/rd-pdca-substeps.json` | chip-cto-lead RD-PDCA fan-out 프로파일 |
| `.ai/ops/` | 빌드·P&R·서버·MCP 운영 가이드 (`build.md`, `servers.md`, …) |
| `.ai/analysis/` | 모듈별 분석서 (`{module}.analysis.md`) |
| `.ai/design-knowledge/` | hard IP·known issues |
| `.ai/bkit-templates/` | PDCA 템플릿 override (`design`·`do`·`analysis`) |
| `.ai/rag/` | `preflight.py`, `audit_search.py` |
| `.ai/adr/` | Architecture Decision Records |

> 칩 공유 RTL 마운트: `git submodule add <url> db/design`. 빌드: `bash db/scripts/build.sh` (상세 `build.md`).

## Conditional Compilation / Build 요약

→ 코딩 규칙은 `conventions.md`, 빌드·클럭·프로그래밍은 `build.md`, 원격 검증 서버는 `servers.md`.
