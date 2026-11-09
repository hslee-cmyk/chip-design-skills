<!-- design-validator 보고, oracle-portability design v0.3.8 (design/oracle-eo1: df3d1a08 v0.3.7 둘째 커밋 + ced5a45c v0.3.8, merge 9554b60a = master 93a9ff82), 읽기만, 2026-10-21 -->
## oracle-portability design v0.3.8 검증 결과

**점수: 84/100. 판정: 조건부. 필수 수정 2건을 고친 뒤 사용자 승인에 올린다.**

- v0.3.7 검증 지적 A·B와 N1~N8은 모두 해소됐다.
- DR-23 (1)~(3)도 빠짐없이 반영됐다.
- 남은 문제 둘:
  - (가) C10 `.ic`를 OP-3 소유로 확정했는데, 계획은 안정성·C10을 OP-4 몫으로 적는다. 이 OP-3 귀속은 내 v0.3.7 보고의 권고였고, 그 권고가 틀렸다(자기 정정).
  - (나) OP-10의 입력 망 계단 갈래 미룸이 계획 문언보다 넓다. 원래 취지와 다른 결정으로 표시해 보고해야 한다.

- 방법: `diff f5b72b9d..df3d1a08`과 `diff 9554b60a..ced5a45c`를 단어 단위로 전부 읽었다. merge 커밋 `9554b60a`는 oracle design을 바꾸지 않았다.
- 계획 확인: 이 tree의 계획 파일은 master `93a9ff82`와 같다(`git diff --quiet` 확인).
- 인용 재측정: design 41(`ab916aba`, `88bc5f2f`), `dc_edges.py:11`, `user_decisions.md` O-78~O-80.

### 1. v0.3.7 지적 해소 (df3d1a08)
| 지적 | 결과 |
|---|---|
| 필수 A (§11.7 묵은 문장) | 해소. `icmr_coord` 소비자를 r과 검사 (4)로 줄였고, `range_final` ICMR 끝 = `v_in` |
| 필수 B (근거 (2) 물리) | 해소. "같은 해 곡선, 매개만 다름, 막는 이유 = 정의 밖"으로 다시 썼다. §19.2에 O-78 (3) 승인을 근거로 적었다 |
| N1 포트 집합 | 해소. 엔진 design 41 v1.12.4 인용 780·784·811행을 `ab916aba`에서 확인했다. 세 metric 모두 묶인 포트를 뺀다. 그래서 design 해석이 아니라 엔진 정의와 일치한다 |
| N2 인용 | 해소 |
| N3 A_d | 해소. A_d = ½{[T(a→oa) − T(a→ob)] − [T(b→oa) − T(b→ob)]}. ±½ 중첩으로 다시 유도해 맞음을 확인했다. 새 `.tf`는 없다 |
| N4~N8 | 해소. min·max 끝, ½(V_a+V_b) = cm0 + 2y 단언, 시뮬레이터 호출 전 `excite` 이름 비교, DC 닫힘 포트의 레일 필터, 'FAIL 대 fail-closed' 구분 모두 반영됐다 |
| C10 문장, r 백로그 메모 | 반영됐다. 다만 C10의 OP-3 귀속은 아래 M1로 다시 연다 |

### 2. DR-23 반영 점검
| 항목 | 결과 |
|---|---|
| (1) 1b를 OP-10에서 뺌 | 반영. §21.6 1b 본문은 미룸 문장과 history로 옮겼다. §7 `feedback_config_undeclared` (b) `input_network_step_deferred`(옛 `no_input_network` 대체), (c) `start_op_deferred`. §18.1 OP-10은 '측정 구성 거부' (i)~(iv), §20 OP-10 행은 범위를 줄였다. §19.2에 AP-1 이관 목록이 있다. 시작점은 `v_in` 참조, 둘째 `.op`는 금지다 |
| (1) `Tran.ic`·`tran_ic_bias_only` 유지, 소비자 = C10 | 소비자가 있으니 쓰는 회로 없는 경로는 아니다. §20과 §18.1 'OP-3 C10 `.ic`' 행에 배선돼 있다. **그런데 귀속 card가 계획과 어긋난다 → M1** |
| (1) DV-20 | 반영. C10 몫으로 줄였고 1b 몫은 AP-1로 옮겼다 |
| (2) DV-19 닫힘 | 반영. §21.2 (e)는 "정의 자리 = gain-budget v6.26 N3.8 문장 하나, 인용만" 꼴이다. §7과 §18.1에 판정 조건(단일 출력·입력 ≥ 2·용량만)이 다시 나오지만 구현에 필요한 최소 술어다. 규칙을 새로 만들지는 않았다 |
| R2 우선순위 | 반영. (d) 단일 입력이 (e)보다 먼저다. §18.1 (iii)에서 순서를 바꾼 변형은 red다. 엔진 41 734행 '`as_is_single_input`이 먼저'와 같다 |
| (3) `[]` 매핑 | v0.3.7에서 반영했고, v0.3.8에서 계획 v0.6.15 N3.9 문장 인용을 더했다 |

### 3. 사유 이름: `icmr_feedback_dc_absent` ↔ `icm_config_feedback_no_dc`
**판정: 받아들일 만하다. 이름을 하나로 통일할 필요는 없다.**

- 계획이 이름 소유를 둘로 나눴다. gain-budget N3.8 584행은 "사유 기록 -- 이름은 design 41", oracle DR-23 (2)는 "사유 이름은 design"이다.
- 오라클은 엔진을 import하지 않는다(NFR-P3). 사유 문자열은 graph 필드가 아니다. graph 규칙 3은 같은 정의의 **양**을 필드 하나로 두라는 규칙이다. 각 시스템의 사유 어휘는 각자 하나씩이면 된다.
- 선례: 기존 짝(`feedback_config_undeclared` ↔ `icm_config_differential_output_undeclared`, `inverting_port_undetermined` ↔ `icm_inverting_port_none/ambiguous/unresolved`)은 이름이 다르다. 그 대응을 적은 곳이 oracle design에 **없다**(grep 결과 엔진 이름은 새 것 하나뿐). 이번 §7·§19.2 대응 메모가 첫 명시다.
- 권고(N2): ICMR 구성 사유 짝 전체를 대응표 하나로 묶는다. 엔진은 세 code로 나누고 오라클은 code 하나와 `detail.why`로 나누는 입도 차이도 함께 적는다. 검증자 원인 변화표가 이 표를 읽는다.

### 4. 묵은 문장
- 본문 규칙에 1b를 OP-10에 두거나 `no_input_network`를 현행으로 쓰는 문장은 **없다**.
- 다만 아래 문장은 머리 표시(v0.3.8 정정)만 붙은 채 옛 본문이 남아 있다:
  - F-4 끝 칸 "DV-20 멈춤(… §18.1 OP-10 손 회로 test 통과가 관문)"
  - F-5 본문
  - §20 OP-10 행의 "남은 막음 = DV-20 … 1b만"
  - 1611행 v0.3.6 상태
  - 1662행
- 판 이력 문장이라 결함은 아니다. 다만 F-4 관문 칸은 지운 test를 가리키므로 history로 옮기면 좋다(N3).

### 5. graph 단일 정본 점검 (별도 항목)
| 대상 | 판정 |
|---|---|
| 1b 닫힘 `.op` → `Tran.ic` | 위반 후보 제거. OP 범위에 writer가 없다. AP-1에서 시작점은 `v_in` 참조로만 쓴다 |
| `Tran.ic`·`tran_ic_bias_only` | 준수. 칸 하나·능력 하나, 소비자 C10. 단 만드는 card와 쓰는 card가 같아야 하므로 M1 |
| `feedback_config_undeclared` 새 `why` 둘 | 준수. 새 코드나 사본이 없다 |
| `icmr_feedback_dc_absent` | 준수. 정의는 gb N3.8 인용이고 `detail`은 출력 넷 이름뿐이다 |
| 'DC 성분' 분류 | **잠재 불일치(N1)**. 오라클은 `Resistor`·`Inductor`, 엔진 `DC_CONDUCTING_PASSIVE_KINDS = ("resistor",)`(`dc_edges.py:11`)로 집합이 다르다. 오라클 입력 `/passives` kind가 `resistor`·`capacitor`뿐이라 `Inductor`는 도달할 수 없어 지금 발동 0이다. 하지만 같은 경계(gb N3.8 'DC 성분')를 두 집합으로 적은 꼴이다 |
| 새 cache·memo·slot·값 칸·둘째 생산자 | 없다 |

### 6. design ↔ 계획 gap (DR-23, O-78, O-79, O-80)
| 계획 문장 | design 자리 | 판정 |
|---|---|---|
| DR-23 (1) 1b를 OP-10에서 구현하지 않음(AP-1) | §21.6 1b, §20 OP-10, §19.2 v0.3.8, §19.5, F-4 | 일치 |
| DR-23 (1) OP-10에서 정의 불능 + 사유(이름 design) | §7 (b)(c), §18.1 OP-10 (i)(ii) | 일치. **단 (b)의 범위가 넓다 → M2** |
| DR-23 (1) IR·능력·test·실현 가능성 행 처리, 쓰는 회로 없는 경로 금지 | §5 340, §8.3, §4.2, F-10, §18.1 OP-3 C10 | 처리했다. **귀속 card는 계획 OP-4와 어긋남 → M1** |
| DR-23 (1) 시작점 = `v_in`, 둘째 `.op` 금지 | §21.6 1b, §19.2 AP-1 목록, §19.5, graph 표 | 일치 |
| DR-23 (1) DV-20 1b 몫 이관, C10 쪽은 design이 적음 | §19.2 DV-20, §19.3 1663, F-10 | 일치 |
| DR-23 (2) / O-78 (2) / O-79 DV-19 = 정의 불능, 0개, 정의 자리 gb N3.8 하나 | §21.2 (e), §7, §19.2 DV-19, F-12, §18.1 OP-5 (e) | 일치. F-12에서 13개 가운데 0개를 다시 쟀다 |
| O-80 R2 단일 입력 먼저 | §21.2 (e), §18.1 (iii) | 일치 |
| DR-23 (3) / O-78 (3) `[]` → `unity_follower` | §11.6 `/measure_feedback` | 일치 |
| 계획 OP-10 행 "그 경로 = 정의 불능 + 사유; 미선언 차동 출력 정의 불능은 그대로" | §7 (a)(b)(c) | 일치 |
| DR-22(줄인 판): 과도 되먹임 = 선언 구성 전체, 슬루 갈래 = 미선언 차동 출력만 | §21.6 1단계, §7 `measure_feedback_undeclared` 이름 대응 | 일치 |
| X-36 (1)(2) | §19.2 v0.3.8 | 일치 |
| gb N6.22 AP-1 "오라클 코드는 AP-1 착수 때 oracle-portability 계획에 OP card를 열어" | §19.2 AP-1 이관 목록 | 일치. 인용문을 실측했다 |
| 계획 OP-4 행 "안정성: C10 규칙 코어화 … `stability_op_netlist` 삭제", N4 OP-4 "C10 판정 상태 … 기존 과도 fixture 판정 불변" | design은 C10 `.ic` 이전을 **OP-3**에 둠(§20 OP-3, §18.1, §4.2, §8.3) | **어긋남 → M1** |
| O-79 IT-2c 쪽 수정 | gain-budget 몫, 이 design 범위 밖 | 해당 없음 |

### 7. 원래 취지와 다름: current_reuse 슬루 사유 문자열
- 결과(정의 불능, fail-closed)는 같고, 사유 이름은 DR-23이 design에 맡겼다. 그래서 **위임 안에 든다.**
- current_reuse는 O-78 (1)이 AP-1의 첫 대표 회로로 지목했다. 따라서 '영구히 입력 망 없음'보다 'AP-1까지 미룸'이 그 회로에는 더 정확한 원인이다.
- 다만 두 가지는 보고해야 한다:
  - v0.3.6에서 사용자에게 "current_reuse 슬루 = `no_input_network`(입력 망 없음)"로 보고했다. 원인 분류가 바뀐 것이므로 알린다.
  - M2와 묶어 '원래 취지와 다름(경미)'으로 표시한다.

### 필수 수정 (must-fix)
1. **M1 C10 `.ic` 귀속 card를 계획 OP-4로 맞춘다.**
   - 계획 OP-4 행은 안정성 C10 코어화와 `stability_op_netlist` 삭제를 갖는다. N4 OP-4는 C10 판정 불변(동일성)을 갖는다.
   - design은 §20 OP-3 행이 §4·§5·§8.1~8.3을 범위로 갖는다는 이유로 OP-3을 택했다. 그런데 §4.2 `stab_benches` 행은 계획상 OP-4 몫이다. 계획 OP-10 선행에도 "OP-4(과도 코어·어댑터)"라고 적혀 있다.
   - (내 v0.3.7 보고 5번의 'OP-3 소유' 권고는 §20만 보고 계획 OP-4 행을 확인하지 않은 오판이었다. 정정한다.)
   - 고칠 곳: §4.2, §5 340행, §8.3, §19.2 v0.3.8 상태, F-10, graph 표, §18.1 'OP-3 C10 `.ic`' 행 이름, §20 OP-3·OP-4 행.
   - `Tran.ic` 칸과 능력을 **같은 card(OP-4)에서 만들고 C10에 배선**한다. OP-3에서 만들고 OP-4에서 쓰면 그 사이에 소비자 없는 칸이 생긴다.
   - §20 OP-3의 '§5 전부'와 OP-4 과도 몫이 겹치는 점도 한 줄로 가른다.
2. **M2 `input_network_step_deferred`의 범위를 계획 문언보다 넓게 잡았으니 보고 표시한다.**
   - 계획은 '용량만 선언된 차동 출력'의 경로로서 입력 망 계단 갈래를 미룬다(N3.9 슬루 행 '구현 자리', DR-23 (1)).
   - design §7 (b)는 그보다 넓다. **구성이 모든 입력 포트에 닿는 모든 선언**(DC 성분 있는 선언, 단일 출력 포함)의 입력 망 계단까지 OP-10에서 뺀다.
   - 지금 해당 회로는 current_reuse 하나뿐이다. 쓰는 회로 없는 경로를 만들지 않는다는 원칙(만들면 배선)과도 맞는다.
   - 그래도 범위 축소이고 사유 문자열도 바뀌었다(7절). §19.2에 '원래 취지와 다름(경미)'으로 적고 사용자 결정 항목으로 올린다.
   - 다른 길: (b)를 용량만 선언된 차동 출력으로 좁히고, 그 밖의 경우는 '입력 망 원소의 다른 단자' 갈래를 OP-10에 남긴다. 단 쓰는 회로가 0개라 권고하지 않는다.

### 고치면 좋은 것 (nice-to-fix)
- N1: 'DC 성분' 분류 표기를 엔진 `DC_CONDUCTING_PASSIVE_KINDS`와 맞춘다. 또는 입력 `/passives` kind가 `resistor`·`capacitor`뿐이라 `Inductor`는 도달할 수 없다고 한 줄 적는다.
- N2: 오라클↔엔진 ICMR 구성 사유 대응표를 기존 짝까지 포함해 한 곳(§19.2 알림)에 두고, 입도 차이를 함께 적는다.
- N3: F-4 끝 칸의 지운 test 관문 문장과 §20 OP-10 행 "남은 막음 = DV-20 … 1b만"을 history로 옮기거나 취소선 표시한다.
- N4: current_reuse처럼 (b)와 (c)가 둘 다 해당하는 회로에서는 (b)만 기록된다. 필요하면 `detail`에 둘 다 해당함을 적는다. 선택 사항이다.

### 미확인
- 엔진 design 41 v1.12.5(`88bc5f2f`)는 승인 대기다. 이름 대응은 그 승인 뒤 확정된다.
- C10을 실제로 돌리는 회로 수(F-10, design도 '미확인'으로 적음).
- §18.1 OP-3 C10 test 파일 이름과 test glob 충돌(design이 '미확인'으로 적음).
- DV-20 ngspice 원문 쪽 번호.
- history 파일은 v0.3.7 둘째 커밋 행과 v0.3.8 행을 diff로만 확인했다.

### 사용자 승인 준비 여부
**아직 아니다.** M1(귀속 card 정정, 문장 수정 수준)과 M2('원래 취지와 다름' 표시와 결정 항목)를 반영한 뒤 올린다. 계획 개정은 필요 없다. M2를 사용자가 승인하면 그대로 두고, 거부하면 (b)를 좁힌다.

### 관련 파일
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/02-design/features/oracle-portability.design.md` (§4.2 322, §5 341, §7 476-478, §8.3 576, §11.6 1051, §18.1 1452-1455, §19.2 1604-1621, §19.6 F-4 1719·F-10~F-12 1725-1727, graph 표 1745-1754, §20 OP-3 1765·OP-4 1766·OP-10 1771, §21.2 (e) 1815, §21.6 1887-1889)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/01-plan/features/oracle-portability.plan.md` (OP-3 499, OP-4 500, OP-10 505, N4 466-467, DR-22 718, DR-23 719, N3.9 444·446)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/docs/01-plan/features/gain-budget-gmid-sizing.plan.md` (N3.8 584, N6.22 2019~)
- `C:/Users/HSLEE/Documents/Todoc/fpga/wt/design-oracle-eo1/skills/analog-gmid-design/gmid_engine/authoring/dc_edges.py` (11)
- design 41: `ab916aba` 780·784·811행, `88bc5f2f` 734·744행
