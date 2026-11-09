# gain-budget 계획 v6.25 독립 검증 (plan/gb-v625 `d9efd9b2` 대 master `c237d96e`)

검증자: 독립 plan validator(작성자 아님, 읽기 전용). 2026-10-21.
대상 diff: plan.md +98/−2(version·Status 줄만 교체), history.md +1(H1 Version History 표 v6.25 행).
근거 code: worktree `wt/gb-v625/skills/analog-gmid-design/gmid_engine`(= E) HEAD `d9efd9b2`.

## 판정 요약

**판정: 조건부 통과** -- 차단 결함 0. 고쳐야 할 것 3(M1~M3), 고치면 좋은 것 4(N1~N4).

| 항목 | 판정 |
|---|---|
| (A) O-73·O-74 반영 범위 | PASS(D4 13회로 확장 = 정당한 유도) -- 단, M2(출처 `origin` 뜻) |
| (B) 실현 가능성 표 인용 | PARTIAL -- 인용 줄은 모두 맞음, SD-M2 사실 오류(M1) |
| (C) `measurement_load`가 해석을 안 바꾸는가 | PARTIAL -- 점 하나의 해석 값은 불변, 탐색 궤적은 바뀔 수 있음(M3) |
| (D) rfc 분리·면적 | PASS(총용량 불변, +250 µm², −1000 µm² 산술 맞음) -- 위치는 원문 추론(N3) |
| (E) `()` 대응 한정 | PASS -- 위치는 N4 |
| (F) graph 단일 정본 | PASS |
| (G) 기존 문언·IT-1/IT-2 정합 | PASS |
| (H) 이력 자리·삭제 | PASS |

## 고쳐야 할 것 (must-fix)

**M1. SD-M2 사실 오류 -- rfc_ota에 `source_manifest.passive_count`가 있다.** plan 착수 실측 SD-M2 "이번 조사 grep으로는 없음"은 틀림:
`assets/heldout/rfc_ota.topology.json:12-16` `"source_manifest": {"figure": "... p.37 Fig.11(CL)", "device_count": 35, "passive_count": 2}`.
`E/authoring/source_manifest.py:7·34-35`가 `passive_count == len(passive_elements)`를 대조하므로 D2(소자 추가)만 하면 spec/topology 로드가 거부된다.
고칠 것: SD-T2 D2에 `passive_count` 2 → 3과 `figure`에 p.35 근거 추가를 명시, SD-M2를 '확인(있음)'으로.

**M2. D4 `supplies_v.source`의 `origin`·`citation` 뜻이 값 출처와 섞인다.** `E/authoring/spec_sources.py:5-6` 머리:
"채택된 논문 값은 `user_spec` + `origin: paper` + `record`로만 들어온다" -- `origin`은 **선언된 값**의 출처다. 그런데 supplies_v 값은
9 library 회로 모두 사용자 결정(2026-10-07, 1.8/0 V·agnd 0.9 V)이고 원문 값과 다르다(ngcc 원문 1.2 V, nmcnr ±1 V, r2r 3.3 V).
D4가 "원문 인용을 `origin`·`citation`에"라고 하면 `origin: paper`가 1.8 V를 논문 값으로 적는 꼴이 된다(heldout r2r는 이미 `origin: paper` + 값 1.8 V -- 같은 혼동의 선례).
`SpecSource` 하나에 origin 하나라 '값 출처'와 '구성 출처'를 함께 담을 수 없다. 고칠 것(계획 문언만): D4·DEC-101 (1)에
"`origin`은 값 출처(library = 사용자 결정 → `user` 또는 생략), 공급 구성의 원문 인용은 `record` 문장(또는 `origin`이 값과 같은 원문일 때만 `citation`)"처럼 갈래를 적는다.
새 키를 만들지 않는 결정(DEC-101 (1))은 그대로 맞다.

**M3. 완료 조건 (4) '해석 metric 변화 0'의 측정 방식이 정해지지 않았다 -- 표지는 탐색 궤적을 바꿀 수 있다.**
`passive_area_decl.excluded`의 소비자는 면적·layout만이 아니다(`git grep` 전수):
`E/metrics/dc_metrics.py:115-118`(면적 metric), `E/metrics/achievability.py:246-251`(GB4 면적 하한),
`E/search/_helpers_area.py:38-40` → `E/search/start_intervals.py:43`·`E/search/iv_area.py:27`(출발 구간 면적 추정),
`E/convergence/converge_point.py:48`, `E/layout/passives.py:20`. 따라서 같은 θ 점의 DC·AC·과도 값은 불변이지만(해석 경로는
`e.measurement_load`를 읽지 않음 -- 읽는 자리는 `E/pipeline/stage_b.py:167`·`E/search/search_context.py:180` 두 곳뿐, 둘 다 `passive_area_decl` 입력),
출발 구간·면적 제약 판정이 바뀌면 찾은 front 점이 달라져 front 위 metric은 바뀔 수 있다. 고칠 것: DEC-100 (4)의 소비자 목록에
GB4 하한·출발 구간 면적 추정을 넣고, 완료 조건 (4)를 "**같은 θ 점(S0 기준선 점) 재평가**에서 해석 metric 변화 0; front 변화는 (3) 변화표"로 적는다.
SD-1 성격 문단의 "front 비지배 관계는 같아도"도 출발 구간 영향까지 포함해 다시 적는다.

## 고치면 좋은 것 (nice-to-fix)

**N1. SD-M1은 지금 닫을 수 있다.** `E/authoring/spec_model.py:5` "`SpecSource` 지문(`__canonical__`)에는 `kind`만",
`E/authoring/SPEC_CONTRACT.md:204` "`record`·`citation`·`decided`·`origin` 문구는 밖", `spec_sources.py:36` supplies_v 허용 kind = `user_spec` 하나.
→ D4는 `supplies_fp`·`spec_fp`를 바꾸지 않는다. '(미확인)'을 '확인 -- 지문 불변'으로 바꾸면 SD-T3 S0 기준선 '지문만' 줄이 빠진다.

**N2. SD-T3 `test_stage_b_library.py:218`은 기대를 spec에서 읽어 만든다**(`decl.get("measurement_load")`면 건너뜀) -- 고정 기대 아님, 자동으로 따라간다. '(미확인)' 대신 '자동 추종, 확인만'.
`test_j_rules_library.py:32`는 표 문자열(docstring) 행이라 판정 대상 아님 -- '확인만' 그대로 맞음.

**N3. rfc 0.5 pF의 out–gnd 위치는 원문 추론이다.** 원문 p.35(paper.md 1887-1891) "The initial sizing was maintained, but 500fF were added for a
total of 2.75pF, to make the Recycling structure stable"은 총 부하 용량만 말하고 연결 자리는 적지 않는다(p.35 1855 "a capacitance of 2.25pF" = 부하).
'총 부하 2.75 pF'에서 출력–접지 병렬로 읽는 것은 타당하나 D2 근거 칸에 "(총 부하 문장에서 추론, 연결 표 확인 때 사용자 확인)"을 적는다.
산술: 2.25 + 0.5 = 2.75 pF(같은 두 넷 병렬 → 소신호 동일), 0.5 pF / 2.00e-15 F/µm² = 250 µm², current_reuse 4 × 0.5 pF = 2 pF → 1000 µm² -- 맞음
(current_reuse spec 실측: Cf1·Cf2·Cs1·Cs2 각 5e-13 F, CL1·CL2는 이미 measurement_load).

**N4. IT-0 기록과 `()` 대응 문단·IT-2 (10)(a) 제안이 데이터 card SD-1 안에 있다.** `()` 대응은 측정 구성 **규칙**(N3.8)의 읽기이고, IT-0 결과는 측정 기록이다.
계획서=규칙, 기록=history 원칙에 따라 `()` 대응 한 문장은 N3.8 'ICMR 측정 구성'·'슬루율 측정 정의' 곁(또는 IT-2 card)으로, IT-0 수치는 history로 옮기는 편이 찾기 쉽다.
내용 자체는 맞다: `spec_elements.py:19-20`(빈 list = β = 1, UD 9), `noise_plan.py:9-10`(`()` = open, None = `noise_feedback_undeclared`), `noise_plan.py:6` docstring 언급 실재.
덧붙여 엔진 안에서 `()`가 spec 쪽 'β = 1 루프'와 잡음 쪽 'open'으로 뜻이 갈리는 것은 기존 상태(이번 변경이 만든 것 아님) -- 백로그 한 줄 권장(graph 규칙 3 관점).

## 항목별 근거

### (A) O-73·O-74 반영 -- PASS
- O-73 각 요소: sizing/면적/layout = DUT(DEC-100 (1)), 모든 해석 = DUT ⊕ 응용 망과 DC/AC/과도 구분(2), 해석에서 빼지 않음·O-66 유지(3), 1단계 `measurement_load`(4), 2단계 응용 topology card·O-68/O-69 대체 여부 그때(5, AP-1 (a)), 이상 전류원 2단계(7, AP-1 (b)), IT-0 as-built 병행(SD-1 선행 = IT-1+IT-2 병합). 빠짐 없음.
- O-74 (1) 원칙 전부 DEC-101 (1)~(5), (2) 회로별 확정 = SD-T1 13행(1~5번 대응 = history 행에 명시, user_decisions O-74와 일치), r2r 문장 정정 = D5, nmcnr ±1 V 인용·입력 DC agnd는 SP-2 때 = SD-T1·IT-1 관계 문단, (3) 목록 = D1·D2·D3, 12회로 불변.
- **D4 13회로 확장**: O-74 (1)은 "원문 공급 구성(single/dual)을 출처와 함께 spec에 선언(한 곳)"으로 회로를 가리지 않는 원칙이고, (2)는 "나머지는 감사대로(… single)"로 13회로 전부의 구성을 확정했다. 원칙 (1) + 확정값 (2)에서 13회로 선언이 바로 나온다 -- **범위 확장 아님, 정당한 유도**. 다만 선언 방식은 M2.
- 결정에 없는 추가: IT-0 기록·`()` 대응(정렬로 표기)·(10)(a) 제안(결정하지 않음 표기) -- 표지가 붙어 있어 무단 결정은 아님(N4는 자리 문제).

### (B) 인용 확인 -- PARTIAL
| 인용 | 실제 | 판정 |
|---|---|---|
| spec_elements.py:9 | 선택 키 `measurement_load` 설명 | 맞음 |
| :37 | `LOAD_KEY = "measurement_load"` | 맞음 |
| :70(:69-71) | true만·`LOAD_KINDS`(=:46 capacitor·resistor) 밖 거부 | 맞음 |
| :118-138 | `_feedback` -- measurement_load와의 상호 배제 검사 없음(`element_value_declaration` :140-173에도 없음) | 맞음 |
| area_decl.py:42-47(:38-55) | `loads = frozenset(...)`, excluded 분기 :48-49 | 맞음 |
| stage_b.py:167, search_context.py:180 | `e.measurement_load`로 이름 tuple → `passive_area_decl` | 맞음 |
| passives.py:20 | `if name in area_decl.excluded` | 맞음 |
| contract_input.py:169 | 제외 규칙 docstring(코드 자리는 passives.py) | 맞음(문서 문장) |
| s1_structure.py:56 | `put("node", "is_rail", net, net in rails)` | 맞음 |
| s1_values.py:29 | `SUPPORTED_SOURCE_KINDS = ("current_source",)` | 맞음 |
| spec_input_dc.py | `{"net": …}`·`input_dc_net_not_rail` :5·9·37 | 맞음 |
| spec_sources.py | `SOURCE_KEYS` :32, `CITED_ORIGINS` :31 | 맞음 |
| spec_supplies.py | `KEYS = ("values", "source")` :20 | 맞음 |
| spec_model.py:307 | `("supplies_fp", ("supplies_v",))` | 맞음, SD-M1은 N1로 닫힘 |
| noise_plan.py:9-10 | `()` = open, None = undeclared | 맞음 |
| test_spec_library_load.py:96, :364-371 | MEASUREMENT_LOADS·CI10 | 맞음 |
| SD-M2 'passive_count 없음' | rfc_ota.topology.json:15 `"passive_count": 2` | **틀림(M1)** |

### (C) measurement_load와 해석 -- PARTIAL
해석 경로(소신호 회로·DC 풀이·과도)는 `measurement_load`도 `excluded`도 읽지 않음(`git grep` 전수). current_reuse Cf/Cs는 topology에 남고 `feedback.elements = [Cf1, Cf2]` 유지 → β 루프·CI-10·잡음 불변. 그러나 excluded가 GB4 면적 하한과 출발 구간 면적 추정에 들어가 탐색 결과가 달라질 수 있음 → M3.

### (D) rfc 분리 -- PASS(N3)
### (E) `()` 대응 -- PASS
측정 구성 규칙에서 `()`(β = 1 루프)와 미선언(β = 1 follower)은 같은 결과: 단일 출력이면 follower, 차동 출력이면 ICMR '차동 모드만 닫음'(O-68 (2), N3.8 580행)·슬루 정의 불능(O-50 G2, 581행). 잡음은 엔진 정의가 다르므로(`()` = open) 한정이 맞다. 새 결정 아님 표기도 맞다.

### (F) graph 단일 정본 -- PASS
외부 소자 표지 = spec 한 자리 → writer `passive_area_decl` 하나. `feedback.elements`와 공존은 정의 축이 달라(β 루프 대 면적·layout) 규칙 3 충족. 공급 구성 = `record` 기록 전용, 새 키·새 필드 없음(소비자 0 → 만들지 않음). 중간 rail = 기존 `supply_nets` → S1 `node.is_rail`. rfc 보상 C = topology 원소 + spec 값(F5). 응용 topology는 정본 자리 없음 → 만들지 않고 계획 개정(규칙 6, S-7). 새 cache·memo·sctx 슬롯·사본 0.

### (G) 기존 문언 정합 -- PASS
O-50 G2(슬루 차동 미선언 = 정의 불능)·O-68 (2)(차동 모드만 닫음)·O-69 (1)(슬루 시작 동작점 = ICMR DC 닫힘 인용, current_reuse Cf 예시)·DEC-23·N3.8 문언 모두 그대로 맞다 -- Cf1·Cf2가 topology·feedback에 남기 때문. SD-1은 `input_dc`를 바꾸지 않아 IT-1 대상·IT-0 집합 불변, 순서 = IT-1+IT-2 병합 뒤. nmcnr 입력 DC는 SP-2 card로 미룸 -- O-74 (2) 문언과 일치.

### (H) 이력·삭제 -- PASS
삭제 2줄 = `version: 6.24` → 6.25, Status 줄 교체. 옛 Status 전문은 새 Status 뒤 "이전 판:"으로 그대로 보존(문자 단위 diff: 삽입만). history 행은 v6.24 행들 바로 뒤(H1 안 Version History 표, 1405행) -- 기존 위치 관례와 같음. "대체한 옛 문장 없음"·"기각한 다른 표현 (가)(나)" 기록 있음.


## 재확인 (plan/gb-v625 `11edba27`, 부모 `d9efd9b2`)

검증자 같음, 읽기 전용. diff = plan +14/−11, history +1(H1 'v6.25 둘째 커밋' 행).

| 지적 | 처리 | 판정 |
|---|---|---|
| M1 passive_count | D2에 `source_manifest.passive_count` 2 → 3(`source_manifest.py:7·34-35`)·`figure` 'p.35' 추가, SD-M2 닫힘(`rfc_ota.topology.json:15`), 실현 가능성 표 행 추가 | 닫힘 |
| M2 origin 뜻 | DEC-101 (1)·D4: 구성·원문 인용 = `record` 문장, `origin`·`citation` = 선언 값 출처 그대로(paper로 바꾸지 않음), 새 키 없음 | 닫힘 |
| M3 탐색 궤적 | DEC-100 (4) 소비자에 `achievability.py:246-251`·`_helpers_area` → `start_intervals.py:43`·`iv_area.py:27` 추가(실재 확인), '탐색 궤적과 front가 바뀔 수 있다'; 성격 문단 동일; 완료 조건 (4) = '같은 θ 점(S0 기준선 점) 재평가 시 해석 값 변화 0, 궤적·front는 (3) 변화표' | 닫힘 |
| N1 SD-M1 | 닫힘(`spec_model.py:5`, `SPEC_CONTRACT.md:204`), D4 결과 '지문 불변' | 닫힘 |
| N2 stage_b test | '자동 추종(210~222행), 확인만' | 닫힘 |
| N3 out–gnd 추론 | D2에 '연결 out–gnd(CL과 병렬)는 추론이다' + 연결 표로 사용자 확인 | 닫힘 |
| N4 자리 | `()` 갈래 문단 → N6.6(IT-2) 끝(1505행, N6.7 앞), IT-0 수치 → history 행. (10)(a) 제안은 SD-1에 남음(표지 '사용자 확인 대기' 있음 -- 수용) | 닫힘(부분 수용) |

S0 기준선 행의 '지문'은 D1(`elements_fp`)·D2(topology hash) 때문에 여전히 맞다. 삭제된 옛 문장은 history 행 '바꾼 옛 문장'에 모두 적혀 있다.

**새 결함 R1 (고쳐야 할 것, 작음)**: N6.6에 새로 넣은 `()` 문단이 "통일 여부는 사용자 지시(2026-10-21)로 분석 중이다(근거 `wt/_drafts/evidence/2026-10-21/feedback_empty_unify_feasibility.md`, 결정 대기)"를 인용하는데
(1) 그 파일이 `_drafts/evidence/2026-10-21/`에 **없다**(ls 0건), (2) 그 사용자 지시가 `user_decisions.md`에 기록되어 있지 않다(grep '통일'·'feedback_empty' 0건).
병합 전에 증거 파일을 만들고 지시 원문을 기록하거나, 그 전까지는 인용을 '분석 예정(사용자 지시 2026-10-21 대화)'으로 낮춘다. 규칙 내용(결정 전까지 잡음은 현 동작 유지)은 맞다.

**graph 단일 정본**: 이번 커밋도 새 필드·cache·사본 0. 공급 구성은 `record` 기록 전용, 표지 소비자 목록만 사실대로 넓혔다. PASS.

**재확인 판정**: M1~M3·N1~N4 모두 닫힘. R1(인용 파일 부재·지시 미기록)만 고치면 **사용자 승인 뒤 병합 가능**.
