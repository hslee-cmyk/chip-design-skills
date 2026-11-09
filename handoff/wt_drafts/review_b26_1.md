# 독립 검토: B26-1 spec card(`draft_b26_1.spec.md`, id 20260930-b26-rail-accessor-set)와 계획 정정안(`draft_b26_plan_patch.md`)

검토자 = 작성자가 아닌 독립 reviewer. 저장소는 읽기만 했다(HEAD = gate `master` cd64170, `git status`는 시작할 때와 같음).
실험은 scratch `C:/g32`에서 했다. `git archive cd64170`으로 만든 사본 세 벌을 썼다.
- `base`: 원본.
- `b26`: B26-1 상당 패치본. 계약 4의 16줄을 선언 레일로 바꾸고, `rail_declaration`·`meta["rails"]`·연결 파일 충돌 거부·`rail_nets` 키 거부를 넣었다. 키워드 인자를 줄줄이 넘기는 대신 `load_topology`가 채우는 전역 레일 집합으로 근사했다.
- `b26f`: `b26`에 픽스처 규칙을 근사로 더한 사본. 선언이 없으면 넷 중 옛 이름 집합에 있는 것을 레일로 본다.

끝난 뒤 C:/g32는 삭제했다. P9는 아직 병합 전이라 base는 cd64170이다. P9 병합 뒤에는 SD 3042 한 줄이 빠진다.

---

## 0. 결론 요약

| 등급 | # | 요지 |
|---|---|---|
| **blocking** | B1 | **V3를 이 card 구조로는 통과할 수 없는데 계획이 없다.** `mutate_changed.py`는 AST가 바뀐 def의 **본문 전체**를 변이한다. B26-1이 바꾸는 def는 약 32개, 변이는 약 2,465개다(`_build_theta_evaluator` 497, `propose_device_roles_gap_fill` 331, `optimize_full_circuit_budget` 229 …). `_metric_kcl_residual`은 base에서 정적 인벤토리가 0이다. B28(V3 이력 복제본)이 들어가면 도구가 실제로 돌고, 레일과 무관한 문장의 생존 변이가 거의 확실하다 |
| **blocking** | B2 | **계약 7의 '역방향'은 공개 진입점 `load_topology` meta에서는 병합본에서도 성립하지 않는다.** analog-grammar `netclass.RAILS`가 대소문자 무관 이름 집합이기 때문이다. test-author가 소스 없이 meta 수준 test로 쓰면 green 실패 → dispute(과거 재시도 원인 유형) |
| should-fix | S1 | 계약 3("`load_topology` 1회 뒤 `compute_metric`을 몇 번 불러도 추가 호출 0회")은 설계대로 구현해도 거짓이다. `_load_full_topology_cached`가 처음 캐시를 못 찾으면 `load_topology`를 한 번 더 부른다. 실측: 1 → 2 → 2 |
| should-fix | S2 | netclass 사실 문장 "극성 판정이다"가 틀렸다. 대부분 **집합 소속** 판정이다. 미루는 진짜 이유는 쓰기 경로와 어댑터에 극성이 필요하다는 점이다. 정정안 DF-19 비고도 같이 고칠 것 |
| should-fix | S3 | DEC-60 넷 전환기 종료와 Phase 4 DF를 Phase 3 전으로 당기는 것은 '알림'이 아니라 **승인 기록**으로 남길 것. 선례: U-39 기본안도 사용자 원문 승인, DF-35·36 앞당김도 사용자 지시 |
| should-fix | S4 | red 진입점을 계약 7 (a)~(d) 항목별로 적을 것. (b)는 `_vertical_stack_id_autofilled`로 red가 난다(실측). 역할 자동채움 null·`headroom_role`은 기대값으로 쓰지 말 것 |
| should-fix | S5 | 계약 6(`rail_nets` 키 거부)과 정정안 N3.16("옛 키 거부 게이트는 MG1")이 서로 어긋난다 |
| minor | M1~M6 | 픽스처 사실 1건 정정(3988은 로드 경로가 아님), `_TEMPLATE` 예외 종류 변화, 연결 파일 선언 형식 미규정, oracle (b) V4 메모, probe 갱신, 정정안 해시 확인 |

사실 문장은 대부분 재측정으로 확인됐다(§1). 경계의 원칙(집합 대 극성)은 줄 단위로는 깨끗하다. 다만 **함수 출력 수준에서는 netclass와 `trace_*`가 섞인다**(B2·S4).

---

## 1. 사실 문장 재측정 (cd64170)

| 문장 | 결과 | 근거 |
|---|---|---|
| B26-1 = 11함수 16줄(SD 1014·1575·1617·2096·2172·3042·3148·3253·3992·4171·4307·4323·4370·4392, SR 2207·4293) | **일치** | `grep -n "_RAIL_NETS\|_DEFAULT_RAIL_…"` 결과와 AST 함수 매핑이 줄 번호까지 같다. 2096·2172는 `seeds = {"vdd": "vdd", "gnd": "gnd"}` |
| 새 인자를 받는 함수 20개(SD 18, SR 2) | **일치, 닫힘 확인** | 20개 각각의 운영 호출자를 AST로 셌다. 호출자는 전부 20개 안에 있거나, 계약 4의 뿌리(`load_topology`, `run_full_circuit_audit_from_topology`, `_build_theta_evaluator`, `l_sharing_classes`, SR `optimize_full_circuit_budget`·`run_matching_safety_with_finger_growth`·`_fixup_euler_blocked_rows`·`run_topology_pipeline_with_finger_fixup`)다. 빠진 호출자는 없다. 운영 미도달 함수(`propose_theta_kcl_gap_fill`, `find_differential_and_mirror_forks`, `node_pole_estimate`)는 바뀌는 함수를 부르지 않는다 |
| test 호출 49 / 2 / 4 | **일치** | `test_selftest_stick_diagram.py` 12함수 49곳(함수별 수도 같다), `test_selftest_sizing_recipe.py` `resolve_stack_layout` 2곳, `tests/probes/` 4파일 `true_current_mirror_groups` 각 1곳. 4 probe는 모두 `load_topology`의 meta를 이미 손에 들고 있다. `monkeypatch`로 이 함수들을 바꾸는 test는 0개 |
| 픽스처 15 + 4 | **15 일치, 4는 3** | 엄격 거부 사본(`b26`) 전체 실행: base 52 failed·746 passed·15 xfailed → b26 65 failed·729 passed·15 xfailed·4 errors. 새 실패 17건은 전부 `supply_nets missing`이다. 내역: sizing 11 FAILED + setup ERROR 4(s039·s041·s050·s053 -- 픽스처 `s037_state`·`s038_state`·`s040_state`·`s052_state`), stick s071(1780·1787)·s125(2798). **3988(`test_s160` conflict_fixture)은 `apply_device_roles_gap_fill`만 부르고 로드하지 않는다** -- b26에서 선언 없이 PASS(M1) |
| 픽스처 규칙이면 기존 판정 불변(`vss` 씨앗 포함) | **확인** | `b26f`에서 두 selftest 파일: base 196 passed·3 xfailed = b26f 196 passed·3 xfailed, 실패 집합 같음 |
| E-LIB 9/9, 감사 9/9 | **확인** | `transistors`와 `meta`(새 키 `rails` 제외, float는 hex)가 9/9 같다. `run_full_circuit_audit_from_topology`: current_reuse·two_stage_ota는 결과가 같고, 나머지 7개는 같은 `ValueError`(`_netlist_sections_structured`) |
| 합성 4소자 수치 | **전부 재현** | base: `diff_pair {(nmos, rail_lo): [Qa, Qb]}`, 엣지 4(rail_lo·rail_hi 경유 포함), `kcl_series_union` 1그룹, `_matching_pairs_autofilled = [Qa, Qb] offset layer1 폴백`, 네 소자 `gm_id_role: matching`·`L_role: mirror`. b26: `{}`, 엣지 2, 2그룹, `null`, `headroom_role`만 |
| oracle (b) setup 불변 | **재현** | base: `two_stage_ota`만 DIFF, 나머지 3 SAME. b26: 4/4 SAME. 입력은 `vdd/gnd/vss`를 라이브러리 밖 이름으로 바꾼 사본의 `stack_groups_kcl`·`stack_groups_geometry` |
| netclass `RAILS*`: SD 11함수(운영 7) | **일치** | 11함수: `find_idiom_matches`, `find_stack_edges`, `find_differential_and_mirror_forks`, `suggest_vertical_stack_composites`, `find_verified_…`, `_propose_vertical_stack_ids`, `_propose_headroom_roles`, `refine_…`(2곳), `audit_theta_root_direction`, `propose_theta_kcl_gap_fill`, `propose_device_roles_gap_fill`. 도달 7개가 정정안 목록과 같다 |
| `_RAIL_NETS` 참조 함수 10 → 3 | **일치** | |
| 레일 판정 운영 함수 SR 14 · SD 14 | **일치** | prep §1 표 기준 |
| 이름 충돌 0 | **일치** | 저장소 grep `rail_declaration\|RailDeclaration` 0건 |
| library `rail_nets` 사용 0 | **일치** | library·tests·run_harness 0건 |
| `supply_nets` 운영 참조 SR 4361 하나 | **일치** | 4352는 docstring |
| "`tests` 트리 안 대문자 레일 이름은 각 1회 -- 해당 픽스처를 확인" | **부정확** | 유일한 출현은 `tests/probe_physical_consistency.py:40`의 probe 레일 집합 `RAIL_HI, RAIL_LO = {"vdd","VDD"}, {…}`이다. 픽스처가 아니다(M1) |

---

## 2. blocking

### B1. V3: 변이 대상이 본문 전체라 이 card는 계획 없이는 V3 FAIL(또는 ERROR)이다

**근거**
- `tools/gates/mutate_changed.py` ①·`mutants()`: 대상 = diff가 닿은 def 중 `ast.dump` 해시가 바뀐 것. 변이는 **그 def의 모든 노드**에 건다(비교 뒤집기·산술·상수·문장 삭제·조기 return·except 삭제, 중첩 def 포함). 바뀐 줄에만 거는 것이 아니다.
- B26-1에서 AST 해시가 바뀌는 def를 셌다. 계약 4의 20개, 그 호출부 전부(`rails=`를 넘겨야 하므로), 뿌리를 합쳐 **약 32개**다. 도구 자신의 `mutants()`를 base 본문에 돌린 변이 수는 **약 2,465개**다(최종 코드에 따라 조금 달라진다). 큰 것:
  - `_build_theta_evaluator` 497(1,004줄)
  - `propose_device_roles_gap_fill` 331
  - `optimize_full_circuit_budget` 229
  - `repair_matching_safety` 112, `_branch_composite_pair` 102, `run_matching_safety_with_finger_growth` 99
  - `refine_…` 95, `_fixup_euler_blocked_rows` 89, `run_topology_pipeline_with_finger_fixup` 64, `load_topology` 58, `_metric_kcl_residual` 54
- 인벤토리(도구의 `reachability.build_graph` + `inventory`, base): `load_topology` 230 test, `propose_device_roles_gap_fill` 231, `_build_theta_evaluator` 110, `optimize_full_circuit_budget` 74 … 사이징 평가를 지나는 느린 test가 대부분이다. 변이 × 인벤토리 실행 시간은 수 일 단위다.
- **`_metric_kcl_residual`의 base 인벤토리는 0이다.** `compute_metric` → `_METRICS_REGISTRY` dict 경유라 정적 그래프에 간선이 없다. 같은 이유로 `_metric_parasitic_pm_deg` 등도 0이다. 새 test가 `sr._metric_kcl_residual`을 **이름으로** 참조하지 않으면 54개 전부 '인벤토리 없음 → 생존'이다.
- B28(`20260930-v3-history-clone`, interface card까지 gate에 있다)이 병합되면 도구가 실제로 돈다. 기준 실행이 실패하면 ERROR다. 그러면 P8·DF-36처럼 "도구가 못 돌아서 auditor가 사이트만 대체 측정"하는 선례를 쓸 수 없다. `레일과 무관한 문장`(예: `_build_theta_evaluator`의 로그·주석성 대입, 레이아웃 경로의 가지)의 생존 변이는 V3 FAIL이다. 등가 변이 면제는 변이 id 목록의 decision 승인으로만 할 수 있다.
- 초안의 "SR 7282·8003·8091은 V3 변이를 죽일 test를 쓸 수 없어 B26-2로 옮긴다"는 논리는 일관되지 않다. `_build_theta_evaluator`는 `kcl_series_union`·`resolve_stack_layout`에 `rails=`를 넘기므로 **어차피 본문 전체(497개)가 V3 대상**이다. 8003을 옮긴다고 대상에서 빠지지 않는다.

**고칠 것(card에 'V3 계획' 절을 추가, 착수 전 결정)**
1. V3 대상 def 목록과 변이 수를 사실 문장으로 적는다. 위 수치는 착수 시 P9 병합본에서 다시 잰다.
2. 처리 방식을 정한다(사용자 결정 U1):
   - (a) 이 card에 한해 V3 대상 범위를 **diff가 닿은 문장과 새 def**로 제한하는 decision 승인을 받는다. 나머지 변이는 id 목록 면제(도구 `--out`으로 목록 생성).
   - (b) card를 더 잘게 나눈다. 다만 `kcl_series_union`·`audit_vertical_stack_id_vs_kcl`이 로드 경로와 평가 경로에 함께 쓰여 경로별로 깔끔히 나눌 수 없다.
   - (c) 전수 실행을 받아들이고 생존 변이마다 test를 보강한다(시간 비용이 매우 크다).
   - 원칙("기본값 없는 키워드 인자")이 이 규모의 변경을 강제하므로, 게이트 판정 범위를 좁히는 것은 사용자 몫이다.
3. 어느 쪽이든 `_metric_kcl_residual`을 대상으로 하는 새 test는 `sr._metric_kcl_residual(spec, ctx)`를 **직접 이름으로** 부른다. 시그니처가 안 바뀌어 base에서도 호출된다. 그리고 레일 제외만이 아니라 본문 가지(`ideal_sources` `value_amp`/`null` 건너뛰기, `exclude_nets`, 최댓값)를 손으로 계산한 기대값으로 덮게 적는다. 이것은 계약 7(d)에 없는 요구다.

### B2. 계약 7 '역방향'은 `load_topology` meta 수준에서 병합본도 성립하지 않는다

**근거(실측, `C:/g32/rev.py`)**: 선언 `supply_nets = [rail_hi, rail_lo]`인 5소자 합성 회로를 만들었다. 내부 노드 이름만 `nmid`(중립) / `vss` / `vdd` / `gnd` / `VSS` / `agnd`로 바꾸거나 게이트 넷을 `vdd`·`gnd`로 바꾸고, `load_topology` meta(`rails` 제외, 이름 역치환)를 중립판과 비교했다. **base·b26 모두 7/7 DIFFERENT**다. b26에서 달라지는 키는 `device_roles`·`_device_roles_autofilled`의 `headroom_role`이다(`vss` 노드 소스 소자가 `mirror` 대 `cascode`). `netclass.RAILS`(`_CaseInsensitiveNetSet`, `VDD/AVDD/DVDD/VCC/VDDA/GND/VSS/AGND/DGND/VSSA`)가 `propose_device_roles_gap_fill`·`refine_…`·`_propose_headroom_roles` 안에서 그대로 이름으로 판정하기 때문이다.

**고칠 것**: 계약 7 역방향의 관찰 대상을 B26-1 사이트만으로 정해지는 값으로 한정해 적는다.
- `_matching_pairs_autofilled`
- `_vertical_stack_id_autofilled`
- `l_sharing_classes`
- kcl_residual
- (직접 호출) `find_matching_candidates`·`_kcl_and_matching_edges`·`kcl_series_union`

그리고 "`headroom_role`·`_device_roles_gap_fill_review_needed`·netclass 유래 필드와 `load_topology` meta 전체의 이름 불변은 계약이 아니다(B26-2)"를 계약 문장으로 넣는다. 지금은 oracle 절에만 있다. test-author는 소스를 못 보므로 interface card에도 싣는다.

---

## 3. should-fix

### S1. 계약 3의 호출 수 문장이 설계와 맞지 않는다
실측(`C:/g32/count.py`, b26): 계약대로 `load_topology` 1회를 부른 뒤 `compute_metric(kcl_residual)`을 3회 부르면 `rail_declaration` 누적 호출이 1 → **2**가 된다. 그 뒤 `l_sharing_classes`를 3회 불러도 2다. 두 번째 호출은 `_load_full_topology_cached`가 처음 캐시를 못 찾아 스스로 `load_topology`를 부른 것이다(새 캐시가 아니라 기존 구조다). `_build_theta_evaluator`도 자기 `load_topology`와 캐시 엔트리로 두 번 읽는다.
**고칠 것**: 불변식을 "`rail_declaration` 호출 수 = `load_topology` 호출 수"로 적는다. 관찰은 "경로마다 첫 평가 뒤 `compute_metric` N회·`l_sharing_classes` N회 동안 증가 0"으로 하고, test는 매번 새 tmp 경로를 쓴다(모듈 수준 캐시가 test 사이에 남는다). 계수 래퍼는 `stick_diagram.rail_declaration`을 바꾼다. SR이 이 이름을 `from stick_diagram import`로 가져오면 그 별칭은 세지 못하므로, "SR은 `rail_declaration`을 import하지 않는다"를 계약에 넣거나 두 이름공간을 다 바꾸게 적는다.

### S2. netclass에 대한 사실 문장과 처리 방향
- 초안 '범위 밖' 3번째 항목과 정정안 DF-19 비고는 "극성 판정이다"라고 한다. 실측하면 **집합 소속이 대부분**이다.
  - 집합 소속 `RAILS`: netclass 80·82·134·137·140·226·269·270·314·321·342, idioms 264·373·529·572·599·714
  - 극성: netclass 102·103(`SUPPLY/GROUND` 분류)과 idioms 600·601뿐
- 미뤄야 하는 진짜 이유는 둘이다.
  - (1) 쓰기 경로: N3.12.2 표에 `skills/analog-grammar/**` 행이 어느 주체에게도 없다. analog-grammar는 별도 skill(`analyze.py` CLI·자체 SKILL.md)이다.
  - (2) SD 쪽 대체(어댑터)에는 극성이 필요하다. netclass는 레일을 `POS/NEG`로 나눠 받으므로, 선언 레일을 정준 토큰으로 바꿔 넘기려면 hi/lo를 알아야 한다. 이것이 D1이다.
- **권고 처리**: analog-grammar 파일은 고치지 않는다. B26-2에서 SD의 `_import_analog_grammar` 호출부에 어댑터를 둔다(code-author 경로). 선언 레일은 극성별 정준 토큰(`VDD`/`GND`)으로, 선언 밖의 레일 이름 넷(`vss`·`agnd` 등, 대소문자 무관)은 중립 토큰으로 바꿔 넘기고 결과를 역치환한다. 경로표 개정(plan_tables 승인)이 필요 없다. 정정안 DF-19 비고의 "경로표 개정 또는 호출부 대체가 필요하다"를 이 기본안으로 적는다.
- 참고: netclass `HINT_*` 정규식(입력·바이어스 이름 힌트)도 이름 기반이다. 레일과 다른 개념이므로 범위를 적어 두면 lint(B26-4)에서 혼동하지 않는다.

### S3. DEC-60 전환기 종료와 앞당김은 승인 기록으로
- N2 결정표는 "무엇이 이미 정해졌는지는 이 표가 정본"이다. DEC-60의 한시 조항과 그 기한("MG1(Phase 4) 전까지")도 결정 내용의 일부다. 종료 논리 자체(전제 소멸: U-26 (b) 9/9, DEC-60 본문 "넷 이름 집합으로 판정하지 않는다"와도 일치)는 타당하다. 다만 선례는 모두 사용자 원문이 있다: U-39는 기본안이어도 `target_kind: decision` 승인 기록(원문 "U-39는 기본안대로 하고")을 남겼고, DF-35·36 앞당김은 사용자 지시("DF-36도 같이 진행해")였다.
- card 머리의 `approval: 20260923-20-dead-code-dup-design`은 design 20(P 목록)의 승인이고 B26을 덮지 않는다. DF-36 선례를 따른 것이지만 그 card에는 사용자 지시가 따로 있었다.
- **고칠 것**: 한 건의 decision 승인 기록(target = DEC-60 넷 전환기 종료 + DF-19·DF-26 넷 몫 MG1 분리 + B26-1을 Phase 3 전 착수)을 받아 card `approval` 줄에 더한다. 착수 조건 3의 "이의 없음 기록"을 이것으로 바꾼다(사용자 결정 U2).

### S4. red 진입점을 항목별로 확정하고, 관찰값을 계약값으로 쓰지 말 것
실측한 red 입력(base assertion 실패 → b26 통과):

| 계약 | 진입점(시그니처 불변) | base → 병합 상당 |
|---|---|---|
| 7(a) | `load_topology` meta `_matching_pairs_autofilled` | `[Qa,Qb offset layer1]` → `None` |
| 7(b) | `load_topology` meta `_vertical_stack_id_autofilled`, 합성 4소자 + `device_roles.Qa.vertical_stack_id = "S1"` | `{Pa,Pb,Qb: S1}` → `{Pa: S1}`. 이 입력이 없으면 7(b)의 red는 oracle (b)(library `two_stage_ota`)뿐이고, 직접 호출은 base TypeError다 |
| 7(c) | `sr.l_sharing_classes`, 게이트가 `rail_hi`인 NMOS 둘 + 게이트 `bp`인 PMOS 둘 | `{Ma,Mb},{Pc,Pd}` → `{Pc,Pd}` |
| 7(d) | kcl_residual, 합성 4소자 ID 1·2·1·2.5 µA | 3.5e-6 → 5.0e-7 |
| 2 | `supply_nets` 없음 | base 받아들임(`DID NOT RAISE` = Failed, DF-36 판정 기록이 red로 셈) |
| 6 | `rail_nets` 키 | base 5.0e-7(키를 읽음) → ValueError |

주의:
- 합성 4소자의 `Pa`·`Pb`(같은 게이트 `bias_p`, 같은 소스 레일)는 실제 전류미러다. 병합 상당에서 `L_role`·`gm_id_role` 자동채움이 `null`이 되는 것은 **관찰값**이지 물리로 정한 기대값이 아니다. `headroom_role`(`cascode`)도 netclass 유래라 틀린 값이다. 이 셋은 test 기대값으로 고정하지 말 것(초안 '재현할 수치'의 역할 문장을 "계약 아님"으로 표시).
- `find_differential_pair_candidates`는 1575줄만 B26-1이고, 후보는 `trace_*`(여전히 `"vdd"`/`"gnd"` 진입)에서 온다. 합성 레일 이름에서는 가지 추적이 비고 층위1 폴백만 동작한다. 7(a)의 "층위1 폴백 후보가 아니다"는 맞지만, "차동 후보 전반"으로 일반화하지 않게 적는다.

### S5. `rail_nets` 거부와 정정안 N3.16 문구
계약 6은 kcl_residual 선언의 `rail_nets` 키를 **지금** `ValueError`로 거부한다. 조용히 무시하면 폴백이므로 방향은 맞다. 그런데 정정안 §3 N3.16은 "metric 키 `rail_nets` 읽기는 B26-1에서 없앤다(옛 키 거부 게이트는 MG1)"라고 한다. 정정안을 "kcl_residual의 `rail_nets`는 B26-1에서 거부, 그 밖의 옛 키(`supplies`, 스칼라 `vdd`, metric `supply_nets`) 거부 게이트는 MG1"로 맞춘다.

---

## 4. minor

- **M1** 픽스처 문장 정정: '작성 전 실측' 7의 stick 4개 중 3988(`test_s160`)은 로드 경로가 아니다. 선언 없이 b26에서 PASS다(추가해도 해는 없음). 영향 test는 sizing 15(FAILED 11 + setup ERROR 4)와 stick 2(s071, s125)다. s003·s043·s125는 **메시지 내용**을 단언하므로(`_COMPENSATION_REGISTRY`, 그룹 이름, 인자 지목) 선언을 반드시 더해야 한다. "대문자 레일 이름 각 1회" 문장은 `tests/probe_physical_consistency.py:40`의 probe 레일 집합이다. 이 probe는 library 파일만 읽으니 B26-1 영향은 없고 B26-4 lint 대상 후보다.
- **M2** `_TEMPLATE.topology.json`: base `AttributeError` → 병합본 `ValueError(supply_nets)`로 예외 종류가 바뀐다. E-LIB 대상 밖이라 판정 영향은 없다. 그러나 이제 필수인 `supply_nets`가 작성 틀에 없다. 틀에 필드를 더하는 것은 오케스트레이터 몫이다(`library/*.topology.json` = 승인 기록 조건). 백로그로 적어 둘 것.
- **M3** 계약 2의 연결 파일: 연결 파일의 `supply_nets`가 list가 아니거나 원소가 틀린 경우의 동작이 정해져 있지 않다. 그 검사에 `rail_declaration`을 쓰면 계약 3의 "정확히 한 번"과 부딪힌다. "연결 파일 선언은 같은 형식 검사를 거친다, 호출 수 불변식은 진입 파일 기준"처럼 한 줄로 정할 것.
- **M4** oracle (b)의 V4: `test_lint.py` (1)은 **인자 정규형이 같은** 피검 호출이 양쪽에 있을 때만 FAIL이다. 원본 경로와 이름 바꾼 경로를 다른 인자 식으로 쓰면 lint를 통과하고, 판단은 auditor `checks.V4.basis`로 간다. interface card에 `_build_theta_evaluator` setup 반환 키(`stack_groups_kcl`·`stack_groups_geometry`)와 "evaluate 호출 금지"를 적어 둘 것.
- **M5** probe 4개는 `rails=meta["rails"]`로 쉽게 고칠 수 있다(모두 meta 보유). `engine_dup_scan` 면제 키는 `path::rule`이라 줄이 바뀌어도 무관하다. 계약 test `test_probe_dup_scan.py:213`의 문자열 조각(`sr.true_current_mirror_groups(by)`)은 스캔 입력 문자열이지 호출이 아니다. 조정할 필요는 없지만 test-author에게 알려 둘 것.
- **M6** 정정안의 해시 주장: `plan_tables_hash` 입력은 N4.1 `ID/담당 Phase/강제 test`, N4.2 `도입`, N6.1 `Phase` 열, 쓰기 경로표다(merge_gate `plan_tables_object`). 정정안이 고치는 칸(N2 DEC-60·69 글, GB0·W0, N3.16, MG1 행, DF 표, N6.1 `범위` 칸, 공격 13, N6.2, U-26)은 이 입력 밖이다. §8의 전후 해시 비교로 충분하다. 단 DF-19 비고 새 글에 `|`가 들어가면 표가 깨지므로 넣지 말 것. 현재 초안 글에는 없다.

---

## 5. 질문별 답

1. **사실 재측정**: §1 표. 틀린 것은 픽스처 4→3(3988), '대문자 레일=픽스처', netclass '극성 판정' 세 문장이다. 11/16·20·49/2/4·15·E-LIB·수치는 일치한다.
2. **red 재현**: 합성 4소자·oracle (b) 모두 base red / 병합 상당 green이 재현됐다. 새 키워드 인자 직접 호출이 base TypeError(red 아님)라는 초안의 주의는 맞다. 계약 7의 각 항목에 시그니처가 안 바뀐 진입점이 있음을 확인했다(S4 표). 역방향만 meta 수준에서는 안 된다(B2).
3. **집합/극성 분리**: 줄 단위로는 깨끗하다. 16줄 모두 소속 판정이고, 씨앗은 레일→자기 자신이라 극성과 무관하다. netclass `RAILS_POS/NEG`에 기대는 B26-1 사이트는 없다. 다만 바뀌는 함수 중 `propose_device_roles_gap_fill`·`refine_…`·`find_differential_pair_candidates`는 **같은 함수 안에서** netclass 이름 판정과 `trace_*` 극성 판정을 함께 쓴다. 그래서 함수 **출력**은 여전히 이름에 기댄다. 계약은 B26-1 사이트만으로 정해지는 출력에 걸어야 한다(B2·S4).
4. **V3**: 초안이 옮긴 3곳 말고도 바뀌는 def 약 32개의 본문 전체(약 2,465 변이)가 대상이다. `_metric_kcl_residual`은 인벤토리가 0이다. 계획이 없으면 FAIL/ERROR다(B1).
5. **계획 정정안**: 판정 표(해시 입력)는 바꾸지 않는다(M6). DEC-60 종료와 앞당김은 '알림'이 아니라 decision 승인 기록 한 건으로 받는 것을 권고한다(S3). 앞당김은 순서 변경이지만 N6.1 `Phase` 열은 그대로다. 해시 승인(plan_tables)은 필요 없고, 결정 승인(decision)이 필요하다.
6. **netclass**: `skills/analog-grammar/**`는 쓰기 경로표에 어느 주체 행도 없다. 경로표를 고치면 plan_tables 해시가 바뀌고 사용자 승인이 필요하다. 권고는 파일을 건드리지 않고 SD 호출부 어댑터(code-author 경로)로 B26-2에서 처리하는 것이다. 어댑터는 극성(D1)이 있어야 한다(S2).

---

## 6. 사용자 결정 목록(진짜 사용자 몫만)

- **U1 (B1)**: B26-1의 V3 처리. (a) 이 card의 V3 대상을 diff가 닿은 문장과 새 def로 좁히고 나머지 변이를 id 목록으로 면제하는 decision 승인, (b) card 재분할, (c) 전수 실행과 test 보강 중 하나. 게이트 판정 범위를 좁히는 일이라 사용자 몫이다.
- **U2 (S3)**: DEC-60 넷 전환기 종료 + DF-19·DF-26 넷 몫을 MG1에서 분리 + B26-1을 Phase 3 전(Phase 2 진행 중)에 착수. 한 건의 decision 승인으로 받는다.
- (참고, 이미 B26-2·B26-3 착수 조건) D1 극성 규칙, D2 MNA 교류접지. netclass 어댑터는 D1에 딸려 간다. analog-grammar 경로표 개정을 택할 때만 별도 사용자 승인(plan_tables)이 필요하다.

결정이 아닌 것(원칙으로 처리): S1·S2·S4·S5·M1~M6 문구 정정, 계약 7 관찰 대상 한정(B2), `_metric_kcl_residual` 직접 참조 test(B1-3).
