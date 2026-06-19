# project-template/ — AI 인프라 스캐폴드

처음 만드는 프로젝트(또는 `.ai` 인프라가 없는 기존 프로젝트)에 적용하는 **AI 관련 인프라 템플릿**.
venezia-fpga의 `.ai/` 구조 + CLAUDE/AGENTS/GEMINI를 일반화한 것이다.

```
project-template/
├── CLAUDE.md / AGENTS.md / GEMINI.md   → <proj>/ (진입점 + 포인터 stub)
├── ai/                                 → <proj>/.ai/
│   ├── project.md       아키텍처·디바이스·디렉토리
│   ├── conventions.md   네이밍·ifdef·Top I/O·합성속성·인코딩·검증 (RTL은 verilog-rtl skill 최우선)
│   ├── build.md         빌드·클럭·프로그래밍·오류대처
│   ├── servers.md       원격 서버·ssh-mcp·xcelium-mcp·tcsh 함정
│   ├── analysis/        RTL 모듈 분석서 (_TEMPLATE.analysis.md + README)
│   ├── knowledge/       재사용 지식(하드IP·known-issues·운영가이드)
│   └── adr/ plans/ experiments/ agent-proposals/ skill-proposals/   (빈 골격)
├── db/                                 → <proj>/db/  (모든 프로젝트 공통 구조)
│   ├── design/   칩 공유 RTL submodule 마운트 지점 (README)
│   ├── scripts/  공통 빌드/프로그래밍 스크립트 — config.sh만 프로젝트별 수정
│   │             (build.sh·build_yosys.sh·build_icecube2.sh·program.sh·synth_icecube2.tcl·prepack)
│   ├── ip/ sdc/ top/   (README stub)
│   └── work/     빌드 출력 (gitignore, .gitkeep)
└── refs/                               → <proj>/refs/  (프로젝트 연관 문서)
```

> `db/` 구조는 **모든 프로젝트 공통**. `db/scripts`의 머신 스크립트는 이 템플릿에서 단일 관리하며,
> 프로젝트별 값은 **`config.sh` 한 곳**(`PROJECT`/`BASE_NAME`/`DEVICE`/`TOP_MODULE`/`DEFINES`/`VERILOG_SRCS`/제약)만 채운다.
> 칩 공유 RTL은 `git submodule add <url> db/design` 으로 마운트.

## 설치
```bash
python install.py --init-ai-infra --project <repo>            # 없는 파일만 생성(안전)
python install.py --init-ai-infra --project <repo> --dry-run  # 미리보기
python install.py --init-ai-infra --project <repo> --force    # 기존 파일 덮어쓰기
```
- **기존 파일은 덮어쓰지 않는다**(skip). 기존 프로젝트에 빠진 부분만 채우기 안전.
- `{{PROJECT_NAME}}`은 repo 폴더명으로 치환. 나머지 `<!-- 채울 것 -->`은 사람이 보강.

## Toolchain 인식 (config.sh/스크립트는 iCE40만)

`--init-ai-infra`와 `--detect-config`는 `db/work`의 툴 프로젝트 파일로 FPGA target을 감지해 다르게 동작한다:

| 감지 | db/scripts·config.sh | build.md |
|------|----------------------|----------|
| **iCE40** (`.prj`, iCEcube2/yosys) | **포함** (다단계 빌드 필요, config.sh만 프로젝트별 수정) | `db/scripts/build.sh` 기반 |
| **Diamond** (`.ldf`) / **Radiant** (`.rdf`) | **생략** (한 줄 빌드) | `diamondc/radiantc "<project>"` **한 줄** (device/top/defines 자동 기입) |
| 미감지 | 생략 | 안내 + 툴파일 추가 후 `--detect-config` 유도 |

→ Diamond/Radiant는 사람용 config.sh를 만들지 않는다. 빌드 방법은 **build.md에 기록**되어 AI가 스크립트 없이 그 한 줄로 빌드한다.

## 다른 install 모드와의 관계
- `--init-ai-infra` : 프로젝트 **AI 인프라**(.ai + db 구조 + refs + 포인터) 스캐폴드 (toolchain 게이팅)
- `--detect-config` : 툴 프로젝트(.ldf/.rdf/.prj) 파싱 → iCE40면 config.sh 생성, Diamond/Radiant면 build.md 한 줄 빌드 기록 + 불필요 스크립트 제거
- `--gen-rd-pdca`   : PDCA 단계 세분화 오버레이 — `bkit/workflow/`
- `--only agents|hooks|bkit-agents` : 에이전트/훅 배포
- 권장 순서: `--init-ai-infra` → `git submodule add <url> db/design` → `--detect-config` → (필요 시) `--gen-rd-pdca` → `--only agents`
