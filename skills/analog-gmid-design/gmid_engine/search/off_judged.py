"""O-h: `off` 선언의 `judged_by` 검사 -- 탐색 전 실행당 한 번 (EO-1 범위 4, 설계 41 §4.8-6, 계획 O-221·O-222, A-45).

진입점: `check_off_judged_by(region_decl, constraint_classes, declared) -> None`.
* `region_decl` = {소자: `RegionDecl`}(S0 술어 필드 `device.region_decl` 의 값), `constraint_classes` = `ConstraintClasses`(S0 필드 `graph/kernel: constraint_classes`),
  `declared` = spec 판정 제약 선언 tuple(`spec.judged_constraints`, `constraint_classes.ss` 의 위치가 가리키는 선언).
* **판정 제약 칸** = `.judged` 의 ((metric, op, 값), ...) metric ∪ `declared[i].metric`(i ∈ `.ss`). `.notes`(미측정·판단 대기)는 아니다.
* off 소자마다 `judged_by` 의 모든 metric 이 아래를 만족해야 한다. 어긴 첫 사유(표 순서, 소자 이름순)로 `SchemaRejectedError`(stop 부류 -- 후보 실패가 아니라 작성자 판단):
  1. `off_judged_by_undeclared`: `judged_by` 가 빈 값.
  2. `off_judged_by_not_judged`: metric 이 판정 제약 칸에 없다.
  3. `off_judged_by_unverified`: 판정 제약 칸에 있어도 `verified_by(metric).kind` ≠ `spice_oracle`(`spice_unverifiable`·`engine_only`) 이거나 레지스트리 밖이다(`verified_by` 가 `KeyError`).
  이유: off 소자의 전류 효과는 오라클이 같은 정의로 다시 재는 metric 으로만 확인할 수 있다(엔진은 1차 ΔV 로 판정, 오라클 왕복은 OP-5).
* 통과하면 None 을 낸다. 값을 저장하지 않는다.
"""
from gmid_engine.authoring import REGION_OFF
from gmid_engine.core import SchemaRejectedError
from gmid_engine.metrics import SPICE_ORACLE, verified_by

GATE = "off_judged_by"


def _stop(reason, violations):
    return SchemaRejectedError(detail={"gate": GATE, "reason": reason, "violations": tuple(violations)})


def check_off_judged_by(region_decl, constraint_classes, declared):
    off = tuple((m, region_decl[m]) for m in sorted(region_decl) if region_decl[m].region == REGION_OFF)
    empty = [(m, ()) for m, r in off if not r.judged_by]
    if empty:
        raise _stop("off_judged_by_undeclared", empty)
    judged = {metric for metric, _op, _value in constraint_classes.judged} | {declared[i].metric for i in constraint_classes.ss}
    absent = [(m, metric) for m, r in off for metric in r.judged_by if metric not in judged]
    if absent:
        raise _stop("off_judged_by_not_judged", absent)
    unverified = []
    for m, r in off:
        for metric in r.judged_by:
            try:
                kind = verified_by(metric).kind
            except KeyError:
                kind = None
            if kind != SPICE_ORACLE:
                unverified.append((m, metric))
    if unverified:
        raise _stop("off_judged_by_unverified", unverified)
