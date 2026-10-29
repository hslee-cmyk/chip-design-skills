# interface card: 20260922-ic3-completeness

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-ic3-completeness.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 현행 계획 N4.1의 IC3 강제 test는 새 엔진 담당 패키지 test 폴더에 새 API로 다시 쓴다(N4.1 머리·N3.11 -- 옛 `contracts/` 폴더는 만들지 않는다). 이 card의 구현은 옛 엔진용이며 IC3 충족 근거가 아니다. 본문의 'library 9회로'는 당시 수치다(지금 library 13회로·held-out 0, O-181). 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `save_instance_json` | `def save_instance_json(path: str, topology_json_path: str, sizing_results: dict, pipeline_result: dict) -> None` |
| `stick_diagram` | `load_topology` | `def load_topology(json_path: str) -> tuple[list[Transistor], dict]` |
| `stick_diagram` | `check_stick_diagram_coverage` | `def check_stick_diagram_coverage(sized_device_names, stick_diagram_devices: dict) -> CoverageVerdict` |
| `stick_diagram` | `run_topology_pipeline` | `def run_topology_pipeline(topology_json_path: str, sizing_overrides: dict, floorplan_hints: dict \| None=None, cell_groups: dict \| None=None) -> dict` |

### `stick_diagram.save_instance_json`

> instance-output JSON 작성 — `pipeline_result`(`run_topology_pipeline()`의 반환값, 또는
> 독립된 물리 cell이 여러 개인 회로라면 §6.9 아래 문단처럼 직접 조립한 동일 스키마의 dict)를
> 손대지 않고 그대로 옮겨 쓴다(§1 표 5번 원칙: 함수 반환값 그대로, 손으로 축약/재구성 금지).
> `sizing_results`는 `{name: {"W":..., "L":..., "ID":..., "gm":..., "gm_id":...}}` 형태를
> 기대한다(sizing_recipe.py의 SizingResult 필드명 그대로).

### `stick_diagram.load_topology`

> topology library JSON(`library/*.topology.json`)을 읽어 (transistors, meta) 반환.

### `stick_diagram.check_stick_diagram_coverage`

> 리포트를 완료로 선언하기 **직전** 반드시 호출한다 — sizing이 끝난 소자 이름 전부가
> 실제로 어떤 stick-diagram 물리 행에든 배치돼 있는지, 단순 집합 차집합으로 확인한다.

### `stick_diagram.run_topology_pipeline`

> `load_topology()` -> `sizing_overrides`로 소자별 layout 필드(n_fingers/finger_w/w/
> stack_id — **필수**, 사이징+finger 배분이 끝난 뒤에만 이 함수를 의미 있게 호출할 수 있다)
> 덮어쓰기 -> `check_finger_width_compatibility()`(§3.5, **세션18 배선** — W가 finger_w의
> 정수배가 아니면 물리적으로 존재할 수 없는 요구라 여기서 즉시 `ValueError`, 아래 euler
> 분석은 이 게이트를 통과해야만 의미가 있다) -> `split_into_stacks()`로 스택(=기본 물리
> 행 후보) 구성 -> §1.6/§1.7이 정한 순서 그대로: 행별 Euler 유효성 -> `check_box_shape()`
> -> `audit_row_split()`(matching-safety, `symmetry.matching_pairs`의 kind 사용) ->
> `pack_floorplan_grouped()` -> `check_stick_diagram_coverage()`.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `INSTANCE_TOP_FIELDS` | `INSTANCE_TOP_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `INSTANCE_SIZING_FIELDS` | `INSTANCE_SIZING_FIELDS: tuple[str, ...]` |
| `stick_diagram` | `CompletenessVerdict` | `class CompletenessVerdict` |
| `stick_diagram` | `check_instance_completeness` | `def check_instance_completeness(instance: Mapping, device_names: Iterable[str]) -> CompletenessVerdict` |
| `stick_diagram` | `NameCollisionVerdict` | `class NameCollisionVerdict` |
| `stick_diagram` | `check_topology_name_uniqueness` | `def check_topology_name_uniqueness(device_names: Sequence[str], passive_names: Sequence[str]) -> NameCollisionVerdict` |

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-ic3-completeness.interface.md`.
