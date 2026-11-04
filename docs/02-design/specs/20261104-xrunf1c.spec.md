---
id: 20261103-xrunf1c
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---

> **[상태 2026-11-04] spec card -- 커밋 안 함, 독립 검증 전.** design 정정 DF-1~DF-6·계획 PF-1~PF-3은 반영됨(아래 '착수 조건'). 사실 문장 재측정 = 같은 폴더 `measure_facts.py` → `facts.txt`(읽기 전용, 엔진 실행 0). 줄 번호 = master `7620f5ee`(`E/search` 변경 `c8ecc4e7..7620f5ee` 0). 실제 base에서 줄은 어긋난다(IT 겹침 표) -- 줄은 찾는 길잡이이고 범위 정본은 이름이다. `E/` = `skills/analog-gmid-design/gmid_engine/`. `P:` = gain-budget 계획 v6.38.8, `D40:` = design 40 v1.16.3, `HC:` = headroom-chain 계획. 앞 초안 = `wt/_drafts/evidence/2026-11-03/card_c/spec_card_draft.md`(대조표 부록 A는 그 파일에 둔다). 판정 기록 자리 = `.ai/verification/20261103-xrunf1c.json`(`_schema.json`).

## 착수 조건

| # | 무엇 | 상태 |
|---|---|---|
| C-1 | design 40 정정 DF-1~DF-6 | 충족: D40:295·314·773·774·796, 위임 A-9·A-27(`evidence/2026-11-03/design_b2_validation.md`: card C '가능', m11 = 이 머리 갱신) |
| C-2 | 계획 정정 PF-1~PF-3 | 충족: P:1299·1364·1704·2546, 위임 A-9·A-25 |
| C-3 | 보류 다리 병합(P:1447 (i)) | 충족: 위임 A-5·A-10(O-226) |
| B-1 | **base 조건**(아래) | **미충족** -- GL-1·IT-1 + IT-2·EO-1 범위 4 미병합(`facts.txt` §5) |
| B-2 | **library 13 회귀 전제**: `fix/o181-tests` 처리 | **미충족, 오케스트레이터 몫**(아래 '멈춤 항목') |

**base = 그때 master = GL-1 → IT-1 + IT-2 → EO-1 범위 4 + 로더 커밋을 포함한 master**(P:1361~1364, D40:2216, 위임 A-9·A-14). 병합 자리 = EO-1 범위 4 뒤, HC-S 앞, TB-1과 N6.1 진행 순서로는 C → TB-1. 뒤따름 = HC-S(P:1366)·HC-1(P:1370).

코드·test 착수를 base 전에 시작하면 IT와 다섯 파일이 겹친다(`search/fd_jacobian.py` `_steps`, `search/kernel.py` docstring, `search/CONTRACT.md`, `_module_map.py`, `tests/search/test_fd_jacobian.py`, `facts.txt` §2). 충돌 hunk는 card C 수정 자리와 다르다. 그래도 test freeze와 red 재현은 위 base에서 한다.

## 의도

선언 E_B 40에서 커널 평가 43·49·64·66(design 인용 history H4, card B 판정 `b_summary.json`에서도 43·64·66·50)이 된 예산 결함을 고친다. 모든 커널 평가를 E_total에 넣고 탐색과 감도 게이트 예산을 나눈다. 이것으로 색인 상한의 전제(커널 평가 수 ≤ E_total)가 구조로 성립하고 등록 때 fail-closed가 켜진다.

사용자 결정: X-8·X-15·X-16·X-17, U-96·U-98·U-99, O-220, X-19(순서 A → B → C). 오케스트레이터 기본안(D40 C 행): B-1·B-2·N-2·N-3·N-4. 위임 채택: A-9. 승인 사실은 근거가 아니다(O-208).

변경 종류 = **동작 변경**(탐색 궤적과 13회로 결과가 바뀐다).

## 관찰 가능한 계약

**정의.** R = 2 × `len(sctx.domain.variables)`. E_total = 선언이면 E_B + N_T + R, 유도면 D. 탐색 예산 = 선언이면 E_B, 유도면 D − N_T − R. 이 card에서 N_T 항은 코드에 없다(층 0은 탐색 예산 안; N_T는 LA-1 범위 15 (g)가 `layer0_budget`으로 더한다, P:2546). 값은 `_helpers_ceiling` 한 자리에서만 계산한다.

1. **탐색 상한.** `find_front` 안에서 감도 게이트 진입 때 `kernel_calls` ≤ 탐색 예산. 게이트 안 커널 평가 수 ≤ R. 실행 끝 `kernel_calls` ≤ E_total, 어기면 `RuntimeError`.
2. **단일 평가.** 탐색 단계의 단일 평가는 평가 전에 `search_stop`을 본다. `kernel_calls` = 탐색 예산 − 1이면 평가, = 탐색 예산이면 평가 안 하고 사유 `eval_budget`. 범위 = 재작성 범위 표 전부(사다리 칸, 주어진 시작점 포함). 층 0 시작점의 재확인(`start_points`)은 캐시 적중이라 커널 0으로 읽는다.
3. **묶음.** `fd_jacobian`은 시작 전에 상계 = 평가할 열 수 × 2(`skip`·스텝 0·`None` 제외)와 남은 한도(`ceiling` − `kernel_calls`)를 비교한다. 남은 한도 = 상계면 실행, = 상계 − 1이면 평가 0개로 `FdBudgetShortfall(needed, remaining)`. `ceiling`이 None이면 확인 없음. 묶음 도중 멈추지 않는다.
4. **shortfall 처리.** 반복 중 야코비안(외층·층 0 `jac_of`) = `_Abort("eval_budget", entry["x"])`. 첫 스텝 야코비안(외층·층 0 `steps0`) = 반복 0, 재시작 0, 정지 사유 `eval_budget`, `aborts` = (`eval_budget`,), 수락 목록 = 시작점 하나에 그 파일의 끝 선택 규칙 적용. 감도 게이트 = 잡지 않는다(결함으로 실행 정지).
5. **유도.** `evaluate`는 `eval_budget`을 쓰지 않는다. `search_ceiling`이 `eval_budget` None이고 평가 시간이 n_θ + 1개 이상일 때 첫 n_θ + 1개로 D를 계산해 `sctx.eval_budget`·`eval_budget_source`에 넣는다. 그 전이 호출에서 `kernel_calls` ≥ D − R이면 `ValueError`(사유 `time_budget_below_search_reserve`), = D − R − 1이면 통과. 전이 뒤 `kernel_calls` = 탐색 예산이면 `search_stop` = `eval_budget`(예외 없음), + 1(주입)이면 `RuntimeError`. `final=True`(`find_front`가 게이트 전에 한 번)는 평가 시간 1개 이상이면 그 전부로 유도하고 `kernel_calls` = D − R이면 통과, + 1이면 `ValueError`.
6. **게이트는 언제나 돈다.** front 점이 있으면 탐색 예산을 다 써도 돈다. `not_run` 없음. 게이트 시작 뒤 `search_ceiling`·`search_stop` 호출 0.
7. **색인 상한.** `find_front` 진입에서 `donors.open_bound(total_of)`, 끝 확인 뒤 `donors.close_bound()`. 그 사이 등록은 항목 수 > (등록된 서로 다른 (블록, 분할) 수) × (E_total + 1)이면 `RuntimeError`. E_total이 None이면 검사 안 하고, 정해진 뒤 첫 등록·끝 확인에서 잰다. 열기 밖 등록(단계 A·B, MOD8)은 검사 안 한다. `open_run`·`S3Index()`는 인자 없음 그대로.
8. **형식.** 결과 JSON 칸 변경 0. `perf.eval_budget`의 뜻은 선언 = E_B, 유도 = D로 갈린다(칸 이름 그대로, `eval_budget_source`가 구분). `resolution.E_B` 값 = `search_ceiling` 값. `perf.block_index_bound` = `donors.index_bound(e_total(sctx))`. 기존 단언 `len(blocks) × (E_total + 1)`(`tests/search/test_find_front.py:108`)과 같은 값이어야 한다. 다르면(호출됐으나 등록 없는 행) 멈추고 보고한다(미측정).

**문언 grep 0**(D40 §2.4.14 (4) C 행): `E/search/`에서 `_budget_stop`, `E/search/find_front.py`에서 `_e_total`·`2 *` 변수 수 항·`eval_budget_source` 분기, `E/search/kernel.py`에서 `EvalBudget`. 예산 확인용 `sctx.eval_budget` 직접 읽기는 `rg -n "eval_budget" E/search`로 남는 곳이 `search_ceiling.py`, `_helpers_ceiling.py`, `find_front.py`(perf·`run_id`), `search_context.py`(생성), `search_values.py`(설정), `__init__.py`·`eval_budget.py`(클래스 이름), 기록 칸 문자열, docstring뿐.

## 재작성 범위

(엔진 인용 용도 = 재작성 범위만, 원칙 8. 옛 코드는 같은 변경에서 삭제.)

| 파일(`E/search/`) | 줄(master) | 범위 | 근거 |
|---|---|---|---|
| `search_ceiling.py` | 신규 | 진입점 `search_ceiling` | 예산 숫자·유도 전이 한 자리 |
| `search_stop.py` | 신규 | 진입점 `search_stop` | 정지 사유 한 자리, 정의 셋을 대체 |
| `_helpers_ceiling.py` | 신규 | `gate_reserve`, `e_total` | E_total 한 자리(DF-2). 소비 = `search_ceiling`·`find_front`·`gate_run` |
| `kernel.py` | :160-165, :31 | 유도·import 삭제. `eval_times` 기록만 | 평가가 예산을 쓰는 구조 제거 |
| `fd_jacobian.py` | :86-111 | 부분: 필수 키워드 `ceiling`, 상계 확인, `FdBudgetShortfall` | 열 평가 규칙은 그대로 |
| `layer0_center.py` | :281 정의 삭제; :321·:503·:527·:599·:674 → `search_stop`; :603-606 → `search_ceiling`; :338·:371 shortfall; :665 앞 칸 확인 | 부분. `scipy_minimize` 전역 이름 호출 유지(NFR-4 관찰 지점) | 사다리·`_halton_probe`·`_maxmin`은 LA-1a가 지운다. C가 그 앞이라 지금 고친다(DF-4) |
| `slsqp_outer.py` | :86 정의 삭제; :115 → `search_stop`; :137·:165 shortfall; :15 docstring | 부분 | 풀이 흐름은 그대로 |
| `l_bin_search.py` | :35 정의 삭제; :47·:55·:79 → `search_stop`; :10 docstring | 부분. NFR-4 정지 사유 반환 유지 | as-built 이름 `_budget_stop`(DF-5) |
| `eps_sweep.py` | :85·:93·:94 → `search_ceiling`, :9 docstring | 부분. 기록 칸 이름 `E_B` 유지 | |
| `residual_probe.py` | :73-76 → `search_stop`·`search_ceiling`, :8 docstring | 부분. 규칙 둘 방지 | **표지**: production 호출자 0인 파일 수정. 지우는 안은 범위 밖(LA-1 범위 15의 U17 ② 잔여) |
| `start_points.py` | :39 앞 | 부분: `given`만 평가 전 확인, 닿으면 그 뒤 후보 평가 없이 `starts`에 `status` = `eval_budget` | |
| `gate_run.py` | :54 | `ceiling=e_total(sctx)`. 잡지 않음 | 게이트 = E_total |
| `find_front.py` | :41-48 삭제; :18·:117; 진입 `open_bound`; `sweep_front` 뒤 `search_ceiling(sctx, final=True)`; 끝 확인·`close_bound` | 부분. `layer0_start`·`sweep_front`·`run_sensitivity_gate` 전역 이름 호출, 진입 재확인 (c), runs 줄 `env_fp`, notes `l_search` 유지 | |
| `s3_index.py` | 클래스 | 부분: `open_bound`·`close_bound`·`index_bound`, (블록, 분할) 수 | fail-closed (5) |
| `open_run.py` | docstring | 서명 불변, 상한 문장 정정 | DF-1 |
| `search_values.py`:46, `search_context.py`:21·:64, `CONTRACT.md`, `_module_map.py` | 문구·항목 | 갱신. 뜻 갈림 한 줄 포함 | 같은 변경에서 맞춤 |
| 함수 레지스트리 §2, D40 §2.4.13 벽시계 경로 인용 | 행 | 갱신 | 레지스트리 §0 규칙 4 |

`_module_map.py` 자리 제안(구조 규칙 C가 판정): `_helpers_ceiling.py` = `eval_budget.py` 층 또는 그 아래, `search_ceiling.py` = `search_context.py` 층, `search_stop.py` = `kernel.py` 층. 소비자 `start_points.py`·`fd_jacobian.py` 층보다 낮아야 한다. 어긋나면 층을 옮기되 멈추지 않는다(계약 무관).

바꾸는 문서는 test 없음. `tests/search/test_fd_jacobian.py` 8곳·`test_layer0_center.py` 1곳 직접 호출에 `ceiling` 필요(test 주체). `open_run()` 호출 320곳(87 파일)은 **안 바뀐다**.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.search.search_ceiling` | `search_ceiling` | `def search_ceiling(sctx, *, final=False)` |
| `gmid_engine.search.search_stop` | `search_stop` | `def search_stop(sctx)` |
| `gmid_engine.search._helpers_ceiling` | `gate_reserve` | `def gate_reserve(sctx)` |
| `gmid_engine.search._helpers_ceiling` | `e_total` | `def e_total(sctx)` |
| `gmid_engine.search.fd_jacobian` | `fd_jacobian` | `def fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset(), *, ceiling)` |
| `gmid_engine.search.fd_jacobian` | `FdBudgetShortfall` | `class FdBudgetShortfall(Exception)` (`needed`, `remaining`) |
| `gmid_engine.search.s3_index` | `S3Index.open_bound` | `def open_bound(self, total_of)` |
| `gmid_engine.search.s3_index` | `S3Index.close_bound` | `def close_bound(self)` |
| `gmid_engine.search.s3_index` | `S3Index.index_bound` | `def index_bound(self, total)` |

이름 충돌: master·`integ/it12` 엔진·test에서 새 심볼 0(`facts.txt` §4). 예외: 지역 변수 `e_total`이 `find_front.py:117·126`(card C가 고침)과 `tests/search/test_find_front.py:107`에 있다. `test_search_ceiling.py`·`test_search_stop.py`·`test__helpers_ceiling.py`는 없음, 나머지 test 파일은 있어 추가한다. `Donors` 추상 메서드는 늘리지 않는다. EO-1 범위 4 뒤 base에서 test 주체가 다시 확인한다.

## graph 단일 정본

* 새 graph 필드 0. 블록 입력·출력 변경 0.
* E_total·R 계산 자리 하나(`_helpers_ceiling`), 사본 `find_front._e_total` 삭제. 탐색 예산 = 그 값에서 유도.
* `S3Index`는 E_total 값을 보관하지 않고 참조 `total_of`만 쥔다(graph 규칙 4). (블록, 분할) 수는 자기 키의 파생이고 다른 생산자가 없다. `perf.block_index_bound`는 같은 메서드를 읽는다.
* `sctx.eval_budget`·`eval_budget_source`: 새 칸 없음. **원칙으로 재판정**: D는 벽시계 표본에서 나온 실행 제어 값이고 설계 값·입력 버전이 없어 graph 필드 대상이 아니며 허용 저장소 (c) 실행 계수 부류다. 틀리면 멈추고 보고.
* **표지**: 칸 하나가 선언 = E_B, 유도 = D로 뜻이 갈린다. 칸을 나누면 결과 JSON 변경이고 design이 안 나눴다. 판정자 확인 항목.
* 같은 입력 재계산 래칫: 새 B 0, 이 card 배정 B 없음.

## 소비자

| 새·바뀐 def | 엔진 소비자 |
|---|---|
| `search_ceiling` | `search_stop`, `layer0_center`(Halton 한도·FD 호출), `slsqp_outer`(FD 호출), `eps_sweep`, `residual_probe`, `find_front` |
| `search_stop` | `layer0_center`, `slsqp_outer`, `l_bin_search`, `residual_probe`, `start_points` |
| `gate_reserve`, `e_total` | `search_ceiling`, `gate_run`, `find_front`, `find_front`의 `total_of` |
| `FdBudgetShortfall` | `layer0_center`·`slsqp_outer` 네 호출부 |
| `open_bound`, `close_bound`, `index_bound` | `find_front` |

`residual_probe`만 production 호출자 0이고 이 card가 만든 것이 아니다.

## 판정 유형 근거

동작 변경(N6.3) 네 다리 + O-225 유보(P:1402·1403·1427·1528). 비트 동일 요구 안 함. 결정성은 항상 검사.

| 다리 | 상태 |
|---|---|
| 정의 toy | 계약 1~7 경계값 test |
| 봉인 불변식 | 값 정의 불변 |
| 기존 회귀 | 새 test 체계 전체, 0 failed. base에 실패가 남으면 목록을 올리고 판정을 멈춘다(B-2) |
| 연기 시험 | 병합 때 2회로, 아래 '연기 시험' |
| 13회로 변화표 | **보류**(채울 시점 = LA-1 측정 시점, LA-1 완료 13). base sha를 판정 기록에 적는다 |
| SPICE 시작점 | **보류**(채울 card = OP-5, EO-1 범위 1~3 배선 뒤, 위임 A-8·A-14·A-23) |
| SPICE front 점 | **보류**(채울 card = CL-1) |

→ 병합해도 '미완료'. 판정 기록에 '미완료(보류 다리: 변화표 = LA-1 측정 시점, SPICE = OP-5·CL-1)'. 병합 판단 = O-226. 계수에 안 든다.

**D40 C 행 완료 (i)(ii)(iii)·판정 측정의 13회로 전수는 위 보류로 옮긴다**(O-225, 계획 상위). (iv) 게이트 실행과 상한 검사는 toy·연기 시험으로 지금 본다.

**red 자리.** 새 키워드 인자의 `TypeError`는 red가 아니다. **`kernel_calls` ≤ E_total만으로는 red가 안 난다**: 선언 E_B 40에서 card B 판정 값은 8회로 전부 이미 E_total 안이다(초안 `facts.txt` §6). 그래서 red = **게이트 진입 때 `kernel_calls` > 탐색 예산**(계약 1)이다. 관찰 = `find_front` 모듈의 `run_sensitivity_gate` 전역 이름을 감싸 진입 때 계수 기록(엔진 무변경). base: 탐색 묶음이 예산을 넘는 합성 입력에서 assertion 실패. 기준 강화라 승인 불요, 표지만.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력: 경계값은 정의 문장에서 손으로 낸다(예산·상계·R). 피검 함수로 기대값을 만들지 않는다.

## 거부해야 할 입력

- 유도 전이에서 `kernel_calls` ≥ D − R → `ValueError`(`time_budget_below_search_reserve`). `CANDIDATE_FAILURE_CLASSES`에 안 잡힌다.
- 게이트 `FdBudgetShortfall` → 잡지 않음. 실행 끝 `kernel_calls` > E_total → `RuntimeError`. 전이 뒤 `kernel_calls` > 탐색 예산 → `RuntimeError`. 색인 등록 상한 초과 → `RuntimeError`.
- `ceiling` 빠진 `fd_jacobian` → `TypeError`. 두 번째 `open_bound`(닫기 전) → `ValueError`.
- 선언 실행은 예산 거부가 없다(작은 E_B도 받음, X-17).

## library 회로 적용 여부

대상 = library 13(O-181·O-182). 전수 측정은 LA-1 측정 시점. 지금 base에서 탐색 전에 멈추는 회로(실측 `../tb1/gcb7_master.jsonl`): `cnr_ota` = 쓰기 계획 `dc_resistor_cycle`, `erfc_ota` = spec `topology_fp_mismatch`와 전류 기저 `mos_zero_current_structural`(둘 다 DR-1 대상, DR-1은 이 card 뒤). `ngcc_3stage_ff`는 card B 구분 `NOT_SEARCHED`. 이 셋은 분모·사유를 따로 적는다. held-out 0개, A' 일반성 판정 정지.

**연기 시험**(P:1427): 후보 `common_gate_amplifier`(n_θ 6, 신호 1단)·`two_stage_ota`(n_θ 10, 신호 2단). 둘 다 2n_θ < 39라 FD 묶음이 시작될 수 있다(코드 유도, 층 0 소비 미측정). 선언 E_B 40 각 1회 + `two_stage_ota` 유도 1회. 직전 master에서 예외 없이 끝나는지와 그 경로 통과는 검증자가 확인하고 선택을 판정 기록에 적는다. 메모리: 회로마다 프로세스를 나눠 순차.

## 무동작 판정 입력(무발동 값)

탐색이 예산 전에 끝나는 합성 실행(E_B를 넉넉히 선언): `FdBudgetShortfall` 0, `eval_budget` 사유 0, 게이트 전 궤적이 base와 같음(같은 θ·`seq`, §2.4.13 비교기). 넉넉한 값은 `2 × n_θ`·바퀴 수에서 유도한 것을 판정 기록에 적는다.

## 재현할 수치

연기 시험 회로마다(판정 기록의 값만 인용): `perf.kernel_calls`, E_total, 게이트 진입 때 `kernel_calls`, 게이트 안 커널 평가 수, R, `block_index_entries`, `block_index_bound`, `stops_eval_budget`, 정지 사유 분포, front 점 수, G-10 판정 1·5. 숫자를 card에 박지 않는다.

## 결정 필요 항목

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| Q-C1 묶음 상계 2 × 열 수 유지(X-8) | 없음(실행 제어) | D40 C (5). 원문 쪽 해당 없음 | 코드 유도만, 미측정: n_θ ≥ 20인 4/9회로(ngcc·nmcnr·sf·current_reuse)는 E_B 40에서 시작 평가 뒤 남은 39 < 2n_θ라 묶음이 시작되지 않을 수 있다(스텝 0·None 제외 시 달라짐) | **조건부 유지 권고**. 규칙은 맞다(대안 '열마다 확인'은 FD가 깨진 채 나옴). E_B 40 실행은 예산 상한만 재고 탐색 품질을 못 잰다 |
| Q-C2 LA-1 측정 시점의 E_B | 위와 같음 | E-13 | 앞 사례 E_B 2000(`evidence/2026-11-01/icmr4/`), 미측정 | **표지**: E_B 40이면 위 4회로는 출발점만 잰다. LA-1 측정 설계자가 FD가 도는 E_B를 정할 것(재점검 입력) |

사용자 질문 없음(O-226). 번복 입력은 위임 기록 A-9.

## 원래 취지와 다름

1. S3Index 생성자 필수 인자 → 열기 메서드(DF-1, A-9).
2. 색인 상한 검사 범위 = `find_front` 안(DF-6). MOD8 예산 = U16 몫.
3. 완료 조건 강화(게이트 진입 단언). 약화 아님.
4. card C가 LA-1a가 지울 코드를 고친다(순서 C → HC-1 → LA-1a).
5. 13회로 판정·변화표·SPICE 유보(O-225, A-5·A-10). D40 C 행 문언은 13회로 전수 그대로다 -- 재점검 때 채운다.

## 절차

(DEC-86 넷, 정본 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리.
2. 깨진 test·기준 약화는 숨기지 않고 보고(`broken_tests`·`criteria_weakened`·`retired_tests`).
3. 변경당 커밋 1.
4. 매 변경 뒤 새 test 체계 전체 실행.

* 판정 기록: 독립 검증자. N6.3 넷(G 확장 lint·값 타입 위치·소유표·G-10)과 '같은 입력 재계산 0' 포함. 구현 뒤 design ↔ 구현 gap.
* 흐름 = N3.12.3 순서 2~6 역할 분리(폐기된 gate·push 절차 제외, 앞 card 관행). test 주체는 interface card만 읽는다.

## 작성 전 실측

(`facts.txt`) 예산 자리 전수 §1, IT 겹침·줄 §2, test 호출 §3, 이름 §4, 선행 상태 §5, 계획·design 줄 §6. **안 잼**: 13회로 실행, EO-1 범위 4 뒤 base(브랜치 없음), 새 4회로 n_θ, 층 0이 쓰는 커널 수, GL-1 G-8이 이 변경에 내는 값. 회로 이름 0, 새 상수 0(`2`는 FD 시도 방향 수).
