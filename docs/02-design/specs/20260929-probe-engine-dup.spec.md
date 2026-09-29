---
id: 20260929-probe-engine-dup
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

design `20-dead-code-dup` v1.2 §2.2-4·§3 PROBE-DUP·§5·§5.1·§8 P4: `A/tests/probes/`에 남는 **진단 스크립트** 안의 엔진 식 재구현을 엔진 정본
호출로 바꾸고(정의가 하나여야 엔진이 바뀔 때 같이 따라간다, WP-14), 재구현이 다시 들어오지 않게 스캐너 `A/tests/tools/probe_dup_scan.py`를
만든다. 진단은 판정이 아니므로 자기참조 문제가 없다(§5.1 -- 승격한 test의 재구현은 oracle이라 이 card 대상이 아니다).
A = `skills/analog-gmid-design/assets`.

대상 범위(원자료 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe_inventory.json`의 `confirmed_engine_dup` 34곳 중, 2026-09-29 현재
`A/tests/probes/`에 있는 probe 12개의 19곳): 삭제된 probe 3개(P1), 승격된 `unit/test_probe_gm_id_monotonicity.py`·`unit/test_probe_prevention_wiring.py`
(§5.1 oracle 유지), 보류 중인 `A/tests/probe_physical_consistency.py`(P3c 보류 -- 승격 후보라 probes/ 밖)는 대상이 아니다.
`probe_mirror_common_L` 93행의 소자·넷 이름 리터럴(원자료 '(참고)' 항목)은 식 재구현이 아니라 DF-23 리터럴이라 대상이 아니다.

| probe(`A/tests/probes/`) | 재구현(원자료 줄, P2 이동 뒤 몇 줄 어긋날 수 있음) | 정본 |
|---|---|---|
| `probe_diode_min_vgs` | 93-104 union-find 동치류 | `sizing_recipe.l_sharing_classes` |
| `probe_diode_vds_window` | 72-76 W = L*ID/IDu | `sizing_recipe.size_transistor` |
| `probe_mirror_common_L` | 97-99 IDu -- LUT private(`_query`·`_log_ID`·`_w_ref_effective`) | `SemiEmpiricalGmIdLUT.id_density_at_vgs` |
| `probe_mirror_design_space` | 164 (gate, source, kind) 미러군 / 170 diode gate==drain / 220-253 W 인라인 | `true_current_mirror_groups` / `is_diode_connected` / `size_transistor` |
| `probe_mirror_gain_ranking` | 158 미러군 / 164 diode / 194-201 W 인라인 | 같음 |
| `probe_mirror_infeasibility` | 87-89 IDu private / 115-116·163-164 W 인라인 | `id_density_at_vgs` / `size_transistor` |
| `probe_mirror_wiring_readiness` | 96 미러군 / 102 diode | `true_current_mirror_groups` / `is_diode_connected` |
| `probe_ratio_pair_analysis` | 145-148 게이트·소스 공유 인라인 판정 | `true_current_mirror_groups` |
| `probe_stack_headroom_feasibility` | 63-74 union-find 스택 그룹 | `l_sharing_classes` 또는 `_hr_resolve_vertical_group`(의미가 같은 쪽) |
| `probe_stacked_diode_options` | 79-80 IDu private / 89-90 W 인라인 | `id_density_at_vgs` / `size_transistor` |
| `probe_supply_current` | 55-66·92-96 레일 직결 공급전류 합 + 레일 집합 재선언 | `sizing_recipe._metric_supply_current` / `_DEFAULT_RAIL_HI`·`_DEFAULT_RAIL_LO` |
| `probe_vds_assignment_paths` | 129 diode gate==drain | `is_diode_connected` |

## 관찰 가능한 계약

1. **스캐너** `A/tests/tools/probe_dup_scan.py`가 생긴다(신규 시그니처 표). `scan_source(source, path)`는 아래 규칙마다 발견을 돌려주고,
   `main(argv)`는 `--root <저장소 루트>`로 `A/tests/probes/**/*.py`를 훑어 발견을 한 줄 JSON씩 출력하고 발견 0이면 exit 0, 1개 이상이면 1,
   입력 오류(없는 루트·구문 오류 파일)는 2다. 발견 한 건 = `{"path", "line", "rule", "concept"}`.
   규칙(엔진 정본과 같은 식의 재구현 -- 위 표의 개념 7종을 AST로):
   * `lut-private`: 어떤 객체든 메서드 `._query(…)`·`._w_ref_effective(…)` **호출**(LUT private 경로로 IDu를 다시 세우는 모양). 데이터 속성
     `_log_ID`·`_grids_list` 읽기만으로는 발견이 아니다 -- `probe_interp_scheme_loo`(99행)는 보간 방식 자체를 실험하는 진단이라 엔진 식 재구현이
     아니고 그 속성을 읽을 수밖에 없다(2026-09-29 착수 전 grep 확인).
   * `diode-inline`: `gate`와 `drain`(속성 `.gate`/`.drain` 또는 첨자 `["gate"]`/`["drain"]`)을 `==`·`!=`로 비교.
   * `mirror-key`: 한 튜플 리터럴 안에 `gate` 접근과 `source` 접근이 함께 있음(미러군 키).
   * `gate-source-share`: 한 불 연산(`and`) 안에 `gate`끼리 비교와 `source`끼리 비교가 함께 있음.
   * `w-inline`: `A * B / C` 모양 산술에서 나눗셈 오른쪽 이름(또는 속성)이 대소문자 무시 `idu`를 포함.
   * `union-find`: `while`의 조건이 `P[x] != x`(같은 이름을 첨자와 비교 대상으로 쓰는 부모 추적) 모양.
   * `rail-set`: 문자열 상수 2개 이상으로 된 집합·리스트·튜플 리터럴에서 원소가 모두 대소문자 무시 레일 이름 후보
     (`vdd`·`vss`·`gnd`·`agnd`·`avdd`·`avss`·`dvdd`·`dvss`)인 것.
2. **교체**: 위 표 19곳을 정본 호출로 바꾼다 -- 정본: `l_sharing_classes`, `_hr_resolve_vertical_group`, `size_transistor`,
   `id_density_at_vgs`, `true_current_mirror_groups`, `is_diode_connected`, `_metric_supply_current`(레일 집합은 모듈 상수
   `sizing_recipe._DEFAULT_RAIL_HI`·`sizing_recipe._DEFAULT_RAIL_LO`). 병합본에서 `main --root <병합본>`이 exit 0, 발견 0(PROBE-DUP).
3. **출력 보존(F4)**: 바꾼 probe마다 교체 전(base)과 교체 뒤의 실행 출력(stdout, 경로 정규화 뒤)이 같다. 다르면 그 probe는 **교체하지 않고 멈춰**
   오케스트레이터에게 차이를 보고한다(결함 후보 -- 제외·면제 방식은 그때 정한다). base에서 끝까지 돌지 않는 probe(예외·시간 초과)는 그 사실과
   교체 뒤에도 같은 지점·같은 예외인지를 보고한다.
4. **B22 (c) 동반 정리**: `A/tests/probes/` 14개 파일 주석의 `H.derived_spec(key, why, **overrides)` 안내 문장(P5에서 지운 함수)을 지우거나 사실에
   맞게 고친다(주석만, 계산 불변).
5. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 바뀌지 않는다. 승격 test(`A/tests/unit/**`)·`A/tests/probe_physical_consistency.py`는 바뀌지 않는다.
   수집 집합은 base에서 사라진 id 0(probes/·tools/는 수집 대상이 아니다).
6. E-LIB·E-INST: 엔진 불변이라 base와 같다(엔진 blob 동일로 확인 가능).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `probe_dup_scan` | `*` | 신규 모듈 `A/tests/tools/probe_dup_scan.py` |
| `probe_dup_scan` | `scan_source` | `def scan_source(source: str, path: str) -> list` |
| `probe_dup_scan` | `main` | `def main(argv: list) -> int` |

## 판정 유형 근거

red-green: 스캐너가 base에 없으므로 계약 1의 test가 base에서 ImportError(red)이고, code-author가 스캐너를 더한 병합본에서 green이다. 도구
추가에 code 커밋·병합이 생기므로 test-only가 아니다(P2 교훈). probe 교체와 주석 정리는 test 경로(`A/tests/probes/`)라 test 커밋에 든다.

## oracle 종류와 출처

(a) 구성 입력: 스캐너 규칙마다 합성 소스 조각(발견해야 할 것·발견하면 안 되는 것)을 test가 만든다 -- 기대는 이 card 계약 1의 규칙 문장.
(c) 동작 보존: probe 출력 교체 전후 동일(기대값 = base 실행 출력). 발견 0은 병합본에서 스캐너를 돌린 결과.

## 거부해야 할 입력

규칙마다 합성 재구현 조각 -- 스캐너가 발견을 내고 `main`이 exit 1. 구문 오류 파일 → exit 2. 정본 호출만 쓰는 조각·주석·문자열 안의
같은 글자·다른 이름(`gate_bias`, `source_file` 등) → 발견 0(오탐 없음).

## library 회로 적용 여부

probe가 읽는 library 회로(파일럿 등)는 출력 보존(계약 3)으로 확인한다. 엔진 불변이라 E-LIB·E-INST는 동일.

## 무동작 판정 입력(무발동 값)

`A/tests/unit/**` 승격 test와 나머지 test 전부 -- 판정이 base와 같다. 재구현이 없는 probe 20개는 스캐너 발견 0이고 바뀌지 않는다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(design 승인 `20260923-20-dead-code-dup-design`). F4(출력이 바뀌는 교체)가 나오면 그 probe를 멈추고 보고한다 -- 제외 방식(면제 목록 등)은
그때 사용자 결정으로 정한다(skip을 미리 만들지 않는다).
