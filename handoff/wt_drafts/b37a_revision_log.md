# B37a spec card 개정 기록 -- v1 → v2

대상: `_drafts/draft_b37a.spec.md`(id `20260930-b37a-ports-roles`). v1 사본 `_drafts/draft_b37a.v1.spec.md`(개정 전에 복사). 입력 검토 `_drafts/review_b37a.md`.
새 파일: `_drafts/draft_b37a_approval_question.md`(사용자 질문 Q1~Q3·승인 기록 초안 -- card 안에 두면 코드 블록의 `## ` 줄이 card 절로 파싱되므로 따로 둠, B34 선례).
측정: gate `master` `7535799`, 저장소 쓰기·상태 변경 git 없음(`git archive`·`git log`·`git show`만). scratch `C:/g68`(`base` = `git archive 7535799`, 모의 `head`, 픽스처 보강 `head_fx`·`base_fx`, 변이 사본 `m_*`·`mut`), 측정 뒤 삭제.
`$PY` = `C:/Python314/python.exe -B`, `PYTHONHASHSEED=0`. 게이트 함수(`mutate_changed.changed_defs`·`mutants`·`_replace_def`·`inventory`, `reachability.build_graph`·`iter_defs`, `role_paths.parse_spec_card`)는 사본 `tools/gates`에서 읽기 전용 import(`main` 실행 없음). N2 분류는 `_drafts/v3_scripts/v3_scope_classify.py`의 `classify`를 그대로 import.
스크립트·출력: `_drafts/b37a_scripts/`(`out/`의 `contracts_*.json`·`mutrun.txt`는 1차 -- v2 계약 케이스 추가 전, `contracts2_*.json`·`mutrun2.txt`는 2차).

## 1. 검토 지적별 처리

| 지적 | 처리 |
|---|---|
| **B1** 계약 3 불변 범위 | library 판 = 레일(`supply_nets`) 밖 **모든** 넷(트랜지스터 단자·`passive_elements`/`ideal_sources` `terminals`·`ports` 키), 합성 판 = **포트 넷만**. `netclass.HINT_INPUT` import 삭제(계약 머리 'test 모양'에 "analog-grammar 기호를 import하지 않는다"). 경계 문장을 검토 권고 3 그대로("비포트 넷 … 이름 의존은 B37b가 닫는다. 비포트 넷 이름만 바꾸는 변형은 계약으로 쓰지 않는다"). B1 반례를 '참고 실측, 계약 아님'으로 적음. 준비 자료 §4.2 C1 문장 정정은 오케스트레이터 문서 커밋 목록(작성 전 실측 4)에 추가 |
| **B2** 픽스처·가짜 선언 | (1) 명시적 `ports: {}` 수용(B26-1 `supply_nets: []` 선례), `_comment`만·출력만·입력만도 수용. (2) 거부 추가: 빈 넷 이름(접근자), 포트 넷이 단자에 없음·포트 넷이 레일(`load_topology` -- 접근자 docstring '검사하지 않는 것'). (3) `input_referred_offset_pairs`: 'ValueError 삭제' → 'offset 쌍이 있는데 입력 0이면 거부 유지', offset 쌍 0이면 `[]`. (4) 픽스처 선언 규칙을 작성 전 실측 7에 적음(합성 toy = `{}`, library 부분 netlist = 그 회로 선언 중 나오는 넷, `direction` 없음, 연결 파일엔 넣지 않음, `test_s013`은 `_rsl_meta["ports"]`). 재측정: 그 규칙으로 보강한 사본에서 새 실패 0, 기대값 변경 0 → DEC-40·V5 대상 아님(§3.4) |
| **B3** red 모양 | `try/except Exception: pytest.fail` 권고 삭제, 세탁 금지와 V4 규칙 (3)을 명시. 새 키워드 직접 호출은 `TypeError` → red 아님(B26-1 V2 선례). 계약 2 = `assert "ports" in meta`. 계약 5 = 독립 base red 없음을 정직하게 적고, 증거는 auditor E3 차이표 + 호출 그래프(판정 기록 두 종류 분리). 계약 8 = 첫 줄 `orig = M.port_declaration`(실측: base `AttributeError` `obj` 있음, `name == "port_declaration"`) |
| **S1** 확인 1 = 회로 해석 | 승인 문안을 "유도가 이름 의존이라 무효 → 자동 채움을 비운다(값의 옳고 그름은 6a J ratify)"로 바꾸고 '틀린 값이 새로 생기지 않는다'·'오분류 결과' 판정 문장 삭제. '확인 사안' 표현 삭제 → Q1(동작 변경)·Q2(`ports` 근거) 둘 다 승인 사안. Q2에 회로별 근거 표(파일 주석·추가 커밋 메시지 -- UTF-8로 다시 읽음)를 붙임. 의도 절의 "파일별 `_comment`의 '사용자 확정'" 문장 정정 |
| **S2** 출력은 포트만 | 결정 항목·승인 기록에서 삭제, "B37b card의 결정 항목"으로 이동. 범위 밖 B37b에 "실효 출력 = 포트 ∪ `HINT_OUT` SIGNAL 넷(B37b까지)"을 사실로만 적음 |
| **S3** V3 / A1 | A1 승인(a: 면제 묶기, b: N2)을 규칙으로 명시하고 두 게이트 card 병합을 착수 조건 3으로. N2 대상을 `classify`로 다시 셈(§3.3): 659 → **81**(감싸는 `for rel_path in linked:`·`if "input_offset_pairs" not in entry:`·`if topology_path not in cache:`, 삭제 지점 뒤 문장, `early_return` 포함). 묶기 효과(B26-1 면제 비승계, 겹칠 수 있는 곳)를 'V3 계획' 2에 적음. 결정 항목 2를 "N2 생존이 남을 때만 새 결정"으로 정정. 모의 판정으로 생존 1개를 찾아 Q3로 올림 |
| **S4** B26-1 겹침 | 1: 경로 3 `refine_…(transistors, ports.inputs, ports.outputs, rails=rails)`, E1·E2 호출의 `rails=` 병기. 2: `port ∩ meta["rails"].nets` 거부(범위 2·계약 6). 3: `test_s013` 둘째 호출 = 같은 test 첫 호출의 `_rsl_meta["ports"]`(판정 영향 없음). 4: 계약 5 호출 `meta["device_roles"] or {}`. 5: E2 차동 간선이 B37a로 처음 켜진다 → 착수 시 재측정 필수(계약 9 '표를 잰 base') |
| **S5** 재측정 범위 | 착수 시 1(a)(b)(c)(e)·7 전부 재측정, 표를 잰 base 커밋을 승인 기록에 적고, 다르면 멈춤(계약 9·착수 조건 4·승인 기록 초안). v2 표는 `7535799`에서 다시 잼(§3.2 -- v1 표와 같음) |
| **S6** MG2 | 합성 기본형 `ports`에서 `direction` 삭제(role만), `direction` 케이스(계약 1·6·7)에만 넣고 MG2 몫으로 적음. 원칙 절의 "MG2 몫 = 키 삭제·옛 키 거부"를 "+ 접근자 `direction` 일치 분기를 거부로 바꾸는 수정 1건"으로 정정 |
| M1 | 3292 → 3293(의도 표 E2 행·작성 전 실측 1(a)) |
| M2 | `references/analog-grammar-integration.md` §5(147~155) 정정을 오케스트레이터 문서 커밋 목록·계획서 소비자에 추가(실측: `ports = topo["ports"]  # load_topology()가 이미 파싱하는 그 dict` + `direction` 읽기) |
| M3 | B3 처리로 해소(try 권고 삭제, V4 (3) 명시) |
| M4 | 레지스트리 새 행 비고에 "GB0 로드 게이트(계획 314행)는 이 접근자를 재사용 -- DUP 금지" |
| M5 | 연결 파일 픽스처 규칙(넣지 않음 / 넣으면 진입 파일과 같게)을 작성 전 실측 7에 적음 |

## 2. 범위·계약 변경 요약(v1 → v2)

* 범위 1: 접근자 = 형식 검사만, `{}` 수용, 빈 넷 이름 거부, docstring '검사하지 않는 것'(존재·레일).
* 범위 2: `load_topology`에 존재 검사(트랜지스터·수동소자·이상원 단자, 진입 + 연결 파일)와 레일 겹침 검사 추가.
* 범위 3: 경로 3 호출에 `rails=rails`(B26-1 뒤 모양).
* 범위 4: '입력 0 + offset 쌍' 거부 유지(조건 변경), offset 쌍 0이면 `[]`.
* 계약 3: library 레일 밖 전부 / 합성 포트만, 정규식 import 없음.
* 계약 4: `meta["device_roles"]` 반영(M1~M6 `S1`, M0 없음) 추가 -- mutrun 생존(vsid 반영 루프)에서 나옴.
* 계약 5: 호출 모양 `or {}`·`rails=`, (b) 신설(sf_pushpull E3 값 고정, Q3에 달림).
* 계약 6: 거부 = 접근자 9 + `load_topology` 2 + 연결 2. 수용 = 단일 7(그중 수동소자·이상원 단자에만 있는 포트 2 -- mutrun 생존에서 나옴) + 연결 3(연결 파일 수동소자 단자 포트 -- mutrun 생존에서 나옴).
* 계약 7: `{}` + offset 쌍 거부, `{}` + 쌍 없음 `[]`, 이름 1개 offset 항목은 쌍 아님(mutrun 생존에서 나옴).
* 계약 8: 계수 래퍼 모양.
* 결정 항목: Q1·Q2·Q3, 확인 2 삭제, V3 문장 정정, 착수 조건 4개.

## 3. 실측(모의 head v2)

모의 head = `7535799` + 범위 1~4 v2(`make_head.py`). B26-1 전이라 레일 겹침은 raw `supply_nets`, CC-4a 전이라 거부는 `ValueError`로 대역. 치환 대상 횟수 assert, import 경로 assert.

### 3.1 계약(`contracts.py`, base/head 새 프로세스)

| 항목 | base | head |
|---|---|---|
| 계약 3 library(레일 밖 전부, 5~35넷) | 6/9(current_reuse 8·ngcc 5·pushpull 4) | **9/9** |
| 계약 3 합성(포트만, 2단 OTA·`tele`) | 각 3결과 | 각 1결과 |
| B1 반례 `nc` → `in2` | 다름 | **다름**(계약 아님 확인) |
| 계약 4 | `{M3,M5}`, `device_roles` S1 = M1·M3·M5 | `{M2..M6}`, S1 = M1~M6 |
| 계약 5 | `KeyError: 'ports'`(base 시그니처 관찰은 v1과 같음) | 4변형 모두 단독 |
| 계약 6 거부 13 | 전부 받음 | 전부 거부(`ports`·`DEC-62`). 접근자 직접: 9 거부, 존재·레일 2 수용 |
| 계약 6 수용 10 | -- | 전부 받음 |
| 계약 7 | 무 `direction` `[]`, `{}`는 쌍 유무 무관 `ValueError` | `[[M1,M2]]` 둘 다, `{}`+쌍 거부, `{}`+무쌍 `[]`, 이름 1개 `[]` |
| 계약 8 | `AttributeError`(`obj` 있음, `name` = `port_declaration`) | 1 → 2 → 2 |

### 3.2 동작 보존(`measure.py --specs`, `compare.py`, base `7535799`)

E-LIB 5회로 차이 = v1 표와 소자·필드까지 같음. E3 3회로 = v1 표와 같음(sf_pushpull 전체 그룹을 표에 추가). audit 9/9·offset 9/9·SPECS 4회로(metric `float.hex`·sized 해시·거부 문구) 같음. library에서 존재·레일·입력 0 거부 무발동(`lib_ports.py`: 포트 넷 9/9 단자에 있음, 레일 겹침 0, 입력 ≥ 1 9/9).

### 3.3 V3(N2, `v3_b37a.py`·`mutrun.py`·`mkmut.py`)

| def | 지금 규칙 | N2 |
|---|---|---|
| `port_declaration`(새) | 27 | 27 |
| `load_topology` | 77 | 27 |
| `input_referred_offset_pairs` | 22 | 16 |
| `_load_full_topology_cached` | 10 | 4 |
| `resolve_stack_layout` | 26 | 4 |
| `_build_theta_evaluator` | 497 | 3 |
| 합 | 659 | **81** |

* v1 근사 35와 차이: 감싸는 복합문 3개, 삭제 지점 뒤 문장(T6), `early_return`(T5), v2 범위의 새 문장.
* 모의 판정(변이마다 새 프로세스, contracts 출력 또는 folded_cascode 평가가 head와 다르면 죽음): 1차 75/81. 생존 6 중 4개는 계약 4·6·7 케이스 추가로 죽음(2차). 남은 2개를 `head_fx`에 넣고 기존 test 전체 실행: `cmp_flip`은 `test_s003`이 죽임, **경로 3 분기 `stmt_delete`는 생존**(등가 아님 -- sf_pushpull 결과가 바뀜). → 계약 5(b) + Q3.
* 참고: vsid 반영 루프 삭제는 기존 test(`test_s049`·`test_s154`·probe 6건)도 죽인다.

### 3.4 pytest(판정 설정, `run_pt.py`)

| 사본 | 결과 | base 대비 |
|---|---|---|
| base | 2 failed·796 passed·15 xfailed | (사본에 git 이력이 없어 `test_ts6_probe_relocate` 2건 -- v1·검토의 42 failed와 다른 것은 사본 환경 차이) |
| head(보강 없음) | 15 failed·4 errors·779 passed | 새 실패 **17**(v1의 18에서 s125 빠짐 -- 이미 `ports: {}`) |
| **head_fx**(규칙대로 보강) | 2 failed·796 passed·15 xfailed | **새 실패 0**. 보강 diff = 입력 픽스처 18줄, assert·기대값·메시지 변경 0 |
| base_fx(같은 보강, base 코드) | 3 failed | + `test_s013` `KeyError: 'ports'`(base에 없는 키 -- 'V3 계획' 5) |

→ "기대값 변경 0, DEC-40·V5 대상 아님"은 가짜 넷 없이 성립한다. 기대값이 바뀌는 곳은 없다(V5/DEC-40 표시 대상 0).

### 3.5 머리 블록

`role_paths.parse_spec_card(text, "20260930-b37a-ports-roles")` 통과: `phase 4`, `evidence_type red-green`, `gate_change no`, `approval ['20260930-b37a-ports-roles']`. 절 12개(의도 ~ 작성 전 실측).

## 4. 사용자에게 올릴 것(오케스트레이터)

`_drafts/draft_b37a_approval_question.md`:
* **Q1** 동작 변경 수용(E-LIB 5회로·E3 3회로 표). 값의 옳고 그름은 6a.
* **Q2** `ports` 선언 확인 -- ngcc·sf_pushpull·two_stage_ota_sf(동작이 바뀜), pushpull·common_gate(선언이 판정 입력이 됨). 파일 주석 없음 / 커밋 메시지의 "사용자 확정 넷 표"에 role이 들어 있었는지 확인 불가.
* **Q3** sf_pushpull E3 값 test 고정(기본안) 또는 비등가 변이 면제(약화).

## 5. 남긴 관찰(이 card 밖)

* sf_pushpull의 `resolve_stack_layout` 경로 3 결과에 base·head 모두 M1~M4가 어느 그룹에도 없다(반환 그룹이 소자 전체를 덮지 않음). 기존 동작 -- 백로그 후보.
* 검토의 `two_stage_ota` 주석 분류('목적 설명만')는 일부 부정확하다: 출력 포트 `OUT` 추가에 '사용자 확정'이 있다(입력은 목적 설명). Q2 표에 반영.
