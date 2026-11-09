# D0a det3 개정 독립 재검토 (review_d0a_det3)

작성 2026-10-06. 검토자는 det3 개정을 쓰지 않았다. 검토 대상은 아래 세 파일이다.
* `draft_p3_d0a.spec.md`: sha256 앞 16자리 `f63e0b619bb3caeb`. 개정 전 사본 `.pre-det3.bak`은 `a11239aad8cd65c9`로, 앞 검토가 본 판과 같다.
* `d0a_briefs.md`: `4ed10acedb99ae70`.
* `d0a_determinism.md`: `b857390451e9d614`.

앞 검토는 `review_d0a_det2.md`다(S2, m-a~m-d).
기준은 gate `master` `6c724de`다. 실제 저장소 HEAD와 master가 모두 이 커밋이다. 실제 저장소는 읽기만 했다(`git -C … show`, clone 원본).

스크래치는 `C:/g346`만 썼다.
* TMP/TEMP는 `C:/g346/tmp`로 두었다.
* `git clone -c core.autocrlf=false --no-local --no-hardlinks`로 복제했고 origin을 제거했다. 이어서 G1 시제품 `install_proto.py`를 설치했다("installed 4").
* **절차 위반 1건(자기 보고)**: 초기에 `cd /c/g346…`가 들어간 명령이 셋 있었다. 하나는 role_guard 훅이 거부했다. 나머지 둘이 쓴 경로는 모두 절대 경로 `C:/g346/…`였고 실제 저장소·`_drafts`는 건드리지 않았다. 그 뒤에는 cd를 쓰지 않았다.
* 작업이 끝난 뒤 `C:/g346`을 삭제했다.

작성자 키트 `p3kit_det3/`는 내 구성기·판정기·변형을 만들고 돌린 **뒤에야** 열었다. 변형 목록만 대조했고 증거로는 쓰지 않았다.

## 판정: **B 0, S 1(추가 항목 X-1 -- 6절), minor 4. 사용자 질문 없음.**

(det3 범위만 보면 S 0이다. S 1은 오케스트레이터가 나중에 더한 검토 항목 X-1이다. X-1은 `m10_t1_open_items.md`가 보고한 `--allow-changed` 문언 문제다.)

앞 검토의 S2는 해소되었다. card 문장만으로 만든 내 구성에서는 다음과 같이 나왔다.
* 계약 순서 구현은 PASS했다.
* 과제가 지정한 변형 10종(누출·정렬 키·A-5·(e5)·(e6))은 모두 FAIL했다. 보조 변형 8종도 모두 FAIL했다.

남은 것은 구성이 겨누지 않는 좁은 틈 셋과 문언 하나다(m-1~m-4).

## 1. 앞 검토 지적의 해소 여부

| 지적 | 해소 | 확인 |
|---|---|---|
| S2 (a) 다중 MOD 참조자 A-5 4개 | 예 | card 300행 요구 + 기대 MOD 단언(308행) |
| S2 (b) `from` 4줄·`import` 2줄 + 목록 전체 단언 | 예 | 302·309행. 예시 목록이 코드 포인트 항목 순서를 고정한다 |
| S2 (c) 대소문자·`_` 섞기 | 예 | 304행. 예시의 세 순서(코드 포인트·대소문자 무시·구두점 무시)를 내가 계산해 보니 맞았다 |
| S2 (d) `import_conflicts` | 예 | (vi) 자식 커밋. `import_time_high`·`absent_split`은 겨누지 않는 목록이라고 적었다 |
| S2 괄호 주장 범위 | 예 | "(a)·(b)·(c)와 (iv-e)~(iv-g)·(vi)가 있는 이 구성에 대해서만" |
| m-a A-2 포함 이유 + (iv-e) | 예 | 144~145행. 이유 문장이 논리적이다(A-2 여부는 고정점 뒤에 정해지므로 정적으로 앞에서 본다) |
| m-b A-3 행 여럿 | 예 | (e6) exit 2, (iv-f)·(iv-g). 아래 2절 |
| m-c `origin` 튜플 | 예 | 158~159행. 담는 원소와 그 목록만 정렬하고, `__future__` 기능 목록은 정렬한다 |
| m-d 보고 근거 | 예 | `d0a_determinism.md` 46행을 §6.3(`6c724de` 454행)으로 고쳤다. 줄 번호는 실측과 맞다 |

* `role_paths.parse_spec_card`(`6c724de` 판 `tools/gates/role_paths.py`, 복제본에서 수정 없음): 개정 후·개정 전 모두 통과했다. id `20260930-p3-move-plan-tool`, phase 3, red-green, gate_change no, approval `20260930-30-module-split-design`이다.
* `interface_card.py --root <6c724de + G1 시제품 "installed 4">`: exit 0, **'기존 함수 0개'**. 신규 시그니처는 `move_plan` `*`·`main`이다.
* briefs의 det3 반영(머리, 1절 5, 2절 7, 3.1)은 card 문언과 같다. 필수 단계 수는 20 그대로다.

## 2. (e6)과 design 30 §6.2(`6c724de`)

* §6.2 A-3(415행)의 식은 "max(셀의 가장 작은 MOD, 피참조의 최대 MOD)"로 **셀 하나**에 대한 식이다. 한 키에 A-3 행이 여럿인 경우는 정하지 않는다.
  §6.2 머리(407행)는 "정확한 문언은 D0a spec card 계약 2·3"이다. 그래서 이 빈칸을 card가 정하는 것은 권한 안이다.
* **fail-closed exit 2는 타당하다.** '최솟값의 최솟값'(시제품)은 두 행을 한 칸처럼 읽는 새 뜻이다. (e5)에서 '칸 MOD 합집합'을 버린 것과 같은 이유로 버렸다. 행 순서로 고르면 결정성 문단에 어긋난다.
  가장 작은 MOD가 같으면 어느 행을 읽어도 식의 값이 같으므로 A-3이다. 이 부분은 엄밀하다.
* **D-31과 맞다.** D-31은 승격·단조 고정점(배정을 올리기만 함)이다. (e6)은 배정을 만들지 않고, 고정점 전에 정적으로 멈추기만 한다.
  §6.2 '결과 조건'(PLAN-LAYER exit 0이어야 열 갱신)에서도 exit 2는 D0b를 멈춘다. 그래서 조용한 진행은 없다.
  순서 "(e5) → (e6) → A-3"과 범위("(e5)와 같은 범위")는 일관적이다.
* **레지스트리 재측정**(`6c724de`, 독립 스크립트, 계약 2 A-4 토큰 규칙 + `MP_ARGS` 별칭 `optimizer` → `theta_search`):
  * 레지스트리 함수 표 15개, 행 **379**, 첫 백틱 토큰 이름 **359**(이름 토큰 없는 행 7).
  * 행이 둘 이상인 이름은 **1**이다. `SemiEmpiricalGmIdLUT`가 **14행**이고, 칸이 모두 MOD 하나짜리 **MOD4**(`gmid_sizing_engine`)다.
  * A-3 행은 **2**이고 서로 다른 이름이다. `run_full_circuit_audit` [7, 9], `_build_theta_evaluator` [3, 4].
  * (e5) 조건이 참인 이름 **0**, (e6) 조건이 참인 이름 **0**.
  * card 151행의 수치와 모두 같다. 그래서 실제 트리 배정은 바뀌지 않는다.

## 3. 합성 단계 `determinism` 독립 재구현 실측

* **구성기·판정기**(`C:/g346/judge.py`, 삭제함)는 card 294~329행 문장만 보고 썼다.
* **C0**는 다음으로 이루어진다.
  * MOD1~7 가짜 표에 `대표 대상` 토큰을 이름 역순으로 적었다.
  * 레지스트리 행 이름도 역순이다.
  * `conflicts` 4: `Cf_b`·`_cf_c`·`cf_a`·`cf_d`.
  * `unassigned` 4: `iso.py` 서로 부르는 쌍 둘.
  * lift-cap 4: 칸 `m2` → `lay7`(MOD7).
  * lift-a4 4: 칸 `m1` → `tok2`(MOD2). `reg_mismatch` 4다.
  * 순환 3↔4·5↔6. `upward` 6이다.
  * (a) 상수 4개를 `r1`(m1)·`r2`(m2)가 함께 읽는다.
  * (b) `src.py` 머리 import를 `sys`·`string`·`re`·`math`·`os`·`json` 순으로 적었다. 기대 `mod_imports["m1.py"]`는 card 예시 목록과 바이트까지 같다.
  * `tool.py` A-K 6개. 배정 30이다.
* **자식 커밋**은 (iv-a)~(iv-g)·(vi) 8개다.
* **판정 내용**은 다음과 같다.
  * (i) 시드 0~7 stdout 바이트가 같고 exit 1이다.
  * (ii) 최상위 세 키, 모든 사전 키가 코드 포인트순이다. 다섯 목록은 기대 집합의 정렬 목록과 같다. A-5 배정과 `mod_imports` 전체를 단언한다.
  * (iii) `check --card ALL` base = head에서 시드 0~7이 같다.
  * (iv) 갈래마다 exit와 배정을 본다.
  * (vi) 시드 0~7이 같고 `import_conflicts` 전체가 기대와 같다. `origins`는 `pa` → `pb` 순서이고 `origin`은 튜플 그대로다.
  * (v) 시드 증인: 서로 다른 집합 반복 순서 **8가지**.
* **정답 구현**은 `p3kit_m1/move_plan_sim.py`(sha256 `a60cfe57…`)를 바탕으로 내가 고쳤다. 정렬 출력, `origin` 그대로, (e5)(A-2 포함, A-3보다 먼저), (e6), A-5 (e2) 읽기를 넣었다. 변형은 그 위에 하나씩 넣었다.

| 구현 | 결과 | 걸린 판정 |
|---|---|---|
| 계약 순서(정답) | **PASS** | -- |
| `from` 줄 순서 누출(모듈 집합 반복) | FAIL | (i) 서로 다른 출력 8·(ii) `mod_imports`·(vi) |
| 원소 정렬 키 대소문자 무시 | FAIL | (ii) 네 목록·(vi) 목록 |
| 원소 정렬 키 구두점·대소문자 무시 | FAIL | (ii)·(vi) |
| 로캘 정렬(`locale.strxfrm`, 시스템 로캘) | FAIL | (ii) 네 목록·(vi) |
| A-5 참조자 집합 첫 원소 | FAIL | (i) 서로 다른 출력 2·(ii) `reg_mismatch` 5·A-5·`mod_imports`·(vi) |
| `import_conflicts` 바깥 순서 누출 | FAIL | (vi) 서로 다른 출력 8 |
| `origin` 튜플 정렬 | FAIL | (vi) 목록 |
| (e5)에서 A-2 단위 제외 | FAIL | (iv-e) exit 1 |
| (e6) 최솟값의 최솟값 | FAIL | (iv-f) exit 1 |
| (e6) 첫 A-3 행 | FAIL | (iv-f) exit 1 |
| (보조) (e5) 없음·첫 행 | FAIL | (iv-a)·(iv-c)·(iv-e) |
| (보조) (e5)를 A-3 뒤에 | FAIL | (iv-c) |
| (보조) `unassigned` 누출 / `upward` 누출 | FAIL | (i) 7·8, (ii) |
| (보조) `check` `assigned` 누출 | FAIL | (iii) 서로 다른 출력 8 |
| (보조) 사전 키 대소문자 무시 / `from` 줄 안 항목 대소문자 무시 | FAIL | (ii) 사전 키 / (ii) `mod_imports` |
| (보조) 시제품 그대로 | FAIL | (i)·(ii)·(iv-a,c,e,f)·(vi) |
| **(e6)을 A-1 단위에도** | **PASS(놓침)** | m-1 |
| **(e5)를 `conflicts` 단위에도** | **PASS(놓침)** | m-1 |
| **`cycles` 바깥 순서 = 단위 이름순 반복으로 찾은 Tarjan 순서**(정렬 없음, 시드와 무관) | **PASS(놓침)** -- 아래 m-2 | m-2 |

작성자 키트의 변형 목록과도 대조했다(열람은 위 실측 뒤). 위 '놓침' 셋은 작성자 키트에 없는 변형이다.

## 4. 남은 지적(minor)

* **(m-1) (e5)·(e6) 범위 경계가 반만 고정된다.**
  (iv-d)는 (e5)가 A-1 단위에 걸리지 않음을 고정한다. 그러나 다음 셋은 고정하지 않는다.
  * (e6)의 같은 경계: (e6)을 A-1 단위에도 거는 구현이 PASS했다.
  * `conflicts` 단위 제외: (e5)를 `conflicts` 단위에 거는 구현이 PASS했다.
  * A-0 단위 제외.
  실제 트리 0건이고 문언은 명확하다. 고정하려면 다음 둘을 더할 것.
  * (iv-h): (iv-f)의 두 행 + MOD3 행 토큰 `q` → `q` = `m3.py`(`A-1`), exit 2 아님.
  * 필요하면 `conflicts` 단위 한 개(C0의 `cf_*` 하나)에 칸 `m2`·`m5` 두 행을 둔 자식 → exit 1(`conflicts`), exit 2 아님.
* **(m-2) `cycles` 바깥 순서는 시드가 아닌 결정적 누출을 놓칠 수 있다.**
  card 문장대로 순환 단위 이름을 모두 소문자(`cy3`·`cy4`·`cy5`·`cy6` 모양)로 두면, 단위 이름순 반복으로 MOD 그래프를 만들고 Tarjan 발견 순서를 그대로 내는 구현이 우연히 정렬 순서를 낸다.
  MOD5·MOD6 쪽 단위 이름만 `Cy5`·`Cy6`으로 바꾸면 그 구현이 `[["m5.py","m6.py"],["m3.py","m4.py"]]`를 낸다(시드 0~7 모두 같은 출력이라 (i)이 아니라 (ii)만 잡는다).
  (c) 요구의 목록에 `cycles`가 없다. 고칠 문안: (c)의 대상 목록에 `cycles`를 더하고 "번호가 큰 순환 쌍의 단위 이름이 작은 쌍보다 코드 포인트로 앞서게(예 `Cy5`·`Cy6` 대 `cy3`·`cy4`)"를 붙일 것.
* **(m-3) '이름순'·'문자열순'의 코드 포인트 한정.** 결정성 문단은 '원소 정렬'에만 "(코드 포인트)"를 적었다. 다음은 한정 없이 '이름순'·'문자열순'이다.
  * 사전 키 이름순.
  * `from` 줄 안 항목 문자열순.
  * 모듈 이름순.
  * `conflicts.mods`, `cycles` 원소 안.

  (ii)의 예시 목록(`JSONDecoder, dumps`)이 항목 순서를 사실상 고정하고, 내 판정기는 사전 키도 코드 포인트로 봐서 두 보조 변형을 잡았다. 그러나 test-author가 card 문언만으로 사전 키 판정을 대소문자 무시로 쓸 여지가 있다.
  한 구절이면 닫힌다: "이 card의 '이름순'·'문자열순'은 모두 코드 포인트 순".
* **(m-4) briefs 196행 낡은 문구.** auditor 3.1에 det2 문장 "(iv) (e5) 네 갈래"가 남아 있다. 지금은 (iv-a)~(iv-g) 일곱 갈래 + (vi)다. 바로 다음 줄(197) det3 문장이 보충하므로 경미하다. "(iv) (e5)·(e6) 갈래들"로 고칠 것.

## 5. 고칠 곳 요약(오케스트레이터)

1. m-1: (iv-h)(그리고 선택으로 `conflicts` 단위 (e5) 자식)을 더한다.
2. m-2: (c) 대상에 `cycles`를 더하고 순환 쌍 이름 순서를 요구한다.
3. m-3: '이름순·문자열순 = 코드 포인트'를 한 구절로 적는다.
4. m-4: briefs 196행 문구.
5. **S(X-1)**: `--allow-changed` 문언 정정과 합성 단계 `allow-changed-declared` 추가(6절).

넷 다 배정 뜻을 바꾸지 않는다. 사용자 질문이 아니다. card 해시가 바뀌면 interface card를 다시 생성한다(이번 판은 '기존 함수 0개').

## 6. 추가 항목 X-1 -- `--allow-changed` 문언(오케스트레이터 요청, card는 고치지 않음)

**대상.** `_drafts/m10_t1_open_items.md` X-1이다.
* 보고 내용: 대역으로 M9 → M10에서 `--allow-changed run_harness.py::run … gmid_design_pipeline.py::run_gmid_design_pipeline`를 주면 `lost` 1과 `rebind` 1이 나와 FAIL한다. 그대로면 DoD E6이 FAIL한다.
* 제안: 허용 id를 `lost`·`rebind`에서도 뺀다.

**판정: 실제 결함이다(S).** 근거는 card 문언과 design 30(`6c724de`)이다. 이 판정은 G1 대역 실측을 다시 하지 않고 문언만으로 내렸다.

**card 문언(175~186행)을 그대로 읽으면 이렇다.**
* `changed`(173~175행): head `run`(같은 파일, 같은 (종류, 키), 해시 다름)은 `changed` 단위다. 끝 문장 "`--allow-changed`에 적힌 id는 뺀다"로 목록에서 빠진다.
* `lost`(186행): "head 같은 파일에 같은 (종류, 키)가 있어 **`changed`로 보고된 것도 아닌 것**"이다. 허용 id는 `changed`로 '보고되지' 않았다. 그래서 base `run`이 `lost`가 된다.
* `rebind`(176행): 제외 대상이 "`changed`로 **이미 보고된** 단위"다. 허용된 `run`은 제외되지 않는다. 그래서 `run`이 새로 읽는 `run_gmid_design_pipeline`(base 출처 없음 → head 그 모듈 정의)이 `rebind`가 된다.
* 정리: 허용이 '보고 단계에서 목록에서 지우기'로 적혀 있다. 그런데 `lost`·`rebind`의 예외는 '보고되었음'을 조건으로 건다. 그래서 허용이 오히려 두 발견을 만든다. 보고된 수치(`lost` 1 + `rebind` 1)가 이 문언에서 그대로 나온다.

**design 30을 보면 이렇다.**
* §3 MOVE-TOTAL(211행): "MOVE-AST (b)(c)(d)를 전 단위로: 바뀐·새·사라진 단위는 M10이 선언한 것(`run_harness.py::run`, `gmid_design_pipeline.py::run_gmid_design_pipeline`)뿐"이고, 도구는 `move_plan check --card ALL --allow-changed …`(E6)다.
* §10 E6(1098~1113행)은 exit 0, 즉 모든 발견 목록이 비어야 한다.
* `run`은 선언된 '바뀐 단위'다. 그 base 짝을 '사라진 단위'((c) → `lost`)로 세는 것은 MOVE-TOTAL 문언에 어긋난다.
* `rebind`((e))는 MOVE-TOTAL 식에 들지 않는다. 그러나 E6이 `check` 전체 발견을 요구하므로 걸린다. card가 이미 '`changed` 단위는 `rebind`에서 뺀다'고 정한 이유(바뀐 단위는 읽는 이름이 바뀌는 게 당연하다)가 선언된 바뀐 단위에도 그대로 적용된다.
* 따라서 고치는 것은 **기준 변경이 아니라 design 문언대로 맞추는 정정**이다. 사용자 질문은 필요 없다.

**제안 문언보다 좁게 고칠 것을 권한다.** 제안("allowed ids를 `lost`/`rebind`에서도 뺀다")을 문자 그대로 읽으면, 허용 id가 head에서 **아예 없어진** 경우도 `lost`에서 빠진다.
* MOVE-TOTAL은 선언 단위의 삭제도 허용하는 문언이라 어긋나지는 않는다.
* 그러나 도구 이름이 `--allow-changed`이고, M10에는 필요 없는 범위다.
* '바뀜'으로 분류된 단위만 빼는 쪽이 정의 하나로 닫힌다.

**정확한 문안**(card 175행 끝 문장을 바꾼다):
> `--allow-changed`에 적힌 id(head 단위 `<경로>::<qualname>`)는 위 정의로 **`changed` 단위이되 `changed` 목록에만 적지 않는다**.
> 아래 `rebind`의 '`changed`로 이미 보고된 단위'와 `lost`의 '`changed`로 보고된 것'은 이 단위를 **포함**한다.
> 그래서 허용된 바뀐 단위의 base 짝(같은 파일·같은 (종류, 키))은 `lost`가 아니다. 그 단위 **자신**이 읽는 이름의 출처 변화도 `rebind`가 아니다.
> 다른 단위의 `rebind`와 `lost`, 그리고 head에 같은 (종류, 키)가 없는 허용 id(삭제)는 그대로 보고한다.
> (design 30 §3 MOVE-TOTAL "바뀐·새·사라진 단위는 M10이 선언한 것뿐" -- E6)

`rebind`(176행)·`lost`(186행)의 '보고된'을 '`changed` 단위인(허용 id 포함)'으로 바꿔도 같은 뜻이다. 둘 중 한 곳에만 적어야 정의가 하나로 유지된다.

**oracle 보강도 필요하다.** 지금 card의 어느 합성 단계도 `--allow-changed`를 쓰지 않는다(grep 0). 문언만 고치면 test가 이 경로를 겨누지 않는다. 필수 합성 단계 하나를 더할 것을 권한다(예: `allow-changed-declared`).
* base: 제자리 파일 `h.py`(N3.10 밖, `--split` 아님)에 함수 `run`.
* head: `run` 몸체가 새 MOD 파일 `mX.py`의 새 함수 `pipe`를 `from mX import pipe`로 불러 쓴다.
* `check --card ALL --base B --head H`를 다음 세 경우로 돌린다.
  * `--allow-changed <A>h.py::run <A>mX.py::pipe` → `changed`·`lost`·`rebind` 모두 [](그 밖 발견도 구성대로).
  * 허용 없음 → `changed` = {`run`, `pipe`}, `lost` [], `rebind` [](`changed` 단위라 제외).
  * `pipe`만 허용 → `changed` = {`run`}, `rebind` [].
* 음성 갈래: 허용되지 않은 다른 단위 `g`가 같은 이름을 import로 다시 묶으면 → `rebind`에 `g`. 허용은 그 id 자신만 덮는다.
* 삭제 갈래: 허용 id가 head에서 없어지면 → `lost`에 남는다(좁은 읽기).

이 단계가 없으면 문언 정정이 test로 고정되지 않는다. 그러면 '만든 것을 배선' 원칙상 E6의 그 경로가 검증되지 않은 채로 남는다.
