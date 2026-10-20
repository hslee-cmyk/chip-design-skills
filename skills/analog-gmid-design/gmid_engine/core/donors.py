"""블록 결과 원천 조회 규약 -- 계산 블록 호출이 같은 입력의 앞선 결과(성공 스냅샷 또는 결정적 도메인 실패 기록)를 찾는 추상 기반
(설계 40 §2.4.4 API, 사용자 결정 X-1 (3)·X-7·X-9).

진입점: `Donors`. 구현은 search `S3Index`(실행 하나에 하나, `search.open_run` 이 만든다). 상태·생성자 인자가 없다.
네 메서드 모두 추상이다 -- 하위가 하나라도 빠뜨리면 생성 때 `TypeError`(블록 호출이 확인하는 형식이 이 기반 하나다).

* 키 = (writer = 블록 이름, part = 분할 key(card B 에서는 "*" 하나), input_version).
* `find`/`register`: 성공 결과 스냅샷의 참조(값 사본 아님). `find_failure`/`register_failure`: 불변 `FailureRecord`.
"""
import abc


class Donors(abc.ABC):
    """블록 결과 원천 조회의 추상 기반."""

    @abc.abstractmethod
    def find(self, writer, part, input_version):
        """등록된 결과 스냅샷(`GraphSnapshot`), 없으면 None."""

    @abc.abstractmethod
    def register(self, writer, part, input_version, snapshot):
        """계산 직후 한 번 등록한다."""

    @abc.abstractmethod
    def find_failure(self, writer, part, input_version):
        """등록된 결정적 도메인 실패 기록(`FailureRecord`), 없으면 None."""

    @abc.abstractmethod
    def register_failure(self, writer, part, input_version, record):
        """결정적 도메인 실패 기록을 한 번 등록한다."""
