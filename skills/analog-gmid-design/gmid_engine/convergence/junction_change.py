"""레이아웃 전·후 접합 용량 변화 (계획 DEC-91 (2), LY8, 설계 40 §3.9 U14 '재검증이 실현 확산 기하의 접합 용량을 쓴다').

진입점: `junction_change(before, after) -> tuple[JunctionChange]`.

`before`·`after` = `ss_dev` 필드가 든 스냅샷(레이아웃 전 front 점과 MOD8 재검증 점). 소자(이름순)마다 (cdb, csb) -- `ss_dev` 가 쓴 접합 용량(F, 소자 전체)
-- 의 전·후를 담는다. 전 = LUT 생성 규칙 확산 기하, 후 = MOD7 `ly.diffusion`.
"""
from .convergence_values import JunctionChange


def junction_change(before, after):
    old = dict(before.column("device", "ss_dev"))
    new = dict(after.column("device", "ss_dev"))
    return tuple(JunctionChange(m, old[m].cdb, old[m].csb, new[m].cdb, new[m].csb) for m in sorted(new) if m in old)
