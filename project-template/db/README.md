# db/ — 하드웨어 빌드 루트 (모든 프로젝트 공통 구조)

칩/FPGA 빌드 관련 파일의 공통 디렉토리 구조. **이 구조는 모든 프로젝트에서 동일**하게 유지한다.

| 디렉토리 | 내용 | git |
|----------|------|-----|
| `design/` | **칩 공유 RTL — git submodule 마운트 지점** (`db/design`). 수정 시 submodule commit | submodule |
| `ip/` | IP 코어 (PLL, SERDES 등) | 추적 |
| `scripts/` | **공통 빌드/프로그래밍 스크립트** — `config.sh`만 프로젝트별 수정 (→ `scripts/README.md`) | 추적 |
| `sdc/` | 제약 파일(`.sdc` 타이밍 / `.pcf`·`.pdc` 핀) | 추적 |
| `top/` | FPGA 전용 top wrapper (`<TOP_MODULE>.v`) | 추적 |
| `work/` | **빌드 출력**(iCEcube2/yosys 산출물, 비트스트림 중간물) | 대부분 gitignore |

- 칩 공유 RTL은 `db/design` 아래에 submodule로 들어온다: `git submodule update --init`.
- FPGA 출력 비트스트림(`*.bin`/`*.nvcm`)은 루트 `img/`에 생성된다(`config.sh`의 `OUTPUT_DIR`).
