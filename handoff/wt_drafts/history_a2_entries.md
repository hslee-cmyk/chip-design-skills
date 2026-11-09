# A2 계획 정정(v5.20)에 맞춘 history 문서 항목

대상: `docs/01-plan/features/gain-budget-gmid-sizing.history.md`(줄 끝 LF). 짝 계획 정정 = `patch_a2_plan.py`(같은 스크립트의 `--history` 옵션이 아래 항목을 **그대로** 넣는다 -- 아래 글은 스크립트의 `HIST_EDITS`·`HIST_INSERTS`에서 생성했고 바이트가 같다).
사용자 규칙(계획 = 설계, 이력 분리)에 따라 계획서에서 뺀 경위·옛 원문·측정 조건·선례·버전 기록은 전부 여기로 간다. 승인 기록 `20260930-b26-before-phase3`의 범위 'history H2·H4와 Version History 행'에 더해, 이력 문서 관례(결정 원문은 H1 U 표, DEC 행에 결정일 추가)대로 H1 두 곳을 함께 고친다(이력 문서라 판정 표·승인 대상 아님).

## 1. 기존 줄 고침

### H1 DEC-60 결정일·경위

옛 글:

```
| DEC-60 | 2026-09-15 | 2026-09-15 U-26으로 nmcnr `supplies_v{vdd: 0.9, vss: −0.9}` 확정(사용자 "1.8로 고쳐", "+-0.9로 고치고"). v5.15에서 `supply_nets`를 library 회로 전부 필수로 올리고 GB0 로드 게이트 거부를 붙였다 |
```

새 글:

```
| DEC-60 | 2026-09-15, 10-01 | 2026-09-15 U-26으로 nmcnr `supplies_v{vdd: 0.9, vss: −0.9}` 확정(사용자 "1.8로 고쳐", "+-0.9로 고치고"). v5.15에서 `supply_nets`를 library 회로 전부 필수로 올리고 GB0 로드 게이트 거부를 붙였다. 2026-10-01 결정 A2(사용자 결정 U2, 승인 기록 `20260930-b26-before-phase3`)로 레일 **넷**의 전환기 이름집합 해석을 B26-1(`20260930-b26-rail-accessor-set`)에서 끝내고 DF-19·DF-26의 넷 몫을 MG1에서 뗐다(v5.20. 원문은 아래 U 표 'A2' 행, 정정 내용은 H2) |
```

### H4 '29개' 행의 계획서 사용처

옛 글:

```
| `review11_code_literals_opsplit.txt` | 계획서 DF-19 |
```

새 글:

```
| `review11_code_literals_opsplit.txt` | 계획서 DF-19(v5.19까지. v5.20부터 아래 '넷 판정 운영 함수 AST 전수' 행이 대체) |
```

## 2. 새 행

### H1 U 표 -- A2 결정 원문

위치: `## H1` 두 번째 표(사용자 결정 U의 확정·닫힘 경위) 끝, `| Phase 1 완료 | 2026-09-23 |` 행 바로 뒤

```
| A2 레일 넷 전환기 종료·B26 앞당김(U2) | 2026-10-01 확정 | "승인 (Recommended)" -- 질문(2026-09-30): ① DEC-60의 '넷 이름으로 전원을 판정하는 전환기' 조항을 끝내고 전원은 topology `supply_nets` 선언으로만 정하며 선언이 없으면 오류 ② DF-19·DF-26 가운데 전원 넷 판정 몫을 MG1(전압값 작업)과 분리 ③ B26-1(spec card `20260930-b26-rail-accessor-set`)과 B34(`20260930-b34-grammar-explicit`, analog-grammar 부재 시 조용한 폴백 -> `ImportError`)를 Phase 3 모듈 분할보다 먼저(Phase 2 진행 중, card `phase: 2`). 다른 선택지는 '①②만 승인, ③은 Phase 3 뒤'와 '보류'. 원칙 기본안(사용자 원칙 '엔진 식은 topology 무관', U-26 (b) 9/9 선언으로 전제 소멸)이어도 DEC-60 한시 조항의 기한과 Phase 4 DF의 순서 변경은 결정 내용이라 U-39·DF-35/36 선례대로 사용자 원문 승인 한 건으로 받았다(review_b26_1 S3). 승인 기록 `20260930-b26-before-phase3`(target_kind decision). 판정 표(`plan_tables_hash` 입력)는 바꾸지 않아 `plan_tables` 승인은 없다. 재검토: B26-1 또는 B34가 병합되지 않은 채 Phase 3 M card가 `stick_diagram`·`sizing_recipe`를 나누기 시작하면 병합되지 않은 card의 앞당김은 효력을 잃는다 |
```

### H2 정정·폐기 행 -- DEC-60 넷 전환기

위치: `## H2` 첫 표 끝, `| 옛 형태 "input+cascode 동시 결정" |` 행 바로 뒤(닫힌 열린 이슈 표 앞)

```
| DEC-60 레일 넷 전환기와 그 인용 문구(v5.19) | 레일 **넷**도 전압과 함께 MG1(Phase 4)까지 이름집합 해석을 허용했다(`supply_nets`가 없던 기존 4회로용 한시 조항). 옛 원문: "`supply_nets`가 없는 기존 4개 회로는 **전환기 이름집합 해석**으로 현 코드 이름 집합(정본 표 N3.16, DF-19·DF-26)을 쓴다", (ii) "선언이 없으면 전환기 이름집합 해석이 찾은 레일 수와 실행 spec 레일 전압의 부호"(이름집합 해석으로 찾은 레일이 정확히 둘이 아니거나 음전위면 거부), N6.2 6a "`supply_nets` 미선언 회로는 레일·교류접지 집합이 전환기 이름집합 해석으로 정해져 `agnd`를 레일로 읽지 못하므로 그 회로의 교류접지·셀 분류·구동 종류·stage 경계·극점 노드·기둥 유도·DEC-65 방향 분류 판정을 무효로 보고한다", U-26 (b) 같은 취지의 무효 목록(루프 탐지 포함). 넷과 전압을 한 변경 단위(MG1)로 묶어 넷 판정이 U-26 (a)(기존 3회로 `supplies_v` 미확정)에 묶여 있었다. 같이 고친 것: DF-19 비고의 '29개(`sizing_recipe` 15 · `stick_diagram` 10 · `run_harness` 4)'는 옛 review11 줄 스캔이었고 `run_harness` 4는 넷 판정이 아니라 전압 선언(스칼라 `vdd: 1.8`, MG1 몫)이었다 -- 2026-09-30 AST 전수(H4)가 대체. DF-26 위치 칸의 줄 번호(sizing_recipe 3882~3883, stick_diagram 3147)는 이미 낡아 이름 상수로 바꿨다. MG1 행의 'DF-19·24·26과 같은 변경 단위' | 2026-10-01 v5.20 -- U-26 (b) 9/9 선언(2026-09-17)으로 전제가 없어졌고 사용자 원칙 '엔진 식은 topology 무관, 이름 기반 `_DEFAULT_RAIL_*`는 정본 아님'(2026-09-30)과 맞지 않는다. 레일 넷 전환기를 B26-1에서 끝내고(없으면 `load_topology` 거부) DF-19·DF-26 넷 몫을 B26-1~B26-4로 MG1에서 분리, 레일 전압 전환기는 MG1까지 유지. Phase 3 전이 싼 근거: 편집 파일 2개 대 Phase 3 뒤 6개 모듈, `_RAIL_NETS` 참조 함수가 `cd64170` 10개(P9 병합 뒤 9개)에서 B26-1 뒤 3개(`trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`·`propose_theta_kcl_gap_fill`)로 준다. kcl_residual `rail_nets` 키는 조용히 무시하지 않고 B26-1에서 거부(review_b26_1 S5). card `phase` 값 선례 = DF-35·DF-36 `phase: 2`. 사용자 결정 U2 승인 `20260930-b26-before-phase3` | 계획서 DEC-60·DEC-69·GB0·W0·N3.16·MG1·DF-19·DF-26·N6.1 Phase 4 범위·공격 13·N6.2 6a·U-26 |
```

### H4 측정 근거 -- 넷 판정 운영 함수 AST 전수

위치: `## H4` 표 끝, "two_stage_ota 크로스오버"로 시작하는 행 바로 뒤

```
| 넷 판정 운영 함수 AST 전수: `sizing_recipe` 14(+이름 상수 `_DEFAULT_RAIL_HI`·`_DEFAULT_RAIL_LO`) · `stick_diagram` 14(+이름 상수 `_RAIL_NETS`, 예제 데이터 2 제외), 그중 운영 경로 밖 3(`node_pole_estimate`·`find_differential_and_mirror_forks`·`propose_theta_kcl_gap_fill`) / 극성이 필요한 곳 = `trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`, 차동·미러 방향 라벨 3함수, `propagate_node_voltages`, `_metric_supply_current`·`_metric_rail_referenced_voltage`·`_metric_battery_centering_deviation`, MNA 고정 노드(`build_ac_network`·`_full_circuit_response`의 `fixed = {"gnd": 0.0}`) | 2026-09-30, 기준 `cd64170`. assets 운영 파일 7개와 `workspaces/run_harness.py`를 AST로 훑음(docstring 제외): 이름 상수 참조, `.rail_nets` 속성, 레일 이름 문자열 리터럴(`vdd`·`vss`·`gnd`·`avdd`·`avss`·`agnd`·`dvdd`·`dvss`·`vcc`·`vee`, 대소문자). 도달 = 모듈 간 최상위 이름 참조 그래프(`run_harness.run`·`optimize_full_circuit_budget`·`run_full_circuit_audit_from_topology`에서). N(넷이 레일인가 판정, B26)과 V(스칼라 `spec["vdd"]`, MG1)를 가름 -- `run_harness` 4곳은 V | 오케스트레이터 사전 조사 `prep_b26_supply_nets.md` §1(저장소 밖 초안, 실측 스크립트는 삭제 -- 방법은 이 칸) | 계획서 DF-19·DF-26 |
```

### H4 측정 근거 -- 선언 대 이름 집합

위치: 위 AST 전수 행 바로 뒤

```
| `supply_nets` 9/9 선언, 선언 집합 = 이름 집합 7/9(다른 2 = `pushpull_follower_buffer`·`sf_pushpull_output_opamp`의 `agnd`, 커패시터 단자에만 나옴), 대문자 변형 0, `linked_topology_files` 사용 0 / 엔진이 최상위 `supply_nets`를 읽는 곳 0(metric 선언 안의 같은 이름 키뿐) | 2026-09-30, 기준 `cd64170`. 회로마다 netlist 단자(source/drain/gate/bulk)와 `passive_elements`·`ideal_sources` 단자에 실제로 나오는 넷으로 `supply_nets`와 stick `_RAIL_NETS`·sizing `_DEFAULT_RAIL_*` 교집합을 대조(`_TEMPLATE`은 선언 없음 -- 작성 틀). 트랜지스터 단자만 보는 집합 판정 사이트는 9회로 모두 결과가 같고 달라지는 곳은 수동소자 단자까지 보는 MNA 고정 노드(B26-3)뿐 | `prep_b26_supply_nets.md` §2 | 계획서 DEC-60·DF-26 |
```

### H4 측정 근거 -- analog-grammar 레일 이름 집합 사용처

위치: 위 선언 대 이름 집합 행 바로 뒤

```
| stick_diagram이 analog-grammar(`netclass`·`idioms`)를 쓰는 함수 12, 그중 운영 경로 8(`suggest_vertical_stack_composites`·`refine_differential_and_mirror_relations`·`find_verified_differential_and_mirror_relations`·`propose_device_roles_gap_fill`·`_propose_headroom_roles`·`_propose_vertical_stack_ids`·`find_stack_edges`·`find_stack_edges` 경유 `geometry_colocation_union`) / 그 12함수가 부르는 analog-grammar 함수 12개가 전부 `RAILS`·`RAILS_POS`·`RAILS_NEG`를 쓴다 / 9회로 `RAILS ∩ 트랜지스터 넷` = `supply_nets ∩ 트랜지스터 넷` 9/9 | 2026-09-30, 기준 `cd64170`. `tools/gates/reachability.build_graph`로 그래프를 만들고 V7 `before_phase3` 루트에서 도달. 옛 '11(운영 7)'은 직접 import만 센 값 | 오케스트레이터 사전 조사 `prep_b34_b35_grammar.md` §2(저장소 밖 초안) | 계획서 DF-19 비고 |
```

### Version History 5.20

위치: `## Version History` 표 끝(파일 마지막 줄), `| **5.19** | 2026-09-18 |` 행 바로 뒤

```
| **5.20** | 2026-10-01 | **DEC-60 레일 넷 전환기 종료 + DF-19·DF-26 넷 몫을 MG1에서 분리**(사용자 결정 U2 "승인 (Recommended)", 승인 기록 `20260930-b26-before-phase3`. 원칙 기본안 -- 사용자 원칙 '엔진 식은 topology 무관', U-26 (b) 9/9 선언 완료). 레일 넷은 `supply_nets`만(없으면 `load_topology` 거부, B26-1 `20260930-b26-rail-accessor-set`), 레일 전압 전환기는 MG1까지 유지. DF-19·DF-26 넷 몫 = B26-1~B26-4(Phase 3 착수 전 가능), 전압 몫 = MG1. DEC-60 (i)은 스펙 선언 회로만, (ii)는 스펙과 무관한 로드 거부. DF-19 비고를 AST 전수(H4) 정본으로 바꾸고 assets 밖 사이트(`analog-grammar` `netclass.RAILS*`, 백로그 B35)를 추가. N3.16·MG1: kcl_residual `rail_nets`는 B26-1에서 거부, 그 밖의 옛 키 거부 게이트는 MG1. N6.1 Phase 4 범위·공격 13·N6.2 6a·U-26 문구 정정. 판정 표 무변경(`plan_tables_hash` 전후 동일, DF-19·DF-26 `수정 Phase` 괄호 밖 토큰 `4` 그대로). DEC-60 상태 칸은 B26-1 병합 뒤 고친다 |
```

## 3. 확인

* 각 새 행의 `|` 수 = 앵커 행의 `|` 수(표 열 수 유지) -- 스크립트가 단언한다. 칸 안 글에는 `|`가 없다(레일 이름 나열은 `·`로 구분).
* H4 행의 원자료 `prep_b26_supply_nets.md`·`prep_b34_b35_grammar.md`는 `wt/_drafts/`의 저장소 밖 초안이다. H4 머리말은 원자료를 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/` 아래로 적어 왔으므로, 저장소 경로가 필요하면 두 초안을 그 아래(또는 `gain-budget-gmid-sizing-20-dead-code-dup/`)에 함께 커밋하고 원자료 칸을 그 경로로 바꾼다(오케스트레이터 판단 -- 이 초안은 '방법은 이 칸'으로 자기 완결하게 적었다).
* H2 행의 수치(편집 파일 2 대 6, `_RAIL_NETS` 참조 함수 10/9/3)는 `draft_b26_plan_patch.md` §0과 `prep_b26_supply_nets.md` §3.5(기준 `cd64170`)에서 옮겼다. 쓰는 자리에서 재측정이 필요하면 커밋 전에 다시 잰다(카드 처리 규칙).
