verdict: Major 1

# FS-1 (20261107-fs1) 순서 3 동결 재판정 3 (A-193) -- 판정자 독립 측정

## 대상과 격리
- test head는 `5d1e215d`다. audit worktree에 `git merge --no-ff`로 들였고, 병합 커밋은 `d59eaedd`다. 엔진 변경은 0이다.
- 격리 복제본은 `C:/fzf1/iso3`다(`--no-hardlinks --no-local`, origin 제거). 실행 래퍼는 `C:/fzf1/run3.sh`, 출력은 `C:/fzf1/out3/`다.
- 작성자 보고는 증거로 쓰지 않았다.

## 1. MR-1 교체 test 둘

| test | base | 옛 성질 유지 | 코드 뒤 예측 |
|---|---|---|---|
| `test_passive_theta_circuit_front_measured` (회로 P + Rz·Cz θ) | PASS | 거의 유지 -- 아래 **MR-3** 한 군데만 다르다 | PASS |
| `test_eval_results_identical_search_memo_vs_caller_memo` (회로 P, gain ≥ 10 dB, 예산 40) | PASS | 유지 | PASS |

**passive θ test의 옛 성질 대조**
- 그대로인 단언: front ≥ 1, unmeasured = (), `ss:` 행 있음, 재계산 0.
- 회로는 θ capacitance(Cz)와 ss_resistance(Rz)를 가진다. 성질 대상이 그대로다.
- 다른 곳: θ 상자 단언 하한이 1e2로 남았는데 입력 상자는 바뀌었다 → MR-3.

**memo test의 옛 성질 대조**
- 그대로인 단언: front_signature, 모든 평가 결과, run_id 비트 동일, 공허 방지 둘.

**전제 `assert_realized_roots_inside_rails`의 손 식**
- 식: F(V_dd) = V_dd/R − (1+r)·I·e^{−λ(V_dd − I·R)}.
- 회로 P(pmos 소스 = vdd, R out→gnd, r4 toy ID ∝ e^{λ·VSD})의 out KCL은 V/R = (1+r)·I·e^{−λ(V − V0)}이다.
- F는 V에 대해 증가하고 F(0) < 0이다. 그래서 근이 레일 안에 있을 조건은 F(V_dd) ≥ 0이다. 식은 맞다.
- r은 front 점(실현 스냅샷)의 `dc_finger.residual`이다. interface §4.3에 따라 코드 뒤에는 실현 r = m·w_f/W_θ − 1이 된다. base에서는 실현 residual = 0이라 자명하게 통과한다.
- 성격: front에 남은 점은 이미 실현을 통과했으므로 사실상 항진 전제다(해가 없음 -- 기록).

**코드 뒤 손 예측**(`C:/fzf1/probe_p.py` → `C:/fzf1/out3/probe_p.txt`, base 엔진)
- 두 test의 유일한 front 점은 EA:s2(given θ_p)다: I = 1e-5, R = 9e4, a = 0.9 V, W = 47.40 µm, w_f = 1 µm, x = 47.40.
- interface §1 단일 멤버에서 m = 47(base m과 같음)이고 r = −0.00847이다.
- F(V_dd) = +1.09e-5 > 0이므로 레일 안에 근이 있다. 슬라이스가 하나라 w_f 이동이 없고, 탐색 궤적은 같다.
- 그래서 **코드 뒤 PASS로 예측**한다.

## 2. RETIRED `test_unmeasured_points_never_in_final_front`

같은 fail-closed 성질('미측정 점은 최종 front에 없고 unmeasured_front로 간다')은 다음 test들이 정적으로 덮는다(grep `unmeasured_front` 전수).
- `search/test_eps_sweep.py:142` `test_unmeasured_never_in_final_front`
  - 같은 입력이다: circuit_c + CL 미선언 + SS.
  - sweep 분류 수준에서 front == (), unmeasured_front ≥ 1, 각 점 sealed이고 unmeasured ≥ 1을 단언한다.
  - 실현 전 단계라 MR-1의 실현 손실과 무관하다.
- `search/test_find_front.py` R-17 세 개:
  - `test_r17_unmeasured_front_points_pass_the_realize_gate_and_failed_one_is_lost`: run["front"] == [], unmeasured_front 길이를 단언한다.
  - `..._realized_row_is_measured_moves_to_front`
  - `test_r17_front_point_whose_realized_row_is_unmeasured_moves_to_unmeasured_front`: 실현 뒤 미측정이 생긴 front 점이 front가 아니라 unmeasured_front로 간다.
  - 이 셋은 find_front의 실현 뒤 재분류(같은 `classify`)를 덮는다.
- 판단: 삭제는 기준 약화가 아니다. sweep 분류 + 실현 뒤 재분류로 성질이 덮인다.
- 덮이지 않는 것(minor r3-1): notes의 `{"verdict": "unmeasured", "rule": "S-1", constraints: gain_ss_db}` 출력 줄 단언(출력 전용).
- ⚠ 위 세 test의 base 실행은 메모리 부족 중단(아래)으로 **미측정**이다. 통과를 확인하지 못했다.

## 3. MR-2 -- 고쳐짐 (정적; base는 WfCell 코드 없음)
- L-2(1):
  - 요청은 nf 4 · 1e-6이고 W' 4e-6 ≠ 기준 2e-6이다.
  - 공허 방지는 `cdb1 != cdb2 and csb1 != csb2`로 되돌아왔다.
  - 손 계산: cdb1 = 1.8·d_cap, cdb2 = 4·d_cap, csb1 = 3·s_cap, csb2 = 4·s_cap. AND가 성립한다.
- R-16 세 단언이 약화 없이 돌아왔다.
  - 탐색 V(s) = I·R(= 스케일 전 a)
  - `ev.objectives.power_w == V_dd·(i + I_b)`(rel 1e-12)
  - with_source일 때 `dc_current["I2"] == R16_IB`(rel 1e-12)
  - `icm_config` 전제도 함께 돌아왔다.

## 4. minor 반영
- n-3: `pytest.raises(LookupError)`로 넓혔다.
- n-5: R-16·S3-6에 `icm_config` 입력 고정 전제가 다시 들어갔다.
- n-6: hand_oracle을 호출 때 import하게 바꿨다. changed 실행에서 `search/test_realize_front.py`가 수집됐다(R-4·R-7 등은 코드 없음 실패·오류).
  - 이 실행의 수집 오류는 `search/test_start_intervals.py` 하나였다.
  - 전체 `--collect-only`는 중단돼 미측정이다. 다만 남은 둘(`test_l_bin_search` polish_cells, `sizing/test_realize_fingers` DeclaredRatio)의 import 줄은 바뀌지 않았다(정적). '3모듈로 줄었다'는 보고는 정적으로 맞다.
- n-8: `list(d["small_m"]) == ["M1"]`(손 값)이다.

## Major

**MR-3 (기준 약화 -- 입력 상자를 바꾸고 단언을 맞추지 않음)**
- 위치: `search/test_find_front.py:302` `assert ... 1e2 <= th[("ss_resistance", "Rz")] <= 1e6`
- 새 입력은 `rbounds=P_RBOUNDS = (1e3, 1e6)`이다. ss_resistance 상자는 `resistance_bounds_ohm`이다(`search/search_values.py:49`, resistance·ss_resistance 공용).
- 옛 test는 rbounds (1e2, 1e6)와 단언 1e2가 같았다. 지금은 단언이 상자보다 한 decade 느슨해서, 상자 밖 값 [1e2, 1e3)이 통과한다.
- 고칠 것: `P_RBOUNDS[0] <= rz <= P_RBOUNDS[1]` 한 줄. 재판정은 이 한 줄만 보면 된다.

## minor
- r3-1: 위 S-1 unmeasured notes 줄의 단언이 없다(출력 전용, LA-1 입력).
- r3-2: `assert_realized_roots_inside_rails`는 front 점에 대해 항진이다(실현을 통과한 점만 front). 해는 없으나 '공허 방지'로 세지 않는다.

## base 재측정
| 묶음 | 결과 | 분류 |
|---|---|---|
| `tests/structure` | 8 failed / 198 passed / 1 deselected (123 s) | 8 = 코드 없음 (앞과 같음) |
| 고친 5파일 | 33 failed / 57 passed / 1 deselected / 4 errors (251 s) | 37 모두 코드 없음 (WfCell 26, perf `wf_neighbor_*` 5, initial_wf·RealizeInput·slice_rounds·G-7 subprocess 등). test 결함 0. MR-1 두 test PASS |

**중단·미측정**
- `C:/fzf1/r3.sh`의 3·4번째 실행(덮는 test 3개 cover와 `--collect-only`)은 하네스가 시스템 메모리 부족으로 중단했다.
- 지시에 따라 다시 띄우지 않았다. 남은 pytest 프로세스는 0이다(확인).
- 손 예측 probe(pytest 아님, 단일 프로세스)는 여유 5.48 GB를 확인한 뒤 한 번 돌렸다.

## 금지 명령
- 이번 재판정에서 `python -`, `sed -i`, `cat > /dev/null`, heredoc은 0회다.
- 끝날 때 python 프로세스는 0이다.

## code 착수
- **불가(Major 1, MR-3 한 줄).**
- 고친 뒤 확인할 것: 그 한 줄. 추가로 메모리가 허락하면 덮는 test 3개 base 통과(`search/test_eps_sweep.py::test_unmeasured_never_in_final_front`, `search/test_find_front.py -k r17`).
