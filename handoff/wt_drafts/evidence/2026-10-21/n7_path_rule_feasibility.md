# N7 경로 기준 'DC 되먹임 없음' 판정 -- 실현 가능성 실측 (O-81 (2) 착수 전)

작성 2026-10-21. 읽기 전용(상태 변경 0, `git -C`만). 대상: 저장소 master `93a9ff82`, design 41 v1.12.5 후보 `wt/design-it2c-o79` `88bc5f2f`, oracle design v0.3.8 `wt/design-oracle-eo1` `ced5a45c`(HEAD `e2fc006b` = 같은 판 둘째 커밋, 1619행 포인터만 더함).
계측 스크립트(저장소 밖, 스크래치): `.../scratchpad/n7_corpus.py`·`n7_directed.py`. 출력은 아래 5절에 그대로 옮겼다.
경로 약칭: `E` = `skills/analog-gmid-design/gmid_engine`, `41` = `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`(design-it2c-o79), `OD` = `docs/02-design/features/oracle-portability.design.md`(design-oracle-eo1), `GB` = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(master).

## 판정: **조건부 실현 가능**

막는 조건(graph 규칙 6의 멈춤)은 없다. 필요한 입력은 모두 이미 있는 graph 필드에서 입력 버전과 함께 읽을 수 있다. 새 필드, 새 cache, 사본은 필요 없다. 판정은 블록 안 지역 술어다. 지금의 kind 판정도 같은 자리에 있다. 순환도 없다. 반전 입력은 선언의 절단 넷으로 구조만 보고 정하며, 이것이 구성 갈래를 고르기 전에 끝난다. 13회로 가운데 영향받는 회로는 0개다. 조건은 넷이다(C1~C4, 8절).

---

## 1. 순서: 반전 입력 식별이 구성 갈래보다 먼저인가, 순환은 없는가

**엔진.** design 41:734 (1)은 '**선언이 있으면 선언이 정한다.** 없으면 `graph.ss_nodal`의 인수분해로 … T_p'라고 적는다. 계획 GB:584도 같다('spec 되먹임 구성 선언이 있으면 그 선언이 정하고, 없으면 동작점 DC 전달 … 부호'). 그런데 no_dc 갈래(41:734 '단일 출력 + DC 성분 없는 선언')는 정의상 **선언이 있는** 경우에만 탄다. 그러니 이 갈래의 반전 입력은 T_p/`_transfer_resolution`(41:735)으로 정하지 않고 **선언이 정한다**.
- 선언이 정하는 넷은 spec 검사가 이미 구조로 보장한다. 선언 소자마다 입력 포트 넷 단자가 **정확히 하나**다(`E/authoring/spec_elements.py:15-17` docstring, `_cut_hits` `:100-115`, 0개 = `feedback_element_not_on_input`, 2개 = `feedback_cut_ambiguous`). 단자 계산 helper는 `E/authoring/_feedback_cuts.py:11-16` `input_terminal_nets`(authoring 층)와 `E/metrics/noise_plan.py:30-31` `_input_side`(ss 회로 층)다. 둘 다 이미 있다.
- 그러므로 경로 판정의 끝점(절단 넷)은 동작점, 전달, 구성과 상관없이 정해진다. 경로 판정은 그 뒤, 구성 선택 직전에 돈다. 순환은 없다.
- 식별 자체는 구성에 의존하지 않는다. 선언 갈래는 netlist + 선언만 보고, 미선언 갈래의 T_p는 봉인점 G(`ss_nodal`)를 본다. 둘 다 `config`를 읽지 않는다.
- 주의(design 몫): 41:734는 '선언이 정한다'의 **계산 방법**(= 절단 넷)을 적지 않았다. design v1.12.6에 '선언 반전 입력 = 선언 소자의 입력 포트 단자 넷(절단 넷), 기존 helper 호출'을 적어야 한다. 셋째 구현을 새로 쓰면 안 된다.

**오라클.** OD:1051 `/measure_feedback`의 `inverting_input`은 'spec이 반전 입력 포트를 선언했을 때만, 없으면 오라클이 `.tf` 부호로 정한다'이다. OD:1834 (e)는 '거부는 **어떤 시뮬레이터 호출보다 먼저**'다. 그래서 경로 판정 끝점을 `.tf`로 정하면 (e)의 이 약속이 깨진다. 시뮬레이터 호출이 먼저 생긴다. 오라클도 끝점을 **`/feedback_passives` 원소의 `/passives` 단자 ∩ 입력 포트 넷**(옛 C14 규칙, OD:841 '위반은 막힘')으로 정하면 된다. 이것은 구조만 보고 정해지고 시뮬레이터 호출 전에 끝난다. `.tf` 식별은 이 판정 뒤 (a)(c) 갈래 안에서만 쓰인다. 순환은 없다. **조건 C1**: 계획 문장이 끝점을 '선언 절단 넷'으로 못박아야 한다.

## 2. 연결 정보의 출처 (graph 입력, 입력 버전)

| 필요한 것 | 기존 graph 필드 | writer | 근거 |
|---|---|---|---|
| 소자 kind | `device.kind` | `s1_structure` | `E/graph/s1_structure.py:64,74` |
| 소자 단자 넷(용량 포함) | `device.pins` (MOS `(d,g,s)`, 2단자 `(t0,t1)`) | `s1_structure` | `:65,75`, `E/graph/CONTRACT.md:149` |
| DC 전도 넷 쌍(용량 = None) | `device.dc_nets` (C1) | `s1_structure` | `:81-83`, 정의 `E/authoring/dc_edges.py:11-19`(DEC-70 유일 정의), CONTRACT.md:150 |
| 원소 종류(MOS/수동/이상원) | `device.element_class` | `s1_structure` | `:62,72` |
| 입력/출력 포트, 레일, 교류 접지 | `node.port_direction`·`node.is_rail`·`node.ac_ground_class` | `s1_structure` | `:56-59` |
| 선언 소자 이름 | `graph.noise_input_cells`(`NoiseDecl.feedback`, 이름만) | `noise_decl`(extras = feedback·caps → 입력 버전) | `E/search/noise_decl.py:33-43`, `E/search/s0_fields.py:23,30` |

- 수동소자의 kind와 단자 넷을 함께 가진 필드가 이미 있다. **`device.pins` + `device.kind`(+ `device.dc_nets`), writer `s1_structure`**다. S1 필드라서 `ctx.base`의 base writer이고 모든 child 스냅샷에 남는다(스냅샷 파생 규칙 5). 지금도 `metrics_aux` READS에 `device.kind`·`device.pins`·`device.element_class`·`node.port_direction`이 있다(`E/metrics/metrics_aux.py:42-46`). 봉인 뒤 블록이 이 필드들을 READS로 읽는 선례다.
- `conductance_matrix`(`E/metrics/_helpers_nodal.py:26-33`)는 용량을 넣지 않고 MOS gm 도장도 넣는다. 그래서 구조 경로 판정의 입력으로 쓰기에 맞지 않다(gate 결합이 섞이고 동작점에 따라 값이 0이 될 수 있다). 쓰지 않는다.
- 선언 소자 **이름**의 출처는 N7과 무관하게 이미 열려 있는 사항이다. kind 판정에도 필요하다. 41:731은 'extras = `human.feedback.elements` 로드 결과 … 커널 컨텍스트에 그 값이 있는 자리는 착수 때 확인, 없으면 멈추고 보고'라고 적었다. 후보는 `graph.noise_input_cells`(writer `noise_decl`, `SEARCH_S0_WRITERS` 원소 `E/search/s0_fields.py:34-40`)를 READS로 읽는 것이다. 다만 IT-2c가 부르는 모든 ss 평가 스냅샷에 그 writer가 남는지는 착수 실측 몫이다(검증 U1/N2와 같은 항목). **N7이 더하는 입력(`device.*`·`node.*`)은 S1 필드뿐이라 새 가용성 위험은 없다.**
- 결론: 멈춤 조건(규칙 6)에 해당하지 않는다. 새 graph 필드는 필요 없다. 판정은 `icm_config` 블록 안 지역 술어이고, 지금의 kind 판정(41:734)과 같은 자리다.

## 3. 경로 정의: 선언 소자만인가, DUT DC 망 전체인가

**물리 유도.** 'DC 되먹임이 있다'는 '용량을 연 DC 선형화 계에서 V(반전 입력)이 V(출력)에 의존한다'는 뜻이다. 구조로 보면 일반 위치에서 0이 아닌 전달 경로가 있다는 뜻이다. 따라서
1. **DUT 안 저항도 센다.** 스펙 규칙 L2 때문에 선언 소자는 하나하나가 입력 넷 단자를 정확히 하나 가진다. 그래서 '선언 소자만' 규칙은 '출력과 절단 넷을 **직접** 잇는 선언 저항이 있다'로 퇴화한다(경로 out–X–in−의 out–X 소자는 입력 단자가 없어 선언할 수 없다). T망 저항 되먹임(R1 출력–X, R2 X–in−, R3 X–접지)은 흔한 실제 꼴이다. 여기서 선언할 수 있는 소자는 R2 하나뿐이고, 선언-만 규칙은 '없음'(거짓 정의 불능)을 낸다. 이 정의는 S-3 망 정의와도 같다. 계획 S-3과 41:738은 '선언 되먹임 DC 망 = 선언 소자를 끊지 않은 봉인점 회로 = `ss.circuit` 그대로'라고 적는다. 즉 O-81 문언의 '선언 DC 망'은 S-3 정의상 DUT 봉인점 망 전체다.
2. **고정 전위 넷은 경유 마디가 될 수 없다**(끝점은 예외). 이상 전압 마디는 신호를 전하지 않는다. 고정 집합은 레일, 교류 접지, 다른 입력 포트 넷이다(`ss_nodal` `fixed` = 교류 접지 ∪ 입력 넷 ∪ 구동 쌍 넷과 같은 뜻, 41:741).
3. **엣지 종류.** 저항(양방향), MOS 채널 d↔s(gds, 소스 쪽 gm), 이상 **전류원은 엣지가 아니다**(증분 컨덕턴스 0, 전압을 전하지 않음). 이 점은 `dc_edges_unpruned`와 다르다. 그 함수는 KCL 전류 경로용이라 이상원을 모두 엣지로 넣는다(`dc_edges.py:18`). 그래서 술어는 `device.dc_nets`를 `element_class != ideal_source`로 걸러 읽는다. 커패시터는 열림이다.
4. **(가장 일반적인 형태) MOS 제어 결합 g→d, g→s(방향 있음)**. 출력이 어떤 MOS의 gate를 구동하고 그 drain이 저항으로 in−에 닿으면, 이것도 실제 DC 되먹임(능동 경로)이다. 이 엣지를 빼면 이런 회로에 '없음'(fail-closed 정의 불능)이 나온다. 결과는 안전하지만 물리적으로는 틀린 거절이다. 이 엣지를 넣으면 판정은 'DC 선형화 계 G의 구조적 의존 그래프에서 출력 → 절단 넷 도달'과 같아진다. 그러면 S-3 닫음 연립((3), 41:734)이 실제로 0이 아닌 루프를 푼다는 것과도 맞는다. 남는 위험: 구조적으로 '있음'이어도 수치 루프 이득이 아주 작은 회로는 (3) 닫음이 나쁜 조건의 연립이 된다. 13회로에는 해당하지 않는다. 생기면 계획부터 고친다.

**권고 = (가) 방향 의존 그래프**(저항·MOS d↔s·MOS g→d/g→s, 용량·이상 전류원 제외, 고정 넷 경유 금지, 끝점 = 선언 절단 넷). 대안 (나)는 무방향 전도 그래프(저항·MOS d–s만)다. 능동 경로를 놓치지만 fail-closed라 안전하다. 둘 다 아래 toy와 13회로에서 같은 결과를 낸다. 물리 정합 최우선, 가장 일반적인 형태 원칙에 따라 (가)를 권고한다.

**toy 실측**(스크립트 `n7_corpus.py`. 차동 입력 inp/inn, M2 drain = out, 꼬리 M5, 레일 gnd·vdd. 결과는 (a) kind 판정 / 선언-만 경로 / DUT 전체 경로):

| toy | 기대 | kind 판정 | 선언-만 | DUT 전체(권고) |
|---|---|---|---|---|
| R 출력–in− | 있음 | 있음 | 있음 | **있음** |
| Cf(출력–in−) + Rb(in−–gnd) | 없음 | 있음 (**틀림**) | 없음 | **없음** |
| Rf ∥ Cf (출력–in−) | 있음 | 있음 | 있음 | **있음** |
| R 분압 출력–in−–gnd | 있음 | 있음 | 있음 | **있음** |
| R in−–gnd만 | 없음 | 있음 (**틀림**) | 없음 | **없음** |
| Cf + Rb(in−–X), X–출력 미선언 R (T망 꼴) | 있음 | 있음 | 없음 (**틀림**) | **있음** |

## 4. 기존 helper (재사용 의무)

- 레지스트리 `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`에는 'DC 도달/경로' 행이 없다. union-find 행(:50)은 '묶는 개념이 다르면 같은 개념으로 세지 않는다'고 적는다. 경로 탐색은 union-find가 아니라 끝점 사이 BFS다.
- 엔진의 기존 도달 코드는 셋 다 이 술어로 쓸 수 없다.
  - `E/authoring/cm_partition.py:42` `_reach`: 비공개이고 수동소자 2단자를 **커패시터 포함**으로 퍼뜨린다(docstring :5-6). DC가 아니다.
  - `E/authoring/hidden_rails.py:20-30`: 함수 안에 인라인 BFS가 있고, 시작점은 레일 집합이다. `dc_edges_unpruned`를 쓰므로 이상원도 엣지에 든다.
  - `E/graph/signal_reach.py`: AC 신호 전파이고 뷰 단위다. `E/graph/loops.py:76`·`feedforward_cells.py:47` `_components`는 강연결 성분이다.
- **재사용할 정본은 엣지 정의다.** `device.dc_nets`(정의 = `dc_edges.py`의 유일 정의, `DC_CONDUCTING_PASSIVE_KINDS` import만)와 `device.pins`를 쓴다. 탐색은 `E/metrics/icm_config.py` 안 비공개 함수 하나로 둔다(예: `_dc_feedback_path(...)`, 이름은 design). 레지스트리에 개념 행 하나('DC 되먹임 경로 술어, 정본 = icm_config 블록 안 함수 하나')를 더한다. 새 공용 유틸은 만들지 않는다. 뒤 S-OS2 card(차동 일반형)가 같은 술어를 쓸 때는 이 함수를 부른다(41 검증 '둘째 생산자' 주의 1).

## 5. 13회로 재계측 + IT-2c toy 영향

`n7_corpus.py`·`n7_directed.py` 출력(그대로 옮김):
```
library/common_gate_amplifier: feedback=[] -> not in branch
library/current_reuse_telescopic_ota: elements=['Cf1','Cf2'] kinds=[capacitor,capacitor] outputs=['Vom','Vop'] cut=['Vim','Vip']
   incident_passives={'Vim':['Cf2','Cs2'],'Vip':['Cf1','Cs1']} kind_rule_dc=False
   declared_only/full_dut/directed: 4 쌍 모두 False
library/folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, pushpull_follower_buffer, sf_pushpull_output_opamp,
  two_stage_ota, two_stage_ota_sf: feedback=[] -> not in branch
heldout/cnr_ota, erfc_ota, r2r_opamp, rfc_ota: feedback=[] -> not in branch
```
- 13회로 가운데 12개는 `[]`(β=1, 이 갈래 아님, `spec_elements.py:19-20`)다. 비지 않은 선언은 `current_reuse_telescopic_ota` Cf1·Cf2 하나이고 **차동 출력**이라 단일 출력 갈래 밖이다. 차동 갈래(O-67 (1))에서도 kind 판정과 경로 판정 모두 '없음'(DC 닫힘)이라 결과가 같다. **영향 0개**(단일 출력 갈래 0개, 차동 갈래 판정 변화 0).
- IT-2c toy:
  - L8 (b1)(용량만 선언 단일 출력, 41:811): 경로 판정도 '없음'이다. 기대 그대로 `config None` + `icm_config_feedback_no_dc`.
  - L8 (b2)(저항 선언 → `declared_feedback`): **조건부**다. toy의 저항이 출력과 절단 넷을 잇는 꼴(Rf 출력–in−)이어야 한다. 'R in−–기준'만 있는 꼴이면 경로 판정은 '없음'으로 바뀐다. 41:811 (b2)와 card T-L8에 toy 연결을 적어야 한다.
  - L10 (e)(41:812 '용량 되먹임 toy·저항 되먹임 toy 창 = 손계산'): MF-1에 따라 용량만 toy는 (b1)과 어긋난다. 저항 toy와 **R∥C 혼합 toy**로 바꾼다(경로 '있음', DC 망 = 저항만 G에 들어감).
  - 새 red 변형(kind 판정을 잡는 것): Cf+Rb(in−–레일) → 정의 불능(kind 판정이면 `declared_feedback` → red). T망(R1 출력–X, R2 X–in− 선언, R3 X–gnd) → `declared_feedback`(선언-만 판정이면 정의 불능 → red).

## 6. 오라클 쪽

- 분류 자리: OD §21.2 2단계(OD:1829-1834). (a) '`declared`이고 `feedback_passives`에 `Resistor`·`Inductor`가 하나라도 있음'(OD:1830), (c) 차동 + DC 성분 없음(OD:1832), (e) 단일 출력 + DC 성분 없음(OD:1834). 분류는 하나이고, ICMR (c)(e)와 슬루 (c)가 같은 분류를 읽는다(OD:1772 점검표). 1b 시작 동작점(OD:1907)도 같은 'DC 성분 있음'을 읽는다. 1619행은 'O-81 (2) 경로 기준 일반화 -- 계획 v6.27 대기' 포인터다.
- 적용할 수 있다. 입력 `/passives`의 원소는 `{name, kind: resistor|capacitor, terminals}`(OD:840)이고, `/feedback_passives`는 이름 배열이다(OD:841). MOS 단자는 `/devices`, 레일은 `/rails`(OD:837), 포트는 `/ports`(OD:845)에 있다. 그래서 같은 방향 의존 그래프를 netlist 입력만으로 만들 수 있고, 시뮬레이터 호출 전에 판정한다((e)의 '어떤 시뮬레이터 호출보다 먼저'를 지킴).
- 표기 정리: 오라클 `Inductor` 갈래는 입력 스키마상 도달하지 않는다(OD:1619, `/passives` kind = resistor|capacitor). 엔진의 지원 수동 kind도 {capacitor, resistor}뿐이다(그 밖은 `passive_kind_unsupported` 정지, `E/graph/CONTRACT.md:154`). 따라서 계획 문장은 kind 이름을 쓰지 말고 'DC 전도 원소(용량은 열림)'로 적는다. 두 쪽 모두 지원 kind 위에서 같은 뜻이 된다.

## 7. graph 단일 정본

- **정의 자리 하나 = gain-budget 계획 N3.8 'ICMR 측정 구성' 안의 판정 문단 하나**(아래 9절 문장). O-79 문장(단일 출력), O-67 (1) 문장(차동, 'DC 성분(컨덕턴스)만'·'DC 성분이 없거나'), 오라클 N3.9 ICMR/슬루 행은 모두 이 문단을 **인용**한다. 지금은 'DC 성분' 표현이 N3.8 안 두 문장(O-79·O-67)에 따로 있다. 정의는 이 문단 하나로 모은다(규칙 3: 한 양 정의 하나).
- **계산 자리:** 엔진은 `E/metrics/icm_config.py` 안 함수 하나(no_dc 갈래, 나중에 S-OS2 card가 부름), 오라클은 §21.2 2단계 분류 하나(OD:1772가 이미 하나로 점검). 엔진과 오라클은 별도 시스템이다(NFR-P3, import 금지). 같은 계획 정의를 따로 구현하는 것은 기존 짝과 같은 꼴이라 허용된다(반전 입력 식별 = 엔진 `nodal_solve` T_p 대 오라클 `.tf`, 판정 분해능 = 엔진 δV_out 대 오라클 시뮬레이터 허용치, GB:584 '엔진은 … 오라클은 `.tf`로 독립하게 잰다'). 판정이 갈리면 '정의 경계 불일치'(O-63 (2))로 변화표에 기록한다.
- 새 graph 필드, cache, sctx 슬롯, `IcmConfig` 값 칸은 없다. 판정 결과는 `config` None + `undefined` code로만 남는다(기존 칸).

## 8. 조건

- **C1 끝점 = 선언 절단 넷**(선언 소자의 입력 포트 단자 넷. 엔진은 기존 helper `input_terminal_nets`/`noise_plan._input_side` 중 하나를 호출하고 셋째 구현은 만들지 않는다. 오라클은 `/feedback_passives` 단자 ∩ 입력 포트). `.tf`/T_p를 쓰지 않는다. 판정은 구성 선택과 어떤 시뮬레이터 호출보다 먼저 한다.
- **C2 입력** = S1 필드 `device.{pins, kind, element_class, dc_nets}`·`node.{port_direction, is_rail, ac_ground_class}`(writer `s1_structure`)를 `icm_config` READS에 더한다. 선언 이름 출처(41:731 착수 확인, 후보 `graph.noise_input_cells`)는 기존 미확인 항목이다. N7 때문에 생긴 것이 아니고, 확인이 안 되면 멈추고 보고한다.
- **C3 술어 정의 선택**(사용자 승인 몫): (가) 방향 의존 그래프(권고, 가장 일반적) 또는 (나) 무방향 전도 그래프. 이상 전류원 제외는 `dc_edges_unpruned`와 다른 점이므로 문장에 적는다.
- **C4 문서 정렬 범위**: N3.8 O-67 (1) 차동 문장, 오라클 N3.9 ICMR/슬루 행, oracle design §21.2 (a)(c)(e)·1b, OD:1772를 같은 판정으로 읽게 고친다. 동작 변화 0, 해당 0개.

## 9. 제안 문장

### gb N3.8 (O-79 문장 바로 앞에 판정 문단 하나 두고, O-79·O-67 (1) 문장은 인용으로 고침)

> **선언 되먹임의 DC 되먹임 판정 -- 정의 하나**(v6.27, 사용자 결정 O-81 (2) -- 소자 종류가 아니라 경로로 판정, 경위 history H1): 선언 되먹임 구성에 **DC 되먹임이 있다** = DUT의 DC 선형화 망(용량은 열림. 이상 전류원은 증분 컨덕턴스 0이라 결합 아님)의 구조적 의존 그래프 -- 저항(양방향), MOS 채널 drain↔source, MOS 제어 gate→drain·gate→source -- 에서 출력 넷(차동 출력이면 출력마다)으로부터 **선언 절단 넷**(선언 소자의 입력 포트 단자 넷, spec 규칙 L2로 소자마다 하나)까지, 측정계 고정 전위 넷(레일·교류 접지·다른 입력 포트 넷)을 중간 마디로 지나지 않는 경로가 있다는 뜻이다. 그런 경로가 없으면 **DC 되먹임 없음**이다. 판정은 netlist 구조와 선언만 읽는다(동작점·시뮬레이터 호출 없음). 그래서 반전 입력 식별(T_p·`.tf`)과 측정 구성 선택보다 먼저 끝나고, 선언이 있을 때 반전 입력은 이 절단 넷이다. 이 계획과 oracle-portability N3.9의 'DC 성분 없는(용량만)'·'DC 성분(컨덕턴스)만'·'DC 성분이 없거나'·'선언 되먹임에 DC 성분이 있으면'은 모두 이 판정으로 읽는다. 예: Cf(출력–in−) + Rb(in−–기준 레일) = 없음, R(in−–접지)만 = 없음, R(출력–in−)·Rf∥Cf·R 분압(출력–in−–접지)·T망(R1 출력–X, R2 X–in−, R3 X–접지) = 있음. 해당 회로 0개(13회로 -- 비지 않은 선언은 current_reuse Cf1·Cf2 하나, 차동, 판정 변화 0; 실측 `_drafts/evidence/2026-10-21/n7_path_rule_feasibility.md`). 엔진과 오라클은 이 정의를 각자 구현한다(NFR-P3). 판정이 갈리면 '정의 경계 불일치'(O-63 (2)). 정의 자리는 여기 하나다.

O-79 문장 고침: '**단일 출력 + DC 성분 없는(용량만) 선언 되먹임**' → '**단일 출력 + DC 되먹임 없는 선언 되먹임**(위 판정, O-81 (2))'.
O-67 (1) 문장 고침: '선언 되먹임의 **DC 성분(컨덕턴스)만** 쓴다. DC 성분이 없거나(용량만 …)' → '선언 되먹임의 DC 망을 쓴다. 위 판정이 '없음'이거나(예 current_reuse Cf1·Cf2)'.
(대안 (나)를 고르면 판정 문단의 '구조적 의존 그래프' 엣지에서 'MOS 제어 gate→drain·gate→source'를 빼고 '무방향'으로 적는다.)

### gb N6.6 완료 조건 고침 (MF-1 = O-81 (1) 포함)

- **(8)(b)** → '(b) 되먹임 선언 단일 출력 toy: (b1) 용량만 선언 → 정의 불능·사유 기록(창 없음) (b2) 저항 되먹임(R 출력–반전 입력) → 선언 구성(DC에서 용량 열림)으로 잰 창 (b3) **경로 판정 red 변형**(O-81 (2)): Cf(출력–in−)+Rb(in−–레일) → 정의 불능(kind 판정이면 선언 구성 창 → red), R(in−–레일)만 → 정의 불능, T망(R2만 선언) → 선언 구성 창(선언 소자만 보는 판정이면 정의 불능 → red)'.
- **(10)(e)** → '(e) 저항 되먹임 toy와 저항+용량 혼합 toy(Rf∥Cf, 출력–반전 입력)에서 DC 망 = 선언 소자를 끊지 않은 봉인점 회로(용량 제외·저항 포함)로 잰 창과 손계산 일치(용량만 선언 toy는 (8)(b1) 정의 불능 -- O-81 (1))'.
- **(10) 새 (h)** → '(h) DC 되먹임 판정 자리 하나(`git grep`) -- 엔진 함수 하나가 READS(S1 `device.pins`·`device.kind`·`device.element_class`·`device.dc_nets`·`node.port_direction`·`node.is_rail`·`node.ac_ground_class`)만 읽음, 새 graph 필드·cache 0; 끝점 = 기존 절단 넷 helper 호출(셋째 구현 0)'.
- **IT-2c 착수 조건(GB:1514)** 덧붙임: '(iii) 41:734 (1) no_dc 갈래 판정을 kind(`DC_CONDUCTING_PASSIVE_KINDS` 유무)에서 N3.8 DC 되먹임 판정으로 바꾼다. code `icm_config_feedback_no_dc`와 `config` 값 집합은 그대로. L8 (b2) toy 연결을 명시하고 (b3)을 더한다. L10 (e) toy를 저항·R∥C로 바꾼다. card T-L8·T-L10·spec 31행도 같이 고친다.'

### design 41 v1.12.6 / oracle design 따라 고칠 자리 (참고, 계획 승인 뒤)
- 41:731 READS에 위 S1 필드를 더한다. 41:734 (1) kind 문구를 판정으로 바꾸고 '선언이 정한다 = 절단 넷(helper)'을 적는다. 41:738 '(용량만)' 문구, 41:744 (2) code 설명, 41:811 (b2)(b3), 41:812 (e), 레지스트리에 행 하나.
- OD §21.2 (a)(c)(e)·1b·OD:1772·OD:1619를 'N3.8 DC 되먹임 판정 인용'으로 고치고 `Inductor` 표기를 정리한다.
