<!--
════════════════════════════════════════════════════════════
  TEMPLATE FILL GUIDE — 신규 프로젝트 project.md 작성 시
  이 주석 블록 전체를 따른 뒤 삭제, 나머지 ⚠️ 경고는 유지
════════════════════════════════════════════════════════════

[0] 작업 전 실행 (실제 상태 확인)
    find <루트> -maxdepth 2 -not -path '*/.git/*'   ← 디렉토리 구조 확인
    find .ai -maxdepth 1                             ← .ai/ 서브항목 확인
    git submodule status                             ← submodule URL·커밋 확인

[1] {{...}} 플레이스홀더 → 모두 실제 값으로 대체
    {{PROJECT_NAME}}    : 레포 루트 디렉토리명 (예: venezia-fpga)
    {{PROJECT_TAGLINE}} : 한 줄 기능 설명 (예: PCM → COLA 프로토콜 변환기)
    {{SUBMODULE_DIR}}   : db/design 서브모듈 레포명 (예: todoc-chip-venezia-digi-t0)
    {{TOP_MODULE}}      : db/top/ 최상위 .v 파일명 (확장자 제외)

[2] Device / Target 테이블 → 실제 디바이스 정보로 채움

[3] Architecture 트리 → <꺾쇠> 예시를 실제 모듈명으로 교체
    · <chip_core_top>  : 공유 RTL 최상위 모듈명
    · <main_ctrl>      : 메인 제어 FSM 모듈명
    · d_<rx/enc/dec/cfg> : 실제 기능 블록 디렉토리명
    · 예시 설명 주석("아래는 예시 — 실제 구조로 교체") 제거

[4] Signal Flow → 실제 데이터 경로 기술 (ASCII 화살표 또는 단계 나열)

[5] Directory Structure 트리
    · [0]의 find 결과 기준으로 없는 행 제거, 새 디렉토리 추가
    · 각 노드 # 뒤 주석: 한 줄 역할 설명 필수 (빈 칸 금지)
    · "없으면 제거" 표시된 선택 항목은 실제 존재 시만 포함

[6] 완료 후 이 FILL GUIDE 주석 블록 전체 삭제, ⚠️ 경고 2개는 유지
════════════════════════════════════════════════════════════
-->
# Project: {{PROJECT_NAME}}

{{PROJECT_TAGLINE}}

## Device / Target

| 항목 | 값 |
|------|-----|
| FPGA / ASIC | |
| Package | |
| Tool | |
| Clock | |

## Architecture

모듈 인스턴스 계층(instantiation hierarchy) + 블록별 역할.
(의존성·신호 연결은 `graphify-out/GRAPH_REPORT.md`와 동기화 권장. 코딩 규칙: 공유 코어 `ext_`, 기능 블록 `d_*`.)

```
{{PROJECT_NAME}}_top                         # FPGA 전용 top wrapper (db/top/)
├── <하드 IP>                                # 예: SB_HFOSC(OSC), SB_IO/SB_IO_OD, PLL / ASIC 아날로그 매크로·패드
└── <chip_core_top>                          # 칩 공유 RTL — {{SUBMODULE_DIR}}/ (submodule, FPGA·ASIC 공용)
    ├── clk / rst_sync                       # 클럭 분배 · 리셋 동기화
    ├── <main_ctrl>                          # 메인 제어 FSM
    │
    ├── d_<rx>/        # 입력 인터페이스 블록  (프로토콜 수신: slave·interface·register·checker)
    ├── d_<enc>/       # 인코딩/송신 블록      (변조·토큰·CRC 생성)
    ├── d_<dec>/       # 디코딩/수신 블록      (복조·CDR·라인코딩·CRC 검증)
    └── d_<cfg>/       # 호스트 제어 인터페이스 (I2C/SPI slave·register interface)
```

<!-- ⚠️ 위 트리의 <꺾쇠> 예시를 실제 모듈명으로 교체 후 이 주석도 삭제 (FILL GUIDE [3]) -->

## Signal Flow

<!-- 주요 데이터 경로 기술 후 이 주석 삭제. 예:
입력 RX → 디코딩 → 코어 처리 → 인코딩 → 출력 TX, 제어는 I2C 레지스터 경유 -->

## Directory Structure

> ⚠️ 갱신 시 `find <루트> -maxdepth 2 -not -path '*/.git/*'` 먼저 실행 후 반영 (기억에서 쓰면 누락 발생)

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
