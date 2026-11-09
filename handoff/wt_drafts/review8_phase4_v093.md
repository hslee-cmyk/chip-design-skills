# 8차 독립 검토 -- Phase 4 `40-defect-fixes` 초안 v0.9.2 → v0.9.3 델타

검토자: 독립 검토 agent(작성자 아님). 저장소는 읽기만 했다(`git show`·`git diff --stat`·`git log -1`·`git ls-tree`, 상태를 바꾸는 git 없음). 스크래치 `C:/g159`(끝나고 삭제).
**루프 종료 규칙**: v0.9.3이 만든 결함과 7차 검토(`review7_phase4_v092.md`)에서 풀리지 않은 항목만 적는다. 그 밖의 것은 '참고'로 둔다.

대상(diff로 확인): `draft_phase4_design.v092.md` → `draft_phase4_design.md`, `phase4_approval_question.v092.md` → `phase4_approval_question.md`, `phase4_revision_log.md` 'v0.9.2 → v0.9.3' 절.
대조 자료(읽기만): `draft_phase3_design_v8.md`(v8.3), `p3_scripts/p3v83_*`, `p3_scripts/e_lib_p3_proposed/e_lib_p3.py`, `p4_card21_rails_measure.md`, `b26_decision_table.md`, `prep_b26_supply_nets.md`, `draft_b37a.spec.md`(card v2), `draft_b26_1.spec.md`(22:20 판), `decision_package.md`, 저장소 `a796468:stick_diagram.py` `load_topology`.

## 판정

**아직 올리지 않는다 -- 고친 뒤 'Phase 3 DoD 뒤 질문 가능'.** 막는 것(blocking) 1건, 고칠 것(should-fix) 2건, minor 4건이다.
7차 검토의 S1·S2·m1~m4·R1·R2는 모두 반영됐다. 정확 일치 식은 Phase 3 v8.3 E5 (iv)와 같다.
B1은 v0.9.3이 새로 고정한 빼는 키 목록 `MASK_META_P4`가 #47(B37a) card v2의 기대 차이표보다 좁다는 문제다. 그 목록을 그대로 쓰면 Phase 4 DoD E11은 반드시 FAIL이 난다. 그런데 승인 질문 (c)는 사용자에게 "셋뿐입니다"라고 묻는다.

---

## 1. 점검 결과

| # | 점검 | 결과 |
|---|---|---|
| 1 | 정확 일치 `rails` 판정 대 Phase 3 v8.3, `P3D` 쪽 INVALID 규칙 | **식은 일치하고 `P3D` 규칙도 타당하다.** 다만 통과 기준에 INVALID 줄이 없다(**S1**). 아래 1.1 |
| 2 | `POLARITY_P4` 출처의 독립성, 상수 표 vs 유도 | 엔진 출력은 아니다(데이터 스캔). 내 독립 재측정으로 9/9 일치한다. 하지만 **재현할 수 없는 1회 측정이고, card 작성 전 조건 한 번으로는 DoD까지 지켜지지 않는다**(**S2**). 아래 1.2 |
| 3 | `MASK_META_P4` 완전성 | **불완전하다(B1)**. #47 card v2 기대 차이표의 `_device_roles_autofilled`·`_device_roles_gap_fill_review_needed`가 빠졌고, `ports` 행의 기대값이 정의되지 않는다. 아래 2 |
| 4 | #21 해시 같음 문장 대 `p4_card21_rails_measure.md` §5 | **일치한다**(§5 제안 문장 그대로). 끝 문장('#17 선병합이어도 성립')만 보고서 §7에서 '측정하지 않음'으로 적힌 추론이다(**m2**) |
| 5 | 낡은 범위·수 | Phase 4 세 파일 안에서는 낡은 것이 없다(P-1~P-37, §9-1~§9-26, 계약 49 + 조건부 5, 1차 4 + 2차 1 모두 본문과 맞다). `decision_package.md`에서 11곳이 낡았다. 아래 4 |

### 1.1 점검 1 상세

* Phase 3 v8.3 E5 판정 python(1031행): `hv == {"__dc__": "RailDeclaration", "nets": want}`이다. `want = {"__set__": sorted(P2D library supply_nets, key=json.dumps)}`이고, P2D 쪽은 `<ABSENT>` 또는 `== hv`다.
* Phase 4 E11 표 `rails` 행: HEAD는 `{"__dc__", "nets": NETS(c), "polarity": POLARITY_P4[c]}` 정확 일치(키 셋), `NETS(c)` = `P3D` library를 `git show`로 읽은 값, `P3D` 쪽은 `{"__dc__", "nets": NETS(c)}` 정확 일치이고 아니면 `E11 INVALID`다.
  * 모양이 Phase 3 (iv)와 같다. #1 (c)(m1)·#17 (c)도 같은 식이다.
* `P3D` 쪽 INVALID 규칙은 타당하다.
  * B26-1은 `phase: 3` card라 `P3D`에는 이미 병합돼 있다. #17은 F2 뒤 단일 경로(P-35)라 `P3D`에 `polarity`가 있을 수 없다.
  * 그러므로 `P3D`에서 B26-1 계약 1 모양이 아니면 '비교 시작 판이 전제와 다르다'가 맞는 진단이다. Phase 3 쪽의 `<ABSENT>` 허용은 P2D가 B26-1 앞이라서이고, 여기서는 필요 없다.
* 빈 곳: E11 통과 기준 칸(design 628행 새 문장)은 "목록 밖 차이 0 + 빼낸 키 계약 판정 FAIL 0((iii)·(iv))"뿐이다. **`E11 INVALID` 줄 없음**이 없다. 그런데 판정 (i)(동등 확인)과 (iii)(`P3D` 열)은 FAIL이 아니라 INVALID를 낸다. 글자대로 읽으면 INVALID가 나도 'FAIL 0'으로 통과한다(→ **S1**). Phase 3 E5 행은 "`E5 INVALID` 줄이 없고 `E5 E-LIB/E-INST PASS`"라고 적는다. 같은 부류의 지적이 Phase 3 6차 검토 N2(E2 INVALID)에도 있었다.

### 1.2 점검 2 상세 -- `POLARITY_P4`의 출처

* **어떻게 만들어졌나**: `b26_decision_table.md` 머리는 "기준 master `cd64170` … 실측은 `C:/g26`에 저장소 사본을 떠서 했고 끝난 뒤 지웠다"이다. 선행 `prep_b26_supply_nets.md` §2.3은 "회로별로 선언 레일이 어떤 단자로 나오는지 셌다"이다.
  * 즉 topology JSON 단자를 센 데이터 스캔이다. 그때 엔진에는 극성 코드가 없었으니 #17 구현 출력이 아니다(엔진 독립 -- 맞다).
  * 그러나 세는 스크립트가 남아 있지 않다(`_drafts/b26_scripts/`에 해당 스크립트 없음, `C:/g26` 삭제). 지금 출처는 **다시 실행할 수 없는 준비 단계 1회 측정**이다. 판정 기록도 아니다.
* **내 독립 재측정**(검토자, 엔진 import 없음): 스크래치 `C:/g159/pol.py`가 `git show HEAD:…/library/<c>.topology.json`을 읽고 §10.3 규칙(PMOS source만 = hi, NMOS source만 = lo, 둘 다 아님 = mid, 둘 다 = CONFLICT)을 적용했다.
  * 결과: 9/9가 `POLARITY_P4`와 같다. pushpull 두 회로만 `agnd = mid`이고 CONFLICT는 0이다.
  * `linked_topology_files`는 6회로에 키가 있지만 모두 빈 목록이다.
  * `git diff --stat cd64170 HEAD -- …/library/`는 `.topology.md` 2개만 바뀌었다. JSON은 `cd64170` 뒤로 그대로다.
  * 그러니 표 값은 지금 맞다.
* **상수 표가 '상수를 지어내지 마라'(메모리) 위반인가**: 값을 지어낸 것은 아니다(규칙 + 선언에서 유도했고 출처가 적혀 있다). 하지만 원칙의 두 번째 절, 즉 '유도한 결과 숫자를 박는 것은 해결이 아니다(근거가 바뀌어도 따라가지 않는다)'에는 걸린다. 근거(library 데이터)가 Phase 4 안에서 바뀔 수 있는 길이 셋 있다.
  * (a) #53이 UD-17a 답에 따라 folded M1·M2의 `kind`나 단자를 바꾼다. 지금 M1·M2 source는 `tail`이라 결과가 바뀌지 않을 가능성이 높지만 증명은 아니다.
  * (b) #55가 `bulk`를 더한다. source 규칙이라 영향은 없다.
  * (c) #44 (C)가 topology 선언을 정정한다(U-09/UD-6).
  * (d) 그리고 UD-1이 (C)가 아니면, 또는 예외 회로가 `supply_roles`를 선언하면 출처 자체가 선언으로 바뀐다.
* **작성자≠검증자 쪽 요구**: 이쪽은 기대값을 미리 고정하라고 한다. 두 원칙을 함께 만족시키는 방법은 **결과 숫자가 아니라 유도 절차(판정 쪽 함수)를 고정**하는 것이다.
* 그래서 '#17 card 작성 전 조건' 한 번만으로는 **충분하지 않다**(→ **S2**). 조건 (1)은 #17 작성 시점에 한 번 잴 뿐이다. #17 뒤에 병합되는 topology 변경 card와 DoD E11에는 닿지 않는다. 누가 재는지(역할)와 산출물 위치·sha도 적혀 있지 않다.

---

## 2. Blocking

### B1. `MASK_META_P4 = ("device_roles", "ports", "rails")`가 #47 card v2의 E-LIB 기대 차이표보다 좁다. 이대로면 E11이 반드시 FAIL이고, `ports` 행은 기대값이 정의되지 않는다 (v0.9.3 결함)

* 근거 1 -- 빠진 meta 키 둘. `draft_b37a.spec.md` 계약 9(143·150~156행)의 기대 차이표(E-LIB)는 이렇다.

  | 회로 | 바뀌는 키 |
  |---|---|
  | ngcc_3stage_ff | `device_roles`, **`_device_roles_autofilled`** |
  | sf_pushpull_output_opamp | `device_roles`, **`_device_roles_autofilled`** |
  | two_stage_ota_sf | `device_roles`, **`_device_roles_autofilled`** |
  | nmcnr_amplifier | **`_device_roles_gap_fill_review_needed`**(12 → 10) |
  | two_stage_ota | **`_device_roles_gap_fill_review_needed`**(9 → 7) |

  * 이 두 키는 `device_roles` 안이 아니라 별도 최상위 meta 키다(`a796468` `stick_diagram.py` `load_topology`의 `meta = {…}` -- `"device_roles"`, `"_device_roles_autofilled"`, `"_device_roles_gap_fill_review_needed"`가 따로 있다).
  * `e_lib_p3.py`는 인자로 받은 키만 빼고 나머지 meta는 `hash`·`per_hash`에 넣는다. 그러므로 #47 병합 뒤 HEAD에서는 5회로의 `per_hash.load`와 전체 `hash`가 `P3D`와 다르다. E11 (ii)는 반드시 FAIL이다.
  * 그리고 v0.9.3 표는 "목록을 바꾸려면 design 개정 -- auditor·DoD 브리핑은 늘리지 않는다"이다. 그래서 DoD 때 고칠 길이 개정 승인뿐이다.
* 근거 2 -- `ports` 행이 성립하지 않는다.
  * `ports`는 #47이 **새로** 만드는 meta 키다(B37a card 35·46행 "결과를 `meta["ports"]`에 싣는다", 143행 "`meta`는 새 키 `"ports"`를 빼고"). `a796468` `load_topology` meta에는 `ports`가 없다. Phase 3 card도 이 키를 더하지 않는다. 그러니 `P3D` `masked.ports` = `"<ABSENT>"`다.
  * 표의 기대값 "`P3D` 값에 #47 card v2 기대 차이표를 적용한 값"은 `<ABSENT>`에 표를 적용한다는 말이 된다. 게다가 그 차이표는 `ports`를 제외한 표다. 그 결과 HEAD의 실제 값과 같을 수 없다(FAIL). `P3D` 열 "기준값(그대로 읽음)"도 `<ABSENT>`라는 사실을 적지 않았다.
  * 또 card 계약 2의 기대식 `meta["ports"] == M.port_declaration(<JSON>)`은 피검 함수 호출이다. 이것을 기대값 출처로 옮기면 #17 `polarity`에서 막은 작성자=검증자 순환이 생긴다. 독립 출처는 card 계약 9 (d)('role 표로 만든 기대값', 예: current_reuse `inputs=("Vim","Vip")`)다.
* 근거 3 -- 사용자 문구. 승인 질문 (c)는 "비교에서 빼는 항목은 … 셋뿐입니다", "포트·소자 역할은 B37a 승인 때 확인하실 기대 차이표"라고 적는다. 둘 다 위 사실과 맞지 않는다. 승인받은 기준이 확정적으로 틀리면, Phase 4 DoD 때 기준을 바꾸는 승인을 다시 받아야 한다.
* **고칠 것**(둘 중 하나. (가) 권고 -- 더 좁고, #47 card의 판정 방식과 같다):
  * **(가) 빼는 키 대신 '(회로, meta 키) 차이 집합 = 승인된 차이표들의 합집합' 판정**: `e_lib_p3.py`를 MASK 없이 두 판에서 돌리고, 회로마다 meta를 키 단위로 비교한다.
    * 다른 (회로, 키) 쌍의 집합은 (#17 `rails` 9회로) ∪ (#47 card v2 차이표, 착수 시 재측정판 -- 승인 기록에 붙은 표) ∪ (#47 `ports` 9회로) ∪ (topology 변경 card의 DEC-40 차이표)와 **정확히 같아야** 한다.
    * 표 안의 값은 각 출처와 정확히 같아야 한다.
    * 이 비교는 `masked` 슬롯이 아니라 MASK 없는 `load` 값에서 판정 python이 키를 꺼내 하면 된다. `e_lib_p3.py` 변경은 필요 없다.
  * **(나) 목록 확장**: `MASK_META_P4 = ("_device_roles_autofilled", "_device_roles_gap_fill_review_needed", "device_roles", "ports", "rails")`. 표에 두 행을 더하고(기대 = `P3D` 값 + #47 승인 차이표, 차이표 밖 회로는 `P3D` 값과 같음), 승인 질문 (c)를 "다섯 항목(레일 선언, 포트, 소자 역할과 그 자동 채움·검토 목록 두 기록)"으로 고친다.
  * 공통:
    * (1) `ports` 행: `P3D` = `"<ABSENT>"`, HEAD = #47 card 계약 9 (d) role 표에서 `P3D` library `ports` 선언으로 만든 값(정규화 모양, 예: 접근자 반환이 dataclass면 `{"__dc__": …}`)을 `==`로 판정한다. 그 직렬화 모양을 #47 interface card에 고정한다는 #47 card 작성 전 조건을 더한다(#17 조건 (3)과 같은 모양).
    * (2) #47 card 착수 시 재측정한 차이표의 키 집합이 이 목록 안에 있지 않으면 design 개정이라고 적는다(card 148행 '표가 다르면 card를 멈추고 다시 확인' -- B26-1 뒤 E2 차동 간선 분기가 처음 켜지므로 `_vertical_stack_id_autofilled`가 더해질 수 있다 [미확인]).

---

## 3. Should-fix

### S1. E11 통과 기준에 `E11 INVALID` 줄 없음이 없다 (v0.9.3 결함)

* v0.9.3이 판정 (i)(`e_lib_p3.py` 무인자 ≠ `e_lib.py` on `P3D`)과 (iii)(`P3D` `masked.rails` 모양 불일치)을 INVALID로 정했다. 그런데 통과 기준 칸은 "빼낸 키 계약 판정 FAIL 0((iii)·(iv))"이다. (iii)은 FAIL이 아니라 INVALID를 내므로, 기준을 글자대로 쓰면 INVALID가 통과한다.
* **고칠 것**: 통과 기준에 "§10 판정 블록 출력에 `E11 INVALID` 줄이 없고 `E11 E-LIB PASS`"를 더한다(Phase 3 E5 행과 같은 문형). (i)이 쓰는 `e_lib.py` 사본의 경로(`P3D:.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py` -- Phase 3 블록과 같음)도 표 아래 한 줄로 적는다.

### S2. `POLARITY_P4` -- 결과 표를 박지 말고 판정 쪽 유도 함수를 고정한다. 표는 그 함수의 자기 점검 기대값으로 둔다 (v0.9.3 결함, 점검 2의 제안)

* 문제:
  * (1) 출처 `cd64170` 표를 다시 실행할 수 없다(1.2).
  * (2) '#17 card 작성 전 조건'은 한 번뿐이라 #17 뒤 topology 변경(#53 UD-17a 갈래, #44 (C), UD-1 (C) 예외 회로의 `supply_roles` 추가)을 따라가지 못한다.
  * (3) 표의 `NETS(c)` 예외 목록은 '#53·#54·#55'뿐이고 #44 (C)(topology 선언 정정)가 없다. `POLARITY_P4` 열에는 예외 문장 자체가 없다.
  * (4) 조건 (1)의 수행 역할·산출물 위치·sha가 없다.
* **고칠 것**:
  * (a) design 커밋에 판정 쪽 유도 스크립트를 넣는다(예: `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/scripts/rail_polarity_p4.py` -- topology JSON의 `supply_nets`·`kind`·`source`와 `supply_roles`만 읽고 엔진 import 0, Phase 3 D-28이 `e_lib_p3.py`를 design 커밋에 넣은 것과 같은 지위, sha256을 판정 기록에).
  * (b) `POLARITY_P4` 표는 '`P3D`에서 이 스크립트가 재현해야 하는 값'(자기 점검)으로 둔다. 다르면 `E11 INVALID` + design 개정이다.
  * (c) E11·#17 (c)의 기대값 = **비교 시작 판 library에서 그 스크립트가 낸 값**으로 한다. 단 topology를 바꾼 card(#53·#54·#55·#44 (C))가 있는 회로는 그 card의 승인된 topology 판에서 같은 스크립트가 낸 값으로 하고, 그 card DEC-40 차이표에 극성 행을 둔다.
  * (d) UD-1이 (C)가 아니거나 `supply_roles`를 선언한 회로는 선언값(스크립트가 선언을 우선)으로 한다.
  * (e) 조건 (1)의 수행자를 auditor 또는 test-author로 적는다(작성자 = 오케스트레이터가 쓴 표를 같은 쪽이 확인하지 않게).
  * (f) 결과를 `.ai/verification/`이 아니라 위 원자료 자리에 둔다.
* 이렇게 하면 '근거 하나(규칙 + 선언)만 두고 계산'이 되고, 기대값이 엔진과 독립인 것도 유지된다. 내 재측정(9/9 일치, `cd64170` 뒤 JSON 무변경)이 스크립트 초안의 근거가 된다.

---

## 4. Minor

| # | 내용 |
|---|---|
| m1 | E11 판정 (ii) "결과 `hash`가 `P3D`와 HEAD에서 같고 … (topology를 바꾼 회로는 위 E11 행대로 …)"에서 전체 `hash`는 회로 하나만 달라도 다르다. 예외 회로가 있으면 이 판정은 성립할 수 없다. `e_lib_p3.py`는 회로별 `per_hash`를 낸다. "예외 회로 밖 회로마다 `per_hash` 같음, 예외 회로는 그 card 차이표"로 적는다. Phase 3 판정 python(`m0["hash"] == m1["hash"]`)을 '따라 쓰면' 이 차이를 놓친다 |
| m2 | #21 (c) 끝 문장 "card base에 #17이 먼저 병합돼 있으면 … 같은 비교가 성립한다"는 보고서 §7 한계("이 측정은 `polarity` 없는 base에서 했다")의 추론이다. 측정이 아니다. '[추론 -- 미측정]'을 붙이거나 'card 작성 때 #17 선병합이면 재측정'으로 적는다 |
| m3 | #17 조건 (3) 직렬화 모양: `dict` → `__dict__`, 비 `dict` Mapping → `__repr__`만 적었다. 값이 `Enum`이면 `{"__enum__": repr}`가 되어 표의 `"hi"`와 같지 않다. `MappingProxyType`의 `__repr__`은 삽입 순서에 묶인다. interface card에 '`polarity`는 `dict[str, str]`(값 `"hi"`/`"lo"`/`"mid"`)' 같은 구체 형을 고정한다고 적는다. §10.3 `supply_roles` 어휘(`rail_high`/`rail_low`/`rail_mid`) → `hi`/`lo`/`mid` 대응도 조건 (2)에 한 줄 |
| m4 | B35(UD-15 (2): #49 또는 #17)가 사이트 8 `_propose_headroom_roles`·14 `propose_device_roles_gap_fill`의 이름 기반 레일 판정을 선언 레일로 바꾸면, `agnd`(mid) 회로에서 `device_roles`·`_device_roles_autofilled`가 바뀔 수 있다(UD-15 (3) 'mid 레일 grammar 매핑'). 이 경우는 표에 없다 [미확인 -- prep 실측은 `trace_*` 교체만 쟀다]. B1 (가)·(나) 어느 쪽이든 'B35 card 작성 때 E-LIB meta 실측, 바뀌면 design 개정'을 #17/#49 행에 한 구절 |

---

## 5. 낡은 범위·수 (점검 5)

**Phase 4 세 파일**: 낡은 것이 없다.
* `P-1~P-37`(승인 질문 24·88행) = design §7.2 마지막 행 P-37이다.
* `§9-1~§9-26` = §9 최대 항목 26이다.
* '계약 49건 + 조건부 5'는 design 603·605행과 승인 질문 21행이 같다.
* '1차 4 + 2차 1'은 승인 질문 9행과 revision log '바뀌지 않은 것'이 같다.
* revision log가 v0.5 기록에 B48~B50을 남긴 것은 이력이라 맞다(7차 1.2와 같음).

**`decision_package.md`(21:48 판)** -- 올리기 전 고칠 곳:

| 행 | 낡은 내용 | 지금 사실 |
|---|---|---|
| 3 | "결정 완료 **11건** · 지금 필요 2묶음(**B26-1 U3~U5**, Phase 3 4건)" | U3·U4·U5, U-BF, Q-B34-PHASE, Q-P2DOD-E2, B47 md 일치가 결정됐다(승인 초안 `approval_20261001-*`·`approval_20260930-b26-b40-reason-key.md`, gate 커밋 `19eb475`·`dc196cd`·`378ebe6`). '지금 필요'에서 B26-1 묶음이 빠지고 결정 완료 수가 늘어야 한다 |
| 9~22(§1) | 결정 완료 표에 위 7건이 없다 | 같은 기록을 더한다 |
| 27~34(§2-1) | U3를 '대기'로, 권고 "(1) 앞선 test-only card"로, "질문 문안 아직 없음"으로 적었다 | U3 답 = "정리 2줄 + 면제 1"(기록 `20261001-b26-v3-equiv-range`, 1차 시도 K1 뒤·2차 시도 착수 전), U4·U5 기록 있음. 절 전체가 낡았다 |
| 39(§2-2 UD-0) | Phase 3 UD-0 기준값이 D-9·D-17뿐이다 | Phase 3 v8.2·v8.3 UD-0 (c) E5 비교 판(P2D 기본안, 대안 c-2)이 빠졌다(Phase 3 쪽, 참고) |
| 52 | "Phase 4 착수 때 결정 (`draft_phase4_design.v05.md` §7)" | 정본은 v0.9.3 §7 |
| 68 | "UD-0(P4) … **P-1~P-32** + 계획 정정 §9", 출처 "v05 §7.2·§9" | P-1~P-37, §9-1~§9-26, 기준에 닿는 것 (a)(b)(c) -- 특히 (c) E11 빼는 항목(B1 고친 뒤의 목록) |
| 69 | UD-18 Q1 "3회로 자동 채움 소실·그룹 변화" | B37a card v2 기대 차이표는 E-LIB 5회로(자동 채움 3 + 검토 목록 2)·E3 3회로다(design #47 행도 'E-LIB 5회로·E3 3회로') |
| 80~81 | DEC-40·topology 수정 승인 대상 "#53·#54" | #55(UD-17e (ii) 조건부, v0.6)와 #44 (C)(같은 표 77행이 nmcnr "(C) topology 정정부터"라 적음)가 빠졌다 |
| 87(§3-3 B47) | "재생성 커밋 승인 + 다른 md 일치 확인"을 대기로 | 승인 `20261001-b47-md-sync`(gate `378ebe6`), md 일치 card `80b9970` |
| 109 | "Phase 4 **P-1~P-32** … 새로 P-26~P-32", 출처 "v05 §7.2" | P-33~P-37(특히 P-36 vsb 비트 동일, P-37 E-LIB 비교)이 빠졌다 |
| 117 | "`draft_phase4_design.md`와 `.v05.md`는 내용이 같다(cmp 동일) -- 둘 다 v0.5" | 지금 v0.9.3(1354줄) 대 v05(1117줄) -- 사실과 반대 |

(3행의 "Phase 4 착수 때 약 15건"은 질문 수가 아니라 항목 수다. §3 표의 행 수(약 19)와 승인 질문 문항 수(1차 4 + 2차 1) 어느 쪽과도 맞지 않는다. 기준을 적거나 고친다.)

---

## 6. 7차 검토 항목 반영 확인

| 항목 | 상태 |
|---|---|
| S1 정확 일치·출처 | 반영. 식은 Phase 3 v8.3 (iv)와 같다. 출처 표는 B1·S2로 남는다 |
| S2 목록을 design 상수로, 승인 질문 (c) | 반영(지위·문장). 목록 내용이 틀렸다 → B1 |
| m1 #1 (c) | 반영. Phase 3 (iv)와 같은 식, base `<ABSENT>` |
| m2 'Phase 2 완료 판정(승인된 선례)' | 반영(승인 질문 24·88행, P-37 근거) |
| m3 #30 커밋 주체·글자 | 반영(`Role: doc`, 같은 gate push, `path::rule` 확인 [미확인]) |
| m4 `P3D` 한 번 정의 | 반영(E2 행) |
| R1 U3 기록 시점 | 반영. B26-1 card 419·436·437·468~472행과 같다 |
| R2 Phase 3 v8.3 가리킴 | 반영 |

## 7. 재현

* `diff` 두 쌍, revision log 426~462행을 확인했다.
* `draft_phase3_design_v8.md` 4·709(D-28 (e))·960~1046(E5 블록)·1052(E5 행)행과 `e_lib_p3.py` 전문을 읽었다.
* `p4_card21_rails_measure.md` 전문, `draft_b37a.spec.md` 35·46·92·101·140~166행, `b26_decision_table.md` 1~35행, `prep_b26_supply_nets.md` 108~130행, `decision_package.md` 전문을 읽었다.
* `git -C <repo> show a796468:skills/analog-gmid-design/assets/stick_diagram.py`(스크래치 사본)의 `load_topology` 8539~8730행: meta 키 집합, `ports` 없음.
* 극성 재측정: `C:/Python314/python.exe -B C:/g159/pol.py HEAD` → 9회로 극성이 `POLARITY_P4`와 같다, CONFLICT 0, 연결 파일 목록 모두 빈 목록. `git diff --stat cd64170 HEAD -- skills/analog-gmid-design/assets/library/` → `.topology.md` 2개뿐이다.
* `git -C <repo> status --short`는 검토 전후 같다(36줄). 스크래치 `C:/g159`는 삭제했다.
