"""파이프라인 exit code -- 예외 -> N3.14 분류의 exit code (계획 N3.14, 설계 00-common §7.1).

진입점: `exit_code_for(exc) -> int`.
"""
from .failure_classes import FAILURE_CLASSES, UNEXPECTED_EXIT_CODE


def exit_code_for(exc):
    """예외 `exc` 의 exit code. MRO 앞에서부터 분류표에 exc 로 등록된 첫 클래스의 code, 없으면 예상 밖(1)."""
    if not isinstance(exc, BaseException):
        raise TypeError("exit_code_for 는 예외 인스턴스를 받는다")
    for cls in type(exc).__mro__:
        for _, entry in sorted(FAILURE_CLASSES.items()):
            if entry.exc is cls:
                return entry.exit_code
    return UNEXPECTED_EXIT_CODE
