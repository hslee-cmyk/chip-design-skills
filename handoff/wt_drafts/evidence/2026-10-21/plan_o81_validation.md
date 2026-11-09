# 계획 개정 독립 검증 -- gain-budget v6.27 · oracle-portability v0.6.16 (O-81·O-82)

- 대상: worktree `wt/plan-o81`, 브랜치 `plan/o81`, 커밋 `1d42c36e`(gb v6.27)·`342b7dfd`(oracle v0.6.16), base master `93a9ff82`
- 변경: 4개 파일, +25/−9
- 입력:
  - 사용자 결정 O-81·O-82(`user_decisions.md` 702·703행)
  - `n7_path_rule_feasibility.md`(C1~C4, §3·§9)
  - `design41_v1125_validation.md`(MF-1·N7·N8)
  - design 41 v1.12.5(`wt/design-it2c-o79` `88bc5f2f`)
  - oracle design v0.3.8(`e2fc006b`)
- 방법: 읽기만 했다. git은 `git -C` + `show`/`diff`/`grep`만 썼다. 인용은 모두 직접 다시 쟀다.

## 점수: 86 / 100 -- 아직 승인 요청 전 (필수 3건, 모두 문언 수정)

---

## 1. O-81 (1)·(2)와 O-82 반영 여부, 범위

| 결정 항목 | 반영 자리 | 판정 |
|---|---|---|
| O-81 (1) MF-1: (8)(b)·(10)(e)의 용량만 toy = 정의 불능, 창 손계산은 저항·저항+용량 toy로 | gb N6.6 (8)(b1)·(b2), (10)(e)(저항 toy, Rf∥Cf toy), IT-2c (iii)(design 41:812 L10 (e)·card 같이) | 충족 |
| O-81 (2) N7: 소자 종류가 아니라 경로로 판정, 엔진·오라클 같은 정의, N3.8 한 자리 | gb N3.8 새 문단 '선언 되먹임의 DC 되먹임 판정 -- 정의 하나'(HEAD 586행), oracle N3.9 'DC 되먹임 판정' 인용 문단, DR-24 | 충족(아래 M1~M3 제외) |
| O-82: 방향 의존 그래프, 끝점 = 선언 절단 넷(.tf·T_p 안 씀), S1 필드 READS, 새 필드·cache 0, `icm_config.py` 비공개 함수 하나 + 레지스트리 행, 계획 문장은 'DC 전도 원소', 오라클 따로 구현, 13회로 판정 변화 0 | 같은 문단, (10)(f), N2.1 O-82 행, oracle O-82 행 | 충족. 단 끝점 helper 호출 꼴은 M1 |
| 절차: 실측 → 계획 → 검증 → 승인 → design | 두 Status 모두 '독립 검증·사용자 승인 전' | 충족 |

**범위 넘침: 없다.** 바뀐 곳은 다음뿐이다.
- O-79 문장 표제와 O-67 (1) 문장을 인용 꼴로 바꿈(O-82 '인용'), N6.6 표제, oracle DR-24(C4 범위)

새 결정을 지어 넣은 곳은 없다.

## 2. 규칙의 물리 점검

**엣지 집합: 맞다.**
- 저항 양방향: 맞다.
- MOS d↔s 양방향: gds와 소스 쪽 gm에 의한 결합이다. '가장 일반적인 형태' 원칙에 맞다.
- MOS g→d, g→s 한 방향: 맞다. gate는 전류를 받지 않으므로 d/s에서 g로 가는 의존은 없다.
- 용량 제외: DC에서 열려 있으므로 맞다.
- 이상 전류원 제외: 증분 컨덕턴스가 0이므로 맞다.

**빠진 것: 이상 전압원(→ M2).**
- 계획 문단은 '이상 전류원'만 엣지에서 뺀다고 적는다. 이상 전압원이 엣지인지, 그 단자 넷이 고정 전위인지는 정하지 않았다.
- `device.dc_nets`의 원천인 `dc_edges_unpruned`(`dc_edges.py:18`)는 이상원을 **전부** 엣지로 넣는다.
- 실현 가능성 문서 §3-3은 `element_class != ideal_source`로 이상원 **전부**를 걸렀다. 계획의 (10)(f) READS에는 `device.element_class`가 빠져 있다.
- 반례: T망에서 X–gnd 사이가 R3가 아니라 Vref(이상 전압원)인 경우.
  - 물리적으로 X는 고정되어 있으므로 in−는 out에 의존하지 않는다. 답은 '없음'이다.
  - 계획 문언대로 X를 고정 전위로 보지 않으면 out–R1–X–R2–in−가 이어져 '있음'(거짓)이 된다.
- 해당 회로는 0개다(static_ac_ground 머리: '이상 전압원 단자는 library 발동 0', `unsupported`로만 기록). 그래도 '정의 하나' 문단이므로 갈래를 닫아야 한다.

**고정 전위 넷 경유 금지에 '다른 입력 포트 넷'과 '교류 접지'를 넣은 것: 물리적으로 정당하다. 다만 이름은 고치기를 권한다.**
- **다른 입력 포트 넷**
  - 측정 구성에서 묶이지 않은 입력 포트는 훑기 원천이나 선언 DC 원천이 구동하는 이상 전압 마디다. 그 넷을 지나는 경로는 출력 의존을 전하지 못한다(원천이 흡수한다).
  - 실제 되먹임을 잘못 막는 경우가 있는가: 막히는 것은 'out → … → in+ → … → in−' 꼴뿐이다. 이때 in−가 따르는 값은 in+ 원천이지 출력이 아니므로 막는 것이 맞다.
  - 반전 입력 자신은 끝점이라 예외다.
  - 차동(S-OS2)에서 상대 절단 넷을 경유하지 못하게 하는 것도 같은 이유로 맞다.
  - 근거는 `ss_nodal` `fixed` 집합(41:741, 실현 가능성 §3-2)과 같은 뜻이다.
- **교류 접지**
  - `node.ac_ground_class`는 레일과 `AC_GROUND_GATE_ONLY`(단자가 전부 MOS gate인 넷)뿐이다(`graph/ac_ground_static.py:6-9`).
  - gate만 붙은 넷으로 **들어오는** 엣지는 없다(g→d, g→s는 나가는 방향만 있다). 그래서 이 넷은 처음부터 경유 마디가 될 수 없고, 넣어도 빼도 결과가 같다.
  - 그 넷은 '외부 바이어스 전압이 걸리는 넷'(같은 파일 9행)이라 DC 고정 전위로 봐도 맞다.
  - 그러나 DC 판정 문장에 AC 개념 이름을 쓰는 것은 DC/AC 분리 원칙과 어긋난다 → N3.

**손계산 toy**(출력 out, 반전 입력 in−, 비반전 in+는 원천이 구동, 레일 gnd·vdd):

| toy | 경로 | 판정 | 계획 예시와 |
|---|---|---|---|
| R out–in− | out–R–in− | 있음 | 같음 |
| Cf(out–in−) + Rb(in−–gnd) | Cf 엣지 아님. in−로 들어오는 엣지는 Rb뿐인데 그 반대편이 gnd(고정)라 막힘. out의 채널 엣지는 레일 또는 내부 마디로 가고, in−는 입력쌍 gate라 들어오는 채널 엣지가 없음 | 없음 | 같음 |
| Rf∥Cf | Rf 엣지 | 있음 | 같음 |
| R 분압 out–in−–gnd | R1 엣지가 in−에 바로 닿음 | 있음 | 같음 |
| R in−–gnd만 | 반대편이 gnd라 막힘 | 없음 | 같음 |
| T망(R1 out–X, R2 X–in−만 선언, R3 X–gnd) | out→X→in−, X는 고정 아님 | 있음 | 같음. R1·R3는 미선언이지만 DUT DC 망 전체이므로 센다 |
| 고리 안 source follower(out → Msf gate, Msf source S – R – in−) | out→(g→s)→S→R→in− | 있음 | 물리와 맞음. 방향을 뒤집은 꼴(in−가 gate)은 '없음' |

- 추가 관찰(→ N4, 사용자에게 보고 권고): 입력이 **source 단자**인 DUT(공통 게이트 입력)에서 용량만 선언하면, DUT 자신의 순방향 소자 채널(d↔s, gds)로 out→in이 이어져 '있음'이 된다.
  - 정의 문장('V(반전 입력)이 V(출력)에 의존')으로는 맞다.
  - 그러나 O-79의 '용량만 = 되먹임 없음' 직관과는 다르다.
  - 단일 입력이면 `as_is_single_input`이 먼저라 이 판정까지 오지 않는다. 해당 회로는 0개다(common_gate_amplifier는 `[]`). 그래도 '원래 취지와 다를 수 있는 판단'이므로 보고한다.

## 3. 정의 자리 하나 -- 인용만 하는가, 낡은 kind 문장이 남았는가

- gb N3.8 586행 새 문단이 정의 자리다. 'O-79 문장'(표제 '단일 출력 + DC 되먹임 없는 선언 되먹임', '없음' = 판정 인용)과 O-67 (1) 문장('위 DC 되먹임 판정이 없음이거나')은 인용 꼴로 바뀌었다.
- oracle N3.9 ICMR 행에 'DC 되먹임 판정' 인용 문단(정의는 gb 한 문단, 오라클은 따로 구현)이 들어갔다. 슬루 행 괄호에도 같은 인용이 있다.
- 두 계획에서 `DC 성분|용량만|커패시터만|Resistor|Inductor|DC_CONDUCTING|kind ∈`를 전수 grep했다(76건). 결정 등록부(O-67·O-69·O-78·O-79 행)와 옛 Status는 기록이라 제외했다. 남은 것은 다음과 같다.
  - **gb 587행 N3.8 슬루율 측정 정의 (→ M3).**
    - '과도 되먹임 … N3.8 'ICMR 측정 구성'(선언 되먹임의 DC 성분만)을 …'과 '**용량만 선언된 차동 출력**(예 … Cf1·Cf2)의 `.tran` 시작 동작점은 …'이 그대로다.
    - 이 행이 슬루 시작 동작점 갈래의 **정의 자리**다(oracle 448행은 '정의 = gain-budget v6.27 N3.8'로 인용).
    - 그런데 여기만 kind 문언이 남았다. 586행의 읽는 규칙이 나열한 문자열('DC 성분 없는(용량만)'·'DC 성분(컨덕턴스)만'·'DC 성분이 없거나'·'DC 성분 있음')과 글자가 달라 규칙에 걸리지 않는다.
    - 예: 차동 출력에 Cf + Rb를 선언하면 kind로는 '용량만'이 아니고 경로로는 '없음'이라 두 문언이 갈린다.
  - gb 1603행(N6.6 범위 요약 -- '선언 되먹임의 DC 성분만, 없거나 미선언이면 차동 모드만 닫음'): 요약문이고 낡은 문언이다 → N2.
  - gb 2023행 AP-1 '용량만 선언된 차동 출력 슬루', oracle 448·507·650·720·721행 '용량만 선언된 차동 출력': 1b 경로의 이름표다. oracle 448행은 판정 인용 괄호가 있어 허용한다 → N6.
  - oracle 446행 '측정 구성은 선언 되먹임의 **DC 성분**(컨덕턴스)만 쓴다': 바로 다음 구절에 v0.6.16 인용 괄호가 있고, gb 읽는 규칙에도 걸린다. 허용한다.
- `Resistor`·`Inductor`: 계획에서는 DR-24가 design §21.2 (a) 문언을 **고치라고 인용하는 자리**에만 있다. 맞다.

## 4. N6.6 (8)(b1)~(b3), (10)(e), (10)(f), IT-2c (iii) 대 design 41 L8/L10과 card

- **번호**
  - 계획 (10)은 base에서 (a)~(e)였으므로 새 항목이 **(f)인 것이 맞다**.
  - 그러나 design 41 L10(812행)은 이미 (a)~(h)를 쓴다. 그중 (f)는 `NodalSystem` writeable 단언이다.
  - IT-2c (iii)의 '판정 자리 하나(완료 조건 (10)(f))를 적는다'를 design 작성자가 L10 (f)로 읽으면 기존 항목과 충돌한다 → N1(design L10 새 항목 기호를 지정).
- **(8)(b1)**
  - 기대: config None + `icm_config_feedback_no_dc`, 창 없음.
  - design L8 (b1)(811행)과 card T-L8(interface 34행)이 이미 같은 기대를 낸다. 일치한다.
- **(8)(b2)**
  - 기대: R out–반전 입력 → `declared_feedback` 창(손계산).
  - L8 (b2) '저항 선언(DC 성분 있음)'의 toy 연결을 명시한다. 일치한다.
- **(8)(b3)**
  - 새 red 변형 셋: Cf+Rb, R in−–레일만, T망. design·card에는 아직 없으므로 IT-2c (iii)가 더하도록 지시한다.
  - 기대값은 위 표대로 손으로 낼 수 있다. config 값만 보면 되고, T망은 창 값을 요구하지 않는다.
- **(10)(e)**
  - design L10 (e) '용량 되먹임 toy·저항 되먹임 toy 창 = 손계산'은 MF-1이 지적한 충돌 그대로다. 계획은 저항 toy와 Rf∥Cf toy로 바꾸고, (iii)가 design·card T-L10을 같이 고치게 한다. 일치한다.
  - Rf∥Cf 창은 Rf만 있는 창과 같다(DC에서 C가 열림). 손계산할 수 있다.
- **IT-2c (iii)**
  - 고칠 대상: kind 판정(`DC_CONDUCTING_PASSIVE_KINDS`, 41:734 (1)) → 경로 판정, code와 값 집합은 그대로.
  - card 쪽 kind 문언이 남은 곳은 spec 30행('DC 성분 = `DC_CONDUCTING_PASSIVE_KINDS` import')과 63행이다. (iii)의 'card(interface·spec)도 같이'가 이를 덮는다.

## 5. 저자 미확인 항목 -- `icm_config`가 `input_terminal_nets(name, topology)`를 부를 수 있는가 (→ M1)

- **그대로는 부를 수 없다.**
  - `input_terminal_nets(name, topology)`(`authoring/_feedback_cuts.py:11-16`)는 `topology.ports`·`topology.passives`가 있는 TopologyDoc 객체를 받는다.
  - `icm_config` 입력(design 41 v1.12.5 731행)은 graph READS(`dc_columns` READS, `graph.ss_nodal`, `node.dc_window`, `device.dc_op`, `device.dc_tol_v`, `node.dc_output_structure`, `node.dc_writer`)와 extras(θ 성분, `fixed_values`, `resistor_values`, LUT, 선형 선언 소자, spec 되먹임 선언 이름)다. **topology 객체는 없다.**
  - 호출 자리 `metrics/ss_evaluate.py`에도 `topology` 참조가 없다(grep 0건).
  - topology를 extras로 새로 넘기면, S1 필드가 이미 덮는 정보를 graph 밖 경로로 다시 들이는 셈이다. 입력 버전 범위 밖 입력이 된다(graph 규칙 2·4 취지 위반 우려).
- **`noise_plan._input_side`(`metrics/noise_plan.py:28-31`)**
  - 같은 규칙('두 단자 중 입력 포트 넷이 정확히 하나')의 둘째 구현이다. `ss` 객체(`ss.input_nets`·`ss.nodes`, 소신호 소자 a/b)를 받는다.
  - metrics 층에 있고 41:738이 `icm_config` 안에서 `ss.circuit`을 쓰므로 닿을 가능성은 있다. 다만 비공개(`_`)이고 noise 전용 파일 안 함수다. 부르려면 공용화(레지스트리 갱신)가 필요하다.
  - 또 소신호 R·C만 원소로 찾으므로, 선언 원소가 그 밖의 kind이면 None을 낸다.
- **멈춤 조건인가: 아니다.** graph 규칙 안에서 닿는 길이 있다.
  - `input_terminal_nets`의 핵심을 '(소자 단자 넷, 입력 포트 넷 집합) → 절단 넷' 순수 함수로 나눈다.
  - authoring 쪽은 topology에서, `icm_config`는 READS인 S1 `device.pins`·`node.port_direction`에서 같은 함수를 부른다.
  - `_input_side`도 이 함수로 바꾸면, 오히려 구현이 둘에서 하나로 준다.
  - 이 경우 기존 helper 서명을 바꾸므로 같은 변경에서 호출부 둘(`spec_elements.py:104`, `spec_views.py:101`)과 레지스트리를 고친다.
- **계획이 지금 적은 '기존 helper `input_terminal_nets` 호출'은 위 사실 때문에 그대로는 구현할 수 없다.** 그래서 호출 꼴을 계획에서 정해야 한다(M1). 실현 가능성 C1이 '`input_terminal_nets`/`_input_side` 중 하나'로 열어 둔 것을 계획이 앞쪽 하나로 좁혔는데, 그쪽이 바로 닿지 않는다.

## 6. 인용 재측정

| 인용 | 확인 | 결과 |
|---|---|---|
| `E/authoring/_feedback_cuts.py:11` | 11행 `def input_terminal_nets(name, topology):` | 맞음 |
| `E/authoring/dc_edges.py:14-18` | 14 `def dc_edges_unpruned`, 15 MOS d–s, 16-17 저항, 18 이상원 전부 | 맞음 |
| `E/graph/s1_structure.py:56-59·64-65·74-75·82` | 56 `is_rail`, 57 `port_direction`, 58 `port_role`, 59 `ac_ground_class`, 64-65 MOS `kind`·`pins`, 74-75 2단자 `kind`·`pins`, 82 `dc_nets` | 맞음 |
| 함수 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` | 파일 실재 | 맞음 |
| `E/metrics/icm_config.py` | 아직 없음(미래 파일, design 41 730행 명시) | 맞음(미래) |
| design 41 v1.12.5: L8 811행, L10 812행, 734행 (1) kind 판정 | `88bc5f2f`에서 확인 | 맞음 |
| oracle design `e2fc006b`: (a) 1830, (c) 1832, (e) 1834, 1b 1907, 점검표 1772, 포인터 1619, `/rails` 837, `/devices` 838, `/passives` 840(kind = resistor·capacitor), `/feedback_passives` 841, `/ports` 845 | 각 행 확인 | 전부 맞음 |
| 13회로 '비지 않은 선언 = current_reuse 하나' | 앞 검증(`plan_o78_validation.md`)에서 `ab916aba` 13개 파싱. 이번 base 사이에 spec 변경 없음 | 맞음 |

## 7. graph 단일 정본 점검(별도 항목)

| 규칙 | 점검 | 결과 |
|---|---|---|
| 1 writer 하나 | 판정 결과는 새 필드 없이 기존 `graph.icm_config`(writer `icm_config`)의 `config` None + `undefined` code로만 남는다. 술어 정의는 한 자리(S-OS2 card는 호출) | 통과 |
| 2 새 cache·슬롯·값 칸 | 0(diff 전수) | 통과 |
| 3 같은 정의 = 하나 | 정의 자리는 gb N3.8 한 문단이고 oracle은 인용한다. **단 gb 587 슬루 행이 kind 문언으로 남아 정의가 둘로 읽힌다**(M3) | 부분(M3) |
| 4 참조 전달 | 끝점은 helper 호출(셋째 구현 금지)이라는 취지는 맞다. 호출 꼴은 M1 | 부분(M1) |
| READS 넓힘 | `icm_config` READS에 S1 `device.kind`·`device.pins`·`device.dc_nets`·`node.is_rail`·`node.port_direction`·`node.ac_ground_class`를 더한다. 모두 writer `s1_structure` 하나의 θ 무관 필드이고, 입력 버전을 거쳐 읽으므로 규칙에 맞다 | 통과 |
| READS의 필요성 | `node.ac_ground_class`는 결과에 영향이 없다(2절). 이상원 처리 갈래(M2)를 정할 때 `device.element_class`가 필요할 수 있다(실현 가능성 C2는 포함했고 계획은 뺐다) | M2와 같이 정리 |
| 효율(정보) | 술어는 θ 무관인데 봉인 뒤 블록 안에서 평가마다 다시 계산된다. 넷 수 N에 대한 BFS O(N)이라 평가 1회(수십 ms)에 비해 무시할 만하다. 새 cache를 만들지 않는 것이 규칙에 맞는다 | 통과(N5: 비용 상한 한 줄 권고) |

## 8. 계획 / history 분리

- gb history H1 'v6.27'에 경위, 바꾼 옛 문장 원문, 추가 목록, 번호 설명이 모두 있다. oracle history v0.6.16에 경위, 바꾼 옛 문장, 추가, 옛 Status가 있다. 좋다.
- 계획 문단은 규칙, 예시 toy, 계산 자리, 정의 자리 선언으로 되어 있다. 'dc_edges_unpruned와 다른 점'은 오해를 막는 정의 경계이므로 계획에 둘 만하다.
- 작은 점: gb 586행 O-79 문단과 1516행 N6.6 표제에 '옛 표제 '…'' 원문이 계획 안에 남아 있다. 표제 대체 표시라 허용하지만, history에 같은 원문이 이미 있으므로 지워도 된다(nice, N7).

---

## 필수 수정 (must-fix)

- **M1 끝점 helper 호출 꼴.** 'icm_config가 기존 helper `input_terminal_nets` 호출'은 그대로는 구현할 수 없다. topology 객체가 `icm_config` 입력(41:731)과 `ss_evaluate.py`에 없다. 계획 문장을 다음처럼 바꾸고 레지스트리 행을 같은 변경에 넣는다.
  - '절단 넷 규칙의 순수 함수 하나(소자 단자 넷 × 입력 포트 넷 → 절단 넷)를 authoring helper에서 나누어, authoring(`spec_elements`·`spec_views`)은 topology에서, `icm_config`는 S1 READS(`device.pins`·`node.port_direction`)에서 부른다.'
  - 가능하면 `noise_plan._input_side`도 같은 함수로 바꾼다(구현 둘 → 하나).
  - 멈춤 조건은 아니다.
- **M2 이상 전압원 갈래.**
  - 지금 '정의 하나' 문단은 이상 전압원을 다루지 않는다. 반면 `device.dc_nets`는 이상원을 전부 엣지로 넣는다.
  - 한 구절로 정한다. 예: '이상원은 엣지가 아니고, 이상 전압원 단자 넷은 고정 전위(경유 금지)' 또는 '이상 전압원이 있으면 정의 불능(지원 밖, fail-closed)'.
  - 그에 따라 (10)(f) READS에 `device.element_class` 필요 여부도 맞춘다.
  - 해당 회로는 0개다.
- **M3 gb N3.8 슬루율 측정 정의(587행) 정렬.**
  - '(선언 되먹임의 DC 성분만)'과 '**용량만 선언된 차동 출력**'을 '위 DC 되먹임 판정이 없음인 차동 출력' 인용으로 바꾼다. 또는 586행 읽는 규칙에 '용량만 선언된'을 더한다.
  - 슬루 시작 동작점의 정의 자리가 여기이고 oracle 448행이 이곳을 인용하므로, 정의가 둘로 읽히지 않게 해야 한다(graph 규칙 3).

## 권장 수정 (nice-to-fix)

- N1: IT-2c (iii)의 '완료 조건 (10)(f)'가 design 41 L10에서는 새 기호(예: (i))로 들어간다고 적는다. design L10 (f) = writeable 단언과 충돌을 피하기 위해서다.
- N2: gb 1603행 N6.6 범위 요약의 '선언 되먹임의 DC 성분만, 없거나 미선언이면'을 판정 인용으로 바꾼다.
- N3: 경유 금지 집합의 '교류 접지'를 DC 이름으로 바꾼다. 예: '레일·외부 바이어스 고정 넷(gate만 붙은 넷)·측정 구성이 구동하는 다른 입력 포트 넷'.
  - gate만 붙은 넷은 들어오는 엣지가 없어 결과에 영향이 없다.
  - 그래서 `node.ac_ground_class` READS를 빼도 된다(DC/AC 분리 원칙).
- N4: source 입력 DUT(공통 게이트 입력, 입력 둘 이상)에서는 '용량만 선언'이 DUT 자신의 채널(gds) 때문에 '있음'으로 판정된다. 정의상 맞지만 O-79의 '용량만 = 없음' 직관과 달라 사용자에게 보고하고 확인을 받는다(0개).
- N5: (10)(f) 또는 문단에 '술어는 평가마다 O(N) BFS, 새 cache 없음'을 한 줄 적는다(효율 원칙의 근거 기록).
- N6: '용량만 선언된 차동 출력'을 1b 경로 이름으로 쓴 곳(gb 2023, oracle 448·507·650·720·721)은 이름표로 둔다. 판정은 인용으로 읽는다는 한 구절을 oracle N3.9 슬루 행에 이미 둔 것으로 충분하다. 손볼 필요 없음, 기록만.
- N7: gb 586·1516행의 '옛 표제 '…'' 원문을 지운다. history에 이미 있다.

## 승인 준비 상태

- **아직 아니다.** M1~M3은 모두 계획 문언 몇 줄이고 결정 변경은 없다. 고친 뒤 재검증하면 승인을 요청할 수 있다.
- N4는 '원래 취지와 다를 수 있는 판단'이므로 승인 요청 때 함께 보고하기를 권한다.

## 미확인

- U1: spec 되먹임 선언 이름이 `icm_config` 커널 컨텍스트에 어디서 들어오는가(41:731 '착수 때 확인'). 이번 개정 전부터 있던 미확인 항목이다.
- U2: `icm_config` 안에서 `ss` 객체 전체(`ss.input_nets`·`ss.nodes`)에 닿는가(`_input_side`를 쓰는 길의 전제). 41:738의 `ss.circuit` 언급만 확인했다.
- U3: `device.kind`로 이상 전류원과 이상 전압원을 가를 수 있는가(kind 이름 목록 `SUPPORTED_SOURCE_KINDS`는 열람하지 않았다).
- U4: 오라클 입력(`/rails`·`/ports`·`/devices`·`/passives`)만으로 엔진과 같은 고정 집합을 만들 수 있는가. gate만 붙은 넷은 결과에 영향이 없어 실질 차이는 없을 것으로 보지만 실측하지는 않았다.

---

## 재검증 (2026-10-21, 커밋 `4e843fbc` gb v6.27 둘째·`aebdef17` oracle v0.6.16 둘째, base `342b7dfd`)

- 대상: `git -C wt/plan-o81 diff 342b7dfd..HEAD`. 4개 파일, +16/−9.
- 읽기만 했다. 상태를 바꾸는 git 명령은 없었다.

### 새 점수: 94 / 100 -- 필수 1건(완료 조건 숫자 한 단어), 고치면 사용자 승인 요청 가능

### (1) M1~M3 해소 여부

**M1 -- 해소. 단 (10)(f)의 호출 수가 어긋난다(R-M1).**
- gb N3.8 정의 문단의 새 문언: '**절단 넷 규칙은 순수 함수 하나**(소자 단자 넷 × 입력 포트 넷 집합 → 절단 넷)로 기존 helper `input_terminal_nets`에서 나누어 둔다'.
  - authoring(`spec_elements.py:104`·`spec_views.py:101`)은 topology에서 부른다.
  - `icm_config`는 S1 READS `device.pins`·`node.port_direction`에서 부른다.
  - `_input_side`(`noise_plan.py:28`, 호출 `:48`)는 같은 변경에서 이 함수로 바꾼다(구현 둘 → 하나, 레지스트리 행 같은 변경).
- topology 객체 없이 S1 필드만으로 닿고, graph 밖 입력이 없다. 실현할 수 있다.
- `_input_side`를 대체해도 동작은 같다.
  - 옛 조건 '`element.a != element.b`이고 입력 넷 단자가 정확히 하나'는 순수 함수의 '입력 포트 넷 단자 수 = 1'과 결과가 같다(a == b이고 그 넷이 입력이면 단자 수가 2라 None).
  - noise_plan은 `ss.nodes[element.a/b]`와 `ss.input_nets`로 인자를 만들 수 있다.
- **R-M1 (10)(f)의 grep 조건이 숫자에서 어긋난다.**
  - 문언: '정의 1곳, **호출 자리 셋**(authoring `spec_elements`·`spec_views`, `icm_config`), `noise_plan` 쪽은 `_input_side` 정의 0·같은 함수 호출'.
  - 실제로 이름을 든 호출 자리는 **넷**이다(spec_elements, spec_views, icm_config, noise_plan).
  - `input_terminal_nets(name, topology)`를 얇은 래퍼로 남기면, 순수 함수 호출 자리는 {래퍼, icm_config, noise_plan} 셋이 되고 authoring 두 곳은 래퍼를 부른다. 래퍼를 남길지에 따라 세는 대상이 달라진다.
  - 검증자가 그대로 grep 단언으로 옮길 수 없으므로 고쳐야 한다. 예: '순수 함수 정의 1곳, 호출 자리 넷(spec_elements·spec_views·icm_config·noise_plan) -- `input_terminal_nets`를 래퍼로 남기면 그 래퍼를 포함해 정의·호출을 함께 적는다'.

**M2 -- 해소.**
- gb 문언: '**이상 전압원**: 지원 밖이다(엔진 지원 이상원 = `current_source` 하나, `E/graph/s1_values.py:29`). DUT에 이상 전압원이 있으면 이 판정은 정의 불능(fail-closed -- 엔진은 그 전에 S1 `s1_dc_conduction`이 `source_kind_unsupported`로 멈춘다, `E/graph/CONTRACT.md:394`); 지원하게 되면 계획부터(S-7)'.
- 확인한 사실:
  - `s1_values.py:29`: `SUPPORTED_SOURCE_KINDS = ("current_source",)`, 주석 '이상 전압원은 교류접지 (3) 미구현 -> 기록만'.
  - `:33`: `(ELEMENT_SOURCE, "source_kind_unsupported")`.
  - `graph/CONTRACT.md:394`: '`source_kind_unsupported` | s1_dc_conduction | 지원 밖 원소 존재'로 멈춘다.
  - 그래서 `icm_config`까지 오는 회로의 이상원은 모두 `current_source`다. **`device.kind`로 충분하고, `device.element_class`를 READS에서 뺀 판단은 맞다.**
- **정보(코퍼스):**
  - heldout `r2r_opamp`에는 `voltage_source` 5개(Vb1 VDD–vb1, Vb3 vb3–VSS, Vb4, Vb5, Vb6 -- 레일에서 바이어스 넷으로)가 있다. 즉 '이상 전압원'은 가상의 경우가 아니다.
  - 다만 r2r은 `feedback.elements = []`라 이 판정에 오지 않고, 엔진은 그 전에 S1에서 멈춘다. 판정 변화 0이라는 주장은 그대로 맞다.
  - r2r의 이상 전압원을 지원할 때(예: SD-1/O-74 공급 구성) 이 정의 불능 갈래도 '계획부터'에 걸린다. 연결은 맞다.
- **oracle `/sources`:**
  - design `e2fc006b` 839행 `/sources` `kind: "current" | "voltage"`를 확인했다. '`current`는 엣지 아님, DUT에 `voltage`가 있으면 이 판정은 정의 불능'은 gb 정의를 그대로 따른 것이다.
  - **맞고 범위 안이다**(M2를 오라클 쪽에서 같은 정의로 읽게 한 것, NFR-P3에 따라 따로 구현).
  - DR-24 입력 목록에도 `/sources`(839행)가 들어갔다.
- **oracle `/bias_voltages` '중간 마디 불가':**
  - 844행 정의는 '구동 소자 없는 **게이트 전용 넷**의 이상 전압'이다. gate 전용 넷으로 들어오는 엣지는 없으므로(gb 문단 'MOS gate만 붙은 외부 바이어스 넷은 들어오는 엣지가 없어 처음부터 중간 마디가 될 수 없다'와 같은 사실) **맞다**.
  - 결과를 바꾸지 않는 설명 문장이고 gb 문장의 오라클 대응이라 범위 안이다.

**M3 -- 해소.**
- gb N3.8 슬루율 측정 정의(587행) 새 문언:
  - '과도 되먹임 … N3.8 'ICMR 측정 구성'(선언 되먹임의 **DC 망**)을 과도 되먹임으로 쓰지 않는다.'
  - '**DC 되먹임 없는 선언 차동 출력**(v6.27 -- '없음' = N3.8 '선언 되먹임의 DC 되먹임 판정', O-81 (2)·O-82; 예 … Cf1·Cf2)의 `.tran` 시작 동작점은 …'.
- 정의 자리 안의 kind 문언이 없어졌다.
- oracle 448행 인용('정의 = gain-budget v6.27 N3.8')과 뜻이 같다. oracle history 둘째 커밋 '확인(M3)'에 문언 변경 없이 기록됐다.

### (2) N1~N3·N5·N7 반영, 낡은 문장·범위 넘침

| 항목 | 반영 | 판정 |
|---|---|---|
| N1 | IT-2c (iii) '완료 조건 (10)(f) -- design 41 L10에서는 새 기호 (i)로 넣는다, L10 (f)는 `NodalSystem` writeable 단언이 쓰고 있음' | 맞음 |
| N2 | gb 1603행 '(선언 되먹임의 DC 망, N3.8 '선언 되먹임의 DC 되먹임 판정'이 없음이거나 미선언이면 차동 모드만 닫음 -- … O-82; …)' | 맞음 |
| N3 | 경유 금지 = 'DC 고정 전위 넷 -- 레일과 측정 구성이 구동하는 다른 입력 포트 넷' + 'MOS gate만 붙은 외부 바이어스 넷은 들어오는 엣지가 없어 처음부터 중간 마디가 될 수 없다'. (10)(f) READS에서 `node.ac_ground_class`가 빠졌고, 인용 줄이 `s1_structure.py:56-57`로 바뀌었다 | 맞음. 결과 불변(gate 전용 넷은 들어오는 엣지 없음) |
| N5 | '비용: 판정은 평가마다 넷 수 N에 대한 BFS 한 번(O(N))이고 S1 base 필드에서 다시 계산한다 -- 새 cache를 두지 않으며 재사용은 graph reuse(같은 입력 버전)가 덮는다' | 맞음 |
| N7 | gb 586 O-79 표제 괄호와 1516 N6.6 표제 괄호의 '옛 표제' 원문을 지웠다. HEAD에서 '옛 표제'는 Status 문장('옛 표제 원문 삭제')에만 남는다 | 맞음 |
| N6 | 이름표로 둠(gb history·oracle history '확인(M3)'에 기록) | 맞음(의도대로) |

- **낡은 문장:**
  - 두 계획을 다시 grep했다. 정의·판정 문단 안의 kind 문언('DC 성분만'·'용량만 선언된 차동 출력'을 판정으로 쓰는 곳)은 gb에서 0건이다.
  - oracle 446행 'DC 성분(컨덕턴스)만 쓴다'는 인용 괄호가 붙어 있고 gb 읽는 규칙에도 걸린다. 허용한다.
  - 1b 이름표는 N6대로 둔다.
- **범위 넘침: 없다.** 모든 변경이 M1~M3·N1~N3·N5·N7·N4 기록에 대응한다.
- **권장 R-N1(새 지적):** IT-2c (iii)는 '판정 자리 하나 … card(interface·spec)도 같이'만 적고, M1의 **순수 함수 분리와 `noise_plan` 변경**은 IT-2c 고칠 목록에 넣지 않았다.
  - 이 변경은 authoring·noise_plan 파일을 건드리므로 IT-2c card의 파일 범위와 test(noise_plan 동작 동일성, authoring 거부 code 동일성)에 들어가야 한다.
  - (iii)에 한 구절을 더하면 card 작성 때 빠뜨리지 않는다.

### (3) 새 인용 재측정

| 인용 | 확인 | 결과 |
|---|---|---|
| `E/authoring/spec_elements.py:104` | `nets = input_terminal_nets(name, topology)` | 맞음 |
| `E/authoring/spec_views.py:101` | 같은 호출 | 맞음 |
| `E/metrics/noise_plan.py:28`, 호출 `:48` | 28 `def _input_side(ss, element):`, 48 `net = _input_side(ss, element)` | 맞음 |
| `E/graph/s1_values.py:29` | `SUPPORTED_SOURCE_KINDS = ("current_source",)` + 주석 '이상 전압원 … 미구현 -> 기록만' | 맞음 |
| `E/graph/CONTRACT.md:394` | `source_kind_unsupported` 행, 블록 `s1_dc_conduction`, 조건 '지원 밖 원소 존재' | 맞음 |
| `E/graph/s1_structure.py:56-57·64-65·74-75·82` | 56 `is_rail`, 57 `port_direction`, 64-65·74-75 `kind`·`pins`, 82 `dc_nets` | 맞음 |
| `graph/ac_ground_static.py:6-9`(gb history) | gate 전용 넷 분류 | 맞음 |
| oracle design `e2fc006b` 839행 `/sources` | `kind: "current" \| "voltage"` | 맞음 |
| oracle design `e2fc006b` 844행 `/bias_voltages` | '구동 소자 없는 게이트 전용 넷의 이상 전압' | 맞음 |

### (4) graph 단일 정본 점검(별도 항목)

| 규칙 | 점검 | 결과 |
|---|---|---|
| 1 writer 하나 | 판정 결과는 기존 `graph.icm_config`의 `config` None + `undefined`에만 남는다. 술어 정의는 한 자리 | 통과 |
| 2 새 cache·슬롯·값 칸 | 0. 비용 문장이 '새 cache 없음, graph reuse'를 적었다 | 통과 |
| 3 같은 정의 = 하나 | gb 슬루 행 정렬로 정의 자리 안의 kind 문언 0. oracle은 인용 | 통과(첫 검증 M3 해소) |
| 4 참조 전달·둘째 구현 | 절단 넷 규칙의 구현이 둘(`input_terminal_nets`, `_input_side`)에서 순수 함수 하나로 준다 | 통과(개선) |
| READS | `device.kind`·`device.pins`·`device.dc_nets`·`node.is_rail`·`node.port_direction`(writer `s1_structure` 하나, θ 무관). `node.ac_ground_class`를 뺐고(결과 불변), `device.element_class`는 불요(S1 정지가 이상원 kind를 `current_source` 하나로 보장) | 통과 |
| 효율 | 평가마다 O(N) BFS, cache 없음 | 통과 |

### (5) N4 기록

- gb history H1 'v6.27 둘째 커밋'에 '**원래 취지와 다를 수 있는 판단 (사용자 보고, N4)**' 항목이 있다.
  - 내용: source 입력 DUT(공통 게이트 입력, 입력 둘 이상)에서 용량만 선언하면 DUT 순방향 채널(d↔s, gds)로 '있음'이 된다. 정의로는 맞지만 O-79 직관과 다르다. 단일 입력이면 `as_is_single_input`이 먼저다. 해당 0개(`common_gate_amplifier`는 `[]`). 계획 변경 없음, 승인 요청 때 함께 보고.
- **사용자 보고 항목으로 기록됐다. 맞다.**

### 남은 수정

- **필수 R-M1:** (10)(f) '호출 자리 셋'을 실제 호출 자리 수와 맞춘다. 래퍼를 남길지 함께 적는다. 한 단어에서 한 구절 정도다.
- **권장 R-N1:** IT-2c (iii) 고칠 목록에 순수 함수 분리, `noise_plan._input_side` 대체, 그 test(동작 동일성)를 넣는다.

### 승인 준비 상태

- R-M1 한 단어를 고치면 **사용자 승인을 요청할 수 있다**. 문언 정밀도 문제라 재검증 없이 같은 승인 차례에서 고쳐도 된다.
- 승인 요청 때 N4(history 기록 항목)를 함께 보고한다.

### 재검증 미확인

- RU1: `icm_config` 커널 컨텍스트에서 spec 되먹임 선언 이름이 어디서 들어오는가(41:731). 이번 개정 전부터 있던 미확인이고 그대로다.
- RU2: 순수 함수를 authoring 층에 둘 때 metrics(`icm_config`·`noise_plan`)가 authoring을 import하는 층 의존이 허용되는가. design 41 734행이 `DC_CONDUCTING_PASSIVE_KINDS`를 authoring에서 import하는 선례가 있어 허용으로 추정하지만, 구조 규칙(tests/structure)으로 실측하지는 않았다.
- 첫 검증 U3(이상원 kind 구별)는 닫혔다(`s1_values.py:29`, `CONTRACT.md:394`). U2(`ss` 객체 접근)는 noise_plan 쪽에서만 필요하고, noise_plan은 이미 `ss`를 받으므로 닫혔다. U4(오라클 고정 넷 집합)는 `/bias_voltages`가 gate 전용이라 결과에 영향이 없으므로 실질적으로 닫혔다.
