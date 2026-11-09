<!-- design-validator 보고 원문(agent ad379dc321340243c), 오케스트레이터가 세션 기록에서 옮김 2026-10-21 -->
## oracle-portability design v0.3.6 검증 결과 (design/oracle-eo1 `158cffab`, 읽기만)

**점수: 80/100. 판정: 조건부 진행.** 아래 필수 수정 7건을 고친 뒤 OP-5·OP-10 구현에 들어간다. 계획 차단 사유는 없다. DR-21·DR-22 범위는 빠짐없이 반영됐고 범위를 넘는 반영도 없다. DV-17·DV-18은 닫혔다. 차동 모드 닫힘의 부호 유도는 맞다. 다만 그 부호를 지킨다고 내세운 test가 실제로는 부호를 가려내지 못하고, graph 단일 정본 위반 후보가 2건 있다.

검사는 약 28턴 안에서 했다. history 파일과 §19.4 X-R3~X-R5 '승인됨' 문구는 읽지 않아 **미확인**이다.

### (1) DR-21·DR-22 반영: 빠진 것도 넘친 것도 없음
| 항목 | 결과 |
|---|---|
| DV-17 닫힘 | 반영. §21.5 4단계 (4), 함수 하나 `transfer_resolvable`, 사유만 기록하고 값 칸 없음. 계획 436행과 같다 |
| DV-18 닫힘 | 반영. §21.2 포트별 식, 사영 삭제, §18.1 (b)에 c=(2,2)와 follower 반례 test, §19.5 1688·1695행 |
| S-OS2 DC 닫힘 | 반영. §21.2 (c), §7 474행 ICMR 갈래 정리, §18.1 (d) |
| X-R3~X-R5 계약 알림 | 반영. U-6 (l)~(n) |
| DR-22 | 반영. §21.6 1b, 능력 `tran_ic_bias_only`, 손 회로 test, current_reuse 실측 보고 |
| 미확인 1건 | DR-21의 "`dc_resolution_in_V` 등 기존 칸의 뜻 정정"이 design 어디에 반영됐는지 찾지 못함 |

### (2) §19.6 인용 근거 점검
| 인용 | 실측 |
|---|---|
| `oracle_netlist.py:435` | 맞음. `Efb_ … {N(o)} {N(o_other)}`로 출력 차를 제어로 쓴다 |
| `oracle_netlist.py:445` | 존재하지만 출력 차 제어가 아님. 제어가 `{N(o)} 0`이다. F-1의 "출력 차를 제어로 쓰는 E" 묶음에서 빼야 한다 |
| `oracle_netlist.py:641` | 맞음. `Ecl_ … output_nodes[0] output_nodes[1]` |
| `:596-598`, `:625`, `:720` | 맞음. `.ic` 주석과 사용처 |
| 추가 근거 | `:765` `tran … 0 tmax`에 uic가 없다. 이 줄을 F-4 근거에 더하면 좋다 |
| §4.1 IR `Vcvs` | 맞음 (305행) |
| F-2·F-6·F-4의 "§4.1 `Tf`·`OpSweep`·`Tran`" | 절 번호 틀림. 실제 위치는 §5 (340·342·345행) |
| F-3 "`/rails` §11.1 **829행**" | 틀림. 829행은 `/process/temp_c`이고 `/rails`는 **834행** |
| F-1·F-5 "`feedback_passives` **833행**" | 틀림. 833행은 `/simulator/options`이고 `feedback_passives`는 **838-839행** |
| §8.3 `default_tolerances`·`tran_ic_bias_only` | 맞음 (584·573행) |

### (3) 차동 모드 닫힘의 부호 유도: 맞음
- 두 Vcvs의 관계식:
  - `tb:dmc:a`: V(in_a) − V(n_cm) = +½(V(o_a) − V(o_b))
  - `tb:dmc:b`: V(in_b) − V(n_cm) = −½(V(o_a) − V(o_b))
- 결과:
  - 입력 차: V(in_a) − V(in_b) = V(o_a) − V(o_b)
  - 입력 공통모드: ½(V(in_a) + V(in_b)) = V(n_cm) = cm0 + y
- in_a는 o_a의 반전 입력이므로 in_a = in−, in_b = in+이다. 그러면 위 식은 in+ − in− = −(Vop − Von)이 되어 계획식과 같다.
- 루프 이득은 A_d·1 < 0 (A_d = d(o_a−o_b)/d(in_a−in_b) < 0)이라 음되먹임이다.
- current_reuse 예시(Vip − Vim = Vom − Vop)도 맞다.

### (4) '|V| = 공칭 `.op` 전압'을 공칭 free(servo) 해로 읽은 해석: 물리적으로 받아들일 만함
- 엄밀히 보면 `.tf` 결과에 걸리는 허용오차는 실제로 푼 개루프 벤치의 `.op` 값에서 나온다.
- 하지만 정의의 판정 점이 '동작점'이고, 두 읽기의 차이는 reltol·|tf_bench_output_shift_V| ≤ reltol·W_rail로 2차 크기다.
- 이 문서에서 '공칭'은 일관되게 1단계 free 실행을 뜻한다(§21.5 1단계).
- 권고(nice-to-fix): 해석임을 §19.4나 계획 쪽 확인 요청으로 남긴다. 그 전까지 "개루프 `.op` 변형은 red"라는 test로 한쪽 해석을 굳히지 않는다.
- 범위 밖 관찰: 개루프 벤치 출력이 레일로 가면 A 자체가 다른 동작점의 값이 된다. 그런데 `tf_bench_output_shift_V`에는 swing의 `nominal_shift` 같은 거부 규칙이 없다.

### (5) 새 멈춤 DV-19·DV-20 판정
- **DV-19는 실제 취지 공백이지만 서술이 부정확하다.**
  - gb 576행 문언("구성 = 선언 되먹임, DC 망 = 용량 제외")을 그대로 적용하면 정의는 된다. 결과가 **개루프**라서 O-50 G4 취지("출력이 회로대로 따름")와 어긋날 뿐이다.
  - "계획이 정하지 않는다"보다 "문언대로면 개루프라 취지와 다름 — 계획이 명시해야 함"이 정확하다.
  - 지금 실측할 수 있으므로 미루지 않아도 된다. library/heldout `sizing_spec` 14개 가운데 `feedback.elements`가 비어 있지 않은 것은 current_reuse(차동) 하나뿐이다. 그래서 (e)에 해당하는 회로는 **0개**다.
  - 단, 이 0개는 빈 list가 `unity_follower`로 매핑된다는 전제에서만 성립한다. 아래 필수 수정 6을 함께 고쳐야 한다.
- **DV-20은 멈춤으로 받아들일 만하다.**
  - SPICE3/ngspice의 uic 없는 `.ic` 의미(바이어스 해에서 노드를 묶고 t > 0에 푼다)는 표준 동작이다. C10이 이미 같은 의미에 기대고 있다(`:597`, `:765`).
  - 같은 미확인이 C10에도 걸려 있다는 점을 함께 적어야 한다.
  - 원문 쪽 번호를 R6에서 기다리지 않아도, §18.1 OP-10 손 회로 test로 오늘 실측해 닫을 수 있다.

### (6) current_reuse 슬루 정의 불능 결론: 실측으로 확인됨
- `current_reuse_telescopic_ota.sizing_spec.json:141-142`: `elements: ["Cf1","Cf2"]`. 145행 기록에 "Cs1·Cs2는 입력-접지 샘플링 커패시터라 되먹임이 아니다"라고 되어 있다.
- `topology.md:124-127`: Cf1 = (Vom, Vip), Cf2 = (Vop, Vim), Cs1 = (Vip, gnd), Cs2 = (Vim, gnd).
- 따라서 design 규칙으로는 `no_input_network`가 맞다.
- 물리 메모: 실제 SC 회로에서 계단은 Cs 하부판에 걸린다. 모델이 Cs를 gnd에 묶어 두었기 때문에 "입력 망은 선언 몫"이라는 결론이 나온다.

### 필수 수정 (must-fix)
1. **[graph 규칙 1·2·4] 슬루 1b (i)의 닫힘 `.op`가 둘째 생산자다** (1845행, §19.5 1699행).
   - 같은 ICMR 벤치의 y = 0 점은 ICMR 훑기 공칭 점 기록 `v_in`이 이미 낸다. 슬루는 ICMR 확정 뒤에만 돌므로 그 기록은 항상 있다.
   - 새 `.op` 대신 그 점 기록 `v_in[in_a]`, `v_in[in_b]`를 `range_final`과 같은 기록 참조 경로로 읽어야 한다.
   - 따로 돌려야 하는 이유가 있다면 그 근거를 적는다.
2. **[graph 규칙 3] `icmr_v`가 같은 이름에 정의 둘이다.**
   - 엔진: gb 1490행 "`icmr_v` = 포트 창 교집합의 폭".
   - 오라클: §21.2 1785행 hi − lo (m 좌표).
   - 둘은 DV-18과 같은 조건에서 어긋난다. 반례는 c = (2,2) follower(포트 폭 2Δy 대 m 폭 Δy), 그리고 DC 닫힘에서 두 포트 창의 오프셋이다.
   - `v_in`에서 포트 창 교집합으로 계산하도록 맞추거나, 새 멈춤(DV-21)으로 올린다.
3. **[graph 규칙 3] DC 닫힘이 입력 공통모드를 ½(V_a+V_b)로 고정한다.**
   - 같은 문서는 공통모드 좌표를 c 가중 m = Σc·V/Σc²로 쓴다 (1776-1777행).
   - c(in_a) ≠ c(in_b)이면 두 정의가 갈린다.
   - Vcvs 이득과 cm0를 c에서 유도하거나, c가 비대칭이면 fail-closed로 막는다.
4. **§18.1 (d)와 F-1의 "짝 부호를 뒤집으면(양되먹임) red"는 test로 보장되지 않는다.**
   - DC `.op`는 평형점의 안정성을 구별하지 않는다.
   - 대칭 손 회로에서는 두 부호 모두 d = 0인 같은 해가 나오고, 오프셋이 있어도 ±Vos 수준만 다르다.
   - 판별 가능한 관측으로 바꿔야 한다. 예: 손 회로에 오프셋을 넣고 기대 부호를 단언하거나, 루프 부호 sign(T)·sign(닫힘) < 0을 구조적으로 단언한다.
   - "CMFB 없으면 `.dc` 미수렴"(F-1)도 단정할 수 없다. 레일로 간 해에 수렴한 뒤 공칭 점 영역 이탈로 정의 불능이 될 수도 있다. 둘 다 fail-closed라는 정도로 고친다.
5. **인용 위치 정정.** 위 (2) 표의 829→834, 833→838-839, §4.1→§5, `:445` 묶음 제외.
6. **`human.feedback.elements: []`의 매핑이 design에 없다.**
   - 엔진 정의는 `gmid_engine/authoring/spec_elements.py:19-20` "빈 list = 되먹임 수동소자 없음 = β=1 루프"다.
   - EO-1 생산자가 빈 list를 `unity_follower`로 매핑한다고 §11.6이나 §11.4에 적어야 한다.
   - 적지 않으면 library 단일 출력 회로가 모두 `declared` + DC 성분 없음 = DV-19 (e)로 떨어진다.
7. **[만들면 반드시 배선 원칙] 1b 경로를 쓰는 library 회로가 0개다.**
   - 1b는 `Tran.ic`, `tran_ic_bias_only`, 입력 망 원소의 다른 단자에 계단을 거는 경로까지 포함한다.
   - 1b가 예시로 삼은 회로가 current_reuse뿐인데, 그 회로는 `no_input_network`로 빠진다. 그래서 이 경로를 실행하는 것은 손 회로 test뿐이다.
   - "입력 망 원소의 다른 단자" 갈래는 대표 회로 추론이 없다(F-5). 그 노드가 용량에만 닿으면 공칭 벤치와 ICMR 벤치의 `.op`에서 DC로 떠서 행렬이 특이해진다. 다른 소자가 구동하는 노드라면 이상 전압원이 그 구동을 덮어쓴다.
   - 지금 구현할지(손 test만으로), 입력 망을 선언한 회로가 생길 때까지 미룰지 사용자 결정을 받아야 한다. 이것도 원래 취지와 다르므로 따로 보고한다.

### 고치면 좋은 것 (nice-to-fix)
- C10 안정성 벤치의 `.ic`(321행 "초기 조건은 요청 조건으로")도 같은 `Tran.ic` 칸과 `tran_ic_bias_only` 능력을 쓴다고 명시한다. 칸 하나, 능력 관문 하나로 두고, C10은 지금 능력 관문 밖에 있다.
- DR-22 문언 "`measure_feedback_undeclared` 슬루 갈래 = 미선언 차동 출력"과 design의 `feedback_config_undeclared`(`why = differential_undeclared`) 사이 이름 대응을 한 줄로 적는다.
- F-1에서 current_reuse 반전 짝을 Cf 연결로 추론한 부분은 설명용일 뿐이고, 판정 근거는 `.tf` 부호라는 점을 적는다.

### graph 단일 정본 점검 (별도 항목)
| 대상 | 판정 |
|---|---|
| 슬루 1b 닫힘 `.op` | **위반 후보**: 둘째 생산자 (필수 1) |
| `icmr_v` | **위반 후보**: 같은 이름에 정의 둘 (필수 2) |
| tb:icm의 ½ 가중 대 c 가중 | **위반 후보**: 같은 정의의 양을 두 식으로 계산 (필수 3) |
| `transfer_resolvable` | 준수. 함수 하나, 값 저장 없음 |
| `sim.a_dc`·`sim.offset_sys` | 준수. writer 하나, `sim_ref`로 참조 |
| `v_in` 원값과 `icmr_coord` 함수 | 준수 |
| `Tran.ic` 값 | 벤치 입력이라 허용. 다만 출처는 필수 1대로 기록 참조여야 한다 |
| 새 cache·memo·사본 칸 | 없음 |

### 관련 파일
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/02-design/features/oracle-portability.design.md` (§21.2 1767-1785, §21.5 1831, §21.6 1844-1845, §19.2 1599-1600, §19.6 1705-1710, §18.1 1448-1449)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/01-plan/features/oracle-portability.plan.md` (436, 441, 443, 713-714)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` (576, 577, 1490)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/tools/spice_oracle/oracle_netlist.py` (435, 445, 596-598, 625, 641, 720, 765)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/gmid_engine/authoring/spec_elements.py` (19-20)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.sizing_spec.json` (141-145)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.md` (124-127)
