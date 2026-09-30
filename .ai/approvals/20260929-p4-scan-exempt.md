---
id: 20260929-p4-scan-exempt
date: 2026-09-29
target_kind: decision
target: skills/analog-gmid-design/assets/tests/probes/probe_mirror_gain_ranking.py::lut-private
scope: P4 -- probe_dup_scan 스캐너에서 probe_mirror_gain_ranking의 VGS 기준 gm·gds 조회(lut._query) 1곳을 면제(공개 API 부재)
---

## 사용자 원문

> 제안대로 승인 (Recommended)

(질문: P4를 제안 ①~⑤대로 spec card를 개정해 재시도할까 -- ③ "gain_ranking의 VGS 기준 gm·gds 조회는 공개 API가 없다(`gm_gds_ratio(gm_id)`는
VGS를 다시 풀어 같은 문제). 스캐너에 승인 기록 기반 면제를 두고(C13 decision 면제와 같은 방식) 이 1곳만 면제, 공개 API는 Phase 4 백로그")

## 범위 설명

덮는 것: `probe_mirror_gain_ranking.py`에서 규칙 `lut-private` 발견(VGS 기준 gm·gds를 `lut._query(lut._log_GM/_log_GDS, …)`로 읽는 `_q` 경로).
IDu 조회(`id_density_at_vgs` 정본이 있음)는 면제 대상이 아니라 교체한다.
덮지 않는 것: 다른 probe, 다른 규칙, 이 파일의 다른 규칙 발견.

## 재검토

Phase 4에서 LUT에 VGS 기준 gm·gds 공개 조회가 생기면 그 호출로 바꾸고 이 면제를 지운다(백로그).
