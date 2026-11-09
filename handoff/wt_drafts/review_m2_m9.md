# 독립 검토: Phase 3 이동 card M2·M3·M4·M5·M6·M8·M9 초안 + `m2_m9_open_items.md`

검토자: 독립 reviewer(작성자 아님). 2026-10-02. 실제 저장소는 읽기만 했다(`git -C`, 시작·끝 `status --porcelain` 37줄 동일·reflog 동일·HEAD `4a286f0`).
스크래치 `C:/g251`(격리 복제본 `git clone --no-local -c core.autocrlf=false`, TMP/TEMP `C:/g251/tmp`, 작업 끝에 `C:/g251`만 삭제).
기준: gate `master` `4a286f0`의 design `30-module-split` v8.5, `draft_p3_m1.spec.md`(틀)·`review_m1.md`·`m_cards_plan.md`·`user_decisions.md` 끝.
작성자 `p3kit_m2_m9/out/`은 증거로 쓰지 않았다. 작성자 생성기(`gen226.py`·`neg226.py`·`chain226.py`)도 쓰지 않았다.

## 판정 요약

| card | 판정 | 차단 B | 수정 S | 경미 m |
|---|---|---|---|---|
| M2 | **조건부 통과** | 0 | 1 (S-1) | m-1·m-2·m-4 |
| M3 | **조건부 통과** | 0 | 1 (S-1) | m-1 |
| M4 | **조건부 통과** | 0 | 2 (S-1·S-2) | m-1·m-3 |
| M5 | **조건부 통과** | 0 | 1 (S-1) | m-1 |
| M6 | **조건부 통과** | 0 | 1 (S-1) | m-1 |
| M8 | **조건부 통과** | 0 | 3 (S-2·S-3·S-4) | m-1·m-3 |
| M9 | **조건부 통과** | 0 | 1 (S-4) | m-1·m-2·m-3 |
| open items | O-1·O-3·O-5·O-6·O-7·O-8 기본안 타당, **O-2·O-4는 사실 정정 필요**(S-1·S-2) | | | |

**모든 '재현할 수치'를 독립 사슬로 재현했다**(아래 표). 차단 결함은 없다. S는 모두 '거부해야 할 입력' 표의 자기 점검 행과 계약 3 (a) 문언 -- 판정기가 실제로 무엇을
거부하는지에 관한 것이고, 판정식·기준 변경이나 사용자 결정을 요구하지 않는다. **새 사용자 질문 0건.**

## 재측정 방법(독립)

* 사슬(내가 새로 씀): `4a286f0` → FU 대역 `c721679`(내 `stand_ins.py fu`: DR·ACF 첫 import 앞 future 한 줄 -- DR 28행·ACF 38행) → T0 W-1 대역 `298ca8e`(T0 계약 11 표대로 3파일 24행) →
  G1 시제품 `1513565`(지정된 `_drafts/g1_kit/install_proto.py`, 'installed 4') → D-11 토큰 `fb27c8a`(승인 기록 초안 49~51행 문안 그대로) → D0a 대역 `6ba0788`(`p3kit_m1/move_plan_sim.py`, `MP_STMT_KEY=names`) →
  D0b 재생성 대역 `1bb0308`(`regen_registry.py --write` one 354·nested 7·nounit 18, `보류(Phase 3)`→`보류(Phase 4)`) = M1 base.
  D0a·D0b 대역 도구는 작성자 키트 사본(사슬 입력 -- 판정 대상 아님)이고 수치는 `review_m1.md` m-4의 독립 재구현 값과 교차 확인했다.
* D0b 전 `plan`: exit 1·`reg_mismatch` 80만, 배정 403(A-4 235·A-1 61·A-5 57·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1). D0b 뒤: exit 0·일곱 0, A-4 245·A-1 61·A-5 53·A-2 39·A-6 3·A-K 2 -- 카드·`review_m1` m-4와 같음.
* 이동은 **내 생성기**(`mover.py`, card base `plan`의 `assignment`·`mod_imports`만 읽음; 머리/끝 분리 = MOD ≥ 8에서 N3.10 ≥ 7 줄, 단위 순서 TL→SD→SR→DR→ACF, W-2 머리 계산, 완전 shim = docstring·future·N3.10 import만 남김).
  내 재수출 줄 8 card × 파일 = `plan` `reexports`와 문자열 일치.
* 판정: `check`(대역), **내 계약 3 판정기**(`c3.py` -- card 문언에서 직접 쓴 `ast.dump` 열 비교, move_plan 미사용), design §10 E3_AST·E3B_AST·`import_any`를 design 파일에서 그대로 뽑아 실행,
  E3b는 card 문언대로 `stick_diagram`을 split 줄기로 바꾼 사본(`<B H>`·`<B B>`), V3/V6/V7(G1 판, gate 캐시), G1 없는 V3 대상 = `git archive 4a286f0 tools/gates`의 `changed_defs`·`mutants` 정적 계수,
  PT3(design §10 정의, junit id별), E-LIB(`e_lib.py` blob `41b72d7d…`)·E-INST(`e_inst_p3.py` `7d26134a…`, base·head 같은 체크아웃 경로).

## 재현 결과(모의 사슬 `C:/g251` -- 커밋은 작성자와 다르고 값이 같다)

| card | 단위(출처) / def | 규칙(base→head) | `mod_imports` 머리/끝 | `check` | `plan`@head | G1 없는 def·변이 | V3/V6/V7(G1) | IMPORT-ANY | E3b 사본(LIVE m/f, 새 FAIL) | PT3 id별 차이 | E-LIB/E-INST |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 18(SD10·SR7·ACF1)/16 | A-4 12·A-1 3·A-5 3 → A-0 18 | 5/0 | 11종 0, 18/18/16 | 일곱 0, 키 사상 차이 0 | 16·315 | PASS `defs` []·`moved` 16 / [] / [] | 7/7/0 | SD 10/1·0, SR 7/1·0(FAIL 9=base 9), ACF 1/0 `INVALID` | `test_ic5::test_gate_docstring_declares_blind_spots` passed→failure 1(T0 A군) | 같음, `engine_origin`만 |
| M3 | 82(SD39·SR43)/100 | A-4 48·A-1 15·A-5 10·A-2 7·A-6 2 → A-0 82 | 8/0 | 0, 82/82/100 | 같음 | 100·3052 | PASS 100 | 8/8/0 | SD 39/26·0, SR 43/22·0 | 0 | 같음 |
| M4 | 104(TL7·SR97)/126 | A-4 69·A-1 19·A-5 9·A-2 7 → A-0 104 | 10/0 | 0, 104/104/126; TL 완전 shim(3문장) | 같음 | 126·3999 | PASS 126 | 9/9/0 | TL 7/3·0, SR 97/26·0 | `test_dup_w_calc::test_size_transistor_calls_new_function` 1(T0 A군) | 같음 |
| M5 | 21(SR)/23 | A-4 11·A-1 6·A-5 3·A-2 1 → A-0 21 | 9/0 | 0, 21/21/23 | 같음 | 23·711 | PASS 23 | 10/10/0 | SR 21/9·0 | 0 | 같음 |
| M6 | 11(SR)/14 | A-4 10·A-1 1 → A-0 11 | 5/0 | 0, 11/11/14 | 같음 | 14·333 | PASS 14 | 11/11/0 | SR 11/7·0 | 0 | 같음 |
| M8 | 30(SR)/58 | A-4 17·A-1 8·A-5 3·A-2 2 → A-0 30 | 13/1 | 0, 30/30/58; SR 완전 shim(10문장, SD 줄 유지) | 같음 | 58·3077 | PASS 58 | 12/12/0 | SR 30/37·0 | `test_ts6_dead_probes::test_audit_vsb_consistency_has_operational_caller` 1(T0 A군) | 같음 |
| M9 | 16(SD8·DR6·ACF2)/16 | A-4 8·A-5 4·A-1 3·A-2 1 → A-0 16 | 8/1 | 0, 16/16/16; DR 완전 shim(4문장) | 같음 | 16·307 | PASS 16 | 13/13/0 | SD 8/10·0, DR 6/5·0, ACF 2/0 `INVALID` | 0 | 같음 |

* PT3: 9개 상태 모두 수집 id 1062(1047 passed·15 xfailed가 M1 base), 차이는 표의 T0 A군 셋뿐 -- 카드 '재현할 수치'의 id·결과와 같다.
  **T0 시제품(`p3kit_t0/install_t0_proto.py`)을 9개 상태 각각에 얹어 A군 3파일만 PT3로 돌리면 모두 141 passed** -- 계약 6 (a) '실패 0(T0 병합 뒤)' 전제가 이 사슬에서 성립한다(O-7 확인).
* E3: M1 base~M6 `stmt` 70·`call` 9·밖 66파일, M8 병합본 69·9·65(차 = SR 1411행 `from topology_library import` 삭제 -- M8 계약 8 (a)), M9 69·9·65 불변. `import_layering`: M1~M8 발견 0, M9 2(큰 번호 import `MOD7→MOD9` 1 + 순환 1).
* E-LIB `hash` `1d2e3bf6…` 9개 상태 같음, E-INST `raw_sha256` 파일럿 `2fc426d9…`·`folded_cascode` `ef3cd996…` 같음, 다른 키는 `engine_origin`뿐(새 MOD 포함·전부 iso 안), stdout(`elapsed` 가림) 같음.
* V4: M4 병합본에서 `--interface-card`(생성된 카드 -- 기존 함수 행 2) 단독·`--subject` 단독·둘 다 모두 PASS `files` [].
* 계약 3(내 판정기): 8 card 모두 (a) 문장 열·(b) split 파일 열·(c) future 첫 문장 일치. 단 **M8·M9는 (a)를 card 문언 그대로 읽으면 불일치**(S-3).

## 탐침(병합본 사본에 변형 하나씩 커밋 -- `check` + 내 계약 3 + IMPORT-ANY + ACF 밖 cwd 로드)

| 변형 | card | `check` | 계약 3 | IMPORT-ANY | ACF 밖 cwd | 비고 |
|---|---|---|---|---|---|---|
| W2a ACF 재수출을 `sys.path.insert` 앞 | M2·M9 | 0 | (b) ACF 불일치 | 통과 | `ModuleNotFoundError` | card R-W2 그대로 재현 |
| W2b `sys.path.insert`와 `from stick_diagram import load_topology` 사이 | M2 | 0 | (b) 불일치 | 통과 | **성공** | 계약 10 첫 구절('load_topology 줄 뒤')·3 (b)만 거부 |
| W2c ACF 파일 끝 | M2 | 0 | (b) 불일치 | 통과 | 성공 | 같음 |
| CROSSORDER(MOD2 안에서 SD 단위를 SR·ACF 단위 뒤로, 바이트 불변) | M2 | 0 | (a) 열 불일치, 다중집합·파일별 순서는 일치 | 통과 | 성공 | m-2 |
| COMOVE(다른 MOD 배정 순수 함수 동반 이동: M2·M4 `_lerp`→, M6 `_score_floorplan`→) | M2·M4·M6 | **`move-set` 1만** | (a) 불일치 | 통과 | -- | S-1: O-2 기본안이 맞다 |
| CACHEDUP(SR에 `_KNEE_L_CACHE: dict = {}` 남기고 재수출에서 뺌 -- 객체 둘) | M4 | `move-set` 3·`move-rejected` 3·`changed` 3·`lost` 2·`rebind` 3·`shim` 1 | (b) 불일치 | 통과 | -- | 거부됨 |
| **USERBACK(캐시는 MOD로, 사용 함수는 SR에 남김)** -- M4 `knee_L_for_kind`, M8 `achievable_metric_bound` | M4·M8 | **`cache` 1** + `move-set`(+`rebind` 등) | 불일치 | 통과 | -- | S-2 |
| SHIMKEEPIMPORT(TL 완전 shim에 `import math`) | M4 | `shim` 1 | (b) 불일치 | 통과 | -- | |
| SHIMKEEPIMPORT(SR 완전 shim에 `from topology_library import …`) | M8 | `shim` 2 | (b) 불일치 | 통과 | -- | |
| **SHIMDROPSD(SR 완전 shim에서 base `from stick_diagram import (…)` 삭제)** | M8 | **0** | (b) 불일치 | 통과 | -- | PT3 수집 오류(`test_selftest_sizing_recipe.py`)·E3b SR 사본 새 FAIL(`load_topology` 등 probe 다수)로도 거부 |
| **SHIMDROPSD(DR 완전 shim에서 `from stick_diagram import load_topology, _audit_result_json` 삭제)** | M9 | **0** | (b) 불일치 | 통과 | 성공 | **PT3 차이 0·E3b DR 사본 PASS -- 계약 3 (b)만 거부**(S-4) |
| TAIL2HEAD(MOD8 끝 SD import를 머리로) | M8 | 0 | **(a)만** 불일치 | 통과 | -- | O-8·S-3 |
| 같은 변형을 M9 상태의 MOD8에 | M9 | 0 | -- | **통과** | -- | MOD8 머리 배치는 M9에서도 동작상 무해 -- 판정은 끝까지 M8 계약 3 (a) 하나 |
| TAIL2HEAD(MOD9) | M9 | 0 | (a) 불일치 | `FAIL instance_report_builder` | -- | card R-D22 재현 |
| SDREX2HEAD(SD의 MOD9 재수출을 SD 머리로) | M9 | 0 | (b) SD 불일치 | FAIL 5(ACF·DR·MOD8·SR·SD) | `ImportError` | D-22 (1) -- IMPORT-ANY가 거부 |

## 발견

### S-1 (M2·M3·M4·M5·M6) R-6 행이 `move-set`(배정 밖 이동)을 깨우지 않는다 -- 표와 open item O-2가 서로 다르다
card 표 R-6은 `sizing_recipe.py::_base_stack_id`(모듈 전역을 읽는 함수)를 골라 기대를 `move-rejected`·`changed`·`lost`·`rebind`·`shim`으로 적었다. 그러면 R-6이 증명해야 할
"이관표 밖 단위를 함께 옮기면 `check` `move-set`이 잡는다"가 M2~M6 어디서도 실행되지 않는다(`move-set`은 R-1·R-4·R-5에서 부수적으로만 뜬다). O-2 기본안은 "auditor는 모듈 전역을 읽지 않는
함수를 골라 `move-set`을 깨운다"인데 표는 그 반대 값을 적어 test-first 실행자가 어느 쪽을 기대로 쓸지 정할 수 없다.
**실측**: 순수 함수 동반 이동 -- M2 `_lerp`(→`topology_authoring`), M4 `_lerp`, M6 `_score_floorplan` -- 셋 다 `check` `move-set` 1만(다른 발견 0), 계약 3 (a) 불일치, IMPORT-ANY 통과.
후보(내 계산, 그 card base에서 전역 읽기 0·데코레이터 없음·다른 MOD 배정): M2~M5 `sizing_recipe.py::_lerp`(MOD6 배정), M6 `_score_floorplan`(MOD8), M3도 `_lerp`.
**고칠 것**: M2~M6 표 R-6 변형을 위 순수 함수로, 기대 = `check` `move-set` 1 + 계약 3 (a)로 바꾼다(지금 `_base_stack_id` 행은 'M-4 연쇄 모양'의 보조 행으로 남겨도 됨). O-2의 '초안 표는 둘째 판 측정값' 문장은 지운다.

### S-2 (M4·M8, open item O-4) R-CACHE 행이 `cache` 판정을 깨우지 않고, O-4의 근거 문장은 사실이 아니다
card R-CACHE는 '캐시만 SR에 남기고 사용 함수는 옮김'이라 사용 함수가 M-4로 거부되어 `cache`가 0이다. O-4는 여기서 "`cache`가 단독으로 FAIL하는 모양은 이관표 배정이 갈려야 생기므로
D0b `plan`에서 먼저 막힌다"고 결론냈다. **반대 방향(캐시는 계획대로 MOD로, 사용 함수는 SR에 남김)은 code-author 실수만으로 생기고 `cache`가 실제로 뜬다**:
M4 `knee_L_for_kind`를 SR에 남긴 변형 `cache` 1(+`move-set` 2 등), M8 `achievable_metric_bound` 변형 `cache` 1·`move-set` 1·`rebind` 1. 즉 계약 7의 '`cache` 발견 0이 판정이다'는
공허한 문장이 아니고, 자기 점검이 그 판정기를 실제로 거부하게 만들 수 있다(메모리 원칙 '게이트는 실제로 거부함을 먼저 확인').
**고칠 것**: M4·M8 R-CACHE 행 변형을 '사용 함수만 SR에 남김'으로 바꾸고 기대 = `check` `cache` 1(+`move-set`), 지금 행은 보조 행으로. O-4 '판정상 문제 없음' 근거 문장과
D0a interface card용 문장('캐시만 남긴 이동은 `cache`가 아니라 `move-rejected`로 거부된다')은 두 방향을 모두 적도록 정정한다(앞 방향 `move-rejected`, 뒤 방향 `cache`).

### S-3 (M8, M9는 경미) 계약 3 (a) 문언을 그대로 실행하면 정상 병합본을 거부한다 -- 그리고 M8에서는 그것이 R-D22의 유일한 판정기다
M8·M9 계약 3 (a): "최상위 문장 = `mod_imports[…]` 줄을 차례로 파싱한 import 문장들 + 옮긴 단위들 + (끝) D-22 끝 import 문장들". `plan`의 `mod_imports`는 머리/끝을 나누지 않은
목록이라(끝 줄 `from stick_diagram import …`이 그 안에 있다) 문언 그대로면 끝 줄을 두 번 센다. **실측**: 내 판정기에서 문언 그대로 읽기 = 정상 병합본 불일치(M8·M9 `a_literal_reading_matches` False),
'머리 = `mod_imports` − D-22 (2) 대상 줄, 끝 = 그 줄들' 읽기 = 일치. 머리/끝 분리 규칙은 '의도' 절에만 있다.
M8에서는 TAIL2HEAD(R-D22)가 `check`·G1·IMPORT-ANY를 모두 통과하고(이 card 병합본·M9 상태 모두) **계약 3 (a)만** 거부하므로(O-8 확인), 이 문언이 그대로 판정식이다.
**고칠 것**: M8·M9 계약 3 (a)를 "`mod_imports[…]` 중 D-22 (2) 대상(N3.10 번호 ≥ 7 모듈) **아닌** 줄을 차례로 + 옮긴 단위들 + D-22 (2) 대상 줄을 차례로"로 바꾼다.
(참고: MOD8의 머리 배치는 M9 상태에서도 IMPORT-ANY를 깨지 않는다 -- O-8의 'MOD8 → SD → MOD9 부분 초기화 위험'은 이 사슬에서 재현되지 않았다. 규칙대로 두는 기본안 자체는 design §2.2 (2) 문언이라 타당.)

### S-4 (M8·M9) SHIM (c)의 base 재수출 줄(`from stick_diagram import …`) 삭제를 `check`가 잡지 않는다 -- 거부 입력 표에 행이 없다
card는 그 줄을 남긴다고 바르게 적었고 계약 3 (b)가 그 열을 정한다. 그러나 **`check`(D0a 대역) `shim`은 이 삭제에 0**이다(SR·DR 모두). M8(SR)은 PT3 수집 오류·E3b SR 사본 새 FAIL로도 잡히지만,
**M9(DR)는 PT3 차이 0·E3b DR 사본 PASS·IMPORT-ANY 통과 -- 계약 3 (b)만 거부**한다. card 계약 7은 SHIM (c) '이름 집합 = (base 재수출) ∪ (옮긴 이름)'을 `check` `shim`이 판정한다고 적어 auditor가 (b)를 생략하면 지나간다.
**고칠 것**: M8·M9 '거부해야 할 입력'에 'R-SHIMc: 완전 shim에서 base `from stick_diagram import …` 줄 삭제 → 기대 = 계약 3 (b)(M8은 + PT3·E3b SR 사본)'을 더하고, 계약 7 SHIM (c) 문장에
'base 재수출 줄 보존은 계약 3 (b)가 판정한다(대역 `check` `shim`은 이 삭제를 보지 않음 -- 실제 D0a에서 다시 잼)'을 적는다. D0a test-author interface card에 이 모양을 알리는 것은 오케스트레이터 몫(D0a 계약 4 (c) 범위).

### 경미
* m-1 (전부) '재현할 수치'의 SR 줄 수 표기(M8 "SR는 43줄", M4 "TL는 25줄" 등)는 생성기가 주석·빈 줄을 지운 결과다. 계약은 AST라 무해하지만 code-author가 주석을 남기면 다르다 -- '관찰(주석 처리에 따라 다름)'으로 적을 것.
* m-2 (M2·M3·M9 -- 여러 파일에서 단위가 오는 card) 계약 3 (a)가 **파일 사이 단위 순서**를 정하지 않는다. 생성기는 TL→SD→SR→DR→ACF를 쓰고(m_cards_plan §3-2), 바이트 불변으로 순서만 바꾼 변형은
  `check`·IMPORT-ANY 통과, 문장 열 비교만 다르다. 순서를 계약에 적거나(권고: TL→SD→SR→DR→ACF, 파일 안은 원본 순서) (a)를 '다중집합 같음 + 원본 파일별 상대 순서 보존'으로 적는다.
* m-3 (M4·M8) 생성된 interface card가 비지 않는다(M4 `knee_L_for_kind`·`feasible_L_window`, M8 `achievable_metric_bound` -- 계약 7 문장 때문, 모듈 칸 `sizing_recipe`). V4는 세 호출 모양 모두 PASS라 무해하나
  M1의 '두 표 비어 있음(V4 subject 우회 이유)'과 다르다는 것을 '작성 전 실측 14'에 한 줄로.
* m-4 (M2·M9) W-2 계약 문언의 '`# noqa: E402`'는 AST 판정 대상이 아니다(어느 판정도 보지 않음) -- '권장(판정 아님)'으로 적을 것.

## 질문받은 탐침에 대한 답

* **R-D22(M8 머리 import 변형)**: 계약 3 (a)만 판정한다는 card 서술은 사실(실측: `check` 0·IMPORT-ANY 통과, M9 상태에서도 통과). 다만 그 (a) 문언이 지금 그대로는 실행 불가(S-3).
* **R-CACHE 'cache' 발견 0**: 그 변형에서는 사실이지만 `cache`를 깨우는 변형이 있다(S-2) -- O-4 결론 정정 필요.
* **W-2 ACF 배치(M2·M9)**: 계약 10 + 3 (b)가 거부한다. 밖 cwd 로드는 '`sys.path.insert` 앞'만 잡고 '사이'·'끝'은 성공하므로 계약 10의 '줄 위치' 구절과 3 (b)가 꼭 필요하다(지금 문언에 있음 -- 타당).
* **SHIM (c) 줄**: 남기는 것이 design §3 SHIM (b)(c)와 맞는 유일한 읽기다(SD = MOD7 → `from <MOD> import` 재수출 줄, (c) 이름 집합에 base 재수출 포함). 삭제는 S-4대로 `check`가 못 본다.

## open items O-1~O-8

| ID | 판단 |
|---|---|
| O-1 | 타당(사실 갱신, D-11 멈춤 경로는 기존 결정). 숨은 사용자 결정 없음 |
| O-2 | **결론은 맞으나 card 표와 어긋남** -- S-1(순수 함수 동반 이동 = `move-set` 1 실측) |
| O-3 | 타당 -- 동적 `getattr(sr, …)` 9줄은 V1 수집 계약 test라 PT3가 판정, E3b 사본이 정적 읽기를 덮는다(완전 shim에서 지운 import 이름 읽기도 E3b TL·SR·DR 사본 새 FAIL로 잡힘 -- 탐침 SHIMDROPSD SR에서 확인) |
| O-4 | **근거 사실 오류** -- S-2 |
| O-5 | 타당(정의상 대상 없음, 위치는 계약 10) |
| O-6 | 타당 -- gate 레지스트리 219행 목적지 칸이 원래 `stick_diagram`이라 `INSTANCE_TOP_FIELDS` SD 잔류는 레지스트리 그대로(첫 토큰 규칙, 승인된 D0a 계약 2). 관찰: 같은 행의 `INSTANCE_SIZING_FIELDS`는 A-5로 MOD9에 가서 D0b 뒤 그 행이 둘째 이름 위치를 틀리게 말한다(REG-DEST는 첫 토큰만 봄) -- `m_cards_plan` B-1(레지스트리 칸 모양) 백로그에 더할 것. 사용자 질문 아님 |
| O-7 | 타당 -- T0 시제품을 얹으면 9개 상태 모두 A군 3파일 141 passed |
| O-8 | 사실 맞음(M9 상태에서도 무해). 판정 문언은 S-3 |

**진짜 사용자 질문: 없음.** S-1~S-4·m은 모두 card 문언·자기 점검 행 정정(판정 기준 강화 또는 서술 정정)이고 design·승인 범위 안이다.

## 정리

스크래치 `C:/g251` 삭제. 실제 저장소 `status --porcelain`(37줄)·reflog·HEAD(`4a286f0`) 시작과 같음(쓰기 0 -- 이 파일만 `_drafts`에 새로 씀).
참고(절차): 이 환경에서는 `export`한 변수가 하위 `bash`에 전달되지 않아 처음 병렬 탐침이 한 복제본에서 겹쳤다 -- 그 결과는 버리고 복제본 경로를 인자로 넘겨 다시 쟀다(위 표는 다시 잰 값만).
