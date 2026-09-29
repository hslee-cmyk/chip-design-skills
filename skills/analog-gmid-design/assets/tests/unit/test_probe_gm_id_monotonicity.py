# -*- coding: utf-8 -*-
"""`probe_gm_id_monotonicity`(2026-09-09, B20) 승격본 -- `_solve_vgs()`가 고른 VGS가 물리적으로 옳은 가지에 있는가.

TS6(계획 N3.11), design `20-dead-code-dup` v1.2 §5.1 P3(대조형 -- 재구현을 oracle로 유지),
spec card `20260923-probe-promote-differential`.

## 배경(원본 probe에서)

gm/ID 곡선은 VGS에 단조감소라는 전제가 PMOS LUT에서 깨진다(누설이 섞인 약반전 꼬리, 바디효과가 걸린 긴 L).
옛 `_solve_vgs()`는 `argsort`로 두 가지(branch)를 섞어 보간해 조용히 틀린 VGS(W 2.36배)를 냈다. B20 수정 뒤
원본 probe §4가 엔진과 독립 계산을 LUT 정의역 전체에서 대조하는 회귀 감시였다. 그 대조를 판정으로 옮긴다.

## 독립 쪽이 엔진 코드를 옮겨 적은 것이 아닌 근거(spec card 계약 3)

* 엔진(피검): `_solve_vgs(gm_id, L, vds, vsb)` -- interface card의 docstring대로 **목표를 품는 가장 오른쪽 구간**을
  격자 위에서 찾는 역탐색이다.
* 이 test의 독립 쪽: **강반전 가지**를 물리로 먼저 정의한다 -- 강반전에서 gm/ID는 VGS에 대해 줄어든다(제곱법칙
  gm/ID = 2/(VGS - VT)). 그래서 강반전 가지 = 곡선의 **가장 높은 VGS 끝에서 왼쪽으로, gm/ID가 계속 커지는 동안**
  이어지는 꼬리다(`strong_inversion_branch_start`). 그 꼬리는 구성상 단조라 역함수가 하나이고, `np.interp`로
  **꼬리 위에서만** 역보간한다(`strong_branch_vgs`). 선택 규칙이 다르다: 엔진은 구간을 오른쪽부터 훑어 부호가
  바뀌는 첫 구간을 고르고, 이 test는 가지를 먼저 잘라 그 가지 안에서 역함수를 쓴다.
* 원본 probe §4의 `rightmost_root`(오른쪽부터 부호 변화 구간을 찾는 재구현)는 **옮기지 않았다** -- 엔진의 선택
  규칙 자체를 다시 쓴 것이라 V4 규칙 (2)(피검 식 재서술)에 걸린다. 원본 §3의 `strong_branch_vgs`는 가지의 시작을
  **전역 최대**(`argmax`)로 잡았는데, 실측(이 LUT의 PMOS 1,350개 곡선)에서 전역 최대가 VGS=0의 약반전 꼬리에 있고
  강반전 쪽에 두 번째 정점이 있는 곡선이 있어 그 정의로는 가지가 단조가 아니다(역보간이 무의미해진다). 그래서
  가지를 위 물리 정의(높은 VGS 끝의 단조감소 꼬리)로 다시 세웠다(design §5.1 '다른 계산 경로로 다시 세운다').

## 판정(계약 4 -- 두 값이 같다는 것만으로 끝내지 않는다)

1. 강반전 가지가 목표를 품으면 엔진 해는 **그 가지 위**(VGS >= 가지 시작)에 있고, 그 VGS에서 곡선을 **정방향으로**
   읽은 gm/ID가 목표와 같으며(역탐색의 결과를 정방향 평가로 확인), 독립 역보간 해와의 차이가 반올림 오차 이내다.
2. 가지가 목표를 품지 못하면(목표가 강반전 정점보다 높거나 꼬리 끝보다 낮다) 엔진이 값을 낼 때 그 값은 근이고,
   **그보다 높은 VGS의 어떤 격자점도 목표에 닿지 않는다**(interface card '가장 큰 VGS 해'의 뜻 -- 구간 탐색이
   아니라 정방향 부호 검사로 본다). 엔진이 거부(`ValueError`)하면 곡선 전체가 목표에 닿지 않아야 한다(근이
   있는데 거부하지 않는다).
3. 합성 곡선으로 두 판정이 약반전 가지 해·더 낮은 근·근이 있는데 거부를 **실제로 거부**하는지 본다.

훑는 정의역: 하네스가 선언한 회로들의 `lut_by_kind` LUT(같은 객체는 한 번) x LUT의 L 앵커 x spec이 선언한
`VDS_candidates` x LUT의 VS 격자 x spec이 선언한 `gm_id_grid`(엔진이 실제로 고르는 목표) -- 숫자를 박지 않는다.

## 옮기지 않은 절(계약 5 -- 판정을 세울 수 없다)

* §1 / §1b(정의역에서 비단조 동작점 비율, vsb/L별 분포): 수정 근거를 남긴 **측정**이다. LUT의 성질을 기록한 것이지
  엔진이 지켜야 할 값이 아니다(비율이 얼마여야 한다는 기준이 없다).
* §2 / §3(파일럿 소자가 이중값 대역에 걸리는가, W가 몇 배 틀리는가): `probe_mirror_design_space`의 사이징 캐시가
  있어야 도는 이력 재현이고, 원본 docstring이 "수정 후에는 정의상 0건"이라 적었다. 그 성질은 위 판정 1·2가 정의역
  전체에서 이미 본다.
"""
import os
import sys

import numpy as np
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import _library_sized_contexts as lsc  # noqa: E402

# 부동소수 반올림 허용(상대값). float64 기계 엡실론의 1e3배 -- 선형 보간 한 번의 반올림(수 ulp)보다 넉넉하고,
# LUT 격자 한 칸(VGS 37.5 mV, gm/ID 수 단위)보다 10자리 이상 작다. 물리 허용오차가 아니라 계산 동일성의 문턱이다.
_ROUNDOFF = 1.0e3 * np.finfo(float).eps


# --------------------------------------------------------------------------------------
# 독립 쪽: 강반전 가지(물리 정의)와 그 위의 역보간
# --------------------------------------------------------------------------------------
def strong_inversion_branch_start(g):
    """강반전 가지의 시작 인덱스: 가장 높은 VGS 끝에서 왼쪽으로 gm/ID가 **엄격히 커지는** 동안 이어지는 꼬리.

    강반전에서 gm/ID는 VGS에 대해 줄어든다(제곱법칙). 그래서 오른쪽 끝에서 거꾸로 올라가며 gm/ID가 더 이상
    커지지 않는 첫 점에서 멈춘다. 반환 인덱스 이후의 곡선은 구성상 엄격한 단조감소다.
    """
    i = len(g) - 1
    while i > 0 and g[i - 1] > g[i]:
        i -= 1
    return i


def strong_branch_vgs(vg, g, gm_id):
    """강반전 가지 위에서 gm_id를 만드는 VGS(가지가 목표를 품지 않으면 None)."""
    i0 = strong_inversion_branch_start(g)
    gg, vv = g[i0:], vg[i0:]
    if not (gg[-1] <= gm_id <= gg[0]):
        return None
    # 가지가 단조감소이므로 뒤집으면 np.interp가 요구하는 단조증가 xp가 된다(역함수가 하나다).
    return float(np.interp(gm_id, gg[::-1], vv[::-1]))


def _vgs_tol(vg):
    return _ROUNDOFF * float(vg[-1] - vg[0])


def _gm_id_tol(g):
    return _ROUNDOFF * max(1.0, float(np.max(np.abs(g))))


# --------------------------------------------------------------------------------------
# 판정 보조(이름이 assert로 시작한다 -- V4 (4))
# --------------------------------------------------------------------------------------
def assert_vgs_on_strong_branch(label, vg, g, gm_id, v_engine, v_independent):
    """판정 1: 엔진 해가 강반전 가지 위에 있고, 정방향으로 읽으면 목표이며, 독립 역보간 해와 같다."""
    assert v_independent is not None, "%s: 판정 1의 전제 위반 -- 가지가 목표를 품지 않는다" % label
    assert v_engine is not None, "%s: 강반전 가지가 목표 %.3f를 품는데 엔진이 거부했다" % (label, gm_id)
    v_start = float(vg[strong_inversion_branch_start(g)])
    assert v_engine >= v_start - _vgs_tol(vg), (
        "%s: 엔진 VGS %.6f가 강반전 가지 시작 %.6f보다 낮다 -- 약반전 쪽 가지의 해다" % (label, v_engine, v_start))
    forward = float(np.interp(v_engine, vg, g))
    assert abs(forward - gm_id) <= _gm_id_tol(g), (
        "%s: 엔진 VGS %.6f에서 곡선을 읽으면 gm/ID %.6f -- 목표 %.6f가 아니다" % (label, v_engine, forward, gm_id))
    assert abs(v_engine - v_independent) <= _vgs_tol(vg), (
        "%s: 엔진 VGS %.9f != 강반전 가지 역보간 %.9f" % (label, v_engine, v_independent))


def assert_no_higher_vgs_reaches_target(label, vg, g, gm_id, v_engine):
    """판정 2(값을 낸 경우): 엔진 해가 근이고, 그보다 높은 VGS의 격자점은 모두 목표의 한쪽에만 있다."""
    forward = float(np.interp(v_engine, vg, g))
    assert abs(forward - gm_id) <= _gm_id_tol(g), (
        "%s: 엔진 VGS %.6f에서 곡선을 읽으면 gm/ID %.6f -- 목표 %.6f의 근이 아니다" % (label, v_engine, forward, gm_id))
    right = g[vg > v_engine + _vgs_tol(vg)]
    same_side = bool(np.all(right < gm_id)) or bool(np.all(right > gm_id))
    assert same_side, (
        "%s: 엔진 VGS %.6f보다 높은 VGS에 목표 %.3f에 닿는 점이 있다 -- 가장 큰 VGS 해가 아니다"
        % (label, v_engine, gm_id))


def assert_refusal_means_unreachable(label, g, gm_id):
    """판정 2(거부한 경우): 곡선 전체가 목표에 닿지 않는다(근이 있는데 거부하지 않는다)."""
    assert gm_id > float(np.max(g)) or gm_id < float(np.min(g)), (
        "%s: 곡선 범위 [%.3f, %.3f]가 목표 %.3f를 품는데 엔진이 거부했다"
        % (label, float(np.min(g)), float(np.max(g)), gm_id))


# --------------------------------------------------------------------------------------
# 정의역(입력 구성 -- 선언에서 읽는다)
# --------------------------------------------------------------------------------------
_DOMAIN_CACHE = []


def _declared_domain():
    """(LUT 목록, VDS 후보, gm_id 목표) -- 하네스가 선언한 회로들의 spec에서 읽고 한 번만 만든다."""
    if not _DOMAIN_CACHE:
        luts, seen, vds, targets = [], set(), set(), set()
        for key, (_topo, spec) in sorted(lsc.declared_circuits().items()):
            vds.update(float(v) for v in spec["VDS_candidates"])
            targets.update(float(v) for v in spec["gm_id_grid"])
            for kind, lut in sorted((spec.get("lut_by_kind") or {}).items()):
                if (kind, id(lut)) in seen:
                    continue
                seen.add((kind, id(lut)))
                luts.append((kind, lut))
        _DOMAIN_CACHE.append((luts, sorted(vds), sorted(targets)))
    return _DOMAIN_CACHE[0]


def _engine_vgs(lut, gm_id, L, vds, vsb):
    """피검 호출. 명시적 거부(ValueError)는 None으로 돌려준다 -- 다른 예외는 그대로 올린다."""
    try:
        return float(lut._solve_vgs(gm_id, L, vds, vsb))
    except ValueError:
        return None


def _sweep():
    """정의역의 곡선마다 (라벨, VGS 격자, gm/ID 곡선, LUT, L, vds, vsb)."""
    luts, vds_list, _targets = _declared_domain()
    for kind, lut in luts:
        vg = np.asarray(lut.VGS_grid, dtype=float)
        for L in [float(v) for v in lut.L_grid]:
            for vds in vds_list:
                for vsb in [float(v) for v in lut.VS_grid]:
                    _id, g = lut._gm_id_curve(L, vds, vsb)
                    g = np.asarray(g, dtype=float)
                    assert g.shape == vg.shape and np.all(np.isfinite(g)), (
                        "%s L=%.4g vds=%.3f vsb=%.3f: gm/ID 곡선이 VGS 격자와 맞지 않거나 유한하지 않다"
                        % (kind, L, vds, vsb))
                    yield ("%s L=%.4gum vds=%.4f vsb=%.3f" % (kind, L * 1e6, vds, vsb), vg, g, lut, L, vds, vsb)


# --------------------------------------------------------------------------------------
# 판정 1: 강반전 가지가 목표를 품으면 엔진 해는 그 가지 위에 있다
# --------------------------------------------------------------------------------------
def test_solve_vgs_lands_on_strong_inversion_branch():
    """oracle 대조: (b) 다른 방법의 독립 계산 -- 강반전 가지를 물리(제곱법칙의 단조감소)로 먼저 정의하고 그 가지
    위에서만 역보간한 VGS(`strong_branch_vgs`), 그리고 엔진 해에서 곡선을 정방향으로 읽은 gm/ID. 엔진 출력을
    기대값으로 쓰지 않는다. 비단조 곡선(전역 최대가 강반전 가지 밖 -- B20이 물던 곳)이 판정에 실제로 들어왔는지도
    센다(공허한 통과 방지).
    """
    _luts, _vds, targets = _declared_domain()
    judged = judged_on_non_monotone = 0
    for label, vg, g, lut, L, vds, vsb in _sweep():
        non_monotone = strong_inversion_branch_start(g) != 0
        for gm_id in targets:
            v_ind = strong_branch_vgs(vg, g, gm_id)
            if v_ind is None:
                continue                      # 판정 2의 대상(아래 test)
            v_eng = _engine_vgs(lut, gm_id, L, vds, vsb)
            assert_vgs_on_strong_branch("%s gm_id=%.2f" % (label, gm_id), vg, g, gm_id, v_eng, v_ind)
            judged += 1
            judged_on_non_monotone += int(non_monotone)
    assert judged > 0, "강반전 가지가 목표를 품는 점이 하나도 없다 -- 판정 1이 무동작이다"
    assert judged_on_non_monotone > 0, (
        "비단조 곡선(약반전 쪽 가지가 있는 곡선)에서 판정한 점이 없다 -- B20이 물던 경우를 보지 않는다")


# --------------------------------------------------------------------------------------
# 판정 2: 가지가 목표를 품지 못하면 가장 높은 VGS의 근이거나, 근이 없어서 거부한다
# --------------------------------------------------------------------------------------
def test_solve_vgs_outside_strong_branch_takes_highest_root_or_refuses_unreachable():
    """oracle 대조: (b) 정방향 평가 -- 엔진 해에서 곡선을 읽어 근인지, 그보다 높은 VGS의 격자점이 모두 목표의 한쪽에
    있는지(= 더 높은 근이 없다)를 곡선 값으로 직접 본다. 거부는 곡선의 최소·최대가 목표를 품지 않을 때만 옳다.
    기대값은 LUT 곡선 자체이고 엔진의 구간 탐색을 다시 쓰지 않는다. 값을 낸 경우와 거부한 경우가 둘 다 실제로
    판정에 들어왔는지 센다.
    """
    _luts, _vds, targets = _declared_domain()
    answered = refused = 0
    for label, vg, g, lut, L, vds, vsb in _sweep():
        for gm_id in targets:
            if strong_branch_vgs(vg, g, gm_id) is not None:
                continue                      # 판정 1의 대상(위 test)
            case = "%s gm_id=%.2f" % (label, gm_id)
            v_eng = _engine_vgs(lut, gm_id, L, vds, vsb)
            if v_eng is None:
                assert_refusal_means_unreachable(case, g, gm_id)
                refused += 1
            else:
                assert_no_higher_vgs_reaches_target(case, vg, g, gm_id, v_eng)
                assert v_eng < float(vg[strong_inversion_branch_start(g)]) + _vgs_tol(vg), (
                    "%s: 가지가 목표를 품지 않는데 엔진 해 %.6f가 가지 위에 있다" % (case, v_eng))
                answered += 1
    assert answered > 0, "가지 밖 목표에 엔진이 값을 낸 점이 없다 -- 판정 2(값)가 무동작이다"
    assert refused > 0, "가지 밖 목표를 엔진이 거부한 점이 없다 -- 판정 2(거부)가 무동작이다"


# --------------------------------------------------------------------------------------
# 합성 반례: 판정이 실제로 거부한다(구성으로 정답이 정해진 곡선)
# --------------------------------------------------------------------------------------
# VGS 0.0 ~ 1.0 V, 0.2 V 간격. gm/ID: 약반전 쪽에서 오르다(10 -> 30) 강반전에서 내린다(30 -> 5).
# 강반전 가지 = 인덱스 2(VGS 0.4)부터. 목표 15의 근은 둘: 약반전 쪽 0.1 V(10->20 구간의 가운데),
# 강반전 쪽 0.8 V(격자점, gm/ID가 정확히 15).
_SYN_VG = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
_SYN_G = np.array([10.0, 20.0, 30.0, 25.0, 15.0, 5.0])


def test_strong_branch_definition_on_synthetic_curve():
    """oracle 대조: (a) 구성 -- 곡선을 손으로 정했으므로 가지 시작(인덱스 2)과 목표 15의 강반전 해(VGS 0.8, 격자점
    위의 값)가 구성으로 정해진다. 가지가 목표를 품지 않는 경우(목표 35 > 정점 30, 목표 2 < 끝값 5)는 None이다.
    """
    assert strong_inversion_branch_start(_SYN_G) == 2
    assert strong_branch_vgs(_SYN_VG, _SYN_G, 15.0) == pytest.approx(0.8, abs=1e-15)
    assert strong_branch_vgs(_SYN_VG, _SYN_G, 35.0) is None
    assert strong_branch_vgs(_SYN_VG, _SYN_G, 2.0) is None
    # 단조감소 곡선이면 가지는 곡선 전체다.
    assert strong_inversion_branch_start(np.array([30.0, 20.0, 10.0])) == 0


def test_strong_branch_judgment_rejects_weak_branch_root():
    """oracle 대조: (a) 합성 입력 -- 목표 15의 약반전 쪽 근은 0.1 V(10->20 구간의 한가운데, 구성으로 정해진다).
    그 근을 엔진 해로 준 경우와, 가지 위지만 근이 아닌 값(0.6 V -> gm/ID 25), 가지 해와 다른 값을 판정이
    **거부**한다. 옳은 해(0.8 V)는 통과한다.
    """
    v_ind = strong_branch_vgs(_SYN_VG, _SYN_G, 15.0)
    assert_vgs_on_strong_branch("합성 정상", _SYN_VG, _SYN_G, 15.0, 0.8, v_ind)
    with pytest.raises(AssertionError):
        assert_vgs_on_strong_branch("합성 약반전 해", _SYN_VG, _SYN_G, 15.0, 0.1, v_ind)
    with pytest.raises(AssertionError):
        assert_vgs_on_strong_branch("합성 근 아님", _SYN_VG, _SYN_G, 15.0, 0.6, v_ind)
    with pytest.raises(AssertionError):
        assert_vgs_on_strong_branch("합성 거부", _SYN_VG, _SYN_G, 15.0, None, v_ind)
    with pytest.raises(AssertionError):
        assert_vgs_on_strong_branch("합성 다른 해", _SYN_VG, _SYN_G, 15.0, 0.8, 0.7)


def test_highest_root_judgment_rejects_lower_root_and_wrong_refusal():
    """oracle 대조: (a) 합성 입력 -- 곡선 [10, 20, 30, 10, 12, 8](VGS 0.0 ~ 1.0 V, 0.2 V 간격)의 강반전 가지는
    인덱스 4(12 -> 8)라 목표 15를 품지 않는다. 목표 15의 근은 둘: 0.1 V(10->20)와 0.55 V(30->10 구간의 3/4).
    낮은 근 0.1 V는 더 높은 VGS(0.2 V: 20)가 목표를 넘으므로 판정이 **거부**하고, 높은 근 0.55 V는 통과한다.
    곡선이 목표를 품는데(15 in [8, 30]) 거부한 경우도 **거부**하고, 품지 않는 목표(40)의 거부는 통과한다.
    """
    vg = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    g = np.array([10.0, 20.0, 30.0, 10.0, 12.0, 8.0])
    assert strong_inversion_branch_start(g) == 4
    assert strong_branch_vgs(vg, g, 15.0) is None
    assert_no_higher_vgs_reaches_target("합성 높은 근", vg, g, 15.0, 0.55)
    with pytest.raises(AssertionError):
        assert_no_higher_vgs_reaches_target("합성 낮은 근", vg, g, 15.0, 0.1)
    with pytest.raises(AssertionError):
        assert_no_higher_vgs_reaches_target("합성 근 아님", vg, g, 15.0, 0.9)
    assert_refusal_means_unreachable("합성 닿지 않는 목표", g, 40.0)
    with pytest.raises(AssertionError):
        assert_refusal_means_unreachable("합성 근이 있는데 거부", g, 15.0)
