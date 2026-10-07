"""실패 레코드 -- N3.14 의 모든 실패(예외의 `.record`, 후보 실패 레코드)가 쓰는 한 형식 (설계 00-common §7.1).

진입점: `FailureRecord`.
"""
import dataclasses
from collections.abc import Mapping

from .determinism import sorted_items
from .immutability import require_immutable


@dataclasses.dataclass(frozen=True)
class FailureRecord:
    """{class, devices, margin, detail} -- 불변이고 fp_of·require_immutable 를 통과한다(실패 캐시 값으로 쓴다).

    * `failure_class`: 비어 있지 않은 문자열(N3.14 분류 키 또는 후보 실패 class 키).
    * `devices`: 소자 이름의 정렬된 tuple(입력 순서·중복과 무관하게 정렬·중복 제거).
    * `margin`: None 또는 float(N3.14 정규화식 결과, `normalized_margin` 이 만든다). int 는 float 로 바꾼다.
    * `detail`: 문자열 키 -> 불변 값. Mapping 또는 (키, 값) 쌍 iterable 로 받아 키 정렬 tuple 로 저장한다.
    """

    failure_class: str
    devices: tuple = ()
    margin: object = None
    detail: tuple = ()

    def __post_init__(self):
        if not isinstance(self.failure_class, str) or not self.failure_class:
            raise ValueError("FailureRecord.failure_class 는 비어 있지 않은 문자열이어야 한다")
        if isinstance(self.devices, str):
            raise TypeError("FailureRecord.devices 는 문자열이 아니라 소자 이름의 모음이어야 한다")
        devices = sorted_items(frozenset(self.devices))
        for device in devices:
            if not isinstance(device, str):
                raise TypeError("FailureRecord.devices 원소는 문자열이어야 한다")
        margin = self.margin
        if margin is not None:
            if isinstance(margin, bool) or not isinstance(margin, (int, float)):
                raise TypeError("FailureRecord.margin 은 None 또는 수여야 한다")
            margin = float(margin)
        raw = self.detail if isinstance(self.detail, Mapping) else dict(self.detail)
        for key in raw:
            if not isinstance(key, str):
                raise TypeError("FailureRecord.detail 키는 문자열이어야 한다")
        detail = sorted_items(raw)
        require_immutable(detail)
        object.__setattr__(self, "devices", devices)
        object.__setattr__(self, "margin", margin)
        object.__setattr__(self, "detail", detail)

    def to_json(self):
        """JSON 직렬화용 dict: {"class", "devices"(list), "margin", "detail"(dict)}."""
        return {
            "class": self.failure_class,
            "devices": list(self.devices),
            "margin": self.margin,
            "detail": dict(self.detail),
        }
