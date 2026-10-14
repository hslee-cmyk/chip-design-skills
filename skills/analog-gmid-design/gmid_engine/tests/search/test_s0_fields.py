"""search/s0_fields.py -- search 의 S0 수준 graph 필드 이름·writer 와 S0 수준 스냅샷 권한표 `S0_WRITERS` (데이터 선언 모듈).

근거(oracle (d) 설계 문장, 기대값은 아래 리터럴):
- 설계 40 v1.9.1 §2.4.8 필드 소유표:
  * `graph/kernel: search_domain`(writer `search_domain`, §2.4.7 Q5 표), `constraint_classes`(제약 분류 블록, D8), `passive_area_decl`(면적 선언 블록).
  * `graph/s1v: noise_input_cells`(writer `noise_decl`, D7).
  * 출발 구간 행(D3): `device: start.row`·`start.point`, `graph/start: conflicts·inactive·macro·rungs·records·area_est_m2·area_fraction·uncovered`
    (writer `start_intervals`). `theta`·`cells`·`current_ref` 는 `rungs` 칸 0 의 사본이라 필드가 아니다(D3), `kvl_*`·`noise_inputs`·`placement` 는 U17 ②.
  * 단계 B 층 `graph/stage_b: residual_probe`(writer `residual_probe`), `dof_numeric`(writer `dof_numeric`) -- §2.4.1 '직렬화하지 않는다'(D5).
- §2.4.1 표 첫 행·§2.4.3: S0 수준 스냅샷 권한표는 S1·S1v·결합·GB4·커널 구조 파생·탐색 S0 필드를 모두 덮는다(필드마다 writer 하나).
"""
from gmid_engine.graph import S1_WRITERS, S1V_WRITERS
from gmid_engine.metrics import METRICS_S0_WRITERS
from gmid_engine.search import s0_fields as F
from gmid_engine.sizing import S2_WRITERS

START_FIELDS = (("device", "start.row"), ("device", "start.point"), ("graph", "conflicts"), ("graph", "inactive"), ("graph", "macro"),
                ("graph", "rungs"), ("graph", "records"), ("graph", "area_est_m2"), ("graph", "area_fraction"), ("graph", "uncovered"))
WRITER_OF = {
    ("graph", "search_domain"): "search_domain",
    ("graph", "constraint_classes"): "constraint_classes",
    ("graph", "passive_area_decl"): "passive_area_decl",
    ("graph", "noise_input_cells"): "noise_decl",
    ("graph", "residual_probe"): "residual_probe",
    ("graph", "dof_numeric"): "dof_numeric",
    **{kf: "start_intervals" for kf in START_FIELDS},
}


def test_record_keys():
    assert (F.START_KEY, F.STAGE_B_KEY) == ("start", "stage_b")


def test_each_search_field_has_the_design_writer():
    for (kind, field), writer in WRITER_OF.items():
        assert F.SEARCH_S0_WRITERS.writer_of(kind, field) == writer, (kind, field)


def test_start_writes_exact_and_no_copy_fields():
    assert set(F.START_WRITES) == set(START_FIELDS)
    for absent in ("theta", "cells", "current_ref", "ladder", "rows", "area_budget_m2"):
        assert ("graph", absent) not in F.START_WRITES


def test_search_table_has_no_extra_writer():
    writers = {w for _kf, w in F.SEARCH_S0_WRITERS.entries}
    assert writers == set(WRITER_OF.values())


def test_stage_b_writers_are_transient_list():
    assert set(F.STAGE_B_WRITERS) == {"residual_probe", "dof_numeric"}


def test_s0_table_covers_every_layer():
    for part in (S1_WRITERS, S1V_WRITERS, METRICS_S0_WRITERS, S2_WRITERS, F.SEARCH_S0_WRITERS):
        assert F.S0_WRITERS.covers(part)
