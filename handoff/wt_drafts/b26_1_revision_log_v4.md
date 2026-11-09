# B26-1 spec card 개정 기록 -- v3 → v4

대상: `_drafts/draft_b26_1.spec.md`(id `20260930-b26-rail-accessor-set`). 개정 전 사본 `_drafts/draft_b26_1.v3.spec.md`. 입력 검토 `_drafts/review2_b26_1.md`(2차 독립 검토).
함께 고친 파일: `_drafts/draft_b34.spec.md`(사본 `draft_b34.v3.spec.md` -- 인계 사이트 10·14를 B35로), `_drafts/b34_revision_log.md` §7, `_drafts/backlog_additions.md` B35 줄.
새 파일: `_drafts/b26_1_survivor_question.md`(사용자 질문 Q1~Q3), `_drafts/b26_scripts/`(측정 스크립트).
측정: gate `master` HEAD `2d58fd8`(엔진 = `7535799` + P9 `b7765b0`, `766b5c2` 이후 엔진 변경 없음). 저장소 쓰기·상태 변경 git 없음(`git archive`·`git show`만). scratch `C:/g83`, 측정 뒤 삭제.
`$PY` = `C:/Python314/python.exe -B`. 게이트 함수(`mutate_changed.changed_defs`·`mutants`·`_replace_def`·`inventory`·`_get`·`_path_nodes`, `reachability.build_graph`·`iter_defs`, `role_paths.parse_spec_card`)는
읽기 전용 import, `main` 미실행.

## 1. 검토 지적별 처리

| 지적 | 처리 |
|---|---|
| B1 'V3 계획' 낡음 | 절 전체 교체. U1 → 결정됨(A1-a, A1-b + 정정 원문 인용). 옛 (a)(b)(c)·`v3_scope_systemic.md` 권고·619 누수 예시·닿은 변이 수치는 아래 부록(history)으로. 대상 수 재측정(§2) |
| B2 생존 72 | 계약 추가: 7(e) E1(device_roles 세 필드, 입력 12소자·기대 dict), 4에 기본값 고정 E3(+`rails` 키워드 전용·기본값 없음), 14에 `_propose_*` gate 없음 직접 호출 E4, 7(a) 양성 E5. 모두 "V3 필수 -- 생략 불가". 사이트 10·14(+E2b)는 B35로 이동. 남는 생존은 면제 없이 사용자 질문(U3, §3) |
| B3 P9 시그니처 단언 | 계약 12 넷째 항목(새 기대: `rails` 추가, 주석 `RailDeclaration`, 앞 두 매개변수 단언 그대로) + U5 승인 경로(`target_kind: diff`, id 후보 `20260930-b26-p9-signature-update`) + 착수 조건 9 + 승인 필요 목록 ③. '작성 전 실측' 7에 P9 card '함수·시그니처 유지'와 충돌 기록. 재측정: P9 test는 주석 `list`까지 모든 매개변수에 단언한다(review2가 적지 않은 점) -- 새 기대에 반영 |
| S1 계약 13 증거 | 'base `TypeError`, red 집계 밖'으로 정정(계약 13 본문, 판정 유형 근거) |
| S2 7(c) meta | 계약 7(c)에 meta 획득 = 합성 topology tmp 파일의 `load_topology`(`rail_declaration`으로 만들지 않음), 표에도 표시 |
| S3 넷리스트 직접 호출 rails | 계약 12 셋째 항목: 그 넷리스트 단자에 나오는 소문자 `vdd`·`gnd`·`vss`(처음 나온 순서, 중복 없이), 없으면 `[]` |
| S4 착수 조건 | 사용자 순서(P9 → P10 → P10b → V3 binding → V3 scope → B34 → B26-1)와 두 게이트 card id로 착수 조건 10항목 재작성. `v3_scope_systemic.md` 참조 삭제 |
| M1 oracle (b) 메모 위치 | 계약 14 아래에서 'oracle 종류와 출처' 절로 이동 |
| M2 승인 B40 | A2 기록은 이미 커밋(`2d58fd8`)되어 범위 ③에 B40이 없다 -- 짧은 추가 승인 U4(문안 `b26_1_survivor_question.md` Q2, id 후보 `20260930-b26-b40-reason-key`). 받지 않으면 B40을 빼는 대안 명시 |
| M3 2,438 | 실제 P9 기준 2,437 재현(§2). '닿은 변이' 개념은 삭제(history로) |

추가로 고친 것: 판정 기록 네 칸(단언 red / 신규 심볼 red / TypeError 집계 밖 / green 회귀 고정) 표, A2 기록 커밋 사실(`2d58fd8`) 반영, 계약 13 AST 측정 기대(head 2개 = B35로 넘긴 10·14).

## 2. V3 대상 재측정(B1)

스크립트(`_drafts/b26_scripts/`): `mk_b1.py`(모의 base = HEAD archive + B34 코드 변경 `build_b34`), `b26v4_head.py`(모의 head, 모드 `review2` = 인계 9·10·10b·13·14·B40, `v4` = 9·10b·13·B40),
`b26v4_classify.py`(범위 정책 card 구현 기준 `v3_scope_widen.py`의 N2b·N2w + 비교용 deep), `b26v4_variant.py`(이름 규칙 변형). 사이트 줄은 b1에서 내용으로 다시 찾았다(13줄, review2와 같음).

| head | 바뀐 def | 변이 전체 | N2b | **card 규칙(N2w)** | deep | 미실행 줄 대상 | 인벤토리 0 대상 |
|---|---|---|---|---|---|---|---|
| review2 재현 | 32 | 2,437 | **265** | 330 | 443 | 9 | 6 |
| review2 문서 값 | 32 | 2,437 | 265 | own 314 | deep 336 | -- | 6 |
| **v4** | 32 | 2,442 | 235 | **301** | 411 | 9 | 6 |

- N2b 265·변이 2,437은 review2와 정확히 같다. 넓힌 T6은 review2 스크립트(C:/g70, 삭제)와 대조할 수 없다. card 규칙의 '바꾸는 이름'에서 ⓑ·ⓒ를 빼면 317, ⓒ만 빼면 318(`b26v4_variant.py`) --
  review2 own(314)은 이름 규칙이 더 좁았던 것으로 본다. 확정 = card 규칙 값(review2 head 330, v4 head 301). deep은 정의가 달라 비교하지 않는다(참고값).
- 시간(v4, N2w): 하한 25.1분, 상한 15.98 h(인벤토리 시간은 `v3_scripts/out/junit_base.xml` 재사용 -- 엔진 소스 = 7535799+P9, P9 새 test 시간은 0으로 셈).
- 미실행 줄: `v3_scripts/out/executed_lines.json`(7535799 사본 기록)을 head → b1 → 7535799 줄 대응으로 재사용.

## 3. 변이 실행(B2 재현, 방법 = review2 §3 근사)

`b26v4_kill.py v4 12 N2d --contracts-first`, `b26v4_contracts.py 12`. 대응 = (연산자, 정규화한 문장 글, 순번). 실행 = 도구 pytest 인자 + `-x --gmid-phase=2 --gmid-strict=`, `PYTHONHASHSEED=1`,
12 병렬(14:45~16:32, CPU 합 20.9 h; 기계 부하로 죽은 변이 중앙값 176 s, 생존 408 s). 인벤토리 기준 실행 21종 모두 rc 0. 추가 계약 근사(`test_b26x_approx.py`, 5 test)는 변이 없는 b1에서 5/5 통과.
변이마다 계약 근사를 먼저 돌리고(빠름) 살면 기존 인벤토리를 돌렸다 -- 그래서 '기존 인벤토리만의 생존 수'는 재지 않았다(판정과 무관).

| 범위 | 옮긴 변이 | 기존 인벤토리가 죽임 | 계약 근사가 죽임 | 생존 |
|---|---|---|---|---|
| N2b | 198 | 111 | 68 | 19 |
| **N2w(card 규칙)** | **264** | 150 | 87 | **27** |
| deep(참고) | 374 | 219 | 89 | 66 |

- 대응 없는 새 문장 변이 37(새 def 14 + 새 문장 23)은 계획된 계약 1·2·3·5·6·13·14 몫(review2와 같은 판단, card 'V3 계획' 2).
- N2w 생존 27 = `_metric_kcl_residual` 3(이름 직접 호출 test 'V3 계획' 4가 죽임) + **남는 24**: E6 13(LUT 없는 repair 4, euler fixup 3, finger growth 6), E7 5(`run_full_circuit_audit` 루프 2,
  `resolve_stack_layout` 1, `propose_vertical_stack_id_gap_fill` 1, `case_collisions` 1), trace `range(i + 1, …)` 2(const+·arith), **등가 4**(`_propose_L_roles` 중복 가드 2, `open_terminals[0]` const−,
  `range` const−).
- review2 'E6 17 + E7 12 = 29'와 다른 이유: review2는 deep 대상까지 셌다(씨앗 문장 등 -- card 규칙에서 대상 밖). review2가 E1(`[0]` const−)·E4(`_propose_L_roles` 가드 2)로 분류한 3개는 등가다
  (`_propose_gm_id_roles`가 `None`을 돌려주는 경우는 같은 인자의 `find_differential_pair_candidates`가 `None`일 때뿐 -- 두 가드 중 하나를 지워도 다른 하나가 같은 `None`; 앞에서 `len == 1`).
- 계약 근사 1차판에서 7(e)의 `Fx`·`Fy` drain을 `rail_hi`로 두었더니 `Qw`(drain `rail_hi`)와 drain을 공유해 'X.drain이 레일' 판정 삭제 변이(4342)가 살았다. drain을 `rail_lo`로 바꾼 판으로
  다시 돌려 죽음을 확인했고 card 7(e) 입력도 그 판으로 적었다(기대 dict 불변).

## 4. 남은 것(오케스트레이터·사용자)

- 사용자 질문 3건(`b26_1_survivor_question.md`): Q1 U3 생존 24 처리(권고 = 앞선 test-only card + 등가 4개 동작 불변 정리), Q2 U4 B40 추가 승인, Q3 U5 P9 시그니처 단언 갱신.
- Q1 (1)이면 test-only card 초안(약 10~14 test, 300~500줄, 합성 픽스처 4~5종)과 B26-1 code-author 몫의 등가 정리 3줄을 card 계약에 넣는 개정(정리 문장 확정 뒤 대상 수 재측정).
- 승인 기록이 커밋되면 card 머리 `approval` 줄에 id 추가.
- B35 card 준비 자료에 사이트 10·14 인계 반영(`backlog_additions.md` B35 줄에 적음).

## 부록 -- history로 옮긴 옛 'V3 계획'(v3 원문)

### (옛) V3 계획 -- v3 원문 그대로

**사용자 결정 U1 대기**(아래 3의 권고). 결정 전에는 착수하지 않는다(착수 조건 5).

1. **대상(재측정 2026-10-01, B34 → B26-1 순서)**. `tools/gates/mutate_changed.py`의 `changed_defs`·`mutants`·`inventory`와 `reachability.build_graph`·`_approved_ids`만 읽기 전용으로
   import했다(도구 `main`은 돌리지 않음). scratch C:/g59(gate `master` `7535799`의 `git archive`)에서 모의 사본 두 벌을 만들었다.
   * **모의 base `b1`** = `7535799` + P9(`kcl_series_union` 본문을 `_kcl_and_matching_edges` 호출로) + B34 코드 변경(사이트 1·2·3·11·11b. docstring 변경은 AST 해시와 무관해 넣지 않음).
     `changed_defs(7535799+P9, b1)` = B34의 4 def(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`)로 B34 card와 같다.
   * **모의 head** = `b1` + B26-1 상당 패치(계약 4의 20함수에 키워드 전용 `rails`, 그 호출부 전부에 `rails=rails`, 뿌리 8곳에 선언 획득 문장, 사이트 교체 -- P9 뒤 SD 13줄 + SR 2줄, 새 def 2개)
     + **B34 인계 삭제**('의도' 표 9·10·10b·13·14·B40).
   * 스크립트: 옛 `_drafts/b26_v3_measure.py`(cd64170, C:/g39)의 head 생성 함수에 P9·B34·인계 삭제를 내용 기준 치환으로 더했다. 사이트 줄은 `b1`에서 다시 찾았다. 측정 뒤 C:/g59는 지웠다.
     수치는 이 절과 `_drafts/b34_revision_log.md` §6에 옮겨 적었다.
   * 도구는 **AST가 바뀐 def의 본문 전체**를 변이한다(① 대상 = def, ② 연산자는 def의 모든 노드. 중첩 def는 따로 대상이 되고, 바깥 def의 변이에도 들어간다). 결과:
     바뀌는 def **32개**(최상위 30 + 중첩 `optimize_full_circuit_budget._evaluate_row_split`·`refine_differential_and_mirror_relations.classify`), 변이 **2,438개**. 뿌리 밖 호출자는 없다(계약 4의 뿌리 =
     SD `load_topology`·`run_full_circuit_audit_from_topology`, SR `_build_theta_evaluator`·`_fixup_euler_blocked_rows`·`l_sharing_classes`·`optimize_full_circuit_budget`·
     `run_matching_safety_with_finger_growth`·`run_topology_pipeline_with_finger_fixup` + `_metric_kcl_residual`). B34의 4 def와 겹치는 def 0개.
   * 그중 **diff가 닿은 문장·식에 걸린 변이는 135개**(좁은 정의: 복합문은 머리 줄만, 조기 return은 새 def에서만. 새 def `rail_declaration` 14개 포함). 인계 삭제 없이 `rails`만 넣은 비교 head는
     def 31·변이 2,447·닿은 변이 105다. 인계 삭제가 더한 몫은 **def +1(`classify` 6변이), 변이 순 −9**(`refine_…` 95 → 84, `propose_device_roles_gap_fill` 331 → 327, `classify` +6),
     **닿은 변이 +30**이다. +30의 대부분은 사이트 10·14 블록을 내어쓴 줄이다(줄 diff 기준이라 들여쓰기만 바뀐 문장도 '닿음'으로 센다). 나머지 2,303개는 이 card가 쓰지 않은 기존 문장이다.
     (옛 측정 cd64170·P9 전: def 31·변이 2,472·닿은 변이 106. P9가 `kcl_series_union`을 49 → 24로 줄인 것이 rails만 넣은 비교 head의 −25다.)
   * def별(변이 / 닿은 변이 / 인벤토리 test 수): `_build_theta_evaluator` 498/3/60, `propose_device_roles_gap_fill` **327/24**/138, `optimize_full_circuit_budget` 230/2/60,
     `repair_matching_safety` 112/3/69, `_branch_composite_pair` 102/1/70, `run_matching_safety_with_finger_growth` 100/4/62, `_fixup_euler_blocked_rows` 90/2/62,
     `refine_differential_and_mirror_relations` **84/28**/145, `run_topology_pipeline_with_finger_fixup` 65/2/61, `find_differential_pair_candidates` 65/4/146, `load_topology` 65/9/137,
     `_evaluate_row_split` 62/1/60, `find_matching_candidates` 60/2/146, **`_metric_kcl_residual` 57/4/0**, `audit_vertical_stack_id_vs_kcl` 56/6/63, `_composite_collapse_for_crossover` 55/1/65,
     `run_full_circuit_audit` 53/1/64, `propose_vertical_stack_id_gap_fill` 48/1/140, `l_sharing_classes` 42/5/60, `check_symmetry_dispositions` 37/1/140, `_propose_L_roles` 30/3/145,
     `_kcl_and_matching_edges` 30/2/140, `resolve_stack_layout` 26/2/61, `_propose_gm_id_roles` 26/2/145, `kcl_series_union` **24/1**/70, `run_full_circuit_audit_from_topology` 23/2/63,
     `_diff_pair_layer1_groups` 22/2/146, `true_current_mirror_groups` 17/1/60, `rail_declaration`(새) 14/14/137, `_kcl_branch_map` 7/1/70, **`refine_…classify` 6/0/145**(새 대상),
     `find_min_crossover_layout_with_branch_composite` 5/1/64. (인벤토리 수는 도구의 test 노드 규칙 -- `tests/tools/` 제외, `test*` 함수 노드 -- 로 센 값이다. 모의 사본에는 B34·P9의
     새 test 파일이 없다. 그 test들이 들어오면 B34 계약 test가 직접 부르는 `refine_…`·`propose_*` 등의 인벤토리가 늘어난다.)
   * **`_metric_kcl_residual`의 인벤토리는 0이다**(`compute_metric` → `_METRICS_REGISTRY` dict 경유라 정적 그래프에 간선이 없다). 57개 전부 '인벤토리 없음 → 생존' = V3 FAIL이다. 모의
     head에 `sr._metric_kcl_residual`을 **이름으로** 부르는 test 파일 하나를 더하면 인벤토리가 1이 되고 '인벤토리 없음' 변이가 0이 된다(재측정에서도 같음).
   * 면제 누수 대조: HEAD `7535799` 트리의 decision 승인 기록 id 26개 중 모의 head 변이 id와 겹치는 것 0개.
   * 시간(cd64170 측정을 그대로 씀. 이번에는 pytest를 돌리지 않았다): scratch 사본 전체 test 1회 813건 272 s(pytest 벽시계 299 s, 796 passed·2 failed -- `.git` 없는 사본의 `test_ts6_probe_relocate` 환경 실패). def별 인벤토리 실행 시간은
     177~192 s다(느린 test 몇 개가 거의 모든 인벤토리에 든다: `test_probe_parasitic_pm_all_circuits` 55 s, `test_s157_M1_known_limitation` 43 s, `test_s157_M1` 24 s, `test_s014_section` 17 s).
     pytest 한 번 기동 4.7~7.1 s. 도구는 변이를 **직렬**로 돈다.
2. **선택지와 비용(U1)** -- 아래 수치는 cd64170 측정 기준이다. 재측정 값으로 바꾸면 (a) 실행 135개(하한 ≈ 11분), (c) 실행 2,438개(하한 ≈ 3.4시간)이고, 결론은 같다:
   * **(a) 이 card의 V3를 diff가 닿은 문장과 새 def로 좁힌다.** 실행 106개: 하한 106 × ~5 s ≈ 9분, 상한(전부 생존·인벤토리 전체 실행) ≈ 5.3시간. 나머지 2,366개는 변이 id 목록 면제
     (`target_kind: decision`, `target` = 변이 id 목록, id는 도구 `mutants()`로 최종 head에서 생성). **실측 결함**: 면제 id는 `<모듈>:<qualname>:<연산자>:<AST 경로>`이고 def 해시나 card에
     묶이지 않으며, 도구(`reachability._approved_ids`)는 head 트리의 **모든** decision 승인 기록을 읽는다. 그래서 이 목록은 뒤 card에서도 같은 경로의 변이를 조용히 면제한다 -- B26-1
     시뮬레이션 head 위에서 B34 대상 def를 변이하면 1,402개 중 **619개**의 id가 이 면제 목록에 이미 있다(B34 자신의 편집으로 경로가 밀리는 몫은 빠지므로 상한). 선례 `20260922-ic3-v3-exempt`도
     같은 구조다(범위 설명에 "본문 구조가 바뀌면 이 면제는 맞지 않는다"고 적었지만 도구는 경로만 본다). (2026-10-01 보충: 이제 B34가 먼저 병합되고 B34 범위가 4 def로 좁아져서, 위 619개 예시는
     B34에 그대로 해당하지 않는다. 같은 구조의 누수는 뒤 card(B35·B26-2 등 같은 def를 다시 바꾸는 card)에 남는다.)
   * **(b) card를 더 잘게 나눈다.** 기본값 없는 키워드 인자는 피호출자에서 뿌리까지 모든 호출자의 AST를 바꾼다. `kcl_series_union`·`resolve_stack_layout`에 `rails`를 넘기는 한
     `_build_theta_evaluator`(498)가 대상이고, `kcl_series_union`·`audit_vertical_stack_id_vs_kcl`은 로드 경로와 평가 경로에 함께 쓰여 경로별로 나눌 수 없다. 나눈 card들의 대상 합은 2,472
     이상이다(여러 card가 같은 def를 바꾸면 그 def는 매번 전부 다시 변이된다). **비용을 줄이지 못한다.**
   * **(c) 전수 실행을 받아들이고 생존 변이마다 test를 보강한다.** 실행 2,472개: 하한(전부 첫 test에서 죽음) 2,472 × ~5 s ≈ 3.4시간, 상한(전부 생존) Σ 변이 × 인벤토리 시간 ≈ 122시간(≈5.1일,
     직렬). 생존 변이 중 등가가 아닌 것은 이 card와 무관한 기존 문장(예: `_build_theta_evaluator` 1,005줄 중 닿은 변이 3개)의 test 공백이라, test-author가 레일과 무관한 기존 동작의 test를
     써야 한다. 등가 변이는 (a)와 같은 id 면제가 필요하다(같은 누수).
3. **권고**: **(a)의 판정 범위를 card별 면제 목록이 아니라 게이트 규칙으로** 한다 -- `_drafts/v3_scope_systemic.md`의 게이트 변경 card(V3 대상 = diff가 닿은 문장 + 새 def, 면제 id를 def
   해시·card에 묶음)를 먼저 병합하고 B26-1은 그 규칙으로 판정한다. 근거: (i) 이 비용은 B26-1 한 건이 아니라 이후 엔진 card 전부의 문제다(B34 1,395개 등 -- 같은 문서), (ii) card별 목록은 위
   실측처럼 뒤 card로 새는 조용한 면제라 '조용한 폴백 금지' 원칙에 어긋난다, (iii) (b)는 비용을 줄이지 못하고 (c)는 이 card 범위 밖의 기존 test 공백을 이 card에 묶는다. 게이트 규칙 변경은
   현 V3 문언 대비 판정 범위 축소(약화)이므로 사용자 승인이 필요하다(같은 문서 §3). 사용자가 게이트 변경을 받지 않으면: (c)를 기본으로 하고 등가 변이만 id 면제(누수는 승인 기록 '재검토'에
   적는다). (a)를 card별 목록으로 받는 것은 누수를 알고 받는 경우에만.
4. **어느 쪽이든 할 것**: 새 test 파일 `A/tests/contracts/test_b26_rail_accessor.py`(test-author)는 `sizing_recipe._metric_kcl_residual(spec, ctx)`를 **이름으로 직접** 부르는 test를 둔다(시그니처가
   안 바뀌어 base에서도 호출된다 -- 인벤토리 0 → 1, 실측). 기대값은 계약 6의 가지를 각각 덮게 손으로 계산한다: MOS 부호, `ID` 없음 `KeyError`, `current_source` 아닌 이상원·단자 2개 미만
   건너뜀, `value_amp` `null` 노드 제외, `value_amp` 값 흘림, `exclude_nets` 제외, 선언 레일 제외, 최댓값·빈 경우 0.0, `rail_nets` 키 `ValueError`. (계약 7(d)만으로는 레일 제외 한 가지만
   덮는다.) 이 파일 이름은 `glob(` 사용처의 패턴(`probe_*.py`, `*.topology.json` 등)과 겹치지 않는다('작성 전 실측' 2).
5. auditor는 착수 시(P9·B34 병합본 base) 도구로 대상 def·변이 수를 다시 재고, 판정 기록 `checks.V3.basis`에 택한 선택지와 면제 승인 id를 적는다.
6. **인계 삭제의 V3 몫**: 두 def(`refine_…`·`propose_device_roles_gap_fill`)는 `rails` 때문에 이미 전체가 대상이다. 그래서 인계 삭제가 더하는 대상 def는 중첩 `classify` 하나(6변이, 인벤토리 145)뿐이고,
   변이 수는 순 −9다('V3 계획' 1). 지운 분기(부재 비교·`unavailable_reason` 키)의 변이는 head에 없으므로 면제할 것도 없다. 내어쓴 블록(사이트 10·14)의 변이 id는 AST 경로가 바뀐다(`body[k].body[i]` →
   `body[k']`). base 생존 목록과 대응시키는 판정을 쓰지 않는 한 영향이 없다. U1의 어느 선택지에서도 이 몫 때문에 승인을 늘릴 필요가 없다.

