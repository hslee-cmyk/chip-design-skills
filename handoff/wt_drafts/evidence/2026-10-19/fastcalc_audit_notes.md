# fastcalc audit notes (append per item)
- O-23..O-30 read: user_decisions.md:642-649
- kernel: search/kernel.py:91-168 evaluate -> size_and_seal -> (sealed) ss_evaluate -> constraint rows
- dc_columns per eval: block_columns.py:741 _solve_input_window -> (1) solve y=1/2 + windows (2) k_max loop of full _solve (3) _refine_ends 2 sides x k_max full _solve (4) final _solve

## perf evidence (read only)
- wt/_scratch_xrunf1b_audit2/results/measure/base/*.extra.json perf.eval_time_median_s: cga 27.2ms, telescopic 261.3ms (40/40 dc_columns SealViolation), folded 63.8, nmcnr 132.7, pushpull 13.2, sf_pushpull 12.9 (40/40 fail), two_stage 49.1, two_stage_sf 41.9 ms. eval budget 40 (b_driver --eval-budget 40)
- times (base): build_search_context 0.28~15.5 s (two_stage_ota_sf 15.5, nmcnr 9.1), find_front 0.9~9.5 s, process 19~61 s
- lut_memo_evictions (nfr4c2 perf_table base_t1): telescopic 8940/40 evals, cga 1573, two_stage 972, sf_pushpull 709 (NFR-2 target 0)
- no cProfile record for new engine found (.ai/verification, wt/_scratch_* searched) -> per-block time 미측정
## code facts
- dc_columns per eval (SP-2 input pending): block_columns.py:691-736 _solve_input_window: solve y=1/2, k_max fixed-point loop of full _solve, _refine_ends(663) 2 sides x k_max full _solve, final _solve; failure path _interior_solution(640) dyadic up to k_max full solves
- _refine_ends re-solves in theta-frame (writer ln_idu = theta, dependents re-derived W) -> NOT size-fixed solve
- writer theta-frame: currents fixed by theta, node V from LUT VGS -> hand calc automated (block_columns.py:1-30)
- metrics_aux.py:224-239 block_residual/ff/nqs reports computed every sealed eval incl FD columns
- ls_swing.py:39-50 VGS-eq heuristic; ls_fields.py:45-55 sigma = LUT ID(VGS_max) at sealed VDS,VSB (KVL not met at drive end)
- offset_systematic.py:37-50 error/A_dm; output pinned by target (two_stage OUT=0.9 in dcswing c.jsonl) -> error ~0 by construction
- gate_run once per front (find_front.py:87) = final verification, OK

## O-31 + 정정 반영 (engine layers: 출발구간/층0/커널평가(SLSQP+FD)/정밀경로/front판정 DEC-98)
- verdict: _refine_ends = theta-frame Newton, not size-fixed; DE-1 범위1 conflates with O-30(가) -> split
- offset_sys theta-frame ~0 by construction (OUT pinned 0.9, REL_TARGET block_columns.py:564) -> front only
- IT-2 per-eval refine vs speed -> user decision
- final report delivered to coordinator

## 범위 추가: 층별 검증 (DEC-45/70/71/73/98)
- 층0 계획 = DEC-71 기둥 조립 presolve(역산 우선, 블록 gain bin x (P,A) 비지배, 조합 DP = 예산 배분, gain_budget_db 출력) / 구현 = layer0_center.py 최소형: 상자 중심 + Chebyshev 전류 중심(:182-240 SLSQP 커널 0) + 커널 max-min SLSQP(:289-420, FD) + Halton(:548); find_front.py:44-50 GB3/GB4/budget 범위 밖 명시. gain_budget_db 엔진 출력 없음(grep: authoring override만)
- 내층/중층: 미구현. SEARCH_METHODS ("default","precision") authoring/spec_settings.py:38,104-106 검증만, 소비자 grep 0 -> precision 선언 조용히 기본 경로 (DEC-73 '정밀 경로 선언 = 정지' 위반 의심)
- 출발 구간: start_intervals.py 손계산(곡선·매크로). tol_vdsat = lut.derived tol_vdsat_max (search/_helpers_curves.py:10,92) vs 봉인7 tol_vdsat_table (block_columns.py:238, _helpers_loo table_at) -> 두 정의
- macro_poles.py:5-7 A_i = 입력 소자 진성 이득(캐스코드 미가정), iv_gain_l.py:9-12 VDS 최근접 격자, VSB 격자0, 블록 목표 g_i = G·A_i,max/ΣA_max (출발 전용, 외층 상자 제약 아님 -- search_domain/slsqp_outer에 rung/start 참조 0)
- front 판정: 엔진 안 oracle 호출 없음(DEC-98 미구현), MOD8 W_request = 쓰기 소자 좌표 고정 + 종속 소자 W 요청 -> 봉인3 KCL 잔차 판정만(block_widths.py:9-12), 크기 고정 재풀이 아님
