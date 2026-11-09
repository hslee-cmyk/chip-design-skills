# DC/AC 분리 원칙 감사 결과 요약 (2026-10-19, 원문 보고 재기록)

출처: 독립 감사 agent 보고(대화 기록). 감사 노트 파일은 남지 않아 오케스트레이터가 보고 원문 요지를 여기에 옮겼다. 사용자 결정 O-26의 근거. 엔진 경로는 `skills/analog-gmid-design/gmid_engine/` 기준, master 2026-10-19 기준 줄 번호.

## A. DC 범위를 신호 개념으로 근사 -- 위반 종류 (1)
- A1 `metrics/ls_swing.py:46-49`, 머리말 :9-11 -- VGS 변을 "전류가 바깥 회로로 고정 = source 비레일"로 선택; rail-source CS에 conduction 변 없음.
- A2 `ls_swing.py:47` `m.vgs_v`, `metrics_aux.py:119-121` -- 범위 끝까지 VGS·VDsat를 봉인점 값 고정(VSB·전류 변화 무시).
- A3 `ls_swing.py:12` -- 저항 DC 강하를 "신호 전류에 따라 변함"으로 제외.
- A4 `metrics/ls_fields.py:9-13, 45-58`, `graph/output_direction.py:7-10, 37-40` -- 슬루 최대 전류 β/σ/κ, β = 봉인점 ID 고정 가정.
- A5 `metrics/offset_systematic.py:7, 46-55` -- 계통 offset = DC 출력 오차 ÷ 소신호 A_dm(Newton 1회 근사).

## B. AC 양을 DC 해가 아닌 점에서 계산 -- 위반 종류 (2), DEC-67 '추정/상한' 허용분
- B1 `search/start_intervals.py:22, 276-282`, `_helpers_curves.py:7, 107` -- 출발 곡선을 VDS = (포화 경계 + 예산)/2, VSB = 첫 격자점에서 읽음.
- B2 `search/iv_gain_l.py:10-12, 60, 81` -- 이득 L 하한을 격자 근사·진성 이득 최대 VGS 마디에서.
- B3 `search/macro_poles.py:6-8, 20-22`, `iv_currents.py`, `iv_speed.py:9-10` -- 매크로 모델을 B1 가정점에서, 단일 극점 근사 대체.
- B4 `metrics/block_gain_model.py:12, 21-22`, `block_gain_bound.py` (GB4) -- KVL 미결합 격자 상위집합 위 상한.

## C. 같은 양을 두 경로가 계산 -- 위반 종류 (3)
- C1 ICMR: `ls_swing.py:107-117` 대 `sizing/block_columns.py` input_windows/saturation_window.
- C2 헤드룸 창: `ls_swing._constraints` 대 `metrics/headroom_bound.py` `_edges` :58-72(다른 변 집합).
- C3 소신호 T(0): `metrics/dc_limit.py`(용량 전용 노드 전하 보존) 대 `metrics/_helpers_nodal.py:5-8`(0 V 제외) -- `block_residual.py:8`, `offset_analysis.py:11`.

## D. 구조적 소신호 판단의 DC 쪽 사용(값 영향 없음/잠재)
- `graph/dc_roles.py:11-21` -- DC 역할을 `ac_ground_class` 술어로 유도(용어 혼재).
- `graph/coupling_vars.py:14-20` -- dc 영역 결합 변수를 AC 블록·signal_nets로 정함(U15 소비 시 위험).

## 위반 아님(요지)
봉인 뒤 ss 계통(ss_dev, metrics_ss, MNA, dc_limit, loop_analysis, rout, noise_*), DC 풀이(block_columns, seal_*, current_basis, writer_plan), input_window(DC Jacobian 감도 + 끝점 재풀이), offset_analysis(DC 1차 섭동, C3 제외), 스펙→바이어스 유도(iv_currents, macro_poles 목표, passive_values), headroom_bound·iv_headroom·iv_domain(DC 부등식), headroom-chain R-1′·R-3.

## 측정 근거
`dcswing/` (이 폴더): part_ab.py·part_c.py·part_c_diag.py, out/ab.jsonl·c.jsonl·diag.jsonl -- 13회로 포트 분류, ls_swing 대 전도 MOS 전부 대 DC 끝 풀이(6회로), `_refine_ends` 미검증 외삽 끝 결함.
