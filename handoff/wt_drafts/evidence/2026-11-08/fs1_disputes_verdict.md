verdict: Major 2 -- M-1 계획 수준(S1: DEC-108 (3) 출발 불능 규칙이 library 단계 B 통과 3/7 회로를 막음), M-2 무표지 편차(kvl_partner 짝 범위 = VGS 묶음, 계획·interface는 '같은 칸'). 둘 다 같은 DEC-108 (3) 개정 한 번으로 닫는다. code 결함으로 되돌릴 것 0. 나머지 dispute 결론은 T 다수, I 4건, 기준선 갱신 1건(§0).

# FS-1 (20261107-fs1) code 뒤 dispute 10건·멈춤 2건 독립 판정

- 판정자 = code 작성자·test 작성자가 아닌 독립 agent(읽기·측정·이 보고서 쓰기만; 엔진·test·card 파일 변경 0).
- 대상: code worktree `wt/20261107-fs1-code`(role/code/20261107-fs1, `205ec028`·`7c239bee`, freeze T `58952cb1` 위).
- 근거 문서: card `docs/02-design/specs/20261107-fs1.{spec,interface}.md`, 계획 DEC-108(308행)·DEC-23(224행)·N6.43(2733~2740행), 결정 A-178~A-195.
- 측정 스크립트·결과(판정자 소유, 케이스마다 append): `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/fs1_judge/`
  (`m_realize.py`→`m_realize.jsonl`, `m_d8.py`→`m_d8.jsonl`, `m_s1.py`→`m_s1.jsonl`, `m_net.py`→`net.txt`, `m_s0.py`→`m_s0_*.jsonl`, pytest 출력 `out_*.txt`). 작성자 임시 측정(`chunks/`, `undef.jsonl`)은 증거로 쓰지 않았다.
- 실행 범위(통과로 세지 않은 것 포함)는 §7.

## 0. 판정 요약

| 항목 | 결론 | 담당 |
|---|---|---|
| **M-1 (S1)** | **P** -- DEC-108 (3) '짝 없음 = 출발 불능' 규칙 때문에 단계 B 통과 library 7개 중 3개가 출발 0이다. 코드는 계획대로다. 안 A(비쓰기 단일 멤버 칸 → 기준 폭 슬라이스 키, 후보·정의 조건부)를 조건부로 권고한다. 계획 개정이 먼저이며 '원래 취지와 다름'으로 표지한다. | 오케스트레이터(계획) → card → code |
| **M-2 (판정자 발견)** | code가 `kvl_partner`의 짝 범위를 w_f 칸이 아니라 VGS 묶음으로 넓혔고 표지가 없다. interface대로 되돌리면 folded_cascode 미러 칸 (M3, M4)와 current_reuse 비쓰기 11개가 출발 불능이 된다(측정). 계획을 '칸 무관 + 같은 L'로 고치는 것을 권고하며 M-1과 한 번에 처리한다. | 오케스트레이터(계획) → card → code(L 조건) |
| S2 | 필수 귀결(맞음) + card 공백. 층 0 출발점 변경은 '원래 취지와 다름'으로 표지한다. | card |
| d2-writer-closed-form | T | test 작성자 |
| realized-toy-no-root | I(D-5 입력 고정) + T(D-7). 손 근이 있는 입력은 측정으로 확인했다. | card → test |
| d8-load-gate | I. 대체 입력 측정 통과. | card → test |
| toy-spec-empty-widths | T 22 + I 1(T-7 RETIRED) | test·card |
| eval-calls-seal4 | T + I-minor. 코드(wf ∈ 입력 버전)가 graph 정본에 맞다. | test·card |
| signature-misses | T 16(+ §8 목록 누락) | test·card |
| signature-misses-search | T ≈ 98(+ §8 목록 누락) | test·card |
| test-premises | T 9항목, S1 종속 1, S2 종속(RETIRED) 1, 원인 규명 전 항목은 §6 | 항목별 |
| s0-baseline | 의도 변경(W5·W9)으로 본다. 갱신은 판정자 몫이고 필드 단위 귀속 측정 1회가 조건이다(이번 측정은 메모리 압박으로 시스템이 중단해 미완). | audit |
| m1-pair-sigma | T. 엔진의 쌍 √2가 정의(DEC-23 A_eff, lut 10.4, interface §3.4 단계 4)에 맞고, helper는 단일 σ를 썼다. | test 작성자 |
| core `keywords=`·`split` | A-188의 필수 귀결(범위 위반 아님). card 기록 누락. | card |
| `point_wf`·`wf_cost`·`_symmetric_partner` | graph 정본에 맞음(사본·slot 0). 기록 누락·레이아웃 스냅샷 주의 minor. | card, LA-1 |

## 1. dispute 10건 판정표

| # | dispute | 분류 | 근거(파일:줄·손 계산·측정) | 고칠 방향 | 담당 |
|---|---|---|---|---|---|
| 1 | d2-writer-closed-form | **T** | `tests/sizing/test_block_dc.py:105-106`이 쓰기 소자(M1·M3)까지 노드 동작점 닫힌 식 `_w_closed`를 1e-9로 비교한다. 쓰기 소자 W의 정의는 θ 좌표 `I·L/exp(θ ln IDu)`(DEC-88, interface §4.2 '기존 식')이다. 다이오드 노드 M1 vgs = 0.5999999465(θ 목표 0.6에서 5.35e-8 V 아래, `m_realize.jsonl` D7_alt 탐색 행에서도 같은 값)이고, 손 계산 gm/ID ≈ 15.2 V⁻¹ × 5.35e-8 V = 8.1e-7이 측정 상대 차 8.18e-7과 맞는다. 노드 풀이 허용오차 문제이고 FS-1과는 무관하다. | `test_block_dc.py:105-106`: 1e-9 닫힌 식 비교는 **종속 소자(M2)만** 한다. 쓰기 소자 M1·M3는 test가 가진 θ로 손 식을 세운다: `op.W == op.current * op.L / math.exp(th[("ln_idu", m)])`(엔진 함수 호출 없음; M1은 `mirror_setup` 구성상 w_m1 = 1.2e-6). 비트 일치가 안 되면 rel 1e-12까지 허용한다(부동소수 연산 순서). | test 작성자 |
| 2 | realized-toy-no-root (D-5·D-7) | **I**(D-5 입력이 interface에 고정됨) + **T**(D-7) | 표를 재현했다(`m_realize.jsonl` D5_orig·D7_orig: 둘 다 `NonconvergentError newton_line_search`). 손 계산: r4 toy는 ln IDu = … + λ·VDS(λ = 0.1, `sizing/conftest.py:52`)이고 triode가 없어 out 노드가 흡수할 수 있는 전류비는 exp(±2λ·0.9) = [0.835, 1.197]뿐이다. 근 위치는 out = 0.9 + ln(s₃/s₂)/(2λ)(s = 실현 W′/θ W 배율, 거울 출력은 s₂/s₁). D-5(정합 칸 200): m = (1, 3 \| 2) → s₂/s₁ = 1.5/1.667 = 0.90, s₃ = 2/1.821 = 1.098 → s₃/s₂ = 1.216 > 1.197 → out = 1.88 V로 레일 밖. D-7(요청 M2 (3, 2e-6)): s₂ = 1.5/0.833 = 1.8 → s₃/s₂ = 0.61 < 0.835 → 레일 밖. 그래서 fail-closed가 맞는 거동이다(`fs1_freeze_r2` n-9 같은 계열). interface §4.4 D-5는 입력을 'D-2 평가 스냅샷(정합 칸 200·나머지 100)'으로 **고정**하므로 D-5는 card 값 결함이다. D-7은 요청 행 값을 interface가 '꼴'로만 주므로 test 선택이다. | **손 근이 있는 입력(측정으로 봉인 통과 확인)**: D-5 → 정합 칸 (M1, M2) 키 100·M3 칸 키 **200**(`m_realize.jsonl` D5_alt_m3_200: 탐색 W (1.2e-6, 4.0e-6, 1.821e-6), 손 oracle m = (1, 4 \| 1), 실현 W′ = (1e-6, 4e-6, 2e-6), out = 0.463 V(M2 vds), `realized_sealed: true`, M3 residual 0.0982, M1 −0.1667). 칸 키 200 ≠ 기준 폭 100인 칸이 하나 남아 'w_f = 칸 키 × 격자' 판별력이 유지된다. 대안 'w_m1 = 2e-6, 정합 칸 200'은 out ≈ 1.37 V로 M3 봉인 7 위반(slack −0.121 V)이라 쓸 수 없다(측정 D5_alt_wm1_2u). D-7 → 요청 `(("M2", (2, 2e-6)),)`: W′ = 4e-6 = 기준 실현 m·w_f, `w_key == 200`, 봉인 통과(D7_alt_nf2·D7_alt_on_D5b). 기대 'W′ = 3·2e-6'은 '2·2e-6'으로 바꾼다. 두 test 모두 '실현 점 손 근이 레일 안'을 전제 단언으로 둔다: |ln(s₃/s₂)| ≤ 1.8λ(A-193과 같은 규칙). card §4.4 D-5 입력 문장 정정이 먼저다. | card(D-5 입력) → test 작성자 |
| 3 | d8-load-gate | **I** | interface §4.4 D-8 '그 슬라이스 하나만 다른 L 격자'는 적재 관문 `lut_slice_axes_mismatch`(`lut/lut_set.py` `_build_slice`, FS-1 전부터 있음)가 막는다. 어떤 구현으로도 만들 수 없는 입력이다. interface 스스로 '적재 관문을 통과하지 못하면 멈추고 보고'라 적어 두었다. | D-8 입력을 '축은 같고, 슬라이스 200(nmos)만 동작점 VGS 마디(0.5·0.625 V)의 GM = 0(off 마디, `sizing/conftest.py:159-175` `r4_arrays` off_points 꼴)'으로 바꾼다. 측정(`m_d8.jsonl`): 적재 통과, 정합 칸 키 200 → `SealViolationError` reason `lut_query_failed`(lut_reason `lut_curve_undefined`, w_key 200, devices M1), 대조 키 100 → 봉인 통과. 기대 문언은 '기존 LUT 조회 불능 사유(reason 기록)'로 하고, 'realize_fingers 0·w_key 100 성공 스냅샷 0'은 그대로 둔다. | card → test 작성자 |
| 4 | toy-spec-empty-widths | **T** 22 + **I** 1 | `tests/lut/conftest.py:84` `TOY_SPEC = LutSpec(1e-8, (("nmos", 1.5e-6),), …)`의 슬라이스 폭이 모두 1.5 µm 미만이라 `widths == ()`가 되고, interface §2·DEC-108 (1) '후보 0 = 적재 E-0 정지'대로 거부된다. 코드는 계약대로다. 이 23개 test는 후보 집합을 재는 test가 아니다(곡선·근·허용오차·지문 성질). 다만 `test_lut_set.py:641-645` T-7은 '후보 0 spec이 적재 통과'를 단언해 새 계획 규칙과 정면으로 모순된다. A-193은 반대 방향(MINW > 슬라이스)을 ⚠ 물리 불일치로 기각했으므로 고칠 방향은 MINW ≤ 슬라이스 하나다. | 22개: `TOY_SPEC`의 `min_finger_w_m`을 toy 슬라이스 폭 이하(예: 그 fixture의 가장 좁은 슬라이스 폭)로 둔다. 기대값은 그대로다(후보 집합이 이 test들의 값에 들지 않음 -- 바뀌면 멈추고 보고). T-7: card §8에 'T-7 = 계획 규칙 변경으로 대상 소멸 → `RETIRED_TESTS_fs1.md`'를 적고, 같은 성질('`widths` 밖 슬라이스는 D7 중점 검사 대상 아님')은 후보 1개 이상 + 최소 폭 아래 슬라이스 1개 toy로 대체한다. | test 작성자(22), card(T-7) |
| 5 | eval-calls-seal4 | **T** + **I**(minor) | 코드가 맞다: `wf`는 dc_solve 출력을 바꾸는 입력이므로 입력 버전(= graph reuse 키, 상위 CLAUDE.md 규칙 2)에 들어야 한다. 빠지면 같은 lineage에서 `ComputeBlock.__call__`(`core/compute_block.py:150-152`)이 낡은 스냅샷을 돌려주어 E-2·N-2가 깨진다(graph 정본 위반). `tests/sizing/conftest.py:798-806` `eval_calls`는 `wf`를 키워드로 넘기면서 반환 `calls`의 extras에는 넣지 않는다. 그래서 봉인 4가 다시 잰 버전이 기록 버전과 다르다(test가 블록 호출을 불완전하게 기술). 'calls에서 키워드 입력을 어떻게 적는가'는 interface §4.1이 정하지 않았다(card 공백). | `conftest.py:798-799`: `(dc_solve, (items, kfixed(ctx), kres(ctx), ctx.lut, wf))` -- `wf`를 extras 맨 뒤에 둔다. 호출 `:805`는 `blk(snap, *ex[:-1], wf=ex[-1], …)`(dc_solve만)로 한다. `test_seal_versions.py:14-15` `expected_version`은 그 extras를 그대로 받아 손 식이 맞는다. card §4.1에 한 줄 더한다: '봉인 4·`calls`의 dc_solve extras = (위치 extras…, wf) -- 필수 키워드 값은 extras 맨 뒤, 입력 버전은 그 전체'. | test 작성자, card |
| 6 | signature-misses | **T** 16 (+ I: §8 목록 누락) | interface §4.1 `size_and_seal(ctx, theta, wf, …)` wf 필수 위치 인자, D-4. `sizing/test_dc_solve_values.py:82·:90`(2), `sizing/test_scc_newton.py:538·570·590·703·776·789·806·844·871·901·902`(parametrize 포함 14 case)가 wf 없이 부른다(grep 실측). `test_scc_newton.py`는 spec 분류 표·§8에 없다(card 소비자 목록 누락). | `wf=hand_wf(ctx)` 또는 `fs1_wf.size_and_seal`로 바꾼다. 기대값은 그대로 두되, 그 ctx LUT가 슬라이스 둘 이상이고 종속 소자가 있으면 손 wf 키가 옛 값과 같은지 먼저 전제로 단언한다(아니면 멈춤). card §8 목록에 `test_scc_newton.py`를 더한다. | test 작성자, card(목록) |
| 7 | signature-misses-search | **T** ≈ 98 case/error (+ I: §8 누락) | 항목별: `test_layer0_center.py:185` spy `wrapped`에 wf 없음(5), `test_search_values.py` `StartPoint`·`EvalKey` 칸(2), `test_slsqp_outer.py`(11), `test_seal7_pending.py::test_real_evaluations`(1), `metrics/test_metrics_aux.py`(8 error)·`metrics/test_ss_evaluate.py`(49 error -- `size_and_seal(ctx` 9곳), `test_kernel.py` lambda `parent` 위치 충돌(1) + `test_u7_without_structure…`(`test_kernel.py:340` `evaluate(s, th, CELLS_C)` wf 없음 -- 같은 묶음), `test_residual_probe.py`(4: 가짜 sctx에 `dc.base` 없음 -- `residual_probe`가 `initial_wf(sctx.dc.base)`를 쓰는 것은 spec W19 '첫 시작점 = initial_wf(base)'와 맞음), `convergence/test_converge_point.py`(17: 가짜 `evaluate`에 wf 없음, `FakeSnapshot`에 `wf_start`·`dc_op` 없음 -- `point_wf`는 필드 읽기라 맞음), `metrics/test_block_param_tables_slices.py:193`(삭제 이름 `reachable_slices` import). 모두 interface §4.1·§4.5·spec W17~W19의 새 서명이다. `test_search_values`·`test_slsqp_outer`·`test_seal7_pending`·`test_residual_probe`·`test_metrics_aux`는 분류 표에 없다. | 서명을 맞춘다(`wf` 인자, `StartPoint(…, wf, source)`, `EvalKey(…, wf_fp, …)`). 가짜 sctx·스냅샷에는 `dc.base`(`graph/start: wf_start`)와 `device dc_op` 행을 준다. `test_block_param_tables_slices`는 `widths`로 바꾼다(분류 표 행 있음). 기대값 변경 0. card §8에 누락 파일을 더한다. | test 작성자, card(목록) |
| 8 | test-premises | 항목별 -- §1.1 | §1.1 표 | §1.1 표 | §1.1 표 |
| 9 | s0-baseline | **의도 변경**(기준선 갱신 정당 -- 단 §5 측정 조건) | §5 | §5 | 판정자(기준선 갱신은 audit 몫) |
| 10 | m1-pair-sigma | **T** (M-1 (b))·**T** (M-2 후반) | 정의 대조: DVGS 열 = 변수 하나의 1σ 섭동을 **소자 하나**에 준 곡선(`lut/mismatch_set.py:7`, `lut/mismatch_sigma.py:1-9` '소자 하나의 게이트 환산 σ', '쌍의 σ(ΔVGS)는 √2·σ_VGS -- 읽는 쪽이 계산'). 그래서 `mismatch_sigma_vgs` = **단일 소자 σ**다. 물리: 독립 두 소자의 ΔVGS 분산 = 2σ²이므로 쌍 σ = √2·σ_단일이다(Pelgrom 꼴). 엔진 `iv_matching_l.py:103-106` `slack = σ_share − √2·σ(L)`, `:134` `share = 값·1e-3/√2`는 interface §3.4 단계 4 '쌍 s(L) = √2·σ'와 같다. 반면 `tests/search/fs1_hand_sigma.py:218-230` `s_of`는 단일 σ를 `s_ref`로 쓰고, `test_iv_matching_l.py:220`은 '값 = σ_share·√2/1e-3'으로 단계 5를 따른다. 그 결과 엔진 비교가 √2·σ(L_k) ≤ (σ(L_{k−1}) + σ(L_k))/2가 되어 L_k에서 통과하지 못한다(측정 하한 2e-5 = 폐쇄값). 손 oracle 단위가 interface 문장('s = 쌍')과 √2만큼 어긋난다. 엔진 결함이 아니고 DEC-23 정의와도 맞다. M-2 후반: θ에 `('y', 'OUT')`·`('y', 'vin_p')`가 없어 엔진 호출 전 `check_theta`가 거부한다(입력 오류). | `fs1_hand_sigma.py:218-220` `s_of`의 반환값에 `math.sqrt(2.0)`를 곱한다(쌍 σ). P2·P3 비교는 같은 배율이라 고르는 (k, w_alt)는 바뀌지 않고 σ_share만 √2배가 된다. `test_iv_matching_l.py:220`은 그대로 둔다. (대안: s_of는 단일로 두고 값을 `σ_share·2/1e-3`로 바꿔도 같은 결과지만, interface 단계 4 문언과 맞추려면 앞의 방법이 맞다.) M-2 후반은 θ에 y 성분(그 회로 스키마의 y 키 전부)을 더한다. card 보정은 불필요하다(단계 4가 이미 '쌍 s'를 정의함). 문언 명료화('s_ref·s_alt = 쌍 s')는 LA-1 입력으로 넘긴다. | test 작성자 |

### 1.1 test-premises 항목별

| 항목 | 분류 | 근거 | 고칠 방향 | 담당 |
|---|---|---|---|---|
| 1(a) `test_without_s1v_start_is_none…`(`test_start_intervals.py:164-182`) | **I → 대상 소멸(RETIRED)** | §3 S2: DEC-108상 w_f는 모든 평가의 입력이고 writer는 `start_intervals` 하나(G-1)라 출발 블록을 늘 불러야 한다. 옛 단언 '뷰 없음 → graph/start 없음·상자 중심'은 as-built 동작이고 계획 규칙이 아니다(계획·design grep 0건). | RETIRED_TESTS_fs1.md에 기록한다. 대체: 'S1v 없는 회로에도 `wf_start`가 있고 `initial_wf` ≠ None'(+ 층 0 출발 = 사다리 허용). | card → test 작성자 |
| 1(b) `test_off_judged_path_passes…`(`test_off_judged.py:170-172`) | **T** | toy LUT에 회로 소자의 kind(pmos)가 없다. 출발 블록 `headroom_bound` `edges['pmos']` KeyError. | toy LUT에 회로의 kind를 다 넣는다(또는 nmos만 쓰는 회로). (엔진 쪽 minor: LUT에 없는 kind가 분류되지 않은 KeyError로 나온다 -- FS-1 전부터, LA-1 입력.) | test 작성자 |
| 1(c) convergence 실경로 `common_gate_amplifier` | S2 결정으로 해소 | 출발 블록을 늘 부르면 KeyError가 사라진다(작성자 표 기준 common_gate n_none 0, 판정자 측정 `m_s1.jsonl` 같음). | 없음(S2 채택 시) | -- |
| 2 `test_sb2_second_start_intervals_computes_nothing` | **T** | `run_stage_b`는 `start_intervals`를 부르지 않는다(`search_context.py:190` `_s0_blocks`가 부름). interface S-B2는 '같은 toy 두 번'만 정했다. | 둘째 `build_search_context`(같은 donors·counters)의 `sctx.dc.base`에서 `wf_start`를 읽고, 블록 행 computes 0을 단언한다. | test 작성자 |
| 3 `test_sb5_…` 칸 멤버 순서 | **T** | interface §3.2 '칸 멤버 = position 오름차순'(dc_colour). 이름 순 기대는 S-3과 모순된다. | 기대 키를 그 스냅샷 `dc_colour` 순으로 만든다(손으로 colour를 읽어 정렬). | test 작성자 |
| 4 `circuit_window` toy 4건(`layer0_center` 3, `find_front` 1) | **S1 결정에 종속** | MA·MB 게이트가 레일에 묶여 `fixed_vgs` 종속이고 KVL 짝 쓰기 멤버가 없는 단일 멤버 칸이다 → 현 계획대로 출발 불능. S1 후보안(§2)이 채택되면 기준 폭 키로 출발해 이 test들의 전제가 다시 선다. | S1 결정 뒤: 채택 → 재실행으로 확인(기대값 변경 0). 기각 → toy를 KVL 짝이 있는 꼴로 바꾸거나 기대를 `start_undefined`로(card 승인). | 오케스트레이터(S1) → test 작성자 |
| 5 `test_n2_improving_wf_move_is_accepted` | **T** | 쓰기 소자 W = I·L/exp(θ ln IDu)는 슬라이스 무관이다. 비례 toy LUT(`wb1_toy.py:46` k = W/W_M)에서 두 MOS가 모두 쓰기 소자이면 키를 바꿔도 면적이 비트 같다. N-2 전제가 서지 않는데 interface가 '안 서면 멈춤'이라 했다. | 종속 소자가 있는 회로(거울 출력 등)와 `write_r4_bins_lut(idu_factor={2e-6: f})`(f ≠ 1, 슬라이스별 IDu)를 쓴다. 종속 W = I·L/IDu_slice가 키에 따라 달라져 면적 차가 생긴다. 전제(같은 θ에서 두 키 목적 차 ≥ 분해능 한 칸)는 그대로 손으로 먼저 단언한다. | test 작성자 |
| 6 `test_realize_r6c_…small_m` | **T** (+ LA-1 minor) | interface §6 'dc_finger가 없으면 None'. dc_solve 안 실패의 부분 스냅샷에는 dc_finger가 없다. | 기대를 `small_m is None`으로 한다(이 실패 꼴). LA-1 minor: dc_solve 안 실패(가장 흔한 실현 탈락)에서 small_m이 늘 None이면 Q-FS1 (2) 진단력이 약하다. 정수 m은 `realize_fingers` 뒤·재풀이 앞에 정해지므로 실패 기록 detail에 m을 싣는 안을 LA-1 재점검에서 본다(graph 사본이 아닌 실패 기록 detail -- 계획 판단 필요). | test 작성자, LA-1 |
| 7 `test_ub1_lookup_at_l_across_bins_is_nan` | **T** (+ card 목록) | spec W5·interface §2: `reachable_slices` 삭제, 후보 = `widths`(L 무관 정적 집합, DEC-108 (1) '원래 취지와 다름' -- 옛 상한 철회). 정의 여부는 슬라이스별 `param_row`가 가른다. 슬라이스 200에서 L 2.5 µm가 자기 bin 안이라 값이 정의된다. | 기대 = 슬라이스 100 None·슬라이스 200 값(손: 그 슬라이스 표 값)으로 포락 값을 손으로 낸다. §8 '기대값 변경은 §1~§7 id로 정당화'의 근거 = §2. card §8에 이 test를 적는다. | test 작성자, card(목록) |
| 8 `test_constraints_slices.py` 2 case | **T** | 옛 선택 함수 동률 → 큰 키 200 전제. 지금 키는 평가 입력이다. 이 test의 목적(소자 슬라이스 키 ≠ 기준 키 100에서 ln2 차)을 지키려면 키 200을 **입력으로** 주어야 한다. | 손 wf를 M1 칸 키 200으로 명시해 준다(`hand_wf(..., {"M1": 200})`). 기대값은 그대로다. | test 작성자 |
| 9 `test_previous_run_front_points…`, `test_engine_written_runs_file…` | **T** | 실현 m = 1(W < w_f) → W′ ≈ 2W → triode 없는 toy에서 KCL 근이 없다 → lost. fail-closed가 맞다(R-6/R-8, Q-FS1). 이 test들은 실현이 아니라 front 존재가 전제다. | toy LUT 후보 키를 탐색 W 하한보다 충분히 좁게 둔다(손 조건: 모든 front 소자 x = W_θ/w_f에서 |m/x − 1|이 toy가 흡수할 수 있는 전류비 안 -- r4 λ 0.1이면 실현 배율 비가 [0.835, 1.197] 안, 예 x ≥ 5). 그리고 '실현 점 손 근 레일 안'을 전제로 단언한다(A-193 규칙). PDK 최소 폭 ≤ 슬라이스를 지킨다. | test 작성자 |
| 10 `test_converge.py` 3 case | **T** | `search.conftest.evaluate` 래퍼가 손 wf(가장 좁은 후보)를 쓴다. 층 0 점은 출발 wf로 평가됐다 → 같은 θ의 다른 입력이다. | 재평가 wf = 그 점 스냅샷이 쓴 칸(test가 `graph/start: wf_start` + 칸 첫 멤버 `dc_op.w_key`를 직접 읽는다. 기대 생산이 아니라 입력 재구성). | test 작성자 |
| 11 θ 키 `('L', 'M4')` 5곳 | **T** | FS-1 diff에 θ 스키마·`l_ties` 코드 변경 0(`git diff --stat 58952cb1 HEAD` -- graph/·s1v 파일 없음). 정본 경로(`build_case`, A-188)가 S1v L 동치류로 M4 L을 묶는데 손 θ(`r2_theta` 류)가 따로 둔다. | 손 θ를 그 sctx 스키마 키에서 만든다(L 동치류 주인 키 하나). | test 작성자 |
| 12 원인 규명 전 | §6 | §6 | §6 | §6 |

## 2. 멈춤 S1 -- 착수 조건 10 실측 ≠ 0

### 2.1 재측정(판정자, `m_s1.jsonl` -- 단계 A → B → 탐색 컨텍스트의 `graph/start: wf_start`, code worktree 엔진)

| 회로 | 단계 A·B | 칸 수 | 다멤버 칸 | None 칸 | None 칸 멤버 (why) | 그 소자 `dc_coord` |
|---|---|---|---|---|---|---|
| common_gate_amplifier | ok·ok | 3 | 0 | 0 | -- | -- |
| current_reuse_telescopic_ota | ok·ok | 40 | 10 | **5** | M23a·M14a·M20b·M11b·M40 (no_member_density) | 모두 dependent `cycle_vgs`, partner None |
| folded_cascode | ok·ok | 7 | 6 | 0 | -- | -- |
| nmcnr_amplifier | ok·ok | 10 | 5 | 0 | -- | -- |
| pushpull_follower_buffer | ok·ok | 6 | 0 | **1** | M2 (no_member_density) | dependent `cycle_vgs` |
| sf_pushpull_output_opamp | ok·ok | 12 | 8 | **1** | M21 (no_member_density) | dependent `cycle_vgs` |
| two_stage_ota | ok·ok | 4 | 3 | 0 | -- | -- |
| cnr_ota·erfc_ota·r2r_opamp | stopped | -- | -- | -- | 탐색 컨텍스트 없음 | -- |
| ngcc_3stage_ff·rfc_ota | review_needed | -- | -- | -- | 탐색 컨텍스트 없음 | -- |

작성자 보고(5·1·1)와 같다. 단계 B까지 가는 7개 회로 가운데 3개가 출발하지 못한다. None 칸 7/82개는 모두 단일 멤버 칸이고, 다멤버 None 칸은 0/32이다. 그 소자들의 `start.row`에는 출발 행이 있다(예: M23a i_start 1.2 µA, w_m 338 µm; M2 i_start 6.8e-11 A; M21 i_start 72.5 µA). 즉 I_i는 있고 KVL 짝만 없다.

### 2.2 연결(topology JSON `netlist` 원문만 -- `net.txt`, 태그 미사용)

| 회로 | 소자 | 연결 (D, G, S; bulk 미선언 = kind별 레일 기본 DEC-61) | 같은 gate 소자 | 역할(연결로 본 것) |
|---|---|---|---|---|
| current_reuse_telescopic_ota | M23a (nmos) | D = G = N24b23a, S = N23a24b | M18b (D Vg25, S Vom1 -- source 다름) | 다이오드 연결. M24b(다이오드, S = gnd) 위에 쌓인 바이어스 스택(M22 pmos 전류원이 N24b23a로 공급)이고, 그 게이트가 캐스코드 M18b 게이트를 준다. VGS = V(N24b23a) − V(N23a24b) = 고리 등식으로 정해진다(`dc_coord` = dependent `cycle_vgs`). gate만 공유하므로 KVL 짝 아님. |
| 〃 | M14a (nmos) | D = G = N14a14b, S = N14a_14b | M9b (S Vop1) | 같은 꼴(M14b 위 스택, M13이 공급, M9b 캐스코드 게이트) |
| 〃 | M20b (pmos) | D = G = N20b, S = N20a20b | M18a (S Vg25) | pmos 같은 꼴(M20a 아래 스택, M21이 흡수, M18a 게이트) |
| 〃 | M11b (pmos) | D = G = N11b, S = N11a11b | M9a (S Vg15) | 같은 꼴(M11a·M12·M9a) |
| 〃 | M40 (pmos) | D = G = gnd, S = Voc_des | 없음 | 다이오드 연결. M39(pmos 다이오드, vdd → Voc_des)와 직렬 분압으로 CMFB 기준 Voc_des를 만든다. VGS = −V(Voc_des)가 직렬 KCL로 정해진다(cycle_vgs). |
| pushpull_follower_buffer | M2 (pmos) | D = vss, G = B, S = vout | 없음 | 출력 팔로워. VSG2는 고리 VGS4 + VSG3 = VGS1 + VSG2(원문 Allen L26 p.26-4)로 정해진다. |
| sf_pushpull_output_opamp | M21 (pmos) | D = vss, G = N20, S = vout | 없음 | 같은 꼴(M22 nmos 팔로워와 push-pull, 원문 Allen L26 p.26-6 Fig. 7.1-1). |

일곱 개 모두 정합 묶음 밖 **단일 멤버 칸**의 고리 등식 종속 소자다. 같은 gate·source·bulk·kind인 쓰기 소자가 회로 어디에도 없다(칸 안팎 모두). DEC-108 (3) 문언('KVL 짝 쓰기 멤버가 없거나 I_i가 없으면 그 칸 출발 불능, 대체값 없음')대로 코드는 칸 None을 내고, interface §6 진입 규칙으로 실행 전체가 평가 0이 된다. 즉 **코드는 계획대로 fail-closed이고 결함이 아니다.** 결과로 library 13개 중 단계 B까지 통과하는 7개 가운데 3개(43 %)가 출발하지 못한다. DEC-108 (3)은 '그런 칸 수 n/N은 … 세고, 많으면 계획 개정'을 스스로 적어 두었다. 이것은 **계획 수준(P)** 사안이다.

### 2.3 대안 비교

| 안 | 내용 | 물리 정합 | DEC-108 취지 | fail-closed | graph 정본·상수 | 복잡도·범위 | 판단 |
|---|---|---|---|---|---|---|---|
| A (오케스트레이터 후보) | 쓰기 소자가 아닌 **단일 멤버** 칸에서 출발 W가 정의되지 않으면, 출발 키 = 그 kind 기준 폭 슬라이스 키(`cap_map[kind].w_key`, `w_ref_m`). 단 그 키가 `widths(lut, kind)`에 있고 `defined(name, key)`일 때만, 아니면 출발 불능 그대로. | 맞음(조건부). 출발 단계의 모든 곡선 읽기(쓰기 소자 W·IDu·4단계 slope bin)가 이미 기준 폭 슬라이스다. 그래서 첫 평가가 출발 단계 모형과 **같은 슬라이스**로 그 소자를 본다(θ 출발값과 첫 평가의 소자 모형 일치). 단일 멤버라 정합 결합이 없고, 평가가 그 w_f에서 정확한 W를 내며 이웃 시험이 w_f를 고친다(DEC-108 (4)). 위험: 실제 W < w_ref이면 실현 m = 1 강제(작은 m, Q-FS1) → 이웃 시험이 아래로 옮기거나 실현 탈락으로 드러난다(fail-closed). | 조건부. 'DEC-108 (3) 끝' 규칙('w_f가 정해지기 전 슬라이스 조회 = 기준 폭 슬라이스, 출발 W 추정과 같은 규칙 하나')을 넓힌 것이다. 그러나 '대체값 없음' 문언을 바꾸므로 **원래 취지와 다름**이다. | 맞음. 기준 키가 후보 밖이거나 정의 불능이면 출발 불능. 평가 중 조회 불능이면 그 평가 실패(다른 슬라이스로 바꾸지 않음). | 새 필드·cache 0, writer 그대로(`start_intervals`가 `wf_start`에 씀), 값은 LUT 선언(`w_ref_m`)이라 상수 발명 0. | 작음: `wf_start_value`에 kind별 기준 키 인자와 쓰기 집합(또는 'W 정의 불능 why 구분') 하나, 기록 code 하나(예: `wf_start_reference`, 출력 전용). | **권고(조건부 맞음)** |
| B | 출발 W 대신 기존 필드 `start.row.w_m`(그 소자 자기 gm/ID 출발값으로 낸 폭)을 칸 W로 쓰고 규칙 (i)/(ii) 적용 | 약함. 고리 종속 소자의 gm/ID는 자유 좌표가 아니다. 측정값 w_m = 338 µm(M23a)·8.2 mm(M20b, I = 1.2 µA, L = 0.15 µm)로 물리적으로 과대하고, 결과 키 = 가장 넓은 슬라이스로 몰린다. | 어긋남. v6.39.2가 철회한 '자기 조회' 계열과 같은 근거 부족. | 맞음 | 필드 READS라 사본 0 | 작음 | 기각 ⚠ (근거 없는 값 -- 원칙 11) |
| C | 고리 등식(VGS4 + VSG3 = VGS1 + VSG2 등)을 출발 단계에서 풀어 그 소자 VGS를 내고 W_i = I·L/IDu(VGS_i) | 가장 정확 | 맞음 | 맞음 | ⚠ 종속 VGS의 둘째 생산자(정본 = DC 블록 고리 풀이) -- graph 규칙 1 위반 소지, 정의 축을 나눠도 같은 고리 계산 중복 | 큼(새 출발 단계 계산 -- O-229 4 '새 인프라' 금지) | 기각 ⚠ |
| D | 단일 멤버 칸의 미정 W = 가장 좁은 정의 후보(규칙 (ii)를 W → 0 극한으로) | 맞음(조건부). w_f ≤ W 조건을 가장 보수적으로 지켜 실현 작은 m 위험이 가장 작다. 그러나 출발 단계 모형(기준 폭)과 첫 평가 슬라이스가 달라진다. | 조건부(같은 '대체값' 문제) | 맞음 | 상수 0 | 작음 | 차선 |
| E (현 계획 유지) | 출발 불능 그대로 | 맞음 | 맞음 | 맞음 | -- | 0 | ⚠ library 3/7 회로 실행 불가 → LA-1 측정 범위가 줄어듦(DEC-108 (3) '많으면 개정' 조건 충족) |

**판정**: 안 A가 물리 정합·fail-closed·graph 규칙과 맞는다(조건부). 단 다음 조건이 붙는다.
1. 계획 DEC-108 (3) 개정이 먼저다. 문언: '쓰기 소자가 아닌 단일 멤버 칸의 출발 W가 KVL 짝 부재로 정의되지 않으면, 출발 키 = 기준 폭 슬라이스 키(후보에 있고 출발점 조회가 정의될 때만, 아니면 출발 불능); 원래 취지와 다름 표지'. 원칙 17(계획 먼저)·19(전수 대조: interface §3.2 (iii) 앞 새 갈래, S-7·S-B6 기대 영향 -- S-B6은 다멤버 칸이라 그대로). 위임 A-195 범위에서 오케스트레이터가 채택할 수 있다(기준 약화 아님 -- test 기준이 아닌 출발 규칙 변경).
2. 범위를 **단일 멤버 칸**으로 한정하는 근거를 계획에 적는다. 다멤버 칸에서는 다른 멤버 W를 쓰는 것이 '차용'(DEC-108 (3) 금지)이 되고, 그 칸의 w_f는 정합 멤버 전부를 묶는다. library 실측에서 다멤버 None 칸 = 0/32(§2.1)이라 지금은 효과가 없다. 이 비대칭은 LA-1 재점검 입력이다.
3. 기록: 기준 키로 출발한 칸을 `graph/start: records`에 남긴다(출력 전용 -- 원칙 9 소비자 = LA-1 n/N 보고).
4. A 채택 뒤 §1.1 항목 4(`circuit_window` toy 4건)를 다시 잰다.

### 2.4 관련 code 편차(판정자 발견, dispute에 없음) -- **Major M-2**

- `search/start_intervals.py:265-271`은 `kvl_partner`의 `cell` 인자로 **w_f 칸이 아니라 같은 VGS 묶음**(`DeviceInfo.group`, 쓰기 계획 parallel_vgs 뿌리)을 넘긴다. interface §3.3('`cell` = 칸 멤버 tuple')과 계획 DEC-108 (3)('IDu_p = **같은 칸에서** … 쓰기 멤버')와 다르고, dispute·코드 주석 어디에도 '원래 취지와 다름' 표지가 없다(원칙 24 위반 = 범위 위반 꼴의 Major).
- 물리 평가: KVL 짝의 결정자는 같은 gate·source·bulk·kind(→ 같은 VGS·VSB)와 같은 L이다. 칸 소속은 물리 결정자가 아니다. 그래서 코드 쪽이 더 일반형이다(원칙 6). 대신 **두 쪽 다 '같은 L' 확인이 없다**(DEC-108 (3) '같은 L'·물리 결정자 문언). IDu = I/(W/L)이 1차로 L 무관이라 출발값 오차는 2차지만 정의와 다르다.
- 판정 측정(`partner.jsonl` -- `m_s1.jsonl`의 쓰기 집합·정합 묶음 + topology 연결로 오프라인 계산): 비쓰기 MOS 중 같은 gate·source·bulk·kind 쓰기 소자가 **자기 w_f 칸 밖에만** 있는 것은 current_reuse_telescopic_ota 11개(M8·M13·M17·M22·M60·M61 ↔ M18_bg, M10·M12·M19·M21·M68 ↔ M66)와 folded_cascode 2개(M3·M4 ↔ MP)다. common_gate·nmcnr는 0개다. 즉 **interface/계획 문언대로 칸 안에서만 짝을 찾으면 folded_cascode(2회로 연기 대상)의 미러 칸 (M3, M4)가 출발 불능**이 되고, current_reuse의 None 칸도 늘어난다. 코드 편차가 지금 2회로 연기를 살리고 있으므로 이것은 '되돌릴 결함'이 아니라 '계획이 틀린 자리'다(원칙 8·17).
- 고칠 방향(권고): 코드를 되돌리지 않고 **계획 DEC-108 (3)·interface §3.3을 'KVL 짝 = 같은 gate·source·bulk·kind·L의 쓰기 소자(칸 무관)'로 개정**한다(S1 개정과 한 번에). 코드에는 L 같음 조건을 더한다(code 작성자, 개정 뒤). 계획을 고치지 않는다면 code가 interface대로 칸 tuple을 넘겨야 한다(그러면 None 칸 수를 다시 잰다).

## 3. 멈춤 S2 -- `build_search_context`의 `start_intervals` 호출 조건 삭제

- 판정: **필수 귀결(맞음) + card 공백(I)**. 근거는 셋이다.
  - DEC-108 (1)·(5): w_f 칸은 모든 평가의 입력이다. interface §3.4·G-1: `graph/start: wf_start` writer = `start_intervals` 하나. §4.1: `evaluate`·`size_and_seal`의 wf는 필수다.
  - 그래서 S1v 뷰가 없는 회로도 평가하려면 출발 블록을 불러야 한다. 다른 블록이 `wf_start`를 쓰면 writer가 둘이 되어 graph 규칙 1 위반이다.
  - 옛 조건(`search_context.py` base 190행 `if views is not None`)과 '뷰 없음 → 상자 중심'은 계획·design에 없는 as-built 동작이다(계획 grep 0건). 원칙 8에 따라 보존 근거가 아니다.
- 부작용: 뷰 없는 회로(library: common_gate_amplifier 등, toy: circuit_c 계열)에서 `graph/start: rungs`가 생긴다. 그래서 층 0 첫 점이 상자 중심이 아니라 출발 사다리가 된다(§6 `test_centre_point…` 실측 근거).
  - 이것은 FS-1이 의도하지 않은 **동작 변경**이므로 '원래 취지와 다름'으로 표지해 보고한다.
  - 물리적으로는 오히려 일반형이다. 모든 회로가 같은 출발 규칙을 쓰고, 상자 중심 대신 출발 구간 사다리에서 시작한다(원칙 6).
  - 대안 '뷰 없으면 `wf_start`만 쓰고 rungs 등은 비움'은 한 블록 안에 두 경로를 만들고(복잡도 덧대기), 뷰 없는 회로만 다른 출발 규칙을 쓰게 한다. 근거가 없으므로 권고하지 않는다.
- 옛 test 2건:
  - `test_without_s1v_start_is_none_and_layer0_uses_box_centre` → 대상이 소멸했다(RETIRED). 대체 단언은 'S1v 없는 회로에도 `wf_start`가 있고 `initial_wf` ≠ None'이다(§1.1 1(a)).
  - `test_off_judged_path_passes…` → toy LUT kind 결함이다(T, §1.1 1(b)). 호출 조건 문제가 아니다.
- card 보정: spec·interface §3.4에 '`start_intervals`는 S1v 뷰 유무와 무관하게 늘 부른다(뷰 의존 경계만 비활성)'를 한 줄 더하고 '원래 취지와 다름'(층 0 출발점 변경)으로 표지한다. 층 0 test의 상자 중심 기대(§6)는 이 문장으로 정당화되는 기대 변경이다.

## 4. 범위 밖 추가 판정

| 추가 | 판정 | 근거 |
|---|---|---|
| `core/compute_block.py` `keywords=`·`ComputeBlock.split` | **필수 귀결(범위 위반 아님), card 기록 누락(I-minor)** | A-188이 dc_solve의 `wf`를 **필수 키워드**로 정했다. 옛 `ComputeBlock.__call__(snapshot, *extras, donors, counters)`는 다른 키워드를 받을 수 없어, 블록을 고치지 않고는 A-188을 구현할 수 없다. 키워드 값은 extras 맨 뒤에 붙어 투영·입력 버전에 들어간다. 입력 버전 = 재사용 키이므로 graph reuse 규칙에 맞고, 빠지면 낡은 lineage 재사용이 된다. `keywords=()`인 다른 블록은 extras·버전이 비트 그대로다(`extras += ()`). 새 상태·cache 0. `split` 소비자 = `sizing/kernel_run.py:62`. spec 재작성 범위(W표)에 이 core 변경 행을 추가 기록한다. |
| `search/point_wf.py` `point_wf`(공개) | **맞음(graph 규칙 4 -- 참조·필드 읽기), minor 1건** | 평가 결과 객체에 `WfInput` 사본 칸을 두지 않고(상위 규칙 2 '결과 객체 값 칸 금지'), 칸 구조 = `wf_start` 값 객체 참조 + 칸 키 = 칸 첫 멤버 `dc_op.w_key`(writer dc_solve)를 읽는다. 둘째 생산자가 아니라 READS다. 소비자 5곳(`eps_sweep:34`·`fd_jacobian:109`·`l_bin_search:74`·`realize_front:83`·`converge_point:72`) -- spec W19 '그 시작점·기준점의 wf 그대로(W-a)'를 실제 경로에 잇는 자리다. minor: **레이아웃 뒤 스냅샷**에 쓰면 요청 행 소자의 `w_key`(요청 슬라이스)를 칸 키로 읽는다. 측정 D7_alt: 요청 M2 `w_key` 200, 칸 키 100이다. 지금 호출자는 모두 탐색·실현 스냅샷이다(`converge_point:72`는 루프 밖 `start` 1회). 그 사용 금지를 독스트링에 적거나 거부 검사를 두는 것을 LA-1 입력으로 넘긴다. interface §4.5/§5에 공개 이름으로 기록해야 한다(I-minor). |
| `polish_cells(..., wf_cost=None)` | **맞음(출력 전용), card 기록 누락(I-minor)** | interface §5 perf 칸 `wf_neighbor_evals`·`wf_neighbor_wall_s`를 만들려고 호출자(`eps_sweep.py:126-146`)가 준 합산 dict를 더한다. 재사용·조회에 쓰지 않는 계수라 cache·memo·sctx 슬롯이 아니다. 반환 꼴(interface)을 바꾸지 않는 최소 배선이다. |
| `start_intervals._symmetric_partner` | **맞음(범위 안)** | interface §3.3 괄호 '차동쌍·가지 대칭의 대칭 짝은 출발 블록이 그 묶음 상대를 직접 짝으로 준다'를 구현한 비공개 도우미다. 정준 위치 순 첫 쓰기 멤버라 이름 의존 0이다. |
| `residual_probe` 정지 사유 `"start_undefined"` | minor | 새 정지 사유 문자열이다. fail-closed(평가 0)이고 interface §6 `start_undefined` 판정과 같은 이름이다. 사유 목록 기록을 LA-1 입력으로 넘긴다. |

## 5. s0-baseline 판정

- 실패 키(작성자 보고, 판정자 재실행 안 함): folded_cascode·ngcc_3stage_ff `stage_b.achievability.curves/gain`, folded_cascode `device */start.row`(M3·M4·M7·M8·M9·M10·MP 등).
- 귀속(코드·계획 대조):
  1. `achievability` -- spec W5(`metrics/block_param_tables.py` `reachable_slices` → `widths`). DEC-108 (1)은 후보 = 최소 finger 폭 이상의 도달 슬라이스 전부(옛 상한 w_hi 철회, '원래 취지와 다름' 표지가 계획에 있음)라고 정한다. 포락 표에 드는 슬라이스 집합이 정의상 바뀌므로 curves·gain 값이 바뀌는 것은 의도 변경이다. ngcc는 단계 B가 `review_needed`(탐색 컨텍스트 없음)라 이 보고 키 차만 있고, 이것도 같은 원인이다.
  2. `start.row` -- folded_cascode spec에는 절대 offset 제약이 없고 구조 가드 `offset_excess <= √2`만 있다(`folded_cascode.sizing_spec.json:49`). 그래서 4단계 L 하한은 꺼져 있고, 바뀌는 것은 6단계 가드 slope bin 폭이다(W9: 옛 소자별 선택 폭 → 그 소자 칸 키 × 격자). 가드 상한(부하 gm/ID 상한)과 그 입력 쪽 gm/ID가 바뀌고, 그 하류(gm_id_chosen·L·w_m·sources)가 따라 바뀐다. 이는 계획 DEC-108 (3) 끝('평가 단계 가드 = 실제 w_f bin', 출발 하류 = 칸 키 READS)이 정한 변경이다. folded_cascode는 S1v 뷰가 있어 S2(늘 호출)의 영향은 없다.
  3. G-10(`test_g10_no_recompute_9circuits.py`, 같은 2회로)이 통과한다는 것은 작성자 보고다. 판정자는 재실행하지 않았다.
- 판정: **회귀가 아니라 의도 변경이며, 기준선 갱신은 정당하다.** 단 조건이 붙는다. 이 판정자의 base(`58952cb1` git archive) 대 code 필드 값 비교(`m_s0.py`·`cmp_s0.py`)는 메모리 압박으로 시스템이 중단해 **측정하지 못했다**(지시대로 재시작하지 않음). 그래서 갱신 전에 audit이 다음 하나를 잰다: 'folded_cascode `start.row` 소자별 다른 하위 칸 ⊆ {gm_id_hi, sources 중 `offset_guard` 항, 그 하류 gm_id_chosen·l_*·bin·w_m·ln_idu}'(스크립트는 위 scratch에 있다 -- base 트리 경로와 code 트리 경로를 차례로 넣어 실행하고 `cmp_s0.py`로 비교). 이 조건 밖 칸이 다르면 회귀다. 기준선 갱신은 작성자가 아니라 audit이 커밋하고, 출처 표기(`u17_1b_s0_baseline.json` 해당 회로 항목 = FS-1 코드로 잰 값, 판정 기록 경로)를 남긴다. 단언 대상에서 키를 빼는 안은 기준 약화라 권고하지 않는다.

## 6. test-premises 12 '원인 규명 전' -- 판정자 실행 결과(pytest 하나씩, `out_*.txt`)

| test | 실측 실패 | 분류 | 고칠 방향 |
|---|---|---|---|
| `search/test_kernel.py::test_u7_without_structure_no_block_residual_record` | 기록에 `block_residual`이 있음(`out_k1.txt`) | **T** | `case_c`가 정본 경로 `build_case`(단계 A → B, A-188 test 변경 e6221caa)로 바뀌어 구조(S1v)가 생겼다. 'without structure' 전제가 test 입력과 어긋난다. 구조 없는 컨텍스트를 따로 만들어 쓴다(`test_without_s1v…` 꼴, 단 그 경우도 S2 뒤에는 `wf_start`가 있음). FS-1 code와 무관하다(구조 코드 변경 0). |
| `search/test_kernel.py::test_partial_snapshot_dc_block_failure` | 전제 '실패 평가가 S3에 기록됨' 불성립 | **S1 종속** | toy = `circuit_window`와 같은 꼴(MA·MB 게이트가 레일에 묶임) → 단일 멤버 종속 칸 출발 불능 → 평가 0. S1 안 A 채택 뒤 다시 잰다. |
| `search/test_find_front.py::test_perf_blocks_rows_totals_and_index_bound` | `s1_structure`가 블록 행에 없음 | **T(FS-1 밖)** | 정본 경로 `build_case`에서 단계 A 계수 행이 이 실행의 `dc.counters`에 들지 않는다. FS-1 diff에 pipeline·계수 변경 0이다. test 전제가 A-188 경로 변경으로 깨졌다. 단계 A 블록 행을 어디서 읽을지 정한다(오케스트레이터 -- FS-1 밖, LA-1 입력). |
| `search/test_find_front.py::test_gate_entry_budget_perf_declared_and_block_index_bound` | 546 ≠ 37 × 21 | **I(FS-1 밖 기존 정의 공백)** | 엔진 `s3_index.py:77-79` `index_bound` = 등록된 서로 다른 (블록, 분할) 수(26) × (E+1)이고, test 손 식은 `len(perf.blocks)`(계수 행 37)를 쓴다. 옛 경로에서는 두 수가 같았고, 정본 경로에서 처음 갈라졌다. 어느 정의가 정본인지는 XRUN-F1 card C8 문언이 정한다. FS-1이 바꾼 것은 아니므로 LA-1 재점검 입력으로 넘기고, FS-1 판정에서는 '기존·FS-1 무관'으로 기록한다. |
| `search/test_find_front.py::test_g7_new_process_twice…` | `wf_start`는 있음(MN1·MN2·MP1·MP2 키 100), front 비어 있음 | **T** | §1.1 항목 9와 같은 원인(실현 m = 1 → 레일 안 근 없음 → lost). toy 후보 키를 좁게 하고 '실현 손 근 레일 안'을 전제로 둔다. |
| `search/test_layer0_center.py::test_centre_point_box_centre_and_current_centre` | L 1e-6 ≠ 상자 중심 칸 1.8e-6 | **T(S2·정본 경로 귀결)** | `run_l0`이 정본 경로 `build_case`를 쓴다 → `graph/start: rungs`가 있다 → 층 0이 사다리 칸에서 출발한다(코드 `layer0_center.py` 사다리 우선 = 기존 규칙). 상자 중심 기대는 '출발 구간 없음'일 때의 기대다. 기대를 사다리 첫 칸 손값으로 바꾸거나 RETIRED(§3 card 문장으로 정당화). |
| `search/test_layer0_center.py::test_same_kind_single_term_cone_centre_is_box_centre` | ln I −23.98 ≠ 상자 중심 −17.92 | **T(같음)** | 같다. |
| `search/test_realize_front.py::test_realize_s3_6…` | 손 전제: out 이동 −2.97 V(test 안 계산) | **T** | `wb1_flow.circuit_s36` 두 소자 모두 칸 키 200(w_f 2 µm). M1 W = w_f/1.15로 맞추면 M2 W ≈ M1 W·IDu_p/IDu_n ≈ W1/1.81(I0 비 2, λ 0.1·ΔVDS 1 V) ≈ 0.48·w_f → m = 1, r2 ≈ +108 %로 레일 밖이 된다. M2 칸 키를 100으로 두면 x2 ≈ 0.96, r2 ≈ +4 %다. 손 이동 ≈ ln(1.15/1.04)/(2λ) ≈ +0.5 V → out ≈ 0.9 V로 두 포화 전제 안이다(대략값 -- 전제 단언은 그대로 둔다). |
| `metrics/test_ss_evaluate.py` 5 failed + 45 error | 49건 `size_and_seal() missing … 'wf'`(:108 `build`), 1건 `evals.jsonl` 없음(`_diff_sealed_point`, :856-866) | **T 49** + **S1 종속(추정) 1** | 49건은 서명 맞춤이다(§1 #7과 같은 묶음). `test_it2d_f_icm…`: find_front가 evals 파일을 쓰지 않았다 = 평가 0 → `start_undefined` 진입으로 추정한다(차동쌍 + CMFB 저항 toy). 확인은 S1 결정 뒤 재실행으로 한다(미확인 -- 통과로 세지 않음). |

## 7. 실행 범위·절차 기록

- 판정자가 실행한 것:
  - 측정 스크립트 4개: `m_realize`(6 case), `m_d8`(3), `m_s1`(13회로), `m_partner`(오프라인).
  - pytest 5회, 하나씩, 착수 전 여유 ≥ 5.4 GB(`out_k1`·`out_ff`·`out_l0`·`out_s36`·`out_sse`).
  - `m_s0`(base 대 code)는 시스템 메모리 압박 회수로 중단됐고 재시작하지 않았다.
  - 끝날 때 python 프로세스 0개를 확인했다.
- **돌리지 않은 것(통과로 세지 않음)**: card 전체 test, `tests/structure`, 2회로 연기(`--run-slow -k`), `search/test_canonical_order.py`, G-10, dispute에 걸린 test 대부분의 재실행(작성자 보고를 그대로 쓰지 않고 정의·코드·손 계산으로 판정했다), M-1 실 LUT test.
- 판정자 금지 명령 위반 자백(모두 판정자 scratch 안, 저장소 파일 영향 0):
  1. `cat > /dev/null </dev/null` 1회. 무동작이지만 금지 목록의 cat 꼴이다.
  2. `python -c` 안 대입(`p=…`) 1회. 아무것도 읽거나 쓰지 않은 무동작이다.
  3. `sed -i` 2회. scratch 측정 스크립트 `m_net.py` 키 이름 정정과, 그 전 같은 스크립트 사본 생성(사본은 바로 지움)이다.
  - 재발 방지: scratch 파일도 Edit/Write만 쓴다.

## 8. 점검표(원칙 26 2묶음 -- 판정 범위)

| 항목 | 결과 | 출처 |
|---|---|---|
| graph 단일 정본 | 위반 0을 확인했다. `wf_start` writer 1, `dc_finger` writer dc_solve, `point_wf`는 READS, wf ∈ dc_solve 입력 버전(reuse 키 정합). 새 cache·sctx 슬롯 0. `wf_cost`는 출력 전용 계수다. | 코드 읽기(§4), dispute #5 |
| G-10 블록 재계산 | 안 함(작성자 보고만 있음) | -- |
| 새 필드 소비자 | `wf_start` → `initial_wf`·`point_wf`·가드 slope bin | 코드 읽기 |
| 구조·파일 분할(tests/structure) | 안 함 | -- |
| 회로 이름 0 | 판정 범위 코드(`start_intervals` 5a·`wf_*`)에 이름 의존 0 | 코드 읽기 |
| fail-closed | 출발 불능 → 평가 0(맞음). 실현 근 없음 → lost(맞음). LUT에 없는 kind → 분류 안 된 KeyError(기존, minor) | 측정 m_realize·m_d8 |
| 상수 발명 0 | 안 A는 LUT 선언 `w_ref_m` 참조다. 실현 근 조건은 toy λ에서 유도했다. | §2·§1 #2 |
| 물리 정합 | 쌍 σ = √2·단일(맞음). 실현 근 없음 = toy triode 부재에 따른 fail-closed. KVL 짝 '같은 L' 확인 부재(M-2 동반 정정). | §1 #10, §2.4 |
| 작성자 ≠ 검증자 | 판정자는 code·test·card를 작성하지 않았다. | -- |
| 원래 취지와 다름 | (1) S1 안 A = DEC-108 (3) '대체값 없음' 완화 (2) M-2 = '같은 칸' 철회 (3) S2 = 뷰 없는 회로의 층 0 출발점 변경 | §2·§3 |
