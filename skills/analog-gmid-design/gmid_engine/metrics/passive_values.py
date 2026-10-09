"""봉인 점의 수동소자 값 -- 값의 정본 하나 (DEC-92, 설계 40 §3.9 U14: 판정 축 면적의 수동소자 블록도 같은 값을 쓴다).

진입점: `passive_values(snapshot, ctx, theta) -> ((수동소자, 값), ...)` 이름순.

`snapshot` = `ss_dev` 필드가 있는 봉인 스냅샷(영점 상쇄 구조 규칙 저항 1/Σgm 이 `ss_dev` gm 에서 나온다), `ctx` = 그 점의 `KernelContext`, `theta` = `Theta`.
값의 출처 셋: spec 선언(`ctx.inputs.element_values`, 수동소자만) ∪ θ 저항·커패시터·ss 저항(sizing `THETA_PASSIVE_KINDS`) ∪ 영점 상쇄 구조 규칙 저항
(`ctx.schema.zero_cancel` 중 reason None). 같은 소자에 둘 이상이면 `ValueError`, θ 이름이 S1 수동소자가 아니면 `ValueError`(스키마가 S1 에서 나오므로
계약 위반 표지). 어느 출처에도 없는 수동소자(결정 대기 등)는 결과에 없다. `ss_evaluate` 와 MOD8 `convergence` 의 `LayoutInput.passives` 가 이 함수를 쓴다.
"""
from gmid_engine.graph import ELEMENT_PASSIVE
from gmid_engine.sizing import THETA_PASSIVE_KINDS, THETA_RESISTANCE

_THETA_PASSIVES = (THETA_RESISTANCE,) + THETA_PASSIVE_KINDS


def passive_values(snapshot, ctx, theta):
    classes = dict(snapshot.column("device", "element_class"))
    passives = {n for n, c in classes.items() if c == ELEMENT_PASSIVE}
    values = {n: v for n, v in ctx.inputs.element_values if n in passives and v is not None}
    gm = {n: dev.gm for n, dev in snapshot.column("device", "ss_dev")}
    structural = tuple((z.resistor, 1.0 / sum(gm[c] for c in z.cells))
                       for z in ctx.schema.zero_cancel if z.reason is None)
    sources = (tuple((key, v) for (kind, key), v in theta.values if kind in _THETA_PASSIVES), structural)
    for pairs in sources:
        for name, value in pairs:
            if name not in passives:
                raise ValueError("ss_evaluate: %r 은 S1 수동소자가 아니다" % (name,))
            if name in values:
                raise ValueError("ss_evaluate: 수동소자 %r 의 값이 두 곳에서 온다(spec·θ·구조 규칙 중 하나만)" % (name,))
            values[name] = float(value)
    return tuple(sorted(values.items()))
