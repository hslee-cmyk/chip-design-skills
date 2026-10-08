"""선언된 제약이 쓰는 LUT 데이터의 존재 검사 (설계 41 §6.4-2b·§7.2, lut/CONTRACT.md 9.5).

진입점: `require_lut_data`.

잡음 제약(`noise_*` metric)이 선언됐는데 잡음 r1 데이터가 없으면 `noise_lut_missing`, offset 제약(`offset_*` metric)이 선언됐는데 mismatch 감도 r1 데이터가 없으면
`mismatch_lut_missing` 으로 로드 단계에서 거부한다(탐색 중 조회 실패로 늦게 알게 하지 않는다). 호출부는 spec 에서 제약 선언을 읽는 쪽(authoring·search 시작,
설계 40 §11 U5·U9)이다.
"""
from ._helpers_fail import schema_rejected


def require_lut_data(lut, kinds, *, noise=False, mismatch=False):
    """`kinds`(소자 kind 집합) 마다 `noise`/`mismatch` 가 True 인 데이터가 `lut` 에 있어야 한다. 없으면 `SchemaRejectedError`
    (`noise_lut_missing`·`mismatch_lut_missing`, detail `kinds` = 없는 kind 정렬 tuple). 둘 다 없으면 잡음 쪽을 먼저 거부한다."""
    for needed, table, reason in ((noise, lut.noise, "noise_lut_missing"), (mismatch, lut.mismatch, "mismatch_lut_missing")):
        missing = tuple(sorted(set(kinds) - set(table))) if needed else ()
        if missing:
            raise schema_rejected(reason, kinds=missing)
