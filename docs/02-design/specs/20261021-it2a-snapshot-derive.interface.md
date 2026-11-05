# interface card: 20261021-it2a-snapshot-derive

> **[상태 표지 2026-10-29] 완료 이력** -- IT-2a 판정 PASS(`integ/it12:.ai/verification/20261021-it2a-snapshot-derive.json`, code `bddef887`), master 미병합. 이 master 사본은 판정 전 동결본이다 -- 판정한 판(approval `20261022-it2a-seal-signature-ext`·`20261022-it2a-o94-ext`, keep = base writer ∪ 봉인 4 호출 목록)은 `integ/it12`에 있고 통합 병합 때 그 판으로 바뀐다. 후속 = card IT-2e(계획 v6.38.4 N6.6 범위 5 -- 같은 집합식을 함수 하나로, spec card 미작성). 본문은 기록이며 덧대지 않는다(O-169).

card IT-2a -- 스냅샷 파생 규칙. test 작성 주체는 소스를 보지 않고 이 문서와 공통 문서 `docs/02-design/specs/20261021-it2-common.md`의 '창 규칙'·'정의 불능 code' 절만 쓴다(DEC-38 -- 본문 코드 없음). 정본 문장 = design 41 v1.12.3(`41:n`). `E/` = `skills/analog-gmid-design/gmid_engine/`. 쓰기 경로 = `E/tests/**`(agent 정의의 옛 `assets/tests/**`가 아니다).

## 관찰 가능한 계약

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.core.graph_snapshot` | `GraphSnapshot.derive_child` | def derive_child(self, keep_writers) -> GraphSnapshot |
| `gmid_engine.sizing.seal_versions` | `seal_versions` | def seal_versions(snapshot, calls, base) -- base None이면 `TypeError` |
| `gmid_engine.sizing.seal` | `seal_dc` | def seal_dc(snapshot, calls, lut, resistances, linear_devices, raise_on_violation=True, *, base, donors, counters) -- `base` 기본값 없음(생략·None이면 `TypeError`) |

(v2 -- design 41 v1.12.8, 사용자 결정 O-94·O-95: keep = base writer ∪ 봉인 4가 받는 호출 목록(커널 블록 ∪ 봉인 항목 블록 여덟), `dc_seal_report`만 keep 밖 → S3 graft.)

### 단언 금지

`NodalSystem.factor` 내부 배열 값, `input_version` 문자열 값(같음·다름만), 분해능 수치 자체, `IcmConfig.transfer`의 resolution 수치, `IcmWindow.model_error_ref`(None만), S3 색인 내부, `RunCounters` 행 타입 이름.

## test 목록(위치 제안 -- 규칙 H 1:1, 이름 접두 `test_it2a_`)

| id | 위치 | 내용(정본) | oracle | base |
|---|---|---|---|---|
| T-L11a | `tests/core/test_graph_snapshot.py`·`tests/sizing/test_kernel_run.py` | `derive_child` keep 밖 필드·`block_version` 삭제; parent에 커널 밖 writer 필드를 실은 픽스처 → child에 없음; base writer 필드 남음; parent 없는 평가 봉인 4 통과; base writer 버전 다른 parent `ValueError`(41:812 (a)) | (식)+(독립) | red |
| T-L11b | seal test 파일 | 위반 픽스처 둘 → `SEAL_FAIL`·detail `foreign_writers`/`base_call_overlap`(먼저 실제 거부 확인) | (식) | red |
| T-L11c | `tests/search/…` | 같은 θ ss 재평가 → ss 블록 outcome `graft`, `computes` 증분 0 | (독립) | red |
| T-L11d | `tests/sizing/test_size_and_seal.py`(기존 4항목 기대 갱신 -- 승인 `20261022-it2a-o94-ext` 범위 2) | 같은 θ parent 재평가·passive θ(capacitance·ss_resistance)만 바뀐 재평가 → DC 열세 블록 computes 0, 커널 4·봉인 항목 8 outcome `reuse`(합 12), `dc_seal_report` outcome `graft` 1(design 41 v1.12.8 L11 (d)) | (독립) | red(base는 reuse 13) |
| T-L11e | seal test 파일 | `seal_versions(snapshot, calls, None)`·`seal_dc(…, base=None)`·`seal_dc`에서 `base` 생략 → `TypeError`(건너뛰어 pass면 red; L11 (d)) | (식) | 새 키워드 직접 호출이라 red로 세지 않음 |

기존 test 기계 수정(승인 `20261022-it2a-o94-ext` 범위 1·3): `test_seal_versions.py::test_empty_calls_pass` base = 그 test의 4 호출 뒤 스냅샷 자신(단언 그대로); 단위 test `seal_dc` 호출 7곳(`test_seal.py:21·163`, `test_scc_newton.py:791`, `test_seal_conduction.py:218·227·303·375` -- 줄은 role/code/it2a `973daf49` 기준)에 `base=ctx.base`.

red 예상 목록 = 엔진 동작·엔진 트리 구조를 보는 test(green 유지 대상·하네스 자체 test 제외). 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `-k` 식 충돌은 base·head `--collect-only` 수를 함께 보고(xrunf1b 3.3 상속).

## 판정 측정(audit)

I-1 red-green, I-2 G2·G5·G7(새 필드 없음 확인), I-3 9회로 결과 비트 동일(제외 칸 = 블록 계수·outcome -- 목록은 감사 소유), I-6 전체 suite·`tests/structure`. (I-n 정의 = 공통 문서 interface 측정표.)

## 변경 이력

- 2026-10-29 `cards/revise-1029`: 위 상태 표지만 더함 -- 본문 불변, 표지 전 원문 = `git show 052465ed:docs/02-design/specs/20261021-it2a-snapshot-derive.interface.md`.
