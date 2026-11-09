# D0a det5 독립 검토 (review_d0a_det5)

검토자: 독립 검증자(작성자 아님). 범위: det5 diff만 -- `draft_p3_d0a.spec.md`·`d0a_briefs.md`·`d0a_determinism.md`를 각 `*.pre-det5.bak`과 대조했다. 작성자 키트는 열지 않았다.
기준: gate `master` = 실제 저장소 HEAD = `6c724de`. 샌드박스는 `C:/g364`(TMP/TEMP 그 아래)이고 작업 끝에 삭제했다.

## 판정: **B 0, S 0, minor 0(+ 선택 1). 착수 막는 것 없음.**

## 1. diff 범위 -- 요청한 변경만 있다

| 파일 | 바뀐 곳 | 확인 |
|---|---|---|
| spec | 49행 det5 머리 한 줄(새 줄) | m-1'와 (iv-i) 문구, (det4) 괄호를 적었다. "필수 단계 수(21)·배정 규칙·뜻은 바뀌지 않는다('작성 전 실측' 15)" |
| spec | 324행 (iv-i) | '`cf_*` 넷 중 하나' → 'C0의 `conflicts` 단위 넷 중 하나'. 끝 `.` → `;`(뒤에 (iv-i')가 이어짐). 기대(exit 1·`conflicts` 4·`assignment`에 없음·exit 2 아님)는 그대로 |
| spec | 325행 (iv-i') 새 줄 | 같은 `conflicts` 단위 넷 중 하나, `q` 없음, 칸 `m2, m5`·`m3, m6`(A-3 행 둘, 가장 작은 MOD 2·3) → exit 1, `conflicts` 4, 그 단위는 `assignment`·`reg_mismatch`에 없음, exit 2 아님 |
| spec | 335행 (det4) 괄호 | '작성자는 다시 실행하지 않았다' → review_d0a_det4 4절 실측 인용. 인용 내용은 그 파일 4절 표와 같다(아래 1.1) |
| spec | 336행 (det5) 새 줄 | (e6)을 `conflicts` 단위에도 거는 구현은 (iv-i')에서 FAIL |
| spec | '작성 전 실측' 15 새 항목(489~492행) | 관찰로 표시했다(기대값 근거 아님). 14 다음 번호다 |
| briefs | 8행 det5 머리, 127행 1절 5 색인 (iv-i'), 201행 열거 `(iv-a)~(iv-i)·(iv-i')`, 204행 (det5) 3.1 점검 줄 | 모두 (iv-i') 추가뿐이다 |
| determinism | 61행 det5 이력 한 줄 | 단계 수 21 그대로, 실측 15 |

* 그 밖의 바이트는 같다. 배정 규칙·계약 1~4·다른 단계·필수 단계 이름은 바뀌지 않았다.
* 필수 단계 수는 어디서나 21이다: spec 469행, briefs 54·115·140·200행, determinism 60·61행, briefs·spec det5 머리. 20이나 22로 적은 곳은 없다.
* gate `6c724de`의 `role_paths.parse_spec_card`로 det5 판과 pre-det5 판을 읽었다. 결과는 같다: id `20260930-p3-move-plan-tool`, phase 3, `red-green`, gate_change no, 승인 1, 절 11개.

### 1.1 (det4) 괄호 인용 확인
* review_d0a_det4 4절 표의 내용:
  * 계약 구현은 PASS다.
  * (iv-h)·(iv-i)·Tarjan 셋은 card 이름에서 FAIL이다.
  * 이름이 모두 소문자이면 Tarjan이 통과한다(놓침).
  * (e6)-on-`conflicts`는 놓쳤다(m-1').
* review_d0a_det3 3절 인용은 4절 앞의 경위다.
* card 335·336행 문장은 이와 같다.

## 2. (iv-i')의 기대 exit 1이 card 규칙과 맞는가 -- **맞다**

다음은 card 문장만으로 따진 것이다.
1. 계약 2 A-1 conf 문장에 따르면 `conflicts` 단위는 A-2~A-7 어느 규칙으로도 정하지 않는다. `assignment`에 키가 없고 `conflicts` 원소로만 보고된다. 따라서 그 단위의 A-3 칸은 배정에 읽히지 않는다(A-3이 적용되지 않음).
2. (e5)의 범위는 'A-0·A-1이 정하지 않은 단위(A-0·A-1 배정도 A-1 `conflicts`도 아닌 단위)'다. **범위** 문장도 "`conflicts` 단위는 … (e5)가 걸리지 않는다"고 한다.
   * (e6)은 '(e5)와 같은 범위'다. 그래서 `conflicts` 단위에서는 (e6) 조건(A-3 행 둘, 최솟값 2≠3)이 참이어도 exit 2가 아니다.
   * 칸이 모두 MOD 둘짜리라 (e5) 조건 자체도 거짓이다(MOD 하나짜리 칸 0). 순서 (e5) → (e6) → A-3은 이 단위에서 공허하다.
3. `reg_mismatch`에는 두 겹으로 들지 않는다.
   * 정의상 MOD가 둘 이상인 칸(A-3 행)은 들지 않는다.
   * 배정 없는 단위(`conflicts`)도 들지 않는다.
4. `conflicts`는 C0 그대로 4다. 레지스트리 행은 `conflicts` 판정(N3.10 토큰)에 쓰이지 않는다. C0의 다른 목록도 비어 있지 않다. 그래서 exit 1·`FAIL`이다.
5. (iv-i)와 짝이 맞다: (iv-i)는 MOD 하나짜리 칸으로 (e5)를, (iv-i')는 A-3 칸으로 (e6)을 겨눈다. (iv-h)(A-1 단위의 (e6) 제외)와 함께 (e6) 범위의 두 제외(A-1·`conflicts`)를 모두 덮는다.

## 3. 재구현 실측 (card 문장만으로, 작성자 키트 미열람)

**구현**(`C:/g364/mp.py`, 삭제함)
* card 계약 2 문장만으로 짠 축소 `plan`이다. 표 파싱은 N3.10 `대표 대상` 열과 레지스트리 `함수`/`이관 목적지` 열로 했다.
* 들어 있는 것:
  * A-1·`conflicts`
  * (e1), (e5) → (e6)(범위: A-1도 `conflicts`도 아닌 단위)
  * A-3·A-4(앉히기·승격·MOD7 상한), A-K, A-5((e2)), A-6, A-7, 단조 고정점
  * 목록 `upward`·`cycles`·`unassigned`·`conflicts`·`reg_mismatch`
  * 결정성 정렬(최상위 첫 세 키, 나머지 키 이름순, 원소는 문자열 또는 `json.dumps(sort_keys)` 순)
* 들어 있지 않은 것: A-0(C0에 대상 없음), A-2, `mod_imports`, `import_*`, `check`. 모두 이 검증의 표적 밖이다.
* 변형은 셋이다. 한 줄씩만 바꿨다.
  * `e6conf`: (e6) 범위에 `conflicts`를 넣음
  * `e5conf`: (e5) 범위에 `conflicts`를 넣음
  * `e6a1`: (e6) 범위에 A-1을 넣음

**구성**(card 300~325행 문장)
* MOD1~MOD7 `m1.py`~`m7.py`는 모두 없다. MOD7 책임은 "레이아웃만"이다.
* split `src.py`·`iso.py`가 있고, `tool.py`는 `--keep`이자 `--split`이다.
* `conflicts` 4: `Cf_b`·`_cf_c`·`cf_a`·`cf_d`(MOD2·MOD3 두 행)
* `iso.py` 쌍 둘: `unassigned` 4
* lift-cap-mod7 넷 → `m2.py`. `upward` 4
* lift-a4 넷 → `m2.py`. `reg_mismatch` 4
* 순환 `cy3`↔`cy4`, `Cy5`↔`Cy6`. 그래서 `upward`는 6이다.
* (a) A-5 상수 넷(`C_a`·`_c_b`·`c_c`·`c_d`): 참조자는 칸 m1·m2 함수이고, 기대는 `m1.py` `A-5`다.
* A-K `tk`가 있다.
* 토큰·레지스트리 행은 이름 역순으로 적었다.
* 자식 (iv-a)·(iv-f)·(iv-g)·(iv-h)·(iv-i)·(iv-i')는 card 문장 그대로다. (iv-i)·(iv-i')의 `conflicts` 단위는 `cf_a`다.

**판정**
* 갈래마다 `PYTHONHASHSEED` 0~7로 돌렸다.
* 시드 사이에 stdout 바이트가 같은지 보고, card 기대를 단언했다.
* C0에서 단언한 것: `upward` 6, `cycles` `[["m3.py","m4.py"],["m5.py","m6.py"]]`, `unassigned`·`conflicts`·`reg_mismatch` 4, `conflicts` 단위 코드 포인트 순서, A-5 넷.
* 시드 증인: 단위 키 집합의 반복 순서가 시드 8개에서 8가지로 서로 달랐다.

| 구현 | C0 | iv-a | iv-f | iv-g | iv-h | iv-i | iv-i' | 결과 |
|---|---|---|---|---|---|---|---|---|
| 계약 | ok(1) | ok(2 `e5 q [2,5]`) | ok(2 `e6 q [2,3]`) | ok(`m2.py` A-3) | ok(`m3.py` A-1) | ok(1) | ok(1) | **PASS** |
| (e6)을 `conflicts`에도 | ok | ok | ok | ok | ok | ok | **exit 2 `e6 src.py::cf_a [2, 3]`** | **FAIL (iv-i')** |
| (e5)를 `conflicts`에도 | ok | ok | ok | ok | ok | **exit 2 `e5 src.py::cf_a [2, 5]`** | ok | **FAIL (iv-i)** |
| (e6)을 A-1에도 | ok | ok | ok | ok | **exit 2 `e6 src.py::q [2, 3]`** | ok | ok | **FAIL (iv-h)** |

* 모든 갈래에서 시드 0~7의 stdout 바이트가 같았다.
* 변형마다 표적 갈래 하나에서만 FAIL했다.
  * (e6)-on-`conflicts`는 (iv-i')가 없으면 놓친다. (iv-i)는 통과하기 때문이다. 이것이 m-1'의 해소다.
  * (e5)-on-`conflicts`는 (iv-i')에서 통과한다. 칸이 MOD 둘짜리라 (e5) 조건이 거짓이기 때문이다. 그래서 (iv-i)가 여전히 필요하다.
* 작성자의 '작성 전 실측' 15와 결과가 같다. 이는 독립 재측정이다(작성자 수치를 받아쓰지 않았다).

## 4. 선택(결함 아님)
* briefs 127행과 determinism 61행은 (iv-i')를 "**같은** `conflicts` 단위에"라고 적었다. card 325행은 "C0의 `conflicts` 단위 넷 중 하나"다.
* 같은 단위를 고르는 것은 card가 허용하는 경우 중 하나다. 그래서 모순은 아니다.
* 다만 색인 문구를 card와 맞추려면 '넷 중 하나(예 (iv-i)와 같은 단위)'로 바꿀 수 있다. 바꾸지 않아도 된다.
