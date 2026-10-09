"""구조 가드 공용 helper -- offset 가드(41 §6.4-2a)와 열잡음 가드(41 §7.5)가 같은 모양이다 (`iv_matching_l`·`iv_noise` 가 함께 쓴다).

* `guard_devices(ctx) -> (입력 소자 이름 tuple, 부하 소자 이름 tuple)`: gain 제약 전달 뷰의 **첫 이득 블록**(가장 앞 stage)에서 구조 역할로 정한다 -- 입력 = AC 역할 input,
  부하 = 역할 mirror·diode_load·load 인 MOS. 캐스코드(이득으로 감쇠)·꼬리(공통모드)는 입력 환산 기여가 아니라 뺀다(41 §6.4-2a, §7.5, 이름 아님 구조).
* `guard_bounds(ctx, inputs, loads, term, ratio, lengths, gm_id_lo, g_in, source) -> (bounds, conflicts)`: 부하 합 가드 `Σ_loads term_k(gm/ID_k) ≤ ratio · Σ_inputs term_in(g_in)` 를 소자별 gm/ID 상한으로 바꾼다.
  `term(소자 이름, gm/ID)` = 그 소자의 기여(호출부가 만든다: 열잡음은 B·gm², offset 은 (gm·σ_VGS)²). 41 §6.2 와 같은 '나머지는 최소(gm/ID 하한)로 두고 k 가 가질 수 있는 최대' 규약:
  level_k = ratio · Σ term_in − Σ_{j≠k} term_j(gm/ID_lo,j), 그리고 term_k(g) ≤ level_k 인 g 의 최댓값(곡선 마디 전수 + 선형 교차, 비단조 대응)을 상한으로 낸다.
  level_k ≤ 0 이거나 어느 g 도 만족하지 못하면 자르지 않고 충돌 레코드(41 §6.6)로 남긴다.
"""
from ._helpers_curves import hull
from .iv_curves import QUANTITY_FT
from .start_values import QUANTITY_GM_ID, SIDE_HI, Bound, StartConflict

_BLOCK_KINDS = ("gain", "composite")
_ROLE_INPUT = "input"
_ROLES_LOAD = ("mirror", "diode_load", "load")


def guard_devices(ctx):
    if ctx.transfer is None:
        return (), ()
    blocks = [b for b in ctx.transfer.blocks if b.kind in _BLOCK_KINDS]
    if not blocks:
        return (), ()
    first = min(blocks, key=lambda b: b.stage)
    ordered = sorted((n for n, _r in first.roles if n in ctx.by_name), key=lambda n: (ctx.by_name[n].colour, n))
    roles = dict(first.roles)
    return (tuple(n for n in ordered if roles[n] == _ROLE_INPUT), tuple(n for n in ordered if roles[n] in _ROLES_LOAD))


def guard_bounds(ctx, inputs, loads, term, ratio, lengths, gm_id_lo, g_in, source):
    base = ratio * sum(term(n, g_in) for n in inputs)
    low = {n: term(n, gm_id_lo[n]) for n in loads}
    bounds, conflicts = {}, []
    for name in loads:
        level = base - (sum(low.values()) - low[name])
        d = ctx.by_name[name]
        bundle = ctx.curves.bundle_of(d.name, d.kind, lengths[name])
        nodes = bundle[QUANTITY_FT].gm_id
        values = [term(name, float(g)) for g in nodes]
        found = hull(nodes, values, level, below=True) if level > 0 else None
        if found is None:
            conflicts.append(StartConflict(name, QUANTITY_GM_ID, ((source, level),), float(min(values)) - level))
        else:
            bounds[name] = (Bound(QUANTITY_GM_ID, SIDE_HI, source, found[1]),)
    return bounds, tuple(conflicts)
