verdict: Major 4, minor 9

# 계획 전수 모순 점검 -- 구간 `cross` (계획 사이 정합)

- 점검자: cross 구간 agent (작성자 아님, 읽기·보고만)
- gain-budget = `git show ec1aad3a:docs/01-plan/features/gain-budget-gmid-sizing.plan.md` (줄 번호는 이 판 기준). v6.39.6 변경 줄 = 033877eb 대비 줄 단위 diff로 뽑은 3, 11, 180, 224, 264, 269, 293, 296, 306, 308, 450-451, 541, 573, 766, 1056, 1084, 1273-1276, 1369, 1417, 1419, 1778, 2740-2753, 2778-2797, 2841, 3011-3014.
- 하위 계획 = master head `475e0b54`의 `docs/01-plan/features/` (작업 트리와 같음). 줄 번호는 그 파일 기준.
  offset-trim v0.8.1, offset-strategy v0.8.2, graph-consumption v0.14.11, oracle-portability v0.6.34, headroom-chain v0.7.9.11.
- 사용자 결정 원문: `wt/_drafts/user_decisions.md` O-255~O-267 행(1236~1248행).
- 시각 사실: O-267 커밋 `ce1ca011` = 2026-11-08 09:14:14, 점검 대상 `ec1aad3a` = 09:15:45 (O-267이 먼저 있었다).

## 먼저 볼 것

### Major (4건)
| # | v6.39.6 기인 | 요지 |
|---|---|---|
| M1 | 예 | oracle-portability :455가 ICMR servo 벤치의 차동 입력쌍을 topology role 문자열로 정의하고 "상위 N3.8 기본 포트 뷰·DEC-106 (1)과 같은 role 선언 쌍"이라 적음. v6.39.6 DEC-106 (1a)·N3.8(:766)은 role을 쌍 판정 근거에서 뺐다 |
| M2 | 예 | headroom-chain N0.1(:71)이 차동 입력쌍을 "포트 역할 `differential_input_p`·`_n`"으로 정의함. graph-consumption(:54)은 용어를 이 N0.1에서 가져온다. DEC-106 (1a)와 정의가 두 자리로 갈린다 |
| M3 | 예 | offset-trim N4(:653, :670)와 :256은 차동 입력 판정을 따로 한다("차동 입력 포트 유무", "derived `diff_pair`가 생기지 않으면 2번 사유"). 이것은 둘째 판정 자리이고, 범위도 derived로 좁다. DEC-106 (1a)는 status를 따지지 않고 rfc·erfc 2/13을 포함한다 |
| M4 | 아니오(v6.38.5) | gain-budget DEC-104 R9(:304)는 card DE-1이 `rel_kvl_branch`를 READS한다고 적는다. graph-consumption U-G1·U-G3(결정됨 O-13), :320, GC-2(:640), 완료 조건 :676은 `rel_kvl_branch`를 지우고 grep 0을 요구한다. 두 규칙을 함께 지킬 수 없다 |

### v6.39.6 기인 지적 전체
M1, M2, M3, m1, m2, m6(일부: (1a) 필드가 닫힌 목록에 빠짐), m7, m8.
공통 원인: v6.39.6 Status(:11)와 card DI-1(N6.48, :2778~2797) 어디에도 하위 계획 전파 항목이 없다. v6.38.x 판들은 "하위 계획 전파"를 적었다(:11 이전 판 사슬, :393). DI-1 재작성 범위 (d)(:2790)는 엔진 code 자리만 나열하고, 같은 판정을 문장으로 다시 적은 하위 계획 자리(headroom-chain N0.1, graph-consumption N3·K-3, oracle-portability N3.9 ICMR 행, offset-trim N4·N3.2)는 나열하지 않는다.

## 지적 표

종류: 1 내부 모순, 2 결정 왜곡·누락·낡은 문언, 3 같은 정의 두 자리, 4 근본원칙, 5 v6.39.6이 정합 규칙을 깸, 6 card 선후·착수·완료.

| 번호 | 판정 | 종류 | 줄 | 충돌 상대 | 근거 | 고칠 방향 (옛 → 새) | 사용자 결정 필요 |
|---|---|---|---|---|---|---|---|
| M1 | Major | 2·3·5 | oracle-portability :455 ('ICMR 측정 구성' 행. "차동 입력쌍 = topology `ports`가 role(`differential_input_p`·`differential_input_n`)로 선언한 차동 입력쌍 … 상위 N3.8 기본 포트 뷰의 여기와 같은 role 선언 쌍이고 상위 DEC-106 (1)이 묶는 쌍과 같음") | gain-budget :306 DEC-106 (1a) ("role 문자열·이름·analog-grammar 태그는 쌍 판정 근거가 아니다". 소비자 목록에 "ICMR·측정 구성", "oracle 넷리스트 생산자(EO-1)"), :766 N3.8 (v6.39.6: "쌍 판정 = DEC-106 (1a) 구조 판정 필드 READS(role 문자열 쌍 판정 0)"), O-264 | 하위 계획이 스스로 "상위 N3.8·DEC-106 (1)과 같음"이라 적으므로 정본은 상위다. 상위가 근거를 바꿔 이 문장은 거짓이 되었고, role을 쌍 판정 규칙으로 남겼다. 같은 행(:455 @2347)과 :457·:728은 "포트 role 이름은 근거로 쓰지 않음"이라 적어 행 안에서도 엇갈린다. library 결과는 13/13 같다(o264 점검 §3.1). 그러나 규칙 근거가 정면으로 다르다 | 옛 "topology `ports`가 role(…)로 선언한 차동 입력쌍 … 같은 role 선언 쌍이고 상위 DEC-106 (1)이 묶는 쌍과 같음" → 새 "오라클 입력의 차동 입력쌍 선언(생산자 = 상위 card EO-1, 원천 = 상위 DEC-106 (1a) 차동 입력쌍 필드; p/n 극성은 상위 role 극성 규약 -- 상위 Q-DI1). 오라클은 role 문자열로 쌍을 판정하지 않음". NFR-P3(엔진 계산을 받지 않음)과 맞는지 함께 적는다. 이 값은 엔진 끝 계산이 아니라 측정 구성 선언이다 | 예 -- 하위 계획 문언 개정(O-267). 정본 방향(오라클이 엔진 필드를 입력 선언으로 받을지, 오라클이 구조 판정을 따로 할지)은 결정 사항이다 |
| M2 | Major | 2·3·5 | headroom-chain :71 (N0.1 Gs⁺ 행: "선언된 차동 입력쌍(포트 역할 `differential_input_p`·`_n`)의 두 포트는 공통모드 변수 하나를 공유하는 한 점"), :73·:162·:239 ("선언된 차동 입력쌍"); graph-consumption :54 ("용어와 정의는 headroom-chain N0.1과 같다(상위 FR-9)") | gain-budget :306 DEC-106 (1)·(1a), :264 DEC-64 (v1) (v6.39.6: "차동 입력쌍(연결 구조 판정 -- DEC-106 (1a), O-264)"), O-264 | 차동 입력쌍 정의가 두 자리에 있다. 상위는 연결 구조로, headroom-chain N0.1은 role로 정의한다. graph 규칙 3(같은 정의 = 하나)의 문서 수준 위반이다. graph-consumption은 용어를 N0.1에서 가져오므로 함께 낡는다. 하위 계획이 "상위 DEC-106"을 인용하므로 정본은 상위다 | headroom-chain :71 옛 "선언된 차동 입력쌍(포트 역할 `differential_input_p`·`_n`)" → 새 "차동 입력쌍(상위 DEC-106 (1a) 구조 판정 필드 READS -- 정의는 상위 한 자리)". :73·:162·:239의 "선언된"은 "(상위 DEC-106 (1a) 판정)"으로 바꾼다. Version History에 O-264 전파를 적는다 | 예 -- 하위 계획 개정(O-267) |
| M3 | Major | 3·5·4(graph 규칙 1) | offset-trim :653 (N4 2번 "차동 입력 포트가 없으면 → `trim_single_input_unsupported`(D-8)"), :670 ("각 회로에서 derived `diff_pair`가 실제로 생기는지는 TR-2에서 측정한다. 생기지 않으면 2번 사유로 보고한다"), :256 (N3.2 '정의되지 않는 경우') | gain-budget :306 DEC-106 (1a) (status 무관: "derived로 좁히지 않는다: 좁히면 분할·교차 결합 입력쌍(3~4멤버라 `review_needed`) 2/13이 정의 불능으로 갈린다", "정본 필드 하나·writer 하나·둘째 생산자 0"); `o264_contradiction_check.md` §3.2 (rfc_ota·erfc_ota) | offset-trim은 차동 입력 판정을 따로 한다(판정 근거도 적지 않음). 운용 기준은 derived `diff_pair` 존재다. 이 둘째 판정 자리는 정본 필드와 rfc·erfc 2/13에서 결과가 갈린다. 상위 :306의 소비자 목록과 DI-1 (d)(:2790)에 offset-trim trim 적용 판정이 없다(만들면 배선 누락). offset-trim 쪽 판정 기준의 정본 자리는 적혀 있지 않다(정본 미지정). graph 규칙상 상위 필드가 정본이다. 불확실 부분: :670은 '적용 예상' 주석 문단이다. 그러나 "생기지 않으면 2번 사유"는 판정 규칙으로 쓰였다 | offset-trim :653 옛 "차동 입력 포트가 없으면" → 새 "상위 DEC-106 (1a) 차동 입력쌍 필드가 서지 않으면(필드 READS -- 둘째 판정 0)". :670 옛 "derived `diff_pair`가 실제로 생기는지 … 생기지 않으면 2번 사유" → 새 "차동 입력쌍 필드(status 무관)가 서는지를 TR-2에서 잰다". 상위 :306 소비자 목록과 DI-1 (d)에 'offset-trim trim 적용 판정(D-8)'을 더한다 | 예 -- 두 계획 개정(O-267) |
| M4 | Major | 2·3(graph 규칙 1·6) | gain-budget :304 DEC-104 R9 (v6.38.5 classab 점검 R-C: "반대쪽 소자 gate가 `kvl_branch` 고리에 묶이면 … 새 필드 0(`rel_kvl_branch` READS); 식·자리 = card DE-1 design 몫") | graph-consumption U-G1 :756 (결정됨 O-13: KVL 정본 = 쓰기 계획 출력, 별도 사이클 필드 없음), U-G3 :758 (결정됨 O-13: `rel_kvl_branch` 삭제 승인), N3.2 표 :320 ("봉인 8만. 정의가 엔진 방정식과 다름"), GC-2 :640 (5)·:398 (삭제), 완료 조건 :676 ("`rel_kvl_branch`… 참조 grep 0") | 상위가 삭제 승인된 필드에 새 소비자(DE-1)를 지정했다. 하위 GC-2 완료 조건(grep 0)과 함께 지킬 수 없다. 그 필드는 엔진 KVL 정본과 정의가 다르다(graph-consumption F-G7). graph-consumption 계획 어디에도 DE-1 소비자가 없고 상위 :304도 U-G3을 언급하지 않는다. v6.39.6 기인은 아니다(v6.38.5 문언) | gain-budget :304 옛 "새 필드 0(`rel_kvl_branch` READS)" → 새 "새 필드 0(KVL 고리 = 쓰기 계획 출력 READS -- graph-consumption U-G1; `rel_kvl_branch`는 U-G3 삭제 대상이라 읽지 않음)". 쓰기 계획 출력에 부유 배터리 결합 gate 고리 정보가 있는지는 DE-1 design 확인 항목으로 둔다. 없으면 계획부터 고친다(S-7) | 예 -- 상위 계획 개정(O-267). U-G3(O-13)은 바꾸지 않는 방향 |
| m1 | minor | 2·5 | graph-consumption :15 (Status "범위 = 선언된 차동 입력쌍"), :148 K-3, :369 '미선언 입력 포트' 행, :399 8. v1 포트 차 루프 | gain-budget :306 (1a), :264 | "선언된 차동 입력쌍"은 v6.39.6 뒤 판정 근거를 흐린다. role을 직접 쓰지 않아 M2보다 약하다 | 옛 "선언된 차동 입력쌍" → 새 "차동 입력쌍(상위 DEC-106 (1a) 구조 판정)" | 예(문언 개정, O-267) |
| m2 | minor | 2·6 | gain-budget :2790 DI-1 재작성 범위 (d) ("oracle 넷리스트 생산자(EO-1 -- `tools/spice_oracle/legacy_adapter.py` `PORT_ROLES` 입력 쪽 포함; card EO-1·oracle-portability 계획 몫이면 그 card로 넘기고 행에 적는다)") | oracle-portability OP-12 :518 (철회 -- "as-built `legacy_adapter`는 상위 card LT-1 순서 3이 지우는 코드라 고치지 않는다", 상위 O-169), :73 (legacy_adapter는 LT-1이 지움, 새 생산자 = EO-1) | 지울 code를 재작성 대상에 넣었다(O-169 위반 소지). 오라클 쪽 쌍 판정 몫의 주인을 "이면 넘긴다"로만 적어 정본이 정해지지 않았다(EO-1 대 oracle-portability). M1과 묶어서 정해야 한다 | 옛 "`legacy_adapter.py` `PORT_ROLES` 입력 쪽 포함; … 몫이면 그 card로 넘기고" → 새 "`legacy_adapter.py`는 LT-1 삭제 대상이라 무변경(O-169). 오라클 입력의 차동 입력쌍 선언 = card EO-1 생산자가 (a) 필드를 READS해 낸다(소유 = EO-1). oracle-portability :455 문언 개정은 M1" | 예(M1과 함께) |
| m3 | minor | 2·6 | gain-budget :1175 V9 (`matching_offset` 멤버 (W/L, ln IDu) 일치 = 검증 소비자), :573 S1 구조 type 목록 (`matching_offset`·`kvl_branch`·`kcl_group`·`vds_eq_vgs`·`matching_ratio` 유지), :2022 card DT-1 (6) (`rel_matching_offset` domain 표기 정정) | graph-consumption :500 (V9 멤버 출처를 `matching_groups`로 옮기는 상위 개정이 삭제의 선행), U-G3 :758 ("V9 개정 뒤" 삭제 승인), :584 X-G7; gain-budget v6.39.6 :306 ("`rel_matching_offset`은 … 삭제를 승인한 사본이라 정본 입력이 될 수 없음") | 하위 계획은 상위 V9 개정을 삭제의 선행으로 요구한다. 상위에는 그 개정 행·card가 없다. 상위 안에서도 :306은 '삭제 승인 사본'이라 하고 :1175는 현행 검증 소비자, :2022는 표기 정정 대상으로 둔다. 실제로 조건부 승인이라 규칙이 정면으로 부딪치지는 않는다. 선후가 비어 있다 | gain-budget에 'V9 멤버 출처 = `matching_groups` diff_pair·`gs_groups`'로 바꾸는 개정 자리(card 또는 V9 문언)를 두거나, :306 문언을 "U-G3 조건부 삭제 대상(V9 개정 뒤)"으로 맞춘다. DT-1 (6)은 삭제 예정 필드의 표기 정정이라 범위를 다시 본다 | 예(O-267) |
| m4 | minor | 6 | oracle-portability :525 (EO-1 위치 "이 계획 OP-3 뒤·첫 동작 변경 card(HC-S·HC-1·GC-*·FX-1·DE-1 등) 앞", 선행 card 목록에 옛 ME-1), :423 U-6 (v6.19 `81fc49a7` 줄 번호 인용) | gain-budget :1331 EO-1 행 ("범위 4 = IT-1 + IT-2 … 아래 모든 동작 변경 card의 완료 판정(SPICE 다리)보다 먼저 -- 병합 선행이 아니다"), :1402, :1413 (범위 1~3 = EO-1 범위 4·OP-3 뒤) | 상위는 EO-1을 범위 4(IT-1+IT-2 뒤)와 범위 1~3으로 나누고, 선후를 '판정 선행이지 병합 선행이 아님'으로 정했다. 하위의 "첫 동작 변경 card 앞"은 병합 선행으로 읽힐 수 있다. 선후 정본은 상위 card라 상위 N6.1이다 | oracle-portability :525 옛 "OP-3 뒤·첫 동작 변경 card … 앞" → 새 "선후 정본 = 상위 N6.1 EO-1 행(범위 4 = IT-1 + IT-2 뒤, 범위 1~3 = 범위 4·OP-3 뒤; 동작 변경 card에는 판정 선행, 병합 선행 아님)". ME-1 → CL-1, v6.19 줄 번호 인용은 현행 판으로 바꾼다 | 예(문언, O-267) |
| m5 | minor | 2 | gain-budget :1371 (offset-trim TR-* 행 "선후 정본은 그 계획(v0.6 `plan/offset-trim-v06` `23e6a142`의 선행·착수 조건)") | offset-trim 현행 v0.8.1 (master) | 낡은 판 인용 | 옛 "v0.6 `plan/offset-trim-v06` `23e6a142`" → 새 "현행 판(master)" 또는 판 번호 없이 "그 계획 N5·card 표" | 아니오에 가까움(표기). O-267상 계획 문언이라 승인 묶음에 넣는다 |
| m6 | minor·불확실 (Major 후보) | 3·4·5 | offset-trim N3.3 결속 2 :285, G-29 :858, X-66 :968 (되돌린 보기로 읽는 구조 필드 = 닫힌 목록 "structure.json 개념, S1 정합 묶음(대응 넷 포함), S1v 신호 경로 역할"), :67·:270 (trim 파일 포트 = 연결·전원·bias·코드 입력), :376 (직렬 저항 trim -- 소스 퇴화 직렬 삽입) | gain-budget :306 DEC-106 (1) ("차동 입력쌍 + 다른 입력 방향 포트 → 정의 불능 정지"), (1a) (새 S1 차동 입력쌍 필드, "같은 source 넷"), :1273 Q-FS2 (기본안 (가) DEC-97 자기동형 궤도 = '찾아 둔 대칭' 정본), O-263 (3) "구조 사실(정합 묶음 등)은 원본 회로에서" | (a) 새 (1a) 필드는 닫힌 목록에 없다. 합성 회로에서 직렬 소스 trim이 '같은 source 넷'을 깨면 그 변형만 정의 불능이 될 수 있다. (b) trim 포트(bias·코드 입력)가 `node.port_direction` = 입력 집합에 드는지 두 계획 모두 정하지 않았다. 들면 모든 합성 회로가 (1) 정의 불능 정지에 걸린다. (c) DEC-97 궤도(θ 묶음, Q-FS2 기본안)가 닫힌 목록에 없다. 한쪽 trim이 자기동형을 깨면 "같은 θ" 부담 비교(offset-trim :72·:132)의 θ 공간이 변형마다 달라진다. (b)(c)는 v6.39.6 전부터 있었고, (a)와 Q-FS2는 v6.39.6이 더했다. 정본 미지정(어느 계획도 정하지 않음) | offset-trim 닫힌 목록에 "상위 DEC-106 (1a) 차동 입력쌍 필드, 상위 DEC-97 궤도(θ 묶음)"를 더할지, trim 포트의 방향 분류(측정 구성 입력 아님 -- O-246 D6 '바이어스 입력'·코드 입력 선언과 같은 층)를 정할지를 결정 질문으로 올린다 | 예 |
| m7 | minor·불확실 (구간 밖 참고, gain-budget 내부) | 1·5 | gain-budget :306 (1a) (빼는 넷에 "이상 전압원 단자"), :2795 DI-1 완료 toy (c‴) "공유 source가 이상 전압원 단자인 쌍" | gain-budget :680 ("topology 원소로서 이상 전압원 미지원(DEC-101 (2)·N6.21 '이상 전압원 없음' 행·N6.35 E-27, 지원 밖 원소 = 단계 A 정지)"), :2379, :2603 E-27 | topology의 이상 전압원은 단계 A에서 정지한다. 그래서 (1a)의 '이상 전압원 단자' 갈래와 toy (c‴)는 엔진 안에서 만들 수 없는 꼴이다. 측정 구성 원(입력 DC 선언 포트)을 뜻한다면 같은 집합 안의 셋째 항과 겹친다 | (1a)·toy (c‴)에 "이상 전압원 = 무엇(topology 원소 미지원 → 해당 0 / 측정 구성 원)"을 한 줄 적거나, toy를 "단계 A 정지"로 기대값을 바꾼다 | 예(O-267) |
| m8 | minor (구간 밖 참고 -- 결정 낡은 문언) | 2 | gain-budget :2793 DI-1 착수 조건 (5) "**code 작성 전 사용자 승인**(사용자 결정 O-266)", :2753 FS-1 code 재개 착수 조건 (7) 같은 문언, :11 m-10 | O-267 (user_decisions :1248, 2026-11-08: "코드는 그냥 하지만 계획수정은 승인받아" -- O-266 대체, code는 위임), CLAUDE.md O-229 7번 예외(교체) | O-267 커밋(09:14)이 ec1aad3a(09:15)보다 먼저인데도 대체된 O-266을 착수 조건으로 인용했다. 더 엄격한 쪽이라 fail-open은 아니다 | 옛 "code 작성 전 사용자 승인(사용자 결정 O-266)" → 새 "code는 위임(O-267 -- O-266 대체); 원칙 위반 code는 재작성. 계획 문언 개정은 사용자 승인" | 예(O-267: 계획 문언) |
| m9 | minor | 2 | offset-trim :645 N4 제목 "library 13회로 적용 판정 방법", :658~:668 표(9회로) | gain-budget DEC-106 (1a) 실측 library 13 (rfc·erfc 포함), O-182 Q-LB1 (library 13) | 판정 표가 9회로뿐이라 M3의 갈림 회로(rfc·erfc)가 표에 없다 | 표에 나머지 4회로를 더하거나 "9회로 -- 나머지 4는 TR-7 측정"으로 적는다 | 아니오에 가까움(표). O-267상 승인 묶음 |

## 개념별 대조 결과 (지시 2의 9개)

| 개념 | 결과 | 정본 |
|---|---|---|
| 차동 입력 판정 (DEC-106 (1a) 대 role 문언) | 갈림: M1 (oracle-portability :455), M2 (headroom-chain :71 → graph-consumption :54), M3 (offset-trim :653·:670), m1, m2 | gain-budget DEC-106 (1a) (하위 계획이 '상위 DEC-106' 인용). offset-trim은 정본 미지정 |
| 입력 DC·공통모드 | 정합: 공통모드 변수 하나·묶음 = 정점 묶음·ΔV = 0 KVL·그 밖 다중 입력 정의 불능 (gain-budget :306 (1)~(4), headroom-chain :71·:73·:239, graph-consumption :54·:148·:369·:399), oracle V_cm = 입력 포트 전압 평균 (oracle-portability :455 @1019 -- 엔진 정의 인용). 갈림은 판정 근거뿐(위 행). 열린 것: trim 포트가 '다른 입력 방향 포트'인지 (m6 (b)) | gain-budget DEC-106 |
| F 고정 노드 | 정합: F = 레일 ∪ 노드 목표 ∪ 선언 입력 포트 (gain-budget :306 (1a) 정의 축, headroom-chain :71, graph-consumption :54). (1a)의 '이상 구동 넷'은 정의 축(측정 구성 결합 대 θ 고정 집합)을 적었으므로 규칙 3 위반이 아니다. 이상 전압원 항은 m7 | gain-budget (용어 = headroom-chain N0.1, FR-9) |
| 정합 묶음·대칭 궤도 | 하위 계획 안에서는 정합. 전류 대칭 S0 필드(`orbits`·`current_symmetry`·`untie_orbits` 입력, writer = HC-1)는 graph-consumption :645·:775와 headroom-chain :351이 같다. 열린 것: Q-FS2 '찾아 둔 대칭' 정본(gain-budget :1273)이 정해지지 않았고, offset-trim 되돌린 보기 닫힌 목록에 궤도가 없다 (m6 (c)) | DEC-93(정합 묶음)·DEC-97(궤도); Q-FS2는 정본 미지정 |
| offset 쌍 | 'offset 쌍'을 정의 용어로 쓰는 계획은 없다(gain-budget·하위 계획 grep 0. o264 점검 #24가 A-209 표현을 이미 정정). σ_in·V_id* 정의는 offset-trim :46·:419와 offset-strategy :107이 gain-budget DEC-23을 인용해 같다. `rel_matching_offset`(불일치 묶음) 상태 정합은 m3 | gain-budget DEC-23 |
| 교류접지 | 하위 5계획 언급 0 (grep `교류접지|ac_ground|AC 접지` = 0). 계획 사이 충돌 없음. gain-budget 안 v6.39.6 문언(:293·:306 "'모든 뷰 교류접지' = 뷰 무관 S1 `ac_ground_class`, (4) 바이어스 종속 넷 미포함")은 :539 '교류접지는 뷰 속성'과 :2018~:2020 card(뷰 무관 분류 (1)(2)를 DC 이름 필드로)와 이어진다. 확인은 design 몫으로 표지되어 있다 -- 내부 구간 몫 | gain-budget N3.2 AC 구조 1 |
| trim 합성 회로·구조 판정 (O-263) | offset-trim :123·:185·:285·:968이 O-263 (3)을 '되돌린 보기 규칙 하나(닫힌 목록)'로 읽는다(X-63, 원래 취지와 다름 표지됨). gain-budget에는 O-258·O-262·O-263 행이 없고 trim 합성을 언급하지 않는다(offset-trim N3.10 :604 "DEC-110 순서를 바꾸지 않음" -- 상위 개정 불요로 읽힘). 갈림 후보는 m6 | offset-trim N3.3 (상위는 정본 미지정) |
| oracle 넷리스트 생산자 (EO-1) | 소유 정합: 생산자 = gain-budget card EO-1, 입력 스키마 정본 = oracle-portability G-18 (oracle-portability :73·:525, gain-budget :1331, graph-consumption U-G10 :763). 갈림: 선후 문언 m4, DI-1이 legacy_adapter를 재작성 대상에 넣음 m2, 차동 쌍 선언 근거 M1 | 생산자·선후 = gain-budget N6.1·N6.20; 스키마 = oracle-portability |
| graph-consumption U-G 결정 (필드 삭제·소유) | U-G1·U-G3 대 gain-budget DEC-104 R9 = M4. U-G3 `rel_matching_offset`·V9 선행 = m3. U-G9 봉인 8 삭제는 gain-budget :2178이 같은 변경 삭제 규칙으로 받아 정합(:675 "봉인 8 멤버 합"은 삭제 때 같이 고칠 문언). U-G4 (`on_mask` 정본, O-249)·U-G13(v6.38.3 재정의)은 상위 정정 표지와 정합. U-G10 EO-1 정합 | graph-consumption U-G (결정됨 O-13) |

## 읽은 범위

- gain-budget ec1aad3a: 전체 3072줄을 줄 단위로 읽지는 않았다(파일 2.1 MB). 읽은 것:
  - v6.39.6 변경 줄 전부를 033877eb와 줄 단위로 비교했다(28 hunk). 그중 전문을 읽은 줄은 :306(DEC-106 전문), :450·:451, :1273~:1276, :1369, :1417, :1419, :2778~:2797(DI-1 전문), :573이다.
  - 개념 키워드로 찾아 앞뒤를 읽은 줄은 :103·:111·:293·:296·:304(R9 부분)·:310(DEC-110 일부)·:324·:539~:556 일부·:675·:680·:766(변경 부분)·:1175·:1331·:1341·:1371·:1382·:1393·:1402·:1413·:1486·:2018~:2022·:2052·:2178~:2200·:2379·:2581·:2595·:2603이다.
- 하위 계획(master 475e0b54): 다섯 파일 전체를 줄 단위로 읽지는 않았다. 키워드 grep(차동 입력·입력쌍·role·direction·공통모드·input_dc·F·궤도·자기동형·matching_groups·rel_*·교류접지·EO-1·O-263·되돌린 보기·θ 소속)으로 찾은 줄과 그 앞뒤만 읽었다.
  - offset-trim: :9~:19, :46, :55, :61~:76, :107, :123, :132~:133, :180~:190, :212~:213, :250~:262, :270~:274, :285, :373~:385, :403~:406, :419, :438, :602~:610, :645~:672, :743, :793~:804, :858, :888, :965~:968, :1016, :1057, :1078, :1085
  - offset-strategy: :8~:13, :36, :51, :107, :134, :148, :221 (해당 개념 언급이 적음)
  - graph-consumption: :11~:15, :54, :72, :148, :173~:175, :202, :219, :229, :320, :325, :369, :398~:399, :465, :478, :500, :584, :640, :645, :676, :756~:766, :775
  - oracle-portability: :73, :123, :135, :139, :144, :151, :423~:424, :429, :433, :452~:457, :505~:525, :598, :728
  - headroom-chain: :24, :71, :73, :162, :237~:239, :351
- user_decisions.md O-255~O-267 원문(:1236~:1248), `o264_contradiction_check.md` §3·§3.2 일부 grep

## 안 본 것

- gain-budget 본문 가운데 변경 줄·키워드 적중 줄 밖(대부분의 N3·N6 card 본문, N7, 부록)과 history(ec1aad3a)는 보지 않았다. history 성격 문장의 원칙 25 위반 점검은 하지 않았다(다른 구간 몫).
- 하위 계획의 키워드 밖 본문(offset-strategy 대부분, oracle-portability OP-1~OP-12 행 본문 나머지, headroom-chain N3·N4 본문 대부분, graph-consumption N3.3·N4 대부분)과 하위 계획 history.
- `docs/01-plan/features/` 안의 verilog-*·analog-topology-json-library 계획: gain-budget 규칙과 공유하는 개념이 없어 대상에서 뺐다(analog-topology-json-library는 머리말만 확인).
- la1_auto_decisions.md(A-행)는 열지 않았다. A-번호 대조는 하지 않았다.
- design 문서(40·41·42)와 엔진 code는 보지 않았다. 문서 점검이라 엔진 사실 확인은 하지 않았다.
- m6·m7은 문서 판독만 했다. 합성 회로나 toy를 실제로 만들어 재지 않았다(불확실 표지).
