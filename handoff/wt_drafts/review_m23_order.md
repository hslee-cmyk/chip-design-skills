# 독립 검토: m2/m3 편집(M card 계약 3 (b) 이름 순서) + M10 모의 `order` 관찰 분류

검토자: 독립 verifier(작성자 아님). 2026-10-07. gate `master` = `2db7622`(검토 중 `863a037`로 전진 -- backfill spec card 문서 2개만 더함, design 30·엔진·도구 변화 0 -- `git diff --stat 2db7622 863a037`).
격리: `C:/g388`(TMP/TEMP = `C:/g388/tmp`, `git clone -c core.autocrlf=false --no-local`, origin 제거, 빈 hooksPath, cd 0회), 작업 끝 삭제(`ls -d /c/g388` → 없음). 실제 저장소 상태 변화 0(`git status`의 기존 `.bkit` 2파일 외 없음).

## 판정 요약

| 등급 | 수 | 내용 |
|---|---|---|
| B | 0 | |
| S | 0 | |
| minor | 3 | m-1 (b) 괄호 주석의 '대문자 → `_` 접두 → 소문자'는 첫 글자 기준 설명일 뿐 / m-2 stand-in 주석의 재측정 커밋 / m-3 SD 끝 줄 번호는 사슬마다 다름 |

`order` 관찰 분류: **예상된 중간 상태(transient)**. D0a 규칙 결함도 M9 card 결함도 아니다. **바꿔야 하는 card 문장 없음.**

## (1) m2/m3 편집 검증

### 1.1 M card 초안(M1~M6·M8·M9) vs `*.pre-m23.bak`

`diff` 결과 8개 파일 모두 바뀐 줄은 정확히 두 곳뿐이다.
* 14행(의도 문단): `` `from <MOD> import a, b, _c` `` 뒤에 `(design §2.2의 형태 예 -- 실제 이름 순서는 아래 계약 3 (b))`만 더함.
* 계약 3 (b) 줄(M1 43·M2 39·M3 36·M4 39·M5 35·M6 35·M8 39·M9 43행): `(`_` 접두 포함, 이름순, `as` 없음)` →
  `(`_` 접두 포함, `as` 없음; 이름 순서 = card base `plan` `reexports["<그 split 파일>"]`의 이 MOD 줄 그대로 -- D0a 계약 2 결정성 문단의 코드 포인트 순, 대문자 → `_` 접두 → 소문자)`.
  같은 줄의 나머지 부분(SD/SR/TL/DR/ACF 문장 열, 앞머리 묶음 정의, (c))은 바이트가 같다.
* 그 밖의 계약 절·실측·수치 줄: 바이트 같음(diff 결과 0).

### 1.2 D0a 결정성 문언과 맞는지

* D0a 계약 2 결정성 문단(`draft_p3_d0a.spec.md` 156~158행): "`from … import` 줄 안 항목 = 항목 문자열순", "이 card의 '이름순'·'문자열순'은 모두 코드 포인트 순"(det4 m-3). 새 (b) 문언은 순서를 따로 정의하지 않고 `plan` `reexports`의 그 MOD 줄을 **그대로** 쓰라고 한다 → 정의가 하나(D0a)뿐이라 맞는다. 옛 '이름순'은 대소문자 무시로 읽힐 여지가 있었는데 이제 없어졌다.
* `reexports` 모양(D0a 112행): `{"<split 파일>": ["from <MOD 줄기> import a, _b, …" MOD마다 한 줄]}`, 값은 그 split 파일에서 다른 파일로 배정된 단위가 바인딩하는 이름 **전부**. card k의 base에서는 앞 card 단위가 이미 A-0(제자리)이라서 MOD k 줄 = 이 card가 옮긴 이름이다. 그래서 (b)의 '이름 집합 = 그 파일에서 옮긴 단위가 바인딩하는 이름 전부'와 같은 집합이다. 같은 split 파일에 뒤 MOD 줄이 함께 있어도 '이 MOD 줄'로 골라내므로 모호하지 않다.
* 14행 괄호: design §2.2의 예 `a, b, _c`는 코드 포인트 순(`_c` < `a` < `b`)이 아니다. 그래서 '형태 예'라고 밝힌 것은 필요한 정정이다.
* **m-1(minor)**: '대문자 → `_` 접두 → 소문자'는 첫 글자에 대해서만 맞는 설명이다(A–Z 0x41–0x5A < `_` 0x5F < a–z 0x61–). 둘째 글자부터는 코드 포인트 비교 그대로다(예 `aB` < `a_b`). 정본은 앞 구절('`reexports` 줄 그대로', '코드 포인트 순')이고 이 구절은 설명이라 모순은 없다. 다만 앞에 '예:'를 붙이거나 '첫 글자 기준'을 덧붙이면 오독 여지가 사라진다. 고치지 않아도 판정은 바뀌지 않는다.

### 1.3 `mkcards.py`(p3kit_m2_m9)

diff는 135행(14행 문장 틀)과 195행((b) 끝 문장 틀) 두 곳뿐이다. 두 틀 문자열은 1.1에서 본 초안 문언과 글자가 같다(`%s` 자리 = 모듈 이름). M1 초안은 이 스크립트가 만들지 않으므로(독스트링) 따로 손으로 고친 것이 맞고, 문언도 같다.

### 1.4 stand-in `move_plan_sim.py`(p3kit_m1·p3kit_m2_m9 -- 두 파일 바이트 같음) / `move_plan_alltok.py`(p3kit_m2_m9)

세 파일의 diff 모양은 같다.
* 고치기 전: `huid in allow`이면 `continue`했다. 그래서 허용 id가 `changed_ids`에 들어가지 않았고, 허용된 단위의 base 짝은 `lost`, 그 단위의 읽기는 `rebind`로 나왔다(det3 문언 결함 = X-1).
* 고친 뒤: 옮긴 단위도 base 같은 단위도 아니면 먼저 `changed_ids.add((p,k,q))`를 하고, 허용 id면 `changed` 목록에만 적지 않는다.
  * `lost`는 `(p,k,q) in changed_ids`를 빼므로 허용 단위의 base 짝이 빠진다.
  * `rebind`도 `(p,k,q) in changed_ids` 단위를 건너뛰므로 허용 단위 자신의 읽기는 보지 않는다.
  * 다른 단위의 `rebind`는 그대로 나온다(D0a 단계 (4)).
  * head에서 지워진 허용 id는 H 단위에 없어 `changed_ids`에 들지 않으므로 base 짝이 `lost`로 남는다(단계 (5)).
  
  D0a 계약 4 `--allow-changed` 문장(178~181행)과 det4 결정 (9)의 좁은 읽기에 맞는다.
* 실측 확인(아래 2절 사슬, F2+M10 head): 허용 있음과 없음의 발견 차이는 `changed`에서 정확히 두 id(`workspaces/run_harness.py::run`, `…/gmid_design_pipeline.py::run_gmid_design_pipeline`)뿐이다. `lost` 110/110·`rebind` 33/33은 같아서 허용이 `lost`·`rebind`를 새로 만들지 않는다. 같은 head에서 M10이 없는 F2 head와 비교하면 `run_harness.py::run`의 `rebind` 6건(F1이 바꾼 import 출처)이 허용 실행에서 사라진다. 계약상 `run`은 `changed` 단위라서 자기 읽기를 보지 않으므로 의도대로다.
* 위치(옛 `or huid in allow` 제거)와 순서 모두 맞다. `method-in-moved-class` 갈래에는 허용을 적용하지 않는데, 계약도 허용 id를 head **최상위 단위**로 정의하므로 맞다.
* **m-2(minor)**: 새 주석 `# NOT det~det5: … current tree has 0 such keys (D0a det3 re-measure 6c724de)`의 근거 커밋은 `6c724de`이다. 이번 gate `2db7622`에서 다시 잰 값이 아니다. stand-in이 측정 전용이고 (e5)·(e6)을 구현하지 않는다고 밝혔으므로 수치 영향은 없다. 다음에 그 수를 인용할 때만 재측정 커밋을 적을 것.

## (2) `order` 관찰 분류

### 2.1 규칙 문언

* D0a 계약 4 `order`(194행 부근): `--card ALL`이면 head의 **모든 MOD 파일**을 자기 번호 k로 보고, import 대상 f가 N3.10 파일이며 번호 ≥ k이면 발견으로 센다. SD = MOD7이 `instance_report_builder`(MOD9)를 import하면 9 ≥ 7이라 발견이 맞다. **규칙은 문언대로 동작했다.**
* design 30 §2.2 D-22 (1)·(4): SD의 MOD 8·9 재수출은 SD 끝에 둔다. 이 위쪽 import는 "M9~F1 동안 `import_layering`이 큰 번호로의 import로 보고한다 … F2가 SD의 위쪽 재수출을 지우면 사라진다".
* §3 LAYER: "M9~F1 중간 상태의 SD → MOD9 임시 재수출은 이 판정의 대상 시점이 아니다".
* §3 ORDER(card k 판정)는 `--card` 파일(MOD k)만 본다. 그래서 M9 card 판정(`--card instance_report_builder.py`)은 SD를 보지 않고, M10 card도 `--card gmid_design_pipeline.py`(초안 87행)라서 이 발견이 나오지 않는다.
* §8 F2 행: `stick_diagram` 임시 재수출 제거, 판정 = LAYER(`import_layering` exit 0).
* §10 E6: F2 뒤 최종 H에서 `check --card ALL --allow-changed <2>` exit 0.

따라서 `--card ALL`을 **중간 판(M9~F1, M10 포함)**에서 돌리면 `order` 1이 나와야 정상이다. 그 판은 어느 card 판정에서도 `--card ALL`로 재지 않는다. `--card ALL`을 판정으로 돌리는 곳은 F2 계약(초안 30행, head = F2)과 DoD E6(head = 최종 H)뿐이다.

### 2.2 '재수출 줄은 `order`에서 면제해야 하는가'(D0a 규칙 결함 여부) -- 아니다

면제하면 F2가 SD의 MOD9 재수출을 남긴 결함(F2 초안 107행 '계약 5·6 (b) FAIL' 입력)을 E6이 놓친다. design은 이 위쪽 import를 LAYER(E1)와 같은 위반으로 본다. 중간 판에서 나오는 것은 design이 명시한 임시 상태이고, 판정 시점(F2 head)에서는 없어야 한다. 규칙을 고칠 이유가 없다.

### 2.3 M9 card 결함 여부 -- 아니다

M9 계약 3 (b) "SD = base 열 − 옮긴 단위 + 파일 **끝**에 재수출 하나"는 design D-22 (1) 그대로다. M9가 `--card ALL`의 `order` 0을 약속하는 문장은 없다.

### 2.4 실측: 사슬 M9 → F1 모의 → F2 모의(+ M10 모의)

* 사슬: `p3kit_f12/mk_chain_r1.sh C:/g388 <저장소> g1_kit/install_proto.py 2db7622`
  * 커밋: `5eec1f1` G1 → `fd1f069` M1–M9 → `5b5ae24` M9 fix → `20e987e` F1 모의 → `b144f4b` F2 모의
  * `mk_f2.py`: SD 재수출 57이름 중 49개를 지우고 8개를 남겼다(MOD2·MOD3 출처). **MOD9 8이름은 모두 지워졌다** -- SD 남은 단위가 읽지 않는다.
* M10 모의(`p3kit_m10_t1/gen_m10b.py`):
  * `892a8e0` = M9 fix + M10
  * `ab0a5d8` = F2 모의 + M10
  * 둘 다 생성 exit 0(파일 2개: `gmid_design_pipeline.py` +79줄, `run_harness.py`)
* 고친 stand-in으로 `check`를 돌렸다(`p3kit_m2_m9/move_plan_sim.py check --card ALL "${MP_ARGS[@]}"`, `MP_STMT_KEY=names`, base = `5eec1f1`).

| head | 허용 | `order` |
|---|---|---|
| `892a8e0`(M9 + M10) | 두 id | **1** -- `stick_diagram.py:4981` imports `instance_report_builder.py` |
| `20e987e`(F1 모의) | 없음 | **1**(같은 줄) |
| `b144f4b`(F2 모의) | 없음 | **0** |
| `ab0a5d8`(F2 + M10) | 두 id | **0** |
| `ab0a5d8`(F2 + M10) | 없음 | **0** |

`b144f4b`에서 SD 최상위 `from <N3.10> import`는 41행(MOD3)과 42행(MOD2)뿐이고, `from instance_report_builder`는 없다. **`order` 발견은 F2에서 사라진다** → 예상된 중간 상태로 확정한다.

* 한계(판정 영향 없음, 기록만):
  * 이 사슬은 근사 배정 모의(`sim_m_d31.py`)다. base는 D0b 재생성 전(G1)이다.
  * 그래서 다섯 실행 모두 `order` 밖에서 큰 잡음이 나온다: `move-set` 107, `move-rejected` 107, `changed` 115~117, `lost` 107~110, `rebind` 23~39, `import-dup` 8. 사슬의 이동이 stand-in `plan` 배정과 다르기 때문이다(F2 이전 판에도 똑같이 있으므로 F2·M10과 무관).
  * 즉 이 측정은 '`order`가 F2에서 사라진다'와 '허용 의미'만 보여 준다. E6 전체 exit 0 모의는 아니다(DoD 초안 208행의 '전체 모의 없음' 그대로).
* **m-3(minor)**: SD 끝 재수출 줄 번호는 사슬마다 다르다. 이번 2db7622 근사 사슬은 4981, M9 초안 21·103행의 2183f2e card 자료 사슬은 4971, F2 초안 203행 00a79a1은 4981이다. M9 초안 21행은 '관찰'로 적혀 있고 위치 규칙은 'SD 파일 끝'이라 판정과 무관하다. DoD 초안 209행의 '4971행'도 '관찰'이라 문제없지만, 인용할 때는 사슬 이름을 함께 적는 것이 좋다.

## (3) 바꿔야 하는 card 문장

**없다.**
* D0a 계약 4 `order`: 그대로 둔다(면제하면 F2 결함을 E6이 놓친다).
* M9: 그대로 둔다.
* F2 계약(초안 30·40·107행): 이미 F2 head `order` 0·LAYER exit 0·남기면 FAIL을 단언한다.
* DoD 초안 209행(v4r 관찰 문단): 이미 'F2 전 상태라 기대된 모양, 최종 H에서 남으면 E6 FAIL'로 적혀 있고 이번 실측과 맞는다.

선택 사항(필수 아님): DoD 209행에 "2db7622 근사 사슬 실측: F1 모의 head `order` 1 → F2 모의 head 0(M10 유무 같음), `review_m23_order.md`"를 한 줄 덧붙일 수 있다.
