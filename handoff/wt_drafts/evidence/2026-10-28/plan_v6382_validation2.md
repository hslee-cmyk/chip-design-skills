# 계획 v6.38.2 독립 검증 2 (2026-10-28)

- 피검: `wt/plan-v6382` 커밋 `233dc336`(첫째) + `a8a44ace`(둘째), 기준 `1fefcab1`. 바뀐 파일 = gain-budget plan·history, `offset-strategy.plan.md`(3행), `graph-consumption.plan.md`(1행).
- 검증자: 독립 검증 2. 작성자도 검증 1 담당도 아니다. 작성자 보고·커밋 메시지·검증 1 결론은 증거로 쓰지 않았고, 아래 근거는 모두 원문·코드·LUT·PDK·아카이브를 직접 읽은 것이다.
- 판정 기준: 오케스트레이터가 작성자에게 준 판정(브리핑 '입력' 절)을 기준으로 처리 여부를 봤다.
- 파일 수정: 이 문서 하나만 썼다. git은 `set -e` + `git -C`로 읽기 명령만 썼다(reset/checkout/stash 없음). `git -C wt/plan-v6382 status --short` 빈 출력, HEAD `a8a44ace`.
- 줄 번호: 계획 = `a8a44ace` 판(DEC-78 :277, DEC-91 :290, DEC-104 :303, DEC-105 :304, LR6 :684, LY2 :999, N6.1 :1239-1241, LA-1 범위 15 :1849, 완료 조건 9·10 :1887·:1888, 착수 조건 :1891, X-LA8 :1928, N6.17 :1974·:1987, SF-1 :2171-2175, TB-1 :2189-2190, N6.32~N6.34 :2228-2274, U-125~U-129 :2451-2455).

## 0. 요약

| 심각도 | 수 | 항목 |
|---|---|---|
| 높음 | 1 | N-1(W-bin의 'W'가 총 폭이라 SPICE·레이아웃 뒤 규칙과 물리적으로 어긋나고, 7 µm 초과 소자는 fail-closed로 몰림) |
| 중간 | 4 | N-2(CPG-1 기준선 spec·bench 경로가 일부만 있음), N-3(DEC-78 개정과 OP-11·N6.17 충돌), N-4(DEC-104 R5′ (2)·(4)를 표지 없이 바꿈), N-5(D-12 미흡) |
| 경미 | 5 | N-6~N-10 |

검증 1의 22건: 적합 19, 부분 적합 2(D-8 → N-2, D-15 → N-3), 미흡 1(D-12 → N-5). 사용자 확인 5건은 모두 계획에 반영됐다(U-125·U-126·U-129, CPG-1 셈 철회, N12 원문 반영).

**승인 상정 의견: 아직 불가.** N-1은 C′ 경로 완료 게이트(CPG-1) 자체를 막을 수 있는 정의 결함이고, 사용자 결정 Q6-1 (A)의 'W' 해석 확인이 필요하다. N-2~N-5는 같은 판에서 고칠 수 있다.

## 1. 검증 1 결함·확인 처리 판정(오케스트레이터 판정 기준)

| # | 오케스트레이터 판정 | 처리 | 판정 | 근거(파일:행) |
|---|---|---|---|---|
| D-1 | 원문 형태 복원 | DEC-105 (4) '목표 행·K-1 (i)·해 없으면 StartConflict(기록 레코드)'로 되돌림. X-LA8은 '원래 취지와 같음' | 적합 | plan :304 (4), :1928; as-built `E/search/start_values.py:66-73` frozen dataclass(기록, 정지 아님) 직접 확인 |
| D-2 | 층 적용은 O-127로 | '구성원이 B·W4·V_R만이면 출발 단계 1회(graph reuse), 층 0 변수가 섞이면 층 0 후보마다 같은 R6 블록' | 적합 | :304 (4) '층 적용' = DEC-104 R6(:303 '출발 단계 스냅샷과 층 0 후보 스냅샷에서 같은 블록') |
| D-3 | 남는 차이만 U-126 | S 좌표는 R5′ (1) 순서상 움직이지 않음을 기본안으로 하고 U-126을 그 질문 하나로 좁힘 | 적합(새 결함 N-4 동반) | :304 (4) '움직이는 좌표', :2452. R5′ (1)·(4)(iii) 원문(:303)과 맞음(§2 (b)) |
| D-4 | W 없는 단계는 상계 유지 | 도달 가능한 슬라이스 포락: 상한 양은 최댓값, 출발 경계는 합집합 | 적합(경미 N-6) | :304 (2) 'W가 아직 없는 단계', WB-1 범위 2 :2238 |
| D-5 | DC 열만, 나머지는 기준 폭 | '읽는 열' 절, DEC-91 (2)도 같은 문언 | 적합 | :290, :304 (2). LUT 직접 확인: `*__W*um_dc.npz` 열 = ID·GM·GDS·VTH·GMBS·VDSAT; 기준 표 `sky130_nfet_pfet_lut_v2.npz`에만 CGG·CGD·CGS·CGB·CDD·CSS·SVG2_*, `_noise_r1` SVG2_F, `_mismatch_r1` DVGS_*; `lut_types.py:27` `SLICE_OPTIONAL_COLUMNS` |
| D-6 | D1은 WB-1 범위 | WB-1 범위 0 '첫 커밋'·완료 조건 (1) red | 적합(경미 N-7) | :2236 |
| D-7 | TB-1 범위 3·4는 LA-1 병합으로만 | 범위 3 끝 문장·범위 4 '**LA-1 통합 병합으로만**' | 적합 | :2189, :2190, DEC-105 (4) 끝 |
| D-8 | SPICE 판정 = 보관 기준선 spec·bench, 엔진 = 현행 spec, C_L은 사용자 확인 | CPG-1 범위 1 '판정 입력', U-129 | 부분 적합 → N-2 | :2267, :2455. 경로 실재 여부는 §2 (c) |
| D-9 | O-140 사본 셈 포함(10항목, H0r 4), C′ 전부 병합 뒤 | 범위 1·완료 조건·순서 고침, 옛 '미병합 허용' 철회 | 적합 | :2267, :2272, :2274, N6.1 :1241; O-164 원문 user_decisions:1145와 일치 |
| D-10 | RS-1은 LA-1 뒤 | 순서 '선행 = LA-1 병합 … CPG-1 앞', N6.1 행 같음 | 적합 | :2257, :1240 |
| D-11 | offset-strategy 옛 인용, GC-5 역참조 | offset-strategy :212·:304·:619, graph-consumption :459 | 적합(경미 N-8: :408 잔여·버전 미갱신) | 해당 행 직접 확인 |
| D-12 | design 넘김 목록 보강 | WB-1 사실 (ii)에 design 40 §3.10.1·42 D-P2만 추가. 목록은 계획 밖에 있음(history :1479 '검증 보고에 둠'), LY2 :999 그대로 | **미흡** → N-5 | 둘째 커밋 history 행 (9) 목록에 D-12 없음 |
| D-13 | history 사실대로 | 첫째 커밋 행 정정 | 적합 | history :1479 |
| D-14 | Q2-2 원문 | '같은 2배 사다리 다음 칸, 사다리 끝 처리는 그 규칙 그대로' | 적합 | :304 (3) |
| D-15 | N12는 원문대로 | DEC-78 행·DEC-105 (9)·SF-1 범위 8에 '목적 축도 같은 선언' | 부분 적합 → N-3 | :277, :304 (9), :2174 |
| D-16 | Q-S1 (라) 등록 | 완료 조건 9 (f) (9) | 적합 | :1887 |
| D-17 | 순서 문자열·착수 조건 | 'WB-1' 삽입, (2′) U-126 | 적합 | :1891, :1892 |
| D-18 | 앵커 동작 변경 표지 | DEC-105 (1)·LA-1 범위 15 (a) '**동작 변경**' | 적합 | :304 (1), :1849 |
| D-19 | '신호 경로' 원칙 기본안·되먹임 경로 | 표지·문언 둘 다 | 적합 | :304 (4) '대상' |
| D-20 | N13 사본 삭제 = 원칙 기본안 | DEC-105 (10)·SF-1 범위 9 | 적합 | :304 (10), :2175 |
| D-21 | as-built 파서 재사용 | WB-1 범위 1 `_bin_blocks`·`bin_index`, 자리 = LUT 적재 메타 | 적합 | :2237; `lut_set.py:88-109` 직접 확인 |
| D-22 | R7 (가) 합 행 | '합 행을 어기면 깨진 행으로 보고 R5′ (4)(ii)로 다시 연다' | 처리됨, 그러나 새 결함 N-4 | :304 (5)(a) |
| 확인 1 | U-126 다시 묻기 | 질문 하나로 좁힘, 시점 = LA-1 design 착수 전 | 적합 | :2452 |
| 확인 2 | U-125 | 그대로 | 적합(경미 N-10) | :2451 |
| 확인 3 | CPG-1 셈 | 10항목으로 바꿈(원문대로) | 적합 | :2272 |
| 확인 4 | CPG-1 입력 | 판정 입력 분리 + U-129 | 부분 적합 → N-2 | :2267 |
| 확인 5 | N12 목적 축 | 원문대로 반영 | 적합(N-3) | :277 |

## 2. 둘째 커밋이 새로 만든 결함과 지정 검사 (a)~(e)

### (a) W-bin '포락' -- 새 상수 없음, 상계 유지. 단 경미 N-6
- 상한 양(A_max)에 슬라이스 위 최댓값을 쓰면, 도달 가능한 W에 대한 상계가 유지된다. 슬라이스가 없는 bin은 커널에서 fail-closed라 도달 집합에서 빠진다. 새 상수는 없다(W_min은 PDK 선언).
- 출발 경계의 합집합은 출발값 전용이라 EP-7에 맞고, 실현 가능한 점을 자르지 않는다.
- fail-closed는 손상되지 않는다. 거부는 커널(슬라이스 없음·순환)에만 있다.
- 미흡(N-6): 구간들의 '합집합'은 이어지지 않을 수 있다(구간 하나인지 구간 집합인지 미정). 상한·출발 경계가 아닌 W 없는 양(예: GB4의 다른 입력)의 포락 방향이 정해지지 않았다. 출발 경계 합집합 toy가 완료 조건에 없다. '원래 취지와 다름/원칙 기본안' 표지도 없다(Q6-1 원문에 없는 확장이다).
- 그러나 포락의 전제인 'W-bin'의 W 자체가 N-1의 결함을 안고 있다.

### N-1 (높음) W-bin을 고르는 'W'가 총 폭이다 -- SPICE·레이아웃 뒤 규칙과 물리적으로 어긋나고 큰 소자는 fail-closed로 몰린다
- 사실(직접 측정):
  - PDK `C:/pdk/sky130_fd_pr/cells/{nfet,pfet}_01v8/*__tt.pm3.spice`의 W bin = nfet 0.36·0.39·0.42·0.52·…·5·**7 → 100 µm**, pfet 0.42·0.55·…·5·**7 → 100 µm**.
  - LUT W 슬라이스는 nfet 20개·pfet 12개이고 모두 bin 경계 폭이며 가장 넓은 것이 7 µm다(`lut_data/sky130_lut_v2/`, manifest).
  - `bin_index`의 '아래 bin 우선' 규칙(`_helpers_bins.py:1-23`) 때문에 7 µm 슬라이스는 [5, 7] bin에 들어간다. 따라서 **[7, 100] µm bin에는 슬라이스가 없다.** 100 µm를 넘으면 bin 자체가 없다.
  - 첫 bin에는 슬라이스가 둘 들어간다(nfet [0.36, 0.39]에 0.36·0.39, pfet [0.42, 0.55]에 0.42·0.55). 어느 슬라이스를 읽을지 정의가 없다(검증 1 D-5 뒷부분, 미처리).
- 계획 문언: DEC-105 (2)(:304)는 'W = I·L/IDu'(소자 총 폭)가 속한 bin을 읽고, 그 bin에 슬라이스가 없으면 fail-closed라고 한다. 결정 자료 PKG §6(d) A도 '실현 폭 W(= I·L/IDu)'다.
- 충돌 1 (P0 물리 정합): SPICE는 소자를 `w = finger_w`, `m = n_fingers`로 만들고(LY8 :1005), bin은 finger 폭으로 고른다. 기준선 판정 넷리스트도 그렇다(아카이브 `_cmp_pilot/H/netlists/two_stage_ota.H0r/pt0.sp`: `XM6 … w=5.00337u … m=225`, `XM1 … w=7.29637u m=1`). 총 폭으로 고른 bin은 SPICE가 쓰는 bin이 아니다. 예: XM6 총 1125 µm는 bin 밖이고, SPICE는 [3, 5]의 5 µm bin을 쓴다.
- 충돌 2 (계획 안 모순): DEC-105 (2)는 '레이아웃 뒤 실현 폭 재확인(N3.17 E5)과 같은 슬라이스 규칙 하나'라고 하지만, 레이아웃 뒤 규칙은 finger 폭 슬라이스다(LY1 `J_slice(kind, fw, …)`, LY2 :999 '후보 finger_w는 PDK 특성화 폭의 DC 슬라이스'). 규칙이 둘이다.
- 영향: PKG §6(b) 9회로 출발점에서 W ≥ 5 µm 소자가 nmos 34/74·pmos 51/68이다. 그 가운데 7 µm를 넘는 소자는 모두 'bin에 슬라이스 없음 → fail-closed'가 된다. CPG-1(H0r 4 이상)을 구조적으로 막을 수 있다. 옛 규칙(kind당 5 µm)이 우연히 SPICE와 맞던 경우(손가락 ≈ 5 µm)가 오히려 틀어진다.
- 원칙: P0(정의 = SPICE와 같은 정의, O-29 (1)), fail-closed의 대상 오류(거짓 거부), graph 규칙 3(같은 양 '소자 슬라이스'의 정의 둘).
- 수정안(사용자 확인 필요, 새 U 행으로): Q6-1 (A)의 'W'를 **SPICE가 bin을 고르는 폭 = finger 폭**으로 읽는다. 레이아웃 전 finger 폭은 PDK·LUT 선언에서 유도하는 규칙 하나로 정한다. 후보는 '특성화 슬라이스 폭 가운데 하나를 고르고 nf = ⌈W/fw⌉'이고, 판정 도구의 5 µm 같은 박힌 값은 쓰지 않는다. 그 규칙은 레이아웃 뒤 LY1·LY2와 같은 함수 하나여야 한다. 대안 (나)는 총 폭을 유지하고 [7, 100] µm bin 슬라이스를 LUT에 추가하는 것인데, 여러 손가락 소자에서 P0 불일치가 남는다. 대안 (다)는 이웃 bin 대체인데, 원문 '대체 없음'과 충돌하므로 기각한다. 첫 bin 두 슬라이스의 선택 규칙도 같은 U에서 정한다.

### (b) U-126 '확장 안 함' 기본안 대 R5′ 원문 -- 맞음
- R5′ (1)(:303): 'spec → S·θ 전류(독립 좌표, R3·R4) → 쓰기 계획 등식 → …'. 같은 곳 (4)(iii): S는 '행이 깨질 때만', 'S만 남으면 층 0 정의역 조건'으로 다시 연다. 목표 행은 검사 행이 아니므로 S를 다시 열지 않는다. 기본안 문언(:2452)과 맞는다.
- 다만 기본안이 곧 원문 형태이므로 남는 질문은 '원문보다 넓힐 것인가'뿐이다. 사용자 확인으로 남겨 둔 것 자체는 오케스트레이터 판정('남는 차이만 U-126')과 맞는다.

### N-4 (중간) DEC-104 R5′ (2)·(4)의 선택·재개방 규칙을 DEC-105에서 표지 없이 바꿈
- R5′ (2)(:303): W4·V_R은 '모든 포화 행·writer_root 행을 함께 만족하는 창 안에서', 고르는 점 = 'max-min -- **K-1 (ii)**'다. 창 안에서는 위반 최소 단계 (i)가 늘 비어 있다. DEC-105 (4)는 같은 선택에 `mirror_vds`를 'K-1 (i)'로 넣는다(:304 '(나) 그 밖 B와 R5′ (2) W4·V_R 선택에서 K-1 (i)에 든다', LA-1 범위 15 (c) :1849). 그러면 R5′ (2)는 '목표 행 위반 최소 → max-min'이 된다. 이는 DEC-104 문언 변경인데 DEC-104 행에 역참조가 없고, 근본원칙 문언 변경 목록(history :1479·:1480)에도 없다.
- D-22 처리(:304 (5)(a)): '합 행을 어기면 그 행을 깨진 행으로 보고 R5′ (4)(ii) K-1로 다시 연다'. 이는 R5′ (4)의 재개방 촉발 행 종류에 가드 합 행(R-1′ 행이 아님)을 더한다. R5′ (4) 끝 '그래도 해가 없으면 fail-closed'와 겹쳐서, 같은 칸 (4)(iii) '출발 단계 fail-closed는 R-1′ 행에만(O-158 (A′) ②, **원래 취지와 다름 승인**)'과 충돌할 수 있다. 앞선 판은 R-1′ 아닌 행을 사다리에 넣을 때마다 승인 표지를 달았다(O-158·O-159). 이번에는 표지가 없다.
- 수정안: (1) DEC-104 R5′ (2)에 'DEC-105 (4) 목표 행이 있으면 K-1 (i)부터' 한 줄과 표지('오케스트레이터 원칙 기본안 -- 원문 Q3-1 "§6.7 위반 최소 단계"')를 단다. (2) D-22는 검증 1 수정안대로 R7 (가) '가드 구간과의 교집합'에 합 행을 포함하는 꼴(나머지 경계 ∩ 합 행 만족 집합, 비면 StartConflict **기록**)을 기본안으로 한다. 재개방 촉발로 둘 경우에는 '출발 단계 fail-closed 아님(기록)'을 명시하고 원래 취지와 다름 표지를 단다. (3) 두 변경을 근본원칙 문언 변경 목록에 넣는다.

### (c) CPG-1 기준선 spec·bench 경로가 아카이브에 있는가 -- 일부만 있다 → N-2 (중간)
- 있는 것(zip 목록 553항목, python zipfile 확인): `_cmp_pilot/H/judge/res/specs.txt`, `_cmp_pilot/verify/o140/folded_cascode.sizing_spec.json`, `_cmp_pilot/H/netlists/<회로>.<변형>/pt*.case.json`.
- 문제:
  1. `specs.txt`는 spec 파일이 아니라 `specdump.py` 출력이다. 덤프에 든 spec은 two_stage_ota·two_stage_ota_sf·folded·nmcnr·pushpull·common_gate의 **6회로 + O-140 사본뿐**이다. **current_reuse_telescopic_ota·sf_pushpull_output_opamp·ngcc_3stage_ff 3회로는 없다.** 또 덤프가 손실된다(`specdump.py`: 비제약 필드를 `json.dumps(…)[:600]`으로 자르고 `source`·`record` 칸을 지움).
  2. `case.json`은 판정한 변형 폴더에만 있다(common_gate·folded H0r·nmcnr H0rX·pushpull·two_stage·two_stage_sf, 그리고 dev). current_reuse·sf_pushpull·ngcc·folded O-140 사본은 front가 0이라 넷리스트가 없다. 10항목 가운데 4항목은 'pt*.case.json과 같은 부하·바이어스 정의'를 읽을 데가 없다. 또 case.json의 바이어스 전압(`extra_sources`)은 그 점의 엔진 값이지 bench 정의가 아니다.
  3. 아카이브에는 library spec 원본과 topology가 없다.
- 확인: 원본은 `git -C wt/integ-it12 show ebad06c1:skills/analog-gmid-design/assets/library/<회로>.sizing_spec.json`(·`.topology.json`)으로 9회로 모두 읽을 수 있다(current_reuse 실측).
- 수정안: 판정 spec은 '기준선 엔진 커밋 `ebad06c1`의 library spec 9개 + 아카이브 O-140 사본'으로 하고, 판정 기록에 sha256을 적는다. bench 조건은 '아카이브 판정 도구(`H/judge/hjudge.py`·`spice_judge_base.py`)의 측정 정의 + 기준선 spec의 `measurement_load`'로 한다. case.json은 사례로만 인용한다. '같은 입력 비교' 표현은 엔진 입력이 현행 spec이므로 '같은 판정 입력'으로 고친다.

### (d) U-129 C_L = topology connectivity -- 맞음
- O-140 D4 원문(user_decisions:974): 'common_gate C_L = 1 pF (topology passive 원소 추가 = connectivity 변경 -- 사용자 지정, measurement_load 표지 여부는 data 커밋 때 확인)'. 기준선 spec 주석(`specs.txt` common_gate: '부하 CL은 SP-6(c) 대기 -- 정해지면 topology에 CL 요소(사용자) + 여기 값')과 topology 정본 규칙(connectivity는 사용자만)이 서로 맞는다. 판단은 적합하다.
- 경미(N-9): U-129 기본안 '기준선 common_gate = C_L 없는 topology + 판정 deck 측정 부하'는 사실과 조금 다르다. 기준선 case `cl: 0.0`이고 spec에 measurement_load가 없으므로 판정 부하도 없다. 'C_L 없음, 측정 부하 없음'으로 고친다.

### (e) DEC-78 개정 대 oracle-portability OP-11 -- 같은 판에서 고칠 충돌 → N-3 (중간)
- OP-11(oracle-portability :513): '정의: 엔진 DEC-78 인용'으로 시작하고, `power_dc_w = Σ_{기준 아닌 레일} voltage × rail_current_A`라 한다. 또 '**엔진 `counted_rails` 부분 선언은 `supply_current_dc`에만 닿고 `power_dc_w`에는 닿지 않는다(`supply.py:65-69`)**'고 명시한다. 개정된 DEC-78(:277 '셈하는 레일 = `counted_rails`가 선언되면 그 레일')과 정면으로 어긋난다. 선언이 있는 회로에서는 엔진과 oracle의 정의가 갈린다(O-29 (1)·O-32 위반). 그 차는 `model_error_power_dc_w`(PW-1b)에 거짓 모델 오차로 들어간다.
- 같은 계획 안에도 낡은 문장이 남았다:
  - N6.17 사실 :1974 '엔진 `power_dc_w`는 모든 레일의 Σ V·I'.
  - 백로그 :1987 '(`power_dc_w`는 이 백로그가 아니다 -- 엔진 `power_dc_w`는 `counted_rails`와 무관 … oracle OP-11과 코드상 갈림이 없다. … B-L10은 이 확인으로 닫았다)'. DEC-78 개정으로 B-L10 닫힘의 근거가 사라졌다.
  - SPICE 해석 표 :658.
- 판단: 같은 판에서 고쳐야 한다. 근거는 셋이다. (1) 검증 1 D-11의 다른 계획 인용(offset-strategy)을 같은 판에서 고친 판정과 같은 꼴이다. (2) OP-11은 DEC-78 문언을 인용 정의로 갖고, 그 반대 명제를 사실로 적고 있다. (3) DEC-105 (9)의 '그 계획 후속 정정'에는 추적 자리(U 행·후속 정정 표 행)가 없다. oracle 입력에 레일 집합을 실어야 하므로 EO-1 입력 계약(인터페이스)도 같이 정해야 한다. 실제 영향은 `counted_rails` 선언 회로(held-out data 커밋)부터라 즉시 발동하지는 않는다. 그래서 '중간'으로 둔다.
- 수정안: (1) oracle-portability OP-11 정의를 '선언이 있으면 선언 레일 ∖ 기준 레일, 없으면 기준 아닌 레일 전부'로 고치고, 그 계획 버전·history를 올린다(gain-budget 동반 승인). 또는 최소한 gain-budget 후속 정정 표에 행 하나와 U 행을 둔다. (2) N6.17 :1974·:1987, :658을 고치고 B-L10을 다시 연다(PW-1a 부호 대조 toy에 선언 레일 toy 추가). (3) EO-1 oracle 입력에 레일 집합을 싣는 자리를 적는다(새 칸이면 writer = spec 로더 하나).

### N-5 (중간) D-12 design 넘김 목록 미반영
- 오케스트레이터 판정은 '경미 13건 전부 반영(… design 넘김 목록 보강 …)'이었다. 둘째 커밋 history 행 (9)에는 D-12가 빠져 있다. 계획에는 WB-1 사실 (ii)의 design 40 §3.10.1·42 D-P2 한 문장만 들어갔다(:2232). 첫째 커밋 history(:1479)는 'design에 넘길 낡은 문언 목록은 v6.38.2 검증 보고에 둠'이라 하여 계획 밖에 두었다.
- 그런데 LA-1 착수 조건 (1)(:1891)은 'design 개정 항목은 아래 후속 정정 표'라고 하고, 후속 정정 표(:1905-1915)에 v6.38.2 행이 없다. design 41 원문 재확인(`wt/plan-v6382/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`):
  - :1044 '§6.4-2 matching 하한'
  - :1495 'matching L 하한'
  - :1569 'A_max가 미상이거나 … 비활성'
  - :1570-1599 §6.4-2(L ≥ √(A_min·IDu/I))·§6.4-6 'L = max(1, 2, 3의 하한)'
  - :1859 부하 gm/ID 상한
  - :1947 §6.7 7a test
  - :1958 '절대 offset 회로에서만 L 하한 활성'
  - 모두 아직 그대로다.
- 계획 안 LY2 :999 '고른 finger_w가 LUT 기준폭(`w_ref_m`)과 다르면'도 그대로다(N-1과 함께 고칠 대상).
- 수정안: 후속 정정 표에 'design 41·40·42·엔진 계약(v6.38.2 DEC-105)' 행을 두고 위 줄 번호와 sizing 계약(`kernel_keys.py:5-6` 'kind당 폭 슬라이스 하나')·lut CONTRACT 1.4(`w_ref_m`)·DEC-104 R5′ (2)(N-4)를 적는다. LY2 :999는 계획 안에서 고친다.

### 경미

- **N-6** (a) 참조. 포락에 '오케스트레이터 원칙 기본안' 표지, 합집합 = 구간 하나(hull)인지 구간 집합인지, 그 밖 W 없는 양의 방향, 출발 경계 toy를 정한다. 출발 단계에서 고정점 함수가 낸 W는 '출발값(EP-7) -- 커널 W와 다른 정의 축'임을 적는다(graph 규칙 3).
- **N-7** D1 정정의 소비자 목록이 모자란다. 실측 `bin_index` 호출: `lut_set.py:97·:105`, `mismatch_sigma.py:26·:30`, `_helpers_anchor.py:39`(조회 L의 bin), `midpoint_checks.py:109`. 계획(:2236)에는 lut_set·mismatch_sigma:26만 있다. 제조 격자 반올림은 W 규칙인데 같은 함수가 L에도 쓰이므로, L 쪽 경계 규칙도 함께 정해야 한다. 반올림 뒤 비교도 float이면 같은 ulp 문제가 남으므로 '격자 정수 단위 비교'까지 적는다. `manufacturing_grid_m`은 실재한다(`assets/sky130_pdk_decl.json`, `layout/contract_input.py:45`).
- **N-8** 동반 계획 offset-strategy(v0.7.3)·graph-consumption(v0.14.1)의 본문을 바꿨는데 버전·Status·각 history 행이 없다. gain-budget Status(:11)에도 DEC-78 개정·동반 계획 변경이 없다. offset-strategy :408 'matching 쪽 L 하한 출발값이 켜져'가 남아 있다.
- **N-9** (d) 참조(U-129 문언).
- **N-10** U-125 '시점' 칸이 '사용자 확인'으로만 되어 있다. R3 하한 행 목록은 LA-1 범위이므로 'LA-1 design 착수 전'으로 맞춘다(U-126과 같은 꼴).

## 3. 원칙 점검표(실측/자기보고 구분)

| 항목 | 판정 | 방법 |
|---|---|---|
| graph 단일 정본(writer 하나·소비자 ≥ 1) | 적합. g_i^(1)·`mirror_vds` S0 필드는 writer 하나, 소비자 LA-1, 병합 규칙 정합. 포락은 각 writer 블록 안. 단 W-bin 슬라이스 정의 둘(N-1)과 출발 W 축 미명시(N-6) | 실측(계획 원문) |
| 새 cache·sctx·사본 | 0. W-bin 지도 = as-built LBinMap(LUT 적재 메타, `lut_set.py:88-109`), 슬라이스 키 = `LutAccess` 성분이라 N3.3 LUT memo 승인 예외 범위 안 | 실측(코드) |
| 만들면 배선 | TB-1 범위 3·4 → LA-1 병합만(적합). DEC-78 개정의 oracle 쪽 미배선(N-3) | 실측 |
| DC/AC 분리 | 적합(W-bin = DC 열, ss는 DC 열에서 파생, 용량은 기준 표) | 실측(LUT 열) |
| O-127 | 적합(층 적용) | 실측 |
| EP-7 | 적합(목표 행·포락·출발 경계는 출발값 전용) | 실측 |
| fail-closed | 결함(N-1 거짓 거부, N-4 출발 fail-closed 범위 모호) | 실측(PDK·LUT) |
| O-153 | 적합(옛 코드 삭제 명시) | 실측 |
| 상수 발명 | 0(포락·D1·사다리) | 실측 |
| 회로 이름 조건 | 0(규칙 문언). 회로 이름은 기록·data·인용에만 | 실측 |
| 계획/이력 분리 | 대체로 적합. design 넘김 목록이 계획 밖(N-5) | 실측 |
| '원래 취지와 다름'·근본원칙 문언 변경 목록 | 누락: R5′ (2) K-1 (i) 삽입·R5′ (4) 합 행 촉발(N-4), W 없는 단계 포락 표지(N-6). DEC-104 (0)·R3·(3)(b)와 DEC-78은 history에 있음 | 실측 |

## 4. 사용자 확인 목록

1. **(새, N-1)** Q6-1 (A)의 'W'를 SPICE가 bin을 고르는 finger 폭으로 읽는가. 레이아웃 전 finger 폭 규칙과 [7, 100] µm bin·첫 bin 두 슬라이스를 어떻게 처리하는가(새 U 행 권고).
2. **U-126**: 기본안 = 원문(S 좌표 확장 없음).
3. **U-125**: 기본안 '대체됨'(원래 취지와 다름).
4. **U-129**: topology C_L 편집 주체·시점, CPG-1 bench(무부하 기준선).
5. **(N-3)** DEC-78 개정에 맞춘 oracle-portability OP-11 정의 정정을 이 판의 동반 승인으로 할지.
6. **(N-4)** R5′ (2) K-1 (i) 삽입·D-22 처리 방식의 근본원칙 문언 변경 승인(대안: R7 (가) 교집합 + 기록).

## 5. 재현 명령

```bash
set -e
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6382; R=/c/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12
E=$R/skills/analog-gmid-design/gmid_engine; P=$W/docs/01-plan/features/gain-budget-gmid-sizing.plan.md
git -C $W diff --stat 1fefcab1..a8a44ace; git -C $W diff --word-diff=plain 233dc336..a8a44ace | head
sed -n '304p' $P; sed -n '2228,2275p' $P; sed -n '2451,2455p' $P; sed -n '1974p;1987p;999p' $P
# N-1: PDK W bin·LUT 슬라이스·판정 넷리스트 finger
python -I -c "import re;t=open('C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice').read().lower();print(sorted({(float(a),float(b)) for a,b in re.findall(r'wmin\s*=\s*([0-9.e+-]+).*?wmax\s*=\s*([0-9.e+-]+)',t,re.S)}))"
ls /c/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/*__W*um_dc.npz
sed -n '1,23p' $E/lut/_helpers_bins.py
python -I -c "import zipfile;z=zipfile.ZipFile('C:/Users/HSLEE/Documents/Todoc/fpga/wt/_archive/cmp1_H_baseline_2026-10-28.zip');print(z.read('_cmp_pilot/H/netlists/two_stage_ota.H0r/pt0.sp').decode()[:1500])"
# N-2: specs.txt 범위·손실, case.json 범위, 기준선 커밋 spec
python -I -c "import zipfile;z=zipfile.ZipFile('C:/Users/HSLEE/Documents/Todoc/fpga/wt/_archive/cmp1_H_baseline_2026-10-28.zip');s=z.read('_cmp_pilot/H/judge/res/specs.txt').decode();print([l for l in s.splitlines() if l.startswith('===')]);print(z.read('_cmp_pilot/H/judge/specdump.py').decode());print(sorted({x.split('/')[3] for x in z.namelist() if x.startswith('_cmp_pilot/H/netlists/') and x.count('/')>3}))"
git -C $R show ebad06c1:skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.sizing_spec.json | head -c 300
# (d) O-140 D4
sed -n '967,977p' /c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md
# N-3: OP-11
sed -n '513p' $W/docs/01-plan/features/oracle-portability.plan.md
# N-7: bin_index 소비자
grep -rn 'bin_index(' $E --include=*.py | grep -v tests
# N-5: design 41 잔여 문장
grep -n 'A_max가 미상\|L ≥ √\|L = max(1, 2, 3\|matching 하한\|matching L 하한\|L 하한 활성' $W/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md
git -C $W status --short
```
