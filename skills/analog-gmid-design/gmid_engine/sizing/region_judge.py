"""공용 영역 판정 -- 전류와 VDS 대 VDSAT 만으로 소자 영역을 가른다 (EO-1 범위 4, 설계 41 §4.8-1, 계획 O-202·O-204·O-205·O-210).

진입점: `judge_region(device, declared, current, vds, vdsat) -> RegionJudgment`. 값만 받는다 -- LUT 를 부르지 않고 I_off·tol 입력 칸이 없다.
`RegionJudgment(device, declared, actual)`: `declared` ∈ {None, "triode", "off"}, `actual` ∈ {saturation, triode, cutoff, out_of_domain, not_judged,
unresolved}. 어긋남 판정은 `region_mismatch.py`.

`vdsat` = 수, `OUT_OF_DOMAIN`(그 점 LUT 조회가 축·L 위치 밖), `None`(VDSAT 열 없음). 위에서 아래로 첫 맞는 행(수치 문턱 없음 -- current = 0 정확히가
꺼짐 경계, VDS = vdsat 정확히가 포화 경계):

| # | declared | current | VDS 대 vdsat | actual |
|---|---|---|---|---|
| 1 | off | 무관 | 무관 | not_judged |
| 2 | None·triode | ≤ 0 | 무관 | cutoff |
| 3 | None | > 0 | VDS < 0 (vdsat 값 안 봄) | triode |
| 4 | triode | > 0 | VDS < 0 | triode |
| 5 | None·triode | > 0 | OUT_OF_DOMAIN | out_of_domain |
| 6 | None·triode | > 0 | None | unresolved |
| 7 | None | > 0 | VDS ≥ vdsat | saturation |
| 8 | None | > 0 | VDS < vdsat | triode |
| 9 | triode | > 0 | VDS < vdsat | triode |
| 10 | triode | > 0 | VDS ≥ vdsat | saturation |
"""
import dataclasses

from gmid_engine.authoring import REGION_OFF, REGION_TRIODE

OUT_OF_DOMAIN = "out_of_domain"                    # vdsat 입력 값: 조회가 LUT 축·L 위치 밖 (문자열 상수)
DECLARED_OFF = REGION_OFF                          # 영역 어휘 정본 = authoring (sizing 은 낱말을 따로 정의하지 않는다)
DECLARED_TRIODE = REGION_TRIODE
ACTUAL_SATURATION = "saturation"
ACTUAL_TRIODE = "triode"
ACTUAL_CUTOFF = "cutoff"
ACTUAL_OUT_OF_DOMAIN = "out_of_domain"
ACTUAL_NOT_JUDGED = "not_judged"
ACTUAL_UNRESOLVED = "unresolved"


@dataclasses.dataclass(frozen=True)
class RegionJudgment:
    device: str
    declared: object
    actual: str


def judge_region(device, declared, current, vds, vdsat):
    if declared == DECLARED_OFF:
        return RegionJudgment(device, declared, ACTUAL_NOT_JUDGED)
    if current <= 0:
        return RegionJudgment(device, declared, ACTUAL_CUTOFF)
    if vds < 0:
        return RegionJudgment(device, declared, ACTUAL_TRIODE)
    if vdsat == OUT_OF_DOMAIN:
        return RegionJudgment(device, declared, ACTUAL_OUT_OF_DOMAIN)
    if vdsat is None:
        return RegionJudgment(device, declared, ACTUAL_UNRESOLVED)
    return RegionJudgment(device, declared, ACTUAL_SATURATION if vds >= vdsat else ACTUAL_TRIODE)
