verdict: Major 3

# JC-1 design 독립 검증 (design v1.16.25, 커밋 `14ed24a3`, 기점 `f1dd8f52`)

- 역할: 독립 검증자(작성자 아님). 읽기·`git -C show/diff/grep`만 했다. 수정·커밋·test·ngspice는 0이다.
- 대상 diff: `git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261106-jc1-card diff f1dd8f52 14ed24a3`(4파일 +34/−15). 사본 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc1v/diff.txt`.
- 정본: 계획 N6.42(plan.md:2683-2702), DEC-91(plan.md:291), 결정 O-247·O-248·O-249(`_drafts/user_decisions.md:1228-1230`).
- 원칙 8 용도 제한: 아래 엔진 인용은 (1) 엔진 밖 사실이 아니라 (2) 재작성 범위와 '그 design 문장이 사실인가'를 확인하는 데만 쓴다. as-built 꼴을 근거로 쓰지 않았다.
- 줄 번호: D40 = `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md`(14ed24a3), D41 = `...41-gain-budget.design.md`.

## Major

### M-1 -- 탐색 평가에서 r의 'W'를 design이 m·w_f로 다시 정의함(계획 문언 둘이 갈라지는데 멈추지 않음, 물리 일관성 위반, as-built 근거 사용)

- 자리: D40:1372 '**W의 뜻**'. D41:1251 'v1.16.25' 문장도 같은 문제다(층 0 국소 조각이 선택 함수의 (m, w_f)로 기하를 만든다).
- 사실:
  - 계획 DEC-91 (2)(plan.md:291)는 두 문장을 함께 둔다. 하나는 "레이아웃 전 r = 소자 폭 비례 … 소자 폭 비 W/w_ref와 같은 값"이고, 다른 하나는 "기하를 읽는 자리는 둘 그대로(배치 확산 / 그 평가 `dc_finger` 행)"이다.
  - 탐색 평가에서는 `DeviceOp.W` = I·L/IDu_s이고 m·w_s = (1 + residual)·`DeviceOp.W`다(D40:1202, `FingerGeom.residual` 정의). 그래서 두 문장이 서로 다른 값을 낸다. design 자신도 "r = (1 + residual)·`DeviceOp.W`/w_ref"라고 적는다.
  - design은 멈추지 않고 "r의 W = 그 평가 `dc_finger`의 m·w_f"로 정했다. 이것은 계획 용어를 design이 해석해서 닫은 것이다. 착수 원칙(계획과 다르면 계획부터, S-7)을 어긴다.
  - 근거로 든 "WB-1 뒤 지금 엔진과 같은 꼴"은 as-built 근거다(원칙 8 위반). "손계산 오차 → E-1"도 맞지 않는다. 이 차이는 근사 오차가 아니라 같은 평가 안에서 고른 정의다.
- 물리·graph 판정:
  1. **한 평가 안에서 소자 폭이 둘이 된다.** 같은 소자의 Cgs·Cgd·Cgb(`caps(…, op.W)`), gm, gds, 전류는 `DeviceOp.W`를 쓴다(base `ss_linearize.py:79·85`). 그런데 Cdb·Csb만 (1 + residual)·W 소자의 값을 쓴다. 물리적으로 한 소자가 아니다.
  2. D40 §3.7-A 3 '소비 기준'(D40:1219)은 "총 폭에 비례하는 양 → `DeviceOp.W`, 손가락 분할로 달라지는 양 → `dc_finger`"로 가른다. 면적 하나만 쓰는 r는 레이아웃 전에 m·w_f/w_ref, 곧 **총 폭의 함수**다. 손가락 분할(m 대 w_f 배분)에는 의존하지 않는다. 그러니 그 기준대로 하면 `DeviceOp.W`를 읽는 쪽이다. 옛 BSIM4 식은 둘레(pd = w_f + 연장)가 분할에 따라 달라져서 `dc_finger`가 필요했지만, 그 이유가 이번 card로 사라진다.
  3. D40:1216은 "실현 총 폭 = 실현 평가 `DeviceOp.W`이고 m·w_f를 따로 계산하거나 저장하지 않는다"고 적는다. 탐색 평가에서 r = m·w_f/w_ref를 쓰면 총 폭에 해당하는 둘째 양을 계산하는 셈이다(graph 규칙 3에 걸림).
  4. 판정 값은 바뀌지 않는다. front 점 판정은 실현 평가에서 하고, 거기서는 residual = 0이라 두 해석의 값이 같다(design도 이렇게 적는다). 따라서 `DeviceOp.W` 쪽을 택하면 물리 일관성만 얻고 판정 비용은 0이다.
- 고칠 방법: design에서 멈추고 계획 DEC-91 (2)·N6.42 범위 1부터 고친다.
  - 권고안(가): 레이아웃 전 r = `DeviceOp.W`/w_ref로 한다. 그 평가의 소자 폭은 하나이고, 기하 = `from_lut_rule(lut_rule_decl, DeviceOp.W, 1)` 또는 같은 값의 면적 비로 둔다. 레이아웃 뒤 배치 소자는 `ly.diffusion` 면적 비 그대로다. 그러면 '기하 자리 둘'은 접합 쪽에서 (배치 확산 / `DeviceOp.W`)가 된다. `dc_finger`의 소비자는 oracle 넷리스트와 mismatch 쪽에 남는다.
  - 대안(나): `dc_finger`를 유지한다. 이 경우 계획에 "탐색 평가의 r는 (1 + residual)·W/w_ref, 정의 축 = 손가락 실현 폭"을 정의 축과 함께 명시하고 '원래 취지와 다름'으로 표지한 뒤 승인받는다.
  - 두 안 모두 D41:1251(층 0 국소 조각)의 기하 입력을 같은 쪽으로 맞춘다.
  - ⚠ (나)는 위 1·2·3 때문에 원칙 1·7과 긴장한다.

### M-2 -- 접합 값 음수에 대한 런타임 fail-closed 없음(E-0 실현 가능·O-197 이식성)

- 자리: D40:1368-1369 (i) 4·5 "분기·문턱·클램프 0"와 D40:1378 (viii)(2). 수동성을 test 시점의 toy와 2회로에서만 단언한다.
- 사실:
  - 음수가 0인 것은 sky130 LUT 한 장에서만 잰 데이터 성질이다. off 단면 전 칸 8 820칸(nmos·pmos 모두)이 0이었다(`combo5_offregion_junction.md` §1 'Dd·Ss 음수 0/8 820').
  - 다선형 보간은 음이 아닌 가중치를 쓰므로, 그 LUT에서는 조회 값도 음수가 될 수 없다.
  - 그러나 같은 생성기의 CSS·CGS는 켜진 점에서 음수가 나온다(base `lut/cap_query.py:9-10`, 조합 (3) 'Csb 음수 10/10' -- `d4_d5_question.md:23`). 차 CDD − CGD·CSS − CGS가 음수가 될 수 있는 열 꼴이라는 뜻이다.
  - O-197은 "PDK를 바꾸면 선언만 바꿔 동작"을 요구한다. 그러니 다른 PDK·LUT에서 음의 Cdb·Csb가 조용히 MNA에 들어갈 수 있다. 이것은 E-0(실현 가능, fail-closed -- 원칙 2·10, O-200, O-229 1)의 fail-open이다.
  - 완료 조건 (2)는 이 card의 test 시점에 두 회로만 본다. 런타임 관문이 아니다.
- 고칠 방법: `junction_at_vgs_min`의 5단계 반환 앞에 부호만 보는 관문을 둔다. cdb < 0 또는 csb < 0이면 분류된 정지(`SealViolationError`, 소자·kind·L·VDS·VSB·값)로 멈춘다. 상수는 0이고 경계는 물리 부호 0이라 클램프가 아니다.
  - 사유 이름은 새로 필요하다. design 규칙("새 사유가 필요하면 멈추고 보고")에 따라 오케스트레이터가 정한다.
  - 완료 조건 (8) fail-closed toy에 "CDD < CGD인 기준 폭 표 → 그 정지"를 더한다.
  - 계획 DEC-91 (2) '음수가 없다' 문장을 "실측 + 런타임 관문"으로 고친다.
  - 새 검증 도구가 아니라 엔진 식 한 줄이라 O-229 4에 걸리지 않는다.

### M-3 -- 재작성 범위 누락: 판정 분해능(NFR-5)에서 cdb·csb를 빼는 근거가 이 card로 사라짐

- 자리: D40:1374 (iv)·1376 (vi)·1377 (vii). (vii)의 대상은 `git grep -i junction`뿐이다.
- 사실(base `f1dd8f52`):
  - `gmid_engine/metrics/lut_parameters.py:5-7·22`: `LUT_PARAMETERS = ("gm", "gmb", "gds", "cgs", "cgd", "cgb")`. 근거 문장은 "cdb·csb 는 PDK 접합 파라미터 폐형식(DEC-91, ngspice 대조 2.3e-11)이라 LUT 조회 불확실성이 없고"이다.
  - metrics CONTRACT 9.1 :941도 같은 문장이고, R4 :1054는 "접합은 폐형식이라 이 절 대상 아님"이다.
  - 소비자는 실재한다: `ss_metrics.py:421` `lut_parameters(...)` → 모든 ss metric의 `MetricResult.resolution`.
  - JC-1 뒤에는 cdb·csb가 LUT 열(CDD·CGD·CSS·CGS)의 보간 값이 된다. 그래서 위 제외 근거가 거짓이 된다.
  - 그 결과 판정 분해능이 접합 몫만큼 과소 정의된다. 이 분해능은 E-1 닫기 [0, 분해능]과 LA-1 gain bin 폭이 소비한다.
  - 이 자리들은 한글 '접합'만 쓰고 'junction'이 없다. 그래서 (vii)의 grep 기준(계획 N6.42 범위 5와 같음)에 잡히지 않는다.
  - D40 §3.8 9(RS-1, D40:1353)의 p 집합 {gm, gmb, gds, cgs, cgd, cgb}도 같은 전제 위에 있다.
- 같은 grep 공백으로 문언만 낡는 자리(분류 누락):
  - `_module_map.py:797`: ss_dev 설명 "PDK 접합 용량 cdb·csb"
  - `layout/contract_output.py:321·323`: "엔진 접합 용량 … 같은 값을 쓴다", "접합 용량이 `pd - Weffcj` 를 STI 측벽으로 쓴다". (v) ⑨는 :322만 유지로 분류했고, :323은 `diffusion.py:13-14`와 같은 엔진 식 가리킴인데 빠졌다.
  - layout CONTRACT :412-414: "같은 값을 쓴다"
  - `core/pdk_decl.py:10`, core CONTRACT :368: "DEC-91 접합 파라미터"
- 고칠 방법: 계획 N6.42 범위 4·5에 두 가지를 더한다(design보다 계획이 먼저, S-7).
  - (a) 분류 대상 grep을 `junction|접합`(대소문자 무시)로 넓힌다.
  - (b) 분해능 처리를 정한다. 권고는 `LUT_PARAMETERS`에 cdb·csb를 넣고 Δp = ε_d·|p|로 두는 것이다. 9.1의 기존 규칙("모든 LUT 열 … 같은 상대 크기")을 그대로 적용하므로 새 상수가 0이다. 대안은 RS-1로 미루면서 그 사이 분해능이 접합 몫을 빼고 있다는 사실을 계획과 LA-1 재점검 입력에 적는 것이다.
  - ⚠ 대안은 LA-1 측정이 과소 분해능 위에서 이루어진다는 뜻이다(O-247이 LA-1 기록을 E-2 트리거로 씀).
  - 어느 쪽이든 완료 조건에 '분해능 Δp에 cdb·csb 항(또는 미룸 표지)'을 넣는다.

## minor (LA-1 재점검 입력 -- O-229 3)

- m1 (D40:1368 (i) 3): CGS 결손 판별을 `c.model ≠ "lut_cgs_cgb"`로 하면 CGS는 있고 CGB만 없는 표도 column "CGS"로 보고된다(`cap_query.py:39`의 `full` = CGS ∧ CGB). 사유는 fail-closed라 맞지만 detail이 틀린다. `cap_map[kind].CGS is None`으로 판별하는 편이 정확하다. 질문 (b) 'CGS 열 없으면 정지, CGG − CGD 대체 금지'는 **계획 범위 안**이다. DEC-91 (2)는 Csb = CSS − CGS로 정의하고, 완료 (8)은 'C 열 없으면 분류된 정지'를 요구하며, CGG − CGD는 다른 정의다.
- m2 (D40:1356): "코드 식별자 = `vgs_axis_min` 계열 -- 아래 (ii)"라고 적었지만, (i)(ii)의 실제 이름은 `junction_at_vgs_min`·`lut_vgs_min_*`이고 `vgs_axis_min`은 어디에도 정의되지 않았다. 문언을 맞춰야 한다.
- m3 (D40:1378 (viii)(8)): fail-closed toy에 CSS 열 없음이 없다. (i) 3은 CSS도 검사하므로 toy 하나를 더 넣어야 짝이 맞는다.
- m4 (D40:1375 (v) ⑦): `kernel.py:147`에 경로가 없다. 실제는 `gmid_engine/search/kernel.py:147`이다(`sizing/kernel.py`는 base에 없음).
- m5 (D40:1378 (viii)(3)): "LUT memo point 키로 확인"이라 했지만, `lut_memo.py`는 hits·misses 계수(`stats`)만 내고 키 목록 접근자는 확인하지 못했다. test 작성 주체가 toy LUT 조회 인자로 확인하는 꼴로 적는 편이 판정 가능성이 분명하다.
- m6 (history v1.16.25 '원래 취지와 다름: 없음'): M-1을 (나)로 닫으면 '원래 취지와 다름' 표지가 필요하다.

## 질문 항목별 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| 1 식·r 정의·대칭 5칸·이중 계상 | **맞음**(r의 W 해석만 M-1) | 원본 Cdb = Cdd − Cgd(책 112쪽), QS 집중 용량(56쪽) -- `gmid_book_lut_definitions.md:96·105·115`. LUT CDD는 접합 포함(`lut_types.py:333`), off 점 rd 0.999~1.03(VDS ≥ 1격자, `combo5` §1). 스탬프 = `stamp_mos.py:28-34` 5칸(cgs·cgd·cgb·cdb·csb), Cdd 스탬프 0. Cdb는 off 점의 CDD − CGD이고 Cgd 칸은 평가 점 CGD라 이중 계상이 없다. 비상호 성분을 버리는 것은 계획 O-248 그대로다. |
| 2(a) residual | **M-1** | D40:1202·1216·1219, base `ss_linearize.py:79-85` |
| 2(b) CGS 없으면 정지 | 계획 범위 안(m1 detail만) | DEC-91 (2) 정의, N6.42 완료 (8) |
| 2(c) 음수 가드 | **M-2**(완료 (2)만으로는 부족) | 위 |
| 2(d) `JunctionSource.reference` | **graph 위반 아님** | 기존 S0 필드 `graph/kernel: junction_source` 칸이고, writer는 `junction_field` 하나다. 선언·LUT `w_ref_m`의 파생이며 S0당 1회다. 새 필드·cache·memo·sctx 슬롯은 0이다. 같은 값을 다른 자리에서 다시 만드는 생산자도 없다(base 비test `from_decls` 호출은 `junction_field.py:19` 하나). `reference.finger_w_m` = `cap_map[kind].w_ref_m`의 같은 float라 `caps(…, w_ref)`의 scale = 1.0이 비트로 정확하다(`cap_query.py:44`). |
| 2(e) 층 0·GB5 → LA-1 | 맞음 | base 엔진 비test·비md `node_c_farad`·`c_out` 계산 0건(`ls_fields.py:8` 주석뿐). 만들면 배선: `junction_at_vgs_min` 소비자는 지금 `ss_dev` 1이고, LA-1 층 0이 둘째 소비자다. |
| 3 off 점 = 조회 좌표 / O-249 | 맞음 | 모든 MOS에 같은 좌표 규칙을 쓰고, 전류·gm/ID·VTH·tol 문턱이나 분류 갈래가 0이다. O-249 "off는 선언으로만"과 모순되지 않는다. 출처 이름 `lut_vgs_min_*`·함수 `junction_at_vgs_min`에 'off'가 없다(m2 문언만). |
| 4 (iv)(v)(vi) base 줄 표본·grep 수 | 표본 맞음(m4, M-3 누락) | 아래 표 |
| 5 완료 조건 test 가능·상수 0·회로 이름 0·O-197 | test 가능(m3·m5) | toy 값이 이진 유한 소수라 비트 대조가 가능하다(ad = 3·2⁻²¹, AD_ref = 2⁻¹⁹ → r = 3/4 = m·w_f/w_ref). 새 코드 리터럴은 0, 회로 이름은 0이다. O-197 정규식은 base에서 고칠 4파일 밖의 적중이 `metrics/__init__.py:95·258·340`뿐이라 병합 뒤 0이 될 수 있다. `perMod` 문언은 대소문자 구분으로 걸리지 않는다. |
| 6 graph 단일 정본·만들면 배선 | writer `ss_dev` 하나 맞음(M-1의 '둘째 폭'만) | 새 필드·cache·사본 0. G-10: memo point 키 = (kind, lo, hi, l_val, vgs_min, vds, vsb, w_ref)라 같은 (kind, L, VDS, VSB) 소자끼리 적중한다(`cap_query.py:52`). |

### 4번 표본 대조(base `f1dd8f52`, `git -C … show`)

| design 인용 | 실측 |
|---|---|
| `junction_cap.py` :23 `_PREFIX`, :26 `_PERMODS`, :37-88 `JunctionParams`, :119-124 `JunctionCaps`, :127-148, :150-171 `junction_caps`, 유지 :24-25·:90-116 | 모두 일치 |
| `junction_source.py` :12 import, :19-25 칸, :28-36 `from_decls`, :38-40 `params_of` | 일치 |
| `junction_field.py` :18-19 | 일치(extras 풀기·호출) |
| `ss_linearize.py` :38 import, :46-47 값, :71-89 `_linearize`, :80-81 호출, :112-115 off | 일치 |
| `metrics/__init__.py` :95·:257·:258·:340 | 일치 |
| `_module_map.py` :682-686 | 일치 |
| `search/search_context.py` :178 `junction_field(base, pdk_decl, …)`, :82-83 | 일치 |
| `ss_evaluate.py` :17-18, `aux_types.py` :28 | 일치 |
| (v) `seal_bulk_reverse.py:6·16·28`, `ss_off_op.py:9·18·50`, `converge_point.py:38·80·88`, `convergence_values.py:97·113·133`, `s0_fields.py:9·16·23·29`, `ss_types.py:6·23·38`, `ss_metrics.py:240`, `noise_devices.py:47-52`, `iv_noise.py:10`, `realized_geometry.py:21`, `compare.py:418·623`, descriptor :151·154 | 일치(`kernel.py:147` 경로만 m4) |
| (vi) `ss_circuit.py:60-61`, `stamp_mos.py:33-34`, `ls_fields.py:36`, 옛 출처 직접 호출 = `ss_linearize.py:81`·`junction_field.py:19` 각 1 | 일치 |
| search CONTRACT :84-85·:126-127·:139, core CONTRACT :450·:462-469 | 일치 |
| grep 수 (vii) | 다시 셈: 엔진 비test 비md 25파일 141줄, CONTRACT 6파일 77줄(convergence 7·core 4·layout 1·metrics 52·search 10·sizing 3), PDK 선언 55줄, oracle 소스 3파일 5줄 + README 2줄, 엔진 test 33파일 435줄, oracle test 2파일 8줄, assets 다른 파일 4파일 13줄, legacy 2파일 10줄 -- **모두 일치**. 다만 grep 기준 자체가 한글 '접합' 자리를 놓친다(M-3). |

## 재지 않은 것

- test·ngspice·pytest 0(브리핑대로).
- 선택 함수가 내는 |residual|의 실제 분포(M-1의 크기). 판정 값에는 영향이 0이라 판정에 쓰지 않았다.
- metrics·core·search·convergence·sizing·layout CONTRACT의 모든 줄 번호. 표본만 대조했다.
- `fp_of`가 `JunctionSource.reference`(DiffusionGeometry tuple)를 지문으로 받는지. 옛 `JunctionParams` frozen 묶음이 extras에 있었으므로 같은 꼴로 보고 직접 실행하지 않았다.
- `d4_d5_question.md`·`o248_plan_verdict.md`는 관련 문장만 grep했다(음수·분해능·residual).
- 결정 간 모순 전수 점검(원칙 20)은 이 판정의 범위 밖이다. M-1·M-2·M-3 개정안을 낼 때 점검자 ≠ 권고 작성자로 따로 해야 한다.

## 재검증

re-verdict: Major 1

- 대상: worktree `wt/20261106-jc1-card`(design/jc1) 머리 `c0821886`. design 변경 = `git -C … diff 14ed24a3 c0821886 -- docs/02-design`이고, 개정 2 `782af40e`와 개정 3 `c0821886`이 해당한다. 기준 계획은 같은 worktree의 v6.38.30이다(DEC-91 (2) P:291, DEC-105 (8) P:305, DEC-107 P:307, N6.42 P:2686-2705). 위임은 A-147·A-149~A-153(`_drafts/la1_auto_decisions.md:153-159`)이다.
- 줄 번호: D40은 `c0821886`의 40-engine design이다(§3.8 10 = D40:1354-1377). 사본은 `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc1v/d40.md`·`d41.md`·`plan.md`이다.
- 읽기·grep·`git show`만 했다. test·ngspice는 0이다. 원칙 8 용도 제한: 엔진 인용은 design 사실 문장의 진위 확인과 재작성 범위 확인에만 썼다.

### 1. 앞 Major·minor 해소

| 항목 | 상태 | 근거(실측) |
|---|---|---|
| M-1 W 정의 | **닫힘** | 계획 P:291 "소자 폭은 그 평가가 쓴 W 하나 … `off` 선언 소자 = 선언 `w_m` … 접합은 `dc_finger`를 읽지 않는다". D40:1357(r = W/w_ref, 레이아웃 뒤 = 면적 비, 둘째 폭 m·w_s 0), D40:1371 (ii)(`pre_layout_geometry(op.W, 1)`, `dc_finger` READS·`_finger_row` 삭제), D40:1217·1218·1219(§3.7-A 3 소비 기준·소비자 문장 갱신), D41:1251(층 0 국소 조각도 W 하나). 원래 취지와 다름 표지가 있다(history 1022행). toy (1)(a)가 '`dc_finger`를 바꿔도 cdb·csb 불변'으로 갈림을 단언한다. |
| M-2 음수 관문 | **닫힘** | D40:1359 (b)·D40:1369 (i) 5: `not (v >= 0)`이므로 음수와 NaN을 모두 잡는다. 경계는 부호 0이고 상수는 0이다. 사유 `junction_cap_negative`{소자, 단자, 값}는 계획에 있는 이름이다(P:291·P:2703 (8)). toy는 d·s·NaN·MNA 미도달을 본다((viii)(8)). 'sky130 음수 0'은 실측 사실로만 적고 규칙 근거로 쓰지 않았다. |
| M-3 분해능 | **닫힘**(공통 ε_d Major 0) | D40:1372 (iv)에서 JC-1의 몫은 `LUT_PARAMETERS`에 cdb·csb를 넣는 소속 하나뿐이다. Δp 꼴의 정본은 DEC-105 (8)·RS-1이다. 과도기에는 '같은 함수 하나'를 쓰고, 공통 ε_d는 **'과도기 as-built' 표지로만** 적었다. (viii)(10)(c)는 "공통 ε_d 식으로 기대값을 만들지 않는다"고 적었다. 규칙 근거나 기대값으로 ε_d를 쓰는 자리는 0이다(D40·D41에서 `ε_d` grep = D40:1353(RS-1 '옛 … 지운다')·1372(표지)·1376(금지 문장)뿐이다). 계획 P:2700 범위 4 문언과 같다. 남은 문언 누락은 아래 r-m3·r-m4(minor)다. |
| m1 열 단위 판별 | 닫힘 | D40:1366 (i) 2: `"CDD"`/`"CSS"` ∉ `table.columns`, `table.CGS is None`, CGB와 섞지 않음. |
| m2 식별자 | 닫힘 | D40:1356: `junction_at_vgs_min`·`lut_vgs_min_*`. |
| m3 CSS toy | 닫힘 | (viii)(8)에 'CSS 열 없음 → column "CSS"'가 있다. |
| m4 경로 | 닫힘 | (v) ⑦ `E/search/kernel.py:147`. |
| m5 memo 키 | 닫힘 | (viii)(3)은 'toy LUT `caps` 조회 인자로 확인'이고, (6)은 `stats` 적중 수를 본다(`lut_memo.py:40` `stats` 실재). |
| m6 원래 취지 표지 | 닫힘 | history(c0821886) 1022행 "**원래 취지와 다름**: 엔진 접합 기하 자리 `dc_finger` → 그 평가가 쓴 W". |

### 2. gap `jc1_design_plan_gap.md` G1~G8

| gap | 상태 | 근거(실측) |
|---|---|---|
| G1 W 정의 | 닫힘 | M-1과 같다. |
| G2 base·순서 | 닫힘(표지) | D40:1364에 base = `4b968c0c`(WB-1 code 브랜치 머리)와 '계획 순서보다 앞당김 = 위임 A-147'이 있다. `git diff --stat f1dd8f52 4b968c0c -- skills/analog-gmid-design` = `references/gmid_sources/README.md` 1파일(+27)뿐이다(design 문장과 같음). `4b968c0c`는 `c0821886`의 조상이다. |
| G3 off 점 근거 시점 | 닫힘 | 계획에 DEC-107이 생겼고(P:307), N6.42 범위 1에 "조회 좌표, 꺼짐 분류 아님(DEC-107)"이 있다(P:2697). D40:1356은 그 둘을 인용한다. |
| G4 리터럴 lint | 닫힘 | (viii)(3)은 '기존 `tests/structure` 규칙 D'를 쓴다. `tests/structure/README.md:47` 'D 숫자 리터럴'이 실재한다. |
| G5 결정성 | 닫힘 | (viii) 머리에 '결정성 비트 동일'(cdb·csb·`junction_model`·S0 `junction_source`)이 있다. |
| G6 fail-closed toy | **부분 -- 아래 R-M1** | CSS toy는 들어갔다. 그러나 VGS 축 결손은 기존 test 인용에 기댔고, 그 test는 결손을 다루지 않는다(3 (e)). |
| G7 S0 bare ValueError | 닫힘(사유 선택은 r-m5) | 기준 폭 표 없음은 `SchemaRejectedError` `lut_cap_kind_undeclared`로 정지한다(실재 -- `lut/lut_set.py:299`, test `tests/lut/test_lut_set.py:242`). AD_ref·AS_ref = 0은 새 사유 `junction_reference_area_zero`로 정지한다. 온도 기록 없음은 기존 ValueError를 두고 '범위 밖'으로 표지했다. |
| G8 grep 한글 | 닫힘 | (vii) 대상 = `grep -n -i -E "junction\|접합" -- skills/analog-gmid-design`. 내가 `4b968c0c`에서 다시 센 값이 design 수와 **모두 일치**한다: 엔진 소스 32/182, 엔진 .md 7/99, PDK 선언 1/103, LUT 생성 규칙 1/1, oracle 소스 4/11, oracle .md 8/19, 엔진 test 37/477, oracle test 2/16, assets 다른 파일 6/15, references 8/16, legacy 4/18. 분류되지 않은 줄은 0이다(카테고리 밖 grep 결과 0). 앞 판정 M-3의 문언 자리(`_module_map.py:797`, `contract_output.py:321·323`, layout CONTRACT :412·:419, `core/pdk_decl.py:10·14`, core CONTRACT :343·:368, `lut_parameters.py:5-7`, metrics CONTRACT :941·R2·R4)도 (iv)에 들어갔다. |

### 3. 작성자 의문

- **(a) `_query`를 구조(devices 유무)로 가르는 것: 맞음.** LUT 쪽 정지는 모두 소자 없이 난다. `lut/_helpers_fail.py:15-17`의 `seal_violation`은 `SealViolationError(detail=…)`이고, `lut/` 비test에서 `devices=` 사용은 0건이다. (i) 2의 열 결손 정지도 소자 없이 던진다. 소자가 붙은 정지는 (i) 5 `junction_cap_negative`뿐이다. 사유 이름 목록으로 가르지 않으므로 새 사유가 생겨도 갈래가 늘지 않는다. 다만 이 갈림은 'LUT 조회 함수는 devices를 붙이지 않는다'는 불변식에 기댄다(r-m6).
- **(b) 새 사유 `junction_reference_area_zero`: 작성자 주장은 반만 맞다.** core CONTRACT :390·:417은 선언 식 결과에 대해 `pdk_quantity_invalid` = '유한하지 않거나 음수(**정확히 0 은 허용**)'로 정의한다. 그런데 같은 문서 :522와 `core/pdk_decl.py:570`은 저항 R□ ≤ 0(**0 거부**)에도 `pdk_quantity_invalid`를 쓴다. 따라서 '0이 의미 없는 양의 0을 거부'하는 기존 사유의 선례가 있다. A-147이 지시한 "사유 이름은 design이 기존 사유 표에서"와도 어긋난다. fail-closed는 어느 쪽이든 성립하므로 minor다(r-m5).
- **(c) `dc_finger` READS 제거 뒤 MOD8 nf 무효화(DEC-91 (4)): 충분하다.**
  - 배치 소자의 nf가 바뀌면 `ly.diffusion`이 바뀌고, extra `diffusion`이 바뀌며(`ss_dev` 입력 버전 = 이름·코드·READS·extras 투영의 지문), 그래서 재계산된다.
  - 배치되지 않은 소자는 r = W/w_ref라 nf와 무관하다. 이것은 정의상 맞는 결과이고 무효화 누락이 아니다. nf와 함께 W가 바뀌면 `device.dc_op`(READS)가 바뀐다.
  - 남는 길은 0이다.
- **(d) 완료 (10)(b) '항 있는 분해능 > 항 없는 분해능': 판정 가능하다.** 조건은 toy의 `lut_rel_tol`이 None이 아니고 0보다 크며, metric이 cdb·csb에 감도를 가지는 것이다. 다만 '항 없는 = base 경로'라는 말이 base 커밋(BSIM4 값, 다른 cdb)과 같은 빌드에서 열만 6개로 줄인 경우 둘 다로 읽힌다. 엄격 부등식은 **같은 빌드·같은 cdb 값**이라야 원인이 하나로 떨어진다(r-m2). 또 (10)(a)의 '`"cdb"`·`"csb"` 문자열이 목록 정의 밖에 없음'은 같은 파일 `_VALUE_FIELDS`(`lut_parameters.py:23`, 단위 스탬프 0 칸 -- 이미 cdb·csb 포함)에 걸린다(r-m1).
- **(e) VGS 축 결손 test 인용: 그 결손을 다루지 않는다 → R-M1.**

### 4. Major

#### R-M1 -- 'VGS 축 결손 = 기존 적재 관문의 분류된 정지'라는 사실 문장이 틀렸고, 완료 (8)의 그 항목에 엔진 자리가 없다(계획과 다름·완료 조건을 판정할 수 없음)

- 자리: D40:1359 fail-closed (d) "`w_ref_m`·VGS 축 결손 = LUT 적재 관문의 기존 사유(`lut_cap_width_unresolved`·`lut_cap_axes_mismatch`)", D40:1376 (viii)(8) "VGS 축·`w_ref_m` 결손 = 기존 적재 test(`test_reject_cap_axes_mismatch`(:232-235)·…) 인용 -- 그 test가 VGS 축 결손 자체를 다루지 않으면 test 작성 주체가 같은 파일에 toy 하나를 더한다".
- 사실(c0821886):
  - `tests/lut/test_lut_set.py:225-235`는 축 값이 **다른** 경우만 본다(VGS = (0.0, 0.5, 1.1) 등). 축 키가 없는 경우는 보지 않는다.
  - 축 읽기 `lut/_helpers_grids.py:10` `npz_grids`는 `npz[axis]`를 그대로 읽는다. 그래서 VGS 키가 없으면 **분류되지 않은 `KeyError`**가 난다. 기준 폭 표(`lut_set.py:288`)도 슬라이스(`:183`)도 같다. `lut_cap_axes_mismatch`(:290)는 키를 읽은 뒤의 비교에서만 나온다.
  - `w_ref_m` 결손은 분류된다(`lut_set.py:313` `lut_cap_width_unresolved`). 사실 문장이 틀린 것은 VGS 축 쪽뿐이다.
  - 계획 완료 (8)(P:2703)은 "LUT VGS 축 … 없으면 분류된 정지"다.
  - design의 대비책("test 작성 주체가 toy를 더한다")대로 하면 그 toy는 `KeyError`로 실패한다. 통과하려면 lut 적재 코드를 고쳐야 하는데, 그 자리가 (iv) 재작성 범위에 없다. 그래서 card가 범위 위반 아니면 멈춤으로 간다.
  - fail-closed 자체(멈춤)는 성립한다. 어긋나는 것은 '분류된'이다.
- 고칠 방법(하나를 고른다):
  - (가) **권고**: (iv)에 lut 적재 자리 하나를 더한다. `npz_grids`가 필요한 축 키(`AXES`)가 없으면 `schema_rejected`로 정지하게 한다. 사유는 기존 `lut_cap_axes_mismatch`(기준 폭 표)·`lut_slice_axes_mismatch`(슬라이스)를 그 호출 자리마다 쓴다. 그러면 새 사유 0, 상수 0이다. test는 같은 파일에 '축 키 없음' toy를 둔다. fail-closed (d) 문장도 그 사실로 고친다.
  - (나) 계획에서 완료 (8)의 'VGS 축 없음'을 '축 불일치(빈 축 포함)'로 한정한다. 키 부재(`KeyError`, 분류 안 됨)는 LUT 파일 형식 위반으로 두고 LA-1 재점검 입력으로 넘긴다. 이 경우 계획 개정이 먼저다. ⚠ 원칙 10 쪽으로 약하다.

### 5. minor (LA-1 재점검 입력)

- r-m1 (D40:1376 (10)(a)): '`"cdb"`·`"csb"` 문자열이 목록 정의 밖에 없음' 검사는 `_VALUE_FIELDS`(`lut_parameters.py:23`, 이미 8열)에 걸린다. 검사 대상을 '`LUT_PARAMETERS`·`_VALUE_FIELDS` 정의 밖'으로 적거나 AST 순회 하나로 한정해야 한다.
- r-m2 (D40:1376 (10)(b)): '항 없는 분해능'은 **같은 빌드에서 `LUT_PARAMETERS`만 6열로 둔 경로**로 명시한다. base 커밋(BSIM4 값)은 red 대조로 따로 둔다. 그래야 엄격 부등식의 원인이 하나다.
- r-m3 (D40:1372 (iv)): metrics CONTRACT 9.1 본문 :938 "`LUT_PARAMETERS` = (gm, gmb, gds, cgs, cgd, cgb)"는 as-built 계약 서술인데, JC-1 뒤 as-built가 8열이 되므로 교체 목록에 넣어야 한다(지금은 :932 머리·:941·R2·R4만 있음).
- r-m4 (D40:1353 §3.8 9, RS-1 design): p 집합이 아직 6열이다. 계획 DEC-105 (8)(P:305)의 'card JC-1이 cdb·csb를 LUT 열 목록에 더한다·off 점 조회 열의 기울기 꼴 = RS-1 착수 조건' 표지가 이 절에 없다.
- r-m5 (D40:1359 (c)): 새 사유 `junction_reference_area_zero`는 A-147 지시('기존 사유 표에서')와 어긋나고, '같은 정의의 기존 사유 없음'이라는 전제는 core CONTRACT :522·`pdk_decl.py:570`(R□ ≤ 0 → `pdk_quantity_invalid`)의 선례와 맞지 않는다. 대안은 `pdk_quantity_invalid`{quantity = `lut_diffusion_ad_per_w_m`/`as_per_w_m`, value 0}를 쓰는 것이다(새 집합 0). 어느 쪽이든 fail-closed다. 오케스트레이터가 고른다(원칙: 새 집합·갈래 점검).
- r-m6 (D40:1371 (ii) `_query`): 구조 판별이 기대는 불변식('LUT 조회 함수는 `devices`를 붙이지 않는다' -- 지금 실측 lut/ 비test `devices=` 0건)을 spec card 계약 문장으로 적어 두기를 권고한다(새 도구 0).

### 6. 새 모순·graph·fail-closed·상수·O-197

- graph 단일 정본:
  - `device.ss_dev` writer는 `ss_dev` 하나다.
  - S0 비례 기준은 기존 필드 `graph/kernel: junction_source` 칸이고 writer는 `junction_field` 하나다.
  - 새 필드·cache·memo·sctx 슬롯·사본은 0이다.
  - 한 평가 안 소자 폭은 하나다(M-1 해소로 둘째 폭 0).
  - 층 0이 같은 함수를 부르므로 둘째 식은 0이다.
  - 위반 0.
- 만들면 배선: `junction_at_vgs_min`의 소비자는 `ss_dev`(지금)와 LA-1 층 0이다. `reference_of`의 소비자는 `ss_dev`다. `dc_finger` READS를 빼도 남는 소비자가 있다(oracle 넷리스트·mismatch, D40:1218).
- fail-closed: 음수·NaN 관문, 열 결손, S0 정지는 모두 분류된다. VGS 축 키 부재만 R-M1이다.
- 상수 0: 부호 경계 0, 축 최솟값은 데이터에서 읽고, toy의 이진 소수는 test 쪽이다.
- 회로 이름 0.
- O-197: PDK 값은 선언 한 곳에만 있다. 정규식 (viii)(4)는 그대로이고, tnom 두 키는 시점 표지대로다.
- 새 모순: 계획 DEC-91 (2)·DEC-105 (2) 소비 기준·DEC-107·N6.42와 design 사이 모순은 찾지 못했다. 다만 r-m4는 RS-1 design 문언이 계획보다 뒤처진 것이다.

### 7. 재지 않은 것

- test·ngspice 실행.
- `fp_of`가 `JunctionSource.reference`를 지문으로 받는지 실행 확인(앞 판정과 같음).
- (iv) 개정 2·3에서 새로 들어간 CONTRACT 줄 번호 전부. 표본으로 :932·:938·:941(9.1)만 확인했다.
- 42 '91' 행·§2.4.8 행 문언의 세부. 판 표지만 봤다.
- 결정 간 모순 전수 점검(원칙 20)은 범위 밖이다. R-M1 (나)를 택하면 따로 해야 한다.

## 재검증 2

re-verdict: Major 0

- 대상: 머리 `c394feef`(부모 `c0821886`), `git -C … diff c0821886 c394feef`. 바뀐 파일은 셋이다: D40 6줄, D42 1줄, history 1줄. 처리 기록은 A-155(`_drafts/la1_auto_decisions.md:161`)다.
- 줄 번호: D40은 `c394feef`의 40-engine design이다. 사본 = `C:/Users/HSLEE/AppData/Local/Temp/la1s_jc1v/d40b.md`.
- 읽기·grep·`git show`만 했다. test·ngspice는 0이다. 원칙 8 용도 제한: 엔진 인용은 design 사실 문장의 진위 확인과 재작성 범위 확인에만 썼다.

### 1. R-M1 해소 -- 닫힘

| 확인 | 결과(실측, `c394feef`) |
|---|---|
| (d) 문장 정정 | D40:1359 (d): `w_ref_m` 결손 = `lut_cap_width_unresolved`(`lut_set.py:313`). VGS(과 다른 `AXES`) 키 결손은 지금 `npz_grids`의 분류되지 않은 `KeyError`이고, `lut_cap_axes_mismatch`(:290)는 값 비교에서만 난다고 사실대로 적었다. 그 결손을 재작성 범위에 넣었다. |
| 호출 자리 여섯 | `git grep "npz_grids("` 비test 결과는 `lut_set.py:183·288·344·404`, `mismatch_set.py:66`, `noise_set.py:58`이다. design (iv) 'LUT 축 키 관문'(D40:1372)의 여섯 자리와 **일치**한다. |
| 기존 사유 | 다섯 개 모두 실재한다. `lut_cap_axes_mismatch`(lut_set.py:290), `lut_slice_axes_mismatch`(:184), `lut_midpoints_axes_mismatch`(:346), `lut_mismatch_axes_mismatch`(mismatch_set.py:71), `lut_noise_axes_mismatch`(noise_set.py:63). 새 사유·상수는 0이다. |
| 받아들이던 파일이 바뀌는가 | 바뀌지 않는다. 축 키가 없는 파일은 지금도 `KeyError`로 멈춘다. `npz_grids` 호출은 `mismatch_set.py:52-60`·`noise_set.py:42-50`의 `except (KeyError, ValueError)` 블록 **밖**에 있다. 그래서 이 변경은 분류되지 않은 정지를 분류된 정지로 바꿀 뿐이다(기준 약화 0, fail-closed 강화). |
| toy 둘 | D40:1376 (viii)(8): 'VGS 축 키가 없는 기준 폭 표 npz → `lut_cap_axes_mismatch`{path, axis "VGS"}(base red = `KeyError`)', '슬라이스 npz 축 키 결손 → `lut_slice_axes_mismatch`'. 같은 파일 `tests/lut/test_lut_set.py`에 둔다. 기존 test(:225-235)가 값 불일치만 다룬다는 사실도 적었다. |

### 2. r-m1~r-m6 반영 -- 모두 반영

- r-m1: (viii)(10)(a)의 검사 대상을 '`LUT_PARAMETERS`·`_VALUE_FIELDS`(:23) 정의 밖'과 AST 순회 하나로 한정했다.
- r-m2: '항 없는 분해능' = 같은 빌드·같은 toy·같은 cdb·csb 값에서 `LUT_PARAMETERS`만 6열로 둔 경로. base 커밋은 따로 red 대조다.
- r-m3: (iv)에 metrics CONTRACT 9.1 :938 '`LUT_PARAMETERS` = (gm, …, cgb)' → 8열이 들어갔다.
- r-m4: D40:1353 §3.8 9에 'v1.16.26 표지'가 붙었다. 내용은 JC-1이 cdb·csb를 `LUT_PARAMETERS`에 더한다는 것, 아래 p 집합은 JC-1 병합부터 8열이라는 것, 그리고 VGS 축 최소 조회 열의 기울기 꼴이 RS-1 착수 조건이라는 것이다.
- r-m5: S0 기준 면적 0 = 기존 `pdk_quantity_invalid`{quantity, value}. 선례 core CONTRACT :522 '`R□ <= 0` `pdk_quantity_invalid`'를 확인했다. `core/pdk_decl.py:96-97` `_reject`도 `SchemaRejectedError`라 같은 예외 부류다. 새 사유 0이고, A-147 '기존 사유 표에서'와 맞는다.
- r-m6: D40:1370 (ii)에 불변식 문장이 들어갔다. 'LUT 조회(`lut/` 비test)는 `devices`를 붙이지 않는다(실측 0건), 소자가 붙은 정지는 음수 관문 하나, 깨지면 갈림을 다시 정함'.

### 3. 작성자 의문

- **(1) 공용 helper가 범위 밖 잡음·mismatch·중점 호출 자리까지 바꾸는 것: 범위 위반(Major)이 아니다. 다만 범위 표지가 필요하다(s-m1).**
  - 계획 완료 (8)(P:2703)은 'LUT VGS 축 … 없으면 분류된 정지'를 요구한다. 그 엔진 자리는 축 읽기 helper 하나다.
  - 호출 자리 셋(lut_set :183·288·404)에서만 막는 길도 있기는 하다. 하지만 그러면 (가) 같은 키 검사를 호출 자리마다 복제하거나 (나) helper에 '사유 없으면 옛 `KeyError`' 갈래를 둬야 한다. (가)는 같은 판정의 둘째 생산자이고 (나)는 새 갈래라 덧대기다(원칙 7·10, 새 갈래 점검). helper 하나에 사유를 호출 자리가 넘기는 꼴이 원리 하나로 닫힌다.
  - 바뀌는 동작은 이미 멈추던 입력의 정지 분류뿐이다. 받아들이던 파일과 판정 값의 변화는 0이다. 그래서 'card 범위 밖 동작 변경'이라 부를 실질이 없다.
  - 계획 N6.42 범위 5는 `junction|접합` grep 분류라 이 자리를 덮지 않는다. 완료 (8)이 근거다.
  - 고칠 것은 둘이다. A-155 문언은 사유 둘(cap·slice)만 적었고, history 개정 4는 '원래 취지와 다름: 없음'이라 적었다. 따라서 범위 확장 사실(호출 자리 여섯·사유 다섯)을 history나 계획 N6.42 범위 표지로 남겨야 한다(s-m1).
  - LM-1e와 `lut_set.py`가 겹치는 문제는 design이 착수 때 rebase로 적었다(계획 P:2705 규칙 그대로).
- **(2) 기존 축 사유 정의에 '축 키 없음'이 드는 해석: 받아들일 수 있다. 단 원문 정의 문언 한 곳은 L을 빼고 있다(s-m3).**
  - lut CONTRACT :223-224(`lut_slice_axes_mismatch`·`lut_cap_axes_mismatch`)는 이름만 나열하고 정의는 코드의 축 비교(`npz_grids(npz) != grids`, `cap_grids[:3] != grids[:3]`)다.
  - mismatch :959 '축·기준 폭 다름', noise :896 '축·기준 폭 불일치' -- 키가 없는 축은 기준 축과 같을 수 없으므로 '다름'에 든다.
  - 중점 :251 (4)는 "`VGS`·`VDS`·`VS` 가 슬라이스 축과 float 단위로 다름"으로 **L을 뺀다**(중점 L은 정의상 슬라이스 L과 다름). 그래서 중점 파일의 L 키 부재를 `lut_midpoints_axes_mismatch`로 분류하면 원문 정의 밖이다.
  - 첫 슬라이스(:404)는 그 자체가 기준이라 '기준과 맞지 않음'이 문자 그대로 맞지 않는다.
  - design의 'lut CONTRACT 각 축 사유 문언에 「축 키 없음 포함」을 더한다'에서 '축 키(L 포함) 없음'과 첫 슬라이스 경우를 명시하면 닫힌다.

### 4. minor (LA-1 재점검 입력)

- s-m1: 축 키 관문의 범위 확장(호출 자리 여섯·사유 다섯 -- A-155 문언 둘보다 넓음)을 history 개정 4나 계획 N6.42 표지에 적는다. 지금은 '원래 취지와 다름: 없음'이다.
- s-m2: 완료 (8) toy는 기준 폭 표·슬라이스 둘뿐이다. 함께 바뀌는 중점(:344)·mismatch(:66)·noise(:58)·첫 슬라이스(:404) 정지는 test가 없다. 같은 파일에 호출 자리 여섯을 도는 parametrize toy 하나를 권고한다(새 도구 0, O-229 2 이 card test 범위).
- s-m3: lut CONTRACT 축 사유 문언 보강에 'L 포함'과 첫 슬라이스(기준 자체) 경우를 명시한다(중점 :251 (4)가 L을 뺌).

### 5. 새 모순·원칙 점검

- graph 단일 정본: 바뀐 것은 정지 분류와 문언뿐이다. 새 필드·cache·사본은 0이다. 축 키 검사 생산자는 helper 하나다.
- fail-closed: 강화만 있다(분류되지 않은 `KeyError` → 분류된 `SchemaRejectedError`). 받아들이던 입력의 변화는 0이다.
- 상수 0, 회로 이름 0, O-197 영향 0.
- 계획 DEC-91 (2)·DEC-105 (2)(8)·DEC-107·N6.42와 design 사이 새 모순은 찾지 못했다. 앞 재검증의 정합(M-1~M-3 해소)은 이번 diff가 건드리지 않았다(D40 바뀐 줄 = 12·1353·1359·1370·1372·1376).

### 6. 재지 않은 것

- test·ngspice 실행.
- 축 키 부재 `schema_rejected` detail 꼴({path, axis})을 읽는 소비자 유무. 기존 사유 detail은 {path} 또는 {path, kind}다.
- D42 '91' 행·history 개정 4 문언의 세부. 범위 표지 유무만 봤다.
- 결정 간 모순 전수 점검(원칙 20)은 범위 밖이다.
