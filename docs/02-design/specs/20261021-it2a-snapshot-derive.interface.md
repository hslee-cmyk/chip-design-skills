# interface card: 20261021-it2a-snapshot-derive

card IT-2a -- 스냅샷 파생 규칙. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3(`41:n`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.core.graph_snapshot` | `GraphSnapshot.derive_child` | def derive_child(self, keep_writers) -> GraphSnapshot |
| `gmid_engine.sizing.seal_versions` | `seal_versions` | def seal_versions(snapshot, calls, base) |

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2a_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-L11a | `tests/core/test_graph_snapshot.py`·`tests/sizing/test_kernel_run.py` | `derive_child` keep 밖 필드·`block_version` 삭제; parent에 커널 밖 writer 필드를 실은 픽스처 → child에 없음; base writer 필드 남음; parent 없는 평가 봉인 4 통과; base writer 버전 다른 parent `ValueError`(41:812 (a)) | (식)+(독립) | red |
| T-L11b | seal test 파일 | 위반 픽스처 둘 → `SEAL_FAIL`·detail `foreign_writers`/`base_call_overlap`(먼저 실제 거부 확인) | (식) | red |
| T-L11c | `tests/search/…` | 같은 θ ss 재평가 → ss 블록 outcome `graft`, `computes` 증분 0 | (독립) | red |

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속).

## 판정 측정(audit)

I-1 red-green, I-2 G2·G5·G7(새 필드 없음 확인), I-3 9회로 결과 비트 동일(제외 칸 = 블록 계수·outcome -- 목록은 감사 소유), I-6 전체 suite·`tests/structure`. (I-n 정의 = 공통 문서 interface 측정표.)
