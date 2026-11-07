# dispute 20261107-fs1: `dc_solve` 직접 호출의 `wf` 전달 자리 (test 작성자 -> 오케스트레이터)

**결정: A-188, a0bf0903 -- 닫음.** interface §4.1: `dc_solve(snapshot, theta_items, fixed_values, resistor_values, lut, *, wf, donors, counters)`, `wf` 필수 키워드 인자, 빠지면 `TypeError`. `sizing/conftest.py` `run_blocks`·`eval_calls`와 `test_block_dc.py` 직접 호출을 이 꼴로 고쳤고 거부 test `test_dc_solve_wf_is_required_keyword` 를 뒀다.

- 근거: interface card §4.1 은 `size_and_seal`·`run_kernel`·`size_and_seal_local` 의 서명만 정하고, spec 재작성 범위 W13 은 "`wf`가 `dc_solve` extras로" 라고만 적는다. `dc_solve(snapshot, theta_items, fixed_values, resistor_values, lut, *, donors, counters)` 의 extras 에서 `wf` 의 위치(`lut` 앞/뒤)·키워드 여부를 interface 가 정하지 않는다.
- 영향: `tests/sizing/conftest.py` 의 `run_blocks`·`eval_calls` 와 `tests/sizing/test_block_dc.py` 의 직접 `dc_solve(...)` 호출(약 8곳), 이를 쓰는 `test_input_window`·`test_scc_newton`·`test_seal`·`test_seal_tolerances`·`test_seal_versions`·`test_seal_writers` 의 `run_blocks` 호출(약 96곳)이 새 서명으로 고쳐지지 않았다. 추측으로 위치를 정하면 code 쪽 서명과 어긋난다.
- 요청: interface card 에 `dc_solve` extras 의 `wf` 자리를 한 줄 정하면(예: 마지막 위치 인자) conftest `run_blocks`·`eval_calls` 두 함수와 직접 호출 8곳만 고치면 된다 (나머지 호출은 `run_blocks` 를 거친다).
- 처리: 이 자리만 미완으로 두고 나머지는 계속했다 (오케스트레이터 지시 6).
