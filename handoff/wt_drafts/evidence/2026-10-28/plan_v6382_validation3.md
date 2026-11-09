# 계획 v6.38.2 독립 검증 3 (2026-10-28) -- 셋째 커밋 `1e4ae472` 중심

- 피검: `wt/plan-v6382` 커밋 `1e4ae472`(셋째, 부모 `a8a44ace`), 기준 `1fefcab1`. 바뀐 파일 8개: gain-budget plan·history, oracle-portability plan·history(v0.6.19), offset-strategy plan·history(v0.7.3.1), graph-consumption plan·history(v0.14.2).
- 검증자: 독립 검증 3. 작성자도 아니고 검증 1·2 담당도 아니다. 작성자 보고·커밋 메시지는 증거로 쓰지 않았다. 아래 근거는 모두 원문·코드(`wt/integ-it12` `ebad06c1`)·LUT·PDK 모델 파일·아카이브 zip을 직접 읽거나 잰 것이다. ngspice-46은 scratchpad에서 새로 돌렸다(§5 재현).
- 파일 수정: 이 문서 하나만 썼다. git은 `set -e` + `git -C` 읽기 명령만 썼다. 끝난 뒤 `wt/plan-v6382` HEAD `1e4ae472`·status 빈 출력, `wt/integ-it12` HEAD `ebad06c1`·status 빈 출력을 확인했다.
- 줄 번호: 계획은 `1e4ae472` 판이다. DEC-78 :277, DEC-91 :290, DEC-104 :303, DEC-105 :304, 표 :658, LY2 :999, LA-1 범위 15 :1849, LA-1 착수 조건 :1891, 후속 정정 표 새 행 :1916, X-LA8 :1929, N6.17 :1974·:1988, SF-1 범위 8 :2175, SB-1 :2214-2227, WB-1 :2229-2246, CPG-1 :2261-2274, U-125~U-130 :2453-2458. history :1479-1481.

## 0. 요약

| 심각도 | 수 | 항목 |
|---|---|---|
| 높음 | 1 | V3-1: bin 경계 규칙이 ngspice 호환 모드에 따라 뒤집힌다. CPG-1 bench(`ngbehavior=hsa`)는 LUT 생성·엔진 규칙과 반대 bin을 고른다. 그래서 U-130의 조건 '읽는 슬라이스의 bin = SPICE bin'이 경계 폭에서 보장되지 않는다. w_hi = 5 µm 규칙은 w_f를 그 경계에 몰리게 한다 |
| 중간 | 2 | V3-2: 손가락 필드의 소비자 목록에서 기존 손가락·폭 생산자 4곳이 빠졌다(mismatch bin, 접합 기하, 옛 oracle 어댑터). 격자 반올림 뒤 총 폭(m·w_f ≠ W)의 정본도 정하지 않았다. V3-3: CPG-1 bench가 EO-1 oracle과 다르고(hsa, 확산 기하 없음), 두 비교 쪽의 기하 규칙도 다르다 |
| 경미 | 7 | V3-4~V3-10 |

검증 2 N-1~N-10 처리 결과: 적합 6(N-2 경로, N-4, N-5, N-6, N-8, N-9), 부분 적합 3(N-1 → V3-1·V3-2·V3-4, N-3 → V3-9, N-7 → V3-6), 판단 1(N-10 → V3-5. card 식별은 작성자가 맞고, 시점 문언은 고쳐야 한다).

**N-1 fail-closed 잔여**: 새 손가락 규칙(m = ⌈W/w_hi⌉, w_hi = 5 µm, 격자 0.005 µm, W_min 0.42 µm, 슬라이스 없으면 m 증가)으로 세면 **nmos 0/74, pmos 0/68**(PKG §6(b) 9회로 출발점 `wt/_step2_gaps/out_survey/*.json`)이다. 아카이브 판정 넷리스트 총 폭(w·m) 기준으로도 **nmos 0/67, pmos 0/47**이다. 둘째 커밋 규칙(총 폭 bin)은 33/74·49/68(출발점), 36/67·28/47(넷리스트)이었다. 'm 증가' 분기는 sky130에서 한 번도 발동하지 않는다(w_f ≤ 5 µm bin에는 모두 슬라이스가 있다). 단, 거짓 거부는 사라졌지만 bin 일치는 아직 보장되지 않는다(V3-1).

**승인 상정 의견: 아직 불가.** V3-1은 U-130의 근거 (i)(P0, 'SPICE와 같은 bin')와 CPG-1 판정을 직접 흔든다. 고치는 방법은 '경계 규칙 = 시뮬레이터 판 + 호환 모드 선언, LUT 생성·EO-1·CPG-1 bench가 같은 선언을 읽음'이다. 이 고침은 같은 판에서 할 수 있다. 다만 CPG-1 bench 모드를 바꾸면 기준선 H0r 셈을 다시 재야 할 수 있어 사용자 확인이 하나 늘 수 있다. V3-2는 같은 판에서 문언으로 고칠 수 있다.

## 1. N-1 손가락 규칙 검사 (a)~(f)

### (a) fail-closed 잔여 수 -- 0 (위 요약)

| 자료 | kind | 소자 | 새 규칙 fail | m > 1 | 둘째 커밋(총 폭) fail |
|---|---|---|---|---|---|
| PKG §6(b) 출발점(`out_survey`) | nmos | 74 | 0 | 34 | 33 |
| | pmos | 68 | 0 | 51 | 49 |
| 아카이브 판정 넷리스트(w·m) | nmos | 67 | 0 | 36 | 36 |
| | pmos | 47 | 0 | 29 | 28 |

- 출발점 W < W_min인 소자는 0이다. W_min에 붙은 소자 32개(nmos 18·pmos 14)는 격자 반올림 뒤 0.42 µm로 bin 안에 든다. D1 정정이 전제다.
- 계획 문언 확인: 사실 (v)(:2233) 'nmos 34/74·pmos 51/68'과 U-130 (iii) '85/142 가운데 7 µm 초과 모두'를 잰 값은 7 µm 초과 82개(33 + 49)다. 문언과 어긋나지 않는다.

### (b) 격자 반올림 뒤 슬라이스 bin = SPICE bin인가 -- 보장되지 않음 → **V3-1 (높음)**

ngspice-46(`C:/ngspice/Spice64/bin/ngspice_con.exe`)으로 같은 sky130 tt 넷리스트를 두 설정에서 돌리고 `showmod … : wmin wmax lmin lmax`로 실제 bin을 읽었다.

| 인스턴스 | 기본 모드(.spiceinit 없음 -- LUT 생성기·엔진 `tools/spice_oracle`와 같음) | `set ngbehavior=hsa`(아카이브 판정 도구 `_cmp_pilot/H/judge/spice_judge_base.py` `SPICEINIT`) |
|---|---|---|
| nfet w = 5u | W bin [3, 5] (아래) | **[5, 7] (위)** |
| nfet w = 7u | [5, 7] | **[7, 100]** |
| nfet w = 0.42u | [0.39, 0.42] | **[0.42, 0.52]** |
| pfet w = 0.42u | [0.42, 0.55] | [0.42, 0.55] |
| nfet/pfet l = 0.5u | L bin [0.25, 0.5] | **[0.5, 1]** |
| l = 1u · 2u · 0.18u | [0.5, 1] · [1, 2] · [0.15, 0.18] | **[1, 2] · [2, 4] · [0.18, 0.25]** |
| w = 100u | -- | "could not find a valid modelname" |

- 결론: 경계값의 소속은 시뮬레이터 판이 아니라 **호환 모드**가 정한다. 기본 모드에서는 아래 bin, hsa에서는 위 bin이다. as-built 규칙(`E/lut/_helpers_bins.py`, lut CONTRACT 4.0.1 '아래 bin 우선')과 LUT 슬라이스(생성기 `wt/_drafts/engine/lut_slices/sky130_dc_width_slices.py`, .spiceinit 없음)는 기본 모드와 맞는다. 반면 CPG-1 bench로 지정한 아카이브 판정 도구는 hsa다.
- 손가락 규칙이 경계를 만든다. w_hi = 5 µm 자체가 bin 경계이고, m = ⌈W/5⌉이면 W/m ∈ (5(m−1)/m, 5]이다. 격자 반올림 때문에 m이 큰 소자일수록 w_f = 5.000 µm에 몰린다(몰리는 비율 ≈ 0.0005·m).
  - 출발점 실측: w_f가 공유 경계에 놓인 소자는 nmos 29/74(5.000 µm 11개, W_min 0.42 µm 18개 -- nfet 0.42는 [0.39, 0.42]/[0.42, 0.52] 공유 경계), pmos 38/68(모두 5.000 µm)이다. **그 전부에서 기본 모드와 hsa의 bin이 다르다.**
  - 판정 넷리스트 실측: nmos 7/67, pmos 2/47.
  - w_hi = 7로 바꿔도 7.000 µm에 몰린다(nmos 21·pmos 16). 그리고 hsa에서 7 µm는 슬라이스 없는 [7, 100]이다.
- L도 같은 문제다. 아카이브 판정 넷리스트 114소자 가운데 L이 bin 경계(0.18·0.25·0.5·1·2·4·8·20 µm)인 소자가 40개다. 예: `two_stage_ota.H0r` XM5·XM7 `l=20u`는 LUT에서 [8, 20] 값을, hsa SPICE에서 [20, 100] 모델을 쓴다.
- 계획 문언과의 관계:
  - DEC-105 (2)(:304)의 조건 '읽는 슬라이스의 bin = SPICE가 그 w_f로 고르는 bin'은 시뮬레이터 모드를 정하지 않아 정의가 닫히지 않았다.
  - D1 정정(:2237 WB-1 범위 0, '격자 정수 비교')은 아래 bin 규칙을 엔진 안에 고정하고 그 근거 선언을 가리키지 않는다.
  - oracle-portability OP-7(:510, D-4 승인)은 경계 규칙 정본을 'LUT 생성 실행에 묶은 선언(모델 파일 sha256 + 시뮬레이터 판)'으로 옮긴다고 한다. **판만으로는 모자란다**(모드가 규칙을 뒤집는다). WB-1 D1은 OP-7을 인용하지 않아, 경계 규칙을 정하는 자리가 둘이 된다(계획 간 충돌).
- 영향: U-130 근거 (i)(P0)가 경계 소자에서 성립하지 않는다. CPG-1(hsa bench)에서 경계 소자의 엔진 예측(아래 bin 슬라이스)과 SPICE(위 bin)가 갈려 모델 오차가 판정 결과에 섞인다. 기준선 H0r 판정도 같은 bench였으므로 비교의 공정성은 유지된다. 그러나 'W-bin 정정으로 SPICE와 맞춘다'는 이 card의 목적은 그 bench에서 측정할 수 없다.
- 수정안(권고):
  1. 경계 규칙의 정본 = '시뮬레이터 판 + 호환 모드(.spiceinit 내용 포함) + 모델 파일 sha256' 선언 하나(OP-7 선언 키 확장)로 한다. LUT 생성·엔진 bin 판정(D1)·EO-1 oracle·CPG-1 bench가 모두 그 선언을 READS한다. D1은 '격자 정수 비교 + 선언된 경계 방향'으로 쓴다.
  2. CPG-1 bench의 호환 모드를 LUT 생성 모드와 같게 둔다. 아카이브 도구의 hsa는 측정 정의가 아니라 실행 설정이므로 빼는 것이 P0에 맞다. 기준선 H0r를 같은 모드로 다시 재는 것은 O-164 기준선 수치를 바꿀 수 있어 새 U 행(사용자 확인)으로 올린다. 대안은 hsa 유지 + 경계 소자 수를 판정 기록에 함께 적는 것이다(P0 미충족 표지).
  3. U-130 근거 (i)에 '같은 경계 선언 아래에서'를 붙이고, WB-1 완료 조건에 경계 w_f·경계 L toy(선언 방향대로 bin, oracle 모드와 일치)를 추가한다.

### (c) w_hi가 상수가 아닌 LUT/PDK 유도인가 -- 상수 발명은 아니다. 다만 조건에서 나온 값이 아니다 → V3-4 (경미)

- `w_ref_m` = 5e-6은 LUT 선언(lut CONTRACT r6 :33·:161 '`w_ref_m` = 5e-06 기록')이다. 그것을 품는 bin의 위 끝 = 5 µm(PDK `.model` wmin/wmax, 아래 bin 규칙)이므로 새 상수는 아니다.
- 그러나 조건 '읽는 슬라이스 bin = SPICE bin'만으로는 m이 하나로 정해지지 않는다. 조건을 만족하는 가장 작은 m이면 ⌈W/7⌉(아래 bin 규칙)이다. 왜 '기준 폭 슬라이스의 bin'인지(예: 용량·잡음 열을 기준 폭 표에서 읽으므로 손가락 기하를 기준 폭에 가깝게 둔다)를 계획이 적지 않았다. 그 선택이 V3-1의 경계 몰림을 만든다.
- 수정안: 선택 근거 한 줄을 적는다(기준 폭 용량 표와 손가락 기하의 일관). 또는 '경계 밖 w_f' 조건을 함께 둔다(V3-1 2안을 택하면 불필요).

### (d) graph 필드 writer 하나·소비자 ≥ 1·둘째 생산자 없음 -- writer는 맞다. 소비자·옛 생산자 목록이 모자란다 → **V3-2 (중간)**

- 계획(:304, WB-1 범위 2a :2240)에서 writer = 커널 W 계산 블록이고, 소비자 = LUT 슬라이스 선택(같은 블록 안 고정점)과 EO-1 넷리스트다. 레이아웃 뒤에는 같은 선택 함수를 쓴다. 이 부분은 맞다.
- as-built에서 손가락 수·인스턴스 폭을 따로 만드는 자리를 grep으로 찾았다. 계획은 eng2spice만 대체 대상으로 적었다.
  1. `E/metrics/device_sigma.py:17-31` `_sigma`: W > 모델 최대 bin 폭이면 n = ceil(W / w_top)(w_top = 100 µm)으로 나눠 mismatch slope bin을 고르고 σ/√n로 환산한다. 둘째 손가락 생산자다.
  2. `E/search/iv_matching_l.py:57-63` `_sigma_vgs`: 총 폭 W = I·L/IDu로 `mismatch_sigma_vgs`의 slope bin을 고른다. 그런데 `E/lut/mismatch_sigma.py` 머리 문서는 'W = 모델 카드에 넘기는 인스턴스 폭 `w`'라고 정의한다. 손가락 폭과 다른 정의다.
  3. `E/metrics/ss_linearize.py:68`: 레이아웃 전 접합 기하 = `pre_layout_geometry(w_m, op.W / w_m)`. 여기서 손가락 폭 = 슬라이스 폭이고 m = W/w_m은 정수가 아니다. 새 규칙에서는 슬라이스 폭(예: 3.0 µm)과 w_f(예: 2.6 µm)가 다르다. 그래서 넷리스트(EO-1, C22 `ad = ad_per_w·finger_w`, `pd = finger_w + pd_extra`)와 엔진 접합 용량의 기하가 갈린다. pd/W는 w_f에 따라 크게 변한다.
  4. `tools/spice_oracle/legacy_adapter.py:318-319`: n = floor(W/W_ref), finger_w = W/n이다(w_f ∈ [5, 10) µm, 셋째 규칙).
- 격자 반올림 뒤에는 m·w_f ≠ W다(출발점 112/142, 넷리스트 114/114). 봉인 W, 면적(`area_search_m2`), gds·gmb의 W 환산, 넷리스트 총 폭 가운데 무엇이 '실현 W'인지 계획에 없다. 둘이 다르면 같은 양(소자 총 폭)의 정의가 둘이 된다(graph 규칙 3).
- 수정안: WB-1 범위 2a 소비자에 (1)~(3)을 넣고, 옛 계산을 같은 변경에서 지운다(O-153, 만들면 배선). (4)는 EO-1이 대체하는 옛 경로로 적는다. '레이아웃 전 실현 총 폭 = m·w_f'를 같은 필드의 성분으로 두고, 면적·gds·접합·mismatch·넷리스트가 그것을 READS한다는 한 줄을 넣는다. 고정점(W → w_f → 슬라이스 → IDu → W)의 수렴 판정도 그 실현 폭으로 한다.

### (e) W-bin 키와 LUT memo 승인 예외 범위 -- 적합

- 슬라이스 키는 기존 `LutAccess` 폭 키 성분이다. design 40 §3.10.1(P-2 승인)의 소자별 키를 재사용하고, LUT memo는 N3.3 승인 예외 그대로다. 새 cache·memo·사본은 0이고, memo 상한 B_r는 다시 재게 되어 있다(:304). 고정점 중간값 (m, 슬라이스)는 블록 안 지역값이라 규칙 2 위반이 아니다.

### (f) 면적·용량·잡음·mismatch와 손가락 분할의 일관 -- 부분 적합 (V3-2에 포함)

- 용량·잡음 열 = 기준 폭 표 × 총 W 환산이고, mismatch 감도 = √(W_ref/(W·…))다. 총 면적 기준이라 분할과 무관하다. 이 부분은 맞다.
- mismatch slope의 bin과 접합 확산 기하는 손가락 폭에 의존한다. 이 둘은 V3-2 (2)(3)대로 손가락 필드를 읽어야 한다. 계획 문언 '접합 용량의 확산 기하는 DEC-91 (2) 그대로'(:304)는 손가락 폭이 w_f인지 슬라이스 폭인지 열어 둔다.

## 2. 검증 2 N-2~N-10 처리 판정

| # | 오케스트레이터 판정 | 처리(파일:행) | 판정 |
|---|---|---|---|
| N-2 | spec = `ebad06c1` 9개 + O-140 사본, bench = 아카이브 판정 도구 정의 | CPG-1 범위 1 :2269 | **경로는 적합**: 9개 spec·topology를 `git -C wt/integ-it12 show ebad06c1:…`로 모두 읽음(7~19 KB). zip 안 `_cmp_pilot/verify/o140/folded_cascode.sizing_spec.json`·`H/judge/hjudge.py`·`spice_judge_base.py`·`run_h_judge.py`·`judge/eng2spice.py`·`res/specs.txt` 실재(zip 553항목). **새 결함 V3-3**(bench 실행 설정) |
| N-3 | OP-11·N6.17 DEC-78 전파 | :277·:658·:1975·:1988, SF-1 범위 8 :2175, oracle-portability :513 OP-11 정의·부호 문단·Status·history v0.6.19 | 적합. 잔여 경미 V3-9(oracle :454 표 행, PW-1a 완료 조건) |
| N-4 | 가드 합 행 재개방 철회(O-158 유지), mirror_vds (가) 기본안 + (나) ⚠ | :304 (5)(a) 'StartConflict 기록만 -- R5′ (4) 재개방 촉발 행은 R-1′ 행뿐', (4) R5′ (2) 제외, :1849, X-LA8 :1929, U-126 :2454 두 질문·⚠ 두 개 | 적합. 경미 V3-7(LA-1 착수 조건 :1891 (2′) 문언이 옛 질문 하나만) |
| N-5 | design 넘김 목록을 계획 표에, LY2 :999 | 후속 정정 표 :1916(D41 줄 번호 15곳·D40·D42·엔진 계약), LY2 :999 '같은 선택 함수 하나' | 적합 |
| N-6 | 경미 | :304 '오케스트레이터 원칙 기본안·원문 밖 확장', 구간 집합(hull 금지), 하한 양 최솟값, 그 밖 양은 W 뒤, 출발 W·w_f = 출발값(EP-7), 완료 조건 toy :2245 | 적합 |
| N-7 | 경미 | 소비자 6곳 :2237(`lut_set.py:97·:105`, `mismatch_sigma.py:26·:30`, `_helpers_anchor.py:39`, `midpoint_checks.py:109` -- grep 실측과 일치), L도 격자 정수 비교 | 목록은 적합. 새 경미 V3-6(L 실현값) + V3-1(경계 방향 근거) |
| N-8 | 경미 | offset-strategy v0.7.3.1(Status·history, :408 포함), graph-consumption v0.14.2, oracle v0.6.19, gain-budget Status :11 | 적합 |
| N-9 | 경미 | U-129 :2457 'C_L 없는 topology, 측정 부하 없음 -- 기준선 case `cl: 0.0`' | 적합 |
| N-10 | 판정 'SF-1/TB-1 중 소비자' vs 작성자 'LA-1 범위 13 U5·U6 또는 SB-1 design 착수 전' | U-125 :2453 | **card 식별은 작성자가 맞음**. 시점 문언은 고칠 것 → V3-5 |

**N-10 근거(계획 원문)**:
- U-125의 대상은 R3 하한 행 목록에 들어갈 '슬루 비차단 하한'이다.
- 하한 행을 구현하는 card는 LA-1 범위 13(:1847 '순수 바이어스 가지 θ 전류의 출발값 = 하한 행 최대(**이 card 시점의 하한 행은 W_min뿐** -- R8·R10 하한은 card SB-1)')과 SB-1(:2214 'DEC-104 R8·R10 공급 요구 하한 구현', 완료 조건의 동적 항 = 셀 전류 − 최소 부하 전류 ≥ C·SR)이다.
- SF-1은 SR 선언 data와 형식만 다룬다(:2168 `.tran` 항목). 하한 행을 쓰지 않는다. TB-1은 θ 기저 S0 필드다.
- 따라서 '그 행의 소비 card'는 LA-1(하한 행 목록의 첫 소비자)과 SB-1(슬루 꼴 하한의 구현자)이다. 'SF-1/TB-1'은 원문 근거가 없다.
- 다만 '또는'은 시점을 하나로 정하지 않는다. LA-1이 SB-1보다 앞서고(SB-1 순서 :2227 '선행 = LA-1·SF-1·TB-1'), LA-1 범위 13 문언이 U-125 답에 의존한다. 그러므로 시점은 '**card LA-1 design 착수 전**'(검증 2 N-10 권고와 같음)이어야 한다.

## 3. 셋째 커밋이 새로 만든 결함과 계획 전체 grep

### V3-3 (중간) CPG-1 bench가 EO-1 oracle과 다르고, 기준선 쪽과 C′ 쪽의 기하 규칙이 다르다
- 아카이브 판정 도구는 `SPICEINIT = "set ngbehavior=hsa\nset ng_nomodcheck\n"`(zip `_cmp_pilot/H/judge/spice_judge_base.py`)이다. 판정 넷리스트는 `w=… l=… m=…`만 있고 ad/as/pd/ps가 없다(zip `H/netlists/two_stage_ota.H0r/pt0.sp`). 그래서 접합 용량이 0이다. 엔진 oracle(EO-1, `tools/spice_oracle/oracle_netlist.py:37` C22 확산 기하, .spiceinit 없음)과 실행 설정·기하가 둘 다 다르다.
- :2269는 '소자 기하(`w`·`m`)만은 C′ 엔진 손가락 필드'라고 한다. 그러면 기준선 H0r 판정(eng2spice `round(W/5 µm)`)과 C′ 판정(⌈W/w_hi⌉, 격자)의 기하 규칙이 다르다. '같은 판정 입력'은 spec·bench에서만 성립한다. 확산 기하를 쓸지(C22)도 정해지지 않았다.
- 수정안: (1) bench 실행 설정(호환 모드)과 확산 기하 포함 여부를 '판정 입력'에 명시한다(V3-1 수정안 2와 함께). (2) 기준선 쪽 기하를 기록값으로 남기고, 기하 규칙 차이를 판정 기록에 적는다. 또는 기준선 W에 같은 손가락 함수를 적용해 다시 잰다(어느 쪽이든 원래 취지 O-164 '같은 판정 입력'의 범위를 문언으로).

### 경미
- **V3-4** §1 (c) 참조. 그리고 U-130 근거 (ii) '손가락 폭 규칙에서 바로 그 소자들(W < 5 µm)만 바뀜'은 일반적으로 참이 아니다. W ∈ (5, 6] µm는 m = 2, w_f ≤ 3 µm라 슬라이스가 3.0 µm로 바뀐다. 출발점 실측에서는 그런 소자가 0이라 결론은 같다. 또 첫 bin 두 슬라이스 예시 'nfet 0.36·0.39'(:304)는 W_min 0.42 µm 아래라 도달할 수 없다(pfet 0.42·0.55만 의미가 있다). hsa 규칙이면 첫 bin 슬라이스는 하나다(V3-1 결정에 종속).
- **V3-5** U-125 시점 :2453 → 'card LA-1 design 착수 전'으로 하나로 정한다. LA-1 착수 조건 :1891에도 U-125를 넣는다(U-126 (2′)와 같은 꼴).
- **V3-6** D1(:2237, :304) 'W·L의 bin 소속은 격자 정수로 반올림한 값끼리 비교'는 L 실현값을 격자에 두는 규칙과 짝이 없다. as-built 넷리스트 L은 격자 밖이다(`l=1.99609u`, `0.49991u` 등). 엔진이 반올림 값으로 bin을 정하고 SPICE가 반올림 전 L을 받으면, 경계 ± 반 격자 안의 L에서 bin이 갈린다(예: 0.5024 µm -- 엔진은 0.500으로 [0.25, 0.5], 기본 모드 SPICE는 0.501 µm 초과라 위 bin). 수정안: '실현 L = 격자 반올림 값, LUT 조회·넷리스트가 같은 값을 READS'를 같은 문장에 둔다(w_f와 같은 꼴).
- **V3-7** WB-1 착수 조건(:2246)이 '계획 v6.38.2 승인 → design'뿐이다. U-130 시점 칸(:2458 'card WB-1 design 착수 전')과 맞지 않는다. LA-1 착수 조건 (2′)(:1891)는 'U-126 -- 범위 15 (c) S 좌표 확장 여부'라서 U-126의 둘째 질문(R5′ (2) 포함)이 빠졌다.
- **V3-8** history 셋째 커밋 행(:1481)의 '옛 문장' 목록에 DEC-91 (2)(:290) 문언 변경('소자 W가' → '손가락 폭 w_f가')이 없다. DEC-105 (2)만 있다. 이 변경은 U-130 '원래 취지와 다름'의 본문인데, 셋째 커밋 행에 근본원칙/결정 문언 변경 표시가 없다. '원래 취지와 다름' 표(X-*)에도 U-130 행이 없다(U-126은 X-LA8이 있음).
- **V3-9** oracle-portability :454 N3 표 `power_dc_w` 행이 아직 'Σ_레일 V·I'(셈하는 레일 없음)다. gain-budget :1988은 'PW-1a 대조 toy에 선언 레일 toy 추가'라고 하지만, PW-1a 완료 조건(:1983-1986)에는 그 toy가 없다.
- **V3-10** (기록) U-130 근거 (iii) 수치는 실측(7 µm 초과 82/142)과 맞다. 사실 (v) 'nfet·pfet 마지막 bin [7, 100] µm'은 기본 모드 기준이다. hsa에서는 7 µm 슬라이스가 그 bin에 든다. 모드 의존 표지가 필요하다(V3-1과 함께).

### 계획 전체 grep 결과
- U-125~U-130: N7.2 행 6개(:2453-2458), Status :11, 사용자 결정 표 :382 'U-125~U-130', :304·:2240(U-130)이 서로 맞다. 착수 조건 연결 누락은 V3-5·V3-7.
- 낡은 문언: 'kind당 폭 슬라이스 하나'는 후속 정정 표(:1916)와 WB-1 사실(:2233)에만 as-built 인용으로 남아 있다. 'GB4 국소 입력'은 (2)에서 지워졌다. '레이아웃 뒤 실현 폭 재확인과 같은 슬라이스 규칙 하나' 옛 문장은 LY2 :999 '같은 선택 함수 하나'로 맞춰졌다. N6.17 'power_dc_w는 이 백로그가 아니다'는 정정되었다.
- 다른 계획: offset-strategy·graph-consumption은 규칙 변경 없이 인용만 바뀌었고 충돌이 없다. oracle-portability는 OP-11 정합, OP-7 경계 선언과 WB-1 D1 사이에 충돌이 있다(V3-1).

## 4. 원칙 점검표

| 원칙 | 판정 | 방법 |
|---|---|---|
| graph 단일 정본(writer 하나·소비자 ≥ 1·둘째 생산자 0) | 결함 V3-2: 기존 손가락 생산자 `device_sigma._sigma`·`ss_linearize:68`·`iv_matching_l` 총 폭·`legacy_adapter`가 목록에 없고, 실현 총 폭 정의가 둘 | 실측(코드 grep) |
| 새 cache·memo·사본 | 0, LUT memo 승인 예외 안 | 실측(계획·`lut_set.py`) |
| 만들면 배선 | 손가락 필드 → EO-1·슬라이스 선택은 배선했고, mismatch·접합 소비자 배선이 누락됨(V3-2). DEC-78 개정 → SF-1 범위 8·OP-11 배선 적합 | 실측 |
| DC/AC 분리 | 적합(DC 열만 W-bin, 용량·잡음은 기준 폭) | 실측(LUT 열) |
| O-127 | 적합(R6 목표 행 층 적용, :304 (4)) | 원문 |
| EP-7 | 적합(출발 W·w_f = 출발값, 정의 축 표기) | 원문 |
| fail-closed | 거짓 거부 0으로 개선(§1 (a)). 경계 bin 불일치는 fail-closed가 아니라 조용한 모델 오차가 된다(V3-1) | 실측(ngspice) |
| O-153 | 옛 eng2spice 관례 대체를 명시했다. 다른 옛 손가락 계산의 삭제는 누락(V3-2) | 실측 |
| 상수 발명 금지 | 위반 없음. w_hi는 LUT 선언 유도(근거 문언 부족 V3-4) | 실측 |
| 회로 이름 조건 | 0(규칙 문언). PDK 폭 예시만 | 원문 |
| 계획/이력 분리 | 대체로 적합. history 옛 문장 누락 V3-8 | 원문 |
| P0 '정의 = SPICE와 같게' | 결함 V3-1(호환 모드 미선언) | 실측(ngspice) |

## 5. '원래 취지와 다름'·근본원칙 문언 변경 목록 완전성

| 항목 | 표지 | 판정 |
|---|---|---|
| DEC-104 (0)·R3·(3)(b) | history :1479(둘째 커밋 정정 문장) | 있음 |
| DEC-104 R5′ (2) | U-126 대안 (나)에 '근본원칙 문언 변경' ⚠. 기본안 (가)는 무변경 | 있음 |
| DEC-104 R5′ (4) 합 행 촉발 | 철회되어 해당 없음(:304 (5)(a)) | 해당 없음 |
| DEC-78 | history :1479·:1481(N-3), oracle v0.6.19 '새 결정 아님(전파)' | 있음 |
| DEC-91 (2) | 첫째 커밋 옛 문장은 :1479 (가)에 있음. 셋째 커밋 'W → 손가락 폭' 변경은 옛 문장·표지 없음 | **누락(V3-8)** |
| U-130(손가락 폭) | :304·:2458·history (1) '원래 취지와 다름' | 있음. X 표 행 없음(V3-8) |
| U-125·U-126·N-6 포락·N13·신호 경로 | 각 표지 있음 | 있음 |
| 새로 필요한 표지 | V3-1 수정안 2(CPG-1 bench 모드 변경)를 택하면 O-164 '같은 판정 입력'의 원래 취지와 다를 수 있어 표지 + U 행 필요 | 예고 |

## 6. 재현 명령

```bash
set -e
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6382; R=/c/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12
E=$R/skills/analog-gmid-design/gmid_engine; P=$W/docs/01-plan/features/gain-budget-gmid-sizing.plan.md
git -C $W diff --stat a8a44ace..1e4ae472; sed -n '304p;2233p;2237p;2240p;2245p;2246p;2269p;2453,2458p' $P
# PDK W bin, LUT 슬라이스
python -I -c "import re;t=open('C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice').read();print(sorted({(float(a),float(b)) for a,b in re.findall(r'wmin\s*=\s*([0-9.e+-]+)\s+wmax\s*=\s*([0-9.e+-]+)',t)}))"
ls /c/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/*__W*um_dc.npz
# 경계 bin: 같은 넷리스트를 .spiceinit 없이 / 'set ngbehavior=hsa' 로 -- 넷리스트 = lod.spice + {n,p}fet mismatch.corner + tt.pm3 include,
#   X<i> d g 0 0 sky130_fd_pr__nfet_01v8 w=5u l=1u 등, .control op; showmod m.x<i>.msky130_fd_pr__nfet_01v8 : wmin wmax lmin lmax
#   (scratchpad .../ng/g.cir = hsa 디렉터리, .../ng2/g.cir = 기본 모드)
/c/ngspice/Spice64/bin/ngspice_con.exe -b g.cir | grep -iE "model x|wmin |wmax |lmin |lmax "
# 판정 도구 실행 설정·넷리스트 기하
python -I -c "import zipfile;z=zipfile.ZipFile('C:/Users/HSLEE/Documents/Todoc/fpga/wt/_archive/cmp1_H_baseline_2026-10-28.zip');s=z.read('_cmp_pilot/H/judge/spice_judge_base.py').decode();print([l for l in s.splitlines() if 'SPICEINIT' in l]);print(z.read('_cmp_pilot/H/netlists/two_stage_ota.H0r/pt0.sp').decode())"
# fail-closed·경계 집계(손가락 규칙 시뮬레이션): scratchpad count.py <out_survey 경로> <zip 경로>
# 옛 손가락 생산자
grep -n "ceil(width" $E/metrics/device_sigma.py; grep -n "pre_layout_geometry" $E/metrics/ss_linearize.py
grep -n "nfin" $R/skills/analog-gmid-design/tools/spice_oracle/legacy_adapter.py; sed -n '57,63p' $E/search/iv_matching_l.py
# CPG-1 spec 경로
for c in two_stage_ota current_reuse_telescopic_ota ngcc_3stage_ff; do git -C $R show ebad06c1:skills/analog-gmid-design/assets/library/$c.sizing_spec.json | wc -c; done
git -C $W status --short; git -C $R status --short
```
