# -*- coding: utf-8 -*-
"""`probe_lut_L_interpolation`(2026-09-08) 승격본 -- LUT의 L 보간이 gm/ID를 비물리적 값으로 만드는가.

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1 P3, spec card `20260923-probe-promote-clean`.

원본 probe는 gm/ID 곡선의 최대값을 **표로 찍기만** 했다. 그 표의 '판정' 열이 쓰던 기준을 assert로 옮긴다:

    gm/ID <= 1/(n V_T),  n >= 1  ->  gm/ID <= q/(k T)

약반전에서 gm/ID는 1/(nV_T)로 포화하고 그 위로 갈 수 없다(n = 1 + C_d/C_ox >= 1). 즉 `q/(kT)`는
어떤 소자·어떤 L에서도 넘을 수 없는 **물리 상한**이다. 원본 probe가 기록한 고장(PMOS 앵커 사이에서
403 / 5516 / 56646)은 이 한 줄에 걸린다.

**옮기지 않은 절**(spec card 계약 4, 판정을 세울 수 없다):
* "기전: ID는 로그보간, GM은 선형보간" 비교표 -- 대안 보간을 test 안에서 다시 만들어야 하고(V4 규칙 (2)),
  두 보간의 차이 자체에는 지켜야 할 값이 없다. 성질로서 남는 것은 위 물리 상한뿐이다.
* "실사이징 영향(VGS/W 환산)" 표와 "현재 저장된 파일럿 산출물은 오염돼 있지 않다" -- 그 시점의 진단이고
  지켜야 할 불변식이 아니다.

T = LUT npz가 스스로 선언한 `temp_c`에서 읽는다(숫자를 지어내지 않는다 -- WP-03).
"""
import math
import os
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _library_sized_contexts as lsc  # noqa: E402
import sizing_recipe as sr  # noqa: E402

# CODATA 2018(2019 SI 재정의) 정의값 -- 둘 다 정확값이다.
_BOLTZMANN_J_PER_K = 1.380649e-23
_ELEMENTARY_CHARGE_C = 1.602176634e-19
_ZERO_CELSIUS_K = 273.15


def thermal_gm_id_limit(temp_c):
    """1/V_T = q/(kT). n >= 1이므로 gm/ID = 1/(n V_T) <= 1/V_T 다."""
    return _ELEMENTARY_CHARGE_C / (_BOLTZMANN_J_PER_K * (float(temp_c) + _ZERO_CELSIUS_K))


def assert_gm_id_max_within_thermal_limit(samples, limit):
    """판정: 표본마다 gm/ID 최대값이 물리 상한 이하이고 유한·양수다.

    samples = [(설명, gm_id_max), ...]. 설명은 실패 메시지에만 쓴다.
    """
    over = [(label, value) for label, value in samples if not (0.0 < value <= limit)]
    assert not over, (
        "gm/ID 최대값이 물리 상한 %.3f(=q/kT)을 벗어난 표본 %d개: %s"
        % (limit, len(over), over[:5]))


def assert_L_range_inside_lut_anchor_span(label, bounds, anchors):
    """판정: 선언된 L 탐색 구간이 LUT L 앵커의 바깥으로 나가지 않는다(외삽 금지)."""
    lo_a, hi_a = float(min(anchors)), float(max(anchors))
    lo_b, hi_b = float(bounds[0]), float(bounds[1])
    assert lo_b <= hi_b, "%s: 탐색 구간이 뒤집혔다 %s" % (label, bounds)
    assert lo_a <= lo_b and hi_b <= hi_a, (
        "%s: L 탐색 구간 [%.4g, %.4g]m 이 LUT 앵커 [%.4g, %.4g]m 밖이다 -- 앵커 밖은 보간이 아니라 외삽이다"
        % (label, lo_b, hi_b, lo_a, hi_a))


def _search_grid(bounds, step):
    lo, hi = float(bounds[0]), float(bounds[1])
    n = int(round((hi - lo) / float(step)))
    grid = [lo + i * float(step) for i in range(max(n, 0) + 1)]
    grid[-1] = min(grid[-1], hi)
    return grid


def _kind_of(topo_json):
    return {dev["name"]: dev.get("kind") for dev in topo_json.get("netlist") or []}


def _median(values):
    ordered = sorted(float(v) for v in values)
    return ordered[len(ordered) // 2]


def _lut_temp_c(real_lut):
    with np.load(real_lut) as data:
        return float(data["temp_c"])


def test_gm_id_max_within_thermal_limit_on_declared_L_search_grid(real_lut):
    """선언된 L 탐색 격자(bounds + L_grid_step) 전체에서 gm/ID 최대값이 물리 상한 이하다.

    oracle 대조: (a) 물리 불변식 -- 약반전 gm/ID <= 1/(n V_T) <= q/(kT)이고, T는 LUT npz의 `temp_c`
    선언에서 읽는다. 기대값을 엔진 출력에서 만들지 않는다. 훑는 점은 원본 probe의 마지막 절이 지적한
    **실제 탐색 격자**(`metric_stage_budget` theta의 bounds를 spec의 `L_grid_step`으로)이고, 격자점
    대부분이 LUT 앵커 밖이라 이 test가 보는 것은 보간값이다.
    """
    limit = thermal_gm_id_limit(_lut_temp_c(real_lut))
    seen, samples = set(), []
    for key, (topo, spec) in sorted(lsc.declared_circuits().items()):
        kind_of = _kind_of(topo)
        vds = _median(spec["VDS_candidates"])
        for decl, devices in lsc.declared_L_search_thetas(topo):
            kinds = {kind_of.get(name) for name in devices} - {None}
            for kind in sorted(kinds):
                lut = (spec.get("lut_by_kind") or {}).get(kind)
                assert lut is not None, "%s/%s: %s LUT가 spec에 없다" % (key, decl["name"], kind)
                for L in _search_grid(decl["bounds"], spec["L_grid_step"]):
                    token = (kind, round(L, 15), round(vds, 12))
                    if token in seen:
                        continue
                    seen.add(token)
                    _vgs, gm_id = lut._gm_id_curve(L, vds, 0.0)
                    samples.append(("%s %s L=%.4gum vds=%.3f" % (key, kind, L * 1e6, vds),
                                    float(np.max(gm_id))))
    assert samples, "훑은 격자점이 없다 -- 선언에서 L 탐색 theta를 못 찾았다"
    assert_gm_id_max_within_thermal_limit(samples, limit)


def test_gm_id_max_within_thermal_limit_over_declared_vds_candidates(real_lut):
    """LUT 앵커 위에서 선언된 VDS 후보 전부에 대해 gm/ID 최대값이 물리 상한 이하다.

    oracle 대조: (a) 위와 같은 물리 불변식. 위 test가 L축(보간)을 훑는 대신 이 test는 **VDS축 전부**를
    훑는다(VDS_candidates는 spec 선언, vsb=0은 원본 probe의 측정 조건과 같다).
    """
    limit = thermal_gm_id_limit(_lut_temp_c(real_lut))
    # 회로들이 같은 LUT 객체를 공유하면 한 번만 훑는다(판정 대상은 LUT이지 회로가 아니다).
    seen, samples = set(), []
    for key, (_topo, spec) in sorted(lsc.declared_circuits().items()):
        for kind, lut in sorted((spec.get("lut_by_kind") or {}).items()):
            if (kind, id(lut)) in seen:
                continue
            seen.add((kind, id(lut)))
            for L in [float(v) for v in lut.L_grid]:
                for vds in [float(v) for v in spec["VDS_candidates"]]:
                    _vgs, gm_id = lut._gm_id_curve(L, vds, 0.0)
                    samples.append(("%s %s L=%.4gum vds=%.3f" % (key, kind, L * 1e6, vds),
                                    float(np.max(gm_id))))
    assert samples, "훑은 앵커가 없다"
    assert_gm_id_max_within_thermal_limit(samples, limit)


def test_declared_L_search_range_stays_inside_lut_anchor_span():
    """선언된 L 탐색 구간이 LUT L 앵커 구간 안에 있다.

    oracle 대조: (a) 구성 -- 다차원 보간은 격자 밖에서 정의되지 않는다(밖은 외삽이다). 원본 probe의
    마지막 절("격자점 대부분이 앵커 밖이다")이 전제하던 것, 즉 **격자점은 앵커 사이여야 한다**를 판정으로
    옮긴 것이다. 기대값(앵커 구간)은 LUT 파일의 L 격자 선언에서 읽는다.
    """
    checked = 0
    for key, (topo, spec) in sorted(lsc.declared_circuits().items()):
        kind_of = _kind_of(topo)
        for decl, devices in lsc.declared_L_search_thetas(topo):
            for kind in sorted({kind_of.get(name) for name in devices} - {None}):
                lut = (spec.get("lut_by_kind") or {}).get(kind)
                assert lut is not None, "%s/%s: %s LUT가 spec에 없다" % (key, decl["name"], kind)
                assert_L_range_inside_lut_anchor_span(
                    "%s/%s(%s)" % (key, decl["name"], kind), decl["bounds"], lut.L_grid)
                checked += 1
    assert checked, "L 탐색 theta 선언을 하나도 못 찾았다 -- 이 판정이 무동작이다"


def test_thermal_limit_rejects_unphysical_lut(real_lut):
    """합성 반례: GM만 부풀린 LUT는 물리 상한을 넘고, 판정이 실제로 거부한다.

    oracle 대조: (a) 구성으로 정답이 정해진 합성 입력 -- GM을 그대로 1000배 하면 gm/ID도 1000배가 되고
    (ID는 그대로), 원본 probe가 기록한 고장 모양(gm/ID 수백~수만)과 같은 자리에 온다. 정상 LUT가 상한
    아래라는 것은 위 test들이 따로 판정한다.
    """
    limit = thermal_gm_id_limit(_lut_temp_c(real_lut))
    # W_ref는 선언된 LUT에서 그대로 가져온다(반례가 바꾸는 것은 GM 하나뿐이어야 한다).
    declared = [spec for _topo, spec in lsc.declared_circuits().values()]
    reference = (declared[0].get("lut_by_kind") or {})["pmos"]
    with np.load(real_lut) as data:
        broken = sr.SemiEmpiricalGmIdLUT(
            data["L"], data["VGS"], data["VDS"], data["VS"], data["ID_p"],
            data["GM_p"] * 1.0e3, data["GDS_p"], data["CGG_p"], W_ref=reference.W_ref)
    L_mid = float(broken.L_grid[len(broken.L_grid) // 2])
    vds_mid = float(broken.VDS_grid[len(broken.VDS_grid) // 2])
    _vgs, gm_id = broken._gm_id_curve(L_mid, vds_mid, 0.0)
    worst = float(np.max(gm_id))
    assert worst > limit, "합성 반례가 상한을 넘지 못했다 -- 반례 구성 오류(GM x1000)"
    with pytest.raises(AssertionError):
        assert_gm_id_max_within_thermal_limit([("합성 반례(GM x1000)", worst)], limit)
    with pytest.raises(AssertionError):
        assert_gm_id_max_within_thermal_limit([("합성 반례(비물리 0 이하)", 0.0)], limit)
    assert math.isfinite(limit) and limit > 0.0
