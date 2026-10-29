# interface card: 20260922-ic5-gate-docstrings

> **[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님.** 판정 기록 `.ai/verification/20260922-ic5-gate-docstrings.json`(FAIL 0)이 있고 이 card의 커밋은 master에 병합됐다. 옛 계획 Phase 1 test 분리 card이고 Phase 1은 폐기됐다(계획 N6.1 '옛 Phase 처리' 1행; N3.11 'TS0~TS6 폐기'). 본문의 spec card·interface card·auditor 판정(V1~V10)·DEC-40 승인·R1 절차는 DEC-86으로 폐기했다(계획 N3.12·N4.2, DEC-40 행) -- 현행 완료 조건은 계획 N6.3이다. 본문의 `A`(`skills/analog-gmid-design/assets`) 아래 옛 엔진·test는 `skills/analog-gmid-design/legacy/`로 옮겨졌고(`60727b06`) 새 test 체계(`gmid_engine/tests/`)에서 돌지 않는다. card LT-1(DEC-99)이 `legacy/`를 지운 뒤에는 tag `legacy-final`에만 남는다. 현행 계획 N4.1의 IC5 강제 test는 새 엔진 담당 패키지 test 폴더에 새 API로 다시 쓴다(N4.1 머리·N3.11 -- 옛 `contracts/` 폴더는 만들지 않는다). 이 card의 구현은 옛 엔진용이며 IC5 충족 근거가 아니다. 본문은 기록이며 덧대지 않는다(O-169).

생성: `tools/gates/interface_card.py`(05-role-separation §11.1). 본문 코드는 넣지 않는다(DEC-38).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `audit_current_forced` | `audit_topology` | `def audit_topology(topology_path: str) -> dict` |
| `sizing_recipe` | `check_quasi_static` | `def check_quasi_static(fT: float, gm: float, Cgg: float, margin: float=0.1) -> QuasiStaticVerdict` |
| `sizing_recipe` | `audit_l_sharing_consistency` | `def audit_l_sharing_consistency(by_name: dict, meta: dict, sized: dict, matching_pairs=(), tol: float=1e-12, classes: dict \| None=None) -> list` |
| `sizing_recipe` | `audit_vsb_consistency` | `def audit_vsb_consistency(by_name: dict, sized: dict, vdd: float, tol: float=1e-06, **kw) -> list` |
| `sizing_recipe` | `validate_no_legacy_vs_key` | `def validate_no_legacy_vs_key(device_roles: dict) -> None` |
| `sizing_recipe` | `validate_metric_units` | `def validate_metric_units(metrics_specs: dict) -> None` |
| `sizing_recipe` | `validate_theta_declaration_order` | `def validate_theta_declaration_order(meta: dict) -> list` |
| `sizing_recipe` | `require_declared_spec_source` | `def require_declared_spec_source(topology_path: str, spec: dict) -> None` |
| `stick_diagram` | `check_mirror_symmetry` | `def check_mirror_symmetry(sequence: list, pair_map: dict) -> MirrorSymmetryVerdict` |
| `stick_diagram` | `check_symmetry_dispositions` | `def check_symmetry_dispositions(transistors: list, matching_pairs: list, dispositions: dict \| None=None) -> SymmetryDispositionsVerdict` |
| `stick_diagram` | `check_multi_leaf_hub_parity` | `def check_multi_leaf_hub_parity(n_fingers_by_leaf: dict) -> MultiLeafHubParityVerdict` |
| `stick_diagram` | `audit_vertical_stack_id_vs_kcl` | `def audit_vertical_stack_id_vs_kcl(transistors: list, matching_pairs: list, device_roles: dict) -> dict` |
| `stick_diagram` | `audit_theta_root_direction` | `def audit_theta_root_direction(transistors: list, sizing_roles: dict \| None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=()) -> list` |
| `stick_diagram` | `require_device_roles_reviewed` | `def require_device_roles_reviewed(topology_json_path: str, meta: dict) -> None` |
| `stick_diagram` | `audit_vertical_stack_id_euler_feasibility` | `def audit_vertical_stack_id_euler_feasibility(transistors: list, device_roles: dict, matching_pairs: list) -> dict` |
| `stick_diagram` | `check_finger_width_compatibility` | `def check_finger_width_compatibility(transistors: list[Transistor], tol: float=1e-09) -> FingerWidthVerdict` |
| `stick_diagram` | `check_euler_condition` | `def check_euler_condition(g: StackGraph) -> EulerVerdict` |
| `stick_diagram` | `check_box_shape` | `def check_box_shape(rows: dict, row_width_tol: float=1.5, max_elongation: float \| None=None, orientation: str='either') -> BoxShapeVerdict` |
| `stick_diagram` | `check_walk_sequence` | `def check_walk_sequence(transistor_sequence: list, transistors: list) -> WalkVerdict` |
| `stick_diagram` | `check_stick_diagram_coverage` | `def check_stick_diagram_coverage(sized_device_names, stick_diagram_devices: dict) -> CoverageVerdict` |
| `stick_diagram` | `audit_row_split` | `def audit_row_split(rows: dict, matching_pairs: list \| None=None, pair_sensitivity: dict \| None=None, row_width_tol: float=1.5, area_budget: str \| None=None) -> AuditResult` |

### `audit_current_forced.audit_topology`

> 한 topology.json을 감사해 {"forward_ok": [...], "forward_flagged": [...],
> "reverse_violations": [...], "no_theta": bool} 반환. names가 3개 이상인 그룹은
> 모든 쌍별 조합으로 펼쳐서 검사한다(matching_pairs의 N-소자 그룹 관례, audit_row_split()
> 과 동일 계약).

### `sizing_recipe.check_quasi_static`

> f_nqs = gm/(2*pi*Cgg); fT <= margin * f_nqs 이어야 준정적 가정이 성립.

### `sizing_recipe.audit_l_sharing_consistency`

> L 동치류 안에서 **L이 갈린** 곳을 찾는다(층0 게이트, 2026-09-10).

### `sizing_recipe.audit_vsb_consistency`

> 선언된 `vsb`가 복원된 노드전압과 맞는지 소자 전수 대조해 어긋난 것만 돌려준다.

### `sizing_recipe.validate_no_legacy_vs_key`

> 옛 이름 `vs`가 `device_roles`에 남아 있으면 즉시 `ValueError`(2026-09-08, B9 개명).

### `sizing_recipe.validate_metric_units`

> metric 선언의 `unit`이 (1) 존재하고 (2) 정규 단위에서 환산 가능하며 (3) 이름 접미사가
> 단위를 말한다면 그것과도 같은지 검사한다. 하나라도 어긋나면 즉시 `ValueError` -- 단위
> 불일치는 제약을 **조용히 무력화**하므로 경고로 넘기지 않는다(A12).

### `sizing_recipe.validate_theta_declaration_order`

> `topology.json`의 `sizing_roles.theta` 배열이 "선언 순서=실행 순서"라는 이 엔진의
> 암묵적 계약(`optimize_full_circuit_budget()`의 `for theta in thetas:` 루프가 배열
> 순서 그대로 `apply_theta_feed()`를 부름)을 실제로 만족하는지 **읽기 전용**으로
> 검사한다(topology.json을 고치지 않음, 2026-08-13 세션31 신설).

### `sizing_recipe.require_declared_spec_source`

> 라이브러리 회로를 사이징할 때 spec의 **출처 선언**을 강제한다(2026-09-10).

### `stick_diagram.check_mirror_symmetry`

> `sequence`(finger 순서)가 `pair_map` 기준으로 중앙 수직축에 대해 좌우 대칭인지 검증한다
> (`build_mirror_symmetric_pattern()`의 역검증). 길이가 홀수면 정중앙 원소 하나는 비교에서
> 제외한다(축 위에 단독으로 걸친 소자이므로 대응 상대가 없다).

### `stick_diagram.check_symmetry_dispositions`

> `find_matching_candidates()`/`find_hub_merge_candidates()`는 **후보**만 낸다 — "이
> 회로 기능상 진짜 matching/병합인가"는 항상 판단(설계자/AI)이 남아 있는데, 그 판단이
> 조용히 누락(후보를 발견하고도 topology JSON `symmetry.matching_pairs`에 채택도, 명시적
> 기각도 안 하고 그냥 빼먹는 것)되는 걸 이 함수가 구조적으로 차단한다. `run_full_circuit_
> audit()`의 3번 체크("every matching/hub-merge candidate has a recorded disposition")와
> 정확히 같은 원리를 topology-authoring 단계(사이징 이전, `devices`/`expected_counts` 같은
> 무거운 인자 없이)에 맞게 경량화한 것이다.

### `stick_diagram.check_multi_leaf_hub_parity`

> hub 하나에 leaf가 N개(N≥2) 달린 구조(각 leaf = 서로 다른 소자 하나, 그 소자의
> finger 개수가 `n_fingers_by_leaf`)가 **finger 개수를 그대로 실현했을 때** 한붓그리기
> 가능한지를 그래프를 만들지 않고 공식으로 빠르게 판정한다(설계 공간 탐색 시 여러 k
> 후보를 빠르게 스크리닝하는 용도 — 최종 채택 전에는 반드시 `build_graph()`+
> `check_euler_condition()`으로 재확인할 것, 이 함수는 그 결과와 항상 일치함을 self-test로
> 직접 검증했다).

### `stick_diagram.audit_vertical_stack_id_vs_kcl`

> L2 축A(`kcl_series_union()`)와 declared `vertical_stack_id`(topology.json
> `device_roles`)가 서로 다른 질문에 답한다는 걸 2026-08-10 세션 대화에서 실측으로
> 확인한 뒤 만든 감사(audit) 도구 -- **탐색 입력이 아니라 사후 대조표**로 쓴다(대화
> 결론: `vertical_stack_id`로 KCL 탐색 범위를 좁히면 오히려 `M11b`/`M12`처럼 진짜
> 2단자 직렬 관계를 vsid 경계가 가로막아 놓친다, 실측 확인됨 -- 그래서 탐색기가
> 아니라 검증 대상으로 쓴다).

### `stick_diagram.audit_theta_root_direction`

> `sizing_roles.theta`의 `"A"`/`"A_signed"` feed가 `root`(이 theta가 전류를 **정의**하는
> 소자)의 값을, `analog-grammar`의 `idioms.m_cascode()`가 이미 찾아둔 캐스코드 관계에서
> **`root`가 lo(전류생성원 쪽)인데 정작 그 위에 얹힌 up(캐스코드)을 reference/terms로
> 참조**하는 경우를 찾는다 -- **방향이 거꾸로일 가능성이 높다는 신호**(캐스코드는 전류를
> 정의하지 않고 그 아래 소자가 이미 정한 전류를 그대로 물려받을 뿐이므로, lo가 자기 위의
> up을 참조해 자기 값을 정하는 건 인과관계가 뒤바뀐 것).

### `stick_diagram.require_device_roles_reviewed`

> `optimize_full_circuit_budget()`이 실제 사이징(`select_L_by_role()`/`search_gm_id_
> for_role()`/matching_pairs L 전파)을 돌리기 **전에** 호출하는 게이트(2026-08-14,
> 사용자 지시 -- "구조적으로 명확한 기능과 필요한 기능을 구분해서 사용자가 review해준
> 적이 없는 부분은 error로 띄우고 일단 review를 받고 review받았다는 표시를 해서
> optimize함수가 실행되도록"). `device_roles`(gm_id_role/L_role)와 `matching_pairs`
> 둘 다 검사한다(이름은 `device_roles`만 가리키지만 하위호환을 위해 유지, 실제로는
> `find_unreviewed_matching_pairs()`도 함께 확인).

### `stick_diagram.audit_vertical_stack_id_euler_feasibility`

> 2026-08-10 세션26 후속(2) K-3에서 발견된 `cmfb_tail`류 문제를 정면으로 잡는
> audit -- `audit_vertical_stack_id_vs_kcl()`(전기적 정합성)과는 다른 질문에 답한다:
> **declared `vertical_stack_id` 그룹 하나가 그 자체로 오일러 실현 가능한가**.

### `stick_diagram.check_finger_width_compatibility`

> W가 그 stack의 finger_w로 정확히 나누어떨어지는지 확인한다.

### `stick_diagram.check_euler_condition`

> PDF/pptx가 명시한 3가지 오일러 조건을 그대로 판정한다:
> 0개 홀수차수 → circuit(닫힌 한붓그리기), 2개 → path(열린 한붓그리기), 4개 이상 → impossible.
> 연결성도 함께 확인한다(차수 조건을 만족해도 그래프가 끊겨 있으면 한 줄 diffusion으로 불가능).

### `stick_diagram.check_box_shape`

> §8 cell shape 게이트 — **SPICE 검증으로 넘어가기 전에 반드시 통과해야 하는 체크포인트**.

### `stick_diagram.check_walk_sequence`

> 제안된(또는 손으로 재배열한) `transistor_sequence`가 실제로 하나의 연속된 diffusion
> strip(한붓그리기)으로 이어지는지 **독립적으로** 검증한다 — `build_stick_diagram()`/
> `hierholzer()`가 순서를 "만드는" 것과 반대로, 이미 만들어졌거나 사람이 제안한 순서를
> "검산"하는 함수다.

### `stick_diagram.check_stick_diagram_coverage`

> 리포트를 완료로 선언하기 **직전** 반드시 호출한다 — sizing이 끝난 소자 이름 전부가
> 실제로 어떤 stick-diagram 물리 행에든 배치돼 있는지, 단순 집합 차집합으로 확인한다.

### `stick_diagram.audit_row_split`

> box-shape를 위해 한 functional group을 여러 물리 행으로 재구성했을 때 **반드시 이
> 함수 하나만** 호출한다 — 그때그때 손으로 `build_stick_diagram()`/`check_box_shape()`/
> interdigitation을 따로따로 확인하다가 순서를 빼먹는 실수(실제 사고, 위 §6.65 docstring)를
> 막기 위해, 고정된 순서로 전부 실행하고 전부 보고한다. 하나라도 실패하면 `ok=False`이고
> `checks`에 어떤 항목이 왜 실패했는지 전부 남는다 — 조용히 건너뛰는 항목이 없다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20260922-ic5-gate-docstrings.interface.md`.
