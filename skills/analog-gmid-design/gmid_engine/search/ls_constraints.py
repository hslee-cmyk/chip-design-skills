"""출력 구동 선언(`driving_spec`) 제약 행 -- MOD5 `ls_fields` 보고에서 (설계 40 §3.8-3, 계획 DEC-58·DEC-70, 체크리스트 D-GB8a).

진입점: `ls_constraint_rows(bundle, driving) -> (rows, unmeasured)`.

* `driving` = spec `DrivingDecl`(슬루율 `slew_rate_v_per_s`·피크 부하 전류 `load_peak_amp`; `load_dc_amp` 는 DC 봉인의 KCL 입력이라 여기 행이 없다). 없으면 행도 미측정도 없다.
* `bundle` = 그 점의 `MetricBundle`(`ss_evaluate(...).ss`). 봉인 안 된 점(None)이면 선언마다 미측정 `ss_requires_sealed_snapshot`. 보고 `ls_fields` 가 없으면 `ls_fields_unavailable`
  (구조 입력 없음 -- `build_search_context(s1v=)` 를 안 줬거나 전달 뷰 제약이 없다).
* **슬루율 행**: 극점 노드 k·방향 d(충전·방전)마다 I_max,k,d ≥ SR · C_k,total ⇔ c = (I_max − SR·C)/s. s = 그 방향 전류의 분해능(`ls_fields` 가 낸 값 -- β 셀 합이면 부동소수 해상도),
  `active` = c ≤ 1. 전류가 미상(κ 셀·공급 셀 없음)이거나 분해능이 없으면 행 없이 미측정(`slew_current_unbounded`·`slew_resolution_undefined`). 행 이름 `ls:<net>:<방향>:slew_rate>=`.
* **피크 전류 행**: `load_peak_margin_a`(출력 노드 방향 전류 최솟값 − 피크 전류) / 출력 노드 전류 분해능 최대값, 이름 `ls:load_peak_amp>=`. 출력 노드 전류가 미상이면 미측정
  `load_peak_current_unbounded`.
"""
from gmid_engine.metrics import REPORT_LS_FIELDS

from .search_values import ConstraintRow

_NOT_SEALED = "ss_requires_sealed_snapshot"
_UNAVAILABLE = "ls_fields_unavailable"
_METRIC_SLEW = "slew_rate_v_per_s"
_METRIC_PEAK = "load_peak_amp"
_DIRECTIONS = ("charge", "discharge")


def ls_constraint_rows(bundle, driving):
    if driving is None:
        return (), ()
    declared = tuple((m, v) for m, v in ((_METRIC_SLEW, driving.slew_rate_v_per_s), (_METRIC_PEAK, driving.load_peak_amp)) if v is not None)
    if not declared:
        return (), ()
    if bundle is None:
        return (), tuple((m, ">=", _NOT_SEALED) for m, _v in declared)
    reports = [dict(rep) for name, rep in bundle.reports if name == REPORT_LS_FIELDS]
    if not reports:
        return (), tuple((m, ">=", _UNAVAILABLE) for m, _v in declared)
    rows, unmeasured = [], []
    for report in reports:
        nodes = report["nodes"]
        if driving.slew_rate_v_per_s is not None:
            for net, cap, i_ch, i_dis, _s_ch, _s_dis, r_ch, r_dis, _sources in nodes:
                for direction, current, res in zip(_DIRECTIONS, (i_ch, i_dis), (r_ch, r_dis)):
                    if current is None:
                        unmeasured.append((_METRIC_SLEW, ">=", "slew_current_unbounded"))
                    elif not res or not res > 0:
                        unmeasured.append((_METRIC_SLEW, ">=", "slew_resolution_undefined"))
                    else:
                        c = (current - driving.slew_rate_v_per_s * cap) / res
                        rows.append(ConstraintRow("ls:%s:%s:slew_rate>=" % (net, direction), float(c), c <= 1))
        if driving.load_peak_amp is not None:
            margin = report["load_peak_margin_a"]
            scale = max([r for n in nodes for r in (n[6], n[7]) if r] or [0.0])
            if margin is None:
                unmeasured.append((_METRIC_PEAK, ">=", "load_peak_current_unbounded"))
            elif not scale > 0:
                unmeasured.append((_METRIC_PEAK, ">=", "slew_resolution_undefined"))
            else:
                c = margin / scale
                rows.append(ConstraintRow("ls:load_peak_amp>=", float(c), c <= 1))
    return tuple(rows), tuple(sorted(set(unmeasured)))
