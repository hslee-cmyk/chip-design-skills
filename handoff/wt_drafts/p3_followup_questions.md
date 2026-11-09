# Phase 3 후속 결정 -- M1-2·W-1·W-2·F1/TS6 (M1/M4 착수 전 묶음 질문)

작성 2026-10-02. 기준 gate `master` **`36e170e`**(= 로컬 `master`, design 30 v8.5 승인본·승인 기록 `20260930-30-module-split-design`).
근거: design §2.2·§3 SHIM·§6.2·§7.1·§8(D0b·M행)·D-11·D-22·D-27, 승인 기록 29·133행("이동 도구가 실제 코드에서 추가 표 개정을 계산하면 그때 다시 묻습니다" -- 위임 없음),
`_drafts/m_cards_plan.md` W-1·W-2·W-4, `draft_p3_m1.spec.md` '결정 필요 항목' M1-2, `review_d0a.md` 39~44·114행, `draft_p3_d0a.spec.md` 계약 2·4.
F1 spec 초안(`draft_p3_f1.spec.md`)은 아직 없다 -- F1/TS6 항목은 gate master 소스로 직접 쟀다.

**재측정(전부 이 작업에서 다시 잼, 관찰)**: 스크래치 `C:/g215`(격리 복제본 `--no-local`, origin 제거, 빈 hooksPath -- 실행 뒤 삭제), 키트 `_drafts/p3fq_kit/`
(측정 전용 -- 역할 산출물 아님, test-author·code-author·auditor에게 건네지 않는다), 원자료 `p3fq_kit/out/`.
M1 base 대역 = `36e170e` + FU 대역(DR·ACF docstring 뒤 future 한 줄, `fu_standin.py`) + G1 시제품(`g1_kit/install_proto.py` -- `mutate_changed.py`·`rt.py` 앵커가 면제 묶기(34)로 바뀌어
그 두 파일만 `dd60db6` 판에 설치; `plan`이 쓰는 `reachability`·`import_layering`·`role_paths`는 `dd60db6..36e170e` diff 0) = 복제본 커밋 `4173db0`(재생성 전).
`plan` = `p3kit_m1/move_plan_sim.py`(D0a 계약 2 재구현 시제품), 인자 = design §6.3 `MP_ARGS`(`p3kit_m1/mpargs.sh`). N3.10 표는 gate master에 UD-0 개정이 이미 들어 있다.

---

## 0. 요약(분류)

| 항목 | 분류 | 사용자 질문 | 묶음 |
|---|---|---|---|
| **M1-2** `_QUERY_CACHE_MAX`(문장 키 = 바인딩 이름) | (ii) N3.10 표 개정 = D-11 별도 승인(design이 정한 멈춤 경로) | **Q1** | M1 전(D0b 전) |
| 오케스트레이터 추가 -- 277행 이름표 정정(②)이 '사실 오류 정정'인가 | ②는 순수 오기 정정이 아님(감사 원자료가 그 행에 상수를 함께 적음) → 배정 변경 = Q1의 선택지 | Q1 안 | 〃 |
| **W-1** 완전 shim과 selftest import | (ii) 판정 기준(SHIM (b)) 또는 test 변경(V5) -- 어느 길이든 사용자 몫 | **Q2** | M1 전(T0 범위) / 늦어도 M4 전 |
| **W-2** ACF 재수출 줄 위치 | (i) design 안 -- §2.2 목적문이 위치를 정한다. card 계약·생성기 문언만 | 없음 | M2·M9 spec |
| **F1/TS6** `test_ts6_probe_relocate` | (ii)지만 F1 V5 질문에 묶는다(착수 조건 = F1) | (Q3 초안, 지금 묻지 않음) | F1 전 |
| (덧) 레지스트리 이름 칸 `A`/`B` 읽기 | (i) D0a 계약 2 문언 명확화(첫 토큰) | 없음 | D0a spec |

M1-1(MOD 파일 모듈 docstring 없음)·M1-3(E3·E3b card 단위 사용, 강화)은 M1 spec 기본안 그대로 (i) -- 이 문서에서 다시 다루지 않는다.

---

## 1. M1-2 -- 문장 단위 키와 `_QUERY_CACHE_MAX` (Q1)

### 1.1 사실(gate master `36e170e` 재측정)

* **키 정의는 승인 범위 안에서 이미 정해져 있다**: design §8 D0b행 "키 정의는 D0a 계약 2", design 개정표 1275행(2차 검토 S7 "문장 단위 키 정의"), D0a 초안 계약 2
  "문장 = 그 문장이 바인딩하는 이름을 이름순으로 `,`로 이은 것". 시제품의 `<stmt:해시>` 키는 '시제품 한계'(D0b spec)다 -- **키를 해시로 되돌리는 것은 선택지가 아니다**(design 기준 변경).
* `plan` 네 판(`p3fq_kit/out/plan_*.summary.json`, 배정 403 모두 같음):

| 판 | 키 | `upward` | `cycles` | 그 밖 다섯 목록 | MOD1 단위 | MOD4 / MOD8 / MOD9 / SD |
|---|---|---|---|---|---|---|
| hash(시제품 = D0b 키트·design F5v85 수치) | `<stmt:해시>` | 0 | 0 | `reg_mismatch` 79, 나머지 0 | 8 | 102 / 32 / 17 / 110 |
| **names(계약 문언)** | 바인딩 이름 | **1** | **1** | 〃 79 | 7 | 105 / 30 / 16 / 111 |
| names + ① N3.10 MOD1 토큰 | 〃 | 0 | 0 | 〃 80 | 8 | 104 / 30 / 16 / 111 |
| names + ② 277행 이름 칸 → `SemiEmpiricalGmIdLUT.__init__` | 〃 | 0 | 0 | 〃 80 | 8 | 104 / 30 / 16 / 111 |

  * names `upward` = `sizing_recipe.py::SemiEmpiricalGmIdLUT`(A-1, MOD1) → `sizing_recipe.py::_QUERY_CACHE_MAX`(A-4, MOD4), `cycles` = {`gmid_lut.py`, `gmid_sizing_engine.py`}. `review_d0a.md` 39~44행과 같다.
  * 키 방식만으로 배정이 바뀌는 문장 4개(`stmt_map.json`): `_QUERY_CACHE_MAX`(SR 257) MOD1 A-5 → MOD4 A-4, `_COMPENSATION_REGISTRY`(SR 1416)·`_L_ROLE_TARGETS`(SR 2605) MOD8 A-5 → MOD4 A-4,
    `INSTANCE_TOP_FIELDS`(SD 8412) MOD9 A-5 → SD A-4. 이 중 계층 위반은 `_QUERY_CACHE_MAX` 하나다(나머지 셋은 레지스트리 칸이 명시한 MOD -- 아래 1.4).
  * ①·② 모두 사상 차이는 `_QUERY_CACHE_MAX: gmid_sizing_engine.py → gmid_lut.py` 하나뿐(`cmp.json` `diff_vs_names`), MOD1 = M1 spec 초안의 8단위 그대로.
* **277행의 내력**(오케스트레이터 질문 ②의 판단 근거):
  * 레지스트리 277행 `| `_QUERY_CACHE_MAX` | 4D 배열 적재, shape 검증, log(ID/GM/GDS) 사전계산(B15), 캐시 dict 5종 생성 | gmid_sizing_engine.py(+ S0 LUT 지문은 circu… |`.
    `git log -L277,277` = 생성 커밋 `1fcb879`(2026-09-14, 레지스트리 최초 작성) 한 번뿐, 그 뒤 변경 없음.
  * 원자료 `docs/03-analysis/gain-budget-gmid-sizing-function-audit/agent1_sizing_1_3021.md:22`: `` | `_QUERY_CACHE_MAX`(301) + `SemiEmpiricalGmIdLUT.__init__`(318-416) | 4D 배열 적재 … | … | R1 | gmid_sizing_engine.py(+ S0 LUT 지문은 circuit_state_graph.py) | … ``
    -- **감사자는 상수와 `__init__`을 한 행으로 묶어 같은 목적지를 주었다.** 레지스트리는 그 함수 칸의 첫 이름만 옮겼다(두 번째 이름 탈락).
  * 그 시점 레지스트리는 LUT 클래스 메서드 전부(`SemiEmpiricalGmIdLUT._query`·`_idu_scan`·`_gm_id_curve`·`_solve_vgs` 등)를 `gmid_sizing_engine.py`로 적었다 -- N3.10 MOD1(`gmid_lut.py` = `SemiEmpiricalGmIdLUT`, A-1)과의
    차이는 클래스 행들에선 A-1이 이기고(`reg_mismatch`로 D0b가 열을 다시 쓴다), 클래스 밖 상수 하나만 A-4로 남아 생긴다.
  * `_QUERY_CACHE_MAX`의 트리 안 참조자 = `SemiEmpiricalGmIdLUT._query`(SR 390 `if len(cache) < _QUERY_CACHE_MAX:`) 하나.

### 1.2 판단

* **(ii) 사용자 질문이다.** design §8 D0b행 멈춤 경로가 "`conflicts`·**A-1이 원천인 `upward` → N3.10 토큰(D-11)**", D-11·승인 기록 133행이 "D0b가 새로 계산하는 N3.10 개정 -- 위임하지 않는다".
  계약 문언 키로 이 `upward`는 gate master에서 생긴다. B26-1·B34의 알려진 변경 범위(m_cards_plan W-9: SD·SR rail 함수, grammar 함수 4개)는 SR 257·372~390행과 레지스트리 277행 밖이라
  D0b base에서도 같을 것으로 보이지만 **미병합이라 확인은 D0b가 자기 base에서 한다**(그래서 아래 조건부 승인).
* **②(277행 이름 칸 정정)는 '사실 오류 정정'이 아니다**: 감사 원자료가 그 행에 `_QUERY_CACHE_MAX`를 **의도적으로** 넣었으므로 원자료에 충실한 정정은
  "`_QUERY_CACHE_MAX` + `SemiEmpiricalGmIdLUT.__init__`" 복원이고, 그러면 첫 이름이 그대로라 `upward`가 그대로다(이름 칸을 모든 토큰으로 읽어도 상수는 여전히 A-4 MOD4).
  `__init__`만 남기는 것은 상수를 레지스트리가 적은 목적지에서 빼는 **배정 결정**이다 -- 질문을 피하려고 입력을 고치면 우회(메모리 '우회/skip은 타당성 검토 후에만')가 된다.
  ②의 효과는 ①과 같으므로 Q1의 대안으로만 올린다.
* **권고 ①**: design이 정한 경로 그대로이고, 선례가 같은 모양이다(UD-0의 A-1 충돌 보정 `_multilinear_interp_point_multi` → MOD1, 레지스트리 칸 결함 `_kv_table` → MOD9도 레지스트리가 아니라 N3.10 토큰으로 닫음).
  레지스트리 card가 따로 필요 없고(277행 목적지는 D0b 재생성이 `gmid_lut.py`로 다시 쓴다), 계획 표에 "상한 상수는 LUT 쪽"이 명시된다. ②는 레지스트리 수정 card(code-author 경로) 하나가 D0b 전에 더 필요하다.
* **묻는 시점**: 승인 기록은 "계산하면 그때" 묻는다. 지금 계산이 D0b base와 같은 결과이므로(위 사실) **조건부 승인**으로 묶는다 -- "D0b가 자기 base에서 계산한 추가 개정이 정확히 이 `upward` 1건일 때 이 diff를 적용, 그 밖이 나오면 다시 묻는다".

### 1.3 Q1 (AskUserQuestion 문안)

* header: `[D-11] 표 1건`
* question: "[D-11] 이동 도구를 승인된 규칙대로 돌리면 LUT 조회 캐시 상한 상수 `_QUERY_CACHE_MAX`(사용처는 MOD1 `SemiEmpiricalGmIdLUT._query` 하나)가 레지스트리 277행 목적지 때문에 MOD4로 가서 MOD1→MOD4 역방향 import와 순환이 생깁니다(승인 범위 밖 표 개정). 어떻게 할까요?"
* 선택지:
  1. **"(가) 계획 표 MOD1에 추가 (Recommended)"** -- "N3.10 MOD1 대표 대상에 `_QUERY_CACHE_MAX` 한 토큰을 더합니다(`_multilinear_interp_point_multi`·`_kv_table` 선례). 역방향·순환 0, MOD1은 8단위 그대로이고 D0b가 다른 개정을 더 계산하면 그때 다시 묻습니다."
  2. "(나) 레지스트리 277행 이름 칸 수정" -- "그 행 함수 칸을 `SemiEmpiricalGmIdLUT.__init__`로 바꿔 상수가 사용처를 따라가게 합니다(계획 표 불변, 결과 같음). 감사 원자료는 그 행이 상수와 `__init__`을 함께 다룬다고 적고 있어 오기 정정이 아니라 배정 변경이며, D0b 전에 레지스트리 수정 card가 하나 더 필요합니다."

### 1.4 최소 개정 문안

* (가)일 때 -- 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 521행(gate master):
  * 현재: `` | MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) | ``
  * 새 문안: `` | MOD1 | `gmid_lut.py` | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 | `GmIdLUT`, `SemiEmpiricalGmIdLUT`, `_multilinear_interp`, `_multilinear_interp_point_multi`, `_QUERY_CACHE_MAX`, `_solve_vgs`, `lut_conditions_from_npz`, gmb 유도(`∂ID/∂VSB`) | ``
    (복제본 측정 `variant.py qtok`와 같은 바이트. 이 줄은 `plan_tables_hash` 입력 밖 -- UD-0 개정과 같은 표.)
  * 승인 기록: `target_kind: diff`, 그 한 줄 diff. D0b가 자기 base에서 계산한 `upward`·`conflicts`가 이 1건뿐임을 D0b 판정 전 확인(다르면 멈추고 다시 묻는다).
  * D0b spec: '작성 전 실측'에 계약 문언 키 `plan` 수치(위 names 판)와 이 개정 적용 판(names+①)을 둘 다 적고, (d)-1 표본에 `_QUERY_CACHE_MAX` → `gmid_lut.py` A-1 행을 더한다.
* (나)일 때 -- 레지스트리 277행 함수 칸 `` `_QUERY_CACHE_MAX` `` → `` `SemiEmpiricalGmIdLUT.__init__` ``(같은 행 나머지 칸 불변, `variant.py regfix`), D0b 전 code-author card(레지스트리 문서, D-27 동결 전).
  그 card는 원자료 22행을 근거로 적고, 상수는 A-5(사용처)로 MOD1에 간다는 사실을 판정 기록에 남긴다.
* 둘 다: D0a spec 계약 2는 바꾸지 않는다(키 = 바인딩 이름). M1 spec 초안 '결정 필요 항목' M1-2는 "Q1 답으로 닫힘(MOD1 8단위)"으로, '재현할 수치'의 `_QUERY_CACHE_MAX` 규칙을 (가) A-1 / (나) A-5로.
* 나머지 세 문장(`_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS` → MOD4, `INSTANCE_TOP_FIELDS` → SD 잔류)은 **(i)**: 레지스트리 칸이 그 MOD를 명시하고(88·294·219행) 계층 위반·`import_time_high`가 없다(names 판 0).
  M4·M8·M9 card 단위 수(105·30·16, ① 적용 시 MOD4 104)와 W-7 CACHE-ID 대상 확인을 그 card '작성 전 실측'에서 D0b 판정 기록 값으로 다시 잰다.

---

## 2. W-1 -- 완전 shim이 unit selftest import를 깬다 (Q2)

### 2.1 사실(gate master `36e170e`, `shim_import_reads.py` → `out/shim_reads.json`)

* SHIM (b)(design §3 215행, D0a 초안 계약 4 (b)): 완전 shim의 최상위 문장 = docstring·재수출 줄·`from __future__`·base main 블록뿐, "남은 일반 import 줄 포함 -- 그 card가 지운다".
  '재수출 줄' = `from <M> import …`이고 `<M>.py`가 **N3.10 파일**(D0a 계약 4) -- 그래서 SR의 `from stick_diagram import …`(SD = MOD7)는 base 재수출로 남는다(SD 경유 이름을 SR에서 읽는 20파일은 안전).
* 완전 shim이 되는 파일(M1 base 대역 배정): TL = M4, SR = M8, DR = M9(`p3kit_m1/out/chain.jsonl` 생성기 표지와 같음).
* 그 파일이 **import 문으로만** 묶는 이름(표준·서드파티·N3.10 밖 split 파일)을 그 파일 경유로 읽는 추적 `.py` 전수 = **3파일·7이름, 모두 V1이 수집하는 unit selftest의 모듈 최상위 24행**:
  * `tests/unit/test_selftest_topology_library.py:24` `from topology_library import (…, math, …)` -- M4
  * `tests/unit/test_selftest_sizing_recipe.py:24` `from sizing_recipe import (…)` 중 `_dc_replace`(`from dataclasses import replace as _dc_replace`)·`json`·`math`·`np`·`nmcnr_predict_ac_response`(`from topology_library` -- TL은 N3.10 밖) -- M8
  * `tests/unit/test_selftest_design_report.py:24` `from design_report import (…, os, …)` -- M9
* 모의 결과(`p3kit_m1/out/simM4.pt3.txt`·`simM9.pt3.txt`): M4 상태 PT3 `1 error during collection`(TL selftest), M9 상태 3 errors(TL·SR·DR selftest) -- card 계약 6 (a) PT3와 V1이 통과할 수 없다.
* T0 초안(`draft_p3_t0.spec.md`)·design §7.1 A·B·C군 표에 이 세 줄이 없다. 세 줄은 모두 `# noqa: E402` 한 줄 import이고 이름의 객체는 출처에서 import해도 같다(동작 불변).

### 2.2 판단

* **(ii)**. 승인된 design대로면 M4가 통과할 길이 없다: shim에 import를 남기면 SHIM (b) 위반(판정 기준), test를 고치면 test 변경(V5 = 사용자 승인). 어느 쪽이든 사용자 몫이고, 기준 쪽은 약화다.
* **권고 = T0에 세 줄을 넣는다**: T0의 책임("test가 정의 위치를 가정하지 않게" -- design §7.1 A군)과 같은 종류다(`topology_library`가 `math`를 묶고 있다는 가정). 판정 기준은 그대로, card 수 그대로,
  T0의 V5 승인 질문에 '리터럴 변경 3 + 비교 완화 1'에 'import 출처 변경 3줄(7이름)'이 더해진다. T0가 이미 test 커밋을 냈다면(이 문서 시점 gate master에는 미병합) 같은 내용의 test-only card를 M4 전에 둔다(선택지 (다)).
* SHIM (b) 완화(선택지 (나))는 기준 약화이고, 남긴 import 줄이 F2까지 살아 '로직 없는 shim'의 판정 대상(문장 종류)이 넓어진다 -- 권고하지 않는다.

### 2.3 Q2 (AskUserQuestion 문안)

* header: `[W-1] shim`
* question: "[W-1] M4·M8·M9에서 topology_library·sizing_recipe·design_report가 재수출만 남은 shim이 되면, 단위 selftest 3개가 이 파일들을 거쳐 import하던 비엔진 이름 7개(math·json·np·os·_dc_replace·nmcnr_predict_ac_response)가 사라져 test 수집이 실패합니다. 어떻게 할까요?"
* 선택지:
  1. **"(가) T0에서 test import 수정 (Recommended)"** -- "M1 전 test-only card T0에서 세 파일 24행의 그 이름들을 원래 출처에서 직접 import하게 고칩니다. 판정 기준은 그대로이고, T0 V5 승인 범위에 'import 출처 변경 3줄'이 더해집니다."
  2. "(나) shim에 기존 import 허용" -- "완전 shim이 원래 있던 import 줄을 남겨도 되게 shim 판정 기준(design §3 SHIM (b))을 넓힙니다. test는 그대로지만 기준 완화이고, 그 줄은 shim 삭제(F2)까지 남습니다."
  3. "(다) 별도 test-only card" -- "M4 전에 그 세 줄만 고치는 test-only card를 하나 더 둡니다(card 17 → 18). 결과는 (가)와 같고 card와 승인이 하나씩 늘어납니다."

### 2.4 최소 개정 문안

* (가): T0 spec 초안 '의도'의 범위 목록에 한 항목 --
  "**(A군 보강, W-1)** 완전 shim이 지울 import 이름을 shim 경유로 읽는 unit selftest 3줄: `test_selftest_topology_library.py:24`의 `math`, `test_selftest_sizing_recipe.py:24`의 `_dc_replace`·`json`·`math`·`np`·`nmcnr_predict_ac_response`,
  `test_selftest_design_report.py:24`의 `os`를 그 이름의 출처(`import math`·`import json`·`import numpy as np`·`import os`·`from dataclasses import replace as _dc_replace`·`from topology_library import nmcnr_predict_ac_response`)에서 import한다.
  같은 줄의 엔진 이름은 그대로(F1 몫). 동작 불변 -- 판정: 세 파일 test id·결과 base와 같음 + 세 이름의 객체 동일(`is`)." T0 V5 승인 문안에 "import 출처 변경 3줄(7이름)".
  거부 입력 한 행: 'shim 경유 import를 하나 남김 → M4 모의(TL 완전 shim) 트리에서 그 파일 수집 오류'. design §7.1 A군 표에 행 하나(문서 개정 -- 다음 design 개정 때, 기준 변경 아님).
  `nmcnr_predict_ac_response`는 TL이 M4 뒤에도 MOD4 재수출로 들고 있으므로 F2 전까지 해석되고, F1이 MOD로 바꾼다.
* (나): design §3 SHIM (b)와 D0a 계약 4 (b) "남은 일반 import 줄 포함 -- 그 card가 지운다" → "base에 있던 import 줄은 남을 수 있다(새 import 줄은 불가 -- (a))". `shim-complete` 합성 입력 (ii)의 기대 1 → 0. 승인 대상 diff.
* (다): design §8 card 표에 test-only card 한 행(M4 전), 계획 N3.12.3 test-only 열거에 그 card. 내용은 (가)와 같다.
* 어느 답이든 M4·M8·M9 card '작성 전 실측'에 `shim_import_reads.py`(gate master판 실측 3파일·7이름)를 그 card base에서 다시 돌려 0인지 적는다.

---

## 3. W-2 -- ACF 재수출 줄 위치 (질문 없음)

### 3.1 사실

* ACF(gate master + FU 대역) 머리: docstring(1~37) → `from __future__ import annotations`(FU) → `import sys`·`import os`·`import glob`(39~41) → `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`(43)
  → `from stick_diagram import load_topology  # noqa: E402`(44). ACF importer: 추적 `.py`에서 모듈 import 0(문자열 목록·`test_ic5` 키만).
* 측정(`w2_acf_position.py` → `out/w2.jsonl`; 자산 사본에 대역 `topology_authoring.py`(`_as_set` 바이트 이동)를 두고 재수출 `from topology_authoring import _as_set` 위치만 바꿈):

| 위치 | 경로를 넣고 로드 | 다른 cwd에서 `spec_from_file_location`(자산 경로 없음) | cwd = 자산에서 `import audit_current_forced`(IMPORT-ANY 조건) |
|---|---|---|---|
| 첫 import 묶음 뒤(41행 뒤 -- 모의 생성기) | ok | **`ModuleNotFoundError: No module named 'topology_authoring'`** | ok |
| 머리 묶음의 마지막 import 뒤(44행 뒤) | ok | ok | ok |

* 어느 판정도 위치를 보지 않는다: D0a 계약 4 `shim`은 위치를 판정하지 않고(초안 159행 "IMPORT-ANY가 본다"), IMPORT-ANY는 cwd = 자산이라 두 위치 모두 통과한다.

### 3.2 판단 -- (i) design 안

design §2.2 106행 "재수출 줄은 그 파일의 import 머리 바로 뒤에 둔다(**남은 모듈 수준 문장이 import 시점에 그 이름을 읽기 전에 묶인다**)"의 목적은 '그 파일의 기존 import가 해석되는 조건에서 재수출도 해석된다'이다.
ACF에서 머리의 import는 경로 설정 문장 뒤에야 해석되므로, 목적에 맞는 읽기는 '경로 설정을 포함한 머리 묶음의 마지막 import 뒤'다. 판정 기준을 바꾸지 않고 위치 규칙을 card 계약에 구체화하는 것(강화)이라
사용자 질문이 아니다(M1-3 강화 선례). SR·TL·DR·SD는 머리에 경로 설정 문장이 없어 두 읽기가 같다.

### 3.3 최소 문안(M2·M9 spec card와 생성기)

* 계약: "split 파일의 재수출 줄 = 파일 앞머리 묶음(docstring 뒤 연속한 `import`·`from … import`·`sys.path` 조작 식 문장) 중 **마지막 import 문 바로 뒤**. ACF에서는 `from stick_diagram import load_topology  # noqa: E402` 뒤(재수출 줄에도 `# noqa: E402`)."
* 거부 입력 행(M2·M9): "ACF 재수출 줄을 `sys.path.insert` 앞에 둠 → auditor 측정: 저장소 밖 cwd의 새 프로세스에서 `importlib.util.spec_from_file_location`으로 ACF를 로드하면 `ModuleNotFoundError`(기대: 정상 위치에서 성공)".
* auditor 판정 명령(M2·M9 `equivalence.commands`에 추가): 위 로드를 병합본에서 실행해 exit 0.
* 생성기(`p3kit_m<k>`): `head_end` 계산이 `sys.path.*` 식 문장을 머리 묶음으로 넘기고 그 뒤 import까지 포함(`w2_acf_position.py`의 계산식과 같게).
* design §2.2 106행 문언 보충("경로 설정 문장 뒤 import까지가 머리")은 다음 design 개정 때 문서 정정으로(기준 변경 아님).

---

## 4. F1/TS6 -- `test_ts6_probe_relocate`가 F1에서 깨진다 (Q3 초안, 지금 묻지 않음)

### 4.1 사실(gate master, `ts6_f1_probe.py` → `out/ts6_f1.json`)

* `tests/contracts/test_ts6_probe_relocate.py`의 `test_moved_tool_matches_base_except_path_lines`(668~673행)는 `tests/tools/derive_achievable_bounds.py`를 base `939f926`의 옛 자리 blob과 비교해
  **경로 줄**(`os.path.*`·`sys.path.insert`·절대 경로 리터럴 문장) 밖 변경이 있으면 FAIL한다. 지금은 PASS.
* 그 도구는 `import sizing_recipe as sr`(33행)과 `sr.` 속성 4개(`achievable_metric_bound` → MOD8, `derived_bounds_path`·`load_derived_bounds` → MOD6, `spec_fingerprint` → MOD3, M1 base 대역 배정)를 쓴다.
  F2 뒤 SR이 없으므로 F1이 고쳐야 한다(계획 534행 '추적 파일 전부 갱신', GONE-SHIM E3 -- 이 파일은 D-9 제외 집합 밖).
* F1 모양 둘(별칭만 바꿈 / 이름 import + `sr.` 제거)을 그 test의 판정 함수(`assert_only_path_lines_changed`)에 넣으면 둘 다 FAIL(`경로 줄이 아닌 변경 [('base', 33, 'import sizing_recipe as sr'), …]`).
* design §7.1 B군 표는 이 파일의 **528행**(`test_assets_dir_holds_engine_entry_points`의 `sizing_recipe.py` 존재 앵커 -- F2에서 깨짐)만 적고 668~673행은 적지 않았다. T0 초안도 528행만.

### 4.2 판단

* GONE-SHIM(도구를 고쳐야 함)과 TS6 P2 계약 test(도구의 비경로 줄 불변)가 F1에서 정면으로 부딪힌다 -- 계약 test 판정을 바꾸지 않고는 F1이 통과할 수 없으므로 **(ii)**.
* 다만 F1은 어차피 test 변경(V5 = 사용자 승인) card이고 착수 조건이 F1이다(메모리 '묻는 건 착수 조건만') -- **M1/M4 묶음에 넣지 않고 F1 V5 질문에 묶는다.** 지금 할 일은 F1 spec 초안에 이 사실을 넣는 것.
* 권고 기본안: F1이 그 test의 기준선을 'base blob에 F1의 import 치환을 적용한 것'으로 바꾼다(그 밖 줄은 여전히 바이트 그대로 -- 엄격도 유지). 치환 규칙(`import sizing_recipe as sr` → MOD import, `sr.<이름>` → 이름)은
  test-author가 interface card의 규칙에서 독립으로 구성한다(F1 출력에서 베끼지 않는다).

### 4.3 Q3 초안(F1 V5 질문과 함께)

* header: `[F1] TS6`
* question: "[F1] shim 삭제 전에 tests/tools/derive_achievable_bounds.py의 `import sizing_recipe as sr`를 바꿔야 하는데, TS6 이동 계약 test(test_ts6_probe_relocate)는 이 파일이 2026-09-23 이동 때와 경로 줄 밖에서 한 글자도 다르지 않을 것을 요구해 실패합니다. 어떻게 할까요?"
* 선택지:
  1. **"(가) 기준선에 import 치환 반영 (Recommended)"** -- "test의 비교 기준을 '이동 때 원본 + F1의 import 치환'으로 바꿉니다. 치환 밖 줄은 지금처럼 바이트 그대로여야 합니다."
  2. "(나) 허용 줄에 import 줄 추가" -- "경로 줄 정의에 'shim 모듈 import 줄과 그 속성 참조 줄'을 더합니다. 구현은 단순하지만 그 줄들의 다른 변경도 통과시키는 완화입니다."
  3. "(다) 이동 비교 test 은퇴" -- "이동 검증은 2026-09-23 판정 기록에 남아 있으므로 그 비교 test 하나를 지웁니다. 가장 간단하지만 이후 도구 변경을 이 test가 더 보지 않습니다."
* F1 spec 문안: "design §7.1 B군에 `test_ts6_probe_relocate.py:668-673`(`test_moved_tool_matches_base_except_path_lines`)을 더한다 -- F1이 `derive_achievable_bounds.py:33`과 `sr.` 속성 4줄을 바꾸면 FAIL(측정). Q3 답에 따라 그 test를 같은 F1 test 커밋에서 고친다."

---

## 5. (덧) 레지스트리 이름 칸 `` `A`/`B` `` 읽기 -- D0a 계약 2 명확화 (질문 없음)

* D0a 초안 계약 2 "레지스트리 행과 단위는 행의 함수 이름 칸 = 단위 키로 짝짓는다"는 이름이 둘 이상인 칸(`` `INSTANCE_TOP_FIELDS`/`INSTANCE_SIZING_FIELDS` `` 219행 등)을 정하지 않는다. 시제품은 **첫 백틱 토큰**만 읽는다.
* 측정(`move_plan_alltok.py`, `MP_REG_ALLTOK=1` -- 칸의 모든 식별자 토큰): names 판 대비 `upward` 1 → 2·`cycles` 1 → 2(새 `stick_diagram.py::load_topology` → `check_topology_name_uniqueness`(SD 잔류)),
  배정 차이 5(`CompletenessVerdict`·`INSTANCE_SIZING_FIELDS`·`check_instance_completeness` MOD9 → SD, `NameCollisionVerdict`·`check_topology_name_uniqueness` MOD3 → SD).
* (i) 기본안: D0a 계약 2에 "함수 칸에 백틱 토큰이 둘 이상이면 **첫 토큰**이 그 행의 단위 키(시제품·D0b 키트·design F5v85 수치와 같은 읽기)"를 적는다(design이 키 정의를 D0a 계약 2에 맡김 -- 기준 변경 아님).
  모든 토큰 읽기는 N3.10 개정을 하나 더 부른다. 관찰: 첫 토큰 읽기에서 IC3 쌍이 갈린다(`INSTANCE_TOP_FIELDS` SD A-4 / `INSTANCE_SIZING_FIELDS` MOD9 A-5) -- 동작 차이 없음(SD가 F2까지 MOD9 이름을 끝에서 재수출,
  `test_ic3.py:107`은 F1이 출처로 바꾼다). M9 card '작성 전 실측'에 적는다.

---

## 6. 묶어서 묻는 순서(M1·M4 착수 전)

1. **Q1**(D-11) -- D0b 착수 조건(D0b spec·test-author 착수 전). 답 (가)면 승인 기록 `target_kind: diff`(계획 521행 한 줄), (나)면 레지스트리 card 하나를 D0b 앞에.
2. **Q2**(W-1) -- T0 test 커밋 전이면 T0 범위로(권고), 늦어도 M4 착수 조건.
3. Q3(F1/TS6)는 F1 V5 질문 때. W-2·(덧)은 질문 없이 M2·M9·D0a spec 문언으로.

두 질문 모두 Recommended를 첫 선택지로 두었고 선택지 설명은 2문장 이하다. 한 번의 AskUserQuestion(질문 2개)로 올릴 수 있다.

## 7. 재현

```bash
bash _drafts/p3fq_kit/build_plan.sh <gate master 커밋>      # C:/g215 복제본, FU·G1 대역, plan hash/names/qtok/regfix
python -B _drafts/p3fq_kit/stmt_map.py C:/g215/r <B> C:/g215/out C:/g215/out/stmt_map.json
python -B _drafts/p3fq_kit/cmp_plans.py C:/g215/out C:/g215/out/cmp.json
MP_STMT_KEY=names MP_REG_ALLTOK=1 python -B _drafts/p3fq_kit/move_plan_alltok.py plan --root C:/g215/r --rev <B> "${MP_ARGS[@]}"
python -B _drafts/p3fq_kit/shim_import_reads.py C:/g215/r <gate master> <out.json>
python -B _drafts/p3fq_kit/w2_acf_position.py C:/g215/r C:/g215 <out.jsonl>
python -B _drafts/p3fq_kit/ts6_f1_probe.py C:/g215/r C:/g215/out/plan_names.json <out.json>
```

`<B>` = `build_plan.sh`가 찍는 `M1-base stand-in pre-regen` 커밋(이번 실행 `4173db0`). 스크래치 `C:/g215`는 측정 뒤 삭제했다(원본 저장소 상태 불변 확인).
