---
id: 20261107-fs1-eval-calls-seal4
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_versions.py::test_pass_and_independent_version_formula
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_versions.py::test_it2a_seal_4_passes_when_fields_are_base_or_call_writers
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_versions.py::test_it2a_seal_4_rejects_base_writer_that_is_also_a_call
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_versions.py::test_it2a_seal_4_rejects_field_of_writer_outside_base_and_calls
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal_versions.py::test_it2e_coverage_violation_still_fails
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_undefined_evaluation
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_circuit_a_undefined
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_triode_declaration_reaches_item7
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_triode_declared_triode_point_still_sealed
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_never_sealed_snapshot (9 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_sealed_snapshot_when_all_pass (2 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_no_sealed_snapshot_when_item7_fails (2 case)
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_violation_reports_worst_item
test_id: skills/analog-gmid-design/gmid_engine/tests/sizing/test_seal.py::test_violation_item6_devices
---
## 문제의 test

`tests/sizing/conftest.py::eval_calls(ctx, theta, wf=None)` 가 돌려주는 `calls` 를 쓰는 test 24개(`seal_dc(snap, calls, ...)` 또는 `seal_versions(snap, calls, base)`, `expected_version(snap, blk, ex)`).
`eval_calls` 는 dc_solve 를 `blk(snap, *ex, donors=..., counters=..., wf=wf)` 로 부르지만 반환하는 `calls` 의 `(dc_solve, (items, kfixed, kres, ctx.lut))` 에는 `wf` 가 들어 있지 않다.

## 근거(oracle 또는 사용자 원문)

* interface §4.1: `wf` 는 dc_solve 의 필수 키워드이고, interface §4.2·§4(키): "같은 θ·다른 w_f 칸 = 다른 키", spec '관찰 가능한 계약' 4·그래프 규칙("평가 캐시는 ... 키 성분에 w_f 지문이 더해질 뿐"). 블록 호출이 같은 lineage(`snapshot.block_version(name) == 입력 버전`)면
  계산 없이 이전 스냅샷을 돌려주므로(`ComputeBlock.__call__`), `wf` 가 dc_solve **입력 버전에 들어가지 않으면** `evaluate(sctx, θ, cells, wf', parent=base)` 의 w_f 이웃 시험(N-2)과 같은 θ·다른 칸 평가(E-2)가 parent 의 낡은 스냅샷(옛 `w_key`)을
  그대로 돌려준다. 그래서 구현은 `wf` 를 입력 버전·투영(extras 맨 뒤)에 넣는다(`compute_block(keywords=("wf",))`, 호출은 키워드, 입력 버전 `block.input_version(snapshot, *extras_with_wf)`).
* 봉인 4(`seal_versions`)는 `block.input_version(snapshot, *extras)` 를 다시 재서 `snapshot.block_version(name)` 과 같아야 한다 -- 같은 extras(맨 뒤 `wf` 포함)로 재야 한다. 커널(`run_kernel`)의 `calls` 는 그렇게 만든다(실측: 커널 경로 test 는 item 4 통과).
  `eval_calls` 의 `calls` 는 `wf` 가 빠져 있어 재계산 버전이 기록 버전과 달라지고 봉인 4 가 `fail`(`blocks = ("dc_solve",)`)이 된다(실측: 위 24개, 실패 사유 전부 item 4 `blocks=('dc_solve',)` 또는 그 결과 단언 어긋남).
* 어떤 구현이든 이 두 요구를 함께 만족할 수 없다: (a) `wf` 가 입력 버전에 든다 (b) wf 없는 extras 로 잰 버전 == 기록 버전. (b) 를 택하면 N-2/E-2 가 깨진다.

## 요청

`eval_calls` 의 반환 `calls` 에서 dc_solve 의 extras 에 `wf` 를 맨 뒤 위치 값으로 더한다: `(dc_solve, (items, kfixed, kres, ctx.lut, None, None, wf))` 꼴(`geometry`·`realized` 자리 None). 그러면 `block.input_version(snap, *extras)` 와 `seal_versions` 가
기록 버전과 일치한다. 호출은 지금처럼 `blk(snap, *ex[:-1], wf=ex[-1], ...)` 또는 `blk.split(ex)` 로 가른다(`ComputeBlock.split` 공개 메서드). 또는 interface §4.1 에 'calls 의 dc_solve extras 맨 뒤 = wf' 를 한 줄 더한다.
`test_seal_versions.py::expected_version` 도 같은 extras 를 쓴다.
