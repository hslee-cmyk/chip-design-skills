"""실행 하나의 블록 결과 색인·계수를 만드는 유일한 자리 (설계 40 §2.4.5 '수명' (1), 사용자 결정 X-12·X-20, 계획 offset-strategy PD-7·PD-8).

진입점: `open_run() -> (donors, counters)` = 새 `S3Index` 와 새 `RunCounters` 의 쌍.

* 부를 때마다 새 쌍이다(앞 호출과 아무것도 나누지 않는다). 실행 사이 비공유는 이 함수가 유일한 생성 자리라는 구조로 지킨다:
  `S3Index(`·`RunCounters(` 를 이 파일과 정의 모듈 밖에서 부르지 않고(구조 규칙 M (M-b)), `run_stage_a` 호출마다 같은 함수 안에서
  1:1 로 짝지어 부르며(M-c), 결과를 모듈·클래스·fixture 에 보관하지 않고(M-d), 디스크에 쓰지 않는다(M-f).
* 엔진 소스에서 이 이름을 참조하는 곳은 이 파일과 `search/__init__.py` 뿐이다(M-a, card B 의 허용 목록은 비어 있다).
* 서명 불변(인자 없음): 색인 항목 수 상한은 생성자 인자가 아니라 `find_front` 가 `donors.open_bound(total_of)` 로 열고 `close_bound()` 로 닫는다(card C, DF-1). 열기 밖(단계 A·B, MOD8)
  등록은 검사하지 않는다.
"""
from ..core import RunCounters
from .s3_index import S3Index


def open_run():
    """(donors, counters) -- 새 `S3Index` 와 새 `RunCounters`."""
    return S3Index(), RunCounters()
