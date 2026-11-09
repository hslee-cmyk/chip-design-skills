# interface card: 20261104-it2e-partial-snapshot

card IT-2e(계획 v6.38.8 N6.6 범위 5, 완료 (11)(e), O-96, N3.3 '실패 평가의 부분 스냅샷', design 41 §4.7-3c, 40 파일표 `seal_versions`·`kernel_run`·`seal` 행).

test 작성 주체는 엔진 소스를 보지 않고 이 문서와 기존 test 하네스(`E/tests/**`)만 쓴다. `E/` = `skills/analog-gmid-design/gmid_engine/`. base = 통합 브랜치 IT-2d 병합 head.

## 관찰 가능한 계약

### 공개 이름

| 모듈 | 심볼 | 서명 |
|---|---|---|
| `gmid_engine.sizing.seal_versions` | `writers_in_scope` | `writers_in_scope(base, blocks) -> frozenset`. `base` = 커널 컨텍스트 스냅샷, None이면 `TypeError`. `blocks` = `ComputeBlock` iterable. 반환 = `base.block_versions` 키 ∪ {블록 `.name`} |

서명 불변: `size_and_seal`, `run_kernel`, `seal_dc`, `seal_versions`, `attach_partial`, `ss_evaluate`.

### 규칙

평가가 parent에서 파생된 스냅샷으로 블록 k에서 후보 실패하면 `EvalResult.partial`(= `exc.partial`):
- `block_versions` 키 = base writer ∪ k 앞 블록
- 필드 writer ⊆ 같은 집합
- k와 그 뒤 블록의 필드 없음(parent 값이 남으면 red)
- 대상 k = 커널 블록(평가 커널 steps·later 구성원)과 봉인 항목 블록 각각
- 봉인 위반 경로: 봉인 보고서 블록 `dc_seal_report` 필드까지 남음
- ss 단계 실패: 규칙 충족, 변경 없음

그래서 부분 스냅샷 지문은 (평가 키, 실패 지점)만으로 정해지고 parent와 무관하다.

합집합식 정의 자리 = `writers_in_scope` 하나. 부르는 자리 = 파생 keep(`kernel_run`), 봉인 4 coverage(`seal_versions`), 실패 부착(`kernel_run`·`seal`). 서로소 단언·parent 일치 검사의 base writer 단독 읽기는 대상 아님. 새 필드·cache·값 사본·블록 호출 0.

### 단언 금지

스냅샷 지문 절대값(같음·다름만), 어느 블록이 k인지의 고정 목록(구성은 실행 head에서 base·블록 상수로 읽음), S3 색인 내부.

## test 목록(접두 `test_it2e_`)

| id | 위치 | 내용 | oracle | base |
|---|---|---|---|---|
| T-E1 | `tests/sizing/test_kernel_run.py` | parent 있는 평가에서 커널 블록 k마다 후보 실패 주입: 키 = base writer ∪ k 앞 블록, k 이후 없음 | (변성) | red |
| T-E2 | `tests/sizing/test_size_and_seal.py` | 봉인 항목 블록 k마다 같은 단언 | (변성) | red |
| T-E3 | 같은 파일 | 대조: parent 없이 같은 θ·같은 주입(`size_and_seal` 직접 호출 또는 별도 커널 컨텍스트, 평가 키 캐시 거치지 않음)의 부분 스냅샷 fp = parent 경로 fp, S3 evals 실패 줄 `snapshot_fp`도 그 fp | (변성) | red |
| T-E4 | 같은 파일 | 봉인 위반 + parent: `dc_seal_report` 필드 남음(지우면 red), fp = 대조 평가와 같음 | (변성) | red |
| T-E5 | `tests/sizing/test_seal_versions.py` | `writers_in_scope` 값(손 집합), `base=None`이면 `TypeError`, coverage 위반 픽스처 FAIL 유지 | (손) | red(`ImportError`, 신규 함수) |
| T-E6 | `tests/sizing/test_seal_versions.py`(AST) | 'base writer ∪ 블록 이름' 합집합·coverage 차집합 꼴의 정의 자리 1, 호출 자리 = keep·coverage·부착, 그 밖 재구현 0 | (독립) | red |
| T-E7 | `tests/sizing/test_size_and_seal.py` | parent 없는 기존 부분 스냅샷 지문 불변 | (c) | green |
| T-E8 | `tests/sizing/test_kernel_run.py` | reuse·graft·compute 계수 변화 0(G-10) | (독립) | green |

**사례 유효 조건 둘**(어기면 그 사례는 무효, 통과로 세지 않음):
- (가) 주입한 θ에서 블록 k가 reuse·graft되지 않고 실제로 실패한다. 부분 스냅샷이 없거나 k가 실패 블록이 아니면 무효.
- (나) 대조 결과가 parent 경로 결과와 같은 캐시 객체가 아니다.

**주입 위치**: 블록 k의 입력 버전이 parent와 달라야 실패가 실행된다. 기존 하네스의 후보 실패 주입(`tests/search/test_kernel.py`의 `partial` 사례 35건 꼴)을 쓰고, 실패 블록은 `exc`의 블록 정보로 확인한다.

### green·기준선 공통 규칙(test 작성자 빈칸 답, 2026-11-04)

- **base green**: 표의 base 칸이 red여도 사례가 base에서 green이면, 그 사례가 옛 동작과 새 동작 모두에 성립하는 회귀 보호인지 확인하고 test는 유지한다. 그 사례는 red 예상 목록에서 빼고 판정자에게 나열한다. 사례 전체가 green이라 새 동작을 가르지 못하면 그 id에 red 사례가 하나는 남아야 한다.
- **회귀 기준선 fixture**(`tests/integration/fixtures/*`, NFR-4 덤프): test 작성자는 고치지 않는다. 판정자가 code 병합본에서 재측정하고 원인 칸을 적으며, 값 변화표는 O-225 보류 표지로 둔다(A-39). 재측정 전 그 test 실패는 판정 전 상태로 보고하고 통과로 세지 않는다.
- **폐기**: 정의가 바뀌어 전제가 깨진 test는 고치지 않고 지우며, 판정 기록 근거에 `retired_tests`(이름·사유)로 적는다. 판정자가 그 목록을 확인한다.

## 고칠 기존 test

없음 예상. 깨지면 보고한다. `tests/search/test_kernel.py`의 `partial` 사례는 parent 있는 줄의 지문이 바뀔 수 있다(동작 변경 칸).

## 판정 측정(audit)

| # | 측정 | 합격 |
|---|---|---|
| A1 | test | PASS |
| A2 | 전체 suite | IT-1 D-1 기준 |
| A3 | 부분 스냅샷을 판정·재사용 입력으로 읽는 엔진 소비자 `git grep`(N6.3 '대상 없음' (ii) 증거) | 0, 기록 + GL-1 병합 뒤 base에서 `ratchet.new` 0(새 키·수 증가 0). `block_columns.py` 쪽 줄어든 키는 판정자가 줄임. 행 추가로 통과시키면 `criteria_weakened`. 이 card는 rule 파일을 고치지 않는다(`structure.json` diff 0, A-34) |
| A4 | 지문 밖 결과 순수 리팩터링(필드별), 결정성 비트 동일 | PASS |
| A5 | 바뀐 실패 줄 수(base↔head evals 실패 줄 `snapshot_fp`), NFR-4 덤프 기준선 | **미완료(보류 다리: 13회로)**; 기준선 갱신은 작성자 아닌 주체가 |
