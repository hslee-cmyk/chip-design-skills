---
title: oracle-portability -- design 이력
design: oracle-portability.design.md
date: 2026-10-16
---

# oracle-portability design 이력

> design 본문(`oracle-portability.design.md`)에 넣지 않는 경위를 둔다. 현행 규칙은 본문이 정본이다.

## H1. 버전 경위

| 판 | 커밋 | 내용 |
|---|---|---|
| v0.1 | f8b9a69 | card OP-0 초안. 승인된 계획 v0.4.2(O-1·O-2, D-1~D-9) 기준, base `6093d07`. 독립 검증·사용자 승인 전 |
| v0.2 | (이 커밋) | 사용자 결정 O-3(DV-1 (가) 확정, DV-2 별도 card, X-D1·X-D2 수용)을 반영했다. offset-trim design TR-0T의 G-15 닫힘으로 PC-10을 정의했다(입력 `output_reference`). 사용자 결정 T-39로 DC 풀이 허용오차 선언을 강제(`dc_tolerance_undeclared`)하고, 입력 환산 전파값 `dc_resolution_in_V`(§13.4)를 결과에 낸다. X-D3 해소, X-D4 신설 |

## H2. 작성 경위 (2026-10-16)

- 지시: 오케스트레이터 'oracle-portability card OP-0(design) 작성'. 범위는 계획 OP-0이다(G 항목 중 OP-0 몫, 형식·스키마·PC 벤치·진단 배선·파일 분할·삭제 목록·test 목록·상위 문서 개정 문안). OP-1 측정이 필요한 칸은 '측정 대기'로 두고, 계획과 다른 결정이 필요하면 멈추고 보고한다(S-7).
- 읽은 것(base `6093d07`):
  - 오라클 8개 파일의 함수·상수 목록
  - `oracle_run.run_one`, `simulate` 결과 칸, `offset_mc_measure` 전체(표본 RNG 순서·V_os 식)
  - 입력 스키마 최상위 칸, `oracle_config.json`
  - smoke 입력 `process` 블록(pmos `lod.spice` include)
  - 엔진 선언 `sources` 목록
  - offset-trim v0.5.5 G-14(닫힘, T-35)·G-15(열림)·N6 오라클 확장 목록
- 실행: 코드 실행·ngspice 실행 없음.
- 멈춤 항목: DV-1(엔진 선언에 없는 include 파일, 계획 N3.4 단일 정본과 D-9의 충돌)과 DV-2(상위 문서 개정 미반영, 구현 card 착수 조건)를 본문 §19.2에 올렸다. DV-1은 임시안만 적고 확정하지 않았다.
