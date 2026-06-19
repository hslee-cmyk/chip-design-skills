# db/scripts/ — 공통 빌드/프로그래밍 스크립트

**`config.sh` 가 유일한 프로젝트별 설정점**이다. 나머지는 `config.sh`를 `source`하는 공통 머신이라
보통 수정할 필요가 없다 (단일 소스: `chip-design-skills/project-template/db/scripts/`에서 관리).

| 파일 | 역할 | 프로젝트별 수정? |
|------|------|------------------|
| `config.sh` | 디바이스·TOP·DEFINES·소스목록·경로·`BASE_NAME` | **예 — 여기만** |
| `build.sh` | 통합 빌드 래퍼(툴 자동 감지) | 아니오 |
| `build_yosys.sh` | Yosys + nextpnr 오픈소스 빌드 | 아니오 |
| `build_icecube2.sh` | iCEcube2 배치 빌드 | 보통 아니오 |
| `synth_icecube2.tcl` | iCEcube2 SBT TCL (config 미사용 → 상단 `top_module`/`base_name` 확인) | 상단 vars 확인 |
| `program.sh` | SPI Flash / NVCM 프로그래밍 | xcf 템플릿(`img/<BASE_NAME>-*-programmer.xcf`)은 보드별로 GUI 생성 필요 |
| `prepack_swg36.py` | SWG36 패키지 핀 prepack (패키지 전용 예시) | 패키지 다르면 교체 |

## 사용
```bash
bash db/scripts/build.sh                 # 자동 감지(iCEcube2 우선, yosys fallback)
bash db/scripts/build.sh --tool yosys|icecube2
bash db/scripts/build.sh --clean
bash db/scripts/program.sh               # SPI Flash (개발)
bash db/scripts/program.sh --nvcm        # NVCM (비가역 OTP — 양산)
```

## 신규 프로젝트 적용 시 체크
1. `config.sh` — `PROJECT`/`BASE_NAME`/`DEVICE`/`PACKAGE`/`TOP_MODULE`/`DEFINES`/`VERILOG_SRCS`/제약파일 채우기.
2. `synth_icecube2.tcl` — 상단 `top_module`/`base_name` 확인(install 시 `{{PROJECT_NAME}}` 치환됨).
3. `program.sh` — iCEcube2 GUI로 `img/<BASE_NAME>-spi-programmer.xcf` 등 생성(보드별).

> ⚠️ `program.sh`는 실제 터미널에서 실행(일부 환경에서 AI bash tool은 DLL init 실패).
