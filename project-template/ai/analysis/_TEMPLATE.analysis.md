# {MODULE} 모듈 분석서

> **작성**: <!-- YYYY-MM-DD -->
> **갱신**: <!-- YYYY-MM-DD (무엇을 반영했는지) -->
> **목적**: <!-- 이 분석서가 다루는 범위 -->
> **참조**: <!-- 관련 plan/design 문서, graphify 리포트 -->

<!--
이 파일은 RTL 수정 전 작성하는 모듈 분석서의 템플릿이다 (`verilog-rtl` skill의 Module Analysis 규칙).
파일명 규칙: `{module}.analysis.md`. 대상·연계 모듈마다 작성하고, 수정 후 갱신한다.
분석서 없이 부분 분석/수정을 시작하지 않는다.
-->

## 1. 개요 / 책임
- 이 모듈의 단일 책임, 상위/하위 모듈과의 관계.

## 2. I/O 신호
| 신호 | 방향 | 폭 | 클럭 도메인 | 용도 |
|------|------|----|-------------|------|
| | | | | |

## 3. FSM 분석 (있으면)
- 상태 enum·전이 조건·리셋 상태·동일 사이클 처리.
- deadlock corner(count==0 등)·off-by-one·pointer wrap 위험.

## 4. 타이밍 / 사이클 관계
- 동일 사이클 처리 로직, latency, sync-read 지연.

## 5. CDC / Reset
- 클럭 도메인 경계·동기화기, 리셋 provenance(동기/비동기), gated clock.

## 6. 의존성 (fan-in / fan-out)
- 참조/피참조 모듈, 공유 신호.

## 7. 합성/리스크 노트
- latch 위험, bit-width truncation, lint 경고, 알려진 이슈.
