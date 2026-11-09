# O-165 재작성 원칙 감사 -- 계획 v6.38.2 (plan-v6382 `b4451d0f`, 기준 `1fefcab1`)

- 역할: O-153 확장(O-165) 감사자, 읽기 전용. 엔진 = `wt/integ-it12` `ebad06c1` (`E` = `skills/analog-gmid-design/gmid_engine`).
- 계획 줄 번호 = `wt/plan-v6382/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(이하 `GB`). 다른 계획은 파일 이름으로 적는다.
- 적용 문언(사용자 원문 O-165 행): (a) 결함 수정이나 결정 반영이 as-built 구조에 맞추려고 루프·불변식·예외·우회·병합 규칙을 덧붙이면, 먼저 그 블록·모듈을 재작성한 단순 구조와 비교(버그 위험·단순성·graph 단일 정본·손계산 속도)하고 단순한 쪽을 고른다. (b) 엔진은 엔진 밖 사실 측정과 재작성 범위에만 인용하고, as-built를 본보기나 보존 대상으로 삼지 않는다.
- 표기: **실측** = 이 감사에서 파일을 직접 읽어 확인한 것, **추론** = 실측에서 끌어낸 판단(측정하지 않음).

---

## 0. 요약

| 구분 | 수 | 내용 |
|---|---|---|
| 재작성 권고 | **5** | R1 DC 블록 재작성(키 루프 불변식 (i)~(iv) 제거, 조건부 -- §1.2 ⚠ 속도), R2 출발 단계 둘째 키 루프 제거(R1과 같은 card), R3 DE-1·WB-1 '나중 병합 card가 배선' 제거, R4 `gain_l_bounds` 분기를 card 하나가 소유(GC-5와 LA-1의 '먼저 병합' 규칙 제거), R5 TB-1 범위 3·4를 LA-1로 옮김('LA-1 통합 병합으로만'과 'SB-1·TB-1 중 먼저' 규칙 제거) |
| 현행 유지(문언만 정정) | 4 | K1 W-bin 지도 재사용, K2 `DeviceOp.w_key` 유지, K3 레이아웃 전/실현 기하 우선 규칙(R1 design에서 재검토), K4 OP-7 거부 범위 |
| (b) 위반 인용 | **9곳**(GB 7 + 같은 내용 반복 2) | §3 표 |
| DC 블록 재작성안 성립 | **조건부 성립** | READS/WRITES 합집합 무모순, SCC 무영향, 레이아웃 뒤 경로는 더 단순해진다. 단 (q1) 입력 포트 W4 뿌리 회로에서는 종속 소자 슬라이스가 노드 풀이에 되먹임돼 '소자 하나짜리 반복'이 아니라 블록 안 벡터 반복이 필요하다. (q2) 병합 블록이 `dc_current`를 READS하게 되어 FD 전류 열에서 노드 풀이 재사용을 잃는다(⚠ 손계산 속도). §1 |

---

## 1. 이미 알려진 실례 재확인 -- W-bin 키 루프 → DC 블록 재작성

### 1.1 계획이 덧댄 것(실측)

- `GB:304` DEC-105 (2) '키 루프' 불변식 (i)~(iv): (i) 슬라이스 키가 평가 입력 버전과 평가 캐시 키에 든다 (ii) 키 반복은 평가 하나 안에서 끝나고 출발 키는 θ와 선언만의 함수다 (iii) 수렴은 소자 키 벡터의 재방문으로 검사하고 상한은 소자 단위(W-bin 수)다 (iv) 레이아웃 뒤 루프(as-built `converge_point`)의 판정·상한은 바꾸지 않는다. 같은 내용이 `GB:2246`(WB-1 범위 3)에 있고 완료 조건 `GB:2250`에도 있다.
- 덧댄 이유가 된 as-built 사실:
  - (1) 노드 풀이(`dc_columns`)와 W 계산(`dc_widths`)이 다른 블록이다. `E/sizing/kernel_run.py:84` `later_blocks = (dc_columns, dc_widths)`.
  - (2) 슬라이스 키를 블록 밖 `LutAccess.w_keys` extras로 kind마다 하나씩 넘긴다. 근거는 `E/sizing/s2_values.py:223-229`, `E/sizing/_helpers_lut.py:29-30` `w_key_of(lut, kind)`, `E/sizing/pre_layout_widths.py:14-22`.
  - 그래서 계획은 W → w_f → 슬라이스 → IDu → W를 블록 사이(평가 수준)의 반복으로 두었고, 블록 함수의 순수성이 보장하던 성질을 불변식 (i)(ii)로 다시 적어야 했다.

### 1.2 재작성안 검증(엔진 블록 선언 기준)

**재작성안 R1**: `dc_columns` + `dc_widths`를 DC 블록 하나로 합친다. 블록 안 순서는 다음과 같다.
1. 쓰기 소자: W = ID·L/exp(θ ln IDu)(DEC-88)를 구하고, 이어서 손가락 규칙 → (m, w_f) → 슬라이스 키를 정한다. 반복은 없다.
2. 노드 풀이(SCC 위상 순서)를 한다.
3. 종속 소자: 순방향 IDu로 W를 구한 뒤 키를 고르는 소자 단위 반복을 돌린다.
4. `dc_op`와 (m, w_f)를 쓴다.

슬라이스 키는 블록 안 값이고, `dc_op.w_key`가 그 기록이다.

| 점검 | 결과 | 근거(실측) |
|---|---|---|
| READS/WRITES | **성립**. READS = `dc_columns` READS(`E/sizing/block_columns.py:95-100`) ∪ `dc_widths` READS 가운데 블록 밖 필드(`dc_current`, `dc_v`·`dc_ln_idu`는 블록 안에서 생기므로 뺌; `E/sizing/block_widths.py:23-26`). WRITES = `dc_v`, `dc_path_values`, `dc_window`, `dc_ln_idu`, `dc_scc_log`(`block_columns.py:101-102`) + `dc_op`(`block_widths.py:27`) + (m, w_f). 하류 READS 이름은 바뀌지 않는다. 봉인 4·스냅샷 keep은 `later_blocks`에서 자동으로 따라온다(`kernel_run.py:84-87`) | 같은 곳 |
| 쓰기 소자 키 = θ 함수 | **성립**. 쓰기 소자는 Kruskal 트리 변(`E/sizing/writer_plan.py:191` `COORD_WRITER`)이고, 노드 writer 식의 VGS는 θ ln IDu에서 나온다(`block_columns.py:182-191` `self.ln_idu`는 θ, `:820-822` 쓰기 소자 ln IDu = θ). W는 슬라이스와 무관하므로 키는 노드 풀이 전에 정해진다 | 같은 곳 |
| SCC | **무영향**. SCC 쓰기 소자 = `COORD_WRITER`이다(`block_columns.py:607-611` writers). 그들의 슬라이스는 1에서 이미 정해졌으므로 GS·Newton(`:618`, `writer_grad :470-500`)은 `w_key_of(kind)`를 소자 키로 바꾸기만 하면 된다. 종속 소자(`DEP_FIXED/PARALLEL/CYCLE`, `writer_plan.py:209-213`)는 노드를 쓰지 않는다 | 같은 곳 |
| 종속 소자 '소자 하나짜리 반복' | **부분 성립(q1)**. 입력 포트 W4 뿌리가 없는 회로에서는 노드 값이 종속 소자 슬라이스와 무관하므로 소자마다 독립 반복이다(키 공간이 유한해 끝나거나 재방문 → NONCONVERGENT). 그러나 아래 네 곳이 **모든 `dc_coord` 소자**(종속 포함)의 슬라이스를 노드 풀이 안에서 읽는다. ① `region_rows`의 VDSAT·tol_VDSAT(`block_columns.py:247-268`) → `input_windows`(`:270-278`) → A6 되풀이(`_solve_input_window :727-781`)의 y 범위 `override` → 노드전압 ② `_tolerance`(`:695-701`)는 모든 coord 소자의 tol_V 셀 ③ `_interior_solution`의 시도 수 상한(`:709-712`) ④ 쓰기 소자 없는 SCC의 허용오차 대체(`:611` '단자가 닿는 MOS'). 그래서 **입력 포트 W4 뿌리 회로**(library 7회로가 `input_dc: pending SP-2` -- `GB` U-128)에서는 종속 키 벡터 → 창 → 노드 → 종속 키의 되먹임이 생긴다. 이 경우 블록 안 바깥 반복(종속 키 벡터가 바뀌면 다시 풂, 재방문이면 NONCONVERGENT)이 필요하다. 상한 '소자마다 W-bin 수'(`GB:304` (iii))만으로는 벡터 반복의 종료 규칙이 안 된다. 재방문 검사가 실제 종료 근거이고 소자 단위 상한은 넘을 때의 처리가 정의되지 않았다(**계획 (iii) 문언 결함** -- 재작성 여부와 무관하게 고칠 것) | 같은 곳 |
| 평가 캐시 키 | **성립**. 레이아웃 전 키는 θ와 선언의 함수다. 지금 평가 키 = (context_fp, schema_fp, θ, cells, 기하 지문)(`E/search/kernel.py:100`)라 θ로 충분하다. 계획 불변식 (i)의 '평가 캐시 키에 슬라이스 키'는 (ii)가 성립하면 중복이고, 재작성하면 구성상 참이 된다(블록 입력 버전 = 투영 값 지문, `E/core/projection.py:8`) | 같은 곳 |
| 레이아웃 뒤 실현 기하 경로 | **성립하고 더 단순해진다**. 실현 W는 `w_request`로 모든 배치 소자에 고정되고(`E/convergence/realized_geometry.py:7-8`, `:20`), 키는 소자의 실현 finger_w(대기 소자는 요청 슬라이스)에서 바로 정해진다. 따라서 레이아웃 뒤에는 키 반복이 없다. 'kind당 슬라이스 하나' 때문에 있던 `kernel_keys`(`E/convergence/kernel_keys.py` 전체)와 `place_layout`의 폭 키 좁히기(`E/convergence/place_layout.py:9`, `:44-56`)가 통째로 사라진다. `key_exclusion`(`E/convergence/key_exclusion.py:5-7` -- kind 키 하나를 뺌)은 소자·그룹 단위로 다시 정해야 한다(design). `converge_point`의 기하 같음·주기 판정(`converge_point.py:96`, `:113`, `:135`)은 `w_keys`를 소자 키 튜플로 읽기만 하면 된다 | 같은 곳 |
| **손계산 속도(q2)** | **⚠ 손해 가능**. 지금 노드 블록은 저항 전류만 READS하도록 일부러 갈라 두었다(`E/sizing/block_currents.py:7-9` 'MOS·이상원 전류만 바뀐 θ 에서 노드전압 블록과 그 하류가 다시 돌지 않게', `block_columns.py:26-27`). FD 야코비안은 그 재사용을 전제로 한다(`E/search/fd_jacobian.py:6-7` '전류 성분은 ④ 노드전압을 건드리지 않는다, 설계 2.2'). 병합 블록은 종속 W에 `dc_current`가 필요하므로 그 열 전체를 READS한다. 그러면 θ 전류 FD 열마다 노드 풀이가 다시 돈다. 계획안(키 = extras)은 bin을 넘지 않는 FD 걸음에서 키가 같아 재사용을 지킨다. 손실 크기는 **측정하지 않았다**(9회로 실행의 블록별 reuse 계수 `counters` -- G-10에서 FD 단계의 `dc_columns` reuse 비율로 잰다) | 같은 곳 |

**판정**: 재작성안은 논리상 성립한다. 불변식 (i)(ii)는 블록 순수성으로 구성상 참이 되고 (iv)는 대상이 없어진다. `LutAccess` 소자 키 운반, `pre_layout_lut_access`, `kernel_keys`, 폭 키 좁히기도 지울 수 있다. 다만 **q2 속도 손해 때문에 무조건 단순하다고 할 수 없다**. 권고는 다음과 같다.
- **기본 = R1 재작성**: 버그 위험이 가장 낮다. 평가 사이 키 불변식과 graft 안전 조건이 사라진다.
- **design 착수 전 게이트**: 9회로 G-10 계수로 FD 단계의 `dc_columns` reuse 비율과 벽시계를 잰다. 손실이 크면(판단 = 사용자, 새 문턱 상수 금지) **R1-b**로 간다. R1-b는 쓰기 소자 기하 블록 G(`dc_current`·`dc_L`·θ ln IDu → 쓰기 소자 (m, w_f)·키 필드, 반복 없음)를 두고, 노드 블록이 그 필드를 READS한다(값 지문이 같으면 재사용). 종속 소자 키는 W 블록 안 소자 단위 반복으로 정한다. 이때 q1 결합(입력 포트 W4 뿌리 회로)만 평가 수준 키 반복이 남는다. 이 둘째 갈래는 계획 불변식의 적용 범위를 'q1 회로'로 좁힌 꼴이다.
- 어느 쪽이든 (iii)의 종료 규칙은 '재방문 = NONCONVERGENT, 키 공간 유한'으로 고치고, '소자 단위 상한'은 근거와 넘을 때의 처리를 정하거나 지운다.

---

## 2. 'as-built 구조에 맞추려 덧댄 것' 전수 표

판별 신호는 네 가지로 본다. ⓐ as-built 함수·파일을 본보기('같은 꼴')나 보존 대상으로 못박음 ⓑ 두 card 사이의 '나중 병합/먼저 병합' 규칙이 as-built 블록·card 경계에서 생김 ⓒ 같은 개념을 여러 card가 나눠 고침 ⓓ 예외·우회·포락·이중 경로.

### 2.1 재작성 권고

| # | 현재 규칙·위치 | 덧댄 이유가 된 as-built 사실 | 재작성안 | 비교(버그 위험 / 단순성 / graph 정본 / 속도 / card 수) | 권고 | 재작성 시 지울 옛 코드·소비자 |
|---|---|---|---|---|---|---|
| R1 ⓐⓓ | 키 루프 불변식 (i)~(iv) -- `GB:304` DEC-105 (2) '키 루프', `GB:2243`(범위 2 `LutAccess` 소자별 폭 키), `GB:2246`(범위 3), `GB:2250` 완료 조건 일부, U-130 행 '키 반복' 구절 | `dc_columns`/`dc_widths` 분리(`kernel_run.py:84`), 슬라이스 = 블록 밖 `LutAccess.w_keys`(kind당 하나 -- `s2_values.py:223-229`, `pre_layout_widths.py:14-22`, `kernel_keys.py:5-6`) | §1.2 R1(DC 블록 하나, 키는 블록 안 값, `dc_op.w_key` 기록). 속도 게이트 실패 시 R1-b | 버그: 평가 사이 키 불변식·graft 조건·출발 키 함수 → 블록 안 반복 하나(↓↓) / 단순성: 불변식 4 → 종료 규칙 1, kind 충돌 좁히기 없음(↓) / 정본: 키 운반 extras 제거, (m, w_f)·W의 writer가 한 블록(=) / 속도: q2 ⚠ FD 전류 열 재사용 손실 가능(측정 필요) / card: WB-1 범위 2·3 축소, LI-1 `kernel_keys` 파일 겹침 소멸 | **재작성(조건부 -- §1.2 게이트)** | `E/sizing/block_widths.py`(병합), `block_columns.py`의 `w_key_of` 6곳(`:122`, `:152`, `:255`, `:353`, `:378`, `:488`), `E/sizing/pre_layout_widths.py` 전체, `E/sizing/_helpers_lut.py:29-30` `w_key_of(kind)`, `LutAccess.w_keys` 의미(`s2_values.py:223-231`), `E/convergence/kernel_keys.py` 전체와 `convergence/__init__.py:34`·`:71`, `place_layout.py` 폭 키 좁히기(`:9`, `:44-56`), `key_exclusion.py` kind 단위 규칙(재정의), `search/kernel.py:96` `LutAccess` 교체, `realized_geometry.py` `w_keys` 인자, `converge_point.py:96` `sctx.dc.lut.w_keys`, `pipeline/stage_b.py:29`·`:152`, `sizing/__init__.py:5`·`:9`·`:12`·`:19`·`:277`·`:295`·`:301`, `_module_map.py:576`·`:620`·`:622`, `kernel_run.py:18`·`:21`·`:84`·`:97-99`, `block_currents.py:7-9` 머리 문장, tests(착수 때 grep) |
| R2 ⓓ | 출발 단계 둘째 키 반복 -- `GB:2245` 범위 2b `iv_matching_l` '출발 단계 계산이라 필드 READS가 아니라 커널과 같은 손가락·선택 함수와 키 반복 불변식(출발값, EP-7)', `GB:304` '전류가 정해진 뒤에는 커널과 같은 손가락·선택 함수와 같은 키 반복 불변식' | 출발 단계가 W를 따로 계산한다(`E/search/iv_matching_l.py:57-63` `w = max(I·L/IDu, W_min)`, kind 키 `d.w_key`) | 손가락·키 선택을 **순수 함수 하나**(W, kind, L → (m, w_f, 키))로 두고 DC 블록과 출발 단계가 그 함수를 부른다. 출발 단계의 IDu는 출발 곡선 값이고 출발값(EP-7)이다. 키 반복은 출발 단계에서도 같은 함수 안의 소자 단위 반복이라 불변식을 다시 적을 필요가 없다 | 버그: 같은 규칙의 둘째 기술 제거(↓) / 단순성(↓) / 정본: 함수 하나(=, graph 규칙 1 위반 아님 -- 출발값은 정의 축이 다름) / 속도 = / card 0 | **재작성**(R1과 같은 card) | `iv_matching_l.py:57-63` 폭·키 계산, `E/metrics/device_sigma.py:17-31` ceil(W/w_top) 분할, `E/metrics/ss_linearize.py:68` `pre_layout_geometry(w_m, W/w_m)` -- 이 셋은 계획 범위 2b가 이미 바꾸게 되어 있음, 정의 자리만 R1 함수로 |
| R3 ⓑ | 'DE-1·WB-1 가운데 나중에 병합되는 card가 (m, w_f) READS를 배선' -- `GB:304` 'DE-1 배선', `GB:1243`, `GB:1686`, `GB:2244`, `GB:2252`, 완료 조건 `GB:2250` (5) '(DE-1이 병합돼 있으면)'; ΔW 변화 원인 '나중 병합 card의 변화표' | 두 card의 선후가 고정되지 않았고(O-126 계열 '파일 겹침만'), (m, w_f)가 아직 없다 | **선후 고정 WB-1 → DE-1**. WB-1은 이미 LA-0 앞이고 EO-1 뒤다(`GB:2252`). DE-1도 EO-1 병합 선행이다(`GB:1243`). DE-1은 처음부터 (m, w_f)를 READS한다 | 버그: 조건부 배선 두 갈래 → 하나(↓) / 단순성(↓) / 정본 = / 속도 = / card 수 0, DE-1이 WB-1을 기다림(일정 비용) | **재작성(규칙 교체)**. 단 O-126 'LA-1과 DE-1 선후 고정 없음'과는 별개 쌍이라 그 결정을 바꾸지 않는다 | 계획 문언 6곳(위), DE-1 완료 조건의 조건부 toy |
| R4 ⓑⓒ | 이득 L 하한 '전류 충돌 사유 분기 = GC-5와 같은 분기 하나, 두 card 가운데 먼저 병합되는 쪽이 분기를 만들고 나중 card는 사유만' -- `GB:304` DEC-105 (1), `GB:1849` 범위 15 (a), `graph-consumption.plan.md:459` | `gain_l_bounds`(`E/search/iv_gain_l.py:118-130`)가 GC-5의 '네 함수·여섯 호출 자리' 가운데 하나(`graph-consumption.plan.md:458`)이고, LA-1도 같은 함수를 고친다 | `gain_l_bounds` **전체 재작성은 LA-1 범위 15 (a) 하나가 소유**한다. 함수가 130줄 이하이고 목표·닫힘·최선 앵커·사유 분기가 모두 여기서 바뀐다. GC-5는 그 함수를 범위에서 빼고 나머지 셋(`matching_bounds`·`area_bounds` 등)만 맡는다. 충돌 표지 입력(1회차 전류)은 GC-5가 만드는 필드를 READS한다 | 버그: 병합 순서에 따라 갈리는 두 구현 → 하나(↓) / 단순성(↓) / 정본: 분기 하나(=) / 속도 = / card 수 0 | **재작성(소유 재배정)** -- graph-consumption 계획 개정 필요 | `iv_gain_l.py:125-127` 닫힘(계획에 있음), GC-5 범위 문언(`graph-consumption.plan.md:458-459`) |
| R5 ⓑⓒ | TB-1 범위 3 '합 행과 이 정정은 소비자(R6 = LA-1)와 같은 통합 병합으로만', 범위 4 '**LA-1 통합 병합으로만**'·'만드는 card는 SB-1과 이 card 가운데 먼저 병합되는 쪽' -- `GB:2194-2195`, `GB:304` (4)·(5) | TB-1은 R6 ⇄ HC-1 순환을 끊으려고 만든 '필드만 card'다(O-144 J3). 범위 3·4는 그 순환과 무관하고 소비자가 LA-1 하나뿐인데 TB-1에 얹혀서 '소비자 0 금지'를 병합 규칙으로 지키게 됐다 | 범위 3(가드 필드 형식·합 행 정정)과 범위 4(술어 인스턴스 S0 필드)를 **card LA-1 범위 15로 옮긴다**. R10 '바이어스 고정 넷' 술어 부정 함수의 제작 card를 하나로 고정한다(SB-1이 R10 구현 card이므로 SB-1 -- 단 SB-1이 LA-1 뒤라면 LA-1이 만들고 SB-1이 부름 -- 순서표로 하나만 남김) | 버그: 병합 조합 3갈래 → 1(↓) / 단순성(↓) / 정본 = / 속도 = / card 수 0(범위 이동), TB-1 범위 1·2만 남아 O-149 규칙이 단순해짐 | **재작성(범위 이동)** -- O-144 J3·O-149의 TB-1 범위 정의를 바꾸므로 **사용자 승인 대상** | 계획 문언(`GB:2194-2195`, `GB:304` (4)·(5)의 'card TB-1 범위 3·4', CPG-1 선행 목록 `GB:1241`·`GB:2281`의 'TB-1 범위 3·4') |

### 2.2 현행 유지(문언 정정만)

| # | 현재 규칙·위치 | as-built 사실 | 판단 | 문언 정정 |
|---|---|---|---|---|
| K1 ⓐ | W-bin 지도 = as-built `lut_set.py` `_bin_blocks`·`bin_index` '그대로 쓴다' -- `GB:304`, `GB:2242` | PDK `.model` wmin/wmax 파서가 하나 있다 | 유지. 파서 하나는 graph 규칙 1(둘째 생산자 금지)의 근거이고 as-built 보존이 아니다. 그런데 같은 card 범위 0이 `bin_index`를 고치므로 '그대로'는 사실과 다르다 | '정본 = PDK `.model` wmin/wmax 파싱 하나(지금 자리 `lut_set.py`), 경계 판정은 범위 0의 격자 비교'로 |
| K2 ⓐ | `DeviceOp.w_key` 유지 -- '엔진 소비자 12자리' -- `GB:304`, `GB:2246` | 소비자 12자리(실측 근거는 계획 인용, 이 감사는 재측정 안 함) | 유지. R1에서도 소자가 쓴 슬라이스의 기록은 물리적으로 필요하다(소신호·봉인이 같은 슬라이스를 읽어야 함). 다만 유지 이유가 소비자 수이면 (b) 위반이다 | 이유를 '그 평가가 소자에 쓴 슬라이스 -- 소신호·봉인·잡음이 같은 슬라이스를 읽는 정본'으로 |
| K3 ⓓ | 레이아웃 전 (m, w_f)와 레이아웃 실현 필드가 함께 있으면 실현 필드 우선, W_request 재봉인점에서는 레이아웃 전 (m, w_f)를 만들지 않음 -- `GB:304` | `w_request` 경로(`block_widths.py:10-13`), 실현 기하 extras(`realized_geometry.py`) | R1에서는 DC 블록 입력 기하가 하나다(규칙 기하 또는 실현 기하). 그래도 우선 규칙을 없애려면 '평가에 쓴 기하' 필드가 레이아웃 필드의 값 사본이 되어 graph 규칙 4와 부딪힌다. 지금 꼴이 최소에 가깝다 | 유지. R1 design에서 다시 판단할 항목으로 등록 |
| K4 | OP-7 거부 범위·writer 실행 제외 목록 -- `oracle-portability.plan.md:510`, `:575`, `:601` | 엔진 as-built와 무관(oracle 실행 설정) | (a) 대상 아님. 검증 회차마다 목록이 넓어진 꼴이지만 fail-closed 정의라 유지 | -- |

---

## 3. (b) 허용 범위 밖 엔진 인용(as-built를 근거·본보기·보존으로 씀)

| # | 위치 | 문장(요지) | 종류 | 고칠 꼴 |
|---|---|---|---|---|
| B1 | `GB:304` DEC-105 (2) | 'writer = W 블록(`DeviceOp.W` writer, **as-built `dc_widths`**) 하나가 `DeviceOp.W`와 함께 씀' | 보존(as-built 블록 경계를 writer 자리로 못박음 -- R1의 원인) | 'writer = W를 쓰는 DC 블록(자리는 design, 재작성 가능)' |
| B2 | `GB:304` 키 루프 (iv) | '레이아웃 뒤 키 루프(**as-built `converge_point.py`** -- 기하 같음 판정·`w_loop_bound` 상한)는 **as-built 판정·상한을 바꾸지 않는다**' | 보존 | 규칙(N3.17 LY1·LY3 고정점·상한)을 인용하고 as-built는 지움 |
| B3 | `GB:2246` 범위 3 | '레이아웃 뒤 루프의 판정·상한은 바꾸지 않음' | B2와 같음(반복) | 같음 |
| B4 | `GB:304`, `GB:2246` | '`DeviceOp.w_key` … 유지한다: **엔진 소비자 12자리**' | 보존 근거 = as-built 소비자 수 | K2 문언 |
| B5 | `GB:304`, `GB:2242` | 'W-bin 지도는 as-built LUT 적재 메타 … 재사용' / '**그대로 쓴다**' | 본보기·보존(일부는 정본 근거로 허용) | K1 문언 |
| B6 | `GB:304`, `GB:2243` | '슬라이스 키는 기존 LUT 접근 키(`LutAccess` 폭 키) 성분으로만', '`LutAccess` 폭 키를 … 소자별로 바꾸고' | 보존(as-built 키 운반체를 정본 꼴로 둠 -- R1의 원인) | '슬라이스 키는 블록 입력 버전에 드는 값(운반 형식은 design)' |
| B7 | `GB:304` DEC-105 (3) | '같은 2배 사다리 -- **as-built `E/search/macro_poles.py:316-326` `feasible_start` 단계** … 사다리 끝 처리는 그 사다리 규칙 그대로' | 본보기(코드를 규칙 정의로) | 규칙 출처를 design 41 §6.5 사다리 정의로. as-built 줄은 LA-1 범위 15 (b)의 재작성 범위로만 인용(`GB:1849`는 이미 그렇게 씀) |
| B8 | `GB:304` DEC-105 (4) | '`StartConflict`(충돌 기록 레코드 -- **as-built `E/search/start_values.py:66-71` frozen dataclass**, `graph/start: conflicts`)' | 본보기(as-built 타입을 정의로) | 정의 = '충돌 기록(정지 아님, margin·사유, `graph/start` 출력 필드 -- N3.14)'. 타입은 design |
| B9 | `GB:2245` 범위 2b | '`iv_matching_l` … **출발 단계 계산이라** 필드 READS가 아니라 커널과 같은 … 키 반복 불변식' | 보존(as-built 단계 경계를 둘째 반복의 근거로) | R2 |

허용 범위 안이라 세지 않은 인용: 다음은 결함 사실이거나 재작성·삭제 범위로 인용한 것이다.
- `iv_gain_l.py:125-127` 결함, `previous[1]` 동작 변경 표지
- `_helpers_bins.py:6-14` 결함
- `pre_layout_widths.py:14-22` 대체 대상
- `kernel_keys.py:5-6` design 어긋남 사실
- `supply.py:65-69` 미배선 사실
- `eng2spice.py:3` 관례 대체
- `block_widths.py:10-13` W_request 사실
- LA-1 범위 15 (a)·(b) 삭제 범위

**합계 9곳**(서로 다른 문장 7, 반복 2).

---

## 4. 재작성 권고가 card 구조를 줄이는 방식

R1·R2를 받으면 WB-1은 다음 세 범위로 줄어든다. 그러면 계획 순서 규칙이 정리된다.
- 범위 0 bin 격자 비교
- DC 블록 재작성(쓰기 소자 키 → 노드 풀이 → 종속 소자 키 → `dc_op`·(m, w_f))
- 손가락·키 순수 함수 하나와 그 소비자 전환(2b)

정리되는 순서 규칙은 다음과 같다.
- **키 루프 불변식 (i)~(iv)와 그 완료 조건 toy 4종**(같은 θ 재평가 비트 동일·다른 계보 같은 점·인위 순환·캐시 키)이 블록 순수성 하나로 줄어든다.
- `kernel_keys`가 지워지므로 **LI-1과의 파일 겹침 행**이 사라진다.
- R3로 **DE-1 '나중 병합 card가 배선'** 규칙과 ΔW 변화 원인의 소유 갈래가 '순서 WB-1 → DE-1' 한 줄이 된다.

R4는 GC-5와 LA-1 사이의 '먼저 병합되는 쪽이 분기' 규칙을 없앤다. R5는 TB-1의 세 병합 갈래('첫 행동 소비자와 통합', 'LA-1 통합으로만', 'SB-1·TB-1 중 먼저')를 범위 1·2의 O-149 규칙 하나로 줄인다. 그 결과 N6.1 순서표에서 조건부 선후(병합 순서에 따라 갈리는 배선 주체)가 다섯 쌍에서 두 쌍으로 준다. 남는 두 쌍은 이미 사용자 승인된 O-159 E-1(R6 재개방 판정 함수 DE-1·LA-1)과 O-151 DK2(R9 조회 함수 DE-1·SB-1)이다. 이 둘도 같은 신호(ⓑ)에 해당하지만 승인 결정이라 이 감사는 '같은 꼴의 기존 규칙'으로만 표지한다(재검토는 사용자 몫). CPG-1 선행 목록의 'TB-1 범위 3·4'는 'LA-1 범위 15'에 흡수된다. card 수는 변하지 않는다. 각 card 안 범위와 병합 규칙이 단순해진다.

---

## 5. 원칙 점검(재작성안 R1~R5)

| 원칙 | R1 | R2 | R3 | R4 | R5 |
|---|---|---|---|---|---|
| graph 단일 정본(writer 하나, 새 cache·memo·sctx·사본 0) | 충족 -- `dc_op`·(m, w_f)·`dc_v` writer가 한 블록, 키는 블록 안 값(사본 아님), LUT memo는 N3.3 예외 그대로. R1-b는 쓰기 소자 기하 필드 writer = G 블록 하나 | 충족 -- 함수 하나 | 충족 | 충족 -- 분기 하나 | 충족 |
| 만들면 배선 | (m, w_f) 소비자 = 슬라이스 선택·EO-1 넷리스트·2b·DE-1(R3로 처음부터) | 충족 | 충족(조건부 배선 제거) | 충족 | 충족 -- 필드와 소비자가 같은 card |
| DC/AC 분리 | 충족 -- DC 블록만, 슬라이스는 DC 열만(`GB:304` '읽는 열') | 충족 | -- | -- | -- |
| O-127 θ 기저 | 충족 -- 쓰기 소자 W는 θ 함수(DEC-88), 종속 소자는 종속 | 충족 | -- | -- | -- |
| EP-7 출발값 | 충족 -- 출발 단계 결과는 출발값 | 충족 | -- | 충족 | -- |
| fail-closed | 충족 -- 슬라이스 없음·재방문 = 실패 레코드. **(iii) 소자 단위 상한 초과 처리 미정의는 계획 결함**(재작성과 무관하게 정정) | 충족 | -- | 충족 | -- |
| 상수·회로 이름 금지 | 충족 -- 새 상수 없음. ⚠ §1.2 게이트에 '손실이 크면'의 문턱 상수를 두지 말 것(사용자 판단) | 충족 | -- | -- | -- |
| **gm/ID 손계산 속도** | **⚠ q2** -- 병합 블록은 `dc_current` READS로 FD 전류 열의 노드 풀이 재사용을 잃는다(`block_currents.py:7-9`, `fd_jacobian.py:6-7`). 측정 전에는 R1을 확정하지 말 것 | = | = | = | = |
| 근본원칙 적용 승인 | R1·R2는 계획 DEC-105 (2) 문언 변경, R5는 O-144 J3·O-149 범위 변경, R4는 graph-consumption 계획 변경 -- **모두 사용자 승인 뒤 계획 개정**(O-165 자체 적용 문언도 승인 대상) | | | | |

**원래 취지와 다름**:
- R1은 검증 8 V8-1이 정한 '키 = 평가 입력'(`GB:304` 키 루프 머리)을 뒤집는다.
- R3은 O-126 계열의 '파일 겹침만(선후 고정 없음)' 관행을 이 쌍에서 깬다(선후 고정 추가).
- R5는 O-144 J3 TB-1 범위를 줄인다.

---

## 6. 측정 출처

- 엔진: `wt/integ-it12` `ebad06c1` 파일을 직접 읽었다.
  - `sizing/block_columns.py:1-102`, `:175-278`, `:470-500`, `:559-620`, `:685-790`, `:814-849`
  - `sizing/block_widths.py` 전체, `sizing/pre_layout_widths.py` 전체, `sizing/_helpers_lut.py` 전체
  - `sizing/kernel_run.py:1-105`, `sizing/writer_plan.py:184-215`, `sizing/s2_values.py:223-231`, `sizing/fixed_point.py` 전체, `sizing/block_currents.py:6-10`
  - `convergence/kernel_keys.py`·`realized_geometry.py` 전체, `convergence/converge_point.py:1-40`·grep, `convergence/place_layout.py:36-60`, `convergence/key_exclusion.py:1-15`
  - `lut/_helpers_bins.py` 전체, `core/projection.py:1-45`, `search/kernel.py` grep, `search/fd_jacobian.py:1-10`·grep
  - `search/iv_matching_l.py:50-66`, `search/iv_gain_l.py:118-130`, `metrics/device_sigma.py:10-33`, `metrics/ss_linearize.py:60-75`
- 계획:
  - `git -C wt/plan-v6382 diff 1fefcab1..b4451d0f`(8 파일)과 word-diff 추가 조각
  - `GB:304` DEC-105 행 전체, `GB:1239-1249`, `GB:1762-1779`, `GB:1849`, `GB:2186-2200`, `GB:2233-2282`, `GB:2458-2464`
  - `graph-consumption.plan.md:458-459`, `oracle-portability.plan.md:510`·`:575`·`:601`
- 측정하지 않은 것:
  - FD 단계 `dc_columns` reuse 비율(q2)
  - `DeviceOp.w_key`·`DeviceOp.W` 소비자 12자리(계획 인용을 그대로 씀)
  - 입력 포트 W4 뿌리 회로 수(U-128 결정에 따라 바뀜, 계획 인용 '7회로 pending' 사용)
