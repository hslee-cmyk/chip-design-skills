# 세션 컨텍스트 (최종 갱신: 2026-08-06, 세션18 끝 — 다음은 세션19)

## 작업 디렉토리
`C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills`

## 지금 상태 (다음 세션이 가장 먼저 할 일)

1. **세션12~17 전부 완료 + 전부 커밋됨** — 다음 세션 시작 시 `git log`/`git status`로
   직접 재확인할 것(세션14 교훈, working tree는 `.bkit/` 도구 상태 파일만 변경돼 있어야
   정상). 세션16 커밋: `58e608b`(크래시 수정 + branch 복합 매칭), `7a41a30`(매칭 목적
   핑거증가 L3+L4). 세션17 커밋 3개(시간순): `4bcaafc`(재설계안 3번 완화) →
   `69d9b39`(crossover 짝짓기 우선순위 재작성, D-1) → `4e38aa6`(offset 우선순위 가중치
   + branch composite 사전병합, F/G절).
2. **세션15 A-3에서 발견한 `common_centroid_layout()` 크래시 완전히 원인 확정 + 수정
   완료**(세션16 0번) — `n_fingers<2`(예: 1)일 때 회전-최적 경로가 `count>=N`을 요구해서
   나던 크래시. `repair_matching_safety()`가 `n_rows=min(2, n_fingers)`로 낮춰 탐색
   경로로 우회하도록 수정, 회귀 0줄.
3. **branch 복합 매칭 구현 완료**(세션16 1번) — `matching pair`가 서로 다른 hub를 써서
   (branch_symmetric, 예: M2a/M2b) `interdigitate_layout()`/`common_centroid_layout()`을
   직접 적용 못 하던 사각지대를, 이미 있던 `kcl_series_union()`(세션10)을 재사용해
   "이 소자가 다른 소자와 물리적으로 같은 직렬 컬럼(예: M1a-M2a 캐스코드 스택)을 이루면
   그 branch 전체를 하나의 합성 소자처럼 묶어" 처리하도록 확장(`_branch_composite_pair()`
   등, `stick_diagram.py`). branch 구조 없는 기존 케이스는 완전히 하위호환.
4. **매칭 목적 핑거증가(L3+L4) 구현 완료**(세션16 2번) — branch 복합 매칭으로도 `n_fingers`
   부족(예: 1) 때문에 3c(common-centroid, 허용오차 0.5)를 기하학적으로 못 만족하는 경우,
   "정확히 필요한 만큼만"(`min_fingers`까지) 핑거를 늘리고 `revalidate_finger_override()`
   (L4)로 gm/ID 스펙을 깨지 않는지 재검증하는 오케스트레이션(`run_matching_safety_with_
   finger_growth()`, `sizing_recipe.py`). `current_reuse_telescopic_ota`의 M6 그룹
   실제 사례로 M1a/M1b/M2a/M2b가 전부 `n_fingers=2`로 자라 3b/3c 필수 게이트를 완전히
   통과함을 self-test로 확인(진짜 common-centroid 회전 배치, residual=0).
5. **재설계안 3번(핑거증가도 gm/ID 예산 때문에 안 되면 인접배치로 완화) 구현 완료**
   (세션17, 아래 "세션17 결론" 참고) — `relaxed_pairs`(layout 전용 최후수단, `repair_
   matching_safety()`) + `allow_layout_relaxation`(`run_matching_safety_with_finger_
   growth()`).
6. **crossover 짝짓기 우선순위 재작성 완료**(세션17 E절) — `find_min_crossover_
   layout()`이 `matching_pairs`를 받으면 이제 `_select_crossover_pairing()`으로 후보
   완전짝짓기를 실제로 구성+채점해 matching_pairs 분할이 최소인 쪽을 고른다. M6 그룹
   실측으로 splits=2(옛 tier1) → splits=0(신규)임을 self-test로 확인.
   `matching_pairs=None`(기존 프로덕션 경로)은 완전히 하위호환.
7. **offset 우선순위 가중치 + branch composite 사전병합 구현 완료**(세션17 F/G절,
   같은 세션에 사용자 확인 질문에서 이어서 진행) — (1) `_count_matching_pair_splits()`가
   `pair_sensitivity`를 받으면 `(offset_splits, other_splits)` 튜플로 CMRR 민감한
   offset 쌍을 ratio보다 우선 보호. (2) `find_min_crossover_layout_with_branch_
   composite()` wrapper 신설 — `_branch_composite_pair()`로 branch(캐스코드 컬럼)를
   미리 합성 소자로 뭉쳐서 crossover 짝짓기가 branch를 갈라놓을 수 없게 **구조적으로**
   보장(이전엔 채점 기반 회피일 뿐이었음, 사용자가 이 사각지대를 직접 발견).
8. **세션15 C절(그룹분할을 harness에 배선하는 것) 완료**(세션18, 아래 "세션18 결론"
   참고) — `run_topology_pipeline_with_finger_fixup()`이 핑거조정 실패 시
   `find_min_crossover_layout_with_branch_composite()`(G-3절 wrapper, branch 구조적
   보장 그대로 적용)로 자동 폴백해 euler-blocked row를 그룹분할로 해결한다. C-2(정직한
   표기)는 `group_splits` 필드로, C-3(`cell_groups` 갭)는 `_seg*` 자동확장으로 확정됨
   (둘 다 사용자 확인 후 구현). `sizing_recipe.py`만 수정, **커밋 `a6ab04b`로 완료**.
9. **고아함수 재점검 + 3건 신규 배선 완료**(세션18, 아래 "세션18 결론" G~J절 참고) —
   AST 콜그래프를 `run_harness.py`(진짜 실행 스크립트)까지 진입점에 포함해 재실행(v1→v2→v3,
   클래스 메소드 호출/dataclass 필드 기본값/레지스트리 dict 값이 래퍼 Call로 감싸진 경우
   3가지 사각지대 발견+수정). 실제로 미배선이던 3건을 이번 세션에 배선:
   - `run_matching_safety_with_finger_growth()`(세션16/17 매칭목적 핑거증가+레이아웃
     완화 체인 전체)를 `optimize_full_circuit_budget()`에 배선(구형 `repair_matching_
     safety()` 단독 호출 대체, `lut_by_kind` 없는 legacy spec은 그대로 폴백).
   - `save_instance_json()`을 `run_harness.py`(harness 함수 자신이 아니라 그걸 부르는
     실행 스크립트)에서 `optimize_full_circuit_budget()` 직후 호출하도록 배선("계산은
     harness, 저장은 스크립트"라는 책임분리, 사용자 확인 후 결정).
   - `check_finger_width_compatibility()`(§3.5 — 자기 docstring이 "euler 분석보다 먼저
     통과해야 하는 선행 게이트"라고 이미 선언했는데 실제 호출부가 없었음)를
     `run_topology_pipeline()`에 배선.
   3건 전부 self-test 추가 + 회귀 0줄 확인. **`sizing_recipe.py`/`stick_diagram.py`/
   `run_harness.py` 전부 아직 미커밋.**
10. **diode-stack/`find_diode_stacks()` 설계 논의 — 결론 안 나고 다음 세션으로 이월**
    (세션18, 아래 "세션18 결론" K~L절 참고, **코드 변경 전혀 없음**) — `solve_diode_
    stack_current()`(KVL 루프 전류 역산)는 현재 4개 회로 중 실제로 필요한 곳이 하나도
    없음을 확인(진짜 diode 체인 M11a-M11b-M12조차 결국 자유비율 theta로 풀렸다) — 배선
    여부는 AskUserQuestion을 사용자가 인터럽트해서 **미결**. `find_diode_stacks()`는
    M57/M58이 한때 진짜 매칭쌍으로 **잘못 분류**됐던 실사고 근거로 여전히 유효한 배선
    후보로 재확인. `find_matching_candidates()`의 `current_mirror` 판정(현재 gate만
    보고 source는 전혀 안 봄)에 source-일치 조건을 추가하자는 방안까지 논의가 진행됐으나
    (같은 gate라도 source가 다르면 VGS 동일이 보장 안 됨 — 사용자가 제기, M57/M58 실제
    connectivity로 검증됨) **이건 "진짜 미러인가"를 걸러줄 뿐 "diode 체인 구조 자체를
    인식"하는 `find_diode_stacks()`의 역할과는 별개**라는 데까지 합의(사용자가 재지적) —
    두 검사 다 필요하다는 잠정 결론, 구체적 설계/구현은 다음 세션.
11. **⚠️ 다음 세션 최우선 — "아날로그 기능분석기.zip"/"회로도 추출기.zip" 검토**(세션18
    끝에 사용자가 시작했다가 "이건 다른 세션에서 진행하자"며 명시적으로 중단) —
    `skills/analog-gmid-design/assets/`에 새로 추가된 미확인 zip 파일 2개(아직 열어보지
    않음). 사용자 말로는 "알려진 기능블럭들을 탐지하는 방법론"이 들어있다고 함 — 위 10번
    (diode-stack/current_mirror 오탐 논의, "기능블럭 자동인식"이라는 같은 주제)과 직접
    연결될 가능성이 높다. **다음 세션은 이 zip 파일들 내용부터 확인**하고, 그 내용을 갖고
    10번 논의를 이어갈 것.
12. **`run_harness.py` 재실행 전략은 여전히 미착수**(세션11 A절, 그리드 축소 or 다른
    최적화 방식) — 8/9번으로 L3/L4/그룹분할/매칭성장 체인이 harness 최상위 경로에 전부
    연결됐지만, 실제 전체 사이징 실행(`current_reuse_telescopic_ota`)은 여전히 손 안 댐.

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

## 다음 세션 작업 순서 (권장, 각 단계 사용자 승인 필수)

1. **⚠️ 최우선 — zip 파일 2개 검토**: `skills/analog-gmid-design/assets/아날로그
   기능분석기.zip` / `skills/analog-gmid-design/assets/회로도 추출기.zip`(둘 다
   세션18 끝에 새로 생김, git에 untracked, **아직 한 번도 안 열어봄**). 사용자 말로는
   "알려진 기능블럭들을 탐지하는 방법론"이 들어있다고 함 — 세션18 결론 K/L절(diode-
   stack/`find_matching_candidates()` 오탐 논의)과 같은 주제("회로 기능블럭 자동인식")
   일 가능성이 높으니, 이 zip 내용을 먼저 확인한 뒤 그 방법론을 갖고 K/L절 논의를
   이어갈 것 — 순서를 바꾸지 말 것(zip 안 보고 K/L절부터 구현 설계하면 이미 있는
   방법론과 충돌하거나 중복 설계할 위험).
2. **diode-stack/`find_matching_candidates()` 오탐 필터 설계 마무리**(세션18 결론 K/L절
   이어서, 1번 zip 검토 내용 반영) — 미결 사항: (a) `solve_diode_stack_current()`를
   지금 배선할지 vs 실제 필요한 회로 생기면 할지(K절, AskUserQuestion이 인터럽트돼
   미결), (b) `find_matching_candidates()`의 `current_mirror`에 source-일치 조건을
   추가하는 구체적 코드 설계(L-3/L-4절, M2a/M2b류 대칭쌍을 걸러내지 않게 `find_
   structural_symmetry_candidates()`와 역할을 어떻게 나눌지), (c) `find_diode_
   stacks()`를 `current_mirror`/`hub_merge` 양쪽에 어떻게 연결할지(annotate만 할지,
   구조적으로 배제할지). 이 세 가지 다 아직 코드 한 줄도 안 씀 — 설계 확정 후 구현+
   self-test+회귀.
3. **세션18에서 만든 커밋되지 않은 변경 3건 커밋 여부 확인**: `sizing_recipe.py`(H절,
   `run_matching_safety_with_finger_growth()` 배선)/`stick_diagram.py`(J절, `check_
   finger_width_compatibility()` 배선)/`run_harness.py`(I절, `save_instance_json()`
   배선) — 전부 self-test+회귀 확인 완료 상태로 대기 중. 2번 논의가 끝나 diode-stack
   관련 코드 변경이 생기면 한꺼번에 커밋할지, 지금 먼저 커밋할지 사용자에게 확인.
4. `run_harness.py` 재실행 전략 논의(세션11 A절 — 그리드 축소 or 다른 최적화 방식) —
   L3(핑거조정)+L4(gm/ID 재검증)+그룹분할+매칭성장 체인이 harness 최상위 경로에 전부
   연결됐으니, 이 새 체인들이 실전(`current_reuse_telescopic_ota` 전체 사이징)에서
   어떻게 동작하는지 end-to-end로 확인할 좋은 시점.
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
