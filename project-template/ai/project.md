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


## Directory Structure

> ⚠️ **채우기 규칙 (신규 프로젝트 project.md 작성 시)** — 이 블록을 실제 값으로 교체할 때:
> 1. `find <루트> -maxdepth 2 -not -path '*/.git/*'` 실행 → **실제 존재하는 항목만** 트리에 포함 (없으면 해당 행 제거)
> 2. `find .ai -maxdepth 1` 실행 → `.ai/` 서브항목도 실제 목록으로 교체
> 3. 각 `#` 뒤 주석: 한 줄 역할 설명 필수 (공백 금지)
> 4. `{{...}}` 플레이스홀더 모두 실제 값으로 대체; 이 `>` 채우기 규칙 블록 삭제

```
{{PROJECT_NAME}}/
├── .ai/
│   ├── project.md              # 이 파일
│   ├── conventions.md          # RTL 코딩 규칙 (프로젝트 고유)
│   ├── KNOWLEDGE_MAP.md        # 지식 시스템 정본 경계
│   ├── rd-pdca-substeps.json   # chip-cto-lead RD-PDCA fan-out
│   ├── ops/                    # build.md · servers.md · MCP 가이드
│   ├── analysis/               # 모듈 분석서 ({module}.analysis.md)
│   ├── design-knowledge/       # hard IP · known issues
│   ├── bkit-templates/         # PDCA 템플릿 override
│   ├── rag/                    # preflight.py · audit_search.py
│   └── adr/                    # Architecture Decision Records
├── .claude/agents/             # 프로젝트 RTL subagents (chip-design-skills 배포)
├── CLAUDE.md                   # 작업 지침 진입점 (정본)
├── AGENTS.md / GEMINI.md       # → CLAUDE.md stub
├── db/
│   ├── design/                 # 칩 공유 RTL — git submodule ({{SUBMODULE_DIR}})
│   ├── ip/                     # IP 코어 (PLL/SERDES 등) — 없으면 제거
│   ├── top/                    # FPGA 전용 top wrapper ({{TOP_MODULE}}.v)
│   ├── sdc/                    # 타이밍·핀 제약 (.sdc / .pcf / .lpf)
│   ├── scripts/                # 빌드·프로그래밍 스크립트 — 없으면 제거
│   └── work/                   # 빌드 산출물 (대부분 gitignore)
├── docs/                       # bkit PDCA 문서 + solutions/
├── formal/                     # formal/lint workspace (공유 RTL submodule 밖 — guard hook 강제)
├── graphify-out/               # 그래프 출력 (GRAPH_REPORT.md)
├── img/                        # 비트스트림 산출물 — 없으면 제거
├── refs/                       # 데이터시트·핀맵·사양서
└── sim/                        # 시뮬레이션 IP — 없으면 제거
```

> 칩 공유 RTL 마운트: `git submodule add <url> db/design`. 빌드: `bash db/scripts/build.sh` (상세 `build.md`).

## Conditional Compilation / Build 요약

→ 코딩 규칙은 `conventions.md`, 빌드·클럭·프로그래밍은 `build.md`, 원격 검증 서버는 `servers.md`.
