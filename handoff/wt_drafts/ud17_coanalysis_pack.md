# UD-17a~e 공동분석 자료: 원본 회로도와 대조할 넷 기준 표

> 작성 2026-10-01. 저장소 HEAD `a796468`(gate master) 기준이고 저장소는 읽기만 했다(쓰기 0, 상태를 바꾸는 git 0).
> * 표의 원천: `git archive HEAD skills/analog-gmid-design/assets skills/analog-grammar`를 `C:/g91`에 푼 사본. 그 사본의 `library/*.topology.json`에 같은 사본의 `topology_to_markdown.py`를 돌렸다(출력은 `C:/g91/out`, 작업 뒤 삭제).
> * 저장소에 추적되는 `library/*.topology.md`는 json보다 오래돼 쓰지 않았다(백로그 B47). 새로 만든 표도 두 회로 모두 추적 .md와 다르다.
> * 수치는 `prep_ud17_f26_f27.md`와 `ud17_scripts/out/report.txt`에서 이미 잰 값을 그대로 옮겼다(θ\* 한 점, clamp 모드).
> * 긴 평가는 다시 돌리지 않았다. 이번에 새로 한 것은 **빠른 점검 하나뿐**이다. 엔진의 `propagate_node_voltages()`·`derive_vsb_from_nodes()`(수정 없음)에 report.txt의 θ\* vds를 넣고 선택지별로 연결만 바꿔 돌렸다(초 단위). 선언 그대로 돌린 F0·C0이 엔진의 충돌 4건과 값을 그대로 재현했다. 이 점검은 vds를 고정한 채 노드전압만 다시 전파한다. 사이징·헤드룸 재배정은 다시 하지 않았다(§2.4, §4.3).

---

## 0. 권한 구분 (먼저 읽을 것)

| 바꿀 대상 | 누가 | 근거 |
|---|---|---|
| **topology.json connectivity**: `netlist`의 `kind`/`source`/`drain`/`gate`, 새 `bulk` 단자, `ideal_sources`·`passive_elements`·`ports`의 단자 | **사용자만** 고친다. Claude는 고치지 않는다 | 메모리 "topology.json이 유일한 토폴로지 소스, connectivity는 사용자만 수정" |
| role/matching 메타데이터: `device_roles`(`vertical_stack_id`, `headroom_role`, `fold_group`, `gm_id_role`, `L_role`, `budget_reference_device`, `vds_match_vgs_of` …), `symmetry.matching_pairs`, `sizing_roles.theta` feed의 부호 | 사용자가 회로 해석을 **확인한 뒤** Claude가 반영한다. 회로위상 해석(fold_group·headroom_role 등)은 혼자 정하지 않고 공동분석한다 | 메모리 "국소 메타데이터는 바로, 단 회로위상 해석은 항상 공동분석" |
| 엔진(공유 코드) 변경: fold_group 컬럼 KVL 풀이, `bulk` 필드 해석, 충돌 노드에서 vsb 유도 금지 등 | 승인 뒤 card로 진행 | 계획 N3.12.3 |

정정을 지시할 때는 대기열에 모았다가 "한꺼번에 반영해" 지시가 올 때 한 번에 반영하고 표를 다시 뽑는다(메모리 "topology 정정은 대기열에 쌓았다가 일괄 반영").

---

## 1. folded_cascode: 넷·소자·선언

### 1.1 넷별 연결 표 (json에서 생성)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `Vg10` | M10.drain, M8.source | 2 |
| `Vg7` | M5.drain, M7.drain, M7.gate, M8.gate | 4 |
| `Vg9` | M10.gate, M7.source, M9.drain, M9.gate | 4 |
| `X` | M1.drain, M3.drain, M6.source | 3 |
| `Y` | M2.drain, M4.drain, M5.source | 3 |
| `bias3` ⚠️ | M5.gate, M6.gate | 2 |
| `gnd` | M10.source, M11.source, M9.source, MN.source | 4 |
| `out` | M6.drain, M8.drain | 2 |
| `tail` | M1.source, M11.drain, M2.source | 3 |
| `vb1` | Ibg.t0, M3.gate, M4.gate, MP.drain, MP.gate | 5 |
| `vb2` | Ibg.t1, M11.gate, MN.drain, MN.gate | 4 |
| `vdd` | M3.source, M4.source, MP.source | 3 |
| `vin_n` ⚠️ | M1.gate | 1 |
| `vin_p` ⚠️ | M2.gate | 1 |

자동 플래그: `bias3`, `vin_n`, `vin_p`는 게이트로만 참조되고 구동 소자가 없다. 입력 핀이면 정상이다. `bias3`은 `ports._comment`가 "교류접지"로 적어 두었고 **DC 전압은 어디에도 선언돼 있지 않다**. `Ibg`는 vb1–vb2 사이 이상 전류원(`implementable: false`, 값 미상)이다.

### 1.2 소자별 연결 표

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | pmos | `tail` | `X` | `vin_n` |
| M2 | pmos | `tail` | `Y` | `vin_p` |
| M3 | pmos | `vdd` | `X` | `vb1` |
| M4 | pmos | `vdd` | `Y` | `vb1` |
| M5 | pmos | `Y` | `Vg7` | `bias3` |
| M6 | pmos | `X` | `out` | `bias3` |
| M7 | nmos | `Vg9` | `Vg7` | `Vg7` |
| M8 | nmos | `Vg10` | `out` | `Vg7` |
| M9 | nmos | `gnd` | `Vg9` | `Vg9` |
| M10 | nmos | `gnd` | `Vg10` | `Vg9` |
| M11 | nmos | `gnd` | `tail` | `vb2` |
| MN | nmos | `gnd` | `vb2` | `vb2` |
| MP | pmos | `vdd` | `vb1` | `vb1` |

`bulk` 필드는 13개 소자 어디에도 없다. 엔진은 NMOS bulk = gnd, PMOS bulk = vdd로 고정 가정한다(`sizing_recipe.py` 3795~3796행 docstring과 `derive_vsb_from_nodes`).

### 1.3 충돌에 관련된 선언 (device_roles · matching · theta feed)

모든 소자가 `vsb: 0.0`을 선언했다. 실제 vsb는 `reconcile_vsb_from_nodes()`가 노드전압으로 다시 유도해 덮어쓴다.

| 소자 | vertical_stack_id | headroom_role | fold_group | gm_id_role | L_role | θ\* vds | θ\* vsb(사용값) |
|---|---|---|---|---|---|---|---|
| M1 | col_m1 | cascode | g_tail | matching | mirror | 0.2 | **1.6** (LUT 0.8로 클램프) |
| M2 | col_m2 | cascode | g_tail | matching | mirror | 0.2 | **1.6** (0.8) |
| M11 | col_m11 | mirror | g_tail | matching | mirror | 0.2 | 0 |
| M3 | col_m3 | mirror | g_x | matching | mirror | 0.2 | 0 |
| M6 | col_m6 | cascode | g_x | gain | mirror | 0.2 | 0.2 |
| M4 | col_m4 | mirror | g_y | matching | mirror | 0.2 | 0 |
| M5 | col_m5 | cascode | g_y | gain | mirror | 0.2 | **1.8** (0.8) |
| M7 (다이오드) | col_m7 | mirror | g_y | matching | mirror | 0.45 | **−0.65** (0) |
| M9 (다이오드) | col_m9 | mirror | g_y | matching | mirror | 0.45 | 0 |
| M8 | col_m8 | cascode | g_vg10 | gain | mirror | 0.2 | 0.2 |
| M10 | col_m10 | mirror | g_vg10 | matching | mirror | 0.2 | 0 |
| MP | biasgen_mp | diode_reference | -- | matching | mirror | 0.675 | 0 |
| MN | biasgen_mn | diode_reference | -- | matching | mirror | 0.45 | 0 |

* 모든 소자가 **자기만의 singleton `vertical_stack_id`**를 가진다. 그래서 헤드룸은 `_fold_group_singleton` 우회(`sizing_recipe.py` 7507~7554행)로 정해진다. 이 우회는 소자마다 역할별 최소 vds만 준다. 주석(7545~7548행)에 "병합 노드 전압의 정확한 KVL 일치는 이 근사가 보장하지 않는다"고 적혀 있다.
* `fold_group` 검사(`_hr_fold_group_check`, 6906행)는 "같은 group 안의 다른 소자와 비레일 넷을 하나라도 공유하는가"만 본다. 그래서 `g_y`는 Y 노드 하나가 아니라 **사슬**이다: M4–M5(Y) → M5–M7(Vg7) → M7–M9(Vg9). M2는 Y에 붙어 있지만 `g_tail`에 들어 있다.
* matching_pairs: {M1,M2} offset·current_forced, {M3,M4} ratio·forced, {M9,M10} ratio·forced, {M7,M8} ratio·forced, {M5,M6} ratio·not forced, {M11,MN} ratio·forced.
* theta feed(전류 방향이 담긴 선언):
  * `r_split_M1_M2` (A, root [M1,M2], reference [MN], 0.5): 주석은 "diffpair가 tail 전류를 반씩 나눔"이다.
  * `kcl_fold_M6` (A_signed, root M6, terms [{M1}, {M3}], 부호 생략 = +1): I6 = I1 + I3. 주석은 "X 노드 KCL(M1+M3가 들어와 M6로 나감)"이다.
  * `kcl_fold_M5` (A_signed, root M5, terms [{M2}, {M4}]): I5 = I2 + I4.
  * θ\* 값은 I3 = 0.75 µA, I1 = 0.25 µA, I6 = 1.0 µA, I11 = 0.5 µA다.
* metric `gain_db`·`pm_deg`가 소자를 이름으로 참조한다: gm1_device M1, fold_leg_a M1, fold_leg_b M3, cascode_p M6, cascode_n M8, mirror_n M10. `cmrr_db`·`psrr_db`의 tail_device는 M11이다.
* `sizing_roles.constraints = []`(U-35 삭제)라 이 회로는 이미 "사이징 판정 보류" 상태다.

### 1.4 json 안의 설명 문장과 connectivity가 어긋나는 곳 (참고, 판정 아님)

연결 자체는 사용자가 확정한 것이다. 아래는 설명 주석(메타데이터)이 현재 연결과 다르게 적힌 곳이다. 회로도와 대조할 때 헷갈리지 않도록 적는다.

| 위치 | 주석 내용 | 현재 netlist |
|---|---|---|
| `symmetry._matching_pairs_comment` | "M3/M4는 MP(gate=drain=**tail**)", "M9(gate=drain=**X**)" | MP gate=drain=`vb1`, M9 gate=drain=`Vg9` |
| `_netlist_correction_2026-08-05` (3) | "**X-branch(M5)** 신호전류 … **Y-branch(M6)** 출력" | M5.source = `Y`, M6.source = `X`(같은 주석의 (4)는 맞게 적혀 있다) |
| `_device_roles_comment_fold` | "Y 노드(M4/M5/M7/M9)" | 넷 Y = M2.drain, M4.drain, M5.source. M7·M9는 Y에 닿지 않는다 |

---

## 2. folded_cascode 충돌별 표

### 2.1 충돌 4건: 값을 만든 경로와 관련 필드 (prep §1.2, report.txt)

엔진은 이름순(`sorted`)으로 먼저 도달한 경로의 값을 노드에 박는다. 나중 경로는 `conflicts`에만 남는다. 그 뒤 박힌 값으로 vsb를 유도한다.

| 충돌 | 먼저 박힌 값과 경로 | 나중 경로 | 차이 | 관련된 topology 필드 |
|---|---|---|---|---|
| M4 @ Y | **0.0**: gnd → M11(nmos, +0.2) → tail 0.2 → M2(**pmos**, source = tail, −0.2) → Y | 1.6: vdd → M4(pmos, −0.2) → Y | 1.6 | M2.kind·source·drain, M11.kind, fold_group g_tail/g_y, singleton vsid |
| M1 @ X | **1.6**: vdd → M3 → X | 0.0: gnd → M11 → tail 0.2 → M1(pmos, −0.2) → X | 1.6 | M1.kind·source·drain, g_tail/g_x |
| M9 @ Vg9 | **−0.65**: Y 0.0 → M5(pmos, −0.2) → Vg7 −0.2 → M7(nmos 다이오드, source = Vg9, −0.45) → Vg9 | 0.45: gnd → M9(다이오드 +0.45) | 1.1 | 위 Y 값 + g_y 사슬 + `bias3` DC 미선언 |
| M8 @ out | **1.4**: vdd → M3 → X 1.6 → M6 → out | 0.4: gnd → M10 → Vg10 0.2 → M8 → out | 1.0 | g_x/g_vg10 singleton, 출력 CM 미선언 |

이 충돌에서 파생된 F26 축 밖 4소자는 M1·M2(vsb 1.6), M5(1.8), M7(−0.65, 순바이어스)다. clamp를 거부로 바꾸면 θ\*는 M7에서 `InfeasibleSizingError`가 나고, 전체 400점이 전부 infeasible이다(prep §4.1).

### 2.2 이번 빠른 점검: 극성만 바꾸면 무엇이 남는가

vds는 θ\* 값 그대로 두고 엔진 전파 함수만 다시 돌렸다.

| 경우 | 충돌(먼저 값 / 다른 값 / 차이) | 축 밖 vsb | 노드 |
|---|---|---|---|
| F0 선언 그대로 | Y 0.0/1.6/**1.6**, X 1.6/0.0/**1.6**, Vg9 −0.65/0.45/**1.1**, out 1.4/0.4/**1.0** | M1 1.6, M2 1.6, M5 1.8, M7 −0.65 | tail 0.2, X 1.6, Y 0.0 |
| F1 M1·M2 kind → nmos | Y 0.4/1.6/**1.2**, X 1.6/0.4/**1.2**, out **1.0**, Vg9 −0.25/0.45/**0.7** | M5 1.4, M7 −0.25 (M1·M2는 0.2로 축 안) | Y 0.4 |
| F2 pmos 유지 + source↔drain 교환 | Y **1.2**, M1 @ tail 0.2/1.4/**1.2**, out **1.0**, Vg9 **0.7** | M2 1.4, M5 1.4, M7 −0.25 | Y 0.4 |
| F3 = F1 + M1·M2 vds 1.4 (X = Y = 1.6이 되게 맞춘 예시) | out **1.0**, Vg9 0.95/0.45/**0.5** | M7 0.95 (Y 경로 기준) | Y 1.6, Vg7 1.4 |

읽는 법:
* X·Y의 1.6 V는 두 성분으로 나뉜다.
  * **극성 부호 0.4 V**: pmos −0.2 대 nmos +0.2. UD-17a 몫이다.
  * **tail 컬럼 KVL 공백 1.2 V**: vdd → M3 → X → M1 → tail → M11 → gnd의 vds 합이 0.6이고 VDD는 1.8이다.
* tail 전압은 실제로 "입력 공통모드 − VGS1"이 정하는데, 이 값이 선언되지 않았다. singleton 우회는 M1에 vds 0.2만 준다. 그래서 **극성을 고쳐도 X·Y 충돌이 1.2 V로 남는다.** prep §2.1의 "(a)가 1.6 V 두 건"이라는 설명을 이렇게 정밀하게 고친다.
* X·Y가 닫혀도(F3) Y 컬럼 0.5 V와 출력 컬럼 1.0 V 공백이 남는다. 이것이 UD-17c다.
* M7 vsb는 어느 경로로 Vg9를 정하느냐에 달렸다: Y 경로면 0.95, M9 경로면 0.45. prep의 SPICE 일관값 0.45는 M9 경로 기준이다.

### 2.3 UD-17a: M1·M2를 어떻게 선언할 것인가 (connectivity, 사용자 몫)

| 선택지 | json에서 바뀌는 것 | 엔진 결과에서 바뀌는 것 | 남는 것 / 주의 |
|---|---|---|---|
| (1) **kind를 nmos로** (NMOS 입력 폴디드) | connectivity(사용자): `netlist` M1·M2 `kind` pmos→nmos. 사용자 확인 뒤 메타(Claude): `kcl_fold_M5`·`M6` 부호(UD-17b). M1·M2 role 재검토(지금은 `headroom_role: cascode`, `gm_id_role: matching`, `fold_group: g_tail`이라 입력쌍 역할과 맞는지 공동분석 대상) | tail KCL이 성립한다(M1·M2가 tail로 전류를 넣고 M11이 뺀다). M1·M2 vsb 1.6 → **0.2**(축 안). LUT가 nmos 표로 바뀌어 M1·M2 W·gm/ID가 바뀐다(미측정). 충돌은 1.6/1.6/1.1/1.0 → **1.2/1.2/0.7/1.0**(F1). M5 vsb 1.8 → 1.4, M7 −0.65 → −0.25로 여전히 축 밖 | tail 컬럼 1.2 V 공백은 그대로라 UD-17c 없이는 F26·F27이 해소되지 않는다. prep의 연결 패턴 근거(nmos tail sink, pmos 폴딩 전류원 M3·M4, pmos 캐스코드 M5·M6, nmos 미러 M7~M10)는 이 선택지와 같은 모양이다 |
| (2) pmos 유지, **source↔drain 교환** (X·Y = source, tail = drain) | connectivity(사용자): M1 source X / drain tail, M2 source Y / drain tail. 메타: UD-17b 부호도 같이 바뀐다(PMOS 전류가 X에서 tail로 나가므로 I6 = I3 − I1) | tail KCL은 성립한다. 노드값은 F1과 같다(F2). M2 vsb 1.4(축 밖), M1 vsb 0.2 | 게이트가 입력이고 source가 고임피던스 폴딩 노드에 붙는 형태라 **교과서형 입력단이 아니다.** 회로도에서 이 방향이 맞는지 따로 확인해야 한다 |
| (3) **유지** (원문이 정말 pmos 입력, source = tail) | 그대로라면 tail에 전류를 넣는 소자가 없다(KCL 불가). 원문이 PMOS 입력 폴디드라면 거울상 연결이 필요하다: tail 전류원을 vdd 쪽 pmos로, 폴딩 전류원 M3·M4를 gnd 쪽 nmos로, 캐스코드·미러 극성도 반대로 → **여러 소자의 connectivity 변경** | 지금과 같다: 충돌 4건, 축 밖 4소자, 거부 시 θ\* infeasible. SPICE상 PMOS 게이트가 약 −1.04 V여야 켜진다(prep §2.1) | 회로도가 지금 json과 정말 같다면 이 회로는 DC 동작점이 없다 |

### 2.4 UD-17b: `kcl_fold_M5`·`kcl_fold_M6` 부호 (메타데이터, UD-17a 답을 따른다)

| 선택지 | json 변경(사용자 확인 뒤 Claude) | θ\* 산술로 본 영향 |
|---|---|---|
| 지금 (+1, +1): I6 = I1 + I3 | -- | I6 = I5 = 1.0 µA. `r_split`(전류가 X·Y → tail로 흐름)과 한 소자 M1의 전류 방향이 서로 반대다 |
| 교과서형 I6 = I3 − I1 (UD-17a (1)·(2)) | `terms: [{"device":"M1","sign":-1},{"device":"M3"}]`, M5도 같은 모양. 주석의 "M1+M3가 들어와"도 고친다 | I6 = I5 = 0.75 − 0.25 = **0.5 µA**. M5~M10 전류가 절반이 되어 W·gain·pm·power가 다시 계산돼야 한다(미측정) |

### 2.5 UD-17c: Y 컬럼(0.5 V)·출력 컬럼(1.0 V)·tail 컬럼(1.2 V) 공백을 어디서 정할 것인가

| 선택지 | json / 엔진 변경 | 결과 |
|---|---|---|
| (i) 외부 DC를 선언한다: `bias3` 전압, 출력 CM, 입력 CM(tail 전압) | **선언할 필드가 지금 없다**(`ports`에 DC 값 없음, `bias3`는 교류접지라고만 적혀 있음). 새 필드와 엔진 해석이 필요하다(공유 코드, 승인 필요). 값 자체는 사용자 스펙이다 | Y = V(bias3) + VSG5, out = 출력 CM, tail = Vin,cm − VGS1로 닫힌다. 남는 전압은 M4·M5 또는 M3·M6·M8·M10의 VDS로 간다 |
| (ii) 엔진이 fold_group 컬럼 KVL을 푼다 (singleton 우회 대체) | 엔진 변경(승인). topology는 그대로 | 공백을 어느 소자에 배분할지 규칙이 필요하다. 외부 DC가 없으면 해가 하나로 정해지지 않는다(출력 CM이 대표적) |
| (iii) 두고, 기본안대로 멈춘다 | prep §5.2 기본안 2(충돌 > tol이면 #23 SEAL_VIOLATION으로 멈추고, 충돌 노드에서 vsb를 유도하지 않음) | folded 정본 실행이 거부로 끝난다. 이 회로는 이미 판정 보류다 |

---

## 3. current_reuse_telescopic_ota: 넷·소자·선언

### 3.1 넷별 연결 표 (json에서 생성)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `N11a11b` | M11a.drain, M11a.gate, M11b.source | 3 |
| `N11b` | M11b.drain, M11b.gate, M12.drain, M9a.gate | 4 |
| `N14a14b` | M13.drain, M14a.drain, M14a.gate, M9b.gate | 4 |
| `N14a_14b` | M14a.source, M14b.drain, M14b.gate | 3 |
| `N1a2a` | M1a.drain, M2a.source | 2 |
| `N1b2b` | M1b.drain, M2b.source | 2 |
| `N20a20b` | M20a.drain, M20a.gate, M20b.source | 3 |
| `N20b` | M18a.gate, M20b.drain, M20b.gate, M21.drain | 4 |
| `N23a24b` | M23a.source, M24b.drain, M24b.gate | 3 |
| `N24b23a` | M18b.gate, M22.drain, M23a.drain, M23a.gate | 4 |
| `N36b` | M36b.drain, M36b.gate, M37b.drain | 3 |
| `N3a4a` | M3a.source, M4a.drain | 2 |
| `N3b4b` | M3b.source, M4b.drain | 2 |
| `N58_57` | M57.source, M58.drain | 2 |
| `N64_63` | M63.drain, M64.source | 2 |
| `N_cc_rz1` | Cc1.t1, Rz1.t0 | 2 |
| `N_cc_rz2` | Cc2.t1, Rz2.t0 | 2 |
| `Ncmfb_tail` | M37a.source, M37b.source, M38.drain | 3 |
| `Vbias1` | Iref.t0, M13.gate, M17.gate, M18_bg.drain, M18_bg.gate, M22.gate, M6.gate, M60.gate, M61.gate, M8.gate | 10 |
| `Vbias2` | M2a.gate, M2b.gate, M57.drain, M57.gate, M58.gate, M68.drain | 6 |
| `Vbias3` | M3a.gate, M3b.gate, M61.drain, M63.gate, M64.drain, M64.gate | 6 |
| `Vbias4` | M10.gate, M12.gate, M19.gate, M21.gate, M38.gate, M5.gate, M60.drain, M66.drain, M66.gate, M68.gate | 10 |
| `Vcmfb` | M36a.drain, M36a.gate, M37a.drain, M7.gate | 4 |
| `Vg15` | M15.gate, M8.drain, M9a.source, M9b.drain | 4 |
| `Vg25` | M17.drain, M18a.source, M18b.drain, M25.gate | 4 |
| `Vim` ℹ️ | Cf2.t1, Cs2.t0, M1b.gate, M4b.gate | 4 |
| `Vip` ℹ️ | Cf1.t1, Cs1.t0, M1a.gate, M4a.gate | 4 |
| `Voc` ℹ️ | M37a.gate, R1.t1, R2.t0 | 3 |
| `Voc_des` | M37b.gate, M39.drain, M39.gate, M40.source | 4 |
| `Vom` | CL2.t0, Cc1.t0, Cf1.t0, M15.drain, M16.drain, R1.t0 | 6 |
| `Vom1` | M18a.drain, M18b.source, M19.drain, M26.gate, M2a.drain, M3a.drain, Rz2.t1 | 7 |
| `Vop` | CL1.t0, Cc2.t0, Cf2.t0, M25.drain, M26.drain, R2.t1 | 6 |
| `Vop1` | M10.drain, M16.gate, M2b.drain, M3b.drain, M9a.drain, M9b.source, Rz1.t1 | 7 |
| `Vx` | M1a.source, M1b.source, M58.source, M6.drain, M7.drain | 5 |
| `Vy` | M4a.source, M4b.source, M5.drain, M63.source | 4 |
| `gnd` | CL1.t1, CL2.t1, Cs1.t1, Cs2.t1, Iref.t1, M10.source, M12.source, M14b.source, M16.source, M19.source, M21.source, M24b.source, M26.source, M38.source, M40.drain, M40.gate, M5.source, M66.source, M68.source | 19 |
| `vdd` | M11a.source, M13.source, M15.source, M17.source, M18_bg.source, M20a.source, M22.source, M25.source, M36a.source, M36b.source, M39.source, M6.source, M60.source, M61.source, M7.source, M8.source | 16 |

자동 플래그는 없다(Vim·Vip·Voc는 `_known_dangling_nets`로 해소돼 있다). 수동소자: CL1(Vop–gnd), CL2(Vom–gnd), Cc1(Vom–N_cc_rz1), Cc2(Vop–N_cc_rz2), Cf1(Vom–Vip), Cf2(Vop–Vim), Cs1(Vip–gnd), Cs2(Vim–gnd), R1(Vom–Voc), R2(Voc–Vop), Rz1(N_cc_rz1–Vop1), Rz2(N_cc_rz2–Vom1). 이상 전류원: Iref(Vbias1–gnd, 1.2 µA).

### 3.2 소자별 연결 표

| Name | Kind | Source | Drain | Gate | | Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|---|---|---|---|---|---|
| M1a | pmos | `Vx` | `N1a2a` | `Vip` | | M1b | pmos | `Vx` | `N1b2b` | `Vim` |
| M2a | pmos | `N1a2a` | `Vom1` | `Vbias2` | | M2b | pmos | `N1b2b` | `Vop1` | `Vbias2` |
| M3a | nmos | `N3a4a` | `Vom1` | `Vbias3` | | M3b | nmos | `N3b4b` | `Vop1` | `Vbias3` |
| M4a | nmos | `Vy` | `N3a4a` | `Vip` | | M4b | nmos | `Vy` | `N3b4b` | `Vim` |
| M5 | nmos | `gnd` | `Vy` | `Vbias4` | | M6 | pmos | `vdd` | `Vx` | `Vbias1` |
| M7 | pmos | `vdd` | `Vx` | `Vcmfb` | | M8 | pmos | `vdd` | `Vg15` | `Vbias1` |
| M9a | pmos | `Vg15` | `Vop1` | `N11b` | | M9b | nmos | `Vop1` | `Vg15` | `N14a14b` |
| M10 | nmos | `gnd` | `Vop1` | `Vbias4` | | M11a | pmos | `vdd` | `N11a11b` | `N11a11b` |
| M11b | pmos | `N11a11b` | `N11b` | `N11b` | | M12 | nmos | `gnd` | `N11b` | `Vbias4` |
| M13 | pmos | `vdd` | `N14a14b` | `Vbias1` | | M14a | nmos | `N14a_14b` | `N14a14b` | `N14a14b` |
| M14b | nmos | `gnd` | `N14a_14b` | `N14a_14b` | | M15 | pmos | `vdd` | `Vom` | `Vg15` |
| M16 | nmos | `gnd` | `Vom` | `Vop1` | | M17 | pmos | `vdd` | `Vg25` | `Vbias1` |
| M18_bg | pmos | `vdd` | `Vbias1` | `Vbias1` | | M18a | pmos | `Vg25` | `Vom1` | `N20b` |
| M18b | nmos | `Vom1` | `Vg25` | `N24b23a` | | M19 | nmos | `gnd` | `Vom1` | `Vbias4` |
| M20a | pmos | `vdd` | `N20a20b` | `N20a20b` | | M20b | pmos | `N20a20b` | `N20b` | `N20b` |
| M21 | nmos | `gnd` | `N20b` | `Vbias4` | | M22 | pmos | `vdd` | `N24b23a` | `Vbias1` |
| M23a | nmos | `N23a24b` | `N24b23a` | `N24b23a` | | M24b | nmos | `gnd` | `N23a24b` | `N23a24b` |
| M25 | pmos | `vdd` | `Vop` | `Vg25` | | M26 | nmos | `gnd` | `Vop` | `Vom1` |
| M36a | pmos | `vdd` | `Vcmfb` | `Vcmfb` | | M36b | pmos | `vdd` | `N36b` | `N36b` |
| M37a | nmos | `Ncmfb_tail` | `Vcmfb` | `Voc` | | M37b | nmos | `Ncmfb_tail` | `N36b` | `Voc_des` |
| M38 | nmos | `gnd` | `Ncmfb_tail` | `Vbias4` | | M39 | pmos | `vdd` | `Voc_des` | `Voc_des` |
| M40 | pmos | `Voc_des` | `gnd` | `gnd` | | M57 | pmos | `N58_57` | `Vbias2` | `Vbias2` |
| M58 | pmos | `Vx` | `N58_57` | `Vbias2` | | M60 | pmos | `vdd` | `Vbias4` | `Vbias1` |
| M61 | pmos | `vdd` | `Vbias3` | `Vbias1` | | M63 | nmos | `Vy` | `N64_63` | `Vbias3` |
| M64 | nmos | `N64_63` | `Vbias3` | `Vbias3` | | M66 | nmos | `gnd` | `Vbias4` | `Vbias4` |
| M68 | nmos | `gnd` | `Vbias2` | `Vbias4` | | | | | | |

`bulk` 필드는 51개 소자 어디에도 없다. 엔진 가정: PMOS bulk = vdd, NMOS bulk = gnd.

### 3.3 충돌에 관련된 선언

| 소자 | vertical_stack_id | headroom_role | 다른 헤드룸 선언 | gm_id / L | θ\* vds | θ\* vsb |
|---|---|---|---|---|---|---|
| M6 | **diffpair_branch_a** | tail | gm_id_match_vgs_of M18_bg | L bias_replica | 0.25 | 0 |
| M7 | vx_tail_b | tail | same_as_device M6, gm_id_match_vgs_of M36a | L bias_replica | 0.25 | 0 |
| M1a / M1b | diffpair_branch_a | -- (compensation stage_devices[0]이 정함) | | matching / mirror | 0.45 | 0.25 |
| M2a | diffpair_branch_a | cascode | (L_cascode theta, metric_stage_budget) | matching / mirror | 0.2 | **0.9227** |
| M2b | diffpair_shadow_b | cascode | same_as_device M2a | | 0.2 | **0.9227** |
| M3a | diffpair_branch_a | cascode | (L_cascode) | | 0.2 | 0.4773 |
| M3b | diffpair_shadow_b | cascode | same_as_device M3a | | 0.2 | 0.4773 |
| M4a / M4b | diffpair_branch_a | -- (compensation stage_devices[1]) | | | 0.45 | 0.0273 |
| M5 | diffpair_branch_a | tail | gm_id_match_vgs_of M66 | L bias_replica | 0.25 | 0 |
| M10 | biasgen_vom_floatsrc_sink | mirror | **vds_match_vgs_of M16** (Vop1 = VGS16), gm_id_match_vgs_of M66 | | **0.6773** | 0 |
| M19 | biasgen_vop_floatsrc_sink | mirror | gm_id_match_vgs_of M66 (vds_match 선언 없음, θ\* 값은 M10과 같은 0.6773) | | 0.6773 | 0 |
| M16 / M26 | output_stage_a / _b | -- (compensation stage_devices[3], gm_id 18.0) | | | 0.9 | 0 |
| M8 / M17 | biasgen_vom_a / biasgen_vop_a | mirror | gm_id_match_vgs_of M18_bg | | 0.825 | 0 |
| M9a | biasgen_vom_a | floating_current_source | budget_reference_device **M10** | matching / mirror, gm/ID 15.5, L 0.15 µm | 0.2978 | **0.825** |
| M18a | biasgen_vop_a | floating_current_source | budget_reference_device **M19** | 〃 | 0.2978 | **0.825** |
| M9b / M18b | biasgen_vom/vop_floatsrc_sink | floating_current_source | budget_reference_device M8 / M17 | | 0.2978 | 0.6773 |
| M61 / M63 / M64 | vbias3_stack | mirror / cascode / cascode | M61: budget_reference_device **M5** (replica 컬럼 바닥 = Vy) | | 0.3125 / 0.5625 / 0.675 | |
| M58 / M57 / M68 | vbias2_stack | cascode / cascode / mirror | M68: budget_reference_device **M6** (컬럼 위 = Vx) | | 0.45 / 0.7875 / 0.3125 | |

* `diffpair_branch_a`는 한 vsid가 vdd~gnd 전체를 혼자 맡는다. M6 0.25 + M1a 0.45 + M2a 0.2 | M3a 0.2 + M4a 0.45 + M5 0.25 = 1.8이고, 그래서 **Vom1 = 0.9 V**가 함의된다. 이 컬럼 안에 Vom1에서 끊는 선언은 없다.
* matching_pairs(관련분): {M1a,M1b} offset, {M4a,M4b} offset, {M2a,M2b} ratio·forced, {M3a,M3b} ratio·forced, {M10,M19} ratio·forced, {M9a,M18a} ratio·forced, {M9b,M18b} ratio·forced, {M16,M26} ratio·forced.
* theta(관련분):
  * `L_cascode` (metric_stage_budget, devices [M2a,M2b,M3a,M3b]).
  * `kcl_sink_M19`: I19 = I17 + I1a − I4a. `kcl_sink_M10`: I10 = I8 + I1b − I4b.
  * `mirror_M18a` (C, target M18a, reference M9a, 1.0). `K_replica` (C, target M9a, reference M15).
  * `kcl_tail_M5` (A, root M5, reference [M4a,M4b]).

---

## 4. current_reuse 충돌별 표

### 4.1 충돌 4건 (모두 0.222722 V, prep §1.2)

| 충돌 | 먼저 박힌 값과 경로 | 나중 경로 | 관련 필드 |
|---|---|---|---|
| M5 @ Vy | **0.0273**: vdd → M17(0.825) → Vg25 0.975 → M18a(0.2978) → **Vom1 0.6773** → M3a(0.2) → N3a4a 0.4773 → M4a(0.45) → Vy | 0.25: gnd → M5(0.25) | M18a.budget_reference_device M19, diffpair_branch_a 한 컬럼 |
| M64 @ Vbias3 | **1.4875**: vdd → M61(0.3125) | 1.2648: Vy 0.0273 → M63 → M64 → Vbias3 | vbias3_stack의 budget_reference_device M5 |
| M1a @ N1a2a | **0.8773**: Vom1 0.6773 → M2a(pmos 0.2, 역산) | 1.1: vdd → M6(0.25) → Vx 1.55 → M1a(0.45) | 같은 컬럼 위 반쪽 |
| M1b @ N1b2b | **0.8773**: gnd → M10(**0.6773 = VGS16**, vds_match_vgs_of) → Vop1 → M2b(역산) | 1.1: vdd → M6 → Vx → M1b | M10.vds_match_vgs_of M16 |

원인은 하나다. **Vom1·Vop1이 두 곳에서 정해진다.** 텔레스코픽 컬럼은 0.9 V를, 출력단 게이트 구속(VGS16 = VGS26 = 0.6773, M10·M19 = M18a 경로)은 0.6773 V를 준다. 엔진에는 "다른 그룹이 고정한 공유 노드"를 컬럼 배정에 반영하는 규칙이 없다.

### 4.2 UD-17d: Vom1·Vop1의 DC를 무엇이 정하는가

| 선택지 | json 변경 | 엔진 결과에서 바뀌는 것 | 회로상 함의 |
|---|---|---|---|
| (i) **출력단 VGS(0.677 V)가 의도다** | 메타(사용자 확인 뒤 Claude): `diffpair_branch_a`를 Vom1·Vop1에서 위(vdd→Vom1: M6·M1a·M2a)와 아래(Vom1→gnd: M3a·M4a·M5)로 나눈다. 아래 반쪽 예산 = V(Vom1)이 되도록 `budget_reference_device`로 M19(또는 M10)에 묶는다. **connectivity는 그대로다** | 빠른 점검 C1(vds만 바꾸고 의존 컬럼은 재배정하지 않음): 아래 반쪽 0.6773 − M3a 0.2 − M4a 0.45 = **M5 vds 0.0273 V**(포화 불가 → 거부 예상, 미측정). 위 반쪽 M6·M7 vds 0.25 → 0.4727, Vx 1.55 → 1.3273. N1a2a는 0.8773으로 일관이 된다. 그러면 **M2a·M2b vsb 0.9227은 파생값이 아니라 진짜 축 밖**이 된다(LUT 0.8 초과, SPICE 클램프 오차 ΔVGS 23 mV, IDu 1.3 %). replica 컬럼 vbias2_stack(M6 참조)·vbias3_stack(M5 참조)이 다시 배정된다(C1에 남은 M58·M64 충돌 2건은 재배정을 안 해서 생긴 것) | 아래 세 소자 최소합 0.9 V가 0.677 V 안에 들어가야 한다. 0.2227 V를 줄여야 하므로 M4a vds(compensation 결정, 0.45)·M5 vds·M3a vds 배분이나 출력단 VGS를 바꾸는 **설계 변경**이 필요하다. 그대로면 꼬리 M5가 triode다 |
| (ii) **컬럼 배정(0.9 V)이 맞다** | 메타·스펙: M16·M26 VGS가 0.9 V가 되도록 해야 한다. `M10.vds_match_vgs_of M16`은 KVL 사실이라 지울 대상이 아니다. 그러면 compensation이 정한 M16 gm/ID 18.0과 충돌한다 | Vop1 = Vom1 = 0.9가 되면 충돌 4건이 사라지고 M2a·M2b vsb는 0.7(축 안)이 된다(prep 일관값). 단 M16·M26의 gm/ID·전류(θ\* 26.2 µA)가 바뀌고 출력단 class-AB 바이어스(M9a·M18a 배터리, M10·M19 KCL)가 다시 계산된다(미측정) | 2단 출력 소자 게이트가 0.9 V인 동작점. 출력단 정지전류가 설계값과 다를 수 있다 |
| (iii) 다른 무엇이 정한다 (예: 첫 단 CM을 CMFB가 잡는다) | 회로도 근거에 따라 다르다. 지금 CMFB(M36~M40)는 Voc(=Vom·Vop 평균)를 감지해 **M7 게이트(Vcmfb)**, 즉 첫 단 위쪽 꼬리를 움직인다 | -- | Vom1을 정하는 소자·루프가 회로도에서 확인돼야 어느 선언으로 옮길지 정할 수 있다 |

참고로 prep §1.3의 "M2a·M2b는 F27 파생, 일관값 0.7"은 (ii)를 전제한 값이다. (i)이면 0.9227이 맞는 값이라 **UD-17e와 같은 bulk 질문이 M2a·M2b에도 걸린다.**

### 4.3 UD-17e: M9a·M18a(그리고 함께 볼 PMOS들)의 bulk

| 선택지 | json 변경 | 엔진 결과 | 비용 |
|---|---|---|---|
| (i) bulk = vdd (지금 엔진 가정) | 없음 | vsb = 1.8 − V(Vg15/Vg25 = 0.975) = **0.825**. LUT VS 축 [0, 0.2, 0.4, 0.6, 0.8]을 0.025 넘는다. 클램프 오차는 ΔVGS 2.9 mV, IDu 0.7 %, gm/gds −0.2 %(SPICE). 거부 모드면 θ\*가 M9a에서 "gm_id 후보 없음"으로 실패한다(원인 표시가 틀림, prep §4.1) | U-27 데이터(VS 0~1.8)가 필요하다. 또는 거부를 받아들인다 |
| (ii) bulk = 자기 source (별도 n-well) | **connectivity(사용자)**: `bulk` 단자를 새로 선언한다(DEC-61 `bulk` 필드). 지금 스키마·netlist에는 없다. **엔진 해석도 없다**: `derive_vsb_from_nodes`가 레일 bulk만 가정하고, 엔진 코드에서 `bulk`는 3795~3796행 docstring에만 나온다 → 엔진 배선 card가 필요하다(승인) | M9a·M18a vsb = 0 → 축 안이고 클램프가 사라진다. Vth가 낮아져 같은 gm/ID에서 VGS·W가 바뀐다(미측정) | 레이아웃에 n-well 분리 면적이 든다. 배터리 소자 매칭({M9a,M18a})은 유지된다 |

같은 질문이 걸리는 소자(소스가 레일이 아닌 소자, θ\* vsb). 축 밖은 굵게 표시했다.
* current_reuse PMOS: **M9a 0.825**, **M18a 0.825**, **M2a 0.9227**, **M2b 0.9227**, M40 0.7875, M57 0.7, M11b 0.675, M20b 0.675, M1a 0.25, M1b 0.25, M58 0.25.
* current_reuse NMOS: M37a/M37b 0.7375, M18b 0.6773, M9b 0.6773, M64 0.5898, M14a/M23a 0.5625, M3a/M3b 0.4773, M4a/M4b/M63 0.0273.
* folded: PMOS **M1·M2 1.6**, **M5 1.8**, M6 0.2. NMOS **M7 −0.65**, M8 0.2.

---

## 5. 원본 회로도에서 확인할 것 (체크리스트)

넷 이름이 아니라 **위 §1.1·§3.1 넷 표의 단자 목록**과 회로도를 한 넷씩 맞춰 보는 방식을 권한다.

**UD-17a (folded M1·M2)**
- [ ] M1·M2의 소자 종류: 화살표 방향, 또는 W 표기 옆의 n/p 표시. 원문은 Maloberti p.34~38이다.
- [ ] M1·M2의 어느 단자가 꼬리 노드에 붙는가(source인가 drain인가). 나머지 단자가 X(M3·M6 쪽)·Y(M4·M5 쪽)에 붙는가.
- [ ] 꼬리 노드에 붙은 전류원이 gnd 쪽 NMOS(M11, gate = vb2 = MN 미러)인가, vdd 쪽 소자인가.
- [ ] 폴딩 전류원 M3·M4가 vdd 쪽 PMOS(gate = vb1 = MP 미러)인가.
- [ ] (UD-17b) X 노드에서 M1 전류가 들어가는 방향인가 나가는 방향인가. 교과서형이면 I(M6) = I(M3) − I(M1)이다.

**UD-17c (folded 컬럼 공백)**
- [ ] `bias3`가 어디서 오는가(외부 핀인지, 내부 생성인지), DC 값이 있는가.
- [ ] 출력 `out`의 DC(공통모드)를 정하는 것: 부하, 궤환, 측정 조건.
- [ ] 입력 공통모드 전압(tail 전압 = Vin,cm − VGS1을 정한다).
- [ ] M7·M9 다이오드 스택(Vg7 = VGS9 + VGS7)이 회로도와 같은가. M5.drain = Vg7 = M7.gate·drain = M8.gate인가.

**UD-17d (current_reuse Vom1·Vop1)**
- [ ] Vom1 넷의 7단자가 회로도와 같은가: M2a.drain, M3a.drain, M18a.drain, M18b.source, M19.drain, M26.gate, Rz2. Vop1도 대칭인가: M2b, M3b, M9a, M9b.source, M10, M16.gate, Rz1.
- [ ] 논문이 Vom1·Vop1의 DC를 무엇으로 정한다고 설명하는가: 출력단 VGS(class-AB 정지전류)인가, 첫 단 CMFB인가.
- [ ] 첫 단 아래 반쪽(M3a 캐스코드 + M4a 입력 + M5 꼬리)의 VDS 배분이나 동작점 표가 논문에 있는가. 0.677 V 안에 들어가는 설계인가.
- [ ] CMFB 출력(Vcmfb)이 M7(첫 단 위쪽 꼬리)만 구동하는가. 다른 곳(예: 2단)도 구동하는가.

**UD-17e (bulk)**
- [ ] M9a·M18a(class-AB 배터리 PMOS)의 body 연결: vdd인가, 자기 source(Vg15·Vg25)인가. 별도 n-well 표시가 있는가.
- [ ] (UD-17d (i)인 경우) M2a·M2b 캐스코드 PMOS의 body 연결.
- [ ] 회로도의 "vdd" 라벨이 소스 연결인지 well/body 표시인지 구분한다. json `_confidence_note`는 bias-gen M61→M58→M57 쪽 'vdd' 라벨이 "well/body bias일 뿐 소스 연결 아님"이라고 적어 두었다. 다른 PMOS에도 같은 표기가 있는지 본다.

---

## 6. 재현 정보

| 항목 | 내용 |
|---|---|
| 사본 | `git -C <repo> archive -o C:/g91/a.tar HEAD skills/analog-gmid-design/assets skills/analog-grammar` → `C:/g91/repo` (HEAD `a796468`) |
| 표 생성 | 사본 안에서 `python -B topology_to_markdown.py library/<name>.topology.json C:/g91/out/<name>.topology.md` (출력 경로를 지정해 사본 안 .md도 덮어쓰지 않았다) |
| 빠른 점검 | `C:/g91/quick_prop.py`: report.txt의 θ\* 소자 줄을 파싱해 엔진 `propagate_node_voltages`·`derive_vsb_from_nodes`를 불렀다(rail vdd/gnd). F0·C0이 엔진 충돌 4건을 값까지 재현했다. 결과 파일은 작업 뒤 `C:/g91`과 함께 삭제했다. 결과 수치는 §2.2·§4.2에 모두 옮겼다 |
| 저장소 | 작업 전후 `git status --short` 동일, HEAD `a796468` |
