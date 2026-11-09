# B80 -- pushpull_follower_buffer find_front 0점 원인 실측

- 작성: 분석 agent, 2026-10-24. 엔진·계획·design은 고치지 않았다. 엔진 `wt/integ-it12/.../gmid_engine`(integ/it12 HEAD `3179cd78`)을 import해서 실행만 했다. 실행 전후 `git status --porcelain`이 같은 것을 확인했다(`out/integ_status_before.txt` = `after.txt`).
- 진단 장치: 메모리 안 monkeypatch만 썼다. 파일 수정은 없다.
  - `slsqp_outer.scipy_minimize`·`evaluate`·`_rows`, `fd_jacobian.evaluate`를 감싸 SLSQP 반복, 평가, 종료 상태를 기록했다.
  - status 4로 끝난 호출은 마지막 jac 점에서 선형화 QP(c + J·d ≥ 0, bounds)를 linprog로 다시 풀었다. 풀리지 않으면 deletion filter로 비호환 행을 골랐다(IIS 근사).
  - 변형 실험(V1·V2 행 모양, 상자 좁히기)도 같은 방식이고, 진단 전용이다.
- 원자료: `wt/_scratch_b80/`
  - 스크립트: `scripts/trace_front.py`, `path_rout.py`, `handcalc_start.py`, `startinfo.py`, `digest.py`, `libsum.py`, `iis_detail.py`. `probe.py`·`eng_seal.py`는 classb 사본이고 출력 경로만 바꿨다.
  - 결과: `out/trace_<tag>.jsonl`(케이스마다 append), `out/path_grid10.jsonl`, `out/handcalc.jsonl`, `out/startinfo.jsonl`, 시작점 θ `out/start_*.json`.
- heldout 회로는 쓰지 않았다. SPICE는 새로 돌리지 않았다. front 점 rout는 엔진 값만 있다(§7 미확인).

## 0. 결론

1. **1차 원인(실측)**: 층 0이 rout 선언을 쓰지 않는다. 그래서 출발점이 spec에서 10^5배 떨어져 있다(rout 1.05e8 Ω, 목표 1e3 Ω).
   - 계획 DEC-71 (3)과 design 41 §5.1 E10이 정한 '버퍼 블록 국소 AC 제약(Z_out ≤ `rout_ss_ohm`)'이 as-built에 없다.
   - 출발 전류는 스펙에서 오지 않는다. `start_intervals`의 자리값(W = W_min 전류) 0.15 nA다.
   - 결정 실험(§3): E10 규칙(출력 follower 공통 배율 하나로 Z_out = 1 kΩ, 면적 선언 안)을 손으로 적용한 출발점 하나만 `given_starts`로 넣었다. 엔진은 그대로 두었다. 이 조건에서 front 1점이 나왔다(엔진 rout 450 Ω, 전력 0.12 mW).
2. **증폭 원인(실측)**: rout 제약 행이 spec에서 먼 곳에서 평평하다.
   - 행은 c = (1000 − R)/s이고 s(분해능) ∝ R이다. 그래서 R ≫ 1 kΩ이면 c → −1/ρ 상수가 된다(ρ = s/R ≈ 0.23~0.36).
   - layer0→spec 직선 경로 21점이 모두 봉인되었다. 이 경로에서 R이 2e5배 줄어드는 동안 c는 −2.9 → −3.7로 오히려 나빠졌다. R ≤ ~1.7 kΩ에 와서야 c가 오른다.
   - SLSQP는 선형화한 QP에서 이 행 하나도 상자 안에서 만족시킬 수 없다(IIS = rout 행 단독). 그래서 status 4 '제약 비호환'으로 끝난다.
   - 두 끝점이 모두 실패하면 ε 스윕이 돌지 않는다(`eps_sweep.py:90`). 그래서 front가 0점이다.
3. **원인이 아님(실측)**:
   - eval 예산: 2000이어도 244회만 쓰고 slsqp_4로 끝났다. 유도 예산 21,543에서도 같다.
   - θ 전류 상자 26자릿수: ±2.3 ln·±14 ln으로 좁혀도 front 0이다.
   - 행 모양만 고치는 것: V1·V2 둘 다 layer0 출발에서 front 0이다(그래도 필요조건 후보로 남는다).
4. **일반성(실측)**: library 9회로 중 front가 생긴 회로는 common_gate_amplifier 하나다(2점). 이 회로만 layer0 점에서 spec 행 위반이 0이다. 나머지는 다음과 같다.
   - 5회로(pushpull, two_stage_ota, two_stage_ota_sf, folded_cascode, ngcc): layer0 점이 ss 제약(gain·offset·noise·rout)을 어긴다. 두 끝점이 slsqp_4로 끝나고, IIS는 ss 행 하나다. 같은 증상이다.
   - 나머지 3회로: 층 0 실패나 예산·시간 소진으로 끝났다(별개 결함, B81).
   - 따라서 '층 0이 ss 제약을 보지 않음 → 외층 SLSQP가 ss 비실현 출발점에서 회복하지 못함'은 **일반 결함**이다. rout 행이 평평한 것은 pushpull·rout 고유의 증폭 요인이다.
5. **IT-0 중복**: IT-0 기준선(`.ai/verification/20261021-it0-baseline.json`, 2026-10-21)이 같은 사실을 이미 기록했다(M-I3 n_front: pushpull 0, library 8회로 중 common_gate 1 외 전부 0). 다만 원인 분석이나 결함 등록은 없었다.
   - IT-0의 `FE/front_empty_circuits = 0`은 '재필터 뒤 비는 front'만 센 값이다(`front_was_empty_before`는 따로 기록). 그래서 front 0점 회로를 결함으로 세지 않았다.
   - 계획에는 DEC-71 상태 칸 '미구현(as-built는 최소형 max-min 시작점 하나 -- card LA-1 F-LA1)'으로 gap이 이미 적혀 있다.
6. **권고**: (가) card LA-1 범위 그대로 버퍼 블록 rout 국소 제약(E10)을 포함한 층 0을 구현한다. 계획 변경은 없다. §6에 비교표가 있다.
   - 별도 보고 1: design 41 §5.1(861행) "버퍼만: 층 0을 rout 모드로 돌린다(**as-built와 같다**)"는 integ/it12 as-built와 다르다. **design↔as-built gap**이다.
   - 별도 보고 2: 지금 as-built는 front 0점을 판정 분류 없이 내보낸다. '성능 판정 보류'나 '층 0 무동작' 같은 분류가 없다(§5 (c)). WP-01 위반 소지가 있다.

## 1. find_front가 spec 점에 닿지 못하는 이유 (항목 1)

### 1.1 흐름과 정지 위치 (코드)

- `find_front.py:68-70`: `layer0_start` → `start_points` → `sweep_front`.
- `eps_sweep.py:73-81`: 시작점마다 끝점 두 개를 푼다. `solve_eps(minimize = power, area, eps = None)`이고, `best is None`이면 `failed`에 넣는다.
- `eps_sweep.py:90`: `if e_p is not None and e_a is not None:`일 때만 ε 격자를 돈다. 두 끝점이 모두 실패하면 ε 점 0개이고 front 0점이다.
- `slsqp_outer.py:335`: `stop = "converged" if out.success else "slsqp_" + str(out.status)`. scipy SLSQP status 4 = "Inequality constraints incompatible"이다. 선형화 부분문제(LSQ)에 실현 가능한 해가 없다는 뜻이다.
- `slsqp_outer.py:362-365`: `best` = 수락 반복 중 모든 c ≥ 0인 점. 하나도 없으면 None이다.
- `slsqp_outer.py:263-265, 321-361`: 후보 실패(`candidate_failure`)가 나면 상자 반경을 2^r로 줄여 재시작한다. 실측에서 첫 두 호출은 첫 스텝이 pmos VGS LUT 축 밖(−0.37 V, −0.14 V)이었다. 그래서 세 번째 호출은 반경 ¼ 상자에서 돌았다.
- `ss_constraints.py:82-86`: `scale = max(res.resolution, model_error)`, `c = (d.value − res.value)/scale`. 분해능은 그 점의 값이다.
- `metrics/resolution.py:13`: rout 분해능 = `rout·Re(∂V0)/V0`이다. 즉 R에 비례한다.

### 1.2 SLSQP 반복 기록 (layer0 출발, eval 2000) -- `out/trace_pp_base.jsonl`

| 호출 | 목적 | 결과 | 마지막 점 음수 행(정규화 c·row_w) | 선형화 QP |
|---|---|---|---|---|
| 1, 2 | power | `candidate_failure`(첫 스텝 pmos VGS −0.37 / −0.14 V, `lut_axis_out_of_range`) | -- | -- |
| 3 | power | status 4, nit 9 | rout −0.884, w_min:M1 −57.4 | **불가**, IIS = {rout 행} 하나 |
| 4 | area | status 4, nit 1 | rout −1.0 | linprog로는 가능. SLSQP만 4를 냈다 |

- 호출 3 IIS 행의 기울기: 전류 열 ≈ 1e-15 / 4e-5, ln_idu 열 ≈ ±7e-3, L 열 ≈ 1e5~1e6 /m이다. L 상자 폭은 4e-9 m다.
- 상자 안 선형 최대 개선량은 0.0036으로, 필요량은 0.884다. 상자를 원래 크기로 되돌려 계산해도 0.104에 그친다(`iis_detail`).
- 호출 4는 linprog로 풀리는데 SLSQP가 4를 냈다. L 변수(미터 단위, ~1e-7)와 ln 변수(~20)가 한 벡터에 섞인 척도 문제로 보인다(**추정**, 따로 가르지 않았다).

### 1.3 경로 표: layer0 → spec 점(pp_grid try 10, 정지 48 µA) ln 좌표 직선 -- `out/path_grid10.jsonl`

| t | 봉인 | 엔진 rout (Ω) | 분해능 s (Ω) | s/R | c_rout |
|---|---|---|---|---|---|
| 0.00 | sealed | 1.05e8 | 3.71e7 | 0.355 | −2.88 |
| 0.25 | sealed | 5.05e6 | 1.52e6 | 0.301 | −3.32 |
| 0.50 | sealed | 2.35e5 | 6.44e4 | 0.274 | −3.63 |
| 0.60 | sealed | 6.80e4 | 1.80e4 | 0.264 | −3.73 |
| 0.75 | sealed | 1.06e4 | 2.69e3 | 0.254 | −3.56 |
| 0.85 | sealed | 3.09e3 | 761 | 0.246 | −2.75 |
| 0.90 | sealed | 1.68e3 | 405 | 0.241 | −1.68 |
| 0.95 | sealed | 915 | 215 | 0.235 | +0.39 |
| 1.00 | sealed | 501 | 115 | 0.229 | +4.35 |

- 경로 위 21점이 모두 봉인되었다. 봉인 가능성은 장애물이 아니다.
- c는 t = 0~0.6에서 단조 감소한다(기울기 부호가 반대다). t ≈ 0.8 전까지 회복하지 못한다. 정의상 c ≈ (1000/R − 1)/ρ → −1/ρ다.
- 엔진 rout 1.05e8 Ω는 classb SPICE 1.07e8 Ω와 맞는다.

### 1.4 후보 가르기 실험 (모두 pushpull, eval 2000)

| 실험 | 출발 | front 점 | 끝점 정지 | 판정 |
|---|---|---|---|---|
| base | layer0 | 0 | 둘 다 slsqp_4 | -- |
| 예산 40 | layer0 | 0 | eval_budget / start_eval_budget | 예산이 작으면 먼저 끝난다 |
| 예산 None(유도 21,543) | layer0 | 0 | 둘 다 slsqp_4(커널 212회) | **예산 무관** |
| 전류 상자 ±2.3 ln | layer0 | 0 | 둘 다 slsqp_4(IIS w_min:M1+M2 / rout+w_min) | **상자 폭 무관** |
| 전류 상자 ±14 ln | layer0 | 0 | 둘 다 slsqp_4 | 무관 |
| + 시작점 t = 0.50 (R 2.3e5) | 경로 위 | 0 | s2 둘 다 slsqp_4 | 출발 거리 |
| + t = 0.75 (R 1.1e4) | 경로 위 | 0 | s2 둘 다 slsqp_4 | 출발 거리 |
| + t = 0.85 (R 3.1e3) | 경로 위 | **1** | s2 power converged | 문턱 R ≲ 3× 목표 |
| + t = 0.90 / 0.95 | 경로 위 | **1 / 1** | -- | -- |
| + spec 점(grid10, 48 µA) | spec 점 | **2** | -- | -- |
| + scaled55(전류만 ×10^5.5, ln_idu 그대로) | 면적 위반 점 | 0 | s2 power 수렴했지만 best 없음 | 면적 선언 위반 출발(c_area < 0) |
| V1 행: c = (T − R)/(ρ·T) | layer0 | 0 | 둘 다 slsqp_4 | 행이 정보를 주지만, 전류를 올리면 면적이 폭주하고 상자 재시작으로 줄어든다 |
| V2 행: c = ln(T/R)/ρ | layer0 | 0 | 둘 다 slsqp_4(IIS = area + rout) | 같음 |
| V1 + 손계산 출발 | §3 출발점 | 1 | -- | -- |
| **손계산 E10 출발(§3)** | §3 출발점 | **1** | s2 정상 | **1차 원인 확인** |

- front가 생긴 실행에서도 front 점은 모두 s2(주어진 출발점)에서 나왔다. s1(layer0)의 두 끝점은 모든 실행에서 실패했다.
- front 점 값(엔진):
  - 손계산 출발: rout 450 Ω, P 0.12 mW, θ I(M2) 45.8 µA
  - t = 0.90: 725 Ω, 0.13 mW
  - t = 0.95: 991 Ω, 0.22 mW
  - grid10: ss 행 c = 1.18 / 0.26

정리:
- 출발점이 spec 행에서 정보가 있는 영역(R ≲ 3 kΩ) 안에 있으면 현행 외층이 front를 낸다.
- 밖에 있으면 rout 행이 평평하고 SLSQP가 4로 끝난다.
- 행 모양만 고쳐도 layer0 출발에서는 front가 생기지 않았다. 면적 결합과 재시작 상자 축소가 다음 장애다.

## 2. 왜 pushpull만 nA인가 (항목 2)

층 0 전류의 출처는 `start_intervals`(설계 41 §6)의 출발 사다리 칸 0이다. `layer0_center.py:126-131` `_box_centre`가 이 칸 0 값을 쓰고, `:198`·`:257-259`가 `current_ref`로 끌어올림을 한다. `start_intervals.py:27`에 따르면 "매크로·미러 전파가 정하지 못한 소자의 전류는 자리값 = 그 점에서 W = W_min 인 전류(`current_ref`)"다(`out/startinfo.jsonl`).

| 회로 | 매크로 전류 | `inactive` 주요 사유 | θ 전류 출처 | layer0 θ 전류 |
|---|---|---|---|---|
| two_stage_ota | 있음(GBW 선언) | -- | 매크로(GBW → gm → I) | 0.90 µA / 24.8 µA |
| pushpull_follower_buffer | **없음** | `speed_ft_6.3 gbw_target_missing`, `current_from_macro stage_current_unavailable` | **자리값 W = W_min 전류** 1.52e-10 / 6.37e-11 A | 0.15~0.36 nA |
| common_gate_amplifier | 없음 | 같음 | 자리값 1.51e-10 A | 0.15 nA |
| folded_cascode | 없음(GBW 미선언) | 같음 | 자리값(일부 소자 µA -- 그 소자 gm/ID 하한과 W_min에서) | 1.0~1.6 µA |

- class-A의 µA~mA는 spec의 GBW·PM에서 매크로 모델이 정한 전류다. nmcnr은 저항 RL이 끼어 전류가 IR 강하에 들어간다(그 회로 θ에 `('current','RL')`이 있다).
- pushpull·common_gate는 GBW 선언이 없다. 그래서 매크로가 꺼지고 W = W_min 자리값이 남는다.
- rout 선언은 `start_intervals`의 어떤 경계에도 들어가지 않는다(`git grep rout` 0건, `search/start_intervals.py`·`iv_*.py`).
- θ 좌표에서는 전류를 일정 배율로 바꿔도 밀도(ln_idu)가 같으면 W만 따라 바뀌고 노드 전압과 봉인 여유는 그대로다(**추정**: 봉인 여유가 전류 스케일과 무관하다는 근거는 classb F5 '전류 ×k 모든 k 봉인' 실측 하나다). 그래서 max-min 단계도 전류를 위로 밀지 못한다.
- 상자 중심(kind 상자 기하 중심)은 모든 회로에서 3~7 nA(nmos)·0.4~0.9 pA(pmos)로 비슷하다. 회로 간 차이를 만드는 것은 상자가 아니라 매크로 전류의 유무다.

## 3. DEC-71 (3) 버퍼 블록 국소 AC 제약 -- 오케스트레이터 추가 항목

### (a) as-built layer0는 DEC-71 presolve가 아니다

- `E/search/layer0_center.py:1-8`: "층 0 최소형 시작점 -- θ 상자 중심에서 출발한 봉인 여유 최대-최소 점 (계획 DEC-71 최소형 = R D18·U-49·PUD DF-10, 오케스트레이터 결정 2026-10-08 'feasibility centering')". 이어서 "블록 gain 예산(GB3·GB4)·LR5 knee·GB5 근사식·슬루 선언은 쓰지 않는다"고 적혀 있다.
- `:26-36`: 목적은 봉인 여유 max-min이고, 경성 제약은 w_min·inversion_floor·current_cone뿐이다. ss 제약과 rout는 없다.
- `E/search/find_front.py:34-38` `_LAYER0_REFINEMENTS_OUT_OF_SCOPE`, `:95-101` note `meaning: feasibility_only`.
- 기둥 유도, 블록 국소 문제, 역산 우선 (4), 국소 AC 제약, 조합 DP는 하나도 없다. 다른 출발점 생성기(feasibility centering)다.
- 계획 DEC-71 상태 칸(계획 270행 끝): "미구현(as-built는 최소형 max-min 시작점 하나 -- card LA-1 F-LA1)". 계획 N6.14 F-LA1(1764행)도 같은 사실을 적었다.

### (b) 버퍼 블록 rout 국소 AC 제약은 구현돼 있지 않다. 이것이 B80의 1차 원인이다

- 엔진 `git grep`(tests 제외): `thevenin`, `테브난`, 'rout 국소' 적중 0이다. `start_intervals`·`layer0_center`에서 `rout` 적중도 0이다.
- 손계산 실험(`scripts/handcalc_start.py`, `out/handcalc.jsonl`):
  - 규칙: design 41 §5.3.3 E10 "한 출력노드의 여러 follower는 공통 배율 하나로 Z_out = `rout_ss_ohm`을 푼다"를 그대로 적용했다.
  - Z_th = 1/(gm1 + gm2), gm = (gm/ID)·I(gmb 제외 -- 손계산 수준). 목표는 spec 선언 `rout_ss_ohm` 1000 Ω와 `area_search_m2` 5e-9 m² 둘뿐이다.
  - 반복: 모든 θ 전류 ×k, k = 1/(1000·Σgm). 면적이 넘으면 θ ln_idu 소자 몫만 Δ 올려 면적 ≤ 선언 − b_A로 둔다(b_A = 정의역 면적 분해능 -- 새 상수 없음).
  - 6회 반복으로 수렴했다. 정지 24.1 µA, Z_th 1012 Ω, 엔진 rout 행 c = +0.63, 면적 3.6e-9 m². 음수 행 0, 봉인이다.
  - 이 점 하나를 `given_starts`로 넣고 엔진은 무수정으로 돌렸다. front **1점**(rout 450 Ω, P 0.12 mW, A 1.97e-10 m²). layer0 s1 쪽 끝점은 여전히 slsqp_4다.
- 판정: 계획이 정한 국소 AC 제약을 층 0이 썼다면 출발점이 rout 정보 영역(§1.3, R ≲ 3 kΩ) 안에 들어온다. 그러면 현행 외층이 front를 낸다. **B80의 1차 원인 = DEC-71 (3) 버퍼 블록 rout 국소 제약 미구현**이다(실측).

### (c) '층 0 무동작'·'성능 판정 보류' 보고 경로는 없다

- 엔진 `git grep`(tests 제외): '층 0 무동작'·`performance_pending`·'성능 판정 보류' 적중 0이다. find_front notes(`find_front.py:71-114`)에도 front가 비었다는 것을 분류하는 verdict가 없다.
- pushpull 출력은 front·pending·unmeasured 모두 0이고, `failed_eps`(stop `slsqp_4`)와 `layer0_minimal`·`feasibility_only` 노트만 남는다.
- 계획상 pushpull은 rout 선언이 있다. 그래서 '무동작'이 아니라 rout 모드로 돌아야 하는 회로다(design 41 §5.1 860-862행).
- common_gate_amplifier·folded_cascode는 gain·rout 제약이 모두 없다. design 41 H2(866-869행)에 따라 '층 0 무동작' 보고 대상인데, 이 보고도 나오지 않는다.
- 판정:
  - 실패 사유(`failed_eps`)는 기록되므로 완전한 무기록은 아니다.
  - 그러나 계획이 정한 분류 보고('층 0 무동작'·'성능 판정 보류')가 없다.
  - front 0점이 결함인지 판정할 신호가 결과에 없다. IT-0도 이것을 결함으로 세지 않았다(§4).
  - **WP-01 위반 소지가 있다(조용한 무동작에 가깝다)**.

### (d) 계획에 이미 기록돼 있는가

- 기록 있음:
  - 계획 DEC-71 상태 칸 '미구현(… card LA-1 F-LA1)'.
  - N6.14 card LA-1 범위 1·8(층 0 손계산 조립 구현, find_front 배선과 '최소형' 정리).
  - LA-0 완료 조건이 '층 0 활성 조건(design 41 §5.1: gain 제약·이득 블록 수·rout 선언)'을 잰다(계획 1816행 부근, `awk` 61행).
  - LA-1 완료 조건 '층 0 무동작 회로(gain·rout 제약 없음, DEC-71 (3) Q5b)'(LA-1 절 70행).
  - design 41 §5.1(860-864행), E10(1416행), P-15(1405행), PQ3·PQ4(1424-1425행).
- 기록 없음:
  - '외층 SLSQP가 ss 비실현 출발점에서 status 4로 front 0'이라는 증상과 rout 행 평평함(분해능 ∝ 값). 계획·`.ai/context.md`(세 사본 grep 0)·backlog(B80 본문 외 0)에 없다.
  - design 41 861행 '(as-built와 같다)'의 부정확.
- 판정:
  - **계획과 as-built의 gap이다. 이미 '미구현'으로 등록되어 있고 card LA-1이 덮는다.** 새 계획 결정은 필요 없다.
  - 다만 design 41 861행 '버퍼만: 층 0을 rout 모드로 돌린다(as-built와 같다)'는 integ/it12 `3179cd78`과 다르다. F-LA6에 따르면 옛 U15 전체판은 master에 없다. **design↔as-built 문장 gap이고 정정 대상**이다.

## 4. 일반성 -- library 9회로 (항목 3, 같은 하네스·eval 2000, `out/trace_lib_*.jsonl`)

| 회로 | front | 층 0 | 층 0 점 음수 행 | 끝점 정지 | 비호환 행(IIS) | 비고 |
|---|---|---|---|---|---|---|
| pushpull_follower_buffer | 0 | sealed | rout | slsqp_4 ×2 | rout | 본 건 |
| two_stage_ota | 0 | sealed | gain, gbw, offset | slsqp_4 ×2 | gain(×2) | 같은 증상 |
| two_stage_ota_sf | 0 | sealed | gain, rout, gbw, offset | slsqp_4 ×2 | gain, offset | 같은 증상 |
| folded_cascode | 0 | sealed | offset, noise | slsqp_4 ×2 | noise, offset | 같은 증상 |
| ngcc_3stage_ff | 0 | sealed | area, gain, gbw, pm, noise | slsqp_4 ×2 | noise(×2) | 같은 증상 |
| nmcnr_amplifier | 0 | 출발점 평가 failed | area, gain, pm, swing, offset, noise | eval_budget / start_eval_budget | -- | 예산 소진(320 s) |
| common_gate_amplifier | **2** | sealed | **없음** | 정상(ε 실패 14) | -- | ss = noise 하나, 층 0에서 이미 만족 |
| sf_pushpull_output_opamp | 0 | `layer0_no_start`(`start_lut_query_failed+probe_eval_budget`) | -- | 시작점 없음 | -- | B81 |
| current_reuse_telescopic_ota | 0 | 출발점 평가 failed | area −5e16 | wall_budget | -- | B81, 823 s |

- 선형 개선량 대 필요량(`iis_detail`, 비L 열·원래 상자 기준 / 필요 |c|):
  - pushpull 0.10 / 0.88
  - two_stage_ota 0.12~0.50 / 0.75~0.80
  - two_stage_ota_sf gain 0.24 / 0.74
  - 줄어든 상자에서는 모든 회로가 1e-3 수준이다.
  - 재시작으로 상자가 0.00~0.01 폭까지 줄어든 호출도 있다(two_stage_ota_sf 14번, folded 15번).
- 결론: **'층 0이 ss 제약을 보지 않는 출발점을 낸다 → 외층 SLSQP가 회복하지 못하고 slsqp_4 → 끝점 둘 다 실패 → ε 스윕 미실행 → front 0'은 library에서 5/9 회로에 같은 꼴로 나타나는 일반 결함이다.**
  - rout 행의 분해능 ∝ 값 평평함은 그 가운데 rout 행(pushpull, two_stage_ota_sf) 고유의 증폭 요인이다.
  - gain(dB) 행은 분해능이 값에 비례하지 않으므로 같은 기제는 아니다(**추정**: dB 행이 먼 곳에서 평평한지는 경로 실험을 하지 않았다).

## 5. IT-0 기준선과 겹치는가 (항목 4)

- IT-0 판정 기록 `wt/integ-it12/.ai/verification/20261021-it0-baseline.json`(e98d0b0f, 2026-10-21) `reproduced_numbers`:
  - M-I3 n_front(AB·SIM): pushpull 0, two_stage_ota 0, two_stage_ota_sf 0, folded 0, nmcnr 0, sf_pushpull 0, current_reuse 0, common_gate 1.
  - **같은 사실이 기준선 수치로 이미 있다.**
- 같은 기록의 `FE/library8/front_empty_circuits = 0`은 `measure_it0.py:540` 정의상 `empty = bool(fr.front) and refilter == 0`, 즉 '있던 front가 재필터로 빈 경우'만 센다. front가 처음부터 0인 경우는 `front_was_empty_before: true`로 따로 남겼고 결함으로 세지 않았다.
- 원인 분석, slsqp_4, rout 행 기록은 IT-0 기록에 없다(`slsqp_4` 적중 0).
- 그 밖:
  - `.ai/verification/xrunf1a.json`에 "front·pending·unmeasured·층 0 결과 9회로 변화 0"과 two_stage_ota_sf `EP:s1 stop eval_budget→slsqp_4` 기록이 있다. 변화 판정용이고 원인 분석은 아니다.
  - backlog `wt/_drafts/backlog_additions.md:155` B80 본문 = classb 보고 그대로다.
  - `.ai/context.md`(세 사본) 적중 0.
- 판정: **사실(front 0)은 IT-0·xrunf1a와 겹친다. 원인과 일반성 분석은 새것이다.** B80은 'pushpull 단독' 항목이 아니라 '층 0 최소형에서 library front 0(7/9)' 항목으로 넓히는 것이 맞다.

## 6. 수정 방향 대안 비교 (항목 5)

| 칸 | (가) card LA-1 층 0 구현(버퍼 블록 E10 rout 모드 포함) -- 계획 그대로 | (나) E10 rout 규칙만 `start_intervals`(§6 출발 구간)에 먼저 넣기 | (다) ss 행 정규화를 로그비·목표점 분해능으로(V1/V2) | (라) 외층에 실현 가능성 회복 단계(phase-1: 위반 합 최소화) 추가 | (마) 상자 축소·예산 증액 |
|---|---|---|---|---|---|
| 물리 정합 | 정지전류를 spec(rout)에서 손계산한다. class-AB 정지점(§3 24 µA)이 SPICE 확인 영역(classb F5: 48 µA → 500 Ω)과 같은 꼴이다 | (가)와 같은 식이다. 다만 블록 국소 모델이 아니라 출발 구간 근사다 | 실현 집합이 같다(c ≥ 0 ⇔ R ≤ T). 물리 무관 | 무관 | 무관 |
| 손계산 일치 | 손계산 그 자체(DEC-73 기본 경로) | 손계산 | 해당 없음 | 커널 반복이 늘어 손계산 속도 원칙과 반대 ⚠ | -- |
| design 단순성 | 큼(card LA-1 전체: 기둥·블록 국소·DP·조립). design 41 §5 이미 있음 | 작음(gm 정의 경로 하나 추가) | 작음(`ss_constraints.py` 한 식) | 중간(새 단계·정지 규칙) | 작음 |
| 실측 | 손계산 E10 출발 → front 1(§3 b). gain 회로는 미측정 | 같은 출발점 실측(§3 b) = front 1 | layer0 출발 front 0(V1·V2) -- **단독 무효** | 미측정 | front 0(상자 ±2.3·±14, 예산 None) -- **무효** |
| 일반성 | 9회로 ss 행 전부(gain 모드·rout 모드) | rout 선언 버퍼만(pushpull). 다른 5회로 미해결 | 전 회로 행 모양. 회복력 보조 | 전 회로 | -- |
| 원칙 | graph 정본: 층 0 산출은 `graph/start` 또는 층 0 블록 필드 writer 하나(design 41). 상수 0(목표 = spec 선언). DC/AC: rout는 봉인 DC 점의 국소 AC(테브난)이고 판정은 GB8 전회로 -- 분리 유지. DEC-103: θ 고정 설계점 | ⚠ 원칙 경고: 계획 우선(S-7) — E10의 자리는 design 41 §5(층 0 국소 문제)인데 §6 출발 구간에 두면 자리가 바뀐다. 또 LA-1이 들어오면 같은 '필요 gm'을 두 자리에서 계산하게 되어 graph 단일 정본(둘째 생산자)을 어긴다 — design 41 §5.3.3 E10, CLAUDE.md 규칙 1 | ⚠ 원칙 경고: 계획 우선 — 분해능 정의(S-19, NFR-5 'c = (값 − 목표)/그 점 분해능')를 바꾸므로 계획 개정이 필요하다 — `ss_constraints.py:15-19`, 계획 NFR-5 | ⚠ 원칙 경고: 손계산 속도 우선 — 커널 반복으로 실현점을 찾는 것은 층 0 손계산 기본 경로(DEC-73)와 반대 방향이다 — 사용자 원칙 2026-10-19 | 문제를 가리기만 함 |
| 계획 변경 | 없음(DEC-71 (3)·DEC-73·LA-1 그대로) | 필요(design 41 §6 범위 추가, 계획 LA-1과 순서) | 필요(NFR-5·S-19) | 필요(DEC-73 단계 추가) | -- |

**권고: (가)**.
- 근거:
  - 1차 원인이 '계획에 있으나 미구현인 DEC-71 (3) 버퍼 rout 국소 제약'이라는 것을 실측했다(§3 b).
  - 같은 꼴의 결함이 gain 회로 5개에 있다. 그것은 같은 card의 gain 모드 층 0(DEC-71 (4) 역산 우선)이 덮는 자리다.
  - 새 상수·필드·cache가 없다. 계획 변경도 없다.
- 이 card를 넣을 때 함께 할 것:
  - LA-1 완료 조건에 '층 0 출발에서 front ≥ 1점(rout·gain 선언 회로)'과 '외층 끝점 slsqp_4 비율'을 측정 항목으로 넣을 것을 제안한다. 이것은 기준을 더하는 것이므로 사용자 결정 대상이다.
  - (c)의 '층 0 무동작'·'성능 판정 보류' 보고 경로를 같은 card에서 배선한다. LA-1 범위 7(자동 켬 (i) 층 0 무동작 회로)과 범위 9(실패 분류)에 이미 있다.
  - design 41 861행 '(as-built와 같다)'를 정정한다.
- (다)는 (가) 뒤에도 출발점이 정보 영역 밖일 때를 위한 보조 후보로 남긴다. 단독으로는 무효로 측정됐다.

원칙 점검(이 권고):
- graph 정본: 새 필드·cache 0. 층 0 산출의 writer는 design 41이 정한 자리 하나다.
- 상수: 0. 목표는 `rout_ss_ohm`·`area_search_m2` 선언값, b_A는 정의역 값이다.
- fail-closed: (c) 보고 경로를 같이 배선한다.
- 회로 이름·태그: E10은 '버퍼 블록 출력노드 follower'라는 구조 판정(DEC-63)이고 이름에 기대지 않는다. 손계산 스크립트의 M1·M2 지정은 진단용이다.
- DC/AC: 국소 Z_th는 봉인 DC 점의 AC 양이고, 판정은 전회로 MNA다.
- DEC-103: θ 고정 설계점이다.
- 손계산 속도: 우선한다.
- **원래 취지와 다름**: 없음. 계획 원문 그대로다.

## 7. 미확인

- front 점(§1.4·§3)의 SPICE rout 대조를 하지 않았다. 엔진 값만 있다(classb F5에서 48 µA 점은 SPICE 500 Ω로 확인).
- 호출 4(area 끝점)는 linprog로 실현 가능한데 SLSQP가 status 4를 냈다. 원인으로 L 변수(미터, 1e-7) 척도를 추정하지만 변수 척도 실험은 하지 않았다.
- gain(dB)·offset·noise 행이 spec에서 먼 곳에서 평평한지(경로 실험)는 재지 않았다. 일반성 표의 '같은 증상'은 정지 꼴(slsqp_4, IIS 단일 ss 행)이 같다는 뜻이다. 기제가 같다는 뜻은 아니다.
- 봉인 여유가 전류 스케일과 무관하다는 것(§2)은 pushpull 한 회로의 실측(classb F5)에 기댄 **추정**이다.
- nmcnr·current_reuse·sf_pushpull의 front 0은 각각 예산 소진, 시간 소진, 층 0 실패로 끝났다. 같은 기제인지 가리지 못했다(B81 쪽).
- 손계산 출발에서도 front는 1점이다. (전력, 면적) front의 넓이와 품질은 따지지 않았다.
- `.ai/context.md` grep은 혼합 인코딩 파일이라 적중 0이 완전하다고 보장하지 못한다.
