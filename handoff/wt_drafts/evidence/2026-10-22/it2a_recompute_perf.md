# IT-2a 소급 측정 -- 블록 안 재계산 효율 (base d3bdbd39 대 head 56080584)

측정일 2026-10-22. 읽기 전용으로 진행했다. 메인 저장소에서는 `git -C … archive`만 썼고 저장소 파일은 고치지 않았다.

## 0. 조건

| 항목 | 값 |
|---|---|
| base | `d3bdbd39` (IT-2a 직전 integ) -> `wt/_scratch_it2a_perf/base` |
| head | `56080584` (IT-2a 병합본) -> `wt/_scratch_it2a_perf/head` |
| 회로 | `folded_cascode`, `two_stage_ota` (parent 재평가 비율: 65/66, 52/53) |
| 탐색 | `find_front(sctx, [])`, `SearchSettings(7200.0, 40, (1e2,1e5), …, (1e-13,1e-10))` (예산 40, yends_analyst.py와 같은 준비 순서) |
| 하네스 | `wt/_drafts/evidence/2026-10-22/it2a_perf/perf.py` (관찰 래퍼만 씀. 원 함수를 그대로 불러 같은 객체를 돌려준다) |
| 실행 | `run_all.sh`로 순차 실행, Python 3.14.2 `-I`, APPDATA export |
| 원자료 | `it2a_perf/perf.jsonl` (profile 1회 + plain 3회), `it2a_perf/rev/perf.jsonl` (순서를 뒤집은 plain), `prof_{base,head}_{circuit}.{txt,pstats}` |
| 모드 | profile = cProfile과 관찰 부가 계산(스냅샷 크기, 복제 시간) 포함. plain = 시간 기록만 |

두 결과 모두 `front_ok = True`였다. 탐색 경로는 base와 head가 같았다. 요청 수, 커널 호출 수, 캐시 적중, LUT 조회 수가 모두 일치했다.

## 1. 결과표

### 1.1 결정적 계수 (base와 head를 정확히 비교할 수 있는 값)

| 항목 | folded base | folded head | two_stage base | two_stage head |
|---|---|---|---|---|
| 요청 / 커널 호출 / 캐시 적중 | 155 / 66 / 89 | 155 / 66 / 89 | 103 / 53 / 50 | 103 / 53 / 50 |
| parent 있는 커널 호출 (서로 다른 parent 수) | 65 (2) | 65 (2) | 52 (3) | 52 (3) |
| `recompute_same_key` (sctx) | 0 | 0 | 0 | 0 |
| 블록 `recompute_same_input` 합 | 0 | 0 | 0 | 0 |
| **LUT 조회 수** (`LutMemo.lookup` 호출) | 65,372 | 65,372 | 20,725 | 20,725 |
| `derive_child` 호출 | -- | 65 | -- | 52 |
| 그 가운데 같은 (parent, keep) 반복 | -- | **63** (최대 35회 반복) | -- | **49** (최대 18회 반복) |
| derive_child 필드 수 parent -> child (평균) | -- | 529 -> 509 | -- | 361 -> 345 |
| derive_child가 빼는 writer | -- | dc_seal_report, metrics_aux, metrics_dc, metrics_ss, passive_values, ss_dev | (같음) | (같음) |
| `dc_seal_report` reuse / graft / compute | 15 / 1 / 49 | **0 / 16** / 49 | 9 / 3 / 40 | **0 / 12** / 40 |
| `ss_dev` reuse / graft | 같음 | 같음 | 3 / 0 | **0 / 3** |
| 그 밖의 블록 계수 | 같음 | 같음 | 같음 | 같음 |
| S3 `find` 호출 / 적중 | 1037 / 1 | 1052 / 16 | 806 / 3 | 818 / 15 |
| `seal_versions` 호출 / 같은 스냅샷 반복 | 65 / 0 | 65 / 0 | 52 / 0 | 52 / 0 |
| seal_versions가 순회하는 필드 수 (평균) | 529 | 509 | 361 | 345 |

### 1.2 시간 (plain, 단위 ms)

메모리 압박이 있는 기기라 실행마다 시간이 ±30~50% 흔들린다. 그래서 회차별 값을 그대로 적는다.

| 회차 | 측 | 탐색 전체 (s) | 평가 1회 중앙값 (evaluate) | 커널 1회 평균/중앙 (parent 있음) | derive_child 합 | seal_versions 합 | dc_seal_report 합 | graft 합 (dc_seal_report) |
|---|---|---|---|---|---|---|---|---|
| folded 1 | base | 15.45 | 169.5 | 141.1 / 133.2 | -- | 159.1 | 46.8 | 0.5 |
| folded 1 | head | 15.14 | 160.2 | 142.7 / 127.2 | 29.2 | 231.6 | 54.7 | 9.2 |
| folded 2 | base | 12.54 | 142.6 | 120.2 / 116.6 | -- | 146.7 | 43.0 | 0.6 |
| folded 2 | head | 10.12 | 107.1 | 92.0 / 89.1 | 23.2 | 99.7 | 34.9 | 6.1 |
| folded 3 | base | 10.47 | 93.8 | 83.7 / 81.1 | -- | 102.4 | 30.8 | 0.3 |
| folded 3 | head | 10.32 | 98.1 | 87.1 / 77.8 | 15.3 | 147.9 | 36.8 | 6.6 |
| two_stage 1 | base | 7.67 | 82.7 | 49.8 / 49.5 | -- | 71.3 | 29.4 | 1.0 |
| two_stage 1 | head | 9.62 | 106.2 | 65.5 / 68.1 | 14.9 | 99.1 | 42.2 | 7.4 (+ss_dev 2.0) |
| two_stage 2 | base | 5.90 | 64.3 | 36.0 / 36.9 | -- | 53.0 | 20.1 | 0.8 |
| two_stage 2 | head | 6.86 | 79.1 | 48.2 / 49.9 | 10.5 | 71.9 | 31.0 | 4.6 (+1.6) |
| two_stage 3 | base | 15.59 | 75.2 | 45.5 / 46.9 | -- | 67.6 | 26.7 | 1.2 |
| two_stage 3 | head | 6.85 | 90.6 | 51.7 / 60.3 | 11.5 | 72.0 | 31.9 | 4.4 (+2.4) |
| two_stage 역순 1 (head 먼저) | head | 5.97 | 72.6 | 44.3 / 43.9 | 10.6 | 68.0 | -- | -- |
| two_stage 역순 1 | base | 7.34 | 84.4 | 48.4 / 50.1 | -- | 68.4 | -- | -- |
| two_stage 역순 2 (head 먼저) | head | 6.01 | 77.9 | 46.3 / 48.4 | 9.5 | 77.0 | -- | -- |

- two_stage 정순 세 회차에서는 head 커널이 14~34% 느렸다. 그러나 head를 먼저 돌린 역순에서는 head가 더 빨랐다(44.3 대 48.4). 정순에서 보인 차이는 실행 순서 편향과 기기 잡음이다. 역순 2회차의 base와 역순 3회차는 메모리 부족으로 harness가 중단했다(§4).
- profile 모드(같은 조건에서 cProfile)의 커널 평균(parent 있음)은 folded 309.2 -> 306.6, two_stage 188.5 -> 195.2(+3.5%)였다. 탐색 전체는 28.60 -> 28.97 s, 19.80 -> 19.39 s였다.
- 함수별 tottime을 profile끼리 비교하면, IT-2a가 실제로 더한 일은 `derive_child`(folded 0.022 s / 65회)와 그 genexpr(35,490회)다. 그 밖의 상위 차이는 LUT, noise planes, 디스크 I/O의 회차 잡음이다(호출 수가 같거나 IT-2a와 무관한 함수).

### 1.3 head가 더한 일의 크기 (plain 기준)

| 항목 | 1회 비용 | folded 탐색당 | two_stage 탐색당 |
|---|---|---|---|
| `derive_child` | 0.2~0.45 ms | 15~29 ms (65회) | 10~15 ms (52회) |
| reuse가 graft로 바뀐 dc_seal_report | 0.3~0.6 ms | +5~9 ms (15회) | +4~7 ms (9회) |
| reuse가 graft로 바뀐 ss_dev | ~0.6 ms | -- | +1.6~2.4 ms (3회) |
| seal_versions (3)(4) used-writer 수집 | ~0.03~0.05 ms (profile 복제 측정) | 2~3.5 ms (65회) | ~1.7~2.4 ms (52회) |
| 합계 추정 | | **약 25~40 ms / 탐색 10~15 s (0.2~0.3%)** | **약 17~27 ms / 탐색 6~9 s (0.3%)** |

parent 스냅샷의 열·정렬 캐시는 스냅샷 객체에 붙어 있다. derive_child는 새 객체를 만들기 때문에 이 캐시가 비어서 시작한다. 그 결과 `GraphRecord.get` 호출이 folded에서 275,085 -> 288,066(+4.7%), two_stage에서 150,405 -> 156,235(+3.9%) 늘었다. 시간으로는 수십 ms 수준이고, 위 합계와 같은 자릿수다.

## 2. 같은 인자 재계산 (인자 지문 기준)

| 대상 | 지문 | folded | two_stage | 판정 |
|---|---|---|---|---|
| `derive_child` | (id(parent.snapshot), hash(frozenset(keep))), parent 참조를 보관해 id 재사용을 막음 | 65회 중 63회 반복(서로 다른 것 2개, 최대 35회) | 52회 중 49회 반복(3개, 최대 18회) | **중복 있음.** 같은 parent와 같은 keep에서 결과가 같은 child를 매번 새로 만든다 |
| `seal_versions` | id(snapshot) | 반복 0 | 반복 0 | 중복 없음. 매번 다른 스냅샷이다 |
| `seal_versions` (3)(4) used-writer 수집 | -- | 매 호출 스냅샷 전체 순회(평균 509 필드) | 345 필드 | 매번 스냅샷 전체를 돈다. 다만 스냅샷이 매번 달라 같은 인자 재계산은 아니다. 1회 0.03~0.05 ms |
| 계산 블록 (`recompute_same_input`) | (block, part, input_version) | 0 | 0 | 중복 없음 |
| 커널 평가 (`recompute_same_key`) | eval_key | 0 | 0 | 중복 없음 |
| LUT 조회 | 수 | base = head | base = head | IT-2a로 인한 변화 없음 |

derive_child 반복이 나오는 자리는 parent를 고정한 채 여러 점을 평가하는 호출부다.
- `gmid_engine/search/fd_jacobian.py:107`: `evaluate(…, parent=base, …)`. FD 열마다 같은 base를 넘긴다.
- `gmid_engine/search/l_bin_search.py:63`: `evaluate(…, parent=base, …)`
- 파생 자리는 `gmid_engine/sizing/kernel_run.py:85-87`이고, 본체는 `gmid_engine/core/graph_snapshot.py:149-168`이다.

## 3. 판정과 해결안 (제안만, 결정은 오케스트레이터)

**head는 base보다 느려지지 않았다.** wall time 차이는 실행 순서를 뒤집으면 방향이 바뀌어 잡음 안에 있다. 결정적 계수로 본 추가 일은 탐색당 0.2~0.3%다. LUT 조회 수와 블록 compute 수는 그대로다. **같은 인자 재계산은 `derive_child` 하나에서 확인됐다.**

| # | 위치 | 내용 | 해결안 (graph 단일 정본 점검) | 권고 |
|---|---|---|---|---|
| P1 | `sizing/kernel_run.py:85-87` 파생 호출, 근원 `search/fd_jacobian.py:107`·`search/l_bin_search.py:63` | 같은 (parent, keep)로 derive_child를 반복한다(63/65, 49/52). 1회 0.2~0.45 ms, 탐색당 10~29 ms | (a) **그대로 둔다.** 비용이 잡음보다 작다. (b) 계산 순서 조정: FD와 L-bin 루프 밖에서 parent를 한 번 파생해 넘긴다. size_and_seal의 parent 계약(`DcEvaluation`)과 설계 41 4.7-3c가 바뀌므로 계획과 design을 먼저 고쳐야 한다. (x) 호출 사이에 (parent, keep) -> child를 기억하는 memo는 블록 밖의 새 cache라 **금지**다. 블록 안 지역 memo는 반복이 호출 사이에서 일어나므로 적용할 수 없다 | **(a)** |
| P2 | `sizing/kernel_run.py:86-87` | keep 집합을 호출마다 새로 만든다. 블록 이름 부분(kernel 블록 4개 ∪ `SEAL_ITEM_BLOCKS` 8개)은 모듈 불변식이다 | 불변식을 밖으로 뺀다: 이름 부분을 모듈 상수 frozenset 하나로 만들고(정의는 `SEAL_ITEM_BLOCKS`와 블록 객체를 읽는다), 호출마다 `base_writers`와 합집합만 한다. 값 사본이나 sctx 슬롯은 아니다. 효과는 µs 단위다 | 선택 (효과 미미) |
| P3 | `sizing/seal.py:75` (dc_seal_report), ss_dev | parent에 있던 dc_seal_report·ss_dev가 keep 밖으로 빠져 reuse가 S3 graft로 바뀌었다(folded 15, two_stage 9+3). graft 1회 0.3~0.6 ms | 설계 의도와 같다(size_and_seal.py 머리: "keep 밖이라 같은 입력이면 S3 graft"). 허용된 재사용 경로(S3 graft)다 | 조치 없음 |
| P4 | `sizing/seal_versions.py:35` | used-writer 수집이 매 호출 스냅샷 전체를 돈다 | 호출마다 스냅샷이 다르다(반복 0). 단언 (3) coverage는 정의상 모든 필드를 봐야 한다. 1회 0.03~0.05 ms | 조치 없음 |
| P5 | `core/graph_snapshot.py:168` | derive_child가 새 스냅샷을 만들어 parent의 `_order_cache`·`_column_cache`·레코드 지문이 이어지지 않는다(GraphRecord.get +4~5%) | 캐시를 child로 옮기면 값 사본·cache 이전에 해당할 수 있어 **승인 없이는 하지 않는다.** 크기는 P1과 같은 자릿수다 | 조치 없음 |

참고(IT-2a 범위 밖, base에도 있음): `seal_versions` (1)은 블록마다 `input_version`을 다시 잰다(`seal_versions.py:22`). 투영을 다시 만드는 이 비용이 profile 복제 측정으로 seal_versions 시간의 약 60%(folded 0.26~0.28 s / 65회)다. 최종 스냅샷에서 다시 재는 것이 이 단언의 목적이라 같은 인자 재계산은 아니다. 기록만 한다.

## 4. 한계

- 기기 메모리 압박 때문에 wall time 잡음이 크다(같은 측을 반복해도 ±30~50%). 결론은 결정적 계수와 각 항목의 1회 비용을 근거로 냈다.
- 순서를 뒤집은 two_stage 측정(`rev/`)은 2회차 base부터 harness가 메모리 부족으로 중단했다. 다시 돌리지 않았다. 완료된 것은 head 2회와 base 1회다.
- `LutMemo.stats()` 영역별 hits·misses 차분은 0으로 나왔다(하네스가 읽는 칸이 맞지 않은 것으로 보인다). LUT 조회 수는 `LutMemo.lookup` 래퍼 계수로 쟀다.
- profile 모드 시간에는 관찰 부가 계산(seal_versions 복제 등)이 들어 있다. 그래서 1회 비용과 시간 비교는 plain 값을 썼다.
