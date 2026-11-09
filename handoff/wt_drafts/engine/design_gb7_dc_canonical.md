# GB7 노드전압·가지전류 DC 정본 설계 (design_gb7_dc_canonical)

- 작성 2026-10-07. 설계 문서만 썼다(코드 없음, 저장소 읽기만).
- 기준: P = `chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(HEAD a21a24f, 행 번호), REQ = `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(맨 끝 '확정 사항'이 이 문서보다 우선), S6a = `_drafts/engine/6a_structure_prep.md` 1.2·1.6, 진단 = `spice_harness_report.md`·`ic11_two_stage_diag.md`·`nmcnr_diag.md`·`lut_coverage_study.md` 5절·`_drafts/prep_ud17_f26_f27.md` 1.2.
- `design_mod3_s1_graph.md`는 작성 시점에 없었다. 이 문서는 S1 입력을 S6a 1.2 필드로 가정하고, 그 문서가 나오면 4절 '입력' 열만 맞춘다.
- 표기: **[제안]** 이 문서의 기본안(원칙에서 유도), **[승인]** 회로 해석이라 사용자 승인 필요(9절), **[추측]** 실측 근거 없음.
- **[2026-10-07 개정 -- reference 검토 Q2·Q3·Q4·Q5·Q10 추천안 확정, 사용자 "B는 추천대로 해."]** 계획 worktree `plan-rev4` 커밋 `defdc24`: DEC-87(Hermite 보간·tol_V 2^p 환산), DEC-88(쓰기 소자 좌표 ln IDu, 봉인 2 = ID 환산 지표, 봉인 7 = `VDS − VDsat ≥ +tol_VDsat` VDSAT 열), DEC-89(레이아웃 뒤 재평가), DEC-90(SPICE 합격 보강), DEC-95 (3)(종속 소자 구조 우선순위 -- U1·U4 결정). 아래 [개정 Q*] 표시.

---

## 0. 왜 이 블록이 임계 경로인가 -- 오늘 실측 요약

| 실측(오늘) | 수치 | 출처 |
|---|---|---|
| 옛 엔진은 소자마다 VDS를 따로 정하고 노드전압을 `propagate_node_voltages()`로 사후 복원 | 복원 충돌 current_reuse 4건(0.2227 V), folded 4건(최대 1.6 V) | spice_harness_report 4단계 3, prep_ud17 1.2 |
| 같은 gate 넷을 공유하는 소자들이 요구하는 gate 전압 차 | Vbias2 0.89 V, Vbias3 0.65 V, Voc_des 0.55 V | spice_harness_report 4단계 3 |
| free-bias SPICE(회로가 스스로 DC를 찾음) | current_reuse·folded 모두 동작 안 함(gain -206/-173 dB, 출력 레일 고착) | spice_harness_report 3.1·3.2 |
| forced 모드 KCL 잔차(엔진 노드전압을 강제했을 때 고정원 전류) | Vy 198 µA, N64_63 -182 µA, folded X -4.3 mA | 같은 문서 3.1·3.2 |
| two_stage_ota | KVL ValueError(0.9172+0.9+0.5625 = 2.3797 V ≠ 1.8 V) | ic11_two_stage_diag 2 |
| nmcnr_amplifier | 모든 θ infeasible(M201 VDS 0.3 고정 → diode M203이 1.5 V 흡수 불가) | nmcnr_diag 1~3 |

결론: '노드전압 하나 = 정본'(DEC-31 P 226)이 구현되지 않아 생긴 결함이다. 이 설계는 **노드마다 writer 하나가 값을 쓰고, 소자 VGS/VDS/VSB는 그 차이로만 읽는다**(N3.4 P 394~396)를 자료구조와 풀이 순서로 강제한다.

---

## 1. 확정 구조와의 대응

| 확정 사항(REQ 466~473) | 이 블록에서의 구현 |
|---|---|
| 1. 단일 정본 graph, 필드마다 writer 1 + 입력 버전, 필드가 곧 캐시 | S2 `dc`의 모든 값은 `DcField` 레코드(2.1). 별도 memo 없음. 재사용 판정 = 입력 지문 일치(6절) |
| 2. 불변 스냅샷 + 구조 공유 | 후보 θ마다 새 `S2Dc`. 입력 지문이 같은 필드는 부모 스냅샷의 필드 객체를 그대로 참조 |
| 3. S3 = 설계점 단위 기록 | 이 블록은 S3에 실패 레코드·요약만 넘긴다(7절). 전체 스냅샷은 front 점·채택 해만 |
| 4. graph 밖은 LUT memo 하나 | VGS 역산·VDsat·ID/W·tol_V 조회는 `lut` memo만 쓴다. 이 블록은 다른 캐시를 만들지 않는다 |
| 5. 강제 test(setter 경유, writer 둘이면 FAIL, 같은 입력 재계산 FAIL) | 8.4 구조 test |
| 파일 구성 규칙 A~D | 5절 파일 목록 |
| 상수 금지(tol_V = LUT LOO) | tol_V, tol_I, K_max, 창 폭, test 허용치 모두 식(3.5·8절) |

---

## 2. S2 `dc` 데이터

### 2.1 필드 레코드(모든 `dc` 필드 공통)

`DcField{value, writer_id, tier ∈ {W0..W4, KCL, L, W, SEAL}, input_fp, version}` (frozen)
- `writer_id` = 이 필드를 쓰는 계산 블록 이름(+ 노드전압이면 쓰는 관계 id). writer 권한표(`sizing/writer_table.py`)에 없는 조합은 setter가 거부한다(SC-a P 404).
- `input_fp` = 이 필드가 읽은 필드들의 (필드 id, version) 정렬 튜플 + 읽은 θ 성분 `float.hex`의 지문. SC-e(P 408) reader 기록이 곧 이것이다.
- `version` = 이 필드 id의 단조 카운터. 값이 바뀔 때만 증가한다(입력이 바뀌어도 결과 값이 같으면 version 유지 -- 하류 재계산을 끊는다).

### 2.2 `S2Dc` 필드 묶음 [제안]

| 묶음 | 키 | 값 | writer(티어) | 비고 |
|---|---|---|---|---|
| `rail_v` | 레일 넷 | 전압 | W0 `w0_rails` | `supplies_v`만(DEC-60 P 254, 스칼라 vdd 폴백 없음 -- REQ C11) |
| `branch_i` | 가지 id | 전류, `source ∈ {kcl, declared, theta}` | KCL `block_currents`(②) | DEC-08 P 203 `value_dc_amp` 고정, DEC-70 P 264 θ 전류 기저 |
| `device_id` | 소자 | ID(부호 포함 방향) | ② | 가지 전류의 투영(소자 = 가지 멤버) |
| `l_class` | L 동치류 | L | L `block_lengths`(③) | N3.9 |
| `scc[k]` | 순환 블록 k | {노드전압들, 종속 gm_id들, 반복 기록{k, q, 잔차}} | W1/W2/W4 `block_columns`(④) | 노드전압의 유일한 출처. 비순환 노드는 크기 1 SCC로 같은 형태 |
| `node_v` | 노드 | `scc[k]`·`rail_v`·W3 값의 읽기 뷰 | (파생, 쓰지 않음) | 조회 편의 인덱스. 별도 저장 없음 |
| `path_values` | 노드 | [(관계 id, 그 관계가 함의하는 값)] | ④가 수렴 후 1회 | 봉인 1 입력. 관계 = 노드에 닿는 모든 VGS 등식·저항 강하·diode 등식 |
| `device_op` | 소자 | {ID, gm_id, L, W, VGS, VDS, VSB} | (VGS/VDS/VSB는 node_v 파생, gm_id는 θ 또는 `scc` 종속값) | `set_device_vds` 같은 API는 없다(N3.4 P 395) |
| `column_window` | 기둥 id | 내부 노드별 [lo, hi], `slack = min(VDS − VDsat)`과 그 소자 | ④ | W4 y 배정 범위이자 보고값. I-C10/U-20(P 980·1097)의 `stack_headroom_slack_v`를 대체 |
| `w` | 소자 | W | W `block_widths`(⑤) | W = ID / (ID/W)(gm_id, L, VDS, VSB) |
| `seal[1..8]` | 봉인 항목 | {잔차 최대, 허용오차, 위반 소자·노드} | SEAL `seal/item_*` | 3.6 |

`SealedSnapshot`은 `seal[1..8]`이 모두 통과한 `S2Dc`만 감싸는 별도 타입이다. `ss`·`ls` 계산 함수는 이 타입만 인자로 받는다(DEC-67 P 261).

### 2.3 writer 티어 → 노드 배정 (N3.4 P 382~397을 구조 규칙으로)

| 티어 | 노드 | 쓰는 관계 |
|---|---|---|
| W0 | `supply_nets` 전부 | `supplies_v` |
| W1 | diode 소자(g = d)의 drain(=gate) 노드 | V(d) = V(s) ± VGS(gm_id, L, VDS = \|V(d) − V(s)\|, VSB). 자기참조 1변수 |
| W2 | (a) G_vgs 트리 엣지로 정해지는 노드(소스 추종: 아는 쪽 단자에서 VGS만큼 떨어진 반대 단자) (b) DC 경로 저항의 먼 쪽 노드(V = V(near) ∓ I·R) (c) `kvl_branch` 등식 노드(DEC-64 P 258) (d) 입력 포트 DC 선언이 있는 포트 넷 | 3.2의 쓰기 계획 |
| W3 | spec `node_voltage_targets_v`에 선언된 노드 | 사람 선언 |
| W4 | 위 어디에도 속하지 않는 노드(고임피던스 drain 노드, 이상 전류원 양단, G_vgs 성분에 고정 노드가 없는 성분의 뿌리) | θ의 y 성분 → 기둥 창 안 위치 |

노드 하나에 위 규칙이 둘 이상 해당하면 **우선순위 W0 > W3 > W1 > W2 > W4로 하나만 writer**가 되고, 나머지 관계는 '비트리 관계'가 되어 그 관계에 든 소자의 gm_id를 종속시킨다(3.2). "먼저 쓴 값 존중"은 없다(P 394).

---

## 3. 풀이 방식

### 3.1 S0당 1회: 쓰기 계획 컴파일 (`writer_plan`)

입력: S1(노드·소자·레일·가지·기둥·관계 엣지 `equal_vgs`·`vds_eq_vgs`·`kvl_branch`, G_vgs 사이클 분류 DEC-64), S1v(CD 셀 source 노드, 버퍼 묶음 DEC-63), spec(W3 목표, 입력 DC 선언), θ 스키마 이전. 출력은 S1 층 graph 필드 `s1.dc_plan`(θ와 무관하므로 S0 지문에만 묶인다).

1. **고정 노드 집합 F** = W0 레일 ∪ W3 선언 노드 ∪ 입력 DC가 선언된 포트.
2. **G_vgs 방향 신장 숲**: G_vgs(MOS gate–source 엣지 + DC 경로 저항 엣지, P 용어집 G_vgs)에서 F를 뿌리로 BFS. 엣지 처리 순서는 (diode 엣지 → 그 밖, 같은 단계는 소자 이름 정렬, NFR-4)이다 [제안]. 트리 엣지 = **writer 소자**(독립 θ 성분 -- **[개정 Q3]** 좌표는 반전 좌표 ln IDu(DEC-88), gm_id는 파생 보고, 먼 쪽 노드를 W1/W2로 씀). **[개정 Q10 (v)]** 같은 관계(equal_vgs 묶음·kvl_branch 사이클) 안에서 어느 소자를 writer(독립)로 둘지는 ratified 선택 → diode → GB5가 gm을 요구하는 소자·뒤 stage 소자 → 대칭 궤도 대표 → 이름 순(DEC-95 (3)·DEC-64) -- BFS 엣지 처리 순서가 이 우선순위를 따른다. 비트리 엣지는 DEC-64 분류 그대로:
   - (v0) 같은 (gate, source) 평행 엣지 = `equal_vgs` → 그 소자 gm_id **종속**(VGS 정합 역산, 3.3 ③).
   - (v1) 입력 포트 둘을 지나는 사이클 → 입력 DC 차가 선언되면 등식, 아니면 '입력 DC 동일 가정'으로 기록하고 그 소자 gm_id 종속(차동쌍 둘째 소자).
   - (v2) `kvl_branch` → 멤버 하나 gm_id 종속(DEC-64 선택 규칙: ratified 선택, 없으면 **[개정 Q10 (v)]** 구조 우선순위 diode → GB5 gm 요구·뒤 stage → 대칭 궤도 대표 → 이름). 루프 가지 전류는 θ 전류 변수(DEC-70).
   - (VDS-1) drain–source 엣지 하나 포함 사이클 → 그 VDS 노드를 W1/W2로 쓰고 포화 하한 부등식으로만 남는다.
3. **G_vgs 성분에 고정 노드가 없으면** 그 성분의 뿌리(이름 정렬 첫 노드)를 W4 y로 둔다. G_vgs에 아예 없는 노드(채널 drain만 붙은 노드)도 W4.
4. **읽기 의존 그래프**: 노드 x의 writer가 읽는 노드(아는 쪽 단자, VDS를 위한 반대 채널 단자, VSB를 위한 bulk 레일)로 방향 엣지를 만들고 Tarjan SCC로 순환 블록을 만든다(SC-c P 406). SCC는 위상 순서로, SCC 안 노드는 쓰기 계획 BFS 순서로 정렬한다.
5. **DOF 표**: 독립 gm_id(트리 엣지 소자) + y(W4 노드) + θ 전류 기저 + 미선언 DC 저항 + L 동치류. 비트리 엣지 수 = 종속 gm_id 수. 이 표가 θ 스키마이며 N3.7 DOF(P 463) 구조 rank의 입력이다.
6. **영향 표**: θ 성분 → 그 성분을 (전이적으로) 읽는 필드 집합. 6절 재사용과 8.4 test의 기대값 원천.

컴파일 실패는 탐색 전 정지다: 노드가 어느 규칙으로도 writer를 못 받음(이론상 W4가 받으므로 발생 시 구조 결함) → `StructureUnresolvedError(undetermined)`, 한 노드에 writer 둘(우선순위 동률) → 같은 예외. 둘 다 N3.14 STRUCTURE_UNRESOLVED(P 734~).

### 3.2 후보 θ마다 블록 실행 순서 (N3.5 P 410: ②③④⑤ → 봉인)

1. **② `block_currents`**: S1 KCL 그래프 + θ 전류 기저 + `matching_ratio` + `value_dc_amp`로 `branch_i`, `device_id`. 노드전압을 읽지 않는다(gm/ID 매개화에서 VGS가 ID를 포함하지 않으므로, DEC-70 P 264). 단 **DC 경로 저항 전류**는 가지 전류에서 정해지므로 저항 강하가 노드전압을 쓰는 W2 관계가 된다(전류가 저항을 정하지 않는다).
2. **③ `block_lengths`**: L 동치류 L. 선언된 reads에 노드전압이 없어야 한다. 어떤 LR 규칙이 VDS를 읽으면 4의 의존 그래프에 자동으로 들어가 SCC가 커진다(별도 분기 없음).
3. **④ `block_columns`**: `rail_v` → SCC 위상 순서로 각 SCC를 푼다(3.3·3.4). SCC가 하나 끝날 때마다 그 노드들의 종속 gm_id를 같은 SCC 필드에 쓴다. 전부 끝나면 `path_values`, `column_window`를 쓴다.
4. **⑤ `block_widths`**: 소자마다 W = ID·L / IDu(**[개정 Q3]** 쓰기 소자는 θ 좌표에서 역산 없이, 종속 소자는 순방향 IDu에서 -- DEC-88. 옛 식 W = ID / (ID/W)(gm_id, L, VDS, VSB)와 같은 값). W_request로 W가 고정된 소자(MOD8 루프)는 반대로 gm_id를 (ID/W) 역산으로 종속시키고 그 소자는 3.1의 '독립 gm_id'에서 빠진다(θ 투영이 바뀌므로 S0 쓰기 계획을 다시 컴파일하지 않고 W 고정 집합을 계획의 입력으로 둔다) [제안].
5. **봉인**(3.6) → 통과 시 `SealedSnapshot`.

### 3.3 노드 하나를 쓰는 순서 -- gm_id 결정변수와 VGS 정합

writer 소자 m(트리 엣지, 아는 단자 a, 쓸 단자 x)에 대해:
1. **[개정 Q3]** 반전 좌표 ln IDu(m)는 θ에서 읽는다(DEC-88. gm_id(m)는 같은 점에서 파생). L은 ③, VSB·VDS는 현재 반복값(x 자신 포함 가능 → 자기참조면 SCC).
2. V(x) = V(a) ± VGS_LUT(ln IDu, L, VDS, VSB)(부호는 kind와 a가 gate인지 source인지로). 역산은 `lut.vgs_for_current_density`(강반전 분지 위 단조, Hermite 칸 안 bisection -- DEC-87·88) 하나만 쓴다.
3. 같은 노드 x에 닿는 **비트리 관계**마다(같은 gate를 공유하는 미러 멤버, 차동쌍 둘째 소자 등) 그 소자 n의 좌표를 **VGS 정합으로 순방향 계산**한다: VGS(n) := V(g) − V(s)(노드값), ln IDu(n) = LUT 순방향(VGS(n), L, VDS, VSB), gm_id(n)는 같은 점의 파생값. gm_id가 LUT 곡선 밖이면 LR3(P 507) 축 밖 → SEAL_VIOLATION(`lut_axis_out_of_range`).
4. 결과: **같은 gate 넷에 소자마다 다른 전압을 요구하는 상태는 표현할 수 없다**. 옛 엔진의 0.89 V(Vbias2)는 구조적으로 0이고, 남는 것은 LUT 순방향/역방향 보간 차뿐이며 그것을 봉인 2가 tol_V로 잰다.

### 3.4 순환 블록 풀이 (SC-c, N3.6 P 441, DEC-32 P 227)

- **창**: SCC 노드 x의 창 [lo_x, hi_x] = x를 지나는 기둥들의 (아래 레일 + x 아래 소자들의 VDsat 합, 위 레일 − x 위 소자들의 VDsat 합)의 교집합. VDsat는 `lut.vdsat`(**[개정 Q1·Q3]** U-27 재생성 LUT의 VDSAT 열 보간 -- 오라클 `@m[vdsat]`과 같은 양, DF-25 대체. 옛 'LUT (ID, gds, VDS)에서 유도' 폐기. 열 전에는 창·봉인 7이 '정의 미확정'이고 2/(gm/ID)를 대신 쓰지 않는다)를 현재 반복값으로 조회한다. 창이 비면(lo > hi) 풀기 전에 SEAL_VIOLATION 항목 7, margin = (lo − hi)/tol_V(nmcnr 실패가 '배정할 곳 없음' ValueError 대신 이 margin으로 나간다).
- **1변수 SCC(diode W1, 소스 추종 W2 자기참조)**: f(V) = V − V_target(V). 소스 추종 nmos는 V(s)가 오르면 VSB가 올라 VGS가 커져 V_target이 내려가므로 f는 단조 증가 → 창 양 끝 부호가 다르면 bisection, 같으면 근 없음 → SEAL_VIOLATION(항목 6 또는 7, 창 끝이 레일/bulk에서 왔으면 6, VDsat에서 왔으면 7). 창 끝에서 단조성 검사(LUT 곡선 검사 N3.7 P 460)가 실패한 구간은 격자 전수 폴백 + 사유 기록(DEC-71 (4) 같은 처리).
- **다변수 SCC**: SCC 안 노드 순서대로 Gauss-Seidel 고정점 반복. 매 반복 q = \|Δk\| / \|Δk−1\|(반복 3개부터), q < 1이면 q^(K_max − k)·\|Δk\|/(1 − q) > tol_V일 때, q ≥ 1이면 K_max 도달 때 NONCONVERGENT(P 441 그대로).
- **K_max = ceil(log2(W_scc / tol_V))**, W_scc = SCC 노드 창 폭의 최댓값(창 폭은 그 노드 기둥의 레일 전압차 이하이므로 상수가 아님). 1변수 bisection도 같은 식이 반복 수다.
- 수렴 판정: 모든 SCC 노드에서 \|Δ\| ≤ tol_V. 시작값: 부모 스냅샷(S2p)의 같은 SCC 값이 있으면 그것(힌트로만, P 367), 없으면 창 중앙.
- W4 노드: y ∈ [0, 1]을 창 안 위치로 사상(V = lo + y·(hi − lo)) [제안 -- θ bounds가 고정이고 창이 θ를 따라 움직여도 y가 창 밖을 가리키지 못한다]. 창 자체가 VDsat(현재 반복값)에 의존하므로 W4 노드는 그 기둥의 SCC에 함께 든다.

### 3.5 허용오차 (N3.6 P 437~442)

- `tol_V` = `lut/tolerance.py`의 (kind, w_key, L 점, VDS)별 LOO 보간 오차 최댓값(**[개정 Q2]** 운영 보간과 같은 축별 Hermite로 재고 2^p 환산, DEC-87). LUT 지문당 1회(LUT memo). **[개정 Q3]** 봉인 2·3·SCC 수렴은 ID 환산 지표(id_equivalent), 봉인 7은 VDSAT 열 LOO `tol_VDsat`(DEC-88).
- `tol_I`(SCC별) = tol_V × max gm(그 SCC 소자). gm은 S2p의 `ss` 값, 첫 평가는 LUT 격자 최댓값(P 440).
- KCL 항목 3은 노드가 속한 SCC의 tol_I, SCC 밖 노드(레일 직결)는 그 노드에 붙은 소자들의 SCC 중 최대 tol_I [제안].

### 3.6 봉인 8항목 = 계산 블록 8개 (N3.6 P 424~435)

봉인 항목은 **writer 경로를 재사용하지 않는다**: 항목 1·2·8은 순방향 `lut.query`(VGS = f(gm_id, L, VDS, VSB))로 최종 노드값에서 다시 계산한다. 쓰는 쪽(역산)과 재는 쪽(순방향)이 같은 함수면 봉인이 자기 확인이 되기 때문이다.

| # | 파일(계산 블록) | 읽는 필드 | 판정 | 실패 detail |
|---|---|---|---|---|
| 1 | `seal/item1_node_conflict.py` | `path_values` | 노드별 max − min ≤ tol_V | 노드, 관계 id 쌍 |
| 2 | `seal/item2_vgs_match.py` | `device_op`, `rail_v`, `scc[*]` | **[개정 Q3]** 모든 소자 \|ln IDu_LUT(노드 VGS) − ln IDu(좌표)\| / (gm/ID) ≤ tol_V(ID 환산 지표, DEC-88) | 소자 |
| 3 | `seal/item3_kcl.py` | `branch_i`, `device_id`, 저항 θ, `node_v` | 내부 노드 \|ΣI\| ≤ tol_I(`exclude_nets`는 사유 선언 넷만) | 노드 |
| 4 | `seal/item4_versions.py` | 모든 파생 필드의 `input_fp` | 기록된 입력 version = 현재 version(정확 일치, SC-b) | 필드 id |
| 5 | `seal/item5_writer_unique.py` | `s1.dc_plan`, 필드 `writer_id` | 노드마다 writer 1, 권한표 일치 | 노드 |
| 6 | `seal/item6_bulk_reverse.py` | `node_v`, 소자 bulk | 순바이어스 크기 ≤ tol_V(DEC-61 P 255) | 소자, 접합 |
| 7 | `seal/item7_saturation.py` | `device_op`, `lut.vdsat` | **[개정 Q3 (ii) (C)]** ID > 0인 MOS VDS − VDsat ≥ +tol_VDsat(VDSAT 열, `intended_region: linear` 선언 소자 제외. 옛 `≥ −tol_V` 대체 -- 엔진이 SPICE `vds_ge_vdsat`보다 보수) | 소자 |
| 8 | `seal/item8_kvl_branch.py` | `kvl_branch` 엣지, `device_op` | \|Σ VGS_LUT − ΔV\| ≤ 멤버 수 × tol_V(DEC-64 v2) | 사이클 id |

- 각 항목은 자기 필드 `seal[i]`를 쓰는 계산 블록이고 reads가 다르므로 θ 한 성분이 바뀌어도 그 성분이 닿는 항목만 다시 잰다(6절).
- `seal/seal.py`(진입점 하나)는 8항목 필드를 모아 전부 통과면 `SealedSnapshot`으로 승격, 하나라도 실패면 위반 크기가 가장 큰 항목으로 `SealViolationError(item, devices, magnitude)`를 낸다(모든 항목 결과는 실패 레코드 detail에 남김 -- 첫 실패에서 멈추지 않는다).
- 항목 5는 S0 컴파일에서 이미 참이어야 하는 성질이라 런타임에는 '계획과 실제 필드 writer 대조'만 한다(구현 결함 탐지용).

---

## 4. 블록별 입력 필드와 무효화

| 블록 | 읽는 것 | 쓰는 것 | 무효화 조건(입력 지문이 바뀌는 경우) |
|---|---|---|---|
| `writer_plan` | S1(노드·소자·관계 엣지·기둥·G_vgs 분류), S1v(CD source), spec(W3·입력 DC), W 고정 집합 | `s1.dc_plan` | S0 지문, W 고정 집합 |
| `w0_rails` | spec `supplies_v` | `rail_v` | spec 지문 |
| ② `block_currents` | θ 전류 기저, `matching_ratio`, `value_dc_amp`, S1 KCL | `branch_i`, `device_id` | θ 전류 성분 |
| ③ `block_lengths` | θ L 성분, LR 입력 | `l_class` | θ L 성분 |
| ④ `block_columns`(SCC마다 한 필드) | `rail_v`, 앞 SCC 노드값, 그 SCC 소자의 θ gm_id·`l_class`·`device_id`(저항 강하), y | `scc[k]`, `path_values`, `column_window` | 그 SCC가 읽는 성분만. 앞 SCC의 version이 그대로면 재사용 |
| ⑤ `block_widths`(소자마다 한 필드) | `device_id`, gm_id, `l_class`, 그 소자 VDS·VSB | `w[dev]` | 그 소자의 다섯 값 중 하나 |
| 봉인 i | 3.6 표 | `seal[i]` | 표의 읽기 필드 |
| `tol_V` | LUT | (LUT memo) | LUT 파일 |

SCC를 필드 단위로 둔 이유: FD 한 스텝이 θ 성분 하나를 움직이면(옛 엔진 실측 바뀐 소자 6.7/51인데 전부 재계산, REQ 4.3 #6) 그 성분이 닿는 SCC와 그 하류만 version이 오른다.

---

## 5. 파일 목록 (규칙 A~D, REQ 1.2)

`gmid_engine/sizing/`(MOD4) -- 파일 하나 = 진입점 하나(A), 계산 블록 하나(C), test 1:1(D).

| 파일 | 진입점 | 계산 블록 | 층 |
|---|---|---|---|
| `s2_model.py` | `S2Dc`·`DcField`·`SealedSnapshot`(타입만, 데코레이터 등록 없음) | 없음 | 0 |
| `writer_table.py` | `writer_for(field_id) -> WriterSpec`(티어 권한표 상수 표 하나) | 없음 | 0 |
| `setter.py` | `put(snapshot_builder, field_id, value, writer_id, input_fp)` -- 유일한 쓰기 경로(권한·version 처리) | 없음 | 1 |
| `field_reuse.py` | `reuse_or_compute(parent, field_id, input_fp, fn)` -- 입력 지문 일치 시 부모 필드 공유 | 없음 | 1 |
| `writer_plan.py` | `compile_writer_plan(s1, s1v, spec, w_fixed) -> DcPlan` | `writer_plan` | 2 |
| `w0_rails.py` | `write_rails` | `w0_rails` | 2 |
| `block_currents.py` | ② | ② | 2 |
| `block_lengths.py` | ③ | ③ | 2 |
| `block_columns.py` | ④(SCC 순회·필드 쓰기) | ④ | 3 |
| `_helpers_columns.py`(helper) | 창 계산·VGS 등식 1개 평가·종속 gm_id 역산(④ 전용) | -- | 2 |
| `block_widths.py` | ⑤ | ⑤ | 4 |
| `seal/item1_node_conflict.py` … `seal/item8_kvl_branch.py` | 항목별 판정 | 항목마다 1 | 5 |
| `seal/tol_i.py` | SCC별 tol_I | `tol_i` | 4 |
| `seal/seal.py` | `seal(s2dc) -> SealedSnapshot` | 없음(조립·승격만) | 6 |
| `size_and_seal.py` | `size_and_seal(ctx, theta, parent) -> SealedSnapshot`(공개 API, REQ 3.2) | 없음 | 7 |

`gmid_engine/core/`(층 0, 수학만 -- 층 0 DEC-71 (4)(d) 국소 고정점도 같은 규칙을 쓰므로 core에 둔다): `bisect_root.py`(창·단조 함수 bisection), `fixed_point_iter.py`(Gauss-Seidel + q 규칙), `k_max.py`(K_max 식). `lut/`: `inverse.py`, `vdsat.py`, `tolerance.py`, `query.py`(기존 REQ 3.1 표 그대로, 이 블록은 소비만).

test: `tests/sizing/test_<file>.py` 1:1 + `tests/contracts/`(IC1·IC2·IC10·IC11, SC-a~e) + `tests/oracles/test_spice_free_nodes.py`(8.3).

---

## 6. 반복 계산 방지 (확정 사항 1·2·4·5)

1. **필드가 곧 캐시**: 블록은 `field_reuse.reuse_or_compute`로만 필드를 만든다. 입력 지문 = (읽은 필드 id, version) + 읽은 θ 성분 `float.hex`. 부모 스냅샷의 같은 필드 `input_fp`와 같으면 **객체를 그대로 참조**(계산 0), 다르면 계산 후 값이 같으면 version 유지.
2. **부모 선택**: 탐색 층이 `size_and_seal(ctx, theta, parent)`의 parent를 넘긴다 -- FD 스텝은 기준점 스냅샷, SLSQP 다음 반복은 직전 반복, 층 0 조립점 검증은 조립점. parent가 없으면 전 필드 계산.
3. **같은 θ 재방문**: 평가 단위 결과는 S3 evals 요약(θ `float.hex`, S0 지문 키, 실패 포함 -- P 416)에서 돌려준다. 전체 스냅샷이 필요하면 결정론적 재생성.
4. **SCC 내부 반복**은 같은 입력의 재계산이 아니라 입력(반복값)이 바뀌는 계산이다. 반복마다 LUT 조회는 LUT memo가 받는다(같은 (kind, L, VDS, VSB, gm_id) 재조회 = memo hit).
5. **금지**: 모듈 전역 dict·`lru_cache`·인스턴스 캐시(lint FAIL), `setdefault`로 기존 값 건너뛰기(SC-b), 블록 안에서 S1/topology 재로드(REQ 4.3 #1 99.3% 사례).

---

## 7. 실패 규약 (N3.14 P 734~751)

| 상황 | 시점 | 예외 / 실패 레코드 class | margin(무차원) |
|---|---|---|---|
| writer 미배정·writer 둘(계획 컴파일) | S0, 탐색 전 | `StructureUnresolvedError`(STRUCTURE_UNRESOLVED, exit 2) | -- |
| 창이 빔(lo > hi) | ④ 풀기 전 | `SealViolationError(item=7, detail=empty_window)` | (lo − hi)/tol_V |
| bisection 창 안에 근 없음 | ④ | `SealViolationError(item=6 또는 7, detail=no_root_in_window)` | 창 끝 \|f\|/tol_V 중 작은 값 |
| 종속 gm_id·VGS 역산이 LUT 축 밖 | ④(3.3 단계 3) | `SealViolationError(detail=lut_axis_out_of_range)`(LR3) | 축 경계까지 거리/tol_V |
| SCC 반복 상한·수축 불가 확정 | ④ | `NonconvergentError(residual)`(NONCONVERGENT, exit 4) | 잔차/tol_V |
| 봉인 항목 1~8 위반 | 봉인 | `SealViolationError(item, devices, magnitude)`(SEAL_VIOLATION, exit 5) | 위반/tol_V 또는 tol_I |

- 탐색 루프는 `CANDIDATE_FAILURE_CLASSES = (SealViolationError, NonconvergentError)`만 이름으로 잡아 S3 실패 레코드 {class, devices, margin, detail}로 기록하고 다음 후보로 간다. 기반 `InfeasibleSizingError`와 `ValueError`는 잡지 않는다(P 749).
- margin이 연속값이므로 SLSQP 제약 함수가 상수 페널티 대신 이 값을 쓴다(P 416). 옛 엔진의 "배정할 곳이 없다" ValueError(nmcnr)와 KVL ValueError(two_stage)가 이 경로로 바뀐다.

---

## 8. test 계획

기대값은 피검 함수를 부르지 않고 만든다(작성자 ≠ 검증자). 허용치도 상수 금지: 등식 test는 부동소수 한계 `n·eps·|ΔV|`(n = 합하는 항 수, eps = `sys.float_info.epsilon`), 근사 test는 tol_V·tol_I.

### 8.1 불변식 (9회로 + 픽스처, `tests/contracts/`)

| test | 판정 | 독립 근거 |
|---|---|---|
| `test_kvl_sum_equals_rail` | 모든 기둥(S1 열거를 test가 topology JSON에서 따로 셈): Σ VDS + Σ 저항 강하 = 레일 전압차, \|차\| ≤ n·eps·ΔV | KVL 정의. 노드값 하나 원칙이면 항등이라 실패 = 경로별 VDS 저장 회귀 |
| `test_vgs_consistency_all_devices`(IC1 P 821) | 모든 소자 \|V(g) − V(s) − VGS\| ≤ tol_V, VGS는 test가 npz를 `scipy.interpolate.RegularGridInterpolator`로 직접 보간 | LUT 파일 |
| `test_kcl_residual` | 내부 노드 \|ΣI\| ≤ tol_I, 소자 전류는 test가 (W, L, VGS, VDS, VSB)에서 npz로 다시 계산 | LUT 파일 + KCL |
| `test_shared_gate_single_voltage` | 같은 gate 넷 소자들의 요구 gate 전압 최대 차 ≤ tol_V | spice_harness 4단계 3 지표(옛 0.89 V) |
| `test_rail_origin_shift_invariance`(IC11 P 831) | (vdd 1.8, gnd 0) 대 (0.9, −0.9): VGS·VDS·VSB·gm_id·W ≤ tol_V 감도 전파값 | 원점 이동 불변 |
| `test_order_shuffle_invariance`(IC2 P 822) | 소자 순서·`PYTHONHASHSEED` 섞기 → 이산 필드 일치, 노드 ≤ tol_V | 결정론 |

### 8.2 손계산 픽스처 (`tests/sizing/`, toy LUT = 제곱법칙 해석식으로 만든 npz 픽스처)

| # | 픽스처 | 손계산 기대 |
|---|---|---|
| F1 | 2소자 기둥: diode nmos + pmos 전류원 | V(x) = Vth + sqrt(2ID/(k·W/L)) 닫힌 꼴, VDS(pmos) = VDD − V(x) |
| F2 | 소스 추종 1변수(체효과 γ) | V(s) 닫힌 꼴 근(2차식), bisection 반복 수 = ceil(log2(창/tol_V)) |
| F3 | 미러(diode + 출력 소자, VDS 다름) | 출력 소자 gm_id = 역산 해석값, VGS 차 = 0 |
| F4 | 2노드 SCC, 수축비 q 알려진 선형 사상 | 반복 수 ≤ K_max, 수렴값 해석해 |
| F5 | q ≥ 1 사상 | `NonconvergentError`(거부 먼저 확인) |
| F6 | 창이 비는 기둥(VDD < ΣVDsat) | SEAL_VIOLATION 항목 7, margin 손계산 |
| F7 | 옛 vsb version으로 만든 W를 넣은 스냅샷(SC-b P 405) | 봉인 4 거부 |
| F8 | 한 노드에 W3 선언 둘 | 계획 컴파일 `StructureUnresolvedError` |
| F9 | two_stage 축소형(M1~M5, 이름 없는 toy) | KVL 항등, M4 gm_id 종속 = 역산값, ValueError 없음 |

### 8.3 SPICE free 모드 합격 판정과 노드전압 기록 (`tools/spice_oracle`, `tests/oracles/`)

- 넷리스트: spice_harness 규칙 재사용(모델·코너·온도 LUT 메타, finger = nf=1 병렬, 폭 = E5 PDK 특성화 폭). `--bias free`, `.nodeset`은 엔진 노드값(초기값일 뿐).
- **[개정 Q4 (v)·Q6]** 넷리스트 기하 = MOD8 수렴 스냅샷의 (finger_w, nf, 행 확산 기하 ad/as/pd/ps), 접합 용량 포함(계획 LY8·DEC-91). sizing 직후 기하는 진단 실행만.
- 판정 1(동작): `intended_region` 밖 MOS 전부 SPICE 포화(\|VDS\| ≥ \|VDSAT\|). **[개정 Q5 (i)]** 엔진이 전도로 예측한 MOS가 SPICE에서 꺼지면(ID 크기 < `off_current_A[소자]`, 엔진이 LUT VGS = 0 누설 ID로 계산해 넘김) FAIL(DEC-90 (1)). 옛 엔진은 current_reuse 30/51, folded 5/13.
- 판정 2(성능): 선언된 성능 제약 중 오라클이 측정하는 것 전부(**[개정 Q5 (ii)]** CMRR·PSRR 포함)를 SPICE 측정값이 만족(계획 T5). 슬루·정착은 측정·기록만, 측정 불가 제약은 `spice_unverifiable[]`로 사전 보고(DEC-90). 합격 조건은 판정 1·2 둘뿐이다(사용자 확정 2026-10-07 8번, 계획 N3.6).
- 기록(노드, 합격 조건 아님): 티어별 \|V_spice − V_engine\|과 소자 ID/gm/gds 차를 T8 모델 오차 기록에 남긴다. W4 고임피던스 노드는 free 모드에서 gds 균형으로 정해져 차가 클 수 있음을 기록에 표시한다.
- 경고(forced 모드에서만, 합격 조건 아님): 노드를 엔진 예측 전압에 강제한 상태의 소자 ID·gm 차(고정원 전류 = 엔진 노드값의 KCL 잔차 포함, 옛 Vy 198 µA)가 LUT로 계산한 허용오차(`tol_V` ID 환산 지표 계열·`tol_I`)를 넘으면 엔진·LUT 결함 신호로 맨 앞에 모은다.
- 대상: 엔진이 해를 내는 회로 전부(9회로 목표), 결과는 넷리스트 sha256 키 디스크 캐시(E3).

### 8.4 구조·재사용 test (`tests/structure/`, 확정 사항 5)

`test_dc_fields_only_via_setter`(원시 대입·전역 캐시 lint 0), `test_one_writer_per_field`(권한표에서 같은 필드 writer 둘 → FAIL), `test_same_input_no_recompute`(같은 θ·parent로 두 번 → 계산 호출 0), `test_fd_step_recomputes_impact_set_only`(θ 한 성분 섭동 → 재계산 필드 집합 = 영향 표, 기대 집합은 F9 손도식에서), `test_seal_uses_forward_lut`(봉인 1·2·8이 `lut.inverse`를 import하지 않음, AST), `test_no_compensation_writes_dc`(MOD5 이상 패키지에서 `sizing.setter` import 0 -- DEC-70).

---

## 9. 옛 엔진 실패를 구조적으로 막는 방식

| 실패(근거) | 옛 원인 | 이 설계에서 막는 구조 | 확인 test |
|---|---|---|---|
| two_stage 원인 A(ic11 3) | compensation(AC)이 탐색으로 고른 VDS를 `set_device_vds`로 확정 기입 | DC 필드 writer 권한표에 AC 블록이 없다(DEC-70). VDS는 저장 필드가 아니라 노드 차 파생. 보상은 봉인 뒤 θ 제약으로만 | `test_no_compensation_writes_dc`, F9 |
| two_stage 원인 B | 노드 CS를 공유하는 두 가지 중 한쪽에 slack 없음(그룹별 VDS 합 검증) | 가지별 VDS 배분이 없다. 노드 CS의 writer는 하나(입력 DC − VGS(M1)), 나머지 VDS는 파생이라 Σ = 레일차가 항등. 포화 부족은 봉인 7 margin | `test_kvl_sum_equals_rail` |
| two_stage 원인 C | 공유 gate·source 미러(M3 diode/M4)의 VGS 동일성 미강제, vds 같을 때만 검사 | `equal_vgs` 비트리 엣지 → M4 gm_id 종속 역산(3.3). VGS 차를 표현할 수 없음 + 봉인 2 순방향 재확인 | F3, `test_shared_gate_single_voltage` |
| nmcnr `stage2_diode_ref`(nmcnr_diag 3) | M201 VDS 0.3 고정 후 diode M203 창 [0.6375, 0.975]이 1.5 V 흡수 불가, diode 예약을 role min_vds로 셈 | NodeC의 writer = diode M203(W1, VGS=VDS 자기일관 bisection). M201 VDS = vdd − V(NodeC) 파생. 예약·배분 없음. 창은 VDsat(LUT)에서 계산 | F1, F6 |
| nmcnr NodeTail KCL 1779 µA(nmcnr_diag 3.3) | 가지 전류 출처 다중 | 가지 전류는 ② 한 곳(KCL 기저), 봉인 3 | `test_kcl_residual` |
| folded F27(prep_ud17 1.2) | 이름순 첫 경로 값을 노드에 박고 나중 경로는 conflicts에만, 충돌해도 진행 | 경로 전파가 없다. writer는 계획이 정한 하나, 다른 관계는 종속 gm_id 또는 봉인 1 실패(진행 안 함) | 봉인 1, F8 |
| folded M7 vsb −0.65(순바이어스) | vsb를 먼저 박힌 비물리 노드값에서 유도 | VSB는 노드값 파생(DEC-61), 순바이어스는 봉인 6 | `test_rail_origin_shift_invariance`, 봉인 6 |
| folded M5 Y 기둥 KVL 미닫힘 | fold_group singleton 우회 | 기둥 KVL 항등(노드값 하나), 우회 분기 없음 | `test_kvl_sum_equals_rail` |
| current_reuse Vom1 이중 구속 0.9 대 0.677 V | 기둥과 출력단 VGS가 같은 노드를 각자 정함 | 우선순위 규칙으로 writer 하나, 다른 쪽 소자 gm_id 종속 | `test_shared_gate_single_voltage` |
| current_reuse free SPICE 불능 | 위 충돌 합 | 봉인 1·2·3 통과 스냅샷만 내보냄 | 8.3 판정 1·3 |
| DF-01 낡은 vsb로 계산된 W(7/51) | `setdefault`, 버전 혼재 | 필드 input_fp + 봉인 4 | F7 |

참고: folded M1·M2 극성(UD-17a)과 current_reuse Iref 값(1.2 µA 대 엔진 0.199 µA)은 이 설계로 풀리지 않는다 -- connectivity·선언 문제다(U6·U7).

---

## 10. 사용자 승인 항목 (회로 해석만, 확정 사항 6)

| # | 항목 | 기본안 [제안] | 걸리는 회로(근거) |
|---|---|---|---|
| U1 | `equal_vgs` 그룹에서 어느 소자 gm_id를 독립으로 둘지(쓰기 계획 트리의 writer 소자 선택) | **결정됨 (2026-10-07, Q10 (v), 계획 DEC-95 (3))**: diode 멤버가 writer, 없으면 GB5가 gm을 요구하는 소자·뒤 stage 소자를 독립으로 남기고 → 대칭 궤도 대표 → 이름. '이름 전단사 후 front 정규화 해시 동일' metamorphic test | two_stage M3/M4(ic11 F2-Ha/Hb/nmcnr 선례), current_reuse Vbias2 {M2a, M2b, M58, M57}·Vbias3 묶음 |
| U2 | 입력 포트 DC가 spec에 없을 때: (a) W4 자유 변수(창 안, 결과에 '요구 입력 공통모드'로 보고) (b) 선언 필수(없으면 정지) | (a) | two_stage CS 노드(ic11 4 마지막 질문), 차동 입력 회로 전부 |
| U3 | 출력 공통모드 등 W3 노드 목표 목록(`node_voltage_targets_v`) | 선언된 것만 W3, 나머지 W4 | current_reuse Voc_des·Vom1/Vop1, folded out |
| U4 | `kvl_branch` 종속 멤버 선택(J12-f) | **결정됨 (2026-10-07, Q10 (v))**: J12-f ratified 선택, 없으면 U1과 같은 구조 우선순위(DEC-64 개정) | sf_pushpull {M18, M19, M21, M22}, pushpull {M1~M4}, 파일럿 v2 4 |
| U5 | SPICE free 대조에서 W4 고임피던스 노드 판정 방식 | **해소(사용자 확정 2026-10-07 8번)**: 노드전압은 합격 조건이 아니라 기록만, 경고는 forced 모드에서만(8.3) | 고이득 출력노드가 있는 회로 전부(spice_harness 4단계 8) |
| U6 | folded M1·M2 극성/단자(UD-17a) | -- (connectivity, 사용자만 수정) | folded |
| U7 | 값 선언 이상 전류원과 θ의 관계(DEC-08 고정 확인) | 선언값 고정, θ와 공존 시 로드 거부(DEC-08 그대로) | current_reuse Iref |
| U8 | 이상 전류원 가지 전압 = W4 자유 변수(J13) | W4 | 이상원 포함 회로(DEC-71 (1)) |
| U9 | 선형 영역 의도 소자 선언(`intended_region`) 목록 | 선언 0(전부 포화 검사) | 9회로 공통(봉인 7) |
| U10 | **[개정 Q4 (ii)(iii)]** 레이아웃 뒤 재평가 | 결정됨(2026-10-07, 계획 DEC-89·LY7): MOD7 결과마다 실현 기하로 이 커널 1회 + 봉인 1~8, diode도 노드전압·봉인 재계산. 이 블록 쪽 요구 = 폭 키(finger_w 슬라이스)가 `device_op` 입력 버전에 들어가 바뀐 소자만 miss | 9회로 공통 |

회로 해석이 아닌 결정(이 문서가 기본안으로 확정): W1 > W2 우선순위와 G_vgs BFS 처리 순서(3.1), y의 창 정규화(3.4), SCC 필드 단위(4절), tol_I 귀속(3.5), 봉인 순방향 재계산(3.6).
