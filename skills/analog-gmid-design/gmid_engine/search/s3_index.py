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
* **항목 수 상한**(fail-closed (5), 설계 40 §2.4.5 '상한', card C): `open_bound(total_of)` 로 연 동안(`find_front` 진입~끝 확인) 등록(`register`·`register_failure`) 직후
  항목 수(`entry_count()`) > `index_bound(total_of())` = (등록된 서로 다른 (블록, 분할) 수) × (E_total + 1)이면 `RuntimeError`(한 키는 한 번만 계산하고 실행의 커널 평가는 E_total 이하이므로
  (블록, 분할)당 항목은 E_total + 1 을 넘을 수 없다). 색인은 E_total 값을 보관하지 않고 참조 `total_of`(인자 없는 호출 가능 객체)만 쥔다(graph 규칙 4) -- None 이면 검사하지 않고,
  정해진 뒤 첫 등록에서 잰다. 열기 전·닫은 뒤(단계 A·B, MOD8) 등록은 검사하지 않는다. 닫기 전 두 번째 `open_bound` 는 `ValueError`.
"""
from ..core import Donors, FailureRecord, GraphSnapshot


class S3Index(Donors):
    """블록 결과 색인. 직접 만들지 않는다(`open_run` 만)."""

    def __init__(self):
        self._snapshots = {}   # (writer, part, input_version) -> GraphSnapshot (참조)
        self._failures = {}    # (writer, part, input_version) -> FailureRecord (참조)
        self._parts = set()    # 등록된 (writer, part) -- 위 두 표의 키에서 나온 파생(상한 식의 쌍 수), 다른 생산자 없음
        self._total_of = None  # 열린 동안 E_total 을 읽는 참조(값 사본 아님) -- 닫힘 = None

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
        self._parts.add(key[:2])
        self._check_bound()

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
        self._parts.add(key[:2])
        self._check_bound()

    def entry_count(self):
        """실행 끝 항목 수 = 성공 키 수 + 실패 키 수(`perf.block_index_entries` 의 출처)."""
        return len(self._snapshots) + len(self._failures)

    def open_bound(self, total_of):
        """항목 수 상한 검사를 연다. `total_of` = 인자 없는 호출 가능 객체(E_total 또는 None). 이미 열려 있으면 `ValueError`."""
        if self._total_of is not None:
            raise ValueError("S3Index.open_bound: 이미 열려 있다 -- close_bound 뒤에 다시 연다")
        if not callable(total_of):
            raise TypeError("S3Index.open_bound: total_of 는 인자 없는 호출 가능 객체여야 한다")
        self._total_of = total_of

    def close_bound(self):
        self._total_of = None

    def index_bound(self, total):
        """(등록된 서로 다른 (블록, 분할) 수) × (total + 1) -- 항목 수 상한 식 하나(검사와 `perf.block_index_bound` 가 같은 메서드를 읽는다)."""
        return len(self._parts) * (total + 1)

    def _check_bound(self):
        if self._total_of is None:
            return
        total = self._total_of()
        if total is not None and self.entry_count() > self.index_bound(total):
            raise RuntimeError("S3Index: 항목 수 " + str(self.entry_count()) + " 가 상한 " + str(self.index_bound(total))
                               + " 를 넘었다(블록 결과 색인 상한 -- 같은 키 재계산 또는 커널 평가 수 > E_total)")
