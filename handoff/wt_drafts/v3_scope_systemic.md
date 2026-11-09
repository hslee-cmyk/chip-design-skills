# V3 대상 범위 -- B28 뒤 모든 엔진 card에 걸리는 구조 문제

측정 2026-09-30, gate `master` cd64170. 저장소·worktree 쓰기 없음. scratch C:/g39(`git archive cd64170` 전체 사본, 끝나면 삭제). 도구 `tools/gates/mutate_changed.py`의
`changed_defs`·`mutants`·`inventory`와 `reachability.build_graph`·`_approved_ids`만 읽기 전용으로 import했다(도구 `main`은 돌리지 않음). 스크립트·출력: `b26_v3_measure.py`,
`b26_v3_leak.py`, `b26_v3_measure.out.txt`(이 폴더).

## 1. 무엇이 문제인가

V3는 **AST가 바뀐 def의 본문 전체**를 변이한다(대상 단위 = def, 연산자는 그 def의 모든 노드 -- 중첩 def 포함). 엔진 함수는 수백~천 줄이라 한두 줄을 고친 card도 그 함수의 기존 문장
전부를 판정 대상으로 끌어온다. B28(`20260930-v3-history-clone`)이 병합되면 도구가 격리 복제본에서 실제로 돌고 기준 실행 실패는 `ERROR`가 되므로, P8·DF-36처럼 "도구가 못 돌아 auditor가
사이트만 대체 측정"하는 경로가 없어진다. 이제 기존 문장의 생존 변이는 그대로 V3 FAIL이다.

공통 측정값: 사본 전체 test 1회 813건 272 s. 정적 인벤토리는 과대 근사라 엔진 def 하나의 인벤토리가 60~159개 test이고 실행 시간 177~192 s다(느린 test 몇 개 --
`test_probe_parasitic_pm_all_circuits` 55 s, `test_s157_M1_known_limitation` 43 s, `test_s157_M1` 24 s, `test_s014_section` 17 s -- 가 거의 모든 인벤토리에 든다). pytest 기동 4.7~7.1 s/회,
도구는 직렬. 아래 '하한' = 변이마다 기동 ~5 s만(전부 첫 test에서 죽음), '상한' = Σ 변이 × 인벤토리 시간(전부 생존).

## 2. card별 측정

| card | 대상 def | 변이(본문 전체) | diff가 닿은 변이 | 인벤토리(test 수) | 하한 | 상한 |
|---|---|---|---|---|---|---|
| **B26-1**(시뮬레이션 head = cd64170 + B26-1 상당 패치) | 31(최상위 30 + 중첩 1) | **2,472** | 106 | 0~146(`_metric_kcl_residual` 0) | ≈3.4 h | ≈122 h(≈5.1일) |
| **P9**(`kcl_series_union` 본문 엣지 정의 → `_kcl_and_matching_edges` 호출, 시뮬레이션 head) | 1 | **24** | 2 | 70(179 s) | ≈2분 | ≈1.2 h |
| **B34**(analog-grammar 조용한 폴백 제거) -- 직접 폴백 def(`_import_analog_grammar` + prep §1.2 표 1~12의 11함수) | 12 | **1,130**(base 본문) | 미측정 | 4~159 | ≈1.6 h | ≈42 h |
| B34 -- 전파 폴백 def(`find_differential_pair_candidates`, `_propose_gm_id_roles`, `_propose_L_roles`, `propose_vertical_stack_id_gap_fill`, `geometry_colocation_union`, `load_topology`) | 6 | **265**(base 본문) | 미측정 | 64~146 | ≈22분 | ≈14 h |

* B26-1 큰 def: `_build_theta_evaluator` 498(닿은 변이 3), `propose_device_roles_gap_fill` 331(17), `optimize_full_circuit_budget` 230(2), `repair_matching_safety` 112(3),
  `_branch_composite_pair` 102(1). `_metric_kcl_residual` 57은 인벤토리 0(`compute_metric` → `_METRICS_REGISTRY` dict 경유라 정적 간선이 없다) -- 이름으로 부르는 test 하나로 1이 된다.
* P9는 작다(def 1개, 46줄). 기존 규칙으로 감당할 수 있다.
* B34 큰 def: `propose_device_roles_gap_fill` 331, `propose_theta_kcl_gap_fill` 242(인벤토리 **5**, 0.2 s), `_propose_vertical_stack_ids` 141, `refine_…` 95,
  `suggest_vertical_stack_composites` 79. `propose_theta_kcl_gap_fill`(242/5)·`find_differential_and_mirror_forks`(50/10)·`audit_theta_root_direction`(36/4)·`find_idiom_matches`(11/15)는 운영 미도달
  함수라 인벤토리가 작아 생존 변이가 많을 가능성이 높다(미실행 -- 추정이 아니라 인벤토리 크기 사실만 적는다). B34의 '닿은 변이'는 B34 패치를 시뮬레이션하지 않아 재지 않았다.
* 같은 def가 여러 card에 걸린다: `propose_device_roles_gap_fill`·`refine_…`·`find_differential_pair_candidates`·`_propose_*`·`load_topology`는 B26-1·B34에 모두 있고 B26-2·B35도 다시 바꾼다.
  card마다 그 def 본문 전체가 다시 변이된다.
* 참고(2026-10-01 정정, 검토 review_v3_cards S8): 계획서 533행 이동 규칙("해시가 같은 함수는 V3 대상에서 뺀다")은 **지금 도구에 구현돼 있지 않다** -- `mutate_changed.main`은 같은 경로의
  base만 비교하고 새 파일이면 그 파일의 def가 전부 대상이 된다(359~364행). 구현은 Phase 3 G1 card(`draft_p3_g1.spec.md`)의 몫이고, G1 병합 전 이동 card는 이 문제를 그대로 겪는다
  (`draft_p3_g1.spec.v3.md` 11~14행: 엔진 4파일 상한 V3 대상 def 473·변이 15,677). 옛 문장 "Phase 3 이동 card는 계획 규칙으로 이 문제가 없다"는 거짓이었다(원문 `v3_scope_systemic.v1.md`).

## 3. 면제 기록의 누수(정책과 별개인 결함)

지금 규칙에서 기존 문장의 생존 변이를 넘기는 길은 변이 id 목록 면제(`target_kind: decision`)뿐이다. 그런데:
* 변이 id = `<모듈>:<qualname>:<연산자>:<AST 노드 경로>`이고 def 해시·card id에 묶이지 않는다.
* 도구는 head 트리의 **모든** decision 승인 기록의 `target` 원소를 면제 집합으로 읽는다(`reachability._approved_ids`, `mutate_changed.main` ⑤).
* 그래서 한 card의 면제 목록은 **뒤 card에서 같은 경로의 변이를 조용히 면제한다** -- 경로에 다른 문장이 와 있어도 그렇다. 실측: B26-1 시뮬레이션 head에서 '닿지 않은 변이' 2,366개를
  면제 목록으로 만들면, 그 head 위에서 B34 대상 def를 변이할 때 1,402개 중 **619개**의 id가 이미 목록에 있다(`refine_…` 90/95, `propose_device_roles_gap_fill` 314/331,
  `find_differential_pair_candidates` 61/65, `load_topology` 56/65 등. B34 자신의 편집으로 경로가 밀리는 몫은 빠지므로 상한).
* 선례 `20260922-ic3-v3-exempt`(C8, `load_topology` body[11]·body[26] 경로 10개 + `save_instance_json` 4개)가 지금 트리에 있고, 범위 설명에 "본문 구조가 바뀌면 이 면제는 맞지 않는다"고
  적었지만 도구는 경로만 본다. cd64170에서 그 14개 경로는 모두 존재하고 범위 설명에 적힌 문장(연결 파일 메타 합치기, device_roles 자동 쌍 중복 제거, `scope_note` 복사, `indent=2`)을 가리킨다(실측 14/14). B26-1이 `load_topology` 앞쪽에 문장을 넣지 않고 뒤쪽만 바꾸면
  이 10개는 B26-1 V3에서도 조용히 면제된다.
* 이것은 '조용한 면제 금지'·'게이트는 실제로 거부하는가'(WP-02) 쪽 결함이다. 범위를 좁히든 안 좁히든 고칠 대상이다.

## 4. 게이트 정책을 바꾸면 약화인가 -- 원문 대조

design `05-role-separation` §10 V3 행(317행, B28 ④ 개정 반영본):
> ① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것(새 def 포함) ② 연산자: 비교 뒤집기, 산술 교체(`+↔-`, `*↔/`), 상수 변경(정수 ±1, 실수는 표기된 마지막 자릿수
> 한 단위 ±), 문장 삭제, 조기 `return`, `except` 본문 삭제 ③ 인벤토리 = 정적 호출 그래프(V7과 같은 그래프)에서 그 함수에 도달하는 test 함수(계획 N4.2 V3 v5.19) … ⑤ 살아남은 변이가
> 있으면 FAIL. 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`. 등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록.

계획 N4.2 V3 행(839행):
> 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것. 연산자 = 비교 뒤집기 / 산술 교체 / 상수 변경(정수는 ±1, 실수는 표기된 마지막 자릿수 한 단위 ±) / 문장 삭제 / 조기 return / except 본문 삭제.
> 변이마다 정적 호출 그래프에서 그 함수에 도달하는 test만 실행(인벤토리). 살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만.

판단:
* **V3 대상을 'diff가 닿은 문장 + 새 def'로 좁히는 것은 약화다.** 원문은 대상 단위를 **def**로 정하고("diff가 닿은 def 중 AST 해시가 바뀐 것") 그 def의 변이가 하나라도 살면 FAIL이다.
  좁히면 지금 규칙이 죽이라고 요구하는 변이(B26-1에서 2,366개)가 판정에서 빠지고, 게이트가 거부하는 경우의 집합이 줄어든다. N0.4 '기준 약화' 8패턴(V5, test diff 대상)의 문자 그대로에는
  들지 않지만, 판정 기준의 적용 범위를 줄이는 게이트 변경이다. B28 승인 기록은 "기준 약화가 아니다(기준 실행 실패는 지금 FAIL, 이후 ERROR -- 둘 다 거부)"라는 근거로 받았는데, 이 변경은
  그 근거를 댈 수 없다. **약화로 다루고 사용자 승인을 받는다**(DEC-40 취지 -- 약화는 매 건 사용자 승인).
* 약화를 받을 근거(사용자 판단 재료): V3의 목적은 "test의 독립성을 결과로 검사"(DEC-38)하는 것이다 -- **이 변경을 위해 쓴 test가 이 변경의 코드를 실제로 판정하는가**. 닿지 않은 기존 문장의
  생존 변이는 그 card의 test가 아니라 **기존 test 공백**(C8 때 백로그 B8로 남긴 것과 같은 종류)을 잰다. def 단위 규칙은 이 공백을 엔진 card마다 그 card의 병합 조건으로 만든다(B26-1 2,472,
  B34 1,395). 좁히되 잃는 정보를 조용히 버리지 않으려면, 좁힌 밖의 변이 수를 도구 출력에 `not_targeted`로 싣고(판정에는 안 씀) 기존 test 공백 백로그로 넘긴다.
* **약화가 아닌 변경**(같은 게이트 card에 넣을 수 있다):
  1. 면제 id를 def 해시(`def_hash`)와 card id에 묶는다 -- §3 누수를 막는다. 거부 집합이 넓어지는 쪽이라 강화다.
  2. 인벤토리를 빠른 test부터 돌린다(`-x`이므로 죽는 변이의 비용이 준다). 판정은 같다. 병렬 실행도 판정을 바꾸지 않는다.

## 5. 필요한 승인

* 게이트 변경 spec card 한 장(`gate_change: yes`, `phase: 0.5` -- B28과 같은 모양, 판정 유형 red-green, redteam `v3_survivor`가 계속 거부하고 새 사례 둘을 더한다: (i) 닿은 문장의 생존 변이 → FAIL,
  (ii) 다른 card의 면제 id가 해시가 다른 def에 걸리지 않음). 쓰기: `tools/gates/mutate_changed.py`(·`reachability._approved_ids` 소비부) = code-author(설계 10 C11 행 "spec card `gate_change: yes`
  + 승인 기록일 때"), redteam = test-author(C10 행).
* 사용자 승인 기록: `target_kind: diff` 한 건 -- 그 spec card + design 05 §10 V3 행 ①·⑤ 개정 + 계획 N4.2 V3 행 문구 개정(B28 `20260930-v3-history-clone`과 같은 형식). 범위 축소(4의 첫 항)는
  **약화 승인**임을 범위 설명에 적는다. N4.2의 V3 알고리즘 칸은 `plan_tables_hash` 입력(N4.2는 `도입` 열만)이 아니므로 `plan_tables` 승인은 필요 없다. 약화 없이 4의 '약화가 아닌 변경'만 하는
  경우에도 게이트 변경이므로 같은 형식의 승인이 필요하다(판정 기준 소유 = 사용자, design 05 §2 V3~V7 행).
* 선후: 이 게이트 card는 B28 병합 뒤, B26-1 착수 전. B26-1 card 'V3 계획' 3의 권고가 이것이다. 사용자가 범위 축소를 받지 않으면 면제 누수 수정(강화)만이라도 먼저 하고, B26-1은 전수 실행
  (c)로 간다 -- 그 경우 B26-1 V3 실행은 하한 ≈3.4 h, 상한 ≈122 h이고 생존 변이의 test 보강이 이 card 범위 밖 기존 동작까지 번진다.
