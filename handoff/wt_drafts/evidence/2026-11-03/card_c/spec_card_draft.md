---
id: 20261103-xrunf1c
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---

> **[상태 2026-11-03] 초안 -- 착수 불가.** 착수 조건 = 아래 '착수 조건' C-1~C-3 승인. 커밋 안 함. 독립 검증·design↔계획 gap·⑩ 결정 모순 점검은 **안 함**.
> 사실 문장 재측정: `wt/_drafts/evidence/2026-11-03/card_c/measure_facts.py` → `facts.txt`(읽기 전용, 엔진 실행 없음). 줄 번호 = master `c8ecc4e7`. `E/` = `skills/analog-gmid-design/gmid_engine/`. `P:` = gain-budget 계획 v6.38.7, `HC:` = headroom-chain 계획, `D40:` = design 40. 앞 card 양식 = `wt/_drafts/engine/XRUNF1B_SPEC_CARD.md`, 판정 기록 형식 = `.ai/verification/xrunf1b.json`, `_schema.json`. 판정 기록 자리 = `.ai/verification/20261103-xrunf1c.json`.

## 착수 조건 (문서만, 엔진 실측 불필요)

| # | 무엇 | 왜 막나 | 승인 |
|---|---|---|---|
| C-1 | **design 40 정정**: 대조표 DF-1~DF-6 | DF-1·DF-3은 지금 문언대로 구현이 불가능하거나 스스로 모순, DF-2는 자리 미정, DF-4는 design/v115 표지가 card 순서와 어긋남(원칙 17 '구현이 design과 다르면 design부터') | 검증 + design↔계획 gap 뒤 사용자 |
| C-2 | **계획 정정**(v6.38.8): PF-1~PF-3 | N6.1 card 표에 card C 행이 없고, E-26이 'card가 없어 LA-1이 자리를 정한다'고 적어 O-220·D40과 둘째 생산 자리가 된다(graph 규칙 1, 원칙 17) | 검증 + ⑩ 뒤 사용자 |
| C-3 | **보류 다리 병합 승인 자리**: 계획 P:1447 (i) | 어느 순서로 병합해도 미완료 병합이다(아래 '병합 시점'). 코드 착수는 막지 않고 병합만 막는다 | IT 보류 다리 질문에 묶어 사용자 |

병합만 막는 것: **GL-1 미병합**(P:1434 '검사 card' 문단, 판정 기록 0·`tools` 안 `scan_shared_calls` 0·`structure_checks.py` G-8 0). O-220 15 card 목록에 없다. 오케스트레이터가 card로 넣어야 한다(표지: 15 → 16).

## 착수·병합 시점 (권고)

**코드 착수 = C-1·C-2 승인 직후, base = 그때 master. IT를 기다리지 않는다.** **병합 = IT-1 + IT-2 통합 병합 뒤, EO-1 병합 뒤, HC-S 병합 앞.** 13회로 판정 실행은 병합 후보 base에서 한 번만.

| 안 | 병합 위치 | 사용자 승인 | 재측정 | 판정 |
|---|---|---|---|---|
| 가 | IT 앞 | 별도 +1(IT 질문 전에 따로) | IT-0·IT-0b를 C master에서 다시 잼(P:1600). PASS 이력 IT-1·IT-2a·IT-2b 변화표도 궤적이 바뀐 base 위로 | ⚠ 기각 |
| 나 | IT 뒤, EO-1 앞 | IT 질문에 묶으면 +0 | C가 IT 위에서 1회(P:1623) | 가능. 시작점 다리 보류 하나 더 |
| **다** | **IT·EO-1 뒤, HC-S 앞** | **IT 질문에 묶으면 +0** | **C가 그 위에서 1회. HC-S·WB-1·HC-1은 C 위에서 재므로 재측정 0** | **권고** |
| 라 | OP-5·CL-1 뒤(완료 뒤) | 0 | -- | 불가: HC-1이 C 뒤(HC:516·531·551), CL-1은 DE-1 등 뒤 |

근거.
- **'EO-1 뒤면 승인이 없어진다'는 틀리다.** EO-1 뒤에도 시작점 다리는 OP-5 전까지 '보류'(P:1447 (iii) 뒤 문장, P:2177 'EO-1 뒤 OP-5 전 기간')이고 front 점 다리는 CL-1 전까지 '보류'(P:1447 (i))다. OP-5·CL-1은 15 card 밖이다. 그래서 card C는 어느 안에서도 미완료 병합이고 승인 건수를 가르는 것은 질문을 묶느냐뿐이다. `la1a_pg/d_questions.md` §5.3(403행)의 '1건 더'는 IT 앞일 때의 계수이고 OP-5·CL-1 보류를 세지 않았다.
- **EO-1을 기다려도 경로 지연이 없다.** HC-1이 C를 기다리지만 HC-1은 HC-S 뒤, HC-S는 EO-1 뒤다(표 #7·P:1290 EO-1 행). C의 병합 자리는 HC-S와 병렬이다.
- **IT 뒤로 두는 근거가 P:1623에 이미 있다.** P:1623 '소스 파일 겹침 0'은 IT-1 기준이고 `integ/it12`와 실측 겹침은 5 파일이다: `search/fd_jacobian.py`(+5 −3, `_steps`), `search/kernel.py`(1줄 docstring), `search/CONTRACT.md`(1줄), `_module_map.py`(3줄), `tests/search/test_fd_jacobian.py`(+16). 같은 줄 끝 문장 '겹치면 card B와 같이 선후를 둔다'가 발동한다. 충돌 hunk는 card C 수정 자리와 다르다(`_steps` 대 진입 함수).
- 다른 동작 변경 card(TB-1·UB-1+NL-1 등)가 EO-1 전에 먼저 병합되면 재측정은 뒤 병합인 C 몫이다(P:1623 관행).

## 의도

선언 E_B 40에서 커널 평가 43·49·64·66(design 인용 history H4, card B 판정 `b_summary.json`에서도 43·64·66·50)이 된 예산 결함을 고친다. 모든 커널 평가를 E_total에 넣고 탐색과 감도 게이트 예산을 나눈다. 이것으로 색인 상한의 전제(커널 평가 수 ≤ E_total)가 구조로 성립하고 등록 때 fail-closed가 켜진다.

사용자 결정: X-8·X-15·X-16·X-17(`wt/_drafts/user_decisions.md`), U-96·U-98·U-99, O-220(공통 선행), X-19(순서 A → B → C). 오케스트레이터 기본안(사용자 결정 아님): D40 §2.4.14 (5) C 행의 B-1·B-2·N-2·N-3·N-4 전부. 승인 사실은 근거가 아니다(O-208) -- 원칙·물리로 재판정은 '결정 필요 항목'.

변경 종류 = **동작 변경**(P:1447 끝 괄호, 탐색 궤적과 13회로 결과가 바뀐다).

## 관찰 가능한 계약

**정의.** R = 2 × `len(sctx.domain.variables)`. E_total = 선언이면 E_B + N_T + R, 유도면 D. 탐색 예산 = 선언이면 E_B, 유도면 D − N_T − R. 이 card에서 N_T 항은 코드에 없다(층 0은 탐색 예산 안; N_T는 LA-1 범위 15 (g)가 `layer0_budget`으로 더한다). 값은 `_helpers_ceiling` 한 자리에서만 계산한다.

1. **탐색 상한.** `find_front` 안에서 감도 게이트 진입 때 `kernel_calls` ≤ 탐색 예산. 게이트 안 커널 평가 수 ≤ R. 실행 끝 `kernel_calls` ≤ E_total, 어기면 `RuntimeError`.
2. **단일 평가.** 탐색 단계의 단일 평가는 평가 전에 `search_stop`을 본다. `kernel_calls` = 탐색 예산 − 1이면 평가, = 탐색 예산이면 평가 안 하고 사유 `eval_budget`. 범위 = 재작성 범위 표 전부(사다리 칸, 주어진 시작점 포함). 층 0 시작점의 재확인(`start_points`)은 캐시 적중이라 커널 0으로 읽는다.
3. **묶음.** `fd_jacobian`은 시작 전에 상계 = 평가할 열 수 × 2(`skip`·스텝 0·`None` 제외)와 남은 한도(`ceiling` − `kernel_calls`)를 비교한다. 남은 한도 = 상계면 실행, = 상계 − 1이면 평가 0개로 `FdBudgetShortfall(needed, remaining)`. `ceiling`이 None이면 확인 없음. 묶음 도중 멈추지 않는다.
4. **shortfall 처리.** 반복 중 야코비안(외층·층 0 `jac_of`) = `_Abort("eval_budget", entry["x"])`. 첫 스텝 야코비안(외층·층 0 `steps0`) = 반복 0, 재시작 0, 정지 사유 `eval_budget`, `aborts` = (`eval_budget`,), 수락 목록 = 시작점 하나에 그 파일의 끝 선택 규칙 적용. 감도 게이트 = 잡지 않는다(결함으로 실행 정지).
5. **유도.** `evaluate`는 `eval_budget`을 쓰지 않는다. `search_ceiling`이 `eval_budget` None이고 평가 시간이 n_θ + 1개 이상일 때 첫 n_θ + 1개로 D를 계산해 `sctx.eval_budget`·`eval_budget_source`에 넣는다. 그 전이 호출에서 `kernel_calls` ≥ D − R이면 `ValueError`(사유 `time_budget_below_search_reserve`), = D − R − 1이면 통과. 전이 뒤 `kernel_calls` = 탐색 예산이면 `search_stop` = `eval_budget`(예외 없음), + 1(주입)이면 `RuntimeError`. `final=True`(`find_front`가 게이트 전에 한 번)는 평가 시간 1개 이상이면 그 전부로 유도하고 `kernel_calls` = D − R이면 통과, + 1이면 `ValueError`.
6. **게이트는 언제나 돈다.** front 점이 있으면 탐색 예산을 다 써도 돈다. `not_run` 없음. 게이트 시작 뒤 `search_ceiling`·`search_stop` 호출 0.
7. **색인 상한.** `find_front` 진입에서 `donors.open_bound(total_of)`, 끝 확인 뒤 `donors.close_bound()`. 그 사이 등록은 항목 수 > (등록된 서로 다른 (블록, 분할) 수) × (E_total + 1)이면 `RuntimeError`. E_total이 None이면 검사 안 하고, 정해진 뒤 첫 등록·끝 확인에서 잰다. 열기 밖 등록(단계 A·B, MOD8)은 검사 안 한다. `open_run`·`S3Index()`는 인자 없음 그대로.
8. **형식.** 결과 JSON 칸 변경 0. `perf.eval_budget`의 뜻은 선언 = E_B, 유도 = D로 갈린다(칸 이름 그대로, `eval_budget_source`가 구분). `resolution.E_B` 값 = `search_ceiling` 값. `perf.block_index_bound` = `donors.index_bound(e_total(sctx))`.

**문언 grep 0**(D40 §2.4.14 (4) C 행): `E/search/`에서 `_budget_stop`, `E/search/find_front.py`에서 `_e_total`·`2 *` 변수 수 항·`eval_budget_source` 분기, `E/search/kernel.py`에서 `EvalBudget`. 예산 확인용 `sctx.eval_budget` 직접 읽기는 `rg -n "eval_budget" E/search`로 남는 곳이 `search_ceiling.py`, `_helpers_ceiling.py`, `find_front.py`(perf·`run_id`), `search_context.py`(생성), `search_values.py`(설정), docstring뿐.

## 재작성 범위

(엔진 인용 용도 = 재작성 범위만, 원칙 8. 범위 근거 = 수정마다, 옛 코드는 같은 변경에서 삭제.)

| 파일(`E/search/`) | 줄(master) | 범위 | 근거 |
|---|---|---|---|
| `search_ceiling.py` | 신규 | 진입점 `search_ceiling` | 예산 숫자·유도 전이 한 자리 |
| `search_stop.py` | 신규 | 진입점 `search_stop` | 정지 사유 한 자리, 정의 셋을 대체 |
| `_helpers_ceiling.py` | 신규 | `gate_reserve`, `e_total` | E_total 한 자리(DF-2). 소비 = `search_ceiling`·`find_front`·`gate_run` |
| `kernel.py` | :160-165, :31 | 유도·import 삭제. `eval_times` 기록만 | 평가가 예산을 쓰는 구조 제거 |
| `fd_jacobian.py` | :86-111 | 부분: 필수 키워드 `ceiling`, 상계 확인, `FdBudgetShortfall` | 열 평가 규칙은 그대로 |
| `layer0_center.py` | :281 정의 삭제; :321·:503·:527·:599·:674 → `search_stop`; :603-606 → `search_ceiling`; :338·:371 shortfall; :665 앞 칸 확인 | 부분. `scipy_minimize` 전역 이름 호출 유지(NFR-4 관찰 지점) | 이 파일의 사다리·`_halton_probe`·`_maxmin`은 LA-1a가 지운다. C는 그 뒤가 아니라 앞이라 지금 고친다(DF-4) |
| `slsqp_outer.py` | :86 정의 삭제; :115 → `search_stop`; :137·:165 shortfall; :15 docstring | 부분 | 풀이 흐름은 그대로 |
| `l_bin_search.py` | :35 정의 삭제; :47·:55·:79 → `search_stop`; :10 docstring | 부분. NFR-4 정지 사유 반환 유지 | as-built 이름은 `_budget_stop`(DF-5) |
| `eps_sweep.py` | :85·:93·:94 → `search_ceiling`, :9 docstring | 부분. 기록 칸 이름 `E_B` 유지 | |
| `residual_probe.py` | :73-76 → `search_stop`·`search_ceiling`, :8 docstring | 부분. production 호출자 0(`git grep`). 규칙 둘 방지 | **표지**: 호출자 0인 파일 수정. 지우는 안은 범위 밖(U17 ② 배선 대상) |
| `start_points.py` | :39 앞 | 부분: `given`만 평가 전 확인, 닿으면 그 뒤 후보 평가 없이 `starts`에 `status` = `eval_budget` | |
| `gate_run.py` | :54 | `ceiling=e_total(sctx)`. 잡지 않음 | 게이트 = E_total |
| `find_front.py` | :41-48 삭제; :18·:117; 진입 `open_bound`; `sweep_front` 뒤 `search_ceiling(sctx, final=True)`; 끝 확인·`close_bound` | 부분. `layer0_start`·`sweep_front` 전역 이름 호출, 진입 재확인 (c), runs 줄 `env_fp`, notes `l_search` 유지 | |
| `s3_index.py` | 클래스 | 부분: `open_bound`·`close_bound`·`index_bound`, (블록, 분할) 수 | fail-closed (5) |
| `open_run.py` | docstring :9 | 서명 불변, '생성자에 필수 인자' 문장 정정 | DF-1 |
| `search_values.py`:46, `search_context.py`:21·:64, `CONTRACT.md`:230·:367-370·:466·:497·:528·:535-537·:1113, `_module_map.py` | 문구·항목 | 갱신. 뜻 갈림 한 줄 포함 | 같은 변경에서 맞춤 |
| 함수 레지스트리 §2, D40 §2.4.13 벽시계 경로 인용 | 행 | 갱신 | 레지스트리 §0 규칙 4 |

바꾸는 문서는 test 없음. test 작성 주체 몫: 표 '판정 유형 근거'. `tests/search/test_fd_jacobian.py` 8곳·`test_layer0_center.py` 1곳의 직접 호출에 `ceiling`이 필요하다. `open_run()` 호출 320곳(test 87 파일)은 **안 바뀐다**(DF-1의 이득).

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

새 이름 충돌 0(`facts.txt` §4, 엔진·test). `Donors` 추상 메서드는 늘리지 않는다(`entry_count`와 같은 S3Index 조회 선례, `tests/core/test_compute_block.py:90` 하위 영향 0).

## graph 단일 정본

* 새 graph 필드 0. 블록 입력·출력 변경 0.
* E_total·R 계산 자리 하나(`_helpers_ceiling`), 사본 `find_front._e_total` 삭제. 탐색 예산 = 그 값에서 유도.
* `S3Index`는 E_total 값을 보관하지 않고 참조 `total_of`만 쥔다(graph 규칙 4). (블록, 분할) 수는 자기 키에서 나온 파생이고 다른 생산자가 없다. `perf.block_index_bound`는 같은 메서드를 읽는다.
* `sctx.eval_budget`·`eval_budget_source`: 새 칸 없음. **원칙으로 재판정**(as-built는 근거 아님): D는 벽시계 표본에서 나온 실행 제어 값이고 설계 값·입력 버전이 없어 graph 필드 대상이 아니며 허용 저장소 (c) 실행 계수 부류다. 틀리면 멈추고 보고.
* **표지**: 칸 하나가 선언 = E_B, 유도 = D로 뜻이 갈린다. 칸을 나누면 결과 JSON 변경이고 design이 안 나눴다. 원칙 7(graph 필드 규칙)의 직접 대상은 아니나 같은 냄새다. 판정자가 확인 항목으로 본다.
* 같은 입력 재계산 래칫: 새 B 0, 이 card 배정 B 없음. 측정 도구는 GL-1 몫.

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

동작 변경(N6.3): 정의 손계산 오라클 toy + 봉인 불변식 + SPICE oracle 판정 + 검증자 값 변화표. 비트 동일 요구 안 함. 결정성은 항상 검사.

| 다리 | 상태 |
|---|---|
| 정의 toy | 계약 1~7 경계값 test |
| 봉인 불변식 | 값 정의 불변, 받은 점 봉인 통과 그대로(변화표에서 새 위반 0) |
| SPICE 시작점 | **보류**(채울 card = EO-1; 병합이 EO-1 뒤면 판정, 꺼짐 정의 판 적음, 옛 식 다리 = OP-5) |
| SPICE front 점 | **보류**(채울 card = CL-1) |
| 변화표 | 회로·칸·옛 값·새 값, 원인 미설명 0 |

→ 병합해도 '미완료'. 판정 기록에 '미완료(보류 다리: 회로·metric 목록, EO-1·OP-5·CL-1)'. 계수에 안 든다.

**red 자리.** 새 키워드 인자의 `TypeError`는 red가 아니다. **설계 완료 조건 (i) `kernel_calls` ≤ E_total만으로는 red가 안 난다**: 선언 E_B 40에서 card B 판정의 as-built 값은 8회로 전부 이미 E_total 안이다(cg 43 ≤ 52, folded 64 ≤ 72, nmcnr 66 ≤ 86, two_stage 50 ≤ 60, tsf 43 ≤ 64, pushpull 40 ≤ 56, sf 40 ≤ 92, current_reuse 40 ≤ 116; `facts.txt` §6). 그래서 red = **게이트 진입 때 `kernel_calls` > 탐색 예산**(계약 1)이다. 관찰 = `find_front` 모듈의 `run_sensitivity_gate` 전역 이름을 감싸 진입 때 계수 기록(엔진 무변경). base: 탐색 묶음이 예산을 넘는 합성 입력과 실회로에서 실패. 기준 강화라 승인 불요, 표지만.

test 목록(이름 착수 때 충돌 확인, 작성 = test 주체): D40 §2.4.14 (5) C 행 test 칸 그대로 + `test_search_ceiling.py`·`test_search_stop.py`·`test__helpers_ceiling.py`(규칙 H)·`test_s3_index.py`(열기·닫기, 열기 밖 검사 없음, `index_bound`)·`test_find_front.py`(계약 1 게이트 진입 관찰)·`test_g10_no_recompute_9circuits.py`(library 13, 게이트 진입 단언 추가, 유도 실행 1회로 이상).

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 입력: 경계값은 정의 문장에서 손으로 낸다(예산·상계·R). 피검 함수로 기대값을 만들지 않는다. 실회로 판정의 기대값은 불변식(≤)이고 값 복사가 아니다.

## 거부해야 할 입력

- 유도 전이에서 `kernel_calls` ≥ D − R → `ValueError`(`time_budget_below_search_reserve`). `CANDIDATE_FAILURE_CLASSES`에 안 잡힌다.
- 게이트 `FdBudgetShortfall` → 잡지 않음. 실행 끝 `kernel_calls` > E_total → `RuntimeError`. 전이 뒤 `kernel_calls` > 탐색 예산 → `RuntimeError`. 색인 등록 상한 초과 → `RuntimeError`.
- `ceiling` 빠진 `fd_jacobian` → `TypeError`. 두 번째 `open_bound`(닫기 전) → `ValueError`.
- 선언 실행은 예산 거부가 없다(작은 E_B도 받음, X-17).

## library 회로 적용 여부

library 13 전수(O-181) n/N 측정: 선언 E_B 40 + 미선언(유도) 실행. 단계 A·B 까지만인 회로와 탐색 없는 회로는 분모·사유를 따로 적는다(test의 `NOT_SEARCHED`, 회로 이름을 규칙에 쓰지 않음). 판정 실행의 `front_budget_s`는 card B 판정의 값을 판정 기록에서 읽는다. held-out 0개 -- A' 일반성 판정 정지. 메모리: 회로마다 프로세스를 나눠 순차.

**n_θ(기록 `la1a_pg/m1_current_facts.jsonl`)**: cg 6, pushpull 8, two_stage 10, tsf 12, folded 16, ngcc 21, nmcnr 23, sf 26, current_reuse 38. 새 4회로(cnr·erfc·r2r·rfc)는 미측정.

## 무동작 판정 입력(무발동 값)

탐색이 예산 전에 끝나는 실행(E_B를 넉넉히 선언): `FdBudgetShortfall` 0, `eval_budget` 사유 0, 게이트 전 궤적이 card B 판정 궤적과 같음(같은 θ·`seq`, §2.4.13 비교기). 묶음 확인·단일 확인이 값을 바꾸지 않음을 보인다. 넉넉한 값은 `2 × n_θ`·바퀴 수에서 유도한 것을 판정 기록에 적는다.

## 재현할 수치

회로마다(판정 기록의 값만 인용): `perf.kernel_calls`, E_total(`perf.eval_budget`·`eval_budget_source`·n_θ에서), 게이트 진입 때 `kernel_calls`, 게이트 안 커널 평가 수, R, `block_index_entries`, `block_index_bound`, `stops_eval_budget`, 층 0·외층 정지 사유 분포, front 점 수, G-10 판정 1·5. 값 변화 목록(회로·칸·옛 값·새 값, D40 §2.4.14 (6)). 비교 기준 = 병합 직전 master. 숫자를 card에 박지 않는다.

## 결정 필요 항목

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| Q-C1 묶음 상계 2 × 열 수를 그대로 쓰나(X-8) | 없음(실행 제어. 점의 값·봉인과 무관) | D40 §2.4.14 (5) C (5). 원문 쪽 해당 없음 | 코드 유도만, 미측정: n_θ ≥ 20인 4/9회로(ngcc·nmcnr·sf·current_reuse)는 E_B 40에서 시작 평가 뒤 남은 39 < 2n_θ라 **FD 묶음이 한 번도 시작되지 않는다**(열 수는 스텝 0·None을 빼면 줄 수 있다). 나머지 회로도 층 0이 예산을 먼저 쓴다(N_T 없음) | **조건부**. 규칙은 맞다(상한을 구조로 보장, 대안 '열마다 확인'은 묶음 중간 정지라 FD가 깨진 채 나옴). 다만 **E_B 40 판정 실행은 예산 상한만 재고 탐색 품질을 못 잰다**. X-17 (v) 유지 권고, 유도 실행을 13회로 전수로 |
| Q-C2 재측정(Q0)의 E_B | 위와 같음 | O-220 재측정, E-13 '비교 전제 E_B 선언' | 앞 사례 E_B 2000(`evidence/2026-11-01/icmr4/`), 미측정 | **표지**: card C 뒤 E_B 40으로 재면 위 4회로는 출발점만 재므로 Q0를 못 가른다. 재측정 설계자가 FD가 도는 E_B를 정할 것 |

사용자 결정이 필요한 것은 위에 없다(규칙 유지 권고). 바꾸려면 X-8·X-17 재검토(O-208).

## 원래 취지와 다름

1. **S3Index 생성자 필수 인자 → 열기 메서드**(DF-1). D40 §2.4.5(card B J-5 오케스트레이터 기본안) 문언과 다르다. X-8 '등록 때 fail-closed'는 그대로다. offset-strategy PD-7 'OS-5가 B_S0를 생성자에'는 그대로이고 'E_total,v 등록'과 오히려 맞다.
2. **색인 상한 검사 범위 = `find_front` 안**(DF-6). D40 (5) '실행 수명 색인 전체'보다 좁다. MOD8 `evaluate(geometry=)`가 E_total 밖이라(D40 C (5)) 전체에 걸면 자기모순이다. MOD8 예산 = U16 몫.
3. **완료 조건 강화**(게이트 진입 단언). 약화 아님.
4. **card C가 LA-1a가 지울 코드를 고친다**(사다리·`_halton_probe`). 순서상 필요(C → HC-1 → LA-1a). 과도기 조건문은 아니다.
5. 15 card에 GL-1 없음(O-220 '최소 15'). 병합 전제라 16.

## 절차

(DEC-86 넷, 정본 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리(WP-13).
2. 깨진 test·기준 약화는 숨기지 않고 보고(`broken_tests`·`criteria_weakened`·`retired_tests`).
3. 변경당 커밋 1.
4. 매 변경 뒤 새 test 체계 전체 실행.

* 판정 기록: 독립 검증자, `.ai/verification/20261103-xrunf1c.json`(`_schema.json`). N6.3 넷(G 확장 lint·값 타입 위치·소유표·G-10)과 '같은 입력 재계산 0' 포함. 구현 뒤 design ↔ 구현 gap.
* interface card는 선택 보조. 위 시그니처 표가 입력.
* 흐름 = N3.12.3 순서 2~6 역할 분리(폐기된 gate·push 절차 제외, 앞 card 관행).

## 작성 전 실측

(명령과 결과 = `card_c/facts.txt`. 사실 문장은 쓰는 자리에서 쟀다.)

1. 사실 재측정: 예산 자리 전수 §1, `open_run` §2, 직접 호출 test §3, 겹침 §5, n_θ §6, 계획 줄 §7, GL-1 §8, v115 표지 §9. **안 잼**: 13회로 실행, 새 4회로 n_θ, 층 0이 쓰는 커널 수.
2. 엔진 인용 용도: 재작성 범위뿐. 예외 표지 = `sctx.eval_budget` 칸(원칙으로 재판정함).
3. 이름 충돌: 0(§4). `test__helpers_ceiling.py` 규칙 H 꼴은 `tests/search/test__helpers_*.py` 선례. test glob 대상 아님(`*.topology.json` 등).
4. 원칙의 계약화: '모든 커널 평가' = 계약 2·3 + 재작성 표. MOD8만 제외(표지).
5. 쓰기 경로: 역할 분리 그대로.
6. 계획서 소비자: `_e_total`·`_budget_stop`은 계획에 E-26만(PF-1). `search_ceiling` 등은 design만.
7. 미배선: 소비자 표. 새 def 전부 호출자 ≥ 1.
8. 기존 test: `eval_budget` 21 파일, `E_B` 12 파일, `start_points` 10 파일 grep -- 궤적 값 단언 목록은 test 주체(D40 (6)). 약화 없음.
9. 승인 줄: 동작 변경 = X-8·X-15·X-16·X-17, 착수 = O-220. 머리 `approval` id는 승인 기록을 만든 뒤 넣는다(지금 없어 뺐다).
10. 범위 계약: 'card 커밋들의 diff'로 판정.
11. test 이름: 판정자가 충돌 확인.
12. 같음 판정: 게이트 전 궤적은 §2.4.13 비교기, `set` 비교 없음.
13. red 모양: '판정 유형 근거'. 시그니처가 안 바뀌는 `find_front`가 맡는다.
14. 상수·회로 이름: `2`는 FD 시도 방향 수로 산술(규칙 D 허용), 그 밖 0. 회로 이름 0.

---

## 부록 A. design(cfe2e316, D40 §2.4.14 (5) C 행) 대조표

대조 범위: 계획 v6.38.7, O-202~O-224 행 예산 키워드 대조(`E_B`, `E_total`, `평가 예산`, `eval_budget`, `card C`, `감도 게이트`, `fd_jacobian`, `N_T`, `front_budget` -- O-220만 걸림) + 문맥상 O-214·O-217·O-218(LA-1a)·O-223(WB-1). **줄 단위 전체 대조 아님.** design/v115(C 행 차이 = '대상 소멸' 표지 3곳, 9 → 13 세 곳).

| # | 대조 항목 | 판정 | 처리 |
|---|---|---|---|
| OK | 규칙 (1)(2)(5)(6)(7)(8), X-8·X-15·X-16·X-17, U-96·U-98·U-99 | 맞음 | 그대로 |
| OK | O-202~O-212(봉인·꺼짐·창), O-215·O-221·O-222·O-224 | 무관(예산에 안 닿음) | -- |
| **DF-1** | §2.4.5 문단 'card C가 생성자 필수 인자로 더한다'(master D40:404, v115:314) | **틀림, 구현 불가**. `open_run()`이 `run_stage_a`보다 먼저 불린다(M-c)인데 R은 그 뒤 만드는 `sctx.domain.variables`를, D는 평가 시간을 읽는다. 값이 그때 없다. offset-strategy PS-6이 B_S0에서 같은 순환을 이미 적었다. 그대로면 test 320곳을 고치고도 값을 못 넣는다 | 생성자 불변, `open_bound(total_of)` |
| **DF-2** | (3) `E_total 계산 자리를 한 곳으로 정하고` | **자리 미정**. `search_ceiling`은 탐색 예산을 낸다. 규칙 A로 같은 파일에 둘째 진입점 불가 | `_helpers_ceiling.e_total` |
| **DF-3** | (3) '게이트 시작 뒤 `search_ceiling` 안 부름' 대 (5) '`fd_jacobian` 안에서 묶음 확인' + '게이트만 E_total' | **모순**. 게이트도 `fd_jacobian`을 부른다. 함수가 어느 한도를 쓸지 받아야 한다. 호출 test 9곳 | 필수 키워드 `ceiling` |
| **DF-4** | design/v115 '대상 소멸'(Halton 한도·Halton 평가·사다리 칸, D40 v115:760·782) | **틀림(순서)**. 지우는 card = LA-1a(P:1999·N6.39)이고 C → HC-1 → LA-1a(HC:531, 표 #16·#22)다. card C 때 코드가 있다. 놔두면 '모든 커널 평가' 보장에 구멍 | v115 표지를 'LA-1a가 지울 때 함께 사라짐, card C 때는 있음'으로 |
| **DF-5** | as-built 인용: (d) `_exhausted`(0건 -- 지금 `l_bin_search.py:35 _budget_stop`, 정의 셋), `gate_run.py:63`(→ :54), `kernel.py:153-158`(→ :160-165), 층 0·외층 줄 전부, 9회로(master만, v115는 13) | 낡음. 규칙은 그대로 | 이 card 재작성 표로 대체. 표지만 |
| **DF-6** | (9) 색인 상한 대 (5) MOD8 범위 밖 | **문장 없음**. 실행 수명 색인과 E_total 범위가 다르다 | `find_front` 안 검사 |
| m | §2.4.5 'E_total 정해지는 순간 한 번 확인' | 첫 등록·끝 확인으로 충족 | 문언 맞춤 |
| m | O-223 Q-W1 실현 평가, CL-1 재풀이가 `find_front` 안에서 커널을 더 쓰면 (8) 끝 확인에 걸림 | **미확인**(자리 = WB-1·CL-1 design) | 그 design에 표지 전달 |
| **PF-1** | P:2464 E-26 / D40 v115:1528 'card C는 현 계획에 card가 없어 LA-1이 자리를 정한다' | **틀림**(O-220 후). LA-1 15 (g)와 C 두 자리가 E_total 자리를 정한다 | 'C가 자리를 정함, LA-1 15 (g)는 N_T 항을 `layer0_budget`으로 더함'. 완료 칸 'N_T 0 고정 grep 0'은 C가 먼저 만족 |
| **PF-2** | N6.1 card 표에 card C 행 없음(P:1287 표 머리부터 전수 grep -- 표 안 'card C'는 WB-1 행의 겹침 언급뿐) | 누락. N6.3 '결정 뒤 card 행' | 행 추가: 선행 card B(병합됨), 뒤 HC-1, SPICE 다리 EO-1·OP-5·CL-1 |
| **PF-3** | P:1563·P:1623 '겹침 0' | 낡음(IT-2 포함 5 파일) | 문언 + 선후 IT → C |
