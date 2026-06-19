# .ai/analysis/ — RTL 모듈 분석서

RTL 수정 전 작성하는 모듈 단위 분석서를 모은다 (`verilog-rtl` skill의 Module Analysis 규칙).

- 파일명: `{module}.analysis.md` (예: `ext_askDecoder.analysis.md`)
- 구조: `_TEMPLATE.analysis.md` 복사 후 작성.
- 규칙: 대상·연계 모듈마다 **먼저 작성**(없이 부분 분석 금지), 수정 후 **갱신**.
- 시작 전 `graphify-out/GRAPH_REPORT.md`로 의존성·신호 연결 먼저 확인(있으면).
