"""블록 결과 이식 -- 원천 스냅샷의 한 블록 열을 대상 lineage 에 graph setter 로 쓴다 (설계 40 §2.4.4 API, 사용자 결정 X-1 (3)).

진입점: `graft(target, block, part, donor, input_version)`.

* `input_version` 은 호출 규칙이 target 위에서 이미 잰 그 입력 버전이다(투영을 다시 만들지 않는다).
* `part` 는 "*" 만 받는다(분할 도입 전). 아니면 `ValueError`.
* `donor.block_version(block.name) != input_version` 이면 `ValueError` -- 블록 호출 fail-closed (2) 의 유일한 검사 자리다.
* 쓰는 곳은 `GraphSnapshot.write` 뿐이다(새 쓰기 경로 없음, writer 권한 검사 그대로). 이식한 행의 값은 계산한 행과 같다
  (블록은 투영만의 순수 함수).
"""


def graft(target, block, part, donor, input_version):
    """donor 의 `block.writes` 열 전부를 target 에 `block.name`·`input_version` 으로 쓴 스냅샷."""
    if part != "*":
        raise ValueError("graft: 분할 도입 전에는 part 가 '*' 여야 한다: " + repr(part))
    if donor.block_version(block.name) != input_version:
        raise ValueError(
            "graft: 원천 스냅샷의 " + repr(block.name) + " 입력 버전이 요청과 다르다 (색인 손상) -- 원천 "
            + repr(donor.block_version(block.name)) + ", 요청 " + repr(input_version)
        )
    rows = {(kind, field): dict(donor.column(kind, field)) for kind, field in block.writes}
    return target.write(block.name, input_version, rows)
