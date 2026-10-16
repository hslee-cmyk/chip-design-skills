# 오라클 C10 폐루프 과도: 조기 종결 계약 개정 (사용자 결정 B, 2026-10-08)

대상: `skills/analog-gmid-design/tools/spice_oracle/README.md` "[신규] C10 PM 안정성 근거" 절차 3~5.
이 문서는 계약 문안이다. 구현 커밋에서 README 절차 3~5 에 같은 문안을 옮기고 이 문서는 근거로 남긴다.
**2026-10-16 문언 일반화(oracle-portability 계획 D-1·N3.7, 사용자 결정 T-33·O-1~O-3)**: 판정 기준(창 판정·조기 종결 규칙)은 오라클 코어가 정의한다. 시뮬레이터 안 창 단위 조기 종결은 선언된 시뮬레이터 어댑터의 능력이다(첫 사례 ngspice). 능력이 없는 어댑터의 실행 방식은 oracle-portability design §8.4를 따른다. 판정 의미는 바뀌지 않는다.

## 0. 문제(실측)
절차 4 의 계획은 시간 척도로 f_lo 만 쓴다(tmax = W = 1/f_lo 급, tstop = t_end + K·W). GHz 로 진동하는(또는 GHz 버스트를 내는
이완 진동) 불안정 회로는 ngspice LTE 걸음 제어가 GHz 주기를 따라가서 tstop(예: 1.6 ms)까지 걸음 수가 끝없이 늘고(>30 분,
메모리 오류) `--timeout-s` 가 없으면 끝나지 않는다. test_rhp_variants_never_pass[rb1e7] 가 걸린다.

## 1. 개정 문안

### (a) 걸음 상한이 f_lo 와 가장 빠른 관련 루프 주파수를 함께 쓴다
* f_crit = **불안정 관련 대역** 안에서 |1+L| 이 최소인 표본의 주파수. 대역 = 스윕 첫 표본부터 **가장 높은 |L|=1 교차(f_hi)를
  지난 첫 표본**까지(|L| >= 1 인 표본과 그 교차 이웃 표본을 포함하는 최소 구간; 닫기 부호 반영 L). 근거: 절차 5 의 판정은
  |L| 이 1 이상인 구간에서만 −1 을 감을 수 있다(Nyquist: |L| < 1 인 꼬리는 −1 을 감지 못함 -- 절차 2 (a) 가 같은 가정). 대역 밖(|L| < 1
  꼬리)에서는 |1+L| → 1 로 argmin 이 스윕 끝(예: 1e10 Hz)에 붙어 의미가 없다. 개루프 RHP 극 주파수는 L 로 셀 수 없어 쓰지 않는다.
  f_hi 는 지금처럼 계획의 다른 항에는 쓰지 않는다(대역 끝으로만). |L| < 1 인 교차가 하나도 없으면(교차 없음) 계획 자체가 없으므로
  (현행 절차 4) 해당 없음; 대역에서 f_crit 이 f_lo 보다 낮게 나오면 tmax 의 min 이 f_lo 항을 고른다(아래 식).
  대역 안에서 |1+L| 최소점은 단일 교차 루프에서 교차 근처(PM 이 작을수록 −1 에 가까움)라 f_crit ~ UGF 부근이 된다.
  기대 f_crit(측정 fixture; 새 규칙 -- 대역 안 argmin, 표본 간격 이내로 UGF 와 일치): lowpm 3.8e5 Hz, β 루프 6.7e5 Hz, classic 1.8 MHz,
  rhp rb1e5 3e7 Hz. CS β=1·twin-T notch 는 대역 상단이 f_hi 라서 f_crit <= f_hi 로 한정되며(옛 규칙은 스윕 상단 1e10 Hz),
  정확한 값은 독립 test 작성자가 fixture 의 .ac 데이터에서 `argmin_{f <= 대역 끝}|1+L|` 로 계산해 기대값으로 고정한다(여기서 숫자를 정하지 않는다).
  걸음 수 상한: tstop·f_hi·n_pp 이하.
* 한 주기당 표본 수 n_pp = ceil(π / arccos(1 − reltol)). 유도: 표본 간격 Δ = 주기/n_pp 일 때 정현파 봉우리를 놓치는 최대 상대
  오차가 1 − cos(π/n_pp) 이므로, 이 오차를 ngspice 가 쓰는 해 정확도 reltol(입력 `testbench.options`, 없으면 기본 1e-3)
  이하로 하는 최소 n_pp (reltol 1e-3 이면 71). 임의 상수 없음.
* tmax = min( 1/(2π f_lo), 1/(f_crit · n_pp) ). td = tr = tf = pw = 1/(2π f_lo), 창 W = 1/f_lo, K, t_end, tstop 은 지금과 같다.
  (f_crit 가 f_lo 근처면 tmax 는 지금보다 줄지 않는다 -- 1/(f_crit n_pp) 가 더 클 때 min 이 1/(2π f_lo) 를 고른다.)
  따라서 안정 회로 중 f_crit·n_pp·2π <= f_lo 가 아닌 것은 걸음이 더 촘촘해져 데이터 표본이 늘 뿐, 창 경계·M_j 정의는 그대로다.

### (b) 창 단위 조기 종결(unstable 확정)
* 폐루프 과도를 창 단위로 실행한다: 조기 종결 능력을 선언한 시뮬레이터 어댑터는 시뮬레이터 안에서 창 경계마다 멈추고 재개해(첫 사례 ngspice: `stop when time >= t_end + j·W` / `resume`) 창 j = 1..K 를 차례로 끝내며,
  창이 끝날 때마다 M_j = max|e| (e = H − H(0), 창 j 안 표본)를 로그에 한 줄(`STABWIN j M_j`) 쓴다. 데이터 파일(`.stab.txt`)은
  멈춘 시각까지 쓴다(`wrdata`).
* 조기 unstable 기준(`early_unstable(M, floor', reltol)`, 기존 창 판정과 같은 M·floor' 정의) -- **엄격한 증가만**:
  창 사이 증가 g(j) := M_j·(1 − reltol) > M_{j−1}·(1 + reltol) + floor'  (측정 분해능을 넘는 증가).
  유도: M_j 는 표본 봉우리라 상대 오차가 최대 1−cos(π/n_pp) <= reltol(절 (a)), 절대 분해능은 floor' 이므로, 두 창의
  측정 불확실 구간이 겹치지 않을 때만 '커졌다'고 인정한다. 새 상수 없음.
  기준: j >= 3 인 첫 창에서 g(j−1) 그리고 g(j) (연속 두 창 증가) 그리고 g↑(M_1, M_j).
  3 은 추세를 세우는 최소 점 수이고 창 한 개의 맥놀이를 거른다.
  **일정 진폭 지속 진동은 g 를 만족하지 못하므로(M_j ≈ M_{j−1}, 증가가 reltol·분해능 이내) 절대 조기 종결하지 않는다.** 그 경우는
  기존 규칙 그대로(K 창 끝까지 또는 시간 상한 -> failed / 기존 판정, 예: test_sustained_oscillation_undetermined_incomplete 의
  현재 결과 불변). 감쇠·완화·비단조 진동도 같은 이유로 영향 없음.
  충족하면 즉시 중단하고 `status = unstable`, `early_stop = {window: j, M: [M_1..M_j], reason}` 를 기록한다. 연장 실행 없음.
* 충족하지 않으면 K 창을 끝까지 돌리고 절차 5 판정을 쓰되, **창 판정을 분해능 인식형으로 바꾼다**(같은 g 족: 증가 g↑(a,b) := b(1−reltol) > a(1+reltol) + floor',
  감소 g↓(a,b) := a(1−reltol) > b(1+reltol) + floor'):
    M_K <= floor'                                  -> stable (불변)
    g↑(M_1, M_K) (M_K 가 M_1 보다 분해능 넘게 큼)    -> unstable
    모든 연속 창에서 g↓(M_{j−1}, M_j)                -> decaying (연장 실행 대상)
    그 밖(분해능 안의 같음 포함)                      -> undetermined
  옛 규칙 'M_K >= M_1 이면 unstable' 의 '=' 근방(분해능 안)은 이제 undetermined 다. 의도(사용자 승인): 일정 진폭 지속 진동은 undetermined
  유지, **분해능으로 확인되는 증가만** unstable. 지속 진동 fixture M = [1.094850, 1.094848, 1.094847, 1.094854, 1.094852, 1.094845]
  (상대 변화 ~5e-6 << reltol)는 undetermined(INCOMPLETE) 불변. 판정이 불변인 기존 fixture: 지속 진동(undetermined), 이완 진동
  rb1e6 M = [1.43, 1.21, 0.68, 1.13, 1.45, 1.30](g↑(M_1, M_K) 아님, g↓ 연쇄 아님 -> undetermined), 명백한 증가(예 rhp rb1e5 와 같은 분해능 넘는
  성장)는 unstable, floor' 도달은 stable, 모든 창 분해능 넘게 감소는 decaying -> 연장. 구현 커밋은 모든 기존 과도 fixture 의 판정이
  개정 전과 같음을 확인해 기록한다(다른 것이 나오면 멈추고 보고).
  조기 기준과의 일관: 조기 기준의 'M_j >= M_1' 은 g↑(M_1, M_j) 로 같은 방식으로 바꾼다.
  연장 실행(decaying 후)의 판정에도 같은 규칙을 쓴다.
* 파이썬은 파일에서 M_j 를 다시 계산해 같은 기준을 검증한다(`transient_decision` 이 잘린 파일을 받아: 마지막 시각이 창 j 끝에
  닿았고 기준을 충족하면 unstable(`early_stop`); 아니고 tstop 에 못 닿았으면 기존대로 `failed`). 시뮬레이터(어댑터)가 중단 시점을 정하고
  판정은 파일이 증명한다.
* 안정 회로 판정 불변 조건: 구현 커밋은 안정 판정이 나는 모든 기존 test 회로·fixture(`stable`/`decaying`->`stable`)에서 창 별 M 이
  위 기준을 한 번도 충족하지 않음을 확인한다(충족하면 기준 설계를 되돌린다). 일정 진폭 지속 진동 fixture 의 판정도 개정 전과 같아야 한다. 불안정은 계속 FAIL.
* 첫 창 안에서 끝나지 않는 GHz 버스트: 창 안 부분 최댓값이 아직 없어 기준을 못 쓴다 -> (c) 가 끊는다.

### (c) 기본 시간 상한(--timeout-s 없어도)
* 설정 `skills/analog-gmid-design/tools/spice_oracle/oracle_config.json` 의 `stability_transient.wall_s_per_window`
  (창 하나를 끝내는 시뮬레이터 실행 시간의 상한 -- 어댑터 보정값, 출처·측정 조건 포함. 첫 사례 ngspice) 를 선언한다. 근거 필드 `justification` 을 같이 둔다: 안정 판정 코퍼스(test
  회로 4종·smoke 회로)의 창당 실측 최댓값 × 여유(실측 분포로 구현 커밋에서 채움 -- 수치는 지금 정하지 않는다).
* 첫 실행 상한 `plan.wall_cap_s` = wall_s_per_window × K (n = 0). 연장 실행 상한 `extension.wall_cap_s` = wall_s_per_window ×
  (K + n), n = `extension_windows`(연장 계획이 정한 추가 창 수; 연장 실행은 K+n 창을 처음부터 다시 돌린다). `transient.wall_cap_s`
  = 첫 실행에 적용한 상한(= plan.wall_cap_s). 실행 시간 상한 = `--timeout-s` 가 있으면 그것(사용자 지정 우선), 없으면 해당 실행의
  wall_cap_s. 동작점 패스에는 적용하지 않는다(기존).
* wall_s_per_window 유도(구현 커밋에서 실측해 config 에 `measured_*`, `safety_factor`, `justification` 로 기록): 창당 비용 c = (실행 시간)/(실행한
  창 수) 를 안정 코퍼스(test 회로 4종·smoke)와 **지속 진동 fixture**(단독 실행 ~107 s/6 창 ≈ 17.8 s/창, 부하 중)에서 잰다.
  wall_s_per_window = safety_factor × max c. safety_factor = 같은 fixture 반복 실행의 max/median 비(부하 변동 실측; 1 미만이면 1) -- 즉
  측정된 변동폭을 그대로 덮는 값이고 임의 배수가 아니다. 반복 횟수·측정치를 config 에 같이 남긴다.
* 끊기면(`TimeoutExpired`) 또는 ngspice 가 치명 오류(메모리·Timestep too small 로 비정상 종료, tstop 미도달)로 끝나면 지금처럼
  `failed`(사유 '과도 시간 초과' / '과도가 tstop 까지 가지 않았다') -> '모름' -> PM 정의 불가 -> PASS 불가. 이 경로는 `unstable` 이
  아니다(진동을 확인한 것이 아니므로).

### (d) 저장 벡터 제한
* 과도 넷리스트 `.control` 은 `save` 로 프로브 벡터만 저장한다: 출력 H 의 식에 쓰는 노드 전압/전류(`hst` 의 피연산자)와 time.
  (`.stab.cir`, `.stab2.cir` 둘 다.) 메모리 오류 완화용이며 데이터 파일 내용은 같다.

## 2. 바뀌는 기대값 목록

| 대상 | 지금 | 개정 후 |
|---|---|---|
| `plan` 새 필드 | -- | `f_crit_hz`(대역 안 argmin), `n_pp`, `reltol`, `wall_cap_s`(첫 실행, n=0), `windows_planned`(= windows) |
| `plan.tmax` | 1/(2π f_lo) | min(1/(2π f_lo), 1/(f_crit·n_pp)); `td/tr/tf/pw/window_s/t_kick_end` 불변; `tstop` = t_end + K·W 불변(계획 필드) |
| `plan.f_hi_hz`, `f_lo_hz`, `kick_V`, `windows`, `floor_V` | 그대로 | 그대로 |
| `transient` 새 필드 | -- | `early_stop`(조기 종결 때만 `{window, M, reason}`), `windows_run`, `wall_cap_s`(적용된 상한), `timeout`(끊겼을 때 기존) |
| 조기 unstable | 없음(전 창 실행) | 위 (b) 기준 충족 시 `status = unstable`, 데이터 파일 마지막 시각 = 창 j 끝 < tstop 이어도 failed 아님 |
| 판정 창(절차 5) | M_K <= floor' stable / M_K >= M_1 unstable / 모든 창 감소 decaying / 그 밖 undetermined | 분해능 인식형: unstable = g↑(M_1,M_K), decaying = 모든 연속 창 g↓, 분해능 안은 undetermined; stable 불변; 조기 경로 추가 |
| 시간 상한 | `--timeout-s` 있을 때만 | 없으면 `plan.wall_cap_s`; 둘 다 끊김 -> `failed` |
| `.stab.cir` `.control` | `tran ...; let hst; wrdata` | + `save <프로브>`, + 창 경계 `stop when`/`resume`, + `STABWIN` 로그 |
| test_rhp_variants_never_pass[rb1e7] | 끝나지 않음 | 유한 시간 안에 끝나고 PASS 불가(unstable 이거나 failed -> 정의 불가) |
| 안정 회로 `ac.stability`, `pm_deg` 등 | -- | 불변 (단 `plan.tmax`·새 필드 외) |

독립 test 가 새로 볼 것(제안): (1) tran_plan 의 f_crit/n_pp/tmax 식, (2) early_unstable 기준 순수 함수 입출력(경계: j=2, 맥놀이
[1,0.5,1.2], 일정 진폭 [1,1,1,1,1] -> 절대 False, 분해능 이내 증가 -> False, 분해능 초과 연속 증가 [1,1.2,1.5] -> True), (3) 잘린 파일 판정 unstable vs failed, (4) 기본 상한 존재와 `--timeout-s` 우선, (5) 안정 fixture 에서
`early_stop` 없음, (6) `.save` 라인.

## 3. 구현 메모 (U6, 2026-10-08 -- 계약 문안과 달라진 곳·계약이 정하지 않은 곳. 아래 문법 메모는 첫 사례 ngspice 어댑터의 방언 메모다)
README `tools/spice_oracle/README.md` "C10 PM 안정성 근거"가 정본이다. 구현이 계약과 다르거나 계약이 정하지 않아 구현이 정한 것만 적는다.
* **창 경계 `stop when time >= x` -> `time > x`**: ngspice 의 `stop when` 이 `>=` 를 받지 않는다(`Syntax error parsing breakpoint specification`, 실측). 경계를 처음 넘은
  표본에서 멈추고 그 표본은 창 j 밖이다(창 안 표본 집합은 계약과 같다). 멈출 때마다 `delete all` 이 필요하다(끝난 조건을 지우지 않으면 resume 이 같은 조건에서 곧바로 다시 멈춘다).
* **스크립트 안 비교는 `>=` 만**: ngspice 명령 줄의 `>`·`<` 는 출력/입력 리다이렉션이라 `let x = (a > b)` 가 조용히 틀리거나 실패한다(실측). g↑·g↓ 의 엄격 부등식을
  `>=` 로 평가한다 -- floor' > 0 이라 값이 정확히 같을 수 없어 파이썬 판정(엄격)과 같다.
* **wrdata 자릿수**: 스크립트가 `set numdgt=8` 을 명시해 파일 반올림 반 단위 u = 5e-9 를 스크립트와 파이썬이 같은 값으로 쓴다(스크립트의 floor' = 계획 floor + u·지금까지의 max|H|).
* **`early_unstable(M, floor', reltol)` 은 엄격 증가(growth)만** 본다(일정 진폭은 False). 사용자 결정 4(2026-10-08)의 한계 사이클은 별도 함수 `limit_cycle_early` 와 조기 창 선택 `early_window` 가 본다:
  j >= 3 에서 창 j−1 과 j 가 모두 flat(M_j(1−reltol) > floor' 이고 g↑·g↓ 둘 다 아님) -> `unstable`, `early_stop.kind = limit_cycle` + `limit_cycle_vs_slow_decay_unresolved`.
  그래서 3.3 의 EARLY_CASES `constant`([1,1,1,1,1] -> False)는 `early_unstable` 에서는 그대로이고 `limit_cycle_early` 에서 True 다.
* 연장 실행도 같은 `.control`(창 단위 실행·조기 종결)로 돌고 `extension.wall_cap_s` 를 기록한다. 시간 초과·치명 오류는 부분 파일로 판정하지 않는 것도 계약과 같다
  (`wrdata` 를 실행 끝에 한 번 쓰므로 killed 실행은 파일이 없다).
* `wall_s_per_window` 는 `oracle_config.json` 에 있고 근거 측정은 `tools/spice_oracle/smoke/measure_wall_s_per_window.py`.
