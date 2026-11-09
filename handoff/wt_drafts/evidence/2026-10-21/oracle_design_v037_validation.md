<!-- design-validator 보고, oracle-portability design v0.3.7 (design/oracle-eo1 `f5b72b9d`, base `158cffab`), 읽기만, 2026-10-21 -->
## oracle-portability design v0.3.7 검증 결과

**점수: 86/100. 판정: 조건부 통과.** 필수 2~6은 모두 반영됐고 내용도 대체로 맞다. 다만 아래 필수 수정 2건을 고쳐야 한다. 하나는 이번 판이 남긴 묵은 문장이고, 다른 하나는 물리 근거 문장 하나가 틀린 것이다. 둘 다 문장만 고치면 되고 계획을 바꿀 일은 아니다. 새 멈춤(DV)을 올릴 항목은 없다.

- 범위: O-78 (3)에 따라 필수 2~6만 보았다. 필수 1·7, DV-19, 1b는 계획 v0.6.15 대기라 범위 밖이다.
- 방법: `git -C … diff 158cffab..f5b72b9d`로 받은 152줄 diff 전부를 읽었다. 인용은 모두 worktree에서 다시 쟀다.

### 1. 필수 2~6 해소 여부 (직접 다시 유도함)

| # | 결과 | 근거 |
|---|---|---|
| 2 `icmr_v` | **해소** | §21.2 'metric 값' = min_p hi_p − max_p lo_p. gb 1490행 "`icmr_v` = 포트 창 교집합의 폭(as-built 뜻 유지)"와 `E/metrics/ls_swing.py:20` "[max lo, min hi] 폭(빈 창은 음수 폭 그대로)"와 같은 뜻이다. 빈 창을 음수로 두는 것도 맞다. m 좌표 hi − lo 정의는 지웠고 m은 끝 확정 r에만 쓴다. c = (2,2)에서 포트 폭 2Δy 대 m 폭 Δy 반례, DC 닫힘에서 교집합 = 포트 폭 − \|d_in\|(d_in 일정)도 맞다. **단, 묵은 문장이 남았다 → 필수 A** |
| 3 c 가중 | **해소. 근거 하나는 고쳐야 함** | `tb:icm` DC = cm0 + y·c_s와 m = (V_a+V_b)/(2c_s)는 맞다. Σe·c = 0이고 c_a = c_b ≠ 0이면 e_a = −e_b라는 동치(근거 (3))도 맞다. 비대칭 c에서 fail-closed하는 것은 **O-78 (3) "공통모드 가중 c 유도·비대칭 fail-closed"로 사용자가 승인한 선택**이다. 그래서 새 DV는 필요 없다. 다만 §19.2 문장은 이를 "계획 문언에서 유도"라고만 적는다. 근거로 O-78 (3)을 함께 적는 것이 정확하다. **근거 (2)는 물리적으로 틀렸다 → 필수 B** |
| 4 부호 test | **해소** | 대수를 다시 풀었다. 바른 짝: d = A_d(d + V_os) → d = A_d·V_os/(1 − A_d). A_d < 0이면 부호 = sign(A_d·V_os), 크기 < \|V_os\|. 뒤집은 짝: d = A_d(−d + V_os) → d = A_d·V_os/(1 + A_d). \|A_d\| > 1이면 1 + A_d < 0이라 부호가 반대이고 크기 > \|V_os\|. 손 회로가 선형이라 불안정 평형점도 `.op`가 유한한 값으로 푼다. 그래서 (d-1)은 실제로 두 경우를 가려낸다. \|A_d\| > 1 조건도 적혀 있다. 보완점은 고치면 좋은 것 N3·N5 |
| 5 인용 | **해소. 전수 다시 잼** | 아래 표 |
| 6 `[]` 매핑 | **해소** | §11.6에 `[]` → `unity_follower`를 적었다. `spec_elements.py:19-20` 문언("빈 list = 되먹임 수동소자 없음 = β=1 루프, UD 9번")과 일치한다. 13개 회로를 다시 쟀다(library 9 + heldout 4). 비어 있지 않은 것은 current_reuse `['Cf1','Cf2']` 하나뿐이다. 계획 v0.6.15 DR-23 (3)과도 같은 내용이다 |

**인용 재측정** (worktree `f5b72b9d`):

| 인용 | 실측 |
|---|---|
| design §11.1 835행 `/rails` | 맞음 |
| 839-840행 | 839행 = `/feedback_passives`, 840행 = `/feedback_passives_basis`. 맞음. v0.3.6에서는 838·839행이었고, §7에 행 하나가 늘어 +1 밀렸다 |
| §5 `Tran` 340, `OpSweep` 342, `Tf` 345 | 맞음 |
| `oracle_netlist.py:435` | 맞음. `Efb_ … {N(o)} {N(o_other)}` |
| `oracle_netlist.py:641` | 맞음. `Ecl_ … output_nodes[0] output_nodes[1]` |
| `oracle_netlist.py:445` | 묶음에서 뺐다. 실제 제어가 `{N(o)} 0`이므로 빼는 것이 맞다 |
| `oracle_netlist.py:596-598`, `:625`, `:720` | 맞음. `.ic` 주석과 사용처 |
| `oracle_netlist.py:765` | 맞음. `tran tmax tstop 0 tmax`에 uic가 없다 |
| gb 1490행, `ls_swing.py:20`, `spec_elements.py:19-20` | 맞음 |
| §4.1 IR `Tf`·`OpSweep`·`Tran` 옛 인용 | 남은 곳 0건 (grep) |

### 2. 새 결함·묵은 문장·범위

- **필수 A (묵은 문장, graph 규칙 3·7)**: §11.7 점 기록(1071행)이 아직 "m은 `icmr_coord` 한 함수 … 끝 값·r·검사 (4)·**`icmr_v`·`icm_margin_v`** 소비자 모두 이 함수"라고 적는다. v0.3.7 §21.2와 §19.6 graph 표("m은 끝 확정 r만")와 어긋난다.
  - 같은 1071행의 `range_final` 문장 "끝 값 = `source` 지목 점의 `conduction.points[]` `m`"도 묵었다. ICMR 점에는 v0.3.6부터 `m` 칸이 없다. §21.2는 이미 "swing은 `m`, ICMR은 `v_in`"으로 고쳐져 있다.
  - 두 문장을 §21.2와 맞춘다.
- **필수 B (물리 근거 오류)**: §21.2 (c) '공통모드 가중 조건'의 근거 (2)는 "c에서 Vcvs 이득을 유도하면 … 훑기 방향이 차동 성분을 섞어 다른 측정이 된다"고 적는다. 틀렸다.
  - 일반화한 이득 g_a = c_b/(c_a+c_b), g_b = −c_a/(c_a+c_b)를 넣어도 V_a − V_b = d_out 행은 그대로다.
  - 닫힘에서 차동 성분은 자유 변수가 아니다. 그래서 해 집합은 같은 1차원 곡선이고, 매개(m 눈금·격자)만 달라진다.
  - v0.3.7부터 `icmr_v`·`icm_margin_v`는 포트 전압으로 낸다. 따라서 끝점과 metric 값은 c 가중과 무관하다.
  - 비대칭 c를 거부하는 근거는 (1) 계획의 '입력 공통모드' = (1,1) 방향, (3) 스키마 직교 규칙과의 동치, 그리고 **O-78 (3) 승인**이면 충분하다.
  - (2)는 "일반화는 계획에 없다(눈금만 다른 같은 곡선이지만 정의 밖이라 막는다)"로 고친다. 지금 상태는 물리적으로 잘못된 문장이 판단 근거로 남아 있는 것이다.
- **범위**: nice-to-fix 반영 셋(C10 `.ic`, 이름 대응, F-1 판정 근거)은 모두 v0.3.6 검증이 고치라고 한 항목 안에 머문다. §19.2의 '1b·DV-19 대기' 한 줄도 O-78 (1)(2)와 맞다. 필수 1·7과 §21.6 1b 본문은 손대지 않았다(diff에 없음).

### 3. graph 단일 정본 점검 (별도 항목)

| 대상 | 판정 |
|---|---|
| `icmr_v` (§21.2) | 준수. 식 하나(`swing_math`)이고 `range_final`도 같은 함수를 쓴다. 엔진과 같은 이름에 정의 하나다. **§11.7 묵은 문장이 문서 안에서 정의 둘처럼 보이게 한다 → 필수 A** |
| m(`icmr_coord`) | 준수. 함수이고 값 칸이 없다. 소비자는 r과 검사 (4)만이다(§11.7 문장을 고친 뒤) |
| `tb:icm` DC = cm0 + y·c_s | 준수. c_s는 입력 `dc_sweep.common`을 읽고, cm0는 기존 공칭 free 해를 읽는다 |
| `closure_common_asymmetric` | 준수. `detail` = 넷 이름뿐이고 계수 사본이 없다 |
| 부호 test (d-1)·(d-2) | 준수. 오라클 쪽 새 칸이 없다 |
| `[]` → `unity_follower` | 준수. 엔진 정의를 인용만 하고 EO-1 직렬화를 거친다 |
| C10 `.ic` = `Tran.ic`, 능력 하나 | 준수. 둘째 초기 조건 칸이 없다 |
| 새 cache·memo·slot·값 칸·사본·둘째 생산자 | 이 판의 변경분에는 없다. 슬루 1b 닫힘 `.op` 둘째 생산자(옛 필수 1)는 범위 밖이고 v0.6.15 DR-23 (1)·AP-1로 넘어간다 |

### 4. design ↔ 계획 gap (v0.6.14 / v6.25, O-78 대기 항목 제외)

| # | 항목 | 판정 |
|---|---|---|
| G1 | `icmr_v` 정의 = gb 1490행 | 일치 |
| G2 | `icmr_v` 대상 포트 = '측정 구성이 묶지 않은 입력 포트' | **계획 침묵, design 해석.** gb 1490행은 이 대상 규칙을 `icm_margin_v`에만 적는다. `icmr_v`는 "as-built 뜻 유지"인데 as-built(`ls_swing`)는 입력 포트 전부를 쓴다. follower에서는 차이가 오프셋 크기다. 엔진 측정 구성 창이 묶인 포트를 포함하는지는 **미확인**이다. 해석임을 §21.2에 적고, 엔진 IT-2와 같은 포트 집합인지 확인을 요청한다(N1) |
| G3 | `closure_common_asymmetric` | O-78 (3) 승인 범위다. design은 근거로 gb 576행 '그 구성은 정의 불능(… code 이름은 design)'을 인용한다. 그런데 그 문언은 S-OS1(B3 대기) 문장이고 비대칭 c와는 상관없다. 인용을 O-78 (3) + N3.14 공통 실패 규약으로 바꾼다(N2) |
| G4 | `[]` 매핑 | v0.6.14에는 문언이 없다. O-78 (3)과 대기 중인 v0.6.15 DR-23 (3)이 같은 내용이라 충돌하지 않는다 |
| G5 | C10 `.ic` 메모 | v0.6.15 DR-23 (1) "C10 쪽은 design이 적는다"를 미리 반영했다. 충돌하지 않는다. 다만 "옮기는 card가 §20에 없다"는 사실 오류다(아래 5) |
| G6 | 계획과 어긋나거나 계획을 넘는 곳 | G2 외에는 찾지 못했다 |

### 5. 작성자 열린 점 판정

- **C10 `.ic` 능력 관문에 owning card 없음 → 문장을 지금 고치고, 실제 귀속은 v0.3.8(DR-23)에서 확정. DV도 백로그도 아니다.**
  - §20 OP-3 행이 이미 §4(§4.2 `stab_benches` 행 포함), §5(`Tran`), §8.1~8.3(능력)을 범위로 갖는다. OP-3은 아직 구현 전이다(`git grep stab_benches` 0건).
  - 그러니 "옮기는 card는 §20 범위표에 아직 없다(미정)"는 틀렸고, OP-3이 소유한다.
  - O-78 (1)로 1b가 AP-1로 빠지면 OP 범위에서 `Tran.ic`·`tran_ic_bias_only`를 실제로 쓰는 곳은 C10 하나뿐이다. 이 칸·능력을 C10(OP-3)에 배선해 남기면 DR-23 (1)의 '쓰는 회로 없는 경로를 남기지 않는다'와 만들면 배선 원칙을 함께 만족한다. v0.3.8에서 이 방향으로 정리하기를 권고한다.
- **끝 분해능 r이 m 좌표라 포트 볼트로는 |c|배 거칠다 → 백로그. 서술도 정정한다.**
  - 다시 유도하면 대칭 c에서 m = V/c이므로 reltol 항은 상쇄된다. 포트 볼트 괄호 = reltol·|V| + |c|·vntol이다. **거칠어지는 것은 vntol 항뿐이다**(|c| < 1이면 그만큼 더 엄격). 그래서 '|c|배'는 과장이다.
  - vntol(~1e-6 V) 크기라 판정에 미치는 영향은 무시할 수 있다.
  - r 식은 design 몫이지만, 엔진 2단계 재훑기와 검사 (4)가 같은 r을 쓰는 교차 계약이다. 이번 판에서 바꾸지 말고 백로그에 둔다. 나중에 metric 단위(포트 V)와 맞출 때 엔진 card와 함께 바꾼다.

### 필수 수정 (must-fix)
1. **(A)** §11.7(1071행)의 묵은 문장 둘을 고친다: `icmr_coord` 소비자 목록에서 `icmr_v`·`icm_margin_v`를 빼고, `range_final` '끝 값 = 지목 점 `m`'은 ICMR이면 `v_in`으로 바꾼다.
2. **(B)** §21.2 (c) '공통모드 가중 조건'의 근거 (2)를 고친다. 차동 성분을 섞는다는 서술은 틀렸고, 같은 해 곡선에 매개만 다르다. §19.2 v0.3.7 상태 문장에는 'O-78 (3) 승인'을 근거로 함께 적는다.

### 고치면 좋은 것 (nice-to-fix)
- N1: `icmr_v` 대상 포트(묶지 않은 포트)가 design 해석임을 적고, 엔진 포트 집합과 같은지 확인을 요청한다(G2).
- N2: `closure_common_asymmetric` 근거 인용에서 gb 576행 S-OS1 문언을 빼고 O-78 (3)으로 바꾼다(G3).
- N3: (d-2) 구조 단언이 단일 끝 T(in_a → o_a)를 쓴다. 루프 부호는 차동 A_d로 정해진다. 이미 재는 `.tf` 네 값으로 A_d 부호를 만들어 단언해야 비대칭 회로에서도 맞다.
- N4: lo_p·hi_p를 '끝 점 기록의 v_in[p]'로 정의했다. c(p) < 0(스키마는 값 ≠ 0만 요구)이면 lo 끝에서 포트가 최대가 되어 창이 뒤집힌다. 그러면 `icmr_v`와 `icm_margin_v`가 음수로 나온다. lo_p = 두 끝 기록의 min, hi_p = max로 정의하거나 c > 0을 스키마 규칙으로 둔다. `icm_margin_v`는 v0.3.6부터 같은 문제가 있었다.
- N5: (d-3) "두 포트가 y·2만큼 움직이고"는 닫힘에서 ½Δd_out만큼 어긋난다. 단언은 ½(V_a+V_b) = cm0 + 2y(구성상 정확)로 둔다.
- N6: `closure_common_asymmetric`의 거부 시점 표기를 통일한다(§7 '훑기 호출 전' / §21.2 '시뮬레이터 호출 전'). `detail` `{in_a, in_b}`는 `.tf` 식별 뒤에야 정해지는 이름이므로, 비대칭 검사는 두 `excite` 포트 이름으로 시뮬레이터 호출 전에 하는 편이 맞다.
- N7: §21.2 `icmr_v` "입력 넷은 범위 규칙으로 레일 안"은 직접 훑는 포트에만 정확하다. DC 닫힘 포트는 ½d_out만큼 다를 수 있고, 레일 밖 필터가 받친다. 이 점을 한 구절 덧붙인다.
- N8: §19.6 F-1 '공칭 점 포화 부족의 음수 margin'은 fail-closed가 아니라 '값으로 FAIL'이다. 서술을 구분한다.

### 미확인
- 엔진 측정 구성 ICMR 창이 follower의 묶인 반전 입력을 `icmr_v` 교집합에 넣는지(G2). 엔진 IT-2 card가 아직 구현 전이다.
- library 차동 입력 회로의 `dc_sweep.common` 값. EO-1 생산자가 아직 없어 비대칭 c 갈래가 발동하는 회로 수를 셀 수 없다(design도 '미확인'으로 적음).
- DV-20(ngspice uic 없는 `.ic` 원문 쪽 번호). 범위 밖이고 그대로 남았다.
- history 파일은 v0.3.7 행(diff)만 읽었다. 다른 행은 읽지 않았다.
- 시뮬레이션은 돌리지 않았다. 부호 test 대수는 손으로 풀어 확인했다.

### 관련 파일
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/02-design/features/oracle-portability.design.md` (§11.7 1071, §19.2 1609, §19.6 1708-1728, §21.2 1788·1794·1795·1801·1803, §18.1 1449, §4.2 321, §7 신설 행, §20 OP-3 1740)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` (576, 1490)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/gmid_engine/metrics/ls_swing.py` (20)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/gmid_engine/authoring/spec_elements.py` (19-20)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/tools/spice_oracle/oracle_netlist.py` (435, 445, 596-598, 625, 641, 720, 765)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-o78/docs/01-plan/features/oracle-portability.plan.md` (DR-23 717행, X-36 646행)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md` (O-78)
