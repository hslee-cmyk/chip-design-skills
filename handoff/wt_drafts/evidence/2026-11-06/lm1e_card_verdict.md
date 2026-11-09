# LM-1e spec·interface card 독립 판정 (card id `20261106-lm1e`)

- 대상: worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261106-lm1e-card`, 브랜치 `card/lm1e`, 커밋 `27b659cc`(WB-1 머리 `6887bc3e`를 `934e00a8`로 병합한 위). 파일 = `docs/02-design/specs/20261106-lm1e.spec.md`(228줄), `20261106-lm1e.interface.md`(192줄). worktree는 깨끗하고, 수정·커밋하지 않았다.
- 판정자 = 독립 agent(card 작성자 아님).
- 기준:
  - 같은 worktree의 계획 v6.38.25 N6.40 LM-1e(P:2645~2652), N3.6 표 10행(P:663), 표 #24
  - design 40 v1.16.22 §3.7-A 7(:1250)·§3.10.8(:1465), design 42
  - O-242·O-246 D7, A-139·A-140·A-141
  - `o246_plan_verdict.md` m3(:92), `lm1d_run_verdict.md`(:40~42)
  - CLAUDE.md O-229
- 방법: `git -C` 읽기, grep·sed(읽기만). ngspice·pytest·엔진 import·python 실행은 0이다.

## 결론: Major 2, minor 5

## 1. 계획 문언 대조 (항목 1)

| 계획 | card | 판정 |
|---|---|---|
| 1 적재 (kind, w_key), `width_differs` 삭제, 위치 선언 = 통합 병합 안 | spec 범위 1·재작성 범위, interface §1·§2 | 같음 |
| 2 D7 적재 거부, 범위 = `widths()`, 사유 `bin_missing_external`(기존 어휘), W_min 아래 대상 밖, 런타임 None 갈래 없음, 표 구성 불변 | spec 범위 2, interface §3(검사 자리 = 구성 뒤, `widths` 정의 1곳) | 같음. 검사 자리 '구성 뒤'는 계획이 정하지 않은 것을 card가 정했다(design 몫 -- M-2) |
| 3 판정 갈래 (a)(b)(c), 집계 규칙 = N3.6 표 10행, None 원인 = 켜진 격자점 없는 셀 | spec 범위 3, interface §5 | **다름 -- M-1** |
| 4 소비자 전수 | spec 범위 4·재작성 범위, `cell_floor`·`sat_threshold` 추가 발견 | 같음(더 넓음) |
| 5 조건부 표지 소멸 | spec 범위 5 | 같음 |
| 6 완료 (1)~(6) | spec 완료 1~7 | (1)의 갈래 toy가 계획의 None 원인과 다르다(M-1). 나머지는 같음 |
| 순서: design(S-7) → spec/interface card, D42 LM 행 | spec 착수 조건 3 '일부 충족' | **다름 -- M-2** |

## 2. Major

### M-1 집계 규칙이 실제 조회 경로에 구현되어 있지 않은데, card는 '이미 구현, 코드 변경 0'이라고 적었다. 갈래 toy도 계획의 None 원인을 쓰지 않는다 (계획과 다름·fail-closed)

- 사실(원 파일): `lut/_helpers_loo.py:143-154` `table_at`(= `TolVTable.at`, `tolerance.py:108-118`)은 조회점 (L, VDS)를 덮는 셀 최대 넷(앵커 lo·hi × VDS 칸 k·k+1)을 다음과 같이 합친다.

  ```python
  vals = [v for v in vals if v is not None]
  return max(vals) if vals else None
  ```

  docstring도 "정의된 값의 최댓값"이라고 적었다.
- 이 조회가 봉인과 SCC tol의 입력이다.
  - 봉인 허용오차 블록 `sizing/seal_tolerances.py:32`(`dc_tol_v` writer)
  - SCC 순환 수렴 `sizing/block_dc.py:370-373` `tol_cell`
- 따라서 '봉인 항목이 쓰는 셀과 그 집계'(표 10행 범위) 안에서 tol 셀 max 집계를 '정의된 항만으로' 낸다. 이것은 표 10행·A-139 집계 규칙과 어긋난다(O-242 기각안 D와 같은 꼴).
- 실제 데이터에서도 일어난다.
  - LM-1d 판정(`lm1d_run_verdict.md`:40~42)에 따르면 실제 LUT의 tol_V 셀은 VDS 격자 k = 0(VDS = 0 V)에서 None이다(ID·GM 0, 8/8 앵커).
  - 그래서 조회 VDS가 첫 VDS 칸 [0, Δ) 안이면 k = 0의 None을 버리고 k = 1 값을 낸다.
  - 이 칸은 ln ID 보간이 무너지는 ID → 0 부근이므로, 정의 불능(fail-closed)이 물리적으로 맞다.
- card의 해당 문언:
  - spec '착수 실측' '판정 갈래 3 = 이미 구현'
  - '이 card에 없는 것' '집계 코드(이미 WB-1 `e6bb22bd`에 있음)'
  - '변경 0 -- 확인만'(봉인 블록 등)
  - '원래 취지와 다름' 5(계획 6 (1) 'base = red'가 성립하지 않음)
- 위 문언이 틀린 이유:
  - `e6bb22bd`가 고친 것은 봉인 1(`seal_node_conflict.py`)·SCC(`block_dc.py` `tolerance`)의 **소자 항 집계**뿐이다. 봉인 3 `seal_kcl.py:65-66`·봉인 8 `seal_kvl_branch.py:31`도 같은 꼴이다.
  - 그 항 하나하나를 만드는 **셀 결합 `table_at`**은 그대로다.
  - interface §5 J-a·J-b는 None을 필드(`dc_tol_v` tamper)나 `tol_v_table` stub으로 주입한다. 그래서 `table_at`을 거치지 않아 이 결함을 보지 못한다.
  - 계획 6 (1)은 "3 (a)~(c) 갈래마다 toy 하나(**None 원인 = 켜진 격자점 없는 셀**; base (a) = 값으로 통과 -- red; (a)·(b)는 집계 항 일부만 None인 꼴 포함 -- base = 정의된 항의 max·min으로 값 -- red)"이다. 이 원인으로 toy를 만들면 base는 `table_at`이 값을 내므로 **실제로 red**다. 계획 문언은 맞고, card가 계획과 다르다.
- 고칠 방법:
  1. 재작성 범위에 `lut/_helpers_loo.py` `table_at`을 넣는다. 결합 셀 가운데 None이 하나라도 있으면 None을 낸다(표 10행 집계 규칙, `tolerance.py:110-111` docstring과 `lut/CONTRACT.md` 4.0 문언도 함께 고친다).
  2. 갈래 toy를 계획대로 'LUT 안 켜진 격자점 없는 셀'로 만든다. 예: VDS = 0 열 ID = 0인 합성 LUT에서 조회 VDS를 첫 칸 안에 둔다. 그러면 (a)는 봉인 2 `seal_undefined`(base = 값, red)이고, (a) 노드 집계와 (b) SCC 일부 None(base = 값, red)도 같은 꼴이다. 기존 필드 주입 J-a~J-c는 회귀 고정으로 남겨도 된다.
  3. '원래 취지와 다름' 5를 지우거나 '필드 주입 toy만 base green'으로 고친다.
  4. 영향 실측을 착수 실측에 더한다(정적 계수: 첫 VDS 칸 조회가 나는 소자·회로 -- 실행은 판정 때). 결과가 바뀌는 점은 '알려진 fail-closed 손실'로 기록한다.
  - `table_at`이 표 10행 범위 밖이라고 보려면, 계획 표 10행에 '조회점 셀 결합은 집계 규칙 밖'과 그 물리 근거를 적는 계획 개정이 먼저다(원칙 17). 판정자 의견은 '범위 안'이다(위 물리 근거).
- tol_VDsat 표도 같은 `table_at`을 쓴다. (c)는 판정 자리가 아니고 '띠 미정' 기록이라 같은 수정으로 기록 쪽이 정의대로 된다.

### M-2 design S-7이 충족되지 않았는데 card가 design 결정을 정했다 (계획 순서와 다름)

- 계획 N6.40 '순서'(P:2652)는 "LM-1e 착수 조건 = 그 승인 → design(S-7) → spec/interface card"다. '다음 단계 표지'는 D40에 갈래·고칠 자리를 적고 "design 42 gap 표에 LM-1d·LM-1e 행을 더한다"이다.
- 실측:
  - D42 `grep -c "LM-1"` = 0이다.
  - D40 v1.16.22 :1250·:1465는 D7 거부와 갈래 유지만 적었다.
  - card 'design에 적을 항목' (i)~(vii)은 D40에 없다: 중점 파일 형식, 짝 슬라이스 판별, 적재 관문 G0~G7b와 새 사유 `lut_midpoints_slice_unmatched`, 옛 `L_source` 대조 삭제(원래 취지와 다름 1), D7 검사 자리, 위치 선언 배열 꼴, 그리고 다른 worktree의 옛 설정 꼴 읽기(원래 취지와 다름 4).
- 이 결정들은 계약(서명·사유 어휘·관문·fail-closed 범위)이라 design 몫이다(원칙 17, '새 엔진은 design 먼저').
- card는 착수 조건 3을 '미충족'으로 표지했고 절차에 'design 개정 → test'를 두어 스스로 막았다. 그래도 순서상 card가 design 결정을 먼저 정한 꼴이다.
- 고칠 방법:
  1. test·code 착수 전에 D40 §3.7-A 7·§3.10.8(과 lut CONTRACT 반영 자리)에 (i)~(vii)과 M-1의 `table_at`을 적는다.
  2. D42에 LM-1d·LM-1e 행을 더한다.
  3. design-validator와 design↔계획 gap을 돌린다.
  4. 그 뒤 card를 design과 대조해, 다른 곳만 고친다. 재판정은 그 gap만 본다.

## 3. minor

- **m1 D7 검사가 쓸 '중점 rows'의 출처가 정해지지 않았다**(interface §3).
  - `midpoint_l_bin_checks`는 `memo`(`LutMemo`)를 받는다. 그런데 `load_lut_set` 안에는 memo가 없다. 적재 중에 버릴 memo를 만들면 같은 값을 실행 memo에서 다시 계산하고, 판별식을 따로 쓰면 둘째 정의가 된다(graph 규칙 3).
  - 고칠 방법: '앵커 2개 bin 안에 그 슬라이스 중점 L이 두 앵커 사이에 있음'을 판별하는 함수 하나를 정한다. `midpoint_checks`의 bracket 판별과 D7이 함께 부르게 한다(design 항목 (v)에 적는다).
- **m2 `L_source` 대조를 지운 뒤 중점 L 관문이 빈다.**
  - 엔진은 중점 L이 승인 목록인지도, 제조 격자 값인지도(LM-1d 계획 1 '제조 격자 값') 더는 확인하지 않는다. G1b는 W만 격자를 본다.
  - 대체 근거(위치 선언 raw sha 고정 + 생성기 sha 직접 대조)는 받아들일 수 있다. 다만 L 격자 관문(`round(L/grid)` 정수, 기존 `lut_width_off_grid`와 같은 꼴)은 엔진에 둘 수 있으므로 더한다. 삭제 결정은 design에 적는다(M-2).
- **m3 U-87 보존 집합의 옛 단일 객체 꼴 읽기에 종료 조건이 없다**(원래 취지와 다름 4).
  - 다른 worktree의 살아 있는 칸을 지키는 이유는 맞다. 다만 다시 볼 시점(모든 worktree가 새 꼴로 옮긴 뒤 삭제)을 적거나 LA-1 재점검 입력으로 넘긴다.
- **m4 완료 조건 8 (ii)·A-5의 문언이 집계 규칙과 어긋난다.**
  - '조회 VDS가 든 격자 칸 두 원소 중 **정의된 것의** max'는 집계 규칙과 다르다. M-1 뒤에는 '모두 정의되어야 하고 그 max'로 고친다(하나라도 None이면 (i)에서 이미 실패).
- **m5 표 10행 범위 밖 '정의된 항만' 집계**(작성자 관찰 + 판정자 추가). 계획 판정 입력이며 card 결함이 아니다(아래 5).

## 4. 의문 판정

| # | 의문 | 판정 |
|---|---|---|
| (2) | 계획 6 (1) 'base = red'와 어긋남 → 계획 정정 필요한가 | **계획 정정 불필요, card를 고친다**(M-1). 계획 6 (1)은 None 원인 = '켜진 격자점 없는 셀'인 toy를 요구한다. 그 원인은 `table_at`을 거치므로 base에서 값이 나와 red다. `e6bb22bd`는 소자 항 집계만 고쳤다. 필드 주입 toy만 base green이다 |
| (3) | 새 사유 `lut_midpoints_slice_unmatched` | **받아들임**. 기존 어휘 49개(grep) 가운데 정의가 같은 것이 없다: `lut_device_undeclared` = manifest 장치가 spec 선언 밖(`provenance.py:215-216`), `lut_slice_missing` = 파일 없음, `lut_cap_width_unresolved` = cap 폭 판별 실패. 계획 3 '새 사유 0'은 판정 갈래 이름이고, 2 '새 이름 0'은 D7 사유다. 이 적재 관문 이름은 금지 대상이 아니다. design에 정의를 적는다(M-2) |
| (4) | D7 영향 정적 계수(fixture 5·test 7·조건부 3) | **근거 확인, 받아들임**(정적, 실행 확인 0) -- 아래 '(4) 재확인' |
| (5) | `dc_metrics` b_P·`icm_config`의 '정의된 항만' min·max | **표 10행 문언 범위('봉인 항목이 쓰는 셀과 그 집계') 밖, 원리('정의 항이 없으면 값을 내지 않음', O-242 기각안 D) 안** -- 계획 판정 입력이다. 근거는 아래 '(5) 판단 근거' |
| (6) | design S-7 미반영 → code 착수 전 design 개정이 필요한가 | **필요**(M-2). test 작성도 그 뒤다 |

**(4) 재확인.**

- 다섯 자리를 원 파일로 확인했다: `test_block_param_tables.py:98-105`(spec W_min 1 µm, `BinToy` + `bin_model_text`), `test_tolerance.py:587-590`(블록 하나·앵커 2개, 키 100·200 슬라이스, `TOY_SPEC` W_min 1.5 µm → `widths` = {200}이 거부), `layout/test_run.py:600-606`(실 LUT, 중점 인자 없음), `test_fingerprint.py:96-101`(`verify_midpoints=None`), `test_slope_unit_check.py:191-246`.
- `BIN_ANCHOR_BIN_LO` (0,0,0,1,1,3,3,4)·`_HI` (0,0,0,0,0,1,1,1)(`tests/lut/conftest.py:1387-1388`)로 보면, 앵커 2개 bin은 LO 행의 model.1·model.3뿐이다.
- 독립 정적 확인: `load_lut_set`을 부르면서 'midpoint'라는 말이 없는 test 파일 26개를 모두 봤다.
  - 이 파일들은 `toy_bins` 계열(앵커마다 bin 하나 -- `toy_bins.py:5`)이거나, `TOY_SPEC` `BinToy`(`widths` = {200} -- 앵커 5·3개 bin)이거나, 이미 목록에 있는 자리다.
  - `min_finger_w_m=` 대입은 6곳이고, 목록과 card의 '영향 없음' 행(`test_block_gain_bound.py:241` 앵커 3개)과 맞다.
- M-1을 고치면 `table_at` 변경으로 영향 test가 더 생길 수 있다. 첫 VDS 칸 조회를 하는 toy·실 LUT test가 대상이고, 다시 세어야 한다.

**(5) 판단 근거.**

- b_P(`dc_metrics.py:57-69`)는 `power_resolution_w`의 판정 분해능이다. 일부 None을 빼면 b_P가 작아진다. 즉 분해능이 실제보다 곱게 보여 fail-closed가 아니다.
- `icm_config._tol_v`(`:180-184`)는 정의된 값의 min이다. None을 빼면 min이 커질 수 있다.
- `search/cell_floor.py:59`의 None 셀 건너뜀도 같은 꼴이다.
- 권고: 표 10행 집계 규칙의 범위를 'tol 셀의 모든 min·max 집계'로 넓히거나, 예외마다 물리 근거를 적는 계획 개정을 한다. 입력은 LA-1 재점검 또는 다음 계획 개정이고, 이 card 범위 밖이다.

## 5. graph·fail-closed·상수·O-197 (항목 7)

- **graph 규칙**:
  - 새 graph 필드는 0이다.
  - `midpoints_sha256`은 `midpoint_sources`에서 계산하는 property다(저장 사본 0).
  - 지문·자료 id·표 캐시 키에 모든 중점 sha가 든다. K-4의 '다른 키 miss'는 입력 버전이 다르기 때문이라 graph 규칙 2에 맞다(과잉 무효화이지만 정의대로).
  - `bin_missing_external` 이름은 `_helpers_loo.py:89` 표 하나에서 읽는다.
  - 남은 것: m1(판별 정의 1곳), m3(옛 꼴 읽기).
- **fail-closed**:
  - G0~G7b는 모두 거부다. 짝 없는 파일을 버리지 않는다. manifest에 `generator_sha256`이 없으면 언제나 거부한다.
  - 다만 M-1(`table_at`의 None 제외)이 표 10행 범위 안의 fail-open 꼴이다.
- **상수 발명**: 0이다(기대 수 30은 확인 장치이고 코드·test에 박지 않음).
- **회로 이름**: 0이다(판정 측정 대상 지정만).
- **O-197**: `min_finger_w_m`·`manufacturing_grid_m`·'모델 bin' 역할 이름만 쓴다.
- **물리**:
  - o2(같은 bin 안 L 비단조 → tol 증가)는 정의대로라고 보고, 자르지 않는 것이 맞다.
  - A-4 '비기준 폭 앵커 2개 bin 행 새 값 ≥ 옛 값'은 `with_external`의 max 정의에서 나온다. 맞다.

## 6. 재지 않은 것(통과로 세지 않음)

- 엔진·test 실행은 0이다. D7 영향 수는 정적이다.
- 첫 VDS 칸 조회의 발생 빈도와 그로 인한 13회로 변화는 재지 않았다.
- 새 tol 값과 two_stage_ota 덤프는 재지 않았다.
- `e6bb22bd` 밖 WB-1 커밋의 집계 꼴은 봉인 1·3·8·SCC·`seal_region`만 읽었다.

## 재판정 (개정 2 `9234bddc`, 2026-11-06)

- 대상: `card/lm1e` `546849f2..9234bddc`(WB-1 머리 `f1dd8f52` 병합 위). 바뀐 파일은 spec·interface 둘뿐이고, worktree는 깨끗하다.
- 기준: 계획 v6.38.27 N6.40 LM-1e 1~6·3b(P:2651), N3.6 표 10행 '규칙의 범위 = 모든 tol 셀 min·max 집계'(P:663), design 40 v1.16.24 §3.7-A 7 'LM-1e 적재 design'(:1251-1259), D42 `D-LM1d`·`D-LM1e`(:348-349).
- 방법: 앞과 같다(읽기·grep만, 실행 0).

### 결론: **Major 1(M-3), minor 2. card 밖 착수 조건 1(C-1).**

### (1) M-1 해소 -- **해소**

- **규칙**: spec 3b (i)과 interface §5에 '결합 셀이 모두 정의되면 max, 하나라도 None이면 None'이 들어갔다. docstring·CONTRACT 4.0 문언도 함께 고친다.
- **호출자 전수**: 판정자가 엔진 비test 코드에서 `table_at(`와 tol 표 `.at(`를 grep해 맞췄다. 결과는 card 표와 같다.
  - `table_at`을 쓰는 표: tol_V·tol_VDsat·잡음 tol(`noise_tolerance.py:39`).
  - tol 표 `.at(` 호출 자리: `seal_tolerances.py:32`, `block_dc.py:373`, `sat_threshold.py:56`, `slice_density.py:29`, `cell_floor.py:69`, `noise_devices.py:33-34`, 그리고 따로 구현된 `device_sigma.py:27`(아래 M-3).
- **갈래 toy**: R LUT는 `tests/sizing/conftest.py:155-169·:193-203`의 `r4_arrays(off_cols=)`·`write_r4_lut(off_cols={kind: n})`를 쓴다. 이 함수는 실제로 있고, VDS index 0..n−1의 ID·GM·GDS를 0으로 둔다. 갈래 toy는 이 LUT를 거쳐 `table_at`에 닿는다.
  - A-0, J-a(`dc_op` vds만 바꾸고 `dc_tol_v`는 주입 0 → `dc_tolerances`), J-b(통과 spy, 값 주입 0), J-c, P-1·P-2 모두 base에서 값이 나와 red다.
  - 전제 R-0(셀 0 None, 셀 1·2 값)을 먼저 단언하고, 안 서면 멈춘다. 필드 주입 toy는 철회했다.

### (2) M-2 -- **(i)~(vii)은 해소, 남은 차이 둘**

card §1~§4는 D40 (i)~(vii)과 같다. 확인한 항목:

- 형식, 짝 판별(meta `device`·폭 키)
- 관문 순서와 사유(G1c `lut_midpoints_l_off_grid`는 D40 (iii) '기존 어휘에 같은 정의 없으면 새 이름 하나' 안. 판정 꼴 = 폭 관문과 같은 `round(L/grid)` 정수라서 앞 판정 r2의 float 비교 문제가 없다)
- `L_source` 대체, D7 자리와 `midpoint_bracket` 순수 함수
- 배열 꼴, 옛 꼴 읽기 종료 조건

남은 차이 둘:

- **(가) 탐색 전도 하한**: 계획 3b (ii)(P:2651)와 D40 셀 결합 규칙(:1259)은 `_conduction_floor`를 이 card 범위에 둔다. card는 범위 밖으로 뺐다(아래 C-1).
- **(나) 잡음 tol**: D40은 'tol_V·tol_VDsat 표가 같은 함수'만 적고 `TolNoiseTable.at`(같은 `table_at`)을 적지 않았다. card는 원인 분류 '잡음 tol'을 더하고 '원래 취지와 다름' 5로 표지했다.
- 둘 다 card가 아니라 design·계획 문언을 고칠 일이다. card에는 정확히 표지되어 있다.

### (3) m1~m4

| 지적 | 반영 | 판정 |
|---|---|---|
| m1 | `midpoint_bracket(l_grid, l_bins, L_m, grid_m, rule)`을 `_helpers_bins`의 순수 함수로 두고 `midpoint_checks`·D7이 같이 부른다. 적재 중 memo 0, 레지스트리 행, 규칙 A(사용 파일 2) | 반영 |
| m2 | G1c L 격자 관문, T-9 toy, 완료 3·A-3 승인 목록 대조(계획 b4) | 반영 |
| m3 | 옛 꼴 읽기 종료 조건(코드 주석 + LA-1 재점검) | 반영 |
| m4 | 완료 8 (ii)·A-5 '모두 정의되고 그 max' | 반영 |

### (4) 3b (ii) 정적 확인 `dc_coord ⊆ dc_op` -- **판정자 확인: 참(같은 집합)**

- `sizing/block_dc.py:822` `_outputs`는 `for m, coord in c.coord.items()`로 소자마다 `ops[m] = DeviceOp(...)`를 쓴다(`:830`·`:836`, 두 갈래 모두).
- `c.coord`는 `device.dc_coord` 열이다(`_helpers_dc_solve.py:75`). 따라서 `dc_op` 키 = `dc_coord` 키다.
- 봉인 2(`seal_vgs_match.py:24-26`)는 `dc_op` MOS 전부를 판정한다. 그래서 봉인점에서는 `dc_coord` MOS의 `dc_tol_v`가 모두 정의되어 있다.
  - ICMR `_tol_v`는 봉인점 값이 바뀌지 않는다.
  - b_P의 `dc_gm` 키는 `seal_tolerances.py:30-35`가 `dc_op` 소자마다 쓴다. b_P도 봉인점 값이 바뀌지 않는다.

### (5) 탐색 전도 하한 범위 밖 표지 -- **표지는 적혔다. 단 계획·design과 다르다(C-1)**

- spec 3b (ii)·'이 card에 없는 것'·관찰·'원래 취지와 다름' 6과 interface 머리·§5에 '범위 밖(LA-1 O-207 묶음 삭제 대상, `off_rules_audit.md`, 사용자 결정 대기)'과 toy 0이 적혀 있다.
- **C-1(card 밖 착수 조건)**:
  - 계획 v6.38.27 3b (ii)와 D40 :1259는 아직 `_conduction_floor`를 이 card 범위에 둔다.
  - 뺀다는 근거는 감사 권고(`off_rules_audit.md`:30 'LM-1e 3b (ii)에서 `_conduction_floor`를 뺀다')와 오케스트레이터 지시뿐이다. `la1_auto_decisions.md`에는 기록이 없다('전도 하한'·`off_rules_audit` grep 0).
  - 원칙 17('계획과 다르면 계획부터')에 따라 test·code 착수 전에 할 일: 위임 결정 기록(A-번호), 계획 3b (ii)·N3.6 표 10행 (ii)·D40 :1259에서 전도 하한 몫 정정, LA-1 O-207 묶음 완료 8에 `_conduction_floor` 추가(감사 :31).
  - 물리상 뺀 결과도 받아들일 수 있다. 전도 하한은 탐색 상자 쪽이라 판정이 바뀌지 않고, 지금 `if not tol: continue` 그대로다. 존폐 자체가 O-203 위반 의심으로 LA-1 차단 묶음에 들어가 있다.

### (6) 작성자 남은 의문

- **(1) 잡음 tol None 경로 -- fail-closed(맞음).**
  - None이 퍼지는 길: `noise_devices.py:33-34` → `noise_sources._tolerance` → NaN(`noise_sources.py:28-29`·`:41`) → `noise_integral.py:151`에서 NaN이 있으면 `lut_i = None` → `lut_v = None`.
  - 그 결과: `known = False`(`:231`), `resolution = None`(`:246`).
  - 판정 쪽 처리: `search/ss_constraints.py:79-81`이 resolution None이면 행 없이 `unmeasured`(`resolution_undefined`)로 둔다. 그래서 `eps_sweep`·`find_front`가 그 점을 `front`가 아니라 `unmeasured_front`로 나눈다.
  - 값을 만족으로 세지 않으므로 fail-closed다. 같은 함수 하나로 바꾸는 card 안(사본 0)이 맞고, 원인 분류 '잡음 tol' 추가도 맞다. D40 문언 정정은 위 M-2 (나).
- **(2) `TolMismatchTable.at` -- 범위 안이고, 이 card에 넣는다 → M-3.**
- **(3) J-b·J-c 성립 조건 -- 조건부로 맞다.**
  - J-b: `block_dc`의 tolerance 호출 자리(`:312`·`:560`·`:791`)는 반복 중 iterate 값으로 `tol_cell`을 부른다. `transient`(`:209-215`)는 `lut_curve_undefined`·축 이탈만 반복 중 이탈로 보고, `tolerance()`가 내는 `SealViolationError(tol_v_undefined)`(`:509-510`)는 보지 않는다. 그래서 iterate가 `vds_floor`(R LUT pmos off_cols 1이면 0.25 V) 아래 첫 칸에 들면 새 None이 실패로 닿는다(계획 3b (i) '반복 중 iterate' 손실). 통과 spy로 그런 호출이 있었는지 단언하는 꼴은 값 주입이 없어서 맞다. θ를 그렇게 고를 수 없으면 멈추고 보고한다(card 그대로).
  - J-c: `sat_threshold`는 `vdsat_v`가 정의된 점에서만 tol 조회에 닿는다. 전제 단언(아니면 멈춤)이 card에 있다.
- **영향 test 정적 계수(함수 11 + 조건부 3)**
  - D7 7(+3)은 앞 판정에서 독립 확인한 값 그대로다.
  - `table_at` oracle 4 함수 자리(`test_tolerance.py:385·:477·:627`, `test_vdsat_tolerance.py:205`)는 interface에 줄 단위로 적혀 있고, 옛 oracle 식을 그대로 다시 쓴 꼴이라 맞다.
  - 목록 밖 변화는 '멈추고 원인별 기록' 규칙으로 닫혀 있다. M-3을 반영하면 mismatch tol oracle test(`tests/lut/test_mismatch_tolerance.py` 류)를 다시 센다.

### M-3 `TolMismatchTable.at`이 표 10행 규칙 범위 안인데 card가 뺐다 (계획과 다름·fail-open 꼴·같은 정의의 둘째 구현)

- 사실: `lut/mismatch_tolerance.py:34-47` `TolMismatchTable.at`은 조회점 (L, VDS)를 덮는 셀(앵커 lo·hi × VDS 칸 k·k+1)을 합칠 때 None을 뺀 max를 낸다(`:45-46` — `table_at`과 같은 결합을 따로 구현한 둘째 정의).
- 계획 표 10행 '규칙의 범위 = **모든 tol 셀 min·max 집계** -- 범위를 판정 자리로 좁힐 물리 근거가 없다', (i) '**tol 표 조회**가 조회점을 덮는 셀을 max로 합칠 때 None이 하나라도 있으면 None'. mismatch tol 표 조회는 이 정의에 그대로 든다.
- 계획 3b가 `table_at`만 적은 것은 3b 자신이 '재작성 범위 사실은 계획 작성 때 실측, 착수 때 base에서 다시'라고 한 목록이다. 규칙 정의 자리는 표 10행이다.
- 소비자 `metrics/device_sigma.py:27-30`은 tol None이면 `extra = None`(fail-closed)으로 받는다. 그래서 규칙을 적용해도 새 None은 기존 갈래로 간다.
- 그대로 두면 정의된 셀만으로 mismatch tol이 나온다(분해능이 실제보다 곱게 보이는 쪽). 그리고 같은 결합 규칙이 두 꼴로 남는다(graph 규칙 3).
- **고칠 방법**(card +0, 작은 변경):
  1. 재작성 범위에 `lut/mismatch_tolerance.py` `TolMismatchTable.at`을 넣어 같은 규칙으로 바꾼다. 가능하면 `table_at`을 재사용해 둘째 구현을 지운다. 셀의 값 칸이 `params[j][1]`이라 `field` 접근을 맞추는 꼴은 card가 정한다.
  2. 호출자 표에 `device_sigma.py:27`을 넣는다.
  3. toy 하나를 더한다(off_cols 꼴 mismatch toy, 첫 VDS 칸 조회 → None, base = 값 → red).
  4. 원인 분류에 'mismatch tol'을 더한다.
  5. '관찰'·'이 card에 없는 것'의 `TolMismatchTable.at` 문언을 지운다.
  6. D40 셀 결합 규칙 문언에 잡음·mismatch 표를 함께 적는다(M-2 (나)와 같이).

### 남은 minor

- **r1 J-a 기대가 조건부로 열려 있다.** '실패 행이 있으면 그 사실 기록'이라 그 경우 test가 무엇을 단언하는지 정해지지 않는다. `dc_op` vds만 바꾼 스냅샷은 다른 봉인에서 실패 행을 낼 수 있다. 고칠 방법: 전제로 단언(M3가 닿는 봉인 1·3·2 행에 실패 행 0 -- 안 서면 멈추고 보고)으로 바꾸고, '기록하고 통과' 꼴을 없앤다.
- **r2 A-12 계수 스크립트**: '판정자 스크립트, 엔진 배선 0'은 계획 3b (i) 착수 실측(LA-1 차단 항목)에 필요해서 O-229 4 예외 안이다. 판정 기록에 스크립트 경로와 돌린 범위를 남기라고 한 줄 더한다.

### 재지 않은 것(통과로 세지 않음)

실행 0이다. 첫 VDS 칸 조회 빈도, 봉인점 새 None 수(A-12), `table_at`·mismatch 변경의 목록 밖 영향 test는 재지 않았다.

## 재판정 2 (개정 3 `ddd73c62`, 부모 `9234bddc`, 2026-11-06)

- 대상: `card/lm1e` `9234bddc..ddd73c62`(spec 89줄·interface 37줄 변경, 두 파일뿐). worktree는 깨끗하다.
- 기준: 계획 v6.38.27(같은 worktree), 위임 A-145(`la1_auto_decisions.md`:151), 사용자 결정 O-249(`user_decisions.md`:1230). v6.38.28은 작성 중이라 판정 대상에서 뺐다.
- 방법: 읽기·grep만 했다(실행 0, 수정·커밋 0).

### 결론: **Major 0.** minor 1(s1). M-3 해소, C-1 근거 기록·착수 조건 7로 닫힘, r1·r2 반영.

### (1) M-3 해소 -- **해소**

- 결합 구현이 하나가 된다.
  - `TolMismatchTable.at`(`lut/mismatch_tolerance.py:34-47`)은 param 검사(`ValueError`)를 한 뒤 `table_at`을 부르게 바뀐다. 자기 안의 `l_position`·`check_axes`·칸·max 줄은 지운다(spec 재작성 범위 :151).
  - `table_at`이 읽는 표 속성은 `L_anchors`·`l_bins`·`vds_grid`·`grid_m`·`rule`·`cells`이고, `TolMismatchTable`은 이 속성을 모두 가진다(`:25-32`).
  - VDS 칸 식도 같다. `np.searchsorted(side="right") − 1`과 `bisect_right − 1`은 정렬 배열에서 같은 값이고, 둘 다 `len − 2`에서 자른다. 축 검사와 context도 같은 꼴이다.
  - 따라서 바뀌는 동작은 None 결합 규칙 하나뿐이다.
- 서명 `table_at(table, value_of, ...)`는 최소 꼴이고 graph 규칙 3에 맞는다. 대안 비교:
  - (가) 문자열과 함수를 둘 다 받기: 한 함수에 입력 꼴 둘과 분기가 생긴다. ⚠ 같은 일의 두 표현이라 단순성에 어긋난다.
  - (나) mismatch 셀에 변수별 속성 추가: 셀 꼴이 `params=((변수, 값), ...)`(`TolMismatchCell`)라 동적 속성을 만들거나 변수별로 표를 쪼개야 한다. 표 구성·U-87 칸 꼴이 바뀌어 범위가 커진다.
  - (다) 셀 → 값 함수(card 안): 호출자 넷이 각각 getter를 넘기고, 결합 규칙은 한 곳에 남는다. 값 사본·보관은 0이다(읽는 방법만 넘김).
  - (다)가 가장 작고, 원칙(정의 1곳·새 저장 자리 0)과 맞는다.
- 비공개 helper라 test 직접 호출은 0이다. tests의 `table_at` grep은 이름 `test_tol_v_cell_is_table_at` 하나이고, 그 test는 공개 `at` 경유라 동작이 바뀌지 않는다.
- G-8 기준선 `g8_baseline.json`:413-418(`tol_mismatch_table` memo lookup 꼴)은 `at` 변경과 무관하다.

### (2) toy M 계약과 적재 거부 여부 -- **계약 충분, 거부 없음**

- interface §5 toy M이 소스 없이 쓸 수 있을 만큼 정해져 있다.
  - 쓰는 것: `tests/lut/conftest.py` `MismatchToy(root, dvgs)`(:2064-2091), 격자(`TOY_L`·`TOY_VGS`·`TOY_VDS`·`TOY_VS` :78-81, `TOY_SHAPE` :2001, `toy_grid_mesh` :2005).
  - 입력: `vth0` = C·v²에서 VDS index 0 열을 NaN으로, `voff` = 상수.
  - 손 셀 값: C·0.25/4. 기존 `test_nan_points_skipped`(:38-44)와 같은 oracle이다.
  - 셀 읽기는 `dict(cells[i][b].params)`로 한다. `TOY_VDS`가 2점이라 결합 셀이 늘 셀 0·1인 점도 적혀 있다.
- 손 식이 맞는지 판정자가 확인했다.
  - VGS 3점의 내부점 LOO = c·h²(h = 0.5), Richardson ÷ 4.
  - toy 지도는 `ToyBuild` 기본(앵커마다 bin 하나)이라 L 방향 LOO가 없다.
  - VDS 2점이라 VDS 방향 LOO도 없다.
  - 그래서 셀 1 = C·0.25/4, 셀 0 = None(그 VDS의 모든 점이 NaN)이다.
- 적재가 거부하지 않는다: `lut/mismatch_set.py`의 거부 사유(:33·:60·:62·:65·:71·:78·:81)는 meta·cap·조건·축·열 없음·모양뿐이고 비유한값 검사는 0이다. 기존 test도 변수 전부 NaN(`toxe`)을 적재한다(:41).
- 거부하면 멈추는 조건도 M-0 전제에 '적재 거부 포함'으로 적혀 있다.

### (3) `offset_analysis.py:117`의 `sigma_of[lab][1]` -- **tol 칸 맞음**

- `sigma_of = {label: (s, t) for label, s, t in sigmas}`(:65)이고, `sigmas` 행은 `device_sigma`의 `(label, sigma_v, tol_rel)`(`device_sigma.py:32`)이다. 그래서 `[1]` = tol이다.
- None이면 `_resolution`이 `(None, None)`을 낸다(:117-118). 이것이 resolution None → `ss_constraints.py:79-81` unmeasured로 가므로 fail-closed다.
- `device_sigma`는 기여 0인 변수(`part == 0`)의 tol을 보지 않는다(:25-26). 그 항이 정확히 0이라 집계 항이 아니므로 맞다.

### (4) C-1·r1·r2

- **C-1**:
  - 근거가 O-249 Q2 위임(A-145 (2) -- 'LA-1 O-207 묶음 완료 8에 `git grep` 0', 계획 3b (ii)·표 10행 (ii)·D40 :1259 정정)으로 기록되어 있다. 앞 판정의 '기록 없음'이 해소됐다.
  - spec 착수 조건 7(계획 v6.38.28 병합 -- 전도 하한 정정, 표 10행 (i)에 잡음·mismatch 조회 명시, D40 셀 결합 문언)이 test·code 전에 걸려 있다. 개정 결과가 card와 다르면 card를 고친다는 문언도 있다. → 닫힘.
- **r1**: J-a0 전제(M3가 닿는 봉인 2·1·3 행 실패 0, 안 서면 멈춤, '기록하고 통과' 꼴 삭제)가 interface §5에 있다. → 반영.
- **r2**: A-12에 '계수 스크립트 경로와 돌린 범위(회로·조회 자리·base/head sha)를 판정 기록에'가 있다. 원인 분류에 '잡음 tol'·'mismatch tol'을 더했고, 두 None 경로의 소스 확인 줄이 있다. → 반영.

### (5) mismatch 쪽 영향 test 계수(0, 새 toy 1) -- **맞음**

- 판정자가 tests에서 `tol_mismatch`·`TolMismatchTable`·`mismatch_tolerance`를 grep했다. 결과:
  - `test_mismatch_tolerance.py` 3 함수: 정의된 변수는 두 셀 모두 정의, 전부 NaN 변수는 두 셀 모두 None이라 옛 결합 = 새 결합이다.
  - `test_device_sigma.py` 6 함수: DVGS가 상수(:38)라 모든 셀이 정의(0)다.
  - `test_offset_analysis.py`: tol을 직접 넣는다.
  - `test_derived_fns.py:200`·`test_lut_memo.py:29`: 표 이름 목록만 본다.
  - `g8_baseline.json`: lookup 꼴만 본다.
- 기대가 바뀌는 test는 0이다. 새 toy는 M(M-0 전제 + M-1) 하나다.

### (6) 물리 정합·graph·fail-closed·범위

- **물리**: mismatch 셀 None의 원인은 그 VDS의 DVGS 점이 모두 정의 없음인 것이다. 그 결합에서 값을 내지 않는 것은 표 10행 원리(정의 항이 없으면 값을 내지 않음)대로다.
- **graph**: 결합 정의 1곳(`table_at` -- 넷이 부름), 둘째 구현 삭제, 새 칸·cache·사본 0이다.
- **fail-closed**: 잡음 경로는 앞 재판정에서 확인했다(unmeasured). mismatch 경로는 위 (3)이다.
- **범위**:
  - 엔진 변경은 card 재작성 범위 안이다(`mismatch_tolerance.py`·`_helpers_loo.py` 서명·CONTRACT 10.3 문언). 위치 선언·topology 변경은 0이다.
  - 전도 하한은 범위 밖이고, 위임 기록과 착수 조건 7로 닫혔다.
- 기준 약화 0, 엔진 변경 누출 0.

### minor

- **s1 O-229 test 범위 문언 불일치**: interface:7은 범위에 `sizing/test_s2_values.py`를 더했다. spec:21(O-229 줄)에는 없고, 더한 이유도 적혀 있지 않다. 고칠 방법: 두 문서를 같게 하고 근거 한 줄(어떤 변경이 그 test에 닿는지)을 적는다. 범위를 넓히는 쪽이라 기준 약화는 아니다. 왕복 없이 test 작성 전에 맞춘다.

### 재지 않은 것(통과로 세지 않음)

실행 0이다. toy M의 실제 셀 값, mismatch 조회의 실 LUT 새 None 수(A-12 'mismatch tol' 원인), 계획 v6.38.28 문언은 재지 않았다.
