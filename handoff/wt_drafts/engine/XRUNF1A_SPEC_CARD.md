# XRUN-F1 card A (RT + W) spec card 초안 (card id `xrunf1a`)

- 작성: 2026-10-15. 개정 2026-10-16(NFR-4 card 2 병합본 ebd7b3c 재측정 반영 -- `wt/_scratch_xrunf1a_card/recheck_ebd7b3c.md`). 읽기 전용 실측과 초안만 담았다. 엔진·test·git 브랜치는 고치지 않았다.
- **card base = `6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`**(NFR-4 card 2 병합 뒤 master. design 40 §2.4.13 763행 'card A의 base = card A 직전 master', J-7과 같음).
- 실측 기준(쓰는 자리에서 다시 잼)
  - 재측정: `wt/nfr4c2-integ` HEAD `ebd7b3c`(NFR-4 card 2 병합본)에서 grep·sed·`git -C` 읽기 전용만(실행 없음). 옛 측정(609965d)은 `609965d`·`cfe2e31`·`e8b619f`가 `skills/` 아래 바이트 동일이므로, 엔진·test 차이는 전부 NFR-4 병합분(31파일)이다. 아래 줄 번호는 ebd7b3c 기준이다.
  - design 근거: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §2.4.6 '첫 평가 버림 제거'(414~429행, cfe2e31 J-4 보완 포함), §2.4.14 (1)~(7)(786~877행), §10.4 공통 완료 조건(1910~1930행), §11 XRUN-F1 행(2015행). 42 `…42-gap-checklist.design.md` D-XR1·D-XR2(282~283행), D-GR6(272행). 계획 v6.11 U-91·U-94(1308·1311행).
  - 사용자 결정 원문: `wt/_drafts/user_decisions.md` 'XRUN-F1 design 착수 결정' X-1~X-5, 'XRUN-F1 design 결정 1~8' X-6~X-13, X-14.
- 경로 접두 `E/` = `skills/analog-gmid-design/gmid_engine/`.

---

## 1. spec card

### 1.1 목표 (사용자 의도 원문)

- 취지 원문(2026-10-15): "계산 재사용은 처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용되게 한다는 것이 원래 취지였어".
- X-1 (1): ln 좌표 원값 보존 규칙을 slsqp_outer·층 0 공용 정본 하나로. X-1 (2): sweep_memo 첫 평가 버림을 U17 ③에서 이번으로 앞당겨 제거(design §2.4.6 '계수 평가 = 실제 첫 평가').
- X-6: RT 정본 대체 대상에 감도 게이트 `gate_run.py:55-61` 포함(기준선 재측정 대상). X-14: `ThetaCoords`는 좌표 변환과 시작 좌표 원값 보존만, clip 옵션 없음. 외층·층 0은 변환 전에 자기 상자로 자르는 단계를 명시, 감도 게이트는 자르지 않음.
- X-4: RT 수정으로 탐색 궤적이 ulp 수준에서 변함 → card 기준선 재측정 승인(값 변화 목록은 판정에서 보고).
- 이 card의 목표 한 줄: **같은 점은 같은 θ 비트가 되게 하고(RT), LUT memo 상한을 재려고 첫 평가를 따로 돌려 버리지 않는다(W). 실행의 첫 커널 평가가 곧 계수 평가다.**

### 1.2 구현하는 design 절

| design 절 | 내용 | 이 card |
|---|---|---|
| 40 §2.4.14 (2) | `ThetaCoords` 정본(만들기·되돌리기·상자 자르기(호출부)·성질·쓰는 곳) | 구현 |
| 40 §2.4.6 '첫 평가 버림 제거' 표(417~426행)와 삭제 문장(429행) | `LutMemo.counting`(`table_cache=None`), `open_count`·`fix_bound`, `bound_state`, n_θ, 창, 키 동치(`canonical_key`), 상한 고정, 옮기는 순서(`BoundedLRU.adopt`), `stats()`(계수 상태 capacity=None), 첫 커널 평가 없는 실행, 독립 계수 | 구현 |
| 40 §2.4.14 (3) A 행 | 재작성 범위(theta_coords 신규, slsqp_outer·layer0_center·gate_run 부분 수정, lut_memo 부분 수정, **`core/bounded_lru.py` 부분 수정(`adopt`, 821~822행)**, sweep_memo 삭제, `_wire_sweep_memo` 단위 재작성, kernel A 부분, `__init__`·`_module_map`·CONTRACT·레지스트리 갱신, `centre_start` docstring) | 범위 정의 |
| 40 §2.4.14 (4) A 행 | 삭제 이름별 grep 범위(`def to_theta`는 '`E/search/` 중 `theta_coords.py` 밖' -- 849행, J-1 해소) | 완료 조건(1.6) |
| 40 §2.4.14 (5) A 행 | 완료 조건 (i)~(iv), test 초안, 판정 측정 | 1.6, interface card |
| 40 §2.4.14 (6) | 기준선 재측정·값 변화 목록 | 판정(interface card A-5·A-6) |
| 42 D-XR1·D-XR2 | DEV → 완료 시 OK | 확인 행 |
| 42 D-GR6 | 문구(첫 평가 버림 제거는 XRUN-F1 A) | 확인만(인스턴스 하나·`call`·`_Unmemoized` 제거는 ③) |

범위 밖(이 card에서 하지 않음): 블록 결과 색인·`RunCounters`·`graft`·`Donors`·부분 스냅샷·`perf.blocks`(card B), FD 묶음·감도 게이트 예산(card C), LUT memo 인스턴스 하나·`memo.call`·`_Unmemoized` 제거·B_r의 U_S0·층 0 항(U17 ③), 감도 게이트 기준점이 상자 밖일 때 '검사 못 함' 보고(후속, X-14), NFR-4(BLAS 고정·재확인·`env_fp`·BP1 끌어올림·L-b 정지 사유 -- base에 병합됨(`E/core/blas_env.py` 있음). card A는 그 코드를 바꾸지 않고 1.3.6 보존 계약을 지킨다), `_budget_stop` 복사 3곳(`slsqp_outer.py:95-100`, `layer0_center.py:280-285`, `l_bin_search.py:35-40` -- 합치기는 card C).

### 1.3 삭제·변경 목록 (ebd7b3c 재측정)

#### 1.3.1 엔진 소스

| # | 대상 | 위치(실측 ebd7b3c) | 처리(design) | 비고 |
|---|---|---|---|---|
| A1 | 새 파일 `E/search/theta_coords.py` | 신규 | frozen dataclass `ThetaCoords` 하나(규칙 A 진입점 1개): `ThetaCoords.start(variables, theta)`(classmethod), `to_theta(x)` | 공개면은 J-2 판단(`start`·`to_theta`·읽기 전용 `x0` tuple, search `__init__` 재수출). 규칙 A: 메서드가 `from_*`·dunder·property 밖이라 '데이터 선언 모듈'이 아니고 일반 판정(진입점 개념 1) |
| A2 | 외층 `solve_eps` | `E/search/slsqp_outer.py:52-77`(`_layout`: `:71-77` `x0`·`exact` 계산), `:106`(언팩), `:112-120`(`def to_theta` -- clip `:115`, 원값 분기 `:116-117`), 쓰는 곳 `:131`(`evaluate`), `:150`·`:178`(`fd_jacobian(..., to_theta, ...)`), `:172`(`point(np.asarray(x0))`). 보존: `:104` 재확인 (e)(`solve_eps` 첫 줄), `:95-100` `_budget_stop` | 부분 수정: `_layout`은 변수·고정값(L 단일 칸 `fixed`와 변수 밖 성분)만, 시작 좌표·원값은 `ThetaCoords.start(variables, 시작 θ + L 단일 칸 고정값)`. 풀이 시작 좌표 = clip(x0ᵢ; loᵢ, hiᵢ), 풀이기가 준 x는 clip 뒤 `coords.to_theta`. 사본 `exact`·`def to_theta` 삭제 | 시작 θ는 as-built `_layout`의 `fixed`(`:61`)를 넣은 사전 -- 동작 그대로(design (2) '만들기' 행) |
| A3 | 층 0 `_maxmin` | `E/search/layer0_center.py:288-306`(`_maxmin` 머리·`def to_theta` `:301-306`, clip `:304`), 시작 좌표 `:371`(`_coord` 사용), FD `:340`·`:373`, 평가 `:326`, `_coord` 정의 `:429-430`. 보존: `:392` `scipy_minimize` 모듈 전역 호출, `:657` 재확인 (d), `:243-258` BP1 `lift_exponent`, `:280-285` `_budget_stop` | 부분 수정: `variables`(하한 조정 뒤 `:290-292`)와 `theta0`으로 `ThetaCoords.start`. 시작 좌표 = clip(x0ᵢ), 풀이기 x는 clip 뒤 `to_theta`. `_coord`·`def to_theta` 삭제 | 호출 `:699`(`_maxmin(sctx, variables, theta, cells, first, tag)`) 서명 불변 |
| A4 | 감도 게이트 `run_sensitivity_gate` | `E/search/gate_run.py:54-61`(`theta = dict(base.theta)`, `x` 계산 `:55`, `def to_theta` `:57-61`), 사용 `:63` | 부분 수정: `ThetaCoords.start(sctx.domain.variables, dict(base.theta))`, x = 시작 좌표(**자르지 않음**), `fd_jacobian(..., coords.to_theta, ...)`. `math` import(`:13`)는 남는 쓰임이 없으면 삭제(실측: 쓰임 `:55`·`:60` 둘 다 대체 대상 → 삭제) | X-14. 변수는 조정 없는 `sctx.domain.variables`(as-built `:49`) |
| A5 | `centre_start` docstring | `E/search/layer0_center.py:649-650`('`build_search_context`가 LUT memo 상한을 정하는 첫 평가(설계 40 §7.3)도 이 점을 쓴다') | 고침: 'n_θ(변수 수)만 `_wire_sweep_memo`가 이 함수로 잰다' | design (3) 마지막 행 |
| A6 | `LutMemo` | `E/lut/lut_memo.py:10-12`(docstring의 `from_sweep`), `:25-36`(`_Unmemoized`, docstring `:26`의 `from_sweep`), `:44`(`_zero_ok`), `:53-58`(`from_sweep`) | 부분 수정: classmethod `LutMemo.counting(lut, n_theta, *, table_cache=None)` 신규, 메서드 `open_count()`·`fix_bound()`·읽기 전용 속성 `bound_state` 신규, `from_sweep` 삭제. 상한 식(`(n_θ + 1)·U_eval,r`), derived 영역 `BoundedLRU(슬라이스 수 × len(DERIVED_TABLES))`(`:50`), `_Unmemoized`(U = 0 영역), 디스크 층(`lookup_persistent` `:64-69`)은 그대로 | 계수 상태 세부 규칙은 design §2.4.6(cfe2e31 J-4 (a)~(g)) 그대로 -- interface C3 |
| A6b | `BoundedLRU` | `E/core/bounded_lru.py`(`canonical_key :7-9`, 최근성 `:37·55`) | 부분 수정: 메서드 `adopt(key, value)` 신규 -- 원 key를 받아 `lookup`과 같은 `canonical_key` 적용, hits·misses 불변, 상한 넘으면 가장 오래된 것 퇴출·`evictions` 계수·퇴출 기록 | design (3) 821~822행, J-4 (b). 계수 상태 memo 고정 때 옮기기에 쓴다(배선) |
| A7 | `E/lut/sweep_memo.py` | 전체(33줄: `_CountingMemo` `:14-25`, `sweep_memo` `:28-33`) | 파일 삭제 | |
| A8 | lut 재수출 | `E/lut/__init__.py:74`(`from .sweep_memo import sweep_memo`), `:157`(`__all__` `"sweep_memo"`) | 삭제 | `LutMemo`(`:18`)는 그대로 |
| A9 | `_wire_sweep_memo` | `E/search/search_context.py:134-150`(docstring `:135-137`, `centre_start` `:138`, `first_eval` `:141-147`(`copy.copy` `:142`), `sweep_memo` 호출 `:149`, 설치 `:150`), 호출 `:217` | **단위 재작성**(함수 전체): n_θ = `len(centre_start(ctx)[0])`를 먼저 재고(그 사이 조회는 호출자 memo), `LutMemo.counting(old.memo.lut, n_θ, table_cache=old.memo.table_cache)`를 `LutAccess(memo, old.w_keys)`로 `ctx.dc`에 넣는다. 임시 컨텍스트·평가 없음 | 이름 `_wire_sweep_memo`는 design이 유지(§2.4.6 '만들기' 행). 남는 import 정리: `copy`(`:23`, 다른 쓰임 0), `evaluate`(`:37`, 다른 쓰임 0), `sweep_memo`(`:29`) 삭제. `dataclasses`(import `:24`, 쓰임 `:213`)·`LutAccess`·`centre_start`는 남는다. 보존: `:27` import의 `blas_environment`, `:203-204` 재확인 (b) |
| A10 | `evaluate` 창 | `E/search/kernel.py:111-115`(재계산 계수·`kernel_calls`·`seq` 증가 = 커널 평가 시작), `:120`(`size_and_seal`), `:159`(`EvalResult` 생성), `:161-162`(캐시·S3) | 부분 수정: 커널 호출 직전 `memo.bound_state == "counting"`이면 `memo.open_count()`, 결과(`EvalResult`)를 만든 직후(성공·후보 실패 모두) `"window_open"`이면 `memo.fix_bound()`(design §2.4.6 '창 열기·닫기' 행). memo = `sctx.dc.lut.memo`(`geometry` 경로 `:93`도 같은 memo). 생성자 memo(`"fixed"`)로 도는 경로는 두 메서드를 부르지 않아 그대로 돈다 | 평가 캐시 적중(`:98-103`)·정의역 밖(`:106-110`)은 커널 평가가 아니다 |
| A11 | `find_front` `perf` | `E/search/find_front.py:130-141`(`memo_evictions`·`perf.update`). 보존: `:78` 재확인 (c), `:117` notes `l_search`, `:153` runs 줄 `env_fp`, `layer0_start`·`sweep_front` 모듈 전역 호출 | 부분 수정: `perf.lut_memo_bound` = `bound_state`가 `"fixed"`면 `"fixed"`(생성자 memo로 돈 탐색 포함), 아니면 `"unfixed_no_kernel_eval"`(첫 커널 평가 없이 끝남) | 결과 JSON 형식 변경(1.5) |
| A12 | 모듈 지도 | `E/_module_map.py:62`(lut 층 표의 `"sweep_memo.py"`), `:275-276`(`lut_memo.py` 책임 문장 'sweep 상계 상한'), `:298-299`(`sweep_memo.py` `ModuleEntry`), search 층 표 `:136-155`, `:908-909`(`search_context.py` 책임 문장). NFR-4 `blas_env.py` 항목(`:45`, `:197-199`)은 그대로 | `sweep_memo.py` 두 곳 삭제, `lut_memo.py` 문장을 '계수 상태로 시작해 첫 커널 평가 뒤 상한 고정'으로, `search/theta_coords.py` `ModuleEntry`(kind `"entry"`, 진입점 `ThetaCoords`, 책임 한 문장 = '탐색 좌표 x ↔ θ 값(ln 좌표 원값 보존)', 계획 ID `("U-91", "NFR-2", "40 §2.4.14")`) 추가, search 층 표에 `theta_coords.py`(search 안 import 없음 → `slsqp_outer.py`·`layer0_center.py`(`:150`)·`gate_run.py`(`:151`)보다 앞 층) | **사실**: `_module_map`의 `LAYERS`·`MODULES`는 `tests/structure`가 기계 검사하지 않는다(엔진 test에서 `_module_map`을 읽는 곳 = `tests/core/test_engine_code_fp.py`의 가짜 트리뿐, `structure_checks.py`에 참조 0). 리뷰 확인 항목 |
| A13 | 함수 레지스트리 | `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md:635`('LUT memo 상한 배선' 행, 정본 `lut.sweep_memo`), §2 개념별 정본(31~63행, `:61` = `read_front_entries`, `:62`·`:63` = NFR-4 BLAS·층 0 끌어올림 -- 마지막 행 `:63`) | **code 주체 몫, 같은 변경**: `:635` 정본을 `LutMemo.counting`·`open_count`·`fix_bound`(배선 = `_wire_sweep_memo`와 `evaluate`의 첫 커널 평가)로 바꾸고 `sweep_memo`·`from_sweep` 문구 삭제. §2 끝(`:63` 뒤)에 행 '탐색 좌표 x ↔ θ 값(ln 좌표 원값 보존)' = `gmid_engine.search.theta_coords.ThetaCoords`(쓰는 곳 = 외층·층 0·감도 게이트) 추가 | design (3) '함수 레지스트리' 행. 2026-10-15 실측: 레지스트리에 `ThetaCoords`·`theta_coords`·`to_theta`·'원값' 0건 |

#### 1.3.2 CONTRACT (실측 위치)

| 위치 | 처리 | 근거 |
|---|---|---|
| `E/lut/CONTRACT.md:45`(머리 r7 요약 '(7) `sweep_memo`(2.2, `LutMemo.from_sweep` 배선)') | 이름 없이 고침(예: '(7) [XRUN-F1 A로 삭제] 첫 평가 상한 배선') | (4) 범위 '엔진 전체(CONTRACT 포함)'. CONTRACT 머리 요약은 history 문서가 아니다 |
| `E/lut/CONTRACT.md:77`(층 표 `sweep_memo.py` 행) | 삭제 | |
| `E/lut/CONTRACT.md:285-287`(§2 상한 인자 예외 문장·`from_sweep` 항목) | `LutMemo.counting`·`open_count`·`fix_bound` 계약으로 교체(interface card C3) | |
| `E/lut/CONTRACT.md:304-312`(§2.2 `sweep_memo` 절 전체, '소비처' 문단 포함) | 삭제하고 §2.2를 '계수 상태 memo' 절로 다시 쓴다 | |
| `E/search/CONTRACT.md:172-173`('효율 수정(r5)' -- `solve_eps` 원값) | 정본 `ThetaCoords`를 가리키게 고침 | |
| `E/search/CONTRACT.md:179-212`(§0 파일·층·진입점 표) | `theta_coords.py` \| `ThetaCoords` 행 추가 | |
| `E/search/CONTRACT.md:431-442`(§3.9 `build_search_context`) | 탐색 memo = 계수 상태 memo(`LutMemo.counting`, n_θ = `centre_start` 변수 수), 컨텍스트 생성 안 커널 평가 0 | `:432` NFR-4 재확인 (b) 문장은 지우지 않는다 |
| `E/search/CONTRACT.md:443-`(§3.10 `evaluate`) | 첫 커널 평가의 창 열기·닫기(`bound_state`) | |
| `E/search/CONTRACT.md:480-485`(§3.13 `solve_eps`, x0 문장 `:483-484` 'x0 = 시작 θ(log 변수는 ln), bounds 로 자름') | `ThetaCoords` + 호출부 상자 자르기로 | `:481` NFR-4 재확인 (e) 문장은 지우지 않는다 |
| `E/search/CONTRACT.md:386-`(§3.21 4 최대-최소) | 시작 좌표·되돌리기 = `ThetaCoords` + 상자 자르기 | |
| `E/search/CONTRACT.md:525-526`(§3.16 `perf` 목록, 머리 `:512`) | `lut_memo_bound` 추가 | 1.5. `:513-514` NFR-4 재확인 (c)·`env_fp`·notes `l_search` 문장은 지우지 않는다 |
| `E/core/CONTRACT.md`(`BoundedLRU` 절) | `adopt(key, value)` 계약 추가(원 key, 계수 불변, 퇴출 규칙) | A6b |
| `E/search/CONTRACT.md` 새 절 | `ThetaCoords` 계약(interface card C1)과 감도 게이트 좌표 규칙(자르지 않음, X-14). 실측: 지금 search CONTRACT에 `run_sensitivity_gate`·`gate_run` 언급 0 | design (3) 'CONTRACT(search)' |

#### 1.3.3 test (test 주체 몫 -- 이 card가 삭제·고칠 목록, 실측)

| 파일 | 처리 | 실측 |
|---|---|---|
| `E/tests/lut/test_sweep_memo.py`(79줄) | 삭제(원본 삭제와 같이, 규칙 H) | 이름 hit(`grep -cw`): `sweep_memo` 7(`:1·8·25·36·44·59·75` -- 옛 초안 6은 오기, 1.3.5 '7'과 맞음)·`first_eval` 1·`from_sweep` 2. `:73-79` 성질(직접 생성자 상한 0 → `ValueError`)은 `test_lut_memo.py:40-43`(`test_bad_capacity_valueerror`, 0 포함)가 이미 덮는다 |
| `E/tests/search/test_sweep_memo_wiring.py`(134줄) | 삭제(원본 없는 test = 규칙 H 고아, design (4)). 검사는 `test_search_context.py`로 옮긴다 | 옮길 성질: 탐색 memo ≠ 호출자 memo(`:82-83`), 상한 = (n_θ+1)·U(`:99`), 값 비트 동일(`:103-119`), 호출자 상한 상수 무영향(`:122-134`) |
| `E/tests/lut/test_lut_memo.py:1`(docstring), `:46-53`(`test_from_sweep_capacity`) | 다시 씀(계수 상태 → 고정) | |
| `E/tests/search/test_find_front.py:19-24`(`PERF_KEYS`·`PERF_KEYS_C7`), `:59-64`(키 21개 정확히) | 고침: `lut_memo_bound` 추가 → 22개 | 1.5. NFR-4 test `test_lb_stop_notes_line_exactly_once`(`:341`, `set(perf) == set(PERF_KEYS_C7)`)는 상수를 따라온다 |
| `E/tests/core/test_bounded_lru.py`(기존 파일) | 신규 test 추가: `adopt`가 원 key를 받아 `lookup`과 같은 키로 적중, hits·misses 불변, 넘치면 퇴출·`evictions`·퇴출 기록(그 키 재계산 = `recomputes_after_eviction`) | design (5) A 행 |
| `E/tests/search/test_slsqp_outer.py:104`(주석 'x0 = exp(ln θ) 가 시작 θ 와 1 ulp 달라'), `:143-154`(`test_start_theta_reused_no_extra_kernel`) | 주석은 사실에 맞게, test는 유지(정본 사용 확인은 신규) | |
| `E/tests/search/test_gate_run.py`(88줄, `GR.fd_jacobian` 대체 선례 `:69`·`:85`) | 신규 test 추가 | |
| `E/tests/search/test_layer0_center.py`, `test_search_context.py` | 신규 test 추가 | |
| 새 `E/tests/search/test_theta_coords.py` | 신규(규칙 H 1:1) | 이름 충돌 0(1.7.2) |
| 탐색 값을 고정한 단언(층 0·외층·감도 게이트·`find_front`의 θ·평가 수·`seq`·memo 통계) | test 주체가 grep으로 목록을 만들고 새 값으로 다시 쓴다(design (6)). 기준 약화(허용 폭 넓히기) 금지 | 후보 파일(실측 grep, 확정 아님): `tests/search/test_layer0_center.py`, `test_kernel.py`, `test_find_front.py`, `test_slsqp_outer.py`, `test_eps_sweep.py`, `tests/convergence/test_converge_point.py`(`kernel_calls`·`sctx.counters` 단언 `:135·165·195·225·284`). NFR-4 신규 후보: `tests/integration/test_layer0_boundary_rows.py`(slow 아님, 8회로 `layer0_start` 시작점의 `w_min` 경계 행 -- 시작점이 `_maxmin` 결과라 RT 영향 가능), `tests/search/test_l_bin_search.py` `test_lb_stop_*`(커널 호출 수·예산 전제), `test_find_front.py` `test_lb_stop_notes_*`(front ≥ 1·stops ≥ 1 전제) |

#### 1.3.4 문서

| 위치 | 처리 |
|---|---|
| 함수 레지스트리(A13) | code 주체, 같은 변경 |
| 42 D-XR1·D-XR2 | 판정 뒤 OK(오케스트레이터) |
| `docs/03-analysis/gain-budget-gmid-sizing.u3-lut-pdk-record.md:129`(`sweep_memo` 언급) | **바꾸지 않는다** -- U3 시점 기록 문서이고 (4) 범위(엔진) 밖 |
| history·design 40·42의 `sweep_memo`·`_CountingMemo`·`from_sweep`·`first_eval` | 바꾸지 않는다('옛' 문장 제외 규칙) |

#### 1.3.5 삭제 이름 grep 0 (design §2.4.14 (4) A 행, 이름별 범위)

| 이름 | grep 범위(이 안에서 단어 단위 0) | 범위 밖 남는 쓰임(지우지 않는다) | 실측 hit ebd7b3c(엔진 `.py`(tests 제외) / CONTRACT `.md` / `tests/`) -- 수는 609965d와 같음 |
|---|---|---|---|
| `sweep_memo` | 엔진 전체(`gmid_engine/` 소스·CONTRACT·`tests/`) | 엔진 밖: `docs/03-analysis/…u3-lut-pdk-record.md:129`, history·design. 주의: `_wire_sweep_memo`·`test_…_sweep_memo_wiring` 같은 합성 이름은 `-w`에 걸리지 않는다(`_wire_sweep_memo`는 design이 유지) | 10 / 3 / 7 |
| `_CountingMemo` | 엔진 전체 | 없음 | 2 / 0 / 3(`test_sweep_memo_wiring.py` 안 test 쪽 같은 이름 클래스 -- 파일 삭제로 0) |
| `from_sweep` | 엔진 전체 | 함수 레지스트리 `:635`(A13에서 고침), history·design | 8 / 4 / 7 |
| `first_eval` | 엔진 전체 | design | 6 / 3 / 1 |
| `_coord` | `E/search/` | 없음(`dc_coord`는 `-w`에 걸리지 않음 -- 실측) | `layer0_center.py:371·429` 2 |
| `def to_theta`(정의) | `E/search/` 중 `theta_coords.py` 밖(design (4) 849행 정정 -- J-1 해소) | `ThetaCoords.to_theta` 메서드(`theta_coords.py`), `fd_jacobian`의 인자 이름 `to_theta`, `tests/search/conftest.py:459`의 `to_theta_fn`(범위 밖) | 3(`gate_run.py:57`, `layer0_center.py:301`, `slsqp_outer.py:112`) |
| `exact` | `E/search/slsqp_outer.py` | 없음 | 6(`:71·76·77·106·116·117`) |

검사 방법 메모(사실): `E/tests/structure/test_removed_names.py`의 AST 검사(`REMOVED_SCOPES`)는 `.py`만 본다. 범위에 CONTRACT·`tests/`가 들어가는 이름은 감사가 `git grep -nw`로 이름·범위마다 잰다(interface card A-1). `to_theta`는 메서드·인자 이름으로 남으므로 `REMOVED_SCOPES`에 넣을 수 없다.

#### 1.3.6 NFR-4 병합분 보존 계약 (ebd7b3c 실측 -- card A가 지우거나 바꾸면 안 되는 것)

| 파일:줄 | 내용 | card A와의 관계 |
|---|---|---|
| `E/search/slsqp_outer.py:31`, `:104` | `blas_environment` import, `solve_eps` 첫 줄 재확인 (e) | A2가 `_layout`·`to_theta`를 바꿀 때 유지 |
| `E/search/layer0_center.py:48`, `:657` | import, `layer0_start` 재확인 (d) | A3는 `_maxmin`만 -- 유지 |
| `E/search/search_context.py:27`, `:203-204` | import(`blas_environment`), `build_search_context` 재확인 (b) | A9는 `_wire_sweep_memo`만 -- 유지 |
| `E/search/find_front.py:22`, `:78`, `:117`, `:153` | import, 재확인 (c), notes `l_search` 한 줄, runs 줄 `env_fp` | A11 perf 추가와 다른 줄 -- 유지 |
| `E/search/layer0_center.py:239`·`:392` | `scipy_minimize` 모듈 전역 호출(이름·키워드 호출·반환 `x` 읽기 -- `tests/search/test_layer0_center.py:588·600`이 바꿔 끼움, design (3) 819·833·837행) | `_maxmin`의 `:392` 호출 방식 유지 |
| `E/search/find_front.py` `layer0_start`·`sweep_front` 모듈 전역 호출 | `tests/integration/nfr4_run_dump.py:317-329`이 감쌈 | 호출 방식 유지 |
| `E/search/layer0_center.py:243-258` | BP1 `lift_exponent`(`_current_centre`) | 범위 밖. n_θ(변수 수)는 무관 |
| `_budget_stop` 3곳: `slsqp_outer.py:95-100`, `layer0_center.py:280-285`, `l_bin_search.py:35-40` | 예산 정지 사유 | **무변경**(합치기는 card C). `layer0_center.py:280-285`는 `_maxmin`(288) 바로 위, `slsqp_outer.py:95-100`은 `_layout`과 `to_theta` 사이라 diff 문맥만 붙는다 |
| `E/search/l_bin_search.py:79`, `E/search/eps_sweep.py` `lb_stops` | L-b 정지 사유 | 범위 밖 |
| `E/search/CONTRACT.md:432·481·513-514` | NFR-4 (b)(e)(c)·`env_fp`·notes `l_search` 문장 | §3.9·§3.13·§3.16을 고칠 때 지우지 않는다 |
| `E/_module_map.py:45`, `:197-199`, 레지스트리 `:62-63` | `blas_env.py` 층·항목, NFR-4 정본 행 2개 | A12·A13 편집 위치와 별개 |
| `tests/core/test_blas_env.py:252-272`(`test_blas_pin_recheck_points_reject_changed_threads`, 점 a~e) | 재확인 다섯 지점을 본다 | card A 뒤에도 통과해야 한다 |

### 1.4 배선 변경 (design 그대로)

#### 1.4.1 `ThetaCoords`

```text
ThetaCoords.start(variables, theta) -> ThetaCoords        # clip 인자 없음(X-14)
  변수마다 x0ᵢ = ln θᵢ(log 변수) | θᵢ(그 밖), 자르지 않음. rawᵢ = θᵢ. 변수 밖 성분 = theta 값 그대로 고정.
coords.to_theta(x) -> dict
  변수마다 v = float(xᵢ): v == x0ᵢ(float 정확 일치) -> rawᵢ, 아니면 log 변수 exp(v), 아니면 v. 고정 성분 그대로.
```

#### 1.4.2 세 경로 (변경 뒤)

| 경로 | variables | 시작 θ | 풀이 시작 좌표 | 풀이기 x → θ | FD에 넘기는 변환 |
|---|---|---|---|---|---|
| 외층 `solve_eps` | `_layout` 결과(정준 순서, `ln_idu_floors` 하한 조정 뒤) | `start.theta` + L 단일 칸 고정값 | clip(x0ᵢ; loᵢ, hiᵢ) | clip(xᵢ) 뒤 `to_theta` | clip 뒤 `to_theta`(함수 이름은 `to_theta`로 `def` 하지 않는다 -- 1.3.5) |
| 층 0 `_maxmin` | 입력 `variables`의 하한 조정 뒤(`:272-274`) | `theta0` | clip(x0ᵢ) | clip(xᵢ) 뒤 `to_theta` | 같음 |
| 감도 게이트 | `sctx.domain.variables`(조정 없음) | `dict(base.theta)` | x0 그대로(자르지 않음) | -- | `coords.to_theta` 그대로 |

- 외층 as-built '잘리지 않았으면 원값'(`slsqp_outer.py:70-75`)은 '자른 좌표 == x0(자르지 않은 시작 좌표)일 때만 원값'으로 같은 결과가 된다(design (2) '상자 자르기' 행).
- `fd_jacobian`(`E/search/fd_jacobian.py:86-111`)은 받은 변환을 그대로 부른다(서명 불변). 움직이는 좌표는 `:99-101`이 상자 안으로 맞춘다.
- 새 점을 만드는 곳(`_box_centre`, Halton 시험점, 수리 bisection)은 대상이 아니다(design (2) '쓰는 곳').

#### 1.4.3 `build_search_context` (변경 뒤)

```text
_s0_blocks -> context_fp -> archive -> SearchContext(...) -> _wire_sweep_memo(ctx):
    n_θ = len(centre_start(ctx)[0])                  # 호출자 memo로 조회
    ctx.dc = replace(ctx.dc, lut=LutAccess(LutMemo.counting(lut, n_θ, table_cache=...), w_keys))
# 커널 평가 0, 임시 컨텍스트 없음
```

#### 1.4.4 `evaluate` (변경 뒤 순서)

요청 계수 → 키 → 메모리 캐시 적중이면 그대로 → 원뿔 밖이면 `STATUS_OUTSIDE_DOMAIN` → (그 컨텍스트의 첫 커널 평가면 `memo.open_count()`) → `size_and_seal`·봉인 상태·ss·목적·제약 → `EvalResult` → (첫 커널 평가면 `memo.fix_bound()`) → 캐시·S3.

#### 1.4.5 배선 확인(만들면 반드시 배선)

`ThetaCoords`는 세 풀이가, `LutMemo.counting`은 `_wire_sweep_memo`가, `open_count`·`fix_bound`는 `evaluate`가(`bound_state`로 판별), `BoundedLRU.adopt`는 `fix_bound`의 옮기기가, `bound_state`는 `evaluate`와 `find_front`(`perf.lut_memo_bound`)가 쓴다. 쓰이지 않는 새 이름을 남기지 않는다.

### 1.5 결과 JSON·공개 API 형식 변경

| 출력 | 바뀌는 것 | 원천 |
|---|---|---|
| `find_front` `SearchFront.perf`, `runs.jsonl` 줄 `perf` | 키 `lut_memo_bound` 추가(값 `"fixed"` 또는 `"unfixed_no_kernel_eval"`) -- 키 수 21 → 22 | design §2.4.6 '첫 커널 평가가 없는 실행' 행, §2.4.14 (5) 판정 측정 열 'card A = `perf.lut_memo_bound`(새 칸)' |
| `perf.lut_memo_evictions` | 키 불변. 값은 상한(U_eval을 재는 점이 as-built 상자 중심 임시 평가 → 실행의 첫 커널 평가로 바뀜)과 퇴출 시점에 따라 달라질 수 있다 | 값 변화 목록 대상 |
| 공개 API | `gmid_engine.lut.sweep_memo` 삭제, `LutMemo.from_sweep` 삭제, `LutMemo.counting`·`open_count`·`fix_bound`·`bound_state` 추가, `BoundedLRU.adopt` 추가, `gmid_engine.search.theta_coords.ThetaCoords` 추가(search `__init__` 재수출 -- J-2 판단) | |
| `run_id`·S3 줄 `code_fp` | 엔진 코드가 바뀌므로 값이 바뀐다(형식 불변) | `find_front.py:142`(`run_id = fp_of((context_fp, code_fp, ...))`) |

### 1.6 완료 조건 (design §2.4.14 (5) A 행 그대로 + 공통)

1. (i) 1.3.5 표 이름마다 그 범위 안 단어 단위 grep = 0(`def to_theta`는 `theta_coords.py` 밖 범위).
2. (ii) `build_search_context` 안 커널 평가 = 0(임시 컨텍스트·버리는 평가 없음). 첫 커널 평가 창의 **독립 계수**로 잰 U_eval,r에 대해 고정 용량 = (n_θ + 1)·U_eval,r(영역 point·curve·root). 독립 계수 = test가 `LutMemo.lookup`·`evaluate`를 감싸 따로 센 값, n_θ = test가 `centre_start`로 따로 잰 값(design §2.4.6 '독립 계수' 행).
3. (iii) `ThetaCoords`: 시작 좌표면 `to_theta` 결과가 시작 θ와 성분마다 비트 동일 -- 외층 `solve_eps`·층 0 `_maxmin`·감도 게이트 세 경로 모두 단위 test로. **층 0·감도 게이트 경로 test는 base(`6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`)에서 실패해야 한다**(비트 단언으로, import 오류가 아니라). 외층은 base 실패를 요구하지 않고 정본 사용(사본 삭제)과 같은 성질만 확인.
4. (iv) design (6) 기준선 재측정과 값 변화 목록(회로·칸·옛 값·새 값) -- 사용자 승인 X-4 범위, 변화는 판정 기록에 보고. `u17_1b_s0_baseline.json`(S0 수준 칸 지문)은 같아야 하고 다르면 결함 보고. **9회로 블록 재계산 계수는 card A의 기준이 아니다** -- 총계·블록별 값을 보고만 한다(card B 비교 자료).
5. 탐색 값을 고정한 test 단언은 새 값으로 다시 썼고 허용 폭을 넓히지 않았다(design (6) 셋째 항목).
6. 전체 suite 한 번(`--run-slow`, 명령 하나 -- 기본 실행은 conftest가 slow를 뺀다) 통과, `tests/structure` 위반 0(규칙 H 포함 -- `-m structure_test_mapping` 결과를 새 base와 비교. NFR-4가 test 파일을 새로 넣었으므로 옛 base와 비교하지 않는다). 1.3.6 보존 계약 유지(재확인 다섯 지점 test 통과).
7. 공통 완료 조건(design §10.4): graph 단일 정본 확인 (a)~(d)·계산값 재사용 확인 (a)~(d) 숫자와 함께 보고. 이 card는 graph 밖 저장소를 늘리지 않는다(계수 상태 memo는 기존 허용 저장소 (a) LUT memo의 상태다).
8. design ↔ 구현 gap 분석(bkit gap-detector, 일치율 90% 이상), 42 D-XR1·D-XR2 OK.
9. 함수 레지스트리 A13이 같은 변경에 있다.

### 1.7 위험

#### 1.7.1 동작·기준선

- RT로 층 0 FD 시험점의 고정 성분 비트가 바뀐다(as-built는 시작점 FD에서 모든 ln 성분이 exp(ln θ)). 실측: 무작위 θ ∈ [1e-9, 1e3](로그 균등) 10,000개 중 74.8 %가 `exp(log(θ)) != θ`, 최대 16 ulp(design (1) 'RT 1~3 ulp'는 H4 회로 값 기준 -- 범위가 넓으면 더 커질 수 있다). 그래서 층 0 결과·front·평가 수가 바뀔 수 있다(X-4 범위).
- W로 U_eval을 재는 점이 바뀐다: as-built는 `centre_start(ctx)`(rung 인자 없음) 점을 임시 컨텍스트에서 평가했다(`search_context.py:138·147`). 새 규칙은 실행의 첫 커널 평가(층 0 사다리 칸 0이 원뿔 안이면 그 점, `layer0_center.py:664-671`). 두 점이 같은지는 **측정하지 않았다**. 다르면 상한·퇴출 수가 바뀐다(값은 memo 순수성으로 불변).
- as-built는 첫 점이 원뿔 밖이면 세 영역 U = 0(`lut/CONTRACT.md:312`)이었다. 새 규칙은 처음으로 커널을 부르는 평가에서 재므로 그런 회로에서 상한이 0 → 양수로 바뀔 수 있다.
- 탐색 값 고정 test가 여러 파일에서 깨질 수 있다(1.3.3 마지막 행).
- base 궤적은 NFR-4 BP1(층 0 끌어올림)로 이미 바뀌었다 -- 기준선 옛 값은 새 base에서 같은 하네스로 잰다(J-7). card 1 P1 시간(224.6 s)은 대조 기준이 아니다.

#### 1.7.2 이름 충돌 (실측 grep, 엔진·tests·tools·workspaces)

- `ThetaCoords`·`theta_coords`·`open_count`·`fix_bound`·`lut_memo_bound`·`unfixed_no_kernel_eval`·`bound_state`·`window_open`·`test_theta_coords`·`test_counting_memo`: 0건(ebd7b3c, 저장소 전체 docs 제외). `counting`: `tests/pipeline/test_stage_a.py:517`의 지역 함수 이름 하나(`LutMemo` 속성과 무관).
- `adopt`: 이미 `core/canon_pointer.py:28` `CanonPointer.adopt`와 test 이름 7개 이상(`test_canon_pointer.py`·`test_rows.py` 등)에 있다. 다른 클래스라 기능 충돌은 없지만 새 test 이름에 `adopt`를 쓰면 `-k adopt` 선택에 섞인다(지금 쓰이는 `-k` 식에는 없음). 새 test 이름은 `test_bounded_lru_adopt_…`처럼 클래스 이름을 붙인다.
- `tests/search/`에 `theta`가 든 파일 이름 0, `E/search/`에도 0.
- 쓰이는 `-k` 식(design §10.4 표·`tests/structure/README.md`): `"test_ic"`(전체), `"g10"`·`"ic11 or kvl_branch_residual"`(integration), `"rule_g or design_value_location"`·`rule_k_`(structure), `"duplicate_args or loop_invariant"`(perf), `"ic1 or ic2 or ic9 or ic10 or shared_gate_net or kcl_residual"`(sizing), `"mna_assembly_count or mna_solve_count"`(metrics). 새 test 이름은 `test_ic`로 시작하지 않고 `g10`·`rule_g`·`rule_k_`·`ic1`·`ic2`·`ic9`를 담지 않는다(interface card 3절 이름 규칙).

#### 1.7.3 순서·충돌

- NFR-4 card 2는 먼저 병합됐다(X-19). 위험은 병합 충돌이 아니라 같은 파일 안 줄 이동과 보존 계약(1.3.6)이다.
- card B는 `kernel.py`를 다시 고친다(A10 창 호출 위치를 지킬 것). card C는 `_budget_stop` 3곳을 합친다(card A 뒤, 줄을 다시 잴 것).

### 1.8 오케스트레이터 판단 (상태 2026-10-16: J-1·J-4·J-5는 design cfe2e31로 해소, J-2·J-3·J-6·J-7은 끝 절 '오케스트레이터 판단'대로)

| id | 질문 | 실측 근거 | 선택지(정하지 않음, 기본안 후보 표시만) |
|---|---|---|---|
| J-1 (**해소**: design (4) 849행이 '`E/search/` 중 `theta_coords.py` 밖'으로 정정) | design (4) `def to_theta` 범위 `E/search/` 0과 (2) `ThetaCoords.to_theta(x)` 메서드(위치 `E/search/theta_coords.py`)가 서로 맞지 않는다 | design 794·796·829행. 메서드 정의는 `def to_theta`로 grep된다 | (가) 범위를 '`E/search/` 중 `theta_coords.py` 밖'으로 문구 정정(design 정정 = 사실 정정, 기본안 후보) (나) 메서드 이름 변경(design (2) 변경) |
| J-2 | `ThetaCoords`의 공개 칸(시작 좌표 x0 등)과 search `__init__` 재수출 여부 | design은 `start`·`to_theta`만 정했다. 호출부가 'clip(x0ᵢ)'을 하려면 x0을 읽어야 한다. test 작성자가 공개 계약만으로 쓰려면 칸 이름이 필요하다 | (가) 칸 `variables`·`x0`·`raw`·`fixed`(tuple) 공개, 재수출 안 함(모듈 경로 `gmid_engine.search.theta_coords`) (나) 칸은 code 몫, test는 `start`·`to_theta`만 쓴다 |
| J-3 | test 관찰 지점(교체 지점)을 공개 계약으로 고정할지 | 층 0·게이트 경로의 '시작 좌표 `to_theta` 비트 동일'과 '컨텍스트 생성 안 커널 0'을 소스 없이 보려면 모듈 속성이 필요하다. 선례: `tests/search/test_gate_run.py:69·85`가 `gate_run.fd_jacobian`을 이미 바꿔 끼운다, card 1 J-5(`layer0_center.evaluate`). 실측(ebd7b3c): `layer0_center.py:55`·`slsqp_outer.py:37`·`gate_run.py:18`이 `fd_jacobian`을, `kernel.py:26`이 `size_and_seal`을 모듈 이름으로 부른다. `gmid_engine.search.fd_jacobian`은 같은 이름 함수로 가려진다(`search/__init__.py:23`) | (가) 세 모듈의 `fd_jacobian` 속성과 `kernel.size_and_seal` 속성을 이름·서명·호출 방식 불변 계약으로(card B도 지킴) (나) 다른 관찰 방법(test 작성자 선택) |
| J-4 (**해소**: design §2.4.6 cfe2e31 -- (a) 계수 상태 `stats()` capacity=None·size=모은 수·evictions 0, 고정 뒤 = `BoundedLRU` 계수 + 계수 상태 hits·misses (b) `BoundedLRU.adopt(key, value)`로 옮김(원 key, 계수 불변, `core/bounded_lru.py` 범위 편입) (c) `canonical_key` 동치 (d) 창 안 예외 조회는 U 제외(`misses`에는 셈) (e) `"counting"`→`"window_open"`→`"fixed"` 한 방향, 그 밖 호출과 `"fixed"` 상태(생성자 memo 포함)의 두 메서드는 모두 `ValueError` (f) 읽기 전용 `bound_state`, 생성자 memo 탐색의 `lut_memo_bound` = `"fixed"` (g) `table_cache=None`. 아래 옛 질문 칸은 이력으로만 남긴다) | `LutMemo` 계수 상태의 세부 규칙 | design §2.4.6 표가 정하지 않은 것(옛 상태) | (a) 계수 상태의 `stats()` 값(특히 `capacity`) (b) 고정 때 항목 옮기기: `BoundedLRU` 공개 `lookup`으로 넣으면 `misses`가 옮긴 수만큼 늘고 퇴출 키가 `_evicted`에 들어간다(→ `recomputes_after_eviction` 계수). 직접 넣으려면 `E/core/bounded_lru.py` 변경이 필요한데 design (3) 재작성 범위표에 그 파일이 없다 (c) '서로 다른 키'의 동치: as-built `_CountingMemo`(`sweep_memo.py:22-24`)는 Python `==`(0.0 = −0.0, 1 = 1.0, NaN ≠ NaN), `BoundedLRU`는 `canonical_key`(`bounded_lru.py:7-9`, 0.0 ≠ −0.0, NaN 적중). design은 '`_CountingMemo` 의미 보존'과 '`BoundedLRU`와 같은 최근성 규칙'을 함께 적었다 (d) 창 안에서 `compute()`가 예외를 낸 조회를 U에 넣나: as-built는 저장된 키만 셌다(넣지 않음) (e) `open_count`·`fix_bound`: `LutMemo(...)` 생성자 memo = 무동작, `counting` memo의 두 번째 호출 = `ValueError`로 읽는 것이 맞는지(design 문장 '계수 상태가 아닌 memo에서는 아무것도 하지 않는다'와 '두 번째 … `ValueError`'), `open_count` 없이 `fix_bound`, 고정 뒤 `open_count` (f) `find_front`가 고정 여부를 읽는 방법(상태 조회 이름)과 `counting`이 아닌 memo로 돈 탐색의 `perf.lut_memo_bound` 값 (g) `LutMemo.counting`의 `table_cache` 기본값 유무(design 서명 `*, table_cache`는 기본값 없음, as-built `from_sweep`은 `=None`) | 기본안 후보: (b) 공개 `lookup` 사용 + test는 옮긴 뒤 `misses`·`hits` 절대값을 단언하지 않음 (c) `BoundedLRU`와 같은 `canonical_key`(독립 계수도 같은 동치로 센다) (d) as-built대로 넣지 않음 (e) 그대로 (f) 상태 조회는 읽기 전용 속성, 생성자 memo의 탐색은 `"fixed"` (g) 필수 키워드 -- **모두 결정 필요** |
| J-5 (**해소**: `bound_state`·계수 상태 `stats()`가 공개 조회) | 계수 상태 test에 필요한 '고정 전 상태' 관찰 | design test 초안 '계수 상태 memo'를 단언하려면 J-4 (a)·(f)의 공개 조회가 필요 | J-4와 함께 |
| J-6 | 9회로 RT 관찰(보고만 vs 판정) | design (iii)은 단위 test로만 판정한다. interface card A-4는 9회로에서 `fd_jacobian` 호출마다 '받은 변환(x) == 기준점 θ(변수 성분)'를 세어 **보고만** 하도록 적었다 | (가) 보고만(기본안 후보, design 그대로) (나) 판정에 넣음(design 변경) |
| J-7 (끝 절 판단: base·head 같은 하네스로 둘 다 잼 -- NFR-4 BP1로 base 궤적이 바뀌어 card 1 값은 더욱 못 쓴다. NFR-4 in-tree 하네스 `tests/integration/nfr4_run_dump.py`·`nfr4_compare.py` 재사용 후보) | 기준선 '옛 값' 출처 | design (6) 'card 1 xrun 판정(029f9b7)이 쓴 값'. 실측: 값은 `wt/_scratch_xrun_audit/m/json/<회로>_p1.json`(perf·digest)과 `wt/_scratch_xrun_audit/s3/<i>a/<context_fp>/{evals,runs}.jsonl`(P1 줄 뒤에 R2 같은 줄)에 있다. 측정 대상은 8f1afc5(= 609965d와 docstring 5파일만 다름, J-8 AST 같음). P1 JSON의 front·pending·unmeasured는 값이 아니라 digest·목록 | (가) 이 파일을 옛 값으로 쓰고 부족한 칸만 base 609965d 같은 계측 1회로 보충 (나) base 9회로 전부 새로 잼 |

### 1.9 원래 취지와 다른 판단 (사용자 규칙 2026-10-15)

취지: "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용".

| # | 내용 | 상태 |
|---|---|---|
| D-1 | 이 card는 취지 쪽으로 움직인다(버리는 첫 평가 제거, 같은 점 같은 비트 → 평가 캐시 적중). 새 이탈 없음 | -- |
| D-2 | (기존 동작, 범위 밖) U_eval = 0 영역은 `_Unmemoized`로 매번 계산하고, 고정 때 그 영역에서 창 밖에 모은 항목은 옮길 곳이 없어 버려진다 | 실행 안 같은 키 재계산이 남는다. design이 '③에서 `_Unmemoized` 제거'로 정했다(§2.4.6 426·441행). 이 card는 바꾸지 않는다 |
| D-3 | (기존 동작, 범위 밖) S0 준비 조회는 호출자 memo, 탐색은 계수 상태 memo -- 두 인스턴스라 같은 LUT 키를 두 번 계산할 수 있다 | design '인스턴스 하나는 단계 ③ 그대로'(412행) |
| D-4 | (기존 동작 유지) n_θ를 재려고 `_wire_sweep_memo`가 `centre_start(ctx)`를 부르고 층 0이 같은 함수를 다시 부른다(상자 중심·전류 중심 계산 두 번, 계산 블록 아님) | design §2.4.6 'n_θ' 행이 as-built 값·방법을 그대로 정했다. 실행 안 중복 계산이지만 design 결정 |
| D-5 | 감도 게이트는 자르지 않는다 | 사용자 결정 X-14. 새 판단 아님 |

---

## 2. 공통 브리핑 (이 card의 code·test·audit agent 필독, 1쪽)

> `U17_STEP1_COMMON_BRIEF.md`를 이 card에 맞춘 판이다. 옛 브리핑의 'S0 스냅샷 영속화' 허용 문장은 폐지됐다.

base = `6be811b(NFR-4 card 2 병합 master, gmid_engine/ = ebd7b3c, 차이는 assets/technique 원문뿐)`(NFR-4 card 2 병합 뒤 master). design: `docs/02-design/features/gain-budget-gmid-sizing.40-engine.design.md` §2.4.6('첫 평가 버림 제거', cfe2e31 J-4 보완 포함)·§2.4.14 (1)~(7)·§10.4·§11 XRUN-F1 행, `…42-gap-checklist.design.md` D-XR1·D-XR2. 계획: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` NFR-2·U-91·U-94. 엔진: `skills/analog-gmid-design/gmid_engine/`. 사용자 결정 기록: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/user_decisions.md`(읽기만, X-1~X-19, N-1~N-6). card: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/engine/XRUNF1A_SPEC_CARD.md`(code·audit), `XRUNF1A_INTERFACE_CARD.md`(test는 이것만 -- 소스 열람 금지).

### 절대 규칙
1. **design 그대로 구현한다. as-built 결정 금지.** design에 없는 것을 정해야 하거나 design이 모순·불가능하면 그 자리에서 **멈추고 보고**한다(무엇이, 어느 절이, 선택지). 범위 축소·대체 금지. spec card 1.8과 끝 절 '오케스트레이터 판단'이 정한 것 밖은 손대지 않는다.
2. **graph 단일 정본(DEC-83, 40 §2.4)**: 설계 값은 graph 필드에만. graph 밖 허용 저장소는 **셋뿐** -- (a) LUT memo(순수 함수, 디스크 LUT 파생표 캐시 포함, U-87), (b) S3 기록(출력)과 그 실행 안 메모리 캐시, (c) 실행 계수. 새 dict 캐시·객체 칸·사본·디스크 캐시 금지. `ThetaCoords`는 풀이 하나 동안의 좌표 변환 값이고 설계 값 저장소가 아니다.
3. **계산값 재사용 = 실행 안에서**: 사용자 취지 "처음 topology를 실행할 때는 항상 계산하고 그 계산된 값이 나머지 최적화를 진행할 때 재사용". 같은 입력은 다시 계산하지 않는다. 취지에서 벗어나는 판단이 필요하면 멈추고 '원래 취지와 다름'으로 보고한다.
4. **틀린 구조는 전체 재작성**(재작성 범위 = design §2.4.14 (3) A 행). 대체한 옛 코드·CONTRACT 문장은 **같은 변경에서 삭제**(만들면 반드시 배선 -- `ThetaCoords`는 세 경로, 계수 상태 memo는 `build_search_context`·`evaluate`가 실제로 쓴다).
5. **건드리지 않는 것**: card B·C 범위(블록 결과 색인·`RunCounters`·`ComputeBlock` 계수·부분 스냅샷·FD 묶음 예산·`_budget_stop` 3곳 합치기), U17 ③ 범위(`memo.call`·인스턴스 하나·`_Unmemoized` 제거·B_r 나머지 항), LUT 파생표 디스크 캐시, `ComputeBlock.code_hash`, 감도 게이트 clip(X-14: 자르지 않음), `fd_jacobian` 서명, **NFR-4 병합분(spec card 1.3.6 보존 계약 전부)**: 재확인 (b)(c)(d)(e) 호출 줄, `find_front`의 `env_fp`·notes `l_search`, `layer0_center.scipy_minimize`·`find_front`의 `layer0_start`·`sweep_front` 모듈 전역 호출, BP1 `lift_exponent`, search CONTRACT의 NFR-4 문장(432·481·513-514).
6. **상수 발명 금지**(WP-03), **회로 이름·소자 이름 코드 금지**.
7. **파일 분할 규칙**: 파일 하나 = 한 개념, (A) 독립 진입점 1개, (B) `_` helper는 그 파일만, (C) 패키지 층 순서 core<lut<authoring<graph<sizing<metrics<search<layout<convergence<report<pipeline, (H) test `tests/<pkg>/test_<file>.py` 1:1 -- 새 `search/theta_coords.py` ↔ `tests/search/test_theta_coords.py`, 지운 `lut/sweep_memo.py` ↔ `tests/lut/test_sweep_memo.py` 삭제, 고아 `tests/search/test_sweep_memo_wiring.py` 삭제. `core/bounded_lru.py` 수정 ↔ 기존 `tests/core/test_bounded_lru.py`에 `adopt` test. `_module_map.py`에 새 파일 등록·지운 파일 삭제(기계 검사 없음 -- 리뷰 항목). 끝나기 전 `tests/structure` 통과(위반 0).
8. **작성자 ≠ 검증자**: code agent는 test·기대값을 쓰지 않는다(옛 test가 깨지면 고치지 말고 목록으로 보고). test agent는 피검 코드를 불러 기대값을 만들지 않는다(oracle = design 식·손계산·같은 함수 두 출력 비교·독립 계수). 같은 커밋에서 코드와 기준을 함께 바꾸지 않는다. 기준 약화(허용 폭 넓히기)는 사용자 승인 사항.

### 실행 환경·git 가드
- python: `/c/Python314/python.exe`(bash에서 `timeout` 래퍼 금지). 실행 위치 `<worktree>/skills/analog-gmid-design`, `python -m pytest -q gmid_engine/tests/<경로> -p no:cacheprovider`. BLAS 스레드는 엔진이 import 때 `pin_blas_threads()`로 1로 고정·확인한다(conftest는 고정하지 않는다). conftest의 `slow` 마커: 기본 실행은 slow test를 빼고, 포함하려면 `--run-slow`(`-m`을 주면 규칙 H 마커 기본 제외가 꺼진다 -- conftest 주석).
- **무거운 실행은 한 번에 하나**(9회로·전체 suite는 순차, 메모리). 전체 suite는 끝에 한 번만. 긴 실행은 결과를 파일에 쓴다(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1a_<role>/run.txt`, 케이스마다 append).
- git: 항상 `git -C <자기 worktree>`, 스크립트는 `set -e`. 다른 worktree·master를 건드리지 않는다. reset --hard·다른 브랜치 checkout·push·merge 금지. 커밋은 자기 브랜치에만.
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` 와 `Claude-Session: https://claude.ai/code/session_012FxFP7YSWEBBCB9rmBQjLL`(`--trailer`로).
- 임시 파일은 `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_xrunf1a_<role>/`(자기 것만).

### 최종 보고(한국어) 필수 항목
1. 구현·작성한 design 절과 상태(구현됨/부분/못함 + 사유).
2. 멈춤·보고 항목(as-built 결정이 필요했던 곳, '원래 취지와 다름' 후보).
3. 지운 옛 코드(파일:줄), 바뀐 배선(호출부 파일:줄), 1.3.5 이름별 grep 결과.
4. graph 단일 정본 자기 점검: graph 밖 저장소가 허용 셋뿐인지, 40 §2.4.8 소유표 대조.
5. 계산값 재사용 자기 점검: `build_search_context` 안 커널 평가 0, 시작 좌표 `to_theta` 비트 동일(세 경로).
6. `tests/structure` 결과(규칙별 대상·위반 수, H는 base와 비교), 관련 test 결과, 깨진 옛 test 목록.
7. 커밋 해시.


## 오케스트레이터 판단 (2026-10-15, 원칙 기본안 -- 사용자 결정 아님)
- J-1: `def to_theta` grep 0 범위를 'E/search/ 중 theta_coords.py 제외'로 design 정정(design 작성자에게 넘김). 메서드 이름은 design대로 to_theta 유지.
- J-2: ThetaCoords 공개면 = `start(variables, theta)`(생성), `to_theta(x)`, 읽기 전용 `x0`(tuple). search/__init__ 재수출(다른 search 공개 이름과 같은 관례).
- J-3: test 관찰 지점을 공개 계약으로 고정: 세 모듈(gate_run·layer0_center·slsqp_outer)의 모듈 속성 `fd_jacobian`, `kernel.size_and_seal` -- 이름·서명·모듈 속성 호출 방식 불변(card 1 J-5 `layer0_center.evaluate` 선례).
- J-4·J-5: 계수 상태 memo 세부 7가지는 design 공백 -> design 40 §2.4.6 보완(design 작성자) 후 검증, card는 그 결과를 따른다. 그 전 code·test 착수 금지. **[2026-10-16 해소: design cfe2e31 보완이 병합됨 -- 1.8 J-4 칸·interface C3가 그 결과를 따른다]**
- J-6: 9회로 좌표 원값 관찰은 보고만(card A 판정은 단위 test 기준, design B-3 결정과 일관).
- J-7: 기준선 옛 값은 card 1 측정 파일을 쓰지 않고, auditor가 같은 환경·같은 하네스로 base(card A 직전 master)와 head를 둘 다 잰다(front가 digest로만 남은 문제, 같은 환경 비교 원칙).
- 측정 복제본 _scratch_xrunf1a_card/wt worktree 제거(깨끗함 확인 후).
- (2026-10-16, nfr4c2 J-O2 교훈) red 예상 목록에는 엔진 동작을 보는 test만 넣는다 -- test 도구(마커 conftest·비교기·하네스) 자체를 시험하는 test는 base에서 green이 정상이라 빼고, 감사는 그런 test를 red 판정 대상으로 세지 않는다.

## 오케스트레이터 design 정정 대기 (초안은 고치지 않음 -- design 작성자 몫, card 착수 전 처리)
- design 40 §10.4 표 '전체(slow 제외)'(1918행) `-m "not slow"`와 1980행 '전체 suite(`not slow`)': NFR-4 뒤 conftest는 기본 실행이 slow를 빼고 `--run-slow`로 포함한다(`-m`을 주면 규칙 H 마커 기본 제외가 꺼진다는 conftest 주석과 어긋남). 명령 문구를 conftest에 맞게 정정.
- design 40 §2.4.14 (4) card C 행(856행) '`_budget_stop` 지금 정의 `layer0_center.py:262`·`slsqp_outer.py:94`': 정의는 3곳(`slsqp_outer.py:95`, `layer0_center.py:280`, `l_bin_search.py:35` -- NFR-4가 셋째를 만듦), 줄도 다름. card C 착수 전 정정(card A 범위 밖).


## 오케스트레이터 판단 (2026-10-16, 감사 순서 3 a591a4e 뒤)
- J-O1: gate 범위 밖 red 23건(AttributeError 17·ImportError 4·KeyError 2)은 nfr4c2 J-O1·J-7 선례대로 red로 인정 -- 새 계약(adopt·counting·bound_state·ThetaCoords·lut_memo_bound) 부재가 원인이고 card 이유와 같다. 다음 card의 interface card에는 '## 신규 시그니처' 절을 넣어 merge_gate가 세게 한다.
- J-O2: A-T10 base red(−0.0/0.0 canonical_key 두 키, 상한 60 대 65)는 J-4 (c) 키 동치 변경의 정당한 결과로 추가 red 인정.
- J-O3: search CONTRACT §3.16 'perf 키는 바뀌지 않는다' -> 범위 한정 문구로 code 쪽에서 수정, 레지스트리 636행 이력 문구 삭제(A13) -- code 작성자 후속 커밋.
- J-O4: bounded_lru lookup 본문 _store 분리는 동작 동일 리팩터링으로 수용(A-8 글자 기준 경미 이탈, 기록만).
- 운영: 감사 순서 6이 메모리 압박 정리로 끊김(agent 턴 종료 뒤 백그라운드 실행 정리). 재실행은 agent가 턴을 끝내지 않고 완료까지 기다리게 브리핑.

- J-O5 (2026-10-16, gap 분석 98% 뒤): as-built 경미 이탈 기록 -- ThetaCoords 공개 필드 variables·raw·fixed(J-2는 x0만 계약, J-2는 오케스트레이터 기본안), theta_of 로컬 이름, _layout 반환형 축소, _Unmemoized hits·misses 이어받기, adopt의 _evicted.discard, to_theta 결과 키 순서. 동작·계약 무영향(evaluate는 정렬 키). 오케스트레이터 기본안 범위로 수용하고 사용자 보고. 병합 뒤 42 D-XR1·D-XR2 OK, design 40 §11 1619행 DEV 문구 갱신. 개선 후보(design 변경 필요): _wire_sweep_memo가 n_θ 하나를 위해 centre_start 전체 호출(층 0이 다시 호출) -- 다음 card 검토.
