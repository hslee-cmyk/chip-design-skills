# 계획 v6.38.3 독립 검증 12 (열셋째 커밋 de252a42, 부모 47866c4b, 판 기준 9d153f2f)

- 검증자: 독립 검증 12. 작성자도 이전 검증자도 아니다. 작성자 보고(history 열셋째 행, 자진 보고 포함)는 증거로 쓰지 않고 다시 쟀다.
- 읽기 전용이다. git은 `set -e` + `git -C`만 썼고 reset·checkout·stash는 쓰지 않았다. 끝난 뒤 상태는 다음과 같다.
  - `wt/plan-v6383`: status 0줄, HEAD de252a42
  - `wt/integ-it12`: status 0줄, HEAD d759838a (grep·읽기만)
- 약어
  - 계획 문서: GB = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, GC = `graph-consumption.plan.md`, HC = `headroom-chain.plan.md`, OS = `offset-strategy.plan.md`, OT = `offset-trim.plan.md`, OP = `oracle-portability.plan.md`
  - 엔진: E = `wt/integ-it12/skills/analog-gmid-design/gmid_engine`
  - 줄 번호는 de252a42 기준이다(긴 줄은 `줄:문자 위치`).
- 원자료: scratchpad `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/v12r/`
  - 파일별 `.diff`·`.wd`: 단어 단위 diff
  - `<커밋>_<계획>.md`: 9d153f2f·47866c4b·de252a42 세 시점의 본문
  - `ctx.py`: 낱말 주변 문맥 추출
- **결론: 높음 0, 중간 2(V12-M1·M2), 경미 6. 상정 불가.**

## 1. 오케스트레이터 판정 A~H 처리

| 판정 | 처리 | 근거(파일:행) |
|---|---|---|
| A 본문 정리(표지 + 옛 문언 공존 0) | 적합(경미 L-3) | GC '대체 표지'는 47866c4b 17건에서 de252a42 1건으로 줄었고, 남은 1건은 Status(GC:15)다. 본문 N3.6-3(GC:433-454)·GC-5 범위(GC:640)·완료 6(GC:677)·FR-G12(GC:114)·FR-G16(GC:118)·GC-2 범위 6(GC:390-394)·K-h(GC:540)·X-G11(GC:589)·BD-11(GC:744)·U-G13(GC:764)·GD-7(GC:778)은 모두 지금 규칙만 담는다. 옛 문언은 GC history 452행(열째)에 있다: `(가-1)` 18건·`use_macro` 19건·'지금 흐름' 5건. PR-1 절(GB:1843)은 한 줄이고 전문은 GB history 1504에 있다. DEC-64(GB:263)·DEC-92(GB:291)·OP:343도 지금 규칙 + history 지시만 남았다. 이 판에서 새로 생긴 '옛 문언' 낱말은 모두 'history' 지시다(GB 9건, HC 5건, OP 2건). 남은 꼴은 결정 기록 행의 '옛 규칙 + →'뿐이다(L-3) |
| B E-13 = DEC-67, J-E·O-109 C1 원래 취지와 다름, WB-0 | **부분 → V12-M1** | 맞게 된 자리: '입력 창의 자리' 문단 개정(GB:269:1526~), J-E·O-109 C1 표시(GB:269, GB:2344, 승인 #34), N6.1 WB-1 착수 조건 WB-0(GB:1244), 완료 grep 상수 이름(GB:2344), FD 스텝 원인 항목(GB:2289). 남은 결함 둘. (1) 개정한 문단은 DEC-70 행(GB:269)인데 'DEC-67'로 불렸다. 실제 DEC-67 행(GB:266:5767)에는 옛 규칙 'θ 고정 선형 감도 끝은 θ 변수 범위(W4 뿌리 y 창)에만'이 그대로 있다. (2) `node.dc_window` 정의 정본인 N3.8 '창 필드'(GB:651)와 IT-2·DE-1 (a) 정의가 E-13과 반대다 |
| C 판정 대상 술어 하나·사본 없음·E-03·SF-1 범위 8 일치 | 적합 | 아래 §3 |
| D OP:343 | 적합 | 예외 문장이 지워졌다. 지금 규칙(EO-1 한 자리, U-123 재측정 경로)과 history 지시만 남았다. OP:449의 `saturation_rule` 인용은 DEC-90 (1)로 바뀌었다. OP 안에서 OP-12를 활성 card로 다루는 문언은 0이다(OP:18 Status·OP:514 철회 행뿐) |
| E 승인 표 기본안 일치 | **부분 → V12-M2** | #13·#16·#20·#21·#22·#23·#27·#32~#38은 기본안이 본문과 맞다. #26 기본안 '대체 표지'만 #35 (d)·GC 0.14.4 열째 커밋(본문 교체)과 반대다 |
| F 소비자 0 칸 전부 삭제, `optional_stages` 칸째 | 적합(경미 L-4) | 아래 §2 |
| G 경미 L-1~L-7 | 적합(잔존 경미 L-1·L-2) | 아래 §4 |
| H 승인 표 갱신 | 부분(V12-M2) | 38행, #1~#38 연속, 누락 0 |

## 2. F 삭제 칸 소비자 재현(엔진 `wt/integ-it12` d759838a, `git grep -w`, `.ai`·assets·legacy·md 밖)

| 칸 | 운영 소비자(tests 제외) | 판정 소비자 | 계획 '지우면 깨지는 곳'(GB:2223) |
|---|---|---|---|
| `search_method`·`SEARCH_METHODS` | `authoring/spec_settings.py:13·35·38·104-106`(검사) | 0. `tools/spice_oracle/legacy_adapter.py:105`는 옛 엔진 인자로 이름만 같고 뜻이 다르다. LT-1 삭제 대상 | 있음 |
| `optional_stages`·`OPTIONAL_STAGES` | `spec_settings.py:35·39·108-117`, `tools/gates/source_lint.py:7·238·242`, redteam 12 `expect.json` | 0 | 있음 |
| `acceptance_rule`·`saturation_rule`·`node_compare_rule`·`device_compare_rule`·`forced_warn_rule`·`front_points_rule` | `spec_settings.py:40-46` | 0 | 있음 |
| `axis_rule`·`tie_rule`·`cycle_cap_rule` | `spec_settings.py:48-51` | 0 | 있음 |
| 섹션 `spice_check`·`front_refilter`, `RuleChoice`, 섹션 지문 | `spec_settings.py:1·5·23-24·31·221·237·244`, `spec_model.py:10·183-184·273-274·300·315-316`, `spec_load.py:146·151`, `spec_schema.py:25`, `spec_sources.py:9·47·48`, `authoring/__init__.py:58·130`, `_module_map.py:428` | 0 | 있음. 단 `spec_sources.py:47`은 빠졌다(L-4) |
| spec data | library 9·heldout 4 `*.sizing_spec.json`(13개, 칸마다 1건; `AC-3` 표지 13건) | -- | 있음('library 9·heldout 4') |
| test | `tests/authoring/*`(fixtures 2·test_spec_settings·test_spec_model·test_spec_schema·test_spec_sources·test_spec_load·test__spec_fields), `tests/generality/topogen/spec_template.py`, `tests/generality/test_spec_generators.py:7`, `tests/metrics/conftest.py:490-499` | -- | 있음. **`tests/integration/test_spec_library_load.py:42·104`**(`ID_TOTALS["AC-3"] = 9` -- pending 표지 집계)는 빠졌다(L-4) |

- 결론: 운영 소비자는 로더 검사·섹션 지문·lint 예외뿐이다. 판정 소비자는 0이다. 결정자 'graph 규칙 1·3, 같은 양의 규칙 정본이 계획에 있음'의 정본 인용도 확인했다.
  - `acceptance_rule`: DEC-90 (1)·N3.6
  - `saturation_rule`: DEC-90 (1)·봉인 9
  - compare_rule 둘: N3.6 'T8 기록만'
  - `front_points_rule`: U-45
  - `axis_rule`: DEC-79 (b)
  - `tie_rule`: DEC-80 (i)
  - `cycle_cap_rule`: N3.6 K_max
- `optional_stages` 칸째 삭제는 DEC-75(GB:274)·LA-1 범위 7(GB:1876)·V6 lint(GB:1052)·N3.15(GB:938)·MOD2(GB:709)와 맞는다. LA-1이 칸·이름·읽기·lint 예외를 함께 다시 만든다. 만들면 배선 원칙에 맞다.
- 완료 조건의 grep 대상(`SEARCH_METHODS`·`OPTIONAL_STAGES`·`SPICE_RULES`·`REFILTER_RULES`·`RuleChoice`·`spice_check_fp`·`refilter_fp`)은 실재 이름과 맞는다. 지문 `search_fp`·`spec_fp`와 `AC-3`을 비교 필드에서 빼는 처리는 타당하다.

## 3. C 술어와 엔진 judged 의미

- 엔진 의미
  - 제약 생산(E/authoring/spec_constraints.py:264-267): `judged = True if kind == user_spec else (False if pending_spice else None)`, 그다음 `metric_decision`이 있으면 False.
  - 참조 해석(E/authoring/spec_refs.py:44·86-89): `judged = target.judged ∧ (자기 metric_decision 없음)`. 대상이 다시 참조면 사슬을 따라간다. 대상이 보상 목표면 True다.
- 계획 술어(GB:2220 SF-1 범위 8, GB:2334 E-03, OS:127·197, 승인 #38): '출처 kind `user_spec`(참조는 사슬 끝 대상의 출처 kind) ∧ metric 결정 대기 아님'.
- 경계 사례를 확인했다.
  - (a) 제약 출처 kind는 {user_spec, pending_spice, reference}뿐이다(`spec_sources.py:40`). 보상 목표 출처 kind는 {user_spec, reference}다(`:41`). 그래서 보상 목표에서 끝나는 사슬은 user_spec이고 엔진의 True와 같다.
  - (b) metric 결정 대기 제약은 `metric = None`이라(`spec_constraints.py:241`) 이름으로 참조할 수 없다(`ref_unresolved`). '대상의 metric 축'이 사슬로 전파되는 경우는 생기지 않는다.
  - 결론: 두 축 술어가 엔진 의미를 빠짐없이 담는다.
- 사본: '순수 함수 한 자리, 저장 사본 없음'이고 `judged_constraints` 계산 속성이 술어를 부른다. graph 규칙 1·3에 맞는다.
- 소비 경로 목록(GB:2220)은 `git grep judged_constraints` 결과와 같다.
  - `graph/s1v_build.py:41`·`views.py:53`
  - `metrics/achievability.py:149·257·277`
  - `pipeline/stage_a.py:169`·`stage_b.py:153`
  - `search/iv_context.py:39·89`
  - `search/search_context.py:110·150·155·168·179`
- E-03 완료(GB:2334)와 SF-1 범위 8 완료(GB:2220)는 같은 조건이다: `ConstraintDecl.judged` grep 0·두 축 회귀 toy·S-10 같은 결과. 검증 11 V11-M3은 닫혔다.

## 4. headroom-chain 잔존 문언·design 인용 번호(작성자 자진 보고 확인)

- **HC:156·157·258**: '층 0 무동작 회로와 층 0 조립 실패 경로(상위 LA-Q2 (b))'가 그대로 있다. 세 줄 모두 판 기준 9d153f2f와 같다(이 판이 손대지 않음).
  - 뜻: 두 이름의 합집합은 상위 DEC-73 (3)(b) '층 0 점 없음 경로'와 같은 집합이다. 규칙 충돌은 없고 이름만 낡았다.
  - '상자 중심'도 확인했다. GB LA-1 범위 6(GB:1875)은 `_box_centre`를 이 경로의 출발점 생성으로 남긴다(빈 사다리·출발 정의 불능의 대체로만 쓰지 않음). 그래서 HC가 상자 중심을 나열한 것은 상위와 모순되지 않는다.
  - 판정: **경미(L-1)**. 이 판이 HC를 v0.7.9.3으로 이미 개정했고 GB에서 이름을 하나로 합쳤으므로(L-6) 같은 판 HC 둘째 커밋에서 맞추기를 권한다. GB 안 잔존 4곳도 함께 고친다.
    - GB:1918: LA-1 완료 항목 머리 '층 0 무동작 회로(... 이 card 규칙이 발동하지 않는 입력)'. 같은 줄 뒤에서는 '층 0 점 없음'(사유 제약 없음)으로 바꿨다.
    - GB:1943: 후속 정정 표 HC 행 '154행 출발점 경로 = 층 0 무동작 회로 + 층 0 조립 실패 경로'
    - GB:1975: LA-Q1 '층 0 무동작 회로 출발점 생성'
    - GB:1976: LA-Q2 선택지 문언. 결정 기록이라 그대로 둬도 된다.
- **자동 켬 번호**: `docs/02-design` 전체 grep에서 '자동 켬'·DEC-73 (4) (v) 인용은 **0건**이다. design 쪽 불일치는 없다.
  - 번호 재매김 뒤 남은 '(v)'는 GB:316 N2.1 O-41 행 '(1) 자동 켬 (v) = 판정 기록 발동 분기 목록 밖 분기' 하나다. 지금 DEC-73 (4)에서는 (iv)이다.
  - 그 밖은 모두 (i)~(iv)로 맞다: GB:272·274·1876·1913·1920·2003·2005, OS:260.
  - 판정: **경미(L-2)**. N2.1 결정 기록이라 번호 대신 내용('판정 기록 분기 목록 밖 분기 -- 지금 DEC-73 (4) (iv)')으로 적기를 권한다.

## 5. 결함

### V12-M1 (중간) E-13(θ y 범위 = KVL 순서 창 하나)이 DEC-67 행과 `node.dc_window` 정의 정본에 전파되지 않았다. 개정 자리는 'DEC-67'로 잘못 불렸다

- **자리**
  - **DEC-67 행(GB:266:5767, 판 무변경)**: '외층 SLSQP 커널 평가 = … 출력 스윙·측정 구성 ICMR은 봉인 뒤 … KCL 선형 감도 끝 -- …; **θ 고정 선형 감도 끝은 θ 변수 범위(W4 뿌리 y 창)에만**'. 이것은 E-13·승인 #34가 바꾼다고 적은 O-109 C1의 커널 쪽 규칙 그 자체다.
  - 열셋째 커밋이 개정한 '**입력 창(J-E·IT-2)의 자리**' 문단은 **DEC-70 행(GB:269:1526~)** 안에 있다. 그런데 다음 자리가 모두 이를 'DEC-67'로 부른다(판정 B와 검증 11의 행 표기를 따른 오기).
    - E-13 행(GB:2344) 'DEC-67 '입력 창의 자리'의 커널 쪽 … (DEC-67 같은 변경에서 개정)'
    - Status(GB:11), GB history 1504
    - 승인 #34 위치 칸
  - 결과: 같은 대상(θ 변수 범위)에 DEC-67(θ 고정 선형 감도 끝)과 DEC-70·E-13(KVL 순서 창)이 함께 걸린다.
  - **`node.dc_window` 정의 정본**(모두 판 무변경)은 θ y 범위를 포화 +tol 창으로 정의한다.
    - N3.8 '창 필드'(GB:651:42559): 'θ 프레임 탐색 창 `node.dc_window`(+tol_VDsat, `sat_threshold`, 측정 구성 없음 -- 커널 탐색; O-58 S-1)'
    - N3.8 '엔진 쪽 계산 자리'(GB:651:29200·36601)
    - IT-2 범위 1(GB:1623:5579): 'θ 프레임 탐색 창 = `node.dc_window`(노드 풀이 블록 출력, +tol …)'
    - DE-1 (a) (ii)(GB:1727:1045): '`node.dc_window` = … 엔진 판정 여유를 더한 창(VDS − VDSAT − tol_VDsat ≥ 0, `block_columns.saturation_rows` 현행 식, `sat_threshold` 정본) -- 커널 탐색이 읽는다(O-58 S-1)'
    - GB:665:449, GB:1561:232
    - 하위 계획 HC:330: 'HC-S의 `saturation_rows`는 θ 프레임 탐색 창(+tol)만이고, 그 창 필드는 `node.dc_window`'
  - 맞은편 규칙은 θ y 범위를 순서 창으로 둔다.
    - E-13(GB:2344)·WB-1 범위 3(GB:2289): 'θ y 범위 = KVL 순서 창 하나 -- 블록 안 입력 창 측정 … 삭제', `fd_jacobian.py:55`가 읽는 `node.dc_window`가 순서 창이 된다.
    - DEC-70(GB:269): '포화 거부는 봉인이 한다'
  - 엔진 사실: as-built `node.dc_window`(입력 W4 뿌리)는 '순서 창 ∩ 입력 포화 창 override'다(`E/sizing/block_columns.py:209-214` `window()`, `:784-790` `_windows`). E-13은 이 교집합의 포화 쪽을 지운다. 그러니 `node.dc_window`의 정의(+tol 포화, `sat_threshold`)가 바뀐다.
  - **원래 취지와 다름 누락**: 승인 #34·E-13은 J-E와 O-109 C1만 든다. **O-58 S-1**('θ 프레임 탐색 창 = +tol 포화 판정 여유 창, 커널 탐색이 읽음')의 θ 프레임 창 정의도 바뀌는데 표시가 없다.
- **막는 경로**
  - (a) card WB-1 범위 3 design: 같은 필드 `node.dc_window`의 정의가 둘이다(N3.8·DE-1 (a) (ii) 대 E-13). graph 규칙 3에 어긋나고 design-validator·gap 분석이 어느 정의로 판정할지 정할 수 없다.
  - (b) card DE-1 (a) 착수·완료: (ii)가 '`saturation_rows` 현행 식으로 커널 탐색 창'을 정의로 요구한다.
  - (c) headroom-chain HC-S: 범위가 θ 프레임 창의 `saturation_rows` 문턱 교체다(HC:330). WB-1이 지울 창 식을 고치게 되어 '만들고 지움'이 생길 수 있다. 순서는 IT-1·IT-2 → HC-S(GB:1632)이고 WB-1과의 선후는 계획에 없다.
  - (d) 원칙: 사용자 결정 O-58 S-1 변경이 '원래 취지와 다름'으로 승인받지 않은 채 들어간다.
- **권고**(문서만, 엔진 0줄)
  - DEC-67 행 GB:266 괄호를 'θ 변수 범위(W4 뿌리 y 범위)는 KVL 순서 창 하나(DEC-70 '입력 창의 자리', N6.35 E-13)'로 고친다.
  - E-13·Status·승인 #34·history 열셋째 행의 'DEC-67 '입력 창의 자리''를 'DEC-70 '입력 창(J-E·IT-2)의 자리'와 DEC-67 영역 원칙 괄호'로 바로잡는다.
  - N3.8 '창 필드'·'엔진 쪽 계산 자리'(GB:651 세 곳)·GB:665·1561·IT-2 범위 1(GB:1623)·DE-1 (a) (ii)(GB:1727)의 `node.dc_window` 정의를 고친다: 'W4 뿌리 y 범위 = KVL 순서 창(측정 구성 없음, tol·`sat_threshold` 없음 -- 포화 거부는 봉인)'. 측정 구성 판정 창(`node.dc_window_cfg`)·정의 창(`node.dc_window_def`) 두 필드는 그대로 둔다.
  - HC:330과 HC-S 범위가 측정 구성 판정 창 쪽 `saturation_rows`만 남는지 재확인해 HC에 반영한다.
  - 승인 #34·사용자 몫 목록의 '원래 취지와 다름'에 O-58 S-1(θ 프레임 창 정의)을 더한다.
  - 비교(물리 정합 / 손계산 속도 / design 단순성 / 실측)
    - 정본 정리: 같음(포화는 봉인이 판정) / 같음 / 필드 정의 하나 / WB-0 실측 그대로
    - 그대로 둠: ⚠ 같은 필드 두 정의(graph 규칙 3)·승인 누락

### V12-M2 (중간) 승인 #26 기본안이 '대체 표지'로 남아 #35 (d)·graph-consumption 열째 커밋(본문 교체)과 반대다

- **자리**: `wt/_drafts/evidence/2026-10-28/plan_v6383_approval_items.md` #26
  - 기본안: '대체 표지(규칙은 상위 한 자리)'
  - 내용: 'GC-2 범위 6·FR-G16·F-G20·K-h·BD-11·GD-10·완료 3 대체 표지'
- **맞은편**
  - #35 (d) 기본안 '그대로'는 '… graph-consumption … GC-2 범위 6·FR-G16·K-h·X-G11·BD-11 … 본문을 지금 규칙만으로'다.
  - 실제 본문(GC:118·390-394·540·674·744)에는 표지가 없고 '원래 취지와 다름 -- 상위 승인 표 #26'만 남았다.
  - #26은 행 수 기록('#13·#16·#20·… 갱신')에서도 빠졌다.
- **막는 경로**: 사용자는 승인 표를 행 단위로 승인한다. #26을 그대로 승인하면 같은 대상(GC-2 범위 6 등)의 형태로 '대체 표지'(O-169 위반 꼴, #16 대안 ⚠과 같은 것)와 '본문 교체'(#35 (d))를 함께 승인하게 된다. 검증 11 V11-M5(#16 '대체 표지 유지' 기본안)와 같은 유형이다.
- **권고**
  - #26 기본안 = '본문 교체(규칙은 상위 IT-1 범위 5 한 자리, 옛 문언 GC history 0.14.4 넷째·열째 행)'
  - #26 대안 = '대체 표지 유지 ⚠ O-169 표지·옛 문언 공존 / 하위 계획 '보존만' 유지 ⚠ 같은 대상 두 규칙'
  - 행 수 기록에 #26을 더한다.

### 경미

- **L-1** 옛 두 경로 이름이 남았다: HC:156·157·258, GB:1918(LA-1 완료 항목 머리)·GB:1943(후속 정정 표 HC 행)·GB:1975(LA-Q1). §4 참조. 규칙 충돌은 없고 이름만 낡았다.
- **L-2** GB:316 N2.1 O-41 행 '자동 켬 (v)'. 지금 번호는 (iv)다. design 인용 0건(§4).
- **L-3** 결정 기록 행에 옛 규칙과 화살표 갱신이 함께 있다(같은 판에서 U-51 GB:2472는 '지금 규칙 + 옛 문언 history' 꼴로 정리됨).
  - GB:2487 U-66: '정밀 경로를 선언하면 탐색 전에 `unsupported_rule_branch`로 정지한다 → … 칸 자체를 지워 로더 거부'
  - GB:1408 LT-1 순서 3 선행: '(옛 선행 '…OP-12…'은 … 삭제)'
  - GC:148 O-13 (4): 'U-G13 (가) + 아래 끝 전류 충돌 경우 (가-1)(… v6.38.3에서 한 규칙으로)'
  - 같은 꼴로 맞추기를 권한다. 판정 경로를 막지는 않는다(효과가 같거나 다음 문장이 지금 규칙을 명시함).
- **L-4** SF-1 범위 11 '지우면 깨지는 곳'(GB:2223)에 둘이 빠졌다. '착수 때 재조사'로 덮이지만 명시를 권한다.
  - `tests/integration/test_spec_library_load.py:42·104`: `ID_TOTALS["AC-3"] = 9` -- 칸 삭제로 pending 표지 집계가 바뀐다.
  - `E/authoring/spec_sources.py:47`(`spice_check` 출처 kind): 지금은 `:48`만 적혔다.
- **L-5** 승인 표 서술이 낡았다.
  - #28 위치 칸 '… 대체 표지(0.14.4 넷째·다섯째·여섯째 커밋)'
  - #23 내용 칸의 GC-2·GC-5 '대체 표지' 서술(기본안은 맞음)
  - #21 대안 '`judged`를 True로 뒤집음 ⚠ S-10 공존 검사 깨짐'(칸 삭제 뒤 대상 없음)
- **L-6** 번호·서술이 낡았다.
  - DEC-75(GB:274:1196) '화이트리스트에 **다섯째** 항목 외층 SLSQP를 더한다': 화이트리스트가 '구현된 항목만'이 되어 서수가 뜻을 잃었다. LA-1 범위 7(GB:1876)은 '항목 '외층 SLSQP''로 고쳤다.
  - N6.1 구현 단위 2(GB:1215) '`optional_stages` 화이트리스트': 칸 삭제 뒤 서술이 낡았다.

### 판 밖 참고(이 판 결함 아님)

- GB:1857 F-LA5는 '`common_gate_amplifier`·`folded_cascode` gain 제약 없음(층 0 무동작)'이라 적는다. 실측으로는 두 회로 모두 `gain_ss_db`를 선언한다(`assets/library/*.sizing_spec.json`). 판 기준 9d153f2f부터 있던 사실 행이고 U-56 '발동 0'(GB:2477)과 어긋난다. 다음 판 사실 갱신 대상이다.

## 6. 오적용 점검(`git diff -U0 47866c4b..de252a42` 모든 hunk)

- 방법: 파일별 hunk를 단어 diff로 읽고, 각 hunk의 행 머리(DEC·card·N 절·표 행)를 의도한 자리와 대조했다.
  - GB 40 hunk: Status 11, DEC-64 263, DEC-70·71 269-270, DEC-73 272, DEC-75 274, DEC-92 291, N2.1 O-169 387, MOD2 709, N3.15 938, V6 1052, 공격 12 1080, N6.1 WB-1·SF-1·LA-1 1244·1247·1254, 선후 1266, IT-1 범위 5 1587, FX-1 1779, PR-1 1843, LA-1 범위 6·7·9·완료·선행·병렬 1875-1930, 후속 정정 1947-1948, LA-Q2 1976, LA-2 2003·2005, 순서 2071, SF-1 범위 8·11 2220·2223, WB-1 범위 3 2289, N6.35 머리·E-03·E-04·E-05·E-13·E-19·E-24·E-32 2328-2363, design 범위 2611
  - GC 18 hunk: Status·FR-G12·FR-G16·O-13·GC-2 범위 6·N3.6-3·K-h·X-G11·GC-5 범위·LA-1 대응·완료 3·완료 6·BD-11·U-G13·GD-7
  - OS 5, OT 2, OP 3, history 6행 추가
- **의도 밖 자리 편집: 0건.** 모든 hunk가 판정 A~H와 경미 L-1~L-7의 지정 자리다. Status 줄 오편집은 없다.
- numstat(일반 = `--ignore-cr-at-eol`)
  - GB +47/−55, GC +37/−53, OS 5/5, OT 2/2, OP 3/3, history는 추가만(GB·GC·OS·OT 각 1, OP 2)
  - CRLF 줄 수 = 전체 줄 수로 파일마다 보존됐다: GB 2647→2639, GC 811→795, 나머지 불변
  - 전체 줄 교체와 줄끝 변환은 0이다.

## 7. 원칙 전수(열셋째 커밋 변경)

| 원칙 | 판정 |
|---|---|
| graph 단일 정본 | 술어 한 자리·저장 사본 0(적합). 소비자 0 칸 삭제는 같은 정의의 둘째 자리를 없앤다(적합). **M1**: `node.dc_window` 정의가 둘이고 DEC-67 대 DEC-70 규칙이 둘이다 |
| O-169(유지 근거 '현' 금지, 표지 공존 금지) | GC·GB 본문 정리 적합. E-24 `not_run` note 유지 근거는 'DEC-79 판정 축 미실행 사실(fail-closed 신호)'이라 물리·원칙 근거다(적합). 잔존: M2·L-3 |
| 만들면 배선 | `optional_stages` 칸·lint 예외는 LA-1 범위 7이 읽기와 함께 다시 만든다(적합) |
| fail-closed | 지운 칸 선언 → 로더가 모르는 키로 거부(적합). 술어가 엔진 의미와 같아 판정 대상 집합 변화 0(적합) |
| 물리 결정자·상수 발명·회로 이름 | 새 상수 0, 회로 이름 0. SF-1 범위 11은 칸마다 정본 결정을 인용(적합) |
| as-built 근거 | 엔진 grep은 소비자 확인으로만 썼고 규칙 근거로 쓴 곳은 0이다 |
| 원래 취지와 다름 | #34에 O-58 S-1 누락(M1). 나머지(#26·#32~#38) 표시 있음 |

## 8. 문서 일관성

| 항목 | 판정 |
|---|---|
| Status·version | GB:11 열셋째 서술. GC:15 0.14.4 열째, OS 0.7.4 둘째, OT 0.6.2 둘째, OP 0.6.21 둘째. HC는 이 커밋 무변경(L-1). 'DEC-67' 오기(M1) |
| history | GB 1504·GC 452·OS 373·OT 229·OP 2행이 바꾼 구절 원문을 담는다: GC 행 `(가-1)` 18·`use_macro` 19, GB 행 PR-1 절·DEC-64·DEC-92·E-03·E-05·자동 켬 원문 |
| N2.1 | O-169 행(GB:387) 위치 칸 'SF-1 범위 8·11·PR-1(철회)' 적합(검증 11 L-5 닫힘). O-41 행 '(v)'(L-2) |
| N7.2 | 이 커밋 무변경. U-66 꼴(L-3) |
| 순서표 N6.1 | WB-1 착수 조건 WB-0(GB:1244), SF-1 범위 11 문언(GB:1247), LA-1 착수 조건 '층 0 점 없음 경로'(GB:1254) 적합 |
| 승인 표 | 38행, #1~#38 연속, 누락 0. 기본안 불일치 #26(M2). #34 원래 취지와 다름 누락·위치 오기(M1). 낡은 서술 #21·#23·#28(L-5) |

## 9. 검증 1~11 적합 항목 회귀

- 이 커밋의 hunk 58개(GB 40, GC 18)와 하위 계획 10개를 모두 읽었다.
- E-31·E-32 본문(E-32는 꼬리 '열째' 한 낱말만 바뀜), DEC-106, GC-5 칸 0 한 규칙(GC:439 글자 불변), U-51(GB:2472), E-34·E-35, SF-1 범위 9·10, IT-1 범위 5 규칙은 바뀌지 않았다.
- 검증 11 적합 판정 자리(E-34·E-35·U-56·`exclude_nets`·#13·#16 본문)도 회귀가 없다.
- **회귀 0.**

## 10. 상정 판단

중간 2건이 남아 **상정 불가**다. 둘 다 문서 수정으로 닫힌다(엔진 0줄).

- **V12-M1**
  - DEC-67 행(GB:266) 괄호를 E-13대로 고친다.
  - '입력 창의 자리' 위치 표기를 DEC-70으로 바로잡는다(GB:2344·GB:11·승인 #34·history).
  - N3.8 '창 필드'·'엔진 쪽 계산 자리'(GB:651)·GB:665·1561·IT-2 범위 1(GB:1623)·DE-1 (a) (ii)(GB:1727)·HC:330의 `node.dc_window` 정의를 KVL 순서 창으로 바꾼다.
  - #34에 O-58 S-1을 더한다.
- **V12-M2**: 승인 #26 기본안·대안을 본문 교체 기준으로 뒤집는다.

경미 L-1~L-6을 함께 처리하면 다음 검증의 종료 기준을 충족할 것으로 본다.
