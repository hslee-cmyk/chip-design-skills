"""writer 권한 위반 예외 -- 필드에 writer 가 둘이거나 권한표 밖 writer·필드에 쓰려 할 때 (계획 N3.4 '노드 하나에 writer 하나', SC-a).

진입점: `WriterPermissionError`.

코드 결함(선언 충돌)이라 N3.14 후보 실패 클래스가 아니다 -- 탐색 루프가 실패 기록으로 삼키지 않고
'예상 밖 예외'(exit code 1)로 드러난다.
"""


class WriterPermissionError(Exception):
    """writer 권한표 위반: (kind, field) 하나에 writer 둘 선언, 또는 권한 없는 writer·선언 없는 필드에 쓰기."""
