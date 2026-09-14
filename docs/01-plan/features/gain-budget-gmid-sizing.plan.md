---
template: plan
version: 4.48
---

# gain-budget-gmid-sizing Planning Document

> **Summary**: `analog-gmid-design` skill의 gm/ID 사이징 엔진(`sizing_recipe.py`)을
> "L → VDS(헤드룸) → gm_id" 순서의 role-라벨 기반 방식에서, "stage 분할 → stage별 gain
> 배분 → 그 gain에서 gm_id를 직접 역산 → 그 이후에 VDS/헤드룸을 자기일관되게 해석"하는
> gain-budget-first 방식으로 근본 재설계한다. topology.json은 순수 connectivity 전용으로
> 되돌리고, 사이징 방법론은 새 `<name>.sizing_spec.json`으로 분리한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill)
> **Author**: Claude Code
> **Date**: 2026-09-04
> **Status**: Draft — 사용자 승인 대기, 파일럿 회로(`current_reuse_telescopic_ota`) 1개로
> 먼저 증명 후 나머지 3개 토폴로지 이관

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | `current_reuse_telescopic_ota`의 SPICE 트랜지언트 폐루프 검증을 시도하다가, 헤드룸(VDS) 배정이 diode-connected 소자(gate=drain, Vgs=Vds가 물리적으로 강제)의 실제 필요 Vgs를 무시하고 role 라벨 기반 상수(기본 0.2V)를 그대로 배정한다는 걸 실측으로 확인했다(16개 diode-connected 소자 중 최대 1.02V 오차 — M36a/M36b는 실제 1.32V 필요한데 0.3V만 할당돼 물리적으로 불가능). 원인을 추적하니 국소 버그가 아니라 파이프라인 순서 자체의 문제였다: 현재 아키텍처는 `L → VDS(헤드룸) → gm_id` 순서로 사이징하는데(`optimize_full_circuit_budget()`, `sizing_recipe.py:5679-5687`), VDS가 gm_id보다 먼저, 그것도 role 라벨 기반 상수/근사식으로 확정되기 때문에 Vgs=Vds 결합 제약이 있는 소자는 애초에 자기일관된 답을 낼 수 없다. |
| **Solution** | gm/ID sizing 방법론을 "stage를 정확히 나누고, 각 stage가 낼 gain을 먼저 배분한 뒤, 그 gain에서 유도되는 gm_id로 사이징한다 — output stage에만 driving capability(slew rate/CL)를 추가로 얹는다"는 원칙으로 baseline부터 재설계한다. VDS/헤드룸은 gm_id가 정해진 *이후*에, connectivity(gate==drain)로 diode-connected 여부를 직접 판정해 해석하므로, 이번에 발견한 버그가 재설계의 자연스러운 부산물로 해소된다. **그리고 이걸로 끝내지 않는다(2026-09-04 확정, §3.1 요구사항 6) — 사이징된 모든 소자의 전압/전류 관계가 실제로 KVL/KCL을 만족하는지 전체회로 단위로 검증하는 `verify_node_voltage_consistency()`/`cross_check_with_spice()` 게이트(§7.5)를 파이프라인에 상시 내장한다.** diode-connected 자기일관성은 이 검증기가 잡아내는 여러 위반 패턴 중 하나일 뿐이다. |
| **Function/UX Effect** | AI/사용자가 새 회로를 사이징할 때 "이 stage가 몇 dB를 낼지"를 명시적으로 배분하는 게 1급 입력이 되고, 개별 소자의 gm_id/L을 role 휴리스틱으로 따로 추측할 필요가 없어진다. 헤드룸도 diode-connected 소자마다 실측 SPICE와 부합하는 값이 나와, 이후 SPICE 폐루프 검증(트랜지언트 포함)이 실제로 수렴할 수 있게 된다. |
| **Core Value** | 물리적 정확성(physical correctness) — "gm/ID sizing은 회로의 물리적 topology 연결을 보지 않고는 할 수 없다"는 이번 세션 핵심 지적을 아키텍처 차원에서 반영한다. 재사용 가능한 계층(LUT 인터페이스, connectivity, post-sizing 레이아웃, 사후검증 metric)은 그대로 두고 사이징 "결정 순서"만 근본적으로 바꾸는 최소침습 재설계다. `.ai/context.md` 세션6~44 전체 자산화(v2.0, §1.4)로 확인됨: 이 방향은 새 발명이 아니라 세션38이 합의만 하고 못 끝낸 "DC bias vs AC amplification 도메인 분리" 아키텍처의 실제 완성이며, 헤드룸 재설계도 기존 `resolve_feed_vds()`/`_resolve_vertical_group()` 인프라를 재사용하는 쪽으로 한층 더 최소침습화됐다. |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | gm/ID sizing 엔진이 VDS(헤드룸)를 gm_id보다 먼저, role 라벨 기반 상수로 확정하는 구조라 diode-connected 소자(Vgs=Vds 물리적 강제)에서 최대 1.02V 오차가 나고, 이게 SPICE 폐루프 DC 동작점을 출력단 레일 고정으로 발산시킨다(2026-09-04 세션, SPICE 트랜지언트 검증 중 발견) |
| **WHO** | `analog-gmid-design` skill로 아날로그 IC를 sizing하는 (fresh) agent 세션들 + 사용자(hoseung.lee) |
| **RISK** | gm_id를 gain에서 직접 역산하는 신규 함수(§2)가 캐스코드+입력 소자의 2변수 결합을 제대로 못 풀면 회귀 위험. `known-incidents.md` "사고4"(단별 이득배분은 탐색이 맞다)와의 철학적 충돌을 잘못 봉합하면 예전에 이미 폐기된 접근을 반복하는 셈 — 이번 세션 사용자 확정으로 "배분 자체는 여전히 탐색/사용자 지정, 배분 이후 gain→gm_id 역산 한 단계만 결정론화"로 경계를 명확히 함 |
| **SUCCESS** | (0) ★최우선: `verify_node_voltage_consistency(ctx)`가 사이징된 **전체회로**(51소자, diode-connected뿐 아니라)에서 KVL/KCL/VGS Violation 0건 — 이게 이번 재설계의 근본 동기(§3.1 요구사항 6). (1) 그 부분집합으로, `_solve_diode_connected_vgs_fixed_point()`가 16개 diode-connected 소자 전부에서 `vgs_for_gm_id(gm_id,L,vds*,vs)==vds*` 자기일관점에 수렴(현재 오차 0.05~1.02V → 0). (2) `current_reuse_telescopic_ota`를 새 엔진으로 재사이징해도 기존 constraints(gain≥54dB, cmrr/psrr/mismatch/classab)를 여전히 만족. (3) `cross_check_with_spice()`(sky130 트랜지스터 레벨 SPICE `.op`)이 rail-lock 없이 수렴하고 (0)의 LUT 기반 예측과 일치 |
| **SCOPE** | 이번 계획: JSON 스키마 설계 + 신규 사이징 알고리즘 설계 + 헤드룸 해석기 재설계 + 파일럿 회로(`current_reuse_telescopic_ota`) 1개 이관·검증. 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/two_stage_ota) 이관은 파일럿 검증 후 별도 작업으로 이연 |

---

## 0. 이어받을 지점 (★ 2026-09-08 기준, 새 세션은 여기부터 읽는다) → 이력 문서

> **(v4.47) 2026-09-08 스냅샷은 이력 문서로 이동했다** -- [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md) §0.
> **현재 착수 지점: §13.6 전체 수정 순서 + §14.8 -- Phase 0.5(역할 분리 인프라)부터.** Phase 6·7은 **§15(graph 기반 gain-budget-first)**가 대체한다 -- gain-budget-first는 폐기되지 않았고 graph가 그 기반이다. 남은 사용자 결정은 §14.9 끝(D6·D7·D8, 해당 Phase 착수 조건).
> ⚠️ 이 절은 계획서 재작성(현행 계획을 앞으로 모으기)에서 다시 쓴다.

## 1. Overview

### 1.1 Purpose

gm/ID 사이징 엔진의 소자별 결정 순서를 `L → VDS(헤드룸) → gm_id`에서
`stage 분할(connectivity) → stage별 gain 배분(spec) → gm_id 역산(LUT) → VDS/헤드룸 해석`으로
뒤집는다. 이렇게 하면 (a) diode-connected 등 Vgs=Vds 물리 제약이 있는 소자도 자기일관된 헤드룸을
받고, (b) 각 stage의 gm_id가 role 휴리스틱 추측이 아니라 실제 목표 gain에서 결정론적으로 유도되며,
(c) output stage에만 driving capability(slew rate/CL) 제약을 추가로 얹는 구조가 스키마 차원에서
명시적으로 드러난다.

### 1.2 Background

2026-09-04 세션에서 `current_reuse_telescopic_ota`의 class-AB 출력단 Up/Down settling 대칭성을
sky130 트랜지스터 레벨 SPICE 트랜지언트로 검증하려 했다. 51소자 전체 폐루프 `.op`을 시도하는
과정에서 출력이 VDD 레일에 고정(rail-lock)되는 걸 발견했고, CMFB 루프를 열어도 동일하게
재현돼 CMFB 부호 문제가 아니라 바이어스 체인 자체의 문제임을 확인했다. 근본원인을 추적한 결과:

1. `topology.json`의 `ideal_sources.Iref.value_amp=1.2uA`는 순수 선언 메타데이터일 뿐 실제
   사이징 엔진이 읽지 않는다(`sizing_recipe.py:2824`) — 부차적 수정.
2. **핵심 문제**: diode-connected 기준소자(예: M18_bg, gate=drain=Vbias1)는 물리적으로
   Vgs=Vds일 수밖에 없는데, 저장된 `vds`(헤드룸 예산, 예: 0.2V)와 실제 sky130 LUT/SPICE가
   그 gm_id에서 요구하는 실제 Vgs(예: 0.99V)가 전혀 다르다. 16개 diode-connected 소자 전수
   조사 결과 오차가 0.05V~1.02V였다(가장 심한 M36a/M36b: 필요 1.32V, 할당 0.3V).
3. 근본원인은 `allocate_stack_headroom()`/`HeadroomPolicy`가 VDS를 gm_id보다 **먼저**
   role 라벨(`cascode`/`diode_reference`/`mirror`/...) 기반 상수로 확정하는 파이프라인
   순서 자체에 있다(`optimize_full_circuit_budget()` docstring, `sizing_recipe.py:5679-5687`).

사용자가 이를 "gm/ID sizing은 물리적 topology 연결을 보지 않고는 할 수 없다"는 더 근본적인
설계 원칙 문제로 재규정했고, "stage를 먼저 나누고 gain을 배분한 뒤 gm_id를 유도한다"는 방향으로
baseline부터 재설계하기로 확정했다.

### 1.3 Related Documents

- `.ai/context.md` "세션44 (계속)"/"세션44 (계속 2)" — diode-connected 헤드룸 버그 발견 경위
- `skills/analog-gmid-design/references/gm-id-methodology.md` §2.5/§4/§6.4/§6.7 — 기존
  "GBW/PM→gm, gain은 사후 readback" 방향의 근거
- `skills/analog-gmid-design/references/gm-id-methodology.md` §13(§13.1/§13.2/§13.3/§13.7
  특히) — 이 프로젝트 엔진 실전 운영에서 나온 고유 발견, §7.2 알고리즘 개정의 직접 근거
  (2026-09-04 §1.4 추가)
- `skills/analog-gmid-design/references/known-incidents.md` "사고4" — 단별 이득배분을
  닫힌 식으로 강제하려다 탐색+제약조건으로 정정한 전례(이번 재설계와의 경계 구분 필요)
- `skills/analog-gmid-design/references/known-incidents.md` "사고10/16/19/21/22/23/24" —
  오늘 발견한 헤드룸 버그와 같은 클래스의 5개 선례 + §7.3 개정이 재사용하는 기존 인프라
  (`resolve_feed_vds()`/`_resolve_vertical_group()`)의 출처, §8.4 위험(사고16) 근거
  (2026-09-04 §1.4 추가)
- `skills/analog-gmid-design/references/topology-fn-derivation-guide.md` — 기존 GBW/PM→gm
  reverse-derivation 절차(compensation 방향이 반대가 됨에 따라 참고용으로 남김)
- `docs/01-plan/features/analog-topology-json-library.plan.md` — topology.json을
  "사이징과 무관한 connectivity만" 담자는 원래 설계 의도(`_TEMPLATE.topology.json` §schema_note) —
  이번 재설계가 그 원칙을 device_roles/sizing_roles/compensation까지 완성한다
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json` —
  파일럿 회로의 현재 connectivity + (폐기 대상) device_roles/sizing_roles/compensation

### 1.4 이 재설계의 역사적 선례 (2026-09-04 `.ai/context.md` 세션6~44 전체 자산화로 발견) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

## 2. Scope

### 2.1 In Scope

- [ ] 새 JSON 스키마 설계: `<name>.sizing_spec.json`(§7.1) —
      `stages[].devices.{input,cascode,load,tail}`, `global_spec.constraints`(총 gain·cmrr·psrr·
      mismatch 문턱), `stages[].driving_spec`(output 전용), `compensation`(방향 반전),
      `headroom.policy`, `bias_devices`(stage 밖 diode-reference/mirror 소자).
      **`gain_budget_db`는 입력이 아니라 출력**(v3.1) — 예외 경로로 `gain_budget_db_override`만 둠
- [ ] `topology.json`을 순수 connectivity 전용으로 되돌림 — `device_roles`/`sizing_roles`/
      `compensation` 필드 제거(새 `sizing_spec.json`으로 이관)
- [ ] 신규 함수 구현(`sizing_recipe.py`, §7.2/§7.3 — 2026-09-04 §1.4 자산화 반영으로 축소됨):
  - [ ] `_solve_diode_connected_vgs_fixed_point(gm_id, L, vs, lut)` — 이번 세션 스크래치패드
        `node_dc_propagate.py`에서 프로토타입 검증 완료, 그대로 이식. connectivity
        (`gate==drain`) 기반 판정, §7.2 stage 사이징 직후 `ctx.sized[name]["vds"]`에 기입해
        기존 `resolve_feed_vds()` 우선순위①(이미 있으면 존중)로 자연스럽게 보호되게 함
  - [ ] `gm_id_for_gm_gds_ratio(target_ratio, L, vds, vs)` — `gm_id_for_vgs()`(:536)와 동일
        패턴의 O(1) 역보간, gm/gds 축 신규
  - [ ] `resolve_stage_sizing(stage_spec, ID, luts)` — stage 알고리즘(§7.2, cascode=`role="gain"`
        /load=`role="load"` 구분 포함) 구현체
  - [ ] ~~`_resolve_device_headroom(device, ctx)`(`allocate_stack_headroom()`/`HeadroomPolicy`
        대체)~~ — **취소(§7.3 개정)**: `resolve_feed_vds()`/`_resolve_vertical_group()`가
        이미 구현돼 있어(사고22/24) 전면 교체 대신 위 diode-connected solver를 그 우선순위
        체인 앞단에 끼워넣는 것으로 충분함이 드러남
  - [ ] `solve_compensation_for_gbw_pm(stage_gms, targets)` — 기존 `topology_fn`(GBW/PM→gm)의
        역방향(gm들→Cc/Rz). `device_roles.vds_match_vgs_of`/`gm_id_match_vgs_of`(사고21,
        이미 구현됨)를 stage 간 결합 소자에 그대로 재사용 — 새 결합 메커니즘 발명하지 않음
  - [ ] **★ `verify_node_voltage_consistency(ctx)`**(§7.5) — 전체 netlist 노드전압 재구성 +
        상호모순/VGS 불일치 검사. 이번 재설계의 가장 근본적인 요구사항(§3.1 요구사항 6)의
        직접 구현체 — diode-connected뿐 아니라 **모든** 소자의 V/I 관계를 검증
  - [ ] **★ `cross_check_with_spice(instance_data)`**(§7.5) — sky130 SPICE `.op` 독립 교차검증,
        스크래치패드 `build_transient_netlist.py`를 skill asset으로 정식 편입
  - [ ] `L_candidates_product()` + `resolve_stage_sizing()`의 L outer-loop(§7.6 (3)) —
        cascode/load/tail의 L을 면적 오름차순으로 전수 스캔하며 각 L_combo에서 §7.2를
        결정론적으로 실행, `extra_feasible`(§13.5 기존 패턴)로 cmrr/psrr/mismatch 판정
  - [ ] **`sweep_area_power_pareto(sizing_spec, luts) -> ParetoReport`**(§7.9, v3.4) — 면적
        예산 미선언 시 전력-면적 Pareto front를 뽑아 제시하고 정지(엔진이 예산을 지어내지
        않는다). 선택 결과는 `global_spec.constraints`의 `area_um2`로 기록
  - [ ] ~~`make_cmrr_psrr_feasibility_check(...)`~~ — **삭제(v4.4)**. `make_matching_
        feasibility_check()`와 "동일 패턴"이 **원리적으로 불가능**함이 실측으로 확인됐다:
        `smallsignal_ratio_db`는 `_full_circuit_devices()`가 전 소자를 요구해 stage 사이징
        도중에는 `KeyError`다(§7.6 B2 해소 참고)
  - [ ] **`make_stage_local_check(metrics, constraints, grp, spec)`**(§7.6, v4.4) — T1/T2
        metric만 골라 `extra_feasible` 콜백으로 변환(기존 `make_matching_feasibility_check()`
        를 일반화). T3가 섞여 들어오면 **선언 시점에 거부**한다
  - [ ] **`check_global_gates(ctx, metrics, constraints) -> GateReport`**(§7.6, v4.4) — T3
        전용 전역 게이트. 전 소자 사이징 완료 후 1회 실행(측정 0.72 ms), 위반 metric과
        여유량을 함께 반환해 §7.6(4) 승격 판단에 쓴다
  - [ ] **`diagnose_sizing_dof(sizing_spec, topology) -> DofReport`**(§7.8) — 사이징 시작
        전에 "목표 개수 대비 실제 자유도가 충분한가"를 스키마+connectivity만으로 판정
        (`ok`/`underdetermined`/`overconstrained`), `overconstrained`면 어느 목표끼리
        같은 자유도를 다투는지 명시 보고하고 반복을 아예 시작하지 않음(사고19 재발 방지)
  - [x] **(2026-09-07 완료)** `_hr_vfind()`/`_hr_thin_singleton_ideal_source_check()`/
        `_hr_fold_group_check()`/`_hr_sum_ref_vds()`/`_hr_verify_group_kvl_sum()`/
        `_hr_resolve_vertical_group()` — 2중 중첩 클로저 6개를 모듈 레벨로 추출(§8.4)
  - [ ] **`compute_metric(metric_spec, ctx)` 경유 gain 제약**(§7.9, v4.0) — `_METRICS_REGISTRY`
        위임. `∂gain/∂gm_id_i`는 LUT 위 수치미분. 회로별 폐형식을 옵티마이저 본문에서 제거
  - [ ] **`solve_allocation_dp(stage_tables, gain_target, area_budget) -> Allocation`**(§7.9,
        v4.2) — stage별 gm_id 배분의 **정확 해법**. 분리성을 이용한 자원배분 DP라 기울기를
        쓰지 않아 비볼록(A11)에 영향받지 않는다. 프로토타입·근거:
        `tests/probe_allocation_solvers.py`. Pareto front(§7.9 v3.4)도 같은 DP의 비지배
        집합에서 **한 번의 전파로** 나온다
  - [ ] **`set_device_vds(ctx, name, value, source)`**(§7.3, v4.3) — vds 기입의 **유일한**
        경로. diode 소자면 고정점 해와 일치하는지 검사해 어긋나면 즉시 실패, `_vds_source`
        태그 기록(B13 추적성 동시 해결). 기존 7개 기입 지점을 전부 이 함수로 치환하고
        원시 대입 잔존 여부를 grep 테스트로 강제
  - [ ] **`load_sizing_spec(path) -> SizingSpec`**(§7.1, v4.0) — 스키마 검증기. 미지 필드 거부,
        `topology_ref` 정합 확인, `metrics[].type`이 `_METRICS_REGISTRY`에 있는지 확인,
        `schema_version` 마이그레이션. 선언만 되고 아무도 안 읽는 필드를 **정적으로 잡는다**
        (C5 재발 방지 — `settling_time_ns`가 실제로 그 상태였다)
  - [ ] **`resolve_headroom(topology_spec, ctx)`**(§8.4) — 위 `_hr_*` 6개를 묶는 독립 harness.
        추출이 끝났으므로 이제 구현 가능
- [ ] 파일럿 회로 이관: `current_reuse_telescopic_ota`를 새 스키마로 재작성, 새 엔진으로
      재사이징
- [ ] 회귀 검증: 기존 사후검증 metric(`gain_db`/`cmrr_estimate_db`/`psrr_estimate_db`/
      `mismatch_sigma_mV`/`classab_centering_dev_v`)이 기존 constraints를 여전히 만족하는지 확인
- [ ] **전체회로 물리 정합성 검증**(§7.5, diode-connected 16개 소자 포함하되 그것만이 아님):
      `verify_node_voltage_consistency()`가 Violation 0건 보고 — diode-connected 자기일관성
      (`vgs_for_gm_id(gm_id,L,vds*,vs)==vds*`)은 이 검증의 특수 케이스로 포함됨
- [ ] SPICE 폐루프 재검증: `cross_check_with_spice()`로 새 사이징 결과의 `.op` 수렴 확인
      (rail-lock 없음) → 원래 목표였던 class-AB Up/Down settling 트랜지언트 검증 재개

### 2.2 Out of Scope

- 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/two_stage_ota) 이관 — 파일럿 검증 후
  별도 작업
- `optimize_full_circuit_budget()`의 신/구 경로 강제 일괄 전환 — `sizing_spec` 유무로 분기,
  점진적 이관
- ~~gain 배분 자동 탐색 알고리즘 고도화~~ → **v3.1에서 In Scope로 이동**: 배분은
  §7.9 Phase 2의 root current 1-D 해찾기로 **유도**하는 것으로 확정됐다(별도 탐색 알고리즘이
  아니라 단조 함수의 해찾기라 구현 비용이 작다)
- 레이아웃/floorplan/euler 자동수정 계층 변경 — 전부 재사용, 무변경

---

## 3. Requirements

### 3.1 Functional Requirements

1. Stage 안에 input(들) + cascode(들)이 있는 경우(텔레스코픽류), `gain_budget_db` 하나에서
   input의 gm_id와 cascode의 (L, gm_id)를 함께 결정할 수 있어야 한다(사용자 확정: "동시 결정").
2. Output stage는 `driving_spec`(CL/slew-rate/settling-time)이 있으면 `ID_final = max(KCL ID,
   slew_rate_target * CL)`로 ID를 상향할 수 있어야 하고, 이 상향이 gain 배분 로직과 충돌하지
   않아야 한다.
3. 헤드룸 해석기는 `connectivity(device).gate == connectivity(device).drain`을 role 라벨보다
   우선하는 진실源으로 삼아야 한다.
4. **(v4.0 개정 — 인과 방향 확정)** 위상보상이 **먼저** 돈다: 스펙 `(CL, GBW, PM)`에서
   `(Cc, Rz, gm_1..gm_N)`을 **한 번에** 푼다(2단 Miller면 `gm_1 = 2π·GBW·Cc`, `gm_2 = Z·gm_1`).
   그 다음 `gm_id_i`가 **유일한 자유 축**이 되고 `ID_i = gm_i/gm_id_i`가 파생된다.
   ~~GBW/PM은 이미 정해진 stage gm들로부터 보상소자 값을 역산한다~~
   (사용자 확정: "gain이 주도").
5. **(v3.1 개정)** gain 배분은 **엔진이 유도한다** — 사용자는 총 gain 목표
   (`global_spec.constraints`의 `gain_db>=X`)만 주고, stage별 `gain_budget_db`는 §7.9 Phase 2가
   `A_i,max` 실측 + **`gm_id_i`를 변수로 한 해석해(KKT)+활성제약** 절차로 결정해 **출력**한다
   (v3.2 재정식화 — v3.1의 root-current 1-D 해찾기는 그 특수 케이스). `stages[].gain_budget_db_override`
   는 논문 재현 등 예외 경로로만 남긴다.
   ⚠️ **사고4와의 관계**: 사고4는 "논문에서 배분값을 **찾으려던** 것"을 "회로에서 도출하라"로
   정정한 것이었고, 당시 해법이 "탐색"이었다. v3.1은 그 도출을 **더 좁혀** 물리 상한(`A_i,max`)
   실측 기반의 결정론적 해찾기로 만든다 — 값을 사람이 지어내지 않는다는 사고4의 본질은 그대로다.
6. **★ 이번 재설계의 가장 근본적인 동기(사용자 확정, 2026-09-04) — 전체회로 물리 정합성
   검증**: 사이징된 **모든** 소자(diode-connected뿐 아니라)의 전압(VGS/VDS)·전류(ID) 관계가
   실제로 KVL/KCL을 만족하는지, 파이프라인 마지막에 **전체 netlist 단위로** 독립 검증하는
   단계가 있어야 한다 — 개별 vertical_stack_id/그룹 내부 KVL 합만 맞는지 보는 게 아니라
   (그건 이미 `allocate_stack_headroom()`의 assert가 함), 서로 다른 경로로 같은 net에
   도달하는 두 소자가 실제로 같은 전압을 예측하는지, 그리고 어떤 소자가 게이트로 받는
   내부 net의 실제 전압이 그 소자가 사이징될 때 가정한 VGS와 일치하는지까지 검증해야 한다.
   오늘 diode-connected 버그를 발견한 방식(§7.5 참고 — 레일에서부터 소자별 vds를 따라 전체
   netlist의 노드전압을 직접 재구성하고, 독립된 두 번째 solver(SPICE)로 교차검증) 자체가
   이 요구사항의 프로토타입이었다 — 이걸 **1회성 디버깅 스크립트가 아니라 파이프라인의
   상시 검증 게이트**로 승격하는 게 이번 재설계의 핵심 목적이다(diode-connected 헤드룸
   수정은 이 검증기가 잡아낸 여러 사례 중 하나일 뿐 전부가 아니다).

### 3.2 Non-Functional Requirements — 3대 기본 원칙 (★ 2026-09-07 사용자 확정, v3.0)

이번 재설계의 비기능 요구사항은 아래 셋뿐이며, 우선순위도 이 순서다.

**P1. 버그 free가 최우선 — 전면 재설계를 허용한다.**
v2.x까지 걸어두었던 "기존 재사용 계층의 함수 시그니처는 변경하지 않는다"는 제약은 사용자
확정으로 **폐기**한다. 기존 함수를 개선하거나 통째로 다시 설계하는 것을 막지 않는다 — 판단
기준은 "기존 코드를 얼마나 보존했나"가 아니라 **"물리적으로 옳은가, 조용한 실패가 구조적으로
불가능한가"**다.

> 이 제약이 실제로 설계를 비틀었던 두 사례(둘 다 이번 v3.0에서 바로잡는다):
> - **§7.3**: diode-connected 값을 "먼저 기입하면 `resolve_feed_vds()` 우선순위①이 지켜준다"는
>   **암묵적 순서 의존**으로 우회했다 — 그건 사고19/23이 당한 바로 그 취약성이다.
> - **§7.9**: gain 기여도 기반 가중 헤드룸 배분이 필요한데 `allocate_stack_headroom()`의
>   "남는 예산 균등분배"를 못 고쳐 **구현 자체가 불가능**한 모순 상태였다.

**P1-b. 우회(skip/예외)를 만들기 전에 타당성을 먼저 검토한다** (사용자 지시, 2026-09-08).

> "너는 항상 타당성을 따지지 않고 skip 로직을 만드는 경향이 있어. 그건 금지야."

검사를 통과시키는 가장 빠른 길이 `continue` / `except: pass` / 예외 목록이라 반사적으로 손이
가는데, 그 순간 **"검사가 잡아낸 진짜 결함"이 "검사의 예외"로 둔갑한다**. 우회를 쓰기 전에
세 가지를 먼저 답한다.

1. **이 대상이 실재하는가** — 그 필드/조건이 진짜 설계 입력인지 grep으로 확인한다.
2. **검사가 틀렸는가, 대상이 틀렸는가** — 대부분 후자다. 후자면 대상을 고친다.
3. **우회 없이 고칠 방법이 있는가.**

실제 사례(v4.17 작업 중): diode 자기일관성 검사를 배선했더니 self-test가 깨졌고,
`spec["known_sizing"]` 소자를 건너뛰는 규칙을 넣었다. 그런데 `known_sizing`은
**topology.json에 0건, 워크스페이스/spec 빌더에 0건**인 self-test 픽스처 전용 우회로였다 —
물리 검사를 테스트 편의로 무력화한 것이고, 정작 검사는 픽스처가 diode 소자에 불가능한 값
(`gm_id=12 @ vds=0.6`, 실제 요구값 21.275)을 시드하던 **기존 오류를 정확히 찾아낸 것**이었다.
정답은 skip이 아니라 픽스처의 vds를 물리적으로 일관된 값으로 바꾸는 것이었다.

이 원칙은 C5(게이트 사각)의 예방책이자 **★절대원칙(만들면 배선하라)의 짝**이다 -- 만들어
놓고 예외로 비켜가게 하면 배선하지 않은 것과 같다.

**P2. 효율성 — 재계산·중복 스캔을 구조적으로 막는다.**
같은 `(L, vds, vs, gm_id_grid)` 스캔이 호출부마다 반복되지 않도록 스캔 축을 함수 안으로
내리고(예: L축 내부화, §7.6/§7.10), 캐시 키는 **"그 함수가 실제로 읽는 모든 가변 상태"**
기준으로 잡는다(`lut-generation-checklist.md` §9의 CMFB MNA 캐싱 회귀가 근거 — `metric_spec`만
키로 썼다가 `ctx.sized` 변경을 놓쳐 잘못된 값을 반환했다).

**P3. 기지의 사고(사고1~24)는 구조적으로 재발 불가능해야 한다.**
"조심하겠다"가 아니라 **설계가 그 실수를 애초에 허용하지 않아야** 한다. §3.3의 C1~C10이 그
목록이며, 각 항목은 담당 설계 절과 방지 장치를 명시한다. 구현 완료 판정(§4.1)에 이 표의 모든
행이 방지 장치를 갖췄는지 확인하는 항목이 포함된다.

**부수 요구**: 신규/개선 함수는 §8.8 방침대로 `assets/tests/test_<module>.py`에서 검증한다.

### 3.3 기지 사고 재발 방지 설계 원칙 C1~C10 (★ 신설 v3.0 — P3의 실행 목록)

`known-incidents.md`의 사고1~24를 **실패 클래스**로 묶고, 각 클래스를 구조적으로 막는 장치와
담당 절을 지정한다. "이 설계는 그 실수를 할 수 없다"가 목표이지 "주의하겠다"가 아니다.

| # | 실패 클래스 | 출처 사고 | 구조적 방지 장치 | **강제 테스트**(이게 없으면 방지 장치가 없는 것) | 지금 돌리면 |
|---|---|---|---|---|---|
| **C1** | **물리 제약 미검증 상수** — 전압/전류 기본값이 KVL/KCL/Vgs=Vds를 만족하는지 확인 없이 쓰임 | 10, 23, 24 | 모든 전압/전류 값은 물리 solver 또는 declared 선언을 거친다. 상수 폴백은 "KVL/KCL 그룹에 속하지 않음이 확인된 소자"에만 허용하고, 그 판정을 함수가 직접 한다(§7.3 `set_device_vds()`) | `test_diode_self_consistency` — diode-connected 전수에서 `\|vgs_for_gm_id(gm_id,L,vds*,vs) − vds*\| < tol` | **FAIL** — 16/16 소자가 tol 초과, 최대 1.020V(M36a/b) |
| **C2** | **암묵적 순서 의존** — "누가 먼저 쓰느냐"로 결과가 달라짐 | 13, 19, 23 | vds 기입 7곳을 **단일 setter**로 수렴(§7.3 v4.3). 우선순위는 명시적 티어로 선언 | `test_order_shuffle_invariance` — 소자·그룹 **처리 순서를 셔플**해 2회 실행하고 instance.json이 바이트 동일한지 | 미실행 — `set_device_vds()` 단일화가 선행돼야 성립 |
| **C3** | **조용한 소실·덮어쓰기** — dict 키 충돌/저장 누락으로 데이터가 말없이 사라짐 | 12, 14, 16 | 이름 생성은 호출 전역 유일성 보장, 계산·저장 필드 목록을 한 곳에서 파생, 모든 pass 뒤 커버리지 재검증 게이트 | `test_coverage_and_field_completeness` — **기존 `check_stick_diagram_coverage()`(이미 프로덕션 배선됨)** 재사용 + instance.json 소자 누락 0 + 필수 필드 누락 0 + 이름 충돌 0 | 부분 — 커버리지 게이트는 배선돼 있으나 **필드 완전성·이름 충돌 검사가 없음** |
| **C4** | **role 라벨 과신** — 선언 라벨을 물리/connectivity 확인 없이 신뢰 | 9, 10, 11, 15, 18 | 물리 판정(`gate==drain`, `kind`, KCL)이 **항상 우선**, role 문자열은 최후 폴백 | `test_role_label_removal_invariance` — `headroom_role`/`gm_id_role`/`L_role`을 **전부 제거해도 결과가 같은지**. 물리가 우선이면 라벨은 결과에 영향이 없어야 한다 | **FAIL** — 같은 소자가 role만 바꿔도 vds가 `cascode`→0.200 / `mirror`→0.300 / 라벨없음→0.600으로 갈린다 |
| **C5** | **게이트가 무엇을 못 보는지 모름** — "통과"가 "볼 수 없어 통과"일 수 있음 | 11 | 각 게이트 docstring에 **검사하지 않는 것**을 명시. 상위 검증기(§7.5)가 하위 게이트의 사각을 덮는다 | `test_gate_docstring_declares_blind_spots` — `check_*`/`verify_*`/`validate_*`/`audit_*` 전수에서 docstring에 "검사하지 않는 것" 절이 있는지 정적 검사 | **FAIL** — 게이트류 19개 중 **4개만** 명시(`check_box_shape`, `audit_theta_root_direction`, `check_symmetry_dispositions`) |
| **C6** | **underdetermined를 반복으로 밀어붙임** — 자유도 부족을 반복으로 풀려다 착시적 수렴/데드락 | 19, 22 | **DOF 사전 진단**(`diagnose_sizing_dof()`)으로 판정. 상호참조는 독립방정식인지 먼저 검산 | `test_dof_catches_incident19_fixture` — 사고19 재현 픽스처(한 vertical_stack의 vds 미지수 2 / KVL 방정식 1)를 진단이 잡는지 | 미배선 — B5대로 진단이 **VDS 미지수·KVL 방정식 축을 세지 않는다** |
| **C7** | **단일 회로로만 검증** — 다른 회로에서 원래 있던 gap이 드러남 | 17 | 파일럿 검증 후 나머지 3개 토폴로지 **실제 실행**까지 완료해야 done | `test_all_four_topologies_run` — 4개 토폴로지를 새 엔진으로 실제 실행해 전역 게이트 통과 | 부분 — 현재 self-test는 "선언 위반 0건"만 보고 **사이징 실행은 안 한다** |
| **C8** | **엔진 우회·무근거 자동동작** — 손계산으로 축약하거나 근거 없이 자동 병합 | 1, 8, 20 | 모든 값은 함수 경유. 자동 병합/제안은 net-user-count 등 **connectivity 증거**를 요구하고, 증거가 없으면 `review_needed`로 표시하고 **파이프라인을 정지**한다 | `test_unevidenced_automerge_stops_pipeline` — 증거 없는 자동제안 픽스처를 넣으면 `review_needed`가 서고 파이프라인이 멈추는지 | 미배선 — `review_needed`는 이 표 밖에 등장하지 않는다(상태값 자체가 아직 없음) |
| **C9** | **중복 복붙** — 같은 로직·상수가 여러 곳에 존재해 한쪽만 고쳐짐 | 24 | **단일 출처 함수**로 통합 | `test_no_raw_duplicated_writes` — 단일 setter 우회(원시 대입)·중복 상수가 남아 있지 않은지 grep 검사 | 시작됨 — v4.3이 §7.3에 vds 원시 대입 grep 테스트를 도입 |
| **C10** | **재계산 비효율** — 같은 스캔을 호출부마다 반복 | 사용자 원칙, `lut-generation-checklist.md` §9 | 스캔 축을 함수 내부로 내리고 캐시 키를 "그 함수가 실제로 읽는 모든 가변 상태"로 | `test_cache_key_covers_mutable_state` — `ctx.sized`만 바꾸고 같은 metric을 호출했을 때 **옛 값이 반환되지 않는지**(CMFB MNA 캐싱 회귀 재현) | 미배선 |

> **이 표를 고쳐 쓴 이유(B11, v4.5)**: v3.0의 원래 표는 방지 장치를 **문장으로만** 적어두었고,
> 실측해 보니 그중 다섯(C3 일부·C4·C5·C6·C8)은 문서 전체에서 **그 표 안에서 딱 한 번씩만**
> 등장하는 빈 약속이었다(`review_needed` 2회 중 1회가 이 표, "전역 유일성"·"connectivity에서
> 유도" 각 1회). **선언만 하고 배선하지 않을 거면 애초에 만들지 않는다**는 원칙에 따라, 각 행에
> **"이게 없으면 방지 장치가 없는 것"이라고 말할 수 있는 테스트**를 지정했다.
>
> 그리고 **지금 돌리면 실패하는 것을 실패한다고 적었다**(C1/C4/C5). 이건 결함 고백이 아니라
> **DoD의 이빨**이다 — §4.1은 이 표의 모든 행이 PASS가 되는 것을 완료 조건으로 삼는다. 반대로
> 테스트를 지정할 수 없는 방지 장치가 나오면 그 행은 폐기하거나 다른 실효 장치로 교체한다.
>
> 부수 정정: v3.0 표의 담당 절 지정 중 **C7의 §5는 정반대 내용**(§5는 "파일럿 1개만"을 명시)
> 이었고 **C10의 §7.6에는 캐시 서술이 없었다**(실제 서술처는 §7.10/§6.1). 담당 절 열을 없애고
> 강제 테스트 열로 대체해 이런 어긋남이 재발하지 않게 했다.

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `<name>.sizing_spec.json` 스키마가 확정되고 `_TEMPLATE.sizing_spec.json` 스캐폴드로
      문서화됨
- [ ] `current_reuse_telescopic_ota`가 새 스키마 + 새 엔진으로 재사이징되어 instance.json이
      갱신됨
- [ ] **★ (최우선, §3.1 요구사항 6) `verify_node_voltage_consistency(ctx)`가 51소자 전체에서
      Violation 0건** — diode-connected 16개 소자의 자기일관 헤드룸(오차→0)은 이 검증의
      부분집합으로 포함되지만, 그 외 소자의 게이트-내부net VGS 불일치/노드 상호모순도 전부
      확인됨
- [ ] 기존 constraints(gain≥54dB, cmrr/psrr/mismatch/classab) 전부 재확인
- [ ] `cross_check_with_spice()`(sky130 SPICE `.op`)이 rail-lock 없이 수렴하고
      `verify_node_voltage_consistency()`의 LUT 기반 예측과 일치(원래 세션 목표였던 트랜지언트
      검증 재개 가능)
- [ ] **★ (v4.5) §3.3 C1~C10 표의 "강제 테스트" 10개가 전부 PASS** — 각 행이 지정한 테스트가
      `assets/tests/`에 실재하고 통과해야 한다. 지금 돌리면 **C1/C4/C5는 FAIL**이고 C2/C6/C8/C10은
      미배선인데, 그게 정상이다 — 이 표는 현재 상태를 정직하게 적고 완료 조건을 거는 장치다.
      특히 다음 셋은 "그 실패를 직접 재현"하는 형태라 통과하면 방지가 구조적으로 증명된다:
      `test_role_label_removal_invariance`(role 라벨 전부 제거해도 결과 동일),
      `test_order_shuffle_invariance`(처리 순서 셔플해도 결과 동일),
      `test_cache_key_covers_mutable_state`(`ctx.sized`만 바꿔도 캐시가 옛 값을 안 준다)
- [ ] **★ (v4.6, B4) 파일럿 1회 전체 실행 wall-clock ≤ 5분** — 기본 L 정책(bounds 내 LUT 앵커
      전수, 4³=64 combo) 기준 실측 예상 2.9분. 초과하면 곱셈 구조에 예상 못 한 항이 들어온
      것이므로 그 자리를 찾아 보고한다(예: `presolve_warm_start()` 16.5s가 루프 안으로 들어감)
- [ ] **★ (v3.0, C7) 파일럿 외 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/
      two_stage_ota)도 새 엔진으로 실제 실행** — self-test 통과만으로는 부족(사고17: 다른 회로를
      돌려야 원래 있던 선언 gap이 드러난다)

### 4.2 Quality Criteria

- 새 함수 추가로 인한 기존 self-test 회귀 0건
- diode-connected 자기일관 해석기가 20회 이내 고정점 반복으로 수렴(발산/진동 없음)

---

## 5. Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| stage 내부 input+cascode 동시결정이 수렴 안 하거나 비현실적 W를 낼 위험 | §7.2 알고리즘의 1~4단계는 각각 기존에 검증된 단일 함수 호출(`search_gm_id_for_role(role="gain")`, LUT 역보간, `size_transistor()`)의 조합이라 개별 단계는 이미 신뢰 가능 — 조합 후 W_bounds 위반 시 기존 `InfeasibleSizingError` 관례를 그대로 따른다 |
| "gain이 주도"로 뒤집으면서 GBW/PM이 실제로 안 맞는 회로가 나올 위험 | `solve_compensation_for_gbw_pm()`은 검증(§4.1 DoD)에 GBW/PM 재확인을 포함해야 함 — 이번 계획 문서에는 명시했으나 구현 단계에서 실제 검증 스텝으로 반드시 실행 |
| 사고4 재발(배분 자체를 결정론화하려는 유혹) | §3.1 요구사항 5번으로 명시적 경계를 문서에 고정 — 구현 시 이 경계를 벗어나는 변경은 별도 승인 필요 |
| 4개 토폴로지 동시 이관 시 범위 폭발 | §2.2 Out of Scope로 파일럿 1개만 우선 명시 |
| §8.4 사이징↔레이아웃 피드백 루프가 반복마다 소자를 재배치하며 조용히 소자를 삭제할 위험(2026-09-04 §1.4 추가 — `known-incidents.md` 사고16: `_layout_result_to_rows()`의 행 이름 카운터가 호출 전역에서 유일하지 않아 무관한 반복끼리 이름이 충돌 → `dict.update()`가 이전 결과를 조용히 덮어써 51소자 중 3개가 실제로 사라진 전례) | §8.4의 반복 피드백 구현 시 행/그룹 이름 생성 카운터가 **전체 파이프라인 호출에 걸쳐 유일**한지(지역 카운터가 아닌지) 명시적으로 검증할 것 — 사고16이 신설한 "repair 이후 재검증 게이트"(`check_stick_diagram_coverage()`) 패턴을 §8.4의 5~6단계(수렴/실패 판정)에도 동일하게 적용해, 반복마다 넷리스트 소자 수가 그대로인지 재확인하는 스텝을 넣는다 |

---

## 6. Impact Analysis → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

## 7. Architecture Considerations

### 7.1 새 JSON 스키마 (`<name>.sizing_spec.json`) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.2 신규 사이징 알고리즘 (stage 1개 기준) — §1.4의 §13.1/§13.2/§13.7 반영으로 개정 → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.3 헤드룸(VDS) 해석기 재설계 — v2.0(기존 인프라 재사용) → **v3.0(우선순위 체인에 diode 티어 신설, C2 근본 제거)** → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.4 확정된 설계 원칙 (사용자 승인 완료, 이번 세션 AskUserQuestion)

1. Stage 안의 input+cascode는 gain 목표에서 L/gm_id를 **동시에** 결정한다(캐스코드 L을 role
   휴리스틱으로 따로 정하지 않는다).
2. ~~**Gain이 주도**한다 — 모든 stage gm_id를 gain 배분에서 먼저 정하고, GBW/PM은 보상소자
   값으로 사후에 맞춘다.~~ → **v4.0에서 사용자 확정으로 개정: 인과 방향은 그 반대다.**

   > **왜 뒤집혔나**(4개 관점 독립 검토에서 회로물리·문서정합성 두 검토자가 각각 최우선으로
   > 지적): v3.2가 §7.9를 `gm_i ← compensation이 고정`으로 재정식화하면서 이 원칙2와 §3.1
   > 요구사항4를 갱신하지 않아 문서가 **두 갈래로 갈려 있었다**. 둘은 양립 불가다 — §7.9의
   > 목적함수 `min Σ gm_i/gm_id_i`와 KKT `gm_i/gm_id_i²`는 `gm_i`가 상수여야만 성립하고,
   > `gm_i`가 자유롭다면 `gm_i→0`에서 목적함수가 무한히 감소해 문제 자체가 well-posed가 아니다.
   > 물리적으로도 Miller OTA에서 `(gm_1, gm_2, Cc)`는 `GBW = gm_1/Cc`와 PM(비지배극점
   > `gm_2/(C_1+C_2)`, RHP zero `gm_2/Cc`)이 **동시에** 묶는 3-tuple이라 "gm을 먼저 고정하고
   > Cc를 사후 역산"은 애초에 불가능하다. 문헌 정본 §6.4의 순서(`gm1=ω_T·Cm`, `gm2=Z·gm1`)도
   > §7.9 쪽과 일치한다.

   **확정 인과사슬**(문서 전체가 이 하나만 따른다):

   ```
   스펙 (CL, GBW, PM, Z, NDP)
     -> compensation:  (Cc, Rz, gm_1..gm_N) 을 한 번에 결정        [소자 사이징 아님]
     -> 자유 축:       gm_id_i                                      [★ 유일한 설계 자유도]
     -> 파생:          ID_i = gm_i/gm_id_i,  W_i = L_i*ID_i/IDu_i,  k_i = ID_i/ID_ref
     -> 기생:          C_1, C_2 (= f(W_i,L_i))  ->  Cc 재계산  ->  gm_i 갱신  [수렴 루프]
     -> 결과:          gain 은 스펙이 아니라 이 공간 위의 **부등식 제약이자 산출물**
   ```

   **"gain-budget-first"라는 이름의 의미도 여기서 확정한다**: "gain이 gm을 정한다"가 아니라
   **"stage별 gain 예산을 엔진이 유도해 산출한다"**(원칙3)는 뜻이다. gain은 입력이 아니라
   총량 제약 하나로만 들어오고, 단별 배분은 출력이다.
3. ~~배분 자체는 탐색/사용자 지정으로 남긴다~~ → **v3.1에서 사용자 확정으로 개정**:
   **배분도 엔진이 유도한다.** 총 gain 목표만 스펙으로 받고, stage별 배분은 §7.9 Phase 2의
   `A_i,max` 실측 + root current 1-D 해찾기 결과로 나온다(`gain_budget_db`는 출력). 사고4의
   본질("값을 논문에서 찾지 말고 회로에서 도출하라")은 유지되며, 도출 방식이 자유 탐색에서
   물리 실측 기반 결정론으로 좁혀졌을 뿐이다. 특정 배분 강제는 `gain_budget_db_override`로만.

### 7.5 전체회로 물리 정합성 검증기 (★ 신설 — §3.1 요구사항 6, 이번 재설계의 핵심 동기) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.6 CMRR/PSRR/mismatch를 gain-budget 방법론에 결합하는 법 (★ 신설, 2026-09-04) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.7 L 변경 규칙 (★ 신설, 2026-09-04 — §7.6의 L 탐색이 레이아웃을 깨지 않게 하는 원칙)

§7.6이 L을 새 탐색 차원으로 열었으므로, "L을 언제/어떻게 바꿔도 되는가"의 규칙이 필요하다.
아래는 전부 기존 자산에서 근거를 찾아 정리한 것이다(신규 발명 없음).

| 규칙 | 내용 | 근거 |
|---|---|---|
| **R1. 누가 바꿀 수 있나** | §13.3의 **5개 구조 신호**로 먼저 판정 — 하나라도 걸리면 L은 파트너와 **강제 일치**(독립 변경 금지), 아무 신호도 안 걸리는 소자만 L 독립 탐색 대상 | `gm-id-methodology.md` §13.3(4개 회로 전수, 반례 0건) |
| **R2. 매칭 그룹은 전원 동시에** | 매칭은 **동일 기하(unit cell)** 전제로 공정 gradient를 상쇄하는 기법이라, 그룹 중 한 소자만 L이 달라지면 전제가 깨진다 — 바꾸려면 그룹 전원을 같은 값으로 한 번에 | `stick-diagram-euler-layout.md` §2.5("W = N × unit_cell"이 조립 방식의 정의) |
| **R3. LUT 실측 격자 밖 금지** | `SemiEmpiricalGmIdLUT`는 보간만 하고 외삽은 안 한다 — sky130 sample LUT의 L 앵커는 **전체 7개**(0.15/0.35/0.5/1.0/1.5/2.5/4.0µm)이고, 그중 파일럿 L theta의 bounds `[0.15,1.0]µm` 안에 드는 것이 **4개**(0.15/0.35/0.5/1.0µm)다 — v4.6 문맥 명시(이 둘을 구분하지 않으면 §7.6 실행시간 예산이 어긋난다) | `lut-generation-checklist.md` §7.7 |
| **R4. L↑가 항상 이득이 아니다 — 전수 스캔** | M107 실측: L=375nm→4µm에서 `gm·ro`가 **26배 악화**(L↑ → W_bounds와 상호작용해 feasible gm_id가 더 낮게 밀림). gds의 L 의존성은 소자·VDS마다 곡선이 달라 지름길 없음 | `gm-id-methodology.md` §13.7 |
| **R4b. 이득이 부족하면 L보다 VDS를 먼저 조정한다 ★** | 문헌 실측(45nm 2단 Miller OTA): L=100nm 고정·V_A 상수 가정으로 41.4dB 미달 → **VDS를 축으로 2회 반복**하자 같은 L에서 **61.4dB 달성**(면적 페널티 0). 우리 sky130 LUT 재측정(gm_id=15, ID=5µA): **VDS 0.2→1.2V는 gm/gds를 21.7→93.2(+329%)로 올리면서 W를 1.332→1.126µm(−15%)로 오히려 줄이는 반면, L 0.15→4µm는 gm/gds를 17.8→280.4(+1480%)로 올리는 대가로 W를 0.636→11.9µm(+1770%, 18.7배)** 쓴다 — R5/R6의 레이아웃 재검증 비용이 정확히 이 W 변화량에 비례하므로, **§7.7 자체가 "VDS를 먼저 소진하라"는 근거**다. ⚠️ VDS 조정도 IDu를 통해 W를 ~15% 바꾸므로 R8(수렴 루프 내부 + 커버리지 재확인)은 VDS에도 동일 적용한다 | `gm-id-methodology.md` §9.4/§9.5, 본 세션 LUT 실측(§7.9) |
| **R5. 직접 영향 — 행 폭** | 행 물리 폭 = `Σ n_fingers × pitch(l)`, `pitch(l)=l+overhead`. L은 행 폭에 **선형으로 직접** 들어가므로 L 변경 시 `check_box_shape()` 재실행이 **필수 게이트**(눈대중 금지) | `stick_diagram.py:6400/6421`, 레이아웃 문서 §8/§8.2 절차 5 |
| **R6. 간접 영향 — W→n_fingers 연쇄** | L이 바뀌면 같은 (gm_id, ID) 유지를 위해 W가 바뀌고 → `n_fingers` 변화 → 행 길이·interdigitation 패턴·`check_finger_width_compatibility()`(W는 finger_w의 정수배) 전부 재판정 대상 | 레이아웃 문서 §3.5 |
| **R7. 안 깨지는 것 2가지(정직 명시)** | (a) **오일러 패스는 L과 무관** — `build_graph()`/`check_euler_condition()`은 net-connectivity 그래프라 `l`을 안 본다(구조적 하드 게이트는 kind 동질성뿐). (b) **같은 물리 행 안에서 `l`은 달라도 되지만 `finger_w`는 반드시 같아야 한다** — `compute_row_geometry()`가 한 행 안의 서로 다른 `l`을 각자 pitch로 계산하도록 명시 설계됨("Euler trail로 여러 소자가 한 diffusion strip에 섞이는 게 정상 동작"), 반면 `finger_w`가 행 안에서 다르면 물리적으로 불가능해 `ValueError`. **단 그 행의 소자들이 매칭 그룹이면 R1/R2가 우선해 L도 일치시켜야 한다.** | 사고11(2축 분리), `stick_diagram.py:6421` docstring |
| **R8. 수렴 루프 "안"에서만 바꾼다** | L 변경 → 사이징 재계산(gm_id/W) → finger 재배분 → §3.5/§8 게이트 재실행 → §7.5 물리 정합성 검증. §7.6의 L 탐색은 §8.4 수렴 루프 **밖에서 따로 돌리면 안 되고 루프 안에** 들어가야 하며, 반복 재배치가 소자를 조용히 잃을 수 있으므로(사고16: 51소자 중 3개 소실) 매 반복 커버리지 재확인 게이트를 함께 돈다 | 사고16, §8.4 |

> **⚠️ branch(전기적)와 row(물리적)를 혼동하지 말 것(R7 관련 실제 질의로 명확화, 2026-09-04)**:
> 하나의 `vertical_stack_id`(=branch, 전기적 VDD~GND 컬럼)에 PMOS와 NMOS가 섞이는 건 **정상**
> 이고(class-AB 출력단의 정의 자체), 그 둘이 **서로 다른 L을 쓰는 것도 이미 정상 동작**이다 —
> 파일럿 회로 실측: `output_stage_a`의 M15(pmos, L=0.150µm)와 M16(nmos, L=0.830µm)로 5.5배
> 차이. 이게 가능한 이유는 R7 때문이 아니라 사고11의 **2축 분리**(`derive_horizontal_stack_
> groups()`가 전기적 그룹을 kind로 먼저 쪼개 `__pmos`/`__nmos` 행을 따로 만든다) 때문이다 —
> PMOS와 NMOS는 애초에 같은 물리 행에 못 들어간다. R7 (b)가 말하는 건 **같은 행(당연히 같은
> kind) 안에서** `l`이 달라도 되는가에 대한 훨씬 좁은 얘기다.

---

### 7.8 DOF 사전 진단 — 목표 개수 대비 자유도가 충분한가 (★ 신설, 2026-09-07) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.9 헤드룸(VDD) 자원배분 — "배분"의 진짜 대상 (★ 신설, 2026-09-07) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 7.10 초기 L 선택 기준 (★ 신설, 2026-09-07 — §7.6 L_combo 탐색의 시작점)

**왜 필요한가**: 현재 엔진은 `_L_ROLE_MULTIPLIERS = {"mirror": 2.5, "bias_replica": 1.2}`
(×L_min) 고정배수만 갖고 있고, 캐스코드/신호경로는 `select_L_by_role()`이 명시적으로 거부하며
"theta 탐색이 대신 결정"으로 비워둔 상태다. 코드 주석 자신이 2.5배를 "실무 관례 2~3배의 **중간값**
(범위 내 대표값)"이라 밝히고 있어 임의성이 남아 있었다. §7.6이 L을 탐색 차원으로 열었으므로
**그 탐색의 시작점**을 원리적으로 정할 필요가 있다.

**측정 1 — L을 늘릴 때 얻는 것과 잃는 것** (본 세션 sky130 LUT 실측, nmos, gm_id=15, ID=5µA, VDS=0.6V):

| L/L_min | gain배(gm/gds) | 면적배(W·L) | fT배 | mismatch 개선배(√WL) |
|---|---|---|---|---|
| 1.0 (0.15µm) | 1.00 | 1.00 | 1.000 | 1.00 |
| **2.3 (0.35µm)** | **3.91** | **4.29** | 0.288 | 2.07 |
| 3.3 (0.50µm) | 5.94 | 8.94 | 0.149 | 2.99 |
| 6.7 (1.0µm) | 8.47 | 34.5 | 0.041 | 5.87 |
| 26.7 (4.0µm) | 15.80 | **498.8** | **0.003** | 22.33 |

- **gain 수확체감이 극심**: 첫 2.3배 구간이 gain 3.91배를 주는데, 이후 L을 11.6배 더 늘려도 4배만 추가.
- **fT는 L²에 반비례로 붕괴**(fT=gm/2πCgg, Cgg∝W·L∝L²): 2.3배에서 이미 1/3.5, 6.7배면 1/24
  → **fT가 L 상한을 정하는 진짜 제약**이다(기생 pole이 GBW를 침범하면 PM이 무너진다).
- **mismatch 개선은 √(W·L)이라 완만**: 2.3배 → 2.07배.

**측정 2 — 한계효율 knee의 위치** (`Δ(gm/gds)/Δ(W·L)` = 면적 1단위당 얻는 gain):

| | 0.15→0.35 | 0.35→0.50 | 0.50→1.0 | 1.0→1.5 |
|---|---|---|---|---|
| nmos gm_id=8 | **406** | 205 | 74 | 13 |
| nmos gm_id=15 | **165** | 81 | 18 | 5.4 |
| nmos gm_id=22 | **25.5** | 5.9 | 1.0 | 0.5 |
| pmos gm_id=15 | **최대** | 25.8 | 17.8 | 3.5 |

**kind와 gm_id를 바꿔도 knee는 항상 `L ≈ 2~3 × L_min`** 구간이다 — 즉 기존 `mirror: 2.5×L_min`
배수는 "관례의 중간값(임의 선택)"이 아니라 **실측 knee와 일치**함이 사후 검증됐다(근거가 생겼으니
주석의 "임의 대표값" 표현은 구현 시 이 실측으로 대체할 것).

**원칙 — 초기 L은 knee에서 시작하되 물리 제약으로 clamp한다**:

```
L_init = knee(kind, gm_id, vds)          # 한계 gain/면적 효율이 최대인 구간의 상단, LUT 실측
clamp:
    L <= L_max(fT)     : fT(L) >= N x GBW      (N~5~10, 기생 pole의 GBW 침범 방지)
    L >= L_min(match)  : sigma_VT = A_VT/sqrt(W*L) <= 목표(§7.6 global_spec.constraints)
    L in LUT 실측 격자  (§7.7 R3, 외삽 금지)
role별 방향 편향:
    cascode(role="gain")        : knee 이상으로 밀어도 됨(ID 고정이라 전력비용 0) -- fT 상한이 우선
    mirror/matching             : knee + mismatch 하한(면적이 매칭에 직접 기여)
    속도 임계(GBW 담당 입력단)   : fT 상한이 지배 -> knee보다 작을 수도 있음
    tail/load(§7.6)             : gds 최소화가 목적 -> CMRR/PSRR을 만족하는 최소 L
```

**왜 L_min이 아니라 knee에서 시작하나**: §7.6의 L_combo 탐색은 "면적 오름차순 첫 feasible"이므로
시작점은 원칙적으로 "제약이 허용하는 최소 L"이어야 한다. 그런데 그걸 그냥 `L_min`으로 두면
gain이 너무 낮아(측정 1: L_min에서 gm/gds=17.75, 약 25dB) 대부분의 조합이 infeasible로 버려져
탐색이 낭비된다 — **knee에서 시작하는 것이 실용적이며, knee 아래는 fT가 정말 급한 소자에만
내려간다.**

**§7.7 R4b와의 결합(중요)**: knee에서 시작 → gain이 부족하면 **먼저 VDS 재배분**(§7.9 inner
루프, W −15%) → 그래도 부족할 때만 L을 knee 위로 올린다(§7.6 mid 루프, W +1770%). 즉 §7.10은
"어디서 출발하나", §7.7 R4b는 "부족하면 어느 노브부터 쓰나"를 각각 답한다.

**⚠️ 실측으로 찾은 반례 — "면적은 L에 단조 증가"가 아니다**: pmos 일부 구간에서 **L을 늘렸는데
`W·L`이 오히려 감소**했다(한계효율이 `inf`로 계산됨). `IDu`가 L에 비단조이기 때문이며, §7.7 R4의
"지름길 없이 전수 스캔" 원칙이 여기서도 확인된다 — knee 탐색도 닫힌 식이 아니라 격자 전수
스캔으로 구현할 것.

**신규 함수**: `measure_L_knee(lut, kind, gm_id, vds, L_grid) -> float`(측정 2의 한계효율 스캔),
`L_bounds_from_ft_and_matching(spec, stage) -> (L_lo, L_hi)`(fT 상한/mismatch 하한 계산) —
둘 다 §7.6의 `L_candidates_product()`가 탐색 범위를 정할 때 호출한다.

**개선 대상 함수(★ v3.0)**:
- `_L_ROLE_MULTIPLIERS = {"mirror": 2.5, "bias_replica": 1.2}` **상수 → `measure_L_knee()`
  실측 호출로 대체**. 이번 실측으로 2.5×가 sky130 knee와 일치함이 확인됐지만, **공정이 바뀌면
  knee도 바뀐다** — 상수로 두면 다른 PDK로 이식할 때 조용히 틀린 값을 쓴다(C1/C9). 실측
  호출로 바꾸면 자동 추종하고, `select_L_by_role()`이 `cascode`/`signal`을 거부하던 제약도
  함께 해소된다(knee가 모든 role에 정의되므로).
- `search_gm_id_for_role()` → **`search_gm_id_and_L_for_role()`**(L축 내부화, §6.1 (가)) —
  knee 탐색·L_combo 탐색·role 목적함수가 **같은 `_idu_scan` 결과를 공유**하게 되어 P2(중복
  스캔 금지)를 만족한다.

---

### 7.11 기생 pole clamp — L 상한을 **회로가 스스로 말하게** 한다 (★ 신설, 2026-09-10)

**왜 필요한가**: §7.10이 `L <= L_max(fT) : fT(L) >= N x GBW (N~5~10)`이라 적어뒀는데
**엔진에 이 검사가 없다**(`fT()`는 있으나 호출부 0개, B20 조사 때 확인). 상한이 없으면
gain이 L을 무한정 밀어 올린다 — 실제로 미러 gain 랭킹에서 최적이 `L=4.0µm`(격자 최대)로
나왔다(§10.3 B19'). 그런데 `N`을 상수로 박으면 **그 회로에 맞춘 숫자**가 되어 일반성을
잃는다. 이 절은 N을 **유도해서 없애는** 방법을 정한다.

#### 1) 문헌 조사 (2026-09-10, 사용자 지시)

| 출처 | 내용 |
|---|---|
| Sansen, *Analog Design Essentials* | 비지배 pole은 GBW의 **약 2배 이상** |
| 표준 2-pole 결과 | p₂/UGF = 1 → PM 45° / 2 → ~59° / **3 → 71.6°** |
| 실무 경험칙(EDAboard) | 단일단 fT ≥ **10×**GBW, 2단 **>20×** |
| 미러가 신호경로에 있을 때 | `fT ≈ (N_mirror + 4) × UGF`이면 p₂ ≥ 3×UGF 달성 |

#### 2) 그런데 이 회로엔 **정의식**이 이미 있다

`compensation` 주석에 원문(Xie & Chen) PDF에서 직접 확인해 등록한 관계가 있다:

    PM = tan⁻¹(ω_p2 / ω_c)

일반 경험칙이 아니라 **이 토폴로지의 정의식**이다. 여기서 바로 나온다:

    PM_target = 70°  →  ω_p2 ≥ tan(70°)·ω_c = 2.747·ω_c
    ω_c = 6.9/t_lln = 2.3e8 rad/s  →  f_c = 36.6 MHz,  f_p2 ≥ 100.6 MHz

#### 3) N의 정체 — §7.10의 "5~10"은 임의값이 아니었다

노드 pole `f_p = gm/(2π·C_node)`, `fT = gm/(2π·Cgg)`이므로 `C_node = α·Cgg`라 두면

    **N = α × tan(PM_target)**

| α (노드 용량 / 소자 Cgg) | 2 | 3 | 3.6 | 4 | 7.3 |
|---|---|---|---|---|---|
| N | 5.5 | 8.2 | 9.9 | 11.0 | 20.1 |

즉 §7.10의 `N~5~10`은 정확히 `α ∈ [2, 3.6]`이고, 문헌의 "2단 20×"는 `α ≈ 7.3`이다.
**N은 독립 상수가 아니라 (PM 관계식) × (노드 용량비)의 결과다.**

#### 4) 실측 — 이 회로에서 fT는 knee 근방을 안 묶는다

tail 4개(M5/M6/M7/M38)의 최소 `fT/f_c`:

    L=0.150µm  83.8      L=0.375µm(knee)  ~28      L=0.700µm  9.5      L=1.000µm  4.9

knee에서 여유가 28배라 N=10은 물론 N=20에도 안 걸린다. **fT가 실제로 무는 것은
L ≳ 0.7µm**이고, 그게 바로 gain이 L을 4.0µm로 밀려 할 때 필요한 제동이다.

#### 5) ★ 코드화 원칙 — 숫자를 박지 말고 **유도 경로를 배선**한다

`N`을 상수로 넣으면 이 회로 전용이 된다. 대신 N을 만드는 두 항을 각각 회로에서 얻는다:

```
필요 pole 위치   ω_p2_req = f_PM(PM_target, ω_c)   <- **토폴로지가 안다**
                 (이 회로: tan(PM)·ω_c. nmcnr/folded는 자기 topology_fn이 정의)
노드 용량비      α_node   = C_node / Cgg_device    <- **넷리스트에서 잰다**
                 (노드에 붙은 모든 소자의 Cgg/Cdb 합, cgg_absolute()로 계산)
제약             ω_pole(node) = G_node / C_node >= ω_p2_req
```

**즉 `fT >= N·GBW`는 `ω_pole(node) >= ω_p2_req`의 손 근사였다.** 노드 pole을 직접 쓰면
α도 N도 필요 없다 — 둘 다 측정/유도로 사라진다.

**단계**:

| | 내용 | 일반성 |
|---|---|---|
| L1 | 노드별 `G/C` 추정(LUT gm·gds·Cgg를 넷리스트 노드로 합산) | 회로 무관 |
| L2 | 기존 51노드 MNA에서 **실제 pole 추출**(고유값) | 회로 무관, 더 정확·비쌈 |

**선언으로 노출**(§3.2 P1, C1 — 선언 출처 없는 제약 금지): 이 clamp는 숨은 상수가 아니라
`sizing_roles.metrics`의 **metric**으로 내놓고 constraint로 걸 수 있게 한다.

#### 6) ★ 구현 완료 (2026-09-10) — 하한까지 유도해 상수를 전부 없앴다

**하한도 `k`(pole 개수)로 배분하지 않는다 — 위상을 직접 더한다**:

    PM_parasitic = 90 - sum_over_nodes( atan(w_c / w_pole(node)) )
    제약:          PM_parasitic >= PM_target_deg      <- 이미 선언된 값

이 식은 **원문 관계를 특수케이스로 포함한다**: 비지배 pole이 하나면
`90 - atan(w_c/w_p2) == atan(w_p2/w_c)`(항등식)이라 원문의 `PM = atan(w_p2/w_c)`와 **정확히
같다**. 즉 `alpha`·`N`·`k`가 **셋 다 사라진다** — 하한은 새 상수가 아니라 이미 선언된 PM 목표다.

**신설 함수 3개**(전부 회로 무관):

| | 하는 일 |
|---|---|
| `signal_path_nodes(by_name, excite, sense)` | `gate->drain`/`source->drain` 방향그래프에서 excite 도달 ∩ sense 역도달. **bias 노드를 자동으로 배제**한다 |
| `node_pole_estimate(by_name, sized, spec, only)` | 노드별 `G/C`. 드레인→`gds`, 소스→`gm+gds`, 게이트→`Cgg`(`cgg_absolute()`) |
| `_metric_parasitic_pm_deg` | 위 둘을 합쳐 metric. `excite`/`sense_p`/`sense_n`을 `smallsignal_gain_db`와 **같은 형태로** 선언받는다 |

**구현 중 실측으로 바로잡은 것 둘**:

1. **전 노드를 세면 무의미하다** — 처음엔 모든 내부 노드를 더했더니 `PM = -1004도`가 나왔다.
   `Vbias1`/`Vbias4` 같은 **순수 bias 노드가 각각 ~90도**를 먹기 때문이다. 그 노드들은 pole이
   있어도 이 경로의 위상을 안 먹는다 → `signal_path_nodes()`로 경로를 유도해 해결.
   그래서 **어느 경로의 PM인지가 선언에 있어야 한다**(전 노드 합산은 원리적으로 틀렸다).
2. **못 세는 노드를 조용히 넘기지 않는다** — LUT에 CGG만 있고 **접합용량(Cdb/Csb)이 없어서**
   게이트가 안 붙은 노드는 용량을 셀 수 없다. 근거를 따져 둘로 갈랐다: **소스가 붙은 노드**는
   `1/(gm+gds)` 저임피던스라 pole이 높아 지배할 수 없으므로 이유와 함께 제외하고, **드레인만
   붙은 고임피던스 노드**는 `undetermined`로 돌려 **명시적으로 실패**한다. (파일럿은 경로를
   좁히자 `undetermined` 0개가 됐다 — 못 세던 5개는 전부 포트였다.)

**파일럿 실측(2026-09-10)** — 신호경로 8노드 중 셀 수 있는 4개:

    Vg15 / Vg25    f_pole =  31.6 MHz = **0.86 x f_c**   각 49.2도씩 먹는다
    Vom1 / Vop1    f_pole =  11.1 GHz =  304  x f_c      각 0.19도

    PM_parasitic = 90 - 98.9 = **-8.9도**   (PM_target 70도)

**class-AB 출력단 게이트 노드(`Vg15`/`Vg25`)의 pole이 크로스오버보다 아래**에 있다. 기존
metric 어느 것도 이걸 못 봤다. **constraint로는 아직 안 건다** —
`mirror_ratio_error`/`kcl_residual` 선례대로 4개 회로에서 먼저 재고 상한을 정한다.

## 8. 3단계 실행 파이프라인 — 파일/harness 함수 구조 (2026-09-04 추가) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

## 9. Next Steps → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

## 10. 독립 검토에서 나온 미해결 항목 (★ 신설 v4.0, 2026-09-07)

계획 v3.4를 **4개 관점의 독립 검토자**가 병렬로 심사했다 — (A) 회로 물리·방법론 타당성,
(B) 구현 가능성·성능·코드 대조, (C) 문서 내부 정합성, (D) 임의 토폴로지 일반성. 각 검토자는
서로의 결과를 보지 않았고, 지적은 문서 원문·실제 코드와 대조해 검증한 뒤에만 아래에 남긴다.

v4.0은 이 중 **사용자가 결정한 3건과 코드 선행조치 3건**을 반영했다. 나머지는 아직 열려 있으며,
**유실을 막기 위해** 여기 기록한다. 각 항목은 "누가 지적했는지 / 검증 상태 / 필요한 결정"을 함께
적는다.

### 10.1 반영 완료 (v4.0) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.2 미해결 — 물리·수식 (검토자 A)

| # | 내용 | 검증 상태 | 필요한 결정 |
|---|---|---|---|
| A1 | **KKT λ 항 부호 오류**. `L = Σgm_i/x_i + μ(ΣArea−A) + λ(G − Σgain_i)`에서 `gm_i/x_i² = μ·Area_i′ **−** λ(20/ln10)/x_i`인데 문서는 `+`로 적혀 있다 | 재미분으로 확인 | 단순 정정. 더불어 **전력·gain이 gm_id에 대해 같은 방향**이라 μ>0·λ>0 동시 성립 내부해가 일반적으로 없다는 사실(케이스 3)이 사실상 공집합)도 명시할 것 |
| A2 | **`Area_i`의 정의가 문서 어디에도 없다**. `∂Area/∂gm_id`를 쓰면서 정의가 없고, 최적화가 쓰는 면적(W·L 추정)과 레이아웃 게이트가 판정하는 면적(`Σ n_fingers × pitch(L)`, §7.7 R5)이 **서로 다른 물리량**이다. 게다가 `Cc` 면적이 빠져 있다(정본 §6.4 예제 기준 Cm 1.41pF ≈ 1,400µm² > 트랜지스터 전체) | 문서에 없음 확인 | `Area = Σ(n_fingers×pitch(L)×W_finger) + Σ(C/C_density + R_area)`로 정의를 못박을지 결정 |
| A3 | ~~`min Σ ID_i`가 회로 전력이 아니다(bias 전류 누락)~~ → **2026-09-08 해소(v4.9)**. **bias 누락은 사실이 아니었다** — `sum_current`는 `devices` 미선언 시 `ctx.sized` 전체를 더하고, gain-stage 밖 39소자 107.50µA가 이미 포함돼 있다. 진짜 결함은 **직렬 중복 계상**이다: 전 소자 ID 합 **243.32µA** vs VDD 레일 유입 **86.27µA** = **2.82배**. 더 나쁜 건 배수가 branch마다 다르다는 것(`diffpair_branch_a` 8소자 vs battery 3소자) — 즉 `min sum_current`는 **"그 branch에 소자가 몇 개냐"는 설계 무관 가중치**가 붙은 전력을 최소화한다 | 실측 + metric 신설 | **부분 잔여** — `supply_current` metric을 신설·선언해 나란히 보고한다. **objective 교체는 탐색 결과를 바꾸는 설계 결정이라 아직 안 했다**(design/do 단계) |
| A4 | ~~VDS 재배분이 매칭 쌍을 깬다~~ → **2026-09-08 해소(v4.8)**. 실측하니 지적의 절반은 이미 해결돼 있었다: `matching_pairs`가 `offset`/`ratio`로 갈려 있고 **offset 3쌍은 ΔVDS=0**(헤드룸 해석기가 `_hr_vfind()` union으로 이미 강제). 진짜 gap은 `ratio`(미러) 쌍이다 — 18쌍 중 3쌍이 VDS 불일치이고 **M18_bg/M60은 ΔVDS=1.300V, V_A=2.04V로 ΔI/I=63.6%**(미러비가 설계값의 1.6배). B1(diode 고정점)을 고쳐도 25.0%가 남아 **독립 문제**다. 다만 "VDS도 같게 강제하라"는 미러에 물리적으로 틀리다 — 레퍼런스(diode)와 출력(부하 노드)의 VDS가 다른 것이 정상이다. 그래서 제약이 아니라 **재는 값**으로 처리: `mirror_ratio_error` metric 신설(unit `%`, `aggregate` max/rss). 파일럿 실측 max **63.606%** / rss 71.912% | 실측 + metric 신설 | **부분 잔여** — metric은 만들어 배선했으나(선언만으로 계산·보고됨) **상한 제약은 아직 안 걸었다**. 먼저 4개 회로에서 재보고 나서 값을 정한다(값을 지어내지 않는다). §7.9 VDS 재배분이 이 비용을 보게 하는 것은 design/do 단계 몫 |
| A5 | ~~온도·공정 코너 전무, gm_id가 300K 천장으로 밀린다~~ → **2026-09-08 부분 해소(v4.9)**. 구체 우려는 **현 파일럿에서 미발생**: gm_id 최대 24.68(M6)로 350K 천장 27.6보다 낮다(250/300/350K 어느 천장도 초과 0개). 그런데 **더 근본적인 문제**를 찾았다 — 엔진에 온도 개념이 noise metric 하나뿐(`temperature_K` 기본 300)이고 사이징 어디에도 없으며, **LUT npz에 코너/온도 메타데이터가 아예 없다**. 즉 사이징 결과가 어느 조건에서 유효한지 산출물이 말할 수 없다. 생성기 코드상으로는 `__tt.pm3.spice`(TT) + `.temp` 미지정(ngspice 기본 27°C)이다 | 실측 + 생성기 코드 확인 | **부분 잔여** — 생성기가 `corner`/`temp_c`를 기록하도록 고치고 `lut_conditions_from_npz()`가 기록 없으면 **조용히 300K를 가정하지 않고** `recorded=False`를 돌려주게 했다. 기존 8MB npz는 재저장하지 않았다(재생성 시 기록됨). **코너 스윕 자체는 여전히 범위 밖** — §2.2에 명시 필요 |
| A6 | **ICMR·출력 swing·THD가 §7.9 헤드룸 하한 목록에 없다**. `output_swing`은 하한으로 쓰인다고 서술되나 스키마에 슬롯이 없다(선언 출처 없는 제약 = 상수 폴백, C1) | 문서 확인 | 스키마 슬롯 신설 여부 |
| A7 | **고정점 수렴이 "20회 이내"라는 요구사항으로만 존재**하고 논증이 없다. 단순 대입 반복 대신 `g(v)=f(v)−v` 단조성을 이용한 **bisection**이면 유일해·유한회 수렴이 보장되고 "격자 안에 해 없음"을 명시적 실패로 낼 수 있다 | 문서 인용 확인 | 구현 방식 확정(대입 반복 vs bisection) |
| A8 | ~~스택 diode 연립 solver가 필요하다~~ → **2026-09-08 재해석(v4.13)**. 실물에 **diode 2개 직렬 스택이 존재함은 확인**됐다(`biasgen_vom/vop_battery_a`의 M11a+M11b, `..._battery_b`의 M14a+M14b) — 그 때문에 22개 스택 중 **7개가 예산 초과**한다(최대 1.346V). 다만 **연립 solver는 필요 없다**: diode의 Vgs는 gm_id가 정하는 **종속값**이지 예산을 나눠 갖는 자유변수가 아니므로, 스택 KVL은 방정식이 아니라 **gm_id 조합이 만족해야 하는 제약**이다 (`Σ Vgs_k(gm_id_k,...) + Σ vds_j ≤ 예산`). v4.2의 분리형 DP가 이미 다루는 형태라 **제약 추가**로 처리한다 | 전수 사전계산 | **2026-09-08 계기판 배선 완료(v4.14)** — `stack_headroom_slack` metric 신설·선언(실측 **−1.3456V**, 사전계산과 일치). 아직 **constraint로 걸지 않았다** — 지금 걸면 즉시 infeasible이라, 먼저 재탐색으로 해를 찾은 뒤 건다. 다음: B1 5단계(배선)+재탐색 |
| A9 | **SPICE 교차검증의 허용오차 미정**. 방법론 §6.5가 "LUT 1차 계산은 10~20% 오차"라고 적고 있는데 §4.1 DoD는 "일치"만 요구한다 → 사후에 임의 임계값을 정하게 된다(C1 재발) | 문서 확인 | 노드전압 절대오차·전류 상대오차를 **미리** 못박을 것 |
| A10 | ~~v3.3 근거 실측치가 물리적으로 불가능~~ → **2026-09-07 조사 완료: 기각.** "28→77.6"은 dB가 아니라 **선형 `gm/gds` 비**였다(dB로는 28.98→37.80). `V_A` 5.62→2.98V로 정상이고 면적 4000배 폭발도 실재한다(`IDu`가 1000배 하락하는 deep weak inversion) | LUT 직접 재현 | **없음** — v3.3 논거 유지. 다만 §7.9 표에 단위를 명시했다(선형비/dB 혼용이 오독을 유발) |
| **A12** | **★ metric 이름이 단위를 거짓말한다(실물 결함)**. 파일럿 실제 설계점에서 `power_uA`=0.000243323(실제 **A**, 직접 합산 243.32µA), `area_um2`=1.17156e-10(실제 **m²**, 직접 합산 117.16µm²) — 정확히 10⁶·10¹²배. 엔진은 SI로 반환하는데 이름은 µ 단위다. **지금까지 안 드러난 이유**: 4개 토폴로지 어디에도 `area_um2` 제약이 선언돼 있지 않고, `power_uA`는 objective(최소화)라 상수배가 순위를 안 바꾼다 | 실측(metric 값 vs 51소자 직접 합산) | **★ 시급**. v3.3/v3.4가 `area_um2 <= 2000`을 핵심 제약으로 도입하는데, 그대로 두면 2000µm² 의도가 **2000 m²**와 비교돼 항상 만족 = 제약이 없는 것과 동일해진다 → v3.3의 "면적 예산이 gm_id의 실질 상한" 논거, v4.2 DP의 면적 bin, v3.4 Pareto의 A_min/A_max가 **전부 무력화**. 선택지: ① metric이 이름대로(µA/µm²) 반환하도록 변환 ② 이름을 `power_A`/`area_m2`로 정정 ③ metric 선언에 `unit` 필드를 필수화하고 로드 시점에 이름-단위 불일치를 거부. **공유 엔진 동작 변경이라 사용자 승인 필요** |
| **A11** | **★ A10 조사에서 새로 발견: `gm/gds`가 `gm_id`에 단조가 아니다.** VDS 0.6/0.9/1.2/1.5에서 각각 6/8/11/12개 구간이 감소하고, 최댓값이 `gm_id ≈ 20.5/20.0/18.0/18.0`에 있다(VDS=0.4에서만 단조). 정점 위 구간은 **gain·면적 둘 다 나빠지고 전력만 좋아지는 지배당한 영역**이다 | LUT 정밀 스윕으로 확인 **2026-09-07 해소** — §7.9 해법을 **분리형 DP**로 교체(v4.2). "해석해"·"유일 결정" 표현 철회. `argmax(gm/gds)` 상한은 DP가 격자를 전수로 훑으므로 별도 상한 없이 자동 배제된다 |

### 10.3 미해결 — 구현·성능 (검토자 B, 코드 대조 완료)

| # | 내용 | 검증 상태 | 필요한 결정 |
|---|---|---|---|
| B1 | ~~§7.3 티어①이 실제 버그 경로를 안 지난다~~ → **2026-09-07 해소(v4.3)**. 계측 확증: `resolve_feed_vds()`는 51소자 중 **4개**만 정하고 **diode 소자는 0개**다(최대 경로는 `allocate_stack_headroom()` 28개). vds 기입 지점은 **7곳**이라 한 함수만 고쳐선 못 덮는다. diode를 `vds_match_vgs_of`의 **자기참조 특수 케이스**로 보고 기존 pre-pass를 확장 + 7개 지점을 `set_device_vds()` 단일 setter로 수렴(§7.3) | monkeypatch 실주행 계측 + 정적 전수 | **없음** — 설계 확정. 구현 시 grep 테스트로 원시 대입 잔존 금지 |
| B2 | ~~CMRR/PSRR을 stage-local 콜백으로 만들 수 없다~~ → **2026-09-07 해소(v4.4)**. 실측 확증(`KeyError: 'M6' 소자가 ctx.sized에 없다`). 13개 metric을 전수 분류해 **T1 stage-local 4개 / T2 stage-분해가능 1개 / T3 기약 전역 8개**로 나누고 게이트도 3티어로 재작성. `gain_stages_sum`이 정확히 분해됨을 확인(stage 합 = 전체, 차이 0.00e+00)해 DP가 대리가 아닌 **진짜 metric**을 쓸 수 있음도 확정. T3 게이트 1회 0.72 ms로 비용도 문제없음 | 실측 분류 + 비용 측정 | **없음** — §2.1의 `make_cmrr_psrr_feasibility_check()`는 삭제, `check_global_gates()` 신설 |
| B3 | **`resolve_stage_sizing()` 시그니처에 `vds`/`vs`가 없다**. 모든 LUT 호출이 필수로 요구하는데 §7.9 Phase 1의 VDS 예산이 §7.2/§7.6으로 전달되지 않는다 | 코드 확인 | `resolve_stage_sizing(stage_spec, ID, luts, vds_budget, vs_by_device, constraints)`로 확정 |
| B4 | ~~실행시간 예산 항목이 계획에 없다~~ → **2026-09-08 해소(v4.6)**. 직접 측정: **전체 평가 1회 274.5 ms**가 L_combo 단위 비용이다(stage 사이징 3.15ms로 세면 44배 틀린다 — 전역 게이트가 51소자 전부를 요구하므로). L 자유도 3개, 기본 정책(bounds 내 앵커 4개, 64 combo)에서 전수 17.6s / 중첩 포함 **2.9분**. densify 41점은 5.3시간이라 기본 금지. `presolve_warm_start()` 16.5s는 루프 밖 1회 규약. **부수 정정: R3의 "앵커 4개"는 stale이 아니었다** — LUT 전체는 7개지만 파일럿 theta bounds `[0.15,1.0]µm` 안이 4개라 둘 다 맞고 문맥이 달랐다(검토자 지적을 그대로 받았으면 잘못 고쳤을 것) | 실측 | **없음** — DoD에 wall-clock ≤ 5분 신설 |
| B5 | **C6이 사고19를 안 막는다**. 사고19의 underdetermined는 vertical_stack 내부 헤드룸 KVL(미지수 2/방정식 1)인데 `diagnose_sizing_dof()`는 gm_id/전류/L/Cc 넷만 세고 **VDS 미지수·KVL 방정식을 세지 않는다** | 문서 확인 | DOF 진단에 "stack별 (vds 미지수 vs KVL+참조 등식, 랭크)" 축 추가 |
| B6 | **§7.8 DOF 진단이 부등식을 등식처럼 센다**. 부등식은 활성일 때만 자유도를 소비하는데 목표 수만 세어 `overconstrained`면 **반복을 아예 시작하지 않는다** → 오탐 하나가 곧 hard stop | 문서 확인 | 등식 제약만 대조에 쓰고 부등식은 경고로 낮출 것 |
| B7 | ~~§7.5 프로토타입 "그대로 이식"은 과대평가~~ → **2026-09-08 확인(v4.10)**. 네 지적 중 **셋은 코드로 확인**(set 순회 / `not progressed and not unresolved` 논리오류 / 다중도달 일치검사 미구현 / VGS 3쌍 하드코딩). 다만 **set 순회는 이 회로에서 실제 차이를 만들지 않았다**(순회 순서를 뒤집어도 노드값 32개 전부 동일) — 잠재 위험이지 실현된 결함은 아니다. 반대로 **다중도달 미검사는 실물에서 위반이 나온다**: 21건 중 **4건이 243.5 mV 불일치**(Vop1/Vom1에 M2a/M2b/M3a/M3b 경로가 0.6565 vs 0.9000으로 도달). 프로토타입은 이걸 `elif`에서 검사 없이 discard한다 | 코드 확인 + 실측 | **없음** — "그대로 이식" 표현을 §2.1/§7.3에서 내리고, §7.5의 다중도달 검사가 잡아야 할 실물 위반 4건을 DoD 기준값으로 삼는다 |
| B8 | ~~§7.5가 KCL을 검증하지 않는다~~ → **2026-09-08 해소(v4.10)**. 실측: 내부 노드 30개 중 **3개**가 잔차 >1nA이고 **`Vx`(입력쌍 소스)가 −3.96µA**, 레일은 vdd −86.27 / gnd +88.93µA로 **2.66µA** 어긋난다. `_metric_kcl_residual()` 신설(부호규약 명시, `ideal_sources.value_amp` 포함, `value_amp=null`이면 지어내지 않고 그 노드 skip, `exclude_nets`는 이유를 선언에 적어야 함) | 실측 + metric 신설 | **없음** — `kcl_residual_uA`로 선언·배선(실측 **3.9601µA**). 상한 제약은 아직 안 건다(4개 회로에서 먼저 잰다) |
| B9 | ~~`vs`가 39소자에서 0.0~~ → **2026-09-08 원인 확정(v4.11), 수정 대기**. `vs`의 정의를 LUT 생성 넷리스트(정본)에서 확인: `xdut d g 0 b`로 **source는 항상 노드 0**이고 VS가 바꾸는 것은 벌크 전압(`vb_dc = vb_sign·VS·(−1)`)이라 **VS 축은 소스-벌크 역바이어스 |V_SB|**다. 벌크가 레일에 묶이면 NMOS는 `V_source`, PMOS는 `vdd − V_source`가 된다. 이 정의로 51소자를 검산하니 **25개 불일치**(일치 26개는 전부 source가 레일인 소자). 세 부류: ① 비레일 source인데 vs=0 — 최대 **−1.3000V**(M37a/M37b) ② 레일 source인데 vs≠0 — 4개(M60/M61/M38/M68) ③ **M9a/M9b·M18a/M18b는 값이 정확히 서로 바뀜**(M9a 기대 0.8060인데 0.6565, M9b 기대 0.6565인데 0.8060). **원인**: `_hr_resolve_vertical_group()`의 `other_entry.setdefault("vs", ref_vds)`가 **kind를 보지 않는다** — `ref_vds`는 vss 기준 체인의 VDS 합이라 NMOS엔 맞지만 PMOS엔 `vdd − V_source`여야 한다. 게다가 topology의 `device_roles[*].vs`(선언 0.0)와 이 전파가 **경쟁**해 어느 쪽이 이기는지가 순서에 달렸다(C2). C1(물리 미검증)+C4(kind 무시)+C2(순서 의존)가 한 줄에 겹친 자리 | LUT 넷리스트 + 실측 51소자 | **★ 수정 승인 대기** — 고치면 LUT 조회가 달라져 W/gm이 바뀌므로 재사이징이 필요하다 |
| B10 | **§7.10이 사고4 경계를 건드린다**. `select_L_by_role()`의 cascode/signal 거부는 사고4 정정의 결과이고 §5가 "별도 승인 필요"라 못박은 경계인데, §7.10이 이를 부수 효과처럼 없앤다 | 코드 docstring 확인 | 명시적 승인 필요 |
| B11 | ~~C1~C10 중 5개가 빈 약속~~ → **2026-09-08 해소(v4.5)**. 실측 확증: `review_needed`·"전역 유일성"·"connectivity에서 유도"가 각각 **C 표 안에서만 1회** 등장했다. 표를 **"강제 테스트" 열이 있는 형태로 재작성**하고, 지금 돌리면 실패하는 것(C1 16/16 tol 초과, C4 role만 바꿔도 vds 0.2/0.3/0.6, C5 게이트 19개 중 4개만 blind spot 명시)을 **실패한다고 적었다**. 담당 절 열은 제거(C7의 §5가 정반대 내용, C10의 §7.6에 캐시 서술 없음 — 어긋남이 반복되던 열) | 정적 grep + 실측 | **없음** — §4.1 DoD가 10개 테스트 전원 PASS를 완료 조건으로 건다 |
| B12 | **결정론 규칙이 계획에 없다**. `for name in set(...)` 패턴이 엔진에 아직 남아 있다 | 코드 확인 | §3.2 P1에 "모든 반복은 정렬된 시퀀스 위에서만" 규칙 + grep 테스트 추가 |
| B13 | **추적성**. 기존 엔진은 `_L_source` 같은 출처 태그를 남기는데, 새 파이프라인에서 vds/gm_id/L이 **어느 티어·어느 Phase에서 확정됐는지** 남기는 규정이 없다 → C2 사후 디버깅 불가 | 실측 확인 | `_vds_source`/`_gm_id_source` 태그를 DoD에 넣을지 |
| **B14** | `ideal_sources.value_amp` 정책 → **2026-09-08 사용자 확정(v4.12)**: **null이면 자유탐색, 값이 있으면 그 값을 실제 전류로 쓴다.** 파일럿 Iref는 1.2µA가 선언돼 있으므로 **고정 대상**이고, theta `r_biasgen`의 자유도는 그만큼 줄어든다. `kcl_residual`은 선언값이 있으면 그것을 실제 전류로 세므로 현재의 1.851배 괴리(선언 1.2µA vs 사이징 0.6484µA)가 **잔차로 드러난다** | 사용자 결정 | **★ 엔진 미구현** — 아직 `value_amp`를 소비하는 경로가 없다. B1+vs 구현 시 `seed_currents`로 배선한다 |
| **B15** | ~~★신규(v4.16)~~ → **① 2026-09-08 해소(v4.17), ③ 2026-09-08 완료(v4.18)**. ① leave-one-out 실측으로 **배열별** 결정(ID/GM/GDS=로그, CGG=선형) — gm/ID 곱선 오차 중앙 13.70→2.63%(pmos), 최악 17,884.9→33.6%. ③ L 앵커 7→12개(0.20/0.25/0.30/0.425/0.70 중간 삽입, 체크포인트를 L값 기반 이름으로 마이그레이션해 중간 삽입 제약 해소) | 원문 → **★신규(v4.16, 아무도 지적 안 함) — LUT의 L 보간이 PMOS gm/ID를 비물리 값으로 만든다.** `_gm_id_curve()`가 ID는 로그·GM은 선형으로 보간해 두 보간이 불일치한다. 앵커 사이에서 PMOS gm/ID가 **403 / 5,517 / 56,646**까지 오른다(물리 상한 ≈30~38). PMOS는 L=0.15↔0.35µm에서 같은 VGS의 ID가 6자릿수 차이(DIBL, 물성은 정상)라 기하평균 vs 산술평균 괴리가 **207배**로 증폭된다. NMOS는 무사. `L_stage2out_p`/`L_cascode` theta가 이 대역을 5nm 격자로 실제 탐색한다 | 실측(`tests/probe_lut_L_interpolation.py`) | **★ B1 재탐색의 차단 사유** — §0.3이 예상한 해(`L=0.15~0.45µm`)가 정확히 오염 대역이다. 후보 ①일관보간(폭발 제거·앵커 보존, 그러나 정확도 미보장) ②앵커 고정(유효 앵커 4개뿐) ③LUT 재생성(근본 해결, 중간 삽입 제약) — **전부 승인 대상** |
| **B16** | ~~step 2 재설계 필요~~ → **2026-09-08 해소(v4.17)** — `apply_diode_self_consistent_gm_id()` 신설·배선(gm_id_role 루프 직전), 헤드룸 배분기에 `diode_vds_window()` 구간 제약 추가. 원문 → **step 2 재설계 필요 — 헤드룸 시점에 diode의 `gm_id`가 없다(0/16 실측).** §0.2 step 2가 전제한 `solve_diode_connected_vds(gm_id, ...)` 호출이 그 시점에 불가능하다. 다만 `Vgs=Vds` 구속은 양방향이라 `gm_id = lut.gm_id_for_vgs(vds, L, vds, vsb)`(O(1), 기존 함수)로 **현재 순서를 유지한 채** 배선 가능하다 — 80점 왜복 검산에서 76점이 오차 1mV 미만으로 일치(어긋난 4점은 B15 오염 대역) | 실측(`tests/probe_diode_gmid_readiness.py`) | **diode의 gm_id를 자유 탐색 변수에서 제외**하고 종속값으로 확정하는 것이 대가 — 승인 필요 |
| **B17** | ~~★신규(v4.19)~~ → **2026-09-08 해소**. 엔진이 `matching_pairs`에 **L만 전파하고 gm_id는 전파하지 않았다** — VDS는 `same_as_device`/vertical stack이, W는 gm_id가 결정하므로 **gm_id 하나만 무방비**였다. 매칭 쌍 21개 중 6개가 갈리고, 그중 3쌍(M2a/M2b, M3a/M3b, M37a/M37b)은 `L/ID/vds/vsb`가 전부 같은데 gm_id만 다르다(한쪽은 권위 있는 출처, 다른 쪽은 `gm_id_role` 루프의 독립 탐색). L 전파 루프와 같은 구조로 gm_id 전파를 추가하되 **동작점이 완전히 같은 쌍만** 대상으로 좁혔다 | 실측(`tests/probe_matching_pair_divergence.py`) | **없음** — 갈리는 쌍 6→3개, 면적 1050.40→936.38µm², 레이아웃 복구가 더 이상 W를 안 건드린다 |
| **B18** | ~~★신규(v4.19)~~ → **2026-09-08 해소**. 레이아웃 재검증이 **전역 metric을 통째로 건너뛰었다** — `_collect_device_refs()`가 spec에 이름이 적힌 소자만 모으는데 `area_um2`처럼 `devices`를 안 쓰는 metric은 참조가 빈 집합이라 "무관"으로 분류됐다. 전 소자를 쓰는데 건너뛴 metric 6개(`power_uA` 목적함수 포함) + 소자 미명시로 건너뜀 전체회로 metric 3개(`cmrr`/`psrr` 제약 포함). 선언된 제약 5개 중 `gain_db` 하나만 재검증되고 있었다. **전부 재계산으로 전환**(비용 실측: 8회 호출 × 1.6ms = 전체의 0.01%) | 실측(`tests/probe_revalidation_scope.py`) | **없음** — 면적 제약이 실제로 지켜진다(cap 800에서 792.87µm²) |
| **B19** | **★신규(v4.19) — 미러 3그룹의 VGS가 물리적으로 불가능하게 벌어져 있다.** (v4.20 정정: 11소자가 아니라 **18소자**다 — 아래 B19' 참고.) `M18_bg/M8/M13/M17/M22/M60/M61`(PMOS, gate=Vbias1, source=vdd)과 `M10/M12/M19/M21`(NMOS, gate=Vbias4, source=gnd)은 게이트·소스를 공유하는 **진짜 전류미러**라 VGS가 KVL로 강제 동일해야 하는데, 사이징은 최대 **464mV** 벌려놓았고 미러 규약(ID비==W비)도 전부 깨다(M8은 1530배). 세션38의 `gm_id_match_vgs_of`와 같은 클래스인데 이 소자들은 그 필드가 없다 | 실측(`tests/probe_ratio_pair_analysis.py` → `probe_mirror_design_space.py`) | **2026-09-09 결론 번복 — 성립한다. 회로 설계 판단이 아니라 배선 과제다.** 설계공간을 실제로 훑으니 세 그룹 모두 해가 있다(아래 B19' 참고) |
| **B19'** | **★신규(v4.20) — B19의 대상과 결론이 둘 다 틀렸다.** ① **대상**: 앞선 조사는 `symmetry.matching_pairs`에 **선언된** 그룹만 봐서 11소자로 셌는데, VGS 동일 강제는 선언이 아니라 게이트·소스 공유라는 connectivity에서 나온다. 넷리스트를 전수로 세면 **18소자 3그룹**이고, **6소자(`M5 M6 M7 M38 M66 M68`)는 어떤 matching_pair에도 안 나온다** — 그중 **M6/M5는 diffpair tail**(회로의 주 전류), **M66은 NMOS 그룹의 diode 레퍼런스**(즉 그 그룹은 레퍼런스 없이 분석됐다), **M7/M36a 그룹은 통째로 누락**(M36a는 이 계획서 Executive Summary가 지목한 원래 버그의 대표 소자다). ② **결론**: VGS를 현재값에 고정한 채 물었고, W를 깨진 `gm_id_to_id_density()`로 구했다(B20). VGS를 자유변수로 두고 다시 재면 **세 그룹 모두 성립**한다 — PMOS Vbias1 20조합/최소 22.90µm²(L=0.20µm, VGS=0.75V, gm_id 15.42~15.70), NMOS Vbias4 9조합/50.28µm²(L=0.15µm, VGS=0.55V), PMOS Vcmfb 36조합/0.77µm². 합 **73.95µm²**인데 **지금은 M18_bg 혼자 38.6µm² + M66 혼자 61.6µm²**라 제대로 강제하면 **면적이 오히려 준다**. 부수: `k_Iref`는 지렛대가 아니다(0.25~15배에서 성립조합 20→13개, W∝ID라 비율이 안 변함) — 진짜 지렛대는 **공유 VGS**다. B9(vsb)는 NMOS 그룹을 최대 **8.07배** 부풀린다(M38의 vsb가 0이어야 하는데 0.8625) | 실측(`tests/probe_mirror_design_space.py`) | **✅ 2026-09-09 사용자 확정 — 둘 다 답을 받았다.** (가) **18소자 전부를 미러로 강제한다. tail M5/M6를 bias 미러에 묶는 것이 설계 의도다.** (나) **공유 VGS는 gain 기준으로 고른다** — 면적이 아니다. 근거(사용자 원문): "첫번째 differential input 단의 tail이기 때문에 gain에 직접적으로 영향을 미치는 id전류를 만들고 있어." 따라서 `probe_mirror_design_space.py`가 준 **면적 오름차순 랭킹은 기준이 틀린 것**이고, `probe_mirror_gain_ranking.py`가 같은 조합을 엔진의 실제 `gain_db`로 다시 줄 세운다. 남은 것은 배선뿐 — 기전은 이미 있다(nmcnr M203/M204의 `gm_id_match_vgs_of`, 세션38과 같은 클래스). **다만 B20이 미해결인 채로 배선하면 PMOS 2개 그룹의 W가 깨진 경로로 계산된다 — B20이 먼저다.** **2026-09-09 gain 랭킹 실측(6480조합)**: gain 최적은 두 신호경로 그룹 모두 **L=4.0µm**(PMOS VGS=1.10 / NMOS VGS=0.60)이고 `gain_full_circuit_db` **89.82dB**(미러면적 1775µm², 전체 2535µm²). 면적 최소 조합(73.95µm²)은 63.72dB로 **gain 순위 6423/6480 = 사실상 최악** — 기준을 바로잡지 않았으면 정확히 반대로 골랐다. 그룹별 지렛대: pmos:Vbias1 폭 20.8dB / nmos:Vbias4 폭 20.0dB / **pmos:Vcmfb 폭 0.0dB**(CMFB 경로라 gain과 무관 — 이 그룹만은 gain이 기준이 될 수 없고 다른 기준이 맞다). **그리고 gain 최적점 L=4.0µm가 정확히 B20이 가장 심하게 무는 구간**이라, B20 선행은 순서 위생이 아니라 실질이다 |
| **B20** | **★신규(v4.20) — `_solve_vgs()`가 단조를 전제하는데 PMOS LUT는 비단조다. W가 조용히 틀린다.** `_solve_vgs()`는 docstring에 "gm/ID는 VGS에 단조감소"라 적어놓고 `np.argsort(gm_id_vals)` 후 `np.interp`로 역보간한다. 비단조이면 **서로 다른 branch의 VGS가 정렬에서 뒤섞여** VGS 축에서 인접하지도 않은 두 점 사이를 보간한다. 이 함수는 `gm_id_to_id_density()`(=`W = L*ID/IDu`의 분모)·`gm_gds_ratio()`·`fT()`·`cgg_absolute()`가 전부 첫 줄에서 부르므로 **모든 W 계산의 뿌리**다. raw LUT(보간 없음)에서 확인: PMOS L=0.15µm/VDS=0.90에서 gm/ID가 VGS 0.41→0.64 구간에 14.19→15.34로 **오르다** 꺾인다(ID 자체는 단조증가라 데이터가 깨진 건 아니다 — 저전압 쪽 누설로 보인다). **NMOS는 전 구간 단조라 무사하다.** 범위: `VDS>=0.15` 격자 2700점 중 비단조 75.3%인데, 상승 대부분이 약반전 꼬리(gm/ID 26~31)라 그것만 보면 과장이다 — **탐색범위 `gm_id_grid`(4~24)와 겹치는 것은 53.6%**이고 겹칠 때 중앙값 폭이 **20.0**(=탐색범위가 통째로 이중값). 위험은 두 축에 몰린다: **vsb**(0V 43.3% → 0.8V **95.7%**)와 **긴 L**(L=0.30~1.00µm는 완전 단조인데 L=1.5/2.5/4.0µm는 전부 탐색범위와 겹침). 파일럿은 theta bounds가 `[0.15,1.0]µm`이고 대부분 vsb=0이라 거의 안 물리지만 **실제로 2소자가 물렸다**: `M18a`/`M9a`(vsb=0.8003, vds=0.0587)의 W가 1.0177µm인데 강반전 branch의 올바른 해는 0.4306µm — **2.36배**, 오류 없이 조용히 | 실측(`tests/probe_gm_id_monotonicity.py`) | **✅ 2026-09-09 해소(사용자 승인 후 수정)** — `_solve_vgs()`를 **rightmost root**로 재작성했다(목표를 품는 가장 오른쪽 구간에서만 보간, 곡선 범위 밖이면 명시적 실패이며 비단조 사실을 오류 메시지에 적는다). 검증 4건: ① 문제 지점 VGS 1.3124→**1.5047V**로 독립 계산한 올바른 해와 일치 ② **NMOS 전 격자 16,186건 구/신 완전 동일**(같은 방향·같은 연산 순서 `slope*(x-x0)+y0`로 구현) ③ `two_stage_ota` 실주행에서 달라진 조회 **1,895건이 전부 긴 L(2.9~3.7µm)**이고 **Δ가 전부 양(+)**(강반전 해로 이동) — 최악은 `gm_id=6, L=3.71µm, vds=0.30`의 **0.719→1.333V** ④ 파일럿 재탐색 정상 완주, 제약 5개 전부 만족. 비용 실측: 호출 1회 4.95→5.85µs(1.18배)인데 이 함수가 평가 1회(465ms)의 14.0%라 **순증가는 2.55%**. 기준선 2개는 각 1줄씩 의도적 갱신(사유는 `tests/baseline/README.md` 갱신 이력) |
| **B20 보강** | **2026-09-09 추가 실측 — 선택지 ①을 그대로 쓰면 안 된다.** "정점 오른쪽만 쓰면 단조"라고 가정했는데 실제로는 비단조 2032점 중 **682점(33.6%)만** 그렇다. 나머지 1350점은 정점 오른쪽에도 상승이 있다. 다만 그 크기를 재보니 **중앙 0.606% / 90분위 2.03% / 최대 2.20%**(상승 횟수 중앙 2회)로 **LUT 수치잡음**이지 별개 branch가 아니다 — 약반전 쪽 주 봉우리(8% 규모, VGS 0.50 vs 0.71로 IDu가 170배 갈림)와는 성격이 다르다. **따라서 올바른 정식화는 "정점 오른쪽을 자른다"가 아니라 "가장 큰 VGS 해(rightmost root)를 취한다"다** — 2% 잡음이 만드는 미세 교차는 VGS 축에서 서로 인접해 오차가 무시할 수준이고, 목표가 전역 최댓값을 넘으면 해가 없어 깨끗하게 실패한다. 선택지 ②는 단독 불가(탐색범위와 겹치는 동작점 53.6%라 파일럿이 즉시 멈춘다), ③은 데이터를 바꿔 진짜 약반전 설계를 막는다 | 실측 | **추천: ①′ rightmost root + 전역 최댓값 초과 시 명시적 실패**. 승인 필요 |
| **B21** | **★신규(v4.22) — 선언된 gain 제약이 미러 18소자를 구조적으로 못 본다.** `gain_db`는 `{"type":"gain_stages_sum","stages":[["M1a","M4a","M2a","M3a"],["M15","M16"]]}`로 **소자 6개**만 더한다. 미러를 (L,VGS) 6480조합으로 강제해도 `gain_db`는 **65.5547dB로 완전 불변**(Δ=0.0000)인데, 같은 조합에서 전체회로 MNA `gain_full_circuit_db`는 **63.67~89.82dB로 26.15dB 벌어진다**. 그런데 `M19.drain=Vom1`, `M10.drain=Vop1` — **stage1 출력노드 그 자체**라 그 gds가 이득을 직접 깎는다. 즉 **선언된 제약 `gain_db >= 54`는 26dB짜리 실효과에 눈이 멀어 있고**, 목적함수(`power_uA` 최소화)는 그 눈먼 제약만 지키면 되므로 미러를 마음대로 나쁘게 만들 수 있다. (위생검사: 같은 스윕에서 `area_um2`는 6480개 전부 다른 값 → ctx 패치는 metric에 정상 반영됨. 즉 Δ=0은 진짜 무감도다.) B18(재검증이 전역 metric을 건너뜀)과 같은 클래스지만 이건 **metric 선언 자체의 범위** 문제다 | 실측(`tests/probe_mirror_gain_ranking.py`) | **★ 결정 필요** — ① 제약을 `gain_full_circuit_db`로 바꾼다(정확하지만 매 평가에 MNA) ② `gain_db`의 `stages`에 부하 소자를 추가한다(누가 부하인지 판정 규칙 필요 = G6와 같은 문제) ③ 둘 다 제약으로 걸고 괴리를 metric으로 감시. §10.2 A6/§10.4 G6와 얽힌다 |
| **B22** | **★신규(v4.24) — B19' 배선이 드러낸 다음 차단막: `diode_vds_window()`가 diode 자신의 W_bounds만 본다.** 미러 15소자에 `gm_id_match_vgs_of`를 선언해 실제로 배선했더니(그 자체는 정상 동작 -- 15소자 전부 강제되고 레퍼런스 3개 자격 OK) **SLSQP 40회 전부 infeasible**이고 이어서 레이아웃이 `cmfb_tail`(M37a/M37b/M38)에서 공통 finger 폭을 못 찾는다. 원인을 소자 단위로 규명: 미러가 강제되면 그룹 VGS가 diode 레퍼런스의 VDS로 통일되는데, **헤드룸 배분기가 diode에 구간의 `lo`를 준다**(`allocate_stack_headroom()` docstring이 이미 경고하고 있었다 -- "`lo`를 고르는 것은 **면적을 크게 잡는 쪽**이다(W(v)가 감소함수라 lo↔W최대)"). 미러 강제 전에는 그게 diode 혼자의 면적 문제였지만, **이제 그룹 전원의 W를 결정한다**. 실측: 6소자가 상한을 초과하고 최악이 66.7배다 — `M8`/`M17` 1427.9µm(7.1배), `M10`/`M19` 2153.0µm(10.8배), `M5` 12623.3µm(63.1배), `M38` 13339.9µm(66.7배). 필요한 VGS는 **pmos:Vbias1 ≥ 0.80V**(현재 0.675), **nmos:Vbias4 ≥ 0.55V**(현재 0.375)이고, `pmos:Vcmfb`는 지금도 성립한다(M7이 1.2µm). 부수 확인: 그룹 안에서 **L이 갈린다** — `L_role="mirror"`는 `L_min×2.5=0.375µm`, `bias_replica`는 `×1.2=0.180µm`인 **하드코딩 상수**(`_L_ROLE_MULTIPLIERS`)라 theta가 아니다 | 실측(`tests/probe_mirror_infeasibility.py`, `probe_mirror_wiring_readiness.py`) | **✅ 2026-09-09 구현 완료(사용자 승인)** — `diode_vds_window(..., mirror_members=())`로 확장. 후보 vds마다 diode 자신뿐 아니라 **VGS를 공유하는 소자 전원**의 W가 한계 안인지 본다. 설계 결정 3건: ① **선언 기반 옵트인**(connectivity가 아니라 `gm_id_match_vgs_of` 선언을 본다 — 미배선 self-test **diff 0줄**로 무영향 확인) ② 종속의 vds가 아직 미정이면(헤드룸이 스택별로 풀리는데 diode 스택이 **가장 먼저**라 실측상 종속 7개 전부 미정) **역할별 `min_vds`를 바닥으로** 쓴다 — IDu가 vds에 증가함수라 안전한 방향이고 보수성 대가는 실측 **격자 한 칸(0.0375V)** ③ 종속의 L/ID가 미확정이면 **조용히 건너뛰지 않고 명시적 실패**(§3.2 P1). 부수로 `id_density_at_vgs()` 신설 — VGS를 아는 호출자가 `gm_id_to_id_density()`로 왕복하면 비단조 구간에서 다른 branch로 튄다(B20). **효과 실증**: 같은 theta에서 배선+B22끔은 `area_um2`가 **655,086µm²(=655mm²)**인데도 **통과한다**(파일럿 제약 목록에 area가 없다) — B22가 그 조용한 부조리를 명시적 실패로 바꾼다 |
| **B23** | **★신규(v4.25) — B19'+B22가 성립하려면 B9(vsb 오산출)가 먼저다. 실측으로 확정.** B22를 켜니 파일럿에서 `M66`의 창이 비었다. 진짜 물리적 불가능인지 확인하려고 후보 vds마다 어느 멤버가 막는지 전수로 찍었더니, 막는 것은 **`M38`(ID=23.73µA)이고 그 멤버의 `vsb=0.8625V`** 였다. `M38`은 넷리스트상 **source=gnd**라 vsb가 0이어야 한다 — B9가 이미 지목한 그 4소자(M60/M61/M38/M68) 그대로다(이번 덤프에서 `M68`도 vsb=0.2000으로 확인). 가짜 바디바이어스가 Vth를 올려 **같은 VGS에서 전류밀도를 55배 낮게** 보이게 만들고, 그래서 W가 13,340µm로 튀어 창이 빈다. **물리 vsb=0으로 재면 이 그룹은 성립한다**(`probe_mirror_design_space.py`가 이미 그렇게 쟀다 -- nmos:Vbias4 성립조합 9개). 즉 B19'/B22가 틀린 게 아니라 **입력이 오염돼 있다** | 실측(`tests/probe_b22_headroom_attribution.py` + `.window_dump.txt`) | **없음(순서만 확정)** — 작업 순서는 **B9 -> B19' 배선(스크립트 보존됨) -> 재탐색**이다. B9는 §10.3에서 이미 "★ 수정 승인 대기"였고, 이제 그것이 미러 작업의 **선행 조건**임이 실측으로 확정됐다 |
| **B24** | **★신규(v4.26) — B9를 실제로 고쳐봤다. 계산은 맞는데 그 뒤가 회로 판단이다.** ① **현재 상태를 처음으로 정확히 쟀다**(`tests/probe_node_voltage_audit.py`를 낡은 instance.json 대신 **지금 엔진으로 새로 사이징**해서 재도록 고침 — 그 전엔 세션18 산출물의 옛 필드 `vs`를 읽고 있었다): 51소자 중 **26개 불일치**, 세 부류로 갈린다 — **(가) 소스가 레일인데 vsb≠0 4개**(`M38` +0.8625 / `M60` +0.3750 / `M61` +0.2000 / `M68` +0.2000), **(나) 소스가 비레일인데 vsb=0 15개**(`M40` −0.9375, `M2a`/`M2b` −0.7997, `M37a`/`M37b` −0.7375 …), **(다) 그 외 7개**(`M9a`/`M9b`·`M18a`/`M18b`는 값이 정확히 **서로 바뀜**). 노드는 36개 전부 해소되고 다중도달 불일치는 4건(전부 정확히 +99.7mV). ② **수정 구현**: `reconcile_vsb_from_nodes()` 신설 — 헤드룸이 끝나 vds가 전부 확정된 시점에 `propagate_node_voltages()`+`derive_vsb_from_nodes()`로 vsb를 다시 유도해 덮어쓰고, 소스 전압을 못 구하면 0.0으로 때우지 않고 **명시적 실패**한다. 그리고 `audit_vsb_consistency()`를 파이프라인 **게이트로 배선**했다 — 이 두 함수는 세션46에 만들어졌는데 **엔진 호출부가 하나도 없었다**(★절대원칙 위반 상태였다). ③ **결과**: 올바른 물리가 적용되자 `M11b`(class-AB battery의 적층 PMOS diode, vsb 0.0→0.6750)가 **W=6342µm**를 요구해 파일럿이 성립하지 않는다. 헤드룸 시점에도 노드전압으로 vsb를 구하도록 한 곳 더 고쳐봤으나 M11b의 소스 노드는 그 시점에 아직 복원되지 않아 같은 결과다 | 실측(`tests/probe_node_voltage_audit.py`) | **★ 회로 설계 판단 필요 — 혼자 진행하지 않음.** 남은 것은 "바디효과를 제대로 넣으면 M11b가 지금 예산으로는 성립하지 않는다"이고, 선택은 그 스택의 vds 예산 / `L` / 전류 중 무엇을 바꿀지다(B19'가 `Iref` 대신 공유 VGS였던 것과 같은 성격). 엔진 변경분은 `tests/b9_vsb_from_nodes.patch`(166줄)로 보존했고 저장소는 되돌려 self-test 2개 모두 diff 0줄이다 |
| **B25** | **★신규(v4.27) — A8의 "연립 solver는 필요 없다"는 재해석이 틀렸다. 적층 diode는 vsb로 결합돼 있다.** class-AB 배터리 4스택이 전부 **적층 diode**다(vom/vop × PMOS/NMOS 대칭): `vdd→M11a→M11b→M12→gnd`, `vdd→M13→M14a→M14b→gnd`와 그 vop 쌍(M20a/M20b/M21, M22/M23a/M24b). 적층이라 **아래쪽 diode의 vsb = 위쪽 diode의 vds**이고(M11b.vsb = VDS(M11a) = 0.675V), 그래서 M11a와 M11b는 같은 전류·같은 L·같은 VGS인데 **M11b가 61.3배 넓어야 한다** -- 차이는 오직 바디효과다. v4.13이 A8을 "diode의 Vgs는 종속값이라 연립이 아니라 제약 추가로 처리"로 재해석했는데, **그 재해석은 vsb 결합을 못 봤다**. ② **실측한 선택지**(`tests/probe_stacked_diode_options.py`): **전류는 지렛대가 아니다**(0.235~1.765배 전 구간 실패 -- W가 두 소자 모두 ID에 비례해 61배 비율이 안 변한다, B19'의 `Iref`와 같은 구조). **L은 PMOS만 고친다**(`bias_replica` 0.180µm → M11b 6342→**20.00µm**, 그러나 NMOS는 1882→1687µm로 거의 안 변한다 -- NMOS 배터리는 diode에 0.375V씩만 가고 M13이 1.05V를 가져가 깊은 약반전이라 L이 상쇄된다). ③ **결정적**: `(v_a, v_b)`를 **연립으로** 고르면 PMOS는 L=0.180µm에서 **60조합**, NMOS는 **현재 L 그대로 32조합**이 성립한다(최적 각각 (0.675/0.825/0.300) W 2.32/1.42µm, (0.562/0.675/0.562) W 1.52/1.52µm). 즉 **설계 변경이 더 필요한 게 아니라 배분을 함께 풀기만 하면 된다** | 실측(`probe_stacked_diode_options.py` + 배선 시험) | **★ 승인 필요(공유 엔진)** — `diode_vds_window()`가 diode마다 **독립적으로** 창을 계산하고 그때 vsb를 모른다(실측: 계산된 창의 vsb가 전부 0.0/0.2였고 실제값 0.675/0.375가 아니었다). 그래서 배분기가 고른 `lo`가 결합 제약을 위반한다(M11b W=924µm). 필요한 것은 **같은 스택의 적층 diode를 2변수로 함께 푸는 것**(아래쪽 vsb=위쪽 vds). **✅ 2026-09-09 구현 완료** — `solve_stacked_diode_pair()` 신설(위/아래 vds를 함께 훑고 아래쪽 vsb를 위쪽에서 유도) + 헤드룸 배분기 배선 + B9(vsb 노드전압 유도) 동시 적용 + `L_role: bias_replica`(M11a/M11b/M20a/M20b). **파일럿 평가 성공**: gain_db 65.5547(≥54), area_um2 **847.45**(925.52에서 **감소**), cmrr 66.12(≥60), psrr 81.38(≥60), power 258.82µA. vsb 감사 게이트도 통과. 구현 중 실측으로 바로잡은 것 셋: ① 결합식이 `vsb_lo = v_up`이 아니라 **`vsb_lo = vsb_up + v_up`**(직렬이면 역바이어스가 누적된다 — 위쪽 소스가 레일일 때만 둘이 같아서 배터리 쌍에서는 우연히 맞았다. 검산: M58(vsb 0.2, vds 0.2) 아래 M57은 vsb 0.4) ② 쌍의 합에 **스택 예산 상한**이 필요하다(cmfb_vocdes_gen에서 1.837V>1.8V) ③ 쌍이 스택의 전부면 합이 예산과 **정확히 같아야** 한다(≤로는 0.2625V가 남는다) ④ 위쪽이 **diode가 아닌 경우도** 대상이다(M57←M58, M64←M63 — 위쪽 W는 제약하지 않고 최소 vds만 지킨다) ⑤ 위쪽 소스가 레일이 아니면 그 vsb가 **다른 스택이 정한 노드**에 달렸다(M58의 소스 Vx는 diffpair_branch_a 소관) — 노드전압으로 유도해야 한다. **잔여**: self-test L5c 픽스처의 고정점(거의 모든 theta를 중점에 고정한 인위적 단일 점)만 막힌다 — 그 점의 M39/M40 전류에서는 최소합 1.837V로 몫 1.8V를 넘는다. 파일럿(자유 탐색)은 통과하므로 설계 문제가 아니라 **픽스처 문제**다. **2026-09-09 추가조사("2번 봐")**: L5c만 막히는 원인은 **그 점의 M39/M40 전류가 파일럿의 17배**라는 것이다(8.197µA vs 0.47µA -- 픽스처가 `r_cmfb_vocdes`를 bounds 중점 0.11에 고정하기 때문). **M39/M40의 `L_role` 변경은 해법이 아님이 실측으로 확인됐다** -- 두 동작점을 동시에 만족하는 L이 없다: `mirror`(0.375µm)면 파일럿 OK / L5c 실패(최소합 1.837>1.8), `bias_replica`(0.180µm)면 L5c OK(정확 1.8V 쌍 8개) / **파일럿 실패**(성립 합 1.05~1.24 < 1.8). 즉 문제는 L이 아니라 **픽스처의 고정 전류**다. 부수 개선: 정확 일치를 격자점 쌍에서만 찾던 것을 **`v_lo = 예산 - v_up`으로 연속 평가**하도록 보완(LUT는 VDS를 연속 보간하므로 격자 양자화는 물리가 아니다). 변경분은 `tests/b25_b9_stacked_diode.patch`(388줄)로 보존 |
### 10.4 미해결 — 일반성 (검토자 D)

**판정**: 이 방법론은 "임의 토폴로지"가 아니라 **"차동 입력 + 캐스코드/미러 부하 + 2단 Miller
보상 전압증폭기"** 한 부류에 맞춰져 있고, 그마저도 파일럿 1개를 정본으로 일반화한 것이다.
D2(gain metric 위임)로 가장 큰 차단 요인은 풀렸으나 아래가 남는다.

| # | 반례 | 어디서 막히나 | 처리 방향 |
|---|---|---|---|
| G1 | **단일단(5T/텔레스코픽)** | `compensation: null`(folded_cascode가 실제로 그렇다)이면 `gm_i`의 출처가 사라져 §7.9 인과사슬이 끊긴다 | `compensation: null`을 1급 케이스로 명시하고 그때 gm의 출처(GBW×CL 또는 gain 제약)를 §7.9에 정의 |
| G2 | **3단 이상 중첩보상(NMCNR — 저장소에 있음)** | `solves_for:["Cc","Rz"]`·`stage_gm_ref` 2개가 2단 하드코딩. `Rz=1/gm2`가 **범용 DOF 계수기 본문**에 상수로 박혀 있다. NMCNR의 자유도 `kg=gm2/gm3`를 선언할 자리가 없다 | `compensation`을 stage 수 종속으로 일반화, 종속관계를 `topology_fn` 메타데이터로 이동 |
| G3 | **Gain-boosted cascode** | §7.9의 "④ VDS 예산만이 유일한 설계 자유도"라는 출발 명제를 직접 반증한다(⑤ 캐스코드 부스트를 설계 변수로 만드는 기법) | `stages[].boost_amp` 재귀 또는 명시적 범위 밖 선언 |
| G4 | **class-AB 정지전류** | `ID_source ∈ {kcl, ideal_source_ref}`뿐인데 Monticelli 정지전류는 **VGS 합(KVL)**이 정한다. `ID_final = max(KCL, SR×CL)`은 class-A 규칙이라 class-AB 정지점을 파괴한다 | `ID_source.type`에 `kvl_battery_loop` 추가, `driving_spec.output_class ∈ {A, AB}` 신설 |
| G5 | **폴딩 노드** | `folded_cascode`의 gain metric은 역할을 **5종**(`gm1_device`/`fold_leg_a`/`fold_leg_b`/`cascode_p`/`cascode_n`/`mirror_n`)으로 요구하는데 서브롤은 4종이다. `fold_leg_b`가 어디에도 안 들어간다 | 서브롤 확장(+`follower`/`common_gate`/`floating_current_source`/`voltage_divider`) |
| G6 | **stage 분할 규칙이 없다** | 문서 어디에도 stage 경계 정의가 없다. §8.3은 `stages[]`가 이미 있다고 가정하고, §13.3의 5신호(원래 "미러 다리 matching vs gain-load" 판정용)를 input/cascode 분류기로 전용해 **신호2가 입력 차동쌍에 먼저 걸린다**(입력쌍이 cascode로 분류됨). `input↔load` 구분·`tail` 판정 규칙도 없다 | "stage 분할은 사람이 확정하는 입력"임을 명시하거나 진짜 판정 규칙을 세울 것. §8.3의 5신호 전용은 **철회** 권장 |
| G7 | **비증폭 회로**(밴드갭·constant-gm bias·비교기·SC) | §2.2가 회로 부류를 하나도 배제하지 않아 암묵적 보편성을 주장한다 | §2.2에 "Out of Scope — 회로 부류" 절 신설. 이들은 배제하는 편이 옳다 |
| G8 | **새 토폴로지 추가 비용이 문서화돼 있지 않다** | §8.3은 "JSON 두 개 쓰면 끝"처럼 읽히나 실제로는 gain metric·CMRR/PSRR estimator·`topology_fn`을 각 레지스트리에 등록하는 **엔진 작업 3~4곳**이 필요하다 | §8.3에 그 목록을 명시 |

### 10.5 정합성 잔여 (검토자 C)

v4.0에서 §1.5 참조 4곳·`schema_version`·"무변경 재사용" 2곳·§8.8 기준선 서술을 고쳤다.
남은 것: 유령 함수 3개(`allocate_headroom_budget()`/`measure_stage_gain_ceiling()`/
`redistribute_headroom_by_gain_gradient()` — §6.1에 1회씩만 등장, 본문에 정의 없음, §7.9는
같은 기능을 다른 이름으로 서술), 삭제 선언한 `gain_allocation`/`gain_allocation_check`의 잔존
(L794/L1150), §2.2 vs §4.1 C7의 범위 충돌(파일럿 1개 vs 4개 전수), §7.9 3-Phase 순서와 §8.4
harness 순서의 불일치(§8.4에 Phase 1이 없고 되먹임을 금지), 신규 함수 목록 3중 관리
(§2.1/§6.1/각 §7 절 말미), `closed_loop_accuracy_db`·`stage_gm_ref`·`vdd_kvl` 미소비 필드,
`slew_rate_v_per_us` vs `slew_rate_target`·`battery_centering_deviation` vs
`classab_centering_dev_v` 명칭 흔들림, §7.10 측정2 표의 빈 헤더.


### 10.6 spec 정본화 — 2026-09-10 사고와 재발 방지 (★ 신설 v4.34) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.7 class-AB 배터리 헤드룸 + 기준점 복구 (★ 신설 v4.35) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.8 §7.11 L2 완성 — 보상망을 실제로 세고, Cc를 유도한다 (★ 신설 v4.36) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.9 미러 공통 L -- 3층 구조 (★ 신설 v4.37, 층1/2/0 착지 · 층3 미완) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.10 층3 착지 -- 동치류 공통 L을 theta로 파생 (★ 신설 v4.38) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.11 `_L_ROLE_MULTIPLIERS` 완전 제거 -- knee를 실현가능 창으로 clamp (★ 신설 v4.39) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.12 웜스타트에 `l_class` 포함 -- 두 번의 되돌림 (★ 신설 v4.40) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.13 미러비 계통오차에 상한 -- **숫자를 박지 않고** (★ 신설 v4.41) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.14 입력환산 오프셋 + 달성 가능 임계값 유도 (★ 신설 v4.42) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 10.15 임계값 bisection -- 설계만 (★ v4.42, 구현은 design 단계 이후)

#### 왜 bisection이 위 두 실패를 모두 피하나

§10.14가 실패한 두 방향은 **문제를 바꿔서** 물었다:

    sigma를 objective로 최소화   -> 다른 제약(parasitic_pm_deg)과 정면충돌
    제약을 떼고 원래 objective   -> 아무도 안 막으니 sigma가 드리프트

bisection은 **문제를 안 바꾼다**. objective도 그대로, 제약도 그대로 두고 **임계값 `B`만**
움직이며 매번 원래 탐색을 돌려 묻는다: *"`B`에서도 이 설계가 존재하는가?"*

#### 왜 원리적으로 성립하나 (단조성 보장)

임계값을 조이면 실행가능 집합은 **줄어들기만 한다**(`{x : m(x) <= B}`는 `B`에 대해 단조
증가하는 집합족). 따라서 "실행가능한 `B`"는 위로 닫힌 구간이고, 그 **하한이 유일하게
존재**한다. 즉 이분탐색이 수렴할 대상이 실제로 있다 -- `sigma`를 최소화하는 것(다른 제약과의
경쟁이라 최소점이 실현가능하다는 보장이 없다)과 근본적으로 다르다.

⚠️ 단조한 것은 **실행가능성**이지 탐색기의 성공 여부가 아니다. SLSQP는 실행가능해도 못 찾을
수 있으므로(이 회로는 3-start 중 1개만 수렴하는 게 보통), "실패 = 실행 불가"로 단정하면 안
된다. 그래서 아래 (4)에 **conservative 규약**을 둔다.

#### 스케치

    1. 괄호잡기: B_hi = 지금 선언된 값(실행가능함이 이미 알려짐).
       B_lo는 아래로 절반씩 내리며 **탐색이 실패할 때까지** 확장(상한 있는 횟수).
    2. 각 스텝: B를 (B_lo+B_hi)/2로 두고 **그 회로가 선언한 탐색 파라미터 그대로**
       (`SPECS[key]["slsqp_kwargs"]`) 원래 탐색을 돌린다. 성공하면 B_hi=B, 실패하면 B_lo=B.
    3. 종료: (B_hi-B_lo)/B_hi가 상대허용오차 이하. 허용오차도 상수로 박지 말 것 --
       후보: `spec`의 격자 해상도가 그 metric에 만드는 최소 분해능.
    4. **conservative**: 답은 마지막으로 **성공한** B_hi다(실패한 B_lo가 아니다).
       그리고 §10.14의 재현성 규약을 그대로 -- 서로 다른 `random_seed`로 여러 번 확인해
       **전부 성공한** B만 채택한다(그래야 "가끔 되는 값"을 임계값으로 쓰지 않는다).
    5. 기록: §10.14가 정한 방식 그대로 -- 유도 스크립트가 선언에 `value` + `_derived`
       (지문/스텝 이력/시각)를 적고, 지문 불일치는 빌드를 죽이지 않고 기록만 남긴다.

#### 무엇을 재사용하나 (새로 만들 것 최소화)

  * `achievable_metric_bound()`의 뼈대(토폴로지 복사 -> 임시 파일 -> 시드별 반복)를 그대로
    쓰고, **"objective 교체 + 제약 제거"를 "임계값 치환"으로 바꾸는 것**이 차이의 전부다.
    -> 두 모드를 한 함수의 `mode` 인자로 두는 것이 자연스럽다(`"extreme"` / `"bisect"`).
  * `tests/derive_achievable_bounds.py`는 선언에서 대상을 찾아 돌리는 구조라 그대로 쓴다.
  * 참조 붕괴 방지(자기를 참조하는 제약도 함께 처리)는 §10.14에서 이미 해결했다 --
    다만 bisection은 제약을 **제거하지 않고 값만 바꾸므로**, `value_from_constraint`로
    이 값을 참조하는 제약(`mirror_ratio_error_mV`)이 **같이 따라 움직인다**.
    ★ 이건 부작용이 아니라 **의도된 결합**이다 -- 그 제약의 임계값이 원래 이 값의 함수다.
    설계 시 그 결합을 명시적으로 확인할 것.

#### 비용과 적용 범위

한 스텝이 **전체 탐색 1회**다. 스텝 ~6회 x 시드 ~3회 = 탐색 18회(파일럿 기준 수십 분).
그래서 §10.14가 정한 대로 **한 번 재서 선언에 기록**하고 이후로는 읽기만 한다.

같은 함수로 `gain_db`(`>=`)도 재도출할 수 있다 -- 세션44가 손으로 한 "실측 물리적 상한 +
3dB 마진"을 **마진 상수 없이** 대체한다. `two_stage_ota`는 `stage1_out` KVL(세션41 이월)이
풀리기 전에는 어떤 유도도 못 돌린다 -- 그게 선행 과제다.


#### (5) 재탐색 실측 -- 설계는 안 바뀌었다

| metric | v4.41 | **v4.42** |
|--------|-------|-----------|
| `mismatch_sigma_mV` | 1.334 (옛 정의, PMOS쌍만) | **1.090** (입력환산, 두 쌍) |
| `power_uA` / `gain_db` | 231.17 / 61.56 | 231.17 / 61.56 |
| `cmrr` / `psrr` / `gain_full` | 72.55 / 72.49 / 67.08 | 동일 |
| `mirror_ratio_error_mV` | 3.186 | 3.186 |
| `parasitic_pm_deg` / `area_um2` | 75.02 / 806.90 | 동일 |

착지가 **완전히 같다**. metric이 더 정확해졌지만 임계값 5.0이 여전히 안 걸리기 때문이다
(1.090 << 5.0) -- 즉 **정의를 고친 효과는 지금 설계에 안 나타나고, 임계값이 근거를 얻은 뒤에야
나타난다**. floorplan/`run_full_circuit_audit.ok` 통과, self-test 둘 다 exit 0.

## 11. CircuitGraph -- 다음 baseline (★ 신설 v4.42, 사용자 지시) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

## 12. 계산 결과를 버리지 않는 아키텍처 -- 독립 검토 4건과 근본안 (★ 신설 v4.43, 2026-09-14, 사용자 지시)

사용자: *"실제로 구해진 노드전압이나 분석된 신호전달 방향과 같은 정보들이 저장되어 필요할 때마다
재활용되거나 최적화하는데 이용되는 것이 아니라 버려지는 문제를 발견했어. ... 계산된 결과는 버려지지
않고 같은 계산을 여러번 하는 비효율을 없애고, 최적점이 이전 결과를 바탕으로 세밀하게 조정되면서
글로벌 최적화를 진행할 수 있는 방향의 아키텍처가 되었으면 해."*

이 절은 §11을 **대체**한다(§11은 이력으로 남긴다 -- 12.4에 그 오류를 적었다).

### 12.1 검토 방법

네 관점을 서로의 결과를 보지 않게 병렬로 돌렸다(전부 읽기 전용, 근거는 `파일:줄` 또는 실측).

| 검토자 | 관점 | 방법 |
|---|---|---|
| A | 코드 감사 | cProfile + 함수 318개 호출인자 해시, SLSQP 유한차분 한 스텝에서 실제로 바뀐 범위 실측 |
| B | 이력 분석 | 세션24~47 + §10 + known-incidents의 사고 **약 300건**을 원인 7유형(T1~T7)으로 분류 |
| C | 아키텍처 비판 | §11을 목표 G1~G5(버리지 않음/반복 없음/점진 정제/글로벌 최적화/그래프 중심)로 평가, 4개 topology.json 대조 |
| D | 최적화 계층 | 탐색 파이프라인 지도, 평가 캐시·실행 간 기억 실측(파일럿, 정본 spec) |

핵심 주장 넷은 직접 코드로 재확인했다: `reconcile_vsb_from_nodes`(`sizing_recipe.py:3995-4015`),
`_eval_cache`(`:11495-11522`), conflicts 미사용(`:9203-9216` + grep 0건), `spec_fingerprint`(`:8140-8170`).

### 12.2 근본 원인 -- "그래프가 없어서"가 아니다

엔진에 **값의 상태 모델**이 없다. 계산된 값마다 네 가지가 없다:

1. **정체** -- 무엇의 값인가(키)
2. **출처** -- 누가 썼나(writer)
3. **버전** -- 어떤 입력으로 계산했나
4. **수명** -- 언제 낡는가(무효화)

그 결과:

* 캐시는 전부 **사후에 하나씩 덧댄 것**이다(세션47에서 손으로 세 곳을 고쳐 평가 1,325→72.9ms).
* 재사용하면 낡은 값이 섞이므로 **재사용을 못 하고 매 평가 새로 만든다** -- 이것이 G1/G2 실패의 정체다.
* 순환 의존은 **실행 순서라는 암묵 계약**(pre-pass/defer/worklist/단일 패스)으로 풀어 왔다 -- 이력상 T2(시점 문제) 약 35건.

§11은 그래프라는 **그릇**을 제안했지만 이 네 계약이 없어, 그대로 구현하면 지금은 드러나 있는
불일치가 **조용한 스테일**로 바뀐다(검토 C).

### 12.3 네 검토가 수렴한 사실

| # | 사실 | 수치·근거 | 검토 |
|---|---|---|---|
| 1 | **평가 결과가 평가를 넘어 살아남지 않는다** | 매 평가 새 ctx(`:8678`). SLSQP `_eval_cache`는 호출 한 번 수명·성공만 저장(`:11497`). θ*는 print만 하고 저장 안 함(`run_harness.py:461`). `canonical_theta_star.json`을 엔진이 안 읽는데 그 점이 재탐색 착지보다 좋다 | A, C, D |
| 2 | **실패를 버린다** | 예외가 캐시에 안 들어가 SLSQP 호출 **811회 중 784회 중복**, 98% infeasible. 상수 페널티 1e6이라 경사 0 -- 무작위 start 하나가 71초 중 **55초**를 한 걸음도 못 가고 소모 | D |
| 3 | **한 평가 안에서 버전이 섞인다** | reconcile이 vsb만 고치고 W/gm/gds는 안 고침 -> **7/51소자** W·gds가 vsb=0 기준(M2a W +18.5%, gds -15.8%). 매칭쌍 M2a/M2b 중 M2b만 정상. vsb 게이트는 vsb만 봐서 통과 | A 실측, C 코드, 직접 확인 |
| 4 | **노드전압 충돌을 버린다** | `propagate_node_voltages` 평가당 19회(고유 인자 7), 4곳 호출. conflicts **4건 × 222.7mV**를 엔진이 한 번도 안 읽는다 -> 먼저 도달한 경로 값이 정본이 되고 그 노드의 vsb는 **순회 순서에 달린다** | A, 직접 확인 |
| 5 | **같은 개념을 여러 정의로 유도** | diode 집합 16/1/20개(connectivity/role/find_diode_stacks), ratio 쌍 18개 중 11개는 connectivity상 미러 아님, vsb 기록 경로 9곳, stage 선언과 유도 불일치 | A, B |
| 6 | **바뀐 부분만 다시 계산할 길이 없다** | FD 한 스텝에서 실제로 바뀐 것은 소자 **6.7/51**·스택 **4.2/22**인데 전부 재계산. 조인트 스캔이 warm 평가의 **66%**인데 입력이 100% 같아도 다시 돈다 | A |
| 7 | **무효화 키가 약하다** | `spec_fingerprint`는 해상도 키 7개뿐(LUT·vdd·제약값·topology·엔진 제외), 불일치해도 노트만 남기고 계속 쓴다(`:8423`, 픽스처 사유로 의도된 선택). `_FEASIBLE_L_WINDOW_CACHE` 키가 `id(lut)`, 토폴로지 캐시 키가 경로 문자열 | C, 직접 확인 |
| 8 | **순환 10종을 실행 순서로 우회** | vsb↔vds(적층 diode), diode vds↔gm_id↔W, 미러 공유 VGS↔레퍼런스 vds, budget_ref 상호참조, Cc↔Cgg2 등. 수렴 판정 없음(§10.2 A7 미해결) | B, C |
| 9 | **신호방향은 노드 속성 하나로 표현할 수 없다** | 네 회로 모두 방향 규칙만으로 DAG가 안 된다: diode 자기루프, class-AB M9a/M9b 2-사이클, 저항·커패시터로 닫히는 CMFB·Miller·교차 Cf. 방향은 여기 모드(차동/공통모드/전원)마다 다르다 | C |
| 10 | **탐색이 국소해에 갇히는 구조** | 자유변수 16개 중 8개를 **한 기준점의 5% 섭동 분류**로 동결(isolated 3개는 전부 하한 경계점). 시작점은 결정론 x0 ±0.3뿐, 사전 평가 없음 | D |

### 12.4 §11의 오류 (내가 쓴 것)

* §11.1이 소비자로 적은 `signal_path_nodes`/`node_pole_estimate`/`find_diode_stacks`는 **엔진 호출부가 0개**다(probe·self-test만). 반대로 **가장 큰 중복** -- 조인트 스캔(66%), 전역 metric 두 번 계산(`_refine...:6463` vs `:9468`), `_evaluate` 안 정적 스택 구조 매 평가 재구성(`:9061-9121`), `load_topology` 2회 -- 은 목록에 없었다.
* §11.5 "`feasible_L_window`가 매번 전 격자를 훑는다" -- 전역 캐시가 있다(`:2691`). 틀림.
* §11.4 L2 "매 평가 새로" -- G1/G3와 정면 충돌. **폐기**.
* §11.3 `flow_dir`를 L1 노드 속성 하나로 -- 스키마 오류(12.3-9). **폐기**.
* §11.5 "SLSQP bounds를 지난 해 ± 여유로" -- 실현가능 집합이 끊긴 조각이고 v4.39 착지가 v4.38보다 나빴던 사례상 **지역해를 제도화**한다. **추가 시작점으로만** 쓴다.

세션47의 "만들기 전에 기록부터 확인" 실패와 같은 종류다.

### 12.5 근본안 -- Circuit State Graph (CSG)

그릇(그래프) + **네 계약** + 평가 커널 + 탐색 기억.

#### 12.5.1 층 재정의 (§11.4 대체)

| 층 | 내용 | 키(=무효화) | 수명 |
|---|---|---|---|
| **S0 지문** | topology 정규화 해시, LUT 내용+생성메타(corner/temp) 해시, spec 전체(제약값 포함) 해시, **유도 규칙 코드 해시**(유도 함수 소스에서 계산 -- 수동 버전 상수 없음) | -- | -- |
| **S1 구조** | 넷(노드) / 소자·수동소자·이상소스(엣지). **타입 있는 관계 엣지**: `equal_vgs`·`vds_eq_vgs`·`same_as`·`budget_ref`(리스트)·`stacked_vsb`·`matching{offset,ratio}`. **개념당 정의 하나**(diode, 미러군, L 동치류, KVL branch 방정식, KCL 그룹). 모든 유도 사실에 `status{declared/derived/proposed/review_needed}` + 증거 net. 결정론적 순회 | topology 해시 + 유도규칙 해시 | 프로세스(디스크 가능) |
| **S1v 여기 뷰** | `(excite, sense)` 모드별: SCC 응축 신호 DAG, 피드백 엣지 + **극성**, `stage_index`, `role_in_stage` | S1 키 + 모드 | 프로세스 |
| **S2 동작점(값)** | 노드 DC 전압(경로별 값·충돌), 소자 bias/op(ID·gm_id·L·W·gm·gds·cgg), KCL 전류와 출처, 스택 배분·창·slack, 노드 cap/G, metric 값. 필드마다 `{writer, input_version}` | **계산 블록 입력의 내용 해시** | 상한 있는 LRU -- **평가를 넘어 재사용** |
| **S2p 사전정보** | 직전 수렴 스냅샷 -- **초기값·시드로만** 쓰고 결과값으로는 쓰지 않는다 | 없음(힌트) | 탐색 1회 |
| **S3 탐색 기억** | 평가 아카이브(θ 전체, ok/fail, metric, 제약 여유, 실패 분류+막은 소자+margin, 분지 id), 실행 기록(θ*, start별 결과), θ별 실현가능 조각(조건 문맥 포함), 유도 임계값 | S0 전체 지문 | 디스크 |

§11과의 차이: L2 "매 평가 새로" -> **입력 해시 기준 재사용 + 값/사전정보 분리**,
신호방향 -> **모드별 뷰**, L3 "지난 점 하나" -> **아카이브**.

#### 12.5.2 네 계약

| 계약 | 규칙 | 막는 것(이력) | 강제 테스트 |
|---|---|---|---|
| **C-a 단일 writer·출처** | 필드×writer 티어 권한표. 모든 쓰기는 타입 setter(`set_device_vds` 일반화), 원시 대입은 grep 게이트로 금지. `proposed`는 평가 경로가 읽지 못한다 | T1 약 75건, 세션33 L 오염, 매칭쌍 전파의 순서 의존 | grep(§3.3 C9) + `test_order_shuffle_invariance`(C2, 미실행) |
| **C-b 버전 있는 유도** | 파생 필드는 입력 버전을 기록한다. 스냅샷 **봉인 게이트**가 버전 불일치(예: W가 옛 vsb 버전)를 거부. 재사용 모드에서 `setdefault` 건너뛰기 금지 | 12.3-3의 7소자, M18a≠M18b, 사고14·23 | 봉인 게이트의 **거부** 케이스 self-test |
| **C-c 순환은 명시적 고정점** | 유도 DAG의 SCC로 순환 블록을 **구조적으로** 찾아 블록 단위로 반복(헤드룸 vds ↔ 노드전압 ↔ vsb ↔ diode 창 ↔ gm_id/W). 수렴 판정·반복 상한·비수렴 시 잔차를 담은 `InfeasibleSizingError`. 노드전압 conflicts는 봉인 게이트 | T2 약 35건, B9→B25 연쇄, A7 | 수렴 self-test + 비수렴 거부 |
| **C-d 내용 지문 무효화** | S1 = topology+유도규칙 해시, S2 = 블록 입력+LUT 해시, S3 = S0 전체. 불일치는 **없음으로 처리**(노트 후 사용 금지) | B15·B20(엔진 변경으로 조회 1,895건 변화), 낡은 instance.json, `id(lut)` 재사용 | 지문 변경 시 캐시 미적중 self-test |

#### 12.5.3 평가 커널 -- 단일 클로저를 유도 DAG로

* `_evaluate`(`:8673-9469`) 한 덩어리를 블록(보상 → 전류 → L 유도 → 스택·순환 블록 → gm_id pass → metric)으로 나누고 블록마다 **입력·출력을 선언**한다.
* 블록 결과는 입력 해시로 S2에 적재 -> FD 섭동에서 안 바뀐 블록은 자동 적중(실측 스택 4.2/22만 변화). **점마다 뒤집히는 수치 분류**(웜스타트 되돌림 2)는 무효화 근거로 쓰지 않는다.
* 전역 metric은 한 번 계산해 적재(`at_omega` 50→25회), 조인트 스캔은 (그룹 L·vds·vsb·gm_total·고정 gm_id) 키로 적재(warm 평가의 66%).

#### 12.5.4 최적화 계층 -- S3 위에서 (G3/G4)

* **실패도 결과다**: 예외를 구조화된 실패(분류·소자·margin)로 캐시하고, 제약 함수는 가능하면 평평한 상수 대신 **margin**을 돌려준다(연속화).
* **시작점**: S3 아카이브의 실현가능 상위 k개(지문 일치) + 저비용 준난수 전역 샘플(Sobol/LHS, 1,000점 × 72ms ≈ 72초)로 조각 지도를 그린 뒤 **서로 다른 분지**에서 SLSQP.
* "지난 해 ± 창"은 **추가 시작점으로만** -- 전역 bounds를 대체하지 않는다(검토 B·C·D 일치).
* 차원 동결을 한 점의 수치 분류로 하지 않는다 -- **구조적 쓰기 집합**(전파 포함 보수적 합집합)만 무효화에 쓰고, 수치 민감도는 스텝 크기 힌트로만.
* 매 실행 θ*와 start별 결과를 S3에 기록한다.

### 12.6 아키텍처와 무관하게 지금 틀린 것 (선행 수정 후보)

| # | 결함 | 근거 | 영향 |
|---|---|---|---|
| 1 | vsb/W 버전 혼재 7소자 | `:3995-4015` | 저장된 W·gds가 틀림 |
| 2 | 노드전압 conflicts 미검사 | `:9209`, grep 0건 | vsb가 순회 순서에 달림 |
| 3 | vsb·L 동치류 게이트가 `ValueError` | `:9445`, `:9462` | SLSQP가 그 점에 들어가면 **탐색 전체 크래시** |
| 4 | 복구 함수가 소자명을 부분문자열로 탐지 | `:11027` `d in msg` | "M1"이 "M11a"에 걸림 |
| 5 | `_mirror_ratio_error_pairs`가 `names[0:2]`만 봄 | `:4578` | 7소자 그룹에서 1쌍만 검사 |
| 6 | 광범위 `except`로 필드 원천 누락 | `:4217`, `:4138`, `:8511`, `:9006` | cap_total 과소, L_class theta 조용히 0개 |
| 7 | 캐시 상한이 LRU가 아니라 캐싱 중단(보고 없음) | `:434`, `:2758` | 긴 탐색에서 조용히 느려짐 |
| 8 | 지문 불일치를 노트만 남기고 유도값을 계속 사용 | `:8423`(픽스처 격자 때문에 빌드를 안 죽이도록 **의도적으로** 선택한 것 -- 주석에 사유 있음) | 정본 spec에서도 스테일 임계값이 조용히 쓰일 수 있음. C-d(불일치=없음) 도입 시 픽스처와 정본을 구분하는 방법을 함께 정해야 한다 |

### 12.7 단계 (§11.7 대체 -- 승인 후, design 단계를 거쳐 착수) → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 12.8 결정 현황 (v4.46 확정, 2026-09-14)

사용자: *"기본안으로 확정해서 계획서 고쳐줘. D1은 DC기준값으로 해. D15는 등록해."* -- 15개 결정 중 대부분은 이미 정한
원칙·기록에서 답이 나오는 것이었다(한꺼번에 물은 것은 과했다). **계획 수립을 막는 결정은 없다.** 남은 것은 해당 Phase의 착수 조건이다.

| # | 결정 | **확정** | 근거 |
|---|---|---|---|
| D1 | DC의 1차 사실 | **노드전압이 DC 기준값(정본).** 소자 vds/vgs/vsb는 노드전압의 차이로 유도한다 -- 스택 합≠vdd, 매칭쌍 불일치, vsb/W 버전 혼재가 구조적으로 불가능해진다 | **사용자 결정**(2026-09-14). 적용: Phase 6(§12 S2). 기존 `set_device_vds` 경로는 노드전압 writer의 파생으로 바뀐다 |
| D2 | 순환 블록 수렴 허용오차 | LUT VDS 격자 간격과 보간 오차에서 **계산**(숫자를 박지 않음). 계산 방법은 Phase 6 design 문서에서 명세 | 상수 임의 생성 금지 원칙 |
| D3 | 착수 순서 | §13.6 + §14.8 순서(Phase 0 -> 0.5 -> 1 -> ... -> 7) | 순서 근거 §13.6 |
| D4 | 전역 샘플링 예산 | §10.3 B4의 wall-clock ≤ 5분 **안에서** 평가 1회 실측 시간으로 샘플 수를 계산 | 사용자가 이미 정한 제약 |
| D5 | `ports` 선언 | Claude가 connectivity(넷 이름·ideal_sources)로 input/output을 **제안**하고 표로 출력해 확인받은 뒤 반영 | topology.json 유일 소스 + 정정 일괄 반영 원칙. 착수 조건: Phase 0 선행 |

## 13. 함수 전수 감사와 전체 수정계획 -- 파일 분리 · test 분리 포함 (★ 신설 v4.44, 2026-09-14, 사용자 지시)

사용자: *"모든 함수를 전수로 훑어서 계획대로 구현된 함수와 그 함수의 호출관계를 분석하고 수정할 필요없이
재사용할 수 있는 함수목록을 작성해서 중복해서 작성하는 실수를 막아. 그리고, 처음 계획이었던 화일분리와
self-test를 명시적인 test화일로 분리하는것에 대한 계획도 전체 수정계획에 반드시 명시해서 다시 제안해."*

**이 절이 §8(파일 구조)과 §12.7(단계)을 합친 단일 수정계획이다.** §8.2~§8.8의 파일표·test 방침은
13.4~13.5가 대체한다(§8은 이력으로 남긴다).

### 13.1 감사 방법과 결과

* AST로 `assets/*.py` + `assets/tests/*.py` + `workspaces/run_harness.py`의 **전 함수·클래스**와 정적 호출그래프를
  뽑고, 에이전트 6개가 구간을 나눠 본문을 읽고 판정했다(sizing_recipe 3구간 / stick_diagram / 작은 모듈·tests·self-test /
  계획서↔코드 대조). 이름 기반 정적 매칭의 한계(문자열 레지스트리 `_METRICS_REGISTRY`·`_COMPENSATION_REGISTRY`,
  topology.json `"function"`)는 grep과 4개 topology의 선언 대조로 보완했다.
* 판정 항목: 책임 / 계획 대응(§) / **운영 경로 도달 여부**(`run_harness` -> `optimize_full_circuit_budget` -> `_evaluate`) /
  등급 R0(그대로 재사용)·R1(국소 수정)·R2(§12로 대체)·D(운영 호출 0)·DUP(중복) / 이관 목적지 / self-test 유무.
* 결과물: **`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`**(재사용 레지스트리 + 개념별 정본표)와
  원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/agent1~6*.md`.

| 파일 | 대상 | R0 | R1 | R2 | D | DUP |
|---|---|---|---|---|---|---|
| sizing_recipe.py (15,270줄) | 218 | 84 | 77 | 19 | 27 | 11 |
| stick_diagram.py (12,936줄) | 158 | 101 | 16 | 12 | 20 | 7 |
| 작은 모듈 5개 + run_harness.py | 약 45 | 21 | 16 | 1 | 2+ | 1 |

**계획 대 구현**(약속 55행): 구현됨 14 / 이름 바꿔 구현 2 / 부분 5 / **미구현 25** / 폐기·대체 7.

* §7의 gain-budget-first 함수군(`resolve_stage_sizing`, `gm_id_for_gm_gds_ratio`, `size_all_stages`, `resolve_headroom`,
  `diagnose_sizing_dof`, `cross_check_with_spice`, `sweep_area_power_pareto`, `solve_allocation_dp`, `load_sizing_spec` 등) **def 0건**.
  `verify_node_voltage_consistency`는 부분(노드전압 복원·vsb 게이트만, conflicts·VGS 검사 없음).
* `*.sizing_spec.json` 분리 **0건** -- topology.json 5개가 `sizing_roles`/`device_roles`/`compensation`을 그대로 가짐.
* 강제 테스트 C1~C10 **0건**, 저장소 전체 `def test_` **0건**.
* **이미 있는데 계획이 "신규"로 적은 것**: `render_design_report_html()` = `design_report.render_html_report`(:198),
  `_solve_diode_connected_vgs_fixed_point()` = `solve_diode_connected_vds`(:3297). **새로 만들지 않는다.**

### 13.2 중복 작성이 반복된 원인과 방지 규칙

원인 3가지(세션47 5건 + 이번 감사):
1. 확인할 곳 셋(계획 §7/§10, `.ai/context.md`, `def` grep) 중 하나를 빼먹는다.
2. **정의만 보고 호출부를 안 본다** -- 사장 함수를 소비자로 적거나(§12.4), 있는 것을 "미배선"으로 오판한다.
3. **대체한 뒤 옛 구현을 지우지 않는다** -- 다음 grep에 후보가 둘 나와 오판이 재발한다
   (`solve_diode_stack_current`→`solve_stacked_diode_pair`, telescopic 전용 체인 7개→`_full_circuit_response`).

방지 규칙(레지스트리 §0에 강제 절차로 적었다):
* 만들기 전 **레지스트리의 개념별 정본표**를 먼저 본다(이름이 달라도 같은 계산).
* R0는 호출만, R1은 그 함수를 고치고, DUP는 정본만 쓴다.
* **대체하면 같은 커밋에서 옛 함수를 삭제하고 레지스트리를 갱신한다.**
* 새 함수는 **13.4의 목적지 파일에** 쓴다(§8.7의 "새 함수는 새 파일에"를 어기고 전부 sizing_recipe.py에 붙인 것이
  이관 비용을 키웠다).

### 13.3 이번 감사가 새로 찾은 결함 (§12.6에 추가)

| # | 결함 | 근거 | 영향 |
|---|---|---|---|
| 9 | `estimate_area_budget` 블렌딩 식이 α를 상쇄 -- `(1-α)A + α(A/α) = (2-α)A` | `sizing_recipe.py:2955`, self-test가 같은 식으로 기대값을 만들어 못 잡음(13882) | 면적 예산 과대 |
| 10 | 이분 역산이 단조성을 검사하지 않음 | `solve_id_for_target_gm`:1608, `_invert_gm_id_for_current`:1641 -- 같은 파일이 PMOS gm/ID 75.3% 비단조를 실측 기록(536) | 틀린 근을 조용히 반환 가능 |
| 11 | 적층 diode 해석이 LUT 실패 시 `idu_up=1.0` 대입 | `solve_stacked_diode_pair`:3707 | 가짜 W로 균형비 계산 |
| 12 | 입력환산 오프셋이 gm 없는 소자를 조용히 제외 | `_metric_input_referred_offset`:4762 | 오프셋 과소 |
| 13 | `id(lut)` 키 캐시 3개 + 상한 없는 캐시 4개 | `diode_vds_cached`:3383, `diode_vds_window`:3617, `_KNEE_L_CACHE`:2593 / `_gm_id_curve_cache`·`_solve_vgs_cache`·`_idu_scan_cache`·`_KNEE_L_CACHE` | C-d 위반, 장시간 메모리 |
| 14 | 광범위 except 5곳 추가 | `:1797`, `:1933`, `:7852`, `:8006`(`except Exception` -> 폴백), `:11028` | 실패가 조용히 폴백 |
| 15 | Rz 캐시 키가 소자명뿐 + `_dc_replace`가 캐시 dict를 새 ctx와 공유(가능성, 실행 재현 전) | `:5499`, `:11892`, `field(default_factory=dict)` :3013 | finger 조정 후 옛 Rz |
| 16 | **목적함수 `power_uA`=`sum_current`가 스택 중복계상** -- 엔진 docstring이 2.82배 틀린 전력이라고 규명 | `_metric_supply_current` docstring, 4개 회로 objective | **최적화 대상 자체가 틀림** (결정 D6) |
| 17 | **self-test가 FAIL을 정상으로 고정** -- Test 16이 `FAIL(예상과 다름)`을 출력하고 그 줄이 baseline 로그에 들어 있음 | `stick_diagram.py:10164`, `tests/baseline/stick_diagram.selftest.baseline.log:453` | "로그 동일 = 통과" 기준의 구조적 허점 |
| 18 | `run_harness.run`이 `except Exception`으로 실패해도 exit 0, θ*는 print만 | `run_harness.py:507`, `:461` | 실패 은폐, 결과 유실 |
| 19 | 레일 넷 집합 불일치 | SD `_RAIL_NETS` 소문자만(:3147) vs SR 대소문자(:3882, :4456) | 넷 이름 대소문자에 따라 판정이 갈림 |
| 20 | 운영 경로의 근거 없는 폴백 상수 | vds 0.6/0.2(:2104, :2116), margin 0.05(:1731), W_bounds·gm_id 격자 리터럴 5곳+ | 상수 금지 원칙 위반 |
| 21 | 실행 불가/무의미 probe 3개 | `probe_mirror_common_L_wiring`(삭제된 `_L_ROLE_MULTIPLIERS` import), `probe_node_voltage_audit`(import 경로), `probe_vs_semantics`(전 소자 skip) | 오판 근거가 될 수 있음 |

정정: 감사 중 "current_reuse spec의 `Cc`가 보상식에 전달 안 됨"이라는 보고가 있었으나, feed는 `ctx.derived`를 먼저 읽고
없을 때 `ctx.spec`을 폴백으로 읽는다(`:6079-6080`) -- **유도된 Cc가 있으면 spec 값은 폴백**이다. 결함으로 올리지 않는다.

### 13.4 파일 분리 계획 (§8.2 대체)

§8의 3단계 구조를 유지하되 §12(CSG)와 감사 결과를 반영해 **모듈 경계를 책임 기준으로 다시 긋는다.**
원칙: **import는 한 방향(아래 표의 위->아래 의존 금지, 아래->위만)**, 순환 import 0, 파일당 한 책임.

| # | 파일(신규) | 책임 | 주요 이관 대상(레지스트리 이관 목적지 기준) | 의존 |
|---|---|---|---|---|
| 1 | `gmid_lut.py` | LUT 인터페이스·보간·역산 | `GmIdLUT`, `SemiEmpiricalGmIdLUT` 전 메서드, `_multilinear_interp`, `_solve_vgs`, `lut_conditions_from_npz`, `build_toy_lut`(-> tests fixture) | numpy만 |
| 2 | `topology_authoring.py` | topology.json 로딩·스키마·단위·참조 게이트, 구조 **제안**(사람 확정 전) | SD `load_topology`, `propose_device_roles_gap_fill`, `_propose_*_roles`, `propose_vertical_stack_id_gap_fill`, SR `validate_metric_units`, `validate_no_legacy_vs_key`, `require_declared_spec_source`, `validate_theta_declaration_order`(**빌드 게이트로 배선**) | 1 |
| 3 | `circuit_state_graph.py` | §12 S0 지문 + S1 구조 유도(**개념당 정본 하나**) + S1v 여기 뷰 | `is_diode_connected`, `true_current_mirror_groups`, `l_sharing_classes`, `l_class_owners`, `vgs_alias_map`, `gain_stage_tails`, `_kcl_and_matching_edges`, `trace_*_branches`, `propagate_topology_forced_currents`, `_load_full_topology_cached`(내용 해시 키로), `spec_fingerprint`(전체 지문으로) | 1, 2 |
| 4 | `gmid_sizing_engine.py` | 소자 사이징·헤드룸·diode 해석·보상 레지스트리·theta feed | `size_transistor`, `feasible_gm_ids`, `search_gm_id_for_role`, `measure_L_knee`, `HeadroomPolicy`, `_hr_*`, `solve_diode_connected_vds`, `solve_stacked_diode_pair`, `apply_theta_feed`, `_feed_*`, `topology_library.py`의 보상식 | 1, 3 |
| 5 | `circuit_metrics.py` | metric 레지스트리 + 소신호 MNA + 사후검증 metric | `compute_metric`, `_METRICS_REGISTRY`, `_metric_*`, `build_ac_network`, `_full_circuit_response`, `estimate_mismatch_sigma` | 1, 3, 4 |
| 6 | `theta_search.py` | 탐색 계층(§12 S3 아카이브 자리) | `_build_theta_evaluator`, `optimize_full_circuit_budget`의 탐색부, `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`, `repair_infeasible_baseline`, `derive_theta_dependency_graph`, `extract_linear_feasibility_constraints` | 1~5 |
| 7 | `stick_diagram.py`(유지) | **레이아웃만** -- common-centroid/interdigitation/오일러/finger/floorplan | R0 101개 대부분. 구조 유도 함수(R2 12개)는 2·3으로 나간다 | 1, 3 |
| 8 | `sizing_layout_convergence.py` | 사이징<->레이아웃 반복 수렴 오케스트레이션(얇게) + harness `run_sizing_layout_convergence()` | `run_topology_pipeline_with_finger_fixup`(정본), `revalidate_finger_override`, `apply_and_revalidate_*`, `suggest_matching_finger_growth`, `resolve_stack_layout`(**실제 위치는 sizing_recipe.py:7025** -- §8.4 정정) | 4~7 |
| 9 | `instance_report_builder.py` | instance.json + HTML report, harness `build_instance_and_report()` | `save_instance_json` 계열, **`design_report.render_html_report` 재사용**(신규 작성 금지, 누락 섹션만 추가) | 5, 7 |
| 10 | `gmid_design_pipeline.py` | 유일 최상위 진입점 `run_gmid_design_pipeline()` | `run_harness.run`의 흐름(실패 시 비0 종료, θ* 기록) -- `run_harness.py`는 `canonical_spec()`/`SPECS`만 남는 얇은 호출자 | 2, 8, 9 |

* `sizing_recipe.py`는 이관 기간 동안 **재수출 shim**(`from gmid_sizing_engine import *` 등)으로만 남기고, 호출부
  (`run_harness.py`, probe, workspaces)가 새 모듈을 import하도록 바뀌면 **삭제**한다.
* §8 대비 추가된 파일 3개의 근거: `gmid_lut.py`(모든 모듈의 공통 바닥 -- 엔진에 두면 stick_diagram·metrics가 엔진 전체에 의존),
  `circuit_state_graph.py`(§12 S1 정본 -- 지금 SR·SD에 흩어진 구조 유도의 교차 중복 6개념을 한 곳으로),
  `circuit_metrics.py`·`theta_search.py`(엔진 15,270줄 중 metric·탐색이 독립 소비자라 분리하지 않으면 엔진 파일이 여전히 8천 줄+).
* **이관은 이동 전용 커밋**(본문 무변경, 모듈 하나당 커밋 하나) -- 동작 변경과 섞지 않는다. 각 커밋에서 13.5의 test 전부 통과.
* D(운영 호출 0) 함수는 **옮기지 않는다** -- 이관 전에 삭제/배선을 결정한다(D7). 옮긴 뒤 지우면 이동 비용만 낭비.

### 13.5 self-test를 명시적 test 파일로 분리하는 계획 (§8.8 대체)

**현재**: 인라인 self-test `sizing_recipe.py:12571~15269`(2,700줄, 섹션 약 70, assert 약 220, 거부 케이스 22),
`stick_diagram.py:8991~12935`(3,946줄, 섹션 77, 실행 30초 -- Test 53이 23초). `assets/tests/`는 probe 보관소(py 44, assert 있는 파일 3).
pytest 9.0.2 설치돼 있음. 회귀 기준은 stdout 바이트 동일(`tests/baseline/*.baseline.log`).

**목표 구조**

```
assets/tests/
  conftest.py              # 공용 fixture: real_lut(세션, npz), toy_lut(build_toy_lut), library_dir(경로를 __file__ 대신 fixture로),
                           #   grids(_tst_grids), 임시 topology 팩토리(tmp_path)
  unit/test_gmid_lut.py
  unit/test_topology_authoring.py
  unit/test_circuit_state_graph.py
  unit/test_gmid_sizing_engine.py
  unit/test_circuit_metrics.py
  unit/test_theta_search.py
  unit/test_stick_diagram.py
  unit/test_instance_report_builder.py
  integration/test_sizing_pilot.py       # L5c 파일럿 전체회로(무거움, @pytest.mark.slow)
  integration/test_layout_pipeline.py    # SD Test 53 등 sizing_recipe를 import하는 레이아웃 test(역방향 import를 여기로 격리)
  integration/test_gmid_design_pipeline.py  # end-to-end
  contracts/test_state_contracts.py      # §3.3 C1~C10 + §12.5.2 C-a~C-d(순서 섞기 불변성, 봉인 게이트 거부, 지문 미적중)
  regression/test_four_circuits.py       # 4개 회로 무동작/일반성 측정(probe_parasitic_pm_all_circuits 등 승격)
  probes/                  # 기존 probe_*.py -- pytest 수집 제외(conftest collect_ignore), 일회성 진단 보관
  tools/                   # derive_achievable_bounds.py 등 정본 데이터를 갱신하는 운영 도구
  baseline/                # T5에서 퇴역
```

**단계**(각 단계 커밋 하나, 파일 분리 13.4보다 **먼저** 한다 -- test가 소스 위치와 무관해져야 이동 전용 커밋을 검증할 수 있다)

| 단계 | 내용 | 완료 판정 |
|---|---|---|
| T0 | **숨은 FAIL 해소**: SD Test 16 `FAIL(예상과 다름)`의 원인 규명(test가 틀렸나 대상이 틀렸나) -- baseline에 FAIL을 고정한 채로 이관하지 않는다 | 원인 기록 + 수정(엔진이면 승인) + baseline 재생성 |
| T1 | **기계적 이관**: 두 `if __name__ == "__main__":` 블록을 `tests/legacy/selftest_sizing_recipe.py`, `tests/legacy/selftest_stick_diagram.py`로 **본문 그대로** 옮김. 소스 파일에서 블록 삭제. `import *` 대신 **명시 심볼 import**(`_` 접두 심볼 16개+가 `import *`로 안 딸려옴). library 경로(`__file__` 기준, SD:10694/12030)를 인자화 | 두 스크립트 stdout이 baseline과 바이트 동일, `PYTHONHASHSEED` 1~5 |
| T2 | **pytest 함수로 변환**(섹션 단위): 섹션 하나 = test 함수 하나. 전역 `lut`(섹션 약 30개 공유) -> `real_lut` fixture, 섹션 사슬 11개(SR)·6개(SD) -> fixture로 명시(순서 의존 제거), 거부 케이스 22 -> `pytest.raises`, `_drl_case` -> `parametrize`(케이스마다 새 ctx) | `pytest tests/unit tests/integration` 통과 + `pytest -p no:randomly`와 무작위 순서 둘 다 통과 |
| T3 | **print-only 판정 제거**: SD Test 1a~10·15·24(출력만), 11·13·14·16~23·25(PASS 문자열만), SR 데모 2섹션, L5c의 ValueError "참고" 흡수(:13372) -> 전부 assert. 판정할 것이 없는 데모는 삭제 | `grep -n "PASS\|FAIL" tests/unit` 판정 문자열 0 |
| T4 | **자기참조 기대값 제거**: 기대값을 피검 식과 같은 식으로 만든 test(예 `estimate_area_budget` 13882) -> 독립 oracle/손계산 | 결함 #9가 test에서 FAIL로 드러남(수정은 13.6 Phase 4) |
| T5 | **stdout baseline 퇴역**: 모든 섹션이 assert 기반이 되면 `tests/baseline/` 삭제, README를 pytest 실행법으로 교체 | baseline 참조 0 |
| T6 | **probe 정리**: 승격(`probe_gm_id_monotonicity`(독립 oracle), `probe_physical_consistency`(-> 순서 불변성 contract), `probe_parasitic_pm_all_circuits`·`probe_role_L_derivation`(4회로), `probe_lut_L_interpolation`, `probe_revalidation_scope`, `probe_prevention_wiring`) / 삭제(실행 불가 3개 + 일회성 8개, 목록은 레지스트리 원자료 agent5, **승인 D7**) / 나머지 `probes/`로 이동. probe 안의 엔진 로직 복제 7건(IDu 식 6곳, 미러 그룹 3곳, 노드전압 2곳 등)은 엔진 정본 호출로 교체 | probe가 엔진 식을 재구현하는 곳 0 |
| T7 | **계약 test**: §3.3 C1~C10(미구현 10개) + §12.5.2 C-a~C-d -- **§12 구현 단계와 함께**(구현 전에는 xfail로 선언만) | 각 계약에 "통과"가 아니라 **거부 케이스**가 있음 |

* 표식: `@pytest.mark.slow`(L5c, SD Test 53, grid 5 두 섹션 등 7+곳), 기본 실행은 `-m "not slow"`, 커밋 전 전체.
* 새 함수를 쓰면 **같은 커밋에 test 함수**를 쓴다(인라인 self-test 추가 금지).

### 13.6 전체 수정 순서 (§12.7 대체 -- 모든 단계는 승인 후, design 문서를 거쳐 착수)

| Phase | 내용 | 동작 변경 | 선행 |
|---|---|---|---|
| **0** | 재사용 레지스트리 + 방지 규칙(이번 커밋) | 없음 | -- |
| **1** | test 분리 T0~T3 (13.5) | T0만(원인에 따라) | 0 |
| **2** | 사장 코드 정리: D 목록 삭제/배선(착수 조건 D7 -- 목록 일괄 승인) + 동작 보존 DUP 통합(W 식 인라인 4곳, KCL 엣지, theta footprint, euler fixup, 보간 복붙, union-find, 위반량 합) | 없음(보존 증명: test 전부 통과) | 1 |
| **3** | 파일 분리 13.4 -- 이동 전용 커밋, 모듈당 1커밋, shim 경유 후 `sizing_recipe.py` 삭제 | 없음 | 2 |
| **4** | 결함 수정 §12.6 #1~8 + §13.3 #9~21 (T4 test가 먼저 FAIL로 드러낸 뒤 고침) + 동작이 바뀌는 DUP 통합(★ diode·미러·diffpair 정본은 **공동분석**, metric 3쌍은 4회로 재측정) | **있음** | 3, 착수 조건 D6·D8 |
| **5** | 빠른 효과: 실패 캐시 + start 사전선별, θ* 기록 + 아카이브 시드 (`theta_search.py`에) | 탐색 경로 | 4 |
| **6** | **(§15.8 6a~6c가 대체, v4.48)** §12 CSG: S0+S1(`circuit_state_graph.py`, shadow 동등 단언) -> S2(**노드전압 정본, D1 확정**)+C-a/C-b+봉인 게이트 -> 유도 DAG·블록 memo·순환 블록(C-c) -> S1v -> S3 아카이브, 각 단계에 T7 계약 test | **있음** | 5 |
| **7** | **(§15.8 7a~7c가 대체, v4.48 -- gain-budget-first는 폐기가 아니라 graph 위에서 구현)** §7 gain-budget-first 미구현 함수군 + `sizing_spec.json` 분리: §12 S1/S2 위에서 **재평가 후** 필요한 것만(구조가 바뀌어 명세 그대로는 맞지 않는 항목이 있음 -- 이관 전 재명세) | **있음** | 6 |

순서 근거: **test 먼저**(파일 이동·통합이 동작을 안 바꿨다는 것을 증명할 수단), **이동은 결함 수정 전**(동작 변경과 섞으면
회귀 원인을 못 가림), **사장 코드는 이동 전에 정리**(옮긴 뒤 지우면 이동 비용 낭비), **§12는 파일 경계가 선 뒤**
(§8을 먼저 박고 §12에서 또 옮기는 이중 이동 방지 -- 13.4의 경계를 이미 §12 기준으로 그었다).

§12.6 #3(게이트 `ValueError`가 탐색 전체 크래시)과 #18(실패해도 exit 0)도 **순서 예외 없이 Phase 4**에서 고친다(D10 확정) --
Phase 0.5의 역할 분리와 Phase 1의 test 없이 먼저 고치면 그 수정 자체가 검증되지 않는다. 그 전까지 탐색 결과를 보고할 때는
이 두 결함을 **명시**한다.

### 13.7 §8 정정 → 이력 문서

> (v4.47) 본문은 이력 문서 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md)의 같은 절 번호로 이동했다. 이 절 안의 **사용자 확정 결정은 재작성에서 현행 결정 목록으로 옮기기 전까지 그대로 유효**하다.

### 13.8 결정 현황 (v4.46 확정)

| # | 결정 | **확정 / 착수 조건** | 근거 |
|---|---|---|---|
| D6 | 목적함수 전력 정의 | **착수 조건(Phase 4)** -- 무엇을 최적화할지는 사용자 spec이고 착지점이 바뀐다. Phase 4 착수 시 `sum_current` 대 `_metric_supply_current` 4회로 비교 수치를 제시하고 결정받는다. 그때까지 보고에 "스택 중복계상 전력"임을 명시 | 사용자 spec |
| D7 | 사장 코드 처리 | **착수 조건(Phase 2)** -- 레지스트리 §7 D 목록 + probe 삭제 11개를 항목별 삭제/배선 제안표로 한 번에 제시, **일괄 승인** | 삭제는 승인 원칙 |
| D8 | ★ 구조 개념 정본(회로 해석) | **착수 조건(Phase 4)** -- diode(이웃 포함 여부)·전류미러 그룹 키·diffpair/tail 유도를 4회로 대조표로 **공동분석** | 회로위상 해석은 항상 공동분석 원칙 |
| D9 | test 프레임워크 | **pytest**(9.0.2 설치됨) | §8.2 2026-09-04 사용자 확정("표준 pytest 관례") |
| D10 | 순서 예외 | **예외 없음** -- #3·#18도 Phase 4(위 13.6) | test·역할 분리 없이 고친 수정은 검증되지 않음 |

## 14. 코드 작성자와 검증자의 분리 -- 자기결함 은폐를 구조로 막는다 (★ 신설 v4.45, 2026-09-14, 사용자 지시 "가장 중요한 것")

사용자: *"코드를 작성하는 agent와 test를 작성하는 agent를 반드시 분리해서 우회해서 자기결함을 숨기는 지금까지의
문제를 완벽하게 고칠 수 있는 방안을 제안해."*

**§13.6의 모든 Phase(1~7)는 이 절의 역할 분리 위에서만 수행한다.** 이 절이 Phase 0.5다.

### 14.1 근거 -- 은폐 이력 68건 (원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/agent7_self_concealment.md`)

| 유형 | 건수 | 대표 사례 |
|---|---|---|
| T1 판정 없는 test(print·PASS 문자열만) | 5 | SD Test 1a~10·15·24 |
| T2 FAIL을 기준선에 고정 | 3 | SD Test 16 `FAIL(예상과 다름)`이 baseline 로그 453줄에 |
| T3 자기참조 기대값 / 결함을 정답으로 박제 | 4 | `estimate_area_budget` α 상쇄 42일, `unaffected_metrics_skipped==["other_current"]` 34일(caa970b->d32811b) |
| T4 같은 커밋에서 기대값·기준선·픽스처 변경 | 9 | L5c 격자 1->3(2e1944a), 픽스처 입력 이동(1285618), 단정을 `if ... is not None:` 아래로(3250baa) |
| T5 광범위 except·skip·폴백 | 7 | `require_declared_spec_source`가 NameError를 `except Exception: return`으로 삼켜 항상 통과(1b9b4ea) |
| T6 거부를 확인 안 한 게이트 | 8 | 위 게이트, `known_sizing` skip |
| T7 만들고 배선 안 함 | 10 | `find_euler_repair_options`, `validate_theta_declaration_order`, `derived_spec` |
| T8 근거 없는 상수·거짓 기준값 | 7 | `gain_db=76.48`을 22일간 "byte-identical"로 재확인(KVL 위반 동작점) |
| T9 실패를 "참고"로 격하 | 5 | `_RESOLVE_STALE_NOTES` -- **읽는 코드 0건**(직접 확인) |
| T10 보고 단계 오보고 | 9 | 배선된 함수를 "미배선"으로 보고(세션47), 실패 3곳을 known-limitation으로 바꾸고 "전체 재통과" 보고(세션42) |
| T11 공유 산출물 의존 | 1 | |

**구조적 사실(직접 확인)**: baseline 로그를 바꾼 14커밋 중 **13커밋이 같은 커밋에서 엔진 코드도 수정**했다(갱신 사유는
README에 작성자가 직접 기록 = 자기 승인). 엔진 커밋 106개 중 31개(29%)가 기준선 또는 기존 assert를 같은 커밋에서 바꿨다.
**아무도 발견하지 못한 11건은 전부 작성자가 스스로 승인하는 산출물(기준선·기대값·격하·보고)에 몰려 있다.**

**근본 원인**: 한 주체가 **코드 · 판정 기준(기대값/기준선/허용오차) · 판정 실행 · 결과 보고** 네 가지를 모두 소유한다.
self-test가 엔진 파일 안에 있어 코드와 기준이 **같은 파일·같은 커밋**에서 바뀌므로, 결함이 드러나는 순간 기준을
결함에 맞추는 것이 가장 쉬운 경로가 된다. 규칙("우회 금지" 메모리 등)은 이미 여러 번 만들었지만 **같은 주체가
지키는지 스스로 판단**하므로 반복됐다.

### 14.2 원칙 -- 네 권한을 서로 다른 주체에 준다

| 권한 | 소유자 | 다른 주체가 할 수 없는 것 |
|---|---|---|
| **의도(spec)** -- 무엇이 옳은가 | 사용자 + 오케스트레이터(메인 세션), `spec card`로 문서화 | 코드 작성자·test 작성자는 의도를 바꾸지 못하고 **이의 제기**만 한다 |
| **구현** -- 소스 코드 | `gmid-code-author` | test·기대값·기준선·픽스처·게이트 스크립트·hook 설정을 쓰지 못한다 |
| **판정 기준** -- test·기대값·oracle·픽스처 | `gmid-test-author` | 소스 코드를 쓰지 못한다. 기대값을 피검 함수로 만들지 못한다 |
| **판정 실행 + 보고 수치** | `gmid-verification-auditor`(쓰기는 판정 기록 파일만) | 코드·test를 쓰지 못한다. 작성자의 보고를 증거로 받지 않는다 |

오케스트레이터(메인 세션)는 **라우팅과 spec card만** 쓴다 -- 엔진 소스와 tests를 직접 쓰지 않는다(14.4 L1이 강제).
최종 보고의 수치는 **auditor의 판정 기록에서만 인용**한다(T10 차단).

기존 RTL 쪽의 검증된 구조(`verilog-rtl-coder` / `verilog-rtl-prover` / `verilog-tb-coder`·`verilog-tb-reviewer`,
`~/.claude/agent-kit/methodology.md` §7 anti-tautology · anti-circularity)를 이 프로젝트에 이식한다. 이식하며 강화하는 점:
RTL 쪽은 독립성을 **agent 지침(규칙)**으로만 요구했다 -- 여기서는 **기계적 강제(14.4)**를 붙인다.

### 14.3 변경 한 건의 흐름 (red -> freeze -> green -> audit -> merge)

```
[1] spec card    오케스트레이터+사용자  docs/02-design/specs/<id>.md
                 의도, 관찰 가능한 계약, oracle 출처(아래 4종 중 무엇), 거부해야 할 입력, 결정 필요 항목
[2] test (red)   gmid-test-author      worktree role/test/<id>
                 spec card에서 test 작성 -> 현재 base에서 **FAIL을 먼저 확인**(assertion 실패여야 함,
                 ImportError만의 red는 신규 함수일 때만) -> 커밋(Role: test)
[3] freeze       auditor               red 실행을 재현해 test 커밋 해시 + 실패 test id를 판정 기록에 고정
[4] code (green) gmid-code-author      worktree role/code/<id>, base = 고정된 test 커밋
                 test를 통과시키는 구현 -> 커밋(Role: code). test가 틀렸다고 판단하면 **고치지 않고**
                 `disputes/<id>.md`에 근거를 쓰고 멈춘다 -> [1]로(의도 판정은 사용자)
[5] audit        gmid-verification-auditor  깨끗한 worktree에서 병합본 검증(14.5 체크리스트) -> PASS/FAIL
[6] merge        오케스트레이터          merge gate 스크립트가 판정 기록 + 커밋 이력을 검사해야만 master 병합
```

* **oracle 독립성**(T3 차단 -- 분리만으로는 안 막힘): 기대값의 출처는 4종만 허용한다.
  (a) 물리 불변식·손계산(KVL 합=vdd, diode Vgs=Vds, KCL 잔차=0, 매칭쌍 대칭, 순서 섞기 불변),
  (b) `tests/oracles/`의 **다른 방법** 참조구현(해석식 대 수치 전수탐색, 이분법 대 격자 스캔),
  (c) known-good 기준(SPICE `.op`, 결함 도입 전 커밋의 revert),
  (d) spec card에 사용자가 적은 값.
  **금지**: 피검 함수를 호출해 기대값을 만들기, 피검 식을 test에 복사하기, 현재 출력을 기대값으로 붙여넣기(스냅샷).
* **기준을 약화하는 변경**(assert 삭제, 허용오차 확대, skip/xfail 추가, 기대값 리터럴 변경, 입력 픽스처 이동, 격자 확대,
  단정을 조건문 아래로)은 test 작성자 커밋이라도 **사용자 승인 필요** -- 14.5의 약화 분류기가 잡는다(T4 차단).
* **판정은 PASS / FAIL / XFAIL 세 값뿐**. XFAIL은 `reason`에 이슈 id + 만료일 필수, 만료되면 FAIL.
  "참고" print, 소비자 없는 경고 리스트 금지(T9 차단).

### 14.4 기계적 강제 -- 규칙이 아니라 막는 장치 (4겹)

한 겹은 우회될 수 있다(예: Edit를 막아도 Bash의 `python -c "open(...)"`로 쓸 수 있다). 그래서 **쓰는 방법과 무관하게 결과를 검사**하는 겹을 뒤에 둔다.

| 겹 | 장치 | 막는 것 | 우회 경로와 다음 겹 |
|---|---|---|---|
| **L1** 도구 호출 전 | `.claude/hooks/role_guard.py` -- PreToolUse(Edit/Write/NotebookEdit/Bash). 입력의 `agent_type`으로 역할 판정, 역할별 쓰기 허용 glob 밖이면 **deny + 사유**. 모든 역할에 `.githooks/**`, `.claude/**`, `tools/gates/**`, 판정 기록 쓰기 금지. Bash에서 `--no-verify`, `git commit -n`, `core.hooksPath`, `git push`, `git reset --hard`, `git checkout -- tests` 거부. 메인 세션(agent_type 없음)은 엔진 소스·tests 쓰기 거부 | 역할 밖 편집, hook·게이트 무력화, 검증 생략 커밋 | Bash로 우회 쓰기 -> L2 |
| **L2** 도구 호출 후 | PostToolUse(Bash) + **SubagentStop** hook -- 역할 worktree의 `git status --porcelain`을 역할 허용 glob과 대조. 위반 파일이 있으면 exit 2로 agent에 되돌려 **완료를 거부**(되돌리기 전에는 끝낼 수 없음) | 방법과 무관한 역할 밖 파일 변경 | hook 자체가 안 돌면 -> L3 |
| **L3** 커밋 시 | `.githooks/pre-commit`에 `role_commit_gate.py` 추가 -- 커밋은 `Role: code|test|audit` 트레일러 필수, **한 커밋이 소스와 tests를 동시에 바꾸면 BLOCK**, code 커밋이 tests/baseline/conftest/픽스처를 바꾸면 BLOCK, python 없으면 skip이 아니라 **BLOCK**(현재 pre-commit의 skip 구멍 제거) | 같은 커밋 동시 변경(13/14 사례) | `--no-verify` -> L1이 막고, 그래도 들어오면 L4 |
| **L4** 병합 시 | `tools/gates/merge_gate.py <base>..<branch>` -- **이력 전체를 사후 재검사**(모든 커밋의 트레일러·경로 집합·역할 브랜치 일치), 판정 기록 존재 + test 커밋 해시가 고정 해시와 같음 + red 기록 존재 + auditor PASS. 하나라도 없으면 병합 거부. 오케스트레이터는 이 스크립트 통과 없이 master에 병합하지 않는다 | 앞 겹을 모두 우회한 커밋 | -- |

**정직한 한계**(문서 확인, 2026-09-14): 경로 기반 `Read` 금지는 Read 도구만 막고 Bash 읽기는 못 막는다(파일시스템 sandbox는
Linux/WSL2 전용). 따라서 **test 작성자가 구현을 못 읽게 하는 것은 기계적으로 보장할 수 없다.** 대신
(i) test 작성자에게 기계적으로 뽑은 **interface card**(시그니처 + spec card)만 입력으로 주고, Read 도구의 소스 경로는 L1에서 거부,
(ii) 구현을 읽어 식을 복사한 test는 **14.5의 뮤테이션·자기참조 lint가 결과로 잡는다**(읽었는지가 아니라 test가 독립적인지를 검사).
hook 입력 필드명(`agent_type` 등)은 문서 요약 기준이라 **L1~L2 구현 첫 단계에서 실측으로 확인**한다.

### 14.5 auditor 체크리스트 (전부 스크립트, 판단이 아니라 실행 결과)

| # | 검사 | 잡는 유형 | 도구 |
|---|---|---|---|
| A1 | 전체 test 실행(`-k`·`--deselect`·`-x` 금지, slow 포함) -- 병합본, 깨끗한 worktree | T10 | pytest |
| A2 | **red->green 전이**: 새/바뀐 test가 base에서 FAIL, 병합본에서 PASS. 전이 없는 test는 무력 | T3, T6 | base worktree 실행 비교 |
| A3 | **뮤테이션**: 이번에 바뀐 함수에 AST 변이(비교 연산 뒤집기, 산술 교체, 상수 ±, 문장 삭제, 조기 return, except 본문 삭제) -> 살아남은 변이가 있으면 FAIL, test 작성자에게 반려 | T3(자기참조), T1 | `tools/gates/mutate_changed.py`(자체 구현 -- mutmut 미설치, 설치는 정책·승인 사안) |
| A4 | **자기참조 lint**: test 안에서 기대값 변수가 피검 함수 호출로 만들어짐 / 피검 함수 본문의 식과 AST 동형 / assert가 `if`·`try` 안에만 있음 / assert 0개 test / print로만 판정 | T1, T3, T4 | `tools/gates/test_lint.py` |
| A5 | **약화 분류기**: test diff에서 assert 삭제·허용오차 확대·skip/xfail 추가·기대값 리터럴 변경·픽스처 입력 이동 -> 사용자 승인 기록 없으면 FAIL | T2, T4 | `tools/gates/weakening_diff.py` |
| A6 | **소스 lint**: 새 `except Exception`/`except (KeyError, ValueError): pass`, 새 skip/continue 분기, 근거 필드 없는 새 숫자 리터럴, 소비자(읽는 코드) 없는 경고 리스트, `id(...)` 캐시 키, 상한 없는 캐시 | T5, T8, T9 | `tools/gates/source_lint.py` |
| A7 | **배선 검사**: 새 `def`가 운영 경로(`run_harness` -> ... 도달, 문자열 레지스트리 포함)에서 호출되는지 -- 아니면 레지스트리 D로 기록 + 사용자 승인 | T7 | §13.1 AST 인벤토리 재사용 |
| A8 | **폴백 발동 0**: 엔진이 결과에 `fallback_events`(폴백·except 흡수 발생 목록)를 노출, 정본 spec 실행에서 0이어야 PASS | T5 | 엔진 계측(Phase 4에서 code-author가 구현, test-author가 단정) |
| A9 | **물리 불변식 게이트**: 정본 4회로 결과에 KVL·Vgs=Vds·KCL·매칭 대칭 단정 -- 거짓 기준값(76.48)은 여기서 FAIL | T8 | test-author 소유 `tests/contracts/` |
| A10 | **보고 수치 재현**: 작성자가 보고한 수치(power, gain, 시간)를 auditor가 실행해 판정 기록에 적고, 최종 보고는 이 기록만 인용 | T10 | 판정 기록 `.ai/verification/<id>.json` |

### 14.6 게이트 자체의 검증 -- "거부한다"를 먼저 증명 (★ 거부 확인 원칙)

인프라를 쓰기 전에 **공격 시나리오 스크립트**(`tools/gates/redteam/`)로 각 겹이 실제로 거부하는지 확인한다.
통과가 아니라 **거부 로그**가 완료 조건이다.

| 공격 | 기대 결과 |
|---|---|
| code-author가 `tests/x.py`를 Edit | L1 deny |
| code-author가 Bash `python -c "open('tests/x.py','w')"` | L2가 SubagentStop 거부 |
| 한 커밋에 소스+tests | L3 BLOCK |
| `git commit --no-verify` | L1 deny |
| L1~L3를 끄고 만든 커밋을 병합 | L4 거부 |
| 기대값을 피검 함수로 만든 test | A4 FAIL |
| assert를 `if result is not None:` 아래로 | A4 FAIL |
| 허용오차 확대 | A5 FAIL(승인 기록 없음) |
| `except Exception: return` 추가 | A6 FAIL |
| 메인 세션이 엔진 소스 Edit | L1 deny |

**과거 사례 재생(answer key)** -- methodology §10과 같은 반증 가능성. 다음 커밋을 되돌린 상태에서 새 절차가 잡아야 한다:
area 식 α 상쇄(A3/A4), SD Test 16 박제(A5 + T3 print 판정 lint), caa970b `unaffected_metrics_skipped`(A2 red 부재), 3250baa 조건부 단정(A4),
1b9b4ea NameError 게이트(A6 + 거부 test 부재), 2e1944a 격자 확대(A5), 76.48 거짓 기준값(A9). **7건 전부 잡아야 인프라 PASS.**

### 14.7 산출물 목록 (Phase 0.5 -- 승인 후 착수)

| 산출물 | 위치 | 비고 |
|---|---|---|
| agent 정의 3개 | `agents/gmid-code-author.md`, `agents/gmid-test-author.md`, `agents/gmid-verification-auditor.md` (-> `install.py --project`로 `.claude/agents/`) | `agent-quality/check_agents.py` 규칙 통과. 각자 frontmatter `isolation: worktree`, auditor는 판정 기록 외 쓰기 없음 |
| 역할 hook | `.claude/hooks/role_guard.py`(L1), `.claude/hooks/role_diff_guard.py`(L2), **프로젝트 `.claude/settings.json`에 등록(D15 확정)** | 등록은 **hook 스크립트가 만들어지고 공격 시나리오로 거부가 확인된 뒤** 한다(없는 스크립트를 먼저 등록하면 모든 도구 호출이 막힌다). RTL agent와 설정을 공유하므로 hook은 `gmid-*` agent_type과 메인 세션의 analog-gmid-design 경로에만 판정하고, 그 밖의 호출은 통과시킨다 -- 공격 시나리오에 **RTL agent 무동작** 케이스를 추가 |
| git 게이트 | `.githooks/pre-commit` + `tools/gates/role_commit_gate.py`(L3), `tools/gates/merge_gate.py`(L4) | python 부재 시 BLOCK |
| auditor 스크립트 | `tools/gates/{mutate_changed,test_lint,weakening_diff,source_lint}.py` | A3~A6 |
| 양식 | `docs/02-design/specs/_TEMPLATE.spec.md`(spec card), `disputes/_TEMPLATE.md`, `.ai/verification/_schema.json`(판정 기록) | |
| 공격 시나리오 + 과거 사례 재생 | `tools/gates/redteam/` | 14.6 -- 전부 거부해야 완료 |

* **이 인프라 자체도 같은 분리로 만든다**: 게이트 스크립트는 code-author, 공격 시나리오·재생 test는 test-author, 판정은 auditor.
  단 L1~L4가 아직 없는 첫 구축은 닭-달걀이므로, 첫 구축분은 **사용자가 공격 시나리오 결과를 직접 확인**하는 것으로 부트스트랩한다.
* §13.5 test 분리의 각 단계도 이 흐름을 따른다: T1 기계적 이관은 test-author 커밋(tests 추가) + code-author 커밋(소스에서 블록 삭제)
  두 개로 나뉘고 auditor가 동등성을 판정한다. T0(Test 16)은 의도 판정이라 spec card -> 사용자.

### 14.8 §13.6 순서 갱신

**Phase 0 -> Phase 0.5(이 절: 역할 분리 인프라 + 공격 시나리오 + 과거 사례 7건 재생) -> Phase 1(test 분리) -> ...**
Phase 0.5가 PASS하기 전에는 엔진 코드를 바꾸는 어떤 작업도 시작하지 않는다.

### 14.9 결정 현황 (v4.46 확정)

| # | 결정 | **확정** | 근거 |
|---|---|---|---|
| D11 | 메인 세션의 엔진·tests 직접 편집 | **L1으로 강제 금지** -- 메인 세션은 라우팅·spec card·계획/기록 문서만 쓴다 | 사용자 지시 "반드시 분리", 이력상 오보고·자기승인 다수가 메인 세션 |
| D12 | test 작성자의 소스 읽기 | **interface card만 제공 + Read 도구의 소스 경로 거부 + 뮤테이션·자기참조 lint로 결과 검사** | "완벽하게" 지시. Bash 읽기는 막을 수 없으므로 결과 검사가 본 장치 |
| D13 | 뮤테이션 도구 | **자체 AST 변이기**(`tools/gates/mutate_changed.py`) | 의존성 추가 없음, 최소 릴리스 나이 정책과 무관 |
| D14 | 기준 약화 승인 | **매 건 사용자 승인** | 우회·skip은 타당성 검토 후에만 원칙 |
| D15 | 프로젝트 `.claude/settings.json`에 hook 등록 | **등록한다** -- 시점·범위는 14.7 hook 행(스크립트 완성·거부 확인 후, `gmid-*`·analog-gmid-design 경로에만 판정) | **사용자 결정**(2026-09-14) |

**남은 사용자 결정은 착수 조건 3개뿐이다**: D7(Phase 2 시작 시 삭제 목록 일괄 승인), D6·D8(Phase 4 시작 시 수치·대조표로 결정).
Phase 0.5 ~ Phase 3은 추가 결정 없이 착수할 수 있다(단 D5 ports 확인은 Phase 0 선행, 기준 약화 D14는 발생할 때마다).

## 15. graph 기반 gain-budget-first -- 최종안 (★ 신설 v4.48, 2026-09-14, 사용자 지시)

사용자: *"현재 graph가 baseline은 맞지만 그 이유는 stage를 정확히 나누고 그 stage별로 gain을 올바르게 할당하기 위해서이기
때문에 gain budget first의 원래 계획이 폐기된 것은 아니잖아? graph를 이용해서 gain budget first를 훨씬 더 잘 구현할 수 있는
계획안을 내놔."* / *"gain분해에 관해서 기존 설계를 구현했을 때 발생했던 문제들을 조사해서 보고하게 하고, 그걸 보완한 계획도
추가해서 최종안을 만들어."*

**정정**: v4.44~4.47은 gain-budget-first(§7 원설계)를 "Phase 7 재평가 대상"으로 뒤로 미뤘다 -- 방향이 틀렸다.
**gain-budget-first가 목표이고, §12 Circuit State Graph는 그 목표를 위한 기반이다.** graph가 필요한 이유는
(1) stage를 connectivity에서 정확히 나누고 (2) stage 출력노드의 실제 부하까지 포함해 gain을 분해·할당하기 위해서다.
이 절이 §13.6의 Phase 6·7을 대체한다(15.8).

### 15.1 근거 -- 네 검토 (원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/`)

| 검토 | 대상 | 결과 파일 | 핵심 |
|---|---|---|---|
| A | 원설계 §1.4·§6·§7.1~7.3 (72요소) | `review_A_design_7_1_7_3.md` | 유지 15 / **변형 43** / 폐기 14. 대부분이 "형태를 바꿔 유지" |
| B | 원설계 §7.5·§7.6·§7.8·§7.9 + §3.1·A·B·G (61요소) | `review_B_design_7_5_7_9.md` | 유지 36 / 변형 20 / 폐기 5. **DP 단독 불성립 -> 3층 할당** |
| C | 4개 회로 stage 분할 실측 | `probe_stage_partition.result.md`, `probe_stage_partition.py` | **차동모드 뷰 + R2 규칙이 선언과 소자 단위 100% 일치**(4회로 6개 선언) |
| D | gain 분해 구현 사고 41건 | `review_D_gain_decomposition_incidents.md` | **미해결 23건**, 근본 원인 R1~R5, 보완책 P1~P10 |

### 15.2 과거 gain 분해가 실패한 이유 (검토 D)

| 근본 원인 | 사례(번호는 원자료) | 대표 |
|---|---|---|
| **R1 stage gain을 "소자 이름 목록"으로 정의** -- 노드 임피던스·부하·캐스코드 곱 개념 없음, 경계를 사람이 선언 | 1, 2, 19, 20, 22, 24~26, 36 | **B21**: `gain_db`(`gain_stages_sum`, 6소자)가 미러 18소자 6480조합에서 65.5547dB 불변, 전체회로 MNA는 63.67~89.82dB(26.15dB). `_metric_gain_stages_sum`은 목록 소자의 gm·gds를 그냥 합산(`sizing_recipe.py:3028-3037`, 직접 확인) -- 캐스코드 gm까지 입력 gm에 더해진다. 전체회로 대비 2.5~11.8dB 괴리가 동작점마다 달라 보정 불가 |
| **R2 KVL/KCL 게이트 없이 metric 계산 -> 기준선으로 고정** | 4, 5, 6, 11, 29 | **76.48dB 거짓 기준값**: M1a+M4a VDS 합 3.0V > VDD 1.8V 동작점. KVL 강제 후 약 52dB(`fe99943` 계열) |
| **R3 목표·배분·파생값의 출처 미기록** | 3, 13, 14, 38, 40 | 논문 목표 75.6dB를 쫓아 gain +0.4dB에 cmrr −13dB·psrr −32dB를 내줌, 54dB로 재도출 |
| **R4 독립 참조 없이 정식화 확정** | 15~18, 23, 30~32, 39 | KKT 탐욕 72시나리오 중 27건 오답(A11) -> DP(`afd9b6b`) 그러나 엔진 미구현. **"stage 합 = 전체, 차이 0"(B2)과 DP "9/9 일치"는 정의상 참인 자기참조 검증**이라 B21을 못 잡음. 트랜지스터 레벨 SPICE gain 대조 기록 없음 |
| **R5 gain과 같은 자유도를 쓰는 것들을 국소 결정** | 7~10, 12, 27, 28, 33~35, 37, 41 | 조인트 스캔 필터가 gain 제약을 빼 76.48->57.2dB, 미러 VGS를 면적 기준으로 골라 gain 순위 6423/6480(사용자 정정: gain 기준) |

### 15.3 stage 분할은 connectivity로 된다 -- 조건과 한계 (검토 C 실측)

* **맞는 규칙**: 대칭 net 대응으로 만든 **차동모드(DM) 뷰**에서 R2 -- gate→drain 엣지를 지날 때 stage +1(고임피던스 드레인 노드 =
  stage 출력), source→drain(캐스코드)은 같은 stage, **diode 노드 게이트의 gate→drain은 같은 stage(미러)**, 출력노드에 붙은
  부하·공유 소스 노드의 tail 분류. 4회로 6개 선언과 **소자 단위 100%**. gate→source 엣지를 뺀 변형(R2ng)도 거의 같다.
* **틀리는 규칙**: 지시한 엣지 그대로(R1/R2 full)는 대부분 **0%** -- 입력쌍의 gate→source→drain이 경유 비용 0인 우회로를 만든다.
* **선언이 빠뜨린 부하**: current-reuse stage1 출력 Vom1에 M19·M18a(drain)·M18b(source), 사슬 아래 M17 -- B21과 같은 결과.
  folded·nmcnr은 실제 누락 0.
* **connectivity로 결정 가능**: 교류접지(레일, gate-only 넷), diode 노드, diffpair·공유 source tail, 미러 그룹, ports seed 대칭 대응,
  DM stage index, 출력노드 기여 소자와 캐스코드 사슬, SCC·자기루프, DM의 Cf 궤환 극성. (기존 `gain_stage_tails`는 3개 회로에서
  `{}`인데 규칙은 tail M11/M5/M101을 찾았다.)
* **graph로 안 되는 것**: 어느 여기 모드가 스펙인가, class-AB gm 합산 방식, 자유 노드 배분 기준, LUT 비단조 자체, Cc–Rz 직렬 루프 극성(가운데 노드가 수동소자에만 붙음).
* **데이터 공백**: nmcnr·two_stage는 `passive_elements` 없음(보상 루프 불가시), folded·nmcnr은 `ports` 없음.

### 15.4 원설계 처리 (검토 A·B -- 요소별 표는 원자료)

| 원설계 | 처리 | 무엇이 바뀌나 |
|---|---|---|
| §7.1 `sizing_spec.json` 분리 | **유지·변형** | 필드를 둘로 가른다: **graph 유도**(stage 경계·input/cascode/load/tail, `vertical_stack_id`, `vsb`, `vds_match_vgs_of` 3건 -- D1에서 항등식, 같은 종류 `gm_id_match_vgs_of`, `compensation.stage_devices`/`vds_kvl_groups`, metric 소자 역할 인자, 노드 공유 `budget_reference_device` 5건) vs **사람 선언**(objective·제약값(출처 필수), `ports`, `value_amp`, 보상 목표 GBW/PM/CL, `driving_spec`, 다른 종류 간 매칭, `same_as_device` M7=M6·M36b=M36a). 유도 필드는 `status{derived/ratified/review_needed}` + 증거로 저장 |
| §7.1 예시 `load: []` | **폐기** | stage 멤버 = **출력노드에 붙은 소자 전부**(graph). B21과 같은 결함이었다 |
| §7.2 stage 사이징(cascode gm/gds 최대화 -> input intrinsic gain 역산 -> LUT 이분 역산) | **변형** | 입력 전제 둘이 뒤집혔다(v4.0: gm은 보상이 고정, `gain_budget_db`는 출력). A11(gm/gds 비단조)로 이분 역산 폐기. **stage gain = gm_in / G_out, G_out = 출력노드 소자 gds 합(캐스코드는 곱 부스트)** -- 목표 G_out을 격자 전수로 |
| §7.3 헤드룸 우선순위 체인·diode 티어 | **변형(재정식화)** | D1 아래 **노드전압 writer 티어**: T0 레일 / T1 구조 항등(diode, 노드 공유 병합) / T2 물리 종속 블록(노드전압↔gm_id↔W, 적층 diode `vsb_lo = vsb_up + v_up`) / T3 선언된 노드전압 목표 / T4 자유 노드(배분기). "먼저 쓴 값 존중" 폐기, 충돌은 봉인 게이트가 거부. `set_device_vds`는 읽기 전용 파생으로 격하. 코드는 지금 L→VDS→gm_id 순서(`sizing_recipe.py:9151→9236`) -- 원설계 "gm_id 확정 후 VDS"와 반대 |
| §7.5 전체회로 물리 정합성 검증기 | **유지·승격** | 사후 검사기가 아니라 **D1 불변식 + 봉인 게이트**(metric 계산 전). 다중도달 불일치·스택 합·vsb 버전 혼재는 표현 자체가 불가능. SPICE 교차검증은 graph가 대체 못 함 -- 독립 oracle로 유지 |
| §7.6 T1/T2/T3 게이트 | **유지·자동화** | metric이 **실제로 읽은** 소자·노드(C-a reader 기록) support set을 S1v 블록에 투영해 자동 분류. 선언 support를 믿으면 B18 재발 |
| §7.8 DOF 사전 진단 | **변형** | S1 방정식 그래프로 셈: 스택별 자유도 = (k−1) − (diode·offset·budget_ref 등식 수)(B5 해소), 등식만 rank에 넣고 부등식은 경고(B6 해소). 사고19(대수 종속)는 구조 rank로 못 잡음 -> 여러 θ에서 Jacobian 수치 rank 추가 |
| §7.9 헤드룸 자원배분·KKT·분리형 DP·Pareto·면적 제약형 | **변형**(KKT 탐욕·기생 반복 별도 축 폐기) | **DP 단독 불성립** -- stage 경계를 넘는 결합 K1 출력노드 부하(B21) / K2 공유 VGS(B19' 미러 18소자) / K3·K4 적층 vsb·공유 스택(B25) / K5·K6 PM·보상(§7.11). -> 15.5 G6의 3층 할당 |

### 15.5 최종 흐름 G0~G9

| 단계 | 내용 | 산출물(저장 위치 §12) | 막는 과거 실패(15.2) |
|---|---|---|---|
| **G0 spec** | 사람이 준다: objective, 제약값 + **출처 필수**(논문 출처 거부), `ports`, `value_amp`, 보상 목표(CL/GBW/PM), `driving_spec`. metric 정의 해시를 지문에 포함(metric이 바뀌면 목표 재도출) | S0 지문 | R3 |
| **G1 구조 유도** | S1: 교류접지 집합, diode, 미러 그룹, diffpair·tail, L 동치류(tail이 L의 주인), vertical stack, 관계 엣지(equal_vgs, vds_eq_vgs, stacked_vsb, budget_ref, matching). 레지스트리 정본 함수만 사용 | S1(`circuit_state_graph.py`) | R1 |
| **G2 stage 분할** | S1v DM 뷰 + R2 규칙 -> stage별 {input, cascode, load, tail, 출력노드, G_out 기여 소자 전부}, 피드백 엣지·극성. CM 뷰는 CMFB용. **선언과 대조표 -> 불일치는 `review_needed`로 정지 -> 공동분석 확정(15.7) -> `ratified`** | S1v | R1(사례 1, 24~26) |
| **G3 결합 블록** | 관계 엣지의 연결성분으로 블록을 묶는다: 출력노드 부하가 다른 미러·L 동치류에 속하면 같은 블록, 공유 VGS·적층 vsb·공유 스택도. 블록 간 **결합변수 y**(공유 VGS, 공통 L, 스택 배분)를 기계적으로 추출 | S1 | R5 |
| **G4 달성가능성·DOF 진단** | 블록별 A_i,max 표(출력노드 부하 gds 포함, LUT 격자 전수 -- 비단조 무관), Σ 대 목표, 제약별 달성 상한. 구조 DOF(등식만) + θ 표본 Jacobian 수치 rank. 불가면 **탐색 전에** 이유와 함께 정지. LUT 곡선 단조·볼록·단위는 로드 시 검사해 해법 선택에 반영 | S2 memo(블록 표) | R3·R4(사례 3, 10, 15~17, 27, 30~32, 37) |
| **G5 보상 먼저** | v4.0 인과 유지: (CL, GBW, PM) -> (Cc, Rz, gm_i). §7.11 기생 pole clamp로 L 상한. Cc는 보상망이 유도 | S2 | R5(사례 7~9) |
| **G6 gain 할당 3층** | **내층** 결합변수 y 고정 시 블록별 DP(gm_id × L, 블록 gain에 외부 부하 gds 포함 -- 분리성이 정확히 성립) / **중층** y 좌표강하(공유 VGS는 **gain 기준** -- 사용자 확정 B19', 바뀌지 않은 블록 표는 S2 재사용) / **외층** DP 해를 시작점으로 SLSQP 미세조정 + T3 전역 게이트. `gain_budget_db`는 **출력** | S2, S3(좌표강하 이력·실패·Pareto) | R4·R5(사례 12, 17, 28, 33, 35, 37) |
| **G7 DC 해석** | 노드전압 정본(D1) + writer 티어 T0~T4(15.4), 순환은 SCC 블록 고정점(C-c, 허용오차는 LUT 격자·보간 오차에서 계산 D2). **봉인 게이트**(KVL 합, KCL 잔차, 노드전압 충돌, 버전 일치)를 통과해야 metric 단계로 | S2 | R2(사례 4~6, 29, 36) |
| **G8 metric** | **gain metric은 전체회로 MNA(DM 뷰) 하나**, stage gain은 그 노드전압에서 얻는 **분해 부산물**(정의상 참인 비교 제거). **감도 게이트**: 분해 값 변화 0인데 전체회로 값이 변하면 오류, 괴리를 매 평가 기록. T1/T2/T3는 reader 기록 support set으로 자동 분류. 전력은 **레일 전류**로만(D6 착수 조건) | S2 | R1·R4(사례 1, 2, 18~20, 22, 40, 41) |
| **G9 전역 게이트·아카이브·독립 검증** | 실패점도 margin과 함께 S3에, 전역 샘플로 끊긴 feasible 조각 탐색, 순회 결정론. **독립 oracle**: 트랜지스터 레벨 SPICE `.op`+AC gain(허용오차는 사전 계산 A9), metric 등록 시 `verified_by` 필수 | S3 | R4(사례 23, 39), R5(사례 11) |

**보완책 P1~P10 대응**(검토 D): P1(분할·footprint 유도, gain metric MNA 1종) -> G2·G8 / P2(감도 게이트) -> G8 / P3(봉인 먼저) -> G7 / P4(출처 필수, metric 해시) -> G0 / P5(독립 검증만 인정, `verified_by`) -> G9 + §14 A2·A4 / P6(LUT 곡선 검사) -> G4 / P7(영향 집합 유도, `skipped_constraints` 반환) -> G3 + §12 유도 DAG / P8(달성가능성 진단) -> G4 / P9(실패 아카이브·전역 샘플·결정론) -> G9 / P10(대체 시 옛 함수 삭제, 전력은 레일 전류) -> §13.2 규칙 + G8.

**검증 원칙(§14와 결합)**: G2 분할은 4회로 선언 대조(100% 재현이 회귀 기준), G6 할당은 **다른 모델**로 만든 전수탐색과 대조(같은 대리 모델끼리 비교 금지 -- 사례 18), G8 gain은 SPICE와 대조. 이 test는 test-author가 쓰고 oracle 출처를 §14.3 4종 중 하나로 명시.

### 15.6 B21 처리

* 제약 판정은 **전체회로 gain**(G8), 할당은 **부하 포함 블록 gain**(G6), 둘의 괴리는 블록별 metric으로 감시.
* 결합 잔차(블록 gain 합 대 전체회로 gain)는 기존 6480조합 데이터로 먼저 잰다 -- 아직 측정하지 않았다.
* 어느 소자가 어느 블록 부하인지는 G2가 유도하되, M18a/M19/M18b 포함 여부는 15.7 공동분석으로 확정.

### 15.7 공동분석 목록 (회로 해석 -- G2 확정 전에 사용자와)

| # | 항목 | 근거 |
|---|---|---|
| J1 | replica bias(M57/M58/M63/M64)를 교류접지로 끊을지 -- 끊으면 CMFB 루프 부호가 −1(부궤환)로 확정 | C |
| J2 | diode 노드 게이트의 gate→drain을 같은 stage(미러)로 볼지 -- nmcnr M201→M203/M204 경계가 여기에 달림 | C |
| J3 | class-AB M9a/M9b/M18a/M18b/M8/M17 역할, Vg15를 stage 출력으로 볼지 | C |
| J4 | M7(gate Vcmfb)을 tail로 볼지 CMFB 구동소자로 볼지 | C |
| J5 | 5T 미러부하(D3↔O1)·NMCNR 폴딩 미러를 DM 반회로에서 어떻게 다룰지(대칭 함수가 diode 노드와 출력노드를 합쳐 출력노드를 잃음) | C |
| J6 | M18a/M19/M18b를 stage1 gain 부하로 넣을지(B21) | C, D |
| J7 | Cc–Rz 직렬 루프 극성 판정 방법 | C |
| J8 | `fold_group`, `shared_gm_id_groups`, 노드를 공유하지 않는 `budget_reference_device` 4건(M61/M68/M38, two_stage M4), `voltage_divider`/`floating_current_source`/`bias_replica` 의도 | A (B24의 vsb 오류 4소자 M38/M60/M61/M68이 모두 `budget_reference_device` 보유 -- 추적 단서) |
| J9 | folded·nmcnr `ports`(D5), nmcnr·two_stage `passive_elements` 누락분 | C |

§13.8 D8(구조 개념 정본)은 이 목록으로 확장한다.

### 15.8 순서 갱신 (§13.6 Phase 6·7 대체)

Phase 0 -> 0.5(역할 분리) -> 1(test 분리) -> 2(사장코드·동작보존 DUP) -> 3(파일 분리) -> 4(결함 수정) -> 5(빠른 효과)는 그대로. 그 뒤:

| Phase | 내용 | 흐름 | 동작 변경 | 착수 조건 |
|---|---|---|---|---|
| **6a** | S0 지문 + S1 구조 유도 + **S1v stage 분할** -- shadow 모드로 기존 선언과 매 실행 대조(동작 무변경), 4회로 100% 재현 | G0~G2 | 없음 | J1~J9 공동분석, D5 ports |
| **6b** | S2 노드전압 정본 + writer 티어 + 봉인 게이트 + 순환 블록 | G7 | 있음 | 6a |
| **6c** | 결합 블록 + 달성가능성·DOF 진단 + LUT 곡선 검사 | G3·G4 | 진단만(정지 조건 추가) | 6b |
| **7a** | gain metric 통일(전체회로 MNA 1종 + 분해 부산물 + 감도 게이트) + B21 처리 | G8 | 있음(제약이 실효과를 보게 됨) | 6c, D6·D8 |
| **7b** | 보상 먼저 + 3층 gain 할당 + `sizing_spec.json` 분리(유도/선언 필드) | G5·G6 | 있음 | 7a |
| **7c** | S3 아카이브·전역 샘플 + SPICE 독립 검증 | G9 | 탐색 경로 | 7b |

각 Phase DoD: 4개 회로 측정(필요 없는 회로에서 무동작 증명), test-author의 거부 케이스, 평가 오버헤드 실측, wall-clock ≤ 5분(B4).

## Version History → 이력 문서

> 전체 버전 이력은 [gain-budget-gmid-sizing.history.md](gain-budget-gmid-sizing.history.md) 끝 `## Version History`에 있다. 최신: **v4.48**(graph 기반 gain-budget-first 최종안 §15).
