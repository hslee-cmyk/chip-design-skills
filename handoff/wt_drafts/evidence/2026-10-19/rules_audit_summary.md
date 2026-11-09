# 계획 규칙 드리프트 감사 결과 요약 (2026-10-19, 원문 보고 재기록)

출처: 독립 감사 agent 보고(대화 기록, 감사 메모 `scratchpad/drift_audit_rules/findings.md`). 기준판 master b2c72a01, v6.18 머리 43729726. `E/` = `skills/analog-gmid-design/gmid_engine/`, `O/` = `skills/analog-gmid-design/tools/spice_oracle/`. L = v6.18 계획 줄(43729726).

| # | 위치 | 어긋날 여지 | 구현 상태 | 최소 수정 방향 |
|---|---|---|---|---|
| A1 | DE-1 범위 1(L1494), F-DE5, IT-2, O-23 | "DC 끝점 풀이"를 θ 고정 쓰기 계획 풀이(saturation_window·_refine_ends)의 일반화로 적음 -- 전류 재분배(스윙)·고정 W 미러 어긋남(offset)·끝까지 몬 전류(슬루)를 정의대로 못 냄 | E/sizing/block_columns.py:1-40·663-694, input_window.py:8-14; 크기 고정 KCL 풀이기 없음 | O-32로 엔진은 θ 고정 손계산 하나, 정확한 값은 oracle |
| A2 | DEC-65(L264), DE-1 (d) | "레일 끝까지 몬 DC 해에서 그 노드로 흐르는 전류"의 노드 조건 미정의(용량 노드 DC 순전류 0) | E/metrics/ls_fields.py:9-13 잔존 | 노드 k를 동작점 전압에 고정하고 입력을 끝까지 몬 DC 해에서 k로 드는 방향별 전류(O-33 (6)) |
| A3 | 용어집 L90·DEC-67 L266·S2 L403·DE-1 범위 3(L1500) | 슬루율 = DC 끝점 전류 ÷ 용량을 정의로 적음(O-29 (2) 모순) | ls_fields.py:6-8·34-45 c_slew, oracle 슬루 정의 미정 O/oracle_compare.py:85-89 | 정의 .tran dV/dt, I/C는 손계산 표기 |
| A4 | DEC-67, N3.8 L537, DE-1 (a)(b)(d) | 스윙·ICMR·슬루가 차동 입력 전제 -- 단일 입력 회로(common_gate, pushpull_follower_buffer) 정의 없음 | oracle 차동 없으면 ICMR unavailable(O/oracle_swing.py:24-25) | 전달 뷰 여기 방향 입력 포트 훑기 일반형(O-33 (7)) |
| A5 | N3.8 표 L548, O-25 (2) | ICMR 의미 셋(엔진 IT-2 y 고정, oracle servo 출력 고정, O-25 출력 자유) | O/oracle_swing.py:16-19 | O-25 하나, oracle 변경(O-33 (5)) |
| A6 | v6.18 관련 계획 후속 정정 표(L1576-1583) | oracle-portability 행 없음(offset_sys .dc, ICMR) | -- | 행 추가 |
| A7 | L537·DEC-96 (2) swing_out_v | VDS ≥ VDSAT + tol 여유가 정의 안에(oracle 여유 0, O/oracle_swing.py:15-16) | 엔진·oracle 둘 다 | 정의 VDS ≥ VDSAT, tol은 판정 여유 분리(O-33 (8)) |
| A8 | DEC-25(L225), LR6 | 기생 pole 위상 기여 '직접 계산' 정의가 구현(전체 PM, β=1이면 pm_ss_deg와 같은 LoopAnalysis)과 다름 | E/metrics/registry.py:42, loop_analysis.py:7,16, ss_metrics.py:14 | 정의를 구현대로 또는 다른 양이면 다른 정의 |
| A9 | N3.7 L521 compensation: null 'gm_1 ≥ 2π·GBW·C_out' | DEC-92(GBW MNA 판정)와 같은 제약 두 정의 | 미구현(U-12) | 손계산(출발값) 표기 또는 삭제 |
| A10 | DT-1(L1561-1563) | dc_roles만; ac_ground_class를 DC·matching 판정 두 곳 더 읽음 | E/graph/matching_groups.py:82, E/graph/net_model.py:48 | DT-1 범위에 두 소비자 |
| A11 | L1600 J3 '방향별 최대 전류(ls, DEC-65)', L1792 N9.1 6b 'VDsat 유도 규칙(DF-25, LUT (ID, gds, VDS) 곡선)' | 옛 문언, DEC-88(VDSAT 열)과 모순 | 코드 반영 없음 | 두 줄 정정 |
| A12 | DEC-92 (3)(a) 영점 상쇄 R = 1/Σgm 기본 | 손분석 설계식이 θ 대신 고정값 | E/metrics/passive_values.py:38 | θ 변수, 식은 출발값(O-33 (10)) |
| A13 | 상수 | LR3 단채널 경계 0.18·0.25 µm 기본안, dof_rank_sample_count 기본 10(L500·N3.15) | 코드에 없음 | 유도식 또는 삭제 |
| A14 | headroom-chain F-11/SD-1 | 빈 창 가운데 값·근 없으면 작은 끝점 대체 | E/sizing/block_columns.py:376-399 | 백로그 계수(M-H5) 유지 |
| A15 | 경미 | 용어집 L99 노드 어드미턴스 특수형 식, N1.1(b) stage gain = 출력노드 임피던스(FR-2와 다름), N3.2-10 FF 유효 gm 손분석 규칙(보고 metric E/metrics/ff_gm_ratio.py), graph-consumption 출발 자리값 기하평균 | 대부분 여지 | 문언 정리 |

다시 볼 사용자 결정(감사 원문): O-30 (가) 적용 범위(→ O-31·O-32로 정리), IT-2 순서(→ O-33 (3)), ICMR 정의 하나(→ O-33 (5)), DE-Q1 슬루 노드 조건(→ O-33 (6)), 단일 입력 일반형(→ O-33 (7)), DEC-92 R(→ O-33 (10)), spec 출처 확인(→ O-33 (12)).

새 원칙 감사(손계산·층별 방법) 원문 요지: `scratchpad/fastcalc_audit/00_notes.md` -- S1~S7, P1~P7, 층별 ST-1~4·L0-1~3·IN-1·OU-1~5·FJ-1~2, 배치 표. 같은 폴더 사본: `fastcalc_audit_notes.md`.
