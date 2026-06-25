<!--
FILL GUIDE — 신규 프로젝트 build.md 작성 시, 이 주석 블록 따른 뒤 삭제
[1] {{PROJECT_NAME}}  : 레포 루트 디렉토리명
[2] {{SUBMODULE_DIR}} : db/design 서브모듈 레포명 (오류 대처 테이블)
[3] 빌드 워크플로우   : 공식 툴 흐름(GUI/CLI) 기술 후 주석 삭제
    (install.py --detect-config 가 Diamond/Radiant 감지 시 한 줄 CLI 자동 기입)
[4] Clock Structure   : 오실레이터/PLL → 클럭 트리 도식 기술 후 주석 삭제
-->
# Build / Clock / Programming — {{PROJECT_NAME}}

## 빌드 워크플로우
<!-- 공식 툴(iCEcube2/Radiant/Diamond) GUI 또는 CLI 흐름. 예시는 venezia build.md 참조. -->

### CLI 빌드 스크립트 (`db/scripts/`, 있으면)
| 파일 | 용도 |
|------|------|
| `config.sh` | 공유 설정(디바이스·소스·경로) |
| `build.sh` | 통합 빌드 래퍼(도구 자동 감지) |
| `program.sh` | SPI Flash / NVCM 프로그래밍 |

```bash
bash db/scripts/build.sh            # 자동 감지
bash db/scripts/build.sh --tool yosys|icecube2
bash db/scripts/build.sh --clean
```

## 오픈소스 툴체인 (대안, iCE40)
```bash
yosys -p "read_verilog -D<DEF> ...; synth_ice40 -top <TOP> -json out.json"
nextpnr-ice40 --up5k --package <PKG> --json out.json --pcf <io.pcf> --asc out.asc
icepack out.asc out.bin && iceprog out.bin
```

## Clock Structure
```
<!-- 오실레이터/PLL → 루트클럭 → 분주/게이팅 클럭 트리. SDC 클럭 도메인과 일치시킬 것. -->
```

## 출력 / 프로그래밍
| 파일 | 용도 |
|------|------|
| `img/*.bin` | SPI Flash (개발 — 재프로그래밍 가능) |
| `img/*.nvcm` | NVCM (**비가역 OTP — 양산용**) |

- ⚠️ NVCM/OTP는 **한 번 쓰면 변경 불가**. 양산 전 SPI Flash로 충분히 검증.
- ⚠️ `program.sh`는 실제 터미널에서 실행(일부 환경에서 AI bash tool은 DLL init 실패).

## 오류 대처
| 증상 | 해결 |
|------|------|
| `File not found: {{SUBMODULE_DIR}}/...` | `git submodule update --init` |
| 툴 not found | PATH/툴 경로 환경변수 설정 |
| P&R timing 실패 | SDC 제약 확인, 목표 주파수 조정 |
