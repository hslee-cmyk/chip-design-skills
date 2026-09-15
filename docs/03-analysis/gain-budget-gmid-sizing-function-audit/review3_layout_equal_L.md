# L을 같게 맞추면 레이아웃이 정말 단순해지는가 -- 레이아웃 관점 검토 (review3)

- 검토일: 2026-09-15. 저장소는 수정하지 않았다. 스크립트와 결과는 이 폴더에 있다.
- 산출물: `measure_equal_L.py` → `summary.txt`, `results.jsonl` / `overhead_check.py` → `overhead_check.txt`
- 입력: 기존 `workspaces/*/*.instance.json` 4개(two_stage_ota, folded_cascode, nmcnr_amplifier, current_reuse_telescopic_ota)의 `netlist`와 `topology_ref`. 넷리스트를 손으로 새로 입력하지 않았다. 사이징 탐색도 돌리지 않았다.

---

## 0. 결론 요약

| 조건 | L을 같게 맞추면 단순해지나 | 근거 |
|---|---|---|
| 서로 다른 물리 행(kind가 다르거나 stack이 다른 경우) | **아니다.** 효과가 0이다 | 행 폭은 행마다 따로 계산된다(`stick_diagram.py:6450-6467`). 오일러 판정은 L을 보지 않는다(`5361-5470`). 4개 회로 중 3개는 행 안 L 혼재가 0개라 행별 L 통일이 아무것도 바꾸지 않았다 |
| 같은 행, 매칭 그룹 | 이미 강제돼 있다(LR2) | 실측한 매칭쌍 중 같은 행에서 L이 다른 쌍은 0개였다(4개 회로 전체) |
| 같은 행, 매칭이 아닌 직렬 소자(확산 공유) | **엔진 기준으로는 아니다.** 물리적으로는 조금 단순해진다(게이트 격자가 규칙적이 되고, dummy·LOD 환경이 균일해진다). 대신 L을 올려 맞추면 면적이 늘어난다 | sky130 규칙은 poly 간격이 L과 무관하고 poly pitch도 고정돼 있지 않다. 실측: L을 행 최댓값으로 맞추면 행 폭 합 +11.4%, 게이트 면적 +15.3%였다 |
| L 통일과 함께 W를 다시 사이징하는 경우(W∝L) | **오히려 나빠질 수 있다** | W 비율이 바뀌어 공통 finger_w가 사라진다. 실측: 최댓값으로 맞추면 `assign_finger_geometry` ValueError, 최솟값으로 맞추면 finger 213→1340개, box 비율 12.96→1285.9 |
| 입력-캐스코드 쌍 | 같은 행에 있는 경우는 telescopic 1개 회로뿐이다. 거기서도 엔진상 이득은 0이고 면적은 늘어난다. 파일럿·folded·nmcnr에서는 두 소자가 다른 행이라 효과가 0이다 | §2.3 |
| FinFET 등 제한 규칙 공정(허용 L 2~3개, 고정 CPP) | **그렇다(사실상 필수)** | §3.2. 이 프로젝트의 sky130에는 해당하지 않는다 |

한 줄 결론: 이 엔진에서 한 행을 단순하게 만드는 변수는 L이 같은지가 아니다. **W 비율이 공통 finger_w의 정수배로 떨어지는지**가 결정한다. L을 같게 맞추는 조치는 매칭(LR2)과 제한 규칙 공정에서만 레이아웃 이득이 있다.

---

## 1. 엔진에서 L이 레이아웃에 들어가는 경로 (코드 추적)

### 1.1 L이 직접 들어가는 곳

| 경로 | 위치 | 동작 |
|---|---|---|
| `Transistor.l` | `stick_diagram.py:63` | 선택 필드. 없으면 그 행은 근사(approx) 계산으로 처리된다 |
| `pitch(l)` | `:6411-6420` | `l + PROCESS_GEOMETRY["finger_pitch_overhead_m"]`. 오버헤드는 **0**이다(`:6407`, sky130 CPP 미확보). 오버헤드 항 자체가 L과 무관하다 |
| `compute_row_geometry` | `:6432-6468` | 행 폭 = Σ n_fingers × pitch(l). docstring(`:6435-6437`)에 "한 행 안에 서로 다른 l이 섞여도 각자의 pitch로 계산"이라고 **명시돼 있다**. 반면 finger_w가 행 안에서 다르면 ValueError(`:6458-6463`) |
| `check_box_shape` | `:6486-6579` | 위 행 폭으로 width_ratio와 elongation을 계산한다. L이 혼재하는지는 보지 않는다 |
| `block_from_rows` / `rebuild_floorplan` | `:8281-8293`, `:8296-8374` | 같은 행 폭을 floorplan 블록 폭으로 쓴다 |
| `assign_finger_geometry` | `:6170-6265` | L은 `overrides["l"]`로 통과시키기만 한다(`:6247`, `:6261`). finger 배정 탐색(`search_stack_finger_w`, `:6125-6167`)은 **W만** 쓴다 |

### 1.2 L이 간접적으로만 들어가는 곳 (W를 거쳐)

- L 변경 → 같은 (gm/ID, ID)를 유지하려고 W가 변경 → `search_stack_finger_w`가 찾는 공통 finger_w(W들의 공약수 성격) 변경 → n_fingers 변경 → 오일러 패리티와 행 폭 변경. 이력 R6(`history.md:4038`)과 같은 사슬이다.
- 이 사슬은 **L이 같은지와 무관하게** L 값이 바뀌기만 해도 생긴다. L을 같게 맞추면 오히려 행 안 W 비율이 L 비율만큼 바뀐다(§2.2 실측).

### 1.3 L과 무관한 제약 (L을 통일해도 해결되지 않는다)

| 제약 | 위치 |
|---|---|
| kind 동질성(PMOS/NMOS 확산 공유 불가) | `build_graph` `:5398-5404`, `derive_horizontal_stack_groups` `:5218-5231` |
| 오일러 조건(노드 차수 짝홀, 연결성) | `check_euler_condition` `:5448-5470`. edge는 (source, drain)과 finger 수만 쓴다 |
| 행 안 finger_w 동일 | `compute_row_geometry` `:6458-6463` |
| W가 finger_w의 정수배 | `check_finger_width_compatibility` `:5320-5345` |
| 기본 stack 분할 키 | `split_into_stacks` `:3136-3144`. stack_id가 우선이고, 없으면 (kind, finger_w)로 나눈다. **L은 키가 아니다** |
| interdigitation / common-centroid 패턴 | `INTERDIGITATION_PATTERNS` `:93-102` 등. 소자 이름과 개수만 쓴다 |
| 행 분리(`apply_explicit_row_split`) | `:6268-6310`. n_fingers만 나눈다 |

### 1.4 엔진이 아예 모델링하지 않는 것 (L 통일의 실제 이득이 생기는 자리)

- dummy: `stick_diagram.py`에서 `dummy` grep 결과 0건이다.
- LOD / WPE / PSE(SA·SB·SD): 없다. reference에서 `stick-diagram-euler-layout.md:378`이 WPE/LOD를 정성적으로 한 번 언급할 뿐이다.
- 허용 L 목록이나 행별 게이트 길이 양자화(FinFET식 규칙): 없다.
- 비용 함수에 행 안 L 혼재 페널티가 없다. 사이징의 면적 metric은 `_metric_sum_area` = Σ W·L(`sizing_recipe.py:3022-3025`)이고, 레이아웃 폭(Σ n_f·pitch)과는 다른 양이다. 이 차이는 이력 A2(`history.md:3337`)에 이미 지적돼 있다.

---

## 2. 실측

### 2.1 현재 산출물(A0, 저장된 netlist 그대로)

| 회로 | 소자 | 물리 행 | 회로 전체의 서로 다른 L | 행 안 L 혼재 행 | 같은 행에서 L이 다른 매칭쌍 |
|---|---|---|---|---|---|
| two_stage_ota | 10 | 6 | 3 (245/730/790 nm) | **0** | 0 |
| folded_cascode | 15 | 10 | 1 (375 nm) | **0** | 0 |
| nmcnr_amplifier | 17 | 12 | 2 (245/375 nm) | **0** | 0 |
| current_reuse_telescopic_ota | 55 | 24 | 9 | **5 (21%)** | 0 |

- sizing dict의 L과 netlist의 l이 다른 소자는 4개 회로 모두 0개다.
- telescopic에서 L이 혼재하는 5개 행(`summary.txt:170-187`):
  - `biasgen_vom_a`: M8/M17 473.9 nm, M9a/M18a 150 nm
  - `biasgen_vom_floatsrc_sink`: M9b/M18b 245 nm, M10/M19 510.9 nm
  - `diffpair_branch_a__pmos_repair…0/…1` (2행): **M1a/M1b 535 nm(입력), M2a/M2b 1000 nm(캐스코드)**, 패턴 `M1a M2a M1b M2b`
  - `diffpair_branch_a__nmos_repair…`: **M3a/M3b 1000 nm(캐스코드), M4a/M4b 1400 nm**
- 박스 판정은 4개 회로 모두 FAIL이다(width_ratio 5.0~26.0). **FAIL이 가장 심한 nmcnr(26.0)과 two_stage(5.5)는 행 안 L 혼재가 0이다.** 박스 불균형의 원인은 L 혼재가 아니라 행별 W와 finger 수의 차이다.

### 2.2 L 통일 시나리오 비교

시나리오 정의(`measure_equal_L.py` docstring):
- **A**: 현재 (W, L)로 `assign_finger_geometry`를 다시 돌린 결과. Bs/Cs와 비교하기 위한 동일 조건 기준선이다.
- **Bw**: 행 안 L을 그 행의 최댓값으로 맞추고 W·n_fingers·finger_w는 유지한다. 순수 기하 효과만 본다.
- **Bs**: 행 최댓값 L, W ∝ L_new/L_old로 조정한 뒤 `assign_finger_geometry`를 다시 돌린다.
- **Cs**: Bs와 같되 행 최솟값 L로 맞춘다.

주의:
1. W∝L은 1차 근사다(같은 gm/ID·ID면 W/L이 일정하다고 본 것). LUT로 다시 사이징한 결과가 아니다.
2. finger_w 탐색 범위를 1e-3~1e3 µm로 넓게 잡았다. 실제 파이프라인은 1~40 µm(`sizing_recipe.py:9820-9822`)라 실제로는 실패가 더 쉽게 난다.
3. 저장된 netlist는 repair·row_split 이후 상태다. 그래서 A는 A0와 다르다. 분할된 소자는 이름이 중복돼 행이 합쳐진다. **비교는 A와 Bs/Cs 사이, A0와 Bw 사이에서만 한다.**

**two_stage / folded / nmcnr**: Bw, Bs, Cs 모두 행 수, finger 합, 오일러 분포, box 비율, 게이트 면적이 A0 또는 A와 **완전히 같다**(`summary.txt:3-31, 37-88, 97-158`). 행 안 L이 이미 하나라서 L 통일이 아무 일도 하지 않는다.

**telescopic**:

| 지표 | A0 | Bw | A | Bs | Cs |
|---|---|---|---|---|---|
| 물리 행 | 24 | 24 | 23 | — | 23 |
| L 혼재 행 | 5 | 0 | 4 | — | 0 |
| finger 합 | 89 | 89 | 213 | — | **1340** |
| 오일러 circuit/path | 7/17 | **7/17 (같음)** | 17/6 | — | 15/8 |
| box width_ratio | 10.13 | 11.82 | 12.96 | — | **1285.9** |
| 게이트 면적 Σn_f·fw·L (µm²) | 1059.0 | 1220.7 (+15.3%) | 1041.4 | — | 812.5 |
| 결과 | | | | **ValueError**: `biasgen_vom_a`에서 finger_w 후보 없음 | diffpair pmos 행이 16→1228 finger, fw 0.18 µm |

- Bw는 오일러 분포가 A0와 똑같다. 이력 R7(a) "오일러 패스는 L 무관"을 실측으로 확인한 것이다.
- Cs의 fw 0.18 µm는 sky130 최소 채널 폭 difftap.2 = 0.42 µm보다 작다. 즉 물리적으로도 만들 수 없다.
- Bs와 Cs가 나빠진 원인: 한 행 안에서 일부 소자만 W가 L 비율(예: 1000/535)만큼 바뀌어 W 비율이 작은 정수비에서 벗어났고, `search_stack_finger_w`(`:6145-6161`)의 정수배 조건이 깨졌다.

### 2.3 pitch 오버헤드를 넣었을 때 (`overhead_check.txt`)

오버헤드 0.29 µm는 sky130 magic 규칙 `gate_to_diffcont = 0.145`의 2배로, 모든 finger에 contact가 있다고 가정한 값이다(open_pdks `sky130.tcl`).

| | A0 행 폭 합 | Bw 행 폭 합 | 증가 | box ratio A0 → Bw |
|---|---|---|---|---|
| 오버헤드 0 (엔진 현재) | 39.29 µm | 43.78 µm | +11.4% | 10.13 → 11.82 |
| 오버헤드 0.29 µm | 65.10 µm | 69.59 µm | +6.9% | 10.00 → 10.00 |

- L 혼재 행 폭(오버헤드 0.29): diffpair pmos 4.23 → 5.16 µm(+22%), `biasgen_vom_a` 4.82 → 6.11 µm(+27%).
- 오버헤드는 L과 무관하게 finger마다 붙는다. 그래서 **L을 통일해도 오버헤드는 줄지 않는다.** L을 올려 맞추면 폭은 반드시 늘어난다.

### 2.4 입력-캐스코드 쌍의 배치 (device_roles 기반, `summary.txt:32-34, 89-94, 159-163, 265-274`)

| 회로 | 입력 / 캐스코드 | 같은 물리 행인가 | L |
|---|---|---|---|
| telescopic | M1a/b(입력) – M2a/b(캐스코드), PMOS | **같은 행**(interdigitated) | 535 / 1000 |
| telescopic | M3a/b(캐스코드) – M4a/b, NMOS | **같은 행** | 1000 / 1400 |
| folded_cascode | M1/M2 행 vs M5/M6(`col_m5`/`col_m6`), M8 | 다른 행 | 전부 375 |
| nmcnr | M102/M103 행 vs M106/M107 행 | 다른 행 | 245 / 375 |
| two_stage | 캐스코드 없음(M3/M4는 headroom_role=cascode로 태그돼 있지만 부하 미러다) | — | — |

→ U-23이 비교 대상으로 지정한 회로(파일럿, folded, nmcnr) 중 이 산출물로 확인 가능한 folded와 nmcnr에서는, 입력-캐스코드 L을 같게 맞춰도 **이 엔진의 어떤 레이아웃 지표도 바뀌지 않는다**(다른 행이므로). 레이아웃 효과가 실제로 생기는 회로는 telescopic이고, 거기서의 효과는 면적 증가다.

---

## 3. 일반 아날로그 레이아웃 관행 (웹 조사)

### 3.1 sky130 (130 nm, 비제한 규칙)

- SkyWater periphery rules: poly.1a 폭 ≥ 0.15, **poly.2 poly-poly 간격 ≥ 0.21**, poly.7 poly 밖 diff 연장 ≥ 0.25, poly.8 endcap ≥ 0.13, difftap.2 최소 채널 폭 0.42(µm). 페이지 요약 기준으로 **게이트 길이별로 달라지는 간격 규칙이나 고정 poly pitch 규칙은 없다.**
- open_pdks magic `sky130.tcl`: gate_to_diffcont 0.145, poly_spacing 0.21, diff_spacing 0.28.
- 판단: sky130에서는 L이 다른 게이트가 한 확산을 공유해도 **DRC상 문제가 없다**. 대가는 게이트 격자가 불규칙해지는 것과 LDE 환경이 비균일해지는 것뿐이다.

### 3.2 FinFET / 제한 규칙 공정

- ASIC North, *FinFET Technology and Layout Part 1*: 허용 게이트 길이는 보통 2~3개(core, 중전압 아날로그, I/O). contacted poly pitch 약 50 nm. 행 끝에는 같은 fin 수의 dummy를 둔다. fin 수가 바뀌면 diffusion break나 dummy가 필요하다.
- SemiWiki, *Analog Mixed-Signal Layout in a FinFET World*: L 선택지가 매우 제한돼 있어 긴 L은 소자를 직렬로 쌓아 구현한다. 규칙적인 litho 주기를 위해 dummy가 필요하고, gate periodicity 제한이 있다. (검색 요약에는 "길이가 다른 소자 간 간격 추가 규칙"이 있었지만, 본문을 fetch했을 때는 확인되지 않았다. 따라서 **미확인**으로 둔다.)
- 판단: 이런 공정에서는 행이나 블록 단위로 L을 통일하는 것이 사실상 **규칙상 필수**이고, L 통일이 곧 레이아웃 단순화다.

### 3.3 LDE와 매칭

- LDE 종류로 OSE, **PSE(poly spacing effect: 매칭 소자는 poly 간격이 같아야 한다)**, WPE, STI/LOD가 거론된다(design-reuse *Mixed-Signal IP Design Challenges in 28 nm and Beyond*, IEEE 7153318 *layout proximity effects for 28nm*).
- BSIM4 stress 모델: multi-finger(NF>1)는 SA, SB, **SD(게이트 사이 거리)** 로 LOD를 계산하고, 유효 SA는 finger별 역수 평균이다(BSIM4.3.0 enhancement 문서, 관련 특허 CN102142057). 한 행 안에 L이 섞이면 각 finger의 SA/SB(확산 끝까지 거리)가 다른 소자의 L 합만큼 달라진다. 매칭 소자의 finger 위치가 대칭이 아니면 **체계적 오프셋 요인**이 된다(모델 식에서 직접 나오는 추론이며, 이 회로로 정량화하지는 않았다).
- STI stress 대책: 연장 활성영역과 dummy로 모든 동작 소자가 같은 STI 경계 거리를 갖게 한다(PatSnap 블로그, ResearchGate 221627766).
- 매칭 일반 규칙(design-reuse *Optimizing Analog Layouts*): 가깝게, 같은 방향, 같은 공정 조건. R/C는 같은 종류와 폭, 끝에 dummy. "MOS 매칭 소자는 같은 L"은 교과서(Hastings)의 관행으로 알려져 있지만, 이번 조사에서 원문을 확인하지 못했다.

### 3.4 관행 요약

- 미러, 차동쌍, 매칭 캐스코드는 같은 unit(W, L)으로 만든다. 이 프로젝트의 LR2와 unit cell 원리(§2.5)와 같은 방향이다.
- 매칭되지 않는 직렬 소자(입력-캐스코드처럼 서로 다른 역할)의 L 통일은 비제한 공정에서는 규칙이 아니다. 격자 규칙성, dummy 공용, LOD 균일성을 위한 선택이다.

---

## 4. 판정과 엔진의 한계

### 4.1 조건별 판정

1. **서로 다른 행**: 단순해지지 않는다(효과 0). 4개 회로 행의 약 90%(58/63)가 이 경우다.
2. **같은 행, 매칭 그룹**: LR2로 이미 통일돼 있다(실측 위반 0).
3. **같은 행, 비매칭 직렬(입력-캐스코드 포함)**:
   - 엔진: 이득 0, 면적 +7~15%(오버헤드에 따라 다름).
   - 물리(sky130): DRC 이득 없음. 게이트 격자 규칙성과 LOD 환경 균일성의 **정성적 이득**만 있다. 이 이득이 매칭에 의미를 가지려면 그 행이 매칭 소자를 interdigitation한 행이어야 한다. telescopic의 `M1a M2a M1b M2b` 행이 바로 그 경우다. 여기서 M1a와 M1b는 대칭 위치라 1차 상쇄는 되지만, 엔진은 이를 검사하지 않는다.
4. **L 통일과 W 재사이징을 같이 하는 경우**: finger_w 공약수 조건이 깨져 **더 복잡해지거나 배치가 불가능해질 수 있다**(Bs 실패, Cs 1340 finger).
5. **제한 규칙 공정**: 단순해진다(필수). 현재 대상 공정이 아니다.

### 4.2 엔진이 L 통일의 이점(과 비용)을 반영하지 못하는 지점

- (G1) `PROCESS_GEOMETRY["finger_pitch_overhead_m"]=0`(`:6407`). 행 폭이 과소평가되고, L 변화의 상대 영향은 과대평가된다(+11.4% vs 오버헤드 반영 시 +6.9%).
- (G2) 행 안 L 혼재 페널티, 허용 L 집합, 게이트 격자 규칙성 판정이 없다. `compute_row_geometry`가 혼재를 명시적으로 허용한다(`:6435-6437`).
- (G3) dummy와 LDE(SA/SB/SD, PSE) 모델이 없어서 L 혼재가 매칭에 주는 영향을 알 수 없다.
- (G4) 사이징 면적 metric(ΣW·L, `sizing_recipe.py:3022`)과 레이아웃 폭(Σn_f·pitch)이 다른 양이다. L 통일의 면적 비용이 두 곳에서 다르게 보인다.
- (G5) `assign_finger_geometry`는 W 비율만 보고 공통 finger_w를 찾는다. L 후보를 바꿀 때 이 탐색이 실패하는지가 사이징 루프 밖에서만 드러난다(`sizing_recipe.py:9805-9811` 사례와 같은 계열).

---

## 5. 계획서 수정 제안 (문장안)

### LR8 (N3.9) 뒤에 추가

> 행 폭은 Σ n_fingers × pitch(L)이고 pitch의 오버헤드 항은 L과 무관하다. 그래서 같은 행 L 통일은 행 폭을 줄이지 않고, L을 올려 맞추면 늘어난다(실측 review3: telescopic 행 폭 합 +6.9~11.4%, 게이트 면적 +15.3%). sky130(비제한 규칙)에서 행 안 L 혼재는 DRC 제약이 아니다. 이 경우 레이아웃 판정은 L이 같은지가 아니라 L 변경에 따른 W 비율로 `assign_finger_geometry` 공통 finger_w가 존재하는지, 행 finger 합, box 비율로 한다. 허용 L 목록이나 고정 CPP를 가진 공정에서는 "행 안 L은 허용 목록의 한 값"을 하드 게이트로 추가한다(대상 공정이 생기면 PDK 선언에서 읽는다).

### U-23 판정 방법에 추가

> 레이아웃 지표는 (i) 같은 물리 행 안 L 종류 수, (ii) `assign_finger_geometry` 성공 여부(실제 finger_w 범위), (iii) 행 finger 합·box width_ratio·Σ n_f·pitch·finger_w로 정한다. 사전 실측(review3): 기존 4개 산출물에서 입력-캐스코드가 같은 물리 행에 있는 회로는 current_reuse_telescopic_ota(M1/M2, M3/M4) 하나뿐이다. folded_cascode와 nmcnr는 두 소자가 다른 행이라 B안의 레이아웃 이득이 구조적으로 0이다. 따라서 U-23의 레이아웃 비교는 telescopic을 포함할 때만 결론을 낼 수 있고, 캐스코드가 다른 행에 있는 회로에서는 평가 수·목적값·제약 여유만 비교한다. B안이 W 재사이징 뒤 공통 finger_w를 잃으면(review3에서 Bs가 ValueError) B안은 기각한다.

### NFR-5에 추가

> 레이아웃을 이유로 L을 같게 맞추는 것은 (a) 매칭 그룹(LR2), (b) 공정이 허용 L 목록을 강제하는 경우에만 한다. 그 외에는 L 통일로 늘어나는 행 폭·면적이 "제약을 만족하는 최소 면적"에 반하므로 하지 않는다.

### 부수 제안 (착수 조건, 사용자 승인 대상)

- G1: `finger_pitch_overhead_m`를 PDK 선언값(sky130 gate_to_diffcont 등)에서 유도하도록 바꾼다. 상수를 박지 말고 PDK 규칙 파일에서 읽는다.
- G3: 매칭 interdigitation 행에 L이 혼재하면(예: telescopic diffpair 행) `audit_row_split`에 "매칭 finger의 좌우 L 합 대칭" 검사를 넣을지는 LDE 모델 확보 이후 사용자가 결정한다.

---

## 출처

- SkyWater SKY130 Periphery Rules: https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html
- open_pdks magic sky130.tcl: https://github.com/RTimothyEdwards/open_pdks/blob/master/sky130/magic/sky130.tcl
- ASIC North, FinFET Technology and Layout Part 1: https://www.asicnorth.com/blog/part-one-finfet-technology-and-layout/
- SemiWiki, Analog Mixed-Signal Layout in a FinFET World: https://semiwiki.com/eda/synopsys/5604-analog-mixed-signal-layout-in-a-finfet-world/
- design-reuse, Mixed-Signal IP Design Challenges in 28 nm and Beyond: https://www.design-reuse.com/article/59990-mixed-signal-ip-design-challenges-in-28-nm-and-beyond/
- IEEE 7153318, layout proximity effects for 28nm Poly/SiON: https://ieeexplore.ieee.org/document/7153318
- design-reuse, Optimizing Analog Layouts: https://www.design-reuse.com/article/61548-optimizing-analog-layouts-techniques-for-effective-layout-matching/
- PatSnap, Layout-Dependent Stress Effects in CMOS: https://www.patsnap.com/resources/blog/rd-blog/layout-dependent-stress-effects-in-cmos-patsnap-eureka/
- Layout-dependent STI stress analysis (ResearchGate 221627766): https://www.researchgate.net/publication/221627766
- BSIM4.3.0 enhancement (SA/SB/SD): http://www.wrcad.com/xictools/docs/model_docs/bsim4.3.0/BSIM430_Enhancement.pdf
- CN102142057 BSIM4 stress model: https://patents.google.com/patent/CN102142057B/en
