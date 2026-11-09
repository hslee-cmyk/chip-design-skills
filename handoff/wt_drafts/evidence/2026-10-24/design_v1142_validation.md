# design v1.14.2 독립 검증 (gain-budget 40·41·42, 계획 v6.37 슬루 맞춤)

- 대상: worktree `wt/design-v1142`, 커밋 `b9393e2e`(base `56dd1f8a`), 문서 40-engine·41-gain-budget·42-gap-checklist
- 기준: 같은 worktree 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v6.37(2347줄), `_drafts/user_decisions.md` O-119~O-126
- 정정 목록 출처: `plan_v637_recheck5~8.md`(design 정정 대상 표), `b80_pushpull_front_zero.md` §3 (d)
- 엔진 실측: `wt/integ-it12` HEAD `34585913`(읽기만)
- 작성자 보고는 증거로 쓰지 않았다. 모든 판정은 아래 재측정에서 나왔다.
- 가드: 파일 수정 0(이 증거 파일만), git은 `git -C <절대경로>` 읽기만. 검증 뒤 `git status` 두 worktree 모두 변경 0, design HEAD `b9393e2e` 그대로.

## 0. 결론

- 점수 **87/100**
- D-1~D-13 13건 모두 정정됐다. 계획 v6.37과 뜻이 다른 곳은 없다.
- 결함: 중 2(M-1 피크 행 분해능 '기존 규칙' 사실 오류, M-2 `ORACLE_ONLY_SPEC` 소비자(spec 로더) 부재 미표시), 소 2(m-3 41 §5.10 U15 호출 경로 '유지' 잔존, m-4 DC 양을 `ls`로 표기), nit 5
- 판정: **조건부 승인 가능**. 원칙 위반으로 막히는 결함은 없다. M-1·m-3·m-4는 문언 정정이다. M-2는 design에 표지를 달고 오케스트레이터가 계획 쪽(로더 소유 card)을 확인하면 된다.

## 1. D-1~D-13 정정 확인 (검사 1)

diff `56dd1f8a..b9393e2e`: 3파일 33줄 바뀜, 줄 수 그대로(40 2126, 41 1993, 42 363).

| # | 자리(v1.14.2 줄) | 정정 원문(요약 인용) | 계획 v6.37 대조 | 판정 |
|---|---|---|---|---|
| D-1 | 40:1248 | «방향별 최대 전류(`LsNode.i_charge_a`·`i_discharge_a` -- 소비자 = 피크 부하 전류 행, P DEC-58): 정의 = P DEC-65(O-26 (1) …). 엔진 손계산 규칙은 **미결 U-115**» | DEC-65(계획 264) «엔진 계산 -- 규칙 미결(U-115)», «as-built … β·σ·κ 고정 전류는 … gap … DE-1 (d)가 U-115 뒤 고친다» | 같음 |
| D-1 | 40:1249 | «**엔진 슬루 칸·행 없음** … 슬루 판정·탐색 = oracle `.tran`(전 폭 계단 출력의 20 %~80 % 구간 기울기)뿐 … (FAIL 뒤 처리 미결 U-112) … card DE-1 (d) 삭제 대상(계획 DE-1 (d) 삭제 목록 (i)~(vi))» | DE-1 (d)(계획 1635) 삭제 (i)~(vi), N3.8 '슬루율 측정 정의'(610), O-122 | 같음 |
| D-1 | 40:1251 | «(가) **피크 행** … 보고 `nodes`는 … 칸 이름으로 읽는다 … 미측정 사유 **`load_peak_resolution_undefined`** … (나) **선언 슬루** … 미측정 `("slew_rate_v_per_s", ">=", "oracle_judged")` 하나» | DE-1 (d) '피크 행 정리'(1635 «칸 순서·꼴은 design», «피크 전용 이름 … 이름은 design»), N3.8 '선언 슬루의 엔진 표시' (가)(610 «사유 'oracle 판정 대상'(이름은 design)») | 같음. 단 분해능 문장 사실 오류 M-1 |
| D-2 | 41:892, 41:924 | «블록 전류(KCL·선언 -- '슬루 하한'은 v6.37 O-122로 없음)» / S 행에서 «슬루 하한이 있으면 ID ≥ I_slew» 삭제 | DEC-71(270) 같은 문언 | 같음 |
| D-3 | 40:1740 R27 | «슬루 '기록만'(Q5 (ii))은 대체 -- 슬루 = oracle `.tran` 판정(합격 T5 안 …) … 정착 '기록만'은 … 그대로» | DEC-90 (2), T5(1262) | 같음 |
| D-4 | 42:102 행 58 | «기대 = 방향별 전류(피크 부하) … 엔진 슬루 칸·행 0(O-122 -- `rg "slew_rate>=\|_node_capacitance" E` 0이 기대)» | DE-1 완료 조건 grep(1647)의 부분집합 | 같음(nit 아님 -- 부분집합이라 모순 없음) |
| D-5 | 40:1722 R9, 40:2075 U7 | «`ls`(방향별 전류(피크 부하) -- 엔진 슬루 칸 0 …)» | DEC-58·O-122 | 같음. 영역 표기 m-4 |
| D-6 | 42:111 행 70 | «(옛 '슬루 제약' 항목 삭제 -- 슬루는 θ 제약이 아니다, 계획 v6.37 DEC-70·O-122)» | DEC-70 | 같음 |
| D-7 | 42:265 D-GB8a (+267 D-GB8c, 300 D-AP1) | D-GB8a «`ls`(방향별 전류(피크 부하) -- 손계산 규칙 미결 U-115, 엔진 슬루 칸 0(O-122))», D-GB8c «`_ORACLE_ONLY` 포함», D-AP1 «`oracle_judged`뿐인 점도 oracle 판정 입력, 그 불합격 = `oracle_only_fail`» | DEC-98 (6), N6.18 | 같음 |
| D-8 | 41:831 | «방향별 최대 전류(… 엔진 손계산 규칙 **미결 U-115** … as-built `ls_fields` β/σ/κ 고정 전류 가정 삭제는 U-115 뒤 DE-1 (d))와 엔진 슬루 몫 삭제(O-122)» | DE-1 삭제 3(1637) «β/σ/κ 고정 전류 가정(O-26 (1) -- … U-115로 정할 규칙으로 고치고 …)» | 같음 |
| D-9 | 40:1262 §3.8-8 | «**슬루는 이 레지스트리에 없다** … 엔진 슬루 registry 행을 두지 않는다(생기면 VB-1 완료 조건 (2) red)» | N6.18 완료 조건 (2)(1933) | 같음. metric 표에 슬루 행 0(재측정) |
| D-10 | 40:1256 §3.8-6, 40:977 §3.1 | «**레지스트리 밖 oracle 전용 항목** … `_ORACLE_ONLY` … `OracleOnlyVerifiedBy(metric, kind, measure)`에는 `model_error_ref` 칸이 없다 … 둘 다 아니면 지금처럼 `KeyError`» | N6.18 범위 (1)(1931) «`verified_by` 계약 개정 … `model_error_ref` 칸을 두지 않는다», DEC-90 (3)(289) | 같음. 소비자 M-2 |
| D-11 | 41:795 | «**oracle 판정 입력** … 미측정 사유가 모두 `oracle_judged` … 인 점은 oracle front 판정 입력 … (가)의 정의 불능 code가 하나라도 있는 점은 … 들지 않는다(fail-closed)» | DEC-98 (6)(297) | 같음 |
| D-12 | 40:2029, 2036, 2037, 2039 §10.5 | «(i) **분류 `oracle_only_fail`** … (ii) … P U-112 범위 … (iii) 슬루를 선언한 held-out 회로의 U17 단계 ② 완료는 P U-112 해소 뒤» + 완료 조건 2·3·5 | DEC-98 (6) (i)~(iii), O-124 | 같음. '피검' 표 행 미갱신 n-5 |
| D-13 | 41:861, 41:1135 | «**as-built는 다르다**: integ/it12 `3179cd78` 층 0은 최소형 시작점(`E/search/layer0_center.py:1-8` …) … E10 … 구현되지 않았다 … 옛 U15 전체판 … master에 병합되지 않았다 -- 계획 F-LA6» | DEC-71 상태 칸(270 끝) «미구현(as-built는 최소형 …)», F-LA6(1770); 엔진 `layer0_center.py:1-8` 실측 일치 | 같음. 같은 사실과 어긋나는 41 §5.10 m-3 |

- recheck8 §4가 '빠졌을 수 있다'고 한 40 1248행은 D-1에 들어 있다. recheck7이 '빠짐'이라 한 40 §3.8-6과 '후보'라 한 41 795행은 D-10·D-11로 들어 있다.
- O-124 원문 «13곳(D-1~D-12, 1248행 포함)»에 D-13(B80 별도 보고 1)이 더해졌다. D-13은 결정 변경이 아니라 as-built 사실 정정이고 Status에 드러나 있다.

## 2. design 안의 일관성 (검사 2)

| 대조 | 판정 |
|---|---|
| `oracle_judged` -- 40:1251 · 40:2029 · 41:795 · 42:300 | 같은 뜻(사유가 모두 `oracle_judged`인 `unmeasured_front` 점만 oracle 입력, 승격 U-112) |
| 방향별 전류 U-115 -- 40:1248 · 41:831 · 42:102 · 42:265 · 40 R9·U7 | 같음 |
| `_ORACLE_ONLY` -- 40:1256 · 40:977 · 40:1262 · 42:267 | 같음 |
| D-13 사실(U15 전체판 미병합) vs **41 §5.10(1246-1248)** «호출 경로(유지): `find_front` → `layer0_start` → `layer0_budget` → …» | **모순(m-3)** -- 엔진에 `layer0_budget` 없음(`git grep` 결과 `search/eval_budget.py:12` 주석 «U15 `layer0_budget` 이 … 읽는다»뿐), 파일 `local_*`·`combo_dp`·`assembly` 0 |
| 40 §10.5 '피검' 표 행(2015 부근) «엔진 시작점 … 과 front 점(P U-45 대상 …)» vs 2029 bullet의 `oracle_judged` 점 추가 | 표 행 미갱신(n-5, 뜻 충돌은 아님) |
| 슬루 잔존 grep(40·41·42 전수, `slew`·`슬루`) | 남은 자리는 모두 정정 문장, spec 필드 `driving_spec{slew_rate_v_per_s?…}`(40:963, spec 필드 유지 -- 계획 1635 '남기는 것' (가)), oracle 슬루 측정 구성(41:812 '슬루 측정 구성 전용' -- oracle 쪽) |

## 3. design이 정한 이름 다섯 (검사 3)

| 이름 | 계획 위임 원문 | 판정 |
|---|---|---|
| `oracle_judged` | 610 «사유 'oracle 판정 대상'(이름은 design)», 1635 '남기는 것' (가) «이름은 design» | 범위 안 |
| `load_peak_resolution_undefined` | 1635 «피크 전용 이름으로 바꾼다(이름은 design)» | 범위 안 |
| `nodes` 칸 꼴(이름·값 쌍, 칸 이름 = `LsNode` 필드) | 1635 «칸 이름으로 읽게 바꾼다 … 칸 순서·꼴은 design» | 범위 안. 1638 «결과 JSON 형식은 그대로»는 metric 값 형식이고 `nodes` 꼴은 1635가 따로 위임 -- 충돌 없음 |
| `_ORACLE_ONLY`·`OracleOnlyVerifiedBy`·`ORACLE_ONLY_SPEC` | 1931 «(자리·이름은 design)», «`verified_by` 계약 개정: 레지스트리 밖 oracle 전용 판정 제약 항목을 허용 … `model_error_ref` 칸을 두지 않는다» | 범위 안 |
| `oracle_only_fail` | 297 DEC-98 (6) (i) «(분류 이름은 design)» | 범위 안 |

- **계획에 없는 결정**: 새 결정 0. 경계 두 곳은 4절(해석 (a)(b))에서 판정했다. `verified_by(name)`의 반환 형 둘·`KeyError` 유지는 '자리·이름은 design' 안의 구현 형식이다.
- **이름 충돌 grep**(`wt/integ-it12` 저장소 전체 `git grep -i`): `oracle_judged`·`load_peak_resolution`·`oracle_only`(`_ORACLE_ONLY`·`ORACLE_ONLY_SPEC`·`oracle_only_fail` 포함)·`OracleOnlyVerifiedBy` 모두 **0건**. test 파일 이름 충돌 0(관련 기존 test 파일은 `tests/metrics/test_verified_by.py`·`test_ls_fields.py`·`tests/search/test_ls_constraints.py`뿐이고 새 test 파일 이름을 design이 정하지 않음).

## 4. 작성자 해석 둘 (검사 4)

### (a) 40:1251 «이 사유는 `bundle`·`ls_fields` 보고를 읽지 않는다» -- **계획에 맞음**

- 계획 610: «기존 미측정 경로(`ls_constraint_rows`의 `unmeasured` 튜플 -- 지금 `ss_requires_sealed_snapshot`·`ls_fields_unavailable`·`slew_current_unbounded`가 쓰는 자리)에 사유 'oracle 판정 대상'을 남긴다». 봉인 여부·보고 유무에 따라 사유를 가르라는 문언은 없다.
- 엔진 실측: `search/kernel.py:155-157`이 봉인 여부와 상관없이 `ls_constraint_rows(bundle, sctx.driving)`를 부르고, `search/eps_sweep.py:34-38` `_CLASSES`는 `unmeasured_front`를 `STATUS_SEALED`로만 받는다. 그래서 봉인 안 된 점이 `oracle_judged`를 달아도 oracle 입력(= `unmeasured_front` 부분집합)에 들지 않는다 -- design 괄호 «봉인 안 된 점은 상태 조건이 `unmeasured_front` 밖으로 보낸다»가 사실이다.
- 봉인됐지만 `ls_fields_unavailable`인 점(구조 입력 없음): 엔진 슬루 계산이 없으므로 슬루 사유를 '보고 없음'으로 둘 이유가 없다. `oracle_judged`가 '엔진이 판정하지 않음'을 더 정확히 나타낸다(fail-closed 유지 -- 그 점은 여전히 최종 `front` 밖).
- 따름 효과(nit n-9): 봉인 안 된 점·보고 없는 점의 슬루 미측정 사유가 `ss_requires_sealed_snapshot`·`ls_fields_unavailable`에서 `oracle_judged`로 바뀌어 `find_front.py:108-111` S-1 notes 집계가 달라진다. DE-1 변화표에 원인으로 적어야 한다.

### (b) 40:1256 «measure가 없으면 올린다 -- fail-closed» -- **계획에 맞음(가드), 문언 보강 권고**

- DEC-90 (3)(289) 본문 «오라클이 측정할 수 없는 선언 제약은 … `spice_unverifiable[]`로 … 출력»의 직접 적용이다. 계획의 «`spice_unverifiable[]`에 오르지 않는다»는 VB-1 대응이 있을 때의 결과 문장이다.
- VB-1 착수 조건이 OP-10 병합(1935)이라 착수 시점에는 두 방향 measure가 모두 있어 이 갈래는 운영 경로에서 발동하지 않는 가드다. VB-1 완료 조건 (1) «오르면 red»와 충돌하지 않는다.
- 다만 '없음'의 정의가 문서에 없다. 엔진은 oracle을 import하지 않으므로(as-built `verified_by.py:8`) '없음'은 `_ORACLE_ONLY` 항목이 없거나 그 measure가 None인 경우뿐이다. 또 `kind = SPICE_ORACLE`인데 measure None인 항목은 as-built 관례(`SPICE_ORACLE`이면 measure 있음)와 어긋난다(n-6).

## 5. 원칙 점검 (검사 5) -- 실측 / 자기보고 구분

| 원칙 | 판정 | 근거(실측) |
|---|---|---|
| graph 단일 정본(writer 하나, 새 cache·memo·sctx·EvalResult 값 칸·사본 금지) | **통과** | 새 graph 필드 0, 새 `sctx` 슬롯 0, `EvalResult` 칸 0. `oracle_judged`는 기존 `unmeasured` 튜플 자리, oracle 입력은 그 사유를 읽음(새 칸 0). `nodes` 꼴 변경은 칸 이름 붙이기(값 칸 0, 슬루 칸 셋 삭제). `_ORACLE_ONLY`·`ORACLE_ONLY_SPEC`은 as-built `_TABLE`과 같은 정적 이름 표. nit n-8: spec 필드 이름 문자열 `slew_rate_v_per_s`가 `_METRIC_SLEW`(`ls_constraints.py:19`)와 `ORACLE_ONLY_SPEC` 키 두 상수에 있게 됨 -- 값이 아니라 이름이지만 출처 하나(`spec_driving.py:17` `DrivingDecl` 필드)를 참조하게 권고 |
| fail-closed | **통과** | `KeyError` 유지, measure 없으면 `spice_unverifiable`, `oracle_judged` 점은 최종 `front` 밖, 다른 사유가 하나라도 있으면 oracle 입력 제외(41:795) |
| 상수 발명 금지 | **통과** | 새 숫자 0. 20 %~80 %는 O-121 B-2, 두 방향 같은 값은 O-50 G2 |
| 회로 이름·topology 태그를 근거로 쓰지 않음 | **통과** | 새 규칙에 회로 이름·태그 갈래 0. 41:861의 B80 인용은 as-built 사실의 출처이고 규칙 근거가 아님 |
| heldout을 근거로 쓰지 않음 | **통과** | 40:2029 (iii)·2036은 의존 기록(계획 DEC-98 (6) (iii) 그대로), 판단 근거로 쓰지 않음 |
| 만들면 배선(새 이름·필드마다 소비자) | **부분 -- M-2** | `oracle_judged` 소비자 = S-1 분류(`_filter`의 `unmeasured` 판정, 실재)·DEC-98 (6) oracle 입력(EO-1/LA-1 front 판정, 계획 card 있음). `load_peak_resolution_undefined` 소비자 = `unmeasured` 출력(실재). `oracle_only_fail` 소비자 = §10.5 완료 조건 3·5 집계. **`ORACLE_ONLY_SPEC`·`OracleOnlyVerifiedBy`의 판정 쪽 소비자 = spec 로더 `SizingSpecDoc.spice_unverifiable`인데 as-built에 없다**(엔진 비test grep: `spice_unverifiable`은 `metrics/verified_by.py` 상수·docstring뿐, `authoring/` 0; 40:977 상태 MISS). design은 이 로더를 누가 언제 만드는지 적지 않았다 |
| DC/AC 분리 | **부분 -- m-4** | 방향별 최대 전류는 계획 DEC-65·metric 표(625 «방향별 최대 전류 … \| DC \| `.dc`»)에서 DC 양이다. 그런데 40 §3.8-3 머리 «3. **`ls` 필드**»(1247), R9(1722)·U7(2075)·42 D-GB8a(265)가 이 양을 `ls`로 묶어 적는다. 슬루가 빠진 뒤 이 묶음에 `ls`(.tran) 양이 남지 않는다. 계획 90 «design 문서와 코드 필드는 개별 표기가 필수다» |
| DEC-103(계산 틀은 질문에 맞춘다) | **통과(관찰 1건)** | design은 방향 전류 엔진 규칙을 정하지 않고 U-115로 둔다(새 틀 결정 0). 관찰: DEC-65 정의(입력을 끝까지 몬 고정 회로의 DC 해)는 '정해진 회로를 흔드는 분석'이라 DEC-103상 KCL 틀 쪽이다. U-115 후보 (가)·(나)는 θ 틀 손계산이므로 U-115를 물을 때 이 원칙 점검을 함께 올리기를 권한다(design 결함 아님) |

## 6. 잔존 grep (검사 6) -- 40·41·42 v1.14.2 전수

| 패턴 | 남은 곳 | 사유 판정 |
|---|---|---|
| `c_slew_farad` | 0 | -- |
| `slew_charge` | 0 | -- |
| `I_slew` | 0 | -- |
| `슬루 하한` | 41:892 «'슬루 하한'은 v6.37 O-122로 없음» | 삭제 표지(계획 270 같은 문언) -- 타당 |
| `슬루율 ×` | 0 | -- |
| `최대 \|dV/dt\|` | 0 | -- |
| `as-built와 같다` | 40:12·41:17 Status(D-13 설명 인용), 40:305·354·463(분할 key `*`·같은 lineage 재사용·연속 축 키 -- 슬루·층 0 무관), 42:99(행 55 `budget_ref` 엣지 -- 무관) | 모두 D-13 대상 밖, 타당 |
| `β·σ·κ 규칙` | 0 | -- |

## 7. 표 칸 수·CRLF·front matter (검사 7)

- 바뀐 표 행 칸 수(백틱 안 `|`·`\|` 제외) = 표 머리: 40:977(4/4), 1722(7/7), 1740(7/7), 2075(8/8); 41:892(4/4), 924(5/5); 42:102(5/5), 111(5/5), 265(6/6), 267(6/6), 300(6/6). 옛 판과도 같음.
- blob 줄 끝: 세 파일 새·옛 모두 CRLF 0(LF 2125 / 1992 / 362), BOM 없음.
- front matter: 세 파일 모두 `version: 1.14.2`, `plan_version: 6.37`.

## 8. 결함 목록과 수정안

| id | 심각도 | 자리 | 내용 | 수정안 |
|---|---|---|---|---|
| M-1 | 중 | 40:1251 (가) | «c = `load_peak_margin_a`(…) ÷ **출력 노드** 방향 전류 분해능 최대값 -- **기존 규칙**». as-built `search/ls_constraints.py:50` `scale = max([r for n in nodes for r in (n[6], n[7]) if r] or [0.0])`는 보고 `nodes` **전부**(극점 노드 전부, `ls_fields.py:86-94`)의 최대값이다(출력 노드 한정은 분자 `load_peak_margin_a`뿐 -- `ls_fields.py:97-99`). 문장이 as-built docstring(`ls_constraints.py:10`)을 옮겨 code와 다르다. 구현자가 '출력 노드만'으로 바꾸면 '기존 규칙' 표지 아래 동작이 바뀐다 | «보고 `nodes` 전부의 방향 전류 분해능 최대값(as-built `:50` 그대로)»으로 고친다. 출력 노드로 좁히려면 동작 변경이므로 계획 근거를 먼저 받는다(S-7) |
| M-2 | 중 | 40:1256·40:977 | `ORACLE_ONLY_SPEC`·`OracleOnlyVerifiedBy`의 판정 쪽 소비자인 spec 로더 `spice_unverifiable`가 as-built에 없다(MISS). VB-1 완료 조건 (1) «슬루 선언 spec이 `spice_unverifiable[]`에 오르지 않음»도 이 로더에 걸린다. 로더 소유 card(계획 1169 MOD2 단위 2·U5)가 VB-1 앞에 오지 않으면 새 표가 소비자 없이 들어온다 | design 40 §3.8-6에 «소비자 = spec 로더 `spice_unverifiable`(as-built MISS, 소유 = U5/MOD2) -- VB-1 착수 때 로더가 없으면 멈추고 보고» 표지를 단다. 오케스트레이터가 계획 VB-1 선행·착수 조건에 로더를 넣을지 확인한다(계획 몫, S-7) |
| m-3 | 소 | 41:1248 §5.10 | «호출 경로(유지): `find_front` → `layer0_start` → `layer0_budget` → …»가 D-13이 새로 적은 사실(U15 전체판 master 미병합, F-LA6)과 어긋난다. 엔진에 `layer0_budget` 없음 | 861·1135와 같은 표지(«옛 U15 전체판 기준 -- master 미병합, 계획 F-LA6; card LA-1이 구현»)를 단다 |
| m-4 | 소 | 40:1247 머리, 40:1722 R9, 40:2075 U7, 42:265 D-GB8a | DC 양(방향별 최대 전류, 계획 625 'DC')을 `ls`로 표기. 계획 90 영역 개별 표기 규칙 | «DC 동작 범위 양(모듈 `ls_fields`)»처럼 영역과 모듈 이름을 나눠 적는다 |
| n-5 | nit | 40 §10.5 '피검' 표 행(2015 부근) | `oracle_judged` 점 추가가 bullet(2029)에만 있다 | 피검 칸에 «+ `oracle_judged`뿐인 `unmeasured_front` 점(P DEC-98 (6))» |
| n-6 | nit | 40:1256 | 'measure가 없으면'의 정의 없음, `kind = SPICE_ORACLE` + measure None 조합 관례 어긋남 | «`_ORACLE_ONLY` 항목이 없거나 measure None이면 -- VB-1 착수(OP-10 병합) 뒤에는 발동 0인 가드»로 적는다 |
| n-7 | nit | 40:12·41:17 Status | «계획 v6.37(사용자 결정 O-119~O-125)» -- 계획 v6.37에 O-125 언급 0(grep). O-125·O-126은 v6.38 몫 | «O-119~O-124»로, D-13 근거는 B80 증거·F-LA6로 |
| n-8 | nit | 40:1256 | spec 이름 문자열이 `_METRIC_SLEW`와 `ORACLE_ONLY_SPEC` 키 두 곳 | `DrivingDecl` 필드 이름 하나를 참조 |
| n-9 | nit | 40:1251 (나) | 해석 (a)의 따름 효과(봉인 안 된 점 S-1 notes 사유 변화) 미기록 | DE-1 변화표 원인 항목으로 적는다 |

## 9. 점수 산정

- 시작 100. M-1 −4, M-2 −4, m-3 −2, m-4 −2, nit 5 × −0.2 = −1 → **87**
- D-1~D-13 정정 완전성·계획 뜻 일치·이름 위임 범위·이름 충돌·표 형식·CRLF·front matter는 모두 감점 없음.
