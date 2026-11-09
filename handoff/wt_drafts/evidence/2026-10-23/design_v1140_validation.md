# design v1.14.0 독립 검증 (2026-10-23)

- 대상: `wt/design-v1131` `c545a528`(부모 `20b9f49d`). numstat은 40 = 16/16, 41 = 47/47, 42 = 6/6이고 줄 수는 그대로다.
- 정본: 계획 v6.35(같은 worktree), 사용자 결정 O-111~O-116.
- 엔진: integ-it12 `1fa7b1e5`.
- 읽기 전용으로 했고 git은 `git -C`만 썼다.

## 점수: 85 / 100

계획 v6.35·v6.34.2의 범위와 완료 조건은 빠짐없이 들어갔다. servo 연립, `IcmConfig` 칸, V_cm 좌표, B77, relabel, 보고 범위, L8 (a)~(g), L10, L12, L13이 모두 있다. 지운 이름의 엔진 소비자는 0이다.

감점은 세 곳이다.
- ICMR 전달 뷰를 spec 로드 칸에 두는 선택이 graph 단일 정본 쪽에서 걸린다(S-1).
- F 성분 미선언 포트를 구동에 넣는 선택이 계획과 design 697에 어긋난다(S-2).
- P (b) 단언을 바꿨는데 계획 문언은 그대로다(S-3).

## 1. 계획 반영 대조

| 계획 | design | 판정 |
|---|---|---|
| N3.8 servo 정의(감지 s를 `node.dc_v`에 묶음, e의 ε 하나, Schur 1칸, 단일·차동 출력 같은 연립, 단일 입력 = 회로 그대로, 선언 되먹임 안 읽음) | 41:729·734 (1)~(3), 40:556 | 일치 |
| `IcmConfig` 칸 = config·피벗(a_e, resolution)·V_cm 셋·undefined, `inverting_port`·`tied_ports`·`transfer` 삭제 | 41:732, 40:556, 42:229 | 일치 |
| 정의 불능 목록(뷰 없음·둘 이상, 입력 셋 이상, e ∥ CM, \|a_e\| 판정 불능, 특이, DC 결측) | 41:734 (1) ①~⑧ | 일치. 단 ⑤는 계획 목록에 없는 갈래(N-1) |
| ICMR 좌표 V_cm(U-106), 정본 = `graph.icm_config` 칸, 포트 창에서 다시 계산 금지 | 41:734 (6), 779~789(AST 대상 `icm_window_metrics`·`_icm_ports`) | 일치 |
| 실행 조건: a_e를 모든 config에서 기록 | 41:732·734 (5) | 일치 |
| B77 영역 규칙(`MetricSignature.domain`, dc = `graph.ss_nodal` Undefined만, 그 밖 = 결측 하나라도), relabel(`:56`~`:62` → dc, ff_gm_ratio ss), 보고 = 전달 뷰 보고만 막음(O-113) | 41:793 (가)~(마) | 일치 |
| 완료 조건 (8)(a)~(g) | 41:811 L8 | 일치(허용치·LUT 원시 함수·전제 단언 둘·(g) 음수 감도 전제 단언) |
| (10)(b)(c)(d) | 41:812 L10 | 일치((i) 삭제 → TN-1) |
| (12) | 41:814 L12 | 일치 |
| (13)(a)~(d) | 41:815 L13 | 일치 |
| (7)(b) | 41:809 P | **다름**: S-3 |

## 2. 작성자가 고른 7건 판정

| # | 결정 | 판정 | 근거 |
|---|---|---|---|
| (1) | ICMR 전달 뷰 = 새 칸 `SizingSpecDoc.icmr_view`(writer `constraint_declaration`) → `DcInputs.icm_view` → extras | **계획 위임 범위 안**("자리는 design")이지만 **원칙 문제가 있다 → S-1** | 아래 S-1 |
| (2) | gain 제약이 없는 회로는 기본 포트 뷰 | 위임 범위 안 | 계획 N3.8 "(선언이 없으면 기본 포트 뷰 -- `default_views`)". 해당 회로는 13개 중 `pushpull_follower_buffer` 하나(design 실측) |
| (3) | 여기 넷이 입력 포트 밖이면 `view_required` | 경계. "뷰 없음"으로 읽으면 위임 범위 안 → N-1 | 계획 정의 불능 목록에 이 갈래가 따로 없다 |
| (4) | 끝 상태를 레일 안 입력으로 자름 | 위임 범위 안 | 기존 규칙 "레일 밖 입력 불허"(40 §3.8-8)를 (8)(g) "포트 끝과 V_cm 끝이 같은 끝 상태"에 맞춰 적용한 것 |
| (5) | `as_is_single_input`은 a_e만 기록하고 피벗 판정 없음 | 위임 범위 안 | 계획 "실행 조건"이 a_e를 모든 config에서 기록하라고 한다. 피벗 판정 불능은 servo 보정 분모일 때만 정의 불능 사유가 된다 |
| (6) | F 성분 미선언 포트도 구동에 넣음(V_cm·metric은 정의 불능) | **계획 밖 → S-2** | 아래 S-2 |
| (7) | P (b)를 servo 손계산으로 바꾸고 계획 (7)(b) 문언은 둠 | **계획 밖(사실 정정 필요) → S-3** | 아래 S-3 |

## 3. 새 code 넷

- 계획은 "code 이름은 design"으로 위임했다(N3.8 정의 불능 문단, 'ICMR 전달 뷰' 문단).
- `icm_inputs_unsupported`(입력 셋 이상), `icm_excite_common_mode`(e ∥ CM), `icm_servo_pivot_unresolved`(\|a_e\| 판정 불능·특이·레일 폭 0)는 계획이 정한 갈래에 이름을 붙인 것이다. 기존 어휘에는 같은 뜻이 없다. `unsupported_rule_branch`는 정지(예외)이지 정의 불능 code가 아니다. 판정은 **수용**.
- `icm_servo_pivot_unresolved`는 옛 `icm_inverting_port_unresolved`를 대체하는 것이라 순증이 아니다.
- `icm_view_ambiguous`는 계획이 `view_required` 재사용을 "쓸지는 design"으로 열어 두었다. 원인과 고칠 자리가 다르다는 사유가 타당하다. **수용**.

## 4. 지운 이름의 소비자

- **엔진**(`1fa7b1e5`, `git grep`, tests 포함): `tied_ports`·`inverting_port`·`follower_beta1`·`declared_feedback`·`icm_config_feedback*`·`icm_inverting_port*`·`icm_config_differential_output*`·`_dc_feedback_reaches`·`kvl_sensitivity` 모두 **0건**이다. IT-2c 전이라 구현된 적이 없다.
- **design**(40·41·42): 남은 출현은 모두 삭제 목록, 부재 단언(L8 (f)), 기록(취소선 4.7-1a), Status 이력이다. 살아 있는 규칙으로 남은 곳은 없다.

## 5. 원칙과 G-10·층·`__all__`·CONTRACT

- **graph 단일 정본**: 새 graph 필드 0, cache 0, V_cm은 `icm_config` 한 자리, 포트 창 재계산 금지(AST)는 맞다. 새 입력 칸은 S-1.
- **fail-closed**: 모든 갈래가 definitional code로 정의 불능을 내고, a_e 작은 분모를 판정 분해능으로 닫았다(옛 B75 해소). 적합.
- **DC/AC 분리**: 용량 개방 DC 야코비안, B77 영역 규칙. 적합.
- **DEC-103**: 섭동은 KCL, 봉인점 = servo 동작점이라 외삽 0. 적합.
- **상수 0, 회로 이름 0**: role 이름이 결과를 정하지 않는다(맞바꿈 toy). 적합.
- **만들면 배선**: 피벗 칸은 출력 전용 선언이고, `inverting_port`·`tied_ports`는 삭제했다. 적합.
- **계획 먼저**: S-2·S-3이 남는다.
- **G-10**: 새 블록 0(`icm_config`·`ss_nodal`·`ss_circuit` 그대로). `icm_config` 입력 버전만 extras 변화로 바뀐다. 맞다.
- **층**: `icm_config`(metrics 3)가 authoring(2)의 `ViewDecl` 값을 extras로 받으므로 방향이 맞다. 맞다.
- **`sizing.__all__`**: 이번 판에서 새 공개 이름이 없다.
- **CONTRACT**: authoring CONTRACT(`SizingSpecDoc.icmr_view`)와 sizing CONTRACT(`DcInputs.icm_view`) 행이 4.7-6 41:797에 있다.

## 6. 지적

### G
없음.

### S

**S-1. ICMR 전달 뷰를 spec 로드 칸에 두면 "gain 제약 뷰" 판정이 두 번째로 생기고, 대상 제약 집합도 다르다** (41:731, 40:556)

근거:
- graph 층에는 이미 "gain 제약이 걸린 전달 뷰"를 가르는 자리가 있다. `graph/s1v_fields.py:256`의 `_constrained_keys(model, judged, METRIC_GAIN_SS)`가 judged 제약의 (excite, sense)를 모아 `gain_views`를 만든다(`:283` → `l_classes` `main_path_signal`). `METRIC_GAIN_SS` 주석(`s1v_values.py:48`)도 "gain 제약 전달 뷰"다.
- design은 같은 판정(gain 제약들의 (여기, 감지))을 spec 로드 `constraint_declaration`에서 한 번 더 한다. 둘째 생산자다(graph 규칙 1). 그 결과는 graph 밖(spec 문서 칸)에 계산값으로 남는다.
- 두 자리의 입력 집합이 다르다. S1v는 judged 제약을 보고, design은 "제약·결정 대기 제약 가운데 뷰 칸이 있는 항목"을 본다. 그래서 같은 회로에서 '하나'인지 '둘 이상'인지의 판정이 갈릴 수 있다.
- 같은 뷰를 card DE-1 (c)의 A_dc도 써야 한다(계획 "DEC-23 '여기 방향'·A_dc가 쓰는 뷰와 같은 하나"). 지금 자리에 두면 셋째 소비 경로가 graph 밖 입력이 된다.

수정안(원칙 순):
- **(가) 권고.** S1v 블록 `s1v_fields`가 이미 가진 `gain_keys`와 뷰 씨앗(기본 포트 뷰 포함)으로 ICMR 전달 뷰(또는 정의 불능 사유)를 graph 필드 하나로 쓰고, `icm_config`(그리고 뒤의 DE-1 (c))가 READS로 읽는다. 장점은 셋이다: writer 하나, θ 무관 S1v라 재계산 0(graph reuse), 판정 입력 집합(judged) 하나. `SizingSpecDoc.icmr_view`·`DcInputs.icm_view`·extras는 두지 않는다.
- (나) spec 로드 칸을 유지하려면 S1v의 `_constrained_keys(…, METRIC_GAIN_SS)`가 그 칸을 읽게 바꿔 판정 자리를 하나로 만든다. 그리고 입력 집합(judged인가, 결정 대기 포함인가)을 계획에서 정한다.
- 어느 쪽이든 '같은 판정 둘'은 graph 규칙 6("정본 자리가 없으면 멈추고 보고")에 해당한다. 오케스트레이터가 정하고, 필요하면 계획에 한 줄 더한다.

원칙: graph 규칙 1·3·4, 만들면 배선.

**S-2. F 성분 미선언 포트를 구동에 넣는 것은 계획과 design 697에 어긋난다** (41:734 (4)(ii)·(6), 700)

근거:
- 계획 N6.6 범위 1(v6.35 판 1521행)은 F 성분 미선언 포트에 대해 이렇게 적는다: "그 포트 하나만 자기 x로 훑는 창은 … 두지 않는다; 측정 구성이 묶지 않은 모든 입력 포트를 같은 x로 함께 움직이는 일반형은 그 포트 노드의 writer를 바꾸는 회로 해석이라 공동분석 대상이고 채택하지 않는다."
- design 41:697도 "그 포트는 측정 구성의 구동 입력이 아니다(KCL 계의 고정 넷으로 봉인점 값에 남는다)"로 남아 있다.
- 그런데 4.7-3b (4)(ii)는 "P3 묶음 = 모든 입력 포트"로 그 포트까지 x로 움직인다. 같은 문서 안에서 모순이고, 계획이 채택하지 않은 회로 해석을 들여온다.
- 계획 IT-2c 착수 조건 (vii)의 "P3 묶음 = 모든 입력 포트"는 `tied_ports` 소멸을 뜻한 문언이다. F 성분 규칙을 바꾼 문언이 아니다.

수정안:
- 구동 = 입력 포트 − F 성분 미선언 포트로 둔다. 그 포트는 봉인점 값에 고정하고, 항목은 `f_component_undeclared`, V_cm 칸과 세 metric은 정의 불능(지금과 같음)으로 둔다.
- 결과 metric은 어차피 정의 불능이라 동작 차이는 진단 값뿐이다.
- 바꾸고 싶다면 계획부터 고친다(공동분석).

원칙: 계획 먼저, 회로 해석은 공동분석.

**S-3. P (b)의 단언이 계획 (7)(b) 문언과 다르다** (41:809)

근거:
- 계획 (7)(b)는 "두 선언 포트가 같은 x만큼 함께 움직인 창(선언 차 유지)"이다.
- servo에서는 포트 감도 s_p = 1 − e_p·(c·vx)/a_e가 포트마다 달라, 두 포트 창 끝의 차가 선언 차와 다르다. 계획 문언은 servo 아래에서 사실이 아니다.
- design이 단언을 "x 구동 몫의 차 = 선언 차 + servo 손계산 끝"으로 바꾼 것은 물리적으로 맞다. 하지만 계획을 그대로 두고 design만 바꿨다.

수정안: 계획 (7)(b)에 사실 정정 한 줄(범위 불변)을 더한 뒤 design 문언을 그대로 둔다(계획 먼저).

원칙: 계획 먼저.

### N

- **N-1.** 41:734 ⑤ "여기 넷이 입력 밖 → `view_required`"는 계획 정의 불능 목록에 없는 갈래다.
  - 계획의 "뷰가 없거나"로 읽는다면 그 해석을 한 줄 적는다.
  - 다만 design은 ④에서 "원인과 고칠 자리가 다르면 새 code"(`icm_view_ambiguous`)라는 기준을 세웠다. ⑤도 원인(뷰는 있으나 여기가 입력 밖)이 `view_required`와 다르다. 같은 기준을 적용할지 정할 것.
  - 발동은 착수 실측 (d)로 잰다.
- **N-2.** 41:817 "`DcInputs.icm_view` 칸이 커널 컨텍스트 지문에 들면"은 사실로 확정된다. `search/search_context.py:206` `context_fp = fp_of((…, dc.lut, dc.inputs))`라 `DcInputs` 전체가 지문에 든다. 그래서 그 칸을 더하면 모든 회로의 `context_fp`(S3 실행 폴더·평가 키)가 한 번 바뀐다. 조건문을 사실 문장으로 고친다. S-1 (가)를 택하면 이 변화는 없다.
- **N-3.** (2) gain 제약이 없는 회로의 기본 뷰 갈래는 S-1 (가)에서 S1v 뷰 씨앗(`collect_views`의 `VIEW_SOURCE_DEFAULT`)으로 같은 결과가 나온다. 정본을 정할 때 함께 옮긴다.

## 미확인

- `ViewDecl`·`DcInputs.icm_view` 값의 `require_immutable`·`fp_of` 통과 여부(코드 실행 안 함, dataclass로 추정).
- 계획 history H1 'v6.35' 행 본문.
