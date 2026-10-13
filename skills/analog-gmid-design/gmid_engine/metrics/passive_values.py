"""GB5 수동소자 값 계산 블록 -- 설계점의 수동소자 값 정본 하나 (DEC-92, J7, 설계 40 §2.4.7·§2.4.8 `device.passive_value`, §3.5).

진입점: `passive_values`(`@compute_block`) -- `passive_values(snapshot, element_values, zero_cancel, theta_passive_pairs(theta))`.

* reads `device.element_class`, `device.dc_gm`(dc 단계 `dc_tolerances` 가 쓴 자기 동작점 gm -- 봉인 전에도 정의된다).
  writes `device.passive_value` = {수동소자: 값} -- 값이 정해진 수동소자만 행이 있다(어느 출처에도 없는 소자 = 결정 대기 등은 행 없음).
* extras: `element_values` = spec 선언((원소, 값 또는 None), ... -- sizing `DcInputs.element_values`, 수동소자 행만 쓴다),
  `zero_cancel` = θ 스키마의 영점 상쇄 판정(sizing `ZeroCancel` tuple), `theta` = θ 쌍 ((kind, key), 값) 중 이 블록이 읽는 수동소자 성분만
  -- 호출부는 `theta_passive_pairs(θ)` 로 골라 넘긴다(설계 40 §2.4.1 'FD 스텝은 그 성분을 읽는 블록만 계산', WP-23 (5): extras 가 투영
  지문에 들어가므로 MOS θ 만 바뀐 스텝에서는 입력 버전이 같아 재사용된다). 고르는 규칙은 `theta_passive_pairs` 하나뿐이고 블록도 같은
  함수로 고른다(전부를 넘겨도 값은 같다 -- 재사용만 잃는다).
* 값의 출처 셋: spec 선언 ∪ θ 저항·커패시터·ss 저항(sizing `THETA_RESISTANCE` + `THETA_PASSIVE_KINDS`) ∪ 영점 상쇄 구조 규칙 저항
  (`zero_cancel` 중 reason None: R = 1/Σ_{c∈S} `dc_gm`_c). 같은 소자에 둘 이상이면 `ValueError`, θ 이름이 S1 수동소자가 아니면 `ValueError`
  (스키마가 S1 에서 나오므로 계약 위반 표지).
* 소비자는 이 필드를 읽는다: `metrics_ss`·`metrics_aux`(소신호 회로)·`metrics_dc`(DC 저항·면적), MOD8 `convergence`(판정 축 면적 입력),
  오라클 입력(U16). 같은 입력이면 블록 재사용(필드가 곧 캐시) -- 값을 다시 만들지 않는다.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.sizing import PASSIVE_VALUES_WRITER, THETA_PASSIVE_KINDS, THETA_RESISTANCE

READS = (("device", "element_class"), ("device", "dc_gm"))
WRITES = (("device", "passive_value"),)
_THETA_PASSIVES = (THETA_RESISTANCE,) + THETA_PASSIVE_KINDS


def theta_passive_pairs(theta):
    """θ 쌍 ((kind, key), 값) 중 수동소자 성분(θ 저항·커패시터·ss 저항)만, 원래 순서로 -- `passive_values` extras 의 θ 칸."""
    return tuple(pair for pair in theta if pair[0][0] in _THETA_PASSIVES)


@compute_block(PASSIVE_VALUES_WRITER, reads=READS, writes=WRITES)
def passive_values(projection):
    element_values, zero_cancel, theta = projection.extras
    passives = {n for n, c in projection.column("device", "element_class") if c == ELEMENT_PASSIVE}
    values = {n: float(v) for n, v in element_values if n in passives and v is not None}
    gm = dict(projection.column("device", "dc_gm"))
    structural = tuple((z.resistor, 1.0 / sum(gm[c] for c in z.cells)) for z in zero_cancel if z.reason is None)
    sources = (tuple((key, v) for (_kind, key), v in theta_passive_pairs(theta)), structural)
    for pairs in sources:
        for name, value in pairs:
            if name not in passives:
                raise ValueError("passive_values: %r 은 S1 수동소자가 아니다" % (name,))
            if name in values:
                raise ValueError("passive_values: 수동소자 %r 의 값이 두 곳에서 온다(spec·θ·구조 규칙 중 하나만)" % (name,))
            values[name] = float(value)
    return {("device", "passive_value"): values}
