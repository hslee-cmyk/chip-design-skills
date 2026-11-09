# 새 원칙(gm/ID 손계산 속도·물리 정합) 감사 결과 요약 (2026-10-19, 원문 보고 재기록)

출처: 독립 감사 agent 보고 2부(대화 기록). 원 메모 사본 `fastcalc_audit_notes.md`. 실행 시간 근거: `wt/_scratch_xrunf1b_audit2/results/measure/base/*.extra.json`(평가 1회 중앙값 13~261 ms), `.ai/verification/nfr4c2/perf_table_base_head_ctrl.json`(LUT memo 퇴출). 블록별 cProfile 기록 없음 -- 비용은 추정. 이후 결정 O-32(엔진 안 크기 고정 순풀이 없음, 정확도는 oracle)·O-33으로 일부 정리됨.

## 속도 쪽 과잉
- S1 block_columns.py:691-736 `_solve_input_window`, :663-688 `_refine_ends` -- SP-2 회로에서 FD 열마다 창 고정점·끝 Newton(평가당 전회로 풀이 최대 ~20회 추정) → O-33 (3).
- S2 :640-660 `_interior_solution` -- y=1/2 실패 시 이분 후보 전회로 풀이(텔레스코픽 40/40 실패, 261 ms/평가, memo 퇴출 8,940).
- S3 :11-16 -- W4 창에 VDSAT 없음 → 비포화 영역까지 y 덮음(기본안: 나중 개선).
- S4 metrics_aux.py:224-239 -- 보고 전용 block_residual·ff_gm_ratio·nqs_ratio를 FD 열마다 → 수락 반복·front로.
- S5 DE-1 커널 끝점 풀이 다수 → O-32·O-33으로 정리.
- S6 FX-1 재조회 비용 미측정(build_search_context 최대 15.5 s) → 증분 재조회, 착수 전 측정.
- S7 LUT memo 퇴출 8/9회로 비 0.

## 물리 정합 쪽 결손
- P1 ls_swing.py:39-50 휴리스틱(F-DE6: 출력 끝 ~0.1 V, ICMR 폭 0.13~0.30 V 차) → DE-1 삭제.
- P2 ls_fields.py:45-55 σ 셀 VGS_max에 봉인점 VDS·VSB(끝에서 KVL 불성립), κ 미측정.
- P3 _refine_ends 미검증 외삽 끝 → fail-closed.
- P4 _refine_ends는 θ 고정 Newton(크기 고정 아님) → 기계 구분(O-32로 엔진은 θ 고정 하나).
- P5 offset_systematic.py:37-50, block_columns.py:564 REL_TARGET -- θ 프레임에서 W가 VDS 차 흡수 → 봉인점 계통 offset 구조적으로 거의 0 → 커널 제외, front 실현 W(O-33 (4)).
- P6 input_window.py:13-14 선형 감도 창 1차 근사, 오차 미측정 → 손계산 인정, oracle 오차 표기.
- P7 seal_vgs_match -- 미러·매칭 W 비 봉인 항목 없음(MOD8 뒤 드러남), 공동분석 후보.

## 엔진 층별 (계획 DEC-45·71·73·98)
- 출발 구간: ST-1 _helpers_curves.py:10·92 tol_vdsat_max(bin 무시) 대 봉인 7 table_at → sat_threshold 정본; ST-2 VSB 0·VDS 중점 → FX-1; ST-3 macro_poles 블록 이득 진성 이득(추정 표기); ST-4 PM 45° 구조 유도(문제 없음).
- 층 0: L0-1 layer0_center.py:289-420 -- DEC-71 (3)~(6) 역산 조립 대신 커널 max-min SLSQP(최소형 D18·U-49) → 손계산 주 계산법 층이 커널 반복(속도 원칙 최대 공백) → O-33 (1); L0-2 find_front.py:44-50 -- 블록 예산 배분자 없음, gain_budget_db 미출력; L0-3 max-min 목적이 봉인 여유뿐.
- 내층·중층: IN-1 authoring/spec_settings.py:38·104-106 -- search_method precision 선언이 소비자 0으로 조용히 기본 경로(fail-closed 위반 의심) → 정지 추가.
- 외층 커널: OU-1 S1·S2, OU-2 S4, OU-3 P1·P2·P5, OU-4 registry 영역 칸, OU-5 S3. 모순 없음 근거: 커널 본체 = θ 고정 손계산 자동화, 봉인 1~9 전 점 판정, ss는 SealedSnapshot MNA만, 실패 분류 fail-closed.
- front 판정: FJ-1 block_widths.py:9-12 -- 실현 W 동작점 재풀이 없음(봉인 3 판정만, fail-closed); FJ-2 DEC-98 oracle 미배선(U17 ②).

## 층 사이 같은 양 재계산
포화 tol(갈림, ST-1), 헤드룸 창(DE-1 뒤 headroom_bound 상한 + 봉인 7만 남아 정당), 블록 이득(출발 추정 허용, 층 0 구현 때 정본 하나), 입력 창(IT-2·DE-1), 곡선 동작점(FX-1).

## 배치 표 요지 (O-32 이전 초안 -- 순풀이 열은 O-32로 oracle 검증으로 바뀜)
동작점·헤드룸: 출발 추정 / 층 0 기둥 / 커널 θ 고정 + 봉인 / front oracle .op. ICMR·고임피던스 출력 스윙: 커널 θ 고정 선형 감도 끝 / front oracle. KVL 고정 출력 스윙·σκ 슬루 전류·CM 의존 바이어스 ICMR: 손계산 표기, 정확도 oracle. 계통 offset: 커널 제외, front 실현 W. mismatch σ: 커널 1차 MNA(DE-Q3 (다)). gain·GBW·PM 등: 커널 MNA. 보고 전용: FD 제외. 전력·면적: θ·LUT 닫힌 식.
