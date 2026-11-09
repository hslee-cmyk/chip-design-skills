# 9차 독립 검토 -- Phase 4 `40-defect-fixes` 초안 v0.9.3 → v0.9.4 델타

검토자: 독립 검토 agent(작성자 아님). 저장소는 읽기만 했다(`git -C` 읽기 명령, `git clone --no-checkout` 사본만 사용). 스크래치 `C:/g168`(끝나고 삭제).
**루프 종료 규칙**: v0.9.4가 만든 결함과 8차 검토(`review8_phase4_v093.md`)에서 풀리지 않은 항목만 적는다.

대상(diff로 확인): `draft_phase4_design.v093.md` → `draft_phase4_design.md`, `phase4_approval_question.v093.md` → `.md`, `decision_package.v3.md`(백업, v2 내용) → `decision_package.md`(v3), 새 파일 `p4_scripts/derive_polarity_p4.py`(sha256 `79dc9d88…455aa`, 문안 기록과 같음), `phase4_revision_log.md` v0.9.4 절.
gate `master` = `dd60db6`(검토 시점. v0.9.4 측정 판 `5f643a9` 뒤 `2eefda1`·`cf26d39`·`84e91a4`·`7718505`·`dd60db6` -- 모두 문서·승인 커밋).

## 판정

**막는 것(blocking) 없음 → 'Phase 3 DoD 뒤 질문 가능'.** 고칠 것(should-fix) 2건, minor 3건이다.
* 8차 검토의 B1·S1·S2·m1~m4는 모두 반영됐다. `decision_package.md` 11곳도 고쳐졌다.
* S1·S2는 design 본문(§6 'E11 차이 집합 표')만 고치면 된다. 승인 질문 (c)의 문장은 바뀌지 않는다. 고친 뒤 다시 검토할 필요는 없다(문구 확인만).

---

## 1. 점검 결과(재측정)

| # | 점검 | 결과 |
|---|---|---|
| 1 | E11 집합 같음 판정(성분 R·P·D47·TC·B35) | **규칙은 결정 가능하고 모든 부류를 잡는다**(아래 1.1 합성 18사례). 빈 곳 둘: 같은 쌍을 두 성분이 바꿀 때 무엇이 먼저인지 규칙이 없다(**S1**). D47 기대값의 모양이 정해지지 않았다(**S2**) |
| 2 | `derive_polarity_p4.py` | `dd60db6`·`a796468`·`cd64170`에서 셋 다 `SELF-CHECK PASS 9/9`, rc 0. import는 `argparse·hashlib·json·posixpath·subprocess·sys`뿐이다(엔진·#17 코드 0). 박힌 결과 상수는 `SELF_CHECK_EXPECTED`(자기 점검)뿐이고, `ROLE_MAP`·`LIB`는 §10.3 어휘와 경로다. 유도가 맞다 |
| 3 | `ports` 기대값 출처 | #47 card(`draft_b37a.spec.md`, `phase: 4`)의 계약 1(85~86행)에 6어휘 role 표가 있다. 작성 전 실측 (d)는 328행에 있다. `PortDeclaration` frozen dataclass, `inputs`·`outputs` tuple은 40·180행에 있다. design의 인용이 맞다 |
| 4 | `decision_package.md` v3 | §1 표가 19행이다(참고 B28 포함). '지금 필요 = Phase 3 4문항'도 맞다(UD-0·D-19·UD-5·UD-1). 다만 gate가 진행해 낡은 곳이 생겼다(**m3**) |

### 1.1 점검 1 상세 -- 합성 판정(검토자 독립 구현)

* design §6 판정 (ii)~(v)와 (iii) 전제를 글자대로 구현했다(`C:/g168/t/judge.py`, 엔진 import 0).
  * 입력은 `e_lib_p3.py` 출력 모양을 흉내 낸 합성 dict다(`circuits.<c>.masked.<k>`, `per_hash.load·V1·V2`).
  * 9회로를 두었다. 성분은 R(9 × `rails`), P(9 × `ports`), D47(c0 `device_roles`·`_device_roles_autofilled`), TC(c5 `transistors`)다.
* 결과(18사례 모두 기대대로):
  * **정상**: `E11 E-LIB PASS`.
  * **승인 밖 쌍이 더 바뀜** → `차이 집합 FAIL 남음=…`. 다섯 형태(R 쪽 `symmetry`, D47 밖 `_device_roles_autofilled`, TC 밖 `V1_own_stack`, B35형 `agnd` 회로 `device_roles`, 새 meta 키) 모두 잡혔다.
  * **승인된 쌍이 안 바뀜** → `빠짐=…`. R(#17 미병합 회로), P(`ports` 없음), D47, TC 모두 잡혔다.
  * **승인 쌍 안의 값이 다름** → `<단위> 계약 FAIL`. R 극성 값, R 계약 밖 필드, P 입력 하나 빠짐, TC 해시, D47 같은 키 안의 다른 소자 필드 모두 잡혔다.
  * **INVALID**: `P3D` `rails`에 `polarity`가 있거나 `P3D`에 `ports`가 있으면 전제 위반 줄이 나왔다. HEAD load 실패는 `FAIL load`로 나왔다.
* **판정이 피검 대상을 import하는가**:
  * 단위 값의 측정은 `e_lib_p3.py`(엔진 `load_topology`·`run_topology_pipeline` 실행)와 (0)의 키 측정이 한다. 이것은 측정 도구이고, Phase 3 E5와 같은 지위다.
  * 기대값 쪽은 엔진을 쓰지 않는다. R은 스크립트가, P는 판정 python이 JSON과 role 표로 만든다. TC는 승인 기록에서 온다.
  * 예외는 D47이다. 출처인 card v2 표가 '모의 head'(작성 쪽 시제품) 측정이다. → S2
* 실측 보조:
  * `a796468`·`dd60db6`의 `load_topology` `meta` 리터럴 키는 둘 다 16개다(AST). `ports`·`rails`는 없다. `_device_roles_*` 두 키는 별도 최상위 키다(작성자 측정과 같다).
  * `run_topology_pipeline` 반환은 `transistors·box_shape·audit_row_split·floorplan·coverage`다. meta를 싣지 않으므로 #17 `polarity`·#47 `ports`가 V1·V2를 바꾸지 않는다(구조상).
  * `dd60db6` library `ports`를 판정 쪽(검토자 스크립트)으로 만들었다. 9/9 6어휘 안이고, current_reuse `["Vim","Vip"]/["Vom","Vop"]`, folded `["vin_n","vin_p"]/["out"]`, two_stage_ota 출력 `["OUT"]`다. card 예와 같다.

### 1.2 점검 2 상세 -- `derive_polarity_p4.py`

* 극성 9/9가 `b26_decision_table.md` §1.2 표와 같다. 근거 소자 수(`evidence`)도 표 열과 같다. 예: current_reuse PMOS 16/NMOS 12, folded 3/4, sf_pushpull 5/5, `agnd` 0/0.
* `other_kinds`는 9회로 모두 비었다(netlist는 pmos·nmos뿐이다. 엔진 `Transistor.__post_init__`도 그 밖 kind를 거부한다).
* `linked_topology_files` 처리(진입 파일 기준 상대 경로, 재귀 없음)는 `load_topology`(8592~8597행)와 같다.
* 합성 거부(`C:/g168/syn` -- `dd60db6` library 사본 git 저장소):

  | 변형 | 결과 |
  |---|---|
  | `agnd`에 PMOS source | self-check FAIL rc 1 |
  | `supply_roles` 키 부족 | `POL ERROR` rc 2 |
  | NMOS source = `vdd` | `GATE FAIL` rc 3 |
  | 선언이 구조와 같음 | PASS rc 0 |
  | 깨진 JSON | rc 2 |
  | 새 회로 추가 | rc 1 -- 메시지는 m1 |
  | 없는 커밋 | 잡히지 않은 traceback rc 1 -- m1 |

---

## 2. Blocking

없음.

## 3. Should-fix

### S1. 같은 (회로, 단위) 쌍을 둘 이상의 성분이 바꿀 때 기대값 우선 규칙이 없다. P 기대값은 TC 판을 따라가지 않는다 (v0.9.4 결함)

* 근거:
  * R 행만 "그 회로를 바꾼 TC card가 있으면 그 card 승인 topology 판에서 실행한 값(마지막 병합)"이라는 규칙을 갖는다.
  * P 행은 "`P3D` library `ports` 선언"으로 고정이다. D47 행은 "#47 착수 시 재측정 표"로 고정이다. TC 행은 "meta 키·`transistors`·V1·V2 어느 것이든"이다. B35 행은 "바뀌면 쌍을 넣는다"이다.
* 실제로 겹칠 수 있는 곳:
  * (a) #44 (C)(nmcnr 선언 정정, TC)와 D47 `(nmcnr_amplifier, _device_roles_gap_fill_review_needed)`.
  * (b) B35(`agnd` 두 회로 `device_roles`·`_device_roles_autofilled`)와 D47 `(sf_pushpull_output_opamp, 같은 둘)`.
  * (c) TC가 포트 넷 선언을 고치면 P 기대값(`P3D` 선언)이 HEAD와 달라진다.
* 이때 `D_exp`는 합집합이라 쌍은 하나다. 그러나 (v)의 기대값이 둘이 되거나 낡은 값이 되어, DoD에서 기준 개정 승인을 다시 받아야 한다.
* **고칠 것**(§6 표 아래 한 문단):
  * 쌍 (c, u)의 기대값은 병합 순서상 **마지막으로 그 쌍을 바꾼 승인 출처**의 값이다. 그 출처의 표는 앞선 출처가 반영된 base에서 잰다(#47 계약 9의 '착수 시 실제 base 재측정'과 같은 원칙).
  * P 기대값의 library 판은 R과 같다. 그 회로를 바꾼 TC가 없으면 `P3D`, 있으면 마지막 TC 승인 판이다.

### S2. D47 기대값의 모양이 정해지지 않았다. 승인 기록의 표는 서술형이고, 출처는 작성 쪽 시제품 측정이다 (v0.9.4 결함)

* 근거:
  * design D47 행의 기대값은 "승인 기록(UD-18 Q1)에 붙은 착수 시 재측정 표의 병합 상당 값(소자·필드까지)"이다.
  * 그런데 그 승인 기록 초안(`draft_b37a_approval_question.md` Q1 표)과 card 계약 9 표는 "`headroom_role` 20개 사라짐(M1·M2 `cascode`, M5~M22)", "12 → 10(M201·M301 안내 2건)" 같은 **서술**이다. (v)가 요구하는 'HEAD 값 `==` 기대값'(값 전체)을 기계적으로 만들 수 없다.
  * 서술만 보는 판정은 같은 키 안의 승인 밖 변화(다른 소자 필드)를 놓친다. 합성 사례 'D47/value'는 기대값이 값 전체일 때만 잡혔다.
  * 또 '병합 상당 값'은 card v2에서 모의 head(작성 쪽 시제품)로 쟀다. P 행이 막은 작성자=검증자 순환이 D47에는 남는다.
* **고칠 것**:
  * D47 기대값 = **`P3D` 값(판정 python이 읽음)에 승인된 삭제 목록을 정확히 적용한 값**으로 정한다. 삭제 목록은 `device_roles`의 (소자, 필드, 옛 값), `_device_roles_autofilled` 항목, `_device_roles_gap_fill_review_needed` 항목이다.
  * #47 card 작성 전 조건 (나)에 "착수 시 재측정 표는 이 삭제 목록을 항목 단위로 적는다(sf_pushpull 18개를 소자별로)"를 더한다.
  * 그러면 기대값이 선언(승인 목록)과 `P3D`에서만 나오고 시제품 출력과 독립이 된다.

## 4. Minor

| # | 내용 |
|---|---|
| m1 | `derive_polarity_p4.py` 종료 코드가 겹친다. 없는 커밋(`rev-parse` 실패, `main`의 `DeriveError`)과 `derive_one`이 잡지 않는 예외(예: netlist 항목이 dict 아님 → `AttributeError`)는 traceback rc 1이 된다. docstring·design의 'rc 1 = self-check 불일치'와 겹친다. 0이 아니면 INVALID라 판정은 같다. 그래도 `main`을 감싸 rc 2로 내는 것이 맞다. 회로가 더 있을 때 메시지가 `SELF-CHECK FAIL 9/9 ['zz_new']`로 나온다(`matched`가 기대 회로만 센다) -- '9/9'가 틀린 인상을 준다 |
| m2 | P-37 행 본문의 지우지 않은 문장 "card가 계약으로 바꾸는 meta 키만 빼서 … 나머지는 해시 같음"과, 승인 질문 88행 "meta 키(`rails`…, `ports`·`device_roles`)만 따로"가 v0.9.4 판정(빼는 목록 없음, 전체 해시 안 씀)과 맞지 않는다. 뒤에 붙인 (v0.9.4) 글이 고치기는 한다. 사용자가 읽는 88행만은 '(v0.9.3까지)'로 표시하거나 취소선을 긋는다 |
| m3 | `decision_package.md`가 gate 진행으로 낡았다(머리 '`5f643a9` 기준'). (1) A1-a `20260930-v3-exempt-binding`이 `dd60db6`에 커밋됐다(`.ai/approvals/` 실측). 표는 '**gate 미커밋**'이다. (2) §2-1 제목 'phase 3 card 병합은 Phase 2 DoD 뒤' -- Phase 2 DoD는 `2eefda1`에서 PASS로 기록됐다. (3) B47 md 일치 결정은 `user_decisions.md`에 없다(정본이라 적힌 파일). gate 기록 `20261001-b47-md-sync`만 있다. B28처럼 '(user_decisions.md에 없음 -- gate 기록)'을 적거나 `user_decisions.md`에 더한다. 나머지 미커밋 표시(A1-b·B33·U3·U4·U5·Q-B34-PHASE)는 `dd60db6`에서도 맞다 |

## 5. 8차 검토 항목 반영 확인

| 항목 | 상태 |
|---|---|
| B1 | 반영((가)). 합성 18사례로 집합 같음·값 같음·INVALID가 모두 작동한다. 남은 빈 곳은 S1·S2(새 표의 세부) |
| S1 | 반영(E11 행 통과 기준 = `E11 INVALID` 없음 + `E11 E-LIB PASS`. `e_lib.py` 사본 경로 -- `dd60db6`에도 `.ai/verification/20260930-df36-instance-relpath/scripts/e_lib.py` 있음) |
| S2 | 반영(판정 쪽 스크립트, 자기 점검 표, auditor 실행 3시점, 산출물 폴더, #44 (C) 포함) |
| m1·m2·m3·m4 | 반영 |
| §5 낡은 곳 11 | 반영(그 뒤 gate 진행분은 m3) |

## 6. 재현

* `diff` 세 쌍과 revision log 465~510행을 읽었다.
* `git clone --no-checkout` → `C:/g168/repo`. `derive_polarity_p4.py --self-check`를 `dd60db6`·`a796468`·`cd64170`에서 실행했다(각 rc 0, 9/9).
* `C:/g168/syn` 합성 7변형(위 1.2 표).
* `C:/g168/t/judge.py` 합성 18사례, `ports_exp.py`(`dd60db6` library), `ast_meta.py`(`load_topology` meta 리터럴, `a796468`·`dd60db6`).
* `git -C <repo> ls-tree dd60db6 .ai/approvals/`, `git log 5f643a9..dd60db6`.
* 저장소 `git status --short`는 검토 전후 같다. `C:/g168`은 삭제했다.
