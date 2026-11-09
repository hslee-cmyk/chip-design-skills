# 독립 검증 -- TS6 '(마) 모듈 전체 정규화 핀' (draft_p4_first.spec.md 계약 8 (A1)·(A3)·계약 5, p4_ts6_question.md)

검증자: 작성자 아님. 작성자 측정 스크립트는 삭제되어 있어 **계약 8 (A1)·(A3) 문장만으로 독립 구현**했다(아래 §6에 정의 원문).
판: gate `master` `4a286f0fad4f9beafd26647e1f95a89086e07919`, 2026-10-02. 격리 복제본 `C:/g243/w`(작업 저장소 working tree에서 `git clone -q --no-local -c core.autocrlf=false -c core.hooksPath=`, `4a286f0` detached, origin 제거), TMP/TEMP = `C:/g243/tmp`, python `C:\Python314\python.exe -B`, gate `tools/gates/pytest_gate.ini`, `--rootdir`/`--confcutdir` = 복제본, `--gmid-phase=2`.
실제 저장소: 읽기 전용(`git -C`만). 시작·끝 HEAD `4a286f0`, `status --porcelain` md5 `dcc7b56b0dc2…` 같음, reflog 345줄·md5 `1bb04b5e…` 같음. 끝난 뒤 `C:/g243`만 삭제.

## 결론

**표·V5 수치는 모두 재현됨. 그러나 (마) 계약에 새 사각 1건(차단급 -- 계약 한 줄 수정으로 닫힘)과 문안 과대 표시 1건이 있다 -- 계약 2 (c) 수정 + 문안 수정 후 질문.**

* **S1(차단 -- 계약·문안)**: 정규형 2 (c) '엔진 import 빼기'가 **모든 문장 목록**(중첩 포함)에 적용되는데 1 별칭표는 **최상위만** 본다. 그래서 루프 안에 `import stick_diagram as <기존 엔진 별칭>`(또는 from-import 모양이면 `from <엔진> import <다른 함수> as achievable_metric_bound`)을 넣어 호출 대상을 바꿔도 정규형이 같다 -- **묶지 않는 모듈(stick_diagram)이어도, 다른 정의 모듈이어도 통과**(S1·S1f·S2 모두 실측). 실행 시 `AttributeError`가 루프의 `except Exception`에 잡혀 '유도 실패'로 넘어가므로 선언 기록이 조용히 빠진다. 지금 test는 이 줄을 비경로 줄로 거부한다 → (마)가 **새로 잃는 보호**인데 계약 '남는 사각'·문안 '잃는 것'에 없고, 문안의 "(+ 다른 엔진 모듈 별칭으로 호출 바꾸기 … 잡음)"은 최상위 별칭에서만 참이다.
  **수정(실측)**: 2 (c)를 **모듈 최상위 문장만**으로 좁힌다(중첩 엔진 import는 남아 비교된다). 이 변형으로 S0·S1·S1f·S2 판정, 23종 검출(S1 23/23·S1f 21/21·S2 23/23), 수용 표본 4종(주석·docstring·구분선·경로 문장 추가) 모두 그대로이고 중첩 import 공격 4종이 전부 검출로 바뀐다(이 도구에는 중첩 import가 없다).
* minor 1~4는 §4(계약 정밀도 -- 독립 구현 사이 판정이 갈릴 수 있는 곳), V5 gate 결함 1건은 §5(백로그 권고).

## 1. 비교표 재현 (순서 II = F1 T → F1 K → #2, 괄호 = 비경로 줄 수)

도구 모양: S0 = `4a286f0` 도구, S1 = F1 별칭 셋(`f12_f1sim.py` 규칙 (2): `import sizing_recipe as sr` → `import circuit_state_graph as _f1_circuit_state_graph` / `sizing_layout_convergence` / `theta_search` 셋(정렬), `sr.X` → `_f1_<목적지>.X`, 목적지 = `spec_fingerprint`→circuit_state_graph, `achievable_metric_bound`→sizing_layout_convergence, 사이드카 두 함수→theta_search), S1f = 같은 목적지 from-import 셋 + `sr.` 지움, S2 = S1 + #2 K(계약 5 전체: docstring 3곳·emit 문구·`book = {fp: {}}`·세 문장 삭제), S2f = S1f + #2 K, S2b·S2fb = theta_search import까지 지운 판, I-K = S0 + #2 K. 목적지 모듈은 재수출 stub(`from sizing_recipe import …`).

| 안 | S0 | S1 | S1f | S2 | S2f | I-K | 표와 |
|---|---|---|---|---|---|---|---|
| 지금 test | PASS | FAIL(12) | FAIL(12) | FAIL(23) | FAIL(23) | FAIL(15) | 같음 |
| (마) F1 핀(편집 0) | PASS | PASS | PASS | FAIL | FAIL | FAIL | 같음 |
| (마) #2 핀(E_#2) | PASS | PASS | PASS | PASS | PASS | PASS | 같음(S2b·S2fb도 PASS) |
| (다+핀) | PASS | PASS | PASS | PASS | PASS | PASS | 같음 |
| (가) 기준선+F1 치환 | FAIL(12) | PASS | FAIL(14) | FAIL(15) | FAIL(25) | FAIL(23) | 같음 |
| (나) 허용 문장 | PASS | PASS | (FAIL 4) | FAIL(13) | -- | FAIL(13) | 같음(S1f는 표에 '--') |
| (다) | PASS | PASS | PASS | PASS | PASS | PASS | 같음 |

**실제 pytest(TS6 파일, 독립 구현을 기존 함수 안에 넣음, 새 id 0)**: base `4a286f0` · F1 T(편집 0·정수 0) · F1 K 별칭 · F1 K from-import · #2 T(E_#2·정수 2) · #2 병합본(별칭·from-import, theta import 삭제판 포함) · 순서 I T(편집 2로 바로) · 순서 I 병합본 = 모두 **33 passed**. T 없는 #2 K(F1 K 위)·순서 I에서 T 없는 K = **1 failed, 32 passed**(실패 = `test_moved_tool_matches_base_except_path_lines`). 수집 id 33개 정렬 목록 sha256(`tests/contracts/` 뒤 id 문자열) `251db052c443` 전 단계 같음.
(질문 노트의 `c66e04745a4a`는 같은 집합의 다른 문자열 형식 해시로 보인다 -- r2는 `251db052…`. 집합 안정성 주장은 맞지만 형식 없이 해시를 옮겨 적지 말 것.)
(A1) 거부 표본 `36e170e`·`a574f97`은 같은 함수 안에서 거부됨(pytest green). 얕은 복제 경계는 이번에 다시 재지 않았다(계약 (A1) 문장 r2 판과 같음).

## 2. 변이 검출

23종(독립 검증 `review_ts6_pin.md` 설명대로 재구성; N9 = `topo_doc["sizing_roles"]["constraints"] = []`):

| 판 | (마) | (다+핀) | (가) | (나) | 지금 test |
|---|---|---|---|---|---|
| S1 | **23/23** | 7/23 | 23/23 | 19/23 | 23/23 |
| S1f(N1·N1b 적용 불가) | 21/21 | 7/21 | 21/21 | 21/21 | 21/21 |
| S2 + E_#2 핀 | 23/23 | 7/23 | -- | -- | -- |

(card '작성 전 실측' 17의 "from-import 20/20(3종 제외)", "#2 병합본 22/22(N1 기준 줄 없음)"과 적용 가능 수만 다르다 -- 내 S2에는 `import run_harness as H` 기준 줄이 있어 N1을 적용했다. 판정은 전부 검출로 같음.)
추가 표본(작성자 주장): N1c(묶지 않는 엔진 모듈 최상위 별칭) 검출, 엔진 아닌 import 바꾸기(`run_harness`→`run_harness_v2`) 검출, 새 `emit` 문장으로 부수효과 검출 -- 재현.

### 내 공격((마)의 사각 겨냥, S1·S1f·S2 공통 결과)

| # | 공격 | (마) | 지금 test | 남는 사각 목록에 | 판정 |
|---|---|---|---|---|---|
| NEW-1 | 루프 안 `import stick_diagram as _f1_sizing_layout_convergence`(묶지 않는 모듈로 별칭 가리기) | **통과** | 거부 | **없음** | **S1 -- 새 사각(계약 2 (c) 범위)** |
| NEW-1b | 루프 안 `import evil_eng as …`(같은 이름 다른 정의 새 엔진 모듈) | **통과** | 거부 | 없음 | 같음 |
| NEW-1c/1d | from-import 모양에서 루프 안 `from stick_diagram import find_hub_merge_candidates as achievable_metric_bound` / `from evil_eng import achievable_metric_bound` | **통과** | 거부 | 없음 | 같음 |
| NEW-2 | 최상위에 같은 별칭을 두 번(`import stick_diagram as <별칭>`을 뒤에) | 검출(내 구현: 뒤가 이김) | 거부 | -- | **minor 1(계약이 정하지 않음 -- 앞이 이기게 구현하면 통과)** |
| NEW-3 | 최상위 `if True:` 안 엔진 import 추가 | 검출(빈 `If`가 남음) | 거부 | -- | 정상 |
| P1 | 새 문장 `targets = targets[:1] if os.path.isfile(topo) else targets` | **통과** | **통과** | '경로 문장' 범주 | 지금 test와 같은 사각(정의상 -- 문안 정밀도 minor 3) |
| P2 | 루프 안 새 문장 `os.path.isfile(topo) and r.update(conservative=r["best"])` | **통과** | **통과** | 같음 | 같음 |
| P3 | 기존 경로 문장 값 바꾸기(`topo`를 다른 파일로) | 통과 | 통과 | 있음 | 설계상 |
| P4 | 기존 비경로 문장을 `os.path` 호출로 감싸 교체 | 검출 | 거부 | -- | 정상(핀 쪽 문장이 남아 다름) |
| F1~F3 | 기존 `emit` f-string 안 부수효과 식 / walrus로 `targets` 자르기 / 기존 `emit` 인자를 부수효과 호출로 교체 | 통과 | 거부 | 있음('그 안의 식') | 설계상 |
| F4 | `def emit` 안 `print(line, flush=True)` 인자에 `file=open(…)` | 통과 | 거부 | 있음(`print` 인자) | 설계상 -- `emit` 정의 본문의 `print`도 빠진다는 점은 문안에 없음(minor 3) |
| S1 | 같은 이름을 묶는 다른 엔진 모듈로 최상위 별칭 바꾸기(`sizing_recipe`) | 통과 | 거부 | 있음 | 설계상 |
| S2 | 같은 이름을 다른 정의로 묶는 새 엔진 모듈(`evil_eng.py`)로 최상위 별칭 | 통과 | 거부 | 있음(R-DEF 위반 몫) | 설계상 |
| T1 | 핀 편집 ①만 적용(쓰기 블록 남김) / ②만 적용 | 검출 / 검출 | -- | -- | 정상 |
| T2 | `pin_commit` = 도구 없는 커밋(`a574f97`) / HEAD 조상 아닌 커밋 / 없는 sha / 기준 문자열 15회 | 모두 거부 | -- | -- | 정상(닫힌 쪽) |
| T3 | **가짜 핀 커밋**: 도구를 N2 변이로 바꾼 커밋 X를 만들고 T가 `pin_commit`=X, 편집 `()`, 정수 0으로 → K가 N2 변이 | test **통과**(1 passed) | -- | -- | V5가 1건('리터럴 변경')으로 보임 -- 사람만 거부 가능 |
| T4 | **편집 쌍 변조, 정수 일치**: #2 T가 ①을 `("    if wrote:\n", "    if wrote and False:\n")`로 바꾸고 정수 2 → K가 그 모양 | test **통과**(1 passed) | -- | -- | V5 발견 1건, **정직한 #2 T와 발견 문구가 같다**(detail은 앞 5개·160자만) -- 사람이 diff로 E_#2 원문과 대조해야 함 |

T3·T4는 핀 설계상 예상된 것(핀 수정 = 사람 승인)이고 V5에 모두 보인다. 다만 V5 출력만으로는 정직/변조를 구별할 수 없으므로 승인 기록 범위 설명에 **E_#2 원문 두 쌍과 `pin_commit` 값**을 적게 한 card 결정 항목 (c)가 실질 방어다(그대로 유지 권고 -- `pin_commit` 값도 원문으로 적게 넓힐 것).

## 3. V5(`weakening_diff.py`, 4a286f0 판) -- 작성자 주장 대조

| 범위 | 결과 | 작성자 주장 |
|---|---|---|
| F1 T(base..F1 T) | FAIL, 발견 **2**(같은 단위: '비교 완화', '리터럴 변경') | 2 -- 맞음 |
| F1 K 별칭 / from-import | PASS, 0 / 0 | 0 -- 맞음 |
| #2 T(F1 K..#2 T) | FAIL, 발견 **1**('리터럴 변경' `['0'] -> ['2', "''", …]`) | 1 -- 맞음 |
| #2 K | PASS, 0 | -- |
| 순서 I T | 2 | 같음 |
| 정수 단언 없이 편집 쌍만 삽입 | **PASS, 0** | '삽입은 V5가 보지 않음' -- **맞음** |
| 뒤 card: 정수 그대로 쌍 내용 교체 | 1('리터럴 변경') | -- |
| 뒤 card: 쌍 추가 + 정수 2→3 | 1('리터럴 변경' `['2'] -> ['3', …]`) | -- |
| 가짜 핀 커밋(T3) / 쌍 변조(T4) | 각 1 | -- |

**게이트 동작 확인**: `compare_units`는 상수 SequenceMatcher의 `replace`·`delete`만 발견으로 친다(코드 194~195행). 합성 확인: `for x in (1, 2, 3)` → `(1, 2, 3, 4)`(격자 확대) 발견 0, 모듈 허용 목록 `ALLOW = ("a",)` → `("a", "b")` 발견 0.

## 4. 계약 정밀도(같은 구현이 나오는가)

계약 (A3) 문장으로 독립 구현했고 단계·23종·수용 표본 판정이 작성자 수치와 같았다. 다만 아래는 문장이 정하지 않거나 구현이 갈린다:
* **S1 관련(차단)**: 2 (c)의 적용 범위('모든 문장 목록')와 1 별칭표('최상위만')가 어긋난다 -- §결론 수정안.
* **minor 1**: 별칭표에서 같은 별칭이 최상위에 두 번 묶일 때(뒤가 이김 / 앞이 이김 / 실패) 미정 -- NEW-2 판정이 갈린다. '실행 순서대로 뒤 문장이 덮는다' 또는 '같은 별칭이 둘 이상이면 실패'로 적을 것.
* **minor 2**: binds의 'Assign 대상 안의 `Name`'이 `X[k] = …`의 `X`도 세는지, 최상위 `for` 대상·`with … as` 대상이 묶는 이름을 세는지 미정(이 도구 표본에서는 판정 불변). 2 (a) docstring 판정이 '원래 목록의 첫 문장'인지(경로 문장을 뺀 뒤 첫 문장이 아님) 한 마디.
* **minor 3(문안·계약 '남는 사각' 정밀도)**: (i) '경로 문장'은 `os.path.*` 호출·`sys.path.insert`·절대 경로 문자열을 **담은** 모든 `Assign`/`AnnAssign`/`AugAssign`/`Expr` -- 새로 넣은 계산 문장도 `os.path` 호출 하나로 통째로 빠진다(P1·P2, 지금 test도 같은 허용). (ii) `print` 인자 제거는 `def emit` 본문의 `print`에도 적용된다(F4).
* minor 4: 수용 표본 '별칭 이름 바꾸기'의 `sr.` → `_f1_sr.`는 `\bsr\.` 치환으로 적을 것(단순 `replace("sr.")`는 `_f1_sr.`를 다시 바꾼다 -- 내 첫 구현이 걸렸다).

## 5. V5 게이트 결함 -- 백로그 권고(이 card 차단 아님)

`weakening_diff.py` 자기 docstring 표가 '격자 확대'를 패턴으로 적지만, 상수 **삽입**만으로 이뤄지는 격자 확대·허용 목록 확대는 발견 0이다(§3 합성). TS6 (마)는 정수 리터럴 단언으로 우회했으므로 이 card는 막히지 않는다. 그러나 다른 test의 허용 목록·면제 튜플·격자 늘리기가 V5 없이 통과할 수 있으므로 **백로그 항목으로 둘 가치가 있다**(메모리 '인프라 작업은 gmid 엔진을 막을 때만' -- 지금 고치지 않음). 후보 규칙: `in`/`not in` 비교 오른쪽이나 `for` 반복 대상에 쓰이는 컬렉션 리터럴(또는 그 이름에 묶인 모듈 상수)의 원소 삽입을 '격자·허용 목록 확대'로 보고(새 test 함수·`parametrize` 원소 추가는 제외).

## 6. 고친 AskUserQuestion 문안(권고 -- 계약 2 (c)를 '모듈 최상위 문장만'으로 고친 뒤의 문장)

* header: `[F1·#2] TS6` (11자)
* multiSelect: false
* question:
  "[F1·#2] Phase 3 F1은 tests/tools/derive_achievable_bounds.py의 `import sizing_recipe as sr`와 `sr.` 속성 줄을, Phase 4 #2는 같은 도구의 사이드카 읽기·쓰기 문장을 바꿉니다. TS6 이동 계약 test(test_moved_tool_matches_base_except_path_lines)는 지금 도구가 2026-09-23 이동 원본과 경로 줄 밖에서 한 글자도 다르지 않기를 요구해 두 card 모두에서 실패합니다(F1 12줄, F1+#2 23줄). 아래 네 안은 **모두 지금 test보다 약합니다**(V5 약화 승인 -- 지금 test는 경로 줄 밖 모든 글자를 고정). '검출'은 선언 기록·계산을 바꾸는 변경 23종 실측입니다. F1 test 커밋에서 이 test를 어떻게 바꿀까요? (한 번만 묻고 #2는 이 답을 따릅니다)"
* options:
  1. label: **"(마) 전체 정규화 핀 (Recommended)"**
     description: "이동 사실은 이동 커밋(9d6800e)을 원본과 비교해 계속 판정하고, 지금 도구는 docstring·출력(emit/print) 호출 인자·최상위 엔진 import 줄·경로 문장(os.path·sys.path 호출이나 절대 경로를 담은 문장 -- 지금 test와 같은 정의)만 빼고 전체 AST를 '핀'(고정 커밋 도구 + 승인된 편집)과 비교합니다. 검출 23/23(+ 이름을 갖지 않은 다른 엔진 모듈로 호출 바꾸기·엔진 아닌 import 바꾸기도 잡음). 잃는 것: docstring·주석·출력 문구(그 안의 식과 부수효과 포함)·엔진 import 줄 모양, 같은 이름을 가진 다른 엔진 모듈로 별칭 바꾸기. V5: F1 = 이 전환 1회, F1의 import 변경은 통과(추가 0). #2 = test 커밋에서 핀 편집 2쌍을 더해 1건(test 먼저 작성 가능). 이후 도구 계산·기록을 바꾸는 card마다 1건."
  2. label: "(다+핀) 이동 커밋 + 6요소 핀"
     description: (현 문안 그대로 -- 수치 재현됨: 7/23, 6요소 밖 16종 0.)
  3. label: "(가) 기준선에 F1 치환 반영"
     description: (현 문안 그대로 -- 12·14·15줄, 23/23 재현됨.)
  4. label: "(다) 이동 커밋끼리만 대조"
     description: (현 문안 그대로 -- 0/23 재현됨.)

계약 2 (c)를 고치지 않고 질문한다면 (마) description의 "(+ 다른 엔진 모듈 별칭으로 호출 바꾸기 … 잡음)"을 지우고 '잃는 것'에 "**함수·루프 안에 엔진 import를 넣어 호출 대상 모듈을 바꾸는 변경**(그 모듈이 그 이름을 갖지 않아도)"을 더해야 한다(NEW-1 -- 지금 test는 잡는다). 권고는 계약 수정(측정상 부작용 0).
비교표 절·계약 '남는 사각'·card D1 (5)·계약 5 42~43행에도 같은 정정(경로 문장 정의, `def emit` 안 `print`, 2 (c) 범위)을 적용할 것.

## 7. 측정 정의(스크립트 삭제 전 원문 요약 -- 재현용)

* (마) 구현: env = `A/*.py` 이름 집합(작업 트리 glob / 커밋 `ls-tree --name-only <c> <A>/`), binds = 최상위 + `if`/`try`(처리기·else·finally)/`with`/`for`/`while` 본문의 def·class 이름, Assign/AnnAssign/AugAssign 대상 안 `Name`, import·from-import 묶는 이름(asname 또는 첫 성분), `*`면 참. N = (1) 최상위 별칭표(엔진 별칭·이름 별칭, 같은 별칭은 뒤가 이김) → (2) `ast.walk` 스냅숏의 모든 `body`/`orelse`/`finalbody` 목록에서 docstring(원래 목록 첫 문장)·경로 문장(원래 노드)·엔진 from-import·엔진 import 별칭 제거(남는 별칭 없으면 문장 제거) → (3) `NodeTransformer`(하위 먼저)로 `Attribute(Name(엔진 별칭), x)`를 binds일 때 `Name(x)`, 이름 별칭 `Name` 치환 → (4) `Name('emit'|'print')` 호출 인자 비움 → `ast.dump(annotate_fields=True, include_attributes=False)`. 핀 상태 = [N(blob_P, env_P)] + [N(E(blob_P), env_P)], E는 각 기준 문자열 정확히 1회 `str.replace`. 변형(S1 수정 확인) = 함수·블록 안 import 문을 비교용 상수 `Expr`로 바꿔 남기고 같은 N.
* test 파일 패치: 기존 함수 본문만 교체(새 id 0) -- (A1) 구조 4조건 + 기준선 대조 + 거부 2커밋, (A3) `pin_commit` 리터럴·`pin_edits` 튜플 리터럴·`assert len(pin_edits) == <정수>`·판정, 거부 표본 4종·수용 표본 4종·기준 문자열 2회 이상 거부(모두 계약 문장 그대로). 도우미는 모듈 수준 함수.
* (가) = `non_path_line_changes(F1별칭(939f926 blob), 도구)`, (나) = 경로 줄 ∪ 엔진 7모듈 import 문 ∪ 엔진 별칭 속성을 담은 단순 문장 줄, (다+핀) = 계약 (A2) 6요소 그대로.
* 모의 커밋(복제본 안, 삭제됨): F1 T `e5aa984`, F1 K 별칭 `fc41fcb`/from-import `eb57980`, T 없는 #2 K `574e025`, #2 T `94b4e66`, #2 병합본 `f5308fa`(theta 삭제판 `569da57`), from-import 쪽 `0a21450`→`dddfa58`(`5f2588c`), 순서 I `5d253f4`→`ace4c73`, 순서 I T 없는 K `d12e1ca`, 가짜 엔진 모듈 `cb003b2`, 정수 단언 없음 `bc08ef2`→`b50260b`, 변조 `2751eaf`→`fdb40f1`, 뒤 card `f5e7ce3`·`931f985`, 가짜 핀 `c12f96e`→`7b0ed19`→`881941d`.
