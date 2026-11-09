---
id: 20260930-b37a-ports-roles
phase: 4
evidence_type: red-green
gate_change: no
approval: 20260930-b37a-ports-roles
---
## 의도

백로그 B37의 앞쪽 절반(B37a). 준비 자료 `_drafts/prep_b37_ports.md`, Phase 4 design 초안 #47을 이 card로 좁혔다. 뒤쪽 절반 B37b(analog-grammar 라이브러리 경로의 `HINT_*` 제거)는 B36 뒤 별도 card다.
(v2 -- 검토 `_drafts/review_b37a.md` 반영. 바뀐 점과 근거는 `_drafts/b37a_revision_log.md`.)
(v3 -- Phase 4 design 초안 v0.9.5 §5.4 #47 '작성 전 조건' (가)(나)와 §6 'E11 차이 집합 표' 성분 P·D47 반영. 계약 9의 산문 차이표를 **항목 단위 삭제 목록(데이터 블록)**으로 바꿨고, `meta["ports"]` 직렬화 모양을 '신규 시그니처'(interface card에 그대로 실림)에 고정했고, 계약 2와 '`ports` 기대값'을 피검 함수가 아닌 독립 oracle(library `ports` 선언 + 계약 1 role 표)로 바꿨다. 재측정 판 = gate `master` `dd60db6`('작성 전 실측' 8). v2 원본은 `_drafts/draft_b37a.spec.pre-p4v095.md`.)

**문제.** topology `ports`는 사람이 쓰는 선언이다(DEC-35 절차의 대상 필드. 파일별 확인 기록은 회로마다 다르다 -- '결정 필요 항목' 1의 Q2 표). 그런데 `stick_diagram.load_topology`는 이 선언을 analog-grammar에 넘기지 않는다. 그래서 `netclass.classify_nets`가 넷 이름 정규식(`HINT_INPUT` 등, NC 39~43)으로 입력·출력을 추정한다.
* library 9회로의 입력 포트 16개 가운데 정규식이 INPUT으로 맞힌 것은 4개(`Vip`·`Vim`·`Vinp`·pushpull `vin`)다. 11개(`vin_p`/`vin_n`/`Vin_p`/`Vin_n`/`Vinn`)는 BIAS, common_gate `vin`은 INTERNAL이 된다(준비 자료 §2.1).
* 그 결과 자동 채움이 넷 이름에 따라 갈린다. 레일(`supply_nets`) 밖의 넷을 **전부** 중립 이름으로 바꾸면 base에서 3/9 회로(current_reuse·ngcc·pushpull)의 `load_topology` meta가 바뀐다('작성 전 실측' 1(b)).
* 이것은 DEC-62(새 토폴로지는 데이터만으로) 위반이다. 선언이 있는데 이름이 동작을 정한다.

선언을 가진 쪽에서 문법으로 가는 운영 진입점은 셋이고, 셋 다 선언을 넘기지 않는다.

| # | 진입점 | 지금 |
|---|---|---|
| E1 | SD `load_topology` → `propose_device_roles_gap_fill`(SD 8668~8671) | `inputs`/`outputs` 없음. `base_inputs`를 쓰는 4함수(`_propose_vertical_stack_ids`·`_propose_gm_id_roles`·`_propose_L_roles`·`_propose_headroom_roles`)가 정규식 분류를 본다 |
| E2 | SD `load_topology` → `propose_vertical_stack_id_gap_fill`(SD 8643~8644) | `inputs` 등이 모두 비어 3293의 `if inputs or …`가 거짓. 차동 다리 간선 기능이 운영에서 꺼져 있다(docstring 3282 "조용히 건너뛴다") |
| E3 | SR `_build_theta_evaluator`(8060~8062) → `resolve_stack_layout` 경로 3(SR 6572) | `refine_differential_and_mirror_relations(transistors)`. 선언 vsid가 없는 회로에서만 탄다. docstring 6537~6543이 "ports 파싱은 필요해지면 추가"라고 적어 두었다 |

`ports`의 다른 소비자: SR `input_referred_offset_pairs`(4481)가 `_load_full_topology_cached`(4806)에 실어 둔 raw `ports`(4833)를 `p.get("direction") == "input"`(4511~4519)으로 읽는다.
엔진에서 `ports`의 `direction`을 읽는 곳은 여기 하나다. `direction`은 MG2(DEC-69, 6a 착수 전)가 지우는 키다(N3.16 786행: `ports{<넷>: {role}}`, `direction`은 role에서 유도).

**원칙 기본안.**
* 선언이 정규식을 이긴다. 준비 자료 §2의 불일치는 '어느 쪽이 맞나'가 아니라 이름 표기(`_p`, `Vinn`) 때문에 생긴 분류 차이다.
* 조용한 폴백 금지(계획 §3.2 P1). `ports` 키가 없으면 정규식으로 돌아가지 않고 거부한다. '포트 없음'은 명시적 `ports: {}`로만 선언한다(B26-1 `supply_nets: []` 선례 -- 빈 선언은 조용한 기본값이 아니라 명시 선언이다).
* 선언은 사실이어야 한다. netlist에 없는 넷이나 레일을 포트로 선언하면 거부한다(조용히 무시하거나 레일 분류를 덮어쓰지 않는다 -- NC 1b는 선언 입력·출력을 레일 분류 위에 덮어쓴다).
* 만들면 배선. 접근자 하나를 만들어 운영 진입점 E1·E2·E3와 `input_referred_offset_pairs`를 같은 card에서 전부 대체한다. E1만 고치면 이름 의존이 E2·E3로 남는다(준비 자료 §4.3).
* role만 읽는다. 이 card 뒤 엔진의 `direction` **소비자**는 0이 된다. 남는 것은 접근자의 '`direction`이 있으면 role과 같아야 한다' 검사 하나다. 그래서 MG2의 ports 몫은 키 삭제·옛 키 거부와, 이 접근자 분기를 거부로 바꾸는 수정 1건이다(작은 def라 V3 비용이 작다).
* 재계산 금지(NFR-2). 선언은 `load_topology`에서 한 번 읽어 `meta["ports"]`에 싣는다. SR은 raw `ports`를 다시 해석하지 않는다. 새 캐시는 만들지 않는다.
* B26-1(`rail_declaration`·`RailDeclaration`·`meta["rails"]`·`resolve_stack_layout(…, *, rails)`)과 같은 모양을 쓴다.

**범위(코드).** A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 gate `master` `7535799` 기준이다.
착수 시점(B34 → B26-1 → Phase 3 → CC-4a 병합 뒤)에는 줄과 모듈이 바뀐다. 오케스트레이터가 card 커밋 전에 다시 재고, '신규 시그니처'의 모듈을 `rail_declaration`이 있는 모듈로 바꾼다(Phase 3 v4 A-3: `load_topology`는 MOD3, 접근자는 `ports`를 읽는 MOD2 쪽 -- 준비 자료 §4.1).
1. **접근자 신설**(SD, B26-1 `rail_declaration` 옆): `port_declaration(topology: dict) -> PortDeclaration`. `PortDeclaration`은 frozen dataclass이고 필드는 `inputs`·`outputs` 둘이다. role → 입출력 대응은 닫힌 표 하나(비공개 상수, role 6개)로 정한다.
   * 형식 검사만 한다(계약 6의 '접근자 거부' 목록). 명시적 `ports: {}`는 `PortDeclaration((), ())`이다.
   * docstring에 '검사하지 않는 것:' 절을 둔다: 포트 넷이 netlist에 있는가, 레일과 겹치는가 -- `load_topology`가 본다(그 dict 하나에는 연결 파일의 소자가 없다).
2. **`load_topology`**: 진입 파일 dict로 접근자를 한 번 부른다. 연결 파일 규칙을 적용하고(계약 2), 연결 파일까지 합친 소자를 만든 뒤 두 검사를 한다(netlist 해석 뒤, 문법 호출 전):
   * 존재: 포트 넷(`inputs ∪ outputs`)이 모두 트랜지스터 단자(source·drain·gate) ∪ `passive_elements` 단자 ∪ `ideal_sources` 단자(진입 파일 + 연결 파일)에 있어야 한다.
   * 레일 겹침: 포트 넷 ∩ `meta["rails"].nets`(B26-1의 `rail_declaration` 결과 -- `load_topology` 안의 그 값)가 비어야 한다.
   결과를 `meta["ports"]`에 싣는다. 그 값을 E2(`propose_vertical_stack_id_gap_fill(…, inputs=, outputs=)`)와 E1(`propose_device_roles_gap_fill(…, inputs=, outputs=)`)에 넘긴다(B26-1 뒤에는 같은 호출에 `rails=rails`도 있다).
   두 피호출 함수는 이미 그 키워드를 받는다. 시그니처와 본문은 바꾸지 않고 docstring만 고친다.
3. **E3**: SR `resolve_stack_layout`에 기본값 없는 키워드 전용 `ports: PortDeclaration`을 더한다(B26-1 뒤 모양 `…, stack_groups_override=None, *, rails, ports`). 경로 3이 `refine_differential_and_mirror_relations(transistors, ports.inputs, ports.outputs, rails=rails)`를 부른다(B26-1 뒤 모양. `rails=`는 B26-1이 이미 넣은 키워드다).
   `_build_theta_evaluator`의 호출(8060~8062)이 `ports=meta["ports"]`를 넘긴다.
4. **`input_referred_offset_pairs`**: 입력 넷 집합을 캐시 엔트리의 `meta["ports"].inputs`에서 읽는다. raw `ports` 읽기(4511~4519)는 지운다.
   * 거부는 **유지하되 조건을 바꾼다**: offset 쌍(`matching_sensitivity == "offset"`이고 이름 2개 이상)이 하나라도 있는데 입력 넷이 0이면 거부한다. 예외 타입은 이 함수가 지금 `ports` 없음에 쓰는 타입 그대로다(7535799 `ValueError`. CC-4a가 이 함수의 타입을 바꿨으면 그 타입). 메시지에 `ports`와 `DEC-62`를 적는다.
   * offset 쌍이 0이면 입력 0이어도 `[]`다(base는 `ports`가 비면 offset 쌍과 무관하게 `ValueError` -- 명시적 `ports: {}`를 받게 되면서 생기는 차이. library 9회로는 모두 입력이 있어 해당 없음).
   * `ports` 키 자체가 없으면 그보다 먼저 `load_topology`가 거부한다.
   `_load_full_topology_cached`의 raw `"ports"` 엔트리(4833)는 소비자가 0이 되므로 지운다. 옆 주석 4831~4832도 함께 지운다.
5. **docstring·주석**(AST 해시 불변): SD `load_topology` meta 목록(`"ports"` 추가), SD 3276~3283(`propose_vertical_stack_id_gap_fill` -- 운영에서는 `load_topology`가 `ports` 선언을 넘긴다), SD 3855~3857(`propose_device_roles_gap_fill` -- 같은 취지).
   그리고 SR 4481~4505(`input_referred_offset_pairs` -- 조건 2를 `meta["ports"].inputs`로, `ports` 없음 거부는 `load_topology`, 입력 0 + offset 쌍 거부), SR 6537~6543(`resolve_stack_layout` -- "ports 파싱은 필요해지면" 삭제).
6. **레지스트리**(code-author, 같은 커밋): 접근자 행을 새로 만든다(개념 '포트 선언(입출력)', 정본 = 이 접근자, 비고 "GB0 로드 게이트(계획 314행 `ports`)는 이 접근자를 재사용한다 -- 두 번째 정본(DUP) 금지"). 311행 `input_referred_offset_pairs` 비고("ports input net" → `meta["ports"].inputs`)와 338행 `resolve_stack_layout`(키워드 `ports`)을 고친다.

**범위 밖.**
* **B37b**: analog-grammar `classify_nets`의 이름 정규식 제거. 비포트 넷의 이름 의존이 여기 남는다: 게이트 전용 비포트 넷의 1c 힌트(`HINT_INPUT`·`HINT_BIAS`·`HINT_FB`·`HINT_CLK`, NC 113~124는 선언되지 않은 게이트 전용 넷마다 힌트를 **항상** 적용한다)와 SIGNAL 넷의 `HINT_OUT`(current_reuse `Vom1`/`Vop1`, two_stage `O1`, two_stage_ota_sf `O1`/`OUT`). library 결과에는 영향이 없다(준비 자료 §3.2 p3·p4 = p1). 합성 반례는 '작성 전 실측' 1(b).
  * 사실로만 적는다: B37a 뒤 E1~E3의 실효 출력 = 선언 출력 포트 ∪ {SIGNAL이고 `HINT_OUT`에 걸리는 넷}이다(B37b까지). B37a가 바꾸는 것은 선언 출력이 **처음으로** `_reaches_output`(idioms 79~)에 들어간다는 점이다. 그 library 효과는 계약 9 삭제 목록·E3 표에 들어 있다.
  * '출력을 포트만으로 볼지'(B37b 뒤 비포트 SIGNAL 넷을 출력에서 뺌)는 `m_cascode` 방향 판정의 회로 해석이고 계획 6a DEC-65·J ratify와 같은 축이다. **B37b card의 결정 항목**이다. 이 card와 그 승인 기록에는 넣지 않는다.
* **B38**: 바이어스 넷 추정(`ports`에 바이어스 role이 없다).
* **MG2**: topology JSON 9개에서 `direction` 키 삭제, 옛 키 거부 게이트, 접근자의 `direction` 일치 분기를 거부로 바꾸는 수정.
* `_TEMPLATE.topology.json`에 `ports` 필드가 없다. library 데이터라 승인 기록 조건이고 오케스트레이터 몫이다. 백로그로 둔다(B26-1 검토 M2와 같은 자리).
* analog-grammar 파일(`skills/analog-grammar/**`)은 고치지 않는다. 쓰기 경로표에 주체가 없다(B36).
* 3회로의 자동 채움 소실(아래 '결정 필요 항목' 1)을 메우는 규칙 확장이나 선언 보강, 사라진 값의 옳고 그름 판단은 6a(DEC-35 ports·역할 제안표, J ratify)로 넘긴다.

이 card는 회로·넷·소자 이름을 읽지 않는다. 판정은 role 어휘(선언 표), 선언 레일, netlist 단자 집합과 `_` 접두 주석 규약만 읽는다.

## 관찰 가능한 계약

모듈 이름: 아래 `M`은 `rail_declaration`이 있는 모듈이다(7535799에서는 `stick_diagram`. Phase 3 병합 뒤 이름은 오케스트레이터가 card 커밋 때 적는다). `load_topology`와 `resolve_stack_layout`·`input_referred_offset_pairs`는 card 커밋 시점의 모듈 이름으로 interface card에 실린다.
거부 예외 `SchemaRejectedError`는 CC-4a가 만든 클래스다(N3.14. `Exception` 직접 하위이고 `ValueError`가 아니다). interface card에 모듈 경로를 싣는다. `input_referred_offset_pairs`의 거부 타입은 범위 4대로 그 함수의 기존 타입이다(interface card에 적는다).

**test 모양(V3 인벤토리 조건).** `port_declaration`·`load_topology`·`resolve_stack_layout`·`input_referred_offset_pairs`는 test 함수 **본문**에서 `<모듈>.<이름>(…)` 형태로 직접 부른다.
`@pytest.mark.parametrize`의 이름 문자열이나 모듈 상수 이름 목록 + `getattr`로만 부르면 V3 정적 인벤토리에서 빠진다(실측 -- v1 '작성 전 실측' 1(e)). 회로·이름 변형의 반복은 parametrize로 해도 된다.
test는 analog-grammar 기호(`netclass.HINT_*` 등)를 import하지 않는다. 바꿀 넷 집합은 topology JSON만으로 정한다(계약 3).

**red 모양.** 허용 예외(00-common §8.1)는 `AssertionError`·`Failed`·신규 심볼 import 오류뿐이고, red 수집 플러그인은 예외 **타입**만 본다(`merge_gate._RedCapture.record`).
* 진입점 호출을 `try` / `except Exception: pytest.fail(…)`로 감싸지 않는다. 그렇게 하면 base의 `KeyError`(`meta["ports"]`)·`TypeError`(`ports=` 키워드)가 `Failed`로 세탁된다. 이 규칙이 막으려는 '동작이 아니라 인터페이스 부재로 생긴 실패'를 red로 세는 우회다. assert를 `try`·`if` 안에만 두면 V4 규칙 (3)에도 걸린다.
* 새 키워드 `ports=`를 직접 넘기는 test는 base에서 `TypeError`다. 허용 밖이라 red로 세지 않는다(B26-1 V2 선례). red는 시그니처가 안 바뀌는 진입점이 맡고, 판정 기록은 두 종류를 나눠 적는다.
* 계약 2는 `assert "ports" in meta`가 정직한 red다(계약 내용이 'meta가 선언을 싣는다'이므로). 계약별 red 근거는 '판정 유형 근거'.

1. **접근자(role → 입출력).** `M.port_declaration(topology)`는 topology JSON 한 파일을 읽은 dict를 받아 `M.PortDeclaration(inputs=…, outputs=…)`를 돌려준다.
   * `inputs`는 role이 `single_ended_input`·`differential_input_p`·`differential_input_n`인 넷 이름의 오름차순 tuple이다. `outputs`는 role이 `single_ended_output`·`differential_output_p`·`differential_output_n`인 넷 이름의 오름차순 tuple이다.
   * `ports`의 키 가운데 `_`로 시작하는 것(주석 규약, 예: `_comment`)은 건너뛴다.
   * 명시적 `ports: {}`와 `_comment`만 있는 `ports`는 `PortDeclaration((), ())`이다. 출력만·입력만 있는 선언도 받는다.
   * `direction` 키는 결과에 영향을 주지 않는다. 있으면 role과 같은 쪽(`input`/`output`)이어야 한다(계약 6). 없어도 결과가 같다.
   * `PortDeclaration`은 frozen dataclass라 `==`가 필드 비교다. 판정은 `(pd.inputs, pd.outputs)` 튜플 비교로 써도 된다.
   * library 9회로 각각에서 기대값은 test가 topology JSON의 `ports`와 위 role 표로 만든다(oracle (a)). 예: `folded_cascode` → `inputs == ("vin_n", "vin_p")`, `outputs == ("out",)`.
2. **`load_topology`가 선언을 싣는다.** `t, meta = load_topology(p)`이면 `meta["ports"]`가 `M.PortDeclaration`이고 `(meta["ports"].inputs, meta["ports"].outputs)`가 **test가 p의 JSON `ports`와 계약 1 role 표로 직접 만든 튜플 쌍**과 같다(library 9 + 합성. oracle (a) -- 피검 함수 `port_declaration`의 출력을 기대값으로 쓰지 않는다. v3, Phase 4 design v0.9.5 §6 성분 P와 같은 원칙).
   * 배선 확인(기대값 출처가 아니다): 같은 p에서 `meta["ports"] == M.port_declaration(<p의 JSON dict>)`도 성립한다. 이 등식은 '`load_topology`가 접근자를 부른다'의 관찰이고, 값의 옳음은 위 독립 기대값이 판정한다.
   * `linked_topology_files`의 연결 파일이 `ports`를 선언하면 그 선언도 같은 형식 검사(계약 6)를 거친다. 그 결과가 진입 파일의 결과와 다르면 거부한다(어느 쪽을 고를지 추측하지 않는다).
   * 연결 파일에 `ports`가 없으면 진입 파일 선언을 쓴다.
   * `meta`의 다른 키와 `transistors`의 동작 보존은 계약 9다.
3. **E1 -- 자동 채움은 포트 넷 이름과 무관(이름 바꾸기 불변, 대표 관찰).**
   * **library 판**: 9회로 각각에서 바꿀 넷 집합 = 레일(`supply_nets`) 밖의 **모든** 넷 -- 트랜지스터 단자(source·drain·gate), `passive_elements`·`ideal_sources`의 `terminals`, `ports`의 키(`_` 키 제외). 정규식은 쓰지 않는다.
   * 그 넷을 회로 안에서 유일한 중립 이름(예: `ZQ<i>Q`)으로 바꾼 topology를 tmp에 쓴다. 바꾸는 곳은 JSON 전체에서 그 넷 이름과 **정확히 같은** 문자열 값과 키다.
   * 원본과 바꾼 topology의 `load_topology` meta를 비교한다. 바꾼 쪽은 meta 문자열 안의 중립 토큰을 원래 이름으로 되돌린다(부분 문자열 치환, 긴 토큰부터 -- 파생 문자열 `…_fold` 포함). `"ports"` 키는 비교에서 빼거나 집합으로 비교한다(정렬 순서가 이름에 따라 바뀐다).
   * 정규화 뒤 `==`이면 통과다. 정규화: `set`/`frozenset` → 정렬 리스트, dataclass → 필드 dict, 나머지 dict·list는 재귀.
   * base: current_reuse(8소자)·ngcc(5소자)·pushpull(4소자)에서 `device_roles`·`_device_roles_autofilled`가 달라져 FAIL. 병합 상당은 9/9 같다('작성 전 실측' 1(b)).
   * **합성 판**(라이브러리와 독립): 아래 합성 2단 OTA와 `tele`에서 **포트 넷만** 바꾼 네 변형 -- 입력 이름 쌍 `("sig_a","sig_b")`, `("Vip","Vim")`, `("vin_p","vin_n")`, `("Vinp","Vinn")` -- 의 meta가 이름을 맞춘 뒤 모두 같다. base에서는 FAIL이다(두 topology 모두 네 변형이 세 가지 결과로 갈린다. 예: 2단 OTA `sig_a`·`vin_p` 판은 입력쌍 M1·M2가, `Vinp` 판은 M2만 `headroom_role: cascode` 제안을 받고, `Vip` 판은 받지 않는다).
   * **경계(이 card의 불변 범위)**: 비포트 넷(게이트 전용 넷의 `HINT_INPUT`·`HINT_BIAS`·`HINT_FB`·`HINT_CLK`, SIGNAL 넷의 `HINT_OUT`)의 이름 의존은 B37b가 닫는다. test는 **비포트 넷 이름만 바꾸는** 합성 변형을 이 card의 계약으로 쓰지 않는다.
     (참고 실측, 계약 아님: `tele`의 캐스코드 게이트 넷 `nc`를 `in2`로 바꾸면 병합 상당에서도 M3·M4의 자동 채움이 달라진다. library에는 그런 넷이 없어서 library 판이 9/9 성립한다.)
4. **E2 -- 차동 다리 간선이 운영에서 동작.** 합성 텔레스코픽 topology(아래 `tele`)에 `device_roles = {"M1": {"vertical_stack_id": "S1"}}`만 선언하면 `meta["_vertical_stack_id_autofilled"]`가 `{"M2": "S1", "M3": "S1", "M4": "S1", "M5": "S1", "M6": "S1"}`이다.
   * 그 제안이 meta에 반영된다: `meta["device_roles"]`에서 M1~M6의 `vertical_stack_id`가 모두 `"S1"`이고 M0에는 없다(`None` 또는 키 없음).
   * 입력 이름 `sig_a`/`sig_b`와 `Vip`/`Vim`에서 같다.
   * 기대값의 근거(oracle (a)): 차동쌍 두 다리는 같은 헤드룸 컬럼에 있다(`propose_vertical_stack_id_gap_fill` docstring의 규칙). 그래서 M1·M2를 묶는다. 그리고 각 다리의 2단자 직렬 사슬(M1–M3–M5: 넷 `x`·`o1`, M2–M4–M6: 넷 `y`·`o2` -- D/S 단자가 정확히 둘인 넷)을 KCL 간선으로 묶는다.
   * base는 `{"M3": "S1", "M5": "S1"}`(차동 간선 없음)이고 `device_roles`의 `S1`도 M1·M3·M5뿐이라 FAIL이다.
5. **E3 -- 레이아웃 1차 그룹이 넷 이름과 무관.** 합성 `tele` topology(선언 vsid 없음)의 네 입력 이름 변형(계약 3과 같은 네 쌍)마다 `t, meta = load_topology(p)`, `g = resolve_stack_layout(t, [], meta["device_roles"] or {}, ports=meta["ports"], rails=meta["rails"])`를 부른다(`device_roles`가 비면 `load_topology`가 `None`을 싣는다 -- `all_device_roles or None`). 그 결과 `sorted(sorted(v) for v in g.values())`가 네 변형에서 모두 같다(oracle (b) 변환 불변).
   * 병합 상당에서는 네 변형 모두 같다. (base 시그니처로 같은 입력을 부르면 `sig_a`·`vin_p`·`Vinp` 판이 `[M0, M1, M2]`를 한 그룹으로 묶고 `Vip` 판은 묶지 않는다 -- 관찰값이다. 이 test 모양으로는 base에서 `KeyError`/`TypeError`라 red가 아니다 -- '판정 유형 근거'.)
   * `ports`는 기본값이 없다. 빠뜨리면 `TypeError`다.
   * **(b) 경로 3이 실제로 쓰인다(승인 기록 값 고정 -- '결정 필요 항목' 1의 Q3에 달림).** 합성 `tele`·2단 OTA와 library 대부분에서는 경로 3 결과가 레거시 폴백(`geometry_colocation_union`)과 같아서, 경로 3 분기 문장(`if refined is not None and refined.get("vertical_stack_id_candidates"):`)을 통째로 지워도 위 (a)와 기존 test가 모두 통과한다(실측 -- 'V3 계획' 1). 두 결과가 갈리는 입력은 library `sf_pushpull_output_opamp` 하나다.
     그래서 `t, meta = load_topology(<sf_pushpull>)`, `g = resolve_stack_layout(t, [tuple(p["names"]) for p in meta["symmetry"]["matching_pairs"] if p["current_forced"]], {k: v for k, v in (meta["device_roles"] or {}).items() if not k.startswith("_")}, ports=meta["ports"], rails=meta["rails"])`(`_build_theta_evaluator`와 같은 인자 모양)의 `sorted(sorted(v) for v in g.values())`가 계약 9 E3 표의 병합 상당 값(전체 목록)과 같음을 판정한다.
     * oracle: 승인 기록(Q1·Q3에서 사용자가 받아들인 E3 표 값). 회로 해석으로 '맞는 값'이라는 뜻이 아니라 '승인된 동작'을 고정한다는 뜻이다.
     * 6a(J ratify)가 이 값을 바꾸면 그때 기대값 변경이 되어 V5·DEC-40 승인 대상이다(그 card가 처리).
     * Q3에서 사용자가 고정을 받지 않으면 이 test는 쓰지 않는다. 그때 그 변이는 해시 묶음 면제(비등가 변이 면제 = 약화, 사용자 승인)로만 V3를 통과한다.
   * 운영 배선: `_build_theta_evaluator`가 `resolve_stack_layout`에 넘기는 `ports`가 그 topology `load_topology` meta의 `"ports"`다(auditor 호출 그래프 확인 + 계약 9의 E3 차이표).
6. **거부(조용한 폴백 없음)·수용.** 아래 입력은 `load_topology`가 `SchemaRejectedError`로 거부한다. 메시지에 `ports`와 `DEC-62`가 있다.
   * **접근자 거부**(`port_declaration(<그 dict>)`를 직접 불러도 같은 예외):
     * 최상위 `ports` 키 없음
     * `ports: null`, `ports`가 dict가 아님(예: list)
     * 포트 항목이 dict가 아님(예: `"sig_a": "input"`), `role` 없음, role이 6개 어휘 밖(예: `"differential_input"`), 넷 이름이 빈 문자열
     * `direction`이 role과 모순(예: `differential_input_p` + `"direction": "output"`, `single_ended_output` + `"direction": "input"`)
   * **`load_topology`만 거부**(접근자 직접 호출은 받는다 -- 범위 1의 '검사하지 않는 것'):
     * 포트 넷이 트랜지스터·`passive_elements`·`ideal_sources` 단자 어디에도 없음(예: `zz_absent`)
     * 포트 넷이 선언 레일(`supply_nets`)의 원소(예: `vdd`를 입력으로 선언)
     * 연결 파일의 `ports`가 위 접근자 규칙을 어기거나 진입 파일 결과와 다름
   * **수용**(거부하지 않는다): 명시적 `ports: {}`, `_comment`만 있는 `ports`(둘 다 `PortDeclaration((), ())`), 출력 role만 있는 선언, 입력 role만 있는 선언, `direction`이 role과 같은 선언, 연결 파일에 `ports` 없음, 연결 파일 `ports`가 진입 파일과 같음.
     그리고 존재 검사의 범위(트랜지스터 단자만이 아니다): 포트 넷이 진입 파일 `passive_elements`의 `terminals`에만 있음(예: 2단 OTA + `{"name": "Rs", "kind": "resistor", "terminals": ["src", <in_p>], "value_ohm": 1e3}`, 포트 `src` = `single_ended_input`), `ideal_sources`의 `terminals`에만 있음(예: `{"name": "Vs", "kind": "voltage_source", "terminals": ["vsrc", "gnd"], "value_volt": 0.9, "implementable": false}`, 포트 `vsrc`), **연결 파일**의 `passive_elements` 단자에만 있음 -- 셋 다 받고 `meta["ports"].inputs`에 그 넷이 들어 있다.
   * **판정기 자기 점검**: 누락 시 정규식 분류로 계속 가는 합성 구현(예: test 안의 가짜 로더가 `ports` 키가 없을 때 `PortDeclaration((), ())`를 돌려준다)과 거부 메시지에 `ports`가 없는 구현을 같은 판정 함수에 넣으면 실패해야 한다(`test_d_delete_telescopic`의 거부 점검과 같은 형태).
7. **`direction` 소비자 교체.** 합성 2단 OTA에 `symmetry.matching_pairs = [{"names": ["M1","M2"], "matching_sensitivity": "offset", "current_forced": true}]`를 둔다. 이때 `input_referred_offset_pairs(p)`가 `direction` 키가 있든 없든 `[["M1","M2"]]`다.
   * base는 `direction`이 없으면 입력 집합이 비어 `[]`를 조용히 돌려준다. 그래서 FAIL이다.
   * 같은 topology에 `ports: {}`(offset 쌍 있음)이면 거부한다(범위 4의 타입, 메시지에 `ports`·`DEC-62`). `ports: {}`이고 offset 쌍이 없으면 `[]`다.
   * 이름이 2개 미만인 offset 항목(`{"names": ["M1"], "matching_sensitivity": "offset"}`)은 쌍이 아니다: 결과에 없고 '입력 0 + offset 쌍' 거부도 일으키지 않는다(`ports: {}`이면 `[]`, 기본 `ports`이면 `[]`).
   * library 9회로의 반환은 base와 같다: current_reuse `[["M1a","M1b"],["M4a","M4b"]]`, folded `[["M1","M2"]]`, nmcnr `[["M102","M103"]]`, two_stage_ota `[["M1","M2"]]`, 나머지 5회로 `[]`.
8. **재계산 없음.** 새 tmp 경로의 topology에서 접근자 호출 수를 센다. `load_topology` 1회 → 1이다. 이어 `input_referred_offset_pairs` 첫 호출 → 2다(`_load_full_topology_cached`가 캐시를 못 찾아 `load_topology`를 한 번 더 부른다 -- 기존 구조).
   그 뒤 같은 경로로 `input_referred_offset_pairs` N회·`_topology_meta_cached` N회 → 2 그대로다.
   * 계수 래퍼 모양: test 본문 첫 줄에서 **원래 함수를 먼저 읽는다** -- `orig = M.port_declaration`. 그 뒤 `monkeypatch.setattr(M, "port_declaration", <orig를 부르며 세는 함수>)`. base에서는 첫 줄이 인터프리터 `AttributeError`(`obj` = 모듈, `name` = `port_declaration`)를 내서 신규 심볼 red가 된다. `monkeypatch.setattr(M, "port_declaration", …)`를 먼저 부르면 pytest가 `obj`·`name` 없는 `AttributeError`를 내서 red로 기록되지 않는다(검토 실측 -- pytest 9.0.2).
   * 래퍼는 `port_declaration`을 정의한 모듈과 `load_topology`가 그 이름을 찾는 모듈의 이름을 **둘 다** 바꾼다(Phase 3 뒤 두 모듈이 다르면 `from … import` 별칭이 생긴다).
   * SR(사이징 모듈)은 `port_declaration`을 import하지 않는다. 선언은 `meta["ports"]`로만 받는다.
9. **동작 보존(auditor, base 대조).**
   * E-LIB 9/9: `transistors`가 같다. `meta`는 새 키 `"ports"`(기대값 = 성분 P)와 아래 **삭제 목록의 쌍만** 다르고, 그 쌍의 값은 base에 삭제 목록을 적용한 값과 `==`다. 목록에 없는 차이가 나오면 FAIL이다.
   * SPECS 4회로 θ 평가(`_library_sized_contexts._evaluate_once` 상당)의 metric `float.hex`, `ctx.sized` 해시, 거부 문구가 base와 같다.
   * `run_full_circuit_audit_from_topology` 9/9가 같다(결과 2, 같은 `ValueError` 7. 메시지 안의 경로 문자열은 빼고 비교).
   * `input_referred_offset_pairs` 9/9가 같다. E-INST가 같다.
   * 비교는 `PYTHONHASHSEED`를 고정하거나 계약 3의 정규화 뒤 `==`로 한다.
   * **표를 잰 base**: 아래 삭제 목록과 E3 표는 gate `master` `dd60db6`에서 잰 값이다(v3 재측정, '작성 전 실측' 8. v2의 `7535799` 측정과 항목까지 같다). 착수 시 실제 base(B34·B26-1·Phase 3·CC-4a 병합 뒤)에서 같은 명령으로 다시 재고, 그 base 커밋을 승인 기록에 적는다. 목록이 다르면 card를 멈추고 다시 확인받는다(B26-1 뒤 E2 차동 간선 분기가 이 card로 **처음** 켜진다 -- B26-1의 E-LIB '불변' 측정은 그 분기가 꺼진 상태였다).
   * **판정 단위(Phase 4 design v0.9.5 §6 E11과 같다)**: 회로마다 `load_topology` meta 키 **하나하나**(빼는 키 목록 없음 -- 두 판에서 실제로 나온 키 전부), `transistors`(= 모든 meta 키를 뺀 `e_lib_p3.py` `per_hash.load`), `V1_own_stack`·`V2_kind_stack`(`e_lib_p3.py` `per_hash`). base와 병합본이 다른 (회로, 단위) 쌍의 집합이 **정확히** {아래 `pairs` 8쌍} ∪ {9회로 × `ports`}여야 한다. 남는 쌍·빠진 쌍 모두 FAIL이다.
   * **기대값(삭제 목록 적용 -- 산문 서술이 아니라 아래 데이터 블록이 정본)**. 사람이 선언한 값은 바뀌지 않는다. 바뀌는 것은 자동 채움·review 목록의 **삭제뿐**이다(추가·값 변경 0 -- 재측정에서 삭제가 아닌 변화가 나오면 이 식으로 기대값을 만들 수 없으므로 card를 멈추고 design 개정). 적용 대상 값 = base의 `e_lib_p3.py` 출력 `circuits.<c>.masked.<키>`(정규화 `{"__dict__": [[json 키, 값], …]}`를 일반 dict로 풀어서). 적용 순서:
     1. `field_removed`의 `[회로, 키, 소자, 필드, 옛 값]`마다 그 키의 그 소자 항목에서 그 필드를 지운다. 필드가 없거나 값이 옛 값과 다르면 `INVALID`(기대값 원자료가 base와 맞지 않는다).
     2. `entry_removed`의 `[회로, 키, 소자]`마다 그 소자 항목을 키째 지운다. 1을 적용한 뒤 그 항목이 `{}`가 아니면 `INVALID`. (엔진은 필드가 모두 빠진 소자를 `{}`로 남기지 않고 키째 뺀다 -- 실측. 그래서 1만 적용하면 `{}`가 남아 병합본과 다르다.)
     3. `review_needed_removed`의 `[회로, 항목]`마다 그 회로 `_device_roles_gap_fill_review_needed` 리스트에서 dict 전체가 같은 항목 하나를 지운다(순서 보존). 없으면 `INVALID`.
     4. 목록 밖은 base 값 그대로다. 그래서 같은 키 안의 승인 밖 변화(다른 소자·필드·항목)도 FAIL로 잡힌다.
     * 측정 확인('작성 전 실측' 8): `dd60db6` base에 1~3을 적용한 값이 모의 병합본 값과 3키 × 9회로 모두 `==`(불일치 0, `INVALID` 0).
     * 수: `field_removed` 58(= `device_roles` 29 + `_device_roles_autofilled` 29 -- ngcc 4·4, sf_pushpull 20·20, two_stage_ota_sf 5·5), `entry_removed` 40(sf_pushpull M5~M22 18개·two_stage_ota_sf M6·M8 -- 두 키 각각), `review_needed_removed` 4(nmcnr 2·two_stage_ota 2 -- 12 → 10, 9 → 7).
     * 바뀌지 않는 단위(측정): 9/9 `transistors`·`V1_own_stack`·`V2_kind_stack`, 그리고 `ports` 밖의 나머지 meta 키 전부(`_vertical_stack_id_autofilled`·`_vertical_stack_id_conflicts`·`symmetry` 포함). 모든 meta 키를 뺀 `e_lib_p3.py` 전체 `hash`가 두 판에서 같다(`223cdec9…`).
     * `ports` 쌍의 기대값은 '`ports` 기대값(성분 P)' 문단(아래 '신규 시그니처' 직렬화 모양 + 독립 oracle)이다.

   ```json
   {"list_id": "b37a-deletion-list-v1",
    "base_commit": "dd60db6515b6fe80ab16349835c19aa75d4f292f",
    "pairs": [
     ["ngcc_3stage_ff", "_device_roles_autofilled"],
     ["ngcc_3stage_ff", "device_roles"],
     ["nmcnr_amplifier", "_device_roles_gap_fill_review_needed"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled"],
     ["sf_pushpull_output_opamp", "device_roles"],
     ["two_stage_ota", "_device_roles_gap_fill_review_needed"],
     ["two_stage_ota_sf", "_device_roles_autofilled"],
     ["two_stage_ota_sf", "device_roles"]
    ],
    "field_removed": [
     ["ngcc_3stage_ff", "_device_roles_autofilled", "M1", "headroom_role", "cascode"],
     ["ngcc_3stage_ff", "_device_roles_autofilled", "M4", "headroom_role", "mirror"],
     ["ngcc_3stage_ff", "_device_roles_autofilled", "M6B", "headroom_role", "mirror"],
     ["ngcc_3stage_ff", "_device_roles_autofilled", "M7", "headroom_role", "mirror"],
     ["ngcc_3stage_ff", "device_roles", "M1", "headroom_role", "cascode"],
     ["ngcc_3stage_ff", "device_roles", "M4", "headroom_role", "mirror"],
     ["ngcc_3stage_ff", "device_roles", "M6B", "headroom_role", "mirror"],
     ["ngcc_3stage_ff", "device_roles", "M7", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M1", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M10", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M11", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M12", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M13", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M14", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M15", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M16", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M17", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M18", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M19", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M2", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M20", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M21", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M22", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M5", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M6", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M7", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M8", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M9", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M1", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M10", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M11", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M12", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M13", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M14", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M15", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M16", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M17", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M18", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M19", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M2", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M20", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M21", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M22", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M5", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M6", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M7", "headroom_role", "cascode"],
     ["sf_pushpull_output_opamp", "device_roles", "M8", "headroom_role", "mirror"],
     ["sf_pushpull_output_opamp", "device_roles", "M9", "headroom_role", "mirror"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M1", "headroom_role", "cascode"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M2", "headroom_role", "cascode"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M4", "headroom_role", "mirror"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M6", "headroom_role", "mirror"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M8", "headroom_role", "cascode"],
     ["two_stage_ota_sf", "device_roles", "M1", "headroom_role", "cascode"],
     ["two_stage_ota_sf", "device_roles", "M2", "headroom_role", "cascode"],
     ["two_stage_ota_sf", "device_roles", "M4", "headroom_role", "mirror"],
     ["two_stage_ota_sf", "device_roles", "M6", "headroom_role", "mirror"],
     ["two_stage_ota_sf", "device_roles", "M8", "headroom_role", "cascode"]
    ],
    "entry_removed": [
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M10"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M11"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M12"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M13"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M14"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M15"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M16"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M17"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M18"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M19"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M20"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M21"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M22"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M5"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M6"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M7"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M8"],
     ["sf_pushpull_output_opamp", "_device_roles_autofilled", "M9"],
     ["sf_pushpull_output_opamp", "device_roles", "M10"],
     ["sf_pushpull_output_opamp", "device_roles", "M11"],
     ["sf_pushpull_output_opamp", "device_roles", "M12"],
     ["sf_pushpull_output_opamp", "device_roles", "M13"],
     ["sf_pushpull_output_opamp", "device_roles", "M14"],
     ["sf_pushpull_output_opamp", "device_roles", "M15"],
     ["sf_pushpull_output_opamp", "device_roles", "M16"],
     ["sf_pushpull_output_opamp", "device_roles", "M17"],
     ["sf_pushpull_output_opamp", "device_roles", "M18"],
     ["sf_pushpull_output_opamp", "device_roles", "M19"],
     ["sf_pushpull_output_opamp", "device_roles", "M20"],
     ["sf_pushpull_output_opamp", "device_roles", "M21"],
     ["sf_pushpull_output_opamp", "device_roles", "M22"],
     ["sf_pushpull_output_opamp", "device_roles", "M5"],
     ["sf_pushpull_output_opamp", "device_roles", "M6"],
     ["sf_pushpull_output_opamp", "device_roles", "M7"],
     ["sf_pushpull_output_opamp", "device_roles", "M8"],
     ["sf_pushpull_output_opamp", "device_roles", "M9"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M6"],
     ["two_stage_ota_sf", "_device_roles_autofilled", "M8"],
     ["two_stage_ota_sf", "device_roles", "M6"],
     ["two_stage_ota_sf", "device_roles", "M8"]
    ],
    "review_needed_removed": [
     ["nmcnr_amplifier", {"device": "M201", "note": "compensation.stage_devices 소속 -- gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 막을 필요는 없음)."}],
     ["nmcnr_amplifier", {"device": "M301", "note": "compensation.stage_devices 소속 -- gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 막을 필요는 없음)."}],
     ["two_stage_ota", {"device": "M4", "field_conflicts": {"headroom_role": ["cascode", "mirror"]}, "note": "이미 선언된 값과 제안이 달라 그 필드만 자동 반영하지 않음(다른 무관한 필드는 그대로 제안)"}],
     ["two_stage_ota", {"device": "M6", "note": "compensation.stage_devices 소속 -- gm_id_role 제안은 sizing_recipe.py의 _AUTHORITATIVE_GM_ID_SOURCES 가드(2026-08-14 신설)로 무시되므로 충돌 없이 안전하게 적용된다(사람이 참고용으로만 확인할 것, 자동 반영 자체를 막을 필요는 없음)."}]
    ]
   }
   ```

   기대 차이표(E3 경로, `resolve_stack_layout` 경로 3 -- 선언 vsid가 없는 5회로 중. `dd60db6` 재측정에서 v2 값과 같다):

   | 회로 | base | 병합 상당 |
   |---|---|---|
   | `ngcc_3stage_ff` | `[M0, M1, M2]` 한 그룹 | `[M0]`, `[M1, M2]` |
   | `sf_pushpull_output_opamp` | `[M17, M18]`, `[M19, M20]` | 네 개로 분리. 전체: `[M5,M6]`·`[M7,M8]`·`[M9,M10]`·`[M11,M12]`·`[M15,M16]` + 단독 `M17`~`M22`(계약 5(b)의 기대값 후보) |
   | `two_stage_ota_sf` | `[M8, M9]` | `[M8]`, `[M9]` |
   | `common_gate_amplifier`, `pushpull_follower_buffer` | 같음 | 같음 |

**합성 topology(계약 3·4·5·6·7 공통).** 최상위 키는 `topology_name`, `schema_version`, `netlist`, `supply_nets: ["vdd","gnd"]`, `symmetry: {"matching_pairs": [], "dispositions": []}`, `ports`다(B26-1 뒤에는 `supply_nets`가 필수다).
기본형 `ports`는 role만 쓴다(**`direction` 없음** -- MG2가 `direction`을 거부로 바꿔도 이 card의 test 픽스처를 고치지 않게): `{<in_p>: {"role": "differential_input_p"}, <in_n>: {"role": "differential_input_n"}, <out>: {"role": "single_ended_output"}}`.
`direction`은 그것을 보는 케이스에만 넣는다: 계약 1의 '있어도 결과가 같다', 계약 6의 모순 2종과 '일치' 수용, 계약 7의 '있든 없든'. (이 케이스들은 MG2가 고친다 -- MG2 몫으로 적어 둔다.)
* **2단 OTA**(`out` = `out`): M1 nmos g=`<in_p>` d=`x` s=`tail` / M2 nmos g=`<in_n>` d=`out` s=`tail` / M3 pmos g=`x` d=`x` s=`vdd` / M4 pmos g=`x` d=`out` s=`vdd` / M5 nmos g=`nb` d=`tail` s=`gnd`.
* **`tele`**(`out` = `o2`): M0 nmos g=`nb` d=`t` s=`gnd` / M1 nmos g=`<in_p>` d=`x` s=`t` / M2 nmos g=`<in_n>` d=`y` s=`t` / M3 nmos g=`nc` d=`o1` s=`x` / M4 nmos g=`nc` d=`o2` s=`y` / M5 pmos g=`o1` d=`o1` s=`vdd` / M6 pmos g=`o1` d=`o2` s=`vdd`.
* 계약 3·5에서 base의 결과와 병합 상당의 자동 채움 값(예: 병합 상당에서 입력쌍 `headroom_role`이 없음)은 **관찰값이지 기대값이 아니다**. test는 변형 사이의 같음만 판정한다(B26-1 검토 S4와 같은 원칙).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `PortDeclaration` | `@dataclass(frozen=True) class PortDeclaration: inputs: tuple; outputs: tuple` |
| `stick_diagram` | `port_declaration` | `def port_declaration(topology: dict) -> PortDeclaration:` |

(모듈 칸은 7535799 기준이다. Phase 3 병합 뒤에는 `rail_declaration`이 있는 모듈로 바꾼다. 바뀌는 기존 시그니처 하나: `resolve_stack_layout(transistors, matching_pairs, device_roles, stack_groups_override=None, *, rails, ports) -> dict`(B26-1의 `rails` 뒤에 `ports`). 지우는 def는 없다.)

**`meta["ports"]` 직렬화 모양(고정 -- v3, Phase 4 design v0.9.5 §5.4 #47 조건 (가). 이 절은 interface card에 그대로 실린다).**
* 값의 형: `PortDeclaration`(위 표의 frozen dataclass). 필드는 정확히 `inputs`·`outputs` 두 개이고 이 순서다. 다른 필드·기본값·`__post_init__` 변환은 없다.
* 필드 값: `tuple[str, ...]`. 원소는 `ports`의 넷 이름(키) 그대로(대소문자·표기를 바꾸지 않는다), Python 기본 `sorted`(코드 포인트 순) 오름차순, 중복 없음. 해당 role이 없으면 빈 tuple `()`.
* `e_lib_p3.py`(Phase 3 D-28) 정규화 결과는 정확히 `{"__dc__": "PortDeclaration", "inputs": [<넷>…], "outputs": [<넷>…]}`이다(키 셋, 그 밖의 키 없음). `ports: {}`이면 `{"__dc__": "PortDeclaration", "inputs": [], "outputs": []}`.
* 이 모양을 바꾸는 구현(필드 추가, list·frozenset 사용, 정렬 규칙 변경, 클래스 이름 변경)은 Phase 4 E11 성분 P 판정과 어긋나므로 design 개정 대상이다. code-author는 이 모양을 지킨다.

**`ports` 기대값(성분 P -- 독립 oracle, 피검 함수를 부르지 않는다).** 회로 c의 기대값은 판정 쪽(test·auditor)이 c의 library `<c>.topology.json`(`git show <판>:<경로>`, 엔진 import 없음)의 `ports`에서 `_` 접두 키를 빼고, 계약 1 role 표(6어휘)로 `inputs`/`outputs`에 나눠 각각 `sorted`해서 만든다. role 표 = `single_ended_input`·`differential_input_p`·`differential_input_n` → `inputs`, `single_ended_output`·`differential_output_p`·`differential_output_n` → `outputs`. 판(커밋)은 Phase 4 design §6 겹침 우선 규칙대로 c를 바꾼 topology 변경 card가 없으면 base(`P3D`), 있으면 마지막 그 card의 승인 커밋이다. `port_declaration`의 출력이나 card의 측정값을 기대값 출처로 쓰지 않는다(작성자=검증자 순환).
* 측정 확인('작성 전 실측' 8, `dd60db6`): 이 oracle 9/9가 모의 병합본 `e_lib_p3.py` `masked.ports`와 같다 -- common_gate `["vin"]`/`["vout"]`, current_reuse `["Vim","Vip"]`/`["Vom","Vop"]`, folded `["vin_n","vin_p"]`/`["out"]`, ngcc `["Vinn","Vinp"]`/`["Vout"]`, nmcnr `["Vin_n","Vin_p"]`/`["Vout"]`, pushpull `["vin"]`/`["vout"]`, sf_pushpull `["vin_n","vin_p"]`/`["vout"]`, two_stage_ota `["vin_n","vin_p"]`/`["OUT"]`, two_stage_ota_sf `["vin_n","vin_p"]`/`["vout"]`. base 값은 9/9 `"<ABSENT>"`.

## 판정 유형 근거

red-green. 모의 head(`7535799` + 범위 1~4 v2, B26-1 전이라 레일은 raw `supply_nets`로 대역, CC-4a 전이라 거부 예외는 `ValueError`로 대역)에서 실측했다('작성 전 실측' 1(b)(c)).
* **base red(계약별)**:
  * 계약 1: 신규 심볼(`M.port_declaration`·`M.PortDeclaration` 접근) `AttributeError`/`ImportError` -- 허용.
  * 계약 2: `assert "ports" in meta` → `AssertionError`.
  * 계약 3: library 판 3/9 + 합성 판(두 topology 모두 네 변형이 세 결과로 갈림) → `AssertionError`.
  * 계약 4: `{M3: S1, M5: S1}` → `AssertionError`.
  * 계약 6: 접근자 거부 9가지 + `load_topology` 거부 2가지(존재·레일) + 연결 파일 2가지를 base는 전부 받아들인다 → `pytest.raises` DID NOT RAISE = `Failed`. 접근자 직접 호출 판은 신규 심볼 red.
  * 계약 7: `direction` 없는 합성 `[]` → `AssertionError`. (`ports: {}` + offset 쌍 거부는 base도 `ValueError`를 내므로 red가 아니다. `ports: {}` + offset 쌍 없음 `[]`는 base `ValueError`라 base 실패지만 허용 밖 예외라 red로 세지 않는다.)
  * 계약 8: 첫 줄 `orig = M.port_declaration` → 인터프리터 `AttributeError`(실측: `obj` 있음, `name == "port_declaration"`) → 신규 심볼 red.
* **계약 5에는 독립된 base red가 없다.** 같은 입력을 base 시그니처로 부르면 네 변형이 실제로 다르지만(관찰), head 시그니처의 같은 test는 base에서 `meta["ports"]` `KeyError` 또는 `ports=` `TypeError`(허용 밖)다. `assert "ports" in meta`를 앞에 두면 계약 2의 red를 빌려 쓰는 것이다.
  그래서 정직하게 나눠 적는다: **계약 5의 base red는 계약 2 몫이다. E3 배선의 증거는 계약 9의 E3 차이표(auditor, base 대조)와 호출 그래프(`_build_theta_evaluator` → `resolve_stack_layout(…, ports=meta["ports"])`)다.** 판정 기록도 두 종류(red 증거 / 차이표·호출 그래프 증거)를 나눠 적는다(B26-1 방식). 계약 5 test((a)·(b))는 head에서 green인 계약 test로 둔다((b)도 base에서는 `ports=` `TypeError`라 red가 아니다).
* 계약 9는 base에서도 green이다(보존). 삭제 목록·E3 표의 차이는 의도한 변화다.
* E-LIB가 의도적으로 바뀌는 card다. 그래서 동작 보존은 '표에 있는 필드만 다름'으로 판정한다(DF-36의 `topology_ref`와 같은 방식).
* **기존 test 기대값 변경 0**(재측정, '작성 전 실측' 7): 새로 실패하는 기존 test 17곳은 입력 픽스처 보강(정직한 넷 선언 -- 신호 입력이 없는 합성 픽스처는 `ports: {}`)과 `test_s013` 두 호출의 `ports=` 추가만으로 모두 통과한다. assert·기대값·메시지 문자열은 바꾸지 않는다. 따라서 기준 약화(DEC-40·V5)가 아니다. (v1의 '입력 role 0개 거부'를 유지했다면 신호 입력이 없는 픽스처에 거짓 입력을 선언해야 했고, 실제 넷을 고르면 s040·s041의 판정이 바뀌었다 -- 검토 B2. 그 규칙은 v2에서 뺐다.)

## oracle 종류와 출처

* 계약 1·2: (a) 구성. 기대 입출력은 test가 topology JSON의 `ports`와 role 표 6행으로 만든다(피검 출력으로 만들지 않는다). 계약 2의 `meta["ports"] == M.port_declaration(…)`은 배선 관찰일 뿐 기대값 출처가 아니다(v3).
* `meta["ports"]`의 E-LIB(Phase 4 E11 성분 P): (a) 구성 -- '신규 시그니처'의 '`ports` 기대값' 문단(library `ports` 선언 `git show` + role 표, 엔진 import 없음)과 직렬화 모양 고정.
* 계약 3·5: (b) 변환 불변(이름 바꾸기). 기대값은 '같은 회로 다른 이름'의 같음이다. 바꿀 넷 집합은 topology JSON만으로 정한다(library: 레일 밖 전부, 합성: 포트 넷) -- 피검 구현의 이름 규칙(`netclass.HINT_*`)을 import하지 않는다.
* 계약 4: (a) 구성(차동 다리 규칙 + 2단자 직렬 사슬, 위 근거).
* 계약 6: (a) 구성(거부·수용해야 할 입력을 test가 만든다).
* 계약 7: (a) 구성(합성 쌍의 게이트가 입력 role 넷)과 library 반환값 (c)(base 실행 결과 -- 위에 적은 값은 base 실측값이다).
* 계약 8: (c) 기존 구조(캐시가 첫 호출에 `load_topology`를 한 번 더 부른다) + (a) 이후 증가 0.
* 계약 9: (c) base 실행 결과(auditor) + **승인 기록(UD-18 Q1) 본문의 항목 단위 삭제 목록**(계약 9 데이터 블록과 같은 내용 -- 착수 시 재측정 판). 기대값 = base 값에 그 목록을 적용한 값. card의 모의 병합본 측정값은 출처가 아니다(작성 쪽 시제품 -- Phase 4 design v0.9.5 §6 D47 행).

## 거부해야 할 입력

계약 6의 거부 목록 전부. `load_topology`는 접근자 형식 검사를 netlist 해석보다 먼저 하고, 존재·레일 겹침 검사는 연결 파일까지 합친 netlist를 만든 뒤 문법 호출 전에 한다.
`_TEMPLATE.topology.json`은 base `AttributeError`(netlist 원소가 설명 문자열) → 병합본 `ports` 거부로 예외 종류가 바뀐다(`ports` 키가 없다). E-LIB 대상 밖이라 판정 영향은 없다.
판정기 자기 점검은 계약 6 끝. 계약 7의 '입력 0 + offset 쌍' 거부.

## library 회로 적용 여부

적용한다. library 9회로 전부 `ports`를 가진다(role 6개 어휘 안, `direction`과 role 9/9 모순 없음, 포트 넷 9/9 netlist·수동소자·이상원 단자에 있음, 레일과 겹침 0, 9/9 입력 role ≥ 1 -- v2 재측정). 계약 1·2·3·7·9 대상이다.
SPECS 4회로는 선언 vsid가 있어 E3 경로 3을 타지 않는다. E3 차이는 SPECS 밖 3회로에서만 난다.

## 무동작 판정 입력(무발동 값)

* `common_gate_amplifier`·`current_reuse_telescopic_ota`·`folded_cascode`·`pushpull_follower_buffer`의 `load_topology` meta(`"ports"` 제외)가 base와 같다.
* SPECS 4회로 평가와 audit 9/9, `input_referred_offset_pairs` 9/9가 base와 같다.
* E3 경로 3 5회로 중 `common_gate_amplifier`·`pushpull_follower_buffer`가 base와 같다.
* 존재·레일 겹침·입력 0 + offset 쌍 거부는 library 9회로에서 발동하지 않는다.

## 재현할 수치

없음(수치 산출물 변화 없음 -- SPECS 4회로 metric `float.hex` 동일, '작성 전 실측' 1(c)).

## V3 계획

**규칙: 승인된 A1(2026-10-01, `_drafts/user_decisions.md`).** A1-a = 면제 누수 수정 게이트 `20260930-v3-exempt-binding`(면제 = `변이 id@함수 원본 해시`, 해시가 같을 때만 적용). A1-b = ② N2 범위 정책 `20260930-v3-changed-stmt-scope`(대상 = 바뀐 문장 + 감싸는 제어문 + 삭제 지점 바로 뒤 문장 + 바뀐 매개변수를 읽는 문장 + 새 def 전체 + 바뀐 기존 def의 `early_return` 항상).
이 card는 두 게이트 card가 병합된 뒤 착수한다('결정 필요 항목'의 착수 조건). 그 전에는 V3가 def 전체(아래 '지금 규칙' 열)라 이 card 범위 밖의 기존 문장이 병합 조건이 된다.

1. **대상 수(모의 head v2, `7535799` 기준. 도구 `mutate_changed.changed_defs`·`mutants`·`inventory` + 범위 정책 card 계약 1 구현 `_drafts/v3_scripts/v3_scope_classify.py`의 `classify`를 그대로 썼다)**. 변이 수는 접근자·검사 문장의 구현 모양에 따라 달라진다(모의 구현 기준 근삿값). 착수 시 auditor가 도구 출력 `targets_by_def`로 다시 잰다.

   | def | 지금 규칙(def 전체) | **N2 대상** | 인벤토리(기존) | N2 대상의 출처 |
   |---|---|---|---|---|
   | `stick_diagram.port_declaration`(새) | 27 | **27** | 137 | 새 def 전체 |
   | `stick_diagram.load_topology` | 77 | **27** | 137 | 새 문장 13개(접근자 호출·`all_passive`·존재·레일 검사·두 호출·meta), 감싸는 `for rel_path in linked:`(`stmt_delete` -- 머리에 변이 연산자 없음), 삭제 지점 뒤 3문장, `early_return` |
   | `sizing_recipe.input_referred_offset_pairs` | 22 | **16** | 60 | 새 문장 3·머리 변경 1, 감싸는 `if "input_offset_pairs" not in entry:`(`stmt_delete`·`cmp_flip`), 삭제 지점 뒤 문장(쌍 판정 `if all(…)`), `early_return` |
   | `sizing_recipe._load_full_topology_cached` | 10 | **4** | 63 | 바뀐 dict 문장, 감싸는 `if topology_path not in cache:`(`stmt_delete`·`cmp_flip`), `early_return` |
   | `sizing_recipe.resolve_stack_layout` | 26 | **4** | 61 | 경로 3 호출 문장(새 문장 + `ports`를 읽는 문장), 삭제 지점 뒤 `if refined is not None and …`(`stmt_delete`·`cmp_flip`), `early_return` |
   | `sizing_recipe._build_theta_evaluator` | **497** | **3** | 60 | `resolve_stack_layout(…)` 호출 문장, 바로 뒤 `stack_id_of = …`, `early_return` |
   | 합 | 659 | **81** | | |

   * v1의 '바뀐 줄에 걸친 변이 35개'는 줄 diff 근사였다. N2는 감싸는 복합문(위 `for`·`if` 3개)과 삭제 지점 바로 뒤 문장, `early_return`을 더하고, v2 범위(존재·레일·입력 0 + offset 쌍 검사)가 새 문장을 더한다.
   * **모의 판정 결과**('작성 전 실측' 1(e)): N2 대상 81개 중 v2 계약(모의)으로 죽음 **79**. 남은 2개는 `resolve_stack_layout`의 삭제 지점 뒤 문장 `if refined is not None and refined.get(…):`의 변이다.
     * `cmp_flip`(`is not None` → `is None`)은 기존 test `test_s003`이 죽인다(전체 test 실행 실측 -- netlist가 빈 픽스처에서 `refined`가 `None`이라 `.get` `AttributeError`).
     * `stmt_delete`(경로 3 분기 통째 삭제 → 항상 레거시 폴백)는 v2 계약 (a)와 **기존 test 전체**로 죽지 않는다(실측). 경로 3과 레거시가 갈리는 입력이 library `sf_pushpull_output_opamp` 하나뿐이고 그 값을 단언하는 test가 없기 때문이다. 이 변이는 등가가 아니다. 계약 5(b)가 죽인다(그 사본에서 sf_pushpull 결과가 `[[M1, M2]]` 하나만 묶음으로 바뀜 -- 실측). 계약 5(b)는 승인 기록 값을 기대값으로 고정하므로 Q3 답에 달렸다.
   * 계약을 v2에서 더한 것 중 4개는 이 측정의 생존 변이에서 나왔다: 계약 4의 `device_roles` 반영(vsid 반영 루프 삭제), 계약 6의 수동소자·이상원·연결 파일 수동소자 단자 수용(존재 검사 범위 문장 2개 삭제), 계약 7의 이름 1개 offset 항목(`len(names) >= 2` 상수 변이). 넷 다 v2 계약으로 죽는다(재실측).
   * auditor는 착수 시 실제 도구(N2 판)로 대상과 생존을 다시 잰다. 모의 판정은 'contracts 출력이 head와 달라지면 죽음'이라는 근사다(실제 test가 그 차이를 단언하는지는 test-author 몫).
2. **면제 묶기(A1-a)의 효과.** 면제 원소는 `<id>@<묶기 해시>`라서 def가 바뀌면 풀린다. `load_topology`·`resolve_stack_layout`·`_build_theta_evaluator`는 B26-1도 바꾸는 def다.
   * B26-1이 이 def들에서 받은 면제는 B37a에서 **승계되지 않는다**. N2에서는 B37a의 대상이 B37a가 바꾼 문장 주변뿐이므로, B26-1 면제 대상(B26-1이 바꾼 문장 주변)과 겹치는 것은 두 card가 같은 문장을 건드릴 때뿐이다 -- 겹칠 수 있는 곳: 각 def의 `early_return`(N2가 바뀐 기존 def마다 항상 대상), `load_topology`·`resolve_stack_layout`의 E1·E2·경로 3 호출 문장(B26-1이 `rails=`를 넣은 바로 그 문장).
   * 그 변이가 이 card의 계약·기존 test로 죽으면 면제가 필요 없다. 죽지 않는 변이가 있으면 B37a용 면제(해시 묶음, 사용자 승인 -- 새 결정)나 test 보강이 필요하다. 이 경우만 '새 결정'이 생긴다.
3. **test 모양**: 본문 직접 호출이면 각 def 인벤토리가 +1이다. parametrize 이름 문자열 + `getattr`이면 +0이다(v1 실측). 계약 절 'test 모양'에 적었다.
4. 승인 기록 면제 id와 겹침 0(HEAD `.ai/approvals`, v1 측정).
5. 인벤토리 기준 실행이 실패하면 ERROR다(B28). selftest 17곳의 픽스처 보강('작성 전 실측' 7)이 test 커밋에 없으면 기준 실행이 실패한다. 순서 3 freeze 뒤 auditor가 base·head 인벤토리 기준 실행을 확인한다.
   기준 실행 주의: 픽스처 보강을 넣은 test 파일을 base 코드로 돌리면 `test_s013`이 `meta["ports"]` `KeyError`로 실패한다(실측). base 기준 실행이 그 test를 포함하면 이 실패는 'base 시그니처에 없는 키워드·키' 몫이다(B26-1의 `rails=` 보강과 같은 구조).

## 결정 필요 항목

1. **승인 기록(사용자 결정 기록 필요) -- `approval: 20260930-b37a-ports-roles`(`target_kind: decision`).** 질문 문안·기록 초안: `_drafts/draft_b37a_approval_question.md`.
   이 card는 **동작을 바꾼다**. library 3회로의 자동 채움 `headroom_role`이 사라지고, 2회로의 review 목록이 줄고, 3회로의 레이아웃 1차 그룹이 바뀐다.
   design 20 승인(`20260923-20-dead-code-dup-design`)은 '동작이 바뀌는 수정'을 덮지 않는다(review_b34 B1, review_b26_1 S3과 같은 결함을 반복하지 않는다). 그래서 사용자 원문이 있는 decision 기록 한 건이 card 커밋 전에 gate에 있어야 한다.
   사용자에게 묻는 것(셋 다 **승인 사안**이다 -- 동작 변경 + 선언 근거 확인 + 승인된 값의 test 고정):
   * **(Q1) 동작 변경 수용.** 계약 9의 **항목 단위 삭제 목록**(데이터 블록 -- `field_removed` 58·`entry_removed` 40·`review_needed_removed` 4, E-LIB 5회로 8쌍)과 E3 표(3회로)를 기록 **본문에 그대로** 싣는다('N개 사라짐'·'12 → 10' 같은 산문은 기록의 출처가 될 수 없다 -- Phase 4 design v0.9.5 §6 D47). 사용자는 이 목록을 승인한다.
     * 근거 문장(원칙으로 말할 수 있는 것만): "사라지는 값은 이름 정규식이 입력을 BIAS로 분류한 **유도**에서 나왔다. 그 유도는 넷 이름에 의존하므로 무효다. 그래서 자동 채움을 비운다."
     * 값 하나하나의 옳고 그름(예: 사람이 선언한 4회로의 입력쌍 `headroom_role`이 `cascode`라 세 회로 입력쌍의 base `cascode`는 사람 관례와 같은 값이었다)과, 세 회로의 `headroom_role`·수직 그룹을 무엇으로 볼지는 회로 해석이다. 6a(DEC-35 ports·역할 제안표, J ratify)에서 공동분석한다. 이 기록은 그 판단을 하지 않는다.
     * 세 회로 모두 SPECS 밖이라 지금 평가 수치는 그대로다(실측).
   * **(Q2) 이 card의 입력으로 쓰는 `ports` 선언 확인.** B37a 뒤 회로의 자동 채움·레이아웃 1차 그룹은 `ports`로 정해진다. 동작이 바뀌는 3회로(ngcc·sf_pushpull·two_stage_ota_sf)와 주석 없는 pushpull, 목적 설명만 있는 common_gate의 `ports`를 사용자에게 확인받는다. 회로별 근거(파일 주석·추가 커밋)는 질문 파일의 Q2 표다.
     * 실측: 파일 안 '사용자 확정'은 folded_cascode·nmcnr_amplifier, '사용자 확인'은 current_reuse, two_stage_ota는 입력은 목적 설명·출력 `OUT`은 '사용자 확정'. ngcc(`5459a44`)·sf_pushpull(`4ea001f`)·two_stage_ota_sf/pushpull(`ad85c2c`)·common_gate(`31f9ad1`)는 추가 커밋 메시지에 "사용자 확정 넷 표"(common_gate는 "판독한 넷 표를 사용자가 확정")가 있으나 그 표에 `ports` role이 들어 있었는지는 메시지만으로 확인되지 않는다.
     * 틀린 회로가 있으면 그 회로의 `ports`를 먼저 고친다(library 데이터 -- 사용자 수정). 그 뒤 삭제 목록을 다시 잰다.
   * **(Q3) sf_pushpull E3 결과를 계약 test 기대값으로 고정하는가.** N2 대상 변이 하나(경로 3 분기 삭제)는 sf_pushpull 값을 단언해야만 죽는다('V3 계획' 1). 기본안: 고정한다(계약 5(b) -- '승인된 동작'의 고정이지 '맞는 값' 판정이 아니다. 6a에서 바뀌면 그때 V5·DEC-40 승인). 대안: 고정하지 않고 그 변이를 해시 묶음 면제(비등가 변이라 약화, 사용자 승인).
   * **원칙 기본안(기록에 적기만 한다)**:
     * `ports` 키 없음·`null`·dict 아님·항목 형식 오류·빈 넷 이름·`direction`과 role 모순은 거부한다. 명시적 `ports: {}`(입력·출력 0)는 받는다(B26-1 `supply_nets: []` 선례).
     * 포트 넷이 netlist에 없거나 레일이면 거부한다.
     * `input_referred_offset_pairs`는 offset 쌍이 있는데 입력이 0이면 거부한다(지금 거부의 취지 유지).
     * 연결 파일 `ports`는 진입 파일과 같아야 한다(B26-1 `supply_nets`와 같은 규칙). 출력 role 0개는 받는다.
     * role 어휘 6개를 닫힌 표로 둔다. N3.16 786행에 어휘를 적는 개정은 판정 표 해시 입력 밖이다(`merge_gate.plan_tables_object` = N4.1·N4.2·N6.1 Phase 열·쓰기 경로표). 그래서 오케스트레이터 문서 커밋으로 한다. 착수 때 개정 전후 `plan_tables_hash`가 같은지 확인한다.
     * 순서: B34(#45) → B26-1(#1) → (Phase 3) → CC-4a(#6) → B37a. 세 card 모두 `load_topology`를 바꾼다(B34는 import 실패 처리, B26-1은 `meta["rails"]`·`resolve_stack_layout(*, rails)`, CC-4a는 `SchemaRejectedError`). B26-2(#17)와는 어느 쪽이 먼저여도 되지만 동시 착수는 하지 않는다(같은 def `_build_theta_evaluator`). Phase 4 design 초안의 `B26-2 ─> B37` 화살표는 B37a에는 필요 없다(극성을 쓰지 않는다).
   * **기록에 넣지 않는 것**: '출력은 포트만'(v1 확인 2). B37b card의 결정 항목이다('범위 밖' B37b).
2. **V3 처리**: 승인된 A1(N2 + 면제 묶기)을 따른다(위 'V3 계획'). 그 자체로는 새 결정이 아니다. **단 N2 대상 중 계약·기존 test로 죽지 않는 변이가 남으면** 그 변이의 면제(해시 묶음)는 사용자 승인 항목이 된다(B26-1 면제는 해시가 바뀌어 승계되지 않는다 -- 'V3 계획' 2).
   모의 측정에서 그런 변이는 하나였고(경로 3 분기 삭제), Q3로 올린다. 착수 시 실제 도구로 더 나오면 오케스트레이터가 freeze 전에 사용자에게 올린다.
3. 대기 중인 결정 UD-15(analog-grammar 소속)는 B37b의 선행 조건이지만 이 card와는 무관하다.

착수 조건:
1. 승인 기록 `20260930-b37a-ports-roles`(Q1·Q2·Q3 답 포함)이 gate에 있다. **그 본문에 계약 9 데이터 블록 형식의 항목 단위 삭제 목록과 그 목록을 잰 base 커밋이 있다**(Phase 4 design v0.9.5 §5.4 #47 조건 (나) -- 없으면 이 card를 커밋하지 않는다).
2. B34·B26-1·(Phase 3)·CC-4a 병합.
3. V3 게이트 card `20260930-v3-exempt-binding`·`20260930-v3-changed-stmt-scope` 병합(A1 승인 -- 승인 기록은 각 card 몫).
4. 착수 시 재측정('작성 전 실측' 1(a)(b)(c)(e)·7·8)이 이 card·승인 기록의 목록·표와 같다. 다르면 멈추고 다시 확인받는다.
5. **Phase 4 design v0.9.5 조건(§5.4 #47 '작성 전 조건', §6 E11 P·D47)**:
   * (가) interface card에 `meta["ports"]` 직렬화 모양이 고정돼 있다 -- '신규 시그니처' 절의 직렬화 모양 문단이 `interface_card.py` 출력에 그대로 실린다(그 절을 옮기므로 별도 작업 없음). 구현이 다른 모양이면 design 개정.
   * (나) 재측정은 `load_topology` meta를 **키 단위**로 잰다(빼는 키 없이 두 판의 키 전부 -- `e_lib_p3.py <root> <out> <두 판 키 합집합 전부>`), `per_hash.load`·`V1_own_stack`·`V2_kind_stack`도 함께. (회로, 단위) 쌍 집합이 계약 9 `pairs` 8쌍 ∪ 9회로 × `ports`와 다르면 card를 멈추고 E11 표를 고치는 design 개정. 같고 항목만 다르면 card 규칙대로 사용자에게 다시 확인받는다(승인 기록의 목록을 새 판 목록으로).
   * (나') 재측정 차이에 삭제가 아닌 변화(값 추가·변경)가 있으면 삭제 목록 식으로 기대값을 만들 수 없다 -- design 개정.
   * (다) `ports` 기대값은 독립 oracle(library `ports` 선언 + 계약 1 role 표)로 만든다. 피검 `port_declaration` 호출이나 card 측정값을 쓰지 않는다.
   * (라) **design 정정 요청(오케스트레이터, 이 card 밖)**: design v0.9.5 §6 D47 행의 적용 규칙은 '`device_roles`는 (소자, 필드, 옛 값)마다 필드를 지운다, `_device_roles_autofilled`·`_device_roles_gap_fill_review_needed`는 목록의 항목을 지운다'이다. 실측으로는 (i) 필드가 모두 빠진 소자 항목은 엔진이 키째 뺀다(sf_pushpull 18·two_stage_ota_sf 2, 두 키 각각) -- 필드 삭제만 적용하면 `{}`가 남아 (v)가 FAIL한다 (ii) `_device_roles_autofilled`의 '항목'은 `device_roles`와 같은 (소자, 필드, 옛 값) 단위다(M1·M2 등은 `L_role`·`gm_id_role`이 남는다). 그래서 D47 적용 규칙에 계약 9의 2단계(`entry_removed`, 비어 있어야 함)와 `_device_roles_autofilled`의 필드 단위를 넣어야 한다. 이 정정 전에는 card를 커밋하지 않는다.

## 작성 전 실측

(v2 재측정: gate `master` `7535799`(엔진 소스 = v1 측정과 같은 커밋). 저장소 쓰기와 상태 변경 git은 없었다(`git archive`·`git log`·`git show`만). 끝난 뒤 `git status`는 시작과 같다.
* scratch `C:/g68`에 `git archive 7535799` 사본 `base`, 모의 `head`(= `base` + 범위 1~4 v2, `make_head.py`), 픽스처 보강 사본 `head_fx`·`base_fx`(`make_fx.py`)를 만들었다. 문자열 치환은 대상이 정확한 횟수로 나오는지 assert로 확인했다. 측정 스크립트마다 import한 모듈 경로가 해당 사본 아래인지 assert로 확인했다.
* 모의 head 대역: B26-1 전이라 레일 겹침은 raw `supply_nets`로, CC-4a 전이라 거부 예외는 `ValueError`로 대신했다.
* 게이트 함수(`mutate_changed`·`reachability`)는 사본 `tools/gates`에서 읽기 전용으로 import했다(`main` 실행 안 함). `$PY` = `C:/Python314/python.exe -B`, `PYTHONHASHSEED=0`.
* 스크립트 사본: `wt/_drafts/b37a_scripts/`(`make_head.py`·`make_fx.py`·`contracts.py`·`measure.py`·`compare.py`·`v3_b37a.py`·`mutrun.py`·`mkmut.py`·`run_pt.py`·`lib_ports.py`·`probe_path3.py`·`contracts_syn.py`·`check_header.py`, 출력 사본 `out/`). 측정 뒤 `C:/g68`을 삭제했다. 수치는 이 절에 옮겼다.
* 착수 시점(B34·B26-1·Phase 3·CC-4a 병합 뒤)에 오케스트레이터가 1(a)(b)(c)(e)·7을 같은 명령으로 다시 재고, 표를 잰 base 커밋을 승인 기록에 적는다. 줄 번호, 모듈 이름, 변이 수, `resolve_stack_layout` 시그니처(`rails` 포함)가 바뀐다.)

1. **사실 문장 재측정.**
   * (a) 줄·소비자(v1 측정, 검토 재확인. 3292 → **3293** 정정 -- 3292는 `if kind == "internal_series"]`).
     * SD `load_topology` 8550, E2 호출 8643~8644, E1 호출 8668~8671, `propose_vertical_stack_id_gap_fill` def 3261·`if inputs or …` 3293·docstring 3282, `propose_device_roles_gap_fill` def 3845·docstring 3855, NC `HINT_*` 39~43·사용 118~121·148, NC 1c 113~124.
     * SR: `input_referred_offset_pairs` 4481·`ports` 읽기 4511~4519, `_load_full_topology_cached` 4806·raw `"ports"` 4833, `resolve_stack_layout` 6470·경로 3 6572·docstring 6537~6543, `_build_theta_evaluator` 7930·호출 8060~8062.
     * `ports`·`direction` 소비자는 SR 4511·4519·4833뿐(`*.py`). 운영 `resolve_stack_layout` 호출자는 SR 8060 하나, test 호출은 `test_s013` 2곳. `input_referred_offset_pairs` 호출자는 SR 4552·4588.
     * library `ports`(`lib_ports.py`): 9/9 있음, role 6어휘 안, `direction`과 role 모순 0, 포트 넷 9/9 단자에 있음, 레일 겹침 0, 9/9 입력 role ≥ 1, `linked_topology_files` 비어 있음 9/9. `_TEMPLATE`에는 `ports` 키가 없다.
     * `ports._comment`(UTF-8로 읽음): '사용자 확정' folded_cascode·nmcnr_amplifier, '사용자 확인' current_reuse, two_stage_ota는 입력 목적 설명 + 출력 `OUT` '사용자 확정', common_gate는 목적 설명, 주석 없음 ngcc·pushpull·sf_pushpull·two_stage_ota_sf. `git log -S'"ports"'`: ngcc `5459a44`, sf_pushpull `4ea001f`, two_stage_ota_sf·pushpull `ad85c2c`, common_gate `31f9ad1`(메시지 인용은 질문 파일 Q2 표).
   * (b) 계약 실측(`contracts.py`, base/head 각각 새 프로세스):
     * 계약 3 library 판(레일 밖 넷 전부, 회로당 5~35넷): base 6/9(current_reuse 8소자·ngcc 5·pushpull 4의 `device_roles`·`_device_roles_autofilled`), head **9/9**.
     * 계약 3 합성 판(포트 넷만): 2단 OTA·`tele` 모두 base는 네 변형이 세 결과, head는 하나.
     * B1 반례(계약 아님): `tele`의 `nc` → `in2`는 base·head 모두 다름(`device_roles`·`_device_roles_autofilled`).
     * 계약 4: base `{M3: S1, M5: S1}`(`device_roles`의 `S1` = M1·M3·M5), head `{M2, M3, M4, M5, M6: S1}`(`device_roles`의 `S1` = M1~M6, M0 없음. 두 이름 변형 같음).
     * 계약 5: base는 `meta["ports"]` `KeyError`. base 시그니처 관찰: `sig_a`·`vin_p`·`Vinp` 판 `[[M0,M1,M2],[M3],[M4],[M5],[M6]]`, `Vip` 판 전부 단독. head는 네 변형 전부 단독.
     * 계약 6: base는 단일 파일 11가지(접근자 거부 9 + 존재·레일 2)와 연결 파일 2가지를 전부 받아들인다. head는 13가지 모두 거부(메시지에 `ports`·`DEC-62`). 접근자 직접 호출은 접근자 거부 9가지를 거부하고 존재·레일 2가지는 받는다. 단일 파일 수용 7가지(`{}`·`_comment`만·출력만·입력만·`direction` 일치·수동소자 단자에만·이상원 단자에만)와 연결 파일 수용 3가지(`ports` 없음·같음·연결 파일 수동소자 단자에만)는 head에서 받는다.
     * 계약 7: base `direction` 없음 `[]`·있음 `[["M1","M2"]]`, `ports: {}`는 offset 쌍 유무와 무관하게 `ValueError`. head는 `direction` 유무 모두 `[["M1","M2"]]`, `{}` + offset 쌍 거부, `{}` + offset 쌍 없음 `[]`, 이름 1개 offset 항목은 `{}`·기본 `ports` 모두 `[]`(base는 `{}`이면 `ValueError`, 기본 `ports`이면 `[]`).
     * 계약 8: base 첫 줄 `orig = M.port_declaration` → `AttributeError`(`obj` 있음, `name == "port_declaration"`). head 계수 1 → 2 → 2.
   * (c) 동작 보존(`measure.py <사본> <out> --specs`, `compare.py`, base 커밋 `7535799`):
     * `load_topology` transistors 9/9 같음. meta(`"ports"` 제외)는 기대 차이표 5회로만 다르다(소자·필드까지 표와 일치 -- v1 표 재현).
     * E3 경로 3은 표 3회로만 다르다(ngcc `[M0,M1,M2]` → `[M1,M2]`, sf_pushpull `[M17,M18]`·`[M19,M20]` 분리, two_stage_ota_sf `[M8,M9]` 분리).
     * audit 9/9 같음(결과 2, `_netlist_sections_structured` 없음 `ValueError` 7 -- 경로 문자열만 다름).
     * `input_referred_offset_pairs` 9/9 같음.
     * SPECS 4회로 `_evaluate_once`: current_reuse·folded는 metric(19·5개 `float.hex`)과 sized 해시가 같고, two_stage_ota·nmcnr은 같은 `InfeasibleSizingError` 문구다. 실행 시간 base/head 20.2/19.3 s, 0.2/0.2, 29.5/30.7, 8.6/8.4(병렬 실행이라 v1보다 느림).
   * (d) 접근자 role 대응: head `meta["ports"]` 9/9가 role 표로 만든 기대값과 같다(예: current_reuse `inputs=("Vim","Vip")`, `outputs=("Vom","Vop")`. two_stage_ota `outputs=("OUT",)`).
   * (e) V3(`v3_b37a.py`, `mutrun.py`):
     * `changed_defs(base, head)` → 6 def, 변이 합 659, N2 대상 81('V3 계획' 1 표).
     * 모의 판정: N2 대상 81개를 하나씩 `mutate_changed._replace_def`로 넣고 `contracts.py`와 folded_cascode `_evaluate_once`를 새 프로세스로 돌려 head 출력과 비교했다(출력이 달라지면 죽음 -- 계약 test가 그 차이를 단언한다는 근사).
     * 1차(v2 계약 초안): 죽음 75, 생존 6 -- `load_topology` 3(존재 검사의 수동소자·이상원 합집합 문장, 연결 파일 수동소자 수집 문장, vsid 제안 반영 루프), `input_referred_offset_pairs` 1(`len(names) >= 2` 상수 −1), `resolve_stack_layout` 2(경로 3 분기 `stmt_delete`·`cmp_flip`).
     * 계약 4·6·7에 케이스를 더한 2차: 앞의 4개 죽음. `resolve_stack_layout` 2개 생존.
     * 생존 2개와 vsid 반영 루프 변이를 `head_fx`에 넣고 기존 test 전체를 돌렸다(`mkmut.py` + `run_pt.py`): `cmp_flip`은 `test_s003`이 죽임, vsid 반영 루프 삭제는 `test_s049`·`test_s154`·probe 6건이 죽임, 경로 3 분기 `stmt_delete`는 **생존**(실패 집합이 base와 같음). 이 사본에서 E3 결과가 head와 다른 회로는 `sf_pushpull_output_opamp` 하나(`[[M1, M2]]`만 묶음).
     * 관찰(이 card 범위 밖): sf_pushpull의 경로 3 결과에는 base·head 모두 M1~M4가 어느 그룹에도 없다(`resolve_stack_layout` 반환 그룹이 소자 전체를 덮지 않음). 기존 동작이다. 백로그 후보로 오케스트레이터에 넘긴다.
2. **이름 충돌.**
   * `git grep -n -e port_declaration -e PortDeclaration -e PORT_ROLE_SIDE` → 0건. `ls skills/analog-gmid-design/assets/tests/contracts | grep -i "b37\|port"` → 없음(v1 측정).
   * 새 test `A/tests/contracts/test_b37a_ports_roles.py`를 `grep -rn "glob(" skills/analog-gmid-design/assets/tests/`와 대조했다. `probe_*.py`(ts6)·`*.topology.json`·`*.py` 전수 스캔과 이름 충돌이 없다.
   * 전수 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_ts3_no_print_verdicts`)는 삭제 이름 참조·print 판정 토큰을 본다. 이 card는 def를 지우지 않으므로 해당 없다. `test_ic_markers_match_plan`은 `gmid_ic` 표식만 본다(IC를 켜지 않음).
3. **원칙의 계약화.**
   * 선언이 이긴다 → 계약 1·2·3(library 9 레일 밖 넷 전부 + 합성 2 topology × 4변형)
   * 조용한 폴백 금지·선언은 사실 → 계약 6(거부 13 + 수용 10 + 판정기 자기 점검)·7('입력 0 + offset 쌍' 거부, 이름 1개 항목은 쌍 아님)
   * 만들면 배선 → 계약 3(E1)·4(E2)·5(E3, 운영 호출은 계약 9 차이표 + auditor 호출 그래프)·7(`direction` 소비자 교체)
   * 재계산 금지 → 계약 8
   * MG2 대비 role만 → 계약 1(`direction` 없음 = 같음)·7, 합성 기본형에 `direction` 없음
   * 회로 무관(DEC-62) → 계약 3이 library 9 전부이고, 코드에 넷·회로 이름 리터럴이 없다(모의 head diff 확인 -- 새 문자열 리터럴은 role 6어휘·`input`/`output`·키 이름(`ports`·`role`·`direction`·`terminals`·`supply_nets`·`passive_elements`)·`_` 접두·오류 메시지뿐)
   * 전부 전 범위로 적었다(library 9회로·합성·거부 13입력).
4. **쓰기 경로(N3.12.2).**
   * SD·SR 코드·docstring·주석, 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 311·338행 + 새 행): gmid-code-author.
   * 새 계약 test와 selftest 17곳 픽스처 보강(7): gmid-test-author(`skills/analog-gmid-design/assets/tests/**`). test는 엔진 소스를 읽지 않는다. 필요한 사실(합성 topology 모양·role 표·정규화·`SchemaRejectedError` 경로·픽스처 선언 규칙)은 이 card와 interface card에 적었다.
   * 오케스트레이터 문서 커밋: N3.16 786행 role 어휘, Phase 4 design #47 문구(`direction` 미사용·B37a/b 분할·`B26-2 ─> B37` 화살표 정정), 준비 자료의 `_TEMPLATE` 'null' 정정과 §4.2 C1 불변 범위 문장 정정(B1 -- '포트 넷과 `HINT_INPUT` 넷까지'는 계약이 아니다), `skills/analog-gmid-design/references/analog-grammar-integration.md` §5(147~155행)의 `ports`를 `direction`으로 읽는 설계 예시(`ports = topo["ports"]  # load_topology()가 이미 파싱하는 그 dict`) → 정본 `meta["ports"]`(`PortDeclaration`)로.
   * `_TEMPLATE.topology.json` `ports` 필드: library 데이터(승인 기록 조건)라 이 card 밖이다. 백로그로 둔다.
   * analog-grammar(`skills/analog-grammar/**`): 손대지 않는다(B36).
5. **계획서 소비자.**
   * `git grep -n -e "ports\.direction" -e "B37" -e "HINT_" -- docs/01-plan docs/02-design` → 계획 263행(DEC-69)·803행(MG2)뿐이다. `ports.direction` 삭제는 MG2에 남는다(이 card와 일치).
   * `git grep -n -e input_referred_offset_pairs -e resolve_stack_layout -- docs/01-plan docs/02-design/features` → history 4곳·계획 MOD8 행 설명뿐이다. 이름을 지우거나 옮기지 않으므로 고칠 것이 없다.
   * 계획 314행 GB0("사람 선언을 읽고 검증한다: … `ports` …")는 이 접근자를 재사용해야 한다 -- 레지스트리 새 행 비고(범위 6).
   * 계획서 밖 소비자: `references/analog-grammar-integration.md` §5(위 4).
6. **미배선(V7).**
   * 새 def는 `port_declaration` 하나이고 `load_topology`가 부른다. 운영 루트에서 도달한다(모의 head 그래프 인벤토리 137).
   * 새 클래스 `PortDeclaration`은 접근자의 반환 레코드다.
   * 되살리는 def와 지우는 def는 없다. V7 면제 승인이 필요 없다.
7. **기존 계약 test·기존 test 영향(재측정).**
   * `git grep -n -i -e direction -e '"ports"' -e input_referred_offset_pairs -e resolve_stack_layout -- skills/analog-gmid-design/assets/tests/contracts tools/gates` → `test_d_delete_telescopic.py` 216~220뿐이다. 합성 topology에 이미 `ports`·role·`direction`이 있고 모순이 없다. head pytest에서 PASS다. 조정이 필요한 계약 test는 0이다.
   * pytest(판정 설정): `$PY -m pytest -c <사본>/tools/gates/pytest_gate.ini --rootdir=<사본> --confcutdir=<사본> --gmid-phase=2 -p no:cacheprovider -q -rfE <사본>/skills/analog-gmid-design/assets/tests`(`run_pt.py`).
     * base 2 failed·796 passed·15 xfailed. 2건은 사본에 git 이력이 없어 생기는 `test_ts6_probe_relocate` 두 건이다(gate 실행과 무관. v1·검토의 42 failed와 다른 것은 사본 환경 차이다).
     * head(보강 없음) 15 failed·4 errors·779 passed·15 xfailed. **새로 실패 17, 고쳐진 것 0.** v1의 18에서 `test_s125`가 빠졌다(그 픽스처는 이미 `ports: {}`이고 v2가 이를 받는다).
     * **head_fx(아래 규칙으로 보강) 2 failed·796 passed·15 xfailed -- base와 같은 실패 집합, 새 실패 0.** 보강 diff는 입력 픽스처 18줄뿐이고 assert·기대값·메시지 문자열 변경은 0이다.
     * base_fx(같은 보강을 base 코드로) 3 failed: base의 2건 + `test_s013`(`meta["ports"]` `KeyError` -- base에 없는 키. 'V3 계획' 5).
   * 새 실패 17의 내역: `test_selftest_sizing_recipe.py` 16(s003·s011·s012·s013·s036~s043·s045·s050·s052·s053. 그중 s039·s041·s050·s053은 setup ERROR -- 픽스처 `*_state`), `test_selftest_stick_diagram.py` 1(s071).
     * 16곳은 `ports` 없는 합성 topology를 tmp에 써서 `load_topology`를 부른다. `test_s013`은 `resolve_stack_layout`의 새 키워드 `ports` 누락 `TypeError`다.
     * s003·s043은 다른 거부의 **메시지 내용**을 단언한다. `ports` 거부가 먼저 나서 실패한다. `ports: {}`를 더하면 원래 거부가 살아난다(실측).
   * **픽스처 선언 규칙**(test-author가 소스 없이 따른다 -- `make_fx.py`가 이 규칙 그대로다):
     * 신호 입력이 없는 합성 toy 픽스처(바이어스 컬럼·미러·단일 소자 -- s003·s036~s043·s045·s050·s052·s053의 topology dict와 그 fixture `s037_state`·`s038_state`·`s040_state`·`s052_state`): `"ports": {}`.
     * 라이브러리 회로의 부분 netlist를 옮긴 픽스처(s011·s012의 `m3a_row_selftest`·`m3a_row_ofcb_selftest` -- current_reuse M3a 행): 그 회로 `ports` 선언 중 이 netlist에 나오는 넷만 같은 role로(`"Vip": {"role": "differential_input_p"}`, `"Vim": {"role": "differential_input_n"}`). 출력 포트(`Vop`/`Vom`)는 이 netlist에 없으므로 넣지 않는다.
     * `direction`은 넣지 않는다(S6). netlist에 없는 넷이나 레일을 선언하지 않는다(v2에서 거부된다).
     * 연결 파일 픽스처에는 `ports`를 넣지 않는다(s071 stick은 진입 파일 `partA`에만 `{}`. `test_ic3`의 `part_b`·s071 `partB`는 그대로). 넣는다면 진입 파일과 같은 선언이어야 한다(다르면 `linked ports differ` 거부 -- 검토 M5 실측).
     * `test_s013` 두 호출: 첫 호출 `ports=_rsl_meta["ports"]`(그 test가 읽은 current_reuse의 meta). 둘째 호출(`_rsl_bad_trs`, topology 없음)은 임의의 유효 선언 -- 같은 test 첫 호출의 `_rsl_meta["ports"]`를 쓴다. 그 호출은 선언 vsid 경로에서 먼저 `ValueError`가 나므로 `ports` 값은 판정에 영향이 없다. B26-1 뒤에는 `rails=`도 같은 방식으로 넣는다.
   * 이 보강은 기대값 변경이 아니라 선언 추가다. V5(`weakening_diff.py`)가 '픽스처 입력 리터럴 변경'으로 표시하면 이 절을 근거로 적는다(B26-1과 같은 처리). 기대값이 하나라도 바뀌면 V5·DEC-40 승인 대상이다 -- 이번 측정에서는 0이다. test 커밋에 넣는다(code 커밋과 분리, 계획 §14).
   * CC-4a 뒤에는 거부가 `SchemaRejectedError`(`ValueError` 아님)다. 그래서 `pytest.raises(ValueError)`로 다른 거부를 보는 s003·s043은 픽스처를 보강하지 않으면 여전히 실패한다(같은 17곳).
8. **(v3) 항목 단위 삭제 목록·`ports` oracle 재측정(gate `master` `dd60db6515b6…`, `git -C R rev-parse gate/master`).**
   * 방법: scratch `C:/g174`에 `git archive dd60db6` 사본 `base`, 같은 사본에 v2 모의 구현(`_drafts/b37a_scripts/make_head.py`를 경로만 바꿔 실행 -- 범위 1~4, B26-1 전이라 레일 = raw `supply_nets`, CC-4a 전이라 `ValueError` 대역. 치환 대상 수 assert 통과 = `7535799` 대비 바뀐 SD `kcl_series_union`(+3 −14)과 겹치지 않음)을 넣은 `head`. 시제품은 측정 전용이고 저장소에 들어가지 않는다.
   * 키 측정: 9회로 `load_topology` meta 키 합집합 -- base 16개(`_device_roles_autofilled`·`_device_roles_gap_fill_review_needed`·`_linked_files_loaded`·`_matching_pairs_autofilled`·`_matching_pairs_needs_review`·`_vertical_stack_id_autofilled`·`_vertical_stack_id_conflicts`·`compensation`·`device_roles`·`ideal_sources`·`netlist_sections_structured`·`schema_version`·`sizing_roles`·`source`·`symmetry`·`topology_name`), head = 그 16 + `ports`.
   * `e_lib_p3.py`(`_drafts/p3_scripts/e_lib_p3_proposed/`)를 두 판에서 17키 전부 MASK로 실행(`PYTHONHASHSEED=0`, `-B -P`): 9/9 `load`·V1·V2 성공, 전체 `hash` 두 판 같음(`223cdec96a4e…` -- `transistors`·V1·V2 불변). 키 단위 차이 쌍 = 계약 9 `pairs` 8쌍 + 9회로 × `ports`, 그 밖 0(`_vertical_stack_id_autofilled` 포함 -- design v0.9.5 §5.4 #47 (나)의 [미확인] 두 건은 이 판에서 '변화 없음').
   * 항목 추출·적용 확인: 차이 쌍마다 base·head 값을 풀어 `field_removed`·`entry_removed`·`review_needed_removed`를 만들고(head에만 있는 소자·필드 0, 값이 바뀐 필드 0 -- 모두 삭제), 계약 9의 적용 1~3을 base에 적용한 값이 head와 3키 × 9회로 `==`. 데이터 블록 sha256(펜스 안 줄의 3칸 들여쓰기를 빼고 LF로 이은 뒤 끝에 LF 1개) `7c1871a6977a21fe…`.
   * `ports` oracle: `git -C R show dd60db6:<library>/<c>.topology.json`의 `ports` + role 표로 만든 값이 head `masked.ports`와 9/9 같다(엔진 import 없음).
   * 산문 차이표(v2, `7535799`)와의 비교: 회로·키·소자·필드·옛 값이 모두 일치(ngcc 4, sf_pushpull 20 = M1·M2 + M5~M22, two_stage_ota_sf 5, nmcnr M201·M301, two_stage_ota M4·M6). v2 산문에 없던 사실 셋 -- (i) 삭제가 `device_roles`와 `_device_roles_autofilled` **두 키에 같은 29건씩** 일어난다 (ii) 필드가 모두 빠진 소자 20개(sf_pushpull M5~M22, two_stage_ota_sf M6·M8)는 두 키에서 **항목째** 사라진다(나머지 9개 소자 -- ngcc M1·M4·M6B·M7, sf_pushpull M1·M2, two_stage_ota_sf M1·M2·M4 -- 는 다른 필드가 남아 항목이 유지된다) (iii) review 항목은 dict 전체(`device`·`note`, two_stage_ota M4는 `field_conflicts`도)로 식별한다.
   * E3·offset·audit(`measure.py`, `compare.py`): E3 표 3회로 차이·2회로 같음, `input_referred_offset_pairs` 9/9·audit 9/9 같음 -- v2 값과 같다. SPECS 평가는 이 판에서 다시 재지 않았다(엔진 변경이 `kcl_series_union` 1곳이라 v2 측정을 그대로 둔다 -- 착수 시 재측정 대상).
   * 저장소 쓰기·상태 변경 git 0(`git archive`·`git show`·`git ls-tree`·`git rev-parse`만). `git status --short` md5 시작·끝 같음. 측정 뒤 `C:/g174` 삭제.
