---
id: 20260930-restore-plan-functions
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-u02-d-list
approval: 20260930-restore-p5-test-list
approval: 20260930-restore-unwired-until-6a
---
## 의도

P5(`20260923-d-delete-dead`)가 "저장소 전체 참조 0"(R-0)으로 지운 8개 중 둘은 **계획서가 소비자·경로로 지정한 함수**였다 -- 삭제 판단에서 계획서의 미래
소비자를 확인하지 않은 오케스트레이터 결함이다(메모리 '만들기 전에 기록부터 확인' 위반). 사용자 결정(2026-09-30 "1번으로 되살리는 card", 범위 "계획 지정
2개만")으로 되살린다. A = `skills/analog-gmid-design/assets`.

| 함수 | 원래 위치 | 계획서 근거 |
|---|---|---|
| `lut_conditions_from_npz` | `sizing_recipe.py`(P5 base 0ecb686의 5371행 근처) | N3.3 S0 지문 "LUT 파일 내용 해시 + 생성 메타(`lut_conditions_from_npz`: corner, temp)", I-A5 "운영 경로에서 불리지 않는다 → 6a(S0에 배선)", MOD1 |
| `derived_spec` | `workspaces/run_harness.py`(0ecb686의 374행 근처) | DEC-26 "spec은 `canonical_spec()`만 정본이다. 변형은 `derived_spec(why 필수)`로만 만든다 -- 구현됨" |

둘 다 회로 무관(LUT 파일 메타·spec dict를 인자로 받는다)이고 엔진 식을 바꾸지 않는다. references 문서가 안내하는 나머지 P5 삭제 함수(`converge_with_parasitics`·
`slew_rate`·`render_stick_diagram`)는 계획 지정이 아니므로 되살리지 않고 문서를 사실에 맞추는 별도 card(B22)로 다룬다.

## 관찰 가능한 계약

1. **복원**: 두 함수가 원래 모듈에 다시 있고, docstring 포함 `ast.dump`가 P5 base(0ecb686)의 정의와 같다(바이트 그대로 복원 -- 이름·본문·docstring 불변).
2. **`lut_conditions_from_npz` 동작**: 인자 `npz_data`의 `files`에 `corner`·`temp_c`가 있으면 `{"recorded": True, "corner": str, "temp_c": float}`(있는 키만),
   둘 다 없으면 `recorded` 가 False이고 `note` 문자열이 있는 dict를 돌려준다(값을 지어내지 않는다). 저장소 LUT `A/sky130_nfet_pfet_lut_sample.npz`는
   `corner`('tt')·`temp_c`(27.0)를 기록하고 있어(2026-09-30 실측) `{"recorded": True, "corner": "tt", "temp_c": 27.0}`. 함수 docstring의 "저장소의 샘플 npz에는
   기록이 없다"는 낡은 문장이지만 바이트 복원(계약 1)이 우선이라 이 card에서 고치지 않는다(B22 문서 card에서 다룬다).
3. **`derived_spec` 동작**(0ecb686 원문 확인): `derived_spec(circuit_key, why, **overrides)`는 `why`가 비었거나 공백뿐이면 `ValueError`, 등록되지 않은
   `circuit_key`는 `canonical_spec`이 `ValueError`. override가 없으면 `canonical_spec(circuit_key)`와 같은 spec을, 있으면 **명시한 키만** 바꾸고 나머지는 정본과 같은
   spec을 돌려주며 그때 `_spec_source`에 바꾼 키와 `why`를 남긴다(override 없을 때는 남기지 않는다). `sizing_recipe.require_declared_spec_source()`가 이 선언을 강제하는 짝이다.
   `_spec_source` 문구에서 override 값이나 정본 값이 비지 않은 list·tuple이면 값 대신 `n<길이>`로 적는다(스칼라는 값 그대로) -- 원문 분기 확인. test는
   스칼라 override와 **list override**(예: 정본의 list 키를 길이가 다른 list로) 둘 다 판정한다(2차 시도 V3 생존 변이 3개가 이 분기였다). override가 없을 때의
   기대값은 피검 반환식과 같은 식(`canonical_spec(key)` 그대로)으로 만들지 않는다(V4 규칙 (2)) -- 성질로 판정한다(예: `_spec_source` 추가 없음, 키 집합과 각 값이
   정본과 같음을 키별로 보되 기대 dict를 피검과 같은 호출 한 번으로 만들지 않는 구성).
4. **P5 계약 test 조정**: `A/tests/contracts/test_d_delete_dead.py`의 삭제 이름 목록(GONE·G-1 판정 대상)에서 두 이름을 뺀다(남은 6개 판정은 그대로). 두 이름을
   합성 예시로 쓰던 판정기 자기 점검 케이스는 남은 삭제 이름으로 바꾸거나 그대로 두되 판정 강도를 낮추지 않는다. 이 조정은 V5 기준 변경이라 사용자 승인
   (DEC-40, R1 운반)이 필요하다.
5. **레지스트리**: §7 D 표에 두 행을 다시 넣는다 -- `처리` `보류(Phase 6a)`, 비고에 계획 근거(N3.3 S0·I-A5 / DEC-26)와 "P5에서 잘못 삭제 → 복원(이 card)".
   §1 집계를 맞춘다(`A/tests/tools/reg_check.py` exit 0).
6. **동작 보존**: E-LIB·E-INST가 base와 같다(두 함수는 운영 경로에서 불리지 않는다). 전체 스위트 FAIL 0.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `sizing_recipe` | `lut_conditions_from_npz` | `def lut_conditions_from_npz(npz_data) -> dict` |
| `run_harness` | `derived_spec` | `def derived_spec(circuit_key: str, why: str, **overrides) -> dict` |

## 판정 유형 근거

red-green: 두 함수가 base에 없어 계약 1~3 test가 base에서 red(AttributeError·ImportError 또는 AssertionError), code 커밋이 복원한 병합본에서 green. P5 계약 test의
목록 조정(계약 4)은 test 커밋에 든다.

## oracle 종류와 출처

(a) 구성 입력: 합성 npz 객체(`files` 속성과 키 조회를 갖춘 가짜)·합성 spec 변형 인자로 계약 2·3의 동작을 판정. (c) 동작 보존: 계약 1의 AST 기대값은 P5 base 0ecb686의
원본 정의(git 이력) -- auditor가 대조한다(test가 git 이력을 읽지 않는다, B28 참고). E-LIB·E-INST 기대값 = base 실행 결과.

## 거부해야 할 입력

`derived_spec`에 빈 `why` → 예외. 등록되지 않은 `circuit_key` → 예외. `lut_conditions_from_npz`에 기록 없는 npz → 값을 지어내지 않고 `recorded` False.

## library 회로 적용 여부

`derived_spec`은 `run_harness`에 등록된 회로 key(파일럿 등)로 판정. E-LIB·E-INST 적용.

## 무동작 판정 입력(무발동 값)

library 회로 전부와 기존 test 전부 -- 판정이 base와 같다(두 함수는 운영 경로 밖).

## 재현할 수치

없음.

## 결정 필요 항목

계약 4의 V5 승인(사용자, R1) -- 승인 기록 `20260930-restore-p5-test-list`. 복원 결정 자체는 사용자 결정(2026-09-30).

## 재시도 기록

1차 시도(2026-09-30, test 5db0187, code 874c95b): V5 발견(P5 계약 test 목록 조정) → 오케스트레이터가 base 판 `weakening_diff.py`로 diff 해시를 재고 1차 code로 green
(730 passed)을 먼저 확인한 뒤 사용자 승인 `20260930-restore-p5-test-list` → R1 운반. 1차 code-author 관찰: `workspaces/run_harness.py` 35행이 메인 저장소 assets 경로를
`sys.path` 맨 앞에 하드코딩해(기존 결함, review22 C-01·DF-35/36 Phase 4), 새 test가 `run_harness`를 먼저 import하면 worktree·격리 복제본이 아니라 메인 트리의
`sizing_recipe`를 잡는다. 2차 시도에서 새 test 파일은 `sizing_recipe`를 `run_harness`보다 먼저 import한다(V5 diff_path 밖이라 승인 해시 불변). 같은 id로 1부터 다시 한다.

2차 시도(2026-09-30, test 3fefdd7, code 06099fa, 판정 미커밋): 복원 대조(ast·원문 바이트·위치)·E-LIB·E-INST·V1·V5·V6 PASS. FAIL -- V7(두 def 미도달, 면제 승인
없음: 이 card가 '만들면 배선, 안 되면 승인'을 미리 다루지 않았다 -- 사용자 승인 `20260930-restore-unwired-until-6a`), V3(`derived_spec` list 값 `n<길이>` 서식 분기 변이 3개
생존 -- 계약 3에 list override 판정 추가), V4 규칙 (2)(override 없음 test의 기대값이 피검과 같은 `canonical_spec` 호출 -- 계약 3에 구성 제약 추가). 같은 id로 1부터 다시 한다.
엔진 blob은 그대로라 auditor 측정(복원 대조·E-LIB·E-INST)은 재사용한다. `test_d_delete_dead.py`는 운반 blob 그대로(V5 승인 유효).
