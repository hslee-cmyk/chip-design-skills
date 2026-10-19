"""후보 실패의 부분 스냅샷 부착 (설계 40 §2.4.7 '실패 평가의 부분 스냅샷', 사용자 결정 X-3).

진입점: `attach_partial(exc, snapshot)`.

스냅샷을 쥔 쪽(sizing `run_kernel`·`seal_dc`, metrics `ss_evaluate`)이 후보 실패 클래스를 이름으로 잡아 붙인 뒤 다시 낸다.
`failure_errors.py` 는 데이터 선언 모듈이라 일반 메서드를 둘 수 없어 부착은 이 함수다. 이미 붙어 있으면 바꾸지 않는다
(가장 안쪽이 이긴다).
"""
from .failure_errors import InfeasibleSizingError
from .graph_snapshot import GraphSnapshot


def attach_partial(exc, snapshot):
    """`exc.partial` 에 실패 직전까지 쓴 `snapshot` 을 붙인다. 이미 있으면 그대로 둔다."""
    if not isinstance(exc, InfeasibleSizingError):
        raise TypeError("attach_partial: exc 는 InfeasibleSizingError 하위여야 한다: " + type(exc).__qualname__)
    if not isinstance(snapshot, GraphSnapshot):
        raise TypeError("attach_partial: snapshot 은 GraphSnapshot 이어야 한다: " + type(snapshot).__qualname__)
    if exc.partial is None:
        exc.partial = snapshot
