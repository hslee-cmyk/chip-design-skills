"""metric 검증 출처(`verified_by`)와 모델 오차(`model_error`) 레지스트리 (설계 40 §3.8-6, DEC-72·DEC-90 (3), 체크리스트 D-GB8c).

진입점: `verified_by(metric) -> VerifiedBy`.

레지스트리 항목(`metric_registry()`)마다 **누가 이 값을 다시 재는가**(`verified_by`)와 **그 대조 결과를 어디에 쓰는가**(`model_error_ref` = `derived.model_error_<metric>`)를 낸다.
* `verified_by` ∈ {`spice_oracle`(오라클이 같은 정의의 값을 잰다: 이득·UGF·GBW·PM·rout·비·전력 등 ngspice AC/DC 측정, offset 은 mismatch Monte-Carlo, 스윙·ICMR 은 `.dc`
  스윕 -- 40 §10.2), `spice_unverifiable`(오라클 측정이 없다 -> spec 로더가 `SizingSpecDoc.spice_unverifiable` 로 판정 제약 중에서 모아 실행 전에 출력, DEC-90 (3)),
  `engine_only`(엔진 내부 구조 가드라 오라클 대응이 없다)}.
* `measure` = 오라클이 쓰는 measure 이름(엔진은 이름만 든다, 오라클을 import 하지 않는다). 잴 수 없으면 None.
* 판정 계층은 `model_error_<metric>` 값(오라클-엔진 차의 크기, 같은 단위)을 분해능 바닥으로 쓴다(`ss_constraint_rows` -- NFR-5). 미측정이면 '판정 보류'(추정).

표는 이 파일 안의 상수 튜플이다(metric 이름 -> 출처). 레지스트리에 있는데 표에 없는 metric 은 `KeyError`(표를 빠뜨리지 않는다 -- test 가 레지스트리 전수를 대조).
`model_error.model_error_pairs(derived)` 가 `derived` 매핑({`model_error_<metric>`: 값})에서 `ss_constraint_rows(model_error=)` 가 받는 ((metric, 값), ...) 을 만든다.
"""
import dataclasses

from .registry import metric_registry

SPICE_ORACLE = "spice_oracle"
SPICE_UNVERIFIABLE = "spice_unverifiable"
ENGINE_ONLY = "engine_only"
MODEL_ERROR_PREFIX = "model_error_"


@dataclasses.dataclass(frozen=True)
class VerifiedBy:
    """metric 하나의 검증 출처. `kind` ∈ {spice_oracle, spice_unverifiable, engine_only}, `measure` = 오라클 measure 이름 또는 None, `model_error_ref` = 모델 오차 기록 키."""

    metric: str
    kind: str
    measure: object
    model_error_ref: str


# (metric, 종류, 오라클 measure 이름) -- measure 이름은 `tools/spice_oracle/oracle_compare.py` MEASURES·U6_MEASURES 의 실제 키다(엔진은 이름만 들고 import 하지 않는다).
# 오라클이 재지 않는 metric 은 measure None -- `spice_unverifiable`(구조 가드는 `engine_only`). gbw 는 오라클이 f3dB·UGF 만 재서 옛 어댑터(`legacy_adapter`)와 같이
# `ugf_hz` 로 대조한다(단일 극점 GBW = UGF).
_TABLE = (
    ("gain_ss_db", SPICE_ORACLE, "dc_gain_db"), ("ugf_ss_hz", SPICE_ORACLE, "ugf_hz"), ("gbw_ss_hz", SPICE_ORACLE, "ugf_hz"),
    ("parasitic_pm_ss_deg", SPICE_ORACLE, "pm_deg"), ("pm_ss_deg", SPICE_ORACLE, "pm_deg"), ("pm_cm_ss_deg", SPICE_ORACLE, "cm_pm_deg"),
    ("ratio_ss_db", SPICE_ORACLE, "ratio_db"), ("rout_ss_ohm", SPICE_ORACLE, "rout_ohm"),
    ("supply_current_dc", SPICE_ORACLE, "supply_current_A"), ("power_dc_w", SPICE_ORACLE, "supply_current_A"),
    ("area_search_m2", ENGINE_ONLY, None),
    ("offset_in_sigma_mv", SPICE_ORACLE, "offset_in_sigma_mv"), ("offset_excess", ENGINE_ONLY, None),
    ("offset_sys_mv", SPICE_UNVERIFIABLE, None), ("mirror_ratio_sigma_pct", SPICE_UNVERIFIABLE, None),
    ("swing_out_v", SPICE_ORACLE, "swing_out_v"), ("icmr_v", SPICE_ORACLE, "icmr_v"), ("icm_margin_v", SPICE_ORACLE, "icm_margin_v"),
    ("ff_gm_ratio", SPICE_UNVERIFIABLE, None),
    # [U7+U8 통합] 잡음 4개(U8): 오라클 `oracle_noise.py` 가 .noise 로 재고 `oracle_compare.py` MEASURES·U6_MEASURES 가 같은 키로 대조한다
    ("noise_th_in_v2hz", SPICE_ORACLE, "noise_th_in_v2hz"), ("noise_fc_in_hz", SPICE_ORACLE, "noise_fc_in_hz"),
    ("noise_excess_th", SPICE_ORACLE, "noise_excess_th"), ("noise_out_int_vrms", SPICE_ORACLE, "noise_out_int_vrms"),
)


def verified_by(metric):
    found = {name: (kind, measure) for name, kind, measure in _TABLE}
    if metric not in metric_registry():
        raise KeyError("verified_by: 레지스트리에 없는 metric %r" % (metric,))
    kind, measure = found[metric]
    return VerifiedBy(metric, kind, measure, MODEL_ERROR_PREFIX + metric)
