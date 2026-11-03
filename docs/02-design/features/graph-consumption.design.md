---
template: design
version: 0.1.3
plan: ../../01-plan/features/graph-consumption.plan.md
plan_version: 0.14.9
---

# graph-consumption Design Document (GC-D 일부: card GC-1, GC-8)

> **Summary**: 승인 계획 `graph-consumption.plan.md`의 GC-1(구조 규칙 L·부채 목록)과 GC-8(`headroom_bound`·`order_terms` 정본 읽기)을 card로 내릴 수 있게 정한다. 공용 필드 정본은 `headroom-chain.design.md`다.
>
> **Status**: v0.1.3(§3 J1 목록, 위임 A-60, 재판정 전). v0.1.2(§3 J1 목록, 위임 A-59, 재판정 전). v0.1.1(§3·§5·§6 HC-1 card 후보 채택, 위임 A-50~A-52, 계획 0.14.9, 독립 판정 전). v0.1, 승인됨 -- 사용자 결정 O-226 위임 A-27(2026-11-04). 계획 기준 = graph-consumption 0.14.8(상위 v6.38.8, master `c0b41eee` 승인 A-25), design v1.16.3에 병합됨(옛 base `8b9ec744`).
>
> **이 판 범위**: GD-1·GD-3·GD-9·GD-14(GC-1), GD-2(HC design 인용), GC-8. **범위 밖**: GD-4·5·7·8·10~13(GC-2·3·5·6·7·9). 그 card 착수 전 이 문서를 개정한다. GD-6 = 소유표에 reader 칸을 더하지 않는다(규칙 L이 기계 판정, 소비자 열로 충분).
>
> **이력**: [graph-consumption.design.history.md](graph-consumption.design.history.md)

## 0. 경계

- as-built 인용은 재작성 범위 목록이다(원칙 8). 줄은 참고, card 착수 때 다시 잰다.
- **GC-0a·GC-0b 미룸**(O-225): GC:637의 GC-D 선행 측정이 없다. 처리 승인은 계획 v6.38.8 몫이다(§7-S1). M-G3는 원래 GC-1에서 다시 재므로(GC:604) GC-1 기준선은 영향이 없다.
- `[재점검]` = LA-1 측정 시점에 다시 본다.

# 부 I. GC-1

## 1. 파일 구성(GD-9)

| 파일 | 내용 |
|---|---|
| `E/tests/structure/rule_l_checks.py` | L-1~L-5 판정, 호출 그래프. **`structure_checks.py` import 0** -- 필요한 AST 도구는 이 파일 안에 둔다. 지문 대상 = 이 파일 |
| `E/tests/structure/rule_l_tables.py` | 진입점·출력 함수·동적 접근 허용·L-5 등록표·출력 전용 필드·칸 목록·기준선 상수 |
| `E/tests/structure/rule_l_debt.py` | 부채 목록 |
| `E/tests/structure/test_rule_l.py` | 현재 코드 판정, 부채 (a)(b)(c) |
| `E/tests/structure/test_rule_l_reject_fixtures.py`, `fixtures/rule_l/` | 거부 먼저 |

엔진 운영 코드 변경 0. `rule_l_checks.py` = code, `rule_l_tables.py`·`rule_l_debt.py`·test·픽스처 = test(A-32 J-1). **병합 자리** = HC-1 + GC-8 바로 앞(A-32 S-8), 기준선 재측정은 검증자 독립 스크립트로 한다. `7620f5ee` 390항목 대비 늘어난 키마다 원인 card와 근거(소유표 소비자 또는 출력 전용 행)를 판정 기록에 적고, 근거 없는 새 `L-1`·`L-2`·`L-4` 키는 부채로 넣지 않고 멈춰 그 card로 되돌린다(위임 A-37). 줄어든 키는 사유만 적는다. `test_structure_test_mapping.py`가 새 파일을 요구하면 test 역할이 그 표에 더한다.

## 2. 진입점과 출력 함수(GD-1)

**도달 판정**: 모듈 AST로 함수 정의 표를 만들고, 호출을 (i) 같은 모듈 이름 (ii) import 이름 (iii) 패키지 `__all__` 재수출로 푼다. `@compute_block` 함수는 그 블록 객체 호출을 호출로 센다. 속성 호출 `x.f()`는 그 이름의 정의가 엔진에 하나일 때만 풀고, 둘 이상이면 후보 전부에 도달로 센다(넓게). 함수 값 전달은 그 이름의 Load를 호출로 센다. **풀지 못한 호출은 L-1 대상 읽기에 영향을 줄 때 위반**이다(fail-closed).

**진입점 11개 = card interface `PARAMS.entry_points`**(A-32 S-1, 측정 근거 spec S-1). 초기안 4개는 이력으로(`_module_map` 'entry'는 근거가 아니다 -- F-G27). OS-2 `run_plan`은 그 card 병합 때 더한다(기준 변경 아님 -- 대상 넓힘).

**출력 함수 5개** = `_ach_body`, `_coupling_report`, `structure_tables`, `orbit_matching_crosstab`, `_from_snapshot`(A-32 S-2). `node_across_front`는 진입점이다. 기준은 N3.1-2다.

이 두 목록은 `7620f5ee` 실측, 병합 base에서 재측정한다.

## 3. 부채·기준선·지문(GD-3), 호출자 0(GD-14)

- **항목 키**: `(규칙 id, 대상)` 문자열 tuple. L-1 = `("L-1", "kind.field")`, L-3 = `("L-3", "블록.kind.field")`, L-4 = `("L-4", "모듈.클래스.칸")`, L-5 = `("L-5", "개념", "파일", "함수")`, L-1x = `("L-1x", "모듈.함수")`, L-1d = `("L-1d", "모듈.함수")`. 줄 번호를 키에 쓰지 않는다. 키 표 정본 = interface '위반 키와 code'.
- **항목 값**: `DebtItem(처리 종류, card id, 사유)`. 처리 어휘는 N3.1-6 그대로. card id는 계획 card 표의 id만(GC-B9 규칙).
- **기준선 상수**: `rule_l_tables.BASELINE`, 정렬 tuple. 검증자가 독립 스크립트로 재고 test 주체가 넣는다.
- **지문**: 정렬 JSON(UTF-8, 구분자 고정)의 sha256. 대상 = N3.1-6 (d) 목록 + `rule_l_checks.py`·`rule_l_tables.py`의 파일 바이트(줄바꿈 정규화). 기록 = `.ai/verification/GC-1.json`.
- **동적 접근 허용 파일**: 넷 = `core/graph_snapshot.py`, `core/projection.py`, `core/graft.py`(core 접근자), `sizing/seal_versions.py`(봉인 판 검사) -- 계획 N3.1-1의 두 부류. 늘리지 않는다. 기존 9함수는 키 `("L-1d", "모듈.함수")` 부채, card GC-7(A-32 S-3).
- **GD-14**: 함수·메서드·클래스(A-32 S-5). **L-4 대상** = spec 계약 6(S-7). AST 호출 그래프에서 진입점 밖이고 호출자 0인 함수 = 위반 `no_caller`(블록 데코레이터 함수는 블록 호출로 센다, `test_` 밖 tests는 대상 아님). `size_and_seal_local` 항목 = 배선 대기, card LA-1. 대상 사전 측정(M-G9) 미룸 -- GC-1 기준선이 그 자리를 잰다.
- **규칙 L-5 '동작점 사본'**: N3.1-5 정의 그대로. 추적이 안 풀리면 위반.

**HC-1과의 경계(GC:663)**: 새 필드에 부채 항목을 줄 수 없다. HC-1 design의 출력 전용 항목(`graph/start: loop_stack_notes`, `device: dc_triode_region`)과 출력 함수 `_chain_start_note`·`_triode_rows`는 목록 추가라 지문이 바뀐다. 칸(`LoopConflict` 내용 칸, `ChainExist`·`ChainCycle` 칸, `chain_cuts` 칸)은 reader가 있어 L-4를 목록 없이 통과하므로 `output_only_slots`에 넣지 않는다(빈 tuple 유지, 위임 A-59·A-60). N3.1-6 (d)에서 '대상 축소·허용 확대'는 기준 약화다. 판정: **항목마다 승인된 design 소유표 행을 근거로 적으면 기록된 기준 변경이고, 근거 없는 추가는 `criteria_weakened`**. 검증자가 HC-1 판정에서 대조한다. **작성자 판단 J1**(§7-S2).

## 4. GC-1 toy(거부 먼저)

| id | 픽스처 | 기대 |
|---|---|---|
| L1 | reader 0 필드, 도달 밖 reader만 | L-1 위반 |
| L2 | 출력 함수만 읽음 + 목록 없음 | L-2 위반 |
| L3 | READS에 안 읽는 열, 블랭킷 READS | L-3 위반 |
| L4 | reader 없는 칸 | L-4 위반 |
| L5a | F-G13 7자리 전부, 속성 꼴 `cells.py`·변수 경유 꼴 `writer_plan.py` | 자리별 L-5 위반. 못 잡으면 GC-1 멈춤 |
| L5b | `layout_input.py` 꼴, 반환·객체 칸 전파 | 동작점 사본 |
| L5c | `SatDevice`·`GateArea` 꼴 | 사본 아님 |
| L6 | 항목 삭제 + 다른 항목 추가 | 부채 (c) 실패 |
| L7 | 고쳐졌는데 남은 항목 | 부채 (b) 실패 |
| L8 | 호출자 0 함수 | GD-14 위반 |
| L9 | 동적 필드 인자 | `field_arg_dynamic` |
| L10 | 지문 대상 파일 한 글자 변경 | 지문 불일치 |

# 부 II. GC-8

HC-1과 같은 통합 병합, GC-8 커밋이 HC-1 커밋 뒤(표 #17, O-191). 변경 종류 = 동작 변경.

## 5. 배선

필드 형식 = `headroom-chain.design.md` §2. GD-2 = 그 표가 정본이다(쓰기 계획 두 필드 + `dc_current_symmetry`).

### 5.1 `order_terms`(`E/sizing/block_columns.py`)

- `order_terms` 호출자 `dc_columns`가 `chain_graph`를 **한 번** READS해 넘긴다(`Circuit`을 함께 쓰는 `icm_config` READS를 넓히지 않음). 새 memo·슬롯 0.
- `on_structural`인 변마다 `hi_net`에 `(True, lo_net)`, `lo_net`에 `(False, hi_net)`를 쌓는다. 항은 쓰지 않는다. 선언 triode 변도 같은 변이다.
- **항 순서 = 필드 변 순서**(D40:2206 (b)): `(colour, 이름)` 정렬·자체 방향 계산 삭제.
- `_kind_sign` 방향 계산 삭제 범위는 이 자리만이다.
- **동작 변화**: 구조적 0 전류·`off` 선언 소자 변이 순서 창에서 빠진다. 13회로 해당 수 미측정 `[재점검]`.
- **WB-1 겹침**(D40:2210): 나중 병합 쪽 완료 조건 = `order_terms` 자체 방향 계산 grep 0, 순서 창 = E-13 정의.

### 5.2 `headroom_bound`(`E/metrics/headroom_bound.py`)

- `_edges(local, edges)` → `_edges(local, chain, vgs_edges, costs)`. 호출자 `metrics/achievability.py`가 READS를 더해 넘긴다.
- VDS 변: `chain.edges`에서 `device ∈ local`이고 `on_structural`. 비용 = `term_kind == sat`이면 `vds_edge_floor_v`, `lut_floor`이면 0.
- VGS 변: `dc_vgs_edge`. 같은 구조적 전도 집합. 비용 = `vgs_min_v`.
- **`lut_floor` 값은 쓰지 않는다**(O-33 (9)). DC 범위 개념과 LUT 표현 범위를 섞지 않는다.
- 창 미상 처리(위임 A-51, HC:342): `on_structural` False 변의 끝 넷이고 위쪽 또는 아래쪽 경로가 없으면 그 행만 `STATUS_UNKNOWN`. 전역 순환이면 지금처럼 전부 `STATUS_UNKNOWN`. 다른 넷의 경로 없음은 `STATUS_CERTIFIED` + 레일 끝(유효한 상한) 그대로. `iv_headroom` 예산은 HC design §8.
- 호출자 둘(위임 A-50): `metrics/achievability.py`, `search/iv_headroom.py`(`_budgets`).
- 상한 건전성: 비용을 줄이기만 하므로 상한이다. 정지 집합 단조는 요구하지 않는다(O-44 (2)). 새로 정지한 회로는 검증자 하네스(엔진 안 우회 스위치 금지).

### 5.3 이름(GC-8 (4))

`edge_costs.vds_min_v` → **`vds_edge_floor_v`**('VDS 변 격자 하한 비용'). 소비자 셋 + `headroom_bound`·`_short_l_bin`을 같은 커밋에서 바꾼다. `vgs_min_v`는 이름 유지('VGS 변 격자 하한 비용'). 정의 변경 자체는 HC-S다.

### 5.4 삭제

`headroom_bound._edges`의 핀 방향 분기, `block_columns` `order_terms` 방향 계산과 정렬. `ls_swing`은 건드리지 않는다(DE-1, 지울 코드에 배선하지 않음). `iv_headroom._edge_nets`는 HC-1.

## 6. GC-8 toy와 완료

| id | 입력 | 기대 |
|---|---|---|
| G1 | 선언 triode 변 toy | `headroom_bound` 비용 0 방향 변, `lut_floor` 값 미사용(손계산 창) |
| G2 | 같은 toy | `order_terms`에 같은 변 있음, 항 순서 = 필드 순서 |
| G3 | `off` 선언·구조적 0 전류 | 두 소비자 모두 변 없음, 끝 넷 한쪽 경로 없으면 그 행 `STATUS_UNKNOWN` |
| G4 | 작은 격자 LUT | `vds_edge_floor_v` 손계산 |
| G5 | 이름 전단사 | 항 순서 불변(base 이름 키 -- red) |
| G6 | `git grep` | `_edges` 핀 분기·`order_terms` 방향·`vds_min_v` 0 |
| G7 | 소유표 | READS = 실제 읽기, 규칙 L 통과 |

**완료**: HC:585와 GC-8 행. 같은 개념에 소비자별 다른 규칙 0(검증자), 커밋별 변화표(O-38 (3)), WP-10 계측.

**재작성 범위**: `E/sizing/block_columns.py`, `E/metrics/headroom_bound.py`, `E/metrics/achievability.py`, `E/search/iv_headroom.py`(둘째 호출자), `E/lut/derived_fns.py`(이름), `E/search/start_intervals.py`, `E/search/_helpers_curves.py`, CONTRACT 해당 줄.

**새 필드**: 0. 새 소비자만 있다.

## 7. 멈춤·승인 항목

- **[v1.16.3 -- S1·S3은 계획 v6.38.8로 닫힘, 착수를 막지 않음]** **S1**: GC:637 GC-D 선행 GC-0a(GC-0b 일부)를 O-225로 미루는 항목은 계획 v6.38.8 승인이 필요하다. 미룬 측정: M-G2·M-G3 예비·M-G3c·M-G4·M-G5·M-G6·M-G9, M-G1·M-G1b·M-G7. 이 판은 GC-1·GC-8에서 값을 정할 때 이들을 쓰지 않는다. GC-0b 입력 항목은 범위 밖 GD로 남긴다.
- **S2**: §3 J1(출력 전용 목록 추가와 지문).
- **S3**: GC-1 공통 착수 조건 cProfile 기준선(엔진 card만, GC-8)의 미룸 여부 = v6.38.8.
- **N3.10 상위 개정 대조**: 이 판에서 전수 대조하지 않았다. 검증자 대조 항목이다.
