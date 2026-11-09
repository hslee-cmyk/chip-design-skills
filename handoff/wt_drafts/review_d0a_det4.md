# D0a det4 개정 독립 재검토 (review_d0a_det4)

작성 2026-10-06. 검토자는 det4 개정의 작성자가 아니고, det3 검토(`review_d0a_det3.md`)의 검토자도 아니다.

검토 대상(sha256 앞 16자리):
* `draft_p3_d0a.spec.md`: `b5b1e96a997b73aa`. 개정 전 사본 `.pre-det4.bak`은 `f63e0b619bb3caeb`로, det3 검토가 본 판과 같다.
* `d0a_briefs.md`: `4ce348ce168a9b98`. 개정 전 사본은 `4ed10acedb99ae70`로, det3 검토 판과 같다.
* `d0a_determinism.md`: `ebfcd9953da23e29`. 개정 전 사본은 `b857390451e9d614`로, det3 검토 판과 같다.

기준은 gate `master` `6c724de`다. 실제 저장소 HEAD와 master가 모두 이 커밋이다. 실제 저장소는 읽기만 했다(`git -C … show`, clone 원본). 작업 뒤 `git status`는 시작 때와 같다(`.bkit` 두 파일만 M).

스크래치는 `C:/g359`만 썼다.
* TMP/TEMP는 `C:/g359/tmp`로 두었다.
* `git clone -c core.autocrlf=false --no-local --no-hardlinks`로 복제했다. 이어서 `6c724de`를 checkout하고, origin을 제거하고, 빈 hooksPath를 걸었다.
* G1 시제품 `g1_kit/install_proto.py`(sha256 `218e2162…`)를 설치했다("installed 4").
* `cd`는 한 번도 쓰지 않았다. 모든 경로는 절대 경로다.
* 작업이 끝난 뒤 `C:/g359`를 삭제했다.

`p3kit_det3/`와 작성자 스크래치 코드는 열지 않았다. 작성자 스크래치 `C:/g358`은 이미 없다.
구현과 구성은 모두 card 문장에서 내가 직접 썼다.

## 판정: **B 0, S 0, minor 1(+ 참고 2). 사용자 질문 없음.**

* det3 검토의 S(X-1)는 해소되었다. m-1~m-4도 모두 해소되었다.
* X-1은 문언 정정이다. 기준 변경이 아니다(2절).
* 새 단계 `allow-changed-declared`의 다섯 갈래를 card 문장만으로 구현해 돌렸다.
  * 계약 구현은 PASS했다.
  * det3 문언 구현, 넓은 구현, 삭제된 허용 id를 `lost`에서 빼는 구현, 출처 기준 구현은 모두 FAIL했다.
* (iv-h)·(iv-i)와 `cycles` 이름 순서 요구를 표적 변형에 처음으로 실제로 돌렸다. 세 변형 모두 FAIL했다.
* 남은 것은 한 가지다. (e6)을 `conflicts` 단위에 거는 변형이 여전히 통과한다(m-1').

## 1. det3 검토 지적의 해소 여부

| 지적 | 해소 | 확인 |
|---|---|---|
| S(X-1) `--allow-changed` 문언 | 예 | card 177~180행. 검토 6절 정확한 문안과 뜻이 같다. `rebind`(181행)·`lost`(191행) 문장은 고치지 않았다. 그래서 정의는 한 곳에만 있다 |
| S(X-1) oracle 보강 | 예 | 필수 단계 `allow-changed-declared`(336~346행). 다섯 갈래이고 검토가 제안한 세 경우 + 음성 + 삭제를 모두 담았다. 3절에서 실측했다 |
| m-1 (iv-h)·(iv-i) | 예 | 322~324행. A-0 제외는 겨누지 않는다고 적었다. 4절에서 실측했다 |
| m-2 `cycles` 이름 순서 | 예 | 311행. 4절에서 실측했다 |
| m-3 코드 포인트 | 예 | 155행. 대상 다섯(사전 키·`from` 줄 안 항목·모듈 이름·`mods`·`cycles` 원소 안)을 열거하고, 대소문자 무시·구두점 무시·로캘 정렬이 아님을 적었다 |
| m-4 briefs 문구 | 예 | briefs 200행. 지금 문구는 "(iv) (e5)·(e6) 갈래들((iv-a)~(iv-i))"이다 |

**필수 단계 수 21은 세 문서에서 일관된다.**
* card의 'oracle' 절을 세면 21이다. v6 4, v7 1, v8.4 10, conf 1, r1 2, UD-6 1, det 1, det4 1(`allow-changed-declared`)이다.
* briefs에서는 114·139·199행이 21이다. 199행의 내역 합도 21이다.
* determinism 60행은 "20 → 21"이다.
* briefs 53행의 "합성 단계 21개(이름 기준 `import-time-high` 하위 단계 포함)"는 개정 전에도 있던 r1 측정 행이다(pre-det4 52행). 세는 기준이 다르고, 수가 우연히 같다(참고 2).
* `d0a_launch.sh`에는 단계 수 문장이 없다.

**`role_paths.parse_spec_card`**(`6c724de`판, 복제본에서 수정 없음)는 개정 후·개정 전 모두 통과했다.
* id는 `20260930-p3-move-plan-tool`이다.
* phase 3, red-green, gate_change no다.
* approval은 `20260930-30-module-split-design`이다.
* 절은 11개로 개정 전과 같다.

**`interface_card.py --root <6c724de + G1 시제품 "installed 4">`**: exit 0, **'기존 함수 0개'**였다. 신규 시그니처는 `move_plan` `*`·`main` 두 행이다. card 해시가 바뀌었으므로 착수 때 interface card는 이 판으로 다시 생성한다.

## 2. design 30 인용(`6c724de`, `git -C <저장소> show` 읽기 전용)

* **211행**은 §3 표의 MOVE-TOTAL 행이다.
  * 식: "Phase 전 base와 Phase 후 병합본 사이에서 MOVE-AST (b)(c)(d)를 전 단위로: 바뀐·새·사라진 단위는 M10이 선언한 것(`run_harness.py::run`, `gmid_design_pipeline.py::run_gmid_design_pipeline`)뿐".
  * 도구: `move_plan check --card ALL --allow-changed …`(E6).
  * card의 줄 번호와 인용이 맞다.
* **1098행**은 `# ---- E6: 정의 보존(MOVE-TOTAL) ----`이다. **1100행**은 `--allow-changed workspaces/run_harness.py::run skills/analog-gmid-design/assets/gmid_design_pipeline.py::run_gmid_design_pipeline`이다.
  * id 모양은 저장소 상대 `<경로>::<qualname>`이다. card 177행의 "head 단위 `<경로>::<qualname>`"과 같다.
* **1113행**은 E6 통과 기준 "exit 0(모든 발견 목록 비어 있음)"이다. 같은 절 E2 ②가 나열하는 발견에 `rebind`가 들어 있다.

**정정인가, 기준 변경인가: 정정이다.**
* det3 문언을 그대로 따르면 E6가 FAIL한다. MOVE-TOTAL이 허용하는 선언된 바뀐 단위 `run`이 다음 둘을 내기 때문이다.
  * 그 base 짝이 '사라진 단위'((c) → `lost`)로 잡힌다.
  * 자기 읽기가 `rebind`로 잡힌다.
* 이것은 design 문언 자체와 어긋난다. det4는 도구를 design 문언에 맞춘다. 판정 기준(E6 exit 0, MOVE-TOTAL 식)은 한 글자도 바뀌지 않는다.
* det4는 '바뀐 단위는 `rebind`에서 뺀다'는 기존 규칙을 선언된 바뀐 단위에도 똑같이 적용한다. 그래서 새 예외를 만든 것이 아니다.
* 좁은 읽기(head에서 사라진 허용 id는 `lost`에 남는다)는 design 문언("사라진 단위 … 선언한 것")보다 엄격하다.
  * 그러나 M10은 삭제가 없다(design 30 133·617행: 새 def와 `run()` 몸체 변경뿐). 그래서 E6 결과는 바뀌지 않는다.
  * design §6.3은 CLI의 정본을 card로 둔다. 따라서 이 선택은 card 권한 안이다.
  * 장래에 선언된 삭제가 생기면 그때 card를 고친다(card 398행 (9)가 근거를 적었다).

## 3. `allow-changed-declared` 독립 실측(card 336~346행 문장만으로)

**구현**(`C:/g359/acd.py`, 삭제함)
* 설치된 G1 시제품의 공개 이름을 card 계약 4·5대로 불렀다: `reachability.read_tree(…, SOURCE_GLOBS)`, `SourceIndex`(`units`·`global_names`·`binding_origin`), `moved_defs` 1회.
* 그 위에 `changed`·`lost`·`rebind`를 card 174~192행 문장대로 짰다.
* 배정 집합은 card 339행대로 구성상 비어 있다. 그래서 `plan`과 나머지 발견 8종은 재구현하지 않았다. 대신 `moved_units` = {}와 `rejected` = {}를 갈래마다 단언했다.

**구성**(합성 저장소, 파일은 `skills/analog-gmid-design/assets/` 아래 -- `_is_source` 참)
* B는 `m1.py`(`k`)와 `h.py`(`run(x): return x`)다.
* H1은 B의 자식이다. `mx.py`에 `pipe(y)`를 두고, `h.py`에 `from mx import pipe`를 넣고, `run`이 `pipe`를 부른다.
* Bg는 B의 자식으로, `h.py`에 `g(): return pipe(1)`을 더했다.
* Hg는 Bg의 자식으로, H1과 같은 변경에 `g`를 그대로 둔다.
* Hd는 B의 자식으로, `h.py`를 빈 파일로 만든다.

| 구현 | (1) | (2) | (3) | (4) | (5) | 결과 |
|---|---|---|---|---|---|---|
| det4 계약 | ok | ok | ok | ok | ok | **PASS** |
| det3 문언(허용 id를 `changed` 목록에서만 뺌) | `lost` [`h.py::run`]·`rebind` [(`run`, `pipe`)] | ok | ok | `lost` 1·`rebind` 2(`g`·`run`) | ok | **FAIL** (1)(4) |
| 넓은 구현(허용 id를 `lost`·`rebind`에서 id로 지움) | ok | ok | ok | ok | `lost` [] | **FAIL** (5) |
| 삭제된 허용 id를 `changed` 단위로 취급(`lost` 아님) | ok | ok | ok | ok | `lost` [] | **FAIL** (5) |
| 출처 기준(허용 id 정의를 출처로 하는 `rebind`도 지움) | ok | ok | ok | `rebind` [] | ok | **FAIL** (4) |

* (4) 계약 구현의 `rebind` 원소는 `{"unit": "…/h.py::g", "name": "pipe", "base": ["unbound", "pipe"], "head": ["def", "…/mx.py", "pipe"]}`다. card 343행과 같다.
* det3 문언 구현의 수치는 card 345행·'작성 전 실측' 14와 같다. 작성자 측정을 독립 구현으로 재현했다.
* 과제가 지정한 다섯 갈래 판정이 모두 card 주장대로 나왔다: 정답 PASS, det3 문언 FAIL, 넓은 구현 FAIL, 삭제 id를 `lost` 아님으로 보는 구현 FAIL. 출처 기준 FAIL도 추가로 확인했다.
* 관찰(결함 아님): (5)의 기대 `changed` []는 Hd의 `h.py`가 비어 있을 때만 성립한다. docstring이나 `pass` 문장을 남기면 그것이 새 문장 단위가 되어 `changed` 1이 된다.
  card의 "`run`을 지움(파일은 남김)"은 B의 `h.py`에 `run`만 있으므로 빈 파일을 뜻한다. test-author가 그렇게 읽으면 된다.

## 4. (iv-h)·(iv-i)·`cycles` 이름 순서 -- 표적 변형 실측(작성자 미실행분)

**구현**(`C:/g359/plan_mini.py`, 삭제함)
* card 계약 2 문장만으로 짠 축소 `plan`이다. 들어 있는 것: A-1·`conflicts`, (e5) → (e6)(범위 = A-1 배정도 `conflicts`도 아닌 단위), A-3·A-4(앉히기·승격·MOD7 상한), A-5((e2)), A-6, 단조 고정점, `upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`, 결정성 정렬.
* 들어 있지 않은 것: 표 파싱(구조로 넘김), A-2·A-K·`mod_imports`·`import_time_high`. 이 검증의 표적 밖이다.

**C0**는 card 300~311행을 따른다.
* `conflicts` 4: `Cf_b`·`_cf_c`·`cf_a`·`cf_d`(MOD2·MOD3 두 행).
* `iso.py` 쌍 둘: `unassigned` 4.
* lift-cap 4: `Lc_1`·`_lc_2`·`lc_3`·`lc_4`(칸 m2) → `lay7`(MOD7).
* lift-a4 4: `La_1`…(칸 m1) → `tok2`(MOD2). `reg_mismatch` 4.
* 순환 3↔4·5↔6.
* (a) A-5 상수 넷 `K_A`·`_k_b`·`k_c`·`k_d`(참조자 `r1` m1·`r2` m2): 기대 `m1.py` `A-5`.
* 토큰·레지스트리 행은 이름 역순이다. `upward`는 6이다.

**판정**
* 갈래 C0·(iv-a)·(iv-d)·(iv-f)·(iv-h)·(iv-i)마다 `PYTHONHASHSEED` 0~7로 돌렸다.
* 시드 사이에 stdout 바이트가 같은지 보고, card의 기대를 단언했다.
* 순환 이름은 두 가지로 돌렸다: card(`Cy5`·`Cy6` 대 `cy3`·`cy4`)와 모두 소문자.

| 구현 | card 이름 | 모두 소문자 | 걸린 곳 |
|---|---|---|---|
| 계약 | **PASS** | **PASS** | -- |
| (e6)을 A-1 단위에도 | **FAIL** | **FAIL** | (iv-h): exit 2 `e6 src.py::q [2, 3]` |
| (e5)를 `conflicts` 단위에도 | **FAIL** | **FAIL** | (iv-i): exit 2 `e5 src.py::cf_a [2, 5]` |
| `cycles` 바깥 = 단위 이름순 반복 MOD 그래프의 Tarjan 발견 순서(원소 안은 정렬) | **FAIL** | PASS(놓침) | C0 (ii): `[["m5.py","m6.py"],["m3.py","m4.py"]]`. 시드 8개 모두 같은 바이트라 (i)은 못 잡는다 |
| (e6)을 `conflicts` 단위에도 | PASS(놓침) | PASS(놓침) | m-1' |

* 세 표적 변형은 card 333행 주장대로 FAIL했다. card 333행의 "det4 개정 작성자는 이 셋을 다시 실행하지 않았다"는 이 검토로 실측이 생겼다. 원하면 이 파일을 인용하도록 그 문장을 고친다(선택).
* 모두 소문자일 때 Tarjan 변형이 통과하는 것은 det3 검토 m-2의 관찰과 같다. 즉 311행 요구가 실제로 필요하다.
* 참고 1: 311행의 요구는 다음 전제에서 성립한다. MOD5·MOD6 쌍보다 이름이 앞선 다른 단위가 MOD3·MOD4로 들어가는 간선을 갖지 않아야 한다.
  * 그런 간선이 있으면 Tarjan이 m3에서 먼저 시작해 다시 우연히 정렬 순서가 나온다.
  * 위쪽 간선은 `upward` 6 단언이 막는다. 큰 번호 MOD에서 내려오는 간선만 남는데, C0 문장에는 그런 단위가 없다.
  * 문구를 더할 필요는 없다고 본다. test-author가 '그 밖에 섞는 단위'를 지을 때 피하면 된다.

## 5. 남은 지적

* **(m-1') (e6)의 `conflicts` 제외가 고정되지 않는다.**
  * (iv-i)는 (e5) 모양 칸(`m2`·`m5`, MOD 하나짜리 둘)만 `conflicts` 단위에 둔다.
  * 그래서 (e6)을 `conflicts` 단위에도 거는 구현이 모든 갈래를 통과했다(4절 표).
  * card 324행은 A-0 제외만 '겨누지 않는다'고 적었고, 이 경계는 언급하지 않는다.
  * 실제 트리에서는 0건이고 문언("(e5)와 같은 범위", 143~144행)은 명확하다. 그래서 minor다.
  * 닫는 방법은 둘 중 하나다.
    * (가) (iv-i)에 짝 갈래 (iv-i')를 둔다: 같은 `conflicts` 단위에 칸 `m2, m5`·`m3, m6` 두 행 → exit 1(`conflicts` 4), exit 2 아님.
    * (나) 324행의 '겨누지 않는다' 문장에 "`conflicts` 단위의 (e6) 제외"를 더한다.
  * 덧붙여 323행의 "`cf_*` 넷 중 하나"는 (c) 예시 이름(`Cf_b`·`_cf_c`)과 글자로 맞지 않는다. "C0의 `conflicts` 단위 넷 중 하나"로 적는 편이 정확하다.
* 참고 2(지적 아님): briefs 53행의 "합성 단계 21개"는 r1 시점 측정 행이다. `import-time-high` 하위 단계를 포함해 센 수로, 지금 필수 단계 21과 기준이 다르다.
  개정 전에도 있던 문장이라 det4 결함이 아니다. 그래도 auditor가 혼동하지 않게 "(r1 측정 기준)"을 붙일 수 있다.

## 6. 고칠 곳 요약(오케스트레이터)

1. m-1': (iv-i') 갈래를 더하거나, '겨누지 않는다' 문장에 `conflicts` 단위의 (e6) 제외를 더한다. 그리고 `cf_*` 문구를 고친다.
2. (선택) card 333행 "다시 실행하지 않았다"를 이 검토의 실측 인용으로 바꾼다. 그리고 briefs 53행에 기준을 표시한다.

둘 다 배정 뜻을 바꾸지 않는다. 사용자 질문이 아니다. card를 다시 고치면 interface card를 다시 생성한다(이번 판은 '기존 함수 0개').
