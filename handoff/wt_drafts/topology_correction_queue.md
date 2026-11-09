# topology 정정 대기열

사용자 지시 원칙(feedback-batch-topology-corrections): 개별 정정 지시는 즉시 JSON에 반영하지 않고 여기 쌓았다가, "한꺼번에 반영해" 지시 때 전부 반영하고 connectivity 표를 다시 출력한다.

| # | 날짜 | 회로 | 정정 | 근거 | 결정 |
|---|---|---|---|---|---|
| 1 | 2026-10-29 | heldout erfc_ota | M19 bulk vdd → vcn, M20 bulk vdd → vcn, M21 bulk vdd → vcp (bulk = source) | `evidence/2026-10-29/erfc_region.md` -- bulk = vdd면 드레인 접합 누설로 VDS +0.246 V(M19·M20), +0.026 V(M21); 원문 Fig.6은 3단자 기호(근거 없음) | O-174 -- **반영됨** 2026-10-29 master 9caee65d(사용자 "한꺼번에 반영해") |
| 2 | 2026-10-28 | library common_gate | passive_elements에 CL(vout–gnd, 1 pF) 추가 + spec `measurement_load: true` | O-167 위임, LA-1 범위 14와 함께(O-140 D7 시점) | O-167 -- **보류**(2026-10-29 일괄 반영 때 제외: O-167·O-140 D7이 'LA-1 범위 14와 같은 변경'으로 시점 지정, 지금 넣으면 IT-0 common_gate front 2→0) |
| 3 | 2026-10-30 | library r2r_opamp (O-181 이관) | MOS 31개 전부 bulk 넷 미선언 -- bulk 넷 선언 필요(값은 사용자 판독: 원문 Hogervorst 1994 Fig.5·10·11, `assets/library/sources/r2r_opamp__hogervorst_1994/source.pdf` p.3·p.5) | `evidence/2026-10-30/r2r_loop_reading.md` -- 쪽 렌더 해상도로 판독 불가, bulk = 레일이면 Q-KV1 고리 N 풀이가 VSB를 읽음 | **철회 2026-10-30** -- 정정 불필요. 계획 DEC-61(bulk는 선택 필드, 미선언 = nmos 가장 낮은 레일·pmos 가장 높은 레일, 엔진 `gmid_engine/graph/bulk_default.py`)과 사용자 확인("명시적으로 source쪽에 붙일 때를 제외하고 명시하지 않을때는 rail이 기준")으로 미선언은 결함이 아님. 13회로 중 10회로가 미선언. 항목은 DEC-61 미확인으로 잘못 올림 |
