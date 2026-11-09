verdict: 모순 5 (계획 문언 충돌 4 + 조건부 충돌 1. O-264를 막을 원칙·결정 충돌은 0이다. 5건 모두 계획 v6.39.6 개정으로 풀린다. 그중 2건은 O-264·A-208이 이미 개정 대상으로 지목했다)

# O-264 결정 간 모순 점검 (원칙 20, 점검자 ≠ 권고 작성자)

- 점검자: 독립 점검 agent. 읽기와 이 보고서 쓰기만 했다. 엔진·topology 실행, git 쓰기, ngspice는 하지 않았다.
- 점검 대상: `wt/_drafts/user_decisions.md:1245` O-264
- 기준 판: master 033877eb (계획 v6.39.5, design v1.16.31)
- 엔진 인용은 원칙 8의 용도 (2)(재작성 범위·소비자 목록)로만 쓴다. 엔진 동작은 근거로 쓰지 않는다.
- 측정 스크립트(읽기 전용, topology json만 읽음). 결과 파일도 같은 폴더에 있다.
  - `C:\Users\HSLEE\AppData\Local\Temp\claude\C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills\63c6146a-ab1d-4035-a169-bae810986922\scratchpad\o264_struct_vs_role.py` → `o264_out.txt`
  - `...\scratchpad\o264_undriven_nets.py` → `o264_undriven.txt`
  - `...\scratchpad\o264_bulk_partner.py` → `o264_bulk.txt`

## 0. O-264 요지(원문 1245행)

1. DEC-106(O-168)의 차동 입력쌍 판정 근거를 ports의 role 문자열에서 연결 구조로 바꾼다. 조건: 입력 방향 포트 두 개가 같은 kind·같은 source 넷을 공유하는 소자쌍의 두 gate에 물린다.
2. 두 포트는 같은 DC(v_cm 변수 하나)로 묶는다. 묶음은 출발 단계 전, 쓰기 계획에서 한다. FS-1 짝은 쓰기 계획의 VGS 병렬 짝이다.
3. 판정 결과는 정본 필드 하나(구조 유도 블록 writer 하나)에 둔다. 쓰기 계획·짝·ICMR·측정 구성이 이 필드를 READS한다. 둘째 판정은 금지한다.

## 1. 결정 쌍별 표

판정 칸: 충돌 = O-264와 문언·정의가 어긋나 개정이 필요함 / 조건부 = 해석을 하나로 정해야 함 / 정합 = 충돌 없음 / 상호작용 = 충돌은 아니고 후속 계획에 적어 둘 것

| # | 결정 | 줄 | 충돌 여부 | 근거 | 권고 처리 |
|---|---|---|---|---|---|
| 1 | DEC-106 (1)·(7) 차동 입력쌍 = role `differential_input_p/n`("이름이 아니라 역할 선언, Q-N4 선례"). 정의 불능 갈래의 하나가 "차동쌍 선언 없이 입력 방향 포트 둘 이상". (7) "(1)의 정의 불능 정지는 포트 역할 선언 기준" | plan:306 | **충돌**(의도된 개정) | O-264 (1)이 바로 이 근거를 구조로 바꾼다. 정의 불능 갈래도 role 기준으로 쓰여 있다 | v6.39.6에서 (1)의 판정 근거와 정의 불능 갈래 셋을 구조로 다시 쓴다: 구조 쌍 둘 이상 / 구조 쌍 없이 입력 포트 둘 이상 / 구조 쌍 + 다른 입력 포트. (7)의 "포트 역할 선언 기준"을 고친다. Q-N4 선례 인용은 "원래 취지와 다름(번복)"으로 표지한다 |
| 2 | DEC-108 (3) 짝 = KVL 짝(gate·source·bulk·kind 넷 동일성 + 출발 L 같음) ∪ 대칭 짝(matching_groups diff_pair·branch_symmetric) | plan:308 (v6.39.5, A-198·A-199) | **충돌**(의도된 개정) | O-264 (2)는 짝을 "쓰기 계획의 VGS 병렬 짝, 묶인 DC 마디 기준"으로 정한다. 지금 문언은 원래 넷 이름으로 비교하고 대칭 짝을 따로 둔다. 같은 개념("gate가 같은 DC 마디")의 정의가 둘이 된다(graph 규칙 3). A-207 214행과 A-208 실측도 같다(대칭 짝 사용 6/6이 입력쌍 반쪽, agent 인용) | A-208대로 v6.39.6에서 대칭 짝 규칙을 지우고 짝을 쓰기 계획의 VGS 병렬 짝으로 바꾼다. **추가 주의**: DEC-106 (3)의 (v0) `parallel_vgs`는 (gate, source)·kind만 본다. DEC-108 (3) (가)는 bulk(VSB)도 결정자로 둔다. 새 짝 정의에 "실효 bulk 같음(DEC-61 기본 포함)"을 남겨야 물리가 맞는다. library 영향은 0/13이다(§3.3) |
| 3 | N3.2 '기본 전달 뷰': 입력 포트가 둘이고 `find_structural_symmetry_candidates`가 두 포트를 대응으로 확인하면 기모드 여기 하나, 아니면 포트마다 단일 여기 | plan:539 | **충돌**(새로 찾음) | "차동 입력"을 셋째 정의(자기동형 대칭)로 정한다. O-264 (3)의 정본 필드 하나와 어긋나고, 같은 계획 764행(N3.8: 기본 뷰 가중은 role p/n)과도 이미 어긋난다. 단일 출력 회로에서는 두 입력 포트가 다른 궤도다(DEC-106 (8) 실측: 다른 궤도 5). 그래서 대칭 기준과 role·구조 기준이 갈린다. as-built `graph/views.py:73-76`은 role 기준이다(재작성 범위 사실) | 539행을 "정본 필드가 차동 입력쌍이면 기모드 여기 하나"로 바꾼다. 대칭 후보 갈래는 지운다. 764행과 같은 정의 하나로 맞춘다 |
| 4 | 차동 입력 판정 소비자 문언: DEC-97 review (b) "두 gate가 회로 차동 입력 포트 p/n"(사용자 결정 2026-10-12 (나')), N3.8 기본 포트 뷰 가중 "role에서 옴", DEC-23 "차동 입력이면 차동 이득·V(p)−V(n)" | plan:296, plan:764, plan:224; user_decisions:290 | **충돌**(문언; 결과 차이 0/13) | O-264 (3)은 판정을 필드 하나에서 READS하라고 한다. 지금 문언은 소비자마다 role 문자열을 직접 읽는다. as-built에는 독립 판정 자리가 적어도 셋 있다: `sizing/writer_plan.py:440-447`, `graph/views.py:73-76`, `authoring/spec_views.py:60-75`. `graph/orbit_matching_crosstab.py:51`도 role을 직접 비교한다. 이것은 graph 규칙 1·3 위반 **의심**이다(판정은 판정자 몫) | 소비자 문언을 "차동 입력쌍 필드 READS"로 바꾼다. **p/n 극성은 다른 축이다**(쌍 여부가 아니라 여기 방향 e의 부호). 계획 764행이 "role을 맞바꾸면 e → −e, 부호가 ε에 흡수"로 이미 극성 불변을 보였다. 그래서 극성의 정본 자리를 따로 정해야 한다. 안: (가) role p/n을 극성 규약으로만 남긴다(축 표기) / (나) O-53 A-1처럼 DC 전달 부호에서 유도한다. 쌍 판정과 극성을 한 문장에 섞지 않는다. 2026-10-12 (나') 문언 변경은 "원래 취지와 다름(근거 교체, 결과 불변)"으로 기록한다 |
| 5 | FR-9·DEC-69·N3.16 '포트' 행(P-4, 사용자 2026-10-12): 포트 방향은 role에서 유도하고 `ports.direction`은 받지 않는다("오면 거부") | plan:180, plan:269, plan:1054, plan:1082; user_decisions:241 | **조건부 충돌** | O-264 (1)의 "입력 방향 포트"를 P-4로 읽으면 방향은 role 문자열에서 나온다(입력 role → input). 그러면 판정이 role을 떠나지 못한다. 반대로 JSON `direction` 키로 읽으면 P-4와 정면으로 어긋난다. as-built 로더 `authoring/ports.py:22,63-66`은 direction을 **필수**로 받는다(계획과 반대, 재작성 범위 사실). topology 13/13의 입력 포트 24/24에 direction이 있고 role과 일치한다(§3.1) | v6.39.6에서 하나로 정한다. 권고 방향: 방향(측정 구성이 구동하는 넷)을 선언 사실로 정본화한다. 이렇게 P-4를 번복하면 role p/n은 쌍 판정 근거가 아니게 된다. topology 수정은 0이다(direction이 이미 13/13에 있음). P-4를 그대로 두면 MG2 구현 때 13개 파일에서 direction을 지워야 한다. 그것은 topology 수정이라 원칙 15에 걸린다(§4). 어느 쪽이든 "원래 취지와 다름(P-4)"으로 기록한다 |
| 6 | DEC-93 (1) 차동쌍 유도: 같은 (kind, **비레일** source) 멤버 중 바이어스 형제를 빼고, 남은 신호 gate 멤버가 **정확히 둘**일 때 derived(3 이상은 review_needed) | plan:293; as-built `graph/matching_groups.py:20-22` | 정합(정의를 고를 때 주의) | DEC-93은 소자 단위 matching 묶음이다(레이아웃·w_f 칸). O-264는 포트 쌍 단위 DC 묶음이다. 정의가 다르므로(축: 소자 matching 대 포트 측정 구성) 필드가 둘이어도 규칙 3 위반이 아니다. 단 O-264 판정을 "DEC-93 **derived** diff_pair ∩ 입력 포트 gate"로 정의하면 rfc_ota(tail 4멤버), erfc_ota(A·B 마디 3멤버씩)가 review_needed라 빠진다. 결과 2/13이 role과 갈리고 정의 불능 정지로 간다(§3.2) | O-264 필드는 DEC-93 후보 집합(`graph.rel_matching_offset`, status 무관)과 `node.port_direction`을 READS해서 포트 쌍 단위로 판정한다. 소스 결합 후보를 다시 계산하지 않는다(둘째 생산자 0). source는 **비레일**로 DEC-93과 같은 정의를 쓴다(§3.4, O-200 물리 근거) |
| 7 | DEC-23 offset 정의 | plan:224 | 정합 | 지금 DEC-23에는 쌍 정의가 없다. 2026-10-08 Q3 정정이 옛 "쌍 = offset 매칭 선언 ∩ ports input 게이트"를 지우고 모든 MOS 오차원으로 바꿨다. DEC-23은 "차동 입력이면" 판정과 여기 방향 e의 **소비자**일 뿐이다. A-209 (d)가 말한 "DEC-23 offset 쌍"은 계획 문언과 다르다(agent 인용, 내 판독은 쌍 생산자 0/1) | #4에 포함한다(READS로 바꿈) |
| 8 | offset-strategy | offset-strategy.plan.md:36, 221 | 정합 | role·ports 판정 자리 0("입력쌍"은 일반 서술 2곳뿐). offset-trim F-5 `input_cells`(offset-trim.plan.md:206)는 소자 단위 입력 셀(첫 gain 블록 ROLE_INPUT)이다. 포트 쌍과 축이 다르다. 그 안의 "noise_decl 두 번째 구현"은 O-264와 무관한 기존 사실이다 | 조치 없음. 다만 offset-trim 개정 때 "차동 입력쌍 필드"와 "입력 셀"의 축을 한 줄 적는다 |
| 9 | O-13 (1): 같은 DC 등식(엣지)은 없애고 변수를 공유한다 | user_decisions:632 | 정합(문언 주의) | O-264 (2)는 "같은 DC(입력 공통모드 변수 하나)로 묶음"이라 변수 공유다. DEC-106 (1)의 정점 묶음과 같다. 다만 "같은 dc로 묶고"를 input_tie 엣지 부활로 읽으면 O-13과 충돌한다 | v6.39.6 문언은 "정점 묶음·변수 공유, 같은 DC 엣지 없음"으로 적는다 |
| 10 | O-168: 입력 포트 공통모드 변수 하나, 연결 대칭(자기동형)과 무관 | user_decisions:1149 | 정합 | O-264의 구조 기준은 소스 결합이다. 대칭이 아니므로 "대칭 무관"과 맞는다. DEC-106의 결정 문언 한정(한 차동쌍)도 그대로다 | 조치 없음 |
| 11 | O-170: v6.38.3 승인(DEC-106 role 기준 포함), U-128 값(nmcnr agnd, current_reuse engine, 4회로 공통모드 변수) | user_decisions:1151 | 정합(근거만 교체) | 결과가 13/13 같으므로 U-128 값과 회로별 적용 범위는 변하지 않는다. 승인 대상이었던 "role 근거"만 바뀐다 | "원래 취지와 다름" 목록에 넣는다(근거 교체, 값 불변) |
| 12 | O-172: current_reuse input_dc = engine(DEC-106 공통모드 변수) | user_decisions:1153 | 정합 | current_reuse는 구조 쌍이 Vip·Vim 하나다(M1a/M1b·M4a/M4b, §3.1). 같은 묶음이다 | 조치 없음 |
| 13 | O-182 Q-LB1: 합격 범위 library 13 | user_decisions:1163 | 정합 | n/N 측정을 13회로 전수로 했다(§3) | 조치 없음 |
| 14 | O-188·DEC-61: bulk 미선언 = kind별 레일 기본 | user_decisions:1169; plan:261 | 정합(짝 정의에 주의) | 차동 입력 판정에는 bulk가 필요 없다(소스 결합이 차동 감지를 정한다). FS-1 짝에는 bulk(VSB)가 결정자다(#2) | #2 처리에 포함한다 |
| 15 | O-197 PDK 이식성 | user_decisions:1178 | 정합 | PDK 값을 쓰지 않는다 | 조치 없음 |
| 16 | O-200 물리 정합 > 손계산, 물리 경계를 수치 문턱으로 정하지 않음 | user_decisions:1181 | 정합 | 구조 판정은 수치 문턱 없이 연결과 측정 구성만 쓴다. 레일 source 제외(#6)는 물리 근거다: 레일은 이상 전압 마디라 두 소자를 결합하지 않는다 | #6대로 비레일을 명시한다 |
| 17 | O-226 LA-1까지 위임(위임 밖: push, 저장소 밖 공유, 근본원칙 변경, topology connectivity, 기준 약화) | user_decisions:1207 | 정합 | 권고 방향(#5 direction 정본화)은 topology 수정 0이고 원칙 변경도 아니다. P-4 번복은 결정 재검토(원칙 20)로 위임 안이다. role 필드 삭제를 택하면 topology 수정이라 위임 밖이다 | role 칸은 지우지 않는다(§4) |
| 18 | O-244: 측정 구성 입력 포트 = `node.port_direction` = input, 판별 하나(재풀이·봉인 3 공용 helper) | user_decisions:1225; plan:678, 682 | 정합(이것을 재사용) | O-264의 "입력 방향 포트(외부에서 구동되는 넷)"는 바로 이 측정 구성 집합이다. 새 판별을 만들면 plan:682 "입력 포트 집합 정의 하나"를 어긴다 | O-264 필드는 그 helper(as-built `authoring/ports.py:34-37 input_port_nets`)가 정하는 집합을 READS한다 |
| 19 | O-257·DEC-108 (2) w_f 칸 = matching_groups mirror·diff_pair·branch_symmetric 폐포 | user_decisions:1238; plan:308 | 정합 | 칸은 소자 matching 축이고 O-264는 포트 DC 묶음 축이다. (2)는 바뀌지 않는다(바뀌는 것은 (3)의 짝, #2) | 조치 없음 |
| 20 | O-262·O-263: trim 파일 포트(작용점·전원·bias·코드 입력)·핀 재연결; "구조 사실(정합 묶음 등)은 원본 회로에서" | user_decisions:1243, 1244 | 상호작용(충돌 아님) | 합성 회로(국면 2)에 trim 포트가 입력 방향으로 들어오면 두 문제가 생길 수 있다. DEC-106의 "차동쌍 + 다른 입력 포트 → 정의 불능"이 발동할 수 있다. 보조 입력쌍 주입형 trim(offset-trim.plan.md:379)은 trim 포트 둘이 소스 결합 쌍 gate에 물려 "차동쌍 둘"이 될 수 있다. O-263 (3)의 "구조 사실은 원본에서"를 따르면 차동 입력 판정도 원본 사실이므로 풀린다 | offset-trim 개정(TR card는 LA-1 뒤) 때 "차동 입력쌍 필드 = 원본 회로 구조 사실"과 "trim 코드·bias 포트의 측정 구성 지위"를 한 줄 적는다. 지금 착수 조건은 아니다 |
| 21 | O-53 A-1: 반전 입력 = 선언 또는 DC 전달 부호, "포트 role 이름은 근거로 쓰지 않음" | user_decisions:673; plan:468 | 정합(선례로 뒷받침) | O-264의 취지(role 근거 금지)와 같다. #4의 극성 대안 (나)의 근거 자리다 | 조치 없음 |
| 22 | 2026-10-14 Q-N4 (가) "포트 역할 = 이름 기반 아님" | user_decisions:369; plan:2940(U-127로 대체됨) | 번복 기록 | Q-N4 (가)의 적용 규칙은 이미 O-53 B3·U-127이 대체했다. DEC-106 (1)이 인용하는 "역할 선언은 이름이 아님" 추론만 O-264가 뒤집는다 | "원래 취지와 다름(Q-N4 추론 번복)"으로 표지한다. 다른 조치는 없다 |
| 23 | A-196~A-206(v6.39.5·FS-1 처리) | la1_auto_decisions:202-212 | #2에 포함 | A-198·A-199의 대칭 짝 규칙이 #2의 대상이다. A-203 L 조건 실측(출발 불능 0/82)과 A-205·A-206 뷰 의존 inactive는 O-264와 무관하다 | A-208이 이미 v6.39.6에 넣었다. 그대로 간다 |
| 24 | A-207·A-208·A-209 | la1_auto_decisions:213-215 | 정합 | O-264와 같은 방향이다(짝 = 쓰기 계획 VGS 병렬 짝, role 판정 재작성, 소비자 READS). A-209 (d)의 "DEC-23 offset 쌍" 표현만 #7과 같이 바로잡는다 | A-209 (d) 문언을 "DEC-23 '차동 입력이면'·e 소비"로 정정한다 |
| 25 | 원칙 12(이름·매직넘버 금지, n/N), 14(연결·원문만, analog-grammar 태그 근거 아님) | CLAUDE.md:37, 39 | 정합 | 구조 판정은 이름 0, 상수 0이다. 일반성은 13/13이다(§3). ports role은 analog-grammar 산물(device_roles 등)은 아니지만 사람·Claude 선언 태그다. 판정 근거에서 빼는 것은 원칙 14를 강화하는 방향이다 | 조치 없음 |
| 26 | 원칙 15(topology connectivity 사용자만) | CLAUDE.md:41 | 관계 있음(§4) | ports 선언은 사용자 확인 대상이었다(U-08 plan:2823 "connectivity 제안표 확인", two_stage ports 주석 "사용자 확정") | §4 |
| 27 | 상위 graph 단일 정본(필드마다 writer 하나, 같은 정의 = 필드 하나, 정본 자리 없으면 멈춤) | fpga/CLAUDE.md '★graph 단일 정본' | 정합(정본 자리 있음) | 정본 자리 후보: S1 구조 유도 블록 하나. 입력은 `graph.rel_matching_offset`(DEC-93 후보)과 `node.port_direction`(O-244 집합)을 READS한다. as-built `graph/matching_groups.py:83`이 이미 같은 두 칸을 읽는 S1 블록이다(재작성 범위 사실). 따로 블록을 세우거나 이 블록의 writes에 칸 하나를 더할 수 있다. 자리 이름은 design 몫이다 | "정본 자리 없음" 사유는 없다. 멈출 일이 아니다 |
| 28 | O-229 임시 규칙(시기·범위) | chip-design-skills/CLAUDE.md 머리 | §5 | | §5 |

## 2. 특히 확인할 질문에 대한 답

### Q1. 입력 방향 선언을 '이름'이 아닌 인터페이스 사실로 써도 되는가?

**쓸 수 있다(판정: 맞음, 실측 근거).** 단 정본 자리는 #5에서 하나로 정해야 한다.

- 물리 결정자: 측정 구성. 어느 넷을 이상 전압원이 구동하는지는 회로 밖의 사실이다(O-244, plan:678). 연결 그래프에는 그 정보가 없다.
- 실측(`o264_undriven.txt`): "회로 안에 DC 구동 단자가 없는 넷(gate·capacitor만)"을 입력으로 추정해 보았다. 입력 포트가 아닌 그런 넷이 11/13 회로에 있다: cnr LPCO·VCR, common_gate VNBias1·2·VPBias1, current_reuse Voc, erfc Z, folded bias3, ngcc VBN·VBP, nmcnr VB1~5, pushpull VNB1·VPB1, r2r vb1·vb3·vb4·vb5n·vb6n, two_stage bias, two_stage_sf bias. common_gate의 입력 vin은 source 단자 2개에 물려 그 추정에서 빠진다.
- 그 결과 연결만으로 입력을 추정하면 r2r_opamp M29/M30(gate vb6n/vb5n, 같은 nmos, source n_t29)이 거짓 차동 입력쌍이 된다(1/13). 그래서 방향 선언은 판정에 꼭 필요한 인터페이스 사실이다. 이름이 아니다.
- 원문 쪽 근거: 이번 점검에서는 열지 않았다(불확실 표지). 물리 근거는 계획에 이미 정본으로 있는 측정 구성 정의(plan:678)다.

### Q2. DEC-23·단계 A 구조 유도(DEC-93 diff_pair)·offset-strategy 사이에 둘째 생산자가 생기는가? 정본 필드 하나를 둘 자리가 있는가?

- DEC-23: 쌍 생산자가 아니다(Q3 정정 이후). 소비자다. offset-strategy: role 판정 자리 0. offset-trim F-5 input_cells는 소자 축이라 다른 정의다.
- DEC-93 diff_pair는 소자 matching 축이다. 포트 쌍 판정과 정의가 다르므로 필드가 둘이어도 된다. 다만 축을 문서에 적어야 한다(상위 규칙 3).
- **둘째 생산자 위험은 두 곳이다.**
  - (a) O-264 블록이 소스 결합 후보를 DEC-93과 따로 다시 계산하는 경우. 그래서 `rel_matching_offset`을 READS해야 한다.
  - (b) 기본 전달 뷰(plan:539, 대칭 기준)·N3.8(plan:764, role)·DEC-97 review(plan:296)·쓰기 계획이 각자 판정을 유지하는 경우. 그래서 모두 READS로 바꿔야 한다. as-built에는 독립 판정이 3곳 이상 있다(#4).
- 정본 자리: 있다(#27).
- **정의 선택 주의**: "DEC-93 derived 쌍"을 쓰면 안 된다. rfc·erfc가 review_needed라 2/13이 빠진다(#6, §3.2). 후보 집합을 status와 무관하게 쓰고 포트 쌍 단위로 판정한다.

### Q3. 구조 판정과 role 판정이 갈리는 회로

§3 표를 본다. library 13회로에서 O-264 문언 그대로 판정하면 **갈림 0/13**이다. 정의를 "DEC-93 derived 쌍"으로 좁히면 **갈림 2/13**(rfc, erfc)이다. CMFB 오차증폭기·다중 입력·계측 증폭기형의 결과도 §3에 있다.

### Q4. 원칙 15와 role 칸 처리

§4를 본다.

### Q5. O-229 시기와 범위

§5를 본다.

## 3. 구조 판정 대 role 판정 n/N

### 3.1 O-264 문언 그대로(입력 방향 포트 두 개 × 같은 kind·같은 source 소자쌍의 두 gate) — `o264_out.txt`

| 회로 | role 판정(입력쌍) | 구조 판정 | 구조 근거(소자, kind, 공통 source) | 일치 |
|---|---|---|---|---|
| cnr_ota | VIP/VIN | VIP/VIN | x2.M1·x22.M1, nmos, VS | 예 |
| common_gate_amplifier | 없음(single_ended_input vin) | 없음(vin은 source 입력) | — | 예 |
| current_reuse_telescopic_ota | Vip/Vim | Vip/Vim | M1a·M1b pmos Vx / M4a·M4b nmos Vy(쌍 2개, 포트 쌍 1개) | 예 |
| erfc_ota | vin_p/vin_n | vin_p/vin_n | M11·M2A·M2B pmos A / M12·M1A·M1B pmos B(교차 결합, 마디마다 3멤버) | 예 |
| folded_cascode | vin_p/vin_n | vin_p/vin_n | M1·M2 nmos tail | 예 |
| ngcc_3stage_ff | Vinp/Vinn | Vinp/Vinn | M1·M2 pmos TAIL | 예 |
| nmcnr_amplifier | Vin_p/Vin_n | Vin_p/Vin_n | M102·M103 pmos NodeTail | 예 |
| pushpull_follower_buffer | 없음(single_ended_input) | 없음(vin → M3 pmos A, M4 nmos B; kind·source 다름) | — | 예 |
| r2r_opamp | Vinp/Vinn | Vinp/Vinn | M1·M2 pmos tail_p / M3·M4 nmos tail_n(상보 쌍 2개, 포트 쌍 1개) | 예 |
| rfc_ota | vin_p/vin_n | vin_p/vin_n | M1a·M1b·M2a·M2b pmos tail(4멤버) | 예 |
| sf_pushpull_output_opamp | vin_p/vin_n | vin_p/vin_n | M1·M2 nmos TAIL | 예 |
| two_stage_ota | vin_p/vin_n | vin_p/vin_n | M1·M2 nmos CS | 예 |
| two_stage_ota_sf | vin_p/vin_n | vin_p/vin_n | M1·M2 nmos CS | 예 |
| **합계** | 차동 11 · 단일 2 | 차동 11 · 단일 2 | 공통 source가 레일인 쌍 0/13 | **13/13 일치(갈림 0)** |

heldout: `assets/heldout`는 master에 없다. 옛 heldout 4회로(rfc·erfc·r2r·cnr)는 library로 옮겨졌다(DEC-85 "이관 4회로", plan:285). 초안 사본 `wt/_heldout/{A_rfc, A_rfc_core, B_erfc, C_r2r, D_cnr}.topology.json` 5파일도 같은 판정으로 5/5 일치했다(library 판정의 중복 확인일 뿐이고, 독립 표본이 아니다).

### 3.2 정의를 'DEC-93 derived diff_pair'로 좁힐 때(규칙 문언 판독, 엔진 실행 없음)

| 회로 | 입력 gate 소스 결합 멤버 수 | DEC-93 (1) status | 갈림 |
|---|---|---|---|
| rfc_ota | tail 4 | review_needed(정확히 둘 아님) | **갈림** |
| erfc_ota | A 3 · B 3 | review_needed | **갈림** |
| current_reuse | Vx: M1a·M1b + M58(gate Vbias2) / Vy: M4a·M4b + M63(gate Vbias3) | 바이어스 형제를 빼면 derived(조건부, M58·M63 형제 판정은 실측 안 함) | 조건부 0 |
| r2r_opamp | tail_p: M1·M2 + M8(gate n_m31) / tail_n: M3·M4 + M5(gate vb3) | 형제를 빼면 derived(조건부, 같음) | 조건부 0 |
| 나머지 9 | 2 | derived | 0 |
| **합계** | | | **갈림 2/13 + 조건부 2/13** |

→ O-264 필드는 DEC-93 후보 집합(status 무관)으로 정의해야 한다(#6).

### 3.3 FS-1 짝의 bulk(VSB) 조건 — `o264_bulk.txt`

입력 점을 묶은 뒤 같은 (kind, gate 마디, source) MOS 쌍 가운데 실효 bulk(선언 또는 DEC-61 기본)가 다른 쌍: **0/13 회로**. supplies 선언이 없는 4회로(cnr·erfc·r2r·rfc)는 기본 레일을 전위로 정할 수 없어서 선언 bulk끼리만 비교했다(조건부). 그래서 bulk 조건을 빼도 지금 library 결과는 같다. 그러나 물리 결정자(VSB)이므로 문언에는 남긴다(#2).

### 3.4 요청 유형별

| 유형 | library 사례 | 구조 판정 | role 판정 | 결과 |
|---|---|---|---|---|
| CMFB 오차증폭기(내부 마디 gate의 소스 결합 쌍) | current_reuse M37a/M37b(Voc/Voc_des), cnr x42/x43(LPCO/VCREF), r2r M29/M30(vb6n/vb5n) — 3/13 | 입력 포트가 아니므로 제외 | 대상 아님 | 3/3 일치. 단 방향 선언 없이 연결만으로 입력을 추정하면 r2r가 거짓 양성이다(Q1) |
| 다중 입력(차동쌍 둘 이상 / 차동쌍 + 다른 입력) | 0/13 | DEC-106 정의 불능 갈래로 간다(문언을 구조로 다시 써야 함, #1) | 같음 | 대상 0 |
| 상보 입력쌍(한 포트 쌍에 결합 쌍 2개) | current_reuse, r2r — 2/13 | 포트 쌍 1 | 1 | 2/2 일치 |
| 분할·교차 결합 입력쌍(3~4멤버) | rfc, erfc — 2/13 | 포트 쌍 1(문언 그대로) / 빠짐(derived 한정) | 1 | 문언 그대로면 일치, derived 한정이면 갈림 |
| 계측 증폭기형(3-opamp, 입력 버퍼 follower) | 0/13 | 입력이 follower gate만 물고 소스 결합 없음 → 차동 아님 → 정의 불능(fail-closed). 원리상 role("차동")과 **갈린다**(불확실: 회로 없음, 판독만) | 차동 | 표본 0. 갈리면 fail-closed 방향(묶지 않고 정지)이라 fail-open은 아니다 |
| 소스 퇴화(두 source가 저항으로 나뉜 쌍)·의사 차동(레일 source) | 0/13 | 퇴화: 같은 source 넷이 아니므로 빠짐(fail-closed). 의사 차동: 문언 그대로면 레일 source 공유라 차동으로 잡힘 → 비레일 한정 필요(#6) | 선언대로 | 표본 0. 레일 한정 문언 보완 |
| 단일 입력 | common_gate, pushpull — 2/13 | 없음 | 없음 | 2/2 일치 |

## 4. 원칙 15와 role 칸

- ports 선언은 사용자 확인 대상인 topology 사실이었다(U-08 plan:2823 "connectivity 제안표 확인"; two_stage_ota.topology.json:360 주석 "출력 포트 OUT 추가(사용자 확정)").
- O-264를 권고 방향(#5: direction 정본화, role p/n은 쌍 근거에서 뺌)으로 구현하면 **topology 파일 수정은 0이다.** direction은 이미 13/13에 있고 입력 포트 24/24가 role과 일치한다.
- role 칸을 지우거나 이름을 바꾸는 일, 또는 P-4를 유지한 채 MG2("direction 오면 거부")를 구현해 13개 파일에서 direction을 지우는 일은 **topology 수정이다.** 그래서 원칙 15·O-226 위임 밖이고, 대기열과 사용자 승인으로만 간다.
- 권고: role 칸은 그대로 둔다. 쌍 판정 근거로 쓰지 않는다. 극성 규약으로 남길지는 #4의 (가)/(나) 중 계획에서 정한다. 출력 role(differential_output_p/n; plan:296, as-built achievability.py:291, s1v_fields.py:87)의 같은 문제는 O-264 범위 밖이다 → LA-1 재점검 입력.

## 5. O-229 시기와 범위

- FS-1 범위(plan:2731-2750, N6.43): w_f 칸, 출발값(DEC-108 (3) 짝 포함), DC 블록 개정.
- O-264 (2)의 "FS-1 짝 = 쓰기 계획 VGS 병렬 짝" → **FS-1 범위 안**이다(DEC-108 (3) 개정, A-208 그대로).
- O-264 (1)(3) → **FS-1 범위 밖**이다. 해당 작업:
  - 구조 판정 블록·필드 신설
  - 쓰기 계획 입력 점(DEC-106, IT-1이 구현해 병합됨, as-built `writer_plan.py:440-447`)의 READS 전환
  - 기본 포트 뷰(`views.py`, `spec_views.py`; plan:539·764)
  - ICMR·icm_config(IT-2c)
  - DEC-97 crosstab(`orbit_matching_crosstab.py`)
  - oracle 넷리스트 생산자(EO-1)·CPG-1 bench: agent 인용(A-209), 직접 확인 안 함
- library에서 role과 구조 결과는 13/13 같다. 그래서 FS-1은 지금 쓰기 계획 출력(role 기준)을 READS해도 결과가 바뀌지 않는다. FS-1 재개는 이 card를 기다릴 필요가 없다.
- 그러나 같은 판정을 독립으로 계산하는 자리가 셋 이상 있다(#4). 이것은 graph 단일 정본 위반 의심이고, O-229 1번상 완화할 수 없는 항목이다. 따라서 **별도 card 하나**(가칭 '차동 입력 구조 판정 필드 + 소비자 READS 재작성', 옛 판정 자리를 같은 변경에서 삭제)를 둔다. 순서는 **LA-1a + LA-1 통합 병합 앞**이다. O-229 4번의 "새 인프라"가 아니라 엔진 변경이다. test 범위는 O-229 2번(그 card toy + structure + 2회로 연기 + 이름 불변성)이다.
- **s1_symmetry 주의**: as-built `graph/s1_symmetry.py:144`는 role p 포트를 정준 위치 동률 깨기에 쓴다. 극성 정본을 #4 (나)로 바꾸면 정준 순서가 바뀔 수 있다. 그러면 `search/test_canonical_order.py`에 영향이 간다. 극성은 이 card에서 (가) 유지로 두고, 바꾸는 일은 LA-1 재점검 입력으로 미루는 것이 범위를 지킨다.

## 6. 원래 취지와 다름(v6.39.6에 기록할 것)

1. P-4(user_decisions:241; FR-9·DEC-69·N3.16)의 "방향은 role에서 유도, direction 거부"를 번복한다(#5, 권고 방향을 택할 때).
2. Q-N4 (가)의 "역할 선언은 이름이 아님" 추론을 번복한다(DEC-106 (1) 괄호, #22).
3. 2026-10-12 (나') diff_pair review 조건 (b)의 근거를 role에서 필드로 바꾼다(결과 불변, #4).
4. v6.39.5 DEC-108 (3) 대칭 짝 규칙을 철회한다(A-208, #2).
5. O-170이 승인한 DEC-106 role 근거를 교체한다(값 불변, #11).
6. plan:539 기본 전달 뷰의 대칭 후보 갈래를 삭제한다(#3).

## 7. 점검 범위와 한계

- 읽은 것:
  - `user_decisions.md`(O-13·53·168·170·172·182·188·197·200·226·244·257·262·263·264, P-4, (나'), Q-N4 행)
  - `la1_auto_decisions.md`(A-196~A-209)
  - 계획(DEC-23·61·69·93·97·106·108, FR-9, N3.2-539, N3.6-678·682, N3.8-764, N3.16-1082, N6.43, U-08, U-127)
  - offset-strategy·offset-trim 계획의 role 관련 행
  - topology 13개 + 초안 5개
  - 엔진 소스의 role 소비 자리(재작성 범위 사실로만)
- 안 한 것:
  - 엔진 실행(DEC-93 status는 규칙 문언 판독)
  - 원문 PDF 쪽 대조(불확실 표지)
  - oracle EO-1의 role 소비 직접 확인(A-209 인용)
  - current_reuse M58·M63, r2r M8·M5의 바이어스 형제 판정 실측(조건부)
- 메모리: 시작 때 여유 5.58 GB. 1 GB 미만 정지 조건에 해당한 적 없음.
