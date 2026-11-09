# xrunf1b (XRUN-F1 card B, 레이아웃 블록 재작업) design↔구현 gap 분석

- 대상: `integ/xrunf1b-r5` da38429f (worktree `C:/Users/HSLEE/Documents/Todoc/fpga/wt/xrunf1b-integ5`), base 2305e587
- design: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` v1.11.2 §2.4.8 행 549~556, §2.4.14 파일 표 881~891, (4) 삭제 목록 908~911
- 분석자: gap-detector(작성자와 독립, 읽기 전용, 정적 분석만). 2026-10-20

## 일치율
- 항목 일치율: 20 항목 중 일치 17, 부분 3, 누락 0, 다름 0 -> (17 + 3×0.5)/20 = 92.5%
- 가중 Overall(비프론트엔드 식: 구조 0.10·기능 0.20·계약 0.20·의도 0.35·행동 0.15): 구조 100, 기능 95, 계약 95, 의도 100, 행동 90 -> **Overall Match Rate 96.5%**
- 코드 쪽 의미 이탈(as-built 결정) 0 건. gap 은 모두 design 문언 정밀도 또는 문서 한 줄 수준

## 항목 대조
| # | design 근거 | 구현 | 판정 |
|---|---|---|---|
| 1 | §2.4.8 549 `ly_point` = `ConservedPoint`, W 없음 | layout/run.py:58, contract_output.py:33 | 일치 |
| 2 | 550 `ly_slice_density` 정식 블록, READS `ly_point`·`ly_pdk`, 추가 인자 `_LutHandle` 하나, 입구 fp 검사 | run.py:70-92, :112-113 | 일치 |
| 3 | 551 `ly_device` 삭제, 네 필드로 칸 분할(사본 0) | run.py:56-67, _ly_fields.py:55-65 | 일치 |
| 4 | 552 `ly_attrs` = `DeviceAttrs(W_m, body, diode)` | contract_output.py:56-61, run.py:61 | 일치 |
| 5 | 553 `ly_pins` = `DevicePins(drain, gate, source)`, body 없음 | contract_output.py:46-52, run.py:59 | 일치 |
| 6 | 554 `ly_w_adjustable` bool | run.py:60 | 일치 |
| 7 | 555 `canon_tables`(writer `ly_canonical_naming`) READS 7·WRITES 2, 새 파일, `_Source`·`_marks`·`_build` 이동, `rejected` 인자 삭제, 정준 위치 1회, W 표지 = `ly_attrs.W_m` | canon_block.py:63-149 | 일치(설계에 없는 비공개 `_Device`·`_canon` 추가 -- 아래 G-4) |
| 8 | 555 `canonical_names` 는 번역만, docstring :1·:3 | canonical_naming.py:1-32 | 일치 |
| 9 | 556 세 블록 READS | finger_candidates.py:36, pattern_select.py:281-284, rows.py:276-279 | 일치(rows 의 `ly_rejected` 제거 확인) |
| 10 | 884 `_ly_fields` 상수·INPUT_FIELDS·LY_WRITERS·BLOCK_WRITERS 맨 앞 WRITER_CANON·F_DEVICE 삭제 | _ly_fields.py:27-83 | 일치 |
| 11 | 887 `_input_columns`·`_BLOCKS`·docstring 3·4 | run.py:10-18, :52, :56-67 | 일치(:11 '블록' 단어 -- G-5) |
| 12 | 888 `outputs.py` 가 `ly_point`·`ly_attrs` 읽음 | outputs.py:45-46, :59, :71, :76-79 | 일치 |
| 13 | 889 공개 export `F_POINT`, effective_placement, convergence CONTRACT:59·63 | layout/__init__.py:5·27·42, effective_placement.py:5·13·29, convergence/CONTRACT.md:59·63 | 일치 |
| 14 | 890 layout CONTRACT 갱신 | layout/CONTRACT.md:188-189, 211-213, 281-287, 297, 425, 462-469, 475 | 부분(:456 '네 계산 블록' 낡은 수 -- G-3) |
| 15 | 883 `_module_map`·`_helpers_alias` docstring | _module_map.py:163, :1013-1017; _helpers_alias.py:4 | 일치 |
| 16 | 878 함수 레지스트리 §2 | function-registry.md:70 | 일치 |
| 17 | §2.4.14 (4) 908~911 삭제 이름 | 엔진 소스·CONTRACT 0; tests/structure/test_removed_names.py:33-35 만 남음(부재 검사 목록) | 부분(design 범위가 tests/ 포함 '없음' -- 예외 문언 없음, G-2) |
| 18 | 556 W-1~W-4 완료 조건 | tests/layout/test_run.py test_w1/w2/w3, 감사 판정 V10 | 부분(W-2 문언 -- G-1) |
| 19 | O-19 (1) '쓴 순서' 단언 삭제·RunCounters 이전 승인 | .ai/approvals/20261019-xrunf1b-o19-order-assert.md, 엔진에 `computed_blocks` 0 | 일치 |
| 20 | `LayoutResult` = (snapshot), 계수는 `RunCounters` | contract_output.py:399, run.py:19 | 일치 |

## gap 표
| id | 심각도 | 내용 | 조치 |
|---|---|---|---|
| G-1 | 중요(design 문언) | design 40 행 556 (W-2) 'layout_outputs 의 devices·w_requests W_m 은 새 값' -- `WRequest` 에는 `W_m` 칸이 없다(contract_output.py:110-117: device·W_old_m·W_new_m·reason·group). 참고 W 에서 오는 요청은 outputs.py:59 `no_usable_slice`(W_old_m = W_new_m = 참고 W_m) 하나뿐이고 그룹 요청·finger_quantization 은 계산 필드에서 와서 두 실행에서 같아야 한다. test(test_run.py:967-973)의 해석은 design 취지와 맞고 구현과도 맞다. 문언만 구현과 다르므로 S-7 에 따라 design 을 먼저 고친다 | 아래 수정 문안 1 |
| G-2 | 경미(design 문언) | §2.4.14 (4) 908 행 범위 '엔진 전체(소스·CONTRACT·tests/)' 남는 곳 '없음' -- 부재 검사 test 자체가 이름을 담는다(test_removed_names.py:33-35). 감사·오케스트레이터 예외로 처리됐지만 design 에 예외가 없다 | 아래 수정 문안 2 |
| G-3 | 경미(계약 문서) | layout/CONTRACT.md:456 '네 계산 블록 호출에 그대로 쓴다' -- 지금은 여섯 블록(같은 파일 :469 '여섯 모두') | '여섯 계산 블록(슬라이스·정준 별칭표 포함) 호출에 그대로 쓴다' 로 (code 쪽 문서 정리) |
| G-4 | 경미(범위 밖 추가, design 미기재) | design 파일 표에 없는 정의: `layout/_helpers_pattern.py:18-35` `DeviceView`·`device_views`(pattern_select·rows 가 `ly_point`·`ly_pins`·`ly_w_adjustable` 를 읽어 합치는 읽기 전용 값, graph 필드 아님), `canon_block.py:43-60` `_Device`·:106 `_canon`. 의미는 design 과 같다(사본 필드 아님, 블록 안 조합) | 아래 수정 문안 3(design 파일 표에 기재) |
| G-5 | 경미(문서 한 단어) | layout/run.py:11 '(장치 단위 별도 블록 없음, ...)' -- 지운 것은 `ly_device` **필드**. CONTRACT.md:462 는 '필드'로 정확 | '블록' -> '필드' (다음 문서 정리 때) |
| G-6 | 참고(검증 못 함) | contract_output.py:111 `WRequest` docstring '`W_old_m` = 그 폭 슬라이스의 W_need' 는 `no_usable_slice` 요청(W_old_m = 참고 W)과 맞지 않는다. base 에서 이미 그랬는지 확인 안 함 | G-1 고칠 때 같이 확인 |

## 필요한 design 수정(정확한 문안)
1. 행 556 (W-2) 중 '그리고 `layout_outputs`의 `devices`·`w_requests` `W_m`은 새 값이다(출력 파생은 다시 만든다)' 를 다음으로 바꾼다:
   '`layout_outputs`는 다시 만든다(출력 파생): `devices`의 `W_m`(참고 W)은 새 값이다. `w_requests` 중 참고 W에서 오는 요청 -- `ly_finger` 값이 없는 소자의 `no_usable_slice`(`WRequest(device, W_old_m = W_new_m = 참고 W_m, …)`, `E/layout/outputs.py:59`) -- 의 `W_old_m`·`W_new_m`은 새 값(2배)이고, 계산 필드에서 오는 나머지 요청(`ly_groups`의 그룹 요청, `ly_finger`의 `finger_quantization`)은 두 실행에서 같다(`WRequest`에는 `W_m` 칸이 없다)'
2. §2.4.14 (4) 908 행 '남아도 되는 곳' 칸 '없음' 을 다음으로 바꾼다:
   '부재 검사 test의 검사 이름 목록(`tests/structure/test_removed_names.py`)만. 계약 입력 클래스 이름 `LayoutDevice`는 남는다(다른 이름)' -- 911 행 '없음'도 같은 예외를 따른다고 한 줄 덧붙인다.
3. §2.4.14 파일 표 886 행(세 블록) 변경 칸 끝에 덧붙인다:
   '. `pattern_select`·`rows`가 같이 쓰는 소자 칸 읽기는 `layout/_helpers_pattern.py`의 `DeviceView`·`device_views(projection, adjustable=False)`(읽기 전용 조합 값, graph 필드 아님 -- 칸은 각 필드에 한 번만)로 한다'
   그리고 881 행(canon_block) 변경 칸 끝에 덧붙인다: '. 블록 안 조합 값 `_Device`(네 필드 칸을 이름 하나로)와 별칭 충돌 검사 `_canon`을 이 파일에 둔다'

## graph 정본·소비 확인
- 새/바뀐 필드: `ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`(입력 필드), `ly_canon`·`ly_canon_rows`(계산 필드), `ly_device` 삭제.
- 엔진 소비자(tests 제외, 정적 확인): ly_point = run.py `_slice_block`·canon_block·finger_candidates·_helpers_pattern.device_views(pattern_select·rows)·outputs·convergence/effective_placement; ly_pins = canon_block·device_views; ly_w_adjustable = canon_block·device_views(adjustable=True, pattern_select); ly_attrs = canon_block·outputs; ly_canon = pattern_select(`@canonical_names()`); ly_canon_rows = rows(`@canonical_names(rows=True)`); ly_rejected = pattern_select:294(rows 에서 빠져도 소비자 있음).
- 소비자 0 인 새 필드 0, 출력 전용 선언 필요 0. 단일 정본 위반(같은 칸 두 필드) 0 -- `DeviceView`·`_Device` 는 필드가 아닌 블록 안 조합 값. `ly_point` 의 `dc_op` 사본 부채(O-27, LI-1)는 기존 1건 그대로, 새 사본 0.

## 하지 않은 것
- 실행 검증 0(test·W-1~W-4 측정·G-10 계수는 감사 기록 xrunf1b.json 을 참고로만 봄, 증거로 쓰지 않음).
- card B 의 레이아웃 밖 부분(RunCounters·donors·open_run·S3 색인·실패 부분 스냅샷·규칙 M·perf.blocks)은 대조하지 않음.
- `tests/layout/conftest.py::staged_snapshot`·`BLOCK_ORDER`·`block_objects` interface(행 556 test 도구) 대조 안 함.
- git diff --stat 전체 변경 집합 대조와 옮긴 정의의 AST 동일성은 직접 확인하지 못함(도구 제약 -- Bash 없음).
- G-6 이 base 부터 있던 문장인지 확인 안 함.
