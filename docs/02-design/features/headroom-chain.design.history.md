---
title: headroom-chain -- design 이력
design: headroom-chain.design.md
date: 2026-11-03
---

# headroom-chain design 이력

> 본문에 넣지 않는 경위를 둔다. 현행 규칙은 본문이 정본이다.

| 판 | 내용 |
|---|---|
| v0.1 | HC-D 첫 판. O-224·O-225 뒤 HC-1 몫을 쓰다가 design 묶음 ② 검증 M7(HC-S 본문·`device.dc_sat_v` 소유표 행 없음)로 HC-S 몫을 함께 넣었다. 40·41은 다른 agent가 고치는 중이라 §13 인계 줄로 남겼다. 독립 검증·승인 전 |
| v0.1.1 | 위임 A-46: 구조 규칙 A로 파일 자리 분할, `vds_floor` = `derived` 경유, 관문 `off_region_gate` 소비자 행 추가. 옛 원문: ¦ 평가 ¦ HC-S ¦ 봉인 7, `metrics_aux._sat_devices`, J_point(§5.3) ¦ / 자리 `E/lut/sat_threshold.py`(lut 층 -- search·sizing·metrics 모두 아래에서 읽는다). / vds_floor(memo, kind, w_key) -> float                               # 옛 _vds_floor 이동, DERIVED_FUNCTIONS 항목 / - **VDSAT 열 읽기는 이 모듈 한 자리다.** 점 입구는 / `E/sizing/seal_region.py`(EO-1이 만든 파일 -- VDSAT 조회 쪽)·`metrics_aux`·`saturation_rows`의 직접 조회. |
