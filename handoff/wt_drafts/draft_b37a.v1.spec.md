---
id: 20260930-b37a-ports-roles
phase: 4
evidence_type: red-green
gate_change: no
approval: 20260930-b37a-ports-roles
---
## 의도

백로그 B37의 앞쪽 절반(B37a). 준비 자료 `_drafts/prep_b37_ports.md`, Phase 4 design 초안 #47을 이 card로 좁혔다. 뒤쪽 절반 B37b(analog-grammar 라이브러리 경로의 `HINT_*` 제거)는 B36 뒤 별도 card다.

**문제.** topology `ports`는 사용자가 확정한 선언이다(DEC-35, 파일별 `_comment`의 '사용자 확정'). 그런데 `stick_diagram.load_topology`는 이 선언을 analog-grammar에 넘기지 않는다. 그래서 `netclass.classify_nets`가 넷 이름 정규식(`HINT_INPUT` 등, NC 39~43)으로 입력·출력을 추정한다.
* library 9회로의 입력 포트 16개 가운데 정규식이 INPUT으로 맞힌 것은 4개(`Vip`·`Vim`·`Vinp`·pushpull `vin`)다. 11개(`vin_p`/`vin_n`/`Vin_p`/`Vin_n`/`Vinn`)는 BIAS, common_gate `vin`은 INTERNAL이 된다(준비 자료 §2.1).
* 그 결과 자동 채움이 넷 이름에 따라 갈린다. 포트 넷과 `HINT_INPUT`에 걸리는 넷을 중립 이름으로 바꾸면 base에서 3/9 회로(current_reuse·ngcc·pushpull)의 `load_topology` meta가 바뀐다('작성 전 실측' 1(b)).
* 이것은 DEC-62(새 토폴로지는 데이터만으로) 위반이다. 선언이 있는데 이름이 동작을 정한다.

선언을 가진 쪽에서 문법으로 가는 운영 진입점은 셋이고, 셋 다 선언을 넘기지 않는다.

| # | 진입점 | 지금 |
|---|---|---|
| E1 | SD `load_topology` → `propose_device_roles_gap_fill`(SD 8668~8671) | `inputs`/`outputs` 없음. `base_inputs`를 쓰는 4함수(`_propose_vertical_stack_ids`·`_propose_gm_id_roles`·`_propose_L_roles`·`_propose_headroom_roles`)가 정규식 분류를 본다 |
| E2 | SD `load_topology` → `propose_vertical_stack_id_gap_fill`(SD 8643~8644) | `inputs` 등이 모두 비어 3292의 `if inputs or …`가 거짓. 차동 다리 간선 기능이 운영에서 꺼져 있다(docstring 3282 "조용히 건너뛴다") |
| E3 | SR `_build_theta_evaluator`(8060~8062) → `resolve_stack_layout` 경로 3(SR 6572) | `refine_differential_and_mirror_relations(transistors)`. 선언 vsid가 없는 회로에서만 탄다. docstring 6537~6543이 "ports 파싱은 필요해지면 추가"라고 적어 두었다 |

`ports`의 다른 소비자: SR `input_referred_offset_pairs`(4481)가 `_load_full_topology_cached`(4806)에 실어 둔 raw `ports`(4833)를 `p.get("direction") == "input"`(4511~4519)으로 읽는다.
엔진에서 `ports`의 `direction`을 읽는 곳은 여기 하나다. `direction`은 MG2(DEC-69, 6a 착수 전)가 지우는 키다(N3.16 786행: `ports{<넷>: {role}}`, `direction`은 role에서 유도).

**원칙 기본안.**
* 선언이 정규식을 이긴다. 준비 자료 §2의 불일치는 '어느 쪽이 맞나'가 아니라 이름 표기(`_p`, `Vinn`) 때문에 생긴 오분류다.
* 조용한 폴백 금지(계획 §3.2 P1). `ports`가 없으면 정규식으로 돌아가지 않고 거부한다.
* 만들면 배선. 접근자 하나를 만들어 운영 진입점 E1·E2·E3와 `input_referred_offset_pairs`를 같은 card에서 전부 대체한다. E1만 고치면 이름 의존이 E2·E3로 남는다(준비 자료 §4.3).
* role만 읽는다. `direction`을 읽게 만들면 MG2에서 다시 고쳐야 한다. 이 card 뒤 엔진의 `direction` 소비자는 0이 된다. MG2의 ports 몫은 키 삭제와 옛 키 거부만 남는다.
* 재계산 금지(NFR-2). 선언은 `load_topology`에서 한 번 읽어 `meta["ports"]`에 싣는다. SR은 raw `ports`를 다시 해석하지 않는다. 새 캐시는 만들지 않는다.
* B26-1(`rail_declaration`·`RailDeclaration`·`meta["rails"]`·`resolve_stack_layout(…, *, rails)`)과 같은 모양을 쓴다.

**범위(코드).** A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 gate `master` `7535799` 기준이다.
착수 시점(B34 → B26-1 → Phase 3 → CC-4a 병합 뒤)에는 줄과 모듈이 바뀐다. 오케스트레이터가 card 커밋 전에 다시 재고, '신규 시그니처'의 모듈을 `rail_declaration`이 있는 모듈로 바꾼다(Phase 3 v4 A-3: `load_topology`는 MOD3, 접근자는 `ports`를 읽는 MOD2 쪽 -- 준비 자료 §4.1).
1. **접근자 신설**(SD, B26-1 `rail_declaration` 옆): `port_declaration(topology: dict) -> PortDeclaration`. `PortDeclaration`은 frozen dataclass이고 필드는 `inputs`·`outputs` 둘이다. role → 입출력 대응은 닫힌 표 하나(비공개 상수, role 6개)로 정한다.
2. **`load_topology`**: 진입 파일 dict로 접근자를 한 번 부른다. 연결 파일 규칙을 적용하고, 결과를 `meta["ports"]`에 싣는다. 그 값을 E2(`propose_vertical_stack_id_gap_fill(…, inputs=, outputs=)`)와 E1(`propose_device_roles_gap_fill(…, inputs=, outputs=)`)에 넘긴다.
   두 피호출 함수는 이미 그 키워드를 받는다. 시그니처와 본문은 바꾸지 않고 docstring만 고친다.
3. **E3**: SR `resolve_stack_layout`에 기본값 없는 키워드 전용 `ports: PortDeclaration`을 더한다(B26-1 뒤 모양 `…, stack_groups_override=None, *, rails, ports`). 경로 3이 `refine_differential_and_mirror_relations(transistors, ports.inputs, ports.outputs)`를 부른다.
   `_build_theta_evaluator`의 호출(8060~8062)이 `ports=meta["ports"]`를 넘긴다.
4. **`input_referred_offset_pairs`**: 입력 넷 집합을 캐시 엔트리의 `meta["ports"].inputs`에서 읽는다. raw `ports` 읽기(4511~4519)와 그 함수 자체의 `ports` 없음 `ValueError`(4512~4517)는 지운다. `ports`가 없으면 그보다 먼저 `load_topology`가 거부한다.
   `_load_full_topology_cached`의 raw `"ports"` 엔트리(4833)는 소비자가 0이 되므로 지운다. 옆 주석 4831~4832도 함께 지운다.
5. **docstring·주석**(AST 해시 불변): SD `load_topology` meta 목록(`"ports"` 추가), SD 3276~3283(`propose_vertical_stack_id_gap_fill` -- 운영에서는 `load_topology`가 `ports` 선언을 넘긴다), SD 3855~3857(`propose_device_roles_gap_fill` -- 같은 취지).
   그리고 SR 4481~4505(`input_referred_offset_pairs` -- 조건 2를 `meta["ports"].inputs`로, `ports` 없음 거부는 `load_topology`), SR 6537~6543(`resolve_stack_layout` -- "ports 파싱은 필요해지면" 삭제).
6. **레지스트리**(code-author, 같은 커밋): 접근자 행을 새로 만든다(개념 '포트 선언(입출력)', 정본 = 이 접근자). 311행 `input_referred_offset_pairs` 비고("ports input net" → `meta["ports"].inputs`)와 338행 `resolve_stack_layout`(키워드 `ports`)을 고친다.

**범위 밖.**
* **B37b**: analog-grammar `classify_nets`의 이름 정규식 제거. 여기에는 비포트 SIGNAL 넷에 대한 `HINT_OUT`(current_reuse `Vom1`/`Vop1`, two_stage `O1`, two_stage_ota_sf `O1`/`OUT`)과 `HINT_INPUT`에 걸리지 않는 게이트 전용 비포트 넷의 1c 힌트가 남는다. library 결과에는 영향이 없다(준비 자료 §3.2 p3·p4 = p1).
* **B38**: 바이어스 넷 추정(`ports`에 바이어스 role이 없다).
* **MG2**: topology JSON 9개에서 `direction` 키 삭제, 옛 키 거부 게이트.
* `_TEMPLATE.topology.json`에 `ports` 필드가 없다. library 데이터라 승인 기록 조건이고 오케스트레이터 몫이다. 백로그로 둔다(B26-1 검토 M2와 같은 자리).
* analog-grammar 파일(`skills/analog-grammar/**`)은 고치지 않는다. 쓰기 경로표에 주체가 없다(B36).
* 3회로의 자동 채움 소실(아래 '결정 필요 항목' 1)을 메우는 규칙 확장이나 선언 보강은 6a(DEC-35 ports·역할 제안표)로 넘긴다.

이 card는 회로·넷·소자 이름을 읽지 않는다. 판정은 role 어휘(선언 표)와 `_` 접두 주석 규약만 읽는다.

## 관찰 가능한 계약

모듈 이름: 아래 `M`은 `rail_declaration`이 있는 모듈이다(7535799에서는 `stick_diagram`. Phase 3 병합 뒤 이름은 오케스트레이터가 card 커밋 때 적는다). `load_topology`와 `resolve_stack_layout`·`input_referred_offset_pairs`는 card 커밋 시점의 모듈 이름으로 interface card에 실린다.
거부 예외 `SchemaRejectedError`는 CC-4a가 만든 클래스다(N3.14. `Exception` 직접 하위이고 `ValueError`가 아니다). interface card에 모듈 경로를 싣는다.

**test 모양(V3 인벤토리 조건).** `port_declaration`·`load_topology`·`resolve_stack_layout`·`input_referred_offset_pairs`는 test 함수 **본문**에서 `<모듈>.<이름>(…)` 형태로 직접 부른다.
`@pytest.mark.parametrize`의 이름 문자열이나 모듈 상수 이름 목록 + `getattr`로만 부르면 V3 정적 인벤토리에서 빠진다(실측 -- '작성 전 실측' 1(e)). 회로·이름 변형의 반복은 parametrize로 해도 된다.

**red 모양(권고).** base에는 `port_declaration`·`meta["ports"]`·`resolve_stack_layout`의 `ports` 키워드가 없다. 그래서 base에서 생기는 예외가 `AttributeError`(신규 심볼, 허용)·`KeyError`·`TypeError`(허용 밖)로 갈린다.
진입점 호출을 `try` / `except Exception as e: pytest.fail(…)` 모양으로 감싸거나, 호출 전에 `assert "ports" in meta`를 두면 base red가 `Failed`·`AssertionError`로 남는다(00-common §8.1 허용 예외 타입).

1. **접근자(role → 입출력).** `M.port_declaration(topology)`는 topology JSON 한 파일을 읽은 dict를 받아 `M.PortDeclaration(inputs=…, outputs=…)`를 돌려준다.
   * `inputs`는 role이 `single_ended_input`·`differential_input_p`·`differential_input_n`인 넷 이름의 오름차순 tuple이다. `outputs`는 role이 `single_ended_output`·`differential_output_p`·`differential_output_n`인 넷 이름의 오름차순 tuple이다.
   * `ports`의 키 가운데 `_`로 시작하는 것(주석 규약, 예: `_comment`)은 건너뛴다.
   * `direction` 키는 결과에 영향을 주지 않는다. 있으면 role과 같은 쪽(`input`/`output`)이어야 한다(계약 6). 없어도 결과가 같다. 이로써 MG2에서 `direction`을 지워도 결과가 같다.
   * `PortDeclaration`은 frozen dataclass라 `==`가 필드 비교다. 판정은 `(pd.inputs, pd.outputs)` 튜플 비교로 써도 된다.
   * library 9회로 각각에서 기대값은 test가 topology JSON의 `ports`와 위 role 표로 만든다(oracle (a)). 예: `folded_cascode` → `inputs == ("vin_n", "vin_p")`, `outputs == ("out",)`.
2. **`load_topology`가 선언을 싣는다.** `t, meta = load_topology(p)`이면 `meta["ports"] == M.port_declaration(<p의 JSON dict>)`다(library 9 + 합성).
   * `linked_topology_files`의 연결 파일이 `ports`를 선언하면 그 선언도 같은 검사(계약 6)를 거친다. 그 결과가 진입 파일의 결과와 다르면 거부한다(어느 쪽을 고를지 추측하지 않는다).
   * 연결 파일에 `ports`가 없으면 진입 파일 선언을 쓴다.
   * `meta`의 다른 키와 `transistors`의 동작 보존은 계약 9다.
3. **E1 -- 자동 채움은 넷 이름과 무관(이름 바꾸기 불변, 대표 관찰).**
   * library 9회로 각각에서 바꿀 넷 집합 = `ports`의 포트 넷(`_` 키 제외) ∪ {게이트·드레인·소스 단자로 나오는 넷 중 레일(`supply_nets`)이 아니고 analog-grammar `netclass.HINT_INPUT.match`에 걸리는 넷}.
   * 그 넷을 회로 안에서 유일한 중립 이름(예: `ZQ<i>Q`)으로 바꾼 topology를 tmp에 쓴다. 바꾸는 곳은 JSON 전체에서 그 넷 이름과 **정확히 같은** 문자열 값과 키다.
   * 원본과 바꾼 topology의 `load_topology` meta를 비교한다. 바꾼 쪽은 meta 문자열 안의 중립 토큰을 원래 이름으로 되돌린다(부분 문자열 치환 -- 파생 문자열 `…_fold` 포함). `"ports"` 키는 비교에서 빼거나 집합으로 비교한다(정렬 순서가 이름에 따라 바뀐다).
   * 정규화 뒤 `==`이면 통과다. 정규화: `set`/`frozenset` → 정렬 리스트, dataclass → 필드 dict, 나머지 dict·list는 재귀.
   * base: current_reuse(8소자)·ngcc(5소자)·pushpull(4소자)에서 `device_roles`·`_device_roles_autofilled`의 `headroom_role`이 달라져 FAIL. 병합 상당은 9/9 같다('작성 전 실측' 1(b)).
   * 합성 판(라이브러리와 독립): 아래 합성 2단 OTA에서 입력 이름 쌍 `("sig_a","sig_b")`, `("Vip","Vim")`, `("vin_p","vin_n")`, `("Vinp","Vinn")` 네 변형의 meta가 이름을 맞춘 뒤 모두 같다. base에서는 FAIL이다(`sig_a`·`vin_p` 판은 입력쌍 M1·M2가, `Vinp` 판은 M2만 `headroom_role: cascode` 제안을 받고, `Vip` 판은 받지 않는다).
   * **경계(이 card의 불변 범위)**: 포트 넷과 `HINT_INPUT`에 걸리는 넷까지다. 비포트 SIGNAL 넷의 `HINT_OUT`과 `HINT_INPUT` 밖 게이트 전용 비포트 넷의 1c 힌트는 B37b가 닫는다. test는 그 넷을 바꾸는 변형을 이 card의 계약으로 쓰지 않는다.
     (참고 실측: library에서는 `HINT_*` 전부에 걸리는 넷까지 바꿔도 병합 상당이 9/9 불변이다. 합성 topology에서 비포트 내부 넷 `vo1`이 OUTPUT으로 분류되는 것은 B37b의 red가 된다 -- 준비 자료 §4.2 C1의 예, 이번에 재지 않았다.)
4. **E2 -- 차동 다리 간선이 운영에서 동작.** 합성 텔레스코픽 topology(아래 `tele`)에 `device_roles = {"M1": {"vertical_stack_id": "S1"}}`만 선언하면 `meta["_vertical_stack_id_autofilled"]`가 `{"M2": "S1", "M3": "S1", "M4": "S1", "M5": "S1", "M6": "S1"}`이다.
   * 입력 이름 `sig_a`/`sig_b`와 `Vip`/`Vim`에서 같다.
   * 기대값의 근거(oracle (a)): 차동쌍 두 다리는 같은 헤드룸 컬럼에 있다(`propose_vertical_stack_id_gap_fill` docstring의 규칙). 그래서 M1·M2를 묶는다. 그리고 각 다리의 2단자 직렬 사슬(M1–M3–M5: 넷 `x`·`o1`, M2–M4–M6: 넷 `y`·`o2` -- D/S 단자가 정확히 둘인 넷)을 KCL 간선으로 묶는다.
   * base는 `{"M3": "S1", "M5": "S1"}`(차동 간선 없음)이라 FAIL이다.
5. **E3 -- 레이아웃 1차 그룹이 넷 이름과 무관.** 합성 `tele` topology(선언 vsid 없음)의 네 입력 이름 변형(계약 3과 같은 네 쌍)마다 `t, meta = load_topology(p)`, `g = resolve_stack_layout(t, [], meta["device_roles"], ports=meta["ports"])`(B26-1 뒤에는 `rails=meta["rails"]`도)를 부른다. 그 결과 `sorted(sorted(v) for v in g.values())`가 네 변형에서 모두 같다(oracle (b) 변환 불변).
   * base에서는 `sig_a`·`vin_p`·`Vinp` 판이 `[M0, M1, M2]`를 한 그룹으로 묶고 `Vip` 판은 묶지 않는다. 병합 상당은 넷 모두 같다.
   * `ports`는 기본값이 없다. 빠뜨리면 `TypeError`다.
   * 운영 배선: `_build_theta_evaluator`가 `resolve_stack_layout`에 넘기는 `ports`가 그 topology `load_topology` meta의 `"ports"`다(auditor 호출 그래프 확인 + 계약 9의 library 그룹 차이표).
6. **거부(조용한 폴백 없음).** 아래 입력은 `load_topology`가 `SchemaRejectedError`로 거부한다. 메시지에 `ports`와 `DEC-62`가 있다. 연결 파일 항목을 뺀 나머지는 `port_declaration(<그 dict>)`를 직접 불러도 같은 예외다.
   * 최상위 `ports` 키 없음
   * `ports: null`, `ports`가 dict가 아님(예: list)
   * `ports: {}`, `_comment`만 있음, 입력 role 넷이 하나도 없음(출력만)
   * 포트 항목이 dict가 아님(예: `"sig_a": "input"`), `role` 없음, role이 6개 어휘 밖(예: `"differential_input"`)
   * `direction`이 role과 모순(예: `differential_input_p` + `"direction": "output"`, `single_ended_output` + `"direction": "input"`)
   * 연결 파일의 `ports`가 위 규칙을 어기거나 진입 파일 결과와 다름
   * 출력 role 넷이 0개인 것은 거부하지 않는다(E1·E2가 빈 출력으로 동작하는 지금 모양 그대로다).
   * **판정기 자기 점검**: 누락 시 정규식 분류로 계속 가는 합성 구현(예: test 안의 가짜 로더가 `ports` 없을 때 `PortDeclaration((), ())`를 돌려준다)과 거부 메시지에 `ports`가 없는 구현을 같은 판정 함수에 넣으면 실패해야 한다(`test_d_delete_telescopic`의 거부 점검과 같은 형태).
7. **`direction` 소비자 교체.** 합성 2단 OTA에 `symmetry.matching_pairs = [{"names": ["M1","M2"], "matching_sensitivity": "offset", "current_forced": true}]`를 둔다. 이때 `input_referred_offset_pairs(p)`가 `direction` 키가 있든 없든 `[["M1","M2"]]`다.
   * base는 `direction`이 없으면 입력 집합이 비어 `[]`를 조용히 돌려준다. 그래서 FAIL이다.
   * library 9회로의 반환은 base와 같다: current_reuse `[["M1a","M1b"],["M4a","M4b"]]`, folded `[["M1","M2"]]`, nmcnr `[["M102","M103"]]`, two_stage_ota `[["M1","M2"]]`, 나머지 5회로 `[]`.
8. **재계산 없음.** 새 tmp 경로의 topology에서 접근자 호출 수를 센다. `load_topology` 1회 → 1이다. 이어 `input_referred_offset_pairs` 첫 호출 → 2다(`_load_full_topology_cached`가 캐시를 못 찾아 `load_topology`를 한 번 더 부른다 -- 기존 구조).
   그 뒤 같은 경로로 `input_referred_offset_pairs` N회·`_topology_meta_cached` N회 → 2 그대로다.
   * 계수 래퍼는 `port_declaration`을 정의한 모듈과 `load_topology`가 그 이름을 찾는 모듈의 이름을 **둘 다** 바꾼다(Phase 3 뒤 두 모듈이 다르면 `from … import` 별칭이 생긴다).
   * SR(사이징 모듈)은 `port_declaration`을 import하지 않는다. 선언은 `meta["ports"]`로만 받는다.
9. **동작 보존(auditor, base 대조).**
   * E-LIB 9/9: `transistors`가 같다. `meta`는 새 키 `"ports"`를 빼고 아래 **기대 차이표의 필드만** 다르다. 표에 없는 차이가 나오면 FAIL이다.
   * SPECS 4회로 θ 평가(`_library_sized_contexts._evaluate_once` 상당)의 metric `float.hex`, `ctx.sized` 해시, 거부 문구가 base와 같다.
   * `run_full_circuit_audit_from_topology` 9/9가 같다(결과 2, 같은 `ValueError` 7. 메시지 안의 경로 문자열은 빼고 비교).
   * `input_referred_offset_pairs` 9/9가 같다. E-INST가 같다.
   * 비교는 `PYTHONHASHSEED`를 고정하거나 계약 3의 정규화 뒤 `==`로 한다.

   기대 차이표(E-LIB, 사람이 선언한 값은 바뀌지 않는다. 바뀌는 것은 자동 채움·review 목록뿐이다):

   | 회로 | 바뀌는 키 | 내용 |
   |---|---|---|
   | `ngcc_3stage_ff` | `device_roles`, `_device_roles_autofilled` | `headroom_role` 4개 사라짐(M1 `cascode`, M4·M6B·M7 `mirror`) |
   | `sf_pushpull_output_opamp` | 〃 | `headroom_role` 20개 사라짐(M1·M2 `cascode`, M5~M22 18개 `cascode`/`mirror`). M5~M22는 항목 자체가 사라진다 |
   | `two_stage_ota_sf` | 〃 | `headroom_role` 5개 사라짐(M1·M2 `cascode`, M4·M6 `mirror`, M8 `cascode`) |
   | `nmcnr_amplifier` | `_device_roles_gap_fill_review_needed` | 12 → 10(M201·M301의 'compensation.stage_devices 소속 gm_id_role' 안내 2건) |
   | `two_stage_ota` | 〃 | 9 → 7(M4 `headroom_role` 충돌 `cascode`/`mirror`, M6 안내) |

   기대 차이표(E3 경로, `resolve_stack_layout` 경로 3 -- 선언 vsid가 없는 5회로 중):

   | 회로 | base | 병합 상당 |
   |---|---|---|
   | `ngcc_3stage_ff` | `[M0, M1, M2]` 한 그룹 | `[M0]`, `[M1, M2]` |
   | `sf_pushpull_output_opamp` | `[M17, M18]`, `[M19, M20]` | 네 개로 분리 |
   | `two_stage_ota_sf` | `[M8, M9]` | `[M8]`, `[M9]` |
   | `common_gate_amplifier`, `pushpull_follower_buffer` | 같음 | 같음 |

**합성 topology(계약 3·4·5·6·7 공통).** 최상위 키는 `topology_name`, `schema_version`, `netlist`, `supply_nets: ["vdd","gnd"]`, `symmetry: {"matching_pairs": [], "dispositions": []}`, `ports`다(B26-1 뒤에는 `supply_nets`가 필수다).
`ports`: `{<in_p>: {"role": "differential_input_p", "direction": "input"}, <in_n>: {"role": "differential_input_n", "direction": "input"}, <out>: {"role": "single_ended_output", "direction": "output"}}`.
* **2단 OTA**(`out` = `out`): M1 nmos g=`<in_p>` d=`x` s=`tail` / M2 nmos g=`<in_n>` d=`out` s=`tail` / M3 pmos g=`x` d=`x` s=`vdd` / M4 pmos g=`x` d=`out` s=`vdd` / M5 nmos g=`nb` d=`tail` s=`gnd`.
* **`tele`**(`out` = `o2`): M0 nmos g=`nb` d=`t` s=`gnd` / M1 nmos g=`<in_p>` d=`x` s=`t` / M2 nmos g=`<in_n>` d=`y` s=`t` / M3 nmos g=`nc` d=`o1` s=`x` / M4 nmos g=`nc` d=`o2` s=`y` / M5 pmos g=`o1` d=`o1` s=`vdd` / M6 pmos g=`o1` d=`o2` s=`vdd`.
* 계약 3·5에서 base의 결과와 병합 상당의 자동 채움 값(예: 병합 상당에서 입력쌍 `headroom_role`이 없음)은 **관찰값이지 기대값이 아니다**. test는 변형 사이의 같음만 판정한다(B26-1 검토 S4와 같은 원칙).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `PortDeclaration` | `@dataclass(frozen=True) class PortDeclaration: inputs: tuple; outputs: tuple` |
| `stick_diagram` | `port_declaration` | `def port_declaration(topology: dict) -> PortDeclaration:` |

(모듈 칸은 7535799 기준이다. Phase 3 병합 뒤에는 `rail_declaration`이 있는 모듈로 바꾼다. 바뀌는 기존 시그니처 하나: `resolve_stack_layout(transistors, matching_pairs, device_roles, stack_groups_override=None, *, rails, ports) -> dict`(B26-1의 `rails` 뒤에 `ports`). 지우는 def는 없다.)

## 판정 유형 근거

red-green. 모의 head(`7535799` + 위 범위 1~4, CC-4a 전이라 거부 예외는 `ValueError`로 대역)에서 실측했다('작성 전 실측' 1(b)(c)(e)).
* base red: 계약 1(신규 심볼 `AttributeError`, 허용), 계약 2·5·8(`meta["ports"]` 없음 → 위 'red 모양'대로 `AssertionError`/`Failed`), 계약 3(library 3/9 + 합성 `AssertionError`), 계약 4(`{M3, M5}` `AssertionError`), 계약 6(단일 파일 11가지 + 연결 파일 2가지를 전부 받아들임 → `pytest.raises` DID NOT RAISE = `Failed`), 계약 7(`direction` 없는 합성 `[]` `AssertionError`).
* 계약 9는 base에서도 green이다(보존). 기대 차이표의 차이는 의도한 변화다.
* E-LIB가 의도적으로 바뀌는 card다. 그래서 동작 보존은 '표에 있는 필드만 다름'으로 판정한다(DF-36의 `topology_ref`와 같은 방식). 기존 test 기대값이 바뀌는 것은 0개다('작성 전 실측' 7). 따라서 기준 약화(DEC-40)는 아니다.

## oracle 종류와 출처

* 계약 1·2: (a) 구성. 기대 입출력은 test가 topology JSON의 `ports`와 role 표 6행으로 만든다(피검 출력으로 만들지 않는다).
* 계약 3·5: (b) 변환 불변(이름 바꾸기). 기대값은 '같은 회로 다른 이름'의 같음이다.
* 계약 4: (a) 구성(차동 다리 규칙 + 2단자 직렬 사슬, 위 근거).
* 계약 6: (a) 구성(거부해야 할 입력을 test가 만든다).
* 계약 7: (a) 구성(합성 쌍의 게이트가 입력 role 넷)과 library 반환값 (c)(base 실행 결과 -- 위에 적은 값은 base 실측값이다).
* 계약 8: (c) 기존 구조(캐시가 첫 호출에 `load_topology`를 한 번 더 부른다) + (a) 이후 증가 0.
* 계약 9: (c) base 실행 결과(auditor) + 기대 차이표(승인 기록에 붙는다).

## 거부해야 할 입력

계약 6의 목록 전부. `load_topology`는 다른 분석 전에(`ports` 검사가 netlist 해석보다 먼저) 거부한다. `_TEMPLATE.topology.json`은 base `AttributeError`(netlist 원소가 설명 문자열) → 병합본 `ports` 거부로 예외 종류가 바뀐다. E-LIB 대상 밖이라 판정 영향은 없다.
판정기 자기 점검은 계약 6 끝.

## library 회로 적용 여부

적용한다. library 9회로 전부 `ports`를 가진다(role 6개 어휘 안, `direction`과 role 9/9 모순 없음). 계약 1·2·3·7·9 대상이다. SPECS 4회로는 선언 vsid가 있어 E3 경로 3을 타지 않는다. E3 차이는 SPECS 밖 3회로에서만 난다.

## 무동작 판정 입력(무발동 값)

* `common_gate_amplifier`·`current_reuse_telescopic_ota`·`folded_cascode`·`pushpull_follower_buffer`의 `load_topology` meta(`"ports"` 제외)가 base와 같다.
* SPECS 4회로 평가와 audit 9/9, `input_referred_offset_pairs` 9/9가 base와 같다.
* E3 경로 3 5회로 중 `common_gate_amplifier`·`pushpull_follower_buffer`가 base와 같다.

## 재현할 수치

없음(수치 산출물 변화 없음 -- SPECS 4회로 metric `float.hex` 동일, '작성 전 실측' 1(c)).

## V3 계획

`mutate_changed.py`(HEAD 판)는 AST 해시(docstring 제외)가 바뀐 def의 본문 전체를 변이한다. 모의 head에서 `changed_defs`는 6개다('작성 전 실측' 1(e)).

| def | 변이 | 인벤토리(기존) | 본문 직접 호출 test 추가 시 | parametrize 이름 문자열만 | 바뀐 줄에 걸친 변이(근사) |
|---|---|---|---|---|---|
| `stick_diagram.port_declaration`(새) | 22 | 137 | 138 | 137 | 22 |
| `stick_diagram.load_topology` | 63 | 137 | 138 | 137 | 7 |
| `sizing_recipe.input_referred_offset_pairs` | 22 | 60 | 61 | 60 | 2 |
| `sizing_recipe._load_full_topology_cached` | 10 | 63 | 64 | 63 | 2 |
| `sizing_recipe.resolve_stack_layout` | 26 | 61 | 62 | 61 | 1 |
| `sizing_recipe._build_theta_evaluator` | **497** | 60 | 60 | 60 | 1 |
| 합 | **640** | | | | 35 |

* '바뀐 줄에 걸친 변이'는 base↔head 줄 diff의 바뀐 줄과 노드 줄 범위가 겹치는 변이 수다. `draft_v3_scope_policy.spec.md`의 N2 정의를 구현한 도구가 아니므로 **근사**다.
* 비용의 78%(497)가 `_build_theta_evaluator` 한 문장(8060~8062 호출에 `ports=` 추가) 때문이다. 같은 def를 B26-1(#1, `rails=`)과 B26-2(#17, 8003 `_rail_nets`)도 바꾼다. 그래서 이 card의 V3 처리는 **B26-1 U1(V3 대상 범위 결정, `draft_v3_decision_question.md`)의 결과를 그대로 따른다**. 별도 사용자 결정을 만들지 않는다.
  * U1 = 2(바뀐 문장 + 감싸는 제어문 + 새 def 전체)이면 대상은 위 근삿값 수준이다(도구가 착수 시 잰다).
  * U1 = 1(def 전체)이면 `_build_theta_evaluator` 497개의 기존 문장 생존이 이 card에 다시 걸린다. B26-1이 그 def의 생존을 test 보강이나 해시에 묶인 면제로 처리했으면 그 처리를 승계할 수 없다. 면제는 def 해시에 묶이고(`20260930-v3-exempt-binding`), 이 card가 해시를 다시 바꾼다.
    그 경우 오케스트레이터가 착수 전에 E3 호출문 변경을 같은 def를 바꾸는 card(B26-2)와 묶을지를 사용자에게 올린다. 이 card의 기본안은 묶지 않는 것이다(E1~E3 동시 배선 원칙).
* **모의 계약 판정으로 죽는 변이(실측, '작성 전 실측' 1(e)).** 대상은 5 def의 변이 전부와 `_build_theta_evaluator`의 바뀐 줄 변이 1개, 합 144개다. 계약 1~3·5~7 모의 판정(`contracts.py`)으로 죽음 89, 생존 55.
  * **위 표의 근사 대상 35개(새 def 전체 + 바뀐 줄) 중 34개가 모의 계약으로 죽는다**: `port_declaration` 22/22, `load_topology` 7/7, `input_referred_offset_pairs` 2/2, `_load_full_topology_cached` 2/2, `resolve_stack_layout` 1/1.
    남는 1개(`sizing_recipe:_build_theta_evaluator:stmt_delete:body[26]`, `stack_groups_geometry = resolve_stack_layout(…)` 문장 삭제)는 기존 test가 죽인다. 모의 계약은 `_build_theta_evaluator`를 부르지 않는다. 대신 그 변이를 넣은 사본에서 SPECS 4회로 `_evaluate_once`가 4/4 `NameError`였다(인벤토리 60개 test가 이 경로를 탄다).
  * **생존 54개는 전부 이 card가 바꾸지 않은 기존 문장이다.**
    * `load_topology` 28: 연결 파일 병합 6, 이름 겹침 거부 2, vsid 반영 루프 2, 자동 채움 루프 8, 매칭쌍 분류 10
    * `resolve_stack_layout` 22: override 반환 2, 선언 vsid 경로 14, 경로 3의 조건(`refined is not None` 비교 포함)·그룹 조립 5, 레거시 폴백 `return` 1
    * `input_referred_offset_pairs` 3: `matching_sensitivity`·`len(names) < 2` 건너뛰기
    * `_load_full_topology_cached` 1: `return` 삭제
    * U1 = 2이면 판정 대상이 아니다. U1 = 1이면 기존 인벤토리 test(60~137개)가 죽이는지를 auditor가 재야 한다. 이번 측정은 기존 test 실행을 하지 않았다.
  * 계약 5의 변환 불변만으로는 경로 3의 `refined is not None` → `is None` 변이가 산다. 합성 `tele`에서 경로 3 결과와 레거시 폴백 결과가 같기 때문이다(모두 단독 그룹). 이 비교는 B37a가 바꾼 문장이 아니다(U1 = 2이면 대상 밖). U1 = 1이면 경로 3이 레거시와 다른 그룹을 내는 입력이 필요하다. 그런 입력을 기대값으로 고정하는 일은 회로 해석이므로, 그 경우 오케스트레이터가 base 실행 결과 (c)로 둘지 사용자에게 올린다.
* test 모양: 본문 직접 호출이면 각 def 인벤토리가 +1이다. parametrize 이름 문자열 + `getattr`이면 +0이다(실측). 계약 절 'test 모양'에 적었다.
* 승인 기록 면제 id와 겹침 0(HEAD `.ai/approvals`).
* 인벤토리 기준 실행이 실패하면 ERROR다(B28). selftest 18곳의 픽스처 보강('작성 전 실측' 7)이 test 커밋에 없으면 기준 실행이 실패한다. 순서 3 freeze 뒤 auditor가 base·head 인벤토리 기준 실행을 확인한다.

## 결정 필요 항목

1. **승인 기록(사용자 결정 기록 필요) -- `approval: 20260930-b37a-ports-roles`(`target_kind: decision`).**
   이 card는 **동작을 바꾼다**. library 3회로의 자동 채움 `headroom_role`이 사라지고, 2회로의 review 목록이 줄고, 3회로의 레이아웃 1차 그룹이 바뀐다.
   design 20 승인(`20260923-20-dead-code-dup-design`)은 '동작이 바뀌는 수정'을 덮지 않는다(review_b34 B1, review_b26_1 S3과 같은 결함을 반복하지 않는다). 그래서 사용자 원문이 있는 decision 기록 한 건이 card 커밋 전에 gate에 있어야 한다.
   기록이 덮을 것(사용자에게 확인받을 항목 -- 준비 자료 §5):
   * **(확인 1) 자동 채움 소실·레이아웃 그룹 변화를 받아들인다.**
     * E-LIB 기대 차이표 5회로: ngcc `headroom_role` 4개, sf_pushpull 20개, two_stage_ota_sf 5개 소실. nmcnr review 12 → 10, two_stage_ota 9 → 7.
     * E3 기대 차이표 3회로: ngcc·sf_pushpull·two_stage_ota_sf 레이아웃 1차 그룹 변화.
     * base 제안은 입력을 BIAS로 오분류한 결과다(예: sf_pushpull 입력쌍 M1·M2 `cascode`, ngcc 테일 M0과 입력쌍 M1·M2를 한 수직 그룹으로 묶음).
     * 사람이 선언한 4회로(current_reuse·folded·nmcnr·two_stage_ota)에서는 입력쌍 `headroom_role`이 `cascode`다. 그래서 B37a 뒤 입력쌍 제안이 `None`이 되는 것은 `_propose_headroom_roles` 규칙(입력이 `AMPLIFYING`이면 `None`)에 **입력쌍을 다루는 칸이 비어 있다**는 사실이 드러나는 것이다. 틀린 값이 새로 생기는 것은 아니다.
     * 세 회로 모두 SPECS 밖이라 지금의 평가 수치는 그대로다.
     * 기본안: 차이표를 승인 기록에 붙인다. 세 회로의 `headroom_role`·수직 그룹을 무엇으로 볼지(사람 선언으로 채울지, 규칙을 넓힐지)는 회로 해석이므로 6a의 ports·역할 제안표(DEC-35 절차)로 넘긴다.
     * 기존 test 기대값 변경 0이라 기준 약화(DEC-40)가 아니다. **승인이 아니라 확인** 사안이다.
   * **(확인 2) 출력은 포트만이다.** current_reuse의 `Vom1`/`Vop1`(1단 출력, 포트 아님)은 B37a 뒤에도 정규식으로 OUTPUT이다. B37b 뒤에는 SIGNAL이 된다. library 결과에는 영향이 없다(준비 자료 §3.2 p3 = p1).
     다만 `_reaches_output`(idioms 81~95, `m_cascode` 방향 판정)이 '출력'을 포트만으로 볼지는 회로 해석의 경계다. 기본안은 '포트만(선언만이 사실)'이고, 확인만 받는다. B37b card의 전제로 이 기록에 함께 남긴다.
   * **(확인 3) 순서**: B34(#45) → B26-1(#1) → CC-4a(#6) 병합 뒤에 착수한다. 근거:
     * 세 card 모두 `load_topology`를 바꾼다(B34는 import 실패 처리, B26-1은 `meta["rails"]`·`resolve_stack_layout(*, rails)`, CC-4a는 `SchemaRejectedError`). 그래서 순차 병합한다.
     * B26-2(#17)와는 어느 쪽이 먼저여도 되지만 동시 착수는 하지 않는다(같은 def `_build_theta_evaluator`).
     * Phase 4 design 초안의 `B26-2 ─> B37` 화살표는 B37a에는 필요 없다. 극성을 쓰지 않는다. 다만 V3 U1 = 1이면 위 'V3 계획'의 묶음 질문이 생긴다.
   * **(원칙 기본안 -- 기록에 적기만 한다)**:
     * `direction`과 role이 모순되면 거부한다. MG2 전까지 두 키가 공존하므로 조용히 한쪽을 고르지 않는다.
     * 연결 파일 `ports`는 진입 파일과 같아야 한다(B26-1 `supply_nets`와 같은 규칙).
     * 출력 role 0개는 받는다.
     * role 어휘 6개를 닫힌 표로 둔다. N3.16 786행에 어휘를 적는 개정은 판정 표 해시 입력 밖이다(`merge_gate.plan_tables_object` = N4.1·N4.2·N6.1 Phase 열·쓰기 경로표). 그래서 오케스트레이터 문서 커밋으로 한다. 착수 때 개정 전후 `plan_tables_hash`가 같은지 확인한다.
2. **V3 처리**: B26-1 U1의 결과를 따른다(위 'V3 계획'). 새 결정이 아니다.
3. 대기 중인 결정 UD-15(analog-grammar 소속)는 B37b의 선행 조건이지만 이 card와는 무관하다.

## 작성 전 실측

(측정: gate `master` `7535799`. 저장소 쓰기와 상태 변경 git은 없었다(`git archive`·`git show`·`git grep`·`git ls-tree` 읽기만. 끝난 뒤 `git status` 시작과 같음).
* scratch `C:/g58`에 `git archive HEAD` 사본 `base`와 모의 `head`를 만들었다. `head` = `base` + 범위 1~4이고, 거부 예외는 CC-4a 전이라 `ValueError` 대역이다. 문자열 치환은 대상이 정확히 1회 나오는지 assert로 확인했다(`make_head.py`).
* 게이트 함수(`mutate_changed`·`reachability`·`role_paths`)는 저장소 `tools/gates`에서 읽기 전용으로 import했다(`main` 실행 안 함). 측정 스크립트마다 import한 모듈 경로가 해당 사본 아래인지 assert로 확인했다.
* `$PY` = `C:/Python314/python.exe -B`, `PYTHONHASHSEED=0`. 측정 뒤 `C:/g58`을 삭제했다. 수치는 이 절에 옮겼다.
* 착수 시점(B34·B26-1·Phase 3·CC-4a 병합 뒤)에 오케스트레이터가 1(a)(e)·7을 같은 명령으로 다시 잰다. 줄 번호, 모듈 이름, `load_topology` 변이 수, `resolve_stack_layout` 시그니처(`rails` 포함)가 바뀐다.)

1. **사실 문장 재측정.**
   * (a) 줄·소비자.
     * `sed -n '<줄>p'`(HEAD 사본): SD `load_topology` 8550, E2 호출 8643~8644, E1 호출 8668~8671, `propose_vertical_stack_id_gap_fill` def 3261·`if inputs or …` 3292·docstring 3282, `propose_device_roles_gap_fill` def 3845·docstring 3855, NC `HINT_*` 39~43·사용 118~121·148.
     * SR: `input_referred_offset_pairs` 4481·`ports` 읽기 4511~4519, `_load_full_topology_cached` 4806·raw `"ports"` 4833, `resolve_stack_layout` 6470·경로 3 6572·docstring 6537~6543, `_build_theta_evaluator` 7930·호출 8060~8062.
     * `git grep -n -e 'get("ports")' -e '\["ports"\]' -- 'skills/analog-gmid-design/assets/*.py' workspaces/run_harness.py` → SR 4511·4833뿐.
     * `git grep -n -e 'direction") ==' -e '"direction"' -- 'skills/analog-gmid-design/assets/*.py'` → `ports` 비교는 SR 4519뿐이다. 나머지는 fork 결과 dict 키다.
     * `git grep -nF -e 'resolve_stack_layout(' …` → 운영 호출자는 SR 8060 하나, test 호출은 `test_s013` 2곳이다.
     * library `ports`(JSON 파싱 스크립트): 9/9 있음, role 6어휘 안, `direction`과 role 모순 0, `_comment` 키 5회로, `linked_topology_files` 비어 있음 9/9.
     * `_TEMPLATE`에는 `ports` 키가 없다(Phase 4 초안 F21과 일치. 준비 자료 §4.2 C3의 "`ports: null`"은 틀린 문장). 로드 결과는 base `AttributeError` → head `ports` 거부.
   * (b) 계약 실측(`rename.py`·`e2probe.py`·`e3probe.py`·`contracts.py`, base/head 각각 새 프로세스):
     * 계약 3: 이름 바꾸기 불변이 base 6/9다. current_reuse 8소자·ngcc 5·pushpull 4의 `headroom_role`이 달라진다. head는 9/9. 바꾸는 넷을 `HINT_*` 전부로 넓혀도 head 9/9다. 합성 4변형은 base 다름, head 같음.
     * 계약 4: base `{M3: S1, M5: S1}`, head `{M2, M3, M4, M5, M6: S1}`(두 이름 변형 같음).
     * 계약 5: base에서 `sig_a`·`vin_p`·`Vinp` 판은 `[[M0,M1,M2],[M3],[M4],[M5],[M6]]`, `Vip` 판은 전부 단독이다. head는 네 변형 전부 단독이다.
       참고: 합성 E3를 `_build_theta_evaluator`로 보려 했으나 review 게이트(`optimize_full_circuit_budget() 실행 전 review가 필요하다`)가 base·head 모두 막는다. 그래서 계약 5는 `resolve_stack_layout` 직접 호출로 둔다.
     * 계약 6: 단일 파일 11가지(키 없음·null·list·`{}`·`_comment`만·출력만·항목 비-dict·role 없음·어휘 밖·`direction` 모순 2가지)와 연결 파일 2가지(진입 파일과 다름·어휘 밖)를 base는 전부 받아들인다. head는 13가지 모두 거부한다(메시지에 `ports`·`DEC-62`). 연결 파일 `ports` 없음·같음은 둘 다 받는다.
     * 계약 7: 합성 `direction` 없음 base `[]`, head `[["M1","M2"]]`.
     * 계약 8: 계수 1 → 2 → 2 → 2.
     * 모의 판정 `contracts.py`(계약 1·2·3·5·6·7을 한 파일로 근사): base FAIL(C3 11가지·연결 파일·C2 `AttributeError`·C1 library 3회로·C1 합성·E3 `KeyError`·offset), head FAIL 0.
   * (c) 동작 보존(`measure.py <사본> <out.jsonl> --specs`, `compare.py`):
     * `load_topology` transistors 9/9 같음. meta(`"ports"` 제외)는 기대 차이표 5회로만 다르다(소자·필드까지 표와 일치).
     * E3 경로 3은 표 3회로만 다르다.
     * audit 9/9 같음(결과 2, `_netlist_sections_structured` 없음 `ValueError` 7 -- 경로 문자열만 다름).
     * `input_referred_offset_pairs` 9/9 같음.
     * SPECS 4회로 `_evaluate_once`: current_reuse·folded는 metric(19·5개 `float.hex`)과 sized 해시가 같고, two_stage_ota·nmcnr은 같은 `InfeasibleSizingError` 문구다. 실행 시간 base/head는 19.2/18.6 s, 0.2/0.2, 10.2/10.2, 22.4/22.0이다.
     * 준비 자료 §3.2 p1·§3.3을 같은 모양으로 재현했다.
   * (d) 접근자 role 대응: head `meta["ports"]` 9/9가 role 표로 만든 기대값과 같다(예: current_reuse `inputs=("Vim","Vip")`, `outputs=("Vom","Vop")`. two_stage_ota `outputs=("OUT",)`).
   * (e) V3(모의 head, `v3inv.py`·`mutrun.py`):
     * `mutate_changed.changed_defs(base, head)` → 6 def. `mutate_changed.mutants` 합 640(V3 계획 표).
     * 인벤토리: `reachability.read_tree(<repo>, "HEAD", GRAPH_PREFIXES)`에 모의 head SD·SR을 덮은 뒤 `reachability.build_graph` + `mutate_changed.inventory`로 쟀다. 승인 기록 면제 id(`mutate_changed._approved(<repo>, "HEAD")`)와 겹침 0.
     * test 모양: 합성 test 파일 `tests/contracts/test_b37a_ports_roles.py` 두 판(본문 직접 호출 / parametrize 이름 문자열 + `getattr`)을 그래프에 넣어 비교했다 → +1 / +0.
     * 모의 계약 판정: 변이를 하나씩 `mutate_changed._replace_def`로 적용하고 `contracts.py`를 새 프로세스로 돌렸다(`_build_theta_evaluator`는 바뀐 줄에 걸친 변이만). 144개 중 죽음 89. 근사 대상 35개 중 34개가 죽었다.
     * 남은 1개(`_build_theta_evaluator:stmt_delete:body[26]`)는 그 변이 사본에서 SPECS 4회로 `_evaluate_once` 4/4 `NameError`였다.
     * 기존 test 인벤토리 실행은 하지 않았다. U1 결과에 따라 대상이 달라지기 때문이다.
2. **이름 충돌.**
   * `git grep -n -e port_declaration -e PortDeclaration -e PORT_ROLE_SIDE` → 0건. `ls skills/analog-gmid-design/assets/tests/contracts | grep -i "b37\|port"` → 없음.
   * 새 test `A/tests/contracts/test_b37a_ports_roles.py`를 `grep -rn "glob(" skills/analog-gmid-design/assets/tests/`와 대조했다. `probe_*.py`(ts6)·`*.topology.json`·`*.py` 전수 스캔과 이름 충돌이 없다.
   * 전수 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_ts3_no_print_verdicts`)는 삭제 이름 참조·print 판정 토큰을 본다. 이 card는 def를 지우지 않으므로 해당 없다. `test_ic_markers_match_plan`은 `gmid_ic` 표식만 본다(IC를 켜지 않음).
3. **원칙의 계약화.**
   * 선언이 이긴다 → 계약 1·2·3(library 9 + 합성 4변형)
   * 조용한 폴백 금지 → 계약 6(13입력 + 판정기 자기 점검)
   * 만들면 배선 → 계약 3(E1)·4(E2)·5(E3, 운영 호출은 계약 9 차이표 + auditor 호출 그래프)·7(`direction` 소비자 교체)
   * 재계산 금지 → 계약 8
   * MG2 대비 role만 → 계약 1(`direction` 없음 = 같음)·7
   * 회로 무관(DEC-62) → 계약 3이 library 9 전부이고, 코드에 넷·회로 이름 리터럴이 없다(모의 head diff 확인 -- 새 문자열 리터럴은 role 6어휘·`input`/`output`·키 이름(`ports`·`role`·`direction`)·`_` 접두·오류 메시지뿐)
   * 전부 전 범위로 적었다(library 9회로·합성·13입력).
4. **쓰기 경로(N3.12.2).**
   * SD·SR 코드·docstring·주석, 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 311·338행 + 새 행): gmid-code-author.
   * 새 계약 test와 selftest 18곳 픽스처 보강(7): gmid-test-author(`skills/analog-gmid-design/assets/tests/**`). test는 엔진 소스를 읽지 않는다. 필요한 사실(합성 topology 모양·role 표·정규화·`SchemaRejectedError` 경로)은 이 card와 interface card에 적었다.
   * N3.16 786행 role 어휘, Phase 4 design #47 문구(`direction` 미사용·B37a/b 분할·`B26-2 ─> B37` 화살표 정정), 준비 자료의 `_TEMPLATE` 'null' 정정: 오케스트레이터 문서 커밋.
   * `_TEMPLATE.topology.json` `ports` 필드: library 데이터(승인 기록 조건)라 이 card 밖이다. 백로그로 둔다.
   * analog-grammar(`skills/analog-grammar/**`): 손대지 않는다(B36).
5. **계획서 소비자.**
   * `git grep -n -e "ports\.direction" -e "B37" -e "HINT_" -- docs/01-plan docs/02-design` → 계획 263행(DEC-69)·803행(MG2)뿐이다. `ports.direction` 삭제는 MG2에 남는다(이 card와 일치).
   * `git grep -n -e input_referred_offset_pairs -e resolve_stack_layout -- docs/01-plan docs/02-design/features` → history 4곳·계획 MOD8 행 설명뿐이다. 이름을 지우거나 옮기지 않으므로 고칠 것이 없다.
   * `git grep -n "ports" docs/01-plan/features/gain-budget-gmid-sizing.plan.md`의 DEC-35·DEC-62·N3.16 786행과 이 card의 원칙이 일치한다(786행에 role 어휘만 더한다 -- 4).
6. **미배선(V7).**
   * 새 def는 `port_declaration` 하나이고 `load_topology`가 부른다. 운영 루트에서 도달한다(모의 head 그래프 인벤토리 137).
   * 새 클래스 `PortDeclaration`은 접근자의 반환 레코드다.
   * 되살리는 def와 지우는 def는 없다. V7 면제 승인이 필요 없다.
7. **기존 계약 test·기존 test 영향.**
   * `git grep -n -i -e direction -e '"ports"' -e input_referred_offset_pairs -e resolve_stack_layout -- skills/analog-gmid-design/assets/tests/contracts tools/gates` → `test_d_delete_telescopic.py` 216~220뿐이다. 합성 topology에 이미 `ports`·role·`direction`이 있고 모순이 없다. head pytest에서 PASS다. 조정이 필요한 계약 test는 0이다.
   * pytest(판정 설정): `$PY -m pytest -c <사본>/tools/gates/pytest_gate.ini --rootdir=<사본> --confcutdir=<사본> --gmid-phase=2 -p no:cacheprovider -q -rfE <사본>/skills/analog-gmid-design/assets/tests`(`run_pt.py`, `ptcmp.py`).
     * base 42 failed·756 passed·15 xfailed. 사본 환경 결함(사본에 없는 경로·git 이력, ts6 probe 등)이고 gate 실행과 무관하다.
     * head 56 failed·4 errors·738 passed·15 xfailed. **새로 실패 18, 고쳐진 것 0.**
   * 새 실패 18의 내역:
     * `test_selftest_sizing_recipe.py` 16: s003·s011·s012·s013·s036~s043·s045·s050·s052·s053. 그중 s039·s041·s050·s053은 setup ERROR(픽스처 `*_state`).
     * `test_selftest_stick_diagram.py` 2: s071·s125.
   * 17곳은 `ports` 없는 합성 topology(s125는 `ports: {}`)를 tmp에 써서 `load_topology`를 부른다. 준비 자료 §3.5의 17과 같은 집합이다.
   * `test_s013`은 `resolve_stack_layout`의 새 키워드 `ports` 누락 `TypeError`다(준비 자료에 없던 1곳 -- E3 시그니처 때문).
   * s003·s043·s125는 다른 거부의 **메시지 내용**을 단언한다. 그래서 입력 role을 포함한 `ports`를 반드시 더해야 원래 판정이 살아난다.
   * 조정은 test-author의 **입력 픽스처 보강**이다: 합성 topology에 `ports`를 더하고, `test_s013` 두 호출에 `ports=`(그 topology의 `load_topology` meta `"ports"` 또는 `port_declaration(<그 dict>)`)를 더한다.
     기대값 변경이 아니라 V5(기준 약화) 승인이 필요 없다. test 커밋에 넣는다(code 커밋과 분리, 계획 §14).
   * CC-4a 뒤에는 거부가 `SchemaRejectedError`(`ValueError` 아님)다. 그래서 `pytest.raises(ValueError)`로 다른 거부를 보는 s003·s043·s125는 픽스처를 보강하지 않으면 여전히 실패한다(같은 18곳).
