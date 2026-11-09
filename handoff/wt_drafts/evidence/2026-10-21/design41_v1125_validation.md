# design 41 v1.12.5 · IT-2c card 재동결 -- 독립 검증 + design↔계획 gap 분석

- 대상: worktree `wt/design-it2c-o79`, 브랜치 `design/it2c-o79`, 커밋 `88bc5f2f`, base master `93a9ff82`(계획 v6.26)
- 변경 파일 4개(18+/15-): design 41(줄 3·4·17·734·738·744·811), `20261021-it2-common.md`, `it2c-icm-config.spec.md`, `it2c-icm-config.interface.md`
- 방법: 읽기만 함. `git -C`·`grep`·Python으로 줄을 추출. 상태를 바꾸는 git 명령은 쓰지 않음.
- 검증자 = 작성자가 아님. 엔진 코드는 열람해 사실만 확인함.

## 0. 판정

**점수 84/100. 필수 1건, 권고 9건.** 새 갈래(41:734)는 계획 v6.26 O-79·O-80 R1·R2와 맞습니다. 물리도 계획 문언 범위 안에서 맞습니다. 그런데 같은 design·card 안의 **L10 (e)가 '용량 되먹임 toy 창 = 손계산'을 그대로 남기고 있습니다.** 이 문장은 새 L8 (b1)과 서로 어긋나며, 그 뿌리는 계획 완료 조건 (10)(e)입니다(필수 MF-1).

## 1. 새 갈래(41:734)의 정확성·일반성

| 항목 | 실측 | 판정 |
|---|---|---|
| code `icm_config_feedback_no_dc` | 41:734 (1)에서 정의, 41:744 (2) 목록, 공통 문서 84행 목록, spec·interface에 있음. category `definitional`, 경로는 `config` None → M7 | 맞음 |
| '없는 DC 성분' = `DC_CONDUCTING_PASSIVE_KINDS` | `gmid_engine/authoring/dc_edges.py:11` `DC_CONDUCTING_PASSIVE_KINDS = ("resistor",)`. 줄 인용이 맞음. 엔진의 DC 전도 정의가 여기 하나라서 import만 하고 새 분류기를 만들지 않음 | 맞음 |
| 일관성: `conductance_matrix` | `_helpers_nodal.py:26-33`은 MOS와 `circuit.resistors`만 넣음. 용량은 넣지 않음. 그래서 kind 정의와 S-3 망 정의가 같은 경계를 씀 | 맞음 |
| R2: 단일 입력이 먼저 | 41:734에 '입력이 하나이면 `as_is_single_input`이 이 갈래보다 먼저다'가 있음. 계획 584 O-80 R2 문언과 같음 | 맞음 |
| 물리 | 용량만 있는 되먹임은 DC에서 열림 → S-3 망에는 되먹임이 없음 → 선언 구성은 개루프. 계획은 이 경우를 정의 불능으로 정함(O-52가 '개루프 별도 정의'를 기각, O-50 G4 취지). design은 그대로 따름 | 맞음 |
| 혼합 R+C | '그중 kind ∈ … 소자가 없으면'이므로 R이 하나라도 있으면 `declared_feedback`. 용량은 `conductance_matrix`에서 빠지므로 '용량 제외·저항 포함' 망이 됨 | 맞음 |
| 빈 목록 `[]` | 41:734에 '선언 소자 0개(빈 목록 = β=1 루프, `spec_elements.py:19-20`)는 이 갈래가 아니다'라고 적음. 인용 줄 19-20 실측이 맞음(docstring '빈 list = 되먹임 수동소자 없음 = β=1 루프'). 계획 1512 '`()` = 미선언 갈래로 읽는다', oracle N3.9 ICMR 행 '`[]` → 미선언(β = 1 follower), design 이름 `unity_follower` -- 선언 + DC 성분 없음으로 읽지 않는다'와 같음. **작성자 해석 1이 맞음** | 맞음 |
| 13회로 해당 수 | `assets/{library,heldout}/*.sizing_spec.json`의 feedback: 12개는 `[]`, `current_reuse_telescopic_ota`만 `['Cf1','Cf2']`. 이 회로는 차동 출력이라 S-OS2로 감. 새 갈래 해당 0개 | '0개'가 맞음 |
| 일반성(물리, 계획 몫) | 판정이 kind로 정해짐. spec 검사(`spec_elements.py` `_cut_hits`)는 소자마다 입력 넷 단자가 정확히 하나이기만 요구함. 그래서 'C_f(출력–in−) + R_b(in−–기준)' 꼴은 R이 있어 `declared_feedback`이 됨. 그러나 출력과 반전 입력 사이 DC 컨덕턴스 경로가 없어 DC에서 개루프임. 물리적으로 가장 일반적인 규칙은 '선언 소자의 DC 성분 망에서 출력–반전 입력 경로가 없음'임. 계획 문언이 '(용량만)'이라 design은 계획대로임. 해당 0개 → 권고 N7(계획 확인) | 계획 문언 범위 안에서는 맞음 |

## 2. L8 (b1)/(b2) 기대값

- (b1) 용량만 선언, 단일 출력, 입력 둘 → `config is None`, `undefined` = 그 code 하나, `node.dc_window_cfg` 항목 없음, 세 metric은 M7로 정의 불능. 구조만 보는 기대값이라 손으로 정할 수 있음. 모양은 S-OS1 단언(L8 (d) 'OS (f) 꼴 toy')과 같음. 차이 하나: S-OS1에는 '선언 `icm_margin_v` 제약 점이 unmeasured' 단언이 있는데 (b1)에는 없음 → 권고 N9.
- (b2) 저항 선언 → `declared_feedback`. 창은 S-3 망(저항이 G에 들어감)에 (3) 반전 입력 KCL 스칼라 닫음을 더한 연립의 끝임. 게이트 전류가 0이므로 u = V_out·R_g/(R_f+R_g) 꼴이 되어 손계산이 됨. 기존 (3)·`saturation_window` 경로를 그대로 씀.
- M7 경로: IT-2d의 `icm_window_metrics(ports, input_dc, config_undefined=())`는 code를 나열하지 않고 `graph.icm_config.undefined`를 그대로 넘김. 그래서 새 code도 같은 경로로 흐르고 IT-2d 계약 변경이 필요 없음.

## 3. card 재동결

| 항목 | 실측 | 판정 |
|---|---|---|
| 바뀐 범위 | card diff는 code 목록 1곳, L8·L10 행·T-L8·T-L10, spec '관찰 가능한 계약' 한 줄, '거부해야 할 입력' 한 줄, 재동결 기록 한 줄. 그 밖은 바뀌지 않음 | O-79/O-80 범위만 바뀜 |
| 줄 인용 | HEAD 41의 811행 = L8, 812행 = L10(Python으로 추출). 모든 diff hunk가 1줄 대 1줄이라 '줄 추가 없음'이 맞음 | 맞음 |
| R3 | 계획은 L8 41:810 → 41:811만 지시했음. card는 L10 41:811 → 41:812도 고침. 같은 한 줄 밀림을 바로잡은 것이라(이전 검증 230행) 정당함. 계획 문언보다 넓지만 결함은 아님 | 초과(정당) |
| IT-2d | spec 24행 'L8 (a) 포트 집합 끝(41:811 v1.12.4)'. L8은 v1.12.5에서도 811행이고 (a) 문언도 같아서 인용은 유효하고 판 표시만 낡음. IT-2d는 code를 나열하지 않고 공통 문서 code 절(갱신됨)을 정본으로 씀. M7 metric 쪽은 L10 (h) '구성 None toy'가 code와 무관하게 덮음. IT-2c interface는 '(b1)의 M7 metric 쪽 단언은 IT-2d'라고 하는데, IT-2d 판정 목록에는 L8 (b1)·(d)의 M7이 이름으로 나오지 않음(S-OS1부터 있던 공백) | **필수 아님** -- 권고 N5 |
| design 40·42 | 40:556은 `IcmConfig` 행에 config None 갈래 code(S-OS1·S-OS2)를 판별로 적음. 42 D-IT2 행은 판별 변경 요약. 둘 다 v1.12.4에 머묾. 계획 R1은 'design 41과 IT-2c card에서 다음만 고친다'라고 정함 | 이번 판에서 바꿀 의무는 없음. 다음 40/42 판 올림 때 덧붙이기 -- 권고 N6 |
| **L10 (e)** | 41:812 '(e) 용량 되먹임 toy·저항 되먹임 toy 창 = 손계산'은 바뀌지 않았음. card T-L10은 '(b)~(g)'로 (e)를 포함하고, spec 31행은 'L10 (a)~(g)'임. 용량만 선언 단일 출력 toy라면 (b1)(창 없음)과 정면으로 어긋남. 뿌리는 계획 N6.6 완료 조건 (10)(e)(1510행) '선언 되먹임 toy(용량 선언)와 저항 되먹임 toy … (용량 제외·저항 포함)로 잰 창과 손계산 일치'로, v6.26에서 맞추지 않았음. 이전 검증(plan_o78_validation)도 놓쳤음 | **필수 MF-1** |

## 4. graph 단일 정본(별도 항목)

| 검사 | 실측 | 판정 |
|---|---|---|
| 새 필드 | 없음. 쓰기는 기존 `graph.icm_config` 하나뿐이고 `node.dc_window_cfg` 항목은 쓰지 않음 | 통과 |
| writer | `icm_config` 그대로(41:730·734 '쓰기는 이 블록의 `graph.icm_config` 하나') | 통과 |
| 새 cache·memo·sctx 슬롯·EvalResult 칸 | 없음 | 통과 |
| 값 사본 | 없음. `IcmConfig` 칸 집합과 `config` 값 집합이 그대로임(744 (1)) | 통과 |
| 둘째 생산자 | DC 전도 정의는 `dc_edges.py:11` import 하나. 판정은 블록 안 지역 술어임. 같은 술어를 내는 자리는 지금 없음. 뒤에 S-OS2 일반형 card가 'DC 성분' 판정을 하면 같은 술어를 공유해야 함(권고 N2와 같이) | 통과(주의 1) |
| 입력 버전 | 판정에 쓰는 소자 kind의 출처를 design이 적지 않았음. `NoiseDecl.feedback`은 이름만 담음(`noise_types.py:23-28`). kind를 투영 밖에서 읽으면 입력 버전이 빠짐 | 미확인 -- 권고 N2 |

## 5. gap 표(계획 문장 → design/card 자리)

| 계획 문장 | design/card 자리 | 판정 |
|---|---|---|
| O-79 N3.8(584): 단일 출력 + DC 성분 없는(용량만) 선언 되먹임 = 정의 불능, 사유 기록 | 41:734 (1), 41:738, 41:744 (2), spec 30행, interface T-L8 | 일치 |
| O-79: 이름은 design 41 | `icm_config_feedback_no_dc`(41:734) | 일치 |
| O-79: 해당 0개, 생기면 계획부터(S-7) | 41:734 '해당 회로 0개 … 생기면 계획부터' | 일치(실측 0개) |
| O-79: 정의 자리는 N3.8 하나(oracle은 인용) | 41:734 '정의 정본 = 계획 … 이 design은 code 이름만 정한다' | 일치 |
| O-79 / N6.6(1514): IT-2c 착수 전 design 41 L8 (b)·card 수정 | 41:811 (b1)(b2), 공통 72·288행, spec, interface | 일치 |
| R1 (i): code 하나를 744 (2)에 추가 | 41:744 (2) | 일치 |
| R1 (ii): 용량만 단일 출력 toy → `config is None` + 새 code, 선언 구성 창 test는 저항 toy로 | 41:811 (b1)(b2), T-L8 | 일치 |
| R1: `config` 값 집합 그대로 | 41:731·744 (1) 바뀌지 않음, 811 (b2) '그대로' | 일치 |
| R2: 단일 입력이면 `as_is_single_input` 먼저 | 41:734, spec 30행 | 일치. 이를 단언하는 test는 없음 -- 권고 N4 |
| R3: card L8 인용 41:810 → 41:811 | 공통 72·288행, spec 31행, interface 34행 | 일치. L10 812까지 고친 것은 초과(정당) |
| 계획 N6.6 완료 조건 (10)(e)(1510): '용량 선언 toy' 창 = 손계산 | 41:812 L10 (e), card T-L10 | **어긋남(MF-1)** -- 계획 자체가 v6.26 N3.8과 맞지 않게 남아 있음 |
| 계획 N6.6 완료 조건 (8)(b): '선언 구성(DC에서 용량 열림)으로 잰 창' | 41:811 (b2) | 일치(저항 toy로 읽을 수 있음). 문언은 낡았음 -- 권고 N8 |
| 계획 1512: `()` = 미선언(β=1) 갈래 | 41:734 '빈 목록은 이 갈래가 아니다', T-FB | 일치. T-FB 대조표에는 적혀 있지 않음 -- 권고 N1 |

## 6. IT-1 영향

- IT-1 card(`20261021-it1-input-tie-removal.{spec,interface}.md`)가 인용하는 41 줄은 666-674, 816, 820, 1686-1694, 1947입니다. 이번 diff가 고친 줄은 3·4·17·734·738·744·811뿐이고 줄 추가도 없어 겹치지 않습니다.
- IT-1 card 파일은 이번 diff에 없습니다. IT-1 card에 `feedback`·`icm_config`·L8·L10 언급은 0건입니다.
- 결론: `role/test/it1`의 test 작성에는 **영향이 없습니다**.

## 7. 필수

- **MF-1**: L10 (e)(41:812)와 card T-L10 (e)는 '용량 되먹임 toy 창 = 손계산'을 기대합니다. 새 L8 (b1)은 같은 꼴(용량만, 단일 출력)에서 창이 없어야 한다고 합니다. test 작성 주체가 두 기대를 함께 받습니다. 원인은 계획 완료 조건 (10)(e)가 v6.26에서 맞춰지지 않은 것입니다. 계획을 먼저 고칩니다(S-7). 한 줄 정렬안: '(e) 용량+저항 선언 toy(DC 망 = 용량 제외·저항 포함)와 저항 되먹임 toy에서 …'. 정렬 뒤 41:812 (e)와 공통·spec·interface T-L10에 'toy는 단일 출력, 저항 포함(용량만이면 (b1))'을 넣습니다. R1의 '다음만 고친다' 범위 밖이므로 사용자 확인 한 줄이 필요합니다. 고르는 쪽은 둘 중 하나입니다. (가) (10)(e)를 '용량+저항 혼합 toy'로 읽는다(새 결정이 아닌 정렬). (나) (10)(e)의 용량 toy 몫을 (b1)으로 바꾼다.

## 8. 권고

- N1: interface T-FB 대조표에 네 줄을 적어 넣습니다. tuple(R 포함) → `declared_feedback` / tuple(용량만, 단일 출력, 입력 둘) → `icm_config_feedback_no_dc` / `()` → `follower_beta1`(no_dc면 red) / `None` → 결정 대기 갈래. 해석 1(`[]` ≠ no_dc)을 막는 test가 됩니다.
- N2: 판정에 쓰는 소자 kind의 출처(extras의 어느 값인지)를 41:734에 한 구절로 적습니다. `NoiseDecl.feedback`은 이름만 있습니다. 출처를 적지 않으면 code 작성자가 멈추거나, 투영 밖 읽기로 입력 버전이 빠질 수 있습니다.
- N3: 같은 단일 출력에서 S-OS1(`icm_config_output_root_w3`)과 no_dc가 함께 걸릴 때 code 순서를 정합니다('`undefined` = 하나' 단언이 서려면 필요함). no_dc 갈래의 `inverting_port`·`tied_ports`·`transfer` 값(None/()/() 추정)도 정합니다.
- N4: R2 우선순위 toy를 덧붙입니다(단일 입력 + 용량만 선언 → `as_is_single_input`). spec 검사가 이 꼴을 받는지는 이전 검증 RU1과 마찬가지로 실행해 보지 않았습니다.
- N5: IT-2d spec 24행 판 표시를 'v1.12.4'에서 'v1.12.5'로 바꿉니다(줄·내용은 같음). IT-2d 판정 목록에 'L8 (b1)·(d) M7 metric 쪽(L10 (h)와 같은 경로)'을 이름으로 적습니다.
- N6: 다음 40/42 판 올림 때 40:556 `IcmConfig` 행과 42 D-IT2 행에 v1.12.5 갈래를 덧붙입니다.
- N7(계획 몫): 'DC 성분 없음'을 kind로 판정하지 않고 '선언 DC 성분 망에서 출력–반전 입력 경로 없음'으로 일반화할지 정합니다. C_f + R_b(in−–기준) 꼴이 kind 판정으로는 개루프 창을 냅니다. 해당 0개입니다(물리 정합 최우선 원칙에 따라 보고함).
- N8(계획 몫): 완료 조건 (8)(b) 문언을 v6.26 N3.8에 맞춥니다(MF-1과 같은 커밋).
- N9: L8 (b1)에 S-OS1과 같은 '선언 `icm_margin_v` 제약 점 unmeasured' 단언을 넣을지 정합니다.

## 9. 미확인

- U1: kind 출처(N2). icm_config extras 안 '선형 선언 소자'에 kind가 들어 있는지 열어 보지 않았습니다.
- U2: 단일 입력 + 용량만 선언을 spec 검사가 받는지 실행해 보지 않았습니다.
- U3: `role/test/it1` 브랜치의 실제 test 파일은 열지 않았습니다. card 인용 줄로만 판정했습니다.
- U4: 41:735의 대표 회로 실측(`dvout_feasibility.md`)은 이번 변경 범위 밖이라 다시 재지 않았습니다.
