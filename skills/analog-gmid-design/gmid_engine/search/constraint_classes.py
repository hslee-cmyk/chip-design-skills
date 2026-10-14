"""spec 판정 제약 분류 계산 블록 -- 목적 축·ss·미측정 분류를 S0 수준 필드 `graph/kernel: constraint_classes` 에 쓴다
(설계 40 §2.4.7 'SearchContext 칸 배정'·§2.4.8, v1.9.1 D8; 설계 7.2·S-1 '빠뜨리지 않음').

진입점: `constraint_classes`(`@compute_block`, writer `constraint_classes`) -- `constraint_classes(snapshot, judged_constraints)`.

* extras: `judged_constraints` = spec `judged_constraints`(선언 순서). metric 레지스트리·카탈로그는 코드 정의라 블록 코드·엔진 코드 지문이 덮는다.
* 분류(선언 순서대로 하나씩):
  - 값이 결정 대기(None)면 `notes` 에 judgment_pending 기록(metric·op·verdict·reason·decision).
  - 목적 축(`power_dc_w`·`area_search_m2`)이면 `judged` 에 (metric, op, float 값) -- 커널 결과로 잰다.
  - 레지스트리에 있고 뷰가 있거나 AUX 형식이면 `ss`(spec 안 위치) -- 점마다 `ss_constraint_rows` 가 잰다.
  - 그 밖은 `notes` 에 미측정 기록(카탈로그에는 있고 레지스트리에는 없으면 `metric_computation_pending`, 아니면 `metric_not_in_registry_or_no_ss_view`) --
    조용히 통과하지 않고 보고에 드러난다(점마다 front 를 거르는 행은 아니다).
* 값 = `ConstraintClasses(judged, ss, notes)` -- notes 는 기록마다 (키, 값) 쌍 tuple(키 순서 = 기록 순서).
"""
from gmid_engine.core import compute_block
from gmid_engine.metrics import AUX_TYPES, metric_catalog, metric_registry
from gmid_engine.sizing import KERNEL_KEY

from .s0_fields import CONSTRAINT_CLASSES_WRITER, CONSTRAINT_CLASSES_WRITES
from .search_values import AXES, ConstraintClasses


@compute_block(CONSTRAINT_CLASSES_WRITER, writes=CONSTRAINT_CLASSES_WRITES)
def constraint_classes(projection):
    (declared,) = projection.extras
    judged, ss, notes = [], [], []
    registry = metric_registry()
    catalog = metric_catalog()
    for index, decl in enumerate(declared):
        if decl.value is None:
            notes.append((("metric", decl.metric), ("op", decl.op), ("verdict", "judgment_pending"),
                          ("reason", "constraint_value_pending"), ("decision", decl.value_decision)))
        elif decl.metric in AXES:
            judged.append((decl.metric, decl.op, float(decl.value)))
        elif decl.metric in registry and (registry[decl.metric].signature.view_kind is not None
                                          or registry[decl.metric].source_type in AUX_TYPES):
            ss.append(index)
        else:
            # [U5] 카탈로그에는 있고 레지스트리에는 없는 이름 = 서명만 있는 계산 대기 metric(metrics/pending_metrics.py)
            pending = decl.metric in catalog and decl.metric not in registry
            notes.append((("metric", decl.metric), ("op", decl.op), ("value", decl.value), ("verdict", "unmeasured"),
                          ("reason", "metric_computation_pending" if pending else "metric_not_in_registry_or_no_ss_view")))
    return {("graph", "constraint_classes"): {KERNEL_KEY: ConstraintClasses(tuple(judged), tuple(ss), tuple(notes))}}
