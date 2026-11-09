# 독립 재검토 r1: M2~M9 card r1m — `review_m2_m9.md` S-1~S-4 해소 확인

검토자: 독립 reviewer(작성자 아님, r1 검토자와도 다른 실행). 2026-10-02.
실제 저장소는 읽기만 했다(`git -C`). `status --porcelain` 37줄(md5 `dcc7b56b…`)·reflog(md5 `1bb04b5e…`, 345줄)·HEAD `4a286f0`가 시작과 끝에 같다.
스크래치는 `C:/g273`만 썼다(`git clone --no-local --no-hardlinks -c core.autocrlf=false <작업 트리>`, TMP/TEMP `C:/g273/tmp`). 작업 뒤 `C:/g273`만 지웠다.
대상: `draft_p3_m2..m9.spec.md`(r1m), `m2_m9_open_items.md`, `draft_p3_d0a.spec.md` 281행(캐시 문장). 작성자 `p3kit_m2_m9/r1m/` 출력은 증거로 쓰지 않았다.
작성자 `c3.py`는 판정에 쓰지 않았고, 아래 N-1의 원인을 설명할 때 한 번만 탐침으로 돌렸다.

## 판정 요약

| card | 판정 | B | S | m | r1 지적 해소 |
|---|---|---|---|---|---|
| M2 | 통과 | 0 | 0 | m-a | S-1 해소. m-2·m-4 해소 |
| M3 | 통과 | 0 | 0 | m-a | S-1 해소 |
| M4 | 통과 | 0 | 0 | m-a | S-1·S-2 해소 |
| M5 | 통과 | 0 | 0 | m-a | S-1 해소 |
| M6 | **조건부 통과** | 0 | **1 (N-1 새 발견)** | — | S-1 해소. 다만 R-6 (b) 실측값이 N-1로 섞여 있다 |
| M8 | 통과 | 0 | 0 | m-a·m-b | S-2·S-3·S-4 해소 |
| M9 | 통과 | 0 | 0 | m-a | S-3·S-4·m-2 해소 |
| open items·D0a 281행 | 통과 | | | | O-2·O-4·O-8 정정이 사실과 맞다. D0a 캐시 문장은 두 방향 모두 맞다 |

새 사용자 질문은 없다. N-1·m은 card 문언만 고치면 된다. 판정 기준을 바꾸지 않는다.

## 독립 사슬(내가 다시 만듦)

* 사슬 입력: FU 대역·T0 W-1 대역·`install_proto.py`(+`g1_core.py`)·`move_plan_sim.py`(`p3kit_m1`와 md5 같음)·`regen_registry.py`. 이것들은 사슬 입력일 뿐 판정 대상이 아니다.
  D-11 토큰은 내 인라인 편집으로 넣었다(MOD1 행 `_multilinear_interp_point_multi` 뒤 `_QUERY_CACHE_MAX`).
  `4a286f0` → FU → T0W1 → G1(`installed 4`) → D11 → D0a → D0b(`one 354·nested 7·nounit 18`, `보류(Phase 4)`) = M1 base `3dc007d`.
* 확인한 수치: D0b 전 `plan`은 `reg_mismatch` 80, 배정 403(A-4 235·A-1 61·A-5 57·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1). D0b 뒤는 일곱 0, A-4 245·A-1 61·A-5 53·A-2 39·A-6 3·A-K 2. r1과 같다.
  * 절차 주의: 이 셸에서도 접두 env(`VAR=x bash …`)가 하위 python에 전달되지 않았다. 첫 빌드는 `MP_STMT_KEY`가 빠진 해시 키로 돌아 A-4 229·`reg_mismatch` 79가 나왔다. 그 결과는 버렸고, 스크립트 안에서 `export`해 다시 빌드했다.
* 이동은 **내 생성기** `mover.py`가 만들었다. 입력은 card base `plan`의 `assignment`·`mod_imports`뿐이다. 재수출 이름은 옮긴 단위에서 직접 계산했고, 그 결과를 `plan` `reexports`와 문자열로 대조해 전부 일치했다.
  * 단위 순서: TL→SD→SR→DR→ACF, 파일 안은 원본 줄 순서.
  * D-22 (2): MOD 번호 ≥ 8이면 N3.10 번호 ≥ 7 모듈을 가리키는 줄을 파일 끝에 둔다.
  * 재수출 줄: base 파일의 앞머리 묶음에서 마지막 import 뒤에 넣는다. SD(MOD7)가 card 번호 > 7 MOD로 내보낼 때만 파일 끝이다.
  * 완전 shim: docstring + future + base N3.10 재수출 줄 + 새 줄.
* 판정 도구:
  * `check`(대역 `move_plan_sim.py`).
  * **내 계약 3 판정기 `c3m.py`**: r1m card 문언에서 직접 썼다. (a)는 고친 문언, 옛 문언, 다중집합 세 읽기를 낸다. (b)·(c)는 card 문언 그대로다.
  * design §10 `import_any`를 design 파일에서 잘라 그대로 실행했다.
  * PT3(design §10 정의, `--junitxml`로 id별 결과를 모음).
  * E3b: design §10 `E3B_AST`를 잘라 `stick_diagram`을 `design_report`·`sizing_recipe`로 바꾼 사본.

| 상태 | 단위/def | `mod_imports` 머리/끝 | `check` | 내 c3 (a)·(b)·(c) | M8·M9 옛 문언 (a) | IMPORT-ANY |
|---|---|---|---|---|---|---|
| M1 | 8/22 | 3/0 | PASS | 일치 | — | 6/6/0 |
| M2 | 18/16 | 5/0 | PASS | 일치(SD·SR·ACF 모두 head) | — | 7/7/0 |
| M3 | 82/100 | 8/0 | PASS | 일치 | — | 8/8/0 |
| M4 | 104/126 | 10/0 | PASS | 일치(TL 완전 shim) | — | 9/9/0 |
| M5 | 21/23 | 9/0 | PASS | 일치 | — | 10/10/0 |
| M6 | 11/14 | 5/0 | PASS | (a) 일치, **(b) SR 불일치 — N-1** | — | 11/11/0 |
| M8 | 30/58 | 13/1 | PASS | 일치(SR 완전 shim) | **불일치(7번째 문장)** | 12/12/0 |
| M9 | 16/16 | 8/1 | PASS | 일치(SD tail·DR 완전 shim·ACF head) | **불일치(4번째 문장)** | 13/13/0 |

## S-1 (R-6) — 해소

변형은 card base에서 내 생성기에 `--extra <uid>`를 주어 만들었다. 정상 `plan`으로 판정했다.

| 변형 | `check` | 내 c3 | IMPORT-ANY |
|---|---|---|---|
| M2 `_lerp` | exit 1, **`move-set` 1만**(`moved but not assigned to this card`) | (a) 불일치, (b) SR 불일치(SD·ACF 일치) | 7/7/0 |
| M3 `_lerp` | `move-set` 1만 | (a)·(b) SR 불일치 | 8/8/0 |
| M4 `_lerp` | `move-set` 1만 | (a)·(b) SR 불일치(TL 일치) | 9/9/0 |
| M5 `_lerp` | `move-set` 1만 | (a)·(b) SR 불일치 | 10/10/0 |
| M6 `_score_floorplan` | `move-set` 1만 | (a)·(b) SR 불일치(N-1 참고) | 11/11/0 |

* 후보 함수의 전역 읽기 확인(M1 base): `_lerp`는 `float`만 읽고 데코레이터가 없으며 배정은 A-4 → `theta_search.py`다. `_score_floorplan`은 `dict`·`float`·`max`만 읽고 배정은 A-4 → MOD8이다.
* M2~M6 표 R-6 행·'작성 전 실측 10'·O-2가 모두 이 값과 맞다. R-6b 보조 행이 남아 있는 것도 r1 권고대로다.

## S-2 (반대 방향 R-CACHE) — 해소, rebind 차이 설명

| 변형 | 만드는 법 | `check` |
|---|---|---|
| M4 `knee_L_for_kind` SR 잔류 | `--exclude`로 생성 | `cache` 1(`gmid_sizing_engine.py::_KNEE_L_CACHE` ← `sizing_recipe.py::knee_L_for_kind`), `move-set` 2, `move-rejected` 1(`derive_class_L` M-4), `changed` 1, `lost` 1, `rebind` 1, `shim` 1 |
| M4 `feasible_L_window` SR 잔류 | 같은 방법 | 같은 모양(`cache` 1 = `_FEASIBLE_L_WINDOW_CACHE`) |
| M8 `achievable_metric_bound` SR 잔류 — 작성자 모양 | 그 함수를 SR에 둔 채 다시 생성한다. SR이 완전 shim이 아니라 base import(`import json` 등)가 남는다 | **`cache` 1·`move-set` 1만** |
| 같은 함수 — r1 검토자 모양 | 정상 M8 병합본에서 그 def를 MOD8에서 빼 완전 shim SR 끝에 붙이고, 재수출 이름에서 뺀다 | `cache` 1·`move-set` 1·**`rebind` 1** |

* M4 두 행은 c3 (a)·(b) SR이 불일치하고(TL은 일치) IMPORT-ANY는 통과한다. card 값과 같다.
* M8 r1 검토자 모양의 `rebind` 1 내역은 `{"unit": "sizing_recipe.py::achievable_metric_bound", "name": "json", "base": ["ext-module", …, "json"], "head": ["unbound", "json"]}`이다.
* **설명**: 두 결과는 SR이 완전 shim이냐 아니냐에서 갈린다. 완전 shim은 SHIM (b)에 따라 `import json`을 지운 SR이다. 그 안에 사용 함수를 되돌려 넣으면 그 함수가 읽는 `json`이 묶이지 않아 `rebind`가 하나 더 생긴다. 작성자처럼 함수를 남긴 채 생성하면 SR에 base import가 그대로 남아 `rebind`가 없다.
* 결론: 두 모양 모두 `cache` 1로 거부되고 IMPORT-ANY는 통과한다. 그래서 card의 R-CACHE 기대 '`cache` 1 + `move-set` 1'은 맞다. 문언 보충 하나만 권한다(m-b).
* D0a 281행 문장과 O-4 문장은 두 방향 모두 사실과 맞다. 앞 방향(캐시만 남김)은 `cache` 0이고 `move-rejected`가 잡는다. 뒤 방향은 `cache`가 잡는다.

## S-3 (계약 3 (a) 새 문언) — 해소

* M8·M9 정상 병합본에서 내 판정기의 고친 문언(대상 아닌 줄 + 단위 + 대상 줄)은 **일치**했다.
  옛 문언 그대로 읽으면 M8은 index 6(7번째 문장), M9는 index 3(4번째 문장)에서 불일치한다. card의 '7번째'·'4번째'와 같다.
* R-D22 변형(병합본의 끝 import 줄을 머리 마지막 import 뒤로 옮김):

| card | `check` | 고친 문언 (a) | 다중집합 (a) | (b) | IMPORT-ANY |
|---|---|---|---|---|---|
| M8 | **0** | **불일치(index 13 = 14번째)** | 같음 | 일치 | 12/12/0 |
| M9 | 0 | **불일치(index 8 = 9번째)** | 같음 | 일치 | **`FAIL: instance_report_builder`** |

* M8에서 R-D22를 거부하는 것은 계약 3 (a)뿐이다. card와 O-8의 서술이 사실이다.

## S-4 (R-SHIMc) — 해소

* **M9**(DR 완전 shim의 `from stick_diagram import load_topology, _audit_result_json` 줄 삭제, 29행 한 줄): **(b) DR만 불일치**(index 2)했고 나머지 판정은 모두 통과했다.

| 판정 | M9 결과 |
|---|---|
| `check` | exit 0, 발견 0 |
| 계약 3 (a) | 일치 |
| 계약 3 (b) | **DR 불일치**(index 2). SD·ACF는 일치 |
| IMPORT-ANY | 13/13/0 |
| ACF 밖 cwd 로드 | 성공 |
| E3b DR 사본 | `LIVE moved_out=6 base_files_reading_moved_out=5`, `E3b PASS`, 새 FAIL 0(정상 병합본과 같음) |
| PT3 | 정상 M9 대비 id 1062 = 1062, id별 결과 차이 0. 둘 다 3 failed·1044 passed·15 xfailed이고, 실패는 T0 A군 3(`test_dup_w_calc`·`test_ic5`·`test_ts6_dead_probes`)이다 |

* 결론: **계약 3 (b)만 거부한다**. card R-SHIMc 행 '**계약 3 (b)(SHIM (c) 열)만**'이 사실이다.
* **M8**(SR 완전 shim의 같은 줄 삭제)은 `check` 0이고 (a)는 일치, **(b) SR은 불일치**(index 8)다. IMPORT-ANY는 12/12/0이다. E3b SR 사본은 새 FAIL 25(`load_topology` probe 등)이고, 정상 병합본은 새 FAIL 0이다. card 값과 같다(PT3는 다시 재지 않음).
* 계약 7 문장 '이 줄(base 재수출 `from stick_diagram import …`)의 보존은 계약 3 (b)가 판정한다 -- 대역 `check` `shim`은 이 줄의 삭제를 보지 않는다'는 M8 45행·M9 49행에 모두 있다.
* 대역 `check`가 이 삭제를 못 보는 이유도 확인했다. `move_plan_sim.py` 721~730행의 `shim`은 head 문장 중 base에 없는 새 문장만 재수출로 센다. base에 있던 줄의 삭제는 (c) 대조에 들어가지 않는다.

## m-2 (파일 사이 단위 순서 TL→SD→SR→DR→ACF) — 해소(경미 의견 1)

여러 파일에서 단위가 오는 card(M2·M3·M9)에 순서만 바꾼 변형을 만들어 쟀다.

| 변형 | 결과 |
|---|---|
| 파일 이름순(ACF→DR→SR→SD→TL, 파일 안은 원본 순서) | M2·M3·M9 모두 `check` PASS, IMPORT-ANY 통과, 내 c3 (a)만 불일치(다중집합은 같음) |
| `plan` 키 순서(uid 정렬 — `assignment`를 그대로 돌면 나오는 순서) | M2에서 `check` `stmt-order` 1 — 파일 안 문장 순서까지 섞이므로 `check`가 잡는다 |
| `--split` 인자 순서(SR→SD→TL→DR→ACF) | M9에서는 TL→SD→SR→DR→ACF와 같은 열이라 전부 일치. M2·M3에서는 SR이 SD 앞이라 이름순 변형과 같은 경우가 된다(계약 3 (a)만 다름) |

* **생성기가 자연히 내는 순서인가**: 아니다. 단순히 순회하면 uid 순서(파일 안까지 섞여 `stmt-order`에 걸림)나 이름순·`--split` 순서가 나온다. TL→SD→SR→DR→ACF는 `m_cards_plan` §3-2가 정한 규약이다.
  r1m이 이 규약을 계약 3 (a)에 출처와 함께 적었고('이 순서도 열 비교 대상이다'), 작성자 생성기·내 생성기 모두 그대로 내므로, 문언만 보고 만들면 같은 결과가 나온다.
* **design 30과의 정합**: design §3·§6.3·§8은 파일 사이 순서를 정하지 않는다. 정하는 것은 같은 (출처, 목적지) 쌍 안의 `stmt-order`(문장 순서 보존)뿐이다. 이 규약은 그것을 지키므로 모순이 아니고, design보다 강한 규정이다(동작상 하중은 없음 — 이름순 변형이 IMPORT-ANY를 통과).
  base의 split 파일 import 관계는 SR → TL(1411행)·SD(5302행), DR → SD, ACF → SD뿐이다. 그래서 TL→SD→SR→DR→ACF는 이 관계의 위상 순서와 맞는다.
* 경미 의견: `m_cards_plan` §3-2의 '원본 파일 초기화 순서'는 실제 실행 순서가 아니다. SR이 먼저 실행을 시작하고 중간에 TL·SD를 import한다. 정확히는 'import 관계의 위상 순서'다. 문서 정정 후보이고 판정에는 무관하다.

## 새 발견

### N-1 (S, M6 — 같은 문장을 가진 M2~M9 전부에 걸린 문언 모호) '앞머리 묶음'을 base 파일에서 잴지, 단위를 지운 뒤에 잴지 정해지지 않았다

**현상**: M6 base(M5 상태)의 SR은 머리 import(…46~50행 `from circuit_metrics import …`) 뒤에 `dense_candidates`·`quantize_L`·`_grid_points_in_range`·`layout_grid_L_candidates`가 오고, 그다음이 파일 중간 import `from topology_library import …`(273행)다. M6은 이 네 단위를 모두 옮긴다. 그러면 단위를 지운 파일에서는 TL import가 머리 묶음에 붙는다. 그래서 두 읽기가 나온다.

| 읽기 | 재수출 줄 위치 | 누가 이렇게 읽나 |
|---|---|---|
| base 파일 기준 | `from circuit_metrics …` 바로 뒤(card 관찰 '51행, 앞 줄 `from circuit_metrics import …`') | 작성자 생성기, 내 생성기 |
| 지운 뒤 기준 | TL import 뒤 | 계약 3 (b) 문언 'SR = base 열 − 옮긴 단위 + 재수출 하나를 앞머리 묶음의 마지막 import 뒤에'를 그대로 구현한 판정기 — 내 `c3m.py`, **작성자 자신의 `c3.py`**(`keep`에서 계산) |

**실측**: 정상 M6 병합본(`check` PASS·IMPORT-ANY 11/11/0)을 두 판정기 모두 **(b) SR 불일치(index 16)**로 거부한다. 작성자 `c3.py`를 이 병합본에 탐침으로 한 번 돌려 `"b": {"sizing_recipe.py": {"match": false, "first_diff": 16}}`을 확인했다.
r1 검토자는 '8 card 모두 (b) 일치'라고 보고했다. 그 판정기가 base 기준으로 읽었다는 뜻이고, 같은 문언이 판정기마다 다른 결과를 낸다는 뜻이다. 이 사슬에서 차이가 드러난 card는 M6뿐이다.

**영향**:
1. 문언대로 판정기를 쓴 auditor는 올바른 M6 병합본을 거부할 수 있다. code-author도 지운 뒤 파일을 보고 TL import 뒤에 둘 수 있다.
2. M6 '작성 전 실측 10' R-6 행의 '(b) sizing_recipe.py 불일치'는 이 모호로 섞인 값이다. R-6은 재수출 이름이 달라 어느 읽기로도 (b) 불일치이므로 결론은 맞다. 다만 그 근거 판정기는 정상 병합본도 거부한다.
3. 실제 base(B26-1·B34 병합 뒤)에서는 다른 card에서도 같은 모양이 생길 수 있다.

**고칠 것**:
* M2~M9 '재수출 줄 위치' 문장과 계약 3 (b)의 'head' 경우에 한 구절을 넣는다: '앞머리 묶음은 **base 파일에서**(옮긴 단위를 지우기 전) 정한다 — 단위를 지운 뒤 머리에 붙게 된 파일 중간 import는 묶음에 넣지 않는다'. card의 관찰 행 번호, 두 생성기, design §2.2 '그 파일의 import 머리'와 맞는 쪽이 이 읽기다.
* 작성자 `c3.py`의 'head' 계산(`keep`에서 묶음 계산)을 base 묶음 기준으로 고친다.
* M6 R-6·정상 병합본의 (b)를 다시 잰다.
* 판정 기준 변경이나 사용자 질문은 필요 없다.

### m-a (전부) N-1 문구를 모든 card에 같이 넣을 것
M6 밖에서는 이 사슬에서 차이가 나지 않았다. 그러나 문장이 같으므로 함께 고쳐야 뒤 card의 실제 base에서 다시 갈리지 않는다.

### m-b (M8) R-CACHE 기대 값에 보충 한 구절
사용 함수를 완전 shim이 된 SR에 되돌려 넣는 모양이면 `rebind` 1(`json`, base `ext-module` → head `unbound`)이 더해진다(S-2 설명). 거부 판정은 같다. 기대 칸에 '(+ 그 함수를 완전 shim SR에 다시 넣는 모양이면 `rebind`)'를 적으면 auditor 실측과 맞추기 쉽다.

## 정리

`C:/g273`을 삭제했다. 실제 저장소의 `status --porcelain`(37줄, md5 `dcc7b56b…`)·reflog(md5 `1bb04b5e…`)·HEAD(`4a286f0`)는 시작과 같다.
쓰기는 이 파일 하나뿐이다(`_drafts/review_m2_m9_r1.md`).
