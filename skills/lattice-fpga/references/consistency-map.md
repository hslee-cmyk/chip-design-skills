# Consistency Map

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. **수정 후: `../skill-validation-prompt.md` 절차(6-Check)로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | reference 반영 위치 |
|------|--------------|-------------------|
| Tool 선택 (iCEcube2/Radiant/Diamond) | Lattice 툴 선택 테이블 | device-guide > 각 디바이스, constraints-guide > PCF/PDC/LPF |
| iCE40 Ultra 스펙 | 사용 환경 | device-guide > iCE40 Ultra |
| iCE40 UltraPlus 스펙 | 사용 환경 | device-guide > iCE40 |
| MachXO2 스펙 | 사용 환경 | device-guide > MachXO2 |
| LatticeXP2 스펙 | 사용 환경 | device-guide > LatticeXP2 |
| PCF 제약 (iCEcube2) | 워크플로우 #2 | constraints-guide > PCF 섹션, device-guide > iCE40 Ultra PCF |
| PDC 제약 (Radiant) | 워크플로우 #2 | constraints-guide > PDC 섹션, device-guide > iCE40 PDC |
| LPF 제약 (Diamond) | 워크플로우 #2 | constraints-guide > LPF 섹션, device-guide > MachXO2/XP2 LPF |
| IO_TYPE 옵션 | - | constraints-guide > IO_TYPE (Radiant/Diamond + iCE40 SB_IO) |
| iCE40 Hard IP (SB_HFOSC, SB_IO 등) | iCE40 Ultra 하드 IP | device-guide > iCE40 Ultra 하드 IP, constraints-guide > iCE40 IO_STANDARD |
| iCEcube2 TCL 빌드 | 환경 구조 db/work/ | tcl-scripts > iCEcube2 TCL |
| 타이밍 게이트 (2-phase 빌드) | 워크플로우 TIMING GATE | tcl-scripts > 빌드 흐름, 타이밍 게이트 출력 형식 |
| 오픈소스 빌드 (Yosys+nextpnr) | iCE40 Ultra 참고 | tcl-scripts > 오픈소스 빌드 플로우, device-guide > 오픈소스 툴체인 (대안) |
| Reveal 디버깅 | 워크플로우 #5 | reveal-debug > 전체 |
| FPGA vs ASIC 공통 RTL | - | fpga-vs-asic > 전체 |
| 리셋 처리 (GSR vs 명시적) | - | fpga-vs-asic > 리셋 처리 |
| 클럭 게이팅 금지 | - | fpga-vs-asic > 클럭 게이팅 |
| 클럭 모듈 flatten | - | fpga-vs-asic > 합성 시 모듈 Flatten 규칙 |
| 메모리 추론 (BRAM) | - | fpga-vs-asic > 메모리 추론 |
| TCL 프로젝트 생성 | 환경 구조 db/work/ | tcl-scripts > iCEcube2/Radiant/Diamond TCL |
| TCL 빌드 자동화 | - | tcl-scripts > Makefile |
| Git submodule 연계 | 환경 구조 db/design/ | tcl-scripts > RTL submodule |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| RTL 설계 | 워크플로우 #1 | verilog-rtl |
| UVM 검증 (Linux) | 워크플로우 #6 | chip-verification |

## 변경 이력

- 2026-03-05 (10차): 클럭 모듈 flatten 규칙 추가 — fpga-vs-asic(합성 시 모듈 Flatten 규칙), consistency-map(원칙 항목 추가)
- 2026-03-04 (9차): 오픈소스 빌드 정보 동기화 — device-guide(up5k→u4k, swg36→sg48+pre-pack), consistency-map(device-guide 반영 위치 추가)
- 2026-03-04 (8차): Reveal #4→#5 번호 누락 수정 (재검증 FAIL 보완)
- 2026-03-04 (7차): 타이밍 게이트 추가 — 워크플로우 5→6단계+TIMING GATE, tcl-scripts(Claude 실행 규칙, 출력 형식), consistency-map(타이밍 게이트 항목, UVM #5→#6), skill-validation-prompt(6단계 반영)
- 2026-02-27 (6차): iCE40 Ultra / iCEcube2 추가 — SKILL.md, device-guide, constraints-guide(PCF), tcl-scripts(iCEcube2 TCL + 오픈소스), consistency-map 전체 업데이트
- 2026-02-20 (5차): 6-Check 체계 전환 — "5-Check"→"6-Check" 표기 갱신, SKILL.md "Git Submodule"→"Git submodule" 통일
- 2026-02-06 (4차): 5-Check 검증 완료 (5/5 PASS), 변경 사항 없음
- 2026-02-06 (3차): [→§X] 참조 마커 시스템 도입, skill-validation-prompt.md 연동
- 2026-02-06 (2차): 필수규칙 vs 상세내용 모순 점검 — 절차적 가이드 구조로 해당 유형의 모순 없음 확인
- 2026-02-06 (1차): 전체 점검 완료 (SKILL.md ↔ 5개 reference 파일 일관성 확보)
