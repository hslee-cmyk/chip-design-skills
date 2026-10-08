"""미러 전류비 랜덤 오차 σ(ΔI/I) 보고 (설계 40 §3.8-8 `mirror_ratio_sigma_pct`, 체크리스트 D-MR, 옛 `mismatch_sigma_v` 대체).

진입점: `mirror_ratio(groups, roles, gm_id, sigmas) -> MirrorRatio`.

* 대상 = S1 matching 그룹 중 mirror 계열(`groups` = ((kind 문자열, 멤버 이름 tuple), ...) -- 호출자가 `graph.matching_groups` 의 mirror 그룹과
  `matching_dispositions` 의 bias_distribution 을 이 형식으로 준다). 계산 대상은 소자 쌍이다: 같은 그룹에 DC 역할이 기준 diode(`roles` 값
  `diode_reference` 로 시작)인 멤버가 있으면 (기준, 나머지 멤버) 쌍, 없으면 멤버 전쌍.
* 쌍 (a, b) 의 전류비 오차: 같은 VGS 에서 전류는 ΔI/I = (gm/ID)·ΔVGS 이므로 독립 게이트 오차 σ_VGS,a·σ_VGS,b(U3 `mismatch_sigma_vgs`)에서
  σ(ΔI/I) = √((gm/ID_a·σ_a)² + (gm/ID_b·σ_b)²) (두 소자 gm/ID 가 같으면 설계 40 §3.8-8 의 (gm/ID)·√2·σ 와 같다 -- 같지 않을 때 일반형).
* metric 값 = 모든 그룹·쌍의 최댓값 [pct], `groups` = 그룹마다 (kind, 멤버, 기준 소자들, 최대 σ pct) 표 -- 보고.
* 분해능: 최댓값 쌍에서 σ_a, σ_b 를 각각 +tol_mismatch 로 흔든 변화의 합. 허용오차가 없으면 None.
* 정의 불가: 대상 그룹 없음(`no_mirror_group`), σ·gm/ID 없는 소자(`sigma_missing`).
"""
import itertools
import math

from gmid_engine.core import PCT_PER_UNIT
from gmid_engine.graph import ROLE_DIODE

from .aux_types import MirrorRatio
from .mna_types import Undefined

QUANTITY = "sigma_pct"
PAIR = 1 + 1                                    # 쌍 = 소자 둘


def _pair(gmid_a, sigma_a, gmid_b, sigma_b):
    return math.hypot(gmid_a * sigma_a, gmid_b * sigma_b)


def _bare(code, detail=()):
    return MirrorRatio(None, undefined=(Undefined(QUANTITY, code, "definitional", detail),))


def mirror_ratio(groups, roles, gm_id, sigmas):
    sigma_of = {d: (s, t) for d, s, t in sigmas}
    role_of = dict(roles)
    gmid_of = dict(gm_id)
    rows = []
    for kind, members in groups:
        absent = tuple(m for m in members if m not in sigma_of or m not in gmid_of)
        if absent:
            return _bare("sigma_missing", (("devices", absent),))
        refs = tuple(m for m in members if role_of.get(m) == ROLE_DIODE)
        pairs = tuple((r, m) for r in refs for m in members if m not in refs) if refs and len(refs) < len(members) \
            else tuple(itertools.combinations(members, PAIR))
        values = tuple((_pair(gmid_of[a], sigma_of[a][0], gmid_of[b], sigma_of[b][0]), a, b) for a, b in pairs)
        if values:
            top = max(values)
            rows.append((kind, tuple(members), refs, top))
    if not rows:
        return _bare("no_mirror_group")
    table = tuple((kind, members, refs, top[0] * PCT_PER_UNIT) for kind, members, refs, top in rows)
    worst = max(rows, key=lambda r: r[3][0])
    value, a, b = worst[3]
    resolution = None
    tol_a, tol_b = sigma_of[a][1], sigma_of[b][1]
    if tol_a is not None and tol_b is not None:
        step = (abs(_pair(gmid_of[a], sigma_of[a][0] + tol_a, gmid_of[b], sigma_of[b][0]) - value)
                + abs(_pair(gmid_of[a], sigma_of[a][0], gmid_of[b], sigma_of[b][0] + tol_b) - value))
        resolution = step * PCT_PER_UNIT
    return MirrorRatio(value * PCT_PER_UNIT, table, resolution)
