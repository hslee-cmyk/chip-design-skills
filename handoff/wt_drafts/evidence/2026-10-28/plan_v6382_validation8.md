# 계획 v6.38.2 독립 검증 8 (2026-10-28) -- 여덟째 커밋 `4efdf9d8` 중심

- 피검 대상: `wt/plan-v6382` 커밋 `4efdf9d8`(여덟째, 부모 `41dacd30`). 판 전체 기준은 `1fefcab1`이다.
  - 바뀐 파일: gain-budget plan(:11·:304·:1239·:1243·:1686·:1931·:2244-2246·:2250·:2252·:2274·:2463)·history(여덟째 커밋 행), oracle-portability plan(:18·:510·:522·:550·:575·:601)·history(v0.6.19 여섯째 커밋 절).
- 검증자: 독립 검증 8. 이 판의 작성자가 아니고 검증 1~7 담당자도 아니다. 작성자 보고·커밋 메시지·history 행은 증거로 쓰지 않았다. 바뀐 줄은 단어 단위 diff(`41dacd30` 대 `4efdf9d8`, difflib 스크립트)로 직접 대조했다.
- 대조한 원문: 계획 원문(`4efdf9d8`), 엔진 코드(`wt/integ-it12` `ebad06c1`).
  - `sizing/block_widths.py:23-50`(`dc_widths` READS/WRITES), `sizing/block_columns.py:95-102`(`dc_columns` READS/WRITES), `sizing/block_currents.py:19-20`, `sizing/block_lengths.py:16-17`
  - `sizing/s2_values.py:223-232`(`LutAccess.__canonical__`)·`:389-406`(`DeviceOp`)
  - `core/compute_block.py:15·:129-149`, `core/projection.py:41-45·:66-77`(입력 버전 = 투영 지문 + extras)
  - `search/kernel.py:94-126`, `search/eval_key.py:13-22`
  - `convergence/converge_point.py:94-148`, `convergence/w_loop_bound.py`, `convergence/kernel_keys.py`, `convergence/realized_geometry.py`
- 이 문서 하나만 썼다. git은 `set -e` + `git -C` 읽기 명령만. 끝난 뒤 `wt/plan-v6382` HEAD `4efdf9d8`, status 빈 출력.
- 줄 번호는 `4efdf9d8` 기준. gb = `gain-budget-gmid-sizing.plan.md`, op = `oracle-portability.plan.md`, E = `wt/integ-it12/skills/analog-gmid-design/gmid_engine`.

## 0. 요약

| 심각도 | 수 | 항목 |
|---|---|---|
| 높음 | 0 | -- |
| 중간 | 3 | **V8-1** 레이아웃 전 키 루프의 자리가 정해지지 않았다. 계획이 정한 '레이아웃 뒤 루프와 같은 꼴(평가 반복)·design은 다른 자리를 고르지 않는다'를 그대로 따르면, 평가 캐시 키(`eval_key`)에 슬라이스 키가 없어 둘째 평가가 첫 평가 결과를 돌려준다. 그러면 루프가 첫 키로 계산한 결과를 '수렴'으로 내는 fail-open이 된다. 또 레이아웃 뒤 루프는 종료 판정·상한이 다르다(기하 같음, `w_loop_bound`). 그래서 '같은 규칙 하나'는 글자대로 성립하지 않는다. **V8-2** 키 루프의 출발 키와 상한이 평가 단위 반복에서 정의되지 않았다. 출발 키는 고정점이 둘일 때 어느 쪽이 결과가 되는지와 '같은 θ = 같은 점' 캐시 의미를 정한다. 상한 '그 kind의 W-bin 수'는 kind가 섞인 소자 전체 반복에서 하나로 정해지지 않는다. **V8-3** OP-7 거부 범위에 '경계 재측정'을 넣었다. 그런데 이 측정이 기존 LUT 옆 선언의 writer다(G-14 :601). 선언이 없으면 거부되므로 선언을 처음 쓸 수 없다(writer 순환). 완료 조건 8의 거부 test도 이 실행을 거부 대상으로 만든다 |
| 경미 | 4 | V8-4~V8-7 |

**승인 상정 의견: 아직 불가(중간 3).** 셋 다 문언으로 고칠 수 있고 판정의 실체는 바꾸지 않는다.

- V7-1 판정의 실체(슬라이스 키 = 평가 입력 `LutAccess`, W 블록 하나가 `DeviceOp.W`·(m, w_f)를 씀, 다음 키 = (m, w_f) READS, graph reuse·S3 graft만)는 엔진 데이터 흐름과 맞는다. 순환·둘째 생산자·새 cache가 없다(§2). 빠진 것은 루프의 자리·출발·상한 세 가지 규칙이다.
- V7-2 판정의 실체(판정·측정 실행 거부, 생성 실행 제외)도 맞다. 다만 '생성 실행 제외'에 기존 LUT 옆 선언 측정(선언의 둘째 writer)이 빠졌다.

## 1. V7-1~V7-8 처리 판정

| # | 기준(오케스트레이터 판정) | 처리(파일:행) | 판정 |
|---|---|---|---|
| V7-1 | 슬라이스 키 = 평가 입력 `LutAccess`(필드 아님). W 블록 `dc_widths` 하나가 `DeviceOp.W`와 (m, w_f)를 씀. 다음 평가 키는 (m, w_f)를 READS해 정하고, 키가 같아질 때까지 반복(graph reuse·S3 graft만, 상한 W-bin 수). 레이아웃 전·뒤 키 루프는 같은 규칙 하나(`converge_point.py:96·:135`, `search/kernel.py:96`과 같은 꼴). DEC-88 쓰기 소자는 루프를 돌지 않음 | gb :304 '레이아웃 전 손가락 규칙' writer·소비자 칸, 'W와 실현 기하의 관계', **키 루프** 문단, 출발 단계 문장; :2244 2a, :2245 2b `iv_matching_l.py`, :2246 3, :2250 (5); X-LA9 :1931, U-130 :2463, Status :11, history 여덟째 행 (1). 낡은 'writer가 키도 씀'·'고정점은 writer 안'·'고정점 함수'·'고정점 writer'는 plan 전체에 0이다(grep). Status와 history의 철회 기록만 남는다 | **문언은 적합, 실체는 부분 적합**. 데이터 흐름·graph 규칙은 맞다(§2). 루프 자리·캐시 키(V8-1)와 출발 키·상한(V8-2)이 빠졌다 |
| V7-2 | OP-7 거부 범위 = 'LUT 또는 LUT로 계산한 엔진 결과를 판정·측정하는 실행'. 생성 실행 제외 | op :510·:522·:575(D-4)·:601(G-14), Status :18, gb :304 (ii), CPG-1 :2274, op history 여섯째 절. 옛 문구 'LUT를 입력으로 받는' 잔존 0(grep) | **부분 적합**. 넓힌 범위와 선언 찾기(G-14 묶는 대상)는 맞다. 다만 거부 목록에 '경계 재측정'이 들어가 기존 LUT 옆 선언 writer가 거부된다 -- **V8-3** |
| V7-3 | 경미 -- finger_w 비교 소비자 | gb :304 소비자 칸에서 삭제. history (3) | 적합 |
| V7-4 | 경미 -- W_request 점 키 출처 | gb :304 '키는 레이아웃 finger_w(실현 필드, LY7)에서 오며 그 점의 레이아웃 전 (m, w_f)는 만들지 않는다(읽는 쪽 없음 …)' | 적합. DE-1 :1686 'W_request 재봉인점에서는 ΔW를 재지 않는다'와 맞다 |
| V7-5 | 경미 -- DE-1 괄호 | gb :1686 'ΔW_k = 판정 W(레이아웃 전 = m·w_f, 실현 기하 (m, w_f) READS …) − θ 유도 W(`DeviceOp.W`)' | 적합 |
| V7-6 | 경미 -- '실측' 표기 | gb :304 '(근거는 검증 6의 추론 -- history; 수치는 나중 병합 card의 변화표가 소유)'. history 여덟째 (6)이 일곱째 행 (8)을 추론으로 읽게 함 | 적합 |
| V7-7 | 경미 -- WB-1·DE-1 파일 겹침 | gb :1239·:2252(WB-1 쪽), :1243(DE-1 쪽) | 적합 |
| V7-8 | 경미 -- OP-7 거부 test | op :550 '거부 test(선언 없음·모드 다름 변형에서 판정·측정 실행 거부, LUT 생성 실행은 통과)' | 부분 적합. 통과 대상에 기존 LUT 옆 선언 측정이 없다 -- V8-3과 같은 자리에서 고친다 |

## 2. V7-1 정본 대 엔진 데이터 흐름·graph 규칙(검사 2)

| 점검 | 엔진 실측(`ebad06c1`) | 판정 |
|---|---|---|
| writer 하나 | `DeviceOp.W` writer = `dc_widths`(`E/sizing/block_widths.py:30`, WRITES `device.dc_op` :27). (m, w_f)를 같은 블록 WRITES에 더하면 계산 자리 1곳이다 | 적합 |
| 순환 없음 | 의존 사슬은 `dc_currents`(READS `dc_current_basis`만, `block_currents.py:19`)·`dc_lengths`(READS `element_class`만, `block_lengths.py:16`) → `dc_columns`(WRITES `dc_v`·`dc_ln_idu`, LUT extras, `block_columns.py:95-102`) → `dc_widths`(READS `dc_v`·`dc_ln_idu`, `block_widths.py:23-26`)다. 키는 블록 출력이 아니라 평가 입력이고 평가 사이에서만 바뀐다 | 적합(graph 안 순환 없음) |
| DEC-88 쓰기 소자 | W = ID·L/exp(ln IDu)(`block_widths.py:47`). ID는 KCL 기저만, L은 element_class만, ln IDu는 θ에서 온다. 셋 다 슬라이스와 무관하다 | 적합('키가 W에서 한 번에 정해짐'은 참. 단 첫 평가의 키가 무엇인지는 V8-2) |
| S3 graft 키에 LutAccess가 입력 버전으로 드는가 | 입력 버전 = 투영 지문(`compute_block.py:15`)이고, 투영 지문 = fp_of((행 지문, extras))(`projection.py:41-45·:66-77`)다. `LutAccess.__canonical__` = (LUT 내용 지문, `w_keys`)(`s2_values.py:231-232`). 그래서 소자별 키가 바뀌면 LUT를 extras로 받는 모든 블록의 입력 버전이 바뀐다. graft 색인 `donors.find(name, _PART, version)`(`compute_block.py:146`) 키에 그대로 든다 | 적합(새 키 성분·새 색인 불필요) |
| 새 cache·sctx 슬롯 | 다음 키 = (m, w_f) READS의 순수 함수다. 직전 키는 루프의 지역값이다(as-built 선례 `converge_point.py:96·:135` `keys_now`). 평가마다 `dataclasses.replace(sctx.dc, lut=…)`(`kernel.py:96`)로 넘기고 sctx 칸을 늘리지 않는다 | 적합 |
| **레이아웃 전 '키 같음'이 레이아웃 뒤 루프와 같은 함수·같은 자리인가** | 아니다. as-built 레이아웃 뒤 루프에는 '키 같음' 함수가 없다. (a) 수렴 = `geometry == previous_geometry`(`converge_point.py:108`)이고 비교 대상은 `RealizedGeometry`(w_request·w_keys·diffusion) 전체다. (b) 순환 = `dc_state in visited[:-1]`(:113-114, dc_state = (w_request, w_keys)). (c) 상한 = `w_loop_bound`(:110, `ceil(log2(구간폭/tol))` -- `w_loop_bound.py:1-22`)이고 W-bin 수가 아니다. (d) 자리 = `converge_point`(front 점마다 탐색 뒤, `evaluate(geometry=)`의 유일한 호출처 -- `converge_point.py:6`). 레이아웃 전 루프는 출발·층 0·커널·외층의 모든 평가에서 돌아야 하므로 이 자리에 둘 수 없다. 인용된 :96·:135는 다음 레이아웃에 넘기는 후보 키(`keys_now`)를 정하는 줄이다. 평가 슬라이스의 종료 판정은 아니다 | **V8-1** |

## 3. 새 결함

### V8-1 (중간) 레이아웃 전 키 루프의 자리와 평가 캐시 키

**사실(계획)**

- gb :304 키 루프: '키가 직전과 같아질 때까지 평가를 반복한다 -- 재사용은 graph reuse·S3 graft(블록, 분할, 입력 버전)만, 상한 = 그 kind의 W-bin 수, 재방문 = NONCONVERGENT. 레이아웃 전 키 루프와 레이아웃 뒤 키 루프는 같은 규칙 하나다(P0 -- 레이아웃 뒤 루프 as-built `convergence/converge_point.py:96·:135`·`search/kernel.py:96`과 같은 꼴; design은 다른 자리를 고르지 않는다)'.
- gb :2246 범위 3도 같은 문구이고, :2249 범위 5는 '레이아웃 뒤: … DEC-89 재평가 자리 그대로'다.

**사실(엔진)**

- 평가 캐시 키 = `eval_key(context_fp, schema_fp, pairs, cells, geometry fp 또는 None)`(`E/search/kernel.py:100`, `eval_key.py:13-22`). 레이아웃 전 평가(`geometry=None`)에서는 `LutAccess.w_keys`가 키에 없다.
- 키가 같으면 `sctx.cache`가 바로 돌려준다(커널 0, `kernel.py:101-106`).
- 레이아웃 뒤 루프는 슬라이스를 `geometry`로 넘긴다. 그래서 `fp_of(geometry)`가 캐시 키에 들어간다(`kernel.py:96·:100`, `converge_point.py:123-124`).
- 같은 꼴(평가 반복)을 레이아웃 전에 쓰려면 `evaluate`에 슬라이스 키를 넘길 인자도 없다.
- 종료 판정·상한·자리는 §2 마지막 행과 같다. 레이아웃 뒤 루프는 기하 같음·`w_loop_bound`·`converge_point`다.

**추론**

- (a) '같은 꼴 = `evaluate`를 다시 부름'으로 읽어 구현하면 다음과 같이 된다.
  - 첫 평가 키 K0 → 결과 → (m, w_f) → K1 ≠ K0이므로 `evaluate(θ)`를 다시 부른다.
  - 같은 θ·cells라 캐시 적중이고, K0으로 계산한 결과가 돌아온다.
  - 그 결과의 (m, w_f) → K1, 직전 K1과 같으므로 '수렴'이다.
  - 결과는 K0 슬라이스로 계산한 점인데 키는 K1로 기록된다. 소자 슬라이스와 그 W의 bin이 어긋난 점이 봉인을 통과한다. 이것은 조용한 fail-open이고 DEC-105 (2) 조건('읽는 슬라이스의 bin = SPICE가 그 w_f로 고르는 bin')을 깬다.
- (b) 피하는 길은 둘이고 결과가 다르다.
  - (i) 루프를 평가 단위 안(`size_and_seal` 둘레, 캐시 키 = θ·cells 그대로)에 둔다. 평가 1회 = 커널 1회·S3 evals 1줄이다.
  - (ii) `evaluate`에 키를 받는 인자를 두고 캐시 키에 키 지문을 넣는다(레이아웃 뒤 `w_fixed_fp`와 같은 꼴). 이 경우 중간 평가도 EvalResult 캐시·S3 evals 줄·`kernel_calls`·E_B 평가 수 예산(`kernel.py:117·:160-165`)에 잡히고, 반복 호출부가 출발·층 0·FD Jacobian·외층 전부로 퍼진다.
  - 둘은 평가 수 예산 소비와 S3 기록 단위가 다르다. '같은 꼴'·'design은 다른 자리를 고르지 않는다'는 어느 쪽도 정하지 않고 오히려 고르지 못하게 막는다.
- (c) '같은 규칙 하나'를 종료 판정·상한까지로 읽으면 레이아웃 뒤 루프를 바꿔야 한다(W-bin 수 상한, 키 같음 판정). 이는 범위 5 'DEC-89 재평가 자리 그대로'와 MOD8 루프 소유 card 범위와 부딪친다. 글자대로 성립하는 것은 '키는 평가 입력 `LutAccess`이고 다음 키는 직전 평가 결과에서 정한다, 재방문은 NONCONVERGENT'까지다.

**막히는 경로**

- card WB-1 design(S-7)은 범위 3을 구현 자리로 옮길 때 (b)의 (i)/(ii)를 골라야 한다. 계획은 '다른 자리를 고르지 않는다'고만 하고 자리를 적지 않았다. 그래서 as-built 결정 금지에 걸려 멈춘다.
- 완료 조건 (1) '고정점이 bin 수 안에서 수렴'·(5)의 판정자는 '같은 규칙 하나'를 무엇으로 셀지(함수 하나? 꼴?) 근거가 없다.
- (ii)를 고르고 캐시 키를 빠뜨리면 (a)가 실제 결함이 된다. 그런데 완료 조건에 그것을 잡는 test가 없다.

**고침(대안 비교)**

| 안 | 내용 | graph 정본 | 물리·손계산 | design 단순성 | 실측 근거 |
|---|---|---|---|---|---|
| (가) 평가 단위 안 | 키 루프를 평가 하나 안(`size_and_seal` 둘레)에 둔다. 캐시 키 = θ·L 칸 그대로(평가 결과는 θ의 함수). 반복 사이 재사용 = graph reuse·S3 graft(입력 버전에 `LutAccess` 지문 포함 -- §2) | 새 cache·sctx 0. EvalResult 값 칸 0 | 같다 | 호출부 변경 0(`evaluate` 하나). E_B·S3 evals 단위 불변 | `kernel.py:94-126`, `projection.py:41-45` |
| (나) 평가 반복 + 키 인자 | `evaluate`에 키 인자를 두고 캐시 키에 키 지문을 넣는다(`w_fixed_fp` 꼴) | 같음 | 같다 | 출발·층 0·FD·외층 호출부 전부가 반복한다. 중간 평가가 E_B·S3에 잡힌다 | `converge_point.py:123`, `eval_key.py:13` |

- 권고: **(가)**. 문언은 '레이아웃 전 키 루프는 평가 하나 안에서 돈다(평가 캐시 키 = θ·L 칸 -- 슬라이스 키는 θ에서 정해지는 양이라 키에 넣지 않는다). 레이아웃 뒤 루프와 같은 것은 꼴(키 = 평가 입력 `LutAccess`, 다음 키 = 직전 평가 결과에서, 재방문 = NONCONVERGENT)이고, 상한·종료 판정·자리는 각 루프의 것(레이아웃 뒤 = as-built `w_loop_bound`·기하 같음 그대로, DEC-89)'으로 바꾼다.
- 완료 조건 (1)에 '같은 θ를 다시 평가하면 수렴 키의 결과와 비트 동일(첫 키 결과가 아님)' toy 한 줄을 더한다.
- 고칠 자리: gb :304 키 루프 문단, :2246 3, :2250 (5), U-130 :2463('레이아웃 뒤 키 루프와 같은 규칙'), X-LA9 :1931, history.

### V8-2 (중간) 키 루프의 출발 키와 상한이 정의되지 않았다

**사실**

- gb :304·:2246은 '다음 평가의 키는 (m, w_f) 필드를 READS해 정한다'고만 한다. 첫 평가의 키(출발 키)는 어디에도 없다.
- 범위 2(:2243)는 as-built 출발 키 규칙(`pre_layout_lut_access` -- kind당 `w_ref_m` 슬라이스)을 '같은 변경에서 지운다'.
- 상한은 '그 kind의 W-bin 수'(:304 두 곳, :2246)다. 그런데 키 루프는 이제 평가 단위 반복이라 한 번에 nmos·pmos 소자 전체의 키 벡터를 바꾼다.

**추론**

- (a) 종속 소자에서 키 K_A로 W가 bin A에 들고 K_B로 W가 bin B에 들면 고정점이 둘이다. bin 사이 ΔVGS −45~−131 mV(gb :2237 (iv))면 경계 부근에서 실제로 생긴다. 이때 결과는 출발 키가 정한다. 출발 키를 parent 평가의 키에서 가져오면 같은 θ가 계보에 따라 다른 점이 된다. 그러면 '같은 θ = 같은 점' 평가 캐시(`kernel.py:100-106`)와 결정성(완료 조건 (6))의 뜻이 깨진다.
- (b) 상한 '그 kind'는 kind가 둘인 공동 반복에서 하나로 정해지지 않는다(최댓값? 합?). 재방문 검사만으로도 유한 상태라 끝나므로, 상한이 재방문 없이 수렴하는 사슬을 자르면 거짓 NONCONVERGENT가 된다. 다섯째 커밋에서 이 상한은 소자 하나의 writer 안 고정점에 맞던 값이었다. 평가 단위로 바뀌면서 근거가 사라졌다.

**막히는 경로**

- card WB-1 design은 출발 키 규칙(θ만의 함수여야 함)과 상한 식을 정해야 한다. 이는 결과 점(9회로 변화표 원인)을 바꾸는 규칙이라 as-built 결정 금지에 걸려 멈춘다.
- 완료 조건 (1) '고정점이 bin 수 안에서 수렴'은 'bin 수'가 정의되지 않아 판정할 수 없다.

**고침**

- 출발 키: θ와 선언만의 함수로 둔다(parent 키 금지). 기본안은 둘이다.
  - (가′) 쓰기 소자는 θ에서 W를 평가 전에 알므로 그 W의 손가락·선택 함수 값으로 둔다. 종속 소자는 그 kind의 `w_ref_m` 슬라이스(w_hi를 잡는 기준 bin과 같은 슬라이스 -- 새 상수 없음)로 둔다.
  - (나′) 전부 `w_ref_m` 슬라이스로 둔다.
  - (가′)는 쓰기 소자 반복을 0으로 만들어 '쓰기 소자는 루프를 돌지 않음'(판정 문구)과 글자대로 맞는다. 그래서 (가′)를 권고한다.
- 고정점이 둘 이상일 때 출발 키에서 처음 닿는 고정점을 쓴다고 적고, 변화표에 '고정점 다중' 표지를 남긴다(출력 전용).
- 상한: 소자 키 벡터의 재방문 검사를 정본으로 둔다(유한 상태라 종료 보장). 상한 '그 kind의 W-bin 수'는 지우거나 '소자마다 키 변경 횟수 ≤ 그 소자 kind의 W-bin 수'로 소자 단위로 고쳐 적는다.
- 고칠 자리: gb :304(두 곳), :2246 3, 완료 조건 (1), history.

### V8-3 (중간) OP-7 거부 목록의 '경계 재측정'이 기존 LUT 선언 writer를 거부한다

**사실**

- op :510: '… 판정·측정하는 실행(상위 EO-1·ME-1 판정·9회로 넷리스트 판정·상위 CPG-1·**경계 재측정**)은 선언의 호환 모드로 실행하고 선언이 없거나 다르면 실행 거부 -- fail-closed; … LUT 생성 실행(OP-8 -- 선언의 writer …)과 LUT·엔진 결과를 쓰지 않는 MC 생성 실행은 거부 대상 아님; 기존 LUT 옆 선언 측정은 측정에 쓴 모드를 근거 칸에 적음'. gb :304 (ii)도 같은 목록이다.
- 같은 계획에서 기존 LUT 선언의 writer는 '검증자가 지금 공유 LUT의 경계 앵커 점에서 … 다시 잰다'(op :510 뒤쪽, D-4 :575)이다. G-14 :601은 이 측정을 바로 '**경계 재측정**에 쓴 시뮬레이터 판 …'이라 부른다.
- gb :304 writer 칸도 '기존 LUT는 검증자가 다시 재서 쓰는 옆 선언 파일 -- oracle OP-7'이다.
- op :550 완료 조건 8 거부 test는 '선언 없음 … 변형에서 판정·측정 실행 거부, LUT 생성 실행은 통과'다. 옆 선언 측정은 통과 목록에 없다.

**추론**

- 기존 LUT에는 아직 선언이 없다(OP-7이 처음 쓴다). 그런데 그 선언을 쓰는 측정 실행이 '선언이 없으면 거부' 목록에 들어 있다. 그래서 선언을 처음 쓸 수 없다(writer 순환).
- 제외 목록은 새 LUT의 writer(OP-8 생성 실행)만 빼고, 기존 LUT의 writer(OP-7 옆 선언 측정)는 빼지 않았다.
- 검증 7 V7-2 고침이 제안한 '경계 재측정 포함'이 그대로 옮겨졌다. 그러나 그 실행이 writer라는 점은 대조하지 않았다.

**막히는 경로**

- card OP-7은 자기 산출물(기존 LUT 옆 선언)을 만드는 측정을 자기 거부 규칙으로 막는다.
  - 거부 test(완료 조건 8)를 글자대로 구현하면 옆 선언 측정도 '선언 없음'에서 거부돼야 한다. 그러면 OP-7 완료가 불가능하다.
  - 거부하지 않게 구현하면 계획 문구를 넘는 as-built 결정이다.
- 뒤따라 WB-1 범위 0(선언 reader, OP-7 선행)과 CPG-1이 막힌다.

**고침**

- 거부 목록에서 '경계 재측정'을 뺀다. 아니면 '선언이 이미 있는 LUT의 경계 재확인 측정'으로 좁힌다.
- 제외 목록을 '선언의 writer 실행 -- 새 LUT 생성 실행(OP-8)과 기존 LUT 옆 선언 측정(OP-7, 측정에 쓴 모드를 근거 칸에 씀)'으로 바꾼다. writer가 둘이라는 것은 이미 정본이다(gb :304 writer 칸).
- 완료 조건 8 통과 목록에 '기존 LUT 옆 선언 측정'을 더한다.
- 고칠 자리: op :510·:522·:575·:550, gb :304 (ii), Status 2곳, 두 history.

## 4. 경미

- **V8-4 `DeviceOp.w_key`의 처리**
  - 완료 조건 (5)(:2250)는 '슬라이스 키 = 평가 입력(필드 아님)'이다. 그런데 as-built `DeviceOp`에는 `w_key` 성분이 있다(`E/sizing/s2_values.py:404`, writer `dc_widths`가 `w_key_of(lut, kind)` 입력 사본을 씀 -- `block_widths.py:48`).
  - 엔진 안 소비자는 0이다(`E/lut/` 밖 `w_key` grep -- DeviceOp를 읽는 자리 없음).
  - 소자별 키로 바뀌면 이 성분은 평가 입력의 graph 안 사본(graph 규칙 4)이다. 판정자가 (5)를 글자대로 대조하면 걸린다.
  - 고침: 범위 2에 '`DeviceOp.w_key`(입력 사본, 소비자 0)는 지운다'를 넣는다. 아니면 '출력 전용 입력 기록'으로 선언한다(만들면 배선 -- 소비자 0이면 삭제가 기본).
- **V8-5 D-4 결정 문언의 재변경 표지**
  - op history 여섯째 절은 '결정 문언 변경은 셋째 커밋 D-4 변경 범위 안'이라고 적는다.
  - 그러나 이번 변경은 승인 결정 D-4(O-1) 행(:575)의 거부 대상을 엔진 넷리스트 판정 실행(EO-1·ME-1·9회로)까지 넓힌다. 이는 셋째 커밋이 승인 질문에 실은 문언과 다르다.
  - 승인 질문의 'D-4 문언 변경' 항목에 이 확장을 한 줄 더해야 한다(원래 취지와 다름은 아님 -- fail-closed 취지 그대로).
- **V8-6 D-4 :575 괄호 읽힘**
  - 'LUT 생성(OP-8)·LUT·엔진 결과를 쓰지 않는 MC 생성 실행 제외'는 'LUT 생성·LUT·엔진 결과'를 한 목록으로 읽힐 수 있다.
  - op :510 꼴('LUT 생성 실행(OP-8)과 LUT·엔진 결과를 쓰지 않는 MC 생성 실행')로 맞춘다. V8-3 고침과 같은 자리다.
- **V8-7 '고정점' 용어 잔존**
  - 완료 조건 (1)(:2250) '고정점이 bin 수 안에서 수렴'과 :304 'W → w_f → 슬라이스 → IDu → W 고정점은 아래 키 루프로 푼다'는 뜻이 통하지만 V8-2 고침(상한) 뒤 '키 루프가 상한·재방문 규칙 안에서 수렴'으로 맞춘다.

## 5. 바뀐 개념의 전 자리 대조(검사 3)

| 개념 | gain-budget | oracle-portability | 판정 |
|---|---|---|---|
| 슬라이스 키 = 평가 입력, W 블록 하나가 W·(m, w_f) | :304(writer·관계·키 루프·출발 단계)·:2244·:2245·:2246·:2250·:1931·:2463·:11 서로 일치. 낡은 구절 0 | -- | 문언 일치, 자리·출발·상한 V8-1·V8-2 |
| 레이아웃 전·뒤 같은 키 루프 | :304·:2246·:2463 | -- | V8-1 |
| (m, w_f) 소비자 | :304 소비자 칸 = 다음 키 선택·EO-1·DE-1·2b ↔ :2244·:2250·:2463 같은 목록 | -- | 일치(V7-3 해소) |
| OP-7 거부 범위 | :304 (ii)·:2274 CPG-1 | :18·:510·:522·:550·:575·:601 같은 문구 | 일치, 범위 V8-3 |
| 다른 계획(offset-strategy·graph-consumption·headroom-chain·offset-trim 등) | OP-7 인용 0, 키 루프·(m, w_f) 인용 0(grep) | -- | 해당 없음 |

## 6. 원칙 점검표(검사 4)

| 원칙 | 판정 | 방법 |
|---|---|---|
| graph 단일 정본(writer 하나·소비자 ≥1·사본/cache 0) | writer 하나(`dc_widths`), 순환 없음, S3 graft 입력 버전에 `LutAccess` 지문 포함, 새 cache·sctx 0 -- 적합. `DeviceOp.w_key` 입력 사본 V8-4. 평가 캐시 키 결함 위험 V8-1 | 엔진 실측(§2) |
| 만들면 배선 | (m, w_f) 소비자 4곳 배선 card 있음. W_request 점 (m, w_f) 안 만듦(읽는 쪽 없음) -- 적합. `DeviceOp.w_key` 소비자 0 V8-4 | 원문 + grep |
| DC/AC 분리 | 위반 없음 | 원문 |
| 계산 틀(DEC-103) | 사이징 θ 고정, 반올림 효과는 W·바이어스 고정 KCL -- 적합 | 원문 |
| O-127 | 변경 없음 | 원문 |
| EP-7 | 출발 단계 W·(m, w_f) = 출발값, '같은 키 루프 규칙' -- 적합(출발 키 V8-2) | 원문 |
| fail-closed | V8-1(캐시 적중으로 수렴 위장 위험), V8-3(writer가 거부됨 -- fail-closed 과잉으로 산출 불가). 슬라이스 없음·재방문 실패 레코드 유지 | 원문 + 코드 |
| O-153 | as-built 자리를 규칙 근거로 쓰지 않음. 다만 'as-built `converge_point`와 같은 꼴; design은 다른 자리를 고르지 않는다'는 as-built 구조를 자리 제약으로 쓴 문구다 -- V8-1 고침에서 '꼴'로 한정 | 원문 |
| 상수·회로 이름 | 위반 없음(상한·출발 키 고침도 LUT·선언 유도) | 원문 |
| 계획/이력 분리 | 옛 문장은 gb history 여덟째 행·op history 여섯째 절로 옮겼다. diff와 대조해 일치한다(:1239·:1243·:2252·:2274는 덧붙임뿐) | diff |
| heldout | 변화 없음 | 원문 |

## 7. U-125~U-131·N2.1·N7.2·순서표·X-LA·history·Status

- U-125~U-131: U-130(:2463)만 바뀌었고 V7-1 문언과 맞다. V8-1 고침을 따라 '레이아웃 뒤 키 루프와 같은 규칙'을 '같은 꼴'로 다시 맞춘다. 시점 칸은 순서표와 맞다.
- N2.1 DEC-105 상태 칸·X-LA8~X-LA10은 서로 맞다. X-LA9는 '원래 취지와 다름' 표지를 유지한다.
- 순서표: WB-1 :1239 ↔ :2252 ↔ DE-1 :1243이 양쪽 겹침으로 일치한다(V7-7).
- Status: gb :11 '첫째~여덟째', op :18 '첫째~여섯째'. 판 번호 6.38.2·0.6.19는 커밋 단위 개정이라 맞다.
- history: gb 여덟째 행 (1)~(8)과 op 여섯째 절의 '바꾼 것·옛 문장'이 diff와 일치한다. '근본원칙·결정 문언 변경 없음'은 D-4 문언 확장에 대해 V8-5.

## 8. '원래 취지와 다름'·결정 문언 변경 목록

| 항목 | 표지 | 판정 |
|---|---|---|
| 오케스트레이터 V6-1 판정 두 구절 철회 | gb history 여덟째 (1), Status :11, :304 본문 | 있음 |
| OP-7 거부 범위 확장(D-4 :575 문언) | op history 여섯째 '셋째 커밋 D-4 변경 범위 안' | 표지 약함 -- V8-5 |
| U-130 손가락 폭 | X-LA9·U-130 '원래 취지와 다름' | 유지 |
| 근본원칙 | 변경 없음 | 해당 없음 |

## 9. 회귀 점검(검증 1~7 적합 항목)

- 손가락 규칙 본문, 포락·합집합, 짝 규칙, D1 격자 정수 비교, bin 경계 선언 키·writer/reader 셋, CPG-1 bench·사본·sha256, DE-1 배선 규칙(나중 병합 card), 소비 기준 축(V6-6), 1차 DC 감도(V6-5), metric 3열(V6-8), DeviceOp.W 소비자 12곳은 바뀐 문언이 없거나 같은 뜻이다.
- V6-4는 W_request 점에서 (m, w_f)를 만들지 않게 바뀌었다(V7-4). 'layout 스냅샷에 두 필드가 함께 있으면 실현 필드' 규칙은 설계점 스냅샷 위 레이아웃 필드 경우로 여전히 성립한다(`converge_point.py:9-10`).
- **회귀 없음.**

## 10. 재현 명령

```bash
set -e
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6382; R=/c/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12
P=$W/docs/01-plan/features/gain-budget-gmid-sizing.plan.md; O=$W/docs/01-plan/features/oracle-portability.plan.md
E=$R/skills/analog-gmid-design/gmid_engine
git -C $W diff --stat 41dacd30..4efdf9d8
sed -n '23,50p' $E/sizing/block_widths.py; sed -n '95,102p' $E/sizing/block_columns.py; sed -n '19,20p' $E/sizing/block_currents.py
sed -n '223,232p' $E/sizing/s2_values.py; sed -n '41,77p' $E/core/projection.py; sed -n '129,149p' $E/core/compute_block.py
sed -n '94,106p' $E/search/kernel.py; sed -n '13,22p' $E/search/eval_key.py
sed -n '94,138p' $E/convergence/converge_point.py; sed -n '1,22p' $E/convergence/w_loop_bound.py
grep -rn "w_key" $E --include=*.py | grep -v "/lut/"          # DeviceOp.w_key 소비자 0
grep -n -o '.\{0,80\}경계 재측정.\{0,80\}' $O $P
git -C $W status --short; git -C $W rev-parse HEAD
```
