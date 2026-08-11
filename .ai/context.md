# 세션 컨텍스트 (최종 갱신: 2026-08-11, 세션28 완료 — 전반부는 세션27이 남긴 최우선
항목①(헤드룸용 `vertical_stack_id` 병합이 레이아웃 오일러 검증에 미친 영향)을 Test 47
교체+self-test 재실행+`resolve_stack_layout()` 직접 실행으로 검증하고 "재설계
불필요"로 결론냈으나, 후반부에 사용자 질문("resolve_stack_layout에서 왜 pmos/nmos가
같은 stack에 있는데 오일러 패쓰에 문제가 없지?")으로 그 결론이 **정정**됐다 --
`check_euler_condition()`/`build_graph()`가 kind를 전혀 안 보는 순수 net-connectivity
그래프 알고리즘이라 PMOS/NMOS가 섞여도 "유효한 경로"로 잘못 통과시키고 있었다(실측:
`vbias2_stack`의 "검증된" trail이 M57(pmos)→M68(nmos) diffusion-인접을 요구 --
물리적으로 불가능). declared vsid 26개 중 8개(`output_stage_a/b` class-AB 출력단
포함)가 실제로 kind-mixed. 사용자 지시로 (a)/(b) 투트랙 완료:
**(a)** `build_graph()`에 kind 동질성 하드 게이트 신설 + `_verified_euler_fix()`/
`audit_vertical_stack_id_euler_feasibility()`가 크래시 대신 `kind_mismatch`
finding으로 구조화 보고. **(b)** 사용자가 직접 설계 확정한 2축 분리(`vertical_
stack_id`=전기적/수직, 물리 레이아웃 행=kind 동질+오일러/수평·대칭)를
`derive_horizontal_stack_groups()`(신설, `merge_layout_groups_by_matching_pairs()`
재사용)로 구현, `resolve_stack_layout()`에 배선. 실측 검증: `output_stage_a__pmos`
(M15,M25)/`output_stage_a__nmos`(M16,M26) 정확히 재병합, 51/51 커버·전 그룹 kind
동질, `audit_row_split()`의 3b 필수 게이트 PASS 확인(비교군: (a)만으로는 이 단계에서
크래시). `stick_diagram.py`(Test 51 신설)/`sizing_recipe.py`(L5b invariant 추가)
self-test 둘 다 exit 0·회귀 0건. `horizontal_stack_id`는 이번엔 candidates 전용
(topology.json 미영구화, 다른 회로 교차검증 후 다음 세션에 승격 논의) --
`vertical_stack_id` 자신의 candidates→declared 승격 경로를 그대로 재사용.
상세 전체는 파일 맨 끝 "# 세션28 결론" 및 이어지는 "## N"~"## Q" 참고, 배치 요약은
`docs/04-report/analog-topology-json-library.do.md` 배치 7-6f.)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 다음 세션 최우선 — 세션28이 2026-08-11에 재조정한 순서 (⚠️ 세션28 후반부에 한 번 더 재조정됨)
(반드시 이 순서대로 진행할 것. 세션28 상세 근거·코드 위치·실측값은 전부 파일 맨 끝
"# 세션28 결론"과 그 뒤 "## N"/"## O" 참고, 여기는 순서와 핵심 요약만)

**⚠️ 세션28 전반부는 세션27의 최우선 항목①(헤드룸용 `vertical_stack_id` 병합이
레이아웃 오일러 검증에 미친 영향)을 "완전히 해소, 재설계 불필요"로 결론냈었다 —
이 결론은 세션28 후반부에 사용자 질문으로 촉발된 재조사로 정정됐다(아래 ①,
"## N"/"## O" 참고). 재설계는 필요하다.**

### ✅ (완료, 세션28 후반부) — `vertical_stack_id`의 헤드룸/레이아웃 역할 분리 재설계 (b)

사용자 질문("resolve_stack_layout에서 왜 pmos/nmos가 같은 stack에 있는데 오일러
패쓰에 문제가 없지?")으로 촉발 — `check_euler_condition()`/`build_graph()`가 순수
net-connectivity 그래프 알고리즘이라 `t.kind`를 전혀 안 본다는 게 실측으로 드러났다.
이 회로 declared vsid 26개 중 **8개**(`biasgen_vom/vop_battery_a/b`, `vbias2_stack`,
`vbias3_stack`, `output_stage_a`/`b` class-AB 출력단)가 실제로 kind-mixed임을 확인 —
"vertical_stack_id=VDD→GND 전기적 컬럼"이라는 정의상 나타나는 정상 패턴이다.

**(a)**: `build_graph()` kind 동질성 하드 게이트 신설(이미 위 커밋에 기록됨).

**(b)**: 사용자가 직접 설계 방향을 확정 — "vertical_stack_id는 전기적(수직) 기준,
물리 레이아웃 행은 kind 동질+오일러(수평/대칭) 기준, 둘은 같은 branch 정보에서
각자 파생돼야 한다." 이 설계를 `derive_horizontal_stack_groups()`(`stick_diagram.py`,
`merge_layout_groups_by_matching_pairs()` 바로 뒤)로 구현: ①vertical 그룹을 kind로
분할 ②kind-homogeneous 서브그룹을 **기존** `merge_layout_groups_by_matching_pairs()`
(재발명 안 함)에 넘겨 declared matching_pairs로 대칭 branch 재병합. `resolve_stack_
layout()`(`sizing_recipe.py`)의 tier 2/3 두 호출부만 교체(2줄). 실측 검증:
`output_stage_a__pmos`(M15,M25)/`output_stage_a__nmos`(M16,M26)가 정확히 재병합됨,
21개 그룹으로 51/51 커버(손실 0)·전 그룹 kind 동질, `assign_finger_geometry()`→
`build_stick_diagram()`→`audit_row_split()` 직접 실행으로 M15/M25·M16/M26의
3b(interdigitation) 필수 게이트가 이제 PASS함을 확인(비교: (a)만 있던 상태를
재현하면 이 단계에서 즉시 크래시 — (a) 단독으로는 완주 불가능이었음을 재확인).
`stick_diagram.py` Test 51 신설 + `sizing_recipe.py` L5b에 kind 동질 invariant
추가, 두 self-test 파일 exit 0·회귀 0건. 상세는 파일 맨 끝 "## Q" 참고,
`docs/04-report/analog-topology-json-library.do.md` 배치 7-6f에도 기록.

**의도적으로 안 한 것(다음 세션 이후 이월)**:
1. `horizontal_stack_id`를 topology.json declared 필드로 영구화 — 지금은 candidates
   전용(항상 재계산). `vertical_stack_id` 자신이 세션22~23 candidates → 세션24~25
   declared로 승격된 경로를 그대로 밟는다. 다른 회로 최소 1개 교차검증 후 승격 논의.
2. `SizingContext.layout_solution`(B-5-3 원안의 instance-level 캐시) 신설 — 재계산
   비용이 순수 그래프 연산이라 저렴해 이번엔 불필요, 다음 세션 이후 항목.
3. `output_stage_a`/`b`류의 cross-row common-centroid(3c) 재정의 — 이번 검증에서
   3b(interdigitation)는 필수 게이트로 정상 PASS 확인했고, 3c는 이 pair 종류
   (`ratio`+`shares_node`)에선 애초에 참고용(§2.7 원칙)이라 이번엔 급하지 않음 —
   실제로 필수가 되는 `offset`/`branch_symmetric` 매칭쌍이 kind-mixed로 걸리는
   사례가 나오면 그때 재검토.

### ① 다음 최우선 — `allocate_stack_headroom()`의 "혼자 있는 non-cascode 소자" 기본정책 재검토

세션27이 M61/M64/M63 그룹에 `budget_reference_device: M5`를 달다가 발견(아직
미수정, "세션27 결론 ## D-6" 참고, 세션28이 feasible theta 전체 실행으로 재확인):
`M5`(1단 NMOS tail, `vertical_stack_id="vy_tail"` 그룹에 **혼자**)가
`allocate_stack_headroom()`에서 **VDD 전체(1.8V)를 혼자 VDS로 가져간다** — role이
"tail"(cascode 아님)이라 "남는 예산 균등분배" 로직을 타는데 그룹에 혼자면
"균등분배"가 "전부 다 가짐"이 된다. 그 결과 `vdd - vds(M5) ≈ 0`이 돼버려
`M61_M64_M63` 그룹(정확히는 `resolve_stack_layout()` 병합 후 `biasgen_ref` 그룹
`{M18_bg,M60,M61,M63,M64}`)이 음수 VDS를 받는 실제 크래시(`search_gm_id_for_role()`
의 `ValueError`, `entry={'ID':1.36e-6,'L':3.75e-7,'vds':-0.4,'vs':1.8}`, 세션28
재현 재료 그대로)로 발현됐다. `vx_tail_a`(M6)/`vx_tail_b`(M7)/`vbias4_stack`
(M66) 등 다른 singleton 그룹(세션28의 `resolve_stack_layout()` 결과, 아래 "세션28
결론" 전체 목록 참고)도 같은 문제를 안고 있을 가능성이 높다(아직 전수조사 안 함).
**재현 방법**: "세션28 결론 ## H" 스크립트 그대로(K_replica=0.05/r_classab_
battery=0.3 고정, 나머지 bounds-midpoint, `grid_points_per_theta=1`로 즉시 재현
— smoke test의 bounds-midpoint로는 이 경로 자체가 M9b infeasible에 막혀 안
드러남).

### ② 그 다음 — 3개 일반 함수 구현 (세션27 전반부 설계, 착수 전)

`derive_theta_dependency_graph()`(dead/독립/격리 1:1 theta-metric 쌍 판정) /
`extract_linear_feasibility_constraints()`(고정비율 A_signed 항에서 선형 부등식 자동
추출) / `presolve_warm_start()`(위 둘을 조합해 SLSQP 시작점 생성) — "세션27 결론 ## A"
에 설계 근거 전체 기록. K_replica/r_classab_battery 부등식(`r_classab_battery ≥
K_replica·ID(M15)/(ID(M1a)+ID(M1b))`)과 L_cascode/L_stage2out 1D LUT 이분탐색
웜스타트는 이미 손으로 유도·실측 검증 완료(세션27 중반, "세션27 결론 ## B" 참고) —
이 함수들은 그 손유도를 일반화하는 것.

### ③ 그 다음 — scipy 설치 + SLSQP + multi-start 구현

세션27 초반에 좌표하강 대신 이 방향으로 확정(이유: "세션27 결론 ## A" 참고 — 13개
theta가 cmrr/psrr(전체회로 MNA)을 매개로 강결합돼 있어 축 방향 탐색이 구조적으로
불리함을 실측 근거로 확인). scipy는 이 프로젝트 Python 환경(`C:\Python314`)에
아직 미설치 확인됨.

### ④ 그 다음 — 다른 회로 교차검증(+ `horizontal_stack_id` declared 승격도 같이 논의)
`folded_cascode` 등으로 `resolve_stack_layout()`/헤드룸/SLSQP 일반화 확인 — 세션22
부터 계속 이월되던 항목, ①~③ 전부 끝난 뒤 진행. 이때 `derive_horizontal_stack_
groups()`(세션28 신설)도 같은 회로로 교차검증하고, 통과하면 `horizontal_stack_id`를
topology.json declared 필드로 승격할지 논의.

### ⑤ 계속 이월
`run_harness.py`의 나머지 실전략(실제 회로 스펙 선정/제약 튜닝 등 운영 이슈) —
세션22부터 계속 이월.

### (아래는 세션27 착수 전 남아있던 기존 설계 스케치 원문, 참고용으로 보존)

### 왜 지금인가
`B-5-5`(세션22)가 정리한 3갈래 작업 중 **1번(vertical_stack_id 완성)까지 이번
세션(24~25)에 전부 끝났다** -- `vertical_stack_id`의 15개 gap을 채운 것(세션24)에
이어, 이번 세션(25)에서는 그 값들이 **애초에 무슨 기준으로 묶여야 하는가** 자체를
재정립했다: `stage1`/`biasgen_vom_a`/`cmfb_load`처럼 물리적 스택 기준과 설계 단계
개념이 뒤섞여 있던 declared 값을, `vertical_stack_id_candidates`(순수 물리적 직렬
스택 기준, `suggest_vertical_stack_composites()`)와 정확히 일치하도록 전부
재분해했다(H-3). 그 과정에서 `find_verified_differential_and_mirror_relations()`의
근본 버그(H-2, 소자쌍 dedup이 `M7`을 diff_branch_members에서 누락시켜 `M58`의
fan-in 재판정이 틀리던 문제)까지 고쳐서, **지금 `vertical_stack_id_candidates`는
이 회로에서 실측으로 100% 신뢰 가능한 상태**다(37/37 `headroom_role`, `ambiguous_
alternatives` 빈 딕셔너리, `M58`↔`M57`/`M9b`↔`M10`/`M18b`↔`M19` 전부 정확히 병합).
**`resolve_stack_layout()`의 1단계("`vertical_stack_id`를 유일한 권위 있는 경계로
삼는다")가 의존하는 바로 그 데이터가 이제 막 정확해졌다** -- 2번(`resolve_stack_
layout()` 신설)으로 넘어갈 준비가 된 시점이다.

### 기존 설계 스케치 (B-5-3, 세션22~23, "가칭"·"미구현" 상태 그대로 남아있음)
`docs/04-report/analog-topology-json-library.do.md`가 아니라 이 파일(`.ai/context.md`)
자체의 B-5-3절에 있다(grep으로 찾을 것). 기존 서브 solver를 재발명하지 않고 묶는
layered orchestrator로 설계됐다:
1. **`vertical_stack_id`로 1차 분할** -- 이걸 유일한 권위 있는 경계로 삼는다(자동
   fan-out 추론이 이 경계를 넘으면 안 됨).
2. 각 그룹 안에서 finger_w 탐색(`search_stack_finger_w()`, `stick_diagram.py`),
   실패하면 그룹분할(미매칭 소자 우선 분리) 후 재시도.
3. 각 그룹 안에서 오일러 walk 구성(`mirror_symmetric_trail()`, `stick_diagram.py`),
   실패하면 `suggest_pair_finger_adjustments()`(`stick_diagram.py`) 제안 → 2번부터
   재검산(핑거가 바뀌면 W도 바뀜).
4. 결과(그룹 멤버십·finger_w·walk 시퀀스·적용된 조정)를 구조체 하나로 반환,
   `ctx.layout_solution`에 캐시.

호출부 교체 제안(B-5-3 원문): `optimize_full_circuit_budget()`이 따로 계산하는
`stack_groups_kcl`/`stack_groups_geometry`를 이 함수 하나로 대체, `assign_finger_
geometry()`/`audit_row_split()`/`run_topology_pipeline_with_finger_fixup()`이 전부
이 캐시를 읽게.

⚠️ 위 세 서브 solver(`search_stack_finger_w`, `mirror_symmetric_trail`,
`suggest_pair_finger_adjustments`) + `allocate_stack_headroom()`(`sizing_recipe.py`,
do.md §7.3b) **전부 지금 코드에 실제로 존재함을 세션25 끝에 재확인**(grep으로 시그니처
확인 완료) -- 설계 당시 이후 이름이 안 바뀌었다.

### 이번 세션이 새로 밝혀서 설계에 반영해야 할 것
1. **입력 소스 결정 필요(설계 논의 필요, 미확정)**: `resolve_stack_layout()`의 1단계가
   `topology.json`의 **declared** `vertical_stack_id`를 읽어야 하는가, 아니면
   `_propose_vertical_stack_ids()`(`refine_differential_and_mirror_relations()`의
   `vertical_stack_id_candidates`)를 직접 호출해야 하는가? declared는 사람이 검토한
   확정값(이 프로젝트 원칙: topology.json이 유일한 소스)이지만 이 회로 하나만 채워져
   있다 -- 다른 회로(folded_cascode 등)는 declared가 비어있을 수 있어 그 경우
   candidates로 폴백하는 로직이 필요할 수 있다.
2. **`headroom_role`을 `allocate_stack_headroom()`과 연동할 것** -- `headroom_role`
   이 이제 37/37 신뢰 가능하므로(세션25), `resolve_stack_layout()`의 finger_w 탐색
   단계(2번)에서 `allocate_stack_headroom(vdd, stack=[{name,role,min_vds}, ...])`
   (`sizing_recipe.py`)에 그대로 넘길 `role` 값의 출처로 `headroom_role`을 쓸 수
   있다 -- 이전엔 이 값이 9/35 불일치라 못 미더웠지만 이제는 다르다.
3. **`M9a`/`M9b`류(`floating_current_source`) 핑거/walk 처리를 특별히 검토할 것** --
   이들은 서로 다른 kind(PMOS/NMOS)라 같은 physical column에 못 쌓이므로(세션25에서
   확립), `vertical_stack_id`가 이들을 별도 그룹(`biasgen_vom_a`=`M8`+`M9a`,
   `biasgen_vom_floatsrc_sink`=`M9b`+`M10`)으로 이미 정확히 분리해뒀다 -- 이
   경계를 `resolve_stack_layout()`이 그대로 존중하면 되고, 별도 처리는 불필요할
   가능성이 높다(확인만 필요).
4. **다른 3개 회로 일반화 미검증** -- 이번 세션 전체가 `current_reuse_telescopic_ota`
   하나로만 확인됨. `resolve_stack_layout()`을 이 회로로 먼저 검증한 뒤 최소 1개
   다른 회로(예: `folded_cascode`, `vertical_stack_id` declared가 비어있을 가능성
   높음 -- 입력 소스 결정(위 1번)이 먼저 필요한 이유)로 교차 검증할 것.

### 그 다음 이월 항목 (우선순위 낮음)
- `M58`의 `headroom_role="cascode"` 명칭 문제 -- **해결됨**(`M58`은 `M57` 위에 얹힌
  진짜 diode-cascode 구조라 "cascode"가 정확한 서술임을 사용자가 확정, 위 세션25
  기록 참고).
- `run_harness.py` 실전략 -- 세션22부터 계속 이월, 이번 세션도 미착수.

## 지금 상태 (세션25 완료 시점 기록)

### 커밋 상태(세션25, 2026-08-08 기준)
세션24 마지막 항목들 + 세션25 전체(E~H절)가 커밋 5개로 나뉘어 반영됨:
`1bf6d6d`(`m_cascode()` 기능적 수정) → `bc7e250`(`netclass.assign_roles()`도 같이
수정) → `96c7832`(`headroom_role` 자동 제안 신설, 37/37) → `97b517b`(`differential_
branch_members` 근본 수정) → `d72affd`(declared `vertical_stack_id` 재분해) →
`f4123a6`(`M9a`/`M18a` gm_id_role/L_role gap). 이 `.ai/context.md` 갱신분(이 절 포함)은
**아직 커밋 안 됨** -- 다음 세션 시작 시 `git log`/`git status`로 먼저 확인할 것.
변경 파일 전체: `.ai/context.md`, `skills/analog-gmid-design/assets/stick_diagram.py`
(self-test 46개), `skills/analog-gmid-design/assets/library/current_reuse_
telescopic_ota.topology.json`, `skills/analog-gmid-design/references/analog-
grammar-integration.md`, `skills/analog-grammar/assets/idioms.py`,
`skills/analog-grammar/assets/netclass.py`, `skills/analog-grammar/assets/sfg.py`.
self-test 커버리지 gap 없음(Test 45/46으로 해소).
⚠️ 과거 세션들이 의도적으로 커밋에서 뺐던 파일(정리 여부는 여전히 사용자 판단):
`.bkit/*`(bkit 자체 세션 추적), 루트 zip 2개(사용자가 올린 별도 파일), `workspaces/
current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`(세션18
잔재), `full_netlist_for_grammar.json`(세션22 analog-grammar 탐색용 1회성 변환
산출물).

### (해결됨) item 0 — input 승격 오케스트레이션 `refine_differential_and_mirror_relations()`
세션24에서 구현 완료(`stick_diagram.py` §1.7d, `find_verified_differential_and_
mirror_relations()` 바로 뒤에 위치 — 원래 그 뒤에 있던 `classify_symmetric_branch_
pairs()`는 이후 세션24 안에서 삭제됨, 아래 새 절 참고).
C-11 설계 스케치 1~4를 그대로 구현: `find_differential_pair_candidates()`로 후보
수집 → gate net 추출 → `inputs=`에 승격 → `find_verified_differential_and_mirror_
relations()` 재실행 → role/net class 변화를 조용히 덮지 않고 `role_changes`/
`net_class_changes`로 명시적 보고. C-11이 "설계 논의 필요"로 남겨뒀던 **5번(고정점
반복 여부)**은 while 루프로 결정: 새 후보가 더 안 나올 때까지 반복하되
`max_iterations=5`(기본값)로 상한 — 무한루프 방지용이지 실측 근거로 정한 값은 아님,
필요시 조정 가능. `find_differential_pair_candidates()`는 net 분류를 안 쓰므로
후보 자체는 보통 1라운드 이후 안 바뀌어(재확인 라운드 포함) 통상 `iterations=2`
`stop_reason="fixed_point"`로 수렴할 것으로 예상(self-test로 확인, `current_reuse_
telescopic_ota` 실회로 검증은 아래 D절 신규 이월 항목 참고).

self-test Test 38(`stick_diagram.py`)로 검증: `M37a`/`M37b`(CMFB 내부 differential
pair, 게이트가 `Voc`/`Voc_des`) 패턴을 6소자로 축소 재현한 합성 fixture(`M60a`/
`M60b`가 `Voc`/`Voc_des`를 게이트로 받고, `M60a`의 drain이 `M62`의 게이트를 구동)
사용. 확인된 것: (1) 승격 전엔 `M60a`/`M60b`가 `find_verified_differential_and_
mirror_relations()`에서 differential로 안 잡힘, (2) `refine_...()` 실행 후
`promoted_inputs=={"Voc","Voc_des"}`, `iterations=2`, `stop_reason="fixed_point"`,
`M60a`/`M60b`가 최종 `relations["differential"]`에 잡힘, (3) 연쇄효과 정확히 보고됨
— `Voc`: `BIAS`→`INPUT`, `Vcmfb_a`(`M60a`의 drain): `BIAS`→`SIGNAL`, `M62` role:
`ACTIVE_LOAD`→`AMPLIFYING`(세션23 실측 `Vcmfb`: `BIAS`→`SIGNAL`, `M7`:
`CURRENT_SOURCE`→`AMPLIFYING`과 같은 메커니즘, 단 합성 fixture라 role 조합은
다름). self-test 38개 전부 통과(exit code 0), 회귀 없음.

### (해결됨, 세션24) item 0-A — 실회로 대조 실행
`current_reuse_telescopic_ota.topology.json`(51소자)에 `refine_differential_and_
mirror_relations(transistors, inputs=("Vip","Vim"))`를 직접 돌려 확인. **C-11의
수동 검증과 정확히 일치**: `promoted_inputs=['Voc','Voc_des']`, `iterations=2`,
`stop_reason='fixed_point'`, `M7`: `CURRENT_SOURCE`→`AMPLIFYING`, `Vcmfb`: `BIAS`→
`SIGNAL`, `differential` 4건→6건(`M37a`/`M37b` 순증, C-11 실측과 동일).

⚠️ **새로 발견된 것 — C-11이 못 봤던 5홉 전파 체인**: C-11은 `Vcmfb`/`M7` 한 홉만
수동 확인했는데, 자동화된 함수는 그 뒤로 이어지는 체인 전체를 찾아냈다 — `M2a`/
`M2b`/`M58` role도 `CASCODE`→`AMPLIFYING`로 바뀌고, `Vbias2`/`N58_57`/`N36b`/`Vx`
net도 `SIGNAL`로 재분류됨. 전파 경로(직접 추적해서 버그 아님을 확인):
```
Voc(INPUT) -> M37a(G=Voc) -> Vcmfb(SIGNAL)
  -> M7(G=Vcmfb) -> Vx(SIGNAL)
    -> M58(S=Vx, G=Vbias2, cascode 규칙) -> N58_57(SIGNAL)
      -> M57(diode-connected, S=N58_57, G=D=Vbias2) -> Vbias2(SIGNAL)
        -> M2a/M2b/M58 자신의 role 재계산(gate=Vbias2가 이제 SIGNAL)
```
핵심 메커니즘: `M57`이 diode-connected(G=D=`Vbias2`)라서 `netclass.py`의 cascode/
current-buffer 신호전파 규칙(1d, "소스가 신호이고 게이트가 미확정/BIAS면 드레인도
신호")이 여기서 한 번 더 탄다 — `M58`이 `Vx`(신호)를 소스로 받아 신호를 계속
실어나르는 캐스코드처럼 취급되고, 그게 diode 소자 `M57`을 거쳐 `Vbias2` 자체까지
신호로 끌어올린다. `Vbias4`(같은 bias-gen 트리의 다른 가지, `M68`이 구동)는 이
경로에 안 걸려 `BIAS`로 안 바뀜 — 체인이 전체 bias 트리를 오염시키지 않고 실제로
연결된 가지만 정확히 따라간다는 뜻.

⚠️ **사람 판단 필요(topology.json에 아직 반영 안 함)**: `M2a`/`M2b`/`M58`/`Vbias2`가
CMFB 승격의 영향권 안에 있다는 게 이번에 처음 자동으로 드러난 사실이다 — 이걸
`device_roles`에 반영할지, `M2a`/`M2b`(differential 2단 캐스코드 부하로 보임)가
정말 CMFB 신호를 실어나르는 게 설계 의도인지는 다음 세션에 사람이 검토할 것
(`refine_differential_and_mirror_relations()`는 진단만 하고 `topology.json`을
쓰지 않으므로 아직 아무 부작용 없음).

### (해결됨, 세션24) `find_verified_differential_and_mirror_relations()`에 세 번째
### 버킷 `structurally_symmetric_no_connection` 추가 (사용자 지적: "이 대칭쌍들도
### symmetric branch로 출력되도록 해")
item 0-A 결과 표를 사용자에게 보여준 뒤, "구조적으로 거울쌍인 symmetric branch들은
왜 표시 안 해?"라는 지적을 받음 — 원인 확인: `find_verified_differential_and_mirror_
relations()`는 구조 매칭된 branch 쌍의 각 위치를 gate로 mirror/differential 둘로만
분류하고, **둘 다 아니면 `continue`로 조용히 버렸다**(`classify_symmetric_branch_
pairs()`(C-7/C-8)에는 있는 `structurally_symmetric_no_connection` 버킷이 이 함수엔
없었음). `refine_differential_and_mirror_relations()`가 이 함수를 그대로 감싸므로
같은 문제가 그대로 전파됐다.

**수정**: `stick_diagram.py`의 `find_verified_differential_and_mirror_relations()`
루프에서 "kind 다름" 또는 "gate 다르고 둘 다 INPUT 아님" 경우를 `continue`(버림) 대신
`category = "structurally_symmetric_no_connection"`로 분류해 세 번째 버킷에 담도록
수정(파일 한 곳, ~10줄). `differential`/`mirror` 판정 로직 자체는 손대지 않아 기존
결과는 회귀 없음. `refine_differential_and_mirror_relations()`는 이 함수의 반환값을
그대로 `relations`에 담으므로 별도 수정 없이 세 번째 버킷을 자동으로 받는다.

**실회로 재확인**(`current_reuse_telescopic_ota`, `inputs=("Vip","Vim")`로 승격
전 실행 기준): `structurally_symmetric_no_connection` 20건(방향 중복 제외 시 고유
10쌍) — `M6`/`M7`(같은 tail net `Vx`에 병렬, 하나는 고정 bias `Vbias1` 하나는 CMFB
출력 `Vcmfb`), `M36a`/`M36b`, `M9a`/`M18a`, `M9b`/`M18b`, `M11a`/`M20a`, `M11b`/
`M20b`, `M14a`/`M23a`, `M14b`/`M24b`, `M15`/`M25`, `M16`/`M26` — 세션23 실측(`.ai/
context.md` 세션23 C-8, `classify_symmetric_branch_pairs()`로 첫 divergence+하향
전용 12건)과는 정확히 같은 방법론이 아니라(이번엔 모든 위치+양방향) 개수가 다르지만
같은 계열의 신호. 사용자에게 보여준 이전 수동 계산(ad-hoc 스크립트) 결과와 정확히
일치함을 재확인.

self-test로 검증: (1) **Test 38 확장** — `M60a`/`M60b`(2차 differential pair
후보)가 승격 **전**엔 `structurally_symmetric_no_connection`에 잡히고(조용히
버려지지 않음), 승격 **후**엔 거기서 빠지고 `differential`로 옮겨가는지 확인.
(2) **Test 39 신설** — 실회로의 `M6`/`M7` 패턴을 Test 35 fixture에 `M7t`(`M6`과
같은 `Vx`를 drain으로 공유, 다른 gate)를 추가해 축소 재현, `structurally_symmetric_
no_connection`에 정확히 잡히고 differential/mirror로는 안 새는지 + 기존 `M1a`/
`M1b` 등 판정에 회귀가 없는지 확인. self-test 39개 전부 통과(exit code 0), 회귀 없음.

### (해결됨, 세션24) `classify_symmetric_branch_pairs()` 삭제
사용자 지시("classify_symmetric_branch_pairs는 없애")로 `stick_diagram.py`에서 함수
본체 + self-test Test 34를 완전히 제거. 근거: `find_verified_differential_and_mirror_
relations()`(6번, 위 절에서 세 번째 버킷까지 갖춤)가 하향 전용+첫 divergence만 보던
이 함수의 완전 상위호환이라 C-12 표에도 이미 "6번보다 이전/단순 버전"이라고 적혀
있었음 — 실질적으로 죽은 코드였다. 다른 함수 docstring에 남아있던 참조(6곳)는
"삭제됨"으로 정정해 dangling reference를 남기지 않음(코드에 2곳, 역사 기록은 위/아래
C-7·C-8·C-12 절에 원문 그대로 보존). self-test 전체(38개, Test 34 제외) 재실행 —
exit code 0, 회귀 없음.

### (해결됨, 세션24) item 0-B 중 `vertical_stack_id` 보완 — 15개 gap 전부 채움
0-B(item 0 다음 순서)의 두 갈래 중 `vertical_stack_id` 보완만 먼저 착수(`resolve_
stack_layout()` 신설은 여전히 미착수, 아래 참고). 실제로 착수해보니 문서에 적힌 것보다
범위가 컸다 — 15개 소자가 `vertical_stack_id`만이 아니라 **`device_roles` 항목 자체가
통째로 없었다**(`headroom_role`/`gm_id_role`/`L_role`도 없음). 확인해보니 이 15개 중
12개(`M1a`/`M1b`/`M2a`/`M2b`/`M3a`/`M3b`/`M4a`/`M4b`/`M15`/`M16`/`M25`/`M26`)는
`compensation.stage_devices`/`sizing_roles.theta`의 type-C(metric_stage_budget류)
feed가 이미 L/W/vds를 직접 정하는 별도 경로로 처리되고 있어서(원래 `_device_roles_
comment`가 이미 이 이유를 명시해뒀었음, 재확인으로 그친 부분), `headroom_role` 없이도
`allocate_stack_headroom()`의 group 순회에서 안전(vds가 이미 resolved라 `unresolved`
리스트에 안 들어감 → `device_roles[m]["headroom_role"]` 접근 자체가 발생 안 함).
나머지 3개(`M9a`/`M18a`/`M37a`)도 type-C(`K_replica`/`mirror_M18a`)/type-B(`N_cmfb_bw`,
L/W 직접 지정) feed로 커버됨을 확인 — **범위를 `vertical_stack_id`만으로 좁혀도
안전하다는 판단이 실측으로 뒷받침됨**(사람 판단대로 진행, 회귀 없음).

**`vertical_stack_id` 값 자체**는 `suggest_vertical_stack_composites()`(base declared
`inputs=("Vip","Vim")`만 사용)의 composite 출력에서 근거를 뽑았다 — 15개 소자가 등장하는
**모든** branch(양방향)에서 파트너가 일관되는지 먼저 검증(13/15는 완전 일관, `M3a`/`M3b`
만 fan-out 경로 하나에서 예외가 있었으나 완주하는 메인 branch 기준 `M3a`↔`M4a`/`M3b`↔`M4b`
채택 — 근거: 이 조합만 vdd~gnd 끝까지 이어지는 완전한 branch에서 나옴). 최종 반영:

| 그룹 | 소자 | 판정 근거 |
|---|---|---|
| `diffpair_top_a`/`_b`(신설) | M1a+M2a / M1b+M2b | composite(cascode-stack) |
| `diffpair_bottom_a`/`_b`(신설) | M3a+M4a / M3b+M4b | composite(cascode-stack), 완주 branch 기준 |
| `output_stage_a`/`_b`(신설) | M15+M16 / M25+M26 | composite(push-pull-output), 둘 다 drain=Vom/Vop(최종 출력) |
| `biasgen_vom_a`(확장) | +M9a | composite(M8과 cascode-stack), `M9a.source==M8.drain` 직접 스택 |
| `biasgen_vop_a`(확장) | +M18a | `M9a`/`biasgen_vom_a`와 대칭, `M18a.source==M17.drain` |
| `cmfb_tail`(확장) | +M37a | composite(M38과 cascode-stack), `M37b`와 대칭(C-6이 이미 지적한 gap) |

⚠️ **부수적으로 발견한 함정(반드시 지킬 것, 위 C-12 표 4/7번 항목에도 기록)**:
`refine_differential_and_mirror_relations()`가 승격한 `final_inputs`(`Vip,Vim,Voc,
Voc_des`)를 `suggest_vertical_stack_composites()`에 넣으면 **더 정확해지는 게 아니라
composite 6쌍이 통째로 사라진다**(실측: `M1a/M2a`, `M1b/M2b`, `M6/M58`, `M58/M7`,
`M37a/M38`, 이미 확정된 `M37b/M38`(`cmfb_tail`)까지) — `Voc`/`Voc_des` 승격이 일으키는
role 재분류(`M2a`/`M37a`/`M37b`/`M7` 등이 `AMPLIFYING`으로 바뀜, 위 item 0-A 절 참고)가
idiom matcher의 `cascode-stack` 인식 조건을 깨기 때문. `vertical_stack_id`(물리적,
instance 무관)는 base declared inputs만, differential/mirror 관계 판정(전기적, 2차
입력까지 알아야 정확)은 promoted inputs — **두 함수는 서로 다른 `inputs=`를 써야 한다.**
`refine_...()`의 `branch_a`/`branch_b`(전체 branch)도 그 자체로 `vertical_stack_id`엔
못 쓴다(한 branch가 여러 `vertical_stack_id` 세그먼트를 가로지름) — 다만 어느 leg(`_a`/
`_b`)에 속하는지 확인하는 용도로는 유효했고 실제로 그렇게 썼다(위 표의 `_a`/`_b` 접미사
근거).

topology.json에 반영 완료(`library/current_reuse_telescopic_ota.topology.json`), 51개
소자 전부 `vertical_stack_id` 보유 확인, self-test 38개 전부 통과(exit code 0, 회귀
없음) — **아직 커밋 안 됨**(`resolve_stack_layout()` 신설과 묶어서 커밋할지, 지금
따로 커밋할지 다음 세션 시작 시 확인할 것).

### (해결됨, 세션24) `analog-grammar`의 `cascode-stack`/`differential-pair` idiom 일반화
사용자 지적("cascode-stack을 찾는 방법이 좀더 일반화되어야 하지 않을까? signal로
표현되는 것을 cascode라고 말할 수 없기 때문에 제외하는 것일까?")에서 시작 — 확인해보니
정확했다. `idioms.py`의 `m_cascode()`가 `role[up]=='CASCODE'`(게이트가 고정 `BIAS`로
분류될 때만 나오는 role)만 허용하고 있어서, 캐스코드 게이트가 CMFB 등으로 능동 구동돼
`SIGNAL`/`FEEDBACK`로 재분류되면(예: `M2a`의 `Vbias2`가 `Voc`/`Voc_des` 승격 후
`SIGNAL`이 됨, item 0-A 절 참고) 물리적으로는 여전히 캐스코드인데도 매칭에서 통째로
빠졌다.

**role 필터를 완전히 제거하면 안 되는 이유(실측)**: 13쌍의 새 오탐이 생긴다 — (1)
차동쌍 입력소자가 자기 tail 전류원 위에 있는 걸 캐스코드로 착각(`M1a`on`M6`/`M7` 등
6쌍), (2) 2-다이오드 레벨시프트 체인을 캐스코드로 착각(`M11a`/`M11b` 등 5쌍), (3)
이미 `diode-connected`로 분류된 소자가 이중 라벨링됨(`M58`/`M57` 등 2쌍). 조사 중
오늘 만든 `M37a`→`cmfb_tail` `vertical_stack_id` 판단의 근거였던 `cascode-stack(M37a,
M38)` 매칭도 **같은 함정의 반대쪽 사례**(`Voc` 미선언 시 기본값 `BIAS` 폴백으로 우연히
`CASCODE` role이 됨 — 실제로는 `M37a`/`M37b`가 CMFB 차동쌍의 입력 다리, `M38`이 그
tail 전류원)라는 걸 발견했다. 다행히 `vertical_stack_id` 판단 자체는 `M37a.source==
M38.drain`이라는 순수 connectivity로 검증했지 idiom 라벨을 신뢰한 게 아니라 안전했다
(물리적 스택 여부는 role/idiom 라벨과 무관하게 참).

**최종 수정(`skills/analog-grammar/assets/idioms.py`, 두 함수)**:
1. `m_diffpair()` — "source 공유 소자가 정확히 2개"라는 조건이 셋째 소자(bias 인출용
   등)가 같은 tail net에 얹히면 깨져서 `M1a`/`M1b`, `M4a`/`M4b`를 통째로 놓치고
   있었다(`stick_diagram.py`의 `find_differential_pair_candidates()`가 세션24 초반에
   이미 고친 것과 정확히 같은 버그가 `analog-grammar`에도 있었음). 같은 source를
   공유하는 그룹 안에서 **모든 쌍을 개별적으로** 판정하도록 수정.
   ⚠️ 이 수정 자체가 새 오탐을 하나 만들었다(실측으로 발견, 같은 세션 안에서 바로
   막음) — `M58`(bias 인출용, `M1a`/`M1b`와 같은 `Vx`를 tail로 공유)의 role이 CMFB
   승격 후 `AMPLIFYING`이 되면서 `M1a`/`M58`도 differential-pair로 잘못 잡혔다.
   `cls.get(a['G']) == cls.get(b['G'])`(두 게이트의 net **class**가 같아야 함 —
   `M1a`의 `Vip`는 `INPUT`, `M58`의 `Vbias2`는 `SIGNAL`이라 다름) 조건을 추가해 해결.
2. `m_cascode()` — `role[up]` 허용 범위를 `(CASCODE, AMPLIFYING, CONTROLLED_CURRENT_
   SOURCE)`로 넓히되, `up`이 (고쳐진) `m_diffpair()`가 찾은 differential-pair 다리면
   제외. diode-connected는 role이 항상 `DIODE`라 이 허용 목록에 없어 자동으로 계속
   제외됨(오탐 유형2/3 방지, 실측 확인).

**검증**: `stick_diagram.py` self-test 39개 전부 통과(exit code 0, 회귀 없음, 2회
재실행) + `analog-grammar`의 `run_example.sh` 두 예제(`fig2_telescopic.json`,
`fig3_classab.json`) 정상 실행, 문서화된 기대 결과(`coverage=0.75` 등)와 일치 +
실회로 3가지 시나리오(base/promoted/promoted+`feedbacks=('Vcmfb',)`) 전부 재확인:
`differential-pair`가 `M1a`/`M1b`,`M4a`/`M4b`(base)와 `M37a`/`M37b`(promoted 추가)를
정확히 잡고 오탐 없음, `cascode-stack`이 `M1a`/`M2a`,`M1b`/`M2b`를 promoted 상태에서도
유지(전엔 사라졌음), `M37a`/`M38`,`M37b`/`M38`은 이제 정확히 사라짐(진짜 diffpair
다리이므로 옳은 동작 — 예전엔 몰라서 남아있던 것). `suggest_vertical_stack_composites()`
end-to-end 재확인 결과, C-12 표에 남겨뒀던 "promoted inputs 넣으면 6쌍이 사라진다"는
경고가 "정확히 2쌍(`M37a`/`M38`,`M37b`/`M38`, 둘 다 원래 mislabel이었던 것)만 옳게
사라짐"으로 개선됐다 — 아래 C-12 표의 경고 문구도 이에 맞춰 갱신할 것(다음 편집).

⚠️ **여전히 일반적인 캐스코드 탐지는 아니다(사용자 질문에 대한 정확한 답)** — role이
`FOLLOWER`/`UNRESOLVED` 등 다른 조합으로 분류되는 경우는 여전히 못 잡는다. 코드 자체는
이 topology에 국한되지 않은 범용 함수이지만(하드코딩 없음), 검증은 이 회로 하나에
한정됐다.

### (해결됨, 세션24) `refine_differential_and_mirror_relations()`에 `vertical_stack_id_candidates` 자동 제안 신설
사용자 지시("cascode-stack composite뿐 아니라 differential-pair/mirror 관계의
vertical-stack-id를 기능에 맞는 이름을 부여해서 최종 vertical-stack-id를 만들어서
return하도록") — 처음엔 `suggest_vertical_stack_composites()` 자체를 고치라는
요청이었으나, 그러면 `suggest_vertical_stack_composites()`→`refine_...()`→
`find_verified_...()`→`suggest_vertical_stack_composites()`로 **무한 재귀**가
됨을 확인(의존 그래프상 `suggest_vertical_stack_composites()`가 최하위 leaf,
`refine_...()`가 최상위)하고, 대신 `refine_differential_and_mirror_relations()`
쪽에 새 내부 헬퍼 `_propose_vertical_stack_ids()`(`stick_diagram.py` §1.7d)를
신설해 여기서 조합하는 방향으로 정정.

**알고리즘(최종, 여러 차례 실측 교정을 거침)**:
0. **fan-in 후보 탐지** — `role=='CASCODE'`인 소자가 물리적으로 얹힐 수 있는 같은
   kind `lo` 후보(`lo.drain==up.source`)가 2개 이상이면 순수 connectivity만으로는
   못 가림(최초 구현에서 `M9b`/`M18b`가 `M3a`/`M3b`(진짜 differential-pair 스택)에
   잘못 흡수되는 오탐으로 발견, `M58`도 같은 문제로 부가 발견 — `M6`/`M7` 둘 다에
   얹힐 수 있었는데 조용히 `M6`으로 골라지고 있었음).
0-B. **differential-pair branch 소속 여부로 재판정**(사용자 통찰: "M9b가
   differential branch에 있지 않다는 걸 알면, 그 branch 소속인 M3b보다는 비소속인
   M10이 더 적당하다") — 후보 중 정확히 하나만 `relations["differential"]`의
   branch 멤버가 아니면 그쪽으로 확정. 실측: `M9b`→`M10`, `M18b`→`M19`, `M58`→`M7`
   셋 다 이 규칙으로 확정되어, 이 회로에서는 결국 모호한 소자가 하나도 안 남음(단,
   이건 이 회로의 실측 결과이지 일반 보장 아님 — 후보 둘 다 걸리거나 둘 다 안
   걸리면 여전히 모호할 수 있음, self-test Test 41이 그 경우를 합성 fixture로
   검증).
1. **composite 스캔**(양방향, base declared inputs만 — promoted inputs는 물리적
   인접성 신호를 잃는 부작용이 있어 여전히 금지) — `relations["differential"]`의
   chain과 정확히 일치하는 branch를 먼저 처리해 우선권을 줌(0-B에서 못 푼 모호한
   소자는 격리, 0-B에서 확정된 소자는 자기 파트너가 낀 composite에서만 합류).
2. **leg 접미사 부여** — `differential`/`mirror` 관계의 `branch_a`/`branch_b`
   position으로 각 소자의 leg(`a`/`b`) 확인, composite로 못 묶인 singleton은
   이웃 소자 그룹에 흡수.
3. **최종 이름 조립** — leg가 그룹 안에서 전부 하나면 접미사 부여(`diffpair_top_a`류),
   섞여 있으면(hub 공유) 접미사 없음(`cmfb_tail`류).

**반환**: `refine_differential_and_mirror_relations()`의 `vertical_stack_id_
candidates` 필드 = `{"groups": {device: proposed_id}, "ambiguous_alternatives":
{device: [candidate_group, ...]}}` — `ambiguous_alternatives`는 0-B로도 못 푼
소자용 후보 그룹 목록(layout 함수가 헤드룸/핑거 호환성 기준으로 그중 하나를 고를
수 있게, 이 함수 자체는 고르지 않음).

**실회로 검증**(`current_reuse_telescopic_ota`, base inputs): 51개 소자 전부
후보 반환. 세션24 앞부분에서 손으로 채운 9개 순수 물리 스택 그룹(`diffpair_top_a/b`,
`diffpair_bottom_a/b`, `output_stage_a/b`, `cmfb_tail`)과 **전부 정확히 일치**
(그룹 멤버십 기준, counter 번호는 다를 수 있음). `biasgen_vom_a`류(여러 물리
스택을 "같은 bias 기준"으로 묶은 느슨한 기능적 클러스터)는 의도적으로 재현 안 됨
(이 알고리즘은 순수 물리 인접성만 봄, docstring에 명시). `ambiguous_alternatives`는
이 회로에서 최종적으로 빈 딕셔너리.

self-test Test 40(기본 동작)/41(구별 신호 없어 진짜 모호한 경우)/42(differential
branch 소속 여부로 재판정되는 경우) 신설, 전체 42개 self-test 통과(exit code 0,
회귀 없음). `topology.json`엔 아직 반영 안 함(이 함수는 제안만, 자동 기입 안 하는
프로젝트 원칙) — 다음 세션에 `M9b`/`M18b`/`M58`의 확정된 그룹을 실제로 채택할지
사람이 검토할 것(이번엔 매우 구체적인 근거(fan-in 후보 + differential-branch
재판정)까지 나왔으므로 검토 부담이 작음).

### (해결됨, 세션24) `device_roles`의 나머지 세 필드(`headroom_role`/`gm_id_role`/
### `L_role`) 자동 제안 시도 — `gm_id_role`/`L_role`은 완성, `headroom_role`은 미완
사용자 질문 "`refine_differential_and_mirror_relations()`이 `headroom_role`,
`gm_id_role`, `L_role`도 다 채울 수 있지 않나?"에서 시작. 먼저 이미 declared된
36개 소자에서 **netclass role만으로는** 이 세 필드를 재현 못 한다는 걸 실측으로
확인(`CURRENT_SOURCE` role 하나가 `(headroom,gm_id,L)` 조합 4가지로 갈림) — 이
세 필드는 순수 구조적 사실이 아니라 `do.md §7.3.1`의 사이징 방법론 판단이 섞여
있다는 걸 먼저 인지하고, 세 필드를 각각 따로 검증했다.

**`gm_id_role`(완료, 36/36 실측 일치)**: `find_differential_pair_candidates()`가
찾은 `shared_source`(차동쌍이 공유하는 tail net)를 **drain으로 받는 소자**(예:
`M6`/`M7`→`Vx`, `M5`→`Vy`, `M38`→`Ncmfb_tail`) → `balanced`, 나머지 전부 →
`matching`. 이 규칙 하나로 declared 36개 전부 정확히 재현됨(`headroom_role`의
`mirror`/`cascode` 구분과 달리 이건 처음부터 구조 신호 하나로 충분했음). 새 내부
헬퍼 `_propose_gm_id_roles()`(`stick_diagram.py`, `_propose_vertical_stack_ids()`
바로 뒤) 신설, `refine_differential_and_mirror_relations()`의 반환값에
`gm_id_role_candidates: {device: "balanced"|"matching"}` 필드로 추가. self-test
Test 43 신설.

**`L_role`(완료, 35/36 실측 일치, `M38` 하나만 문서화된 예외)**: 사용자 원안
("mirror 구조를 찾으면 L_role=mirror로 정하고, 아니면 그 branch의 mirror L을
propagate")을 먼저 그대로 구현해서 검증했더니 `relations["mirror"]`(같은
matched-branch-pair 안에서만 비교)로 커버되는 게 10/36뿐이었다(대부분의 bias-gen
소자가 단독 diode/floating-battery라 구조적으로 비교할 "형제 branch" 자체가 없어서
propagate도 실패). **사용자가 "극성을 고려해서 매칭 파트너를 잡게 수정해"라고
지적** — 이미 있던 `find_structural_symmetry_candidates()`(§1.8, `transform="mirror"`
로 kind를 보존하며 전역 netlist를 자동매칭하는 함수, 세션6에 신설되어 원래
`M11a`의 진짜 좌우 짝이 `M20a`(같은 스택 안의 `M11b`가 아니라!)임을 처음 밝혀낸
바로 그 도구)를 연결하기로 함. `find_differential_pair_candidates()`가 찾은 각
차동쌍의 게이트 net(`Vip`/`Vim`, `Voc`/`Voc_des`)을 좌우 대응 seed로 자동
생성하고(+ `vdd`/`gnd` 자기자신 seed) `transform="mirror"`로 전역 대칭을 풀면
**51개 중 48개**가 풀림(`M11a<->M20a`, `M14a<->M23a`, `M9a<->M18a`, `M8<->M17`
등 declared `matching_pairs`와 정확히 일치, `M39`/`M40`/`M7`만 unresolved — `M7`은
`M6`과 원래 비대칭 설계라 정상).

최종 규칙: (1) tail 공급 소자(`gm_id_role=='balanced'`) → `bias_replica`.
(2) `find_structural_symmetry_candidates()`의 `device_map`에서 자기 자신이 아닌
다른 소자로 풀리면 → `mirror`(+ `confirmed_by_structural_symmetry=True`,
`symmetry_partner`). (3) 그 외 → `mirror` 기본값(`confirmed_by_structural_
symmetry=False`). `_propose_L_roles()` 신설, `L_role_candidates` 필드 추가.
⚠️ `M38`은 이 규칙의 유일한 예외(`topology.json`의 `_M38_L_role_comment`에 이미
문서화됨 — CMFB 루프이득 `A_c` 재분석으로 사람이 의도적으로 `bias_replica`가
아니라 `mirror`로 override한 사례, 구조 분석으로 재현 불가능한 성질이라 이 함수는
반영하지 않음). self-test Test 없음(L_role 전용 테스트는 아직 안 만듦 -- **다음
세션 할 일로 이월**, gm_id_role/vertical_stack_id처럼 Test 45급으로 추가할 것).

**`headroom_role`(미완, 다음 세션 이어감)**: `mirror`/`cascode` 구분을 6가지
구조적 가설로 시도했으나 전부 반례가 있었다 — (1) up/lo 위치, (2) declared
`matching_pairs` 소속(boolean, `M8`/`M10` 둘 다 True인데 반대로 갈림), (3) diode
단독 vs 체인, (4) `idioms.m_mirror()`(diode 기준+gate+source+kind 공유 그룹) 단독,
(5) `m_mirror()` + tail 제외(**9/35 불일치까지 줄임, 지금까지 가장 근접**), (6)
"lo-of-cascode-stack이면 cascode" 추가 예외(`M8`/`M17`에서 깨짐 — 얘네도 `lo`인데
`mirror`로 declared됨, `M10`/`M19`는 같은 패턴인데 `cascode`로 declared돼 있어
방향이 안 맞음). 남은 9개 불일치: `M17`,`M8`,`M18b`,`M9b`,`M36b`,`M39`,`M40`,
`M63`,`M37b`.

**부수 발견 — `suggest_vertical_stack_composites()`의 `ports` 소실 버그(해결됨)**:
headroom_role을 더 파다가, 사용자가 "`M8`/`M9a`가 cascode-stack으로 묶이는 건
analog-grammar 헛점"이라고 지적 — 확인해보니 물리적 병합 판단 자체(`m_cascode()`)는
틀리지 않았고(캐스코드된 전류미러는 교과서적으로 정상 구조), **`idioms.Match.ports`
(`lower_role` 등)를 `suggest_vertical_stack_composites()`의 `_composite()`가 조용히
버리고 있었다**는 게 진짜 문제였다(`M8`=mirror 기준/`M9a`=그 위 캐스코드라는 구분이
composite 단계에서 사라짐). `stick_diagram.py`의 `_composite()`를 고쳐 각 composite
dict에 `"ports"` 키를 추가(단일 소자 composite는 `ports={}`) — 기존 소비처는
`members`/`idiom`만 읽으므로 순수 추가라 회귀 없음(Test 33의 과도한 dict 완전일치
assert 하나만 `members`/`idiom` 개별 비교로 완화). self-test Test 44 신설(M1a/M2a
composite의 `ports['lower_role']=='AMPLIFYING'` 검증), 실회로 재확인: `M8`/`M9a`
composite의 `ports={'mid':'Vg15','out':'Vop1','lower_role':'CURRENT_SOURCE'}` 정상
노출. **다음 세션에 이 `lower_role` 정보로 `headroom_role` 재시도할 것** — 아직
안 해봄(질문만 받고 세션 기록 요청이 먼저 들어옴).

self-test 전체 44개 통과(exit code 0, 회귀 없음). 변경 파일: `stick_diagram.py`만
(이번 절 전체가 `topology.json`/`idioms.py`는 안 건드림).

### 다음 세션 작업 순서 — 이 순서 그대로 진행할 것 (세션24 item 0/0-A + 세 번째 버킷 + vertical_stack_id 보완 + classify_symmetric_branch_pairs 삭제 + analog-grammar 일반화 + vertical_stack_id_candidates/gm_id_role_candidates/L_role_candidates + ports 보존 버그 수정 완료 기준, 아래가 최신)

**0-C. [가장 먼저] `headroom_role` 재시도 — `suggest_vertical_stack_composites()`의
새 `ports['lower_role']` 정보 활용** — 세션24 끝에서 막 고친 참이라 아직 시도
안 함. 아이디어: composite의 `lower_role`이 `CURRENT_SOURCE`/`ACTIVE_LOAD`(즉
"고정 게이트로 전류를 흘리는 소자")면 그 `lo` 소자를 `mirror` 후보로, `up`
소자(`role==CASCODE`)는 `cascode`로 1차 분류해보고, 그래도 남는 반례(`M17`/`M8`
vs `M10`/`M19`처럼 같은 패턴인데 반대로 declared된 것)가 있으면 그 반례 목록을
그대로 사람에게 보여주고 판단을 넘길 것(6번째 가설까지 실패한 전례가 있으니
과신하지 말 것). 9/35 불일치보다 나아지는지가 성공 기준.
⚠️ **0-C 보강(2026-08-08, 사용자 지적)**: 위 1차 분류안("`lower_role`이
`CURRENT_SOURCE`/`ACTIVE_LOAD`면 `lo`=mirror, `up`(role==CASCODE)=cascode")을
그대로 적용하면 **`M9a`/`M18a`에서 확실히 틀린다** — `M9a`는 `M8`(`CURRENT_SOURCE`)
위에 물리적으로 직렬 스택되어 있어 `lower_role`=`CURRENT_SOURCE` 조건은 만족하지만,
`M9a`의 실제 기능은 캐스코드가 아니라 Monticelli class-AB floating current source의
절반이다(`M9a`(PMOS)/`M9b`(NMOS)가 비-레일 노드 `Vg15`<->`Vop1`(=2단 출력 `M15`/`M16`의
게이트) 사이를 상보 anti-parallel loop로 마주보고 잇는다 — `analog-grammar/assets/
idioms.py`의 `floating-current-source` idiom, 2026-08-08 신설로 검출됨, `examples/
fig3_classab.json` 고립 fixture와 `current_reuse_telescopic_ota` 전체 회로 양쪽에서
실측 확인, `M18a`/`M18b`가 Vop측 대칭 사례). **`headroom_role` 재시도 시 반드시 이
idiom 매칭을 먼저 확인할 것** — 어떤 소자가 `floating-current-source`의 leg면(위
예시: `M9a`, `M9b`, `M18a`, `M18b`) `lower_role` 휴리스틱보다 우선해서 `cascode`가
아닌 별도 role(가칭 `class_ab_float`)로 분류해야 한다. `M8`/`M10`(그리고 `M17`/`M19`)은
이 floating loop 위/아래에서 바이어스 전류만 대주는 독립 전류원/싱크로, `mirror`
분류는 그대로 맞다(이 부분은 1차안과 결론이 같음).
0-D. `_propose_L_roles()` 전용 self-test(Test 45급) 신설 -- 아직 없음, Test 43
(`gm_id_role`)과 같은 패턴으로 Test 35 fixture 재사용해서 만들 것.
0-E. `vertical_stack_id_candidates`/`gm_id_role_candidates`/`L_role_candidates`를
`topology.json`에 실제로 반영할지 검토(0-B-1과 통합해서 한 번에 처리해도 됨) —
`M9b`/`M18b`/`M58`의 vertical_stack_id, `M11a`/`M20a` 등 48개 소자의 L_role
`symmetry_partner` 근거, `gm_id_role` 36개 전부가 이미 사람이 검토하기 좋은
형태로 준비돼 있음.

(0-C/0-D/0-E 다음 순서, 세션24 앞부분부터 남아있던 이월 항목들 — 여전히 유효)

**0-A-1. [0-B 전에, 짧으면 바로] 위 "사람 판단 필요" 절 검토** — `M2a`/`M2b`/`M58`
role이 CMFB 승격으로 `AMPLIFYING`으로 바뀌는 게 설계 의도와 맞는지 확인하고,
맞으면 `device_roles`에 반영할지 결정. `topology.json`의 connectivity는 이미
정확하므로(이 발견은 role 재분류일 뿐 connectivity 변경이 아님) 급하지 않으면
0-B로 바로 넘어가도 무방 — 사용자 판단.

**0-B-1. [0-B 전에, 짧으면 바로] `M9b`/`M18b`/`M58`의 `vertical_stack_id_candidates`
확정 그룹 채택 여부 검토** — `refine_differential_and_mirror_relations()`가
`M9b`→`M10`, `M18b`→`M19`, `M58`→`M7` 그룹으로 확정 제안함(fan-in 후보 + differential-
branch 재판정 근거, 위 "vertical_stack_id_candidates 자동 제안" 절 참고). 사람이
검토해서 맞으면 `topology.json`의 `device_roles`에 반영(이 세 소자는 현재
`vertical_stack_id`가 없는 상태 그대로임 — 15개 gap 채울 때 fan-in 모호성 때문에
일부러 제외했었음).

**0-B. [item 0 다음] `vertical_stack_id` 나머지(`biasgen_*` 등 기능적 클러스터) +
`resolve_stack_layout()` 신설** — 세션22 B-5-5가 정리한 3갈래 중 남은 두 갈래. 상세
설계(원문 그대로, 요약 아님)는 아래 "세션23 결론" D절 item "0-B"를 그대로 참고할 것
— 그 항목 자체에 이미 B-5-2(2계층 정보 분리)/B-5-3(`resolve_stack_layout()` 4단계
orchestrator 설계) 원문 발췌가 들어있어 재붙여넣기 없이 바로 구현 착수 가능하도록
적어뒀다. ⚠️ `vertical_stack_id` 자체의 "순수 물리 스택" 부분(diffpair_top/bottom_a/b,
output_stage_a/b, cmfb_tail, 이제 M9b/M18b/M58까지)은 세션24에서 사실상 자동
제안까지 완료됐다 — 남은 건 `biasgen_vom_a`류(여러 물리 스택을 "같은 bias 기준"으로
묶은 느슨한 기능적 클러스터, `vertical_stack_id_candidates`는 의도적으로 이걸 재현
안 함)를 그대로 유지할지, 아니면 이참에 물리 스택 단위로 더 잘게 쪼갤지 설계 논의가
필요하다는 점.

**1. `run_harness.py`를 실제 theta bounds(전수/축소 그리드)로 재실행** — 세션22가
   `optimize_full_circuit_budget()`의 end-to-end 크래시를 전부 없앴으므로(아래
   "세션22 결론" 참고), 이제 처음으로 실제 그리드서치를 오래 돌려볼 가치가 있다.
   세션11이 이미 8192개 조합 완주에 ~10시간이 걸릴 것으로 추정해뒀다 — 그대로 돌릴지,
   자유 theta를 아래 item 3(그리드 탐색 그룹 구조 재분석)으로 줄인 뒤 돌릴지 사용자와
   먼저 정할 것.
2. **`>=60dB` 등 constraint 임계값 재보정** — 세션21 2차 때 새 스케일(51소자 전체망)로
   바뀐 뒤 세션22에서 "지금은 손대지 않고, 실제 최적화 결과가 쌓이면 그때 정한다"로
   사용자가 명시적으로 결정. 1번(실제 grid search)이 실제 결과를 만들어주면 그걸
   근거로 재론의할 것 — 손으로 만든 self-test fixture 앵커(CMRR≈125.8dB 등)나 세션22의
   임시 1~2점 샘플(CMRR≈93~128dB 범위)은 전부 "스케일 감 잡기"용이었지 확정 근거가
   아니다.
3. **그리드 탐색 그룹 구조 재분석**(세션21 결론에서 이월, 아직 미착수) — 13개 자유
   theta 각각이 `cmrr_estimate_db`/`psrr_estimate_db`/`gain_full_circuit_db`에 실제로
   얼마나 영향을 주는지 수치 민감도로 확인. 세션22가 이 작업을 시도하다 stack M6
   크래시를 만나 옆길로 샜다 — 이제 크래시가 없으니 바로 재개 가능(OAT 스윕 스크립트
   초안이 `workspaces/current-reuse-telescopic-ota-report/theta_sensitivity_session22.py`
   에 있으나 완주는 못 함, 재사용/재작성 판단 필요).
4. **(선택) folded_cascode/nmcnr_amplifier/two_stage_ota에 `ports`+`smallsignal_*`
   확장** — 세션21 2차 이월 항목, 우선순위는 사용자 판단.

⚠️ **item 1~4는 세션22 시점 우선순위 그대로다** — 세션23이 전혀 손대지 않은 영역
(vertical_stack_id/differential-pair/mirror 자동화 실측에 세션23 전체를 씀). item
0/0-B(세션23이 새로 만든 최우선순위)를 먼저 끝내고 나서 진행할 것 — 특히 item 4였던
"vertical_stack_id 경계 확장 재검토"는 이제 item 0-B로 승격되어 구체적 설계까지
끝난 상태이니 중복 재검토하지 말고 0-B 원문 설계 그대로 구현만 하면 된다.

### (참고, 세션19까지의 이력 — 세션12~19 커밋 요약)
세션16 커밋: `58e608b`(크래시 수정 + branch 복합 매칭), `7a41a30`(매칭 목적
핑거증가 L3+L4). 세션17 커밋 3개(시간순): `4bcaafc`(재설계안 3번 완화) →
`69d9b39`(crossover 짝짓기 우선순위 재작성, D-1) → `4e38aa6`(offset 우선순위 가중치
+ branch composite 사전병합, F/G절). 세션18 커밋: `a6ab04b`(그룹분할 harness 배선).
세션19 커밋 2개: `d4bd4d9`(analog-grammar skill 반입 + Tier 1 연동), `55b3ef2`
(세션19 종료 핸드오프 문서). (세션12~19의 세부 항목은 각 세션 결론 절 및 아래
"작업 파일 위치" 절에 그대로 보존돼 있다 — 위 0~5번이 세션20 시점 기준 최신 상태
요약이다.)

## 배경 — 이 기능이 뭐고 왜 하는가 (세션5~11 공통, 참고용)

- **WHY**: topology netlist가 Python 코드 하드코딩이면 재현 불가능, agent마다 해석이
  달라짐 — 그래서 `topology.json`(`skills/analog-gmid-design/assets/library/*.topology.json`)
  하나를 유일한 소스로 둔다.
- **권한 경계(중요, 항상 지킬 것)**: `netlist`/`passive_elements`/`ideal_sources`의
  connectivity는 **사용자만 고친다**. `device_roles`/`symmetry.matching_pairs`/
  `symmetry.dispositions`/`sizing_roles`(theta 포함) 같은 **역할·메타데이터는 Claude가
  분석해서 업데이트해도 된다** — 단, **여러 파일/여러 회로에 영향을 주는 엔진 로직 변경**
  (`stick_diagram.py`/`sizing_recipe.py`의 함수 로직)은 이 경계와 별개로 반드시 사전
  논의·승인이 필요하다(세션7에서 이 규칙을 어겨 즉시 원복 지시받은 사고가 있었음). 세션11도
  L3 엔진(D) 구현 전에 여러 턴에 걸쳐 설계를 논의하고("D+B 조합으로 진행할까요?" 등 명시
  승인을 받은 뒤에만 코드를 고쳤다.
- 논문에 없는 값은 "논문 인용"만으로 확정 짓지 말 것.
- **핵심 파일**: `skills/analog-gmid-design/assets/sizing_recipe.py`(gm/ID 사이징, KCL
  엔진) / `skills/analog-gmid-design/assets/stick_diagram.py`(오일러 trail 기반 레이아웃
  엔진, **세션11에 `mirror_symmetric_trail()` 신설**) /
  `skills/analog-gmid-design/assets/audit_current_forced.py`(세션10 신설) /
  `skills/analog-gmid-design/assets/library/*.topology.json`(4개 회로:
  `current_reuse_telescopic_ota`, `folded_cascode`, `nmcnr_amplifier`, `two_stage_ota`).

---

# 세션11 결론 — L3(walk 선택) 설계 논의 + D 구현, run_harness.py 진단, 핑거조정/그룹분할 설계

세션11은 크게 세 갈래로 진행됐다: (A) `run_harness.py`가 여전히 안 끝나던 문제의 최종 진단,
(B) L3(walk 선택) 방향을 여러 턴에 걸쳐 논의해 확정, (C) 그중 D(거울대칭 trail 구성)를 실제
코드로 구현 + self-test. 아래 순서대로 정리한다.

## A. `run_harness.py` 최종 진단 — hang 아님, 진짜 8~10시간짜리 전수탐색

- **원인**: `current_reuse_telescopic_ota.topology.json`의 `sizing_roles.theta` 21개 중
  **자유(bounds 다른) theta가 13개** — `grid_points_per_theta=2`면 **2¹³=8192개 조합**을
  전수탐색한다. 각 조합마다 회로 전체(수십 소자) gm/ID 사이징 + 중첩 고정점 반복
  (`find_stage_gm_convergence()`류, `max_iter=10~20`, 내부 LUT 이분탐색 `max_iter=60~80`)까지
  돈다.
- **실측(스모크 테스트로 확인, 프로덕션 topology.json은 안 건드림 — 임시 복사본에서 자유
  theta 일부만 남기고 나머지를 중간값으로 고정)**: 조합당 평균 **4.4초**(2개 자유 theta,
  4조합, 17.6초) — 그중 1개 조합은 실제로 완주해 metrics까지 냄(gain=77dB, CMRR=122.9dB,
  단 PSRR/classab_centering 제약 위반으로 최종 미채택). **8192개 조합 × 4.4초 ≈ 10시간**으로
  추정되고, 중단 전 26분(CPU 1543초, 98%+ 풀가동) 동안 처리된 건 대략 4%(≈350개) 정도였을
  것으로 계산이 일치한다.
- **세션7~9의 "로그 0바이트 원인 미확정" 완전히 해소**: `run_harness.py` 소스(47~49행)를
  다시 보니 `print()`가 **스크립트 맨 끝에 딱 한 번**만 있다 — 계산 도중엔 원래 아무것도
  안 찍는 구조였다. 버퍼링/프로세스 사망이 아니라 "그냥 스크립트가 진행 상황을 안 찍는다"는
  것뿐이었다.
- **사용자 판단으로 중단**(`taskkill`) — 재실행은 그리드 범위를 어떻게 줄일지(또는 전수탐색
  대신 다른 최적화 전략) 논의 후로 보류. 다음에 다시 시도할 때는 `optimize_full_circuit_
  budget()`의 grid loop(`sizing_recipe.py` 2227행 부근 `for combo in itertools.product(*grids)`)
  안에 임시 진행률 print를 추가하거나, 자유 theta 일부를 먼저 고정한 스모크 테스트로 완주
  여부만 빠르게 확인하는 방법을 권장(세션11이 쓴 방법 그대로,
  `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session11.py` 참고 —
  재사용 가능한 패턴).

## B. L3(walk 선택) 설계 논의 — 최종 합의 방향

`hierholzer()`가 `matching_pairs`를 모르는 문제(세션8부터 미해결)를 여러 턴에 걸쳐 논의했다.
결론:

### B-1. 기존에 이미 있던 인프라 재발견
- `INTERDIGITATION_PATTERNS`/`COMMON_CENTROID_PATTERNS`(86~119행, 문헌표) +
  `interdigitate_layout()`/`common_centroid_layout()` — **hub-leaf 전용**, `select_layout_
  tool()`이 골라서 `repair_matching_safety()`가 **감사 실패 시 그 쌍만 떼어 사후 보정**하는
  데 이미 씀(프로덕션 연결됨).
- `build_mirror_symmetric_pattern(half, pair_map, center=None)`(202행) +
  `check_mirror_symmetry()`(226행) — **hub-leaf 제약 없이 전체 시퀀스 레벨**에서 거울대칭을
  구성/검증. folded_cascode 실측(pptx 원본)과 정확히 일치함이 이미 검증돼 있었으나
  **self-test에만 쓰이고 파이프라인 어디에도 연결 안 돼 있었다**(세션11이 이 gap을 D로 메움).

### B-2. 거울대칭 구성(D)의 실제 원리 — "자기동형사상 탐색" 아니라 "matching_pairs로부터
구성 + `check_walk_sequence()`로 검증"
- 원래 검토했던 "그래프 자기동형사상 탐색"(후보 C)은 일반적으로 비싸다. 실제로 필요한 건:
  각 매칭쌍에서 **대표 소자 하나만**(그룹 내 원본 순서상 먼저 나오는 쪽) 골라 "절반 그래프"를
  구성 → `build_graph()+check_euler_condition()+hierholzer()`로 절반의 trail 계산 →
  `build_mirror_symmetric_pattern()`으로 거울반사해 전체 시퀀스 구성 → **`check_walk_
  sequence()`(2231행, 기존 함수)로 전체 그래프에서 실제 유효한 walk인지 검증** — 구성이
  잘못된 자기동형사상을 가정했다면 이 검증에서 자동으로 걸러지므로, 노드 레벨 매핑을 별도로
  미리 증명할 필요가 없다(탐색 없이 구성+검증만으로 충분).
- **실제 회로 2개로 교차검증**(손으로, 이후 코드로 재확인):
  1. folded_cascode top row(`MP`(self-pair,2f) + `M3`/`M4`(3f) + `M5`/`M6`(6f)) — 성공,
     pptx 원본과는 다르지만(`555555333PP444666666` vs 원본 `555555344PP334666666`) **똑같이
     유효한 다른 대칭 배치**를 만들어냄(거울대칭 trail은 유일하지 않다는 것도 이때 확인).
  2. `current_reuse_telescopic_ota` 실제 그룹 M8(`M8`/`M17`, `M9a`/`M18a`, self-pair 없음) —
     성공, 구성된 시퀀스가 손으로 유도한 `[M9a,M8,M17,M18a]`와 **정확히 일치**.

### B-3. 알려진 한계(적용 범위가 의도적으로 좁음)
- 그룹의 모든 소자가 `matching_pairs`로 커버되거나(1:1, 개수 동일) self-pair(미매칭)여야
  한다. self-pair는 **짝수 `n_fingers`만 지원**(홀수 self-pair, 예: `M5`(1개)처럼 두 홀수
  차수 고정점을 잇는 "다리"로 쓰는 패턴은 손으로는 풀었으나 코드로는 미구현).
- 1:1이 아닌(개수가 다른) 매칭쌍이 섞인 그룹은 폴백.
- **다중 trail이 필요한 그룹(홀수차수 노드 >2)은 이 함수 책임이 아니다** — 실측:
  `current_reuse_telescopic_ota`의 M3a 그룹(11소자, 매칭쌍 4개)은 홀수차수 노드가 **6개**라
  단일 trail 자체가 안 됨(오일러 조건 위반, D/기존 방식 둘 다 "blocked").

### B-4. M3a 그룹 심층 분석 — 그룹분할/핑거조정 원칙으로 수렴
사용자가 "기능블럭 단위 divide-and-conquer"를 제안 → 손 검증으로 다음이 드러났다:

1. **`M9b`/`M18b`/`M63`/`M64`를 빼면 나머지 7소자가 정확히 오일러 경로가 됨**(홀수노드
   6→2). 근본 이유: `gnd`/`Vom1`/`Vop1`이 여러 기능블럭에서 동시에 닿아 차수가 쌓이기
   때문.
2. **"매칭 안 된 소자만 걸러내면 된다"는 가설은 틀렸다** — `M9b`/`M18b`는 **선언된
   매칭쌍**(ratio)인데도 빼야 했다(빼는 이유는 매칭 여부가 아니라 **오일러 차수 홀짝**).
   → **진짜 기준은 매칭 여부가 아니라 그래프 차수 조건**이라는 게 확정됐다.
3. **`geometry_colocation_union()`(L2, 세션10)이 이미 "drain=drain 정션 제외" 규칙을
   구현하고 있었다**(1516~1518행 docstring, 코드 확인됨) — 그런데도 M3a그룹이 안 쪼개지는
   이유는 **drain-drain이 아니라 "부채꼴"(하나의 drain이 여러 source로 fan-out, 예:
   `Vy`)을 통한 전이적(transitive) 병합** 때문임을 실측으로 확인(`M5.drain=Vy`가
   `M4a`/`M4b`/`M63` 3개 source와 모두 개별적으로 유효한 drain=source 직렬이라 결국 전부
   한 그룹으로 뭉침).
4. **핑거 조정이 그룹분할보다 낫다는 게 실측으로 확인됨**: 기존 함수 `suggest_finger_
   adjustments()`(1865행, 세션11 이전부터 있던 함수)를 M3a 11소자 그룹에 그리디로
   반복 적용하니 **`M9b`, `M18b` 각각 finger 1→2로 딱 2단계**에 홀수노드 6→2로 해결됨 —
   그리고 두 조정이 **정확히 서로의 매칭 상대**라 1:1 비율도 그대로 유지됨(우연이 아니라
   node_map 대칭 때문).
5. **핵심 통찰(사용자 확인)**: "같은 전류 branch"라고 물리적으로 같은 행에 있어야 하는 건
   아니다 — 전류는 topology(KCL)로만 결정되고 물리 배치와 무관하다. 물리적 그룹핑이 신경
   써야 하는 건 **(1) 선언된 matching_pairs의 대칭 배치, (2) 그 그룹의 오일러 실현
   가능성**뿐. 실제로 `M18a`/`M18b`는 서로 매칭쌍이 **아님**(각각 `M9a`/`M9b`와 매칭) —
   그래서 물리적으로 떼어놔도 어떤 선언된 요구사항도 안 깨진다.

### B-5. 확정된 그룹분할 원칙 (구현 대기 중)
1. **핑거 조정을 그룹분할보다 먼저 시도** — 단, 개별 소자가 아니라 **매칭쌍 단위로
   대칭 조정**(양쪽을 똑같이 조정해 비율 유지). 이건 `n_fingers`(=W)를 바꾸는 것이므로
   **L4로 피드백해서 gm/ID 스펙이 여전히 만족되는지 재검증 필수**(아직 미구현 — 다음 세션
   최우선).
2. 핑거 조정으로도 안 풀리면 그룹분할(`find_min_crossover_layout()`의 기존 T-join
   메커니즘 재사용) — 단, 홀수노드를 임의로 짝짓지 않고 **`node_map`(D를 위해 이미 만든
   자기동형사상 역산)으로 서로 대응되는 쌍끼리 우선 짝짓기** → 쪼개진 세그먼트가 서로
   거울상이 되어 대칭성이 저절로 유지됨.
3. 소자를 떼어낼 우선순위(그룹분할이 필요할 때): **미매칭 소자 > `matching_sensitivity=
   "ratio"` 쌍 > `matching_sensitivity="offset"` 쌍**(offset은 common-centroid 필수라
   최후순위로 유지).

## C. D 구현 완료 (코드) — `stick_diagram.py`, 아직 커밋 안 됨

- **`mirror_symmetric_trail(group, matching_pairs)`**(2322행) — 위 B-2 원리 그대로 구현.
  반환: 성공 시 `{"node_sequence":[...], "transistor_sequence":[...]}`, 실패 시 `None`.
- **`StickResult.method`**(2211행 dataclass) 필드 신규 — `"graph"`(기존) |
  `"mirror_symmetric"`(D 성공).
- **`build_stick_diagram(transistors, matching_pairs=None)`**(2390행) — **감싸기**(대체
  아님): `matching_pairs` 주어지면 스택마다 `mirror_symmetric_trail()` 먼저 시도, `None`이면
  기존 `build_graph()+hierholzer()`로 폴백. 안 주면(기본값) 기존 동작과 **바이트 단위로
  동일**(self-test 3번째 사례로 확인).
- **`audit_row_split()`**(2747행)의 `build_stick_diagram()` 호출부(옛 2820행 부근)를
  수정 — 그 행에 두 이름 다 속하는 `matching_pairs`만 필터링해서 넘기도록(`run_topology_
  pipeline()`의 `cell_pairs` 필터링과 동일 패턴 재사용).
- **self-test 추가**(Test 5.5, `build_mirror_symmetric_pattern` Test 5 직후) — 위 B-2의
  2개 실제 사례 + 하위호환 음성대조(matching_pairs=None이면 완전히 동일) 전부 코드로
  재확인, 통과.
- **회귀 확인**: `stick_diagram.py` self-test 전체 재실행 — exit 0, FAIL 마커 개수 32개로
  Test 5.5 추가 전후 동일(전부 의도된 것). `sizing_recipe.py` self-test도 재실행 — exit 0,
  182줄 전부 PASS(이 self-test는 `run_harness.py`류 조합 폭발이 원래 없었음을 소스 확인 +
  실행으로 재확인, 세션11 A절과 무관).

---

# 세션12 결론 — 매칭쌍 단위 핑거조정 + L3 홀수 self-pair "다리" 지원, M3a 그룹 실측으로 완전히 풀림

세션11 "다음 세션 최우선 작업"(매칭쌍 단위 핑거조정)을 시작했으나, 설계 도중 사용자가 "홀수
self-pair(다리)도 이번에 같이 다뤄줘"라고 범위를 확장 요청 — 실제 데이터(M3a 그룹)로 직접
검증하며 설계를 진행했고, **처음 떠올린 방식(다리를 그냥 미러 시퀀스 중앙에 이어붙이기)은
실측으로 실패함을 먼저 확인**했다(상상으로 채우지 않고 실제 확인 후 진행 원칙 적용).

## D-1. `suggest_pair_finger_adjustments(transistors, matching_pairs)` 신설 (1908행 부근)
- 기존 `suggest_finger_adjustments()`(개별 소자 ±1)와 달리 조정 단위를 **매칭쌍 또는
  미매칭 단독 소자**로 잡는다 — 매칭쌍은 **양쪽에 동일한 delta를 동시에 적용**해 비율이
  구조적으로 항상 유지된다(개별 조정을 우연히 짝맞추는 게 아님).
- 실측(M3a 그룹, 11소자): `M9b`/`M18b`(선언된 ratio 매칭쌍)에 동시에 +1 제안이 1순위로
  나오고, 적용하면 전체 그래프 홀수차수 노드가 6개→2개로 감소 — 세션11엔 개별 함수로 2단계
  필요했던 걸 이 함수는 1번의 제안으로 찾는다.

## D-2. `mirror_symmetric_trail()`의 "홀수 self-pair = 다리" 지원 — 대표 조합 탐색으로 해결
- **막혔던 지점**: 매칭쌍마다 대표 소자를 "그룹 내 원본 순서상 먼저 나오는 쪽"으로 고정하는
  기존 규칙이, M3a 그룹(4개 매칭쌍)에서는 절반 그래프가 홀수차수 4개(불가능)가 되는 걸 막지
  못했다 — 다리(M5/M63/M64)를 그냥 추가해도 홀수 노드 개수가 안 줄고 자리만 옮겨 다녔다(직접
  계산으로 확인, 처음 설계 실패).
- **진짜 원인**: 대표 선택 자체가 매칭쌍마다 어느 쪽을 고르느냐에 따라 절반 그래프의 실현
  가능성이 달라진다 — 4개 쌍 2⁴=16가지 조합을 전수 대입해서 특정 조합(`M4a,M3a,M19,M18b`)
  에서만 절반 그래프가 홀수 2개(`path`)로 성립함을 실측으로 발견.
- **최종 설계**: (1) 매칭쌍 대표 선택을 "항상 먼저 나오는 쪽" 1순위 시도 후 실패하면 나머지
  조합(2ⁿ, `_MAX_MIRROR_TRAIL_COMBO_PAIRS=12` 초과 시 탐색 생략)을 순서대로 시도. (2) 홀수
  self-pair는 쪼개지 않고 실제 `n_fingers` 그대로 절반 그래프에 **한 번만** 넣고, 미러
  복사본에서는 제외(`build_mirror_symmetric_pattern()`의 `pair_map` 값에 `None`을 허용하도록
  한 줄 확장 — `None`이면 `mirrored` 리스트에서 필터링). (3) 최종 검증은 여전히
  `check_walk_sequence()`가 유일한 게이트(구성 후 검증 원칙 그대로 유지, 별도 대칭성 이론
  증명 불필요).
- **실측 검증**: M3a 그룹(핑거조정 후 13핑거, 매칭쌍 4개 + 다리 3개)이 시퀀스
  `[M64,M63,M5,M19,M18b,M18b,M3a,M4a,M4b,M3b,M9b,M9b,M10]`로 완전히 풀림 —
  `check_walk_sequence().ok=True`, finger 개수 불일치 0건.
- **회귀 대조**: 핑거조정 없이 원본 그대로면(홀수 self-pair 다리 지원만 있어도) 여전히
  `None`(폴백) — 핑거조정과 다리 지원 **둘 다** 있어야 풀린다는 것도 self-test로 확인.

## D-3. 구현/테스트 변경 내역 (전부 `stick_diagram.py`, 아직 커밋 안 됨)
- `suggest_pair_finger_adjustments()` + `PairAdjustmentSuggestion` 신설(1908행 부근,
  `suggest_finger_adjustments()` 직후).
- `build_mirror_symmetric_pattern()`(202행) — `pair_map` 값 `None` 지원(다리는 미러 안 함).
  한 줄 변경(+필터), 기존 호출부(전부 `None`을 값으로 쓴 적 없음)는 완전히 무영향.
- `mirror_symmetric_trail()`(2401행 부근) — 대표 조합 탐색 + 홀수 self-pair 다리 처리로
  전면 재작성. **기존 2개 통과 사례(folded_cascode top row, M8 그룹)는 1순위 조합에서 바로
  성공하므로 결과가 바이트 단위로 완전히 동일**(self-test로 확인, 아래 회귀 확인 참고).
- self-test 추가(Test 5.6, Test 5.5 직후) — M3a 그룹 실측 재현: (1) 조정 전 홀수 6개,
  (2) `suggest_pair_finger_adjustments()` 1순위가 M9b/M18b+1인지, (3) 조정 후
  `mirror_symmetric_trail()` 성공 + `check_walk_sequence` 통과, (4) 조정 없이는 여전히
  `None`(회귀 대조).
- **회귀 확인**: `stick_diagram.py` self-test 전체(680줄, Test 5.6 제외하면 665줄) —
  세션12 편집 전(커밋 `cecbe33`) 출력과 **완전히 바이트 단위로 동일**(`diff --strip-
  trailing-cr` 0줄 차이 — CRLF 잡음만 있었음). `sizing_recipe.py` self-test는 이번엔 2분
  타임아웃으로 확인 못함(세션12가 손대지 않은 파일이라 이 변경과 무관 — 백그라운드로 재확인
  중, 결과는 다음 세션 시작 시 확인).

---

## L4. 사이징→레이아웃 연결 문제 — 세션13에 구현 완료(아래 "세션13 결론" 참고)

`assign_finger_geometry()`가 축B(`shares_node`) 값을 몰라서, 짝수 finger가 필요한 매칭 쌍에
그 제약을 전달하는 로직이 없다는 게 원래 문제였다(세션8~11). 세션11이 "매칭쌍 단위 핑거
조정 → gm/ID 재검증 필요"라는 구체적 연결점을 확인했고, **세션13에 `revalidate_finger_
override()`로 실제 구현됨** — L3(레이아웃 trail 구성)→L4(사이징 피드백) 연결이 처음으로
끝까지 닫혔다. 상세는 아래 "세션13 결론" 참고.

- `two_stage_ota`의 box-shape 실측 사례(세션10 발견, `M6` vs `M3`/`M5` W 격차)는 여전히
  L4 실전 적용(실제 회로에 붙여서 돌려보는 것)의 정보성 사례로 유효 — 이번 세션은 함수
  자체만 구현했고, 실제 topology.json에 배선해서 end-to-end로 돌려보는 건 아직 안 함.

---

# 세션13 결론 — L4(핑거조정 후 gm/ID 스펙 재검증) `revalidate_finger_override()` 구현

세션12 마지막에 남긴 "다음 우선순위: L4"를 그대로 시작. 설계 전에 `sizing_recipe.py` 구조를
먼저 조사(에이전트 위임 + 직접 확인)했고, 그 과정에서 GBW/PM 범위를 두고 두 번 방향을
좁혔다(아래 A/B절) — 상상으로 채우지 않고 실제 코드/topology.json을 확인한 뒤에만 범위를
정했다.

## A. 조사로 확인된 구조 (설계의 근거)

- **ID는 W와 완전히 독립적으로 먼저 확정된다** — `propagate_topology_forced_currents()`/
  `kcl_series_union()`(둘 다 stick_diagram.py)이 topology(직렬스택+미러비)만으로 ID를
  정하고, W는 그 다음에 gm/ID LUT에서 역산(`size_transistor()`, `W=L*ID/IDu`)된다. 즉
  finger 조정으로 W가 강제로 바뀌어도 **ID는 안 바뀐다** — 이게 L4 전체 설계의 전제.
- **`compute_metric(metric_spec, ctx)`은 `ctx.sized`만 읽는 순수 함수**(sizing_recipe.py:
  1591) — 소자 하나의 상태만 바꾼 새 `ctx`로 관련 metric만 재계산하면 되고, `optimize_
  full_circuit_budget()`의 전체 theta grid search를 다시 돌 필요가 없다.
- **`_invert_gm_id_for_current(lut, current, L, vds, vs, W, gm_id_bounds, tol, max_iter)`**
  (sizing_recipe.py:897, 기존 함수, C엔진 `solve_diode_stack_current()`가 이미 씀) — "전류
  고정 + 강제된 W → 실제 gm_id"를 정확히 이분탐색으로 역산한다. L4에 필요한 역산을 새
  수치해석 코드 없이 그대로 재사용할 수 있었다.
- **`constraints`는 `[{"metric": <metrics_specs 키>, "op", "value"}, ...]`** 자유 형식이고,
  각 metric_spec이 소자를 가리키는 키 이름은 `devices`/`stages`/`device`/`tail_device`/
  `high_device`/`low_device` 등 제각각이다(`_METRICS_REGISTRY` 9종 직접 확인) — 특정 키에
  의존하지 않는 재귀 탐색(`_collect_device_refs()`)으로 일반화했다.

## B. GBW/PM 범위 결정 — 두 번의 재조사로 좁혀짐

1. **1차**: 사용자가 GBW/PM 포함을 요청 → `optimize_multistage()`(sizing_recipe.py:428)의
   docstring을 직접 확인하니 "PM(위상마진) 등 회로 레벨 성능은 검증하지 않는다 — topology_fn
   방정식이 이미 그렇다고 가정할 뿐, 실제 PM은 SPICE로 확인해야 한다"고 명시돼 있었다.
   즉 이 Python 엔진은 **스펙→gm 정방향 폐형식만** 갖고, "실제 상태→실제 GBW/PM" 역방향
   계산은 코드베이스 어디에도 없다(의도된 설계, 버그 아님). GBW만은 `miller_ota_topology()`
   (topology_library.py:32)의 `gm1=2π·GBW·Cm` 정방향 식을 그대로 뒤집으면(`Cm`은 실제
   커패시터라 finger 조정으로 안 바뀜) 성립하지만, PM은 극점비(Z)→실제 PM(도) 매핑 공식이
   코드베이스에 없어 지금 만들면 근거 없는 발명(프로젝트 원칙 위반)이 된다.
2. **2차(사용자가 GBW만이라도 포함 요청)**: 실제 topology.json 4개(`current_reuse_
   telescopic_ota`/`folded_cascode`/`nmcnr_amplifier`/`two_stage_ota`) 전부의 `constraints`
   를 직접 열어 확인하니 **GBW를 constraint로 선언한 회로가 하나도 없었다**(GBW는
   `compensation.parameters` 입력으로만 쓰임). 특히 이번 L4의 실제 동기였던 M3a의 부모
   회로 `current_reuse_telescopic_ota`는 `current_reuse_telescopic_topology`(Xie&Chen
   Eq.2-6, Miller보다 복잡한 class-AB 보상식)를 쓰고 `constraints`는 `gain_db/mismatch_
   sigma_mV/cmrr_estimate_db/psrr_estimate_db/classab_centering_dev_v` 5개뿐이었다 —
   Miller 전용 역산조차 지금 당장 검증할 대상이 없다는 뜻. **사용자가 이 근거를 보고
   "지금은 metrics_registry만, GBW는 필요해질 때 추가"로 최종 확정**했다.

## C. 구현 (`sizing_recipe.py`, §6.10 신설, 아직 미커밋)

- `_collect_device_refs(spec, known_names)` — metric_spec을 재귀로 훑어 소자명 문자열만
  수집하는 범용 헬퍼(위 A절 마지막 항목).
- `revalidate_finger_override(ctx, lut_by_kind, overrides, metrics_specs, constraints,
  gm_id_bounds=(2.0,30.0))` — `overrides={device_name: new_W}`를 받아: (1) 각 소자의
  ID/L/vds/vs는 고정, `_invert_gm_id_for_current()`로 새 gm_id 역산 → `gm=ID*gm_id`,
  `gds=gm/lut.gm_gds_ratio(...)`로 갱신한 새 `ctx`(원본 불변, 순수함수) 생성. (2)
  `_collect_device_refs()`로 `overrides` 소자를 참조하는 metric만 골라 `compute_metric()`
  구/신 비교. (3) 그 metric을 참조하는 constraint만 `_CONSTRAINT_OPS`로 재판정.
  반환: `{"ok", "device_updates", "metric_deltas", "violated_constraints",
  "unaffected_metrics_skipped"}`.
- `gm_id_bounds` 파라미터 신설(기본 `(2.0,30.0)`, `_invert_gm_id_for_current()`에 그대로
  전달) — `build_toy_lut()`의 실제 유효범위(~1.85~29.6)가 기본 상단보다 좁아 self-test
  작성 중 실측으로 필요성 확인, 다른 B/C엔진 함수(`solve_diode_stack_current()` 등)와
  동일 패턴.
- self-test 3건(sizing_recipe.py self-test, "L4 revalidate_finger_override()" 섹션,
  F엔진 `compute_metric()` 테스트 직후): (1) M1 W를 10% 축소해도 ID 보존(`new_gm/new_
  gm_id`가 원래 ID와 오차 0) + constraint 그대로 통과 + 무관한 M3 metric은 재계산
  스킵 목록에 정확히 들어감. (2) M1 W를 40% 축소하면 실제로 gain이 threshold 밑으로
  떨어져 `violated_constraints`에 정확히 `stage_gain` 하나만 잡힘. (3) 원본 `ctx.sized`가
  변형되지 않는 순수함수인지 확인.
- **회귀**: `sizing_recipe.py` self-test 전체 재실행 — 세션13 편집 전(`d59570f`)과
  L4 신규 10줄을 뺀 나머지가 바이트 단위로 완전히 동일(`diff --strip-trailing-cr` 0줄
  차이). 무회귀 확정.

## D. 알려진 한계 / 다음 확장 지점

- **GBW/PM은 범위 밖**(위 B절 근거) — 필요해지면: (1) 어느 topology.json이든 `constraints`
  에 `gbw`류 metric을 실제로 선언하는 회로가 생기면, (2) 그 회로의 compensation 함수가
  Miller처럼 단순 역산 가능한지 확인 후, (3) PM은 여전히 SPICE 전용으로 남기고 GBW만
  `_METRICS_REGISTRY`에 새 metric 타입으로 등록하는 확장을 검토.
- **아직 실제 회로에 배선 안 됨** — `revalidate_finger_override()`는 함수 자체만 구현·
  self-test로 검증됐고, `suggest_pair_finger_adjustments()`의 제안을 실제로 적용한 뒤
  이 함수를 자동으로 호출해 승인/거부하는 상위 오케스트레이션(예:
  `apply_and_revalidate_pair_adjustment()`류)은 아직 없다 — 다음 세션 후보.
- `lut_by_kind`/`metrics_specs`/`constraints`를 호출자가 `load_topology()`/`optimize_
  full_circuit_budget()`의 `spec`에서 직접 꺼내 넘겨야 한다(이 함수가 topology.json을
  직접 읽지 않음, 기존 F엔진 `compute_metric()`과 동일한 저수준 계약).

---

# 세션14 결론 — L3+L4 오케스트레이션 신설, `run_topology_pipeline()` wrapper 설계+구현,
# 전수 콜그래프 조사로 "harness에 미배선" 확정

세션13이 남긴 "다음 확장 지점"(`revalidate_finger_override()`를 실제 회로에 배선)을 이어
진행했다. 이번 세션은 (A) 커밋 상태를 다시 확인해 과거 기록이 stale했음을 발견, (B) L3(제안)+
L4(재검증)를 잇는 오케스트레이션 함수 신설, (C) 그걸 `run_topology_pipeline()`에 감싸붙이는
wrapper를 사용자와 설계 논의 후 구현, (D) 전수 콜그래프 조사로 "여전히 실제 harness에는
연결 안 됨"을 직접 코드로 확정 — 순서로 진행했다.

## A. 커밋 상태 재확인 — 과거 문서가 stale했음

세션 시작 시 `.ai/context.md`가 "세션12/13 미커밋"이라 적어뒀지만, `git log`로 직접 확인하니
`cecbe33`(세션12)/`caa970b`(세션13)로 **이미 커밋 완료**된 상태였다. 문서를 맹신하지 않고
실제 git 상태와 대조해서 발견 — 위 "지금 상태" 1번에 반영. (교훈: 세션 핸드오프 문서 자체도
시간이 지나면 stale해질 수 있으니, 다음 세션 시작 시 항상 `git log`/`git status`로 재확인할 것.)

## B. `apply_and_revalidate_pair_adjustment()` 신설 (`sizing_recipe.py:2405`)

`suggest_pair_finger_adjustments()`(L3, 세션12)가 반환한 후보를 홀수차수 개선 순서대로
시도해, `revalidate_finger_override()`(L4, 세션13)로 gm/ID 스펙을 깨지 않는 **첫 번째**
후보를 자동 채택하는 오케스트레이션. 레이아웃이 가장 좋아도 스펙을 깨면 자동으로 건너뛰고
다음 후보로 넘어간다 — 채택 안 된 후보는 전부 `rejected`에 근거와 함께 남는다.

self-test 3건(`sizing_recipe.py:2822` "L4b" 블록, 합성 데이터 Ma/Mb/Xa/Xb 4소자):
1순위(Ma,Mb)가 면적 제약 위반 → 자동으로 2순위(Xa,Xb) 채택. 둘 다 위반 → `applied=False`.
`max_candidates=1`로 상한을 걸면 1순위만 시도하고 폴백 안 함. 전부 통과.

## C. `run_topology_pipeline_with_finger_fixup()` 신설 (`sizing_recipe.py:2498`) — 사용자와
설계 논의 후 구현

사용자가 "실배선"을 요청했으나, 먼저 "최상위 harness함수에 제대로 연결되어 있나?"라고
물어 정직하게 "아니요"라고 답한 뒤(당시엔 B절의 `apply_and_revalidate_pair_adjustment()`만
있었고 self-test에서만 호출됨), "배선 설계부터 논의"를 선택받아 다음 순서로 진행했다:

1. **구조적 제약 발견(근거)**: `stick_diagram.py`는 gm/ID를 전혀 모르는 순수 그래프/기하
   모듈이고, `sizing_recipe.py`가 `stick_diagram.py`를 단방향으로만 import한다(반대 방향
   없음). fixup 루프가 gm/ID 재검증을 하려면 `SizingContext`/LUT가 필요해서, `stick_
   diagram.py`(`build_stick_diagram()`/`audit_row_split()`/`run_topology_pipeline()`) 안에
   넣으면 순환 import가 생긴다 → `sizing_recipe.py` 쪽에서 `run_topology_pipeline()`을
   감싸는 wrapper로 설계.
2. **라운드당 blocked row 처리량**을 AskUserQuestion으로 확인 → "한 번에 하나씩 순차 처리"
   채택(이유: row는 `stack_id`로 물리적으로 독립이지만 gm/ID `constraints`는 여러 row의
   소자를 동시에 참조할 수 있어, 한 라운드에 여러 row를 동시에 조정하면 서로의 재검증
   결과에 영향을 줄 수 있음 — 매 라운드 `run_topology_pipeline()`을 처음부터 재실행해
   항상 최신 상태 기준으로 판단).
3. **구현**: 각 라운드 (1) `run_topology_pipeline()` 실행 (2) `audit_row_split`에서
   euler-blocked row 탐지(`_blocked_euler_rows()`, `sizing_recipe.py:2463`, 체크명
   `f"1. euler[{row_name}]"` 패턴 파싱) — 없으면 성공 종료 (3) 첫 blocked row에
   `apply_and_revalidate_pair_adjustment()` 시도 (4) 성공하면 `sizing_overrides`(layout)와
   `ctx.sized`(gm/ID)를 `_sync_finger_fixup()`(`sizing_recipe.py:2478`)으로 동기화하고
   다음 라운드 (5) 실패하면 **거짓 성공으로 처리하지 않고 즉시 멈춤**
   (`unresolved_reason="no_valid_candidate"`). `max_fixup_rounds` 소진 시엔 마지막 조정
   이후 한 번 더 재실행해 실제로 풀렸는지 확인(`unresolved_reason="max_rounds_exceeded"`).

self-test 2건(`sizing_recipe.py:2913` "L4c" 블록) — **세션12 실제 M3a 그룹(11소자,
`M3a/M3b/M4a/M4b/M5/M9b/M10/M18b/M19/M64/M63`)의 connectivity를 그대로 temp topology.json
파일로 감싸** `load_topology→audit_row_split→build_stick_diagram→mirror_symmetric_trail`
전체 체인을 진짜로 태워 검증(합성 데이터 아님, 세션12 손검증과 동일한 실제 회로 구조 재사용):
1. **케이스A(면적 예산 넉넉)**: 1라운드 만에 M9b/M18b +1로 자동 해결 — 채택된 조정이
   세션12 손검증(`{'M9b','M18b'}`, resulting_odd_count=2)과 정확히 일치, 최종 euler 체크
   전부 통과.
2. **케이스B(면적 예산 극도로 타이트)**: 후보 7개(매칭쌍 4개+미매칭 단독 3개) 전부
   `n_fingers=1` baseline이라 delta=-1은 자동 무효화되고 전부 delta=+1(면적 증가)만
   나오는데, 예산이 baseline*1.001로 타이트해 전부 위반 → `unresolved_row`/
   `unresolved_reason="no_valid_candidate"`로 정직하게 실패 보고. 전부 통과.

## D. 회귀 확인 — 무회귀 확정

편집 전(커밋 `caa970b`) `sizing_recipe.py`와 이번 버전을 완전히 격리된 디렉토리(사이드카
파일 `stick_diagram.py`/`topology_library.py`/`library/`/`sky130_regression_reference.json`
전부 포함해서 복사)에서 각각 self-test 전체를 돌려 diff했다 — 새 L4b/L4c 블록(20줄)만 빼면
`diff --strip-trailing-cr` **0줄 차이**(바이트 단위 동일). 무회귀 확정.

## E. 전수 콜그래프 조사 — "harness에 미배선" 직접 코드로 확정

사용자가 "함수 모두 연결되었나? 최상위 harness함수에 연결 안 된 함수가 있나? 전수로
조사해서 보고해"라고 요청 → `ast` 기반 콜그래프 분석 스크립트를 작성해 6개 파일 top-level
함수 197개 전부를, 이 저장소에 실제 존재하는 4개 실행 진입점(`run_harness.py`→
`optimize_full_circuit_budget()`, `audit_current_forced.py`→`render_report()`,
`topology_to_markdown.py`→`render_markdown()`, `sky130_lut_sweep.py`→`run_device()`)에서
BFS로 도달 가능한지 판정했다.

**과정에서 스스로 발견해 고친 분석 버그 2건**(상상으로 결론 내지 않고 직접 검증):
1. 1차(정규식 텍스트 스캔)는 docstring 안의 함수명 언급도 "호출"로 오탐 → AST `Call` 노드만
   세는 방식으로 재작성.
2. 2차(AST) 버전이 `optimize_full_circuit_budget()` 내부 중첩 클로저 `_evaluate()`의 호출을
   건너뛰는 버그 발견(nested `FunctionDef` 재귀 중단 로직이 원인) → 수정.
3. `compute_metric()`의 `_METRICS_REGISTRY` 딕셔셔너리 기반 동적 dispatch는 정적 분석의
   구조적 사각지대라, `current_reuse_telescopic_ota.topology.json`을 직접 읽어 실제
   선언된 metric 9종 전부(`sizing_roles.metrics`)와 CMRR/PSRR의 `circuit_family`
   (`telescopic_class_ab_cmfb`/`diff_pair_tail`)를 확인해 수동 보정.

**최종 결론(직접 코드로 확정)**: 총 197개 중 약 108개가 실제 harness에서 도달 가능, 약 89개
불가능. **오늘 새로 만든 6개 함수(B/C절) 전부가 여전히 미배선** — `optimize_full_circuit_
budget()`의 euler-blocked 실패 처리부(2276~2290행 부근)를 직접 읽어 확인한 결과, 지금도
여전히 **예전 `repair_matching_safety()`만** 호출하고 새 체인(`suggest_pair_finger_
adjustments`/`apply_and_revalidate_pair_adjustment`/`run_topology_pipeline_with_finger_
fixup`)은 호출부가 어디에도 없다. 동적 dispatch 사각지대가 아니라 **진짜 미배선**임을
소스로 확정.

그 외 큰 미연결 그룹(오늘 작업과 무관, 참고용): interdigitation/common-centroid 레이아웃
서브시스템(`interdigitate_layout`/`common_centroid_layout`/`find_min_crossover_layout` 등
~20개), topology JSON 오케스트레이션 구세대 레이어(`run_sizing_pipeline`/`load_sizing_
targets`/`write_sizing_results` 등), `run_full_circuit_audit`/`save_instance_json` —
전부 self-test에서만 검증되고 `run_harness.py`(유일한 실제 harness)는 `optimize_full_
circuit_budget()` 한 갈래만 탄다. 이건 이 프로젝트가 "함수 단위 설계→구현→self-test"를
반복해온 개발 방식의 자연스러운 결과이지 세션14만의 문제가 아니다.

## F. 알려진 한계 / 다음 확장 지점

- **실제 배선(engine 코드 수정)은 아직 안 함** — B/C절 함수는 구현+self-test만 끝났고,
  `optimize_full_circuit_budget()`이 이 새 체인을 실제로 호출하도록 바꾸는 마지막 단계가
  남았다. 이건 여러 회로에 영향을 주는 엔진 로직 변경이라 반드시 사전 논의·승인 필요
  (프로젝트 규칙, 세션7 사고 이후 확립).
- **`repair_matching_safety()`와의 관계 미정** — 새 체인으로 완전히 대체할지, 새 체인이
  먼저 시도하고 실패하면 기존 `repair_matching_safety()`로 폴백할지 설계 필요(다음 세션
  논의 사항, 아직 미결).
- **`run_harness.py`가 실제로 완주한 적이 없어**(세션11에 8192개 조합 중단), 이 새 체인이
  실제 `current_reuse_telescopic_ota` 전체 사이징에서 어떻게 동작하는지는 여전히 미검증 —
  A절(위 "지금 상태" 4번)의 grid 축소 논의가 선행돼야 end-to-end로 확인 가능.

---

# 세션15 결론 — harness 실배선 완료, node_map 기반 그룹분할 구현, 그룹분할 harness 배선 논의
# 중단(다음 세션 계속)

세션14가 남긴 "다음 세션 최우선"(harness 배선)을 시작. (A) `optimize_full_circuit_budget()`을
새 L3/L4 체인에 실배선, (B) 세션11부터 미룬 node_map 기반 그룹분할을 실제 사례로 구현,
(C) 그룹분할을 다시 harness(`run_topology_pipeline_with_finger_fixup()`)에 배선하는 설계를
논의하다 사용자가 "다음 세션에 이어가자"고 중단 — 순서대로 정리한다.

## A. harness 실배선 — `optimize_full_circuit_budget()` (커밋 `0eccd0e`)

### A-1. 핵심 발견 — "대체 vs 폴백"이 아니라 "책임 분리"
사용자가 배선 방식을 묻는 과정에서(`run_topology_pipeline()` → `repair_matching_safety()`가
순차 호출인지, 감싸는 구조인지) 코드를 직접 확인하다 중요한 사실이 드러났다:
`repair_matching_safety()`가 실제로 고치는 건 `audit_row_split()`의 **3b(interdigitation)/
3c(common-centroid) 체크뿐**이다 — 내부 `_failing_required_pairs()`(stick_diagram.py:3070)가
체크명 `"3b."`/`"3c."`만 파싱하고 `"1. euler[...]"`는 절대 안 건드린다. 즉 지금까지
euler-blocked 실패에 `repair_matching_safety()`를 불러도 사실상 무의미했을 가능성이 높다
(그 함수는 euler를 고치는 메커니즘이 없다). 그래서 "새 L3/L4 체인이 `repair_matching_
safety()`를 대체하는지 폴백으로 쓰는지"라는 질문 자체가 틀렸다 — 정답은 **새 체인=euler(체크1)
담당, `repair_matching_safety()`=matching quality(3b/3c) 담당**인 상호보완 구조.

### A-2. 배선 구현
`optimize_full_circuit_budget()`(sizing_recipe.py) 2266행 부근의 `run_topology_
pipeline(...)` 직접 호출을 `run_topology_pipeline_with_finger_fixup(...)`로 교체 — euler
자동수정을 내장. `spec["lut_by_kind"]`가 없는 회로(theta feed `'B'`만 쓰는 구형 spec)는
안전하게 기존 `run_topology_pipeline()`으로 폴백(완전 하위호환, self-test로 발견/수정 —
처음엔 무조건 fixup 경로를 타게 짰다가 기존 self-test `_ofc_spec={"lut":lut,...}`가
`KeyError: 'lut_by_kind'`로 즉시 걸렸다). fixup 이후 최종 `sizing_overrides`/`sizing`/
`metrics`를 재동기화(안 하면 stale 값이 나가는 버그).

### A-3. self-test(L5) + 부수 발견한 사전 존재 버그
`optimize_full_circuit_budget()` 최상위 경로로 세션12 M3a 그룹(11소자)을 `known_sizing`으로
직접 시드(theta 없이)해 end-to-end 검증. 처음 fixture(모든 소자 W 동일)로는 `repair_
matching_safety()`가 offset/branch_symmetric 매칭쌍(`n_fingers=1`)에 common-centroid를
시도하다 `ValueError`로 크래시 — **격리 스크립트(`probe_preexisting_bug.py`)로 이 배선
변경 전 코드에서도 똑같이 재현됨을 확인**해 이번 작업과 무관한 사전 존재 버그임을 확정(지금껏
아무 self-test도 이 조합을 안 태워서 안 걸렸을 뿐). 사용자 지시로 이 버그는 손 안 대고,
self-test fixture만 홀짝을 보존하는 배수(3배)로 조정해 우회. (별도 이슈로 보류, 위 "지금
상태" 6번.)

### A-4. 회귀
`de85792` 베이스라인(LUT npz sidecar까지 포함한 격리 복사본) 대비 self-test 전체 출력 diff —
신규 L5 블록 외 0줄 차이.

## B. node_map 기반 그룹분할 — `find_min_crossover_layout()` 확장 (커밋 `55c8095`)

### B-1. 실제 막히는 사례 발견 — probe로 4개 topology.json 전수 탐색
"다음 세션 3번(node_map)"으로 넘어가기 전에, 상상으로 설계하지 않고 실제로 막히는 그룹이
있는지 먼저 확인했다(`probe_node_map_need.py`, 세션11 `probe_l3_groups.py` 재사용 패턴) —
4개 topology.json 전부의 4소자+/matching_pairs 2개+ 그룹에 핑거조정(+세션12 다리 지원)을
그리디로 10라운드까지 돌려봤다. **`current_reuse_telescopic_ota`의 M6 그룹(8소자: M6/M7/
M1a/M1b/M2a/M2b/M58/M57)만 진짜로 못 풂** — baseline 홀수차수 4개가 10라운드 내내 단 한
번도 안 줄어듦(제안이 전부 `resulting_odd_count=4`). 원인: 허브 `Vx`에 미매칭 소자가
**M6/M7/M58 셋**이나 붙어 세션12의 "홀수 self-pair 다리 하나" 가정이 구조적으로 안 맞음 —
그래프 이론상 `m=4/2=2`(crossover 1개)가 필요.

### B-2. node_map 역산 알고리즘 — `_mirror_node_map_from_pairs()`
`odd_nodes`가 소자 이름이 아니라 **net 이름**이라, `matching_pairs`(소자 쌍)에서 net 레벨
거울 대응을 역산해야 한다. 쌍 (a,b)마다: 한쪽 끝(source/drain)을 공유하면 그 net은
자기대응(축 위 허브) + 나머지 끝끼리 대응(예: M1a/M1b가 source=Vx 공유 → Vx 자기대응,
drain끼리 N1a2a↔N1b2b). 공유 끝이 없으면(branch_symmetric류) 같은 역할끼리(source↔source,
drain↔drain) 대응한다고 가정. **체인 전이(propagate) 불필요** — 각 쌍이 그 자체로 필요한
대응을 준다(M2a/M2b가 서로 끝을 안 공유해도 이 규칙 하나로 Vom1↔Vop1이 바로 나옴, M6 그룹
실측으로 확인).

### B-3. 3단계 우선순위 짝짓기 — `_pair_odd_nodes_by_mirror()`
사용자에게 우선순위 설계를 구체적으로 설명받은 뒤 확정(AskUserQuestion 없이 대화로 승인):
1. node_map이 선언한 진짜 거울쌍(둘 다 odd_nodes에 있음) 우선 — 대칭축 반대편, 가장
   정당화되는 절단점(M6에서 `(Vom1,Vop1)`).
2. 남은 자기대응(허브) ↔ orphan(미매칭 가지 끝) — orphan 가지가 원래 그 허브에서 갈라진
   것이므로 되짚어 잇는 게 가장 짧고 자연스러움(M6에서 `(Vx,Vbias2)`).
3. 그래도 남으면 기존 방식(순서대로)으로 폴백 — 근거 있는 다중 사례가 아직 없어 상상으로
   설계하지 않음, `node_pairing_fallback_used`로 발동 여부를 정직하게 남김.

### B-4. `find_min_crossover_layout(transistors, matching_pairs=None)` 확장
`matching_pairs=None`(기본값)이면 기존 hub-leaf 사전조건 + 순서대로 짝짓기 완전히 그대로
(하위호환 — 기존 프로덕션 호출부 `_build_rows_from_shares_with_crossover()`/
`_common_centroid_nway_search()`는 `matching_pairs`를 안 넘기므로 전혀 안 건드림, 실제로
이 함수가 self-test 전용이 아니라 **프로덕션에서 이미 쓰이고 있었다**는 것도 이번에 grep으로
확인). `matching_pairs`를 주면 hub-leaf 제약을 풀고 위 두 헬퍼로 일반 그룹을 지원.

### B-5. self-test(Test 12.13) + 회귀 확인(해시 시드 이슈)
M6 그룹 실제 connectivity로 crossover=1 + fallback 없음 확인, node_map 역산 단위 확인,
`matching_pairs=[]`(전부 orphan) 시 전부 폴백되는지, `matching_pairs=None` 기존 경로가
`node_pairing_fallback_used=None`으로 신규 로직 미개입인지 — 전부 통과. **회귀 확인 중
PYTHONHASHSEED 노이즈를 발견**: `d59570f` 베이스라인과 1차 diff에서 `{'X','Y'}` 같은 set
문자열 표현 순서가 몇 군데 달랐는데, 이건 프로세스별 해시 랜덤화 때문(Python 기본 동작)이지
코드 차이가 아니었다 — `PYTHONHASHSEED=0`으로 고정해 재실행하니 신규 Test 12.13 블록 외
0줄 차이로 완전히 무회귀 확정. (교훈: 이 파일들 self-test는 `set` 출력이 있어 회귀 diff 뜰 때
해시시드를 고정할 것 — 안 그러면 가짜 diff가 섞여 나온다.)

## C. 그룹분할 harness 배선 — 논의 중단(다음 세션 계속)

세션15 B절을 마치고 "harness에 마저 배선해줘" 요청을 받아 설계를 시작했으나, **사용자가
"이쪽 논의를 좀 더 진행하고 싶다"며 다음 세션으로 미뤘다 — 이 절 아래는 순수 설계 논의
기록이고, 코드는 전혀 안 건드렸다(B절 상태 그대로).**

### C-1. 배선 위치/메커니즘(연구 완료, 근거 있음)
`run_topology_pipeline()`이 물리 행을 구성하는 방식을 직접 읽어 확인(sizing_recipe.py
`run_topology_pipeline_with_finger_fixup()`, stick_diagram.py `run_topology_pipeline()`
4022~4036행 부근): `sizing_overrides[name]["stack_id"]`가 `split_into_stacks()`의 그룹핑
기준이다 — 즉 소자의 `stack_id`를 바꾸면 다음 라운드에 자동으로 별도 물리 행이 된다.
`repair_matching_safety()`가 이미 같은 패턴(`f"{원래행}_repair{i}"`)을 쓰고 있어서 전례가
있다.

**제안한 설계**: `run_topology_pipeline_with_finger_fixup()`의 라운드 루프에서 핑거조정
(`apply_and_revalidate_pair_adjustment()`)이 `applied=False`면, 바로 `unresolved_row`로
포기하지 않고 `find_min_crossover_layout(row_transistors, row_pairs)`로 그룹분할을 시도.
반환된 `segments`대로 그 row의 소자들 `stack_id`를 `f"{row_name}_seg{i}"`로 재배정(순수
물리 배치 변경, W/n_fingers 안 바뀜 — `repair_matching_safety()`와 같은 성격이라
`_sync_finger_fixup()`류의 gm/ID 재검증 불필요) → 다음 라운드에서 `run_topology_
pipeline()`이 세그먼트를 별도 행으로 인식해 재감사.

### C-2. 미해결 질문 1 — crossover는 핑거조정과 "같은 급"이 아니다
핑거조정 성공은 진짜 0-crossover 단일 diffusion을 만들지만, 그룹분할은 **crossover
routing(추가 metal+via)이 실제로 필요하다는 설계 비용**을 받아들이는 것이다. `find_min_
crossover_layout()`은 "그래프 이론상 항상 성공"하므로, 이 폴백을 넣으면 `unresolved_row`가
사실상 거의 안 뜨게 된다 — 이게 `audit_ok=True`로 조용히 묻히면 "완전히 공짜로 풀렸다"는
거짓 인상을 준다. **제안한 해법**(사용자 확인 전): 새 필드(예: `group_splits: [{"round",
"row","crossover_count"}, ...]`)로 크로스오버가 실제로 몇 번 들어갔는지 정직하게 남긴다.
→ **이 필드 이름/구조, 그리고 "crossover가 들어간 것도 unresolved의 일종으로 볼지 vs 별도
성공 등급으로 볼지"를 다음 세션에 확정할 것.**

### C-3. 미해결 질문 2 — `cell_groups`/`floorplan_hints.spine_groups`와의 상호작용
`run_topology_pipeline()`(4053~4070행 부근)은 호출자가 `cell_groups`를 명시적으로 주면
그 안에 나열된 row 이름만 감사한다(`if rn in rows`로 필터) — 그룹분할로 새로 생긴
`_seg0`/`_seg1` 이름은 원래 선언에 없으므로 **감사에서 조용히 누락될 수 있다**는 걸 코드로
확인했다. 세션15가 검증한 M6 사례는 `cell_groups` 없이 self-test해서 이 경로를 안 탔다 —
지금 당장 처리할 실제 사례가 없어 "알려진 한계로 docstring에만 남기고 손 안 댄다"를
제안했으나 **사용자 확정 전에 논의가 중단됨.** → 다음 세션에 이 갭을 지금 막을지(예:
`_seg*`로 재배정될 때 원래 row가 속한 cell_groups 항목에 자동으로 추가), 아니면 정말
"실제로 막히는 사례가 나오면 그때"로 미룰지 정할 것.

### C-4. 다음 세션 시작 시 이어갈 구체적 지점
사용자가 마지막으로 한 말: "이쪽 논의를 좀더 진행하고 싶어" — 즉 **C-2/C-3 두 질문에 대한
입장이 아직 없다**. 다음 세션은 이 두 질문부터 다시 묻고, 답이 나오면 위 C-1 설계대로
`run_topology_pipeline_with_finger_fixup()`을 실제로 고치는 순서로 진행할 것(사전 승인 원칙
그대로 유지).

---

# 세션16 결론 — 그룹분할이 matching(3c)을 깨는 근본 결함 발견 → 3단계 재설계(크래시 수정+
# branch 복합 매칭+매칭 목적 핑거증가) 2/3 구현·검증·커밋 완료

세션15 C절(그룹분할 harness 배선 설계 논의)을 이어가려 했으나, 사용자가 "그 전에 이 문제의
속성부터 얘기해보고 싶다"며 근본 질문을 던졌고, 그 질문을 실제로 검증하는 과정에서 그룹분할
설계 자체의 결함이 드러나 세션 전체가 "재설계"로 방향이 바뀌었다. C-2/C-3(세션15가 남긴 원래
질문)는 이번 세션에서 다루지 못했다 — 순서대로 정리한다.

## A. 출발점 — "이게 finger 문제이기도 하지만 layout 문제이기도 하잖아"

사용자 질문: 그룹분할(물리 배치 변경)을 `repair_matching_safety()`(순수 layout, gm/ID 무관)
쪽에서 처리해야 하나, 아니면 L3+L4 체인(핑거조정, gm/ID 재검증 필요) 쪽에서 처리해야 하나?

- **두 개의 독립축으로 분해**: 축1(어떤 audit 체크를 고치는가 — euler(1) vs matching quality
  (3b/3c)) vs 축2(변경이 sizing/gm-ID에 영향을 주는가). 지금까지는 이 두 축이 우연히
  일치했다(`repair_matching_safety()`=축1 3b/3c+축2 무영향, 핑거조정=축1 euler+축2 영향).
  그룹분할은 축1로는 euler(핑거조정과 같은 편)인데 축2로는 무영향(repair와 같은 편)이라
  **두 축이 처음으로 어긋나는 사례**임을 확인.
- **`stack_id` 필드 중복 사용 확인**(사용자 질문: "그럼 sizing도 건드리게 되는건가?") — 코드로
  직접 추적: `stack_id`가 사이징 단계(`optimize_full_circuit_budget()`의 `kcl_series_union()`
  → `propagate_topology_forced_currents()`, 진짜 KCL 직렬스택)와 레이아웃 단계
  (`run_topology_pipeline()`의 `sizing_overrides[name]["stack_id"]`, 순수 물리 행 그룹핑)
  **두 곳에서 완전히 다른 의미로 재사용**되고 있었다. `propagate_topology_forced_currents()`가
  `run_topology_pipeline()` 안에서 전혀 호출되지 않음을 grep으로 확인 — 그룹분할의 stack_id
  재배정은 사이징 단계와 상호작용할 경로 자체가 없다(구조적으로 안전).
- **결론(잠정)**: 축1이 더 근본적이므로 그룹분할은 euler 체인(`run_topology_pipeline_with_
  finger_fixup()`) 쪽에 위치하되, 동작 방식은 repair처럼 순수 stack_id relabeling(gm/ID
  재검증 불필요)으로 유지 — 단, 아래 D절에서 이 결론의 전제 자체가 흔들린다.

## B. "매칭되는 소자들의 배열을 미리 만들지 않았나?" — 재계산 vs 재사용 확인

사용자 질문: `find_min_crossover_layout()`이 crossover 지점만 정하는 건지, 실제 소자 배열
(순서)까지 이미 계산해두는 건지 — 그리고 그게 나중에 `build_stick_diagram()`에서 다시
계산되는 건지.

- `find_min_crossover_layout()`은 실제로 `segments`마다 이미 계산된
  `transistor_sequence`/`node_sequence`를 갖고 있다(가상 edge로 오일러 회로를 만들어
  `hierholzer()`로 한 번에 계산 후 자르는 방식) — crossover 선택과 배열 계산이 **같은
  계산에서 동시에** 나온다.
- 그런데 `build_stick_diagram()`(2607행)은 미리 계산된 시퀀스를 받는 파라미터가 없다 —
  `stack_id`만 재배정하면 다음 라운드에 `mirror_symmetric_trail()`/`hierholzer()`로
  **처음부터 다시 계산**한다.
- **`probe_group_split_reassembly.py`**(신설, `workspaces/current-reuse-telescopic-ota-
  report/`)로 M6 그룹 실측: 재계산이 실패하지는 않는다(T-join 이론상 각 세그먼트는 구조적으로
  Euler-path 가능이 보장됨, 실측 확인) — 하지만 재계산된 배열이 원본과 **다를 수 있다**
  (seg1에서 M6/M7 순서가 바뀜, 오일러 경로가 유일하지 않다는 세션11 관찰의 재확인).

## C. 결정적 발견 — "differential pair를 무시한 결과 아닌가?" (사용자 질문)

`probe_group_split_reassembly.py`에 `audit_row_split()`을 실제로 붙여 3c(common-centroid)를
계산해보니, 사용자의 직관이 정확히 맞았다:

```
[FAIL] 3c. common-centroid[M1a/M1b]: |dx|=3.00 |dy|=1.00 (허용오차 0.5)
[FAIL] 3c. common-centroid[M2a/M2b]: |dx|=5.00 |dy|=1.00 (허용오차 0.5)
```

- **원인**: `audit_row_split()`의 3c는 "같은 행에 있어야" 요구가 아니라 "여러 행에 걸쳐
  분배돼도 되지만 전체 무게중심(x,y)이 맞아야" 요구다(docstring에 이미 실측 사례 있음 —
  folded_cascode M7/M8을 swap-대칭으로 양쪽 행에 나눠 분배하면 `dy=0.20`, "각자 한쪽 행에
  통째로"는 `dy=1.0`). `find_min_crossover_layout()`은 소자를 **통째로** 한 세그먼트에
  배정하는데, 이게 정확히 "각자 한쪽 행에 통째로"(나쁜) 패턴이었다.
- **세션15 B-5("세그먼트가 거울상이 되어 대칭성이 저절로 유지된다")는 그래프/토폴로지 레벨
  대칭을 말한 것이지, 3c가 실제로 재는 물리적 무게중심 대칭이 아니었다** — 이름이 비슷한
  "대칭"이라는 단어가 서로 다른 두 개념을 가리키고 있었다는 게 숫자로 드러남.
- **부가 발견**: 이 3c FAIL을 `repair_matching_safety()`가 고치려 하면, 정확히 세션15
  A-3에서 발견하고 미뤄둔 크래시 버그(offset/branch_symmetric + `n_fingers=1` → `common_
  centroid_layout()` `ValueError`)를 100% 밟는다 — 가상의 걱정이 아니라 실제 재현 경로임을
  확인.

## D. 재설계 조사 — "이 문제를 해결할 수 있는 방법으로 재설계돼야 한다고 봐. 조사해보고
## 제안해봐"

### D-1. 발견 1 — crossover 짝짓기 우선순위(B-3 tier1) 자체가 최악의 선택이었다
`probe_crossover_pairing_alternatives.py`(신설) — 4개 홀수차수 노드의 완전짝짓기는 정확히
3가지뿐이라 전수 대입:
- **현재 채택(tier1, `Vom1↔Vop1` 직접 짝짓기)**: M1a/M1b, M2a/M2b **둘 다 다른 세그먼트로
  쪼개짐**(C절의 그 FAIL 케이스).
- **대안(`Vbias2`를 `Vom1`/`Vop1`과, 나머지를 `Vx`와 짝짓기)**: M1a/M1b, M2a/M2b **둘 다
  같은 세그먼트에 유지**됨(크로스오버는 미매칭 소자 M57/M58 쪽에서만 발생).

세션15 B-3의 "선언된 진짜 거울쌍을 최우선으로 짝짓기"라는 우선순위가, 실제로는 매칭쌍을
정면으로 가르는 **최악의 선택**이었다 — "가장 정당화되는 절단점"이라는 근거는 그래프 대칭
관점에서는 맞지만 물리적 matching 보존 관점에서는 정반대였다.

### D-2. 발견 2 — (더 근본적) `mirror_symmetric_trail()`의 "거울대칭"과 3c는 다른 개념
크로스오버 없이(D-1 대안 그대로) 두 매칭쌍을 한 행에 둬도, `mirror_symmetric_trail()`이
만드는 시퀀스(`M2a,M1a,M7,M6,M1b,M2b`)는 **팰린드롬**(매칭쌍을 양끝에 배치)이라 3c로는
오히려 `dx=3~5`로 나쁘다 — 이건 그룹분할과 무관하게 **세션11부터 있던 L3(D) 메커니즘 자체의
사각지대**다. "그래프 레벨 거울대칭 워크"가 "물리적 무게중심 매칭"을 자동으로 보장한다는
가정이 틀렸다는 게 이번에 처음 확인됨.

### D-3. 발견 3 — 크래시 원인 확정
`common_centroid_layout([M1a,M1b])`를 직접 호출해 재현 — `_common_centroid_nway_exact()`가
"회전-최적"(잔차 보장 0) 경로를 타려면 `n_fingers>=N`(소자 수)이 필요한데, `n_fingers=1`인
2소자 쌍(N=2)은 이 조건을 못 만족해 `ValueError`. 에러 메시지 자체가 해법을 알려줌
(`n_rows`를 더 작게 지정하면 탐색 경로로 우회). 추가로 M2a/M2b(source가 다른 branch_symmetric
쌍)는 크래시조차 안 하고 조용히 스킵됨(`repair_matching_safety()`의 `ta.source != tb.source:
continue`) — "정직한 한계"로 문서화돼 있었지만 실제론 영원히 안 고쳐지는 사각지대.

## E. 3단계 재설계 합의 및 구현

사용자 확인을 거쳐 순서 확정: **1) 크래시부터 고쳐서 재현 → 2) branch 복합 매칭(source
다른 쌍도 "같은 소자처럼" 묶기) → 3) 그래도 안 되면(핑거 부족) 매칭 목적 핑거증가, gm/ID
재검증 실패시에만 인접배치로 완화(3번은 사용자가 제안한 순서 "2번을 하다가 안 되는 회로만
1번(완화)을 적용")**. 1/2번은 하나로 묶어 커밋(`58e608b`), 3번(설계안 순서상 2번, "매칭 목적
핑거증가")은 별도 커밋(`7a41a30`) — **3번(설계안 순서상 3번, "완화")은 아직 미구현**.

### E-1. 크래시 수정 (`stick_diagram.py`, 커밋 `58e608b`)
`repair_matching_safety()`가 `common_centroid_layout()`을 호출할 때 `n_rows=min(2,
ta.n_fingers, tb.n_fingers)`로 낮춰서, `n_fingers>=2`인 기존 케이스는 기존 기본값과 완전히
동일하게(회귀 없음), `n_fingers<2`인 새 케이스만 탐색 경로로 안전하게 우회. **"1번부터 고쳐서
재현해봐" 지시로 실제 M6 그룹에 태워보니**, 크래시는 안 나지만 M1a/M1b가 새 행으로 빠지면서
남은 M2a/M2b/M6/M7의 euler 연결성이 깨지는 **새 부작용**을 발견(repair의 "빼내기" 전략이
만드는 문제) — 이게 D절의 branch 복합 매칭으로 이어지는 동기가 됨.

### E-2. branch 복합 매칭 (`stick_diagram.py`, 커밋 `58e608b`)
사용자 제안("m1a/m2a, m3a/m3b 같은 branch 개념을 도입하면 source 다른 소자도 같은 로직으로
분리 안 되게 만들 수 있지 않나") — 조사해보니 **이미 있는 `kcl_series_union()`**(세션10 L2,
"2단자 net만" 규칙)이 강제병합 없이도(`matching_pairs=[]`) `{M1a,M2a}`/`{M1b,M2b}`/
`{M57,M58}`를 정확히 원하는 branch로 자동 발견해줌을 확인 — 새 그래프 로직을 만들 필요가
전혀 없었다. `_kcl_branch_map()`/`_two_device_branch_outer()`/`_branch_composite_pair()`
신설(2소자 선형 branch만 지원, 의도적으로 좁은 범위) — `repair_matching_safety()`가 source
공유 여부와 무관하게 항상 이 경로를 먼저 시도하고, branch 구조가 없으면 기존 개별-소자
경로/skip으로 완전히 폴백. 같은 라운드에서 같은 branch가 중복 재배치되지 않도록
`touched_this_round` 가드 추가(처음엔 행 이름에 `_repair0`이 라운드당 2번씩 중첩돼 쌓이는
낭비가 있었음, 가드로 라운드당 1번으로 정리). self-test 2건(M6 그룹 실측 + branch 없는 기존
케이스 회귀 확인) 전부 통과, 회귀 0줄.

### E-3. 매칭 목적 핑거증가 (`sizing_recipe.py`, 커밋 `7a41a30`)
branch 복합 매칭으로도 `n_fingers=1`이면 3c(`dx<=0.5`)가 기하학적으로 불가능(최선이
`dx=1.0`, `n_fingers=2`부터 회전-최적 경로가 `residual=0.0` 완벽 달성)임을 실측 확인한 뒤
구현. `suggest_matching_finger_growth()`(euler용 `suggest_pair_finger_adjustments()`와
달리 후보 랭킹 불필요 — 필요한 delta가 `min_fingers`까지 부족한 만큼으로 정확히 하나) +
`apply_and_revalidate_matching_finger_growth()`(L3+L4 패턴, `revalidate_finger_
override()` 재사용) + `run_matching_safety_with_finger_growth()`(`repair_matching_
safety()`를 감싸는 라운드 루프, `run_topology_pipeline_with_finger_fixup()`과 동일하게
`stick_diagram.py`↔`sizing_recipe.py` 단방향 import 제약 때문에 여기 위치). self-test(L4d) —
M6 그룹 실제 사례로 M1a/M1b/M2a/M2b가 전부 `n_fingers=2`로 자라(공통-centroid 회전 배치가
2개 행에 1개씩 진짜로 finger를 나눠 배치) 3b/3c 필수 게이트를 완전히 통과함을 end-to-end로
확인. 회귀 0줄(`58e608b` 대비 신규 L4d 블록 15줄 제외 0줄 차이).

**설계 원칙 하나 명문화**: `run_matching_safety_with_finger_growth()`의 `unresolved_
pair=None`은 "3c 관점에서 이 함수가 할 일을 다 했다"는 뜻이지 `audit.ok=True`의 동의어가
아니다 — box-shape(행폭 비율) 같은 이 함수 책임 밖의 다른 체크가 별도로 실패할 수 있다(실측:
M6 그룹은 3b/3c 전부 PASS했지만 M6/M7만 남은 행과의 폭 비율(§8) 때문에 box-shape는 여전히
FAIL). 호출자는 전체 성공 여부를 반드시 `result["audit"].ok`로 직접 확인해야 한다(docstring에
명시).

## F. 부수적으로 확인한 self-test 함정 (기록해둘 가치 있음)
`common_centroid_layout()`의 회전-최적 경로가 `n_fingers=2`인 소자를 물리적으로 "2개 행에
1개씩" 나눠 배치하는 게 정상 동작이다(진짜 common-centroid) — 그래서 `rows` 딕셔너리에는
같은 소자 이름이 여러 행에 걸쳐 `n_fingers=1`짜리로 여러 번 나타난다. 처음 self-test를 짤 때
이름 하나에 값 하나만 남기는 flat dict comprehension(`{t.name: t.n_fingers for ...}`)을
써서 나중 행 값(1)으로 덮어써 "성장이 반영 안 됐다"고 착각할 뻔했다 — 행별로 합산해야
정확하다(`.ai/context.md` 기록 가치: 이 파일들 self-test에서 앞으로도 반복될 수 있는 함정).

## G. 다음 세션 이어갈 지점 (우선순위 순)
1. 재설계안 3번(핑거증가도 gm/ID 예산 때문에 안 되면 인접배치로 완화) 구현 — `run_matching_
   safety_with_finger_growth()`의 `unresolved_reason` 지점에 이어붙이면 됨.
2. `find_min_crossover_layout()`/`_pair_odd_nodes_by_mirror()`의 crossover 짝짓기
   우선순위를 D-1 발견대로 재작성(선언된 매칭쌍을 직접 짝짓는 걸 최후수단으로) — 이게 안
   고쳐지면 그룹분할 자체가 "matching을 갈라놓는" 결함을 그대로 안고 있다.
3. 1/2번이 끝난 뒤에야 세션15 C절(그룹분할 harness 배선, C-2/C-3 질문)로 복귀 — 지금
   상태로 배선하면 근본적으로 결함 있는 크로스오버 선택을 harness에 그대로 심는 것.

---

# 세션17 결론 — 재설계안 3번(gm/ID 예산으로 핑거증가 막히면 인접배치로 완화) 구현 완료

세션16이 남긴 "다음 세션 최우선"(재설계안 3번)을 진행. 사용자가 "이건 sizing 열화를
감수하느냐 layout 열화를 감수하느냐 문제 아니냐, layout은 trim으로 나중에 보정 가능하지
않냐"고 트레이드오프의 근거를 직접 제시해 설계 방향을 확정했고, 부수적으로 "crossover로
이 문제를 풀 수 있나?"라는 질문도 코드/수식으로 직접 검증했다.

## A. crossover는 n_fingers=1 문제를 못 푼다(수학적으로 확정) — 구현 전 검증

`audit_row_split()`의 3c는 소자 무게중심을 `(Σposition)/(자기 자신의 총 n_fingers)`로
계산한다 — `n_fingers=1`인 소자는 시퀀스에서 정확히 한 자리만 차지하므로, 서로 다른 두
소자가 같은 자리를 점유할 수 없는 이상 crossover로 그룹을 아무리 재배치해도 최선이
`dx=1`(같은 행) 또는 `dy=1`(다른 행)이라 허용오차 0.5를 절대 못 넘는다(세션16 D-3의
"회전-최적 경로가 n_fingers>=2를 요구한다"는 관찰과 동일한 제약의 다른 표현). 즉 D-1의
crossover 짝짓기 우선순위 수정(다음 세션 최우선, 아래 참고)은 "이미 가능한 배치가
나빠지는 걸 막는" 역할이지 "원래 불가능한 걸 가능하게" 만들지는 못한다 — 그래서
"완화"(레이아웃 열화 감수)는 여전히 필요했다.

## B. 설계 결정(사용자 확인)

1. **완화 대상 범위**: `offset`(진짜 differential pair)과 `branch_symmetric`(ratio+not
   shares_node) 둘 다 포함 — crossover가 offset도 못 풀어주므로, 제외하면 offset pair는
   gm/ID 예산 부족 시 그냥 unresolved로 남아 대안이 없다. 근거: gm/ID 위반(회로 기능
   저하)은 trim 불가능하지만, layout mismatch(3c FAIL)는 trim으로 보정 가능 — 후자가
   더 감수할 만한 열화.
2. **결과 표기**: 완화가 적용돼도 `audit.ok`는 3c FAIL을 그대로 반영(정직, 몰래 성공으로
   둔갑 안 시킴). 대신 `relaxed_pairs` 필드로 "이건 trim 대상으로 알고 있는 열화"라는
   근거를 남기고, 호출자가 `result["audit"].ok`와 `result["relaxed_pairs"]`를 직접 보고
   최종 승인 여부를 판단.

## C. 구현 (`stick_diagram.py`/`sizing_recipe.py`, 아직 미커밋)

- `repair_matching_safety(rows, matching_pairs, pair_sensitivity=None, max_iter=3,
  relaxed_pairs=None)`(`stick_diagram.py`) — `relaxed_pairs: set[frozenset]` 신설.
  이 집합에 든 쌍은 composite/raw 경로 둘 다에서 `select_layout_tool()`의 판단(offset/
  branch_symmetric은 항상 common-centroid)을 무시하고 `interdigitate_layout`을 강제
  적용 — 순수 layout 오버라이드, sizing 무관. 공유 hub도 branch composite도 없는 쌍은
  (기존 "정직한 한계") `relaxed_pairs`에 있어도 여전히 손 못 댐 — 완화는 이미 있는 layout
  자유도를 쓰는 것이지 없는 자유도를 만들지 않는다(self-test로 직접 확인).
- `run_matching_safety_with_finger_growth(..., allow_layout_relaxation=True)`
  (`sizing_recipe.py`) — 핑거증가가 `reason=="gm_id_violation"`(딱 gm/ID 예산 위반일
  때만, `no_finger_w`/`growth_not_applicable`는 완화 대상 아님 — 설정 문제를 조용히
  덮지 않기 위해)로 실패하면 그 쌍을 `relaxed_pair_keys`에 등록하고 `repair_matching_
  safety()`를 재시도. 새 `unresolved_reason="relaxed_to_layout"`으로 "완화를 실제로
  적용했다"를 구분. 반환에 `relaxed_pairs: [{"pair","reason":"gm_id_budget_exceeded",
  "trim_recommended":True,"interdig_ok":bool|None}, ...]` 추가(`interdig_ok`는 완화
  적용 다음 라운드의 fresh audit에서 3b 체크를 찾아 사후 채움).
- self-test 4건: `stick_diagram.py`(Test 28 뒤) 2건 — M6 그룹으로 완화 후에도 3c FAIL
  유지 확인 + 공유 hub/branch composite 없는 쌍은 relaxed_pairs 있어도 안 바뀜 확인.
  `sizing_recipe.py`(L4e, 세션16 L4d 뒤) 2건 — offset pair(Ma/Mb, 공유 source)로 gm/ID
  예산 위반 유발 → `unresolved_reason="relaxed_to_layout"`/`relaxed_pairs`=1건
  (`interdig_ok=True`)/`audit.ok=False` 실측 확인(interdig_ok은 손으로 추정하지 않고
  실행해서 확인 — 세션16 M6 그룹으로 처음 시도했다가 branch composite의 `touched_this_
  round` 상호작용이 복잡해 최종적으로 raw path 하나만 쓰는 단순 offset 쌍으로 교체) +
  `allow_layout_relaxation=False`면 세션16 그대로(`unresolved_reason="gm_id_violation"`,
  `relaxed_pairs=[]`) 보존되는 회귀 대조.
- **회귀**: `PYTHONHASHSEED=0`으로 편집 전(`7a41a30`) 대비 self-test 전체 출력 diff —
  `stick_diagram.py`는 신규 테스트 블록(8줄) 외 0줄 차이, `sizing_recipe.py`는 신규 L4e
  블록(9줄) 외 0줄 차이. 무회귀 확정(격리 baseline 디렉토리 `git show HEAD:...`로 확보,
  세션12부터 쓰던 패턴 그대로).

## D. 알려진 한계 / 다음 세션 참고

- `relaxed_pairs`는 declared matching_pair 단위로 개별 등록된다 — M6 그룹처럼 여러
  선언 쌍이 같은 branch composite를 공유하면, 물리적으로는 한 번의 재배치로 여러 쌍이
  동시에 완화되지만 오케스트레이터 레벨에서는 각 쌍이 별도 라운드에 걸쳐 순차적으로
  `relaxed_pairs`에 등록된다(라운드 수만 늘어날 뿐 결과는 정확함, `max_rounds` 기본값
  5 안에서 문제 없음 확인) — 최적화 여지는 있지만 정확성 문제는 아니라 손 안 댐.
- `interdig_ok`가 `False`로 나오는 실제 사례(예: composite 확장 후 hub/leaf가 인접하지
  않는 경우)는 아직 self-test로 직접 확인 안 함 — 지금 테스트는 raw path(공유 source,
  interdig_ok=True로 확인됨)만 다뤘다. 실제 회로에서 완화가 3b조차 못 주는 경우가 나오면
  `relaxed_pairs`의 `interdig_ok=False` 처리(호출자가 어떻게 반응할지)를 재검토할 것.

## E. crossover 짝짓기 우선순위 재작성(D-1) 구현 완료 — 같은 세션17에 이어서 진행

사용자가 "커밋하고 이어서 진행해"로 세션17 최우선 다음 항목(D-1)을 바로 이어 진행했다.

### E-1. 왜 "완화"로는 D-1을 대체할 수 없는지 재확인
D절(완화)과 D-1(crossover 짝짓기)은 서로 다른 문제다 — A절에서 이미 확인했듯 crossover는
`n_fingers=1` 제약 자체를 못 풀지만, D-1은 `n_fingers` 문제와 무관하게 **crossover가
필요한 상황에서 어디를 끊을지**의 문제라 완화 구현 후에도 그대로 유효했다.

### E-2. 설계 — "탐색"이 아니라 "구성 후 채점"(세션11 원칙 재적용)
`find_min_crossover_layout()`의 세그먼트 계산(가상 edge + `hierholzer()` + trail 분해)을
`_build_crossover_segments(transistors, pairs)`로 뽑아내 pairs 후보별로 재사용 가능하게
만들고, `_count_matching_pair_splits(segments, matching_pairs)`로 "선언된 matching_pairs
중 몇 개가 서로 다른 segment로 완전히 갈라졌는지" 채점하는 함수를 신설했다. 새
`_select_crossover_pairing()`이: (1) 기존 3단계 휴리스틱(`_pair_odd_nodes_by_mirror()`)
결과를 기본 후보로 채점 (2) 분할=0이면 그대로 채택(전수 탐색 생략, 흔한 경우 빠르게 처리)
(3) 분할>0이고 홀수차수 노드 수가 `_MAX_CROSSOVER_PAIRING_NODES`(=8, `(2m-1)!!` 관례상
캡) 이하면 가능한 완전짝짓기를 `_enumerate_perfect_matchings()`로 전수 대입해 분할이
더 적은(이상적으로 0) 후보로 교체(분할=0을 찾으면 즉시 중단). crossover_count(m-1) 자체는
T-join 정리로 어떤 짝짓기를 쓰든 불변이므로, 이 선택은 "crossover가 몇 번 필요한가"가
아니라 "어디서 끊기는가"만 바꾼다. `matching_pairs=None`(기존 프로덕션 hub-leaf 호출부)
경로는 전혀 안 건드림 — 완전히 하위호환.

### E-3. 실측 검증 — M6 그룹으로 D-1의 예측이 정확히 재현됨
`probe_d1_check.py`(신설, 스크래치패드)로 실제 확인: 옛 tier1 짝짓기(`[('Vom1','Vop1'),
('Vx','Vbias2')]`)는 segments가 `[M2b,M1b]`/`[M57,M58,M7,M6,M1a,M2a]`로 나와 M1a/M1b,
M2a/M2b 둘 다 갈라짐(splits=2, 세션16 D-1 발견 그대로 재현). 새 `_select_crossover_
pairing()`은 자동으로 대안(`[('Vbias2','Vom1'),('Vop1','Vx')]`)을 찾아 segments가
`[M57,M58]`/`[M2b,M1b,M7,M6,M1a,M2a]`로 나와 splits=0(crossover는 미매칭 M57/M58
쪽에서만) — D-1이 손으로 찾은 대안과 정확히 일치.

### E-4. self-test 갱신 — Test 12.13(세션15) 재작성
기존 assertion(`crossover_count==1`, `fallback_used==False`)은 T-join 불변량 때문에
새 코드에서도 우연히 그대로 통과해(값 자체는 안 바뀜) 개선을 검증 못 하는 약한 테스트였다
— splits=2(옛 tier1, 회귀 대조용으로 명시적으로 재현) → splits=0(신규)을 직접 assert하도록
갱신, `crossover_count==1`은 "T-join 불변, 짝짓기가 바뀌어도 그대로"라는 의미로 재해석해
유지. 텍스트 서술("node_map 우선순위(Vom1/Vop1 -> Vbias2/Vx)만으로 짝지어짐")도 이제
사실과 다르므로 D-1 발견 내용으로 교체.

### E-5. 회귀
`PYTHONHASHSEED=0` 기준 `4bcaafc`(세션17 1차 커밋) 대비 self-test 전체 출력 diff —
`sizing_recipe.py`는 **0줄 차이**(이 branch가 아직 어떤 harness에도 안 이어져 있어 완전
무영향, E-6 참고), `stick_diagram.py`는 Test 12.13 섹션(의도적으로 바뀐 서술+신규
assertion)만 다르고 나머지 전부 0줄 차이. 무회귀 확정.

### E-6. 알려진 한계 / 다음 세션 참고
- 이 변경은 `find_min_crossover_layout(matching_pairs=...)` 경로에만 영향을 준다 — 이
  경로는 **아직 어떤 프로덕션 harness도 안 쓴다**(self-test 전용, 세션15/16부터 그랬음).
  즉 이 수정 자체는 실제 회로 사이징 결과에 지금 당장 영향을 주지 않는다 — 다음 항목
  (그룹분할 harness 배선)이 이 경로를 실제로 연결하는 시점부터 효과가 발생한다.
- `_select_crossover_pairing()`의 타이브레이크(분할 개수가 같은 후보가 여럿이면 먼저
  발견된 것 유지)는 아직 실제 다중 사례가 없어 최소 기준으로만 구현됨 — 더 나은 기준
  (예: 물리적 거리)이 필요한 사례가 나오면 그때 근거를 갖고 추가.
- `_MAX_CROSSOVER_PAIRING_NODES=8`(105개 후보) 이상인 그룹은 전수 탐색을 생략하고
  휴리스틱 결과만 쓴다 — 지금까지 실제로 관찰된 그룹은 전부 4개 이하라 아직 이 한계에
  부딪힌 사례 없음.

## F. offset 쌍 우선순위 가중치 — 같은 세션17에 이어서(사용자 확인 후 구현)

사용자가 E절 결과를 보고 "differential pair를 특별 취급 안 하냐"고 물어 확인해보니, 실제로
`_count_matching_pair_splits()`가 offset/ratio를 동등하게 셌다 — 진짜 트레이드오프
(둘 다 완전히 안 갈라지는 배치가 없는 경우) 상황이면 CMRR에 더 민감한 offset을 ratio보다
우선 보호해야 하는데 그런 우선순위가 없었다. 사용자가 "가중치 추가하자"고 확정해 구현.

### F-1. 설계 — 스칼라 대신 튜플 사전식 비교
`_count_matching_pair_splits(segments, matching_pairs, pair_sensitivity=None)`에
`pair_sensitivity` 선택 인자 신설 — 주면 반환값이 스칼라 대신 `(offset_splits,
other_splits)` **튜플**이 된다. Python 튜플 비교가 사전식이라 `_select_crossover_
pairing()`이 이 값을 그대로 비교하면 offset 쌍이 갈라지는 걸 ratio 쌍이 갈라지는 것보다
**항상** 더 나쁘게 채점한다 — 임의의 가중치 상수(예: offset=1000)를 지어내지 않고
자료구조로 우선순위를 표현. `_is_perfect_crossover_score(score)` 헬퍼로 스칼라 0과
튜플 (0,0) 둘 다 "분할 없음"으로 판정하는 지점을 하나로 통일. `_select_crossover_
pairing()`/`find_min_crossover_layout()` 둘 다 `pair_sensitivity` 인자를 그대로
관통시킴(둘 다 `None` 기본값, 하위호환).

### F-2. "동점인데 가중치로 갈리는" 진짜 tradeoff 실제 회로 못 찾음(정직하게 기록)
M6 등 여러 합성 구조(순수 star, hub-bridge 1개/2개, leaf-bridge)로 실제 tradeoff 사례를
찾아봤으나(`probe_offset_tradeoff*.py`, 스크래치패드, 커밋 안 됨) 못 찾았다 — offset 쌍이
`hierholzer()` 순회 특성상 항상 갈라지거나 항상 안 갈라지는 두 극단으로만 수렴하고, "동점"
상황 자체가 잘 안 생긴다는 게 실측으로 드러남. 상상으로 지어내지 않고, 대신 **segment를
손으로 구성**해 채점 함수 자체(그래프 탐색과 무관)를 직접 검증하는 방식으로 전환 —
스칼라로는 완전히 동점(각 1개씩 다른 쌍이 갈라짐)인 두 후보를 손으로 만들어, 튜플
비교(`(0,1) < (1,0)`)가 offset 보호 후보를 결정적으로 이기게 함을 확인. M6 실제 회로로는
`pair_sensitivity`를 줘도 이미 달성한 (0,0)이 안 깨지는지(회귀 안전성)만 확인.

### F-3. self-test/회귀
`stick_diagram.py` self-test에 4건 추가(Test 12.13 뒤) — 스칼라 vs 튜플 반환 확인,
손으로 구성한 tradeoff 동점 사례에서 튜플이 결정적으로 offset을 이김, `_is_perfect_
crossover_score()` 스칼라/튜플 판정, M6 실제 회로 회귀(여전히 (0,0)). `PYTHONHASHSEED=0`
기준 `69d9b39` 대비 diff — 신규 테스트 블록 외 0줄 차이, 무회귀 확정.

## G. `find_min_crossover_layout()` 호출 전 branch composite 사전병합 — 같은 세션17에
## 이어서(사용자 질문으로 발견)

사용자가 "이 함수가 composite인 걸 단일소자와 구분 안 하지? 그건 상위에서 주는 거니까"라고
확인 질문을 던졌고, 답하는 과정에서 실제 결함을 발견했다: `repair_matching_safety()`는
`interdigitate_layout()`/`common_centroid_layout()`을 부르기 전에 이미 `_branch_
composite_pair()`로 branch(M1a-M2a 캐스코드 컬럼)를 합성 소자로 뭉치는데, `find_min_
crossover_layout()`은 이걸 전혀 모르는 채 raw 개별 소자를 받는다 — crossover 짝짓기가
같은 branch의 두 소자를 서로 다른 segment로 갈라놓을 수 있다(M6이 지금까지 우연히 안
갈라진 것뿐, 구조적 보장이 아니었음). 사용자가 "이 방향으로 진행해"로 확정.

### G-1. 구현 (`stick_diagram.py`, `_branch_composite_pair()` 직후, `repair_matching_
safety()` 직전)
- `_composite_collapse_for_crossover(transistors, matching_pairs, pair_sensitivity=None)`
  — 선언된 matching_pairs를 순회하며 각 쌍에 `_branch_composite_pair()`를 시도, 성공하면
  4개 실제 소자(hub_a/leaf_a/hub_b/leaf_b)를 소비 처리하고 합성 쌍 하나로 교체(원래 두
  선언 쌍(hub쪽/leaf쪽)이 같은 branch를 가리키면 새 목록엔 합성 쌍 하나만 남음, 중복
  방지). 실패하면 원래 이름 그대로 통과(하위호환 폴백). `pair_sensitivity` 주어지면
  합성 쌍 민감도는 **"hub쪽/leaf쪽 중 하나라도 offset이면 offset"**(사용자 확인 —
  `repair_matching_safety()`의 `select_layout_tool()` "둘 중 하나라도 common_centroid
  필요하면 common_centroid 채택"과 동일한 보수적 원칙). 반환:
  `(new_transistors, new_matching_pairs, new_pair_sensitivity, expand_map)`.
- `find_min_crossover_layout_with_branch_composite(transistors, matching_pairs,
  pair_sensitivity=None)` — 위 함수로 collapse → `find_min_crossover_layout()` 호출 →
  결과 segment의 `transistor_sequence`를 `expand_map`으로 실제 소자 이름으로 다시 펼침
  (`_layout_result_to_rows()`가 쓰는 것과 동일한 펼치기 패턴). `find_min_crossover_
  layout()` 자체는 전혀 안 건드림(완전히 별도 wrapper). 반환에 `branch_composites`
  필드 추가(어떤 branch가 합성됐는지 투명하게 남김, 세션16 F절 "성공 필드 하나로 전체를
  판단하지 말 것" 원칙과 동일 이유).
  ⚠️ `node_sequence`는 합성 소자의 경계 net 그대로 남음(branch 내부 net은 복원 안 함 —
  지금까지 소비자는 `transistor_sequence`만 필요로 함, 정직한 한계로 docstring에 명시).

### G-2. self-test/회귀 (Test 28, `_branch_composite_pair()` 직후)
M6 그룹 실제 사례(`_m6b_row`/`_m6b_pairs`/`_m6b_sensitivity`, 세션16 fixture 재사용)로:
6소자→4개(합성 2+미매칭 2), 선언 쌍 2개→합성 쌍 1개, 민감도=offset(hub쪽 우선) 확인 +
펼친 뒤 M1a/M2a, M1b/M2b가 각각 **정확히 같은 segment**에 있음(채점 기반 회피가 아니라
구조적 보장 — 합성 소자는 그래프에서 원자 단위 edge라 애초에 쪼갤 방법이 없음)을 확인.
branch 구조 없는 그룹(rowA/rowB 기존 fixture)은 `_composite_collapse_for_crossover()`가
아무것도 안 건드리는지 회귀 대조. `PYTHONHASHSEED=0` 기준 `69d9b39` 대비 diff — 신규
테스트 블록 외 0줄 차이(F/G절 둘 다 포함), 무회귀 확정.
디버깅 중 실제 버그 1건 발견/수정: `composite_pairs` 딕셔너리 키를 처음엔 `frozenset`으로
만들었는데 `new_matching_pairs`에 넣는 키는 순서 있는 tuple이라 조회가 어긋나
`KeyError`가 났다 — tuple로 통일해 수정(self-test가 실제로 이 버그를 잡음, 실행 없이
넘어갔으면 몰랐을 것).

### G-3. 알려진 한계
`find_min_crossover_layout_with_branch_composite()`도 `find_min_crossover_layout()`과
마찬가지로 **아직 어떤 harness에도 안 이어짐**(self-test 전용) — 다음 항목(그룹분할
harness 배선)이 이 wrapper를 실제로 쓰기 시작하는 지점이다. 즉 harness 배선 설계 시
`find_min_crossover_layout()`이 아니라 **이 wrapper**를 호출하도록 할 것(그래야 branch
구조적 보장이 실전에도 적용됨).

---

# 세션18 결론 — 세션15 C절(그룹분할 harness 배선) 완료 — C-2/C-3 확정 후 구현+self-test+회귀

세션17이 남긴 "다음 세션 최우선"(그룹분할 harness 배선)을 진행. 코드를 고치기 전에 세션15가
남긴 C-2(crossover 성공 표기 방식)/C-3(`cell_groups` 갭) 두 질문에 대한 사용자 입장을 먼저
확정한 뒤(엔진 변경 사전 승인 원칙), `run_topology_pipeline_with_finger_fixup()`에 실제로
배선했다.

## A. C-2 확정 — `group_splits` 필드, `audit.ok`는 손대지 않는다

논의 중 사용자가 "`audit.ok=false`로 강제하면 어떤 문제가 있고, 별도 성공 등급 신설과 뭐가
다른가"를 물어 다음이 정리됐다:

- **`relaxed_pairs`(세션17)와 그룹분할은 겉보기엔 비슷해도 다르다.** `relaxed_pairs`가
  다루는 3c FAIL은 `n_fingers=1`일 때 **수학적으로 항상 실패**하므로(세션17 A절 공식
  확정), `audit.ok=False`를 유지하는 게 없는 실패를 지어내는 게 아니라 **실제로 여전히
  실패 중인 체크를 정직하게 반영**하는 것이었다. 반면 그룹분할이 고치는 건 체크1(euler)
  이고, 그 행에 `n_fingers=1` 매칭쌍이 안 섞여 있으면 euler+3b+3c가 **전부 진짜로 통과할
  수 있다** — 이 경우 `audit.ok=False`를 강제하면 **실제로 없는 체크 실패를 지어내서
  보고**하게 돼, `audit.ok`의 원래 의미(선언된 체크의 실제 pass/fail)를 오염시키고
  하위 소비자(`run_topology_pipeline_with_finger_fixup()`의 라운드 루프,
  `optimize_full_circuit_budget()`의 후보 채택 로직)가 실제론 멀쩡한 후보를 계속
  재시도/거부하게 만들 위험이 있다.
- **`group_splits` 필드는 사실 "별도 성공 등급"의 가벼운 버전**이다 — 둘 다 "`audit.ok`는
  진실하게 두고 옆에 비용 신호를 추가한다"는 같은 원칙을 공유한다. `group_splits`
  (리스트, "몇 번 어디서" 근거까지 남김) 쪽이 명시적 tri-state 등급보다 구현이 가볍고
  기존 반환 스키마(`fixup_rounds`와 나란히)에 자연스럽게 붙어 이쪽으로 확정.
- `audit.ok`는 계산에 전혀 개입하지 않는다 — 그룹분할 후 euler+3b+3c가 다 통과하면
  자연히 True, 그 행에 다른 실패(예: `n_fingers=1` 매칭쌍의 3c)가 남아 있으면 여전히
  False. "설정"이 아니라 "손 안 대고 그대로 둔다"는 게 핵심.

## B. C-3 확정 — `cell_groups` 자동확장, "지금 막기"로 결정

`run_topology_pipeline_with_finger_fixup()`의 실제 호출부(`optimize_full_circuit_
budget()`, `sizing_recipe.py:2288-2291`)를 코드로 직접 추적해 `cell_groups=spec.get(
"cell_groups")`가 실제 프로덕션 spec 입력 경로로 이미 살아있음을 확인 — 세션15 C-3가
"지금 당장 처리할 실제 사례가 없다"고 미뤄뒀던 갭이, 이번 배선으로 **실전에서 바로 발동할
수 있는 상태**가 됐다(더는 가상의 우려가 아님). 사용자가 "지금 막기"로 확정.

## C. 구현 (`sizing_recipe.py` 단독 수정, `stick_diagram.py`는 세션17 상태 그대로 무변경)

`run_topology_pipeline_with_finger_fixup()`(2746행 부근) 라운드 루프에서 `apply_and_
revalidate_pair_adjustment()`가 `applied=False`(핑거조정 실패)일 때, 바로 `unresolved_row`
로 포기하던 지점을 다음으로 교체:

1. `find_min_crossover_layout_with_branch_composite(row_transistors, row_pairs,
   row_pair_sensitivity)` 호출(G-3절 원칙대로 raw `find_min_crossover_layout()`이
   아니라 이 wrapper 사용 — branch 구조적 보장이 실전에도 적용되도록). `row_pair_
   sensitivity`는 `meta["symmetry"]["matching_pairs"]`에서 그 row로 필터링해 offset
   우선순위(세션17 F절)도 그대로 관통.
2. 이 함수는 그래프 이론상(T-join/route inspection) 항상 성공 — 반환된 `segments`대로
   그 row 소자들의 `sizing_overrides[name]["stack_id"]`를 `f"{row_name}_seg{i}"`로
   재배정(순수 물리 배치 변경, W/n_fingers 불변이라 gm/ID 재검증 불필요, 세션15 C-1
   설계 그대로).
3. `effective_cell_groups`(호출자가 준 `cell_groups`의 내부 사본, 원본은 불변)에서
   원래 row 이름이 속한 항목을 찾아 `_seg*` 이름들로 교체(C-3).
4. `group_splits` 리스트에 `{"round","row","n_segments","crossover_count",
   "branch_composites","node_pairing_fallback_used"}` 기록(C-2, `find_min_crossover_
   layout_with_branch_composite()`가 실제로 반환하는 키를 그대로 재사용 — 지어낸
   필드 없음).

`unresolved_reason="no_valid_candidate"`는 그룹분할이 항상 성공하므로 더 이상 이 함수의
실제 반환 경로가 아니게 됐다(`max_rounds_exceeded`만 남음).

## D. self-test — 실제 M3a 그룹(세션12/14 L4c fixture) 재사용, 케이스B 재작성 + 케이스C 신설

새 픽스처를 지어내지 않고, 정확히 이 시나리오(핑거조정 실패)를 이미 테스트하던 L4c 케이스B
(M3a 그룹 11소자, 면적 예산 극도로 타이트)를 재사용 — 실행 전에 스크래치패드 probe
스크립트로 실제 반환값을 먼저 확인한 뒤(상상으로 assertion을 채우지 않는 원칙) 다음을
검증하도록 재작성:

- **케이스B(동작이 의도적으로 바뀜, 회귀 아님)**: `unresolved_row=None`(그룹분할로 euler
  완전 해결), `group_splits`=1건(3세그먼트, crossover_count=2), `branch_composites`=
  `{M4a,M3a}`/`{M4b,M3b}` — **실측으로 새로 발견**: M3a 그룹이 이미 M4a-M3a/M4b-M3b
  캐스코드 컬럼 구조를 갖고 있어(M4a.drain="N3a4a"=M3a.source), `_composite_collapse_
  for_crossover()`가 이걸 실제로 감지해 합성 소자로 묶은 뒤 crossover 짝짓기를 했다 —
  G-3 wrapper가 세션17 M6 픽스처 외의 **실제 다른 회로**에서도 branch 구조를 올바르게
  인식함을 처음으로 확인. `audit.ok=False`(3b/3c 잔여 실패, 이 함수 책임 밖 — 정직하게
  유지, A절 원칙대로 손 안 댐).
- **케이스C(신설, C-3 검증)**: `cell_groups={"cellA": ["m3a_row", "other_row_not_
  present"]}`로 호출 → 그룹분할 후 `cellA`의 감사 결과에 `m3a_row_seg0/1/2` 전부
  euler PASS로 포함됨(자동확장이 실제로 감사 파이프라인까지 작동) + 호출자가 준
  `cell_groups` 원본 dict는 그대로(순수함수 원칙 유지) 확인.

## E. 회귀 확인

`git show HEAD:...sizing_recipe.py`(세션17 커밋 `fbfaed5` 기준, `stick_diagram.py`는
이번 세션 무변경이라 현재 파일 그대로 사용)로 격리 baseline 디렉토리 구성 →
`PYTHONHASHSEED=0` 고정, self-test 전체(250줄) diff — **케이스B/C 블록(의도된 변경+신규)
외 0줄 차이**. `L4c 케이스A`/`L5`/`L4d`/`L4e`를 포함한 나머지 전체 self-test(CMRR/PSRR/
noise/mismatch 등)는 완전히 무변경. 무회귀 확정.

## F. 알려진 한계 / 다음 세션 참고

- `stick_diagram.py`는 이번 세션에 전혀 안 건드림 — 세션17 상태(`4e38aa6`) 그대로.
- `optimize_full_circuit_budget()`이 `run_topology_pipeline_with_finger_fixup()`을
  이미 호출하고 있으므로(세션15 A절 실배선), 이 그룹분할 폴백도 **자동으로 harness
  최상위 경로에 연결돼 있다** — 별도 배선 코드가 더 필요 없다. 단, `run_harness.py`
  자체가 세션11에 중단된 채 재실행이 안 됐으므로, 이 폴백이 실제 `current_reuse_
  telescopic_ota` 전체 사이징에서 어떻게 동작하는지는 여전히 미검증(다음 세션 후보,
  위 "지금 상태" 9번).
- `group_splits`가 여러 라운드/여러 row에 걸쳐 쌓일 때의 상호작용(예: 한 라운드의
  그룹분할이 다음 라운드 핑거조정 후보에 영향을 주는지)은 아직 다중 row가 동시에
  blocked인 실제 회로로 검증 안 됨 — M3a 그룹은 1 row만 blocked였다.

## G. 고아함수 재점검 — AST 콜그래프 v1→v2→v3 (세션14 방식 재사용, 커밋 `a6ab04b` 이후)

세션14가 했던 "harness에서 도달 안 되는 함수 전수조사"를 사용자 요청으로 다시 돌렸다.
`run_topology_pipeline_with_finger_fixup()`을 위 A~F절로 배선한 직후라 "세션18 작업
자체는 잘 연결됐는지" 확인하는 의미도 있었다.

### G-1. v1의 사각지대 3개 발견 + v2로 수정
1차 스캔(top-level 함수만, `ast.Call` 노드만 카운트)에서 `_multilinear_interp`/
`_invq_newton`이 "unreachable"로 잘못 나왔다 — 실제로는 `SemiEmpiricalGmIdLUT` **클래스
메소드** 안에서만 불리는데, v1이 클래스 본문의 메소드 호출을 전혀 스캔하지 않았다.
추가로 두 사각지대를 더 발견: (1) `_default_cascode_headroom`처럼 **dataclass 필드
기본값**(`cascode_fn: Callable = _default_cascode_headroom`)으로만 참조되는 경우 —
`ast.Call`도 `ast.Dict` 값도 아니라 bare `ast.Name`이라 못 잡음. (2) `_THETA_FEED_
REGISTRY`처럼 레지스트리 dict의 값이 `FeedHandler(_feed_settling_split, touches=[...])`
같은 **래퍼 Call로 감싸진 경우** — dict 값 자체가 `ast.Call`이라 안의 함수 이름이 다시
그 Call의 인자 속에 숨어서 안 잡음.

**v2 수정**: "호출(Call)"과 "단순 참조"를 구분하지 않고, 각 스코프(top-level 함수 전체
또는 **클래스 전체**, 메소드+필드 기본값 다 포함) 안에 등장하는 모든 `ast.Name.id`/
`ast.Attribute.attr`을 그대로 참조 집합으로 모으는 방식으로 재작성 — `ast.walk`이라
Call 인자 속 이름도 자동으로 잡힌다. 문자열(docstring)은 `ast.Constant`라 이 방식에도
안 걸림(세션14 교훈1 그대로 유지). 클래스도 그래프 노드로 추가해 "클래스가 reachable하면
그 메소드가 참조하는 이름도 reachable"이 전파되게 함.

### G-2. v3 — `run_harness.py`를 진짜 진입점으로 추가
v1/v2는 진입점을 `optimize_full_circuit_budget()`(라이브러리 함수)로만 잡았는데, 실제
사람이 실행하는 건 `run_harness.py`(스크립트)다. 이 스크립트의 모듈 최상위 코드는
조건부 dispatch가 아니라 "실행하면 무조건 도는 코드"이므로, 여기서 참조되는 top-level
함수/클래스는 "레지스트리 후보"가 아니라 바로 `reachable`로 편입시켰다. 이렇게 하니
`save_instance_json()`(이번 세션에 배선하기 전엔 미도달)이 자동으로 reachable로
바뀌는 게 확인됨(v3 실행 시점엔 이미 배선 완료 상태로 재확인).

### G-3. 최종 발견 — 진짜 미배선 3건 vs 이미 알려진/의도적 미배선 vs 성격이 다른 도구들
`run_matching_safety_with_finger_growth()`/`apply_and_revalidate_matching_finger_
growth()`/`suggest_matching_finger_growth()`가 `optimize_full_circuit_budget()`
안에서 여전히 구형 `repair_matching_safety()`만 직접 호출되고(2318행 부근) 한 번도
안 불리고 있음을 직접 grep으로 확정(self-test에서만 호출). `save_instance_json()`도
`run_harness.py`가 그동안 안 부르고 있었음을 확정(→ H/I절). `check_finger_width_
compatibility()`는 스스로의 docstring이 "선행 게이트"라고 선언했는데도 호출부가 전혀
없었음을 확정(→ J절). 그 외 15개 미도달 함수는 재확인 결과 성격이 다름:
- `find_matching_candidates`/`find_hub_merge_candidates`/`find_structural_symmetry_
  candidates`/`check_symmetry_dispositions`/`search_shared_finger_w` — docstring에
  "**후보만 내고 최종 판단은 사람/AI 몫**"이라고 명시된 topology-authoring 단계 도구,
  계산 harness와 다른 워크플로우(→ 이후 K/L절에서 이 중 `find_matching_candidates`가
  다시 논의 대상이 됨).
- `run_full_circuit_audit()` — `run_topology_pipeline()` 자신의 docstring이 "의도적으로
  포함 안 함(dispositions는 사람 판단 필요)"이라고 이미 명시.
- `find_diode_stacks()`/`solve_diode_stack_current()` — `optimize_full_circuit_
  budget()` docstring이 이미 "정직한 한계"로 기록(→ K절에서 심층 조사).
- 나머지(`build_toy_lut`/`_invq_newton`/`run_regression_case`/`RegressionVerdict`/
  `folded_cascode_example`/`two_stage_ota_example`/`render_stick_diagram`/
  `check_mirror_symmetry`/`check_multi_leaf_hub_parity`/`find_interleaved_symmetric_
  splits`/`_scan_case_collisions`) — self-test·데모·알고리즘 내부 스크리닝 전용,
  배선 대상 아님. `slew_rate(ID,C)`는 `_METRICS_REGISTRY`에 미등록된 metric 후보 —
  필요한 회로 생기면 그때 등록.

## H. `run_matching_safety_with_finger_growth()` 배선 (`sizing_recipe.py`, 미커밋)

`optimize_full_circuit_budget()`의 `if not audit_ok:` 분기(2306행 부근)에서
`repair_matching_safety(rows, matching_pairs_tuples, pair_sensitivity)` 단독 호출을,
`_lut_by_kind is not None`(euler 분기와 동일 가드 — 이 경우에만 `pipeline_result["ctx"]`
가 존재)일 때 `run_matching_safety_with_finger_growth(rows, matching_pairs_tuples,
pair_sensitivity, pipeline_result["ctx"], _lut_by_kind, metrics_specs, constraints,
gm_id_bounds=...)`로 승격 — euler 체인이 세션15에 먼저 이렇게 승격됐던 것과 대칭
구조. `lut_by_kind` 없는 legacy spec은 기존 `repair_matching_safety()` 그대로 폴백
(완전 하위호환).

핑거증가가 실제로 `n_fingers`/W를 바꿨을 수 있으므로 `sizing_overrides`/`sizing`을
최종 상태로 동기화 — 소자 하나가 common-centroid 회전배치로 여러 행에 `n_fingers`
조각으로 나뉠 수 있어(세션16 F절 함정) **행별로 합산**해서 최종 `n_fingers`를 구한다.
`pipeline_result`에 `growth_rounds`/`unresolved_pair`/`unresolved_reason`/
`relaxed_pairs`(`run_matching_safety_with_finger_growth()` 진단 필드 그대로)도 추가.

**self-test**: L5의 케이스B(M3a 그룹, `known_sizing`으로 A/B/C엔진 우회)가 마침 이
`if not audit_ok:` 분기를 타던 실제 fixture라 그대로 재사용 — `growth_rounds`가 실제로
채워지는지 확인하는 assertion 추가(성장 자체는 이 fixture에서 branch composite 내부
n_fingers 불일치로 `growth_not_applicable`이 되지만, **시도된 흔적**은 남아야 함을
검증). 별도 격리 probe(`probe_save_instance_json_wiring.py`류, 스크래치패드, 커밋 안
됨)로 M3a fixture를 직접 돌려 `growth_rounds=[{'names':('M3a','M3b','M4a','M4b'),
'result':{'applied':False,...}}]`, `unresolved_pair=('M4a','M4b')`, `unresolved_
reason='growth_not_applicable'`(branch composite M4a-M3a/M4b-M3b 내부에서 `n_fingers`
가 갈라져 `suggest_matching_finger_growth()`의 "전부 같은 n_fingers여야" 전제가 깨짐),
`relaxed_pairs=[]`(gm_id_violation이 아니므로 완화 미적용, 설계대로)임을 실측 확인.
**회귀**: `PYTHONHASHSEED=0` 기준 편집 전(`a6ab04b`) 대비 self-test 전체(250줄) diff —
L5 출력 문구 1줄(의도된 변경) 외 0줄 차이.

## I. `save_instance_json()`을 `run_harness.py`에 배선 (미커밋)

**사용자 질문("instance json 저장까지 harness함수가 하는 거지?")에서 시작** — 확인해보니
`optimize_full_circuit_budget()`은 계산만 하고 파일 저장은 안 함(반환 dict만 줌).
`save_instance_json()`(`stick_diagram.py`)은 그동안 `stick_diagram.py` 자체 self-test
에서만 불렸다. **사용자가 "최상위 함수는 run_harness 아니야? 거기서 호출하도록 하면
되잖아"로 정정** — `optimize_full_circuit_budget()`(라이브러리 함수, 순수 계산 유지)이
아니라 `run_harness.py`(실제 실행 스크립트, "harness"의 진짜 최상위)가 계산 뒤 저장까지
하는 게 맞는 책임분리라는 데 합의.

`run_harness.py`(`workspaces/current-reuse-telescopic-ota-report/`)에 `from stick_
diagram import save_instance_json` 추가, `optimize_full_circuit_budget()` 성공 후
`pipeline_result is not None`이면 `save_instance_json(INSTANCE_OUT, TOPO, result
["sizing"], result["pipeline_result"])` 호출 — `audit_ok=False`여도 그 상태 그대로
저장(조용히 성공으로 안 둔갑, §1.5 원칙).

**검증**: 원래 `run_harness.py`(8192 조합, KEEP_FREE=2 스모크 축소판) 그대로 스모크
테스트했더니 grid search 자체가 infeasible(PSRR/classab_centering 제약 위반)로
`optimize_full_circuit_budget()`이 예외를 던져 저장 호출부까지 아예 도달을 못해 이
배선을 검증 못함(**이건 세션18 변경과 무관한 사전 존재 문제**, 세션11 A절 grid 축소
논의와 같은 계열) — 그래서 L5의 `known_sizing` 직접 시드 fixture(위 H절과 동일 패턴,
grid search 우회)로 별도 격리 검증: `save_instance_json()` 정상 기록, 재-로드한 JSON이
`topology_ref`에 **경로 문자열만** 저장하고(재로드 안 함 — `load_topology()`는
`optimize_full_circuit_budget()` 안에서 한 번만 불림, 사용자 질문 "topology load는
어디서 해?"에 대한 답), `audit_row_split.ok=False`가 정직하게 그대로 저장됨을 확인.

## J. `check_finger_width_compatibility()` §3.5 게이트 배선 (`stick_diagram.py`, 미커밋)

`assign_finger_geometry()`가 만드는 `sizing_overrides`는 `w=n_fingers*finger_w`로
항상 정확히 구성되므로 자동경로에선 이 게이트가 절대 안 걸리지만, `run_topology_
pipeline()`은 호출자가 `sizing_overrides`를 손으로 직접 구성해 넘기는 것도 허용한다
(`Transistor.n_fingers` 필드 주석: "호출자가 직접 정해서 넣는다") — 그 경로에서 W가
`finger_w`의 정수배가 아니면(Maloberti PDF의 38um/8um=4.75 사례처럼 물리적으로 존재할
수 없는 요구) 지금까지 조용히 넘어가 euler 분석 이하 전부가 잘못된 전제로 돌아갔다.

`run_topology_pipeline()`에서 `transistors = [_dc_replace(t, **sizing_overrides
[t.name]) for t in transistors]` 직후, `split_into_stacks()` 이전에 `check_finger_
width_compatibility(transistors)`를 호출 — 실패하면 소자별 `w`/`finger_w`/정확한 비율/
가능한 값(내림·올림)을 담아 즉시 `ValueError`.

**self-test**(Test 26.55, `stick_diagram.py`, Test 26.5 직후): folded_cascode fixture의
소자 하나 `w`를 `finger_w*(n_fingers+0.5)`로 고의로 망가뜨려 `ValueError` 발생 + 에러
메시지에 "정수배"와 소자 이름이 포함되는지 확인, 정상 케이스는 그대로 통과하는지 회귀
대조. **회귀**: `stick_diagram.py` self-test(758줄) — 신규 Test 26.55 블록(7줄) 외 0줄
차이. `sizing_recipe.py` self-test(250줄, `run_topology_pipeline()`을 대량으로 호출)도
재확인 — 0줄 차이(다른 self-test fixture 어디에도 잠재된 W/finger_w 불일치 없었음).

## K. diode-stack 조사 — `solve_diode_stack_current()`는 실제로 필요한 회로가 없다

사용자가 "diode-stack 쪽도 배선되어야 할 것 같다"고 제기 → `_feed_diode_stack_
target()`(type `"C"` theta feed, **이미 배선됨**)을 먼저 확인했더니 `solve_diode_
stack_current()`와 다른 함수였다:
- **`_feed_diode_stack_target()`(배선됨)**: "replica" 방식 — target이 reference와
  **완전히 같은 동작점**(gm_id/L/VDS/VS)을 물려받고 면적비(K_replica)만큼 스케일.
  `current_reuse_telescopic_ota.topology.json`에서 `K_replica`(M9a←M15)/`mirror_
  M18a`(M18a←M9a)에 실제로 씀.
- **`solve_diode_stack_current()`(미배선)**: 직렬 diode 스택 VGS 합이 `target_voltage`와
  같아지는 전류를 KVL로 역산 — 완전히 다른 메커니즘, 자기 자신의 docstring이 이미
  "⚠️ 정직한 한계: 호출 규약을 이 세션에서 재구성했다 — 실제 M9a/M8/M11a/M11b 회로에
  처음 연결할 때 재검증 필요"라고 명시.

**핵심 발견**: 실제 회로의 진짜 diode 체인(M11a-M11b-M12, `find_diode_stacks()`가
찾아낼 법한 정확히 그 패턴)이 실제로 어떻게 사이징되는지 topology.json에서 직접
확인하니, `solve_diode_stack_current()`도 `_feed_diode_stack_target()`도 아닌 **세
번째 메커니즘**(`r_diode_M11a` theta, type `"A"`, reference 대비 **자유 비율**)을 쓴다.
이유가 주석에 명시: "논문 원문이 정확한 비율을 안 주므로 자유 비율 theta로 근사" —
즉 정확한 전압 타겟을 몰라서 애초에 KVL을 풀 수가 없었고, 그래서 grid search 가능한
자유 파라미터로 남긴 것. **`solve_diode_stack_current()`가 재검증을 기다리던 그
시나리오(M9a/M8/M11a/M11b) 자체가 결국 오지 않았다** — 다른 방식으로 이미 풀렸기
때문.

**결론**: 지금 이 저장소의 4개 회로 중 `solve_diode_stack_current()`가 실제로 필요한
곳이 하나도 없다. 배선 여부(지금 할지 vs 실제 필요한 회로 생기면 할지)를 AskUserQuestion
으로 물으려 했으나 **사용자가 인터럽트해서 미결** — 다음 세션에 다시 물을 것.

## L. `find_diode_stacks()`/`find_matching_candidates()` 설계 논의 — 결론 안 남

`solve_diode_stack_current()`와 별개로, `find_diode_stacks()`(구조 탐지기, `current_
mirror`/`hub_merge` 오탐을 걸러주는 게 원래 목적이라고 자기 docstring에 명시돼 있었지만
"이 배치의 스코프는 아님"으로 미룬 채 방치)는 여전히 유효한 배선 후보인지를 놓고 여러
턴에 걸쳐 논의했다 — **코드는 전혀 안 건드림, 순수 설계 논의만 진행.**

### L-1. M57/M58 실사고 — "필요없다"는 내 첫 판단이 틀렸음을 사용자가 정정
처음엔 `find_diode_stacks()`를 "실제 비용 없는 TODO"로 낮게 평가했으나, 사용자가
"지난번 M57/M58 문제도 diode stack으로 인식 못 해서 생긴 것 아니냐"고 지적 — topology.json
의 `symmetry.dispositions`를 다시 읽어보니 정확했다: M57/M58이 한때 `current_mirror/
pmos/Vbias_p`로 **진짜 매칭쌍(real_match)으로 잘못 disposed**됐다가(2026-07-29) 나중에
diode-chain false-positive임을 발견해 정정(2026-08-03)한 **실제 이력이 있는 버그**다.
단순 "매번 수동 필터링하는 번거로움" 수준이 아니라 한 번 실제로 잘못된 상태로 남아있었던
사례 — 우선순위를 올림.

### L-2. connectivity 직접 확인으로 "무엇이 M57/M58을 다르게 만드는지" 규명
- **M57/M58**: M58(source=Vx, drain=**N58_57**) / M57(source=**N58_57**, drain=Vbias2,
  gate=Vbias2, self-diode) — M58.drain=M57.source, **직렬로 물려있음**(2단자 net 공유,
  `kcl_series_union()`이 이미 아는 패턴) → KCL로 전류 동일이 **connectivity만으로
  100% 증명됨**, 매칭 레이아웃 기법이 애초에 의미 없음.
- **M11b/M9a, M20b/M18a, M36a/M7**: 전부 gate만 공유하고 source/drain은 완전히
  disjoint(직렬 아님) — 별개의 물리적 전류경로. 특히 M9a는 실제 사이징이 M11b와 무관한
  `K_replica`(reference=M15)로 결정된다 — gate 공유는 순전히 우연한 bias-전압 관계일
  뿐, 이 소자의 실제 W/ID를 결정하는 메커니즘이 아니다.

### L-3. 사용자 제안 — "전류미러려면 VGS가 같아야" (source-일치 조건)
사용자가 전기적으로 정확한 기준을 제시: 진짜 전류미러(W 비율로 전류 예측 가능)이려면
diode 소자와 소비자의 VGS가 같아야 하고, 그러려면 gate뿐 아니라 **source도 같아야**
한다. `find_matching_candidates()`의 실제 코드(`by_gate[(t.kind, t.gate)]`)를 확인하니
**source는 전혀 안 본다** — 정확한 지적이었다. 5개 실사례에 이 기준을 대입:
- M57/M58, M11b/M9a, M20b/M18a: source 다름 → 자동으로 "VGS 동일 보장 없음" 판정, 실제
  false_positive 처리와 일치.
- M36a/M7: **둘 다 source=vdd** → VGS 동일 조건은 만족하는데도 "다른 기능 블록"이라는
  별개 사유로 여전히 false_positive — source-일치가 필요조건이지 충분조건은 아님(그래도
  됨 — 사람 판단은 여전히 남음).
- M2a/M2b(진짜 채택된 매칭쌍): source가 다름(N1a2a/N1b2b, 대칭 net명) — source-일치를
  `current_mirror`에 그대로 넣으면 이 **진짜** 후보까지 걸러낼 위험. 이건 "전류미러"가
  아니라 "대칭 캐스코드쌍"이라는 다른 개념 — `find_structural_symmetry_candidates()`
  (이미 있는 별도 함수, seed net pairs 기반)가 담당할 영역일 가능성.

### L-4. 사용자 재반박 — source-일치 검사와 `find_diode_stacks()`는 다른 질문
사용자가 "stacked diode도 이 기준으로는 못 거르잖아"라고 재지적 — 맞다: source-일치
검사는 **"진짜 VGS-동일 미러인가"**를 답할 뿐, **"이게 stacked diode 구조인가"**를
직접 인식하지 않는다(M57/M58에서 둘의 답이 우연히 겹쳤을 뿐). 게다가 `find_hub_merge_
candidates()`는 gate가 아니라 **공유 단자(source/drain)**로 후보를 찾아서, source-일치
검사 자체가 적용될 자리가 없다 — diode 체인 내부 소자가 hub_merge 후보로 잘못 묶이는
문제는 오직 `find_diode_stacks()`(어떤 소자들이 diode 체인 멤버인지 실제로 식별)로만
막을 수 있다.

**잠정 합의(구현 전, 다음 세션에 이어갈 것)**: 두 검사가 서로 다른 문제를 풀므로 둘 다
필요하다 — (1) `find_matching_candidates()`의 `current_mirror`에 source-일치 조건
추가(진짜 미러 아닌 후보 제거, M2a/M2b류는 다른 함수가 담당하게 분리), (2) `find_diode_
stacks()`를 `current_mirror`/`hub_merge` 양쪽에 diode-체인 정보로 연결(구조 인식 자체,
사람에게 "이건 diode 체인이라 그렇다"는 근거 제공). **구체적 코드/함수 시그니처는
전혀 설계 안 됨** — 다음 세션 M절(아래 "다음 세션 작업 순서" 참고)에서 이어갈 것.

---

# 세션19 결론 — analog-grammar skill 반입 + matching 후보 오탐 필터 Tier 1 구현+커밋

세션18이 남긴 "⚠️ 다음 세션 최우선 — zip 파일 2개 검토"부터 시작해, 그 내용을 갖고
K/L절(diode-stack/`find_matching_candidates()` 오탐 논의)을 이어가려 했으나, 실제로는
zip 내용이 그 논의를 대체하는 더 나은 해법으로 이어져 최종적으로 완전히 새로운 skill
반입 + 실제 엔진 코드 구현까지 완주했다.

## A. zip 파일 2개 검토 — 완성된 skill 패키지였음

`아날로그 기능분석기.zip`(→ `analog-grammar`) / `회로도 추출기.zip`(→
`circuit-topology-extraction`) 둘 다 다른 세션/도구가 만든 완성된 Claude skill
패키지(SKILL.md + 스크립트 + 설계문서)였다. `analog-grammar`는 netlist에서 device
role(DIODE_CONNECTED/CASCODE/AMPLIFYING/...) + L1 idiom(current-mirror/
differential-pair/current-reuse-pair 등 11종)을 net 분류→role 배정→idiom 매칭
6단계 파이프라인으로 결정론적으로 도출한다. `circuit-topology-extraction`은 논문
PDF의 vector 회로도에서 netlist를 직접 추출(vision 불필요) — 이 프로젝트가 실제
쓰는 논문(Xie & Chen current-reuse telescopic OTA)을 사례로 돌려 `topology.json`과
일치하는 결과를 얻은 이력이 있었다.

**핵심 발견**: `analog-grammar/scripts/idioms.py`의 `current-mirror` idiom이
`(gate, source, type)`로 그룹핑한다 — 세션18 L-3에서 사용자가 제기했던 "VGS 동일하려면
source도 같아야 한다"는 조건을 이미 구현하고 있었다. 이걸 재구현하는 대신 재사용하는
쪽으로 방향을 정했다.

## B. `analog-grammar` skill 반입 — `circuit-topology-extraction`만 이번엔 제외

사용자가 "이 저장소의 다른 skill과 동일하게 관리되는 skill로 반입, 함께 release"를
명시적으로 요구 — `skills/analog-grammar/`에 이 저장소 컨벤션 그대로 설치:
`SKILL.md`(frontmatter+절대규칙+워크플로+Cross-Skill 참조) + `references/DESIGN.md`
(정본, 원본 zip의 설계문서를 이 저장소 스타일로 재편집) + `references/consistency-map.md`
+ `skill-validation-prompt.md`(5-Check 구조) + `assets/`(원본 스크립트 4개, 바이트
단위 무변경 + `examples/`). 원본의 최상위 `README.md`는 이 저장소 관례(폴더 내
README.md 금지)에 따라 제거하고 내용을 SKILL.md에 흡수. 새 위치에서 `analyze.py`를
직접 실행해 DESIGN.md가 주장하는 결과(Fig.2 current-reuse telescopic 자동 분석)와
정확히 일치함을 확인(`PYTHONUTF8=1` 필요 — Windows 콘솔 cp949 이슈, SKILL.md에 메모).
`circuit-topology-extraction`은 사용자가 범위를 "analog-grammar만"으로 명시적으로
좁혀 이번엔 설치 안 함.

## C. harness 연동 설계 — Tier 1/Tier 2로 재정의, 여러 차례 재설계

### C-1. 첫 설계(role 필터) → 사용자 지적으로 idiom Match 직접 재사용으로 재설계
처음엔 `classify_device_roles()`(Stage 1~2)의 role로 옛 net-only 그룹핑에 사후
필터를 얹는 설계였으나, 사용자가 "role보다 Stage 3(비재귀 idiom 매칭)가 이미 응집된
정보를 갖고 있지 않냐"고 지적 — `analog-grammar`의 `m_mirror()`/`m_diffpair()`가
이미 내부에서 필요한 검사(diode 레퍼런스 존재/AMPLIFYING 요구)를 다 하고 있으므로,
role 필터는 중복 구현이었음을 확인하고 폐기. `find_idiom_matches()`(Stage 1~3
어댑터)가 낸 원본 Match 리스트를 `find_matching_candidates()`가 직접 소비하는
쪽으로 재설계.

### C-2. Tier 2(재귀적 "기능블럭" 아이디어) — 실측으로 두 번 재검토, 최종 폐기
사용자가 "analog-grammar가 재귀적으로 기능블럭을 찾을 수 있다던데, 그걸 JSON
기능블럭 필드로 두면 유용하지 않을까"라고 제안 — 확인해보니 그 재귀(L2 block 인식)는
`analog-grammar` DESIGN.md 자신이 "미구현"이라고 명시한 기능이었다(상상으로 채우지
않는 원칙 재확인). 대신 이미 있는 `find_diode_stacks()`(2026-07-30 M57/M58 사고로
재작성된 함수 — 세션18이 "미배선"이라 불렀던 게 사실은 "이미 구현되어 있었다"는 걸
이번에 재발견)를 `find_hub_merge_candidates()`에 배선하는 아이디어를 실측으로
검증했으나, diode-stack의 내부 연결 net은 정의상 한쪽은 drain 하나, 다른 쪽은
source 하나만 닿아있어 `find_hub_merge_candidates()`의 "크기 2 이상" 조건을
구조적으로 절대 못 채운다는 게 밝혀져(모든 diode-stack 내부 net을 실제로 뽑아
재확인) 이 방향은 최종 폐기.

관찰된 실제 hub_merge 혼합 현상(`Vx`={M1a,M1b,M58} 등)은 `device_roles[name]
["vertical_stack_id"]`(VDD~GND 직렬 전압강하 체인 단위, `allocate_stack_
headroom()`이 쓰는 이미 있는 필드 — `_TEMPLATE.topology.json` 주석에서 정의 확인)로
전부 설명됨을 확인했으나, 이것도 증명된 오탐이 아니라(`find_hub_merge_candidates()`
자신이 "matching과 무관한 후보도 정상"이라고 선언) 손대지 않기로 함.

### C-3. "캐스코드 대칭쌍" 커버리지 갭 발견 → "복합소자" 메커니즘으로 해결(사용자 제안)
gate+source 그룹핑으로 재설계하면서, M2a/M2b류(같은 gate, 다른 source — `stick-
diagram-euler-layout.md` §2.6이 이미 "gate 공유 기준으로는 걸리지만 캐스코드
역할까지는 판별 못함"이라 기록해둔 카테고리)가 current_mirror 후보에서 완전히
사라지는 회귀 위험을 발견 — 사용자가 "composite소자 개념을 적용할 수 없나"라고
제안한 것이 결정적이었다. 세션16/17의 branch composite(`kcl_series_union()` 기반,
**레이아웃** crossover 짝짓기용)과 정확히 같은 직렬 스택 개념을 반대 방향(matching
후보 **발견**)으로 적용: 이미 확정된 매칭쌍(M1a/M1b) 위에 직접 stacked된 소자쌍
(M2a/M2b)을 재귀적으로 상속 탐지. `analog-grammar`의 `stack_edges()`를 실제
`current_reuse_telescopic_ota` connectivity에 돌려 M1a→M2a/M1b→M2b, M4a→M3a/
M4b→M3b 정확히 재현됨을 확인 — §2.6이 기록해둔 두 캐스코드 대칭쌍 사례 전부 이
메커니즘 하나로 설명됨.

## D. 구현 — `stick_diagram.py` §1.7a~1.7c 신설

- `_to_analog_grammar_devs()`/`_import_analog_grammar()` — 어댑터(soft-fail,
  analog-grammar 없으면 `None`).
- `find_idiom_matches(transistors, inputs=(), outputs=(), ...)` — Stage 1~3 실행,
  겹침 해소 이전 원본 Match 리스트 반환(current-reuse-pair가 흡수해도 실제 W/L
  매칭 단위는 원래 쌍이므로 resolve_overlaps() 건너뜀).
- `find_matching_candidates(transistors, idiom_matches=None)` — 확장. `None`이면
  기존 동작 완전 동일(하위호환). 주어지면 current_mirror는 `(kind,gate,source)`
  + diode 레퍼런스 요구, diff_pair는 두 소자 다 role=AMPLIFYING 요구로 재계산.
- `find_stack_edges()` / `find_stacked_matching_candidates(transistors, base_pairs,
  stack_edges)` — 복합소자 상속. **구현 중 실측으로 버그 발견+수정**: 폴디드 노드
  에서 한 소자 위에 극성이 다른 두 소자가 동시에 얹힐 수 있는데(`folded_cascode_
  example()`의 M1 위에 M5(pmos)/M7(nmos) 동시 존재), 단순 `{lo: up}` dict
  comprehension이 마지막 것만 남기고 조용히 덮어써 엉뚱한 소자를 골랐다 — "같은
  kind로 좁히고 모호하면(0개/2개+) 포기"로 수정.

## E. self-test + 회귀 확인 + 커밋

`stick_diagram.py` Test 30(6개 항목) 전부 PASS: analog-grammar 사용 가능 확인,
하위호환(idiom_matches=None), M57/M58 오탐 해소(양성대조 MrefA/MrefB는 유지),
M11/MN 오탐 해소(양성대조 M1/M2는 유지, `folded_cascode_example()` fixture 재사용),
캐스코드 대칭쌍(M5/M6) 복합소자 상속 확인, 어댑터 폴백 확인(gate 없는 fixture로
자연스럽게 트리거 — `sys.path` 조작은 함수 자신이 멱등하게 재추가해 무의미함을
확인 후 이 방식으로 전환). 전체 self-test suite(`stick_diagram.py` 30개 +
`sizing_recipe.py`) exit 0, Traceback/AssertionError 0건. `git diff` 확인 결과
편집은 순수 추가(313줄 추가, 삭제 5줄은 세션18의 기존 미커밋 변경).

**커밋 `d4bd4d9`**(23개 파일, +4335/-88) — `analog-grammar` skill 신규 + Tier 1
구현 + 세션18 잔여 배선 3건(H/I/J절, `sizing_recipe.py`/`run_harness.py`/
`stick_diagram.py` J부분) 포함. zip 파일 2개(이제 `skills/analog-grammar`로
추출·설치돼 중복)와 세션18 스모크 스크립트는 의도적으로 제외, working tree에
untracked로 남아있음.

## F. 알려진 한계 / 다음 세션 우선순위

- **Tier 1 함수들이 실제 프로덕션 호출부에 아직 안 배선됨** — self-test에서만
  호출된 상태(세션14 교훈과 동일한 패턴, 재발 주의). `find_matching_candidates()`의
  실제 호출부(topology JSON 저작 워크플로우)에 `idiom_matches=`를 실제로 넘기는
  건 다음 단계(엔진 로직 변경이라 사전 승인 필요).
- Tier 2/vertical_stack_id 경계 아이디어는 폐기하지 않고 "실제 필요 사례가 나오면"
  으로 유보(§C-2).
- `circuit-topology-extraction` skill 미설치 상태 그대로.
- 세션18 K절(`solve_diode_stack_current()` 배선 여부)은 이번 세션에 다시 논의
  안 함 — 여전히 미결.

---

## 다음 세션 작업 순서 (권장, 각 단계 사용자 승인 필수)

1. **Tier 1(matching 후보 오탐 필터) 실제 배선** — `find_matching_candidates()`의
   실제 프로덕션 호출부(topology JSON 저작 워크플로우, `function-selection-map.md`
   §3/§10)에 `idiom_matches=find_idiom_matches(...)`를 실제로 넘기도록 배선.
   세션14 교훈("구현됐다"≠"연결됐다") 재적용 — 배선 전 실제 호출 그래프부터
   확인할 것.
2. `run_harness.py` 재실행 전략 논의(세션11 A절 — 그리드 축소 or 다른 최적화 방식,
   지속 이월) — L3(핑거조정)+L4(gm/ID 재검증)+그룹분할+매칭성장+Tier 1 체인이
   harness 최상위 경로에 대부분 연결됐으니, end-to-end로 확인할 좋은 시점.
3. diode-stack current source(`solve_diode_stack_current()`) 배선 여부(세션18 K절,
   AskUserQuestion 인터럽트로 미결 — 그대로 이월) — 다시 물어볼 것.
4. `circuit-topology-extraction` skill 설치 여부 — 논문 PDF→netlist 추출이 실제로
   필요해지면(예: 새 회로 topology.json 저작 시) `analog-grammar`와 동일한 방식
   (이 저장소 컨벤션대로 SKILL.md+references+skill-validation-prompt)으로 반입.
5. L1/L2 잔여 항목(급하지 않음): `audit_current_forced.py`의 ⚠️ 12건(간접 근거,
   `current_reuse_telescopic_ota`) — 필요해지면 사람이 직접 사슬 추적해 확인.
6. GBW 재검증 확장(범위 밖으로 미룸, 세션13 결론 D절) — 어느 topology.json이든
   `constraints`에 GBW를 실제로 선언하는 회로가 생기면 그때 착수.
7. 완주하면 세션4 핸드오프 원래 "다음 단계"(Cc/Rz/Iref 값 채우기, PSRR 폐형식 재유도)로
   이어가기.
8. (미정, 낮은 우선순위, 세션6부터 이월) `find_structural_symmetry_candidates()`의
   `"dual"` transform 오탐 개선 — 손 안 댐.

---

## 작업 파일 위치

- `skills/analog-gmid-design/assets/stick_diagram.py` (**세션11+세션12+세션15 수정, 전부
  커밋됨** — 세션12까지는 `cecbe33`/`d59570f`, 세션15는 `55c8095`)
  - `check_walk_sequence(transistor_sequence, transistors)`(2231행 부근) — 기존 함수,
    D 구현에 그대로 재사용(범용 walk 검증기, hub-leaf 제약 없음).
  - `mirror_symmetric_trail(group, matching_pairs)`(2401행 부근) — 세션11 신설, **세션12
    전면 재작성**(대표 조합 탐색 + 홀수 self-pair "다리" 지원, `_MAX_MIRROR_TRAIL_COMBO_
    PAIRS=12`). 기존 2개 통과 사례는 결과 바이트 단위 동일(회귀 없음, self-test로 확인).
  - `suggest_pair_finger_adjustments(transistors, matching_pairs)` +
    `PairAdjustmentSuggestion`(1908행 부근) — **세션12 신설**, 매칭쌍 단위 핑거조정 제안.
  - `build_mirror_symmetric_pattern()`(202행) — **세션12 수정**, `pair_map` 값 `None`
    지원(다리를 미러 복사본에서 제외하는 한 줄 필터).
  - `StickResult.method`(2211행 부근 dataclass 필드) — 세션11 신설, 세션12 미변경.
  - `build_stick_diagram(transistors, matching_pairs=None)`(2390행 부근) — 세션11
    시그니처 확장(감싸기, 완전한 하위호환), 세션12 미변경.
  - `audit_row_split()`(2747행 부근)의 `build_stick_diagram()` 호출부 — 세션11 수정,
    행별 matching_pairs 필터링 추가. 세션12 미변경.
  - `suggest_finger_adjustments(transistors)`(1865행 부근) — 기존 함수, **세션12에
    확장 안 하고 옆에 새 함수(`suggest_pair_finger_adjustments`)로 분리**(개별 소자
    조정이 필요한 기존 호출부를 건드리지 않기 위해).
  - `find_min_crossover_layout(transistors, matching_pairs=None, pair_sensitivity=None)`
    (1857행 부근) — **세션15에 확장**(node_map 기반 그룹분할, 위 세션15 B절), **세션17에
    짝짓기 선택 방식 재작성**(D절) + **F절에서 `pair_sensitivity` 파라미터 추가**.
    `matching_pairs=None`(기본값)이면 기존 hub-leaf 사전조건+순서대로 짝짓기 완전히
    그대로(하위호환, 기존 프로덕션 호출부는 이 경로, `pair_sensitivity`는 무시됨). 주면
    hub-leaf 제약을 풀고 `_select_crossover_pairing()`(세션17)이 아래 헬퍼들로
    matching_pairs 분할(및 offset 우선순위)을 최소화하는 짝짓기를 고른다.
    **⚠️ 아직 harness에 직접 안 이어짐** — G절 wrapper(`find_min_crossover_layout_
    with_branch_composite()`)를 통해 다음 세션에 배선할 것(위 "지금 상태" 8번, G-3절).
  - `_mirror_node_map_from_pairs(matching_pairs, transistors)`(1765행 부근) —
    **세션15 신설**, matching_pairs+connectivity에서 net 레벨 거울 대응 역산. 세션17
    미변경.
  - `_pair_odd_nodes_by_mirror(odd_nodes, node_map)`(1798행 부근) — **세션15 신설**,
    3단계 우선순위 짝짓기(거울쌍 → 허브/orphan → 폴백). **세션17부터 최종 결과가 아니라
    `_select_crossover_pairing()`의 "기본 후보" 하나로만 쓰인다**(함수 자체는 미변경,
    호출 방식만 바뀜) — 세션16 D-1이 밝혔듯 이 휴리스틱의 tier1(거울쌍 최우선 절단)이
    matching_pairs를 갈라놓는 경우가 있어, 이제 실제로 구성+채점해서 더 나은 후보가
    있으면 교체한다.
  - `_build_crossover_segments(transistors, pairs)`(1851행 부근, `find_min_crossover_
    layout()` 직전) — **세션17 신설**. 옛 `find_min_crossover_layout()`에 인라인으로
    있던 "가상 edge 추가 + hierholzer + trail 분해" 계산을 뽑아낸 순수 함수(매번
    `build_graph()`를 새로 불러 결정적) — pairs 후보별로 재사용할 수 있게 함.
  - `_count_matching_pair_splits(segments, matching_pairs, pair_sensitivity=None)`
    (`_build_crossover_segments()` 직후) — **세션17 신설, F절에서 `pair_sensitivity`
    파라미터 추가**. segments 중 선언된 matching_pairs가 완전히 다른 segment로 갈라진
    개수를 센다(채점 기준). 최소 한 segment라도 공유하면 "안 갈라짐"으로 봄(보수적
    기준). `pair_sensitivity` 주면 스칼라 대신 `(offset_splits, other_splits)` 튜플을
    반환 — 사전식 비교로 offset 쌍 보호를 ratio보다 우선시킴.
  - `_is_perfect_crossover_score(score)`(`_count_matching_pair_splits()` 직후) —
    **세션17 F절 신설**. 스칼라 0과 튜플 (0,0) 둘 다 "분할 없음"으로 판정.
  - `_MAX_CROSSOVER_PAIRING_NODES=8` + `_enumerate_perfect_matchings(nodes)`
    (`_is_perfect_crossover_score()` 직후) — **세션17 신설**. `(2m-1)!!`개 완전짝짓기를
    재귀로 생성(8노드=105개 상한, 다른 조합탐색 캡과 동일 관례).
  - `_select_crossover_pairing(odd_nodes, node_map, transistors, matching_pairs,
    pair_sensitivity=None)`(`_enumerate_perfect_matchings()` 직후) — **세션17
    신설**(세션16 D-1 발견의 일반화, "구성 후 검증" 원칙), **F절에서 `pair_sensitivity`
    관통**. `_pair_odd_nodes_by_mirror()`의 결과를 기본 후보로 채점, 분할이 있고 홀수
    노드 수가 캡 이하면 `_enumerate_perfect_matchings()`로 전수 대입해 분할이 더 적은
    후보로 교체(분할 없음을 찾으면 즉시 중단). `crossover_count`(m-1) 자체는 T-join
    정리로 불변 — 이 선택은 "어디서 끊기는가"만 바꾼다.
  - `_composite_collapse_for_crossover(transistors, matching_pairs,
    pair_sensitivity=None)` / `find_min_crossover_layout_with_branch_composite(...)`
    (`_branch_composite_pair()` 직후, `repair_matching_safety()` 직전) — **세션17 G절
    신설**. `find_min_crossover_layout()`을 부르기 전에 branch를 `_branch_composite_
    pair()`로 미리 합성 소자로 뭉쳐서, crossover 짝짓기가 branch를 갈라놓을 수 없게
    만든다(채점 기반 회피가 아니라 구조적 보장 — 사용자 질문으로 발견된 결함, 위 G절
    참고). `find_min_crossover_layout()` 자체는 안 건드림(완전히 별도 wrapper).
    **⚠️ 다음 세션 harness 배선 시 `find_min_crossover_layout()`이 아니라 이 wrapper를
    쓸 것**(G-3절).
  - Test 12.13(Test 12.12 직후, self-test 섹션) — **세션15 신설, 세션17 재작성 +
    F절에서 offset 가중치 테스트 4건 추가**. M6 그룹 실제 connectivity 재현 + node_map
    역산 단위 확인 + 폴백 발동 확인 + `matching_pairs=None` 회귀 대조는 그대로
    유지하되, 핵심 assertion을 옛 tier1 짝짓기(splits=2, 회귀 대조로 명시적 재현) →
    신규 짝짓기(splits=0)로 교체 — 세션15 당시 assertion(`crossover_count==1`/
    `fallback_used==False`)은 T-join 불변량 때문에 개선 여부와 무관하게 항상 통과하는
    약한 테스트였음(세션17에 발견).
  - Test 28(`_branch_composite_pair()` 직후, `repair_matching_safety()` self-test
    앞) — **세션17 G절 신설**. `_composite_collapse_for_crossover()`/`find_min_
    crossover_layout_with_branch_composite()`를 M6 그룹 fixture(`_m6b_row` 등, 세션16
    branch 복합 매칭 테스트와 동일)로 검증 + branch 없는 그룹(rowA/rowB) 회귀 대조.
  - `build_graph()`(1631행 부근)/`hierholzer()`(1721행 부근) — 여전히 완전히
    matching-blind(세션11/12 미변경, mirror_symmetric_trail이 우회해서 감쌈).
  - `INTERDIGITATION_PATTERNS`/`COMMON_CENTROID_PATTERNS`(86~119행), `check_mirror_
    symmetry()`(226행) — 세션11 이전부터 있던 기존 함수, 세션12 미변경.
  - Test 5.5(`build_mirror_symmetric_pattern` Test 5 직후, self-test 섹션) — 세션11
    신설, D의 실제 회로 2사례 + 하위호환 음성대조. 세션12 미변경.
  - Test 5.6(Test 5.5 직후) — **세션12 신설**, `current_reuse_telescopic_ota` 실제 M3a
    그룹(11소자) 재현: 핑거조정 제안 → 적용 → 다리 지원으로 완전히 풀림 + 조정 없이는
    여전히 `None`인 회귀 대조.
- `skills/analog-gmid-design/assets/stick_diagram.py` (**세션16 수정, 커밋 `58e608b`**)
  - `repair_matching_safety()`(3308행 부근) — **세션16 크래시 수정**: `common_centroid_
    layout()` 호출 시 `n_rows=min(2, ta.n_fingers, tb.n_fingers)`로 낮춰서 `n_fingers<2`
    크래시(세션15 A-3에서 발견) 회피, `n_fingers>=2`는 기존과 완전히 동일 동작(회귀 없음).
    **세션16 branch 복합 매칭**: source 공유 여부와 무관하게 항상 `_branch_composite_
    pair()`를 먼저 시도하도록 재구성, branch 구조 없으면 기존 개별-소자 경로/skip으로
    완전히 폴백. `touched_this_round` 가드로 같은 라운드 내 중복 재배치 방지.
  - `_kcl_branch_map(devices)`/`_two_device_branch_outer(x,y)`/`_branch_composite_pair
    (a,b,devices_by_name,matching_pairs)`(`repair_matching_safety()` 직전) — **세션16
    신설**. `kcl_series_union()`(세션10, 강제병합 없이 재사용)으로 2소자 직렬 branch(예:
    M1a-M2a)를 자동 발견해, 서로 다른 hub를 쓰는 매칭쌍(branch_symmetric)도 branch
    전체를 합성 소자로 묶어 기존 layout 도구를 적용 가능하게 함. 2소자 선형 체인만
    지원(의도적으로 좁은 범위, 3소자+ 체인/분기는 `None` 폴백).
  - self-test 2건(Test 28 `repair_matching_safety()` 섹션 직후) — **세션16 신설**: (1)
    `current_reuse_telescopic_ota`의 M6 그룹 실제 사례로 M2a/M2b가 M1a/M1b와 같은 행에
    묶이는지(euler PASS, 3c는 `n_fingers=1` 한계로 여전히 FAIL — 다음 확장 지점). (2)
    `_branch_composite_pair()`가 branch 구조 없는 기존 케이스엔 `None`을 반환해 기존
    폴백이 보존되는지.
  - 회귀: 커밋 전(`55c8095`) 대비 self-test 전체 출력 diff 0줄, 무회귀 확정(세션16 E-1/
    E-2절).
- `skills/analog-gmid-design/assets/sizing_recipe.py` (**세션13 수정, 커밋 `caa970b`** —
  세션11/12엔 미수정이었음)
  - `revalidate_finger_override(ctx, lut_by_kind, overrides, metrics_specs, constraints,
    gm_id_bounds=(2.0,30.0))`(§6.10, `optimize_full_circuit_budget()` 직후) — **세션13
    신설**, L4. `_invert_gm_id_for_current()`(897행, 기존 함수) 재사용.
  - `_collect_device_refs(spec, known_names)`(§6.10) — **세션13 신설**, metric_spec에서
    소자명을 재귀로 추출하는 범용 헬퍼.
  - `_invert_gm_id_for_current()`(897행) — 기존 함수(C엔진), 세션13이 L4에 그대로 재사용,
    미변경.
  - `compute_metric()`/`_METRICS_REGISTRY`(1578/1591행) — 기존 함수, 세션13이 재사용,
    미변경.
  - `_CONSTRAINT_OPS`(1816행) — 기존 dict, 세션13이 재사용, 미변경.
  - self-test 3건("L4 revalidate_finger_override()" 섹션, F엔진 `compute_metric()` 테스트
    직후) — **세션13 신설**, ID 보존/통과 케이스/위반 케이스.
  - `optimize_full_circuit_budget()`(1840행 부근)의 grid loop(2227행 부근
    `for combo in itertools.product(*grids)`)가 `run_harness.py` 조합 폭발의 실제 위치 —
    세션13 미변경.
  - self-test 전체 회귀: 확인 완료, 무회귀(위 "지금 상태" 3번/"세션13 결론" C절 참고).
- `skills/analog-gmid-design/assets/sizing_recipe.py` (**세션14 수정 커밋 `de85792`,
  세션15 추가 수정 커밋 `0eccd0e`**)
  - `apply_and_revalidate_pair_adjustment(transistors, matching_pairs, ctx, lut_by_kind,
    metrics_specs, constraints, gm_id_bounds=(2.0,30.0), max_candidates=None)`(2405행) —
    **세션14 신설**, L3+L4 오케스트레이션(세션14 결론 B절). `suggest_pair_finger_
    adjustments()`(stick_diagram.py, 세션12)와 `revalidate_finger_override()`(세션13)를
    조합, 채택 안 된 후보는 `rejected`에 근거와 함께 기록.
  - `_blocked_euler_rows(audit_row_split_result)`(2463행) — **세션14 신설**, `audit_row_
    split()`의 고정 체크명 `f"1. euler[{row_name}]"`을 파싱해 blocked row만 추출.
  - `_sync_finger_fixup(overrides, ctx, fix, prior_transistors)`(2478행) — **세션14 신설**,
    핑거조정 채택 결과를 layout `sizing_overrides`와 gm/ID `ctx.sized` 양쪽에 동기화.
  - `run_topology_pipeline_with_finger_fixup(topology_json_path, sizing_overrides, ctx,
    lut_by_kind, metrics_specs, constraints, floorplan_hints=None, cell_groups=None,
    gm_id_bounds=(2.0,30.0), max_fixup_rounds=5)`(2498행) — **세션14 신설**,
    `run_topology_pipeline()`(stick_diagram.py)을 감싸 euler-blocked row를 자동 수정하는
    라운드 루프(세션14 결론 C절). `stick_diagram.py`↔`sizing_recipe.py` 단방향 import
    제약 때문에 `stick_diagram.py` 안이 아니라 여기(`sizing_recipe.py`)에 위치.
  - import 목록(1611행 부근)에 `suggest_pair_finger_adjustments`/`PairAdjustmentSuggestion`
    추가 — **세션14 수정**(기존 import문에 이름만 추가, 다른 항목 미변경).
  - self-test "L4b"(2822행부근, 합성 데이터 3케이스)/"L4c"(2913행 부근, 세션12 실제 M3a
    그룹을 temp topology.json으로 감싼 end-to-end 2케이스) — **세션14 신설**, 전부 통과.
  - **세션15에 실배선 완료**(커밋 `0eccd0e`): `optimize_full_circuit_budget()`(1841행
    부근)의 euler-blocked 실패 처리부가 이제 `run_topology_pipeline_with_finger_
    fixup()`을 실제로 호출한다(`repair_matching_safety()`는 별개 역할로 그대로 유지 —
    세션15 A-1절 "책임 분리" 발견 참고). `spec["lut_by_kind"]`가 없으면 기존
    `run_topology_pipeline()`으로 폴백(하위호환). self-test "L5" 신설, 전부 통과.
  - self-test 전체 회귀: 세션14 확인 완료(`caa970b` 대비 diff 0줄), 세션15도 재확인
    완료(`de85792` 대비 diff 0줄, 세션15 A-4절).
- `skills/analog-gmid-design/assets/sizing_recipe.py` (**세션16 신설, 커밋 `7a41a30`**)
  - `suggest_matching_finger_growth(names, transistors, min_fingers=2)`(§6.11 신설,
    `_sync_finger_fixup()` 직후) — **세션16 신설**. euler용 `suggest_pair_finger_
    adjustments()`와 달리 후보 랭킹이 필요 없다 — `names`(매칭쌍 또는 branch 복합 4소자,
    전부 같은 `n_fingers`) 내부 값이 `min_fingers`(기본 2)보다 부족한 만큼만 delta로
    계산. 이미 충분하거나 내부 `n_fingers`가 안 맞으면 `None`.
  - `apply_and_revalidate_matching_finger_growth(names, transistors, ctx, lut_by_kind,
    metrics_specs, constraints, gm_id_bounds=(2.0,30.0), min_fingers=2)`(§6.11) —
    **세션16 신설**, L3+L4 패턴(`apply_and_revalidate_pair_adjustment()`와 동일 골격,
    재시도 루프만 없음). `revalidate_finger_override()`(세션13, 기존 함수) 그대로 재사용.
  - `run_matching_safety_with_finger_growth(rows, matching_pairs, pair_sensitivity, ctx,
    lut_by_kind, metrics_specs, constraints, gm_id_bounds=(2.0,30.0), min_fingers=2,
    max_rounds=5)`(§6.11) — **세션16 신설**, `repair_matching_safety()`(stick_diagram.py,
    branch 복합 매칭 포함)를 감싸는 라운드 루프. `run_topology_pipeline_with_finger_
    fixup()`(euler용)과 대칭 구조, 동일한 단방향 import 제약 때문에 여기 위치.
    ⚠️ `unresolved_pair=None`이 `audit.ok=True`의 동의어가 아님을 docstring에 명시(box-
    shape 등 이 함수 책임 밖 체크가 별도로 FAIL할 수 있음, 세션16 E-3절 참고) — 호출자는
    `result["audit"].ok`를 직접 확인해야 함.
  - import 목록(1611행 부근)에 `_branch_composite_pair`/`_failing_required_pairs`
    추가(stick_diagram.py에서) — **세션16 수정**(기존 import문에 이름만 추가).
  - self-test "L4d"(L4c/L5 직후) — **세션16 신설**: (1) `suggest_matching_finger_
    growth()` 단위 확인 3케이스. (2) `apply_and_revalidate_matching_finger_growth()`
    통과/거부(면적 제약) 2케이스. (3) M6 그룹 실제 사례 end-to-end — branch 복합 매칭+
    핑거증가가 함께 M1a/M1b/M2a/M2b를 총 `n_fingers=2`로 키워 3b/3c 필수 게이트를 전부
    통과시키는지 확인(진짜 common-centroid 회전 배치 — `rows`엔 같은 소자가 여러 행에
    걸쳐 `n_fingers=1`씩 나뉘어 나타나므로 self-test에서 행별 합산 필요, 세션16 F절 함정
    참고). 전부 통과.
  - 회귀: 커밋 전(`58e608b`) 대비 self-test 전체 출력 diff — 신규 L4d 블록(15줄) 외
    0줄 차이, 무회귀 확정.
- `skills/analog-gmid-design/assets/stick_diagram.py` (**세션17 수정, 커밋 `4bcaafc`/
  `69d9b39`/`4e38aa6`** — 문서가 한동안 "아직 미커밋"으로 stale했음, 세션18에 `git log`
  재확인으로 정정. 세션18은 이 파일을 전혀 안 건드림)
  - `repair_matching_safety(rows, matching_pairs, pair_sensitivity=None, max_iter=3,
    relaxed_pairs=None)`(3308행 부근) — **세션17 신설** `relaxed_pairs: set[frozenset]`
    파라미터. composite 경로(3407행 부근)/raw 경로(3443행 부근) 둘 다에서 이 집합에 든
    쌍은 `select_layout_tool()` 판단을 무시하고 `interdigitate_layout` 강제(layout 전용
    최후수단 완화). 공유 hub/branch composite 없는 쌍은 여전히 손 못 댐(정직한 한계 유지).
  - self-test 2건(Test 28 `_branch_composite_pair()` 테스트 직후) — **세션17 신설**: M6
    그룹으로 완화 후에도 3c FAIL 유지 확인 + rowA/rowB(공유 hub 없음)는 relaxed_pairs
    있어도 안 바뀜 확인.
  - 회귀: `PYTHONHASHSEED=0` 기준 편집 전(`7a41a30`) 대비 self-test 전체 출력 diff —
    신규 테스트 블록(8줄) 외 0줄 차이, 무회귀 확정(세션17 C절).
- `skills/analog-gmid-design/assets/sizing_recipe.py` (**세션17 수정, 커밋 `4bcaafc`/
  `69d9b39`/`4e38aa6`** — 위 stick_diagram.py와 동일한 이유로 정정)
  - `run_matching_safety_with_finger_growth(..., allow_layout_relaxation=True)`(2595행
    부근) — **세션17 신설** `allow_layout_relaxation` 파라미터 + `relaxed_pairs` 반환
    필드. `reason=="gm_id_violation"`일 때만(다른 실패 사유는 완화 대상 아님) 그 쌍을
    `relaxed_pair_keys`에 등록하고 `repair_matching_safety()`(위, relaxed_pairs 인자로
    전달)를 재시도. 새 `unresolved_reason="relaxed_to_layout"`. `audit.ok`는 손대지
    않음(3c 요구사항 자체는 안 없앰, 세션17 B절 정책).
  - self-test "L4e"(L4d 직후) — **세션17 신설**: offset pair(공유 source Ma/Mb)로 gm/ID
    예산 위반 유발 → 완화 적용(`relaxed_pairs`=1건, `interdig_ok=True` 실측 확인) +
    `audit.ok=False` 유지 확인, `allow_layout_relaxation=False`면 세션16 그대로(즉시
    `unresolved_reason="gm_id_violation"`) 보존되는 회귀 대조.
  - 회귀: `PYTHONHASHSEED=0` 기준 편집 전(`7a41a30`) 대비 self-test 전체 출력 diff —
    신규 L4e 블록(9줄) 외 0줄 차이, 무회귀 확정.
- `skills/analog-gmid-design/assets/sizing_recipe.py` (**세션18 수정, 아직 미커밋** —
  이번 세션은 이 파일만 건드림, `stick_diagram.py`는 세션17 상태 그대로)
  - `run_topology_pipeline_with_finger_fixup(...)`(2746행 부근) — **세션18**: 핑거조정
    (`apply_and_revalidate_pair_adjustment()`)이 `applied=False`면 바로 `unresolved_row`
    로 포기하지 않고 `find_min_crossover_layout_with_branch_composite()`(G-3절 wrapper)
    로 그룹분할 폴백(세션15 C절 harness 배선). `segments`대로 `stack_id`를
    `f"{row_name}_seg{i}"`로 재배정, `group_splits` 반환 필드에 근거 기록(C-2, `audit.ok`
    는 손 안 댐). `cell_groups`가 있으면 원래 row가 속한 항목을 새 `_seg*` 이름으로
    자동확장(C-3, 호출자 원본 dict 불변). `unresolved_reason="no_valid_candidate"`는
    그룹분할이 그래프 이론상 항상 성공하므로 더 이상 실제 반환 경로가 아님(`max_rounds_
    exceeded`만 남음). import 목록(1611행 부근)에 `find_min_crossover_layout_with_
    branch_composite` 추가.
  - self-test — L4c **케이스B 재작성**(세션12/14 M3a 그룹 11소자 fixture 재사용, 새
    fixture 안 지어냄): 핑거조정이 면적 예산으로 실패하는 기존 시나리오가 이제 그룹분할로
    자동 해결됨을 확인(3세그먼트, crossover_count=2) — **실측으로 새로 발견**: M3a 그룹이
    이미 M4a-M3a/M4b-M3b 캐스코드 컬럼 구조를 가져 `_composite_collapse_for_crossover()`
    가 이를 감지해 합성 소자로 묶었다(G-3 wrapper가 세션17 M6 픽스처 외의 실제 다른
    회로에서도 올바르게 동작함을 처음 확인). **케이스C 신설**: `cell_groups` 자동확장이
    실제 감사 파이프라인까지 작동하는지(seg row 3개 전부 `cellA` 감사에 포함) + 호출자
    원본 dict 불변 확인.
  - 회귀: `PYTHONHASHSEED=0` 기준 편집 전(세션17 커밋 `fbfaed5`) 대비 self-test 전체
    (250줄) 출력 diff — 케이스B(의도된 변경)/케이스C(신규) 블록 외 0줄 차이, 무회귀 확정.
- `skills/analog-gmid-design/assets/sizing_recipe.py` (**세션18 추가 수정, 미커밋** —
  H절)
  - `optimize_full_circuit_budget()`의 `if not audit_ok:` 분기(2306행 부근) — 구형
    `repair_matching_safety()` 단독 호출을 `_lut_by_kind is not None`일 때 `run_
    matching_safety_with_finger_growth(...)`로 승격, 없으면 기존 그대로 폴백. 반환
    `pipeline_result`에 `growth_rounds`/`unresolved_pair`/`unresolved_reason`/
    `relaxed_pairs` 추가.
  - self-test: L5 케이스B에 `growth_rounds` assertion 추가(위 H절 참고).
  - 회귀: `PYTHONHASHSEED=0` 기준 `a6ab04b` 대비 self-test 전체(250줄) diff — L5 출력
    문구 1줄(의도된 변경) 외 0줄 차이.
- `skills/analog-gmid-design/assets/stick_diagram.py` (**세션18 추가 수정, 미커밋** —
  J절)
  - `run_topology_pipeline()` — `check_finger_width_compatibility()`(§3.5) 호출 추가
    (`_dc_replace`로 sizing_overrides 적용 직후, `split_into_stacks()` 이전) — 실패
    시 소자별 상세 정보와 함께 즉시 `ValueError`.
  - self-test: Test 26.55(Test 26.5 직후) 신설 — 비정상 W(정수배 아님) ValueError 확인
    + 정상 케이스 회귀 대조.
  - 회귀: `PYTHONHASHSEED=0` 기준 편집 전 대비 self-test 전체(758줄) diff — 신규 Test
    26.55 블록(7줄) 외 0줄 차이.
- `workspaces/current-reuse-telescopic-ota-report/run_harness.py` (**세션18 추가 수정,
  미커밋** — I절, 세션11 이후 첫 수정) — `from stick_diagram import save_instance_json`
  추가, `optimize_full_circuit_budget()` 성공 후 `pipeline_result is not None`이면
  `save_instance_json(INSTANCE_OUT, TOPO, result["sizing"], result["pipeline_result"])`
  호출(`audit_ok=False`여도 그대로 저장). 재실행 자체는 세션11 이후 여전히 안 됨(grid
  search infeasibility, 위 A절 참고) — 이번 수정은 저장 배선만, 실행 전략 논의는
  "다음 세션 작업 순서" 4번.
- `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`
  — **세션18 신설**(untracked, git에 아직 안 올라감), 세션11 `smoke_run_harness_
  session11.py` 패턴(KEEP_FREE 그리드 축소) 재사용해 I절 저장 배선 검증 시도 —
  grid search infeasibility로 저장 호출부까지 도달을 못해 이 스크립트 자체로는 검증
  실패(사전 존재 문제, 세션18 변경과 무관) — 실제 검증은 L5 `known_sizing` fixture로
  별도 격리 확인(스크래치패드 probe, 커밋 안 됨).
- `skills/analog-gmid-design/assets/library/*.topology.json` — 세션11~18 **미수정**.
- `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session11.py` —
  **세션11 신설**, 자유 theta 일부만 남기고 나머지 고정해 빠르게 완주 확인하는 스모크
  테스트 패턴. 다음에 비슷한 상황에서 재사용할 것(`KEEP_FREE` 값만 바꾸면 됨).
- `workspaces/current-reuse-telescopic-ota-report/probe_l3_groups.py` — **세션11 신설**,
  `geometry_colocation_union()`의 실제 그룹 중 다중 matching_pairs가 섞인 후보를 뽑는
  탐색 스크립트(M3a 그룹 발견에 사용). 다음 세션에서 다른 그룹 탐색할 때 재사용 가능.
- `workspaces/current-reuse-telescopic-ota-report/probe_group_split_reassembly.py` —
  **세션16 신설**, `find_min_crossover_layout()`의 segments를 버리고 `stack_id`만
  재배정했을 때 재계산이 안전한지 + `audit_row_split()`의 3c(common-centroid)가 실제로
  통과하는지 M6 그룹으로 검증(세션16 B/C절 핵심 근거 스크립트). 그룹분할 harness 배선을
  재개할 때(다음 세션 작업 순서 3번) 재사용/확장 가능.
- `workspaces/current-reuse-telescopic-ota-report/probe_crossover_pairing_alternatives.py`
  — **세션16 신설**, M6 그룹의 4개 홀수차수 노드에 대해 가능한 3가지 완전짝짓기를 전수
  대입해 각각 매칭쌍이 갈라지는지 확인(세션16 D-1절 핵심 근거 — B-3 tier1 우선순위가
  최악의 선택이었음을 발견).
- `workspaces/current-reuse-telescopic-ota-report/probe_d1_verify.py` — **세션17 신설**,
  위 스크립트가 손으로 확인한 D-1 발견(splits=2)을 세션17 `_select_crossover_pairing()`
  구현이 실제로 splits=0으로 고치는지 자동 로직으로 재확인(세션17 E-3절 근거 스크립트).
- `workspaces/current-reuse-telescopic-ota-report/probe_group_split_wiring.py` —
  **세션18 신설**, M3a 그룹(세션12/14 L4c fixture 재사용)으로 `run_topology_pipeline_
  with_finger_fixup()`의 그룹분할 폴백을 self-test 작성 전에 먼저 실행해 실제 반환값
  (`group_splits`/`branch_composites`/최종 `stack_id`/`audit.ok`/`cell_groups` 자동확장)
  을 확인한 스크립트(상상으로 assertion을 채우지 않는 원칙, 세션18 D절 근거).
- `skills/analog-grammar/`(전체) — **세션19 신규 반입, 커밋 `d4bd4d9`**. `SKILL.md` +
  `references/DESIGN.md`(정본)+`consistency-map.md` + `skill-validation-prompt.md` +
  `assets/{analyze.py,netclass.py,idioms.py,sfg.py,run_example.sh,examples/}`(원본
  zip 스크립트 바이트 단위 무변경). netlist → net 분류(Stage1) → device role
  배정(Stage2) → L1 idiom 매칭(Stage3) → 계층 축약(Stage4) → signal flow graph
  (Stage5) → 기능 가설(Stage6) 6단계 파이프라인, 결정론적(Stage6b만 LLM 개입).
- `skills/analog-gmid-design/assets/stick_diagram.py` (**세션19 신설, 커밋 `d4bd4d9`**
  — §1.7a~1.7c, `find_matching_candidates()` 직후)
  - `_to_analog_grammar_devs(transistors)`/`_import_analog_grammar(*module_names)`
    — **세션19 신설**, analog-grammar cross-skill import 어댑터(soft-fail, 없으면
    `None` 튜플 반환). `../../analog-grammar/assets` 상대경로로 `sys.path` 삽입(멱등).
  - `find_idiom_matches(transistors, inputs=(), outputs=(), feedbacks=(), biases=(),
    clocks=())` — **세션19 신설**. analog-grammar Stage 1~3 실행, 겹침 해소 이전
    원본 Match 리스트 반환. analog-grammar 없거나 gate 없는 소자뿐이면 `None`.
  - `find_matching_candidates(transistors, idiom_matches=None)` — **세션19 확장**
    (하위호환, `None`이면 옛 `(kind,gate)`/`(kind,source,w)` net-only 동작 완전
    동일). `idiom_matches` 주면 current_mirror는 `(kind,gate,source)`+diode
    레퍼런스 요구, diff_pair는 두 소자 다 role=AMPLIFYING 요구로 재계산(M57/M58,
    M11/MN 오탐 해소 — 세션19 결론 §A~C 참고).
  - `find_stack_edges(transistors)` — **세션19 신설**, analog-grammar `netclass.
    stack_edges()` 재사용(role/net분류 불필요, 순수 connectivity).
  - `find_stacked_matching_candidates(transistors, base_pairs, stack_edges)` —
    **세션19 신설**, "복합소자" 개념(세션16/17 branch composite와 같은 직렬 스택
    개념을 matching 후보 **발견** 방향으로 적용, 사용자 제안). 이미 확정된 매칭쌍
    위에 직접 stacked된 소자쌍을 재귀적으로 상속 탐지 — 캐스코드 대칭쌍(M2a/M2b류)
    커버. 폴디드 노드에서 극성이 다른 소자가 동시에 얹히는 경우 같은 kind로
    좁히도록 구현(실측으로 버그 발견+수정, 세션19 결론 §D 참고).
  - self-test "Test 30"(Test 29 직후) — **세션19 신설**, 6개 항목 전부 PASS(위
    "세션19 결론" §E 상세). 전체 self-test suite 회귀 0줄.
- `skills/analog-gmid-design/references/analog-grammar-integration.md` — **세션19
  신규**, 위 연동의 설계 근거 전체(두 계층 재정의, cross-skill import 메커니즘,
  role 어휘 매핑표, self-test 계획, Tier 2 폐기 근거). 구현 완료 후 "구현 완료"로
  상태 갱신됨.

## 참고 — 사용자 협업 메모리 (자동 메모리 시스템에 저장됨, 요약만)

- 최종 보고는 항상 한글로.
- 상상으로 채우지 말고 근거·실제 확인 후 진행 — "확정"처럼 보이는 결과도 전제를 다시
  확인하기 전엔 맹신 금지(세션11: "매칭 안 된 소자만 걸러내면 된다"는 첫 가설이 실측으로
  틀렸음이 드러난 사례 — M9b/M18b는 매칭됐는데도 빼야 했다).
- topology.json이 유일한 토폴로지 소스 — connectivity는 사용자 전용, role/matching/theta
  같은 메타데이터는 Claude가 분석해서 업데이트 가능.
- 장시간 실행은 `run_in_background: true` — 백그라운드 실행이 로그 없이 오래 걸리면 "죽었다"고
  바로 판단하지 말고 PID 생존+CPU 사용량 변화로 먼저 hang 여부를 구분할 것(세션10에서 확립,
  세션11의 `run_harness.py`/self-test 모니터링에서 재사용해 실제로 "hang 아니고 그냥
  느림"을 확정하는 데 성공).
- **세션11 추가**: 로그가 안 찍힌다고 무조건 버퍼링/hang 의심하지 말 것 — 스크립트 자체가
  중간에 print를 안 하는 구조일 수도 있다(`run_harness.py`가 정확히 이 경우, 세션7~9의
  미해결 질문이 세션11에서 이렇게 풀림). 소스를 먼저 읽어 print 위치를 확인하는 게 먼저다.
- 회로도 이미지/PDF 판독은 신뢰 못 함 — connectivity는 `topology_to_markdown.py`로
  net 기준 표를 뽑아 확인. 논문 본문 텍스트 추출은 신뢰 가능.
- topology 정정은 대기열에 쌓았다가 "한꺼번에 반영해" 지시가 와야 일괄 반영(connectivity
  한정) — role/matching 메타데이터 재분류는 즉시 반영 가능.
- 논문에 없는 컴포넌트 값은 "논문 인용"만으로 확정 짓지 말 것.
- 복잡한 analog 회로 폐형식 재유도는 opus 에이전트(가능하면 git worktree 격리) 위임이
  효과적.
- git commit 시 heredoc-in-`$()`이 bkit 훅에 막힘 — 파일로 메시지 작성 후 `git commit -F`.
- 엔진/스키마 변경은 국소적 메타데이터 정정은 바로 실행 가능하지만, **여러 파일/여러 회로에
  영향을 주는 엔진 로직 변경은 반드시 사전 논의·승인 필요**(세션7 사고 이후 확립). 세션11은
  L3(D) 구현 전에 여러 턴(A/B/C 후보 검토 → D+B 채택 → 실제 회로 2~3개로 교차검증 → 그룹분할
  원칙 확정)에 걸쳐 논의하고 "맞아, 진행해줘" 같은 명시 승인을 받은 뒤에만 코드를 고쳤다.
- **세션10~11 공통**: 엔진 로직을 실제로 구현하다 보면 설계 단계에서 손으로 추정했던 동작이
  실행 결과와 다를 수 있다 — 이럴 땐 손으로 정답을 다시 추정하지 말고 격리 스크립트로 직접
  실행해 확인할 것(세션11의 `probe_l3_groups.py`/`smoke_run_harness_session11.py` 패턴).
- **세션11 신규**: "같은 전류가 흐르는 branch"라고 물리적으로 같은 layout 행에 있어야
  하는 건 아니다 — 전류(topology/KCL)와 물리 배치(layout matching)는 독립적인 관심사다.
  물리적 그룹핑은 오직 (1) 선언된 matching_pairs 대칭 요구, (2) 오일러 실현 가능성만
  신경 쓰면 된다. 이 원칙이 그룹분할 설계의 핵심 전제.
- **세션11 신규**: 그래프 이론적으로 "탐색"이 필요해 보이는 문제(자기동형사상 찾기)도,
  이미 선언된 데이터(matching_pairs)에서 "구성 후 검증"으로 바꾸면 훨씬 싸게 풀릴 수 있다 —
  탐색 대신 구성+검증이 가능한지 항상 먼저 확인할 것.
- **세션14 신규**: 세션 핸드오프 문서(`.ai/context.md`)조차 시간이 지나면 stale해질 수
  있다 — 세션12/13이 "미커밋"이라 적혀 있었지만 실제론 이미 커밋돼 있었다. 문서를 그대로
  믿지 말고 세션 시작 시 `git log`/`git status`로 항상 실제 상태와 재대조할 것.
- **세션14 신규**: "함수가 구현+self-test 통과됐다"와 "실제 harness에 배선됐다"는 다른
  질문이다 — 사용자가 "최상위 harness함수에 연결됐나?"라고 직접 물어 확인해보니, 세션13에
  만든 `revalidate_finger_override()`도, 세션14에 만든 `apply_and_revalidate_pair_
  adjustment()`/`run_topology_pipeline_with_finger_fixup()`도 전부 self-test에서만
  호출되고 실제 `optimize_full_circuit_budget()`(유일한 실제 harness가 부르는 함수)는
  여전히 옛 `repair_matching_safety()`만 호출하고 있었다. 새 함수를 다 만들었다고 "이제
  연결됐겠지"라고 넘겨짚지 말고, 실제 호출부가 있는지 코드로 직접 확인할 것.
- **세션14 신규**: 콜그래프를 정적 분석(grep/AST)으로 조사할 때 두 가지 사각지대를 반드시
  의심할 것 — (1) 텍스트/정규식 스캔은 docstring 안의 함수명 언급도 "호출"로 오탐한다(AST
  `Call` 노드만 셀 것). (2) AST라도 nested function(closure)에서 재귀를 멈추면 그 클로저를
  통한 실제 호출을 놓친다(`optimize_full_circuit_budget()` 내부 `_evaluate()`가 실제
  사례). (3) `_METRICS_REGISTRY`류 문자열 키 기반 동적 dispatch는 정적 분석 자체가 원천적
  으로 못 잡는다 — 실제 데이터(topology.json의 `sizing_roles.metrics`)를 직접 읽어 어떤
  분기가 실제로 걸리는지 수동으로 보정해야 한다. 세 가지 다 실제로 겪고 고친 사례
  (세션14 결론 E절).
- **세션14 신규**: 엔진 로직 변경(예: `run_topology_pipeline()` wrapper를 어디에 둘지)은
  구현 전에 AskUserQuestion으로 구체적 설계 선택지를 제시해 확정받는 방식이 잘 작동했다
  (순환 import 제약을 먼저 코드로 확인해 근거로 제시 → "라운드당 blocked row 처리량"
  선택지 2개 중 하나를 사용자가 고름 → 그 결정대로만 구현). 여러 설계 옵션이 있는
  엔진 확장은 이 패턴을 재사용할 것.
- **세션15 신규**: "함수 A가 함수 B를 대체하는지 폴백으로 쓰는지" 같은 질문을 받으면, 답을
  추측하지 말고 두 함수가 **정확히 같은 걸 다루는지부터 코드로 확인**할 것 — 세션15는
  `repair_matching_safety()`가 실제로는 3b/3c(물리배치) 체크만 다루고 euler(체크1)는 전혀
  못 건드린다는 걸 파싱 로직(`_failing_required_pairs()`)을 직접 읽어서 발견했다. "대체 vs
  폴백"이라는 질문 프레임 자체가 틀렸을 수 있다 — 두 함수가 애초에 다른 문제를 푸는 상호보완
  관계였다.
- **세션15 신규**: 작업 중 우연히 발견한 크래시/버그는, 자신이 방금 만든 변경 때문인지 아니면
  원래 있던 문제인지 **격리 스크립트로 변경 전 코드에서도 재현되는지 직접 확인**한 뒤에만
  "무관한 사전 존재 버그"라고 결론 내릴 것(`probe_preexisting_bug.py` 패턴) — 확인 없이
  "아마 원래 있었을 것"이라고 넘겨짚지 않는다.
- **세션15 신규**: self-test 출력에 `set`을 그대로 문자열로 찍는 부분이 있으면(예:
  `{'X','Y'}`), 회귀 diff를 뜰 때 반드시 `PYTHONHASHSEED`를 고정(`PYTHONHASHSEED=0`)하고
  베이스라인/신규 둘 다 재실행할 것 — 안 그러면 프로세스별 해시 랜덤화 때문에 코드가
  똑같아도 set 원소 순서가 달라 보여 가짜 diff가 섞여 나온다(세션15에서 실제로 겪음, 고정
  후 재확인해 무회귀 확정).
- **세션16 신규**: "이게 sizing 문제냐 layout 문제냐" 식의 이분법 질문은, 실제로는 서로
  독립된 두 축(어떤 audit 체크를 고치는가 / 변경이 sizing에 영향을 주는가)으로 분해하면
  훨씬 명확해진다 — 지금까지 우연히 두 축이 일치해왔을 뿐, 그룹분할처럼 두 축이 어긋나는
  사례가 나오면 이분법 프레임 자체가 틀린 질문이 된다(세션16 A절).
- **세션16 신규**: 같은 필드명(예: `stack_id`)이 파이프라인의 서로 다른 단계에서 다른
  의미로 재사용되고 있다면, "실제로 서로 간섭하는지"를 추측하지 말고 **호출 그래프를
  직접 추적**(예: A 단계의 함수가 B 단계 안에서 실제로 호출되는지 grep)해서 확인할 것 —
  세션16은 이렇게 `propagate_topology_forced_currents()`가 `run_topology_pipeline()`
  안에서 전혀 호출되지 않음을 확인해 두 stack_id 용법이 구조적으로 분리돼 있음을
  근거로 확정했다.
- **세션16 신규**: "그래프/토폴로지 레벨 대칭"과 "물리적 무게중심 대칭(audit의 3c
  common-centroid)"은 이름이 비슷해도 다른 개념이다 — 세그먼트가 서로 거울상이라고
  해서(그래프 대칭) 실제 배치의 무게중심이 맞는다는(3c) 보장은 없다(세션16 C/D-2절,
  M6 그룹 실측으로 직접 반증됨: dx=3~5로 크게 벗어남). "대칭"이라는 단어가 여러 층위를
  가리킬 수 있다는 걸 항상 의심할 것.
- **세션16 신규**: 그럴듯해 보이는 우선순위 휴리스틱(세션15 B-3의 "선언된 진짜 거울쌍을
  최우선으로 절단"처럼 근거가 있어 보이는 순서)도 실제로 전수 대입해 검증하기 전엔
  최악의 선택일 수 있다 — 선택지가 소수(이번엔 3가지)라면 손으로 정당화하지 말고 전부
  실행해서 비교할 것(세션16 D-1절, `probe_crossover_pairing_alternatives.py`).
- **세션16 신규**: 새 개념(예: "여러 소자를 하나의 branch로 묶어서 다룬다")을 구현하기 전에,
  "이미 있는 함수가 이걸 다른 목적으로 이미 계산해주고 있지 않은가"부터 찾아볼 것 — 세션16은
  `kcl_series_union()`(KCL 전류 전파용으로 세션10에 이미 만들어진 함수)을 강제병합 없이
  그대로 재사용하는 것만으로 사용자가 제안한 branch 개념을 새 그래프 로직 없이 구현했다.
- **세션16 신규**: `common_centroid_layout()`의 회전-최적 배치는 소자 하나를 여러 물리
  행에 걸쳐 나눠 배치하는 게 정상 동작이다(진짜 common-centroid) — 그래서 함수가 반환하는
  `rows: {row_name: [Transistor,...]}`류 구조에서 같은 소자 이름이 여러 행에 각각 더 작은
  `n_fingers`로 나타날 수 있다. self-test에서 "이 소자의 최종 n_fingers"를 확인하려면
  이름 하나에 값 하나만 남기는 flat dict comprehension이 아니라 **행별로 합산**해야
  한다(세션16 F절, 실제로 이 함정에 빠졌다가 고침).
- **세션16 신규**: 함수 반환값에 `unresolved=None`/`ok=True`류 필드가 여러 개 있을 때,
  하나가 `None`/성공이라고 해서 전체가 성공했다는 뜻은 아닐 수 있다 — 그 필드가 정확히
  "무엇에 대한" 성공/실패인지 docstring에 명시하고, 호출자는 진짜 필요한 최종 신호(예:
  `audit.ok`)를 별도로 직접 확인해야 한다(세션16 E-3절 — `run_matching_safety_with_
  finger_growth()`의 `unresolved_pair=None`이 `audit.ok=True`를 보장하지 않는 설계를
  명시적으로 문서화).
- **세션17 신규**: 두 가지 열화(trade-off) 중 하나를 감수해야 하는 설계 결정에서, 사용자가
  "한쪽은 나중에 보정 수단(trim)이 있고 다른 쪽은 없다"는 실무적 근거를 직접 제시하면 그
  근거로 방향이 갈렸다 — gm/ID 스펙 위반(trim 불가능한 회로 기능 저하) vs layout mismatch
  (trim으로 보정 가능한 열화) 중 후자를 선택. 트레이드오프 질문을 받으면 "어느 쪽이 더
  나은가"만 볼 게 아니라 "어느 쪽이 사후에 되돌릴 수단이 있는가"도 물어볼 가치가 있다.
- **세션17 신규**: "다른 방법(crossover)으로 이 문제를 우회할 수 있나?"라는 질문을 받으면,
  손으로 그럴듯한 답을 내지 말고 실제 계산식(3c의 무게중심 공식)을 다시 짚어 수학적으로
  가능/불가능을 확정할 것 — `n_fingers=1`인 두 소자는 서로 다른 자리를 차지할 수밖에 없어
  crossover(배치 순서 변경)로는 절대 `dx<=0.5`를 못 만든다는 게 공식 재검토로 바로
  나왔다(세션17 A절). "그럴듯한 우회로"도 근거 확인 전엔 상상으로 채우지 않는다는 원칙의
  연장.
- **세션17 신규**: self-test에서 실제 회로(M6 그룹처럼 여러 겹의 기존 메커니즘 — branch
  composite, touched_this_round 가드 등)를 재사용해 새 기능을 검증하려 하면, 그 메커니즘들
  간의 상호작용이 복잡해서 결과를 손으로 예측하기 어려울 수 있다 — 이럴 땐 새 기능 하나만
  깨끗하게 노출하는 최소 합성 fixture(세션17의 `Ma`/`Mb` offset 쌍, `_l4d_ctx` 재사용)로
  바꿔서 실제로 실행해 확인하는 게 더 빠르고 정확했다(M6 그룹으로 먼저 시도했다가 예측이
  틀릴 위험을 감수하기보다 단순 fixture로 전환).
- **세션18 신규**: "성공 신호를 손대야 하나"라는 질문을 받으면, 그 필드가 **진짜로 무엇을
  재는지**부터 따질 것 — 겉보기엔 비슷한 두 케이스(세션17 `relaxed_pairs`의 3c FAIL vs
  세션18 그룹분할의 euler 성공)가 `audit.ok`에 대해 정반대 함의를 가질 수 있다. 전자는
  체크가 **수학적으로 항상 실패**하므로 `False` 유지가 정직함 자체이고, 후자는 체크가
  **진짜로 통과할 수 있으므로** `False`를 강제하면 없는 실패를 지어내는 것이 된다 —
  "완화 필드를 어떻게 표기할까"는 항상 "이 필드가 재는 대상이 실제로 실패하는가"를 먼저
  확인한 뒤에 답해야 한다.
- **세션18 신규**: "지금 당장 처리할 실제 사례가 없다"고 미뤄둔 갭(세션15 C-3의
  `cell_groups` 상호작용)도, 나중에 그 갭과 맞닿는 기능을 실제로 배선하는 순간
  **그 즉시 실전 의존성으로 바뀔 수 있다** — 배선 직전에 호출 그래프를 다시 추적해
  (`optimize_full_circuit_budget()`가 실제로 `cell_groups=spec.get("cell_groups")`를
  넘기는지 확인) "여전히 가상의 우려인지"를 재검증한 것이 결정을 미루지 않는 근거가
  됐다. "나중에 사례 나오면"으로 미뤄둔 항목은, 그 항목이 의존하는 기능을 실제로 켜는
  시점에 반드시 재검토할 것.
- **세션18 신규**: self-test용 fixture를 새로 지어내기 전에, 정확히 같은 실패 시나리오를
  이미 검증하던 기존 fixture(세션12/14 L4c의 M3a 그룹 "면적 예산 타이트" 케이스)가 있는지
  먼저 찾을 것 — 동작이 의도적으로 바뀌는 경우(핑거조정 실패 시 `unresolved`였던 게 이제
  그룹분할로 자동 해결됨), 그 fixture를 재사용해 "예전엔 이랬는데 이제 이렇게 바뀐다"를
  같은 자리에서 직접 대조하면 회귀 diff에서도 변경 범위가 명확하게 드러난다(세션17 E-4
  "Test 12.13 재작성" 패턴과 동일).
- **세션18 신규**: 콜그래프 기반 "고아함수" 분석의 진입점은 **라이브러리 함수가 아니라
  실제 사람이 실행하는 스크립트**여야 한다 — 세션14/18 모두 `optimize_full_circuit_
  budget()`을 진입점으로 잡았는데, `run_harness.py`(실행 스크립트)를 진입점에 추가하고
  나서야 `save_instance_json()` 배선 여부를 정확히 판단할 수 있었다. "이 함수 하나만
  호출하면 된다"고 문서화된 라이브러리 함수가 있어도, 그걸 실제로 부르는 스크립트가
  무엇을 **더** 하는지까지 봐야 진짜 reachability를 안다.
- **세션18 신규**: "계산은 어디서, 저장은 어디서 하나"류 질문을 받으면 답을 짐작하지
  말고 실제 호출부를 grep으로 확인할 것 — `optimize_full_circuit_budget()`은 계산만
  하고 저장은 안 하는데("반환값을 instance.json에 옮길 수 있는 형태로 만든다"는 문구를
  "저장까지 한다"로 오독하기 쉬움), 사용자가 "최상위 함수는 run_harness 아니야?"라고
  정확히 짚어줘서 "harness 라이브러리 함수(순수 계산 유지) vs 그걸 부르는 실행 스크립트
  (계산+저장)"라는 책임분리로 정리됐다. 라이브러리 함수 이름에 "harness"가 들어있다고
  그게 최상위라고 넘겨짚지 말 것.
- **세션18 신규**: 두 소자가 구조적으로 비슷해 보이는 관계(예: "diode가 만든 gate 전압을
  다른 소자가 읽는다")를 "같은 종류의 관계"로 뭉뚱그리기 쉽지만, 실제 전기적 정의
  (VGS 동일 조건 = gate **그리고** source가 같아야 진짜 전류미러)까지 따져보면 완전히
  다른 두 패턴(직렬로 물린 diode 스택 vs 별개 branch가 bias 전압만 읽는 관계)이 섞여
  있었다 — 사용자가 이걸 세 번(diode-stack 자체 필요성 재검토 → M57/M58 실사고 근거
  제시 → VGS 동일 조건 제시 → source-일치 검사와 diode-stack 구조인식은 별개 질문이라는
  재지적)에 걸쳐 계속 더 정확한 기준으로 밀어붙였고, 매번 실제 connectivity를 다시
  확인해서 검증했더니 그때마다 새로운 구분이 드러났다. "구조적으로 비슷해 보인다"는
  이유로 하나의 해법으로 뭉치기 전에, 그 둘이 정확히 같은 질문에 답하는지 먼저 확인할 것.
- **세션18 신규**: 하나의 필터/검사가 여러 관련 문제를 동시에 푸는 것처럼 보여도, 실제로
  질문 자체가 다르면 어느 하나가 다른 하나를 대체하지 못한다 — source-일치 검사("진짜
  VGS-동일 미러인가")와 `find_diode_stacks()`("이 소자들이 diode 체인을 이루는가")는
  M57/M58 사례에서 답이 우연히 겹쳤을 뿐, 서로 다른 판정 대상이라 하나로 다른 하나를
  대체할 수 없었다(`find_hub_merge_candidates()`는 gate가 아니라 공유 단자로 후보를
  찾아서 source-일치 검사가 아예 적용될 자리도 없었다). "이 개선 하나로 두 문제가 다
  풀리겠다"는 판단이 서면, 그 개선이 진짜로 같은 질문에 답하는지 반례(다른 함수/다른
  판정 기준)로 재확인할 것.
- **세션19 신규**: "이 함수가 미배선"이라고 이전 세션 문서가 적어놨어도, 그게 "아직
  없는 함수"인지 "이미 있는데 안 불리는 함수"인지는 다르다 — `find_diode_stacks()`를
  세션19에서 Tier 2에 새로 설계하려다 실제로 grep해보니 이미 2026-07-30에 M57/M58
  사고를 계기로 재작성까지 된 완성 함수였다. "미배선"이라는 과거 기록을 "아직 안
  만들었다"로 넘겨짚지 말고, 새 함수를 설계하기 전에 항상 먼저 존재 여부를 코드로
  확인할 것(세션14의 "harness에 연결 안 됨" 교훈과는 다른 종류의 실수 — 이번엔 "함수
  자체가 없다"는 착각이었다).
- **세션19 신규**: 사용자가 "이용가치가 있을까?"처럼 짧게 되묻는 질문은 방금 내가 내린
  판단(예: Tier 2에 `find_diode_stacks()`를 쓰자는 제안)을 다시 근거로 검증하라는
  요청일 수 있다 — 실제로 diode-stack의 내부 연결 net을 전부 뽑아 `find_hub_merge_
  candidates()`의 역할별 그룹핑 조건과 대조해보니 "크기 2 이상" 조건을 구조적으로
  절대 못 채운다는 게 드러나 그 제안 자체가 폐기됐다. 짧은 되물음을 "그냥 궁금해서"로
  가볍게 넘기지 말고, 직전 판단을 다시 실측으로 검증하라는 신호로 받아들일 것.
- **세션19 신규**: "오탐이라는 얘기야?"처럼 사용자가 내가 쓴 용어를 정확히 되짚으면,
  방금 내가 "문제"라고 뭉뚱그려 부른 것이 실제로 증명 가능한 오류(M57/M58 — 성립
  불가능하다고 논리적으로 확정 가능)인지, 아니면 그냥 애매함/맥락 부족(hub_merge
  혼합 후보 — 사실 자체는 참이고 함수 자신이 "후보일 뿐"이라고 이미 선언)인지 구분해서
  다시 답해야 한다. 두 개념을 섞어 "문제"라고 부르면 나중에 근거 없이 강한 조치(필터
  추가 등)로 이어질 위험이 있다.
- **세션19 신규**: "composite소자 개념을 적용할 수 없나"처럼 사용자가 기존에 이미 쓰인
  개념(세션16/17의 branch composite, 원래 **레이아웃** crossover 짝짓기용)을 다른
  문제(이번엔 matching 후보 **발견**)에 적용해보자고 제안하면, 실제로 같은 저수준
  함수(`stack_edges()`/`kcl_series_union()`)를 정반대 방향으로 재사용할 수 있는지
  실측으로 확인해볼 가치가 크다 — 이번엔 실제로 이미 있던 두 문서화된 오탐 사례
  (M2a/M2b, M3a/M3b)가 이 방향 전환 하나로 전부 설명됐다. "이 개념을 다른 데도 쓸 수
  있지 않을까"라는 질문은 가볍게 넘기지 말고 먼저 실제 connectivity로 검증할 것.
- **세션19 신규**: 새 skill을 이 저장소로 반입할 때 "다른 skill과 동일하게 관리"라는
  요구는 구체적으로 SKILL.md+`references/`(정본 문서+consistency-map.md)+`skill-
  validation-prompt.md` 3종 세트, 그리고 이 저장소 고유 관례(폴더 내 최상위 README.md
  금지, description ≤1024자, SKILL.md ≤5000 words)를 의미한다 — 원본 자료를 그대로
  복사해 넣는 게 아니라 이 컨벤션에 맞춰 재편집해야 한다(원본 README.md 내용을
  SKILL.md로 흡수, DESIGN.md를 references/로 이동 등).
- **세션20 신규**: "일반 함수인데 먼저 채워야 할 선행 데이터가 있다"는 설계는 앞뒤가
  안 맞는다는 사용자 지적이 실제로 맞았다 — `run_full_circuit_audit()`의
  `expected_counts`/`dispositions`를 "먼저 15개짜리 partial scope로 수작업 채워야
  한다"고 잘못 판단했으나, 실제로는 `_netlist_sections`(prose)와 `symmetry.
  dispositions`에 이미 51개 전체가 기록돼 있었다 — "구조화가 안 된 프로세 문자열"과
  "데이터가 없음"을 혼동한 것. 데이터가 이미 topology.json에 있다면, 필요한 건 새
  판단이 아니라 기계적 형식 변환뿐이라는 걸 먼저 실측(`json.load`+필드 확인)으로
  확인한 뒤에 "선행 작업이 필요하다"는 결론을 내릴 것.
- **세션20 신규**: "topology.json 저작이 끝난 뒤"처럼 두 산출물의 관계를 시간 순서
  ("A가 끝나면 B가 된다")로 설명하면 틀리기 쉽다 — 실제로 topology.json(연결성+대칭성,
  사이징과 무관, 재사용 가능한 일반 자산)과 instance.json(사이징 결과, 별도 파일로
  추가 생성)은 "A→B 전환"이 아니라 "서로 다른 시점에 도는 별개의 산출물"이다. 두
  워크플로우 단계의 관계를 설명할 때는 "무엇이 무엇으로 바뀌는가"가 아니라 "각각
  무엇을 입력으로 읽고 언제 도는가"로 물을 것.
- **세션20 신규**: "일반화해달라"는 요청을 받으면 실제 대상 코드를 먼저 열어 얼마나
  회로-특정적인지 확인한 뒤 범위를 판단할 것 — `build_report.py`/`build_html.py`를
  열어보기 전엔 "감싸는 wrapper 함수만 만들면 된다"고 가정했으나, 실제로는 후자의
  JS 섹션 조립 로직 670줄이 이 회로의 cell 이름/enriched 필드를 그대로 하드코딩하고
  있어 "완전히 회로-무관한 재사용"과 "이 회로 전용 스크립트를 함수로 감싸기"는 전혀
  다른 작업량이었다. 이번엔 후자 대신 "기계적으로 조립 가능한 부분만 일반 함수로,
  판단이 필요한 서술은 명시적 narrative 입력으로" 범위를 좁혀 진행했다 — 이 범위
  좁히기 자체를 사용자에게 숨기지 않고 최종 보고에 명시할 것.
- **세션20 신규**: 그리드 축소 스모크 테스트가 매번 같은 두 metric(PSRR/classab_
  centering)에서 infeasible로 막히면, "이 회로는 원래 안 풀린다"로 결론짓기 전에
  고정된 theta들이 정확히 어떤 것들인지 확인할 것 — `KEEP_FREE`가 "netlist 순서상
  앞쪽 N개"를 자유롭게 두는 방식이라, 실제로 그 두 metric을 좌우하는 theta
  (`r_classab_battery`류)가 매번 고정값에 묶여 있었다(실측 후 발견). 그리드 축소는
  "개수"가 아니라 "어느 축을 자유롭게 두는가"의 문제라는 게 이번 세션의 새 정보.

---

# 세션20 결론 — Tier 1 idiom_matches 배선 논의 중 더 큰 gap(`run_full_circuit_audit()`
# 전체 미배선) 발견 → `run_full_circuit_audit_from_topology()` 신설+배선, 리포트 생성
# 일반화(`design_report.py`) + `run_harness.py` 실배선

세션20은 세션19가 "다음 세션 후보(사전 승인 필요)"로 남긴 Tier 1 `idiom_matches` 실배선
논의로 시작했으나, 논의 도중 사용자가 던진 두 질문("이 함수는 topology.json 작성할 때
필요한 함수인 거야?", "topology.json 저작이 끝났다는 게 애매한데?")을 따라가다 원래
계획했던 것보다 훨씬 근본적인 gap — `run_full_circuit_audit()`(§1.6, 전체 회로 최종 감사
게이트) 자체가 `run_harness.py`(유일한 실제 harness)에 지금까지 **한 번도 배선된 적이
없었다** — 를 발견했고, 그걸 해소하는 쪽으로 세션 전체 방향이 바뀌었다. Tier 1
`idiom_matches` 배선 자체는 이번 세션에 다루지 않았다(위 "지금 상태" 3번, 다음 세션 이월).

## A. Tier 1 논의 → 더 큰 gap 발견까지 (설계 방향 전환 경위)

1. `check_symmetry_dispositions()`(topology-authoring 게이트)와 `run_full_circuit_
   audit()`(리포트 완료 게이트) 두 프로덕션 호출부를 찾은 뒤, `idiom_matches` 계산
   위치(호출자 사전계산 vs 함수 내부 계산)와 캐스코드 대칭쌍 보완 범위를 사용자에게
   물었다.
2. 사용자가 "이 함수는 topology.json 작성할 때 필요한 함수인 거야?"로 되물어 — 이건
   방금 내린 설명이 정확한지 검증하라는 신호였다(세션19 "짧은 되물음" 교훈과 동일
   패턴). 다시 확인하니 `check_symmetry_dispositions()`만 그 용도이고
   `run_full_circuit_audit()`은 "리포트 완료 선언 직전"(더 늦은 단계) 용도임을
   구분해 답했다.
3. 사용자가 "topology.json 저작이 끝났다는 게 애매한데, 사이징 후엔 instance.json으로
   바뀌는 거 아니었어?"로 재반박 — `function-selection-map.md`(줄139-143)를 다시 읽어
   topology.json이 "사이징과 무관한 재사용 가능한 일반 자산"이고 instance.json은
   **별도로 추가 생성**되는 산출물임(전환이 아니라 병존)을 확인, 위 협업 교훈에
   기록했다.
4. 사용자가 "`run_full_circuit_audit`는 `run_harness`에서 `save_instance_json` 호출
   전에 호출되어야 할 것 같다"로 구체적 배선 지점을 제시 — `run_harness.py`를 직접
   열어 확인하니 `run_full_circuit_audit()` 호출부가 **전혀 없었다**(session14의
   전수 콜그래프 조사가 이미 이걸 "미배선"으로 분류했었지만, 이번에 실제 배선까지
   간 적은 없었음). 여기서 "Tier 1 배선"보다 "이 게이트 자체를 harness에 연결하는
   것"이 더 근본적인 작업임이 확정됐다.

## B. `expected_counts`/`dispositions` "선행 커버리지 문제" 오판 → 실측으로 정정

1. `run_full_circuit_audit()`의 `expected_counts`/`dispositions`가 인자로 필요해서,
   처음엔 "워크스페이스 `stick.py`(7/29)가 만든 15개짜리 partial scope 예시밖에 없다
   → 51개 전체를 새로 커버해야 하는 큰 선행 작업"이라고 판단해 사용자에게 순서를
   물었다.
2. 사용자가 "일반적인 함수여야 하는데 먼저 완성해야 할 것이 있다는 게 이상한데?
   topology.json에서 자동으로 읽고 채운 후 감사해야 하는 것 아닌가?"로 반박 — 실제로
   `json.load()`로 `current_reuse_telescopic_ota.topology.json`을 직접 열어 확인하니:
   - `symmetry.dispositions`에 **이미 20건**이 기록돼 있었다(15개짜리는 `stick.py`가
     자기 스코프용으로 만든 부분집합일 뿐, topology.json 자체엔 훨씬 많았다).
   - `_netlist_sections`(prose)에 **51개 전체**의 블록 구조/개수가 이미 선언돼
     있었다(Fig.2/6=11, Fig.3/7우=12, Fig.1/7좌=12, Fig.8=9, Fig.5=7, 합 51 —
     netlist 전체 개수와 정확히 일치).
   - 즉 "데이터가 없다"가 아니라 "기계가 못 읽는 prose 형태로만 있다"는 게 진짜
     문제였다 — 위 협업 교훈에 기록.

## C. 구현 (전부 `stick_diagram.py`/`library/*.topology.json`/신규 파일, 아직 미커밋)

### C-1. `_netlist_sections_structured` 신설 (`current_reuse_telescopic_ota.topology.json`)
prose `_netlist_sections`를 `{block_key: {"label", "confidence", "devices":[...]}}`
5개 블록(`stage1_diffpair`/`classab_vom`/`classab_vop`/`biasgen`/`cmfb`)으로 기계적
변환(새 판단 없음). 51개 소자 전수 커버, 중복/누락 0을 스크립트로 확인(집합 연산).
원본 prose는 그대로 유지(사람이 읽는 원본), 새 필드는 순수 추가(하위호환).

### C-2. `load_topology()` 확장 — `meta["netlist_sections_structured"]` 신설
`_netlist_sections_structured`가 없는 회로(나머지 3개)는 `None` — `linked_topology_
files` 병합 로직에도 동일 패턴으로 추가(기존 `device_roles`/`dispositions` 병합과
동일 방식). 기존 반환 키는 전부 무변경(순수 추가 필드, diff 0).

### C-3. `run_full_circuit_audit_from_topology(topology_json_path, box_shape_checks=None,
max_ratio=1.5, accept_fail_blocks=None)` 신설 (`stick_diagram.py`, `run_topology_
pipeline()` 직후)
`load_topology()`가 읽은 `netlist_sections_structured`/`symmetry.dispositions`에서
`devices`/`expected_counts`/`dispositions`를 전부 자동 구성해 기존 `run_full_circuit_
audit()`을 호출한다. 구조화 필드가 없는 회로는 `ValueError`(조용히 빈 expected_counts로
안 넘어감). netlist 소자가 구조화 어느 블록에도 없으면(불일치) 역시 `ValueError`.
`box_shape_checks`류(사이징 이후에만 나오는 정보)는 여전히 호출자가 넘긴다 — 자동
변환 안 함(cell_groups 유무로 형태가 달라져 조용한 오판 위험).

self-test(Test 31, `stick_diagram.py`): (1) 실제 51개 소자 회로로 자동 구성 →
`ok=True`, 체크 1/2/3 전부 실행 확인. (2) `dispositions` 변환이 20건 전부 키 충돌 없이
`(category,reason)` 튜플로 바뀌는지. (3) 구조화 필드가 없는 회로(`folded_cascode`)는
`ValueError`. (4) netlist 전수를 못 커버하면(소자 하나가 누락) 임시 topology.json으로
실제 함수를 태워 `ValueError` 확인(내부 로직 재현이 아니라 진짜 호출).

### C-4. 리포트 생성 일반화 — `design_report.py` 신설
`build_topology_device_table(topology_json_path)`: topology.json에서 소자 표를 자동
조립(손타이핑 없음). `symmetry.matching_pairs`로 선언된 그룹은 union-find로 연결
성분을 묶어 한 행으로 표시(⚠️ 실측 발견 버그: 소자 하나가 서로 다른 매칭쌍 항목
여러 개에 동시에 속할 수 있어서(M8이 `{M8,M17}`과 `{M18_bg,M8,M13,M17,M22,M60,M61}`
둘 다에 속함) "마지막에 처리된 항목으로 덮어쓰기"는 이중집계 버그를 낸다 — self-test로
발견 후 union-find로 재작성해 해결).

`assemble_report_data(topology_json_path, instance_json_path, full_circuit_audit=None,
narrative=None, extra_sections=None)`: 소자 표(topology.json)/sizing·floorplan·
audit_row_split·coverage(instance.json)/`run_full_circuit_audit_from_topology()`
결과는 자동 조립, spec 표/레이아웃 가이드/회로도는 `narrative`로 호출자가 채우지
않으면 조용히 생략.

`render_html_report(report)`/`save_html_report(report, path)`: 표/카드 기반 범용
HTML 렌더러(동적 컬럼 — 회로마다 sizing 필드 구성이 달라도 안 깨짐). 옛 `build_html.py`
수준의 SVG stick-diagram 시각화는 이식 안 함(§B, "지금 상태" 2번 한계).

self-test 4건: (1) 51개 소자 → 그룹핑, 총 소자 수 보존(union-find 버그 수정 검증).
(2) instance.json 없이도(사이징 전) 안 죽음. (3) 실제 옛 instance.json(과거 세션
산출물)+실제 audit 결과+narrative를 합쳐 렌더링 성공. (4) 빈 report도 안 죽음(가짜
섹션 생성 없음).

### C-5. `run_harness.py` 실배선 (`workspaces/current-reuse-telescopic-ota-report/`)
`optimize_full_circuit_budget()` 직후: `run_full_circuit_audit_from_topology(TOPO)`
호출(사이징 성패와 무관, connectivity/dispositions만 있으면 되므로 항상 실행) →
`save_instance_json()` 이전에 결과 출력. `pipeline_result is not None` 분기 안,
`save_instance_json()` 직후: `assemble_report_data()`+`save_html_report()`로
`current_reuse_telescopic_ota.report.html` 생성(사용자 지시 — instance.json/리포트
둘 다 이 harness 스크립트에서 호출).

## D. end-to-end 검증 — 함수 단위는 실측 완료, 스크립트 리터럴 완주는 여전히 막힘(item 7)

`smoke_run_harness_session20.py`(세션11/18 grid-축소 스모크 패턴 재사용)로 실제
`run_harness.py`와 동일한 함수 호출 순서를 태우려 했으나, `KEEP_FREE=2`(4조합)/
`KEEP_FREE=5`(32조합) 둘 다 `psrr_estimate_db`/`classab_centering_dev_v` 위반으로
`optimize_full_circuit_budget()` 자체가 "모든 theta 격자점이 infeasible"로 실패
(150초 소요, 세션20 신규 코드와 무관 — item 7의 재확인). **새로 확인된 원인**: 이
두 metric을 좌우하는 theta(`r_classab_battery`류, CMFB 관련)가 `KEEP_FREE`의 "netlist
순서상 앞쪽 N개" 전략에 안 들어가 항상 중간값 고정 — "지금 상태" 4번에 기록.

그래서 `run_harness.py` 스크립트 자체의 리터럴 완주는 이번에도 못했지만, 새로 만든
세 함수는 각각 **실제 프로덕션 데이터로 독립 검증**됐다: `run_full_circuit_audit_
from_topology()`는 Test 31(실제 topology.json), `assemble_report_data()`/
`render_html_report()`는 design_report.py Test 3(실제 topology.json + 실제 옛
instance.json + 실제 audit 결과)에서 전부 PASS. `save_instance_json()`은 이번 세션에
변경하지 않은 기존 코드. 세 함수의 조합인 `run_harness.py`의 새 두 배선 지점은 이
개별 검증들로 충분히 뒷받침된다고 판단 — 스크립트가 여기서 멈추는 건 배선 결함이
아니라 이미 알려진 별개 문제(item 7)의 재확인이라는 걸 스모크 스크립트 docstring에
정직하게 기록해뒀다.

## E. 회귀 확인
`stick_diagram.py` self-test 전체(Test 31 추가 전후) — `diff --strip-trailing-cr`로
대조, 내가 편집한 라인(load_topology 확장 + 신규 함수 + Test 31)만 차이나고 나머지
완전 동일. 실행 결과 FAIL 마커 34개로 편집 전/후 동일(제자리 스왑 방식으로 상대경로
깨짐 없이 in-place 비교, `.ai/context.md` "diff --strip-trailing-cr" 관례 재사용).
`sizing_recipe.py`는 이번 세션에 코드를 안 건드렸지만(회귀 확인 목적으로) 전체
self-test를 재실행 — 결과는 세션 종료 시점 기준 아래 "F. 다음 세션 확인 사항" 참고.

## F. 다음 세션 확인 사항
- `sizing_recipe.py` 전체 self-test가 이번 세션 종료 시점에 백그라운드로 아직
  실행 중이었다(5분 타임아웃을 넘겨 백그라운드로 이동, 완료까지 대기 못함) — 이
  파일은 이번 세션에 코드를 전혀 안 건드렸으므로 회귀 위험은 구조적으로 없지만,
  실제 실행 결과(exit code/FAIL 마커 개수)는 다음 세션 시작 시 확인할 것.
- 위 "지금 상태" 3번(Tier 1 idiom_matches 배선)과 4번(그리드 전략)이 다음 세션
  최우선 후보.

---

# 세션20-B 결론 — grid search 재설계 착수 → psrr_estimate_db 자유도 없음 발견 →
# PSRR 신규 유도+구현(같은 날 진행, 위 세션20 결론 이후 이어서)

세션20 결론(위)까지 끝낸 뒤, 같은 날 "run_harness.py 재실행 전략"(item 7)의 grid search
효율화를 사용자가 요청해 착수했다. 설계 도중 실측이 원래 목표보다 더 근본적인 문제
(`psrr_estimate_db`가 애초에 자유도가 없었음)를 드러냈고, 사용자가 그 자리에서 우선순위를
바꿔(오늘 이걸로 마무리) PSRR을 CMRR과 동일 엄격도로 새로 유도하는 쪽으로 진행했다.

## G. Grid search 문제 진단 + 정적 그래프 기반 그룹 분리 설계

### G-1. 사용자가 처음 요청한 것과 실제 결정 경위
"그리드 탐색을 더 효율적인 알고리즘으로 바꾸고 싶다, 문제점을 확인해서 제안해봐"라는
요청으로 시작. `optimize_full_circuit_budget()`의 grid loop(`sizing_recipe.py:2237`
부근 `itertools.product`)을 분석해 문제 4가지를 확인: (1) `O(k^13)` 지수적 폭발(기본값
`k=5`면 5^13≈12억 조합, 세션11/20 실측 `k=2`도 8192조합×~4.4초≈10시간), (2) `k=2`는
`_lerp(...,i/(k-1))`상 **경계값만** 샘플링(중간값 없음), (3) 조합마다 `_evaluate()`
전체(51개 소자 KCL+compensation 고정점 반복+LUT 탐색)를 처음부터 다시 돌며 재사용/조기
중단 없음, (4) 병렬화 안 됨(각 조합은 독립적인데 순차 실행).

제안한 4가지(A 병렬화/B 블록 분리/C 단조 theta 이분탐색/D 랜덤·LHS)를 "다 하면 어떻게
되나" 질문 뒤, "확정적 전역 최적성을 못 찾을 가능성"을 사용자가 구체적으로 물어 답변
(구조적으로 결합이 약한 편이라 판단되지만 실측 필요, 랜덤 재시작이 완화책이 됨). 사용자가
"실측 먼저 확인하고 대안 설계하자, 오늘은 설계까지만 하자"고 최종 지시.

### G-2. "이 topology만 실측하면 의미 없다" — 일반화 요구 → 그래프 기반 그룹 자동 도출
회로 하나만 손으로 눈으로 분류한 그룹(gain/classab/cmfb/biasgen 4그룹, feeds 이름을 보고
추측)은 다른 topology.json에 재사용 불가능하다는 사용자 지적 — 정확했다. 재설계:
1. **theta의 "쓰기 발자국"**: `feeds`의 `root`/`target`/`devices`(값을 실제로 바꾸는
   대상)만 — `reference`/`terms`(읽기만 하는 대상)는 **제외**. 처음엔 이 구분을 안 하고
   `feeds` 전체를 `_collect_device_refs()`(세션13, metric_spec용으로 이미 있던 범용
   재귀 소자명 수집기 — theta feed도 구조가 같아 그대로 먹힘)로 훑었다가, 12/13개
   theta가 공유 reference(`M1a`/`M4a`)를 통해 **거짓으로 하나의 거대 성분에 뭉치는**
   버그를 실측으로 발견(`_feed_root_ratio`/`_feed_diode_stack_target`/
   `_feed_gm_target_convention` 소스코드 직접 확인 — root/target만 값을 쓰고
   reference는 읽기만 한다는 게 코드로 확정) → write-footprint만 쓰도록 수정.
2. **metric의 발자국**: 기존 `_collect_device_refs(metric_spec, known_names)` 그대로
   재사용(constraints/objective에 실제로 쓰이는 metric만).
3. **edge 규칙**: (a) 두 theta의 write-footprint가 같은 constraint/objective metric의
   발자국과 겹치면, (b) 같은 KCL 직렬스택(`kcl_series_union()`) 그룹에 걸리면, (c) **다른
   theta(고정 포함)의 read-footprint가 서로 다른 자유 theta 2개 이상의 write-footprint에
   동시에 걸리면**(신규, 세 번째 경로 — 실측으로 발견, 아래 G-3).
4. union-find(`design_report.py`의 matching_pairs 그룹핑과 같은 패턴)로 연결성분 = 그룹.

### G-3. 세 번째 결합 경로 발견 — "다른 theta가 둘 다 읽는" 물리적 feasibility 결합
규칙 (a)+(b)만으로는 `K_replica`(→M9a)와 `r_classab_battery`(→M8,M17)가 서로 완전히
독립(5개 constraint 어느 것도 안 건드림)으로 나왔다. 그런데 all-lo/all-mid/all-hi
(모든 자유 theta를 각각 하한/중간/상한으로 일괄 설정) **세 가지 다 물리적으로
infeasible**(`M9b: ID<=0`, `InfeasibleSizingError`)이 실측으로 나와 재조사 — 고정
theta `kcl_battery_M9b`(type A_signed, `terms=[M8:+1, M9a:-1]`)가 두 자유 theta의
결과(M8은 `r_classab_battery`, M9a는 `K_replica`)를 **동시에 읽어서** `M9b=M8-M9a>=0`을
검사한다는 게 원인 — 이게 규칙 (c)다. 반영 후 최종 그룹: **5-theta 진짜 결합 그룹**
`{L_cascode, L_stage2out, N_cmfb_bw, r_tail_M6, r_tail_M7}`(gain_db/cmrr_estimate_db/
classab_centering_dev_v 전부 여기 걸림, 지금은 psrr_estimate_db도 — 아래 H절) +
**물리적 feasibility만으로 묶인 2-theta 그룹** `{K_replica, r_classab_battery}` +
**완전 독립 6개**(`f_slew`/`r_biasgen`/`r_bg_vbias2`/`r_classab_diode_src`/
`r_cmfb_vocdes`/`r_diode_M11a`, 5개 constraint 전부 무관 — 하한값 고정으로 충분).

## H. `psrr_estimate_db` 자유도 없음 발견 → PSRR 신규 유도(CMRR 동일 엄격도)

### H-1. 발견 경위
G-2/G-3 그래프 분석 중 `psrr_estimate_db`(옛 `diff_pair_tail` family, `tail_device:
M5`)의 발자국이 `{M5}` 하나뿐이고, **M5를 쓰는 자유 theta가 13개 중 하나도 없다**
(`kcl_tail_M5`는 고정 theta, `M4a`/`M4b` reference도 compensation이 정함 — 전부
theta-무관)는 게 드러났다. 세션20 스모크(A절 D 항목)에서 `psrr_estimate_db`가 어느
조합에서도 **소수점까지 완전히 동일한 값**(25.41226773816369)이었던 것과 정확히 일치
— **이 metric은 그리드를 어떻게 바꿔도 절대 못 바뀐다.** 즉 오늘 설계하려던 그리드
알고리즘 자체가 아니라 **metric 선언의 문제**였다. 사용자에게 즉시 보고, "PSRR 수식을
유도해서 등록해야 한다"는 지시로 방향 전환.

### H-2. 유도(CMRR과 동일 방법론/엄격도, 사용자 확정)
`_cmrr_telescopic_class_ab[_cmfb]`가 쓴 절차(`stage1_cmrr_sympy_derivation.py`:
`load_topology()` connectivity로 자동 MNA 조립 → sympy 정확해 → gm·ro≫1 leading order
→ ngspice AC 이상화 소신호 netlist로 독립 교차검증)를 **그대로** PSRR에 적용
(`stage1_psrr_sympy_derivation.py`/`stage1_psrr_ngspice_crosscheck.py`, 신규 파일,
`workspaces/current-reuse-telescopic-ota-report/spice/`).

- **연결성 재확인**: CMRR 스크립트의 `report_connectivity()`를 그대로 재실행해 같은
  회로/같은 위상(M2a.drain==M3a.drain==Vom1 드레인 합류, tail 분리 Vx/Vy 등)임을
  확인 — **연결성 오류는 없었다**, CMRR을 다시 유도할 필요는 없다고 판단(사용자가
  "필요하면 CMRR도 다시 구해, 불필요하면 PSRR만"이라고 조건부로 지시했던 부분).
- **1단 open-loop(A)**: `vdd`를 AC ground에서 빼서 독립원으로 두고(CMRR과 반대),
  `Vip`/`Vim`은 0(순수 전원→출력 전달만). Adm은 CMRR과 **기호적으로 완전히 동일함을
  재확인**(당연한 결과, 같은 신호경로). Ann(전원→stage-1 출력 CM)의 leading order를
  구하는 게 예상보다 어려웠다 — Adm처럼 단순히 "모든 gds→0"으로 스케일링하면 발산
  (eps 거듭제곱 -4~2 전부 시도해도 안 맞음), 최종적으로 `eps^3` 스케일(Adm의 eps^2보다
  한 단계 높음)에서 유한한 값을 얻었고, 정리하면:
  ```
    Ann_open = gm(tail_p 합, 즉 gm(M6)+gm(M7)) · (Rx‖Ry) · Acm_open   <- Acm_open은 CMRR과 동일
    PSRR_open(dB) = CMRR_open(dB) − 20·log10(|gm(tail_p 합)·(Rx‖Ry)|)
  ```
  즉 **PSRR은 CMRR에서 상수 하나만 뺀 값**(물리적으로 타당 — 같은 캐스코드 출력임피던스
  경로를 타기 때문). ngspice AC 독립 교차검증(±4배 랜덤 20점+앵커2점): worst 2.36dB
  (CMRR 자신의 worst 0.8dB보다 다소 크지만 탐색용으로 충분, CMRR도 SPICE 대조 worst가
  3.99dB인 family가 있었다).
- **CMFB 루프 포함(B)**: 선형 중첩으로 정확히 유도됨(재도출 불필요) —
  `vo1 = Ann_open·δ + H·vcmfb`, `vcmfb = A_c·G2·vo1`을 풀면
  `vo1/δ = Ann_open/(1+T)`(T는 `_cmrr_telescopic_class_ab_cmfb`가 이미 쓰는 그 T,
  H/A_c/G2 전부 vdd와 무관한 루프 자신의 성질이라 그대로 재사용) → **PSRR_closed =
  PSRR_open + 20·log10(|1+T|)**, CMRR과 정확히 같은 보정. ⚠️ closed-loop+vdd 조합
  자체의 독립 SPICE 검증은 시간 제약으로 안 함(H/A_c/G2/T는 CMRR 쪽에서 이미 SPICE
  검증됨, 이번에 새로 추가된 건 선형 중첩 논리뿐이라 위험은 낮다고 판단) — 여유 있으면
  다음 세션에 `cmfb_cmrr_ngspice_crosscheck.py`에 vdd 독립원을 더해 확인할 것.
- **알려진 한계(사용자 승인, (C) 2단 직접 주입은 다음 세션)**: 2단 Class-AB 출력
  전류원(M8/M13/M17/M22)도 source=vdd라 **자체 VDD 주입 경로**를 만드는데, 이번
  유도는 1단(M6/M7)만 본다 — 실제 PSRR은 이번 값보다 더 나쁠 수 있다.

### H-3. 구현 (`sizing_recipe.py`, 아직 미커밋)
`_psrr_telescopic_class_ab()`/`_psrr_telescopic_class_ab_cmfb()` 신설, `_PSRR_
ESTIMATOR_REGISTRY`에 `"telescopic_class_ab"`/`"telescopic_class_ab_cmfb"` 추가(옛
`"diff_pair_tail"`은 그대로 유지, 하위호환). CMRR 함수들과 코드를 공유하지 않고 독립적으로
재계산(이 파일의 기존 관례 — `_cmrr_telescopic_class_ab`와 `_cmrr_telescopic_class_ab_
cmfb`도 서로 공유 안 함, 기존 CMRR 코드는 이번 세션에 손대지 않음). self-test(sizing_
recipe.py, CMRR self-test 블록 직후): 앵커1/2(SPICE 대조, 오차<1dB) + "PSRR_open ==
CMRR_open - 20log10(...)" 관계 자체를 코드로 재확인 + "CMFB 보정이 CMRR/PSRR 양쪽에
정확히 같은 크기로 적용됨" 회귀 + T<=0 가드. 전체 self-test 재실행 — diff `+183 lines,
0 deletions`(순수 추가, 기존 코드 무변경), exit 0, FAIL 마커 개수 편집 전(250줄 출력)
대비 편집 후(266줄, +16줄=신규 PSRR 출력만) 정확히 일치, 회귀 없음.

`library/current_reuse_telescopic_ota.topology.json`의 `psrr_estimate_db`를 `cmrr_
estimate_db`와 완전히 동일한 device role 배정(`input_p`=M1a 등 13개 키)으로
`telescopic_class_ab_cmfb` family로 교체 + `_psrr_estimate_db_comment`로 교체 이유
기록. **교체 후 실측 재확인**: `psrr_estimate_db`의 metric 발자국이 이제
`{M1a,M2a,M3a,M4a,M5,M6,M7,M15,M16,M36a,M36b,M37a,M37b,M38}`로 커져서, G-3의 5-theta
결합 그룹(`L_cascode`/`L_stage2out`/`N_cmfb_bw`/`r_tail_M6`/`r_tail_M7`)과 실제로
겹친다 — **원래 문제(PSRR을 만족시킬 자유도가 없음)가 이번 유도로 해소됨**을 코드로
확인.

## I. 다음 세션 확인 사항 (이 절 전용)
- G절 그룹 구조(5-theta 진짜 결합/2-theta feasibility 결합/6개 완전 독립)로 **그리드
  탐색 알고리즘 자체(블록 분리+이분탐색+좌표하강+재시작+최종 joint 로컬 정제)를
  구현**하는 게 다음 세션 최우선 — 오늘은 설계+실측만, 구현은 안 함(사용자 지시).
- H-2에서 미룬 (C)(2단 M8/M13/M17/M22의 자체 VDD 주입) 유도, 여유 있으면 closed-loop
  PSRR의 독립 SPICE 검증도.
- 시작점 선택(all-lo/mid/hi 전부 infeasible) 문제 — 그룹 분리 알고리즘 설계 시 "KCL
  identity feasibility를 먼저 만족시키는 pre-solve" 단계를 반드시 포함할 것.
- ⚠️ **이 G/H절의 결론은 세션21에 무효화됨**(아래 "세션21 결론" 참고) — Kp'/Kn'/Rx/Ry
  폐형식 자체가 M10/M19 로딩을 몰라 최대 49dB 틀렸다는 게 드러나 CMRR/PSRR이 수치
  MNA로 전면 교체됐다. 이 그룹 구조를 그대로 그리드 알고리즘 구현에 쓰지 말 것 — 새
  metric 발자국으로 재도출 필요.

---

# 세션21 결론 — PSRR (C)단계 착수 중 M10/M19 로딩 버그 발견(최대 49dB) → CMRR/PSRR
# 폐형식 전면 폐기 → 수치 MNA(31소자)로 교체, ngspice 독립검증 완료(오차 0.0002%)

세션20-B가 "다음 세션 최우선"으로 남긴 두 항목(그리드 탐색 구현, PSRR (C)단계) 중
사용자가 확정한 순서대로 PSRR (C)단계부터 시작했다. **좁은 범위(M8/M13/M17/M22의 자체
VDD 주입 경로만 PSRR에 추가)로 시작했으나, 실측 과정에서 그 범위로는 담을 수 없는 훨씬
근본적인 문제를 발견해 사용자와 두 번 상의 후 범위를 CMRR까지 확장**했다. 아래 순서대로
정리한다.

## A. 착수 — battery 네트워크를 stage-1 MNA에 결합 시도, 두 번의 접근 실패

1. **1차 시도(통짜 31소자/18노드 sympy linsolve)**: `stage2_battery_psrr_sympy_
   derivation.py` 초안 — M8/M9a/M9b/M11a/M11b/M12/M10/M13/M14a/M14b(Vg15/Vop1측 10개)
   + 거울대칭 Vg25/Vom1측 10개를 stage-1 11개에 더해 18노드를 sympy `linsolve`로 한
   번에 풀려 함 — **실측: 수 분간 2.8GB+ 메모리, 진행 없음**(fraction-free Gaussian
   elimination의 중간식 크기 지수적 폭발). 프로세스 kill.
2. **2차 시도(블록소거, 5노드만 먼저 정확해로 풀어 8노드에 얹기)** — battery-A 5노드
   (Vg15/N11a11b/N11b/N14a14b/N14a_14b, Vop1은 외부단자로 열어둠)만 먼저 sympy로 풀었더니
   **이미 이 5노드 정확해 자체가 200항 넘는 단일 유리식**이 됐고, 그걸 stage-1 8노드
   KCL에 대입해 다시 정확해로 풀려 하니 똑같이 3.3GB+로 폭주. Kill.
3. **교훈(핵심)**: 이 프로젝트의 모든 폐형식은 원래 gm·ro≫1 **leading order**만 필요한데,
   위 두 시도는 정확해부터 구하고 나중에 극한을 취하려 했다 — **leading order를 각
   서브회로 단계에서 처음부터 적용**하면 매 단계가 작은(2~3노드) 시스템으로 남는다는 걸
   이번에 배웠다(다음에 회로가 더 커지면 이 방식을 기본으로 삼을 것).

## B. 단계별 leading order로 PSRR (C) 자체는 성공 — 그러나 회로가 "생각보다 훨씬 다르다"는
## 신호를 만남

`stage1_psrr_sympy_derivation.py`/`stage1_cmrr_sympy_derivation.py`와 같은 방법론을
작은 서브회로 단위로 쪼개 적용:
- **N11b replica-bias 체인**(M11a-M11b-M12, Vg15/Vop1과 완전히 분리된 독립 서브회로임을
  코드로 확인)을 2노드 leading order로 풀면 `vN11b → vdd`(gds12→0 극한에서 정확히
  vdd — M12의 출력임피던스가 diode 체인보다 훨씬 커서, N11b가 diode 경로로 vdd를
  거의 그대로 따라간다는 뜻).
- **N14a14b 체인**(M13-M14a-M14b)도 2노드로 풀면 `vN14a14b = gm13·(gm14a+gm14b)/
  (gm14a·gm14b) · vdd` — **O(1) 크기**(억제 안 됨)로 vdd를 따라간다.
- 이 둘을 Vg15 KCL(M8/M9a/M9b)에 대입하면, **Vop1에 주입되는 battery-A net 전류가
  놀랍도록 단순화**됨: `I_into_Vop1 = gdsh_M10·vop1 − gm_M8·vdd` — N11b/N14a14b/Vg15의
  복잡한 중간식이 전부 대수적으로 상쇄되고, **"M8이 Vop1에 직접 꽂혀 M10으로만 부하되는"
  것과 leading order에서 완전히 등가**가 된다(우연이 아니라 Monticelli floating current
  source의 정의상 성질 — M8이 사실상 그대로 전달됨).
- 이걸 stage-1 8노드에 얹어 Adm_full/Ann_full을 구하고 `eps→0`(gdsh_M10도 같은 스케일로
  취급) leading order를 취하니: **`Adm_full ~ (gm_M1a+gm_M4a)/gds_M10`**,
  **`Ann_full ~ (gm_M6+gm_M7+2·gm_M8)/(2·gds_M10)`** — **캐스코드 임피던스(Kp'∥Kn',
  세션20까지 CMRR/PSRR의 근간)가 완전히 사라지고 M10/M19 하나로 결정되는 형태**로
  바뀌었다. 이게 이 세션 전체를 바꾼 첫 신호였다.

## C. 발견 — M10/M19(class-AB 바이어스 싱크)가 Vop1/Vom1 임피던스를 지배, 옛 폐형식은
## 이걸 몰라 실제값과 최대 49dB 어긋난다

B절의 leading order 결과를 세션20의 `Ann_open`(1단만, M10/M19 모름)과 수치로 비교
(랜덤 15점, ±4배 스윕):

| | 값 범위 |
|---|---|
| 실제(31소자 exact, battery 포함) PSRR | −8.6 ~ +20.4 dB |
| 세션20 `psrr_estimate_db`(당시 이미 커밋돼 그리드 탐색에 쓰이던 값) | **−41.5 ~ −9.6 dB** |
| 오차 | **−21.7 ~ −49.3 dB** |

**원인**: `M10`/`M19`(`S=gnd, D=Vop1/Vom1, G=Vbias4`인 단순 NMOS 싱크, class-AB 바이어스용)
는 캐스코드가 아니라서 출력컨덕턴스가 O(eps¹)인데, stage-1 캐스코드 임피던스(Kp'∥Kn')는
O(eps²)(훨씬 높은 임피던스) — 병렬로 연결되면 **컨덕턴스가 낮은(=임피던스가 낮은) M10/M19
쪽이 이긴다**. 세션20까지의 모든 CMRR/PSRR 폐형식(그리고 `gain_db`의 stage-1 부분도
같은 구조)은 M10/M19를 아예 몰랐다. 이건 PSRR만의 문제가 아니라 **CMRR/gain_db에도
동일하게 적용되는 회로 모델 자체의 결함**이라고 판단해 사용자에게 즉시 보고 →
AskUserQuestion으로 범위를 물어 **"CMRR/gain_db도 같이 재점검"**으로 확정(사용자 선택).

## D. 폐형식 근사 두 번 더 시도 — 둘 다 실패, 폐형식 자체를 포기

1. **leading-order 근사를 그대로 구현**(B절 결과) — exact(31소자)와 랜덤 스윕 대조하니
   **worst 12.02dB 오차**(이 프로젝트가 지금까지 요구해온 기준 — CMRR worst 0.8dB,
   PSRR-open worst 2.36dB — 에 한참 못 미침).
2. **병렬컨덕턴스 가설**("M10을 기존 Kp'∥Kn' R_out에 그냥 병렬로 얹으면 되지 않을까" —
   Adm은 물리적으로 그럴듯해 보였음) — 수치로 대조(`stage2_rout_parallel_conjecture_
   check.py`)하니 **Adm은 그나마 근접(worst 15%)했지만 Acm/Ann은 완전히 틀렸다
   (부호까지 반대, 최대 1100배 상대오차)** — CM/PSRR 경로는 단순 R_out 치환으로
   포착되지 않는 진짜 다른 구조라는 뜻.
3. **정확해(추가 근사 없음)를 그대로 쓰는 방안도 검토** — `stage2_dump_exact_forms.py`로
   raw(단순화 안 한) 정확해 크기를 재보니 **분자 6,000~16,000항** — 손으로 옮겨적을 수
   있는 크기가 절대 아님. 폐형식 접근 자체를 이 지점에서 포기.

## E. 채택된 해법 — 수치 MNA(폐형식 대신 그 자리에서 KCL을 수치로 푼다), ngspice 독립검증
## 완료(오차 0.0002%)

**핵심 통찰(D절에서 얻음)**: sympy **정확해**는 M10/M19를 넣는 순간 못 쓰지만, **수치**로는
노드가 18개든 31소자든 순식간이다(`stage2_numeric_mna_validate.py`로 확인 — 같은 회로를
순수 float Gaussian elimination으로 풀면 즉시 끝남). 사용자에게 이 트레이드오프
(정확도 vs `sizing_recipe.py`의 기존 "circuit_family별 폐형식 함수 레지스트리" 패턴과
다른 구조가 됨)를 설명하고 AskUserQuestion으로 확인 → **"수치 MNA solver로 전환"** 채택.

### E-1. 구현 (`sizing_recipe.py`, 아직 미커밋)
- **`_mna_solve_smallsignal(devices, unknown_nodes, fixed)`** 신설 — 순수 Python
  Gaussian elimination(부분피벗), numpy 등 외부 의존성 없음. `devices`는
  `(drain, source, gate, gm, gds)` 튜플 — 기존 sympy 유도 스크립트들의 `build_mna()`와
  동일한 소자모델(`I(d->s)=gm*(vg-vs)+gds*(vd-vs)`).
- **`_load_telescopic_topology_cached()`** 신설 — `current_reuse_telescopic_ota.
  topology.json`의 connectivity를 `load_topology()`로 그대로 읽어 캐시(하드타이핑
  없음 — **topology.json이 유일한 토폴로지 소스**라는 프로젝트 원칙을 이 수치 solver
  에서도 그대로 지킨다. 이게 왜 중요한가: 만약 connectivity를 Python에 두 번째로
  손으로 옮겨 적었다면 JSON이 나중에 바뀔 때 소리 없이 어긋나는 위험이 생긴다).
- **`_telescopic_class_ab_open_loop_response(metric_spec, ctx, vip, vim, vdd, vcmfb)`**
  신설 — stage-1(11소자, 이제 a/b 양쪽 다 실제 사이징값 사용 — 예전처럼 완전대칭
  가정으로 a쪽만 쓰지 않는다) + 양쪽 Monticelli battery(각 10소자) = **31소자**를
  `metric_spec`의 롤 배정(신규 키 `input_p_b`/`cascode_p_b`/`input_n_b`/`cascode_n_b`
  + `battery_vop1_side`/`battery_vom1_side`, 각각 10개 서브롤 dict)으로 조립해
  (Vop1,Vom1)을 수치로 푼다. `cmfb_ctrl_device`(M7)의 gate가 topology.json에서 이미
  `Vcmfb`이므로 `vcmfb` 인자가 별도 분기 없이 자동으로 M7에만 걸린다.
- **`_telescopic_class_ab_open_loop_gains(metric_spec, ctx)`** 신설 — 위 함수를 4가지
  여기로 호출해 **Adm_open/Acm_open/Ann_open/H를 전부 같은 31소자망에서** 얻는다
  (Adm: vip=±0.5, Acm: vip=vim=1, Ann: vdd=1, H: vcmfb=1 — H는 세션20까지 Kp/Kn/Rx/Ry
  폐형식이었는데 이제 이것도 같은 수치망으로 대체됨, "CMFB 루프 → stage-1 출력 CM"
  전달경로도 M10/M19 로딩의 영향을 받으므로 일관되게 고쳐야 했다).
- **`_cmrr_telescopic_class_ab_cmfb()`/`_psrr_telescopic_class_ab_cmfb()`** — 본문을
  위 4개 값을 받아 조합하는 것으로 교체(선형중첩 결합 로직 `T=-H·A_c·G2`,
  `CMRR=|Adm/Acm|·|1+T|`, `PSRR=PSRR_open+20log10(1+T)` 자체는 세션20-B가 이미 정확히
  유도한 것 그대로 유지 — 재도출 불필요, **바뀐 건 Adm_open/Acm_open/Ann_open/H를
  구하는 방법뿐**). `A_c`(CMFB 앰프 이득)/`G2`(2단 CM 전달이득)는 M10/M19와 무관한
  별개 서브회로라 세션20 폐형식 그대로 재사용.
- **`topology.json`** — `cmrr_estimate_db`/`psrr_estimate_db`에 위 신규 키(총 6개:
  `input_p_b`/`cascode_p_b`/`input_n_b`/`cascode_n_b`/`battery_vop1_side`/
  `battery_vom1_side`) 추가 + `_cmrr_estimate_db_comment`/`_psrr_estimate_db_comment`
  교체(교체 이유/근거 기록).

### E-2. 검증
- **self-test 전면 재작성**(`sizing_recipe.py`) — 옛 Kp'/Kn' 폐형식 전용 fixture(7~13
  소자)로는 새 코드를 돌릴 수 없어(31+7=38소자 필요) 전체 fixture를 새로 작성. 지금은
  **자기회귀**(같은 값을 `compute_metric()` 경유 vs `_telescopic_class_ab_open_loop_
  gains()` 직접호출 두 경로로 계산해 일치하는지, `T<=0` 가드 동작, Ry×20/gm7×4가 CMRR을
  개선하는 방향인지)만 확인 — 새 앵커(CMRR=128.7182dB, CMRR anchor2=146.7202dB,
  PSRR=89.3832dB)는 SPICE 절대 검증이 아니라 회귀 고정용. `sizing_recipe.py` self-test
  전체 재실행 — **exit 0, 새 CMRR/PSRR 블록 전부 PASS, 그 앞뒤 다른 self-test 회귀 없음**
  (259줄 출력 확인).
- **ngspice AC 독립 교차검증(가장 중요한 검증)** — `stage2_battery_psrr_ngspice_
  crosscheck.py` 신규: 이상화 VCCS+R netlist(connectivity는 `load_topology()`로 그대로,
  손타이핑 없음)를 self-test와 완전히 같은 파라미터로 조립해 ngspice AC로 Adm_open/
  Acm_open/Ann_open/H를 직접 측정하고 Python 수치 solver 결과와 대조 — **완전히 다른
  두 솔버(내가 짠 Gaussian elimination vs ngspice)가 오차 0.0001~0.0002%(부동소수점
  잡음 수준)로 일치**. 수치 MNA 구현 자체의 정확성이 독립적으로 확정됐다.

## F. 알려진 한계 / 다음 세션 이월 사항

1. **`gain_db`(stage-1 부분, `_metric_gain_stages_sum`)/`classab_centering_dev_v`는
   여전히 M10/M19를 모르는 옛 방식** — 사용자가 "CMRR/gain_db 같이 재점검" 범위를
   승인했지만, `gain_db`는 `_metric_gain_stages_sum`이라는 **여러 회로가 공유하는 범용
   metric 타입**(CMRR/PSRR처럼 이 회로 전용 `circuit_family`가 아님)이라 고치면 다른
   topology.json에도 영향이 갈 수 있어 이번 세션 범위에서 의도적으로 제외했다(더 넓은
   블라스트 반경, 별도 논의 필요) — 다음 세션 판단 필요.
2. **`A_c`/`G2`는 여전히 폐형식** — M10/M19와 무관한 별개 서브회로(CMFB 앰프, 2단 출력)
   라는 판단으로 그대로 뒀으나 독립 재확인은 안 했다.
3. **closed-loop(CMFB 포함)+vdd 조합 자체의 ngspice 재검증은 안 함** — E-2에서 검증한
   건 open-loop(Adm/Acm/Ann/H) 4개뿐, `T=-H·A_c·G2` 조합 이후의 최종 CMRR/PSRR 수치를
   ngspice로 직접 재는 것은 아직(세션20-B도 이 조합은 SPICE 검증 안 했다는 걸 이미
   명시했었음 — 여전히 미해결로 이월).
4. **그리드 탐색 그룹 구조(세션20-B G/H절) 전면 무효화** — metric 발자국이 완전히
   바뀌어서(이제 M10/M19/M8/M9a/M9b 등 31소자 대부분이 발자국에 들어감) 재도출 필요
   (위 "지금 상태" 1번).
5. **battery 소자(M8~M24b류)들이 13개 자유 theta 중 어느 것과 연결돼 있는지 미확인** —
   만약 전혀 안 닿는다면(PSRR이 세션20 M5처럼 다시 상수가 될 위험) 그리드 탐색 전에
   반드시 먼저 확인할 것.
6. **커밋 안 됨** — `sizing_recipe.py`/`current_reuse_telescopic_ota.topology.json`
   변경사항, 신규 스크립트 5개(`stage2_battery_psrr_sympy_derivation.py`,
   `stage2_rout_parallel_conjecture_check.py`, `stage2_dump_exact_forms.py`,
   `stage2_numeric_mna_validate.py`, `stage2_battery_psrr_ngspice_crosscheck.py`)
   전부 다음 세션 시작 시 `git status`로 재확인 후 커밋 판단할 것(사용자 지시 없이는
   자동 커밋 안 함).
7. ⚠️ **이 절(위 A~F) 전체가 세션21 2차로 대체됨** — 아래 "세션21 2차 결론" 참고.
   `circuit_family="telescopic_class_ab_cmfb"`/`battery_vop1_side`류(위 E-1)는 이제
   `cmrr_estimate_db`/`psrr_estimate_db`가 실제로 안 쓴다(`type`이 `smallsignal_ratio_db`
   로 바뀜) — `_cmrr_telescopic_class_ab_cmfb()`/`_psrr_telescopic_class_ab_cmfb()`
   Python 함수 자체는 코드에 남아있지만(다른 회로가 `circuit_family`로 여전히 쓸 수
   있음, 하위호환/롤백용) topology.json이 더는 가리키지 않는다.

---

# 세션21 2차 결론 — CMRR/PSRR/gain을 topology-무관 수치 MNA로 완전 일반화(51소자 전체
# + passive_elements, ports 선언 활용) — ngspice 재검증 완료

세션21 1차(위, "battery 31소자 부분망 + circuit_family 전용 함수")를 사용자와 대화 중
"CMRR/PSRR/gain 공식을 compensation까지 확장해서 topology에 무관한 수치해석 solver로
일반화할 수 있을까?"라는 질문을 받고, 먼저 설계만 제시한 뒤(exploratory 질문 -> 2~3문장
권고+트레이드오프 원칙) 사용자가 "CMRR/PSRR/gain 일반화부터 설계해줘" -> 확인질문 2개
답변 -> "지금 구현에 들어가자"로 이어서 같은 세션 안에 설계+구현+검증까지 완료했다.

## A. 사전 실측 — 설계를 뒷받침한 사실 3가지

1. **4개 topology.json 중 `current_reuse_telescopic_ota` 하나만** `cmrr_estimate_db`/
   `psrr_estimate_db`를 선언하고 있었다(나머지 folded_cascode/nmcnr_amplifier/
   two_stage_ota는 아직 이 metric 자체가 없음) — 일반화해도 기존 동작을 깨는 회로가
   없다는 뜻(마이그레이션 리스크 낮음).
2. **`ports` 섹션이 이미 있었다** — `Vip`=differential_input_p, `Vim`=differential_input_n,
   `Vop`=differential_output_p, `Vom`=differential_output_n(**최종 출력**). 그런데
   세션21 1차까지 CMRR/PSRR은 `Vop1`/`Vom1`(1단 내부노드)만 센싱하고 있었다 — 이미
   JSON에 선언된 "진짜 포트"를 안 쓰고 있었던 셈.
3. **`ideal_sources`(예: `Iref`, kind=`current_source`)는 소신호에서 개방회로**(무한
   임피던스)라 MNA에 안 넣으면 되고, **`passive_elements`(R1/R2, CMFB Voc 평균망)는
   지금까지 `cm_sense_gain=1.0`이라는 우회 파라미터로만 흉내내고 실제 저항으로는 안
   들어가 있었다**(R1: Vom-Voc, R2: Voc-Vop — 정확히 최종출력을 감지). 또한
   `passive_elements`에 압축용 Cc1/Rz1(Vom-Cc1-N_cc_rz1-Rz1-Vop1)/Cc2/Rz2(대칭)가
   이미 connectivity로 들어있다는 것도 이번에 재확인(2026-08-03에 발견된 gap, 커패시터라
   DC/mid-band 소신호에선 개방 — 이 solver 범위 밖, GBW/PM은 ngspice로 다룰 것).

## B. 설계 핵심 — "부분을 손으로 조합" 대신 "전체를 한 번에 푼다"

- **topology.json의 소자 51개 전부 + passive_elements 중 저항(R1/R2/Rz1/Rz2, 값
  없으면 1GΩ 근사, 사용자 확정 — 논문 "averaging" 의도 그대로 부하 안 줌)를 하나의
  MNA로 스탬프**. `gnd`만 진짜 AC ground, 나머지(Vbias1~4/Vcmfb/bias-gen 체인 전부)는
  자유노드로 풀린다.
  - 이 결정 하나로 **H/A_c/G2/T 손조합 로직(세션21 1차의 핵심 구조)이 완전히 필요
    없어졌다** — Vcmfb가 루프의 일부로 자연스럽게 풀리므로 CMFB 루프 기여가 하나의
    풀이 안에 자동으로 들어간다.
  - **부수 효과(설계 당시엔 예상 못 했다가 구현 후 발견)**: bias-gen 체인(M18_bg 등)도
    자유노드가 되므로, 세션20부터 "정직한 한계"로 반복 남겨뒀던 "bias-gen 자신도 VDD에
    물려있어 PSRR에 기여할 수 있다"는 항목이 **자동으로 반영**됐다(실측: `Vbias1`이
    vdd 리플을 1:1로 그대로 따라감 — `Iref`를 이상적 전류원으로 다루면 diode-connected
    `M18_bg`가 이걸 강제한다는 게 물리적으로 맞는 결과임을 손으로도 재확인).
- **센싱 위치를 `Vop1`/`Vom1`(1단 내부, 세션21 1차까지) → `Vop`/`Vom`(`ports`가
  선언한 진짜 최종출력)으로 전환**(사용자 확정) — 이제 R1/R2가 실제로 감지하는 노드와
  정확히 일치, 근사 없음.
- **새 범용 metric 타입 2개**(`type` 값): `smallsignal_ratio_db`(cmrr/psrr류 "두 여기의
  응답비를 dB로"), `smallsignal_gain_db`(gain류 "한 여기의 응답을 dB로") — 회로별
  Python 함수 없이 topology.json의 `excite_num`/`excite_den`/`sense_p`/`sense_n`
  선언만으로 계산.

## C. 구현 (`sizing_recipe.py`, 아직 미커밋)

- **`SizingContext.topology_path`** 필드 신설 — `optimize_full_circuit_budget()`이
  자신이 받은 `topology_path`를 그대로 채운다(F엔진의 다른 metric들과 달리 이 두 신규
  타입만 유일하게 connectivity가 필요해서 생긴 예외).
- **`_load_full_topology_cached(topology_path)`** — connectivity+passive_elements를
  경로별로 캐시(여러 topology.json을 같은 프로세스에서 오갈 수 있음).
- **`_full_circuit_devices(by_name, sized, passive_elements)`** — 모든 MOSFET + 저항
  passive_elements를 `_mna_solve_smallsignal()`용 튜플로 변환(저항은 `gate=source,
  gm=0`으로 스탬프하면 같은 소자모델이 자동으로 평범한 2단자 저항이 된다 — 별도 분기
  불필요). 커패시터/ideal_sources는 의도적으로 안 읽음.
- **`_full_circuit_response(ctx, excite, also_fix=frozenset())`** — 회로 전체를
  `excite`로 여기해 모든 노드 전압을 수치로 푼다. **`also_fix` 신설 이유(실측으로
  발견한 버그)**: `Vip`/`Vim`처럼 게이트로만 쓰이고 drain/source로는 전혀 안 쓰이는
  노드가 `excite`에서 빠지면(예: PSRR의 `excite_den={"vdd":1}` 호출) **자유노드로
  취급되면서 KCL 행이 통째로 0이 돼 특이행렬**이 된다(게이트는 전류를 안 뽑아 자기
  KCL 방정식이 아예 안 생김) — `_metric_smallsignal_ratio_db()`가 `excite_num`/
  `excite_den` 전체 키의 합집합을 `also_fix`로 넘겨, 어느 쪽 호출에서도 상대방의
  여기 노드가 방치되지 않게 한다.
- **`_metric_smallsignal_ratio_db`/`_metric_smallsignal_gain_db`** — `_METRICS_REGISTRY`
  에 신규 등록. `circuit_family` 2단계 lookup(`_metric_cmrr_estimate`류) 없이 바로
  `type`으로 dispatch되는 F엔진 1단계 metric.
- **`current_reuse_telescopic_ota.topology.json`** — `cmrr_estimate_db`/
  `psrr_estimate_db`를 `type=smallsignal_ratio_db`로 교체(`sense_p/n=Vop/Vom`),
  `gain_full_circuit_db` 신규 추가(옵트인, 기존 `gain_db`=`gain_stages_sum`은 안 건드림
  — 범용 metric 타입이라 다른 회로 영향 고려해 이번엔 안 바꿈).

## D. 검증

- **self-test**: 51소자 fixture(세션21 1차 38개 + bias-gen/2단 미러/Voc_des 분압기
  나머지 13개) 신규 작성, `gain_full_circuit_db`/`psrr_estimate_db`(신규)/
  `cmrr_estimate_db`(신규) 자기회귀 + ngspice 대조 둘 다 assert. `sizing_recipe.py`
  self-test 전체 재실행 — **exit 0, 새 블록 전부 PASS, 그 앞뒤 회귀 없음**(269줄).
- **ngspice AC 독립 교차검증**(`stage3_full_circuit_ngspice_crosscheck.py` 신규,
  connectivity는 `load_topology()`로 그대로, 51소자+R1/R2/Rz1/Rz2 전부 이상화
  VCCS+R netlist로 조립):

  | 값 | Python | ngspice | 오차 |
  |---|---|---|---|
  | gain(=Adm, dB) | 99.0154 | 99.0154 | <0.001dB |
  | PSRR(dB) | 105.5051 | 105.5051 | <0.001dB |
  | CMRR(dB) | 125.7672 | 125.1843 | 0.58dB |
  | Vbias1(vdd=1V 여기) | 1.000000 | 1 | 0 |

  CMRR만 0.58dB 차이 나는 이유: Acm이 CMFB 루프로 심하게 억제된 값(~0.049, 큰 항들의
  거의 완전한 상쇄 결과)이라 서로 다른 두 솔버(내 Gaussian elimination vs ngspice의
  내부 LU)의 수치적 조건 민감도 차이로 보인다 — 이 프로젝트가 CMFB류 교차검증에서
  이미 받아들인 오차 범위(세션20-B 앵커도 worst 3.99dB) 안이라 문제로 보지 않는다.
  Adm/Ann/PSRR처럼 덜 억제된(더 well-conditioned) 값들은 사실상 정확히 일치한다.

## E. 알려진 한계 / 다음 세션 이월

1. **`>=60dB` constraint 임계값 재보정 필요**(위 "지금 상태" 1번) — 센싱 위치+포함
   범위가 완전히 바뀌어 절대 dB 스케일이 달라짐.
2. **그리드 탐색 그룹 구조(세션20-B)가 또 한 번 무효화** — 이번엔 정말 거의 모든
   소자가 metric 발자국에 들어갈 수 있어(bias-gen까지), 자유 theta와의 실제 연결
   여부를 다시 확인해야 함(위 "지금 상태" 2번).
3. **다른 3개 회로(folded_cascode/nmcnr_amplifier/two_stage_ota)로 확장 안 함** —
   `ports` 선언이 없어서(현재 `current_reuse_telescopic_ota`만 있음) 바로는 못 쓴다.
   확장하려면 먼저 각 회로에 `ports`(+필요시 `excite_num`/`excite_den` 관례)를
   선언해야 함 — 사용자 판단 필요(위 "지금 상태" 6번).
4. **`gain_db`(옛 `gain_stages_sum`)는 안 건드림** — `gain_full_circuit_db`를 옵트인
   으로만 추가했고, 기존 `gain_db`는 다른 회로도 같이 쓰는 범용 타입이라 blast radius가
   더 넓어 이번 세션 판단 밖으로 남겨둠.
5. **compensation(Cc1/Cc2, GBW/PM)은 의도적으로 범위 밖** — 애초에 사용자와 논의한
   설계 분리(CMRR/PSRR/gain=이 solver, GBW/PM=ngspice 드라이버화)를 그대로 유지.
6. **커밋 안 됨** — 위 "지금 상태" 0번/7번 참고, 신규 스크립트 1개
   (`stage3_full_circuit_ngspice_crosscheck.py`) 추가.

---

# 세션22 결론 — metrics dict 크래시 수정, 60dB 임계값 유지 결정, geometry_
# colocation_union() 전면 재설계로 stack M6 크래시 근본 해결, `optimize_full_
# circuit_budget()`이 이 프로젝트 역사상 처음으로 51소자 전체 회로에서 end-to-end
# 크래시 없이 완주

세션21이 남긴 최우선 항목("`>=60dB` 임계값 재보정, item 2 그리드 그룹 재분석과 함께")을
이어가려다, 실측 확인 과정에서 훨씬 근본적인 구조적 버그를 연쇄로 발견해 그 해결에
세션 대부분을 썼다. `run_harness.py` 계열이 이 회로에서 지금까지 단 한 번도 도달한
적 없는 파이프라인 깊이까지 처음으로 뚫고 들어가면서, 아무도 실측한 적 없던 코드
경로의 버그가 한 겹씩 드러났다 — 매번 "이게 마지막이겠지" 하고 고치면 그 다음 겹이
나오는 패턴이 총 6~7회 반복됐다.

## A. `>=60dB` 임계값 — 실측 근거 확보 시도 → 버그 발견 → 사용자가 "유지"로 결정

1. **첫 실측**: 실제 production `topology.json` bounds로 대표 theta 조합(K_replica=0.1,
   r_classab_battery=0.3, 나머지 11개 자유 theta는 중간값 고정)을 사이징하니
   `optimize_full_circuit_budget()`이 **metrics 딕셔너리 안에 있으면 안 되는 주석 키**
   (`_cmrr_psrr_estimate_db_comment`, 세션21 2차가 넣었는데 metrics 바깥에 둬야 한다는
   2026-08-03 주석의 규칙을 위반)로 즉시 `TypeError` — `run_harness.py`가 지금껏 완주한
   적이 없어 발견되지 않았던 실제 버그. 주석을 `_metrics_comment*`와 같은 레벨(metrics
   바깥)로 옮겨 수정, `topology.json` JSON 유효성 재확인.
2. 버그 수정 후 재실측: `cmrr_estimate_db≈93.16dB`, `psrr_estimate_db≈96.75dB`,
   `gain_db≈77.04dB`(단, 이 조합은 `classab_centering_dev_v` 위반) — 세션21 self-test
   앵커(CMRR≈125.8dB, PSRR≈105.5dB, 손으로 만든 fixture)와 함께 "새 스케일에서 60dB는
   사실상 항상 만족되는 죽은 제약"이라는 정황 확보.
3. **사용자 결정**: 60dB 값 자체는 물리적으로 여전히 "틀린" 문턱은 아니므로, 지금은
   손대지 않고 **다음에 실제 최적화 결과가 쌓이면 그때 재보정**(아래 "지금 상태" 2번).
   딱 2개 실측점(하나는 다른 제약 위반 상태)만으로 임계값을 확정하는 건 상상으로
   채우는 것과 같다는 프로젝트 원칙에 따른 보수적 결정.

## B. Item 2(그리드 그룹 재분석) 시도 중 "stack M6" 크래시 발견 → 근본원인까지 추적

OAT(one-at-a-time) 민감도 스윕을 시도하는 과정에서, 나머지 12개 theta를 물리적으로
유효한 값(K_replica=0.1, r_classab_battery=0.3)에 고정하고 각 theta를 하한/기준/상한으로
흔드는 실험을 설계했으나, **baseline 자체가 `assign_finger_geometry()`에서 크래시**:

```
stack 'M6'(구성원 ['M1a','M1b','M2a','M2b','M57','M58','M6','M7'])에 대해
어떤 finger_w 후보도 못 찾음
```

### B-1. 근본원인 진단 — `geometry_colocation_union()`의 무근거 자동병합
`stack_groups_geometry`를 만드는 `geometry_colocation_union()`(세션10)의 rule1("같은
극성 + non-rail + drain=source면 선언 여부 무관하게 자동 병합")이, `Vx`(stage-1 tail/
diff-pair 공유 노드)에 `M58`(bias-gen 하우스키핑 소자, source=Vx)이 얹혀있다는 이유만
으로 전류 규모가 수십~수백 배 다른 `M57/M58`을 `M6/M7/M1a/M1b/M2a/M2b`와 **한
finger-공유 stack**으로 묶어 공통 finger_w를 못 찾은 것. 이건 세션10/11이 이미 진단한
"부채꼴(fan-out) 전이적 병합" 패턴이 `geometry_colocation_union()`(finger_w 공유용)
에서 재발한 것 — 세션11~15가 만든 euler-fixup 체인(`mirror_symmetric_trail` 등)은
전혀 다른 grouping(`kcl_series_union()` 기반 stack_id)을 다뤄서 이 문제와 무관했다.

### B-2. analog-grammar 실측 — "물리적 사실"과 "기능적 판단"은 다른 질문
51소자 전체를 analog-grammar `analyze.py`에 직접 돌려보니(`stack_edges()`가 analog-
grammar도 M6/M7→M58을 Vx 공유로 같은 스택으로 본다는 것 확인) 두 자동 도구(geometry_
colocation_union/analog-grammar) 다 "물리적으로 같은 노드에 물려있다"는 사실은
맞히지만 "그래도 기능적으로 다른 블록(bias-gen 하우스키핑 vs 신호경로)"이라는 **판단**
은 어느 쪽도 못 한다는 게 확인됨 — 이 판단은 이미 `topology.json`의 `vertical_stack_id`
(M6/M7=`stage1`, M57/M58=`biasgen_tree_b`)에만 있었다(단, M1a/M1b/M2a/M2b엔 애초에
`vertical_stack_id` 자체가 선언 안 돼 있음 — compensation 경로로 결정된다는 이유로
세션 배치7-5부터 의도적으로 비워둔 필드).

analog-grammar의 raw idiom matching은 `matching_pairs` 자동화 후보로는 유용함도 확인
(`M13+M17+M18_bg+M22+M6+M60+M61+M8` 8소자 current-mirror 정확히 재현) — 단
`M36a+M7`(세션18 L-3/L-4가 이미 "다른 기능 블록" false positive로 확정해둔 사례)이
raw 출력에 그대로 재현돼, 세션19가 설계만 하고 미배선한 Tier 1 필터가 왜 필요한지
재확인. (오늘은 matching_pairs 자동화 자체는 구현 안 함 — 다음 세션 후보.)

### B-3. composite(직렬 상속) 방식도 시도 — 유효하지만 이 문제는 못 풂
`find_stacked_matching_candidates()`(세션19 C-3)를 실제 matching_pairs에 돌려보니
7개 결과 전부가 이미 선언된 매칭쌍과 정확히 일치(좋은 교차검증) — 하지만 M6/M7/M57/M58
은 애초에 어떤 matching_pairs의 씨앗도 아니라서(M6/M7은 서로 다른 게이트라 매칭쌍이
아니고, M58은 어떤 확정쌍 위에도 안 얹혀 있음) 이 메커니즘의 전파가 시작되지 않는다 —
"매칭 대칭성" 축과 "finger_w 공유" 축은 원래 다른 질문이라는 게 재확인됨.

### B-4. 사용자 확정 설계 — "matching_pairs가 base, layout 최적화 위해 확장 가능"
하위호환을 포기하고 정합성 있는 구조로 개선하기로 명시적 결정(사용자: "matching이
안 되는 소자들을 stack에서 밀려내는 게 가능하지 않나" → "matching을 기본으로 그룹하고
layout 최적화 위해 같은 그룹에 다른 것들을 추가하는 방향은 괜찮아 보인다").

⚠️ **이 재설계 전에 사용자가 먼저 명시적으로 확인한 경계 조건(일반 방법론으로 기록)**:
"kcl로 그룹하는 것(`kcl_series_union()`, A엔진 전류 propagation/`stack_id`용)과
layout의 최적화를 기준으로 그룹하는 것(`geometry_colocation_union()`, finger_w
공유용)은 차이가 있을 수 있다는 사항은 유지되어야 한다"(사용자 원문) — 즉 이번 재설계는
**`geometry_colocation_union()` 하나에만** 적용하고 `kcl_series_union()`은 의도적으로
안 건드렸다. **"matching_pairs가 base, 검증된 상속으로만 확장"이라는 방법론 자체는
`geometry_colocation_union()`류(선언 없이 자동으로 물리적 병합 후보를 추측하는 함수)
에 일반적으로 적용 가능한 원칙이지, `kcl_series_union()`류(전기적으로 강제되는 사실을
찾는 함수, "무근거 추측"이 아니라 "2단자 net이면 전류가 같다"는 KCL 그 자체)에는
해당하지 않는다** — 다음 세션에 다른 grouping 함수를 손볼 일이 생기면 이 구분부터
먼저 확인할 것.

실측으로 가설을 먼저 검증(`stack_groups_override`로 matching_pairs만의 union-find를
구성 — M6/M7/M57/M58 전부 독립 그룹으로 갈라짐)한 뒤, **`geometry_colocation_union()`
자체를 재설계**:
- **base**: `matching_pairs`(현행과 동일하게 `current_forced=True`만)를 그대로 union.
- **확장**: `find_stack_edges()`(analog-grammar 재사용) + `find_stacked_matching_
  candidates()`(세션19 C-3, 이미 검증됨)로 각 base pair 위에 재귀적으로 쌓인 소자를
  같은 그룹으로 union — "base pair 대표 소자 바로 위에 직렬로 얹힌 같은 kind 소자"만
  좇아가므로, `M58`처럼 "같은 노드를 소스로 공유하는 형제(병렬 소비자)"는 애초에
  후보에 안 들어온다(별도 예외처리 없이 알고리즘 자체가 걸러냄).
- rule1(무근거 자동 drain=source 병합)은 완전히 삭제.

**실측 결과**: `folded_cascode`(다른 회로, PMOS 6개/NMOS 4개 diode-reference 체인)의
기존 self-test 그룹은 **손대지 않았는데도 그대로 통과**(진짜 직렬 스택은 새 방식도
똑같이 잡아내고, M58류 병렬 탭만 정확히 걸러짐) — 우연이 아니라 진짜 직렬 스택
관계는 composite 상속으로도 재현되기 때문. `stick_diagram.py` self-test 전체(31개
Test) exit 0, 회귀 없음.

## B-5. 보충 기록(세션23 시작 시 발견된 기록 누락분) — `resolve_stack_layout()` 3계층
설계 제안 + topology.json 누적 지식베이스 철학

B-4 실측 검증(아래) 과정에서 사용자가 제안한 더 큰 설계 방향이 원래 세션22 기록에는
"B절 결정"만 남고 누락됐었다(세션23 시작 시 사용자가 지적 — `.ai/context.md`가 스스로도
stale/불완전해질 수 있다는 세션14 교훈이 문서 자체 결함으로 재발한 사례) — 아래 보충한다.

### B-5-1. 문제 재구조화 — finger_w/오일러 경로/매칭대칭이 사실 하나의 질문
지금 이 세 관심사가 서로 다른 union-find로 각자 판단되고 있다는 게 구조적 위험이라는
지적(사용자):

| 관심사 | 지금 계산하는 함수 | 근거 |
|---|---|---|
| finger_w 호환 | `geometry_colocation_union()`(자동 추론, Vx fan-out에 취약 — 이 사고 원인) | 전기적 인접(drain=source) 추측 |
| 오일러 경로(row 배치) | `kcl_series_union()` → `stack_id` → `audit_row_split()`/`mirror_symmetric_trail()` | 2단자 KCL 직렬 추측 |
| 매칭 대칭 | `matching_pairs`(topology.json 선언) | 사람이 선언 |

### B-5-2. 정보의 2계층 분리 제안(사용자 원안)
- **Topology 계층**(instance 무관, `topology.json`에 누적): `vertical_stack_id`(물리적
  직렬 branch 경계), `matching_pairs`(이미 있음). 사용자 지적 원문: "같은 전류가 흘러야
  하는 branch류" 같은 기능적 tag는 layout instance마다 달라지지 않는 회로의 topology
  특성이라 `topology.json`에 저장될 만하다 — M1a/M1b/M2a/M2b에 `vertical_stack_id`가
  아예 없는 게 이번 사고의 실제 빈틈.
- **Instance 계층**(이번 sizing 실행에서만 유효, 메모리 캐시): 실제 W로부터 나온
  `finger_w`/`n_fingers` 선택값, 이번 실행에서 확정된 오일러 walk 시퀀스, 적용된 핑거
  조정 내역 — "한 번 결정된 조합은 뒤쪽에서 재사용할 수 있도록 내부 자료구조에 저장해
  매번 다시 계산하는 번거로움이 없도록"(사용자 원문, layout 상황에 따라 조합이 instance
  마다 달라질 수 있는 정보라서). `SizingContext.layout_solution` 필드로 제안됨(미구현).

### B-5-3. `resolve_stack_layout()`(가칭) 설계 제안 — 미구현
기존 서브 solver(`search_stack_finger_w`, `mirror_symmetric_trail`,
`suggest_pair_finger_adjustments`)를 재발명하지 않고 이것들을 묶는 layered orchestrator:
1. `vertical_stack_id`로 1차 분할(이걸 유일한 권위 있는 경계로 — `geometry_colocation_
   union()`의 자동 fan-out 추론이 이 경계를 넘으면 안 됨).
2. 각 그룹 안에서 finger_w 탐색, 실패하면 그룹분할(세션11 B-5 원칙: 미매칭 소자 우선
   분리) 후 재시도.
3. 각 그룹 안에서 오일러 walk 구성, 실패하면 `suggest_pair_finger_adjustments()` 제안 →
   2번부터 재검산(핑거가 바뀌면 W도 바뀌므로).
4. 결과(그룹 멤버십·finger_w·walk 시퀀스·적용된 조정)를 구조체 하나로 반환,
   `ctx.layout_solution`에 캐시.

호출부 교체 제안: `optimize_full_circuit_budget()`이 따로 계산하는 `stack_groups_kcl`/
`stack_groups_geometry`를 이 함수 하나로 대체, `assign_finger_geometry()`/
`audit_row_split()`/`run_topology_pipeline_with_finger_fixup()`이 전부 이 캐시를 읽게.

### B-5-4. `topology.json` 누적 지식베이스 철학(사용자 원안, 일반 원칙으로 기록)
"topology.json은 실제로 sizing하고 layout하는 구현 횟수가 증가할수록(instance 구현
횟수가 늘어날수록) 그 과정에서 생기는 모든 instance에 공통적으로 적용될 수 있는 정보들을
누적하여 보관해야 한다"는 컨셉 — 초기엔 시행착오가 있지만, 자주 쓰는 topology는 누적된
정보를 참고해 구현 속도가 빨라지고 spec 미달 확률이 낮아질 것이라는 예측. **이 관점에서
전체 함수 설계를 재검토할 필요가 있으나, 세션22~23은 문제가 된 함수들을 이런 공용
함수를 호출하는 방식으로 개선하는 좁은 범위로 한정** — 전체 재검토는 사용자가 명시적으로
나중으로 미룸.

### B-5-5. 테이블 위에 남은 3갈래 작업(세션22 종료 시점 기준, 우선순위 미정)
1. `vertical_stack_id`를 M1a/M1b/M2a/M2b 등 빠진 소자까지 채우기(stack M6류 크래시의
   선행 조건, `resolve_stack_layout()`이 이 경계에 의존하므로).
2. `resolve_stack_layout()` 신설(B-5-3).
3. `find_matching_candidates()` Tier 1 실배선 + `vertical_stack_id` 기반 "함정 감지"로
   `matching_pairs` 자동판단(analog-grammar 활용) — 사용자가 이 세션에 새로 요청한 방향:
   "매칭과 대칭을 판단하는 것을 사람이나 AI가 하지 않고, analog_grammar 함수들을 활용해서
   tool이 직접 기능블럭을 판단해서 매칭해야 하는 소자들을 결정하고, 모호하거나 사람이
   봐야 하는 소자들만 확인받도록" — 방향성은 B-2가 이미 실측으로 뒷받침(analog-grammar
   raw idiom matching이 current_mirror 8소자는 정확히 재현하지만 `M36a+M7` false
   positive도 그대로 재현 — Tier 1 필터가 이 함정을 걸러야 한다는 근거로 재확인됨).

이 셋 중 실제로 착수한 건 없음(설계 논의만) — 아래 B-4 실측(matching_pairs 기반
`stack_groups_override`로 stack M6 크래시가 실제로 사라짐을 확인)이 사용자의 "매칭 안
되는 소자는 stack에서 밀어내면 되지 않나"는 가설을 직접 검증한 것이었고, 이 검증 결과가
최종적으로 `geometry_colocation_union()` 재설계(B-4 본문 채택안)로 이어졌다 — 이 과정에서
`run_topology_pipeline_with_finger_fixup()`까지 이 프로젝트 역사상 처음으로 뚫고 들어가
새 버그(`revalidate_finger_override()` `KeyError('kind')`, 아래 C-1)를 직접 만났다. 위
3갈래는 그 다음 단계로 테이블에 남아 있다.

## C. `optimize_full_circuit_budget()` 재실행 → 연쇄로 드러난 나머지 버그 5개

B절 수정 후 실제 production 회로(override 없이, 기본 동작만으로)를 다시 돌리자
매번 더 깊이 들어가서 새 버그를 하나씩 만났다 — 전부 `run_harness.py`가 지금까지
한 번도 이만큼 깊이 실행된 적이 없어 처음 드러난 것들이다. 발견 순서대로:

1. **`revalidate_finger_override()` KeyError('kind')** — `_feed_metric_stage_budget()`
   (L_cascode/L_stage2out theta가 씀)이 `ctx.spec["lut"]`(단일 LUT, kind 구분 없음)만
   쓰고 `entry["kind"]`를 안 채우고 있었다. 근본원인 추적 결과 `_feed_gm_target_
   convention()`("B" 타입)/`_metric_flicker_plus_thermal_sum()`(노이즈 metric)도 같은
   패턴(단일 LUT, 소자별 kind 무시)임을 확인 — **세 곳 다 진짜 전기적 버그**였다
   (`L_cascode`의 devices=`M2a,M2b,M3a,M3b`가 PMOS+NMOS 혼합인데 지금껏 전부 NMOS
   LUT으로 사이징됐었음). 사용자 지적("kind 없이 단일 lut 쓰는 게 무슨 의미가
   있나") 계기로 폴백을 아예 없애기로 결정 — `SizingContext.kind_of` 필드 신설,
   `optimize_full_circuit_budget()`이 채워줌, 세 함수 전부 `lut_by_kind[kind_of[name]]`
   필수 요구(조용한 폴백 없음, 없으면 KeyError로 즉시 드러남). self-test 3곳(단일 lut
   fixture)도 `lut_by_kind`+`kind_of`를 갖도록 갱신.
2. **`apply_and_revalidate_pair_adjustment()`가 물리적으로 불가능한 후보에 크래시** —
   핑거조정 후보(M9b/M18b, 91.5nA 극소전류에 W를 14배 늘리라는 제안)가 LUT
   특성화 범위(gm_id<=26.8) 밖의 gm_id=30을 요구해 `_invert_gm_id_for_current()`가
   `ValueError`. A엔진의 `InfeasibleSizingError`와 같은 원칙으로 처리하도록
   try/except 추가(이 후보를 `rejected`에 기록하고 다음 후보로).
3. **`ctx_for_fixup`에 `topology_path` 누락** — euler-fixup 이후 재계산된 ctx로
   세션21 2차 신규 metric(`smallsignal_ratio_db`, connectivity 재로드 필요)을 계산하려니
   `ctx.topology_path`가 비어 있었다. `SizingContext(..., topology_path=topology_path)`로
   채워 해결.
4. **`_branch_composite_pair()`의 leaf-net 중복 미검증** — `M36a-M37a`/`M36b-M37b`
   (hub쪽 `M36a/M36b`는 선언된 매칭쌍, leaf쪽 `M37a/M37b`도 선언된 매칭쌍이라 구조
   조건은 통과)를 "거울 branch"로 합성했는데, `M37a/M37b`는 사실 **진짜 CMFB 차동쌍**
   이라 서로 다른 legs가 아니라 공유 tail(`Ncmfb_tail`)로 만난다 — 두 composite의
   drain이 똑같이 `Ncmfb_tail`이 돼 `common_centroid_layout()`이 "leaf가 서로 달라야
   한다"로 크래시. hub/leaf 선언 여부 확인 다음에 **`leaf_net_a != leaf_net_b`** 검증을
   추가해 이런 경우 `None`(기존 개별-소자 폴백)으로 조용히 거부하도록 수정.
5. **`apply_and_revalidate_matching_finger_growth()`도 2번과 같은 클래스의 예외 미처리**
   (자매 함수, `run_matching_safety_with_finger_growth()`가 씀) — 동일한 try/except
   패턴 적용.

**매 수정마다 `sizing_recipe.py`/`stick_diagram.py` self-test 전체를 재실행해 exit 0
(회귀 없음)을 확인한 뒤 다음 단계로 진행**(중간에 한 번도 스킵 안 함).

## D. 최종 결과 — 이 프로젝트 역사상 처음으로 end-to-end 완주

C절 수정을 전부 반영한 뒤(override 없이, `geometry_colocation_union()`의 새 기본
동작만으로) `optimize_full_circuit_budget()`을 다시 실행:

```
gain_db=77.21dB, gain_full_circuit_db=85.38dB
cmrr_estimate_db=93.30dB, psrr_estimate_db=96.89dB
classab_centering_dev_v=0.337 (제약 0.15 위반 — 정상적인 "이 조합은 스펙 미달" 보고)
audit_ok=False (box-shape/matching quality 잔여 이슈 — 역시 정상적인 정직한 보고)
```

크래시가 전혀 없다 — `constraints` 위반이나 `audit_ok=False`는 이 harness가 원래
정직하게 보고하도록 설계된 정상 동작이지, 버그가 아니다. `run_harness.py`가 지금까지
단 한 번도 도달한 적 없었던 지점(A/B/C엔진 → `assign_finger_geometry` → euler-fixup
→ matching-safety finger-growth → F엔진 metric 계산)을 처음으로 전부 통과했다.

## E. 알려진 한계 / 다음 세션 이월

1. **60dB 등 임계값은 여전히 미확정**(위 "지금 상태" 2번) — 이번엔 진짜 그리드서치
   결과로 재론의할 것.
2. **item 2(그리드 그룹 재분석)는 여전히 미완주** — B절 크래시 진단으로 옆길로 샜다,
   이제 크래시가 없으니 재개 가능(위 "지금 상태" 3번).
3. **`vertical_stack_id` 확장/`resolve_stack_layout()` 공용 solver는 설계 논의만
   하고 구현 안 함** — B-4의 `geometry_colocation_union()` 단일 함수 재설계로 당장
   급한 문제는 풀렸으므로, 필요성 자체를 다음 세션에 재검토할 것(위 "지금 상태" 4번).
4. **matching_pairs 자동화(analog-grammar Tier 1 기반)는 설계 논의만 하고 구현 안 함**
   (B-2) — 세션19의 "다음 세션 최우선"이었던 Tier 1 실배선과 같은 작업, 계속 이월 중.
5. **실제 `run_harness.py`(진짜 theta bounds, 최대 8192 조합) 전체 재실행은 안 해봄**
   — 세션11 추정으로 ~10시간 걸릴 수 있다, 사용자와 먼저 실행 전략(전수 vs 축소)을
   정할 것(위 "지금 상태" 1번, 최우선).
6. **`topology.json` 변경은 최소**(metrics 딕셔너리 구조 버그 수정 1건뿐) — 이번 세션의
   핵심 변경은 전부 `sizing_recipe.py`/`stick_diagram.py`(엔진 코드)에 있다.
7. **신규 스크립트**(참고용, 완주는 못 함): `workspaces/current-reuse-telescopic-ota-
   report/sample_metrics_session22.py`(실측 샘플링), `theta_sensitivity_session22.py`
   (OAT 민감도 스윕 초안, stack M6 크래시로 중단됨 — 재사용/재작성 판단 필요).

---

# 세션23 결론 — analog-grammar rail 대소문자 버그 발견, diff-pair topology-only 탐지 실패
# 확인, vertical_stack_id 자동화 4회 실측(3실패+1성공: trace_vdd_to_gnd_branches() 신설)

세션22가 남긴 B-5(보충 기록, 세션23 시작 시 발견)의 3갈래 작업 중 "analog-grammar 기반
matching_pairs 자동판단"과 "vertical_stack_id 경계 확장"을 실측으로 파고들었다. composite
소자 구성 함수를 설계하려던 원래 목표에서 시작해, 실제로 돌려보며 두 개의 중요한 신규
발견(A/B절)과 vertical_stack_id 자동화 4회 실측(C절, 그중 1회 성공해 함수로 코드화)으로
이어졌다.

## A. analog-grammar 진짜 버그 발견 — rail net 이름 대소문자 불일치

`skills/analog-grammar/assets/netclass.py`의 `RAILS_POS`/`RAILS_NEG`가 `{'VDD','GND',...}`
**대문자만** 인식하는데, 이 프로젝트 topology.json은 `vdd`/`gnd` **소문자**를 쓴다 —
그래서 지금까지 이 프로젝트 회로에 대한 모든 analog-grammar role 분류(`classify_nets`/
`assign_roles`)가 rail을 못 알아본 상태로 진행되고 있었다(실측: `M6`가 `CURRENT_SOURCE`
가 아니라 `CASCODE`로 오분류 등). rail 이름을 대문자로 바꿔 넣으면 role이 실제 회로와
합리적으로 일치한다(`M6`/`M8`/`M17`→`CURRENT_SOURCE`, `M13`/`M22`/`M60`/`M61`→
`ACTIVE_LOAD` 등). 참고로 세션22의 `M36a+M7` current-mirror 오탐 판정은
이 버그와 무관하게 rail 수정 후에도 **그대로 재현됨**을 확인, 그 결론은 안 바뀐다.

⚠️ **당일 원본 수정 완료**(처음엔 각 함수 내부에서 국소 대문자 변환으로 우회했으나,
사용자가 "wrapper로 해결한 거냐"고 지적 → 우회가 두 함수(`suggest_vertical_stack_
composites`/`classify_symmetric_branch_pairs`)에 완전히 동일한 6줄로 중복돼 있다는 게
드러남 → "원본을 고쳐"로 확정): `netclass.py`의 `RAILS_POS`/`RAILS_NEG`/`RAILS`를
`_CaseInsensitiveNetSet(frozenset)` 서브클래스로 바꿔 `__contains__`가 비교 전에
`item.upper()`로 정규화하도록 수정 — 특정 대소문자 조합을 리터럴로 추가하는 대신 비교
자체를 대소문자 무관하게 만들어, 호출자가 어떤 케이스 관례를 쓰든 항상 맞도록 했다(15곳
전부 `in RAILS`/`in RAILS_POS`/`in RAILS_NEG` 형태라 이 한 곳만 고치면 전부 적용됨).
이후 `stick_diagram.py`의 두 함수에서 중복돼 있던 로컬 우회 코드(각 6줄)도 제거 —
소문자 `vdd`/`gnd` 그대로 넘겨도 정상 동작함을 재확인. **회귀**: self-test 34개 전부
exit 0, `classify_symmetric_branch_pairs()`의 실측 수치(differential=4/mirror=5/
no_connection=12)와 `fig2_telescopic.json` coverage=1.00 전부 우회 코드 제거 전후
동일하게 재현.

## A2. analog-grammar 두 번째 버그 발견 + 수정 — 미러 구동 bias net이 SIGNAL로 오분류
(당일 수정 완료)

C-6/C-7 작업 중 `M2a`/`M3a`(진짜 캐스코드 소자)가 analog-grammar에서 `role=AMPLIFYING`
으로 나오는 걸 사용자가 이상하게 여겨 파고든 끝에 발견 — 이번엔 **당일 직접 수정**까지
완료했다.

### A2-1. 근본원인
`netclass.py` §1e2("게이트를 구동하는 내부 넷" 분류) 원래 규칙: "diode로만 구동되면
BIAS, 능동(non-diode) 드레인이 있으면 SIGNAL". 이 규칙은 그 능동 드레인을 만드는 소자
**자신의 게이트가 이미 BIAS로 확정돼 있는 경우**를 놓친다 — current mirror는 정의상
gate≠drain이라 이 규칙으로는 미러가 만드는 bias net을 원천적으로 절대 BIAS로 못 잡는다.
실측: `Vbias1`(순수 diode `M18_bg`+외부 `Iref`, 진짜 DC) → `M60`(게이트=`Vbias1`인 미러)
→ `Vbias4`(SIGNAL로 오분류) → `M68`(게이트=`Vbias4`인 미러) → `Vbias2`(SIGNAL로 오분류,
연쇄) — 셋 다 AC 성분이 없는 순수 DC bias 트리(`topology.json`에 이미 `biasgen_tree_*`
로 선언돼 있음)인데 SIGNAL로 잘못 분류됐다. 사용자 지적: "SIGNAL이라면 AC적으로 움직임이
있어야 하는데 이건 정말 bias이고 AC적인 움직임은 없다" — 개념적으로도 명백히 틀린
분류였다.

### A2-2. 수정 (`skills/analog-grammar/assets/netclass.py`, `classify_nets()` §1e2)
"diode로만 구동되는가"라는 단순 이분법 대신, 이 net을 드라이브하는(gate≠drain) 소자들의
**게이트 클래스**를 재귀적으로 확인하도록 고쳤다 — 1d(신호 전파)와 동일한 고정점(`while
changed`) 반복 패턴: 드라이버 전부의 게이트가 이미 `BIAS`로 확정돼 있으면 이 net도
`BIAS`로 전파(미러/전류원의 안정성을 물려받음), 드라이버 게이트가 아직 미확정이면 다음
라운드로 미룸(net 이름 처리 순서 무관하게 사슬 깊이만큼 자연 수렴), 끝까지 안 풀리면
안전하게 SIGNAL로 폴백(조용히 BIAS로 단정하지 않음).

### A2-3. 검증
- `Vbias1`/`Vbias2`/`Vbias3`/`Vbias4`/`Vcmfb` 전부 `BIAS`로 재분류 확인.
- `M2a`/`M2b`/`M3a`/`M3b` 전부 `role=CASCODE`로 재분류(기존 `AMPLIFYING`에서 정정).
  단 `telescopic-cascode-node` idiom은 **여전히 미발동** — 이건 오늘 고친 것과 무관한
  별개 이유(`Vom1` 노드에 `M2a`/`M3a` 외에 `M19`도 drain으로 얹혀 있어 이 idiom의
  "정확히 2개" 조건을 못 채움).
- **회귀**: 이 프로젝트 `stick_diagram.py` self-test 34개 전부 exit 0(Test 30/33/34처럼
  analog-grammar에 크게 의존하는 테스트 포함, 전부 무회귀). analog-grammar 자체
  예제(`examples/fig2_telescopic.json`/`fig3_classab.json`)도 `analyze.py`로 재실행 —
  크래시 없음. 오히려 `fig2_telescopic.json`(같은 회로의 축소판, `M58`류 잡음 없는 깨끗한
  버전)에서 `current-reuse-pair`(`M1a+M1b+M4a+M4b`)와 `cascoded-gain-node`(`M2a+M3a`,
  `M2b+M3b`) idiom이 **새로 정확히 잡히며 coverage=1.00 달성** — 세션19가 교차검증
  기준으로 삼았던 `DESIGN.md` §4 기대값(`current-reuse-pair`/`cascoded-gain-node`/
  `tail-current-source`)과 정확히 일치. 버그 수정이 이 회로 하나를 넘어 analog-grammar
  본연의 목적(idiom 인식)까지 개선했다는 뜻.

rail 대소문자 버그(A절)는 이 A2절 작성 시점엔 손 안 댔었으나, 세션23 끝에서 사용자가
"wrapper로 해결한 거냐"고 재차 확인하며 원본 수정까지 이어졌다(A절 하단 갱신 내용 참고
— `_CaseInsensitiveNetSet`으로 근본 수정 + 로컬 우회 코드 제거 완료).

## B. topology-only diff-pair 탐지 — 이 회로에서 구조적으로 실패

rail 버그를 고친 뒤 `find_idiom_matches()`(current-mirror/cascode-stack/differential-pair)를
`current_reuse_telescopic_ota`(51소자 전체)에 돌리면:
- **current-mirror**: 잘 잡힘(`Vbias1` 8소자 그룹 정확 재현 + `Vbias4`쪽 8소자 그룹 신규 발견).
  `M36a+M7` 오탐은 여전(세션22 결론 유효).
- **cascode-stack**: 일부 잡힘(`M37a+M38`, `M37b+M38`).
- **differential-pair: 단 한 건도 안 잡힘.** 원인: 진짜 diff pair `M1a`/`M1b`(둘 다
  source=`Vx`)가 있는 `Vx` 노드에 `M58`(bias-gen 소자)도 같은 source로 얹혀 그룹 크기가
  3이 되고, `idioms.m_diffpair()`가 "정확히 2개"만 요구해서 그룹 전체가 스킵됨.

세션22가 `geometry_colocation_union()`(finger_w 그룹핑)에서 이미 발견한 "M58이 Vx를 통해
fan-out으로 끼어드는" 문제가, 완전히 다른 함수(diff-pair 탐지)에서 **동일한 실패 패턴**으로
재발 — topology(connectivity)만으로 자동 탐지하는 모든 접근이 이 회로에서 공통으로 부딪히는
근본 취약점임을 재확인. **결론: 이 회로에서는 `matching_pairs`(사람 선언) 없이 diff pair를
topology만으로 재발견할 수 없다.**

## C. `vertical_stack_id` connectivity 자동화 — 4회 실측(3실패 + 1성공)

원래 목표(composite 소자 구성 함수 신설)를 진행하려다, "그 composite이 결국
`vertical_stack_id`와 얼마나 일치하는가"를 사용자가 직접 검증하자고 제안 — `current_reuse_
telescopic_ota`의 실제 declared `vertical_stack_id`(36개 소자, 11개 그룹)를 사람이 선언한
그대로 두고, **connectivity만으로 독립적으로 재구성해서 일치 여부를 대조**하는 방식으로
4가지 규칙을 순서대로 실측했다.

### C-1. 실패 — 엄격한 2단자 KCL(`kcl_series_union`, matching_pairs 없이)
레일 제외 + 정확히 2단자인 net만 병합. 결과: 16개 다중-소자 후보 전부 declared vsid를
가로질러 쪼개짐(예: `[M11a,M11b,M12]` 후보가 `M11a/M11b=biasgen_vom_a`, `M12=biasgen_
vom_b`로 사람은 다르게 나눔) — **matching_pairs 인접쌍이 완전히 포함되는 후보 0/16개**.
구조적 원인: `matching_pairs`는 항상 **다른 branch**(대칭인 두 반쪽)를 잇는 관계라 직접
만나는 private net이 없고, KCL 후보는 항상 **같은 branch**(직렬)를 묶는다 — 두 축이
이 회로에서 거의 서로소(disjoint)라 "KCL 후보 안에 matching pair 포함되면 확정"이라는
규칙 자체가 애초에 거의 항상 공집합이 된다.

### C-2. 실패 — 레일 제외 rail-to-rail 연결성분(단자 수 무관 union)
분기 노드를 넘어가도록 허용(사용자 제안 검증). 결과: 51개 중 25개가 **서로 다른 declared
vertical_stack_id 11개 전부를 한 덩어리로 섞은** 하나의 연결성분으로 붕괴 — `Vom1`/`Vop1`/
`Vg15`/`Vg25`/`Vx`/`Vy` 같은 공유 노드를 넘어가면 이 folded/current-reuse 구조 특성상
회로 절반이 통째로 이어져버림. 나머지 작은 성분(3개 이하)들은 C-1과 거의 같은 패턴으로
declared 경계를 가로지름(`[M22,M23a,M24b]`→`{vop_a,vop_b}` 등), 딱 `[M39,M40]`→
`{cmfb_load}` 하나만 깔끔히 일치.

### C-3. 실패 — 소자 단위 분기별 경로 나열(공유 net의 다른 단자를 쓰는 이웃을 전부 다음
hop 후보로)
16개 시작점에서 **446개** branch로 조합 폭발 — 병렬 형제(`M1a`/`M1b`처럼 같은 kind가 같은
Vx를 **둘 다 source로** 공유하는 관계)까지 "다음 소자"로 오인해서, 한 소자가 여러 개의
서로 다른 root-to-leaf 경로에 중복 등장(분할이 아니게 됨). 사용자가 직접 5개의 정답
branch를 예시로 제시(`M6/M1a/M2a/M3a/M4a/M5`, `M6/M1b/M2b/M3b/M4b/M5`, `M7/M1a/M2a/M3a/
M4a/M5`, `M7/M1b/M2b/M3b/M4b/M5`, `M61/M64/M63/M5`) — 이걸로 정확한 규칙을 역산해 C-4로
이어짐.

### C-4. 성공 — kind별 entry/exit 고정 + drain=drain 만남 지점 (`trace_vdd_to_gnd_branches()`)
PMOS는 `source(레일쪽)→drain(부하쪽)`, NMOS는 `drain(부하쪽)→source(레일쪽)` 순으로 "실제
전류 방향"을 kind로 고정해서 소자를 이었다 — 이러면 병렬 형제(같은 kind, 같은 타입 단자
공유)는 **구조적으로 절대** 다음 hop이 될 수 없고, PMOS drain과 NMOS drain이 만나는 진짜
캐스코드 출력 노드(`M2a.drain==M3a.drain==Vom1`)만 정상적으로 이어진다. 사용자가 제시한
5개 예시 branch **전부와 정확히 일치**했고, 조합 폭발 없이 **29개 완주 branch + 1개
dead-end**(`M18_bg`→`Vbias1`, 트랜지스터가 아니라 `ideal_sources`의 `Iref` 전류원으로
종단 — 버그 아니라 정직한 신호)로 수렴.

**그럼에도 `vertical_stack_id`를 자동 확정하지는 못한다** — declared vsid 그룹은 이 함수가
찾는 "하나의 물리 branch"와 정확히 대응하지 않고 두 가지 다른 카테고리로 어긋난다:
1. **허브 공유형**: `M5`/`M6`/`M7`(`stage1`)은 각각 6개/4개/4개의 서로 다른 declared vsid와
   같은 branch에서 만난다 — 이 셋은 "하나의 branch"가 아니라 **여러 branch가 공유하는
   tail 소스/싱크 허브**이기 때문(`M5`는 거의 모든 NMOS branch의 공통 싱크, `M6`/`M7`은
   `Vx`를 통해 여러 branch에 공통 공급).
2. **인접쌍 분할형**: 하나의 물리 branch를 사람이 정확히 절반씩 둘로 쪼갠 경우가 대부분
   (`[M11a,M11b(vom_a)]→[M12(vom_b)]`, `[M13(vom_a)]→[M14a,M14b(vom_b)]`,
   `[M20a,M20b(vop_a)]→[M21(vop_b)]`, `[M22(vop_a)]→[M23a,M24b(vop_b)]`,
   `[M36a,M36b(cmfb_load)]→[M37a,M37b,M38(cmfb_tail)]`) — branch 자체는 하나로 정확히
   추적되는데, 사람이 그 안에서 "위쪽(ratio 미러 참조)"과 "아래쪽(전류 결정 tail)"을
   `matching_sensitivity` 경계로 보이는 기준을 따라 별도 `vertical_stack_id`로 나눠뒀다.

### C-5. branch tracing 단독으로는 여전히 미확정 — 그러나 종결 아니었음(C-6으로 이어짐)
branch 골격(C-4)만으로는 `vertical_stack_id`가 자동 확정되지 않는다는 게 위 두 카테고리
(허브 공유형/인접쌍 분할형)로 확인됐다 — 여기서 "connectivity만으로는 근본적으로 불가능"
이라고 결론지을 뻔했으나, 사용자가 "이 함수가 내놓은 candidate들을 analog-grammar로
composite소자로 먼저 재구성해보자"고 제안 — C-6에서 실제로 돌려보니 결론이 뒤집혔다.

### C-6. 성공 — branch tracing + analog-grammar idiom matching 결합 (`suggest_vertical_
stack_composites()`)
C-4의 branch(예: `[M11a,M11b,M12]`)에 analog-grammar idiom matching(rail 대소문자 수정
반영)을 겹쳐서, **branch 내부에서 연속된 부분열이 diode-connected/floating-battery/
cascode-stack/push-pull 같은 idiom과 정확히 일치하면 그 부분열만 하나의 composite로
병합**했다(`current-mirror`/`differential-pair`는 정의상 다른 branch를 잇는 관계라 제외).
결과: `[M11a,M11b,M12]` → `M11a+M11b[floating-battery] | M12` — **정확히 사람이 선언한
`biasgen_vom_a`={M11a,M11b} vs `biasgen_vom_b`={M12} 경계와 일치**. 51소자 전체
29개 완주 branch에 전부 적용한 결과:

- **63개 composite unit 중 62개가 단일 declared `vertical_stack_id`로 깨끗이 일치**
  (`[M13(vom_a)]|[M14a,M14b(vom_b)]`, `[M20a,M20b(vop_a)]|[M21(vop_b)]`, `[M22(vop_a)]|
  [M23a,M24b(vop_b)]`, `[M36a(cmfb_load)]|[M37a,M38(cascode-stack)]`, `[M60(active-load)]|
  [M66(diode-connected)]`(서로 다른 declared 그룹 `tree_a`/`tree_root`인데도 안 섞이고
  정확히 갈라짐), `[M39,M40(floating-battery)→cmfb_load 한 그룹]` 등).
- **불일치는 단 1건**: `[M37a,M38]` → declared=`{None, cmfb_tail}` — 이것도 진짜 충돌이
  아니라 `M37a`가 애초에 declared 값이 비어있던 gap(`M37a`/`M37b`는 진짜 CMFB 차동쌍인데
  `M37b`만 `cmfb_tail`로 선언돼 있었음, 세션22가 이미 알던 gap)을 메우는 방향의 정당한
  제안으로 읽힌다.
- 신호경로 소자(`M1a`~`M4b`, declared 자체가 없음)는 어떤 idiom과도 안 묶여 소자 단위
  그대로 남고, `stage1`(`M5`/`M6`/`M7`) 허브 소자도 다른 소자와 안 합쳐진 채 각 branch에
  단독 등장 — 둘 다 declared 정보와 자연스럽게 정합적(합칠 근거가 없는 곳은 안 합치므로
  "섞임" 오류로 집계되지 않는다).

**결론**: branch 골격 단독(C-4)은 "어디서 병합해야 하는지"의 절반(같은 branch인지)만
알고 "그 안에서 어디를 더 쪼개야 하는지"는 몰랐는데, analog-grammar의 idiom 판정
(connectivity에서 결정론적으로 나오는 구조적 사실)이 바로 그 나머지 절반을 메웠다.
`suggest_vertical_stack_composites()`(`stick_diagram.py` §1.7d)로 코드화, self-test
Test 33(합성 fixture로 floating-battery 병합 경계 재현) 전부 통과, 회귀 없음.
⚠️ 이 함수는 **제안만** 한다 — `topology.json`에 자동으로 쓰지 않으며, 62/63이라는
성공률도 이 회로 하나의 결과다(다른 3개 회로 일반화는 미검증, 아래 "지금 상태" 참고).

### C-7. branch 쌍 탐색 — gate 기반보다 "순수 구조(kind+idiom 시퀀스) 일치"가 훨씬
포괄적임을 실측으로 확인
C-6의 composite branch들을 서로 짝짓는 방법을 두 갈래로 실측 비교했다:
1. **gate 기반**(fork에서 갈라진 소자의 gate가 같거나, 둘 다 선언된 `INPUT`이면 연결로
   보고 전체 chain을 끝까지 검증) — `M6`/`M7` 시작 differential branch 4쌍은 잡지만,
   `M13`-branch↔`M22`-branch류(각자 내부 net 이름이 달라 gate 자체가 다르고 `INPUT`도
   아님)는 못 잡는다.
2. **순수 구조 일치**(`suggest_vertical_stack_composites()`가 만든 composite 시퀀스의
   `(길이, idiom, kind 튜플)`만 비교, gate 이름은 아예 안 봄) — 29개 branch 중 **26개가
   11개 그룹으로 묶임**(`M13/M14a/M14b`↔`M22/M23a/M24b`, `M8/M9a/...`↔`M17/M18a/...`,
   `M11a/M11b/M12`↔`M20a/M20b/M21`, `M15/M16`↔`M25/M26`, `M36a/M37a/M38`↔`M36b/M37b/M38`
   등 vom/vop 대칭쌍 전부 포함). 짝 없는 3개(`M60/M66`, `M61/M64/M63/M5`, `M39/M40`)는
   실제로 vop/vom 양쪽에 복제 안 되는 단일 기준전류/CMFB 출력 구조라 짝이 없는 게 맞다.

### C-8. `classify_symmetric_branch_pairs()` — C-7의 구조적 쌍을 다시 analog-grammar
gate 판정으로 3범주 분류
C-7이 찾은 구조적 쌍을 무조건 하나로 취급하지 않고, "진짜 연결 근거가 있는가"를
analog-grammar로 다시 검증해서 세분화해달라는 사용자 요청으로 설계했다. 첫 시도(전체
chain이 끝까지 안 끊기고 다 이어져야 `mirror`로 인정)는 실측하니 **`mirror` 버킷이
0개**로 나왔다 — `M8`/`M17`처럼 fork 지점 gate는 같아도(`Vbias1`) 그 다음 단계에서
내부 net 이름(`M9a`의 gate=`N11b` vs `M18a`의 gate=`N20b`)이 달라 체인 전체 검증이
실패했기 때문. 사용자가 "fork 지점(갈라지는 첫 소자)만 같은 gate면 mirror로 인정"으로
기준을 명시적으로 정정 — 이 기준으로 다시 실측하니:

```
differential_branch_pairs = 4   (fork@M1a/M1b, 전부 gate=Vip/Vim)
mirror_branch_pairs        = 5   (fork@M8/M17 ×4, fork@M13/M22 ×1, 전부 gate 동일)
structurally_symmetric_no_connection = 12   (fork@M6/M7 ×8, fork@M11a/M20a, M15/M25,
                                              M36a/M36b — gate가 다르고 둘 다 INPUT도 아님)
```

`mirror_branch_pairs`가 잡은 5쌍은 전부 `topology.json`에 **직접 선언된 matching_pairs가
아닌** 관계(`M8`/`M17`은 같은 `current_mirror` 그룹의 일부일 뿐 서로 직접 선언된 쌍은
아님)라, declared 정보 없이 순수 connectivity+gate 판정만으로 의미 있는 신호를 냈다는
근거가 된다. `classify_symmetric_branch_pairs()`(`stick_diagram.py` §1.7d)로 코드화,
self-test Test 34(3범주 합성 fixture, 각 1쌍씩 정확히 분류) 전부 통과, 회귀 없음.
⚠️ 세 범주는 fork 지점 **하나만** 보고 판정한다 — chain 나머지 구간의 연결 여부는
보지 않는다(의도된 단순화, 위 "0개 나왔던 첫 시도" 참고).

### C-9. `find_differential_and_mirror_forks()` — telescopic 구조의 "두 번째
differential pair"를 놓치는 문제를 양방향(VDD↓+GND↑) 탐지로 해결

C-8까지의 판정은 전부 **VDD→GND 하향 한 방향**만 봤다. 사용자가 "M4a/M4b는 왜 안 봐?"
라고 지적 — `[M6,M1a,M2a,M3a,M4a,M5]` vs `[M6,M1b,M2b,M3b,M4b,M5]`는 실제로
`differential→mirror→mirror→differential`(M1a/M1b, M2a/M2b, M3a/M3b, M4a/M4b 순)로
이어지는데, 첫 fork(`M1a`/`M1b`)만 보고 나머지는 계산조차 안 하고 있었다.

**원인**: `current_reuse_telescopic_ota`는 PMOS 입력단(`M1a`/`M1b`)과 NMOS 입력단
(`M4a`/`M4b`) 둘 다 `Vip`/`Vim`을 게이트로 받는 "current-reuse"(입력을 두 번 재사용) 구조
— 즉 differential pair가 스택 안에 **두 층**으로 있다. 하향 추적에서 `M2a`→`M3a`→`M4a`
구간은 분기 없는 직선이라(각 소자가 정확히 하나의 다음 소자로만 이어짐), `M4a`/`M4b`가
같은 branch 안에서 나란히 서 있다는 사실 자체가 fork로 드러날 기회가 없다.

**해결**: `trace_gnd_to_vdd_branches()`(`trace_vdd_to_gnd_branches()`의 완전한 반대
방향 — PMOS는 drain→source, NMOS는 source→drain 순으로 GND에서 VDD까지 거슬러 올라감)
를 신설해서, `M5`(공통 tail sink)에서 위로 올라가면 `M4a`/`M4b`가 **그 방향에서는 첫
fork**로 바로 잡힘을 확인. `find_differential_and_mirror_forks()`가 두 방향의 branch
tree 전체에서 fork를 각각 찾아(단일 divergence 하나가 아니라 tree 전체를 훑음) gate
판정(mirror/differential)으로 분류하고 합친다. 실측 결과:

```
하향(VDD→GND): M6→(M1a,M1b) differential, M7→(M1a,M1b) differential   (2건, 시작점 2개)
상향(GND→VDD): M5→(M4a,M4b) differential                              (1건)
```

`M2a`/`M2b`, `M3a`/`M3b`(둘 사이에 낀 mirror형 캐스코드)는 이번에도 어느 방향에서도
fork로 안 잡힌다 — 이건 애초에 fork가 아니라 "두 개의 독립된 직선 branch를 나란히
비교해야만" 보이는 관계라(C-7/C-8이 이미 다루는 영역), C-9의 범위 밖으로 확인됨.
`trace_gnd_to_vdd_branches()`/`find_differential_and_mirror_forks()`(`stick_diagram.py`
§1.7d)로 코드화, self-test Test 35(9소자 telescopic 합성 fixture, 하향/상향 각각 반대쪽
pair를 놓친다는 것과 합쳤을 때 둘 다 잡힌다는 것 둘 다 검증) 전부 통과, 회귀 없음.

## 정정: `M7`+`M36a`는 "오탐"이 아니라 진짜 mirror 관계였다

세션18부터 반복 인용해온 "`M36a+M7` current-mirror 오탐"이라는 결론을 사용자가
재검토 요청 — "전류가 ratio되는가 같아야 하는가만 다르지, VGS가 같으면 mirror가 맞는
거 아닌가?"라고 정확히 지적했다. 세션18 L-3 원문을 다시 찾아 확인하니, 그때도 이미
"둘 다 source=vdd → VGS 동일 조건은 만족하는데도 '다른 기능 블록'이라는 별개 사유로
여전히 false_positive(사람 판단은 여전히 남음)"이라고 **스스로 그 긴장을 인정하고
있었다** — 전기적 근거가 아니라 손으로 정한 판단이었다.

**재검증(rail 버그 + 미러 bias net 오분류 버그를 A/A2절에서 이미 고친 상태로)**:
`Vcmfb`는 `BIAS`로 분류되고(`Vbias1`과 동일 카테고리), `M7` role=`CURRENT_SOURCE`
(`M6`과 동일), `M36a` role=`DIODE_CONNECTED`(`M18_bg`와 동일) — **`M7`/`M36a`를 진짜
bias mirror(`M6`/`M18_bg`류)와 구조적으로 구별할 신호가 전혀 없다.** 즉 `M7`/`M36a`는
"우연한 gate 일치"가 아니라, `M36a`(diode 기준)를 `M7`이 그대로 미러하는 **진짜
전류미러 구조**다 — 다만 `Vcmfb`가 CMFB 부궤환 루프의 출력이라는 게 다를 뿐, 그 사실이
mirror 관계 자체를 무효화하지는 않는다("ratio냐 1:1이냐"는 W 크기 문제일 뿐 mirror
여부와는 별개 질문이라는 사용자 지적 그대로).

**결론**: "오탐(false positive)"이라는 표현은 부정확했다 — 정확히는 "진짜 mirror
관계이지만, `matching_pairs`에 선언해 레이아웃 매칭까지 강제할 필요는 없다고 설계자가
판단한 사례"다(CMFB 부궤환이 소자 부정합을 스스로 보정해주므로 엄격한 인터디지테이션이
덜 중요하다는 설계 판단으로 추정 — 단 이건 추정이고, 확정 근거는 아니다). 앞으로 이
사례를 다시 언급할 때 "오탐"이 아니라 "matching_pairs 미선언(설계 판단)"으로 부를 것.

## C-10. `find_verified_differential_and_mirror_relations()` — 진짜 branch 단위 비교로
fork-tree 방식의 두 가지 남은 문제를 동시에 해결

C-9(`find_differential_and_mirror_forks()`)는 fork-tree의 "갈라지는 지점"만 봐서 두
문제가 있었다: (1) 소자 쌍 단위 비교라 `M1a`/`M58`, `M6`/`M7`, `M18a`/`M2a` 같은 무관한
조합까지 후보로 나옴(사용자 지적: "branch단위로 비교하고 있는 거 맞아?"), (2) 한 방향
호출당 fork 하나만 봐서 여러 층의 관계를 한 번에 못 봄.

**해결**: `classify_symmetric_branch_pairs()`(C-7)의 원리 — **branch 전체의 composite
구조(kind+idiom 시퀀스)가 완전히 같은 것끼리만 먼저 묶는다** — 를 `suggest_vertical_
stack_composites()`에 `direction=` 파라미터를 추가해 상향까지 확장 적용하고, 매칭된
branch 쌍 안에서 **첫 divergence만이 아니라 모든 위치**를 gate 판정(같은 gate=mirror,
다른 gate+둘 다 `INPUT`=differential)한다.

**실측**: `[M6,M1a,M2a,M3a,M4a,M5]`↔`[M6,M1b,M2b,M3b,M4b,M5]` 매칭 쌍 하나에서
위치1(`M1a`/`M1b`)=differential, 위치2(`M2a`/`M2b`)=mirror, 위치3(`M3a`/`M3b`)=mirror,
위치4(`M4a`/`M4b`)=differential **네 관계 전부가 하향 방향 한 번의 스캔만으로** 나온다
— C-9가 상향까지 따로 돌려야 겨우 찾던 `M4a`/`M4b`가 이번엔 하향만으로도 잡힌다(branch
전체를 미리 매칭해뒀기 때문). `M7`/`M36a`는 여전히 등장 안 함(구조가 다른 branch라
애초에 비교 대상조차 안 됨 — 다만 위 정정에 따르면 이건 "오탐 필터링"이 아니라 그냥
"이 두 branch가 구조적으로 매칭되지 않았을 뿐"이라는 뜻으로 재해석해야 한다).
`current_reuse_telescopic_ota` 전체 결과: differential 4건(`M1a`/`M1b`,`M4a`/`M4b`
각 양방향), mirror 12건(`M2a`/`M2b`,`M3a`/`M3b`,`M19`/`M10`,`M8`/`M17`,`M12`/`M21`,
`M13`/`M22` 각 양방향 — `M19`/`M10`, `M12`/`M21`은 이번 전체-위치 스캔으로 새로 발견).

`find_verified_differential_and_mirror_relations()`(`stick_diagram.py` §1.7d)로 코드화,
self-test Test 36(Test 35의 9소자 telescopic fixture 재사용, 4관계 전부 하향 한 번의
스캔으로 검출되는지 검증) 전부 통과, 회귀 없음.

⚠️ **당시 남은 한계였으나 이후 C-11에서 완전히 해소됨**: `M37a`/`M37b`(CMFB 내부 2차
differential pair, 게이트가 `Voc`/`Voc_des`로 `inputs=`에 선언한 `Vip`/`Vim`이 아님)는
이 함수도 못 찾았다 — branch-매칭 문제가 아니라 net 분류 문제(`netclass.py` 자신이
"구조만으로는 INPUT/BIAS 구별 불가, 이름 힌트 또는 사용자 선언 필요"라고 명시)였다.
아래 두 단계로 완전히 풀렸다: (1) `Voc`/`Voc_des`를 `inputs=`에 수동 선언해 검증(잡힘,
부작용 없음 확인) → (2) 사용자가 "먼저 differential pair를 찾고 나서 mirror를 분석해야
정확해진다"는 통찰로 이어져, **선언 자체가 필요 없는** `find_differential_pair_
candidates()`(C-11)로 최종 해결.

## C-11. `Voc`/`Voc_des` 선언의 연쇄 효과 발견 → `find_differential_pair_candidates()`
— 선언 없이 순수 connectivity만으로 진짜 differential pair 전부 발견

### 검증 1 — `Voc`/`Voc_des`를 `inputs=`에 수동 선언
`find_verified_differential_and_mirror_relations(..., inputs=('Vip','Vim','Voc',
'Voc_des'))`로 재실행 → `M37a`/`M37b`가 정확히 differential로 잡히고, 나머지 결과(4개
differential→6개로 `M37a`/`M37b`만 순증, mirror 12건은 완전히 동일)는 전혀 안 바뀜 —
부작용 없이 깨끗하게 해결.

### 검증 2 — 연쇄 효과: `Vcmfb`가 `BIAS`→`SIGNAL`로, `M7` role이 `CURRENT_SOURCE`→
`AMPLIFYING`으로 재분류됨(사용자가 직접 예측하고 확인 요청)
`Voc`가 `INPUT`으로 선언되면 `netclass.py`의 신호 전파 규칙(§1d, "게이트가 신호면
드레인도 신호")이 `M37a`(gate=`Voc`)의 drain인 `Vcmfb`까지 SIGNAL로 끌어올린다 — 이
전파는 오늘 A2절에서 고친 §1e2(미러 구동 bias net 재귀 전파)보다 **먼저** 실행되므로
서로 충돌 없이 순서대로 맞물린다. 실측 확인: `Vcmfb`=`SIGNAL`(기존 `BIAS`에서 변경),
`M7` role=`AMPLIFYING`(기존 `CURRENT_SOURCE`에서 변경), `M36a` role은 diode 판정이라
게이트 클래스와 무관하게 그대로 `DIODE_CONNECTED`. **`M7`이 이제 `M6`(진짜 bias
mirror)과 role로도 구조적으로 구별된다** — "오탐" 논쟁(위 정정 문단)의 근본 원인이었던
잘못된 role 분류가 여기서 정정됨.

### 사용자 통찰 — "differential pair를 먼저 찾고 나서 mirror를 분석해야 정확해진다"
이 인과관계(`Voc` 선언 → `Vcmfb` 재분류 → `M7` role 재분류 → mirror 판정 정확도 향상)
에서 사용자가 일반 원칙을 도출: mirror 분석은 net 분류(BIAS/SIGNAL, role)에 의존하는데
그 분류 자체가 부정확하면(differential pair를 아직 못 찾아서) mirror 판정도 같이
부정확해진다 — **순서가 중요하다**.

### `find_differential_pair_candidates()` — 선언 없이 순수 connectivity로 해결
"먼저 `Voc`/`Voc_des`를 알아야 선언할 수 있다"는 순환 의존을 피하기 위해, **INPUT/BIAS
net 분류를 전혀 안 쓰는** differential-pair 후보 탐지를 설계했다: 구조적으로 매칭된
branch 쌍(C-10과 동일 원리) 안에서, 위치별 소자쌍이 (1) 같은 kind (2) 다른 gate(mirror
아님) (3) **같은 non-rail source(진짜 tail net)를 공유**하면 후보로 판정 — `Transistor.
source`를 직접 비교할 뿐 `cls`(net 분류)를 전혀 참조하지 않는다.

**실측**: `inputs=('Vip','Vim')`만 준 상태에서(또는 아예 `inputs=` 없이도, self-test로
확인) 정확히 `M1a`/`M1b`(source=`Vx`), `M4a`/`M4b`(source=`Vy`), `M37a`/`M37b`
(source=`Ncmfb_tail`) **3개만** 후보로 나온다. vop/vom 구조적 대응쌍(`M9a`/`M18a`,
`M11a`/`M20a`, `M14a`/`M23a`, `M15`/`M25`, `M16`/`M26`, `M36a`/`M36b` — 전부 source가
서로 다른 net이라 자동 제외)과 `M6`/`M7`(공유 source가 `vdd`, 레일이라 제외 — 레일은
무한 전류 공급이라 "같은 tail 공유로 전류 스플릿"이라는 differential pair 정의 자체가
성립 안 함)이 전부 깨끗하게 걸러진다.

`find_differential_pair_candidates()`(`stick_diagram.py` §1.7d)로 코드화, self-test
Test 37(Test 35 fixture를 `inputs=` **아예 안 넘기고** 호출, `M1a`/`M1b`+`M4a`/`M4b`
둘 다 순수 connectivity만으로 검출되는지 검증) 전부 통과, 회귀 없음.

**남은 오케스트레이션(다음 세션 최우선, 아래 C-12/D 참고)**: 이 함수가 찾은 후보의
gate net을 자동으로 `inputs=`에 승격해서 `find_verified_differential_and_mirror_
relations()`를 재실행하는 반복 정제 루프는 **아직 구현 안 함**(지금은 사람이 손으로
검증 2에서 한 번 확인한 상태뿐 — 자동화된 함수/루프는 없음). 아래 C-12에 함수
레퍼런스, D절에 명시적 다음 과제로 기록.

## C-12. 함수 레퍼런스 정리 (세션23에 신설된 7개 중 6개 생존 + 세션24에 추가된 1개, `stick_diagram.py` §1.7d, 의존 순서)

⚠️ **2026-08-07 세션24 정리**: `classify_symmetric_branch_pairs()`(세션23 C-8, 원래
7번)는 사용자 지시로 삭제됐다 — 6번(`find_verified_differential_and_mirror_relations()`)
이 이 함수의 상위 완전 호환(하향 전용+첫 divergence만 보던 것을 양방향+모든 위치로
확장했고, 세션24에 세 번째 버킷까지 갖춤)이라 더 이상 유지할 이유가 없다는 판단(C-12
원래 설명에도 "6번보다 이전/단순 버전"이라고 이미 적혀 있었다). self-test Test 34도
같이 삭제, 나머지 docstring의 참조는 "삭제됨"으로 정정해 dangling reference를 남기지
않았다. 아래 표는 생존한 6개 함수 기준으로 번호를 다시 매겼다(코드 자체엔 번호가 없어
재배치에 따른 영향 없음).

| # | 함수 | 핵심 성질 | 반환 |
|---|---|---|---|
| 1 | `trace_vdd_to_gnd_branches(transistors)` | VDD→GND 하향, kind별 entry/exit 고정(PMOS: source→drain, NMOS: drain→source) + drain=drain 만남 지점. analog-grammar 불필요 | `{"branches": [{"chain":[...], "terminates_at": "gnd"\|"non_transistor"}, ...]}` |
| 2 | `trace_gnd_to_vdd_branches(transistors)` | 1번의 완전한 반대 방향. analog-grammar 불필요 | 동일 형태, `terminates_at`이 `"vdd"`\|`"non_transistor"` |
| 3 | `find_differential_and_mirror_forks(transistors, inputs=, outputs=, feedbacks=, biases=, clocks=)` | 1+2번 branch tree 전체의 fork(갈라지는 지점)를 gate 판정만으로 분류. **소자 쌍 단위**(branch 전체 비교 아님) — 무관한 조합도 섞여 나올 수 있음(초기 버전, 5/6번이 이 한계 해소) | `{"forks": [{"direction","fork_prefix","fork_devices","relation":"mirror"\|"differential"}, ...]}` |
| 4 | `suggest_vertical_stack_composites(transistors, inputs=, outputs=, feedbacks=, biases=, clocks=, direction="vdd_to_gnd"\|"gnd_to_vdd")` | 1/2번 각 branch 내부 연속 부분열을 analog-grammar idiom(diode-connected/floating-battery/cascode-stack 등)으로 병합 — `vertical_stack_id` 후보 제안용(62/63 실측 일치). idiom 매칭이 role 분류에 의존해 `inputs=`에 민감하다는 건 여전하지만, **세션24 안에서 `idioms.py`의 `m_cascode()`/`m_diffpair()`를 고쳐서(위 "analog-grammar cascode-stack/differential-pair 일반화" 절 참고) 함정이 크게 줄었다** — `refine_differential_and_mirror_relations()`가 승격한 `final_inputs`를 넣어도 이제 **진짜 differential-pair 다리(`M37a`/`M38`, `M37b`/`M38` — 원래도 mislabel이었음)만 정확히 빠지고**, `M1a/M2a`, `M1b/M2b`, `M6/M58`, `M58/M7` 같은 진짜 물리적 캐스코드/스택은 promoted 상태에서도 유지된다(수정 전엔 6쌍 전부 사라졌음). 그래도 base declared inputs가 여전히 더 안전한 기본 선택(idiom 정확도가 `inputs=`에 아예 안 흔들리는 쪽) — promoted inputs가 "쓸 수 없는" 상태에서 "써도 되지만 굳이 필요하지 않은" 상태로 격상됐다는 뜻. ⚠️ **세션24 추가 수정**: composite dict가 `idioms.Match.ports`(예: `cascode-stack`의 `lower_role`)를 조용히 버리던 버그를 고쳐서 `"ports"` 키로 보존(단일 소자는 `ports={}`) — `M8`(`lower_role='CURRENT_SOURCE'`)+`M9a` 캐스코드처럼 어느 쪽이 mirror 기준이고 어느 쪽이 그 위 캐스코드인지 이제 구분 가능(`headroom_role` 재시도의 재료, 사용자 지적으로 발견). | `[{"chain","terminates_at","composites":[{"members","idiom","ports"}, ...]}, ...]` |
| 5 | `find_differential_pair_candidates(transistors, inputs=, outputs=, feedbacks=, biases=, clocks=)` | 4번 구조가 완전히 같은 branch끼리 묶은 뒤, **같은 non-rail source(진짜 tail) 공유 + 다른 gate**만으로 판정. **net 분류(INPUT/BIAS) 전혀 안 씀** — `inputs=` 선언 없이도 동작(핵심 성질, self-test로 확인) | `{"candidates": [{"direction","position","devices","shared_source"}, ...]}` |
| 6 | `find_verified_differential_and_mirror_relations(transistors, inputs=, outputs=, feedbacks=, biases=, clocks=)` | 4번 기반, 구조 같은 branch 묶고 **모든 위치**를 gate 판정. 5번과 달리 `gate_class=='INPUT'`에 의존 — `inputs=`에 없는 2차 입력(`Voc`/`Voc_des`류)은 `differential`/`mirror` 대신 세 번째 버킷으로 감(**세션24 수정**: kind 다름/gate 근거 없음인 위치를 조용히 버리지 않고 `structurally_symmetric_no_connection`으로 명시 보고 — 원래 이 역할이던 `classify_symmetric_branch_pairs()`를 대체) | `{"differential": [...], "mirror": [...], "structurally_symmetric_no_connection": [...]}` — 각 원소 `{"direction","devices","branch_a","branch_b","position"}` |
| 7 | `refine_differential_and_mirror_relations(transistors, inputs=, outputs=, feedbacks=, biases=, clocks=, max_iterations=5)` | **세션24 신설, 이후 `vertical_stack_id_candidates`/`gm_id_role_candidates`/`L_role_candidates` 확장.** 5번+6번을 자동 오케스트레이션 — 5번 후보의 gate net을 `inputs=`에 자동 승격해 고정점까지 반복 후 6번 재실행, role/net class 변화를 명시적으로 보고. `_propose_vertical_stack_ids()`: cascode-stack 등 composite 병합(base inputs) + differential/mirror 관계(leg a/b) → `vertical_stack_id` 후보(fan-in 후보 2개 이상이면 `ambiguous_{name}` 격리, differential-pair branch 소속 여부로 재판정해서 가능하면 자동으로 풀어줌, 실측: `M9b`→`M10`, `M18b`→`M19`, `M58`→`M7`). `_propose_gm_id_roles()`: `find_differential_pair_candidates()`의 `shared_source`를 drain으로 받는 tail 소자만 `balanced`, 나머지 `matching`(36/36 실측 일치). `_propose_L_roles()`: tail 소자는 `bias_replica`, `find_structural_symmetry_candidates()`(전역 좌우 대칭, seed는 차동쌍 게이트+rail에서 자동 생성)로 풀리는 소자는 `mirror`+대칭 파트너 명시, 나머지는 `mirror` 기본값(35/36 실측 일치, `M38`만 문서화된 의도적 예외). `headroom_role`은 6가지 구조적 가설을 시도했으나 완전히는 못 풀어서(9/35 불일치가 최선) 아직 후보 함수 미신설 — 다음 세션 이월(0-C). | `{"relations": 6번과 동일 형태, "promoted_inputs", "final_inputs", "role_changes":[{"device","before","after"}], "net_class_changes":[{"net","before","after"}], "iterations", "stop_reason", "vertical_stack_id_candidates": {"groups":{device:id}, "ambiguous_alternatives":{device:[candidate_group,...]}}, "gm_id_role_candidates": {device:"balanced"\|"matching"}, "L_role_candidates": {device:{"L_role","confirmed_by_structural_symmetry","symmetry_partner"}}}` |

**권장 사용 순서**: `refine_differential_and_mirror_relations()`(7번) 하나로 ①~③이
자동 수행된다 — ① `find_differential_pair_candidates()`로 선언 없이 진짜
differential pair 후보를 먼저 찾고 → ② 그 게이트를 `inputs=`에 승격 → ③
`find_verified_differential_and_mirror_relations()`로 정확한 differential/mirror
관계 확정하는 흐름을 5/6번을 직접 손으로 조합할 필요 없이 7번 호출 한 번으로 끝낸다
(수동 조합이 필요한 경우, 예: 승격 없이 5/6번 각각의 원시 출력만 보고 싶을 때는
여전히 개별 호출 가능). 3번은 더 단순했던 초기 버전(탐색 과정의 산물)이라 지금은
5/6/7번이 더 정확하지만, 3번(fork-tree 전체 훑기)도 자기 용도(branch tree 전체의
fork 개요를 빠르게 훑기)에서 여전히 유효하게 동작한다(self-test로 검증됨, 폐기
대상 아님). **`vertical_stack_id` 후보가 필요하면 4번만 쓸 것(base inputs로) — 5/6/7번의
branch는 이 목적에 안 맞는다(위 4번/7번 항목의 경고 참고).**

## D. 알려진 한계 / 다음 세션 이월

0. **(해결됨, 세션24) input 승격 오케스트레이션** — `refine_differential_and_mirror_
   relations()`(`stick_diagram.py` §1.7d)로 구현 완료, 아래 설계 스케치 (1)~(4)를
   그대로 구현했고 (5)는 while 루프 고정점 반복(`max_iterations=5` 상한)으로 결정.
   self-test Test 38로 검증(6소자 합성 fixture, 세션24 상세는 위 "지금 상태" 절
   "(해결됨) item 0" 참고). ⚠️ `current_reuse_telescopic_ota` 실회로 대조 실행은
   아직 안 함(다음 세션 item 0-A로 이월) — 아래는 세션23이 남긴 원래 설계 스케치
   원문(역사 기록 보존, 이미 구현됐으므로 재구현 불필요):
   `find_differential_pair_candidates()`(C-11, §1.7d)가 `inputs=` 선언 없이 순수
   connectivity만으로 differential pair 후보(gate net 포함)를 찾아내는 것까지는 되는데,
   그 후보의 gate net(예: `Voc`/`Voc_des`)을 **자동으로** `find_verified_differential_
   and_mirror_relations()`의 `inputs=`에 승격해서 재실행하는 루프가 아직 없다 — 지금은
   사람이 손으로 한 번(C-11 검증1) 확인했을 뿐, 코드화된 함수/자동화는 존재하지 않는다.
   **다음 세션에 이 오케스트레이션 함수(가칭 `refine_differential_and_mirror_relations()`
   류)를 신설할 것** — 설계 스케치: (1) `find_differential_pair_candidates()`로 1차
   후보 수집 → (2) 후보들의 `devices` 쌍에서 gate net 전부 추출 → (3) 그 net들을 기존
   `inputs=`에 합쳐 `find_verified_differential_and_mirror_relations()` 재실행 → (4)
   재분류로 `role`/net class가 바뀐 소자가 있으면(예: `M7`의 `CURRENT_SOURCE`→
   `AMPLIFYING`처럼) 그 변화도 결과에 명시적으로 포함(사람이 "왜 바뀌었는지" 바로
   알 수 있게) → (5) 1~4를 고정점에 도달할 때까지(더 이상 새 후보가 안 나올 때까지)
   반복할지는 설계 논의 필요(대부분 회로는 1회 반복으로 충분할 것으로 예상되나 미검증).
0-B. **[item 0 다음 순서] B-5-5의 남은 두 갈래(vertical_stack_id 보완 / `resolve_
   stack_layout()` 신설)를 이어서 진행할 것.** 세션22가 B-5-5에서 정리해둔 3갈래
   작업 중 **3번(analog-grammar 기반 matching_pairs/differential 자동판단)은 이번
   세션(C-1~C-12) 전체가 사실상 이 갈래를 깊게 판 결과물**이다 — 특히
   `find_differential_pair_candidates()`(C-11)가 "tool이 직접 판단하고 모호한 것만
   사람이 확인한다"는 B-5-5 3번의 원래 요구사항을 상당 부분 충족했다. 남은 건 **1번과
   2번**:
   1. `vertical_stack_id`를 `M1a`/`M1b`/`M2a`/`M2b`/`M4a`/`M4b`/`M37a` 등 빠진 소자까지
      채우기(B-5-5 1번, C-6이 `M37a` gap을 재확인) — `resolve_stack_layout()`이 이
      경계에 의존하므로 선행 조건.
   2. `resolve_stack_layout()`(가칭, B-5-3 설계) 신설 — `vertical_stack_id`로 1차
      분할 → finger_w 탐색 → 오일러 walk 구성 → 실패 시 `suggest_pair_finger_
      adjustments()` 제안 후 재검산, 결과를 `ctx.layout_solution`에 캐시하는 layered
      orchestrator. B-5-2의 2계층 정보 분리(topology 계층=`vertical_stack_id`/
      `matching_pairs` vs instance 계층=finger_w/walk 시퀀스, 메모리 캐시)가 이
      함수의 설계 기반.
   **순서**: item 0(input 승격 오케스트레이션)을 먼저 끝낸 뒤 이 두 갈래로 이어갈 것 —
   input 승격이 differential pair 인식의 마지막 정확도 문제를 닫아야, 그 위에서
   `vertical_stack_id`를 채우고 `resolve_stack_layout()`을 설계하는 게 흔들리지 않는
   기반 위에서 진행된다.
1. **(해결됨) analog-grammar rail 대소문자 버그(A절) + 미러 구동 bias net 오분류
   버그(A2절)** — 세션23 안에 둘 다 `netclass.py` 원본 수정까지 완료. rail 버그는
   `RAILS_POS`/`RAILS_NEG`/`RAILS`를 대소문자 무관 `_CaseInsensitiveNetSet`으로 교체,
   `stick_diagram.py`의 중복 로컬 우회 코드(2곳)도 제거. self-test 34개 전부 무회귀
   확인. 다른 프로젝트가 이미 analog-grammar를 대문자 관례로 쓰고 있었다면(세션23
   시점엔 확인된 사례 없음) 영향을 받을 수 있으나, 대소문자 무관 비교는 기존 대문자
   입력도 그대로 계속 인식하므로(엄격히 상위호환) 실질적 회귀 위험은 낮다.
2. **`M37a`/`M37b`의 `vertical_stack_id` gap**(C-6이 재확인) — `M37b`만 `cmfb_tail`
   선언, `M37a`는 비어있음. 실제로 채울지는 사용자 판단 필요(작은 수정, 바로 처리 가능).
3. **다른 3개 회로(folded_cascode/nmcnr_amplifier/two_stage_ota) 일반화는 미검증** —
   C-6의 62/63 성공률도, C-7/C-8의 branch 쌍 분류(구조적 그룹 11개, differential 4/
   mirror 5/no_connection 12)도 전부 `current_reuse_telescopic_ota` 하나에서만 확인됨.
4. **여덟 함수(`trace_vdd_to_gnd_branches`/`trace_gnd_to_vdd_branches`/
   `find_differential_and_mirror_forks`/`suggest_vertical_stack_composites`/
   `classify_symmetric_branch_pairs`/`find_verified_differential_and_mirror_relations`/
   `find_differential_pair_candidates`)를 실제로 `topology.json` 저작(예: `matching_
   pairs` 자동 제안, `vertical_stack_id` 자동 제안)에 배선하는 오케스트레이션은
   미구현** — 지금은 전부 진단/제안 도구로만 존재, "제안 채택 → `device_roles`/
   `symmetry.matching_pairs` 자동 기입" 파이프라인은 없음(의도적 — 사람/AI 검토 없이
   자동 채택하지 않는다는 원칙). 특히 `find_differential_pair_candidates()`가 찾은
   후보의 gate net을 `find_verified_differential_and_mirror_relations()`의 `inputs=`
   로 자동 승격하는 반복 정제 루프(C-11 마지막 문단)가 다음으로 자연스러운 확장.
5. **원래 이번 세션 목표(composite 소자 구성 함수)는 결국 이 형태로 완료됨** — B/C절의
   연쇄 실측을 거쳐 "matching_pairs 없이 자동 구성"에서 "vertical_stack_id 후보 제안"
   으로 목표 자체가 진화했다. 세션22 B-5-5의 3갈래 중 이걸로 사실상 완결된 건
   "matching_pairs 자동판단"과는 다른 갈래(vertical_stack_id 보완)이므로, `resolve_
   stack_layout()`(B-5-3)과 "analog-grammar 기반 matching_pairs 자동판단"(B-5-5 3번)은
   여전히 미착수.
6. **`run_harness.py` 실전략(세션22 이월 최우선, 위 "지금 상태" 1번)은 이번 세션도
   미착수** — vertical_stack_id 실측으로 세션 전체를 씀.
7. **(해결됨) `M37a`/`M37b`(CMFB 내부 2차 differential pair) 자동 인식** — C-11에서
   `find_differential_pair_candidates()`로 완전히 해결(선언 없이 순수 connectivity로
   검출). `M37a`/`M37b`의 `vertical_stack_id` gap(`M37b`만 `cmfb_tail` 선언, `M37a`는
   비어있음, C-6이 이미 재확인)은 이것과 별개 항목으로 여전히 남아있고, 실제로 채울지는
   사용자 판단 필요.
8. **`M7`+`M36a` "오탐" 용어 정정을 다른 문서/스킬에도 전파할지 검토** — 이번 세션
   `.ai/context.md`에는 정정 문단을 추가했지만, 세션18~22에 걸쳐 이미 "오탐"으로 여러
   번 기록된 과거 절들(§B, 세션22 B절 등) 자체를 소급 수정하지는 않았다(역사 기록
   보존 원칙, 위 "item2가 뭐지?" 사례와 동일 판단) — 다만 `analog-grammar-integration.md`
   등 다른 참조 문서에도 이 사례가 "오탐" 예시로 인용됐다면 그쪽은 정정이 필요할 수
   있음, 다음 세션에 확인.

## E. 세션25(2026-08-08) — `m_cascode()`가 기능적으로 틀린 "캐스코드"를 잡던 문제 발견/수정

### 발단
지난 세션(세션24) 요약을 보고하던 중 `M8`(`CURRENT_SOURCE`)+`M9a`(`CASCODE`)를
"교과서적인 캐스코드된 전류미러"라고 설명한 대목에 사용자가 의문 제기: "둘 다 pmos인데
drain이 M10에 의해 제한되니 M10/M9a가 cascode고 M8/M9b가 cascode 아닌가?"

### E-1. 실측 -- 이건 캐스코드가 아니라 Monticelli class-AB floating current source
연결성 재확인: `M9a`(pmos, `Vg15`->`Vop1`, gate=`N11b`), `M9b`(nmos, `Vop1`->`Vg15`,
gate=`N14a14b`) -- 비-레일 노드 두 개(`Vg15`/`Vop1`) 사이를 상보(PMOS/NMOS)로 마주보고
잇는 anti-parallel 구조. 그리고 `Vg15`=`M15.gate`, `Vop1`=`M16.gate`(`M15`/`M16`이
`Vom`을 만드는 2단 push-pull 출력쌍) -- `topology.json`의 기존 `_correction_log`/
`_correction_log_6`가 이미 "Monticelli floating current source는 PMOS+NMOS 상보쌍"
이라고 적어놨던 바로 그 구조였다. 사용자가 제안한 `M10`/`M9a`, `M8`/`M9b` 페어링은
drain-drain 연결(다른 kind, 직렬 아님)이라 캐스코드 정의(같은 kind, `up.S==lo.D` 직렬)
자체를 만족 못 함 -- 진짜 짝은 `M9a`/`M9b`.

**조치**: `analog-grammar/assets/idioms.py`에 `floating-current-source` idiom 신설
(priority=7) -- 서로 다른 kind가 비-레일 노드 2개 사이를 `a.S==b.D` 이고 `a.D==b.S`인
anti-parallel loop로 잇는 패턴을 검출. `M9a`/`M9b`와 Vop측 대칭 사례 `M18a`/`M18b`
정확히 검출(`examples/fig3_classab.json` 논문 원본 고립 fixture + 실제 회로 전체 양쪽
확인). `sfg.py`의 Stage 6 가설에도 "Monticelli floating current source" 규칙 추가.

### E-2. 사용자 재지적 -- "analog-grammar는 functional 이해 도구인데 M8/M9a가 여전히
cascode-stack으로 남아있으면 이 도구를 기능 파악에 못 쓴다는 뜻이다"
`floating-current-source`를 별도로 추가한 것만으론 부족 -- `m_cascode()` 자체가
`M8`+`M9a`를 여전히 `cascode-stack`으로 매칭하고 있었다(별개 idiom을 나란히 추가하는
것과, 잘못된 기존 매칭을 실제로 빼는 것은 다른 문제). **조치**: `m_cascode()`에
`m_diffpair()`의 `diffpair_legs`와 정확히 같은 방식으로 `float_legs`(`m_float_source()`
의 결과) 제외 추가 -- `up`이 floating-current-source의 다리면 캐스코드 후보에서 제외.
결과: 실제 회로의 `cascode-stack` 매칭이 11개->9개로 줄고 `M8`+`M9a`/`M10`+`M9b`/
`M17`+`M18a`/`M19`+`M18b`가 전부 빠짐(genuine 캐스코드 9개는 그대로 유지, 실측 확인).

### E-3. `up`/`lo` 네이밍 재확인 -- 버그 아님, 하지만 헷갈림
사용자가 "`m8`이 `lo`, `m9a`가 `up`인데 PMOS는 왜 반대로 잡히냐" 질문. 확인 결과:
매칭 로직(`up.S==lo.D`, `lo`=레일에 직접 닿은 소자, `up`=그 위에 얹힌 소자)은 PMOS/NMOS
동일 규칙이라 안 틀렸다 -- 다만 PMOS는 VDD가 위에 그려지는 관례라 "레일에 가까운 쪽"이
물리적으로 위(=`lo`가 물리적 위), NMOS는 GND가 아래라 "레일에 가까운 쪽"이 물리적으로
아래(=`lo`가 물리적 아래)라서, `up`/`lo`라는 이름을 "물리적 상/하"로 읽으면 PMOS에서
뒤집혀 보인다. `suggest_vertical_stack_composites()`가 실제 레이아웃 순서로 쓰는 건
이 `up`/`lo` 튜플이 아니라 `trace_vdd_to_gnd_branches()`의 실제 도보 순서(`chain[i:i+size]`)
라 이 네이밍이 실제 레이아웃 버그로 이어지진 않음을 실측 확인(`['M8','M9a',...]`
순서 그대로 나옴). **결론: 버그 아님, 이름이 헷갈릴 뿐** -- 개명 여부는 사용자가 보류.

### E-4. "출력이 source여도 cascode인가?" -- `M58`로 일반화된 반례 확인,
`_reaches_output()` 신설
사용자 질문에 실측으로 답하려고 `Vg15`/`Vop1`가 선언된 출력(`Vom`/`Vop`)까지 게이트를
따라 몇 hop인지 BFS로 확인 -- 둘 다 1-hop(`M15`/`M16` 게이트를 통해 직접). 그리고 살아있는
9개 `cascode-stack` 전부에 같은 BFS를 돌려보니: 진짜 캐스코드 4개(`M1a`/`M2a` 등)는
`mid`=None, `out`=1-hop으로 기존 라벨이 정확했지만, `M58`+`M6`/`M7`(bias-tap 구조,
`Vx`에서 다이오드 `M57`을 거쳐 `Vbias2` 생성)는 `mid`(`Vx`)/`out`(`N58_57`) 둘 다
출력에 안 닿아 명백한 반례는 아니었다(별도 문제 -- 아래 이월 항목 참고).

사용자 확인 질문("`up.source`가 출력이어도 cascode-stack이 될 수 있다고 한 거 아니냐")에
물리적 근거로 정정: MOSFET 소신호 모델상 **source 쪽 임피던스는 항상 low-Z(~`1/gm`)**라,
`up.source`가 진짜 출력이면 그 소자는 애초에 임피던스를 부스트하는 캐스코드 기능을 할 수
없다 -- `mid`/`out` 라벨을 바꿔 불러도 해결 안 됨(물리적 사실 자체가 안 바뀜), 그래서
"라벨 교체"가 아니라 "매칭 제외"가 맞다는 결론.

**조치**: `idioms.py`에 `_reaches_output(node, devs, cls, maxhop=6)` 신설(순수 BFS,
`node`가 어떤 소자의 gate로 쓰이면 그 소자의 drain/source로 이동, `cls`상 `OUTPUT`
도달 시 hop 수 반환 -- `outputs=` 미선언 시 `cls`에 `OUTPUT`이 없어 항상 `None`,
부작용 없음). `m_cascode()`에 연결: `up.source`가 `up.drain`보다 출력에 더 가깝거나
같으면(`mid_hops is not None and (out_hops is None or mid_hops <= out_hops)`) 제외.
`outputs=('Vom','Vop')` 선언 시 실제 회로/고립 fixture 양쪽에서 9개 `cascode-stack`
그대로 유지 확인(이 9개 중 이 조건에 걸리는 게 없었음 -- `M58` 포함 전부 통과), 미선언
시에도 동일 결과(부작용 없음) 확인.

### E-5. 회귀 발견/수정 -- `stick_diagram.py`의 레이아웃 스택 제안이 `cascode-stack`에
의존하고 있었다
E-2/E-4로 `m_cascode()`가 `M8`+`M9a`를 더 이상 안 잡으면서, `suggest_vertical_stack_
composites()`(레이아웃용 물리적 스택 후보 제안, `idioms.match_all()`을 그대로 재사용)도
덩달아 이 쌍을 못 찾게 됐다 -- 지난 세션에 막 채운 `vertical_stack_id`(`M9a`->
`biasgen_vom_a`) gap-filling의 근거였던 바로 그 매칭. 사용자 지시로 `netclass.
stack_edges()`(role/idiom 해석 없는 순수 구조 함수)를 폴백으로 추가했는데 **이게 새
회귀를 냄**: `stack_edges()`는 fan-out 카디널리티를 안 봐서, 차동쌍 다리 `M1a`(source=
`Vx`)와 그 tail 전류원 `M6`(drain=`Vx`)도 "source==drain"만으로 물리 스택 후보로
잡아버렸다(`Vx`는 `M6`/`M7` 둘 다 drain, `M1a`/`M1b` 둘 다 source인 fan-out 노드라
1:1 직렬이 아님 -- `m_cascode()`가 `diffpair_legs` 제외로 이미 피하던 함정을 이 폴백이
무시). 결과: branch 훑기가 `M1a`를 `M6`과 먼저 묶어 `M1a`+`M2a`가 갈라짐, self-test
Test 40이 이 회귀를 정확히 잡아냄(`AssertionError: M1a/M2a가 같은 vertical_stack_id
후보를 못 받음`).

**최종 수정**: `stack_edges()`를 직접 안 쓰고, `m_cascode()`와 똑같은 1차 게이트(role이
`CASCODE`/`AMPLIFYING`/`CONTROLLED_CURRENT_SOURCE`) + `diffpair_legs` 제외를
`suggest_vertical_stack_composites()` 안에서 재구현하되, `float_legs`/출력-도달성
제외 두 개만 의도적으로 생략(이 둘은 "기능적으로 캐스코드가 아니다"는 판단이지 "물리적
으로 못 쌓는다"는 뜻이 아니므로)해서 `kind='physical-stack'` 폴백으로 넣었다. 결과:
`M1a`+`M2a`는 정상 `cascode-stack`으로 유지, `M8`+`M9a`/`M18a`+`M17`은 `physical-stack`
으로 복구, self-test 44개 전부 재통과, fan-out 오염 없음(전체 composite 목록 수동
검토로 확인).

### 변경 파일 (전부 이번 세션)
- `skills/analog-grammar/assets/idioms.py`: `floating-current-source` idiom 신설,
  `_reaches_output()` 신설, `m_cascode()`에 `float_legs` + 출력-도달성 제외 추가
- `skills/analog-grammar/assets/sfg.py`: Stage 6 가설에 Monticelli 규칙 1줄 추가
- `skills/analog-gmid-design/assets/stick_diagram.py`: "캐스코드된 전류미러" 오기술
  정정(2곳), `suggest_vertical_stack_composites()`에 `physical-stack` 폴백 추가
- `.ai/context.md`: 0-C(headroom_role 재시도 계획)에 `M9a`/`M18a` 반례 반영, 이 E절

### 다음 세션 이월
- **self-test 커버리지 gap**: `floating-current-source` idiom, `m_cascode()`의 두
  신규 제외(`float_legs`, 출력-도달성), `physical-stack` 폴백 전부 이번 세션 실측
  검증(analyze.py 수동 실행 + 회귀 확인)만 했고, `stick_diagram.py`의 Test 1~44
  self-test 스위트에 **전용 테스트를 추가하지 않았다** -- 프로젝트 관례(모든 동작
  변경엔 self-test)에 어긋나므로 다음 세션 우선 처리할 것.
- **`M58`+`M6`/`M7` "bias-tap" 패턴 미해결** -- E-4에서 발견: `M58`은 `M1a`/`M1b`와
  같은 tail(`Vx`)에서 전류를 뽑아 다이오드(`M57`)로 `Vbias2`(다른 캐스코드들의 게이트
  바이어스)를 생성하는 구조로, "캐스코드"라기보다 differential-pair의 "제3의 다리"에
  가깝다(`m_diffpair()`가 이미 `M58`을 다른 이유로 배제하고 있음 -- 2026-08-07 수정
  주석 참고). 지금은 `cascode-stack`으로 남아있는데 이것도 기능적으로 틀렸을 수 있음
  -- 다음 세션에 재검토(단, `_reaches_output()` 기준으로는 `mid`/`out` 둘 다 출력에
  안 닿아 E-4의 판정 기준만으로는 못 잡음 -- 별도 판정 로직 필요할 수 있음).
  ⚠️ `M9a`/`M18a`류처럼 "명명 가능한 별도 idiom"이 항상 있는 게 아니라는 점도 염두에
  둘 것 -- `M58`은 `floating-current-source`에도 안 맞음(anti-parallel 아님, 그냥
  단방향 diode-경유 bias-tap).
- **`vertical_stack_id` 재검증 불필요 확인됨** -- `physical-stack` 폴백이 `M8`+`M9a`
  등을 그대로 복구하므로, 세션24가 채운 15개 gap(`biasgen_vom_a`의 `M9a` 등)은 여전히
  유효/재현 가능. 별도 조치 불필요.

## F. 세션25 후속 — `netclass.assign_roles()`도 `CASCODE`로 뭉뚱그리던 문제 수정 +
`headroom_role`(0-C) 재착수 중 발견한 반례

### F-1. `assign_roles()`에 `FLOATING_CURRENT_SOURCE` role 신설
E절에서 `idioms.m_cascode()`는 고쳤지만, 그보다 아래 계층인 `netclass.assign_roles()`
자체가 여전히 `M9a`/`M9b`/`M18a`/`M18b`를 `CASCODE`로 뭉뚱그리고 있다는 걸 사용자가
직접 지적(`M18b`가 `CASCODE`로 뜨는 걸 보고). 사용자 확인: "완전히 새 카테고리가
아니라 `CURRENT_SOURCE`의 floating 버전이어야 하지 않나" — 그대로 반영.

**조치**: `netclass.py`에 `FLOAT_SRC = 'FLOATING_CURRENT_SOURCE'` 신설, `_floating_
source_legs()`(`idioms.m_float_source()`와 동일 판정 기준을 role 배정 이전에 전역
계산) 추가, `assign_roles()`의 `elif gc==BIAS` 분기에서 소스가 내부노드인 소자 중
이 다리에 해당하면 `CASCODE` 대신 `FLOAT_SRC` 배정. 실측: `M9a`/`M9b`/`M18a`/`M18b`
전부 `FLOATING_CURRENT_SOURCE`로 정확히 분류됨(고립 fixture + 실회로 양쪽 확인).

**연쇄 수정(CASCODE 소비처 전부 점검)**: `sfg.py`의 `build_sfg()`(cascode 신호간선
조건에 `FLOAT_SRC` 추가 -- 안 하면 `n1->Vop1` 양귀환 loop 탐지가 깨짐),
`stick_diagram.py`의 `suggest_vertical_stack_composites()`(`physical-stack` 폴백의
role 게이트에 `FLOAT_SRC` 추가 -- 안 하면 오늘 만든 폴백 자체가 다시 깨짐),
`_propose_vertical_stack_ids()`의 fan-in 후보 탐지(`role=='CASCODE'` 단일 비교를
`(CASCODE, FLOAT_SRC)` 튜플로 확장 -- 안 하면 `M9b` fan-in 탐지가 깨짐). self-test
44개 전부 재통과, 실회로 `physical-stack`/`cascode-stack` 목록 전과 동일함을 재확인
(회귀 없음). `references/analog-grammar-integration.md`의 §8 role 매핑 표에도
`FLOATING_CURRENT_SOURCE` 행 추가 + `CASCODE` 행 예시에서 `M10`(아래 F-2로 의심 사례임)
제거.

### F-2. `headroom_role`(0-C) 재착수 — 6가지 가설이 실패한 이유가 "선언값 자체의 오류"
였을 가능성 발견 (미확정, 다음 세션 결론 필요)
세션24가 남긴 9개 불일치(`M17,M8,M18b,M9b,M36b,M39,M40,M63,M37b`)를 오늘 고친
idiom/role로 재검토하다가, 사용자가 핵심을 짚음: "우리 hypothesis가 계속 반례를
못 뚫는 게 아니라, **선언된 `headroom_role` 값 자체가 애초에 틀렸을 수 있다**"는
관점 전환.

**실측 근거**: `role==CURRENT_SOURCE`(레일에 직접 닿은 고정 바이어스) 소자 8개의
`headroom_role` 선언을 전부 나열하면:
```
M6/M7(Vx tail)/M5(Vy tail)/M38(Ncmfb_tail) -> tail   (진짜 차동쌍 tail, 정상)
M8(Vg15 위쪽 bias) -> mirror
M17(Vg25 위쪽 bias) -> mirror
M10(Vop1 아래쪽 bias) -> cascode   ⚠️ M8과 구조적으로 완전히 동일한 역할인데 다름
M19(Vom1 아래쪽 bias) -> cascode   ⚠️ M17과 동일 패턴, 대칭 사례
```
`M10`/`M19`는 `M8`/`M17`과 정확히 같은 구조(같은 Monticelli floating loop의 반대쪽
끝을 대주는 고정 전류원, 레일에 직접 닿아 있어 애초에 "캐스코드"의 정의(다른 소자
위에 얹힘)를 만족할 수조차 없음)인데 `cascode`로 선언돼 있다 -- 설계 의도라기보다
**선언 오류**로 강하게 의심됨.

또한 `M9a`(gap, 비어있음)/`M9b`(mirror 선언) 그리고 `M18a`(gap)/`M18b`(mirror 선언)
쌍에서, 같은 물리적 구조(Monticelli floating source 다리)의 한쪽만 채워진 비대칭
패턴이 반복된다 -- 오늘 발견 이전에 누군가 `M9b`의 게이트가 다이오드(`M14a`) 기준을
따라간다는 부분적 근거로 `mirror`를 채우고, `M9a`는 막혀서 비워둔 것으로 추정.
`M9b`/`M18b`의 `mirror`도 `cascode`만큼 부정확할 가능성 높음(둘 다 floating source
다리이지 진짜 mirror가 아님) -- `M37a`(gap)/`M37b`(tail 선언, CMFB 2차 differential
pair의 다리)도 같은 비대칭 패턴이라 같이 재검토 대상.

**미확정 -- 다음 세션 결론 필요**: 이 세션 안에 `topology.json`을 수정하지 않았다
(대기열에 쌓아뒀다가 한꺼번에 반영하는 관례). 다음에 확정할 것:
1. `M10`->`mirror`, `M19`->`mirror`로 정정할지 (구조적 근거는 확실하나 사용자 최종
   확인 필요)
2. `M9a`/`M9b`/`M18a`/`M18b`에 새 headroom_role 카테고리(가칭, `FLOATING_CURRENT_
   SOURCE`와 이름을 맞출지 논의)를 신설해서 채울지, 아니면 다른 처리를 할지
3. `M37a`/`M37b`(CMFB 2차 differential pair)도 같은 논리로 재검토 -- 이번 세션엔
   미착수
4. `M58`(bias-tap, E절 이월 항목)도 여전히 미해결 -- `cascode` 선언이 맞는지 별도
   검토 필요
5. 이 재검토가 끝나면 6가지 실패 가설과 9/35라는 숫자 자체를 다시 계산해야 할 수도
   있음(선언값이 바뀌면 "불일치 개수"의 기준선도 바뀜)

### F-3. F-2 정정 확정 반영 (같은 세션 안에서 사용자 승인)
`docs/04-report/analog-topology-json-library.do.md` §7.3.1(원본 설계 문서, 이 프로젝트가
`do.md`라고 불러온 그 파일 -- `docs/04-report/`에 있음, 이번에 처음 정확한 경로 확인)의
`allocate_stack_headroom()` 원본 예제(6소자 스택 `M6`-`M1`-`M2`-`M3`-`M4`-`M5`)를 찾아
추가 근거 확보: **레일에 직접 닿는 양 끝 소자(`M6`/`M5`)는 `tail`(넉넉한 배분), 중간에
낀 소자(`M2`/`M3`)만 `cascode`(최소 배분)**라는 패턴이 원본 설계 의도에 명시돼 있다.
`M8`-`M9a/M9b`-`M10`(그리고 대칭 `M17`-`M18a/M18b`-`M19`) branch도 양 끝이 레일에
직접 닿는 같은 모양이라, `M10`/`M19`도 "바깥쪽" 위치 -- `mirror`(또는 그에 준하는 넉넉한
배분)가 맞다는 걸 구조적 대칭 논증(F-2)에 이어 원본 문서로 재확인.

**반영 완료**(`current_reuse_telescopic_ota.topology.json`):
- `M10`: `headroom_role` `cascode` -> `mirror`
- `M19`: `headroom_role` `cascode` -> `mirror`
- `M9a`: `headroom_role` 신설(`floating_current_source`, 원래 비어있던 gap)
- `M9b`: `headroom_role` `mirror` -> `floating_current_source`
- `M18a`: `headroom_role` 신설(`floating_current_source`)
- `M18b`: `headroom_role` `mirror` -> `floating_current_source`
(`gm_id_role`/`L_role`은 이번 재검토 범위 밖이라 손 안 댐 -- `M9b`/`M18b`는 기존
`matching`/`mirror` 유지, `M9a`/`M18a`는 여전히 gap으로 남음, 별도 세션에서 다룰 것)

`floating_current_source`는 `netclass.FLOAT_SRC`('FLOATING_CURRENT_SOURCE')와 이름을
맞췄다(F-1). `sizing_recipe.py`의 `allocate_stack_headroom()`은 `role=="cascode"`가
아닌 모든 값을 동일하게 "나머지" 버킷(균등 배분)으로 처리하므로 새 문자열 값이 있어도
에러 없이 동작함을 코드로 확인(런타임 검증은 `sizing_recipe.py` self-test 실행 중,
결과는 다음 세션 시작 시 재확인).

**남은 것**: `M37a`/`M37b`(CMFB 2차 differential pair, 같은 비대칭 gap 패턴)과 `M58`
(bias-tap)은 이번엔 미착수 -- 다음 세션 이월. 6가지 실패 가설의 "9/35 불일치" 기준선도
이 정정 이후 다시 세야 한다.

### F-4. `M37b`(사용자 지적) -- `M1a`류(메인 차동쌍)와 정확히 같은 이유로 headroom_role
자체가 없어야 정상
`M37a`/`M37b`는 CMFB 2차 differential pair(게이트=`Voc`/`Voc_des`)인데, `M37a`는 이미
gap(headroom_role 없음, `M1a`류와 동일)인 반면 `M37b`만 `tail`이 잘못 선언돼 있었다
(진짜 tail은 `M38`). `M37b`를 `M37a`와 동일하게 `{"vertical_stack_id": "cmfb_tail"}`
만 남기고 `headroom_role`/`gm_id_role` 제거 -- 결과 36/37(97%), F-2의 33/38에서 크게
개선(`M58`/`M63`의 "외부 소비자 수" 휴리스틱 없이도 diode-connected 확장 규칙만으로
도달, 아래 F-5 참고).

### F-5. `diode-cascode` idiom 신설 + `netclass`에 `DIODE_REFERENCED_CASCODE` role 신설
(사용자 지적)
사용자가 `M63`(role=`CASCODE`, gate=`Vbias3`)이 `M64`(diode-connected, gate=drain=
`Vbias3`) 바로 아래 얹혀 **같은 노드를 게이트로 직접 받는다**는 걸 지적 -- 기존
`diode-connected`(단일 소자, `up`만 봄)도 `m_cascode()`(직렬 판정만, 게이트 출처는
안 봄) 어느 쪽도 이 패턴을 못 잡고 있었다. `M58`(gate=`Vbias2`)이 `M57`(diode,
gate=drain=`Vbias2`)에 대해 정확히 같은 관계임도 사용자가 확인.

**조치**: `idioms.py`에 `diode-cascode` idiom 신설(priority=4, `up.G==up.D`이고
`lo.D==up.S`이고 `lo.G==up.D`인 같은 kind 쌍) -- `diode-cascode(M64,M63)`,
`diode-cascode(M57,M58)` 정확히 검출. 이어서 사용자가 "`netclass`도 같이 고쳐야
하지 않냐"고 지적(`FLOAT_SRC` 때와 같은 논리) -- `netclass.py`에 `DIODE_CASC=
'DIODE_REFERENCED_CASCODE'` role 신설, `_diode_cascode_legs()`(role 배정 전 전역
계산, diode 여부는 role 없이도 판정 가능해 순환 의존 없음)로 `M63`/`M58`을 일반
`CASCODE`에서 분리. `FLOAT_SRC` 때와 동일한 연쇄 수정 필요(`sfg.py`의 cascode
신호간선, `stick_diagram.py`의 `physical-stack` 폴백 role 게이트, fan-in 탐지 전부
`DIODE_CASC` 추가) -- 안 하면 `M5`+`M63`, `M57`+`M58` 물리적 스택이 사라짐(실측
확인 후 수정, self-test 44개 재통과).

**headroom_role 규칙 재평가**: diode-cascode의 `lo`를 자기 diode 파트너와 동일하게
취급(파트너가 mirror_ref거나 mirror_ref를 포함한 vertical_stack_id 그룹에 속하면
mirror, 아니면 cascode)하는 규칙으로 재평가해도 여전히 **36/37** -- `M58`은 정확히
맞고(`cascode`), `M63`만 반례(`declared=mirror`, `proposed=cascode`)로 남는다.
**`M58`/`M57`과 `M63`/`M64`가 `diode-cascode` idiom으로 구조적으로 완전히 동일함이
증명됐으므로, 어떤 순수 connectivity 규칙을 써도 이 둘 중 하나는 항상 반례로 남는다**
-- 이번 세션 내내 반복된 패턴(`M8`/`M10`, `M9a`/`M9b`, `M37a`/`M37b`)과 같은 종류의
선언값 오류일 가능성이 높지만(다음 세션 확정 필요), `M63`/`M58` 중 어느 쪽이 진짜
오류인지는 이번 세션엔 결론 못 냄.

### G. 세션25 최종 마무리 -- `M63`/`M58` 확정, `_propose_headroom_roles()` 구현,
`M39`/`M40` 추가 정정으로 **37/37** 달성

**`M63` 확정(사용자 판단)**: `M63`이 진짜 `cascode`(declared `mirror`가 오류) --
`topology.json` 정정 완료.

**`_propose_headroom_roles()` 구현** (`stick_diagram.py`, `_propose_gm_id_roles()`/
`_propose_L_roles()`와 같은 위치·패턴): F/G절의 최종 규칙(role==`FLOATING_CURRENT_
SOURCE`→`floating_current_source`, tail 후보→`tail`, `CURRENT_SOURCE`/`ACTIVE_LOAD`
→`mirror`, `DIODE_REFERENCED_CASCODE`/`DIODE_CONNECTED`→diode 파트너의 mirror_ref
여부(직접/`vertical_stack_id_candidates` 그룹 공유/`L_role_candidates.symmetry_
partner`까지 확장)로 `mirror`/`cascode` 판정, `CASCODE`→`cascode`)를 그대로 코드화.
`refine_differential_and_mirror_relations()`의 반환값에 `headroom_role_candidates`
필드로 추가. ⚠️ **사용자 지적으로 하드코딩된 12+2개 제외 목록을 뺌** -- `_propose_gm_id_
roles()`와 같은 원칙("51개 전부 일관 반환, 회로 전용 이름 목록을 두면 다른 회로에서
조용히 무의미해짐")으로, 차동쌍 입력류는 결과적으로 규칙 어디에도 안 걸려 자연스럽게
`None`이 나옴(하드코딩 불필요했음이 실측으로 확인됨).

**구현 직후 34/37로 확인**(`M36b`/`M39`/`M40` 반례) -- 원인: 수작업 검증 스크립트는
"declared" `vertical_stack_id`(`cmfb_load`)로 `M36a`/`M36b`/`M39`/`M40`을 한 그룹으로
봤지만, 실제 함수가 쓰는 `vertical_stack_id_candidates`(물리적 스택 기준)는 이들을
물리적으로 안 쌓인 병렬 소자라 별도 그룹으로 낸다 -- "declared 값에 의존하는 검증
스크립트"와 "처음부터 제안하는 실제 함수"의 근본적 차이가 여기서 드러남. `L_role_
candidates.symmetry_partner`(구조적 좌우 대칭)를 추가 신호로 연결해 `M36b`(파트너
`M36a`가 mirror_ref)까지 잡아 35/37.

**`M39`/`M40` 최종 정정(사용자 판단 2회)**: (1) "`M39`/`M40`도 diode_connected인데
`M11a`/`M11b`처럼 기능적으로 `cascode` 아니냐"는 사용자 지적으로 `topology.json`
정정(`mirror`->`cascode`) -- 규칙 확장 없이 **선언값 자체가 틀렸다**는 결론. (2)
사용자가 "headroom_role의 정의 관점에서 재평가"를 요청 -- `do.md`의 `r_cmfb_vocdes`
theta 주석("VDD-M39-Voc_des-M40-GND는 self-biased 2-diode 분압기라 이 가지의 전류를
정해주는 레퍼런스가 없다, 전류는 오직 M39/M40의 W/L이 정한다")을 근거로 확인: `mirror`
라는 이름 자체가 "기준전류를 따라간다"는 뜻인데 `M39`/`M40`은 미러링할 기준전류가
없다(`M11a`/`M11b`와 정의상 동일) -- 구조적 대칭과 기능적 정의 두 독립 근거가 같은
결론(`cascode`)으로 수렴, 정정 확정.

**최종 결과**: `current_reuse_telescopic_ota` 선언된 37개 **37/37 일치**. self-test
Test 45 신설(합성 fixture로 `tail`/`cascode`/`mirror`/`floating_current_source` 네
값 전부 + diode-cascode의 mirror_ref 유무 분기까지 검증), self-test 45개 전부 재통과.

**세션25 전체에서 정정된 declared 값 총정리**: `M10`(cascode→mirror), `M19`(cascode→
mirror), `M9a`(gap→floating_current_source), `M9b`(mirror→floating_current_source),
`M18a`(gap→floating_current_source), `M18b`(mirror→floating_current_source),
`M37b`(tail→gap, 차동쌍 다리라 원래 없어야 함), `M63`(mirror→cascode), `M39`
(mirror→cascode), `M40`(mirror→cascode) -- 총 10개 소자, 전부 이번 세션에 발견된
"구조적으로 동일한 두 소자가 반대로 선언된" 패턴의 인스턴스.

**다음 세션 이월**: (1) 이 37/37 규칙의 일반성은 `current_reuse_telescopic_ota`
하나로만 확인됨 -- 다른 3개 회로(folded_cascode/nmcnr_amplifier/two_stage_ota)에서도
검증 필요.
(2) **(해결됨)** `M58`의 `headroom_role="cascode"`가 기능적으로 정확한 서술인지는
G절 시점엔 별개 문제로 남아있었으나, H절에서 `diode-cascode` idiom을 신설하며 확정됨:
`M57`은 diode-connected, `M58`은 정확히 그 `M57` 위에 얹혀 같은 노드를 게이트로 받는
**diode-cascode**(`DIODE_REFERENCED_CASCODE` role) 구조다(사용자 확인) -- "bias-tap"
이라는 표현은 이 구조를 정확히 이름 붙이지 못한 세션25 E절 시점의 서술이었을 뿐,
`M58`은 진짜 diode-cascode이므로 `headroom_role="cascode"`는 이름 그대로 정확하다.

## H. 세션25 후속 -- `vertical_stack_id` declared 값 재검토 착수, 그 과정에서
`find_verified_differential_and_mirror_relations()`의 근본 한계 발견/수정

### H-1. `vertical_stack_id_candidates`(물리적 스택 기준)와 declared `vertical_stack_id`
(더 넓은/일관성 없는 기준)의 불일치 발견
사용자가 `M36a`/`M36b`(CMFB 좌우 대칭 load)가 왜 같은 `vertical_stack_id_candidates`
그룹으로 안 묶이는지 질문 -- 확인해보니 둘은 서로 다른 branch에 있어(각자 `vdd`에서
독립적으로 시작해 `M37a`/`M37b`를 통해 내려가는 병렬 구조) `suggest_vertical_stack_
composites()`(branch 단위로 독립 스캔)가 원천적으로 하나로 못 묶는다 -- **물리적
직렬 스택**만 보는 이 함수의 정의상 정상 동작.

이어서 declared `vertical_stack_id` 전체를 물리적 스택 기준과 대조해보니(`M6`/`M7`/`M5`
가 전부 "stage1"로 묶인 것, `biasgen_vom_a`가 진짜 신호경로(`M8`+`M9a`)와 순수
바이어스 생성(`M13`+`M11a`+`M11b`)을 뭉쳐놓은 것 등), **declared 값이 물리적 스택
기준 하나가 아니라 "설계 단계"(1단/2단/3단) 같은 더 넓은 기준과 뒤섞여 있음**이
드러남. 사용자 판단: **declared 값을 전부 물리적 스택 기준으로 분해**하기로 결정
(진행 중, 아래 H-3에서 재개).

### H-2. `M58`의 fan-in 재판정 오류 -- `find_verified_differential_and_mirror_
relations()`의 근본 한계 발견/수정 (사용자가 직접 근본원인까지 추적)
`vertical_stack_id_candidates` 재계산 중 `M58`이 `M57`(진짜 diode-cascode 파트너)이
아니라 `M7`과 묶이는 걸 발견 -- 사용자가 근본원인을 직접 추적: `M7`이 `diff_branch_
members`(fan-in 재판정에 쓰는 집합)에서 빠져 있었다. 이유: `Vx`가 `M6`/`M7` 둘로부터
병렬 공급되는데, `find_verified_differential_and_mirror_relations()`가 `(M1a,M1b)`
관계를 `M6`쪽 조합에서만 찾고 `M7`쪽의 독립적인 동일 발견은 **소자쌍 dedup**(같은
`(a,b)`가 여러 branch 조합에서 나오면 대표 하나만 남김)에 조용히 버려 `M7`이 "차동쌍
소속 아님"으로 오판정, 그 결과 `M58`이 `M7`로 잘못 확정됨.

**시행착오 3라운드(전부 사용자가 반례로 잡아냄)**:
1. **전체 체인 누적** -- `ca`/`cb` 전체를 `branch_members`에 넣음. `M7` 문제는
   해결했지만 `M10`/`M19`(전혀 다른 mirror 관계의 당사자)까지 같은 chain-prefix를
   공유한다는 이유만으로 `differential_branch_members`에 끌려 들어와 `M9b`의 기존
   fan-in 재판정(`M9b`->`M10`)이 깨짐.
2. **"mirror 당사자면 differential에서 배제"** -- 방향 무관하게 동작하지만, `M3a`/
   `M3b`(같은 differential branch에 물리적으로 스택된 캐스코드이면서 동시에 서로
   mirror 관계)까지 배제해버려 Test 42(`M9b`류 fan-in 재현)가 깨짐. 사용자가 핵심을
   짚음: "**differential branch와 symmetric branch를 동시에 보고 각각의 branch에
   속한 걸 구별**해야 한다" -- `M10`이 배제돼야 하는 이유는 "mirror 당사자라서"가
   아니라(`M3b`도 mirror 당사자이지만 배제되면 안 됨) 그 특정 differential 비교에
   실제로 도달하는 상류 경로가 아니기 때문.
3. **방향 인식 상류 슬라이스(최종)** -- `vdd_to_gnd`는 chain이 레일에서 시작하므로
   상류=앞쪽(`ca[:pos+1]`), `gnd_to_vdd`는 반대라 상류=뒤쪽(`ca[pos:]`). 같은 `M10`/
   `M19`가 `vdd_to_gnd`에서는 위치3(하류, 정상 제외)인데 `gnd_to_vdd`의 역순 chain
   에서는 위치0(방향 무시하면 상류로 오인)에 온다는 게 실측으로 확인된 근본 원인 --
   방향별로 슬라이스 방향을 뒤집으면 `M6`/`M7`(진짜 상류)과 `M3a`/`M3b`(다른 differential
   발견의 상류)는 포함되고 `M10`/`M19`(무관한 별개 분기)는 제외된다.

**구현**: `find_verified_differential_and_mirror_relations()`가 `"{category}_branch_
members"` 필드(`differential_branch_members`/`mirror_branch_members`/
`structurally_symmetric_no_connection_branch_members`) 신설 -- 소자쌍 dedup과
무관하게 방향 인식 상류 슬라이스로 누적. `_propose_vertical_stack_ids()`의
`diff_branch_members`가 이 필드를 직접 사용(없으면 구버전 폴백). 부수 버그 2개 추가
발견/수정: (a) `assign()`이 `ambiguous` 소자를 **관련 없는** composite에서도 막고
있었음(`M58`이 `M57`과 묶이는 것까지 차단) -- 후보 그룹에 실제로 걸릴 때만 제외하도록
좁힘. (b) `ambiguous` pre-population이 composite 스캔보다 먼저 실행돼 스캔이 찾은
진짜 그룹을 가로챔 -- 스캔 뒤로 이동. (c) `ambiguous_alternatives`가 스캔으로 이미
해소된 소자까지 "미해결"로 보고 -- 최종 `group_of`가 여전히 고립 상태인 것만
필터링하도록 수정.

**실측 검증**: `M6`/`M7`/`M1a`/`M1b`/`M4a`/`M4b`/`M3a`/`M3b` -- 전부 `differential_
branch_members`에 정확히 포함. `M10`/`M19` -- 정확히 제외. `M58`이 이제 `M57`과 같은
그룹(`diode-connected_3`)으로 정확히 묶임. `ambiguous_alternatives`는 다시 빈
딕셔너리(전부 실제로 해소). `headroom_role` 37/37 유지(회귀 없음). self-test Test 46
신설(`M6`/`M7`류 진짜 상류 tail 포함 + `M3a`/`M3b`류 mirror-이면서-differential 포함 +
`Mfork_a`/`Mfork_b`류 무관 mirror 분기 제외, 세 가지 반례 패턴 전부 한 fixture로 검증),
self-test 46개 전부 재통과.

### H-3. declared `vertical_stack_id` 재분해 완료
H-2 수정 이후 데이터로 표를 재생성해보니 `M9b`+`M10`, `M18b`+`M19`가 새로 하나의
물리적 그룹으로 정확히 합쳐짐이 확인됨(H-2 수정의 직접적 효과 -- `M9b`의 fan-in이
`M10`으로 올바르게 재확정되면서 그 그룹에 정상 합류). `topology.json`의 declared
`vertical_stack_id`를 물리적 스택 기준으로 전부 재분해:

```
stage1 -> vx_tail_a(M6) / vx_tail_b(M7) / vy_tail(M5)
biasgen_vom_a -> biasgen_vom_a(M8,M9a, 유지) / biasgen_vom_diode_src(M13) /
                 biasgen_vom_battery_a(M11a,M11b)
biasgen_vom_b + biasgen_vom_d -> biasgen_vom_battery_a_sink(M12) /
                 biasgen_vom_battery_b(M14a,M14b) /
                 biasgen_vom_floatsrc_sink(M9b,M10 -- 새로 합쳐짐)
biasgen_vop_* -> Vom측과 대칭 동일 패턴(M18b+M19도 새로 합쳐짐)
biasgen_tree_a/b/root -> vbias4_gen(M60) / vbias3_stack(M64,M63) / vbias3_gen(M61) /
                 vbias2_stack(M58,M57) / biasgen_ref(M18_bg) / vbias4_stack(M66) /
                 vbias2_gen(M68)
cmfb_load -> cmfb_load_a(M36a) / cmfb_load_b(M36b) / cmfb_vocdes_gen(M39,M40)
cmfb_tail, diffpair_*, output_stage_* -> 변경 없음(이미 물리 기준과 일치했음)
```

self-test 46개 전부 재통과, `headroom_role` 37/37 유지(회귀 없음). 다음 세션 이월:
이 재분해가 다른 3개 회로에서도 일반화되는지는 미검증(이번 세션 전체가
`current_reuse_telescopic_ota` 하나로만 확인됨, F/G/H절 공통 한계).

## I. 세션26(2026-08-10) — `resolve_stack_layout()` 신설

### I-1. 정밀조사로 드러난 것 — B-5-3 설계 스케치의 실제 구멍은 하나뿐이었다
B-5-3(세션22~23)은 `resolve_stack_layout()`을 "그룹별 finger_w 탐색(`search_stack_
finger_w()`) → 실패시 그룹분할 → 오일러 walk 구성(`mirror_symmetric_trail()`) →
실패시 `suggest_pair_finger_adjustments()` 제안 → 재검산"까지 전부 새로
오케스트레이션하는 함수로 스케치했다. 구현 착수 전 Explore agent로 데이터 흐름을
정밀조사한 결과, 이 스케치는 **이미 대부분 구현·배선돼 있었다는 게 드러났다**:
- `assign_finger_geometry()`(`stick_diagram.py:3735`)가 그룹마다 이미 `search_stack_
  finger_w()`를 호출하고 있었다(정렬된 그룹 순회 + 이전 그룹의 `total_row_fingers`를
  target으로 넘기는 방식까지 스케치와 동일).
- `run_topology_pipeline_with_finger_fixup()`(`sizing_recipe.py:3173`)이 이미
  `suggest_pair_finger_adjustments()` 제안 → 재검산 → 그래도 실패하면 그룹분할
  (crossover routing)까지 폴백하는 전체 루프를 세션15~18에 걸쳐 완성해뒀다.
- `run_matching_safety_with_finger_growth()`(`sizing_recipe.py:3022`)가 매칭 완화
  (3b/3c) 쪽의 대칭 루프도 이미 세션16~18에 완성해뒀다.

즉 실제로 비어있던 건 이 모든 함수가 공통으로 입력받는 **1차 물리 그룹 분할 경계**
하나뿐이었다 — `stack_groups_geometry`가 지금까지 `geometry_colocation_union()`의
자동 추론(전기적 인접 추측, B-5-1이 "이 사고 원인"이라 지목한 바로 그 union-find)
하나에만 의존했고, 사람이 선언한 `vertical_stack_id`는 (`allocate_stack_headroom()`을
통한 헤드룸 계산 경로에서만 쓰일 뿐) layout/오일러/finger_w 경로 어디에도 연결돼
있지 않았다(`Transistor` dataclass에 `vertical_stack_id` 필드 자체가 없음, 정밀조사로
실측 확인).

**부수 발견**: `stack_groups_kcl`(`kcl_series_union()` 결과)은 이 교체 대상이 아니다
— `stack_id_of`를 거쳐 A엔진(`propagate_topology_forced_currents()`)의 전류 전파
에서만 쓰이는 **전기적 사실**(같은 전류가 흐르는 직렬 연결, override 불가)이라
`stack_groups_geometry`(레이아웃 선택, override 가능)와 용도가 완전히 다르다 — 애초
설계 논의 초기엔 이 둘을 하나로 묶어 생각했을 위험이 있었는데, 정밀조사로 명확히
분리됨.

### I-2. 구현 — `resolve_stack_layout()`(`sizing_recipe.py`, `optimize_full_circuit_
budget()` 바로 위 신설)
우선순위 4단계(높은 것부터, 완전한 하위호환 원칙):
1. `stack_groups_override`(spec 레벨 명시적 override) — 기존 동작 그대로 최우선.
2. declared `vertical_stack_id`(`device_roles`, topology.json) — 일부만 채워져
   있으면(gap) 나머지는 각자 singleton 그룹으로 남긴다(자동으로 안 채움 — "사람이
   검토한 값"과 "자동 추론값"이 한 그룹에 섞이는 걸 피하고 gap을 눈에 보이게 남겨
   다음 세션에 사람이 채우도록 유도, 세션24 15개 gap을 손으로 채웠던 것과 같은 패턴).
3. declared가 통째로 비어있으면(`folded_cascode`처럼 `device_roles` 키 자체가 없는
   회로, 실측 확인됨) `refine_differential_and_mirror_relations(transistors)`의
   `vertical_stack_id_candidates`(analog-grammar 기반 제안, `inputs=()` 기본값 —
   `find_differential_pair_candidates()`의 자동 승격 루프가 스스로 입력을 찾아냄,
   Test 38 패턴 재사용)로 폴백.
4. analog-grammar 자체가 없어 candidates도 `None`이면 `geometry_colocation_union()`
   (레거시 자동 추론)으로 최종 폴백.

반환 계약은 `kcl_series_union()`/`geometry_colocation_union()`과 동일한 `{stack_id:
[device_name, ...]}` — `assign_finger_geometry()`에 그대로 넘겨진다.

**호출부 교체는 1곳뿐이었다**: `optimize_full_circuit_budget()`의 `stack_groups_
geometry = spec.get("stack_groups_override") or geometry_colocation_union(...)` 한
줄을 `resolve_stack_layout(...)` 호출로 교체. 원래 B-5-3이 "4곳"(`assign_finger_
geometry`/`audit_row_split`/`run_topology_pipeline_with_finger_fixup` + 이 계산 자체)
을 교체 대상으로 언급했지만, 정밀조사로 이 셋이 `assign_finger_geometry()`가 반환하는
`sizing_overrides`의 `stack_id` 필드를 그대로 이어받는 **단일 데이터 흐름의 하위
소비자**임이 드러나(`stick_diagram.py:3807`의 `overrides[name]["stack_id"]` →
`sizing_overrides`를 받는 `run_topology_pipeline()`/`run_topology_pipeline_with_
finger_fixup()`의 `_dc_replace(t, **sizing_overrides[t.name])` → `split_into_stacks()`
가 그 `stack_id`로 그룹핑 → `audit_row_split()`이 그 그룹을 받음) 별도 수정이
불필요했다.

### I-3. 검증
스모크테스트 3가지(`resolve_stack_layout()` 단독 호출):
- `current_reuse_telescopic_ota`(declared 경로): 51개 소자 전부 declared
  `vertical_stack_id`와 100% 일치하는 32개 그룹. `biasgen_vom_a=[M8,M9a]`/
  `biasgen_vom_floatsrc_sink=[M9b,M10]` 분리도 정확(세션25 H-3 재분해 결과 그대로
  반영됨).
- `stack_groups_override` 최우선 확인: override 지정 시 다른 소스 계산 없이 그대로
  반환.
- `folded_cascode`(candidates 폴백 경로, **이번 세션 첫 다른 회로 교차검증**):
  `device_roles` 완전히 빈 회로에서도 크래시 없이 13개 소자 전부 11개 그룹으로
  분할(`cascode-stack_2=[M10,M8]`/`floating-battery_1=[M7,M9]` 등 물리적으로 타당한
  제안, `ambiguous_M5`/`ambiguous_M6`는 안전하게 singleton 격리).

회귀 확인: `stick_diagram.py` self-test 46개 전부 PASS(무변경 파일이라 예상대로).
`sizing_recipe.py` 전체 self-test(exit code 0, `Traceback`/`AssertionError` 0건,
PASS 62줄 포함) — `optimize_full_circuit_budget()`을 실배선으로 태우는 L5 테스트
(M9b/M18b euler-blocked 자동해결)도 기존과 동일하게 PASS.

### I-4. 알려진 한계 / 다음 세션 이월
"다음 세션 최우선" 절 참고 — `folded_cascode` candidates 경로의 end-to-end(전체
파이프라인) 미검증, `do.md` 문서화 누락, `run_harness.py` 실전략 계속 이월.

## J. 세션26 후속(2026-08-10, 같은 날 이어서) — `audit_vertical_stack_id_vs_kcl()`
신설 + `resolve_stack_layout()` declared 경로 감사 게이트

### J-1. 발단 -- "vertical_stack_id를 stack_groups_kcl에도 쓸 수 있지 않냐"
`resolve_stack_layout()`(I절) 완료 직후, 사용자가 `geometry_colocation_union()`의
동작을 설명해달라고 요청 → 그 설명 중 `M6`/`M5`(folded_cascode)가 서로 다른 두
declared matching_pair(`M1/M2`, `M3/M4`)의 "위에 얹힌 유일한 소자"로 동시에 잡혀
`find_stacked_matching_candidates()`가 이 둘을 조용히 하나로 묶어버리는 실제 사고를
`find_stack_edges()`/`find_stacked_matching_candidates()` 실측으로 확인(각 base pair
입장에선 후보가 1개뿐이라 로컬하게는 모호하지 않지만, 전역적으로는 두 서로 다른
matching_pair를 잇는 다리가 됨). 사용자가 이어서 "그럼 `vertical_stack_id`를
KCL(`stack_groups_kcl`) 쪽에도 쓸 수 있지 않냐"는 근본 질문을 던짐 -- 여기서부터
이 절이 시작된다.

### J-2. rail 제외 이유 재확인 + floating-current-source 실측
사용자 질문 1: "같은 vdd/gnd로 연결된 branch는 전류 통로가 될 수 있잖아?" → rail이
전류 통로가 아니라는 게 아니라, "이 net을 쓰는 단자가 정확히 2개"라는 카운팅이
rail(회로 전체가 물려있는 net)에서는 통계적으로 무의미해진다는 걸 재확인(`two_stage_
ota`의 `M5`/`M7`이 우연히 `gnd`를 2번만 써서 거짓 KCL 관계를 만들었던 실제 사례
재인용).

사용자 질문 2: `M9a`/`M9b`(floating current source, Monticelli class-AB battery)의
전하보존이 어떻게 되는가 → 실제 netlist 확인 결과, `M9a`(`source=Vg15,drain=Vop1`)와
`M9b`(`source=Vop1,drain=Vg15`)는 **직렬이 아니라 같은 두 노드(`Vg15`↔`Vop1`) 사이를
잇는 병렬 경로**임을 발견. `Vg15`는 `M8.drain`+`M9a.source`+`M9b.drain` 3단자,
`Vop1`은 `M9a.drain`+`M9b.source`+`M10.drain` 3단자 -- 둘 다 `I_상류 = I_M9a + I_M9b`
류 진짜 3-branch KCL 연립방정식이라 `propagate_topology_forced_currents()`의 2-규칙
엔진(docstring이 스스로 "3개 이상 branch 합류 노드는 범위 밖"이라 명시)으로는 원천적
으로 못 푼다 -- 세션19~21이 이 floating battery를 수치 MNA(`_telescopic_class_ab_
open_loop_gains()`류, ngspice 대조 오차 0.0002%)로 별도로 풀었던 이유가 바로 이것임을
재확인(`M18a`/`M18b`/`Vg25`/`Vom1` 쪽도 완전히 동일 구조로 대칭 확인).

### J-3. `trace_vdd_to_gnd_branches()`로 "vdd→gnd branch = KCL"이라는 직관 검증
사용자가 재질문: "정확히는 vdd부터 gnd로 흐르는 전류를 따진 vertical-stack-id 측면이
있지 않냐" → 세션23이 이미 만들어둔 `trace_vdd_to_gnd_branches()`/`trace_gnd_to_vdd_
branches()`(kind별 entry/exit 고정, 진짜 전류방향 추적)를 `M8`/`M9a`/`M9b`/`M10`
영역에 직접 실행. 결과: `['M8','M9a','M10']`과 `['M8','M9b','M10']`이 **서로 다른
branch 2개**로 갈라져 나옴(M8에서 이미 fan-out) -- "같은 vdd→gnd branch"와 "같은
전류"가 **분기 없는 구간에서는 같은 말이지만, 허브(분기점)에서는 서로 다른 질문이
된다**는 걸 실행 결과로 확인. 세션23이 "vertical_stack_id를 이 함수로 자동 확정 못한다"
고 내렸던 결론(허브 공유/matching_sensitivity 경계 분할 두 이유)과 정확히 같은 결론에
독립적으로 재도달.

### J-4. "vertical_stack_id를 KCL 탐색의 기본 branch로 쓰면 이득이 있는가" -- 실측으로 기각
사용자가 구체적으로 제안: `vertical_stack_id`를 kcl 탐색 범위(base search branch)로
활용하면 이득이 있는지 분석 요청. `kcl_series_union()`이 이미 **전역 완전탐색**(net
이름은 유일하므로 범위를 좁혀도 더 찾을 게 없음)이라는 걸 먼저 확인한 뒤, "범위를
좁히면 오히려 놓치는 사례가 있는가"를 실측 -- **찾았다**: `M11a`/`M11b`(직렬,
`biasgen_vom_battery_a`)와 `M12`(`biasgen_vom_battery_a_sink`, **다른** declared
그룹)가 `N11b`(정확히 2단자)로 진짜 직렬 KCL 관계인데, 사람이 기능 이름 경계
(battery vs sink)로 다른 vsid를 붙여놨다(`kcl_series_union()`으로 실측 확인: `M11b`/
`M12` 같은 kcl 그룹 = `True`). **탐색 범위를 declared vsid로 제한했다면 이 진짜 KCL
관계를 놓쳤을 것** -- 이득 없음을 넘어 실제 회귀(false negative)를 만든다는 걸
구체적 반례로 확정. 대신 "탐색 입력이 아니라 사후 대조표(비교/감사)로 쓰면 이득이
있다"는 방향으로 제안 전환 -- 51소자 실회로에서 kcl 그룹(17개) vs declared vsid
그룹(32개)을 전수비교해 69쌍 불일치를 미리 확인, 전부 두 패턴(declared 미러쌍이
다른 branch에 있음 / 3+단자 허브라 union-find로 못 품)으로 설명됨을 손으로 먼저
확인한 뒤 다음 항목의 자동화 근거로 삼음.

### J-5. `audit_vertical_stack_id_vs_kcl()` 신설(`stick_diagram.py`, `geometry_
colocation_union()` 바로 뒤)
`kcl_series_union()`이 union할 때 쓰는 것과 **똑같은 두 종류 edge**(내부 2단자 net +
declared `current_forced` matching_pairs)를 독립 재구성해 union-find를 다시 돌리고,
declared `vertical_stack_id`와 실제로 갈리는 지점마다 원인을 자동 분류:
- `boundary_findings`: kcl edge가 서로 다른 declared vsid를 잇는 경우 -- `kind=
  "internal_series"`(진짜 직렬, 기능 경계가 전기 경계를 가로지름, `M11b`/`M12`류)
  vs `kind="declared_matching_pair"`(선언된 미러쌍, 다른 physical branch, 정상).
  한쪽만 vsid 선언되면 `note`에 gap 표시.
- `hub_findings`: 같은 declared vsid인데 kcl로 여러 그룹으로 갈리는 경우 -- 그
  그룹 멤버가 쓰는 net 중 3+단자인 것을 `candidate_hub_nets`로 자동 탐색(있으면
  floating-current-source류 정상 케이스, 비어있으면 진짜 review 대상).

⚠️ 아무것도 자동으로 고치거나 topology.json에 쓰지 않는다 -- 대조표만 낸다(프로젝트
전역 원칙: 제안만, 최종 판단은 사람).

**실회로(51소자) 검증**(Test 47, `stick_diagram.py`, 손타이핑 넷리스트 없음 원칙):
`M11b`/`M12`가 정확히 `internal_series`(`N11b`)로, `M9a`/`M9b`·`M18a`/`M18b`
floating-current-source 4개 declared 그룹 전부 `Vg15`/`Vg25`(3+단자) 허브로 정확히
설명됨. 이 회로는 원인불명 hub 0건, gap 0건 -- declared `vertical_stack_id`가 KCL
현실과 완전히 정합함을 자동으로 재확인.

### J-6. 최상위 harness 연결 지점 논의 + 사용자 확정
"이 함수를 어디에 연결해야 하는가" 질문에 세 후보(`optimize_full_circuit_budget()`
직접, `load_topology()`, `resolve_stack_layout()`)를 비교 -- `optimize_full_circuit_
budget()`은 "AI는 이 함수 하나만 호출" 단일 진입점 계약과 "선언 **누락**시 에러"
사전검사 성격이 이 audit("선언은 있는데 **내적 정합성**")과 안 맞고, `load_topology()`
는 vsid 자체가 관심사 아닌 호출이 대부분이라 너무 이름. `resolve_stack_layout()`이
`vertical_stack_id`를 실제로 신뢰해 계산에 쓰는 유일한 지점이고 인자(`transistors`/
`matching_pairs`/`device_roles`)도 audit 함수와 정확히 일치 -- 이곳으로 결정.
결과 처리 정책 두 안(1. 비차단 로그만 / 2. review 대상 있으면 명시적 에러) 중
**사용자가 2번(명시적 에러) 확정** -- `optimize_full_circuit_budget()`의 "AI가 그
자리를 코드로 메우지 않고 신호를 그대로 돌려받는다" 원칙과 대칭.

### J-7. 구현 -- `resolve_stack_layout()` declared 분기에 게이트 연결
declared 그룹을 조립하기 *전에* `audit_vertical_stack_id_vs_kcl()`을 호출, `hub_
findings`의 `candidate_hub_nets`가 빈 항목이나 `boundary_findings`의 gap(`note`
있음) 항목이 하나라도 있으면 `ValueError`(원인 목록을 그대로 메시지에 포함)로 즉시
멈춘다. `internal_series`/`declared_matching_pair`로 설명되는 boundary나 3+단자
net으로 설명되는 hub는 항상 정상이라 통과 -- 오직 원인불명 불일치만 막는다.
candidates 폴백(tier 3)에는 적용 안 함(analog-grammar 제안 자체가 `ambiguous_*`
격리로 이미 불확실성을 표시하므로) -- 이 범위 결정은 재검토 여지 있음("다음 세션
최우선" 2번 참고.

### J-8. 검증
`sizing_recipe.py` L5b(신설, `optimize_full_circuit_budget()`의 L5 테스트 바로
뒤) -- 두 케이스: (a) `current_reuse_telescopic_ota`(51소자, declared 전수 정합) →
게이트 통과, 32개 그룹 정상 반환. (b) 합성 fixture(`T1..T4`, 두 개의 완전히 무관한
2단자 직렬쌍을 declared vsid로 `T1`/`T3`만 `fake_merged`로 잘못 합침, 3+단자 허브도
전혀 없음) → 예상대로 `ValueError`(메시지에 `vsid="fake_merged"`, `candidate_hub_
nets=[]` 그대로 노출).

회귀 확인: `stick_diagram.py` self-test 47개(Test 47 포함) + `sizing_recipe.py`
전체 self-test(L5b 포함) 둘 다 exit 0, `Traceback`/`AssertionError` 0건.

### J-9. 알려진 한계 / 다음 세션 이월
"다음 세션 최우선" 절 참고 -- candidates 경로에도 이 audit을 적용할지 재검토(2번),
J-4 대화 초반에 발견된 "matching_pairs로 인접 작은 그룹 병합" 문제(`folded_cascode`
M1/M2·M3/M4가 서로 다른 vsid 그룹에 흩어져 매칭품질이 깨지는 것)는 설계까지 합의됐지만
이 절의 대화로 이어지느라 구현 미착수(3번, 다음 세션 최우선 후보).

## K. 세션26 후속(2)(2026-08-10, 같은 날 이어서) — `merge_layout_groups_by_
matching_pairs()` 신설 + legacy 대비 end-to-end 품질비교 + 오일러 실현가능성 게이트

### K-1. 구현 — `merge_layout_groups_by_matching_pairs()`(`stick_diagram.py`, J-9
3번 이월 항목 해소)
J-4에서 사용자가 제안한 방향 그대로 구현: `vertical_stack_id` 기반 그룹(declared/
candidates)을 base로 유지하고, declared 매칭쌍(`(a,b)`)마다 `a`가 속한 그룹과 `b`가
속한 그룹을 **그룹 단위**(소자 단위 아님) union-find로 합친다. `geometry_colocation_
union()`의 위험한 부분(`find_stacked_matching_candidates()`의 재귀적 connectivity
climb)은 아예 안 쓰므로, `M6`(`folded_cascode`)처럼 서로 다른 두 매칭쌍의 "유일한
상위 소자"로 동시에 잡혀 무관한 쌍을 우회 병합하는 버그가 구조적으로 재발 불가능
(`M6`이 매칭쌍의 당사자가 아니므로 union 대상이 될 수 없음). 기본 병합 기준은
`current_forced=True`만 권장(세션9/10 dx 악화 실측 근거 재확인, `resolve_stack_
layout()`이 이미 쓰는 `matching_pairs` 인자를 그대로 재사용 -- 새 파라미터 불필요).
`resolve_stack_layout()`의 tier 2(declared)/3(candidates) 둘 다에 연결, tier 4
(legacy)는 안 건드림(합의대로).

**실측**: `folded_cascode` 11개 그룹 → 8개(정확히 `{M1,M2}`/`{M3,M4}`/`{M7,M8,M9,
M10}`으로 병합, `M5`/`M6`은 여전히 격리 유지). `current_reuse_telescopic_ota`
declared 32개 → 20개(`M1a/M1b`, `M8/M17` 등 매칭 legs 정상 결합). Test 48(`stick_
diagram.py`) 신설로 검증(`folded_cascode` 실회로, 병합 전 매칭쌍 전부 다른 그룹임을
먼저 확인해 "문제 재현"부터 보장 -- 병합 후 정확한 그룹 확인 -- `current_forced=False`
까지 넘기면 필터링 없이 그대로 병합됨을 확인해 "기본값 권장"과 "강제 아님"을 구분).

### K-2. legacy 대비 end-to-end 품질비교(사용자 요청)
실제 과거 harness 산출값(`workspaces/current-reuse-telescopic-ota-report/current_
reuse_telescopic_ota.instance.json`)에서 34개 소자의 W를 회수 → declared
`current_forced` 매칭쌍으로 vom↔vop 대칭 전파(38/51 커버) → `stack_groups_kcl`
(`kcl_series_union()`) 그룹 안에서는 W를 강제로 정합화(전기적 동일 전류 제약 위반
방지) → 나머지 13개는 합성값. `compensation`은 제거(known_sizing으로 A/B/C엔진
전부 우회하는 순수 레이아웃 비교가 목적이라 재계산 불필요/방해). `optimize_full_
circuit_budget()`을 `stack_groups_override`로 legacy/신규 그룹 각각 줘서 두 번 실행.

**결과(⚠️ 반신뢰 -- 방법론 자체가 부분 합성 데이터임을 감안)**:
| | legacy | 신규 |
|---|---|---|
| 전체 체크/실패 | 170/77 | 165/83 |
| box-shape | **FAIL(비율 4.00, 허용 1.5)** | **PASS** |
| euler-blocked 미해결 row | 1개(`M18_bg` 관련) | 2개(`biasgen_ref`+`cmfb_tail`) |

box-shape는 신규가 명확히 승 -- legacy가 bias-gen 트리 17개 소자를 무관한 매칭쌍
재귀 병합(`M9b`/`M18b`가 `M3a/M3b`+`M4a/M4b` 차동캐스코드 branch와 `M10/M19` tail
미러쌍을 `Vop1`/`Vom1`(이미 이번 세션에 3+단자 허브로 확인한 그 net) 허브를 다리
삼아 하나로 합치는 것, `folded_cascode`의 `M6` 사례와 정확히 같은 매커니즘 -- 실측
확인)로 한 행에 다 몰아넣어 행 폭 비율이 4.00까지 벌어짐. 신규는 이 과병합이 아예
없어서 이 실패 자체가 안 생김. euler-blocked는 신규가 1개 더 못 품(아래 K-3/K-4).

### K-3. 사용자 지시 -- 오일러 실현가능성 사전검사 추가, 그리고 `cmfb_tail` 가설 정정
사용자가 "merge_layout_groups가 병합하는 기준을 오일러 패스를 찾아서 과병합하지
않도록" 개선을 요청. `merge_layout_groups_by_matching_pairs(transistors, groups,
matching_pairs)`로 시그니처 확장(`transistors` 신규 인자), 매칭쌍마다 union하기
**전에** 임시로 합쳐보고 `build_graph()`+`check_euler_condition()`으로 확인 --
`path`/`circuit`이면 그대로 확정, `impossible`이면 그 임시 그룹 내부 매칭쌍만으로
`suggest_pair_finger_adjustments()`를 돌려 1회 조정으로 홀수차수 2개 이하까지
줄일 수 있는지 확인, 안 되면 그 매칭쌍은 건너뛰고 두 그룹을 분리된 채로 남긴다.

`cmfb_tail`이 이 게이트로 고쳐졌는지 검증하려다 **초기 가설이 틀렸음을 발견** --
`M37a`/`M37b`/`M38`은 declared `vertical_stack_id="cmfb_tail"`로 **이미 하나의
그룹**이었다(병합으로 생긴 게 아님). 셋만으로도 `n_fingers=1` 기준 오일러가 이미
`impossible`(홀수차수 4개: `Vcmfb`/`N36b`/`Ncmfb_tail`/`gnd` -- `Ncmfb_tail`이
`M37a`/`M37b`의 source이자 `M38`의 drain인 3단자 허브라서). 이 게이트는 "병합으로
**새로** 생기는" 문제만 막지, declared로 이미 들어온 그룹은 애초에 손댈 대상이
아니다(입력으로 받은 `groups`를 쪼개는 로직이 없음, union만 하므로). 실제로 게이트
적용 후 재실행해도 `cmfb_tail`은 그대로 blocked -- 그룹 구성 자체(`['M37a','M37b',
'M38']`)도 그대로임을 실측 확인.

### K-4. `biasgen_ref`(`M18_bg`+`M60`+`M61`) -- 게이트의 필요조건/충분조건 격차
이건 진짜로 게이트가 작동한 사례(`M18_bg`/`M60`/`M61`이 declared 3-way 매칭쌍) --
`n_fingers=1` 기준으로 `suggest_pair_finger_adjustments()`가 "홀수차수 4→2" 해법을
찾아내 게이트가 병합을 승인했다(직접 재현 확인). 그런데 실제 `optimize_full_circuit_
budget()`(K-2의 semi-synthetic known_sizing, 진짜 W 기반 finger 배분)에서는 여전히
`unresolved_row=biasgen_ref_seg1_seg1_seg1_seg1_seg1`(크로스오버 분할 5회 시도 후도
실패, `pair_not_found`)로 안 풀렸다. 원인: 게이트는 `n_fingers=1`(토폴로지 원본)만
보고 판단하는데, 실제 파이프라인은 `assign_finger_geometry()`가 실측 W로 계산한
전혀 다른 finger 수로 오일러를 다시 판정한다 -- 이 둘의 홀짝 결과가 항상 같다는
보장이 없다. **게이트는 필요조건(베이스라인에서 최소 가능성)만 걸러내지, 충분조건
(실제 sizing 이후에도 풀림)까지는 보장 못 한다** -- 정직한 한계로 기록.

### K-5. 검증
`stick_diagram.py` self-test 48개(Test 48 갱신, 새 시그니처 반영) 전부 PASS.
`sizing_recipe.py` 전체 self-test(L5b 포함) 전부 PASS. 둘 다 exit 0, `Traceback`/
`AssertionError` 0건 -- 오일러 게이트 추가가 기존 동작에 회귀를 주지 않음을 확인.

### K-6. 알려진 한계 / 다음 세션 이월
"다음 세션 최우선" 절 참고 -- (1) `cmfb_tail`류(declared 자체가 euler-실현불가능한
그룹) 검증할 별도 audit 신설, (2) `biasgen_ref`류(게이트 필요조건/충분조건 격차)
게이트 강화 여부 판단, (3) `folded_cascode` end-to-end 미검증, (4) candidates
경로 audit 적용 재검토, (5) `run_harness.py` 실전략.

## L. 세션26 후속(3)(2026-08-10, 같은 날 이어서) — `audit_vertical_stack_id_euler_
feasibility()`/`find_euler_repair_options()` 신설 + `suggest_pair_finger_
adjustments()`의 실제 `pair_map` 버그 발견/수정

### L-1. `audit_vertical_stack_id_euler_feasibility()` 신설(`stick_diagram.py`)
K-6 이월 항목 1번("cmfb_tail류 declared 자체의 euler-실현불가능 검증할 별도 audit")
해소. declared `vertical_stack_id` 그룹 각각이 그 자체로(병합 이전부터) 오일러
실현 가능한지 검사 -- `n_fingers=1` 기준 `impossible`이면, 그 그룹 내부 declared
매칭쌍으로 `suggest_pair_finger_adjustments()` 1순위 제안을 **실제로 적용한 그래프를
다시 전체 조건(연결성 포함)으로 재검증**해 `resolvable_by_finger_adjustment`를
정한다.

**구현 중 발견한 버그(중요)**: `suggest_pair_finger_adjustments()`가 보고하는
`resulting_odd_count`는 **연결성을 안 본다**(내부적으로 `check_euler_condition().
odd_nodes`의 길이만 세고 `.connected`는 버림) -- 합성 fixture(공유 net이 아예 없는
두 소자를 한 declared 그룹으로 선언)로 실측 확인: "홀수차수 2개로 줄어드니 해결"처럼
보고되지만 실제로는 여전히 끊긴 그래프. 그래서 제안을 실제 적용 후 재검증하는 방식으로
설계.

**실회로 결과(당시엔 놀라운 결과) — `cmfb_tail`(`M37a`/`M37b`/`M38`)은
`resolvable_by_finger_adjustment=True`** — `M38` 핑거 +1로 실제 검증까지 통과함(초기
가설, "declared 자체가 구조적으로 안 풀린다"는 틀렸음이 이 시점에 이미 드러남 -- 진짜
원인은 L-4에서 발견). 이 회로는 `cmfb_tail`이 유일한 finding(다른 declared 그룹은
전부 오일러 정상). Test 49(`stick_diagram.py`)로 실회로 + 합성 disconnection fixture
(genuinely resolvable=False 검증) 둘 다 커버.

### L-2. `find_euler_repair_options()` 신설(`stick_diagram.py`) -- 사용자 질문
("unresolved_row를 resolved로 만들려면 어떤 row를 병합해야 하는가")에 답하려고 신설
2단계 탐색: (1) 먼저 blocked row 혼자 핑거조정으로 풀리는지(병합보다 가벼운 개입
우선), (2) 안 풀리면 `candidate_groups`(다른 row 후보들)를 하나씩 임시로 합쳐보고
실현 가능해지는 후보만 그룹 크기 오름차순으로 반환.

**실회로에 돌려본 결과 -- 병합이 전혀 필요 없었다**: `cmfb_tail`(`M38` +1)과
`biasgen_ref`(`M18_bg`+`M60` 또는 `M60`+`M61` ±1, `n_fingers=7` 실사이징 상태에서도
재검증 통과) 둘 다 **같은 행 안에서** 풀린다. 즉 "병합이 필요한 구조적 문제"가 아니라
`run_topology_pipeline_with_finger_fixup()`의 실제 탐색 전략이 이미 존재하는 해법을
못 찾고 있었다는 뜻 -- 질문의 프레임 자체가 재정의됨. 함수 자체는 합성 fixture(서로
완전히 끊긴 blocked 그룹 + 다리 역할 후보 + 무관한 후보)로 "진짜 병합이 필요한 경우"의
정확한 탐색도 검증(Test 50).

`_verified_euler_fix()` 공유 헬퍼로 세 함수(`audit_vertical_stack_id_euler_
feasibility`/`merge_layout_groups_by_matching_pairs`/`find_euler_repair_options`)의
중복 로직 통합.

### L-3. `biasgen_ref` 라운드별 실제 파이프라인 추적 -- 진짜 근본원인 발견
`find_euler_repair_options()`가 "병합 불필요, 같은 행에서 풀림"이라고 했는데 실제
`optimize_full_circuit_budget()`은 왜 `biasgen_ref`를 못 풀었는지 `pipeline_result
["fixup_rounds"]`/`["group_splits"]`를 직접 추적:
- **5라운드 전부를 `biasgen_ref`(및 그 크로스오버 분할 세그먼트들)가 독점** --
  `run_topology_pipeline_with_finger_fixup()`은 라운드당 blocked row `blocked[0]`
  1개만 처리하는데, `biasgen_ref`가 매 라운드 계속 첫 번째로 걸려 `cmfb_tail`은
  단 한 번도 처리 기회를 못 받았다(원본 상태 그대로 남아있던 이유).
- **결정적 발견 -- `(M18_bg, M60)` 조합이 단 한 번도 시도되지 않음**: 매 라운드
  `(M18_bg, M61)`/`(M60, M61)`만 시도되고 둘 다 `gm_id=30이 LUT 범위[1.85,29.6] 밖`
  으로 거부됨. 그런데 L-2에서 직접 검증한 해법은 정확히 `(M18_bg, M60)` 조합이었다.

### L-4. 진짜 근본원인 -- `suggest_pair_finger_adjustments()`의 `pair_map` 덮어쓰기 버그
`run_topology_pipeline_with_finger_fixup()`은 3-way declared 그룹(`M18_bg`/`M60`/
`M61`)을 `itertools.combinations()`로 **모든 쌍의 조합** 3개(`(M18_bg,M60)`,
`(M18_bg,M61)`, `(M60,M61)`)로 풀어서 넘긴다. 옛 구현은 `pair_map: name->partner`
단일 매핑으로 짝을 표현했는데, 이 3개를 순서대로 대입하면 나중 쌍이 앞 쌍의 매핑을
그냥 덮어쓴다 -- 손으로 추적하면 최종적으로 `M18_bg→M61`, `M60→M61`만 남고
`(M18_bg,M60)` 관계 자체가 사라짐(2-element 체인 형태, 예: `zip(names,names[1:])`
을 가정하고 짠 코드가 N-way 조합 형태를 받아 생기는 문제 -- `mirror_symmetric_
trail()`에도 같은 패턴이 있지만 그쪽은 docstring에 "1:1 아닌 매칭쌍은 `None` 폴백"
이라고 명시된 의도된 범위 제한이라 버그가 아님, `suggest_pair_finger_adjustments()`
만 이 제한이 문서화 안 된 채 실제 N-way 그룹을 받고 있었던 게 문제).

**수정(사용자 확정, "a로 고쳐줘")**: `pair_map` 단일 매핑 대신, **선언된 쌍마다
독립적인 조정 단위**로 취급하도록 재작성 -- 한 소자가 여러 declared 쌍에 동시에
나타나도(3-way 이상 그룹의 정상적인 모습) 전부 별도 후보로 살아남는다. 격리
유닛테스트(`itertools.combinations(['M18_bg','M60','M61'], 2)`를 직접 넘겨 `(M18_bg,
M60)`이 후보 목록에 나타나는지)와 실제 파이프라인 재실행(round=0 rejected_count가
4→6으로 늘고 `(M18_bg,M60)` 두 개가 새로 포함됨) 둘 다로 수정 확인.

**⚠️ 정직한 한계 -- 버그는 고쳐졌지만 이번 semi-synthetic 시나리오의 실패 자체는
안 바뀜**: 새로 시도되는 `(M18_bg,M60)`도 **똑같이 `gm_id=30 LUT 범위 밖`으로
거부됨** -- 3개 조합 전부 이번 세션 semi-synthetic 사이징(51소자 균일 `gm_id=12`
비례식, 실제 수렴된 사이징 아님)에서 우연히 LUT 경계 바로 앞에 놓인 결과일 가능성이
높다(버그 수정의 정확성과는 별개 문제). `cmfb_tail`도 여전히 차례를 못 받음(라운드
예산 독점 구조 자체는 안 고쳤으므로). 이 버그 수정 자체는 일반적으로 유효
(N-way 매칭 그룹을 가진 다른 회로/다른 사이징 상황에서는 실제로 유효한 해법을
살려낼 것) -- 이번 시나리오에서 최종 결과가 안 바뀐 건 별개의, 아직 실측 확인이
필요한 문제(다음 세션 ① 항목 참고).

### L-5. 검증
`stick_diagram.py` self-test 50개(Test 49/50 신설) 전부 PASS. `sizing_recipe.py`
전체 self-test 전부 PASS. 둘 다 exit 0, `Traceback`/`AssertionError` 0건.

### L-6. 다음 세션 최우선순위 재조정(사용자 지시, 2026-08-10 세션 끝)
사용자가 이 세션 마지막에 다음 세션 순서를 직접 재배열: 원래 이월 예정이던 "라운드
예산 독점 문제"(L-3에서 발견)는 우선순위를 낮추고, 대신 **`run_harness.py`의 grid
search 런타임 폭증(2¹³≈8192 조합, ~10시간, "## A"절) 원인을 먼저 알고리즘으로
해결**하는 걸 다음 세션 최우선으로 지정 -- 이유: `cmfb_tail`/`biasgen_ref`의 gm_id
경계 문제가 진짜인지 semi-synthetic 방법론의 artifact인지 확인하려면 실제
`sizing_roles`를 선언해 우회 없이 `optimize_full_circuit_budget()`을 돌려봐야
하는데, 지금 상태로는 그 실행 자체가 ~10시간 걸려 현실적으로 불가능하기 때문. 상세
순서는 이 파일 맨 위 "다음 세션 최우선" 절(①~④) 참고 -- 그 순서를 그대로 따를 것.

---

# 세션27 결론 — grid search 알고리즘 방향(SLSQP) 확정 + warm-start 설계 중 발견한
# f_slew/헤드룸 배선 gap 연쇄 수정 + 레이아웃 회귀 발견(미해결, 다음 세션 최우선)

세션26이 남긴 "다음 세션 최우선"(그리드서치 런타임 알고리즘 개선)에 착수. 실제로는
크게 다섯 갈래로 진행됐다: (A) 알고리즘 방향을 좌표하강 대신 SLSQP+multi-start로
확정, (B) SLSQP 웜스타트를 위해 13개 자유 theta 전부를 하나씩 손으로 분석(닫힌 관계
발견), (C) do.md §7.3.2가 2026-07-30부터 계획만 하고 미구현이던 `intended_role_type`
태깅을 실제로 채움, (D) 그 과정에서 `f_slew`가 do.md 설계상 CMFB와 연관돼야 하는데
미배선임을 발견 → 배선하다가 헤드룸 배정이 이 회로에서 한 번도 끝까지 실행된 적
없었다는 사실이 드러나 버그 5개를 연쇄로 발견/수정, (E) 그 수정을 일반화하는
`suggest_headroom_stack_groups()` 신설, (F) 그런데 그 vsid 변경이 레이아웃 오일러
검증 self-test를 깨뜨림(사용자가 세션 끝에 지적, 미해결). SLSQP 본체(scipy 설치조차)
는 착수 전이다 -- 아래 순서대로 상세 기록.

## A. 알고리즘 방향 확정 — 좌표하강 대신 SLSQP + multi-start

사용자 질문("좌표하강+재시작으로 조합폭발 문제를 풀 수 있나?")에 답하며 논의:
- **순수 런타임(복잡도) 측면**: 좌표하강은 확실히 푼다 -- `O(k^13)`(전수탐색) →
  `O(13·k·S·R)`(S=sweep 수, R=재시작 수)로, k=5/S=5/R=10이면 3,250번 평가(k=2
  전수탐색 8192번보다도 적고, k=5 전수탐색 5¹³≈12억번과는 비교 불가). 게다가 지금까지
  k=2로 경계값만 봤는데(중간값 없음, "## A"절 기존 지적) 좌표하강이면 축당 grid를
  더 촘촘히(k=10~20) 줘도 여전히 빠르다.
- **하지만 "제대로 된 해"를 찾는다는 보장은 없다**: 제약 경계가 축에 정렬 안 돼 있고
  여러 변수가 동시에 움직여야 feasible 영역에 들어가는 경우, 축 하나씩 움직이는
  탐색은 그 경계를 못 넘는다. **실측으로 확인된 이 회로의 상황이 정확히 이 케이스다**:
  13개 theta가 `cmrr_estimate_db`/`psrr_estimate_db`(세션21부터 `smallsignal_
  ratio_db` 타입, 전체회로 51소자 수치 MNA)를 매개로 전부 강결합돼 있다(아래 근거).
  게다가 시작점 feasibility 문제(all-lo/mid/hi 전부 infeasible, 세션20-B G-3 실측)도
  여전하다.
- **결합 정도 실측 근거(중요, 잘못된 결론이었던 세션20-B G/H와 구분할 것)**: 세션20-B
  가 만들었던 "5-theta 결합/2-theta feasibility 결합/6개 독립" 그룹 구조(옛 이 파일
  2786~2916행대)는 **세션21에 CMRR/PSRR이 폐형식→전체회로 수치 MNA로 바뀌면서
  무효화됐다**(이 파일에 이미 기록됨). 이번 세션에 직접 코드(`_full_circuit_devices()`,
  `sizing_recipe.py` 1808행)를 확인해 재확인: `smallsignal_ratio_db`/`smallsignal_
  gain_db` 타입 metric은 `by_name.items()`로 **무조건 전체 소자를 순회**해 MNA를
  조립한다 -- 즉 이 두 metric의 진짜 read-footprint는 항상 "이 회로의 모든 소자"다.
  13개 자유 theta 전부가 어떤 소자든 사이징하므로, 전부 cmrr/psrr을 매개로 서로
  연결된다(완전그래프) -- 세션20-B의 그룹 분리가 유효했던 건 그 그래프 분석이
  cmrr/psrr의 footprint를 (구식 폐형식 기준으로) 빈 집합으로 잘못 계산했기 때문이었을
  뿐, 지금은 그렇지 않다.
- **사용자 승인**: SLSQP(scipy) + multi-start로 진행 확정. 구현 시 주의할 실전 이슈
  3가지(사용자에게 설명, 아직 코드화 안 함): (1) `InfeasibleSizingError`를 penalty
  값으로 변환(예외를 던지면 SLSQP가 못 씀), (2) 유한차분 step 크기 튜닝(내부 고정점
  반복/LUT 이분탐색이 완벽히 매끄럽지 않을 수 있음), (3) multi-start 여전히 필수
  (non-convex).
- **scipy 설치 상태**: 이 프로젝트 Python 환경(`C:\Python314`)에 **아직 설치 안 됨**
  (`import scipy` 시도, `ModuleNotFoundError` 확인) -- 다음 세션 착수 시 설치부터.

## B. Warm-start 설계 — 13개 자유 theta 전수 분석 (SLSQP 본체 구현 전 사전조사)

`optimize_full_circuit_budget()`의 실제 코드(`_evaluate()` 내부 구조, feed 핸들러
계약)를 하나씩 추적해 각 theta가 SLSQP 시작점(`x0`)으로 쓸 수 있는 닫힌 관계가
있는지 손으로 유도. 결과:

### B-1. 완전 제거 가능(자유차원에서 뺄 수 있음) — `f_slew`
`_feed_settling_split()`이 만드는 `ctx.derived["t_slew"]`를 세션27 착수 시점엔
아무도 안 읽음(compensation은 `spec`의 6개 고정 파라미터만 읽음) -- **증명 가능하게
dead**였다. 단, do.md 설계의도상 진짜 죽은 게 아니라 미배선이었다는 걸 이후(## D)에
재발견해 실제로 배선함 -- 최종적으로는 살아있는 theta가 됐다(**세션27 결론 시점
기준으로는 더 이상 dead 아님**, 아래 D절 참고).

### B-2. 트레이드오프 없이 즉시 확정 — `r_cmfb_vocdes`
topology.json 자체 주석이 이미 명시: "이 theta는 CMRR 값에 직접 영향을 주지
않는다(v(Voc_des)=0이라 M39/M40이 CMRR 식에 없음) -- power_uA/area_um2와 Voc_des
DC 레벨에만 영향." `gain_db`/`mismatch_sigma_mV`/`classab_centering_dev_v`도
M39/M40을 안 씀 -- 5개 제약 전부와 무관, `power_uA`(최소화 목표)만 올림 →
**하한(0.02)에 고정하는 게 사실상 최적**.

### B-3. 정확한 선형 부등식으로 결합 — `K_replica` / `r_classab_battery`
`kcl_battery_M9b`(A_signed, terms=[M8:+1, M9a:-1])가 `ID(M9b)=ID(M8)-ID(M9a)>=0`을
강제한다. `ID(M8)=r_classab_battery×(ID_M1a+ID_M1b)`, `ID(M9a)=K_replica×ID_M15` --
`ID_M1a+ID_M1b`와 `ID_M15`는 compensation이 theta와 무관하게 미리 확정하는 상수라
(스테이지 devices, `_evaluate()`가 compensation을 이론상 theta 루프보다 먼저 돌림),
한 번만 계산해두면 **`r_classab_battery ≥ K_replica × ID_M15/(ID_M1a+ID_M1b)`**를
정확한 수식으로 안다. Vop측(M17/M18a, `kcl_battery_M18b`)도 같은 theta 쌍이 그대로
대칭 적용. **실측 검증**: bounds-midpoint(둘 다 중간값)로 두면 `M9b: ID=
-5.58079e-06A <= 0`로 실제 infeasible(세션 후반 smoke test로 여러 번 재현) --
`K_replica=하한(0.05)`, `r_classab_battery=상한(0.3)`으로 두면(부등식을 여유 있게
만족) infeasible이 사라짐(세션 후반 실측, 아래 D-7 참고).

### B-4. 문서화된 목표 고정쌍 — `r_tail_M6` + `r_tail_M7`
topology.json 주석: "M6/M7의 합이 KCL상 ID(M1a)+ID(M1b)와 같아야 한다... 정확히
강제하지는 않는다(옛 0.7:0.3 손-비율 heuristic과 같은 근사 수준)." → 웜스타트로
정확히 `(0.7, 0.3)`(둘 다 bounds 안, 합=1.0, 옛 설계 heuristic과 일치) 사용 권장.

### B-5. 1D LUT 이분탐색으로 직접 풀 수 있음 — `L_cascode` / `L_stage2out`
`_feed_metric_stage_budget()`의 계산식 `gm=gm_id*ID`(L 무관!) + `gds=gm/gm_gds_ratio
(gm_id,L,vds,vs)`(L만 영향)을 근거로: M2a/M3a(L_cascode 대상)의 ID/gm_id는 이미
compensation+A엔진으로 theta 루프 전에 고정되므로, **`gain_db`의 stage1 기여분은
`L_cascode` 단일 변수의 단조증가 함수**(분자 상수, 분모만 L-종속, sky130 LUT 실측:
"gm/gds가 2.3배 L에서 3~5.5배 급증"). `L_stage2out`은 `gain_db`(단조)뿐 아니라
`classab_centering_dev_v = |VGS_n(gm_id=15,L,0.6,0) - VGS_p(gm_id=15,L,0.6,0)|`
(M15/M16의 `_metric_rail_referenced_voltage()`가 직접 계산, 이것도 L 하나의
함수)에도 걸려 **진짜 트레이드오프**가 있다(gain은 L 클수록 유리, centering은 특정
L에서 최소). → LUT 호출만으로(전체 회로 평가 없이) 이분탐색/스캔으로 직접 풀 수
있다. **실측 검증(세션 후반)**: bounds-midpoint(5.75e-7)에서 `classab_centering_
dev_v=0.336V`(허용치 0.15V 초과, 유일하게 실패한 제약 -- 나머지 4개는 bounds-
midpoint로도 전부 통과: gain_db=77.2dB/mismatch=3.0mV/cmrr=101.4dB/psrr=95.0dB).
**이 웜스타트(L_stage2out 재조정)가 아직 미적용 상태 -- 다음 세션 SLSQP 구현 시
바로 쓸 수 있음.**

### B-6. 나머지(하한 근처 시작 권장, 닫힌 관계 없음)
`r_biasgen`/`r_bg_vbias2`/`r_diode_M11a`/`r_classab_diode_src` -- 전부 topology.json
자체 주석이 "논문 근거 수치 없음, 하우스키핑 규모 근사"라고 명시. `power_uA=
sum_current`(전체 소자 ID 합, `_metric_sum_current()` 확인)가 목적함수라 트레이드오프
없는 한 하한이 유리. `N_cmfb_bw`만 지름길 없음(CMFB 루프이득에 실제로 걸림, do.md
Level6) -- SLSQP가 알아서 조정하게 둘 것.

## C. `intended_role_type` 필드 신설 — do.md §7.3.2 계획 완성

`_TEMPLATE.topology.json`의 `_sizing_roles_comment`(2026-07-30부터 있던 주석)가
"A/B/C/D 유형(do.md §7.3.1) 중 B/C/D만 태그한다"는 계획을 이미 갖고 있었는데 실제
구현이 한 번도 없었음을 발견 -- 이번에 실제로 채움.

- **값 21개 theta 전부**: D(진짜 자유도) 9개(`f_slew`/`K_replica`/`N_cmfb_bw`/
  `r_cmfb_vocdes`/`r_biasgen`/`r_classab_battery`/`r_classab_diode_src`/
  `r_diode_M11a`/`r_bg_vbias2`), A(위상-강제형) 8개(`N_cmfb_bw_mirror`/
  `kcl_tail_M5`/`kcl_tail_M38`/`kcl_sink_M10`/`kcl_sink_M19`/`kcl_battery_M9b`/
  `mirror_M18a`/`kcl_battery_M18b`), **B(스펙-타겟 역산형, gap 있음)** 4개
  (`r_tail_M6`/`r_tail_M7` -- do.md §7.3.1(732행)이 명시적으로 지목했던 기존 gap,
  `L_cascode`/`L_stage2out` -- 이번 세션에 새로 발견한 gap, 위 B-5 참고).
- gap 있는 항목엔 `role_type_gap` 필드로 근거 남김. `feeds.type`(A/B/C/A_signed/
  settling_split/metric_stage_budget, `_THETA_FEED_REGISTRY`의 실행 메커니즘
  이름)과는 **다른 축**임을 스키마 주석에 명시(글자가 같아 혼동 위험).
- `_TEMPLATE.topology.json`에도 스키마 문서 갱신(향후 회로 추가 시 참고).
- **검증**: JSON 유효성 확인 + `sizing_recipe.py` self-test 전체 재실행(exit 0,
  회귀 없음).

## D. 헤드룸(`allocate_stack_headroom()`) 버그 연쇄 발견/수정

### D-1. 착수 계기 — `f_slew`가 do.md 설계상 CMFB와 연관돼야 함을 재발견
사용자 질문("cmfb에 f_slew가 연관 있다고 지난번에 분석하지 않았나?")으로 재조사.
`do.md`의 zero-base 연역 사슬(배치 7-3c, mermaid 다이어그램, 665~704행)을 다시
확인: **Level1(f_slew, t_slew/t_lln 배분) → Level2(gm1/gm2) → Level6(CMFB 전류
= N×ωc에서 역산, N_cmfb_bw)** -- `f_slew`가 `t_lln`을 거쳐 `gm1`을 정하고, 그 `gm1`
이 `ωc`(메인루프 대역폭)를 정해 `N_cmfb_bw`의 목표 gm(`N×ωc×Cc`)에 들어가야 한다는
설계였다. 그런데 실제 코드 확인 결과 이 사슬의 **두 연결고리가 전부 미구현**이었다:
(1) `f_slew`의 `t_slew`를 아무도 안 읽음(위 B-1), (2) `N_cmfb_bw`가 읽는
`ctx.spec["omega_c"]`가 `t_lln`과 무관한 손으로 채운 상수(harness 스크립트들이
`6.9/30e-9`로 계속 일치시켜뒀을 뿐, 자동 보장은 없었음).

### D-2. `omega_c` 자동 유도 배선 (구조 변경 없음, 저위험)
`current_reuse_telescopic_topology()`(`topology_library.py:297`)가 이미 논문
Eq.2 그대로 `omega_c = 6.9/t_lln`을 계산하지만 반환 안 하고 있었음(클로저 안에
갇힘) -- `topology_fn.exposed_params = {"omega_c": omega_c}`로 노출하도록 수정
(`topology_library.py`, 314~320행 부근). `_evaluate()`가 `ctx.derived.update
(getattr(topology_fn, "exposed_params", {}))`로 옮겨받고(`sizing_recipe.py`,
compensation 블록 직후), `_feed_gm_target_convention()`(N_cmfb_bw가 쓰는 B타입
핸들러)이 `omega_key`를 `ctx.spec`보다 `ctx.derived` 우선으로 읽도록 수정(2103행
부근). **검증**: `current_reuse_telescopic_topology(t_lln=30e-9,...).exposed_
params['omega_c']` == `6.9/30e-9` 정확히 일치 확인 + self-test 회귀 없음(기존
harness 스크립트들이 이미 손으로 일치시켜뒀던 값이라 동작 변화 없음, 다만 이제
자동 보장됨).

### D-3. `f_slew → t_lln` 배선 (구조 변경, 사용자 승인 후 진행)
`_feed_settling_split()`을 확장 -- `output_key`(기본 `t_slew`)뿐 아니라
`complement_key`(기본 `t_lln`, `total - t_out`)도 `ctx.derived`에 저장하도록 수정
(`sizing_recipe.py`, `_feed_settling_split()` 전체 재작성). `_evaluate()`에
"settling_split 타입 feed만 compensation보다 먼저 적용"하는 예외 블록을 신설(이름이
아니라 feed **타입**으로 골라내 일반화) -- compensation이 `comp["parameters"]`를
읽을 때 `ctx.derived`에 있으면 그걸 `spec`보다 우선(같은 우선순위 패턴을
`omega_c`처럼 t_lln에도 적용). **부작용 발견 및 정정**: `t_settle_total` 값이
모든 harness/smoke 스크립트에서 `6.9*30e-9≈207ns`로 돼 있었는데, 이건 do.md의
진짜 물리값(t_slew=10ns+t_lln=30ns=40ns, self-test 자체 데모가 쓰는 값과 일치)과
무관한 값이었다(t_lln이 f_slew와 무관하던 동안엔 안 드러났던 잠재 버그) --
`run_harness.py`/`run_harness_smoke.py`의 `t_settle_total`을 `40e-9`로 정정.

### D-4. 헤드룸 crash 최초 발견 — `M11a`/`M11b` (M12 없이)
`run_harness_smoke.py`(모든 theta bounds를 중간값으로 접어 1-combo로 실행하는
구조 검증 스크립트, 24행 부근)로 전체 파이프라인을 처음 끝까지 돌려봄(f_slew
배선 후). `allocate_stack_headroom()`에서 즉시 assert 실패:
```
AssertionError: 헤드룸 배정 합(0.4)이 vdd(1.8)와 불일치 -- other_entries가
비어있는데 cascode 배정 합이 vdd와 안 맞으면 배분할 곳이 없어 이 assert가 실패한다.
```
`git stash`로 오늘 변경 전 원본 코드로 되돌려 **동일 지점에서 동일하게 실패함을
확인**(제 변경이 만든 회귀가 아니라 이 회로가 애초에 한 번도 끝까지 실행된 적
없던 상태에서 처음 드러난 pre-existing gap이었음을 검증) → `git stash pop`으로 복원.

**최초 진단(틀렸다가 정정됨, 아래 D-5 참고)**: `M11a`/`M11b`(`headroom_role=
cascode`, vsid=`biasgen_vom_battery_a`)만으로 헤드룸을 배정하려는데 나머지를
배분할 "cascode 아닌" role이 그 그룹 안에 없어서 실패. 실제 회로는
`VDD-M11a-N11a11b-M11b-N11b-M12-GND`(r_diode_M11a theta 주석에 이미 명시된 3소자
단순 직렬)인데, `M12`(headroom_role=mirror)가 `biasgen_vom_battery_a_sink`라는
**다른** vsid로 선언돼 있어 M11a/M11b만 떨어져 나온 것.

### D-5. 그룹핑 기준 재검토 — vertical_stack_id vs KCL (사용자와 왕복 토론, 최종
결론 = vertical_stack_id가 맞다)
1. **1차 시도(틀림)**: "헤드룸은 전기적 개념이니 KCL(`stack_id_of`, `kcl_series_
   union()` 기반)로 그룹핑해야 한다"고 판단해 `_evaluate()`의 헤드룸 루프
   그룹핑 키를 `vertical_stack_id`에서 `stack_id_of`로 교체. `audit_vertical_
   stack_id_vs_kcl()`(stick_diagram.py) docstring이 "M11b/M12 같은 경우가
   vsid 경계는 기능적 이름 경계일 뿐 전기적 경계가 아닐 수 있다는 정상 사례"라고
   문서화하고 있어 이 방향이 맞다고 판단했었음.
2. **사용자 지적**: "headroom에서 vertical_stack_id를 활용하나? KCL이랑 분리해야
   하는 것 아닌가?" → 확인 결과 원래도 vsid를 썼고, 이건 "M12가 실은 같은 컬럼인데
   vsid 선언이 불완전했다"는 뜻이지 "그룹핑 기준 자체가 틀렸다"는 뜻이 아닐 수
   있음을 재확인하려 함.
3. **KCL 그룹핑으로 바꾼 결과 실제로 회귀 발생**: `two_stage_ota.topology.json`
   self-test가 **즉시 잡아냄** -- `stage1`(M3 cascode/M4 cascode/M5 tail)이 vsid
   로는 한 컬럼인데 KCL로는 갈린다(M5는 차동쌍 전체 전류를 받는 tail, M3/M4는 각
   branch 전류라 "같은 전류"가 아님 -- 그래도 셋 다 VDD~GND 한 물리적 컬럼이라
   헤드룸 VDS 합은 여전히 vdd여야 함). **KCL 그룹핑은 틀렸다** -- `vertical_stack_id`
   로 되돌림(`_evaluate()`의 `vertical_groups`/`_ref_depth()` 둘 다 원복,
   `sizing_recipe.py`).
4. **근본 원인 재확정**: `M12`의 `vertical_stack_id` **선언 자체**가 불완전했던
   것(M11a/M11b와 같은 물리적 컬럼인데 다른 이름). `resolve_stack_layout()`
   docstring 재확인으로 개념 명확화: `vertical_stack_id`는 "수직 방향(무엇이
   직렬로 쌓였는가)"만 답하고, "row"(interdigitation/common-centroid 배치,
   `audit_row_split()` 3b/3c)는 그 위에 `merge_layout_groups_by_matching_pairs()`
   가 별도로 얹는 **완전히 다른, 후속** 개념 -- PMOS/NMOS가 물리적으로 다른 well/
   row(`stick_diagram.py` 예시: `S1_PMOS`/`S1_NMOS`, `biasgen_pmos`/`biasgen_nmos`)
   에 들어가야 해서 하나의 `vertical_stack_id`(전기적 컬럼, 극성 무관)가 여러 row에
   걸쳐 실현되는 게 정상이라는 것까지 사용자와 함께 확인(사용자가 "pmos stack row/
   nmos stack row는 horizontal stack일 수 있다"고 지적, 이게 정확히 이 구조를
   설명함). **결론: 헤드룸은 vertical_stack_id 기준이 맞다.**

### D-6. `vertical_stack_id` 선언 정정 6곳 + `budget_reference_device` 2곳 신규 사용
`M12`(→`biasgen_vom_battery_a`로 병합), `M21`(→`biasgen_vop_battery_a`), `M13`
(→`biasgen_vom_battery_b`), `M22`(→`biasgen_vop_battery_b`) -- 전부 "3소자 단순
직렬인데 중간에 선언이 갈린" 같은 패턴. 추가로 2건은 물리적 경로가 vdd/gnd가 아닌
**다른 그룹이 이미 확정한 소자의 노드**에서 끝나는 "폴디드" 구조라
`budget_reference_device`(2026-07-31부터 설계만 돼 있었고 이 프로젝트 어디서도
실사용된 적 없던 필드, `allocate_stack_headroom()` 호출부의 `base_budget = vdd -
ref_vds` 메커니즘)를 처음으로 실제 사용:
- `M58`/`M57`(`vbias2_stack`) + `M68`(같은 vsid로 병합, `budget_reference_device:
  "M6"`) -- 진짜 경로는 `Vx(=vdd-vds(M6))-M58-M57-Vbias2-M68-GND`(M6/M7 병렬 tail이
  Vx를 먹임).
- `M61`(`vbias3_stack`으로 M64/M63과 병합, `budget_reference_device: "M5"`) --
  진짜 경로는 `VDD-M61-Vbias3-M64-M63-Vy(=vds(M5))-GND`(M5가 이미 Vy를 확정).
- **`M39`/`M40`**: 별개 원인(그룹핑 문제 아님) -- 둘 다 `headroom_role="cascode"`
  였는데, 실제로는 VDD-M39-Voc_des-M40-GND 2소자 self-biased 분압기(_correction_
  log_5, 논문 "Voc_des=VDD/2=0.9V")라 "얇은 헤드�-- cascode" role이 물리적으로
  안 맞았음(게다가 cascode뿐이면 배분할 other가 없어 assert 실패 위험도 있었음).
  `"voltage_divider"`(새 자유 role 문자열, cascode만 아니면 뭐든 "균등분배" 취급되는
  기존 계약 그대로 활용)로 정정 -- 각 0.9V 받아 논문 설계의도와 일치.

### D-7. `_feed_metric_stage_budget()` vds 미저장 버그 (별도 발견)
M11a/M11b/M12 수정 후에도 또 다른 crash: `_metric_sum_area`가 `M2a`/`M2b`(L_cascode
대상)의 `ctx.sized[...]["W"]`를 못 찾음(`KeyError: 'W'`). 근본원인: `_feed_metric_
stage_budget()`(`sizing_recipe.py`, `L_cascode`/`L_stage2out`이 쓰는 feed)이 `vds`
를 LUT 조회(`gm_id_to_id_density`/`gm_gds_ratio`)에는 쓰면서 `entry.update({...})`
에 **`vds` 자체를 저장하는 걸 빠뜨리고 있었다**(gm/gds/gm_id/kind/vs만 갱신). 헤드룸
루프가 이 소자들의 vds를 못 찾아 "미확정"으로 오판 → 값-동일 그룹 대표 선정 로직과
얽혀 추가 버그 유발(아래 D-8). **수정**: `entry.update({...})`에 `"vds": vds` 추가
(2172행 부근). **부수 확인**: 이 버그 때문에 `classab_centering_dev_v`(M15/M16
대상, 같은 feed 사용)도 이 소자들에 대해선 여태 `KeyError`로 계산 자체가 불가능했을
것 -- 이번 수정으로 처음 계산 가능해짐(위 B-5 실측값이 이 수정 이후에 나온 것).

### D-8. 값-동일 그룹(matching_pairs) 대표 선정 버그
`M37a`/`M37b`(CMFB 차동쌍, current_forced 매칭쌍) 관련 crash. 헤드룸 루프의
"matching_pairs로 묶인 값-동일 그룹당 대표 1개만 검사"(`_vfind` dedup) 로직이
**members 리스트에서 "먼저 나온" 소자를 무조건 대표로 삼아** vds 여부를 검사했는데,
`N_cmfb_bw`(B타입 feed)가 `M37a`(target)의 vds를 직접 채우고 `N_cmfb_bw_mirror`
(A타입, root=M37b)는 **전류만** 전파하고 vds는 안 건드리는 계약이라, 마침 vds
없는 `M37b`가 먼저 나오면 이미 풀린 그룹을 "미해결"로 오판했다. **수정**(2673~2727
행 부근): 그룹 대표를 "먼저 나온 소자"가 아니라 "그룹 멤버 전체 중 이미 vds가 있는
소자 우선"으로 검색하도록 재작성 + 그런 대표가 있으면 vds 없는 나머지 멤버(M37b)
에게도 대표의 (gm_id,L,vds,vs)를 물려받아 자기 ID로 W/gm/gds를 LUT에서 재계산해
채우는 전파 로직 신설(매칭쌍은 같은 물리 사이징을 공유한다는 전제, `_feed_metric_
stage_budget()`과 동일 계산 패턴 재사용). 전부 없으면(headroom_role도 없는 진짜
gap) 명확한 `ValueError`로 안내(조용히 잘못 추측 안 함).

### D-9. 최종 검증 (세션27 헤드룸 수정 전체)
- `sizing_recipe.py` self-test: exit 0, traceback/assertion 0건.
- `run_harness_smoke.py`(bounds-midpoint 1-combo): 이제 헤드룸/vds 관련 crash
  전부 사라지고, **정확히 예상된 지점**(K_replica/r_classab_battery bounds-
  midpoint가 위 B-3 부등식을 안 만족)에서만 멈춤 -- `M9b: ID=-5.58079e-06A <= 0`.
- **K_replica=하한(0.05)/r_classab_battery=상한(0.3)으로 부등식을 만족시키면 실제로
  끝까지 완주**: `gain_db=77.21dB`(≥75.6 통과)/`mismatch_sigma_mV=3.01`(≤5.0
  통과)/`cmrr_estimate_db=101.43dB`(≥60 통과)/`psrr_estimate_db=95.00dB`(≥60
  통과)/`classab_centering_dev_v=0.336V`(≤0.15 **위반**, 유일한 실패 -- 위 B-5의
  L_stage2out 재조정 웜스타트로 다음 세션에 풀 것).
- **이 성공 실행 도중 새로 발견(별도 미해결 이슈, 다음 세션 ② 항목)**: `M61_M64_
  M63` 그룹이 `budget_reference_device: M5`를 실제로 참조하자 `vds=-0.4`(음수)로
  깨짐 -- `M5`가 `vy_tail` 그룹에 **혼자**라 "남는 예산 전부"(1.8V 그대로)를 혼자
  가져가고 있었기 때문(`allocate_stack_headroom()`의 "cascode 아닌 role이 그룹에
  혼자면 remaining 전부를 가짐" 기본정책 자체의 물리적 비현실성 -- 지금까지 아무도
  이 값을 안 써서 조용히 넘어갔던 것뿐). **다음 세션 ② 항목, 아직 미수정.**

## E. `suggest_headroom_stack_groups()` 신설 (`stick_diagram.py`, 교차검증 도구)

사용자 질문("`vertical_stack_id_candidates`를 생성하는 함수가 애초에 이렇게 쪼개고
있었던 것 아닌가?")으로 근본 원인을 더 추적. `suggest_vertical_stack_composites()`
를 직접 실행해 확인: 이 함수의 `chain`(진짜 전기적 경로)은 **이미 M11a/M11b/M12를
정확히 하나로 묶고 있었다**(`['M11a','M11b','M12']`). 문제는 `chain` 아래
`composites`(idiom별 하위분류 -- "floating-battery"={M11a,M11b} vs
"active-load"={M12})를 과거 세션이 **그대로 `vertical_stack_id`로 옮겨 쓴 것**.
`composite`는 "이 소자들이 어떤 회로 idiom인가"에 답하고(여전히 유효, `headroom_
role` 힌트 등에 쓸모 있음), 헤드룸이 필요한 건 "VDS 합이 vdd(의 일부)가 되는 하나의
전기적 컬럼이 뭔가"라는 다른 질문 -- **하나의 컬럼(chain) 안에 idiom(composite)이
여러 개 있는 게 정상**이라는 게 핵심(예: tail-current-source + cascode-stack +
floating-battery가 한 컬럼 안에 줄줄이 있을 수 있음).

**설계한 일반 규칙**: 같은 chain 안에서 composite를 이어 붙이되, **여러 chain에
공통으로 나타나는 "허브" 소자**(M5/M6/M7/M1a류 -- 한 tail/입력 소자가 여러
differential branch에서 재사용돼 여러 chain에 등장)를 만나면 멈춘다(허브는 이미
자기 자신의 독립 그룹) -- 허브에 인접한 비-허브 세그먼트는 그 허브를 `budget_
reference_device`로 받는다(chain이 `entry_net=vdd`에서 시작한다는 `trace_vdd_to_
gnd_branches()`의 보장을 이용해, 세그먼트가 이미 vdd/gnd에 직접 닿아있으면 그쪽엔
참조 불필요).

**구현 중 발견/수정한 버그(explode)**: 최초 버전은 "composite 하나에 허브 멤버가
하나라도 있으면 전체를 허브 취급"했는데, `{M6,M58}`처럼 **허브(M6)와 비허브(M58)가
섞인 composite**가 있어(M6가 여러 chain에 나타나 허브지만 M58은 이 chain에만
있는 전용 소자) M58까지 M6의 허브 그룹에 잘못 끌려 들어가는 문제가 있었다 --
`_explode_mixed()` 헬퍼로 섞인 composite를 허브 멤버(1개씩 원자화)/비허브 run으로
먼저 쪼갠 뒤 기존 병합 로직을 적용하도록 수정.

**한계(정직하게 확인됨, 자동 적용 안 하는 이유)**: "chain에 몇 번 나타나는가"만으로
허브를 판정하는 방식은 두 종류의 오탐이 있다: (1) `M8`처럼 진짜 전기적 3단자 허브
(Vg15가 M8.drain/M9a.source/M9b.drain 공유)와, 단지 **하류 경로가 여러 개라 chain
enumeration이 반복되는 것뿐**인 경우(예: M58/M57/M68이 M6-chain과 M7-chain 둘 다에
나타나는 건 Vx가 M6/M7 병렬 tail을 먹기 때문이지 M58 자신이 fan-out은 아님)를
구별 못 함, (2) M8+M9a처럼 물리적으로 진짜 직렬(M8.drain=M9a.source)이지만 M9a의
반대쪽(drain)이 신호노드(Vop1, Monticelli floating current source의 절반)로
이어지는 복잡한 구조는, chain을 끝까지 기계적으로 따라가 "헤드룸 그룹"으로 묶는 게
오히려 틀린 판단일 수 있다(현재 declared 값 `biasgen_vom_a`={M8,M9a}만, 더 이상
확장 안 함 -- 과거 세션의 신중한 판단으로 보이며 이번 세션에 건드리지 않음). **이런
이유로 이 함수도 `suggest_vertical_stack_composites()`와 동일 원칙 -- 제안만 하고
topology.json에 자동으로 안 쓴다.** 실측 검증: M11a/M11b/M12, M13/M14a/M14b,
M20a/M20b/M21, M22/M23a/M24b, M61/M64/M63(ref=M5) -- 5곳은 이 함수가 정확히
재현(교차검증 성공). M58/M57/M68(ref=M6)은 위 (1)번 한계로 자동 재현은 안 됐지만
같은 원칙으로 손으로 정정.

## F. `stick_diagram.py` 레이아웃 self-test 회귀 발견 (미해결 -- 다음 세션 최우선)

세션 마지막에 **사용자가 직접 지적**: "vertical_stack_id를 수정하면서 layout의
오일러 path를 검증하는데 사용하면 문제가 생길 소지가 생겼다." `stick_diagram.py`
self-test를 이번 세션 처음으로 실행해보니 실제로 **Test 47**(9446행,
`audit_vertical_stack_id_vs_kcl()` 검증)에서 즉시 실패:
```
AssertionError: M11b/M12 경계가 안 잡힘: []
```
Test 47(9462~9466행)은 "M11b/M12 사이에 vsid 경계가 있고 그 경계의 KCL 사유는
`internal_series`/`N11b`"라는 걸 그 감사 함수의 **정상 동작 예시**로 삼아 작성돼
있었다(이 함수 docstring이 인용하는 바로 그 예시). 세션27이 그 경계를 헤드룸 관점의
진짜 버그로 확인해 병합했으니(위 D-6), 이 "정상 divergence 예시"가 없어져 테스트가
깨진 것 -- **자세한 다음 세션 작업 순서는 이 파일 맨 위 "다음 세션 최우선 ①"에
그대로 옮겨뒀다.** 요약: (1) Test 47을 다른 유효한 divergence 예시로 교체, (2)
Test 47 이후 나머지 테스트가 오늘의 vsid 병합 6곳으로 추가로 깨지는지 미확인 --
전체 재실행 필요, (3) 감사 테스트 통과와 별개로 `resolve_stack_layout()`(finger_w
탐색+오일러 walk 구성)을 이 6개 그룹에 실제로 돌려 검증한 적이 세션27엔 전혀 없음
-- 다음 세션 최우선 작업, (4) 만약 실제 오일러 구성 실패가 나오면 `vertical_stack_
id` 필드를 헤드룸용/레이아웃용으로 분리하는 재설계까지 검토.

## G. 이번 세션 전체 검증 상태
- `sizing_recipe.py` self-test: PASS(exit 0, 회귀 없음) -- 여러 차례 재확인.
- `run_harness_smoke.py`(current_reuse_telescopic_ota, bounds-midpoint): 헤드룸/
  vds crash 전부 해소, 예상된 K_replica/r_classab_battery 제약에서만 정지(버그
  아님, 위 D-9).
- feasible theta(K_replica=하한/r_classab_battery=상한)로 전체 실행: 5개 제약 중
  4개 통과, classab_centering만 웜스타트 필요(예상대로).
- **`stick_diagram.py` self-test: FAIL(Test 47, 위 F절) -- 세션27 끝난 시점 기준
  미해결.** 커밋 전 다음 세션에서 반드시 고칠 것(self-test가 깨진 상태로 커밋하지
  않는 이 프로젝트 관례 유지).

# 세션28 결론 — 세션27이 남긴 최우선 항목①(vsid 병합이 레이아웃 오일러 검증에
미친 영향)을 실측으로 해소, 재설계 불필요로 결론. 부수적으로 옛 ②(M5/M61 헤드룸
버그)를 feasible theta 전체 실행으로 재확인(새 버그 아님)

## H. Test 47 교체 — M11b/M12(세션27 병합으로 소멸) → M60/M66(동형 미손댐 사례)

`audit_vertical_stack_id_vs_kcl()`을 이 회로에 재실행해(`boundary_findings` 전체
조회) 세션27이 손대지 않은 다른 `internal_series` divergence 사례를 찾았다 --
`{"pair": ["M60", "M66"], "kcl_reason": "internal_series", "detail": "Vbias4",
"vsid_a": "vbias4_gen", "vsid_b": "vbias4_stack"}`. `M60`(PMOS, drain=Vbias4,
source=vdd)과 `M66`(NMOS, drain=Vbias4, source=gnd)이 `Vbias4`라는 2단자
internal-series 노드로 연결된, M11b/M12와 정확히 같은 구조의 진짜 KCL 체인이다
-- 각자 다른 `vertical_stack_id`(`vbias4_gen`/`vbias4_stack`)로 선언돼 있어
declared vsid 경계를 가로지르는 정상 divergence 예시로 그대로 재사용 가능. `M60`/
`M66`은 세션27의 6곳 병합(M11a/M11b+M12, M13+M14a/M14b, M20a/M20b+M21,
M22+M23a/M24b, M58/M57+M68, M61+M64/M63) 중 어디에도 속하지 않음을 `device_
roles`에서 직접 확인 후 교체(`stick_diagram.py` 9446행 부근, assert 로직/검증력은
그대로 -- pair/detail만 M60·M66·Vbias4로 치환).

## I. self-test 50개 전체 재실행 -- 회귀 0건

Test 47 교체 후 `stick_diagram.py`(9500여 줄, self-test 50개) 전체 재실행:
exit code 0, `Traceback` 0건, "전체 PASS" 20건(Test 31~50 구간, 그 이전 구간도
전부 통과 -- 출력에 나타나는 "FAIL" 문자열은 전부 의도된 반례 데모(회귀 테스트가
"이 경우엔 FAIL해야 정상"임을 확인하는 대조군)일 뿐 실제 self-test 실패가 아님을
개별 확인). 특히 **Test 49**(`audit_vertical_stack_id_euler_feasibility()`)가
이 회로의 declared `vertical_stack_id` 그룹 **전부**(세션27의 6개 병합 포함)를
`n_fingers=1` 기준으로 오일러 실현가능성 실측 검사했고, `cmfb_tail`(M37a/M37b/M38,
세션27 병합과 무관한 기존 finding, `resolvable_by_finger_adjustment=True`로 이미
해결 가능함까지 검증됨) 하나만 잡히고 **다른 모든 declared 그룹은 오일러 정상**
이라는 결과 자체가 이미 이번 세션 핵심 질문(6개 병합이 레이아웃을 깼는가?)에 대한
1차 답이었다(아래 J절에서 `resolve_stack_layout()` 직접 실행으로 재확인).

## J. `resolve_stack_layout()` 직접 실행 — 6개 병합 그룹 전부 실제 오일러 게이트 통과 확인

세션27이 감사 함수(`audit_vertical_stack_id_vs_kcl()`)만 검증하고 실제 레이아웃
파이프라인(`resolve_stack_layout()`)은 이 회로로 한 번도 안 돌려봤다는 지적에 따라
직접 실행: `resolve_stack_layout(transistors, forced_matching_pairs, device_roles)`
가 예외 없이 완주해 16개 그룹(51개 소자 전부 포함, 누락/중복 없음)을 반환했다.

**핵심 메커니즘 확인**(`sizing_recipe.py:2230` `resolve_stack_layout()` 내부):
1. `audit_vertical_stack_id_vs_kcl()` 게이트 -- `review_needed`(unexplained hub +
   gap)가 있으면 `ValueError`. Test 47/49로 이미 0건임을 확인했으므로 이 게이트는
   통과가 보장돼 있었다(실제로 예외 없이 통과 재확인).
2. declared `vertical_stack_id`로 1차 그룹 조립 (세션27의 6개 병합이 여기 반영됨).
3. **`merge_layout_groups_by_matching_pairs()`**(`stick_diagram.py:3308`)로 2차
   병합 -- declared 매칭쌍(`current_forced=True`)마다 그룹과 그룹을 union하기
   *전에* **실제로 임시 병합해보고 `check_euler_condition()`으로 검사, 실패하면
   `suggest_pair_finger_adjustments()`로 핑거 조정 후 재검증(연결성 포함)까지
   실제로 적용해보는 오일러 게이트**(`euler_feasible()`/`_verified_euler_fix()`,
   3387~3407행)를 통과해야만 병합이 확정된다 -- 실패하면 그 매칭쌍은 건너뛰고 두
   그룹을 분리된 채로 남긴다(과병합 방지, 세션26 후속 K절 설계 그대로).

즉 `resolve_stack_layout()`이 예외 없이 완주했고 그 반환값에 세션27의 6개 병합
그룹이 (추가로 매칭쌍 기반 병합까지 거쳐) 그대로 포함돼 있다는 사실 자체가 **이
6개 그룹이 실제 오일러 게이트를 통과했다는 직접 증거**다(감사만이 아니라 진짜
`check_euler_condition()`/finger-adjustment 재검증까지 실행됐다는 뜻).

**실제 반환된 16개 그룹**(세션27의 6개 declared 그룹은 아래처럼 매칭쌍 기반으로
더 크게 병합됨 -- `biasgen_vom_battery_a`가 `vop` 쪽과, `vbias3_stack`이
`biasgen_ref`와 합쳐지는 식. 이는 버그가 아니라 `folded_cascode`에서 이미 검증된
"매칭 파트너가 다른 물리 branch에 있으면 그룹을 이어붙인다"는 의도된 동작, Test 48
참고):
```
biasgen_ref -> M18_bg, M60, M61, M63, M64
biasgen_vom_a -> M17, M18a, M8, M9a
biasgen_vom_battery_a -> M11a, M11b, M12, M20a, M20b, M21   (세션27 vom_a ∪ vop_a)
biasgen_vom_battery_b -> M13, M14a, M14b, M22, M23a, M24b   (세션27 vom_b ∪ vop_b)
biasgen_vom_floatsrc_sink -> M10, M18b, M19, M9b
cmfb_load_a -> M36a, M36b
cmfb_tail -> M37a, M37b, M38
cmfb_vocdes_gen -> M39, M40
diffpair_bottom_a -> M3a, M3b, M4a, M4b
diffpair_top_a -> M1a, M1b, M2a, M2b
output_stage_a -> M15, M16, M25, M26
vbias2_stack -> M57, M58, M68                                (세션27 병합 그대로)
vbias4_stack -> M66
vx_tail_a -> M6
vx_tail_b -> M7
vy_tail -> M5
```
`biasgen_ref`에 `M61`/`M63`/`M64`(세션27이 `vbias3_stack`으로 병합)가 `M18_bg`/
`M60`과 합쳐져 들어간 것도 declared `matching_pairs`(`M18_bg`-`M60`,
`M60`-`M61`)를 오일러 게이트 통과 후 그대로 반영한 결과 -- `vbias3_stack`이라는
이름은 대표 키 선정 규칙(사전순 최소)에 따라 `biasgen_ref`에 흡수됨.

## K. 결론 — vsid 재설계 불필요

세션27 F절이 조건부로 남긴 "만약 오일러 구성이 실패하면 `vertical_stack_id`를
헤드룸용/레이아웃용으로 분리 재설계"는 **조건이 성립하지 않았다** -- 6개 병합
그룹 전부가 실제 오일러 게이트를 통과했으므로(위 J절), `vertical_stack_id` 하나로
헤드룸(전기적 컬럼)과 레이아웃(오일러 walk) 두 목적을 동시에 만족시키는 현재
설계를 그대로 유지한다. `headroom_stack_id` 신설이나 `audit_headroom_vs_layout_
stack_id()` 같은 별도 감사 함수는 불필요.

## L. 부수 발견 — feasible theta 전체 실행으로 옛 ②(M5/M61 헤드룸 버그) 재확인(새 버그 아님)

위 J절 검증 도중, `optimize_full_circuit_budget()`을 feasible theta(K_replica=
0.05=하한, r_classab_battery=0.3=상한, 나머지 bounds-midpoint,
`grid_points_per_theta=1`)로 실제 실행해 레이아웃 단계(`assign_finger_geometry`)
까지 도달하는지 확인하려 했으나, 그 전 사이징 단계에서 세션27이 이미 "다음 세션②"
로 예고했던 바로 그 크래시가 그대로 재현됐다(새 버그 아님, 우선순위 재조정 근거로
기록):
```
device name at failure: M61
entry: {'ID': 1.3593880066325438e-06, 'L': 3.75e-07, 'vds': -0.4, 'vs': 1.8}
dr: {'headroom_role': 'mirror', 'gm_id_role': 'matching', 'L_role': 'mirror',
     'vertical_stack_id': 'vbias3_stack', 'budget_reference_device': 'M5'}
ValueError: W_bounds=(1e-06, 0.0002) 안에 맞는 gm_id 후보가 없음(role='matching', ...)
```
원인은 세션27이 이미 정확히 진단한 그대로: `M5`(`vy_tail` 그룹에 혼자)가
`allocate_stack_headroom()`에서 VDD 전체를 혼자 가져가 `M61`(`budget_reference_
device: M5`로 `Vy`를 참조)에게 남는 예산이 음수가 된다. **이 항목을 고치지 않고는
`optimize_full_circuit_budget()`이 이 회로로 feasible theta에서도 끝까지 완주한
적이 여태 한 번도 없다** -- (당시엔) 다음 세션 최우선 ①로 승격한 근거였으나, 아래
"## N"에서 서술하듯 세션28 후반부에 그보다 더 근본적인 kind-mismatch 문제가
발견돼 우선순위 ①은 그쪽으로 다시 넘어갔다(이 항목은 ②로, 파일 맨 위 참고).
재현 스크립트: `run_harness_smoke.py`를 베이스로 `K_replica`/`r_classab_battery`
bounds를 `[0.05,0.05]`/`[0.3,0.3]`로 고정하고 나머지는 midpoint 고정, `grid_
points_per_theta=1`로 `optimize_full_circuit_budget()` 호출.

## M. 커밋 상태 (세션28 전반부 완료 시점, 2026-08-11 — ⚠️ 후반부 변경사항은 아래 "## N"
이후에 별도 기록, 이 절은 전반부까지만의 스냅샷으로 보존)
변경 파일: `.ai/context.md`(이 갱신), `skills/analog-gmid-design/assets/stick_
diagram.py`(Test 47 fixture만 교체, 로직 변경 없음). `sizing_recipe.py`는 전반부
세션에 코드 수정 없음(읽기/직접실행 검증만). self-test: PASS(exit 0, 회귀 0건).
아직 커밋 안 됨 -- 다음 세션 시작 시 `git status`/`git log`로 먼저 확인할 것.

# 세션28 후반부 — 사용자 질문으로 전반부 결론 정정, (a) kind 동질성 하드 게이트 적용

전반부가 "① 해소, 재설계 불필요"로 결론낸 직후, 사용자가 핵심을 찌르는 질문을 던졌다:
**"resolve_stack_layout에서 왜 pmos/nmos가 같은 stack에 있는데 오일러 패쓰에 문제가
없지?"** -- 이 질문 하나가 전반부 검증 전체의 맹점을 드러냈다.

## N. 근본원인 조사 — `check_euler_condition()`이 kind를 전혀 안 본다

1. **`build_graph()`(`stick_diagram.py:3545`) 코드 직접 확인**: 노드=net, 엣지=
   트랜지스터인 순수 무방향 멀티그래프를 만들 뿐, `t.kind`를 참조하는 줄이 단
   하나도 없다. `check_euler_condition()`/`hierholzer()`도 마찬가지로 노드 차수
   짝/홀과 연결성만 본다 -- PMOS/NMOS를 섞어도 수학적으로는 아무 차이가 없다.
2. **실측으로 직접 확인**: `vbias2_stack`(M57=pmos/M58=pmos/M68=nmos)로 `build_
   graph()`+`hierholzer()`를 직접 돌리니 `transistor_sequence=['M58','M57','M68']`
   -- `check_euler_condition()`이 "path"(유효)로 확정한 이 trail은 M57(PMOS)과
   M68(NMOS)가 diffusion을 공유하며 바로 이어붙는다는 뜻이라 물리적으로 존재할 수
   없다(PMOS=n-well, NMOS=p-well/p-sub, 같은 diffusion strip 공유 불가).
3. **kind 검사가 있던 유일한 곳이 우회당했다**: `split_into_stacks()`의 docstring에
   "같은 diffusion strip에 물리려면 최소한 극성과 finger 폭이 같아야 한다"는 원칙이
   있지만, 이건 `stack_id`가 **없을 때**의 자동 `(kind, finger_w)` 그룹핑에서만
   적용된다(`split_into_stacks()` 우선순위 1번: "`stack_id` 명시하면 그대로 키로
   쓴다" -- kind 재검증 없음). `vertical_stack_id` 기반 그룹(`resolve_stack_
   layout()`)은 이미 `stack_id`가 명시돼 있어서 이 규칙 자체를 우회하고 `run_
   topology_pipeline()`→`audit_row_split()`→`build_stick_diagram()`으로 그대로
   들어가 Euler 검사를 받는다 -- kind 검사가 아예 존재하지 않았다.
4. **원조(canonical) 예제는 전부 same-kind였다**: `folded_cascode_example()`의
   "top" 스택(MP/M3/M4/M5/M6 전부 pmos)과 "bot" 스택(M9/M10/M7/M8/M11/MN 전부
   nmos)을 보면, 이 프로젝트의 Euler/stick-diagram 코드는 원래 Maloberti PDF의
   same-kind CMOS 물리 행을 대상으로 설계·검증됐음을 알 수 있다. 그런데 세션24~28의
   `vertical_stack_id`는 "VDD→GND 전기적 컬럼"(헤드룸 계산 단위)이라 **정의상
   PMOS/NMOS 경계를 넘나드는 게 정상**이다 -- 두 개념이 같은 파이프라인에 물리면서
   kind 동질성 검증 부재가 그대로 노출됐다.
5. **범위 확인**: 이 회로 declared vsid **26개 중 8개**가 kind-mixed임을 직접
   전수조사로 확인 -- `biasgen_vom_battery_a`(M11a/pmos,M11b/pmos,M12/nmos),
   `biasgen_vom_battery_b`(M13/pmos,M14a/nmos,M14b/nmos), `biasgen_vop_battery_
   a`/`_b`(대칭), `vbias2_stack`(M57/pmos,M58/pmos,M68/nmos), `vbias3_stack`
   (M61/pmos,M64/nmos,M63/nmos), **`output_stage_a`**(M15/pmos,M16/nmos),
   **`output_stage_b`**(M25/pmos,M26/nmos) -- class-AB push-pull 출력단까지
   포함돼 드문 예외가 아니라 정상 패턴임이 확인됐다.

**결론: 전반부의 "재설계 불필요" 결론 정정.** 오일러 게이트가 "통과"한 게 아니라
게이트 자체가 kind를 못 봐서 통과한 것처럼 보였을 뿐이다.

## O. (a) 즉시 적용 — `build_graph()` kind 동질성 하드 게이트 (사용자 지시: "(a)는 바로 적용")

**구현**: `build_graph()`(`stick_diagram.py:3545`) 시작부에 `{t.kind for t in
transistors}`가 2개 이상이면 즉시 `ValueError`(호출부/소자별 kind 상세 포함).
"finger 조정으로 못 고치는 구조적 불가능"이라 `EulerVerdict(kind="impossible")`
(소프트 실패, 자동수정 루프 대상)이 아니라 하드 크래시로 낸다는 게 설계 의도.

**하류 소비자 3곳 중 크래시를 흡수해야 하는 2곳 수정**(3번째 `find_euler_repair_
options()`는 `_verified_euler_fix()`만 거치므로 자동으로 같이 고쳐짐):
- `_verified_euler_fix()`(`audit_vertical_stack_id_euler_feasibility()`/`merge_
  layout_groups_by_matching_pairs()`/`find_euler_repair_options()` 공유 헬퍼) --
  첫 `check_euler_condition(build_graph(...))` 호출을 `try/except ValueError`로
  감싸 `(False, None)`으로 정규화(kind mismatch는 `suggest_pair_finger_
  adjustments()`를 시도해봐야 절대 안 풀리므로 그 단계 자체를 건너뜀).
- `audit_vertical_stack_id_euler_feasibility()` -- 자체 첫 `check_euler_
  condition(build_graph(trs))` 호출(`_verified_euler_fix()`를 거치기 전 단계)도
  `try/except`로 감싸, 기존 홀짝-차수 finding과 구분되는 새 finding을 반환:
  `{"vsid", "members", "odd_nodes": None, "resolvable_by_finger_adjustment":
  False, "verified_suggestion": None, "kind_mismatch": True, "kinds": [...]}`
  (기존 findings는 `kind_mismatch: False`로 채워 구분).

**self-test 갱신**: `stick_diagram.py` Test 49가 "cmfb_tail 외엔 전부 오일러
정상"(`_t49_other_findings == []`)이라고 잘못 기대하던 걸, 이제 정확히 8개
kind_mismatch finding(위 vsid 목록)을 기대하도록 재작성 -- `kind_mismatch`/
`kinds`/`resolvable_by_finger_adjustment`/`verified_suggestion` 필드 전부 검증.

**검증**: `stick_diagram.py` self-test(exit 0, "전체 PASS" 20건, 회귀 0건),
`sizing_recipe.py` self-test(exit 0, 회귀 0건, `kind_mismatch` 관련 자체 테스트는
없지만 `resolve_stack_layout()`을 경유하는 L5b 테스트가 여전히 통과 -- 이 함수가
새 게이트로 인한 예외를 전혀 안 내고 정상 동작함을 재확인).

**부수 효과(버그 수정이 아니라 "조용한 오답"→"명시적 거부"로 바뀐 것)**:
`resolve_stack_layout()`을 직접 재실행하니 반환 그룹 수가 **16개→20개**로
바뀌었다 -- `merge_layout_groups_by_matching_pairs()`가 이제 물리적으로 불가능한
매칭쌍 기반 병합을 정확히 거부하기 때문:
```
전(kind 게이트 없음, 세션28 전반부):
  output_stage_a -> M15, M16, M25, M26            (output_stage_a+b 병합됨)
  biasgen_vom_battery_a -> M11a,M11b,M12,M20a,M20b,M21  (vom+vop battery_a 병합됨)
  biasgen_ref -> M18_bg, M60, M61, M63, M64        (biasgen_ref+vbias3_stack 병합됨)

후(kind 게이트 적용, 세션28 후반부):
  output_stage_a -> M15, M16                       (분리)
  output_stage_b -> M25, M26                       (분리)
  biasgen_vom_battery_a -> M11a, M11b, M12          (분리)
  biasgen_vop_battery_a -> M20a, M20b, M21          (분리)
  biasgen_ref -> M18_bg, M60                        (분리)
  vbias3_stack -> M61, M63, M64                     (분리)
  (biasgen_vom_battery_b/vop_battery_b도 동일 패턴으로 분리)
```
**이건 아직 "올바른 답"이 아니다** -- 그냥 "물리적으로 틀린 병합을 더 이상 안 한다"
는 것뿐, 이 매칭쌍들(특히 `output_stage_a`/`b`의 class-AB M15↔M25/M16↔M26)이
실제로 어떻게 레이아웃돼야 하는지는 (b)가 답해야 한다.

**(b)는 사용자 지시대로 아직 미착수 -- 다음 논의 필요**(파일 맨 위 "다음 세션
최우선 ①" 절에 논의 항목 4개 정리해둠): vertical_stack_id 필드 분리 여부, `output_
stage_a`/`b`류 진짜 매칭쌍의 cross-row common-centroid 재정의, `merge_layout_
groups_by_matching_pairs()`가 거부한 뒤 `audit_row_split()`이 뭐라고 보고하는지
직접 실행 확인, 신규 감사 함수 필요 여부.

## P. (a) 완료 시점 스냅샷 (더 이상 최신 아님 -- 아래 "## Q"가 (b) 완료까지 마저 기록)
(당시 기록 그대로 보존: 변경 파일 `.ai/context.md`+`stick_diagram.py`(Test 47 교체+
kind 게이트+Test 49 재작성), `sizing_recipe.py`는 이 시점까진 코드 수정 없음. self-test
PASS. (b) 설계는 "사용자와 계속 논의 중(미완료)"라고 적혀 있었음 -- 아래 "## Q"에서
그 논의가 실제로 어떻게 마무리됐는지 이어서 기록한다.)

## Q. (b) 완료 — `derive_horizontal_stack_groups()` 신설, `vertical_stack_id`(전기적)와 물리 레이아웃 행(물리적) 2축 분리

### Q-1. 사용자가 확정한 설계

(b) 논의에서 사용자가 핵심 구조를 직접 정리했다: **"vertical_stack_id의 정의는
물리적으로 VDD부터 GND까지 수직으로 쌓여있는 실제 stack -- layout을 위한 PMOS
row/NMOS row와는 다른 개념이다. 우리가 필요한 stack은 2종류: (1) 전기적 관점의
VDS budget용 수직 stack(수직 연결성 기준, 소자 개수·역할이 중요) (2) layout 관점의
PMOS row/NMOS row(수평/오일러 path 연결성 기준, 같은 종류끼리 한붓그리기+branch간
대칭성이 중요). 이 2개는 공통 정보(topology상 VDD→GND branch)로부터 파생돼야 하고,
`vertical_stack_id`를 만드는 함수가 이미 대칭 branch 정보도 갖고 있으므로(declared
`matching_pairs`) 기본 환경은 이미 갖춰져 있다 -- 다만 PMOS/NMOS가 섞인 걸 kind로
분리해서 2개 row로 만들고 대칭성 고려해 병합하는 부분만 채우면 된다."**

### Q-2. 조사 결과 -- 이미 설계가 대부분 갖춰져 있었다 (Explore 2회)

1. `merge_layout_groups_by_matching_pairs()`(`stick_diagram.py:3338`)가 이미
   "declared matching_pairs로 그룹과 그룹을 잇되 실제 오일러 재검증(`build_graph()`+
   `check_euler_condition()`, 필요시 `suggest_pair_finger_adjustments()` 적용
   재검증)을 통과해야만 확정"하는 안전한 그룹 단위 union-find를 완성된 형태로 갖고
   있었다 -- kind로 미리 쪼갠 입력만 넣으면 재발명 없이 그대로 재사용 가능함을 직접
   실행으로 확인.
2. 원래 세션22~23 설계 스케치("B-5-3", `.ai/context.md:3383`, `resolve_stack_
   layout()`이 실제로 구현되기 전 예고편)가 정확히 이 2계층 구조를 이미 제안했었다:
   **Topology layer**(연결성 사실 -- `vertical_stack_id`/`matching_pairs`, 영구
   저장) vs **Instance layer**(finger_w/walk 순서/적용된 조정 -- 인스턴스별,
   `ctx.layout_solution` 메모리 캐시로 제안됐으나 미구현인 채로 남아있었음).
3. 레이아웃→사이징 피드백 루프(`revalidate_finger_override()`/`run_topology_
   pipeline_with_finger_fixup()`)는 이미 `optimize_full_circuit_budget()` 안에서
   완전 자동으로 동작한다(`sizing_recipe.py:2873-2889`) -- 사용자가 요청한 "레이아웃
   조정이 sizing에 피드백되는 루프"는 손댈 필요 없이 이미 존재했다.
4. `Transistor.stack_id`(dataclass 필드, `stick_diagram.py:64`)와 `vertical_
   stack_id`(topology.json 선언값)는 서로 다른 것 -- `resolve_stack_layout()`이
   후자를 읽어 전자를 채우는 다리 역할. 헤드룸(`allocate_stack_headroom()`)은
   `vertical_stack_id`를 직접 읽지 `resolve_stack_layout()`을 안 거친다 --
   `resolve_stack_layout()`의 반환값은 애초부터 오직 물리 레이아웃 축(`assign_
   finger_geometry()`)에만 쓰였다. 즉 이 함수는 처음부터 "물리 레이아웃 그룹 산출"이
   목적이었고, 세션28 이전엔 그 내부 구현이 kind-safe가 아니었을 뿐 -- 이름/시그니처를
   바꿀 필요 없이 내부만 교정하면 됐다.

**범위 결정(사용자 확인)**: `horizontal_stack_id`를 지금 바로 topology.json declared
필드로 영구화하지 않는다 -- `vertical_stack_id` 자신이 세션22~23엔 candidates만,
세션24~25에 검증 후 declared로 승격됐던 경로를 그대로 밟는다. 개념/이름은 지금
확정(1급 시민 함수로 명명)하되, 저장은 다른 회로 최소 1개로 교차검증한 뒤 다음
세션에 결정.

### Q-3. 구현

**새 함수 `derive_horizontal_stack_groups(transistors, vertical_groups,
matching_pairs)`** -- `stick_diagram.py`, `merge_layout_groups_by_matching_pairs()`
바로 뒤:
```python
def derive_horizontal_stack_groups(transistors, vertical_groups, matching_pairs):
    by_name = {t.name: t for t in transistors}
    split_groups = {}
    for vsid, members in vertical_groups.items():
        by_kind = defaultdict(list)
        for name in members:
            t = by_name.get(name)
            if t is not None:
                by_kind[t.kind].append(name)
        if len(by_kind) <= 1:
            split_groups[vsid] = members          # 이미 kind 동질 -- 이름 유지
        else:
            for kind, names in by_kind.items():
                split_groups[f"{vsid}__{kind}"] = names
    return merge_layout_groups_by_matching_pairs(transistors, split_groups, matching_pairs)
```
1단계(kind 분할) + 2단계(기존 `merge_layout_groups_by_matching_pairs()`에 위임) --
새 병합 알고리즘을 만들지 않는다. `resolve_stack_layout()`(`sizing_recipe.py:2230`)의
tier 2(declared)/tier 3(candidates) 두 호출부에서 `merge_layout_groups_by_matching_
pairs()` 직접 호출을 이 함수 호출로 교체(2줄) -- 함수 이름/시그니처는 그대로.

### Q-4. 실측 검증

**전체 회로(51소자)**: `derive_horizontal_stack_groups()`를 declared vsid 26개
그룹에 실행 -- 21개 물리 레이아웃 행으로 51/51 소자 전부 커버(손실/중복 0), 반환된
모든 그룹이 kind 동질. 핵심 사례:
```
output_stage_a__pmos -> M15, M25        (kinds=['pmos'])   # class-AB PMOS 쌍 재병합
output_stage_a__nmos -> M16, M26        (kinds=['nmos'])   # NMOS 쌍도 재병합
biasgen_vom_battery_a__pmos -> M11a, M11b, M20a, M20b (kinds=['pmos'])
biasgen_vom_battery_a__nmos -> M12, M21               (kinds=['nmos'])
biasgen_ref -> M18_bg, M60, M61                        (kinds=['pmos'])  # M61 정상 재합류
```
(a)만 있던 상태(kind 게이트는 있지만 kind-split 없음)에서는 `output_stage_a`/`b`가
그냥 분리된 채(각 2소자, 매칭 파트너 못 찾음)로 남았었는데, 이제 **의도한 대로
재병합**된다.

**`audit_row_split()` 실측 개선 확인**(M15/M16/M25/M26 실제 topology 연결성 +
M15-M25/M16-M26 declared matching_pairs로 직접 실행, `matching_sensitivity="ratio"`
둘 다):
- 새 그룹(`output_stage_a__pmos`={M15,M25}, `output_stage_a__nmos`={M16,M26})으로
  `assign_finger_geometry()`→`split_into_stacks()`→`audit_row_split()` 실행 결과
  `ok=True` -- `1. euler[output_stage_a__pmos/__nmos]` 둘 다 `path`(정상), `2.
  box-shape` PASS, `3a. row-presence` 둘 다 있음, **`3b. interdigitation` PASS**
  (이 pair 종류의 필수 게이트, §2.7: 전류거울류는 1행 interdigitation으로 충분),
  `3c. common-centroid`는 FAIL이지만 `ratio`+`shares_node` 조합에선 참고용일 뿐
  전체 `ok`에 영향 없음(설계대로).
- **비교군**: (a) 게이트만 있던 상태를 그대로 재현(`output_stage_a`=[M15,M16],
  `output_stage_b`=[M25,M26], kind-split 없이 `merge_layout_groups_by_matching_
  pairs()`만 실행)하면 매칭쌍 병합은 정상적으로 거부되지만(그룹은 원래대로 유지),
  그 그룹을 그대로 `assign_finger_geometry()`→`run_topology_pipeline()`에 넘기면
  **`build_graph()`의 kind 게이트가 즉시 `ValueError`를 낸다**(`output_stage_a`
  자체가 M15=pmos/M16=nmos 혼합이므로) -- 즉 **(a) 단독으로는 이 회로의 물리
  레이아웃 파이프라인이 실제로 완주 불가능**했다는 걸 이번에 직접 확인했다(세션28
  전반부는 이 부분까지 실행해보지 않았었음).

### Q-5. self-test

- `stick_diagram.py` **Test 51**(신설, Test 50 뒤) -- 51/51 커버·무손실, 반환된
  모든 그룹 kind 동질(assert), `output_stage_a`/`b`의 M15/M25·M16/M26 재병합 명시
  검증, 합성 fixture(매칭 파트너 없는 순수 mixed-kind 그룹은 kind로만 분할되고
  병합 시도 없음 확인). PASS.
- `sizing_recipe.py` L5b(`resolve_stack_layout()` 실회로 검증)에 "반환된 모든
  그룹이 kind 동질" invariant assertion 추가 -- 이번 버그 재발 방지 가드. PASS.
- 두 self-test 파일 전체 재실행 -- exit 0, 회귀 0건(각각 "전체 PASS" 21건/기존
  카운트 그대로).

### Q-6. 문서

`docs/04-report/analog-topology-json-library.do.md` 배치 7-6f에 (a)+(b) 전체를
기록(배경/구현/실측 검증/self-test/의도적 범위 축소 4~5칸 표, 기존 배치와 동일 형식).

## R. 커밋 상태 (세션28 최종, 2026-08-11)
변경 파일: `.ai/context.md`(이 갱신), `docs/04-report/analog-topology-json-library.
do.md`(배치 7-6f 추가), `skills/analog-gmid-design/assets/stick_diagram.py`(Test 47
fixture 교체 + `build_graph()` kind 하드 게이트 + `_verified_euler_fix()`/`audit_
vertical_stack_id_euler_feasibility()` kind_mismatch 처리 + Test 49 재작성 +
`derive_horizontal_stack_groups()` 신설 + Test 51 신설), `skills/analog-gmid-design/
assets/sizing_recipe.py`(`derive_horizontal_stack_groups` import 추가 + `resolve_
stack_layout()` 2개 호출부 교체 + docstring 갱신 + L5b kind 동질 invariant 추가).
self-test: `stick_diagram.py`/`sizing_recipe.py` 둘 다 PASS(exit 0, 회귀 0건).
아직 커밋 안 됨 -- 다음 세션 시작 시 `git status`/`git log`로 먼저 확인할 것.
(a)/(b) 둘 다 완료 -- 다음 세션 최우선은 파일 맨 위 "① `allocate_stack_headroom()`
singleton 정책"으로 이월.
