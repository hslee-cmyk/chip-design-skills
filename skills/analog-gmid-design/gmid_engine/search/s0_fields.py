"""search 의 S0 수준 graph 필드와 S0 수준 스냅샷 권한표 (설계 40 §2.4.1·§2.4.2·§2.4.7·§2.4.8, v1.9.1 D3·D5·D6·D8).

데이터 선언 모듈이다(상수와 권한표뿐). 각 계산 블록 파일이 자기 writes 로 이 이름을 쓴다.

* `graph/kernel`(key sizing `KERNEL_KEY`): `search_domain`(writer `search_domain`), `constraint_classes`(writer `constraint_classes`), `passive_area_decl`(writer `passive_area_decl`).
* `graph/s1v: noise_input_cells`(writer `noise_decl` -- 값 = metrics `NoiseDecl` 전체, v1.9.1 D7).
* `graph/start`(key `START_KEY`, writer `start_intervals` -- 41 §6, A8): `conflicts`, `inactive`, `macro`, `rungs`(출발 사다리 칸 = as-built `ladder`, 칸 0 = 선택점), `records`(매크로 모델 기록),
  `area_est_m2`, `area_fraction`, `uncovered`; `device`: `start.row`(`StartRow`), `start.point`((VDS, VSB) -- 출발 곡선 동작점). `kvl_model`·`kvl_rows`·KVL 기록·`noise_inputs`·`placement` 은 U17 ②.
* 단계 B 층 `graph/stage_b`(key `STAGE_B_KEY`): `residual_probe`(writer `residual_probe`), `dof_numeric`(writer `dof_numeric`) -- 실행 안 상태다(디스크 스냅샷 없음, NFR-2·U-89). 블록 배선은 소비자 층 0 과 함께 U17 ②(v1.9.1 D5) -- 여기는 필드 자리와 writer 선언(`STAGE_B_WRITES`)뿐이다.
* `S0_WRITERS` = S2 권한표(sizing `S2_WRITERS` -- S1·쓰기 계획·커널 구조 파생·평가 커널 필드) ∪ graph `S1V_WRITERS`(S1v·결합) ∪ metrics `METRICS_S0_WRITERS` ∪ 이 파일의 표.
  S0 수준 스냅샷(단계 A 가 실행마다 처음부터 만들고 그 실행 안에서만 재사용하는 것)이 이 표 아래에 산다.
"""
from gmid_engine.core import WriterTable
from gmid_engine.graph import S1V_WRITERS
from gmid_engine.metrics import METRICS_S0_WRITERS
from gmid_engine.sizing import S2_WRITERS

START_KEY = "start"
STAGE_B_KEY = "stage_b"
SEARCH_DOMAIN_WRITER = "search_domain"
CONSTRAINT_CLASSES_WRITER = "constraint_classes"
PASSIVE_AREA_WRITER = "passive_area_decl"
NOISE_DECL_WRITER = "noise_decl"
START_INTERVALS_WRITER = "start_intervals"
RESIDUAL_PROBE_WRITER = "residual_probe"
DOF_NUMERIC_WRITER = "dof_numeric"
SEARCH_DOMAIN_WRITES = (("graph", "search_domain"),)
CONSTRAINT_CLASSES_WRITES = (("graph", "constraint_classes"),)
PASSIVE_AREA_WRITES = (("graph", "passive_area_decl"),)
NOISE_DECL_WRITES = (("graph", "noise_input_cells"),)
START_WRITES = (("device", "start.row"), ("device", "start.point"), ("graph", "conflicts"), ("graph", "inactive"), ("graph", "macro"),
                ("graph", "rungs"), ("graph", "records"), ("graph", "area_est_m2"), ("graph", "area_fraction"), ("graph", "uncovered"))
STAGE_B_WRITES = ((RESIDUAL_PROBE_WRITER, (("graph", "residual_probe"),)), (DOF_NUMERIC_WRITER, (("graph", "dof_numeric"),)))
SEARCH_S0_WRITERS = WriterTable(tuple(
    (kind, field, writer)
    for writer, writes in ((SEARCH_DOMAIN_WRITER, SEARCH_DOMAIN_WRITES), (CONSTRAINT_CLASSES_WRITER, CONSTRAINT_CLASSES_WRITES),
                           (PASSIVE_AREA_WRITER, PASSIVE_AREA_WRITES), (NOISE_DECL_WRITER, NOISE_DECL_WRITES),
                           (START_INTERVALS_WRITER, START_WRITES)) + STAGE_B_WRITES
    for kind, field in writes))
S0_WRITERS = S2_WRITERS.union(S1V_WRITERS).union(METRICS_S0_WRITERS).union(SEARCH_S0_WRITERS)
