# 독립 검증 -- TS6 '(다+핀)' 선택지 (p4_ts6_question.md, draft_p4_first.spec.md 계약 8 (A)/(A2)/(B))

검증자: 작성자 아님(작성자 스크립트 `mkT.py`·`attack.py` 등은 삭제됨 -- 계약 8 문장만으로 독립 구현).
판: gate `master` `4a286f0fad4f9beafd26647e1f95a89086e07919`, 2026-10-02. 격리 복제본 `C:/g233/w`(`git clone -c core.autocrlf=false -c core.hooksPath= --no-local`, origin 제거, detached `4a286f0`), 얕은 경계 실험용 `C:/g233/sh`, TMP/TEMP = `C:/g233/tmp`. python `C:\Python314\python.exe -B`, pytest 9.0.2, gate `tools/gates/pytest_gate.ini`, `--rootdir`/`--confcutdir` = 복제본, `--gmid-phase=2`.
실제 저장소: 읽기 전용(`git -C`만). 시작·끝 HEAD `4a286f0`, `status --porcelain` md5 `dcc7b56b…` 같음, reflog 345줄·머리 md5 같음. 끝난 뒤 `C:/g233` 삭제(측정 스크립트도 같이 삭제 -- 아래에 정의를 원문으로 남긴다).

## 결론

**표 수치는 재현됨. 그러나 질문 문안의 (다+핀) 설명은 보호 범위를 과대 표시한다 -- 문안 수정 후 질문(차단 1건 = S1).**
계약 문장은 test-author가 같은 판정을 내도록 구현하기에 **대체로 충분**(아래 모호점 4건은 이번 표본에서 판정을 바꾸지 않음 -- minor).

## 1. 재현 결과 (비교표)

순서 II(F1 먼저): S0 = 지금 도구(F1 T만), S1 = F1 모양(`f12_f1sim.py` 규칙 (2): `import sizing_recipe as sr` → `import circuit_state_graph as _f1_circuit_state_graph` 등 별칭 import 셋, `sr.` 4곳 → 목적지 별칭), S2 = S1 + #2 K(계약 5, card D1의 15쌍 원문 그대로). 순서 I = 지금 도구 + #2 K.

| 안 | S0 | S1 | S2 | 순서 I 병합본 | 7종 검출(S1) | 문구·구분선 | 비고 |
|---|---|---|---|---|---|---|---|
| 지금 test | PASS | FAIL 12 | FAIL 23 | FAIL 15 | 7/7 | FAIL | 표와 같음 |
| (다+핀) | PASS | PASS | PASS | PASS | 7/7 | PASS | 표와 같음 |
| (가) 기준선+F1 치환 | FAIL 12 | PASS | FAIL 15 | (FAIL 23) | 7/7 | FAIL | 표와 같음 |
| (나) 허용 문장 | PASS | PASS | FAIL 13 | (FAIL 13) | 5/7(3a·3d 놓침) | FAIL | 표와 같음 |
| (다) 이동 커밋만 | PASS | PASS | PASS | PASS | 0/7 | PASS | 표와 같음 |

* pytest(독립 구현을 복제본 TS6 파일의 기존 함수 안에 넣음, 새 id 0): 지금 도구·S1·S2·순서 I 병합본 모두 **33 passed**, 수집 id 33개 정렬 sha256 앞 12자 `c66e04745a4a` 패치 전후 같음. 대조: S1+3a 변이 → `1 failed, 32 passed`(그 함수), S1+N2 변이(아래) → **33 passed**.
* (A1) 구조 확인: `9d6800e` 통과(부모 `a574f97` 하나, 부모 tree에 새 자리 없음, HEAD 조상, blob = HEAD 도구 바이트 동일, `non_path_line_changes(939f926 blob, 이동 blob) = []`). `36e170e` 거부(부모에 새 자리 있음), `a574f97` 거부((d) 새 자리 blob 없음), 얕은 경계(`.git/shallow` = `9d6800e`) 거부(부모 0개 → '정확히 하나' 위반, 닫힘).
* 계약 (A2) 합성 표본(base blob): 바꿀 문자열 각 1회 확인, 5종 거부(`call`·`record`·`call`·`targets`·`record`), import 줄·출력 문구 2종 수용 -- 계약대로.
* 추가 F1 모양(from-import, 맨 이름 호출 -- 규칙 (2) 밖이지만 F1이 고를 수 있는 모양): (다+핀) S1'·S2' PASS(정규화가 `sr.X`를 `Name(X)`로 바꾸므로 맨 이름과 같아짐). (가) FAIL 14·(나) FAIL 7 -- (가)·(나)는 F1 모양에 민감.

## 2. 새 변이 -- 핀의 사각 (S1 위, 모두 선언 `value`·`_derived` 기록 또는 유도 입력을 바꾸는 변경)

| # | 변이 | (다+핀) | (가) | (나) | (다) |
|---|---|---|---|---|---|
| N1 | 다른 모듈의 같은 이름 함수 호출(`import sizing_recipe_legacy as _legacy` + `_legacy.achievable_metric_bound(…)`) | **PASS** | FAIL | FAIL | PASS |
| N1b | 호출 대상을 기존 별칭 `H.achievable_metric_bound`로 | **PASS** | FAIL | FAIL | PASS |
| N2 | 기록 가드 `if wrote:` → `if wrote and False:`(선언 파일 안 씀) | **PASS** | FAIL | FAIL | PASS |
| N3 | 루프 안 비대입 문장 `r.update(conservative=r["best"])` | **PASS** | FAIL | FAIL | PASS |
| N4 | 루프 사이 `book[fp].clear()` | **PASS** | FAIL | FAIL | PASS |
| N5 | `cons = (…)[:1]`(제약 일부만) | **PASS** | FAIL | FAIL | PASS |
| N6 | `spec = dict(H.canonical_spec(key), n_starts=1)` | **PASS** | FAIL | FAIL | PASS |
| N7 | `if not targets:` → `if targets:` | **PASS** | FAIL | FAIL | PASS |
| N8 | `targets[:] = targets[:1]`(대입 대상이 Subscript) | **PASS** | FAIL | FAIL | PASS |
| N8b | `targets += [("gain_db", "max")]`(AugAssign) | **PASS** | FAIL | FAIL | PASS |
| N9 | `topo_doc` 읽은 뒤 `constraints = []`(빈 선언을 덮어씀) | **PASS** | FAIL | FAIL | PASS |
| N10 | 순서 바꾸기: `if wrote:` 쓰기 블록을 기록 루프 앞으로 | **PASS** | FAIL | FAIL | PASS |
| N11 | `json.dump(topo_doc…)` → `H.dump(topo_doc…)`(별칭 정규화가 모듈을 지움) | **PASS** | FAIL | FAIL | PASS |
| N12 | 루프 앞 `H.SPECS[key]["slsqp_kwargs"] = None` | **PASS** | FAIL | FAIL | PASS |
| N16 | `r = dict(<핀 호출 그대로>, conservative=-1.0)` | **PASS** | FAIL | PASS | PASS |
| N17 | 핀 호출 뒤 `r = …load_derived_bounds(topo)`로 덮음(Try 안 -- 루프 '직속' 아님) | **PASS** | FAIL | PASS | PASS |
| 검출 계 | | **0/16** | 16/16 | 14/16 | 0/16 |

대조군(핀이 실제로 닫는 것): 기록 For 안 문장 추가 → FAIL(`record`), `fp` 중복 → FAIL(개수 2), 기록 For 복제 → FAIL(개수 2). 경로 줄 변경(`topo` 경로)은 모든 안이 PASS(설계상 허용 -- 범위 밖).
합계(7종 + 새 16종): **(다+핀) 7/23, (가) 23/23, (나) 19/23, (다) 0/23**.

참고 측정(계약 밖 변형, 결정용 정보):
* 별칭 정규화를 엔진 모듈 별칭(`sizing_recipe`·Phase 3 목적지)으로만 좁힘 → N11만 추가 검출(1/16). 표 단계 결과 불변.
* 전체 모듈 정규화 비교(docstring·`emit()` 인자·import 문·경로 문장만 뺀 `ast.dump`) → S0·S1·from-import PASS, 문구·구분선 PASS, 7/7 + 13/16(N1·N1b·N11만 놓침), **단 S2·순서 I FAIL**(#2가 `book` 시작 줄·사이드카 블록을 바꾸므로 #2에서 한 번 V5). 즉 (가)·(나)보다 test-first·문구 무관에서 낫고, (다+핀)보다 보호가 크며, 비용은 #2 V5 한 번.

## 3. 판정

**S1(차단 -- 질문 문안).** 질문의 (다+핀) 설명 "실측: 계산을 바꾸는 변이 7종 모두 잡고 … 핀 밖(문구·구분선 등)은 사람 diff 검토로만"은 사용자에게 핀이 계산·기록 전체를 지킨다는 인상을 준다. 7종은 모두 핀 6요소 **안**을 건드리는 변이로 골라졌고(선택 편향), 핀 밖 줄로 선언 기록을 바꾸는 변경은 16종 중 0종 검출이다(기록 가드 끄기·입력 준비 줄·루프 안 비대입 문장·순서·호출 대상 모듈). '잃는 보호'를 문구·구분선으로만 적으면 V5 '약화' 승인 범위 설명이 사실과 다르다. 같은 과대 표시가 spec 계약 5(41행 "계산·탐색 인자·선언 기록 블록은 계약 8 핀이 기계로 지키고")와 D1 (5)(129행 "핀 밖(docstring·출력 문구·`book` 시작 줄·사이드카 블록·`emit` 구분선)은 기계 보호가 없다")에도 있다 -- 같이 고칠 것.
**minor 1(계약 정밀도).** 독립 구현으로 같은 판정을 냈지만 아래는 문장이 정하지 않는다(이번 표본에서 판정 불변):
 (a) 정규화의 바꾼 노드 모양(`Name(id=<이름>, ctx=원래 ctx)`로 명시 권고 -- from-import F1 모양과 같아지는 근거), (b) `from … import` 이 '모듈 별칭'에 드는지(이 도구는 무관), (c) (3) `fp`가 단일 대상만인지((2)는 '하나에'라고 적음), (d) (4) '직속 Assign 문들'의 비교가 순서 있는 목록인지.
**minor 2(표본).** (A2) 수용 표본 `import sizing_recipe as sr` → `import theta_search as sr`는 별칭 `sr`가 그대로라 정규화를 시험하지 않는다 -- 별칭 이름이 바뀌는 F1 모양(`_f1_<목적지>` 셋 또는 from-import) 수용 표본을 하나 더 두는 것을 권고(실측 둘 다 PASS).
**minor 3.** `c["_derived"] = {` '기록 제거' 표본은 바꿀 문자열 1회 단언 뒤 지울 범위(5줄 문장 전체)를 문장이 정하지 않는다 -- 'AST 문장 전체 삭제'로 적을 것.
V5(`weakening_diff`) 발견 수는 이번에 다시 재지 않았다(표·변이 범위 밖).

## 4. 고친 AskUserQuestion 문안 (권고)

권고 선택은 (다+핀) 그대로 둘 수 있다(test-first, F1·#2 재수정 0이 측정으로 맞음). 다만 잃는 보호를 수치로 드러낸다. 오케스트레이터가 위 '전체 모듈 정규화 핀'을 계약으로 만들 의사가 있으면 질문 전에 card를 고쳐 선택지로 넣는 것이 낫다(지금 계약 밖이라 여기 넣지 않음).

* header: `[F1·#2] TS6` (11자)
* multiSelect: false
* question:
  "[F1·#2] Phase 3 F1은 tests/tools/derive_achievable_bounds.py의 `import sizing_recipe as sr`와 `sr.` 속성 줄을, Phase 4 #2는 같은 도구의 사이드카 읽기·쓰기 줄을 바꿉니다. TS6 이동 계약 test(test_moved_tool_matches_base_except_path_lines)는 지금 도구가 2026-09-23 이동 원본과 경로 줄 밖에서 한 글자도 다르지 않기를 요구해 두 card 모두에서 실패합니다(F1 12줄, F1+#2 23줄). 어느 안도 지금보다 약하고(V5 약화 승인), 아래 '검출'은 계산·기록을 바꾸는 변경 23종(핀 요소 안 7 + 핀 밖 16) 실측입니다. F1 test 커밋에서 이 test를 어떻게 바꿀까요? (한 번만 묻고 #2는 이 답을 따릅니다)"
* options:
  1. label: **"(다+핀) 이동 커밋 + 핵심 핀 (Recommended)"**
     description: "이동 사실은 이동 커밋(9d6800e)을 원본과 비교해 계속 판정하고, 지금 도구는 6요소(achievable_metric_bound 호출 인자, targets·fp 대입, 루프 직속 대입, value·_derived 기록 루프, 선언 파일 쓰기 with)만 AST로 고정합니다. 검출 7/23: 6요소 안 변경 7종은 모두 잡지만, 6요소 밖 줄로 기록을 바꾸는 변경(기록 가드 끄기, 입력 준비 줄, 루프 안 대입 아닌 문장, 문장 순서, 호출 대상 모듈 바꾸기) 16종은 하나도 못 잡습니다 -- 그 범위는 사람 diff 검토뿐. F1·#2 모두 통과(test 먼저 작성 가능), 문구·import 변경 통과, 이후 재수정 없음."
  2. label: "(가) 기준선에 F1 치환 반영"
     description: "비교 기준을 '이동 원본 + F1 import 치환'으로 바꾸고 그 밖 줄은 지금처럼 전부 고정합니다. 검출 23/23(경로 줄 밖 전부). 그러나 F1 test를 F1 이전 도구에 얹으면 실패(12줄)해 test를 먼저 쓸 수 없고, F1이 다른 import 모양(from-import)을 고르면 그 치환을 다시 맞춰야 하며, #2에서 다시 실패(15줄)해 #2가 기준선을 고치고 V5를 다시 받습니다. 문구 한 글자도 막습니다."
  3. label: "(나) 허용 줄에 import 문장 추가"
     description: "경로 줄 정의에 엔진 모듈 import 문과 그 별칭 속성을 담은 문장을 더합니다. 검출 19/23(achievable_metric_bound 호출 문장 전체가 허용되어 sense 강제·탐색 인자 무시·호출 결과 덮어쓰기를 놓침). F1 통과(test 먼저 가능), #2에서 다시 실패(13줄)해 V5를 다시 받고, 이후 문구 변경마다 실패합니다."
  4. label: "(다) 이동 커밋끼리만 대조"
     description: "이동 커밋(9d6800e)의 도구만 원본과 비교합니다. 이동 사실 판정은 남지만 지금 도구는 어떤 test도 보지 않아(검출 0/23), 이후 어떤 도구 변경으로도 이 test는 실패하지 않습니다. F1·#2 모두 재수정이 없고 가장 단순합니다."

비교표 절(`p4_ts6_question.md`)에 넣을 줄: "변이 검출(23종)" 열 = (다+핀) 7/23, (가) 23/23, (나) 19/23, (다) 0/23(지금 test는 S1에서 이미 FAIL이라 새 16종에 대해 따로 재지 않음); '(다+핀)이 잃는 것' 줄에 N1~N17 범주 원문 추가.

## 5. 측정 정의(스크립트 삭제 전 원문 -- 재현용)

* 핀 독립 구현: 최상위 `ast.Import` 별칭 집합 → `Attribute(Name(별칭), x)`를 `Name(x, 원래 ctx)`로 → `ast.walk`로 6요소 수집, 요소마다 개수 1 + `ast.dump` 같음. `call` = (args dump 목록, keywords dump 목록)(호출 대상 식 제외 -- 계약 문장대로), `loop` = (For.target dump, 직속 Assign dump 순서 목록).
* (가) = `non_path_line_changes(F1(base blob), 도구)`, (나) = 허용 줄 = 경로 줄 ∪ 엔진 모듈(`sizing_recipe`·`topology_library`·`design_report`·`stick_diagram`·`circuit_state_graph`·`sizing_layout_convergence`·`theta_search`) import 문 ∪ 그 별칭 속성을 담은 단순 문장 전체 줄.
* 7종 원문은 card D1 (2)와 같은 치환(3c는 5줄 문장 전체 삭제, x3은 `with open(topo, "w"…)` 3줄 삭제).
