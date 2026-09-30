---
id: 20260930-p9-e1-correction
date: 2026-09-30
target_kind: diff
target: 93171ace7d84658f31c641e0611427bb920a24f04ea9fee50b15bf3c6177e393
diff_base: d99919c6b7f1d04f74a9f2dd96902fc6eeadcebc
diff_head: 6398a28bb168e5d2ce86e6df7da46a5edeb02bff
diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
scope: design 20-dead-code-dup §10 E1(DoD 판정 기준)·§6.2·§8 P9 행·196행 정정 승인 -- P9 card 20260930-p9-kcl-edges 착수 조건
---

## 사용자 원문

> E1 문구 정정 승인하고 topology.json주석은 보류해.

(앞서 보고: P9 사전 실측 결과 `kcl_series_union`은 KCL 그룹을 돌려주는 다른 질문이고 엔진 운영 호출자가 2곳이라 지우지 않고 본문의 엣지 정의만 정본
`_kcl_and_matching_edges` 호출로 바꾸는 방향이 원칙 기본안이며, 그러려면 승인된 design의 E1 문구 '`kcl_series_union` 참조 0' 정정이 필요하다고 알렸다.
교체 문안은 정정 커밋 6398a28에 그대로 반영했다.)

## 범위 설명

덮는 것: design 20 §10 E1 행 교체(판정 명령 `tests/contracts -k "dup_w_calc or dup_kcl_edges"` + 두 판정 기록 V2, 옛 기준 '두 이름 참조 0' 삭제 -- 기준 변경),
§6.2 대상·방향(정본 후보, `_metric_kcl_residual` 제외), §8 P9 행, 196행 판정 유형 문장 사실 정정.
덮지 않는 것: `topology.json` 주석 정리(사용자 보류), 계획 N6.2 문장, `_kcl_and_matching_edges` 정본 확정(B26, Phase 4).
