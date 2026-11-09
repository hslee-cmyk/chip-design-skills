# 독립 재검토 r2: M2~M9 card N-1 정정 확인 (`review_m2_m9_r1.md` N-1·m-a·m-b)

검토자: 독립 reviewer(작성자 아님, r1·r1 재검토자와 다른 실행). 2026-10-06.
대상: `draft_p3_m2..m9.spec.md`(N-1 정정판, 비교 대상 `*.spec.pre-n1.bak`), `m_cards_plan.md` §3-2(비교 `m_cards_plan.pre-n1.bak`), `draft_p3_m1.spec.md` 계약 3 (b).
작성자 판정기 `p3kit_m2_m9/r1m/c3.py`와 생성기(`gen226.py`·`neg266.py`)는 쓰지도 열지도 않았다. 판정기와 이동 생성기는 card 문언에서 새로 썼다(`C:/g287/kit/c3r.py`·`mover.py`·`rvlib.py`, 스크래치이며 삭제함).

## 판정 요약

| card | 판정 | 근거(정상 병합본, 내 판정기 새 문언) |
|---|---|---|
| M2 | **통과** | 계약 3 (a)(b)(c) 일치: SD·SR·ACF 모두 head. `check` PASS(발견 0) |
| M3 | **통과** | (a)(b)(c) 일치: SD·SR head. `check` PASS |
| M4 | **통과** | (a)(b)(c) 일치: TL은 완전 shim(3문장), SR head. `check` PASS |
| M5 | **통과** | (a)(b)(c) 일치: SR head. `check` PASS |
| M6 | **통과**(N-1 해소) | 정상 병합본 (a)(b)(c) 일치(SR 49문장). R-6은 (a)·(b) 모두 불일치하고 `check` `move-set` 1로 여전히 거부된다. 옛 문언으로는 정상 병합본이 (b) SR index 16에서 거부된다(N-1 재현) |
| M8 | **통과** | (a)(b)(c) 일치: SR 완전 shim(10문장), D-22 끝 import 1줄. (b)에 head 경우가 없으니 문언을 바꾸지 않은 것이 맞다 |
| M9 | **통과** | (a)(b)(c) 일치: SD는 파일 끝, DR은 완전 shim(4문장), ACF head. `check` PASS |
| M1 | **문언 동치**(고칠 것 없음) | M1 (b)의 'import 머리 바로 뒤(base에서 첫 비-import 문장 앞)'는 base 기준이다. M1 대상 SR에서 새 문언과 같은 자리(index 11)가 나온다 |
| `m_cards_plan` §3-2 | 통과 | 'import 관계의 위상 순서' 정정(r1 m-2)이 사실과 맞다. 생성 규칙은 바뀌지 않았다 |
| M8 R-CACHE 보충(m-b) | 통과 | 문구가 r1 m-b와 같다. 이번에 다시 재지는 않았다 |

새로 발견한 B·S급 문제는 없다. 사용자에게 물을 것도 없다. 경미한 것 2건은 아래 m-1·m-2에 적었다(card 판정과는 무관).

## 사슬(독립으로 다시 만듦, 스크래치 `C:/g287`)

* 복제는 `git clone -q -c core.autocrlf=false --no-hardlinks --no-local <작업 트리>`로 했다. TMP·TEMP는 `C:/g287/tmp`이고 `MP_STMT_KEY=names`는 스크립트 안에서 export했다.
* 사슬은 `b4734cd` → FU 대역(`fu_standin.py`) → T0 W-1 대역(`t0w1_standin.py`) → G1 시제품(`g1_kit/install_proto.py`(md5 `733d173f…`) + `g1_core.py`, `installed 4`) → D-11 순서다. D-11은 **실제 커밋의 토큰을 그대로 썼고 모의 편집은 하지 않았다**. MOD1 행의 `_QUERY_CACHE_MAX`는 1개다. 그다음 D0a 대역(`move_plan_sim.py` md5 `affb8694…`) → D0b 재생성 대역(`regen_registry.py`, `one 354·nested 7·nounit 18`, `보류(Phase 4)`)을 거쳐 M1 base `e92219b`가 된다.
* **실제 D-11 커밋을 확인했다.** 비교 사슬 B를 따로 만들었다: `4a286f0` + FU + T0W1 + G1(card 35 전 판 `install_proto.py.pre-35.bak`) + 모의 토큰(`variant.py qtok`). 결과는 다음과 같다.
  * `plan` 출력 JSON 전체가 **D0b 전후 모두 A = B**다. D0b 전은 `reg_mismatch` 80이고 배정은 A-4 235·A-1 61·A-5 57·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1이다. D0b 뒤는 일곱 목록이 0이고 A-4 245·A-1 61·A-5 53·A-2 39·A-6 3·A-K 2다.
  * 재생성한 레지스트리 md5(`6600b3ef…`)가 같다.
  * `skills/` 트리 해시(`c764085a…`)와 `tools/migrate` 트리 해시가 같다.
  * plan.md 차이는 N3.12.2 쓰기 경로표 2행(F1 workspaces)뿐이다. N3.10 표는 같다.
  * `4a286f0..b4734cd` 사이 `skills/` 변경은 0이다. `tools/`는 card 35(`mutate_changed.py`·redteam 35)가 바뀌었고 `plan`에는 영향이 없다.
  * 결론: 실제 커밋은 모의 결과를 하나도 바꾸지 않는다. 단위 수는 MOD1 8·MOD2 18·MOD3 82·MOD4 104·MOD5 21·MOD6 11·MOD8 30·MOD9 16이고 SD 잔류 111·ACF 2로 `m_cards_plan` §1 r1 표와 같다.
* 이동은 card마다 **내 생성기 `mover.py`**가 만들었다. 입력은 그 card base `plan`의 `assignment`·`mod_imports`뿐이고, 규칙은 `m_cards_plan` §3-2와 card '재수출 줄 위치' 새 문언이다. 앞머리 묶음은 base 파일에서 잰다.
  * 재수출 이름은 옮긴 단위에서 직접 계산했다. 8 card 모두 `plan` `reexports`와 문자열이 같다.
  * 각 card의 `plan`(그 card base)은 일곱 목록이 모두 0이다.
* 판정에는 `check`(대역 `move_plan_sim.py`, 계약 2)와 **내 계약 3 판정기 `c3r.py`**를 썼다. 판정기는 세 읽기를 낸다.
  * `new`: N-1 정정 문언. 앞머리 묶음 = base 파일의 docstring 뒤 연속한 import·`sys.path` 식 문장, 그중 마지막 import 뒤에 재수출을 둔다.
  * `old`: pre-n1 문언을 글자 그대로 읽은 것. 묶음을 단위를 지운 뒤의 열에서 잰다.
  * `m1`: M1 문언. base에서 첫 비-import 문장 앞에 둔다.
  * (a)는 MOD ≥ 8이면 D-22 (2) 줄을 끝으로 보낸다. (b)는 완전 shim·SD 파일 끝·head 세 경우로 나뉘고, 재수출 이름 = 그 파일 배정 단위가 바인딩하는 이름(이름순)이다. (c)는 첫 문장이 `from __future__ import annotations`인지 본다.

| card | base → head | 단위 | `mod_imports` 머리/끝 | 재수출 위치(내 생성기) | `check` | c3 new (a)(b)(c) | c3 old | c3 m1 |
|---|---|---|---|---|---|---|---|---|
| M1 | `e92219b`→`44d0eea` | 8 | 3/0 | SR base 45행 뒤 | PASS | 일치(SR 223) | 일치 | 일치 |
| M2 | →`f98e27a` | 18 | 5/0 | SD 40행 뒤·SR 46행 뒤·ACF 44행 뒤 | PASS | 일치 | 일치 | ACF 불일치(index 5, 아래 m1 설명) |
| M3 | →`a50ad4b` | 82 | 8/0 | SD 41·SR 47 뒤 | PASS | 일치 | 일치 | 일치 |
| M4 | →`ddcdb1b` | 104 | 10/0 | TL 완전 shim·SR 48 뒤 | PASS | 일치(TL 3·SR 79) | 일치 | 일치 |
| M5 | →`445123e` | 21 | 9/0 | SR 49 뒤 | PASS | 일치(SR 59) | 일치 | 일치 |
| **M6** | →`cd11c63` | 11 | 5/0 | SR 50 뒤(→ 병합본 51행, card 관찰과 같음) | PASS | **일치(SR 49)** | **(b) SR 불일치 index 16** | 일치 |
| M8 | →`bc1af83` | 30 | 13/1 | SR 완전 shim | PASS | 일치(SR 10) | 일치 | 일치 |
| M9 | →`397fbf8` | 16 | 8/1 | SD 파일 끝·DR 완전 shim·ACF 45 뒤 | PASS | 일치(SD 123·DR 4·ACF 11) | 일치 | ACF 불일치(index 5) |

* card '모의 병합본' 관찰 행 번호와 비교했다. M2 SD 41·SR 47·ACF 45, M6 SR 51, M9 ACF 46행이 모두 내 생성기 출력(삽입 base 행 + 1)과 같다.

## N-1 확인

1. **모양**: M6 base(`445123e`) SR의 최상위는 index 15(50행 `from circuit_metrics import …`) 다음에 옮길 단위 4개가 온다. index 16~19가 `dense_candidates`·`quantize_L`·`_grid_points_in_range`·`layout_grid_L_candidates`이고, 그다음 index 20(273행)이 파일 중간 import `from topology_library import …`다. 단위를 지우면 이 import가 머리 묶음에 붙는다.
2. **새 문언(base 기준)**: 정상 M6 병합본이 (a) 16문장, (b) SR 49문장, (c) 모두 일치한다. 재수출은 index 16 자리이고 `from circuit_metrics …` 바로 뒤다.
3. **옛 문언(지운 뒤 기준)**: 같은 병합본이 (b) SR **index 16에서 불일치**한다. 기대 자리가 index 17, 즉 TL import 뒤다. r1의 N-1 측정값(index 16)과 같으므로 **N-1이 재현된다**. 8 card 중 옛 문언과 새 문언이 갈리는 곳은 M6뿐이다. 나머지 7 card는 두 읽기가 같은 결과를 낸다.
4. **M6 R-6 여전히 거부**: card base에서 내 생성기에 `--extra sizing_recipe.py::_score_floorplan`을 주어 만들었고(`b3bafed`), 판정은 정상 `plan`으로 했다.
   * `check`는 exit 1이고 **`move-set` 1만** 나온다(`moved but not assigned to this card`).
   * 계약 3 새 문언: (a) 불일치(index 12, 기대 16 대 실제 17문장), (b) SR 불일치(index 16, 기대 49 대 실제 48). 옛 문언도 같은 index에서 불일치한다.
   * card 134~135행의 'N-1 정정 뒤 재측정' 값과 같다: (a) index 12, (b) index 16, 정상 병합본 SR 49문장. 재수출 자리가 정상과 같고 이름 집합에 `_score_floorplan`이 더 있다는 설명도 맞다.
5. **M8 (b)를 바꾸지 않은 것이 맞다**: M8은 단위를 SR에서만 받는다(SR 30단위). SR은 완전 shim이 된다(잔여 단위 0, N3.10·`--keep` 밖). 그래서 (b)에는 head 경우가 없고 '앞머리 묶음' 구절이 걸릴 데가 없다.
   M8 card는 '재수출 줄 위치' 일반 문장(20행)에만 구절을 더했고 (b)(39행)는 그대로다. diff로 확인했다. 실측으로도 new·old·m1 세 읽기가 모두 일치한다.
6. **M9**: ACF는 head 경우라 (b)에 구절이 들어갔다. ACF의 base 묶음(`import sys/os/glob` → `sys.path.insert` → `from stick_diagram …` → M2 재수출)은 단위를 지워도 바뀌지 않는다. 옮긴 단위가 묶음 뒤에만 있기 때문이다. 그래서 두 읽기가 같다(실측 일치).
7. **M1 문언 동치**: M1 (b)는 '재수출을 import 머리 바로 뒤(**base에서** 첫 비-import 문장 앞)에'라고 적는다. 처음부터 base 기준이라 N-1 모호가 없다.
   M1이 단위를 내보내는 파일은 SR 하나다. SR 머리에는 `sys.path` 식 문장이 없으므로 'base 첫 비-import 문장 앞'과 'base 머리 묶음의 마지막 import 뒤'가 같은 자리(index 11, 45행 `import numpy as np` 뒤)다. new·m1 판정 모두 일치한다. 그래서 M1은 고칠 필요가 없다.
   * 두 문언이 갈리는 곳은 `sys.path` 문장이 머리에 있는 ACF(M2·M9)뿐이다. m1 읽기로는 재수출이 `sys.path.insert` 앞으로 가서 index 5에서 불일치한다. 이것은 W-2가 M2·M9에 묶음 문언을 따로 둔 이유이고, M1 문언을 M2~M9 틀로 옮겨 쓰지 않은 것이 맞다.
8. **판정기 실효 확인**: 내 생성기에는 처음에 완전 shim 판별 버그(dict 키 대 index 비교)가 있었다. 그 첫 M4 출력은 TL이 완전 shim이 되지 않고 재수출이 머리에 붙은 모양이었다. 이 출력을 내 판정기 (b) TL이 불일치(index 2, 기대 3 대 실제 5문장)로 거부했고 `check`도 `shim` 2로 거부했다.
   그 출력은 버렸고, 생성기를 고친 뒤 M4부터 다시 만들었다(위 표가 고친 판). 이 일은 판정기가 공허하지 않다는 우연한 증거로만 적는다.

## 경미 의견(판정 무관)

* **m-1 (`variant.py qtok`를 실제 gate에 쓰면 안 된다)**: 앵커 `…_multilinear_interp_point_multi\`, `가 토큰이 들어간 새 행의 접두이기도 하다. 그래서 `b4734cd`(토큰 있음)에 돌려도 `count == 1`이 되어 **`_QUERY_CACHE_MAX`를 한 번 더 넣는다**(첫 사슬에서 실측했고, 그 사슬은 버렸다).
  작성자 키트가 이후 `b4734cd` 이상에서 사슬을 만들 때 qtok 단계를 빼야 한다. 아니면 '이미 있으면 멈춤' 가드를 더해야 한다. card 문언과는 무관하다.
* **m-2 (진행 중 실제 저장소 변화)**: 작업 중에 실제 저장소 HEAD가 `b4734cd` → `7243f28`로 나아갔다. 다른 실행이 docs 커밋 3개(`8b64a84`·`298089b`·`7243f28`, B34 승인 기록·references·spec card)를 만들었다. 이 검토는 `b4734cd`를 명시 checkout해 그 판으로 쟀다.
  새 커밋은 B34 card 문서뿐이고 엔진은 아직 바뀌지 않았다. M2 W-9(B34가 바꾸는 def 4개가 모두 M2 단위)는 B34 병합 뒤 실제 base에서 다시 확인할 사항으로 남는다.

## 정리

* 스크래치 `C:/g287`은 삭제했다(아래 끝 줄).
* 실제 저장소는 `git -C` 읽기와 `clone`(작업 트리에서)만 했고 쓰지 않았다. 시작 시점은 HEAD `b4734cd`·status 39줄이었다. 끝 시점은 HEAD `7243f28`·status 38줄·reflog +3이고, 이 +3은 위 m-2의 다른 실행이 만든 docs 커밋이다(reflog 시각 15:42~15:50, 모두 `commit:`).
* 쓰기는 이 파일 하나뿐이다(`_drafts/review_m2_m9_r2.md`).
