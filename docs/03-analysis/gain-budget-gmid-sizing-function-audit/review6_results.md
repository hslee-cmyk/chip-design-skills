

## [요약] 측정 불가 항목

| 항목 | 사유 |
|---|---|
| `supply_nets`를 topology.json에서 읽기 | **측정 불가** -- library 7개 topology.json 어디에도 `supply_nets` 키가 없다(DEC-60 "미구현", plan.md:244). DEC-60이 명시한 전환기 해석(`sizing_recipe.py:3882-3883` `_DEFAULT_RAIL_HI={vdd,VDD}` / `_DEFAULT_RAIL_LO={gnd,GND,vss,VSS}`)으로 대체 측정했고, 7개 회로 전부 상단·하단 레일이 정확히 1개씩 판정됐다(agnd 3레일 회로는 agnd에 DC 엣지가 없어 기둥 경로에 등장하지 않음 -- plan.md:255 예측과 일치). |
| MNA를 **실제 사이징 결과값**으로 구동 | **부분 측정 불가** -- `_full_circuit_devices()`가 `ctx.sized`(사이징 완료 컨텍스트)를 요구하고 그걸 만들려면 사실상 평가 1회를 돌려야 한다. 대신 topology에서 같은 스탬프 형식을 직접 조립하고 gm/gds만 합성값으로 채워 **실제 solver 함수**를 구동했다 -- 행렬 차원·스탬프 연산 수가 동일하므로 시간은 유효하고, 값은 무의미하다. 평가 1회 전체 비용은 [M7]에서 별도 실측. |
| `two_stage_ota` MNA를 파일럿과 같은 조건으로 | 측정됨(n=4). 다만 `two_stage_ota`에는 `passive_elements`가 없어 저항 스탬프가 0이다. |
| `_evaluate()` 1회를 `two_stage_ota`로 실측 | **미측정** -- 지시상 전수 스윕 금지라 파일럿(`probe_runtime_budget.py`)만 돌렸다. two_stage_ota는 자유 theta 2개·grid 49조합이라 필요하면 별도 실행 가능. |

## [요약] 핵심 수치 한눈에

| 항목 | 값 | 출처 |
|---|---|---|
| LUT 파일 크기 | 13,835,060 B (13.84 MB), 압축해제 13.83 MB | `sky130_nfet_pfet_lut_sample.npz` |
| LUT 격자 | L 12 x VGS 49 x VDS 49 x VS 5 = 144,060점/배열, 배열 12개(n/p x ID·GM·GDS·CGG·CGD·SID_1F) | [M1] |
| `_query()` 1점 4축보간 (캐시미스) | **16.9 us** | [M1] |
| `_query()` 캐시 히트 | **0.43 us** | [M1] |
| `_gm_id_curve()` (L,vds,vs)당 1회 | **968 us** | [M1b] |
| `_solve_vgs()` 곡선캐시 warm | **6.7 us** | [M1b] |
| `_sizing_bundle()` 소자 1개 전수격자(41x13x57=30,381점) | **1.22 s** | [M1b] |
| 파일럿 MNA 차원 | **n=31** (51 MOS + 4 저항 스탬프, net 37, 고정 6) | [M2] |
| 파일럿 MNA 조립 / solve / 전체 | **80.8 / 16.8 / 135.6 us** | [M2] |
| two_stage_ota MNA 차원 / 조립 / solve / 전체 | **n=4**, 7.6 / 3.9 / 21.2 us | [M2] |
| 파일럿 25점 복소 AC MNA solve | **339 us/평가** | [M8] |
| 파일럿 가지/기둥 | **32 / 62** | [M4] |
| two_stage_ota 가지/기둥 | **4 / 3** | [M4] |
| 파일럿 자유 theta(선언) / SLSQP 실자유변수 | **14 / 5~6** | [M5][M6] |
| two_stage_ota 자유 theta / 격자 조합 | **2 / 49** (7^2) | [M5] |
| 파일럿 평가 1회(현재 실측) | 성공 경로 **98.5 ms**, 12combo 평균 57.5 ms(실패 11건 편향) | [M7] |
| 파일럿 presolve 1회 | **12.0 s** | [M7] |
| 파일럿 L theta 수 | **5** (3 선언 + 2 `l_class` 파생) -> 앵커4 전수 1,024 combo = 58.9 s | [M7] |
**
- **_solve_vgs() 곡선캐시 warm, gm_id 스윕 30381회**: 총 0.2047 s -> **6.74 us/call**
- **_solve_vgs() 캐시 히트 재스윕 30381회**: 총 0.0825 s -> **2.714 us/call**
- 캐시 크기: _gm_id_curve_cache=533, _solve_vgs_cache=24922, _query_cache=0
- **_sizing_bundle() 전수 격자 30381점(콜드 캐시부터)**: 총 **1.220 s** -> 40.15 us/점
  -> 소자 1개당 L x VDS x gm_id 전수 스캔 1회의 실측 비용이 이 값이다.
[M1b done]


## [M2] 전체회로 소신호 MNA 조립/풀이 (2026-09-16 12:53:32)

| 회로 | MOS | 저항스탬프 | 총 스탬프 | 전체 net | 고정노드 | **MNA 차원 n** | 조립 us | solve us | 합계 us |
|---|---|---|---|---|---|---|---|---|---|
| `current_reuse_telescopic_ota` | 51 | 4 | 55 | 37 | 6 | **31** | 71.9 | 9.3 | 95.0 |
| `two_stage_ota` | 7 | 0 | 7 | 9 | 4 | **5** | 7.6 | 특이행렬(합성 gm/gds 탓) | ValueError: telescopic_class_ab MNA 특이행렬(노드 bias 고립  |
| `folded_cascode` | 13 | 0 | 13 | 14 | 2 | **12** | 26.0 | 특이행렬(합성 gm/gds 탓) | ValueError: telescopic_class_ab MNA 특이행렬(노드 bias3 고립 |
| `nmcnr_amplifier` | 15 | 0 | 15 | 17 | 2 | **15** | 25.8 | 특이행렬(합성 gm/gds 탓) | ValueError: telescopic_class_ab MNA 특이행렬(노드 VB1 고립 또 |
| `sf_pushpull_output_opamp` | 22 | 3 | 25 | 23 | 5 | **17** | 29.6 | 5.4 | 49.1 |
| `two_stage_ota_sf` | 9 | 0 | 9 | 10 | 5 | **5** | 8.6 | 특이행렬(합성 gm/gds 탓) | ValueError: telescopic_class_ab MNA 특이행렬(노드 bias 고립  |
| `pushpull_follower_buffer` | 6 | 0 | 6 | 9 | 4 | **4** | 5.5 | 특이행렬(합성 gm/gds 탓) | ValueError: telescopic_class_ab MNA 특이행렬(노드 VPB1 고립  |

- 측정 함수: `sizing_recipe._mna_solve_smallsignal()` (sizing_recipe.py:4970) -- **실제 엔진 함수**.
- gm/gds는 합성값(gm=100uS, gds=1uS) -- `ctx.sized`(사이징 결과)를 만들지 않고 구동하기 위함. 행렬 크기/스탬프 연산 수는 실제와 동일하므로 **시간**은 유효, **값**은 무의미.
- 반복 200회 평균. 고정노드 = 레일(`_DEFAULT_RAIL_HI/LO` 이름 집합) + `ports` 선언 넷 (`_full_circuit_response()`의 gnd+excite+also_fix 규칙 재현).

### 참고(프록시): 같은 차원의 dense numpy.linalg.solve
| n | dense solve us |
|---|---|
| 4 | 3.47 |
| 5 | 3.69 |
| 12 | 4.83 |
| 15 | 5.54 |
| 17 | 6.29 |
| 31 | 11.26 |
[M2 done]


## [M2] 전체회로 소신호 MNA 조립/풀이 (2026-09-16 12:53:50)

| 회로 | MOS | 저항스탬프 | 총 스탬프 | 전체 net | 고정노드 | **MNA 차원 n** | 조립 us | solve us | 합계 us |
|---|---|---|---|---|---|---|---|---|---|
| `current_reuse_telescopic_ota` | 51 | 4 | 55 | 37 | 6 | **31** | 80.8 | 16.8 | 135.6 |
| `two_stage_ota` | 7 | 0 | 7 | 9 | 5 | **4** | 7.6 | 3.9 | 21.2 |
| `folded_cascode` | 13 | 0 | 13 | 14 | 5 | **9** | 15.3 | 4.2 | 33.5 |
| `nmcnr_amplifier` | 15 | 0 | 15 | 17 | 9 | **8** | 14.2 | 3.8 | 39.7 |
| `sf_pushpull_output_opamp` | 22 | 3 | 25 | 23 | 6 | **17** | 28.8 | 5.2 | 51.1 |
| `two_stage_ota_sf` | 9 | 0 | 9 | 10 | 6 | **4** | 8.2 | 3.9 | 22.1 |
| `pushpull_follower_buffer` | 6 | 0 | 6 | 9 | 7 | **2** | 4.8 | 3.6 | 18.5 |

- 측정 함수: `sizing_recipe._mna_solve_smallsignal()` (sizing_recipe.py:4970) -- **실제 엔진 함수**.
- gm/gds는 합성값(gm=100uS, gds=1uS) -- `ctx.sized`(사이징 결과)를 만들지 않고 구동하기 위함. 행렬 크기/스탬프 연산 수는 실제와 동일하므로 **시간**은 유효, **값**은 무의미.
- 반복 200회 평균. 고정노드 = 레일(`_DEFAULT_RAIL_HI/LO` 이름 집합) + `ports` 선언 넷 (`_full_circuit_response()`의 gnd+excite+also_fix 규칙 재현).

### 참고(프록시): 같은 차원의 dense numpy.linalg.solve
| n | dense solve us |
|---|---|
| 2 | 3.35 |
| 4 | 3.53 |
| 8 | 3.81 |
| 9 | 3.84 |
| 17 | 5.21 |
| 31 | 9.19 |
[M2 done]

> **주**: 위 [M2] 표는 두 번 실행됐다. 첫 실행은 gate-only net을 고정하지 않아 5개 회로가 특이행렬로 실패했고, 두 번째(마지막) 표가 `_full_circuit_response()`의 `also_fix` 규칙(gate로만 쓰이는 net 0V 고정)을 반영한 **정본**이다.


## [M3] 회로 규모 집계 (2026-09-16 12:54:53)

| 회로 | MOS 총 | nmos | pmos | net 총 | 레일 net | 신호 net | 이상원 | 저항 | 커패시터 | theta 총 | theta 자유 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `current_reuse_telescopic_ota` | 51 | 24 | 27 | 37 | 2 ['gnd', 'vdd'] | 35 | 1 | 4 | 8 | 22 | **14** |
| `folded_cascode` | 13 | 6 | 7 | 14 | 2 ['gnd', 'vdd'] | 12 | 1 | 0 | 0 | 5 | **1** |
| `nmcnr_amplifier` | 15 | 7 | 8 | 17 | 2 ['vdd', 'vss'] | 15 | 0 | 0 | 0 | 11 | **0** |
| `pushpull_follower_buffer` | 6 | 3 | 3 | 9 | 2 ['vdd', 'vss'] | 7 | 0 | 0 | 1 | 0 | **0** |
| `sf_pushpull_output_opamp` | 22 | 11 | 11 | 23 | 2 ['vdd', 'vss'] | 21 | 1 | 3 | 2 | 0 | **0** |
| `two_stage_ota` | 7 | 4 | 3 | 9 | 2 ['gnd', 'vdd'] | 7 | 0 | 0 | 0 | 3 | **2** |
| `two_stage_ota_sf` | 9 | 6 | 3 | 10 | 2 ['gnd', 'vdd'] | 8 | 0 | 0 | 2 | 0 | **0** |

- `theta 자유` = `sizing_roles.theta[i].bounds`의 lo != hi 인 항목 수 (lo==hi는 고정값).
- 이상원 = `ideal_sources`(전부 `kind=current_source`), 저항/커패시터 = `passive_elements`.


## [M4] DC 전도 그래프: 가지(branch)/기둥(column) 수 -- 계획 DEC-71 정의

### supply_nets 선언 상태
- `current_reuse_telescopic_ota`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용
- `folded_cascode`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용
- `nmcnr_amplifier`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용
- `pushpull_follower_buffer`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용
- `sf_pushpull_output_opamp`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용
- `two_stage_ota`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용
- `two_stage_ota_sf`: `supply_nets` **없음** -> DEC-60 전환기 해석(이름 집합) 사용

| 회로 | DC 엣지(잎제거전) | 잎제거 | DC 엣지 | 하단레일 | 상단레일 | 분기노드(차수>=3, 레일제외) | **가지 수** | **기둥 수** |
|---|---|---|---|---|---|---|---|---|
| `current_reuse_telescopic_ota` | 56 | 2 | 54 | ['gnd'] | ['vdd'] | 9 | **32** | **62** |
| `folded_cascode` | 14 | 0 | 14 | ['gnd'] | ['vdd'] | 3 | **8** | **7** |
| `nmcnr_amplifier` | 15 | 0 | 15 | ['vss'] | ['vdd'] | 3 | **10** | **9** |
| `pushpull_follower_buffer` | 6 | 0 | 6 | ['vss'] | ['vdd'] | 0 | **3** | **3** |
| `sf_pushpull_output_opamp` | 26 | 0 | 26 | ['vss'] | ['vdd'] | 1 | **9** | **8** |
| `two_stage_ota` | 7 | 0 | 7 | ['gnd'] | ['vdd'] | 1 | **4** | **3** |
| `two_stage_ota_sf` | 9 | 0 | 9 | ['gnd'] | ['vdd'] | 1 | **5** | **4** |

### 회로별 상세

**`current_reuse_telescopic_ota`** -- 가지 32, 기둥 62
- 분기노드(레일 제외): ['Ncmfb_tail', 'Vg15', 'Vg25', 'Vom', 'Vom1', 'Vop', 'Vop1', 'Vx', 'Vy']
- 잎 가지치기로 제거된 DC 엣지: ['Rz1', 'Rz2']
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `Ncmfb_tail` -- `vdd` : ['M37a', 'M36a']
    - `Ncmfb_tail` -- `vdd` : ['M37b', 'M36b']
    - `Ncmfb_tail` -- `gnd` : ['M38']
    - `Vg15` -- `vdd` : ['M8']
    - `Vg15` -- `Vop1` : ['M9a']
    - `Vg15` -- `Vop1` : ['M9b']
    - `Vg25` -- `Vom1` : ['M18a']
    - `Vg25` -- `Vom1` : ['M18b']
    - `Vg25` -- `vdd` : ['M17']
    - `Vom` -- `vdd` : ['M15']
    - `Vom` -- `gnd` : ['M16']
    - `Vom` -- `Vop` : ['R1', 'R2']
    - `Vom1` -- `Vx` : ['M2a', 'M1a']
    - `Vom1` -- `Vy` : ['M3a', 'M4a']
    - `Vom1` -- `gnd` : ['M19']
    - `Vop` -- `vdd` : ['M25']
    - `Vop` -- `gnd` : ['M26']
    - `Vop1` -- `Vx` : ['M2b', 'M1b']
    - `Vop1` -- `Vy` : ['M3b', 'M4b']
    - `Vop1` -- `gnd` : ['M10']
    - `Vx` -- `vdd` : ['M6']
    - `Vx` -- `vdd` : ['M7']
    - `Vx` -- `gnd` : ['M58', 'M57', 'M68']
    - `Vy` -- `gnd` : ['M5']
    - `Vy` -- `vdd` : ['M63', 'M64', 'M61']
    - `gnd` -- `vdd` : ['M12', 'M11b', 'M11a']
    - `gnd` -- `vdd` : ['M14b', 'M14a', 'M13']
    - `gnd` -- `vdd` : ['M21', 'M20b', 'M20a']
    - `gnd` -- `vdd` : ['M24b', 'M23a', 'M22']
    - `gnd` -- `vdd` : ['M66', 'M60']
    - `gnd` -- `vdd` : ['M40', 'M39']
    - `gnd` -- `vdd` : ['Iref', 'M18_bg']  [이상원 포함]

**`folded_cascode`** -- 가지 8, 기둥 7
- 분기노드(레일 제외): ['X', 'Y', 'tail']
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `X` -- `vdd` : ['M3']
    - `X` -- `gnd` : ['M6', 'M8', 'M10']
    - `X` -- `tail` : ['M1']
    - `Y` -- `vdd` : ['M4']
    - `Y` -- `gnd` : ['M5', 'M7', 'M9']
    - `Y` -- `tail` : ['M2']
    - `gnd` -- `tail` : ['M11']
    - `gnd` -- `vdd` : ['MN', 'Ibg', 'MP']  [이상원 포함]

**`nmcnr_amplifier`** -- 가지 10, 기둥 9
- 분기노드(레일 제외): ['NodeF1', 'NodeF2', 'NodeTail']
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `NodeF1` -- `NodeTail` : ['M102']
    - `NodeF1` -- `vss` : ['M104']
    - `NodeF1` -- `vdd` : ['M106', 'M108']
    - `NodeF2` -- `NodeTail` : ['M103']
    - `NodeF2` -- `vss` : ['M105']
    - `NodeF2` -- `vdd` : ['M107', 'M109']
    - `NodeTail` -- `vdd` : ['M101']
    - `vdd` -- `vss` : ['M201', 'M203']
    - `vdd` -- `vss` : ['M202', 'M204']
    - `vdd` -- `vss` : ['M302', 'M301']

**`pushpull_follower_buffer`** -- 가지 3, 기둥 3
- 분기노드(레일 제외): (없음)
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `vdd` -- `vss` : ['M5', 'M3']
    - `vdd` -- `vss` : ['M4', 'M6']
    - `vdd` -- `vss` : ['M1', 'M2']

**`sf_pushpull_output_opamp`** -- 가지 9, 기둥 8
- 분기노드(레일 제외): ['TAIL']
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `TAIL` -- `vdd` : ['M1', 'R1a', 'M5', 'M6']
    - `TAIL` -- `vdd` : ['M2', 'R1b', 'M7', 'M8']
    - `TAIL` -- `vss` : ['M3']
    - `vdd` -- `vss` : ['M11', 'M12', 'R1c', 'M13', 'M14']
    - `vdd` -- `vss` : ['M9', 'M10', 'M15', 'M16']
    - `vdd` -- `vss` : ['M17', 'M18']
    - `vdd` -- `vss` : ['M19', 'M20']
    - `vdd` -- `vss` : ['M22', 'M21']
    - `vdd` -- `vss` : ['IBias', 'M4']  [이상원 포함]

**`two_stage_ota`** -- 가지 4, 기둥 3
- 분기노드(레일 제외): ['CS']
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `CS` -- `vdd` : ['M1', 'M3']
    - `CS` -- `vdd` : ['M2', 'M4']
    - `CS` -- `gnd` : ['M5']
    - `gnd` -- `vdd` : ['M7', 'M6']

**`two_stage_ota_sf`** -- 가지 5, 기둥 4
- 분기노드(레일 제외): ['CS']
- 가지 목록(끝점A -- 끝점B : 직렬 소자):
    - `CS` -- `vdd` : ['M1', 'M3']
    - `CS` -- `vdd` : ['M2', 'M4']
    - `CS` -- `gnd` : ['M5']
    - `gnd` -- `vdd` : ['M7', 'M6']
    - `gnd` -- `vdd` : ['M9', 'M8']

- 기둥 열거는 가지 그래프 위 단순 경로 DFS(노드 재방문 금지, 가지 재사용 금지), 상한 200,000.
- `supply_nets` 미선언이므로 레일은 전부 전환기 해석(`vdd`/`VDD` = 상단, `gnd`/`GND`/`vss`/`VSS` = 하단).
[M3+M4 done]


## [M5] 탐색 공간 크기: theta 차원 / 격자 해상도 / 표본 수 (2026-09-16 12:55:39)

### SPECS 레지스트리 (workspaces/run_harness.py:308)

| circuit_key | topology_file | search_method | grid_points_per_theta | slsqp_kwargs | report_dir |
|---|---|---|---|---|---|
| `two_stage_ota` | two_stage_ota.topology.json | grid (기본값) | 7 | - | two-stage-ota-report |
| `current_reuse_telescopic_ota` | current_reuse_telescopic_ota.topology.json | slsqp | 2 | {'n_starts': 3, 'maxiter': 25} | current-reuse-telescopic-ota-report |
| `folded_cascode` | folded_cascode.topology.json | grid (기본값) | 400 | - | folded-cascode-report |
| `nmcnr_amplifier` | nmcnr_amplifier.topology.json | grid (기본값) | 5 | - | nmcnr-amplifier-report |

### theta 차원과 격자 조합 수

| circuit_key | theta 총 | 고정(lo==hi) | **자유 theta N** | gpt | **격자 조합 수** | L후보 | VDS후보 | gm_id격자 | 소자당 L x VDS x gm_id |
|---|---|---|---|---|---|---|---|---|---|
| `two_stage_ota` | 3 | 1 | **2** | 7 | **49** = 7^2 | 41 | 13 | 57 | 30381 |
| `current_reuse_telescopic_ota` | 22 | 8 | **14** | 2 | **16,384** = 2^14 | 41 | 13 | 57 | 30381 |
| `folded_cascode` | 5 | 4 | **1** | 400 | **400** = 400^1 | 41 | 13 | 57 | 30381 |
| `nmcnr_amplifier` | 11 | 11 | **0** | 5 | **1** = 5^0 | 41 | 13 | 57 | 30381 |

### 자유 theta 목록 (feeds.type = 결정변수 성격)

**`two_stage_ota`** (자유 2 / 총 3)
- 고정 `kcl_tail_M5` type=A bounds=[1, 1]
- **자유** `L_mirror_M3` type=metric_stage_budget bounds=[1.5e-07, 4e-06]
- **자유** `L_mirror_M5` type=metric_stage_budget bounds=[1.5e-07, 4e-06]

**`current_reuse_telescopic_ota`** (자유 14 / 총 22)


## [M5] 탐색 공간 크기: theta 차원 / 격자 해상도 / 표본 수 (2026-09-16 12:55:44)

### SPECS 레지스트리 (workspaces/run_harness.py:308)

| circuit_key | topology_file | search_method | grid_points_per_theta | slsqp_kwargs | report_dir |
|---|---|---|---|---|---|
| `two_stage_ota` | two_stage_ota.topology.json | grid (기본값) | 7 | - | two-stage-ota-report |
| `current_reuse_telescopic_ota` | current_reuse_telescopic_ota.topology.json | slsqp | 2 | {'n_starts': 3, 'maxiter': 25} | current-reuse-telescopic-ota-report |
| `folded_cascode` | folded_cascode.topology.json | grid (기본값) | 400 | - | folded-cascode-report |
| `nmcnr_amplifier` | nmcnr_amplifier.topology.json | grid (기본값) | 5 | - | nmcnr-amplifier-report |

### theta 차원과 격자 조합 수

| circuit_key | theta 총 | 고정(lo==hi) | **자유 theta N** | gpt | **격자 조합 수** | L후보 | VDS후보 | gm_id격자 | 소자당 L x VDS x gm_id |
|---|---|---|---|---|---|---|---|---|---|
| `two_stage_ota` | 3 | 1 | **2** | 7 | **49** = 7^2 | 41 | 13 | 57 | 30381 |
| `current_reuse_telescopic_ota` | 22 | 8 | **14** | 2 | **16,384** = 2^14 | 41 | 13 | 57 | 30381 |
| `folded_cascode` | 5 | 4 | **1** | 400 | **400** = 400^1 | 41 | 13 | 57 | 30381 |
| `nmcnr_amplifier` | 11 | 11 | **0** | 5 | **1** = 5^0 | 41 | 13 | 57 | 30381 |

### 자유 theta 목록 (feeds.type = 결정변수 성격)

**`two_stage_ota`** (자유 2 / 총 3)
- 고정 `kcl_tail_M5` type=A bounds=[1, 1]
- **자유** `L_mirror_M3` type=metric_stage_budget bounds=[1.5e-07, 4e-06]
- **자유** `L_mirror_M5` type=metric_stage_budget bounds=[1.5e-07, 4e-06]

**`current_reuse_telescopic_ota`** (자유 14 / 총 22)
- **자유** `f_slew` type='settling_split' bounds=[0.1, 0.5]
- **자유** `L_cascode` type=metric_stage_budget bounds=[1.5e-07, 1e-06]
- **자유** `L_stage2out_p` type=metric_stage_budget bounds=[1.5e-07, 1e-06]
- **자유** `L_stage2out_n` type=metric_stage_budget bounds=[1.5e-07, 1e-06]
- **자유** `K_replica` type=C bounds=[0.05, 0.2]
- **자유** `N_cmfb_bw` type=B bounds=[2, 5]
- 고정 `N_cmfb_bw_mirror` type=A bounds=[1, 1]
- **자유** `r_cmfb_vocdes` type=A bounds=[0.02, 0.2]
- **자유** `r_biasgen` type=A bounds=[0.02, 0.15]
- **자유** `r_tail_M6` type=A bounds=[0.5, 0.9]
- **자유** `r_tail_M7` type=A bounds=[0.1, 0.4]
- **자유** `r_classab_battery` type=A bounds=[0.1, 0.3]
- **자유** `r_classab_diode_src` type=A bounds=[0.02, 0.15]
- 고정 `kcl_tail_M5` type=A bounds=[1, 1]
- 고정 `kcl_tail_M38` type=A bounds=[1, 1]
- **자유** `r_diode_M11a` type=A bounds=[0.02, 0.15]
- **자유** `r_bg_vbias2` type=A bounds=[0.02, 0.15]
- 고정 `kcl_sink_M10` type=A_signed bounds=[1, 1]
- 고정 `kcl_sink_M19` type=A_signed bounds=[1, 1]
- 고정 `kcl_battery_M9b` type=A_signed bounds=[1, 1]
- 고정 `mirror_M18a` type=C bounds=[1, 1]
- 고정 `kcl_battery_M18b` type=A_signed bounds=[1, 1]

**`folded_cascode`** (자유 1 / 총 5)
- **자유** `Ibg` type=const bounds=[5e-07, 5e-05]
- 고정 `r_split_M1_M2` type=A bounds=[0.5, 0.5]
- 고정 `r_mirror_M3_M4` type=A bounds=[1.5, 1.5]
- 고정 `kcl_fold_M6` type=A_signed bounds=[1, 1]
- 고정 `kcl_fold_M5` type=A_signed bounds=[1, 1]

**`nmcnr_amplifier`** (자유 0 / 총 11)
- 고정 `Ibg_tail` type=const bounds=[1e-05, 1e-05]
- 고정 `r_split_M102_M103` type=A bounds=[0.5, 0.5]
- 고정 `r_fold_M108_M109` type=A bounds=[0.5, 0.5]
- 고정 `kcl_M104` type=A_signed bounds=[1, 1]
- 고정 `kcl_M105` type=A_signed bounds=[1, 1]
- 고정 `r_series_M106` type=A bounds=[1, 1]
- 고정 `r_series_M107` type=A bounds=[1, 1]
- 고정 `kcl_M203` type=A_signed bounds=[1, 1]
- 고정 `kcl_M302` type=A_signed bounds=[1, 1]
- 고정 `r_mirror_M204_M203` type=A bounds=[1, 1]
- 고정 `kcl_M202` type=A_signed bounds=[1, 1]

### 표본 수 공식
- **grid** (sizing_recipe.py:9722-9770): `prod_i (1 if lo_i==hi_i else grid_points_per_theta)` 조합, 각 조합마다 `_evaluate(theta)` 1회. 고정 theta는 1점으로 접힌다(sizing_recipe.py:9738).
- **slsqp** (sizing_recipe.py:11343 `_optimize_theta_slsqp`): 기본 `n_starts=6, maxiter=80`; 파일럿은 `SPECS`가 `n_starts=3, maxiter=25`로 덮어쓴다(run_harness.py:331). SciPy SLSQP는 반복마다 목적·제약의 유한차분 기울기를 쓰므로 반복 1회 평가 수 ~ (N_free+1). 따라서 대략 `n_starts x maxiter x (N_free+1)` = 평가 횟수 상한.
    - `current_reuse_telescopic_ota`: 3 x 25 x (14+1) = **1,125 평가**(상한 추정)
[M5 done]


## [M6] 저장소에 기록된 기존 타이밍 증거 (2026-09-16 12:57:25)

| file:line | 발췌(요약) |
|---|---|
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:573` | / `presolve_warm_start()` / **16.5 s** / ★ 1회성인데 크다 — L_combo 루프 **안**에 들어가면 안 된다 / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:574` | / **전체 평가 1회**(51소자 사이징+헤드룸+전 metric) / **274.5 ms** / ← **L_combo 단위 비용의 진짜 값** / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:575` | / `find_optimal_sizing()` 1회(stage 하나, L 고정) / 3.15 ms / 참고 — 이걸로 예산을 세면 **틀린다**(아래) / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:580` | > 6.3 ms지만, **B2에서 확인했듯 전역 게이트는 51소자 전부가 사이징돼야 돈다**. 따라서 combo 단위 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:581` | > 비용은 stage 사이징이 아니라 **전체 평가 1회(274.5 ms)**다. 약 44배 차이다. |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:587` | / **knee 창 3앵커**(v4.7 기본) / 3³ = **27** / **7.4 s** / **74 s (1.2분)** / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:588` | / bounds 내 LUT 앵커 4개 / 4³ = 64 / 17.6 s / 175.7 s (2.9분) / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:591` | / densify 41점 / 68,921 / **5.3시간** / 53시간 / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:596` | ~~bounds 내 앵커 전수(2.9분)~~보다 싸면서 면적 제약이 걸린 정상 조건에서 **전수와 동일한 답**을 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:598` | 2. **`dense_candidates()` densify는 기본 금지**한다. 5.3시간은 설계 반복 도구로 쓸 수 없다. |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:601` | 3. **`presolve_warm_start()`(16.5 s)는 L_combo 루프 **밖**에서 1회만** 호출한다. 루프 안에 들어가면 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:602` | 64 combo × 16.5 s = 17.6분이 여기서만 추가된다. |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:608` | **DoD 측정 항목 신설**: 파일럿 1회 전체 실행 wall-clock **≤ 5분**(기본 정책 기준). 초과하면 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:650` | **비용**: 27 combo × 274.5 ms = **7.4 s**(전수 343의 12.7배 절감), 중첩(레이아웃 5회 × VDS 2회) |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:2435` | **평가 1회 1,325ms → 72.9ms(18배)**, 탐색 1,465초 → 134초. 이 원칙은 메모리 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3290` | - [ ] **★ (v4.6, B4) 파일럿 1회 전체 실행 wall-clock ≤ 5분** — 기본 L 정책(bounds 내 LUT 앵커 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3291` | 전수, 4³=64 combo) 기준 실측 예상 2.9분. 초과하면 곱셈 구조에 예상 못 한 항이 들어온 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3292` | 것이므로 그 자리를 찾아 보고한다(예: `presolve_warm_start()` 16.5s가 루프 안으로 들어감) |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3356` | / B4 / ~~실행시간 예산 항목이 계획에 없다~~ → **2026-09-08 해소(v4.6)**. 직접 측정: **전체 평가 1회 274.5 ms**가 L_combo 단위 비용이다(stage 사이징 3.15ms로 세면 44배 틀린다 — 전역 게이트가 51소자 전부를 요구하므로). L 자유도 3개, 기본 정책(bounds 내 앵커 4개, |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3456` | / B4 / 실행시간 예산 항목 없음 / 해소 -- DoD에 wall-clock ≤ 5분(현재 평가 1회 72.9ms) / P:349-351; 커밋 199b5c9 / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3520` | / **SUCCESS** / Phase별 DoD(§4) -- 최종: 4개 회로에서 stage 분할이 선언과 일치, gain 제약이 전체회로 gain으로 판정되고 분해와의 괴리가 기록됨, 봉인 게이트(KVL/KCL/노드충돌/버전) 위반 0, C1~C10 강제 test PASS, SPICE 교차검증 허용오차 내, 파일럿 wall-clock ≤ |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3788` | / A53 / D4 전역 샘플 수는 wall-clock ≤ 5분 안에서 실측으로 계산(5분=B4 DoD) / 2026-09-14 / plan:1020, plan:349-351 / G9 / **유효·미구현** / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3872` | / **7b** / `gain_budget_db`가 출력, 3층 할당 결과를 **다른 모델** 전수탐색과 대조, `sizing_spec.json` 유도 필드 `status`/증거, 파일럿 wall-clock ≤ 5분(B4) / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:3894` | / 전체회로 MNA를 매 평가 여러 번 -- 5분 초과 / `build_ac_network` 1회 조립·S2 블록 memo, wall-clock DoD(§4.1 7b) / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:4481` | * 캐시는 전부 **사후에 하나씩 덧댄 것**이다(세션47에서 손으로 세 곳을 고쳐 평가 1,325→72.9ms). |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:4549` | * **시작점**: S3 아카이브의 실현가능 상위 k개(지문 일치) + 저비용 준난수 전역 샘플(Sobol/LHS, 1,000점 × 72ms ≈ 72초)로 조각 지도를 그린 뒤 **서로 다른 분지**에서 SLSQP. |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:4581` | / D4 / 전역 샘플링 예산 / §10.3 B4의 wall-clock ≤ 5분 **안에서** 평가 1회 실측 시간으로 샘플 수를 계산 / 사용자가 이미 정한 제약 / |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:5038` | 각 Phase DoD: 4개 회로 측정(필요 없는 회로에서 무동작 증명), test-author의 거부 케이스, 평가 오버헤드 실측, wall-clock ≤ 5분(B4). |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:5069` | / **4.6** / 2026-09-08 / **B4 해소 — 실행시간 예산 신설**. v4.5까지 계획에 예산 항목 자체가 없어 §7.6 L_combo 전수 스캔 × §7.9 중첩 루프의 곱을 아무도 세지 않았다. 직접 측정: `_build_theta_evaluator()` 69ms(1회성), **`presolve_warm_start() |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:5070` | / **4.7** / 2026-09-08 / **L 탐색을 knee 창 + 경계 검사로 확정 + 단위 불일치(A12) 발견**. "LUT 전체를 훑지 말고 knee 근방만 최소 탐색해야 하지 않나"라는 지적을 받아 LUT 전 앵커 7³=343 combo를 전수로 돌렸다. **면적 제약이 걸리느냐에 따라 답이 뒤집힌다**: 무제약/≤500µ |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:5101` | / **4.38** / 2026-09-10 / **층3 착지 + 중복계산 전수검사**. ① `synthesize_l_class_thetas()`가 동치류 공통 L을 **theta로 파생**한다(손선언 없음, 이름도 파생 -- 사용자 지시 "특정 이름으로 하지마"). feed 타입 `l_class` 신설(L만 확정, 레지스트리 확장 계약대로 |
| `docs/01-plan/features/gain-budget-gmid-sizing.history.md:5123` | / **5.9** / 2026-09-15 / **일반성 점검 반영**(사용자 승인 범위: 개선안 A 정의 일반화, B 지원 범위 명시와 미검증 분기 정지 게이트, C 측정 대상 확대. 독립 감사 `generality_audit.md` S-01~S-14·M-01~M-07·H-01~H-20 판정표 `v59_disposition.md`). A: |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:189` | / DEC-04 / **(2026-09-14 재정의, 사용자 "난 강제하고 싶지 않아")** 블록 안 소자(input·cascode·load·tail)의 gm_id·L은 S1 등식 관계(매칭, L 동치류, 공유 VGS)로 묶인 것을 제외하면 소자마다 **독립 결정변수**다. 함께 정하라는 규칙을 두지 않는다. 소자 사이의 결합은 블록 ga |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:218` | / DEC-34 (D4) / 전역 샘플 수는 사람 선언 `wall_clock_budget_s`(7b 전에는 `SPECS[circuit]` 항목, 7b부터 `sizing_spec.json` human. 기본안은 파일럿 선언값 300 s(5분)를 모든 사이징 대상 회로에 같게 적용하고 사용자가 회로별로 바꿀 수 있다, 확정 U-26) 안에서  |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:396` | * **전역 샘플 수(DEC-34)**: `N = floor((wall_clock_budget_s − T_fixed) / t_eval)`(`wall_clock_budget_s`는 회로별 선언값, DEC-34). `T_fixed` = 같은 실행에서 샘플을 뺀 단계(층 0 기둥 조립 presolve(DEC-71), GB0~GB5, DP, 좌표 |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:647` | / `human` / `objective`, `constraints[]{metric, op, value, source}`(`metric`은 실제 metric 이름, 예 `gain_ss_db`·`rout_ss_ohm`·`pm_ss_deg`), `ports{<넷>: {role}}`(`direction` 없음, role에서 유도), `eleme |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:869` | / 6b / GB7: W 티어, 순환 블록, 봉인, SC-a~SC-e, 평가 커널 계산 블록과 S2 memo, NFR-4 결정론, DF-25(VDsat 유도 규칙과 포화 하한 교체), 봉인 항목 7(포화 여유)·8(`kvl_branch` 등식), S2 `dc`/`ss`/`ls` 분리, CD source 노드 W2, 평가 커널 계산 블록 분 |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:889` | / 7b / `gain_budget_db` 출력, 3층 할당이 다른 모델 전수탐색과 격자 분해능 안 일치, `sizing_spec.json` 이관 기존 4개 회로 equivalence, derived 필드마다 status·evidence·rule_hash, `driving_spec`이 있는 회로에서 극점 노드별 방향별 최대 전류 ≥ 슬루율 |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:890` | / 7c / SPICE 비교가 N3.8 허용오차 안, 같은 지문 재실행에서 아카이브 적중 > 0이고 θ* 목적값이 첫 실행 이하, IC1~IC11 전원 PASS, wall-clock ≤ 선언 `wall_clock_budget_s`(파일럿 300 s) / |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:896` | * 성능: Phase 4부터 매 Phase 보고 -- 조건 = 정본 spec, `SPECS[circuit]["slsqp_kwargs"]`, 파일럿 탐색 1회의 전체 wall-clock과 평가 시간 중앙값, 기계 정보. wall-clock 예산 게이트(DEC-34)는 7b·7c. |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:961` | / U-26 / 레일·예산 선언 확정: (a) 기존 4개 회로의 `supply_nets`·`supplies_v{넷: 전압}`(nmcnr은 **확정(2026-09-15 사용자 "1.8로 고쳐", "+-0.9로 고치고")**: sky130 재설계 전원 `supplies_v{vdd: 0.9, vss: −0.9}`. 옛 `vdd` 2.0은 논문  |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:968` | / U-33 / 층 0 기둥 조립 presolve(DEC-71)를 탐색의 기본 경로로 둘지 / 실측 후 결정. 사이징 대상 회로 전부에서 콜드 스타트(층 0 없이 선언 x0·전역 샘플에서 출발)와 층 0 조립점 출발을 같은 spec·탐색 인자로 돌려 비교한다: (i) 평가 수 (ii) 최종 목적값 (iii) 활성 제약 여유(NFR-5, 제 |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:984` | / 전체회로 MNA 반복으로 wall-clock 예산 초과 / `build_ac_network` 1회 조립, 봉인 스냅샷당 전역 metric 1회, S2 memo / |
| `docs/01-plan/features/gain-budget-gmid-sizing.plan.md:1012` | / `7b-compensation-allocation` / `sizing_spec.json` v5 스키마·로더·이관·topology.json 필드 제거 절차, GB5 규칙(단일단 U-12, 3단, class-AB J3), 내층 DP 상태·bin 해상도, 중층 좌표강하 종료, 외층 인자, 면적·Pareto(U-13), U-14, `value |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_generality_audit.md:82` | / M-03 / 208(DEC-34), 371, 800, 801 / 전역 샘플 수 식의 `300 s`, "파일럿 wall-clock 5분" / M / 시간 예산이 파일럿 기준 상수로 박혀 모든 회로 샘플 수와 S2 LRU 상한(365)에 들어감 / 소자 수가 크게 다른 회로 / "`wall_clock_budget_s`를 `sizing_sp |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_generality_audit.md:105` | / H-14 / 422, 800, 801, 859 / 검증 회로 선택 / H / 3층 할당 대조 "파일럿과 한 개 회로", 그룹 좌표강하·wall-clock은 파일럿만 / 파일럿 외 / DEC-47(221)대로 4개 회로 전부 + 규칙 분기 발동 회로로 확대(4절) / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_generality_audit.md:128` | / E-12 / 179 / DEC-04 근거(파일럿 미러 동치류 8·11소자, 6.5초 대 5.4초, 면적 3배) / E / 결정 근거 / **높음**: "블록 단일 L 불채택"이 파일럿 한 회로·tt 한 코너 측정으로 확정 / 4개 회로 재측정 전까지 "파일럿 근거"로 상태 표시 / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_generality_audit.md:190` | 3. **여러 검증이 4개보다 적은 회로로 되어 있다.** 3층 할당 대조 "파일럿과 한 개 회로"(422), 그룹 좌표강하·wall-clock 파일럿만(800-801), 결합 잔차 데이터 파일럿만(408), 레이아웃 비교 파일럿만(859), DEC-04 근거 파일럿만(179). |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_disposition.md:28` | / M-03 / 반영 / 211(DEC-34), 378, 619(N3.15), 813, 814, 820, 891 / `wall_clock_budget_s` 회로별 선언, 파일럿 300 s는 선언값 / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_disposition.md:97` | / 9 / 중간 / 기존 3개 회로 `wall_clock_budget_s` 선언 U·착수 조건 없음 / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_reverify.md:40` | / 9 / **높음(상향)** / 6b LRU 상한(372)과 6c DOF 표본 수(420)가 N을 쓰고, N은 회로별 `wall_clock_budget_s` 선언이 있어야 계산된다(211, 378). 선언값은 파일럿뿐이다. 6b DoD "봉인 위반 0(사이징 대상 회로)"(810)는 folded·two_stage·nmcnr에서 LRU 상 |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_reverify.md:49` | / N1 / 순환 / 막음 / 304, 236, 115, 419, 811~814 / 루프 분류 (iii) "수동소자를 거쳐 **여기 포트 넷으로 돌아오는** 전역 되먹임"은 이제 `기록만`이라 ratify와 무관하게 항상 정지한다(304, 236). 파일럿에는 `Cf1 [Vom, Vip]`, `Cf2 [Vop, Vim]`가 있어 Vip → |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_reverify.md:64` | **커밋 불가.** N1은 plan 문장과 파일럿 실측 넷(Cf1/Cf2가 여기 포트 Vip/Vim으로 귀환)만으로 6c~7c의 파일럿 완료 조건을 원천 봉쇄한다. N2(J3에 따라 파일럿 봉쇄), N3(스펙 미선언 회로의 레일 넷 미정의), 이월 #9(기존 3개 회로 `wall_clock_budget_s` 착수 조건 없음 → 6b des |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_reverify2.md:32` | / 이월 #9 높음(`wall_clock_budget_s`) / 해소 / 211 DEC-34 기본안 300 s 공통, 878 U-26(c), 795 6b 착수 조건 / 없음 / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review4_v59_verify.md:34` | / 9 / 누락 / 중간 / 211, 372, 378, 420, 793 / 전역 샘플 수 N은 회로별 선언 `wall_clock_budget_s`가 입력이고, 6b LRU 상한(372)과 6c DOF 표본 수(420)가 N을 쓴다(378). 선언값이 있는 회로는 파일럿(300 s)뿐이다(211). 기존 3개 회로(folded, two_st |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review5_schema_unification.md:89` | - `human{objective, constraints[]{metric, op, value, source}, ports, value_amp, compensation_targets{CL, GBW, PM}, driving_spec, wall_clock_budget_s, supplies, node_voltage_targets, gain_bud |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review5_schema_unification.md:96` | - `structure.json` (PLAN:326, 794), `wall_clock_budget_s` (PLAN:211, 378), `driving_spec` (PLAN:233, 439), `value_from_constraint` (PLAN:198, 599). |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review5_v511_verify.md:35` | / M2 / 순환 / 중간 / 254(6), 395, 389, 446, 888 / (c) 비지배 점 수 상한을 "DEC-34 예산 식"에서 계산한다고 했는데, 그 식의 `T_fixed`에 층 0 자신의 실행 시간이 들어간다(395). 상한을 정하려면 층 0을 이미 돌린 시간이 필요한 순환이다. 또 S2 LRU 상한(389)은 샘플 수와 S |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review_B_design_7_5_7_9.md:20` | / §7.6-4 / (B2) metric **T1/T2/T3 3티어 게이트** + `check_global_gates()` / stage 사이징 중엔 T1/T2만, 전 소자 후 T3 / **변형** -- 수동 분류표가 아니라 **유도 분류**(§Q4) / **미구현**: `check_global_gates` def 0; "T3 전역 게이트 |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/review_D_gain_decomposition_incidents.md:73` | / 33 / 8 / gain 관련 전체회로 계산 비용: ① `parasitic_pm_deg`가 25개 주파수 복소 MNA를 돌며 한때 `_evaluate`의 **28%** ② 목표 "at_omega 50→25회" ③ `_full_circuit_response`가 smallsignal metric(gain_full/cmrr/psrr)마다 5 |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_ambiguities.md:39` | / X05 / 공통 / 4 / "평가 오버헤드 실측"(plan:378, 399), "wall-clock ≤ 5분(B4)"(plan:392은 7b만, plan:1558은 **각 Phase**) / 측정 조건이 없다: 어떤 spec(정본?)·`slsqp_kwargs`(run_harness.py:326 n_starts=3/maxiter=25)· |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_ambiguities.md:159` | / P6b-09 / 6b / 2 / C-b "파생 필드는 입력 버전을 기록"(plan:1056) / 버전 표현(내용 해시? 단조 카운터?)과 비용이 없다 -- 평가 72.9ms 예산(메모리 실측)에 필드마다 해시를 붙이면 역행 / 없음 / 버전 = 쓰기마다 증가하는 writer 카운터(필드 단위), S2 memo 키만 내용 해시 / 아니오 |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_ambiguities.md:196` | / P7b-07 / 7b / 2,5 / 면적 제약형(A08, plan:263), `Area_i` 정의 미결(A2, plan:818), 면적 예산 미선언 시 Pareto 후 정지(A09, plan:264) -- 파일럿에 area 제약 없음 / 7b 파이프라인이 파일럿에서 Pareto로 정지하므로 DoD "파일럿 wall-clock ≤5분"( |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_ambiguities.md:208` | / P7c-04 / 7c / 2 / D4 "wall-clock ≤5분 안에서 평가 1회 실측 시간으로 샘플 수를 계산"(plan:1101), "Sobol/LHS, 1,000점 × 72ms ≈ 72초"(plan:1069) / 식에서 빼야 할 고정 비용(presolve 16.5s history:573, DP, 좌표강하, SLSQP polish |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_contradictions.md:56` | / 22 / 범위 / plan:392 7b DoD "파일럿 wall-clock ≤ 5분(B4)"; plan:40 "파일럿 wall-clock ≤ 5분" / plan:1558 "**각 Phase DoD**: … wall-clock ≤ 5분(B4)" / 5분 기준이 7b 한정인지 모든 Phase인지 다름(0.5~3은 파일럿 실행 대상 아님)  |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:17` | / 2 / **Phase DoD** / §4.1 376-393 / §15.8 1558(공통 DoD) / §4.1 378(공통) / Context Anchor SUCCESS 40 / §13.5 T0~T7 완료 판정 1234-1243 / §14.6 1393·1410 / §14.7 1421 / **다름.** (a) wall-clock ≤5분이  |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:25` | / 10 / **근거 통계** / Exec Problem 26(7/51, 68건, 14커밋 중 13) / Context WHY 37(41건 중 23) / §0.1 49(15,270·2,700·12,936·3,946줄) / §12.2 1001(1,325→72.9ms) / §12.3 1008-1021 / §13.1 1124-1136(R0~DU |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:36` | / 16 / **wall-clock ≤ 5분** / Context 40 / §4.1 7b 392 / §5 414 / §12.8 D4 1101 / §3.4 A53 308 / §15.8 1558 / **다름**: 1558은 모든 Phase, 392는 7b만(#2) / N6.3 또는 N6.2 7b 중 하나로 결정(N7) / -- / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:37` | / 17 / **전역 샘플 수** / §12.8 D4 1101("실측으로 **계산**") / §12.5.4 1069("1,000점 × 72ms ≈ 72초") / G9 1517 / **모순**: 1069가 1,000이라는 숫자를 박았다. D4와 상수 금지 원칙(B03)에 어긋난다 / N3.5(규칙: D4 계산) / 1069의 숫자는 "예시  |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:162` | / 1066-1072 / 12.5.4 최적화 계층 / 규범 → N3.5 / 1069의 1,000점은 삭제(#17). 제목 "(G3/G4)"는 §12.1 목표 번호라 **충돌** / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:298` | N7 공동분석·남은 결정(J1~J9, D5~D8, D14 상시, A33, bisection·TS4~6 배치, override 존치, wall-clock 범위, 미배정 이슈) |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:452` | 2. wall-clock ≤ 5분이 모든 Phase의 DoD인지 7b만의 DoD인지(#2, #16). |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite2_duplication_history_map.md:457` | 7. §12.5.4의 "1,000점" 삭제(D4와 모순). |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite_X_decisions.md:65` | / A53 / D4 전역 샘플 수는 wall-clock ≤ 5분 안에서 실측으로 계산(5분=B4 DoD) / 2026-09-14 / plan:1020, plan:349-351 / G9 / **유효·미구현** / |
| `docs/03-analysis/gain-budget-gmid-sizing-function-audit/rewrite_Y_open_issues.md:56` | / B4 / 실행시간 예산 항목 없음 / 해소 -- DoD에 wall-clock ≤ 5분(현재 평가 1회 72.9ms) / P:349-351; 커밋 199b5c9 / |
| `.ai/context.md:8866` | 자유 theta 13개)가 10분+ 무응답이었다(CR절 실측). CR절 원안은 "row_split/box_shape/ |
| `.ai/context.md:9004` | 10분+ 무응답 -- A절 수정이 효과가 없어 보여 조사한 결과, 이 회로는 애초에 |
| `.ai/context.md:10183` | 삭제. 커밋 `5054026`. 통합본 `ast.parse()` 문법 확인만 했고 전체 실행(10분+ 소요)은 |
| `.ai/context.md:13945` | 잘못 잡았다. 실제는 앵커 4개 기준 **2.9분**. (다만 내 첫 추정 "0.4초"도 44배 낙관이었다 -- |
| `.ai/context.md:14356` | - **평가 1회 1,325ms → 72.9ms(18배)**, 탐색 1,465s → 134s. |
| `.ai/context.md:14658` | - 핵심: DEC-59(지원 범위 = 규칙 분기 검증 발동, `기록만` 분기 항상 정지 `unsupported_rule_branch`), DEC-60(레일 넷 topology `supply_nets` / 전압 스펙 `supplies`, 미선언은 현행 이름 집합 전환기 해석), DEC-61(소자 선택 필드 `bulk`, 기본 nmos=최저· |
| `workspaces/run_harness.py:23` | 매번 처음부터 다시 돌고 있었다(사용자 실측 지적: current_reuse_telescopic_ota 10분+ |
| `skills/analog-gmid-design/assets/sizing_recipe.py:4992` | SLSQP 1 start = 84점에 35.1s). 계획 문서 §7.6의 L_combo 전수 스캔은 이 호출을 수백~수만 배로 |
| `skills/analog-gmid-design/assets/sizing_recipe.py:9492` | #       그랬다(사용자 실측 지적: current_reuse_telescopic_ota 10분+ 무응답). 아래 세 헬퍼는 |
| `skills/analog-gmid-design/assets/tests/probe_L_search_window.py:27` | (자동 테스트가 아니라 조사용. 웜스타트 16.5s + 343 combo 73s = 90초 이상 걸린다.) |
| `skills/analog-gmid-design/assets/tests/probe_runtime_budget.py:8` | (stage 2개 6.3ms vs 전체 평가 274.5ms). |
| `skills/analog-gmid-design/assets/tests/probe_runtime_budget.py:12` | presolve_warm_start()      16.5 s  (1회성 -- L_combo 루프 안에 들어가면 안 된다) |
| `skills/analog-gmid-design/assets/tests/probe_runtime_budget.py:13` | 전체 평가 1회              274.5 ms |
| `skills/analog-gmid-design/assets/tests/probe_runtime_budget.py:14` | L_combo 전수(앵커 4^3=64)  17.6 s   -> 중첩(레이아웃 5회 x VDS 2회) 175.7 s = 2.9분 |
| `skills/analog-gmid-design/assets/tests/probe_runtime_budget.py:15` | densify 41점(41^3)         5.3시간  -> 기본 금지 |
| `skills/analog-gmid-design/references/stick-diagram-euler-layout.md:1151` | 부분)을 row_split 재시도 매 라운드마다 처음부터 다시 호출해, 10분+ 무응답이 발생했다. |

- 총 91 행 적중.

### workspaces/run_harness_out*.log -- 엔진이 직접 찍은 SLSQP 실측

| 로그 | mtime | SLSQP 자유변수 | start별 (iters, elapsed) | 누적 캐시 점수 | 총 SLSQP 초 | **평가 1점당 ms(역산)** |
|---|---|---|---|---|---|---|
| `run_harness_out.log` | 2026-09-03 | - | (SLSQP 종료 로그 없음 -- 측정 불가) | - | - | - |
| `run_harness_out10.log` | 2026-09-04 | 6 | (12 it, 35.1s), (24 it, 74.1s), (1 it, 23.2s) | 270 | 132.4 | **490.4** |
| `run_harness_out2.log` | 2026-09-03 | - | (SLSQP 종료 로그 없음 -- 측정 불가) | - | - | - |
| `run_harness_out3.log` | 2026-09-03 | - | (SLSQP 종료 로그 없음 -- 측정 불가) | - | - | - |
| `run_harness_out4.log` | 2026-09-03 | 6 | (25 it, 240.6s), (25 it, 147.1s), (25 it, 468.5s) | 949 | 856.2 | **902.2** |
| `run_harness_out5.log` | 2026-09-03 | 5 | (25 it, 676.7s), (25 it, 278.3s), (25 it, 299.5s) | 940 | 1254.5 | **1334.6** |
| `run_harness_out6.log` | 2026-09-03 | 5 | (25 it, 105.2s), (25 it, 462.4s), (25 it, 384.2s) | 744 | 951.8 | **1279.3** |
| `run_harness_out7.log` | 2026-09-03 | 5 | (24 it, 13.2s), (2 it, 4.4s), (5 it, 12.9s) | 33 | 30.5 | **924.2** |
| `run_harness_out8.log` | 2026-09-03 | 6 | (12 it, 33.4s), (24 it, 69.8s), (1 it, 22.3s) | 270 | 125.5 | **464.8** |
| `run_harness_out9.log` | 2026-09-04 | 6 | (12 it, 35.0s), (24 it, 74.1s), (1 it, 22.9s) | 270 | 132.0 | **488.9** |

- `누적 캐시=N점` = `_cached_evaluate` 캐시에 들어간 **서로 다른 theta 점 수** (sizing_recipe.py:11498 `_eval_cache`). 총 초/점수 = 평가 1점당 실측 시간.
- SLSQP 자유변수는 topology의 자유 theta 전부가 아니다: `presolve_warm_start()`가 `vote_determined`/`stage_budget_L`을 고정하고, 의존그래프 분류가 `coupled`/`ambiguous`인 것만 남는다(sizing_recipe.py:11445-11449). 파일럿 실측 = **5~6개**(선언 자유 theta 14개 중).
[M6 done]


## [M8] 주파수응답 MNA(복소) -- `parasitic_pm_deg`의 25점 스윕 (2026-09-16 12:59:05)
- 근거: `sizing_recipe.py:4407` `n_pts = 25` -- 평가 1회마다 omega 25점에서 `full_circuit_response_at_omega()`(:4267)가 복소 MNA를 푼다. 조립은 `build_ac_network()`(:4230)가 평가당 1회로 캐싱(세션47 수정).

| n | 복소 solve us/회 | x25 = 평가당 us | 실수 solve us/회(대조) |
|---|---|---|---|
| 4 | 4.06 | **101.6** | 3.55 |
| 12 | 6.16 | **153.9** | 5.72 |
| 17 | 7.64 | **191.0** | 5.93 |
| 31 | 13.55 | **338.7** | 9.15 |
- 파일럿(n=31)의 25점 복소 solve만으로 평가당 약 위 값 -- 평가 1회 총 ~70~100 ms 중 선형대수 자체는 1 ms 미만이다. 즉 **비용은 LUT 조회·사이징 루프 쪽**이다.
[M8 done]
