# v6.22 계획 수준 항목 P1~P9 독립 분석 (읽기 전용)

- 작성: 독립 분석 agent, 2026-10-20. 저장소 master `512b3c48`, `git -C`만 씀, 파일 수정 없음(이 보고서만 씀).
- 대상: gain-budget 계획 v6.21(`docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, 아래 `GP`), oracle 계획 v0.6.11, offset-strategy 계획 v0.7(`OSP`); design 41 v1.12(`wt/design-it12-window` `7f548040`, 아래 `D41`), oracle design v0.3.3(`wt/design-oracle-eo1`, `ODD`), offset-strategy design v0.2.6(`wt/design-os-ss1`, `OSD`). `E` = `skills/analog-gmid-design/gmid_engine`.
- 판정 원칙: graph 단일 정본(사본·둘째 생산자·새 캐시 금지), DC/AC 분리, gm/ID 손계산 속도와 물리 정합, 상수·규칙 발명 금지, fail-closed, 만들면 배선, 구조 독립, P-1(가장 일반적인 물리 규칙), S-7(계획 먼저), 최소 변경, 작성자≠검증자.
- 줄 번호 한계: 계획의 긴 줄은 한 줄이 문단 하나다. 아래 '현재 문안'은 그 줄 안의 구절이다.

## 요약 표

| # | 사실 확인 | 권고(원칙 모두 충족 시) | 원래 취지 |
|---|---|---|---|
| P1 | **validator 지적이 맞다**(코드로 확인) | keep = `ctx.base`에 `block_version`이 있는 writer ∪ 그 평가의 호출 블록. parent 검사도 같은 writer 집합으로 넓힘. `CONTEXT_WRITERS`를 sizing으로 옮길 필요 없음 | 취지 같음(writer 집합 사실 정정) |
| P2 | 완료 조건 (2)가 O-58 S-1 뒤 문언으로 낡았다 | '창 끝 함수 하나 + writer 셋 열거'로 고침 | 취지 같음(문언 정정) |
| P3 | 같은 해가 칸 셋에 실린다(design). 계획 문언 '두 필드 공유'도 DE-1 전에는 같은 정의의 칸 둘이다 | KVL 고정 포트는 `node.dc_window_cfg` 하나만 정본, `graph.icm_config.kvl` 삭제, 다듬은 창은 그 포트에 쓰지 않음 | **원래 취지와 다름(승인 문언 '두 필드 공유')** -- 사용자 결정 |
| P4 | (a) 규칙 문자 그대로이고 범위를 넓힌 것이 아님 (b) 계획 범위 밖이고 P3 원칙과 충돌 | (a) 계획에 명시 (b) **원칙 충돌 → 사용자 결정** | (a) 같음 (b) 다름 |
| P5 | 커널 A6 b·c는 지금 조용한 대체 | 채택, 계획에 동작 변경 + red 변형으로 등록 | 취지 같음(O-25 (3) 확장), 동작 변경 |
| P6 | DE-1 전에는 '정의 창'이 없다. design의 READS는 θ 프레임 창 | 같은 측정 구성·같은 기준의 커널 창(DE-1 전 `node.dc_window_cfg`) | 취지 같음(문언 정정) |
| P7 | 계획은 A = 0과 `.tf` 실패만 거부한다 | \|A\| ≤ 판정 분해능이면 `unavailable`(N3.8 정의 자리 인용) | 취지 같음(P-1 일반형), 동작 변경 |
| P8 | 선언 입력 DC가 칸 둘에 들어간다 | `dc_sweep.input_dc` 하나 + `input_dc_V` 삭제. **'공칭 점 좌표' 대체를 지우는 부분은 반대**(엔진 정의와 어긋남) | 부분적으로 다름 -- 사용자 결정 |
| P9 | (v, L) 자리가 없다(U17 ② 이월, Q8 열림). kernel 행은 계획 v0.7이 이미 정했다 | 순서 제약 OS-2 > U17 ②(+Q8) 추가. kernel 행은 design 개정만. 469행 표기 정정 | 취지 같음 |

---

## P1. 스냅샷 파생 keep 집합 (O-59 (2))

**사실(코드)**
- `E/sizing/kernel_run.py:69-75`: `base = ctx.base`; parent가 없으면 `snapshot = base`, 있으면 `PLAN_WRITERS` 버전만 base와 같은지 보고 `snapshot = parent.snapshot`.
- 탐색 경로의 `ctx.base`는 S0 수준 스냅샷이다. `E/search/search_context.py:171` `base = dc_ctx.base.widen(S0_WRITERS)`, 그 뒤 `search_domain`·`junction_field`·`mismatch_field`·`model_error_field`·`constraint_classes`·`passive_area_decl`·`metric_structure`·`noise_decl`·`start_intervals`(:172-187), `:205` `dataclasses.replace(dc_ctx, base=base)`. `S0_WRITERS` = `S2_WRITERS ∪ S1V_WRITERS ∪ METRICS_S0_WRITERS ∪ SEARCH_S0_WRITERS`(`E/search/s0_fields.py:40`). 단계 A의 S1 스냅샷도 `GraphSnapshot.empty(S0_WRITERS)`(`E/pipeline/stage_a.py:223`)에서 시작해 `build_s1v`(:238)를 담는다.
- `_CONTEXT_WRITERS` = S1 writer ∪ `PLAN_WRITERS`(`search_context.py:44`). 주석(:43)대로 `context_fp`에 쓰려고 만든 것이다. `build_s1v`·`coupling_vars`·위 S0 탐색 블록·metrics S0 블록은 여기에 없다.
- 결론: 계획 문언(GP:421 N3.3, GP:494 N3.6 4행, GP:1480 범위 4, GP:1486 완료 (11)) 그대로 구현하면 (i) parent 없는 평가가 봉인 4에서 `SEAL_FAIL`로 떨어진다. 스냅샷이 base이고 base에 `search_domain`·`build_s1v` 등의 필드가 있기 때문이다. (ii) parent가 있는 평가의 child에서는 S1v·S0 필드가 지워져, 그 필드를 읽는 봉인 뒤 블록(metric 구조·잡음·mismatch 출처 등)이 입력을 잃는다. **validator 지적이 맞다.**

**θ 무관성 확인**(규칙이 성립하려면 base의 모든 필드가 모든 평가에서 유효해야 한다)
- base는 평가 전에 만든다. `build_kernel_context`(`E/sizing/kernel_context.py`의 `lift_s1`→`dc_rails`→`s1_symmetry`→`dc_current_basis`→`dc_writer_plan`→`dc_scc_order`→`kernel_fields`→`dc_theta_schema`)와 `_s0_blocks`가 만들고, 어느 블록도 평가 θ를 입력으로 받지 않는다. 입력은 topology·spec·LUT·PDK 선언·설정뿐이다. `search_domain`은 θ 상자를 정의할 뿐 θ의 함수가 아니다. 단계 B 필드(`residual_probe`·`dof_numeric`)는 아직 배선되지 않았다(`s0_fields.py` 머리, U17 ②). GB4 필드는 실행 상수다.
- 그래서 지금 코드에서 base 필드는 모두 평가 θ와 무관하고 모든 평가에 유효하다. 규칙이 틀리지 않는다.
- 남는 위험: 앞으로 누가 θ 의존 writer를 base에 쓰면 규칙이 조용히 틀린다. 이를 막는 불변식을 같이 둔다: "base writer ∩ 평가 호출 블록 = ∅(봉인 4가 단언, 위반 = SEAL_FAIL)".

**선택지**
- (가) design 안(`D41` 4.7-3c): `CONTEXT_WRITERS`를 sizing으로 옮기고 keep = 그것 ∪ 호출 블록. 위 (i)(ii) 결함이 그대로다. 기각.
- (나) validator 안: keep = `ctx.base`에 `block_version`이 있는 writer ∪ 이 평가의 호출 블록. 집합은 base 스냅샷에서 읽는다(사본 목록 없음).
- (다) child를 parent가 아니라 base에서 출발하고, 호출 블록 필드만 parent에서 graft. (나)와 결과가 같지만 새 기계(선택 graft)가 필요해 최소 변경이 아니다.
- (라) keep = `S0_WRITERS` 권한표 전체 ∪ 호출 블록. 권한표에는 평가 커널 writer(S2)도 들어 있어(`s0_fields.py` 머리) 낡은 커널 필드가 남는다. 기각.
- (마) **놓친 보완**: (나)를 쓰면 parent에서 넘어오는 base writer 필드가 base와 같은지 확인해야 한다. 지금 parent 검사는 `PLAN_WRITERS` 버전만 본다(`kernel_run.py:72`). 이 검사를 keep의 base writer 전부로 넓힌다(같은 검사의 일반형, 새 규칙 아님, fail-closed).

**원칙 판정((나)+(마))**: graph 단일 정본 충족(집합 = base 자신의 `block_versions`, 사본 없음). fail-closed 충족(parent 검사 확장, 위 불변식 단언). 구조 독립 충족. 최소 변경 충족(`_CONTEXT_WRITERS`는 `context_fp` 전용으로 자리 그대로 두고, sizing 이동·공개 이름이 필요 없다). P-1 충족. DC/AC 무관.

**권고**: (나)+(마).

**계획 문안**
- GP:421 N3.3 현재: "S0 입력 writer(`S1_WRITERS` ∪ `PLAN_WRITERS` -- 정본 = `E/search/search_context.py:44` `_CONTEXT_WRITERS` 정의 인용, 사본 목록 금지; parent 검사로 같음을 확인한 것 -- writer 집합 정밀화, O-59 (2) 뜻 그대로·취지 변경 아님)"
  → 제안: "S0 수준 writer(그 평가의 커널 컨텍스트 스냅샷 `ctx.base`에 `block_version`이 있는 writer -- 정본 = 그 스냅샷의 `block_versions`, 사본 목록 금지; `ctx.base`는 평가 θ를 읽지 않는 블록만으로 평가 전에 만들어지므로 모든 평가에 유효하다. parent 검사는 이 writer 전부의 버전이 base와 같은지 확인한다(옛 `PLAN_WRITERS`만 → 전부, fail-closed). `_CONTEXT_WRITERS`(`search_context.py:44`)는 `context_fp` 전용이고 이 규칙의 정본이 아니다 -- v6.22 사실 정정, O-59 (2) 뜻 그대로)". 같은 문단 끝의 "봉인 4가 '...writer ∈ `_CONTEXT_WRITERS`(...) ∪ 그 평가의 호출 블록'을 단언"도 "writer ∈ base writer ∪ 그 평가의 호출 블록, 그리고 base writer ∩ 호출 블록 = ∅을 단언"으로 바꾼다.
- GP:494 N3.6 4행: "`_CONTEXT_WRITERS`(`S1_WRITERS` ∪ `PLAN_WRITERS`, 정본 `E/search/search_context.py:44`) ∪ 그 평가의 호출 블록" → "`ctx.base`에 `block_version`이 있는 writer ∪ 그 평가의 호출 블록(두 집합은 서로소)".
- GP:1480 범위 4: 같은 치환. 착수 실측에 "parent 없는 평가 스냅샷(= base)의 writer 목록"을 더한다.
- GP:1486 완료 (11) (a) 현재: "S1·계획 필드(`_CONTEXT_WRITERS` writer)는 child에 남음" → "base writer 필드(S1·S1v·계획·S0 탐색·metrics S0)는 child에 남음, parent 없는 평가가 봉인 4를 통과함(지금 문언으로 구현하면 red)". (b)에 "base writer ∩ 호출 블록 ≠ ∅ 픽스처가 FAIL"을 더한다.
- 반영 대상: `D41` 4.7-3c의 'CONTEXT_WRITERS 정의 자리' 항목 삭제, keep 식 교체. `OSD` 129행(스냅샷 파생 규칙 영향)의 keep 표기도 갈아야 한다.

## P2. IT-2 완료 조건 (2) 대 O-58 S-1

**사실**: GP:1486 (2) "입력 CM 창을 계산하는 곳이 `block_columns`(정본 함수 `saturation_window`) 하나". 그런데 O-58 S-1(GP:1477 범위 1)은 writer를 둘로 정했다. `dc_columns`가 θ 프레임 창 `node.dc_window`를 쓰고, 봉인 뒤 블록(`D41` 4.7-3b `icm_config`, 파일 `E/metrics/icm_config.py`)이 측정 구성 판정 창을 쓴다. 다듬은 창 블록(`E/sizing/window_refine.py`)도 창을 계산한다. 그래서 (2)의 '`block_columns` 하나'는 승인된 범위 1과 모순되는 낡은 문언이다. 그대로 두면 test 작성자가 `icm_config`를 위반으로 판정한다.

**선택지**: (가) 문언을 '창 끝 함수 하나 + 부르는 자리 열거'로 고친다. (나) `icm_config`도 `block_columns` 안에 둔다. 이는 층 순서와 맞지 않는다(O-58 S-1이 기각한 (다)안과 같은 꼴). 기각.

**원칙**: (가)가 단일 정본(함수 하나), 최소 변경, S-7을 모두 충족한다. 확인할 점 하나가 있다. `D41` 4.7-3b (4)는 "끝 = `saturation_window`의 끝 정의"라고 적어, 함수를 부르는지 식을 다시 쓰는지가 모호하다. **함수를 호출해야 한다**(식 재구현은 둘째 생산자다).

**문안**: GP:1486 (2) → "`git grep`으로 `ls_swing`의 입력 창 계산 자리 0 -- 입력 CM 창 끝을 내는 함수는 `saturation_window` 하나(끝 풀이는 `_refine_ends` 하나)이고, 부르는 자리는 셋이다: `dc_columns`(θ 프레임 창), 봉인 뒤 측정 구성 블록(측정 구성 판정 창, O-58 S-1), 다듬은 창 블록. 그 밖에서 창 끝 식을 다시 쓴 자리는 0(`headroom_bound.py`는 다른 개념이라 제외)". 취지 같음.

## P3. KVL 고정 출력 선형 끝의 칸 셋

**사실**: GP:566(N3.8)은 "측정 구성 판정 창과 다듬은 창이 같은 연립 결과를 쓰면 그 연립은 평가마다 한 번 풀어 두 필드가 공유한다". `D41` 4.7-3b는 그 해를 `graph.icm_config` 칸 `kvl`에 쓰고, `node.dc_window_cfg`에도 쓰며, `dc_window_refine`이 그 칸의 끝을 `node.dc_window_def_refined`로 옮긴다. 같은 값이 세 칸에 실린다. `kvl` 칸의 소비자는 `dc_window_refine` 하나다.

**물리·정의 점검**: 계획은 KVL 고정 구조에서 커널 창과 다듬은 창이 **모두** 같은 선형 감도 끝('추정')이라고 정했다(GP:1477 범위 1). DE-1 전에는 두 창의 기준이 모두 '+tol'이다. 따라서 DE-1 전 KVL 포트에서는 판정 창과 다듬은 창이 같은 정의·같은 정밀도·같은 기준의 양이다. 계획 자신의 규칙 '다른 정밀도·다른 기준은 다른 이름'의 역, 그리고 graph 규칙 3(같은 정의의 양 두 칸 금지)에 따르면 그 포트에서는 칸이 하나여야 한다. 계획 문언 '두 필드 공유'도 이 규칙과 충돌한다.

**선택지**
- (가) design대로 칸 셋. 사본 둘이다. 기각.
- (나) 계획 문언 그대로 칸 둘(`dc_window_cfg` + `dc_window_def_refined`). DE-1 전 KVL 포트에서는 사본이다.
- (다) KVL 고정 포트의 정본 = `node.dc_window_cfg` 하나. `graph.icm_config.kvl`을 지우고(구조 분류는 `graph.icm_config`의 기존 칸으로 나타냄), 다듬은 창 블록은 그 포트에 쓰지 않는다. front·보고 metric은 그 포트에서 `dc_window_cfg`를 읽는다. 어느 쪽을 읽을지는 graph에 이미 있는 구조 분류로 정한다(새 규칙 아님). DE-1 뒤에는 정의 기준 창이 측정 구성 블록의 `node.dc_window_def`(`D41` 4.7-3b writer 자리)이므로, KVL 포트의 정의 기준 값도 그 칸 하나다.
- (라) `kvl` 칸만 지우고 칸 둘(= (나)).

**원칙**: (다)만 단일 정본, 재계산 0, 최소 생산자를 모두 충족한다. 대가로 front 소비자가 포트 구조에 따라 읽을 칸을 고른다. 그러나 그 선택 근거가 이미 graph에 있으므로 새 상수·규칙이 아니다. fail-closed와 정확도 '추정' 표기는 유지된다.

**권고**: (다). 단 승인된 문언 '두 필드가 공유'를 바꾸므로 **원래 취지와 다름(문언) -- 취지(정본 하나·재계산 0, O-58 S-1·S-2)와는 같음, 사용자 결정 필요**.

**문안**: GP:566 "...같은 연립 결과를 쓰면 그 연립은 평가마다 한 번 풀어 두 필드가 공유한다(재계산 0, 정본 하나 -- O-58 S-1·S-2)" → "...그 연립은 평가마다 한 번(측정 구성 블록) 풀고 그 끝은 측정 구성 판정 창 한 칸에만 쓴다. KVL 고정 포트에서는 다듬은 창이 같은 정의·정밀도·기준의 양이므로 따로 쓰지 않고, front·보고는 그 칸을 읽는다(구조 분류 = 측정 구성 블록 출력; 그 해를 담는 다른 칸 금지; DE-1 뒤 정의 기준 값도 측정 구성 블록의 정의 창 한 칸 -- 재계산 0, 정본 하나, O-58 S-1·S-2)". GP:1486 완료 (5)·(8)(d)·(10)(d)에 "KVL 끝을 담는 칸 = 1(`git grep`)"을 더한다.

## P4. design as-built 두 가지

**(a) G_vgs 밖 고립 입력 포트를 다중 뿌리 정지에 셈**(`D41` 4.7-1 5)
- 사실: 쓰기 계획은 그 넷을 W4 y 키 = 넷으로 쓴다(`D41`이 인용한 `writer_plan.py:236-238`). 계획 IT-1 범위 4(GP:1415 부근, IT-Q1 (나) GP:1445)는 "입력 포트인 W4 뿌리가 둘 이상이면 정지"다. 고립 포트도 문자 그대로 '입력 포트인 W4 뿌리'다. **범위를 넓힌 것이 아니라 계획이 그 경우를 명시하지 않았을 뿐이다.**
- 물리: 그런 포트는 게이트·소스·저항 어디에도 닿지 않는다. 회로가 DC를 정하지 않으니 사용 환경이 정할 DC다(예: 용량 결합 입력). 뿌리가 둘이면 y가 둘이다. 정지가 fail-closed로 맞다.
- 권고: 계획 범위 4에 "G_vgs 밖 고립 입력 포트(쓰기 계획이 W4 y 키 = 그 넷으로 쓰는 포트)도 입력 포트인 W4 뿌리로 센다"를 명시하고, 코퍼스 발동은 IT-0 M-I1이 잰다. 취지 같음(문언 명시).

**(b) F 성분의 입력 DC 미선언 포트에 자기 x 창**(`D41` 4.7-3 3 (나))
- 사실: 계획 범위 1 (c)(GP:1477)는 '입력 DC 선언 포트(F)'만 다룬다. (나)는 계획 밖이다(S-7 위반 -- design이 먼저 정함).
- 원칙 충돌: 계획 O-49 P3(같은 GP:1477)은 "한 포트만 움직이고 다른 선언 포트를 고정하면 차동 입력이 생겨 공통모드 창이 아니다"라고 정했다. (나)는 그 포트 하나만 x로 움직인다. 그러면 다른 입력 포트(뿌리 성분의 포트 등)가 고정된 상태라 ICMR 정의(O-25 (2) 공통모드 훑기)와 어긋난다. 또 그 포트는 회로가 트리 경로로 DC를 정하는 노드다. 바깥에서 고정하면 쓰기 계획(그 노드의 writer)이 바뀐다. 이것은 "이 포트가 무엇이냐"는 회로 해석 문제다.
- 선택지: (1) design대로 자기 x(P3와 충돌) (2) P-1 일반형: 측정 구성이 묶지 않은 모든 입력 포트를 같은 x만큼 함께 움직인다(뿌리 포트는 y, 선언 포트는 선언값 + x, F 성분 미선언 포트는 해의 값 + x). 이 경우 그 포트 노드의 writer가 바깥 구동으로 바뀌므로 쓰기 계획 개정이 필요하다. (3) 그런 포트가 있으면 정의 불능 + 사유 기록(fail-closed, 발동 회로가 들어올 때 구현 -- DEC-76과 같은 처리).
- 판정: (1)은 P3·O-25 (2)와 충돌한다. (2)는 물리 일반형이지만 쓰기 계획을 바꾸는 회로 해석이 들어가 사용자 공동 분석 대상이다. (3)은 모든 원칙을 충족하는 안전한 기본안이지만 heldout r2r_opamp 꼴에서 metric이 정의 불능이 된다.
- **원칙 충돌로 올림 -- 단일 권고 없음.** 원칙상 기본안은 (3)(DEC-76 선례, fail-closed, 계획 밖 동작 금지)이고, (2)는 회로 해석 공동분석 뒤 결정한다. design의 (나)는 계획이 정할 때까지 빼야 한다. **원래 취지와 다름(design이 계획 범위를 넘음).**

## P5. 커널 되풀이 미수렴·tol 미정 → `unsettled` → metric 정의 불능

**사실**: 지금 동작은 A6 b(tol 미정이면 한 번만 적용)와 A6 c(`k_max` 소진이면 마지막 창을 그대로 씀, 수렴 표시 없음)다(`E/sizing/block_columns.py:719-733`, `D41` A6 행). 이는 수렴하지 않은 값을 수렴한 값처럼 쓰는 조용한 대체다. 계획의 fail-closed는 다듬은 창 (iii)~(v)(GP:1477)와 O-25 (3) '창 끝 풀이 실패는 fail-closed'만 말한다. 커널 되풀이에 대해서는 말하지 않는다.

**판정**: fail-closed·N3.14 공통 실패 규약·O-25 (3)의 일반형(P-1)이다. y 범위로는 계속 써서 탐색이 그 점을 평가하게 두므로(`D41` 4.7-3 1), 손계산 속도도 해치지 않는다. 다만 이것은 **동작 변경**이다(지금은 값이 나옴). 그리고 발동률이 미측정이다(`D41` 804행). 발동률이 높으면 ICMR 제약 회로에서 front가 비게 될 수 있다.

**권고**: 채택. S-7에 따라 계획에 먼저 적는다. 문안(GP:1477 범위 1 '끝 풀이 규칙' 뒤): "커널 창 되풀이(`_solve_input_window`)가 `k_max` 안에 tol 안으로 수렴하지 않거나 tol이 미정이면, 그 창은 y 범위로만 쓰고 그 창을 읽는 metric·커널 ICMR 제약은 정의 불능(사유 `input_window_unsettled`)이다 -- O-25 (3)의 커널 쪽 적용, 동작 변경(N4 0번)". GP:1486 (6)에 동작 변경 항목을 더하고, red 변형 "커널 되풀이 미수렴 toy·tol 미정 toy"와 착수 실측 "library 9회로 발동률"(card 0)을 더한다. 취지 같음.

## P6. DE-1 전 다듬은 창의 출발 창

**사실**: GP:1477 "writer = 수락 반복·front에서만 도는 별도 블록, 입력 = 정의 창". 정의 창 `node.dc_window_def`는 DE-1 (a)가 만들고, 이 card는 만들지 않는다(`D41` 4.7-2 표 '예약'). 그래서 DE-1 전에는 입력이 존재하지 않는다. `D41` 4.7-4의 READS는 `node.dc_window`(θ 프레임 창)다.

**판정**: 다듬은 창은 측정 구성(follower·선언 되먹임)에서 잰다(GP:1477 '측정 구성'). θ 프레임 창은 측정 구성이 없는 다른 구성의 창이라, 그 끝은 다른 해 계열의 x다. 같은 개념·같은 기준에서 출발하려면 DE-1 전에는 측정 구성 판정 창(+tol, 다듬은 창 기준 칸 '+tol 판정 기준'과 같음)이 맞다. DE-1 뒤에는 정의 창이다. 이 선택은 P3의 '같은 측정 구성·같은 기준 칸 하나' 규칙과도 일관된다. 새 규칙이 아니다(계획의 '같은 개념·정밀도', O-21).

**권고**: GP:1477 "(writer = ..., 입력 = 정의 창 -- `node.dc_v`는 읽지 않는다...)" → "(writer = ..., 입력 = 같은 측정 구성·같은 기준의 커널 창 -- DE-1 전 측정 구성 판정 창(`+tol`), DE-1 뒤 정의 창; θ 프레임 창 `node.dc_window`와 `node.dc_v`는 읽지 않는다...)". `D41` 4.7-4 READS를 `node.dc_window` → `node.dc_window_cfg`로 고친다(design 개정). 취지 같음(문언 정정).

## P7. oracle DV-14: 0이 아닌 작은 |A|

**사실**: `ODD` 1580(DV-14), 1749(§21.5 4단계). 계획 N3.9 `offset_in_sigma_mv` 행은 'A = 0·`.tf` 실패 = `unavailable`'만 정한다. 판정 분해능의 정의 자리는 GP:566 N3.8 하나다. 그 정의는 "N3.8 '감도 게이트' ε를 그 DC 전달에 적용한 값, 새 상수 없음; oracle `.tf` 쪽은 같은 정의를 인용"이다. 반전 입력 식별은 이미 '전달 크기 ≤ 판정 분해능 = 정의 불능'(O-53 A-1)이다.

**판정**: A = 0은 |A| ≤ 분해능의 특수한 경우다. 분해능 이하의 A로 나눈 σ_in은 수치적으로 정해지지 않은 값이다(물리 정합 위반). P-1 일반형, fail-closed, 상수 발명 없음(정의 자리 인용)을 모두 충족한다. 동작 변경이지만, 바뀌는 값은 원래 무의미하던 값뿐이다.

**권고**: oracle 계획 N3.9 `offset_in_sigma_mv` 행 현재 'A = 0·`.tf` 실패 = `unavailable`' → "\|A\| ≤ 판정 분해능(정의 자리 = gain-budget N3.8 '판정 분해능의 정의 자리', 인용) 또는 `.tf` 실패 = `unavailable`(사유를 나눠 기록: `tf_failed` / `transfer_unresolved`; A = 0은 앞 갈래에 포함) -- 동작 변경, 차동 비트 동일 조건의 예외는 이 갈래가 발동한 회로뿐이고 발동 회로를 변화표에 적는다". 엔진 쪽 σ 입력 환산(DEC-23 A_dc)에도 같은 규칙이 있는지 확인하는 일을 같은 개정에 더한다(엔진·oracle 한 정의). 취지 같음.

## P8. oracle DV-15: 입력 DC 두 칸

**사실**: `ODD` 841 `/swing_icmr {..., input_dc_V?, input_dc_pending?}`, 1712 "`icm_margin_v` = min(V_icm − lo, hi − V_icm), V_icm = `input_dc_V`가 있으면 그 값, 없으면 공칭 점 좌표, `input_dc_pending`이면 내지 않음". 새 `dc_sweep.input_dc`(넷별 선언 입력 DC)도 같은 spec 선언에서 온다.

**판정**
- 선언 입력 DC가 두 칸에 실리는 것은 사본이다(graph 규칙 3 일반형). 정본은 넷별 선언(`dc_sweep.input_dc`) 하나가 맞다(스칼라는 그것의 사영으로 유도할 수 있다). `input_dc_V` 삭제에 동의한다. `input_dc_pending`도 선언 상태의 사본이면 같은 이유로 삭제한다. 그 뜻(선언 보류)은 `input_dc` 칸의 있음/보류 표지 하나로 옮긴다. 의미는 착수 때 확인해야 한다(이 분석은 칸 뜻을 1712행 문언으로만 확인했다).
- **'공칭 점 좌표' 대체 삭제에는 반대한다.** 입력 DC 미선언 회로에서 공칭 점의 입력 좌표는 선언의 사본이 아니다. 설계점 θ(W4 입력 뿌리 y)이고, oracle이 시뮬레이션하는 넷리스트 자신의 소스 값이다(O-46 (2) 'oracle은 자기 op 점 값'과 정합). 엔진 정의도 `icm_margin_v` = 포트별 margin(V_p − lo_p, hi_p − V_p), V_p = 동작점 포트 전압이다(GP:1478 범위 2). 미선언 회로에서도 엔진은 값을 낸다. 그런데 oracle이 내지 않으면 DEC-98 대조가 비고, 엔진·oracle 정의가 갈라진다(물리·정의 정합 위반). 이 부분은 조용한 대체가 아니라 정의다.
- 사영 V_icm = Σc·V_in,decl/Σc²는 P3 묶음 훑기(모든 비묶음 포트 같은 x) 아래에서 엔진의 포트별 margin 최솟값과 같다(c가 모두 같고 창이 x 이동량 좌표일 때). 그 동치를 design에서 증명하거나 test로 확인해야 한다(c가 다르면 같지 않다).

**권고**(원칙 모두 충족): G-18 개정 -- "`swing_icmr.input_dc_V`·`input_dc_pending` 삭제(선언 입력 DC 정본 = `dc_sweep.input_dc` 하나). V_icm = 선언이 있으면 그 사영(§21.2 4단계), 없으면 공칭 점(x = 0)의 입력 좌표(설계점 θ -- 사본 아님, 엔진 정의 GP 범위 2와 같음)". validator 안 가운데 '공칭 점 좌표 대체 삭제(동작 변경)'는 기각한다. **원래 취지와 다름(입력 계약 칸 삭제 = OP-3 계약 변경) -- 사용자 결정 필요.** 기각 근거도 같이 올린다.

## P9. offset-strategy

**(i) (v, L)의 graph 자리**: `OSD` 123은 (v, L)을 `graph/metrics: constraint_rows`(writer = search 제약 블록)에 두는데, 그 필드는 U17 ②로 이월됐고 40 §2.4.12 Q8(미측정 값 자리)이 열려 있다. 선택지는 넷이다. (가) 순서 제약 OS-2 > U17 ②(+Q8 결정). (나) OS-2가 `constraint_rows` 필드와 writer만 당겨 만든다(U17 ② 일부 선행, Q8 결정은 여전히 필요). (다) 과도기 `EvalResult` 칸. 사본이고, 지울 대상에 새 소비자를 다는 것이라 기각. (라) 결과 JSON을 쓸 때 다시 계산. 둘째 생산자라 기각. (가)와 (나) 모두 원칙을 충족하고, (가)가 최소 변경이다(계획에 순서 한 줄). **권고 (가)**: OSP 순서 절에 "OS-2 착수 조건 = U17 ② 병합(`graph/metrics: constraint_rows` 필드·writer)과 40 §2.4.12 Q8 결정(사용자) -- 과도기 칸 금지"를 더한다. U17 ②가 길어지면 (나)로 바꾸는 것은 그때 사용자 결정으로 한다. 취지 같음.

**(ii) 커널 행**: `OSD` 116은 아직 v0.6.2 식 v = k·σ + |V_sys|다. OSP v0.7(132행 O-53 A2, 208행)은 이미 커널 k·σ_in ≤ `offset_in_max_v`, front k·σ_in + |V_id*| ≤ `offset_in_max_v`(DEC-74 front 전용 예외)로 나눠 정했다. **계획 결정은 이미 있다. design 개정만 하면 된다**(S-7 순서가 맞다: 계획 → design). design이 개정할 것: 커널 행 단일 항(분해능 규칙도 항 하나), front 판정 자리, front 값은 front 점 자신의 스냅샷에서 읽기(`OSD` 129 (3)이 이미 짚음 -- P1 keep 집합 교체 뒤에도 커널 밖 writer라 그대로 성립), 기호 |V_sys| → 부호 있는 V_id*의 크기(O-50 G1).

**(iii) OSP 469행 표기**: 현재 "`sctx.cache`(card B 뒤에는 `S3Index` 평가 키 부분)". F-5(OSP 149)는 "XRUN-F1 card B·U17 ② 뒤에는 `sctx.cache`·`computed_keys`가 S3 메모리 색인..."이다. 제안: "`sctx.cache`(XRUN-F1 card B·U17 ② 뒤에는 S3 메모리 색인의 평가 키 부분 -- F-5)". 표기 정정이고 취지 같음. validator가 말한 '순서'가 이 선후 표기와 다른 뜻이면 다시 확인해야 한다(이 분석은 F-5와 대조했다).

---

## 남은 확인(이 분석이 재지 않은 것)
- P4 (a)의 계획 IT-1 범위 4 정확한 줄: GP:1415 부근(긴 줄)과 IT-Q1 GP:1445에서 구절을 확인했다. 범위 4 원문 전체는 읽지 않았다.
- P8 `input_dc_pending`의 정확한 뜻과 소비자: `ODD` 1712 문언만 확인했다.
- P1 θ 무관성은 지금 코드의 블록 목록으로 확인했다. 단계 B 블록이 배선되는 U17 ② 때 다시 확인해야 한다(위 불변식 단언이 자동으로 잡는다).
