---
template: plan
version: 1.3 (adapted — non-web project)
---

# analog-topology-json-library Planning Document

> **Summary**: `analog-gmid-design` skill의 topology netlist/matching/floorplan 정보를
> Python 코드 하드코딩에서 topology당 1개의 JSON library 파일로 분리하고, 기존 ~30개
> 계산 함수는 그대로 둔 채 JSON 입출력을 담당하는 얇은 오케스트레이션 레이어를 추가한다.
>
> **Project**: chip-design-skills (analog-gmid-design skill)
> **Author**: Claude Code
> **Date**: 2026-07-28
> **Status**: Draft — Design 단계에서 구체 스키마 승인 필요

---

## Executive Summary

> **2026-07-28 최종 수정**: 아래 내용은 구현 중 스키마가 3차례 조정된 뒤의 최종 상태를
> 반영한다 — 특히 "topology JSON이 floorplan/layout 인접정보까지 담는다"는 초기 발상은
> 실측으로 폐기됐다(§2.2 참고: matching 배치는 finger 개수가 정해져야 계산 가능한데, 그건
> 사이징 결과값이라 topology 단계엔 없다). topology JSON은 이제 **connectivity + matching
> kind + 위상보정 함수 참조만** 담고, floorplan/layout은 전부 사이징 이후 instance-output
> JSON에서 계산된다.

| Perspective | Content |
|-------------|---------|
| **Problem** | `folded_cascode_example()`/`two_stage_ota_example()`처럼 회로 netlist(Transistor 리스트) + 대칭성/matching 정보가 Python 코드 안에 직접 하드코딩돼 있다. 새 topology마다 코드를 새로 짜야 하고, sizing만 바뀌어도 layout 구조를 기계적으로 재현할 방법이 없다. 리포트를 완성하는 agent가 문서(prose)를 해석해 layout을 다르게 재구성할 위험도 여기서 비롯된다(PRE-FLIGHT 사고27 참고). |
| **Solution** | topology의 **사이징과 무관한** 구조적 정보(connectivity + 대칭성/matching kind + 위상보정 함수 참조)를 topology당 JSON 1개로 분리해 `library/` 폴더에 모은다. 기존 계산 함수(`build_graph`/`check_euler_condition`/`check_box_shape`/`pack_floorplan_grouped` 등 ~30개)는 시그니처를 바꾸지 않고, 그 위에 "JSON 로드 → 기존 함수 호출 → 결과를 JSON에 다시 씀"을 담당하는 오케스트레이션 레이어를 신설한다. layout/floorplan(finger 배분·row 분할·좌표)은 사이징 이후에만 계산 가능하므로 topology JSON이 아니라 instance-output JSON에서 만든다. `sizing_recipe.py`는 기존 인자 호출 방식을 유지하면서 JSON 입출력도 추가로 지원하도록 확장한다. |
| **Function/UX Effect** | 새 회로 설계 시 topology JSON(connectivity+matching+compensation)과 사이징 값을 `run_topology_pipeline()`에 넘기면, layout 계산(box-shape/matching-safety/floorplan)이 기계적으로 검증 가능해진다. 최종 사이징+layout 결과를 담은 instance-output JSON을 layout 실행 agent에게 그대로 넘기면, 그 agent가 문서를 해석해 다르게 만들 여지가 사라진다. |
| **Core Value** | 재현성(reproducibility) + agent 간 해석 불일치 제거 — 이번 세션에서 실제로 재발한 "fresh agent가 스펙을 다르게 해석해 floorplan/stick diagram을 누락한" 사고 유형을 구조적으로 차단한다. |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | topology netlist가 Python 코드 하드코딩이라 재현 불가능, agent마다 해석이 달라짐 |
| **WHO** | 이 skill을 사용해 아날로그 회로 sizing+layout 리포트를 작성하는 (fresh) agent 세션들 |
| **RISK** | 오케스트레이션 레이어 설계가 기존 30개 함수의 self-test 회귀를 깨뜨릴 위험 — Design 단계에서 "함수 시그니처 무변경" 원칙으로 최소화(실제로 끝까지 지켜짐) |
| **SUCCESS** | folded_cascode/two_stage_ota 두 example이 JSON library 항목(connectivity+matching)으로 이관된 뒤, connectivity가 기존 하드코딩 버전과 100% 동일하고 파이프라인이 정직한 box-shape/audit/floorplan 결과를 산출 |
| **SCOPE** | 이번 작업: 스키마 설계 + 오케스트레이션 레이어 + 2개 example 이관 + telescopic OTA 시연·전체 리포트 완성 |

---

## 1. Overview

### 1.1 Purpose

topology의 netlist·대칭성/matching kind·위상보정 함수 참조를 재사용 가능한 데이터(JSON)로
분리해, 같은 topology를 다른 spec으로 재사이징해도 layout 계산(box-shape/matching-safety/
floorplan)을 기계적으로 재현할 수 있게 한다. layout 자체(finger 배분/row 분할/좌표)는
사이징 이후에만 의미가 있으므로 topology JSON에는 담지 않는다.

### 1.2 Background

이번 세션 중 "새 background agent를 새 context로(힌트 없이) 띄워 논문을 구현시키는" 블라인드
재현 테스트에서, agent가 sizing은 정확히 했지만 §5(stick diagram)의 일부 sub-block과 §8
(floorplan) 전체를 누락한 채 "완료"로 보고하는 사고가 발생했다(design-report-spec.md
PRE-FLIGHT 사고27). 원인 중 하나는 topology 구조 정보가 prose 문서로만 존재해 agent가
매번 코드를 새로 해석/작성해야 했다는 것 — 사용자는 이 근본 원인을 "topology 구조 정보 자체를
기계가 읽는 JSON으로 고정하면, 해석 여지가 사라진다"는 방향으로 지적했다.

### 1.3 Related Documents

- `skills/analog-gmid-design/references/design-report-spec.md` PRE-FLIGHT 사고 1~27
- `skills/analog-gmid-design/references/stick-diagram-euler-layout.md`
- `skills/analog-gmid-design/assets/stick_diagram.py` (Transistor 클래스, ~30개 계산 함수)

---

## 2. Scope

### 2.1 In Scope

- [x] topology library JSON 스키마 설계 — **최종**: connectivity(netlist) + 대칭성/matching
      kind(`symmetry`) + 위상보정 함수 참조(`compensation`)만. layout/floorplan은 사이징과
      무관하지 않다는 게 실측으로 드러나 topology JSON에서 제외(구현 중 3차 수정, 완료)
- [x] instance-output JSON 스키마 설계 (topology 구조 + 실제 사이징 값 + 그 값으로 계산한
      layout 결과 전부 — layout 실행 agent에게 그대로 전달하는 최종 산출물). 완료
- [x] `stick_diagram.py`에 오케스트레이션 레이어 추가 (`load_topology()`/
      `run_topology_pipeline()`/`save_instance_json()`) — 기존 ~30개 계산 함수 시그니처는
      변경하지 않는다(끝까지 지켜짐). 완료
- [x] `sizing_recipe.py`에 JSON 입출력 지원 추가(`load_sizing_targets()`/
      `write_sizing_results()`/`run_sizing_pipeline()`) — 기존 인자 호출 방식과 공존. 완료
- [x] `folded_cascode_example()`을 `library/folded_cascode.topology.json`으로 이관(connectivity
      diff=0 확인). 완료
- [x] `two_stage_ota_example()`을 `library/two_stage_ota.topology.json`으로 이관(connectivity
      diff=0 확인, `compensation`을 `miller_ota_topology`로 연결). 완료
- [x] 이관 후 connectivity가 기존 example과 동일한지 회귀 검증 — 완료. **box-shape/audit_row_
      split/floorplan은 "기존 하드코딩 버전과 동일"이 목표가 아니다** — `run_topology_
      pipeline()`은 row 분할을 자동 탐색하지 않으므로 단일 행 후보 기준의 정직한 결과(현재는
      branch_symmetric/diff_pair 쌍에서 FAIL)를 낸다. 이는 알려진 설계상 한계이지 회귀가 아니다
- [ ] **(2026-07-28 추가, 사용자 확인)** `library/_TEMPLATE.topology.json` 스캐폴드 +
      "논문/스펙 → topology JSON" 작성 절차(Design §4.5)를 **current-reuse telescopic OTA
      논문에 실제로 적용해 시연** — folded_cascode/two_stage_ota만으로는 스키마가 "이미 있는
      구조를 JSON으로 옮기는 것"만 검증하지 "새 논문에서 처음부터 authoring"이 실제로
      가능한지는 검증하지 못한다(순환 검증 위험 — 스키마 자체가 그 두 example에서
      역설계됐으므로). telescopic OTA는 이미 이번 세션에서 한 번 읽혔고, Class-AB/bias-gen/
      CMFB처럼 기존 두 example에 없는 구조(예: 기존 3개 compensation 함수와 안 맞는 새
      위상보정 방식일 가능성)를 갖고 있어 더 강한 검증이 된다. 시연 결과로 스키마/절차의
      부족한 부분을 찾아 기록한다(§4 Success Criteria 참고)
- [ ] **(2026-07-28 재추가, 사용자 확인 — 범위 재확대)** telescopic OTA의 **전체 리포트를
      완성**한다 — 시연용 topology JSON 작성에서 멈추지 않고, 그 JSON을 실제로
      `run_sizing_pipeline()`/`run_topology_pipeline()`으로 끝까지 돌려 21개 소자(Stage-1/
      Stage-2/Class-AB/bias-gen/CMFB) 전부의 사이징+stick diagram+floorplan을 계산하고,
      `workspaces/current-reuse-telescopic-ota-report/final_report.html`을 완전한 8섹션
      리포트(§7 표 참고 — 특히 8번 물리 floorplan)로 갱신한다. 이것이 원래 사고
      (PRE-FLIGHT 27번 — floorplan 통째로 누락, CMFB/bias-gen/Class-AB stick diagram 누락)를
      이 새 도구로 실제로 재현 없이 완주할 수 있는지의 최종 증거가 된다

### 2.2 Out of Scope

- `sizing_recipe.py`의 범용 수치 엔진(GmIdLUT/size_transistor/optimize_multistage) 내부 로직
  변경 — JSON 입출력만 추가, 계산 로직 자체는 무변경
- `topology_library.py`의 위상보상 방정식(miller_ota_topology 등) 내부 로직 변경 — 단, telescopic
  OTA가 기존 3개 함수와 안 맞으면 `compensation: null`로 두고 새 함수 유도는 하지
  않는다(Design §4.5 6단계 원칙 그대로 — 새 함수 유도는 `topology-fn-derivation-guide.md`
  절차이고 이번 범위 밖)
- telescopic OTA **회로 자체의 새로운 설계 개선**(예: 논문과 다른 spec으로 재사이징) — 기존
  `sizing_results.json`의 spec을 그대로 재현하는 것이 목적이지 새 설계를 하는 게 아니다

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | topology library JSON 스키마가 소자 connectivity(name/kind/source/drain/gate)를 온전히 표현 — **W/L/finger_w/n_fingers는 제외**(사이징 산출물, 구현 중 수정) | High | Done |
| FR-02 | 스키마가 대칭성/matching 선언(kind: current_mirror/diff_pair/branch_symmetric, pair 목록)을 표현 | High | Done |
| FR-03 | ~~스키마가 layout 그룹핑(sub-block/stack_id 배정)을 표현~~ — **폐기**: stack_id 배정은 사이징 이후 `sizing_overrides`로만 정해지며 topology JSON은 이를 표현하지 않는다(구현 중 실측으로 확정) | — | Dropped |
| FR-04 | ~~스키마가 floorplan 인접정보를 표현~~ — **폐기**: floorplan은 instance-output JSON에서만 `pack_floorplan_grouped()`를 실제 실행해서 얻는다(`run_topology_pipeline()`의 `floorplan_hints` 선택 인자로 커스텀 그룹핑만 지원, topology JSON 필드는 아님) | — | Dropped |
| FR-05 | `load_topology(json_path)` → `Transistor` 객체 리스트(connectivity만) + `meta`(symmetry/compensation)로 변환 | High | Done |
| FR-06 | `run_topology_pipeline()`이 기존 계산 함수(`split_into_stacks`/`check_box_shape`/`audit_row_split`/`pack_floorplan_grouped`/`check_stick_diagram_coverage`)를 그대로 호출하고 결과를 반환 — `run_full_circuit_audit()`는 `dispositions` 판단이 필요해 의도적으로 미포함(호출자가 별도 호출) | High | Done |
| FR-07 | `sizing_recipe.py`가 JSON에서 gm/ID sizing 목표를 읽고(`load_sizing_targets`) 결과(W/L/ID/gm)를 JSON에 쓰는(`write_sizing_results`) 경로 지원, 기존 함수 인자 호출 방식은 그대로 유지 | High | Done |
| FR-07b | (신설) `run_sizing_pipeline()`이 topology JSON의 `compensation` 참조를 `_COMPENSATION_REGISTRY`(allowlist)로 조회해 `topology_library.py` 함수를 안전하게 호출 | High | Done |
| FR-08 | `folded_cascode_example()`/`two_stage_ota_example()` 이관 후 **connectivity**가 기존 example과 diff=0 재현(self-test 자체는 아직 통합 전 — 배치 4 예정) | High | Done(connectivity) / Pending(self-test 통합) |
| FR-09 | instance-output JSON은 layout 실행 agent가 별도 해석 없이 그대로 소비 가능한 형태(사이징된 netlist/floorplan 좌표/box-shape·audit 판정/coverage 포함) | High | Done |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| 회귀 안전성 | 기존 30개 함수 시그니처 무변경, self-test 전량 exit 0 | `PYTHONIOENCODING=utf-8 python stick_diagram.py`/`sizing_recipe.py` — 확인 완료 |
| 재현성 | 같은 topology JSON + 같은 sizing_overrides → 항상 동일한 layout 결과(row 분할은 자동 탐색하지 않으므로 "동일 입력 → 동일 출력"이 재현성의 정의다, "항상 PASS"가 아니다) | 이관된 두 example의 connectivity를 기존 하드코딩 버전과 diff(diff=0 확인), 동일 sizing_overrides 재실행 시 결과 동일성 |
| 해석 명확성 | instance-output JSON을 받은 agent가 추가 판단 없이 layout 실행 가능 | Design 단계에서 스키마 필드별 "이 필드만 보면 무엇을 할 수 있는가" 명세 완료 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [x] topology library JSON 스키마 문서화 완료(Design 문서에서 최종 확정 — connectivity+
      matching kind+compensation 참조만, layout/floorplan은 instance 단계로 이동)
- [x] instance-output JSON 스키마 문서화 완료
- [x] 오케스트레이션 레이어 함수 구현 + docstring(`load_topology`/`run_topology_pipeline`/
      `save_instance_json`)
- [x] `sizing_recipe.py` JSON I/O 확장 구현(`load_sizing_targets`/`write_sizing_results`/
      `run_sizing_pipeline`)
- [x] `library/folded_cascode.topology.json`, `library/two_stage_ota.topology.json` 생성
- [x] 이관 회귀 검증 통과 — **connectivity가 기존 example과 diff=0**(box-shape/audit_row_split
      결과는 "기존과 동일"이 기준이 아니다 — row 분할 미탐색 상태의 정직한 결과가 기준)
- [x] `library/_TEMPLATE.topology.json` 스캐폴드 생성 + 논문→JSON 절차 문서화(Design §4.5)
- [x] **telescopic OTA 논문으로 시연 — 완료**: 원문 PDF 18페이지 직접 재확인, 41개 소자
      `library/current_reuse_telescopic_ota.topology.json` 작성 → `load_topology()`/
      `run_topology_pipeline()` 실제 실행 검증 → `docs/03-analysis/analog-topology-json-
      library.gap-findings.md`에 7개 실제 발견 기록. 핵심 발견: (1) `compensation: null`
      판단이 다시 한번 정확했음(구조 불일치), (2) `find_matching_candidates()`의
      `diff_pair` 경로가 W를 요구해 topology 단계에서 항상 빈 결과 반환(Design §4.5 절차
      수정함), (3) `run_topology_pipeline()`이 확신도 LOW로 표시한 bias-gen sub-block의
      실제 연결 결함(Euler 불가)을 정확히 잡아냄 — 검증 게이트의 실전 가치 확인,
      (4) `check_stick_diagram_coverage()`가 41개 소자 전부 커버 확인(PRE-FLIGHT 사고27
      재발 없음)
- [ ] **telescopic OTA 전체 리포트 완성**: 21개 소자 전부 사이징+stick diagram+floorplan 계산,
      `run_full_circuit_audit()`/`check_stick_diagram_coverage()` 둘 다 `ok=True`,
      `final_report.html`이 8개 섹션(물리 floorplan 포함) 전부를 담고 있음을 시각 검증
- [ ] `stick_diagram.py` self-test 전체 exit 0
- [ ] `function-selection-map.md`/`SKILL.md`/`consistency-map.md`에 새 함수/스키마 반영

### 4.2 Quality Criteria

- [ ] 기존 self-test(Test 1~25) 전부 여전히 PASS
- [ ] 새 오케스트레이션 함수에 대한 self-test 추가

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| JSON 스키마가 실제로 필요한 정보(예: interdigitation 패턴, common-centroid 배치)를 다 못 담아 결국 다시 prose로 보충 설명해야 함 | High | Medium | Design 단계에서 이관 대상 두 example의 실제 데이터(M3/M4 current_mirror, M1/M2 diff_pair, M5/M6 branch_symmetric 등)를 스키마에 직접 채워 넣어보며 필드 부족을 조기 발견 |
| 오케스트레이션 레이어가 기존 함수 호출 순서(§1.6 run_full_circuit_audit 단일 게이트 원칙 등)를 깨뜨림 | High | Low | 오케스트레이션 함수는 기존 harness 함수(run_full_circuit_audit/check_stick_diagram_coverage) 호출 순서를 그대로 재현하고, 직접 로직을 새로 만들지 않는다 |
| `sizing_recipe.py` JSON I/O 추가가 기존 `optimize_multistage()` 등 호출부(다른 세션의 스크립트)를 깨뜨림 | Medium | Low | 기존 함수 시그니처는 무변경, JSON I/O는 별도 wrapper 함수로만 추가 |

---

## 6. Impact Analysis

### 6.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|--------------------|
| `stick_diagram.py` | Python asset | `load_topology()`/`save_topology()`류 오케스트레이션 함수 추가, `folded_cascode_example()`/`two_stage_ota_example()`는 JSON 로더로 대체(또는 병행 유지) |
| `topology_library.py` | Python asset | topology 구조 선언을 JSON에서 읽는 경로 추가 |
| `sizing_recipe.py` | Python asset | JSON 입출력 wrapper 함수 추가 |
| `library/*.json` (신규) | 데이터 파일 | topology 구조 정본 |
| `function-selection-map.md`/`SKILL.md`/`consistency-map.md` | 문서 | 새 함수/스키마 반영 |

### 6.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| `folded_cascode_example()` | CALL | 이번 세션의 self-test Test 1~24, scratchpad `save_final_json.py` | Needs verification — 결과 동일성 회귀 검증 필수 |
| `two_stage_ota_example()` | CALL | 이번 세션의 self-test, scratchpad 스크립트 | Needs verification |
| 기존 ~30개 계산 함수 | CALL | self-test `__main__` 블록 전체 | None — 시그니처 무변경이 설계 원칙 |

### 6.3 Verification

- [ ] 이관 전/후 `folded_cascode_example()`/`two_stage_ota_example()` 결과 diff
- [ ] self-test 전체 재실행, exit 0 확인

---

## 7. Architecture Considerations

> Next.js/웹앱 전용 프레임워크 선택 섹션(원 템플릿 7.1/7.2/8.3/8.4)은 이 프로젝트(Python
> 기반 analog-gmid-design skill)에 해당 없음 — 생략. 구체적 JSON 스키마 옵션 비교는
> `/pdca design` 단계에서 3안 비교 후 사용자 승인을 받는다.

### 7.1 확정된 설계 원칙 (사용자 승인 완료)

| 결정 | 선택 | 근거 |
|------|------|------|
| 리팩토링 범위 | `topology_library.py` + `stick_diagram.py` (JSON화) + `sizing_recipe.py`(JSON I/O 추가, 엔진 로직 무변경) | 사용자 확인 |
| 함수 재사용 방식 | 기존 함수 시그니처 무변경, 오케스트레이션 레이어 신설 | 사용자 확인 — 회귀 위험 최소화 |
| 마이그레이션 대상 | folded_cascode, two_stage_ota 두 example만 | 사용자 확인 — telescopic OTA는 별도 세션 |

---

## 9. Next Steps

1. [ ] `/pdca design analog-topology-json-library` — 구체 JSON 스키마 3안 비교, 사용자 승인
2. [ ] 승인된 설계로 오케스트레이션 레이어 + 스키마 구현 (`/pdca do`)
3. [ ] 회귀 검증 + 문서 반영

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-28 | Initial draft (Checkpoint 1/2 확인 완료) | Claude Code |
