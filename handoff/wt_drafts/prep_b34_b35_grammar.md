# B34·B35 준비 자료 -- `skills/analog-grammar` 의존 (조용한 폴백 + 이름 집합 레일)

측정 시점: gate `master` = `cd64170`(2026-09-30). 저장소·worktree 쓰기 없음. scratch `C:/g33`(끝나고 삭제함):
`git archive HEAD skills/analog-gmid-design/assets skills/analog-grammar workspaces/run_harness.py tools/gates docs/01-plan`로 만든 사본 3벌
-- `full`(원본), `nog`(analog-grammar를 뺀 사본), `pol`(analog-grammar 극성 제거 변이, §3.3 실측용).
A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`, AG = `skills/analog-grammar/assets`. 줄 번호는 cd64170 기준이다.

---

## 요약

* **B34 재현됨.** analog-grammar가 없으면 `current_reuse_telescopic_ota` θ\*(`tests/canonical_theta_star.json`) 평가가 성공하던 것이 `ValueError`로 바뀐다(vertical_stack_id 그룹 `biasgen_vop_a` / `biasgen_vop_floatsrc_sink` 순환). 이 밖에도 알려지지 않았던 차이가 있다.
  * `load_topology` meta가 **9/9 회로**에서 달라진다.
  * `_device_roles_gap_fill_review_needed`가 9회로 모두 **0건**이 된다. 원본에서는 28·4·5·12·1·1·9·2건이었다.
  * 자동 채움 `device_roles`와 `_matching_pairs_*`가 사라진다. 그 결과 **review 게이트 `require_device_roles_reviewed`(SR 7952)가 검사할 재료를 잃고 아무것도 막지 않는 상태가 된다.**
* **실제로 일어나는 경로가 있다.** `install.py` 29행 `SKILLS`에 `analog-gmid-design`은 있고 `analog-grammar`는 없다. 설치본(`~/.claude/skills/analog-gmid-design`)은 `../../analog-grammar/assets`가 없어서 늘 B34 폴백으로 돈다.
* **B35 사용처 목록:** SD에서 analog-grammar를 쓰는 함수는 12개다. 그중 운영 경로(V7 `before_phase3` 루트에서 도달)가 8개다. 옛 '11(운영 7)'은 직접 import한 것만 센 값이고, `geometry_colocation_union`이 `find_stack_edges`를 거쳐 더해진다. 이 12함수가 부르는 AG 함수 12개가 전부 `RAILS`·`RAILS_POS`·`RAILS_NEG`를 쓴다.
* **9회로에서 바꿔도 동작은 같다.** 9회로 전부 `RAILS ∩ 트랜지스터 넷` = `supply_nets ∩ 트랜지스터 넷`이다(실측). 따라서 레일 판정을 선언으로 바꿔도 library 결과는 그대로다.
* **SD 운영 경로는 극성을 쓰지 않는다(실측).** analog-grammar의 극성(`POS`/`NEG`)을 없앤 변이에서도 `load_topology` 9/9와 SPECS 4회로 평가가 원본과 같았다. 바뀐 것은 운영 경로 밖인 `find_idiom_matches` 원본 출력 5회로뿐이다(`push-pull-output` 소실).
* **게이트 공백.** analog-grammar는 N3.12.2 쓰기 경로표의 어떤 행에도 맞지 않는다. 그래서 오케스트레이터 규칙상 hook이 **즉시 통과**시키고, EL3/EL4 5분류에서도 '역할 밖'이 된다. V3·V7·source_lint·interface_card가 보는 범위에도 들지 않는다. 엔진 판정을 바꾸는 코드가 trailer·test·audit 없이 수정될 수 있다는 뜻이다. 마지막 수정은 `3250baa`(2026-09-03, 게이트 기준 커밋 `ece1bf3` 이전)이다.
* **권고.**
  * B34: 독립 소형 card. 명시적 오류로 바꾼다(red-green). B26과 무관하게 지금 할 수 있다.
  * B35: analog-grammar에 명시 레일 인자를 넣고, SD는 B26-1 `meta["rails"]`를 그 인자로 넘긴다. 착수 조건은 두 가지다.
    * 게이트 변경 card: analog-grammar를 쓰기 경로표와 게이트 범위에 넣는다.
    * B26-2(D1)가 먼저 끝나야 한다. 극성까지 한 번에 넣기 위해서다.
  * 호출부 번역(analog-grammar를 고치지 않는 방법)은 기각한다(§3.2).

---

## 1. B34 -- import와 폴백

### 1.1 import 코드

* SD 1025~1031행 주석: "analog-grammar가 sys.path에 없으면 … 조용히 None을 반환한다 -- 호출자는 None이면 … 기존 동작으로 폴백해야 한다". 설계 의도로 적혀 있다.
* SD 1045~1058행 `_import_analog_grammar(*module_names)`의 동작 순서:
  1. `os.path.dirname(__file__)/../../analog-grammar/assets`를 `sys.path` 맨 앞에 넣는다. 이미 있으면 다시 넣지 않는다.
  2. `importlib.import_module(name)`으로 bare 이름 `netclass`·`idioms`를 import한다.
  3. `ImportError`가 나면 모듈 수만큼 `None`을 담은 튜플을 돌려준다.
  4. `ImportError`가 아닌 예외는 그대로 올린다.
* SD 1035~1042행 `_to_analog_grammar_devs`: gate가 없는 소자를 뺀다. 결과가 `[]`이면 어댑터들이 `None`을 돌려준다. 즉 **'설치 안 됨'과 '입력에 gate 소자 없음'이 같은 `None`으로 섞인다.**
* 레지스트리 179·180·360·505행: 이관 목적지는 `topology_authoring`(MOD2)이다. 360행 비고는 "R1(sys.path 부작용을 패키지 import로)".

### 1.2 폴백 사이트 전수 (analog-grammar 부재 시)

직접 폴백(`_import_analog_grammar`가 준 None을 검사하는 곳):

| # | SD 함수 | 줄 | 부재 시 동작 | 운영 도달 |
|---|---|---|---|---|
| 1 | `find_idiom_matches` | 1072~1074 | `None` | 아니오 |
| 2 | `find_stack_edges` | 1088~1090 | `None` | 예 |
| 3 | `find_differential_and_mirror_forks` | 1312~1314 | `None` | 아니오 |
| 4 | `suggest_vertical_stack_composites` | 1444~1446 | `None` | 예 |
| 5 | `find_verified_differential_and_mirror_relations` | 1713~1715 | `None` | 예 |
| 6 | `_propose_vertical_stack_ids` | 1893~1895 | `None` | 예 |
| 7 | `_propose_headroom_roles` | 2258~2260 | `None` | 예 |
| 8 | `refine_differential_and_mirror_relations` | 2399~2401(내부 함수가 `(None, None)`을 준다) → 2410 `None` | `None` | 예 |
| 9 | 같은 함수 | 2494~2495 `if _netclass_al is not None:` | active-load·signal-mirror·branch-load 후보를 **빈 채로** 진행한다 | 예 |
| 10 | `audit_theta_root_direction` | 3380~3382 | `[]`. docstring이 "검사 못 한 것과 문제없음이 구분되지 않는다"고 스스로 적어 두었다 | 아니오 |
| 11 | `propose_theta_kcl_gap_fill` | 3528~3531 | `unavailable_reason`을 담은 빈 dict | 아니오 |
| 12 | `propose_device_roles_gap_fill` | 4070~4073(`_static_ref_roles = ()`), 4087 `if _idioms_lcmf is not None:` 블록 건너뜀 | 정적 레퍼런스 집합이 빈 채로 진행한다 | 예 |

전파 폴백(위의 None을 받아서 다시 None을 내거나 조용히 건너뛰는 곳):

| SD 함수 | 줄 | 동작 |
|---|---|---|
| `find_differential_pair_candidates` | 1543 | `None` |
| `_propose_gm_id_roles` | 2092 | `None` |
| `_propose_L_roles` | 2165·2169 | `None` |
| `refine_differential_and_mirror_relations` | 2420·2440 | `None` |
| `propose_device_roles_gap_fill` | 3966~3970 | `unavailable_reason`을 담은 빈 제안 |
| `propose_vertical_stack_id_gap_fill` | 3296 `if relations is not None:` | 차동 다리 검사를 건너뜀. docstring 3282행 "조용히 건너뛴다" |
| `geometry_colocation_union` | 3115~3116 `if stack_edges:` | 적층 상속 확장을 건너뜀. docstring 3085행 "soft-fail" |
| `load_topology` | 8668~8737 | `unavailable_reason`을 **읽는 소비처가 0곳**(grep)이다. 자동 채움·review 목록이 `None`으로 meta에 실린다 |
| SR `_build_theta_evaluator` | 7952 `require_device_roles_reviewed(topology_path, meta)` | 이 게이트가 보는 `_device_roles_autofilled`·`_matching_pairs_needs_review`(SD 4688·4729)가 비어 있어 **막을 대상이 없다** |

### 1.3 재현 (scratch `C:/g33`, `repro.py` -- 케이스마다 JSONL append)

환경 확인:

| 사본 | analog-grammar 디렉터리 | `_import_analog_grammar("netclass","idioms")` 결과 |
|---|---|---|
| `full` | 있음 | `[True, True]` |
| `nog` | 없음 | `[False, False]` |

**(a) SPECS 4회로 θ 평가** (`tests/unit/_library_sized_contexts._evaluate_once`, θ = `_theta_point` 규칙):

| 회로 | full | nog |
|---|---|---|
| current_reuse_telescopic_ota | 성공 | **`ValueError`**: "vertical_stack_id 그룹 ['biasgen_vop_a', 'biasgen_vop_floatsrc_sink']가 서로 의존관계를 완결할 수 없다 … 'biasgen_vop_a'의 budget_reference_device('M19')가 아직 VDS 미확정 … 'biasgen_vop_floatsrc_sink'의 budget_reference_device('M17')가 아직 VDS 미확정". 발생 위치 SR 8643 `_evaluate` |
| folded_cascode | 성공 | 같음(metric·sized 해시 동일) |
| two_stage_ota | `InfeasibleSizingError`('stage1_ref') | 같음 |
| nmcnr_amplifier | `InfeasibleSizingError`('stage2_diode_ref') | 같음 |

원인 사슬(meta 차이에서 읽은 것): nog에서는 `device_roles`의 `vds_match_vgs_of`(M8→M15, M17→M25, M19→M26)가 채워지지 않는다. `budget_reference_device`(M37a→M36a, M37b→M36b, M63→M5)와 `fold_group` 4개도 채워지지 않는다. 그래서 두 vsid 그룹이 서로의 VDS를 기다리는 순환이 남는다.

**(b) `load_topology` meta, library 9회로** (`_TEMPLATE` 제외):

| 회로 | 달라지는 meta 키 | 요지 |
|---|---|---|
| common_gate_amplifier | `device_roles`, `_device_roles_autofilled` | headroom_role 3개·gm_id_role 1개 사라짐 |
| current_reuse_telescopic_ota | + `_device_roles_gap_fill_review_needed` | vds_match_vgs_of 3개, fold_group 4개, budget_reference_device 3개 사라짐. review 28 → 0 |
| folded_cascode | `_device_roles_gap_fill_review_needed` | review 4 → 0 |
| ngcc_3stage_ff | + `_matching_pairs_autofilled`·`_needs_review`·`symmetry` | L_role 3·gm_id_role 10·headroom_role 11 사라짐. 자동 matching_pair (M1, M2) 사라짐. review 5 → 0 |
| nmcnr_amplifier | review 목록 | 12 → 0 |
| pushpull_follower_buffer | device_roles·review | headroom_role 2 사라짐. review 1 → 0 |
| sf_pushpull_output_opamp | + matching·symmetry | L_role 3·gm_id_role 3·headroom_role 22 사라짐. review 1 → 0 |
| two_stage_ota | device_roles·review | budget_reference_device 1·gm_id_role 2 사라짐. review 9 → 0 |
| two_stage_ota_sf | + matching·symmetry | L_role 3·gm_id_role 5·headroom_role 9 사라짐. review 2 → 0 |

`transistors`는 9/9 같다. `run_full_circuit_audit_from_topology`도 9/9 결과가 같다. 2회로는 같은 결과이고 7회로는 같은 `ValueError`(`_netlist_sections_structured` 없음)이며, 차이는 경로 문자열뿐이다.

**(c) 어댑터:** `find_stack_edges`·`find_idiom_matches`는 9/9에서 값 → `None`이 된다.

### 1.4 동작 차이 정리

1. **사이징 결과가 바뀐다.** current_reuse θ\*가 성공에서 `ValueError`로 바뀐다. 다른 회로는 지금은 결과가 같지만, device_roles가 바뀐 상태로 평가되므로 θ 탐색 공간이 달라진다.
2. **안전 게이트가 무력화된다.** review 목록과 자동 채움 목록이 비므로 `require_device_roles_reviewed`가 아무것도 막지 않는다. "검사 통과"와 "검사 못 함"이 구분되지 않는다.
3. **matching·symmetry가 바뀐다.** 자동 matching_pair가 사라진다(3회로). 이는 L 전파(SR의 matching_pairs 루프)와 geometry 그룹(`geometry_colocation_union` 확장 생략)을 바꾼다.
4. **진단 신호가 섞인다.** `None`이 '설치 안 됨'과 'gate 소자 없음'을 함께 뜻한다(§1.1). `unavailable_reason`은 만들어 놓고 아무도 읽지 않는다(만들고 배선하지 않은 상태).
5. **test만이 잡는다.** `tests/unit/test_selftest_stick_diagram.py::test_s115_section`(2617~2626행)은 `find_idiom_matches(...) is not None`을 단언한다. 그래서 판정 실행(pytest_gate)에서는 부재가 FAIL로 드러난다. 운영 실행(run_harness·설치본)에는 이런 검사가 없다.

### 1.5 원칙 대조

* **조용한 폴백 금지**(계획 §3.2 P1, 메모리 '우회/skip 타당성 검토'): 세 질문에 답하면 다음과 같다.
  1. 대상은 실재하는가: 설치본에서 실재한다.
  2. 검사가 틀렸나, 대상이 틀렸나: 폴백 자체가 틀렸다. 결과를 바꾸므로 '보강 기능 없이 기존 동작'이라는 전제가 거짓이다.
  3. 우회 없이 고칠 수 있나: 명시적 의존으로 고칠 수 있다.
* **만들면 배선:** `unavailable_reason`은 소비처가 없다.

---

## 2. stick_diagram이 analog-grammar에서 쓰는 것 (재고)

### 2.1 SD → AG 사용표 (AST, cd64170)

| SD 함수(줄) | 운영 도달 | 쓰는 AG 심볼 |
|---|---|---|
| `find_idiom_matches`(1061) | 아니오 | `netclass.classify_nets`·`assign_roles`, `idioms.match_all` |
| `find_stack_edges`(1083) | 예 | `netclass.stack_edges` |
| `find_differential_and_mirror_forks`(1287) | 아니오 | `classify_nets` |
| `suggest_vertical_stack_composites`(1363) | 예 | `classify_nets`·`assign_roles`·`match_all`·`m_diffpair`, 상수 `CASCODE`·`AMP`·`CTRL_SRC`(idioms 재수출)·`FLOAT_SRC`·`DIODE_CASC` |
| `find_verified_differential_and_mirror_relations`(1625) | 예 | `classify_nets` |
| `_propose_vertical_stack_ids`(1811) | 예 | `classify_nets`·`assign_roles`, `CASCODE`·`FLOAT_SRC`·`DIODE_CASC` |
| `_propose_headroom_roles`(2197) | 예 | `classify_nets`·`assign_roles`·`match_all`, `FLOAT_SRC`·`CURR_SRC`·`ACTIVE_LOAD`·`CASCODE`·`DIODE` |
| `refine_differential_and_mirror_relations`(2317) | 예 | `classify_nets`·`assign_roles`·`match_all`, `ACTIVE_LOAD`·`BIAS`. Match 종류 `current-mirror`·`diffpair-branch-load` |
| `geometry_colocation_union`(3062) | 예 | `find_stack_edges` 경유 |
| `audit_theta_root_direction`(3341) | 아니오 | `find_idiom_matches`, `idioms.propagate_reference_role_through_cascode` |
| `propose_theta_kcl_gap_fill`(3442) | 아니오 | `find_idiom_matches` |
| `propose_device_roles_gap_fill`(3845) | 예 | `classify_nets`·`match_all`·`propagate_reference_role_through_cascode`·`find_cascoded_active_load_legs`, `DIODE`·`CURR_SRC`·`ACTIVE_LOAD`·`CASCODE` |

* 운영 도달 판정은 `tools/gates/reachability.build_graph` + `gate_config.json` `before_phase3` 루트로 했다. 운영 경로에서 이 함수들을 부르는 곳은 `load_topology`, SR `_build_theta_evaluator`·`resolve_stack_layout`·`optimize_full_circuit_budget` 등 49개 노드다.
* SD가 소비하는 Match 종류: `current-mirror`, `differential-pair`, `diffpair-branch-load`, `diode-cascode`, `cascode-stack`(SD 991·993·2267·2268·2513·2520·3547·3555·3573). `push-pull-output`은 소비하지 않는다.
* SD가 읽는 net class 값: `BIAS`와 role 상수뿐이다. `SUPPLY`·`GROUND`는 읽지 않는다.

### 2.2 AG 쪽 레일 이름 집합 사용 (B35)

`AG/netclass.py` 33~35행: `RAILS_POS = {VDD, AVDD, DVDD, VCC, VDDA}`, `RAILS_NEG = {GND, VSS, AGND, DGND, VSSA}`, `RAILS = 둘의 합`. 대소문자는 무시한다(`_CaseInsensitiveNetSet`).

| AG 함수 | 줄 | 종류 |
|---|---|---|
| `netclass.classify_nets` | 102·103(POS→`SUPPLY`, NEG→`GROUND`), 134·137·140·226 | 102·103은 극성, 나머지는 소속 판정 |
| `netclass.is_mutual_loop_partner` | 80·82 | 소속 |
| `netclass._floating_source_legs` | 269·270 | 소속 |
| `netclass.assign_roles` | 314·321 | 소속 |
| `netclass.stack_edges` | 342 | 소속 |
| `idioms.m_diffpair` | 264 | 소속 |
| `idioms.m_cascode` | 373 | 소속 |
| `idioms._walk_single_fanout_top` | 529 | 소속 |
| `idioms.m_diffpair_branch_load` | 572 | 소속 |
| `idioms.m_pushpull` | 599·600·601 | 극성 |
| `idioms.m_telescopic` | 714 | 소속 |
| `sfg.build_sfg` | 29·31·33 | 소속. SD는 쓰지 않고 AG CLI `analyze.py`만 쓴다 |

* 인접 관찰(B35 범위 밖, 백로그 후보): `classify_nets` 1c(116~124행)는 gate 전용 넷을 이름 정규식으로 분류한다(`HINT_INPUT/BIAS/FB/CLK`, 148행 `HINT_OUT`). `load_topology`(SD 8668)는 topology `ports`를 선언해 두고도(9/9 회로가 가짐) `propose_device_roles_gap_fill`에 `inputs`/`outputs`를 넘기지 않는다. 그래서 운영 경로에서 이름 힌트가 켜져 있다. 레일과 같은 종류의 'topology 무관' 위반이다.

### 2.3 저장소 추적·쓰기 주체·게이트

* **추적**: `git ls-files skills/analog-grammar` 11파일이 이 저장소에서 추적된다. 이력 11커밋이고 전부 analog-gmid-design 작업 커밋이다(`d4bd4d9` 반입 ~ `3250baa`). Role trailer는 없고, 전부 게이트 기준 커밋 `ece1bf3` 이전이다.
* **N3.12.2 쓰기 경로표**(계획 591~666행): `skills/analog-grammar/**`에 맞는 행이 **없다**.
  * gmid-code-author는 자기 행만 쓸 수 있으므로 쓰지 못한다. B26-1 초안의 'code-author 쓰기 경로 밖'이 이 뜻이다.
  * 오케스트레이터나 gmid가 아닌 agent는 668행 "위 표의 어떤 행과도 겹치지 않으면 즉시 통과"에 걸린다. 그래서 **trailer·승인 없이 쓸 수 있다.**
  * '판정 트리' 행(665)은 `skills/analog-gmid-design/**`만 덮는다. 그런데 analog-grammar는 판정 실행이 import하는 코드다(SD `sys.path.insert`). 668행이 막으려던 "Python이 import하는 새 파일이 판정 실행을 바꾸는 것"이 트리 밖에서 열려 있다.
* **게이트 도구 범위**: 아래 도구 어디에도 analog-grammar가 없다.
  * `role_paths.py` 61~64행 5분류: 소스 `A/*.py`, test, 도구, 데이터. 문서는 `docs/**` 등이다.
  * `reachability.py` 171~172행 `GRAPH_PREFIXES`/`SOURCE_GLOBS`
  * `mutate_changed.py`(V3)
  * `source_lint.py` 37행
  * `interface_card.py` 27행 `ENGINE_GLOBS`
  * `weakening_diff.py` 251행
  * `pytest_gate.ini` testpaths = gmid tests만

  결과:
  * analog-grammar 수정 커밋은 EL3/EL4에서 '역할 밖'이 되어 통과한다.
  * analog-grammar 변이는 V3에서 측정되지 않는다.
  * V7 그래프는 `importlib` 동적 import라서 SD → AG 간선을 원래 못 본다.
  * analog-grammar 자체 test는 없다. gmid test(`test_selftest_stick_diagram` Test 30 계열 등)가 간접으로 검사할 뿐이다.
* **배포**: `install.py`(사용자 경로) `SKILLS`에 analog-grammar가 없다(§요약). 현재 `~/.claude/skills`에는 둘 다 설치돼 있지 않다.

---

## 3. 원칙과 수정안

### 3.1 B34 -- 명시적 의존 (권고: 필수 의존 + 명시적 오류)

비교:

| 안 | 내용 | 판단 |
|---|---|---|
| (a) 필수 의존, 모듈 최상위 import | `import stick_diagram`만 해도 analog-grammar가 필요해진다 | Phase 3 뒤 MOD7(레이아웃 전용)은 analog-grammar가 필요 없다. 지금 최상위에 두면 MOD 분리 뒤 레이아웃만 쓰는 경로까지 묶인다. 어댑터가 MOD2로 간 뒤라면 MOD2 최상위 import가 맞다 |
| **(b) 필수 의존, 지연 import + 명시적 오류** | `_import_analog_grammar`가 `ImportError`를 삼키지 않는다. 메시지에 찾은 경로와 필요한 skill 이름을 적어 다시 던진다(예외 종류는 `ImportError` 하위형). 모든 `is None` 폴백(§1.2 표 1~12)과 `unavailable_reason` 2곳을 지운다 | **권고.** 지금 바로 가능하고, 옮길 때는 (a)로 자연스럽게 바뀐다 |
| (c) 선언된 선택 의존 + 명시적 오류 | '보강 기능'으로 남기되 부재를 결과에 드러낸다(meta에 `grammar_unavailable`을 싣고 소비처가 거부) | 기각. §1.3이 보여주듯 이 기능은 보강이 아니라 사이징 입력(device_roles·vsid·review 게이트)의 원천이다. 선택 의존으로 둘 근거가 없다 |

B34 card 계약 초안(관찰 가능한 것만):

1. analog-grammar를 import할 수 없으면 아래가 전부 `ImportError`(하위형 포함)를 낸다. 메시지에 `analog-grammar`와 탐색 경로를 적는다.
   * `load_topology(json_path)`: 다른 meta를 만들기 전에 낸다.
   * `find_stack_edges`, `find_idiom_matches`
   * §1.2의 운영 함수 8개와 비운영 4개
2. `None`·`[]`·`unavailable_reason` 반환이 없어진다. `propose_device_roles_gap_fill`·`propose_theta_kcl_gap_fill` 반환에서 `unavailable_reason` 키가 사라진다(소비처 0이라 호출부 변경 없음).
3. **범위 밖:** '입력에 gate 소자 없음 → `None`'(`_to_analog_grammar_devs`가 `[]`인 경우)은 이 card에서 그대로 둔다. test `test_s120_section`이 고정하는 동작이다. 다만 부재와 섞이지 않게 docstring에 뜻을 나눠 적는다.
4. **동작 보존:** analog-grammar가 있으면 E-LIB 9/9(`load_topology`, `run_topology_pipeline`)와 E-INST(파일럿·folded_cascode)가 base와 같다. 이번 실측의 `full` 사본이 base 값이다.

* 판정 유형: **red-green**. test는 파일 시스템을 건드리지 않고 부재를 흉내 낸다: `monkeypatch.setitem(sys.modules, "netclass", None)`(`idioms`도). 이렇게 하면 `importlib.import_module`이 `ImportError`를 낸다.
  * base: 조용히 `None`/meta를 반환 → `pytest.raises` 'DID NOT RAISE' = `Failed` → red
  * 병합본: green
* oracle: 구성 oracle(부재 = 거부). 동작 보존은 base 실행 결과(auditor)로 본다.
* 거부해야 할 입력: 부재. 판정기 자기 점검으로, 조용한 반환을 하는 합성 구현을 넣으면 test가 실패해야 한다(`test_d_delete_telescopic`의 거부 점검과 같은 형태).
* 쓰기 경로:
  * SD: code-author
  * test: test-author(`A/tests/contracts/`)
  * SD 1025~1031행 주석과 docstring(1045·1304·1384·1533·1676·1892·2070·2152·2241·2349·3282·3374·3527·3933행 등의 "analog-grammar가 없으면 None"): code-author
  * `references/analog-grammar-integration.md`의 같은 서술: 오케스트레이터
* 계획서 소비자: 지우는 이름 없음. `unavailable_reason`은 문서 grep으로 확인해야 한다(착수 시 재측정).
* 선후: B26-1과 독립이다. 겹치는 함수(`propose_device_roles_gap_fill`·`refine_…`)가 있어 둘을 동시에 열면 병합 충돌 가능성이 있다. **Phase 3 M2(어댑터를 MOD2로 이동) 전에** 넣는 것이 싸다. 이동은 해시 동일성 증명이므로 먼저 최종형을 만들어 두면 된다.
* 우선순위 판단(메모리 '인프라는 엔진을 막을 때만'): 이것은 인프라가 아니라 엔진의 조용한 폴백이다. 사이징 결과와 review 게이트를 바꾸므로 엔진 결함으로 분류한다.

### 3.2 B35 -- 레일을 `supply_nets` 선언으로

세 안을 비교한다.

**(1) analog-grammar 확장 (권고)**

* 레일 판정을 받는 곳을 analog-grammar의 **진입 인자**로 만든다. 중간 함수가 인자를 줄줄이 넘기지 않아도 되는 구조가 이미 있다: `classify_nets`가 레일에 `imp[n] = RAIL_Z`(226행)와 `cls = SUPPLY/GROUND`를 붙이므로, 그 아래 `assign_roles`·`_floating_source_legs`·`idioms.m_*`(시그니처가 `(devs, cls, imp, role)`로 고정된 REGISTRY)는 `n in RAILS` 대신 `imp.get(n) == RAIL_Z`로 판정할 수 있다.
* 레일 인자가 필요한 곳은 `cls`가 없는 두 곳뿐이다: `classify_nets(…, *, rails)`와 `stack_edges(devs, *, rails)`. `is_mutual_loop_partner(a, b)`는 호출부(`assign_roles`/idioms)가 가진 `imp`를 넘기게 바꾼다.
* 인자에 **기본값을 두지 않는다**(B26-1 원칙 2와 같다). analog-grammar 단독 CLI(`analyze.py`, `run_example.sh`)는 선언이 없는 netlist를 받는 도구다. 거기서는 **CLI 경계에서** 이름 집합을 명시 가정으로 만들어 넘기고, analog-grammar의 기존 방식대로 assumptions에 보고한다. 이름 집합 상수는 CLI 모듈로 옮기고 라이브러리 함수에서는 참조를 0으로 만든다.
* SD 쪽: 어댑터(`_to_analog_grammar_devs` 옆)가 `rails`를 받아 넘긴다. 운영 함수 8개에 기본값 없는 키워드 인자 `rails`를 더한다. 값은 B26-1 `meta["rails"]`에서 온다. B26-1이 이미 `refine_…`·`propose_device_roles_gap_fill`·`resolve_stack_layout`에 `rails`를 넘기도록 계약했으므로 배선이 이어진다. `geometry_colocation_union`은 SR 호출부가 이미 쥔 `meta["rails"]`를 받는다.
* 극성: 102·103행 `SUPPLY`/`GROUND` 라벨과 `m_pushpull`은 극성이 필요하다. 이 몫은 B26-2(D1)의 극성 선언을 받는다.
  * **실측(§3.3): SD 운영 경로는 극성을 소비하지 않는다.**
  * 그래도 analog-grammar 출력(`find_idiom_matches` 원본, CLI)은 극성을 쓴다. 극성 없이 먼저 하면 analog-grammar API를 두 번 바꾸게 된다. 그래서 **B26-2 뒤 한 card로 하는 것이 기본**이다.

**(2) 호출부 번역 (analog-grammar를 고치지 않음) -- 기각**

`_to_analog_grammar_devs`에서 넷 이름을 바꿔치기하는 방법이다. 선언 레일은 analog-grammar 이름 집합의 원소로 바꾸고, 선언에 없는데 이름이 겹치는 넷(`vdd` 같은 내부 넷)은 탈출 이름으로 바꾼다. 문제는 다섯 가지다.

* (i) 극성마다 이름 집합 원소가 5개뿐이다. 서로 다른 레일을 구분해 담을 수 있는 수에 상한이 생긴다. 이 상한 자체가 topology 의존이다.
* (ii) 어느 원소로 바꿀지 고르려면 극성이 필요하다. 극성을 뭉개면 `find_idiom_matches` 원본 출력이 바뀐다(§3.3 실측 5회로).
* (iii) 넷 이름을 키로 쓰는 출력을 **전부** 역변환해야 한다. `cls`·`imp` dict, `stack_edges` 노드, `Match.ports`의 `mid`·`ref`·`lo`·`diode`·`out` 등이다. 입력 힌트 `inputs`/`biases`도 변환해야 한다. 오류가 조용히 날 자리가 많다.
* (iv) SD가 analog-grammar의 이름 집합을 인코딩 통로로 참조하게 된다. B26-4 '운영부 레일 이름 리터럴 0'의 취지(이름으로 레일을 정하지 않는다)를 우회만 하는 셈이다.
* (v) analog-grammar 자체는 여전히 이름 기반이다(일반화 원칙 미충족).

**(3) monkeypatch(모듈 전역 `RAILS` 교체) -- 기각**

전역 상태를 바꾸는 조용한 경로다. 캐시·동시성 문제가 있고, 판정 불가능한 부작용이 생긴다.

**(1)의 착수 조건: 쓰기 경로와 게이트 확장.** 아래를 **게이트 변경 card 하나로** 한다. 계획 판정 표 변경이므로 `target_kind: plan_tables` 승인과 게이트 변경 승인이 필요하다. B28 선례와 같은 모양이다.

1. N3.12.2 행 추가:
   * gmid-code-author: `skills/analog-grammar/assets/*.py`(조건 없음)
   * 오케스트레이터: `skills/analog-grammar/SKILL.md`·`references/**`·`skill-validation-prompt.md`
   * 사용자: `skills/analog-grammar/**`(판정 트리)
2. `role_paths.py` 소스 분류에 `skills/analog-grammar/assets/*.py`를 넣는다. `05-role-separation` 5분류 정의도 함께 고친다.
3. `reachability.py`(그래프 접두어·소스 판정), `mutate_changed.py`(V3 대상), `source_lint.py`, `interface_card.py`(`ENGINE_GLOBS`), `weakening_diff.py`(소스 판정)에 같은 glob을 넣는다. V7은 `importlib` 동적 import를 못 보므로 `_import_analog_grammar`가 부르는 모듈 이름을 간선으로 인식해야 한다. 이는 V7 그래프 한계(Phase 3 design §1 '백로그 후보')와 같은 종류다.
4. analog-grammar test 위치: 별도 testpaths를 만들지 않고 gmid `A/tests/contracts/`(test-author 경로)에 둔다. analog-grammar는 gmid 판정의 입력이므로 그 판정 트리에서 검사한다.

이 게이트 공백은 B35와 무관하게 **B34의 근본 원인과 같은 문제**다. 판정을 바꾸는 코드가 게이트 밖에 있다. 따라서 B35를 미뤄도 이 게이트 card는 따로 백로그에 둘 가치가 있다(가칭 B36 '판정 import 트리 밖 코드').

### 3.3 실측 -- 극성 뭉개기 변이 (`pol` 사본)

`netclass.classify_nets` 1a를 `if n in RAILS: cls[n] = SUPPLY`로 바꿨다(극성 구분 제거). `idioms.m_pushpull`은 `return []`로 바꿨다. 그리고 `repro.py`를 다시 실행했다.

* `load_topology` 9/9 meta·transistors: full과 **같다**.
* SPECS 4회로 평가: **같다**. current_reuse는 metric 전부 `float.hex`까지 같고 sized 해시도 같다. 나머지 3회로는 같은 결과·예외다.
* `find_stack_edges` 9/9: 같다.
* `find_idiom_matches`: 5회로 다르다(current_reuse, ngcc, nmcnr, two_stage_ota, two_stage_ota_sf). `push-pull-output` Match가 사라졌기 때문이고, 운영 경로 밖이다.

결론:
* SD 운영 경로의 레일 의존은 **소속 판정뿐**이다.
* 9회로는 `RAILS ∩ 트랜지스터 넷 = supply_nets ∩ 트랜지스터 넷`이다(9/9 EQUAL). 그래서 (1)의 library 무동작 판정 입력이 성립한다. `agnd`는 두 pushpull 회로에서 커패시터에만 있어 트랜지스터 판정에 무관하다.

### 3.4 B35 card 모양 (B26-2 뒤)

* 판정 유형 **red-green**.
* 합성 topology는 B26-1 oracle (a)의 `rail_hi`/`rail_lo` 선례를 따르고, 선언에 없는 내부 넷 `vdd`를 하나 더 둔다.
  * base:
    * `rail_lo`로 이어진 두 NMOS가 `stack_edges`에 잡힌다.
    * `classify_nets`가 `rail_*`를 레일로 보지 않는다. 그 결과 role·headroom 제안이 바뀐다.
    * 내부 넷 `vdd`를 레일로 본다.
  * 병합본: 선언대로 판정한다.
* **oracle (b) 레일 이름 바꾸기 불변:** `load_topology` meta **전체**. B26-1 초안 114행이 "analog-grammar `RAILS`와 B26-2 사이트 때문에 meta 전체 불변은 계약이 아니다"라고 남긴 빈칸을 B35가 닫는다. 이것이 B35의 대표 관찰이다.
* 동작 보존: E-LIB 9/9, E-INST 2(§3.3 근거).
* 원칙 계약:
  * topology 무관: analog-grammar 라이브러리 함수에 레일 이름 참조 0. B26-4 lint 범위에 `AG/*.py`를 넣는다.
  * 폴백 금지: `rails` 기본값 없음.
  * 재계산 금지: 새 캐시 없음, `meta["rails"]` 재사용. 참고로 `load_topology`마다 `classify_nets`가 여러 번 다시 실행된다(레지스트리 438행 비고 -- 별도 NFR-2 건).
  * 배선: 새 인자 실인자가 전부 `load_topology` meta에서 온다.

---

## 4. 어디에 들어가나

| 항목 | 들어갈 곳 | 선후 |
|---|---|---|
| B34 | 독립 card(Phase 2 진행 중에 앞당김, B26-1과 같은 '원칙 기본안' 앞당김 형식) | Phase 3 M2 전. B26-1과는 파일이 겹치므로 순차로 한다(어느 쪽이 먼저여도 된다) |
| 게이트 공백(가칭 B36) | 게이트 변경 card(B28 형식) + 계획 N3.12.2 개정(plan_tables 승인) | B35 착수 조건. 단독으로도 백로그 |
| B35 | B26 연속 card(B26-2 뒤. 이름은 B26-5 또는 B35 유지). DF-19 비고의 'assets 밖 사이트'(`draft_b26_plan_patch.md` 75행)를 해소하는 card | B26-1(`meta["rails"]`) → B26-2(D1 극성) → 게이트 card → B35. B26-4 lint 범위에 `AG/*.py`를 더하는 것은 B35 병합 뒤 |
| Phase 3 | 레지스트리상 어댑터(`_import_analog_grammar`·`_to_analog_grammar_devs`·`find_stack_edges`·`find_idiom_matches`)와 소비 함수 대부분은 **MOD2 `topology_authoring`**, `geometry_colocation_union`은 MOD7에 남는다(MOD7 → MOD2 import는 계층 규칙상 허용). 레지스트리 360행 R1(sys.path를 패키지 import로)은 동작 변경이라 이동 card(M2)가 아니라 별도 card다 | B34는 M2 전이 싸다. B35가 Phase 3 뒤로 가면 MOD2 파일에서 한다. Phase 3 design 쪽 검토거리(사용자 결정 아님): N3.10 MOD3의 책임이 'S1 구조 유도(개념당 정본)'인데 analog-grammar 기반 role 유도는 MOD2로 배정돼 있다. `_propose_headroom_roles`의 diode 정의(netclass role)와 SR `is_diode_connected`(gate==drain)가 다른 정의인 DUP(레지스트리 434행)도 같은 자리의 문제다 |

---

## 5. 사용자 결정 (원칙으로 정할 수 없는 것만)

1. **analog-grammar의 소속** -- 다음 둘 중 하나다.
   * (a) 별도 skill로 두고 gmid 게이트 범위에 넣는다: §3.2 게이트 card, N3.12.2 개정.
   * (b) analog-gmid-design 안으로 흡수한다(MOD2/MOD3 하위). analog-grammar skill의 단독 사용(`analyze.py` CLI, SKILL.md)을 없애거나 코드를 둘로 두는 것(DUP)을 감수해야 한다.

   skill 경계와 공유 설정은 사용자 몫이다. **기본안은 (a)** 다. 흡수는 DUP나 다른 skill의 기능 삭제를 부른다. 어느 쪽이든 판정 표 개정 승인(`plan_tables`)과 게이트 변경 승인이 필요하다.
2. **`install.py`** (쓰기 주체가 사용자인 경로, EL1이 Claude의 쓰기를 거부함): `SKILLS`에 `"analog-grammar"`를 더하는 편집은 사용자만 할 수 있다. B34 수정 뒤에는 이것이 없으면 설치본이 조용히 틀리는 대신 **명시적으로 실패**한다. 결정이라기보다 사용자 작업 1건이다.

사용자 결정이 **아닌** 것(원칙 기본안): B34 폴백 제거(조용한 폴백 금지), B35 방식((1) analog-grammar 확장, 번역·monkeypatch 기각), analog-grammar CLI 경계로 이름 집합 가정을 옮기는 것, 순서(B34 → B26-1/2 → 게이트 card → B35). 기존 대기 결정 D1(B26-2 극성)은 B35의 선행 조건이지만 새 결정은 아니다.

---

## 부록 -- 명령과 원자료 (scratch 삭제 전 기록)

* 사본: `git archive HEAD <경로들> | tar -x -C C:/g33/{full,nog}`. `nog`는 `skills/analog-grammar`를 뺐다. `pol`은 `full`을 복사한 뒤 §3.3 두 줄을 변이했다.
* `inv.py`: `tools/gates/reachability.build_graph`로 SD·SR·run_harness 그래프를 만들고 `before_phase3` 루트에서 도달을 계산한다. SD 최상위 def마다 `_import_analog_grammar` 반환 별칭의 속성 접근과 어댑터 호출을 수집한다(§2.1). AG 함수별 `RAILS*` 이름 참조 줄을 뽑는다(§2.2).
* `repro.py <루트> <jsonl>`: 순서대로 다음을 한다.
  1. env 기록
  2. library 9회로마다 `load_topology`(transistors·meta 키별 해시), `find_stack_edges`·`find_idiom_matches` 해시, `run_full_circuit_audit_from_topology`
  3. `run_harness.SPECS` 4회로 `_library_sized_contexts._evaluate_once`(metric `float.hex`, sized 해시, 예외 전문)

  케이스마다 append한다.
* `detail.py`: 두 사본의 `load_topology` meta 중 `device_roles`(필드별), `_matching_pairs_*`, `symmetry`, review 목록을 비교한다(§1.3 (b)).
* 레일 동치 확인: library 9회로 netlist 트랜지스터 단자 넷에 대해 `{n | n in netclass.RAILS}` == `supply_nets ∩ 넷` → 9/9 EQUAL.
