"""S3 메모리 색인의 블록 결과 부분 -- 실행 하나 동안 (블록, 분할, 입력 버전)마다 처음 계산한 결과를 쥔다
(설계 40 §2.4.5 '블록 결과 색인', 사용자 결정 X-1 (3)·X-2·X-9·X-12·X-20, 계획 NFR-2).

진입점: `S3Index`(`Donors` 구현). 생성은 비공개 계약이다 -- `search.open_run` 만 `S3Index()` 를 부른다(구조 규칙 M (M-b)).

* 키 = (writer = 블록 이름, part = 분할 key("*" 하나), input_version). 실행 바깥 지문(`code_fp`·`env_fp`·spec 지문·`context_fp`·`run_id`)을
  키에 넣지 않는다(실행 사이 비공유를 키 모양으로도 지킨다). 디스크에 쓰지 않는다.
* 값 = 결과 스냅샷의 참조(값 사본 아님 -- graph 단일 정본) 또는 결정적 도메인 실패의 불변 `FailureRecord`.
  graph 밖 허용 저장소 (b)이다. 퇴출하지 않는다(퇴출하면 같은 입력 재계산이 생긴다).
* fail-closed: (3) 같은 키 재등록 `ValueError`(원천은 키마다 하나), (4) 등록하는 스냅샷의 `block_version` != 키의 입력 버전 `ValueError`,
  (6) 한 키에 성공 스냅샷과 실패 기록이 함께 등록되려 하면 `ValueError`(블록 순수성 위반). (1)(2) 는 블록 호출·`graft` 가 한다.
* 조회는 키 일치뿐이다(색인을 순회하지 않는다).
"""
from ..core import Donors, FailureRecord, GraphSnapshot


class S3Index(Donors):
    """블록 결과 색인. 직접 만들지 않는다(`open_run` 만)."""

    def __init__(self):
        self._snapshots = {}   # (writer, part, input_version) -> GraphSnapshot (참조)
        self._failures = {}    # (writer, part, input_version) -> FailureRecord (참조)

    def find(self, writer, part, input_version):
        return self._snapshots.get((writer, part, input_version))

    def register(self, writer, part, input_version, snapshot):
        key = (writer, part, input_version)
        if not isinstance(snapshot, GraphSnapshot):
            raise TypeError("S3Index.register: snapshot 은 GraphSnapshot 이어야 한다")
        if key in self._snapshots:
            raise ValueError("S3Index.register: 같은 키 " + repr(key) + " 재등록 -- 원천은 키마다 하나다")
        if key in self._failures:
            raise ValueError("S3Index.register: 키 " + repr(key) + " 에 이미 실패 기록이 있다 -- 성공과 실패가 섞였다(블록 순수성 위반)")
        if snapshot.block_version(writer) != input_version:
            raise ValueError("S3Index.register: 스냅샷의 " + repr(writer) + " 입력 버전이 키와 다르다: " + repr(key))
        self._snapshots[key] = snapshot

    def find_failure(self, writer, part, input_version):
        return self._failures.get((writer, part, input_version))

    def register_failure(self, writer, part, input_version, record):
        key = (writer, part, input_version)
        if not isinstance(record, FailureRecord):
            raise TypeError("S3Index.register_failure: record 는 FailureRecord 여야 한다")
        if key in self._failures:
            raise ValueError("S3Index.register_failure: 같은 키 " + repr(key) + " 재등록 -- 원천은 키마다 하나다")
        if key in self._snapshots:
            raise ValueError("S3Index.register_failure: 키 " + repr(key) + " 에 이미 성공 스냅샷이 있다 -- 성공과 실패가 섞였다(블록 순수성 위반)")
        self._failures[key] = record

    def entry_count(self):
        """실행 끝 항목 수 = 성공 키 수 + 실패 키 수(`perf.block_index_entries` 의 출처)."""
        return len(self._snapshots) + len(self._failures)
