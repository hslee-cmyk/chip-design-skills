# 오라클 C10 폐루프 과도: 조기 종결 계약 개정 (사용자 결정 B, 2026-10-08)

대상: `skills/analog-gmid-design/tools/spice_oracle/README.md` "[신규] C10 PM 안정성 근거" 절차 3~5.
이 문서는 계약 문안이다. 구현 커밋에서 README 절차 3~5 에 같은 문안을 옮기고 이 문서는 근거로 남긴다.

## 0. 문제(실측)
절차 4 의 계획은 시간 척도로 f_lo 만 쓴다(tmax = W = 1/f_lo 급, tstop = t_end + K·W). GHz 로 진동하는(또는 GHz 버스트를 내는
이완 진동) 불안정 회로는 ngspice LTE 걸음 제어가 GHz 주기를 따라가서 tstop(예: 1.6 ms)까지 걸음 수가 끝없이 늘고(>30 분,
메모리 오류) `--timeout-s` 가 없으면 끝나지 않는다. test_rhp_variants_never_pass[rb1e7] 가 걸린다.

## 1. 개정 문안

### (a) 걸음 상한이 f_lo 와 가장 빠른 관련 루프 주파수를 함께 쓴다
* f_crit = 측정 곡선 L(닫기 부호 반영)에서 |1+L| 이 최소인 표본의 주파수(`min |1+L|` 위치 -- 폐루프가 가장 약하게 눌린 곳 =
  Nyquist 곡선이 −1 에 가장 가까운 곳 = 지속 진동이 생긴다면 그 주파수). 개루프 RHP 극 주파수는 L 로 셀 수 없으므로(절차 2
  '편각 원리는 차만 준다') 쓰지 않는다. f_hi(가장 높은 교차)는 이전 결정대로 계획에 쓰지 않는다.
* 한 주기당 표본 수 n_pp = ceil(π / arccos(1 − reltol)). 유도: 표본 간격 Δ = 주기/n_pp 일 때 정현파 봉우리를 놓치는 최대 상대
  오차가 1 − cos(π/n_pp) 이므로, 이 오차를 ngspice 가 쓰는 해 정확도 reltol(입력 `testbench.options`, 없으면 기본 1e-3)
  이하로 하는 최소 n_pp (reltol 1e-3 이면 71). 임의 상수 없음.
* tmax = min( 1/(2π f_lo), 1/(f_crit · n_pp) ). td = tr = tf = pw = 1/(2π f_lo), 창 W = 1/f_lo, K, t_end, tstop 은 지금과 같다.
  (f_crit 가 f_lo 근처면 tmax 는 지금보다 줄지 않는다 -- 1/(f_crit n_pp) 가 더 클 때 min 이 1/(2π f_lo) 를 고른다.)
  따라서 안정 회로 중 f_crit·n_pp·2π <= f_lo 가 아닌 것은 걸음이 더 촘촘해져 데이터 표본이 늘 뿐, 창 경계·M_j 정의는 그대로다.

### (b) 창 단위 조기 종결(unstable 확정)
* 폐루프 과도를 창 단위로 실행한다: ngspice 안에서 `stop when time >= t_end + j·W` / `resume` 로 창 j = 1..K 를 차례로 끝내며,
  창이 끝날 때마다 M_j = max|e| (e = H − H(0), 창 j 안 표본)를 로그에 한 줄(`STABWIN j M_j`) 쓴다. 데이터 파일(`.stab.txt`)은
  멈춘 시각까지 쓴다(`wrdata`).
* 조기 unstable 기준(`early_unstable(M, floor', reltol)`, 기존 창 판정과 같은 M·floor' 정의) -- **엄격한 증가만**:
  창 사이 증가 g(j) := M_j·(1 − reltol) > M_{j−1}·(1 + reltol) + floor'  (측정 분해능을 넘는 증가).
  유도: M_j 는 표본 봉우리라 상대 오차가 최대 1−cos(π/n_pp) <= reltol(절 (a)), 절대 분해능은 floor' 이므로, 두 창의
  측정 불확실 구간이 겹치지 않을 때만 '커졌다'고 인정한다. 새 상수 없음.
  기준: j >= 3 인 첫 창에서 g(j−1) 그리고 g(j) (연속 두 창 증가) 그리고 M_j >= M_1.
  3 은 추세를 세우는 최소 점 수이고 창 한 개의 맥놀이를 거른다.
  **일정 진폭 지속 진동은 g 를 만족하지 못하므로(M_j ≈ M_{j−1}, 증가가 reltol·분해능 이내) 절대 조기 종결하지 않는다.** 그 경우는
  기존 규칙 그대로(K 창 끝까지 또는 시간 상한 -> failed / 기존 판정, 예: test_sustained_oscillation_undetermined_incomplete 의
  현재 결과 불변). 감쇠·완화·비단조 진동도 같은 이유로 영향 없음.
  충족하면 즉시 중단하고 `status = unstable`, `early_stop = {window: j, M: [M_1..M_j], reason}` 를 기록한다. 연장 실행 없음.
* 충족하지 않으면 K 창을 끝까지 돌리고 기존 판정(절차 5: stable / unstable / decaying / undetermined, 연장)을 그대로 쓴다.
  기존 규칙의 변경은 없다 -- 조기 기준은 **추가 단축 경로**일 뿐이다.
* 파이썬은 파일에서 M_j 를 다시 계산해 같은 기준을 검증한다(`transient_decision` 이 잘린 파일을 받아: 마지막 시각이 창 j 끝에
  닿았고 기준을 충족하면 unstable(`early_stop`); 아니고 tstop 에 못 닿았으면 기존대로 `failed`). ngspice 가 중단 시점을 정하고
  판정은 파일이 증명한다.
* 안정 회로 판정 불변 조건: 구현 커밋은 안정 판정이 나는 모든 기존 test 회로·fixture(`stable`/`decaying`->`stable`)에서 창 별 M 이
  위 기준을 한 번도 충족하지 않음을 확인한다(충족하면 기준 설계를 되돌린다). 일정 진폭 지속 진동 fixture 의 판정도 개정 전과 같아야 한다. 불안정은 계속 FAIL.
* 첫 창 안에서 끝나지 않는 GHz 버스트: 창 안 부분 최댓값이 아직 없어 기준을 못 쓴다 -> (c) 가 끊는다.

### (c) 기본 시간 상한(--timeout-s 없어도)
* 설정 `skills/analog-gmid-design/tools/spice_oracle/oracle_config.json` 의 `stability_transient.wall_s_per_window`
  (창 하나를 끝내는 ngspice 실행 시간의 상한) 를 선언한다. 근거 필드 `justification` 을 같이 둔다: 안정 판정 코퍼스(test
  회로 4종·smoke 회로)의 창당 실측 최댓값 × 여유(실측 분포로 구현 커밋에서 채움 -- 수치는 지금 정하지 않는다).
* 계획 시간 상한 `plan.wall_cap_s` = wall_s_per_window × (계획 창 수 K + 연장 창 수 n). 실행 시간 상한 = `--timeout-s` 가 있으면
  그것(사용자 지정 우선), 없으면 `plan.wall_cap_s`. 동작점 패스에는 적용하지 않는다(기존).
* 끊기면(`TimeoutExpired`) 또는 ngspice 가 치명 오류(메모리·Timestep too small 로 비정상 종료, tstop 미도달)로 끝나면 지금처럼
  `failed`(사유 '과도 시간 초과' / '과도가 tstop 까지 가지 않았다') -> '모름' -> PM 정의 불가 -> PASS 불가. 이 경로는 `unstable` 이
  아니다(진동을 확인한 것이 아니므로).

### (d) 저장 벡터 제한
* 과도 넷리스트 `.control` 은 `save` 로 프로브 벡터만 저장한다: 출력 H 의 식에 쓰는 노드 전압/전류(`hst` 의 피연산자)와 time.
  (`.stab.cir`, `.stab2.cir` 둘 다.) 메모리 오류 완화용이며 데이터 파일 내용은 같다.

## 2. 바뀌는 기대값 목록

| 대상 | 지금 | 개정 후 |
|---|---|---|
| `plan` 새 필드 | -- | `f_crit_hz`, `n_pp`, `reltol`, `wall_cap_s`, `windows_planned`(= windows) |
| `plan.tmax` | 1/(2π f_lo) | min(1/(2π f_lo), 1/(f_crit·n_pp)); `td/tr/tf/pw/window_s/t_kick_end` 불변; `tstop` = t_end + K·W 불변(계획 필드) |
| `plan.f_hi_hz`, `f_lo_hz`, `kick_V`, `windows`, `floor_V` | 그대로 | 그대로 |
| `transient` 새 필드 | -- | `early_stop`(조기 종결 때만 `{window, M, reason}`), `windows_run`, `wall_cap_s`(적용된 상한), `timeout`(끊겼을 때 기존) |
| 조기 unstable | 없음(전 창 실행) | 위 (b) 기준 충족 시 `status = unstable`, 데이터 파일 마지막 시각 = 창 j 끝 < tstop 이어도 failed 아님 |
| 판정 창(절차 5) | M_K <= floor' stable / M_K >= M_1 unstable / 모든 창 감소 decaying / 그 밖 undetermined | 불변 (조기 경로 추가뿐) |
| 시간 상한 | `--timeout-s` 있을 때만 | 없으면 `plan.wall_cap_s`; 둘 다 끊김 -> `failed` |
| `.stab.cir` `.control` | `tran ...; let hst; wrdata` | + `save <프로브>`, + 창 경계 `stop when`/`resume`, + `STABWIN` 로그 |
| test_rhp_variants_never_pass[rb1e7] | 끝나지 않음 | 유한 시간 안에 끝나고 PASS 불가(unstable 이거나 failed -> 정의 불가) |
| 안정 회로 `ac.stability`, `pm_deg` 등 | -- | 불변 (단 `plan.tmax`·새 필드 외) |

독립 test 가 새로 볼 것(제안): (1) tran_plan 의 f_crit/n_pp/tmax 식, (2) early_unstable 기준 순수 함수 입출력(경계: j=2, 맥놀이
[1,0.5,1.2], 일정 진폭 [1,1,1,1,1] -> 절대 False, 분해능 이내 증가 -> False, 분해능 초과 연속 증가 [1,1.2,1.5] -> True), (3) 잘린 파일 판정 unstable vs failed, (4) 기본 상한 존재와 `--timeout-s` 우선, (5) 안정 fixture 에서
`early_stop` 없음, (6) `.save` 라인.
