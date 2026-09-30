---
id: 20260929-probe-engine-dup
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
approval: 20260929-p4-scan-exempt
approval: 20260930-p4-relocate-test-retire
---
## 의도

design `20-dead-code-dup` v1.2 §2.2-4·§3 PROBE-DUP·§5·§5.1·§8 P4: `A/tests/probes/`에 남는 **진단 스크립트** 안의 엔진 식 재구현을 엔진 정본
호출로 바꾸고(정의가 하나여야 엔진이 바뀔 때 같이 따라간다, WP-14), 재구현이 다시 들어오지 않게 스캐너 `A/tests/tools/probe_dup_scan.py`를
만든다. 진단은 판정이 아니므로 자기참조 문제가 없다(§5.1 -- 승격한 test의 재구현은 oracle이라 이 card 대상이 아니다).
A = `skills/analog-gmid-design/assets`.

**재구현의 기준은 '같은 개념의 같은 식'이다** -- 식 모양이 비슷해도 엔진 정본과 다른 질문에 답하면 복제가 아니다(1차 시도 실측, 아래 개정 기록).
대상 범위(원자료 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/probe_inventory.json`의 `confirmed_engine_dup` 중 2026-09-29 현재
`A/tests/probes/`에 있는 것, 1차 시도 측정으로 다시 가름): 삭제된 probe 3개(P1), 승격된 `unit/test_probe_gm_id_monotonicity.py`·`unit/test_probe_prevention_wiring.py`
(§5.1 oracle 유지), 보류 중인 `A/tests/probe_physical_consistency.py`(P3c 보류)는 대상이 아니다. `probe_mirror_common_L` 93행의 소자·넷 이름
리터럴은 DF-23 리터럴이라 대상이 아니다.

| probe(`A/tests/probes/`) | 교체 대상(원자료 줄, P2 이동 뒤 어긋날 수 있음) | 정본 |
|---|---|---|
| `probe_diode_vds_window` | 72-76 gm/ID 입력에서 W | `sizing_recipe.size_transistor` |
| `probe_mirror_common_L` | 97-99 IDu -- LUT private | `SemiEmpiricalGmIdLUT.id_density_at_vgs` |
| `probe_mirror_design_space` | 164 (gate, source, kind) 미러군 / 170 diode / 229-230 IDu private | `true_current_mirror_groups` / `is_diode_connected` / `id_density_at_vgs` |
| `probe_mirror_gain_ranking` | 158 미러군 / 164 diode / 194 IDu private | 같음 |
| `probe_mirror_infeasibility` | 87-89 IDu private | `id_density_at_vgs` |
| `probe_mirror_wiring_readiness` | 96 미러군 / 102 diode | `true_current_mirror_groups` / `is_diode_connected` |
| `probe_ratio_pair_analysis` | 145-148 게이트·소스 공유 인라인 판정 | `true_current_mirror_groups` |
| `probe_stacked_diode_options` | 79-80 IDu private | `id_density_at_vgs` |
| `probe_supply_current` | 55-66·92-96 레일 직결 공급전류 합 + 레일 집합 재선언 | `sizing_recipe._metric_supply_current` / `_DEFAULT_RAIL_HI`·`_DEFAULT_RAIL_LO` |
| `probe_vds_assignment_paths` | 129 diode gate==drain | `is_diode_connected` |

대상에서 뺀 것(재구현 아님, 1차 시도 측정):
* **정해진 VGS에서의 W = L·ID/IDu**(`probe_mirror_design_space` 220-253, `probe_mirror_gain_ranking` 194-201, `probe_mirror_infeasibility`
  115-116·163-164, `probe_stacked_diode_options` 89-90): `size_transistor`는 gm/ID에서 VGS를 다시 풀어 W를 낸다 -- 다른 질문이다. 교체하면
  PMOS 그룹에서만 출력이 달라졌다(예: M6 요구 W 102.756 → 21.337 um). IDu 조회 부분만 정본으로 바꾼다.
* **union-find**(`probe_diode_min_vgs` 93-104, `probe_stack_headroom_feasibility` 63-74): `l_sharing_classes`는 '같은 L' 동치류(미러·ratio 쌍 포함)이고
  probe가 묶는 것은 다른 개념이다(이 회로에서 출력이 같은 것은 우연). 알고리즘 모양이 같다고 엔진 식 복제가 아니다.
* **VGS 기준 gm·gds 조회**(`probe_mirror_gain_ranking`의 `_q` → `lut._query(lut._log_GM/_log_GDS, …)`): 공개 API가 없다(`gm_gds_ratio(gm_id)`는
  VGS를 다시 풀어 위와 같은 문제). 승인 면제 `20260929-p4-scan-exempt`로 스캐너 발견에서 뺀다 -- 공개 API는 Phase 4 백로그.

## 관찰 가능한 계약

1. **스캐너** `A/tests/tools/probe_dup_scan.py`가 생긴다(신규 시그니처 표). `scan_source(source, path)`는 아래 규칙마다 발견을 돌려주고,
   `main(argv)`는 `--root <저장소 루트>`로 `A/tests/probes/**/*.py`를 훑어 발견을 한 줄 JSON씩 출력한다. 발견 한 건 =
   `{"path", "line", "rule", "concept", "exempt"}`, `path`는 루트 기준 상대 경로(`/` 구분). 면제되지 않은 발견이 0이면 exit 0, 1개 이상이면 1,
   입력 오류(없는 루트·구문 오류 파일)는 2다.
   규칙(AST, 아래 '접근'은 속성 `.gate`, 첨자 `["gate"]`, `.get("gate")` 셋 다):
   * `lut-private`: 어떤 객체든 메서드 `._query(…)`·`._w_ref_effective(…)` **호출**(LUT private 경로로 IDu 등을 다시 세우는 모양). 데이터 속성
     `_log_ID`·`_grids_list` 읽기만으로는 발견이 아니다 -- `probe_interp_scheme_loo`(99행)는 보간 방식 자체를 실험하는 진단이다.
   * `diode-inline`: `gate` 접근과 `drain` 접근을 `==`·`!=`로 비교.
   * `mirror-key`: 한 튜플 리터럴 안에 `gate` 접근과 `source` 접근이 함께 있음(미러군 키).
   * `gate-source-share`: 한 `and` 안에 `gate` 접근끼리 비교와 `source` 접근끼리 비교가 함께 있음.
   * `rail-set`: 문자열 상수 2개 이상으로 된 집합·리스트·튜플 리터럴에서 원소가 모두 대소문자 무시 레일 이름 후보
     (`vdd`·`vss`·`gnd`·`agnd`·`avdd`·`avss`·`dvdd`·`dvss`)인 것.
   **면제**: `main`은 `<root>/.ai/approvals/*.md`(이름이 `_`로 시작하지 않는 것) 중 머리 블록에 `target_kind: decision`이 있는 기록의 `target:` 값
   (`,`로 나눈 원소)을 읽고, 원소 `<path>::<rule>`과 같은 발견에 `"exempt": true`를 붙여 exit 판정에서 뺀다(C13 decision 면제와 같은 읽기).
2. **교체**: 위 표의 곳을 정본 호출로 바꾼다 -- 정본: `size_transistor`, `id_density_at_vgs`, `true_current_mirror_groups`, `is_diode_connected`,
   `_metric_supply_current`(레일 집합은 모듈 상수 `sizing_recipe._DEFAULT_RAIL_HI`·`sizing_recipe._DEFAULT_RAIL_LO`). 병합본에서
   `main --root <병합본>`이 exit 0(면제 아닌 발견 0, PROBE-DUP).
3. **출력 보존(F4)**: 바꾼 probe마다 교체 전(base)과 교체 뒤 실행 출력(stdout, 경로·경과 시간 정규화)이 같다. 다르면 그 교체는 하지 않고 멈춰
   보고한다(결함 후보). base에서 끝까지 돌지 않는 probe는 그 사실과 교체 뒤 같은 지점·같은 예외인지를 보고한다.
4. **B22 (c) 동반 정리**: `A/tests/probes/` 14개 파일 주석의 `H.derived_spec(key, why, **overrides)` 안내 문장(P5에서 지운 함수)을 지우거나 사실에
   맞게 고친다(주석만, 계산 불변).
5. **P2 영구 바이트 대조 폐기**: `A/tests/contracts/test_ts6_probe_relocate.py::test_relocated_probes_match_base_except_path_lines`(probe 전체를 P2 base와
   '경로 줄 말고 바이트 그대로'로 영구 대조)를 지운다 -- P2의 이동 증거는 P2 판정 기록에 남았고, 이 test가 있으면 이후 probe 수정이 모두 막힌다.
   그 함수만 쓰던 헬퍼도 지운다. 사용자 승인 `20260930-p4-relocate-test-retire`(DEC-40, V5).
6. 엔진 소스(`A/*.py`, `workspaces/run_harness.py`)는 바뀌지 않는다. 승격 test(`A/tests/unit/**`)·`A/tests/probe_physical_consistency.py`는 바뀌지 않는다.
   수집 집합은 base에서 사라진 id가 계약 5의 test 하나뿐이다(probes/·tools/는 수집 대상이 아니다).
7. E-LIB·E-INST: 엔진 불변이라 base와 같다(엔진 blob 동일로 확인 가능).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `probe_dup_scan` | `*` | 신규 모듈 `A/tests/tools/probe_dup_scan.py` |
| `probe_dup_scan` | `scan_source` | `def scan_source(source: str, path: str) -> list` |
| `probe_dup_scan` | `main` | `def main(argv: list) -> int` |

## 판정 유형 근거

red-green: 스캐너가 base에 없으므로 계약 1의 test가 base에서 ImportError(red)이고, code-author가 스캐너를 더한 병합본에서 green이다. 도구
추가에 code 커밋·병합이 생기므로 test-only가 아니다(P2 교훈). probe 교체·주석 정리·계약 5 삭제는 test 경로라 test 커밋에 든다.

## oracle 종류와 출처

(a) 구성 입력: 스캐너 규칙마다 합성 소스 조각(발견해야 할 것·발견하면 안 되는 것)과 합성 승인 기록(면제)을 test가 만든다 -- 기대는 이 card
계약 1의 규칙 문장. (c) 동작 보존: probe 출력 교체 전후 동일(기대값 = base 실행 출력). 발견 0은 병합본에서 스캐너를 돌린 결과.

## 거부해야 할 입력

규칙마다 합성 재구현 조각(`.get()` 접근 포함) -- 발견을 내고 `main`이 exit 1. 구문 오류 파일·없는 루트 → exit 2. 면제 target이 다른 파일·다른
규칙을 가리키면 면제되지 않는다(exit 1). `target_kind: decision`이 아닌 승인 기록의 target은 면제가 아니다. 정본 호출만 쓰는 조각·주석·문자열 속
같은 글자·다른 이름(`gate_bias`, `source_file`)·정해진 VGS의 W 식·일반 union-find → 발견 0(오탐 없음).

## library 회로 적용 여부

probe가 읽는 library 회로(파일럿 등)는 출력 보존(계약 3)으로 확인한다. 엔진 불변이라 E-LIB·E-INST는 동일.

## 무동작 판정 입력(무발동 값)

`A/tests/unit/**` 승격 test와 계약 5 밖의 test 전부 -- 판정이 base와 같다. 재구현이 없는 probe는 스캐너 발견 0이고 바뀌지 않는다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(2026-09-29 사용자 승인 "제안대로 승인": 면제 `20260929-p4-scan-exempt`, 계약 5 폐기 `20260930-p4-relocate-test-retire`). 백로그: VGS 기준
gm·gds 공개 조회 API(Phase 4), 정해진 VGS의 W와 `size_transistor` W의 PMOS 차이(결함 후보, P3b의 PMOS gm/ID 비단조와 같은 뿌리 추정).

## 재시도 기록

1차 시도(2026-09-29, test f80bde9·ed9be4b): test-author가 교체 19곳 중 10곳(probe 4개)에서 출력이 달라져 되돌리고(F4), P2 계약 test
`test_relocated_probes_match_base_except_path_lines`가 교체·주석 정리와 충돌해 멈췄다. 원인은 이 card(오케스트레이터)가 원자료 분류를 그대로 믿은
것 -- W 인라인 4곳과 union-find 2곳은 엔진 정본과 다른 개념이었다. 사용자 결정으로 규칙 `w-inline`·`union-find`를 빼고 교체 대상을 다시 가르고,
면제와 계약 5를 더했다. 같은 id로 1부터 다시 한다(R1: 계약 5의 test blob 운반).
