# review2 -- draft_b26_1.spec.md (20260930-b26-rail-accessor-set) 2차 독립 검토

검토자: 독립 reviewer(작성자 아님, 1차 검토자 아님). 저장소는 읽기만 했다(HEAD = gate `master` `7535799`).
scratch는 `C:/g70`만 썼고 측정 뒤 지웠다. 저장소 쓰기와 상태 변경 git은 없었다(`git show`·`git archive`만).

**모의 사본 구성**
- `b1`(모의 base) = `7535799` archive + P9 **실제** 병합본(`b7765b0`)의 `stick_diagram.py`와 `tests/contracts/test_dup_kcl_edges.py` + B34 코드 변경(`v3_scripts/v3_scope_classify.py`의 `build_b34`: 사이트 1·2·3·11·11b).
- 모의 head = `b1` + B26-1 상당 패치(`v3_scripts/sim_head.py`의 `build_b26`). 사이트 줄은 b1에서 내용으로 다시 찾았다. 13줄: SD 1014·1571·1613·2092·2168·3133·3238·3973·4152·4288·4304·4351·4373. 여기에 인계 삭제 9·10·10b·13·14·B40을 내용 기준 치환으로 더했다. 치환 뒤 흔적 grep은 0이다.

V3 대상 분류는 `v3_scope_classify.classify`(N2b)를 그대로 썼고, 넓힌 T6을 더했다. 넓힌 T6은 사용자 결정 A1-b 정정 "같은 블록 뒤쪽에서 바뀐 이름을 읽는 문장 전부"를 구현한 것이다.
- **own**: 복합문은 자기 필드에서 읽을 때만 센다.
- **deep**: 복합문은 하위 블록에서 읽어도 그 복합문 몫과 하위의 읽는 단순문을 센다.

변이를 죽일 수 있는지는 다음처럼 쟀다.
- head의 대상 변이 중 **기존 문장**에 걸린 300개를 b1의 같은 문장 변이로 옮겼다. 같은 문장은 (연산자, 정규화한 문장 글, 순번)으로 찾았다. 정규화 규칙: `rails.nets`↔`_RAIL_NETS`, `rails=rails` 제거, 씨앗 dict, SR `set(rails.nets)`↔`set(_DEFAULT_RAIL_HI) | set(_DEFAULT_RAIL_LO)`.
- 옮긴 변이를 b1에서 **기존 test 인벤토리**로 실행했다. 실행 조건: 도구와 같은 pytest 인자에 `-x`, `--gmid-phase=2 --gmid-strict=`, `PYTHONHASHSEED=1`, 8개 병렬.
- b1에서는 레일 이름 집합이 library·픽스처의 선언과 같고, 인계 분기는 항상 참이다. 그래서 같은 변이는 의미가 같다(근사).
- 기준 실행: 인벤토리 합집합 208 passed·3 xfailed였다. ts6 이력 test 2개는 뺐다.
- 새 문장 변이 36개(새 def `rail_declaration`, 선언 획득 문장, 연결 파일 검사)는 대응 문장이 없다. 이것들은 계획된 계약으로 죽는지를 따로 판단했다.

## 요약 판정

| 등급 | # | 제목 |
|---|---|---|
| **blocking** | B1 | **'V3 계획' 절이 낡았다.** U1을 '대기'로 적고 옛 선택지 (a)(b)(c)와 `v3_scope_systemic.md` 권고를 그대로 두었다. 사용자는 N2(b)+넓힌 T6과 면제 묶기(A1-a)를 정했다. 이 정책으로 다시 재면 대상이 **265(N2b) / 314~336(넓힌 T6)**이다. card 수치(2,438/135)와 범위 정책 card 수치(228)는 둘 다 이 card의 실제 head 값이 아니다 |
| **blocking** | B2 | **N2 대상 중 기존 test가 못 죽이는 변이가 72개다**(기존 문장 300개 실행: N2b 229개 중 53, 넓힌 T6 몫 71개 중 19). 계획된 계약이 더 죽이는 것은 1~3개뿐이다. 추가 계약 없이는 V3 FAIL이다. 특히 **인계 삭제 사이트 10**이 생존 13개를 들여온다. card 'V3 계획' 6의 "인계 몫은 승인 증가 없음, classify 6변이"는 N2에서 거짓이다 |
| **blocking** | B3 | **P9 병합본의 영구 계약 test 2개가 B26-1에서 FAIL한다.** `test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`는 매개변수 목록이 정확히 `[netlist, matching_pairs]`·`[transistors, matching_pairs]`인지 단언한다. 계약 12는 P9 test에 "`rails=`를 더하는 것"만 적었다. 기대값(시그니처) 변경은 test-author가 혼자 할 수 없다(작성자≠검증자, V5). 승인 경로가 card에 없다 |
| should-fix | S1 | 계약 13의 증거 종류가 틀렸다. "B34 병합 뒤 base에서도 성립(green)"이라고 했지만, `rails=`를 넘기는 test는 base에서 `TypeError`다. green-green이 아니라 'base TypeError, red 집계 밖'이다(계약 14와 같은 처리) |
| should-fix | S2 | 계약 7(c)의 red 형태는 meta를 어떻게 얻느냐에 달렸다. 계약 12는 "`RailDeclaration`은 `rail_declaration`으로 얻는다"고 한다. 그렇게 meta를 만들면 base red가 단언형이 아니라 `AttributeError`(신규 심볼)가 된다. 표의 '단언 red'가 성립하려면 meta를 합성 topology 파일의 `load_topology`로 얻어야 한다 |
| should-fix | S3 | 계약 12에 **넷리스트만 쓰는 직접 호출**(selftest 49곳, P9 test 2 호출부 × 11 케이스)의 `rails` 값 규칙이 없다. 지금 규칙은 'topology의 `supply_nets`'와 '로드 경로 픽스처'뿐이다. test-author가 소스 없이 정할 수 있게 "base가 레일로 읽던 이름 중 그 넷리스트 단자에 나오는 것(SD = 소문자 `vdd`·`gnd`·`vss`)"을 적을 것 |
| should-fix | S4 | 착수 조건·순서 문장이 사용자 순서(P9 → P10 → P10b → V3 binding → V3 scope → B34 → B26-1)와 다르다. 착수 조건 5가 아직 `v3_scope_systemic.md`를 가리킨다. 두 게이트 card id(`20260930-v3-exempt-binding`, `20260930-v3-changed-stmt-scope`) 병합을 조건으로 적을 것 |
| minor | M1 | oracle (b) 메모(V4)가 계약 14 아래 글머리표로 들어가 있다. 계약 7·oracle 절로 옮길 것 |
| minor | M2 | 승인 기록 초안의 '덮는 것' ③에 B40(`unavailable_reason` 키 삭제)이 없다. 이것은 도달 불가 분기 삭제가 아니라 관찰 가능한 출력 변경이다. 한 구절 더할 것 |
| minor | M3 | `V3 계획` 1의 B26 head 수치(def 32·변이 2,438)는 시뮬레이션 P9 기준이다. 실제 P9(`b7765b0`) 기준으로는 def 32·변이 2,437이다(`kcl_series_union` 23). auditor 재측정 대상이므로 결론에는 영향이 없다 |

**1차 검토 처리**: B2·S1·S2·S3·S5·M1~M6은 실제로 고쳐졌다(아래 1). B1은 '절은 생겼으나 결정 반영 전 상태로 굳었다' → 이번 B1·B2. S4는 표는 생겼으나 7(c) red 형태에 조건이 빠졌다 → S2.

---

## 1. 1차 검토 지적 처리 확인

| 1차 | 확인 |
|---|---|
| B1 V3 계획 | 'V3 계획' 절과 `_metric_kcl_residual` 직접 호출 test(4)가 생겼다. 그러나 U1 결정(N2(b)+넓힌 T6, A1-a 면제 묶기)이 반영되지 않았다 → B1·B2 |
| B2 역방향 | 계약 7 관찰 대상이 B26-1 사이트로 정해지는 값으로 한정됐다. '계약이 아닌 것' 문장이 계약 절에 들어갔다. 고쳐짐 |
| S1 호출 수 | 불변식이 "= `load_topology` 호출 수 + 선언 있는 연결 파일 수"로 바뀌었다. 새 tmp 경로 규칙, SR은 import 금지도 들어갔다. 고쳐짐 |
| S2 netclass | "대부분 집합 소속"으로 정정됐다. 어댑터 대신 B35(진입 함수 `rails` 인자)를 택한 근거도 적혔다. 고쳐짐(처리 방향은 1차 권고와 다르지만 근거가 있다) |
| S3 승인 | `approval: 20260930-b26-before-phase3`. 기록 초안의 범위에 B26-1·B34가 둘 다 있다. 고쳐짐(M2만 남음) |
| S4 red 표 | 표가 생겼다 → S2(7(c) 조건) |
| S5 rail_nets | 계약 6이 "kcl_residual `rail_nets` 지금 거부, 그 밖의 옛 키는 MG1"으로 맞춰졌다. 고쳐짐 |
| M1~M6 | 3988 정정, `_TEMPLATE` 백로그, 연결 파일 형식 검사(계약 2), probe `rails=meta["rails"]`, `test_probe_dup_scan` 문자열 -- 반영됨. M4는 위치만 어긋났다(M1) |

## 2. V3 -- N2(b)+넓힌 T6 재측정 (B1)

| 정의 | 대상 변이 | 미실행 줄 변이 | 인벤토리 0 | 하한(×5 s) | 상한(Σ×인벤토리 시간) |
|---|---|---|---|---|---|
| def 전체(지금 규칙) | 2,437 | -- | -- | -- | -- |
| **N2b**(T6 = 삭제 뒤 한 문장) | **265** | 6 | 6(`_metric_kcl_residual`) | 22분 | 14.1 h |
| N2b + 넓힌 T6(own) | **314** | -- | -- | 26분 | 16.8 h |
| N2b + 넓힌 T6(deep) | **336** | 12 | 7 | 28분 | 17.9 h |

- 인벤토리 0 변이는 `sr._metric_kcl_residual`을 이름으로 부르는 test 하나로 0이 된다(재현함).
- 범위 정책 card의 B26-1 수치 228은 P9·B34·인계 삭제가 없는 옛 시뮬레이션이다. 이 card의 값은 N2b 265이고, 넓힌 T6을 더하면 314~336이다. 사용자 결정문의 "B26-1 변이 수(228) 재측정 필요"는 이 수로 바꾼다.
- def별 N2b → deep 큰 것:
  - `propose_device_roles_gap_fill` 40 → 57
  - `refine_…` 37 → 40
  - `run_matching_safety_with_finger_growth` 11 → 30
  - `audit_vertical_stack_id_vs_kcl` 14 → 16
  - `load_topology` 12 → 15
  - `rail_declaration` 14
  - `find_differential_pair_candidates` 13
  - `_propose_L_roles` 9 → 13
- 인계 삭제의 몫: 사이트 10(`if _netclass_al is not None:` 내어쓰기)으로 블록 2496~2523 문장이 계약 1의 '들여쓰기만 바뀐 문장 = 새 문장'(T1)이 되어 **부분 트리 전체**가 대상이다. 사이트 14 블록도 같다. `refine_…`의 N2b 37개 중 약 26개가 이 블록이다.
- **고칠 것**(오케스트레이터, card 'V3 계획' 절 전체 교체):
  - U1 → 결정됨. 원문 A1-a·A1-b와 그 정정을 인용한다.
  - 대상 수는 위 표로 적는다. 착수 시 auditor가 실제 병합본에서 다시 잰다.
  - 옛 선택지 (a)(b)(c)와 619개 누수 예시는 history로 옮긴다.
  - '6. 인계 삭제의 V3 몫'을 아래 B2 결과로 고친다.

## 3. 기존 test가 못 죽이는 대상 변이 -- 필요한 추가 계약 (B2)

실행: 옮긴 300개 중 **죽음 228 / 생존 72**다(N2b 53, 넓힌 T6 몫 19). 죽은 것의 중앙값은 85 s, 생존은 226 s다. 8개 병렬로 벽시계 약 95분, CPU 합 9.5 h가 걸렸다.

생존 72개를 계획된 계약이 죽이는지 판단했다.
- 계약 7(c)는 `true_current_mirror_groups` `if tr.gate in rails` 삭제 1개를 죽인다.
- 계약 7(a)의 층위1 항목은 지금 문장이 **부정형**("후보가 아니다")과 **비교형**("보통 내부 노드와 같은 결과")뿐이다. 그래서 층위1 루프 삭제(결과가 늘 빈 것)를 죽이지 못한다. 양성 기대값이 있어야 죽인다.
- 나머지는 계획된 계약과 무관하다.

| 묶음 | 생존(head 경로) | 원인 | 필요한 것 |
|---|---|---|---|
| E1 `propose_device_roles_gap_fill` 레일 사이트(B26-1 사이트 자체) | **13**: 4139 `y.gate in rails` 삭제, 4260 `for x` 삭제, 4275 cmp×2, 4276 `!= 1` const+, 4291 삭제·cmp, 4329 `for x` 삭제, 4338 삭제·cmp×2, 4360 삭제·cmp. 넓힌 T6 4278 `[0]` const−도 같은 묶음 | 이 사이트들은 `vds_match_vgs_of`·`budget_reference_device`·`fold_group` 제안을 정한다. 순수 연결성 + 레일 판정이고 netclass가 아니다. 계약 7은 이 필드를 관찰 대상에 넣지 않았다('계약이 아닌 것'에도 없다). library·기존 test도 이 판정을 보지 않는다 | **계약 7(e) 신설**: 합성 topology(선언 `rail_hi`/`rail_lo`)에서 손으로 정한 기대값. (i) 보상단 Y의 gate가 선언 레일이면 `vds_match_vgs_of` 제안 없음. (ii) 열린 단자가 정확히 하나이고 이웃 Y.source가 선언 레일일 때만 `budget_reference_device` = 그 이웃. 열린 단자 둘이면 제안 없음. (iii) X.drain이 선언 레일이면 `fold_group` 없음, Y.source가 선언 레일이면 `fold_group` 없음. 양성 1개 이상 포함. 관찰 경로는 `propose_device_roles_gap_fill(..., rails=)` 직접 호출(시그니처 바뀜 → base `TypeError`, red 밖)이나 `load_topology` meta `_device_roles_autofilled`의 그 세 필드다. 후자는 시그니처가 안 바뀌어 red가 된다. '계약이 아닌 것'과 겹치지 않게 필드를 지정한다 |
| E2 인계 사이트 10 블록(`refine_…` 2485~2512) | **13**: `for m in _matches_al` 삭제, 그 안 `current-mirror`/`diffpair-branch-load` 가지, `active_load_leg_candidates.update`, `signal_referenced_mirror_legs`, `branch_load_partner_candidates` 대입·비교 | 기존 test가 이 블록의 출력을 전혀 보지 않는다(b1에서도 미검증). 내어쓰기 때문에 N2에서 새 문장이 됐다 | 둘 중 하나. **(권고) 사이트 10 삭제를 이 card에서 빼고 B35로 넘긴다.** analog-grammar 진입 계약을 다시 쓰는 card이고 이 블록이 쓰는 netclass·idioms 출력을 판정해야 한다. 분기가 도달 불가인 채로 남는 것은 docstring에 이미 적혀 있다. **또는** 합성 회로에서 refine 반환의 세 필드 기대값을 손으로 정한 계약을 더한다(oracle (a)). 이 경우 netclass 유래 값이라 '계약이 아닌 것'과 충돌하므로 B26-1에 맞지 않다 |
| E2b 사이트 14 뒤 | 1: `gain_role_candidates \|= cascoded_active_load_legs` 삭제(T6) | 블록 자체(4058~4078)는 죽었다. 바로 뒤 합치는 문장의 결과(gain 역할 후보)를 보는 test가 없다 | 사이트 14도 B35로 넘기면 함께 빠진다. 남기면 gain 역할 관찰 계약이 필요하다(역시 netclass 유래) |
| E3 T3(b) def 기본값 상수 | **6**: `refine_…` `max_iterations=5` ±1, `repair_matching_safety` `max_iter=3` ±1, `run_full_circuit_audit` `row_width_tol=1.5` ±0.1 | 키워드 전용 `rails`를 더하면 def 머리가 바뀐다. 그래서 T3(b)가 def 자기 필드(기본값)를 대상에 넣는다. 기존 test는 기본값에 민감하지 않다 | **계약 4에 한 줄**: 세 함수의 기본값이 그대로다(`inspect.signature(...).parameters[...].default` 단언 -- 5, 3, 1.5). 값싸고 base에서도 통과한다(green-green). 이 card가 바꾸지 않는 값을 고정하는 회귀 test다 |
| E4 죽은 가드 | **3**: `_propose_L_roles` `if gm_id_roles is None`·`if candidates is None` 삭제, `_propose_gm_id_roles` `if candidates is None` 삭제 | 운영 흐름에서는 `refine_…`이 먼저 `None`으로 돌아가 도달하지 않는다. 직접 부르면 도달한다 | **계약 14에 더함**: gate 없는 입력 `fx`로 `_propose_gm_id_roles(fx, (), (), (), (), (), rails=…)`·`_propose_L_roles(fx, {}, (), (), (), (), (), rails=…)`가 `None`을 돌려준다. 가드를 지우면 `TypeError`가 난다 |
| E5 층위1 양성 | 5: `_diff_pair_layer1_groups` `for t` 삭제, `find_differential_pair_candidates` 층위1 루프(body[9]) 삭제, `range(i + 1, …)` arith·const±(T4 조상) | 계약 7(a)가 부정형·비교형만 있다 | **계약 7(a)에 양성 기대값**: 같은 kind, 다른 gate, **선언 밖** 넷을 source로 공유하는 두 소자(이름 `vdd`인 비선언 넷 포함)는 `find_matching_candidates` `diff_pair`·층위1 후보에 **있다**(손으로 적은 기대 dict). `range(i+1)` ±1 3개는 체인 3개 이상인 branch 쌍 입력이 있어야 죽는다. 등가일 수 있으니 auditor가 판정한다 |
| E6 실행되지 않는 경로(`rails=` 호출부의 이웃) | **17**: `optimize_full_circuit_budget`(+중첩 `_evaluate_row_split`) 9411·9413 `repair_matching_safety` 가지 4개(미실행 줄), `_fixup_euler_blocked_rows` 11704~11708 3개(미실행), `run_matching_safety_with_finger_growth` 10개(11809·11810·11837·11844~11846·11886~11890) | 호출문에 `rails=rails`를 붙여 새 문장이 되고, 그 뒤 문장이 T6·넓힌 T6로 대상이 됐다. 이 경로는 기존 test가 실행하지 않거나 결과를 보지 않는다 | 레일과 무관한 기존 경로(euler-blocked fixup, finger growth, LUT 없는 repair)라 이 card가 test를 쓰는 것은 범위 밖 비용이다. **승인 기록이 필요한 면제**(A1-a 묶기 규칙, `target_kind: decision`, 변이 id@함수 해시)로 처리할지, test 보강을 백로그 card로 먼저 낼지를 'V3 계획'에 적는다. 사용자 승인 몫이다 |
| E7 기타 넓힌 T6·T6 | 12: `run_full_circuit_audit` `mc["current_mirror"]`·`mc["diff_pair"]` 루프 삭제 2, `resolve_stack_layout` 6578 `if refined…` 삭제 1, `propose_vertical_stack_id_gap_fill` 3271 `if inputs or…` 삭제·3275 1+1, `propose_device_roles_gap_fill` 3967·3968 씨앗·4508 `case_collisions` 3, `_propose_*` 씨앗 `seeds[ga]=gb`·`seeds[gb]=ga` 4 | 바뀐 호출문의 결과를 쓰는 뒤 문장을 관찰하는 test가 없다 | `run_full_circuit_audit` 결과의 `found_groups`(current_mirror/diff_pair 그룹) 기대값 계약, 포트 선언이 있는 `propose_vertical_stack_id_gap_fill` 계약을 더하거나, E6와 같이 면제 승인 |

**숫자 정리**: 생존 72 = E1 14 + E2 13 + E2b 1 + E3 6 + E4 3 + E5 5 + E6 17 + E7 12 + 7(c)가 죽이는 `true_current_mirror_groups` 1(표에는 따로 적지 않음).
- 위 계약(E1·E3·E4·E5)을 더하고 E2·E2b를 B35로 넘기면, 남는 것은 E6 17 + E7 12 = 29개다(테스트 보강이나 면제 승인 대상).
- 계약 test는 '앞 검토의 교훈'대로 쓴다: 이름은 `_b26_` 접두로 유일하게, 직접 호출, parametrize 문자열 금지.

주의(근사의 한계):
- b1은 레일을 이름 집합으로 판정한다. head의 선언 기반과 library·픽스처에서 같지만, 합성 입력에서는 다르다.
- B34 계약 test 파일은 사본에 없다(초안만 있다). B34 test가 `refine_…` 출력의 세 필드를 보지 않으므로 E2 결론은 바뀌지 않는다고 본다.
- 새 문장 36개(`rail_declaration` 14, 선언 획득·연결 파일 검사, `rail_nets` 거부, `l_sharing_classes` meta 거부)는 계약 1·2·5·6이 죽인다고 판단했다(계약 1은 거부 4종과 빈 list 수용을 각각 둘 것, 계약 2는 연결 파일 형식 위반과 집합 불일치를 각각 둘 것).

## 4. red 형태 (계약별)

| 계약 | 진입점 | base 결과 형태 | 판정 |
|---|---|---|---|
| 1 | `rail_declaration` | `AttributeError`(신규 심볼, 표에 있음) | red(신규 심볼) |
| 2 | `load_topology`(선언 없음 → `pytest.raises(ValueError)`) | `Failed`(DID NOT RAISE, `builtins.Failed`) | red |
| 3 | `monkeypatch.setattr(sd, "rail_declaration", …)` | `AttributeError` | 신규 심볼 red |
| 5 | `l_sharing_classes(by, meta 없음 "rails")` | `Failed` | red |
| 6 | kcl_residual `rail_nets` | `Failed` | red |
| 7(a)(b)(d) | `load_topology` meta / `compute_metric`·`_metric_kcl_residual` | 단언 실패 | red(시그니처 불변 진입점) |
| 7(c) | `l_sharing_classes(by, meta)` | meta를 `rail_declaration`으로 만들면 `AttributeError`, `load_topology`로 얻으면 단언 실패 | **S2** -- `load_topology`로 얻게 적을 것 |
| 13 | `refine_…(…, rails=)`, `propose_…(…, rails=)` 부재 | `TypeError` | **S1** -- red도 green도 아님, 집계 밖으로 적을 것 |
| 14 | 직접 호출(`rails=`) | `TypeError` | card가 정직하게 '집계 밖'으로 처리함(맞다) |
| 신규 E1(제안) | `load_topology` meta 세 필드 | 단언 실패 | red 가능 |
| 신규 E3·E4(제안) | 서명 기본값 / 직접 호출 | green / `TypeError` | 집계 밖 |

card의 V2 주의(새 키워드 인자 직접 호출은 `TypeError`라 red가 아니다)는 맞다. 판정 기록에 '단언 red', '신규 심볼 red', 'TypeError 집계 밖', 'green 회귀 고정' 네 칸을 나눠 적게 하면 계약 13·14와 E3·E4가 정직하게 분류된다.

## 5. test 파급 (B3, S3)

- **P9 계약 test(B3)**: `b7765b0:…/tests/contracts/test_dup_kcl_edges.py` 281~298행이 두 함수의 매개변수 목록을 정확히 단언한다(`["netlist", "matching_pairs"]`, `["transistors", "matching_pairs"]`). B26-1 병합본에서 두 test가 FAIL이다. 262·271행의 호출 2곳(11 케이스씩)은 `rails=` 추가로 해결된다. 하지만 시그니처 단언은 **기대값 변경**이다.
  - **고칠 것**: 계약 12에 "P9 계약 2·3의 시그니처 단언은 B26-1이 계약으로 바꾼다(새 기대 = 앞의 매개변수 + 키워드 전용 `rails`, 기본값 없음)"를 적는다.
  - 오케스트레이터가 `target_kind: diff` 승인 기록(사유: P9 '시그니처 유지' 계약을 B26-1 계약 4가 대체, 판정 기준 약화 아님 -- 매개변수 목록 단언은 유지)을 받는다.
  - test-author는 interface card의 새 시그니처로 갱신한다.
  - P9 card '의도'의 "함수·시그니처 유지"와 충돌한다는 것을 card '작성 전 실측' 7에 적는다.
- 다른 시그니처 고정 test: `grep "signature("` → `test_dup_w_calc.py`(무관)뿐이다.
- **넷리스트 직접 호출(S3)**: selftest 49곳(card 실측)과 P9 test 2곳은 topology 없이 `Transistor` 목록을 만든다.
  - P9 test의 레일 이름 입력은 `gnd` 3회 사용 케이스 하나다(112~114행). 3회 사용 규칙으로 결과가 같으므로 어떤 선언이든 판정은 불변이다.
  - 규칙을 card에 적을 것: "`rails = stick_diagram.rail_declaration({"supply_nets": [그 넷리스트 단자에 나오는 'vdd','gnd','vss'(소문자 정확히 일치)]})`. 대문자 레일 이름 픽스처는 없다(card 실측)."
- 로드 경로 픽스처 17개(sizing 15 + stick 2)는 1차 실측과 같은 규칙이다. test-author가 소스 없이 할 수 있다(파일·줄·이유가 card에 있다).
- B34 계약 test `rails=` 추가는 계약 12 셋째 항목에 있다. 할 수 있다.
- 추가 계약(E1·E3·E4·E5)을 더하면 test-author가 읽어야 할 문장이 는다. 각 계약에 입력(소자 생성자 인자)과 기대값을 card 문장으로 적어야 소스 없이 쓸 수 있다. E1은 회로 구성(보상단 선언 `compensation.stage_devices`, `vertical_stack_id` 선언)이 필요하니 '재현할 수치'에 입력 JSON을 싣는다.

## 6. B34 인계의 정확성 (도달 불가 확인)

B34 뒤 `_import_analog_grammar`는 실패하면 `ImportError`를 던지고, 성공하면 모듈 튜플을 돌려준다.

| 사이트 | 근거 | 결론 |
|---|---|---|
| 9 `classify`의 `netclass is None` | 위 반환 규칙 | 도달 불가 |
| 9 `cls_before is None` | `cls`는 `netclass.classify_nets` 반환 튜플의 첫 원소(dict, netclass.py 92~95 docstring "(netclass dict, impedance dict, assumptions list)") | 도달 불가 |
| 10b `relations is None` | `find_verified_…`의 `None`은 `netclass is None`(1715)·`not devs`(1718)뿐이다. `find_differential_pair_candidates`의 `None`은 `suggest_vertical_stack_composites`의 같은 두 조건(1446·1449)에서만 나온다. 같은 `transistors`라 `devs`가 비면 루프 첫 회 2420에서 먼저 반환된다 | 도달 불가 |
| 10·13·14 | `_netclass_al`·`_netclass_lcmf`·`_idioms_lcmf`는 늘 모듈이다 | 도달 불가. 지워도 의미 불변 |
| B40 | 분기는 gate 소자 없는 입력에서 여전히 참이고, 키만 지운다 | 맞다 |

- 줄 번호(7535799): 2400·2410·2420·2440·2494·2495·3966~3970·4071~4073·4087·4110·4111, docstring 3932~3933·2349~2350. **card 표와 일치**한다.
- 모의 head에서 `cls_before is None`·`relations is None`·`_netclass_al is not None`·`_netclass_lcmf is not None`·`_idioms_lcmf is not None`·`cascoded_active_load_legs = set()`은 0회다.
  - `netclass is None`이 5회 남는 것은 B35 사이트 5~8 등 다른 def에 있는 것이다.
  - `unavailable_reason`이 5회 남는 것은 `propose_theta_kcl_gap_fill`(B39)과 docstring이다.
- **결론**: 인계는 의미상 맞다. 문제는 V3 비용뿐이다(B2 E2).

## 7. 사실 재측정

| 문장 | 결과 |
|---|---|
| 인계 사이트 줄(7535799) | 일치 |
| 운영 `supply_nets` 참조 = SR 4361 하나(4352는 docstring) | 일치 |
| B34 변경 뒤 SD 사이트가 4줄 당겨짐(1575 → 1571) | 일치(b1에서 1571·1613·2092·2168·3133(P9 뒤)·3238·3973·4152·4288·4304·4351·4373) |
| 대상 def 32 / 변이 2,438 / 닿은 135 | 실제 P9 기준 def 32 / 2,437(M3). '닿은 변이'는 N2 이후 쓰지 않는 개념이라 지울 것 |
| `classify` 새 대상 6변이 | 일치. 다만 N2에서 인계 몫은 '6변이'가 아니라 사이트 10·14 블록 전체(B2) |
| 인벤토리 수 | b1(+P9 test)에서 `refine_…` 145~146, `propose_device_roles_gap_fill` 138~139 등 card와 같은 크기 |
| 기준 실행 | b1 인벤토리 합집합 208 passed·3 xfailed(ts6 2개 제외) |

## 8. 권고 수정 요약

1. (B1) 'V3 계획' 절을 결정 반영판으로 교체한다. 대상 265(N2b) / 314~336(넓힌 T6). 착수 조건 5 = 두 게이트 card 병합(S4).
2. (B2) 계약 추가:
   - 7(e) device_roles 세 필드(E1)
   - 4에 기본값 고정(E3)
   - 14에 `_propose_*` gate 없음 직접 호출(E4)
   - 7(a) 양성(E5)
   - 사이트 10(+14)을 B35로 넘기거나, 넘기지 않으면 그 몫의 계약·승인(E2)
   - E6·E7 29개는 test 보강 card를 먼저 내거나 A1-a 묶기 면제 승인(사용자 몫)으로 처리하고, 'V3 계획'에 적는다
   - 추가 계약은 모두 "V3 필수 -- 생략 불가"로 표시한다
3. (B3) 계약 12와 승인 경로에 P9 시그니처 단언 갱신을 넣는다.
4. (S1·S2) 계약 13 증거 종류를 고친다. 7(c) meta 획득 경로를 `load_topology`로 적는다.
5. (S3) 넷리스트 직접 호출의 `rails` 규칙을 적는다.
6. (M1~M3) 문단 위치, 승인 기록 B40 구절, 수치 정정.

## 산출물·정리

scratch `C:/g70`의 내용:
- `base`(archive), `wb`·`w0~w7`(b1 사본)
- `scripts/m70.py`(모의 head·대상 분류·넓힌 T6), `kill70.py`(head→b1 대응·변이 실행), `drive70.py`, `baseline70.py`, `sum70.py`, `dump70.py`
- `out/targets.txt`(대상 336 목록), `out/survivors.txt`(생존 72 목록)

수치는 이 문서에 옮겨 적었다. 측정 뒤 `C:/g70`을 삭제했다.
