# review -- draft_b37a.spec.md (20260930-b37a-ports-roles)

검토자는 작성자가 아닌 독립 reviewer다. 저장소는 읽기만 했다(HEAD = gate `master` `7535799`. `git status`는 시작할 때와 같다).
scratch는 `C:/g63`이다. `git archive HEAD`로 만든 사본 `base`, 범위 1~4를 구현한 모의 `head`, `head`에 픽스처를 보강한 두 사본 `head_fx`·`head_dm`을 썼다.
모의 `head`에서 거부 예외는 `ValueError`로 대신했다(CC-4a 전이기 때문이다).
치환할 문자열은 정확히 1회 나오는지 assert로 확인했고, import한 모듈 경로가 사본 아래에 있는지도 assert로 확인했다. 인터프리터는 `C:/Python314/python.exe -B`, `PYTHONHASHSEED=0`이다.
측정을 마친 뒤 `C:/g63`은 삭제했다.

## 요약 판정

| 등급 | # | 요지 |
|---|---|---|
| **blocking** | B1 | 계약 3의 불변 범위 문장("포트 넷과 `HINT_INPUT`에 걸리는 넷까지")이 병합본에서 거짓이다. 비포트 게이트 전용 넷이 `HINT_INPUT`에 걸리면 head에서도 결과가 이름에 따라 달라진다(실측 반례). 또 oracle이 엔진 정규식 `netclass.HINT_INPUT`을 import해 바꿀 넷을 고르므로 B37b와 충돌한다. 정규식이 필요 없는 대안 oracle(레일 밖 넷 **전부** 이름 바꾸기)을 실측했다: base 3/9 FAIL(같은 red), head 9/9 |
| **blocking** | B2 | "기존 test 기대값 변경 0 → DEC-40 아님"은 픽스처에 **어떤 넷을** 선언하느냐에 달려 있다. 자연스러운 선택(입력 소자 게이트)이면 s040·s041이 review 게이트로 새로 실패한다. 18/18이 살아나는 것은 netlist에 **없는** 가짜 넷을 입력으로 선언할 때뿐이다. 그 가짜 선언이 통과하는 것도 접근자가 존재 여부를 검사하지 않기 때문이다(포트 = 레일, 빈 이름도 통과). '입력 role ≥ 1 필수' 규칙이 신호 입력이 없는 픽스처에 거짓 선언을 강요한다 |
| **blocking** | B3 | 'red 모양' 권고 `try / except Exception: pytest.fail`은 `KeyError`·`TypeError`(허용 밖)를 `Failed`(허용)로 세탁한다. B26-1의 V2 선례("새 키워드 `TypeError`는 red로 세지 않는다")와 어긋난다. 계약 5에는 독립된 base red가 없다. 계약 8을 `monkeypatch.setattr`로 쓰면 red로 기록되지 않는다(실측) |
| should-fix | S1 | (확인 1)은 '확인'만으로 닫을 수 없다. "틀린 값이 새로 생기지 않는다", "base 제안은 오분류 결과"는 소자 단위 회로 해석이다. 동작이 바뀌는 3회로(ngcc·sf_pushpull·two_stage_ota_sf)의 `ports`에는 파일 안에 '사용자 확정' 기록이 없다. card가 근거로 든 "파일별 `_comment`의 '사용자 확정'"은 9개 중 3개 파일에만 맞는다 |
| should-fix | S2 | (확인 2) '출력은 포트만'은 B37b의 전제이고, `_reaches_output`/`m_cascode` 방향 판정의 회로 해석(6a DEC-65·J 공동분석)이다. B37a 승인 기록에서 빼야 한다. 그리고 B37a 뒤에도 실효 출력은 포트 ∪ `HINT_OUT` SIGNAL 넷이다 |
| should-fix | S3 | V3: "B26-1 U1 결과를 그대로 따른다, 새 결정 없음"은 U1 = 1일 때 거짓이다. 면제는 def 해시에 묶이므로, B26-1이 같은 3 def에서 받은 면제는 B37a에서 모두 풀린다. 그러면 새 면제 승인이 필요하다. A1을 착수 조건으로 명시하고, N2 대상(감싸는 제어문 포함)으로 다시 셀 것 |
| should-fix | S4 | B26-1과 겹치는 지점이 card 문장에 반영되지 않았다: 경로 3 호출의 `rails=`, `port ∩ supply_nets` 검사(NC 1b가 레일 분류를 덮어쓴다), `test_s013` 둘째 호출의 `ports` 출처, `meta["device_roles"]`가 `None`일 수 있음 |
| should-fix | S5 | 착수 시 재측정 목록이 1(a)(e)·7뿐이다. 승인 기록에 붙는 E-LIB·E3 차이표(1(c))도 실제 base(B34·B26-1·Phase 3·CC-4a 뒤)에서 다시 재고, 표를 잰 base 커밋을 승인 기록에 적어야 한다 |
| should-fix | S6 | MG2: `direction` 일치 검사는 MG2가 고쳐야 하는 분기가 된다(`direction`을 거부하게 되므로). 계약 test의 합성 topology가 모두 `direction`을 들고 있으면 MG2가 B37a test를 고쳐야 한다 |
| minor | M1~M5 | 줄 번호 3292 → 3293, `references/analog-grammar-integration.md` §5 소비자 누락, V4 규칙 (3), GB0와의 정본 관계, 연결 파일 픽스처 주의 |

**재측정으로 맞은 것**:
* 줄 번호: SD 8550·8643~8644·8668~8671·3261·3282·3845·3855, SR 4481·4511~4519·4806·4831~4833·6470·6537·6543·6572·7930·8060~8062. 3292만 틀렸다(M1).
* `ports`·`direction` 소비자는 SR 4511·4519·4833뿐이다(`*.py`).
* 운영 `resolve_stack_layout` 호출자는 SR 8060 하나다. `input_referred_offset_pairs` 호출자는 SR 4552·4588이다.
* library `ports` 9/9, role 6어휘, `direction` 모순 0, `_TEMPLATE` `ports` 없음.
* 계약 4: base `{M3,M5}` → head `{M2..M6}`.
* 계약 5: 관찰값이 card와 같다.
* 계약 6: 단일 파일 11가지를 base는 전부 받고, head는 전부 거부한다.
* 계약 7: base `[]` → head `[["M1","M2"]]`.
* 계약 8: 1 → 2 → 2.
* E-LIB 차이표·E3 차이표: 소자·필드까지 card와 같다.
* V3: 6 def, 변이 641(내 접근자 구현이 23개라 card의 22와 1 차이), `_build_theta_evaluator` 497.
* pytest: base 42 failed·756 passed·15 xfailed, head 새 실패 18(card 목록과 같은 집합).

---

## B1. 계약 3 -- 불변 범위 문장이 거짓이고, oracle이 피검 정규식에 기댄다

**실측**(`rename2.py`, 합성 `tele`, 입력 `sig_a`/`sig_b`): 캐스코드 게이트 넷 `nc`를 `in2`로 바꿨다. `in2`는 비포트이고 게이트 전용이며 `HINT_INPUT`에 걸린다.
card 계약 3 규칙대로 포트 ∪ `HINT_INPUT` 넷 = `[in2, o2, sig_a, sig_b]`를 `ZQ<i>Q`로 바꿔 meta를 비교했다.

| 사본 | 결과 |
|---|---|
| base | 다름 |
| **head(병합 상당)** | **다름** -- `_device_roles_autofilled`/`device_roles`의 M3·M4. 원래 이름(`in2` = INPUT 힌트)에서는 `headroom_role` 없음, 중립 이름(BIAS 기본값)에서는 `cascode` |

* 원인: NC 1c(netclass 113~124)는 선언되지 않은 게이트 전용 넷마다 `HINT_INPUT`을 **항상** 적용한다. B37a는 포트만 선언하므로 비포트 게이트 전용 넷은 여전히 이름으로 분류된다.
* 그래서 '이 card의 불변 범위 = 포트 넷과 `HINT_INPUT`에 걸리는 넷'은 library에 그런 넷이 없어서 성립한 관찰일 뿐 계약이 아니다.
* test-author는 card 문장만 보고 이런 합성 입력을 정당하게 만들 수 있다. 그러면 head에서 green이 실패하고 dispute로 간다(과거 재시도 원인과 같은 유형). 준비 자료 §4.2 C1의 같은 문장도 틀렸다.
* 대조(같은 스크립트): 꼬리 게이트(`nb` → `vi1`·`inp`)를 바꾼 변형은 head에서 같았다. 결과가 갈리는 것은 그 넷이 캐스코드·신호 경로의 분류를 바꿀 때뿐이다.

**oracle 독립성.** 바꿀 넷 집합을 `netclass.HINT_INPUT.match`로 고르게 하면 다음 문제가 생긴다.
* test가 analog-grammar 내부 기호를 import한다. test-author는 그 import 경로(`skills/analog-grammar/assets`의 `sys.path` 주입)를 interface card로 알 수 없다.
* B37b가 그 정규식을 라이브러리 경로에서 옮기면 B37a 계약 test가 깨진다.
* 피검 구현의 이름 규칙으로 test 입력을 만드는 셈이라, V4 (1) 식에는 걸리지 않아도 auditor `checks.V4.basis`의 독립성 판단을 흐린다.

**대안 실측**(`rename_all.py`): library 9회로에서 `supply_nets` 밖의 넷을 **전부** 바꿨다. 범위는 트랜지스터 단자, `passive_elements`·`ideal_sources` 단자, `ports` 키다.

| 사본 | 불변 | 깨지는 회로 |
|---|---|---|
| base | 6/9 | current_reuse·ngcc·pushpull(card 계약 3의 red와 같은 3회로, 같은 키) |
| head | **9/9** | 없음 |

**고칠 것.**
1. library 판의 바꿀 넷 집합을 'supply_nets 밖의 모든 넷'으로 바꾼다. 정규식 import가 필요 없고, red·green이 card 수치와 같다.
2. 합성 판(4변형)은 **포트 넷만** 바꾼다. 지금도 사실상 그렇다.
3. 경계 문장을 고친다: "비포트 넷(게이트 전용 넷의 `HINT_INPUT`·`HINT_BIAS`·`HINT_FB`·`HINT_CLK`, SIGNAL 넷의 `HINT_OUT`)의 이름 의존은 B37b가 닫는다. test는 비포트 넷 이름만 바꾸는 합성 변형을 이 card의 계약으로 쓰지 않는다."
4. 준비 자료 §4.2 C1 문장도 같은 취지로 고친다(오케스트레이터 문서).

## B2. 픽스처 보강 -- "기대값 변경 0"은 넷 선택에 달려 있고, 가짜 선언이 통과한다

**실측**(모의 head + 두 selftest 파일에서 `json.dump`를 감싸 합성 topology에 `ports`를 넣는 측정 장치, `test_s013` 두 호출에 `ports=`. 판정 설정은 card의 pytest 명령 그대로):

| 사본 | 결과 | base(42 failed) 대비 |
|---|---|---|
| head(보강 없음) | 56 failed·4 errors | 새 18(card와 같은 집합) |
| `head_dm`: 입력 = netlist에 **없는** 넷 `zz_b37_dummy_in` | 43 failed | 18개 전부 회복. 새 1 = `test_ic3::test_linked_topology_files_merge_and_collision`(측정 장치가 프로세스 전역 `json.dump`를 바꿔 연결 파일 `part_b`에도 `ports`를 넣은 결과. 실제 픽스처 편집에서는 생기지 않는다 -- M5) |
| `head_fx`: 입력 = 첫 소자 중 다이오드가 아니고 게이트가 레일이 아닌 소자의 게이트 넷(자연스러운 선택) | 45 failed·1 error | **새 `test_s040_VGS`·`test_s041_section`**(`optimize_full_circuit_budget() 실행 전 review가 필요하다`) + `s071`(연결 파일마다 다른 입력을 고른 장치 결과) + 위 `test_ic3` |

* s040 픽스처(`_vmv_test`)는 바이어스 컬럼 4소자이고 **신호 입력이 없다**(게이트 `vb_ka`·`vb_ma`·`vb_kb`·`NodeA`). s125는 PMOS 둘(게이트 `vb`)이다.
* '입력 role이 하나도 없으면 거부'(계약 6) 때문에 test-author는 거짓 입력을 선언해야 한다.
  * 실제 넷을 선언하면 엔진 분류가 바뀌어 기존 판정이 깨진다(s040·s041).
  * 깨지지 않는 길은 netlist에 없는 넷을 선언하는 것뿐이다.
* 그 길이 열려 있는 것은 접근자가 존재를 검사하지 않기 때문이다. 모의 head 실측(card 범위 밖 입력):
  * netlist에 없는 포트 넷 → 통과
  * 포트 = `vdd`(레일) → 통과. NC 1b는 선언을 레일(1a) 위에 덮어쓴다(준비 자료 §1.1).
  * 빈 문자열 넷 이름 → 통과
  * 모두 조용한 무시이거나 레일 오분류다.
* 결론: "selftest 18곳 픽스처 보강 = 입력 보강이지 기대값 변경 아님 → DEC-40 아님"은 **가짜 넷 선언을 전제로만** 참이다. card는 test-author에게 넷 선택 규칙을 주지 않았다.
  * test-author는 소스를 볼 수 없다. 그래서 자연스러운 선택 → 실패 → dispute로 가거나, 실패를 피하는 넷을 탐색하게 된다(기준에 맞춰 입력을 고르는 일).

**고칠 것(원칙 기본안 + 사용자 몫 구분).**
1. 접근자 거부 목록에 둘을 더한다. 근거는 선언은 사실이어야 한다는 원칙과 조용한 무시 금지다.
   * 포트 넷이 트랜지스터·수동소자·이상원 단자 어디에도 없음
   * 포트 넷 ∈ `supply_nets`(B26-1 뒤에는 `meta["rails"]`로 판정할 수 있다)
2. '입력 role 0개 거부'는 원칙으로 정해지지 않는다. 기본안을 B26-1 선례(`supply_nets: []` = 명시적 '레일 없음' 수용)와 맞춘다.
   * **`ports` 키 없음·null·dict 아님·항목 형식 오류는 거부하고, 명시적 `ports: {}`(입력 0)는 받는다.**
   * 입력 0인 topology에서는 E1~E3가 지금과 같게 동작한다. 비포트 넷 정규식은 어차피 B37b까지 남는다.
   * `input_referred_offset_pairs`는 offset 쌍이 있는데 입력이 0이면 지금처럼 거부를 **유지**한다(card 범위 4의 'ValueError 삭제'를 '입력 0 + offset 쌍 있음일 때 거부'로 바꾼다).
   * 이렇게 하면 픽스처는 `ports: {}`나 실제 포트로 정직하게 보강된다. s040·s041·s125의 판정도 바뀌지 않는다(head_dm과 같은 효과, 단 가짜 넷 없이).
3. 사용자가 '입력 0 거부'를 유지하길 원하면, 신호 입력이 없는 기존 픽스처의 판정이 바뀐다는 사실(s040·s041 실측)을 승인 기록에 적어야 한다. 그때는 DEC-40·V5 대상인지 다시 판단해야 한다.
4. 어느 쪽이든 card '작성 전 실측' 7에 픽스처별 선언 규칙을 적는다(test-author가 소스 없이 따를 수 있게).
   * 신호 입력이 있으면 그 게이트 넷, 없으면 `{}`
   * 연결 파일(`part_b` 등)에는 `ports`를 넣지 않는다

## B3. red 모양 -- 허용 밖 예외의 세탁, 계약 5·8의 red 근거

* 00-common §8.1 허용 예외는 `AssertionError`·`Failed`·신규 심볼 import 오류뿐이다. 플러그인은 예외 **타입**만 본다(`merge_gate._RedCapture.record`).
  * `try: … except Exception as e: pytest.fail(…)`로 감싸면 base의 `KeyError`(`meta["ports"]`)·`TypeError`(`ports=` 키워드)가 `Failed`로 기록된다.
  * 그 규칙이 막으려던 '동작이 아니라 인터페이스 부재로 생긴 실패'를 red로 세는 우회다.
  * B26-1 card는 같은 상황을 "`TypeError`는 red로 세지 않는다. red는 시그니처가 안 바뀌는 진입점이 맡는다"고 나눠 적었다. B37a 권고는 그 선례와 반대다.
* 실측(`contracts.py`, base, 자연스러운 test 모양):
  * 계약 2: `meta["ports"]` → `KeyError`
  * 계약 5: `KeyError`, 또는 `meta.get` 모양이면 `TypeError`
  * 계약 8: 플러그인이 신규 심볼로 인정하지 않는 `AttributeError`(아래)
* **계약 2**: `assert "ports" in meta`가 정직한 red다(계약 내용이 'meta가 선언을 싣는다'이므로). 이 모양만 권고한다.
* **계약 5**: base에서 같은 test로 관찰할 수 있는 E3 동작 red가 없다.
  * 같은 입력을 base 시그니처로 부르면 네 변형이 실제로 다르다(`sig_a`·`vin_p`·`Vinp` `[M0,M1,M2]`, `Vip` 단독). 하지만 head에서는 `TypeError`라 같은 test가 될 수 없다.
  * `assert "ports" in meta`를 앞에 두는 모양은 계약 2의 red를 빌려 쓰는 것이다.
  * card에 정직하게 적는다: "계약 5의 base red는 계약 2 몫이다. E3 배선의 증거는 계약 9의 E3 차이표(auditor)와 호출 그래프다." 판정 기록도 두 종류를 나눠 적는다(B26-1 방식).
* **계약 8**: `monkeypatch.setattr(M, "port_declaration", wrap)`가 base에서 내는 `AttributeError`에는 `obj`·`name` 속성이 없다(pytest 9.0.2 실측: `AttributeError("<module 'stick_diagram'> has no attribute 'port_declaration'") obj=None name=None`).
  * 그래서 `merge_gate.new_symbol_pair`가 `None`을 돌려주고 red로 기록되지 않는다.
  * 원래 함수를 먼저 `orig = M.port_declaration`으로 읽는 모양이면 인터프리터 `AttributeError`(obj = 모듈, name = 심볼)가 나서 신규 심볼 red가 된다. 이 모양을 계약 8에 적는다.
* 권고 모양을 따르다 assert를 `try` 안에 두면 V4 규칙 (3)('assert가 if·try 안에만 있음')에 걸린다. 'red 모양' 절에서 try/except 권고를 지우면 함께 해소된다.

---

## S1. (확인 1)은 회로 해석을 포함한다 -- '확인'이 아니라 근거를 갖춘 결정으로

* 차이표는 재현했다(`elib.py`).
  * ngcc: M1 `cascode`, M4·M6B·M7 `mirror` 소실
  * sf_pushpull: 20개 소실(M1·M2 `cascode`, M5~M22)
  * two_stage_ota_sf: 5개 소실
  * nmcnr review 12 → 10, two_stage_ota review 9 → 7
  * E3 그룹: ngcc `[M0,M1,M2]` → `[M1,M2]`, sf_pushpull `[M17,M18]`·`[M19,M20]` 분리, two_stage_ota_sf `[M8,M9]` 분리
  * 새로 생긴 값은 0이다.
* card 문장 중 원칙으로 말할 수 있는 것: "base 값은 이름 정규식이 입력을 BIAS로 분류한 **유도**에서 나왔다(유도가 무효)."
* 원칙으로 말할 수 없는 것(소자별 회로 해석):
  * "base 제안은 오분류 결과다"(값 자체가 틀렸다는 판정)
  * "틀린 값이 새로 생기지 않는다"
  * card 스스로 적었듯, 선언 4회로에서 입력쌍 `headroom_role`은 `cascode`다. 그러니 세 회로 입력쌍의 base `cascode`는 사람 관례와 **같은 값**이었다. B37a는 그 값을 근거 없는 값에서 `None`으로 바꾼다.
  * M5~M22의 `mirror`/`cascode`가 맞았는지는 재지 않았다.
  * 사용자 기록 규칙상 이런 해석은 혼자 판단하지 않고 공동분석한다.
* 근거 문장도 틀렸다. card는 "`ports`는 사용자가 확정한 선언이다(DEC-35, 파일별 `_comment`의 '사용자 확정')"라고 적었다. 실측(library `ports._comment`):

  | 기록 | 회로 |
  |---|---|
  | '사용자 확정' | folded_cascode, nmcnr_amplifier |
  | '사용자 확인' | current_reuse |
  | 목적 설명만 | two_stage_ota, common_gate |
  | 주석 없음 | ngcc, pushpull, sf_pushpull, two_stage_ota_sf |

  * 동작이 바뀌는 3회로는 모두 주석이 없다. ngcc는 추가 커밋 `5459a44` 메시지의 "사용자 확정 넷 표"가 근거일 수 있으나, card가 그것을 인용하지 않았다.
  * DEC-35 절차(제안 → 표 → 사용자 확인)와 J9 ports ratify는 6a-2 항목이다.
* **고칠 것.**
  * 승인 기록 문안을 "유도가 이름 의존이라 무효 → 자동 채움을 비운다(값의 옳고 그름은 6a J ratify)"로 쓰고, '틀린 값이 새로 생기지 않는다'는 판정 문장을 뺀다.
  * 동작이 바뀌는 3회로(그리고 주석 없는 pushpull·common_gate)의 `ports`를 이 card의 입력으로 쓴다는 사실을 사용자에게 함께 확인받는다. 회로별 근거(커밋·주석)를 표로 붙인다.
  * B37a 뒤 이 회로들의 행동은 그 선언으로 정해지기 때문이다. DEC-35 '확인' 단계를 건너뛰지 않는다.
  * 이것은 승인이 필요한 결정이다(동작 변경 + 선언 근거 확인). '확인 사안'이라는 표현은 뺀다.

## S2. (확인 2) '출력은 포트만'을 B37a 승인 기록에서 뺄 것

* B37a 뒤에도 NC 1e는 SIGNAL 넷에 `HINT_OUT`을 적용한다. 그래서 E1~E3의 실효 출력 = 포트 ∪ {SIGNAL이고 `HINT_OUT`에 걸리는 넷}이다.
  * B37a가 바꾸는 것은 선언 출력이 **처음으로** `_reaches_output`(idioms 79~)에 들어간다는 점이다. 기존에는 `outputs` 미선언이라 정규식 출력만 들어갔다.
  * 이 변화의 library 효과는 S1 차이표에 이미 들어 있다.
* '출력 = 포트만'(B37b 뒤 `Vom1`/`Vop1`·`O1`·`OUT`이 SIGNAL이 됨)은 `m_cascode` 방향 판정에서 무엇을 '출력'으로 볼지의 회로 해석이다. 계획 6a의 DEC-65 출력 방향 분류·J ratify와 같은 축이다.
* B37a 기록에 '기본안 포트만, 확인만'으로 미리 넣으면, B37b의 회로 해석을 공동분석 없이 앞당겨 정하게 된다.
* **고칠 것**: (확인 2)를 지우고 B37b card의 결정 항목으로 옮긴다. B37a 범위 밖 절에 "실효 출력은 포트 ∪ `HINT_OUT` SIGNAL 넷(B37b까지)"을 사실로만 적는다.

## S3. V3 계획 -- A1 미결정과의 정합

* 수치 재현: 모의 head에서 `mutate_changed.changed_defs` = 6 def, `mutants` 합 641. 내 `port_declaration`이 23개라 card(22)와 1 차이가 난다. 나머지 def(`load_topology` 63, `input_referred_offset_pairs` 22, `_load_full_topology_cached` 10, `resolve_stack_layout` 26, `_build_theta_evaluator` 497)는 card와 같다.
* **U1 = 1이면 '새 결정 없음'이 거짓이다.**
  * `load_topology`·`resolve_stack_layout`·`_build_theta_evaluator`는 B26-1이 이미 V3 대상으로 삼는 def다(B26-1 card 표: 65/26/498).
  * B26-1이 이 def들의 등가 변이를 면제로 처리하면, 면제 원소는 `<id>@<묶기 해시>`라서(`20260930-v3-exempt-binding`) B37a가 def를 바꾸는 순간 전부 풀린다.
  * 그러면 B37a는 같은 등가 변이를 **새로** 면제 승인받거나 test로 죽여야 한다(사용자 승인 = 새 결정).
  * card는 이 사실을 'U1 = 1이면' 단락에서 언급하지만, 결정 항목 2의 "새 결정이 아니다"와 모순된다.
  * 같은 def를 두 card가 연달아 바꾸는 비용은 B34 검토 S5와 같은 뿌리다.
* 기존 인벤토리 실행을 하지 않았으므로, U1 = 1의 확정 생존(어떤 test도 실행하지 않는 줄) 수가 없다. B26-1에서는 그 수가 298이었다.
* **N2 정의와 근사의 차이**: card의 '35개'는 줄 diff 근사다. `draft_v3_scope_policy`의 N2는 감싸는 복합문의 자기 필드 변이와 그 복합문의 `stmt_delete`를 더한다. 모의 head에서 바뀐 줄을 감싸는 복합문:
  * `load_topology`의 `for rel_path in linked:`(연결 파일 `ports` 검사가 루프 안에 있다)
  * `input_referred_offset_pairs`의 `if "input_offset_pairs" not in entry:`
  * `_build_theta_evaluator` 8060 문장은 최상위라 추가가 없다.
  * 이 추가분은 계약 2(연결 파일)·계약 7·8로 죽을 것으로 보이지만 재지 않았다.
* **고칠 것.**
  * 착수 조건에 "A1(V3 범위) 결정"을 명시한다.
  * 결정 항목 2를 다음처럼 바꾼다: "U1 = 2이면 새 결정 없음. U1 = 1이면 B26-1 면제는 승계되지 않고 B37a용 면제(해시 묶음) 또는 test 보강이 필요하다 -- 사용자 승인 항목이 생긴다."
  * U1 = 1이면 freeze 전에 3 def의 기존 인벤토리 실행으로 생존 목록을 잰다.
  * 근사 표 옆에 N2 기준 대상(위 두 복합문 포함)을 적는다(착수 시 도구 `targets_by_def`).

## S4. B26-1과 겹치는 지점

1. **경로 3 호출**: B26-1 뒤 `resolve_stack_layout` 경로 3은 `refine_differential_and_mirror_relations(transistors, *, rails)`를 부른다. B37a 범위 3과 계약 문장은 `refine_…(transistors, ports.inputs, ports.outputs)`로 적어 `rails=`가 빠졌다. "B26-1 뒤 모양 `…, ports.outputs, rails=rails`"로 적는다. E1·E2 호출(`propose_*_gap_fill`)도 B26-1의 `rails=`와 함께 간다.
2. **레일과 포트 겹침**: NC 1b는 선언 입력·출력을 레일 분류(1a) 위에 덮어쓴다. B26-1이 `meta["rails"]`를 주므로 `port ∩ rails ≠ ∅` 거부를 이 card에 넣을 수 있다(B2-1). 지금 모의 head는 `vdd` 입력 선언을 받는다.
3. **`test_s013` 둘째 호출**(`_rsl_bad_trs`, topology 없음): card의 "그 topology의 meta 또는 `port_declaration(<그 dict>)`"이 적용되지 않는다. 그 호출은 선언 vsid 경로에서 먼저 `ValueError`가 나므로 `ports` 값은 판정에 영향이 없다. test-author용으로 "임의의 유효 선언(예: 같은 test 첫 호출의 `meta["ports"]`)"을 적는다.
4. **계약 5 호출 모양**: `load_topology`는 `device_roles`가 비면 `None`을 싣는다(`all_device_roles or None`). 계약 문장의 `resolve_stack_layout(t, [], meta["device_roles"], …)`는 그때 `AttributeError`가 난다. `meta["device_roles"] or {}`로 적는다(`tele`에서는 자동 채움이 있어 실측상 문제가 없었다).
5. **병합 순서**: B34 → B26-1 → (Phase 3) → CC-4a → B37a. 텍스트 충돌은 모두 기계적이다(같은 호출에 키워드 추가). 의미 충돌은 위 1·2와, B37a가 E2의 차동 간선 분기(B26-1 측정 때는 운영에서 꺼져 있던 경로)를 **처음으로 켠다**는 점이다. B26-1의 E-LIB '불변' 측정은 그 분기가 꺼진 상태였다. 그래서 B37a 착수 시 재측정(S5)이 필요하다.

## S5. 착수 시 재측정 범위

* card는 착수 시 1(a)(e)·7만 다시 잰다고 적었다. 승인 기록에 붙는 E-LIB 차이표와 E3 차이표(1(c))는 `7535799`에서 잰 값이다.
* B26-1(씨앗 `vss` 추가 등)·B34·CC-4a·Phase 3 이동 뒤에도 같은지는 재지 않았다.
* 고칠 것:
  * 1(b)(c)도 착수 시 같은 명령으로 다시 잰다.
  * 승인 기록에 '표를 잰 base 커밋'을 적는다.
  * 표가 달라지면 card를 멈추고 다시 확인받는다.

## S6. MG2와의 관계

* 계약 1·6의 '`direction`이 있으면 role과 같아야 한다'는 MG2(옛 키 `direction` 거부) 전까지만 의미가 있다. MG2는 `port_declaration`의 그 분기를 거부로 바꿔야 한다. 그러니 "MG2의 ports 몫은 키 삭제와 옛 키 거부만 남는다"는 정확하지 않다(접근자 수정 1건이 남는다. 작은 def라 V3 비용은 작다).
* card는 합성 topology의 `ports`를 전부 `direction` 포함으로 정의했다. 그대로 쓰면 MG2가 B37a 계약 test의 픽스처를 고쳐야 한다.
* 고칠 것: 합성 topology 기본형에서 `direction`을 빼고(role만), `direction` 관련 케이스(계약 1의 '있어도 같다', 계약 6 모순 2종, 계약 7의 '있든 없든')에만 넣는다.

---

## minor

* **M1**: "`3292`의 `if inputs or …`" → 실제는 3293이다(3292는 `if kind == "internal_series"]`). 준비 자료도 같은 오기다.
* **M2**: 계획서 소비자 grep(`docs/01-plan`·`docs/02-design`)이 `skills/analog-gmid-design/references/analog-grammar-integration.md` §5(147~155)를 놓쳤다. 이 문서는 `ports`를 `direction`으로 읽는 설계 예시(`ports = topo["ports"]  # load_topology()가 이미 파싱하는 그 dict`)를 싣고 있다. B37a 뒤 정본은 `meta["ports"]`(`PortDeclaration`)다. 오케스트레이터 문서 커밋 목록에 더한다(B34 검토 M1과 같은 유형).
* **M3**: B3의 V4 규칙 (3) 주의(위).
* **M4**: 계획 GB0(6a, MOD2)는 '사람 선언을 읽고 검증한다'의 항목으로 `ports`를 든다. 레지스트리 새 행('포트 선언(입출력)', 정본 = 접근자)에 "GB0 로드 게이트는 이 접근자를 재사용한다"를 적어 두 번째 정본(DUP)을 예방한다.
* **M5**: 연결 파일 규칙(진입 파일과 다르면 거부)은 맞다. 다만 test-author에게 "기존 연결 파일 픽스처(`test_ic3` `part_b`, s071)에는 `ports`를 넣지 않는다. 넣는다면 진입 파일과 같은 선언"을 적는다. 측정 장치가 연결 파일마다 다른 선언을 넣자 두 test가 `linked ports differ`로 실패했다.

## 산출물·정리

* 스크립트(C:/g63, 삭제함):
  * `make_head.py`: 모의 head
  * `rename.py`·`rename2.py`·`rename_all.py`: 계약 3과 B1 반례·대안
  * `contracts.py`: 계약 2·4~8, 예외 타입
  * `elib.py`: E-LIB·E3 차이표
  * `v3.py`: changed_defs·mutants·감싸는 복합문
  * `make_fx.py`·`run_pt.py`: 픽스처 보강 두 방식의 pytest
* 수치는 이 문서에 옮겨 적었다.
* 저장소 쓰기와 상태 변경 git은 없었다(`git archive`·`git show`·`git grep`·`git log`만 썼다). 끝난 뒤 `git status`는 시작할 때와 같다.
