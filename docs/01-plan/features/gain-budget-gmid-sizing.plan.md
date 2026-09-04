---
template: plan
version: 1.0
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
| **Solution** | gm/ID sizing 방법론을 "stage를 정확히 나누고, 각 stage가 낼 gain을 먼저 배분한 뒤, 그 gain에서 유도되는 gm_id로 사이징한다 — output stage에만 driving capability(slew rate/CL)를 추가로 얹는다"는 원칙으로 baseline부터 재설계한다. VDS/헤드룸은 gm_id가 정해진 *이후*에, connectivity(gate==drain)로 diode-connected 여부를 직접 판정해 해석하므로, 이번에 발견한 버그가 재설계의 자연스러운 부산물로 해소된다. |
| **Function/UX Effect** | AI/사용자가 새 회로를 사이징할 때 "이 stage가 몇 dB를 낼지"를 명시적으로 배분하는 게 1급 입력이 되고, 개별 소자의 gm_id/L을 role 휴리스틱으로 따로 추측할 필요가 없어진다. 헤드룸도 diode-connected 소자마다 실측 SPICE와 부합하는 값이 나와, 이후 SPICE 폐루프 검증(트랜지언트 포함)이 실제로 수렴할 수 있게 된다. |
| **Core Value** | 물리적 정확성(physical correctness) — "gm/ID sizing은 회로의 물리적 topology 연결을 보지 않고는 할 수 없다"는 이번 세션 핵심 지적을 아키텍처 차원에서 반영한다. 재사용 가능한 계층(LUT 인터페이스, connectivity, post-sizing 레이아웃, 사후검증 metric)은 그대로 두고 사이징 "결정 순서"만 근본적으로 바꾸는 최소침습 재설계다. |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | gm/ID sizing 엔진이 VDS(헤드룸)를 gm_id보다 먼저, role 라벨 기반 상수로 확정하는 구조라 diode-connected 소자(Vgs=Vds 물리적 강제)에서 최대 1.02V 오차가 나고, 이게 SPICE 폐루프 DC 동작점을 출력단 레일 고정으로 발산시킨다(2026-09-04 세션, SPICE 트랜지언트 검증 중 발견) |
| **WHO** | `analog-gmid-design` skill로 아날로그 IC를 sizing하는 (fresh) agent 세션들 + 사용자(hoseung.lee) |
| **RISK** | gm_id를 gain에서 직접 역산하는 신규 함수(§2)가 캐스코드+입력 소자의 2변수 결합을 제대로 못 풀면 회귀 위험. `known-incidents.md` "사고4"(단별 이득배분은 탐색이 맞다)와의 철학적 충돌을 잘못 봉합하면 예전에 이미 폐기된 접근을 반복하는 셈 — 이번 세션 사용자 확정으로 "배분 자체는 여전히 탐색/사용자 지정, 배분 이후 gain→gm_id 역산 한 단계만 결정론화"로 경계를 명확히 함 |
| **SUCCESS** | (1) `_solve_diode_connected_vgs_fixed_point()`가 16개 diode-connected 소자 전부에서 `vgs_for_gm_id(gm_id,L,vds*,vs)==vds*` 자기일관점에 수렴(현재 오차 0.05~1.02V → 0). (2) `current_reuse_telescopic_ota`를 새 엔진으로 재사이징해도 기존 constraints(gain≥54dB, cmrr/psrr/mismatch/classab)를 여전히 만족. (3) 새 사이징 결과로 만든 sky130 트랜지스터 레벨 SPICE 넷리스트의 `.op`이 rail-lock 없이 수렴 |
| **SCOPE** | 이번 계획: JSON 스키마 설계 + 신규 사이징 알고리즘 설계 + 헤드룸 해석기 재설계 + 파일럿 회로(`current_reuse_telescopic_ota`) 1개 이관·검증. 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/two_stage_ota) 이관은 파일럿 검증 후 별도 작업으로 이연 |

---

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
- `skills/analog-gmid-design/references/known-incidents.md` "사고4" — 단별 이득배분을
  닫힌 식으로 강제하려다 탐색+제약조건으로 정정한 전례(이번 재설계와의 경계 구분 필요)
- `skills/analog-gmid-design/references/topology-fn-derivation-guide.md` — 기존 GBW/PM→gm
  reverse-derivation 절차(compensation 방향이 반대가 됨에 따라 참고용으로 남김)
- `docs/01-plan/features/analog-topology-json-library.plan.md` — topology.json을
  "사이징과 무관한 connectivity만" 담자는 원래 설계 의도(`_TEMPLATE.topology.json` §schema_note) —
  이번 재설계가 그 원칙을 device_roles/sizing_roles/compensation까지 완성한다
- `skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json` —
  파일럿 회로의 현재 connectivity + (폐기 대상) device_roles/sizing_roles/compensation

---

## 2. Scope

### 2.1 In Scope

- [ ] 새 JSON 스키마 설계: `<name>.sizing_spec.json`(§7.1) — `stages[].devices.{input,cascode,load}`,
      `stages[].gain_budget_db`, `stages[].driving_spec`(output 전용), `compensation`(방향 반전),
      `headroom.policy`, `bias_devices`(stage 밖 diode-reference/mirror 소자)
- [ ] `topology.json`을 순수 connectivity 전용으로 되돌림 — `device_roles`/`sizing_roles`/
      `compensation` 필드 제거(새 `sizing_spec.json`으로 이관)
- [ ] 신규 함수 구현(`sizing_recipe.py`, §7.2):
  - [ ] `_solve_diode_connected_vgs_fixed_point(gm_id, L, vs, lut)` — 이번 세션 스크래치패드
        `node_dc_propagate.py`에서 프로토타입 검증 완료, 그대로 이식
  - [ ] `gm_id_for_gm_gds_ratio(target_ratio, L, vds, vs)` — `gm_id_for_vgs()`(:536)와 동일
        패턴의 O(1) 역보간, gm/gds 축 신규
  - [ ] `resolve_stage_sizing(stage_spec, ID, luts)` — stage 알고리즘(§7.2) 구현체
  - [ ] `_resolve_device_headroom(device, ctx)` — `allocate_stack_headroom()`/`HeadroomPolicy`
        대체, connectivity(`gate==drain`) 기반 판정
  - [ ] `solve_compensation_for_gbw_pm(stage_gms, targets)` — 기존 `topology_fn`(GBW/PM→gm)의
        역방향(gm들→Cc/Rz)
- [ ] 파일럿 회로 이관: `current_reuse_telescopic_ota`를 새 스키마로 재작성, 새 엔진으로
      재사이징
- [ ] 회귀 검증: 기존 사후검증 metric(`gain_db`/`cmrr_estimate_db`/`psrr_estimate_db`/
      `mismatch_sigma_mV`/`classab_centering_dev_v`)이 기존 constraints를 여전히 만족하는지 확인
- [ ] diode-connected 자기일관성 검증: 16개 소자 전부 `vgs_for_gm_id(gm_id,L,vds*,vs)==vds*`
      수렴 확인
- [ ] SPICE 폐루프 재검증: 이번 세션에서 만든 sky130 SPICE 넷리스트 생성기(스크래치패드
      `build_transient_netlist.py`)로 새 사이징 결과의 `.op` 수렴 확인 → 원래 목표였던
      class-AB Up/Down settling 트랜지언트 검증 재개

### 2.2 Out of Scope

- 나머지 3개 토폴로지(folded_cascode/nmcnr_amplifier/two_stage_ota) 이관 — 파일럿 검증 후
  별도 작업
- `optimize_full_circuit_budget()`의 신/구 경로 강제 일괄 전환 — `sizing_spec` 유무로 분기,
  점진적 이관
- gain 배분(`gain_budget_db` 자체의 값) 자동 탐색 알고리즘 고도화 — 이번 계획은
  `gain_allocation.method="explicit"|"search"` 스위치만 스키마에 마련하고, "search"의 실제
  탐색 전략은 기존 theta grid-search/SLSQP 메커니즘을 그대로 재사용(신규 탐색 알고리즘 설계는
  범위 밖)
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
4. GBW/PM(위상보상)은 이미 정해진 stage gm들로부터 Cc/Rz 등 보상소자 값을 역산해야 한다
   (사용자 확정: "gain이 주도").
5. gain 배분 자체(`gain_budget_db`가 어떻게 정해지는지)는 여전히 탐색 또는 사용자 명시로
   자유도를 남겨야 한다(사고4 원칙 유지) — 다만 "배분된 gain_i → gm_id_i" 단계만은 예외 없이
   결정론적 역산이어야 한다.

### 3.2 Non-Functional Requirements

- 기존 재사용 계층(LUT 인터페이스, connectivity 파싱, 사후검증 metric, 레이아웃 파이프라인)의
  함수 시그니처는 변경하지 않는다(`analog-topology-json-library.plan.md`가 지킨 것과 동일한
  원칙, §6.1 Changed Resources 참고).
- 신규 함수는 기존 self-test 관례(`python sizing_recipe.py` 인라인 self-test)에 맞춰 검증한다.
- 재계산 효율성 원칙(사용자 피드백 메모리) 준수 — stage 알고리즘이 매 반복마다 LUT 스캔을
  중복 실행하지 않도록, 기존 `_idu_scan()` 캐싱 패턴을 그대로 재사용한다.

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `<name>.sizing_spec.json` 스키마가 확정되고 `_TEMPLATE.sizing_spec.json` 스캐폴드로
      문서화됨
- [ ] `current_reuse_telescopic_ota`가 새 스키마 + 새 엔진으로 재사이징되어 instance.json이
      갱신됨
- [ ] 16개 diode-connected 소자 전부 자기일관 헤드룸 확인(오차 → 0)
- [ ] 기존 constraints(gain≥54dB, cmrr/psrr/mismatch/classab) 전부 재확인
- [ ] sky130 SPICE `.op`이 rail-lock 없이 수렴(원래 세션 목표였던 트랜지언트 검증 재개 가능)

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

---

## 6. Impact Analysis

### 6.1 Changed Resources

- **재설계(신규 작성)**: `device_roles`, `sizing_roles`(`theta`/`metrics`/`objective`/
  `constraints`), `compensation` — topology.json에서 제거되고 `sizing_spec.json`으로 대체
- **재설계(신규 함수)**: `allocate_stack_headroom()`/`HeadroomPolicy`/`_default_cascode_headroom()`
  대체(`_resolve_device_headroom()`), `search_gm_id_for_role()`의 역할 축소(cascode gm/gds
  최대화 용도로만 재사용), `optimize_multistage()`/`topology_fn`의 GBW/PM→gm 방향 반전
- **무변경(재사용)**: `SemiEmpiricalGmIdLUT`/`vgs_for_gm_id()`/`gm_id_for_vgs()`/
  `gm_id_to_id_density()`/`gm_gds_ratio()`, `size_transistor()`/`converge_with_parasitics()`,
  `load_topology()`/connectivity 파싱, `symmetry.matching_pairs`/analog-grammar idiom 탐지,
  `assign_finger_geometry()`/euler 자동수정/matching-safety 자동수정/floorplan,
  `cmrr_estimate_db`/`psrr_estimate_db`/`pelgrom_mismatch`/`nulling_resistor_ohm`/
  `battery_centering_deviation` 등 사후검증 metric 전부

### 6.2 Current Consumers

- `workspaces/run_harness.py` — `optimize_full_circuit_budget()` 단일 진입점 호출자, 신규
  `sizing_spec` 유무로 신/구 경로 분기 필요
- `stick_diagram.py`의 `run_topology_pipeline_with_finger_fixup()` — 사이징 결과(W/L/gm_id)를
  소비하는 후단, 입력 스키마 무관하게 그대로 동작

### 6.3 Verification

§6 절(원본 계획 §6 "검증 계획") 참고 — self-test, 회귀 대조, diode-connected 고정점 수렴,
SPICE 폐루프 재검증 4단계.

---

## 7. Architecture Considerations

### 7.1 새 JSON 스키마 (`<name>.sizing_spec.json`)

```jsonc
{
  "schema_version": "3.0",
  "topology_ref": "current_reuse_telescopic_ota.topology.json",

  "global_spec": {
    "vdd": 1.8,
    "objective": {"minimize": "power_uA"},
    "closed_loop_accuracy_db": null
  },

  "stages": [
    {
      "id": "stage1_input",
      "devices": {
        "input":   ["M1a","M1b","M4a","M4b"],
        "cascode": ["M2a","M2b","M3a","M3b"],
        "load":    []
      },
      "ID_source": {"type": "kcl"},
      "gain_budget_db": 30.0,
      "gain_allocation": {"method": "explicit"}
    },
    {
      "id": "stage2_output",
      "devices": {"input": ["M15","M16","M25","M26"], "cascode": [], "load": []},
      "ID_source": {"type": "kcl"},
      "gain_budget_db": 24.0,
      "gain_allocation": {"method": "explicit"},
      "driving_spec": {
        "CL_farad": 1e-12,
        "slew_rate_v_per_us": null,
        "settling_time_ns": {"up_max": 40, "down_max": 40}
      }
    }
  ],

  "gain_allocation_check": {"total_target_db": 54.0},

  "compensation": {
    "function": "solve_compensation_for_gbw_pm",
    "targets": {"GBW_hz": 5e6, "PM_target_deg": 60},
    "solves_for": ["Cc", "Rz"],
    "stage_gm_ref": ["stage1_input", "stage2_output"]
  },

  "headroom": {
    "policy": "post_gm_id_self_consistent",
    "vertical_stacks": [
      {"id": "output_stage_a", "members": ["M15","M16"], "vdd_kvl": true}
    ]
  },

  "bias_devices": [
    {"name": "M18_bg", "role": "diode_reference",
     "ID_source": {"type": "ideal_source_ref", "ref": "Iref"},
     "gm_id_policy": "min_gm_id_in_bounds"}
  ]
}
```

**핵심 변경 요지**:
- `sizing_roles.metrics.gain_stages_sum`(사후 readback, whole-circuit 단일 제약) →
  `stages[].gain_budget_db`(사전 배분, per-stage). whole-circuit `gain_db>=54`는
  `gain_allocation_check.total_target_db`로 격하(사이징 입력이 아니라 배선 시점 정합성 assert).
- `device_roles.headroom_role` 폐기 → §7.3 헤드룸 해석기가 connectivity로 직접 판정.
- `device_roles.gm_id_role` 폐기(gain stage 소속 소자는 §7.2로 유도) — bias-gen 소자만
  `bias_devices[].gm_id_policy`로 단순 존속(strong-inversion 최소화, 기존 role="matching"과
  동일 근거).
- `sizing_roles.theta`의 A/B/C/D taxonomy 폐기 — 배분 자체가 자유인 것만
  `gain_allocation.method="search"`로 남김.

### 7.2 신규 사이징 알고리즘 (stage 1개 기준)

```
입력: stage.gain_budget_db, stage.devices.{input,cascode,load}, ID(KCL로 이미 확정)

1. cascode 소자: L 후보군에서 gm/gds 최대화 지점을 스캔(기존 search_gm_id_for_role(role="gain")
   재사용) → (L_cas, gm_id_cas) 확정, ro 기여분 = gm_gds_ratio(gm_id_cas, L_cas, vds_cas) 확정.
2. 필요한 input 쪽 intrinsic gain = 10^(gain_budget_db/20) / (cascode가 만든 ro 부스트) →
   input의 목표 gm/gds_effective 역산.
3. input 소자: gm_gds_ratio(gm_id, L, vds)가 2번 목표값과 같아지는 gm_id를 LUT 이분탐색으로
   직접 역산(신규 gm_id_for_gm_gds_ratio()).
4. size_transistor()로 W 확정(기존 함수 그대로).

output stage 추가: driving_spec이 있으면 ID_final = max(KCL ID, slew_rate_target*CL_farad)로
ID 상향 후 위 1~4를 그 ID로 실행 — 같은 gm_id에서 ID만 커지면 gm도 커지므로 gain은 여유가
생기는 방향(배분과 충돌하지 않음).
```

캐스코드 없는 단순 stage는 "cascode 부스트=1(0dB)"로 두면 2/3단계가 자연스럽게 특수 케이스로
커버된다.

### 7.3 헤드룸(VDS) 해석기 재설계

```
_resolve_device_headroom(device, ctx) -> float(vds):
    if connectivity(device).gate == connectivity(device).drain:
        # diode-connected: Vgs=Vds 자기일관점을 고정점 반복으로 직접 푼다
        return _solve_diode_connected_vgs_fixed_point(gm_id, L, vs, lut)
    else:
        # 외부 게이트 구동(캐스코드/입력/tail): 기존 Jespers 근사 유지
        return 2.0/gm_id + margin

vertical_stack 안에서: diode-connected 소자는 위 값으로 먼저 확정(예산에서 제외 —
기존 budget_reference_device 패턴 재사용) → 나머지가 남은 vdd를 분배.
```

`gate == drain` 판정은 `load_topology()`가 이미 파싱한 `netlist`에서 추가 인프라 없이 가능하다.

### 7.4 확정된 설계 원칙 (사용자 승인 완료, 이번 세션 AskUserQuestion)

1. Stage 안의 input+cascode는 gain 목표에서 L/gm_id를 **동시에** 결정한다(캐스코드 L을 role
   휴리스틱으로 따로 정하지 않는다).
2. **Gain이 주도**한다 — 모든 stage gm_id를 gain 배분에서 먼저 정하고, GBW/PM은 보상소자 값으로
   **사후에** 맞춘다.
3. `known-incidents.md` 사고4와의 경계: **배분 자체(어느 stage가 얼마의 gain을 가질지)는
   여전히 탐색/사용자 지정**으로 남기고, "배분된 gain_i → gm_id_i" 이 한 단계만 결정론적
   역산으로 바꾼다.

---

## 8. 3단계 실행 파이프라인 — 파일/harness 함수 구조 (2026-09-04 추가)

### 8.1 배경

사용자 지적: `sizing_recipe.py`라는 파일명이 "gm/ID sizing을 실제로 수행하는 엔진"이라기보다
"사이징에 필요한 도구 모음"처럼 느껴진다. AI가 회로마다 topology를 제멋대로 다르게 해석해
일관성 없이 사이징하는 사고(이 프로젝트 실제 이력, `known-incidents.md`)를 막으려면,
**"topology 수집" → "gm/ID 방법론으로 사이징(+레이아웃 수렴)" → "결과물 산출"** 세 단계를
물리적으로 분리된 파일로 명확히 나누고, 각 단계를 대표하는 이름의 top-level harness 함수
하나가 그 안의 모든 하위 함수를 순차 호출하도록 구조화한다. self-test는 소스 파일에 인라인으로
두지 않고 별도 test 파일로 분리한다(기존 `python sizing_recipe.py` 인라인 self-test 관례에서
전환, 2026-09-04 사용자 확정).

### 8.2 3단계 구조 개요

| 단계 | 책임 | 소스 파일 | test 파일 | top-level harness |
|---|---|---|---|---|
| 1 | topology netlist + 제약 + FoM 스펙 구성 | `topology_authoring.py`(신규) | `tests/test_topology_authoring.py` | `author_topology_spec()` |
| 2 | gm/ID 방법론 기반 사이징 엔진 | `gmid_sizing_engine.py`(신규, `sizing_recipe.py` 핵심부 계승) | `tests/test_gmid_sizing_engine.py` | (엔진 함수군 — harness는 아래 오케스트레이션 파일에서 호출) |
| 2 | 오일러 패스 stick-diagram/레이아웃 | `stick_diagram.py`(기존 유지, 소스 로직 변경 없음) | `tests/test_stick_diagram.py`(신규 — 기존 인라인 self-test, `stick_diagram.py:8980`~파일 끝 약 4000줄 이관) | — |
| 2 | 사이징↔레이아웃 반복 수렴 오케스트레이션 | `sizing_layout_convergence.py`(신규, 얇은 조정 로직만) | `tests/test_sizing_layout_convergence.py` | `run_sizing_layout_convergence()` |
| 3 | instance.json + HTML report 산출 | `instance_report_builder.py`(신규) | `tests/test_instance_report_builder.py` | `build_instance_and_report()` |
| 전체 | 위 3개 harness를 순서대로 호출하는 유일한 최상위 진입점 | `gmid_design_pipeline.py`(신규) | `tests/test_gmid_design_pipeline.py`(end-to-end 통합) | `run_gmid_design_pipeline()` |

`tests/`는 `skills/analog-gmid-design/assets/tests/`에 신설한다(소스와 물리적으로 분리, 표준
pytest 관례와 동일 — 2026-09-04 사용자 확정). 각 단계는 독립적으로도 호출 가능해야 한다(예:
topology만 다시 다듬고 싶을 때 `author_topology_spec()`만 재실행) — 그러면서도
`run_gmid_design_pipeline()` 하나만 부르면 3단계가 전부 순차 실행된다.

### 8.3 Stage 1 — `topology_authoring.py`

**왜 분리하나**: topology 수집(논문/스펙 해석, netlist 확정)은 gm/ID *방법론* 실행과 완전히
다른 활동이다 — 전자는 "이 회로가 무엇인가"를 확정하는 일(사람+AI 협업, 재해석 여지가 있는
일), 후자는 "이 회로를 어떻게 사이징하는가"를 결정론적으로 실행하는 일이다. 섞여 있으면 AI가
사이징 도중 topology를 "편의상 다시 해석"하는 사고가 반복된다.

**harness**: `author_topology_spec(source_spec: dict) -> (topology.json, sizing_spec.json)`

내부에서 순차 호출:
1. netlist 등록/검증(connectivity만, 값 없음) — 기존 `load_topology()`/스키마 검증 재사용
2. `symmetry.matching_pairs`/`dispositions` 자동탐지 — 기존 analog-grammar idiom 탐지
   (`find_matching_candidates()` 등, `stick_diagram.py`에서 import) 재사용
3. gain-stage 후보(§1 스키마의 `stages[].devices.{input,cascode,load}`) 자동제안(신규) —
   사람이 최종 확정
4. `ideal_sources`/`passive_elements` connectivity 등록
5. figure-of-merit 스펙(`global_spec`, `stages[].gain_budget_db`, `driving_spec`,
   `gain_allocation_check`) 등록 — 사람이 확정하는 입력을 받아 스키마에 채워넣는 역할
6. 완성된 `topology.json` + `sizing_spec.json`을 `library/`에 저장

### 8.4 Stage 2 — `gmid_sizing_engine.py` + `stick_diagram.py` + `sizing_layout_convergence.py`

**파일명 근거**: "sizing_recipe"(도구 모음 느낌) → "gmid_sizing_engine"(gm/ID 방법론을
결정론적으로 실행하는 엔진이라는 정체성 명시). 기존 `sizing_recipe.py`의 LUT 인터페이스/
`size_transistor()`/사후검증 metric은 그대로 옮기고, 이번 계획(§2/§3/§4)의 gain-budget-first
알고리즘(`resolve_stage_sizing()`)과 헤드룸 해석기(`_resolve_device_headroom()`)가 이 파일의
핵심부가 된다.

**harness**: `run_sizing_layout_convergence(topology_spec) -> instance_data`
(`sizing_layout_convergence.py`에 위치, 실제 계산 로직은 갖지 않고 아래 순서로 호출만 한다)

내부 순차 호출(사용자가 명시한 "사이징→레이아웃→피드백→재사이징" 루프):
1. `gmid_sizing_engine.size_all_stages()` — §2 알고리즘으로 전체 gm_id/L/W 1차 확정
2. `gmid_sizing_engine.resolve_headroom()` — §3 헤드룸 해석기로 VDS 확정
3. `stick_diagram.assign_finger_geometry()` — finger/width 배분
4. `stick_diagram.check_euler_condition()`/`resolve_stack_layout()` — 오일러 패스 레이아웃
   가능성 검증
5. 4번이 실패하거나 finger 수/width가 바뀌면(레이아웃 제약으로 인한 조정) → 그 변경분을
   1번 사이징 엔진에 피드백(예: W 상한 축소로 gm_id 재탐색) → 2~4 재실행
6. 수렴(레이아웃 목표 달성 + 사이징 constraint 유지)하면 종료, 최대 반복 초과 시 명시적
   실패 보고(조용히 타협하지 않음 — 이 프로젝트 §1.5 원칙)

`sizing_layout_convergence.py`는 1~6단계를 순서대로 호출하는 얇은 오케스트레이션만 담고,
실제 계산 로직은 전부 `gmid_sizing_engine.py`/`stick_diagram.py`에 남는다(레이어 분리 원칙
유지, `run_topology_pipeline_with_finger_fixup()`가 이미 증명한 패턴과 동일).

### 8.5 Stage 3 — `instance_report_builder.py`

**harness**: `build_instance_and_report(instance_data) -> (instance.json 경로, report.html 경로)`

내부 순차 호출:
1. `save_instance_json()`(기존 `stick_diagram.py` 함수 이관 또는 재사용) — 사이징+레이아웃
   결과를 instance.json으로 저장
2. `render_design_report_html()`(신규 — 현재 워크스페이스마다 ad hoc하게 있던
   `build_report.py`/`build_html.py`를 skill asset으로 정식 편입) — 사람이 검토 가능한
   HTML report 생성(gm_id/W/L 표, 헤드룸 검증 결과, gain 배분 대조표, CMRR/PSRR/mismatch 등
   사후검증 metric 요약 포함)

### 8.6 최상위 파이프라인 — `gmid_design_pipeline.py`

```python
def run_gmid_design_pipeline(source_spec: dict) -> str:
    """3단계를 순서대로 실행하는 유일한 최상위 진입점 -- AI는 이 함수 하나만 호출한다
    (optimize_full_circuit_budget()의 '단일 진입점' 원칙을 3단계 구조에 맞게 계승)."""
    topology_json, sizing_spec_json = author_topology_spec(source_spec)
    instance_data = run_sizing_layout_convergence(sizing_spec_json)
    instance_path, report_path = build_instance_and_report(instance_data)
    return report_path
```

각 단계 harness는 독립 호출도 가능(예: topology만 다시 다듬고 싶으면 `author_topology_spec()`만
재실행) — `run_gmid_design_pipeline()`은 그 3개를 그대로 이어 붙이기만 한다(새 로직 없음).

### 8.7 기존 `sizing_recipe.py`와의 관계

`sizing_recipe.py`는 폐기되지 않는다 — 이번 재구조화로 그 내용이 성격별로 새 파일로
재배치된다:
- LUT 인터페이스, `size_transistor()`, 사후검증 metric → `gmid_sizing_engine.py`
- topology 스키마 검증/analog-grammar 연동 부분 → `topology_authoring.py`(이미
  `stick_diagram.py`에 있던 것과 통합 검토)
- (변경 없음) 레이아웃/euler → `stick_diagram.py` 그대로

이 재배치는 §5(마이그레이션 계획)의 "파일럿 회로 1개로 먼저 증명" 범위 안에서 함께
수행한다 — 새 gain-budget-first 알고리즘 구현과 파일 재구조화를 별개 작업으로 쪼개지 않는다
(어차피 새 함수들은 새 파일에 바로 작성되므로 추가 이관 비용이 없음).

### 8.8 self-test 분리 방침

기존 관례(`python sizing_recipe.py`/`python stick_diagram.py` 실행 시 파일 하단의 인라인
self-test 블록이 함께 실행됨)에서 전환 — **`stick_diagram.py`를 포함해 소스와 test를 물리적으로
분리한다**(2026-09-04 사용자 확정 — 처음엔 `stick_diagram.py`는 이번 재구조화 범위 밖으로
잡았으나, 사용자 지시로 범위에 포함시킴):

- `skills/analog-gmid-design/assets/tests/test_<module>.py` 형태(모듈당 1개, `gmid_design_
  pipeline.py`만 end-to-end 통합 test로 별도 성격).
- 각 test 파일은 대응하는 소스 모듈을 import해서 검증하는 표준 구조(`sizing_recipe.py`가
  지금까지 쌓아온 self-test 커버리지 — L5c 헤드룸 singleton, ideal_sources 대조 검증 등 —
  는 성격에 맞는 새 test 파일로 이관).
- **`stick_diagram.py:8980`부터 파일 끝(12923줄)까지의 `if __name__ == "__main__":` 인라인
  self-test 블록(약 3900줄)을 `tests/test_stick_diagram.py`로 이관한다.** `stick_diagram.py`
  자체의 소스 로직(오일러 패스/finger 배분/floorplan 계산 함수들)은 이번 재구조화에서 손대지
  않는다 — 이관 대상은 self-test 블록뿐이며, 이관 후 `stick_diagram.py`는 소스 함수만
  남기고 self-test import는 `test_stick_diagram.py` 쪽에서 `from stick_diagram import *`
  (또는 명시적 심볼 import)로 가져간다.
- 이관 시 회귀 확인: `python tests/test_stick_diagram.py` 실행 결과가 이관 전
  `python stick_diagram.py` 실행 결과(현재 selftest_session*.log들)와 동일한 PASS/FAIL
  집합을 내는지 대조한다 — 이관 자체가 코드 로직을 바꾸지 않으므로 결과가 완전히 같아야 함.

---

## 9. Next Steps

1. 이 계획 문서에 대한 사용자 최종 승인
2. `<name>.sizing_spec.json` 스키마의 `_TEMPLATE.sizing_spec.json` 스캐폴드 작성
3. §8 파일 구조대로 5개 신규 파일(+`tests/` 6개, `stick_diagram.py` self-test 이관분 포함)
   스캐폴딩 — 빈 함수 시그니처와 docstring만 먼저 작성해 구조를 고정
4. `stick_diagram.py`의 인라인 self-test(8980~12923줄)를 `tests/test_stick_diagram.py`로
   이관하고 §8.8의 회귀 대조(이관 전/후 PASS/FAIL 집합 동일) 확인 — 다른 신규 함수 구현보다
   먼저 해도 되는 독립 작업이라 가장 먼저 처리
5. §7.2/§8.3~8.5 신규 함수 구현 + 대응 test 파일에 self-test 작성(파일럿 회로 착수 전,
   toy LUT로 단위 검증)
6. `current_reuse_telescopic_ota` 파일럿 이관 + §4 Success Criteria 전항목 검증
7. 검증 통과 시 나머지 3개 토폴로지 이관 계획을 별도 문서로 후속 작성

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-09-04 | 초안 작성 — SPICE 트랜지언트 검증 중 발견한 diode-connected 헤드룸 버그를 계기로 gain-budget-first 근본 재설계안 정리 |
| 1.1 | 2026-09-04 | §8 추가 — 3단계 실행 파이프라인(topology 수집/gm-ID 사이징+레이아웃 수렴/결과물 산출)을 대표하는 5개 신규 파일 + top-level harness 함수 구조 확정, self-test를 `tests/test_<module>.py`로 분리하는 방침 확정 |
| 1.2 | 2026-09-04 | `stick_diagram.py`의 기존 인라인 self-test(8980~12923줄)도 `tests/test_stick_diagram.py`로 이관하는 것으로 §8.2/§8.8/Next Steps 수정(처음엔 재구조화 범위 밖으로 뒀으나 사용자 지시로 포함) |
