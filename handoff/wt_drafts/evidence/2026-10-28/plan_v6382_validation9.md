# 계획 v6.38.2 독립 검증 9 (2026-10-28) -- 아홉째 커밋 `b4451d0f` 중심

- 피검 대상: `wt/plan-v6382` 커밋 `b4451d0f`(아홉째, 부모 `4efdf9d8`). 판 전체 기준은 `1fefcab1`이다.
  - 바뀐 파일: gain-budget plan(:11 Status·:304 DEC-105 (2)·:2243 2a·:2244 2b·:2246 3·:2250 완료 조건·:2463 U-130)·history(아홉째 커밋 행), oracle-portability plan(:18 Status·:510 OP-7·:550 완료 조건 8·:575 D-4)·history(v0.6.19 일곱째 커밋 절).
- 검증자: 독립 검증 9. 이 판의 작성자가 아니고 검증 1~8 담당자도 아니다. 작성자 보고·커밋 메시지·history 행은 증거로 쓰지 않았다. 바뀐 줄은 `git diff --word-diff`(`4efdf9d8..b4451d0f`)로 직접 대조했다.
- 대조한 엔진 원문: `wt/integ-it12` `ebad06c1`(E = `skills/analog-gmid-design/gmid_engine`).
  - `search/kernel.py:94-126`(`evaluate`·`eval_key` 호출·`size_and_seal(dc, …, parent=base)`), `search/eval_key.py:13-22`
  - `convergence/converge_point.py:90-140`(기하 같음 :108, `w_loop_bound` :110, `visited` :113-114)
  - `sizing/s2_values.py:223-232·:403`, `sizing/block_widths.py:48`(`w_key_of(lut, kind)`)
  - `DeviceOp.w_key` 소비자 전수(`grep -rnE "\.w_key\b"`), `lut/noise_query.py:20-27`, `lut/mismatch_query.py:24-29`, `lut/_helpers_columns.py:15-31`, `lut/vdsat_query.py`, `lut/gmb.py:35·:50`, `metrics/noise_devices.py:29-31`, `metrics/device_sigma.py:36-41`, `metrics/ss_linearize.py:57-75`
  - `assets/lut_v2_location.json`(슬라이스 32개 GMBS·VDSAT 포함 재생성, 2026-10-08)
- 이 문서 하나만 썼다. git은 `set -e` + `git -C` 읽기 명령만. 끝난 뒤 `wt/plan-v6382` HEAD `b4451d0f`, status 빈 출력.
- 줄 번호는 `b4451d0f` 기준. gb = `gain-budget-gmid-sizing.plan.md`, op = `oracle-portability.plan.md`.
- 오케스트레이터 추가 지시(검사 5 -- O-153 as-built 인용 감사)를 §7에 넣었다.

## 0. 요약

| 심각도 | 수 | 항목 |
|---|---|---|
| 높음 | 0 | -- |
| 중간 | 2 | **V9-1** `DeviceOp.w_key` 유지 문장이 든 '소비자 12자리' 중 2자리(`metrics/noise_devices.py:31`, `metrics/metrics_aux.py:181` → `device_sigma.py:41`)는 기준 폭 전용 표(noise·mismatch)를 이 키로 조회한다. 그래서 소자별 슬라이스 키가 들어가면 기준 bin 밖 소자마다 `lut_column_unavailable`(`noise_query.py:25-26`, `mismatch_query.py:28-29`)로 실패한다. 완료 조건 (5) '소비자 12자리 유지'와 범위 2 '잡음·mismatch는 기준 폭 환산 유지'가 이 두 자리에서 서로 어긋난다. **V9-2** 불변식 (iv)가 as-built 레이아웃 뒤 루프(`converge_point.py` 기하 같음·`w_loop_bound`)의 판정·상한을 '바꾸지 않는다'고 못박는다. as-built를 보존 대상으로 삼은 규칙이라 O-153(근본규칙)과 충돌한다 |
| 경미 | 6 | V9-3~V9-8 |

**상정 의견: 아직 불가(중간 2).** 둘 다 문언으로 고친다. 판정의 실체(불변식 (i)~(iii), OP-7 제외 범위, `w_key` 유지)는 맞다.

- V8-1~V8-7 처리는 대체로 적합하다(§1). 오케스트레이터 판정 기준((i)~(iv)·V8-3·V8-4)이 문언에 그대로 옮겨졌다.
- V8-4의 '소비자 12자리'는 내 실측과도 맞다(§2). 검증 8의 '소비자 0'은 틀렸다. 다만 그 12자리의 성격이 둘로 갈린다(V9-1).

## 1. V8-1~V8-7 처리 판정

| # | 기준(오케스트레이터 판정) | 처리(파일:행) | 판정 |
|---|---|---|---|
| V8-1 | V7-1 자리 지정 구절 철회. (i) 슬라이스 키가 평가 입력 버전·평가 캐시 키에 듦(fail-closed). 레이아웃 뒤 루프는 as-built 불변(iv) | gb :304 '키 루프' 문단(철회 표지 + (i)~(iv) + '자리·함수 구성·출발 키 구체 꼴은 design 몫'), :2246 3, :2250 (1) toy '같은 θ 재평가 = 수렴 키 결과와 비트 동일(첫 키 결과가 아님)', :2463 U-130 '같은 것은 키를 평가 입력으로 두는 꼴뿐', Status :11, history 아홉째 (1). 옛 '같은 규칙 하나'·'design은 다른 자리를 고르지 않는다'는 Status·:304 철회 표지에만 남는다(grep) | **적합**. (i)의 '평가 캐시 키' 문언은 V9-3(경미). (iv)의 O-153 문제는 V9-2 |
| V8-2 | (ii) θ → 결과는 함수, 출발 키는 θ·선언만의 함수(parent 키 금지). (iii) 재방문 검사, 상한 소자 단위 | gb :304 (ii)(iii), :2246 3, :2250 (1) toy '같은 θ·다른 계보 → 같은 점' | **적합**. 상한 초과 때의 결과가 적히지 않았다 -- V9-4(경미) |
| V8-3 | OP-7 거부 제외 = OP-8 LUT 생성 + OP-7 옆 선언 측정 + LUT 없는 MC 생성. 거부 test 통과 목록도 같게 | op :510(거부 목록에서 '경계 재측정' 뺌, '선언의 writer 실행 -- LUT 생성 실행(OP-8)과 기존 LUT 옆 선언 측정(이 card)'), :550 완료 조건 8 통과 목록, :575 D-4 괄호, gb :304 (ii), Status op :18·gb :11, op history 일곱째 절 | **적합(잔여 경미)**. op :522 요약 문장은 제외를 적지 않는다 -- V9-5 |
| V8-4 | `DeviceOp.w_key` 유지(소비자 12자리) | gb :304·:2246 3·:2250 (5) | **처리 적합, 내용은 V9-1**. 12자리는 실측과 맞다(§2) |
| V8-5 | 경미 -- D-4 문언 재변경 표지 | op history 일곱째 절 '결정 문언 변경 … 승인 질문의 'D-4 문언 변경' 항목에 한 줄 추가 … 원래 취지와 다름은 아님' | 적합 |
| V8-6 | 경미 -- D-4 괄호 읽힘 | op :575 '선언의 writer 실행(LUT 생성 실행 OP-8과 기존 LUT 옆 선언 측정 OP-7)과 LUT·엔진 결과를 쓰지 않는 MC 생성 실행은 제외' | 적합 |
| V8-7 | 경미 -- '고정점' 용어 | gb :304 'W → … → W 반복은 … 키 반복으로 푼다', :2250 '키 반복이 소자 단위 상한·재방문 규칙 안에서 수렴'. '고정점은'·'고정점이 bin' 0(grep). '키 반복' 정의는 :304 한 자리('정의는 이 자리 하나') | 적합 |

## 2. 불변식 (i)~(iv) 대 엔진 사실(검사 2)

| 점검 | 엔진 실측(`ebad06c1`) | 판정 |
|---|---|---|
| (i) '평가 입력 버전' | 입력 버전 = 투영 지문이고 `LutAccess.__canonical__` = (LUT 지문, `w_keys`)(`s2_values.py:231-232`). 소자별 키로 바뀌어도 S3 graft 색인 키에 그대로 든다 | 적합 |
| (i) '평가 캐시 키' | `eval_key(context_fp, schema_fp, pairs, cells, geometry fp 또는 None)`(`kernel.py:100`). 레이아웃 전에는 슬라이스 키 자리가 없다. (ii)대로 키 반복이 평가 하나 안이면 캐시 조회가 반복보다 먼저라 수렴 키를 캐시 키에 넣을 수 없다. 넣을 수 있는 것은 출발 키뿐이고, 출발 키는 (ii)로 θ·선언의 함수라 이미 θ·`context_fp`가 정한다 | 모순은 아님. 다만 '평가 캐시 키'가 θ 단위 `eval_key`인지 반복 안 키인지 갈린다 -- V9-3(경미) |
| (ii) θ → 결과 함수, parent 키 금지 | `size_and_seal(dc, …, parent=base)`(`kernel.py:124`)는 parent 스냅샷을 graph reuse에만 쓴다. 입력 버전이 같을 때만 재사용하므로 결과가 θ의 함수라는 것과 맞다. 출발 키를 parent에서 가져오는 경로는 as-built에 없다(`pre_layout_lut_access` kind당 기준 폭) | 적합 |
| (iii) 재방문 검사·소자 단위 상한 | 키 공간 = 소자별 bin 수의 곱(유한)이라 벡터 재방문 검사만으로 종료가 보장된다. 소자 단위 상한은 벡터가 재방문하지 않아도 한 소자가 bin 수보다 많이 바뀌면 닿을 수 있다 | 상한 초과 결과 미기재 -- V9-4(경미) |
| (iv) 레이아웃 뒤 루프 | as-built 수렴 = `geometry == previous_geometry`(:108), 순환 = `dc_state in visited[:-1]`(:113-114), 상한 = `w_loop_bound`(:110). (i)(기하 지문이 `eval_key`에 듦 :100)·(iii)(재방문 = NONCONVERGENT)의 원칙은 이미 따른다 | 사실 기술은 맞다. 규칙 꼴은 V9-2 |
| (i)~(iv) 서로 | (ii)의 '평가'는 θ 단위 평가, (iv)의 루프는 기하가 입력에 더해지는 평가다. (ii)는 레이아웃 전 평가에 대한 진술로 읽어야 (iv)와 맞는다('θ → 결과'를 레이아웃 뒤에서는 (θ, 기하) → 결과로) | V9-3에 묶음(경미) |
| `DeviceOp.w_key` 소비자 | `.w_key` 속성 읽기(`grep -rnE "\.w_key\b"`, lut·tests 밖) = `metrics/ls_fields.py:55`, `metrics/metrics_aux.py:119·:120·:181`, `metrics/noise_devices.py:31`, `metrics/ss_linearize.py:63·:65·:66·:73`, `sizing/seal_conduction.py:29`, `sizing/seal_saturation.py:36·:42` -- **12자리, 계획 목록과 일치**. 모두 `ops`/`dc_op`의 `DeviceOp`다. 따로 `search/iv_matching_l.py:66`·`search/iv_noise.py:58`은 탐색 문맥 `ctx.by_name[...]`의 `d.w_key`(DeviceOp 아님) | 12자리 적합. 성격은 V9-1 |

## 3. 새 결함

### V9-1 (중간) '소비자 12자리 유지'와 '잡음·mismatch는 기준 폭' 규칙이 두 자리에서 어긋난다

**사실(계획)**

- gb :304·:2246 3: '`DeviceOp.w_key` 성분(그 평가가 소자에 쓴 슬라이스 키의 기록 -- writer = W 블록, 값 = 평가 입력 키)은 유지한다: 엔진 소비자 12자리(… `metrics/metrics_aux.py:119·:120·:181`, `metrics/noise_devices.py:31`, …)'.
- gb :2250 완료 조건 (5): '`DeviceOp.w_key` 기록 성분의 소비자 12자리 유지'.
- gb :304 '읽는 열'·:2243 범위 2: '읽는 열 = 슬라이스의 DC 열과 그 열에서 나오는 `ss` 값만, 용량·잡음·mismatch는 기준 폭 환산 유지'. 완료 조건 (1) '용량·잡음 열은 기준 폭 환산 그대로'.

**사실(엔진)**

- `metrics/noise_devices.py:31` `noise_params(memo, op.kind, op.w_key, …)` → `lut/noise_query.py:25-26` `if table.w_key != w_key: raise seal_violation("lut_column_unavailable", column="SVG2", …)`. 잡음 표는 kind당 하나(기준 폭)다.
- `metrics/metrics_aux.py:181`이 `ops[m].w_key`로 행을 만들고 → `metrics/device_sigma.py:41` `mismatch_dvgs(memo, kind, w_key, …)` → `lut/mismatch_query.py:28-29` 같은 검사로 `column="DVGS"` 실패를 낸다.
- 지금은 키가 kind당 기준 폭 하나(`block_widths.py:48` `w_key_of(lut, kind)`)라 두 표의 키와 같아서 통과한다.
- 나머지 10자리는 슬라이스 조회다. `op_point`·`gmb`(`gmb.py:35·:50` 슬라이스 열 우선), VDSAT·`tol_vdsat_table`(`_helpers_columns.py:21-22` 슬라이스 열 우선; 공유 LUT 슬라이스는 VDSAT 포함 -- `lut_v2_location.json`), `slice_map[(kind, w_key)].w_m`, `_gmb_model`(슬라이스 열 먼저 -- `ss_linearize.py:57-58`)이다. 소자별 키를 그대로 받아도 맞다.

**추론**

- card WB-1이 소자별 키를 `DeviceOp.w_key`에 쓰면 다음 둘 중 하나가 된다.
  - 두 자리를 그대로 두면, 기준 bin(5 µm 슬라이스 bin) 밖의 모든 소자가 잡음·mismatch 조회에서 `lut_column_unavailable`로 실패한다. 이 실패는 fail-closed이지만 거짓 거부다. 범위 2 '잡음·mismatch는 기준 폭 환산'도 어긴다.
  - 두 자리를 기준 폭 키(LUT 적재 메타 -- 잡음·mismatch 표의 `w_key`)로 바꾸면 (5) '소비자 12자리 유지'를 글자대로 어긴다.
- 계획은 범위 2에서 '기준 폭 환산 **유지**'라고만 적는다. as-built의 기준 폭 환산은 '키 = 기준 폭 키'에 기대고 있으므로, 키가 소자별로 바뀌면 두 소비자를 바꿔야 한다는 사실(재작성 범위)이 빠졌다.

**막히는 경로**

- card WB-1 완료 조건 (4) 9회로 변화표: 기준 bin 밖 소자가 있는 회로는 잡음·mismatch metric 평가에서 실패해 변화표를 못 낸다. 아니면 (5) 판정자가 '12자리 유지'를 대조할 때 2자리가 빠져 불일치가 난다.
- design(S-7)은 '유지'와 '기준 폭' 가운데 하나를 골라야 한다. 이는 as-built 결정 금지에 걸린다.

**고침**

- gb :304·:2246 3·:2250 (5)의 12자리를 정의로 둘로 가른다.
  - 슬라이스 키 소비자 10자리: `ls_fields.py:55`, `metrics_aux.py:119·:120`, `ss_linearize.py:63·:65·:66·:73`, `seal_conduction.py:29`, `seal_saturation.py:36·:42`. 소자별 키를 그대로 읽는다.
  - 기준 폭 소비자 2자리: `noise_devices.py:31`, `metrics_aux.py:181`(→ `device_sigma.py:41`). 범위 2 '읽는 열'에 따라 같은 변경에서 기준 폭 표의 키로 바꾼다(재작성 범위; 옛 읽기 삭제).
- 범위 2에 '기준 폭 열 조회는 소자 슬라이스 키가 아니라 기준 폭 표 키로 한다'를 규칙으로 한 줄 넣는다(키 이름·자리는 design).
- 착수 때 재조사 목록에 `search/iv_noise.py:58`·`search/iv_matching_l.py:66`(탐색 문맥 `d.w_key` -- 범위 2 '출발 구간·층 0이 같은 접근 하나'로 소자별 키가 되면 같은 문제)을 더한다.
- 완료 조건 (1)에 toy 한 줄을 더한다: '기준 bin 밖 소자의 잡음·mismatch가 기준 폭 표에서 읽힘(base = 소자 키로 조회 → `lut_column_unavailable` -- red)'.

| 안 | 내용 | graph 정본 | 물리 | design 단순성 | 근거 |
|---|---|---|---|---|---|
| (가) 권고 | 12자리를 10 + 2로 가르고, 2자리는 기준 폭 표 키로 바꾼다 | `w_key`는 기록 하나 그대로, 기준 키는 LUT 메타(graph 밖 로드 1회) | 잡음·mismatch 표가 기준 폭에만 있음(`읽는 열`) | 바뀌는 자리 2 | `noise_query.py:25-26`, `mismatch_query.py:28-29` |
| (나) | `DeviceOp`에 기준 키 칸을 더한다 | 같은 정의(kind의 기준 폭 키)의 사본 -- graph 규칙 2·3 위반 | 같음 | 칸 증가 | 기각 |

### V9-2 (중간) 불변식 (iv)가 as-built를 보존 대상으로 못박는다(O-153)

**사실**

- gb :304 (iv): '레이아웃 뒤 키 루프(as-built `convergence/converge_point.py` -- 기하 같음 판정·`w_loop_bound` 상한)는 as-built 판정·상한을 바꾸지 않는다'.
- gb :2246 3: '레이아웃 뒤 루프의 판정·상한은 바꾸지 않음'.
- 근본규칙 O-153(gb :371)·DEC-104 (1′)(gb :303)는 'as-built 코드의 구조·자리·블록 경계·이름·서명 … 은 어느 단계에서도 판단 근거가 아니다'라고 적는다. N9.2 9번·:2536은 'design은 현재 코드 재작성까지 염두에 둔다'고 적는다.

**추론**

- (iv)는 원칙에서 유도한 불변식이 아니라 as-built 구현(판정식·상한식)을 규칙으로 고정한다. design이 두 루프의 수렴 판정을 원칙((i)·(iii))으로 하나로 맞추거나 `w_loop_bound`를 재작성하는 길을 계획이 막는다.
- 실측상 as-built 레이아웃 뒤 루프는 (i)(기하 지문이 `eval_key`에 듦, `kernel.py:100`)·(iii)(재방문 = NONCONVERGENT, `converge_point.py:113-114`)을 이미 따른다. 그래서 고정할 이유가 원칙 쪽에 없고, as-built를 지키려는 것 말고는 근거가 없다.
- 검증 8 V8-1이 걱정한 것(범위 5 'DEC-89 재평가 자리 그대로'·MOD8 소유 card와의 충돌)은 '이 card가 레이아웃 뒤 루프를 바꿀 범위가 아니다'는 card 범위 문제다. 이것을 as-built 불변 규칙으로 적을 필요는 없다.

**막히는 경로**

- card WB-1 design(S-7)과 design-validator: N9.2 9번은 블록·모듈마다 재작성 범위·근거를 적게 하는데, (iv)는 레이아웃 뒤 루프를 재작성 후보에서 빼라고 한다. 그래서 design이 O-153과 계획 사이에서 멈춘다.
- 원칙 감사(O-153 후속 '기존 문언 전수 감사')에서 이 판이 새로 넣은 보존 문언이 걸린다.

**고침**

- (iv)를 원칙 불변식으로 바꾼다: '(iv) 레이아웃 뒤 평가도 (i)·(iii)을 따른다 -- 기하(슬라이스 키 포함)는 평가 입력 버전·평가 캐시 키에 들고, 수렴은 상태 재방문 검사이며 순환은 NONCONVERGENT(fail-closed)다. 레이아웃 뒤 루프의 종료 판정 대상(기하 전체)·상한은 그 루프의 정의(DEC-89·N3.17)가 정한다.'
- card 범위로 '이 card(WB-1)는 레이아웃 뒤 루프의 판정·상한을 바꾸지 않는다(범위 밖 -- 소유 = DEC-89 재평가·MOD8 card); as-built가 (i)·(iii)과 어긋나면 그 소유 card의 재작성 범위로 적는다'를 범위 5에 둔다. 규칙이 아니라 범위 진술이다.
- :2246 3도 같게 맞추고, U-130 :2463 '레이아웃 뒤 루프와 같은 것은 키를 평가 입력으로 두는 꼴뿐'은 '(i)·(iii) 원칙은 두 루프 공통'으로 바꾼다.

## 4. 경미

- **V9-3 (i) '평가 캐시 키'의 지시 대상**
  - (ii)로 키 반복이 평가 하나 안이면 θ 단위 캐시(`eval_key`, `kernel.py:100`) 조회는 반복보다 먼저다. 그래서 수렴 키를 그 키에 넣을 수 없다. 출발 키는 θ·선언의 함수라 이미 θ·`context_fp`가 정한다.
  - 판정자가 '`eval_key`에 슬라이스 키 성분이 있는가'를 글자대로 대조하면, design이 넣을 필요 없는 성분(출발 키 지문)을 넣게 된다. 이 성분을 캐시 키용으로 따로 계산하면 출발 키의 둘째 생산자가 된다.
  - :2250 (1) 괄호 '캐시 키에 슬라이스 키'도 같다.
  - 고침: '(i) 슬라이스 키는 평가 입력 버전(S3 graft 색인 키)에 든다. 평가 결과를 다시 쓰는 모든 캐시는 그 결과를 정한 입력(θ·L 칸·선언, 레이아웃 뒤는 기하)을 키로 가진다 -- 다른 키로 계산된 결과를 graft·적중으로 받지 않는다(fail-closed).' (ii)의 'θ → 결과'에 '레이아웃 전 평가'를 붙인다.
- **V9-4 (iii) 상한 초과 때의 결과**
  - '소자마다 키 변경 횟수 ≤ 그 소자 kind의 W-bin 수'를 넘었을 때(벡터 재방문 없이) 무엇이 되는지가 없다.
  - 고침: '넘으면 NONCONVERGENT 실패 레코드(사유에 상한 초과 표지, fail-closed)'를 한 구절 더한다. 완료 조건 (1)의 인위 순환 toy 옆에 '상한 초과 toy'를 둔다.
- **V9-5 op :522 요약 문장**
  - 'LUT 또는 … 판정·측정하는 실행만, 선언 호환 모드로 실행, 없거나 다르면 거부'라고만 하고 선언의 writer 실행 제외를 적지 않는다. 정의 자리 :510·:575와 test :550은 맞다.
  - 고침: :522 괄호에 '(선언의 writer 실행 제외 -- :510)'을 더한다.
- **V9-6 op :510 문체**
  - '… 기존 LUT 옆 선언 측정(이 card -- …) -- 과 LUT·엔진 결과를 쓰지 않는 MC 생성 실행은 …'에서 '-- 과'가 끊겨 읽힌다. :575 꼴로 맞춘다.
- **V9-7 `DeviceOp.w_key` 유지의 근거 문언(O-153)**
  - 유지 근거로 '엔진 소비자 12자리'(as-built 소비자 수)를 든다. 소비자 목록 인용 자체는 재작성 범위로 허용된다. 그러나 '유지' 판단의 근거는 정의여야 한다.
  - 정의상 이 성분은 LUT 슬라이스를 가리키는 키, 곧 기록 참조다(graph 규칙 4 '값 사본 대신 기록 참조'에 해당하고, 값 사본이 아니다). 그래서 유지가 맞다.
  - 고침: 근거를 '성분 = 그 평가가 소자에 쓴 슬라이스의 참조 키(graph 규칙 4) -- 소비자는 착수 때 재조사(아래 목록)'로 바꾼다. 소비자 수는 근거가 아니라 배선 점검 목록으로 둔다.
- **V9-8 '경계 재측정' 용어**
  - op :601 G-14 행은 '경계 재측정'을 기존 LUT 옆 선언 측정의 이름으로 쓴다. :510에서는 거부 목록에서 이 말을 뺐다. 뜻은 맞지만 같은 실행을 :510은 '기존 LUT 옆 선언 측정', :601은 '경계 재측정'으로 부른다.
  - 한 이름으로 맞춘다.

## 5. 바뀐 개념의 전 자리 대조(검사 3)

| 개념 | gain-budget | oracle-portability | 판정 |
|---|---|---|---|
| 키 반복 불변식 (i)~(iv) | :304(정의 한 자리)·:2246 3(요약)·:2250 (1)(5)·:2463 U-130·:11 Status, :1931 X-LA9('키 루프' 이름 그대로 -- 정의 참조로 읽힘) | -- | 서로 일치. (iv) V9-2, (i) V9-3 |
| '고정점' → '키 반복' | 잔존 0(:304·:2250) | -- | 적합 |
| `DeviceOp.w_key` 유지 | :304·:2246·:2250 같은 목록 | -- | V9-1·V9-7 |
| OP-7 거부 제외 | :304 (ii) | :18·:510·:550·:575 일치, :522 V9-5, :601 V9-8 | 적합(경미 2) |
| 다른 계획(offset-strategy·graph-consumption·headroom-chain·offset-trim 등) | 키 루프·`w_key`·OP-7 거부 범위 인용 0(검증 8과 같은 grep, 이 커밋은 다른 계획 파일 변경 0) | -- | 해당 없음 |

## 6. 원칙 점검표(검사 4)

| 원칙 | 판정 | 방법 |
|---|---|---|
| graph 단일 정본 | writer 하나(W 블록), 새 cache·sctx 슬롯 0, 재사용 = graph reuse·S3 graft(입력 버전에 `LutAccess` 지문) -- 적합. `w_key`는 참조 키라 사본 아님(V9-7). V9-1 고침 (나)안은 사본이라 기각 | 엔진 실측 §2 |
| 만들면 배선 | `w_key` 소비자 12자리 실재(배선됨). V9-1의 2자리는 배선이 규칙과 어긋남 | grep |
| DC/AC 분리 | 변경 없음 | 원문 |
| O-127 θ 기저 | 변경 없음 | 원문 |
| EP-7 | 출발 키 = θ·선언 함수(출발값) -- 적합 | 원문 |
| fail-closed | (i)·(iii) 순환 fail-closed 적합. 상한 초과 미기재 V9-4. V9-1은 fail-closed이지만 거짓 거부 | 원문 + 코드 |
| O-153 | (iv) as-built 보존 V9-2, `w_key` 근거 V9-7, 기존 문언 §7 | grep |
| 상수·회로 이름 | 위반 없음(상한 = LUT bin 수 유도) | 원문 |
| 계획/이력 분리 | 옛 문장은 gb history 아홉째 행·op history 일곱째 절로 옮겼다. diff와 일치한다 | diff |
| heldout | 변경 없음 | 원문 |

- U-125~U-131: U-130만 바뀌었고 :304와 맞다(V9-2 고침 때 같이 맞춤). 시점 칸 'card WB-1 design 착수 전'은 순서표와 맞다.
- N2.1·N7.2: DEC-105 상태 칸 변경 없음. X-LA9 '원래 취지와 다름' 표지 유지.
- 순서표: WB-1 :2252(순서) 변경 없음. V9-1 고침의 두 자리(`metrics/*`)는 기존 파일 겹침 card(LI-1·DE-1)와 새 겹침이 없다(`noise_devices.py`·`device_sigma.py`는 2b가 이미 `device_sigma.py` 범위).
- Status: gb :11 '첫째~아홉째', op :18 '첫째~일곱째' 맞다.
- '원래 취지와 다름'·결정 문언 변경 목록: 이 커밋의 결정 문언 변경 = D-4(O-1) 제외 범위(op history 일곱째 절 표지 있음, 취지 같음). 키 루프 문언은 오케스트레이터 판정 철회(:304 표지)라 사용자 결정 문언 변경 아님. 근본원칙 변경 없음.
- 회귀(검증 1~8 적합 항목): 손가락 규칙·포락·짝 규칙·D1 격자 비교·bin 경계 선언 writer/reader·CPG-1·DE-1 배선·소비 기준 축·`DeviceOp.W` 소비자 12곳은 문언이 그대로다. W_request 점 (m, w_f) 미생성(V7-4) 유지. **회귀 없음.**

## 7. O-153 as-built 인용 감사(오케스트레이터 추가 검사 5)

- 기준: 계획 규칙·불변식이 as-built 구조·자리·이름을 근거로 삼거나, '같은 꼴'의 본보기로 삼거나, 보존 대상으로 못박으면 결함이다. 허용되는 인용은 (1) 엔진 밖 사실(PDK bin·ngspice 모드·LUT 열) (2) 재작성 범위(바꿀·지울 코드·소비자 목록) (3) 현재 식별자 지칭(gb :523 '현재 식별자로만 인용')·미구현 gap 표기다.
- 방법: 두 계획 전 판에서 'as-built'(gb 108·op 2), '같은 꼴'(gb 22·op 4), '그대로 쓴다'(gb 6·op 2), 엔진 경로+'같은 규칙'을 python으로 전수 추출해 문맥 260자로 하나씩 분류했다(142건 + 엔진 경로 인용).

| # | 자리 | 문언 | 분류 | 심각도·고침 |
|---|---|---|---|---|
| A-1 | gb :304 (iv), :2246 3 | '레이아웃 뒤 키 루프(as-built `converge_point.py` -- 기하 같음 판정·`w_loop_bound` 상한)는 as-built 판정·상한을 바꾸지 않는다' | **보존 대상으로 못박음** | 중간 -- V9-2 |
| A-2 | gb :272 (DEC-80 bin 폭) | '전력 b_P = max(… `power_resolution_w` … `E/search/objectives.py:13`) 중 큰 값 -- `eps_sweep.py:47-48`과 같은 규칙' | **as-built 코드를 규칙 본보기로** | 경미 -- 같은 문장의 'DEC-80 (ii)·NFR-5와 같은 꼴'이 원칙 근거라 결론은 선다. `eps_sweep.py` 인용을 지우고 식을 규칙으로 적는다(design 착수 영향 없음) |
| A-3 | gb :2385 U-51(닫힘) | '외층 SLSQP가 그 시작점의 반복 상한(as-built `slsqp_outer` 식 maxiter = Σ_i max(⌈log2(상자폭_i / FD 스텝_i)⌉, 1), `slsqp_outer.py:179-181`) 안에 수렴하지 못하면' | **as-built 식을 규칙 정의로** | 경미 -- 식이 문장 안에 있어 규칙은 정의된다. 'as-built `slsqp_outer` 식'과 줄 인용을 빼고 식 자체를 상한 정의로 적는다(사용자 결정 U-51의 결론 불변). 폴백 card 착수 영향 없음 |
| A-4 | gb :304 (DEC-104 R6 목표 행) | '`StartConflict`다(충돌 **기록** 레코드 -- as-built `E/search/start_values.py:66-71` frozen dataclass, `graph/start: conflicts`; 정지가 아니며 …)' | as-built 형태로 정의를 보강 | 경미 -- '충돌 기록, 정지 아님'이 정의다. dataclass 꼴 인용은 식별자 지칭으로 줄인다 |
| A-5 | gb :304 (W-bin 지도), :2242 범위 1 | 'W-bin 지도는 as-built LUT 적재 메타(`_bin_blocks`·`bin_index` …)를 재사용한다', '… 그대로 쓴다(둘째 파서 금지)' | 보존처럼 읽힘(근거는 graph 규칙 1 + PDK 사실) | 경미 -- 'W-bin 지도 = PDK `.model` wmin/wmax에서 유도한 정의 하나(파서 하나 -- graph 규칙 1); as-built `_bin_blocks`가 그 정의면 재사용, 재작성하면 옛 것 삭제'로 원칙을 앞에 둔다 |
| A-6 | gb :304 (매크로 P = 0) | '같은 2배 사다리(사용자 결정 Q2-2 B 원문 … -- as-built `macro_poles.py:316-326` `feasible_start` 단계)' | 근거 = 사용자 결정, as-built = 자리 지칭 | 허용 |
| A-7 | gb :304 '읽는 열'·:290 | '옛 읽기 … (as-built `pre_layout_widths.py:14-22`)를 대체' | 재작성 범위 | 허용 |
| A-8 | gb :304 g_i^(1)·:1849 | 'as-built `iv_gain_l.py:125-127` 결함 …', '… 닫힘 삭제', 'as-built는 마지막 평가 앵커 … 동작 변경' | 재작성 범위·gap | 허용 |
| A-9 | gb :304 D1, :2241 범위 0 | 'as-built 1 ulp 경계 비교(`_helpers_bins.py:6-14`)는 … 고친다' | 재작성 범위 | 허용 |
| A-10 | gb :1891·:1915 | design 41 '(as-built와 같다)' 문장 정정 목록 | 재작성 대상(design 문언) | 허용 |
| A-11 | gb :223 DE-1, :264, :1687, :1696, :2449 | as-built `offset_systematic`·`ls_fields` β/σ/κ는 gap, 대체·삭제 | 재작성 범위 | 허용 |
| A-12 | gb :1452~:1550 IT-1·IT-2 | as-built 쓰기 계획·`_solve_input_window`·`ls_swing.py:114` 전제를 결정에 맞춰 고침, IT-Q2 (나) 'as-built 그대로' 대안 | 재작성 범위·대안 비교의 현 상태 | 허용(대안 (나)는 기각된 안의 현 상태 서술) |
| A-13 | gb :1581·:1593·:1597, :2435 U-101 | `_refine_ends` 삭제, `_solve_input_window` 미수렴, `region_rows`(as-built `_Circuit` 메서드) 접근 경로 | 재작성 범위·식별자 | 허용 |
| A-14 | gb :1793 | 'servo … 봉인점 예측값(as-built `Vo,pred` -- `oracle_netlist.py:441-447`)에 묶는' | 양의 식별(정의 = 봉인점 예측값) | 허용 |
| A-15 | gb :270·:272·:1819~:1843·:1872·:1902·:1924·:2383 | '미구현(as-built는 최소형 …)', F-LA 실측, X-LA2 'as-built 이탈' | gap·실측 진단 | 허용 |
| A-16 | gb :1229·:384 | 'IT-0은 as-built로 병행', 'as-built 데이터 위에서 잰 기준선' | 측정 기준선의 조건(규칙 아님) | 허용 |
| A-17 | gb :2028·:2456 U-123, op :514 OP-12 | as-built `legacy_adapter` `has_load` 결함 수정 | 재작성 범위 | 허용 |
| A-18 | gb :2000·:1978 | as-built `verified_by.py` `KeyError`·`power_dc_w` 정의 불일치 → 계약 개정 | 재작성 범위 | 허용 |
| A-19 | gb :2197 | 'as-built `vds_saturation`도 test만 읽음' | 사실 진술(만들면 배선 판단 자료) | 허용 |
| A-20 | gb :2419·:2420 | 옛 근거 'as-built처럼 올리기만'·'as-built test가 이미 …'를 v6.38.1 C3에서 정정한 표지 | 이미 고친 자리 | 허용 |
| A-21 | gb :2237 | 'design 40 §3.10.1이 소자당 키를 정했고 as-built가 어긋나 있다' | gap | 허용 |
| A-22 | gb :303·:371·:370·:523·:2507·:2536 | O-153·O-152·DEC-104 (1′) 원칙 문언 자체 | 원칙 | 해당 없음 |
| A-23 | op :513 | 'as-built `supply.py:65-69`는 아직 닿지 않음 -- 상위 card SF-1 범위 8이 고침' | 재작성 범위 | 허용 |
| A-24 | gb·op '같은 꼴'(26건) 나머지 | 모두 계획 안 규칙·결정(DEC-74·DEC-80·NFR-5·R9·O-37·D-4 등)이나 산출물 관례(sha256 옆 파일)를 본보기로 든다. 엔진 코드를 본보기로 든 것은 A-2뿐(이 판 :304의 옛 'converge_point와 같은 꼴'은 철회 표지 안 인용) | 계획 내부 참조 | 허용 |
| A-25 | gb '그대로 쓴다'(6)·op(2) 나머지 | JSON 키 이름(:105), GB0 로드 게이트(:1077), ME-1 값(:2018), 엔진 손가락 필드(:2274), 오라클 기준선(op :466·:504) -- 계획 결정이나 측정 자료 | 허용 |

- 요약: 결함 4건(A-1 중간 = V9-2, A-2·A-3·A-4·A-5 경미)이다. 나머지는 재작성 범위·gap·식별자·엔진 밖 사실이다. A-1은 이 커밋이 새로 넣었다. A-4·A-5는 v6.38.2(이 판의 앞 커밋들)에서 들어왔다(`1fefcab1`에 `start_values.py:66-71`·`_bin_blocks` 0건, `git show` grep). A-2·A-3은 이전 판부터 있었다(O-153 후속 전수 감사 대상).

## 8. 재현 명령

```bash
set -e
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6382; R=/c/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12
P=$W/docs/01-plan/features/gain-budget-gmid-sizing.plan.md; O=$W/docs/01-plan/features/oracle-portability.plan.md
E=$R/skills/analog-gmid-design/gmid_engine
git -C $W diff --stat 4efdf9d8..b4451d0f; git -C $W diff --word-diff=plain 4efdf9d8..b4451d0f -- $P $O
grep -rnE "\.w_key\b" --include=*.py $E | grep -v "/lut/\|/tests/"      # DeviceOp.w_key 12자리 + search 2자리
sed -n 20,27p $E/lut/noise_query.py; sed -n 24,29p $E/lut/mismatch_query.py; sed -n 36,41p $E/metrics/device_sigma.py
sed -n 15,31p $E/lut/_helpers_columns.py; sed -n 57,58p $E/metrics/ss_linearize.py
sed -n 94,126p $E/search/kernel.py; sed -n 104,114p $E/convergence/converge_point.py
grep -c "as-built" $P $O; grep -c "같은 꼴" $P $O
git -C $W status --short; git -C $W rev-parse HEAD
```
