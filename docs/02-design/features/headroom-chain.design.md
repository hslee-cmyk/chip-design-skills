---
template: design
version: 0.1.2
plan: ../../01-plan/features/headroom-chain.plan.md
plan_version: 0.7.9.9
---

# headroom-chain Design Document (HC-D: card HC-S, HC-1)

> **Summary**: 승인 계획 `headroom-chain.plan.md`의 HC-S(포화 기준 단일화)와 HC-1(R-1′ + R-3 + 선언 triode)을 card로 내릴 수 있게 필드·함수·배선·시험·재작성 범위를 정한다. GC-8·GC-1은 `graph-consumption.design.md`, HC-O는 이 판 밖이다.
>
> **Status**: v0.1.2(§3.1·§3.4·§7.2·§9, 위임 A-49). v0.1.1(§2·§3 card 후속, 위임 A-46). v0.1 승인됨 -- 사용자 결정 O-226 위임 A-27(2026-11-04). 계획 기준 = headroom-chain 0.7.9.9(상위 v6.38.10, 승인 판 v6.38.8 master `c0b41eee` 승인 A-25), design v1.16.3에 병합됨(옛 base `8b9ec744`).
>
> **결정 입력**: O-190·O-191(R-1′ 묶음, HC-1 + GC-8 통합 병합), O-202~O-212(전도·포화 경계·`off`), O-214·O-217·O-218(LA-1a), O-220·O-224(칸별 판정 유지), O-225(구현 우선).
>
> **이력**: [headroom-chain.design.history.md](headroom-chain.design.history.md)

## 0. 읽는 법과 경계

- **값 원칙**: 수치 상수 0. VDSAT·VDS 하한은 LUT에서, 경계는 정의에서 온다(계획 N0).
- **as-built 인용 제한**(원칙 8): `E/...` 인용은 지울·바꿀 범위 목록이다. 자리·writer·판정의 근거가 아니다. 줄 번호는 base 기준 참고값이고 card 착수 때 다시 잰다. IT-1·IT-2·EO-1·TB-1·card C가 먼저 병합되므로 줄과 이름이 바뀔 수 있다.
- **tol 문언**: 계획 본문의 '+tol_VDsat'·'− tol' 잔재는 계획 머리(HC:42)대로 상위 N3.6 '전도·포화 경계·`off` 선언 정본'이 이긴다. 이 문서는 정본만 쓴다. 정리 대상 줄은 §12-S1.
- **HC 문언 변경 0**(O-224). R6 효력(첫 통과 칸 채택)은 재질문 묶음으로 미룬다.
- **측정 표지**: `[재점검]` = O-225로 미룬 측정이 없어 계획 권고를 기본안으로 쓴 항목이다. LA-1 측정 시점에 다시 본다. 전부 §11에 모았다.
- **경로 약어**: `E/` = `skills/analog-gmid-design/gmid_engine/`. `HC:n` = 계획 n행, `GC:n` = graph-consumption 계획, `P:n` = 상위 계획, `D40:n`·`D41:n` = 상위 design.

## 1. 한 문장 판정

**HC:255와 HC:259·260의 관계(O-224 표지 -- 이 문서가 정한다)**: 충돌 기록은 `graph/start: rungs`와 각 칸의 θ 값을 바꾸지 않고 사다리 선택(GC-5 칸 0 규칙)에도 쓰이지 않으며, 거르기는 그 필드를 그대로 둔 채 소비 경로가 커널로 평가할 칸에서 같은 J_point 판정의 위반 칸만 빼는 소비자 쪽 일이고, 그래서 HC:255의 '사다리·θ는 바꾸지 않는다'는 생산 필드에 대한 문장으로, HC:259·260의 '거르기·다음 칸'은 평가 순회에 대한 문장으로 함께 성립한다.

이 읽기에서 ⚠가 하나 남는다: 거르기는 base가 커널을 불렀을 칸을 부르지 않으므로 칸 0이 걸린 회로에서 시작 칸·`repairs` 경로가 바뀐다. 이것은 HC:441 앞 문장('시험점을 거르면 결과가 바뀐다, 바뀐 칸마다 출처 기록')에 드는 변화이고 '충돌만 추가'(같은 행 뒤 문장, 칸이 하나도 안 걸리거나 걸린 칸이 어차피 평가되지 않은 경우)와 구분해 변화표에 적는다.

## 2. graph 소유표(새·바뀐 필드 전수)

상위 D40 §2.4.8에 같은 행을 옮기는 일은 §13의 인계 줄이다. 형식 정본은 이 표다(D40:454 'R-1′ 필드 형식의 정본 = HC-D design').

| (kind, field) | 값 형식 | writer(1) | 층 | 제작 card | 소비자 |
|---|---|---|---|---|---|
| `device: dc_sat_v` | `SatBound(vdsat_v, tol_v, reason)` -- §3.2 | DC 블록(as-built 자리 `dc_widths`, `device.dc_op`와 같은 블록 -- P:577, WB-1이 재작성) | 평가 | HC-S | 봉인 7, `metrics_aux._sat_devices`, J_point(§5.3), 관문 `off_region_gate`(§3.4, 위임 A-46) |
| `node: dc_root_path` | `RootPath(root_kind ∈ {F, W4}, root_net, steps)`; `steps` = ((변 참조, 부호), ...) -- 변 참조 = MOS 이름(방향은 `dc_vgs_edge`를 참조) 또는 저항 이름 | `dc_writer_plan` | S0 | HC-1 | `chain_graph` 블록 |
| `device: dc_vgs_edge` | `VgsEdge(lo_net, hi_net)` -- `off` 선언을 뺀 모든 MOS의 (gate, source) 변(쓰기 계획 열거와 같음, 41 §4.8), 비트리 포함 | `dc_writer_plan` | S0 | HC-1 | `iv_headroom`(HC-1), `headroom_bound._edges`(GC-8), `chain_graph`(`triode_protected`의 Gs⁺ 변) |
| `graph: dc_current_symmetry` | `CurrentSymmetry(ties, negated, zeros)` | `dc_current_symmetry`(sizing 층, 새 블록) | S0 | HC-1 | `search_domain`(읽기만), `chain_graph`(구조적 0 전류 MOS) |
| `graph: chain_graph` | `ChainGraph(nodes, edges, vr_edges, root_rows)` -- §5.1 | `chain_graph`(sizing 층, 새 블록 = R-1′ 블록) | S0 | HC-1 | `iv_headroom`, `order_terms`·`headroom_bound`(GC-8), `search_domain`(단좌표 자르기), J_point, F_exist, R6(LA-1a), 층 0(LA-1) |
| `graph: triode_protected` | ((X, (Z, ...)), ...) -- 선언 triode X별 지켜지는 소자 | `chain_graph` | S0 | HC-1 | `dc_seal_triode`(기록) |
| `graph: stack_candidates` | ((X, Y), ...) | `stack_candidates`(graph 층, 새 블록) | S1 | HC-1 | 봉인 7 사유 세분, 칸별 R-3 판정 |
| `graph/start: loop_conflicts` | `LoopConflict` tuple -- §6.2, 위반 칸만 | `loop_dependents`(7a 블록, `E/search/iv_kvl_choice.py`) | S0 | **HC-1**(D42 D-LA1a 정정 -- §13) | 칸 번호 = 칸 거르기(엔진). 나머지 칸 = 출력 전용(§6.3) |
| `graph/start: loop_stack_notes` | 칸별 R-3 기록 tuple | `loop_dependents` | S0 | HC-1 | **출력 전용**: 결과 JSON·단계 보고(U-H15 (가)) |
| `graph: dc_seal_triode` | 봉인 항목(정의역 게이트) | `dc_seal_triode`(새 블록) | 평가 | HC-1 | 봉인 판정 |
| `device: dc_triode_region` | `TriodeRegion(vds_v, vdsat_v, region, protected_none)` | `dc_seal_triode` | 평가 | HC-1 | **출력 전용**: 봉인 보고 |
| `graph: dc_seal_7`(바뀜) | 사유 어휘·`detail` 칸 추가 -- §7.2 | `dc_seal_region`(writer 변경 = card EO-1 범위 4 -- 41 §4.8-3, `dc_seal_saturation`·`seal_saturation.py` 삭제, EO-1 범위 4 → HC-S 표 #7이라 이 문서의 card는 처음부터 이 writer를 고친다) | 평가 | 칸 = HC-S·HC-1 | 그대로 |
| `graph/kernel: search_domain`(바뀜) | 상자 + 칸 `chain_cuts` | `search_domain` 그대로 | S0 | HC-1 | 상자 = 기존 소비자, `chain_cuts` 칸 = 출력 전용 |
| `gvgs_summary.vds_saturation`, `REL_VDS_SATURATION` | **삭제** | -- | -- | HC-1 | 엔진 소비자 0(HC:190), test 표 3곳 + metamorphic 1곳은 test 역할이 다시 씀 |

**소비자 표지**(위임 A-18, O-226): `f_exist` 구간 칸(`node_lo`·`node_hi`·`vr_*`)과 `chain_cuts` 단좌표 자르기는 HC-1이 만들고 R6 전 엔진 소비자가 0이다(소비자 = 같은 LA-1 경로의 R6, 표 #16·#22). toy로 잠그는 기간 예외이고 사용자 보고 항목이다.

**쓰지 않는 필드(R6 몫)**: `graph/start: loop_dep`, `reopen`, `start.guard`, `kvl_adjusted`·`kvl_macro_recheck`는 HC-1이 만들지 않는다. HC-1은 `graph/start: records`·`conflicts`에 쓰지 않는다(writer = `start_intervals`, M2 지적과 같은 규칙).

**새 cache·memo·sctx 슬롯·사본**: 0. 구조는 graph reuse, 점 풀이는 S3 색인(§5.3), LUT는 LUT memo.

---

# 부 I. HC-S

## 3. `sat_threshold`와 `device: dc_sat_v`

### 3.1 정본 함수(HC:331, G 이름 닫음)

자리 = lut 층(search·sizing·metrics 모두 아래에서 읽는다). 파일은 구조 규칙 A로 나눈다(위임 A-46): `E/lut/sat_threshold.py`(`sat_threshold`·`SatBound`), `E/lut/sat_threshold_grid.py`, `E/lut/derived_fns.py`(`vds_floor` 항목).

```
sat_threshold(memo, kind, w_key, L, vgs, vds, vsb) -> SatBound(vdsat_v, tol_v, reason)
sat_threshold_grid(memo, kind, w_key) -> VDSAT 열 배열 또는 None   # edge_costs·곡선용, 같은 열 읽기 한 자리
derived(memo, "vds_floor", kind, w_key) -> float                    # 옛 _vds_floor 이동, DERIVED_FUNCTIONS·DERIVED_TABLES 항목(HC:515, 위임 A-46·A-49)
```

- **VDSAT 열 읽기는 `column_source` 한 자리다**(두 입구가 같은 출처를 읽는다, 위임 A-46). 점 입구는 L bin을 지키는 보간(`vdsat`, lut CONTRACT 4.0), 격자 입구는 같은 열 원소다. 시험: 격자점에서 두 입구 값이 같다.
- **tol_v**: `tol_vdsat_table(...).at(L, vds)`. '구별 불가' 기록 전용(O-204). 판정·절단에 안 쓴다.
- **정의역**: 선언 방향 VDS < 0이면 LUT 조회 없이 `reason = REASON_REVERSE_VDS`, 두 값 None(옛 SD-2, HC:385). 이 사유의 뜻 = 포화 아님.
- **사유 어휘**(`SatBound.reason`, 값이 있으면 None): `reverse_vds`, `vdsat_column_unavailable`, `lut_domain`(O-205 (1) 정의 불능), `off_declared`(필드 쪽에서만). tol 셀이 None이면 `vdsat_v`는 있고 `tol_v`만 None이다.
- **예외**: `SealViolationError`를 사유 키로 나눠 받고, 모르는 사유는 소자 이름을 달아 다시 던진다(광범위 except 0).

### 3.2 값 칸: `sat_v` 칸을 두지 않는다

HC:331·515는 칸을 '(VDsat, tol, sat_v)'로 적었다. O-204 뒤 `sat_v` = VDsat이라 같은 정의가 두 칸이 된다. graph 규칙 3에 따라 `vdsat_v` 한 칸으로 두고, 소비자의 `SatDevice.sat_v`는 `vdsat_v`를 읽는다. **작성자 판단 J1**(HC:42 머리 '정본이 이긴다'의 적용, 원래 취지 변경 아님).

### 3.3 `dc_sat_v` writer

DC 블록이 `dc_op`를 쓰는 같은 평가에서 `sat_threshold`의 정의되는 모든 MOS 값을 쓴다. 선언 없는 비전도 소자도 담는다. `off` 선언 소자는 값 없이 `off_declared`만 남긴다(HC:331, 순서 EO-1 → HC-S이라 어휘가 있다, 과도기 갈래 0). `triode` 선언 소자는 값을 쓴다(`triode` 경계가 읽는다).

### 3.4 소비자 배선과 결측 동작 표(HC:331 'design이 표로')

| 소비자 | 바꾸는 일 | `reverse_vds` | `vdsat_column_unavailable` | `lut_domain` | `tol_v` None |
|---|---|---|---|---|---|
| 봉인 7 `dc_seal_region`(EO-1 범위 4 뒤 -- 41 §4.8-3) | 공용 영역 판정의 VDSAT 입력을 `dc_sat_v` READS로(LUT 조회 삭제 -- HC-S). 판정 = VDS ≥ VDsat(EO-1 그대로, `2·tol` 항은 EO-1이 이미 지움). `|VDS − VDsat| < tol` 기록 = EO-1 `indistinct` 그대로 | 선언 없음 = 거부, 사유 '포화 아님(역방향 VDS)', `triode` 선언 = 통과(41 §4.8-2 VDS < 0 행) | `vdsat` `None` → EO-1 `unresolved`, **항목 미정**(N3.6 7행, 통과로 세지 않음 -- HC:580 '거부' 문장은 계획 정정 표지) | `OUT_OF_DOMAIN` → E-0 정의 불능 거부 | 판정 그대로, 띠 '미정' 기록 |
| `metrics_aux._sat_devices` | `dc_sat_v` READS, 직접 조회 삭제 | `sat_v` None | `sat_v` None | `sat_v` None | `sat_tol_v` None |
| 커널 창 행 `saturation_rows`(WB-1 범위 3a가 지우기 전까지, 시도 전압) | `sat_threshold` 호출로 교체, 여유 = VDS − VDsat. 행 집합 그대로. HC:580의 `saturation_rows` 호출 문장은 이 행으로 읽는다 | None(창 안 좁힘, base와 같음) | None | None | 영향 없음 |
| `icm_config`의 봉인점 `region_rows` 행 | **`device.dc_sat_v` READS**(HC-S가 배선 -- 같은 소자·같은 점 둘째 생산자 금지), 여유 = VDS − VDsat. 행 집합 그대로 | None(창 안 좁힘, base와 같음) | None | None | 영향 없음 |
| 관문 `off_region_gate`(41 §4.8-7, 위임 A-46 -- 같은 소자·같은 점 둘째 생산자 금지) | 기준 VDSAT·vdsat(X) = `device.dc_sat_v.vdsat_v` READS. 보정점 vdsat(X + ΔX) = `sat_threshold(...).vdsat_v`(`lut_domain` → `OUT_OF_DOMAIN`). ΔX = 0이면 조회 0 | `triode`만 도달: `OUT_OF_DOMAIN`, 조회 0(41 §4.8-7, 위임 A-49) | 해당 없음(봉인 미정이면 ss에 안 옴) | `OUT_OF_DOMAIN` → `off_gate` 거부 | 영향 없음 |
| `iv_domain`·`iv_headroom._lower_bound` | `tol_vdsat` 호출 삭제. VDsat은 곡선 묶음의 VDSAT 곡선 -- 곡선 생성이 `sat_threshold_grid`를 읽게 배선 | 해당 없음(곡선 VDS ≥ 0) | 그 경계 비활성, `inactive` 기록(대체값 없음, U-H15 원리) | 그 곡선 점 제외 | 해당 없음 |
| `edge_costs` | `_tol_vdsat_grid` 삭제. 포화 술어 = `vds ≥ sat_threshold_grid`. VDS 비용 = 포화 가능 격자점의 VDSAT 최솟값(따로 잡은 tol 최솟값 합 삭제) | -- | VDSAT 열 없음 = 포화 거르기 없음(문턱 하한 0, DEC-67 상한 예외, HC:331) | 그 격자점은 on_mask가 이미 뺌 | 해당 없음 |
| `block_columns` VDS 정의역 | `_vds_floor` 삭제, `vds_floor` 호출 | -- | -- | -- | -- |

**작성자 판단 J2**: HC:580은 `iv_domain`·`iv_headroom`이 '그 함수를 부른다'고 적었으나, tol을 지우면 두 자리에 남는 것은 곡선 값이다. 곡선 점마다 점 입구를 다시 부르면 같은 열을 두 번 읽는다. 곡선 생성이 격자 입구를 읽으면 정본은 하나이고 호출 경로로 보일 수 있다.

**동작 변화 한 줄**(HC:331): `metrics_aux`의 `SealViolationError` 재발생이 `dc_sat_v` 사유 기록으로 바뀐다.

### 3.5 삭제(HC:515 재작성 범위)

`E/search/_helpers_curves.py` `tol_vdsat`; `E/lut/derived_fns.py` `_tol_vdsat_max`·`DERIVED_FUNCTIONS` 항목·`_tol_vdsat_grid`; `E/sizing/block_columns.py` `_vds_floor`; `E/sizing/seal_region.py`(EO-1이 만든 파일 -- VDSAT 조회 쪽)·`E/metrics/ss_off_gate.py`(EO-1이 만든 파일, 위임 A-46)·`metrics_aux`·`saturation_rows`의 직접 조회. SD-1은 WB-1 몫이라 건드리지 않는다.

### 3.6 HC-S 순서와 변경 종류

시작 조건 = HC-D 승인, card C, IT-1 병합, EO-1 병합(표 #7). 뒤따름 = HC-1, WB-1(표 #6·#11). 변경 종류 = 동작 변경(O-34), 다리 (a) 시작점 ngspice, (b) `headroom_unattainable`(HC:541). ⚠ HC:582의 '봉인 7 보고·metric `sat_v` 순수 리팩터링'은 O-204 뒤 성립하지 않는다(`2·tol`·`+tol` 삭제가 값을 바꾼다) -- EO-1이 봉인 7을 먼저 바꿨으면 그 부분만 순수 리팩터링이고, 아니면 동작 변경으로 변화표에 적는다(§12-S1).

### 3.7 HC-S toy(test 역할, 기대값은 정의 문장에서 손으로)

| id | 입력 | 기대 | base |
|---|---|---|---|
| S1 | VDS < 0 | `reverse_vds`, LUT 조회 0 | LUT 축 오류 -- red |
| S2 | L이 bin 경계를 넘음, 격자점 위 VDS | bin 안 앵커 값 | 옛 함수와 다름 -- red |
| S3 | VDSAT 열 없음 | 사유, 0이 아님. `edge_costs`는 그 점 포함, 봉인 = 미정(통과로 세지 않음) | 옛 0 대체 -- red |
| S4 | VDS = VDSAT, VDS = VDSAT − ε < 띠 | 앞 = 통과 + 띠 기록, 뒤 = 거부 + 띠 기록 | 옛 tol 여유 -- red |
| S5 | 선언 없음·`triode`·`off` 셋 | `off`만 사유, 나머지 값 | 필드 없음 -- red |
| S6 | 격자점 | 점 입구 = 격자 입구 | -- |
| S7 | 작은 격자 LUT | `vds_min_v` 손계산, 비포화 격자점의 작은 VDSAT을 안 씀 | 정의 다름 -- red |
| S8 | `git grep` | `_tol_vdsat_max`·`_tol_vdsat_grid`·`tol_vdsat(` 0, `dc_sat_v` writer 1 | -- |
| S9 | 관문: 필드 기준 VDSAT 주입(위임 A-46) | s′이 필드 값 기준, ΔX = 0이면 `sat_threshold` 호출 0 | LUT 직접 조회 -- red |

---

# 부 II. HC-1

## 4. 쓰기 계획 블록 출력과 방향 규칙 P(G-2)

- **P**(자리 `E/sizing/_helpers_polarity.py`, 정의 1곳): `upward_vds(kind, pins) -> (lo, hi)`, `upward_vgs(kind, pins) -> (lo, hi)`. nmos = source가 낮은 단자, pmos = source가 높은 단자에서 유도한다.
- **1회 호출**: `dc_writer_plan`이 변마다 한 번 P를 불러 `dc_vgs_edge`를 쓰고 `dc_root_path`는 그 변을 참조한다(D40:2206 (c) 참조형). VDS 쪽은 `chain_graph`가 변마다 한 번 부른다. 소비자는 P를 부르지 않고 필드를 읽는다.
- **`dc_root_path`**: 트리 BFS(`walk`)가 쓰는 선행 넷·변에서 만든다. F 성분은 `root_kind = F`, W4 성분은 `W4`, 고립 넷은 `steps = ()`. 값 사본 없음(부호·참조만).
- **파일 분할**: 구조 규칙 줄 수 안이면 `writer_plan.py` 안, 넘으면 `writer_plan_paths.py` 조각. card 실측.
- **`dc_current_symmetry`**: `E/search/current_symmetry.py`를 `E/sizing/current_symmetry.py`로 옮겨 블록으로 감싼다. READS = 궤도·생성원·`dc_colour`·`dc_current_basis`, extras = spec `search.untie_orbits`. **같은 커밋에서** `search_domain`의 호출을 필드 읽기로 바꾼다(D40:2206 (e) 생산자 둘 기간 0).

## 5. 제약 그래프, F_exist, J_point(G-1, G-11, G-12)

### 5.1 `ChainGraph`(`E/sizing/chain_graph.py`, sizing 층 3 이하)

```
ChainEdge(device, lo_net, hi_net, lo_node, hi_node, term_kind, on_structural, coords, route)
VrEdge(resistor, far_net, near_net)        # 값 미선언 DC 경로 저항, I_R 구조적 0 제외
RootRow(device, net)                       # dc_self_referential 소자의 writer_root 행
```

- **변은 MOS마다 하나**(HC:332). `term_kind` ∈ {`sat`, `lut_floor`(선언 triode), `off`}. `on_structural` = `off` 선언도 구조적 0 전류도 아님. 변을 지우지 않고 표지하므로 VDS-1 포함 관계(HC:265)가 표지로 깨지지 않는다.
- **마디**: F*와 미지수 묶음(W4 뿌리 또는 고립 넷). `lo_node`·`hi_node`는 `dc_root_path.root`에서 읽는다.
- **`coords`**: 변 가중치가 의존하는 θ 좌표 전부 -- 양 끝 넷의 `steps`에 든 MOS의 ln IDu(writer)·L, W4 y, θ 저항, 그 소자 자신의 ln IDu·L과 VSB를 정하는 source 넷의 좌표. 'VDS·VSB도 좌표에 든다'고 세어야 단좌표 부등식이 가정 동작점 없이 정말 1변수 함수가 된다(C-10, P-1).
- **`route`** = `cut`(좌표 1개) / `filter`(2개 이상) / `none`(0개, θ 무관 -- 판정은 J_point).
- **결정성**: 변 순서 키 = 소자 `dc_colour`. **D40:2206 (a) 닫음**: 변 키가 소자 색이고 구조 색은 정점마다 유일(D40 §2.4.8 구조 색 행, 소자도 정점)하므로 평행 소자도 갈리고 DEC-97 마지막 키는 **공허**하다. `TieBreak` 기록은 만들지 않고 HC:237의 빌린 형식도 필요 없다(D40:2206 (g)와 충돌 없음). 그 결과 계획 M-NM1 일곱째 자리는 측정 대상으로 되돌아가지 않는다. **작성자 판단 J3**.
- **V_R·I_R**(HC:228, O-225 표지): `VrEdge`는 연결만 담는다. 구간 값은 F_exist의 인자다. I_R 의존을 필드·서명에 넣지 않는다(§5.2). 저항 전류를 읽는 일은 호출자 몫이고 정본 = `dc_current_basis`(G-12).
- **W3 목표 넷(G-11)**: F 성분 넷이라 V_known = 목표값 + 경로 합. 따로 ΔV 항을 두지 않는다.
- **writer_root 행(D40:2206 (d))**: 근 존재 집합이 한 구간이라는 증명이 없다(LUT 곡선 비단조 가능). 그래서 **F* 차분 변으로 넣지 않고 F_exist 밖 교집합**으로 둔다. 판정은 J_point의 점 풀이 결과로 한다. 측정으로 한 구간이 확인되면 단순화할 수 있다 `[재점검]`.

### 5.2 판정 함수 한 자리: `E/sizing/chain_judge.py`

```
f_exist(chain, weights, vr_bounds) -> ChainExist(feasible, cycle, node_lo, node_hi, vr_lo, vr_hi)
j_point(chain, point_view) -> ChainVerdict(state, rows, reason)      # state ∈ {ok, violated, undefined}
```

- **`weights`**: 변 → (term, V_known(lo), V_known(hi)), 가정 동작점 값. `vr_bounds`: 저항 → (lo, hi) 또는 `None`. I_R을 받지 않는다.
- **`f_exist` 알고리즘**: 가상 시작점 Bellman–Ford, 변 순서 = 필드 순서. `cycle` = `ChainCycle(edges, path_kind, theta_free, violation)`.
- **HC:236 읽기**: '위반량이 가장 큰 순환'을 전역 최대로 찾으려면 단순 순환 열거가 필요한데(일반 그래프에서 NP-hard) HC:238이 열거를 금지한다. 그래서 **마디 수만큼 완화한 뒤 선행 그래프에 있는 순환들 가운데 최대, 동률이면 정준 순서 첫 순환**으로 읽는다. 출처 기록 전용이라 판정에 영향이 없다. **작성자 판단 J4**.
- **퇴화 등가**: 판정 자리는 `j_point`만 부른다. `f_exist`는 순환 출처와 R6 구간에만 쓴다(HC:242).
- **`j_point`는 점 풀이를 직접 하지 않는다.** `point_view`는 그 점의 평가 필드 읽기(`node.dc_v`, `device.dc_op`, `device.dc_sat_v`)이거나 풀이 실패 기록이다.

행 정의(`rows` = 위반 행만):

| 행 | 대상 | 위반 |
|---|---|---|
| `sat` | `op.current > 0`, 선언 없음 | VDS < `vdsat_v`, 또는 `reverse_vds` |
| `lut_floor` | 선언 triode | VDS < `vds_floor` |
| `writer_root` | `RootRow` | 풀이 실패 사유 = 근 없음 |

- 비전도 소자(`op.current ≤ 0`)와 `off` 선언 소자는 행 없음. 비전도의 최종 판정은 봉인 9다(HC:86).
- `vdsat_v` 결측·`lut_domain`·다른 풀이 실패 = `undefined`(E-0, 사유 기록). 칸 거르기는 이 칸도 뺀다.

### 5.3 점 풀이 자리: 커널 DC 접두 + S3 색인

- **문제**: J_point의 '쓰기 계획 정확 풀이'를 따로 풀면, 통과한 칸을 커널이 다시 풀어 같은 입력 재계산이 된다(HC:571 위반). 새 슬롯으로 넘기면 graph 규칙 2 위반이다.
- **결정**: `E/search/kernel.py`에 DC 접두 함수 `dc_prefix(sctx, theta, cells, origin)`를 둔다. `evaluate`가 쓰는 DC 블록 열(`dc_columns`, `dc_widths`까지)을 같은 `donors`·`counters`로 부르고, `evaluate`도 이 함수를 지나간다. 블록 호출이 S3 색인에 등록·graft·실패 재연을 하므로 **같은 θ는 한 번만 푼다**. 근 없음 실패도 `register_failure`로 재연된다.
- **색인 상한**: 접두 블록도 색인에 등록되어 칸 수만큼 항목이 는다. S0 블록 여유로 D40 §2.4.5 상한을 넘지 않는지는 G-10 판정 기준에서 본다.
- **'커널 평가 0'**(HC:259) = `kernel_calls`·평가 예산에 안 든다. 블록 계수는 `compute`로 잡히고 뒤 커널 평가에서 `graft`가 된다.
- **작성자 판단 J5**. 대안 비교:

| 안 | 재계산 | graph 규칙 | 단순성 | 판단 |
|---|---|---|---|---|
| **DC 접두 + 색인** | 0 | 기존 길 | `evaluate` 분할 필요 | 채택 |
| 블록 안 순수 풀이 | 통과 칸마다 1회 중복 | HC:571 위반 | 호출 단순 | ⚠ 기각 |
| 풀이 결과 슬롯 | 0 | 규칙 2 위반 | 단순 | ⚠ 금지 |

- **LA-1a 인계**: D41:1794는 R6를 `@compute_block`이라 적고 J_point를 '부르기만' 한다. `j_point`가 풀이 필드를 받으므로 블록 안 R6는 그 필드를 얻을 길이 필요하다. LA-1a design이 §6.2의 드라이버 꼴을 쓸지 정해야 한다(§13).

## 6. 7a 블록의 HC-1 꼴과 칸 판정

### 6.1 흐름

1. S0 스냅샷 완성 직후, `find_front` 전에 드라이버 `judge_rungs(sctx)`(`E/search/iv_kvl_choice.py`)가 칸마다 `layer0_start`와 같은 θ 조립으로 `dc_prefix`를 부르고 `j_point`를 낸다. 호출 자리의 정확한 줄은 card 실측(`SearchContext` 생성 뒤 한 곳).
2. 위반 칸에서만 그 칸 동작점으로 `f_exist`를 불러 순환 출처를 얻는다(같은 입력 재호출 0).
3. 칸마다 §7.3 R-3 기록을 낸다. 풀이가 없는 칸은 그 사유만.
4. `loop_dependents(projection)` 블록이 판정 묶음을 extras로 받아 두 필드를 쓴다. 판정은 이 블록 밖에서 처음 만들어지고 영속 자리는 이 필드 하나다(사본 아님). **드라이버는 base B0에서 칸을 판정하고 `loop_dependents`로 B1을 만든 뒤 `sctx`와 커널 컨텍스트의 base 참조를 B1로 한 번 바꾼다**(새 칸 0, 실행당 1회, `find_front` 전). DC 블록 READS에 `loop_conflicts`가 없어 입력 버전이 같고 색인 graft가 유효하다. 교체가 안 되면 멈추고 보고한다(graph 규칙 6).

**재개방 없음**(HC:255): J_point 위반이면 곧바로 기록한다. 비활성 갈래 0.

`rungs` 필드를 읽고 쓰지 않는다. GC-5 병합 전후 어느 쪽이든 '칸 번호 = 그때 `rungs`의 번호'로 같은 코드가 돈다(GC:438·440과 무의존).

### 6.2 `LoopConflict`

`LoopConflict(rung, state, rows, cycle, reason)` -- 위반·정의 불능 칸만. `rows` = (행 종류, 소자 또는 넷, 여유). `cycle` = `ChainCycle` 또는 None. 입력 포트 창 뿌리 성분의 빈 창은 같은 사유 코드 `chain_violation` + `path_kind`(HC:239, 완료 5 (ii)).

- **비어 있음 = 전 칸 통과**: 무동작 회로에서 빈 값이므로 HC:452 단언이 성립한다.
- **`StartConflict` 어휘와의 관계**: D41:1773의 `quantity = "kvl"` 형식은 소자·경계 하나짜리라 칸·순환을 못 담는다. 칸 있는 새 형식을 쓴다. 이름 정본은 이 절이다.

### 6.3 출력 전용 선언(O-224)

- **칸별 기록의 내용 칸**(`state`, `rows`, `cycle`, `reason`)과 `loop_stack_notes` 전체는 **출력 전용**이다. 엔진 reader 0, 독자 = 결과 JSON·단계 A 보고·재측정 사람.
- **칸 번호 칸**(`rung`)만 칸 거르기가 읽는다. 거르기가 J_point를 다시 부르면 같은 입력 재계산이고(HC:252·262), 거르기용 필드를 따로 두면 같은 사실이 두 필드다(graph 규칙 3). 그래서 규칙 L 표현은 **필드 reader = 칸 거르기, 내용 칸 = L-4 출력 전용 칸 목록**이다.
- **작성자 판단 J6**: O-224 '칸별 기록 = 출력 전용'을 칸 단위로 읽었다. 필드 단위로 읽으면 위 둘 중 하나를 어긴다.
- R6 첫 통과 칸 효력은 만들지 않는다.

### 6.4 칸 거르기(HC:259·260, G-4)

- **자리**: `E/search/layer0_center.py` `layer0_start`의 칸 순회, 커널 평가 앞. 칸이 `loop_conflicts`에 있으면 `start_status = "chain_filtered"`로 건너뛰고 수를 센다.
- **보고 칸**: `Layer0Result`에 `chain_filtered`(칸 번호 tuple). 재방문 재판정 0(G-4 (0)) -- 필드를 읽는다.
- **남은 칸 0**(G-4 (1)): 기록하고 순회 뒤 단계로 간다. 지금 그 단계는 as-built `_halton_probe`이고 LA-1a가 지운다.
- **`_halton_probe`·`_repair`에는 배선하지 않는다.** LA-1a가 지울 코드다(HC:259 대상 = 칸, P4; GC-8의 `ls_swing` 처리와 같은 원칙). 층 0 세 자리는 LA-1 몫이고 `j_point`를 부른다.
- **HC:262 '시험점 판정을 S3 평가 기록에'**: 칸 판정의 재사용은 위 필드와 §5.3 색인으로 충족된다. LA-1 세 자리의 평가 기록 칸은 LA-1 design이 정한다. 새 칸을 지금 만들지 않는다(소비자 없음).
- ⚠ **기간 위험**: `STATUS_PENDING_SEAL7` 칸은 지금 탐색 출발로 받아들여진다. 포화 위반 칸을 거르면 base가 출발하던 회로가 칸을 잃을 수 있고, 칸 0의 근 없음 칸을 거르면 `_repair` 출발도 없어진다. 시제품 칸별 재측정에서 아래 칸이 새 출발을 준 회로 0/9였다(d_questions §4, agent 인용). LA-1a R6 전까지 front가 줄 수 있다. 변화표 원인 항목으로 적고 판단은 재측정으로 미룬다 `[재점검]`.

### 6.5 단좌표 자르기(HC:258, G-4 (2))

- **자리**: `search_domain` 블록이 `chain_graph`를 READS하고 `route = cut` 변마다 `chain_cut(edge, variable, lut)`(`chain_judge.py`, 정의 1곳)을 불러 그 변수의 lo·hi를 좁힌다. 줄면 `chain_cuts` 칸에 (좌표, 방향, 값, 변)을 적는다(HC:253 관행).
- **풀이**: 좌표 상자 위 1변수 함수 g(c) = V(hi) − V(lo) − term. 근 찾기 함수와 허용오차는 기존 공용 함수의 선언을 쓴다(새 상수 0). 이름은 card 실측.
- **만족 집합이 한 구간이 아니거나 비면** 상자를 바꾸지 않고 `chain_cuts`에 사유를 적는다. 그 점은 J_point가 거른다. 대체값 없음, 정지 없음(G-4 경계, U-H15 원리).
- **두 호출 자리**: 이 자리는 모든 좌표가 상자에 열린 입력이다. R5′ (4)(iii)는 다른 좌표가 그 점에 고정된 입력이다. 입력이 다르고, 이미 자른 단좌표 행은 그 안에서 깨지지 않는다. 같은 입력을 두 번 자르지 않는다.
- **발동**: L도 좌표로 세므로 발동 회로가 적거나 없을 수 있다. 13회로 수 미측정 `[재점검]`. 0이면 toy로만 검증되는 코드이고 절대원칙 대상이라 §12-S3에 올렸다.

## 7. R-3과 선언 triode

### 7.1 적층 후보(G-5)

`stack_candidates`(S1, `E/graph/stack_candidates.py`): kind·gate 넷이 같고 Y.source = X.drain인 (X, Y). (gate, source) 묶음 정본 `gs_groups`로는 유도되지 않는다 -- 이 관계는 X.drain과 Y.source를 잇는 것이라 묶음 키가 다르다. 그래서 `pins`·`kind`에서 직접 낸다. `composite_diodes`를 부르지 않는다. 복합 diode 정본과 집합 대조(M-H3)·U-H2 질문은 `[재점검]`.

### 7.2 판정 함수와 봉인(G-6, G-7, G-13)

```
stack_unsat(memo, kind, w_key, vgs_y, vsb_x) -> StackJudge(holds, lhs_max, rhs, l_at_max, vgs_at_max)   # E/lut/stack_unsat.py(구조 규칙 A, test tests/lut/test_stack_unsat.py, 위임 A-49)
```

- max_{L, VGS(X) ∈ LUT 정의역} [VGS(X) − VDsat(X; VDS = VGS(X) − VGS(Y), VSB(X))] < VGS(Y). VDsat은 `sat_threshold_grid`에서 읽고 VDS가 음수인 점은 포화 불가로 센다.
- **G-13**: 범위 = LUT 정의역 전체(H-14). 탐색 상자 ⊆ LUT 정의역이므로 상자로 좁힌 판정보다 덜 성립한다(보수적). 상자를 읽지 않는다.
- **봉인**: `dc_seal_region`(41 §4.8-3 -- EO-1 범위 4가 만듦, 이 칸은 HC-1이 더함)이 extras 대신 `stack_candidates`를 READS한다. 위반 소자 X가 후보이고 Y가 전도(`dc_op.current > 0`)이며 선언 triode가 아니면 `stack_unsat`을 부른다. 성립하면 `detail`에 `reason = stack_unsaturable`, X·Y·VGS(Y)·좌우 값·VP 칸. 거부 여부는 그대로다. 위반 소자에서만 부른다.
- **G-6**: Y 상태는 풀린 `dc_op`에서 읽는다. 노드 풀이 반복 안에서 부르지 않는다.
- **사유 문언**(G-7): '이 Y 상태에서 X 크기로는 포화 불가, triode 선언 필요'. '또는 Y 크기 변경'은 **넣는다** -- 판정이 Y 고정 아래라 사실에 맞고 불가능 증명으로 읽히지 않게 한다. **작성자 판단 J7**.
- **VP 보고 칸**: n = 1 + gmb/gm, VT0 = VS 축 0점의 VTH. VS 축에 0점이 없으면 칸 None + 사유(M-H1b 미측정 `[재점검]`).

### 7.3 출발 기록

§6.1-3에서 후보마다 `dc_prefix` 결과로 같은 `stack_unsat`을 부르고, 성립하면 `loop_stack_notes`에 (칸, X, Y, 좌우 값)을 적는다. 정지 없음(U-H15 (가)). `off`·`triode` 선언 X, Y 꺼짐은 판정 안 함.

### 7.4 선언 triode(HC:309~320)

- **새 블록 `dc_seal_triode`**: READS `dc_op`·`dc_sat_v`·`triode_protected`. (i) 게이트: VDS ∈ [`vds_floor`, VDS 축 끝]이고 VGS 역산 정의. 어기면 소자 이름 + 사유 `triode_lut_domain`, 봉인 7 위반으로 분류하지 않음. (ii) `dc_triode_region` 기록. (iii) 지켜지는 소자 없으면 `protected_none = True` 기록.
- **`triode_protected` 계산**: Gs⁺(`dc_vgs_edge` + 저항 변)에서 X 변을 지우면 Z.d와 Z.s가 끊어지고 지우기 전에는 이어진 Z. 지우기 전에 안 이어진 Z는 넣지 않는다('모든 경로'가 공허한 경우).
- **선언 대조**(`triode` 포화·꺼짐 = 선언 오류)는 EO-1 공용 영역 판정 함수 몫이다. 여기서 만들지 않는다.
- **`off`**: R-1′ 항·R-3·출발 `sat_threshold` 호출 없음(HC:516). 효과 판정은 상위 N3.6 (5).
- **U-H14**(파일럿 선언)는 spec 승인이고 이 design 밖이다.

## 8. `iv_headroom` 배선과 예산 관계(G-3)

- `_edge_nets` 삭제. 방향은 `chain_graph.edges`, VGS는 `dc_vgs_edge`에서 읽는다. 구조적 전도 = `on_structural`.
- **성립 시점**: 선언 triode 비용 0·tol 제외 비용은 `headroom_bound`를 바꾸는 GC-8 커밋에서 성립한다(HC:343). 두 커밋 사이는 커밋별 변화표로 가른다.
- **창 미상 넷**: 구조적 0 전류 소자를 빼 레일에 안 닿는 넷은 그 예산 행을 빼고 `inactive`에 `WHY_WINDOW_UNKNOWN`을 적는다. 대체값 없음(HC:342).
- **G-3 출처 분리**: 소거식 = J_point 행(`loop_conflicts`), 헤드룸 예산 = `SRC_HEADROOM_*`. **포함 관계**: 헤드룸 비용 ≤ 같은 변의 점 비용(격자 최솟값)이므로 예산이 깨진 경로는 소거식도 깨진다. 역은 아니다.
- **새 graph 필드 소비**: `Bound` 새 출처 이름은 지금 쓰지 않는다. 좁히는 길은 §6.5뿐이다(`chain_cuts`).

## 9. HC-1 재작성 범위

| 파일 | 일 |
|---|---|
| `E/sizing/writer_plan.py`, `s2_values.py` | `dc_root_path`·`dc_vgs_edge` 출력, 값 형식 |
| `E/sizing/chain_graph.py`, `chain_judge.py`, `_helpers_polarity.py`, `current_symmetry.py`(이동) | 새 파일. `_module_map`·권한표 등록 |
| `E/graph/gvgs_cycles.py`, `s1_values.py`, `CONTRACT.md` 7.5·264~268·589 | `vds_saturation` 삭제 |
| `E/graph/stack_candidates.py` | 새 파일 |
| `E/search/iv_kvl_choice.py` | 새 파일: 드라이버 + `loop_dependents` |
| `E/search/kernel.py` | `dc_prefix` 분리(`evaluate`가 지나감) |
| `E/search/layer0_center.py` | 칸 거르기, 보고 칸 |
| `E/search/search_domain.py`, `current_symmetry.py`(옮김), `search_values.py` | 필드 읽기, 단좌표 자르기, `chain_cuts` |
| `E/search/iv_headroom.py`, `s0_fields.py` | 정본 읽기, `_edge_nets` 삭제, 권한표 |
| `E/sizing/seal_region.py`(EO-1 뒤), `seal_triode.py`(새) | 사유 세분, 게이트·영역 기록 |
| `E/lut/stack_unsat.py` | 신규: `stack_unsat`·`StackJudge`(구조 규칙 A, 위임 A-49) |
| `E/search/CONTRACT.md:866-870` | 열린 항목 닫기 |

- **선행**: TB-1, HC-S, IT-1, card C, GC-D design 승인, GC-1. **뒤따름**: GC-8 커밋(같은 통합 병합), LA-1a·LA-1.
- **변경 종류** = 동작 변경. 다리: 출발 부분 = 시작점 ngspice, 정의역 게이트 = 발동 회로 있으면 front oracle, 없으면 계수 0 기록. 선언 triode 회로 다리 = HC-O까지 보류. EO-1 완료 판정 선행.
- **HC:548·583 비교 대상**: **있으면 R6 필드 `loop_dep`, 없으면 7a 블록 출력 `loop_conflicts`**. HC-1 병합 때는 뒤쪽이다.
- **HC:255 끝점**: 'R6가 없는 기간'의 끝 = 선택 유보(O-220) 중 R6 card(LA-1a 또는 LA-1).

## 10. HC-1 toy와 test(test 역할, 기대값은 손계산)

| id | 회로·입력 | 기대 | 완료 |
|---|---|---|---|
| H1 | 고립 넷 하나 + nmos·pmos 두 변, 가중치 합 > 0 | `f_exist` 순환, 경로 'F* 경유' | 5 (i) |
| H2 | 같은 입력에 VDS 여유 충분 | 순환 없음, 구간 손계산 | 3 |
| H3 | 입력 포트 창 뿌리 성분, 빈 창 | `chain_violation`, 마디 = v_cm | 5 (ii) |
| H4 | 같은 창 뿌리 성분 안 두 넷 | `path_kind`, `theta_free` | 5 (iii) |
| H5 | 값 미선언 저항, `vr_bounds` 둘 | 차분 변 쌍 구간 손계산, 서명에 I_R 없음 | 3 |
| H6 | 자기 참조 writer, 근 없음 | J_point `writer_root` 위반 | 3 |
| H7 | 평행 소자 둘 | 변 둘, 순서 = 색, `TieBreak` 0, 이름 전단사 불변 | 3, 4 |
| H8 | 미지수 0 점 | J_point와 F_exist 같은 판정, 판정 자리 호출 = J_point만 | 등가 |
| H9 | 위반 칸 + 통과 칸 사다리 | `rungs` 필드 비트 동일, `loop_conflicts` = 위반 칸만, 커널이 위반 칸 안 부름 | §1 |
| H10 | 전 칸 위반 | 빈 평가 기록, 다음 단계로 감 | G-4 (1) |
| H11 | 통과 칸 | `dc_columns` 계수 compute 1 + graft 1, `kernel_calls`에 접두 안 듦. B1 평가의 `dc_columns`가 B0 칸 판정을 graft | 6 |
| H12 | 무동작 회로 | 새 칸 전부 빈 값 | 1 |
| H13 | 적층 toy, 판정식 성립 | 봉인 거부 + 세분 사유, 출발 기록만·탐색 계속 | 5 (v) |
| H14 | 판정식 불성립, Y 꺼짐 | 일반 사유, 면제 없음 | 5 (v) |
| H15 | H13에 X triode 선언 | 탐지 무발동, 게이트·영역 기록 | 5 (vi) |
| H16 | triode 정의역 밖 | 게이트 거부, 봉인 7 분류 아님 | 5 (iv) |
| H17 | 지켜지는 소자 있음·없음·d·s 끊김 | 집합 손계산 | N3.3 |
| H18 | `off` 선언 소자 | `on_structural` False, `sat_threshold` 호출 0 | N3.4 |
| H19 | 단좌표 변(L 고정 toy) | 상자 손계산, 만족 집합 두 구간이면 안 자름, 빈 집합이면 기록만 | H-B |
| H20 | 대칭 `zeros` toy | `search_domain` 계산 0, 필드 읽기, writer 1 | 12 |
| H21 | VDS-1 대조 표 | base ⊆ 새 길이 1, 차집합 원인 (i)~(iv) | 3 |
| H22 | `git grep`·규칙 L | `vds_saturation`·`_edge_nets` 0, 새 필드 규칙 L 통과 | 6, 12 |

자리: `E/tests/sizing/test_chain_graph.py`, `test_chain_judge.py`, `E/tests/search/test_iv_kvl_choice.py`, `E/tests/sizing/test_seal_triode.py`, `E/tests/graph/test_stack_candidates.py`. 파일명은 구조 규칙 H로 card에서 확정.

**완료 판정**(검증자): HC:546~585 그대로. WP-10 cProfile·중복 인자 계측 포함.

## 11. 미룬 측정(O-225)과 기본안

| 측정 | 없어서 정하지 못한 것 | 이 판의 기본안 | 표지 |
|---|---|---|---|
| M-H1 | L 결정 경로, U-H4 | 변경 없음 | 재점검 |
| M-H1b | LUT VS 축 0점, VDS 축 | VP 칸 None 갈래, on_mask 유도 | 재점검 |
| M-H1c | U-H14 근거 | 선언 없음, spec 승인 대기 | 재점검 |
| M-H2·M-H2b | 13회로 크기, N4 예측, 단좌표 발동 | 숫자 없음. N4는 규칙으로만 판정 | 재점검 |
| M-H3 | 후보 대 정본 집합, U-H2 | §7.1 직접 유도 | 재점검(다르면 사용자 질문) |
| M-H4 | 설명력 | 완료 8은 보고 항목 | 재점검 |
| M-H5 | SD-2 기준선 | 변화표에 base 수만 | 재점검 |
| M-H6 | 입력 창 비겹침, U-H3 | 사유 코드 정지 | 재점검 |
| writer_root 한 구간 | 차분 변 단순화 | F_exist 밖 교집합 | 재점검 |
| 칸당 시간 | O-224 비용 | 미측정 | 재점검 |
| cProfile 기준선(HC:509) | WP-10 비교 | 계획 v6.38.8 측정 게이트 표대로 | 닫힘 |

## 12. 멈춤·승인 항목

**[v1.16.3 -- S1·S2·S3·S5는 계획 v6.38.8(master `c0b41eee`, 승인 A-25)·위임 A-16~A-18로 닫힘, 착수를 막지 않는다. 기록으로 남김. S4는 LA-1a 보류와 함께 남음]**

- **S1 계획 정리(HC:42 착수 조건)**: HC-S·HC-1 착수 전 tol 잔재 줄 정리가 조건으로 적혀 있다. 이 design이 찾은 줄: HC:582(봉인 7·`sat_v` 순수 리팩터링), HC:331·515(`sat_v` 칸, J1), HC:420 D-1 '− tol'. O-224 '문언 변경 0'은 칸별 기록 범위이고 이 정리와 별개로 읽었다. 계획 v6.38.8에 넣을지 결정이 필요하다.
- **S2 게이트 처리**: HC:514 HC-D 선행 = HC-0, HC:505·509. O-225는 '계획 v6.38.8에서 항목별로 적고 승인'이라 적었다. 이 design은 그 승인을 전제로 쓰였고, 승인 전에는 착수할 수 없다.
- **S3 만들면 배선(절대원칙)**: (a) `f_exist` 구간 칸(`node_lo`·`node_hi`·`vr_*`)은 HC:228·516이 HC-1 몫으로 정했으나 엔진 소비자가 R6뿐이라 그 기간 소비자 0이다. 기본안 = 계획대로 HC-1이 만들고 toy로 잠근다(소비자 card 표 #16·#22). 대안 = 구간 칸을 첫 소비 card로 옮김(HC:516 문언 변경). (b) 단좌표 자르기 13회로 발동 0 가능. 둘 다 승인 요구.
- **S4 칸 범위 충돌(M3)**: D41:1899 'R6는 칸 0만'은 HC:254·417과 다르다. 이 design은 HC 쪽을 따른다. LA-1a가 칸 0만 부르면 이 칸별 기록이 사라진다. LA-1a 절의 계획 공백으로 남아 있다.
- **S5 O-224 읽기**: J6. 사용자 승인 때 확인이 필요하다. 필드 단위로만 읽어야 하면 O-224 (ii)로 돌아가 묻는다.

## 13. 40·41·42에 인계하는 줄(이 판에서 고치지 않음)

| 자리 | 고칠 내용 |
|---|---|
| D40:451 | `records`의 KVL 기록 문장: HC-1은 안 쓴다. `kvl_adjusted`·`kvl_macro_recheck`는 R6 쓰기이므로 `graph/start: records`에 둘 수 없다(M2) |
| D41:1772 | '`kvl_*`는 `records`, 충돌은 `conflicts`'를 `loop_conflicts`로. `kvl_unsatisfied{rows}`는 `LoopConflict.rows`와 같은 사실이라 삭제. `kvl_adjusted`·`kvl_macro_recheck`는 LA-1a가 자기 출력 자리를 정한다(자리가 없으면 멈춤) |
| D41:1773 | `StartConflict.quantity = "kvl"` → §6.2 `LoopConflict` |
| D40:481, D42 D-LA1a | `loop_conflicts` 제작 card = HC-1(m8). 층: HC-1은 S0, L0 값(m7)은 LA-1 design |
| D41:1794·1799·1901 | writer·파일 이름은 이 문서와 같음. 드라이버 꼴과 §5.3 인계 |
| D40:454, D40:2206, D42 D-TB1b | '미작성' → 이 문서, (a)(c)(d)(e)(g)(h) 닫힘 |
| D40 §2.4.8 | §2 표 행 추가, `device: dc_sat_v` 행(M7) |
| D42 D-NM1 | 일곱째 자리 = 공허(J3) |
| D41 §6.7-1·§6.1, 40 봉인 7 절 | 계획 N3.8: 제약 그래프 판정·칸·거르기, 사유 세분·게이트 |
| D40:2210, D41:686 | HC-S 인용 대상 = 이 문서 |
| `wt/_drafts` DQ §5.2·§5.3 | HC-S 시작 조건(M7) |

## 14. G·D40 항목 닫힘 표

| 항목 | 자리 |
|---|---|
| G-1 | §2, §5 |
| G-2 | §4 |
| G-3 | §8 |
| G-4 | §6.4, §6.5 |
| G-5 | §7.1, §7.4 |
| G-6 | §7.2 |
| G-7 | §5.2, §6.2, §7.2, §7.4 |
| G-8 | HC-O 몫, 이 판 밖 |
| G-10 | 연결 서명 = §7.1. skill 문서 신설은 별도 항목, 대조만 |
| G-11, G-12 | §5.1 |
| G-13 | §7.2 |
| D40:2206 (a) | §5.1 공허 |
| (b) | graph-consumption §4 |
| (c) | §4 |
| (d) | §5.1 |
| (e) | §4 |
| (f) | 구조 색 정의 = D40 §2.4.8 인용 |
| (g) | §5.1 |
| (h) | §5.1 `on_structural` |
