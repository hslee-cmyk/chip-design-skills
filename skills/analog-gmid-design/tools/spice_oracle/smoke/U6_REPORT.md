# U6 SPICE 오라클 구현 기록 (2026-10-08~09, 기록 -- test 아님, 판정 증거도 아님: 판정은 auditor 의 격리 복제본 test, WP-13)

대상: 설계 40 §4·§10.2·§11 U6, 계획 v6.2 N3.6/N3.8, `docs/03-analysis/oracle-c10-early-termination.contract.md` d56ba66(+ 3 구현 메모),
사용자 결정 4(지속 진동 = unstable(limit_cycle) FAIL), Q10(Z = N + P, `.pz`), Q3·Q4(offset MC, 스윙·ICMR), Q11(`.noise`).
환경: Windows 11, ngspice-46, sky130 tt 27 C, Python 3.14. **측정은 다른 에이전트의 ngspice 가 6~20 개 동시에 도는 공유 머신에서 했다 -- 같은 `.stab.cir` 가 81.5 s ~ 1547.5 s 로 달랐다(부하 변동).**

## 1. C10 조기 종결 계약 이행 (오라클 C10 test 파일: 59 test, `-m "not slow"`)

| 항목 | 결과 |
|---|---|
| 걸음 상한 tmax = min(1/(2π f_lo), 1/(f_crit·n_pp)), f_crit = 대역 한정 argmin | CS β=1 f_crit = 10^7.35 Hz, 노치 1e4 Hz, rb1e6 4.22e4 Hz, rb1e7 4.2e3 Hz (독립 test 의 `band_f_crit` 과 일치 -- test_multi_crossing_plan_uses_f_lo·test_plan_default_reltol 통과) |
| 창 단위 실행(`stop when`/`resume`, `STABWIN j M_j` 로그), `.save` 제한, `early_stop`·`windows_run`·`wall_cap_s` 기록 | test_growing_fixture_early_stop, test_stab_netlist_saves_probes_only[4], test_early_unstable_predicate[12], test_config_declares_wall_cap 통과 |
| 기본 시간 상한 `oracle_config.json` (wall_s_per_window 306.1 s = c_worst 138.8 x safety 2.205) | rb1e7 변형이 상한 1836.6 s(= 306.1 x K 6)에서 끊겨 **유한 시간 안에 끝남**(전체 1843 s; 옛 코드는 30 분 넘게 끝나지 않음) |
| 안정 fixture 판정 불변 | 아래 표: 안정 11 개 실행 모두 `stable`(조기 기준 한 번도 불충족), `ac` 스칼라(pm_deg·pm_open_loop_deg·pm_crosscheck_deg·gap·ugf_hz·dc_gain_db·loop_ugf_hz) 24 개 sim 이 옛 코드와 **비트 동일**. 달라진 2 개는 N 이 세어지게 된 희박 스윕(아래 3) |

판정 변화(전/후)는 옛 코드(master 병합 직후, 같은 test 입력) 대 이 구현이다. 전 = `tmp_base`, 후 = `tmp_f6`(전체 not-slow 실행, 위 명령). `P(pz,확인)` = `.pz` 의 P 와
개루프 과도 확인 결과(True/False/None).

| fixture(test dir) | file | 전 tr / N / verdict | 후 tr(early) / N / P(pz,확인) / verdict | 전 M | 후 M |
|---|---|---|---|---|---|
| classic0 | o/t3stage.free.sim.json | unstable / N=2 / FAIL | unstable 창3:growth / N=2 / P=None(None) / FAIL | [0.0492, 0.0934, 0.186, 0.293, 0.219, 0.359] | [0.0546, 0.109, 0.233] |
| lowpm0 | o/t3stage.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=None(None) / PASS | [0.0363, 0.0167, 0.00781, 0.00418, 0.00218, 0.00104] | [0.0369, 0.0152, 0.00644, 0.00232, 0.000958, 0.000443] |
| rhp0 | o/trhp_posfb.forced.sim.json | unstable / N=0 / INCOMPLETE | undetermined / N=0 / P=2(True) / INCOMPLETE | [1.05, 1.06, 1.06, 1.05, 1.07, 1.07] | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] |
| rhp0 | o/trhp_posfb.free.sim.json | unstable / N=0 / INCOMPLETE | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] | [1.06, 1.06, 1.06, 1.06] |
| test_cache_stability_outside_a0 | o1/tfb_cs_rfeedback.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=0(None) / PASS | [0.0613, 0.0135, 0.00253, 0.000598, 0.000118, 2.53e-05] | [0.0635, 0.00997, 0.00156, 0.000242, 3.74e-05, 5.47e-06] |
| test_cache_stability_outside_a0 | o2/tfb_cs_rfeedback.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=0(None) / PASS | [0.0613, 0.0135, 0.00253, 0.000598, 0.000118, 2.53e-05] | [0.0635, 0.00997, 0.00156, 0.000242, 3.74e-05, 5.47e-06] |
| test_cache_stability_outside_a0 | o3/tfb_cs_rfeedback.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=0(None) / PASS | [0.0613, 0.0135, 0.00253, 0.000598, 0.000118, 2.53e-05] | [0.0635, 0.00997, 0.00156, 0.000242, 3.74e-05, 5.47e-06] |
| test_cache_stability_outside_a1 | o1/t3stage.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=None(None) / PASS | [0.0363, 0.0167, 0.00781, 0.00418, 0.00218, 0.00104] | [0.0369, 0.0152, 0.00644, 0.00232, 0.000958, 0.000443] |
| test_cache_stability_outside_a1 | o2/t3stage.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=None(None) / PASS | [0.0363, 0.0167, 0.00781, 0.00418, 0.00218, 0.00104] | [0.0369, 0.0152, 0.00644, 0.00232, 0.000958, 0.000443] |
| test_cache_stability_outside_a1 | o3/t3stage.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=None(None) / PASS | [0.0363, 0.0167, 0.00781, 0.00418, 0.00218, 0.00104] | [0.0369, 0.0152, 0.00644, 0.00232, 0.000958, 0.000443] |
| test_classic_sparse_sweep_coun0 | o/t3stage.free.sim.json | unstable / N=None / INCOMPLETE | unstable 창3:growth / N=2 / P=None(None) / FAIL | [0.0501, 0.0988, 0.187, 0.294, 0.366, 0.295] | [0.0889, 0.132, 0.239] |
| test_multi_crossing_plan_uses_0 | o/tnotch.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=None(None) / PASS | [0.00707, 0.00362, 0.00171, 0.000936, 0.000528, 0.00029] | [0.00726, 0.00336, 0.00151, 0.000503, 0.000237, 0.000112] |
| test_no_pm_raw_not_checked0 | o/trc_lowpass_div.free.sim.json | None / N=None / INCOMPLETE | None / N=None / P=None(None) / INCOMPLETE | - | - |
| test_plan_default_reltol0 | o/tcs_nmos_rload.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=0(None) / PASS | [0.0135, 4.53e-06, 9.5e-08, 9.2e-08] | [0.0135, 1.59e-05, 1.09e-07, 9.2e-08] |
| test_rhp_constraint_never_pass0 | o/trhp_posfb.free.sim.json | unstable / N=0 / INCOMPLETE | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] | [1.06, 1.06, 1.06, 1.06] |
| test_rhp_constraint_never_pass1 | o/trhp_posfb.free.sim.json | unstable / N=0 / INCOMPLETE | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] | [1.06, 1.06, 1.06, 1.06] |
| test_rhp_constraint_never_pass2 | o/trhp_posfb.free.sim.json | unstable / N=0 / INCOMPLETE | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] | [1.06, 1.06, 1.06, 1.06] |
| test_rhp_control_pass_without_0 | o/trhp_posfb.free.sim.json | unstable / N=0 / PASS | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] | [1.06, 1.06, 1.06, 1.06] |
| test_rhp_variants_never_pass_r0 | o/trhp_posfb.free.sim.json | (없음) | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | - | [1.06, 1.06, 1.06, 1.06] |
| test_rhp_variants_never_pass_r1 | o/trhp_posfb.free.sim.json | (없음) | undetermined / N=0 / P=2(True) / FAIL | - | [1.31, 1.1, 1.14, 1.18, 1.1, 1.1] |
| test_rhp_variants_never_pass_r2 | o/trhp_posfb.free.sim.json | (없음) | failed / N=0 / P=2(True) / FAIL | - | - |
| test_rhp_with_other_fail_is_fa0 | o/trhp_posfb.free.sim.json | unstable / N=0 / FAIL | unstable 창4:limit_cycle / N=0 / P=2(None) / FAIL | [1.06, 1.06, 1.06, 1.06, 1.06, 1.06] | [1.06, 1.06, 1.06, 1.06] |
| test_stable_beta_loop_value_un0 | o/tfb_cs_rfeedback.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=0(None) / PASS | [0.0613, 0.0135, 0.00253, 0.000598, 0.000118, 2.53e-05] | [0.0635, 0.00997, 0.00156, 0.000242, 3.74e-05, 5.47e-06] |
| test_stable_cs_beta1_value_unc0 | o/tcs_nmos_rload.free.sim.json | stable / N=0 / PASS | stable / N=0 / P=0(None) / PASS | [0.0135, 3.92e-06, 3e-09, 0, 0, 0] | [0.0135, 1.59e-05, 1.8e-08, 0, 0, 0] |
| test_stable_sparse_sweep_nyqui0 | o/t3stage.free.sim.json | stable / N=None / INCOMPLETE | stable / N=0 / P=None(None) / PASS | [0.0371, 0.0162, 0.00853, 0.00438, 0.0018, 0.00106] | [0.0375, 0.015, 0.00456, 0.00209, 0.000968, 0.000448] |
| test_sustained_oscillation_und0 | o/trhp_posfb.free.sim.json | undetermined / N=0 / INCOMPLETE | undetermined / N=0 / P=2(True) / FAIL | [1.43, 1.21, 0.683, 1.13, 1.45, 1.3] | [1.31, 1.1, 1.14, 1.18, 1.1, 1.1] |
| test_tail_above_one_nyquist_un0 | o/tnotch.free.sim.json | stable / N=None / INCOMPLETE | stable / N=None / P=None(None) / INCOMPLETE | [0.00699, 0.00354, 0.00171, 0.000919, 0.000505, 0.000276] | [0.00731, 0.00334, 0.00144, 0.000486, 0.000227, 0.000106] |
| test_timeout_s_overrides_defau0 | t.free.sim.json | failed / N=0 / None | failed / N=0 / P=2(True) / None | - | - |
| test_truncated_transient_faile0 | t.free.sim.json | failed / N=0 / None | failed / N=0 / P=2(True) / None | - | - |


* **한계 사이클**(사용자 결정 4): rb1e5(Rb 100 kΩ) 는 창 4 에서 `limit_cycle` 조기 종결 -- 창 최댓값 M = [1.0606, 1.0591, 1.0594, 1.0592] 가 reltol 1e-4 + floor' 7.0e-5 안에서 일정.
  `limit_cycle_vs_slow_decay_unresolved` 를 비교표 맨 앞·`summary` 최상위에 올린다.
* **rb1e6**(sustained): M = [1.31, 1.10, 1.14, 1.18, 1.10, 1.10] -- 창 사이 변화가 분해능(1e-4) 밖이라 **`limit_cycle` 기준을 충족하지 않는다**. 과도는 `undetermined` 로 남고(옛 규칙과 같은 결과),
  free verdict 는 `.pz` P = 2 가 개루프 과도(출력 변위 V_T 의 창 3 연속 증가)로 확인되어 Z = 0 + 2 = 2 >= 1 -> **FAIL** (INCOMPLETE 에서 FAIL 로). 지속 진동이 `unstable(limit_cycle)` 이 되는 것은 창 진폭이 분해능 안에서
  일정한 때(rb1e5 형)뿐이다 -- 사용자 결정 4 의 "분해능 안" 문구 그대로. (주의: rb1e6 은 계약 3의 단독 실행 예 M = [1.311, 1.159, 1.272, 1.198, 1.120, 1.099] 와 같은 종류의 이완 진동이다.)
* **rb1e7**: 과도가 상한에서 끊겨 `failed`(진동 확인이 아니므로 unstable 아님), `.pz` P = 2 가 개루프 과도 확인(창 3, 1 s)으로 FAIL.

### 실행 시간 (test 호출 시간, 같은 test 입력)

| test | 전(옛 코드, 한가한 시각) | 후(이 구현, 공유 머신 부하 아래) |
|---|---|---|
| test_rhp_variants_never_pass[rb1e5] | (옛 코드에서는 `oracle_config.json` 부재로 즉시 실패 -- 시간 비교 없음) | 57.9 s (과도 창 4 조기 종결) |
| test_rhp_variants_never_pass[rb1e6] | (같은 이유로 비교 없음; 옛 tmax 의 단독 오라클 실행은 아래 sustained 와 같은 회로 15.6 s) | 1080 s |
| test_rhp_variants_never_pass[rb1e7] | **끝나지 않음**(> 30 분, 메모리 오류; 계약 0) | 1843 s (= 상한 1836.6 s + 확인·판정 7 s) |
| test_sustained_oscillation_undetermined_incomplete | 15.6 s | 809 s (같은 .stab.cir 단독 반복: 81.5 / 783 / 883 / 1548 s) |
| 오라클 C10 파일 전체(not slow) | 66 s | 4290 s(1 h 11 m) |
| 느린 test(`-m slow`: test_rhp_fixture_closed_loop_oscillates_and_n_is_zero[rb1e7], 독립 기준 실행 -- 오라클 코드 아님) | - | 1453 s 통과 |
| 나머지 오라클 test(C10 제외, not slow, 531 개) | 958 s(527 통과 + 1 실패) | 1044 s(530 통과 + **같은 1 실패**) |

나머지 오라클 test 의 1 실패 `test_oracle_cm_loop.py::test_engine_mna_matches_ngspice_cm_pm` 는 옛 코드에서도 같은 실패(엔진 모듈 import 불가, 이 구현과 무관).
오라클 소스 독립(C1) test 가 새 파일 3 개에도 통과(+3).

## 2. 독립 `.pz` 와 Nyquist (사용자 결정 Q10)

* N: 적응 세분화(인접 편각 >= π/2 구간을 `ac dec` 로 이분 재측정, 상한 10 라운드). 희박 스윕 두 fixture 가 세어진다: classic(points_per_decade 2) N = 2(라운드 3, 표본 5 추가), stable lowpm(points_per_decade 3)
  N = 0(라운드 2, 표본 3 추가) -- 둘 다 밀한 스윕에서 센 값(2, 0)과 같다.
* P: `.pz`(큰 L·C 없는 개루프, 동작점 패스 값). 작은 회로 RHP fixture 는 극을 정확히 낸다(손 모형 5.63e3 rad/s 대 5.09e3, ±10 %). 안정 CS·β 루프 fixture 는 P = 0. **3단 CS·노치 회로는 `.pz` 가 반복 한도에서 포기**(P = None, 폐루프
  과도·N 이 판정). **파일럿 forced(소자 51 개)는 경고 없이 RHP 극 23 개를 내는 오답**(개루프 과도에는 증가 없음, 폐루프 과도 stable) -> `.pz` 신뢰 규칙(README 절차 8)이 stable 판정을 지킨다.
* 최종 판정: 과도 unstable(한계 사이클 포함) 또는 N >= 1 또는 (Z >= 1 이고 P 가 쓸 수 있음) -> FAIL. Z = 0 + 과도 undetermined 는 INCOMPLETE(Nyquist 만으로 안정이라 하지 않음).

## 3. `.noise`·offset MC·스윙/ICMR 자체 점검 (`smoke/u6_selfchecks.py`, 손계산·독립 경로 대조)

| 점검 | 결과 |
|---|---|
| `.noise` 저항 분압 RC(Ra = Rb = 2 kΩ) 입력 환산 열잡음 | 6.6304e-17 V²/Hz, 손계산 4kT(Ra‖Rb)/H0² = 6.63043e-17 와 상대 6.4e-7, 몫 각 0.5 |
| `.noise` 폐루프 적분(tfb_cs_rfeedback) | 3.83146e-4 Vrms, ngspice 자체 `onoise_total` 3.83130e-4 와 4e-5 일치, 꼬리 수렴 |
| offset MC(5T OTA, r = 0.05 -> 201 표본) | σ_in = 3.236 mV, 소자·변수별 1σ 결정적 섭동 감도 RSS = 3.212 mV (비 1.008), M1 vth0 감도 1.1843 mV 대 손계산 slope/sqrt(L_um·W_um) = 1.1865 mV |
| 스윙·ICMR(5T OTA, 입력 DC 0.9 V) | 스윙 1.2065 V(출력 창 0.2967 ~ 1.6142 V), ICMR 0.6289 V(입력 창 0.6701 ~ 1.2990 V), icm_margin 0.2299 V |
| 파일럿(forced) `.noise` | 개루프 th_in 4.65e-15 V²/Hz, fc 5.2e5 Hz; 폐루프 적분 6.76e-4 Vrms(상한 1 회 확장, 수렴) -- 입력 셀 이름은 호출자 선언이라 excess 값은 선언에 따른다 |

## 4. 알려진 한계·결정 필요 (보고서 본문 참고)

* 샘플링 kT/C 는 과도 기반 측정을 만들지 않았다(`ktc_sampling = not_measured`).
* 파일럿 free 모드는 smoke 의 옛 엔진 덤프에서 DC 해가 죽는다(smoke 보고 §2) -- 스윙/ICMR/MC 는 free servo 가 필요해 파일럿에는 아직 못 돌렸다(5T OTA·CS 로 검증).
* `.pz` 신뢰 규칙은 사용자 결정 Q10 의 문구 'Z >= 1 이면 FAIL' 에 단서(폐루프 과도 stable 이면 `.pz` 무시, 과도 미정이면 개루프 과도 확인)를 붙인 것이다.
