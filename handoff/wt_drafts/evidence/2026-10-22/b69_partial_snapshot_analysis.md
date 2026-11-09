# B69 분석 -- 실패 평가 부분 스냅샷의 parent keep 필드 (읽기 전용)

- 대상: worktree `wt/integ-it12` head `0c048327`, 엔진 `E = skills/analog-gmid-design/gmid_engine`
- 정본: 계획 v6.31 N3.3(스냅샷 파생 규칙)·U-93(X-3), design 40 §2.4.7 '실패 평가의 부분 스냅샷', design 41 v1.12.8 4.7-3c(753행)
- 원자료: `.ai/verification/20261021-it2a-snapshot-derive/raw/{probe_b69.jsonl, run3, run4}`, 같은 폴더 `scripts/test_zz_it2a_audit_probe.py:117-143`
- 파일 수정·커밋 없음. 실측은 import 한 번(블록 READS 순서 점검, 스크립트는 scratchpad)과 감사 raw 재집계뿐이다.

## 0. 사실 정정(브리핑 대비)

1. **낡은 필드는 k+1..8이 아니라 k..끝이다.** 실패한 블록 k 자신의 parent 필드도 남는다. 블록 호출(`E/core/compute_block.py:143`)은 `block_version(name) == version`이면 그 스냅샷을 그대로 돌려주므로(reuse), 실패했다는 것은 k의 입력 버전이 parent와 다르다는 뜻이다. 그런데 들어간 스냅샷에는 parent의 k 필드가 그대로 있다. 감사 탐침 `probe_b69.jsonl`(kcl 주입)에서 `dc_seal_kcl: [true, true]`(있음, parent 버전과 같음)로 확인했다.
2. **커널 블록에서 실패해도 같다.** `dc_columns`나 `dc_widths`에서 실패하면 그 뒤 커널 블록과 봉인 항목 여덟의 parent 필드가 모두 남는다(`E/sizing/kernel_run.py:85-89`, `:56-62`). design 41 753은 이것을 '커널 블록에 이미 있던 성질'로 적었다.
3. **ss 단계 실패와 봉인 위반에는 낡은 필드가 없다.**
   - ss 단계: 시작 스냅샷은 봉인 스냅샷이다. ss writer는 keep 밖이라 derive_child가 이미 뺐다. 그래서 ss 부분 스냅샷에는 이번 평가에서 쓴 ss 필드만 있다.
   - 봉인 위반: 12블록을 모두 부른 뒤라 낡은 필드가 없다. `dc_seal_report`는 derive 때 빠졌고 이번에 새로 썼다(`E/sizing/seal.py:79-88`).
4. **감사 41행은 B69 사례가 아니다.** 41행은 BASE 쪽이 parent의 keep 밖 필드(metrics·ss·report)를 더 가졌던 차이다. run4에서 writer 목록을 실측한 32행을 다시 집계했다.
   - HEAD 부분 스냅샷 32개 가운데 29개는 ss 단계 실패다(ss_dev·passive_values가 있음).
   - 3개(folded 1, two_stage_ota_sf 2)는 12블록이 모두 있고 `dc_seal_report`가 없다. `dc_seal_report` 블록 실패인지 봉인 항목 실패(B69 사례)인지는 raw에 실패 단계가 없어 **미확인**이다.
   - 9회로 HEAD(run3)의 실패 줄 부분 스냅샷은 150개다. 이 중 parent가 있는 DC·봉인 항목 단계 실패가 몇 개인지는 **미확인**이다(eval_fps 행에 parent·실패 단계 칸이 없다).

## 1. 소비자 전수

grep 범위: `attach_partial`, `.partial`, `partial=`, `snapshot_fp`, `evals.jsonl`, `write_snapshot`. 대상은 엔진 전체와 저장소 전체(docs·.ai 제외)이고, 결과는 tests 밖과 tests 안으로 나눠 적었다.

| # | 자리 | 무엇을 하나 | parent 낡은 필드를 값으로 읽나 | 어디로 들어가나 |
|---|---|---|---|---|
| P1 | `E/sizing/kernel_run.py:56-62` `_call_block` | 커널 블록 실패 때 들어간 스냅샷을 `attach_partial` | 읽지 않음(붙이기만) | 생산자(낡은 필드가 들어오는 입구) |
| P2 | `E/sizing/seal.py:66-70` | 봉인 항목 블록 실패 때 같은 동작 | 읽지 않음 | 생산자(B69가 넓힌 입구) |
| P3 | `E/sizing/seal.py:74-78`·`:87` | report 블록 실패, 봉인 위반 | 읽지 않음 | 생산자. 낡은 필드 없음(0절 3) |
| P4 | `E/metrics/ss_evaluate.py:113-115` | ss 단계 실패 | 읽지 않음 | 생산자. 낡은 필드 없음 |
| C1 | `E/search/kernel.py:128`·`:141` | `exc.partial`을 지역 `partial`로 받음 | 읽지 않음 | `EvalResult.partial`(`:166-167`) |
| C2 | `E/search/kernel.py:89-90` `_record` | `rec["snapshot_fp"] = result.partial.fp` | **fp만** 읽음. fp는 값 내용 지문이라 낡은 값이 지문에 섞인다(`E/core/graph_snapshot.py:40-41`, `:65-73`) | S3 `evals.jsonl` 실패 줄의 기록 식별자 |
| C3 | `E/search/kernel.py:170` `sctx.cache[key] = result` | EvalResult를 평가 키로 보관. 적중하면 같은 객체를 돌려줌(`:101-106`) | 읽지 않음 | 같은 θ 재요청이 같은 객체를 받음. 판정 입력 아님 |

이어서 소비자가 없음을 확인한 자리:

- **parent로 쓰는 자리**: `evaluate`의 parent는 `parent.evaluation`이다(`:123`). 실패 결과의 `evaluation`은 None이므로 parent가 없는 평가가 된다. 부분 스냅샷을 parent로 쓰는 코드는 0곳이다(design 40 §2.4.7 '재사용' 행과 같음). parent를 넘기는 탐색 자리는 `fd_jacobian.py:107`, `layer0_center.py:324`, `l_bin_search.py:63`, `slsqp_outer.py:118`이고, 모두 `res.evaluation` 계보를 쓴다.
- **재사용 키(graph reuse·S3 graft)**:
  - S3 색인에는 블록이 성공한 출력 스냅샷만 등록된다(`compute_block.py:170`). 실패는 `FailureRecord`만 등록된다(`:161`). 부분 스냅샷 객체는 등록되지 않는다.
  - 등록된 중간 스냅샷에도 아직 부르지 않은 블록의 parent 필드는 있다. 그러나 graft는 `block.writes` 열만 옮기고 `donor.block_version(block.name) == input_version`을 확인한다(`E/core/graft.py:17-23`). 그래서 낡은 필드는 다른 평가로 넘어가지 않는다.
  - graph reuse는 그 블록의 버전이 같을 때만 성립한다. 낡은 필드가 '입력 버전이 같은 값'으로 잘못 쓰이는 경로는 없다.
- **판정(FailureRecord)**: 실패 블록은 자기 READS 투영만 읽는다. 커널 4블록과 봉인 항목 8블록의 READS writer가 모두 자기보다 앞 블록이거나 base writer임을 import로 실측했다. 자기 자신이나 뒤 블록에서 읽는 READS는 0이다(스크립트 `scratchpad/reads_order.py`, 12블록 전부 `[]`). 그래서 실패 판정은 낡은 필드를 읽지 않는다. 실패 경로에서는 봉인 4가 돌지 않으므로 이 순서 성질이 유일한 보장이다.
- **보고·출력**:
  - `find_front.py:61`은 `res.evaluation.snapshot.fp`(성공)만 읽는다.
  - `archive.write_snapshot`이 디스크에 쓰는 스냅샷은 front 점과 채택 해뿐이다(`archive.py:6`, `:58-60`). 실패 부분 스냅샷의 본문은 디스크에 남지 않는다.
  - `start_points.py:41-42`와 `layer0_center.py:448-494`는 `res.failure`만 읽는다.
- **S0 디스크 스냅샷·재시작·front 조회**: `evals.jsonl`을 읽는 엔진 코드는 0곳이다. `front_entries.py`·`front_query.py`는 `runs.jsonl`의 front 항목만 읽는다. tools·legacy에도 소비자가 없다(git grep 0).
- **tests**:
  - `tests/search/test_kernel.py:457-621`(B-T19·B-T20)은 모두 **parent 없는** 평가다. `partial.block_versions` 포함·제외와 `line["snapshot_fp"] == r.partial.fp`를 단언한다.
  - `tests/core/test_failure_partial.py`는 attach 계약이다.
  - parent가 있는 실패의 부분 스냅샷을 단언하는 test는 0개다.

## 2. 영향 판정

- **값이 쓰이는 경로(판정·출력 값·재사용 키)는 0이다.** parent 낡은 필드를 값으로 읽는 엔진 소비자는 없다.
- **fp만 다른 경우(기록 식별자)는 있다.** C2 실패 줄 `snapshot_fp` 하나다.
  - 부분 스냅샷 fp는 값 내용 지문이다. 그래서 **같은 θ·같은 실패 지점이라도 parent가 무엇이냐에 따라 fp가 달라진다.** parent가 없으면 낡은 필드가 없고, parent가 있으면 parent 값이 섞인다.
  - 성공 줄의 fp는 모든 필드가 이번 평가에서 확인된 값이므로 parent와 무관하다. 실패 줄만 '같은 평가 = 같은 지문'이 깨진다. 탐색 경로가 바뀌면 같은 실패 θ의 지문이 바뀐다.
  - 실행 안에서는 평가 키 캐시(C3) 때문에 한 θ를 한 번만 평가하므로 드러나지 않는다. 실행 사이나 기준선 사이 대조에서 드러난다. IT-2a 감사가 부분 지문 41행 차이를 따로 설명해야 했던 것이 같은 종류의 비용이다.
- **design 계약과의 차이**: design 40 §2.4.7 '형식' 행은 "어디까지 계산했는지는 그 스냅샷의 `block_versions`가 말한다"고 적는다. parent가 있으면 실패 블록 k와 그 뒤 블록이 parent 버전으로 `block_versions`에 있으므로 이 문장이 거짓이다(as-built ≠ design 40, 작음). test B-T19 (4)가 적은 계약 "그 블록·이후 블록 필드 없음"도 parent가 있으면 성립하지 않는다. parent 경로 test가 없어 지금은 드러나지 않는다.
- **계획 문언과의 차이**: U-93은 '그때까지 계산한 부분 스냅샷', N3.3은 "'없음'이 '낡은 값'보다 안전(fail-closed)"이라고 적는다. 지금 부분 스냅샷에는 이번 평가가 계산하지도 확인하지도 않은 값이 있다. design 41 753이 이미 '원래 취지와 다름(작음)'으로 표시했다.
- **결론**: 사용자 결과·판정·재사용에 주는 영향은 0이다. 기록 식별자(fp)의 결정성과 design 40 계약 문장 하나가 어긋난다. 앞으로 실패 스냅샷을 저장하거나 읽는 소비자(design 40이 적은 U17 ② G-7 최종 형식 등)가 생기면 그때 바로 낡은 값 경로가 된다. 지금 고치는 비용이 작은 쪽이다.

## 3. 해결안(가장 일반적인 형태부터)

일반형 규칙은 다음과 같다. **부분 스냅샷 = 실패 시점 스냅샷에 N3.3 스냅샷 파생 규칙을 '이미 부른 블록'으로 적용한 것.** 즉 `derive_child(base writer ∪ 이번 평가에서 실패 전에 부른 블록)`이다. parent에서 파생할 때의 keep(base writer ∪ 부를 블록)과 같은 술어이고, 봉인 4 coverage 술어(`E/sizing/seal_versions.py:32-36` -- writer ∈ base writer ∪ calls)와도 같다. 회로 이름이나 상수는 들어가지 않는다.

### (가) 실패 시점 부분 스냅샷을 '이미 부른 블록 ∪ base writer'로 줄인다 -- 권고

- **자리**:
  - P2(`seal.py:69`): `calls`(커널 블록 + 이미 성공한 봉인 항목, `:63`·`:71`)와 `base`(필수)가 이미 손에 있다.
  - P1(`kernel_run.py:61`): `run_kernel` 루프의 '이미 부른 블록' 지역 tuple을 `_call_block`에 넘긴다.
  - 술어의 정본은 함수 하나로 둔다. 예: `seal_versions.py`에 `base ∪ calls` 이름 집합을 내는 함수를 두고, `run_kernel`의 derive(`kernel_run.py:86-87`), 봉인 4 coverage, 부분 스냅샷 줄이기가 모두 그 함수를 부른다. `kernel_run → seal → seal_versions` import 방향이라 순환이 없다. 지금도 같은 집합식이 `kernel_run.py:86`과 `seal_versions.py:32-36` 두 곳에 있으므로, 셋째 사본을 만들지 않고 한 곳으로 모으는 편이 규칙 1·3에 맞다.
  - P3의 봉인 위반 경로에서는 줄이지 않는다. 줄인다면 `dc_seal_report`를 부른 블록에 넣어야 한다(빠뜨리면 방금 쓴 보고서가 지워진다). P3 report 실패 경로와 P4 ss 단계는 낡은 필드가 없어 줄여도 바뀌지 않는다. 일관성을 위해 P3 report 실패 경로에도 같은 함수를 둘 수 있다.
- **graph 단일 정본**: 위반 없음.
  - `derive_child`는 계획이 이미 승인한 구조 공유 파생이다. FieldValue 객체를 공유하므로 값 사본이 아니다.
  - 새 cache·memo·sctx 슬롯·EvalResult 칸이 없다(`exc.partial`·`EvalResult.partial`은 X-3/U-93으로 승인된 기존 칸).
  - writer를 더하지 않는다. 블록 호출이 없으므로 reuse/graft/compute 계수 변화가 0이고 G-10도 그대로다.
- **fail-closed**: 낡은 필드가 '없음'이 된다. 나중에 읽는 소비자는 낡은 값 대신 `KeyError`를 받는다. N3.3 원칙 그대로다.
- **결정성 회복**: 남는 필드는 base(모든 평가에 유효)와 이번 평가에서 reuse·graft·compute로 확인한 블록뿐이다. 그래서 부분 fp는 (θ, 실패 지점)만의 함수가 되고 parent와 무관해진다.
- **parent 없는 경로는 바뀌지 않는다.** 스냅샷 writer가 이미 base writer ∪ 부른 블록이다. 봉인된 평가에서 봉인 4 coverage가 통과한다는 사실(감사 579 봉인 행)이 base 자체가 이 술어를 만족한다는 증거다. 그래서 fp가 그대로이고, 기존 B-T19 (1)~(4)의 `partial.fp == entered.fp`도 그대로다. 단 test를 돌려 확인하지는 않았다(**미실측, 추론**).
- **바뀌는 test와 계수**:
  - 기존 test 변경 0(위 추론, 판정은 감사 실측).
  - 새 test(작성 = test 역할): parent가 있는 실패를 12블록(커널 4 + 봉인 항목 8)으로 매개화한다. 각 경우 (i) `partial.block_versions` 키 ⊆ base writer ∪ 대상 앞 블록이고 대상과 그 뒤 블록이 없음을 본다. (ii) 같은 θ·같은 주입을 parent 없이 평가한 부분 fp와 같은지 본다(parent 독립 -- 독립 oracle). 봉인 위반 + parent 1건(보고서가 남음)을 더해 약 13건이다.
  - 엔진 계수 변화 0. 9회로 기록에서는 parent가 있는 DC·봉인 항목 실패 줄의 `snapshot_fp`만 바뀐다. 줄 수는 **미확인**(0절 4의 3행이 후보).
- **계획·design 개정**: 계획 우선 규칙을 따른다.
  - 계획: N3.3 스냅샷 파생 규칙에 한 절을 더한다. 내용은 '실패 평가의 부분 스냅샷(U-93)에도 같은 규칙, 부르는 블록 = 실패 전에 부른 블록'이다. 또는 U-93 행에 같은 정오를 넣는다. 성격은 취지 회복이고 새 결정이 아니다. 지금 계획은 부분 스냅샷의 필드 범위를 정하지 않으므로, 규칙을 새로 적는 것은 계획 개정이다.
  - design 40 §2.4.7: '정의'·'형식' 행에 줄이는 방법과 자리를 적는다.
  - design 41 4.7-3c 753: B69 서술을 해소 문장으로 바꾼다.
  - 그 뒤 card로 진행한다.
- **실현 가능성 점검표**(코드로 끝까지 확인):

| 확인 | 결과 | 근거 |
|---|---|---|
| seal 실패 자리에 base·calls가 있나 | 있음 | `seal.py:48-50`(base 필수), `:63`·`:71`(calls 누적, 실패 블록은 `:71` 전이라 빠짐) |
| 커널 실패 자리에 '이미 부른 블록'이 있나 | 지역 변수로 만들 수 있음(지금은 넘기지 않음) | `kernel_run.py:88-89`, `:100-101` 루프 |
| derive_child가 base writer 버전·필드를 유지하나 | 유지 | `graph_snapshot.py:149-168` |
| parent 없는 경로가 no-op인가 | 술어 = 봉인 4 coverage, 봉인 행에서 통과 | `seal_versions.py:32-37`, 감사 579행 |
| 첫 부착 유지와 충돌하나 | 없음. 가장 안쪽(seal)이 줄인 스냅샷을 붙이고, 재연 예외는 바깥 `_call_block`이 줄여서 붙임 | `failure_partial.py:19-20` |
| 줄인 스냅샷이 S3 색인에 들어가나 | 안 들어감(등록은 블록 성공 출력만) | `compute_block.py:161`·`:170` |
| 계수·G-10 영향 | 0(블록 호출 없음) | -- |
| 상수·회로 이름 | 없음 | -- |

### (나) 부분 스냅샷을 '블록 진입 전 스냅샷'으로 바꾼다 -- 기각

지금 부착하는 것이 이미 '그 블록에 들어간 스냅샷'이다(`kernel_run.py:61`, `seal.py:69`). 문언 그대로 하면 아무것도 바뀌지 않는다. parent 경로에서 낡은 필드가 없는 더 이른 스냅샷은 `ctx.base`(derive 전)뿐이다. 그것을 붙이면 이번 평가가 실제로 계산한 앞 블록 결과가 사라져 U-93 '그때까지 계산한'에 어긋난다.

### (라) 참고 -- derive keep을 base writer만으로 줄이고 모두 S3 graft로 되돌린다 -- 기각

부분 스냅샷 문제는 저절로 사라진다. 그러나 다음 이유로 기각한다.

- 커널 12블록의 graph reuse 경로를 없앤다. 계획 O-59 (2)·N3.3의 '두 길' 중 하나를 바꾸는 큰 계획 개정이다.
- 9회로 계수 행이 reuse→graft로 넓게 바뀐다.
- parent 결과가 같은 donors 색인에 등록돼 있어야 재계산 0이 된다. 모든 호출 경로에서 그런지는 **미확인**이다.
- 출력 기록 하나를 위해 엔진 전체 동작을 바꾸므로 비례하지 않는다.

### (다) 현행 유지 -- 차선

값 소비자가 0이므로 지금 결과는 바뀌지 않는다. 그러나 남는 문제가 셋이다. (1) 실패 줄 fp가 parent에 따라 달라진다. (2) design 40 §2.4.7 '형식' 문장과 B-T19 (4) 계약이 parent 경로에서 거짓이다. (3) N3.3 원칙과 반대 방향인 '원래 취지와 다름(작음)'이 계속 남는다. 유지하려면 그 차이를 사용자 승인으로 확정하고 design 40 문장을 고쳐야 하는데, 이것은 기준을 약하게 하는 쪽이다.

## 4. 권고

**(가)를 권고한다.** 부분 스냅샷은 실패 시점 스냅샷에 N3.3 파생 규칙을 '이미 부른 블록 ∪ base writer'로 적용한 것으로 정의한다.

- 계획 N3.3(또는 U-93)에 한 절을 더하고, design 40 §2.4.7과 design 41 753을 고친 뒤 card로 진행한다. 정본은 술어 함수 하나이고, 부르는 자리는 `run_kernel` derive, 봉인 4 coverage, `seal_dc`·`_call_block` 실패 부착이다.
- 근거:
  - 값 소비자가 0이라 위험이 작다.
  - 계수와 재사용 변화가 0이다.
  - 실패 줄 지문의 결정성(parent 독립)이 돌아온다.
  - design 40 계약 문장이 다시 참이 된다.
  - 새 저장이나 사본이 없다(graph 단일 정본 규칙 1~6 준수).
- **원래 취지와 다름 여부**:
  - 권고 (가): **취지 회복**이다(U-93 '그때까지 계산한', N3.3 "'없음'이 '낡은 값'보다 안전"). 원래 취지와 다르지 않다.
  - 현행 (다): design 41 753에 적힌 대로 '원래 취지와 다름(작음)'이다.
- **미확인**:
  - run3 9회로 실패 줄 150개 가운데 parent가 있는 DC·봉인 항목 단계 실패 수, 즉 (가)로 fp가 바뀔 줄 수. run4의 3행은 실패 단계를 판별하지 못했다.
  - parent 없는 경로의 fp 불변. 추론만 했고 test는 돌리지 않았다.
  - 봉인 아닌 점의 `passive_values`·`metrics_dc`(`kernel.py:142-147`)가 후보 실패를 낼 때의 처리. try가 없고 이 분석 범위 밖이다.
