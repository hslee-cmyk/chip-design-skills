# I-C11 two_stage_ota KVL 실패 진단 (2026-10-07)

진단만 한 문서다. 저장소는 고치지 않았다.
실행은 `git clone --no-hardlinks gmid-light /c/g455/repo`로 만든 복제본(6df4bd7 checkout)에서만 했다. monkeypatch 실험 스크립트는 `/c/g455/scratch`에만 두었고, 끝난 뒤 /c/g455는 삭제했다.
수치는 전부 이번 실행에서 직접 측정했다. 측정하지 않은 것은 **[추측]**, 회로 위상 해석이 필요한 판단은 **[사용자 확인 필요]**로 표시했다.

## 1. 기록 원문과 행 번호 (6df4bd7, 메인 저장소와 같은 커밋)

| 문서 | 행 | 원문 |
|---|---|---|
| plan `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` N5.3(951행 `### N5.3 열린 이슈`) | 981 | `\| I-C11 \| two_stage_ota stage1_out 분리와 nmcnr stage2_diode_ref 이월 -- 해소 전에는 두 회로에서 유도 기능을 돌릴 수 없다 \| U-09 \|` |
| plan N6.1 Phase 4 행 | 1003 | "... 기존 4개 회로 실행 가능성(I-C11), IC11 활성 \| red-green \| U-04, U-05, U-09, U-26, U-27 \| `40-defect-fixes`" |
| plan N6.3 | 1033 | "동작 보존 Phase(1~3)는 실행 가능한 회로 전부에서 equivalence(I-C11 해소 전 two_stage·nmcnr, ...)" |
| plan U-09 | 1086 | `\| U-09 \| two_stage stage1_out 분리·nmcnr stage2_diode_ref 이월을 언제 풀지 \| Phase 4에서 DF와 함께. 근거: 기존 4개 회로 측정(N6.3)이 Phase 4부터 동작 변경 판정에 필요 \| Phase 4 \|` |
| plan 40-defect-fixes 범위 | 1160 | "... I-C11 해소 설계 ..." |
| history `gain-budget-gmid-sizing.history.md` | 411 | "I-A10, I-A11, I-B22, I-C10, I-C11은 v5.0에서 새로 연 항목이고 아직 열려 있다(계획서 N5.3)." |
| history | 459 | "신설: ... I-C11(옛 A66, U-09)" |
| history | 4357 | `\| A66 \| two_stage stage1_ref/stage1_out 분리는 "여기서 멈춤, 별도 세션" \| 세션41 \| context:12420 \| §10.15 선행(plan:865), 4회로 측정 선행(history:3004) \| 유효·미구현(이월) \|` |
| history | 1491~1492 | `stage1_out` KVL 오차: sizing self-test +0.162 → −0.038 V, stick_diagram +0.754 → +0.391 V(B15/B16 배선의 부수 효과) |
| history | 3418 | "`two_stage_ota` \| `stage1_out` VDS 합이 vdd와 불일치 -- 세션41 이월 항목" |
| history | 3560 | "0. 선행: ... two_stage `stage1_out`·nmcnr `stage2_diode_ref` 이월 해소 -- 이것이 없으면 4개 회로 일반성 측정 자체가 불가능하다" |
| `.ai/context.md` 세션41 §3 | 12381~12432 | M4(vds_match_vgs_of=M6, 1.004V) + M2(compensation, 1.2V) + M5(0.4V) = 2.60V ≠ 1.8V. "M1/M2/M6은 compensation(AC 도메인)이 정하고 M3/M4/M5/M7은 헤드룸(DC 도메인)이 정하는데, 이 둘을 서로 맞춰주는 메커니즘이 없다". 사용자 결정: 여기서 멈춤 |
| test | `assets/tests/unit/test_selftest_sizing_recipe.py` 2396·2538, `test_selftest_stick_diagram.py` 482 | I-C11 strict xfail 3건(S051·S054·S157)과 짝을 이루는 `_known_limitation`(메시지에 `stage1_out`·`KVL` 포함을 단언) |

## 2. 실패 재현 (복제본, `python run_harness.py two_stage_ota`)

```
sizing_recipe.py:9217 optimize_full_circuit_budget -> _evaluate(theta_values)
sizing_recipe.py:8636 _evaluate -> _resolve_vertical_group(vsid)
sizing_recipe.py:7197 _hr_resolve_vertical_group -> _verify_group_kvl_sum(vsid, members)
sizing_recipe.py:7079 _hr_verify_group_kvl_sum -> raise ValueError(
ValueError: 'stage1_out' 그룹의 VDS 합(2.37965V)이 vdd(1.8V)와 불일치(diff=+0.579654V) -- KVL(직렬 branch
전압강하 합=vdd)이 깨졌다. 소자별 값: M4=0.9172, M2=0.9, refs(M5=0.5625). ...
```

* 하네스 exit code는 **0**이다. `run()`이 예외를 잡고 `[FAIL]`만 찍기 때문이다. 이 부분은 DF-37/CC-4 몫이며 이번 원인과는 별개다.
* 실패 함수는 `_hr_verify_group_kvl_sum`(6976~7085)이다. 호출 지점은 `_hr_resolve_vertical_group` 7196~7198행으로, 멤버 전부가 이미 vds를 가진 "unresolved 없음" 분기다.
* 실패 그룹은 `stage1_out` = {M4, M2}이고, `budget_reference_device`는 M5다.

`set_device_vds`와 KVL 검증 호출을 실행 순서대로 기록한 결과다(첫 평가).

| 순서 | 소자 | vds | `_vds_source` | 비고 |
|---|---|---|---|---|
| 1 | M1 | 0.9000 | `compensation:stage0` | `optimize_multistage()`가 VDS_candidates에서 **탐색으로 고른 값**(8301행 기입) |
| 2 | M2 | 0.9000 | `compensation:stage0` | 같음 |
| 3 | M6 | 0.3000 | `compensation:stage1` | |
| 4 | M4 | 0.9172 | `metric_stage_budget` | feed `vds_match_vgs_of={M4:M6}`가 정한 VSG(M6)(gm_id 16.5, L 0.34 µm) |
| 5 | (검증) stage1_out | | | M5가 아직 없어서 `_HeadroomDependencyNotReady`를 내고 다음 pass로 미룸 |
| 6 | M3 | 0.3375 | `allocate_stack_headroom:stage1_ref` | diode, gm_id 미확정(`+diode_pending`) |
| 7 | M5 | 0.5625 | `allocate_stack_headroom:stage1_ref` | stage1_ref에 남은 0.9 V를 M3와 M5가 나눔 |
| 8 | M7 | 1.5000 | `allocate_stack_headroom:stage2` | |
| 9 | (검증) stage1_out | | | 0.9172 + 0.9 + 0.5625 = 2.3797 → **ValueError** |

세션41 기록(2.60 V)과 값이 다른 이유는 그 뒤 B15/B16 등으로 개별 수치가 바뀌었기 때문이다. 깨지는 자리와 구조는 그대로다.

다른 3개 회로의 현재 상태(같은 복제본, 하네스):
* `folded_cascode`: 사이징 성공.
* `current_reuse_telescopic_ota`: 사이징 성공.
* `nmcnr_amplifier`: 같은 계열의 실패다. 메시지는 `'stage2_diode_ref' 그룹(예산 1.5V, 미해결 ['M203']): 스택 예산 1.5V 중 0.525V를 배정할 곳이 없다 ... 구간: [M203∈[0.6375,0.975]]`이고, 모든 theta 격자점이 infeasible이다. compensation이 고른 M201 vds 0.3이 확정값으로 들어가는 바람에 diode M203이 1.5 V를 혼자 받아야 하는 상황이다. I-C11의 nmcnr 몫이 이것이다.

## 3. 근본 원인

### 원인 A (확정, 실측): compensation이 탐색으로 고른 VDS를 KVL과 무관한 확정값으로 쓴다

* `optimize_multistage()`는 stage 소자의 VDS를 objective(power)의 **탐색 변수**로 다룬다. 즉 이 값은 물리 제약이 아니다. 그런데 `_evaluate()` 8301행은 이 값을 `set_device_vds(..., "compensation:stage{i}")`로 확정값처럼 기입한다.
* 탐색 상한(cap)은 `reserved_vds_for_other_stack_members()`가 정한다. 이 함수는 같은 컬럼의 다른 멤버를 `metric_stage_budget` 고정 vds나 `min_vds_by_role` 하한으로만 예약한다. M4처럼 `vds_match_vgs_of`로 VSG(M6)=0.917 V에 묶인 값은 알지 못한다. 그래서 M4 자리에 `_feed_vds_fallback`의 cascode 하한 0.2 V를 예약하고, cap = 1.8−0.2(M4)−0.2(M5) = 1.4 V가 되어 0.9 V가 통과한다. 이 cap 값은 함수 본문과 spec `min_vds_by_role={"cascode":0.2,"tail":0.2}`로 계산했고, 실행 중에 계측해 찍지는 않았다.
* cap은 부등식이다. 정확히 고쳐도 KVL 등식(합 = vdd)을 보장하지 못한다.

### 원인 B (확정, 실측): 노드를 공유하는 두 branch 중 한쪽에 slack이 없다

* stage1_ref(VDD-M3-D3-M1-CS-M5-GND)와 stage1_out(VDD-M4-O1-M2-CS-M5-GND)는 노드 CS, 즉 VDS(M5)를 공유한다.
* `stage1_out`의 멤버 M4(vds_match)와 M2(compensation)는 헤드룸 단계 전에 이미 값이 정해져 있다. 그래서 이 그룹은 배분을 거치지 않고 검증만 받는다(7196~7198행). 공통 항인 M5는 다른 그룹(stage1_ref)의 배분기가 정한다. 결과적으로 세 값의 합이 vdd가 되는지는 우연에 달려 있다.
* 물리적으로 VDS(M2) = V(O1) − V(CS)는 노드 전압에서 나오는 종속값이다. 이 branch에서 slack 역할을 해야 하는 것은 M2다.

### 원인 C (확정, 반사실 실험으로 드러남): shared-gate 미러 쌍의 VGS 동일성이 강제되지 않는다

* M3(diode, gate=drain=D3, source=vdd)와 M4(gate=D3, source=vdd)는 gate 넷과 source 넷이 같으므로 VSG(M3)=VSG(M4)다. connectivity만으로 나오는 사실이다. 또 M3는 diode이므로 VSD(M3)=VSG(M3)다.
* 엔진은 두 소자의 gm_id를 서로 다른 경로로 정한다.
  * M4: feed(`L_mirror_M3`, `gm_id_role=matching`, `gm_id_min=8`)가 정한다. 이때 VSG(M4)≈1.22 V(L 0.79 µm)다.
  * M3: B16(`apply_diode_self_consistent_gm_id`)이 배분기가 준 vds에서 역산한다.
  * 두 경로는 서로를 모른다.
* 기존 matching pair gm_id 검사(`_evaluate` 8849행 근방)는 두 vds가 **같을 때만** 동작한다. vds가 다르면 VGS 불일치가 걸리지 않고 통과한다(아래 F1-only 결과가 그 예다).
* nmcnr은 같은 패턴(diode M203 / 파트너 M204)에 `gm_id_match_vgs_of: M203`을 선언해서 이 문제를 피했다. F1 실험에서 M203 gm_id 21.70, M204 21.72로 일치했다. two_stage에는 이 선언이 없다.

### 반사실 실험 (monkeypatch, 저장소 미수정)

| 실험 | 내용 | 결과 |
|---|---|---|
| CF-balanced | VSD(M3)=VSD(M4)=VSG(M6), M1=M2=vdd−VSG(M6)−0.2, M5=0.2로 강제 | KVL은 닫힘. 그러나 원인 C 검사에서 실패: `matching pair (M3,M4) ... gm_id_M3=17.3387, gm_id_M4=8` |
| CF-Ha | VSD(M3)=VSG at M4 gm_id 8(diode 자기일관), M1=vdd−VSD(M3)−0.2, M2=vdd−VSG(M6)−0.2, M5=0.2, M1/M2 W는 compensation 값 유지 | **완주**. gain_db 61.40, power 251.7 µA, area 520 µm², mismatch 0.366 mV. M3 vds 1.2228 / M4 0.9172라 미러 VSD 차가 0.31 V(systematic offset). W를 vds별로 다시 계산하면 `assign_finger_geometry`가 `stack M1 ... finger_w 후보 없음`으로 실패(diff pair는 W가 같아야 함) |
| CF-Hb | VSG(M3)=VSG(M4)=VSG(M6), M4 gm_id를 그 VSG에서 역산 | **완주**. gain_db 61.20, power 251.7 µA, area 785 µm²(M3/M4 gm_id 17.34, W 170 µm) |
| F1-only(일반형, 4절) | compensation vds가 충돌하면 slack으로 강등, 선언은 그대로 | **완주**. gain_db 57.22, area 612. 단 M3 gm_id 17.25 / W 119.6 µm, M4 gm_id 8 / W 2.74 µm. 같은 VSG(0.9375 V)를 공유해야 하는 쌍이 다른 VGS로 사이징됨(원인 C가 조용히 통과). **이 해는 받으면 안 된다** |
| F1 + `M3.vds_match_vgs_of: M4`(Ha 선언 흉내) | | 모든 격자점 infeasible. `stack_kvl_vgs_limit()`이 M4 gm_id 탐색에 vgs_max = 1.8−0.9(M1의 compensation **임시** vds)−0.2 = 0.70 V를 걸어 42점이 탈락하고, 나머지는 gain 53.3 < 57. F1을 `stack_kvl_vgs_limit()`에도 반영해야 한다(F1b) |

H-b에서 L별 gm_id(VSG(M6)=0.9172 V, pmos LUT): L 0.15 µm 7.62(gm_id_min 8 위반), 0.34 µm 16.26, 0.79 µm 17.34, 4 µm 17.26. 비교용으로 gm_id 8에서의 VSG는 0.34 µm 1.161 V, 0.79 µm 1.223 V다.

## 4. 수정안 (일반형: 회로·소자 이름을 쓰지 않고 선언·connectivity·`_vds_source`만 사용)

### F1 (엔진, 필수): compensation VDS를 임시값으로 보고, KVL과 충돌하면 그 그룹의 slack으로 쓴다

* vds 결정의 권위 순서를 정한다: 물리 제약(`vds_match_vgs_of`, `same_as_device`, diode 자기일관) > 선언(`metric_stage_budget` vds) > compensation 임시값 > 배분기.
* 그룹의 KVL 등식이나 배분기 실행가능성이 compensation 임시값 때문에 깨질 때만, 그 멤버를 미확정으로 되돌린다.
  * 남은 미확정 값-그룹이 그것 하나뿐이면 vds = vdd − Σrefs − Σ나머지로 정한다.
  * 미확정이 여럿이면 기존 `allocate_stack_headroom`에 넘긴다.
  * 결과가 role `min_vds`보다 작으면 명시적 ValueError를 낸다. 조용히 우회하지 않는다.
* 강등된 소자는 L·gm_id·ID·W를 compensation 값으로 유지하고 gds만 새 vds에서 다시 계산한다. W까지 다시 계산하면 offset 매칭쌍의 W가 갈라져 finger 배치가 실패한다(실측).
* 바뀌는 함수(대략):
  * `_hr_resolve_vertical_group`(7088~): 강등 helper `_hr_demote_provisional_vds(env, vsid, members)` 신설(~40줄), 호출 2곳(검증 분기·배분기 실패 분기 ~10줄). 단일 slack 배정은 별도 분기로 둔다(~15줄). 실측에서 singleton thin-role 우회(`_thin_singleton`)를 타면 `ideal_sources` 정당화 실패로 거부됐기 때문이다.
  * `stack_kvl_vgs_limit`(1668~): compensation 임시 vds를 고정항이 아니라 role `min_vds`로 취급한다(~10줄, F1b). F2-Ha를 택할 때만 필수다.
  * `reserved_vds_for_other_stack_members`(6607~): 선택 사항이다. `vds_match_vgs_of` 멤버를 참조 VGS로 예약하면 탐색이 처음부터 실행 가능한 VDS를 고른다. 등식은 F1이 보장하므로 없어도 닫힌다. 참조 VGS가 compensation의 다른 stage에 의존하므로 2-pass가 필요하다(~20줄).
  * 합계 약 65~95줄.
* 일반형 monkeypatch(`demote_exp.py`) 측정 결과:
  * `folded_cascode`: FIX=0/1의 sizing sha256 동일(`3b935978...`), 강등 0회 / 호출 5,200회.
  * `current_reuse_telescopic_ota`(파일럿, SLSQP 3 start): FIX=0/1의 sizing sha256 동일(`54faa21b3c6c...`), 강등 0회 / 호출 35,664회, metrics도 동일(gain_db 61.557, power 231.17 µA 등).
  * `nmcnr_amplifier`: 실패하던 실행이 **완주**한다. 강등 1회(`stage2_diode_ref:M201`)로 M201 vds가 0.3에서 1.1625(= 1.8 − M203 0.6375)가 됐다. I-C11의 nmcnr 몫도 원인 A·B와 같다는 뜻이다. 결과 metrics(pm 44.1°, cmrr 4.6 dB, power 4.04 mA)는 따로 봐야 하며 이 진단 범위 밖이다.
  * `two_stage_ota`: 완주한다(강등 91회 = stage1_out:M2 49 + stage1_ref:M1 42). 다만 원인 C 때문에 F1만으로는 물리적으로 틀린 해가 나오므로 F2가 필요하다.

### F2 (원인 C, 필수, 방향은 **[사용자 확인 필요]**)

connectivity에서 일반적으로 유도되는 사실이 있다. 같은 kind이고 gate 넷과 source 넷이 같은 두 소자는 VGS가 같다. 그중 하나가 diode(gate=drain)면 그 VDS가 곧 그 VGS다. 이 등식을 강제하는 방향은 아래 셋 중 하나다. 셋 다 이름 없이 구현할 수 있다.

* **F2-Ha**: 비 diode 파트너의 gm_id(feed·role)를 권위로 두고, diode vds := VGS(파트너)로 정한다. CF-Ha에서 gain 61.40이었고 M3/M4 VSD 차 0.31 V(systematic offset)가 남는다. F1b가 필요하다.
* **F2-Hb**: diode의 VGS를 다른 등식으로 정하고 파트너 gm_id를 역산한다. 이 회로에서는 미러 출력 노드가 다음 단 게이트이므로 그 등식은 VSG(M3)=VSG(M6), 즉 systematic offset 0 조건이다. CF-Hb에서 gain 61.20, area 785 µm²였다. `gm_id_min=8`은 L≥0.34 µm에서만 만족한다. 기존 `L_mirror_M3`의 `gm_id_role=matching` 의도(강반전 쪽)를 사실상 덮어쓴다.
* **F2-nmcnr 선례**: diode vds는 배분기 window에서 받고, 파트너 gm_id는 `gm_id_match_vgs_of`로 diode VGS에서 역산한다. 엔진 변경 없이 topology에 `M4.gm_id_match_vgs_of: M3`만 선언하면 된다. 다만 M4는 feed의 `gm_id_role`·`gm_id_min`도 받으므로 둘 사이의 우선순위를 정해야 한다.

다음은 회로 해석이라 결론을 내리지 않았다. 모두 **[사용자 확인 필요]**다.
* systematic offset 0을 요구하는지, M3/M4를 강반전 matching으로 둘지(→ F2 방향).
* offset 매칭 diff pair인 M1/M2의 VDS가 서로 달라도 되는지(실측 F1 0.2 vs 0.22, CF-Ha 0.377 vs 0.683).
* CS 노드 전압(VDS(M5))을 tail 하한으로 둘지, spec에 없는 입력 공통모드에서 유도할지.

방향이 정해진 뒤의 엔진 F2 구현:
* 공유 gate/source 쌍을 넷으로 판정하는 helper(~25줄).
* `vds_match_of` pre-pass에 자동 등록(Ha) 또는 `gm_id_match_vgs_of` 2차 pass에 자동 등록(Hb·nmcnr 방식), 각 ~10줄.
* matching pair 검사(8849행 근방)를 "vds가 같을 때만"에서 "공유 gate/source면 VGS 차 ≤ tol"로 넓힌다(~15줄). 조용한 통과를 막기 위해서다.

## 5. 필요한 test와 기대값의 독립 출처

| # | test | 기대값 | 독립 출처 |
|---|---|---|---|
| T1 | two_stage_ota 전 vertical 그룹에서 Σvds(멤버)+Σvds(`budget_reference_device`)가 vdd와 같은지(상대 1e-9) | 1.8 V | KVL 정의. 그룹·ref는 test가 topology 선언에서 직접 읽음(피검 함수 미사용) |
| T2 | 2소자 컬럼 픽스처(compensation 소자 + diode, 해석식 toy LUT)에서 slack vds = vdd − VGS_diode | 해석식(예: 제곱법칙 VGS=Vth+sqrt(2ID/(k·W/L)))으로 손계산한 숫자 | 손계산 |
| T3 | 넷으로 찾은 공유 gate·source 쌍 전부에서 \|VGS_a−VGS_b\| ≤ tol(각 소자 gm_id/L/vds/vsb → `vgs_for_gm_id`) | 0 | connectivity 사실. F1-only 해(M3 0.9375 V vs M4 ≈1.22 V)로 **red** 재현 가능 |
| T4 | 무동작: folded·파일럿에서 base와 병합본의 sizing 직렬화 sha256이 같고 강등 0회 | base 해시 | base 실행 산출물(00-common §11 절차, auditor) |
| T5 | nmcnr `stage2_diode_ref`의 slack 소자 vds = vdd − vds(diode) | 1.8 − 0.6375 = 1.1625 V(현재 격자·LUT) | 손계산. diode 구간 하한은 `diode_vds_window`로 따로 구하거나 auditor가 실측 |
| T6 | slack < min_vds이면 명시적 ValueError | ValueError | 계약(우회 금지) |
| 기존 | strict xfail `test_s051_optimize_full_circuit_budget`·`test_s054_section`·`test_s157_M1`이 XPASS→FAIL로 해소를 알림. 그때 xfail을 풀고 `_known_limitation` 3건을 삭제 | | 승인 `20260922-c9-ic11-split`·`20260923-c9-v4-exempt`·`20260923-ts2-pytest-split`의 Phase 4 재검토 줄, 백로그 B9·B12 |

판정 기준은 등식(KVL, VGS 동일)으로만 둔다. gain_db ≥ 57 충족 여부(F1-only 57.22, CF-Ha 61.40, CF-Hb 61.20)는 방향이 정해진 뒤 auditor가 측정한다.

## 6. 정리

* 실패 위치: `_hr_verify_group_kvl_sum` ← `_hr_resolve_vertical_group('stage1_out')`. M4 0.9172(VSG(M6)) + M2 0.9(compensation 탐색값) + M5 0.5625(stage1_ref 배분) = 2.3797 V.
* 원인:
  * (A) compensation VDS를 확정값으로 쓰고, 그 cap 계산이 `vds_match_vgs_of`를 모른다.
  * (B) 노드 CS를 공유하는 두 branch 중 `stage1_out`에 slack이 없다.
  * (C) diode 미러 쌍의 VGS 동일성이 강제되지 않는다. A·B만 고치면 C가 조용히 통과한다.
* nmcnr `stage2_diode_ref` 실패도 A·B와 같은 원인이고, F1로 완주한다.
* 수정안은 F1(엔진 일반형, 약 65~95줄)과 F2(VGS 동일성, 방향은 사용자 결정)다. folded와 파일럿에서 F1의 무동작을 측정했다(해시 동일, 강등 0회).
