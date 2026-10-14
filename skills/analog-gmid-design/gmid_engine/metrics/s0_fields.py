"""metrics 의 S0 수준 graph 필드 -- 레코드 key·writer 이름·필드·권한표 조각 (설계 40 §2.4.1·§2.4.2·§2.4.8, v1.9.1 D2·D7·D8·D9).

데이터 선언 모듈이다(상수와 권한표 조각뿐). 각 계산 블록 파일이 자기 writes 로 이 이름을 쓴다. 이 조각은 S2 권한표(sizing `S2_WRITERS`)와 graph S1v·결합 표,
search 의 S0 필드 표와 합쳐 S0 수준 스냅샷 권한표가 된다(search `S0_WRITERS`).

* `graph/ach`(key `ACH_KEY`, writer `achievability` -- GB4, 41 A4~A7): `curve_checks`, `gain_checks`(`GainCheck` | None), `area_bound`, `headroom_rows`,
  `buffer_window_report`, `warnings`, `reasons`, `verdict`, `dof`(구조 DOF만 -- `numeric_ranks` = ()), `count_budget`, `local_inputs`(`LocalInputs`).
* `graph/s1v: metric_structure`(writer `metric_structure`, MOD5 -- metric 구조 입력 `MetricStructure`).
* `graph/kernel: junction_source`(writer `junction_source`), `mismatch_source`(writer `mismatch_source`), `model_error`(writer `model_error`).
"""
from gmid_engine.core import WriterTable

ACH_KEY = "ach"
ACHIEVABILITY_WRITER = "achievability"
METRIC_STRUCTURE_WRITER = "metric_structure"
JUNCTION_SOURCE_WRITER = "junction_source"
MISMATCH_SOURCE_WRITER = "mismatch_source"
MODEL_ERROR_WRITER = "model_error"
ACH_WRITES = (("graph", "curve_checks"), ("graph", "gain_checks"), ("graph", "area_bound"), ("graph", "headroom_rows"),
              ("graph", "buffer_window_report"), ("graph", "warnings"), ("graph", "reasons"), ("graph", "verdict"), ("graph", "dof"),
              ("graph", "count_budget"), ("graph", "local_inputs"))
METRIC_STRUCTURE_WRITES = (("graph", "metric_structure"),)
JUNCTION_SOURCE_WRITES = (("graph", "junction_source"),)
MISMATCH_SOURCE_WRITES = (("graph", "mismatch_source"),)
MODEL_ERROR_WRITES = (("graph", "model_error"),)
METRICS_S0_WRITERS = WriterTable(tuple(
    (kind, field, writer)
    for writer, writes in ((ACHIEVABILITY_WRITER, ACH_WRITES), (METRIC_STRUCTURE_WRITER, METRIC_STRUCTURE_WRITES),
                           (JUNCTION_SOURCE_WRITER, JUNCTION_SOURCE_WRITES), (MISMATCH_SOURCE_WRITER, MISMATCH_SOURCE_WRITES),
                           (MODEL_ERROR_WRITER, MODEL_ERROR_WRITES))
    for kind, field in writes))
