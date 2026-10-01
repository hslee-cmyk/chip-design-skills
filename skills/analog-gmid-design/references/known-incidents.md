# 알려진 사고 기록 (정본) — SKILL.md 절대 원칙의 근거

> SKILL.md 상단 "핵심 원칙"의 절대 원칙 4개는 각각 아래 사고에서 도출됐다. 원칙 자체는
> SKILL.md에 한 줄로 유지하고, 판단 근거가 더 필요할 때만 이 문서를 연다.

## 사고 1 — 함수를 호출하지 않고 손으로 축약/재구성함

telescopic OTA 리포트에서 `build_stick_diagram()`을 호출하지 않고, 100핑거짜리 stack을
8개짜리 "대표 패턴"으로, 8핑거로 사이징된 소자를 게이트 1개짜리 시퀀스로, closed circuit인
소자를 2개짜리 open path로 손으로 지어 넣었다. §4의 결정 텍스트와 §5의 시각 자료가 서로
다른 소스에서 나와 어긋났다.

**틀린 이유**: 함수가 이미 있는데 그 출력을 손으로 흉내 내면 함수를 쓰는 목적 자체가
무효화된다. 길다/복잡하다/패턴이 뻔하다는 사유는 축약의 근거가 되지 않는다.

**규칙**: 리포트에는 함수를 실제로 실행한 반환값을 자르거나 다시 쓰지 않고 그대로 옮긴다.
시퀀스가 길어지는 것은 축약할 이유가 아니다 — 리포트 HTML은 긴 시퀀스의 가로 스크롤을
지원한다.

## 사고 2 — 논문 원문을 확인하지 않고 일반 지식으로 topology를 채움

2단 OTA 논문 재현에서 Stage 1(입력단)은 원문대로 정확히 재현했지만, Stage 2(출력단, ~12개
소자) 전체를 "일반적으로 2단 OTA 출력단은 이렇게 생겼다"는 지식으로 채웠다. 실제 원문
Fig.1의 소자 구성과 달랐다.

**틀린 이유**: 외부 논문의 회로는 일반형 지식으로 대체할 수 없다 — 일반형이 그 논문의 실제
구현과 다를 수 있다.

**규칙**: 원문 도면을 직접 읽고 소자별 `{name, kind, source, drain, gate, role}` 표
(`netlist.md` 등)로 먼저 옮긴 뒤, 이후 모든 판단은 그 표만 근거로 진행한다. 표에 없는
소자·연결은 만들어내지 않는다. 확실하지 않은 연결은 "⚠ 가정"으로 명시한다.

## 사고 3 — 리포트 시각화 코드를 재사용하지 않고 새로 만들거나 텍스트로 대체함

`report_template.html`에 검증된 `renderSchematic()`/`renderStack()` SVG 함수가 있는데도,
§5(stick diagram)를 `build_stick_diagram()`의 `rendered` 문자열 필드(터미널용 monospace
요약)를 그대로 `<pre>` 텍스트로 리포트에 넣었다. 같은 리포트의 §1(topology)도
`renderSchematic()`을 쓰지 않고 좌표를 손으로 박은 1회성 SVG로 새로 작성했다.

**틀린 이유**: 데이터를 계산하는 것과 그 데이터를 시각화하는 것은 별개의 두 단계이고, 둘
다 재사용 대상이다. `rendered` 필드는 그림이 아니라 텍스트 요약일 뿐이다.

**규칙**: `report_template.html`은 참고 예시가 아니라 재사용해야 하는 검증된 구현체다 —
파일을 복사해 시작점으로 삼고, `renderSchematic()`/`renderStack()` 본문은 한 줄도 새로
쓰지 않는다.

## 사고 4 — 소자가 gm/ID로 사이징 불가능할 때 이유를 "논문에 없다"로 잘못 짚음

CMFB/replica-bias 회로에 대해 논문이 명시적 gm/ID나 gm 목표치를 주지 않았다는 이유로 "이
서브블록은 gm/ID 사이징 범위 밖"이라 결론 냈다. 실제로는 이미 사이징된 메인 경로 소자를
그대로 복제하는 구조라 회로 내 기능적 역할만으로 로컬 타겟을 유도할 수 있었다. 같은 논리로
보상 소자(Cc/Rz)도 "범위 밖"으로 처리했지만, 이미 사이징된 gm값에 표준 pole-zero 공식
(R≈1/gm2 등, `gm-id-methodology.md` §6.4/§6.7/§10)을 적용하면 바로 계산되는 값이었다.

**틀린 이유**: "레퍼런스 자료에 이 값이 없다"는 "도출 불가능하다"의 증거가 아니다 —
실무에는 애초에 대조할 논문/정답이 없다.

**규칙**: 이 skill의 목적은 논문 재현이 아니라 임의의 topology+spec에 대해 모든 소자
(능동+수동)의 값을 확정하는 것이다. 값이 없다고 스킵하지 않는다 — 상세 절차는 SKILL.md
§1.5.

**재발(2026-07-30, `docs/04-report/analog-topology-json-library.do.md` 배치 7-3f)**:
캐스코드의 채널길이(L)를 이득식(§6.7 Phase 2)으로 역산하려면 단별 이득 배분(Av1/Av2)이
필요한데, 논문 Table I가 `Adm` 총 이득만 주고 단별 배분을 안 준다는 이유로 "이 역산은
이 논문에 없어서 배치 스코프 밖"이라고 초안에 적었다가 사용자 지적으로 정정했다 — 사고4와
글자 그대로 같은 실수(gm/ID 목표치 대신 이득 배분 목표치라는 점만 다름)다. **바로잡은
결론**: 단별 이득 배분은 원래 정답이 없는 트레이드오프 문제이므로, 논문에서 값을 찾을 게
아니라 총 이득 제약(`Av1_dB+Av2_dB ≥ Av_target`)을 만족하는 배분을 **탐색으로 도출**하면
된다 — 이미 있는 4-원칙 탐색(배치 7-3d)에 `L_cascode`/`L_stage2out`을 자유변수로, 총이득을
제약으로 추가해 흡수했다(별도 새 메커니즘을 만들 필요조차 없었다).

## 사고 5 — harness 함수 사이의 입출력이 실제로 맞물리는지 끝까지 확인하지 않음

`analog-topology-json-library.do.md` 배치 7 전체(7-1~7-5)를 "82개 함수 AST 호출 추적"으로
감사해 여러 gap을 찾아냈지만, 이 감사는 "함수가 존재하는가/호출되는가"만 봤지 **인접한
두 함수 사이에서 한쪽의 출력이 다른 쪽이 요구하는 입력과 실제로 맞는 타입·완전성으로
연결되는지**는 끝까지 추적하지 않았다. 그 결과, spec부터 instance.json까지 실제로 한
번도 손으로 끝까지 추적해보지 않은 채 "배치 7이 완성되면 harness만으로 완주 가능하다"고
암묵적으로 가정하고 있었다.

**틀린 이유**: 함수가 각자 존재하고 각자 잘 동작해도, 한 함수의 출력 스키마와 다음 함수가
기대하는 입력 스키마 사이에 사람만 채울 수 있는 간극이 있으면 전체 파이프라인은 여전히
harness만으로 안 끝난다 — "부품이 다 있다"와 "부품이 조립된다"는 다른 주장이다.

**실제로 드러난 사례(2026-07-31)**: 사용자가 "완전히 구현됐다고 가정하고 spec→instance.json
전체를 시나리오로 끝까지 추적해보라"고 요구해 실제 함수 시그니처를 코드로 재확인하며
따라가다가, `size_transistor()`(raw W만 반환) → `run_topology_pipeline()`(`n_fingers`/
`finger_w`/`stack_id`가 **이미 채워진** `sizing_overrides`를 필수로 요구) 사이에 이 둘을
잇는 함수가 **하나도 없다**는 게 드러났다. `split_into_stacks()`의 docstring조차 스스로
"stack_id 배정은 회로 지식이 필요한 판단이라 이 함수가 대신 결정하지 않는다"고 인정하고
있었다 — 이전의 어떤 리뷰·감사(§7.9의 12개 항목 검토, 다른 배치들의 "검증" 행 등)도 이
gap을 못 잡았다. 배치 7-5(최종 재생성)까지 계획해놓고도 이 연결이 실제로는 사람/AI가
손으로 메워야 했다는 뜻이다.

**규칙**: 이 skill의 함수 집합이 수정되거나 확장될 때마다, spec부터 instance.json까지
**실제 함수 호출로 처음부터 끝까지 한 번 추적**해 (a) 모든 단계가 harness/원소 함수만으로
연결되는지(사람이 메우는 지점이 없는지), (b) 같은 입력을 다시 넣으면 같은 결과가 재현되는지,
(c) 그 결과가 spec하에서 최선임이 보장되는지 확인한다 — SKILL.md 절대 원칙 5번 + §5
마지막 체크리스트 항목("skill 최종 게이트")이 이 규칙을 강제한다. 개별 함수의 존재·정확성
검증(사고1~4)만으로는 부족하다 — **연결부**를 끝까지 추적하는 것이 이 사고의 핵심 교훈이다.

## 사고 6 — 순수 수식 함수 self-test에 실제 회로의 소자 이름을 역할 검증 없이 씀

`telescopic_class_ab` CMRR 폐형식(`_cmrr_telescopic_class_ab`, 둘 다 Phase 2에서 삭제)의 self-test를 작성하며,
"이 함수는 gm/gds *값*만 받는 순수 수식 함수라 topology.json엔 애초에 그 값이 없다"는
이유로 `SizingContext(sized={"M1a": {gm,gds}, ...})`를 손으로 만들었다. 그런데 여기 쓴
소자 **이름**(M1a/M2a/M3a/M4a/M6/M7/M5)이 `current_reuse_telescopic_ota.topology.json`에
실제로 존재하는 이름이었고, 그 이름들이 "PMOS 입력/PMOS 캐스코드/NMOS 입력/NMOS 캐스코드/
tail"이라는 역할이라는 가정을 **논문 Figure를 읽은 기억만으로** 부여하고 실제 JSON으로
확인하지 않았다. 사용자가 지적해서 확인해보니 kind는 다행히 다 맞았지만, 캐스코드 접합
노드 이름을 설명할 때는 실제로 틀렸다("Vom1"이라고 말했지만 실제 노드명은 "N2a3a"였음 —
위상 자체는 맞았지만 설명이 틀렸다).

**틀린 이유**: "gm/gds 값 자체는 topology.json에 없으니 손으로 채워도 된다"는 예외가,
"그 값을 채우는 대상 소자 **이름**이 실제 존재하는 회로의 진짜 이름과 일치한다"는 사실까지
면제해주지 않는다. 값과 이름은 별개이고, 이름을 실제 회로에서 가져다 쓰는 순간 그 이름에
딸린 kind/connectivity 가정도 그 회로 기준으로 참이어야 한다.

**규칙**: self-test/함수가 실제 `library/*.topology.json`에 존재하는 특정 소자 이름(범용
placeholder가 아니라)을 참조하면, 그 이름에 대한 kind/connectivity 가정을 코드로 쓰기 전에
반드시 `load_topology(그 실제 파일)`을 호출해 (a) 각 역할에 배정한 소자의 `kind`가
가정과 일치하는지, (b) 역할 배정이 함의하는 connectivity 관계(같은 노드 공유, source=drain
연결 등)가 실제 `source`/`drain`/`gate` 필드로 성립하는지를 assert로 먼저 검증하는 블록을
넣는다. "수식 자체 검증"과 "역할 배정 검증"은 항상 별도의 두 블록으로 나눠 쓴다 — 실제
구현 예시: `sizing_recipe.py`의 `telescopic_class_ab` self-test(Phase 2에서 삭제, 2026-07-31, `_crt_by_name`
블록).

## 사고 7 — 공유 엔진 코드를 사전 승인 없이 고침 (원칙의 최초 근거)

세션7에서 `stick_diagram.py`/`sizing_recipe.py`처럼 여러 회로/여러 파일에 영향을 주는 공유
엔진 함수 로직을 사전 논의·승인 없이 고쳤다가, 즉시 원복 지시를 받았다(`.ai/context.md` 줄
742-743). 이 사건 자체의 상세 서사(무엇을 어떻게 고쳤는지)는 세션7 원문이 이후 요약 과정에서
소실돼 `.ai/context.md`에 지금은 이 한 줄 인용만 남아 있다 — 그 자체가 "세션 로그도 stale/불
완전해질 수 있다"는 별도 교훈이다(사고 8 B-5 참고, 같은 패턴이 세션14→23에서도 재발).

**틀린 이유**: `netlist`/`passive_elements`/`ideal_sources` 같은 connectivity나
`device_roles`/`symmetry.*`/`sizing_roles` 같은 역할·메타데이터는 Claude가 분석해서 바로
갱신해도 되는 영역이지만, 여러 회로가 공유하는 엔진 함수의 계산 로직은 한 번 바뀌면 그
순간 이 skill이 다루는 4개 토폴로지 전부의 사이징 결과가 동시에 바뀐다 — 되돌리기 비용이
개별 topology.json 필드 수정과 차원이 다르다.

**규칙**: `stick_diagram.py`/`sizing_recipe.py`의 함수 로직을 바꾸는 작업은 항상 설계를
먼저 논의하고 명시적 승인을 받은 뒤에만 코드를 고친다 — 이 원칙은 세션11(L3 엔진 D 구현
전 여러 턴 논의)부터 지금까지 일관되게 지켜지고 있다(Claude 메모리 `feedback_act_
decisively_within_analysis_authority.md`도 같은 경계를 별도로 기록).

## 사고 8 — `geometry_colocation_union()`의 무근거 자동병합이 "stack M6" 크래시를 유발

세션22 OAT(one-at-a-time) 민감도 스윕을 준비하던 중 baseline 자체가
`assign_finger_geometry()`에서 크래시했다: `stack 'M6'(구성원 ['M1a','M1b','M2a','M2b',
'M57','M58','M6','M7'])에 대해 어떤 finger_w 후보도 못 찾음`.

**근본원인**: `stack_groups_geometry`를 만드는 `geometry_colocation_union()`(세션10 신설)의
rule1("같은 극성 + non-rail + drain=source면 선언 여부 무관하게 자동 병합")이, `Vx`(stage-1
tail/diff-pair 공유 노드)에 `M58`(bias-gen 하우스키핑 소자, source=Vx)이 얹혀있다는 이유만
으로 전류 규모가 수십~수백 배 다른 `M57`/`M58`을 `M6`/`M7`/`M1a`/`M1b`/`M2a`/`M2b`와 **한
finger-공유 stack**으로 묶어 공통 finger_w를 못 찾았다. analog-grammar `analyze.py`로도
같은 결과가 재현돼("물리적으로 같은 노드에 물려있다"는 사실 자체는 맞음), 이 문제가
"물리적 사실"과 "기능적 판단"(bias-gen 하우스키핑 vs 신호경로)을 구분 못 하는 자동추론
공통 패턴임이 재확인됐다.

**해결**: `geometry_colocation_union()`을 "`matching_pairs`(선언된 것만)를 base union으로
쓰고, `find_stack_edges()`(analog-grammar)+`find_stacked_matching_candidates()`(세션19
C-3)로 base pair 위에 직렬로 얹힌 같은 kind 소자만 재귀적으로 union"하는 방식으로 재설계 —
무근거 rule1은 완전히 삭제. `M58`처럼 "같은 노드를 소스로 공유하는 형제(병렬 소비자)"는
알고리즘 구조 자체가 후보에서 배제한다(별도 예외처리 불필요). `folded_cascode`(무관한 다른
회로)의 기존 self-test 그룹이 손대지 않았는데도 그대로 통과해 회귀 없음을 확인.

**일반 원칙(사용자 확정)**: "matching_pairs가 base, 검증된 상속으로만 확장"이라는 방법론은
`geometry_colocation_union()`류(선언 없이 자동으로 물리적 병합 후보를 추측하는 함수)에
일반적으로 적용 가능하지만, `kcl_series_union()`류(전기적으로 강제되는 사실을 찾는 함수 —
"2단자 net이면 전류가 같다"는 KCL 그 자체)에는 해당하지 않는다 — 두 종류의 grouping 함수를
같은 원칙으로 섞어 고치지 말 것.

**부수 확정 — topology.json 누적 지식베이스 철학(사용자 원안, 일반 원칙)**: 이 사고를 계기로
"finger_w 호환"(`geometry_colocation_union()`)/"오일러 경로"(`kcl_series_union()`→
`stack_id`)/"매칭 대칭"(`matching_pairs`)이 서로 다른 union-find로 각자 판단되고 있다는
구조적 위험이 지적됐고, `vertical_stack_id`(물리적 직렬 branch 경계) 같은 **회로 자체의
불변 특성**은 instance마다 다시 계산하지 않고 topology.json에 누적 저장해야 한다는 방향으로
정리됐다(`resolve_stack_layout()` 3계층 orchestrator 설계, 세션26 I절에서 실제 구현). "topology.json은
구현 횟수가 늘수록 모든 instance에 공통 적용될 정보를 누적 보관해야 한다"는 이 철학이
`vertical_stack_id`/`device_roles`/`symmetry.*` 필드가 지금처럼 topology.json에 자리잡은
근거다.

## 사고 9 — `headroom_role` 선언이 구조적으로 동일한 소자쌍에서 반대로 선언된 사례 10건

세션25 F~G절에서 `device_roles.headroom_role`을 소자별로 점검하다가, **구조적으로 완전히
동일한 역할인데 한쪽만 정확하고 반대쪽이 다르게 선언된** 사례가 10개 소자에서 발견됐다:
`M10`/`M19`(`cascode`로 잘못 선언 — 실제론 `M8`/`M17`과 구조적으로 동일한 "바깥쪽" 위치라
`mirror`가 맞음), `M9a`/`M9b`/`M18a`/`M18b`(Monticelli floating current source 다리인데
`mirror`/gap으로 잘못 선언), `M37b`(진짜 CMFB 2차 차동쌍 다리인데 `tail`로 잘못 선언),
`M63`(`mirror`로 잘못 선언, 실제론 diode-cascode), `M39`/`M40`(`mirror`로 잘못 선언, 실제론
"미러링할 기준전류가 없는" 2-diode self-biased 분압기라 `cascode`가 맞음).

**틀린 이유**: `headroom_role`처럼 "물리적 배치 위치"를 뜻하는 role 필드는 사람이 한 번
선언해도, 그 소자와 구조적으로 대칭인 파트너가 다른 role을 받았다면 둘 중 하나는 틀렸을
가능성이 높다 — 그런데 이 비대칭이 정기적으로 재검증되지 않으면 한쪽만 고쳐지고 반대쪽은
방치된 채로 계속 오탐지된 값을 근거로 헤드룸이 배정된다.

**규칙**: `headroom_role`을 선언·수정할 때는 같은 idiom을 공유하는 구조적 파트너가 있는지
먼저 확인하고, 있으면 둘이 같은 role을 받는지(또는 정당하게 다르다면 그 이유가 무엇인지)를
항상 함께 검증한다.

**후속(2026-09, 세션44~45)**: 이 사고가 잡은 것은 "선언값 자체의 대칭성 오류"였지만, 이후
`headroom_role="diode_reference"`/`"cascode"` 자체의 **배정 공식**이 diode-connected 소자의
물리 제약(Vgs=Vds)을 전혀 모델링하지 않는다는 훨씬 근본적인 문제가 별도로 발견됐다(사고 10
참고, `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`) — "role 선언을 구조로
재검증할 것"이라는 이 사고의 원칙이 그 후속 조사에서도 그대로 적용됐다(선언은 맞았는데 그
선언을 소비하는 공식 자체가 틀렸던 경우).

## 사고 10 — `HeadroomPolicy.thin_roles`/`diode_reference` 신설 — "얇게 배정"이 diode-connected의 실제 필요 Vgs를 검증한 적이 없었다 ★

세션28 U절, M18_bg(diode-connected 기준전압 생성기, singleton) 헤드룸 크래시를 고치며
"diode-connected는 전부 cascode처럼 얇게 배정"이 아니라 **"이 소자가 예산을 나눠 가질
파트너/설계의도가 있는가"**가 진짜 구분 기준임을 확정했다(M39/M40=있음→`voltage_divider`,
M18_bg=없음→신규 `diode_reference`). `HeadroomPolicy.thin_roles={"cascode","diode_
reference"}`로 일반화하고 `_default_cascode_headroom()`(Jespers `2/gm_id+margin` 근사)을
공유하게 했다.

**틀린 이유(2026-09, 세션44~45에 뒤늦게 발견)**: 이 결정 자체가 "0.2V(min_vds 상수 또는
Jespers 근사)가 diode-connected 소자의 실제 필요 Vgs와 맞는지"는 한 번도 검증하지 않았다.
diode-connected 소자는 gate=drain이라 물리적으로 **Vgs=Vds가 강제**되는데, `2/gm_id+margin`
공식은 원래 "외부에서 게이트가 구동되는 진짜 캐스코드"(Vds가 Vdsat 근처만 넘으면 됨)를
위한 근사라 Vth가 통째로 빠진다. 게다가 실제 호출 경로(`sizing_recipe.py:5227` 부근
`stack_entries` 생성부)는 entry에 `gm_id`조차 안 넣어서 이 공식은 죽은 코드였고, 실제로는
그냥 `min_vds_by_role` 상수(미선언 시 0.2V 기본값)로 떨어지고 있었다.

**실측(세션45)**: `current_reuse_telescopic_ota`의 diode-connected 소자 16개 전부에서
`vgs_for_gm_id(gm_id,L,vds,vs)`(LUT 역산, 실제 sky130 특성)와 저장된 `vds` 사이 오차가
0.05V~1.02V(`M36a`/`M36b`가 최악: 필요 1.32V인데 할당 0.3V, 물리적으로 불가능)로 확인됐다.
sky130 트랜지스터 레벨 SPICE로 51소자 전체 폐루프 `.op`을 돌려보니, 이 어긋남이 바이어스
체인 전체를 설계 의도와 다른 값으로 밀어붙여 출력단이 VDD 레일에 고정(rail-lock)되는
결과로 직접 이어졌다(CMFB를 열어도 동일 재현 — CMFB 부호 문제가 아니라 바이어스 체인 자체의
문제로 확정).

**규칙/후속**: "얇게 배정"이라는 정책 자체는 진짜 캐스코드에는 맞지만, diode-connected
소자(gate==drain, connectivity로 판정 가능 — role 라벨을 신뢰하지 않는다)에는 Vgs=Vds
자기일관점을 직접 푸는 별도 해석기가 필요하다는 게 이번 재조사의 결론이다. 이 문제는 더 나아가
"VDS(헤드룸)가 gm_id보다 먼저, role 기반 상수로 확정되는 파이프라인 순서 자체"가 근본 원인
임이 드러나 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(gain-budget-first 근본
재설계, §3 헤드룸 해석기 재설계)의 직접 계기가 됐다 — 새 파이프라인은 gm_id를 먼저 정하고
헤드룸을 그 이후에 자기일관되게 해석하도록 순서 자체를 뒤집는다. 사고 19도 같은 클래스("헤드룸이
다른 메커니즘에 의해 조용히 먼저 확정된다")의 이전 사례이니 함께 참고할 것.

## 사고 11 — `check_euler_condition()`이 소자 kind(PMOS/NMOS)를 전혀 안 본다

세션28 후반부(N~O절), `resolve_stack_layout()`이 6개 vsid 병합 그룹 전부 "실제 오일러 게이트
통과"로 확인돼 "레이아웃 재설계 불필요"로 결론냈으나, 사용자가 "pmos/nmos가 같은 stack인데
오일러 패스에 문제가 없는 게 이상하지 않냐"고 질문해 뒤집혔다.

**근본원인**: `build_graph()`/`check_euler_condition()`이 순수 net-connectivity 그래프
알고리즘이라 `t.kind`(pmos/nmos)를 전혀 참조하지 않는다 — 무방향 그래프라 PMOS/NMOS를
섞어도 수학적으로 차이가 없다. `vertical_stack_id`(전기적으로 VDD~GND 한 컬럼이면 kind가
섞이는 게 정상, 예: class-AB output_stage_a의 M15(pmos)+M16(nmos))를 그대로 물리 레이아웃
행으로 취급하면, PMOS와 NMOS를 같은 물리적 행에 놓으라는 잘못된 결과가 나온다. 실측:
declared vsid 26개 중 8개가 kind-mixed였고, `vbias2_stack`의 hierholzer 결과가 `M57`(PMOS)과
`M68`(NMOS)이 diffusion을 공유하며 바로 이어붙는 물리적으로 불가능한 trail을 "path"(정상)로
확정하고 있었다.

**해결**: 두 개념을 명시적으로 분리 — (a) `build_graph()`에 kind 동질성 하드 게이트 신설
(다른 kind는 애초에 같은 그래프에 안 넣음). (b) `derive_horizontal_stack_groups()` 신설 —
`vertical_stack_id`(전기적) 그룹을 kind로 먼저 쪼갠 뒤 `merge_layout_groups_by_matching_
pairs()`(재발명 안 함)로 declared `matching_pairs` 기준 대칭 branch를 재병합해 **물리
레이아웃 행**을 만든다.

**교훈(일반화)**: "게이트를 통과했다"는 관찰이 실제로는 "게이트가 그 조건을 볼 수 없어서 그냥
통과한 것"일 수 있다 — 검증 함수가 실제로 무엇을 체크하는지(무엇을 체크 **안** 하는지)를
코드로 직접 확인하지 않은 채 "통과했다"를 결론의 근거로 삼지 말 것. `vertical_stack_id`
(전기적, KVL 헤드룸 축)와 물리 레이아웃 행(오일러 패스/대칭 배치 축)은 "같은 축의 다른
표현"이 아니라 **항상 별도로 파생해야 하는 서로 다른 두 축**이다.

## 사고 12 — `suggest_pair_finger_adjustments()`의 `pair_map` 덮어쓰기로 N-way 매칭 그룹의 특정 쌍이 조용히 사라짐

세션26 L-3~L-4, 3-way declared 그룹(`M18_bg`/`M60`/`M61`)을 `itertools.combinations()`로
3개 쌍으로 풀어 함수에 넘기는데, 옛 구현이 `pair_map: name->partner` 단일 매핑(1:1 체인
가정)으로 짜여 있어 나중 쌍이 앞 쌍의 매핑을 덮어써 `(M18_bg,M60)` 관계 자체가 소실됐다 —
실제로 유효한 해법이었는데도 시도조차 되지 않았다.

**규칙**: "1:1 아닌 매칭쌍은 무시"가 문서화된 의도된 제한인 함수(`mirror_symmetric_trail()`)
와, 문서화 안 된 채 실제로는 N-way 그룹을 받고 있던 함수(`suggest_pair_finger_
adjustments()`)를 구분해야 한다 — 같은 "쌍 단위 처리" 코드 패턴이라도 실제로 받는 입력의
계약이 다르면 버그 여부가 갈린다. "선언된 쌍마다 독립적인 조정 단위"로 재작성해 해결.

## 사고 13 — theta 선언 순서 = 실행 순서라는 암묵 계약이 깨져 stale 값을 참조

세션31 BM절, `K_replica`(M9a가 M15를 참조하는 replica feed)가 topology.json theta 배열에서
M15의 최종 gm_id/L을 정하는 `L_stage2out_p`보다 **앞에** 선언돼 있어, M9a가 compensation의
잠정 초기값(stale)을 복제하고 있었다. 처음엔 "기존부터 있던 특성"으로 넘어가려 했으나
사용자가 "stale함은 특성이 아니고 고쳐야 할 부분 아닌가?"로 정정을 요구해 실제 버그로
재분류됐다.

**해결**: theta 배열 순서를 이동해 `K_replica`가 `L_stage2out_p` 뒤에 오도록 수정 +
`validate_theta_declaration_order()`(참조 소자가 선언 순서상 앞서는지 확인하는 정적 검사기)
신설로 회귀방지.

**교훈**: "원래 그랬다"/"기존 특성"이라는 판단은 그 자체로 근본원인 조사를 회피하는 이유가
될 수 없다 — theta 배열처럼 "선언 순서=처리 순서"인 암묵 계약이 있는 구조는, 새 theta를
추가할 때마다 그 계약이 실제로 지켜지는지 확인할 것.

## 사고 14 — `_finalize()`가 재계산한 `ID`를 `.update()` dict에서 빠뜨려 하류가 stale 값을 읽음

세션31 BO~BP절, `gm`은 새 값(`I_new` 기준)으로 정확히 재계산되는데, `ctx.sized[name]["ID"]`는
`_finalize()`의 `.update({...})` dict에 `"ID"` 키 자체가 없어서 이전 compensation 값이
그대로 남았다. 여러 디버그 스크립트가 `entry["ID"]`를 직접 읽어 "ID가 안 바뀌었다"고 오판하며
수 시간의 잘못된 조사(사후 `ctx.derived` 스냅샷 검사만으로 실행 도중 분기를 증명하려 한 것
자체가 근본 허점)로 이어졌다. 하류의 `_feed_diode_stack_target()` 등도 잘못된 전류로 연쇄
사이징되는 실제 파급이 있었다.

**규칙**: 사후 `ctx.derived`/`ctx.sized` 스냅샷 검사만으로는 실행 중 분기를 증명하지 못한다 —
의심되면 실제 코드 지점에 임시 print를 삽입해 런타임 값을 실측할 것(Claude 메모리
`feedback_no_assumption_without_evidence.md`의 구체 사례). `.update()`류 dict 갱신부를
새로 쓰거나 고칠 때는 "계산한 모든 필드가 저장 목록에 실제로 들어있는가"를 계산 로직과 나란히
재확인하는 습관을 들일 것 — 계산은 맞는데 저장 목록만 누락되는 조용한 전파 버그는 증상이
"값이 하나도 안 바뀐다"처럼 보여서 다른 원인(로직 자체가 안 도는가?)으로 오인하기 쉽다.

## 사고 15 — `vertical_stack_id`(헤드룸 축)와 `stack_groups_override`(레이아웃 행 축)를 혼동

세션31 BY절, 두 가지 "그럴듯한 서사"가 실측으로 반증됐다: (1) "M7의 L을 못 키운 게 매칭
때문"이라 추정했으나 실측하니 매칭과 무관(M7은 매칭 파트너가 없는 단독 소자, 진짜 원인은 toy
LUT의 성긴 L 격자). (2) `vertical_stack_id`(헤드룸 예산 축)만 보고 "M5/M7은 물리적으로
무관하니 L을 분리해도 된다"고 결론냈으나, `stack_groups_override`(실제 레이아웃 행 그룹핑
축, self-test에 이미 `"M5":["M5","M7"]`로 선언돼 있었음)를 확인하지 않아 틀렸다 — 사용자가
"physical_stack_id는 어떻지?"로 유도해 드러났다.

**근본원인/규칙**: 이 프로젝트엔 "물리적 그룹"을 나타내는 필드가 **둘** 있다 —
`vertical_stack_id`(헤드룸 예산 축, KVL)와 `stack_groups_override`/`derive_stack_groups()`
(실제 레이아웃 행 축, 오일러 패스/interdigitation). "왜 이 값이 이렇게 나왔는가"는 반드시
실제 코드 경로를 추적해 확인하고, 그럴듯한 서사로 대체하지 말 것 — 물리적 배치를 판단할 땐
둘 다 확인해야 한다(사고 11의 "전기적 축 vs 물리 레이아웃 축" 구분과 같은 계열의 재발).

## 사고 16 — 행 이름 카운터가 호출 전역에서 유일하지 않아 무관한 반복끼리 이름이 충돌 → 소자가 조용히 삭제됨

세션32 F절, `current_reuse_telescopic_ota`(51소자) 실행 결과 `instance.json`의 `netlist`가
48개뿐이었다(M17/M18_bg/M61 누락). `run_full_circuit_audit.ok`(선언 대조라 이 누락을 못
잡음)와 `coverage.ok`(repair *이전* 시점 계산이라 못 잡음) 둘 다 이 손실을 통과시켰다. 처음엔
Euler-blocked 문제(7-way current-mirror 그룹이라 한붓그리기 불가능)로 오판했으나, blocked
row를 실제로 재현해보니 `status='ok'`였다(가설이 실측으로 반증됨).

**근본원인**: `_layout_result_to_rows(layout, templates, base_row_name)`가 새 행 이름을
`f"{base_row_name}_repair{i}"`(`i`는 **그 호출 안에서만** 0부터 시작, 호출 전체에 걸쳐
전역적으로 유일하지 않음)로 지었다. 허브 소자(M18_bg)가 매번 새 파트너와 재배치되며
`"biasgen_ref_seg1_repair0_repair0"` 같은 이름이 남는데, 나중에 **완전히 무관한 다른 쌍**을
처리하며 우연히 같은 이름이 다시 생성되면 `current_rows.update(new_rows)`가 그 남은 소자를
조용히 덮어써 삭제했다.

**해결**: `existing_rows` 파라미터 추가 + `reserved` set으로 이미 쓰인 이름을 피해가며 카운터
증가(`while new_row_name in reserved: i+=1`) — 두 호출부(개별-pair, branch-composite) 둘 다
필터/삭제를 먼저 끝내고 그 이후의 `current_rows`를 `existing_rows=`로 넘긴 뒤 호출하도록
순서 변경.

**교훈(가장 중요한 부분)**: 이 버그를 실제로 잡아낸 건 **직전에 독립적으로 추가된
`check_stick_diagram_coverage()`의 repair-이후 재검증 게이트**였다 — Claude 메모리
`feedback_build_it_wire_it_or_ask.md`(★절대원칙★ "만들면 반드시 배선")를 지켜 이 게이트를
실제로 배선해뒀기 때문에 소자 유실이 조용히 묻히지 않고 드러났다. 여러 반복(loop)에 걸쳐
이름/ID를 새로 짓는 함수는 카운터가 호출-지역적인지 전역적인지 항상 명시적으로 확인할 것 —
지역 카운터가 여러 호출에 걸쳐 우연히 충돌하면 `dict.update()`가 이전 값을 조용히 삭제한다.

## 사고 17 — 다른 회로로 교차검증하면 회귀가 아니라 원래부터 있던 선언 누락이 드러난다

세션31 BV~BW절, 신규 메커니즘(`vertical_stack_id` gap-fill) 검증차 라이브러리 4개 회로를
전부 실행해보니 `two_stage_ota`가 `resolve_stack_layout()`에서 크래시했다 — `M3/M1`,
`M4/M2`, `M6/M7` 세 쌍이 KCL로는 직렬인데 `vertical_stack_id`가 한쪽만 선언돼 있었다.

**근본원인**: 이건 그 세션의 회귀가 아니라 세션22~25부터 있던 선언 누락(이전 커밋 기준으로도
동일하게 재현 확인됨) — 단지 `two_stage_ota`가 그때까지 제대로 실행된 적이 없어 안 드러났을
뿐이다. `_kcl_and_matching_edges()`(edge 재구성 로직 단일 정의) + `propose_vertical_stack_
id_gap_fill()`(내부 2단자 net + `current_forced` matching_pairs만 묶음, **`declared_
matching_pair`(미러쌍) 갭은 의도적으로 제외** — 미러 출력이 회로 반대편에 있는 게 흔해
"같은 헤드룸 컬럼" 보장이 없음)로 자동 gap-fill을 `load_topology()`에 배선.

**규칙**: 새 엔진 메커니즘을 만들면 그 메커니즘을 처음 촉발한 회로 하나로만 검증하지 말고
라이브러리의 **다른 모든 회로**로도 실제 실행까지 해볼 것 — self-test의 정적 검증 통과만으로는
"이 회로에서 우연히 한 번도 노출 안 된 기존 gap"을 잡을 수 없다.

## 사고 18 — 대칭 구조는 "복사"가 아니라 "연결에서 유도되는 사실"이어야 한다

세션42 최종완료 §7-0, `biasgen_vop_a`(M17+M18a)의 KVL 검증에서 39mV 불일치가 발견됐다:
M17.vds(0.939V, netlist로 검증된 정확값) + M18a.vds(0.9V, "M9a의 완전한 replica"라는
세션6부터의 설계 가정) = 1.839V ≠ vdd(1.8V).

**근본원인**: M17→M25 관계는 실제 connectivity(M17.drain=Vg25=M25.gate, 둘 다 source=vdd)
에서 대수적으로 강제되는 사실인 반면, M9a→M18a "vds까지 통째로 replica"는 검증 없이 가정된
설계였다. 완전 대칭인 Vom측(M9a/M9b/M10)엔 `budget_reference_device`/`vds_match_vgs_of`
선언이 있었지만, 대칭인 Vop측(M18a/M18b/M19)엔 그 선언 3개가 통째로 누락돼 있었다.

**해결**: "복사" 대신 `propose_device_roles_gap_fill()`에 두 신규 자동탐지 소스 추가 —
`budget_reference_device` 자동탐지(공유 net의 유일한 외부 단자가 정확히 1개 소자의 drain일
때만), `fold_group` 자동탐지(반대 kind가 drain을 공유할 때). 두 규칙 다 "공유 net을 정확히
2개 소자만 터치해야 자동판정, 3개 이상이면 review_needed"라는 일반 위상수학적 원칙으로
확정 — 구현 중 4-way 합류 오판/평행소자를 직렬로 오판/상호참조 순환 3종 오탐을 실측으로 잡아
규칙을 좁혔다.

**교훈**: "논문/이전 설계가 A와 B를 같은 값으로 정했다"는 서술을 볼 때, 그게 connectivity로
강제되는 대수적 사실인지 검증 안 된 가정인지 먼저 구분할 것 — 대칭이라고 해서 값까지 같아야
한다는 보장은 없다.

## 사고 19 — theta feed의 role 폴백이 헤드룸 KVL 계산을 조용히 무력화 — 상호참조는 근본적으로 underdetermined ★

세션43(계속)~(계속2), `L_cascode` theta가 처리되는 시점에 M2a/M3a는 아직 값이 없어
`resolve_feed_vds()`가 role 폴백(`headroom_role="cascode"` → 0.2V)으로 조용히 확정됐다 —
그 결과 나중에 헤드룸 루프가 "이미 vds가 있다"고 보고 `budget_reference_device` 상호참조
KVL 계산(M2a↔M3a)을 아예 실행하지 않았다(죽은 코드).

**시도했다가 실패한 것**: `resolve_feed_vds()`가 `(vds, source)`를 반환하도록 확장해 role
폴백값을 "미확정"으로 재분류하는 수정을 시도했으나, `_referenced_singleton` 분기가 애초에
`budget_reference_device`의 leftover 계산을 안 타서 값 자체는 안 바뀌었다(A측은 착시적
통과, B측은 진짜 순환 데드락으로 악화) — 전부 되돌렸다.

**근본원인(대수적으로 확정)**: `M2x.vds + M3x.vds = 상수` 방정식 하나에 미지수가 둘이라
**상호참조 자체가 근본적으로 underdetermined**임을 직접 대입으로 증명했다(두 leftover 공식을
서로 대입하면 항등식 `b=b`만 나옴 — 독립방정식이 아니다).

**해결**: `budget_reference_device` 상호참조 대신, 물리적으로 하나의 vdd~gnd branch
(M6-M1a-M2a-M3a-M4a-M5)를 **하나의 vertical_stack_id로 병합**. `allocate_stack_headroom()`이
이미 "thin role은 각자 최소치, 나머지는 남는 예산 균등분배"를 하므로 이게 바로 필요했던
"정확히 반씩 나눈다"는 규칙 그 자체였다 — 새 코드 없이 topology.json 재구성만으로 diff=0.0V
KVL 달성, 4개 회로 전체 byte-diff 0(회귀 없음).

**부수 발견(중요)**: 옛 `gain_db≈76.48dB` 베이스라인이 이번에 새로 강제된 KVL 제약 이전,
즉 **물리적으로 불가능한 헤드룸 조합 위에서 SLSQP가 도달한 값이었을 가능성**이 드러났다(KVL을
실제로 강제하니 달성 가능한 gain이 ~52dB로 크게 낮아짐) — "정직한 실패가 거짓 성공보다
낫다"는 이 프로젝트 원칙의 구체적 실증 사례.

**예방/후속(2026-09, 세션44~45)**: 소자의 VDS/헤드룸을 두 개 이상의 서로 다른 메커니즘
(theta feed의 role 폴백, headroom 루프의 KVL 계산)이 각자 독립적으로 건드릴 수 있는
구조라면, 어느 한쪽이 "이미 확정됨"으로 오판해 다른 쪽을 죽은 코드로 만들 위험이 있다 —
상호참조로 풀릴 것 같은 두 미지수 관계는 먼저 "이게 정말 독립방정식 두 개인가, 아니면
대수적으로 자유도가 부족한가"를 손으로 검산할 것. 사고 10(diode-connected 헤드룸이 gm_id보다
먼저 role 상수로 확정되는 문제)이 정확히 같은 클래스("헤드룸이 다른 메커니즘에 의해 조용히
먼저 확정된다")의 후속 사례이며, `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`가
"VDS를 gm_id **이후**에만 확정한다"는 순서 자체의 재설계로 이 클래스 전체를 근본 해소하려는
시도다.

## 사고 20 — 자동 KCL/theta 제안 알고리즘의 3가지 함정(diode-mirror 누락/일괄승격/3-way hub 오판정)

`propose_theta_kcl_gap_fill()` 초안에서 세 가지 독립된 버그가 발견됐다: (a) `folded_cascode`
의 diode `MP`를 declared matching_pairs에 없는 게이트-미러 파트너(`M3`/`M4`)와 단절된 고아
자유변수로 방치, (b) 교착 시 레일 인접 소자를 한꺼번에 자유 root로 승격시켜 실제로는 KCL로
풀렸어야 할 `M104`/`M202`류를 조기 확정, (c) `m_cascode()`가 3-way hub 노드(X: M1/M3/M6)를
2소자 캐스코드로 오판정해 `M3→M6 ratio=1.0`을 적용한 결과 `I(M1)=0`이라는 물리적으로 틀린
값을 산출.

**근본원인**: (a) declared matching_pairs 우선 규칙과 게이트-전용 미러 관계
(`idioms.m_mirror()`) 인식 규칙이 애초에 없었다. (b) 승격을 배치로 처리해 서로 다른
우선순위의 자유도가 동시에 확정됐다. (c) `mid` net의 사용자 수를 확인하지 않고 인접한 두
소자만 보고 캐스코드로 단정했다.

**해결**: declared mirror/gate mirror 규칙 추가, "한 번에 하나씩" 승격으로 전환, `mid` net
사용자 수가 정확히 2일 때만 캐스코드 규칙 적용. "마지막 검증 패스"(bounds 중앙값 재평가로
전류 0/음수를 자동 검출)도 신설.

**교훈**: connectivity 기반 자동 제안 알고리즘을 새로 짤 때는 반드시 (1) 3-way 이상 hub
노드를 2-way로 오인하지 않는 net-user-count 체크, (2) 자유도 승격은 배치가 아니라 단계적으로,
(3) declared 관계(matching_pairs/mirror)를 구조 추론보다 항상 먼저 확인할 것.

## 사고 21 — compensation이 정한 gm의 게이트를 구동하는 load가 KVL로 그 값과 결합돼 있는데, 서로 독립적으로 확정됐다 — "DC bias vs AC amplification" 도메인 분리 원칙 ★★

세션38(2026-08-19), `M301.gate=M204.drain`(둘 다 `source=vss` 공유)이라 물리적으로
`VGS(M301)=VDS(M204)`가 KVL로 강제되는데, `M301`(compensation이 GBW/PM 스펙에서 실제로
유도한 gm3 값의 소자)과 `M204`(헤드룸 루프가 독립적으로 정한 vds)가 서로의 값을 전혀 확인하지
않고 있었다 — 실측 `lut.vgs_for_gm_id(gm_id=24.0, L=2.45e-7, vds=1.65, vs=0)=0.536V`인데
당시 `M204.vds=1.0V`로 **0.464V 어긋남**.

**왜 M301의 gm을 바꾸는 게 답이 아닌가**: `Rm=1/gm3`(RHP-zero 완전제거 조건)이 이 gm3 값
자체로 보상망(Cm1/Cm2/Rm)을 설계하므로, M301의 실제 gm이 물러서면 그 설계 근거가 깨진다 —
맞춰야 할 건 M301이 아니라 M204의 vds(다른 load와 나누는 헤드룸 배분)다.

**해결**: `device_roles`에 `vds_match_vgs_of`(참조 소자의 VGS를 그대로 이 소자의 VDS로) 신설
— 헤드룸 루프에 pre-pass로 `target_vgs=ref_lut.vgs_for_gm_id(ref.gm_id, ref.L, ref.vds,
ref.vs)`를 구해 `ctx.sized[m]["vds"]`에 직접 기입한 뒤, 그 다음은 기존 by_vgrp 코드가
"이미 풀린 소자"로 자연스럽게 처리(새 분기 불필요). `gm_id_match_vgs_of`(device_roles 레벨,
같은 세션 전반부 신설, VGS를 공유해야 하는데 서로 다른 gm_id_role을 쓰던 M203/M204 케이스에
적용)와 같은 이름 컨벤션의 자매 필드 — 둘 다 "이 소자의 물리량은 참조 소자의 물리량과
KVL/KCL로 강제 동일하다"는 선언을 상호배타 필드로 표현한다.

**사용자가 대화로 발견을 일반화**: "M109/M201도 같은 문제", "M4/M6도"로 확장 지시 →
`compensation.stage_devices` 소속 소자의 gate가 내부 노드에 물린 모든 경우를 감사했다.
방향 판정 기준을 한 번 잘못 세웠다가(태그 소속 여부로 "M4도 authoritative, M6도
authoritative → 방향 불명확") 사용자가 정정: **`compensation.stage_devices` 배열의
신호경로 순서**(앞 stage=load, 뒷 stage=gm)가 방향을 정하는 진짜 기준이다 — 태그만으로는
"진짜 스펙에서 유도된 값"과 "그냥 theta feed 안에 하드코딩된 추정 상수"를 구분 못 한다(M4의
`vds=0.2`는 후자였음). M109→M201/M4→M6 2건도 같은 메커니즘으로 해소, M4/M6 적용만으로
`two_stage_ota`의 `gain_db`가 57.55→62.79dB로 개선됐다(별도 자유도를 안 늘리고 기존 KVL
버그만 고쳤는데도).

**최종 종합 원칙(사용자 정식화)**: "AC signal은 input이 root, bias망의 시작점은 DC 전압이다.
DC bias 최적화를 먼저 하고 AC gain 타겟을 그 위에서 맞춰야 한다." **DC 도메인**(root=rail+
외부 고정 전류원, 도구=headroom/`same_as_device`/`budget_reference_device`/
`vds_match_vgs_of`)과 **AC 도메인**(root=differential input, 도구=compensation/
`gm_id_role`)은 물리적으로 결합돼 있지만(DC 헤드룸이 부족하면 AC 스윙/이득이 꺾인다)
개념적으로는 별개의 최적화 문제 — 이 프로젝트 엔진이 지금까지 이 둘을 서로 확인 없이 독립적으로
풀어온 것 자체가 이번에 찾은 모든 gap(M301/M204, M109/M201, M4/M6, Monticelli 체인)의 공통
근본원인이었다. Phase 1(DC 그래프를 완전히 정합되게 먼저 풀기) → Phase 2(Phase 1이 남긴 진짜
자유도만 AC 타겟에 맞춰 탐색)로 엔진을 재구성하자는 게 세션38이 남긴 합의된 방향(설계만,
당시 미구현).

**★ 2026-09 세션44~45와의 관계**: 오늘 발견한 diode-connected 헤드룸 버그(사고10) 및 진행 중인
`gain-budget-gmid-sizing` 재설계(`docs/01-plan/features/gain-budget-gmid-sizing.plan.md`)는
바로 이 "DC/AC 도메인 분리" 원칙을 완성하는 작업이다 — 이 계획의 "VDS를 gm_id 확정 **이후**에만
푼다"는 새 파이프라인 순서는, 사실상 세션38이 설계만 하고 못 끝낸 Phase 1/Phase 2 아키텍처의
실제 구현에 해당한다. 재설계 시 이 사고 항목의 "신호경로 순서로 방향 판정" 원칙과 `vds_match_
vgs_of`/`gm_id_match_vgs_of` 두 primitive를 재사용/일반화할 것.

## 사고 22 — 그룹 단위 단일패스 헤드룸 정렬은 두 그룹이 서로 다른 멤버를 통해 맞물리는 상호참조(Monticelli)를 못 푼다 — fixed-point worklist로 일반화

세션39, `current_reuse_telescopic_ota`의 Monticelli floating battery(M8/M9a/M9b/M10)를 손으로
KVL을 끝까지 풀어보니, "자동 N-hop 그래프 엔진"까지 새로 만들 필요 없이 **기존 primitive
(`vds_match_vgs_of`/`budget_reference_device`)가 이미 정확한 답을 주는데, 그룹 단위 단일패스
정렬(`_ref_depth()`)이 두 그룹(`biasgen_vom_a`가 `biasgen_vom_floatsrc_sink`의 M10을, 그
반대 그룹이 `biasgen_vom_a`의 M8을 각각 참조하는 상호참조)을 순환 참조로 오판**함이 드러났다.
실제로는 "M10 pre-pass(M16만 있으면 즉시) → grpA 완결(M10 참조) → grpB 나머지 완결(grpA의
M8 참조)" 순서의 선형 해가 있었다.

**해결**: 그룹 처리 로직 전체를 `_resolve_vertical_group(vsid)` 함수로 뽑은 뒤, 기존 3곳의
즉시 `ValueError`(vds_match_vgs_of pre-pass/same_as_device/budget_reference_device 미확정)를
새 내부 전용 예외 `_HeadroomDependencyNotReady`로 바꿔 "지금은 준비 안 됐지만 나중에 될 수
있다"는 신호로 쓰고, "지금 풀 수 있는 그룹부터" 여러 pass에 걸쳐 재시도하는 fixed-point
worklist로 교체했다.

**자체 발견한 2차 버그(진전 판정 기준)**: worklist 1차 구현("이번 pass에 완결된 그룹이
0개면 실패")을 손으로 시뮬레이션하다가, grpA가 grpB보다 먼저 시도되면 grpA는 실패하고
grpB는 pre-pass로 M10을 채우지만(진전!) grpB 자신도 grpA의 M8을 기다리느라 "이번 pass 완결
그룹 0개"로 잘못 종료되는 경우를 발견 — "그룹 완결 수"가 아니라 **"ctx.sized에 vds가 채워진
소자 수가 이번 pass 동안 늘었는가"**로 진전 판정을 바꿔 해결.

**교차검증**: 실제 적용 후 `M10.vds`(새로 계산된 0.87578130502...V)가 **전체회로 MNA로
독립 계산되는 `vop1_level_v` metric과 소수점 끝까지 정확히 일치**함을 확인 — 손 유도가 실제로
물리적으로 정확했다는 강한 증거(이전엔 0.9V로 0.024V 어긋나 있었다).

**교훈**: 여러 그룹이 서로 다른 멤버를 통해 맞물리는(상호참조) 의존관계는 "그룹당 재귀 깊이
하나"짜리 위상정렬로는 못 푼다 — 새 계산 로직을 발명하기 전에, 먼저 "기존 primitive로
스케줄링 순서만 고치면 풀리는가"부터 손 시뮬레이션으로 확인할 것(이번엔 실제로 새 계산 로직이
전혀 필요 없었다).

## 사고 23 — 일반화된 theta feed 핸들러의 `vds=feed_spec.get("vds", 0.6)` 하드코딩이 진짜 VDD-GND 2소자 컬럼(output_stage_a)의 KVL을 검증 없이 깼다 — 사고19와 같은 근본 클래스 ★★★

세션40, `current_reuse_telescopic_ota`의 class-AB 출력단(M15/M16, `output_stage_a`)에 대해
"정성적 설계원리에 비춰 개선 여지가 있나?"라는 사용자 질문을 파고들다가, `sizing_roles.theta`
전체에 M15/M16의 ID를 직접 제어하는 theta가 없는데도 `f_slew`를 스윕해도 `M15/M16.vds`가
**항상 정확히 0.6**으로 고정돼 있는 걸 발견했다. 근본원인: `_feed_metric_stage_budget()`
(`sizing_recipe.py` 3255행)의 `vds = feed_spec.get("vds", 0.6)`가 `_metric_stage_budget_
finalize()`를 통해 M15/M16 **각자에게 독립적으로** `ctx.sized[name]["vds"]`에 직접
기록된다(theta feed는 헤드룸 루프보다 **먼저** 실행됨). `output_stage_a`는 진짜 VDD-GND
2소자 컬럼이라 `VDS(M15)+VDS(M16)=vdd`가 KVL로 강제돼야 하는데 `0.6+0.6=1.2≠1.8V`로
**처음부터 어긋나 있었다.** 헤드룸 루프가 나중에 이 그룹을 처리할 때 두 멤버 다 이미
`vds`가 있는 걸 보고 "이미 풀린 그룹"으로 판단해(합이 vdd와 같은지는 검사 안 함) 조용히
넘어갔다 — 이 세션이 M8/M17/M19에 적용한 `vds_match_vgs_of` 체인 전부, 그리고 그걸 기반으로
한 block-coordinate 탐색 전부가 이 잘못된 `M15.vds=0.6` 위에서 계산된 것이었다는 뜻.

**부수 발견(SLSQP block-coordinate descent 버그 5개, 같은 세션)**: L을 gain_db 목표로
탐색하는 `_optimize_theta_slsqp_block_coordinate()`(6-var SLSQP ↔ L joint-scan 교대) 구현
중 (1) `l_ref` 갱신 누락으로 교대가 한 번도 안 일어남, (2) `l_ref` 갱신이 "수렴 시 break"
검사 **뒤**에 있어 가장 좋은 라운드 결과가 최종 라운드에 전달 안 됨(순서 교체로 해결), (3)
coarse-to-fine 스케줄 신설(사용자 요청 "시간 단축"), (4) 좋은 지점(gain_db=69.4 근방) 주변
격자는 전부 크래시하고 격자 하한만 살아남는 **좁고 끊긴 feasible 조각**이 있어 전체범위
격자스캔이 구조적으로 못 찾음 → `window_around_reference` 신설(SLSQP 연속탐색만 찾을 수
있는 영역), (5) windowed 재탐색이 너무 얇은 VDS를 골라 n_starts=1 fast round가 통째로
크래시하는 경계 케이스 → presolve x0을 미리 평가해 안전망으로 등록.

**교훈**: "여유가 있다"와 "VDS 값 자체가 물리적으로 무의미하다(0.01V, 사실상 triode)"는
다른 문제다(사용자가 "vds여유가 0.01이라는 것이 vds가 0.01V라는 거야?"로 표현을 정정 요구한
경위 참고) — 격자 해상도를 넓히는 게 근본 해법이 아니라 그 동작점 자체가 무의미한지부터
확인할 것. 그리고 이 사고의 핵심 교훈: **"일반화된 함수의 물리적 의미 있는 기본값
(전압/전류/L/gm_id)은 그 값이 실제로 쓰이는 소자가 KVL/KCL 그룹에 속하는지 확인 없이는
안전하지 않다"** — 사고19(diode-connected 헤드룸이 gm_id보다 먼저 role 상수로 확정)와 정확히
같은 근본 클래스다.

## 사고 24 — 하드코딩된 `vds=0.6`이 4곳에 복붙돼 있었다 — "복사 대신 단일 우선순위 함수" 원칙, `resolve_feed_vds()` 신설 ★★★★

세션41, 사고23이 최우선으로 남긴 "일반화된 함수의 하드코딩 기본값 전수조사"를 실행했다.
`_THETA_FEED_REGISTRY`(7개)/`_METRICS_REGISTRY`(14개) 등록 핸들러 전체에서
`\.get\("(vds|vgs|vs|gm_id|L|W|ID|gm|gds|vdd|id)"\s*,\s*[0-9]` 패턴을 전수 grep한 결과,
**같은 `vds=0.6` 하드코딩의 4개 서로 다른 사본**을 찾았다:
1. `_feed_metric_stage_budget()`(사고23의 원 발견).
2. `_feed_gm_target_convention()`(타입 B) — `current_reuse_telescopic_ota`의 `N_cmfb_bw`
   feed(target=M37a)가 실제로 이 0.6 기본값을 쓰고 있었다. topology.json 자체 주석(M38 항목)이
   이 하드코딩 값을 "정상적으로 결정된 값"으로 믿고 `budget_reference_device` 배선을 설계한
   흔적까지 남아 있었다 — 잘못된 가정이 문서화 관례를 통해 전파된 사례.
3. `_metric_stage_budget_vds_by_device()` — docstring이 스스로 "①과 동일 기본값"이라 명시한
   **read-side 복제본**(①은 write-side). 이런 복제본은 ①만 고치면 write/read 기본값이
   서로 어긋나 헤드룸 예약이 실제 배정과 불일치하게 된다.
4. `search_stage_budget_L_warm_start()`(`gm_id=15.0` 기본값까지 동일) — presolve 참조점만
   편향시키지만, 세션40이 이걸로 찾은 gain_db≈69.4dB 지점 전체가 무효화 후보였던 이유의 뿌리.

낮은 우선순위로 `min_vds_by_role.get(role, 0.2)` 복붙 2곳(`reserved_vds_for_other_stack_
members()`/`allocate_stack_headroom()` 호출부)도 추가 발견.

**사용자 지시**: "자꾸 복사해서 쓰는 부분이 없어야 해. 한곳만 고치면 전부 고쳐지는 설계가
필요해... 그리고, 전부고쳐. 이월하지 말고." — 찾은 7건 전부를 그 세션 안에서 설계·구현·검증까지
완료했다.

**해결(현재 이 프로젝트가 실제로 쓰는 구조)**: `resolve_feed_vds(name, declared_vds, ctx)`
하나로 통합 — (1) `ctx.sized[name]`에 이미 vds가 있으면(compensation/다른 theta가 먼저
확정) **그 값을 존중**(새로 지어내지 않음, 이게 핵심이었다 — M15/M16이 compensation으로
이미 vds=0.9V를 정확히 배정받고 있었는데 `_feed_metric_stage_budget()`이 확인도 안 하고
0.6V로 덮어쓰고 있었을 뿐, **필요한 메커니즘은 이미 존재했다**). (2) `declared_vds`(feed_spec
명시값) 있으면 그대로. (3)(4)는 `_feed_vds_fallback(declared_vds, role, min_vds_by_role)`로
위임 — `headroom_role`이 있으면 `min_vds_by_role[role]`(`allocate_stack_headroom()`이 실제로
참조하는 것과 동일 소스, 없으면 `_DEFAULT_MIN_VDS_FALLBACK=0.2`), 둘 다 없으면(진짜 KVL
무관 자유 소자) `_DEFAULT_UNCONSTRAINED_VDS=0.6`.

**검증**: `_build_theta_evaluator()`+`presolve_warm_start()`로 실제 확인 — `output_stage_a`
(M15/M16 합=1.8000V=vdd, diff=0.0000), `output_stage_b`(M25/M26 동일), `cmfb_tail`
(M36a+M37a+M38 합=1.8000V=vdd) 전부 KVL 정확히 만족. 3개 다른 회로는 self-test에서 회귀
없음(이 우선순위 함수의 (1)은 compensation이 미리 vds를 정해준 소자에서만 발동하므로 다른
회로 기존 동작을 안 바꾼다).

**★★★★ 2026-09 세션44~45와의 직접적 관계 — 이게 오늘 발견한 버그의 정확한 코드 위치다**:
`resolve_feed_vds()`/`_feed_vds_fallback()`은 "중복 제거"(같은 상수 4곳 복붙 방지)는
완벽하게 해결했지만, **diode-connected 소자(gate=drain, Vgs=Vds가 물리적으로 강제)에 대해
`min_vds_by_role[role]`(또는 그 폴백 0.2V)이 실제로 그 소자의 gm_id가 요구하는 진짜 Vgs와
같은지는 애초에 검증 대상이 아니었다** — 이 함수가 푸는 문제는 "값이 일관되게 하나의
소스에서 나오는가"이지 "그 값이 물리적으로 옳은가"가 아니다. 2026-09-04 세션(오늘)이 SPICE
트랜지언트 검증 중 이 잔여 gap을 실측으로 발견했다(16개 diode-connected 소자 중 최대 1.02V
오차, M18_bg는 `_DEFAULT_MIN_VDS_FALLBACK`을 그대로 받아 실제 필요 Vgs≈0.99V인데 0.2V만
할당). 즉 **사고19/23/24가 만든 "중복 없는 단일 소스" 인프라는 정확했지만, 그 단일 소스
자체(`min_vds_by_role`/`_DEFAULT_MIN_VDS_FALLBACK`)가 diode-connected 소자에게는 여전히
물리적 근거 없는 상수였다** — 사고19가 남긴 경고("이 값이 실제로 맞는 값인지는 검증된 적이
없다")가 결국 실현된 사례. `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`의 재설계는
이 `resolve_feed_vds()`/`_feed_vds_fallback()` 인프라를 그대로 재사용하되, diode-connected
소자 한정으로 `_DEFAULT_MIN_VDS_FALLBACK` 대신 Vgs=Vds 고정점 반복을 끼워넣는 방향이다(계획
§3 `_resolve_device_headroom()`).

**교훈**: "복사하지 말고 단일 소스로" 원칙을 지켰다는 사실 자체가 "그 단일 소스의 값이
물리적으로 옳다"를 보장하지 않는다 — 중복 제거와 물리적 정확성은 서로 다른 축의 문제이고,
전자를 풀었다고 후자가 저절로 풀리지 않는다.
